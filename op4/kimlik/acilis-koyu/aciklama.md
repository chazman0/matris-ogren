# Kemer Çizgisi (koyu zemin) — op4 açılış ekranı

Seçilen D "Kemer Çizgisi" kavramının koyu zeminli sürümü; `../kemer-cizgisi-acik/` klasöründeki açık sürümün **koyu ikizi**. Özgün koyu kavram `../kemer-cizgisi/` klasöründe olduğu gibi durur; bu klasör ondan türetildi ve açık sürümdeki iki ek buraya aynen taşındı: kilit taşı yerine otururken taşın arkasında beliren **loş, sıcak bir ışık** ve çentikli ölçü çizgisi yerine B "Gece" kavramındaki **düz ilerleme çizgisi**. Zaman çizelgesi açık sürümle birebir aynıdır; yalnız opaklıklar koyu zemine göre ayarlandı.

## Fikir

Koyu bir çizim paftasında önce iskele çizgileri belirir: simetri ekseni, üzengi çizgisi ve zemin. Kemer, iki ayağından aynı anda yükselen ince altın bir çizgiyle çizilir; her tamamlanan yükleme adımı kemere bir derz çizgisi olarak işlenir. Kalemler tepede buluşunca kilit taşı en son çizilir. "Hazır" anında kemer Kahve ile dolar, Krem kilit taşı yukarıdan yerine iner ve **taş oturduğu anda arkasında loş bir lamba yanmış gibi sıcak bir ışık belirip yavaşça söner**; iskele çizgileri kalkar, OPUS FORTİS yazısı belirir. Işık taşın arkasından gelir: logo renkleri değişmez, Antrasit pafta taşın çevresinde bir an ısınır. Krem taş koyu zeminde zaten seçildiğinden açık sürümdeki kenar çizgisine gerek yoktur ve eklenmemiştir.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `kare-0.png`, `kare-50.png`, `kare-oturma.png`, `kare-100.png` | 1920×1080 (2×, %200 DPI) kareler. `kare-oturma` ışığın tepe anıdır (t = 4050 ms) |
| `kare-*-960x540.png` | Aynı karelerin 960×540'a Lanczos ile küçültülmüş hâli (%100 DPI) |
| `animasyon.html` | Tek dosyalık canlı önizleme. Varlıklar `../kimlik/` ve `../fontlar/` klasörlerinden okunur. Altında Tekrar oynat düğmesi, Yavaş (¼×) seçeneği ve zaman kaydırıcısı var. `?t=4050` adresiyle istenen an dondurulur |
| `kontur.json`, `katmanlar/` | Özgün koyu kavramdan kopya: kalem yolları, hayalet kontur, ölçüler; renk maskesiyle ayrılmış kemer ve kilit taşı katmanları (logo yeniden çizilmedi) |
| `kontur.py` → `uret.py` → `html_yap.py` → `dogrula.py` | Üretim sırası: kontur, kareler, HTML, başsız Chromium ile kare karşılaştırması (`dogrulama/`) |
| `../kemer-cizgisi-secim.html`, `../kemer-cizgisi-secim.png` | Koyu ve açık sürümün yan yana, eşzamanlı karşılaştırması (tek dosya) ve temas kâğıdı |

`uret.py` kareleri milisaniye cinsinden zamanla üretir ve zaman çizelgesi `animasyon.sablon.html` ile birebirdir; `dogrula.py` dört anı (250, 1960, 4050, 4650 ms) Chromium'da dondurup Pillow kareleriyle karşılaştırır (ortalama fark ≈ 1/255; yalnız harf ve çizgi kenarlarındaki yumuşatma ile kalem ucu halesinin profil farkı).

## Renkler

| Öğe | Renk |
|---|---|
| Zemin | Antrasit `#14181B`. Kemerin arkasında çok hafif radyal ışık, merkezde ≈ `#222425` (özgün koyu D) |
| İskele (eksen, zemin çizgisi) | Gri `#8C8C8C` %30, 0,75 DIP |
| Üzengi çizgisi / tarama / yay merkezi işareti | Gri %20 / %13 / %40 |
| Hayalet kontur (gizli çizgi, kesikli) | Gri %26, 0,75 DIP, kesik 3,5 / boşluk 3 |
| Çizim izi | Altın `#B08950`, **1,5 DIP** (açık sürümde 1,75), yuvarlak uç ve birleşim |
| Adım derzleri | Altın %42, 0,75 DIP |
| Kalem ucu | Krem `#EDE6D8` nokta (r = 1,6) ve Altın hale (r = 16, radyal geçiş %42 → %20 → %0) |
| Dolgu | Resmî simge PNG'si: Kahve `#8A6B3C` kemer, Krem kilit taşı (değiştirilmedi) |
| **Kilit taşı ışığı** | Altın radyal geçiş, merkez (268, 136,9), yarıçap 112 (≈ 2,25 × taş genişliği 49,5), cosinus profili; **tepe opaklık %28** (açıkta %22), **son karede kalan %5,5** (açıkta %5). Logonun arkasında çizilir; sert kenar ve beyaz çekirdek yok. Tepe anında taşın 20 px üstünde zemin `#14181B` → ≈ `#342F27` olur |
| **Genişleyen halka** | Altın, **tepe %4,5** (açıkta %3,5), yarıçap 28 → 150, yumuşak yarı genişlik 26; kenarı belli olmayan tek bir dalga |
| Kurum yazısı | `opus-fortis-yazi-koyu-zemin.png` (Krem yazı, Altın kilit taşı noktası) |
| Metin | Krem (ürün adı; alt başlık %80; "Hazır" %95), Gri (durum %90; sürüm %85; © %70), Altın (yüzde, ilerleme) |
| **İlerleme izi / dolgu / uç** | **Krem %10** (1 px) / Altın (1 px) / son 48 px'te Altın → `#DBCAAF` (Altın %30 + Krem %70, "Gece" değeri), t² ile; uçta 14×2 px, 1,5 px bulanık `#DBCAAF` %55 parıltı (yalnız hareket ederken) |
| Pencere kenarı | İçten 1 px, beyaz %7 |

Kalın yazılanlar açık sürümden farklı olan ya da bu sürüme yeni eklenen değerlerdir. Krem kilit taşı kenar çizgisi (açık sürümdeki Altın %70, 0,9 DIP) burada **yoktur**.

## Tipografi

| Öğe | Yazı tipi | Boyut (DIP) | Renk |
|---|---|---|---|
| `op4` | Inter Light (wght 300, opsz 32) | 92 | Krem |
| Yapı analizi ve tasarımı | Cormorant Garamond Medium (500) | 25 | Krem %80 |
| Durum satırı | Inter Regular (400) | 12,5 | Gri %90, "Hazır" Krem %95 |
| Yüzde (`%50`, Türkçe yazımla % önde) | Inter Medium (500) | 12,5 | Altın |
| Sürüm 0.1.0 / © 2026 Opus Fortis | Inter Regular | 11 | Gri %85 / %70 |

Boyutlar ve konumlar açık sürümle ve özgün koyu D ile aynıdır. İ, ı, ş, ğ, ü, ö, ç ve … glifleri üç yazı tipinde de var; dosyalardan denetlendi.

## Yerleşim (mantıksal px / DIP, pencere 960×540)

- Kemerin ekseni x = 268. Simge içeriği (kilit taşı tepesinden ayağa) y = 112'den başlar, 256 yüksekliğindedir (ölçek 0,27497). Zemin çizgisi y = 368'dedir.
- Kilit taşı: üst kenar y ≈ 112, alt kenar y ≈ 167,6; üst genişlik 49,5; ağırlık merkezi (268, 136,9). Işığın merkezi budur.
- Kurum yazısı 232 genişliğindedir, x = 268'e ortalanır, harf tabanı y = 418'dedir.
- Sağ sütun x = 512 ile 904 arasındadır. `op4` tabanı 236, alt başlık tabanı 282, durum satırının tabanı 352'dedir.
- İlerleme çizgisi y = 368'dedir (kemerin zemin çizgisiyle aynı hiza), x 512–904, 1 px. "Gece" biçimi: ince iz, soldan sağa uzayan Altın dolgu, çentik yok. Alt bilgi tabanı 500'dedir.

## Hareket çizelgesi (ms) — açık sürümle birebir

| Zaman | Olay |
|---|---|
| 0–220 | Pencere opaklığı 0 → 1 |
| 80–680 | İskele çizgileri uzar: eksen yukarıdan aşağı, üzengi ve zemin çizgileri merkezden dışa doğru (ease-out cubic) |
| 150–750 | Kesikli hayalet kontur belirir. Kalem uçları ayak ortalarında görünür |
| 500–800 | Yay merkezi işareti (küçük çember) belirir |
| 120–620 / 220–720 / 320–820 / 420–920 | Sırasıyla `op4`, alt başlık, durum ve ilerleme çizgisi, alt bilgi belirir: opaklık artar, metin 6 px yukarı kayar |
| 250–700 | **Arayüz hazırlanıyor…** (p 0 → 0,12). Kalemler ayak tabanında dışa ve içe yürür, sonra bacaklardan yükselir |
| 700–1300 | **DirectX 12 aygıtı açılıyor…** (0,12 → 0,30) |
| 1300–2400 | **Hesap motoru (Python) yükleniyor…** (0,30 → 0,62). p = 0,50 anı t = 1960 (`kare-50`) |
| 2400–3050 | **Kesit kütüphanesi okunuyor…** (0,62 → 0,84) |
| 3050–3650 | **Son proje açılıyor…** (0,84 → 1,00). p = 0,86'da (≈ 3150 ms) dört kemer kalemi derz ortalarında buluşur. Kalan sürede dört kilit taşı kalemi taşın üst ve alt kenarını kapatır |
| Her adım sınırında | Kemere derz çizgisi düşer (220 ms; bacakta yatay, yayda radyal). Durum metni değişir: eskisi 110 ms'de söner, yenisi 70–250 ms arasında 4 px aşağıdan gelir |
| 250–3650 | İlerleme çizgisinin ucunda açık altın geçiş ve parıltı görünür (çizgi hareket hâlindeyken) |
| 3650 | **Hazır** (%100) |
| 3650–3870 | Ucun açık geçişi ve parıltısı söner, çizgi düz Altın kalır |
| 3650–4000 | Kemer dolgusu (Kahve) 0 → 1 |
| 3700–4200 | İskele ve hayalet kontur söner |
| 3750–4150 | Altın iz ve derz çizgileri söner |
| 3800–4250 | Kilit taşı (Krem) 0 → 1 olur ve 12 px yukarıdan yerine iner: "kilit taşı oturur" |
| **3820–4060** | **Işık yükselir:** taşın çevresindeki Altın radyal ışık, ease-out cubic ile %0 → **%28** (merkez opaklığı). Taşın inişiyle aynı anda, taş yerine tam otururken ışık tepeye ulaşır |
| **4050** | **Tepe anı** (`kare-oturma`): ışık %28, taş 1 px yukarıda ve %91 opak, iz %25, iskele silinmek üzere |
| **4060–5100** | **Işık söner:** ease-out cubic ile %28 → **%5,5** (≈ 1040 ms). 4650'de ≈ %7,3, ana pencereye geçişte ≈ %5,5 kalır |
| 3900–4800 | Genişleyen halka: yarıçap 28 → 150 (ease-out), opaklık ilk 150 ms'de **%4,5**'e çıkıp (1 − u)^1,5 ile söner. Kenarı belli olmayan tek bir dalga |
| 4150–4650 | OPUS FORTİS yazısı (koyu zemin sürümü) belirir ve 8 px yukarı kayar |
| ≈ 4650 | Son kare (`kare-100`). Uygulamada ≈ 400 ms bekledikten sonra ana pencereye çapraz geçiş yapılır; kalan %5,5 ışık o geçişte pencereyle birlikte söner |

Adım içi yumuşatma `0,55·u + 0,45·(½ − ½cos πu)` biçimindedir. Kalem adım sınırında yavaşlar ama durmaz. Bitiş geçişlerinin hepsi ease-out cubic'tir.

**Kalem parametresi `g`:** Her kemer yarısında iki kalem vardır (dış ve iç). Aynı `g` değerinde iki kalem aynı yapım cephesindedir. Evre ağırlıkları: taban 0,068, bacak 0,440, yay 0,425, derz 0,067. Kemer kalemleri ilerlemenin ilk %86'sını kullanır, kilit taşı kalemleri kalan %14'ü.

## Kilit taşı ışığı: yerel uygulama (Direct2D)

Açık sürümdeki notlar (`../kemer-cizgisi-acik/aciklama.md`, "Kilit taşı ışığı: yerel uygulama") aynen geçerlidir; koyu zemine özgü değerler şunlardır:

1. **Fırça:** `ID2D1RadialGradientBrush`, merkez (268, 136,9), yarıçap 112, 13 durak (`a(u) = ½ + ½·cos(πu)`, renk Altın), `D2D1_EXTEND_MODE_CLAMP`; **logo bitmap'lerinden önce**, zeminin hemen üstüne çizilir. Kahve kemer ve Krem taş ışığı örter, ışık yalnız Antrasit paftada görünür.
2. **Opaklık animasyonu:** `isik(t) = 0,28 · e₃(s(t, 3820, 4060)) − (0,28 − 0,055) · e₃(s(t, 4060, 5100))`, `e₃(u) = 1 − (1 − u)³`, `s` 0–1'e kırpılmış oran. Karede yalnız `brush->SetOpacity(isik(t))` değişir; `FillRectangle((156, 25, 380, 249), brush)` yeter.
3. **Halka:** `r(t) = 28 + 122·e₃(s(t, 3900, 4800))`, `SetOpacity(0,045 · min(1, 6u) · (1 − u)^1,5)`; duraklar açık sürümdeki gibi (25 örnek, `(½ + ½·cos(π·min(1, |u·R − r| / 26)))²`).
4. **Bantlaşma (koyu zeminde önemli):** %28'lik tepe Antrasit üzerinde kırmızı kanalda 44 kademe demektir ve cosinus profili 112 px'te sıfıra iner; koyu tonlarda 1 LSB'lik basamaklar görünür olabilir. `uret.py` bu yüzden ışığı ve halkayı zeminle birlikte kayan noktalı hesaplayıp ±0,5 LSB titreşimle 8 bite indirir. Yerelde ya `DXGI_FORMAT_R16G16B16A16_FLOAT` ara hedefe çizip son adımda titreşimli (dither) dönüşüm yapın ya da zemin + ışığı %2'lik gürültü döşemesiyle kapatın (özgün koyu D'deki zemin notu).
5. **Kenar çizgisi yok:** Açık sürümdeki `kilit_*` yollarından çizilen Altın kenar bu sürümde çizilmez.
6. **Erişilebilirlik:** `SPI_GETCLIENTAREAANIMATION` kapalıysa ışık ve halka atlanır, yalnız kalan %5,5 ışık doğrudan son karede çizilir.

## Diğer yerel uygulama notları (Win32 + Direct2D/DirectWrite)

1. **Pencere, iş parçacığı, sunum, logo, çizgiler, kesik çizgiler, hale ve zemin, metin, gerçek ilerleme, erişilebilirlik, %100 DPI:** özgün koyu sürümdeki (`../kemer-cizgisi/aciklama.md`) notlar aynen geçerlidir (iz 1,5 DIP, hale r = 16 Altın %42 → %20 → %0, zemin radyal fırçası merkez (268, 235), yarıçaplar 380 × 330).
2. **İlerleme çizgisi ("Gece" biçimi, koyu):** İz ve dolgu `FillRectangle` ile aygıt pikseline oturtulur: kalınlık `max(1, round(1 × ölçek))` px, iz Krem %10, dolgu genişliği `round(p × 392 × ölçek) / ölçek`. Uç için 48 DIP genişliğinde `ID2D1LinearGradientBrush` (`#DBCAAF`, alfa durakları u² ile 0 / 0,03 / 0,11 / 0,25 / 0,44 / 0,69 / 1) dolgu dikdörtgenine `PushAxisAlignedClip` ile kırpılır. Parıltı önceden üretilmiş 14×2 DIP, σ = 1,5 DIP bulanık, %55 opak küçük bir sprite'tır (ya da `CLSID_D2D1GaussianBlur`). **Yalnız hareket ederken:** uç ve parıltının opaklığı gösterilen ilerlemenin hızına bağlanır: `ucA = clamp(|dp/dt| / 0,08 s⁻¹)`, 150 ms'lik üstel yumuşatmayla; uzun süren bir adımda çizgi duraklayınca parıltı kendiliğinden söner, adım gelince yeniden belirir. "Hazır"da 220 ms'de söner. Çentik ve adım işareti yoktur.

## Not

Son karedeki "simge üstte, yazı altta" dizilişi, verilen kimlik dosyalarındaki yatay logo düzenlerinden biri değildir. Simge ve yazı ayrı resmî PNG'ler olarak kullanıldı, hiçbiri değiştirilmedi; ışık logonun arkasına eklenen ayrı bir çizimdir. Kurumsal kimlik kılavuzu bu dizilişe izin vermiyorsa son kare `opus-fortis-yatay-koyu-zemin.png` ile değiştirilebilir (kemer o zaman yatay logodaki konuma çizilir ve "Hazır"da yazı kısmı belirir).
