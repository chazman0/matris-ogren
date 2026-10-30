# op4 açılış ekranı — "Kemer Çizgisi", açık zemin

Koyu zemin ikizi `../acilis-koyu/` klasöründedir (aynı zaman çizelgesi, ışık ve ilerleme çizgisi; yalnız renk ve opaklıklar
zemine göre). Hangisinin varsayılan olacağı kullanıcı kararıyla belirlenir; program ikisini de taşır ve ayar olarak sunar.

Kullanıcı kararı (30.10.2026): beş alternatif arasından **Kemer Çizgisi** seçildi; **açık zemin** varyasyonu kullanılacak,
**kilit taşı yerine otururken etrafında çok loş bir ışık** yanacak, ilerleme çubuğu çentiksiz **düz çizgi** ("Gece" biçimi) olacak.

Bu klasör yerel uygulamanın (Win32 + Direct2D/DirectWrite, ayrı iş parçacığı; MIMARI.md §17) tek kaynağıdır:

| Dosya | İçerik |
|---|---|
| `aciklama.md` | Renkler, tipografi, yerleşim (960×540 DIP), hareket çizelgesi (ms), kilit taşı ışığı ve ilerleme çizgisi, Direct2D uygulama notları |
| `kontur.json` | Simge PNG'sinin alfa kanalından çıkarılmış kalem yolları (8 kalem, `g` parametresi), hayalet kontur, ölçüler — derlemede `constexpr` diziye çevrilir |
| `katmanlar/kemer.png`, `katmanlar/kilit.png` | Resmî renkli simgenin renk maskesiyle ayrılmış iki katmanı (dolgu ve kilit taşı animasyonu için) |
| `kare-0.png`, `kare-50.png`, `kare-oturma.png`, `kare-100.png` | Referans kareler (960×540): başlangıç, %50, ışığın tepe anı (4050 ms), bitiş — yerel çizimin görsel doğrulama hedefi |
| `uret.py`, `kontur.py`, `html_yap.py`, `animasyon.sablon.html` | Kareleri ve tarayıcı önizlemesini yeniden üreten betikler (`python3 uret.py`; varlıklar `..` ve `../fontlar`) |

Yazı tipleri `../fontlar/` altındadır (Inter, Cormorant Garamond, Cinzel; SIL OFL 1.1 — lisans dosyaları yanındadır).
