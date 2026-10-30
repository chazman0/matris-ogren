# op4 kimlik dosyaları (Opus Fortis)

Bu klasördeki `*_placeholder.*` dosyaları **yer tutucudur**; gerçek Opus Fortis logosu henüz gelmedi.
`op4/araclar/yer_tutucu_kimlik.py` ile üretilirler (Pillow).

| Dosya | Nerede kullanılır | Gerçek dosya geldiğinde |
|---|---|---|
| `opus_fortis_logo_placeholder.png` | açılış (yükleme) ekranının logo yuvası | aynı klasöre **`logo.png`** adıyla koyun; program önce onu arar |
| `op4_simge_placeholder.ico` | op4.exe simgesi, kurulum sihirbazı, Başlat menüsü kısayolu | **`op4.ico`** adıyla koyun; CMake ve kurulum betiği önce onu kullanır |
| `op4_simge_placeholder.png` | belgeler | — |

Logo yuvası: 96 DPI'da 540 × 150 piksellik kutu (en-boy oranı korunur, saydamlık desteklenir). Yüksek DPI
ekranlarda (200 %) keskin görünmesi için logonun en az **1080 × 300** piksel, saydam zeminli PNG olması önerilir.
Simge: 16, 20, 24, 32, 40, 48, 64, 128 ve 256 piksellik katmanları olan tek bir `.ico`.
