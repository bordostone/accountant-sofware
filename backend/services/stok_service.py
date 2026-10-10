from backend.database import get_db
from backend.models import StokCreate, StokUpdate

def generate_stok_kod(conn, tip: str = "URUN") -> str:
    cursor = conn.cursor()
    prefix = "STK" if tip == "URUN" else "HZM"
    cursor.execute("SELECT id FROM stoklar WHERE tip = ? ORDER BY id DESC LIMIT 1", (tip,))
    row = cursor.fetchone()
    next_id = (row['id'] + 1) if row else 1
    return f"{prefix}-{next_id:04d}"

def list_stoklar(tip: str = None, search: str = None, sadece_kritik: bool = False):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM stoklar WHERE 1=1"
    params = []
    if tip:
        query += " AND tip = ?"
        params.append(tip)
    if sadece_kritik:
        query += " AND tip = 'URUN' AND stok_miktari <= kritik_stok"
    if search:
        query += " AND (ad LIKE ? OR kod LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s])

    query += " ORDER BY ad ASC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_stok(stok_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stoklar WHERE id = ?", (stok_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_stok(data: StokCreate):
    conn = get_db()
    cursor = conn.cursor()
    kod = data.kod or generate_stok_kod(conn, data.tip)
    cursor.execute("""
        INSERT INTO stoklar (kod, ad, tip, birim, alis_fiyati, satis_fiyati, kdv_orani, stok_miktari, kritik_stok)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        kod, data.ad, data.tip, data.birim, data.alis_fiyati,
        data.satis_fiyati, data.kdv_orani, data.stok_miktari, data.kritik_stok
    ))
    stok_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_stok(stok_id)

def update_stok(stok_id: int, data: StokUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stoklar SET
            ad = ?, tip = ?, birim = ?, alis_fiyati = ?, satis_fiyati = ?,
            kdv_orani = ?, stok_miktari = ?, kritik_stok = ?, durum = ?
        WHERE id = ?
    """, (
        data.ad, data.tip, data.birim, data.alis_fiyati, data.satis_fiyati,
        data.kdv_orani, data.stok_miktari, data.kritik_stok, data.durum, stok_id
    ))
    conn.commit()
    conn.close()
    return get_stok(stok_id)

def delete_stok(stok_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stoklar WHERE id = ?", (stok_id,))
    conn.commit()
    conn.close()
    return True
