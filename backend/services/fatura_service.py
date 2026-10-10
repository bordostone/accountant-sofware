from datetime import datetime, date
from backend.database import get_db
from backend.models import FaturaCreate
from backend.services.cari_service import recalculate_cari_bakiye
from backend.utils import yaziyla_tutar, para_format, tarih_format

def generate_fatura_no(conn, fatura_turu: str = "SATIS") -> str:
    cursor = conn.cursor()
    yil = date.today().year
    prefix = "SF" if fatura_turu == "SATIS" else "AF"
    
    cursor.execute("""
        SELECT fatura_no FROM faturalar 
        WHERE fatura_no LIKE ? 
        ORDER BY id DESC LIMIT 1
    """, (f"{prefix}{yil}%",))
    row = cursor.fetchone()
    if row and row['fatura_no']:
        last_str = row['fatura_no']
        try:
            num = int(last_str[len(prefix) + 4:]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"{prefix}{yil}{num:06d}"

def list_faturalar(fatura_turu: str = None, cari_id: int = None, odeme_durumu: str = None, search: str = None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT f.*, c.unvan as cari_unvan, c.kod as cari_kod, c.telefon as cari_telefon, c.vergi_no as cari_vergi_no
        FROM faturalar f
        JOIN cariler c ON f.cari_id = c.id
        WHERE 1=1
    """
    params = []
    if fatura_turu:
        query += " AND f.fatura_turu = ?"
        params.append(fatura_turu)
    if cari_id:
        query += " AND f.cari_id = ?"
        params.append(cari_id)
    if odeme_durumu:
        query += " AND f.odeme_durumu = ?"
        params.append(odeme_durumu)
    if search:
        query += " AND (f.fatura_no LIKE ? OR c.unvan LIKE ? OR f.aciklama LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    query += " ORDER BY f.fatura_tarihi DESC, f.id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_fatura(fatura_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.*, c.unvan as cari_unvan, c.kod as cari_kod, c.vergi_dairesi as cari_vergi_dairesi,
               c.vergi_no as cari_vergi_no, c.tckn as cari_tckn, c.adres as cari_adres,
               c.il as cari_il, c.ilce as cari_ilce, c.telefon as cari_telefon, c.eposta as cari_eposta
        FROM faturalar f
        JOIN cariler c ON f.cari_id = c.id
        WHERE f.id = ?
    """, (fatura_id,))
    fatura = cursor.fetchone()
    if not fatura:
        conn.close()
        return None

    res = dict(fatura)
    
    # Kalemleri al
    cursor.execute("SELECT * FROM fatura_kalemleri WHERE fatura_id = ?", (fatura_id,))
    res['kalemler'] = [dict(k) for k in cursor.fetchall()]

    # Bu faturaya bağlı yapılan tahsilat/ödemeleri al
    cursor.execute("""
        SELECT kbh.*, k.ad as kasa_adi, b.banka_adi, b.iban
        FROM kasa_banka_hareketleri kbh
        LEFT JOIN kasalar k ON kbh.kasa_id = k.id
        LEFT JOIN bankalar b ON kbh.banka_id = b.id
        WHERE kbh.fatura_id = ?
        ORDER BY kbh.islem_tarihi ASC
    """, (fatura_id,))
    res['odemeler'] = [dict(o) for o in cursor.fetchall()]

    # Ayarları al (Yazdırma için)
    cursor.execute("SELECT * FROM ayarlar WHERE id = 1")
    ayarlar = cursor.fetchone()
    res['ayarlar'] = dict(ayarlar) if ayarlar else {}

    # Yazı ile toplam tutar
    res['yaziyla_genel_toplam'] = yaziyla_tutar(res['genel_toplam'])
    conn.close()
    return res

def create_fatura(data: FaturaCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    fatura_no = data.fatura_no or generate_fatura_no(conn, data.fatura_turu)
    
    # Hesaplamalar
    ara_toplam = 0.0
    kdv_toplam = 0.0
    satir_verileri = []
    
    for k in data.kalemler:
        brut = round(k.miktar * k.birim_fiyat, 2)
        iskonto_tutari = round(brut * (k.iskonto_orani / 100.0), 2)
        net_tutar = round(brut - iskonto_tutari, 2)
        
        # Manuel KDV tutarı veya oran hesabı
        if k.kdv_tutari is not None and k.kdv_tutari >= 0:
            kdv_tutari = round(float(k.kdv_tutari), 2)
            kdv_orani = float(k.kdv_orani) if k.kdv_orani is not None else (round((kdv_tutari / net_tutar) * 100, 2) if net_tutar > 0 else 0.0)
        else:
            kdv_orani = float(k.kdv_orani if k.kdv_orani is not None else 20.0)
            kdv_tutari = round(net_tutar * (kdv_orani / 100.0), 2)
            
        satir_toplami = round(net_tutar + kdv_tutari, 2)
        
        ara_toplam += net_tutar
        kdv_toplam += kdv_tutari
        
        satir_verileri.append({
            "stok_id": k.stok_id,
            "aciklama": k.aciklama,
            "miktar": k.miktar,
            "birim": k.birim,
            "birim_fiyat": k.birim_fiyat,
            "kdv_orani": kdv_orani,
            "kdv_tutari": kdv_tutari,
            "iskonto_orani": k.iskonto_orani,
            "iskonto_tutari": iskonto_tutari,
            "satir_toplami": satir_toplami
        })

    # Genel iskonto varsa
    genel_iskonto_tutari = round(ara_toplam * (data.iskonto_orani / 100.0), 2)
    ara_toplam_net = round(ara_toplam - genel_iskonto_tutari, 2)
    
    # Genel KDV toplamı elle belirtilmişse onu kullan
    if data.kdv_toplam is not None and data.kdv_toplam >= 0:
        kdv_toplam = round(float(data.kdv_toplam), 2)
    else:
        kdv_toplam = round(kdv_toplam, 2)
        
    genel_toplam = round(ara_toplam_net + kdv_toplam, 2)
    kalan_tutar = genel_toplam

    # 1. Faturayı Kaydet
    cursor.execute("""
        INSERT INTO faturalar (
            fatura_no, fatura_turu, fatura_tarihi, vade_tarihi, cari_id,
            ara_toplam, iskonto_orani, iskonto_tutari, kdv_toplam, genel_toplam,
            odenen_tutar, kalan_tutar, odeme_durumu, aciklama
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, 'BEKLIYOR', ?)
    """, (
        fatura_no, data.fatura_turu, data.fatura_tarihi, data.vade_tarihi, data.cari_id,
        ara_toplam_net, data.iskonto_orani, genel_iskonto_tutari, kdv_toplam, genel_toplam,
        kalan_tutar, data.aciklama
    ))
    fatura_id = cursor.lastrowid

    # 2. Kalemleri Kaydet ve Stok Miktarlarını Güncelle
    for s in satir_verileri:
        cursor.execute("""
            INSERT INTO fatura_kalemleri (
                fatura_id, stok_id, aciklama, miktar, birim, birim_fiyat,
                kdv_orani, kdv_tutari, iskonto_orani, iskonto_tutari, satir_toplami
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fatura_id, s['stok_id'], s['aciklama'], s['miktar'], s['birim'], s['birim_fiyat'],
            s['kdv_orani'], s['kdv_tutari'], s['iskonto_orani'], s['iskonto_tutari'], s['satir_toplami']
        ))
        
        # Stok hareketi (Stok seçildiyse)
        if s['stok_id']:
            if data.fatura_turu == "SATIS":
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari - ? WHERE id = ?", (s['miktar'], s['stok_id']))
            else: # ALIS
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari + ? WHERE id = ?", (s['miktar'], s['stok_id']))

    # 3. Cari Hareketi İşle
    if data.fatura_turu == "SATIS":
        # Satış faturasında Müşteri BORÇLANIR
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_fatura_id)
            VALUES (?, ?, 'FATURA_SATIS', ?, ?, 0.0, ?, ?)
        """, (data.cari_id, data.fatura_tarihi, fatura_no, genel_toplam, f"Satış Faturası No: {fatura_no}", fatura_id))
    else:
        # Alış faturasında Tedarikçi ALACAKLANIR
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_fatura_id)
            VALUES (?, ?, 'FATURA_ALIS', ?, 0.0, ?, ?, ?)
        """, (data.cari_id, data.fatura_tarihi, fatura_no, genel_toplam, f"Alış Faturası No: {fatura_no}", fatura_id))

    # 4. Cari Bakiyesini Yeniden Hesapla
    recalculate_cari_bakiye(conn, data.cari_id)

    conn.commit()
    conn.close()
    return get_fatura(fatura_id)

def cancel_fatura(fatura_id: int):
    """Faturayı iptal eder, stokları ve cari hareketini geri alır."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faturalar WHERE id = ?", (fatura_id,))
    fatura = cursor.fetchone()
    if not fatura:
        conn.close()
        raise ValueError("Fatura bulunamadı.")
    
    if fatura['odenen_tutar'] > 0:
        conn.close()
        raise ValueError("Bu faturaya ait yapılmış ödemeler/tahsilatlar bulunmaktadır. Önce ödeme kayıtlarını siliniz.")

    # 1. Stokları geri al
    cursor.execute("SELECT * FROM fatura_kalemleri WHERE fatura_id = ?", (fatura_id,))
    kalemler = cursor.fetchall()
    for k in kalemler:
        if k['stok_id']:
            if fatura['fatura_turu'] == "SATIS":
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari + ? WHERE id = ?", (k['miktar'], k['stok_id']))
            else:
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari - ? WHERE id = ?", (k['miktar'], k['stok_id']))

    # 2. Cari hareketini sil
    cursor.execute("DELETE FROM cari_hareketler WHERE ref_fatura_id = ?", (fatura_id,))

    # 3. Fatura durumunu IPTAL yap
    cursor.execute("UPDATE faturalar SET odeme_durumu = 'IPTAL', kalan_tutar = 0.0 WHERE id = ?", (fatura_id,))

    # 4. Cari bakiyesini güncelle
    recalculate_cari_bakiye(conn, fatura['cari_id'])

    conn.commit()
    conn.close()
    return True

def update_fatura(fatura_id: int, data: FaturaCreate):
    """Mevcut bir faturayı günceller, eski stokları geri alır, yeni stokları ve cari bakiyeyi senkronize eder."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faturalar WHERE id = ?", (fatura_id,))
    fatura = cursor.fetchone()
    if not fatura:
        conn.close()
        raise ValueError("Fatura bulunamadı.")

    if fatura['odeme_durumu'] == 'IPTAL':
        conn.close()
        raise ValueError("İptal edilmiş fatura üzerinde değişiklik yapılamaz.")

    old_cari_id = fatura['cari_id']
    old_fatura_turu = fatura['fatura_turu']

    # 1. Eski kalemlerin stok etkilerini geri al
    cursor.execute("SELECT * FROM fatura_kalemleri WHERE fatura_id = ?", (fatura_id,))
    eski_kalemler = cursor.fetchall()
    for ek in eski_kalemler:
        if ek['stok_id']:
            if old_fatura_turu == "SATIS":
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari + ? WHERE id = ?", (ek['miktar'], ek['stok_id']))
            else: # ALIS
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari - ? WHERE id = ?", (ek['miktar'], ek['stok_id']))

    # Eski kalemleri sil
    cursor.execute("DELETE FROM fatura_kalemleri WHERE fatura_id = ?", (fatura_id,))

    # 2. Yeni kalemleri ve toplamları hesapla
    ara_toplam = 0.0
    kdv_toplam = 0.0
    satir_verileri = []

    for k in data.kalemler:
        brut = round(k.miktar * k.birim_fiyat, 2)
        iskonto_tutari = round(brut * (k.iskonto_orani / 100.0), 2)
        net_tutar = round(brut - iskonto_tutari, 2)
        
        # Manuel KDV tutarı veya oran hesabı
        if k.kdv_tutari is not None and k.kdv_tutari >= 0:
            kdv_tutari = round(float(k.kdv_tutari), 2)
            kdv_orani = float(k.kdv_orani) if k.kdv_orani is not None else (round((kdv_tutari / net_tutar) * 100, 2) if net_tutar > 0 else 0.0)
        else:
            kdv_orani = float(k.kdv_orani if k.kdv_orani is not None else 20.0)
            kdv_tutari = round(net_tutar * (kdv_orani / 100.0), 2)
            
        satir_toplami = round(net_tutar + kdv_tutari, 2)

        ara_toplam += net_tutar
        kdv_toplam += kdv_tutari

        satir_verileri.append({
            "stok_id": k.stok_id,
            "aciklama": k.aciklama,
            "miktar": k.miktar,
            "birim": k.birim,
            "birim_fiyat": k.birim_fiyat,
            "kdv_orani": kdv_orani,
            "kdv_tutari": kdv_tutari,
            "iskonto_orani": k.iskonto_orani,
            "iskonto_tutari": iskonto_tutari,
            "satir_toplami": satir_toplami
        })

    genel_iskonto_tutari = round(ara_toplam * (data.iskonto_orani / 100.0), 2)
    ara_toplam_net = round(ara_toplam - genel_iskonto_tutari, 2)
    
    # Genel KDV toplamı elle belirtilmişse onu kullan
    if data.kdv_toplam is not None and data.kdv_toplam >= 0:
        kdv_toplam = round(float(data.kdv_toplam), 2)
    else:
        kdv_toplam = round(kdv_toplam, 2)
        
    genel_toplam = round(ara_toplam_net + kdv_toplam, 2)

    # Ödeme durumunu ve kalan tutarı güncelle
    odenen_tutar = float(fatura['odenen_tutar'] or 0.0)
    kalan_tutar = max(0.0, round(genel_toplam - odenen_tutar, 2))
    if odenen_tutar >= genel_toplam and genel_toplam > 0:
        yeni_odeme_durumu = "ODENDI"
    elif odenen_tutar > 0:
        yeni_odeme_durumu = "KISMI"
    else:
        yeni_odeme_durumu = "BEKLIYOR"

    fatura_no = data.fatura_no or fatura['fatura_no']

    # 3. Fatura tablosunu güncelle
    cursor.execute("""
        UPDATE faturalar SET
            fatura_no = ?,
            fatura_tarihi = ?,
            vade_tarihi = ?,
            cari_id = ?,
            ara_toplam = ?,
            iskonto_orani = ?,
            iskonto_tutari = ?,
            kdv_toplam = ?,
            genel_toplam = ?,
            kalan_tutar = ?,
            odeme_durumu = ?,
            aciklama = ?
        WHERE id = ?
    """, (
        fatura_no, data.fatura_tarihi, data.vade_tarihi, data.cari_id,
        ara_toplam_net, data.iskonto_orani, genel_iskonto_tutari, kdv_toplam, genel_toplam,
        kalan_tutar, yeni_odeme_durumu, data.aciklama, fatura_id
    ))

    # 4. Yeni kalemleri kaydet ve yeni stokları düş/ekle
    for s in satir_verileri:
        cursor.execute("""
            INSERT INTO fatura_kalemleri (
                fatura_id, stok_id, aciklama, miktar, birim, birim_fiyat,
                kdv_orani, kdv_tutari, iskonto_orani, iskonto_tutari, satir_toplami
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fatura_id, s['stok_id'], s['aciklama'], s['miktar'], s['birim'], s['birim_fiyat'],
            s['kdv_orani'], s['kdv_tutari'], s['iskonto_orani'], s['iskonto_tutari'], s['satir_toplami']
        ))
        if s['stok_id']:
            if data.fatura_turu == "SATIS":
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari - ? WHERE id = ?", (s['miktar'], s['stok_id']))
            else:
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari + ? WHERE id = ?", (s['miktar'], s['stok_id']))

    # 5. Cari hareketini güncelle
    borc_tutar = genel_toplam if data.fatura_turu == "SATIS" else 0.0
    alacak_tutar = genel_toplam if data.fatura_turu == "ALIS" else 0.0
    islem_turu = "FATURA_SATIS" if data.fatura_turu == "SATIS" else "FATURA_ALIS"
    aciklama_metin = f"{'Satış' if data.fatura_turu == 'SATIS' else 'Alış'} Faturası No: {fatura_no}"

    cursor.execute("SELECT id FROM cari_hareketler WHERE ref_fatura_id = ?", (fatura_id,))
    ch = cursor.fetchone()
    if ch:
        cursor.execute("""
            UPDATE cari_hareketler SET
                cari_id = ?,
                tarih = ?,
                islem_turu = ?,
                evrak_no = ?,
                borc = ?,
                alacak = ?,
                aciklama = ?
            WHERE ref_fatura_id = ?
        """, (data.cari_id, data.fatura_tarihi, islem_turu, fatura_no, borc_tutar, alacak_tutar, aciklama_metin, fatura_id))
    else:
        cursor.execute("""
            INSERT INTO cari_hareketler (cari_id, tarih, islem_turu, evrak_no, borc, alacak, aciklama, ref_fatura_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data.cari_id, data.fatura_tarihi, islem_turu, fatura_no, borc_tutar, alacak_tutar, aciklama_metin, fatura_id))

    # 6. Cari bakiyelerini yeniden hesapla
    if old_cari_id != data.cari_id:
        recalculate_cari_bakiye(conn, old_cari_id)
    recalculate_cari_bakiye(conn, data.cari_id)

    conn.commit()
    conn.close()
    return get_fatura(fatura_id)

def delete_fatura(fatura_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM faturalar WHERE id = ?", (fatura_id,))
    fatura = cursor.fetchone()
    if not fatura:
        conn.close()
        raise ValueError("Fatura bulunamadı.")
        
    fatura_turu = fatura['fatura_turu']
    cari_id = fatura['cari_id']
    
    # 1. Stok hareketlerini geri al
    cursor.execute("SELECT stok_id, miktar FROM fatura_kalemleri WHERE fatura_id = ?", (fatura_id,))
    for k in cursor.fetchall():
        if k['stok_id']:
            if fatura_turu == "SATIS":
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari + ? WHERE id = ?", (k['miktar'], k['stok_id']))
            else:
                cursor.execute("UPDATE stoklar SET stok_miktari = stok_miktari - ? WHERE id = ?", (k['miktar'], k['stok_id']))
                
    # 2. Kalemleri sil
    cursor.execute("DELETE FROM fatura_kalemleri WHERE fatura_id = ?", (fatura_id,))
    
    # 3. Bu faturaya bağlı cari hareketini sil
    cursor.execute("DELETE FROM cari_hareketler WHERE ref_fatura_id = ?", (fatura_id,))
    
    # 4. Bu faturaya bağlı kasa/banka hareketlerinin fatura bağlantısını kaldır
    cursor.execute("UPDATE kasa_banka_hareketleri SET fatura_id = NULL WHERE fatura_id = ?", (fatura_id,))
    
    # 5. Faturayı sil
    cursor.execute("DELETE FROM faturalar WHERE id = ?", (fatura_id,))
    
    # 6. Cari bakiyesini güncelle
    recalculate_cari_bakiye(conn, cari_id)
    
    conn.commit()
    conn.close()
    return True

