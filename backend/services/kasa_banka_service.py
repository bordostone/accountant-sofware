from datetime import date
from backend.database import get_db
from backend.models import KasaCreate, BankaCreate, OdemeTahsilatCreate
from backend.services.cari_service import recalculate_cari_bakiye

def list_kasalar():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT k.id, k.kod, k.ad, k.para_birimi, k.aciklama, k.created_at,
               COALESCE((
                   SELECT SUM(CASE 
                       WHEN islem_turu IN ('KASA_TAHSILAT', 'BANKA_KASA_VIRMAN', 'CEK_TAHSILATI_KASA') THEN tutar
                       WHEN islem_turu IN ('KASA_ODEME', 'KASA_BANKA_VIRMAN', 'MASRAF_ODEME') THEN -tutar
                       ELSE 0.0 END)
                   FROM kasa_banka_hareketleri
                   WHERE kasa_id = k.id
               ), 0.0) as bakiye,
               (SELECT COUNT(*) FROM kasa_banka_hareketleri WHERE kasa_id = k.id) as islem_sayisi
        FROM kasalar k
        ORDER BY k.id ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        cursor.execute("UPDATE kasalar SET bakiye = ? WHERE id = ?", (r["bakiye"], r["id"]))
    conn.commit()
    conn.close()
    return rows

def create_kasa(data: KasaCreate):
    conn = get_db()
    cursor = conn.cursor()
    kod = data.kod or f"KAS-{cursor.execute('SELECT COUNT(*) FROM kasalar').fetchone()[0] + 1:02d}"
    cursor.execute("""
        INSERT INTO kasalar (kod, ad, para_birimi, aciklama)
        VALUES (?, ?, ?, ?)
    """, (kod, data.ad, data.para_birimi, data.aciklama))
    kasa_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": kasa_id, "kod": kod, "ad": data.ad}

def get_kasa(kasa_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kasalar WHERE id = ?", (kasa_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_kasa(kasa_id: int, data: KasaCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE kasalar SET
            ad = ?, para_birimi = ?, aciklama = ?
        WHERE id = ?
    """, (data.ad, data.para_birimi or "TRY", data.aciklama or "", kasa_id))
    conn.commit()
    conn.close()
    return {"id": kasa_id, "ad": data.ad}

def delete_kasa(kasa_id: int, cascade: bool = True):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM kasa_banka_hareketleri WHERE kasa_id = ?", (kasa_id,))
    mov_count = cursor.fetchone()[0]
    if mov_count > 0:
        cursor.execute("DELETE FROM cari_hareketler WHERE ref_hareket_id IN (SELECT id FROM kasa_banka_hareketleri WHERE kasa_id = ?)", (kasa_id,))
        cursor.execute("DELETE FROM kasa_banka_hareketleri WHERE kasa_id = ?", (kasa_id,))

    cursor.execute("UPDATE cekler SET tahsil_kasa_id = NULL WHERE tahsil_kasa_id = ?", (kasa_id,))
    cursor.execute("DELETE FROM kasalar WHERE id = ?", (kasa_id,))
    conn.commit()
    conn.close()
    return True

def list_bankalar():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.banka_adi, b.sube_adi, b.hesap_no, b.iban, b.para_birimi, b.aciklama, b.created_at,
               COALESCE((
                   SELECT SUM(CASE 
                       WHEN islem_turu IN ('BANKA_GELEN_HAVALE', 'KASA_BANKA_VIRMAN', 'CEK_TAHSILATI_BANKA', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT') THEN tutar
                       WHEN islem_turu IN ('BANKA_GIDEN_HAVALE', 'BANKA_KASA_VIRMAN', 'MASRAF_ODEME') THEN -tutar
                       ELSE 0.0 END)
                   FROM kasa_banka_hareketleri
                   WHERE banka_id = b.id
               ), 0.0) as bakiye,
               (SELECT COUNT(*) FROM kasa_banka_hareketleri WHERE banka_id = b.id) as islem_sayisi
        FROM bankalar b
        ORDER BY b.id ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        cursor.execute("UPDATE bankalar SET bakiye = ? WHERE id = ?", (r["bakiye"], r["id"]))
    conn.commit()
    conn.close()
    return rows

def get_banka(banka_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bankalar WHERE id = ?", (banka_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_banka(data: BankaCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bankalar (banka_adi, sube_adi, hesap_no, iban, para_birimi, aciklama)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.banka_adi, data.sube_adi, data.hesap_no, data.iban, data.para_birimi, data.aciklama))
    banka_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": banka_id, "banka_adi": data.banka_adi, "iban": data.iban}

def update_banka(banka_id: int, data: BankaCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bankalar SET
            banka_adi = ?, sube_adi = ?, hesap_no = ?, iban = ?,
            para_birimi = ?, aciklama = ?
        WHERE id = ?
    """, (data.banka_adi, data.sube_adi or "", data.hesap_no or "", data.iban, data.para_birimi or "TRY", data.aciklama or "", banka_id))
    conn.commit()
    conn.close()
    return {"id": banka_id, "banka_adi": data.banka_adi, "iban": data.iban}

def delete_banka(banka_id: int, cascade: bool = True):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM kasa_banka_hareketleri WHERE banka_id = ?", (banka_id,))
    mov_count = cursor.fetchone()[0]
    if mov_count > 0:
        cursor.execute("DELETE FROM cari_hareketler WHERE ref_hareket_id IN (SELECT id FROM kasa_banka_hareketleri WHERE banka_id = ?)", (banka_id,))
        cursor.execute("DELETE FROM kasa_banka_hareketleri WHERE banka_id = ?", (banka_id,))

    cursor.execute("UPDATE cekler SET tahsil_banka_id = NULL WHERE tahsil_banka_id = ?", (banka_id,))
    cursor.execute("DELETE FROM bankalar WHERE id = ?", (banka_id,))
    conn.commit()
    conn.close()
    return True

def list_hareketler(islem_turu: str = None, cari_id: int = None, kasa_id: int = None, banka_id: int = None, baslangic: str = None, bitis: str = None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT kbh.*, 
               k.ad as kasa_adi, 
               b.banka_adi, b.iban as banka_iban,
               c.unvan as cari_unvan, c.kod as cari_kod,
               f.fatura_no
        FROM kasa_banka_hareketleri kbh
        LEFT JOIN kasalar k ON kbh.kasa_id = k.id
        LEFT JOIN bankalar b ON kbh.banka_id = b.id
        LEFT JOIN cariler c ON kbh.cari_id = c.id
        LEFT JOIN faturalar f ON kbh.fatura_id = f.id
        WHERE 1=1
    """
    params = []
    if islem_turu and isinstance(islem_turu, str):
        query += " AND kbh.islem_turu = ?"
        params.append(islem_turu)
    if cari_id and not str(type(cari_id)).endswith("Query'>"):
        query += " AND kbh.cari_id = ?"
        params.append(int(cari_id))
    if kasa_id and not str(type(kasa_id)).endswith("Query'>"):
        query += " AND kbh.kasa_id = ?"
        params.append(int(kasa_id))
    if banka_id and not str(type(banka_id)).endswith("Query'>"):
        query += " AND kbh.banka_id = ?"
        params.append(int(banka_id))
    if baslangic and isinstance(baslangic, str):
        query += " AND kbh.islem_tarihi >= ?"
        params.append(baslangic)
    if bitis and isinstance(bitis, str):
        query += " AND kbh.islem_tarihi <= ?"
        params.append(bitis)

    query += " ORDER BY kbh.islem_tarihi DESC, kbh.id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def create_islem(data: OdemeTahsilatCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    tutar = abs(float(data.tutar))
    if tutar <= 0:
        conn.close()
        raise ValueError("Tutar 0'dan büyük olmalıdır.")

    # 1. Kasa/Banka Hareketi Ekle
    cursor.execute("""
        INSERT INTO kasa_banka_hareketleri (
            islem_tarihi, islem_turu, kasa_id, banka_id, cari_id, fatura_id, tutar, aciklama, evrak_no
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.tarih, data.islem_turu, data.kasa_id, data.banka_id, data.cari_id, data.fatura_id,
        tutar, data.aciklama, data.evrak_no
    ))
    islem_id = cursor.lastrowid

    # 2. Türüne göre bakiye ve cari hareketi işle
    if data.islem_turu == "KASA_TAHSILAT":
        # Kasaya para girdi
        if not data.kasa_id:
            raise ValueError("Kasa seçilmelidir.")
        cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.kasa_id))
        
        # Cari varsa Alacaklandır (Müşteri ödedi, borcu kapandı)
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'NAKIT_TAHSILAT', ?, 0.0, ?, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Nakit Tahsilat", islem_id))
            recalculate_cari_bakiye(conn, data.cari_id)

    elif data.islem_turu == "KASA_ODEME":
        # Kasadan para çıktı
        if not data.kasa_id:
            raise ValueError("Kasa seçilmelidir.")
        cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.kasa_id))
        
        # Cari varsa Borçlandır (Tedarikçiye ödedik, borcumuz azaldı)
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'NAKIT_ODEME', ?, ?, 0.0, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Nakit Ödeme", islem_id))
            recalculate_cari_bakiye(conn, data.cari_id)

    elif data.islem_turu == "BANKA_GELEN_HAVALE":
        # Bankaya para girdi
        if not data.banka_id:
            raise ValueError("Banka hesabı seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.banka_id))
        
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'HAVALE_TAHSILAT', ?, 0.0, ?, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Gelen Havale/EFT", islem_id))
            recalculate_cari_bakiye(conn, data.cari_id)

    elif data.islem_turu in ("KREDI_KARTI_TAHSILAT", "POS_TAHSILAT"):
        # Kredi Kartı ile Tahsilat (Banka / POS Hesabına Giriş)
        if not data.banka_id:
            cursor.execute("SELECT id FROM bankalar ORDER BY id ASC LIMIT 1")
            first_b = cursor.fetchone()
            if first_b:
                data.banka_id = first_b[0]
                cursor.execute("UPDATE kasa_banka_hareketleri SET banka_id = ? WHERE id = ?", (data.banka_id, islem_id))
            else:
                raise ValueError("Kredi kartı tahsilatının aktarılacağı banka / POS hesabı seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.banka_id))

        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'KREDI_KARTI_TAHSILAT', ?, 0.0, ?, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Kredi Kartı ile Tahsilat", islem_id))
            recalculate_cari_bakiye(conn, data.cari_id)

    elif data.islem_turu == "BANKA_GIDEN_HAVALE":
        # Bankadan para çıktı
        if not data.banka_id:
            raise ValueError("Banka hesabı seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.banka_id))
        
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'HAVALE_ODEME', ?, ?, 0.0, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Giden Havale/EFT", islem_id))
            recalculate_cari_bakiye(conn, data.cari_id)

    elif data.islem_turu == "KASA_BANKA_VIRMAN":
        # Kasadan Bankaya para aktarımı (Kasa -, Banka +)
        if not data.kasa_id or not data.banka_id:
            raise ValueError("Hem kasa hem banka hesabı seçilmelidir.")
        cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.kasa_id))
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.banka_id))

    elif data.islem_turu == "BANKA_KASA_VIRMAN":
        # Bankadan Kasaya para çekme (Banka -, Kasa +)
        if not data.kasa_id or not data.banka_id:
            raise ValueError("Hem kasa hem banka hesabı seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.banka_id))
        cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.kasa_id))

    elif data.islem_turu == "MASRAF_ODEME":
        if data.kasa_id:
            cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.kasa_id))
        elif data.banka_id:
            cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.banka_id))

    # 3. İlgili Fatura Varsa Durumunu Güncelle
    if data.fatura_id:
        cursor.execute("SELECT genel_toplam, odenen_tutar FROM faturalar WHERE id = ?", (data.fatura_id,))
        fat = cursor.fetchone()
        if fat:
            yeni_odenen = float(fat['odenen_tutar']) + tutar
            genel_top = float(fat['genel_toplam'])
            kalan = max(0.0, round(genel_top - yeni_odenen, 2))
            
            durum = 'ODENDI' if kalan <= 0.01 else 'KISMI'
            cursor.execute("""
                UPDATE faturalar SET odenen_tutar = ?, kalan_tutar = ?, odeme_durumu = ?
                WHERE id = ?
            """, (yeni_odenen, kalan, durum, data.fatura_id))

    conn.commit()
    conn.close()
    return {"success": True, "islem_id": islem_id}

def get_hareket(hareket_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT kbh.*, 
               k.ad as kasa_adi, 
               b.banka_adi, b.iban as banka_iban,
               c.unvan as cari_unvan, c.kod as cari_kod,
               f.fatura_no
        FROM kasa_banka_hareketleri kbh
        LEFT JOIN kasalar k ON kbh.kasa_id = k.id
        LEFT JOIN bankalar b ON kbh.banka_id = b.id
        LEFT JOIN cariler c ON kbh.cari_id = c.id
        LEFT JOIN faturalar f ON kbh.fatura_id = f.id
        WHERE kbh.id = ?
    """, (hareket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_islem(islem_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kasa_banka_hareketleri WHERE id = ?", (islem_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Kasa/Banka hareket kaydı bulunamadı.")

    tur = row['islem_turu']
    tutar = float(row['tutar'])
    kasa_id = row['kasa_id']
    banka_id = row['banka_id']
    cari_id = row['cari_id']
    fatura_id = row['fatura_id']

    # 1. Eski bakiye etkisini geri al
    if tur in ("KASA_TAHSILAT", "CEK_TAHSILATI_KASA") and kasa_id:
        cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, kasa_id))
    elif tur == "KASA_ODEME" and kasa_id:
        cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, kasa_id))
    elif tur in ("BANKA_GELEN_HAVALE", "CEK_TAHSILATI_BANKA", "KREDI_KARTI_TAHSILAT", "POS_TAHSILAT") and banka_id:
        cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, banka_id))
    elif tur == "BANKA_GIDEN_HAVALE" and banka_id:
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, banka_id))
    elif tur == "KASA_BANKA_VIRMAN":
        if kasa_id: cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, kasa_id))
        if banka_id: cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, banka_id))
    elif tur == "BANKA_KASA_VIRMAN":
        if banka_id: cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, banka_id))
        if kasa_id: cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, kasa_id))
    elif tur == "MASRAF_ODEME":
        if kasa_id: cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, kasa_id))
        elif banka_id: cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, banka_id))

    # 2. Bağlı cari hareketini sil ve cari bakiyesini güncelle
    cursor.execute("DELETE FROM cari_hareketler WHERE ref_hareket_id = ?", (islem_id,))
    if cari_id:
        recalculate_cari_bakiye(conn, cari_id)

    # 3. Bağlı fatura varsa durumunu güncelle
    if fatura_id:
        cursor.execute("SELECT genel_toplam, odenen_tutar FROM faturalar WHERE id = ?", (fatura_id,))
        fat = cursor.fetchone()
        if fat:
            yeni_odenen = max(0.0, float(fat['odenen_tutar']) - tutar)
            genel_top = float(fat['genel_toplam'])
            kalan = max(0.0, round(genel_top - yeni_odenen, 2))
            durum = 'BEKLIYOR' if yeni_odenen <= 0.01 else ('ODENDI' if kalan <= 0.01 else 'KISMI')
            cursor.execute("UPDATE faturalar SET odenen_tutar = ?, kalan_tutar = ?, odeme_durumu = ? WHERE id = ?", (yeni_odenen, kalan, durum, fatura_id))

    # 4. Kasa/banka hareketini sil
    cursor.execute("DELETE FROM kasa_banka_hareketleri WHERE id = ?", (islem_id,))
    conn.commit()
    conn.close()
    return True

def update_islem(islem_id: int, data: OdemeTahsilatCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kasa_banka_hareketleri WHERE id = ?", (islem_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        raise ValueError("Kasa/Banka hareket kaydı bulunamadı.")

    # 1. Eski kaydın etkilerini geri al
    old_tur = old_row['islem_turu']
    old_tutar = float(old_row['tutar'])
    old_kasa_id = old_row['kasa_id']
    old_banka_id = old_row['banka_id']
    old_cari_id = old_row['cari_id']
    old_fatura_id = old_row['fatura_id']

    if old_tur in ("KASA_TAHSILAT", "CEK_TAHSILATI_KASA") and old_kasa_id:
        cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (old_tutar, old_kasa_id))
    elif old_tur == "KASA_ODEME" and old_kasa_id:
        cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (old_tutar, old_kasa_id))
    elif old_tur in ("BANKA_GELEN_HAVALE", "CEK_TAHSILATI_BANKA", "KREDI_KARTI_TAHSILAT", "POS_TAHSILAT") and old_banka_id:
        cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (old_tutar, old_banka_id))
    elif old_tur == "BANKA_GIDEN_HAVALE" and old_banka_id:
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (old_tutar, old_banka_id))
    elif old_tur == "KASA_BANKA_VIRMAN":
        if old_kasa_id: cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (old_tutar, old_kasa_id))
        if old_banka_id: cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (old_tutar, old_banka_id))
    elif old_tur == "BANKA_KASA_VIRMAN":
        if old_banka_id: cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (old_tutar, old_banka_id))
        if old_kasa_id: cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (old_tutar, old_kasa_id))
    elif old_tur == "MASRAF_ODEME":
        if old_kasa_id: cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (old_tutar, old_kasa_id))
        elif old_banka_id: cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (old_tutar, old_banka_id))

    # Eski cari hareketini sil (aşağıda güncel hali yeniden eklenecek)
    cursor.execute("DELETE FROM cari_hareketler WHERE ref_hareket_id = ?", (islem_id,))

    if old_fatura_id:
        cursor.execute("SELECT genel_toplam, odenen_tutar FROM faturalar WHERE id = ?", (old_fatura_id,))
        fat = cursor.fetchone()
        if fat:
            yeni_odenen = max(0.0, float(fat['odenen_tutar']) - old_tutar)
            genel_top = float(fat['genel_toplam'])
            kalan = max(0.0, round(genel_top - yeni_odenen, 2))
            durum = 'BEKLIYOR' if yeni_odenen <= 0.01 else ('ODENDI' if kalan <= 0.01 else 'KISMI')
            cursor.execute("UPDATE faturalar SET odenen_tutar = ?, kalan_tutar = ?, odeme_durumu = ? WHERE id = ?", (yeni_odenen, kalan, durum, old_fatura_id))

    # 2. Şimdi yeni verileri uygula
    tutar = abs(float(data.tutar))
    if tutar <= 0:
        conn.close()
        raise ValueError("Tutar 0'dan büyük olmalıdır.")

    cursor.execute("""
        UPDATE kasa_banka_hareketleri SET
            islem_tarihi = ?,
            islem_turu = ?,
            kasa_id = ?,
            banka_id = ?,
            cari_id = ?,
            fatura_id = ?,
            tutar = ?,
            aciklama = ?,
            evrak_no = ?
        WHERE id = ?
    """, (
        data.tarih, data.islem_turu, data.kasa_id, data.banka_id, data.cari_id, data.fatura_id,
        tutar, data.aciklama, data.evrak_no, islem_id
    ))

    # Yeni bakiye etkilerini uygula
    if data.islem_turu == "KASA_TAHSILAT":
        if not data.kasa_id: raise ValueError("Kasa seçilmelidir.")
        cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.kasa_id))
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'NAKIT_TAHSILAT', ?, 0.0, ?, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Nakit Tahsilat", islem_id))
    elif data.islem_turu == "KASA_ODEME":
        if not data.kasa_id: raise ValueError("Kasa seçilmelidir.")
        cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.kasa_id))
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'NAKIT_ODEME', ?, ?, 0.0, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Nakit Ödeme", islem_id))
    elif data.islem_turu == "BANKA_GELEN_HAVALE":
        if not data.banka_id: raise ValueError("Banka hesabı seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.banka_id))
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'HAVALE_TAHSILAT', ?, 0.0, ?, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Gelen Havale/EFT", islem_id))
    elif data.islem_turu in ("KREDI_KARTI_TAHSILAT", "POS_TAHSILAT"):
        if not data.banka_id:
            cursor.execute("SELECT id FROM bankalar ORDER BY id ASC LIMIT 1")
            first_b = cursor.fetchone()
            if first_b:
                data.banka_id = first_b[0]
                cursor.execute("UPDATE kasa_banka_hareketleri SET banka_id = ? WHERE id = ?", (data.banka_id, islem_id))
            else:
                raise ValueError("Banka / POS hesabı seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.banka_id))
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'KREDI_KARTI_TAHSILAT', ?, 0.0, ?, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Kredi Kartı ile Tahsilat", islem_id))
    elif data.islem_turu == "BANKA_GIDEN_HAVALE":
        if not data.banka_id: raise ValueError("Banka hesabı seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.banka_id))
        if data.cari_id:
            cursor.execute("""
                INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_hareket_id)
                VALUES (?, ?, 'HAVALE_ODEME', ?, ?, 0.0, ?, ?)
            """, (data.cari_id, data.tarih, data.evrak_no, tutar, data.aciklama or "Giden Havale/EFT", islem_id))
    elif data.islem_turu == "KASA_BANKA_VIRMAN":
        if not data.kasa_id or not data.banka_id: raise ValueError("Hem kasa hem banka seçilmelidir.")
        cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.kasa_id))
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.banka_id))
    elif data.islem_turu == "BANKA_KASA_VIRMAN":
        if not data.kasa_id or not data.banka_id: raise ValueError("Hem kasa hem banka seçilmelidir.")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.banka_id))
        cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.kasa_id))
    elif data.islem_turu == "MASRAF_ODEME":
        if data.kasa_id: cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.kasa_id))
        elif data.banka_id: cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, data.banka_id))

    # Cari bakiye güncellemeleri
    affected_caris = set(filter(None, [old_cari_id, data.cari_id]))
    for cid in affected_caris:
        recalculate_cari_bakiye(conn, cid)

    # Fatura bakiye güncellemesi
    if data.fatura_id:
        cursor.execute("SELECT genel_toplam, odenen_tutar FROM faturalar WHERE id = ?", (data.fatura_id,))
        fat = cursor.fetchone()
        if fat:
            yeni_odenen = float(fat['odenen_tutar']) + tutar
            genel_top = float(fat['genel_toplam'])
            kalan = max(0.0, round(genel_top - yeni_odenen, 2))
            durum = 'ODENDI' if kalan <= 0.01 else 'KISMI'
            cursor.execute("UPDATE faturalar SET odenen_tutar = ?, kalan_tutar = ?, odeme_durumu = ? WHERE id = ?", (yeni_odenen, kalan, durum, data.fatura_id))

    conn.commit()
    conn.close()
    return {"success": True, "islem_id": islem_id}

