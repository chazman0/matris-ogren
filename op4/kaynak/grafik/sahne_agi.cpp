// op4 grafik — sahne anlığından katı görünüm ağı (bkz. sahne_agi.h).
#include "grafik/sahne_agi.h"

#include <algorithm>
#include <cmath>
#include <map>

#include "arayuz/tema.h"

namespace op4 {
namespace {

Kesit2B Dikdortgen(const char* ad, float h, float b) {
    Kesit2B k;
    k.ad = ad;
    const float H = h * 0.5f, B = b * 0.5f;
    k.u = {-B, B, B, -B};
    k.v = {-H, -H, H, H};
    return k;
}

Kesit2B KesitKur(const SahneAnlik& s, const SahneCubugu& c, int yay) {
    float h = 0, b = 0, tw = 0, tf = 0, r = 0;
    KesitTuru tur = KesitTuru::Bilinmiyor;
    if (c.kesit < s.kesitler.size()) {
        const SahneKesiti& k = s.kesitler[c.kesit];
        tur = k.tur;
        h = static_cast<float>(k.h);
        b = static_cast<float>(k.b);
        tw = static_cast<float>(k.tw);
        tf = static_cast<float>(k.tf);
        r = static_cast<float>(k.r);
    }
    if (h <= 0 || b <= 0) {  // kesit ölçüsü bilinmiyor (Faz 2'de kesitCoz): türe göre görsel varsayılan
        switch (c.tur) {
            case CubukTuru::Kolon: h = 0.34f, b = 0.30f, tur = KesitTuru::I; break;
            case CubukTuru::Kiris: h = 0.40f, b = 0.18f, tur = KesitTuru::I; break;
            case CubukTuru::Asik: h = 0.20f, b = 0.10f, tur = KesitTuru::I; break;
            case CubukTuru::Capraz: h = 0.10f, b = 0.10f; break;
            default: h = 0.20f, b = 0.15f; break;
        }
    }
    if (tur == KesitTuru::I) {
        if (tw <= 0) tw = std::max(0.006f, h * 0.025f);
        if (tf <= 0) tf = std::max(0.008f, h * 0.04f);
        r = std::min(r, std::max(0.0f, 0.5f * (b - tw) - 0.001f));
        return IProfil("I", h, b, tw, tf, r, r > 0 ? yay : 0);
    }
    return Dikdortgen("R", h, b);
}

V3 F(V3d p) { return {static_cast<float>(p.x), static_cast<float>(p.y), static_cast<float>(p.z)}; }

void PanelUzat(const SahneAnlik& s, const SahnePaneli& p, Ag& ag) {
    std::vector<V3> k;
    for (uint32_t i = 0; i < p.koseSayisi && p.koseBas + i < s.panelKoseleri.size(); ++i) {
        const uint32_t d = s.panelKoseleri[p.koseBas + i];
        if (d < s.dugumler.size()) k.push_back(F(s.dugumler[d].p));
    }
    if (k.size() < 3) return;
    V3 n{};
    for (size_t i = 0; i < k.size(); ++i) {
        const V3 &a = k[i], &b = k[(i + 1) % k.size()];
        n.x += (a.y - b.y) * (a.z + b.z);
        n.y += (a.z - b.z) * (a.x + b.x);
        n.z += (a.x - b.x) * (a.y + b.y);
    }
    n = Birim(n);
    if (n.z < 0) n = -n;
    const float t = std::max(0.01f, static_cast<float>(p.kalinlik > 0 ? p.kalinlik : 0.02));
    const float ax = std::fabs(n.x), ay = std::fabs(n.y), az = std::fabs(n.z);
    std::vector<float> u, v;
    for (const V3& q : k) {
        if (az >= ax && az >= ay) {
            u.push_back(q.x);
            v.push_back(q.y);
        } else if (ay >= ax) {
            u.push_back(q.x);
            v.push_back(q.z);
        } else {
            u.push_back(q.y);
            v.push_back(q.z);
        }
    }
    const std::vector<uint32_t> tri = Ucgenle(u, v);
    for (int yuz = 0; yuz < 2; ++yuz) {
        const V3 off = yuz == 0 ? V3{} : n * (-t);
        const V3 nn = yuz == 0 ? n : -n;
        const uint32_t b = static_cast<uint32_t>(ag.koseler.size());
        for (const V3& q : k) {
            ag.koseler.push_back({q + off, nn});
            ag.Kapsa(q + off);
        }
        for (size_t i = 0; i + 2 < tri.size(); i += 3)
            ag.indisler.insert(ag.indisler.end(), {b + tri[i], b + tri[i + 1], b + tri[i + 2]});
    }
    for (size_t i = 0; i < k.size(); ++i) {
        const V3 a = k[i], c = k[(i + 1) % k.size()], d = n * (-t);
        const V3 yn = Birim(Capraz(c - a, n));
        const uint32_t b = static_cast<uint32_t>(ag.koseler.size());
        ag.koseler.push_back({a, yn});
        ag.koseler.push_back({c, yn});
        ag.koseler.push_back({c + d, yn});
        ag.koseler.push_back({a + d, yn});
        ag.indisler.insert(ag.indisler.end(), {b, b + 1, b + 2, b, b + 2, b + 3});
        ag.kenarlar.insert(ag.kenarlar.end(), {a, c, a + d, c + d});
    }
}

}  // namespace

Ag SahneAgiKur(const SahneAnlik& s, const SahneAgiAyari& a) {
    const tema::Renkler& R = tema::Etkin().r;
    auto secili = [&](ElemanKimligi k) { return a.secim && std::binary_search(a.secim->begin(), a.secim->end(), k); };
    // Renk sınıfı → eleman listesi (parça başına bir çizim çağrısı).
    struct Sinif {
        uint32_t renk, kenar;
        std::vector<size_t> cubuk, panel;
    };
    std::map<std::pair<uint32_t, uint32_t>, Sinif> siniflar;
    auto ekle = [&](uint32_t renk, uint32_t kenar) -> Sinif& {
        auto& x = siniflar[{renk, kenar}];
        x.renk = renk;
        x.kenar = kenar;
        return x;
    };
    for (size_t i = 0; i < s.cubuklar.size(); ++i) {
        const SahneCubugu& c = s.cubuklar[i];
        const ElemanKimligi k = CubukKimligi(c.no);
        uint32_t renk = R.digerCubuk;
        switch (c.tur) {
            case CubukTuru::Kolon: renk = R.kolon; break;
            case CubukTuru::Kiris: renk = R.kiris; break;
            case CubukTuru::Asik: renk = R.asik; break;
            case CubukTuru::Capraz: renk = R.capraz; break;
            default: break;
        }
        uint32_t kenar = R.kenar;
        if (secili(k)) {
            renk = R.seciliDolgu;
            kenar = R.secim;
        } else if (a.yalnizSecili) {
            renk = tema::Renk(0xF0F1F3);
            kenar = tema::Renk(0x454B53, 0.15f);
        }
        if (a.uzerinde == k) kenar = R.uzerinde;
        ekle(renk, kenar).cubuk.push_back(i);
    }
    for (size_t i = 0; i < s.paneller.size(); ++i) {
        const ElemanKimligi k = PanelKimligi(s.paneller[i].no);
        uint32_t renk = R.doseme, kenar = R.kenar;
        if (secili(k)) {
            renk = R.seciliDolgu;
            kenar = R.secim;
        } else if (a.yalnizSecili) {
            renk = tema::Renk(0xF0F1F3);
        }
        if (a.uzerinde == k) kenar = R.uzerinde;
        ekle(renk, kenar).panel.push_back(i);
    }
    Ag ag;
    for (auto& [anahtar, sn] : siniflar) {
        AgParcasi p;
        p.renk = sn.renk;
        p.kenarRenk = sn.kenar;
        p.indisBas = static_cast<uint32_t>(ag.indisler.size());
        p.kenarBas = static_cast<uint32_t>(ag.kenarlar.size());
        for (const size_t i : sn.cubuk) {
            const SahneCubugu& c = s.cubuklar[i];
            if (c.i >= s.dugumler.size() || c.j >= s.dugumler.size()) continue;
            Uzat(KesitKur(s, c, a.yayParca), F(s.dugumler[c.i].p), F(s.dugumler[c.j].p), ag);
        }
        for (const size_t i : sn.panel) PanelUzat(s, s.paneller[i], ag);
        p.indisSayi = static_cast<uint32_t>(ag.indisler.size()) - p.indisBas;
        p.kenarSayi = static_cast<uint32_t>(ag.kenarlar.size()) - p.kenarBas;
        if (p.indisSayi > 0) ag.parcalar.push_back(p);
    }
    // Seçili ve üzerindeki parçalar en son: kenar çizgileri diğerlerinin önünde kalsın (derinlik eşitliğinde).
    std::stable_partition(ag.parcalar.begin(), ag.parcalar.end(),
                          [&](const AgParcasi& p) { return p.kenarRenk != R.secim && p.kenarRenk != R.uzerinde; });
    return ag;
}

}  // namespace op4
