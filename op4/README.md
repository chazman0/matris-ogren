# op4 — Opus Fortis yapısal modelleme ve analiz programı (yerel Windows uygulaması)

op4, Matris Öğren'in hesap motorunu (Python: `yapi.py`, `yapi_serbest.py`, `tasarim.py`, `rapor.py` …) gömülü olarak
kullanan, **web uygulaması olmayan**, kurulum dosyasıyla dağıtılan bir Windows programıdır (AutoCAD / Tekla benzeri).
Bu klasör programın **iskeletidir** (araç zinciri kanıtı): derleme, DirectX 12 çizimi, arayüz, gömülü Python, başsız
ekran testi ve kurulum paketi uçtan uca çalışır; modelleme komutları sonraki adımlardadır.

| Katman | Seçim | Not |
|---|---|---|
| Dil / derleyici | C++20, MSVC x64 (Visual Studio 2022+), statik CRT | VC++ yeniden dağıtılabilir paketi gerekmez |
| Grafik | Direct3D 12, donanım GPU'su (yüksek başarım tercihli), yoksa WARP | MSAA (donanımda 8×, WARP'ta 4×) + çözme; D32 **ters-Z** sonsuz perspektif |
| Arayüz | Dear ImGui (docking dalı, v1.92.9b, işleme özeti doğrulanır) | yerleştirme alanı, ana menü, Özellikler, Komut, durum çubuğu; PerMonitorV2 DPI |
| Hesap motoru | resmî Windows gömülebilir CPython 3.13 + numpy 2.5.3 + sympy 1.14.0 | `python3XX.dll` çalışma anında yüklenir (bağlama yok); tek işçi iş parçacığı |
| Kurulum | Inno Setup 6 → `op4-setup.exe` | Başlat menüsü, kaldırıcı, `.op4` ilişkilendirme, kullanıcıya özel kurulum seçeneği |

## Klasörler

```
op4/
  CMakeLists.txt          derleme (Dear ImGui FetchContent ile; OP4_IMGUI_DIZINI ile yerel kopya verilebilir)
  kaynak/                 C++ kaynakları
    ana.cpp               giriş noktası, komut satırı, test kipleri, uygulama döngüsü
    grafik.*              D3D12 aygıtı, takas zinciri, MSAA/derinlik hedefleri, boru hatları, ekran dışı okuma
    golgelendirici.h      HLSL (katı, çizgi, arka plan, sonsuz ızgara) — çalışma anında D3DCompile
    geometri.*            kesit (I/H profili, köşe yuvarlatmalı) → uzatılmış katı ağ + kenar çizgileri + çubuk ekseni
    kamera.h              yörünge kamerası; titreşimsiz (mutlak) kaydırma, imlece doğru yakınlaşma
    arayuz.*              ImGui arayüzü
    acilis.*              açılış (yükleme) ekranı, Opus Fortis logo yuvası
    motor.*               gömülü CPython köprüsü (web_kopru.calistir)
    proje.*               .op4 proje dosyası kaydet / aç, dosya pencereleri
    resim.*               PNG oku / yaz (WIC)
    gunluk.*              günlük
    op4.manifest, op4.rc.in   DPI farkındalığı, UTF-8 kod sayfası, simge, sürüm bilgisi
  kimlik/                 Opus Fortis kurumsal kimliği (logolar, palet), op4.ico, yer tutucular (bkz. kimlik/README.md)
  kurulum/op4.iss         Inno Setup betiği (UTF-8 BOM'lu)
  araclar/
    python_hazirla.py     gömülü Python + numpy/sympy + motor dosyaları → paket/python, paket/motor
    kimlik_uret.py        kurumsal simgeden op4.ico üretici
    yer_tutucu_kimlik.py  yer tutucu logo / simge üretici (gerçek kimlik yoksa yedek)
    mingw.cmake           Linux'ta MinGW-w64 ile sözdizimi / bağlama denetimi
```

Kurulu program düzeni: `op4.exe`, `kimlik\`, `python\` (python313.dll, python313.zip, `python313._pth`, numpy, sympy),
`motor\` (web_kopru.py ve motor modülleri, önceden derlenmiş `.pyc`).

## Derleme (Windows)

```
cmake -S op4 -B op4-yapi -A x64
cmake --build op4-yapi --config Release --parallel
cmake --install op4-yapi --config Release --prefix paket
python op4\araclar\python_hazirla.py --paket paket        :: Python 3.13 x64 ile çalıştırın
"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" /DPaket=%CD%\paket /DCikti=%CD%\dagitim op4\kurulum\op4.iss
```

## Komut satırı

| Komut | İş |
|---|---|
| `op4.exe [proje.op4]` | açılış ekranı → ana pencere |
| `op4.exe --test-motor` | gömülü Python + web_kopru: `surum_json()`, `calistir(bina_sablonlar)`, kuyruk üzerinden `determinant` ve `bina_sablon`; süreleri yazar |
| `op4.exe --test-ekran a.png [--boyut 960x540] [--arayuzsuz]` | pencere açmadan WARP ile tek kare çizer (arayüz dahil), PNG kaydeder; model piksel oranıyla sağlama |
| `op4.exe --test-acilis a.png [--olcek 1.5]` | açılış ekranını PNG'ye çizer |
| `op4.exe --test-pencere 8` | gerçek pencere + takas zinciri + motor; betikli kaydırma (imleç altındaki noktanın kayması), Shift+döndürme, tekerlek |
| ortak | `--gunluk dosya.log`, `--warp` (donanım yerine WARP), `--motorsuz`, `--surum` |

Çıkış kodları: 0 başarılı, 1 kullanım hatası, 2 test hatası, 3 zaman aşımı, 5 çökme. Test kiplerinde Windows hata
pencereleri kapatılır ve bir bekçi iş parçacığı süre sınırı uygular (CI asılı kalmaz).

Gezinme: **sol sürükle = kaydır**, **Shift + sol sürükle = döndür**, orta sürükle = kaydır, tekerlek = imlece doğru
yakınlaş, F = tümünü göster, K = kesit / çubuk görünümü, G = ızgara.

## CI

`.github/workflows/op4.yml` (windows-latest): yapılandır → derle → paket → `--test-motor` (soğuk + ılık) →
`--test-ekran` / `--test-acilis` (PNG'ler günlüğe `-----OP4-PNG-BASLA-----` / `-----OP4-PNG-BITIR-----` arasında base64) →
`--test-pencere` → Inno Setup → sessiz kur / kurulu programla motor testi / sessiz kaldır → özet tablosu → yapıtlar
(`op4-setup`, `op4-test-ciktilari`).

Yerel (Linux) denetim: MinGW-w64 ile derlenip Wine 9 + vkd3d + lavapipe (Xvfb) altında `--test-ekran`,
`--test-acilis` ve `--test-pencere --motorsuz` çalışır. Wine'da numpy içe aktarımı Wine'ın eksik bir işlevine
(0x80000100) takıldığı için `--test-motor` yalnız gerçek Windows'ta sınanır.

## CI ölçümleri (windows-latest, Visual Studio 18 2026 / MSVC 14.51, Python 3.13.16)

| Ölçü | Değer |
|---|---|
| CMake yapılandırma (Dear ImGui sığ klonu dahil) | ≈ 18 s |
| Derleme (Release, imgui + op4) | ≈ 21–28 s |
| Paket hazırlama (gömülü Python + pip + budama + .pyc) | ≈ 13–15 s (önbellekle) |
| Inno Setup derlemesi | ≈ 14 s |
| op4.exe (statik CRT) | 1,0 MB |
| python/ (CPython 3.13 + numpy 2.5.3 + sympy 1.14.0, budanmış) | 96 MB |
| motor/ (.py + .pyc) | 4,7 MB |
| op4-setup.exe (LZMA2) | 27,3 MB |
| Motor açılışı (DLL + Py_InitializeEx + import web_kopru + bina_sablonlar) | ≈ 350–410 ms (import web_kopru ≈ 320–380 ms) |
| WARP ekran dışı kare (640×360, MSAA 4×, arayüz dahil) | ≈ 7–11 ms |
| Gerçek pencere (Basic Render Driver, ekranı kaplayan) | ≈ 37 ms/kare; kaydırmada imleç altı kayma 0,0001 px |

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
* Wine 9 (yerel denetim): `EnumWarpAdapter` E_NOTIMPL, numpy içe aktarımı Wine taslak işlevine (0x80000100) takılır,
  dosya yönlendirmeli stdin ile Python başlamaz — bunlar Wine'a özgüdür, gerçek Windows'ta yoktur.
