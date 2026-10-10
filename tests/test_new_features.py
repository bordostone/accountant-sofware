import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import init_db, get_db
from backend.services import kasa_banka_service, cari_service, rapor_service
from backend.models import OdemeTahsilatCreate, CariCreate, CariUpdate

class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        test_db = os.path.abspath("test_muhasebe_features.db")
        if os.path.exists(test_db):
            os.remove(test_db)
        
        import backend.database as db_mod
        db_mod.DB_PATH = test_db
        init_db()

        bankalar = kasa_banka_service.list_bankalar()
        self.banka_id = bankalar[0]["id"]

        # Reset bank balance to 0
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE bankalar SET bakiye = 0.0 WHERE id = ?", (self.banka_id,))
        conn.commit()
        conn.close()

    def tearDown(self):
        import backend.database as db_mod
        if os.path.exists(db_mod.DB_PATH):
            os.remove(db_mod.DB_PATH)

    def test_cari_personel_fields_and_filtering(self):
        # 1. Create a regular customer
        c1 = cari_service.create_cari(CariCreate(
            kod="M-001",
            unvan="Müşteri Ltd.",
            tip="MUSTERI",
            is_personel=False
        ))
        self.assertFalse(c1["is_personel"])

        # 2. Create a personnel
        c2 = cari_service.create_cari(CariCreate(
            kod="P-001",
            unvan="Ahmet Yılmaz",
            tip="HEPSI",
            is_personel=True,
            personel_gorevi="Usta Başı",
            personel_departman="Fabrika / Kesim"
        ))
        self.assertTrue(c2["is_personel"])
        self.assertEqual(c2["personel_gorevi"], "Usta Başı")
        self.assertEqual(c2["personel_departman"], "Fabrika / Kesim")

        # 3. Filter by tip="PERSONEL"
        personeller = cari_service.list_cariler(tip="PERSONEL")
        self.assertEqual(len(personeller), 1)
        self.assertEqual(personeller[0]["kod"], "P-001")

        # 4. Filter by tip="MUSTERI"
        musteriler = cari_service.list_cariler(tip="MUSTERI")
        self.assertEqual(len(musteriler), 1)
        self.assertEqual(musteriler[0]["kod"], "M-001")

    def test_cari_update_correction(self):
        # Create cari
        c = cari_service.create_cari(CariCreate(
            kod="C-DUZELT-01",
            unvan="Eski Unvan",
            tip="MUSTERI",
            telefon="05551112233"
        ))
        cid = c["id"]

        # Update cari (düzeltme)
        updated = cari_service.update_cari(cid, CariUpdate(
            kod="C-DUZELT-01",
            unvan="Yeni Güncel Unvan A.Ş.",
            tip="MUSTERI",
            telefon="05559998877",
            is_personel=True,
            personel_gorevi="Genel Müdür",
            personel_departman="Yönetim"
        ))
        self.assertEqual(updated["unvan"], "Yeni Güncel Unvan A.Ş.")
        self.assertEqual(updated["telefon"], "05559998877")
        self.assertTrue(updated["is_personel"])
        self.assertEqual(updated["personel_gorevi"], "Genel Müdür")

        # Re-fetch from DB
        fetched = cari_service.get_cari(cid)
        self.assertEqual(fetched["unvan"], "Yeni Güncel Unvan A.Ş.")
        self.assertTrue(fetched["is_personel"])

    def test_kredi_karti_tahsilat_lifecycle(self):
        # Create customer
        c = cari_service.create_cari(CariCreate(
            kod="C-KREDICART-01",
            unvan="Kart Müşterisi",
            tip="MUSTERI"
        ))
        cid = c["id"]

        # Create credit card collection (3500 TL via POS/Bank)
        tahsilat = kasa_banka_service.create_islem(OdemeTahsilatCreate(
            islem_turu="KREDI_KARTI_TAHSILAT",
            tarih="2026-10-09",
            tutar=3500.0,
            banka_id=self.banka_id,
            cari_id=cid,
            aciklama="POS Kredi Kartı Çekimi",
            evrak_no="SLIP-987"
        ))
        islem_id = tahsilat["islem_id"]

        # 1. Bank balance should increase by 3500
        bankalar = kasa_banka_service.list_bankalar()
        banka = next(b for b in bankalar if b["id"] == self.banka_id)
        self.assertEqual(banka["bakiye"], 3500.0)

        # 2. Cari balance should reflect collection (-3500 or alacak 3500)
        cari = cari_service.get_cari(cid)
        self.assertEqual(cari["bakiye"], -3500.0)

        # 3. Cari ekstre should show KREDI_KARTI_TAHSILAT
        ekstre = cari_service.get_cari_ekstre(cid)
        self.assertEqual(len(ekstre["hareketler"]), 1)
        self.assertEqual(ekstre["hareketler"][0]["islem_turu"], "KREDI_KARTI_TAHSILAT")
        self.assertEqual(ekstre["hareketler"][0]["alacak"], 3500.0)
        self.assertEqual(ekstre["toplam_alacak"], 3500.0)

        # 4. Rapor service should count it in tahsilat
        rapor = rapor_service.get_tahsilat_odeme_raporu(baslangic="2026-10-01", bitis="2026-10-31")
        self.assertEqual(rapor["ozet"]["toplam_tahsilat"], 3500.0)

        # 5. Delete transaction (reversal)
        kasa_banka_service.delete_islem(islem_id)
        bankalar = kasa_banka_service.list_bankalar()
        banka = next(b for b in bankalar if b["id"] == self.banka_id)
        self.assertEqual(banka["bakiye"], 0.0)

        cari = cari_service.get_cari(cid)
        self.assertEqual(cari["bakiye"], 0.0)

if __name__ == '__main__':
    unittest.main()
