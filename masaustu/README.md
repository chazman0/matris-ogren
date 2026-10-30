# Matris Öğren — masaüstü sürümü

Matris Öğren'in Windows, macOS ve Linux için kurulabilen, **internet bağlantısı olmadan** çalışan bilgisayar programı.
Uygulamanın içeriği web sürümüyle (`docs/`) **aynı koddur**; masaüstü sürümü buna yerel menüler, kısayollar, dosya
iletişim kutuları, çoklu pencere, son dosyalar, otomatik kayıt ve çökme sonrası kurtarma, sürükle-bırak, dosya
ilişkilendirmesi (`.matris`) ve rapordan doğrudan PDF ekler. Python hesap motoru (sympy, numpy) programla birlikte gelir.

## Kullanıcılar için

### İndirme ve kurulum

Paketler GitHub'da **Releases** sayfasında (sürüm etiketleri, ör. `v1.0.0`) ya da **Actions → Masaüstü sürümü** çalıştırmasının
"Artifacts" bölümünde bulunur.

| Sistem | Dosya | Not |
|---|---|---|
| Windows | `Matris-Ogren-Kurulum-<sürüm>-x64.exe` | Kurulum sihirbazı (Türkçe); kullanıcı klasörüne kurulur, yönetici izni gerekmez, klasör seçilebilir. Masaüstü ve Başlat menüsü kısayolu oluşturur, `.matris` dosyalarını ilişkilendirir. |
| Windows | `Matris-Ogren-Tasinabilir-<sürüm>-x64.exe` | Kurulumsuz, tek dosya; USB bellekten çalışır. |
| macOS | `Matris-Ogren-<sürüm>-mac-arm64.dmg` (Apple işlemci), `…-mac-x64.dmg` (Intel) | dmg'yi açıp simgeyi Uygulamalar klasörüne sürükleyin. |
| Linux | `Matris-Ogren-<sürüm>-linux-x86_64.AppImage` | `chmod +x` ile çalıştırılabilir yapıp açın. |
| Linux | `Matris-Ogren-<sürüm>-linux-amd64.deb` | `sudo apt install ./Matris-Ogren-…deb` |

**Paketler imzasızdır** (ücretli kod imzalama sertifikası kullanılmıyor):

- **Windows SmartScreen** "Windows bilgisayarınızı korudu" derse: **Ek bilgi → Yine de çalıştır**.
- **macOS** ilk açılışta "doğrulanamadı" derse: Uygulamalar'da simgeye **sağ tık → Aç → Aç**. (Gerekirse Terminal'de
  `xattr -cr "/Applications/Matris Öğren.app"`.)

### Çalışma biçimi

- **Dosya → Aç / Kaydet / Farklı kaydet**: projeler `.matris` dosyasıdır (bina modeli JSON'u + görünüm + araç kutusu yerleşimi).
  Kaydedilmiş bir projede **Ctrl+S** soru sormadan aynı dosyaya yazar. Başlık çubuğundaki **•** kaydedilmemiş değişiklik demektir;
  böyle bir pencere kapatılırken "Kaydet / Kaydetme / Vazgeç" sorulur.
- **Son dosyalar** Dosya menüsündedir. Bir `.matris` (ya da `.json`) dosyasını pencereye **sürükleyip bırakmak**, dosyaya **çift
  tıklamak** ya da komut satırından `MatrisOgren proje.matris` vermek de açar. Açık bir dosya yeniden açılmak istenirse o pencere öne gelir.
- **Çoklu pencere**: Dosya → Yeni pencere (Ctrl+Shift+N). Her pencere kendi projesini taşır.
- **Otomatik kayıt ve kurtarma**: kaydedilmemiş değişiklikler düzenli aralıklarla kurtarma klasörüne yazılır. Program ya da
  bilgisayar beklenmedik biçimde kapanırsa bir sonraki açılışta "Kurtar" önerilir; pencere içeriği çökerse yeniden yüklemeden sonra
  son durum geri gelir. Klasör: Dosya → Kurtarma klasörünü göster.
- **Dışa aktarma** (IFC, CSV, JSON, HTML rapor, resim) yerel "Kaydet" iletişim kutusuyla; **Rapor → PDF olarak kaydet** raporu
  A4 PDF olarak doğrudan yazar, **Rapor → Yazdır** (Bina sayfasında) statik raporu yazıcıya gönderir. **Tablolar (.csv)** bütün
  tabloları tek bir CSV dosyasına yazar; tablo verisi dosyadan değil, **Analiz → Tablolar** penceresinde yapıştırarak girilir.
- Bağlantılar (web sürümü, kaynak kodu) varsayılan tarayıcıda açılır; program kendisi hiçbir ağ isteği yapmaz.
- Ayarlar, son dosyalar ve kurtarma kayıtları: Windows `%APPDATA%\Matris Öğren`, macOS `~/Library/Application Support/Matris Öğren`,
  Linux `~/.config/Matris Öğren`.
- Menü kısayolları: **Yardım → Klavye kısayolları**. En çok kullanılanlar: Ctrl+N yeni, Ctrl+O aç, Ctrl+S kaydet,
  Ctrl+Z / Ctrl+Y geri al / yinele, F5 çöz, F6 tasarım kontrolleri, F9 statik rapor, Ctrl+T tablolar, Ctrl+E IFC, Ctrl+G aks verisi,
  F11 tam ekran, Ctrl+1…4 sayfalar (macOS'ta Ctrl yerine ⌘). Bina sayfasının araç kısayolları (S seç, L çubuk çiz, K kolon, R kiriş,
  X çapraz, Ctrl+Enter çöz, 1–4 görünümler…) uygulamanın **Yardım** sayfasındaki "Klavye kısayolları" kartında ve Bina sayfasında
  **?** tuşuyla açılan pencerededir; ikisi de araç kutusunun komut kaydından üretilir.

## Geliştiriciler için

Gereksinim: Node.js 22 (npm 10). Masaüstü çatısı Electron'dur; sürümler `package.json`'da tam olarak sabitlenmiştir
(`electron` 45.x, paketleyici `electron-builder` 26.x) ve `package-lock.json` ile kilitlidir.

```bash
cd masaustu
npm ci                 # bağımlılıklar (çatının ikili dosyası ayrıca indirilir)
npm run hazirla        # ../docs → uygulama/ + yerel Python motoru ve kütüphaneler (ağ gerekir; sonra önbellekten)
npm start              # programı geliştirme kipinde aç
npm run dist           # bu işletim sistemi için paketle (dist/)
npm run dist:dir       # paketlemeden yalnız açılmış uygulama klasörü (hızlı deneme)
npm run onizle         # uygulama/'yı programdaki başlıklarla (CSP dahil) http://127.0.0.1:8765/ adresinde sun
npm run denetle        # sözdizimi denetimi
```

Notlar:

- Çatının ikili dosyasının indirilemediği ortamlarda `ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm ci` ile bağımlılıklar kurulur;
  `hazirla`, testler ve `onizle` çatı olmadan çalışır.
- Vekil sunucu (`HTTPS_PROXY`) arkasında `hazirla.js` kendini `NODE_USE_ENV_PROXY=1` ile yeniden başlatır (Node ≥ 22.21).
- `uygulama/`, `.onbellek/`, `build/`, `dist/` ve `node_modules/` üretilen klasörlerdir; git'e girmez. `docs/` değişince
  `npm run hazirla` yeniden çalıştırılır.

### Dosyalar

| Dosya | Görev |
|---|---|
| `package.json` | Sürümler, betikler ve paketleme ayarları (`build`: appId `com.matrisogren.app`, ürün adı "Matris Öğren", `.matris` ilişkilendirmesi, hedefler). |
| `hazirla.js` | `../docs`'u `uygulama/`ya kopyalar; motorun Pyodide sürümünü (`docs/motor.worker.js` → `PYODIDE_SURUM`) ve yüklediği paketleri (`loadPackage([...])`) okur, bağımlılıkları `pyodide-lock.json`'dan çözer, çekirdek + tekerlekleri SHA-256 denetimiyle `uygulama/pyodide/` altına indirir; sayfalardaki CDN kütüphanelerini (formül dizgisi, markdown) `uygulama/kutuphane/`ye indirip adresleri yerelleştirir; kopyadaki worker'a `self.MATRIS_PYODIDE_URL = "./pyodide/"` ekler; `uygulama/masaustu.json` ve `build/icon.png` yazar. Çıkış kodu 3 = ağ hatası. |
| `main.js` | Ana süreç: `app://matris/` protokolü, pencereler ve pencere durumu, Türkçe menü, IPC, dosya iletişim kutuları, son dosyalar, otomatik kayıt / kurtarma, tek örnek, dosya ilişkilendirmesi, sürükle-bırak, PDF. |
| `preload.js` | Yalıtılmış ön yükleme betiği: sayfaya yalnız `window.masaustu` yüzeyini açar; sürükle-bırakı işler. |
| `lib/menu.js` | Menü şablonu (saf veri; testler doğrudan inceler), komut listesi (`komutListesi`, aşağıdaki Komutlar tablosu) ve menü kısayolları penceresinin metni (`kisayolMetni`). |
| `lib/sunucu.js` | `uygulama/` dosyalarının sunulması: yol denetimi, içerik türleri (`application/wasm` vb.), HTML'e İçerik Güvenliği Politikası. |
| `lib/yardimci.js` | Saf yardımcılar: atomik yazma, proje okuma, ayar deposu, son dosyalar, komut satırı, pencere sınırı, kurtarma, süzgeçler, PDF bilgi sözlüğü. |
| `../docs/masaustu_kopru.js` | Sayfa tarafı köprü: `window.MatrisDosya` ve `masaustu-*` olayları (web sürümünde de yüklenir). |
| `../.github/workflows/masaustu.yml` | Üç işletim sistemi için paketleme ve sürüm yayımlama. |

### Mimari ve güvenlik

- Uygulama dosyaları `app://matris/` özel protokolüyle sunulur (standart + güvenli şema, fetch ve CORS açık): modül worker,
  `WebAssembly.instantiateStreaming` ve `fetch` dosya sisteminden değil bu protokolden çalışır. Servis çalışanı masaüstünde
  kaydedilmez (köprü `navigator.serviceWorker.register`'ı devre dışı bırakır).
- HTML yanıtlarında CSP: yalnız uygulamanın kendi dosyaları (`'self'`), WebAssembly derlemesi (`'wasm-unsafe-eval'`) ve satır içi
  betiklerin SHA-256 özetleri; dış kaynak yok.
- Pencereler `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false`; sayfa yalnız `window.masaustu`'yu görür. IPC
  yalnız kendi pencerelerimizden ve `app://matris/` adresinden kabul edilir. Uygulama dışına gezinme engellenir; `http(s)`
  bağlantıları varsayılan tarayıcıda açılır; izin istekleri (pano ve tam ekran dışında) reddedilir; gömülü webview yoktur.
- Sürükle-bırakta dosya yolu yalnız ön yükleme betiğinde (gerçek kullanıcı olayı, `isTrusted`) alınır; sayfa yol göremez.
  "Klasörde göster" yalnız bu oturumda programın kaydettiği dosyalar için çalışır.
- PDF, betikleri kapalı gizli bir pencerede üretilir; belgeye `<title>` yoksa eklenir, PDF bilgi sözlüğündeki üretici girdileri silinir.
- Tarayıcı kimliğinden (user agent) çatı ve uygulama belirteçleri çıkarılır; kullanıcıya görünen hiçbir yerde çatının adı geçmez.

## Sayfa ↔ masaüstü sözleşmesi

Sayfa kodu masaüstüne **doğrudan değil**, `docs/masaustu_kopru.js`'in sunduğu `window.MatrisDosya` ve iki olay üzerinden bağlanır.
Aynı kod web sürümünde de çalışır (web'de iletişim kutusu yerine indirme / dosya seçici kullanılır).

### `window.MatrisDosya`

Bütün işlemler Promise döndürür; kullanıcı iletişim kutusundan vazgeçerse sonuç `null` olur.

| Üye | Masaüstünde | Web'de |
|---|---|---|
| `masaustu` | `true` | `false` |
| `kaydet(ad, icerik, tur, secenek?)` → `{ad, yol?}` | Yerel "Kaydet" iletişim kutusu (son klasör, tür süzgeci; uzantı yoksa eklenir). `tur === "matris"`: proje kaydı — pencerenin dosyası biliniyorsa **iletişim kutusu açmadan** ona yazar; `secenek.farkli` ile her zaman sorar. Başarılı proje kaydında pencere "temiz" olur. | `Blob` indirme |
| `ac(turler?, secenek?)` → `{ad, icerik, yol?}` | Yerel "Aç" iletişim kutusu. `turler` içinde `"matris"` varsa proje açar (pencere dosyaya bağlanır, son dosyalara eklenir). `secenek.ikili` → `icerik` `Uint8Array`. | `input[type=file]` (`accept` türlerden) |
| `pdfYazdir(html, ad)` → `{ad, yol?}` | Tam HTML → A4 PDF (yerel "Kaydet"); sonra "Klasörde göster" bildirimi | Yeni pencerede yazdırma (açılır pencere engelliyse görünmez çerçevede) |
| `degisti(kirli = true)` | Başlıkta **•**, kapatırken soru; `false` temiz demek | etkisiz |
| `projeKaynagi(fn)` | `fn() → {ad, icerik}` (projenin `.matris` metni). Kirliyken ~20 sn'de bir kurtarma kaydı alınır | etkisiz |
| `yeni()` | Pencerenin dosya bağını ve kirli bayrağını sıfırlar ("Yeni proje" sonrası çağırın) | etkisiz |
| `klasordeGoster(yol)` | Kaydedilen dosyayı dosya yöneticisinde gösterir | etkisiz |
| `bekleyenDosya()` | Henüz işlenmemiş son açılan dosyayı verir ve kuyruktan çıkarır (geç yüklenen sayfa betikleri için) | `null` |
| `kirliMi()`, `turCoz(tur, ad)` | Yardımcılar | aynı |

`tur`: `"matris"`, `"json"`, `"ifc"`, `"csv"`, `"tsv"`, `"html"`, `"pdf"`, `"txt"`, `"md"`, `"svg"`, `"png"`, `"dxf"`; uzantı (`".ifc"`),
MIME türü (`"text/csv"`) ya da boş (dosya adından) da olur. `icerik`: metin, `Blob`, `ArrayBuffer` ya da `Uint8Array`.
CSV'yi Türkçe tablo programları için `"﻿" + metin` (BOM) ve `;` ayırıcıyla vermek çağıranın işidir.

### Olaylar

İkisi de `window` üzerinde, `cancelable` `CustomEvent`'tir. Olayı **işleyen dinleyici `e.preventDefault()` çağırır**; işlenmeyen
komutlarda köprünün yerleşik davranışı çalışır, işlenmeyen dosyalar `bekleyenDosya()` ile alınabilir.

- **`masaustu-komut`** — `e.detail = {komut, ...ek}`: menüden ya da kısayoldan gelen komut. Ana süreç pencere kapatılırken
  "Kaydet" seçilirse `{komut: "kaydet", kapatmak: true}` gönderir; sayfa `MatrisDosya.kaydet(ad, metin, "matris")` ile kaydedince
  pencere kendiliğinden kapanır (vazgeçilirse açık kalır).
  Yerleşik davranışlar (işlenmezse): `geri-al` / `yinele` odak bir metin kutusundaysa metni geri alır / yineler; `sayfa` alt gezinti
  düğmesine tıklar; `ayarlar` Ayarlar penceresini açar; `yazdir` sayfayı yazdırır (Bina sayfası bu komutu kendisi işler ve statik
  raporu yazdırır, bkz. Komutlar ³); `kaydet` / `farkli-kaydet`, sayfa
  `MatrisDosya.projeKaynagi(fn)` bildirmişse projeyi `fn()`'in verdiği metinle kaydeder (yani bina sayfasının yalnız
  `projeKaynagi`, `degisti` ve `masaustu-dosya-acildi`'yi bağlaması Kaydet / Farklı kaydet / kapatırken kaydet için yeter).
- **`masaustu-dosya-acildi`** — `e.detail = {ad, icerik, yol?, kurtarma?}`: Dosya → Aç, son dosyalar, çift tıklama / komut satırı,
  sürükle-bırak ya da kurtarma ile gelen `.matris` / `.json` içeriği (metin, BOM'suz). `kurtarma: true` ise içerik otomatik kayıttan
  gelir; sayfa onu yükleyip `MatrisDosya.degisti(true)` demelidir. Dosyalar sayfanın bütün betikleri yüklendikten (`load`) sonra gelir.

Örnek bağlama (bina sayfası):

```js
window.addEventListener("masaustu-komut", function (e) {
  const d = e.detail;
  if (d.komut === "kaydet" || d.komut === "farkli-kaydet") {
    e.preventDefault();
    MatrisDosya.kaydet((bina.ad || "bina") + ".matris", projeMetni(), "matris", { farkli: d.komut === "farkli-kaydet" });
  } else if (d.komut === "coz") { e.preventDefault(); coz(); }
});
window.addEventListener("masaustu-dosya-acildi", function (e) {
  e.preventDefault();
  projeyiYukle(JSON.parse(e.detail.icerik));
  MatrisDosya.degisti(!!e.detail.kurtarma);
});
MatrisDosya.projeKaynagi(function () { return { ad: (bina.ad || "bina") + ".matris", icerik: projeMetni() }; });
// her model değişikliğinde: MatrisDosya.degisti(true)
```

### Komutlar

Tablo menü şablonunun (`lib/menu.js` → `komutListesi()`) birebir dökümüdür: her menü öğesi bir satır (aynı komut birden çok
menüde olabilir); `testler/js/masaustu.test.js` iki yönlü karşılaştırır, `testler/test_bina_kablolama.py` her komutun
`docs/bina.js`'te (ya da köprünün yerleşik davranışında) işlendiğini denetler.

¹ Sayfaya ait tuş: menüde gösterilir, ama tuş sayfaya gider (sayfanın kendi klavye işleyicisi; metin kutularının doğal davranışı
bozulmaz). Menüden tıklanınca yine komut gelir. macOS'ta Ctrl yerine ⌘; yinele ⇧⌘Z. Dosya → Aç (Ctrl+O), Yeni pencere,
Son dosyalar, Tam ekran (F11), yakınlaştırma, Yardım → Klavye kısayolları, Web sürümü, Kaynak kodu ve Hakkında ana süreçte
işlenir, sayfaya komut gelmez.

² `csv`: Bina sayfasının bütün tablolarını (Tablolar penceresindeki her tablo, `Tablo: başlık;grup;ad` satırıyla başlayan bölümler)
**tek bir CSV dosyasına** kaydeder: `;` ayırıcı, ondalık virgül, BOM (Türkçe yerel ayarlı tablo programları için). Pencere açılmaz.
CSV dosyası içe aktarılmaz; tablo verisi Tablolar penceresinde hücreleri tablo programından **yapıştırarak** girilir (⁴).

³ `yazdir`: Bina sayfasında statik raporu üretir (çözüm yoksa önce çözer) ve rapor penceresinde yazdırma iletişim kutusunu açar;
başka sayfada sayfa komutu işlemez ve köprünün yerleşik davranışı (`window.print()`) sayfayı yazdırır.

⁴ `tablolar`: Tablolar ve metraj penceresi (sarı hücreler düzenlenir; sekmeyle ayrılmış hücreler yapıştırılır, Ctrl+Z geri alır).

| `komut` | ek alanlar | Menü | Kısayol |
|---|---|---|---|
| `yeni` | | Dosya › Yeni proje | `Ctrl+N` |
| `kaydet` | | Dosya › Kaydet | `Ctrl+S` |
| `farkli-kaydet` | | Dosya › Farklı kaydet… | `Ctrl+Shift+S` |
| `json-iceri` | | Dosya › Bina verisi (.json)… | |
| `ifc` | | Dosya › IFC yapı modeli (.ifc)… | `Ctrl+E` |
| `csv` | | Dosya › Tablolar (.csv)… ² | |
| `json-disari` | | Dosya › Bina verisi (.json)… | |
| `rapor-html` | | Dosya › Statik rapor (.html)… | |
| `resim` | | Dosya › Görünüm resmi (.png)… | |
| `rapor-pdf` | | Dosya › Raporu PDF olarak kaydet… | `Ctrl+P` |
| `geri-al` | | Düzen › Geri al | `Ctrl+Z` ¹ |
| `yinele` | | Düzen › Yinele | `Ctrl+Y` ¹ |
| `eleman-kopyala` | | Düzen › Elemanları kopyala | |
| `eleman-yapistir` | | Düzen › Elemanları yapıştır | |
| `sil` | | Düzen › Seçileni sil | `Delete` ¹ |
| `secimi-birak` | | Düzen › Seçimi bırak | `Esc` ¹ |
| `tasi` | | Düzen › Taşı… | |
| `dondur` | | Düzen › Döndür… | |
| `ayna` | | Düzen › Ayna… | |
| `dizi` | | Düzen › Doğrusal dizi… | |
| `ozellik-ata` | | Düzen › Özellik ata… | |
| `mafsal` | | Düzen › Uç serbestlikleri (mafsal)… | |
| `yalniz-cekme` | | Düzen › Yalnız çekme | |
| `bol` | | Düzen › Böl… | |
| `kesisimde-bol` | | Düzen › Kesişimlerde böl | |
| `birlestir` | | Düzen › Birleştir | |
| `dugum-birlestir` | | Düzen › Düğümleri birleştir | |
| `ayarlar` | | Düzen › Ayarlar… | `Ctrl+,` |
| `sayfa` | `sayfa: "hesap"` | Görünüm › Hesapla | `Ctrl+1` |
| `sayfa` | `sayfa: "dersler"` | Görünüm › Dersler | `Ctrl+2` |
| `sayfa` | `sayfa: "se"` | Görünüm › Sonlu eleman | `Ctrl+3` |
| `sayfa` | `sayfa: "bina"` | Görünüm › Bina | `Ctrl+4` |
| `gorunum-3b` | | Görünüm › 3B görünüm | |
| `gorunum-plan` | | Görünüm › Plan (seçili Z aksında) | |
| `gorunum-on` | | Görünüm › Önden (seçili Y aksında) | |
| `gorunum-yan` | | Görünüm › Yandan (seçili X aksında) | |
| `sigdir` | | Görünüm › Modeli sığdır | `Ctrl+Shift+F` |
| `kat-suzgeci` | | Görünüm › Kat süzgeci… | |
| `yalit` | | Görünüm › Seçileni yalıt | |
| `tumunu-goster` | | Görünüm › Tümünü göster | |
| `tel-kafes` | | Görünüm › Tel kafes / katı | |
| `etiketler` | | Görünüm › Etiketler | |
| `arac-kutulari` | | Görünüm › Araç kutularını göster / gizle | `Ctrl+Shift+T` |
| `arac-ozellestir` | | Görünüm › Özelleştir… | |
| `arac-varsayilan` | | Görünüm › Varsayılan yerleşime dön | |
| `arac-disari` | | Görünüm › Yerleşimi dışa aktar… | |
| `arac-iceri` | | Görünüm › Yerleşimi içe aktar… | |
| `secim-kipi` | | Çizim › Seç | |
| `cubuk-ciz` | | Çizim › Çubuk çiz (iki kesişim) | |
| `hizli-cubuk` | | Çizim › Hızlı çubuk (aks parçası) | |
| `kolon-ekle` | | Çizim › Hızlı kolon | |
| `kiris-ekle` | | Çizim › Hızlı kiriş | |
| `capraz-ekle` | | Çizim › Hızlı çapraz… | |
| `doseme-ekle` | | Çizim › Hızlı panel / döşeme | |
| `egik-cubuk` | | Çizim › Eğik çubuk | |
| `uretec-makas` | | Çizim › Makas… | |
| `uretec-cerceve` | | Çizim › Beşik çerçeve… | |
| `uretec-asik` | | Çizim › Aşıklar… | |
| `uretec-kren` | | Çizim › Kren yolu… | |
| `sablon` | | Çizim › Şablondan bina… | |
| `mesnet-ata` | | Çizim › Mesnet ata… | |
| `yuk-ata` | | Çizim › Yük ata… | |
| `olc-uzaklik` | | Çizim › Uzaklık | |
| `olc-aci` | | Çizim › Açı | |
| `olc-alan` | | Çizim › Alan | |
| `olc-kot` | | Çizim › Kot farkı | |
| `olc-koordinat` | | Çizim › Koordinat sorgula | |
| `olc-temizle` | | Çizim › Ölçüleri temizle | |
| `yakalama` | | Çizim › Kesişimlere yakalama | |
| `aks-hizli` | | Aks › Hızlı aks (yeni model)… | |
| `aks-duzenle` | | Aks › Aks verisini düzenle… | `Ctrl+G` |
| `kat-duzenle` | | Aks › Katları düzenle… | |
| `aks-ekle` | | Aks › Aks ekle… | |
| `aks-sil` | | Aks › Aks sil… | |
| `aks-yapisik` | | Aks › Elemanlar akslara yapışık | |
| `aks-sistemi-ekle` | | Aks › Ek aks sistemi ekle… | |
| `aks-sistemleri` | | Aks › Aks sistemlerini düzenle… | |
| `aks-sistemi-sec` | | Aks › Görünür aks sistemi… | |
| `aks-yukari` | | Aks › Bir üst aks | `PageUp` ¹ |
| `aks-asagi` | | Aks › Bir alt aks | `PageDown` ¹ |
| `izgara` | | Aks › Aks ızgarasını göster / gizle | |
| `aks-balon` | | Aks › Aks balonları | |
| `aks-olcu` | | Aks › Ölçü zinciri | |
| `coz` | | Analiz › Çöz | `F5` |
| `yuk-durumlari` | | Analiz › Yük durumları… | |
| `kombinasyonlar` | | Analiz › Yük birleşimleri… | |
| `deprem` | | Analiz › Deprem parametreleri… | |
| `kar-ruzgar` | | Analiz › Kar ve rüzgâr… | |
| `tablolar` | | Analiz › Tablolar (düzenle, yapıştır)… ⁴ | `Ctrl+T` |
| `isi-haritasi` | | Analiz › Isı haritası | `Ctrl+Shift+H` |
| `yuk-akisi` | | Analiz › Yük akışı | |
| `sekil-degistirme` | | Analiz › Şekil değiştirmiş biçim | |
| `sonuclari-temizle` | | Analiz › Sonuçları temizle | |
| `tasarim-kontrol` | | Tasarım › Tüm kontroller | `F6` |
| `betonarme` | | Tasarım › Betonarme kiriş ve kolonlar | |
| `celik` | | Tasarım › Çelik elemanlar | |
| `temel` | | Tasarım › Temeller | |
| `kesit-oner` | | Tasarım › Kesit öner ve uygula | |
| `metraj` | | Tasarım › Metraj | |
| `rapor` | | Rapor › Statik hesap raporu | `F9` |
| `proje-bilgileri` | | Rapor › Proje bilgileri… | |
| `rapor-icerik` | | Rapor › Rapor içeriği… | |
| `rapor-pdf` | | Rapor › PDF olarak kaydet… | |
| `rapor-html` | | Rapor › HTML olarak kaydet… | |
| `yazdir` | | Rapor › Yazdır… ³ | `Ctrl+Shift+P` |
| `ifc` | | Rapor › IFC dışa aktar… | |
| `csv` | | Rapor › Tabloları CSV kaydet… ² | |
| `sayfa` | `sayfa: "dersler"` | Yardım › Dersler | `F1` |
| `sayfa` | `sayfa: "yardim"` | Yardım › Kullanım kılavuzu | |

### `window.masaustu` (ön yükleme betiği — doğrudan kullanmayın, `MatrisDosya` üzerinden)

| Üye | Kanal | Açıklama |
|---|---|---|
| `surum`, `platform` | — | program sürümü, işletim sistemi |
| `kaydet({ad, icerik, filtreler, baslik})` | `matris:kaydet` | dışa aktarma iletişim kutusu → `{ad, yol}` / `null` |
| `ac({filtreler, ikili, baslik})` | `matris:ac` | genel açma → `{ad, yol, icerik}` / `null` |
| `projeKaydet({ad, icerik, farkli})` | `matris:proje-kaydet` | proje kaydı (bilinen dosyaya doğrudan) |
| `projeAc()` | `matris:proje-ac` | proje açma; pencere dosyaya bağlanır |
| `pdfYazdir({html, ad})` | `matris:pdf` | HTML → PDF |
| `klasordeGoster(yol)` | `matris:klasorde-goster` | yalnız bu oturumda kaydedilenler |
| `degisti(kirli)`, `yeni()`, `otomatikKayit(icerik, ad)`, `hazir()` | `matris:kirli`, `matris:yeni`, `matris:otomatik-kayit`, `matris:hazir` | pencere durumu |
| `tamEkran()`, `yeniPencere()`, `harici(url)` | `matris:tam-ekran`, `matris:yeni-pencere`, `matris:harici` | pencere işleri, varsayılan tarayıcı |
| `komutDinle(fn)`, `dosyaDinle(fn)` | `matris:komut`, `matris:dosya-acildi` | ana süreçten gelenler; dönen işlev dinleyiciyi bırakır |

## Dağıtım (GitHub Actions)

`.github/workflows/masaustu.yml` elle (**Actions → Masaüstü sürümü → Run workflow**) ya da `v*` etiketi itilince çalışır:
Windows (NSIS kurulum + taşınabilir), macOS (arm64 ve x64 dmg; geçici imza) ve Linux (AppImage + deb) üç ayrı işte paketlenir
(`npm ci` → `npm run denetle` → Linux'ta birim testleri → `npm run hazirla` → `electron-builder --publish never`), çıktılar
"artifact" olarak saklanır. Etiketli çalıştırmada sürüm numarası etiketten alınır (`v1.2.3` → `1.2.3`) ve paketler GitHub
sürümüne eklenir. İş akışının yetkisi yalnız okuma; sürüm işi yalnız `contents: write` alır; eylemler işleme özetleriyle sabitlenmiştir.

## Testler

- `testler/js/masaustu.test.js` (`node --test`): `hazirla.js` yardımcıları, worker'ın yerel Pyodide adresi, ön yükleme yüzeyi (sahte
  çatı modülüyle), menü şablonu, Komutlar tablosu ↔ `komutListesi()` (iki yönlü), ana süreç yardımcıları, protokol sunucusu.
- `testler/test_masaustu.py` (pytest): sözdizimi, `package.json` / kilit dosyası / iş akışı alanları, git'e girmemesi gerekenler,
  `hazirla.js` çıktı yapısı (ağ yoksa atlanır), `MatrisDosya` web yolu ve masaüstü köprüsü (tarayıcıda, sahte `window.masaustu` ile),
  hazırlanan uygulamanın CDN'siz (çevrimdışı) motor yüklemesi ve bir bina şablonunun çözümü.
