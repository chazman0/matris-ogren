# op4 arayüz yönü B — "Atölye" (yoğun profesyonel)

Taslak görselleri bu klasördeki `uret.py` üretir (`python3 uret.py`; yardımcılar `tuval.py` = çizim/simge kütüphanesi, `sahne.py` = 3B görünüm). Her şey Pillow ile çizilmiştir: arayüz kromu, elle çizilmiş tek renkli çizgi simgeler ve numpy z‑tamponlu yazılımsal 3B görünüm (ekstrüde I/L profiller, tek ışık yönü, ince koyu kenarlar).

| Dosya | İçerik |
|---|---|
| `ana.png` 1920×1080, `ana-2x.png` 3840×2160 | Ana ekran: Model sekmesi, 6 kiriş seçili, bağlamsal mini araç çubuğu, Özellikler açık |
| `kucuk.png` 1366×768 | Küçük ekran davranışı (daraltılmış şerit, dar paneller) |
| `detay-serit.png` (2×) | Şerit kırpımı |
| `detay-panel.png` (2×) | Model ağacı + Özellikler kırpımı |
| `secsuz.png` | Seç ve Süz penceresi (görünüm üstünde, önizleme altın konturla) |
| `sonuc.png` | Tasarım sekmesi, D/C renk haritası + 5 eşikli lejant, sonuç gösterim kartı, Tablolar rıhtımı |
| `kat-kapsami.png` (2×) | Durum çubuğu: kat kapsamı anahtarı ve "3 katta uygulanacak" önizlemesi |

## 1. Kavram

**Atölye** bir mühendislik iş istasyonudur: nötr açık gri yüzeyler, sıkı yoğunluk, en büyük alan 3B görünüme. İki ticari referansın *fikirleri* (M programının şerit + yan panel + seçim anahtarları + doğrudan değiştirme; A programının kat kavramı, kat kapsamı anahtarı, Model Explorer, D/C lejantı, tablolar) tek bir iskelete yerleştirilir; marka, ikon sanatı ya da renk kopyalanmaz.

İskelet (1920×1080, 1×):

```
┌ Başlık 30 ───────────────────────────────────────────────────────────────┐
├ Şerit: sekme satırı 26 + gövde 78 = 104 ─────────────────────────────────┤
├ Ray 36 ┬ Model ağacı 268 ┬ Görünüm sekmeleri 22 / 3B görünüm 1268×806 ┬ Özellikler 320 ┬ Pencere şeridi 28 ┤
├ Rıhtım: sekme 22 + içerik 40 (Komut / Mesajlar / Tablolar) ──────────────┤
├ Komut satırı 30 ─────────────────────────────────────────────────────────┤
└ Durum çubuğu 26 ─────────────────────────────────────────────────────────┘
```

Her şey **bir tık uzaklıkta**: sol ray (çizim paleti + seçim anahtarları), sağ pencere şeridi (Özellikler / Kataloglar / Model ağacı / Filtre & görünürlük / Sorgu), altta sekmeli rıhtım. Görünüm iskeletin %55'ini kaplar; paneller kapatılınca %80'e çıkar.

## 2. İlkeler

1. **Görünüm esastır.** Krom, görünümün içine değil kenarına yerleşir; görünüm içindeki her şey (araç pili, düğmeler, mini araç çubuğu, lejant) yarı saydam beyaz kart üstünde yüzer ve modelin önüne geçmez.
2. **Yoğun ama hizalı.** 20 px satır, 12 px gövde yazısı, 11 px etiket; iki sütunlu özellik ızgarasında etiket sütunu sabit (108 px), değer sütunu giriş kutusu.
3. **Bir vurgu, bir seçim.** Kahve (`#8A6B3C`) yalnızca *etkin/birincil* için (sekme çizgisi, birincil düğme, basılı araç, komut etiketi, bağlantı); Altın (`#B08950`) yalnızca *seçim* için (model konturu, ağaç satırı, pencere şeridi işareti, başlangıç tutamacı). İkisi aynı anlamda asla kullanılmaz.
4. **Renk anlam taşır.** Model nesneleri tür bazlı nötr griler; D/C ölçeği 5 eşik; Kahve/Altın modelde yalnızca seçim–hover–tutamaç anlamında.
5. **Komut akışı aynı yerde yazılır.** Durum çubuğu solunda adım yönergesi, altta komut satırı (Ctrl+Q ile hızlı başlat aynı kutu), rıhtımda geçmiş + sonuç.
6. **Kat bir sınıf vatandaştır.** Ağaçta katlar → nesneler, durum çubuğunda etkin kat + kat kapsamı anahtarı, görünüm sekmelerinde "Plan – Kat 2 (+9,00)".
7. **Bağlam kalıcıdır.** Özellikler paneli seçime göre bölümlerini değiştirir; mini araç çubuğu seçimin yanında en sık dört alanı verir.

## 3. Renk belirteçleri

Marka: Kahve `#8A6B3C`, Krem `#EDE6D8`, Altın `#B08950`, Antrasit `#14181B`, Gri `#8C8C8C` (`/op4/kimlik/README.md`).

| Belirteç | Hex | Kullanım |
|---|---|---|
| `zemin` | `#F3F4F6` | Uygulama zemini: başlık, sekme satırı, raylar, rıhtım sekmeleri, durum çubuğu |
| `yuzey` | `#FFFFFF` | Paneller, şerit gövdesi, giriş kutuları, kartlar |
| `yuzey2` | `#F8F9FA` | Panel ve bölüm başlıkları, tablo başlığı, pasif satır vurgusu |
| `yuzey3` | `#EEF0F2` | Basılı/etkin nötr düğme zemini |
| `cizgi` | `#D7DAE0` | Güçlü ayraç, panel kenarı, giriş kenarı (`#C9CDD3` giriş kutuları) |
| `cizgi2` | `#E6E8EC` | Satır çizgisi, ince ayraç |
| `metin` | `#14181B` | Birincil metin (Antrasit) |
| `metin2` | `#4E545C` | İkincil metin, pasif sekme |
| `metin3` | `#8C8C8C` | Yer tutucu, ipucu, grup etiketi (Gri) |
| `vurgu` | `#8A6B3C` | Kahve: etkin sekme üst çizgisi, birincil düğme, Dosya düğmesi, basılı araç simgesi, bağlantı, hover konturu |
| `vurgu_ton` / `vurgu_ton2` | `#F2ECE2` / `#E1D5C2` | Basılı araç zemini / kenarı |
| `secim` | `#B08950` | Altın: seçim konturu, seçili ağaç satırı şeridi, etkin pencere düğmesi şeridi, başlangıç tutamacı |
| `secim_ton` / `secim_ton2` | `#F6EFE1` / `#EBDFC6` | Seçili satır zemini, seçim kartı, Seç ve Süz sonuç kutusu |
| `ok` / `uyari` / `hata` | `#2E7D4F` / `#C7861B` / `#B4443A` | Durum renkleri (rıhtım sonucu, rozet, yetersiz eleman) |
| `vp_ust` → `vp_alt` | `#FCFCFD` → `#E6E8EB` | Model arka planı dikey gradyanı (beyaz → açık gri) |

Model nesne renkleri (gölgeleme öncesi taban): kolon `#CFD3D9`, kiriş `#D5D8DD`, tali/aşık `#DADDE2`, çapraz `#C6CAD1`, döşeme `#E6E3DC`, temel `#D9D6CF`; kenarlar `#454B53` (%50 saydam, 0,5 px @1×). Işık yönü (−0,45, −0,50, +0,74); yüzey katsayısı 0,50 + 0,40·lambert + 0,12·gök; yumuşak yer gölgesi + kolon dibi teması.

D/C ölçeği (5 eşik, kullanıcı düzenler): ≤0,50 `#4C7FC2` · 0,50–0,70 `#3F9A62` · 0,70–0,90 `#D6B534` · 0,90–1,00 `#E08A2E` · >1,00 `#C83C32`. Açık/koyu çifti: koyu temada aynı tonların %15 koyultulmuşu (sonraya).

Seçim ve hover (modelde):

| Durum | Görünüm |
|---|---|
| Seçili | Altın kontur 2 px (dış siluet, örtmeden bağımsız) + açık altın dolgu `#F1E6CE` (gölgeleme 0,84–1,0) + iç kenarlar altın %55 |
| Hover | İnce kahve kontur 1 px (`#8A6B3C`), dolgu değişmez; imleç ipucu beyaz kart, kahve kenar |
| Tutamaç | Başlangıç: altın kare 8 px, beyaz 2 px çerçeve, koyu 1 px hat; bitiş: kahve kare; orta nokta: altın noktalı daire; ölçü etiketi altın kenarlı kutu (değer yazılabilir) |
| Süzgeç önizlemesi | Seçimle aynı altın kontur (secsuz.png: Kat 2'deki 31 IPE400) |
| Yalnız seçiliyi göster | Diğerleri %85 saydam (Ctrl+5) |

## 4. Yazı ölçeği

Inter (değişken; `opsz` = mantıksal boyut, 14–32 aralığına kırpılır; ağırlıklar `set_variation_by_axes`). Türkçe glifler (İ ı ş ğ ü ö ç) tüm boyutlarda kontrol edildi.

| Boyut | Ağırlık | Yer |
|---|---|---|
| 13 | 600 | Başlık çubuğu "op4", iletişim kutusu başlığı |
| 12 | 600 / 500 / 400 | Panel başlıkları, sekme adları (etkin 600), ağaç satırı, özellik değeri, komut satırı, düğmeler |
| 11 | 600 / 500 / 400 | Şerit düğme etiketleri, bölüm başlıkları (600), görünüm pili, mini araç çubuğu, durum çubuğu, rıhtım satırları, pencere şeridi (dikey) |
| 10 | 600 / 400 | Şerit grup etiketleri, kısayol rozetleri, durum anahtarları (ORTO/YAKALA), ipucu metni, lejant |
| 9 | 600 / 500 | Rozetler ("6 seçili", "2"), lejant eşik kutuları |
| 8 | 600 | Yalnız ray bölüm etiketleri (ÇİZ / SEÇ) |

Sayılar her yerde `tnum` (tablo rakamları) ile; ondalık ayırıcı virgül, binlik ayırıcı ince boşluk ("1 842", "5 670").

## 5. 8 px aralık ızgarası

Ana ızgara 8 px, yarım adım 4 px (iç dolgular). Modül yükseklikleri: 20 (ağaç/özellik satırı), 22 (görünüm ve rıhtım sekmeleri), 24 (panel sekmeleri, arama, düğme), 26 (şerit sekme satırı, durum çubuğu, ray anahtarı), 28 (panel başlığı, mini araç çubuğu, ray paleti), 30 (başlık, komut satırı), 36 (iletişim başlığı), 40 (nesne başlığı, panel alt çubuğu, rıhtım içeriği), 56 (büyük şerit düğmesi), 78 (şerit gövdesi). Yatay: ray 36, pencere şeridi 28, paneller 268/320 (8'in katı + 4 kenar), panel iç dolgu 12, giriş kutusu iç dolgu 7, grup aralığı 6+6. Simge kutuları 24 (büyük), 16/14 (küçük/satır), 12 (sevron/onay).

## 6. Panel yerleşim kuralları

- **Sağ pencere şeridi** = tek iskelet, çok pencere (Özellikler, Kataloglar, Model ağacı, Filtre & görünürlük, Sorgu). Varsayılan tek açık pencere; etkin düğme altın şerit + açık altın zemin. Ctrl+tık ile yığma; sürükleyip sola/alta yapıştırma (Model ağacı bu taslakta sola yapıştırılmış, düğmesinde "sol" işareti). Pencere yüzdürülebilir.
- **Sol ray** iki bölüm: ÇİZ (hızlı çizim paleti, etkin araç kahve şerit + açık zemin) ve SEÇ (seçim anahtarları: açık olanlar beyaz kutu + kahve nokta, kapalı olanlar soluk). Altta doğrudan değiştirme (D) anahtarı (altın) ve anahtarları gizle (göz).
- **Model ağacı** 268 px: başlık + sekmeler (Model / Göster / Tablolar / Raporlar) + arama + ağaç; derinlik 14 px/düzey; sağda sayı/kot sütunu; etkin kat satırı gri zemin + göz; seçili satır altın şerit + "6 seçili" rozeti. Altta özet satırı.
- **Özellikler** 320 px: başlık (ara/pin/kapat) → nesne başlığı (simge, "Kiriş · 6 seçili", alt satır kesit·malzeme·kat·aks) → bölümler (Genel / Kesit / Konum / Serbestlikler / Yükler / Analiz / Tasarım; katlanabilir) → alt çubuk (Uygula birincil, Al, Anında uygula anahtarı). Çoklu seçimde farklı değerler "(farklı)" gri; kesit/malzeme yanında "…" katalog düğmesi; uç serbestlikleri yanında altın/kahve kare tutamaç renk kodu.
- **Görünüm** alanı: üstte görünüm sekmeleri (3B görünüm · Plan – Kat 2 (+9,00) · Yükselti – Aks 1 · +); sol üst araç pili (3B ▾ · Perspektif ▾ · Tüm katlar ▾ · Renk: türe göre ▾ · çubuk↔ekstrüde anahtarı); sağ üst dört düğme (tam görünüm, seçiliye yakınlaş, kesit düzlemi, gösterim seçenekleri — küp yok); sol alt eksen üçlüsü; sağ alt kamera bilgisi. Aks baloncukları ve kat seviye çizgileri ekran uzayında.
- **Rıhtım** sekmeli (Komut / Mesajlar [rozet] / Tablolar); varsayılan 2 satır, Tablolar açılınca 128 px; sağda pin/daralt.
- **Komut satırı** ayrı 30 px satır, kahve sol şerit: "Komut: |  · Son: …"; sağda kısayol rozetleri (Ctrl+Q odakla/hızlı başlat, Tab tamamla, Enter yinele, Esc iptal).
- **Durum çubuğu**: sol adım yönergesi (› ile); orta ORTO / YAKALA / SÜRÜKLE anahtarları + X Y Z kilitleri + orta tuş modu; sağ kat kapsamı anahtarı (Bu kat / Benzer katlar / Tüm katlar) + Etkin kat ▾ + birim ▾ + imleç koordinatı + seçili sayısı (tutamaç sayısıyla).
- **İletişim kutuları** modsuz, görünümün üstünde sağa hizalı yüzer; Uygula ile açık kalır; altta sol: ikincil eylemler, sağ: birincil (kahve) + Kapat.

## 7. Şerit yapısı

Sekme satırı 26 px: **Dosya** (kahve dolgulu arka plan menüsü) + Model · Düzenle · Yükler · Analiz · Tasarım · Görünüm · Raporlar (etkin sekme beyaz, kahve 2 px üst çizgi, gövdeyle birleşik). Sağda "Şeridi özelleştir", daralt, yardım.

Gövde 78 px: gruplar; büyük düğme = 24 px simge + 11 px etiket (min 48 px genişlik), küçük düğmeler 3'lü sütun (14 px simge + etiket, 18 px adım), grup etiketi 10 px gri altta, iletişim başlatıcı "›", gruplar arası 1 px ayraç. Basılı araç: `vurgu_ton` zemin + `vurgu_ton2` kenar + kahve simge/600 etiket.

Model sekmesi (taslak): **Aks & Kat** (Aks, Kat | Aks sistemi…, Kat verisi…, Çalışma düzlemi ▾) · **Kolon** (Kolon | Çelik, Betonarme, Kompozit) · **Kiriş** (Kiriş [basılı] | Ana kiriş, Tali kiriş, Aşık) · **Çapraz** (Çapraz | X, V/Λ, Tek diyagonal) · **Döşeme** (Döşeme | Betonarme, Kompozit, Boşluk) · **Duvar** (Duvar | Perde, Dolgu, Açıklık) · **Temel** (Temel | Tekil, Sürekli, Radye) · **Hızlı kolon / kiriş** (Hızlı kolon, Hızlı kiriş | Hızlı çapraz, Tali kirişler…, Kat kopyala…) · **Seç** (Seç, Seç & Süz | Benzerini seç, Kata göre ▾, Tersine çevir).

Tasarım sekmesi (sonuc.png): **Yönetmelik** (ÇYTHYE 2018 ▾ | Tercihler…, Kombinasyonlar, Malzeme katsayıları) · **Çelik** (Tasarla, Kontrol et | Otomatik kesit ▾, Yanal tutma, Birleşimler) · **Betonarme** (Tasarla | Donatı, Kesme, Detay) · **Göster** (D/C haritası [basılı], Deformasyon, Diyagram | Değerler, N · V · M ▾, 1,2G + 1,6Q ▾) · **Sonuç** (Tablolar, Rapor | Etkileşimli tasarım, elektronik tablo'e aktar, Tablo kümeleri).

Diğer sekmeler (kurgu): Düzenle (Kopyala/Taşı/Döndür/Ayna/Çoğalt, Böl/Birleştir/Uzat/Kırp, Kat kopyala, Toplu düzenle), Yükler (Desenler, Durumlar, Kombinasyonlar, Geçerli desen ▾, Düğüm/Çubuk/Alan yükü ata, Mesnet, Göster/Temizle), Analiz (Model kontrolü, Çöz F5, Seçenekler, Kütle kaynağı), Görünüm (Yeni görünüm ▾, Plan/Yükselti, Kesit düzlemi, Render Ctrl+1…5, Tema, Bina görünüm sınırları), Raporlar (Tablo seç, Tablo kümeleri, Rapor, Dışa aktar).

## 8. Simge stili

Tek renkli çizgi simgeler, 24 birimlik ızgara, **1,5 px** kalem (küçüklerde 1,3–1,4), yuvarlak birleşim, dolgu yalnızca anlam gerektiğinde (ok ucu, baloncuk, seçim imleci). Renkler: `#2F343B` büyük, `#3C4148` küçük, `metin2` görünüm/pil, kahve etkin, `#B3B7BE` kapalı anahtar. Emoji yok; marka simgesi (kemer) yalnızca başlık çubuğunda, orijinal PNG'den ölçeklenir, yeniden çizilmez. Taslaktaki tüm simgeler `tuval.py::simge_ciz` içinde yol tanımıdır; C++'a aynı yol listesi taşınır.

## 9. Küçük ekran davranışı (1366×768, `kucuk.png`)

- Paneller daralır: Model ağacı 232, Özellikler 288; ray ve pencere şeridi sabit.
- Şeritte ikinci öncelikli küçük düğme sütunları gizlenir (Kolon, Çapraz, Döşeme, Duvar, Temel grupları yalnız büyük düğme); daha dar ekranda gruplar "▾" açılır düğmeye çöker, en dar ekranda şerit yana kaydırılır.
- Rıhtım 36 px (2 satır), komut satırı ipuçları yalnız ilk ikisi; durum çubuğunda "Orta tuş" ve "Etkin kat" gizlenir, yönerge kısalır; kat kapsamı anahtarı her zaman kalır.
- Ağaçta "6 seçili" rozeti "6" olur; sığmayan satırlar kaydırılır.
- Özellikler kaydırılır; alt çubuk (Uygula) her zaman görünür.
- 1280 altında: Model ağacı otomatik pencere şeridine döner (tek panel), görünüm %60'ı korur.

## 10. Dear ImGui + özel bileşenlere eşleme

| Bölge | Uygulama |
|---|---|
| Pencere iskeleti | Tek ana `DockSpace`, sabit yerleşim (kullanıcı yalnız yan pencereleri taşır); bölge yükseklikleri sabit sayılardan (30/26/78/22/40/30/26) DPI ölçeğiyle çarpılır |
| Başlık çubuğu | Kenarlıksız Win32 pencere (DWM), ImGui `BeginMainMenuBar` yerine özel çocuk; marka PNG'si doku olarak |
| Şerit | Özel bileşen: sekme satırı `ImDrawList` ile; gövde `BeginChild` + grup/düğme ızgarası (JSON tanımı: sekme → grup → büyük/küçük düğme → komut kimliği); göz simgesiyle gizleme, sürükle‑sırala, kullanıcı sekmesi |
| Sol ray | `ImageButton` benzeri özel düğme; anahtarlar `ToggleIcon` (Ctrl+tık tekil, Shift+tekerlek kapsam seviyesi) |
| Model ağacı | `TreeNodeEx` + `SpanAvailWidth` + özel satır çizimi (sağ sütun, rozet, göz); arama `InputTextWithHint`; sağ tık bağlam menüsü |
| Özellikler | `BeginTable` 2 sütun (etiket 108 px sabit); bölüm `CollapsingHeader` stilinde özel başlık; değer hücresi türe göre `InputText` / `Combo` / salt metin / onay; "…" düğmesi katalog penceresini açar; çoklu seçimde "(farklı)" ve yazılan değer tümüne |
| Pencere şeridi | Özel dikey sekme çubuğu: simge + döndürülmüş metin (metin `ImFont` glifleriyle `AddText` yerine döndürülmüş dörtlülerle, `ImRotate` tekniği) |
| 3B görünüm | DirectX 12 render hedefi `ImTextureID` olarak `Image`; üstündeki pil/düğmeler/mini araç çubuğu/lejant `Begin` + `NoDecoration|NoDocking|AlwaysAutoResize` yüzen pencereler; tutamaçlar, ölçü etiketleri ve imleç ipucu `GetForegroundDrawList` ile ekran uzayında |
| Rıhtım | Sekmeli `BeginTabBar`; Komut: geçmiş listesi; Tablolar: `BeginTable` (sıralama, süzgeç, elektronik tablo'e aktar) |
| Komut satırı | `InputText` + `CallbackCompletion|CallbackHistory`; Ctrl+Q odaklar; sonuç listesi Son/Şerit/Menü/Tümü sekmeli açılır pencere; Türkçe + İngilizce takma adlar aynı tabloda |
| Durum çubuğu | Özel; kat kapsamı üç durumlu segmentli anahtar (`Alt+1/2/3`), önizleme balonu `BeginTooltip` yerine kalıcı küçük pencere |
| İletişim kutuları | Modsuz `Begin` pencereleri (NoDocking), "Uygula ile açık kalır"; Seç ve Süz kural satırları `BeginTable` |
| Yazı tipi | `imgui_freetype` ile Inter değişken: 400/500/600 ağırlıkları ayrı `ImFont` örnekleri, boyutlar 9–13 px × DPI; atlas DPI değişince yeniden kurulur; `tnum` için FreeType özelliği ya da sabit genişlikli rakam alt kümesi |
| Simgeler | 24 birimlik yol listesi → `ImDrawList::AddPolyline/AddRect/AddCircle` 1,5 px × DPI; önbellekli doku isteğe bağlı |
| Tema | `ImGuiStyle` renkleri yukarıdaki belirteçlerden; `FrameRounding` 3, `WindowRounding` 4, `ScrollbarSize` 6, `ItemSpacing` (8,4), `FramePadding` (7,3) |

## 11. Dosyadaki 25 çıkarımın taslaktaki yeri

| # | Çıkarım | Taslakta |
|---|---|---|
| 1 | Ribbon sekme iskeleti | Sekme satırı: Dosya + Model/Düzenle/Yükler/Analiz/Tasarım/Görünüm/Raporlar (`ana.png`, `detay-serit.png`); Model ve Tasarım gövdeleri çizildi |
| 2 | Göz simgesiyle sekme gizleme, sıralama, kullanıcı sekmesi | Sekme satırı sağında "Şeridi özelleştir"; JSON şerit tanımı (§10) |
| 3 | Hızlı Başlat Ctrl+Q + komut satırı | Komut satırı altta ("Komut: … · Son: KİRİŞ — 6 kiriş eklendi (Kat 2)"), sağında Ctrl+Q rozeti "odakla / hızlı başlat" |
| 4 | Durum çubuğu içeriği | Sol yönerge; orta ORTO/YAKALA/SÜRÜKLE + X Y Z + orta tuş; sağ kat kapsamı + birim + koordinat + "Seçili: 6 (12 tutamaç)"; komut satırı hemen üstünde |
| 5 | Yan panel = tek iskelet, çok pencere | Sağ pencere şeridi: Özellikler (altın etkin), Kataloglar, Model ağacı (sola yapıştırılmış işareti), Filtre & görünürlük, Sorgu |
| 6 | Kalıcı bağlamsal Özellikler + kütüphane ayrımı | Özellikler paneli bölümleri Genel/Kesit/Konum/Serbestlikler/Yükler/Analiz/Tasarım; "(farklı)" çoklu değer; "…" katalog düğmeleri; Uygula / Anında uygula; Kataloglar penceresi şeritte |
| 7 | Bağlamsal mini araç çubuğu | Seçimin üstünde: IPE400 ▾ · S355 ▾ · Kat 2 ▾ · Mafsal ▾ + kopyala/taşı/sil |
| 8 | Seçim anahtarları çubuğu | Sol rayın SEÇ bölümü (tümü, düğüm, kolon, kiriş, döşeme, duvar, aks, yük, mesnet, temel) + göz; kapsam seviyesi Shift+tekerlek (§10) |
| 9 | Seçim filtresi diyalogu | `secsuz.png`: Kategori/Özellik/Koşul/Değer satırları, Ve/Veya, parantez, kayıtlı `.filtre` listesi, aynı motor görünüm süzgeci ve renk kuralı |
| 10 | Seç menüsü ölçütleri + Benzerini seç + gruplar | Şerit Seç grubu (Benzerini seç, Kata göre ▾, Tersine çevir); diyalogda "Benzerini seç", Ctrl+K/J ipuçları; ağaçta Gruplar (3) |
| 11 | Kat kapsamı anahtarı | Durum çubuğunda Bu kat / Benzer katlar / Tüm katlar (Benzer katlar etkin), Alt+1/2/3; `kat-kapsami.png`: "3 katta uygulanacak — Kat 1, Kat 2 (ana kat), Kat 3 · Zemin hariç"; "Etkin kat: Kat 2 ▾" |
| 12 | Kat Verisi tablosu | Şerit Aks & Kat → "Kat verisi…"; ağaçta Katlar düğümü (kot, göz, etkin kat); görünüm sekmesi "Plan – Kat 2 (+9,00)" |
| 13 | Aks sistemi diyalogu | Şerit "Aks sistemi…"; ağaçta Aks sistemi "A–D × 1–5"; modelde aks baloncukları + uzantılar |
| 14 | Kat/aks görünümleri | Görünüm sekmeleri: 3B görünüm · Plan – Kat 2 (+9,00) · Yükselti – Aks 1 · +; "Görünüm özellikleri: arka plana çift tık" |
| 15 | Yerleştirme ve yakalama | Şerit Hızlı kolon / Hızlı kiriş / Hızlı çapraz; durum çubuğu ORTO/YAKALA; nesne özellikleri Özellikler paneline gömülü (Düzlemde, Derinlik) |
| 16 | Doğrudan değiştirme tutamaçları | Seçili kirişte altın başlangıç / kahve bitiş tutamacı, orta nokta tutamacı, yazılabilir "5 670" ölçü etiketi; rayda D anahtarı (altın) |
| 17 | Kopyala/Taşı/Çoğalt diyalogu | Mini araç çubuğunda kopyala/taşı; şerit "Kat kopyala…"; Düzenle sekmesi kurgusu (§7) |
| 18 | Yük modeli | Özellikler → Yükler bölümü: "Geçerli desen: G · Sabit ▾", çizgisel yük G/Q, öz ağırlık; ağaçta Yük desenleri (5) / Yük durumları (5) / Kombinasyonlar (14) |
| 19 | Mesnet/serbestlik formu | Özellikler → Serbestlikler: Başlangıç ucu (altın kare) / Bitiş ucu (kahve kare) / Mesnet "Bağlı"; rayda Mesnet aracı |
| 20 | Sonuç gösterimi | `sonuc.png`: D/C renk haritası, görünüm altında 5 eşikli lejant (düzenlenebilir eşik kutuları, "1 eleman > 1,00" rozeti), "Sonuç gösterimi" kartı (kombinasyon, D/C–Deformasyon–M3, ölçek, gölge, kübik eğri, animasyon + hız), Tablolar rıhtımı (D/C rozetli satırlar, elektronik tablo'e aktar), Özellikler → Tasarım/Sonuç bölümleri |
| 21 | Model ağacı | Sol panel: Model/Göster/Tablolar/Raporlar sekmeleri; Katlar → Kat 2 → Kolonlar (20), Kirişler · IPE400 (31) → Ana çerçeve [6 seçili]…, Tali kirişler, Çaprazlar, Döşemeler; Kesitler, Malzemeler, Yükler, Gruplar, Analiz modeli |
| 22 | Görsel dil (açık tema) | Nötr açık gri krom, beyaz→açık gri model zemini, tür bazlı nötr nesne renkleri, altın seçim konturu + açık dolgu, ince kahve hover; "Yalnız seçiliyi göster" ve görünüm süzgeci %85 saydam (`secsuz.png` seçeneği) |
| 23 | Render modları | Görünüm pilinde çubuk ↔ ekstrüde anahtarı (ekstrüde etkin); Ctrl+1…5 Görünüm sekmesinde |
| 24 | Navigasyon | Sağ altta "Orta tuş: kaydır · Ctrl+orta: döndür", durum çubuğunda orta tuş modu, sol altta küçük eksen üçlüsü (küp yok), sağ üstte tam görünüm / seçiliye yakınlaş |
| 25 | Komut tutarlılığı | Komut satırı (Türkçe + İngilizce takma ad, Tab tamamlama, geçmiş), "Uygula ile açık kalır" iletişim kutuları, Özellikler'de Uygula/Al, listelerde Ekle/Kopyasını ekle/Değiştir/Sil deseni (Kataloglar) |

Not: Taslak modelde Kat 2'de 31 IPE400 kiriş vardır (A–D × 1–5 aks ızgarasında 15 çerçeve + 16 bağ kirişi); ağaçta bu nedenle "Kirişler · IPE400 (31)" yazılmıştır. Kat kapsamı anahtarı 3B görünümde de etkin gösterilmiştir çünkü op4'te kapsam, plan penceresine değil "Etkin kat" bağlamına bağlıdır (A programından sapma, bilinçli).
