# Kemer Çizgisi · koyu zemin

`kemer-cizgisi-acik/` klasörünün **koyu ikizi**. Özgün koyu D kavramından (`../kemer-cizgisi/`, dokunulmadı) türetildi ve açık sürümdeki iki ek buraya da aynen taşındı:

1. **Kilit taşı ışığı:** taş yerine otururken taşın arkasında beliren loş Altın radyal ışık (+ tek yumuşak halka). Zamanlama ve geometri açık sürümle birebir; yalnız opaklıklar koyu zemine göre ayarlandı (tepe %28, kalan %5,5, halka %4,5).
2. **Düz ilerleme çizgisi ("Gece" biçimi):** çentikli ölçü çizgisi yerine ince iz + soldan sağa uzayan Altın dolgu, açık uç ve yalnız hareket ederken görünen parıltı; koyu zemin değerleriyle (iz Krem %10, uç `#DBCAAF`).

Zaman çizelgesi, yerleşim, kalem yolları, derzler, dolgu sırası ve dört kare anı (250 / 1960 / 4050 / 4650 ms) iki sürümde **aynıdır**; `../kemer-cizgisi-secim.html` ikisini yan yana, eşzamanlı oynatır. Geri kalan her şey (iskele, hayalet kontur, kalemler, 1,5 DIP iz, koyu zemin kurum yazısı, tipografi, pencere kenarı) özgün koyu D'deki gibidir. Açık sürümdeki kilit taşı kenar çizgisi burada **yoktur** (Krem taş koyu zeminde zaten ayrılır).

| Dosya | İçerik |
|---|---|
| `kare-0`, `kare-50`, `kare-oturma`, `kare-100` (`.png`, `-960x540.png`) | 1920×1080 ve 960×540 kareler (`uret.py`) |
| `animasyon.html` | Canlı önizleme (varlıklar `../kimlik`, `../fontlar`); Tekrar oynat, ¼× yavaş, `?t=4050` ile dondurma |
| `aciklama.md` | Renkler, ışık zaman çizelgesi, Direct2D notları |
| `kontur.py` → `uret.py` → `html_yap.py` → `dogrula.py` | Üretim ve doğrulama sırası; `dogrulama/` Chromium–Pillow karşılaştırmaları |
