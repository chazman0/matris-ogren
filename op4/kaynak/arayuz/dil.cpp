// op4 arayüzü — yerelleştirme ve sayı biçimi (bkz. dil.h). Çeviri tablosu dil_tablosu.cpp'dedir.
#include "arayuz/dil.h"

#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <string_view>
#include <unordered_map>

namespace op4 {

namespace {
ArayuzDili g_dil = ArayuzDili::Turkce;
char g_ondalik = ',';
bool g_binlik = true;

const std::unordered_map<std::string_view, const char*>& Tablo() {
    static const std::unordered_map<std::string_view, const char*> t = [] {
        std::unordered_map<std::string_view, const char*> m;
        size_t n = 0;
        const CeviriGirdisi* g = CeviriTablosu(n);
        m.reserve(n);
        for (size_t i = 0; i < n; ++i) m.emplace(g[i].tr, g[i].en);
        return m;
    }();
    return t;
}
}  // namespace

void DilAyarla(ArayuzDili d) { g_dil = d; }
ArayuzDili EtkinDil() { return g_dil; }
ArayuzDili DilKodundan(std::string_view kod) { return kod == "en" ? ArayuzDili::Ingilizce : ArayuzDili::Turkce; }

const char* Tr(const char* turkce) {
    if (g_dil == ArayuzDili::Turkce || !turkce) return turkce;
    const auto& t = Tablo();
    const auto i = t.find(turkce);
    return i == t.end() ? turkce : i->second;
}

std::string Trf(const char* bicim, ...) {
    char b[1024];
    va_list a;
    va_start(a, bicim);
    std::vsnprintf(b, sizeof(b), Tr(bicim), a);
    va_end(a);
    return b;
}

size_t CeviriSayisi() { return Tablo().size(); }

void SayiBicimiAyarla(char ondalik, bool binlik) {
    g_ondalik = ondalik == '.' ? '.' : ',';
    g_binlik = binlik;
}

std::string Sayi(double v, int basamak, bool sabit) {
    if (!std::isfinite(v)) return "—";
    basamak = basamak < 0 ? 0 : (basamak > 9 ? 9 : basamak);
    char b[64];
    std::snprintf(b, sizeof(b), "%.*f", basamak, std::fabs(v));
    std::string s = b;
    std::string tam = s, kesir;
    if (const size_t n = s.find('.'); n != std::string::npos) {
        tam = s.substr(0, n);
        kesir = s.substr(n + 1);
    }
    if (!sabit)
        while (!kesir.empty() && kesir.back() == '0') kesir.pop_back();
    std::string o;
    for (size_t i = 0; i < tam.size(); ++i) {
        if (g_binlik && i > 0 && (tam.size() - i) % 3 == 0 && tam.size() > 3) o += "\xE2\x80\x89";  // ince boşluk
        o += tam[i];
    }
    if (!kesir.empty()) o += g_ondalik + kesir;
    bool sifir = true;
    for (char ch : o)
        if (ch >= '1' && ch <= '9') sifir = false;
    if (v < 0 && !sifir) o = "−" + o;
    return o;
}

std::string Kot(double z) {
    if (std::fabs(z) < 0.0005) return "±" + Sayi(0.0, 2);
    return (z > 0 ? "+" : "−") + Sayi(std::fabs(z), 2);
}

}  // namespace op4
