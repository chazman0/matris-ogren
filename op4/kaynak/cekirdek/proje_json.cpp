// op4 çekirdek — JSON ham alt değer tarayıcısı. Sahibi: D (dosya-cozum).
#include "cekirdek/proje_json.h"

#include <cstddef>

namespace op4 {
namespace {

bool Bosluk(char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }

void BoslukAtla(std::string_view s, size_t& i) {
    while (i < s.size() && Bosluk(s[i])) ++i;
}

// s[i] == '"' iken dizgenin sonundaki tırnağın ARDINA ilerler; bozuksa false.
bool DizgeAtla(std::string_view s, size_t& i) {
    if (i >= s.size() || s[i] != '"') return false;
    for (++i; i < s.size(); ++i) {
        if (s[i] == '\\') {
            ++i;
            continue;
        }
        if (s[i] == '"') {
            ++i;
            return true;
        }
    }
    return false;
}

// Bir değeri atlar (nesne / dizi derinlik sayılarak; dizgelerdeki parantezler sayılmaz).
bool DegerAtla(std::string_view s, size_t& i) {
    BoslukAtla(s, i);
    if (i >= s.size()) return false;
    const char c = s[i];
    if (c == '"') return DizgeAtla(s, i);
    if (c == '{' || c == '[') {
        int derinlik = 0;
        while (i < s.size()) {
            const char d = s[i];
            if (d == '"') {
                if (!DizgeAtla(s, i)) return false;
                continue;
            }
            if (d == '{' || d == '[') ++derinlik;
            else if (d == '}' || d == ']') {
                if (--derinlik == 0) {
                    ++i;
                    return true;
                }
                if (derinlik < 0) return false;
            }
            ++i;
        }
        return false;
    }
    // sayı, true, false, null
    const size_t bas = i;
    while (i < s.size() && s[i] != ',' && s[i] != '}' && s[i] != ']' && !Bosluk(s[i])) ++i;
    return i > bas;
}

}  // namespace

std::string_view JsonBasiniTemizle(std::string_view s) {
    if (s.size() >= 3 && static_cast<unsigned char>(s[0]) == 0xEF && static_cast<unsigned char>(s[1]) == 0xBB &&
        static_cast<unsigned char>(s[2]) == 0xBF)
        s.remove_prefix(3);
    size_t i = 0;
    BoslukAtla(s, i);
    return s.substr(i);
}

std::optional<std::string_view> JsonUstDeger(std::string_view metin, std::string_view anahtar) {
    const std::string_view s = JsonBasiniTemizle(metin);
    size_t i = 0;
    if (s.empty() || s[0] != '{') return std::nullopt;
    ++i;
    for (;;) {
        BoslukAtla(s, i);
        if (i >= s.size()) return std::nullopt;
        if (s[i] == '}') return std::nullopt;
        const size_t anahtarBas = i;
        if (!DizgeAtla(s, i)) return std::nullopt;
        const std::string_view k = s.substr(anahtarBas + 1, i - anahtarBas - 2);
        BoslukAtla(s, i);
        if (i >= s.size() || s[i] != ':') return std::nullopt;
        ++i;
        BoslukAtla(s, i);
        const size_t degerBas = i;
        if (!DegerAtla(s, i)) return std::nullopt;
        if (k == anahtar) return s.substr(degerBas, i - degerBas);
        BoslukAtla(s, i);
        if (i >= s.size()) return std::nullopt;
        if (s[i] == ',') {
            ++i;
            continue;
        }
        if (s[i] == '}') return std::nullopt;
        return std::nullopt;
    }
}

}  // namespace op4
