import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import init_db, get_db, DB_PATH
from backend.services import kasa_banka_service, cari_service, fatura_service
from backend.models import OdemeTahsilatCreate, CariCreate, FaturaCreate, FaturaKalemIn

class TestKasaBanka(unittest.TestCase):
    def setUp(self):
        # Fresh db for testing
        test_db = os.path.abspath("test_muhasebe.db")
        if os.path.exists(test_db):
            os.remove(test_db)
        
        import backend.database as db_mod
        db_mod.DB_PATH = test_db
        init_db()

        kasalar = kasa_banka_service.list_kasalar()
        self.kasa_id = kasalar[0]["id"]
        bankalar = kasa_banka_service.list_bankalar()
        self.banka_id = bankalar[0]["id"]

        # Reset initial balances for clear assertions
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE kasalar SET bakiye = 0.0 WHERE id = ?", (self.kasa_id,))
        c.execute("UPDATE bankalar SET bakiye = 0.0 WHERE id = ?", (self.banka_id,))
        conn.commit()
        conn.close()

        # Create Cari
        cari = cari_service.create_cari(CariCreate(kod="C-TEST-01", unvan="Test Müşteri Ltd", tip="MUSTERI"))
        self.cari_id = cari["id"]

    def tearDown(self):
        import backend.database as db_mod
        if os.path.exists(db_mod.DB_PATH):
            os.remove(db_mod.DB_PATH)

    def test_nakit_tahsilat_lifecycle(self):
        # 1. Tahsilat ekle (1000 TL)
        data1 = OdemeTahsilatCreate(
            islem_turu="KASA_TAHSILAT",
            tarih="2026-10-08",
            tutar=1000.0,
            kasa_id=self.kasa_id,
            cari_id=self.cari_id,
            aciklama="Elden tahsilat"
        )
        res = kasa_banka_service.create_islem(data1)
        islem_id = res["islem_id"]

        kasalar = kasa_banka_service.list_kasalar()
        self.assertEqual(kasalar[0]["bakiye"], 1000.0)
        c = cari_service.get_cari(self.cari_id)
        self.assertEqual(c["bakiye"], -1000.0)

        # 2. Tahsilatı güncelle (1500 TL yap)
        data2 = OdemeTahsilatCreate(
            islem_turu="KASA_TAHSILAT",
            tarih="2026-10-08",
            tutar=1500.0,
            kasa_id=self.kasa_id,
            cari_id=self.cari_id,
            aciklama="Güncellenmiş tahsilat"
        )
        kasa_banka_service.update_islem(islem_id, data2)
        kasalar = kasa_banka_service.list_kasalar()
        self.assertEqual(kasalar[0]["bakiye"], 1500.0)
        c = cari_service.get_cari(self.cari_id)
        self.assertEqual(c["bakiye"], -1500.0)

        # 3. Tahsilatı sil
        kasa_banka_service.delete_islem(islem_id)
        kasalar = kasa_banka_service.list_kasalar()
        self.assertEqual(kasalar[0]["bakiye"], 0.0)
        c = cari_service.get_cari(self.cari_id)
        self.assertEqual(c["bakiye"], 0.0)

    def test_fatura_tahsilat_sync(self):
        # Fatura oluştur: 5000 TL satış faturası
        fat_data = FaturaCreate(
            fatura_no="FAT-TEST-001",
            fatura_turu="SATIS",
            cari_id=self.cari_id,
            fatura_tarihi="2026-10-08",
            kalemler=[
                FaturaKalemIn(
                    aciklama="Hizmet",
                    miktar=1.0,
                    birim="Adet",
                    birim_fiyat=5000.0,
                    kdv_orani=0
                )
            ]
        )
        fat = fatura_service.create_fatura(fat_data)
        fatura_id = fat["id"]

        # Başlangıç durumu
        f_info = fatura_service.get_fatura(fatura_id)
        self.assertEqual(f_info["odeme_durumu"], "BEKLIYOR")
        self.assertEqual(f_info["kalan_tutar"], 5000.0)

        # 2000 TL tahsilat
        islem = kasa_banka_service.create_islem(OdemeTahsilatCreate(
            islem_turu="KASA_TAHSILAT",
            tarih="2026-10-08",
            tutar=2000.0,
            kasa_id=self.kasa_id,
            cari_id=self.cari_id,
            fatura_id=fatura_id,
            aciklama="Kısmi ödeme"
        ))
        islem_id = islem["islem_id"]

        f_info = fatura_service.get_fatura(fatura_id)
        self.assertEqual(f_info["odeme_durumu"], "KISMI")
        self.assertEqual(f_info["odenen_tutar"], 2000.0)
        self.assertEqual(f_info["kalan_tutar"], 3000.0)

        # Tahsilatı sil -> Fatura tekrar BEKLIYOR ve 5000 kalan olmalı
        kasa_banka_service.delete_islem(islem_id)
        f_info = fatura_service.get_fatura(fatura_id)
        self.assertEqual(f_info["odeme_durumu"], "BEKLIYOR")
        self.assertEqual(f_info["odenen_tutar"], 0.0)
        self.assertEqual(f_info["kalan_tutar"], 5000.0)

    def test_virman_and_delete(self):
        # Kasaya başlangıçta 1000 koyalım
        kasa_banka_service.create_islem(OdemeTahsilatCreate(
            islem_turu="KASA_TAHSILAT",
            tarih="2026-10-08",
            tutar=1000.0,
            kasa_id=self.kasa_id,
            aciklama="Kasaya para yatırma"
        ))

        # Kasadan bankaya 400 TL virman
        virman = kasa_banka_service.create_islem(OdemeTahsilatCreate(
            islem_turu="KASA_BANKA_VIRMAN",
            tarih="2026-10-08",
            tutar=400.0,
            kasa_id=self.kasa_id,
            banka_id=self.banka_id,
            aciklama="Bankaya yatırılan"
        ))
        virman_id = virman["islem_id"]

        k = kasa_banka_service.list_kasalar()[0]["bakiye"]
        b = kasa_banka_service.list_bankalar()[0]["bakiye"]
        self.assertEqual(k, 600.0)
        self.assertEqual(b, 400.0)

        # Virmanı sil
        kasa_banka_service.delete_islem(virman_id)
        k = kasa_banka_service.list_kasalar()[0]["bakiye"]
        b = kasa_banka_service.list_bankalar()[0]["bakiye"]
        self.assertEqual(k, 1000.0)
        self.assertEqual(b, 0.0)

    def test_type_change_kasa_to_banka(self):
        # 1. Kasa Tahsilat olarak 500 TL gir
        islem = kasa_banka_service.create_islem(OdemeTahsilatCreate(
            islem_turu="KASA_TAHSILAT",
            tarih="2026-10-08",
            tutar=500.0,
            kasa_id=self.kasa_id,
            cari_id=self.cari_id,
            aciklama="Nakit tahsilat sanılmıştı"
        ))
        islem_id = islem["islem_id"]

        self.assertEqual(kasa_banka_service.list_kasalar()[0]["bakiye"], 500.0)
        self.assertEqual(kasa_banka_service.list_bankalar()[0]["bakiye"], 0.0)
        self.assertEqual(cari_service.get_cari(self.cari_id)["bakiye"], -500.0)

        # 2. Aslında Banka Gelen Havale imiş, düzenle
        kasa_banka_service.update_islem(islem_id, OdemeTahsilatCreate(
            islem_turu="BANKA_GELEN_HAVALE",
            tarih="2026-10-08",
            tutar=500.0,
            banka_id=self.banka_id,
            cari_id=self.cari_id,
            aciklama="Düzeltildi: Havale ile gelmiş"
        ))

        self.assertEqual(kasa_banka_service.list_kasalar()[0]["bakiye"], 0.0)
        self.assertEqual(kasa_banka_service.list_bankalar()[0]["bakiye"], 500.0)
        self.assertEqual(cari_service.get_cari(self.cari_id)["bakiye"], -500.0)

        # 3. Hareketi sil
        kasa_banka_service.delete_islem(islem_id)
        self.assertEqual(kasa_banka_service.list_kasalar()[0]["bakiye"], 0.0)
        self.assertEqual(kasa_banka_service.list_bankalar()[0]["bakiye"], 0.0)
        self.assertEqual(cari_service.get_cari(self.cari_id)["bakiye"], 0.0)

    def test_banka_and_kasa_crud(self):
        from backend.models import BankaCreate, KasaCreate
        # 1. Yeni banka ekle
        b_res = kasa_banka_service.create_banka(BankaCreate(
            banka_adi="Ziraat Bankası",
            sube_adi="Merkez Şube",
            hesap_no="998877",
            iban="TR99 0001 0002 0003 0004 0005 06"
        ))
        b_id = b_res["id"]
        b_detay = kasa_banka_service.get_banka(b_id)
        self.assertEqual(b_detay["banka_adi"], "Ziraat Bankası")
        self.assertEqual(b_detay["iban"], "TR99 0001 0002 0003 0004 0005 06")

        # 2. Bankayı güncelle
        kasa_banka_service.update_banka(b_id, BankaCreate(
            banka_adi="Ziraat Bankası Ticari",
            sube_adi="Sanayi Şube",
            hesap_no="998877",
            iban="TR99 0001 0002 0003 0004 0005 99"
        ))
        b_detay = kasa_banka_service.get_banka(b_id)
        self.assertEqual(b_detay["banka_adi"], "Ziraat Bankası Ticari")
        self.assertEqual(b_detay["sube_adi"], "Sanayi Şube")

        # 3. Bankayı sil
        kasa_banka_service.delete_banka(b_id)
        self.assertIsNone(kasa_banka_service.get_banka(b_id))

        # 4. Yeni kasa ekle, güncelle, sil
        k_res = kasa_banka_service.create_kasa(KasaCreate(ad="Dolar Kasası", para_birimi="USD"))
        k_id = k_res["id"]
        k_detay = kasa_banka_service.get_kasa(k_id)
        self.assertEqual(k_detay["ad"], "Dolar Kasası")

        kasa_banka_service.update_kasa(k_id, KasaCreate(ad="Euro Kasası", para_birimi="EUR"))
        k_detay = kasa_banka_service.get_kasa(k_id)
        self.assertEqual(k_detay["ad"], "Euro Kasası")
        self.assertEqual(k_detay["para_birimi"], "EUR")

        kasa_banka_service.delete_kasa(k_id)
        self.assertIsNone(kasa_banka_service.get_kasa(k_id))

if __name__ == '__main__':
    unittest.main()
