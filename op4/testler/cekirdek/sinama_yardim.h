// op4 C++ sınamaları — ortak yardımcılar (sözleşme). Depo dosyası okuma.
#pragma once

#include <fstream>
#include <sstream>
#include <string>

namespace op4::sinama {

// op4/ altındaki göreli yol ("veri/komutlar.json") → içerik. Bulunamazsa boş.
inline std::string Op4Dosyasi(const std::string& goreli) {
    std::ifstream f(std::string(OP4_KAYNAK_DIZINI) + "/" + goreli, std::ios::binary);
    std::ostringstream s;
    s << f.rdbuf();
    return s.str();
}

inline std::string DepoDosyasi(const std::string& goreli) {
    std::ifstream f(std::string(OP4_DEPO_DIZINI) + "/" + goreli, std::ios::binary);
    std::ostringstream s;
    s << f.rdbuf();
    return s.str();
}

}  // namespace op4::sinama
