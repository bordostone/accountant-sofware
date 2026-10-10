from datetime import datetime, date, timedelta
from backend.database import get_db

def get_dashboard_summary():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Toplam Alacak (Müşterilerden beklenen net alacak: bakiye > 0)
    cursor.execute("SELECT COALESCE(SUM(bakiye), 0.0) FROM cariler WHERE bakiye > 0")
    toplam_alacak = float(cursor.fetchone()[0])

    # 2. Toplam Borç (Tedarikçilere borcumuz: bakiye < 0, mutlak değeri)
    cursor.execute("SELECT COALESCE(SUM(ABS(bakiye)), 0.0) FROM cariler WHERE bakiye < 0")
    toplam_borc = float(cursor.fetchone()[0])

    # 3. Kasa Toplamı
    cursor.execute("SELECT COALESCE(SUM(bakiye), 0.0) FROM kasalar")
    toplam_kasa = float(cursor.fetchone()[0])

    # 4. Banka Toplamı
    cursor.execute("SELECT COALESCE(SUM(bakiye), 0.0) FROM bankalar")
    toplam_banka = float(cursor.fetchone()[0])

    # 5. Çekler: Portföydeki Alınan ve Verilen Çekler
    cursor.execute("""
        SELECT COALESCE(SUM(tutar), 0.0), COUNT(*) 
        FROM cekler 
        WHERE cek_turu = 'ALINAN' AND durum IN ('PORTFOYDE', 'BANKAYA_VERILDI')
    """)
    res = cursor.fetchone()
    alinan_cek_tutar = float(res[0])
    alinan_cek_sayi = int(res[1])

    cursor.execute("""
        SELECT COALESCE(SUM(tutar), 0.0), COUNT(*) 
        FROM cekler 
        WHERE cek_turu = 'VERILEN' AND durum = 'PORTFOYDE'
    """)
    res = cursor.fetchone()
    verilen_cek_tutar = float(res[0])
    verilen_cek_sayi = int(res[1])

    # 6. Vadesi Geciken ve Bu Hafta Gelen Çek Alarmları
    today_str = date.today().strftime("%Y-%m-%d")
    hafta_sonu_str = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT COALESCE(SUM(tutar), 0.0), COUNT(*) 
        FROM cekler 
        WHERE durum IN ('PORTFOYDE', 'BANKAYA_VERILDI') AND vade_tarihi < ?
    """, (today_str,))
    res = cursor.fetchone()
    geciken_cek_tutar = float(res[0])
    geciken_cek_sayi = int(res[1])

    cursor.execute("""
        SELECT COALESCE(SUM(tutar), 0.0), COUNT(*) 
        FROM cekler 
        WHERE durum IN ('PORTFOYDE', 'BANKAYA_VERILDI') AND vade_tarihi >= ? AND vade_tarihi <= ?
    """, (today_str, hafta_sonu_str))
    res = cursor.fetchone()
    yaklasan_cek_tutar = float(res[0])
    yaklasan_cek_sayi = int(res[1])

    # 7. Son 5 Fatura
    cursor.execute("""
        SELECT f.id, f.fatura_no, f.fatura_turu, f.fatura_tarihi, f.genel_toplam, f.odeme_durumu, c.unvan as cari_unvan
        FROM faturalar f
        JOIN cariler c ON f.cari_id = c.id
        ORDER BY f.id DESC LIMIT 5
    """)
    son_faturalar = [dict(r) for r in cursor.fetchall()]

    # 8. Son 5 Kasa/Banka Hareketi
    cursor.execute("""
        SELECT kbh.id, kbh.islem_tarihi, kbh.islem_turu, kbh.tutar, kbh.aciklama,
               COALESCE(k.ad, b.banka_adi) as hesap_adi, c.unvan as cari_unvan
        FROM kasa_banka_hareketleri kbh
        LEFT JOIN kasalar k ON kbh.kasa_id = k.id
        LEFT JOIN bankalar b ON kbh.banka_id = b.id
        LEFT JOIN cariler c ON kbh.cari_id = c.id
        ORDER BY kbh.id DESC LIMIT 5
    """)
    son_hareketler = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "toplam_alacak": toplam_alacak,
        "toplam_borc": toplam_borc,
        "toplam_kasa": toplam_kasa,
        "toplam_banka": toplam_banka,
        "nakit_varlik_toplami": toplam_kasa + toplam_banka,
        "alinan_cek_tutar": alinan_cek_tutar,
        "alinan_cek_sayi": alinan_cek_sayi,
        "verilen_cek_tutar": verilen_cek_tutar,
        "verilen_cek_sayi": verilen_cek_sayi,
        "geciken_cek_tutar": geciken_cek_tutar,
        "geciken_cek_sayi": geciken_cek_sayi,
        "yaklasan_cek_tutar": yaklasan_cek_tutar,
        "yaklasan_cek_sayi": yaklasan_cek_sayi,
        "son_faturalar": son_faturalar,
        "son_hareketler": son_hareketler
    }

def get_kdv_raporu(baslangic: str = None, bitis: str = None):
    conn = get_db()
    cursor = conn.cursor()

    # Satış Faturaları KDV Toplamı
    query_satis = "SELECT COALESCE(SUM(kdv_toplam), 0.0), COALESCE(SUM(ara_toplam), 0.0) FROM faturalar WHERE fatura_turu = 'SATIS' AND odeme_durumu != 'IPTAL'"
    params_satis = []
    if baslangic:
        query_satis += " AND fatura_tarihi >= ?"
        params_satis.append(baslangic)
    if bitis:
        query_satis += " AND fatura_tarihi <= ?"
        params_satis.append(bitis)

    cursor.execute(query_satis, params_satis)
    res_satis = cursor.fetchone()
    hesaplanan_kdv = float(res_satis[0])
    satis_matrah = float(res_satis[1])

    # Alış Faturaları KDV Toplamı
    query_alis = "SELECT COALESCE(SUM(kdv_toplam), 0.0), COALESCE(SUM(ara_toplam), 0.0) FROM faturalar WHERE fatura_turu = 'ALIS' AND odeme_durumu != 'IPTAL'"
    params_alis = []
    if baslangic:
        query_alis += " AND fatura_tarihi >= ?"
        params_alis.append(baslangic)
    if bitis:
        query_alis += " AND fatura_tarihi <= ?"
        params_alis.append(bitis)

    cursor.execute(query_alis, params_alis)
    res_alis = cursor.fetchone()
    indirilecek_kdv = float(res_alis[0])
    alis_matrah = float(res_alis[1])

    conn.close()

    fark = round(hesaplanan_kdv - indirilecek_kdv, 2)
    return {
        "baslangic": baslangic,
        "bitis": bitis,
        "satis_matrah": satis_matrah,
        "hesaplanan_kdv": hesaplanan_kdv,
        "alis_matrah": alis_matrah,
        "indirilecek_kdv": indirilecek_kdv,
        "fark": fark,
        "durum": "ÖDENECEK KDV" if fark > 0 else ("DEVREDEN KDV" if fark < 0 else "DENK")
    }

def get_faturalar_raporu(baslangic: str = None, bitis: str = None, tur: str = "HEPSI", durum: str = "HEPSI", search: str = None):
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT f.*, c.unvan as cari_unvan, c.kod as cari_kod
        FROM faturalar f
        JOIN cariler c ON f.cari_id = c.id
        WHERE 1=1
    """
    params = []
    if baslangic:
        query += " AND f.fatura_tarihi >= ?"
        params.append(baslangic)
    if bitis:
        query += " AND f.fatura_tarihi <= ?"
        params.append(bitis)
    if tur and tur != "HEPSI":
        query += " AND f.fatura_turu = ?"
        params.append(tur)
    if durum and durum != "HEPSI":
        query += " AND f.odeme_durumu = ?"
        params.append(durum)
    if search:
        s = f"%{search}%"
        query += " AND (f.fatura_no LIKE ? OR c.unvan LIKE ? OR f.aciklama LIKE ?)"
        params.extend([s, s, s])

    query += " ORDER BY f.fatura_tarihi DESC, f.id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    satis_rows = [r for r in rows if r["fatura_turu"] == "SATIS" and r["odeme_durumu"] != "IPTAL"]
    alis_rows = [r for r in rows if r["fatura_turu"] == "ALIS" and r["odeme_durumu"] != "IPTAL"]

    satis_toplam = round(sum(r["genel_toplam"] for r in satis_rows), 2)
    satis_ara_toplam = round(sum(r["ara_toplam"] for r in satis_rows), 2)
    satis_kdv = round(sum(r["kdv_toplam"] for r in satis_rows), 2)
    satis_odenen = round(sum(r["odenen_tutar"] for r in satis_rows), 2)
    satis_kalan = round(sum(r["kalan_tutar"] for r in satis_rows), 2)

    alis_toplam = round(sum(r["genel_toplam"] for r in alis_rows), 2)
    alis_ara_toplam = round(sum(r["ara_toplam"] for r in alis_rows), 2)
    alis_kdv = round(sum(r["kdv_toplam"] for r in alis_rows), 2)
    alis_odenen = round(sum(r["odenen_tutar"] for r in alis_rows), 2)
    alis_kalan = round(sum(r["kalan_tutar"] for r in alis_rows), 2)

    net_fark = round(satis_toplam - alis_toplam, 2)

    return {
        "baslangic": baslangic,
        "bitis": bitis,
        "filtre_tur": tur,
        "filtre_durum": durum,
        "ozet": {
            "satis_toplam": satis_toplam,
            "satis_ara_toplam": satis_ara_toplam,
            "satis_kdv": satis_kdv,
            "satis_adet": len(satis_rows),
            "satis_odenen": satis_odenen,
            "satis_kalan": satis_kalan,
            "alis_toplam": alis_toplam,
            "alis_ara_toplam": alis_ara_toplam,
            "alis_kdv": alis_kdv,
            "alis_adet": len(alis_rows),
            "alis_odenen": alis_odenen,
            "alis_kalan": alis_kalan,
            "net_fark": net_fark,
            "toplam_adet": len(rows)
        },
        "faturalar": rows
    }

def get_tahsilat_odeme_raporu(baslangic: str = None, bitis: str = None, islem_grubu: str = "HEPSI", search: str = None):
    conn = get_db()
    cursor = conn.cursor()

    TAHSILAT_TURLERI = {'KASA_TAHSILAT', 'BANKA_GELEN_HAVALE', 'CEK_TAHSILATI_KASA', 'CEK_TAHSILATI_BANKA', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT'}
    ODEME_TURLERI = {'KASA_ODEME', 'BANKA_GIDEN_HAVALE', 'MASRAF_ODEME'}
    VIRMAN_TURLERI = {'KASA_BANKA_VIRMAN', 'BANKA_KASA_VIRMAN'}

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
    if baslangic:
        query += " AND kbh.islem_tarihi >= ?"
        params.append(baslangic)
    if bitis:
        query += " AND kbh.islem_tarihi <= ?"
        params.append(bitis)

    if islem_grubu == "TAHSILAT":
        query += f" AND kbh.islem_turu IN ({','.join(['?']*len(TAHSILAT_TURLERI))})"
        params.extend(list(TAHSILAT_TURLERI))
    elif islem_grubu == "ODEME":
        query += f" AND kbh.islem_turu IN ({','.join(['?']*len(ODEME_TURLERI))})"
        params.extend(list(ODEME_TURLERI))
    elif islem_grubu == "VIRMAN":
        query += f" AND kbh.islem_turu IN ({','.join(['?']*len(VIRMAN_TURLERI))})"
        params.extend(list(VIRMAN_TURLERI))

    if search:
        s = f"%{search}%"
        query += " AND (kbh.aciklama LIKE ? OR kbh.evrak_no LIKE ? OR c.unvan LIKE ? OR k.ad LIKE ? OR b.banka_adi LIKE ?)"
        params.extend([s, s, s, s, s])

    query += " ORDER BY kbh.islem_tarihi DESC, kbh.id DESC"
    cursor.execute(query, params)
    raw_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    toplam_tahsilat = 0.0
    tahsilat_adet = 0
    kasa_tahsilat = 0.0
    banka_tahsilat = 0.0
    cek_tahsilat = 0.0

    toplam_odeme = 0.0
    odeme_adet = 0
    kasa_odeme = 0.0
    banka_odeme = 0.0
    masraf_odeme = 0.0

    islenmis_hareketler = []
    for r in raw_rows:
        tur = r["islem_turu"]
        tutar = float(r["tutar"])
        yon = "BILINMIYOR"
        giris = 0.0
        cikis = 0.0

        if tur in TAHSILAT_TURLERI:
            yon = "TAHSILAT"
            giris = tutar
            toplam_tahsilat += tutar
            tahsilat_adet += 1
            if tur == "KASA_TAHSILAT":
                kasa_tahsilat += tutar
            elif tur in ("BANKA_GELEN_HAVALE", "KREDI_KARTI_TAHSILAT", "POS_TAHSILAT"):
                banka_tahsilat += tutar
            elif "CEK" in tur:
                cek_tahsilat += tutar
        elif tur in ODEME_TURLERI:
            yon = "ODEME"
            cikis = tutar
            toplam_odeme += tutar
            odeme_adet += 1
            if tur == "KASA_ODEME":
                kasa_odeme += tutar
            elif tur == "BANKA_GIDEN_HAVALE":
                banka_odeme += tutar
            elif tur == "MASRAF_ODEME":
                masraf_odeme += tutar
        elif tur in VIRMAN_TURLERI:
            yon = "VIRMAN"
            giris = tutar
            cikis = tutar

        hesap_tanimi = r.get("kasa_adi") or r.get("banka_adi") or "Kasa / Banka"
        if tur == "KASA_BANKA_VIRMAN":
            hesap_tanimi = f"Kasa ({r.get('kasa_adi') or ''}) ➔ Banka ({r.get('banka_adi') or ''})"
        elif tur == "BANKA_KASA_VIRMAN":
            hesap_tanimi = f"Banka ({r.get('banka_adi') or ''}) ➔ Kasa ({r.get('kasa_adi') or ''})"

        islenmis_hareketler.append({
            **r,
            "yon": yon,
            "giris": giris,
            "cikis": cikis,
            "hesap_tanimi": hesap_tanimi
        })

    net_nakit_akisi = round(toplam_tahsilat - toplam_odeme, 2)

    return {
        "baslangic": baslangic,
        "bitis": bitis,
        "islem_grubu": islem_grubu,
        "ozet": {
            "toplam_tahsilat": round(toplam_tahsilat, 2),
            "tahsilat_adet": tahsilat_adet,
            "kasa_tahsilat": round(kasa_tahsilat, 2),
            "banka_tahsilat": round(banka_tahsilat, 2),
            "cek_tahsilat": round(cek_tahsilat, 2),
            "toplam_odeme": round(toplam_odeme, 2),
            "odeme_adet": odeme_adet,
            "kasa_odeme": round(kasa_odeme, 2),
            "banka_odeme": round(banka_odeme, 2),
            "masraf_odeme": round(masraf_odeme, 2),
            "net_nakit_akisi": net_nakit_akisi,
            "toplam_adet": len(islenmis_hareketler)
        },
        "hareketler": islenmis_hareketler
    }

def get_hesap_hareketleri_raporu(baslangic: str = None, bitis: str = None, hesap_secimi: str = "TUMU", search: str = None):
    conn = get_db()
    cursor = conn.cursor()

    secili_kasa_id = None
    secili_banka_id = None
    hesap_bilgisi = None

    if hesap_secimi.startswith("KASA_"):
        secili_kasa_id = int(hesap_secimi.replace("KASA_", ""))
        cursor.execute("SELECT * FROM kasalar WHERE id = ?", (secili_kasa_id,))
        k = cursor.fetchone()
        if k:
            hesap_bilgisi = {"tip": "KASA", "id": k["id"], "ad": k["ad"], "bakiye": k["bakiye"]}
    elif hesap_secimi.startswith("BANKA_"):
        secili_banka_id = int(hesap_secimi.replace("BANKA_", ""))
        cursor.execute("SELECT * FROM bankalar WHERE id = ?", (secili_banka_id,))
        b = cursor.fetchone()
        if b:
            hesap_bilgisi = {"tip": "BANKA", "id": b["id"], "ad": b["banka_adi"], "iban": b["iban"], "bakiye": b["bakiye"]}

    # 1. Devir Bakiyesi Hesaplama (başlangıç tarihinden önceki hareketler)
    devir_bakiye = 0.0
    if baslangic:
        if secili_kasa_id:
            cursor.execute("""
                SELECT COALESCE(SUM(CASE 
                    WHEN islem_turu IN ('KASA_TAHSILAT', 'BANKA_KASA_VIRMAN', 'CEK_TAHSILATI_KASA') THEN tutar
                    WHEN islem_turu IN ('KASA_ODEME', 'KASA_BANKA_VIRMAN', 'MASRAF_ODEME') THEN -tutar
                    ELSE 0.0 END), 0.0) as devir
                FROM kasa_banka_hareketleri
                WHERE kasa_id = ? AND islem_tarihi < ?
            """, (secili_kasa_id, baslangic))
            devir_bakiye = float(cursor.fetchone()["devir"])
        elif secili_banka_id:
            cursor.execute("""
                SELECT COALESCE(SUM(CASE 
                    WHEN islem_turu IN ('BANKA_GELEN_HAVALE', 'KASA_BANKA_VIRMAN', 'CEK_TAHSILATI_BANKA', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT') THEN tutar
                    WHEN islem_turu IN ('BANKA_GIDEN_HAVALE', 'BANKA_KASA_VIRMAN', 'MASRAF_ODEME') THEN -tutar
                    ELSE 0.0 END), 0.0) as devir
                FROM kasa_banka_hareketleri
                WHERE banka_id = ? AND islem_tarihi < ?
            """, (secili_banka_id, baslangic))
            devir_bakiye = float(cursor.fetchone()["devir"])
        else:
            # Tüm hesaplar için net devir
            cursor.execute("""
                SELECT COALESCE(SUM(CASE 
                    WHEN islem_turu IN ('KASA_TAHSILAT', 'BANKA_GELEN_HAVALE', 'CEK_TAHSILATI_KASA', 'CEK_TAHSILATI_BANKA', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT') THEN tutar
                    WHEN islem_turu IN ('KASA_ODEME', 'BANKA_GIDEN_HAVALE', 'MASRAF_ODEME') THEN -tutar
                    ELSE 0.0 END), 0.0) as devir
                FROM kasa_banka_hareketleri
                WHERE islem_tarihi < ?
            """, (baslangic,))
            devir_bakiye = float(cursor.fetchone()["devir"])

    # 2. Dönem İçi Hareketler
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
    if secili_kasa_id:
        query += " AND kbh.kasa_id = ?"
        params.append(secili_kasa_id)
    elif secili_banka_id:
        query += " AND kbh.banka_id = ?"
        params.append(secili_banka_id)

    if baslangic:
        query += " AND kbh.islem_tarihi >= ?"
        params.append(baslangic)
    if bitis:
        query += " AND kbh.islem_tarihi <= ?"
        params.append(bitis)

    if search:
        s = f"%{search}%"
        query += " AND (kbh.aciklama LIKE ? OR kbh.evrak_no LIKE ? OR c.unvan LIKE ? OR k.ad LIKE ? OR b.banka_adi LIKE ?)"
        params.extend([s, s, s, s, s])

    query += " ORDER BY kbh.islem_tarihi ASC, kbh.id ASC"
    cursor.execute(query, params)
    raw_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    yuruyen_bakiye = devir_bakiye
    toplam_giris = 0.0
    toplam_cikis = 0.0
    islenmis_hareketler = []

    for r in raw_rows:
        tur = r["islem_turu"]
        tutar = float(r["tutar"])
        giris = 0.0
        cikis = 0.0

        if secili_kasa_id:
            if tur in ('KASA_TAHSILAT', 'BANKA_KASA_VIRMAN', 'CEK_TAHSILATI_KASA'):
                giris = tutar
            elif tur in ('KASA_ODEME', 'KASA_BANKA_VIRMAN', 'MASRAF_ODEME'):
                cikis = tutar
        elif secili_banka_id:
            if tur in ('BANKA_GELEN_HAVALE', 'KASA_BANKA_VIRMAN', 'CEK_TAHSILATI_BANKA', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT'):
                giris = tutar
            elif tur in ('BANKA_GIDEN_HAVALE', 'BANKA_KASA_VIRMAN', 'MASRAF_ODEME'):
                cikis = tutar
        else:
            # Tüm hesaplar
            if tur in ('KASA_TAHSILAT', 'BANKA_GELEN_HAVALE', 'CEK_TAHSILATI_KASA', 'CEK_TAHSILATI_BANKA', 'KREDI_KARTI_TAHSILAT', 'POS_TAHSILAT'):
                giris = tutar
            elif tur in ('KASA_ODEME', 'BANKA_GIDEN_HAVALE', 'MASRAF_ODEME'):
                cikis = tutar
            elif tur in ('KASA_BANKA_VIRMAN', 'BANKA_KASA_VIRMAN'):
                # İç virman: genel nakit dengesini değiştirmez ama kayıtta her ikisi de görülebilir
                giris = tutar
                cikis = tutar

        toplam_giris += giris
        toplam_cikis += cikis
        yuruyen_bakiye += (giris - cikis)

        hesap_tanimi = r.get("kasa_adi") or r.get("banka_adi") or "Kasa / Banka"
        if tur == "KASA_BANKA_VIRMAN":
            hesap_tanimi = f"Kasa ({r.get('kasa_adi') or ''}) ➔ Banka ({r.get('banka_adi') or ''})"
        elif tur == "BANKA_KASA_VIRMAN":
            hesap_tanimi = f"Banka ({r.get('banka_adi') or ''}) ➔ Kasa ({r.get('kasa_adi') or ''})"

        islenmis_hareketler.append({
            **r,
            "giris": giris,
            "cikis": cikis,
            "yuruyen_bakiye": round(yuruyen_bakiye, 2),
            "hesap_tanimi": hesap_tanimi
        })

    return {
        "baslangic": baslangic,
        "bitis": bitis,
        "hesap_secimi": hesap_secimi,
        "hesap_bilgisi": hesap_bilgisi,
        "ozet": {
            "devir_bakiye": round(devir_bakiye, 2),
            "toplam_giris": round(toplam_giris, 2),
            "toplam_cikis": round(toplam_cikis, 2),
            "donem_net": round(toplam_giris - toplam_cikis, 2),
            "kapanis_bakiye": round(yuruyen_bakiye, 2),
            "toplam_adet": len(islenmis_hareketler)
        },
        "hareketler": islenmis_hareketler
    }
