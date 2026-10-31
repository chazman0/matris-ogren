# op4 arayüz yönü B — "Atölye · Modern"

Kullanıcı kararı (31.10.2026): Stüdyo yerine **Atölye**, ancak **biraz modernleştirilmiş**. Bronz/kahve–altın vurgu
kullanılmaz; **üst çubuk (başlık + şerit), model ağacı ve Özellikler bölümü beğenildi**, korunur; **Ayarlar** bölümü
eklenir (Program, Görüntü, Dil). Logolar gösterildikleri yerde (başlık çubuğu işareti, Hakkında) değiştirilmez; açılış
ekranı ayrıdır ve aynen kalır.

Görselleri bu klasördeki üreteç çizer: `python3 uret.py` (≈ 35 s; `--hizli` yalnız `ana-kobalt.png`).

| Dosya | İçerik |
|---|---|
| `ana-kobalt.png` · `ana-petrol.png` · `ana-grafit.png` | 1920×1080 ana ekran, üç vurgu seçeneği, aynı içerik: Depo Binası – Tokat OSB (3 kat, HE340A / IPE400 / IPE200 / L100×10), Model sekmesi, 6 kiriş seçili |
| `kucuk.png` | 1366×768, önerilen varsayılan (Kobalt), "sıkı" yoğunluk |
| `ayarlar-program.png` · `ayarlar-goruntu.png` · `ayarlar-dil.png` | 1920×1080, Ayarlar penceresi karartılmış programın üstünde |
| `detay-serit.png` · `detay-panel.png` | 2× kırpım: başlık + şerit; model ağacı + Özellikler + pencere şeridi |
| `karsilastirma.png` | 2400 px: üç vurgu seçeneği (etiketli, renk örnekli) + üç Ayarlar sayfası |
| `belirtec.py` | **Tek belirteç modülü**: bütün renkler, vurgu paletleri, yarıçaplar, aralıklar, gölgeler, yazı ölçeği, modül yükseklikleri |
| `tuval.py` · `sahne.py` · `uret.py` · `ayarlar.py` · `karsilastir.py` | Çizim altyapısı + simgeler · yazılımsal 3B görünüm · ana ekran · Ayarlar · karşılaştırma paftası |

Palet değişimi tek satırdır: `belirtec.py` → `VARSAYILAN_PALET = "kobalt"` (`"petrol"`, `"grafit"`).

## 1. Kavram

**Atölye · Modern**, Atölye'nin yoğun mühendislik iskeletini olduğu gibi tutar, yüzeyini bugünün masaüstü
uygulamalarının diline taşır: katmanlı beyaz/gri yüzeyler, 1 px ince kenarlar, yalnız açılır pencerelerde ve görünüm
üstündeki araçlarda belirgin, panellerde ise neredeyse sezilmeyen gölge; kartlarda, girişlerde ve düğmelerde 6 px
yarıçap; tutarlı 8 px ritim; Noto Sans SemiCondensed'in 400/500/600 ağırlıklarıyla net bir yazı hiyerarşisi. Paneller Stüdyo'daki gibi
yüzmez; **kenara yapışık kalır**, görünüm iskeletin merkezidir. Renk tek bir **vurgu** ailesiyle sınırlıdır ve anlam taşır:
etkin, birincil, odak, seçim. Anlamsal renkler (D/C ölçeği, uyarı, hata) vurgudan bağımsızdır.

İskelet (1920×1080, "rahat" yoğunluk, 1× piksel):

```
┌ Başlık 32 ─ işaret · op4 · hızlı erişim │ proje adı • kaydedilmedi │ kullanıcı · Ayarlar · Yardım · pencere ┐
├ Şerit sekmeleri 32 ─ [Dosya] Model Düzenle Yükler Analiz Tasarım Görünüm Raporlar        Şeridi özelleştir ┤
├ Şerit gövdesi 88 ─ gruplar: büyük düğme 52×60 + 3'lü küçük sütun (20 px) · grup adı altta · başlatıcı ↘   ┤
├ Ray 40 ┬ Model ağacı 272 ┬ Görünüm sekmeleri 32 / 3B görünüm 1256×756 ┬ Özellikler 320 ┬ Pencere şeridi 32 ┤
├ Rıhtım: sekmeler 32 + içerik 48 (Komut · Mesajlar · Tablolar) ─────────────────────────────────────────────┤
├ Komut satırı 32 ─────────────────────────────────────────────────────────────────────────────────────────┤
└ Durum çubuğu 28 ─ yönerge │ ORTO YAKALA SÜRÜKLE · X Y Z │ Kat kapsamı [Bu kat|Benzer katlar|Tüm katlar] · Etkin kat · birim · XYZ · seçili ┘
```

## 2. Atölye'den ne değişti

| Alan | Atölye | Atölye · Modern |
|---|---|---|
| Vurgu | Kahve birincil + Altın seçim | **Tek vurgu ailesi** (Kobalt / Petrol / Grafit); bronz ve kahve–altın arayüzden kalktı (logo dokunulmadı) |
| Yüzeyler | Tek gri zemin + beyaz paneller | Katmanlar: `zemin` krom → `yuzey` paneller → `alan` dolgulu girişler → `zemin2` gömme izler; panel kenarında görünüme 8 px çok yumuşak gölge |
| Yarıçap | 2–4 px karışık | 6 px (kart, giriş, düğme, çip, satır vurgusu) · 4 px (onay kutusu, tuş rozeti) · 8 px (açılır pencere, görünüm pili) · 10 px (kipli pencere) |
| Ritim | 20/22/26/30 px karışık | 8 px ızgara, 4 px yarım adım: 32/32/88 üst krom, 24 px satırlar, 28/32 px denetimler |
| Şerit | Kahve "Dosya", beyaz sekme dili + kahve üst çizgi, 14 px küçük simgeler | Vurgu dolgulu "Dosya" düğmesi; etkin sekme **3 px yuvarlak alt çizgi**; büyük simge 24, küçük simge **16** (tutarlı); grup adı 10/500 ortalı; diyalog başlatıcısı ↘ simgesi; ayraçlar 1 px `cizgi2` |
| Model ağacı | Sekme metinleri, kutulu arama, düz satırlar, altın şerit | **Segmentli denetim** (Model / Göster / Tablolar / Raporlar), dolgulu arama + Ctrl+F rozeti, 24 px satır, **girinti kılavuzları**, seçili satır içe yerleşik 6 px yuvarlak ton + 3 px vurgu + hap rozet, etkin kat "etkin" çipi |
| Özellikler | Kutulu girişler, gri bölüm bantları | **Dolgulu (kenarsız) alanlar**, odakta beyaz + vurgu kenar + 3 px **odak halkası**; bölümler ince ayraçla, kapalı bölüm sağda **özet** (Tasarım: "ÇYTHYE 2018 · D/C 0,62") |
| Pencere şeridi | Altın şerit + altın zemin | Vurgu tonu yuvarlak zemin + 3 px vurgu çizgisi; sığmayan düğmeler yalnız simge |
| Rıhtım / komut | Kahve "Komut:" | Vurgu imleç çizgisi + komut simgesi; ipuçları **tuş rozetleri** (Ctrl Q, Tab, Enter, Esc); TR · EN takma ad çipi |
| Durum çubuğu | Düz metin anahtarlar | **Çipler** (nokta göstergeli ORTO / YAKALA / SÜRÜKLE), kare X Y Z kilitleri, kat kapsamı **vurgu dolgulu segmentli denetim**, etkin kat ve birim açılır çip, seçim çipi "● 6 seçili 12 tutamaç" |
| 3B görünüm | Beyaz→gri gradyan, altın seçim, kahve üzerinde | Gradyan + model arkasında **ortam ışığı**; seçim = vurgu 2 px kontur + **yumuşak hale** + açık dolgu; üzerinde = açık vurgu 1 px; etkin katın seviye çizgisi vurgu; araç pili ve düğme grubu tek yüzen kapta; gezinme ipucu çipi |
| Tutamaçlar | Altın başlangıç / kahve bitiş | **Dolu kare = başlangıç, içi boş kare = bitiş** (renk körlüğünde de ayrışır), orta nokta halka; Özellikler'deki "Başlangıç ucu / Bitiş ucu" işaretleri aynı biçim |
| D/C ölçeği | Mavi–yeşil–sarı–turuncu–kırmızı | Aynı sıra, **renk körlüğüne göre ayarlandı** (§3.4) |
| Ayarlar | Yok | **Kipli Ayarlar penceresi**: arama, kategori listesi, kartlı sayfalar, değişiklik işareti, Varsayılana dön, İptal / Uygula / Tamam (§7) |
| Kontrast | `metin3` #8C8C8C (3,4:1) | `metin3` **#646B75** (beyazda 5,4:1, zeminde 4,9:1); bütün metin çiftleri ≥ 4,5:1 (§3.5) |

## 3. Renk belirteçleri (`belirtec.py`)

### 3.1 Nötr yüzeyler (üç palette ortak)

| Belirteç | Hex | Kullanım |
|---|---|---|
| `zemin` | `#F3F4F6` | Krom: başlık, şerit sekme satırı, ray, pencere şeridi, rıhtım sekmeleri, durum çubuğu, görünüm sekmeleri |
| `zemin2` | `#E9ECEF` | Gömme iz: segmentli denetim yuvası, kaydırıcı izi |
| `yuzey` | `#FFFFFF` | Paneller, şerit gövdesi, kartlar, açılır pencereler |
| `yuzey2` | `#F8F9FA` | Tablo başlığı, Ayarlar sol gezinti |
| `sayfa` | `#F5F6F8` | Ayarlar sayfa zemini (kartların arkası) |
| `alan` / `alan_kenar` | `#F3F4F6` / `#E3E6EA` | Dolgulu giriş alanı ve 1 px iç kenarı |
| `hover` / `basili` | `#F0F2F4` / `#E7EAEE` | Satır ve düğme üzerinde / basılı (nötr) |
| `cizgi` / `cizgi2` | `#E1E4E8` / `#ECEEF1` | Panel kenarı, güçlü ayraç / ince ayraç, satır çizgisi, girinti kılavuzu |
| `kenar` | `#CDD2D8` | İkincil düğme, onay kutusu, radyo, tuş rozetinin alt kenarı |
| `metin` | `#14181B` | Birincil metin (Antrasit) |
| `metin2` | `#4A515A` | Alan etiketi, ikincil metin, pasif sekme |
| `metin3` | `#646B75` | Açıklama, grup adı, yer tutucu, birim |
| `metin4` | `#A0A6AE` | Yalnız devre dışı ve kapalı simge (metin için kullanılmaz) |
| `simge` / `simge2` | `#353B43` / `#59606A` | Şerit, ray simgeleri / panel ve görünüm simgeleri |
| `golge` / `karartma` | `#0F172A` | Gölge rengi (saydamlıkla) / kipli pencere arkası %38 |

### 3.2 Vurgu paletleri (bronz yok)

Rol tanımı: `vurgu` birincil düğme, etkin sekme çizgisi, açık anahtar, onay kutusu, basılı araç simgesi, bağlantı;
`vurgu_koyu` üzerinde/basılı birincil; `vurgu_metin` beyaz ve ton zeminde vurgu metni; `vurgu_ton`/`vurgu_ton2` basılı
araç, etkin gezinti satırı, açık çip; `secim` model konturu, seçili ağaç satırı, seçim rozeti, tutamaçlar;
`secim_ton`/`secim_ton2` seçili satır ve seçim çipi; `secim_dolgu` modelde seçili elemanın taban rengi;
`hover_model` modelde üzerinde konturu; `odak` odak halkası (3 px, %28) ve odaktaki alan kenarı.

| Belirteç | A — Kobalt mavisi (önerilen) | B — Petrol yeşili | C — Grafit (tek renk) |
|---|---|---|---|
| `vurgu` | `#2563EB` | `#0F766E` | `#262B31` |
| `vurgu_koyu` | `#1D4ED8` | `#115E59` | `#111418` |
| `vurgu_metin` | `#1D4ED8` | `#0F6B64` | `#262B31` |
| `vurgu_ton` | `#EEF3FE` | `#E8F4F2` | `#EBEDF0` |
| `vurgu_ton2` | `#CFDDFC` | `#BFE0DB` | `#D3D8DE` |
| `secim` | `#2563EB` | `#0F766E` | `#2F6FDB` (yalnız seçim mavisi) |
| `secim_ton` | `#EAF1FE` | `#E6F3F1` | `#ECF2FD` |
| `secim_ton2` | `#C9DAFC` | `#BCDDD8` | `#C9DBF8` |
| `secim_dolgu` | `#C9DBFB` | `#BFE3DD` | `#CCDDF8` |
| `hover_model` | `#5B8FF2` | `#3E9C93` | `#6E9BE6` |
| `odak` | `#2563EB` | `#0F766E` | `#2F6FDB` |

- **A Kobalt**: vurgu = seçim; tek renkli, en tanıdık dil. Önerilen varsayılan.
- **B Petrol**: sakin mühendislik tonu. D/C ölçeğinin yeşili (`#2BA37B`) bilinçli olarak daha açık ve sarıya yakın tutuldu; ikisi yan yana gelmez (seçim D/C kipinde ayrı gösterilir).
- **C Grafit**: arayüz antrasit/gri; **mavi yalnız seçimde ve odakta**. Birincil düğme, Dosya, etkin sekme çizgisi, anahtar ve kat kapsamı grafittir.

### 3.3 Anlamsal renkler (vurgudan bağımsız)

| Belirteç | Hex | Kullanım |
|---|---|---|
| `ok` / `ok_ton` | `#1E7B4C` / `#E8F5EE` | Başarılı sonuç ("6 kiriş eklendi"), çakışma yok |
| `uyari` / `uyari_ton` / `uyari_dolgu` | `#A15C07` / `#FEF3DC` / `#E9A23B` | Mesaj sayacı, kaydedilmedi noktası |
| `hata` / `hata_ton` / `hata_kenar` | `#C0362C` / `#FCEBEA` / `#F2C4C0` | Yetersiz eleman, silme simgesi |
| `eksen_x/y/z` | `#C0362C` / `#1E7B4C` / `#2E6AB3` | Eksen üçlüsü |

### 3.4 D/C ölçeği (5 eşik, kullanıcı düzenler)

| Aralık | ≤ 0,50 | 0,50–0,70 | 0,70–0,90 | 0,90–1,00 | > 1,00 |
|---|---|---|---|---|---|
| Renk | `#2E6AB3` | `#2BA37B` | `#F3D84C` | `#DD6A1C` | `#A61B2E` |
| Rozet metni | beyaz 5,5:1 | Antrasit 5,6:1 | Antrasit 12,5:1 | Antrasit 5,2:1 | beyaz 7,5:1 |

Yeşilden kırmızıya sıra korunur; parlaklık basamaklı seçildi (CIELAB L 44 → 60 → 86 → 58 → 36). Machado (2009)
benzetimiyle komşu sınıflar arası en küçük fark: döteranopide ΔE 27, protanopide ΔE 35, tritanopide ΔE 21 (Atölye
ölçeğinde döteranopide sarı–turuncu yalnız ΔE 9 idi). Renk tek ipucu değildir: lejantta sayısal eşik kutuları, tabloda
sayı + "Yetersiz" metni, aşan eleman sayısı rozeti.

### 3.5 Kontrast denetimi (WCAG 2.x)

| Çift | Oran | Çift | Oran |
|---|---|---|---|
| `metin` / `yuzey` | 17,9 | `metin3` / `zemin` | 4,9 |
| `metin2` / `yuzey` | 8,0 | `metin3` / `alan` | 4,9 |
| `metin2` / `zemin2` (segment) | 6,8 | `metin3` / `sayfa` | 5,0 |
| `metin3` / `yuzey` | 5,4 | `uyari` / `uyari_ton` (sayaç) | 4,7 |
| beyaz / `vurgu` (A · B · C) | 5,2 · 5,5 · 14,3 | `vurgu_metin` / `vurgu_ton` (A · B · C) | 6,0 · 5,6 · 12,2 |
| beyaz / `secim` rozeti (A · B · C) | 5,2 · 5,5 · 4,8 | `ok` · `hata` / `yuzey` | 5,3 · 5,5 |

Metin olmayan öğeler (anahtar izi, seçim konturu, odak kenarı) ≥ 3:1: `secim` görünüm zemininin alt tonunda
4,2 / 4,4 / 3,9.

### 3.6 Model (3B görünüm) renkleri

| Belirteç | Hex | | Belirteç | Hex |
|---|---|---|---|---|
| `vp_ust` → `vp_alt` | `#FBFCFD` → `#E4E8EC` | | `kolon` / `kiris` | `#CBD0D7` / `#D3D7DD` |
| `vp_isik` (ortam ışığı, model arkasında) | `#FFFFFF` | | `tali` / `asik` / `capraz` | `#D9DDE2` / `#D9DDE2` / `#C4C9D0` |
| `izgara` / `izgara_ana` / `aks` | `#B7BCC4` / `#9AA0A8` / `#7E858F` | | `doseme` / `temel` | `#E3E5E8` / `#D6D8DB` |
| `kenar` / `kenar_ince` / `kenar_doseme` | `#454B53` / `#5A616A` / `#8E939A` | | | |

Işık yönü (−0,45, −0,50, +0,74); yüzey katsayısı 0,50 + 0,40·lambert + 0,12·gök; yumuşak yer gölgesi + kolon dibi teması.

| Durum | Görünüm |
|---|---|
| Seçili | `secim_dolgu` taban (gölgeleme 0,84–1,0), iç kenarlar `secim` %60, dış siluet **2 px `secim`** + 5 px'lik çizginin 3,2 px Gauss bulanıklığı %42 **hale** |
| Üzerinde | `hover_model` 1 px kenarlar %80; ipucu kartı (6 px yarıçap, açılır gölge): "● K2-A1 Kolon · HE340A · S355" |
| Tutamaç | Başlangıç: beyaz çerçeveli **dolu** `secim` kare 12 px · Bitiş: `secim` çerçeveli **içi boş** kare · Orta: beyaz daire + 1,5 px `secim` halka · Ölçü etiketi: beyaz, `secim` kenar, 600 ağırlık, yazılabilir |
| Etkin kat | Seviye çizgisi ve üçgen `vurgu`, etiket 600 ("+9,00 Kat 2") |
| Yalnız seçiliyi göster | Diğerleri %85 saydam (Ayarlar'dan %60 / %85 / gizle) |

## 4. Yazı ölçeği

**Noto Sans SemiCondensed** (OFL, `kimlik/fontlar/notosans-*`; kullanıcı kararı 31.10.2026, MIMARI §25.1): Noto Sans
v2.015 değişken dosyasından wdth 87,5 ile kesilmiş statik 400 / 500 / 600 / 700 örnekleri (imgui_freetype değişken eksen
kurmaz); belirteç `belirtec.py` `YAZI_AILESI`, gömme `araclar/kimlik_uret.py` `ARAYUZ_YAZI`. Metin imgui_freetype ile
LightHinting | ForceAutoHint, yatay piksel yakalama, tam piksel boyut ve konumla çizilir; ailede olmayan simgeler
(≈ ≤ ≥ ← → ↺ ▾ …) Inter alt kümesinden MergeMode ile birleşir. Açılış ekranı (marka) Inter Light ve Cormorant Garamond'la
kalır. Türkçe glifler (İ ı Ş ş Ğ ğ Ü ü Ö ö Ç ç) bütün boyutlarda bulunur ("İptal", "İş parçacığı", "ÖNİZLEME", "ÇİZ",
"KİRİŞ"). Boyutlar aşağıdaki tablodadır; Ayarlar › Görüntü › **Yazı boyutu** (Küçük / Orta / Büyük) bütün ölçeği
`YAZI_BOYUTU` çarpanıyla (11/12 · 1 · 7/6; gövde 11 · 12 · 14 px) büyütür, yazıya bağlı modül ölçüleri de aynı oranla
büyür (§7.2).

| Rol | Boyut / ağırlık | Yer |
|---|---|---|
| Sayfa başlığı | 20 / 600 | Ayarlar sayfa başlığı |
| Pencere başlığı | 15 / 600 | "Ayarlar", iletişim kutuları |
| Başlık | 13 / 600 | Panel ve kart başlığı, nesne adı ("Kiriş"), "op4", gezinti kategorisi |
| Gövde | 12 / 400 · 500 · 600 | Alan değeri ve etiketi (400), düğme ve sekme (500), etkin sekme, seçili satır, bölüm başlığı (600) |
| Etiket | 11 / 400 · 500 · 600 | Şerit düğme adı, durum çubuğu, rıhtım satırı, görünüm pili, açıklama satırı (400) |
| Küçük | 10 / 400 · 500 · 600 | Şerit grup adı, tuş rozeti, durum çipleri, ipucu |
| Rozet / bölüm | 9 / 600 | Sayaç rozeti; BÜYÜK HARF bölüm etiketi (ÇİZ / SEÇ / ÇİZGİ KALINLIKLARI), harf aralığı +0,6 px |

Sayılar `tnum` ile; ondalık virgül, binlik ince boşluk ("1 842", "5 670", "+13,50").

## 5. Aralık, yarıçap, gölge ve modül ölçüleri

- **8 px ızgara, 4 px yarım adım.** Panel iç dolgusu 12 (ağaç ve Özellikler), kart iç dolgusu 16, kartlar arası 16,
  Ayarlar sayfa kenarı 32, sütun arası 24.
- **Yarıçap** (`R`): `kucuk` 4 · `orta` 6 (ana) · `buyuk` 8 · `pencere` 10 · `hap` (anahtar, sayaç).
- **Gölge** (`GOLGE`, bulanıklık / dy / saydamlık; iki katman: geniş ortam + dar yakın): `panel` 6/0/%6 (panelden
  görünüme 8 px geçiş) · `kabarik` 2/1/%10 (segmentteki seçili hap) · `yuzen` 8/2/%10 (görünüm pili) · `acilir`
  14/6/%14 (mini araç çubuğu, ipucu, açılır liste) · `kipli` 28/12/%24 (Ayarlar).

| Modül (px, 1×) | Rahat (≥ 1600×900) | Sıkı |
|---|---|---|
| Başlık · şerit sekmesi · şerit gövdesi | 32 · 32 · 88 (= 152) | 28 · 28 · 76 (= 132) |
| Ray · model ağacı · Özellikler · pencere şeridi | 40 · 272 · 320 · 32 | 36 · 232 · 288 · 28 |
| Görünüm sekmeleri · rıhtım sekmesi · rıhtım içeriği | 32 · 32 · 48 | 28 · 28 · 40 |
| Komut satırı · durum çubuğu | 32 · 28 | 28 · 26 |
| Panel başlığı · nesne başlığı · panel alt çubuğu | 40 · 48 · 48 | 36 · 48 · 44 |
| Segment · arama · ağaç satırı · özellik satırı · alan · bölüm | 28 · 28 · 24 · 24 · 20 · 28 | 24 · 24 · 22 · 22 · 20 · 24 |
| Büyük şerit düğmesi · küçük düğme satırı · ray düğmesi | 60 yükseklik (≥ 52 genişlik) · 20 · 32 | 48 · 18 · 28 |

Simge kutuları: 24 (büyük şerit), 18 (ray), 16 (küçük şerit, panel başlığı, görünüm grubu), 14 (ağaç, pil), 12–10
(sevron, başlatıcı). Çizgi kalemi 1,5 px (küçüklerde 1,3–1,4), yuvarlak birleşim.

## 6. Bileşenler

| Bileşen | Tanım |
|---|---|
| **Birincil düğme** | `vurgu` dolgu, 6 px, metin beyaz 12/600; 1 px aşağı %10 gölge; üzerinde `vurgu_koyu`. Yükseklik 28 (panel), 32 (pencere). Bir görünümde tek birincil (Uygula, Tamam) |
| **İkincil düğme** | `yuzey` + 1 px `kenar`, 12/500 `metin`, 1 px %6 gölge; üzerinde `hover`, basılı `basili`; devre dışı metin `metin4` |
| **Hayalet düğme / bağlantı** | Zemin yok, `vurgu_metin` 500 ("Ayrıntılı…", "Profili dışa aktar…") |
| **Dolgulu giriş** | `alan` + 1 px `alan_kenar`, 6 px, iç dolgu 8; isteğe bağlı sol simge ve sağ ek (Ctrl+F, birim). Odakta `yuzey` + 1 px `odak` kenar + 3 px `odak` %28 halka + `odak` imleç. Çoklu seçimde "(farklı)" `metin3` |
| **Açılır liste** | Dolgulu giriş + sağda 10 px sevron; salt okunur türünde `yuzey` + `kenar` |
| **Segmentli denetim** | `zemin2` iz (6 px), 2 px iç boşluk; seçili parça beyaz **kabarık hap** (4 px, `kabarik` gölge), 600; seçili olmayanlar 500 `metin2`, aralarında 1 px `kenar` ayraç (seçiliye komşu değilse). **Vurgu türü**: seçili parça `vurgu` dolgulu — yalnız işlem kapsamını değiştiren anahtarlarda (kat kapsamı) |
| **Anahtar (toggle)** | 28×16 hap; açık `vurgu`, kapalı `#C3C9D0`; 12 px beyaz düğme + %18 gölge; 120 ms kayma (Hareketi azalt açıksa anında) |
| **Onay kutusu / radyo** | 14 px, 4 px yarıçap; işaretli `vurgu` + beyaz onay. Radyo 14 px; seçili `vurgu` daire + beyaz iç nokta |
| **Sekmeler** | Şerit ve rıhtım: metin sekmesi, etkin 600 + **3 px yuvarlak `vurgu` alt çizgi**. Görünüm sekmeleri: belge sekmesi, etkin olan üst köşeleri 6 px yuvarlak, görünüme kesintisiz bağlanır, simgesi `vurgu` |
| **Ağaç satırı** | 24 px; girinti 16; sevron + 14 px simge + 12 px metin + sağda sayı/kot (`tnum`, `metin3`). Üzerinde: içe yerleşik (6 px kenar boşluğu) `hover` 6 px yuvarlak zemin, sağda göz ve ⋯ belirir. Seçili: `secim_ton` + sol 3 px `secim` çizgi + `secim` simge + 600 + hap rozet "6 seçili". Etkin kat: 600, `vurgu` simge, "etkin" çipi + göz. Girinti kılavuzları 1 px `cizgi2`. **Zebra yok** |
| **Özellik satırı** | 24 px; etiket sütunu 104 (12/400 `metin2`), değer alanı 20 px dolgulu; katalog alanının yanında 20×20 ⋯ düğmesi; bölüm başlığı 28 px (sevron + 12/600), bölümler arası 1 px `cizgi2`; kapalı bölüm sağda özet/rozet |
| **Tablo satırı** | 28 px (Ayarlar), 24 px (rıhtım tabloları); başlık `yuzey2` 11/600 `metin2`; satır ayracı 1 px `cizgi2`; **zebra yok**; üzerinde `hover` 4 px yuvarlak, satır eylemleri (⋯) yalnız üzerindeyken; düzenlenen satır `vurgu_ton` |
| **Çip** | 20 px, 6 px; türler: `acik` (vurgu tonu + nokta), `kapali` (1 px `cizgi`, `metin3`), `secim`, `notr` (`zemin2`). Durum çubuğu: ORTO / YAKALA / SÜRÜKLE, seçim sayacı, TR · EN |
| **Rozet** | 16 px hap, 9/600 `tnum`; seçim (`secim` + beyaz), uyarı sayacı (`uyari_ton` + `uyari`), D/C (ölçek rengi + otomatik metin rengi) |
| **Tuş rozeti** | 18 px, 4 px, `yuzey` + 1 px `cizgi` + 1 px koyu alt kenar (`kenar`), 10/500 `metin2`; birleşik tuşlar ayrı rozetler (Ctrl · Shift · F) |
| **Açılır pencere** (mini araç çubuğu, ipucu, menü, kat kapsamı önizlemesi) | `yuzey`, 1 px `cizgi`, 8 px (ipucu 6 px), `acilir` gölgesi; mini araç çubuğu 32 px, alanlar simge + değer + sevron, ayraç 1 px; seçime 6 px ok |
| **Görünüm pili / düğme grubu** | Beyaz %96, 1 px `cizgi`, 8 px, `yuzen` gölge, 32 px; çubuk ↔ ekstrüde ikonlu segment |
| **Kaydırıcı** | 4 px `zemin2` iz, dolu kısım `vurgu`, 16 px beyaz düğme + `kenar` + 6 px `vurgu` merkez |
| **Adımlayıcı** | Dolgulu alan, değer 12/500 + birim `metin3`, sağda − / + (28 px kare, 1 px ayraç) |
| **Kaydırma çubuğu** | 4 px hap, `metin` %22, iz görünmez; üzerinde 8 px'e genişler |
| **Odak halkası** | Bütün etkileşimli öğelerde klavye odağında 3 px `odak` %28, öğenin yarıçapı + 3 |
| **Değişti işareti** (Ayarlar) | Etiketin solunda 6 px `vurgu` nokta + kontrol yanında "Varsayılan: …" `metin3` |

## 7. Ayarlar penceresi

**Açılış:** başlık çubuğundaki dişli, Dosya › Ayarlar, `Ctrl+,`, komut satırında `ayarlar` / `settings`. Kipli
pencere, arkası %38 karartılır; 1440×960 (DPI ile çarpılır, ekranın %94'üne kırpılır), 10 px yarıçap, `kipli` gölge.

**Yapı:**

```
┌ Başlık 56 ─ [⚙] Ayarlar · Kullanıcı ayarları · op4 0.1.0 · Ctrl+,                                          ✕ ┐
├ Gezinti 256 ─────────────┬ Sayfa (zemin `sayfa`) ──────────────────────────────────────────────────────────┤
│ [⌕ Ayarlarda ara  Ctrl F]│  Program ayarları  (20/600)                                                       │
│ ⚙ Program ayarları  ⌄    │  açıklama (12/400)                                                                │
│   ┃ Başlangıç            │  ┌ kart ─────────────────┐  ┌ kart ─────────────────┐   iki sütun, 16 px aralık   │
│   │ Kayıt ve kurtarma    │  │ simge  Başlık 13/600  │  │                        │   kart başlığı 40 px        │
│   │ …                    │  │ satır 44 (açıklamalı) │  │                        │   satır ayracı cizgi2       │
│ 🖥 Görüntü ayarları  ›   │  └───────────────────────┘  └────────────────────────┘                            │
│ 🌐 Dil ayarları      ›   │                                                                                    │
│ ─ ayarlar.json           │                                                                                    │
│   İçe aktar · Dışa aktar │                                                                                    │
├ Alt çubuk 64 ─ [↺ Varsayılana dön ▾] Bu sayfa ya da tüm ayarlar    ● 1 değişiklik · …   [İptal] [Uygula] [Tamam] ┤
```

- **Gezinti:** üç kategori (36 px, 13/600, etkin olan `vurgu_ton` zemin + `vurgu_metin`); etkin kategorinin alt
  bölümleri (30 px, 12/400) dikey kılavuz üzerinde **kaydırma izleyicili** (görünen bölüm 3 px `vurgu` çizgi + 600);
  tıklama bölüme kaydırır.
- **Arama** (Ctrl+F): ayar kayıt defterindeki etiket, açıklama ve anahtar sözcüklerde arar (ör. "MSAA", "yedek",
  "dil", "tf"); sonuçlar sayfa sınırı olmadan tek listede, eşleşen sözcük vurgulu; Esc temizler.
- **Satır:** solda etiket 12/500 + açıklama 11/400 `metin3`, sağda denetim (28 px). Varsayılandan farklı ayar:
  `vurgu` nokta + "Varsayılan: …".
- **Varsayılana dön ▾:** menü "Bu sayfayı varsayılana döndür" / "Tüm ayarları varsayılana döndür" (onay sorar).
- **İptal** değişiklikleri atar (Esc), **Uygula** kaydeder ve açık kalır (değişiklik yoksa devre dışı), **Tamam**
  uygular ve kapatır (Enter). Değişiklik sayısı alt çubukta. Ayarlar `%APPDATA%\op4\ayarlar.json` dosyasına yazılır;
  İçe/Dışa aktar firma profili paylaşımı içindir.
- Görüntü ayarları **canlı önizlenir** (vurgu rengi, yoğunluk, çizgi kalınlıkları arkadaki programda hemen görünür);
  İptal eski duruma döner.

### 7.1 Program ayarları

| Bölüm | Ayar | Denetim | Varsayılan | Seçenekler / aralık |
|---|---|---|---|---|
| Başlangıç | Açılışta | radyo (açıklamalı) | **Başlangıç paneli** | Başlangıç paneli · Son projeyi aç · Boş çalışma alanı |
| | Son dosyalar listesi | adımlayıcı | 10 öğe | 0–30 |
| Kayıt ve kurtarma | Otomatik kayıt | anahtar | Açık | — |
| | Kayıt aralığı | segment | 5 dk | 2 · 5 · 10 · 15 dk |
| | Kurtarma dosyaları | açılır | 7 gün sakla | 1 gün · 7 gün · 30 gün · süresiz; klasör `%LOCALAPPDATA%\op4\Kurtarma`; çökme sonrası açılışta geri yükleme önerilir |
| | Kaydederken yedek al (.op4.bak) | anahtar | Açık | — |
| Geri al | Geri al derinliği | adımlayıcı | 100 adım (taslakta 200: değiştirilmiş örnek) | 10–1000; ≈ 1,2 MB / adım |
| | Görünüm değişikliklerini geçmişe ekle | anahtar | Kapalı | döndür, yakınlaştır, kesit düzlemi |
| Varsayılan birimler | Kuvvet · Uzunluk · Kesit · Gerilme · Sıcaklık · Açı | açılır ×6 | kN · m · mm · MPa · °C · derece | N/kN/tf · mm/cm/m · mm/cm · MPa/kN/m²/kgf/cm² · °C · derece/radyan; yeni projelerde geçerli |
| Klasörler | Şablon klasörü | yol + Gözat… | `%USERPROFILE%\Belgeler\op4\Şablonlar` | — |
| | Proje klasörü | yol + Gözat… | `%USERPROFILE%\Belgeler\op4\Projeler` | — |
| Hesap motoru | İş parçacığı sayısı | açılır | Otomatik (mantıksal çekirdek − 1) | 1 … çekirdek sayısı |
| | Bellek sınırı | kaydırıcı + değer | sistem belleğinin %50'si (taslakta 16 / 32 GB) | 2 GB – %90 |
| | Zaman aşımı | adımlayıcı | 30 dk | 1–600 dk, 0 = sınırsız; süre dolunca sorulur |
| | Arka planda çöz | anahtar | Açık | arayüz kilitlenmez, ilerleme durum çubuğunda |
| Kısayollar | Profil | açılır | op4 varsayılan | kullanıcı profilleri; Profili dışa aktar… (.json) |
| | Arama · Kısayol ekle · satıra çift tık = tuş yakalama | tablo | — | yakalama alanı odak halkalı, "Tuşlara basın… (geçerli: Home)"; çakışma anında uyarı; alt bilgide "7 / 142 komut · çakışma yok" |

Varsayılan kısayollar (taslakta görünenler): Hızlı başlat / komut satırı **Ctrl+Q** · Çöz **F5** · Seç ve Süz
**Ctrl+Shift+F** · Seçimi tersine çevir **Ctrl+K** · Önceki seçim **Ctrl+J** · Tam görünüm **Home** · Seçiliye
yakınlaş **Shift+Space** · Kat kapsamı **Alt+1 / 2 / 3** · Render kipleri **Ctrl+1…5** · Yakala **F3** · Orto **F8** ·
Ayarlar **Ctrl+,**. Tek harfli anında kısayol yoktur (MIMARI §5.4); harfler komut satırına gider.

### 7.2 Görüntü ayarları

| Bölüm | Ayar | Denetim | Varsayılan | Seçenekler / aralık |
|---|---|---|---|---|
| Grafik | Grafik bağdaştırıcısı | açılır | Otomatik — yüksek performanslı | bağdaştırıcı listesi; altında DirectX 12 özellik düzeyi ve bellek |
| | Kenar yumuşatma (MSAA) | segment | 4× | Kapalı · 2× · 4× · 8× |
| | Görüntü kalitesi | segment | Dengeli | Taslak · Dengeli · Yüksek (profil ayrıntısı, eğri bölme, gölge) |
| | Ağ toleransı | segment | ±%2 | ±%1 · ±%2 · ±%5 — analiz ağı eniyilemesi en kaba uygun ağı seçer (MIMARI §17, GCI) |
| Model görünümü | Arka plan | segment + iki renk + önizleme | Gradyan, `#FBFCFD` → `#E4E8EC` | Gradyan · Düz |
| | Eleman kenarı · Aks çizgisi · Seçim konturu | kaydırıcı ×3 | 1,0 px · 1,0 px · 2,0 px (taslakta 2,5: değiştirilmiş örnek) | 0,5–3 · 0,5–3 · 1–4 px |
| | Etiket boyutu | segment | Orta (11 px) | Küçük 10 · Orta 11 · Büyük 13 px |
| | Eksen balonları | anahtar + konum | Açık · Baş | Baş · Son · İkisi |
| | Kat düzlemleri | anahtar + dolgu | Açık · %6 | dolgu %0–20; etkin kat vurgulu |
| | Yer gölgesi ve ortam ışığı | anahtar | Açık | — |
| | Çalışma ızgarası | anahtar + aralık | Açık · 1,00 m | 0,10–10 m, uzaklıkla solar |
| Seçim ve üzerinde | Önizleme | canlı örnek | — | seçili (2 px + hale) · üzerinde (1 px) · normal |
| | Vurgu rengini izle | anahtar | Açık | kapalıyken seçim ve üzerinde rengi ayrı seçilir |
| | Seçim · üzerinde rengi | renk ×2 | palet `secim` · `hover_model` | izleme açıkken salt okunur |
| | Yalnız seçiliyi göster (Ctrl+5) | segment | %85 saydam | %60 saydam · %85 saydam · Gizle |
| Arayüz | Vurgu rengi | seçim çipleri | **Kobalt** | Kobalt · Petrol · Grafit (anlamsal renkler değişmez) |
| | Arayüz ölçeği | açılır | Sistemi izle | %100 · %125 · %150 · %175 · %200; yazı atlası yeniden kurulur |
| | Yoğunluk | segment | Otomatik | Rahat · Sıkı · Otomatik (1600×900 altında Sıkı) |
| | Yazı boyutu | segment | **Orta** | Küçük · Orta · Büyük — yazı ölçeğinin tamamı `YAZI_BOYUTU` çarpanıyla (11/12 · 1 · 7/6; gövde 11 · 12 · 14 px @ 100 %); satır, şerit, ağaç ve özellik satırı yükseklikleri yazıyla birlikte büyür (arayüz ölçeği = DPI × çarpan; metin kırpılmaz); Otomatik yoğunluk ölçeklenmiş alanı izler; canlı önizleme, İptal geri döner (`ayarlar.json` `arayuz.yazi_boyutu`) |
| | Hareketi azalt | anahtar | Kapalı (sistem ayarını izler) | geçişler anında |
| | Açılış ekranı | iki küçük resim + radyo | **Açık** | Açık · Koyu (`kimlik/acilis`, `kimlik/acilis-koyu`; logo ve canlandırma aynı) |

### 7.3 Dil ayarları

| Bölüm | Ayar | Denetim | Varsayılan | Seçenekler |
|---|---|---|---|---|
| Arayüz dili | Dil | iki seçenek kartı + **canlı önizleme** | **Türkçe** | Türkçe · English. Önizleme iki dili yan yana gösterir: şerit sekmeleri, Özellikler satırları (Kesit/Section, Başlangıç ucu: Mafsal / Start release: Pinned), komut satırı, kat kapsamı. Yeniden başlatmadan uygulanır |
| Sayı ve tarih | Ondalık ayırıcı | segment | Virgül (1,5) | Virgül · Nokta |
| | Binlik ayırıcı | segment | İnce boşluk | İnce boşluk · Nokta · Yok (ondalık nokta seçiliyken "Nokta" kapanır) |
| | Tarih biçimi | açılır | 31.10.2026 (GG.AA.YYYY) | GG.AA.YYYY · YYYY-AA-GG · 31 Ekim 2026 |
| | Tablo ondalıkları | adımlayıcı | 3 basamak | 0–6 |
| | Örnek | salt okunur | "12 345,678 kN · 31.10.2026" | — |
| Birim sistemi | Birim sistemi | segment + Ayrıntılı… | **kN · m** | kN · m · tf · m; dönüşüm örneği (4,20 kN/m ⇄ 0,428 tf/m; 1 842 kN ⇄ 187,8 tf). Ayrıntılı… → Program › Varsayılan birimler |
| Komut takma adları | İngilizce takma adları kabul et | anahtar | Açık | kolon = column, kiriş = beam |
| | Esnek Türkçe eşleme | anahtar | Açık | i/ı · s/ş · c/ç · g/ğ · o/ö · u/ü aynı sayılır (Türkçe klavyesiz yazım) |
| | Takma ad tablosu | arama + tablo + Takma ad ekle | op4 listesi (142 komut · 286 takma ad) | Komut · Türkçe · English · Kısa (KOLON kolon column KL, KİRİŞ kiriş beam KR, ÇAPRAZ çapraz brace ÇP, DÖŞEME döşeme slab DŞ, AKS aks grid AK, KAT kat story KT, SEÇSÜZ seçsüz selectfilter SS, KATKOPYALA katkopyala copystory KK, TAŞI taşı move TŞ, KOPYALA kopyala copy KP, ÇÖZ çöz solve F5); CSV olarak dışa aktar |

## 8. Panel ve yerleşim kuralları (Atölye'den korunan, güncellenen)

- **Başlık çubuğu** 32: Opus Fortis işareti (koyu simge PNG'si, ölçeklenir, yeniden çizilmez) + "op4" 13/600 + hızlı
  erişim (Yeni, Aç, Kaydet, Yazdır │ Geri al, Yinele); ortada dosya adı + `uyari_dolgu` nokta "kaydedilmedi"; sağda
  kullanıcı, **Ayarlar** (dişli), Yardım, pencere düğmeleri.
- **Şerit**: Model sekmesi grupları Atölye ile aynı (Aks & Kat · Kolon · Kiriş · Çapraz · Döşeme · Duvar · Temel ·
  Hızlı yerleştir · Seç); basılı araç `vurgu_ton` + `vurgu_ton2` + `vurgu` simge + `vurgu_metin` 600; iletişim kutusu
  olan gruplarda ↘ başlatıcı. Sağda göz simgeli "Şeridi özelleştir" ve daralt.
- **Sol ray** 40: ÇİZ (11 araç, etkin araç `vurgu_ton` + sol 3 px `vurgu` çizgi) · SEÇ (10 seçim anahtarı; açık =
  beyaz kutu + 1 px `cizgi` + `vurgu` nokta, kapalı = `metin4`) · doğrudan değiştirme (açık: `secim_ton`) · anahtarları gizle.
- **Model ağacı** 272: başlık 40 (pin, kapat) → segment 28 → arama 28 → satırlar 24 → alt bilgi 32 ("263 eleman ·
  80 düğüm · 3 kat" + seçileni ağaçta göster).
- **Görünüm**: sekmeler (3B görünüm · Plan – Kat 2 (+9,00) · Yükselti – Aks 1 · +); sol üst pil (3B ▾ · Perspektif ▾
  · Tüm katlar ▾ · Renk: türe göre ▾ · çubuk ↔ ekstrüde); sağ üst dört düğmelik grup (tam görünüm, seçiliye yakınlaş,
  kesit düzlemi, gösterim seçenekleri — küp yok); sol alt eksen üçlüsü yarı saydam daire üstünde; sağ alt gezinme çipi
  ("Sol sürükle: kaydır · Shift+sol: döndür · Tekerlek: yakınlaş", MIMARI §25 gezinme kuralı).
- **Özellikler** 320: başlık 40 (ara, pin, kapat) → nesne başlığı 48 (32 px `secim_ton` simge kutusu, "Kiriş" +
  "6 seçili" rozeti, alt satır kesit · malzeme · kat · aks, ⋯) → bölümler Genel / Kesit / Konum / Serbestlikler /
  Yükler / Analiz (kapalı, özet) / Tasarım (kapalı, D/C rozeti) → alt çubuk 48 (Uygula birincil, Al, Anında uygula).
- **Pencere şeridi** 32: Özellikler · Kataloglar · Model ağacı (sola yapıştırılmış işareti) · Filtre & görünürlük · Sorgu.
- **Rıhtım**: Komut · Mesajlar (uyarı sayacı) · Tablolar; 2 satır geçmiş (komut adı `vurgu_metin` 600, sonuç `ok` + onay).
- **Komut satırı** 32 ve **durum çubuğu** 28: §2 tablosu; kat kapsamı anahtarı her yoğunlukta görünür.

## 9. Küçük ekran kuralları (`kucuk.png`, 1366×768)

1. 1600×900 altında **Sıkı** yoğunluk otomatik (Ayarlar › Görüntü › Yoğunluk ile zorlanabilir); modül ölçüleri §5.
2. Şerit: Kolon, Çapraz, Döşeme, Duvar, Temel gruplarında küçük düğme sütunları gizlenir (yalnız büyük düğme); 1280
   altında gruplar ▾ açılır düğmeye çöker; en dar ekranda şerit yatay kaydırılır.
3. Sol ray: ilk 7 araç + "⋯ Diğer araçlar"; seçim anahtarları 24 px adım (22 px kutu); "anahtarları gizle" taşma menüsüne geçer.
4. Model ağacı 232: segment yazısı 10 px, girinti 12, "6 seçili" rozeti "6" olur; sığmayan adlar … ile kısalır.
5. Özellikler 288 kaydırılır; alt çubuk (Uygula) her zaman görünür. Pencere şeridinde sığmayan düğmeler yalnız simge.
6. Görünüm pilinden "Renk: türe göre" düşer (Görünüm sekmesinde kalır); gezinme çipi kısalır.
7. Rıhtım 40 (2 × 18 px satır); komut satırında yalnız ilk iki ipucu; durum çubuğunda "Kat kapsamı" yazısı, "Orta tuş",
   "Etkin kat" ve başlıktaki kullanıcı adı gizlenir; **kat kapsamı anahtarı her zaman kalır**.
8. 1280 altında Model ağacı otomatik olarak pencere şeridine döner (tek panel), görünüm ≥ %60 kalır.
9. Ayarlar: pencere ekranın %94'ü; 1200 px altında kartlar tek sütun; 1000 px altında gezinti yalnız simge.
10. En küçük istemci alanı **1024 × 640** mantıksal px (Sıkı yoğunluk, tek panel, görünüm ≥ %60, durum çubuğu öğeleri
    çakışmaz); pencere bunu arayüz ölçeğiyle (DPI × yazı boyutu) çarpıp `WM_GETMINMAXINFO` ile uygular. Ekran dışı
    sınamada daha küçük `--boyut` olduğu gibi çizilir (günlüğe uyarı).

## 10. Dear ImGui + özel bileşenlere eşleme

| Konu | Uygulama |
|---|---|
| Belirteçler | `belirtec.py` tek kaynak → derlemede `op4/veri/tema.json` (renk, yarıçap, aralık, yazı ölçeği, modül ölçüleri, üç palet) üretilir; C++ `Tema` yapısı açılışta okur. Vurgu değişimi çalışırken `Tema::paletUygula()` ile `ImGuiStyle::Colors` yeniden kurulur; yeniden başlatma yok |
| `ImGuiStyle` | `FrameRounding` 6 · `ChildRounding` 6 · `PopupRounding` 8 · `WindowRounding` 10 (kipli) · `TabRounding` 6 · `GrabRounding` 8 · `ScrollbarRounding` 2 · `FrameBorderSize` 1 · `PopupBorderSize` 1 · `FramePadding` (8, 4) · `ItemSpacing` (8, 8) · `ItemInnerSpacing` (6, 4) · `WindowPadding` (12, 12) · `ScrollbarSize` 8 · `AntiAliasedFill/Lines` açık; hepsi × DPI |
| Renk eşleme | `WindowBg/ChildBg` = `yuzey` · `PopupBg` = `yuzey` · `FrameBg` = `alan` · `FrameBgHovered` = `hover` · `FrameBgActive` = `yuzey` · `Border` = `cizgi` · `Text` = `metin` · `TextDisabled` = `metin4` · `Button` = `yuzey` · `ButtonHovered` = `hover` · `ButtonActive` = `basili` · `Header` = `secim_ton` · `HeaderHovered` = `hover` · `CheckMark` = beyaz (kutu `vurgu` özel çizim) · `SliderGrab` = `vurgu` · `Tab*` özel · `NavHighlight` = `odak` · `ModalWindowDimBg` = `karartma` %38 · `TableBorderLight` = `cizgi2` · `TableRowBgAlt` = saydam (zebra yok) |
| Gölge | ImGui'de gölge çağrısı yok: 64×64 önceden bulanıklaştırılmış yuvarlak dikdörtgen dokusu, 9 dilimli `AddImage` ile; türler `GOLGE` tablosundan (iki katman). Panel → görünüm geçişi 8 px gradyan `AddRectFilledMultiColor` |
| Odak halkası | Her özel bileşen sonunda `IsItemFocused() && io.NavVisible` ise `AddRect(min − 3, max + 3, odak %28, yarıçap + 3, 0, 3)`; dolgulu alan odakta beyaz + `odak` kenar |
| Segmentli denetim | `Segmentli(id, ögeler, &secili, Stil::Notr/Vurgu)`: `InvisibleButton` parçalar, `AddRectFilled` iz + hap, metin `ImGui::RenderText`; ←/→ ile gezinme |
| Anahtar | `Anahtar(id, bool*)`: hap + daire, `ImGui::GetTime()` ile 120 ms kayma (Hareketi azalt = 0) |
| Şerit | Özel bileşen; `komutlar.json` (sekme → grup → büyük/küçük düğme → komut kimliği, başlatıcı); etkin sekme alt çizgisi `AddRectFilled` 3 px yuvarlak; küçük ekran kuralları genişlik ölçümüyle |
| Sol ray · pencere şeridi | `InvisibleButton` + `AddImage`/yol simgeleri; dikey metin döndürülmüş dörtgenlerle (`ImRotate` tekniği) |
| Model ağacı | `TreeNodeEx` + `SpanFullWidth` + `FramePadding` 24 px satır; satır zemini `ChannelsSplit` ile metnin altına (içe 6 px, 6 px yuvarlak); girinti kılavuzları `AddLine`; rozet ve göz özel; arama `InputTextWithHint` + simge |
| Özellikler | `BeginTable` 2 sütun (etiket 104 sabit), satır 24; alanlar `InputText` / `Combo` (FrameBg = `alan`); bölüm başlığı özel (sevron, özet, rozet); "(farklı)" `TextDisabled` |
| Görünüm | DirectX 12 hedefi `Image`; pil ve düğme grubu `NoDecoration` yüzen pencereler; seçim konturu: kimlik tamponu → kenar algılama 2 px + hale = 5 px maske, iki geçişli 3,2 px Gauss, %42; üzerinde 1 px; arka plan tam ekran geçişi (gradyan + ortam ışığı elipsi) |
| Rıhtım · komut · durum | `BeginTabBar` (özel alt çizgi); komut `InputText` + `CallbackCompletion/History`; durum çubuğu özel çipler; kat kapsamı vurgu segmenti `Alt+1/2/3` |
| Ayarlar | `BeginPopupModal("Ayarlar")`, boyut min(1440, %94) × min(960, %94); sol `BeginChild` 256 (`Selectable` kategoriler, alt bölümler `SetScrollHereY` ile kaydırma izleme); sağ `BeginChild` + `BeginTable(2, SizingStretchSame)` içinde kartlar (`BeginChild` `Borders` + `AutoResizeY`, `ChildRounding` 6); alt çubuk sabit. Ayarlar kayıt defteri (kimlik, etiket, açıklama, anahtar sözcük, sayfa, bölüm, varsayılan, tür) aramayı, değişti işaretini ve Varsayılana dön'ü besler. Kopyalanan ayar yapısıyla fark sayılır; Uygula → `ayarlar.json`; Esc = İptal, Enter = Tamam |
| Tuş yakalama | Odaklı yakalama alanında `ImGuiKey` döngüsü + `io.KeyMods`; ilk tuş bırakıldığında birleşim yazılır; çakışma kayıt defterinden anında |
| Yazı tipi | `imgui_freetype` (FreeType 2.13.3, LightHinting \| ForceAutoHint) + Noto Sans SemiCondensed statik 400/500/600/700 (gömülü alt küme; semboller Inter'den MergeMode); boyutlar 9–20 × DPI × yazı boyutu (ImGui 1.92 dinamik yazı tipleri, tam piksel). `tnum`: Noto Sans'ın rakamları varsayılan olarak eşit genişliklidir |
| Simgeler | 24 birimlik yol listeleri (`tuval.py::simge_ciz`, ≈ 140 simge) → `AddPolyline/AddCircle/AddRect` 1,5 px × DPI; önbellekli doku isteğe bağlı |

## 11. 25 ilkenin yeri

Atölye `tasarim.md` §11'deki eşleme aynen geçerlidir (aynı iskelet ve aynı içerik). Değişenler: **5** etkin pencere
düğmesi altın yerine vurgu tonu; **16** başlangıç/bitiş tutamacı altın/kahve yerine **dolu/boş kare** (aynı ilke,
renk körlüğüne dayanıklı); **22** seçim vurgusu "altın kontur + açık dolgu" yerine **vurgu konturu + hale + açık
dolgu**, üzerinde ince açık vurgu. ARAYUZ_ILKELERI.md'deki "kahverengi–altın vurgu" kullanıcı kararı bu kararla
güncellenmelidir (vurgu: Kobalt / Petrol / Grafit, varsayılan Kobalt).
