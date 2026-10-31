# op4 — Yönetmelik Sihirbazı (tasarım belirtimi, taslak)

Yeni projeye başlamadan önce analiz için **dışarıdan gelen** verileri (malzeme sınıfları, TS 498:2021 yükleri, TBDY 2018
deprem parametreleri, zemin ve temel, yük birleşimleri, analiz seçenekleri) **yönetmelik sırasıyla**, seçimlerle ilerleyen
sekiz adımda toplayan pencere. Değerler bina modeline (`model/bina.json`) yazılır; sonradan **Proje › Yönetmelik
verileri…** ile aynı pencere herhangi bir adımda yeniden açılır (MIMARI §25.1 "Yönetmelik sihirbazı (yeni)").

**Tek doğruluk kaynağı hesap motorudur.** Bu belgedeki alan adları, varsayılanlar, izinli değerler ve doğrulama sınırları
depodaki motorun okuyucusundan alınmıştır: `yapi.py` (`_bina_oku`, `_yuk_durumlarini_oku`, `_spektrum`, `_dts`, `_bys`,
`_deprem_on`, `_kombinasyon_listesi`, `kutuphane`, `deprem_onizleme`), `yapi_veri.py` (bütün tablolar; her kayıt `kaynak`
ve `dogrulandi` taşır), `temel.py` (`oku`, `VARSAYILAN`, `KAYNAK`, sınır sabitleri), `tasarim.py` (çelik YDKT/GKT seçimi),
`docs/bina.js` (bugünkü web arayüzü: Yükler / Deprem / Bina–temel sekmeleri) ve `docs/web_kopru.py` (`bina_kutuphane`,
`bina_deprem`). Motorun bilmediği bir değer sihirbazda **icat edilmez**; emin olunmayan yerler "doğrulanmalı" diye işaretlidir.

| Görsel (1920×1080) | İçerik |
|---|---|
| `sihirbaz-1-proje.png` | Adım 1 — Proje künyesi, yapı türü kartları, ön geometri (H_N tahmini), uygulanacak yönetmelikler; Adım 4 "eksik" |
| `sihirbaz-4-deprem.png` | Adım 4 — TBDY 2018: S_S/S_1 (DD-2, DD-3), zemin sınıfı ZA–ZF, BKS → I, Tablo 4.1 → R, D; hesaplanan S_DS, S_D1, T_A, T_B, DTS, BYS, T_pA, EDYY karoları; canlı tasarım spektrumu |
| `sihirbaz-5-zemin.png` | Adım 5 — geoteknik rapor değerleri (q_em, q_k → q_t, k₀ tipik aralık çubuğu, γ), temel tipi kartları, mütemadi temel varsayılanları, ters T kesit önizlemesi ve anında denetim |
| `sihirbaz-8-ozet.png` | Adım 8 — durum bandı, uyarılar, yedi özet kartı (yönetmelik başvurularıyla), "Ardından", modele yazılacak yama |
| `karsilastirma.png` (2400 px) | Dört ekran etiketli, 2 × 2 |

Görsellerdeki sayıların hepsi motor işlevleriyle hesaplanmıştır (`uret.py` motoru içe aktarır). **Saha değerleri temsilîdir**
(S_S = 1,200, S_1 = 0,350, q_em = 150 kN/m², k₀ = 18 000 kN/m³ …); Tokat/Merkez koordinatının gerçek harita değerleri değildir.

---

## 1. İlkeler

1. **Yönetmelik sırası = adım sırası.** Proje ve yapı türü (hangi yönetmelikler) → malzeme (TS 500 / ÇYTHYE) → yükler
   (TS 498:2021) → deprem (TBDY 2018 Bölüm 2–4) → zemin ve temel (TBDY Bölüm 16, TS 500 md. 10) → birleşimler (TS 500 md.
   6.2.6, ÇYTHYE 5.3, TBDY 4.4.4) → analiz seçenekleri (TBDY 4.5.8 ve motor ayarları) → özet. Her adım yalnız önceki
   adımların sonucuna bağlıdır (§2'deki bağımlılık çizelgesi); geri dönüp değiştirince etkilenen sonraki adımlar
   yeniden doğrulanır.
2. **Seç → hesaplanan değer hemen görünür.** Bağımlı büyüklükler (I, R, D, F_S, F_1, S_DS, S_D1, DTS, BYS, S_k, s, q_t …)
   giriş kutusu değil **salt okunur çip**tir; yanında yönetmelik tablosu yazılıdır. Elle değiştirmek ayrı bir "Elle
   değiştir" eylemidir ve motorun yazdığı uyarıyla birlikte gelir (motor zaten `I`, `R`, `D` farkında uyarı ekler).
3. **Akıllı varsayılan, açık kaynak.** Her alanın varsayılanı yapı türünden ve seçili şablondan gelir; çipte kaynağı yazar
   ("şablon", "Tablo 4.1", "kullanıcı"). Saha verisi (S_S, S_1, q_em, k₀) için **varsayılan yoktur**: boş kalır, adım "eksik"
   olur. (Web arayüzündeki `SS: 1.0, S1: 0.3` gibi yer tutucu değerler sihirbazda kullanılmaz.)
4. **Çevrimdışı.** op4 ağa çıkmaz (MIMARI: Belge penceresi yerel). Harita spektral ivme katsayıları resmî **Türkiye
   Deprem Tehlike Haritası** etkileşimli hizmetinden (AFAD, tdth.afad.gov.tr) kullanıcı tarafından okunur ve girilir
   ya da raporundan içe aktarılır; koordinat yalnız kayıt içindir.
5. **Motorla aynı hesap.** Önizleme hesapları motorun tablolarıyla yapılır (§6.3); arayüzde ayrı, "yaklaşık" tablo tutulmaz.
6. **Renk anlam taşır, tek başına taşımaz.** Durumlar simge + metinle (✓ / ! / boş daire + "Eksik"); vurgu rengi tek
   (modernize palet: kobalt / petrol / grafit seçeneklerinden biri; taslakta kobalt yer tutucu), tunç/kahve–altın yok.

---

## 2. Akış ve bağımlılıklar

```
 1 Proje & yapı türü ──sistem──► 2 Malzemeler (beton+donatı | yapı çeliği | ikisi)
   │  il/ilçe, rakım ───────────► 3 Yükler: kar bölgesi (Ek 1) ve S_k (Çizelge 3)
   │  H_N (tahmini) ────────────► 3 rüzgâr q(z) · 4 BYS, T_pA
   │  sistem ───────────────────► 4 Tablo 4.1 listesi, C_t · 6 varsayılan küme · 7 çatlamış kesit varsayılanı
 3 Yükler ──kullanım sınıfı────► 4 n önerisi (Tablo 4.3) · kar açık ─► 6 kar satırları
 4 Deprem ──zemin sınıfı───────► 5 (salt okunur) · E açık ─► 6 deprem satırları · 7 çatlamış kesit zorunlu
          ──S_DS, DTS──────────► 4 taşıyıcı sistem kuralları (md. 4.3.4) · 8 özet
 5 Zemin & temel ──beton───────► (2'deki betonlardan biri; çelikte C30/37 varsayımı)
 6 Birleşimler ── açık durumlar (G Q S W E) ile açılır; satır sayısı canlı
 7 Analiz ── betonarme + E ise catlamis_rijitlik = true (TBDY 4.5.8.1)
 8 Özet ── "Projeyi oluştur" ⇒ tek işlem, tek geri alma adımı
```

**Adım durumları** (adım çubuğunda simge + metin):

| Durum | Görünüm | Ne zaman |
|---|---|---|
| Etkin | Dolu vurgu dairesi, numara | Açık olan adım |
| Tamam | Yeşil daire ✓ | Ziyaret edildi, bütün zorunlu alanlar geçerli, uyarı yok |
| Uyarı | Amber daire ! | Geçerli ama motor bir uyarı yazacak: doğrulanmamış kütüphane kaydı (`dogrulandi: false`), Ek 1 kar bölgesi (OCR), I/R/D elle değiştirildi, çatlamış kesit kapalı, taşıyıcı sistem kuralı (md. 4.3.4) ya da BYS sınırı, EDYY Tablo 4.4'e göre uygulanamaz, q_k boş |
| Eksik | Boş daire, kırmızı ! | Zorunlu alan boş ya da motorun reddedeceği değer (ör. S_S boş, ZF ile deprem açık, q_em ≤ 0, h_tabla > h_govde) |
| Varsayılan | Boş daire, gri numara | Ziyaret edilmedi; şablon/yapı türü varsayılanları geçerli (alt satırda "(şablon)") |

"Projeyi oluştur" yalnız **eksik** adım yokken etkin olur; uyarılar engellemez (motor da çözer, uyarıyı rapora yazar).

---

## 3. Ortak arayüz

### 3.1 Yerleşim (1920×1080, 1×; DPI ile ölçeklenir)

Modal pencere 1600 × 944, ekran ortasında; arkada program kabuğu %42 karartılır (açılışta boş "Adsız 1", Z = 0 ızgarası).

| Bölge | Ölçü | İçerik |
|---|---|---|
| Başlık | 56 px | Simge karosu, "Yönetmelik Sihirbazı" (15/600), alt satır proje adı (11/400); sağda **Yönetmelik şablonu** açılır listesi (330 px), "Şablon olarak kaydet…", kapat |
| Adım çubuğu (sol) | 272 px | "YÖNETMELİK SIRASI"; 8 satır × 62 px: durum simgesi, başlık (12/600), yönetmelik kümesi (10/500), değer özeti (11/400; uyarı/eksik renkli); bağlantı çizgisi tamamlanan aralıkta yeşil; altta ilerleme çubuğu, durum açıklaması, kütüphane notu |
| İçerik (orta) | 984 px (iç dolgu 28) | "ADIM n / 8" (10/700 vurgu), başlık (18/600), bir–iki satır açıklama, sağda bölüm çipleri; bölümler: başlık satırı (simge + 12/600 + sağda **ⓘ başvuru çipi**), alan satırları 26–28 px, iki sütun (448 + 24 + 456) |
| Etki kartı (sağ) | 344 px | **Bu adımın etkisi**: MODELE YAZILAN (eş aralıklı yazı, `anahtar = değer`), PROJE BELGESİNE, ETKİLEDİĞİ ADIMLAR / ÇÖZÜMDE KULLANILDIĞI YER, UYARILAR, KAYNAK ("Madde metnini Belge penceresinde aç ›") |
| Alt çubuk | 60 px | Solda "Adımı varsayılana döndür" ve kısayol ipucu; sağda Geri · Atla (yalnız isteğe bağlı adımda) · **İleri: ‹sonraki adım›** (birincil). Adım 8'de Geri · Şablon olarak kaydet… · **Projeyi oluştur** |

### 3.2 Alan türleri

| Tür | Görünüm | Davranış |
|---|---|---|
| Sayı + birim | Sağa hizalı tablo rakamları, birim kutunun içinde soluk ("kN/m²", "g", "m") | Ondalık virgül ya da nokta kabul edilir; görüntü virgül + ince boşluk binlik ("18 000"); odakta vurgu kenarı + 2 px hale |
| Açılır liste | Metin + sevron; uzun listelerde arama (il 81 kayıt, kullanım sınıfı 25 kayıt) | Seçenek etiketinde değer: "Konut (oda ve koridorlar) — 2,0 kN/m²" |
| Segmentli seçim | 2–6 seçenek; seçili dolu vurgu | ZA…ZF, Otomatik/Ampirik/Rayleigh, x / y / xy; uyarılı seçenekte amber nokta (ZF) |
| Seçim kartı | 3 kart, radyo, simge, yönetmelik satırları | Yapı türü, temel tipi; "kısıtlı" rozeti (Karma) |
| Hesaplanan çip | Yuvarlak, `ad = değer birim`; vurgu (ana çıktı) / nötr / yeşil (sağlandı) | Salt okunur; üzerine gelince formül ve tablo ipucu; "Elle değiştir" sağ tık menüsünde |
| Sonuç karosu | 108 × 46; küçük ad, 16/600 değer, birim/tablo | S_DS, S_D1, T_A, T_B, DTS, BYS, T_pA, EDYY |
| ⓘ başvuru çipi | "ⓘ Tablo 3.1" | İpucu: madde başlığı, tablo satırı, motor kaynağı (`kaynak` alanı); tıklayınca Belge penceresinde yönetmelik metni (yerel) |

### 3.3 Doğrulama dili

Satır altı ileti, motorun öğretici hata metinleriyle **aynı cümle** (ör. "deprem.SS = 3,2: değerler g cinsinden boyutsuzdur
(Türkiye'de S_S ≤ ~2,0, S_1 ≤ ~0,6)."). Hata (kırmızı kenar) = motor reddeder; uyarı (amber kenar) = motor çözer ama
`uyarilar`a yazar; bilgi (gri) = açıklama. İleti kaynağı ⓘ ile gösterilir.

### 3.4 Klavye

Tab / Shift+Tab alanlar arası; **Alt+→ İleri, Alt+← Geri**; Ctrl+1…8 doğrudan adım; Enter alanı onaylar (adım
değiştirmez); Esc kapatır (değişiklik varsa "Uygulanmamış değişiklikler: Uygula / Vazgeç / İptal"). Komut satırı eşdeğeri:
`YÖNETMELİK [adım]` açar, `YÖNETMELİK UYGULA` (özetteki onayın günlüğe yazılan karşılığı).

---

## 4. Adımlar ve alanlar

Sütunlar: **Alan** · **Motor anahtarı** (bina JSON; `—` = yalnız proje belgesi) · **Birim** · **Varsayılan** · **İzinli /
seçenekler** · **Doğrulama** (motorun kuralı; H = hata/eksik, U = uyarı) · **Bağımlılık** · **Kaynak**.

### 4.1 Adım 1 — Proje ve yapı türü (`sihirbaz-1-proje.png`)

**Proje künyesi** (rapor kapağı: `rapor.statik_rapor(secenek={"proje": {ad, yer, il, ilce, ada, parsel, malik, hazirlayan, kontrol, tarih}})`)

| Alan | Motor anahtarı | Birim | Varsayılan | İzinli | Doğrulama | Bağımlılık | Kaynak |
|---|---|---|---|---|---|---|---|
| Proje adı | `baslik` (+ künye `ad`) | — | "Adsız N" | metin | boşsa motor "Bina modeli" yazar | pencere başlığı, rapor | — |
| Açıklama (isteğe bağlı) | `aciklama` | — | boş | metin | — | IFC proje açıklaması | — |
| İl | `yuk_durumlari.S.il` + künye | — | şablondan / boş | 81 il (`TS498_KAR_BOLGE_IL`) | — | Adım 3 kar bölgesi | TS 498:2021 Ek 1 |
| İlçe | `yuk_durumlari.S.ilce` + künye | — | "Merkez" (varsa) | ilin ilçeleri | Ek 1'de yoksa H: "kar bölgesini (1–9) doğrudan girin" | Adım 3 | TS 498:2021 Ek 1 |
| Ada / parsel, yapı sahibi, hazırlayan, kontrol eden, tarih | — (künye) | — | tarih bugün | metin / tarih | — | rapor kapağı | — |
| Enlem / Boylam | — (künye `koordinat`) | ° (WGS84 ondalık) | boş | sayı | Türkiye kutusu dışında (≈ 35,8–42,2 K; 25,6–44,9 D) U | Adım 4 kaynak satırı | — |
| Rakım | `yuk_durumlari.S.rakim` | m | boş → 0 | ≥ 0 | negatif H (motor `pozitif`) | S_k (Çizelge 3) | TS 498:2021 md. 11 |

**Yapı türü** (kart):

| Seçim | Motor | Uygulanan yönetmelikler | Sonraki adımlara etkisi |
|---|---|---|---|
| Betonarme | `sistem: "betonarme"` | TS 500:2000 (+T1/T2/T3), TS 708:2016, TBDY 2018 Bölüm 7, TS 498:2021 | Adım 2 beton + donatı; Adım 4 Tablo 4.1 A ve B satırları (motor `onuretimli` grubunu betonarmeyle uyumlu sayar), C_t = 0,10 (çerçeve) / 0,07; Adım 6 `ts500`; Adım 7 çatlamış kesit açık |
| Çelik | `sistem: "celik"` | ÇYTHYE 2018 (YDKT/GKT), TBDY 2018 Bölüm 9, TS 498:2021 | Adım 2 yapı çeliği (+ temel için beton); Adım 4 C satırları, C_t = 0,08; Adım 6 `cythye_ydkt`; κ = 0,5, C_h = 1,0 |
| Karma (kısıtlı) | `sistem`: kullanıcı **ana taşıyıcı sistemi** seçer | ikisi | Motorda tek `sistem` ve tek `kombinasyon_kumesi` vardır; eleman tahkiki kesitin malzemesine göre yapılır (`_eleman_tasarla`: çelik kesit → ÇYTHYE, beton → TS 500). Çelik elemanlar `ts500` kümesinde YDKT dayanımıyla ama TS 500 katsayılarıyla tahkik edilir → **açık soru 1** |

**Ön geometri (tahmini)** — modele yazılmaz; yalnız önizleme (BYS, T_pA, rüzgâr q):

| Alan | Motor | Birim | Varsayılan | İzinli | Doğrulama |
|---|---|---|---|---|---|
| Kat sayısı | — | adet | 4 (şablon) | 1–12 (aks–kat `EN_FAZLA_KAT`) | > 12 U ("genel model gerekir") |
| Tipik kat yüksekliği | — | m | 3,00 | ≥ 2,00 | < 2,00 H (motor: "kat yüksekliği en az 2 m") |
| H_N | — (hesap) | m | kat × yükseklik | — | model kurulunca `kot_N − kot_0` (TBDY md. 3.3.1.3: bina tabanından) |

**Uygulanacak yönetmelikler** çipleri yapı türünden türetilir; Karma'da ikisi de etkin.

### 4.2 Adım 2 — Malzemeler (görsel yok; içerik)

| Alan | Motor anahtarı | Varsayılan | Seçenekler | Önizleme (salt okunur) | Doğrulama | Kaynak |
|---|---|---|---|---|---|---|
| Beton sınıfı | `malzemeler["C30"] = {"kutuphane": "C30/37"}` (ad = sınıfın ilk parçası) | C30/37 | C16/20, C18/22, C20/25, C25/30, C30/37, C35/45, C40/50, C45/55, C50/60 | f_ck, f_ctk, E_c (Çizelge değeri), f_cd = f_ck/1,5, f_ctd = f_ctk/1,5, γ = 25 kN/m³, ν = 0,20, G = 0,40·E_c | Deprem açıkken C25'ten düşük: U ("TBDY 7.2.5: deprem elemanlarında en az C25" — kütüphane notu, **doğrulanmalı**: motor zorlamıyor) | TS 500:2000 Çizelge 3.2 |
| Donatı | `malzemeler["B420C"] = {"kutuphane": "B420C"}` | B420C | B420C, B500C | f_yk, f_su, E_s = 200 000 MPa, f_yd = f_yk/1,15, ε_sy | — | TS 708:2016; TS 500 Çizelge 3.1; TBDY 7.2.5.3b |
| Yapı çeliği | `malzemeler["S275"] = {"kutuphane": "S275"}` | S275 (çelik), S355 öneri yok | S235, S275, S355 | F_y, F_u (t ≤ 40 mm) ve 40 < t ≤ 80 mm değerleri, E = 200 000, G = 77 200 MPa, γ = 78,5 | — | ÇYTHYE 2018 Tablo 2.1A |
| Elle E / γ (gelişmiş) | `malzemeler[ad].E`, `.gamma`, `.G` | kapalı | sayı (MPa, kN/m³) | — | açılırsa U | — |
| Paspayı (yeni kesitler) | kesitte `pas` (m) | 0,030 | 0,015–0,100 | d′ = pas + 0,02 | — | motor varsayımı (`_tasarim_varsayimlari`) |

Örnek önizleme (motordan): C30/37 → f_ck 30, f_ctk 1,9, E_c 32 000, f_cd 20,0, f_ctd 1,267 MPa; B420C → f_yd 365,22 MPa.

### 4.3 Adım 3 — Yükler, TS 498:2021

Yük durumları: `yuk_durumlari.G.acik` her zaman `true` (kilitli); `Q.acik` varsayılan `true`.

**Sabit yük (G)** — öz ağırlık otomatik (betonarme γ = 25, çelik 78,5 kN/m³; `TS498_BIRIM_AGIRLIK`).

| Alan | Motor anahtarı | Birim | Varsayılan | Seçenekler | Doğrulama | Kaynak |
|---|---|---|---|---|---|---|
| Normal kat kaplaması | yeni döşemelerde `g_ek` = `KAPLAMALAR` anahtarı (motor metin anahtarını kabul eder) ya da sayı | kN/m² | şablondan (taslakta `sap-seramik-siva` 1,23) | `sap-seramik-siva` 1,23 · `sap-parke-siva` 1,15 · `sap-mermer-siva` 1,99 · `sap-siva` 1,03 · elle | `sap-seramik-siva` **doğrulanmamış** (seramik birim ağırlığı) → U | TS 498:2021 md. 3.2, 5.4–5.6 → TS ISO 9194 (katman toplamı) |
| Çatı kaplaması | çatı döşemelerinde `g_ek` | kN/m² | `cati-teras` 1,45 | aynı liste | — | aynı |
| Dış / iç duvar | `duvarlar[ad] = {"kutuphane": …}`; kirişte `duvar` | kN/m² (duvar alanı) | `tugla-delikli-19` 2,70 | `tugla-delikli-19/13`, `tugla-bosluklu-19/13`, `tugla-dolu-19`, `gazbeton-20/25/10`, elle `kN_m2` | elle değer ≥ 0 | TS 498 md. 5 → TS ISO 9194 |
| Duvar yerleşimi (yeni kirişler) | — (varsayılan) | — | dış kirişlerde | dış / hepsi / yok | — | — |
| Çatı parapeti | çatı kirişinde `duvar_h` | m | 1,0 | 0 < h ≤ 10 | > 10 H | motor |
| Döşeme kalınlığı (yeni) | `dosemeler[].h` | m | 0,14 (web arayüzü), motor 0,12 | 0 < h ≤ 1,0 | > 1,0 H ("metre girilir") | — |

**Hareketli yük (Q)** — her döşemede `kullanim` ya da `q`. Sihirbaz **varsayılanları** belirler (normal kat, çatı, merdiven,
balkon); mevcut döşemelere uygulama §7.3.

| Kullanım sınıfı (`TS498_HAREKETLI`) | q (kN/m²) | Çizelge 6 satırı | n öneri (Tablo 4.3 eşlemesi) |
|---|---|---|---|
| konut, ofis, teras, hastane-oda, dukkan-konut, cati-gezilen | 2,0 | 2 | 0,3 |
| cati-arasi | 1,5 | 1 | 0,3 |
| derslik, yatakhane | 3,5 | 3 | 0,6 |
| hastane-mutfak, merdiven-konut, cati-bahcesi | 3,5 | 3 | 0,3 (hastane-mutfak eşlemesi "yorum") |
| koridor-genel, merdiven-umumi, balkon (≤ 10 m²) | 5,0 | 4 | 0,3 (koridor/merdiven "yorum") |
| magaza, toplanti, lokanta, kutuphane, atolye-hafif, spor, tribun-sabit | 5,0 | 4 | 0,6 (kütüphane, atölye "yorum") |
| garaj (≤ 2,5 t) | 5,0 | 6 | 0,3 |
| tribun-ayakta | 7,5 | 5 | 0,6 |
| depo | 5,0 | **satır yok**, öğretim varsayımı, `dogrulandi: false` → U | 0,8 |

Balkon > 10 m²: motor q = 5,0 + 0,35·(A − 10) uygular (Çizelge 6 satır 4). Hareketli yük azaltması (Çizelge 7) kütüphanede
var, **motor uygulamaz** → sihirbazda seçenek olarak gösterilmez (açık soru 6).

**Kar (S)** — `yuk_durumlari.S`

| Alan | Anahtar | Birim | Varsayılan | İzinli | Doğrulama | Kaynak |
|---|---|---|---|---|---|---|
| Kar yükü hesaba katılsın | `S.acik` | — | açık (açık soru 10) | — | — | TS 498:2021 md. 11 |
| Kar bölgesi | `S.bolge` (boşsa motor `S.il`/`S.ilce`'den bulur) | — | Ek 1'den (Tokat/Merkez → 3) | **1–9** | dışı H; Ek 1'den gelirse U ("OCR aktarımı, doğrulanmadı; Ek 2 haritasından teyit") | Ek 1 / Ek 2 |
| Rakım | `S.rakim` | m | Adım 1 | ≥ 0 | — | Çizelge 3 |
| S_k elle | `S.Sk` | kN/m² | boş (hesaplanır) | ≥ 0 | — | — |
| Çatı eğimi α | `S.alpha` | ° | boş (düz çatı) | ≥ 0 | — | TS EN 1991-1-3 Tablo 5.2 (`dogrulandi: false` → U) |
| μ₁ elle | `S.mu` | — | 0,8 | ≥ 0 | 0,8 dışı "kullanıcı değeri" | aynı |
| C_e, C_t | `S.Ce`, `S.Ct` | — | 1,0 / 1,0 | ≥ 0 (C_e: 0,8 açık, 1,0 normal, 1,2 korunaklı) | — | aynı |

Hesaplanan (motor `kar_Sk`, `kar_mu1`): **S_k** = Çizelge 3 [bölge][rakım sütunu] (ara rakımda **bir üst** satır; 1000 m
üstü 1000 m değeri × 1,10 (≤ 1500 m) / × 1,15); **μ₁** = 0,8 (α ≤ 30°), 0,8·(60 − α)/30, 0 (α ≥ 60°); **s = μ₁·C_e·C_t·S_k**
çatı döşemelerine. Örnek: bölge 3, 623 m → S_k = 0,85, s = 0,68 kN/m². Deprem kütlesinde çatı karının %30'u (Tablo 4.3 notu).
Not: istekte geçen "bölge I–IV" eski TS 498:1997'dir; TS 498:2021 ve motor **9 bölge** kullanır.

**Rüzgâr (W)** — `yuk_durumlari.W`

| Alan | Anahtar | Varsayılan | İzinli | Kaynak |
|---|---|---|---|---|
| Rüzgâr hesaba katılsın | `W.acik` | açık (motor varsayılanı kapalı; açık soru 9) | — | TS 498:2021 md. 14 |
| Bileşke katsayı C | `W.C` | 1,2 (kapalı bina: +0,8 basınç, −0,4 emme) | > 0; kule tipi 1,6 | Çizelge 5 (1.1.1) |
| Sarp yamaç / yüksek yer | `W.sarp` | hayır | evet → q ≥ 1,1 kN/m² | md. 14.3 |

Önizleme: q(z) Çizelge 4 basamakları — z ≤ 8 m: 0,5 · 8–20 m: 0,8 · 20–100 m: 1,1 · > 100 m: 1,3 kN/m² (q = v²/1600);
H_N'ye göre kat kat tablo. Motor W+X, W−X, W+Y, W−Y durumlarını F_i = C·q(z_i)·B_cephe·kat payı ile kurar.
ÇYTHYE md. 5.3 notu (karakteristik rüzgâr ≥ 0,5 kN/m²) çelikte bilgi olarak gösterilir.

### 4.4 Adım 4 — Deprem, TBDY 2018 (`sihirbaz-4-deprem.png`)

**Deprem yer hareketi** (md. 2.2–2.3.2)

| Alan | Anahtar | Birim | Varsayılan | İzinli | Doğrulama | Kaynak |
|---|---|---|---|---|---|---|
| Deprem etkisi | `yuk_durumlari.E.acik` | — | açık | — | kapalıysa adım "Atla" ile geçilebilir; özet U | TBDY md. 4.7 |
| Tasarım düzeyi | `deprem.DD` | — | `"DD-2"` (sabit) | — | DD-2 dışı U (motor: "dayanıma göre tasarımda DD-2 esastır", md. 4.4.1) | md. 2.2 |
| S_S (DD-2) | `deprem.SS` | g | **boş** | 0 < S_S ≤ 3,0 | boş/0 H; > 3,0 H | md. 2.3.2.1 |
| S_1 (DD-2) | `deprem.S1` | g | **boş** | 0 < S_1 ≤ 1,5 | boş/0 H; > 1,5 H | aynı |
| S_S, S_1 (DD-3) | `deprem.SS_DD3`, `S1_DD3` | g | boş (isteğe bağlı) | ≥ 0; **ikisi birlikte** | tek biri H; boşsa motor λ = 1 alır (U değil, bilgi); DD-3 > DD-2 U ("doğrulanmalı") | md. 4.9.1.4 (λ) |
| Kaynak | — (`kaynaklar.deprem`) | — | "elle girildi" | elle · rapordan · panodan | — | — |

"Rapordan içe aktar…": harita hizmetinin rapor metni (PDF'ten kopyalanan ya da kaydedilen metin) ayrıştırılır; S_S, S_1 (ve
varsa DD-3, PGA, PGV, raporun kendi S_DS/S_D1 değerleri) bulunur, kullanıcıya önizleme ile onaylatılır. Raporda zemin sınıfına
göre S_DS/S_D1 varsa sihirbazın hesabıyla karşılaştırılır (fark > %1 → U). Biçim **doğrulanmalı** (açık soru 4).

**Yerel zemin sınıfı** (Tablo 16.1, md. 16.4) — `deprem.zemin_sinifi`, varsayılan şablondan; ZA (V_S30 > 1500 m/s) · ZB
(760–1500) · ZC (360–760) · ZD (180–360) · ZE (< 180) · **ZF**: segmentte seçilebilir ama deprem açıkken **eksik**
("sahaya özel zemin davranış analizi gerekir, TBDY 16.5; Tablo 2.1/2.2'de değer yok" — motor hata verir; açık soru 2).

**Bina kullanım sınıfı** (Tablo 3.1) — `deprem.BKS` 1/2/3 → `deprem.I` 1,5 / 1,2 / 1,0 (salt okunur çip; elle değişirse U).

**Taşıyıcı sistem** (Tablo 4.1, md. 4.3) — `deprem.tasiyici` (kanonik anahtar; eski takma adlar motorca çevrilir) →
`R`, `D` (salt okunur), süneklik düzeyi, izinli BYS. Liste yapı türüne göre süzülür; varsayılan liste arayüz alt kümesi
(`TBDY_TASIYICI_ARAYUZ`), "Tüm satırlar" anahtarıyla tablonun 42 satırı (`tasiyici_sistemler(hepsi=True)`):

| Kod | Anahtar | R | D | İzinli BYS |
|---|---|---|---|---|
| A11 | `betonarme-cerceve-yuksek` | 8 | 3 | ≥ 3 |
| A13 | `betonarme-perde-bosluksuz` | 6 | 2,5 | ≥ 2 |
| A15 | `betonarme-perde-cerceve` | 7 | 2,5 | ≥ 2 |
| A16 | `betonarme-tek-katli-mafsalli` | 3 | 2 | — (H ≤ 12 m) |
| A31 | `betonarme-cerceve-sinirli` | 4 | 2,5 | ≥ 7 (yalnız DTS 3, 4) |
| C11 | `celik-cerceve-yuksek` | 8 | 3 | ≥ 3 |
| C12 | `celik-dismerkez-capraz` | 8 | 2,5 | ≥ 2 |
| C13 | `celik-merkezi-capraz` | 5 | 2 | ≥ 4 |
| C16 | `celik-tek-katli-mafsalli` | 4 | 2 | — (H ≤ 12 m) |
| C31 | `celik-cerceve-sinirli` | 4 | 2,5 | ≥ 7 (yalnız DTS 3, 4) |

Kurallar (motor `_deprem_on` uyarıları; sihirbazda U, listede ilgili satır soluk + ipucu): BYS < izinli BYS ("bu yükseklikte
kullanılamaz"); DTS = 1a–4a ve süneklik "sınırlı" (md. 4.3.4.1); A31/B31/C31 ve DTS ∉ {3, 4} (md. 4.3.4.3); taşıyıcı grup
yapı türüyle uyuşmuyor. Engellesin mi uyarsın mı: açık soru 8.

**Hesap seçenekleri**

| Alan | Anahtar | Varsayılan | Seçenekler | Doğrulama | Kaynak |
|---|---|---|---|---|---|
| Periyot T_p | `deprem.periyot` | `"otomatik"` | otomatik (motor: DTS 3–4 ya da BYS ≥ 6 ise ampirik, değilse Rayleigh ≤ 1,4·T_pA) · ampirik · rayleigh | — | md. 4.7.3 |
| C_t | `deprem.Ct` | Otomatik (anahtar yazılmaz) | 0,10 betonarme çerçeve · 0,08 çelik · 0,07 diğer | > 0 | Denk. 4.27; tamamı perdeli binada Denk. 4.28 (C_t = 0,1/√A_t ≤ 0,07) motor uygulamaz → bilgi |
| n | `deprem.n` | Otomatik (anahtar yazılmaz; motor döşemelerin kullanım sınıflarından en büyük n'yi alır) | 0,3 · 0,6 · 0,8 · 1,0 | 0 ≤ n ≤ 1 | Tablo 4.3 |
| Ek dışmerkezlik | `deprem.dismerkezlik` | 0,05 | ≥ 0 (arayüz üst sınırı 0,30) | > 0,30 H (web arayüzüyle aynı) | md. 4.5.10.2 |
| Dolgu duvarlar | `deprem.dolgu` | `"bitisik"` | bitişik gevrek (λδ/h ≤ 0,008κ) · esnek derzli (0,016κ) | — | md. 4.9.1.3 |

**Hesaplanan değerler (motorla birebir; önizlemede model yoksa H_N = Adım 1 tahmini)**

| Büyüklük | Formül (motor) | Kaynak | Örnek |
|---|---|---|---|
| F_S, F_1 | Tablo 2.1/2.2 satırı, sütunlar arası doğrusal, uçlarda sabit (`zemin_katsayisi`) | md. 2.3.3.1 | ZD: 1,020 / 1,950 |
| S_DS, S_D1 | S_S·F_S, S_1·F_1 | Denk. 2.1 | 1,224 / 0,682 g |
| T_A, T_B, T_L | 0,2·S_D1/S_DS; S_D1/S_DS; 6 s | Denk. 2.3, md. 2.3.4.1 | 0,112 / 0,558 s |
| S_ae(T) | (0,4 + 0,6T/T_A)S_DS · S_DS · S_D1/T · S_D1·T_L/T² | Denk. 2.2 | grafik |
| DTS | S_DS ≥ 0,75 → 1; ≥ 0,50 → 2; ≥ 0,33 → 3; diğer 4; BKS 1 ise "a" | Tablo 3.2 | 1 |
| BYS | Tablo 3.3, **üç sütun** (DTS 1–2 / 3 / 4): sınırlar 7; 10,5; 17,5; 28; 42; 56; 70 · 10,5; 17,5; 28; 42; 56; 70; 91 · 10,5; 17,5; 28; 42; 56; 91; 105 | Tablo 3.3 | H_N 12 m → 6 |
| T_pA | C_t·H_N^0,75 | Denk. 4.27 | 0,645 s |
| R_a(T), S_aR(T) | R/I (T > T_B); D + (R/I − D)T/T_B; S_aR = S_ae/R_a | Denk. 4.1, 4.8 | grafik |
| EDYY uygunluğu | düzenli: DTS 1–2 BYS ≥ 4, DTS 3–4 BYS ≥ 5; diğer: 5 / 6 | Tablo 4.4 | uygun |
| λ | S_ae(T_p; DD-3)/S_ae(T_p; DD-2) (DD-3 yoksa 1) | md. 4.9.1.4 | 0,446 |
| E_d(Z) | (2/3)·S_DS·G | Denk. 4.10 | 0,816·G |
| Drift sınırı | 0,008κ / 0,016κ; κ: betonarme 1,0, çelik 0,5 | Denk. 4.34 | 0,008 |
| θ_II sınırı | 0,12·D/(C_h·R); C_h: betonarme 0,5, çelik 1,0 | Denk. 4.35 | 0,09 |

V_tE, F_i, m_t model ister; model varken spektrum kartının altında `bina_deprem` önizlemesi (taban kesme, kat kuvvetleri)
açılır (bugünkü web Deprem sekmesiyle aynı).

**Spektrum grafiği**: T = 0–3 s (sağ tık: 0–6 s), y = S_a [g]. Seriler: DD-2 elastik (seri 1, düz 2 px), S_aR (seri 2, düz),
DD-3 elastik (seri 3, kesik — düşük kontrast olduğu için kesik çizgi + doğrudan etiket); T_A, T_B kesik dikey; T_pA noktalı
dikey + iki işaret + etiket. Lejant üstte, kısa doğrudan etiketler eğrilerin yanında. Üzerine gelince artı imleç ve ipucu
(T, S_ae, R_a, S_aR). Grafik altında "Tablo görünümü" anahtarı (motorun nokta listesi `_spektrum_noktalari`: 0,05 s adım + köşe periyotları + T_p).

### 4.5 Adım 5 — Zemin ve temel (`sihirbaz-5-zemin.png`)

**Zemin** (`temeller.zemin`; zemin sınıfı Adım 4'ten salt okunur, "Adım 4'te değiştir")

| Alan | Anahtar | Birim | Varsayılan | İzinli | Doğrulama | Kaynak |
|---|---|---|---|---|---|---|
| Emniyet gerilmesi q_em | `zemin.q_em` | kN/m² | şablon / 200 (motor) | > 0 | ≤ 0 H | TS 500 md. 10.1 (servis G+Q: p_maks ≤ q_em) |
| Karakteristik taşıma gücü q_k | `zemin.q_k` | kN/m² | boş | > 0 | boş U: motor q_k = 3·q_em varsayar (`GS_KLASIK`, "VARSAYIM") | TBDY md. 16.8.3, Denk. 16.6–16.7 |
| (hesap) q_t | — | kN/m² | q_k/γ_Rv, γ_Rv = 1,4 | — | — | Tablo 16.2 |
| Yatak katsayısı k₀ | `zemin.k0` | kN/m³ | şablon / 20 000 (motor) | > 0 | ≤ 0 H | TS 500 md. 10.4.2 (Winkler) |
| Zemin birim hacim ağ. γ | `zemin.gamma` | kN/m³ | 18 | > 0 | motor okur, **tahkiklerde henüz kullanmıyor** (bilgi) | — |
| Rapor no / tarih | — (künye `geoteknik`) | — | boş | metin | — | — |

k₀ tipik aralık çubuğu yalnız **öğreticidir** (yönetmelik değeri değil; web arayüzündeki Bowles 1996 Tablo 9-1 plaka değerleri):
gevşek kum 4 800–16 000 · orta sıkı kum 9 600–80 000 · sıkı kum 64 000–128 000 · killi orta sıkı kum 32 000–80 000 · siltli
orta sıkı kum 24 000–48 000 · kil q_u ≤ 200 kPa 12 000–24 000 · 200–800 kPa 24 000–48 000 · > 800 kPa > 48 000. Zemin sınıfına
göre önerilen bant gösterilir; eşleme **doğrulanmalı** (sınıf V_S30'a, k₀ deney türüne ve temel boyutuna bağlıdır).

**Temel tipi** — `temeller.tip`: `tekil` · `surekli` (mütemadi) · `radye`. Kartta model: tekil = kolon başına B × L, mesnet
ankastre/mafsal/elastik; mütemadi = aks boyunca ters T kiriş, Winkler (k_z = k₀·B·l_etki, dönme yayı k₀·B³/12·l); radye =
iki doğrultulu ızgara, düğüm yayı k₀·A_etki, isteğe bağlı aks kirişleri.

| Tip | Alan | Anahtar | Birim | Varsayılan (motor) | İzinli / doğrulama (motor `temel.oku`) | Kaynak |
|---|---|---|---|---|---|---|
| Tekil | B, L | `varsayilan.B`, `.L` | m | 1,5 / 1,5 (web arayüzü 1,6) | > 0 | — |
| | h | `varsayilan.h` | m | 0,6 | ≥ 0 | — |
| | Mesnet | `mesnet` | — | `ankastre` | ankastre · mafsal · elastik (k₀ yayları: k_Z = k₀BL, k_rX = k₀BL³/12, k_rY = k₀LB³/12) | — |
| Mütemadi | Doğrultu | `surekli.yon` | — | `xy` | x · y · xy | — |
| | Akslar | `surekli.akslar` | — | `"tum"` | "tum" ya da aks adları (model akslarıyla; yeni projede yalnız "tum") | — |
| | B tabla | `surekli.B` | m | 1,20 | 0 < B ≤ 6 | — |
| | h tabla | `surekli.h_tabla` | m | 0,40 | 0 ≤ h ≤ h_govde; < 0,20 U | TS 500 md. 10.4.2 (≥ 200 mm) |
| | b gövde | `surekli.b_govde` | m | 0,50 | 0 < b ≤ B | — |
| | h gövde (toplam) | `surekli.h_govde` | m | 1,00 | 0 < h ≤ 4; ≥ L_n/10 model kurulunca U | TS 500 md. 10.4.2 |
| | Taşma | `surekli.tasma` | m | 0,5 | ≥ 0 | — |
| | Ağ aralığı | `surekli.ag` | m | otomatik (0,5'ten SD sınırına göre büyür) | otomatik ya da ≥ 0,10 | — |
| | Yatay | `surekli.yatay`, `kh_oran` | — | `tutulu` | tutulu · yay (k_h/k_z oranı **zorunlu**, geoteknik rapordan) | — |
| Radye | h | `radye.h` | m | 0,80 | 0 < h ≤ 4; < 0,30 U | TS 500 md. 10.4.2 (≥ 300 mm) |
| | Taşma, ağ, yatay | `radye.tasma`, `.ag`, `.yatay` | m | 1,0 / 0,5 / tutulu | mütemadi ile aynı | — |
| | Kirişli radye | `radye.kiris` | m | `null` | {b > 0 (0,5), h > radye.h (1,2)} | — |
| Hepsi | Temel betonu / donatı | `temeller.malzeme`, `.donati` | — | ilk beton; çelik binada C30/37 varsayımı (motor uyarır) | `malzemeler` içinden | — |
| | Paspayı | — | mm | 50 (sabit) | — | TS 500 md. 10.1 |

**Anında denetim** kutusu motorun okuma kurallarını gösterir (✓ sağlandı / ○ model kurulunca ya da çözümde): h_tabla ≥ 0,20;
b_govde ≤ B; h_tabla ≤ h_govde; B ≤ 6 m, h ≤ 4 m; h_govde ≥ L_n/10; zımbalama (TS 500 md. 8.3.1), ρ ≥ 0,002 (md. 10.3.3).

### 4.6 Adım 6 — Yük birleşimleri

| Alan | Anahtar | Varsayılan | Seçenekler | Doğrulama |
|---|---|---|---|---|
| Kombinasyon kümesi | `kombinasyon_kumesi` | betonarme `ts500`, çelik `cythye_ydkt` | `ts500` (TS 500 md. 6.2.6 + TS 498 kar + TBDY 4.4.4.1) · `cythye_ydkt` (ÇYTHYE 5.3.1 + TBDY 9.2.5.1; deprem satırında 1,2G, rüzgâr 1,6W) · `cythye_gkt` (ÇYTHYE 5.3.2 + TBDY Denk. 9.1a–c) | betonarmede ÇYTHYE kümesi U; çelikte `ts500` U |

Önizleme tablosu = motorun `_kombinasyon_listesi` çıktısı, açık durumlarla canlı: satır (şablon ad), tür (dayanım / deprem /
servis / öteleme), açılım (W → 4 yön; E_d(H) → Denk. 4.9'un 32 varyantı; öteleme → 4 tekli), "uygulanır" ya da neden
("T durumu yok", "S = 0 (kar kapalı)", "… ile özdeş"), kaynak. Kapalı satırlar soluk. G Q S W E açıkken sayılar:

| Küme | Dayanım | Deprem | Servis | Öteleme | Toplam |
|---|---|---|---|---|---|
| `ts500` | 18 | 64 | 2 | 4 | 88 (T, H satırları uygulanmaz) |
| `cythye_ydkt` | 16 | 64 | 1 | 4 | 85 |
| `cythye_gkt` | 16 | 96 | — | 4 | 116 |

Notlar: kombinasyonlar yeniden çözülmez, durum sonuçlarının katsayılı toplamıdır; öteleme birleşimleri zarfa girmez; deprem
birleşimlerinde betonarmede çatlamış kopyalar (G~c, Q~c, S~c) kullanılır (Adım 7).

### 4.7 Adım 7 — Analiz seçenekleri

| Alan | Anahtar | Varsayılan | Seçenekler | Doğrulama | Kaynak |
|---|---|---|---|---|---|
| Çatlamış (etkin) kesit rijitliği | `analiz.catlamis_rijitlik` | `null` → betonarme + deprem: `true` | açık / kapalı | betonarme + deprem + kapalı U ("TBDY 4.5.8.1'e aykırı") | TBDY md. 4.5.8, Tablo 4.2 |
| (salt okunur) Tablo 4.2 | — | kolon eğilme 0,70, kiriş 0,35, bağ kirişi 0,15, perde eğilme ve kesme 0,50; kesme 1,0 | — | — | Tablo 4.2; iki K: deprem dışı birleşimler brüt (md. 4.5.8.3) |
| Diyafram | `deprem.diyafram` | `rijit` (kat kütle merkezinde efendi düğüm) | rijit · esnek | — | motor modeli |
| Kiriş öz ağırlığı | `analiz.kiris_oz` | `net` (A = b·(h − t_döşeme)) | net · brüt | betonarmede görünür | motor |
| Çelik yanal burulma boyu | `analiz.celik_Lb` | `otomatik` (döşemeli kirişte pozitif momentte L_b = 0, negatif momentte açıklık ve C_b diyagramdan) | otomatik · boy | çelikte görünür | ÇYTHYE Denk. 9.1 (C_b) |
| Diyagram nokta sayısı | `analiz.diyagram_nokta` | 11 | 3–41 (motor kırpar) | tam sayı | — |
| P-Δ / ikinci mertebe | — | **gizli** | — | motor uygulamaz: θ_II denetlenir (Denk. 4.35), β_II yalnız bildirilir; çelikte B1/B2 yok | açık soru 7 |

### 4.8 Adım 8 — Özet ve onay (`sihirbaz-8-ozet.png`)

- Durum bandı: "7 adım tamam · 2 uyarı · 0 eksik" ve tek cümle ("Uyarılar oluşturmayı engellemez").
- Uyarı kutusu: her uyarı adım numarası, motorun cümlesi ve "Düzenle" (o adıma, ilgili alana odakla).
- Yedi özet kartı (iki sütun): her satır `etiket · değer · yönetmelik başvurusu` (ör. "Spektrum · S_DS 1,224 · S_D1 0,682 ·
  Denk. 2.1–2.3", "Kar · Bölge 3 · 623 m · S_k 0,85 · s 0,68 kN/m² · Çizelge 3"); uyarılı satırda amber simge, kart rozeti amber.
- **Ardından**: boş modelle başla (Z = 0 ızgarası) · Hızlı aks sihirbazını aç (MIMARI `HIZLIAKS`) · şablondan başla (9 yapı
  şablonundan biri; yönetmelik değerleri şablonun `deprem`, `yuk_durumlari`, `temeller` alanlarının **üstüne** yazılır).
- Sağda "Projeye uygulanacak": `model/bina.json` yamasının özeti ve `proje/yonetmelik.json` içeriği; altta "Tek geri alma
  adımı", "Model ağacında Yönetmelik verileri düğümü; durum çubuğunda `TBDY · DTS 1 · ZD` çipi".
- Düğmeler: Geri · Şablon olarak kaydet… · **Projeyi oluştur** (yeniden açılışta etiket **Uygula**).

---

## 5. Varsayılanlar (yapı türüne göre, şablon yokken)

| Alan | Betonarme | Çelik |
|---|---|---|
| Malzemeler | C30/37 + B420C | S275 (+ temel için C30/37 + B420C) |
| Tablo 4.1 | A11 (R 8, D 3) | C11 (R 8, D 3) |
| C_t | 0,10 | 0,08 |
| Kombinasyon kümesi | `ts500` | `cythye_ydkt` |
| Çatlamış kesit | açık (deprem açıksa zorunlu) | uygulanmaz |
| κ / C_h | 1,0 / 0,5 | 0,5 / 1,0 |
| Kaplama / duvar | `sap-parke-siva` önerilir (doğrulanmış) ya da şablon; `tugla-delikli-19` | şablon |
| Temel | tekil 1,5 × 1,5 × 0,6, ankastre | aynı |

---

## 6. Veri akışı

### 6.1 Model yaması (`model/bina.json`; örnek = görsellerdeki proje)

```json
{
  "baslik": "Konut Bloğu A",
  "sistem": "betonarme",
  "malzemeler": {"C30": {"kutuphane": "C30/37"}, "B420C": {"kutuphane": "B420C"}},
  "duvarlar": {"tugla19": {"kutuphane": "tugla-delikli-19"}},
  "yuk_durumlari": {
    "G": {"acik": true}, "Q": {"acik": true},
    "S": {"acik": true, "il": "Tokat", "ilce": "Merkez", "rakim": 623, "mu": 0.8},
    "W": {"acik": true, "C": 1.2},
    "E": {"acik": true}
  },
  "deprem": {
    "SS": 1.2, "S1": 0.35, "SS_DD3": 0.45, "S1_DD3": 0.13, "DD": "DD-2",
    "zemin_sinifi": "ZD", "BKS": 3, "I": 1.0,
    "tasiyici": "betonarme-cerceve-yuksek", "R": 8, "D": 3,
    "periyot": "otomatik", "dismerkezlik": 0.05, "dolgu": "bitisik", "diyafram": "rijit"
  },
  "temeller": {
    "tip": "surekli", "malzeme": "C30", "donati": "B420C",
    "zemin": {"q_em": 150, "q_k": 450, "k0": 18000, "gamma": 19},
    "surekli": {"yon": "xy", "akslar": "tum", "B": 1.2, "h_tabla": 0.4, "b_govde": 0.5,
                "h_govde": 1.0, "tasma": 0.5, "ag": "otomatik", "yatay": "tutulu"}
  },
  "kombinasyon_kumesi": "ts500",
  "analiz": {"catlamis_rijitlik": true, "kiris_oz": "net", "diyagram_nokta": 11}
}
```

Kurallar: `n` ve `Ct` **Otomatik** seçiliyse anahtar yazılmaz (motor hesaplar); `I`, `R`, `D` tablo değeriyle yazılır (JSON
kendini anlatsın; motor fark görürse uyarır); `kar.bolge` Ek 1'den bulunmuşsa yazılmaz (motor `il/ilce`'den bulur ve
"doğrulanmadı" notunu kendisi ekler), kullanıcı bölgeyi elle seçtiyse `bolge` yazılır. Döşeme/kiriş düzeyindeki varsayılanlar
(`kullanim`, `g_ek`, `h`, `duvar`) modele değil proje belgesine yazılır ve yeni nesne oluşturulurken uygulanır.

### 6.2 Proje belgesi (`.op4` içinde yeni girdi `proje/yonetmelik.json`; S15 "kaydetme katkısı")

```json
{
  "tur": "op4-yonetmelik", "bicim_surumu": 1, "motor_surumu": "…",
  "kunye": {"ad": "Konut Bloğu A", "il": "Tokat", "ilce": "Merkez", "ada": "1124", "parsel": "7",
            "malik": "", "hazirlayan": "Ayşe Kaya, İnş. Müh.", "kontrol": "", "tarih": "2026-10-31",
            "koordinat": {"enlem": 40.3139, "boylam": 36.5544}, "yapi_turu": "betonarme",
            "geoteknik": {"rapor_no": "GR-26/114", "tarih": "2026-10-12"}},
  "on_geometri": {"kat": 4, "kat_h": 3.0, "HN": 12.0},
  "kaynaklar": {"deprem": {"tur": "elle", "not": "", "rapor_degerleri": null}},
  "varsayilanlar": {"doseme": {"kullanim": "konut", "g_ek": "sap-seramik-siva", "h": 0.14},
                    "cati": {"kullanim": "cati-gezilen", "g_ek": "cati-teras", "parapet_h": 1.0},
                    "merdiven": "merdiven-konut", "balkon": "balkon",
                    "duvar": {"dis": "tugla19", "ic": null, "yerlesim": "dis"}, "kesit_pas": 0.03},
  "adimlar": {"1": "tamam", "2": "tamam", "3": "uyari", "4": "tamam", "5": "tamam", "6": "tamam", "7": "tamam"},
  "sablon": {"ad": "Opus Fortis — betonarme konut", "kimlik": "…", "surum": 3}
}
```

Rapor üretilirken `kunye` → `rapor.statik_rapor(secenek={"proje": …})`. Bilinmeyen alanlar korunur (D1 sözleşmesi).

### 6.3 Motor çağrıları

| Ne zaman | İstek | Süreç | Not |
|---|---|---|---|
| Program açılışı (bir kez) | `bina_kutuphane` | yardımcı | malzemeler, kullanım sınıfları, duvar/kaplama, kar (Çizelge 3, il→bölge), rüzgâr, `deprem` (FS, F1, BKS, taşıyıcı, Ct, n, Tablo 4.2, 4.4), `temel`, `kombinasyon_kumeleri`, `dogrulanmamis` |
| Her değişiklikte (önizleme) | yerel C++ hesap (§9.6), **aynı tablolar** | arayüz | 0 gecikme; `kutuphane()` bugün **DTS (Tablo 3.2) ve BYS (Tablo 3.3) tablolarını ve T_L'yi vermiyor** → eklemeli motor değişikliği önerisi: `kutuphane()["deprem"]` içine `"DTS": TBDY_DTS, "BYS": TBDY_BYS, "spektrum": TBDY_SPEKTRUM` |
| İleri / Uygula öncesi (bağlayıcı) | önerilen yeni işlem `bina_spektrum` {SS, S1, SS_DD3, S1_DD3, zemin_sinifi, BKS, HN, Ct, R, D} → {FS, F1, SDS, SD1, TA, TB, TL, DTS, BYS, TpA, Ra, uyarilar, spektrum[]} | yardımcı | `_spektrum`, `_dts`, `_bys` sarmalayıcısı; yerel sonuçla karşılaştırılır (fark → hata günlüğü) |
| Model varken | `bina_deprem` (`deprem_onizleme`) | yardımcı | V_tE, F_i, m_t; 150–400 ms gecikmeyle |
| Projeyi oluştur / Uygula | model çekirdeği `uygula("yonetmelikUygula", yama)` | arayüz (QuickJS) | tek işlem → tek geri alma adımı; `B4` beyaz listesine eklenir |

Motora yalnız **eklemeli** değişiklik (MIMARI §20.3): iki tablo anahtarı ve bir köprü işlemi; varsayılan davranış değişmez.

### 6.4 Komut kataloğu (`op4/veri/komutlar.json`, önerilen kayıtlar)

| id | ad | etiket | şerit | not |
|---|---|---|---|---|
| `proje.yonetmelik` | YÖNETMELİK (takma: YS) | Yönetmelik verileri… | Dosya › Proje (büyük) ve Model › Proje | `YÖNETMELİK 4` doğrudan Adım 4; yeni projede otomatik açılır (ayar) |
| `proje.yonetmelik_sablonu` | YÖNETMELİKŞABLONU | Yönetmelik şablonları… | Dosya › Proje (küçük) | şablon yöneticisi |

Ayar: "Yeni projede Yönetmelik sihirbazını aç" (varsayılan açık); Başlangıç paneline "Yönetmelik sihirbazıyla yeni proje".

---

## 7. Yeniden açma ve düzenleme

### 7.1 Giriş noktaları

Dosya › Proje › **Yönetmelik verileri…**; Model ağacında "Yönetmelik verileri" düğümü (çift tık); durum çubuğundaki
`TBDY · DTS 1 · ZD` çipi; Tasarım sekmesi Yönetmelik grubu ("ÇYTHYE 2018 ▾ | Tercihler…, Kombinasyonlar"); bir uyarının
"Düzenle" bağlantısı (doğrudan ilgili alana). Pencere istenen adımda açılır; adım çubuğu serbest gezilir (sıra zorunlu değil).

### 7.2 Mevcut modelle fark

- Açılışta değerler modelden okunur (`bina.json` + `yonetmelik.json`); proje belgesi yoksa (eski dosya, web `.json`) modelden
  çıkarılır, künye boş, adımlar "Varsayılan/Uyarı".
- H_N, kat sayısı ve rüzgâr tablosu artık **modelden** gelir (salt okunur, "modelden" çipi); Adım 1 ön geometrisi gizlenir.
- Alt çubukta birincil düğme **Uygula**; öncesinde "Değişiklikler" listesi: `deprem.zemin_sinifi ZC → ZD`, etkiler
  ("Sonuçlar eskidi; 64 deprem birleşimi yeniden hesaplanacak"). Tek geri alma adımı; sonuç özeti "eski" işaretlenir (D/C
  renkleri soluklaşır, F5 ister) — MIMARI düzenleme akışıyla aynı.
- Akslar artık bilindiği için mütemadi temel "Akslar" listesi gerçek aks adlarıyla açılır; h_govde ≥ L_n/10 gibi geometri
  denetimleri ✓/U olur.

### 7.3 Nesne düzeyi varsayılanlar

Kullanım sınıfı, kaplama, döşeme kalınlığı, duvar değişince sorulur: **Yalnız yeni nesneler** (varsayılan) · **Önceki
varsayılanı kullananlar** (değeri eski varsayılana eşit olan döşemeler/kirişler; elle değiştirilmişler korunur) · **Hepsi**.
Önizleme: "12 döşeme değişecek (Kat 1–4), 3 döşeme elle değiştirilmiş — korunacak".

---

## 8. Yönetmelik şablonları

- **İçerik:** sihirbaz durumunun alt kümesi. Kapsam onay kutuları (kaydederken): Malzemeler ✓, Yükler ✓, Deprem seçenekleri
  (BKS, taşıyıcı sistem, periyot, n, C_t, dışmerkezlik, dolgu) ✓, **Saha değerleri** (S_S, S_1, zemin sınıfı) ☐, **Zemin
  değerleri** (q_em, q_k, k₀, γ) ☐, Temel tipi ve boyutları ✓, Birleşimler ✓, Analiz ✓, Künye ☐ (yalnız "hazırlayan / kontrol
  eden" ✓). Sahaya özgü değerler varsayılan olarak şablona girmez.
- **Biçim:** `*.op4ys` (UTF-8 JSON) `{"tur": "op4-yonetmelik-sablonu", "bicim_surumu": 1, "ad", "aciklama", "yapi_turu",
  "kapsam": [...], "degerler": {...}, "olusturan", "tarih", "motor_surumu"}`; eksik alan → yapı türü varsayılanı.
- **Yer:** kullanıcı `%APPDATA%\Opus Fortis\op4\sablonlar\yonetmelik\`; firma klasörü Ayarlar › Program ayarları'ndan (ağ
  paylaşımı, salt okunur, "firma" rozeti); bir şablon "varsayılan" işaretlenir (yeni projede seçili gelir).
- **Uygulama:** başlıktaki açılır listeden; değişen alanlar "şablon" çipi alır; şablon sonradan değişse proje etkilenmez
  (değerler projeye kopyalanır, `sablon.surum` yalnız iz).
- **Yönetici:** Ekle / Kopyasını ekle / Yeniden adlandır / Sil / İçe aktar / Dışa aktar (op4 liste deseni).
- Doğrulanmamış kütüphane kaydı içeren şablon kaydedilirken uyarı listesi gösterilir.

---

## 9. Dear ImGui uygulama notları

1. **Pencere:** `ImGui::OpenPopup("Yönetmelik Sihirbazı")` + `BeginPopupModal(…, ImGuiWindowFlags_NoResize | NoSavedSettings
   | NoDocking | NoTitleBar)`, boyut 1600 × 944 × DPI (1366 × 768'de ekranın %94'ü, adım çubuğu 56 px simge şeridine
   daralır, sağ etki kartı içerik altına iner). Karartma `ImGuiCol_ModalWindowDimBg` = palet `karartma` %42. Başlık ve alt
   çubuk özel çizim (`ImDrawList`), gövde üç `BeginChild`: `adimlar` (272), `icerik` (kaydırmalı, 984), `etki` (344, kaydırmalı).
2. **Adım çubuğu:** satır başına `InvisibleButton` + `ImDrawList` (daire, ✓/! glifi, bağlantı çizgisi, etkin satır yuvarlak
   dikdörtgen + 3 px şerit); klavye ile Ctrl+1…8. Durumlar `YonetmelikDurumu::adimDurumu(i)` ile her karede (ucuz) hesaplanır.
3. **Alan satırları:** `BeginTable("alanlar", 3, SizingFixedFit)`: etiket 132–176 px · değer · ⓘ/yardımcı metin. Alt simgeli
   etiketler (S_DS, q_em) için küçük yardımcı `MetinAltSimge(const char* "S_{DS}")` (ana yazı + %74 boy, 0,24 em aşağı).
4. **Sayı girişi:** `InputText` + `CallbackCharFilter` (rakam, `,` `.` `-`), odak kaybında yerel ayardan bağımsız çözümleme;
   görüntü `Bicim::sayi(x, ondalik)` (virgül, U+2009 binlik). Birim, `GetItemRectMax()` ile kutunun içine sağdan
   `AddText` (soluk). Hata/uyarı kenarı `PushStyleColor(ImGuiCol_Border)` + `FrameBorderSize 1`.
5. **Segment, kart, çip:** özel bileşenler (`Segment(id, secenekler, &secili)`, `SecimKarti`, `HesapCipi`, `SonucKarosu`);
   hepsi `ImDrawList` + `InvisibleButton`, odak halkası `ImGuiCol_NavHighlight`. Uzun listeler: `BeginCombo` +
   `InputTextWithHint("##ara")` süzgeci (Türkçe büyük/küçük harf: İ/i, I/ı kuralıyla katlama).
6. **Yerel önizleme hesabı:** `tbdy::Spektrum`, `tbdy::Dts`, `tbdy::Bys`, `ts498::KarSk`, `ts498::RuzgarQ` — tablolar
   `bina_kutuphane` yanıtından doldurulur (C++'ta sabit tablo yok). Altın değerler Python'dan üretilip doctest fikstürü olur
   (örn. SS 1,2 / S1 0,35 / ZD → F_S 1,02, F_1 1,95, S_DS 1,224, DTS 1, H_N 12 → BYS 6); `bina_spektrum` ile çapraz denetim.
7. **Grafik:** `ImDrawList::AddPolyline` (2 px × DPI, AA açık), 300 örnek; kesik çizgi için parça parça; ızgara `cizgi2`,
   eksen yazıları tablo rakamlarıyla. Üzerine gelince dikey imleç + `BeginTooltip` (T, S_ae, R_a, S_aR). Seri renkleri
   paletten (`seri1–3`), metinler metin belirteçlerinden.
8. **Durum modeli:** `struct YonetmelikDurumu { Kunye; OnGeometri; Sistem; Malzemeler; Yukler; Deprem; ZeminTemel;
   Birlesim; Analiz; Kaynaklar; Varsayilanlar; }` — `FromBina(json, yonetmelik_json)`, `BinaYamasi() → json`,
   `Dogrula() → vector<Ileti{alan, duzey, metin, kaynak}>`. İleti metinleri motorun hata cümleleriyle aynı tablodan
   (yerelleştirme anahtarı `sihirbaz.<adim>.<alan>.<kural>`).
9. **İş parçacığı:** motor istekleri yardımcı sürece (MIMARI yönlendirmesi: kütüphane, deprem önizleme); yanıtlar UI
   kuyruğuna, `id` eşlemesiyle eski yanıt atılır; gecikme göstergesi grafiğin sağ üstünde küçük döner simge.
10. **Erişilebilirlik ve dil:** her durum simge + metin; bütün metinler yerelleştirme tablosundan (Türkçe / English, MIMARI
    §25.1 Dil ayarları); ondalık ayırıcı ayardan; yazı Inter 400/500/600, 10–18 px × DPI.
11. **Tema:** bütün renkler tek belirteç başlığından (`tema_belirtecleri.h`, taslaktaki `PALET` sözlüğüyle aynı adlar).

---

## 10. Test önerileri

- Motor ↔ sihirbaz eşdeğerliği: her adımın `BinaYamasi()` sonucu `yapi._bina_oku` ile okunur; `B.deprem`, `B.kar`,
  `B.ruzgar`, `B.temeller`, `B.analiz` beklenenle aynı ve `B.uyarilar` sihirbazın "uyarı" listesinin üst kümesi.
- Önizleme: 5 zemin × 7 S_S × 7 S_1 × 3 BKS ızgarasında C++ spektrum = `yapi._spektrum` (1e-9); BYS için 3 sütunun
  bütün sınırları (7; 10,5; … 105 m) ± 1 mm.
- Kar: 9 bölge × rakım {0, 200, 201, 650, 1000, 1001, 1500, 1501} = `kar_Sk`.
- Birleşim sayıları (§4.6 tablosu) `_kombinasyon_listesi` ile.
- Gidiş-dönüş: `yonetmelik.json` + `bina.json` → sihirbaz → değişiklik yok → bayt eşit (D1 sözleşmesi).
- Ekran: `--test-ekran` ile 1920×1080 ve 1366×768 sihirbaz görüntüleri bu taslaklarla gözle karşılaştırılır.

---

## 11. Uyum notları (bugünkü web arayüzü ↔ motor; sihirbaz motoru izler)

| Konu | `docs/bina.js` | Motor | Sihirbaz |
|---|---|---|---|
| BYS önizlemesi | `bysHesapla` DTS 3 ve 4'ü **tek sütunda** (DTS 3 sınırları) toplar | `_bys` üç sütun (DTS 4: 91 / 105 m) | motor (üç sütun) |
| Periyot | normalize ederken `"otomatik"` → `"ampirik"` | varsayılan `"otomatik"` | "Otomatik" seçeneği korunur |
| Tekil temel B, L | 1,6 m | 1,5 m | 1,5 m yazılır |
| Döşeme `g_ek` boşsa | 1,5 kN/m² | 0,0 | kaplama takımı açıkça yazılır |
| Döşeme `h` boşsa | 0,14 | 0,12 | açıkça yazılır |
| S_S/S_1 boşsa | 1,0 / 0,3 yer tutucu | hata | boş + "eksik" |

---

## 12. Açık sorular (kullanıcıya)

**Kararlar (31.10.2026, kullanıcı):**
- **1 Karma yapı:** ilk sürümde desteklenir — motor eleman grubuna / kat bölgesine göre taşıyıcı sistem ve kombinasyon
  kümesi uygular ("kısıtlı" kart kalkar).
- **2 Sahaya özel spektrum:** ilk sürümde — kullanıcı tanımlı T–S_ae tablosu (ZF ve isteğe bağlı her sınıf için); 13'teki
  motor eki (`bina_spektrum`, DTS/BYS tabloları) bununla birlikte yapılır.
- **6 Hareketli yük azaltması (TS 498 Çizelge 7):** ilk sürümde, seçenek olarak.
- **8 Kural ihlalleri:** sihirbaz **engeller** — kurala aykırı seçimde "İleri" kilitlenir; adım çubuğunda "eksik",
  alanın altında neden + yönetmelik maddesi + düzeltme önerisi gösterilir.
- **9 Rüzgâr, 10 Kar:** varsayılan açık.
- Diğerleri açık; önerilen varsayılanlarla ilerlenir.

1. **Karma yapı:** motor tek `sistem` ve tek kombinasyon kümesi uygular; karma yapıda çelik elemanlar TS 500 katsayılarıyla
   (YDKT dayanımı) tahkik edilir. Karma kartı "kısıtlı" olarak mı kalsın, yoksa motora eleman grubuna göre küme eklensin mi?
2. **ZF / sahaya özel spektrum:** ZF seçilince adım "eksik" oluyor. Kullanıcı tanımlı spektrum tablosu (T–S_ae) girişi
   istenir mi? (Motorda yok; eklemeli değişiklik gerekir.)
3. **DD-1 ve DD-4, PGA/PGV:** motor yalnız DD-2 (+ DD-3, λ) kullanır. Diğer düzeyler yalnız rapor için kaydedilsin mi?
4. **Harita hizmeti raporunu içe aktarma:** hangi biçim esas alınsın (PDF'ten kopyalanan metin, kaydedilen PDF)? PDF metin
   çıkarımı için paketlenecek bir Python bileşeni gerekir.
5. **Ön geometri:** yeni projede H_N tahmini sihirbazda kalsın mı (BYS/T_pA önizlemesi için), yoksa Adım 4 model kurulana dek
   "H_N bilinmiyor" mu göstersin? Rijit bodrum (TBDY md. 4.3.2.3) motor tarafından desteklenmiyor — gösterilmesin mi?
6. **Hareketli yük azaltması (TS 498 Çizelge 7):** tablo kütüphanede, motor uygulamıyor. Seçenek olarak eklensin mi?
7. **P-Δ:** motor θ_II'yi denetliyor, β_II'yi uygulamıyor; Adım 7'de yalnız bilgi satırı yeterli mi?
8. **Taşıyıcı sistem kural ihlalleri** (BYS sınırı, DTS–süneklik, A31/C31): motor yalnız uyarıyor. Sihirbaz engellesin mi?
9. **Rüzgâr varsayılanı:** motor ve web arayüzü kapalı başlatıyor; sihirbazda açık önerdim. Onay?
10. **Kar varsayılanı:** Çizelge 3'te en küçük S_k 0,75; "kar yağmayan yer" durumunu kim belirler — her projede açık mı başlasın?
11. **Şablon yeri ve kapsamı:** firma şablonları için ağ klasörü kullanılacak mı; saha değerlerinin şablona girmemesi uygun mu?
12. **Mevcut döşemelere uygulama** (§7.3) varsayılanı "Yalnız yeni nesneler" mi olsun?
13. **Motor eki onayı:** `kutuphane()["deprem"]` içine DTS/BYS/spektrum tabloları ve yeni `bina_spektrum` köprü işlemi.
14. **Varsayılan kaplama:** `sap-seramik-siva` doğrulanmamış (seramik birim ağırlığı); varsayılan `sap-parke-siva` (doğrulanmış)
    mı olsun, yoksa seramik değeri TS EN 1991-1-1 Ek A ile doğrulanıp kayıt düzeltilsin mi?
15. **Birim sistemi:** motor yalnız kN·m çalışır; Dil ayarlarındaki birim sistemi sihirbazda yalnız gösterimi mi değiştirsin?

**Doğrulanmalı işaretli değerler (kaynak tarafında):** TS 498:2021 Ek 1 il/ilçe kar bölgeleri (OCR aktarımı); TS EN 1991-1-3
μ₁ ve C_e (motor `dogrulandi: false`); seramik kaplama; "depo" hareketli yükü; Tablo 4.3 ↔ Çizelge 6 "yorum" eşlemeleri
(hastane-mutfak, atölye-hafif, kütüphane, koridor-genel, merdiven-umumi); TBDY 7.2.5 "en az C25" notu; k₀ zemin sınıfı
eşlemesi (öğretici); q_k = 3·q_em varsayımı (yönetmelik değeri değil).

---

## 13. Görsellerin üretimi

`python3 uret.py` (bu klasör; Pillow + depodaki motor). `tuval.py` Atölye çizim kütüphanesinin kopyasıdır ve **sabit renk
içermez**; bütün renkler `uret.py` başındaki `PALETLER` / `PALET_SEC` sözlüğündendir. Modernize palet gelince yalnız o sözlük
(ya da `PALET_SEC = "…"` satırı) değişir ve görseller yeniden üretilir. Grafik seri renkleri (`seri1–3`) renk doğrulayıcısından
geçmiştir (komşu çiftlerde CVD ΔE ≥ 9,2; `seri3` düşük kontrastlı olduğu için kesik çizgi + doğrudan etiketle kullanılır).
Yazı Inter (op4/kimlik), kod blokları eş aralıklı sistem yazısı; Türkçe glifler (İ ı ş ğ ü ö ç) 1:1 büyütmede denetlendi.
