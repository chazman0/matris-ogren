// op4 çekirdek — onizleme.png çizimi (CPU, izometrik). Sahibi: D (dosya-cozum).
#include "cekirdek/proje_onizleme.h"

#include <algorithm>
#include <cmath>
#include <numeric>

#include "cekirdek/proje_zip.h"

namespace op4 {
namespace {

struct Renk {
    uint8_t r, g, b;
};
constexpr Renk RenkKodu(uint32_t rgb) {
    return {static_cast<uint8_t>(rgb >> 16), static_cast<uint8_t>(rgb >> 8), static_cast<uint8_t>(rgb)};
}

// Stüdyo belirteçleri (op4/tasarim/taslaklar/studyo/tasarim.md §3); küçük resimde okunsun diye çizgi renkleri koyulaştırıldı.
constexpr Renk ZEMIN_UST = RenkKodu(0xFFFFFF), ZEMIN_ALT = RenkKodu(0xE7E8EA);
constexpr Renk AKS = RenkKodu(0xD3CEC4), IZGARA = RenkKodu(0xE6E2DB), DOSEME = RenkKodu(0xC9C4BA);
constexpr Renk KOLON = RenkKodu(0x5F6B78), KIRIS = RenkKodu(0x7D8894), ASIK = RenkKodu(0x9AA2AB),
               CAPRAZ = RenkKodu(0x8F7A5E), MESNET = RenkKodu(0x8A6B3C);

Renk CubukRengi(CubukTuru t) {
    switch (t) {
        case CubukTuru::Kolon: return KOLON;
        case CubukTuru::Kiris:
        case CubukTuru::Kren: return KIRIS;
        case CubukTuru::Asik:
        case CubukTuru::MakasDikme:
        case CubukTuru::MakasDiyagonal: return ASIK;
        case CubukTuru::Capraz:
        case CubukTuru::Bag: return CAPRAZ;
        default: return KIRIS;
    }
}

struct Nokta2 {
    double x = 0, y = 0, d = 0;  // ekran (y aşağı) ve derinlik (büyük = uzak)
};

class Tuval {
public:
    explicit Tuval(int n) : n_(n), p_(static_cast<size_t>(n) * static_cast<size_t>(n) * 4) {
        for (int y = 0; y < n; ++y) {
            const double t = n > 1 ? static_cast<double>(y) / (n - 1) : 0.0;
            for (int x = 0; x < n; ++x) {
                uint8_t* q = &p_[(static_cast<size_t>(y) * static_cast<size_t>(n) + static_cast<size_t>(x)) * 4];
                q[0] = static_cast<uint8_t>(std::lround(ZEMIN_UST.r + (ZEMIN_ALT.r - ZEMIN_UST.r) * t));
                q[1] = static_cast<uint8_t>(std::lround(ZEMIN_UST.g + (ZEMIN_ALT.g - ZEMIN_UST.g) * t));
                q[2] = static_cast<uint8_t>(std::lround(ZEMIN_UST.b + (ZEMIN_ALT.b - ZEMIN_UST.b) * t));
                q[3] = 255;
            }
        }
    }

    void Karistir(int x, int y, Renk c, double a) {
        if (x < 0 || y < 0 || x >= n_ || y >= n_ || a <= 0) return;
        a = std::min(a, 1.0);
        uint8_t* q = &p_[(static_cast<size_t>(y) * static_cast<size_t>(n_) + static_cast<size_t>(x)) * 4];
        q[0] = static_cast<uint8_t>(std::lround(q[0] + (c.r - q[0]) * a));
        q[1] = static_cast<uint8_t>(std::lround(q[1] + (c.g - q[1]) * a));
        q[2] = static_cast<uint8_t>(std::lround(q[2] + (c.b - q[2]) * a));
    }

    // Kenar yumuşatmalı kalın çizgi: piksel merkezinin parçaya uzaklığından örtü.
    void Cizgi(Nokta2 a, Nokta2 b, double kalinlik, Renk c, double opaklik) {
        const double r = kalinlik * 0.5;
        const int x0 = static_cast<int>(std::floor(std::min(a.x, b.x) - r - 1)), x1 = static_cast<int>(std::ceil(std::max(a.x, b.x) + r + 1));
        const int y0 = static_cast<int>(std::floor(std::min(a.y, b.y) - r - 1)), y1 = static_cast<int>(std::ceil(std::max(a.y, b.y) + r + 1));
        const double dx = b.x - a.x, dy = b.y - a.y, uu = dx * dx + dy * dy;
        for (int y = std::max(y0, 0); y <= std::min(y1, n_ - 1); ++y)
            for (int x = std::max(x0, 0); x <= std::min(x1, n_ - 1); ++x) {
                const double px = x + 0.5 - a.x, py = y + 0.5 - a.y;
                const double t = uu > 1e-12 ? std::clamp((px * dx + py * dy) / uu, 0.0, 1.0) : 0.0;
                const double ex = px - t * dx, ey = py - t * dy;
                const double d = std::sqrt(ex * ex + ey * ey);
                Karistir(x, y, c, std::clamp(r + 0.5 - d, 0.0, 1.0) * opaklik);
            }
    }

    // Çokgen dolgu (tek-çift kuralı, satır tarama).
    void Dolgu(const std::vector<Nokta2>& k, Renk c, double opaklik) {
        if (k.size() < 3) return;
        double ymin = k[0].y, ymax = k[0].y;
        for (const Nokta2& p : k) {
            ymin = std::min(ymin, p.y);
            ymax = std::max(ymax, p.y);
        }
        std::vector<double> xs;
        for (int y = std::max(0, static_cast<int>(std::floor(ymin))); y <= std::min(n_ - 1, static_cast<int>(std::ceil(ymax))); ++y) {
            const double yc = y + 0.5;
            xs.clear();
            for (size_t i = 0; i < k.size(); ++i) {
                const Nokta2 &p = k[i], &q = k[(i + 1) % k.size()];
                if ((p.y <= yc && q.y > yc) || (q.y <= yc && p.y > yc)) xs.push_back(p.x + (yc - p.y) / (q.y - p.y) * (q.x - p.x));
            }
            std::sort(xs.begin(), xs.end());
            for (size_t i = 0; i + 1 < xs.size(); i += 2)
                for (int x = std::max(0, static_cast<int>(std::ceil(xs[i] - 0.5))); x <= std::min(n_ - 1, static_cast<int>(std::floor(xs[i + 1] - 0.5))); ++x)
                    Karistir(x, y, c, opaklik);
        }
    }

    OnizlemeResmi Al() && {
        OnizlemeResmi r;
        r.genislik = r.yukseklik = n_;
        r.rgba = std::move(p_);
        return r;
    }

private:
    int n_;
    std::vector<uint8_t> p_;
};

// İzometrik izdüşüm: Z çevresinde 45°, 30° yükseklik açısı (Stüdyo 3B varsayılanına yakın).
struct Izdusum {
    double c = std::cos(0.7853981633974483), s = std::sin(0.7853981633974483);
    double ce = std::cos(0.5235987755982988), se = std::sin(0.5235987755982988);
    double olcek = 1, ox = 0, oy = 0;
    Nokta2 Ham(V3d p) const {
        const double x1 = p.x * c - p.y * s, y1 = p.x * s + p.y * c;
        return {x1, -(p.z * ce + y1 * se), y1 * ce - p.z * se};
    }
    Nokta2 Ekran(V3d p) const {
        Nokta2 h = Ham(p);
        return {h.x * olcek + ox, h.y * olcek + oy, h.d};
    }
};

}  // namespace

OnizlemeResmi OnizlemeCiz(const SahneAnlik& s, int boyut) {
    boyut = std::clamp(boyut, 16, 1024);
    Tuval t(boyut);
    Izdusum iz;
    // Sınır: düğümler ve aks uçları; boş modelde Z = 0 çalışma ızgarası (30 m × 30 m).
    double xmin = 1e300, xmax = -1e300, ymin = 1e300, ymax = -1e300;
    auto kapsa = [&](V3d p) {
        const Nokta2 h = iz.Ham(p);
        xmin = std::min(xmin, h.x);
        xmax = std::max(xmax, h.x);
        ymin = std::min(ymin, h.y);
        ymax = std::max(ymax, h.y);
    };
    for (const SahneDugumu& d : s.dugumler) kapsa(d.p);
    for (const SahneAksi& a : s.akslar)
        if (a.eksen != 2) {
            kapsa(a.bas);
            kapsa(a.son);
        }
    const bool bos = s.dugumler.empty();
    if (bos) {
        kapsa({0, 0, 0});
        kapsa({30, 30, 0});
        kapsa({30, 0, 0});
        kapsa({0, 30, 0});
    }
    const double kenar = boyut * 0.08;
    const double genis = std::max(xmax - xmin, 1e-9), yuksek = std::max(ymax - ymin, 1e-9);
    iz.olcek = std::min((boyut - 2 * kenar) / genis, (boyut - 2 * kenar) / yuksek);
    iz.ox = boyut * 0.5 - (xmin + xmax) * 0.5 * iz.olcek;
    iz.oy = boyut * 0.5 - (ymin + ymax) * 0.5 * iz.olcek;
    const double cizgi = std::max(1.0, boyut / 160.0);

    if (bos) {
        for (int i = 0; i <= 6; ++i) {
            const double v = i * 5.0;
            t.Cizgi(iz.Ekran({v, 0, 0}), iz.Ekran({v, 30, 0}), cizgi * 0.75, IZGARA, 1.0);
            t.Cizgi(iz.Ekran({0, v, 0}), iz.Ekran({30, v, 0}), cizgi * 0.75, IZGARA, 1.0);
        }
    }
    for (const SahneAksi& a : s.akslar)
        if (a.eksen != 2) t.Cizgi(iz.Ekran(a.bas), iz.Ekran(a.son), cizgi * 0.6, AKS, 0.8);
    // Döşemeler (%24 saydam, Stüdyo) ve kenarları.
    for (const SahnePaneli& p : s.paneller) {
        std::vector<Nokta2> k;
        for (uint32_t i = 0; i < p.koseSayisi; ++i) {
            const size_t j = static_cast<size_t>(p.koseBas) + i;
            if (j >= s.panelKoseleri.size() || s.panelKoseleri[j] >= s.dugumler.size()) break;
            k.push_back(iz.Ekran(s.dugumler[s.panelKoseleri[j]].p));
        }
        if (k.size() < 3) continue;
        t.Dolgu(k, DOSEME, 0.30);
        for (size_t i = 0; i < k.size(); ++i) t.Cizgi(k[i], k[(i + 1) % k.size()], cizgi * 0.5, DOSEME, 0.9);
    }
    // Çubuklar uzaktan yakına.
    std::vector<size_t> sira(s.cubuklar.size());
    std::iota(sira.begin(), sira.end(), size_t{0});
    std::vector<double> derinlik(s.cubuklar.size(), 0.0);
    for (size_t i = 0; i < s.cubuklar.size(); ++i) {
        const SahneCubugu& c = s.cubuklar[i];
        if (c.i < s.dugumler.size() && c.j < s.dugumler.size())
            derinlik[i] = iz.Ham(s.dugumler[c.i].p).d + iz.Ham(s.dugumler[c.j].p).d;
    }
    std::stable_sort(sira.begin(), sira.end(), [&](size_t a, size_t b) { return derinlik[a] > derinlik[b]; });
    for (const size_t i : sira) {
        const SahneCubugu& c = s.cubuklar[i];
        if (c.i >= s.dugumler.size() || c.j >= s.dugumler.size()) continue;
        t.Cizgi(iz.Ekran(s.dugumler[c.i].p), iz.Ekran(s.dugumler[c.j].p), cizgi * 1.5, CubukRengi(c.tur), 1.0);
    }
    // Mesnetler: düğümün altında küçük Kahve üçgen.
    const double m = std::max(2.0, boyut / 64.0);
    for (const SahneMesnedi& ms : s.mesnetler) {
        if (ms.dugum >= s.dugumler.size()) continue;
        const Nokta2 p = iz.Ekran(s.dugumler[ms.dugum].p);
        t.Dolgu({p, {p.x - m, p.y + m * 1.6, p.d}, {p.x + m, p.y + m * 1.6, p.d}}, MESNET, 0.9);
    }
    return std::move(t).Al();
}

std::string OnizlemePng(const SahneAnlik& sahne, int boyut) {
    const OnizlemeResmi r = OnizlemeCiz(sahne, boyut);
    return PngKodla(r.rgba.data(), r.genislik, r.yukseklik);
}

}  // namespace op4
