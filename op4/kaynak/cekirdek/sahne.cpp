// op4 çekirdek — sahne anlığı yardımcıları ve sınama düzeneği (sözleşme S4; tam uygulama).
#include "cekirdek/sahne.h"

namespace op4 {

void SahneAnlik::DizinleriKur() {
    dugumDizini_.clear();
    cubukDizini_.clear();
    panelDizini_.clear();
    dugumDizini_.reserve(dugumler.size());
    cubukDizini_.reserve(cubuklar.size());
    panelDizini_.reserve(paneller.size());
    sinir = Kutu3d{};
    for (size_t i = 0; i < dugumler.size(); ++i) {
        dugumDizini_[dugumler[i].no] = static_cast<uint32_t>(i);
        sinir.Kapsa(dugumler[i].p);
    }
    for (size_t i = 0; i < cubuklar.size(); ++i) cubukDizini_[cubuklar[i].no] = static_cast<uint32_t>(i);
    for (size_t i = 0; i < paneller.size(); ++i) panelDizini_[paneller[i].no] = static_cast<uint32_t>(i);
    for (const SahneAksi& a : akslar) {
        sinir.Kapsa(a.bas);
        sinir.Kapsa(a.son);
    }
}

namespace {
std::optional<size_t> Bul(const std::unordered_map<uint32_t, uint32_t>& m, uint32_t no) {
    const auto i = m.find(no);
    if (i == m.end()) return std::nullopt;
    return static_cast<size_t>(i->second);
}
}  // namespace

std::optional<size_t> SahneAnlik::DugumDizini(uint32_t no) const { return Bul(dugumDizini_, no); }
std::optional<size_t> SahneAnlik::CubukDizini(uint32_t no) const { return Bul(cubukDizini_, no); }
std::optional<size_t> SahneAnlik::PanelDizini(uint32_t no) const { return Bul(panelDizini_, no); }

bool SahneAnlik::Var(ElemanKimligi k) const { return !Sinir(k).Bos(); }

Kutu3d SahneAnlik::Sinir(ElemanKimligi k) const {
    Kutu3d s;
    switch (k.tur) {
        case ElemanTuru::Dugum:
            if (const auto i = DugumDizini(k.no)) s.Kapsa(dugumler[*i].p);
            break;
        case ElemanTuru::Mesnet:
            if (const auto i = DugumDizini(k.no))
                for (const SahneMesnedi& m : mesnetler)
                    if (m.dugum == *i) s.Kapsa(dugumler[*i].p);
            break;
        case ElemanTuru::Cubuk:
            if (const auto i = CubukDizini(k.no)) {
                const SahneCubugu& c = cubuklar[*i];
                if (c.i < dugumler.size() && c.j < dugumler.size()) {
                    s.Kapsa(dugumler[c.i].p);
                    s.Kapsa(dugumler[c.j].p);
                }
            }
            break;
        case ElemanTuru::Panel:
            if (const auto i = PanelDizini(k.no)) {
                const SahnePaneli& p = paneller[*i];
                for (uint32_t n = 0; n < p.koseSayisi && p.koseBas + n < panelKoseleri.size(); ++n) {
                    const uint32_t d = panelKoseleri[p.koseBas + n];
                    if (d < dugumler.size()) s.Kapsa(dugumler[d].p);
                }
            }
            break;
        case ElemanTuru::Aks:
            for (const SahneAksi& a : akslar)
                if (a.kimlik == k) {
                    s.Kapsa(a.bas);
                    s.Kapsa(a.son);
                }
            break;
        case ElemanTuru::Temel:
            for (const SahneTemeli& t : temeller)
                if (t.kimlik == k && t.dugum < dugumler.size()) s.Kapsa(dugumler[t.dugum].p);
            break;
        default:
            break;
    }
    return s;
}

SahnePtr BosSahne() {
    static const SahnePtr bos = [] {
        auto s = std::make_shared<SahneAnlik>();
        s->baslik = "Adsız 1";
        s->sistem = "celik";
        s->seviyeler.push_back({"±0.00", 0.0, 0});
        s->DizinleriKur();
        return SahnePtr(s);
    }();
    return bos;
}

SahnePtr OrnekSahneAnlik() {
    auto s = std::make_shared<SahneAnlik>();
    s->surum = 1;
    s->modelSurumu = 3;
    s->baslik = "Örnek çerçeve";
    s->sistem = "celik";
    const double aciklik = 6.0, ara = 5.0, kot = 3.5;
    s->seviyeler = {{"±0.00", 0.0, 0}, {"+3.50", kot, 1}};
    s->kesitler.push_back({"HE340A", "HEA 340", KesitTuru::I, "S275", 0.330, 0.300, 0.0095, 0.0165, 0.027});
    s->kesitler.push_back({"IPE300", "IPE 300", KesitTuru::I, "S275", 0.300, 0.150, 0.0071, 0.0107, 0.015});
    s->malzemeler = {"S275"};
    s->gruplar = {"KOLON", "KIRIS", "BAG"};

    // Akslar: A (x = 0), B (x = 6) → eksen x; 1 (y = 0), 2 (y = 5) → eksen y; iki Z aksı.
    auto aks = [&](uint8_t eksen, uint32_t sira, const char* ad, V3d bas, V3d son, V3d balon) {
        SahneAksi a;
        a.kimlik = {ElemanTuru::Aks, 0, static_cast<uint32_t>(eksen) * 65536u + sira};
        a.ad = ad;
        a.sistem = "GLOBAL";
        a.eksen = eksen;
        a.bas = bas;
        a.son = son;
        a.balon = balon;
        s->akslar.push_back(a);
    };
    aks(0, 0, "A", {0, -1.5, 0}, {0, ara + 1.5, 0}, {0, -2.0, 0});
    aks(0, 1, "B", {aciklik, -1.5, 0}, {aciklik, ara + 1.5, 0}, {aciklik, -2.0, 0});
    aks(1, 0, "1", {-1.5, 0, 0}, {aciklik + 1.5, 0, 0}, {-2.0, 0, 0});
    aks(1, 1, "2", {-1.5, ara, 0}, {aciklik + 1.5, ara, 0}, {-2.0, ara, 0});

    // Düğümler: aks–kat numaralaması 1000·kat + 20·ix + iy + 1.
    for (int kat = 0; kat <= 1; ++kat)
        for (int ix = 0; ix <= 1; ++ix)
            for (int iy = 0; iy <= 1; ++iy) {
                SahneDugumu d;
                d.no = static_cast<uint32_t>(1000 * kat + 20 * ix + iy + 1);
                d.p = {ix * aciklik, iy * ara, kat * kot};
                d.tur = DugumTuru::AksKat;
                d.bayrak = kat == 0 ? dugum_bayragi::MESNETLI : 0;
                s->dugumler.push_back(d);
            }
    auto dizin = [](int kat, int ix, int iy) { return static_cast<uint32_t>(kat * 4 + ix * 2 + iy); };
    uint32_t no = 1;
    auto cubuk = [&](uint32_t i, uint32_t j, CubukTuru tur, uint32_t kesit, uint32_t grup, double aci) {
        SahneCubugu c;
        c.no = no++;
        c.i = i;
        c.j = j;
        c.tur = tur;
        c.kesit = kesit;
        c.grup = grup;
        c.aci = aci;
        const V3d x = Birim(s->dugumler[j].p - s->dugumler[i].p);
        const double D = std::hypot(x.x, x.y);
        c.yYerel = D > 0 ? V3d{-x.x * x.z / D, -x.y * x.z / D, D} : V3d{x.z > 0 ? -1.0 : 1.0, 0, 0};
        s->cubuklar.push_back(c);
    };
    for (int ix = 0; ix <= 1; ++ix)
        for (int iy = 0; iy <= 1; ++iy) cubuk(dizin(0, ix, iy), dizin(1, ix, iy), CubukTuru::Kolon, 0, 0, 0.0);
    for (int iy = 0; iy <= 1; ++iy) cubuk(dizin(1, 0, iy), dizin(1, 1, iy), CubukTuru::Kiris, 0, 1, 0.0);
    for (int ix = 0; ix <= 1; ++ix) cubuk(dizin(1, ix, 0), dizin(1, ix, 1), CubukTuru::Kiris, 1, 2, 0.0);
    for (int ix = 0; ix <= 1; ++ix)
        for (int iy = 0; iy <= 1; ++iy) s->mesnetler.push_back({dizin(0, ix, iy), 0x3F, MesnetTuru::Ankastre});
    s->DizinleriKur();
    return s;
}

}  // namespace op4
