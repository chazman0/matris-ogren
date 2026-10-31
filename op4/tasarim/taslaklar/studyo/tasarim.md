# op4 arayüz yönü C — "Stüdyo" (modern minimal)

Üretim: `python3 uret.py` (bu klasör; `tuval.py` çizim altyapısı, `sahne.py` 3B sahne). Çıktılar: `ana.png` 1920×1080, `ana-2x.png` 3840×2160, `kucuk.png` 1366×768, `detay-serit.png`, `detay-panel.png`, `secsuz.png`, `sonuc.png`, `kat-kapsami.png`. Yazı tipleri `kimlik/fontlar/` (Inter değişken, Cormorant Garamond); logolar `kimlik/` dosyalarından oranı korunarak yerleştirildi, yeniden çizilmedi.

## 1. Kavram

Stüdyo, op4'ü **beyaz kâğıt üstünde çalışan bir stüdyo masası** gibi kurar: açık, sıcak bir zemin (`#F3F1ED`) üzerinde yumuşak gölgeli, 8 px yuvarlatılmış **kartlar** yüzer — solda model ağacı, ortada 3B görünüm, sağda denetçi. Araçlar görünümün üstünde **yüzen ray ve çipler** olarak durur; komut satırı görünümün altında **yüzen bir çubuktur**, durum çubuğu ise pencerenin en altında düz ve sakin bir şerittir. Marka rengi yalnız **anlam taşıyan yerlerde** görünür: Altın = seçim ve etkin durum, Kahve = komut imleci, "Dosya" ve başlangıç/bitiş tutamacı; Kahve→Altın **gradyanı yalnız birincil eylemde** (Çöz, diyalogda Seç). Açılış ekranı "Kemer Çizgisi" ile aynı kâğıt tonu, aynı Inter/Cormorant ikilisi ve aynı altın çizgi dili kullanıldığından program açılıştan arayüze geçerken aynı ailede kalır.

## 2. İlkeler

1. **Beyaz yüzey, tek vurgu**: tüm kromda tek nötr aile; Altın yalnız "şu an etkin/seçili" demektir, kırmızı/turuncu yalnız sonuç ve hata.
2. **Nefes alan yoğunluk**: 8 px ızgara, 24–26 px satırlar, 16 px kart kenar boşluğu; ama her dosya maddesi (yönerge, kapsam, birim, koordinat, sayaç) yerinde.
3. **Komut mantığı M programı, kat mantığı A programı**: komut → özellikler yan panelde → noktalar; kat kapsamı anahtarı durum çubuğunda her işlemi kapsar.
4. **Her şey süzülebilir ve kaydedilebilir**: Seç & Süz motoru seçim, görünüm süzgeci ve renk kuralı için tek motor; `.filtre` dosyaları firma profiliyle paylaşılır.
5. **Yüzen ama sabit**: ray, çipler, mini araç çubuğu ve komut çubuğu görünüm kartının içinde sabit kenar boşluklarında durur; dar ekranda içerik kısalır, yer değiştirmez.

## 3. Renk belirteçleri

| Belirteç | Hex | Kullanım |
|---|---|---|
| `zemin` | `#F3F1ED` | Pencere zemini (kartların arkası) |
| `yuzey` | `#FFFFFF` | Kartlar, şerit, başlık çubuğu |
| `yuzey2` | `#F7F5F1` | Giriş alanları, çift satır zebra |
| `yuzey3` | `#EFECE6` | Parçalı anahtar yuvası, pasif anahtar dolgusu |
| `durum` | `#ECE9E3` | Durum çubuğu zemini |
| `cizgi` | `#E6E2DB` | Kılçık çizgiler, bölüm ayraçları |
| `cizgi2` | `#D3CEC4` | Alan/düğme kenarlıkları |
| `metin` (Antrasit) | `#14181B` | Birincil metin, etkin ikon |
| `metin2` | `#5A5E62` | İkincil metin, pasif ikon |
| `metin3` (Gri) | `#8C8C8C` | Açıklama, grup adı, kısayol |
| `kahve` | `#8A6B3C` | Dosya pili, komut imleci, bitiş tutamacı, hover konturu |
| `kahve_koyu` | `#6F5530` | Altın pil üstünde metin |
| `altin` | `#B08950` | Seçim konturu, etkin sekme alt çizgisi, başlangıç tutamacı, anahtar "açık" |
| `altin_dolgu` | `#F4EBDA` | Etkin düğme/pil dolgusu, seçili ağaç satırı |
| `altin_zemin` | `#F8F2E6` | Bilgi kutuları (kesit önerisi, eşleşen sayısı) |
| `krem` | `#EDE6D8` | Koyu pil üstü metin (Dosya, ipucu) |
| `hata` / `uyari` / `tamam` | `#C8372D` / `#D9A13B` / `#4C9A63` | Yetersiz / uyarı / uygun |
| `eksen_x/y/z` | `#B5553F` / `#4F8F5A` / `#3F6FAF` | Köşedeki eksen üçlüsü |

Model renkleri (görünüm): arka plan beyaz → `#E7E8EA` düşey gradyan (A programı arka plan değişince renk çifti değişir ilkesi; koyu tema için ayrı çift tasarlanır). Nesne türü varsayılanları: kolon `#8E99A6`, kiriş `#AAB3BD`, aşık/ikincil `#C2C8CF`, çapraz `#B39C7E`, döşeme `#DAD7D1` %24 saydam; kenarlar yüz renginin %50 koyusu, 0,5 px. **Seçim** = Altın kontur 1,4 px + `#E9D3A8` dolgu; **hover** = Kahve 1 px kontur + küçük etiket çipi. D/C 5 eşik: `#5B8FC9` ≤0,50 · `#55A86E` ≤0,70 · `#D9B13B` ≤0,90 · `#E07B2A` ≤1,00 · `#C8372D` >1,00 (açık ve koyu zeminde okunur).

## 4. Tipografi

Inter değişken (opsz = boyut, ağırlık eksenden): 

| Rol | Boyut / ağırlık |
|---|---|
| Diyalog başlığı | 17 / 600 |
| Panel başlığı (Kiriş, K2-05) | 15 / 600 |
| Sekme, başlık çubuğu "op4" | 13 / 600 (pasif 500) |
| Gövde, alan değeri, düğme | 12–12,5 / 450–600 |
| Ağaç satırı | 12 / 450 (ana kat ve kök 600) |
| Alan etiketi, durum çubuğu | 11–11,5 / 400–600 |
| Şerit düğme adı, grup adı | 11 / 500 · 10,5 / 500 |
| Rozet, çip, kısayol | 10–10,5 / 500–600 |

Proje adı başlık çubuğunda **Cormorant Garamond 19 / 600** (açılış ekranındaki alt başlıkla aynı aile). Türkçe glifler (İ ı ş ğ ü ö ç) üç yazı tipinde de var; maketlerde "Seç & Süz", "Çöz", "Kirişler", "Düğümler", "ÇYTHYE" ile denetlendi. Sayılar Türkçe yazımla (6 000, +9,00, 1,04).

## 5. Boşluk ve ölçüler (8 px ızgara)

- Kenar boşluğu 16 px (dar ekran 12), kartlar arası 16, kart yarıçapı 8, gölge: 10 px bulanıklık, 4 px aşağı, %10.
- Başlık çubuğu 40 · sekme şeridi 32 · grup satırı 84 → **şerit toplam 116 px** (dar: 36 + 30 + 74 = 102).
- Durum çubuğu **26 px**, komut çubuğu **30 px** (yüzen, görünüm kartı içinde 16 px üstünde).
- Sol model ağacı **300 px**, sağ denetçi **340 px** (dar: 300), araç rayı 40 px, ray düğmesi 36.
- Satırlar: ağaç 24, alan 22 (satır adımı 26), bölüm başlığı 28, tablo satırı 22, çip 30, mini araç çubuğu 32.
- Metin tabanları 8 px katlarına oturur (alan: y+17, ağaç: y+16, çip: y+19,5 ≈ dikey merkez).

## 6. Panel yerleşimi kuralları

- **Üst krom** (başlık + şerit) tek beyaz yüzeydir; altındaki gövde zemin rengindedir, kartlar yüzer.
- **Sol kart = Model ağacı** (Model / Göster / Tablolar / Raporlar sekmeleri; arama; katlar → nesneler; kütüphane, yükler, gruplar). Ağaçtan seçim modelde vurgulanır; alt bilgi "Seçileni ağaçta göster" ve sayaç.
- **Orta kart = Görünüm**: solda yüzen ray (seç, kaydır, döndür, pencere zoom, Home, plan/3B/kesit, çubuk↔ekstrüzyon, ölç, sorgu); üstte görünüm çipleri (ad, derinlik/sınır, Seçim çipi) ve sağda render/görünürlük düğmeleri; altta eksen üçlüsü (sol), seçim anahtarları (sağ) ve komut çubuğu.
- **Sağ kart = Yan panel iskeleti**: üstte pencere düğmeleri (Özellikler, Kataloglar, Model ağacı, Filtre & görünürlük, Sorgu; etkin olan Altın pil, sağda sabitle/yüzdür), altında seçili pencere. Özellikler nesne türüne göre bölümler gösterir; alt bilgi "Anında uygula" anahtarı + Uygula / Al.
- **Alt dock** (sonuçlarda): görünüm kısalır, tablolar kartı görünümün altında aynı genişlikte açılır.
- **Diyaloglar** zemin %22 karartılır, kart 10 px yarıçap ve büyük gölge; sol sütun kayıtlı öğeler, sağ gövde, alt düğme sırası (birincil en sağda gradyan).

## 7. Şerit yapısı

`Dosya` (Kahve pil, arka plan menüsü) + sekmeler **Model · Düzenle · Yükler · Analiz · Tasarım · Görünüm · Raporlar**; etkin sekme Altın alt çizgi. Sağda "Şeridi özelleştir" (göz: sekme gizle, dişli: sırala/kullanıcı sekmesi, ok: daralt). Grup satırı: büyük düğme (24 px ikon + 11 px ad, 58×58) ve 3'lü küçük yığın (16 px ikon + ad), gruplar kılçık ayraçla ayrılır, grup adı altta gri. Etkin komut (KİRİŞ) Altın dolgu + Altın kenar. Sağ uçta her sekmede sabit: **Geçerli yük deseni** açılır listesi ve **Çöz F5** gradyan düğmesi.

Model sekmesi grupları: Aks & Kat · Kolon · Kiriş (+ İkincil, Aşık, Konsol) · Çapraz · Döşeme · Duvar · Temel · Hızlı kolon / Hızlı kiriş · Seç (+ Seç & Süz…, Benzerini seç, Tersine çevir). Tasarım sekmesi: Yönetmelik · Tasarım (Çelik, Betonarme, Kompozit) · Göster (D/C renkleri, Şekil değiştirme, N/V/M, Reaksiyonlar) · Tablolar · Rapor. Dar ekranda küçük yığınlar yalnız ikon olur.

## 8. İkon dili

Tek renk çizgi ikonlar, **1,5 px kalem**, yuvarlak uç ve birleşim, 24 birimlik kutuda 2 px iç pay; boyutlar 24 (şerit büyük), 20 (ray), 16 (küçük düğme, çip), 14 (ağaç, alan içi). Renk: etkin Antrasit, pasif `metin2`, açıklama `metin3`; ikon hiçbir zaman renkli değildir (Altın yalnız dolgu/pil). Emoji yok; tüm ikonlar `tuval.py` içinde vektör olarak tanımlı (81 ikon) ve 4× süper örnekleme ile çizilir — yerel sürümde aynı tanımlar ImDrawList yollarına çevrilir.

## 9. Seçim ve vurgu

- Seçili nesne: Altın kontur + açık altın dolgu (modelde), ağaçta Altın sol şerit + `altin_dolgu` satır, denetçide "6 seçili" rozeti.
- Üzerine gelme: ince Kahve kontur + "C2-31 · HE340A · Kat 2" çipi.
- Doğrudan değiştirme: **Altın = başlangıç**, **Kahve = bitiş**, beyaz kare = orta (böl/köşe ekle), ölçü çipi "6 000" tıklanıp yazılabilir.
- Bağlamsal mini araç çubuğu seçimin yanında: kesit · malzeme · kat · serbestlik ön ayarı · "…" (özelleştirilebilir profil).
- "Seçim" çipi görünüm üstünde: sayı, kesit, kat; Benzerini seç · Yalnız seçili (Ctrl+5) · Ctrl+K ters · kapat.

## 10. Dar ekran davranışı (1366×768, `kucuk.png`)

Model ağacı kartı kapanır ve rayın tepesine "Model ağacı" düğmesi olarak taşınır (tıklayınca görünüm üstüne yüzer); denetçi 300 px; şeritte küçük yığınlar yalnız ikon, yük deseni listesi gizlenir, Çöz kalır; görünüm çipleri kısalır ("Derinlik: tümü"); "Seçim" çipinde eylemler gizlenir (sağ tık menüsünde kalır); denetçide Genel ve Konum bölümleri kapalı başlar; durum çubuğunda ipucu metni ve koordinat gizlenir, kat kapsamı "Bu kat / Benzer / Tümü" olur. Hiçbir öğe yer değiştirmez, yalnız kısalır.

## 11. Yerel eşleme (Dear ImGui + özel bileşenler)

| Maket öğesi | Uygulama |
|---|---|
| Zemin, kart, gölge | `ImGui::Begin` çerçevesiz pencereler; kart = `ImDrawList::AddRectFilled` (yuvarlak 8) + gölge dokusu (9-slice, önceden bulanıklaştırılmış) |
| Başlık çubuğu | Özel pencere kromu (DWM, `WM_NCHITTEST`), logo `ID2D1Bitmap`/DX12 dokusu, Cormorant başlık |
| Şerit | Özel `Serit` bileşeni: sekme şeridi (`ImGui::TabBar` değil, kendi çizimi) + grup satırı; JSON tanımı (`serit.json`) → göz/sürükle/kullanıcı sekmesi |
| Yüzen ray, çipler, mini araç çubuğu | Görünüm penceresi içinde `SetCursorPos` ile konumlanan çocuk pencereler (`ImGuiWindowFlags_NoBackground` + kendi kartı) |
| Yan panel iskeleti | Tek `ImGui` penceresi; pencere düğmeleri + içerik; Ctrl+tık yığma, sürükle-yapıştır için kendi dock mantığı (ImGui docking dalı gerekmez) |
| Özellikler bölümleri | `Bolum()` (collapsing header'ın özel çizimi), `Alan()` (`InputText` + "…" düğmesi → katalog modal), çoklu seçimde "—" |
| Parçalı anahtar, anahtar, rozet | Özel `Parcali()`, `Anahtar()`, `Rozet()` bileşenleri (tema belirteçlerinden renk) |
| Komut çubuğu | `InputText` + öneri listesi (Son / Şerit / Menü / Tümü), Ctrl+Q ve `:` odaklar; TR/EN takma ad tablosu |
| Durum çubuğu | Tek satır `ImGui` penceresi; kat kapsamı `Parcali()`, kapsam balonu `BeginTooltip` yerine kendi kart |
| 3B görünüm | DX12 çerçeve dokusu (`ImGui::Image`); seçim/hover konturu DX12 tarafında (stencil + kalınlaştırma), tutamaçlar ve çipler ImGui katmanında |
| İkonlar | `tuval.py` yol tanımları → `ImDrawList::AddPolyline/PathStroke` (1,5 px, yuvarlak uç) veya ön-render atlas; DPI'ya göre yeniden üretilir |
| Yazı | Inter değişken, ağırlık başına ayrı atlas (400/450/500/600/700), opsz 14; Cormorant yalnız başlık |
| Tema | Belirteç tablosu (`tema.json`: açık + koyu çift); ImGui `StyleColors` yalnız fallback |

Ölçek: tüm ölçüler mantıksal px; `S = DPI/96` ile çarpılır (maketteki `Tuval.S` ile aynı mantık).

## 12. Dosya §4 — 25 çıkarımın maketteki yeri

| # | Çıkarım | Maketteki karşılığı |
|---|---|---|
| 1 | Ribbon sekme iskeleti | Sekme şeridi: Dosya + Model/Düzenle/Yükler/Analiz/Tasarım/Görünüm/Raporlar; Model ve Tasarım grupları (`ana.png`, `sonuc.png`, `detay-serit.png`) |
| 2 | Göz ile sekme gizleme, sürükleyerek sıralama, kullanıcı sekmesi | Şerit sağ ucu "Şeridi özelleştir" göz/dişli/daralt simgeleri (`detay-serit.png`); JSON tanımı §11 |
| 3 | Hızlı Başlat (Ctrl+Q) + komut satırı | Yüzen komut çubuğu: "Komut: _", "Ctrl+Q · Hızlı başlat" çipi, geçmiş simgesi, "TR \| EN takma adlar" (`ana.png` alt) |
| 4 | Durum çubuğu içeriği | Sol yönerge "Kiriş: ikinci noktayı seçin" + Enter/Esc ipucu; orta Orto / Akıllı yakalama / Sürükle + X Y Z kilit + orta tuş; sağ kat kapsamı, birim, koordinat, "6 nesne · 12 tutamaç" (`ana.png`, `kat-kapsami.png`) |
| 5 | Yan panel = tek iskelet, çok pencere | Sağ kart üstünde Özellikler (Altın pil) · Kataloglar · Model ağacı · Filtre & görünürlük · Sorgu + sabitle/yüzdür (`detay-panel.png`) |
| 6 | Kalıcı bağlamsal Özellikler paneli + "…" katalog | Bölümler Genel/Kesit/Konum/Serbestlikler/Yükler/Analiz/Tasarım; Profil ve Malzeme yanında "…"; "6 farklı" çoklu değer; Anında uygula / Uygula / Al (`detay-panel.png`) |
| 7 | Bağlamsal mini araç çubuğu | Seçimin yanında "IPE400 · S355 · Kat 2 · Mafsal · …" kartı, altın bağlantı çizgisi (`ana.png`) |
| 8 | Seçim anahtarları çubuğu + kapsam seviyesi | Görünüm sağ altındaki yüzen pil: tümü, düğüm, kolon, kiriş, döşeme, duvar, aks, yük, mesnet, temel + "Kapsam: Eleman ▾" + göz (`ana.png`) |
| 9 | Seçim filtresi diyalogu | `secsuz.png`: Kategori/Özellik/Koşul/Değer satırları, parantez, Ve/Veya, kayıtlı `.filtre` listesi, "Görünüm süzgeci yap", "Renk kuralı…" |
| 10 | Select ölçüt listesi, Benzerini seç, Ctrl+K/J/Q, gruplar | `secsuz.png` özellik listesi notu; "Benzerini seç" düğmesi (diyalog, şerit Seç grubu, Seçim çipi); "Ctrl+K ters"; ağaçta Gruplar (3) |
| 11 | Kat kapsamı anahtarı | Durum çubuğunda Bu kat / Benzer katlar / Tüm katlar (Alt+2), "3 katta uygulanacak" önizlemesi; balon: ana kat, benzer katlar, Zemin "Yok — etkilenmez", geri al tek adım (`kat-kapsami.png`) |
| 12 | Kat Verisi tablosu | Ağaçta Kat 3/Kat 1 "benzer → Kat 2", Kat 2 "ana kat", Zemin "temel" rozetleri; kotlar; Page Up/Down plan katı (§11 komutlar) (`detay-panel.png`) |
| 13 | Aks sistemi diyalogu | Şerit "Aks sistemi" düğmesi; ağaçta "Aks sistemleri (1)"; modelde A–D / 1–5 balonları ve ince kâğıt ızgarası (`ana.png`) |
| 14 | Kat/aks görünümleri, derinlik, bina sınırları | Görünüm çipi "Derinlik: tümü · Sınır: Zemin–Kat 3"; rayda Plan/3B/Kesit düzlemi; kot cetveli (`ana.png`) |
| 15 | Hızlı kolon/kiriş, yakalama, nesne özellikleri paneli | Şerit "Hızlı kolon / Hızlı kiriş" grubu; durum çubuğunda Orto + Akıllı yakalama + "sağ tık yakalama"; çizim özellikleri sağ paneldeki Özellikler'e gömülü (`ana.png`) |
| 16 | Doğrudan değiştirme tutamaçları | K2-01 üzerinde Altın başlangıç, Kahve bitiş, beyaz orta kare, "6 000" ölçü çipi (`ana.png`, `ana-2x.png`) |
| 17 | Kopyala/Taşı/Çoğalt diyalogu | Düzenle sekmesi (kopyala, taşı, ayna, çoğalt ikonları `tuval.py`'de hazır); açık kalan diyalog deseni §6 (bu makette açılmadı) |
| 18 | Yük modeli, geçerli yük deseni | Şerit sağ ucu "Geçerli yük deseni: G — Ölü yük"; Özellikler Yükler bölümü "G 4,2 kN/m · Q 6,0 kN/m"; ağaçta "desen 5 · durum 6 · komb. 12" |
| 19 | Mesnet/serbestlik formu | Serbestlikler bölümü: Başlangıç (Altın) / Bitiş (Kahve) parçalı anahtar, ön ayar "Mafsal", Ux Uy Uz Rx Ry Rz dolu/boş, kısmi/yay notu (`detay-panel.png`) |
| 20 | Sonuç gösterimi | `sonuc.png`: D/C renk haritası + 5 eşik lejantı görünüm altında (sayılarla), "Maks 1,04 (K2-05)" işareti; Şekil değiştirmiş şekil kartı (durum/kombo, ölçek, gölge, kübik eğri, kontur, N/V2/V3/T/M2/M3, animasyon); durum çubuğunda animasyon + hız; alt dock tablolar (Tablo seç, küme, elektronik tablo) |
| 21 | Model ağacı | Sol kart: Model/Göster/Tablolar/Raporlar; katlar → Kolonlar/Kirişler/İkincil/Çaprazlar/Döşemeler/Düğümler; Kütüphane, Yükler, Gruplar; seçili satırlar vurgulu (`detay-panel.png`) |
| 22 | Görsel dil (açık tema) | Zemin/kart/altın belirteçleri §3; model beyaz→açık gri gradyan; seçim Altın kontur + dolgu; hover Kahve; "Yalnız seçili" (Seçim çipi ve göz düğmesi) |
| 23 | Render modları, çubuk ↔ ekstrüzyon | Rayda çubuk/ekstrüzyon düğmeleri (Ctrl+1/Ctrl+4 ipucu) ve görünüm sağ üstünde parçalı anahtar; model ekstrüde I-profillerle (`ana.png`) |
| 24 | Navigasyon, eksen üçlüsü, F-tuşları | Rayda kaydır/döndür/pencere zoom/Home; durum çubuğunda "Orta tuş: Kaydır"; köşede küçük X/Y/Z üçlüsü (küp yok); Çöz F5, "F6 şekil değiştirme" (`sonuc.png` durum satırı) |
| 25 | Komut tutarlılığı (TR + EN takma ad, Apply ile açık diyalog, Ekle/Kopyasını ekle/Değiştir/Sil) | Komut çubuğunda "TR \| EN takma adlar"; Seç & Süz'de "Uygula" + "Seç" ayrımı (diyalog açık kalır); Kesit önerisi kartı ve tablo düzenleme düğmeleri (`sonuc.png`) |
