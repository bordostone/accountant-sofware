import os
import sqlite3
from datetime import datetime, date

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "muhasebe.db")

def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # 1. Ayarlar Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ayarlar (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        firma_adi TEXT NOT NULL DEFAULT 'ÖZERLER MERMER SAN. VE TİC. LTD. ŞTİ.',
        yetkili TEXT DEFAULT 'Hakan Özer',
        vergi_dairesi TEXT DEFAULT 'Afyonkarahisar Vergi Dairesi',
        vergi_no TEXT DEFAULT '6540123456',
        tckn TEXT DEFAULT '',
        telefon TEXT DEFAULT '0 (272) 214 00 00',
        eposta TEXT DEFAULT 'muhasebe@ozerlermermer.com.tr',
        web TEXT DEFAULT 'www.ozerlermermer.com.tr',
        adres TEXT DEFAULT 'Organize Sanayi Bölgesi 2. Cadde No: 14 Afyonkarahisar',
        varsayilan_iban TEXT DEFAULT 'TR12 0006 2000 0001 2345 6789 01',
        varsayilan_banka TEXT DEFAULT 'Garanti BBVA - Afyon Şubesi',
        fatura_notu TEXT DEFAULT 'İşbu fatura bedeli 30 gün içerisinde ödenmelidir. Gecikmelerde aylık %3 vade farkı uygulanır.',
        para_birimi TEXT DEFAULT '₺'
    );
    """)

    # 2. Cariler (Müşteri & Tedarikçi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cariler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kod TEXT UNIQUE NOT NULL,
        unvan TEXT NOT NULL,
        tip TEXT NOT NULL CHECK(tip IN ('MUSTERI', 'TEDARIKCI', 'HEPSI')),
        yetkili_kisi TEXT DEFAULT '',
        vergi_dairesi TEXT DEFAULT '',
        vergi_no TEXT DEFAULT '',
        tckn TEXT DEFAULT '',
        telefon TEXT DEFAULT '',
        eposta TEXT DEFAULT '',
        adres TEXT DEFAULT '',
        il TEXT DEFAULT '',
        ilce TEXT DEFAULT '',
        borc REAL NOT NULL DEFAULT 0.0,
        alacak REAL NOT NULL DEFAULT 0.0,
        bakiye REAL NOT NULL DEFAULT 0.0,
        durum TEXT NOT NULL DEFAULT 'AKTIF',
        notlar TEXT DEFAULT '',
        is_personel INTEGER NOT NULL DEFAULT 0,
        personel_gorevi TEXT DEFAULT '',
        personel_departman TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 3. Stok & Hizmet Kartları
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stoklar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kod TEXT UNIQUE NOT NULL,
        ad TEXT NOT NULL,
        tip TEXT NOT NULL CHECK(tip IN ('URUN', 'HIZMET')),
        birim TEXT NOT NULL DEFAULT 'Adet',
        alis_fiyati REAL NOT NULL DEFAULT 0.0,
        satis_fiyati REAL NOT NULL DEFAULT 0.0,
        kdv_orani INTEGER NOT NULL DEFAULT 20,
        stok_miktari REAL NOT NULL DEFAULT 0.0,
        kritik_stok REAL NOT NULL DEFAULT 5.0,
        durum TEXT NOT NULL DEFAULT 'AKTIF',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 4. Kasalar (Nakit Kasa)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kasalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kod TEXT UNIQUE NOT NULL,
        ad TEXT NOT NULL,
        para_birimi TEXT NOT NULL DEFAULT 'TRY',
        bakiye REAL NOT NULL DEFAULT 0.0,
        aciklama TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 5. Bankalar (Banka Hesapları - Havale/EFT)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bankalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        banka_adi TEXT NOT NULL,
        sube_adi TEXT DEFAULT '',
        hesap_no TEXT DEFAULT '',
        iban TEXT NOT NULL,
        para_birimi TEXT NOT NULL DEFAULT 'TRY',
        bakiye REAL NOT NULL DEFAULT 0.0,
        aciklama TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 6. Faturalar (Satış & Alış)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faturalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fatura_no TEXT UNIQUE NOT NULL,
        fatura_turu TEXT NOT NULL CHECK(fatura_turu IN ('SATIS', 'ALIS')),
        fatura_tarihi TEXT NOT NULL,
        vade_tarihi TEXT,
        cari_id INTEGER NOT NULL REFERENCES cariler(id) ON DELETE RESTRICT,
        ara_toplam REAL NOT NULL DEFAULT 0.0,
        iskonto_orani REAL NOT NULL DEFAULT 0.0,
        iskonto_tutari REAL NOT NULL DEFAULT 0.0,
        kdv_toplam REAL NOT NULL DEFAULT 0.0,
        genel_toplam REAL NOT NULL DEFAULT 0.0,
        odenen_tutar REAL NOT NULL DEFAULT 0.0,
        kalan_tutar REAL NOT NULL DEFAULT 0.0,
        odeme_durumu TEXT NOT NULL DEFAULT 'BEKLIYOR' CHECK(odeme_durumu IN ('BEKLIYOR', 'KISMI', 'ODENDI', 'IPTAL')),
        aciklama TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 7. Fatura Kalemleri (Detay Satırları)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fatura_kalemleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fatura_id INTEGER NOT NULL REFERENCES faturalar(id) ON DELETE CASCADE,
        stok_id INTEGER REFERENCES stoklar(id) ON DELETE SET NULL,
        aciklama TEXT NOT NULL,
        miktar REAL NOT NULL DEFAULT 1.0,
        birim TEXT NOT NULL DEFAULT 'Adet',
        birim_fiyat REAL NOT NULL DEFAULT 0.0,
        kdv_orani INTEGER NOT NULL DEFAULT 20,
        kdv_tutari REAL NOT NULL DEFAULT 0.0,
        iskonto_orani REAL NOT NULL DEFAULT 0.0,
        iskonto_tutari REAL NOT NULL DEFAULT 0.0,
        satir_toplami REAL NOT NULL DEFAULT 0.0
    );
    """)

    # 8. Çek Takibi (Alınan & Verilen Çekler)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cekler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cek_turu TEXT NOT NULL CHECK(cek_turu IN ('ALINAN', 'VERILEN')),
        cek_no TEXT NOT NULL,
        vade_tarihi TEXT NOT NULL,
        giris_tarihi TEXT NOT NULL DEFAULT (date('now', 'localtime')),
        tutar REAL NOT NULL DEFAULT 0.0,
        para_birimi TEXT NOT NULL DEFAULT 'TRY',
        banka_adi TEXT NOT NULL,
        sube_adi TEXT DEFAULT '',
        hesap_no TEXT DEFAULT '',
        kesideci TEXT DEFAULT '',
        cari_id INTEGER NOT NULL REFERENCES cariler(id) ON DELETE RESTRICT,
        durum TEXT NOT NULL DEFAULT 'PORTFOYDE' CHECK(durum IN ('PORTFOYDE', 'BANKAYA_VERILDI', 'TAHSIL_EDILDI', 'CIROLANMIS', 'KARSILIKSIZ', 'IADE_EDILDI')),
        tahsil_tarihi TEXT,
        tahsil_kasa_id INTEGER REFERENCES kasalar(id) ON DELETE SET NULL,
        tahsil_banka_id INTEGER REFERENCES bankalar(id) ON DELETE SET NULL,
        cirolanan_cari_id INTEGER REFERENCES cariler(id) ON DELETE SET NULL,
        aciklama TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 9. Kasa & Banka Hareketleri (Nakit, Havale, EFT, Virman, Kredi Kartı)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kasa_banka_hareketleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        islem_tarihi TEXT NOT NULL,
        islem_turu TEXT NOT NULL CHECK(islem_turu IN (
            'KASA_TAHSILAT', 'KASA_ODEME', 
            'BANKA_GELEN_HAVALE', 'BANKA_GIDEN_HAVALE', 
            'KASA_BANKA_VIRMAN', 'BANKA_KASA_VIRMAN', 
            'CEK_TAHSILATI_KASA', 'CEK_TAHSILATI_BANKA', 
            'MASRAF_ODEME', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT', 'DIGER'
        )),
        kasa_id INTEGER REFERENCES kasalar(id) ON DELETE SET NULL,
        banka_id INTEGER REFERENCES bankalar(id) ON DELETE SET NULL,
        cari_id INTEGER REFERENCES cariler(id) ON DELETE SET NULL,
        fatura_id INTEGER REFERENCES faturalar(id) ON DELETE SET NULL,
        cek_id INTEGER REFERENCES cekler(id) ON DELETE SET NULL,
        tutar REAL NOT NULL,
        para_birimi TEXT NOT NULL DEFAULT 'TRY',
        aciklama TEXT DEFAULT '',
        evrak_no TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 10. Cari Hareketleri (Cari Ekstre İçin Hesap Defteri)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cari_hareketler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cari_id INTEGER NOT NULL REFERENCES cariler(id) ON DELETE CASCADE,
        tarih TEXT NOT NULL,
        islem_turu TEXT NOT NULL,
        evrak_no TEXT DEFAULT '',
        borc REAL NOT NULL DEFAULT 0.0,
        alacak REAL NOT NULL DEFAULT 0.0,
        aciklama TEXT DEFAULT '',
        ref_fatura_id INTEGER REFERENCES faturalar(id) ON DELETE SET NULL,
        ref_hareket_id INTEGER REFERENCES kasa_banka_hareketleri(id) ON DELETE SET NULL,
        ref_cek_id INTEGER REFERENCES cekler(id) ON DELETE SET NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # --- Otomatik Şema Güncelleme (Migration) ---
    # 1. Cariler tablosunda is_personel, personel_gorevi, personel_departman kontrolü
    cursor.execute("PRAGMA table_info(cariler)")
    cari_cols = [c[1] for c in cursor.fetchall()]
    if "is_personel" not in cari_cols:
        cursor.execute("ALTER TABLE cariler ADD COLUMN is_personel INTEGER NOT NULL DEFAULT 0")
    if "personel_gorevi" not in cari_cols:
        cursor.execute("ALTER TABLE cariler ADD COLUMN personel_gorevi TEXT DEFAULT ''")
    if "personel_departman" not in cari_cols:
        cursor.execute("ALTER TABLE cariler ADD COLUMN personel_departman TEXT DEFAULT ''")

    # 2. kasa_banka_hareketleri CHECK constraintinde KREDI_KARTI_TAHSILAT kontrolü
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='kasa_banka_hareketleri'")
    tbl_row = cursor.fetchone()
    if tbl_row and 'KREDI_KARTI_TAHSILAT' not in tbl_row[0]:
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kasa_banka_hareketleri_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            islem_tarihi TEXT NOT NULL,
            islem_turu TEXT NOT NULL CHECK(islem_turu IN (
                'KASA_TAHSILAT', 'KASA_ODEME', 
                'BANKA_GELEN_HAVALE', 'BANKA_GIDEN_HAVALE', 
                'KASA_BANKA_VIRMAN', 'BANKA_KASA_VIRMAN', 
                'CEK_TAHSILATI_KASA', 'CEK_TAHSILATI_BANKA', 
                'MASRAF_ODEME', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT', 'DIGER'
            )),
            kasa_id INTEGER REFERENCES kasalar(id) ON DELETE SET NULL,
            banka_id INTEGER REFERENCES bankalar(id) ON DELETE SET NULL,
            cari_id INTEGER REFERENCES cariler(id) ON DELETE SET NULL,
            fatura_id INTEGER REFERENCES faturalar(id) ON DELETE SET NULL,
            cek_id INTEGER REFERENCES cekler(id) ON DELETE SET NULL,
            tutar REAL NOT NULL,
            para_birimi TEXT NOT NULL DEFAULT 'TRY',
            aciklama TEXT DEFAULT '',
            evrak_no TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        """)
        cursor.execute("INSERT INTO kasa_banka_hareketleri_new SELECT * FROM kasa_banka_hareketleri;")
        cursor.execute("DROP TABLE kasa_banka_hareketleri;")
        cursor.execute("ALTER TABLE kasa_banka_hareketleri_new RENAME TO kasa_banka_hareketleri;")
        cursor.execute("PRAGMA foreign_keys = ON")

    conn.commit()

    # Varsayılan ayarları ekle
    cursor.execute("SELECT COUNT(*) FROM ayarlar")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO ayarlar (id) VALUES (1)")
        conn.commit()

    # Varsayılan Kasa ve Banka Kontrolü
    cursor.execute("SELECT COUNT(*) FROM kasalar")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO kasalar (kod, ad, para_birimi, bakiye, aciklama) 
        VALUES ('KAS-01', 'Merkez TL Kasası', 'TRY', 0.0, 'Ana Nakit Kasa')
        """)
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM bankalar")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO bankalar (banka_adi, sube_adi, hesap_no, iban, para_birimi, bakiye, aciklama) 
        VALUES ('Garanti BBVA', 'Afyon Şubesi', '1234567', 'TR12 0006 2000 0001 2345 6789 01', 'TRY', 0.0, 'Ana Ticari Mevduat Hesabı')
        """)
        conn.commit()

    conn.close()

def seed_sample_data():
    """Kullanıcının sistemi anında deneyebilmesi için gerçekçi örnek veriler yükler."""
    conn = get_db()
    cursor = conn.cursor()

    # Daha önce eklenmiş mi kontrol et
    cursor.execute("SELECT COUNT(*) FROM cariler")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    today = date.today().strftime("%Y-%m-%d")

    # 1. Örnek Cariler
    cariler = [
        ('CARI-001', 'Anadolu İnşaat Taahhüt A.Ş.', 'MUSTERI', 'Ahmet Yılmaz', 'Afyon V.D.', '1234567890', '', '0532 111 2233', 'ahmet@anadoluinsaat.com', 'Mermerciler Sitesi No: 12', 'Afyonkarahisar', 'Merkez', 'Büyük ölçekli proje müşterimiz'),
        ('CARI-002', 'Ege Doğaltaş ve Mermer İhracat Ltd.', 'MUSTERI', 'Mehmet Kaya', 'Konak V.D.', '2345678901', '', '0533 222 3344', 'mehmet@egedogaltas.com', 'Liman Cad. No: 45', 'İzmir', 'Alsancak', 'Düzenli plaka ve fayans alıcısı'),
        ('CARI-003', 'Elmas Kesici Takımlar Sanayi A.Ş.', 'TEDARIKCI', 'Kemal Demir', 'Ostim V.D.', '3456789012', '', '0312 385 0000', 'siparis@elmaskesici.com', 'Ostim Sanayi 100. Yıl Bulvarı', 'Ankara', 'Yenimahalle', 'Katrak lamaları ve elmas tel tedarikçisi'),
        ('CARI-004', 'Akdeniz Lojistik ve Nakliyat Ltd.', 'TEDARIKCI', 'Süleyman Çelik', 'Akdeniz V.D.', '4567890123', '', '0542 444 5566', 'operasyon@akdenizlojistik.com', 'Liman Yolu No: 8', 'Mersin', 'Akdeniz', 'Konteyner ve tır nakliye hizmeti'),
        ('CARI-005', 'Toros Madencilik ve Ocak İşletmeleri', 'TEDARIKCI', 'Murat Yıldız', 'Bucak V.D.', '5678901234', '', '0248 325 1122', 'info@torosmaden.com', 'Mermer Ocakları Bölgesi', 'Burdur', 'Bucak', 'Ham bej blok mermer tedariki')
    ]
    for c in cariler:
        cursor.execute("""
        INSERT INTO cariler (kod, unvan, tip, yetkili_kisi, vergi_dairesi, vergi_no, tckn, telefon, eposta, adres, il, ilce, notlar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, c)

    # 2. Örnek Stok / Hizmetler
    stoklar = [
        ('STK-001', 'Afyon Beyazı Mermer Plaka (2cm Cilalı)', 'URUN', 'm²', 850.0, 1450.0, 20, 240.0, 50.0),
        ('STK-002', 'Traverten Classic Cross-Cut Fayans (30x60x1.2)', 'URUN', 'm²', 420.0, 780.0, 20, 520.0, 100.0),
        ('STK-003', 'Burdur Beji Honlu Plaka (3cm)', 'URUN', 'm²', 950.0, 1650.0, 20, 180.0, 40.0),
        ('STK-004', 'Mermer Masa Tablası (100x200cm Toros Siyah)', 'URUN', 'Adet', 3500.0, 6800.0, 20, 15.0, 3.0),
        ('STK-005', 'Özel Ebatlama ve Pah Kırma İşçiliği', 'HIZMET', 'Metre', 0.0, 85.0, 20, 0.0, 0.0),
        ('STK-006', 'Vinç ile Yükleme ve İndirme Hizmeti', 'HIZMET', 'Saat', 0.0, 1200.0, 20, 0.0, 0.0)
    ]
    for s in stoklar:
        cursor.execute("""
        INSERT INTO stoklar (kod, ad, tip, birim, alis_fiyati, satis_fiyati, kdv_orani, stok_miktari, kritik_stok)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, s)

    # 3. İkinci Banka Hesabı Ekle
    cursor.execute("""
    INSERT INTO bankalar (banka_adi, sube_adi, hesap_no, iban, para_birimi, bakiye, aciklama)
    VALUES ('Türkiye İş Bankası', 'Afyon Sanayi Şubesi', '4587123', 'TR45 0006 4000 0002 9876 5432 01', 'TRY', 0.0, 'Maaş ve Masraf Hesabı')
    """)

    # 4. Örnek Satış Faturası (Anadolu İnşaat)
    cursor.execute("""
        INSERT INTO faturalar (
            fatura_no, fatura_turu, fatura_tarihi, vade_tarihi, cari_id,
            ara_toplam, iskonto_orani, iskonto_tutari, kdv_toplam, genel_toplam,
            odenen_tutar, kalan_tutar, odeme_durumu, aciklama
        ) VALUES (
            'SF2026000001', 'SATIS', ?, ?, 1,
            29000.0, 0.0, 0.0, 5800.0, 34800.0,
            10000.0, 24800.0, 'KISMI', 'Afyon beyazı cilalı plaka satışı'
        )
    """, (today, today))
    fat1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO fatura_kalemleri (fatura_id, stok_id, aciklama, miktar, birim, birim_fiyat, kdv_orani, kdv_tutari, satir_toplami)
        VALUES (?, 1, 'Afyon Beyazı Mermer Plaka (2cm Cilalı)', 20, 'm²', 1450.0, 20, 5800.0, 34800.0)
    """, (fat1_id,))

    # Cari Hareketi (Satış Faturası Borcu)
    cursor.execute("""
        INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_fatura_id)
        VALUES (1, ?, 'FATURA_SATIS', 'SF2026000001', 34800.0, 0.0, 'Satış Faturası No: SF2026000001', ?)
    """, (today, fat1_id))

    # Kısmi Tahsilat (Banka Havalesi 10.000 TL)
    cursor.execute("""
        INSERT INTO kasa_banka_hareketleri (islem_tarihi, islem_turu, banka_id, cari_id, fatura_id, tutar, aciklama, evrak_no)
        VALUES (?, 'BANKA_GELEN_HAVALE', 1, 1, ?, 10000.0, 'Fatura Kısmi Havale Tahsilatı', 'EFT-88912')
    """, (today, fat1_id))
    hareket1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
        VALUES (1, ?, 'HAVALE_TAHSILAT', 'EFT-88912', 0.0, 10000.0, 'Gelen Havale/EFT', ?)
    """, (today, hareket1_id))

    # 6. Örnek Alış Faturası (Elmas Kesici Takımlar)
    cursor.execute("""
        INSERT INTO faturalar (
            fatura_no, fatura_turu, fatura_tarihi, vade_tarihi, cari_id,
            ara_toplam, iskonto_orani, iskonto_tutari, kdv_toplam, genel_toplam,
            odenen_tutar, kalan_tutar, odeme_durumu, aciklama
        ) VALUES (
            'AF2026000001', 'ALIS', ?, ?, 3,
            12000.0, 0.0, 0.0, 2400.0, 14400.0,
            0.0, 14400.0, 'BEKLIYOR', 'Katrak laması ve elmas testere alımı'
        )
    """, (today, today))
    fat2_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO fatura_kalemleri (fatura_id, stok_id, aciklama, miktar, birim, birim_fiyat, kdv_orani, kdv_tutari, satir_toplami)
        VALUES (?, NULL, 'Katrak Laması Seti', 2, 'Adet', 6000.0, 20, 2400.0, 14400.0)
    """, (fat2_id,))

    cursor.execute("""
        INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_fatura_id)
        VALUES (3, ?, 'FATURA_ALIS', 'AF2026000001', 0.0, 14400.0, 'Alış Faturası No: AF2026000001', ?)
    """, (today, fat2_id))

    # 7. Örnek Çekler
    from datetime import timedelta
    vade_yaklasik = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    vade_gecmis = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    vade_gelecek = (date.today() + timedelta(days=25)).strftime("%Y-%m-%d")

    # Müşteriden Alınan Çek 1 (Vadesi Yaklaşan)
    cursor.execute("""
        INSERT INTO cekler (cek_turu, cek_no, vade_tarihi, giris_tarihi, tutar, banka_adi, sube_adi, kesideci, cari_id, durum, aciklama)
        VALUES ('ALINAN', 'CK-44589', ?, ?, 45000.0, 'Garanti BBVA', 'Alsancak Şb', 'Ege Doğaltaş Ltd.', 2, 'PORTFOYDE', 'Plaka siparişi avans çeki')
    """, (vade_yaklasik, today))
    cek1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_cek_id)
        VALUES (2, ?, 'CEK_GIRIS', 'CK-44589', 0.0, 45000.0, 'Alınan Çek No: CK-44589', ?)
    """, (today, cek1_id))

    # Müşteriden Alınan Çek 2 (Vadesi Geçmiş - Uyarı için)
    cursor.execute("""
        INSERT INTO cekler (cek_turu, cek_no, vade_tarihi, giris_tarihi, tutar, banka_adi, sube_adi, kesideci, cari_id, durum, aciklama)
        VALUES ('ALINAN', 'CK-11204', ?, ?, 18500.0, 'Yapı Kredi', 'Afyon Şb', 'Anadolu İnşaat', 1, 'PORTFOYDE', 'Tahsili gecikmiş müşteri çeki')
    """, (vade_gecmis, today))
    cek2_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_cek_id)
        VALUES (1, ?, 'CEK_GIRIS', 'CK-11204', 0.0, 18500.0, 'Alınan Çek No: CK-11204', ?)
    """, (today, cek2_id))

    # Tedarikçiye Verilen Çek (Toros Madencilik)
    cursor.execute("""
        INSERT INTO cekler (cek_turu, cek_no, vade_tarihi, giris_tarihi, tutar, banka_adi, sube_adi, kesideci, cari_id, durum, aciklama)
        VALUES ('VERILEN', 'VCK-8812', ?, ?, 60000.0, 'Garanti BBVA', 'Afyon Şb', 'Özerler Mermer', 5, 'PORTFOYDE', 'Blok mermer alımı vadeli firma çekimiz')
    """, (vade_gelecek, today))
    cek3_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_cek_id)
        VALUES (5, ?, 'CEK_CIKIS', 'VCK-8812', 60000.0, 0.0, 'Verilen Firma Çeki No: VCK-8812', ?)
    """, (today, cek3_id))

    # Carilerin bakiyelerini senkronize et
    for c_id in [1, 2, 3, 4, 5]:
        cursor.execute("""
            SELECT COALESCE(SUM(borc), 0.0) as top_borc, COALESCE(SUM(alacak), 0.0) as top_alacak
            FROM cari_hareketler WHERE cari_id = ?
        """, (c_id,))
        b_res = cursor.fetchone()
        tb = float(b_res['top_borc'])
        ta = float(b_res['top_alacak'])
        cursor.execute("UPDATE cariler SET borc = ?, alacak = ?, bakiye = ? WHERE id = ?", (tb, ta, tb - ta, c_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_sample_data()
    print("Veritabanı başarıyla oluşturuldu ve hazırlandı!")
