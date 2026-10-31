# op4 — Opus Fortis yapısal modelleme ve analiz programı (yerel Windows uygulaması)

op4, Matris Öğren'in hesap motorunu (Python: `yapi.py`, `yapi_serbest.py`, `tasarim.py`, `rapor.py` …) gömülü olarak
kullanan, **web uygulaması olmayan**, kurulum dosyasıyla dağıtılan bir Windows programıdır (ticari CAD ve yapı modelleme programları benzeri).
Bu klasör programın **iskeletidir** (araç zinciri kanıtı): derleme, DirectX 12 çizimi, arayüz, gömülü Python, başsız
ekran testi ve kurulum paketi uçtan uca çalışır; modelleme komutları sonraki adımlardadır.

| Katman | Seçim | Not |
|---|---|---|
| Dil / derleyici | C++20, MSVC x64 (Visual Studio 2022+), statik CRT | VC++ yeniden dağıtılabilir paketi gerekmez |
| Grafik | Direct3D 12, donanım GPU'su (yüksek başarım tercihli), yoksa WARP | MSAA (donanımda 8×, WARP'ta 4×) + çözme; D32 **ters-Z** sonsuz perspektif |
| Arayüz | Dear ImGui (docking dalı, v1.92.9b, işleme özeti doğrulanır) | yerleştirme alanı, ana menü, Özellikler, Komut, durum çubuğu; PerMonitorV2 DPI |
| Hesap motoru | resmî Windows gömülebilir CPython 3.14 + numpy 2.5.3 + sympy 1.14.0 (sürüm + SHA256 sabit) | ayrı süreç `op4motor.exe` (`Py_Main` → `op4_sunucu`); iki boru üstünde tel protokolü; ana + tembel yardımcı motor; iptal, yeniden başlatma |
| Kurulum | Inno Setup 6 → `op4-setup-<sürüm>.exe` | Başlat menüsü, kaldırıcı, `.op4` ilişkilendirme, kullanıcıya özel kurulum seçeneği, Opus Fortis sihirbaz görselleri |

Belirtim ve aşamalı plan: [`MIMARI.md`](MIMARI.md) (bağlayıcı); özeti `TASARIM.md` §20.

## Klasörler

Faz 1 dört paketle paralel yürür; paketler arası arayüzler (sözleşme katmanı S1–S27), dosya sahipliği ve kabul denetimleri
[`MIMARI.md` §24 "F1 paket sözleşmeleri"](MIMARI.md)'ndedir (A derleme-motor, B model-cekirdegi, C arayuz-goruntu,
D dosya-cozum). Sahiplik tablosunu `testler/test_op4_sozlesme.py` denetler.

```
op4/
  CMakeLists.txt          hedefler: op4_cekirdek, op4_cekirdek_js (Windows + Linux), op4_cekirdek_testleri (doctest),
                          op4.exe ve op4motor.exe (Windows); kaynaklar klasör deseniyle (*_win.cpp / *_posix.cpp platforma göre)
  CMakePresets.json       ön ayarlar: win-surum, win-hata, linux-cekirdek, linux-cekirdek-asan (ASan + UBSan)
  cmake/                  Derleyici.cmake (uyarılar, OP4_UYARI_HATA varsayılan AÇIK, OP4_ASAN), Golgelendiriciler.cmake
                          (FXC SM 5.1), Bagimliliklar.cmake + bagimlilik_<ad>.cmake
                          (imgui, nlohmann/json 3.12.0, doctest 2.5.3; işleme özeti / SHA256 doğrulamalı; OP4_<AD>_DIZINI)
  golgelendiriciler/      op4.hlsl — tek kaynak: derlemede fxc ile vs_5_1 / ps_5_1 bayt koduna, op4.exe'ye gömülür
  kaynak/                 C++ kaynakları
    cekirdek/             platformdan bağımsız sözleşmeler ve uygulamaları (kimlik, sahne, öznitelik, seçim, seçme, görünüm,
                          model çekirdeği arayüzü, motor protokolü, hizmeti ve süreç istemcisi (motor_istemci.*), proje
                          belgesi / dosyası, ayarlar, sonuç, komut defteri, arayüz kancaları, Hizmetler, uygulama kabuğu)
    motor_barindirici/    op4motor.cpp — hesap motoru süreci: tutamaç temizliği, dosya denetimi, BLAS iş parçacıkları, Py_Main
    cekirdek_js/          model çekirdeği (B): QuickJS-ng ortamı (js_ortami.*), gömülü JS (JsGom), ModelCekirdegi köprüsü
    platform/             alt süreç (surec_win / surec_posix), dosya sistemi (atomik yazma, kullanıcı klasörleri)
    arayuz/ grafik/       C modülleri (arayuz_modulu.cpp, golgelendirici_bayt.*)
    dosya/ cozum/         D modülleri (dosya_modulu.cpp, cozum_modulu.cpp)
    ana.cpp               giriş noktası (komut satırı → kip)          secenekler.*   bayraklar ve test yardımcıları
    uygulama.cpp          açılış → ana pencere → döngü (kabuk + modüller)
    test_motor.cpp        --test-motor, --oz-sinama                    test_ekran.cpp --test-ekran, --test-acilis, --senaryo
    motor_modulu.cpp      MotorHizmeti = süreç istemcisi; "Hesap motoru" durum öğesi, Ayarlar › Hesap motoru,
                          motor.yeniden_baslat (OP4_MOTOR=gomulu: Faz 0 süreç içi motor, tanı)
    grafik.*              D3D12 aygıtı, takas zinciri, MSAA/derinlik hedefleri, boru hatları, ekran dışı okuma
    golgelendirici.h      golgelendiriciler/op4.hlsl metni (gömülü bayt kodu yoksa çalışma anı D3DCompile yedeği)
    geometri.*            kesit (I/H profili, köşe yuvarlatmalı) → uzatılmış katı ağ + kenar çizgileri + çubuk ekseni
    kamera.h              yörünge kamerası; titreşimsiz (mutlak) kaydırma, imlece doğru yakınlaşma
    arayuz.*              ImGui arayüzü (Faz 0)
    acilis.*              açılış (yükleme) ekranı, Opus Fortis logo yuvası
    motor.*               süreç içi gömülü CPython köprüsü (Faz 0; yalnız OP4_MOTOR=gomulu tanı kipi)
    proje.*               Faz 0 .op4 (JSON; kamera) kaydet / aç, dosya pencereleri
    resim.*               PNG oku / yaz (WIC)
    gunluk.*              günlük
    op4.manifest, op4.rc.in   DPI farkındalığı, UTF-8 kod sayfası, simge, sürüm bilgisi
  js/                     op4_cekirdek.js (QuickJS cephesi), op4_ops.js (yeni saf işlemler) — JSDoc sözleşmeleri
  motor/                  op4_sunucu.py (motor süreci sunucu döngüsü), op4_protokol.py (tel protokolü)
  veri/                   komutlar.json (37 F1 komutu, sahipleriyle), oznitelikler.json, sahne_kodlari.json; kurulumda <uygulama>\veri
  testler/                cekirdek/ (doctest), js/ (node), python/ (pytest), ortak/ (motor_protokol.json, profil_adlari.json)
  kimlik/                 Opus Fortis kurumsal kimliği (logolar, palet), op4.ico, yer tutucular (bkz. kimlik/README.md)
  kurulum/op4.iss         Inno Setup betiği (UTF-8 BOM'lu, CRLF); motor_gereksinimleri.txt (numpy, sympy, mpmath; SHA256)
  araclar/
    python_hazirla.py     gömülü Python + numpy/sympy + motor dosyaları → paket/python, paket/motor
    kimlik_uret.py        kurumsal simgeden op4.ico; --sihirbaz ile kurulum sihirbazı BMP'leri (7 DPI ölçeği)
    yer_tutucu_kimlik.py  yer tutucu logo / simge üretici (gerçek kimlik yoksa yedek)
    gunluk_png_yaz.py     CI: PNG → günlüğe base64 blok (::group::, sha256)
    gunluk_png_coz.py     günlükten (ya da günlük aracının JSON kaydından) PNG'leri çözer, sha256 denetler
    ci_bekle.sh           GitHub Actions çalışmasını bitene dek izler, adım tablosunu basar
    mingw.cmake           Linux'ta MinGW-w64 ile sözdizimi / bağlama denetimi
```

Kurulu program düzeni: `op4.exe`, `op4motor.exe`, `kimlik\`, `veri\` (komut kataloğu, öznitelik şeması, sahne kodları),
`python\` (python314.dll, python314.zip, `python314._pth`, numpy, sympy), `motor\` (web_kopru.py ve motor modülleri,
op4_sunucu.py, op4_protokol.py, önceden derlenmiş `.pyc`). Motor sunucu günlükleri:
`%LOCALAPPDATA%\Opus Fortis\op4\gunluk\motor-ana.log` ve `motor-yardimci.log` (önceki oturumunki `*.onceki.log`).

## Derleme (Windows)

```
cmake --preset win-surum -B op4-yapi [-DOP4_SURUM=X.Y.Z]          :: ya da: cmake -S op4 -B op4-yapi -A x64
cmake --build op4-yapi --config Release --parallel
ctest --test-dir op4-yapi -C Release --output-on-failure
cmake --install op4-yapi --config Release --prefix paket
python op4\araclar\python_hazirla.py --paket paket        :: Python 3.14 x64 ile çalıştırın
python op4\araclar\kimlik_uret.py --sihirbaz sihirbaz     :: kurulum sihirbazı görselleri (Pillow)
"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" /DSurum=X.Y.Z /DPaket=%CD%\paket /DCikti=%CD%\dagitim /DSihirbaz=%CD%\sihirbaz op4\kurulum\op4.iss
```

**Linux (yalnız çekirdek ve sınamaları):**

```
cmake --preset linux-cekirdek-asan && cmake --build --preset linux-cekirdek-asan     # clang, -Werror, ASan + UBSan
OP4_MOTOR_SINAMA_ZORUNLU=1 ctest --preset linux-cekirdek-asan                       # motor istemcisi ↔ python3 -m op4_sunucu
node --test op4/testler/js/*.test.js
python3 -m pytest op4/testler/python testler/test_web_kopru_op4.py -q -p no:cacheprovider
```

Motor sınamaları (`motor_*.cpp`, `test_sunucu.py`) sunucuyu `python3 -m op4_sunucu` olarak başlatır; çoğu sahte motorla
(yalnız standart kitaplık), gerçek `docs/web_kopru.py` sınamaları numpy + sympy ister. `OP4_MOTOR_SINAMA_ZORUNLU=1`
(CI) iken eksik Python / paket sınamayı düşürür.

Çevrim dışı derlemede bağımlılık klasörleri verilir: `-DOP4_NLOHMANN_JSON_DIZINI=… -DOP4_DOCTEST_DIZINI=… -DOP4_IMGUI_DIZINI=…`.

**Sürüm** tek kaynaktan gelir: `op4/CMakeLists.txt` içindeki `OP4_TABAN_SURUM` (Faz 0: `0.0.1`; `op4.iss` varsayılanı
aynıdır, `testler/test_op4_araclar.py` denetler). CI'da `op4-vX.Y.Z` etiketi itildiğinde sürüm etiketten alınır
(`-DOP4_SURUM`, `/DSurum`); op4.exe sürüm bilgisi, açılış ekranı, `--surum` çıktısı ve `op4-setup-X.Y.Z.exe` aynı değeri taşır.
`/DSihirbaz` verilmezse kurulum aracının varsayılan sihirbaz görselleri kullanılır. Sihirbazın karşılama sayfası açıktır
(sol panelde Opus Fortis görseli).

## Komut satırı

| Komut | İş |
|---|---|
| `op4.exe [proje.op4]` | açılış ekranı → ana pencere |
| `op4.exe --test-motor` | hesap motoru süreçleri (`op4motor.exe` → `op4_sunucu`): ana motorun açılışı, tembel yardımcı (`bina_sablonlar`, `determinant`), `bina_sablon`, `bina_kimlik`, anlatımsız `bina_coz`, hesap ortasında iptal, yeniden başlatma, kapanış; sunucu günlüklerini basar |
| `op4.exe --oz-sinama` | kurulu programın kendi kendini sınaması: motor, model çekirdeği ("Adsız 1", şablon), `.op4` kaydet / aç, ekran (uygulanmamış adımlar "atlandı") |
| `op4motor.exe --denetle` | kurulumun motor dosyalarını denetler (eksikse okunur ileti, çıkış 2) |
| `op4.exe --test-ekran a.png [--boyut 960x540] [--arayuzsuz]` | pencere açmadan WARP ile tek kare çizer (arayüz dahil), PNG kaydeder; model piksel oranıyla sağlama |
| `op4.exe --test-acilis a.png [--olcek 1.5]` | açılış ekranını PNG'ye çizer |
| `op4.exe --test-pencere 8` | gerçek pencere + takas zinciri + motor; betikli kaydırma (imleç altındaki noktanın kayması), Shift+döndürme, tekerlek |
| ortak | `--gunluk dosya.log`, `--warp` (donanım yerine WARP), `--motorsuz`, `--surum` |
| `--hata-katmani` | D3D12 hata ayıklama katmanını (varsa) açar; `--test-ekran` ve `--test-pencere`'de katmanın hata iletisi testi düşürür |
| `--golgelendirici-dizini <klasör>` | geliştirici: gömülü bayt kodu yerine `<klasör>\op4.hlsl` çalışma anında derlenir |
| `OP4_MOTOR=gomulu` (ortam) | tanı: süreç yerine Faz 0'ın süreç içi gömülü motoru |

Test kipleri ölçümleri günlüğe `OP4OLCUM anahtar=değer …` satırları olarak da yazar (`senaryo=motor|ekran|pencere`,
`hata_katmani=var|yok`, `hata_katmani_iletileri hata=… uyari=…`). Her `--test-ekran` katmanın varlığını yoklar.

Çıkış kodları: 0 başarılı, 1 kullanım hatası, 2 test hatası, 3 zaman aşımı, 5 çökme. Test kiplerinde Windows hata
pencereleri kapatılır ve bir bekçi iş parçacığı süre sınırı uygular (CI asılı kalmaz).

Gezinme: **sol sürükle = kaydır**, **Shift + sol sürükle = döndür**, orta sürükle = kaydır, tekerlek = imlece doğru
yakınlaş, F = tümünü göster, K = kesit / çubuk görünümü, G = ızgara.

## CI

`.github/workflows/op4.yml` (MIMARI §20). Tetikleyiciler: `main` ve `claude/**` dallarına itme ile çekme istekleri (yollar:
`op4/**`, `docs/*.js`, `docs/*.py`, kök `*.py`, iş akışı), `op4-v*` etiketleri (yol süzgeci uygulanmaz) ve elle başlatma.

**`windows` işi (`windows-2025`, sabit imaj):** sürüm → yapılandır → derle → paket (+ `--surum` denetimi) → `--test-motor`
(soğuk + ılık) → `--test-ekran` / `--test-acilis` → D3D12 hata ayıklama katmanı yoklaması (`System32\d3d12SDKLayers.dll`,
Graphics Tools özelliği; katman varsa `--hata-katmani` ile 0 hata iletisi aranır) → `--test-pencere` (**engelleyici**) →
Inno Setup (kurulu `license.txt`'nin ilk 60 satırı ve "commercial" geçen satırlar günlüğe basılır; sihirbaz görselleri
üretilir) → sihirbaz karşılama sayfasının ekran görüntüsü (tanı; hiçbir şey kurulmaz) → `C:\op4 dene ŞĞİı` yoluna sessiz
kurulum, kurulu programla `--test-motor` ve `--surum`, sessiz kaldırma ve klasör denetimi → özet → yapıtlar
(`op4-setup-<sürüm>`, `op4-test-ciktilari`).

**`yayinla` işi:** yalnız `op4-v*` etiketinde ve `windows` başarılıysa; `op4-setup-<sürüm>.exe` ve `.sha256` dosyasını o
etiketin GitHub sürümüne (Release) ekler (`contents: write` yalnız bu işte).

### Günlükten doğrulama (yapıtlar indirilemediğinde)

Ekran görüntüleri (`onizleme`, `sahne`, `acilis`, `sihirbaz`, `sihirbaz_ekran`) günlüğe 256 renge indirgenmiş PNG olarak
yazılır (`gunluk_png_yaz.py`; her biri `::group::OP4-PNG <ad>` içinde, `OP4-PNG ad=… bayt=… gunluk_bayt=… sha256=… gen=…
yuk=…` satırı ve `-----OP4-PNG-BASLA-----` / `-----OP4-PNG-BITIR-----` arasında base64). Okuma:

```
op4/araclar/ci_bekle.sh --isleme "$(git rev-parse HEAD)"          # arka planda; bitince adım tablosu
# günlük aracıyla işin günlüğü alınır (return_content, tail_lines ≥ 3000); sonuç bir dosyaya kaydedilir
python3 op4/araclar/gunluk_png_coz.py <kayıt.json ya da ham günlük> <klasör> --olcum
```

Çözücü zaman damgalarını ve `##[group]` satırlarını atar, sha256 ve boyutu denetler (bozuk / kesik blokta çıkış kodu 2) ve
`OP4OLCUM` satırlarını listeler.

Yerel (Linux) denetim: MinGW-w64 ile derlenip Wine 9 + vkd3d + lavapipe (Xvfb) altında `--test-ekran`,
`--test-acilis` ve `--test-pencere --motorsuz` çalışır. Wine'da numpy içe aktarımı Wine'ın eksik bir işlevine
(0x80000100) takıldığı için `--test-motor` yalnız gerçek Windows'ta sınanır.

## CI ölçümleri (windows-2025, Visual Studio 18 2026 / MSVC 14.51, Python 3.13.16)

| Ölçü | Değer |
|---|---|
| CMake yapılandırma (Dear ImGui sığ klonu dahil) | ≈ 18 s |
| Derleme (Release, imgui + op4) | ≈ 21–28 s |
| Paket hazırlama (gömülü Python + pip + budama + .pyc) | ≈ 13–15 s (önbellekle) |
| Inno Setup derlemesi | ≈ 14 s |
| op4.exe (statik CRT) | 1,0 MB |
| python/ (CPython 3.13 + numpy 2.5.3 + sympy 1.14.0, budanmış) | 96 MB |
| motor/ (.py + .pyc) | 4,7 MB |
| op4-setup-<sürüm>.exe (LZMA2) | 27,3 MB |
| Motor açılışı (DLL + Py_InitializeEx + import web_kopru + bina_sablonlar) | ≈ 350–410 ms (import web_kopru ≈ 320–380 ms) |
| WARP ekran dışı kare (640×360, MSAA 4×, arayüz dahil) | ≈ 7–11 ms |
| Gerçek pencere (Basic Render Driver, ekranı kaplayan) | ≈ 35–39 ms/kare; kaydırmada imleç altı kayma 0,0001 px |
| D3D12 hata ayıklama katmanı (Faz 0 kapanışı, run 41073083474) | imajda **var** (Graphics Tools kurulu); ekran ve pencere testinde 0 hata, 0 uyarı |
| Inno Setup | 6.7.1; kurulu `license.txt` ticari kullanım dahil serbest ("including commercial applications"; atıf ve değiştirilmiş sürüm koşulları) |
| Kurulum yolu `C:\op4 dene ŞĞİı` | sessiz kurulum ≈ 5 s, kurulu programla motor testi geçer, kaldırmada klasör tamamen silinir |

## Karşılaşılan tuzaklar

* Git Bash, `/nologo` gibi `/` ile başlayan bağımsız değişkenleri Windows yoluna çevirir (`C:/Program Files/Git/nologo`):
  MSBuild seçenekleri `-nologo -v:minimal` biçiminde verilir; Inno Setup adımı PowerShell'de çalışır.
* Windows'ta boruya yönlendirilen Python çıktısı cp1252'dir; Türkçe karakterli `print` UnicodeEncodeError verir
  (`PYTHONUTF8=1` + `sys.stdout.reconfigure(encoding="utf-8")`).
* Python başvuruları (`Py_DecRef`) `Py_FinalizeEx`'ten SONRA bırakılırsa erişim ihlali (0xC0000005) olur; C++ RAII
  sarmalayıcıları yorumlayıcı kapanmadan açıkça bırakılır.
* Gömülü Python geçersiz (bozuk) standart tutamaç devralırsa `init_sys_streams` ile süreci sonlandırır; tutamaç hiç
  yoksa (Gezgin'den / Start-Process ile açılış) sys.stdout = None olur ve sorun çıkmaz. Python yüklenmeden önce geçersiz
  tutamaçlar boşaltılır.
* CI'da yapıtlar ve ham günlük adresi (blob depolama) indirilemez: PNG'ler 256 renge indirgenip günlüğe base64 yazılır
  ve günlük GitHub API'siyle okunur.
* GPU'suz makinede "Microsoft Basic Render Driver" donanım bağdaştırıcısı gibi listelenir (WARP'tır).
* Varsayılan yığındaki tamponlar COPY_DEST başlangıç durumuyla oluşturulursa hata ayıklama katmanı uyarı #1328 verir
  (tamponlar her zaman COMMON başlar); COMMON ile oluşturulup kopyalamada örtük yükseltmeye bırakılır.
* `ISCC.exe`'nin dosya sürüm bilgisi 0.0.0.0'dır; Inno Setup sürümü kaldırma kaydındaki `DisplayVersion`'dan okunur.
* Wine 9 (yerel denetim): `EnumWarpAdapter` E_NOTIMPL, numpy içe aktarımı Wine taslak işlevine (0x80000100) takılır,
  dosya yönlendirmeli stdin ile Python başlamaz — bunlar Wine'a özgüdür, gerçek Windows'ta yoktur.
