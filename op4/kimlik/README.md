# Opus Fortis kurumsal kimlik (op4)

Kaynak: Opus Fortis kurumsal kimlik klasörü (kullanıcıdan). Bütün dosyalar saydam arka planlı PNG'dir.

| Dosya | İçerik | Zemin |
|---|---|---|
| `opus-fortis-yatay-koyu-zemin.png` (2000×712) | Kahverengi kemer + krem "OPUS FORTİS" yazısı, İ noktası altın kilit taşı | Koyu |
| `opus-fortis-yatay-acik-zemin.png` (2000×712) | Antrasit kemer ve yazı, gri kilit taşı | Açık |
| `opus-fortis-yazi-acik-zemin.png` (2000×369) | Tek satır "OPUS FORTİS" yazısı, antrasit; İ noktası altın kilit taşı | Açık |
| `opus-fortis-yazi-koyu-zemin.png` (2000×369) | Tek satır "OPUS FORTİS" yazısı, krem; İ noktası altın kilit taşı | Koyu |
| `opus-fortis-simge-renkli.png` (1200×1397) | Kahverengi kemer, krem kilit taşı | Koyu ya da açık |
| `opus-fortis-simge-koyu.png` (1200×1397) | Antrasit kemer, gri kilit taşı | Açık |
| `opus-fortis-simge-beyaz.png` (1200×1397) | Beyaz kemer, gri kilit taşı | Koyu |

## Renkler

| Ad | Hex |
|---|---|
| Kahve (kemer) | `#8A6B3C` |
| Krem (yazı, kilit taşı) | `#EDE6D8` |
| Altın (İ noktası kilit taşı) | `#B08950` |
| Antrasit | `#14181B` |
| Gri (kilit taşı, tek renk sürüm) | `#8C8C8C` |

Simgede kemerin tepesindeki ayrı parça kilit taşıdır; açılış ekranı animasyonları bu parçayı kullanabilir.

## op4'te kullanım

| Yer | Dosya (öncelik sırasıyla) |
|---|---|
| Açılış (yükleme) ekranının logo yuvası (açık zemin) | `logo.png` → `opus-fortis-yatay-acik-zemin.png` → `opus_fortis_logo_placeholder.png` |
| op4.exe simgesi, kurulum sihirbazı, Başlat menüsü kısayolu | `op4.ico` (`op4/araclar/kimlik_uret.py` ile `opus-fortis-simge-renkli.png`'den üretilir) → `op4_simge_placeholder.ico` |
| Arayüz renkleri (ImGui teması, açılış ekranı bandı) | yukarıdaki palet: antrasit zemin, kahve vurgu, altın seçim, krem yazı |

Logo yuvası 96 DPI'da 540 × 160 piksellik kutudur (en-boy oranı korunur, saydamlık desteklenir; 2000 piksellik kaynaklar
yüksek DPI'da da keskindir). `*_placeholder.*` dosyaları gerçek kimlik gelmeden önce kullanılan yer tutuculardır
(`op4/araclar/yer_tutucu_kimlik.py`); gerçek dosyalar eksikse yedek olarak kalırlar.
