// op4 çekirdek — Türkçe metin yardımcıları (sözleşme S6; tam uygulama).
#include "cekirdek/turkce.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>

namespace op4 {

std::string TurkceKatla(std::string_view s) {
    std::string o;
    o.reserve(s.size());
    for (size_t i = 0; i < s.size(); ++i) {
        const auto c = static_cast<unsigned char>(s[i]);
        if (c < 0x80) {
            o += static_cast<char>(c >= 'A' && c <= 'Z' ? c + ('a' - 'A') : c);
            continue;
        }
        if (i + 1 < s.size()) {
            const auto d = static_cast<unsigned char>(s[i + 1]);
            char k = 0;
            if (c == 0xC3) {
                switch (d) {
                    case 0x87: case 0xA7: k = 'c'; break;  // Ç ç
                    case 0x96: case 0xB6: k = 'o'; break;  // Ö ö
                    case 0x9C: case 0xBC: k = 'u'; break;  // Ü ü
                    case 0x82: case 0xA2: k = 'a'; break;  // Â â
                    case 0x8E: case 0xAE: k = 'i'; break;  // Î î
                    case 0x9B: case 0xBB: k = 'u'; break;  // Û û
                    default: break;
                }
            } else if (c == 0xC4) {
                switch (d) {
                    case 0x9E: case 0x9F: k = 'g'; break;  // Ğ ğ
                    case 0xB0: case 0xB1: k = 'i'; break;  // İ ı
                    default: break;
                }
            } else if (c == 0xC5) {
                if (d == 0x9E || d == 0x9F) k = 's';  // Ş ş
            }
            if (k) {
                o += k;
                ++i;
                continue;
            }
        }
        o += static_cast<char>(c);
    }
    return o;
}

bool TurkceOnekMi(std::string_view onek, std::string_view metin) {
    const std::string a = TurkceKatla(onek), b = TurkceKatla(metin);
    return b.compare(0, a.size(), a) == 0;
}

std::string OndalikVirgul(double v, int basamak) {
    if (!std::isfinite(v)) return v != v ? "—" : (v > 0 ? "∞" : "−∞");
    if (basamak < 0) basamak = 0;
    if (basamak > 12) basamak = 12;
    char b[64];
    std::snprintf(b, sizeof(b), "%.*f", basamak, v);
    std::string s = b;
    if (const size_t n = s.find('.'); n != std::string::npos) {
        while (!s.empty() && s.back() == '0') s.pop_back();
        if (!s.empty() && s.back() == '.') s.pop_back();
        if (const size_t m = s.find('.'); m != std::string::npos) s[m] = ',';
    }
    if (s == "-0") s = "0";
    return s;
}

bool SayiOku(std::string_view metin, double& deger) {
    std::string s(metin);
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t')) s.erase(s.begin());
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t')) s.pop_back();
    if (s.empty()) return false;
    for (char& c : s)
        if (c == ',') c = '.';
    char* son = nullptr;
    const double v = std::strtod(s.c_str(), &son);
    if (son != s.c_str() + s.size() || !std::isfinite(v)) return false;
    deger = v;
    return true;
}

}  // namespace op4
