# op4 — iş takibi (yapılan, yapılacak, eksikler, iyileştirme)

Yaşayan belge. Her oturumun başında okunur, iş bittikçe güncellenir. Bağlayıcı belirtim `MIMARI.md`; bu dosya yalnız
durum ve sıra tutar. Tarihler 2026. Son güncelleme: **31.10, op4 0.1.0 teslim edildi, Faz 2/3/6/7b ve sihirbaz başladı.**

---

## 0. Nasıl çalışıyoruz (yeni oturum için)

- **Dal:** `claude/dreamy-franklin-nvl0oo` (bütünleştirme). Başka dala itme yok. `main` 50+ işleme geride (d5281fd,
  PR #6); main'e PR kullanıcı isteyince açılır.
- **Paketler:** her iş kendi worktree'sinde ve dalında yürür (`/home/user/wt/<paket>`, dal `op4-<paket>`), itmez;
  bütünleştirici `git merge --no-ff` ile alır, Linux + MinGW + sınamalar yeşilse iter, Windows CI'ı izler.
- **Paket brifi şablonu:** ortak kurallar (sahiplik, doğrulama komutları, MSVC tuzakları, işleme ileti sonu) her pakete
  verilir; en son sürümü oturum karalama klasöründeydi, gerekirse bu bölümden yeniden yazılır.
- **Doğrulama:** `cmake -S op4 --preset linux-cekirdek` (+ `-asan`), ctest; MinGW `op4/araclar/mingw.cmake`
  `-DOP4_UYARI_HATA=ON`; `node --test op4/testler/js testler/js`; pytest bekçi + sözleşme + araçlar + web_kopru_op4 +
  op4/testler/python. Motor değiştiyse ilgili `testler/test_*.py` ve 9 şablonda bayt bayt aynılık.
- **Bekçiler:** `testler/test_program_adi_yok.py` (başka yazılım ürün adı yazılmaz; `git add`'den sonra çalıştır),
  `testler/test_op4_sozlesme.py` (her op4 dosyasının §24.3'te sahibi olmalı).
- **CI okuma:** iş günlüğü API'den en çok son ~5000 satır gelir. PNG'ler günlüğe base64 basılır
  (`op4/araclar/gunluk_png_coz.py`). Başarısız ekran testinin nedeni ek açıklamaya ve günlük sonuna yazılır.
  Yapıt (artifact) indirme: `actions_get download_workflow_run_artifact` → blob URL (ortam ağ izninde
  `*.blob.core.windows.net` açıldı, 31.10).
- **Sürüm:** `op4/CMakeLists.txt` `OP4_TABAN_SURUM` (şu an 0.1.0) ya da `op4-vX.Y.Z` etiketi. Etiket itmek izin
  sistemince engellendi ("herkese açık yüzey"); Release için kullanıcı onayı / izin kuralı gerekir.
- **MSVC tuzakları:** C4244 (int→float örtük), C4701 (ilk değersiz yerel), C2220 uyarı=hata. D3D12 okuma tamponunda son
  satır doldurulmaz (e0738a0). Windows'ta `core.autocrlf` → `.gitattributes` LF kuralları. `python -I` PYTHONUTF8'i yok
  sayar → `-X utf8`.

---

## 1. Yapılanlar

### 1.1 op4 0.1.0 (teslim: 31.10, `op4-setup-0.1.0.exe`, CI koşusu 41191245508, işleme e0738a0, tamamen yeşil)
- **Altyapı (A):** CMake ön ayarları, MSVC /W4 /WX, FXC SM 5.1 gömülü gölgelendiriciler, `op4motor.exe` ayrı süreç
  (CPython 3.14 gömülü, numpy/sympy karmalı), iptal + yeniden başlatma, Inno Setup kurulum, Türkçe yolla sessiz kurulum
  sınaması.
- **Model çekirdeği (B):** QuickJS-ng; `docs/` saf modülleri değişmeden; 9 şablon eşdeğerlik derlemi (1292 kayıt, 0 fark);
  geri al / yinele; `icerikDegisti` (S11).
- **Arayüz (C):** Atölye·Modern (Kobalt; Petrol/Grafit seçenek), şerit (komutlar.json), model ağacı, Özellikler (salt
  okunur), rıhtım, komut satırı (Türkçe katlama), kat kapsamlı durum çubuğu, Ayarlar (Program/Görüntü/Dil, arama,
  varsayılana dön), TR/EN, Kemer Çizgisi açılış ekranı (açık varsayılan, koyu seçilebilir), gezinme (sol kaydır,
  Shift+sol döndür, imlece yakınlaşma), BVH seçme, Başlangıç paneli, kısayollar §25.1, `--senaryo` ekran sınamaları.
- **Yazı:** Noto Sans SemiCondensed (statik 400–700, op4.exe'ye gömülü), imgui_freetype LightHinting|ForceAutoHint,
  piksel yakalama; Küçük/Orta/Büyük yazı boyutu; en küçük pencere 1024×640.
- **Dosya ve çözüm (D):** `.op4` ZIP (miniz), eski biçimler, atomik yazma, otomatik kayıt + kurtarma, son dosyalar, belge
  başına tek örnek, F5 eşzamansız çözüm + iptal, D/C renkleri, sonuç karması ile yeniden açılışta renkler, IFC dışa
  aktarma (uygulama adı "op4 · Opus Fortis"), ayarların anında kaydı.
- **Motor ekleri:** sahaya özel spektrum (TBDY 2.4.1.2 %90 alt sınır; ZF çözülür), `bina_spektrum`, DTS/BYS/T_L tabloları,
  hareketli yük azaltması (TS 498 Çizelge 7), karma yapı (malzemeye göre birleşim kümesi; doğrultuya göre sistem; κ ve C_h
  kat başına; C_t doğrultu başına; yükseklik boyunca en küçük R).
- **Tasarım belgeleri:** `op4/tasarim/` Atölye·Modern, harman Seç & Süz, Yönetmelik sihirbazı, ARAYUZ_ILKELERI.

### 1.2 Web uygulaması (matris-ogren, GitHub Pages, main)
- Yapı/Bina revizyonu tamamlandı ve yayında (PR #5, #6). op4 için yapılan motor ekleri bu dalda; web arayüzü yeni
  anahtarları henüz göstermiyor (bkz. §3.4).

---

## 2. Sürmekte olan (31.10 başlatıldı; her biri ayrı dal)

| Paket | Dal / worktree | Kapsam | Durum |
|---|---|---|---|
| Faz 3 seçim | `op4-faz3-secim` · `/home/user/wt/op4-faz3` | Özellikler düzenleme, kat/kullanım seçimi, Seç & Süz (harman), yük/mesnet atama | sürüyor |
| Faz 2 görüntü | `op4-faz2-goruntu` · `/home/user/wt/op4-faz2` | Gerçek kesitler (tüm aileler, temeller), çubuk/kesit, LOD, görüntü ağı ±%2 | sürüyor |
| Sihirbaz | `op4-sihirbaz` · `/home/user/wt/op4-sihirbaz` | 8 adımlı Yönetmelik sihirbazı, `proje/yonetmelik.json`, `.op4ys` şablonları | sürüyor |
| Faz 6 IFC | `op4-faz6-ifc` · `/home/user/wt/op4-faz6` | `ifc_iceri.py`, eşleme, rapor penceresi, isteğe bağlı bileşen | sürüyor |
| Faz 7b ağ | `op4-faz7-ag` · `/home/user/wt/op4-faz7` | Analiz ağı ±%2 (radye, mütemadi, vute, kren, istasyon, Navier), Ağ raporu | sürüyor |

Worktree'ler kapsayıcıya bağlıdır; oturum kapanırsa dallar itilmemiş olabilir — önce `git branch` / worktree listesine bak.

---

## 3. Yapılacaklar

### 3.1 Faz sırası (MIMARI §22)
- [ ] **Faz 2** gerçek kesitler + görüntü ağı ±%2 → `0.2.0` (sürüyor)
- [ ] **Faz 3** Seç & Süz, kat/kullanım seçimi, atamalar, özellik düzenleme → `0.3.0` (sürüyor)
- [ ] **Faz 4** çizim ve düzenleme komutları, yakalama, çalışma düzlemi, çok katlı çizim (§12) → `0.4.0`
      — Faz 3 birleşince başlar (aynı dosyalar, seçim altyapısına bağlı)
- [ ] **Faz 5** analiz, tasarım ve çıktılar op4'te: sonuç diyagramları (§6.10), tablolar, rapor, Belge penceresi
      (WebView2, §15), motor başarımı ve ölçek (seyrek çözücü) → `0.5.0`
- [ ] **Faz 6** IFC içe aktarma → `0.6.0` (sürüyor)
- [ ] **Faz 7a** genel modelde radye/mütemadi — web çalışmasında yapıldığı düşünülüyor; Faz 7b paketi doğrulayacak
- [ ] **Faz 7b** analiz ağı ±%2 → `0.7.0` (sürüyor)
- [ ] **Faz 8** Sonlu eleman, Matris hesaplayıcı, Dersler op4'te; Electron sürümü kaldırılır → `1.0.0`
- [ ] Yönetmelik sihirbazı (sürüyor; Faz sırası dışı, kullanıcı isteği)

### 3.2 Kullanıcının 10 isteği — durum
| # | İstek | Durum |
|---|---|---|
| 1 | Temel çizim komutları | Faz 4 (bekliyor) |
| 2 | Kat / kullanım yeri bazlı seçim, yük ve mesnet ataması | Faz 3 (sürüyor); kat öznitelikleri ve kapsam anahtarı 0.1.0'da |
| 3 | Select & Filter (her öznitelikle) | Faz 3 (sürüyor; harman tasarım onaylı) |
| 4 | Boş çalışma sayfasıyla başla, şablonlar kalsın | **Yapıldı** (0.1.0) |
| 5 | Gerçek kesit görünümü, çubuk/kesit seçmeli | Faz 2 (sürüyor) |
| 6 | Kaydet / Farklı kaydet / Aç | **Yapıldı** (0.1.0) |
| 7 | IFC içe aktarma | Faz 6 (sürüyor); dışa aktarma 0.1.0'da |
| 8 | Kaydırma titremesi yok; sol kaydır, Shift+sol döndür | **Yapıldı** (0.1.0; kayma < 0,5 px CI'da) |
| 9 | Yüksek kalite, DirectX 12, GPU | DX12 0.1.0'da; kalite/LOD Faz 2; **gerçek GPU'da hiç sınanmadı** (yalnız WARP) |
| 10 | Ağ ±%2 (analiz + görüntü) | Görüntü: Faz 2; analiz: Faz 7b (ikisi de sürüyor) |
| — | Setup + açılış ekranı + her şey op4'te | Kurulum ve açılış yapıldı; "her şey op4'te" Faz 5 ve 8 ile tamamlanır |

### 3.3 Kullanıcı kararı bekleyenler
- **GitHub Release:** `op4-v0.1.0` etiketi itilemedi (izin). Kullanıcı izin kuralı ekleyecek mi, kendisi mi yapacak?
- **MIMARI §23** açık kararları:
  - Belge penceresi (a/b/c)
  - Serbest çizim
  - Pencere seçimi Ctrl+sol
  - F tuşları
  - Kod imzalama sertifikası (SmartScreen uyarısı)
  - Inno Setup ticari lisans doğrulaması
  - IFC bileşeni boyutu (+120 MB)
  - Web sürümü yayında kalsın mı
  - Büyük modeller için scipy (+90 MB)
  - Plak/kabuk FE kapsam dışı
- **Ayarlar:** "Arayüz ölçeği" ile "Yazı boyutu" çakışıyor (ikisi de ölçeği büyütüyor) — birini kaldırma önerisi.
- **Seç & Süz açıkları (secsuz.md §20/3–6):**
  - Ctrl+Shift+I / Ctrl+K
  - Panel genişliği 400 px
  - Kat çipi varsayılanı
  - Süzgeç kaydında kat ölçütü
- **Sihirbaz açıkları (sihirbaz.md §12):**
  - DD-1/DD-4 yalnız rapor
  - Harita raporu biçimi
  - Ön geometri H_N
  - Rijit bodrum
  - P-Δ bilgi satırı
  - Firma şablon klasörü (ağ)
  - Mevcut döşemelere uygulama varsayılanı
  - Varsayılan kaplama (seramik doğrulanmamış)
  - Birim sistemi yalnız gösterim mi
- **Yerel yapay zekâ yardımcısı:** öneri yazıldı (ayrı süreç, isteğe bağlı bileşen, yalnız komut önerir, hesap
  yapmaz). Kullanıcı faz olarak eklenmesini onaylarsa MIMARI'ye yeni bölüm.

### 3.4 Web uygulaması (docs/) borçları
- [ ] `docs/bina.js` model normalleştiricisi yeni anahtarları siliyor (`deprem.ozel_spektrum`, `tasiyici_x/y`,
      `tasiyici_bolgeleri`, `Ct_x/y`, `kombinasyon_kumeleri`, `yuk_durumlari.Q.azaltma`) ve ZF'yi ZC yapıyor. op4 çekirdeği
      korur (denendi); web arayüzü düzeltilmeli + giriş alanları.
- [ ] `bysHesapla` DTS 3 ve 4'ü tek sütunda topluyor (motor üç sütun).
- [ ] Model yüklenirken `periyot: "otomatik"` sessizce `"ampirik"` oluyor.
- [ ] Isı haritası ve eleman bilgisi karma yapıda birincil birleşim kümesini kullanıyor.
- [ ] Web sürümünün geleceği (§23.8) kararına bağlı.

---

## 4. Bilinen eksikler (0.1.0 itibarıyla)

### Arayüz (C)
- Çift aralığı (kerning) tablosu yok (ImGui uygulamıyor).
- Şerit özelleştirme, grup başlatıcıları (↘), kısayol yakalama tablosu, Ayarlar içe/dışa aktarma yok.
- Kesit görünümünde seçim halesi kaplama yaklaşımı (ID tamponu kenar bulanıklığı değil).
- Açılış ekranında durum metni kaydırma animasyonu basit; "hareketi azalt" erişilebilirlik seçeneği yok.
- Tek gerçek GPU sınaması yok; ekranlar WARP'ta doğrulandı. Gerçek kartta ilk çalıştırma kullanıcıda.

### Dosya ve çözüm (D)
- Kaydetme ve otomatik kayıt UI iş parçacığında (50 MB sonuçta ≈ 1 s donma).
- Kapatma onayı yerel TaskDialog (Atölye biçiminde değil; soru sözleşmesi eşzamanlı).
- D/C renk ölçeği web 4 bantlı (S19); Atölye tasarımı 5 bantlı → karar.
- `testler/senaryolar/dosya_*`, `cozum_*` senaryo dosyaları yazılmadı.
- `Hizmetler::KareIsiEkle`'nin kaldırma karşılığı yok (S22 `KareIsiKaldir`) — modüller erken kapanırsa gerekir.

### Altyapı (A)
- Gölgelendirici kazanç ölçütü (A4, > 40 ms) WARP'ta tutmuyor; yalnız uyarı. Ölçüt "≥ 25 ms" ya da soğuk açılış.
- `win-hata` (Debug) ön ayarı CI'da derlenmiyor.

### Motor — doğrulanamayan kurallar (`dogrulandi: false`, sonuçta uyarı)
- Resmî metinlere (Resmî Gazete, AFAD) bu ortamdan erişilemedi. Kullanıcı / mühendis doğrulaması gereken:
  - Özel spektrumda doğrusal ara değer ve son T sonrası S_ae·T_son/T uzatması.
  - Özel spektrumda S_DS/S_D1 türetimi (verilmezse).
  - ZF'de %90 alt sınırın ZE standart spektrumuna göre alınması; ZF'de DD-3 tablosu yoksa λ = 1.
  - Hareketli yük azaltmasının deprem birleşimlerinde uygulanmaması; eşit olmayan kat yüklerinde düzeltme.
  - Karma yapı: κ/C_h kat başına, C_t doğrultu başına (kullanıcı kararı 31.10); yükseklik boyunca en küçük R kuralı;
    TBDY md. 4.3.6 uygulanmıyor; perdeli doğrultuda C_t = 0,07 üst sınır (A_t yok → `Ct_x/Ct_y` elle).
- Kaplama "sap-seramik-siva" birim ağırlığı doğrulanmadı; TS 498 Ek 1 kar bölgeleri OCR aktarımı; TS EN 1991-1-3 μ₁, C_e.

### Yayın
- Kod imzası yok → SmartScreen uyarısı.
- Herkese açık GitHub Release yok (§3.3).

---

## 5. İyileştirme (optimizasyon) görevleri

| # | Konu | Ölçüm (son) | Hedef |
|---|---|---|---|
| O1 | Model çekirdeği geometrik işlemleri (aksSihirbazUygula yolu) | 5k çubuk: aks 451 ms, 20k: 1687 ms (Windows) | ≤ 100 ms / 300 ms bütçe (B7) |
| O2 | 20k çubuk model yükleme | 1169 ms (Windows) | < 500 ms |
| O3 | Kaydetme / otomatik kayıt arka plana | ≈ 1 s / 50 MB UI donması | donma yok |
| O4 | Motor başarımı (MIMARI §8.6 madde 8) | — | `celik-sanayi-4hol` anlatımsız çözüm ≥ 2×, 1e-12 eşdeğerlik |
| O5 | Büyük modeller seyrek çözücü (scipy, isteğe bağlı) | ≈ 6000 SD sınırı | gerçek bina IFC'leri |
| O6 | Görüntü: örnekleme, LOD, kare süresi | WARP pencere ort. 40 ms/kare | gerçek GPU'da 60 fps, 20k eleman |
| O7 | Motor açılışı | soğuk 479 ms / ılık 543 ms (CI) | ≤ 1000 ms (tutuyor), izle |
| O8 | Kurulum boyutu | paket 114 MB, setup 33 MB | IFC (+120) ve scipy (+90) isteğe bağlı kalsın |
| O9 | Gölgelendirici gömülü kazanç | çalışma anı 37–48 ms → 0,3 ms | tamam; ölçütü güncelle |
| O10 | CI günlüğü (PNG dökümü kuyruğu dolduruyor) | ~12 600 satır | ekran dökümlerini ayrı işe / küçült |

---

## 6. Başka depo
- **tokat-214-215-218-su-atiksu:** etiket çakışması önleme yapıldı ve itildi; kalan adımlar yalnız Windows'ta (DWG
  üretimi, teslim klasörü D:\). Bulutta yapılacak iş yok. Kural: kaynak klasör salt okunur; veri yalnız
  `D:\TOKAT SANAYİ\09.05.2025\5-ALTYAPI\mekanik revize`; Word sürecini sonlandırma.

---

## 7. Güncelleme günlüğü
| Tarih | Ne değişti |
|---|---|
| 31.10 | Dosya oluşturuldu: 0.1.0 teslimi, Faz 2/3/6/7b + sihirbaz paketleri başladı |
