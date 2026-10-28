# Matris Öğren — tasarım belgesi haritası

Kod yorumları bir tasarım belgesinin bölümlerine başvurur. Örnekler: `docs/bina.js` "Veri şeması: tasarım belgesi §3 (bina JSON)
ve §4 (çıktı "veri"); alan adları bağlayıcıdır", `rapor.py` "Statik hesap raporu (tasarım belgesi §14.1)", `docs/aks_sistemi.js`
"Aks verisi (§19.1)". Özgün belge depoda yoktur. Bu dosya o numaralandırmanın **koddan ve testlerden yeniden kurulmuş haritasıdır**:
her bölümün konusu, bağlayıcı kararları, onu uygulayan dosyalar ve kilitleyen testler.

- Kod ile bu dosya çelişirse kod ve testler geçerlidir; bu dosya onlara göre düzeltilir.
- Yeni bir özellik eklenirken önce buraya bölümü (ya da alt bölümü) yazılır, kod yorumu o numaraya başvurur.
- Aynı "§" işareti iki başka numaralandırmada da geçer, karıştırılmamalıdır: `dersler/BICIM.md §1–§8` (ders biçimi) ve
  `rapor.py` içindeki "§1–§14" (statik raporun kendi bölüm numaraları, bkz. §14.1).
- (*çıkarım*) işaretli bölümlere kodda doğrudan başvuru yoktur; içerik koddaki davranıştan çıkarılmıştır.

Kullanıcı kılavuzu: [`KULLANIM.md`](KULLANIM.md) (§3.9 Python, §3.10–3.12 Bina sayfası). Masaüstü sözleşmesi:
[`masaustu/README.md`](masaustu/README.md).

---

## Dilimler

Bina özelliği "dilim" adlı aşamalarla geldi; yorumlardaki "Dilim N" bunlardır.

| Dilim | Kapsam | Başlıca dosyalar |
|---|---|---|
| 1 | Bina sayfası: aks–kat modeli, TS 498 yükleri, döşeme → kiriş → kolon → temel → zemin yük akışı, G/Q çözümü, yük akışı ekranları | `yapi.py`, `yapi_veri.py`, `docs/bina.js` |
| 2 | Yükler ve birleşimler: kar, rüzgâr, TBDY 2018 eşdeğer deprem, çatlamış rijitlik, TS 500 / ÇYTHYE / TBDY kombinasyon kümeleri, zarf | `yapi.py`, `yapi_veri.py` |
| 3 | Kesit tahkikleri (TS 500, ÇYTHYE 2018), Tasarım sekmesi, eleman ayrıntısı, N–M eğrileri | `tasarim.py`, `docs/bina.js` |
| 4f | Kablolama: `window.MatrisBina` iç API'si, araç kutuları, sağ tık, ölçüm, rapor / IFC / tablolar / ısı haritası, masaüstü komutları (1. aşama); aks tabanlı çizim (2. aşama, `docs/bina_cizim.js`) | `docs/bina.js`, `docs/bina_cizim.js` ve §14–§19 modülleri |

## Sürüm şeması

| Nesne | Alan | Değer | Anlamı |
|---|---|---|---|
| Bina girdisi | `surum` | 1 (eski kayıtlarda 2) | Aks–kat modeli: `kolonlar`, `kirisler`, `dosemeler`, `duvarlar` (§3). Motor `yapi.py`. |
| Bina girdisi | `surum` | 3 | Genel düğüm–çubuk–panel modeli: `dugumler`, `cubuklar`, `paneller`, `mesnetler`, `kren`, `uretecler`, `aks_sistemleri` (§12, §19). Motor `yapi_serbest.py`. |
| Çözüm verisi | `veri.surum` | 2 | Aks–kat çözümü (`yapi.bina_coz`, §4). |
| Çözüm verisi | `veri.surum`, `veri.model` | 3, `"genel"` | Genel model çözümü (`yapi_serbest.bina_coz`, §4). |
| Proje dosyası | `tur`, `surum` | `"matris-proje"` | `.matris`: `{tur, surum, uygulama, kaydedildi, bina, gorunum, arac_yerlesimi}`; düz bina JSON'u da açılır. |

**Yönlendirme kuralı** (tek kural; Python `yapi._serbest_mi`, arayüz `s3Var`, çizim `genelMi`): bina **genel modeldir** ⇔
`int(surum) ≥ 3`, ya da `cubuklar`, `paneller`, `dugumler`, `mesnetler`, `uretecler` listelerinden biri boş değil, ya da bir
`ek_yukler` kaydının `dugum` değeri bir REF sözlüğü (`{"aks": [..], "z": ..}`) ya da türü `cubuk` / `panel`. Aks–kat düğüm yükü
`{"tur": "dugum", "aks": ["B", "2"], "kat": 1}` ve boş listeler genel model yapmaz. Doğruluk tablosu
`testler/test_bina_kablolama.py` (`C1_TABLOSU`) ve `testler/test_yapi_serbest.py`'de iki yönden kilitlidir.

---

## §1 Amaç ve ilkeler (*çıkarım*)

Öğretim ve ön boyutlandırma aracı. İlkeler: her hesap adım adım anlatılır ve aynı işi yapan Python kodu verilir; kütüphane
değerleri `kaynak` ve `dogrulandi` taşır (`yapi_veri.py`); hatalar öğreticidir (`MatrisHatasi` ne yapılacağını söyler); motor
tarayıcıda (Pyodide) ve masaüstünde çevrimdışı çalışır; başka yazılım ürünlerinin adı geçmez (`testler/test_program_adi_yok.py`).

## §2 Koordinatlar ve eksenler

- **Bina sistemi:** X sağa (harfli akslar), Y plan derinliği (sayılı akslar), Z yukarı (kot). Birimler kN, m.
- **Motor** (`sonlu_eleman` `cerceve3b`) Y yukarı çalışır; dönüşüm tek yerdedir: `yapi._motor_koordinat` / `_bina_vek`
  (`x_m = X, y_m = Z, z_m = −Y`). Sonuçlar bina koordinatında döner.
- **Yerel eksenler:** x′ i → j; yatay ya da eğik çubukta y′ çubuğu içeren düşey düzlemde yukarı, z′ = x′ × y′; düşey çubukta
  y′ = −X, z′ = −Y (yukarı giden kolon). `aci` x′ etrafında döndürür; aci = 0'da kesitin h boyutu (güçlü eksen) y′ doğrultusundadır.
- **Kolon `yon` takası:** aks–kat kolonunda `yon: "x"` → aci 0, `"y"` → aci 90 (motor eksenleri sabit, I'lar takas edilir).
- Uygulayanlar: `yapi.py`, `docs/model_ops.js`, `docs/aks_sistemi.js`, `docs/ifc_disari.js` (IFC de Z yukarı; bina koordinatı
  doğrudan yazılır), `alan.py` (lif işaretleri). İşaret kuralları `testler/test_alan.py` ve `testler/js/isi_haritasi.test.js`'te kilitli.

## §3 Bina girdisi (JSON)

- **surum 1 (aks–kat):** şema `yapi.py` modül belgesindedir: `akslar.x/y`, `katlar` (0 = temel), `malzemeler` (kütüphane adı),
  `kesitler` (`dikdortgen` b/h ya da `profil`), `kolonlar` (`aks`, `kat`, `kesit`, `yon`), `kirisler` (`bas`/`son` aynı aks çizgisinde),
  `dosemeler` (tek hücre, `kullanim` / `q`, `g_ek`, `dagitim`), `duvarlar`, `ek_yukler` (`kiris`, `dugum`, `doseme`), `temeller`
  (§13), `yuk_durumlari`, `deprem`, `kombinasyon_kumesi`, `analiz`.
- **surum 3 eki (genel model):** `akslar.z` (Z aksları; `kat` işaretlisi kat seviyesidir), `aks_sistemleri`, `dugumler`, `cubuklar`,
  `paneller`, `mesnetler`, `kren`, `uretecler`, REF'li `ek_yukler`. Şema `yapi_serbest.py` modül belgesinde ve KULLANIM.md §3.9.1'de.
- Alan adları **bağlayıcıdır**: arayüz, köprü, rapor, tablolar ve IFC aynı adları okur.

## §4 Çözüm verisi (`veri`)

- **surum 2 (aks–kat, `yapi.bina_coz`):** `bina`, `ag` (düğümler, elemanlar, temel), `yukler` (döşeme payları, kirişler, kolonlar),
  `durumlar`, `kombinasyonlar`, `sonuclar`, `zarf`, `akis` (kolonlar, temeller, korunum, sankey), `deprem`, `ruzgar`, `kar`,
  `kutle_merkezi`, `rijitlik_merkezi`, `tasarim` (§11), `temel` (§13), `ozet`, `cozum_kimligi`.
- **surum 3 "genel" (`yapi_serbest.bina_coz`):** aynı anahtarlar + `model: "genel"`, `ag.cubuklar`, `ag.paneller`,
  `ag.dugumler[].tur` (aks, bolme, kesisim, ic, efendi), `yukler.paneller` / `yukler.cubuklar`, `akis.mesnetler` (açık mesnetler:
  dugum, adres, tip, N_G, N_Q, MX, MY), `kren`, `yalniz_cekme`, `bina.seviyeler`, `uyarilar`.
- **akis.temeller** yalnız temel mesnetlerini (kaynak `temel`: B, L, h, N_temel) taşır; açık `mesnetler` kayıtları `akis.mesnetler`'dedir.
- Köprü önbelleği: `cozum_kimligi` (normalize girdinin özeti; `yapi.cozum_kimligi(bina)` çözmeden verir); son çözümlerin iç paketi
  (`ic`) tembel kombinasyon, tasarım ayrıntısı, kesit önerisi, rapor, tablolar ve ısı haritası için saklanır.

## §5, §7–§10 Yükler, ağ, deprem, birleşimler (*çıkarım*)

Kodda bu numaralarla başvuru yoktur (rapor.py'deki §5–§10 raporun kendi bölümleridir). İçerik Dilim 1–2'dir ve `yapi.py`'de
yaşar: TS 498:2021 yükleri ve TS 500 md. 11.4.3 45° dağıtımı (döşeme → kiriş), `cerceve3b` ağı ve rijit diyafram (efendi düğüm),
yük durumları G, Q, S, W±X/Y, EX±, EY±, EZ, kren K; TBDY 2018 eşdeğer deprem yükü (spektrum, R/D, T_pA / Rayleigh, dışmerkezlik,
η_bi, göreli kat ötelemesi), çatlamış kesit (Tablo 4.2) ve iki K; kombinasyon kümeleri `ts500`, `cythye_ydkt`, `cythye_gkt`,
süperpozisyon ve zarf; Bina sayfasının yük, deprem ve sonuç sekmeleri. Ayrıntı: KULLANIM.md §3.9.

## §6 Kütüphane

`yapi_veri.py` (salt veri): beton, donatı, yapı çeliği; IPE / HEA / HEB profilleri (Iy güçlü eksen); TS 498 hareketli yükleri,
birim ağırlıklar, duvar ve kaplama takımları; TBDY tabloları; kombinasyon satırları. Her kayıt `kaynak` ve `dogrulandi` taşır;
`yapi.dogrulanmamis_kayitlar()` doğrulanmamışları listeler. Köprü `bina_kutuphane` arayüze verir (`docs/bina.js`
`kutuphaneNormalize`).

## §11 Kesit tahkikleri (tasarım)

- `tasarim.py`: TS 500 betonarme kiriş (eğilme, kesme) ve kolon (N–M etkileşimi, e_min, eş zamanlı noktalar, TBDY 7.3 sınırları);
  ÇYTHYE 2018 çelik (YDKT / GKT; eğilme, YBB, basınç, kesme, çekme, bileşik etki); basit kesitler (kutu, boru, korniyer, U).
- Kayıt (`veri.tasarim.elemanlar[]`): `{no, tur, adres, kesit, dc, durum, belirleyen, kontroller, ozet}`; genel modelde ek `cubuk`,
  `grup`, `L`, `varsayimlar`, `kaynak`; `kontroller[0]` D/C'yi belirleyen satır. D/C dayanım satırlarının en büyüğüdür; yönetmelik
  alt/üst sınır koşulları (`kosul: true`) yalnız sağlanmadığında belirler.
- Arayüz: Tasarım sekmesi (D/C bantları, süzgeç, kayıt ↔ sahne eşlemesi), `bina_eleman_tasarim` (anlatımlı ayrıntı; genel modelde
  `tur: "cubuk"` ve çubuk numarası).
- **Kesit önerisi:** `yapi_serbest.kesit_oner` (köprü `bina_kesit_oner`). Yanıt alanları: `cubuk, tur, kesit, oneri, sistem, malzeme,
  b, h, kaynak, dc_once` (Tasarım tablosunda görünen D/C), `dc_oneri, degisim` (büyüt / küçült / aynı), `uygula` (`{ad, tanim, yeni}`
  ya da null); üst düzeyde `uyarilar`. Aks–kat çözümü genel motorla bir kez yeniden çözülür. Arayüz: sağ tık "Kesit öner" ve
  "Kesit öner ve uygula" komutu ("Hepsini uygula" yeniden çözer).

## §12 Genel 3B model (surum 3)

`docs/model_ops.js` (saf düzenleme işlemleri: genelleştirme, çubuk / panel / mesnet ekleme, böl, birleştir, taşı, döndür, ayna,
dizi, üreteçler) ve `yapi_serbest.py` (motor). Aks–kat binası aynı kurallarla genel listeye çevrilir (`genellestir`); iki yol aynı
tepkileri ve iç kuvvetleri verir (`testler/test_yapi_serbest.py`).

### 12.1 Düğüm başvurusu (REF)

`{"dugum": no}`, `{"aks": [x, y], "kat": k}` (aks–kat), `{"X", "Y", "Z"}` (yalnız geriye uyum); §19.2 biçimleri. Aynı konuma
(1 mm) düşen başvurular tek düğümdür.

### 12.2 Çubuk türleri, yükler, paneller

- Çubuk `tur`: kolon, kiris, capraz, makas-ust, makas-alt, makas-dikme, makas-diyagonal, asik, kren, bag, diger. Uç serbestlikleri
  `serbest: {i: [...], j: [...]}` (N, Vy, Vz, T, My, Mz), `yalniz_cekme`, `K` ([güçlü, zayıf]), `Lb`, `aci`, `duvar`.
- Panel `tur`: doseme, cati, cephe; `dagitim`: iki (açıortay bölgeleri; dikdörtgende 45° kuralı), tek-13, tek-24, yok; kalınlık 0
  taşıyıcı olmayan kaplamadır (sac). Kar μ1 panel eğiminden, rüzgâr panel normaline (c_p otomatik ya da dört değer).
- Ek yükler: çubuk (yayılı / tekil, global ya da yerel yön), düğüm (REF, FX…MZ), panel `{tur: "panel", panel, durum: G | Q | S, p}`
  (kN/m², aşağı +; eski `{g, q}` de okunur). Kren: `kren` kaydı → K durumu, konum başına alt durumlar, hareketli yük birleşimlerine eklenir.
- Yalnız çekme çubuğu varsa birleşimler süperpozisyonla değil, doğrudan ve yinelemeli çözülür.

### 12.3 Temel kuralı

En alt Z seviyesindeki (kat 0) **bütün aks kesişimleri** — hangi aks sisteminde olursa olsun — `temeller.mesnet` ile mesnetlenir
(açık `mesnetler` kaydı yoksa); bölme, kesişim ve koordinat düğümleri asla. **Mütemadi ve radye temel genel modelde çözülmez:** motor
öğretici hata verir (`TEMEL_TIP_HATASI`), arayüz genel modele geçerken onayla tekil temele çevirir, rapor "analiz yapılmadı" notu
düşer. Sınır: genel modelde `EN_FAZLA_SD = 2000` (aks sınırı yok); aks–kat modelinde 12 × 12 aks, 12 kat, 1500 SD.

## §13 Temeller

`temel.py`: mütemadi temel (seçilen aks çizgileri boyunca ters T temel kirişleri, Winkler düğüm yayları k_z = k0·B·l, tabla dönme yayı
k0·B³/12·l) ve radye (iki doğrultulu ızgara, şerit I = b·h³/12, J ≈ b·h³/6; isteğe bağlı aks kirişleri); taban basıncı, oturma,
farklı oturma, TS 500 / TBDY 16.8 zemin denetimleri, zımbalama, donatı. Tekil temel (B × L; ankastre / mafsal / elastik) `yapi.py`'dedir.
Çıktı `veri.temel`; anlatımda "Temel ve zemin" adımı; arayüzde Temel sekmesi ve temel tipi seçici (`docs/bina.js`).

## §14 Çıktılar

### 14.1 Statik hesap raporu

`rapor.py` (`statik_rapor(bina, veri, secenek)`, `dosya_adi`; köprü `bina_rapor`). Tek dosya HTML5, gömülü CSS, A4 yazdırma, dış
kaynak yok. Bölüm sırası sabit: 1 kapak/künye, 2 yönetmelikler, 3 genel bilgiler, 4 malzemeler, 5 kesitler, 6 yükler, 7 deprem,
8 analiz yöntemi, 9 yük birleşimleri, 10 analiz sonuçları, 11 betonarme, 12 çelik, 13 temel, 14 sonuç; metraj özeti, Ek A düğümler,
Ek B çubuklar, Ek C seçilen tablolar. Veri olmayan bölüm "Bu modelde uygulanmadı" notuyla kalır.

### 14.2 IFC

`docs/ifc_disari.js` (`window.MatrisIFC`): IFC4 STEP; proje → yapı → katlar, aks ızgaraları (ek sistemler dahil), fiziksel model
(kolon, kiriş, üye, döşeme, kaplama, temel), malzeme ve profil setleri, isteğe bağlı yapısal analiz modeli, G / Q yükleri ve D/C
özellikleri. GlobalId'ler belirlenimci (aynı modelden aynı kimlik).

## §15 Tablolar ve metraj

### 15.1 TABLO şeması

`tablolar.py` modül belgesi: `{ad, baslik, grup, sutunlar: [{ad, baslik, birim, tur, duzenlenebilir, ...}], satirlar: [{degerler,
yol?, hucre?, ozet?}], toplam?, aciklama, kaynak}`. `yol` bina JSON'undaki gerçek alana işaret eder (seçiciler `{"no": 3}`,
`{"ad": "A"}`); `degisiklikleri_uygula` kopyaya yazar, `aks_yeniden_adlandir` bağlı bütün başvuruları günceller. Rapor ve arayüz aynı
tabloları kullanır; köprü `bina_tablolar`. Metraj eğitim amaçlı yaklaşık keşiftir (birim fiyat yok).

### 15.3 Tablo editörü

`docs/tablo_editoru.js` (`window.MatrisTablo`): sarı (düzenlenmiş) hücreler, "Uygula" (tek geri al adımı), sekmeyle ayrılmış
yapıştırma, CSV dışa aktarma (BOM, `;`, ondalık virgül), rapora tablo seçimi. Masaüstü "Tablolar (.csv)" bütün tabloları tek CSV'ye
yazar; CSV dosyası içe aktarılmaz.

## §16 Isı haritaları

### 16.1 Çubuk alanları

`alan.eleman_alanlari(ic, durum, ...)`: istasyonlarda N, Vy, Vz, T, My, Mz, eğri yer değiştirme (M/EI'nin integrali), lif
gerilmeleri, von Mises, kullanım oranı; kombinasyon = durumların katsayılı toplamı, zarf = istasyon bazında en büyük / en küçük
(yeniden çözüm yok). İşaret: σ(y, z) = N/A − Mz·y/Iz − My·z/Iy.

### 16.2 Panel ve radye alanları

`alan.panel_alanlari`: dikdörtgen döşeme (aks–kat döşemesi ya da genel modelde yatay, dört köşeli, eksenlere paralel `doseme`
paneli) için Navier plağı (w, m_x, m_y) ve 45° yük payı poligonları. `alan.radye_alani` (c): radye / mütemadi temelde Winkler
oturması w ve taban basıncı p = k0·w. Köprü `bina_alan`; eleman bilgi paneli için `eleman_bilgi_alani` (§17.2).

### 16.4 Görüntüleyici

`docs/isi_haritasi.js` (`window.MatrisIsi`): WebGL (yoksa SVG) yapı görünümü ve tek eleman görünümü (kesit gerilme haritası,
tarafsız eksen, boyunca grafikler).

## §17 Bina sayfası etkileşimi

### 17.1 Araç kutuları ve ölçme

`docs/arac_kutusu.js` (`window.MatrisArac`): komut kaydı (`komutKaydet`, `baglar`), katalog, yüzen / sürüklenen / gruplanan
kutular, Özelleştir, hazır yerleşimler, tek kaynaklı kısayollar (`kisayollar()`; Yardım sayfasındaki tablo ve Bina sayfasındaki `?`
penceresi bundan üretilir), kullanılamayan komutun nedeni. `docs/olcum.js` (`window.MatrisOlcum`): uzaklık, açı, alan, kot farkı,
koordinat, eleman boyu; çizim kipinde yalnız aks kesişimleri ve düğümlere yakalama (§19), ölçüm kipinde orta nokta ve izdüşüm de.

### 17.2 Sağ tık ve eleman bilgisi

`docs/eleman_bilgi.js` (`window.MatrisBilgi`): bağlam menüsü (sağ tık, uzun basma, Shift+F10) ve iğnelenebilir sekmeli denetçi
(geometri, kesit, bağlantı, yükler, iç kuvvetler, yer değiştirme, tasarım, metraj, yük yolu). İstemci tarafı model bina + `veri`'den
türetilir; çözümden sonra köprü `bina_eleman_bilgi` (`{cozum_kimligi, tur: cubuk | kolon | kiris | fe, no, durum?}` → `{paket:
{sekmeler: {ic, yer}, ...}}`) "Motor ayrıntısı" bölümlerini ekler (istasyon iç kuvvetleri, en büyük değerler, uç yer değiştirmeleri).

### 17.3 Tam ekran ve yerleşim (*çıkarım*)

`docs/bina.js`: ⛶ / F tam ekran (Esc ya da F çıkar), daraltılabilir araç çubuğu ve özellik paneli, sonuçlar sağ panelde ya da alt
çekmecede, sürüklenen ayırıcılar, telefonda alt şerit. Kutuların sahneyi örtmemesi için kenar payları (`kenarPaylari`), "Sığdır"
modeli kutuların arasına yerleştirir.

## §18 Masaüstü sürümü (*çıkarım*)

`masaustu/` (masaüstü çatısının adı kullanıcıya görünen metinlerde geçmez): `docs/` aynı kodla çevrimdışı paketlenir, Python motoru
programla gelir. Türkçe menü (`masaustu/lib/menu.js`), `.matris` dosyaları, son dosyalar, çoklu pencere, otomatik kayıt ve kurtarma,
yerel kaydet / aç, rapordan PDF. Sayfa ↔ masaüstü sözleşmesi (`window.MatrisDosya`, `masaustu-komut`, `masaustu-dosya-acildi`) ve
komut tablosu: `masaustu/README.md`. CSP satır içi olay özniteliklerini (`onclick=` …) çalıştırmaz; `docs/` HTML'inde kullanılmaz.

## §19 Aks sistemi tabanlı modelleme

**Karar:** çizim yalnız aks kesişimleri (ve mevcut çubukların bölme / kesişim noktaları) arasındadır; serbest koordinatlı düğüm ve
serbest çizim komutu yoktur. Aks taşınınca ona bağlı bütün düğüm ve elemanlar taşınır (konumlar her çözümde akslardan hesaplanır).

### 19.1 Aks verisi

`akslar: {x: [{ad, konum, tur?, gorunur?, balon?}], y: [...], z: [{ad, konum, kat?}]}`; `akslar.z` tek kaynaktır: `kat: n` taşıyan Z
aksının konumu kat n'nin kotudur (`katlar` eşlenir). `aks_sistemleri`: döndürülmüş / ötelenmiş kartezyen (`x`, `y`) ya da silindirik
(`r`, `teta`) ek sistemler; `z: null` ise GLOBAL Z aksları. Uygulayan: `docs/aks_sistemi.js` (`window.MatrisAks`: sihirbaz, aks
düzenleyici, sahne katmanı), `yapi_serbest._akslari_oku`.

### 19.2 Düğüm başvurusu

`{"aks": ["B", "3"], "z": "Saçak"}` (GLOBAL), `{"sistem": "KANAT-B", "aks": ["C", "2"], "z": "±0.00"}` (ek sistem; silindirikte
`aks = [r, teta]`), `{"aks": ["A", "1"], "kat": k}` (eski), `{"dugum": no}` → `dugumler` kaydı: `{no, tur: "bolme", cubuk_i, cubuk_j,
oran}`, `{no, tur: "kesisim", a: [REF, REF], b: [REF, REF]}` ya da `{no, X, Y, Z}` (yalnız geriye uyum). Kayıtsız `{"dugum": no}`
(no < 100000) eski aks–kat numarasıdır: no = 1000·kat + 20·ix + iy + 1.

### 19.3 Tablo ve düzlem seçici

Aks verisi tablosu (`tablolar.py` "Akslar" / "Aks sistemleri"; ad değişince bağlı başvurular güncellenir) ve düzlem seçici: planda
Z aksları (kat dışı Saçak, Mahya, Kren dahil), önden cephede Y aksları, yandan kesitte X aksları; PgUp / PgDn komşu düzleme geçer.
Çizim araçları: `docs/bina_cizim.js` (çubuk çiz, hızlı kolon / kiriş / çapraz / panel, eğik çubuk, makas, beşik çerçeve, aşık,
kren yolu, mesnet, yük ata, düzenleme ve değiştirme komutları).
