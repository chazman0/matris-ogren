// op4 platform sözleşmesi — dosya sistemi yardımcıları: atomik yazma, okuma, kullanıcı klasörleri
// (MIMARI §13.2, §18.4; "F1 paket sözleşmeleri" §S17).
//
// Bütün yollar UTF-8 std::string'dir (Windows'ta içeride UTF-16'ya çevrilir; Türkçe karakterli ve boşluklu yollar —
// "C:\op4 dene ŞĞİı" — desteklenir). Uygulayan: D (dosya-cozum). Taşınabilir taslak (dosya_sistemi.cpp) std::filesystem
// ile çalışır; D, Windows'ta ReplaceFileW + 5 × 100 ms yeniden deneme (OneDrive paylaşım ihlali) ve FlushFileBuffers ile
// dosya_sistemi_win.cpp'yi yazar (MIMARI §13.2, D23).
#pragma once

#include <string>
#include <string_view>

namespace op4 {

// `veri`yi aynı klasörde geçici dosyaya yazar, diske boşaltır, hedefin yerine koyar. bak = true ise eski dosya
// "<yol>.bak" olarak kalır. Başarısızsa hedef DEĞİŞMEZ.
bool AtomikYaz(const std::string& yol, std::string_view veri, bool bak, std::string& hata);
bool DosyaOku(const std::string& yol, std::string& veri, std::string& hata, size_t enFazlaBayt = size_t{1} << 31);
bool DosyaVar(const std::string& yol);
bool DizinKur(const std::string& yol);  // ara klasörlerle; varsa true
bool DosyaSil(const std::string& yol);

struct KullaniciDizinleri {
    std::string ayarlar;   // %APPDATA%\Opus Fortis\op4            (POSIX: $XDG_CONFIG_HOME/opus-fortis/op4)
    std::string yerel;     // %LOCALAPPDATA%\Opus Fortis\op4       (POSIX: $XDG_DATA_HOME/opus-fortis/op4)
    std::string kurtarma;  // <yerel>\kurtarma
    std::string gunluk;    // <yerel>\gunluk
    std::string cokme;     // <yerel>\cokme
    std::string gecici;    // <yerel>\gecici
};
// Klasörleri bulur ve (olusturmak = true ise) oluşturur. Sınamada OP4_KULLANICI_DIZINI ortam değişkeni hepsini o kökün
// altına yönlendirir (senaryolar kullanıcının gerçek ayarlarına dokunmaz).
KullaniciDizinleri KullaniciDizinleriniBul(bool olusturmak);

}  // namespace op4
