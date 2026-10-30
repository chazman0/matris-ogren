// op4 çekirdek — eleman kimliği metin dönüşümleri (sözleşme S1; tam uygulama).
#include "cekirdek/kimlik.h"

#include <charconv>

namespace op4 {
namespace {

struct TurBilgisi {
    ElemanTuru tur;
    const char* kod;
    const char* ad;
};

constexpr TurBilgisi kTurler[] = {
    {ElemanTuru::Yok, "yok", "Yok"},
    {ElemanTuru::Cubuk, "cubuk", "Çubuk"},
    {ElemanTuru::Panel, "panel", "Panel"},
    {ElemanTuru::Dugum, "dugum", "Düğüm"},
    {ElemanTuru::Mesnet, "mesnet", "Mesnet"},
    {ElemanTuru::Yuk, "yuk", "Yük"},
    {ElemanTuru::Aks, "aks", "Aks"},
    {ElemanTuru::AksSistemi, "aks_sistemi", "Aks sistemi"},
    {ElemanTuru::Temel, "temel", "Temel"},
    {ElemanTuru::Referans, "referans", "Referans"},
    {ElemanTuru::Olcu, "olcu", "Ölçü"},
};
static_assert(sizeof(kTurler) / sizeof(kTurler[0]) == ELEMAN_TURU_SAYISI);

const TurBilgisi* Bilgi(ElemanTuru t) {
    const auto i = static_cast<size_t>(t);
    return i < sizeof(kTurler) / sizeof(kTurler[0]) ? &kTurler[i] : nullptr;
}

template <class T>
bool SayiOku(std::string_view s, T& v) {
    if (s.empty()) return false;
    const auto [p, hata] = std::from_chars(s.data(), s.data() + s.size(), v);
    return hata == std::errc() && p == s.data() + s.size();
}

}  // namespace

const char* TurKodu(ElemanTuru t) {
    const TurBilgisi* b = Bilgi(t);
    return b ? b->kod : "yok";
}

const char* TurAdi(ElemanTuru t) {
    const TurBilgisi* b = Bilgi(t);
    return b ? b->ad : "Yok";
}

std::optional<ElemanTuru> TurKodundan(std::string_view kod) {
    for (const TurBilgisi& b : kTurler)
        if (kod == b.kod) return b.tur;
    return std::nullopt;
}

std::string KimlikMetni(ElemanKimligi k) {
    std::string s = TurKodu(k.tur);
    s += ':';
    s += std::to_string(k.no);
    if (k.alt != 0) {
        s += '/';
        s += std::to_string(k.alt);
    }
    return s;
}

std::optional<ElemanKimligi> KimlikCoz(std::string_view metin) {
    const size_t iki = metin.find(':');
    if (iki == std::string_view::npos) return std::nullopt;
    const auto tur = TurKodundan(metin.substr(0, iki));
    if (!tur || *tur == ElemanTuru::Yok) return std::nullopt;
    std::string_view kalan = metin.substr(iki + 1);
    std::string_view altMetni;
    if (const size_t egik = kalan.find('/'); egik != std::string_view::npos) {
        altMetni = kalan.substr(egik + 1);
        kalan = kalan.substr(0, egik);
    }
    ElemanKimligi k{*tur, 0, 0};
    if (!SayiOku(kalan, k.no)) return std::nullopt;
    if (!altMetni.empty() && !SayiOku(altMetni, k.alt)) return std::nullopt;
    if (altMetni.empty() && metin.back() == '/') return std::nullopt;
    return k;
}

}  // namespace op4
