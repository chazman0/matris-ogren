# op4 — Seç & Süz: hibrit tasarım (pratik ölçüt rafı + isteğe bağlı Gelişmiş kural katmanı)

Durum: tasarım önerisi, 31.10.2026. Dayanak: MIMARI §11 (seçim, Seç ve Süz, sorgu dili, atama kapsamları), §24 S5 / S7
sözleşmeleri, `op4/tasarim/ARAYUZ_ILKELERI.md` ilke 8–11 ve 21. Görseller Atölye iskeletiyle (yenilenmiş yön) çizildi;
renkler geçicidir ve bu belge **renkten bağımsızdır**: yalnız belirteç adları (`vurgu`, `seçim`, `hover`, `yüzey`…)
geçer, değerleri ayrı paletten gelir (§18).

| Görsel | İçerik |
|---|---|
| `secsuz-pratik.png` | Pratik katman: Kesit listesi açık, HE340A ve IPE400 işaretli, çipler "Kat 2 ve Kesit HE340A veya IPE400" → 51 eleman; L100x10 satırının üzerinde canlı önizleme |
| `secsuz-kat.png` | Kat ölçütü: Benzer katlar kapsamı (durum çubuğuyla aynı anahtar) + Kullanım yeri "köşe kolon" → 12 kolon |
| `secsuz-gelismis.png` | Gelişmiş açık: çipler kural satırına dönüşmüş, ek koşul "Uzunluk > 5,00 m" (histogramlı), iki yönlü sorgu metni, "Süzgeç olarak kaydet" |
| `sec-menusu.png` | Şerit "Seç" bölünmüş düğmesinin menüsü (ölçüte göre seç, alt menüde canlı sayılar) ve elemana sağ tık menüsü |
| `yuk-ata-hedef.png` | YÜKATA komutu: Hedef istemi aynı ölçütleri sunar (Seçim · Kat · Kesit · Kullanım yeri · Grup · Süzgeç) → 42 dış kiriş, ok önizlemesi |
| `karsilastirma.png` | Beşinin etiketli yan yana sayfası (2400 px) |

Görsellerdeki bütün sayılar örnek modelden (Depo Binası – Tokat OSB: A–D × 1–5 aks, 3 kat, 263 eleman) `ozn.py` ile
**hesaplanmıştır**; elle yazılmış sayı yoktur. Üreteç: `secsuz_uret.py` (Atölye `uret.py` / `tuval.py` / `sahne.py`
kopyaları üstüne).

---

## 0. Karar özeti

1. Seç & Süz **tek pencere, iki katman**dır. Varsayılan katman **pratik**tir: solda ölçüt kategorileri, sağda o
   kategorinin **sayılı onay listesi**; işaretlemek anında seçer. Kural editörü varsayılan olarak **görünmez**.
2. Birleştirme kuralı tektir ve ekranda yazılıdır: **aynı ölçütte işaretlenenler "veya", ölçütler arasında "ve"**.
   Etkin ölçütler üstte **çip** olarak okunur: `Kat 2  ve  Kesit HE340A veya IPE400 → 51 eleman`.
3. **Kip** (Yeni seçim / Ekle / Çıkar / Kesişim) panelin tepesinde parçalı anahtardır; her işaretleme, panel açıldığında
   alınan **taban seçime** göre yeniden hesaplanır (birikmez, geri alınabilir).
4. **Kat kapsamı** (Bu kat / Benzer katlar / Tüm katlar) Kat ölçütünü **üretir**; panel ile durum çubuğu aynı anahtarı
   paylaşır. Kat çipi silinirse evren tüm modeldir.
5. **Hızlı eylemler**: Tümü, Tersine çevir, Önceki seçim, Temizle, Benzerini seç, Yalnız seçiliyi göster, Seçimi grup
   olarak kaydet.
6. **Gelişmiş** anahtarı mevcut çipleri **kural satırlarına çevirir** (kullanıcı asla boş editörle başlamaz); burada
   sayısal karşılaştırma, metin içerir, boş/dolu ve tek düzey "veya grubu" eklenir; aynı ifade MIMARI §11.3 sorgu
   dilinde iki yönlü yazılır ve **süzgeç** olarak kaydedilir (seçim süzgeci, görünüm süzgeci, renk kuralı: tek motor).
7. Girişler: şerit **Seç ▾** menüsü (ölçüte göre seç), **sağ tık** (Benzerini seç / Bu kesittekileri / Bu kattakileri…),
   **Ctrl+F**, model ağacı ve **atama komutlarının Hedef istemi** (YÜKATA, MESNETATA, KESİTATA…) — hepsi aynı ölçüt
   bileşenini kullanır.

## 1. Sorun ve hedef

- Önceki taslak (`studyo/secsuz.png`, `atolye/secsuz.png`) M programının süzgeç diyaloğunu izliyordu: Kategori /
  Özellik / Koşul / Değer satırları, parantez, Ve/Veya, `.filtre` dosyaları. Kullanıcı: **"kullanımı karmaşık; aslında
  güzel"**. A programının seçimi **pratik** (Seç menüsünden ölçüt seç → listeden işaretle), M programınınki **ayrıntılı**.
  İstenen: ikisinin **hibriti**.
- Asıl istek (değişmedi): "herhangi bir eleman grubunu ya da yeri **süzülebilir herhangi bir özellikle** seç — ör. tüm
  HE340A profiller, tüm kirişler"; "**çizim, yük atama ve mesnet atamada** kata ya da eleman kullanım yerine göre seçim".
- Tasarım ilkesi: **sık iş tek tıkla, nadir iş bir anahtar uzakta.** Kullanıcının %90 işi "şu kattaki şu kesitler",
  "şu katlardaki köşe kolonlar", "dış kirişler", "D/C > 0,9" türündendir: bunlar onay listesiyle biter. Sayısal eşik,
  metin deseni, veya-grubu gibi %10'luk işler Gelişmiş'te durur ve yine çiplerden başlar.

## 2. Kavram: iki katman, tek motor, tek yer

```
            ┌───────────────────── Seç & Süz penceresi (sağ panel) ─────────────────────┐
 girişler → │ Kip: [Yeni seçim | Ekle | Çıkar | Kesişim]                                  │
 Ctrl+F     │ ÖLÇÜTLER  [Kat 2 ×] ve [Kesit HE340A veya IPE400 ×]      (Gelişmiş ○)       │
 Seç ▾      │ ✓ 51 eleman eşleşiyor → yeni seçim: 51                                      │
 sağ tık    │ ┌ kategoriler ┐┌ değer listesi (n / N) ─────────────┐                       │ ← PRATİK katman
 Hedef:     │ │ Nesne türü 7││ ☑ HE340A          20 / 60          │                       │   (varsayılan)
            │ │ Kat       ①││ ☑ IPE400          31 / 93          │                       │
            │ │ Kesit     ②││ ☐ IPE200          12 / 60          │                       │
            │ │ …           ││ …                                  │                       │
            │ └─────────────┘└────────────────────────────────────┘                       │
            │ HIZLI EYLEMLER  Tümü · Tersine çevir · Önceki · Temizle · Benzerini seç …   │
            └─────────────────────────────────────────────────────────────────────────────┘
                     │  Gelişmiş ●  (aynı çipler → satırlar; + sayısal / metin / boş-dolu / veya grubu)
                     ▼
            [Kat ▾][içinde ▾][Kat 2 ▾]  ve  [Kesit ▾][içinde ▾][HE340A, IPE400 ▾]  ve  [Uzunluk ▾][> ▾][5,00 m]
            sorgu: kat içinde [2] ve kesit içinde [HE340A, IPE400] ve uzunluk > 5 m      ← AYRINTILI katman
            [Süzgeç olarak kaydet]  → seçim süzgeci · görünüm süzgeci · renk kuralı
```

- **Tek motor**: her pratik etkileşim bir sorgu ifadesi üretir (§7.3); Gelişmiş aynı ifadeyi satır olarak gösterir.
  Değerlendirici C++ çekirdekte, S5 sütunlu tablo üstünde çalışır (MIMARI §11.3).
- **Tek yer**: pencere sağ panelin **pencere şeridinde** "Seç & Süz" adıyla durur (Özellikler'in hemen altında);
  ayrı modal diyalog yoktur. Eski "Filtre & görünürlük" penceresi **Görünürlük** adını alır ve kayıtlı süzgeçleri
  görünüm süzgeci olarak kullanır.

## 3. Yerleşim ve girişler

### 3.1 Panel (görsel 1–3)

Sağ panel, Seç & Süz etkinken **400 px**'e genişler (kullanıcı sürükleyerek değiştirir; en az 320 px — o zaman kategori
sütunu yalnız simge, 40 px). Dikey düzen (8 px ızgara, 1× mantıksal piksel):

| Bölge | Yükseklik | İçerik |
|---|---|---|
| Başlık | 28 | simge + "Seç & Süz", sabitle, kapat |
| Kip | 8 + 22 + 10 | "Kip" + 4 parçalı anahtar (eşit genişlik) |
| Ölçütler | 20 + 22·n + 8 | "ÖLÇÜTLER" etiketi, sağda `Ctrl+Shift+F` rozeti + **Gelişmiş** anahtarı; çipler satır sonunda kaydırılır; sağda "Temizle" |
| Sonuç kutusu | 44 | ✓ simgesi, "51 eleman eşleşiyor → yeni seçim: 51", altında tür dağılımı + "önceki seçim: 6 kiriş (Ctrl+J)" |
| Gövde | kalan | sol **kategori sütunu 160 px** + sağ **değer listesi** (kaydırılır) |
| Hızlı eylemler | 20 + 2×28 | iki satır düğme (§10) |
| Alt çubuk | 40 | ☑ Yalnız görünenler · anahtar **Anında uygula** · Kapat (anında uygula kapalıysa yerine birincil **Seç (Enter)** gelir) |

Kategori sütunu satırı 24 px: simge 13 px + ad (11,5 px); sağda ya **işaretli değer sayısı** rozeti (`vurgu` dolgulu,
"1", "2") ya da o kategorideki **farklı değer sayısı** (soluk metin, "7", "13"). Etkin kategori: `yüzey` zemin + 2 px
`vurgu` sol şerit + 600 ağırlık. Kategoriler dört başlık altında: TEMEL · KONUM VE GEOMETRİ · ATAMA · SONUÇ; en altta
**+ Özellik ekle…** (şemadaki her alan, §5.2).

Değer listesi: başlık (12,5/600) + sağda sayı açıklaması ("n: Kat 2 ile · N: modelde"), arama kutusu, "Tümü · Hiçbiri ·
Ters" bağlantıları ve sıralama ("aileye göre ▾"), sonra satırlar (22 px; grup satırı 20 px, üç durumlu onay).
Listenin altında: birleştirme kuralının kısa hatırlatması ve **SON KULLANILANLAR** (son 3 bileşim, tek tıkla geri
çağrılır, sayılarıyla).

### 3.2 Girişler (hepsi aynı paneli açar ya da aynı motoru çağırır)

| Giriş | Davranış |
|---|---|
| **Ctrl+F** | Paneli açar, son etkin kategoride arama kutusuna odaklanır. Panel açıksa yalnız odak. |
| Şerit **Model › Seç › Seç ▾** (bölünmüş düğme, görsel 4 ①) | Üst yarı: seçim aracı (imleç). Alt yarı menü: **ölçüte göre seç** (14 kategori) + seçim eylemleri. Kategori satırı tıklanırsa panel **o kategoride** açılır; **▸** alt menüsü değerleri **sayılarıyla** listeler, değere tık doğrudan seçer (panel açılmadan). |
| Şerit **Seç & Süz** büyük düğmesi | Paneli açar/kapatır (basılı görünür). |
| Şerit küçük düğmeler | Benzerini seç · **Kata göre ▾** (kat listesi, sayılarıyla) · Tersine çevir |
| **Elemana sağ tık** (görsel 4 ②) | Başlıkta eleman özeti; **Benzerini seç**, "BUNA GÖRE SEÇ": Bu kesittekileri / Bu kattakileri / Bu kullanım yerindekileri / Bu akstakileri / Bu gruptakileri ▸ (sağda değer ve sayı), **Seç & Süz'de aç (ölçütleri doldur)** |
| Model ağacı | Kat → tür → kullanım yeri düğümü tıklanınca o kümeyi seçer (MIMARI §5.6); sağ tık "Seç & Süz'de aç" düğümün ölçütlerini çip yapar |
| Görünüm üstündeki seçim rozeti | "Seçim: 51 eleman · 20 kolon · 31 kiriş · Kat 2"; tık paneli açar |
| Komut satırı | `SEÇ kesit=IPE400 kat=2` / `SS` (Seç & Süz) / `SEÇ :sorgu kat içinde [2] ve …` — §11.3 dilinde |
| Atama komutları | **Hedef:** istemi (§13) |

## 4. Pratik katman — etkileşim

- **İşaretle = uygula.** Değer satırına tık onay kutusunu değiştirir; "Anında uygula" açıkken seçim aynı karede
  güncellenir (tek `Secim::Uygula`, §16.2). Kapalıyken yalnız önizleme konturu ve sayılar güncellenir; **Seç (Enter)**
  uygular.
- **Satır üstünde durma = önizleme.** İmleç bir değer satırındayken o değer eklenirse **seçime katılacak** elemanlar
  görünümde ince `hover` konturla çizilir ve görünümde küçük etiket çıkar: "Önizleme · L100x10: +8 çapraz → 59 ·
  Tık: Kesit ölçütüne ekler (veya)" (görsel 1). Sayı = o satırın n değeri (§6).
- **Değiştiriciler** (görünümdeki fare eşlemesiyle aynı): **Ctrl+tık** satırı o anki kipten bağımsız **Ekle**,
  **Shift+tık** **Çıkar**, **Ctrl+Shift+tık** **Kesişim** olarak uygular (tek seferlik).
- **Grup satırı** (aile, alt tür, kat grubu) üç durumlu onaydır; tık tüm üyeleri işaretler/kaldırır.
- **Çip ×** o ölçütü kaldırır; çipe tık ilgili kategoriyi açar; çip üzerinde Delete aynı.
- **Temizle** (çip satırının sağı) tüm ölçütleri kaldırır; seçim **taban seçime döner** (§8).
- **Boş ölçüt** seçime dokunmaz: hiçbir değer işaretli değilken panel, seçimi taban seçimde bırakır ("boş = tümü"
  yorumu yapılmaz; tümünü seçmek için **Tümü** eylemi vardır).

## 5. Kategoriler

### 5.1 Hazır kategoriler (sütun sırası)

S5 sütunları `kaynak/cekirdek/oznitelik.h` (`oznitelik::*`) ve `veri/oznitelikler.json` kimlikleridir. "Faz 1" =
tabloda bugün var; "ek" = §16.1'de önerilen eklemeli sütun.

| Kategori | Sütun(lar) | Değer kaynağı | Liste biçimi | Sayım / not |
|---|---|---|---|---|
| **Nesne türü** | `tur`, `alt_tur` (Faz 1) | şema `degerler`; modelde bulunanlar | Çubuk ▸ kolon, kiriş, tali kiriş, aşık, çapraz…; Panel ▸ döşeme, duvar; Düğüm; Mesnet; Temel; Yük | Seçim anahtarı kapalı türler soluk + "anahtar kapalı" ipucu (ray SEÇ bölümü) |
| **Kat** | `kat` (liste, Faz 1) + Kat Verisi (ana kat, benzer) | `akslar.z` kat seviyeleri | Kat satırı iki satırlı: ad + "kot · ana kat / benzer → Kat 2 / temel"; üstte kapsam anahtarı (§9) | Kat aralığını aşan kolon her katında sayılır; toplamda bir kez. "Herhangi bir katı / tüm katları" seçeneği |
| **Kesit** | `kesit` (görünen ad), `profil` (normal ad, Faz 1) | modeldeki kesitler | **aileye göre** gruplu (HEA, IPE, L köşebent, Kutu…); arama `profilAdiNormal` ile ("HE340A" = "HEA 340") | Kesitsiz elemanlar (panel, düğüm) listelenmez |
| **Malzeme** | `malzeme`, `sistem` (Faz 1) | modeldeki malzemeler | sisteme göre gruplu (çelik / betonarme) | — |
| **Kullanım yeri** | `alt_tur` + `kullanim_yeri` (Faz 1) → `kullanim` (ek) | MIMARI §10.3 algoritması | alt türe göre gruplu: Kolon ▸ köşe/kenar/iç; Kiriş ▸ dış/iç/konsol; Döşeme ▸ iç/kenar/konsol; Çapraz ▸ dış cephe/iç; Düğüm ▸ temel/kolon üstü/ara; Cephe ▸ ±X/±Y | Değer bir **çifttir** ("köşe kolon"): türü de içerir; Nesne türü ölçütüyle ayrıca kesişir |
| **Aks** | `aks_x`, `aks_y` (ek; liste) | aks sistemi | X aksları, Y aksları; "kesişim" için kategori başlığında **herhangi biri / hepsi** | Kolon iki aksta birden (A ve 1) sayılır; tolerans 1 cm |
| **Doğrultu** | `dogrultu` (ek; enum: x, y, z, egik) | uç koordinatları; tolerans 1° (ayar) | X'e paralel · Y'ye paralel · Z'ye paralel (düşey) · Eğik | Paneller listelenmez |
| **Düzlem** | `duzlem` (ek; liste) | uçların ortak kotu / aksı | XY · Kat k (+kot); XZ · Aks j; YZ · Aks i | Eleman birden çok düzlemde olabilir (kiriş: XY · Kat 2 ve XZ · Aks 1) |
| **Uzunluk** | `uzunluk` (Faz 1, m) | düğümden düğüme | ≤ 20 farklı değerde **değer listesi** (1 cm yuvarlak: "4,50 m (60)"); fazlasında **histogram + aralık kaydırıcısı** + otomatik kutular | Aralık çipi: "Uzunluk 5,00–7,50 m" |
| **Grup / süzgeç** | `grup` (Faz 1) → `gruplar` (ek; liste) + kayıtlı süzgeçler | `.op4` `secim/` katkısı | "Gruplar" (sabit kimlik listeleri) ve "Süzgeçler" (dinamik; huni simgeli) iki bölüm | Süzgeç sayısı canlı değerlendirilir |
| **Etiket** | `etiketler` (ek; MIMARI §10.6) | eleman etiketleri | düz liste, arama | herhangi biri / hepsi |
| **Yük deseni** | `yuk_desenleri` (ek; liste) | `ek_yukler` kayıtları | desen adı + tür (yayılı/tekil/alan/duvar) alt satırı; "(ek yük yok)" satırı | W/E/K motor üretimidir: soluk, "otomatik" |
| **Mesnet / serbestlik** | `serbest_i`, `serbest_j` (Faz 1), `mesnet_tipi` (ek) | uç serbestlikleri, mesnet ön ayarları | Çubuk ▸ iki ucu mafsal / i ucu mafsal / sürekli / yalnız çekme; Düğüm ▸ ankastre / mafsal / kayıcı / yay / mesnetsiz | — |
| **D/C aralığı** | `dc` (ek; sonuç), `dc[komb]` | son çözüm | 5 eşik (ölçek ayarından): ≤0,50 · 0,50–0,70 · 0,70–0,90 · 0,90–1,00 · >1,00; üstte kombinasyon seçici (belirleyen / belirli) | Çözüm yoksa kategori soluk: "Önce çözün (F5)"; sonuç eskiyse uyarı rozeti |

### 5.2 "+ Özellik ekle…" — herhangi bir süzülebilir özellik

Şemadaki (`oznitelikler.json`) **her** alan bir kategori olarak eklenebilir; liste aranabilir ve şema gruplarına göre
(Kimlik, Kullanım, Konum, Geometri, Kesit ve malzeme, Bağlantı, Yükler, Mesnet ve temel, Sonuç, Metraj, IFC, Kullanıcı)
düzenlidir. Alan türüne göre bileşen otomatik seçilir:

| Şema türü | Bileşen |
|---|---|
| `enum`, `metin` | değer listesi (sayılı); ≥ 12 değerde arama kutusu, ≥ 20 değerde önek/aile gruplaması |
| `sayi` | ≤ 20 farklı değerde değer listesi; değilse histogram + aralık |
| `bool` | evet / hayır / boş (3 satır) |
| `liste` | değer listesi + "herhangi biri / hepsi" |
| `sozluk` (`pset[...]`, `kullanici[...]`) | önce anahtar seçilir, sonra değer listesi |

Eklenen kategori **sabitlenir** (kullanıcı ayarı, `Ayarlar › arayüz`), sürükleyerek sıralanır, sağ tıkla gizlenir.
Hazır 14 kategori de gizlenebilir; varsayılan küme firma profiliyle paylaşılır.

## 6. Sayım mantığı (n / N)

Her değer satırı iki sayı gösterir: **n** kalın, **/ N** soluk.

- **N** = evrende bu değeri taşıyan eleman sayısı (evren: §6.1).
- **n** = bu değer işaretlenirse, **diğer kategorilerin** etkin ölçütleriyle birlikte eşleşecek eleman sayısı
  (yönlü sayım: kendi kategorisi hariç tutulur, böylece aynı kategoride "veya" ile eklenecek katkı görünür).

Biçimsel: etkin ölçütler `C = {k → V_k}`; eleman `e` için `uyar_k(e) = (değerler_k(e) ∩ V_k ≠ ∅)`.
`n(k, v) = |{ e ∈ E : v ∈ değerler_k(e) ∧ ⋀_{j≠k} uyar_j(e) }|`. Sonuç kutusundaki toplam
`|{ e ∈ E : ⋀_k uyar_k(e) }|`'dir (her eleman bir kez).

Örnek (görsel 1, ölçütler Kat = {Kat 2}): HE340A **20** / 60 · IPE400 **31** / 93 · IPE200 **12** / 60 · L100x10 **8** / 24 ·
KUTU 80x4 **0** / 4. HE340A + IPE400 işaretli → 51 (20 kolon · 31 kiriş). L100x10 üzerinde: "+8 çapraz → 59".

Kurallar:
- n = 0 olan satır soluk yazılır ama **seçilebilir** (Ekle kipinde anlamlıdır); sıralama "sayıya göre" seçilirse sona
  iner.
- Liste değerli alanlarda (kat, aks, etiket, düzlem) bir eleman birden çok satırda sayılır; grup satırlarında ve sonuç
  kutusunda **tekrarsız** sayılır.
- Grup satırı n'i üyelerinin n toplamı değil, tekrarsız birleşimidir.
- "Yalnız görünenler" açıkken N ve n yalnız görünür elemanlardan sayılır (gizli/yalıtık dışı).
- Sonuç kategorisi (D/C) sonuç eskiyse sayılar soluk + "eski" rozeti taşır; seçim yine yapılır.

### 6.1 Evren

`E` = seçilebilir elemanlar: ray SEÇ bölümündeki **seçim anahtarları** açık türler ∩ (Yalnız görünenler ise görünür
olanlar). Kat kapsamı evreni daraltmaz; Kat ölçütünü üretir (§9) ve bu yüzden çip olarak görünür.

## 7. Birleştirme anlamı ve çipler

### 7.1 Kural

| Durum | Anlam |
|---|---|
| Aynı kategoride birden çok değer | **veya** (birleşim): "HE340A **veya** IPE400" |
| Farklı kategoriler | **ve** (kesişim): "Kat 2 **ve** (HE340A veya IPE400)" |
| Liste değerli alan, varsayılan | eleman listesindeki **herhangi bir** değer işaretliyse uyar |
| Liste değerli alan, "hepsi" | işaretli değerlerin **hepsini** taşıyan eleman uyar (ör. Aks A **ve** Aks 1 → A/1 kolonu) |
| Hiç ölçüt yok | seçime dokunulmaz (§4) |

Bu kural tek ve sabittir; pratik katmanda "ve/veya" seçilmez. Farklı bir bileşim (ör. "Kat 2 kolonları **veya** Kat 3
kirişleri") Gelişmiş'tedir ya da iki adımda Ekle kipiyle yapılır.

### 7.2 Çipler

- Çip = `kategori adı (soluk, 10 px)` + `değerler (600)` + `×`. Değerler "veya" ile yazılır; 3'ten fazlası
  "HE340A, IPE400 +3" biçiminde kısalır, ipucunda tamamı görünür.
- Çipler arasında soluk **"ve"** yazılır. Satır sığmazsa çip bir alt satıra kayar, satır başı yine "ve" ile başlar.
- Kat kapsamından üretilen Kat çipi kapsamı yazar: "Kat 1, 2, 3 (benzer)" (görsel 2); elle düzenlenirse "(özel)".
- Sonuç kutusu çiplerin hemen altındadır: "**n eleman eşleşiyor → <kip>: m**" ve tür dağılımı ("20 kolon · 31 kiriş").

### 7.3 Çipten sorgu metnine (MIMARI §11.3 dilbilgisi)

| Çip | Sorgu metni |
|---|---|
| Kat 2 | `kat içinde [2]` |
| Kat 1, 2, 3 (benzer) | `kat kapsamda` (kayıtta) / `kat içinde [1, 2, 3]` (anlık) — bkz. §14.5 |
| Kesit HE340A veya IPE400 | `kesit içinde [HE340A, IPE400]` (normalleştirilmiş) |
| Kullanım yeri köşe kolon | `kullanim içinde [kolon.kose]` (ek alan `kullanim`) |
| Aks A ve 1 (hepsi) | `aks hepsi [A, 1]` (ek işleç; yoksa `aks içerir A ve aks içerir 1`) |
| Uzunluk 5,00–7,50 m | `uzunluk arasında 5 m ile 7,5 m` |
| D/C 0,90–1,00 veya > 1,00 | `dc > 0.9` (bitişik aralıklar birleştirilir) |
| Süzgeç "Dış kirişler" | `süzgeç = "Dış kirişler"` (ek; döngü denetimli) |

Bütün çiplerin bileşimi `… ve … ve …` olur; Gelişmiş bu metni gösterir ve düzenletir (§14).

## 8. Kipler ve taban seçim

| Kip | Sonuç seçim | S7 `SecimKipi` |
|---|---|---|
| **Yeni seçim** (varsayılan) | `R` | `Yeni` |
| **Ekle** | `S₀ ∪ R` | `Ekle` |
| **Çıkar** | `S₀ ∖ R` | `Cikar` |
| **Kesişim** | `S₀ ∩ R` ("seçim içinde süz") | `IcindeSuz` |

- `R` = eşleşen küme, `S₀` = **taban seçim**: panel açıldığı anda, ya da seçim panel dışından (görünümde tık, ağaç,
  komut) değiştiği anda alınan anlık görüntü. Her işaretleme sonucu `S₀`'dan **yeniden** hesaplar; böylece
  işaretleme/kaldırma ve kip değiştirme birikmez, her an tutarlıdır ("Ekle"de bir kesiti kaldırınca yalnız onun katkısı
  gider).
- Kip değişimi aynı `S₀` ve `R` ile sonucu anında yeniden üretir.
- Panel kapanınca ya da **Temizle** ile ölçütler boşalınca seçim olduğu gibi kalır; `S₀` bırakılır.
- Sonuç kutusu kipe göre yazılır: "→ yeni seçim: 51" · "→ seçime eklenecek: +45 (6 → 51)" · "→ çıkarılacak: −6" ·
  "→ kesişim: 6".
- Değiştiriciler (Ctrl/Shift+tık) yalnız o satırın katkısını geçici kiple uygular ve `S₀`'ı yeniler (tek seferlik
  işlem, sonraki tık yine paneldeki kiple çalışır).

## 9. Kat kapsamı tümleşimi

- Durum çubuğundaki **Bu kat / Benzer katlar / Tüm katlar** anahtarı (ilke 11; Alt+1/2/3) ile Kat kategorisinin başındaki
  anahtar **aynı durumdur** (görsel 2).
- Kapsam **Kat çipini üretir**:
  - **Bu kat** → `[etkin kat]` (plan görünümünde planın katı; 3B'de "Etkin kat" açılır listesi, durum çubuğunda yazar).
  - **Benzer katlar** → etkin katın ana katı + Kat Verisi'nde ona "benzer" katlar (ana kat başka kata benzer olamaz;
    "Yok" seçilen kat dışarıda — görselde Zemin).
  - **Tüm katlar** → `[1 … n]`, **zemin/temel seviyesi hariç** (ilke 11).
- Panel açıldığında Kat çipi kapsamdan **otomatik** gelir (kapsam varsayılan olarak her işlemde geçerlidir). Kullanıcı
  çipi silerse evren tüm modeldir ("Kat ölçütü yok"); durum çubuğu anahtarı değişmez.
- Kat listesinde elle işaretleme kapsamı **"Özel"** yapar: durum çubuğu anahtarında hiçbir parça seçili görünmez, yanında
  "Özel: Kat 1, 3" yazar; Alt+1/2/3 yeniden bağlar.
- Kapsam değişince (Alt+2) Kat çipi yeniden üretilir ve sonuç yeniden hesaplanır; komut geçmişine "KAPSAM Bu kat →
  Benzer katlar · Kat ölçütü yeniden üretildi" yazılır.
- Sağ tık menüsündeki "Bu kesittekileri / kullanım yerindekileri / akstakileri seç" kapsamı uygular (sayılar kapsam
  içindedir; görsel 4'te Tüm katlar: IPE400 93, Aks A 39 — Zemin'deki 5 temel hariç). "**Bu kattakileri seç**" açık bir
  kat seçimidir, kapsamı aşar (yalnız o kat).
- Benzer katlarda **aynı plan konumu** (A programının benzer kat seçimi): Benzerini seç ayarlarında "Aynı plan konumu
  (benzer katlarda)" seçeneği; tık seçimi o elemanın benzer katlardaki aynı x–y konumundaki aynı tür eşlerini ekler
  (tolerans 1 cm). Ölçüt olarak `plan_konumu` (ek) çipi üretir: "Plan konumu = B/2".

## 10. Hızlı eylemler

| Eylem | Kısayol | Tanım |
|---|---|---|
| **Tümü** | Ctrl+A | Evrendeki (seçim anahtarları + görünür) tüm elemanlar; kat kapsamı çipi varsa onunla kesişir. "Tümü" seçici bir ölçüt eklemez. |
| **Tersine çevir** | Ctrl+Shift+I (takma: Ctrl+K) | `E ∖ S`; Kat çipi varsa yalnız o katlarda tersler. |
| **Önceki seçim** | Ctrl+J | Seçim geçmişi (son 16 anlık görüntü, oturum içi; seçim geri al kapsamında değildir — MIMARI §9.4). Ardışık basış daha geriye gider. |
| **Temizle** | Esc (komut ve açılır liste yokken) · Ctrl+Shift+A | Seçimi boşaltır; panel ölçütleri kalır (çiplerden "Temizle" ayrı). |
| **Benzerini seç** | Ctrl+B | Seçili elemanların **ortak değerlerini** çip yapar ve uygular. Varsayılan ölçütler **alt tür + kesit**; ayarlar (düğmenin ▾'i): + malzeme, kullanım yeri, kat, uzunluk ±1 cm, aynı plan konumu (benzer katlarda). Kat kapsamı uygulanır. Seçim boşsa soluk ("önce bir eleman seçin"). |
| **Yalnız seçiliyi göster** | Ctrl+5 | Diğer elemanlar %85 saydam (render modu, ilke 22–23); düğme basılı kalır, tekrar basınca kapanır. |
| **Seçimi grup olarak kaydet…** | Ctrl+G | Küçük kart: ad, tür = **Sabit grup** (kimlik listesi; silinen elemanlar düşer) ya da **Süzgeç** (mevcut çiplerden dinamik); "Grup / süzgeç" kategorisinde ve ağaçta görünür. |

Not: "Benzerini seç" ile çiplerin kurulması, M ve A yaklaşımlarının **köprüsüdür**: kullanıcı bir örnek eleman gösterir,
panel ölçütleri yazar, kullanıcı çipleri düzeltir.

## 11. Klavye kısayolları

| Kısayol | Kapsam | İşlev |
|---|---|---|
| **Ctrl+F** | genel | Seç & Süz panelini aç / arama kutusuna odak |
| **Ctrl+Shift+F** | panel | Gelişmiş aç/kapa |
| Ctrl+A | genel | Tümünü seç (§10) |
| **Ctrl+Shift+I** · Ctrl+K | genel | Tersine çevir |
| Ctrl+J | genel | Önceki seçim |
| Esc · Ctrl+Shift+A | genel | Seçimi temizle (Esc sırası: açık liste → etkin komut → seçim) |
| Ctrl+B | genel | Benzerini seç |
| Ctrl+5 | genel | Yalnız seçiliyi göster |
| Ctrl+G | genel | Seçimi grup olarak kaydet |
| Alt+1 / Alt+2 / Alt+3 | genel | Kat kapsamı (ilke 11) |
| Tab / Shift+Tab | panel | Bölge değiştir: kip → çipler → kategoriler → liste → hızlı eylemler |
| ↑ ↓ | panel | Kategori ya da değer satırında gez |
| ← → | panel | Kategori sütunu ↔ değer listesi; kip anahtarında kip değiştir |
| Boşluk | panel | Satırı işaretle (Ctrl+Boşluk: ekle, Shift+Boşluk: çıkar) |
| Harf yazmak | panel listesi | Arama kutusuna yazar (tür-öncesi arama) |
| Delete | çip odakta | Ölçütü kaldır |
| Enter | panel | Anında uygula kapalıysa: Seç; Gelişmiş'te ad alanında: süzgeç olarak kaydet |
| Tab / Enter / Esc | atama komutu | Hedef isteminde sonraki ölçüt / uygula / iptal (§13) |

Çakışma notları (kullanıcı onayı, §20): ilke 10 "Temizle = Ctrl+Q" önerir, fakat op4'te **Ctrl+Q hızlı başlattır**
(ilke 3, `komutlar.json`) — Temizle bu yüzden Esc / Ctrl+Shift+A'dır. Ctrl+S dosya kaydıdır; panelde süzgeç kaydı
Ctrl+S kullanmaz. `komutlar.json`'da **Alt+1…4 görünüm (3B/Plan/Ön/Yan)**, MIMARI §25'te **Alt+1/2/3 kat kapsamı**dır:
çakışma çözülmelidir (öneri: görünümler Ctrl+Alt+1…4).

## 12. Şerit menüsü ve sağ tık

### 12.1 Şerit — Model › Seç grubu (görsel 4 ①)

- **Seç** büyük düğmesi **bölünmüştür**: üst yarı seçim aracını etkinleştirir; alt yarı (▾) menüyü açar.
- Menü başlığı: "ÖLÇÜTE GÖRE SEÇ — PANELİ O ÖLÇÜTTE AÇAR". Satırlar: Türe göre ▸, Kata göre ▸, Kesite göre ▸,
  Malzemeye göre ▸, Kullanım yerine göre ▸, Aksa göre ▸, Doğrultuya göre (X / Y / Z) ▸, Düzleme göre (XY / XZ / YZ) ▸,
  Uzunluk aralığına göre…, Gruba / süzgece göre ▸, Etikete göre ▸, Yük desenine göre ▸, Mesnet / serbestliğe göre ▸,
  D/C aralığına göre ▸; ayraç; Tümünü seç, Tersine çevir, Önceki seçim, Seçimi temizle, Benzerini seç (kısayollarıyla);
  ayraç; Seç & Süz paneli… (Ctrl+F); altta neden metni ("Benzerini seç: önce bir eleman seçin").
- **Alt menü** (▸): başlık "KAPSAM: <kat kapsamı> · TIK: YENİ SEÇİM"; değerler simgesi ve **N sayısıyla**
  (HE340A 60 · IPE400 93 · IPE200 60 · L100x10 24 · KUTU 80x4 4); en altta "Panelde aç: Kesit…" ve
  "Ctrl+tık: ekle · Shift+tık: çıkar". 30'dan fazla değerde alt menü arama kutusuyla açılır ve ilk 30'u gösterir.
- Menü satırına tık (▸ dışı) paneli o kategoride açar; alt menü değerine tık panel açmadan seçer ve komut geçmişine
  `SEÇ kesit = IPE400 → 93` yazar.
- Aynı menü Seç grubundaki **Kata göre ▾** küçük düğmesinde yalnız kat listesi olarak vardır.

### 12.2 Elemana sağ tık (görsel 4 ②)

- Başlık: "Kiriş K2-A23 · IPE400 · Kat 2" + alt satır "dış kiriş · Aks A · 2–3 · 6,00 m · benzer: 93".
- **Benzerini seç** (Ctrl+B) en üstte.
- "BUNA GÖRE SEÇ": **Bu kesittekileri seç** (IPE400 · 93) · **Bu kattakileri seç** (Kat 2 · 72) · **Bu kullanım
  yerindekileri seç** (dış kiriş · 42) · **Bu akstakileri seç** (Aks A · 39) · **Bu gruptakileri seç ▸**. Sağda değer
  ve sayı; sayılar kat kapsamı içindedir (§9).
- **Seç & Süz'de aç (ölçütleri doldur)** — elemanın kesit, kat, kullanım yeri değerlerini çip yapar, kip Yeni.
- Ayraçtan sonra Özellikler, Yalnız bunu göster (Ctrl+5), Gizle, Sil (Del); en altta kapsam notu.
- Çoklu seçimde sağ tık: başlık "6 eleman (Kiriş ×6)"; "BUNA GÖRE SEÇ" ortak değerleri kullanır; ortak olmayan ölçüt
  satırı soluk ("kesit farklı").
- Değiştiriciler burada da geçerlidir: Ctrl+tık Ekle, Shift+tık Çıkar.

## 13. Atama komutlarıyla tümleşim (Yük ata, Mesnet ata, Kesit ata…)

Komut akışı (MIMARI §11.6–§11.7, ilke 18–19): komut başlar → özellikleri **Özellikler** penceresinde (yük deseni, tür,
değer, yön, kip Ekle / Değiştir / Sil) → **Hedef** verilir → önizleme → Enter uygular (**tek geri al adımı**).

### 13.1 Hedef istemi (görsel 5)

- **Komut satırında** komut adının yanında seçenek pilleri: `YÜKATA  Hedef: [Seçim] [Kat] [Kesit] [Kullanım yeri]
  [Grup] [Süzgeç] | [Seç & Süz…]`. Değeri verilmiş pil değeriyle yazılır ("Kat: benzer (1–3)", "Kullanım yeri: dış
  kiriş"); etkin pil `vurgu` dolguludur.
- Pile tık (ya da Tab ile gelip Enter) pilin üstünde **aynı değer listesi bileşenini** açar (Seç & Süz'deki liste:
  gruplu, n / N sayılı, ↑↓ / Boşluk / Enter). Komut satırına yazmak da çalışır: `kat benzer`, `kullanim dis`,
  `kesit IPE400`, `:sorgu …`.
- **Özellikler** penceresinde "Hedef" bölümü aynı ölçütleri çip olarak gösterir ("Kat 1, 2, 3 · benzer ve Kullanım yeri
  dış kiriş"), altında hızlı ekleme pilleri (+ Seçim, + Kat, + Kesit, + Kullanım yeri, + Grup, + Süzgeç) ve **sonuç
  kutusu**: "42 kiriş · 3 kat · 42 yük kaydı", kat dağılımı, uyarılar ("Önceki G yükü olan 14 kiriş: Ekle → toplanır").
- **Seçim** pili: komut başladığında seçim varsa hedef varsayılan olarak seçimdir (pil işaretli gelir); yoksa Kat pili
  kat kapsamından dolu gelir ve kullanıcı ölçüt ekler ya da görünümde elemanlara tıklar (tık = Seçim ölçütüne ekle).
- **Önizleme**: hedef elemanlar `seçim` konturuyla, yük okları (yayılı yükte eleman başına 5 ok + üst çizgi, `vurgu`
  %80) görünümde; ağaçta katlarda "14" rozetleri, kullanım yeri düğümünde "14 hedef".
- **Uygula (Enter)**: kayıtlar `BC.yukEkle` ile tek işlemde yazılır; komut geçmişine hedef sorgusu metniyle düşer
  (`HEDEF kat içinde benzer(Kat 2) ve kullanım yeri = dış kiriş → 42 kiriş`).
- **Hedefi süzgeç olarak kaydet**: hedef ölçütleri "Dış kirişler" adıyla kaydedilir; sonraki atamalarda Süzgeç pilinden
  tek tıkla gelir. Yazılan kayıtlar elemana bağlıdır (süzgeç yeniden değerlendirilmez); süzgeç yalnız hedef seçimini
  hızlandırır.

### 13.2 Komut başına varsayılan ölçütler

| Komut | İstemde öne çıkan ölçütler | Ek hazır hedefler |
|---|---|---|
| YÜKATA (çubuk / alan / düğüm / duvar) | Kat · Kesit · Kullanım yeri · Grup · Süzgeç | "2–5. kat döşemeleri", "çatı aşıkları", "dış kirişler" (MIMARI §11.6 örnekleri) |
| MESNETATA, TEMEL | Kat (varsayılan: en alt seviye) · Kullanım yeri (düğüm: temel / kolon üstü) | "En alt seviyedeki bütün düğümler", "kolon alt uçları" (MIMARI §11.7) |
| KESİTATA | Kesit · Kullanım yeri · Kat | "Benzerini seç" sonucu |
| SERBESTLİK (uç serbestliği) | Nesne türü · Doğrultu · Aks | "Y'ye paralel tali kirişler" |
| GRUPATA / ETİKETATA | Seçim · Süzgeç | — |
| Çizim komutları (Kat kopyala, Çoğalt) | Kat kapsamı (hedef katlar) | — |

Kat kapsamı her atamada uygulanır ve durum çubuğu "3 katta uygulanacak" yazar (ilke 11).

## 14. Gelişmiş katman (görsel 3)

### 14.1 Açılış: çiplerden satıra

- **Gelişmiş** anahtarı (Ctrl+Shift+F) açılınca gövde (kategori sütunu + liste) yerine **kural kartı** gelir; kip, çip
  başlığı ("ÖLÇÜTLER → KURAL SATIRLARI") ve sonuç kutusu yerinde kalır.
- Her çip bir satır olur: `[Alan ▾] [İşleç ▾] [Değer ▾] [sil]`. "Kat 2" → `Kat · içinde · Kat 2`; "Kesit HE340A veya
  IPE400" → `Kesit · içinde · HE340A, IPE400`. Satırlar arasında soluk "ve". Üstte **Eşleşme: [Tümü sağlansın (ve) ▾]**
  ve "çiplerden üretildi" notu (damlalık simgesi = "seçimden yeniden üret").
- **Değer** alanı pratik katmandaki **aynı listeyi** açılır kart olarak açar (n / N sayılı, aranabilir).

### 14.2 Ek koşullar

| Alan türü | İşleçler | Değer bileşeni |
|---|---|---|
| sayı (birimli) | = ≠ < ≤ > ≥ · arasında | sayı kutusu + birim kutusu ("5,00" [m]); altında **histogram** (eşleşenlerin dağılımı, eşik çizgisi, "geçen 31 · elenen 20") |
| metin | = ≠ · içerir · ile başlar · `~` joker (`IPE*`) | metin kutusu + öneri listesi |
| enum / liste | içinde · içinde değil · (liste) hepsi | değer listesi |
| her tür | boş · dolu (`yok` / `var`) | değer alanı gizlenir |
| indisli (`dc[komb]`, `pset[...]`) | alanın türüne göre | önce indis seçici |

Yeni eklenen satır `vurgu_ton` zemin + sol `vurgu` şeritle 2 sn işaretlenir; görsel 3'te "Uzunluk > 5,00 m" 20 kolonu
(4,50 m) eler → 31 kiriş.

### 14.3 Gruplama (tek düzey)

- Üst düzey bağlaç **Tümü sağlansın (ve)** ya da **Herhangi biri (veya)**.
- **+ Veya grubu** (üst düzey "ve" iken) bir kutu açar; içindeki satırlar "veya" ile bağlanır. Üst düzey "veya" iken
  düğme **+ Ve grubu** olur. Grubun içinde grup açılamaz (iki düzey: VE-of-VEYA ya da VEYA-of-VE).
- Daha derin ifade sorgu metninde yazılabilir; o zaman satır görünümü "Sorgu metninde düzenleyin (3 düzey)" der ve
  satırlar salt okunur olur.

### 14.4 İki yönlü sorgu metni

- Kartın altında **SORGU METNİ · İKİ YÖNLÜ** kutusu: `kat içinde [2] ve kesit içinde [HE340A, IPE400] ve uzunluk > 5 m`.
  Satır değişince metin, metin değişince (300 ms sonra ya da Enter) satırlar güncellenir.
- Hatalı metin öğretici iletiyle konumu gösterir (MIMARI §11.3): "3. sözcük: 'kesitt' alanı yok; 'kesit' mi demek
  istediniz?" — satırlar son geçerli halde kalır.

### 14.5 Gelişmiş'ten pratiğe dönüş

- Gelişmiş kapatılınca çipe çevrilebilen her satır (`alan içinde [değerler]`, üst düzey "ve", pratik kategorisi olan
  alan) yeniden çip olur.
- Çevrilemeyenler (sayısal karşılaştırma, metin içerir, boş/dolu, veya grubu) **tek bir çipte** toplanır: "Gelişmiş: 1
  koşul" (çipe tık Gelişmiş'i açar). Hiçbir koşul kaybolmaz; pratik listelerde işaretleme bu çiple "ve" bağlanır.
- Kat kapsamından gelen çip kayıtta iki biçimde saklanabilir: **sabit** (`kat içinde [1, 2, 3]`) ya da **kapsamı izle**
  (`kat kapsamda`, ek anahtar sözcük). Varsayılan: sabit; kaydetme kartında "Kat kapsamını izle" onay kutusu.

### 14.6 Süzgeç olarak kaydet

- Kart: **Ad** (odakta), kullanım onayları: ☑ **Seçim süzgeci** ("Grup / süzgeç" kategorisinde ve ağaçta "Süzgeçler"
  altında), ☐ **Görünüm süzgeci** (Görünürlük penceresinde; eşleşmeyenler %85 saydam ya da gizli), ☐ **Renk kuralı**
  (eşleşenler tek renk; renk seçici açılır). Birincil düğme **Süzgeç olarak kaydet**, ikincil **.filtre dışa aktar…**.
- Süzgeç = sorgu metni + ad + kullanım bayrakları + oluşturma tarihi; **dinamiktir** (her kullanımda yeniden
  değerlendirilir), `.op4` içinde `secim/suzgecler.json`'da saklanır (C katkısı, S24 kural 5). `.filtre` (JSON) firma
  profiliyle paylaşılır; içe aktarılınca alan adları şemaya göre denetlenir.
- Kayıtlı süzgeçler listesi kartın altında sayılarıyla ("IPE400 kirişler – Kat 2 · seçim · 31").

## 15. Boş model ve büyük model davranışı

### 15.1 Boş model / boş durum

- Seçilebilir eleman yoksa gövdede boş durum: simge + "Modelde seçilebilir eleman yok" + bağlantılar **Hızlı aks…**,
  **Şablondan yeni…** (MIMARI §5.2 Başlangıç paneli); kip ve hızlı eylemler soluk.
- Kategoride değer yoksa satır soluk, sağda "—"; tıklanınca liste "Bu modelde kesit tanımlı değil" der.
- D/C: çözüm yoksa kategori soluk, liste yerine "Önce çözün (F5)" düğmesi; sonuç eskiyse "eski" rozeti.
- Seçim anahtarı kapalı türler (ör. düğüm) Nesne türü listesinde soluk + "anahtar kapalı — ray › SEÇ" ipucu; tıklamak
  anahtarı açmayı önerir.
- Özellikler penceresi seçim yokken "Seçim yok" boş durumunu ve Seç & Süz / Önceki seçim (n eleman) / Tümünü seç
  kısayollarını gösterir (görsel 4).

### 15.2 Büyük model (100 bin eleman, 500+ kesit, 1000+ etiket)

- **Sanal listeler**: değer listesi ve kategori listesi `ImGuiListClipper` ile çizilir; yalnız görünen satırlar
  hesaplanır. 100 bin değerli liste de akıcı kaydırılır.
- **Arama kutusu**: 12+ değerde her zaman görünür (Kesit, Grup, Etiket'te sabit); Türkçe harf katlamalı, büyük/küçük
  duyarsız (`turkce.h`), kesitte `profilAdiNormal` ile. Joker `*` ve önek ("IPE 4" → IPE400, IPE450).
- **Gruplama**: 20+ değerde aile/önek grupları otomatik (Kesit: aile; Etiket: "imalat-*" öneki), gruplar kapalı başlar.
- **Sayım motoru**: her (kategori, değer) için eleman **bit kümesi** (satır başına 1 bit; 100 bin satır = 12,5 KB).
  Kategori VEYA maskesi = işaretli değer kümelerinin birleşimi; "kendi hariç" maskeleri **önek/sonek VE** dizileriyle
  O(K) üretilir; `n(k, v) = popcount(küme(v) ∧ hariç_k)`. 100 bin satır × 1000 değer ≈ 1,6 M sözcük işlemi: bir iş
  parçacığında < 5 ms. Gerekirse iş havuzunda; arayüz sonuç gelene kadar eski sayıları soluk gösterir ("sayılıyor…").
- **Önbellek**: bit kümeleri `OznitelikTablosu`nun `sahneSurumu` ile anahtarlanır; tablo değişmezdir (S5), yeni
  sürümde yeniden kurulur. Sayısal alanların histogramı (64 kutu) aynı anda üretilir.
- **Seçim uygulama**: `S₀` ve `R` sıralı kimlik dizileri; birleşim/fark/kesişim doğrusal birleştirme (O(|S₀|+|R|)).
  Görünüm vurgu tamponu yalnız `Secim::Surum()` değişince yenilenir (S7).
- **Önizleme** (satır üzerinde) 60 ms gecikmeli başlar, imleç başka satıra geçince iptal edilir; 20 binden fazla eleman
  önizlemesi yalnız sayı gösterir, kontur çizmez.
- **Çok uzun çip değerleri**: "HE340A, IPE400 +38"; çip ipucu tam listeyi sanal listeyle gösterir.

## 16. S5 ve S7 sözleşmeleriyle eşleme

### 16.1 S5 — öznitelik tablosu (`oznitelik.h`, `oznitelikler.json`)

- Kategoriler **şemadan** kurulur: kategori = şema kaydı (`id`, `ad`, `tur`, `birim`, `esanlamlilar`, `grup`); liste
  değerleri sütunun `sozluk`'ünden (enum/metin) ya da sayı dizisinden; sayımlar sütun dizileri üstünde (`kod[satir]`,
  `sayi[satir]`, `listeBas/listeDeger`). Değer gösterimi `OznitelikTablosu::Gosterim` ile (ondalık virgül, birim).
- Faz 1'de var olanlar yeterlidir: Nesne türü (`tur`, `alt_tur`), Kat (`kat`), Kesit (`kesit`, `profil`), Malzeme
  (`malzeme`, `sistem`), Kullanım yeri (`alt_tur` + `kullanim_yeri`), Grup (`grup`), Uzunluk (`uzunluk`), Mesnet /
  serbestlik (`serbest_i`, `serbest_j`), konum (`x`, `y`, `z`).
- Önerilen **eklemeli** sütunlar (kural: yalnız eklenir, `id` değişmez; `faz: 3`):

| id | tür | kaynak | not |
|---|---|---|---|
| `kullanim` | enum | türetilmiş | `alt_tur.kullanim_yeri` ("kolon.kose") — Kullanım yeri tek sütunla süzülsün |
| `dogrultu` | enum | türetilmiş | x / y / z / egik (uç koordinatlarından; tolerans ayarı) |
| `aks_x`, `aks_y` | liste | türetilmiş | üstünde bulunduğu akslar (MIMARI §11.2 Konum) |
| `duzlem` | liste | türetilmiş | "xy:k", "xz:aks", "yz:aks" anahtarları |
| `plan_konumu` | metin | türetilmiş | "B/2" (benzer katlarda aynı konum için) |
| `gruplar` | liste | model | çoklu grup üyeliği (Faz 1 `grup` tek değerlidir) |
| `etiketler` | liste | model | MIMARI §10.6 |
| `yuk_desenleri` | liste | model | ek yük kayıtlarının desenleri |
| `mesnet_tipi` | enum | model | ankastre / mafsal / kayici / yay / ozel / yok |
| `dc` | sayı | sonuç | belirleyen D/C; `dc[komb]` indisli |

- Gelişmiş ve sorgu dili alan adlarını `id`, `ad` ve `esanlamlilar` ile eşler (Türkçe katlamalı).

### 16.2 S7 — seçim (`secim.h`)

- Panelin her uygulaması **tek** `Secim::Uygula(kume, SecimKipi::Yeni)` çağrısıdır; `kume` paneldeki `S₀`/`R`/kip'ten
  hesaplanmış sonuçtur. Böylece `degisti` olayı **bir kez** yayınlanır ve `Surum` bir artar (ara durum yayınlanmaz).
  (Kipler §8'deki tabloya göre `Ekle / Cikar / IcindeSuz` ile de birebir eşlenir; tek çağrı tercih nedeni `S₀`'dan
  yeniden hesaplamanın birikmeyi önlemesidir.)
- `Tersle` (simetrik fark) yalnız seçim döngüsü/gezgin içindir; **Tersine çevir** `E ∖ S` olarak hesaplanıp `Yeni`
  ile uygulanır.
- `Ayikla` (silinen elemanlar) panel `S₀`'ını da ayıklar.
- Önerilen eklemeli API: `SecimGecmisi` (son 16 anlık görüntü; `Ekle(liste)`, `Onceki()`, `Sonraki()`) — Önceki seçim
  (Ctrl+J) için; seçim geri al kapsamına girmez (MIMARI §9.4).
- Önizleme konturu için S9'a eklemeli alan: `GorunumDurumu::onizlemeKumesi` (kimlik listesi + sürüm); çizici `hover`
  konturuyla çizer.

## 17. Dear ImGui uygulama notları

| Parça | Uygulama |
|---|---|
| Pencere | Sağ panel iskeletinde (`PENCERELER`) bir pencere: `BeginChild("SecSuz")`; pencere şeridinde dikey düğme (Atölye §10) |
| Kip anahtarı | Özel `Parcali()` bileşeni (durum çubuğundaki kat kapsamıyla aynı kod); ←/→ ile gezinme `ImGuiNavInput` |
| Çipler | Özel `OlcutCipi()`: `ImDrawList::AddRectFilled` (yarıçap = yükseklik/2), metin `AddText` iki ağırlıkta; `×` için `InvisibleButton`; satır sonu kaydırması `CalcTextSize` toplamıyla elle; çip `Selectable` gibi odak alır (Delete) |
| Sonuç kutusu | `BeginGroup` + elle çizim; sayı değişince 150 ms sayaç geçişi (isteğe bağlı) |
| Kategori sütunu | `BeginChild` (160 px, kenarlıksız) + satır başına `Selectable` (`SpanAvailWidth`) ve özel çizim (simge yolu, rozet) |
| Değer listesi | `BeginChild` + `ImGuiListClipper`; satır = `InvisibleButton` + özel üç durumlu onay (`AddRectFilled` + onay yolu); sağa hizalı sayılar `CalcTextSize`; `IsItemHovered` → önizleme isteği (gecikmeli); değiştirici tuşlar `io.KeyCtrl/KeyShift`; tür-öncesi arama `io.InputQueueCharacters` → arama kutusuna |
| Arama kutusu | `InputTextWithHint`, Türkçe katlama `turkce.h`; joker eşleme çekirdekte |
| Histogram / aralık | `ImDrawList` sütunları + iki tutamaç `InvisibleButton` (`IsItemActive` + `GetMouseDragDelta`); değer kutusu `InputText` (ondalık virgül, `turkce.h` sayı okuma) |
| Kural satırları (Gelişmiş) | `BeginTable` 4 sütun (alan 96 · işleç 70 · değer esnek · sil 22); açılır listeler özel `BeginPopup` (değer listesi bileşenini yeniden kullanır); veya grubu = girintili `BeginGroup` + kenar çizgisi |
| Sorgu metni | `InputTextMultiline` + 300 ms gecikmeli ayrıştırma; hata konumu `AddUnderline` (kırmızı dalga yerine düz çizgi) ve ipucu |
| Şerit bölünmüş düğme | Şerit bileşeninde `Bolunmus` düğme türü (JSON: `"tur": "bolunmus", "menu": "secim.olcut_menusu"`); üst/alt yarı ayrı `InvisibleButton` |
| Menüler | `BeginPopup` + özel satır çizimi (simge · metin · sağda kısayol rozeti ya da sayı · ▸); alt menüler `BeginMenu` yerine kendi popup'ı (sayıları tembel hesap); sağ tık `BeginPopupContextVoid` + görünüm seçme isabeti (S8 `EnYakin`) |
| Komut satırı seçenek pilleri | Komut satırı bileşenine "seçenek" listesi (S20 komut kataloğuna `secenekler` alanı, eklemeli); pil = `Button` stili özel çizim; açılır liste komut satırının üstünde `SetNextWindowPos` ile |
| İş parçacığı | Sayım ve eşleşme işleri iş havuzunda değişmez tablo üstünde (S24 kural 3); sonuç UI iş parçacığına kuyrukla döner; seçim yalnız UI iş parçacığında uygulanır (S24 kural 2) |
| Kimlikler | `PushID(kategori_id)`, `PushID(deger_kodu)` — sözlük kodu kararlıdır |
| Kalıcılık | Panel durumu (etkin kategori, sabitlenen kategoriler, kip, Anında uygula, son 3 bileşim) `Ayarlar › arayüz`; süzgeçler ve gruplar `.op4` `secim/` katkısı |
| Komut kataloğu | Yeni komutlar `komutlar.json`'a: `secim.secsuz` (Ctrl+F), `secim.benzer` (Ctrl+B), `secim.onceki` (Ctrl+J), `secim.ters` (Ctrl+Shift+I, takma Ctrl+K), `secim.temizle` (Ctrl+Shift+A), `secim.grup_kaydet` (Ctrl+G), `secim.yalniz_secili` (Ctrl+5), `secim.olcut_menusu`; mevcut `secim.tumu`, `secim.temizle`, `secim.ters` korunur |
| Sınama | `--senaryo` ile panel durumu kurulup `--test-ekran` görüntüsü alınır (§19) |

## 18. Renk ve tema bağımsızlığı

Bu belge ve uygulama yalnız **belirteç adlarını** kullanır:

| Belirteç | Seç & Süz'deki kullanımı |
|---|---|
| `vurgu` | etkin kip parçası, işaretli onay kutusu, sayı rozetleri, bağlantılar, etkin komut pili, birincil düğme |
| `vurgu_ton`, `vurgu_ton2` | çip zemini/kenarı, değerli pil, yeni eklenen kural satırı, menüde etkin satır |
| `secim`, `secim_ton` | modelde seçim konturu + dolgusu, ağaçta seçili satır, sonuç kutusu |
| `hover` (model) | önizleme konturu ve önizleme etiketi kenarı (seçimden ayrışan nötr koyu) |
| `yuzey`, `yuzey2`, `zemin`, `cizgi`, `cizgi2` | panel, kategori sütunu, ayraçlar |
| `metin`, `metin2`, `metin3` | ad, ikincil, soluk (N sayıları, n = 0 satırlar, ipuçları) |
| `uyari`, `hata`, `ok` | atama uyarıları, hatalı sorgu, başarı |
| D/C ölçeği | D/C aralığı satırlarının renk noktaları |

Taslaklarda geçici olarak nötr yüzeyler + tek soğuk vurgu kullanıldı (`secsuz_uret.py` başındaki `PALET`); yeni palet
gelince yalnız o sözlük değişir ve görseller yeniden üretilir.

## 19. Kabul ölçütleri ve sınamalar

Örnek modelde (Depo Binası – Tokat OSB şablonu) şu sonuçlar birebir tutmalı (taslaklardaki sayılar):

| Senaryo | Beklenen |
|---|---|
| Kat = Kat 2, Kesit = HE340A veya IPE400 | 51 (20 kolon · 31 kiriş); Kesit n/N: 20/60, 31/93, 12/60, 8/24, 0/4 |
| Kat 2 ve IPE400 | 31 kiriş |
| Kapsam Benzer katlar (ana Kat 2; Kat 1, 3 benzer; Zemin Yok) + köşe kolon | 12 kolon; Kat n/N: 4/87, 4/72, 4/84, 0/20 |
| + Uzunluk > 5,00 m | 31 kiriş (20 kolon elenir) |
| Kapsam Benzer + dış kiriş (YÜKATA hedefi) | 42 kiriş, 42 yük kaydı, tek geri al adımı |
| Tüm katlar (Zemin hariç) + Aks A | 39 (15 kolon · 12 kiriş · 12 çapraz) |

Birim sınamaları (C++ çekirdek, Linux CI): yönlü sayım (`n` kendi kategorisini hariç tutar), liste değerli "herhangi /
hepsi", kip cebiri (`S₀` ile birikmesizlik: işaretle → kaldır → aynı seçim), Gelişmiş ↔ çip gidiş-dönüşü kayıpsız,
sorgu metni ↔ satır gidiş-dönüşü, 100 bin satırda sayım < 16 ms (ölçüm, `OP4OLCUM`). Ekran sınaması: `--test-ekran`
görüntüleri bu taslaklarla gözle karşılaştırılır (MIMARI §25 kabul ilkesi).

## 20. Açık sorular (kullanıcı onayı)

**Kararlar (31.10.2026, kullanıcı):** 1 ve 2 onaylandı — Alt+1/2/3 kat kapsamı (Bu kat / Benzer katlar / Tüm katlar),
görünümler Ctrl+Alt+1…4 (3B / Plan / Ön / Yan); Seçimi temizle Esc + Ctrl+Shift+A (Ctrl+Q hızlı başlat olarak kalır).
3–6 açık; önerilen varsayılanlarla uygulanır.

1. **Alt+1…4 çakışması**: `komutlar.json` görünümleri (3B/Plan/Ön/Yan) ile kat kapsamı (Alt+1/2/3) — öneri: görünümler
   Ctrl+Alt+1…4.
2. **Temizle kısayolu**: ilke 10'daki Ctrl+Q op4'te hızlı başlat; öneri Esc + Ctrl+Shift+A.
3. **Tersine çevir**: Ctrl+Shift+I birincil, Ctrl+K takma ad olarak kalsın mı?
4. **Panel genişliği**: Seç & Süz etkinken sağ panelin 400 px'e genişlemesi (diğer pencerelerde 320).
5. **Kat çipi varsayılanı**: panel açılınca kat kapsamından otomatik Kat çipi gelsin mi (öneri: evet; "kapsam her işlemi
   kapsar" ilkesiyle tutarlı), yoksa yalnız Kat kategorisine girilince mi?
6. **Kayıtta kapsam**: süzgeç kaydında Kat ölçütünün varsayılanı "sabit" mi, "kapsamı izle" mi?

## 21. Üreteç

- `secsuz_uret.py` — beş ekran + karşılaştırma sayfası; `python3 secsuz_uret.py [--yalniz secsuz-pratik,…]`. Ekranlar
  2× çizilip 1920×1080'e indirilir (küçük puntoda harf aralıkları doğru kalsın diye).
- `ozn.py` — sahne modelinden öznitelik tablosu (S5 benzeri) + yönlü sayım motoru (§6); `python3 ozn.py` sayıları
  döker.
- `uret.py`, `tuval.py`, `sahne.py` — Atölye üretecinin kopyaları; `tuval.py`'ye 12 yeni simge (tür, kullanım yeri,
  doğrultu, uzunluk, grup, tümü, geçmiş, silgi, damlalık, kesişim, histogram, kod), `sahne.py`'ye yüklemle seçim kipi
  (`mod="ozel"`, `secim_fn`, `hover_fn`) ve önizleme konturu eklendi.
