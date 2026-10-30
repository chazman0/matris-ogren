// op4 — dosya modülü (D; sözleşme S15–S17, S21, S23). Windows.
//
// TASLAK: F1 iş 1.6'da D burada şunları yapar —
//   * Hizmetler::iletisim'e IFileDialog / TaskDialogIndirect uygulamasını bağlar (şimdilik kabuğun betikli yedeği),
//   * sahibi "D" olan dosya.* komutlarına işleyici bağlar (Yeni, Şablondan, Aç, Kaydet, Farklı kaydet, İçe / dışa aktar,
//     IFC dışa aktar, Kurtar, Çıkış) — uygulama.cpp'nin Faz 0 menü yolu bağlanan komutu kendiliğinden çağırır,
//   * Hizmetler::kapatmaOnayi'nı (Kaydet / Kaydetme / Vazgeç) ve otomatik kayıt kare işini kurar,
//   * model/bina.json (çekirdek Metin) ve manifest katkılarını ekler; ModulOrtami::acilisDosyasi'nı ilk karede açar,
//   * "Dosya/Son dosyalar" menü katkısı ve Ayarlar › Dosya sayfası, ayarlar.json kalıcılığı, tek örnek borusu,
//     .op4 ilişkilendirmesi, çökme dökümü.
#include "cekirdek/kabuk.h"

namespace op4 {

void DosyaModuluKur(Hizmetler&, ModulOrtami&) {}

}  // namespace op4
