import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.database as db_mod
from backend.database import init_db, get_db
from backend.services import cari_service, kasa_banka_service
from backend.routers import api_ayarlar

class TestStartupAndReset(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.abspath("test_startup.db")
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        db_mod.DB_PATH = self.test_db
        init_db()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_idempotent_init_db(self):
        # 1. Başlangıçta init_db çağrıldı
        # 2. Tekrar çağırıldığında hata vermemeli
        init_db()
        init_db()
        
        # Kasalar ve bankalar kontrol
        kasalar = kasa_banka_service.list_kasalar()
        bankalar = kasa_banka_service.list_bankalar()
        self.assertGreaterEqual(len(kasalar), 1)
        self.assertGreaterEqual(len(bankalar), 1)

    def test_user_deletes_records_then_restarts_does_not_crash(self):
        # Kullanıcı tüm carileri sildi
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM cariler")
        c.execute("DELETE FROM faturalar")
        c.execute("DELETE FROM fatura_kalemleri")
        c.execute("DELETE FROM cari_hareketler")
        c.execute("DELETE FROM kasa_banka_hareketleri")
        conn.commit()
        conn.close()

        # Yeniden başlatma simülasyonu (init_db tekrar çalışır)
        try:
            init_db()
        except Exception as e:
            self.fail(f"init_db crashed on restart after deletion: {e}")

        # Bakiyeler sıfır olmalı, hayali 42.000 TL veya 28.500 TL olmamalı
        kasalar = kasa_banka_service.list_kasalar()
        bankalar = kasa_banka_service.list_bankalar()
        for k in kasalar:
            self.assertEqual(k["bakiye"], 0.0)
        for b in bankalar:
            self.assertEqual(b["bakiye"], 0.0)

    def test_verileri_sifirla_api(self):
        res = api_ayarlar.verileri_sifirla(tumunu_temizle=True)
        self.assertTrue(res["success"])
        
        kasalar = kasa_banka_service.list_kasalar()
        bankalar = kasa_banka_service.list_bankalar()
        for k in kasalar:
            self.assertEqual(k["bakiye"], 0.0)
        for b in bankalar:
            self.assertEqual(b["bakiye"], 0.0)

if __name__ == '__main__':
    unittest.main()
