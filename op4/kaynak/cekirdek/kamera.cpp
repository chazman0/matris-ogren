// op4 çekirdek — görünüm kamerası ve mutlak çapalı gezinme (MIMARI §7.2; bkz. kamera.h). Sahibi: C.
#include "cekirdek/kamera.h"

#include <algorithm>
#include <cmath>

#include <nlohmann/json.hpp>

namespace op4 {
namespace {

constexpr double YAKIN = 0.05;          // perspektif yakın düzlem (m); ters-Z, uzak düzlem sonsuz
constexpr double ORTO_DERINLIK = 1e4;   // ortografikte hedefin önünde ve arkasında çizilen derinlik (m)
constexpr double EN_KUCUK_UZAKLIK = 0.05;
constexpr double ORTO_EN_KUCUK = 0.05, ORTO_EN_BUYUK = 1e6;

// a ekseni (birim) çevresinde θ döndürme (Rodrigues).
V3d Dondur(V3d v, V3d a, double t) {
    const double c = std::cos(t), s = std::sin(t);
    return v * c + Capraz(a, v) * s + a * (Nokta(a, v) * (1.0 - c));
}

struct Isin2 {
    V3d o, d;  // d birim olmak zorunda değil
};

// Kameranın (px, py) pikselinden geçen ışını (analitik; ters matris kullanmaz → kaydırmada en yüksek doğruluk).
Isin2 PikselIsini2(const GorunumKamerasi& k, double px, double py, double g, double y) {
    const double nx = px / g * 2.0 - 1.0, ny = 1.0 - py / y * 2.0, en = g / std::max(1.0, y);
    const V3d f = k.Ileri(), r = k.Sag(), u = k.Yukari();
    if (k.d.ortografik) {
        const double hy = k.d.ortoYukseklik * 0.5, hx = hy * en;
        return {k.d.hedef + r * (nx * hx) + u * (ny * hy) - f * k.d.uzaklik, f};
    }
    const double ty = std::tan(k.d.dikeyAci * 0.5), tx = ty * en;
    return {k.Goz(), f + r * (nx * tx) + u * (ny * ty)};
}

}  // namespace

V3d GorunumKamerasi::GozYonu() const {
    const double ce = std::cos(d.egim);
    return {ce * std::cos(d.sapma), ce * std::sin(d.sapma), std::sin(d.egim)};
}

V3d GorunumKamerasi::Sag() const { return {-std::sin(d.sapma), std::cos(d.sapma), 0.0}; }

V3d GorunumKamerasi::Yukari() const { return Capraz(Sag(), Ileri()); }

double GorunumKamerasi::PikselBoyu(double h) const {
    h = std::max(1.0, h);
    if (d.ortografik) return d.ortoYukseklik / h;
    return 2.0 * d.uzaklik * std::tan(d.dikeyAci * 0.5) / h;
}

GorusIzdusumu GorunumKamerasi::Izdusum(double g, double y, double dpiOlcek) const {
    g = std::max(1.0, g);
    y = std::max(1.0, y);
    const V3d r = Sag(), u = Yukari(), b = GozYonu(), e = Goz();
    // Görünüm (satır öncelikli, sütun vektörü): satırlar sağ, yukarı, geri; öteleme −e.
    const std::array<double, 16> V{r.x, r.y, r.z, -Nokta(r, e), u.x, u.y, u.z, -Nokta(u, e),
                                   b.x, b.y, b.z, -Nokta(b, e), 0, 0, 0, 1};
    std::array<double, 16> P{};
    const double en = g / y;
    if (d.ortografik) {
        const double hy = d.ortoYukseklik * 0.5, hx = hy * en;
        const double N = d.uzaklik - ORTO_DERINLIK, F = d.uzaklik + ORTO_DERINLIK;
        // ters-Z: derinlik (−z) = N → 1, F → 0.
        P = {1.0 / hx, 0, 0, 0, 0, 1.0 / hy, 0, 0, 0, 0, 1.0 / (F - N), F / (F - N), 0, 0, 0, 1};
    } else {
        const double fy = 1.0 / std::tan(d.dikeyAci * 0.5);
        P = {fy / en, 0, 0, 0, 0, fy, 0, 0, 0, 0, 0, YAKIN, 0, 0, -1, 0};
    }
    GorusIzdusumu o;
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) {
            double t = 0;
            for (int k = 0; k < 4; ++k) t += P[i * 4 + k] * V[k * 4 + j];
            o.gorunumIzdusum[i * 4 + j] = t;
        }
    o.genislik = g;
    o.yukseklik = y;
    o.goz = e;
    o.ortografik = d.ortografik;
    o.dpiOlcek = dpiOlcek;
    return o;
}

void GorunumKamerasi::Sigdir(const Kutu3d& k, double g, double y) {
    if (k.Bos()) return;
    g = std::max(1.0, g);
    y = std::max(1.0, y);
    const double en = g / y, pay = 0.86;  // görüş alanının %86'sı
    V3d koseler[8];
    for (int i = 0; i < 8; ++i)
        koseler[i] = {(i & 1) ? k.enBuyuk.x : k.enKucuk.x, (i & 2) ? k.enBuyuk.y : k.enKucuk.y,
                      (i & 4) ? k.enBuyuk.z : k.enKucuk.z};
    d.hedef = k.Merkez();
    const V3d r = Sag(), u = Yukari(), b = GozYonu();
    for (int tur = 0; tur < 3; ++tur) {
        if (d.ortografik) {
            double x0 = 1e300, x1 = -1e300, y0 = 1e300, y1 = -1e300;
            for (const V3d& p : koseler) {
                const V3d v = p - d.hedef;
                x0 = std::min(x0, Nokta(v, r));
                x1 = std::max(x1, Nokta(v, r));
                y0 = std::min(y0, Nokta(v, u));
                y1 = std::max(y1, Nokta(v, u));
            }
            d.hedef = d.hedef + r * ((x0 + x1) * 0.5) + u * ((y0 + y1) * 0.5);
            const double hx = std::max(1e-6, x1 - x0), hy = std::max(1e-6, y1 - y0);
            d.ortoYukseklik = std::clamp(std::max(hy, hx / en) / pay, ORTO_EN_KUCUK, ORTO_EN_BUYUK);
            double derin = 0;
            for (const V3d& p : koseler) derin = std::max(derin, Nokta(p - d.hedef, b));
            d.uzaklik = std::max(10.0, derin * 2.0 + 10.0);
            continue;
        }
        const double ty = std::tan(d.dikeyAci * 0.5) * pay, tx = ty * en;
        double D = 0.5;
        for (const V3d& p : koseler) {
            const V3d v = p - d.hedef;
            const double x = std::fabs(Nokta(v, r)), yy = std::fabs(Nokta(v, u)), z = Nokta(v, b);
            D = std::max({D, z + x / tx, z + yy / ty, z + 4.0 * YAKIN});
        }
        d.uzaklik = D;
        // İzdüşen kutuyu ortala (bir düzeltme turu yeter).
        double x0 = 1e300, x1 = -1e300, y0 = 1e300, y1 = -1e300;
        for (const V3d& p : koseler) {
            const V3d v = p - d.hedef;
            const double z = D - Nokta(v, b);
            if (z <= 1e-9) continue;
            const double sx = Nokta(v, r) / z, sy = Nokta(v, u) / z;
            x0 = std::min(x0, sx);
            x1 = std::max(x1, sx);
            y0 = std::min(y0, sy);
            y1 = std::max(y1, sy);
        }
        if (x1 > x0) d.hedef = d.hedef + r * ((x0 + x1) * 0.5 * D) + u * ((y0 + y1) * 0.5 * D);
    }
}

void StandartYonUygula(GorunumKamerasi& k, StandartYon y) {
    switch (y) {
        case StandartYon::Izometrik:
            k.d.ortografik = false;
            k.d.sapma = -127.0 * DERECE;  // taslaktaki bakış (sahne.py az = −127°, el = 23°)
            k.d.egim = 23.0 * DERECE;
            break;
        case StandartYon::Plan:
            k.d.ortografik = true;
            k.d.sapma = -90.0 * DERECE;  // sağ = +X, yukarı = +Y
            k.d.egim = 90.0 * DERECE;
            break;
        case StandartYon::On:
            k.d.ortografik = true;
            k.d.sapma = -90.0 * DERECE;  // göz −Y tarafında; sağ = +X, yukarı = +Z
            k.d.egim = 0.0;
            break;
        case StandartYon::Yan:
            k.d.ortografik = true;
            k.d.sapma = 0.0;  // göz +X tarafında; sağ = +Y
            k.d.egim = 0.0;
            break;
    }
}

void KameraSuruklemesi::Basla(const GorunumKamerasi& k, SuruklemeTuru tur, double px, double py, V3d P, double g,
                              double y) {
    tur_ = tur;
    c0_ = k.d;
    mx0_ = px;
    my0_ = py;
    P_ = P;
    g_ = std::max(1.0, g);
    y_ = std::max(1.0, y);
}

void KameraSuruklemesi::Guncelle(GorunumKamerasi& k, double px, double py) const {
    if (tur_ == SuruklemeTuru::Yok) return;
    GorunumKamerasi k0;
    k0.d = c0_;
    if (tur_ == SuruklemeTuru::Kaydir) {
        const Isin2 i = PikselIsini2(k0, px, py, g_, y_);
        const V3d f = k0.Ileri();
        const double payda = Nokta(i.d, f);
        if (std::fabs(payda) < 1e-15) return;
        const double t = Nokta(P_ - i.o, f) / payda;
        const V3d Q = i.o + i.d * t;
        k.d = c0_;
        k.d.hedef = c0_.hedef + (P_ - Q);
        return;
    }
    // Döndürme: P çevresinde katı döndürme (önce C₀'ın sağ ekseni, sonra dünya Z).
    const double dS = -DONME_K * (px - mx0_);
    const double e1 = std::clamp(c0_.egim + DONME_K * (py - my0_), -EGIM_SINIRI, EGIM_SINIRI);
    const double dE = e1 - c0_.egim;
    const V3d sag0 = k0.Sag();
    V3d v = Dondur(c0_.hedef - P_, sag0, -dE);
    v = Dondur(v, {0, 0, 1}, dS);
    k.d = c0_;
    k.d.sapma = c0_.sapma + dS;
    k.d.egim = e1;
    k.d.hedef = P_ + v;
}

void Yakinlas(GorunumKamerasi& k, double adim, V3d P) {
    double f = std::pow(1.2, adim);
    if (!(f > 0) || !std::isfinite(f)) return;
    if (k.d.ortografik) {
        const double h = std::clamp(k.d.ortoYukseklik / f, ORTO_EN_KUCUK, ORTO_EN_BUYUK);
        f = k.d.ortoYukseklik / h;
        const V3d fw = k.Ileri();
        V3d v = P - k.d.hedef;
        v = v - fw * Nokta(v, fw);
        k.d.hedef = k.d.hedef + v * (1.0 - 1.0 / f);
        k.d.ortoYukseklik = h;
        return;
    }
    const V3d e = k.Goz();
    const double gp = Uzunluk(e - P);
    if (gp / f < EN_KUCUK_UZAKLIK) f = std::max(1.0, gp / EN_KUCUK_UZAKLIK);
    if (k.d.uzaklik / f > 1e6) f = k.d.uzaklik / 1e6;
    k.d.hedef = P + (k.d.hedef - P) * (1.0 / f);
    k.d.uzaklik /= f;
}

V3d CalismaDuzlemiNoktasi(const GorunumKamerasi& k, double px, double py, double g, double y, double calismaZ) {
    const Isin2 i = PikselIsini2(k, px, py, g, y);
    if (std::fabs(i.d.z) > 1e-12) {
        const double t = (calismaZ - i.o.z) / i.d.z;
        const V3d h = i.o + i.d * t;
        // Kameranın önünde ve makul uzaklıkta ise (ufka çok yakın düzlem noktaları atılır).
        const double derin = Nokta(h - k.Goz(), k.Ileri());
        if (t > 0 && (k.d.ortografik || (derin > YAKIN && derin < k.d.uzaklik * 50.0))) return h;
    }
    // Hedef derinliği: hedeften geçen görüntü düzlemi.
    const V3d f = k.Ileri();
    const double payda = Nokta(i.d, f);
    if (std::fabs(payda) < 1e-15) return k.d.hedef;
    return i.o + i.d * (Nokta(k.d.hedef - i.o, f) / payda);
}

std::string KameraJson(const KameraDurumu& d) {
    nlohmann::json j = {{"hedef", {d.hedef.x, d.hedef.y, d.hedef.z}},
                        {"uzaklik", d.uzaklik},
                        {"sapma_derece", d.sapma / DERECE},
                        {"egim_derece", d.egim / DERECE},
                        {"ortografik", d.ortografik},
                        {"orto_yukseklik", d.ortoYukseklik},
                        {"dikey_aci_derece", d.dikeyAci / DERECE}};
    return j.dump();
}

bool KameraJsonOku(std::string_view metin, KameraDurumu& d) {
    const nlohmann::json j = nlohmann::json::parse(metin, nullptr, false);
    if (j.is_discarded() || !j.is_object()) return false;
    KameraDurumu o = d;
    auto sayi = [&](const char* ad, double& v, double carpan = 1.0) {
        if (j.contains(ad) && j[ad].is_number() && std::isfinite(j[ad].get<double>())) v = j[ad].get<double>() * carpan;
    };
    if (j.contains("hedef") && j["hedef"].is_array() && j["hedef"].size() == 3) {
        const auto& h = j["hedef"];
        if (h[0].is_number() && h[1].is_number() && h[2].is_number()) o.hedef = {h[0], h[1], h[2]};
    }
    sayi("uzaklik", o.uzaklik);
    sayi("sapma_derece", o.sapma, DERECE);
    sayi("egim_derece", o.egim, DERECE);
    sayi("orto_yukseklik", o.ortoYukseklik);
    sayi("dikey_aci_derece", o.dikeyAci, DERECE);
    if (j.contains("ortografik") && j["ortografik"].is_boolean()) o.ortografik = j["ortografik"].get<bool>();
    o.uzaklik = std::clamp(o.uzaklik, 1e-3, 1e7);
    o.ortoYukseklik = std::clamp(o.ortoYukseklik, ORTO_EN_KUCUK, ORTO_EN_BUYUK);
    o.egim = std::clamp(o.egim, -90.0 * DERECE, 90.0 * DERECE);
    o.dikeyAci = std::clamp(o.dikeyAci, 5.0 * DERECE, 120.0 * DERECE);
    d = o;
    return true;
}

}  // namespace op4
