# op4 — oturum rehberi (Claude Code bu dosyayı her oturumda okur)

**op4**, Opus Fortis'in yerel Windows yapı analizi ve tasarım programı: C++20 + Direct3D 12 + Dear ImGui arayüz,
ayrı süreçte gömülü CPython hesap motoru (`op4motor.exe`), QuickJS model çekirdeği, Inno Setup kurulum. Depo aynı
zamanda motorun ve eski web uygulamasının (Matris Öğren, `docs/`) kaynağını taşır; op4 bunları paketler.

Kullanıcı Türkçe konuşur; bütün yanıtlar, işleme iletileri, kod yorumları ve tanımlayıcılar Türkçedir (tanımlayıcılar
ASCII). Kullanıcı birden çok cihazdan, farklı oturumlarda çalışır; süreklilik bu dosya ve `op4/IS_TAKIP.md` ile sağlanır.

## Oturum başında (her seferinde)
1. `op4/IS_TAKIP.md`'yi oku: yapılanlar, **sürmekte olan paketler**, kullanıcı kararı bekleyenler, eksikler,
   iyileştirme görevleri.
2. `git fetch --all`; `main` ile açık dalları (özellikle `op4-*` paket dalları) ve açık PR'ları gözden geçir.
3. Kullanıcıya 3–5 satırlık durum özeti ver, sonra işe başla. Kullanıcı "devam et" derse IS_TAKIP'teki sıradaki işi al.

## Oturum sonunda (ya da büyük bir adım bitince)
- `op4/IS_TAKIP.md`'yi güncelle: yapılanlar, sürmekte olanlar (dal + durum), yeni eksikler, günlük satırı.
- İşle ve **it**. Kapsayıcı geçicidir; itilmeyen iş kaybolur. Paket dallarını da it.

## Dal düzeni (çoklu cihaz)
- `main`: Windows CI'ı yeşil, kurulabilir sürüm. Doğrudan yazılmaz; PR ile birleşir (kullanıcı onayıyla).
- Oturum dalı: oturumun verdiği `claude/...` dalı. Bütünleştirme orada yapılır; iş bitince `main`'e PR.
- Paket dalları: büyük işler `op4-<paket>` dallarında (yerelde `git worktree add /home/user/wt/<paket>`) yürür;
  bütünleştirici `git merge --no-ff` ile alır. Paket dalları da itilir ki başka cihazdan devam edilebilsin.
- Aynı paketi iki oturum aynı anda sürmez: IS_TAKIP "Sürmekte olan" tablosunda paketin sahibi (oturum / tarih) yazılır.

## Bağlayıcı belgeler
- `op4/MIMARI.md` — mimari, faz planı (§22), paket sözleşmeleri S1–S27 (§24; sahiplik §24.3, değişiklik kuralı §24.4,
  günlük §24.6), kullanıcı kararları (§25, §25.1).
- `op4/tasarim/` — onaylı arayüz tasarımları (Atölye·Modern, Seç & Süz, Yönetmelik sihirbazı).
- `TASARIM.md` (§20 mimari, §21 .op4 biçimi), `KULLANIM.md`.

## Değişmez kurallar
- Başka yazılım ürünlerinin adlarını hiçbir izlenen dosyaya yazma; `testler/test_program_adi_yok.py` bekçisi
  (`git add`'den SONRA çalıştır).
- Her op4 dosyasının MIMARI §24.3'te sahibi olmalı (`testler/test_op4_sozlesme.py`).
- Hesap motorunda yeni anahtar vermeyen modellerin çıktıları **bayt bayt aynı** kalır (9 şablon). Yönetmelik kuralı
  madde numarasıyla uygulanır; doğrulanamayan kural `dogrulandi: false` + sonuç uyarısı ile işaretlenir, uydurulmaz.
- Sözleşme (S*) değişiklikleri yalnız eklemeli + §24.6 satırı. Her model değişikliği tek geri al adımı.
- Arayüz metinleri yerelleştirme tablosundan, TR + EN. Renk / ölçü elle yazılmaz (`op4/kaynak/arayuz/tema.h`).
- Herkese açık bir şey (Release etiketi, yayın) kullanıcı onayı olmadan yapılmaz.

## Doğrulama
```bash
cmake -S op4 --preset linux-cekirdek -B /home/user/wt/yapi && cmake --build /home/user/wt/yapi -j8 && (cd /home/user/wt/yapi && ctest --output-on-failure)
cmake -S op4 -B /home/user/wt/yapi-mingw -G Ninja -DCMAKE_TOOLCHAIN_FILE=$PWD/op4/araclar/mingw.cmake -DOP4_UYARI_HATA=ON && cmake --build /home/user/wt/yapi-mingw -j8
node --test op4/testler/js/*.test.js testler/js/*.test.js
python3 -m pytest -q -p no:cacheprovider testler/test_program_adi_yok.py testler/test_op4_sozlesme.py testler/test_op4_araclar.py testler/test_web_kopru_op4.py op4/testler/python
```
- MSVC /W4 /WX yalnız Windows CI'da: C4244 (örtük int→float), C4701 (ilk değersiz yerel) sık yakalanır.
- Motor değiştiyse ilgili `testler/test_*.py`; `docs/` kopyaları `python3 web_yap.py`, defter `python3 defter_yap.py`.

## CI ve kurulum dosyası
- `.github/workflows/op4.yml`: Linux çekirdek (ASan) + Windows (MSVC, ctest, motor, ekranlar, açılış, pencere, Inno
  Setup, Türkçe yolla sessiz kurulum). Yeşil koşuda yapıt `op4-setup-<sürüm>`.
- Kullanıcıya kurulum dosyası verme: `actions_list list_workflow_run_artifacts` → `actions_get
  download_workflow_run_artifact` (kısa ömürlü blob URL) → `curl` ile indir, ZIP özetini GitHub'daki `digest` ile
  karşılaştır, `.exe`'yi çıkar, dosya olarak gönder. Ortamın ağ izninde `*.blob.core.windows.net` açık olmalı.
- CI günlüğünden ekran görüntüsü: `op4/araclar/gunluk_png_coz.py`. Günlük API'si son ~5000 satırı verir.
- Sürüm: `op4/CMakeLists.txt` `OP4_TABAN_SURUM` ya da `op4-vX.Y.Z` etiketi (etiket = Release; kullanıcı onayı).

## Kullanıcı tercihleri (özet; ayrıntı MIMARI §25.1 ve IS_TAKIP)
- Arayüz Atölye·Modern, vurgu Kobalt, yazı Noto Sans SemiCondensed; sol sürükle kaydır, Shift+sol döndür.
- Yönetmelik sihirbazı kural ihlalinde engeller; rüzgâr/kar varsayılan açık; karma yapı, sahaya özel spektrum,
  hareketli yük azaltması ilk sürümde.
- Kullanıcı hızlı ilerleme ister; büyük işleri paralel paketlere böl, ama her paket önce uçtan uca çalışan, sınanmış
  bir dilim teslim etsin.
