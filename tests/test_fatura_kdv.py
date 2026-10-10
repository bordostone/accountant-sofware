import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.database as db_mod
from backend.database import init_db, get_db
from backend.services import cari_service, fatura_service
from backend.models import CariCreate, FaturaCreate, FaturaKalemIn

class TestFaturaKdv(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.abspath("test_fatura_kdv.db")
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        db_mod.DB_PATH = self.test_db
        init_db()

        # Test carisi ekle
        c = cari_service.create_cari(CariCreate(kod="C-KDV-01", unvan="KDV Test Cari", tip="MUSTERI"))
        self.cari_id = c["id"]

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_custom_kdv_rate(self):
        # KDV oranı %8 olan kalem ekle
        fat_data = FaturaCreate(
            fatura_no="FAT-KDV-001",
            fatura_turu="SATIS",
            cari_id=self.cari_id,
            fatura_tarihi="2026-10-09",
            kalemler=[
                FaturaKalemIn(
                    aciklama="Özel KDV'li Hizmet",
                    miktar=2.0,
                    birim="Adet",
                    birim_fiyat=500.0,
                    kdv_orani=8.0
                )
            ]
        )
        fat = fatura_service.create_fatura(fat_data)
        self.assertEqual(fat["ara_toplam"], 1000.0)
        self.assertEqual(fat["kdv_toplam"], 80.0)
        self.assertEqual(fat["genel_toplam"], 1080.0)
        self.assertEqual(fat["kalemler"][0]["kdv_orani"], 8.0)
        self.assertEqual(fat["kalemler"][0]["kdv_tutari"], 80.0)

    def test_manual_kdv_tutari_override(self):
        # Kullanıcı KDV tutarını doğrudan 153.75 TL olarak girdi
        fat_data = FaturaCreate(
            fatura_no="FAT-KDV-002",
            fatura_turu="ALIS",
            cari_id=self.cari_id,
            fatura_tarihi="2026-10-09",
            kalemler=[
                FaturaKalemIn(
                    aciklama="Gelen İrsaliyeli Fatura",
                    miktar=1.0,
                    birim="Adet",
                    birim_fiyat=1000.0,
                    kdv_orani=20.0,
                    kdv_tutari=153.75 # Manuel KDV tutarı
                )
            ]
        )
        fat = fatura_service.create_fatura(fat_data)
        self.assertEqual(fat["ara_toplam"], 1000.0)
        self.assertEqual(fat["kdv_toplam"], 153.75)
        self.assertEqual(fat["genel_toplam"], 1153.75)
        self.assertEqual(fat["kalemler"][0]["kdv_tutari"], 153.75)

    def test_manual_overall_kdv_toplam(self):
        # Kullanıcı genel KDV toplamını alt özetten 205.50 TL olarak girdi
        fat_data = FaturaCreate(
            fatura_no="FAT-KDV-003",
            fatura_turu="SATIS",
            cari_id=self.cari_id,
            fatura_tarihi="2026-10-09",
            kdv_toplam=205.50,
            kalemler=[
                FaturaKalemIn(
                    aciklama="Ürün Satışı",
                    miktar=1.0,
                    birim="Adet",
                    birim_fiyat=1000.0,
                    kdv_orani=20.0
                )
            ]
        )
        fat = fatura_service.create_fatura(fat_data)
        self.assertEqual(fat["ara_toplam"], 1000.0)
        self.assertEqual(fat["kdv_toplam"], 205.50)
        self.assertEqual(fat["genel_toplam"], 1205.50)

if __name__ == '__main__':
    unittest.main()
