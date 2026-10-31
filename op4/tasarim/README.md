# op4 arayüz tasarımı

| Dosya | İçerik |
|---|---|
| `ARAYUZ_ILKELERI.md` | İki yaygın ticari programın kullanım mantığından çıkarılan 25 bağlayıcı ilke (şerit iskeleti, kat kapsamı anahtarı, seçim anahtarları, Seç & Süz, bağlamsal Özellikler, tutamaçlar, sonuç gösterimi, gezinme) |
| `taslaklar/pafta/` | A — "Pafta": krem yüzeyler, ince çizgiler, bol boşluk; altın yalnız etkin/seçili durumda |
| `taslaklar/atolye/` | B — "Atölye": nötr açık gri, yoğun bilgi; sol ray, sekmeli alt rıhtım; kahve birincil vurgu |
| `taslaklar/studyo/` | C — "Stüdyo": beyaza yakın yüzeyler, yumuşak gölgeli yüzen paneller, ince sekme şeridi |

Her taslak klasöründe: `tasarim.md` (kavram, renk ve tipografi belirteçleri, 8 px ızgara, yerleşim kuralları, Dear ImGui eşlemesi, 25 ilkenin taslaktaki yeri), `uret.py` (Pillow ile taslak görsellerini yeniden üretir; yazı tipleri ve logolar `../../kimlik/`), `ana.webp` / `kucuk.webp` / `secsuz.webp` / `sonuc.webp` (1920×1080, 1366×768, Seç & Süz, Tasarım sekmesi).

İlk iskeletin varsayılan arayüzü kullanıcı tarafından reddedildi (görünüm, yerleşim, yazı tipi, yoğunluk, çalışma mantığı); yeni arayüz bu taslaklardan seçilecek yönle, kod yazılmadan önce onaylanacak.

## Seç & Süz (harman tasarım; Faz 3)

`secsuz/`: varsayılan **pratik katman** (sayılı ölçüt listeleri; aynı ölçütte "veya", ölçütler arasında "ve"; Yeni / Ekle /
Çıkar / Kesişim; kat kapsamı; hızlı eylemler) ve isteğe bağlı **Gelişmiş katman** (çiplerden üretilen kural satırları,
sayısal/metin koşullar, süzgeç olarak kaydet → seçim, görünüm, renk kuralı). Kullanıcı kararı: kural düzenleyicisi tek
başına "komplike", ölçüt listeli seçim "pratik"; ikisinin harmanı. Belge `secsuz.md`; görseller `*.webp`; üreteç
`secsuz_uret.py` (+ `ozn.py`; Atölye üretecinin `uret.py`, `tuval.py`, `sahne.py` dosyalarını `../taslaklar/atolye/`
klasöründen kullanır).
