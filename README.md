# Ön Muhasebe Pro — Masaüstü & Yerel Muhasebe Yazılımı

**Fatura Kesme, Kasa & Banka (Nakit, Havale, EFT), Çek/Senet Takibi, Müşteri & Tedarikçi Cari Yönetimi ve Mali Raporlama Platformu**

---

## 🌟 Öne Çıkan Özellikler

1. **Fatura Yönetimi**:
   - Satış ve Alış faturaları düzenleme.
   - Otomatik fatura numarası üretimi (`SF2026000001`, `AF2026000001`).
   - Dinamik ürün/hizmet kalemleri ekleme, miktar, birim fiyat, KDV (%0, %1, %10, %20), iskonto.
   - Anlık ara toplam, KDV ayrımı ve genel toplam hesaplama.
   - Resmi formatta **A4 Fatura Çıktısı (Yazdır / PDF Kaydet)**.
   - Türk Lirası cinsinden otomatik yazı ile tutar: *`YALNIZ #OTUZ DÖRT BİN SEKİZ YÜZ TL SIFIR KURUŞ#TUR`*.
   - Faturaya istinaden anında tek tıkla Nakit, Havale veya Çek ile ödeme/tahsilat alma.

2. **Kasa & Banka (Nakit, Havale, EFT)**:
   - Nakit Kasa yönetimi (Tahsilat, Ödeme).
   - Banka Hesapları (Garanti, İş Bankası vb. IBAN takibi).
   - Gelen Havale / EFT ve Giden Havale / EFT işlemleri.
   - Virman: Kasadan Bankaya yatırma, Bankadan Nakit çekme.
   - Kasa ve Banka bakiyelerinin anlık takibi.

3. **Çek & Senet Takibi**:
   - **Alınan Çekler** (Müşteri çekleri) ve **Verilen Çekler** (Firma çekimiz).
   - Çek No, Vade Tarihi, Keşideci, Banka/Şube, Tutar ve İlgili Cari takibi.
   - **Vade Alarmları**:
     - 🔴 **Kırmızı**: Vadesi geçmiş tahsil edilmemiş çekler!
     - 🟡 **Sarı**: Bu hafta tahsil edilmesi gereken çekler!
     - 🟢 **Yeşil**: İleri vadeli portföy çekleri.
   - Çek İşlemleri:
     - *Tahsil Et*: Doğrudan Nakit Kasaya veya Banka hesabına aktarım.
     - *Bankaya Ver*: Takasa/tahsile gönderme.
     - *Ciro Et*: Başka bir tedarikçiye çek devretme (cari borçtan düşülür).
     - *Karşılıksız*: Karşılıksız çıkan çekin cariye geri yansıtılması.

4. **Cari Hesap Yönetimi (Müşteri & Tedarikçi)**:
   - Müşteri ve Tedarikçi kartları, adres, telefon, vergi dairesi ve numarası.
   - Çift taraflı borç / alacak ve güncel bakiye takibi.
   - **Cari Hesap Ekstresi**: Tarih aralıklı, yürüyen bakiyeli, yazdırılabilir ve PDF'e dönüştürülebilir resmi ekstre.

5. **Stok & Hizmet Yönetimi**:
   - Ürün ve Hizmet kartları, alış fiyatı, satış fiyatı, KDV oranı ve stok miktarı.
   - Fatura düzenlerken ürün seçildiğinde fiyat ve KDV otomatik dolar.

6. **Mali Raporlar & Gösterge Paneli**:
   - Toplam Alacak, Toplam Borç, Kasa/Banka Mevcudu, Portföydeki Çekler.
   - KDV Beyanname Özeti: Hesaplanan KDV (391) vs İndirilecek KDV (191) ve Net Ödenecek / Devreden KDV.

---

## 🚀 Yerel Olarak Çalıştırma (Hemen Denemek İçin)

Program şu anda bilgisayarınızda hazırdır.

### macOS İçin:
- Finder'dan `baslat_mac.command` dosyasına çift tıklayınız.
- Veya terminalden:
  ```bash
  cd /Users/hakan/on-muhasebe
  ./.venv/bin/python run_app.py
  ```
- Tarayıcınız otomatik olarak `http://127.0.0.1:8000` adresinde açılacaktır.

---

## 📦 Başka Bir Bilgisayara Kurulum (Setup) Rehberi

Bu yazılımı şirketinizdeki başka bir bilgisayara (Windows veya Mac) taşımak için iki yöntem sunulmuştur:

### 1. Windows Bilgisayara Hızlı Kurulum (Python Zaten Kurulu İse - YALNIZCA 300 KB):
Hedef Windows 10/11 bilgisayarınızda zaten Python kuruluysa en pratik ve hafif yöntem budur:
1. `dist_windows/OnMuhasebe_Hizli_Kurulum.zip` dosyasını (yalnızca 311 KB) Windows bilgisayara kopyalayıp klasöre çıkartınız.
2. Klasör içindeki **`Kurulum.bat`** dosyasına çift tıklayınız:
   - Sisteminizdeki Python'u (Python 3.9, 3.10, 3.11, 3.12, 3.13) otomatik tespit eder.
   - Temiz bir sanal ortam (`.venv`) oluşturur ve gerekli paketleri yükler.
   - Masaüstünüze **"Özerler Mermer - Ön Muhasebe"** resmi kısayolunu ekler.
3. Masaüstündeki kısayola çift tıklayarak hemen kullanmaya başlayabilirsiniz (Arka planda sessizce açılır, siyah konsol penceresi görünmez).

### 2. Windows Bilgisayara %100 Çevrimdışı (Offline) Kurulum (Python Kurulu DEĞİLSE):
Hedef bilgisayarda Python veya internet bağlantısı yoksa:
1. `dist_windows/OnMuhasebePro_Windows_Offline.zip` arşivini (38 MB) hedef Windows bilgisayara kopyalayıp bir klasöre çıkartınız.
2. Klasör içindeki **`Kurulum.bat`** dosyasına çift tıklayınız.
   - İçerisinde gömülü Python ve tüm tekerlek kütüphaneleri hazır gelir.
   - İnternet bağlantısı veya Python kurulumu **kesinlikle gerekmez**.
3. **Portatif (USB) Kullanım:** Kurulum yapmadan doğrudan USB bellekten `Baslat_Sessiz.vbs` ile de çalıştırabilirsiniz.

### 3. macOS Bilgisayara Kurulum:
1. Klasörü yeni Mac'e kopyalayınız.
2. `baslat_mac.command` dosyasına çift tıklayınız.

---

## 💾 Verileri Yedekleme ve Taşıma

Tüm faturalarınız, carileriniz ve ödemeleriniz `data/muhasebe.db` isimli tek bir dosyada güvenle saklanır.
- **Tek Tıkla Yedek:** Uygulama içerisinden **"Firma & Ayarlar"** menüsüne gidip **"Veritabanı Yedeğini İndir (.db)"** butonuna basarak anında yedeğinizi bilgisayarınıza indirebilirsiniz.
- Başka bir bilgisayara verileri aktarmak için sadece `data/muhasebe.db` dosyasını o bilgisayardaki `data/` klasörüne kopyalamanız yeterlidir.
