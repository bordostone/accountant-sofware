import math

BIRLER = ["", "BİR", "İKİ", "ÜÇ", "DÖRT", "BEŞ", "ALTI", "YEDİ", "SEKİZ", "DOKUZ"]
ONLAR = ["", "ON", "YİRMİ", "OTUZ", "KIRK", "ELLİ", "ALTMIŞ", "YETMİŞ", "SEKSEN", "DOKSAN"]
BASAMAKLAR = ["", "BİN", "MİLYON", "MİLYAR", "TRİLYON"]

def _uc_basamak(n: int) -> str:
    yuz = n // 100
    on = (n % 100) // 10
    bir = n % 10
    
    parts = []
    if yuz == 1:
        parts.append("YÜZ")
    elif yuz > 1:
        parts.append(f"{BIRLER[yuz]} YÜZ")
        
    if on > 0:
        parts.append(ONLAR[on])
        
    if bir > 0:
        parts.append(BIRLER[bir])
        
    return " ".join(parts).strip()

def sayi_yaziya(sayi: int) -> str:
    if sayi == 0:
        return "SIFIR"
    
    parts = []
    basamak_idx = 0
    kalan = sayi
    
    while kalan > 0:
        uc = kalan % 1000
        if uc > 0:
            metin = _uc_basamak(uc)
            # Özel kural: "BİR BİN" denmez, sadece "BİN" denir
            if basamak_idx == 1 and uc == 1:
                metin = "BİN"
            elif BASAMAKLAR[basamak_idx]:
                metin = f"{metin} {BASAMAKLAR[basamak_idx]}"
            parts.insert(0, metin)
        kalan = kalan // 1000
        basamak_idx += 1
        
    return " ".join(parts).strip()

def yaziyla_tutar(tutar: float, para_birimi: str = "TL") -> str:
    """Örnek: 1250.75 -> YALNIZ BİN İKİ YÜZ ELLİ TL YETMİŞ BEŞ KURUŞTUR"""
    try:
        tutar = round(float(tutar), 2)
        tam = int(math.floor(tutar))
        ondalik = int(round((tutar - tam) * 100))
        
        tam_yazi = sayi_yaziya(tam)
        ondalik_yazi = sayi_yaziya(ondalik) if ondalik > 0 else "SIFIR"
        
        if ondalik > 0:
            return f"YALNIZ #{tam_yazi} {para_birimi} {ondalik_yazi} KURUŞ#TUR"
        else:
            return f"YALNIZ #{tam_yazi} {para_birimi} SIFIR KURUŞ#TUR"
    except Exception:
        return f"{tutar} {para_birimi}"

def para_format(tutar: float, sembol: str = "₺") -> str:
    """1234567.89 -> 1.234.567,89 ₺"""
    try:
        val = float(tutar or 0.0)
        neg = "-" if val < 0 else ""
        val = abs(val)
        parts = f"{val:,.2f}".split(".")
        integer_part = parts[0].replace(",", ".")
        decimal_part = parts[1]
        return f"{neg}{integer_part},{decimal_part} {sembol}"
    except Exception:
        return f"{tutar} {sembol}"

def tarih_format(iso_tarih: str) -> str:
    """2026-10-06 -> 06.10.2026"""
    if not iso_tarih:
        return ""
    try:
        parts = iso_tarih.split("T")[0].split("-")
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
        return iso_tarih
    except Exception:
        return iso_tarih
