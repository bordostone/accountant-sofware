from datetime import date
from backend.database import get_db
from backend.models import CariCreate, CariUpdate, CariHareketCreate

def generate_cari_kod(conn) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cariler ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    next_id = (row['id'] + 1) if row else 1
    return f"CAR-{next_id:04d}"

def list_cariler(tip: str = None, search: str = None, durum: str = None, bakiye_durumu: str = None, sort_by: str = "unvan_asc"):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT c.*,
            (SELECT COUNT(*) FROM faturalar WHERE cari_id = c.id) as fatura_sayisi,
            (SELECT COUNT(*) FROM cekler WHERE cari_id = c.id) as cek_sayisi
        FROM cariler c
        WHERE 1=1
    """
    params = []
    if tip == "PERSONEL":
        query += " AND c.is_personel = 1"
    elif tip and tip != "HEPSI":
        query += " AND c.tip = ?"
        params.append(tip)
    if durum:
        query += " AND c.durum = ?"
        params.append(durum)
    if search:
        query += " AND (c.unvan LIKE ? OR c.kod LIKE ? OR c.yetkili_kisi LIKE ? OR c.vergi_no LIKE ? OR c.telefon LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s])

    if bakiye_durumu == "BORCLU":
        query += " AND c.bakiye > 0.001"
    elif bakiye_durumu == "ALACAKLI":
        query += " AND c.bakiye < -0.001"
    elif bakiye_durumu == "SIFIR":
        query += " AND ABS(c.bakiye) <= 0.001"
    elif bakiye_durumu == "BAKIYELI":
        query += " AND ABS(c.bakiye) > 0.001"

    if sort_by == "bakiye_desc":
        query += " ORDER BY c.bakiye DESC"
    elif sort_by == "bakiye_asc":
        query += " ORDER BY c.bakiye ASC"
    elif sort_by == "unvan_desc":
        query += " ORDER BY c.unvan DESC"
    elif sort_by == "kod_asc":
        query += " ORDER BY c.kod ASC"
    elif sort_by == "borc_desc":
        query += " ORDER BY c.borc DESC"
    elif sort_by == "alacak_desc":
        query += " ORDER BY c.alacak DESC"
    else:
        query += " ORDER BY c.unvan ASC"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_cari(cari_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cariler WHERE id = ?", (cari_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_cari(data: CariCreate):
    conn = get_db()
    cursor = conn.cursor()
    kod = data.kod or generate_cari_kod(conn)
    is_pers = 1 if getattr(data, 'is_personel', False) else 0
    pers_gorev = getattr(data, 'personel_gorevi', '') or ''
    pers_dep = getattr(data, 'personel_departman', '') or ''
    
    cursor.execute("""
        INSERT INTO cariler (kod, unvan, tip, yetkili_kisi, vergi_dairesi, vergi_no, tckn, telefon, eposta, adres, il, ilce, notlar, is_personel, personel_gorevi, personel_departman)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        kod, data.unvan, data.tip, data.yetkili_kisi, data.vergi_dairesi, data.vergi_no,
        data.tckn, data.telefon, data.eposta, data.adres, data.il, data.ilce, data.notlar,
        is_pers, pers_gorev, pers_dep
    ))
    cari_id = cursor.lastrowid

    # Açılış bakiyesi varsa devir hareketi oluştur
    if data.acilis_bakiyesi and data.acilis_bakiyesi > 0:
        borc = data.acilis_bakiyesi if data.acilis_bakiye_turu == "BORC" else 0.0
        alacak = data.acilis_bakiyesi if data.acilis_bakiye_turu == "ALACAK" else 0.0
        today = date.today().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama)
            VALUES (?, ?, 'DEVIR', 'DEVIR-001', ?, ?, 'Açılış Devir Bakiyesi')
        """, (cari_id, today, borc, alacak))
        
        # Cari tablosunu güncelle
        recalculate_cari_bakiye(conn, cari_id)

    conn.commit()
    conn.close()
    return get_cari(cari_id)

def update_cari(cari_id: int, data: CariUpdate):
    conn = get_db()
    cursor = conn.cursor()
    is_pers = 1 if getattr(data, 'is_personel', False) else 0
    pers_gorev = getattr(data, 'personel_gorevi', '') or ''
    pers_dep = getattr(data, 'personel_departman', '') or ''

    cursor.execute("""
        UPDATE cariler SET
            unvan = ?, tip = ?, yetkili_kisi = ?, vergi_dairesi = ?, vergi_no = ?,
            tckn = ?, telefon = ?, eposta = ?, adres = ?, il = ?, ilce = ?,
            durum = ?, notlar = ?, is_personel = ?, personel_gorevi = ?, personel_departman = ?
        WHERE id = ?
    """, (
        data.unvan, data.tip, data.yetkili_kisi, data.vergi_dairesi, data.vergi_no,
        data.tckn, data.telefon, data.eposta, data.adres, data.il, data.ilce,
        data.durum, data.notlar, is_pers, pers_gorev, pers_dep, cari_id
    ))
    conn.commit()
    conn.close()
    return get_cari(cari_id)

def delete_cari(cari_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Bu cariye ait faturaların kalemlerini ve faturaları sil
    cursor.execute("SELECT id FROM faturalar WHERE cari_id = ?", (cari_id,))
    fatura_ids = [r['id'] for r in cursor.fetchall()]
    for fid in fatura_ids:
        cursor.execute("DELETE FROM fatura_kalemleri WHERE fatura_id = ?", (fid,))
    cursor.execute("DELETE FROM faturalar WHERE cari_id = ?", (cari_id,))
    
    # 2. Bu cariye ait çekleri sil
    cursor.execute("DELETE FROM cekler WHERE cari_id = ?", (cari_id,))
    
    # 3. Bu cariye ait kasa/banka hareketlerinin cari_id bağlantısını kaldır veya sil
    cursor.execute("DELETE FROM kasa_banka_hareketleri WHERE cari_id = ?", (cari_id,))
    
    # 4. Bu cariye ait cari hareketleri sil
    cursor.execute("DELETE FROM cari_hareketler WHERE cari_id = ?", (cari_id,))
    
    # 5. Cari kaydını sil
    cursor.execute("DELETE FROM cariler WHERE id = ?", (cari_id,))
    conn.commit()
    conn.close()
    return True

def recalculate_cari_bakiye(conn, cari_id: int):
    """Cari hesabın toplam borç, alacak ve net bakiyesini hesaplar."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(borc), 0.0) as top_borc, COALESCE(SUM(alacak), 0.0) as top_alacak
        FROM cari_hareketler
        WHERE cari_id = ?
    """, (cari_id,))
    res = cursor.fetchone()
    top_borc = float(res['top_borc'])
    top_alacak = float(res['top_alacak'])
    net_bakiye = top_borc - top_alacak  # Pozitifse Müşteri bize borçlu, Negatifse biz cariye borçluyuz

    cursor.execute("""
        UPDATE cariler SET
            borc = ?,
            alacak = ?,
            bakiye = ?
        WHERE id = ?
    """, (top_borc, top_alacak, net_bakiye, cari_id))

def get_cari_ekstre(cari_id: int, baslangic_tarihi: str = None, bitis_tarihi: str = None):
    """Cari hesap ekstresini yürüyen bakiye ile birlikte döner."""
    conn = get_db()
    cursor = conn.cursor()
    cari = get_cari(cari_id)
    if not cari:
        conn.close()
        return None

    # Devir bakiyesi hesapla (başlangıç tarihinden önceki hareketler toplamı)
    devir_bakiye = 0.0
    if baslangic_tarihi:
        cursor.execute("""
            SELECT COALESCE(SUM(borc), 0) - COALESCE(SUM(alacak), 0) as devir
            FROM cari_hareketler
            WHERE cari_id = ? AND tarih < ?
        """, (cari_id, baslangic_tarihi))
        row = cursor.fetchone()
        devir_bakiye = float(row['devir']) if row and row['devir'] else 0.0

    query = """
        SELECT * FROM cari_hareketler
        WHERE cari_id = ?
    """
    params = [cari_id]
    if baslangic_tarihi:
        query += " AND tarih >= ?"
        params.append(baslangic_tarihi)
    if bitis_tarihi:
        query += " AND tarih <= ?"
        params.append(bitis_tarihi)

    query += " ORDER BY tarih ASC, id ASC"
    cursor.execute(query, params)
    hareketler = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Yürüyen bakiye hesapla
    yuruyen = devir_bakiye
    islenmis_hareketler = []
    toplam_borc = 0.0
    toplam_alacak = 0.0

    for h in hareketler:
        borc = float(h['borc'] or 0.0)
        alacak = float(h['alacak'] or 0.0)
        toplam_borc += borc
        toplam_alacak += alacak
        yuruyen += (borc - alacak)
        
        durum_str = "(B) Borçlu" if yuruyen > 0.001 else ("(A) Alacaklı" if yuruyen < -0.001 else "0 Bakiye")
        h['yuruyen_bakiye'] = yuruyen
        h['bakiye_durumu'] = durum_str
        islenmis_hareketler.append(h)

    return {
        "cari": cari,
        "baslangic_tarihi": baslangic_tarihi,
        "bitis_tarihi": bitis_tarihi,
        "devir_bakiye": devir_bakiye,
        "hareketler": islenmis_hareketler,
        "toplam_borc": toplam_borc,
        "toplam_alacak": toplam_alacak,
        "son_bakiye": yuruyen,
        "son_bakiye_durumu": "(B) Borçlu" if yuruyen > 0.001 else ("(A) Alacaklı" if yuruyen < -0.001 else "0 Bakiye")
    }

def add_cari_hareket(data):
    conn = get_db()
    cursor = conn.cursor()
    cari = get_cari(data.cari_id)
    if not cari:
        conn.close()
        raise ValueError("Cari kart bulunamadı.")
    
    tutar = abs(float(data.tutar))
    if tutar <= 0:
        conn.close()
        raise ValueError("Tutar 0'dan büyük olmalıdır.")

    borc = 0.0
    alacak = 0.0

    if data.islem_turu == "BORC_DEKONTU":
        borc = tutar
    elif data.islem_turu == "ALACAK_DEKONTU":
        alacak = tutar
    elif data.islem_turu == "DEVIR":
        if data.hareket_yonu == "BORC":
            borc = tutar
        else:
            alacak = tutar
    else:
        if data.hareket_yonu == "ALACAK":
            alacak = tutar
        else:
            borc = tutar

    cursor.execute("""
        INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.cari_id, data.tarih, data.islem_turu, data.evrak_no or "", borc, alacak, data.aciklama))
    hareket_id = cursor.lastrowid

    recalculate_cari_bakiye(conn, data.cari_id)
    conn.commit()
    conn.close()
    return {"id": hareket_id, "cari_id": data.cari_id, "borc": borc, "alacak": alacak}

def delete_cari_hareket(hareket_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cari_hareketler WHERE id = ?", (hareket_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Hareket kaydı bulunamadı.")
    
    if row['ref_fatura_id'] or row['ref_hareket_id'] or row['ref_cek_id']:
        conn.close()
        raise ValueError("Bu hareket faturaya, banka/kasaya veya çeke bağlıdır. Buradan silinemez.")

    cari_id = row['cari_id']
    cursor.execute("DELETE FROM cari_hareketler WHERE id = ?", (hareket_id,))
    recalculate_cari_bakiye(conn, cari_id)
    conn.commit()
    conn.close()
    return True

def get_cari_hareket(hareket_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cari_hareketler WHERE id = ?", (hareket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_cari_hareket(hareket_id: int, data: CariHareketCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cari_hareketler WHERE id = ?", (hareket_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Hareket kaydı bulunamadı.")
    
    if row['ref_fatura_id'] or row['ref_hareket_id'] or row['ref_cek_id']:
        conn.close()
        raise ValueError("Bu hareket faturaya, banka/kasaya veya çeke bağlıdır. Buradan düzenlenemez.")

    old_cari_id = row['cari_id']
    tutar = abs(float(data.tutar))
    if tutar <= 0:
        conn.close()
        raise ValueError("Tutar 0'dan büyük olmalıdır.")

    borc = 0.0
    alacak = 0.0

    if data.islem_turu == "BORC_DEKONTU":
        borc = tutar
    elif data.islem_turu == "ALACAK_DEKONTU":
        alacak = tutar
    elif data.islem_turu == "DEVIR":
        if data.hareket_yonu == "BORC":
            borc = tutar
        else:
            alacak = tutar
    else:
        if data.hareket_yonu == "ALACAK":
            alacak = tutar
        else:
            borc = tutar

    cursor.execute("""
        UPDATE cari_hareketler SET
            cari_id = ?,
            tarih = ?,
            islem_turu = ?,
            evrak_no = ?,
            borc = ?,
            alacak = ?,
            aciklama = ?
        WHERE id = ?
    """, (data.cari_id, data.tarih, data.islem_turu, data.evrak_no or "", borc, alacak, data.aciklama, hareket_id))

    if old_cari_id != data.cari_id:
        recalculate_cari_bakiye(conn, old_cari_id)
    recalculate_cari_bakiye(conn, data.cari_id)

    conn.commit()
    conn.close()
    return {"id": hareket_id, "cari_id": data.cari_id, "borc": borc, "alacak": alacak, "tutar": tutar, "evrak_no": data.evrak_no, "islem_turu": data.islem_turu}


