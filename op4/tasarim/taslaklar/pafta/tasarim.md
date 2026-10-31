# op4 arayüz tasarımı — Yön A "Pafta" (çizim paftası dinginliği)

Üretim: `python3 uret.py` (Pillow + numpy; yazı tipleri ve logolar `op4/kimlik/`den okunur, logolar yalnız ölçeklenir).
Bu belge, taslakların arkasındaki kavramı, ölçüleri ve yerel uygulama (Dear ImGui + özel bileşenler) eşlemesini verir.
Referans dosyadaki 25 çıkarımın her birinin taslakta nerede görüldüğü §15'te tablo olarak listelenir.

| Dosya | İçerik |
|---|---|
| `ana.png` 1920×1080 · `ana-2x.png` 3840×2160 | Model sekmesi, 6 kiriş seçili, mini araç çubuğu, tutamaçlar, üzerine gelme, Özellikler açık |
| `kucuk.png` 1366×768 | Aynı oturum, dar düzen (sol ağaç şeride iner, şerit "dar" kipi, kısa Özellikler) |
| `detay-serit.png` | Şeridin 2× kırpımı (başlık + sekmeler + Model grupları) |
| `detay-panel.png` | Model ağacı + Özellikler, 2× kırpım |
| `secsuz.png` | Seç ve Süz penceresi (Kategori / Özellik / Koşul / Değer, Ve/Veya, kayıtlı süzgeçler, Benzerini seç, sonuç) |
| `sonuc.png` | Tasarım sekmesi, D/C renk haritası, 5 eşikli lejant, sonuç araç çubuğu, tablo bölmesi, Özellikler → Tasarım |
| `kat-kapsami.png` | Durum çubuğu kat kapsamı anahtarı ve "3 katta uygulanacak" önizlemesi (2× kırpım) |

---

## 1. Kavram

Program bir **çizim paftasıdır**: sıcak krem kâğıt, üzerinde ince antrasit kıl çizgiler, büyük ve tek renkli çizgi
simgeler, bol boşluk. Açılış ekranındaki (`kimlik/acilis/kare-100.png`) kemer, Inter + Cormorant Garamond ikilisi ve
krem zemin burada çalışma ortamına dönüşür: başlık çubuğundaki belge adı Cormorant ile pafta başlığı gibi yazılır,
görünüm penceresinin sağ alt köşesinde bir **pafta köşesi** (proje · görünüm · gösterim · birim) durur, modelin
oturduğu zemin 1 m kareli bir kâğıttır.

Renk bir anlam taşımadığı sürece yoktur. **Altın tek "niyet mürekkebi"dir**: seçili nesne, etkin sekme/düğme/pencere,
odak imleci, kat kapsamı anahtarının etkin dilimi, başlangıç tutamacı. **Kahve** ikinci derecedir: Dosya düğmesi, bitiş
tutamacı, üzerine gelme konturu, bağlantı metinleri. Geri kalan her şey antrasit mürekkep ve gri kurşun kalemdir.
Sonuç renkleri (D/C) ve sınıf renkleri bu kuralın dışında, yalnız veriye bağlı olarak görünür.

## 2. İlkeler

1. **Kâğıt üstünde mürekkep.** Yüzeyler üç krem tonu; kutu yok, kenarlık yok, yalnız kıl çizgi ayırıcılar ve alt çizgili giriş alanları.
2. **Altın = niyet.** Kullanıcının seçtiği / etkinleştirdiği / odakladığı her şey altın; başka hiçbir süs altın değildir.
3. **Büyük simge, küçük etiket.** Şeritte 30 px çizgi simge + 11 px etiket; grup adları 9 px harf aralıklı büyük harf.
4. **Görünüm kalptir.** Paneller sakin olsun ki model öne çıksın: beyaz→açık gri gradyan, kâğıt zemin, yumuşak gölge, ince koyu kenar.
5. **Her şey yerinde kalır.** Özellikler kalıcıdır, komut satırı hep altta, durum çubuğu hep yönerge verir; iletişim kutuları Uygula ile açık kalır.
6. **Tek iskelet.** Yan panel tek çerçeve–çok penceredir; aynı kural motoru seçimi, görünürlüğü ve rengi süzer; aynı ölçek tablo, lejant ve özellik paneline gider.
7. **8 px ızgara.** Tüm ölçüler 8'in (küçük bileşenlerde 4'ün) katı; metin taban çizgileri satır içinde `y + h/2 + 0,36·boy` ile hizalanır.

## 3. Renk belirteçleri

Marka (kimlik/README.md): Kahve `#8A6B3C`, Krem `#EDE6D8`, Altın `#B08950`, Antrasit `#14181B`, Gri `#8C8C8C`.

| Belirteç | Hex | Kullanım |
|---|---|---|
| `kagit` | `#F6F2EA` | Ana yüzey: şerit, paneller, pencere gövdesi |
| `kagit_acik` | `#FBF8F2` | Giriş alanları, kartlar, yüzen araç çubukları, komut satırı |
| `kagit_koyu` | `#EFE9DD` | Başlık çubuğu, durum çubuğu, tablo başlığı, pasif segment dolgusu |
| `cizgi` | `#D9D6CF` | Kıl çizgi (kâğıt→antrasit %13): panel kenarları, alan alt çizgisi |
| `cizgi_soluk` | `#E6E3DC` | Bölüm ayırıcıları, tablo satır çizgileri (%7) |
| `cizgi_koyu` | `#BBB9B4` | Düğme çerçevesi, onay kutusu kenarı, pafta köşesi çerçevesi (%26) |
| `metin1` | `#14181B` | Birincil metin (Antrasit) |
| `metin2` | `#5C5E5D` | İkincil metin, etiketler (%68) |
| `metin3` | `#8C8C8C` | Sönük metin, sayımlar, grup adları (Gri) |
| `altin` | `#B08950` | Seçim konturu, etkin sekme alt çizgisi, odak imleci, başlangıç tutamacı, anahtar "açık" |
| `altin_acik` | `#EBE1D1` | Seçili satır / etkin düğme dolgusu (%16) |
| `altin_orta` | `#D4C0A0` | Etkin düğme çerçevesi, çip kenarı (%48) |
| `kahve` | `#8A6B3C` | Dosya düğmesi, bitiş tutamacı, üzerine gelme konturu, bağlantı metni ("Katalog ›") |
| `krem` | `#EDE6D8` | Birincil düğme metni (antrasit zemin üstünde) |
| `hata` | `#A8453A` | Sınır aşımı, uyarı sekmesi |
| `yesil` | `#5B8A4A` | "Analiz güncel" noktası |

Görünüm penceresi:

| Belirteç | Hex | Kullanım |
|---|---|---|
| `gok_ust → gok_alt` | `#FFFFFF → #E9E7E2` | Dikey gradyan model arka planı |
| `pafta_zemin` | `#FAF8F3` | Zemin paftası; 1 m ızgara `%5,5`, 6 m'de `%10` antrasit karışımı |
| `celik` | `#D6D4CE` | Çelik üye temel rengi (gölgeleme 0,63–1,03 çarpanı) |
| `beton` | `#E9E6DF` | Döşeme |
| `secim_dolgu` | `#CBBDA8` | Seçili üye dolgusu (çelik→altın %30) + 1,5 px altın kontur |
| kenar | antrasit %52 | 0,75 px yüz kenarı |
| üzerine gelme | kahve %95 | 0,9 px kontur |
| gölge | antrasit %11, 2,5 px bulanık | Işık yönünde zemine izdüşüm |

D/C (açık tema çifti; koyu tema için aynı tonların %20 daha doygun sürümü ayrılır): `< 0,50 #86A9C8` · `0,50–0,70 #83B072` ·
`0,70–0,90 #DCBC52` · `0,90–1,00 #DE8B40` · `> 1,00 #C4463A`. Üye dolgusunda %22 beyazla açılır; lejant, tablo rozeti ve
Özellikler → Tasarım çubuğu doygun sürümü kullanır.

## 4. Tipografi ölçeği (Inter değişken, opsz 14; Cormorant Garamond yalnız belge adı)

| Rol | Boy / ağırlık | Yer |
|---|---|---|
| Belge adı | Cormorant Garamond 19 / 600 | Başlık çubuğu ortası |
| Panel başlığı | 12,5 / 600 | "Model ağacı", "Özellikler", pencere başlığı 15 / 600 |
| Sekme | 13 / 500 (etkin) · 13 / 450 | Şerit sekmeleri; panel sekmeleri 11,5 |
| Seçim özeti | 13 / 600 + 11 / 400 | "6 kiriş seçili" |
| Gövde | 12 / 400 · değer 12 / 500 | Ağaç satırı, alan metni, menü değeri |
| İkincil | 11 / 400 | Ağaç alt metni, sayım, lejant, durum çubuğu |
| Şerit büyük düğme | 11 / 450 (iki satır: 50/62 px taban çizgileri) | |
| Şerit küçük düğme · yüzen çubuk | 11,5 / 400 · 11,5 / 500 | |
| Bölüm başlığı | 9,5 / 600, harf aralığı 1,0 px, BÜYÜK | "GENEL", "KESİT" … |
| Grup adı (şerit) | 9 / 500, harf aralığı 1,1 px, BÜYÜK | "AKS & KAT" |
| Pafta köşesi | 8,5 / 600 harf aralıklı + 10 / 400 | |
| Kısayol rozeti | 10 / 500, `kagit_koyu` yuvarlak dolgu | "Ctrl+Q", "Alt+2" |

Türkçe glifler (İ ı ş ğ ü ö ç) Inter'de tamdır; Σ, ⁴, ³, ✓ de vardır. "∈" yoktur → koşul listesinde "içinde" metni kullanılır.
Sayılar Türkçe biçimde (ondalık virgül, binlik boşluk): `6,000 m`, `23 130 cm⁴`.

## 5. 8 px ızgara ve ölçüler (1×, mantıksal px)

| Öğe | Ölçü |
|---|---|
| Başlık çubuğu | 36 |
| Şerit sekme satırı + gövde | 30 + 84 = **114** |
| Komut satırı | **30** (odak çizgisi altın, 1 px) |
| Durum çubuğu | **26** |
| Sol panel (Model ağacı) | 300 · dar düzende 36 px dikey şerit |
| Sağ panel (Özellikler) + pencere şeridi | 320 + 36 · dar düzende 280 + 36 |
| Panel iç kenar | 16; alan sağ kenarı 12 |
| Satır yüksekliği | 24 (alan 20 + 2 px pay); bölüm başlığı 28; kapalı bölüm 28 + 8 ayırıcı |
| Şerit büyük düğme | 68 × 58, simge 30, etiket 11; küçük düğme satırı 20, simge 15 |
| Yüzen araç çubuğu / mini araç çubuğu | 32 yüksek, yarıçap 6 / 16 (hap), gölge 6 px bulanık %12 |
| Seçim anahtarları çubuğu | 30 yüksek, düğme 32 |
| Pafta köşesi | 236 × 44, iki satır, dikey bölme 150 |
| Tutamaç | 6 px daire (başlangıç altın, bitiş kahve), 8 px kare orta tutamaç |
| Aks balonu | r = 10, 11 / 500 etiket |
| Yarıçaplar | alan 3 · düğme 4 · yüzen kart 6 · hap 16 · pencere 8 |
| Çizgi kalınlıkları | kıl çizgi 1 · simge 1,5 · kenar 0,75 · seçim 1,5 · üzerine gelme 0,9 |

## 6. Panel yerleşimi kuralları

- **Sağ yan panel = tek çerçeve, çok pencere.** 36 px dikey şerit: Özellikler · Kataloglar · Model ağacı · Filtre & görünürlük · Sorgu.
  Etkin düğme `kagit_acik` zemin + 3 px altın sol çubuk. Varsayılan tek pencere açık; Ctrl+tık yığar; düğme sürüklenince
  pencere yüzer ya da sol/alt kenara yapışır (Model ağacı taslakta sola yapışıktır; şeritte küçük nokta bunu gösterir).
- **Özellikler** kalıcıdır; seçim özeti (altın nokta, ad, kısa özet, Ortak/Tek tek), ardından bölümler
  Genel / Kesit / Konum / Serbestlikler / Yükler / Analiz / Tasarım. Kapalı bölüm sağda tek satır özet gösterir. Kesit ve
  Malzeme alanlarının yanında "…" katalog düğmesi (24 × 20). Alt çubuk: **Uygula** (birincil) · **Al** · "Anında uygula" anahtarı.
  Yer kalırsa kesit önizleme kartı (IPE400 çizimi + h, b, tw, tf, Iy, Wpl).
- **Model ağacı** solda; sekmeler Model / Göster / Tablolar / Raporlar; arama; ağaç satırı 24 px, seviye başına 14 px girinti,
  kat satırlarında göz düğmesi ve nesne sayısı; seçili satırlar `altin_acik` + 3 px altın çubuk; alt bilgi "6 seçili · 245 nesne · 4 kat · Seçiliye git".
- **Görünüm penceresi** paneller arasındaki tüm alanı alır; üstünde yüzen görünüm çubuğu (sol üst), sol altta eksen üçlüsü
  ve seçim anahtarları, sağ altta pafta köşesi; seçimin yanında mini araç çubuğu. Sonuç kipinde görünümün altında 30 px lejant
  şeridi ve 224 px tablo bölmesi.
- **Komut satırı** görünümün değil pencerenin altındadır (tüm genişlik), durum çubuğunun hemen üstünde.
- **Pencereler** (Seç ve Süz, Aks sistemi, Kat verisi, Çoğalt…) görünüm penceresi üstünde, %55 kâğıt perde ile; başlık ikon + ad +
  gri açıklama; alt çubukta kıl çizgi, solda ikincil eylem, sağda [Birincil] [İkincil…] [İptal].

## 7. Şerit yapısı

Sekmeler: **Dosya** (kahve dolgulu, arka plan menüsü) · **Model** · **Düzenle** · **Yükler** · **Analiz** · **Tasarım** · **Görünüm** · **Raporlar**.
Etkin sekme altında 2 px altın çizgi; sağ uçta yardım ve şeridi daraltma.

| Sekme | Gruplar (büyük düğmeler · küçük düğmeler) |
|---|---|
| Model (taslak) | **Aks & Kat** Aks sistemi, Kat verisi · Plan: Kat 2 ▾, Yükselti…, Referans düzlemi — **Kolon** · HE340A ▾, Alt/Üst kot, Döndür — **Kiriş** · IPE400 ▾, Tali kiriş, Mafsal–Mafsal ▾ — **Çapraz** · L100×10 ▾, X/V/K ▾ — **Döşeme** · 15 cm BA ▾, Boşluk — **Duvar** — **Temel** · Tekil, Sürekli, Radye — **Hızlı kolon / kiriş** — **Seç** Seç (etkin), Seç ve Süz · Benzerini seç, Tersine çevir, Gruplar… |
| Düzenle | Kopyala/Taşı (Doğrusal, Dairesel, Ayna, **Kat** — açık kalan diyalog, dx/dy/dz×n, Orijinali sil, Hangi atamalar) · Böl/Birleştir/Uzat/Kırp · Kat kopyala · Tablodan düzenle · Geri/Yinele |
| Yükler | Yük desenleri (Ad/Tür/Öz ağırlık/Otomatik yanal) → Durumlar → Kombinasyonlar · Geçerli yük deseni ▾ · Ata: Düğüm/Çubuk/Alan (Ekle/Değiştir/Sil) · Mesnet (6 DOF + ankastre/mafsal/kayıcı/serbest, Bağlı/Mesnetli, yay, kısmi 0–1) · Atamaları göster/temizle |
| Analiz | Model kontrolü · Çöz (F5) · Seçenekler · Analiz modeli görünümü |
| Tasarım (taslak) | **Yönetmelik** TS EN 1993 · Tercihler…, Kombinasyonlar, Tasarım grupları — **Tasarım** Tasarımı başlat, Kontrol et · Yalnız seçili, Yinele, Kesitleri kilitle — **Göster** D/C oranı (etkin), P–M oranı, Ayrıntı · Eşikler…, Değerleri yaz, Gösterimi temizle — **Sonuçlar** Şekil değiştirme, N/V/M, Reaksiyon · Zarf ▾, Ölçek ▾, Animasyon — **Tablolar** Tablo seç, Rapor · elektronik tablo'e aktar, Tablo kümeleri |
| Görünüm | Yeni görünüm (plan/yükselti/3B/iki nokta) · Kesit düzlemi, Kesit kutusu · Görünüm sınırları · Render (Ctrl+1…5) · Tema (model arka planı) · Pencereler |
| Raporlar | Tablo seç · Tablo kümeleri · Rapor şablonu · Dışa aktar (elektronik tablo/CSV/PDF/IFC) |

Özelleştirme: sekme başlığına gelince sağında 14 px göz simgesi belirir (gizle); sekmeler sürüklenerek sıralanır; "Kullanıcı"
sekmesi JSON tanımıyla (`arayuz/serit.json`) firma profiline girer. Dar ekranda önce küçük düğme listeleri gizlenir ("dar" kipi),
hâlâ sığmazsa sondan başlayarak gruplar tek açılır düğmeye döner.

## 8. Simge dili

- 24 birimlik tasarım ızgarası, tek renk, **1,5 px** çizgi (her boyda sabit), yuvarlak uç ve köşe, dolgu yalnız imleç/ok gibi küçük işaretlerde.
- Boylar: şerit büyük 30, küçük 15, panel 16, yüzen çubuk 15, seçim anahtarı 17, durum çubuğu 14, satır 12.
- Renk = metin rengi: etkin `metin1`, ikincil `metin2`, kapalı anahtar `metin3`; altın hiçbir simgede kullanılmaz (altın yalnız zemin/kontur).
- Yapısal simgeler kesit/şema çizimleridir (kolon = I profil ön görünüşü, kiriş = mesnetli çubuk, çapraz = çerçeve + X, döşeme = kalınlıklı plak,
  temel = pabuç + zemin çizgisi, aks = balonlu çizgiler, kat = yığılmış düzlemler); hızlı kolon/kiriş = eleman + imleç oku.
- Emoji yok, marka simgesi yok; referans programların ikon sanatı kopyalanmaz.

## 9. Seçim, üzerine gelme, tutamaç

| Durum | Görünüm penceresi | Paneller |
|---|---|---|
| Seçili | 1,5 px **altın** kontur (dış siluet + yüz kenarları) + `secim_dolgu` hafif altın dolgu | `altin_acik` satır + 3 px altın sol çubuk |
| Üzerine gelme | 0,9 px **kahve** kontur + imleç yanında antrasit etiket "C3-B1 · HE340A" | `kagit_koyu` satır |
| Tutamaç | **başlangıç altın**, **bitiş kahve** (6 px daire, krem kenar); orta tutamaç 8 px kare (altın çerçeve) → bölme/köşe | Serbestlikler bölümünde aynı renkli noktalar |
| Ölçü etiketi | "6,000 m" krem hap, altın çerçeve; tıklanıp yazılır | — |
| Odak | 1,5 px altın imleç + alt altın çizgi (komut satırı), alan alt çizgisi altın | |
| Yalnız seçiliyi göster | diğerleri %85 saydam (Ctrl+5) | |

## 10. Görünüm penceresi (pafta)

Arka plan beyaz→açık gri dikey gradyan; zemin paftası 1 m ızgaralı krem kâğıt (6 m'de koyu çizgi), kıl çerçeve; aks çizgileri
zeminde kesik-noktalı, uçlarında balonlar (A–D, 1–5); kat seviyeleri D/1 köşesinin sağında kısa kesik çizgi + "+9.00 Kat 2";
ekstrüzyon kipinde gerçek I/L kesitler, tek yönlü ışık (sol-ön-üst) + gök katkısı, uzaklıkla kâğıda solma (%20), zemine
yumuşak gölge; çubuk kipinde eksen çizgileri + düğüm noktaları. Sol altta eksen üçlüsü (küp yok), sağ altta pafta köşesi.
Yüzen görünüm çubuğu: **Çubuk ↔ Ekstrüzyon** segmenti · Gölge · Izgara · Kat düzlemleri · Perspektif ▾ · Görünüm: 3B ▾ ·
Kesit düzlemi · Görünüm sınırları. Arka plana çift tık → görünüm özellikleri.

## 11. Durum çubuğu ve komut satırı

Durum çubuğu (26 px, `kagit_koyu`): **sol** adım yönergesi / hata ("Kiriş: ikinci noktayı seçin · Enter bitirir · Esc iptal · Tab yakalama adayı");
**orta** Orto (O) · Akıllı yakalama (S) · Sürükle-bırak (D) tıklanabilir anahtarlar (açık: `altin_acik` zemin) + X Y Z kilit kutuları (kilitli: altın);
**sağ** "Kat kapsamı" + üç durumlu segment **Bu kat / Benzer katlar / Tüm katlar** (Alt+1/2/3) · birim ▾ · imleç koordinatı · "6 seçili · 12 tutamaç" · marka yazısı.
Plan dışı görünümde kapsam anahtarı gri + ipucu; etkinken işlem öncesi "3 katta uygulanacak" kahve metni ve anahtarın üstünde
önizleme kartı (kat listesi, ana kat, benzer → ana, Zemin "Yok" — temel seviyesi dışlanır).

Komut satırı (30 px, `kagit_acik`): "Komut:" + altın imleç; sağda "Son: KİRİŞ — 6 kiriş eklendi (Kat 2)"; yazarken Türkçe/İngilizce
takma ad ve ipucu ("beam · kiriş · Enter: en üstteki komut"); Ctrl+Q ya da `:` odaklar; sonuç listesi Son / Şerit / Menü / Tümü sekmeli
açılır pencere (yukarı doğru), nesne etiketleri (K12, B3) de aranır; seçilen komutun şeritteki yeri 1 s altın vurgulanır;
geçmiş ok simgesi ve ↑ ile.

Klavye: Esc bitir, Enter son komut, Space/orta tuş tamamla, D doğrudan değiştirme, O/S/H anahtarlar, Ctrl+1…5 render,
Shift+tekerlek kapsam seviyesi, Home/End/Shift+Space zoom, F5 çöz, F4/F6 deformasyonsuz/deformasyon, Ctrl+A/K/J/Q seçim, Ctrl+T tablolar.

## 12. Küçük ekran davranışı (1366×768 — `kucuk.png`)

- Sol Model ağacı 36 px dikey sekme şeridine iner (Model ağacı · Göster · Tablolar · Raporlar); tıklanınca görünümün üstüne yüzer.
- Sağ panel 280 px; Özellikler'de kesit önizleme kartı gizlenir, Genel/Konum bölümleri kısalır; bölüm özetleri korunur.
- Şerit "dar" kipi: küçük düğme listeleri gizlenir, büyük düğmeler ve grup adları kalır (1252 px); daha darda gruplar açılır düğmeye döner.
- Görünüm çubuğunun son iki düğmesi (Kesit düzlemi, Görünüm sınırları) "…" menüsüne gider; kamera biraz yukarı alınır.
- Durum çubuğu yönergesi kısalır, marka yazısı gizlenir; komut satırı ipucu korunur.
- 1280 px altı desteklenmez (uyarı); yüksek DPI'da tüm ölçüler mantıksal px × ölçek (2× çıktı `ana-2x.png`).

## 13. Yerel eşleme: Dear ImGui + özel bileşenler (C++ / DirectX 12)

**Stil** (`ImGuiStyle`): `WindowBg = kagit`, `ChildBg = kagit`, `PopupBg = kagit_acik`, `FrameBg = kagit_acik`, `Border = cizgi`,
`Text = metin1`, `TextDisabled = metin3`, `Header/HeaderHovered/HeaderActive = altin_acik`, `CheckMark/SliderGrab = altin`,
`Button = 0` (yalnız hover `kagit_koyu`), `TitleBg = kagit_koyu`, `Separator = cizgi_soluk`, `TableHeaderBg = kagit_koyu`,
`TableRowBgAlt = kagit_acik`; `FrameRounding 3`, `ChildRounding 4`, `PopupRounding 6`, `WindowRounding 6` (yüzen),
`FrameBorderSize 0` (alt kıl çizgi özel), `WindowPadding (16,16)`, `FramePadding (8,4)`, `ItemSpacing (8,4)`, `CellPadding (8,4)`,
`ScrollbarSize 8`, `GrabMinSize 8`. Bütün belirteçler `arayuz/tema.json`dan yüklenir (koyu tema aynı anahtarlarla ikinci set).

**Yazı tipleri**: ImGui değişken eksenleri bilmez; Inter `wght` 400/450/500/600 ve boylar 9–19 px için FreeType (`ImGuiFreeType`)
ile `FT_Set_Var_Design_Coordinates` çağıran özel yükleyiciyle ayrı `ImFont`lar oluşturulur (DPI ölçeğinde yeniden rasterize).
Cormorant 19/600 yalnız başlık için. Harf aralıklı başlıklar `ImDrawList::AddText` ile harf harf.

**Özel bileşenler** (`arayuz/bilesen/*.cpp`, hepsi `ImDrawList` üstünde):
`Serit` (sekme satırı + gruplar + büyük/küçük düğme, dar kipi, özelleştirici), `YanPanelSeridi` (dikey metin: önceden döndürülmüş
glif atlası), `Ozellikler` (bölüm + satır + alan + "…" düğmesi + çip + D/C çubuğu; `ImGui::InputText` gömülü),
`ModelAgaci` (`TreeNodeEx` + özel satır zemini ve sayım sütunu), `SegmentAnahtar`, `KatKapsami` (durum çubuğu + önizleme popover),
`KomutSatiri` (Ctrl+Q açılır listesi, takma ad tablosu TR/EN), `DurumCubugu`, `YuzenCubuk` (gölge = 3 katmanlı yarı saydam
yuvarlak dikdörtgen), `MiniAracCubugu` (seçim merkezine bağlı, profil dosyası ile özelleştirilir), `SecSuz` (kural tablosu
`BeginTable`), `TabloBolmesi` (`BeginTable` + sıralama + elektronik tablo), `Lejant`, `PaftaKosesi`.

**Simgeler**: 24 birimlik yol tanımları (`arayuz/simgeler.json`) → çalışma anında `PathLineTo/PathStroke` ile 1,5 px × DPI ölçeği;
sık kullanılanlar MSAA'lı atlasa önceden rasterize edilir (16/24/30 px).

**Görünüm**: DX12 render-to-texture → `ImGui::Image`; ID tamponu (R32_UINT) ile seçim/üzerine gelme kenarları post-process'te
(kimlik farkı = kenar; seçili → altın 1,5 px, hover → kahve 0,9 px, diğer → antrasit %52 0,75 px); gradyan arka plan tam ekran üçgen;
zemin paftası ve ızgara ayrı geçiş (uzaklıkla solma); gölge: ışık yönünde düzlemsel izdüşüm + ayrılabilir Gaussian; aks balonları,
kot etiketleri, tutamaçlar, ölçü etiketleri ve mini araç çubuğu `ImDrawList` katmanında ekran koordinatlarıyla (model→ekran dönüşümü
CPU'da). Render kipleri (tel/gölgeli tel/gri/katı/yalnız seçili) piksel gölgelendirici sabitleri; çubuk ↔ ekstrüzyon geometri yolu.

## 14. İçerik (taslaktaki oturum)

Proje "Depo Binası – Tokat OSB": aks A–D × 1–5 (6 m), kotlar ±0.00 / +4.50 / +9.00 / +13.50; HE340A kolon (60), IPE400 kiriş (93),
IPE200 çatı aşığı (24), L100×10 X çapraz (36), 15 cm BA döşeme (ofis bölümü 3–5 aksları, 12). Seçili: K2-2AB … K2-3CD (Kat 2,
aks 2 ve 3, A–D). Mini araç çubuğu "IPE400 · S355 · Kat 2 · Mafsal". Komut satırı: "Son: KİRİŞ — 6 kiriş eklendi (Kat 2)".
Kat kapsamı: Benzer katlar (Kat 2 ana kat; Kat 1 ve Kat 3 benzer; Zemin yok).

## 15. Referans dosyadaki 25 çıkarımın taslaktaki karşılığı

| # | Çıkarım | Taslakta nerede |
|---|---|---|
| 1 | Ribbon sekme iskeleti | `ana.png` sekme satırı: Dosya + Model / Düzenle / Yükler / Analiz / Tasarım / Görünüm / Raporlar; Model grupları `detay-serit.png`; Tasarım grupları `sonuc.png`; diğer sekmeler §7 |
| 2 | Göz simgesiyle sekme gizleme, sürükleme, kullanıcı sekmesi | Etkileşimde görünür (sekme başlığına gelince göz simgesi); kural ve JSON tanımı §7; şerit sağ ucunda daraltma |
| 3 | Hızlı Başlat (Ctrl+Q) + komut satırı | `ana.png` alt komut satırı: "Komut: _ · Son: …", sağda "Hızlı başlat: komut, iletişim kutusu, ayar, etiket (K12, B3) · TR/EN", Ctrl+Q rozeti, geçmiş simgesi; `kat-kapsami.png` komut yazılırken "beam · kiriş" takma adı |
| 4 | Durum çubuğu içeriği | `ana.png` durum çubuğu: sol yönerge; orta Orto / Akıllı yakalama / Sürükle-bırak + X Y Z kilit; sağ kat kapsamı, birim ▾, koordinat, "6 seçili · 12 tutamaç" |
| 5 | Yan panel = tek iskelet, çok pencere | Sağ 36 px şerit: Özellikler (altın etkin), Kataloglar, Model ağacı (sola yapışık, nokta), Filtre & görünürlük, Sorgu; `detay-panel.png` |
| 6 | Kalıcı bağlamsal Özellikler + kütüphane ayrımı | `detay-panel.png`: Genel / Kesit / Konum / Serbestlikler / Yükler / Analiz / Tasarım; "…" katalog düğmeleri; çoklu seçim "K2-2AB … K2-3CD (6)", Ortak/Tek tek; Uygula / Al / Anında uygula; ağaçta Kütüphaneler (Kesitler, Malzemeler) |
| 7 | Bağlamsal mini araç çubuğu | `ana.png` seçimin üstünde "IPE400 ▾ · S355 ▾ · Kat 2 · Mafsal ▾ · ⚙ (özelleştir)" |
| 8 | Seçim anahtarları çubuğu | Görünüm sol altındaki yüzen çubuk: Düğüm, Kolon, Kiriş, Çapraz, Döşeme, Duvar, Aks, Yük, Mesnet, Temel, Tümü + "Kapsam: Nesne ▾" (Shift+tekerlek) |
| 9 | Seçim filtresi diyalogu | `secsuz.png`: ( Kategori / Özellik / Koşul / Değer ) Ve/Veya satırları, parantez, kayıtlı `.filtre` listesi, üst segment Seçim süzgeci / Görünüm süzgeci / Renk kuralı |
| 10 | Seç menüsü ölçütleri + Benzerini seç + gruplar | Şerit Seç grubu (Benzerini seç, Tersine çevir, Gruplar…); `secsuz.png` "Benzerini seç — seçili 6 kirişten kural üretildi"; Kat / Kesit / Serbestlik / Yük deseni kuralları; ağaçta Gruplar (3) |
| 11 | Kat kapsamı anahtarı | Durum çubuğu segmenti Bu kat / **Benzer katlar** / Tüm katlar; `kat-kapsami.png` önizleme: Kat 3 benzer → Kat 2, Kat 2 ana kat, Kat 1 benzer, Zemin yok, "3 katta uygulanacak · plan konumu + nesne türü eşleşir", Alt+2 |
| 12 | Kat Verisi tablosu | Şerit "Kat verisi" düğmesi; ağaçta Katlar (kot, sayım, göz); "Plan: Kat 2 ▾" seçici; Kat verisi formu §7 |
| 13 | Aks sistemi diyalogu | Şerit "Aks sistemi"; ağaç "Aks sistemi A–D × 1–5"; görünümde balonlu aks çizgileri (doğrudan tutamaçla taşınır) |
| 14 | Kat / aks görünümleri | Görünüm çubuğu "Görünüm: 3B ▾" (plan/yükselti listesi), "Görünüm sınırları", "Kesit düzlemi"; şerit "Plan: Kat 2 ▾", "Yükselti…"; pafta köşesi görünüm adı |
| 15 | Yerleştirme ve yakalama | Şerit "Hızlı kolon / kiriş" grubu; durum çubuğu Orto / Akıllı yakalama; `kat-kapsami.png` "Tab yakalama adayı"; Özellikler → Konum (Düzlemde / Derinlikte / Uç ofseti) = nesne özellikleri formunun yan panele gömülmesi |
| 16 | Doğrudan değiştirme tutamaçları | `ana.png` K2-3BC: altın başlangıç, kahve bitiş, orta kare tutamaç, yazılabilir "6,000 m" ölçü etiketi; durum çubuğu "D: doğrudan değiştirme" |
| 17 | Kopyala / Taşı / Çoğalt diyalogu | Düzenle sekmesi tanımı §7 (Doğrusal / Dairesel / Ayna / Kat, açık kalan diyalog, Orijinali sil) — taslakta çizilmedi |
| 18 | Yük modeli | Ağaç: Yük desenleri G · Q · W · E (4), Kombinasyonlar TS EN 1990 (12); Özellikler → Yükler özeti "G 2,50 · Q 5,00 kN/m"; `secsuz.png` "Yük deseni = Q"; Yükler sekmesi ve geçerli yük deseni §7 |
| 19 | Mesnet atama formu | Özellikler → Serbestlikler: ● Başlangıç (altın) / ● Bitiş (kahve) Mafsal ▾, Serbest çipleri M2 · M3 (+); 6 DOF + hızlı ön ayar formu §7 |
| 20 | Sonuç gösterimi | `sonuc.png`: D/C renk haritası, görünüm altında 5 eşikli lejant (sayımlarla, "Eşikleri düzenle…"), sonuç çubuğu Model / Deformasyon / N / V / M / D/C + Zarf ▾ + Ölçek ▾ + Gölge + Kübik + animasyon kaydırıcısı, değer etiketleri, tablo bölmesi (Çelik tasarım özeti / Eleman kuvvetleri / Mesnet reaksiyonları / Kat tepkileri / Uyarılar), Özellikler → Tasarım (D/C çubuğu, kontroller) |
| 21 | Model ağacı | Sol panel: Model / Göster / Tablolar / Raporlar; Katlar → Kat 2 → Kolonlar (20), Kirişler (31) → K2-2AB…, Çaprazlar, Döşemeler; Kütüphaneler; Yükler; Gruplar; seçim ağaçla eşzamanlı, "Seçiliye git" |
| 22 | Görsel dil (açık tema) | Tüm ekranlar: krem kâğıt yüzey, beyaz→açık gri gradyan model arka planı, altın kontur + hafif dolgu seçim, kahve hover; D/C paleti açık/koyu çift §3; "Yalnız seçiliyi göster" §9 |
| 23 | Render modları | Görünüm çubuğu **Çubuk ↔ Ekstrüzyon** segmenti; Gölge / Izgara / Kat düzlemleri; Ctrl+1…5 §11 |
| 24 | Navigasyon | Sol altta eksen üçlüsü (küp yok); Perspektif ▾; durum çubuğu "Shift+tekerlek: kapsam seviyesi"; kısayollar §11 (F5, F4/F6, Home/End) |
| 25 | Komut tutarlılığı | Komut satırında Türkçe + İngilizce takma ad ("beam · kiriş"), TR/EN ibaresi, geçmiş; `secsuz.png` "Seçime ekle / Seçimden çıkar" ile açık kalan pencere; Ekle / Kopyasını ekle / Değiştir-Göster / Sil deseni katalog ve liste formlarında §7 |
