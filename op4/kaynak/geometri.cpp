#include "geometri.h"

#include <algorithm>
#include <cmath>

namespace op4 {

void Ag::Kapsa(V3 p) {
    enKucuk = {std::min(enKucuk.x, p.x), std::min(enKucuk.y, p.y), std::min(enKucuk.z, p.z)};
    enBuyuk = {std::max(enBuyuk.x, p.x), std::max(enBuyuk.y, p.y), std::max(enBuyuk.z, p.z)};
}

Kesit2B IProfil(const std::string& ad, float h, float b, float tw, float tf, float r, int yayParca) {
    Kesit2B k;
    k.ad = ad;
    auto ekle = [&](float u, float v) {
        k.u.push_back(u);
        k.v.push_back(v);
    };
    // Köşe yuvarlatması: merkez (cu, cv), a0 → a1 (radyan), uç noktalar dahil.
    auto yay = [&](float cu, float cv, float a0, float a1) {
        int n = std::max(1, yayParca);
        for (int i = 0; i <= n; ++i) {
            float a = a0 + (a1 - a0) * static_cast<float>(i) / static_cast<float>(n);
            ekle(cu + r * std::cos(a), cv + r * std::sin(a));
        }
    };
    const float H = h * 0.5f, B = b * 0.5f, T = tw * 0.5f;
    ekle(-B, -H);
    ekle(B, -H);
    ekle(B, -H + tf);
    yay(T + r, -H + tf + r, -0.5f * PI, -PI);          // alt başlık – gövde, sağ
    yay(T + r, H - tf - r, PI, 0.5f * PI);             // gövde – üst başlık, sağ
    ekle(B, H - tf);
    ekle(B, H);
    ekle(-B, H);
    ekle(-B, H - tf);
    yay(-T - r, H - tf - r, 0.5f * PI, 0.0f);          // üst başlık – gövde, sol
    yay(-T - r, -H + tf + r, 0.0f, -0.5f * PI);        // gövde – alt başlık, sol
    ekle(-B, -H + tf);
    return k;
}

namespace {

float Alan2(const std::vector<float>& u, const std::vector<float>& v, const std::vector<uint32_t>& ix) {
    float a = 0;
    for (size_t i = 0; i < ix.size(); ++i) {
        size_t j = (i + 1) % ix.size();
        a += u[ix[i]] * v[ix[j]] - u[ix[j]] * v[ix[i]];
    }
    return a;
}

bool UcgenIcinde(float pu, float pv, float au, float av, float bu, float bv, float cu, float cv) {
    float d1 = (pu - bu) * (av - bv) - (au - bu) * (pv - bv);
    float d2 = (pu - cu) * (bv - cv) - (bu - cu) * (pv - cv);
    float d3 = (pu - au) * (cv - av) - (cu - au) * (pv - av);
    bool neg = (d1 < 0) || (d2 < 0) || (d3 < 0);
    bool pos = (d1 > 0) || (d2 > 0) || (d3 > 0);
    return !(neg && pos);
}

}  // namespace

std::vector<uint32_t> Ucgenle(const std::vector<float>& u, const std::vector<float>& v) {
    std::vector<uint32_t> kalan(u.size());
    for (size_t i = 0; i < u.size(); ++i) kalan[i] = static_cast<uint32_t>(i);
    if (Alan2(u, v, kalan) < 0) std::reverse(kalan.begin(), kalan.end());
    std::vector<uint32_t> cikti;
    size_t koruma = 0;
    while (kalan.size() > 3 && koruma++ < 10000) {
        bool kesildi = false;
        for (size_t i = 0; i < kalan.size(); ++i) {
            uint32_t a = kalan[(i + kalan.size() - 1) % kalan.size()], b = kalan[i], c = kalan[(i + 1) % kalan.size()];
            float cross = (u[b] - u[a]) * (v[c] - v[a]) - (v[b] - v[a]) * (u[c] - u[a]);
            if (cross <= 1e-12f) continue;  // içbükey ya da doğrusal köşe
            bool bos = true;
            for (uint32_t p : kalan) {
                if (p == a || p == b || p == c) continue;
                if (UcgenIcinde(u[p], v[p], u[a], v[a], u[b], v[b], u[c], v[c])) {
                    bos = false;
                    break;
                }
            }
            if (!bos) continue;
            cikti.insert(cikti.end(), {a, b, c});
            kalan.erase(kalan.begin() + static_cast<long>(i));
            kesildi = true;
            break;
        }
        if (!kesildi) break;  // bozuk çokgen: kalanı yelpazeyle kapat
    }
    for (size_t i = 1; i + 1 < kalan.size(); ++i) cikti.insert(cikti.end(), {kalan[0], kalan[i], kalan[i + 1]});
    return cikti;
}

void Uzat(const Kesit2B& k, V3 bas, V3 son, Ag& ag, float kenarAcisi) {
    const size_t n = k.u.size();
    if (n < 3) return;
    V3 x = son - bas;
    float L = Uzunluk(x);
    if (L < 1e-6f) return;
    x = x * (1.0f / L);
    V3 v = V3{0, 0, 1} - x * Nokta(V3{0, 0, 1}, x);
    if (Uzunluk(v) < 1e-3f) v = V3{1, 0, 0} - x * Nokta(V3{1, 0, 0}, x);  // düşey eleman
    v = Birim(v);
    V3 u = Capraz(v, x);
    auto dunya = [&](size_t i, V3 o) { return o + u * k.u[i] + v * k.v[i]; };

    ag.eksenler.push_back(bas);
    ag.eksenler.push_back(son);

    // Kenar normalleri (2B, dışa doğru) ve keskinlik.
    std::vector<V3> yuzNormal(n);
    for (size_t i = 0; i < n; ++i) {
        size_t j = (i + 1) % n;
        float du = k.u[j] - k.u[i], dv = k.v[j] - k.v[i];
        yuzNormal[i] = Birim(u * dv - v * du);
    }
    const float esik = std::cos(kenarAcisi * PI / 180.0f);
    std::vector<bool> keskin(n);  // köşe i: (i-1) ve i kenarları arasında
    for (size_t i = 0; i < n; ++i) keskin[i] = Nokta(yuzNormal[(i + n - 1) % n], yuzNormal[i]) < esik;

    // Yan yüzler.
    for (size_t i = 0; i < n; ++i) {
        size_t j = (i + 1) % n;
        V3 ni = keskin[i] ? yuzNormal[i] : Birim(yuzNormal[(i + n - 1) % n] + yuzNormal[i]);
        V3 nj = keskin[j] ? yuzNormal[i] : Birim(yuzNormal[i] + yuzNormal[(j + 1) % n]);
        uint32_t t = static_cast<uint32_t>(ag.koseler.size());
        ag.koseler.push_back({dunya(i, bas), ni});
        ag.koseler.push_back({dunya(j, bas), nj});
        ag.koseler.push_back({dunya(j, son), nj});
        ag.koseler.push_back({dunya(i, son), ni});
        ag.indisler.insert(ag.indisler.end(), {t, t + 1, t + 2, t, t + 2, t + 3});
    }
    // Uç kapakları.
    std::vector<uint32_t> uc = Ucgenle(k.u, k.v);
    for (int s = 0; s < 2; ++s) {
        V3 o = s == 0 ? bas : son;
        V3 nn = s == 0 ? -x : x;
        uint32_t t = static_cast<uint32_t>(ag.koseler.size());
        for (size_t i = 0; i < n; ++i) {
            ag.koseler.push_back({dunya(i, o), nn});
            ag.Kapsa(dunya(i, o));
        }
        for (size_t i = 0; i + 2 < uc.size(); i += 3) {
            if (s == 0)
                ag.indisler.insert(ag.indisler.end(), {t + uc[i], t + uc[i + 2], t + uc[i + 1]});
            else
                ag.indisler.insert(ag.indisler.end(), {t + uc[i], t + uc[i + 1], t + uc[i + 2]});
        }
        // Kapak dış çizgisi (yuvarlatma dahil).
        for (size_t i = 0; i < n; ++i) {
            ag.kenarlar.push_back(dunya(i, o));
            ag.kenarlar.push_back(dunya((i + 1) % n, o));
        }
    }
    // Boyuna keskin kenarlar.
    for (size_t i = 0; i < n; ++i)
        if (keskin[i]) {
            ag.kenarlar.push_back(dunya(i, bas));
            ag.kenarlar.push_back(dunya(i, son));
        }
}

Ag OrnekSahne(int yayParca) {
    // HE340A: h 330, b 300, tw 9.5, tf 16.5, r 27 mm. IPE300: h 300, b 150, tw 7.1, tf 10.7, r 15 mm.
    Kesit2B he = IProfil("HE340A", 0.330f, 0.300f, 0.0095f, 0.0165f, 0.027f, yayParca);
    Kesit2B ipe = IProfil("IPE300", 0.300f, 0.150f, 0.0071f, 0.0107f, 0.015f, yayParca);
    Ag ag;
    const float aciklik = 6.0f, ara = 5.0f, kot = 3.5f;
    const float ust = kot + 0.165f;  // kiriş üst yüzü
    for (float y : {0.0f, ara}) {
        Uzat(he, {0, y, 0}, {0, y, ust}, ag);              // kolonlar (güçlü eksen çerçeve düzleminde)
        Uzat(he, {aciklik, y, 0}, {aciklik, y, ust}, ag);
        Uzat(he, {0.165f, y, kot}, {aciklik - 0.165f, y, kot}, ag);  // çerçeve kirişi (kolon başlıkları arasında)
    }
    for (float x : {0.0f, aciklik}) Uzat(ipe, {x, 0.15f, ust - 0.15f}, {x, ara - 0.15f, ust - 0.15f}, ag);  // bağ kirişleri
    return ag;
}

}  // namespace op4
