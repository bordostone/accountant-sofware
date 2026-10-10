from datetime import datetime, date
from backend.database import get_db
from backend.models import CekCreate, CekDurumGuncelle
from backend.services.cari_service import recalculate_cari_bakiye

def list_cekler(cek_turu: str = None, durum: str = None, search: str = None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT ck.*, 
               c.unvan as cari_unvan, c.kod as cari_kod, c.telefon as cari_telefon,
               ciro_c.unvan as ciro_cari_unvan,
               k.ad as tahsil_kasa_adi,
               b.banka_adi as tahsil_banka_adi
        FROM cekler ck
        JOIN cariler c ON ck.cari_id = c.id
        LEFT JOIN cariler ciro_c ON ck.cirolanan_cari_id = ciro_c.id
        LEFT JOIN kasalar k ON ck.tahsil_kasa_id = k.id
        LEFT JOIN bankalar b ON ck.tahsil_banka_id = b.id
        WHERE 1=1
    """
    params = []
    if cek_turu:
        query += " AND ck.cek_turu = ?"
        params.append(cek_turu)
    if durum and durum != "HEPSI":
        query += " AND ck.durum = ?"
        params.append(durum)
    if search:
        query += " AND (ck.cek_no LIKE ? OR c.unvan LIKE ? OR ck.kesideci LIKE ? OR ck.banka_adi LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])

    query += " ORDER BY ck.vade_tarihi ASC, ck.id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Vade durumu analizi
    today = date.today()
    for row in rows:
        try:
            v_tarih = datetime.strptime(row['vade_tarihi'], "%Y-%m-%d").date()
            diff_days = (v_tarih - today).days
            row['kalan_gun'] = diff_days
            
            if row['durum'] in ('TAHSIL_EDILDI', 'CIROLANMIS', 'IADE_EDILDI'):
                row['vade_uyari'] = 'KAPANDI'
            elif diff_days < 0:
                row['vade_uyari'] = 'GECIKTI'  # Kırmızı
            elif diff_days == 0:
                row['vade_uyari'] = 'BUGUN'    # Turuncu
            elif diff_days <= 7:
                row['vade_uyari'] = 'YAKLASTI' # Sarı
            else:
                row['vade_uyari'] = 'NORMAL'   # Yeşil
        except Exception:
            row['kalan_gun'] = 0
            row['vade_uyari'] = 'NORMAL'

    return rows

def get_cek(cek_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ck.*, c.unvan as cari_unvan, c.kod as cari_kod
        FROM cekler ck
        JOIN cariler c ON ck.cari_id = c.id
        WHERE ck.id = ?
    """, (cek_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_cek(data: CekCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    tutar = abs(float(data.tutar))
    giris_tarihi = data.giris_tarihi or date.today().strftime("%Y-%m-%d")

    cursor.execute("""
        INSERT INTO cekler (
            cek_turu, cek_no, vade_tarihi, giris_tarihi, tutar,
            banka_adi, sube_adi, hesap_no, kesideci, cari_id, aciklama, durum
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PORTFOYDE')
    """, (
        data.cek_turu, data.cek_no, data.vade_tarihi, giris_tarihi, tutar,
        data.banka_adi, data.sube_adi, data.hesap_no, data.kesideci, data.cari_id, data.aciklama
    ))
    cek_id = cursor.lastrowid

    # Cari Hareketi:
    # ALINAN ÇEK: Müşteri çeki verdi, müşterinin borcu düşer (ALACAKLANIR)
    if data.cek_turu == "ALINAN":
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_cek_id)
            VALUES (?, ?, 'CEK_GIRIS', ?, 0.0, ?, ?, ?)
        """, (data.cari_id, giris_tarihi, data.cek_no, tutar, f"Alınan Müşteri Çeki No: {data.cek_no} (Vade: {data.vade_tarihi})", cek_id))
    else:
        # VERİLEN ÇEK: Tedarikçiye çek verdik, tedarikçiye borcumuz azaldı (BORÇLANIR)
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_cek_id)
            VALUES (?, ?, 'CEK_CIKIS', ?, ?, 0.0, ?, ?)
        """, (data.cari_id, giris_tarihi, data.cek_no, tutar, f"Verilen Firma Çeki No: {data.cek_no} (Vade: {data.vade_tarihi})", cek_id))

    recalculate_cari_bakiye(conn, data.cari_id)
    conn.commit()
    conn.close()
    return get_cek(cek_id)

def update_cek_durumu(cek_id: int, data: CekDurumGuncelle):
    conn = get_db()
    cursor = conn.cursor()
    cek = get_cek(cek_id)
    if not cek:
        conn.close()
        raise ValueError("Çek bulunamadı.")

    eski_durum = cek['durum']
    yeni = data.yeni_durum
    tarih = data.islem_tarihi or date.today().strftime("%Y-%m-%d")
    tutar = float(cek['tutar'])

    # 1. Tahsil Edildi
    if yeni == "TAHSIL_EDILDI":
        if data.kasa_id:
            cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.kasa_id))
            cursor.execute("""
                INSERT INTO kasa_banka_hareketleri (islem_tarihi, islem_turu, kasa_id, cek_id, tutar, aciklama, evrak_no)
                VALUES (?, 'CEK_TAHSILATI_KASA', ?, ?, ?, ?, ?)
            """, (tarih, data.kasa_id, cek_id, tutar, f"Çek Tahsilatı (Kasa) No: {cek['cek_no']}", cek['cek_no']))
        elif data.banka_id:
            cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, data.banka_id))
            cursor.execute("""
                INSERT INTO kasa_banka_hareketleri (islem_tarihi, islem_turu, banka_id, cek_id, tutar, aciklama, evrak_no)
                VALUES (?, 'CEK_TAHSILATI_BANKA', ?, ?, ?, ?, ?)
            """, (tarih, data.banka_id, cek_id, tutar, f"Çek Tahsilatı (Banka) No: {cek['cek_no']}", cek['cek_no']))
        else:
            raise ValueError("Tahsilatın yapılacağı Kasa veya Banka hesabı seçilmelidir.")

        cursor.execute("""
            UPDATE cekler SET durum = ?, tahsil_tarihi = ?, tahsil_kasa_id = ?, tahsil_banka_id = ?
            WHERE id = ?
        """, (yeni, tarih, data.kasa_id, data.banka_id, cek_id))

    # 2. Cirolandı (Başka bir cariye / tedarikçiye verildi)
    elif yeni == "CIROLANMIS":
        if not data.cirolanan_cari_id:
            raise ValueError("Çekin cirolandığı cari (tedarikçi) seçilmelidir.")
        
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_cek_id)
            VALUES (?, ?, 'CEK_CIKIS', ?, ?, 0.0, ?, ?)
        """, (data.cirolanan_cari_id, tarih, cek['cek_no'], tutar, f"Cirolanan Çek No: {cek['cek_no']} (Asıl Keşideci: {cek['kesideci'] or cek['cari_unvan']})", cek_id))
        
        recalculate_cari_bakiye(conn, data.cirolanan_cari_id)

        cursor.execute("""
            UPDATE cekler SET durum = ?, cirolanan_cari_id = ?
            WHERE id = ?
        """, (yeni, data.cirolanan_cari_id, cek_id))

    # 3. Karşılıksız Çıktı
    elif yeni == "KARSILIKSIZ":
        # Çek karşılıksız çıkınca müşterinin düşülen borcu müşteriye geri yansıtılır (BORÇLANIR)
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_cek_id)
            VALUES (?, ?, 'CEK_KARSILIKSIZ', ?, ?, 0.0, ?, ?)
        """, (cek['cari_id'], tarih, cek['cek_no'], tutar, f"Karşılıksız Çıkan Çek No: {cek['cek_no']}", cek_id))
        
        recalculate_cari_bakiye(conn, cek['cari_id'])

        cursor.execute("UPDATE cekler SET durum = ? WHERE id = ?", (yeni, cek_id))

    # 4. Bankaya Verildi / Portföyde / İade Edildi
    else:
        cursor.execute("UPDATE cekler SET durum = ? WHERE id = ?", (yeni, cek_id))

    conn.commit()
    conn.close()
    return get_cek(cek_id)

def delete_cek(cek_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM cekler WHERE id = ?", (cek_id,))
    cek = cursor.fetchone()
    if not cek:
        conn.close()
        raise ValueError("Çek bulunamadı.")
        
    tutar = float(cek['tutar'])
    tahsil_kasa_id = cek['tahsil_kasa_id']
    tahsil_banka_id = cek['tahsil_banka_id']
    cari_id = cek['cari_id']
    cirolanan_cari_id = cek['cirolanan_cari_id']
    
    # 1. Eğer tahsil edildiyse kasa/banka bakiyesini geri al
    if cek['durum'] == "TAHSIL_EDILDI":
        if tahsil_kasa_id:
            cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, tahsil_kasa_id))
        if tahsil_banka_id:
            cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, tahsil_banka_id))
            
    # 2. Bu çeke bağlı kasa/banka hareketlerini sil
    cursor.execute("DELETE FROM kasa_banka_hareketleri WHERE cek_id = ?", (cek_id,))
    
    # 3. Bu çeke bağlı cari hareketleri sil
    cursor.execute("DELETE FROM cari_hareketler WHERE ref_cek_id = ?", (cek_id,))
    
    # 4. Çeki sil
    cursor.execute("DELETE FROM cekler WHERE id = ?", (cek_id,))
    
    # 5. Cari bakiyelerini yeniden hesapla
    if cari_id:
        recalculate_cari_bakiye(conn, cari_id)
    if cirolanan_cari_id:
        recalculate_cari_bakiye(conn, cirolanan_cari_id)
        
    conn.commit()
    conn.close()
    return True
