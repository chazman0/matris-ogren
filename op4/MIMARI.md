# op4: Mimari Belirtim ve Aşamalı Plan

Taslak 2 (gözden geçirilmiş) · 2026-10-30 · Depo: `chazman0/matris-ogren` · Ürün: **op4** (Opus Fortis) · Hedef: Windows x64 yerel program, `op4-setup-<sürüm>.exe`

Bu sürüm iki girdiyle hazırlandı: Taslak 1'in bağımsız eleştirel incelemesi ve iskelet denemesinin CI'daki gerçek sonuçları. Deneme run 41063633682 (işleme `89f629a`, dal `claude/dreamy-franklin-nvl0oo`, henüz main'e birleşmedi) uçtan uca yeşil geçti. Değişen her karar §0'da kanıtıyla listelenir. Bu belge kendi başına bağlayıcıdır; Taslak 1'in yerini alır.

> **Ürün adı kuralı.** `testler/test_program_adi_yok.py` depoda başka yazılım ürünlerinin adını yasaklar. Bu belge ve op4'ün bütün metinleri (kod yorumları, arayüz, belgeler, katalog JSON'ları) bu kurala uyar. Karşılaştırmalarda "ticari CAD ve çelik detay programları", "yaygın yapı analiz programları" denir. Dil, kütüphane, standart ve platform adları serbesttir.
>
> **Düzeltildi (Faz 0 kapanışı):** denemenin `op4/README.md` 4. satırındaki iki yasak ürün adı kaldırıldı. Bekçi testi artık op4'ün C++, HLSL, CMake, kaynak, bildirim ve kurulum dosyalarını (`.cpp .h .hpp .hlsl .cmake .iss .nsi .rc .in .manifest .ini .ps1 .sh`) ve `op4/`, `.github/` altındaki bütün metin dosyalarını da tarar.

---

## 0. İnceleme: bulgular ve düzeltmeler

Önem düzeyleri: **K** kritik, **Y** yüksek, **O** orta, **D** düşük, **B** bilgi.

| No | Önem | Bulgu (Taslak 1 ya da deneme) | Kanıt | Düzeltme (bu taslak) |
|---|---|---|---|---|
| D1 | K | Ürün adı bekçisi kırık; ayrıca C++, HLSL ve iss uzantıları hiç taranmıyor | `op4/README.md:4`; `UZANTILAR` kümesinde `.cpp .h .iss` yok | Faz 0 kapanışında README düzeltilir ve uzantılar genişletilir. Deneme kaynakları tarandı; README dışında temiz. |
| D2 | Y | İptal varsayımı yanlış. `PyErr_SetInterrupt` yalnız Python'un işlediği sinyalde etkilidir. Deneme `Py_InitializeEx(0)` ile başlıyor, bu kipte SIGINT işleyicisi kurulmaz. İptal, bir paketin `signal` modülünü dolaylı içe aktarmasına kalırdı. | `op4/kaynak/motor.cpp:280` | Motor süreci Python'u olağan yoldan başlatır (`Py_Main`). Sunucu döngüsü Python'dadır ve açılışta `signal.signal(SIGINT, default_int_handler)` çağrılır. İptal `_thread.interrupt_main()` ile yapılır; son çare süreci sonlandırmaktır. CI'da sınanır (§8.4). |
| D3 | Y | Motor barındırıcısı gereğinden karmaşık. `PyConfig_InitIsolatedConfig` ve NuGet başlık/lib bağımlılığı öngörülmüştü; oysa PyConfig yapısının düzeni sürüme bağlıdır ve `GetProcAddress` ile güvenle kullanılamaz. | Deneme DLL'i çalışma anında yüklüyor; başlık ya da lib gerekmiyor | `op4motor.exe` yaklaşık 150 satırdır: tutamaç temizliği, dosya denetimi, `Py_Main(-X utf8 -m op4_sunucu …)`. Yalıtımı `._pth` sağlar. Protokol `op4/motor/op4_sunucu.py` içindedir ve Linux'ta python3 ile birebir test edilir. NuGet Python bağımlılığı kalkar. |
| D4 | Y | Protokol stdout'tan geçseydi motor modüllerindeki `print` çağrıları çerçeveyi bozardı. | `matris_ogren.py` 2, `yapi.py` 6 `print(` çağrısı | Protokol miras alınan ayrı boru tutamaçlarından geçer. fd 1 ve 2 günlük dosyasına yönlendirilir. |
| D5 | Y | Python 3.13 seçimi. 3.13 Ekim 2026'da yalnız güvenlik düzeltmesi evresine girdi; python.org bu evrede embeddable ikili yayımlamaz. | PEP 719 takvimi. PyPI'de numpy 2.5.3 cp314, scipy 1.18.1 cp314 ve ifcopenshell py314 win_amd64 tekerlekleri var. | op4'ün gömülü çalışma zamanı **3.14** olur. 3.15 çok yeni. Motor Linux CI'da hem 3.13 hem 3.14 ile test edilir; web sürümünün Pyodide Python'u ayrıdır. |
| D6 | Y | Genel (surum 3) modelde radye ve mütemadi temel yok. op4'te çizim komutları ve IFC içe aktarma genel model üretir. Bu yüzden ±%2 analiz ağı eniyilemesinin ana ailesi (radye, mütemadi) op4'ün asıl akışında hiç bulunmaz. | `yapi_serbest.py:975` `TEMEL_TIP_HATASI` | Faz 7a: temel ızgarası ve Winkler yayları genel modele taşınır (Python). Paralel izde yürür; Faz 6'dan önce bitmesi hedeflenir. |
| D7 | Y | Yoğun çözücüde ölçek sınırı. 6000 SD'de matris başına ≈ 290 MB bellek ve O(n³) süre gerekir. Gerçek IFC binaları 20–60 bin SD tutar. | `yapi.py:2584` `np.linalg.solve`, `yapi_serbest.py:2428` `np.linalg.inv(Kff)` | Faz 5'te "motor ölçeği" işi: SD eşiğinin üstünde isteğe bağlı bant ya da seyrek çözüm yolu (scipy, BSD). Yoğun yolla 1e-9 eşdeğerlik aranır. Kullanıcı kararı gerekir (§23). |
| D8 | O | "Bit düzeyinde aynı" ölçütleri gerçekçi değil. numpy vektörleştirmesi toplama sırasını değiştirir. Windows'taki OpenBLAS çekirdekleri (EPYC) Linux'takilerden farklıdır. QuickJS ile V8'in Math.sin, cos ve atan2 son basamakları farklı olabilir. | Taslak 1 Faz 5 ölçütleri, Faz 1 `--oz-sinama` ölçütü | Platformlar ve uygulamalar arası karşılaştırmalar toleranslıdır: motor için bağıl 1e-9, JS çekirdek için 1e-12. Bayt eşitliği yalnız aynı yürütücüdeki gidiş-dönüşte aranır. |
| D9 | O | Sıralama hatası. `katUyeligi`, `kullanimYeri` ve `oznitelikCikar` Faz 4'teydi; oysa Faz 1'deki model gezgini (kata göre sayılar, tıkla seç) ve "Hedef katlar" bunlara dayanıyor. | Taslak 1 Faz 1 ve 3 iş listeleri | Bu işlevler Faz 1'e alınır. |
| D10 | O | Sıralama: Seç ve Süz ile atama kapsamları çizim komutlarından önce gelmeli. Değiştirme komutları (KOPYALA, TAŞI, KATLARAKOPYALA, ÖZELLİKEŞLE) ve her seçim istemindeki "Süzgeç…" seçeneği bu altyapıyı kullanır. Altyapı şablonlarda ve içe alınan modellerde hemen işe yarar, ayrıca daha küçük ve az risklidir. | Bağımlılık çözümlemesi | Yeni sıra: Faz 3 Seç ve Süz ve atama (istek 2, 3); Faz 4 çizim ve düzenleme (istek 1, 2). |
| D11 | O | IFC dışa aktarma Faz 5'e ertelenmişti. Kullanıcı bugün sahip olduğu bu özelliği korumak istiyor ("export olduğu gibi import da"). Çekirdek `ifc_disari.js`'i değişmeden çalıştırdığı için iş, bir menü ve dosya penceresinden ibaret. | İstek 7 | Faz 1'e alınır. |
| D12 | O | Gölgelendirici hattı. Taslak 1 DXC ve SM 6.0 diyordu; deneme çalışma anında FXC ile SM 5.0 derliyor ve bu açılışa 40–67 ms ekliyor. SM 6 özelliğine ihtiyaç yok. | `grafik.cpp:74,285` | Gölgelendiriciler derlemede Windows SDK `fxc.exe` ile SM 5.1'e derlenir ve bayt kodu başlığa gömülür. DXC ancak gerekirse gelir. |
| D13 | O | D3D12 hata ayıklama katmanı CI'da hiç sınanmadı. Yalnız `OP4_HATA_AYIKLAMA` derlemesinde açılıyor ve Server 2025 imajında Graphics Tools (`d3d12SDKLayers.dll`) bulunmayabilir. | `grafik.cpp:112–119` | Faz 0 kapanışında katmanın varlığı yoklanır. Yoksa yalnız test derlemesinde Agility SDK NuGet paketindeki SDKLayers kullanılır. GPU tabanlı doğrulama yalnız gecelik işte açılır. **Sonuç (Faz 0 kapanışı):** windows-2025 imajında katman var; `--hata-katmani` ile ekran ve pencere testleri 0 hata, 0 uyarı. |
| D14 | O | Kurulum aracının lisansı doğrulanmadı. Inno Setup'ın yeni sürümlerinde ticari kullanım için ücretli lisans şartı getirildiği biliniyor; jrsoftware.org bu ortamdan erişilemedi. Opus Fortis ticari bir kullanıcıdır. | — | CI, kurulu `license.txt` dosyasının başını günlüğe basar. Şart varsa lisans alınır ya da NSIS'e (zlib) geçilir; NSIS `masaustu/` paketinde zaten kullanılıyor. **Sonuç (Faz 0 kapanışı):** imajdaki Inno Setup 6.7.1'in `license.txt`'si ticari kullanım dahil serbest; atıf ve değiştirilmiş sürüm koşulları var. |
| D15 | O | Kimlik varsayımı eskidi. Taslak 1 "logo sonra gelecek" diyordu; gerçek dosyalar `op4/kimlik/` altında duruyor ve deneme bunları açılış ekranında, simgede ve temada kullanıyor. | `op4/kimlik/README.md` | §18 gerçek dosya adlarıyla yeniden yazıldı. `kimlik_uret.py` kullanılır; palet README'den alınır. |
| D16 | O | Klasör çakışması. Taslak 1'de `op4/kaynak/` veri klasörüydü (komutlar.json); denemede C++ kaynak klasörü. | Deneme ağacı | C++ kodu `op4/kaynak/` altında alt klasörlere ayrılır; veriler `op4/veri/` altına gider. |
| D17 | O | Belge bölmesinde hava boşluğu. `NoAutoMerge` çözümü ImGui çoklu görünüm alanını gerektirir; bu denemede kapalı ve DX12'de her pencere için ayrı takas zinciri demek. | Deneme notları | Belge içeriği ayrı, üst düzey bir "Belge penceresi"nde açılır (§15). Hava boşluğu sorunu doğmaz. |
| D18 | O | Proje başına sekme Faz 1'i şişiriyor: belge başına JSContext, motor önbelleği, görünüm kümesi. | Taslak 1 §3 | 1.0'da pencere başına bir proje olur. İkinci dosya yeni bir op4 penceresinde açılır. Kopyala-yapıştır süreçler arası özel pano biçimiyle çalışır. Yardımcı motor tembel başlar. |
| D19 | O | ifcopenshell ayrıntıları eksikti. 0.9.0.post1 iki haftadan yeni (2026-10-15). Bağımlılıkları shapely (GEOS, LGPL), lark, isodate, python-dateutil, pyparsing ve typing-extensions. win_amd64 tekerleği ≈ 43 MB. | PyPI | 0.9.0 (2026-09-29) sabitlenir. IFC içe aktarma isteğe bağlı kurulum bileşeni olur. LGPL lisans metinleri ve kaynak bağlantıları eklenir. |
| D20 | O | "Filtrelenebilir bütün özellikler" eksik kalmıştı: kullanıcı etiketleri, IFC özellik kümeleri (Pset), durum ve kombinasyon bazlı sonuçlar yoktu. "katman" ise ortada bir katman sistemi olmadan listelenmişti. | Taslak 1 §11.2 | `etiketler`, `kullanici.*`, `ifc.pset.*` ve indisli sonuç öznitelikleri eklenir; ETİKET komutu gelir. "katman" kaldırılır. |
| D21 | D | Temel CAD komutu ÖLÇEKLE yok; ModelOps'ta da yok. | `model_ops.js` taraması | `op4_ops.olcekle` eklenir (Faz 4). |
| D22 | D | Denemede tek harf kısayollar var (F, K, G); bu, komut satırı kuralıyla çelişir. | `op4/README.md` | Faz 1'de Shift+F, Ctrl+Shift+K ve F7 olur. |
| D23 | D | Dosya kilidi ile atomik yazma çelişiyor. Açık FILE_SHARE_READ tanıtıcısı dururken ReplaceFileW başarısız olur; OneDrive klasörlerinde paylaşım ihlalleri görülür. | Taslak 1 §12.2 | Yerine koymadan önce tanıtıcı kapatılır, işlem yeniden denenir. Denemenin JSON biçimli `.op4` dosyası da okunur. |
| D24 | D | Günlükten PNG çözme ve CI bekleme araçları depoda değil, yalnız oturum klasöründe duruyor. | Deneme raporu | Bu araçlar `op4/araclar/` altına alınır; PNG satırına sha256 eklenir. |
| D25 | D | `windows-latest` kayıyor: VS 18 2026 ve MSVC 14.51 geldi. Altın görüntüler WARP sürümüne bağlıdır. | Deneme günlüğü | `runs-on: windows-2025` sabitlenir; üretici adı verilmez, `-A x64` yeterlidir. |
| D26 | D | Karma GPU'lu dizüstülerde ayrık GPU'yu seçtiren dışa aktarımlar (NvOptimusEnablement, AmdPowerXpressRequestHighPerformance) denemede yok. Bu istek 9'u ilgilendirir. | `grafik.cpp` | Faz 1'de eklenir. |
| D27 | D | ImGui fare konumunu tamsayıya yuvarlar; betikli olaylar bir sıra kuralına uymalıdır. | Deneme tuzağı 8 | Gezinme hesabı Win32 olaylarından yapılır; ImGui yalnız arayüz isabetini belirler. |
| D28 | D | `python/` klasörü yaklaşık 6 bin dosya; virüs tarayıcıları kurulumu ve ilk içe aktarmayı yavaşlatır. | Paket ölçümü | Saf Python paketleri (sympy, mpmath, motor) önceden derlenmiş `.pyc` olarak zip içinde taşınır. Etkisi ölçülerek karar verilir. |
| D29 | D | Türkçe karakterli kurulum yolu sınanmadı; kullanıcı başına kurulumda yol `C:\Users\Şükrü…` olabilir. | — | CI'da `C:\op4 dene ŞĞİı` yoluna kurulum yapılır. |
| D30 | D | İki motor süreci çekirdek sayısı kadar OpenBLAS iş parçacığı açar ve işlemciyi aşırı yükler. | — | Ana motor çekirdek−1, yardımcı motor 1 iş parçacığıyla çalışır; ayar numpy içe aktarılmadan önce yapılır. |
| D31 | B | Masaüstü (Electron) sürümü Faz 8'e kadar kullanılacak ve titreşim orada sürüyor. | `docs/bina.js:1585–1587`, `cizim3b.js` `jestler` | İsteğe bağlı geçici düzeltme (Faz 1): yaklaşık 20 satırlık çapa düzeltmesi ve fare eşlemesinin çevrilmesi. |
| D32 | B | Motorda plak ya da kabuk sonlu elemanı yok. İstek 10 döşeme ağlarını da kapsıyor olabilir. | `TASARIM.md` §16, §12 | Kullanıcı kararı (§23). |
| D33 | B | Tahminler ölçümle düzeltildi: motor hazır olma süresi 0,35–0,55 s (Taslak 1 ≤ 4 s varsaymıştı); kurulum dosyası 27,3 MB (Taslak 1: 50–90 MB). | Deneme | §3.2 ve §6.13 güncellendi. |
| D34 | B | Masaüstüne CSV içe aktarma eklendi; Taslak 1'in "her şey op4'te" listesinde yoktu. Analiz ayarları paneli de açıkça yazılmamıştı. | `tablo_editoru.js` CSV ayrıştırıcısı | Faz 5'e eklendi. |
| D35 | B | Web tarafında (`docs/*.js`) başka oturumlar paralel geliştirme yapıyor; çekirdek API'si kayabilir. | Depo etkinliği | Eşdeğerlik derlemi ve sözleşme testleri bunu yakalar. `docs/` modüllerinde yalnız eklemeli değişiklik yapılır. |

---

## 1. Kararlar özeti

| Konu | Karar | Dayanak |
|---|---|---|
| Ürün biçimi | `op4.exe` (arayüz; statik CRT, 1,0 MB) ve `op4motor.exe` (Python barındırıcısı; iki süreç: ana ve tembel yardımcı). `op4-setup-<sürüm>.exe` Inno Setup ile üretilir (lisans doğrulanır; yedek NSIS). Açılışta gerçek Opus Fortis logolu açılış ekranı vardır. | Deneme yeşil (§3.2) |
| Arayüz | Dear ImGui v1.92.9b-docking (işleme `b48d1af…` doğrulanır) ve Win32 kabuk. Yerel `IFileDialog` ve `TaskDialogIndirect`. | Deneme: Türkçe yazı, docking, WARP'ta tam ekran görüntüsü |
| Grafik | Doğrudan Direct3D 12. Donanımda MSAA 8×, WARP'ta 4×. Ters-Z ve sonsuz uzak düzlem (D32). Gölgelendiriciler derlemede FXC SM 5.1 ile derlenir. Kamera-göreli koordinat, örneklenmiş kesit ağları, sabit piksel kalınlıklı çizgiler. | Deneme; D12 |
| Gezinme | Sol sürükle kaydırır, Shift+sol sürükle döndürür, tekerlek imlece doğru yakınlaştırır, orta sürükle kaydırır. Hesap mutlak çapaya göredir. | Deneme: kayma 0,0001 px |
| Hesap motoru | Mevcut Python motoru. CPython 3.14 embeddable ayrı süreçte çalışır, sunucu döngüsü Python'dadır, borular ayrıdır. Protokol `web_kopru.calistir` JSON'udur. | D2–D5 |
| Model çekirdeği | QuickJS-ng; `docs/` altındaki saf JS modülleri değişmeden çalışır. | Taslak 1 kararı korunur |
| Belge içerikleri | Dersler, rapor önizleme ve yazdırma, adım adım matematik ayrı "Belge penceresi"nde gösterilir (WebView2, yerel dosyalar, ağ yok). Kullanıcı onayı gerekir; yerel matematik denemesi seçenek olarak sunulur. | D17, §15 |
| Proje dosyası | `.op4` ZIP'tir. Denemenin JSON biçimli `.op4` dosyası da açılır. Kaydet, Farklı kaydet, Aç, otomatik kayıt, kurtarma ve son dosyalar desteklenir. | İstek 6 |
| IFC | Dışa aktarma Faz 1'de (QuickJS'te `ifc_disari.js`). İçe aktarma Faz 6'da (`ifc_iceri.py`, ifcopenshell 0.9.0, isteğe bağlı bileşen). | D11, D19 |
| Görüntü ağı ±%2 | Analitik dış çizgi; Hausdorff ≤ %2·min(h, b) ve A, I_y, I_z ±%2 koşulunu sağlayan en az köşeli LOD0; ekran uzayı LOD'u. | İstek 5, 9, 10 |
| Analiz ağı ±%2 | `ag_eniyile.py`: Richardson ve GCI. Önkoşul: genel modelde radye ve mütemadi temel (Faz 7a). | D6 |
| Motor ölçeği | Yoğun çözüm varsayılan kalır. SD eşiğinin üstünde isteğe bağlı bant ya da seyrek çözüm yolu (Faz 5). | D7 |
| Başlangıç | Program boş model "Adsız 1" ile açılır. Şablonlar Başlangıç panelinde ve Dosya › Yeni › Şablondan menüsünde durur. | İstek 4 |
| Serbest çizim | Her yeni nokta en parametrik başvuruyla yazılır (REF öncelik sırası). Katı §19 kipi proje ayarıdır. | Kullanıcı onayı (§23) |
| Belge modeli | Pencere başına bir proje. | D18 |
| CI | Linux çekirdek işi ve Windows işi (`windows-2025`). Ekran görüntüleri ve ölçümler günlüğe yazılır. | Deneme |

---

## 2. Hedefler, kapsam, ilkeler

### 2.1 İstek → bölüm → faz

| # | İstek | Bölüm | Faz |
|---|---|---|---|
| 1 | Temel çizim komutları | §12 | 4 |
| 2 | Çizimde, yük ve mesnet atamada kat ya da kullanım yeri bazlı seçim | §10.2, §10.3, §11.6, §11.7, §12.6 | 1 (öznitelikler, gezgin), 3 (atama kapsamları), 4 (hedef katlar) |
| 3 | Seç ve Süz: bütün filtrelenebilir özellikler (bütün HE340A'lar, bütün kirişler…) | §11 | 3 |
| 4 | Boş çalışma sayfasıyla başla, şablonlar kalsın | §5.2, §13.4 | 1 |
| 5 | Kesitleri gerçek biçimiyle gör; çubuk ya da kesit görünümü seçilebilsin | §6.6, §6.7 | 2 (denemede yalnız sabit bir I profili ve geçiş tuşu var) |
| 6 | Kaydet, Farklı kaydet, Aç | §13 | 1 (denemede yalnız kamera kaydediliyor) |
| 7 | IFC içe aktarma; dışa aktarma da korunur | §14 | Dışa 1, içe 6 |
| 8 | Titreşimsiz kaydırma; sol tık kaydırsın, Shift+sol tık döndürsün | §7 | Denemede kanıtlandı; Faz 1'de seçim ve komutlarla birleşir |
| 9 | Yakın planda kalite düşmesin; DX12 ve GPU kullanılsın | §6 | Temeli denemede; Faz 1 ve 2 |
| 10 | Eleman ağ eniyilemesi ±%2 | §6.11 (görüntü), §17 (analiz) | 2, 7 |
| — | Program olsun: op4 adı, setup dosyası, Opus Fortis logolu açılış ekranı | §18 | Denemede çalışıyor; Faz 0 kapanışı |
| — | Her şey op4'e: Bina, Sonlu eleman, Matris, Dersler | §15, §16 | 1–5, 8 |

### 2.2 İlkeler

1. **Program, web değil.** Pencere, şerit, menüler, görünüm alanı, komut satırı, özellik ızgarası, tablolar, iletişim kutuları ve dosya işlemleri yereldir. op4 sunucu açmaz ve ağ isteği yapmaz. WebView2 yalnız Belge penceresinde, kurulumla gelen yerel belgeleri gösterir.
2. **Motor sözleşmesi korunur.** `web_kopru.py` şemaları bağlayıcıdır; motora yalnız eklemeli, isteğe bağlı parametreler eklenir. `pytest testler` ve `node --test testler/js/*.test.js` değişmeden geçer.
3. **Tek kaynak.** Motor modülleri kökte, JS çekirdek modülleri `docs/` altındadır. op4 bunları paketler. Komut, kısayol ve öznitelik katalogları `op4/veri/` altındaki JSON'lardan üretilir.
4. **Önce belge.** Her faz kodu yazmadan önce kendi TASARIM.md bölümünü ekler:
   - TASARIM §20 op4 mimarisi, §21 .op4 biçimi, §22 komut çerçevesi, §23 sorgu dili
   - TASARIM §24 görüntü ağı, §25 IFC içe aktarma, §26 ağ eniyileme, §19.4 serbest düğüm
5. **Sınanabilirlik.** Her etkileşim betikli bir senaryodan sürülebilir. Platformdan bağımsız C++ çekirdeği ve motor sunucusu Linux'ta test edilir.
6. **Sayısal karşılaştırma kuralı.** Platformlar ve uygulamalar arası karşılaştırmalar bağıl toleranslıdır: motor için 1e-9, JS çekirdek için 1e-12. Bayt eşitliği yalnız aynı yürütücü içindeki gidiş-dönüşte aranır (D8).
7. **Türkçe arayüz.** Gösterimde ondalık virgül kullanılır; birimler kN ve m'dir. Kod adları depodaki gibi ASCII Türkçedir.
8. **Bağımlılık kuralı.** Her bağımlılık sabit sürüm, işleme özeti ya da SHA256 ile alınır. Sürüm en az iki hafta önce yayımlanmış olmalıdır.

### 2.3 Kapsam dışı (bu plan)

- macOS ve Linux için op4.
- Plak ve kabuk sonlu elemanı (kullanıcı kararı, §23), ikinci mertebe analiz, kapasite tasarımı.
- Otomatik güncelleme, lisans sunucusu, çok kullanıcılı düzenleme.
- Çizim paftası çıktısı ve DXF alt katmanı. Bunlar 1.0 sonrası iş listesindedir.
- Colab defteri (`Matris_Ogren.ipynb`, `defter_yap.py`) olduğu gibi sürer.

---

## 3. Mevcut durum

### 3.1 Envanter ve yeniden kullanım

| Bileşen | Boyut (satır) | op4'teki yeri |
|---|---|---|
| Kök motor: `matris_ogren`, `sonlu_eleman`, `yapi`, `yapi_serbest`, `yapi_veri`, `tasarim`, `temel`, `rapor`, `tablolar`, `alan` | ≈ 34 bin | `op4motor` içinde çalışır. Paketleme kökten yapılır; `docs/` kopyalarının aynılığı CI'da denetlenir. |
| `docs/web_kopru.py` | 915 | Giriş noktası; yalnız ek işlemler eklenir. |
| `docs/model_ops.js` (2659), `aks_sistemi.js` (2768), `bina_cizim.js` (2781; SAF kısmı), `ifc_disari.js` (2318), `tablo_editoru.js` (1635; `_ic`) | ≈ 8,5 bin saf mantık | QuickJS'te değişmeden çalışır. DOM katmanları `window` ve `document` tanımsız olduğu için kurulmaz (`bina_cizim.js:35`). |
| `bina.js` (6538), `cizim3b.js` (403), `arac_kutusu.js` (1833), `eleman_bilgi.js` (1639), `olcum.js` (873), `isi_haritasi.js` (2592), `se.js` (1290), `app.js` (1433) | ≈ 16,6 bin | C++, ImGui ve DX12 ile yeniden yazılır; davranışları belirtim kaynağıdır. |
| `etkilesim*.js` (≈ 8,3 bin), `dersler.json`, KaTeX, marked | — | Belge penceresinde yeniden kullanılır. |
| `masaustu/` (Electron) | ≈ 1,5 bin | Faz 8'e kadar sürer, sonra kaldırılır. |
| Deneme `op4/` | ≈ 4,2 bin (C++, CMake, iss, Python) | Faz 1'in başlangıç noktası (§19). |

### 3.2 CI denemesinin kanıtladıkları (run 41063633682)

| Konu | Sonuç |
|---|---|
| Araç zinciri | Windows 10.0.26100 (Server 2025), Hyper-V, EPYC 7763, 16 GB. VS 18 2026, MSVC 19.51 (14.51), CMake 4.4.4. Varsayılan üretici "Visual Studio 18 2026"; `-A x64` yeterli. |
| Süreler | Yapılandırma, ImGui klonuyla birlikte, 17–19 s. Release derleme 21–28 s. Paketleme önbellekle 13–15 s. ISCC 14–17 s. Sessiz kurulum 7–8 s. İş toplamı ≈ 2,5 dk. |
| Boyutlar | op4.exe 1,0 MB (statik CRT). `python/` 96,1 MB: 3.13.16, numpy 2.5.3, sympy 1.14.0; budamayla ≈ 19 MB ayıklandı. `motor/` 4,7 MB. Kurulum dosyası 27,3 MB (LZMA2/max, solid). |
| Gömülü Python | DLL `LoadLibraryExW` ile yükleniyor; başlık ve lib gerekmiyor. DLL yükleme 1,4–5 ms, Py_InitializeEx 10–13 ms, `import web_kopru` 320–512 ms, `bina_sablonlar` 13–18 ms (9 şablon). Kuyruktan determinant 1,9 ms, Py_FinalizeEx 45–70 ms. GUI açılışında std tutamaçları yok, yine de çalışıyor. |
| WARP | `EnumWarpAdapter`, özellik düzeyi 12_1, MSAA 4× (R8G8B8A8, D32). Ekran dışı kare 640×360'ta 7–11 ms, 960×540'ta 15–30 ms. Aygıt ve gölgelendirici hazırlığı 55–260 ms (derleme 40–67 ms). Gerçek pencerede 206–217 kare, ≈ 37–39 ms/kare. "Basic Render Driver" pencere kipinde SOFTWARE bayrağı taşımıyor: VendorId 0x1414 ve DeviceId 0x8C ile tanınıyor. |
| Gezinme | Kaydırmada imleç altındaki noktanın kayması 0,0001 px. Shift+sürüklede Δyaw −1,0400 rad (beklenen). Tekerlekte kayma 0,0000 px. |
| Kurulum | Inno Setup 6 imajda kurulu. Betik UTF-8 BOM'lu; Türkçe ve İngilizce. `{autopf}\Opus Fortis\op4`; kullanıcı başına kurulum seçeneği; `.op4` ilişkilendirmesi; MinVersion 10.0.17763. Sessiz kurulum, kurulu exe ile motor testi ve sessiz kaldırma temiz geçiyor. |
| Ekran görüntüsü | 256 renge indirgenmiş PNG, base64 olarak günlükte: önizleme 42 KB, sahne 48 KB, açılış 9,7 KB. Çözüldü ve incelendi: docking'li arayüz ve Türkçe karakterler, ışıklı ekstrüde çelik çerçeve, sonsuz ızgara, gerçek logolu açılış ekranı. |
| Yerel denetim | MinGW-w64 13 ile derleniyor. Wine 9, vkd3d ve lavapipe (Xvfb) altında `--test-ekran`, `--test-acilis` ve `--test-pencere --motorsuz` çalışıyor. numpy Wine'da çalışmıyor. |

**Tuzaklar (artık kural):**
1. Git Bash, `/` ile başlayan bağımsız değişkenleri yola çevirir. MSBuild seçenekleri `-nologo` biçiminde yazılır; ISCC ve kurulum adımları pwsh'ta çalışır.
2. Windows'ta Python'un boru çıktısı cp1252'dir. `PYTHONUTF8=1` ve `reconfigure(utf-8)` kullanılır.
3. Py_DecRef, Py_FinalizeEx'ten sonra çağrılırsa erişim ihlali olur. Başvurular sonlandırmadan önce bırakılır.
4. Geçersiz std tutamacı devralınırsa `init_sys_streams` süreci sonlandırır. Tutamaçlar Python'dan önce temizlenir; zip, `._pth` ve `web_kopru.py` önceden denetlenir.
5. Program Files salt okunurdur. `.pyc` dosyaları UNCHECKED_HASH ile önceden derlenir.
6. `._pth` içeriği: `python3XX.zip`, `.`, `Lib\site-packages`, `..\motor`; `import site` yoktur.
7. Basic Render Driver SOFTWARE bayrağı taşımaz.
8. ImGui fare konumunu tamsayıya yuvarlar. Betikli konum olayları NewFrame'den sonra, düğme ve tekerlek olaylarından önce eklenir.
9. ImGui'nin varsayılan yazı tipinde Türkçe glif yoktur. Sırasıyla Segoe UI, Arial, Tahoma yüklenir.
10. Wine'a özgü sorunlar (gerçek Windows'ta yok): `EnumWarpAdapter` E_NOTIMPL döndürür, numpy içe aktarımı bir taslak işleve takılır, dosya yönlendirmeli stdin ile Python başlamaz.
11. MCP günlük aracının varsayılan 500 satırlık kuyruğu orta adımları kaçırır; günlüğün tamamı alınıp kaydedilen dosyada aranır.
12. Aynı dala paralel itme olabilir; her itmeden önce getirilip birleştirilir.

**Denemede eksik kalanlar:**
- İsteklerin hiçbiri iskeletin ötesinde uygulanmadı.
- `.op4` dosyası yalnız kamerayı saklıyor; C++ tarafında JSON ayrıştırıcı yok.
- Bina, Sonlu eleman, Matris ve Dersler arayüzleri yok; `dersler/` paketlenmiyor.
- Gölgelendiriciler çalışma anında derleniyor.
- Gerçek GPU sınanmadı.
- İmza, etiketten sürüm damgası ve Release yayımı yok.
- Çoklu görünüm alanı kapalı; ekranlar arası canlı DPI değişimi sınanmadı.
- Gerçek pencerenin takas zincirinden ekran görüntüsü alınmadı.
- `--test-pencere` adımı `continue-on-error` ile işaretli.

### 3.3 Motor süreleri

| Ölçüm | Linux (4 vCPU, 3.13) | Windows CI (EPYC) |
|---|---|---|
| `import web_kopru` | 0,95 s | 0,32–0,51 s |
| `betonarme-3kat-3x3` (216 SD), `bina_coz` | 2,9 s; yanıt 0,98 MB | Faz 1'de ölçülür |
| `celik-sanayi-4hol` (1392 SD), anlatımlı / anlatımsız | 17,4 s / 12,5 s | Faz 1'de ölçülür |

Sanayi çözümünün profili: `_durumlari_coz` 9,3 s (durum başına sonuç çıkarımı 4,7 s, diyagram hazırlığı 1,7 s, yoğun çözüm 3,2 s), `_tasarim` 3,5 s, `ozet` 3,2 s.

### 3.4 Web sürümünde titreşimin ve yakınlaşınca kalite kaybının kök nedenleri

1. **Geri besleme.** `cizim3b.js` `jestler()` her harekette noktayı o anki viewBox'a göre okur (`kamera.svgNokta`). Fark `kaydir` ile viewBox'a uygulanır (`bina.js:1587`). Sonraki ölçüm kaydırılmış kutuda yapıldığı için salınım oluşur.
2. **Kare başına tam SVG yeniden üretimi** (`sahneCiz`).
3. **Koordinat yuvarlama.** Koordinatlar 0,1 birime yuvarlanır (`cizim3b.js:19`, `r1`). 20× yakında bu 2 px'lik basamaklar demektir.
4. **Olaylar kareyle birleştirilmez.**
5. **Fare eşlemesi ters.** `kipSec` sol sürüklemeyi döndürmeye bağlar (`bina.js:1585`).

op4'teki çözümler mutlak çapa gezinmesi, GPU'da durağan tamponlar ve çift hassasiyetli kameradır. Bunlar denemede ölçüldü (§3.2) ve K1–K5 değişmezleriyle kilitlenir (§7.4).

---

## 4. Üst düzey mimari

```
┌──────────────── op4.exe  (pencere başına bir proje; çok iş parçacığı) ────────────────┐
│ UI iş parçacığı : Win32 döngüsü → girdi birleştirme → ImGui → Komut yöneticisi → D3D12  │
│ Çekirdek       : QuickJS-ng JSContext (model otoritesi, geri al yığını)                 │
│ Motor G/Ç      : boru çiftleri ↔ op4motor süreçleri; yanıtlar UI kuyruğuna              │
│ İş havuzu      : kesit ağı/LOD kovaları, BVH, zip/PNG, öznitelik zenginleştirme, IFC ağı │
└──────┬────────────────────────────┬────────────────────────────────┬─────────────────┘
  boru çifti (4 B uzunluk + UTF-8 JSON)   boru çifti                      (Faz 5) owned pencere
┌──────▼──────────────────┐  ┌──────▼────────────────────────┐  ┌──────▼──────────────────┐
│ op4motor  "ana"          │  │ op4motor  "yardımcı" (tembel)  │  │ Belge penceresi          │
│ Py_Main → op4_sunucu.py  │  │ matris, ders, se_*, kütüphane, │  │ WebView2, yalnız         │
│ web_kopru.calistir,      │  │ deprem önizleme, ifc_iceri     │  │ https://belge.op4/ →     │
│ çözüm önbelleği          │  │ (OPENBLAS 1 iş parçacığı)      │  │ <kurulum>\belge          │
└──────────────────────────┘  └───────────────────────────────┘  └──────────────────────────┘
```

**Düzenleme akışı:**
1. Komut noktaları toplar; yakalama C++ BVH üstünde yapılır.
2. Önizleme yalnız üst katmanda çizilir.
3. İşleme anında çekirdeğe tek işlem gider: `uygula(islem, parametreler)`.
4. Çekirdek eklenen, silinen ve değişen kümelerin raporunu döndürür.
5. `sahne()` tipli dizileri verir.
6. UI yalnız değişen örnekleri yazar, BVH'yi yeniler, sonuçları "eski" işaretler ve otomatik kayıt zamanlayıcısını kurar.

**Çözüm akışı:**
1. F5'te çekirdekten `metin()` alınır.
2. Ana motora `bina_coz` gönderilir (`anlat:false`).
3. Dönen `veri` ile `SonucOzeti` kurulur; çekirdekte `sonucEsle` çalışır; D/C renkleri güncellenir.
4. Ayrıntı işlemleri istendikçe `cozum_kimligi` ile çağrılır.

**Proje durumu:**
- Dosya yolu ve kirli bayrağı
- Çekirdek bağlamı
- `SahneAnlik` (değişmez) ve `OznitelikTablosu` (sütunlu)
- `Secim`, `SecimKumeleri`, `Suzgecler`
- `Gorunumler` (kamera, kip, kesit kutusu, görünürlük)
- `SonucOzeti` (cozum_kimligi, D/C dizileri, eski mi)
- GPU kaynakları

`ElemanKimligi = {tur: u8 (Cubuk, Panel, Dugum, Mesnet, Yuk, Aks, AksSistemi, Temel, Referans, Olcu), no: u32, alt: u16}`.

---

## 5. Arayüz (Dear ImGui)

### 5.1 Karar

ImGui seçilir. Gerekçeler:
- CI'da FetchContent ile saniyeler içinde derlenir (deneme: 18 s yapılandırma).
- DX12 arka ucu aynı takas zincirine çizer; böylece penceresiz WARP ile tam ekran görüntüsü alınır.
- CAD etkileşimi (yakalama işaretleri, tutamaçlar, lastik bant) anlık çizimle doğal yazılır.
- ≈ 1 MB, MIT lisanslı.

Bedeli: şerit, özellik ızgarası, tablo düzenleyici, komut satırı ve bildirimler özel yazılır (≈ 6–8 bin satır, Faz 1–5'e dağıtılır). Erişilebilirlik ve IME desteği sınırlıdır (§5.11).

Yardımcılar: ImPlot (grafikler), imgui_freetype ve FreeType (Faz 2), nanosvg (simge atlası), Win32 (`IFileDialog`, `TaskDialogIndirect`, OLE sürükle-bırak, pano, `SHAddToRecentDocs`).

### 5.2 Pencere düzeni ve boş başlangıç

**Üst bölüm:**
- Başlık: "op4 — proje.op4 •".
- Hızlı erişim çubuğu: Yeni, Aç, Kaydet, Geri al, Yinele, Çöz.
- Şerit sekmeleri: Dosya, Model, Çizim, Düzenle, Seçim, Yükler, Mesnet ve Temel, Analiz, Sonuçlar, Tasarım, Rapor, Görünüm, Öğren, Yardım. İstenirse klasik menü çubuğu da açılır.

**Orta bölüm:**
- Çalışma alanı sekmeleri: **Bina** (proje), **Sonlu eleman**, **Matris**. Dersler Belge penceresinde açılır.
- Bina alanında docking ile bölünebilen 3B, Plan, Cephe ve Kesit görünümleri vardır.
- Görünüm küpü ve düzlem seçici şerit bulunur.

**Kenar panelleri ve alt şerit:**
- Sol: Model gezgini.
- Sağ: Özellikler, Sonuçlar, Tasarım.
- Alt: komut satırı ve durum çubuğu. Durum çubuğunda imleç koordinatı, etkin kat ve düzlem, YAKALA (F3), IZGARA (F7), DİK (F8), IZG.YAKALA (F9), KUTUPSAL (F10), DİNAMİK (F12), seçilebilirlik çipleri, seçim sayısı, motor durumu ve grafik bağdaştırıcısı yer alır. Deneme bağdaştırıcıyı "DirectX 12 · … · MSAA 4×" diye gösteriyor.

**Açılış:**
- Program her zaman boş model "Adsız 1" ile açılır. Görünüm alanında Z = 0 çalışma ızgarası görünür.
- Sağda katlanabilir Başlangıç paneli vardır: Boş model, Hızlı aks sihirbazı, Şablondan yeni (9 şablon, küçük resimli), Aç, Son dosyalar, IFC içe aktar (Faz 6).
- Ayar: "Açılışta Başlangıç panelini göster".

**Yerleşim:** ImGui docking; kullanıcı klasöründe `arayuz.ini`; "Arayüzü sıfırla" komutu.

### 5.3 Şerit, menü, bağlam menüsü

- Hepsi `op4/veri/komutlar.json` dosyasından üretilir.
- Kullanılamayan komut soluk görünür ve ipucunda nedenini yazar (ör. "Böl: önce çubuk seçin").
- Sağ tık menüsü seçimin türüne göre kurulur: Bilgi, Özellikler, Isı haritasında incele, Yük akışı, Tasarım ayrıntısı, Kesit öner ve uygula, Benzerini seç, Gizle, Yalıt, Sil.
- Komut sırasında sağ tık menüsünde Enter, İptal ve komutun seçenekleri bulunur.

### 5.4 Komut satırı ve kısayollar

- Görünüm alanı odaktayken yazılan harfler komut satırına gider. Tek tuşla anında çalışan harf kısayolu yoktur.
- Denemedeki F, K ve G kısayolları Faz 1'de Shift+F (sığdır), Ctrl+Shift+K (kesit görünümü) ve F7 (ızgara) olur.
- Ctrl, Shift ve F tuşlu kısayollar anında çalışır.
- Dinamik giriş (F12) imlecin yanında görünür; ayrıntı §12.

### 5.5 Özellik ızgarası

- Satırlar öznitelik şemasından gelir. Çoklu seçimde farklı değerler "(çeşitli)" olarak görünür.
- Kesit alanında arama kutusu vardır: "HE340A" yazmak "HEA 340"yi bulur. Uç serbestlikleri için 6+6 onay kutusu vardır.
- Bir düzenleme çekirdeğe tek işlem olarak gider ve tek geri al adımıdır. Hata satırın altında öğretici metinle görünür.
- Faz 1'de salt okunurdur; düzenleme Faz 3'te gelir.

### 5.6 Model gezgini

```
Proje
├─ Aks sistemleri
├─ Seviyeler ve katlar
│   └─ Kat k → Kolon / Kiriş / Döşeme / Çapraz / … → kullanım yeri (köşe, kenar, iç…) (sayılarla)
├─ Temeller · Kesitler · Malzemeler · Yük durumları
├─ Seçim kümeleri · Süzgeçler
└─ Referans modeller (IFC)
```

- Bir düğüme tık o kümeyi seçer; Ctrl ile ekler (istek 2).
- Faz 1'de kat, tür ve sayı düğümleri vardır; tam sürüm Faz 3'te gelir.

### 5.7 Tablolar

`bina_tablolar` TABLO şeması yerel tablo düzenleyicide gösterilir (Faz 5):
- `ImGuiListClipper` sayesinde 100 bin satır akıcı kaydırılır.
- Sütunlar sıralanır, süzülür ve dondurulur; düzenlenebilir hücreler sarıdır.
- "Uygula" komutu çekirdekte `tabloUygula` çalıştırır; tek geri al adımıdır.
- Sekmeyle ayrılmış veri yapıştırılabilir.
- **CSV içe aktarma** `tablo_editoru.js` ayrıştırıcısıyla yapılır.
- CSV dışa aktarma BOM, `;` ve ondalık virgül kullanır.
- Satıra tık o elemanı seçer.

### 5.8 İletişim kutuları ve bildirimler

- Dosya pencereleri `IFileDialog` ile açılır (denemede var).
- Soru pencereleri `TaskDialogIndirect` ile gösterilir.
- Uzun işler durum çubuğunda ilerleme gösterir ve iptal edilebilir.
- Bildirimler tost olarak çıkar. "Uyarılar" panelinde bir uyarıya tık ilgili elemanı seçer.

### 5.9 Yazı tipi, DPI, tema

- **Yazı tipleri:** sistemdeki Segoe UI, sonra Arial, sonra Tahoma (denemede çalışıyor). Bunlara simge ve matematik glifleri için Segoe UI Symbol ve Cambria Math birleştirilir. Paketli Noto Sans (OFL) yedek olarak kalır. Komut satırında JetBrains Mono (OFL) kullanılır.
- **Faz 2:** imgui_freetype ile hafif ipucu ve ImGui 1.92 dinamik yazı tipleri; `WM_DPICHANGED`'de yazı tipi atlası yeniden kurulmaz.
- **DPI:** manifestte PerMonitorV2, UTF-8 kod sayfası ve longPathAware bildirilir (denemede var).
- **Tema:** kimlik paleti; antrasit #14181B zemin, kahve #8A6B3C vurgu, altın #B08950 seçim, krem #EDE6D8 yazı (denemede var). Açık tema da vardır. Eleman türü renkleri mevcut 3B anlamlarını korur.

### 5.10 Belge penceresi ilişkisi

- WebView2 içeriği ana pencerenin docking alanına konmaz. Ayrı bir üst düzey pencerede açılır (ana pencereye ait, görev çubuğunda tek simge).
- Böylece ImGui menüleri ile HWND arasında hava boşluğu sorunu doğmaz ve çoklu görünüm alanı gerekmez.
- İleride yerleştirme istenirse WebView2 görsel barındırma (CompositionController ve DirectComposition) denenir.

### 5.11 Bilinen sınırlar

Ekran okuyucu desteği yoktur. Türkçe klavye IME gerektirmez, `WM_CHAR` yeterlidir; Doğu Asya IME'si temel düzeydedir. Görünüş yerel denetimlerden farklıdır. Bunlar kabul edilir ve kayıt altına alınır.

---

## 6. Grafik motoru (Direct3D 12)

### 6.1 Aygıt, takas zinciri, kaynaklar

**Adaptör:**
- `EnumAdapterByGpuPreference(HIGH_PERFORMANCE)` kullanılır (denemede var); en az D3D_FEATURE_LEVEL_11_0 gerekir.
- `NvOptimusEnablement` ve `AmdPowerXpressRequestHighPerformance` dışa aktarılır (Faz 1, D26).
- Donanım yoksa WARP kullanılır. Basic Render Driver VendorId 0x1414 ve DeviceId 0x8C ile tanınır; durum çubuğunda "yazılım işleyici" uyarısı çıkar ve MSAA 4× ile sınırlanır.
- Ayarlar › Grafik'te adaptör ve MSAA düzeyi (1, 2, 4, 8) seçilebilir.

**Takas zinciri:**
- `FLIP_DISCARD`, 3 tampon, `FRAME_LATENCY_WAITABLE_OBJECT`, `SetMaximumFrameLatency(1)` (denemede var).
- Sahne MSAA ara hedefe çizilir ve çözülür; arayüz çözülmüş tampona çizilir.
- Faz 2'de sRGB görünümlü hedeflerle gamma-doğru kenar yumuşatmaya geçilir.

**İsteğe bağlı çizim:**
- Girdi, animasyon ya da yeni veri yoksa kare üretilmez (`MsgWaitForMultipleObjectsEx`).
- Sürüklemede kuyruktaki fare iletilerinin yalnız sonuncusu kullanılır.

**Kaynaklar:**
- Faz 1'de commit'li kaynaklar ve halka yükleme kullanılır.
- Faz 2'de D3D12MA'ya geçilir.
- Tek gölgelendirici-görünür tanımlayıcı yığını vardır; ImGui 1.92'nin tanımlayıcı ayırıcısı bu yığından beslenir.

**Gölgelendiriciler:**
- Derlemede Windows SDK `fxc.exe` ile `vs_5_1` ve `ps_5_1` hedeflerine derlenir; bayt kodu başlığa gömülür. Hatalar derlemede yakalanır, açılıştaki 40–67 ms kalkar.
- Çalışma anı derlemesi yalnız `--golgelendirici-dizini` geliştirici kipinde vardır.

**Hata ayıklama:**
- `--grafik-denetim` hata ayıklama katmanını açar.
- CI yoklaması ve Agility SDK yedeği için bkz. D13.
- Aygıt kaybında DRED raporu yazılır, kaynaklar yeniden kurulur ve belge kaybolmaz.

### 6.2 Hassasiyet ve koordinatlar

- Model CPU'da `double` tutulur. GPU'ya sahne çapasına göreli `float` yazılır.
- Kamera çapadan 1 km'den fazla uzaklaşırsa çapa yeniden belirlenir.
- Derinlik D32 ters-Z'dir; perspektifte uzak düzlem sonsuzdur (denemede var).
- IFC'den gelen 500 000 m gibi büyük koordinatlarda titreme olmaz.

### 6.3 Çizim geçişleri

1. Opak katılar (kesit ağları, döşemeler, temeller).
2. Kenar çizgileri (derinlik ofsetiyle; denemede kırılma açılı normaller ve kenar çizgileri var).
3. Çubuk görünümü ve noktalar: ekran uzayında genişletilmiş, analitik kenar yumuşatmalı dörtgenler.
4. Saydam geçiş: önce sıralı yarı saydam çizim; yoğun saydam sahnede (IFC referans katmanı) WBOIT.
5. Üst katman: vurgu, tutamaçlar, yakalama işaretleri, lastik bant, ölçüler.
6. MSAA çözümleme.
7. Etiketler ve ImGui.

Sonsuz ızgara gölgelendiricide analitik çizilir (denemede var); aralık 0,05–100 m arasında uyarlanır.

### 6.4 Veri ve örnekleme

- **ProfilKutuphanesi:** her (kesit geometrisi, LOD) çifti için birim boylu ekstrüzyon ağı ve kenar listesi tutulur.
- **UyeOrnegi** (64 bayt): `p_i`, `p_j` (çapaya göreli), y′, `h_olcek_i` ve `h_olcek_j` (vute), profil-LOD dizini, renk, bayraklar, eleman kimliği.
- Her (profil, LOD) kovası için bir `DrawIndexedInstanced` çağrısı yapılır.
- LOD seçimi ve kovalama gezinme bitince yapılır (150 ms boşta ya da ölçek 1,5× değişince), iş havuzunda ve atomik değişimle.
- **Gezinmede CPU geometri üretimi ve örnek tamponu yazımı sıfırdır** (K2). Ekran uzayı etiketleri K2'nin dışındadır.
- Model değişince yalnız eklenen, silinen ve değişen örnekler yazılır.

### 6.5 Çubuk görünümü

- Sabit piksel kalınlığı: varsayılan 2 px, seçili 3 px.
- Renk tür paletinden gelir (kolon, kiriş, çapraz, makas, aşık, kren, bağ, diğer).
- Mafsallı uç içi boş daireyle, yalnız çekme çubuğu piksel uzayında kesik çizgiyle gösterilir.
- Düğümler noktadır; serbest düğümün ayrı simgesi vardır.
- Mesnetler ekran boyutlu SDF simgeleridir.
- Yükler ok ve değerle gösterilir; durum başına açılıp kapanır.

### 6.6 Kesit (katı) görünümü

**Kesit geometrisinin tek kaynağı** `ifc_disari.js` içindeki `kesitCoz` işlevidir (satır 681). Bu işlev şu an dışa aktarılmıyor; Faz 2'de eklemeli olarak dönüş nesnesine eklenir. Motorun `_kesit_kart` çözüm sırasıyla aynıdır. Döndürdüğü kayıt: `{tur, ölçüler (m), köşe yarıçapları, UPN eğimi, 2L aralığı, vute}`.

Dış çizgiler:
- I/H: kütüphanedeki gövde–başlık yarıçapı r ile (`yapi_veri.PROFILLER` 5. alan).
- KUTU: r_o = 1,5t, r_i = t.
- BORU, betonarme dikdörtgen, dolu daire.
- L: kök yarıçapı r1 (EN 10056-1 tablosu) ve uç yarıçapı r2 = r1/2.
- 2L: aralık s.
- UPN: %8 eğim, r = tf, r2 = tf/2.
- Vute: üst yüz hizalı, derin uçta alta doğru büyür.

Yönelim: `aci = 0` iken kesitin h doğrultusu y′'dür.

**Görünüm kipleri:**
- Çubuk | Kesit | Kesit ve eksen çizgisi.
- Tür bazlı geçersiz kılma yapılabilir; kısayol Ctrl+Shift+K.
- Görsel hizalama: varsayılan analiz eksenidir. "Üst yüz hizalı" ve "uçları kolon yüzüne kırp" seçenekleri yalnız görüntüyü değiştirir ve rozetle belirtilir.

### 6.7 Paneller ve temeller

- Panel çokgeni çekirdekteki `panelGeometrisi` ile kurulur. earcut ile tam üçgenlenir ve kalınlık kadar ekstrüde edilir; üst yüz düğüm düzlemindedir.
- Kalınlığı 0 olan sac panel ince, yarı saydam bir yüzeydir. Cephe panelleri yarı saydamdır.
- Temeller katıdır: tekil, mütemadi (ters T) ve radye.

### 6.8 Etiketler, aks balonları, ölçüler

- Bütün yazılar ekran uzayında, ImGui arka plan çizim listesiyle çizilir; her yakınlıkta keskindir.
- Aks çizgileri dünya uzayında kesik çizgidir; balonları ekran uzayındadır. Planda ölçü zincirleri gösterilir.
- Çakışma ayıklama ekran kovalarıyla yapılır. Öncelik: seçili > aks > ad > değer.

### 6.9 Seçme ve vurgu

- CPU BVH: çubukta kesit prizması ya da kapsül, panelde çokgen, düğümde küre testi.
- Üzerine gelme: çubukta ekran uzaklığı ≤ 4 px (DPI ölçekli); 100 bin elemanda 1 ms'nin altında.
- Pencere ve kesişen seçimi izdüşüm testleriyle yapılır.
- "Yalnız görünenler" seçeneği R32_UINT kimlik tamponu ve eşzamansız geri okuma kullanır (Faz 3).
- Vurgu bayt bayrak tamponuyla güncellenir.
- BVH ve testler çekirdektedir ve Linux'ta test edilir.

### 6.10 Sonuç görselleştirme (Faz 5)

Hepsi `bina_alan` istasyon verisinden gelir:
- Şekil değiştirmiş biçim (animasyonlu).
- N, Vy, Vz, T, My, Mz diyagram şeritleri.
- Isı haritası: `isi_haritasi.js` ve `alan.py` kuralları; node altınlarıyla test edilir.
- D/C bantları, tepki okları, Navier panel alanları, radye basıncı ve oturma.
- Durum, kombinasyon ve zarf seçici.

### 6.11 Görüntü ağı ±%2 (bağlayıcı tanım)

S tam (analitik) dış çizgi, S₀ LOD0 dış çizgisi olsun. LOD0 şu koşulları sağlar:
- (a) d_H(S, S₀) ≤ 0,02·min(h, b);
- (b) A, I_y ve I_z bağıl sapmalarının her biri ≤ 0,02. S₀ için sayısal (çokgen) değerler, S için kapalı biçimli analitik değerler kullanılır;
- (c) (a) ve (b)'yi sağlayan **en az köşeli** dış çizgi seçilir.

Analitik değerler katalogla da karşılaştırılır (≤ %1). Örnek: IPE 80'de analitik A = 2·46·5,2 + 69,6·3,8 + (4−π)·5² = 764,3 mm², katalogda 7,64 cm².

Yöntem:
- Yay n parçaya bölünür; n, e = r(1 − cos(θ/2n)) ≤ ε olacak en küçük değerdir.
- Örnek: IPE 80'de ε = 0,92 mm ve r = 5 mm iken yay başına 2 parça yeter. Köşeyi keskinleştirmenin sapması 2,07 mm olduğu için yay atılamaz.
- HEA 340'ta ε = 6 mm ve r = 27 mm iken yine 2 parça yeter.
- Tam dairelerde alan korumalı çokgen kullanılır.
- Normaller analitiktir; yuvarlak yüzeyler pürüzsüz görünür.
- Bütün kütüphane profilleri birim testle denetlenir.

Uzaklık LOD'ları: LOD1 yay tek parça, LOD2 kutu prizması, LOD3 çizgi. Bir LOD ancak sapmasının ekran izdüşümü ≤ 0,5 px ise kullanılır. Yakın planda her zaman LOD0 çizilir. Ölçme, yakalama ve dışa aktarma analitik geometriyi kullanır.

Ağ iyileştirme:
- meshoptimizer ile köşe önbelleği, aşırı çizim ve getirme sıralaması iyileştirilir; 16 bit dizin kullanılır.
- IFC referans ağlarında `meshopt_simplify` mutlak hata kipiyle çalışır: hata = 0,02 × en küçük sınır kutusu kenarı (alt sınır 0,05 m). Gerçekleşen hata rapora yazılır.

Görünüm › İstatistik: üçgen sayısı, LOD dağılımı, en büyük sapma, kare ve GPU süresi.

### 6.12 Kesit kutusu, düzlem görünümü, görünürlük

- Kesit kutusu: 6 kırpma düzlemi ve tutamaçlar.
- Plan ve cephe görünümü ortografiktir, döndürme kapalıdır. Etkin düzlemin ± yarım kat derinliğindekiler normal, dışındakiler hayalet çizilir. PgUp ve PgDn komşu düzleme geçer.
- Görünürlük tür ve görünüm süzgeci bazlıdır: gizle, yalıt, hepsini göster.

### 6.13 Başarım bütçeleri

| Ölçüt | Hedef | Bugünkü ölçüm |
|---|---|---|
| Gezinme, 1080p, 20 bin üye, katı görünüm, tümleşik GPU | ≥ 60 kare/s | — (gerçek GPU'da kullanıcı denetimi) |
| Gezinmede CPU geometri üretimi | 0 | Mimari gereği |
| Üzerine gelme ve yakalama, 100 bin eleman | ≤ 1 ms | — |
| Çekirdek işlemi, 5 bin / 20 bin çubuk | ≤ 100 / ≤ 300 ms | — |
| Süzgeç değerlendirmesi, 100 bin eleman | ≤ 10 ms | — |
| Açılış ekranının görünmesi | ≤ 0,3 s; en az 1,2 s görünür | Ekran ≈ 1,23 s'de kapanıyor |
| Motor hazır | ≤ 1 s | 0,35–0,55 s |
| Etkileşimli boş çalışma alanı | ≤ 1,5 s | — |

### 6.14 Sınama kipleri ve ekran görüntüsü

Ayrı bir `op4sinama.exe` yazılmaz; denemede kanıtlanan `op4.exe` test kipleri genişletilir:
- `--test-ekran a.png [--boyut] [--arayuzsuz]`
- `--test-acilis a.png [--olcek]`
- `--test-pencere N`
- `--test-motor`
- Faz 1'de eklenenler: `--senaryo s.json` (komut dizgileri, sentetik olaylar, bekle ve çek adımları; deterministik saat) ve `--oz-sinama`.

Ortak bayraklar: `--warp`, `--motorsuz`, `--gunluk`, `--grafik-denetim`.

Çıkış kodları: 0 başarılı, 1 kullanım, 2 test hatası, 3 zaman aşımı, 5 çökme. Bir bekçi iş parçacığı süre sınırı uygular.

---

## 7. Gezinme (istek 8)

### 7.1 Eşleme ("op4 varsayılanı")

| Girdi | İş |
|---|---|
| Sol sürükle (eşik 4 px, DPI ölçekli) | Kaydır: boşta, seçimde ve komut sırasında |
| **Shift + sol sürükle** | Döndür: yörünge, merkez imlecin altındaki nokta. Plan ve cephede kaydırır. |
| Orta sürükle / Shift + orta sürükle | Kaydır / döndür |
| Tekerlek | İmlecin altındaki noktaya yakınlaştır; çentik başına 1,2×, kesirli tekerlek desteklenir |
| Orta çift tık, `Shift+F` | Sığdır |
| Sol tık (sürüklemesiz) | Seç; komutta nokta ver; tutamaçta bas-sürükle düzenler |
| Ctrl + sol tık / Shift + sol tık | Seçime ekle ya da çıkar / seçimden çıkar |
| Ctrl + sol sürükle | Pencere seçimi seçime ekler: soldan sağa tamamen içindekiler, sağdan sola değenler |
| Ctrl + Shift + sol sürükle | Pencereyle seçimden çıkar |
| Sağ tık | Bağlam menüsü |
| Görünüm küpü, `Alt+1…4`, `PgUp`/`PgDn` | Standart görünümler; düzlem ya da kat değiştir |
| Dokunmatik | İki parmak kaydırır ve kıstırır |

Ayarlar › Fare'de iki hazır eşleme vardır: "op4 varsayılanı" ve "klasik CAD" (orta kaydırır, Shift+orta döndürür, sol sürükle pencere seçer). Yörünge kipi turntable (varsayılan) ya da trackball olabilir; duyarlılık ayarlanır.

### 7.2 Mutlak çapa (denemede ölçüldü)

**Basış anında saklananlar:** kamera C₀ (`double`), imleç pikseli m₀ ve imlecin altındaki dünya noktası P. P önce BVH ışın vuruşundan, yoksa çalışma düzlemi kesişiminden, o da yoksa yörünge merkezi derinliğinden bulunur.

**Kaydırma:** m'nin C₀'a göre ışını, P'den geçen ve C₀ görüntü düzlemine paralel düzlemle kesiştirilir; kesişim Q'dur. C = C₀ ⊕ öteleme(P − Q). Hesap her olayda C₀'dan yeniden yapılır.

**Döndürme:** yaw = −k·Δx (dünya Z ekseni etrafında), pitch = −k·Δy (C₀'ın sağ ekseni etrafında). k = 0,3°/px; pitch ∈ (−89,9°, 89,9°); merkez P'dir.

**Yakınlaştırma:** f = 1,2ⁿ.
- Perspektifte: konum = P + (C.konum − P)/f.
- Ortografikte: ölçek /= f, ardından P sabit kalacak şekilde öteleme.
- Sınırlar: P'ye en yakın uzaklık 0,05 m; ortografik ölçek alt ve üst sınırı.

Girdi kaynağı Win32 `WM_MOUSEMOVE` (ya da `WM_POINTER`) olaylarıdır; ImGui'nin tamsayıya yuvarlanmış konumu kullanılmaz. Kamera matematiği `kaynak/cekirdek/kamera.*` içindedir: platformdan bağımsız, `double`, Linux'ta test edilir. Denemedeki `kamera.h` buraya taşınır.

### 7.3 Görünümler

- Her görünümün kendi kamerası vardır: 3B, Plan (Z aksı), Cephe (X ya da Y aksı), Kesit (serbest düzlem).
- "Seçime yakınlaş" komutu vardır.
- Görünüm kameraları `.op4` içinde saklanır.

### 7.4 Değişmezler

| Kod | Değişmez | Yer |
|---|---|---|
| K1 | 300 adımlık rastgele kaydırma yolunda P'nin izdüşümü imleçten ≤ 0,5 px uzaktadır; son konum ara yoldan bağımsızdır | Linux; Windows `--test-pencere` (ölçülen 0,0001 px) |
| K2 | Gezinme boyunca geometri üretimi 0 ve örnek tamponu yazımı 0 bayttır | WARP |
| K3 | Yakınlaştırmada imlecin altındaki nokta ≤ 0,5 px sabit kalır | Linux; Windows |
| K4 | Döndürme merkezi ekranda ≤ 0,5 px sabit kalır | Linux |
| K5 | 1×–1000× yakınlıkta çizgi kalınlığı ayarlanan değerin ±0,5 px içindedir | WARP görüntü ölçümü |

---

## 8. Hesap motoru tümleşimi

### 8.1 Süreç modeli

**`op4motor.exe`** küçük bir C++ barındırıcıdır (≈ 150 satır; denemedeki `motor.cpp` yükleyicisinden türetilir). Sırasıyla şunları yapar:
1. Geçersiz std tutamaçlarını boşaltır (tuzak 4).
2. `python3XX.dll`, `python3XX.zip`, `._pth` ve `motor\op4_sunucu.py`'nin varlığını denetler. Eksik dosya okunur bir hata iletisi ve çıkış kodu verir; `Py_FatalError` ile karşılaşılmaz.
3. `OPENBLAS_NUM_THREADS` değerini ana motorda çekirdek−1, yardımcıda 1 yapar.
4. `LoadLibraryExW` ile DLL'i yükler ve `Py_Main(["op4motor", "-X", "utf8", "-B", "-m", "op4_sunucu", "--istek", <tutamaç>, "--yanit", <tutamaç>, "--rol", "ana|yardimci"])` çağırır.

`Py_Main` kararlı ABI'dedir ve yapı düzenine bağlı değildir. Python olağan yoldan başlar: sinyal işleyicileri kurulur ve UTF-8 kipi açılır. Yalıtımı `._pth` sağlar: ortam değişkenleri ve kayıt defteri yok sayılır, site yüklenmez (D3).

**`op4/motor/op4_sunucu.py`** sunucu döngüsüdür:
1. `sys.stdout` ve `sys.stderr` günlük dosyasına yönlendirilir; fd 1 ve 2 de yönlendirilir (D4).
2. `signal.signal(SIGINT, signal.default_int_handler)` çağrılır.
3. `web_kopru` içe aktarılır ve `hazir` iletisi gönderilir.
4. Ana iş parçacığı istekleri sırayla `calistir()` ile işler.
5. Bir okuyucu iş parçacığı istek borusunu dinler. `iptal` gelince `_thread.interrupt_main()` çağırır; `kapat` gelince düzgün çıkış yapar.

**Protokol testleri:** `pytest op4/testler/python/test_sunucu.py` sunucuyu Linux'ta `python3 -m op4_sunucu` olarak başlatır. İstek, yanıt, iptal, büyük yanıt ve çökme senaryoları bu yolla sınanır. C++ istemcisi (Win32 ve POSIX) aynı sunucuyla ctest'te sınanır.

**Neden ayrı süreç:**
- numpy, ifcopenshell ve OCCT'deki yerel çökmeler arayüzü düşürmez.
- LAPACK çağrısı sürerken bile son çare olarak süreç sonlandırılabilir.
- GIL arayüzü etkilemez; bellek yalıtılır.
- Yeniden başlatma ucuzdur (≈ 0,5 s).

Denemedeki süreç içi gömme yalnız Faz 1'e kadar `--test-motor` tanı kipi olarak kalır, sonra kaldırılır.

### 8.2 Protokol

Çerçeve: 4 bayt küçük-endian uzunluk ve ardından UTF-8 JSON (en çok 512 MB). Aktarım miras alınan iki anonim borudur.

```
UI → motor:  {"tur":"istek","id":17,"istek":{"islem":"bina_coz","girdi":{...},"ayarlar":{...}}}
             {"tur":"iptal","id":17}     {"tur":"kapat"}
motor → UI:  {"tur":"hazir","surum":{"motor","python","numpy","sympy"},"sure_ms":…}
             {"tur":"durum","metin":"…","oran":45}
             {"tur":"ilerleme","id":17,"metin":"Kombinasyonlar","oran":60}      (Faz 5)
             {"tur":"yanit","id":17,"sure_ms":2891,"yanit":<calistir() metni olduğu gibi>}
             {"tur":"gunluk","duzey":"uyari","metin":"…"}
```

`istek` gövdesi web isteğiyle birebir aynıdır. `yanit` alanına `calistir` çıktısı metin olarak eklenir; ara katmanda yeniden ayrıştırılmaz.

### 8.3 Yönlendirme

| Örnek | Başlama | İşlemler |
|---|---|---|
| ana | Açılış ekranında | `bina_coz`, `bina_kombinasyon`, `bina_eleman_tasarim`, `bina_kesit_oner`, `bina_eleman_bilgi`, `bina_rapor`, `bina_tablolar`, `bina_alan`, `bina_yuk_yolu`, `bina_kimlik`, `bina_ag_eniyile` |
| yardımcı | İlk istekte (tembel) | Matris işlemleri, `ders_calistir`, `yardim`, `se_coz`, `se_ornekler`, `se_ornek`, `bina_kutuphane`, `bina_sablonlar`, `bina_sablon`, `bina_deprem`, `ifc_iceri` |

### 8.4 İptal, ilerleme, yeniden başlatma, sınırlar

- **İptal:** okuyucu iş parçacığı `_thread.interrupt_main()` çağırır. KeyboardInterrupt bir sonraki bayt kodu sınırında yükselir; süren uzun LAPACK çağrısı bitince devreye girer. Yanıt `{"hata":"İşlem iptal edildi.","hata_turu":"iptal"}` olur.
- **Yeniden başlatma:** iptalden sonra 5 s içinde yanıt gelmezse UI süreci `TerminateProcess` ile sonlandırır ve yeniden başlatır (≈ 0,5 s). Önbellek boşalır; ayrıntı işlemleri `bina` gönderilerek çağrılır (köprü bunu destekliyor).
- **Zaman aşımı yoktur;** geçen süre ve ilerleme görünür.
- **Bellek tavanı:** Job Object ile konur (varsayılan sistem belleğinin %60'ı). Aşılırsa öğretici hata verilir.
- **İleti tutarlılığı:** iptal ile yanıt yarışabilir; `id` eşlemesiyle eski yanıtlar atılır.

### 8.5 Paketleme

| Klasör | İçerik |
|---|---|
| `python\` | CPython **3.14.x** embeddable: dll, zip, `*.pyd`, `vcruntime140*.dll`, `._pth`. `Lib\site-packages\` altında numpy 2.5.3 cp314 (yerel uzantıları olduğu için düz klasör). |
| `python\saf.zip` | sympy 1.14.0 ve mpmath, UNCHECKED_HASH `.pyc` ile. Dosya sayısı ve açılış süresi ölçülür; kötüleşirse düz klasöre dönülür (D28). |
| `motor\` | Kökteki motor modülleri, `docs/web_kopru.py`, `op4_sunucu.py`; Faz 6–7'de `ifc_iceri.py`, `ag_eniyile.py`. `.pyc` önceden derlenir. |
| `bilesen\ifc\` (isteğe bağlı) | ifcopenshell 0.9.0, shapely, lark, isodate, python-dateutil, pyparsing, typing-extensions (Faz 6) |
| `bilesen\seyrek\` (isteğe bağlı) | scipy 1.18.1 (Faz 5, kullanıcı kararı) |

- `araclar/python_hazirla.py` (denemede var) şunları yapar: embeddable zip, `pip download --only-binary=:all: --platform win_amd64 --python-version 3.14 --require-hashes` (`op4/kurulum/motor_gereksinimleri.txt`), budama ve `.pyc`.
- Ölçülen kurulu boyut ≈ 102 MB, kurulum dosyası 27,3 MB. IFC bileşeniyle ≈ +120 MB kurulu ve ≈ +45 MB kurulum dosyası beklenir.
- Kurulum yolu sınaması: `C:\op4 dene ŞĞİı` (D29).

### 8.6 Motorda yalnız eklemeli değişiklikler

Varsayılanlar bugünkü davranışı korur; mevcut testler değişmeden geçer.

1. `bina_coz` girdisine `anlat` (varsayılan true) eklenir. `_bina_coz_yaniti` bugün `yapi.bina_coz(bina, goster="yok")` çağırıyor; false ise `anlat=False` iletilir ve `bloklar: []` döner.
2. `bina_kimlik`: `{bina}` alır, `{cozum_kimligi}` döndürür (`yapi.cozum_kimligi`, satır 4358).
3. KeyboardInterrupt yakalanınca `hata_turu: "iptal"` döner.
4. `ayarlar.sd_siniri` (isteğe bağlı): `yapi.EN_FAZLA_SD` 1500, `yapi_serbest.EN_FAZLA_SD` 2000 ve `temel.EN_KUCUK_AG` 0,10 istek başına yükseltilir. op4 varsayılanı 6000 SD'dir ve ayarlanır. "Tarayıcı sınırı" iletileri bu durumda "bellek ve süre sınırı" diye okunur.
5. İlerleme kancası (Faz 5): `mo.ayarlar.ilerleme` (varsayılan None).
6. Yeni işlemler: `bina_kimlik` (Faz 1), `ifc_iceri` (Faz 6), `bina_ag_eniyile` (Faz 7).
7. Ürün adı parametreleri: `bina_rapor` ve IFC için `secenek.uygulama`. Varsayılan "Matris Öğren" kalır.
8. **Başarım (Faz 5):** profil güdümlü hızlandırma. Hedefler `_durum_sonuclari`, `_diyagram_hazirla`, `ozet` ve `tasarim._json` dönüşümleridir. Koşul: bütün şablonlarda altın sonuçlarla bağıl ≤ 1e-12 fark ve aynı uyarı listeleri (bit eşitliği aranmaz; D8). Hedef: `celik-sanayi-4hol` anlatımsız çözümünde ≥ 2× hız.
9. **Seyrek yol (Faz 5; kullanıcı kararı):** `ayarlar.cozucu = "otomatik" | "yogun" | "seyrek"`. Otomatik kip SD > 3000 iken RCM sıralaması ve bantlı Cholesky (`scipy.linalg.cholesky_banded`) ya da `scipy.sparse.linalg.splu` kullanır. `np.linalg.inv(Kff)` gerektiren yoğuşturma yolları faktörle çözüme çevrilir. Yoğun yolla bütün şablonlarda bağıl ≤ 1e-9 eşdeğerlik aranır. scipy yoksa öğretici hata verilir.
10. **Genel modelde radye ve mütemadi temel (Faz 7a):** `temel.ag_kur` ızgarası, şerit rijitlikleri ve Winkler yayları `yapi_serbest`'e bağlanır; `TEMEL_TIP_HATASI` kalkar. Aks–kat çözümüyle eşdeğerlik test edilir.

---

## 9. Model çekirdeği (QuickJS-ng)

### 9.1 Karar

| Seçenek | Emek | Doğruluk riski | Başarım | Test |
|---|---|---|---|---|
| **QuickJS-ng gömülü (seçilen)** | Düşük (cephe ≈ 1,5 bin satır) | Çok düşük: aynı kod | Komut başına 5–100 ms (5 bin çubuk) | Mevcut node testleri ve eşdeğerlik derlemi |
| C++'a taşıma | ≈ 10 bin satır | Yüksek: REF, bölme, kesişim, üreteç ve aks silme kuralları ince | En iyi | Hepsi yeniden yazılmalı |
| Python'a taşıma (motor içinde) | Orta-yüksek | Orta | Etkileşimli komut motor kuyruğunda bekler; çözüm sürerken düzenleme yapılamaz | Yeni testler |

Sıcak noktalar ölçümle C++'a taşınabilir; cephe API'si aynı kalır. quickjs-ng (MIT) MSVC ile derlenir; sürüm iki haftadan eski son kararlı sürüme sabitlenir.

### 9.2 Modüller ve ön yükleme

**Modüller:** `docs/aks_sistemi.js`, `model_ops.js`, `bina_cizim.js`, `ifc_disari.js`, `tablo_editoru.js` (`_ic`), `op4/js/op4_ops.js`, `op4/js/op4_cekirdek.js`.

**Ön yükleme:**
- `globalThis.self = globalThis` tanımlanır; UMD sarmalayıcıları birbirini `self` üstünden bulur (`model_ops.js:56`).
- `window` ve `document` tanımsız bırakılır.
- `structuredClone` yoksa C ile yazılmış bir sürümü sağlanır. `model_ops.js` `kopya` bunu kendiliğinden kullanır; yoksa JSON yoluna düşer.
- `console` op4 günlüğüne yönlendirilir; sınamada `Date.now` deterministik saate bağlanır.

**Gömme:** JS kaynakları exe'ye kaynak dosyası olarak gömülür; hata yığınlarında satır numarası kalır. Açılışta derleme süresi ölçülür (beklenen ≈ 50 ms). Gerekirse `qjsc` bayt koduna geçilir.

**`docs/` içindeki tek ek:** `ifc_disari.js` dönüş nesnesine `kesitCoz` eklenir. Web davranışı değişmez.

### 9.3 Cephe API'si (`op4/js/op4_cekirdek.js`)

```
yeniBos(secenek)            → {ozet}
yukle(binaMetni, kaynak)    → {ozet, uyarilar, surum}
uygula(islem, parametreler) → {basarili, uyarilar, eklenen, silinen, degisen, sahne_surumu, gecis_onayi?}
geriAl() / yinele()         → aynı rapor
sahne()                     → SAHNE (tipli diziler + küçük JSON)
oznitelikler()              → sütunlu ÖZNİTELİK TABLOSU
sonucEsle(veriOzeti)        → çubuk/panel ↔ tasarım satırı, FE eleman listesi, aks–kat no
denetle()                   → ModelOps.denetle
metin()                     → kanonik bina JSON metni
ifcDisari(secenek)          → IFC4 STEP metni
tabloUygula(degisiklikler)  → MatrisTablo._ic.degisiklikleriUygula
```

- `islem` adları beyaz listedir.
- Genel modele geçiş C1 sözleşmesiyle yapılır (`genelGecisGerekli`, `genelGecisMetni`): çekirdek `gecis_onayi` döndürür, UI TaskDialog ile sorar, onay gelirse işlem `{onay: true}` ile yeniden çağrılır.
- Mütemadi ya da radye temelli modelde, Faz 7a'ya kadar, onay metni temelin tekile döneceğini açıkça yazar.

**SAHNE içeriği:**
- `seviyeler`
- `akslar`: 3B doğru parçaları, ad, balon yeri, sistem
- `dugumler`: Float64 konum, Int32 no, Uint8 tür
- `cubuklar`: no, i ve j, tür, kesit dizini, aci, 12 bitlik serbestlik maskesi, bayraklar, y′, grup, üreteç
- `paneller`
- `mesnetler`, `temeller`
- `yukler`
- `kesitler` (`kesitCoz` sonuçları), `malzemeler`
- `sahne_surumu`

Tipli diziler ArrayBuffer olarak sıfır kopyayla geçer.

### 9.4 İş parçacığı ve geri al

- Tek çekirdek iş parçacığı vardır. UI isteği kuyruğa koyar; 16 ms içinde biten işlem aynı karede görünür.
- Geri al, değişmez anlık görüntülerle yapılır. Sınır 100 adım ya da 512 MB'dır. Geri al yığını dosyaya kaydedilmez.
- Seçim kümeleri ve görünüm durumu geri al kapsamına girmez.

### 9.5 Eşdeğerlik ve başarım

- **Eşdeğerlik derlemi:** `op4/testler/js/derlem_uret.js`, mevcut node test girdileri ve 9 şablondan (işlem, girdi, çıktı) üçlüleri üretir. QuickJS çıktıları bunlarla karşılaştırılır: sayılarda bağıl 1e-12, diğer alanlar birebir. Linux ve Windows'ta koşar. `docs/` modülleri başka oturumlarda değiştikçe derlem yeniden üretilir (D35).
- **Başarım:** `celik-sanayi-4hol` ve sentetik 5 bin / 20 bin çubuklu modellerde ölçülür; hedefler ≤ 100 ms ve ≤ 300 ms.

### 9.6 Yeni saf işlemler (`op4/js/op4_ops.js`, node testli)

| Faz | İşlemler |
|---|---|
| 1 | `bosModel`, `katUyeligi`, `kullanimYeri`, `profilAdiNormal`, `oznitelikCikar` (temel alanlar), `sahneCikar`, `sonucEsle` |
| 3 | `oznitelikCikar` tam şema, `etiketAta` |
| 4 | `otele`, `buda`, `uzat`, `gerdir`, `ucBagla`, `kutupsalDizi`, `katlaraKopyala`, `olcekle`, `refOncelikli` |

---

## 10. Modelleme kuralları (TASARIM §19.4)

### 10.1 REF öncelik sırası ve serbest düğüm

Bir komutun ürettiği her yeni nokta, sırayla ilk uyan en parametrik başvuruyla yazılır:
1. Var olan düğüm.
2. Aks kesişimi `{aks, z}` ya da `{sistem, aks, z}`.
3. Bir çubuk üstündeki bölme düğümü `{tur: "bolme", cubuk_i, cubuk_j, oran}`.
4. Kesişim `{tur: "kesisim"}`.
5. Hiçbiri uymazsa serbest düğüm `{no, X, Y, Z}`.

Kurallar:
- Aks taşınınca 1–4 ile yazılan noktalar birlikte taşınır; 5 yerinde kalır.
- Serbest düğüm rozetle gösterilir. AKSABAĞLA komutu (`aksaBagla`, `serbestleriBagla`) onları sonradan aksa bağlar. Denetim serbest düğüm sayısını raporlar.
- "Yalnız aks noktaları (katı §19 kipi)" ayarı açıkken 5 reddedilir. op4 varsayılanı kapalıdır; kullanıcı onayı gerekir.
- Kat 0 temel kuralı serbest düğümlere uygulanmaz. Çözümden önce "mesnetsiz" denetimi bir hızlı düzeltme önerir.

### 10.2 Kat ve seviye üyeliği (`katUyeligi`; Faz 1)

- Seviyeler `akslar.z`'dir; `kat` işaretli olanlar kat seviyesidir. Tolerans 1 mm'dir.
- **Düğüm:** kotu bir Z aksına 1 mm'den yakınsa o seviyededir.
- **Kolon** (düşeyle açısı ≤ 10°): üst ucu z_{k−1} < z_üst ≤ z_k + 1 mm aralığındaysa kat k'dır. Kat aralığını aşan kolon kat listesi taşır.
- **Yatay çubuk ve panel:** z_{k−1} + 1 mm < z ≤ z_k + 1 mm aralığındaysa kat k'dır. En üst katın üstündekiler en üst kata atanır; kat 0 ve altındakiler "temel" sayılır.
- "Seviye" özniteliği en yakın Z aksının adını taşır.
- **Eğik ve çapraz çubuk:** üst ucunun kotuna göre atanır.

### 10.3 Kullanım yeri (`kullanimYeri`; Faz 1)

**Alt tür:** kolon, kiriş, döşeme, çatı, cephe, çapraz, makas-üst, makas-alt, makas-dikme, makas-diyagonal, aşık, kren, bağ, temel, mesnet, düğüm, yük.

**Konum sınıfı:**

| Eleman | Sınıflar |
|---|---|
| Kolon | köşe, kenar, iç |
| Kiriş | dış, iç, konsol |
| Döşeme | iç, kenar, konsol |
| Çapraz | dış cephe, iç |
| Düğüm | temel, kolon üstü, ara |
| Cephe | ±X, ±Y yüzü |

**Algoritma:**
1. Her katın plan zarfı, o kattaki döşeme panellerinin birleşimidir; döşeme yoksa kolonların dışbükey zarfıdır.
2. Zarf köşesindeki kolon (iç açı < 170°) köşe, zarf kenarındaki kenar kolonudur; kalanlar iç kolondur.
3. Zarf kenarı üstündeki kiriş dış kiriştir.
4. Bir ucu başka hiçbir taşıyıcıya bağlı olmayan kiriş konsoldur.

Tolerans 1 cm'dir.

### 10.4 Kesit adı eşleme (`profilAdiNormal`)

| Yazılan | Normal ad |
|---|---|
| "HE340A", "HE 340 A", "HEA340", "HE-A 340" | "HEA 340" |
| "HE300B" | "HEB 300" |
| "IPE300" | "IPE 300" |
| "RHS", "SHS" | KUTU |
| "CHS" | BORU |
| "U200", "UPN200" | "UPN 200" |
| "L100x10", "L 100.100.10" | "L 100x10" |

HEM serisi kütüphanede yoktur; yazılırsa "kütüphanede yok" denir.

JS, C++ ve Python (IFC) üç uygulamadır. Hepsi `op4/testler/ortak/profil_adlari.json` sınama vektörlerini paylaşır.

### 10.5 Aks–kat (surum 1) modelleri

- Şablonlar olduğu gibi açılır, görüntülenir ve çözülür. Sahne `genellestir` görünümüyle üretilir; kimlikler `genelSecim` ile eşlenir.
- Modeli çeviren ilk düzenlemede bir kez onay istenir (C1). Mütemadi ya da radye temel, Faz 7a'ya kadar, genel modelde tekile döner ve bu açıkça uyarılır.

### 10.6 Etiketler ve kullanıcı öznitelikleri (yeni)

- Çubuk, panel ve düğümde `etiketler: ["…"]` ve `kullanici: {anahtar: değer}` alanları olabilir.
- IFC'den gelen elemanlar `ifc: {GlobalId, sinif, ad, pset: {"Pset_X.Ozellik": değer}}` alanını taşır.
- Motorun bilinmeyen alanları yok saydığı bir pytest ile kilitlenir.
- IFC dışa aktarımda etiketler ve kullanıcı alanları eklemeli bir seçenekle `Pset_op4` kümesine yazılır.

---

## 11. Seçim, Seç ve Süz, atama kapsamları (Faz 3; istek 2 ve 3)

### 11.1 Seçim yöntemleri

| Yöntem | Ayrıntı |
|---|---|
| Fare | §7.1'deki tık ve pencere eşlemeleri |
| SEÇ komutu | [Pencere] [Kesişen] [Çit] [Çokgen] [Tümü] [Önceki] [Ters] [Süzgeç…] |
| Seçilebilirlik süzgeci | Durum çubuğundaki tür çipleri |
| Model gezgini | Kat, tür ya da kullanım yeri düğümü o kümeyi seçer |
| BENZERİNİSEÇ | Varsayılan ölçüt aynı alt tür ve kesit; ölçütler ayarlanır |
| Seçim döngüsü | Üst üste elemanlarda aynı noktaya tekrar tık |

### 11.2 Öznitelik şeması (`op4/veri/oznitelikler.json`)

Her kayıt:

```
{id, ad, tur: sayi | metin | enum | bool | liste | sozluk, birim?,
 kaynak: model | turetilmis | sonuc | ifc | kullanici,
 uygulandigi: [...], esanlamlilar: [...], duzenlenir?, yazici?, indis?: durum | kombinasyon | anahtar}
```

Süzgeç arayüzü, sorgu dili, özellik ızgarası ve tablo sütunları bu şemadan üretilir.

| Grup | Öznitelikler |
|---|---|
| Kimlik | tür, no, ad, grup, üreteç (no, tip), kaynak (aks–kat no), **etiketler**, IFC GlobalId, IFC sınıfı, IFC adı |
| Kullanım | alt tür, kullanım yeri, sistem (çelik / betonarme) |
| Konum | kat (liste), seviye, üstünde bulunduğu X/Y aksları, aks sistemi, X/Y/Z en küçük ve en büyük, serbest düğüme bağlı mı |
| Geometri | uzunluk, doğrultu, eğim açısı, aci, panel alanı, kalınlık, köşe sayısı |
| Kesit ve malzeme | kesit adı, profil (normal), aile, h, b, A, I_güçlü, I_zayıf, kg/m, malzeme, sınıf, donatı |
| Bağlantı | i ve j uç serbestlikleri, mafsal durumu, yalnız çekme, K, Lb |
| Yükler | ek yük var mı (G/Q/S), yük türü, değer aralığı, duvar, panel kullanım sınıfı, g_ek, dağıtım, kar, rüzgâr c_p |
| Mesnet ve temel | mesnet tipi, serbestlik maskesi, temel tipi, B×L×h |
| Sonuç | D/C; **D/C[kombinasyon]**; durum; belirleyen kontrol ve kombinasyon; **\|N\|[durum]**, \|V\|maks, \|M\|maks; en büyük yer değiştirme; tepki; yalnız çekme devre dışı; sonuç eski mi |
| Metraj | ağırlık, hacim, alan |
| IFC (Faz 6) | `pset[...]` değerleri, kaynak dosya |
| Kullanıcı | `kullanici[anahtar]` |
| Görünüm | görünür, yalıtık, seçim kümesi üyeliği |

### 11.3 Sorgu dili (TASARIM §23)

Dilbilgisi:

```
ifade  := terim (("veya"|"or"|"|") terim)*
terim  := etken (("ve"|"and"|"&") etken)*
etken  := ("değil"|"not"|"!") etken | "(" ifade ")" | kosul
kosul  := alan isleç deger | alan "arasında" deger "ile" deger
        | alan "içinde" "[" deger ("," deger)* "]" | alan ("var"|"yok")
alan   := ad [ "[" metin "]" ]                    ← indisli öznitelik
isleç  := "=" | "!=" | "<" | "<=" | ">" | ">=" | "~" | "içerir"
deger  := sayı [birim] | "metin" | yalın-sözcük | enum
```

Kurallar:
- Alan adları şemadaki `id`, `ad` ya da `esanlamlilar` olabilir. Eşleme Türkçe harf katlamalı ve büyük/küçük harf duyarsızdır.
- `profil` ve `kesit` değerleri §10.4'e göre normalleştirilir.

Örnekler:

```
profil = HE340A
tur = kiris
tur = kolon ve kat içinde [2,3] ve kullanim_yeri = kose
kesit ~ "IPE*" ve uzunluk arasında 5 ile 7
dc > 0.9 ve sistem = celik
dc["1.4G+1.6Q"] > 0.8
aks = B ve dogrultu = dusey
serbest_j içerir My
etiketler içerir "imalat-1"
pset["Pset_BeamCommon.IsExternal"] = evet
```

- Ayrıştırıcı ve değerlendirici C++ çekirdektedir ve sütunlu tablo üzerinde çalışır.
- Hatalı sorgu öğretici iletiyle konumu gösterir: "3. sözcük: 'kesitt' alanı yok; 'kesit' mi demek istediniz?".

### 11.4 "Seç ve Süz" penceresi

- **Kural oluşturucu:** Alan / İşleç / Değer satırları ile VE ve VEYA grupları. Üstteki sorgu metniyle iki yönlü eşitlenir.
- **Canlı geri bildirim:** eşleşme sayısı anında güncellenir, sahnede önizleme vurgusu görünür.
- **Değer listeleri:** enum alanlarında modeldeki mevcut değerler sayılarıyla listelenir, ör. "HEA 320 (70)".
- **Hedef:** Yeni seçim / Seçime ekle / Seçimden çıkar / Seçim içinde süz.
- **Kapsam:** Bütün model / Görünenler / Etkin kat / Seçim.
- **Kayıt:** "Süzgeç olarak kaydet" (dinamik) ve "Seçim kümesi olarak sakla" (sabit liste).
- **Hızlı süzgeç:** model gezgini başlığındaki kutu aynı dili kullanır.

### 11.5 Seçim kümeleri, süzgeçler, görünüm süzgeci

- **Seçim kümeleri** kimlik listeleridir; silinen elemanlar kümeden düşer.
- **Süzgeçler** sorgu metinleridir; her kullanımda yeniden değerlendirilir.
- **Görünüm süzgeci** görünüm başına gizler, yalıtır ya da renklendirir; ör. "dc > 1" kırmızı.
- Hepsi `.op4` içinde saklanır.

### 11.6 Yük atama (YÜKATA)

- **Tür:**
  - Çubuğa yayılı (q ya da q1, q2; x1, x2; yön global −Z, X/Y ya da yerel y/z).
  - Çubuğa tekil (P, x).
  - Panele alan yükü (p, kN/m², aşağı pozitif).
  - Düğüme kuvvet (FX … MZ).
  - Kirişe duvar (duvar kütüphanesinden).
- **Durum:** yalnız G, Q ya da S (`yapi_serbest.py:1385` kuralı). W, E ve K yükleri motorca üretilir.
- **Kip:** Ekle / Değiştir (aynı durumdaki önceki ek yük silinir) / Sil.
- **Hedef:** seçim, süzgeç ya da model gezgini düğümü. Örnekler: "2–5. kat döşemeleri Q = 2 kN/m²", "çatı aşıklarına S", "dış kirişlere 270 duvarı".
- **Önizleme:** eşleşen eleman sayısı, sahnede vurgu ve üretilecek kayıt sayısı. "Uygula" tek geri al adımıdır.
- **Model:** `ek_yukler` kayıtları `BC.yukEkle` ile yazılır. Aks–kat modelinde model çevrilmeden yazılır (C10).
- **Görünüm:** yükler durum başına ok ve değerle gösterilir; Yükler tablosu vardır.

### 11.7 Mesnet ve temel atama (MESNETATA, TEMEL)

- **Ön ayarlar:** `BC.MESNET_ON_AYAR` (ankastre, mafsal, kayıcı, kaldır, yay) ve 6 serbestlik onay kutusu.
- **Hedef:** seçim, "en alt seviyedeki bütün düğümler", "kolon alt uçları", "seçili katların düğümleri" ya da süzgeç.
- Kat 0 temel kuralıyla açık mesnetlerin ilişkisi uyarıyla anlatılır.
- **TEMEL:** tekil B×L×h. Mütemadi ve radye temel Faz 7a'dan sonra genel modelde de çözülür.

---

## 12. Çizim ve düzenleme (Faz 4; istek 1 ve 2)

### 12.1 Komut çerçevesi (TASARIM §22)

**Kayıt dosyası** `op4/veri/komutlar.json`. Faz 1'de alt küme, Faz 4'te tam katalog. Her kayıt:

```
{id, ad, takma_adlar[], kisayol?, ikon, serit: {sekme, grup, boyut},
 ipucu, yardim, kosul, secim (once | sonra | yok), tekrarlanir}
```

Şerit, menü, bağlam menüsü, komut satırı tamamlama ve Yardım › Kısayollar tablosu bu dosyadan üretilir. Kullanıcı takma adları ve kısayolları `%APPDATA%\Opus Fortis\op4\` altındaki `takma_adlar.json` ve `kisayollar.json` dosyalarındadır.

**Komut yapısı:** her komut C++ durum makinesidir.
- İstem türleri: nokta, mesafe, açı, seçim (her seçim isteminde [Süzgeç…] seçeneği), seçenek, metin.
- Seçenekler köşeli ayraçla gösterilir: [Kapat/Geri al/Tür].
- Önizleme yalnız üst katmandadır; işleme anında çekirdekte **tek işlem** çalışır ve tek geri al adımıdır.

**Akış kuralları:**
- Esc iptal eder. Enter ya da Boşluk bitirir; boşta son komutu yineler.
- Komut içinde Geri al son noktayı geri alır.
- Önce seçip sonra komut da, önce komut sonra seçim de desteklenir.
- Gezinme, yakalama açma-kapama ve görünüm değiştirme komut sırasında saydamdır.

**Komut satırı:** önek ve alt dizi tamamlama; Türkçe harf katlama (İ/i/ı/I, ş/s, ğ/g, ç/c, ö/o, ü/u); geçmiş; çıktı alanı.

### 12.2 Koordinat girişi

| Biçim | Örnek |
|---|---|
| Mutlak | `x,y[,z]` |
| Göreli | `@dx,dy[,dz]` |
| Kutupsal | `@L<açı` |
| Aks kesişimi | `B/3` ya da `B/3/Saçak` |
| Düğüm | `#100004` |
| Doğrudan uzaklık | imleç yönünde bir sayı |

Birim m'dir; `600cm` ve `6000mm` gibi sonekler kabul edilir. Tek değerli istemlerde ondalık virgül de kabul edilir. Ayrıştırıcı çekirdektedir ve Linux'ta test edilir.

### 12.3 Nesne yakalama, izleme, çalışma düzlemi

**Yakalama (F3) önceliği:**
1. Aks kesişimi
2. Düğüm
3. Uç
4. Orta
5. Kesişim
6. Dik
7. En yakın
8. Merkez
9. Uzantı
10. Paralel

**Yardımcılar:** ızgara yakalama (F9; adım 0,05 m = `YAKALAMA_ADIMI`), dik izleme (F8), kutupsal izleme (F10), nesne izleme.

**Davranış:**
- Tolerans 10 px'dir (DPI ölçekli); Sekme adaylar arasında dolaştırır.
- Her yakalama sonucu §10.1'deki REF adayını da taşır; örneğin orta nokta, oranı 0,5 olan bölme düğümü adayıdır.

**Çalışma düzlemi:** plan seviyesi, cephe ya da `ÇD` komutuyla 3 noktadan serbest düzlem.

### 12.4 Komut kataloğu

Çekirdek işlemleri ModelOps (MO), MatrisAks (MA), MatrisBinaCizim (BC) ve op4_ops (OP4) modüllerindendir. Bütün MO, MA ve BC adları depoda doğrulandı.

**Çizim**

| Komut | Takma ad | Çekirdek işlemi |
|---|---|---|
| ÇUBUK [Tür] [Kesit] [Mafsal] [Hedef katlar] | `L`, `ÇZ` | MO.cubukZinciri, BC.cubukTuru |
| ÇOKLUÇUBUK [Kapat] [Panel de oluştur] | `PL`, `ÇÇ` | MO.cubukZinciri, MO.panelOlustur |
| DÜĞÜM | `PO`, `DG` | MO.dugumEkle |
| KOLON [Tüm katlar] [Hedef katlar] | `K` | BC.kolonCiftleri, MO.cubukCiz |
| KİRİŞ [Hedef katlar] | `R` | MO.cubukCiz |
| ÇAPRAZ [X, /, \, V, ters V, K, dışmerkez, diz] | `X` | MO.caprazUret (K ve yalnız çekmede yönetmelik uyarısı) |
| PANEL / DÖŞEME [Tür] [Kalınlık] [Dağıtım] | `D`, `PN` | MO.panelOlustur |
| EĞİK | `E` | MO.cubukCiz |
| DUVAR (yük) | `W` | MO.ozellikAta |
| MAKAS, BEŞİK, AŞIK, KRENYOLU, CEPHEKİRİŞİ, ÜRETEÇDÜZENLE | `MK`, `BÇ`, `AŞ`, `KY`, `CK` | MO.makasUret, besikCerceveUret, asikUret, krenYoluUret, cepheKirisleriUret, uretecGuncelle |
| HIZLIAKS | `HA` (`Shift+G`) | MA.hizliAks, BC.aksSihirbazUygula |
| AKSEKLE, AKSSİL, AKSTAŞI, AKSOFSET, AKSSİSTEMİ, AKSTABLOSU | `AE`, `ASİ`, `AT`, `AO`, `AS`, `G` | MA.aksEkle, aksSil (BC.aksSilEngelleri), aksTasi, OP4.otele, MA.sistemEkle |

**Düzenleme**

| Komut | Takma ad | Çekirdek işlemi |
|---|---|---|
| SİL | `SL`, `Del` | MO.cubukSil, panelSil, dugumSil |
| KOPYALA [Çoklu] | `CO`, `KP`; `Ctrl+C` ve `Ctrl+V` (süreçler arası pano biçimi `OpusFortis.op4.Secim`) | MO.dogrusalDizi |
| TAŞI | `M` | MO.tasi |
| DÖNDÜR [Referans] [Kopya] | `RO` | MO.dondur |
| AYNA [Kaynağı sil] | `MI` | MO.ayna |
| **ÖLÇEKLE** [Kopya]: aks konumlarını ve serbest düğümleri baz noktaya göre ölçekler; kesitler değişmez; aks–kat modelinde onay ister | `SC`, `ÖL` | OP4.olcekle |
| ÖTELE [Aks oluştur] | `O` | OP4.otele |
| DİZİ (doğrusal / kutupsal) | `AR` | MO.dogrusalDizi, OP4.kutupsalDizi |
| BUDA / UZAT (yeni uç `{kesisim}` olur) | `TR` / `EX` | OP4.buda / OP4.uzat |
| BÖL (nokta, eşit, uzunluk, oran, akslarda, kesişimlerde, düzlemle) | `BR`, `B` | MO.bol, kesisimlerdeBol, duzlemleBol |
| BİRLEŞTİR, DÜĞÜMBİRLEŞTİR | `J`, `DB` | MO.birlestir, dugumleriBirlestir |
| GERDİR | `ST` | OP4.gerdir |
| ÖZELLİKEŞLE | `MA` | MO.ozellikAta, serbestlikAta |
| MAFSAL, YALNIZÇEKME, KESİT, AÇI, **ETİKET** | `MF`, `YÇ`, `KS`, `AÇ`, `ET` | MO.serbestlikAta, ozellikAta, OP4.etiketAta |
| AKSABAĞLA | `AB` | MO.aksaBagla, BC.serbestleriBagla |
| KATLARAKOPYALA | `KK` | OP4.katlaraKopyala |
| GERİAL, YİNELE | `Ctrl+Z`, `Ctrl+Y` | Çekirdek geriAl, yinele |

**Ölçme ve görünüm:** UZAKLIK, AÇI, ALAN, KOT, KOORDİNAT, BOY, ÖLÇÜTEMİZLE, ÇD, SIĞDIR, GİZLE, YALIT, TÜMÜNÜGÖSTER, KESİTKUTUSU, 3B, PLAN, ÖN, YAN.

**Analiz ve sistem:** ÇÖZ (F5), TASARIM (F6), RAPOR (`Ctrl+Shift+R`), TABLOLAR (`Ctrl+T`), IFCDIŞA (`Ctrl+E`), IFCİÇE, YENİ, AÇ, KAYDET, FARKLIKAYDET.

Mevcut web kısayollarının harfleri (L, K, R, X, D, E, W, M, B, J, U) takma ad olarak korunur.

### 12.5 Tutamaçlar

- Seçili çubukta uç ve orta tutamaç, panelde köşe tutamaçları, aks balonunda taşıma tutamacı görünür.
- **Uç tutamacı:** sürükleyince yakalamayla yeni hedef seçilir; sonuç `dugumTasi` ya da `ucBagla` olur.
- **Orta tutamaç:** TAŞI komutunu çalıştırır.
- **Aks balonu:** `aksTasi` ile 0,05 m adımla taşır.

### 12.6 Çok katlı çizim (istek 2)

- KOLON, KİRİŞ, ÇUBUK, PANEL ve ÇAPRAZ komutlarında "Hedef katlar" seçeneği vardır: etkin kat, tümü, aralık ("2-5") ya da liste ("1,3,5").
- Öğe etkin kat düzleminde önizlenir.
- İşlemede her hedef kat için REF'lerdeki z adı o katın Z aksıyla değiştirilir. Serbest düğümler kot farkı kadar ötelenir. Hepsi tek işlemde oluşur (`katlaraKopyala`).
- Her katta çakışan eleman denetimi uygulanır (`BC.mevcutCubuk`, `aksKatCakisan`).

### 12.7 Ölçme

- `olcum.js` kuralları C++'ta uygulanır: uzaklık, açı, alan, kot farkı, koordinat, eleman boyu.
- Esc yarım kalan ölçümü bırakır; tamamlanmış ölçüler kalır.
- Sonuç komut geçmişine yazılır.

---

## 13. Proje dosyası ve dosya işlemleri (Faz 1; istek 4 ve 6)

### 13.1 `.op4` biçimi (TASARIM §21)

```
proje.op4  (ZIP, deflate; "mimetype" ilk girdi ve sıkıştırmasız)
  mimetype             "application/x-op4"
  manifest.json        {tur:"op4-proje", bicim_surumu:1, uygulama:{ad:"op4", surum, firma:"Opus Fortis"},
                        kaydedildi, model_ozeti, motor_surumu, icerik:[...]}
  model/bina.json      bina JSON (surum 1 ya da 3), kanonik UTF-8 (çekirdek metin())
  gorunum/gorunum.json görünümler, kameralar, kipler, kesit kutusu, görünürlük, görünüm süzgeçleri
  secim/kumeler.json   seçim kümeleri ve kayıtlı süzgeçler
  sonuc/ozet.json      {cozum_kimligi, tarih, motor_surumu, ozet, dc_dizisi}
  sonuc/veri.json      (isteğe bağlı) bina_coz veri'si
  ifc/kaynak.json      IFC içe aktarma kaynağı ve eşleme tablosu
  onizleme.png         256×256
```

Açılışta ilk bayt `{` ise dosya denemenin JSON biçimidir (kamera ve görünüm ayarları; `model` alanı boş yer tutucu). Kameralar alınır, model boş açılır.

Açma sırası:
1. Manifest doğrulanır.
2. `bicim_surumu` yükseltme zinciri uygulanır.
3. Çekirdek `yukle` ve `denetle` çalışır.
4. `sonuc/` varsa `bina_kimlik` ile karşılaştırılır; kimlikler eşleşirse D/C renkleri hemen görünür.
5. Dosya daha yeni bir sürümle kaydedilmişse salt okunur açılır ve uyarı verilir.

### 13.2 Kaydet, Farklı kaydet, Aç

- **Kısayollar:** `Ctrl+S`, `Ctrl+Shift+S`, `Ctrl+O`.
- **Süzgeçler:** op4 projesi, `.matris`, bina `.json`, IFC.
- **Atomik yazma:**
  1. Aynı klasöre geçici dosya yazılır ve `FlushFileBuffers` çağrılır.
  2. Hedefte açık tanıtıcı varsa kapatılır.
  3. Hedef varsa `ReplaceFileW` (isteğe bağlı `.bak`), yoksa `MoveFileExW(REPLACE_EXISTING|WRITE_THROUGH)` kullanılır (denemedeki yol).
  4. Paylaşım ihlalinde 5 kez, 100 ms aralıkla yeniden denenir (OneDrive).
  5. Yerine konduktan sonra okuma kilidi yeniden açılır.
- **Kirli işareti:** başlıkta "•"; kapanışta Kaydet / Kaydetme / Vazgeç sorulur.
- **İkinci açılış:** aynı dosya başka bir op4 penceresinde açıksa o pencere öne getirilir (tek örnek borusu).

### 13.3 Otomatik kayıt ve kurtarma

- Kirli belge varsayılan 5 dakikada bir (1–30 dk) `%LOCALAPPDATA%\Opus Fortis\op4\kurtarma\<guid>.op4` dosyasına yazılır.
- Temiz kapanışta kurtarma dosyaları silinir.
- Açılışta artık kayıt bulunursa "Kurtar / Sil / Sonra" sorulur.
- Beklenmeyen hatada `MiniDumpWriteDump` ile `cokme\` altına döküm yazılır.

### 13.4 Yeni ve şablonlar (istek 4)

Program her zaman `yeniBos()` modeliyle açılır:

```
{tur:"bina", surum:3, baslik:"Adsız 1", sistem:"celik", birim:{kuvvet:"kN", uzunluk:"m"},
 akslar:{x:[], y:[], z:[{ad:"±0.00", konum:0, kat:0}]}, katlar:[{no:0, ad:"±0.00", kot:0}],
 malzemeler:{C30, B420C, S275, S355}, kesitler:{}, dugumler:[], cubuklar:[], paneller:[],
 mesnetler:[], ek_yukler:[], uretecler:[], yuk_durumlari:{G, Q}, deprem:{etkin:false}, temeller:{tip:"tekil"}}
```

Kütüphaneden ilk kez seçilen kesit `kesitler` içine kendiliğinden eklenir (ör. "HEA 340" → `{tip:"profil", profil:"HEA 340", malzeme:"S275"}`).

Dosya › Yeni seçenekleri:
- Boş model.
- Hızlı aks sihirbazıyla.
- Şablondan: 9 şablon. `bina_sablon` çıktıları derlemede `op4/veri/sablonlar/*.json` olarak paketlenir; böylece şablonlar motor hazır olmadan da açılır. Küçük resimler derlemede WARP ile üretilir.

### 13.5 Son dosyalar, eski biçimler, kabuk

- **Son dosyalar:** 10 dosya; atlama listesi (`SHAddToRecentDocs`); Başlangıç panelinde küçük resimle.
- **Eski biçimler:** `.matris` ve düz bina `.json` açılır; dışa aktarma da yapılabilir (web sürümüyle paylaşım için).
- **Kabuk:** `.op4` ilişkilendirmesi `OpusFortis.op4.Proje` (denemede var). Tek örnek borusu `\\.\pipe\OpusFortis.op4.<SID>` kullanılır; `--yeni-ornek` ile ayrı süreç açılır.

---

## 14. IFC (istek 7)

### 14.1 Dışa aktarma (Faz 1)

- `ifc_disari.js` QuickJS'te değişmeden çalışır; `secenek.uygulama = {ad:"op4", surum, firma:"Opus Fortis"}` verilir.
- Menü: Dosya › Dışa aktar › IFC (`Ctrl+E`).
- Mevcut seçenekler korunur: analiz modeli, yükler, D/C. GlobalId'ler belirlenimcidir. Başlık zaman damgası sınamada sabitlenir.

### 14.2 İçe aktarma hattı (Faz 6; `ifc_iceri.py`, yardımcı motor, ifcopenshell 0.9.0)

1. **Ön tarama:** şema (IFC2X3, IFC4, IFC4X3), birim ölçeği, sınıf sayıları, katlar, ızgaralar.
2. **Seviyeler:** `IfcBuildingStorey.Elevation` (yerleşim zinciriyle) `akslar.z` (kat işaretli) ve `katlar` olur. Kat dışı kotlar eleman uç kotlarının kümelenmesinden isteğe bağlı Z aksı olur.
3. **Izgaralar:** global eksenlere paralelse `akslar.x/y`; döndürülmüş ya da ötelenmişse `aks_sistemleri`; RADIAL ızgara silindirik sistem olur. Eğrisel aks atlanır ve uyarılır.
4. **Analitik model varsa öncelikli kullanılır** (`IfcStructuralAnalysisModel`):
   - `IfcStructuralCurveMember` ve topoloji kenarları çubuk olur.
   - `IfcStructuralPointConnection` düğüm, `IfcBoundaryNodeCondition` mesnet olur.
   - `IfcRelConnectsStructuralMember` uç serbestliklerine çevrilir.
   - Yük grupları `ek_yukler` olur: PERMANENT_G → G, VARIABLE_Q → Q, kar → S; kalanlar rapora yazılır.
   - Fiziksel elemanla bağ `IfcRelAssignsToProduct` üzerinden kurulur.
5. **Analitik model yoksa fiziksel elemandan eksen çıkarılır:** önce `Axis` temsili; yoksa `IfcExtrudedAreaSolid` (CardinalPoint ofseti ağırlık merkezine düzeltilir); son çare üçgen ağının PCA ekseni (uyarıyla). `aci` 0,01° hassasiyetle hesaplanır.
6. **Düğüm birleştirme:** 5 mm toleransla. İsteğe bağlı olarak `kesisimlerdeBol`, `aksaBagla` ve `serbestleriBagla` UI tarafından çekirdekte çağrılır.
7. **Kesit ve malzeme eşleme** §14.4'e göre yapılır. Eşlenemeyenler pencerede sorulur; seçimler hatırlanır.
8. **Uç serbestlikleri** (analitik model yoksa): varsayılan çaprazlar iki ucu mafsallı, kirişler sürekli.
9. **Çıktı:**
   - Bina JSON (surum 3); her elemanda `ifc` alanı, Pset değerleriyle (§10.6).
   - İçe aktarma raporu.
   - Referans ağı dosyası `gecici\ifc-<sha>.op4ag` (ikili; float32 konum, uint32 dizin, GlobalId).
10. **İlerleme ve iptal:** `ilerleme` iletisiyle; geometri `ifcopenshell.geom.iterator` ile çok iş parçacıklı üretilir.

**Ölçek önlemi:** model SD sınırını aşıyorsa pencere seçenek sunar: yalnız referans olarak aç, seçili katları al, ya da seyrek çözücüyle sürdür (Faz 5).

**Bileşen:** IFC içe aktarma kurulumda isteğe bağlı bir bileşendir. LGPL-3.0 (ifcopenshell), OCCT (LGPL-2.1 ve istisna) ve GEOS (LGPL-2.1) metinleri ile kaynak bağlantıları `lisanslar/` altındadır. Bileşenler ayrı `.pyd` ve `.dll` dosyaları olarak durur, böylece değiştirilebilirler. Bileşen yoksa menü kurulum yönlendirmesi gösterir.

### 14.3 Eşleme tablosu (IFC → op4)

| IFC | op4 | Not |
|---|---|---|
| IfcProject, IfcSite, IfcBuilding | `baslik`; rapor künyesi | Birimler m ve kN'a çevrilir |
| IfcBuildingStorey | `akslar.z` (kat işaretli) ve `katlar` | Adlar korunur |
| IfcGrid, IfcGridAxis | `akslar.x/y` ya da `aks_sistemleri` | AxisTag aksın adı olur |
| IfcColumn / IfcBeam | çubuk `kolon` / `kiris` | |
| IfcMember | BRACE ve STRUT → `capraz`; PURLIN → `asik`; CHORD → kota göre makas-üst ya da makas-alt; POST ve STUD → `kolon` ya da `makas-dikme`; diğerleri → `diger` | |
| IfcSlab FLOOR, LANDING / ROOF | panel `doseme` / `cati` | Kalınlık ekstrüzyon derinliğidir; delikler uyarılır |
| IfcSlab BASESLAB | Faz 7a'dan sonra radye; öncesinde uyarı | |
| IfcPlate, IfcCovering | kalınlığı 0 olan panel | İsteğe bağlı |
| IfcFooting PAD_FOOTING | `temeller.ozel` tekil temel ve kolon altı mesnet | |
| IfcFooting STRIP_FOOTING, FOOTING_BEAM | Faz 7a'dan sonra mütemadi; öncesinde uyarı | |
| IfcWall | İsteğe bağlı duvar yükü ve referans ağı | |
| IfcMaterial | `malzemeler` | "S355JR" → S355; "C30/37" → C30 |
| Diğer sınıflar | Referans katmanı | Analize girmez |

### 14.4 Profil eşleme

| IFC profili | op4 karşılığı |
|---|---|
| `IfcIShapeProfileDef` | Önce `ProfileName` §10.4'e göre normalleştirilip kütüphanede aranır; bulunamazsa ölçülerle %1 toleransla eşlenir |
| `IfcRectangleProfileDef` | Betonarme dikdörtgen b×h |
| `IfcRectangleHollowProfileDef` | KUTU |
| `IfcCircleHollowProfileDef` | BORU |
| `IfcCircleProfileDef` | Dolu daire |
| `IfcLShapeProfileDef` | Eşit kollu ise L; değilse eşleme penceresi |
| `IfcUShapeProfileDef` | Ad ya da ölçüyle UPN |
| `IfcCompositeProfileDef` (iki L) | 2L |
| `IfcCShapeProfileDef`, `IfcTShapeProfileDef`, `IfcArbitraryClosedProfileDef` | Desteklenmez. Çokgenden A ve I hesaplanır, en yakın kütüphane kesiti önerilir; **sessiz eşleme yapılmaz** |

### 14.5 Pencere ve birleştirme

- İçe aktarma penceresi: ön tarama özeti, seçenekler, eşleme tablosu, sonra çalıştır.
- Sonuç yeni pencerede açılır. "Mevcut modele ekle" seçeneği ofset ve aks birleştirmeyle çalışır.
- Rapor panelinde uyarıya tık ilgili elemanı seçer.

---

## 15. Belge penceresi (WebView2; Faz 5 ve 8)

### 15.1 Sınır ve gerekçe

**Yerel olanlar:** pencere ve bütün CAD/analiz arayüzü, sonuç görselleştirme, grafikler, Matris giriş ızgarası, Sonlu eleman tabloları ve çizimi.

**Belge penceresinde olanlar:**
- Ders gövdeleri: markdown, KaTeX ve renkli makrolar, etkileşimli SVG çizimleri (≈ 8,3 bin satır `etkilesim*.js`), çözümlü örnekler, alıştırmalar.
- Statik rapor önizleme, yazdırma ve PDF (rapor HTML ve satır içi SVG kullanıyor, `rapor.py`).
- Adım adım anlatım blokları.

**Gerekçe:** bu içerik yerelde yeniden yazılamayacak kadar büyük; WebView2 bir işletim sistemi bileşenidir. Tarayıcı açılmaz, sunucu, ağ ve Pyodide yoktur; içerik kurulumla gelir.

**Yerel matematik seçeneği (kullanıcı kararı):** Faz 5'te 3 günlük, süresi sınırlı bir deneme yapılır. Matris ve anlatım çıktısının yerelde çizilip çizilemeyeceği bakılır: TeX → SVG dönüşümü QuickJS'te ve SVG → doku dönüşümü yerel bir SVG çizicisiyle. Olursa Matris ve anlatım tamamen yerel olur, Belge penceresi yalnız dersler ve baskı için kalır. Dersleri yerelde yeniden yazmak +10–14 haftadır.

### 15.2 Uygulama

- Ana pencereye ait, ayrı üst düzey pencere. Yerel Win32 araç çubuğu: Geri, Yazdır, PDF, HTML kaydet.
- Ortam tembel başlatılır; kullanıcı veri klasörü `%LOCALAPPDATA%\Opus Fortis\op4\WebView2`.
- İçerik `SetVirtualHostNameToFolderMapping("belge.op4", <kurulum>\belge, DENY_CORS)` ile gelir.
- **Ağ engeli:** `AddWebResourceRequestedFilter("*")` ile `https://belge.op4/` dışındaki her istek reddedilir; sayaç testi 0'ı denetler. CSP vardır.
- **Kapatılanlar:** yeni pencere, indirme, varsayılan bağlam menüsü, sürüm derlemesinde geliştirici araçları.
- **Mesajlaşma:** `postMessage({tur:"motor", id, istek})`. op4 yalnız beyaz listedeki işlemleri yardımcı motora iletir (`ders_calistir`, matris işlemleri, `se_*`, `yardim`); kaynak `https://belge.op4` olmalıdır.
- **Rapor:** HTML `gecici\rapor-<kimlik>.html` dosyasına yazılır (2 MB'lık `NavigateToString` sınırı nedeniyle). Yazdırma `ICoreWebView2_16::Print`, PDF `ICoreWebView2_7::PrintToPdf` ile yapılır.
- **Çalışma zamanı:** Windows 11'de yerleşiktir; Windows 10'da genellikle kuruludur. Kurulum sihirbazı denetler; yoksa önyükleyiciyi çalıştırır. Bileşen yine de yoksa Belge penceresi açıklama ve kurulum düğmesi gösterir; CAD ve analiz etkilenmez.

### 15.3 Ortak web modülleri

- `docs/app.js` içinden `blok_gorunum.js` (md, KaTeX, kod, şema oynatıcı) ve `ders_gorunum.js` ayrılır; web sürümü de bunları kullanır.
- op4 kabuk sayfası `op4/belge/op4_belge.html` motor çağrılarını yerel köprüye yönlendirir.
- KaTeX ve marked SHA256 denetimiyle paketlenir.

---

## 16. Sonlu eleman, Matris ve Dersler (Faz 8)

- **Sonlu eleman:**
  - Düğüm, eleman, mesnet, yük, yay ve çökme tabloları yereldir.
  - Model türleri: yay, cubuk, kafes, kiris, cerceve, kafes3b, cerceve3b (`dersler/BICIM.md` §8.3).
  - Hazır örnekler `se_ornekler` ve `se_ornek` ile gelir; çözüm `se_coz` ile yardımcı motorda yapılır.
  - Çizim aynı DX12 işleyicisiyle yapılır; 2B'de ortografik, döndürme kapalı.
  - Şekil değiştirmiş biçim, N/V/M (uzayda ayrıca Vz, My, T), tepkiler ve denge yerel görünür.
- **Matris hesaplayıcı:**
  - İşlem tanımları tek kaynak `docs/hesap_islemleri.json` dosyasındadır (`app.js` `ISLEMLER` yerine); web de bunu kullanır.
  - Yerel giriş ızgarası: boyut değiştirme, "1 2; 3 4" metni, yapıştırma, sembolik değer.
  - Ayarlar ve zincirleme vardır.
  - Çıktı yerel matematik denemesine göre yerelde ya da Belge penceresinde gösterilir.
- **Dersler:** içindekiler yerel ağaçtır; gövde Belge penceresindedir; örnek kodlar `ders_calistir` ile çalışır. `dersler/` derlenmiş içeriği pakete girer.

---

## 17. Analiz ağı eniyilemesi ±%2 (Faz 7; TASARIM §26)

### 17.1 Önkoşul (Faz 7a): genel modelde radye ve mütemadi temel

- `temel.ag_kur`, şerit rijitlikleri (I = b·h³/12, J ≈ b·h³/6), Winkler yayları ve isteğe bağlı aks kirişleri `yapi_serbest`'e bağlanır; `TEMEL_TIP_HATASI` kalkar.
- Kolon tabanı mesnetleri temel ızgarasına bağlanır.
- `rapor`, `tablolar` ve `alan.radye_alani` genel modelde çalışır.
- **Eşdeğerlik:** `betonarme-4kat-radye` ve mütemadi temelli şablon `genellestir` ile çevrilip çözülür. Tepkiler, oturma ve taban basıncı aks–kat çözümüyle bağıl ≤ 1e-6 olmalıdır.
- Bundan sonra C1 onayı temeli tekile döndürmez; IFC'de BASESLAB ve STRIP_FOOTING eşlenir.

### 17.2 Ağa bağlı yerler

| Aile | Parametre | Bugünkü kural |
|---|---|---|
| Radye | `temeller.radye.ag` | 0,5 m'den başlar; SD sınırına sığana dek büyütülür (`temel.ag_kur`) |
| Mütemadi | `temeller.surekli.ag` | Aynı; Winkler yayları düğümlerde |
| Vute | `analiz.vute_parca` (1–6) | Kademeli prizmatik |
| Kren | `kren[].konum_sayisi` | Hareketli yük zarfı |
| İstasyon | `analiz.diyagram_nokta` (3–41), `bina_alan.istasyon` (2–61) | Uç değer yakalama |
| Navier | `alan.py` terim sayısı | Isı haritası plak alanı |

Prizmatik çerçeve çubukları doğrusal statikte tek elemanla kesindir. Bu bir testle kilitlenir: çubuğu 2 ya da 4 parçaya bölmek sonuçları 1e-9 içinde değiştirmez. Deprem eşdeğer yük yöntemi ve Rayleigh periyodu kat kütleleriyle çalışır; mod birleştirme yoktur, dolayısıyla eleman bölmeye duyarsızdır. Döşemeler yük dağıtımıyla temsil edilir; plak FE yoktur (§23).

### 17.3 İzlenen büyüklükler

| Aile | İzlenen büyüklükler |
|---|---|
| Radye | en büyük oturma, en büyük taban basıncı, kolon altı tepkileri, kolon yüzü kritik kesitinde ve açıklık ortasında şerit ortalamalı momentler (iki doğrultu), zımbalama V_pd, temel D/C maks |
| Mütemadi | oturma ve basınç maks, temel kirişi M (kolon yüzü ve açıklık), V, kolon tepkileri |
| Vute | uç momentleri, en büyük sehim, D/C, tepe ötelemesi |
| Kren | kren kirişi M ve V maks, kolon N zarfı |
| İstasyon | M maks ve min, D/C maks |
| Navier | panel m_x, m_y, w maks |

**Tekillik kuralı:** tekil kolon yükü altındaki düğüm tepe momenti plak tekilliği yüzünden yakınsamayabilir. Bu değer yalnız bilgi olarak raporlanır, eniyileme ölçütüne girmez.

### 17.4 Algoritma (`ag_eniyile.py`)

1. **Aday dizisi:**
   - Radye ve mütemadi: a_k = a₀/rᵏ, r = √2, a₀ = min(2,0 m; en kısa açıklık/4); alt sınırlar `EN_KUCUK_AG` ve SD sınırı.
   - Vute n ∈ {1, 2, 3, 4, 6, 8, 12}; kren {5, 9, 17, 33}; istasyon {11, 21, 41, 61}; Navier terim sayısı {5, 9, 17, 33}.
2. **Hafif çözüm:** anlatımsız, yalnız karakteristik durumlar; tasarım kombinasyonları süperpozisyonla bulunur. Yalnız çekme çubuğu varsa kombinasyon doğrudan çözülür.
3. **Hata tahmini** (kabadan inceye ardışık üç aday):
   - p = ln(|f₁ − f₂| / |f₂ − f₃|) / ln r, [0,5; 4] aralığına kırpılır;
   - f* = f₃ + (f₃ − f₂)/(rᵖ − 1);
   - GCI = 1,25·|f − f*|/|f*|.
   - Monoton olmayan dizide salınım bayrağı konur.
   - |f*| ailenin en büyük değerinin %1'inden küçükse mutlak ölçek kullanılır.
4. **Seçim:** bütün izlenen büyüklükler için GCI ≤ %2 sağlayan **en kaba** aday. Sınıra ulaşılırsa "±%2 doğrulanamadı" uyarısı verilir.
5. **Doğrulama:** seçilen ağ ile en ince çözülen ağ arasındaki fark raporlanır.
6. **Sonuç:** `analiz.ag_secimi = {…, tolerans: 0.02, kimlik}` ve `ag_raporu` yazılır. Analiz › Ağ raporu altında ImPlot yakınsama grafikleriyle gösterilir.

### 17.5 Bağlantı ve maliyet

- Köprü işlemi `bina_ag_eniyile` girdi olarak `{bina, aileler?, tolerans?}` alır. **Çözücüye dokunulmaz;** çalışma yalnız mevcut girdi parametrelerini değiştirir.
- op4'te yeni projelerde varsayılan açıktır. F5 öncesinde, ilgili alt modelin kimliği değiştiyse otomatik koşar. Web sürümünde ve eski projelerde kapalıdır.
- Maliyet 3–6 ek hafif çözümdür. Yalnız ilgili aile varsa çalışır ve kimliğe göre önbelleğe alınır.

---

## 18. Kimlik, açılış ekranı, kurulum

### 18.1 Kimlik dosyaları (`op4/kimlik/`; mevcut)

| Yer | Dosya (öncelik sırasıyla) |
|---|---|
| Açılış ekranı logo yuvası (açık zemin; 96 DPI'da 540×160 kutu) | `logo.png` → `opus-fortis-yatay-acik-zemin.png` (2000×712) → `opus_fortis_logo_placeholder.png` |
| Koyu tema "Hakkında" ve arayüz | `opus-fortis-yatay-koyu-zemin.png`, `opus-fortis-yazi-koyu-zemin.png` |
| Simge | `op4.ico` (`araclar/kimlik_uret.py` ile `opus-fortis-simge-renkli.png`'den; 16–256) → `op4_simge_placeholder.ico` |
| Kurulum sihirbazı görselleri (Faz 0 kapanışı) | `simge-renkli` ve `yatay` PNG'lerinden 164×314 ve 55×55 BMP |
| Palet | README tablosu (kahve #8A6B3C, krem #EDE6D8, altın #B08950, antrasit #14181B, gri #8C8C8C); `kimlik_uret.py` bunu `renkler.json`'a da yazar |

Yeni bir logo dosyası konunca kod değişmeden kullanılır; dosya eksikse uyarı verilir, derleme durmaz.

### 18.2 Açılış ekranı (denemede çalışıyor)

- `wWinMain` başında, D3D başlatılmadan önce gösterilir: katmanlı pencere, WIC ile PNG, DPI ölçekli.
- İçerik: logo, "op4", alt başlık, antrasit bant, altın ilerleme çubuğu ve durum satırı, sürüm, "© Opus Fortis".
- En az 1,2 s görünür, ana pencere hazır olunca kapanır.
- `--acilis-yok` bayrağı açılış ekranını kapatır; `--test-acilis` ekranı PNG'ye çizer.

### 18.3 Kurulum

Betik `op4/kurulum/op4.iss` (UTF-8 BOM). Mevcut ayarlar:
- `AppPublisher` Opus Fortis; sabit `AppId`.
- `DefaultDirName={autopf}\Opus Fortis\op4`.
- Türkçe ve İngilizce sihirbaz.
- LZMA2/max, solid.
- Başlat menüsünde "Opus Fortis" klasörü; isteğe bağlı masaüstü kısayolu.
- `.op4` ilişkilendirmesi; MinVersion 10.0.17763.

Değişiklikler:
- `PrivilegesRequired=lowest` ile varsayılan kullanıcı başına kurulum (yönetici gerekmez). `PrivilegesRequiredOverridesAllowed=dialog commandline` korunur.
- `AppUserModelID = OpusFortis.op4`.
- `[Components]`: Çekirdek (zorunlu), IFC içe aktarma (Faz 6, isteğe bağlı), Seyrek çözücü (Faz 5, kararla).
- Dosya adı `op4-setup-<sürüm>.exe`; sürüm etiketten alınır.
- WebView2 denetimi ve önyükleyicisi (Faz 5).
- Kaldırmada kullanıcı verileri sorulduğunda silinir; varsayılan korumaktır.

**Lisans doğrulaması (D14):** CI, `%ProgramFiles(x86)%\Inno Setup 6\license.txt` dosyasının ilk satırlarını günlüğe basar. Ticari kullanım şartı varsa iki yol vardır: lisans satın alınır (kullanıcı kararı) ya da `op4/kurulum/op4.nsi` ile NSIS'e (zlib) geçilir. NSIS'te aynı adımlar ve aynı sessiz kurulum ve kaldırma testi uygulanır.

**Bağımlılık:** `op4.exe` ve `op4motor.exe` statik CRT ile derlenir. `python3XX.dll` kendi `vcruntime140*.dll` dosyalarıyla gelir. CRT nesneleri sınırdan geçirilmez.

**İmza:** paketler imzasızdır; SmartScreen uyarısı belgelenir. `OP4_IMZA_*` gizli anahtarları tanımlanırsa `signtool` adımı çalışır (OV sertifikası ya da bulut imzalama hizmeti; kullanıcı kararı).

### 18.4 Kullanıcı verileri

- `%APPDATA%\Opus Fortis\op4\`: `ayarlar.json`, `arayuz.ini`, `takma_adlar.json`, `kisayollar.json`.
- `%LOCALAPPDATA%\Opus Fortis\op4\`: `kurtarma\`, `gunluk\`, `cokme\`, `gecici\`, `WebView2\`, `onbellek\`.

---

## 19. Kod düzeni, derleme, bağımlılıklar, lisanslar

```
op4/
  CMakeLists.txt  CMakePresets.json (win-surum, win-hata, linux-cekirdek, linux-cekirdek-asan)
  cmake/          Bagimliliklar.cmake (FetchContent + işleme özeti doğrulaması, denemedeki yöntem),
                  Golgelendiriciler.cmake (fxc), JsGom.cmake, Surum.cmake (etiketten)
  kaynak/         C++ (denemedeki dosyalar buraya dağıtılır)
    cekirdek/     kamera, bvh, yakalama, secim, secim_suzgeci, oznitelik_tablosu, komut_cercevesi,
                  girdi_sozdizimi, proje_dosyasi (.op4 zip), ayarlar, sahne_anlik, profil_ad,
                  motor_istemci (çerçeveleme, yönlendirme; Win32 + POSIX süreç)
                  → op4_cekirdek kitaplığı: Windows başlığı yok, Linux'ta derlenir
    geometri/     profil_dis_cizgi, tessellation (±%2), ekstruzyon, lod, panel_ucgenleme,
                  ag_iyilestirme, ozellik_hesabi                    → Linux'ta derlenir
    cekirdek_js/  QuickJS barındırıcı, ön yükleme, cephe, tipli dizi köprüsü → Linux'ta derlenir
    grafik/       aygit, takas_zinciri, bellek, gecisler, ornekler, etiketler, kimlik_tamponu, ekran_goruntusu
    arayuz/       ana_pencere, serit, komut_satiri, dinamik_giris, ozellik_izgarasi, model_gezgini,
                  tablo_duzenleyici, suzgec_penceresi, yuk_paneli, mesnet_paneli, durum_cubugu,
                  gorunum_kupu, baslangic_paneli, iletisim, acilis_ekrani
    platform/win/ giriş, manifest, DPI, pano, sürükle-bırak, tek örnek, ilişkilendirme
    belge/        WebView2 barındırma, mesaj köprüsü, yazdırma/PDF
    motor_barindirici/ op4motor.exe (Py_Main)
  golgelendiriciler/ *.hlsl
  motor/          op4_sunucu.py (Python sunucu döngüsü)
  js/             op4_cekirdek.js, op4_ops.js
  veri/           komutlar.json, oznitelikler.json, varsayilan_ayarlar.json, sablonlar/ (derlemede), ikonlar/, fontlar/
  belge/          op4_belge.html (+ derlemede kopyalanan modüller)
  kimlik/         (mevcut)
  kurulum/        op4.iss (+ yedek op4.nsi), motor_gereksinimleri.txt (karmalı), lisanslar/
  araclar/        python_hazirla.py, kimlik_uret.py, yer_tutucu_kimlik.py, mingw.cmake (mevcut);
                  gunluk_png_coz.py, ci_bekle.sh, lisans_envanteri.py, sablon_dok.py, altin_yenile.py
  testler/        cekirdek/ (doctest), js/ (node), python/ (pytest: op4_sunucu, ifc_iceri, ag_eniyile),
                  ortak/ (profil_adlari.json vb.), senaryolar/*.json, altin/*.png
kök: ifc_iceri.py, ag_eniyile.py (Faz 6–7)
```

CMake'teki `if(NOT WIN32) FATAL_ERROR` koşulu yalnız Windows hedeflerine daraltılır; `op4_cekirdek` ve testler her platformda derlenir.

**Bağımlılıklar ve lisanslar:**

| Bileşen | Sürüm | Lisans | Faz |
|---|---|---|---|
| Dear ImGui (docking) | v1.92.9b-docking, `b48d1af…` (1.93.0 iki haftadan yeni olduğu için atlandı) | MIT | var |
| ImPlot | 1.92 uyumlu işleme | MIT | 5 |
| FreeType ve imgui_freetype | 2.13.x | FTL (belgede atıf) | 2 |
| quickjs-ng | iki haftadan eski son sürüm | MIT | 1 |
| nlohmann/json | 3.12.x | MIT | 1 |
| miniz | 3.0.x | MIT | 1 |
| doctest | 2.4.x | MIT | 1 |
| nanosvg | sabit işleme | zlib | 1 |
| meshoptimizer | ≥ 0.22 | MIT | 2 |
| earcut.hpp | 2.2.4 | ISC | 2 |
| D3D12MemoryAllocator | 3.x | MIT | 2 |
| WebView2 SDK ve WIL | ≥ 1.0.2903 / sabit | Microsoft WebView2 SDK lisansı (yeniden dağıtılabilir; metin paketlenir) / MIT | 5 |
| CPython embeddable | 3.14.x | PSF | 1 |
| numpy | 2.5.3 | BSD-3; tekerlekteki OpenBLAS BSD, gfortran çalışma zamanı GPL ve çalışma zamanı istisnası | var |
| sympy, mpmath | 1.14.0 / sabit | BSD | var |
| scipy (isteğe bağlı) | 1.18.1 | BSD-3 | 5 |
| ifcopenshell (isteğe bağlı) | 0.9.0 | LGPL-3.0-or-later; OCCT LGPL-2.1 ve istisna | 6 |
| shapely (GEOS), lark, isodate, python-dateutil, pyparsing, typing-extensions | sabit, karmalı | BSD-3 (GEOS LGPL-2.1), MIT, BSD-3, Apache-2.0/BSD, MIT, PSF | 6 |
| KaTeX, marked | 0.19, 18 | MIT | 5, 8 |
| Noto Sans, JetBrains Mono | sabit | OFL-1.1 | 2 |
| Inno Setup (derleme aracı) | imajdaki 6.x | Doğrulanacak (D14) | 0 |
| NSIS (yedek) | 3.x | zlib | yedek |

`araclar/lisans_envanteri.py` paketlenen tekerleklerin METADATA ve LICENSE dosyalarından ve C++ bağımlılık listesinden `lisanslar/` klasörünü ve Hakkında penceresindeki listeyi üretir. LGPL bileşenleri için kaynak bağlantısı ve değiştirilebilirlik notu eklenir.

**Kodlama kuralları:**
- C++20, `op4::` ad alanı.
- MSVC: `/W4 /permissive- /utf-8 /Zc:__cplusplus /MP` (denemede var; `/WX` Faz 1'de açılır). Clang: `-Wall -Wextra -Werror`.
- Kullanıcı metinleri UTF-8'dir. İstisnalar yalnız sınırlarda kullanılır.
- Türkçe ASCII adlar ve öğretici hata iletileri.
- Üretici adı verilmez (`cmake -A x64`).

---

## 20. CI ve bu ortamdan doğrulama

### 20.1 İşler (`.github/workflows/op4.yml`)

**Tetikleyiciler:**
- `main` ve `claude/**` dallarına push; PR'lar.
- Yollar: `op4/**`, `docs/*.js`, `docs/*.py`, kök `*.py`, iş akışı dosyası.
- `op4-v*` etiketi; `workflow_dispatch` (`altin_yenile`).

Eylemler işleme özetiyle sabitlenir.

| İş | Ortam | Adımlar |
|---|---|---|
| `cekirdek-linux` (Faz 1) | ubuntu-24.04 | Python 3.13 ve 3.14, Node 22, clang, ninja. `cmake --preset linux-cekirdek-asan`, `ctest` (kamera, BVH, yakalama, süzgeç dili, proje zip, tessellation, QuickJS eşdeğerliği, motor istemcisi ↔ `python3 -m op4_sunucu`). `node --test op4/testler/js/*.test.js`. `pytest op4/testler/python`. `OP4OLCUM` ölçümleri. |
| `windows` | **windows-2025** | Önbellek (`_deps`, pip). Yapılandır ve derle. `ctest`. Paketleme (3.14). `--test-motor` soğuk ve ılık. Senaryolar (WARP; PNG ve `OP4OLCUM`). `--test-pencere` (**engelleyici**). Hata ayıklama katmanı yoklaması. Inno lisans satırları. ISCC (pwsh). Sessiz kurulum `C:\op4 dene ŞĞİı`. Kurulu programla `--oz-sinama`. Sessiz kaldırma ve klasör denetimi. Özet. Artifact. |
| `yayinla` | ubuntu, yalnız etikette | `needs: windows`; artifact GitHub Release'e eklenir (`contents: write`) |

Mevcut `testler.yml` aynen sürer (bekçi testi dahil). `masaustu.yml` Faz 8'de kaldırılır. Gecelik iş GPU tabanlı doğrulamayı açar.

### 20.2 Günlükten doğrulama yöntemi (deneme ile kanıtlandı)

Artifact'lar ve ham günlük yönlendirmesi blob depolamaya gider ve bu ortamdan 403 döner. Yöntem:
1. Çalışma durumu api.github.com'dan `op4/araclar/ci_bekle.sh <run_id>` ile izlenir. Ön planda uyku yasak olduğu için arka planda çalıştırılır.
2. `mcp__github__get_job_logs` aracı `ToolSearch "select:mcp__github__get_job_logs,mcp__github__actions_list,mcp__github__actions_get"` ile yüklenir ve `return_content=true`, büyük `tail_lines` (≥ 2300) ile çağrılır. Varsayılan 500 satır orta adımları kaçırır. Yanıt sınırı aşarsa araç sonucu bir dosyaya kaydeder.
3. `python3 op4/araclar/gunluk_png_coz.py <kayıt> <çıktı-klasörü>` JSON'daki `logs_content` alanını açar, zaman damgalarını atar, işaretler arasını çözer ve sha256 denetler. base64 bağlama hiç girmez.
4. PNG'ler Read ile incelenir.

Kullanıcı kurulum dosyasını Actions › Artifacts bölümünden ya da Releases sayfasından indirir.

### 20.3 Günlük protokolü

```
::group::OP4-PNG sahne
OP4-PNG ad=sahne bayt=48211 gunluk_bayt=… sha256=<hex> gen=960 yuk=540
-----OP4-PNG-BASLA-----
<base64 -w 100>
-----OP4-PNG-BITIR-----
::endgroup::
OP4OLCUM senaryo=gezinme_kaydir kare=300 yeniden_uretim=0 en_buyuk_capa_px=0.0001 ort_kare_ms=…
```

- Günlüğe basılan görüntü 256 renge indirgenir (Pillow yalnız CI'da). Görüntü başına ≤ 300 KB, iş başına ≤ 6 MB.
- **Altın karşılaştırma CI'da tam renkli PNG ile yapılır:** fark alanı ≤ %0,5 ve ΔE ≤ 8. Başarısızlıkta fark görüntüsü de basılır.
- `altin_yenile` girdisi yeni altın üretir; yeniler bu ortamda incelenip depoya konur.

### 20.4 Yerel denetim (Linux)

- MinGW-w64 13 ve `op4/araclar/mingw.cmake` ile derleme ve bağlama denetimi yapılır.
- Wine 9, vkd3d ve lavapipe (Xvfb) altında ekran testleri çalışır; motor testleri yalnız gerçek Windows'ta yapılır.
- Gömülü Python'un yerel taklidi için NuGet "python" paketinden zip kurulur (api.nuget.org erişilebilir, python.org değil).

---

## 21. Test stratejisi

| Katman | Ne | Nerede |
|---|---|---|
| Motor (değişmez) | `pytest testler -q`, ders denetimi, bekçi testi | `testler.yml` |
| Motor eklemeleri | `anlat=false` eşitliği; `bina_kimlik`; `sd_siniri`; iptal türü; bilinmeyen alanların yok sayılması; başarım (altınla bağıl ≤ 1e-12); seyrek yol (yoğunla ≤ 1e-9); genel modelde radye ve mütemadi (aks–kat ile ≤ 1e-6); `ifc_iceri`; `ag_eniyile` | pytest (Linux; 3.13 ve 3.14) |
| Motor sunucusu | İstek ve yanıt, iptal (`interrupt_main`), kilitlenme sonrası sonlandırma ve yeniden başlatma, 50 MB yanıt, stdout'a `print` protokolü bozmuyor | pytest ve ctest (Linux); Windows `--test-motor` |
| JS çekirdek | Mevcut node testleri; `op4_ops`; cephe; derlem üretimi | node |
| QuickJS eşdeğerliği | Derlem QuickJS'te yürütülür, 1e-12 | ctest (Linux ve Windows) |
| C++ çekirdek | K1, K3, K4; BVH; yakalama; süzgeç dili (60'tan fazla örnek, HE340A); `.op4` gidiş-dönüşü ve eski biçimler; tessellation ±%2; komut durum makineleri; ASan ve UBSan | doctest |
| Ortak vektörler | `profil_adlari.json` JS, C++ ve Python'da aynı sonucu verir | üçü |
| Grafik | WARP altınları; K2; K5; büyük koordinat; kimlik tamponu ile CPU seçme tutarlılığı; katman varsa hata ayıklama katmanında 0 hata | Windows |
| Uçtan uca | Komut betikleri (ör. `YENI; HIZLIAKS …; KOLON tum; …; COZ; KAYDET; AC`); model karması; D/C değerleri Linux pytest ile bağıl ≤ 1e-9; ekran görüntüsü | Windows |
| Kurulum | Sessiz kurulum ve kaldırma, Türkçe karakterli yol, `--oz-sinama`, ilişkilendirme, isteğe bağlı bileşenler | Windows |
| Elle (kullanıcı) | Her fazın kurulum dosyasıyla gerçek GPU'da denetim listesi: gezinme, yakın plan, yüksek DPI, karma GPU, iki ekran | Kullanıcı |

---

## 22. Aşamalı plan (özet)

| Faz | Başlık | İstekler | Teslim | Boyut |
|---|---|---|---|---|
| 0 | İskelet: **TAMAMLANDI** (deneme). Kapanış: bekçi, CI tetikleyicileri, araçlar, lisans ve katman yoklaması, main'e PR | Program | `op4-setup-0.0.x.exe` | XS, 2–3 gün |
| 1 | Program kabuğu: model çekirdeği, motor süreci, boş başlangıç, dosya işlemleri, gezinme ve seçim, kat ve kullanım öznitelikleri, IFC dışa aktarma | 4, 6, 8, 9, 2 (temel), 7 (dışa) | `0.1.0` | L, 4–5 hafta |
| 2 | Gerçek kesitler, yüksek kalite, görüntü ağı ±%2 | 5, 9, 10 (görüntü) | `0.2.0` | M, 2,5–3,5 hafta |
| 3 | Seç ve Süz; kat ve kullanım yeri bazlı seçim; yük ve mesnet atama | 2, 3 | `0.3.0` | L, 3–4 hafta |
| 4 | Çizim ve düzenleme komutları; çok katlı çizim | 1, 2 | `0.4.0` | XL, 5–7 hafta |
| 5 | Analiz, tasarım ve çıktılar; Belge penceresi; motor başarımı ve ölçeği | Her şey op4'te | `0.5.0` | XL, 6–8 hafta |
| 6 | IFC içe aktarma | 7 | `0.6.0` | L, 3–4 hafta |
| 7 | 7a genel modelde radye ve mütemadi; 7b analiz ağı ±%2 (Python ağırlıklı **paralel iz**; Faz 1'den sonra başlar, 7a Faz 6'dan önce biter) | 10 (analiz) | `0.7.0` | L, 4–5 hafta |
| 8 | Sonlu eleman, Matris, Dersler; Electron sürümü kaldırılır; 1.0 | Her şey op4'te | `op4-setup-1.0.0.exe` | L, 4–5 hafta |

Toplam ≈ 32–42 hafta (bir deneyimli geliştirici eşdeğeri). Faz 7 paralel yürürse kritik yol ≈ 28–37 haftadır.

**Sıralamanın gerekçesi:**
- Riskli altyapı (Windows CI, WARP, gömülü Python, kurulum) denemede doğrulandı.
- Faz 1 model, motor ve dosya temelini kurar. Kat ve kullanım öznitelikleri gezgin ve seçim için şimdiden gereklidir (D9). IFC dışa aktarma ucuzdur ve mevcut bir özelliği korur (D11).
- Görüntü mimarisi (örnekleme, LOD, seçme) etkileşim ağırlıklı işlerden önce oturur.
- Seç ve Süz ile atama kapsamları, değiştirme komutlarının ve "Süzgeç…" istemlerinin altyapısıdır; çizimden önce gelir (D10).
- Sonuçlar IFC içe aktarmadan önce gelir; içe alınan model analizle anlam kazanır. Seyrek yol büyük IFC modelleri için Faz 5'te hazır olur.
- Analiz ağının anlamlı olması için genel modelde temel gerekir (D6).
- Electron sürümü her şey op4'e geldiğinde kaldırılır.
- Her faz sonunda etiketli bir Release çıkar; main'e her itme bir artifact üretir.

---

## 23. Kullanıcı onayı gereken kararlar

1. **Belge penceresi:** dersler, rapor önizleme ve yazdırma ile anlatım, ayrı bir yerel pencerede WebView2 ile gösterilir; program yerel kalır, ağ yoktur. Seçenekler:
   - (a) Kabul.
   - (b) Matris ve anlatım çıktısı için yerel matematik denemesi (Faz 5, 3 gün).
   - (c) Derslerin tamamen yerel yeniden yazımı (+10–14 hafta).
2. **Serbest çizim:** §19'daki "serbest koordinatlı düğüm yok" kararı gevşetilir. Parametrik öncelik korunur; katı kip bir proje ayarıdır, varsayılan kapalıdır.
3. **Pencere seçimi:** Ctrl+sol sürükle (sol sürükle kaydırdığı için). "Klasik CAD" fare hazırı da sunulur.
4. **Kısayollar:** F3, F7, F8, F9, F10, F12. Rapor `Ctrl+Shift+R` olur. Tek harfler takma ada dönüşür (harf + Enter).
5. **Kimlik:** gerçek logo, simge ve palet geldi ve kullanılıyor. Onay bekleyenler: kurulum sihirbazı görselleri ve kod imzalama sertifikası (isteğe bağlı satın alma).
6. **Platform:** Windows 11 ve Windows 10 (1809+) x64. Windows 10 Ekim 2025'te genel destek dışına çıktı; sınama Windows 11 / Server 2025 sınıfında yapılır. macOS ve Linux paketleri Faz 8'de sona erer.
7. **IFC bileşeni:** ifcopenshell (LGPL), OCCT ve GEOS isteğe bağlı bileşen olarak gelir; kurulu boyuta ≈ +120 MB ekler.
8. **Web sürümü:** GitHub Pages'teki web sürümünün yayında kalıp kalmayacağı. `docs/` ders ve çekirdek kaynağı olarak depoda kalır.
9. **Analiz ağı kapsamı:** motorda plak ve kabuk sonlu elemanı yoktur. ±%2 eniyileme radye, mütemadi, vute, kren, istasyon ve Navier ailelerine uygulanır; döşemelerin sonlu eleman ağı bu plan dışındadır. Plak/kabuk FE ayrı ve büyük bir iştir.
10. **Kurulum aracı lisansı:** Inno Setup ticari kullanım koşulu doğrulanır. Gerekirse lisans alınır ya da NSIS kullanılır.
11. **Python sürümü:** gömülü çalışma zamanı 3.14 olur (3.13 güvenlik evresinde ve ikili yayımlanmıyor). Motor 3.13 ile de uyumlu kalır.
12. **Pencere başına bir proje:** 1.0'da proje sekmeleri yoktur; ikinci proje yeni pencerede açılır.
13. **Büyük modeller:** seyrek çözücü yolu için scipy (≈ +90 MB, isteğe bağlı bileşen). Seçilmezse op4 ≈ 6000 SD ile sınırlı kalır; gerçek binaların IFC'leri çoğu zaman bunu aşar.
14. **Geçici düzeltme:** masaüstü (Electron) sürümünde titreşim düzeltmesi ve sol/Shift fare eşlemesi (≈ 1 gün). İstenirse Faz 1'de yapılır.

---

## 24. F1 paket sözleşmeleri

Faz 1 dört paketle **paralel** yürür. Bu bölüm, paketlerin birbirini beklemeden çalışabilmesi için arayüzleri (sözleşme
katmanı, "S"), dosya sahipliğini, birlikte çalışma kurallarını ve paket başına kabul denetimlerini sabitler. Sözleşme
katmanı derlenen, sınanan **taslak uygulamalarla** birlikte gelir: program bugün derlenir, Faz 0 davranışı değişmez,
her paket kendi taslağını gerçeğiyle değiştirir. Bölüm §4, §6–§9, §12–§14 ve §19–§21'e dayanır; çelişkide onlar geçerlidir.

### 24.1 Paketler ve Faz 1 iş listesi

Faz 1 iş listesi önceki bölümlerde numarasızdı; numaralar burada sabitlenir.

| İş | Paket | Kapsam | Dayanak |
|---|---|---|---|
| 1.1 | **A** derleme-motor | Derleme yapısı: Windows'suz `op4_cekirdek` (Linux'ta derlenir ve sınanır), CMakePresets (win-surum, win-hata, linux-cekirdek, linux-cekirdek-asan), Linux CI işinin genişletilmesi (Python 3.13 + 3.14, ASan/UBSan, `OP4OLCUM`), gölgelendiricilerin derlemede FXC SM 5.1 ile derlenmesi, `/WX` | §6.1, §19, §20.1, D12 |
| 1.2 | **A** derleme-motor | Motor süreci: `op4motor.exe`, `op4/motor/op4_sunucu.py`, Win32 ve POSIX C++ istemcisi (çerçeveleme, id, iptal, yeniden başlatma, yönlendirme), `docs/web_kopru.py`'ye eklemeli işlemler (`anlat`, `bina_kimlik`, iptal türü, `sd_siniri`) ve pytest | §8 |
| 1.3 | **B** model-cekirdegi | QuickJS-ng tümleşimi, ön yükleme, tipli dizi köprüsü; `op4/js/op4_cekirdek.js` cephesi ve `op4/js/op4_ops.js` (`bosModel`, `katUyeligi`, `kullanimYeri`, `profilAdiNormal`, `oznitelikCikar`, `sahneCikar`, `sonucEsle`); node sınamaları ve 1e-12 eşdeğerlik derlemi | §9, §10.2–§10.5 |
| 1.4 | **C** arayuz-goruntu | Şerit / menü / hızlı erişim (`komutlar.json`'dan), komut satırı, durum çubuğu, Başlangıç paneli (boş "Adsız 1", 9 şablon, hızlı aks), çubuk görünümü çizimi, gezinme (sol sürükle kaydır, Shift+sol döndür, tekerlek imlece, orta kaydır, görünüm küpü, Alt+1…4, PgUp/PgDn), CPU BVH seçme ve pencere seçimi, vurgu, model gezgini (kat → tür → kullanım yeri, sayılarla), salt okunur Özellikler, GPU tercih dışa aktarımları (D26), Ayarlar › Grafik, `--senaryo` | §5, §6.1, §6.5, §6.9, §7 |
| 1.5 | **D** dosya-cozum | Çözüm: F5 eşzamansız, iptal, sonuç özeti, D/C renkleri, eski işareti; şablon dökümü (`op4/veri/sablonlar/`) | §4 çözüm akışı, §13.4 |
| 1.6 | **D** dosya-cozum | Dosyalar: `.op4` ZIP (miniz), atomik yazma, kirli işareti, otomatik kayıt ve kurtarma, son dosyalar, `.matris` / `.json` içe aktarma, ilişkilendirme, tek örnek borusu, çökme dökümü, IFC dışa aktarma (JS çekirdek üstünden) | §13, §14.1 |
| 1.7 | entegratör (+ hepsi) | Bütünleştirme ve kabul: uçtan uca senaryolar, `--oz-sinama`, TASARIM §20 (mimari), §21 (.op4 biçimi; D yazar), §22 (komut çerçevesi; C yazar), `op4-v0.1.0` etiketi | §21, §22 |

### 24.2 Sözleşme katmanı (S)

Bütün C++ sözleşmeleri `op4::` ad alanında, Türkçe ASCII adlarla ve başlık yorumlarında belgelidir. "Taslak" sütunu
sözleşme işlemesinde gelen uygulamanın durumunu gösterir: **tam** = kullanılabilir, **taslak** = doğru biçimde boş /
"henüz uygulanmadı" döner.

| Kod | Dosya | Konu | Uygulayan | Kullanan | Taslak |
|---|---|---|---|---|---|
| S1 | `kaynak/cekirdek/kimlik.h` | `ElemanKimligi {tur u8, alt u16, no u32}`, tür kodları, metin biçimi `cubuk:12` | S | hepsi | tam |
| S2 | `kaynak/cekirdek/olay.h` | `Olay<…>` gözlemci listesi (UI iş parçacığı) | S | hepsi | tam |
| S3 | `kaynak/cekirdek/vektor.h` | `V3d`, `Kutu3d` (double) | S | hepsi | tam |
| S4 | `kaynak/cekirdek/sahne.h`, `veri/sahne_kodlari.json` | `SahneAnlik` (değişmez, `SahnePtr`): seviyeler, akslar, düğümler, çubuklar, paneller, mesnetler, temeller, kesitler; kod tabloları; `OrnekSahneAnlik()` sınama düzeneği | B üretir | C çizer, BVH | tam |
| S5 | `kaynak/cekirdek/oznitelik.h`, `veri/oznitelikler.json` | Sütunlu öznitelik tablosu, Faz 1 alan kimlikleri, `OrtakOzellikler` ("(çeşitli)") | B üretir | C gezgin, Özellikler | tam |
| S6 | `kaynak/cekirdek/turkce.h` | Türkçe harf katlama, ondalık virgül, sayı okuma | C | hepsi | tam |
| S7 | `kaynak/cekirdek/secim.h` | `Secim` (sıralı, tekrarsız; Yeni / Ekle / Çıkar / Tersle / İçinde süz; sürüm, olay) | C | hepsi | tam |
| S8 | `kaynak/cekirdek/secme.h` | `GorusIzdusumu` (double), `SecmeDizini` (BVH: EnYakin, Adaylar, Pencere, IsinVurusu, Sinir) | C | C | taslak (izdüşüm tam, BVH boş) |
| S9 | `kaynak/cekirdek/gorunum.h` | `GorunumDurumu` (kip, renk kipi, ızgara, üzerindeki eleman, `SonucBoyamasi`, çizim / sığdır istekleri) | C | C okur, D sonuç yazar | tam |
| S10 | `kaynak/cekirdek/gezgin.h` | Model gezgini ağacı (kat → alt tür → kullanım yeri; sayılar, kimlikler) | C | C | taslak |
| S11 | `kaynak/cekirdek/model_cekirdegi.h` | `ModelCekirdegi`: YeniBos, Yukle, Uygula (beyaz liste), GeriAl, Yinele, GeriAlBilgisi, Sahne, Oznitelikler, Ozet, Denetle, Metin, SonucEsle, IfcDisari; `IslemRaporu` (eklenen / silinen / değişen, C1 geçiş onayı) | B | C, D | taslak (geçici C++ çekirdeği: boş model, yükle, metin) |
| S12 | `kaynak/cekirdek/motor_protokol.h`, `motor/op4_protokol.py`, `testler/ortak/motor_protokol.json` | Tel protokolü: çerçeve, ileti biçimleri (bağlayıcı alan sırası), Y1–Y4 değişmezleri, süreç komut satırı, çıkış kodları; C++ ve Python kodlayıcıları ortak vektörlerle | S | A | tam |
| S13 | `kaynak/cekirdek/motor_hizmeti.h` | `MotorHizmeti` (eşzamansız Gonder / Iptal / Pompala; işleyiciler UI iş parçacığında, her istek için tam bir kez), `MotorRoluSec` (§8.3), `MotorIstemcisiOlustur` | A | D, C, A | Windows'ta süreç içi gömülü motor uyarlayıcısı (`motor_modulu.cpp`); süreç istemcisi taslak |
| S14 | `kaynak/platform/surec.h` | Alt süreç + iki anonim boru (Win32 / POSIX) | A | A | taslak |
| S15 | `kaynak/cekirdek/proje_belgesi.h` | `ProjeBelgesi`: yol, ad ("Adsız N"), pencere başlığı ("op4 — ad •"), kirli işareti, **kaydetme katkıları** (her modül kendi ZIP girdisini yazar / okur), olaylar | D | C başlık, hepsi katkı | tam |
| S16 | `kaynak/cekirdek/proje_dosyasi.h` | `.op4` ZIP okuma / yazma, `BicimSapta`, manifest, son dosyalar, kurtarma kayıtları | D | D | taslak (BicimSapta, SonDosyaEkle tam) |
| S17 | `kaynak/platform/dosya_sistemi.h` | Atomik yazma, okuma, kullanıcı klasörleri (`OP4_KULLANICI_DIZINI` sınama yönlendirmesi) | D | hepsi | taşınabilir tam; Windows sağlamlaştırması D |
| S18 | `kaynak/cekirdek/ayarlar.h` | `Ayarlar` (grafik → C, arayüz → C, dosya → D, motor → A, çekirdek → B gruplarıyla), JSON gidiş-dönüşü, bilinmeyen anahtarlar korunur | D kalıcılık | hepsi | tam |
| S19 | `kaynak/cekirdek/sonuc.h` | `SonucOzeti`, `SonucDurumu` (eski işareti, olay), `DcRengi` (web ölçeği: < 0,7 / 0,9 / 1,0 / > 1), `BoyamaKur`, yanıt çözümü | D | C çizer | kısmi (renk, durum tam; yanıt çözümü taslak) |
| S20 | `kaynak/cekirdek/komut.h`, `veri/komutlar.json` | Komut kataloğu (id, ad, takma adlar, kısayol, şerit / menü yeri, ipucu, **sahip**) ve kayıt defteri: Bagla, Bul (Türkçe katlamalı), Tamamla, Durum (kullanılamama nedeni), Calistir, SatirCalistir, KisayolBul | C | hepsi bağlar | tam |
| S21 | `kaynak/cekirdek/arayuz_kancalari.h` | Panel, durum öğesi, menü katkısı, ayar sayfası kayıtları; `Bildirimler` (C uygular), `IletisimKutulari` (D uygular); pencere açmayan sınama sürümleri | C defter | hepsi kaydeder | tam (ImGui çizimi C'de) |
| S22 | `kaynak/cekirdek/hizmetler.h` | `Hizmetler`: paketlerin TEK buluşma noktası (işaretçiler, olaylar `modelDegisti` / `modelYuklendi` / `sahneDegisti`, `kapatmaOnayi`, kare işleri); `ModelIslemiUygula` (C1 onay döngüsü + kirli + seçim ayıklama + sonuç eski), `GeriAlUygula`, `YineleUygula`, `ModelYuklendi` | S | hepsi | tam |
| S23 | `kaynak/cekirdek/kabuk.h`, `kaynak/moduller_listesi.cpp` | `UygulamaKabugu` (ortak nesnelerin sahibi; ayarlar ve katalog yükleme; boş "Adsız 1"), `ModulOrtami` (sahiplik, ana pencere, test kipi, açılış dosyası), modül sırası A → B → C → D(dosya) → D(çözüm) | S | uygulama | tam; modüller taslak |
| S24 | `kaynak/secenekler.h`, `kaynak/test_kipleri.h` | F1 komut satırı bayraklarının tamamı (`--senaryo`, `--oz-sinama`, `--yeni-ornek`, `--acilis-yok`, `--grafik-denetim`, `--golgelendirici-dizini` …); test kiplerinin dağılımı | A | hepsi | tam (senaryo ve öz sınama taslak) |
| S25 | `kaynak/grafik/golgelendirici_bayt.h` | Derlemede üretilmiş gölgelendirici bayt kodu; grafik.cpp önce bunu sorar, yoksa çalışma anında derler | A | C | taslak (boş) |
| S26 | `js/op4_ops.js` | Yeni saf işlemler; JSDoc imzaları ve dönüş biçimleri; `KODLAR`, `OZNITELIK_IDLERI`, `TASLAK` listesi | B | B cephesi | `bosModel` tam; diğerleri biçimce doğru boş |
| S27 | `js/op4_cekirdek.js` | QuickJS cephesi (`olustur()` örneği): yöntemler S11 ile birebir; `ISLEMLER` beyaz listesi; hata kuralı; geri al kuralı | B | B'nin C++ köprüsü | yeniBos, yukle, metin, ozet tam; diğerleri taslak |

**Bağlayıcı kurallar (sözleşmeler arası):**
1. Model değişikliği her zaman `ModelIslemiUygula` / `GeriAlUygula` / `YineleUygula` yolundan geçer; böylece kirli işareti,
   seçim ayıklama, sonuç eskime ve olaylar tek yerde kalır. Yükleme `ModelYuklendi` ile biter; belge durumunu D
   `ProjeBelgesi::Acildi` ile kurar.
2. Hizmetler'e yalnız UI iş parçacığından dokunulur. Motor yanıtları `MotorHizmeti::Pompala`, çekirdek iş parçacığı
   (ileride) kendi kuyruğuyla UI'ye döner.
3. Sahne ve öznitelik anlıkları değişmezdir (`shared_ptr<const …>`); iş havuzu (BVH, LOD) kilitsiz okur.
4. Komutların davranışı yalnız `KomutYoneticisi::Bagla` ile eklenir; menü, şerit, kısayol ve komut satırı aynı defterden
   geçer. Faz 0 menüsü (`uygulama.cpp` `IstekleriIsle`) bir komut bağlanınca kendiliğinden onu çağırır.
5. `.op4` içeriği katkılarla toplanır: model → B'nin `Metin()`'i (D katkıyı ekler), `gorunum/` ve `secim/` → C,
   `sonuc/`, `manifest.json`, `onizleme.png` → D.

### 24.3 Dosya sahipliği

Bir paket YALNIZ kendi dosyalarını değiştirir. Aşağıdaki tablo makinece okunur (`testler/test_op4_sozlesme.py`):
**ilk eşleşen satır geçerlidir**; `*` klasör ayırıcısını geçmez, `**` geçer. Paketler: **A**, **B**, **C**, **D**; **S** =
sözleşme dosyası (§24.4 değişiklik kuralı); **-** = paket dışı: kurumsal kimlik ve açılış ekranı tasarım dosyaları
(`op4/kimlik/`; kullanıcının marka dosyaları değiştirilmez, açılış tasarımını kimlik çalışması yürütür; F1 paketleri
yalnız okur — C, açılış ekranını `acilis.cpp`'de bu dosyalardan çizer). Depodaki her op4 dosyası
bir satıra uymalıdır; yeni dosya, sahibinin klasörüne ya da adlandırma önekiyle eklenir.

```sahiplik
op4/MIMARI.md                                   S
op4/README.md                                   S
op4/kimlik/**                                   -
op4/cmake/JsGom.cmake                           B
op4/cmake/bagimlilik_quickjs.cmake              B
op4/cmake/bagimlilik_miniz.cmake                D
op4/cmake/**                                    A
op4/CMakeLists.txt                              A
op4/CMakePresets.json                           A
op4/.gitignore                                  A
op4/golgelendiriciler/**                        A
op4/kaynak/cekirdek/kimlik.h                    S
op4/kaynak/cekirdek/kimlik.cpp                  S
op4/kaynak/cekirdek/olay.h                      S
op4/kaynak/cekirdek/vektor.h                    S
op4/kaynak/cekirdek/sahne.h                     S
op4/kaynak/cekirdek/sahne.cpp                   S
op4/kaynak/cekirdek/oznitelik.h                 S
op4/kaynak/cekirdek/secim.h                     S
op4/kaynak/cekirdek/secme.h                     S
op4/kaynak/cekirdek/gorunum.h                   S
op4/kaynak/cekirdek/gezgin.h                    S
op4/kaynak/cekirdek/model_cekirdegi.h           S
op4/kaynak/cekirdek/motor_protokol.h            S
op4/kaynak/cekirdek/motor_protokol.cpp          S
op4/kaynak/cekirdek/motor_hizmeti.h             S
op4/kaynak/cekirdek/proje_belgesi.h             S
op4/kaynak/cekirdek/proje_dosyasi.h             S
op4/kaynak/cekirdek/ayarlar.h                   S
op4/kaynak/cekirdek/sonuc.h                     S
op4/kaynak/cekirdek/komut.h                     S
op4/kaynak/cekirdek/turkce.h                    S
op4/kaynak/cekirdek/arayuz_kancalari.h          S
op4/kaynak/cekirdek/hizmetler.h                 S
op4/kaynak/cekirdek/hizmetler.cpp               S
op4/kaynak/cekirdek/kabuk.h                     S
op4/kaynak/cekirdek/kabuk.cpp                   S
op4/kaynak/platform/surec.h                     S
op4/kaynak/platform/dosya_sistemi.h             S
op4/kaynak/grafik/golgelendirici_bayt.h         S
op4/kaynak/secenekler.h                         S
op4/kaynak/test_kipleri.h                       S
op4/kaynak/moduller_listesi.cpp                 S
op4/kaynak/cekirdek/motor_*                     A
op4/kaynak/cekirdek/oznitelik.cpp               B
op4/kaynak/cekirdek/oznitelik_*                 B
op4/kaynak/cekirdek/secim.cpp                   C
op4/kaynak/cekirdek/secme*                      C
op4/kaynak/cekirdek/bvh*                        C
op4/kaynak/cekirdek/kamera*                     C
op4/kaynak/cekirdek/gezinme*                    C
op4/kaynak/cekirdek/gezgin.cpp                  C
op4/kaynak/cekirdek/komut.cpp                   C
op4/kaynak/cekirdek/komut_*                     C
op4/kaynak/cekirdek/turkce.cpp                  C
op4/kaynak/cekirdek/arayuz_kancalari.cpp        C
op4/kaynak/cekirdek/girdi_*                     C
op4/kaynak/cekirdek/proje_*                     D
op4/kaynak/cekirdek/ayarlar.cpp                 D
op4/kaynak/cekirdek/sonuc*                      D
op4/kaynak/cekirdek/cozum_*                     D
op4/kaynak/platform/surec_*                     A
op4/kaynak/platform/dosya_sistemi*              D
op4/kaynak/cekirdek_js/**                       B
op4/kaynak/motor_barindirici/**                 A
op4/kaynak/grafik/golgelendirici_bayt*          A
op4/kaynak/grafik/**                            C
op4/kaynak/arayuz/**                            C
op4/kaynak/dosya/**                             D
op4/kaynak/cozum/**                             D
op4/kaynak/ana.cpp                              A
op4/kaynak/secenekler.cpp                       A
op4/kaynak/test_motor.cpp                       A
op4/kaynak/motor.*                              A
op4/kaynak/motor_modulu.cpp                     A
op4/kaynak/gunluk.*                             A
op4/kaynak/golgelendirici.h                     A
op4/kaynak/op4.manifest                         A
op4/kaynak/op4.rc.in                            A
op4/kaynak/proje.*                              D
op4/kaynak/uygulama.*                           C
op4/kaynak/test_ekran.cpp                       C
op4/kaynak/arayuz.*                             C
op4/kaynak/acilis.*                             C
op4/kaynak/grafik.*                             C
op4/kaynak/geometri.*                           C
op4/kaynak/kamera.h                             C
op4/kaynak/matematik.h                          C
op4/kaynak/resim.*                              C
op4/motor/op4_protokol.py                       S
op4/motor/**                                    A
op4/js/**                                       B
op4/veri/sahne_kodlari.json                     S
op4/veri/komutlar.json                          C
op4/veri/oznitelikler.json                      B
op4/veri/sablonlar/**                           D
op4/veri/**                                     C
op4/testler/cekirdek/ana_test.cpp               S
op4/testler/cekirdek/sinama_yardim.h            S
op4/testler/cekirdek/sozlesme_*                 S
op4/testler/cekirdek/motor_*                    A
op4/testler/cekirdek/cekirdek_js_*              B
op4/testler/cekirdek/arayuz_*                   C
op4/testler/cekirdek/secme_*                    C
op4/testler/cekirdek/kamera_*                   C
op4/testler/cekirdek/dosya_*                    D
op4/testler/cekirdek/cozum_*                    D
op4/testler/js/sozlesme.test.js                 S
op4/testler/js/**                               B
op4/testler/derlem/**                           B
op4/testler/python/test_protokol.py             S
op4/testler/python/**                           A
op4/testler/ortak/**                            S
op4/testler/senaryolar/arayuz_*                 C
op4/testler/senaryolar/dosya_*                  D
op4/testler/senaryolar/cozum_*                  D
op4/testler/altin/**                            C
op4/araclar/sablon_dok.py                       D
op4/araclar/kimlik_uret.py                      C
op4/araclar/yer_tutucu_kimlik.py                C
op4/araclar/**                                  A
op4/kurulum/**                                  A
.github/workflows/op4.yml                       A
docs/web_kopru.py                               A
testler/test_web_kopru_op4.py                   A
testler/test_op4_sozlesme.py                    S
testler/test_op4_araclar.py                     A
```

**Ortak dosyalar için kurallar:**
- `op4/CMakeLists.txt` (A): kaynaklar **klasör deseniyle** toplanır (`*_win.cpp` yalnız Windows, `*_posix.cpp` yalnız diğerleri).
  B, C ve D yeni `.cpp` dosyalarını kendi klasörlerine koyar; CMake'e dokunmaz. Yeni bağımlılık kendi
  `cmake/bagimlilik_<ad>.cmake` dosyasında (`op4_bagimlilik_git` / `op4_bagimlilik_url`; işleme özeti ya da SHA256 zorunlu).
  Sınamalar `op4/testler/cekirdek/<önek>_*.cpp` olarak eklenir; tek doctest yürütücüsüne kendiliğinden girer.
- `.github/workflows/op4.yml` (A): Linux işi `ctest`, `node --test op4/testler/js/*.test.js` ve `pytest op4/testler/python`'ı
  desenle çalıştırır; Windows işi `ctest` çalıştırır. Diğer paketler yeni dosya ekleyerek CI'a girer. Windows'a özgü yeni bir
  CI adımı gerekiyorsa (ör. D'nin şablon dökümü) A'ya §24.6 günlüğüyle istek bırakılır ya da A'nın onayıyla tek adım eklenir.
- `op4/veri/komutlar.json` (C): F1'in bütün komutları (37) sahipleriyle ÖNCEDEN yazılmıştır; paketler yalnız `Bagla` çağırır.
  Yeni komut gerekirse komutun sahibi listenin SONUNA kendi kaydını ekler (id, kısayol ve katlanmış ad tekil kalmalı;
  `sozlesme_komut.cpp` denetler). Kayıt silmek ya da id değiştirmek yasaktır.
- `kaynak/cekirdek/ayarlar.h` (S): her paket yalnız kendi grubuna alan ekler (`grafik`, `arayuz` → C; `dosya` → D;
  `motor` → A; `cekirdek` → B); JSON okuma / yazma satırları D'nin `ayarlar.cpp`'sindedir, ekleyen paket aynı işlemede ekler.
- `kaynak/secenekler.h` (S): F1 bayraklarının hepsi tanımlıdır; yeni bayrak bir alan + `Ayristir` satırı + `ana.cpp`
  yardım yorumudur (A'ya bildirilir).
- `kaynak/uygulama.cpp` (C): Faz 0 ana döngüsü. Motor (A) ve dosya komutları (D) buraya **dokunmadan** bağlanır: A
  `MotorModuluKur`'da `Hizmetler::motor`'u değiştirir, D `dosya.*` komutlarını bağlar. Sığdır, motor durumu ve kare işleri
  kabuktan okunur.
- `docs/` (web sürümü): yalnız eklemeli değişiklik (D35). `docs/web_kopru.py` A'nındır; `docs/ifc_disari.js`'e `kesitCoz`
  eki Faz 2'dir (B). Kök motor modülleri F1'de değişmez.
- TASARIM.md: §20 (mimari) entegratör, §21 (.op4 biçimi) D, §22 (komut çerçevesi) C yazar; bölüm başlığı dışında
  birbirinin bölümüne dokunulmaz.

### 24.4 Sözleşme değişiklik kuralı

- S dosyalarında **yalnız eklemeli** değişiklik serbesttir: yeni yapı alanı (varsayılanlı), yeni sanal olmayan yardımcı,
  yeni enum değeri (sona), yeni ileti türü (bilinmeyen tür hata değildir), yeni komut / öznitelik / kod kaydı.
- Mevcut bir imzayı, alan anlamını, enum değerini, kod tablosu değerini, ileti alan sırasını değiştirmek ya da silmek
  **entegratör onayı** ister ve aynı işlemede bütün kullanıcı paketlerin derlemesini ve sınamalarını yeşil tutmalıdır.
- Her S değişikliği §24.6 günlüğüne bir satır ekler. Sözleşme sınamaları (`sozlesme_*.cpp`, `sozlesme.test.js`,
  `test_protokol.py`, `testler/test_op4_sozlesme.py`) yalnız güçlendirilebilir; gevşetilmez.
- Taslak bir uygulamayı gerçeğiyle değiştirmek sözleşme değişikliği değildir (ör. B'nin `gecici_cekirdek.cpp`'yi silip QuickJS
  çekirdeğini koyması). Taslak listeleri (`Op4Ops.TASLAK`, `Op4Cekirdek.TASLAK`) uygulandıkça kısalır.

### 24.5 İtme ve birleştirme

Bütün paketler aynı dala iter (`claude/dreamy-franklin-nvl0oo`). Her itmeden önce `git fetch origin && git merge --no-edit
origin/claude/dreamy-franklin-nvl0oo`; zorla itme yok. Sahiplik kuralı nedeniyle birleştirme çatışması yalnız ortak
dosyalarda beklenir; çatışmada dosyanın sahibinin sürümü esas alınır, diğer paketin değişikliği kendi bloğuna taşınır.
Her paket kendi işlemesinden sonra Linux (`cekirdek-linux`) ve Windows (`windows`) işlerinin yeşil olduğunu doğrular.

### 24.6 Sözleşme değişiklik günlüğü

| Tarih | Kod | Değişiklik | Paket |
|---|---|---|---|
| 2026-10-30 | S1–S27 | İlk sürüm: başlıklar, taslaklar, kabuk, komut kataloğu (37 komut), öznitelik şeması (23 alan), sahne kodları, tel protokolü ve ortak vektörler, sahiplik tablosu | S |

### 24.7 Paket kabul denetimleri

Her denetim bir sınamaya ya da CI ölçümüne bağlıdır; "nerede" sütunu onu gösterir. Bir paket, kendi satırlarının tamamı
yeşilken teslim eder. Sayısal eşikler §6.13, §7.4, §8.4 ve §9.5'tendir.

**A — derleme-motor (1.1, 1.2)**

| # | Denetim | Nerede |
|---|---|---|
| A1 | `op4_cekirdek`, `op4_cekirdek_js` ve sınamaları Linux'ta clang ile `-Werror` derlenir; `ctest` yeşil | `cekirdek-linux` işi |
| A2 | `CMakePresets.json`: win-surum, win-hata, linux-cekirdek, linux-cekirdek-asan; ASan + UBSan ön ayarıyla `ctest` yeşil | `cekirdek-linux` |
| A3 | Python 3.13 ve 3.14 ile `pytest op4/testler/python` yeşil | `cekirdek-linux` (matris) |
| A4 | Gölgelendiriciler derlemede FXC ile SM 5.1'e derlenir, `GomuluGolgelendirici` dolu döner; ekran testi çalışma anı derlemesi olmadan geçer ve `OP4OLCUM` aygıt süresi açılıştan 40 ms'den fazla kısalır | Windows, `--test-ekran` günlüğü |
| A5 | `OP4_UYARI_HATA` varsayılanı ON: MSVC `/W4 /WX`, bütün hedefler uyarısız | Windows derleme adımı |
| A6 | `op4motor.exe` (≈ 150 satır): tutamaç temizliği, dosya denetimi (eksikte okunur ileti, çıkış 2), BLAS iş parçacığı ayarı (ana çekirdek − 1, yardımcı 1), `Py_Main(-X utf8 -B -m op4_sunucu …)` | Windows, kurulu programla motor testi |
| A7 | `op4_sunucu.py`: stdout / stderr ve fd 1–2 günlüğe; `print` protokolü bozmaz; `hazir` iletisi; ana iş parçacığında sıralı `calistir`; okuyucu iş parçacığında `iptal` (`interrupt_main`) ve `kapat`; Y1–Y4 | `op4/testler/python/test_sunucu.py` (Linux) |
| A8 | C++ istemcisi (Win32 + POSIX) `python3 -m op4_sunucu`'ya karşı: istek / yanıt, kuyruktaki ve çalışan isteğin iptali, 5 s'de yanıt yoksa sonlandırıp yeniden başlatma (bekleyenlere `motor_yeniden`), sunucu çökmesi (`motor_coktu`), 50 MB yanıt, eski id'li yanıtın atılması | `op4/testler/cekirdek/motor_*.cpp` (ctest, Linux ve Windows) |
| A9 | `docs/web_kopru.py` eklemeli işlemler: `bina_coz` `anlat:false` (veri `anlat:true` ile 1e-9 içinde aynı, `bloklar: []`), `bina_kimlik`, KeyboardInterrupt → `hata_turu: "iptal"`, `ayarlar.sd_siniri`; mevcut `pytest testler` ve node testleri değişmeden yeşil | `testler/test_web_kopru_op4.py` |
| A10 | `MotorModuluKur` süreç istemcisini bağlar; `--test-motor` soğuk açılış ≤ 1 s (hazır), `--test-pencere` motor hazır; durum çubuğu "Hesap motoru" öğesi; `motor.yeniden_baslat` komutu | Windows CI günlüğü, `OP4OLCUM senaryo=motor` |
| A11 | Paket: `op4motor.exe`, `motor/op4_sunucu.py`, `motor/op4_protokol.py` kurulumda; `C:\op4 dene ŞĞİı` yoluna kurulu programla motor testi geçer | Windows kurulum adımı |

**B — model-cekirdegi (1.3)**

| # | Denetim | Nerede |
|---|---|---|
| B1 | quickjs-ng iki haftadan eski sürüme sabit (`cmake/bagimlilik_quickjs.cmake`, işleme özeti); MSVC ve clang ile uyarısız | Linux + Windows derleme |
| B2 | Ön yükleme: `self = globalThis`, `window` / `document` tanımsız, `structuredClone` yedeği, `console` → günlük, sınamada deterministik `Date.now`; `docs/` modülleri değişmeden yüklenir; açılış derleme süresi `OP4OLCUM cekirdek_derleme_ms` (beklenen ≈ 50 ms) | ctest `cekirdek_js_*`, Windows günlüğü |
| B3 | `op4_ops.js`: `TASLAK` boş; `katUyeligi` (§10.2), `kullanimYeri` (§10.3), `profilAdiNormal` (§10.4; `testler/ortak/profil_adlari.json` vektörlerinin hepsi), `oznitelikCikar` (23 Faz 1 alanı), `sahneCikar`, `sonucEsle` node sınamalarıyla | `node --test op4/testler/js/*.test.js` |
| B4 | Cephe `op4_cekirdek.js`: `TASLAK` boş; `uygula` beyaz listesi (`hizliAks`, `aksSihirbazi`, `baslikDegistir`, `genellestir`), geri al / yinele (100 adım, 512 MB), C1 `gecis_onayi`, kanonik `metin()` (aynı model → aynı bayt) | node |
| B5 | C++ köprüsü: `ModelCekirdegiOlustur` QuickJS çekirdeğini döndürür; `Sahne()` 9 şablonun her biri için düğüm / çubuk / panel sayıları JS ile aynı; tipli diziler kopyasız | ctest `cekirdek_js_*` |
| B6 | Eşdeğerlik derlemi (`op4/testler/derlem/`, `derlem_uret.js`): mevcut node test girdileri + 9 şablon; QuickJS çıktıları node ile sayılarda bağıl 1e-12, diğer alanlar birebir; Linux ve Windows | ctest |
| B7 | Başarım: `celik-sanayi-4hol` ve sentetik 5 bin / 20 bin çubukta `uygula` ≤ 100 / ≤ 300 ms | ctest, `OP4OLCUM senaryo=cekirdek` |
| B8 | `duzenle.geri_al`, `duzenle.yinele`, `model.denetle` bağlı; GeriAlBilgisi menüde ad gösterir | ctest (kabuk) |

**C — arayuz-goruntu (1.4)**

| # | Denetim | Nerede |
|---|---|---|
| C1 | Şerit, menüler, hızlı erişim ve kısayollar `komutlar.json`'dan üretilir; bağsız komut soluk ve nedeni ipucunda; F, K, G tek harf kısayolları kalkar (Shift+F, Ctrl+Shift+K, F7) | senaryo `arayuz_serit`, ekran görüntüsü |
| C2 | Komut satırı: önek ve alt dizi tamamlama, Türkçe katlama, geçmiş, boşta Enter son komutu yineler, bilinmeyende yakın komut önerisi | ctest `arayuz_*` + senaryo |
| C3 | Açılış: "Adsız 1", Z = 0 çalışma ızgarası, Başlangıç paneli (Boş model, Hızlı aks, 9 şablon, Aç, Son dosyalar); "Açılışta göster" ayarı | senaryo `arayuz_baslangic`, PNG |
| C4 | Çubuk görünümü: sabit 2 px (seçili 3 px), tür paleti, mafsal / serbest düğüm / mesnet simgeleri; `OrnekSahneAnlik` ve şablon sahneleri çizilir | WARP PNG (altın) |
| C5 | Gezinme K1 (300 adım ≤ 0,5 px), K3, K4 Linux'ta `kamera_*` sınamalarıyla; Windows `--test-pencere` kayma ≤ 0,5 px; görünüm küpü, Alt+1…4, PgUp/PgDn | ctest + `--test-pencere` |
| C6 | BVH: üzerine gelme ≤ 4 px (DPI ölçekli), 100 bin elemanda ≤ 1 ms; pencere seçimi (soldan sağa tam içinde, sağdan sola değen); Ctrl / Shift kipleri; vurgu | ctest `secme_*`, `OP4OLCUM` |
| C7 | Model gezgini: kat → alt tür → kullanım yeri, sayılarla; tık seçer, Ctrl ekler; Özellikler paneli salt okunur, çoklu seçimde "(çeşitli)" | ctest `arayuz_gezgin`, senaryo |
| C8 | `NvOptimusEnablement` ve `AmdPowerXpressRequestHighPerformance` dışa aktarılır; Ayarlar › Grafik bağdaştırıcı ve MSAA seçimi; WARP'ta "yazılım işleyici" uyarısı | Windows (dumpbin / günlük) |
| C9 | `--senaryo` yürütücüsü: komut, olay, bekle, çek adımları, deterministik saat; CI senaryoları PNG ve `OP4OLCUM` basar | Windows CI |
| C10 | Hata ayıklama katmanında bütün senaryolarda 0 hata iletisi; `gorunum/gorunum.json` katkısı (kameralar .op4'te saklanır) | Windows CI |

**D — dosya-cozum (1.5, 1.6)**

| # | Denetim | Nerede |
|---|---|---|
| D1 | `.op4` ZIP (miniz): `mimetype` ilk ve sıkıştırmasız, manifest, katkılarla gidiş-dönüş bayt eşit (aynı yürütücü); bilinmeyen girdiler korunur; daha yeni `bicim_surumu` salt okunur açılır | ctest `dosya_*` (Linux) |
| D2 | Atomik yazma: geçici dosya + boşaltma + ReplaceFileW / MoveFileExW, paylaşım ihlalinde 5 × 100 ms; yarım yazmada hedef bozulmaz; Türkçe karakterli yol | ctest + Windows senaryo |
| D3 | Eski biçimler: Faz 0 JSON `.op4` (kamera alınır, model boş), `.matris`, bina `.json`; `BicimSapta` içeriğe bakar | ctest `dosya_*` |
| D4 | Kirli işareti başlıkta "•"; kapanışta Kaydet / Kaydetme / Vazgeç (`kapatmaOnayi`); otomatik kayıt 5 dk (1–30), kurtarma klasörü, açılışta Kurtar / Sil / Sonra; temiz kapanışta kurtarma silinir | senaryo `dosya_kirli`, `dosya_kurtarma` |
| D5 | Son dosyalar (10, atlama listesi), `.op4` ilişkilendirmesi, tek örnek borusu `\\.\pipe\OpusFortis.op4.<SID>` (ikinci açılış öne getirir; `--yeni-ornek`), çökme dökümü `cokme\` | Windows senaryo / kurulum adımı |
| D6 | 9 şablon `op4/veri/sablonlar/` (+ `dizin.json`: ad, başlık, açıklama, dosya) motor hazır olmadan açılır; döküm aracı `araclar/sablon_dok.py` ve "döküm güncel" sınaması | pytest + senaryo `dosya_sablon` |
| D7 | F5: `bina_coz` (`anlat:false`) eşzamansız, arayüz donmaz; ilerleme ve iptal; sonuç özeti paneli; D/C renkleri (`DcRengi`, web ölçeği); model değişince "Sonuçlar eski" | senaryo `cozum_f5`, PNG |
| D8 | D/C değerleri Linux pytest'teki doğrudan `web_kopru` çözümüyle bağıl ≤ 1e-9 (`betonarme-3kat-3x3`, `celik-sanayi-4hol`); süreler `OP4OLCUM senaryo=cozum` | Windows senaryo + pytest |
| D9 | `.op4` açılışında `sonuc/` varsa `bina_kimlik` ile eşleşirse D/C renkleri hemen görünür | senaryo `cozum_acilis` |
| D10 | IFC dışa aktarma (`Ctrl+E`): `ifc_disari.js` QuickJS'te; `uygulama = {ad:"op4", surum, firma:"Opus Fortis"}`; GlobalId'ler belirlenimci, sınamada zaman damgası sabit; aynı model iki kez → aynı bayt | senaryo `dosya_ifc`, ctest |

**1.7 — Faz 1 bütün kabulü (entegratör)**
- Kurulu `op4-setup-0.1.0.exe` ile: açılış "Adsız 1" → şablondan yeni → F5 → D/C renkleri → kaydet → kapat → aç → renkler
  `bina_kimlik` ile geri gelir → IFC dışa aktar; bütün adımlar tek senaryoda, WARP ve hata ayıklama katmanında 0 hata.
- `--oz-sinama` kurulu programda geçer (motor, çekirdek, şablon, kaydet / aç, ekran).
- Gezinme bütçeleri ve K1–K4 korunur; etkileşimli boş çalışma alanı ≤ 1,5 s (`OP4OLCUM`).
- `pytest testler`, `node --test testler/js/*.test.js`, bekçi testi, `cekirdek-linux` ve `windows` işleri yeşil.
- TASARIM §20–§22 yazılmış; `op4/README.md` güncel; §24.2 "Taslak" sütununda taslak kalmamış.
