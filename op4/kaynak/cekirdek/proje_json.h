// op4 çekirdek — JSON metninden ham alt değer çıkarma (dosya-cozum yardımcıları). Sahibi: D (dosya-cozum).
//
// Neden: .matris içindeki "bina" ve bina_coz yanıtındaki "veri" değerleri, yeniden yazılmadan (anahtar sırası, sayı
// yazımı ve boşluklar korunarak) çekirdeğe / dosyaya geçer. Böylece içe aktarılan model, kaynak metni doğrudan
// yükle'ye verilmiş gibi aynı kanonik metni üretir ve 1–50 MB'lık çözüm verisi ikinci kez kodlanmaz.
#pragma once

#include <optional>
#include <string_view>

namespace op4 {

// UTF-8 BOM'u ve baştaki boşlukları atar.
std::string_view JsonBasiniTemizle(std::string_view metin);
// Üst düzey JSON nesnesinde `anahtar`ın değerinin HAM metni (ör. "{…}", "[…]", "\"…\"", "12.5", "null").
// Metin bir nesne değilse, anahtar yoksa ya da sözdizimi bozuksa nullopt. Anahtar karşılaştırması kaçışsız baytlarla
// yapılır (op4'ün aradığı anahtarlar ASCII'dir).
std::optional<std::string_view> JsonUstDeger(std::string_view metin, std::string_view anahtar);

}  // namespace op4
