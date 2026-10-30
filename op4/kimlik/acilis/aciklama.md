# Kemer Çizgisi (açık zemin) — op4 açılış ekranı

Seçilen D "Kemer Çizgisi" kavramının açık zeminli sürümü. Koyu özgün sürüm `../kemer-cizgisi/` klasöründe olduğu gibi durur; bu klasör ondan kopyalanıp uyarlandı. İki istek uygulandı: **açık zemin** ve kilit taşı yerine otururken taşın çevresinde **çok loş, yumuşak bir ışık**. Ek istekle ilerleme göstergesi, 45° çentikli ölçü çizgisi yerine B "Gece" kavramındaki **düz ilerleme çizgisi** oldu.

## Fikir

Krem'den türetilmiş sıcak bir çizim paftasında önce iskele çizgileri belirir: simetri ekseni, üzengi çizgisi ve zemin. Kemer, iki ayağından aynı anda yükselen ince altın bir çizgiyle çizilir; her tamamlanan yükleme adımı kemere bir derz çizgisi olarak işlenir. Kalemler tepede buluşunca kilit taşı en son çizilir. "Hazır" anında kemer Kahve ile dolar, Krem kilit taşı yukarıdan yerine iner ve **taş oturduğu anda çevresinde loş, sıcak bir ışık belirip yavaşça söner**; iskele çizgileri kalkar, OPUS FORTİS yazısı belirir. Işık taşın arkasından gelir: logo renkleri değişmez, kâğıt taşın çevresinde bir an ısınır. Işık sönerken taşın kâğıda değen üst ve alt kenarındaki ince altın çizgi kalır; Krem taş bu sayede krem kâğıttan ayrılır.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `kare-0.png`, `kare-50.png`, `kare-oturma.png`, `kare-100.png` | 1920×1080 (2×, %200 DPI) kareler. `kare-oturma` ışığın tepe anıdır (t = 4050 ms) |
| `kare-*-960x540.png` | Aynı karelerin 960×540'a Lanczos ile küçültülmüş hâli (%100 DPI) |
| `animasyon.html` | Tek dosyalık canlı önizleme. Varlıklar `../kimlik/` ve `../fontlar/` klasörlerinden okunur. Altında Tekrar oynat düğmesi, Yavaş (¼×) seçeneği ve zaman kaydırıcısı var. `?t=4050` adresiyle istenen an dondurulur |
| `karsilastirma.html` | Kendi kendine yeten karşılaştırma sayfası: canlı animasyon (gerçek boyuta yakın, tekrar/yavaş/an dondurma), dört kare ve "koyu (önceki) · açık (yeni)" son kare şeridi. Görseller ve yazı tipleri (Latin + Türkçe alt kümesi, WOFF2) gömülüdür |
| `ozet.png` | 2400 px genişlikte temas kâğıdı: dört açık kare etiketli, altta koyu son kare karşılaştırma için |
| `kontur.json` | Simge PNG'sinin alfa kanalından çıkarılmış kalem yolları (8 kalem, her noktada `g` parametresiyle), kesikli hayalet kontur ve ölçüler. Koordinatlar simge PNG'si (1200×1397) üzerindedir |
| `katmanlar/kemer.png`, `katmanlar/kilit.png` | Resmî `opus-fortis-simge-renkli.png` renk maskesiyle iki katmana ayrılmış hâli (logo yeniden çizilmedi) |
| `font-alt/*.woff2` | `pyftsubset` ile Latin + Türkçe (U+0020–017F, genel noktalama) alt kümesine indirilmiş değişken yazı tipleri; yalnız `karsilastirma.html` için |
| `kontur.py` → `uret.py` → `html_yap.py` → `dogrula.py` → `karsilastirma_yap.py`, `ozet_yap.py` | Üretim sırası: kontur, kareler, HTML, başsız Chromium ile kare karşılaştırması, karşılaştırma sayfası ve temas kâğıdı |

`uret.py` kareleri milisaniye cinsinden zamanla üretir ve zaman çizelgesi `animasyon.sablon.html` ile birebirdir; `dogrula.py` dört anı (250, 1960, 4050, 4650 ms) Chromium'da dondurup Pillow kareleriyle karşılaştırır (ortalama fark ≈ 1/255, yalnız harf ve çizgi kenarlarındaki yumuşatma farkı).

## Renkler

| Öğe | Renk |
|---|---|
| Zemin (kâğıt) | `#F6F2EA` (Krem `#EDE6D8`'den türetilmiş sıcak açık ton). Kemerin arkasında radyal hafif aydınlanma, merkezde `#FBF8F2`; köşelere doğru hafif vinyet `#EFE9DD` |
| İskele (eksen, zemin çizgisi) | Antrasit `#14181B` %22, 0,75 DIP |
| Üzengi çizgisi / tarama / yay merkezi işareti | Antrasit %15 / %10 / %30 |
| Hayalet kontur (gizli çizgi, kesikli) | Antrasit %20, 0,75 DIP, kesik 3,5 / boşluk 3 |
| Çizim izi | Altın `#B08950`, **1,75 DIP** (koyu sürümde 1,5; açık zeminde biraz daha dolu), yuvarlak uç ve birleşim |
| Adım derzleri | Altın %55, 0,75 DIP |
| Kalem ucu | Kahve `#8A6B3C` nokta (r = 1,6) ve Altın hale (r = 13, radyal geçiş %22 → %10 → %0) |
| Dolgu | Resmî simge PNG'si: Kahve `#8A6B3C` kemer, Krem `#EDE6D8` kilit taşı (değiştirilmedi) |
| Kilit taşı kenarı | Taşın üst ve alt kenarında (kâğıda değen kenarlar) Altın %70, 0,9 DIP; kilit taşı kalemlerinin yolları. Krem taşı krem kâğıttan ayırır |
| Kilit taşı ışığı | Altın radyal geçiş, merkez (268, 136,9), yarıçap 112 (≈ 2,25 × taş genişliği 49,5); tepe opaklık %22, son karede kalan %5. Logonun arkasında çizilir |
| Genişleyen halka | Altın, tepe %3,5, yarıçap 28 → 150, yumuşak yarı genişlik 26; kenarı belli olmayan tek bir dalga |
| Kurum yazısı | `opus-fortis-yazi-acik-zemin.png` (Antrasit yazı, Altın kilit taşı noktası) |
| Metin | Antrasit (ürün adı; alt başlık %80; durum %62, "Hazır" %92; sürüm %55; © %45), Altın (yüzde, ilerleme) |
| İlerleme izi / dolgu / uç | Antrasit %12 (1 px) / Altın (1 px) / son 48 px'te Altın → `#C2A579` (Altın %70 + Krem %30), t² ile; uçta 12×2,5 px, 1,5 px bulanık `#C2A579` %45 parıltı |
| Pencere kenarı | İçten 1 px, Antrasit %8 |

Karşıtlık: Altın iz kâğıt üzerinde yaklaşık 2,8:1; bu yüzden kalınlık 1,75 DIP'e çıkarıldı ve derz çizgileri %55'e alındı. Durum satırı (Antrasit %62 ≈ `#696C6E`) ≈ 5,5:1, "Hazır" ≈ 13:1.

## Tipografi

| Öğe | Yazı tipi | Boyut (DIP) | Renk |
|---|---|---|---|
| `op4` | Inter Light (wght 300, opsz 32) | 92 | Antrasit |
| Yapı analizi ve tasarımı | Cormorant Garamond Medium (500) | 25 | Antrasit %80 |
| Durum satırı | Inter Regular (400) | 12,5 | Antrasit %62, "Hazır" Antrasit %92 |
| Yüzde (`%50`, Türkçe yazımla % önde) | Inter Medium (500) | 12,5 | Altın |
| Sürüm 0.1.0 / © 2026 Opus Fortis | Inter Regular | 11 | Antrasit %55 / %45 |

Boyutlar ve konumlar koyu sürümle aynıdır. İ, ı, ş, ğ, ü, ö, ç ve … glifleri üç yazı tipinde de var; dosyalardan denetlendi.

## Yerleşim (mantıksal px / DIP, pencere 960×540)

- Kemerin ekseni x = 268. Simge içeriği (kilit taşı tepesinden ayağa) y = 112'den başlar, 256 yüksekliğindedir (ölçek 0,27497). Zemin çizgisi y = 368'dedir.
- Kilit taşı: üst kenar y ≈ 112, alt kenar y ≈ 167,6; üst genişlik 49,5; ağırlık merkezi (268, 136,9). Işığın merkezi budur.
- Kurum yazısı 232 genişliğindedir, x = 268'e ortalanır, harf tabanı y = 418'dedir.
- Sağ sütun x = 512 ile 904 arasındadır. `op4` tabanı 236, alt başlık tabanı 282, durum satırının tabanı 352'dedir.
- İlerleme çizgisi y = 368'dedir (kemerin zemin çizgisiyle aynı hiza), x 512–904, 1 px. "Gece" biçimi: ince iz, soldan sağa uzayan Altın dolgu, çentik yok. Alt bilgi tabanı 500'dedir.

## Hareket çizelgesi (ms)

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
| 3800–4250 | Kilit taşı (Krem) 0 → 1 olur ve 12 px yukarıdan yerine iner: "kilit taşı oturur". Taşın üst ve alt kenarındaki altın çizgi taşla birlikte belirir ve kalır |
| **3820–4060** | **Işık yükselir:** taşın çevresindeki Altın radyal ışık, ease-out cubic ile %0 → %22 (merkez opaklığı). Taşın inişiyle aynı anda, taş yerine tam otururken (ease-out'ta hareketin büyük kısmı 4050'ye kadar biter) ışık tepeye ulaşır |
| **4050** | **Tepe anı** (`kare-oturma`): ışık %22, taş 1 px yukarıda ve %91 opak, iz %25, iskele silinmek üzere |
| **4060–5100** | **Işık söner:** ease-out cubic ile %22 → %5 (≈ 1040 ms). 4650'de ≈ %6,5, ana pencereye geçişte ≈ %5 kalır |
| 3900–4800 | Genişleyen halka: yarıçap 28 → 150 (ease-out), opaklık ilk 150 ms'de %3,5'e çıkıp (1 − u)^1,5 ile söner. Kenarı belli olmayan tek bir dalga |
| 4150–4650 | OPUS FORTİS yazısı (açık zemin sürümü) belirir ve 8 px yukarı kayar |
| ≈ 4650 | Son kare (`kare-100`). Uygulamada ≈ 400 ms bekledikten sonra ana pencereye çapraz geçiş yapılır; kalan %5 ışık o geçişte pencereyle birlikte söner |

Adım içi yumuşatma `0,55·u + 0,45·(½ − ½cos πu)` biçimindedir. Kalem adım sınırında yavaşlar ama durmaz. Bitiş geçişlerinin hepsi ease-out cubic'tir.

**Kalem parametresi `g`:** Her kemer yarısında iki kalem vardır (dış ve iç). Aynı `g` değerinde iki kalem aynı yapım cephesindedir. Evre ağırlıkları: taban 0,068, bacak 0,440, yay 0,425, derz 0,067. Kemer kalemleri ilerlemenin ilk %86'sını kullanır, kilit taşı kalemleri kalan %14'ü.

## Kilit taşı ışığı: yerel uygulama (Direct2D)

Işık tek bir `ID2D1RadialGradientBrush` ile, **logo bitmap'lerinden önce** (zeminin hemen üstüne) çizilir; böylece Kahve kemer ve Krem taş ışığı örter, ışık yalnız kâğıtta görünür ve logo renkleri değişmez.

1. **Fırça:** `D2D1_RADIAL_GRADIENT_BRUSH_PROPERTIES{ center = (268, 136,9), gradientOriginOffset = (0, 0), radiusX = radiusY = 112 }`. Durak koleksiyonu, `a(u) = ½ + ½·cos(πu)` eğrisinin 13 örneğidir (u = 0, 1/12, …, 1): her durakta renk Altın, alfa `a(u)`; `D2D1_GAMMA_2_2`, `D2D1_EXTEND_MODE_CLAMP`. Son durak alfa 0'dır; dışarıda hiçbir şey çizilmez (sert kenar yok). Fırça premultiplied alfa ile kurulduğu için `D2D1_ALPHA_MODE_PREMULTIPLIED` hedefte doğru harmanlanır.
2. **Opaklık animasyonu:** Durak koleksiyonu sabittir; karede yalnız `brush->SetOpacity(isik(t))` değişir:
   `isik(t) = 0,22 · e₃(s(t, 3820, 4060)) − (0,22 − 0,05) · e₃(s(t, 4060, 5100))`, burada `s` 0–1 arasına kırpılmış doğrusal oran, `e₃(u) = 1 − (1 − u)³`. `FillRectangle((156, 25, 380, 249), brush)` (merkez ± 112) yeter.
3. **Halka (isteğe bağlı):** İkinci bir radyal fırça, yarıçap `R = r(t) + 26`, duraklar `a(u) = (½ + ½·cos(π·min(1, |u·R − r(t)| / 26)))²` (25 örnek), `r(t) = 28 + 122·e₃(s(t, 3900, 4800))`, `SetOpacity(0,035 · min(1, 6u) · (1 − u)^1,5)`. Yarıçap değiştiği için durak koleksiyonu her karede yeniden kurulur; 25 durak için maliyeti önemsizdir. Alternatif: tek sabit fırça + `SetTransform(Scale(R/176))` ile ölçek animasyonu.
4. **Bantlaşma:** %22'lik tepe 8 bitte 56 kademe demektir, cosinus profili kenara doğru çok yavaş sıfıra iner. Kâğıt zemini zaten ±0,5 LSB titreşimli bir bitmap olarak üretildiğinden (bkz. aşağıda) bantlaşma görünmez; yine de `DXGI_FORMAT_R16G16B16A16_FLOAT` ara hedef kullanılabilir.
5. **Kilit taşı kenarı:** Dört kilit taşı kalem yolundan (`kontur.json`: `kilit_*`) kurulan `ID2D1PathGeometry`, `DrawGeometry(..., 0,9 DIP, Altın fırça opaklık 0,70·dKilit)`, `SetTransform(Translation(0, kilit_dy))` ile taşla birlikte iner. Taş tam oturunca da kalır.
6. **Erişilebilirlik:** `SPI_GETCLIENTAREAANIMATION` kapalıysa ışık ve halka atlanır, yalnız kalan %5 ışık ve kenar çizgisi doğrudan son karede çizilir.

## Diğer yerel uygulama notları (Win32 + Direct2D/DirectWrite)

1. **Pencere, iş parçacığı, sunum, logo, çizgiler, kesik çizgiler, metin, gerçek ilerleme, erişilebilirlik:** koyu sürümdeki (`../kemer-cizgisi/aciklama.md`) notlar geçerlidir. Değişenler aşağıdadır.
2. **Zemin:** Kâğıt `#F6F2EA` ile doldurulur, üstüne iki radyal fırça gelir: merkez aydınlanması (merkez (268, 235), yarıçaplar 380 × 330, duraklar `(1 − u)²` ile `#F6F2EA` → `#FBF8F2`, opak) ve vinyet (merkez (480, 270), yarıçaplar 795 × 511, alfa `clamp((d − 0,5)/0,9)^1,5` ile `#EFE9DD`, d = 0…1,42). Açık tonlarda bantlaşma daha az görünür, yine de bir kez ±0,5 LSB titreşimle bitmap'e çizilip saklanması önerilir.
3. **Kurum yazısı:** `opus-fortis-yazi-acik-zemin.png` (kaynak kutusu (98, 86)–(1902, 285), hedef genişlik 232).
4. **Kalem ucu:** Kahve nokta; hale `ID2D1RadialGradientBrush` 3 durak Altın %22 → %10 → %0, yarıçap 13.
5. **İlerleme çizgisi ("Gece" biçimi):** İz ve dolgu `FillRectangle` ile aygıt pikseline oturtulur: kalınlık `max(1, round(1 × ölçek))` px, dolgu genişliği `round(p × 392 × ölçek) / ölçek`. Uç için 48 DIP genişliğinde `ID2D1LinearGradientBrush` (`#C2A579`, alfa durakları u² ile 0 / 0,03 / 0,11 / 0,25 / 0,44 / 0,69 / 1) dolgu dikdörtgenine `PushAxisAlignedClip` ile kırpılır. Parıltı önceden üretilmiş 12×2,5 DIP, σ = 1,5 DIP bulanık küçük bir sprite'tır (ya da `CLSID_D2D1GaussianBlur`). **Yalnız hareket ederken:** uç ve parıltının opaklığı gösterilen ilerlemenin hızına bağlanır: `ucA = clamp(|dp/dt| / 0,08 s⁻¹)`, 150 ms'lik üstel yumuşatmayla; böylece uzun süren bir adımda çizgi duraklayınca parıltı kendiliğinden söner, adım gelince yeniden belirir. "Hazır"da 220 ms'de söner. Çentik ve adım işareti yoktur.
6. **Pencere kenarı:** 1 px, Antrasit %8. Windows 11'de yuvarlak köşe ve sistem gölgesi `DWMWCP_ROUND` ile; açık pencere koyu masaüstünde gölgesiz kalmamalı.
7. **%100 DPI:** 0,75 DIP'lik iskele çizgileri yarım piksel yumuşatılmış görünür; daha keskin istenirse 1 px ve %55 opaklık. 1,75 DIP'lik altın iz her iki ölçekte de nettir.

## Not

Son karedeki "simge üstte, yazı altta" dizilişi, verilen kimlik dosyalarındaki yatay logo düzenlerinden biri değildir. Simge ve yazı ayrı resmî PNG'ler olarak kullanıldı, hiçbiri değiştirilmedi; kilit taşı kenarındaki altın çizgi ve ışık logonun üstüne/arkasına eklenen ayrı çizimlerdir. Kurumsal kimlik kılavuzu bu dizilişe izin vermiyorsa son kare `opus-fortis-yatay-acik-zemin.png` ile değiştirilebilir (o dosyada kemer Antrasit, kilit taşı Gri'dir; renkli simgeyle dolgu o zaman yatay logodaki konuma çizilir).
