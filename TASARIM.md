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
- **akis.temeller** yalnız tekil temel mesnetlerini (kaynak `temel`: B, L, h, N_temel) taşır (mütemadi / radyede boş); açık `mesnetler`
  kayıtları `akis.mesnetler`'dedir (yaylı mesnette `tip: "yay"`, `yay: {kx…krz}` bina eksenlerinde).
- **akis.sankey** kenarları `{kaynak, hedef, durum, kN, tur}`: `tur` `panel-cubuk` (`P{n}` → `Ç{n}`), `cubuk-cubuk`, `cubuk-mesnet`
  (`M{düğüm}`), `dugum-cubuk` (`D{düğüm}`), `dugum-mesnet`. Düğüm kuralı: her durumda ve her çubuk ucu düğümünde girenler (düğüme
  aşağı kuvvet veren çubuklar, düğüm yükü) çıkanlara (yukarı tutan çubuklar, mesnet / yay tepkisi) oranla bölünür; mütemadi / radye
  ağının düğümünde tek çıkış `M{n}`'dir. Durum başına en çok 600 panel ve 600 öteki kenar (kesilirse `akis.sankey_kesildi`); `tur`'suz
  eski kayıt `panel-cubuk` sayılır.
- **durumlar[d] / sonuclar[k]**: yanıta yazılmayan yaylar (mütemadi / radye temel ağı) varsa `yay_ozet` {FX…MZ} (bina eksenlerinde
  toplamları); yazılan `yaylar` kayıtları `tur` taşıyabilir: `yay-mesnet` (yaylı açık mesnet), `diyafram-mesnet` (rijit diyaframlı
  seviyedeki mesnedin ceza yayı); türsüz kayıt Winkler / elastik temel yayıdır. Σ tepki = Σ `tepkiler` + Σ yazılan yaylar (motor →
  bina: Fx→FX, Fz→−FY, Fy→FZ, Mx→MX, Mz→−MY, My→MZ) + `yay_ozet`.
- **yukler.eylemler** `{durum: {cubuklar, dugumler, G_carpani?}}`: rüzgâr, deprem ve kren durumlarının yükleri (IFC için; genel modelde
  çubuk yayılı / tekil yükleri, iki modelde düğüm kuvvetleri, EZ'de G çarpanı). **temel.oz_yuk** `{elemanlar: [{no, q}], dugumler:
  [{dugum, P}], W}`: temel öz ağırlığının temel.py'nin eklediği yükleri (Σq·L + ΣP = W).
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

- `tasarim.py`: TS 500 betonarme kiriş (eğilme, kesme) ve kolon (N–M etkileşimi, e_min, eş zamanlı noktalar, iki eksenli eğilmede
  Bresler, TBDY 7.3 sınırları); ÇYTHYE 2018 çelik (YDKT / GKT; eğilme, YBB, basınç, kesme, çekme, bileşik etki); basit kesitler (kutu,
  boru, korniyer, U). `kesit_sinifi` basit kesit adını da çözer (Tablo 5.1A/B parça oranları: `{profil, egilme, basinc, parcalar,
  kaynak}`).
- Genel modelin betonarme kolonu aks–kat ile aynı tahkiki alır: iki eksenli eğilme (Bresler) satırı D/C'ye girer; özet `yon`, `bX`/`bY`
  (bina X/Y izdüşümleri, 90° döndürülmüş kolonda takaslı) ve `N_max`/`N_min` (birleşim başına alt uç N'si) aks–kat kuralındadır.
- Kayıt (`veri.tasarim.elemanlar[]`): `{no, tur, adres, kesit, dc, durum, belirleyen, kontroller, ozet}`; genel modelde ek `cubuk`,
  `grup`, `L`, `varsayimlar`, `kaynak`; `kontroller[0]` D/C'yi belirleyen satır. D/C dayanım satırlarının en büyüğüdür; yönetmelik
  alt/üst sınır koşulları (`kosul: true`) yalnız sağlanmadığında belirler.
- Arayüz: Tasarım sekmesi (D/C bantları, süzgeç, kayıt ↔ sahne eşlemesi), `bina_eleman_tasarim` (anlatımlı ayrıntı; genel modelde
  `tur: "cubuk"` ve çubuk numarası).
- **Kesit önerisi:** `yapi_serbest.kesit_oner` (köprü `bina_kesit_oner`). Yanıt alanları: `cubuk, tur, kesit, oneri, sistem, malzeme,
  b, h, kaynak, dc_once` (Tasarım tablosunda görünen D/C), `dc_oneri` (mevcut iç kuvvetlerle tahmin), `degisim` (büyüt / küçült / aynı / donatı: betonarme
  kolonda b × h aynı, gerekli ρ büyük), `uygula` (`{ad, tanim, yeni, ek_kesitler?}` ya da null), `gerekce` (metin listesi), `dc_sonra`
  (`yinele` > 0 ise yeniden çözümdeki D/C, yoksa `dc_oneri`); üst düzeyde `dc_sonra`, `donati_azaltma` ve `uyarilar` (yakınsamadıysa
  D/C > 1 kalan çubuklar). `yinele` (en çok 3): 0. tur bütün önerileri uygular, sonraki turlar yalnız D/C > 1 grupları büyütür. Aks–kat çözümü genel motorla (gerçek temelle) bir kez yeniden çözülür. Parçalı aks–kat elemanı tek öneridir (`cubuklar`, `kaynak.parca`
  > 1; `dc_oneri` parçaların en büyüğü); `grup: true` üye listesine tek grup önerisi verir (`grup {kesit, tur, uye}`); depremli
  `yinele` yanıtı `oteleme {sinir, once, sonra}` taşır ve öneri göreli kat ötelemesi sınırını aştırmaz; köprü yanıtında `sure_ms`.
  Arayüz: "Kesit öner ve uygula" komutu (sağ tıkta tek eleman; araç kutusunda ve masaüstü Tasarım menüsünde seçim ya da bütün model;
  "Kesit grubuna uygula (N çubuk)"; "Hepsini uygula" yeniden çözer, ötelemeyi önce → sonra yazar, bekleme notunda süre tahmini).

## §12 Genel 3B model (surum 3)

`docs/model_ops.js` (saf düzenleme işlemleri: genelleştirme, çubuk / panel / mesnet ekleme, böl, birleştir, taşı, döndür, ayna,
dizi, üreteçler) ve `yapi_serbest.py` (motor). Aks–kat binası aynı kurallarla genel listeye çevrilir (`genellestir`); iki yol aynı
tepkileri ve iç kuvvetleri verir (`testler/test_yapi_serbest.py`).

### 12.1 Düğüm başvurusu (REF)

`{"dugum": no}`, `{"aks": [x, y], "kat": k}` (aks–kat), `{"X", "Y", "Z"}` (yalnız geriye uyum); §19.2 biçimleri. Aynı konuma
(1 mm) düşen başvurular tek düğümdür.

### 12.2 Çubuk türleri, yükler, paneller

- Çubuk `tur`: kolon, kiris, capraz, makas-ust, makas-alt, makas-dikme, makas-diyagonal, asik, kren, bag, diger. Uç serbestlikleri
  `serbest: {i: [...], j: [...]}` (N, Vy, Vz, T, My, Mz), `yalniz_cekme`, `K` ([güçlü, zayıf]), `Lb`, `aci`, `duvar` (duvar taşıyabilen
  türler kiris, bag, diger). Türlerin Türkçe adı tek sözlüktür (`yapi_serbest.TUR_ADI`, `tablolar.TUR_ADI`, `rapor.TUR_ADI`: kiriş,
  çapraz, makas üst başlık, makas alt başlık, makas dikmesi, makas diyagonali, aşık, kren kirişi, bağ, diğer); motor adresi
  `Ç{no} ({TUR_ADI[tur]})`, makine `tur` alanları değişmez.
- Makas üreteci: mafsallı gövdede `yanal_tutma` (`"uc-dikme"` varsayılan: uç dikmeleri, Warren'ın ilk / son diyagonali ve K makasın ara
  dikmeleri moment sürekli; `"yok"`: bütün gövde mafsallı) düzlem dışı mekanizmayı önler.
- Panel `tur`: doseme, cati, cephe; `dagitim`: iki (açıortay bölgeleri; dikdörtgende 45° kuralı), tek-13, tek-24, yok; kalınlık 0
  taşıyıcı olmayan kaplamadır (sac). Kar μ1 panel eğiminden, rüzgâr panel normaline (c_p otomatik ya da dört değer).
- Ek yükler: çubuk (yayılı / tekil, global ya da yerel yön), düğüm (REF, FX…MZ), panel `{tur: "panel", panel, durum: G | Q | S, p}`
  (kN/m², aşağı +; eski `{g, q}` de okunur). Kren: `kren` kaydı → K durumu, konum başına alt durumlar, hareketli yük birleşimlerine eklenir.
- Yalnız çekme çubuğu varsa birleşimler süperpozisyonla değil, doğrudan ve yinelemeli çözülür.

### 12.3 Temel kuralı

**Temel düğümleri:** en alt Z seviyesindeki (kat 0), açık `mesnetler` kaydı olmayan ve en az bir çubuk taşıyan **aks kesişimleri** —
hangi aks sisteminde olursa olsun; bölme, kesişim ve koordinat düğümleri asla.

- **Tekil:** temel düğümleri `temeller.mesnet` ile nokta mesnettir (B × L kaydı, `ozel` ek sistemde `{sistem, aks}`); çözümde
  `veri.temel = temel.tekil_ozet(...)`.
- **Mütemadi ve radye:** sabit mesnet yoktur; düğümler `temel.py`'nin Winkler ağına bağlanır. Ağ **GLOBAL X/Y aks çizgileri** boyunca
  kurulur: mütemadide temel kotunda kolonu olan akslarda temel kirişleri (`surekli.akslar` GLOBAL adlar: x doğrultulu hatlar için Y
  aksı, y doğrultulu hatlar için X aksı adları), radyede GLOBAL aks zarfı + taşma üzerinde ızgara.
- **Izgara dışındaki taban** (GLOBAL kesişimden 1 mm'den uzak, ek aks sistemi): yalnız **kirişsiz radyede** ağa katılır — düğümden
  geçen sanal ızgara çizgileri (`x=<X>` / `y=<Y>`) eklenir. Mütemadi temelde ve kirişli radyede öğretici hata ("… GLOBAL X/Y aks
  kesişiminde değil (ek aks sistemi) …"); o düğüme `mesnetler` ile mesnet verilir.
- **Ağın üzerindeki açık mesnet hatadır** ("Düğüm N (…) açık mesnetli ('mesnetler') ve <mütemadi temel|radye> ağının üzerinde …");
  ağa bağlanmayan taban ve boş ağ da öğretici hata verir; temel seviyesindeki bağ çubuğu yalnız uyarıdır.
- **temel.py yeniden kullanımı:** genel motor temel.py'ye aks–kat görünümü verir (`yapi_serbest._temel_gorunum(B, ilk=False, ag=None)`:
  GLOBAL akslar sıralı `xk/xad/yk/yad`, `kat`, `temeller`, `malzemeler`, `kesitler`, `taban_ixy`, `kolonlar`, `kolon_key`, `kolon_no`,
  `sanal`); çözümsüz modelde de çalışır (tablolar). Çıktı aks–kat `veri.temel` şemasıyla aynıdır; ek olarak temel elemanları
  `veri.ag.elemanlar`'da (`tur` `temel-kirisi` | `radye-serit`, `cubuk` null, `kesit` TK | RS), ağ düğümleri `veri.ag.dugumler`'de
  (`tur: "temel"`), `veri.akis.korunum.G.temel_oz = W`, `veri.yukler` toplamı ve kat 0 satırı W'yi içerir, `veri.bina.temeller.tip`
  çözülen tiptir (`.surekli` / `.radye` normalize).
- Sınır: genel modelde `EN_FAZLA_SD = 2000` (aks sınırı yok; temel ağı dahil, `ag` gerekirse büyütülür); aks–kat modelinde 12 × 12 aks,
  12 kat, 1500 SD.

### 12.4 Açık mesnetler: yaylı ve diyafram bağlı

- `mesnetler[]` kaydı `kx, ky, kz` (kN/m) ve `krx, kry, krz` (kN·m/rad) yay rijitliklerini **bina eksenlerinde** taşıyabilir (her biri
  pozitif sayı ya da yok). Aynı doğrultu hem tutulu hem yaylı olamaz ("mesnetler[k]: <yön> hem tutulu hem yaylı verilemez (<anahtar>).");
  ≤ 0 ya da sayı olmayan değer hatadır. Motor yayları `kx→kx, ky→kz, kz→ky, krx→krx, kry→krz, krz→kry` ile motor eksenlerine çevirir;
  yay kayıtları `tur: "yay-mesnet"` taşır, mesnet kaydı `tip: "yay"`.
- Rijit diyaframlı bir seviyedeki düğümün `ux`/`uy`/`rz` mesnedi köle SD'lere ceza yayı olarak uygulanır (k_t = 10⁶·max EA/L,
  k_r = 10⁶·max EI/L; `K_r = TᵀKT` efendiye bağlar; yay kayıtları `tur: "diyafram-mesnet"`); `uz`/`rx`/`ry` olağan mesnettir. Uyarı:
  "Düğüm N (adres) rijit diyaframlı <kat adı> seviyesinde: ux/uy/rz mesnedi diyafram bağıyla (ceza rijitliği) uygulandı; bu nokta
  bütün katın yatay hareketini tutar." Arayüzde Mesnet aracı önce sorar (Olduğu gibi uygula / Yalnız düşey mesnet (uz, rx, ry) / Bu
  katın diyaframını esnek yap / Vazgeç); diyafram kipi `analiz.diyafram[kat]` > `deprem.diyafram` > "rijit" (katta kalınlıklı panel yoksa
  esnek) sırasıyla okunur.

## §13 Temeller

`temel.py`: mütemadi temel (seçilen aks çizgileri boyunca ters T temel kirişleri, Winkler düğüm yayları k_z = k0·B·l, tabla dönme yayı
k0·B³/12·l) ve radye (iki doğrultulu ızgara, şerit I = b·h³/12, J ≈ b·h³/6; isteğe bağlı aks kirişleri); taban basıncı, oturma,
farklı oturma, TS 500 / TBDY 16.8 zemin denetimleri, zımbalama, donatı. **İki motor da temel.py'yi kullanır:** aks–kat (`yapi.py`)
doğrudan, genel model (`yapi_serbest.py`) §12.3'teki aks–kat görünümüyle; temel öz ağırlığı G'ye eklenir ve `veri.temel.oz_yuk`
dağılışını verir. Tekil temel (B × L; ankastre / mafsal / elastik) `yapi.py`'dedir (genel modelde de aynı kayıt). Çıktı `veri.temel`;
anlatımda "Temel ve zemin" adımı; arayüzde Temel sekmesi ve temel tipi seçici (`docs/bina.js`; genel modelde mütemadi / radye açık,
sahne güncel çözümde temel kirişlerini ve radyeyi `veri.temel.hatlar` / `model.plak`'tan çizer).

## §14 Çıktılar

### 14.1 Statik hesap raporu

`rapor.py` (`statik_rapor(bina, veri, secenek)`, `dosya_adi`; köprü `bina_rapor`). Tek dosya HTML5, gömülü CSS, A4 yazdırma, dış
kaynak yok. Bölüm sırası sabit: 1 kapak/künye, 2 yönetmelikler, 3 genel bilgiler, 4 malzemeler, 5 kesitler, 6 yükler, 7 deprem,
8 analiz yöntemi, 9 yük birleşimleri, 10 analiz sonuçları, 11 betonarme, 12 çelik, 13 temel, 14 sonuç; metraj özeti, Ek A düğümler,
Ek B çubuklar, Ek C seçilen tablolar. Veri olmayan bölüm "Bu modelde uygulanmadı" notuyla kalır.

- §10.1 korunum: Σ tepki = Σ mesnet tepkisi + Σ yazılan yay kuvveti + `yay_ozet` (§4); düğüm tablolarında yaylı mesnet, diyafram bağlı
  mesnet ve elastik temel yayı ayrı türle (rijitlikleriyle), mütemadi / radye ağı tek "zemin yayları" satırıyla (ağ düğümlerinin yatay
  tutulma tepkileri "temel ağı (yatay tutulu)" satırlarıdır). Korunum tablosunda
  "temel öz ağırlığı" satırı.
- §5: basit çelik kesitlerin sınıfı (`tasarim.kesit_sinifi`, "<ad>: basınçta …, eğilmede …" ve parça oranları).
- §13: iki modelde de temel analizi ve tasarımı `veri.temel`'den; model mütemadi / radye ama çözümde o sonuç yoksa "Bu çözümde
  mütemadi/radye temel sonucu yok (çözüm eski ya da temel tipi değişti); binayı yeniden çözün."; boyutlar `veri.bina.temeller`'in
  normalize kaydından; açık mesnetler ayrı tabloda.

### 14.2 IFC

`docs/ifc_disari.js` (`window.MatrisIFC`): IFC4 STEP; proje → yapı → katlar, aks ızgaraları (ek sistemler dahil), fiziksel model
(kolon, kiriş, üye, döşeme, kaplama, temel), malzeme ve profil setleri, isteğe bağlı yapısal analiz modeli, yükler ve D/C
özellikleri. GlobalId'ler belirlenimci (aynı modelden aynı kimlik).

- **Yükler:** G / Q / S'ye ek olarak W, E ve K eylemleri `veri.yukler.eylemler`'den (§4) her durumun yük grubuna yazılır: çubuk yayılı /
  tekil yükleri IfcStructuralLinearAction / IfcStructuralCurveAction (global bileşenler q·vek), tekil yük ve düğüm kuvvetleri
  IfcStructuralPointAction; rijit diyaframın efendi düğümü kendi IfcStructuralPointConnection'ı ("Kat k diyafram merkezi", üye bağlantısı
  yok); EZ, G eylemlerinin `G_carpani` ile ölçeklenmiş kopyası. Yanıt boyutu sınırında eylemler yazılmamışsa (`eylemler_not`) eski not
  uyarı olarak kalır.
- **Temel öz ağırlığı:** mütemadi / radyede `veri.temel.oz_yuk` (temel elemanlarına yayılı, düğümlere tekil), tekil temelde temel başına
  γ·B·L·h.
- **Vute:** kutu ve U tabanlı vute daralan katı (değişken kesit) olarak; boru, korniyer ve çift korniyer tabanlı vute sabit kesitle ve
  uyarıyla. Basit profil boyutları motorla aynı kuralla (UPN yuvarlatması, eşit olmayan kollu korniyer yok).

## §15 Tablolar ve metraj

### 15.1 TABLO şeması

`tablolar.py` modül belgesi: `{ad, baslik, grup, sutunlar: [{ad, baslik, birim, tur, duzenlenebilir, ...}], satirlar: [{degerler,
yol?, hucre?, ozet?}], toplam?, aciklama, kaynak}`. `yol` bina JSON'undaki gerçek alana işaret eder (seçiciler `{"no": 3}`,
`{"ad": "A"}`); `degisiklikleri_uygula` kopyaya yazar, `aks_yeniden_adlandir` bağlı bütün başvuruları günceller. Rapor ve arayüz aynı
tabloları kullanır; köprü `bina_tablolar`. Metraj eğitim amaçlı yaklaşık keşiftir (birim fiyat yok).

### 15.3 Tablo editörü

`docs/tablo_editoru.js` (`window.MatrisTablo`): sarı (düzenlenmiş) hücreler, "Uygula" (tek geri al adımı), sekmeyle ayrılmış
yapıştırma, CSV dışa aktarma (BOM, `;`, ondalık virgül), rapora tablo seçimi. Masaüstü "Tablolar (.csv)" bütün tabloları tek CSV'ye
yazar.

**CSV içe aktarma** ("İçe aktar (.csv)…"; masaüstünde Dosya › İçe aktar › Tablolar (.csv)…, komut `csv-iceri`; `MatrisTablo.ac(...,
{csvIceri: true})`, `ed.csvIceAktar()`): BOM kabul; ayırıcı `;` `,` ya da sekme kendiliğinden; `Tablo: başlık;grup;ad` bölümleri
birden çok tabloyu doldurur, yoksa etkin tablo; başlık hücreleri sütun başlıklarıyla, satırlar anahtar sütunuyla (yoksa sırayla)
eşlenir; yalnız düzenlenebilir hücreler değişir ve sarı bekleyen hücre olur ("Uygula", Ctrl+Z); bilinmeyen ya da düzenlenemeyen
sütunlar bildirilir.

**Genel model tablo kuralları:** Duvar Yükleri duvar taşıyabilen her çubuğu (kiris, bag, diger) listeler, duvarsız satırın Duvar ve
yükseklik hücreleri o çubuğun kaydına yazar (genelleştirilmiş modelde `kaynak` yalnız köken bilgisidir); döşeme kalıbı kenar başına kiriş
yarı genişliği kadar içeri ötelenmiş net alandır (dikdörtgende (dx − b₁/2 − b₃/2)·(dy − b₂/2 − b₄/2), aks–kat ile aynı); kat
ağırlıkları `veri.yukler.katlar`'dan (iki motorda her kolonun ağırlığı üst seviyesine); Mesnetler tablosunda açık mesnetin `k_x … k_rz`
hücreleri düzenlenir, Mesnet Tepkileri satır türleri "mesnet", "yaylı mesnet", "mesnet (diyafram bağıyla)", "elastik mesnet (zemin
yayı)", "zemin yayı" ("Yay rijitliği" sütunu yalnız yaylı satır varsa).

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

`docs/arac_kutusu.js` (`window.MatrisArac`): komut kaydı (`komutKaydet`, `baglar`), katalog, kenara yerleşen (rıhtım, §17.4) ya da
yüzen, sürüklenen, gruplanan kutular, Özelleştir, hazır yerleşimler, tek kaynaklı kısayollar (`kisayollar()`; Yardım sayfasındaki tablo ve Bina sayfasındaki `?`
penceresi bundan üretilir), kullanılamayan komutun nedeni. `docs/olcum.js` (`window.MatrisOlcum`): uzaklık, açı, alan, kot farkı,
koordinat, eleman boyu; çizim kipinde yalnız aks kesişimleri ve düğümlere yakalama (§19), ölçüm kipinde orta nokta ve izdüşüm de.

### 17.2 Sağ tık ve eleman bilgisi

`docs/eleman_bilgi.js` (`window.MatrisBilgi`): bağlam menüsü (sağ tık, uzun basma, Shift+F10) ve iğnelenebilir sekmeli denetçi
(geometri, kesit, bağlantı, yükler, iç kuvvetler, yer değiştirme, tasarım, metraj, yük yolu). İstemci tarafı model bina + `veri`'den
türetilir; çözümden sonra köprü `bina_eleman_bilgi` (`{cozum_kimligi, tur: cubuk | kolon | kiris | fe, no, durum?}` → `{paket:
{sekmeler: {ic, yer}, ...}}`) "Motor ayrıntısı" bölümlerini ekler (istasyon iç kuvvetleri, en büyük değerler, uç yer değiştirmeleri).

### 17.3 Tam ekran ve yerleşim

`docs/bina.js`: ⛶ / F tam ekran (Esc ya da F çıkar), daraltılabilir araç çubuğu ve özellik paneli, sonuçlar sağ panelde ya da alt
çekmecede, sürüklenen ayırıcılar, telefonda alt şerit. "Sığdır" modeli kenar paylarının içine yerleştirir (`MatrisBina.izdusum().alan`);
3B'de aks balonu ve kot etiketi payı yetmezse kenar payı büyür.

### 17.4 Araç kutusu yerleşimi: rıhtım (kenar şeritleri) ve taşma çekmecesi

Yerleşim (`MatrisArac.Duzen.rihtim(liste, W, H, sec)`, `docs/arac_kutusu.js`) katman boyutu ve kutu listesinin **saf işlevidir;
geçmişi yoktur** (aynı girdi aynı çıktı; büyütüp küçültmek ya da tam ekrana girip çıkmak aynı yerleşime döner).

- **Kayıt (yerleşim sürüm 2):** kutu `yer` (`"kenar"` | `"serbest"`), `kenar` (ust / alt / sol / sag), `sira`, `katli` (yalnız
  kullanıcının daraltması; yerleşim yazmaz), `konum` (yalnız yüzen kutu). **Öncelik = kutu dizisindeki sıra.** Sürüm 1 kayıtlar bir kez
  dönüştürülür (`otoKatli`, `otoKonum` atılır, kenar çapadan, bina sayfasında birleşik "Düzenleme ve aks" ikiye ayrılır) ve bildirim
  gösterilir: "Araç kutuları kenar yerleşimine geçirildi; bir kutuyu sahneye sürükleyerek yüzdürebilirsiniz."
- **Şeritler:** üst ve alt **bant** bütün genişlikte tek satır, sol ve sağ **sütun** bantların arasında tek sütun. Kutu biçimleri bir kez
  ölçülür: yatay başlıklı / başlıksız / daraltılmış, dikey tek / iki düğme sütunlu / daraltılmış çip.
- **Sığdırma:** bantta yer yetmezse en düşük öncelikli kutudan başlayarak başlık gizlenir, yine yetmezse en düşük öncelikli kutu
  çıkarılır; sonra başlıklar öncelik sırasıyla geri verilir. Sütunda önce tek, gerekirse iki düğme sütunu; yine sığmayan en düşük
  öncelikli kutu çıkarılır. En küçük sahne (yükseklik 120, genişlik 200 px) korunur. Çıkarılan kutu kalınlığını değiştirmeden öteki
  şeride düşebilir, yoksa **taşma çekmecesine** gider.
- **Taşma çekmecesi:** "⋯ n" düğmesi (sayı rozeti; içindeki komut etkinse onun simgesi) yönetici düğmesiyle birlikte sol alt köşede, alt
  bandın ilk öğeleridir (kutuların üstüne binmez). Çekmece varsa yerleşim iki geçiş yapar (ikinci geçişte köşeye çekmece düğmesi eklenir).
  Çekmece kümesi kaydedilmez; yer açılınca kutu kendiliğinden döner. Esc ya da dışarı basma kapatır (odak düğmeye döner).
- **Kenar payları = şerit kalınlıkları:** sahnenin sığdırma dikdörtgeni şeritlerin içindedir; kenardaki kutu modeli örtemez. Yüzen
  kutular paya sayılmaz (kullanıcı sahnenin üstüne koymuştur).
- **Kullanıcı eylemleri kazanır:** kenara sürükleyip bırakılan (yerleştirme işaretiyle), açılan (▸) ya da "Gizli kutular → göster" ile
  geri gelen kutu şeridinin başına geçer; bu yüzden başka bir kutu çekmeceye düşerse bildirim söyler ("“X” sığmadı; ⋯ düğmesinden
  açılır."). Sahneye bırakılan kutu yüzer (`yer: "serbest"`, çapa kaydedilir); bir kutunun üstüne binerse en yakın boş yerde gösterilir,
  çapa değişmez. Kutu menüsü: kenardaki kutuda "Kenar › Üst / Alt / Sol / Sağ" ve "Sahnede yüzdür", çekmecedeki kutuda ayrıca "Kenara
  sabitle", yüzen kutuda "Yatay yap / Dikey yap" ve "Kenara yerleştir". "Varsayılana dön" sayfanın varsayılan yerleşimine döner.
- **Sayfa tuşları:** `MatrisArac.SAYFA_TUSLARI` (Esc, Shift+F10, Enter, ?, PgUp, PgDn, F, Shift+F, Ctrl+Shift+Z, Backspace;
  `{kisayol, ad, grup}`): Bina sayfasının `?` penceresi, Yardım kartı ve masaüstü Yardım › Klavye kısayolları aynı satırları gösterir.
- Telefonda (katman < 640 px) kutular sahnenin altındaki kaydırılabilir şerittir; rıhtım ve çekmece kullanılmaz.

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

## §20 op4 mimarisi (*taslak*; Faz 0)

op4, Opus Fortis için yerel Windows yapısal modelleme ve analiz programıdır (web sayfası değil). Bağlayıcı belirtim, gerekçeler ve
aşamalı plan [`op4/MIMARI.md`](op4/MIMARI.md)'dedir; bu bölüm onun §1, §4 ve §8'inin özetidir. Çelişkide MIMARI.md geçerlidir.
Faz 0 iskeleti (`op4/`, `.github/workflows/op4.yml`) CI'da uçtan uca çalışır; aşağıdaki hedef mimari Faz 1'den itibaren kurulur.

### 20.1 Kararlar (MIMARI §1)

| Konu | Karar |
|---|---|
| Ürün | `op4.exe` (arayüz; C++20, statik CRT) ve `op4motor.exe` (Python barındırıcısı; ana + tembel yardımcı süreç). Kurulum `op4-setup-<sürüm>.exe` (Inno Setup; lisans doğrulanır, yedek NSIS); sürüm `op4-vX.Y.Z` etiketinden. Açılışta Opus Fortis logolu açılış ekranı. |
| Arayüz | Dear ImGui (docking) + Win32 kabuk; yerel dosya ve görev pencereleri. Türkçe arayüz, ondalık virgül, kN ve m. |
| Grafik | Doğrudan Direct3D 12; donanımda MSAA 8×, WARP'ta 4×; ters-Z sonsuz uzak düzlem (D32); kamera-göreli koordinat, örneklenmiş kesit ağları, sabit piksel kalınlıklı çizgiler. |
| Gezinme | Sol sürükle kaydırır, Shift + sol sürükle döndürür, tekerlek imlece doğru yakınlaştırır; hesap mutlak çapaya göredir (kayma ≤ 0,0001 px ölçüldü). |
| Hesap motoru | Kökteki Python motoru değişmeden; gömülü CPython ayrı süreçte, protokol `web_kopru.calistir` JSON'u (§20.3). |
| Model çekirdeği | QuickJS-ng; `docs/` altındaki saf JS modülleri (`model_ops`, `aks_sistemi`, `ifc_disari` …) değişmeden çalışır, model otoritesidir. |
| Belge içerikleri | Dersler, rapor önizleme ve adım adım matematik ayrı bir "Belge penceresi"nde (yerel dosyalar, ağ yok). |
| Proje dosyası | `.op4` (ZIP); Kaydet, Farklı kaydet, Aç, otomatik kayıt, kurtarma, son dosyalar. Pencere başına bir proje. |
| IFC | Dışa aktarma Faz 1 (`ifc_disari.js`), içe aktarma Faz 6 (isteğe bağlı bileşen). |
| Ağ ±%2 | Görüntü ağı: analitik dış çizgi + LOD; analiz ağı: `ag_eniyile.py` (Richardson, GCI). |
| CI | Windows işi `windows-2025` (derle, WARP ekran görüntüleri, gerçek pencere, kurulum / kaldırma), etikette Release; ekran görüntüleri ve `OP4OLCUM` ölçümleri günlüğe yazılır. |

### 20.2 Üst düzey yapı (MIMARI §4)

```
op4.exe  (pencere başına bir proje)
  UI iş parçacığı : Win32 döngüsü → girdi birleştirme → ImGui → komut yöneticisi → D3D12
  Çekirdek        : QuickJS-ng bağlamı (model otoritesi, geri al yığını)
  Motor G/Ç       : boru çiftleri ↔ op4motor süreçleri; yanıtlar UI kuyruğuna
  İş havuzu       : kesit ağı / LOD, BVH, zip / PNG, öznitelik zenginleştirme, IFC ağı
      │ boru çifti (4 B uzunluk + UTF-8 JSON)          │                         │ (Faz 5)
  op4motor "ana": op4_sunucu.py, çözüm önbelleği    op4motor "yardımcı" (tembel)    Belge penceresi
```

- **Düzenleme:** komut noktaları toplar (yakalama C++ BVH'de) → önizleme yalnız üst katmanda → işlemede çekirdeğe tek işlem
  (`uygula(islem, parametreler)`) → çekirdek eklenen / silinen / değişen kümeleri döndürür → UI yalnız değişen örnekleri yazar,
  sonuçları "eski" işaretler, otomatik kaydı kurar.
- **Çözüm:** F5 → çekirdekten bina metni → ana motora `bina_coz` (`anlat: false`) → `SonucOzeti`; ayrıntılar istendikçe
  `cozum_kimligi` ile.
- **Proje durumu:** dosya yolu ve kirli bayrağı, çekirdek bağlamı, değişmez sahne anlığı ve sütunlu öznitelik tablosu, seçim ve
  süzgeçler, görünümler, sonuç özeti, GPU kaynakları. Eleman kimliği `{tur, no, alt}`.

### 20.3 Hesap motoru tümleşimi (MIMARI §8)

- **Süreç:** `op4motor.exe` (≈ 150 satır C++) geçersiz std tutamaçlarını boşaltır, gömülü Python dosyalarını denetler (eksikse
  okunur hata, `Py_FatalError` yok), BLAS iş parçacığı sayısını ayarlar (ana: çekirdek − 1, yardımcı: 1) ve
  `Py_Main(-X utf8 -B -m op4_sunucu --istek … --yanit … --rol ana|yardimci)` çağırır. Yalıtımı `._pth` sağlar.
- **Sunucu** (`op4/motor/op4_sunucu.py`): stdout / stderr ve fd 1–2 günlüğe yönlendirilir (motordaki `print` protokolü bozmaz);
  `SIGINT` işleyicisi kurulur; `web_kopru` içe aktarılınca `hazir` gönderilir; istekler ana iş parçacığında sırayla
  `calistir()` ile işlenir; okuyucu iş parçacığı `iptal`te `_thread.interrupt_main()`, `kapat`ta düzgün çıkış yapar.
- **Protokol:** miras alınan iki anonim boru; çerçeve 4 bayt küçük-endian uzunluk + UTF-8 JSON (≤ 512 MB). UI → motor
  `{"tur":"istek","id","istek":{islem, girdi, ayarlar}}`, `{"tur":"iptal","id"}`, `{"tur":"kapat"}`; motor → UI `hazir`,
  `durum`, `ilerleme` (Faz 5), `yanit` (`calistir` metni olduğu gibi, yeniden ayrıştırılmaz), `gunluk`. İstek gövdesi web
  isteğiyle birebir aynıdır (§4 ve `docs/web_kopru.py` şemaları bağlayıcıdır).
- **Yönlendirme:** ana süreç bina çözümü, kombinasyon, tasarım, kesit önerisi, eleman bilgisi, rapor, tablolar, alan, yük yolu,
  `bina_kimlik`, `bina_ag_eniyile`; yardımcı süreç matris işlemleri, dersler, yardım, sonlu eleman, kütüphane, şablonlar,
  deprem önizleme, `ifc_iceri`.
- **İptal ve sınırlar:** iptal yanıtı `{"hata": "İşlem iptal edildi.", "hata_turu": "iptal"}`; 5 s içinde yanıt yoksa süreç
  sonlandırılıp yeniden başlatılır (≈ 0,5 s). Zaman aşımı yok, ilerleme görünür; bellek tavanı Job Object ile (varsayılan %60);
  `id` eşlemesiyle eski yanıtlar atılır.
- **Paket:** `python\` (CPython embeddable, numpy, `._pth`), saf paketler önceden derlenmiş `.pyc` ile, `motor\` (kök motor
  modülleri, `web_kopru.py`, `op4_sunucu.py`); isteğe bağlı `bilesen\ifc\`, `bilesen\seyrek\`. Kurulum yolu Türkçe karakter ve
  boşluk içerebilir (CI `C:\op4 dene ŞĞİı` yoluna kurar).
- **Motorda yalnız eklemeli değişiklik:** varsayılanlar bugünkü davranışı korur (`anlat` varsayılan true, `bina_kimlik`,
  iptal türü, `ayarlar.sd_siniri`, ilerleme kancası, ürün adı parametresi; seyrek çözüm yolu ve genel modelde radye /
  mütemadi temel ilgili fazlarda). `pytest testler` ve `node --test testler/js/*.test.js` değişmeden geçer.

**Faz 1 paket sözleşmeleri** (`op4/MIMARI.md` §24): dört paket (A derleme-motor, B model-cekirdegi, C arayuz-goruntu, D
dosya-cozum) paralel çalışır; aralarındaki arayüzler `op4/kaynak/cekirdek/` başlıklarında (S1–S27: eleman kimliği, sahne
anlığı, öznitelik tablosu, seçim ve seçme, model çekirdeği, motor tel protokolü ve hizmeti, proje belgesi ve dosyası,
ayarlar, sonuç, komut defteri, arayüz kancaları, Hizmetler, uygulama kabuğu) ve `op4/js/` JSDoc'unda sabittir; komut
kataloğu `op4/veri/komutlar.json`. Kilitleyen: `op4/testler/` (doctest, node, pytest; Linux ve Windows CI),
`testler/test_op4_sozlesme.py` (dosya sahipliği, komut kataloğu, kod tabloları).

Uygulayan (Faz 0): `op4/kaynak/` (C++ iskeleti; motor şimdilik süreç içi `motor.cpp`, `--test-motor` tanı kipi), `op4/kurulum/op4.iss`,
`op4/araclar/` (`python_hazirla.py`, `kimlik_uret.py`, `gunluk_png_yaz.py`, `gunluk_png_coz.py`, `ci_bekle.sh`),
`.github/workflows/op4.yml`. Kilitleyen: `testler/test_op4_araclar.py` (günlük protokolü, iş akışı sözleşmesi, sürüm tek kaynağı,
sihirbaz görselleri), `testler/test_program_adi_yok.py` (op4'ün C++, HLSL, CMake ve kurulum dosyaları dahil), Windows CI.

---

## §21 op4 proje dosyası (`.op4`) biçimi (Faz 1)

Bağlayıcı belirtim `op4/MIMARI.md` §13'tür; bu bölüm onun dosya düzeyindeki ayrıntısıdır (F1 iş 1.6, D paketi yazar).
Çelişkide kod ve sınamalar geçerlidir.

### 21.1 Kapsayıcı

- `.op4` bir **ZIP** arşividir (deflate düzey 6; zip64 gerekirse kendiliğinden). Girdi adları UTF-8'dir (genel amaçlı bit 11).
- **Sıra bağlayıcıdır:** `mimetype` (sıkıştırmasız, ilk girdi; içerik tam olarak `application/x-op4`), `manifest.json`,
  `model/bina.json`, ardından diğer girdiler yol sırasıyla. `onizleme.png` sıkıştırmasız saklanır.
- Bütün girdilerin değiştirilme zamanı manifest'teki `kaydedildi` anıdır (yerel saatle DOS zamanı): aynı içerik + aynı
  manifest → aynı baytlar (aynı makinede; D8 kuralı).
- Okuma sınırları (sıkıştırma bombası ve bozuk dosya): en çok 4096 girdi, açılmış girdi başına 1 GiB, toplam 3 GiB; her
  girdinin CRC32'si denetlenir. Şifreli ve deflate dışı yöntemli girdiler reddedilir.
- Bozuk / kesik dosyada açma reddedilir, mevcut model değişmez ve öğretici Türkçe hata verilir ("Dosya bozuk ya da yarım
  kalmış: ZIP dizini bulunamadı …; varsa .bak yedeğini ya da kurtarma kaydını açın").

### 21.2 Girdiler

| Yol | Yazan (katkı, `ProjeBelgesi`) | İçerik | Zorunlu |
|---|---|---|---|
| `mimetype` | D | `application/x-op4` | evet (yoksa uyarı) |
| `manifest.json` | D | §21.3 | evet |
| `model/bina.json` | D (B'nin `Metin()`'i) | bina JSON (surum 1 ya da 3), kanonik UTF-8; dosyadaki baytlar `Metin()` ile birebir | evet |
| `gorunum/gorunum.json` | C | görünümler, kameralar, kipler, kesit kutusu, görünürlük, görünüm süzgeçleri | hayır |
| `secim/kumeler.json` | C | seçim kümeleri ve kayıtlı süzgeçler (kimlik metni `cubuk:12`) | hayır |
| `sonuc/ozet.json` | D | §21.5 | hayır (sonuç varsa) |
| `sonuc/veri.json` | D | son `bina_coz` yanıtının `veri` nesnesi, köprünün yazdığı ham metin | hayır |
| `ifc/kaynak.json` | (Faz 6) | IFC içe aktarma kaynağı ve eşleme tablosu | hayır |
| `onizleme.png` | D | 256 × 256 RGBA küçük resim (CPU izometrik çizim, Stüdyo renkleri) | hayır |
| diğer | — | **korunur**: açılan dosyanın tanınmayan girdileri yeniden kaydedilirken olduğu gibi yazılır | — |

Katkı sırası: model 0, görünüm 10, seçim 20, sonuç 30, önizleme 40. Her katkı kendi girdisini yazar ya da (sonuç yokken
`sonuc/*` gibi) siler.

### 21.3 `manifest.json`

```json
{"tur": "op4-proje", "bicim_surumu": 1,
 "uygulama": {"ad": "op4", "surum": "0.1.0", "firma": "Opus Fortis"},
 "kaydedildi": "2026-10-31T12:34:56Z", "model_ozeti": "39 düğüm, 63 çubuk, 18 panel, 4 kat", "motor_surumu": "…",
 "icerik": [{"yol": "model/bina.json", "bayt": 13491}, …]}
```

- `tur` `op4-proje` değilse dosya reddedilir; `bicim_surumu` 1'den küçükse ya da yoksa "bozuk".
- **Yükseltme zinciri:** güncelden eski `bicim_surumu` değerleri sırayla n → n+1 dönüştürücülerinden geçer (bugün tek
  biçim var: 1).
- **Daha yeni biçim** (`bicim_surumu > 1`): dosya **salt okunur** açılır (başlık "op4 — ad (salt okunur)"), Kaydet
  Farklı kaydet'e gider, uyarı verilir.
- Tanınmayan manifest anahtarları korunur (daha yeni sürümün eklediği alanlar yeniden kaydedilince kaybolmaz).

### 21.4 Açma ve kaydetme sırası

**Açma** (`DosyaIslemleri::Ac`): `ProjeOku` (biçim saptama → ZIP çözümü / eski biçim dönüşümü) → çekirdek `Yukle` + `Denetle`
→ `ModelYuklendi` (seçim ve sonuç temizlenir, Sığdır istenir) → `ProjeBelgesi::Sifirla` → `IcerikDagit` (katkılar kendi
girdilerini okur; kamerayı geri yükleyen katkı bekleyen Sığdır'ı `SigdirYapildi` ile iptal edebilir) → `Acildi` (temiz
durum, `acildi` olayı) → son dosyalar, atlama listesi, okuma kilidi. Önce dosya okunur, sonra kaydedilmemiş değişiklik
sorulur (bozuk dosya için kullanıcı boşuna sorulmaz).

**Kaydetme:** korunan girdiler (açılan dosyanın her şeyi) + `IcerikTopla` → manifest → ZIP → **bellekte doğrulama**
(`ProjeZipCoz`) → okuma kilidi bırakılır → atomik yazma (§21.7) → okuma kilidi yeniden açılır → `Kaydedildi`, kurtarma
kaydı silinir, son dosyalar. Eski biçimden açılan ya da salt okunur belge her zaman Farklı kaydet ile yazılır (uzantı
`.op4` eklenir).

### 21.5 `sonuc/ozet.json`

```json
{"bicim": 1, "cozum_kimligi": "bina-531fa88fc9470a4b", "tarih": "2026-10-31T12:00:00Z", "motor_surumu": "…",
 "sahne_surumu": 7, "sure_ms": 2085,
 "ozet": {"metin": "216 SD, 84 kombinasyon; G = 2714.76 kN, Q = 480.0 kN", "sd_sayisi": 216, "kombinasyon_sayisi": 84,
          "en_buyuk_dc": 0.99786, "en_buyuk_dc_elemani": "cubuk:12", "asan_sayisi": 0},
 "uyarilar": ["…"],
 "dc_dizisi": [{"kimlik": "cubuk:1", "dc": 0.60775, "belirleyen": "eğilme + eksenel", "kombinasyon": "…", "satir": 0}, …],
 "model_karmasi": "fnv1a64:…", "eski": false}
```

`dc_dizisi` çekirdeğin `SonucEsle` eşlemesidir (kimliğe göre sıralı; tasarımsız eleman `dc: null`). `model_karmasi` çözülen
model metninin (çözüme giden `Metin()`) FNV-1a 64 karmasıdır; `eski` kaydedilirken sonucun eski olup olmadığıdır.

**Açılışta eşleştirme (MIMARI §13.1.4):** karma açılan modelin `Metin()` karmasıyla aynı ve `eski` false ise sonuç hemen
güncel görünür (D/C renkleri motor beklemeden). Değilse "Sonuçlar eski" görünür ve hesap motoru varsa `bina_kimlik` istenir;
dönen `cozum_kimligi` kayıtlıyla aynıysa ve bu arada model değişmediyse sonuç güncellenir. `eski: true` kaydedilmiş sonuç
eski kalır (denetim istenmez).

### 21.6 Eski biçimler (içe aktarma)

`BicimSapta` uzantıya değil içeriğe bakar: `PK\3\4` → `.op4` ZIP; `ISO-10303-21;` → IFC (Faz 6'ya dek "henüz
desteklenmiyor"); `{` ile başlayan metin → uzantı `.op4` ise Faz 0 denemesinin JSON biçimi, `.matris` ise web sürümü
projesi, diğerleri bina JSON'u.

| Biçim | Dönüşüm |
|---|---|
| Faz 0 JSON `.op4` (`{"bicim": "op4-proje", "kamera", "gorunum", "model": {…}}`) | kamera ve görünüm `gorunum/gorunum.json`'a (`{"bicim":1,"kaynak":"op4-deneme","kamera":{"hedef":[x,y,z],"uzaklik","sapma","egim"},"kip":"cubuk"\|"kesit","kenarlar","izgara"}`); model boş açılır |
| `.matris` (`{tur: "matris-proje", surum: 1, bina, gorunum, arac_yerlesimi}`) | `bina` değeri **ham alt metin** olarak (anahtar sırası ve sayı yazımı korunur) çekirdeğe; `surum > 1` reddedilir; web görünüm ayarları alınmaz (uyarı); `.matris` içinde düz bina JSON'u da kabul edilir |
| bina `.json` (`{"tur": "bina", …}` ya da `{"bina": {…}}` sarmalayıcısı) | metin (ya da `bina` alt metni) olduğu gibi çekirdeğe |

İçe aktarılan belge "Adsız N"dir; Kaydet, kaynakla aynı klasörde `<ad>.op4` önererek Farklı kaydet açar, kaynak dosyaya
dokunulmaz. Ters yön: **Bina dışa aktar** `.json` (`Metin()`) ya da `.matris` (`{"tur":"matris-proje","surum":1,
"uygulama":"op4 · Opus Fortis","kaydedildi","bina"}`) yazar.

### 21.7 Atomik yazma

1. Hedefle aynı klasörde `<yol>.~op4-<süreç>-<sayaç>.tmp` oluşturulur, yazılır, diske boşaltılır (`FlushFileBuffers` /
   `fsync`) ve **tanıtıcısı kapatılır**.
2. Hedef varsa Win32'de `ReplaceFileW` (öznitelik, ACL ve eşitleme istemcisinin dosya kimliği korunur; ayar açıksa
   `<yol>.bak`), yoksa `MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH)`; POSIX'te `rename` + klasör `fsync`.
3. Paylaşım ihlali, kilit ihlali, eşlenmiş dosya, erişim reddi (eşitleme istemcileri) ve `ReplaceFileW`'nin "kaldırılamadı /
   taşınamadı" hataları geçicidir: **5 deneme, 100 ms aralık**. `ERROR_UNABLE_TO_MOVE_REPLACEMENT_2`'de yedek adına taşınan
   asıl dosya geri alınır.
4. Başarısızlıkta geçici dosya silinir ve **hedef değişmeden kalır**; ileti dosyayı tutan programı (eşitleme istemcisi,
   virüs tarayıcısı, başka op4 penceresi) anar. Salt okunur işaretli hedef yeniden denenmez.
5. Açık proje `FILE_SHARE_READ` okuma kilidiyle tutulur (başka program okuyabilir, yazamaz); kaydetmeden önce bırakılır,
   sonra yeniden açılır. Uzun yollar `\\?\` önekiyle açılır; bütün yollar UTF-8 → UTF-16 (Türkçe karakterli ve boşluklu
   yollar).

### 21.8 Otomatik kayıt ve kurtarma

- Klasör `%LOCALAPPDATA%\Opus Fortis\op4\kurtarma\` (sınamada `OP4_KULLANICI_DIZINI`). Oturum başına `<guid>.op4` (tam
  proje ZIP'i), `<guid>.json` (`{bicim, asil_yol, baslik, zaman, model_ozeti, surum, surec}`) ve `<guid>.kilit` (oturum
  kilidi: Win32'de paylaşımsız ve kapanınca silinen dosya, POSIX'te `flock`; süreç çökse de işletim sistemi bırakır).
- Belge kirliyken ve son otomatik kayıttan sonra değişiklik varsa, ilk değişiklikten `otomatik_kayit_dk` (varsayılan 5,
  1–30) sonra yazılır; yazma hatası bir kez uyarılır, bir aralık sonra yeniden denenir.
- Kaydedince, Yeni / Aç / Şablondan'da ve **temiz kapanışta** (belge temiz ya da kapanış onaylandı — "Kaydetme" dahil) oturumun
  kaydı silinir. Onaysız kapanışta (ör. pencere kapatma isteği kapanış onayından geçmediyse) kayıt kalır.
- Açılışta (ilk kare) kilidi tutulmayan kayıtlar "artık" sayılır ve Stüdyo **Kurtarma** kartı açılır: kayıt başına
  **Kurtar** (birincil) ve **Sil**, altta **Sonra**. Kurtar: model ve katkılar yüklenir, belge yolu `asil_yol`, belge kirli;
  önce bu oturumun kaydı yazılır, sonra eski kayıt silinir. Komut satırı: `KURTAR`, `KURTAR <n>`, `KURTAR sil <n>`,
  `KURTAR sonra`.
- Beklenmeyen hatada `cokme\op4-YYYYMMDD-HHMMSS-<pid>.dmp` (`MiniDumpWriteDump`; en yeni 10 döküm tutulur).

### 21.9 Son dosyalar, ayarlar, kabuk

- `ayarlar.json` `dosya` grubu: `otomatik_kayit`, `otomatik_kayit_dk`, `son_dosya_sayisi` (varsayılan 10), `yedek_bak`,
  `son_dosyalar` (en yeni başta, tekrarsız, Türkçe katlamalı karşılaştırma), `son_klasor`. Ayarlar değiştikçe (en çok
  saniyede bir) ve kapanışta atomik yazılır; bilinmeyen anahtarlar korunur.
- Atlama listesi `SHAddToRecentDocs`; ilişkilendirme `OpusFortis.op4.Proje` (`op4.exe "%1"`, kurulum betiği).
- **Tek örnek borusu:** `\\.\pipe\OpusFortis.op4.<SID>.<belge karması>` (karma: büyük / küçük harf duyarsız tam yolun
  FNV-1a 64'ü). Belgeyi açık tutan süreç bu adla sunucu açar (`FILE_FLAG_FIRST_PIPE_INSTANCE`, yalnız yerel istemci); aynı
  dosya yeniden açılmak istenince yeni süreç bağlanır, sunucuya `AllowSetForegroundWindow` verir, `{"tur":"one_gel"}`
  yazar ve çıkar; sunucu penceresi öne gelir. Başka dosya her zaman yeni pencerede açılır (pencere başına bir proje).
  `--yeni-ornek` denetimi atlar.

### 21.10 IFC dışa aktarma (MIMARI §14.1)

`Ctrl+E`: çekirdek `IfcDisari(secenek, veri)`; `secenek = {"analiz": true, "yukler": true, "dc": <güncel sonuç var>,
"uygulama": {"ad": "op4", "surum", "firma": "Opus Fortis", "tam_ad": "op4 · Opus Fortis"}, "zaman": "YYYY-MM-DDTHH:MM:SS"}`
(test kiplerinde sabit `2026-01-01T00:00:00`: aynı model → aynı bayt); `veri` güncel sonucun `sonuc/veri.json` metni.
Dosya atomik yazılır.

**Uygulayan:** `op4/kaynak/cekirdek/proje_dosyasi.cpp` (biçim), `proje_zip.cpp` (miniz 3.0.2; `op4/cmake/bagimlilik_miniz.cmake`),
`proje_json.cpp`, `proje_onizleme.cpp`, `proje_islemleri.cpp` (akış ve `dosya.*` komutları), `sonuc.cpp`, `sonuc_ek.cpp`,
`cozum_akisi.cpp` (sonuç katkısı), `op4/kaynak/platform/dosya_sistemi*.cpp` (atomik yazma, kilitler), `op4/kaynak/dosya/`
(Windows: dosya pencereleri, TaskDialog, tek örnek borusu, çökme dökümü, Stüdyo kartları). **Kilitleyen:**
`op4/testler/cekirdek/dosya_*.cpp`, `cozum_*.cpp` (ctest; ASan + UBSan), `op4/araclar/sablon_dok.py --denetle`.
