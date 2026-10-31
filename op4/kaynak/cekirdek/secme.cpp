// op4 çekirdek — seçme dizini (sözleşme S8; tam uygulama). Uygulayan: C (arayuz-goruntu), Faz 1 iş 1.4.
//
// BVH: öğe başına dünya kutusu (çubuk kapsülü / düğüm küresi / panel çokgeni), merkez noktalarına göre en uzun eksende
// ortadan bölme, yaprak ≤ 4 öğe. Ekran sorguları (EnYakin, Adaylar, Pencere) düğüm kutularının 8 köşesini izdüşürüp ekran
// dikdörtgeniyle eler; yakın düzlemin arkasına taşan kutu "belki" sayılır ve inilir. Öğe testleri kırpma uzayında yakın
// düzleme göre kırpılmış parçalarla yapılır (kameranın arkasına uzanan çubuk doğru çizilir ve seçilir).
#include "cekirdek/secme.h"

#include <algorithm>
#include <cmath>
#include <numeric>

namespace op4 {
namespace {

// 4×4 genel ters (kofaktör), double. Tekilse false.
bool Ters4(const std::array<double, 16>& m, std::array<double, 16>& t) {
    std::array<double, 16> inv{};
    inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
    inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
    inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
    inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
    inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
    inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
    inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
    inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
    inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
    inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
    inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
    inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
    inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
    inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
    inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
    inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];
    const double det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
    if (std::fabs(det) < 1e-300) return false;
    for (size_t i = 0; i < 16; ++i) t[i] = inv[i] / det;
    return true;
}

void Carp4(const std::array<double, 16>& m, const double v[4], double o[4]) {
    for (int r = 0; r < 4; ++r) o[r] = m[r * 4] * v[0] + m[r * 4 + 1] * v[1] + m[r * 4 + 2] * v[2] + m[r * 4 + 3] * v[3];
}

// Kırpma uzayı noktası. Görünür yarı uzay: h = w − z ≥ 0 (ters-Z yakın düzlem) ve w > 0.
struct K4 {
    double x, y, z, w;
};
K4 Kirp(const GorusIzdusumu& g, V3d p) {
    const double v[4] = {p.x, p.y, p.z, 1.0};
    double o[4];
    Carp4(g.gorunumIzdusum, v, o);
    return {o[0], o[1], o[2], o[3]};
}
inline double Yari(const K4& c) { return c.w - c.z; }
inline bool Onunde(const K4& c) { return c.w > 1e-12 && Yari(c) >= 0.0; }
inline K4 Ara(const K4& a, const K4& b, double t) {
    return {a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t, a.w + (b.w - a.w) * t};
}
struct E2 {
    double x, y;
};
inline E2 Ekran(const GorusIzdusumu& g, const K4& c) {
    return {(c.x / c.w * 0.5 + 0.5) * g.genislik, (0.5 - c.y / c.w * 0.5) * g.yukseklik};
}

// Doğru parçasını yakın düzleme göre kırpar; tamamen arkadaysa false. ta, tb: dünya parametresi (0..1).
bool ParcaKirp(K4& a, K4& b, double& ta, double& tb) {
    ta = 0;
    tb = 1;
    const double ha = std::min(Yari(a), a.w), hb = std::min(Yari(b), b.w);
    if (ha < 0 && hb < 0) return false;
    if (ha >= 0 && hb >= 0) return true;
    const double t = ha / (ha - hb);
    const K4 c = Ara(a, b, t);
    if (ha < 0) {
        a = c;
        ta = t;
    } else {
        b = c;
        tb = t;
    }
    return a.w > 1e-12 && b.w > 1e-12;
}

double NoktaParcaUzakligi(E2 p, E2 a, E2 b, double& s) {
    const double dx = b.x - a.x, dy = b.y - a.y, l2 = dx * dx + dy * dy;
    s = l2 > 1e-18 ? std::clamp(((p.x - a.x) * dx + (p.y - a.y) * dy) / l2, 0.0, 1.0) : 0.0;
    return std::hypot(p.x - (a.x + dx * s), p.y - (a.y + dy * s));
}

bool CokgenIcinde(const std::vector<E2>& c, E2 p) {
    bool ic = false;
    for (size_t i = 0, j = c.size() - 1; i < c.size(); j = i++)
        if ((c[i].y > p.y) != (c[j].y > p.y) && p.x < (c[j].x - c[i].x) * (p.y - c[i].y) / (c[j].y - c[i].y) + c[i].x) ic = !ic;
    return ic;
}

bool ParcalarKesisir(E2 a, E2 b, E2 c, E2 d) {
    auto yon = [](E2 p, E2 q, E2 r) { return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x); };
    const double d1 = yon(c, d, a), d2 = yon(c, d, b), d3 = yon(a, b, c), d4 = yon(a, b, d);
    return ((d1 > 0) != (d2 > 0)) && ((d3 > 0) != (d4 > 0));
}

struct Dikdortgen {
    double x0, y0, x1, y1;
    bool Icinde(E2 p) const { return p.x >= x0 && p.x <= x1 && p.y >= y0 && p.y <= y1; }
};

bool ParcaDikdortgeneDeger(E2 a, E2 b, const Dikdortgen& r) {
    if (r.Icinde(a) || r.Icinde(b)) return true;
    const E2 k[4] = {{r.x0, r.y0}, {r.x1, r.y0}, {r.x1, r.y1}, {r.x0, r.y1}};
    for (int i = 0; i < 4; ++i)
        if (ParcalarKesisir(a, b, k[i], k[(i + 1) % 4])) return true;
    return false;
}

// Öğe türü önceliği (EnYakin): düğüm > mesnet > çubuk > panel > aks.
enum OgeTuru : uint8_t { DUGUM = 0, MESNET = 1, CUBUK = 2, PANEL = 3, AKS = 4 };

struct Oge {
    ElemanKimligi kimlik;
    OgeTuru tur = DUGUM;
    uint32_t a = 0, b = 0;   // düğüm: düğüm dizini; çubuk: i, j düğüm dizinleri; panel: dizin; aks: aks dizini
    double yaricap = 0;      // ışın testi (m)
    Kutu3d kutu;
    V3d merkez;
};

struct BvhDugumu {
    Kutu3d kutu;
    uint32_t sol = 0;   // iç düğüm: sol çocuk dizini (sağ = sol + 1); yaprak: ilk öğe sırası
    uint32_t sayi = 0;  // yaprakta öğe sayısı; iç düğümde 0
};

bool Izinli(OgeTuru t, const SecmeAyari& a) {
    switch (t) {
        case DUGUM: return a.dugumler;
        case MESNET: return a.mesnetler;
        case CUBUK: return a.cubuklar;
        case PANEL: return a.paneller;
        case AKS: return a.akslar;
    }
    return false;
}

}  // namespace

bool GorusIzdusumu::Izdusur(V3d p, double& px, double& py) const {
    const K4 c = Kirp(*this, p);
    if (c.w <= 1e-12) return false;
    const E2 e = Ekran(*this, c);
    px = e.x;
    py = e.y;
    return true;
}

Isin PikselIsini(const GorusIzdusumu& g, double px, double py) {
    std::array<double, 16> t{};
    if (!Ters4(g.gorunumIzdusum, t)) return {g.goz, {0, 0, -1}};
    const double nx = px / g.genislik * 2.0 - 1.0, ny = 1.0 - py / g.yukseklik * 2.0;
    // Ters-Z: yakın düzlem derinlik 1, uzak (sonsuz) 0. İki noktayı geri izdüşür.
    auto geri = [&](double z) {
        const double v[4] = {nx, ny, z, 1.0};
        double o[4];
        Carp4(t, v, o);
        return o[3] != 0.0 ? V3d{o[0] / o[3], o[1] / o[3], o[2] / o[3]} : V3d{o[0], o[1], o[2]};
    };
    const V3d yakin = geri(1.0), uzak = geri(0.5);
    return {g.ortografik ? yakin : g.goz, Birim(uzak - yakin)};
}

struct SecmeDizini::Ic {
    SahnePtr sahne = BosSahne();
    std::vector<Oge> ogeler;
    std::vector<uint32_t> sira;      // BVH yaprak sırası → ogeler dizini
    std::vector<BvhDugumu> dugumler;

    void Kur();
    uint32_t Bol(uint32_t bas, uint32_t son);

    // Ekran testi: öğenin imlece uzaklığı (px) ve vuruş noktası; tolerans dışında / görünmezse false.
    bool EkranTesti(const Oge& o, const GorusIzdusumu& g, E2 m, double tol, SecmeVurusu& v) const;
    bool PencereTesti(const Oge& o, const GorusIzdusumu& g, const Dikdortgen& r, PencereKipi kip) const;
    bool IsinTesti(const Oge& o, const Isin& i, double& t, V3d& p) const;
    void PanelKoseleri(uint32_t panel, std::vector<V3d>& k) const;
    // Kutunun ekran sınırı; köşelerden biri yakın düzlemin arkasındaysa false (sınırsız).
    bool KutuEkrani(const GorusIzdusumu& g, const Kutu3d& k, Dikdortgen& r, bool& hepsiOnde) const;

    template <class F>
    void EkranGez(const GorusIzdusumu& g, const Dikdortgen& alan, F&& f) const;
};

void SecmeDizini::Ic::PanelKoseleri(uint32_t panel, std::vector<V3d>& k) const {
    k.clear();
    const SahnePaneli& p = sahne->paneller[panel];
    for (uint32_t i = 0; i < p.koseSayisi; ++i) {
        const uint32_t ki = p.koseBas + i;
        if (ki >= sahne->panelKoseleri.size()) break;
        const uint32_t d = sahne->panelKoseleri[ki];
        if (d < sahne->dugumler.size()) k.push_back(sahne->dugumler[d].p);
    }
}

void SecmeDizini::Ic::Kur() {
    ogeler.clear();
    sira.clear();
    dugumler.clear();
    const SahneAnlik& s = *sahne;
    const size_t n = s.dugumler.size();
    auto nokta = [&](uint32_t i) { return i < n ? s.dugumler[i].p : V3d{}; };
    for (uint32_t i = 0; i < n; ++i) {
        Oge o;
        o.kimlik = DugumKimligi(s.dugumler[i].no);
        o.tur = DUGUM;
        o.a = i;
        o.yaricap = 0.10;
        o.merkez = s.dugumler[i].p;
        ogeler.push_back(o);
    }
    for (const SahneMesnedi& m : s.mesnetler) {
        if (m.dugum >= n) continue;
        Oge o;
        o.kimlik = {ElemanTuru::Mesnet, 0, s.dugumler[m.dugum].no};
        o.tur = MESNET;
        o.a = m.dugum;
        o.yaricap = 0.15;
        o.merkez = s.dugumler[m.dugum].p;
        ogeler.push_back(o);
    }
    for (const SahneCubugu& c : s.cubuklar) {
        if (c.i >= n || c.j >= n) continue;
        Oge o;
        o.kimlik = CubukKimligi(c.no);
        o.tur = CUBUK;
        o.a = c.i;
        o.b = c.j;
        double r = 0.05;
        if (c.kesit < s.kesitler.size()) r = std::max(r, 0.5 * std::max(s.kesitler[c.kesit].h, s.kesitler[c.kesit].b));
        o.yaricap = r;
        o.merkez = (nokta(c.i) + nokta(c.j)) * 0.5;
        ogeler.push_back(o);
    }
    std::vector<V3d> k;
    for (uint32_t i = 0; i < s.paneller.size(); ++i) {
        PanelKoseleri(i, k);
        if (k.size() < 3) continue;
        Oge o;
        o.kimlik = PanelKimligi(s.paneller[i].no);
        o.tur = PANEL;
        o.a = i;
        o.yaricap = 0.0;
        V3d m{};
        for (const V3d& p : k) m = m + p;
        o.merkez = m * (1.0 / static_cast<double>(k.size()));
        ogeler.push_back(o);
    }
    for (uint32_t i = 0; i < s.akslar.size(); ++i) {
        Oge o;
        o.kimlik = s.akslar[i].kimlik;
        o.tur = AKS;
        o.a = i;
        o.yaricap = 0.05;
        o.merkez = (s.akslar[i].bas + s.akslar[i].son) * 0.5;
        ogeler.push_back(o);
    }
    for (Oge& o : ogeler) {
        switch (o.tur) {
            case DUGUM:
            case MESNET:
                o.kutu.Kapsa(nokta(o.a));
                break;
            case CUBUK:
                o.kutu.Kapsa(nokta(o.a));
                o.kutu.Kapsa(nokta(o.b));
                break;
            case PANEL:
                PanelKoseleri(o.a, k);
                for (const V3d& p : k) o.kutu.Kapsa(p);
                break;
            case AKS:
                o.kutu.Kapsa(s.akslar[o.a].bas);
                o.kutu.Kapsa(s.akslar[o.a].son);
                break;
        }
        const V3d r{o.yaricap, o.yaricap, o.yaricap};
        o.kutu.enKucuk = o.kutu.enKucuk - r;
        o.kutu.enBuyuk = o.kutu.enBuyuk + r;
    }
    sira.resize(ogeler.size());
    std::iota(sira.begin(), sira.end(), 0u);
    if (ogeler.empty()) return;
    dugumler.reserve(2 * ogeler.size() / 4 + 2);
    dugumler.push_back({});
    Bol(0, static_cast<uint32_t>(sira.size()));
}

// [bas, son) aralığı için düğüm kurar (kök dizini 0, çocuklar ardışık). Döndürür: düğüm dizini.
uint32_t SecmeDizini::Ic::Bol(uint32_t bas, uint32_t son) {
    // Yinelemeli yığınla (derin ağaçlarda özyineleme taşmasın).
    struct Is {
        uint32_t dugum, bas, son;
    };
    std::vector<Is> yigin{{0, bas, son}};
    while (!yigin.empty()) {
        const Is is = yigin.back();
        yigin.pop_back();
        Kutu3d kutu, merkezler;
        for (uint32_t i = is.bas; i < is.son; ++i) {
            kutu.Kapsa(ogeler[sira[i]].kutu);
            merkezler.Kapsa(ogeler[sira[i]].merkez);
        }
        dugumler[is.dugum].kutu = kutu;
        const uint32_t n = is.son - is.bas;
        if (n <= 4) {
            dugumler[is.dugum].sol = is.bas;
            dugumler[is.dugum].sayi = n;
            continue;
        }
        const V3d e = merkezler.enBuyuk - merkezler.enKucuk;
        const int eksen = e.x >= e.y && e.x >= e.z ? 0 : (e.y >= e.z ? 1 : 2);
        auto deger = [&](uint32_t i) {
            const V3d& m = ogeler[i].merkez;
            return eksen == 0 ? m.x : (eksen == 1 ? m.y : m.z);
        };
        const uint32_t orta = is.bas + n / 2;
        std::nth_element(sira.begin() + is.bas, sira.begin() + orta, sira.begin() + is.son,
                         [&](uint32_t a, uint32_t b) { return deger(a) < deger(b); });
        const uint32_t sol = static_cast<uint32_t>(dugumler.size());
        dugumler.push_back({});
        dugumler.push_back({});
        dugumler[is.dugum].sol = sol;
        dugumler[is.dugum].sayi = 0;
        yigin.push_back({sol, is.bas, orta});
        yigin.push_back({sol + 1, orta, is.son});
    }
    return 0;
}

bool SecmeDizini::Ic::KutuEkrani(const GorusIzdusumu& g, const Kutu3d& k, Dikdortgen& r, bool& hepsiOnde) const {
    r = {1e300, 1e300, -1e300, -1e300};
    hepsiOnde = true;
    bool herhangi = false;
    for (int i = 0; i < 8; ++i) {
        const V3d p{(i & 1) ? k.enBuyuk.x : k.enKucuk.x, (i & 2) ? k.enBuyuk.y : k.enKucuk.y,
                    (i & 4) ? k.enBuyuk.z : k.enKucuk.z};
        const K4 c = Kirp(g, p);
        if (!Onunde(c)) {
            hepsiOnde = false;
            continue;
        }
        herhangi = true;
        const E2 e = Ekran(g, c);
        r.x0 = std::min(r.x0, e.x);
        r.y0 = std::min(r.y0, e.y);
        r.x1 = std::max(r.x1, e.x);
        r.y1 = std::max(r.y1, e.y);
    }
    return herhangi;
}

template <class F>
void SecmeDizini::Ic::EkranGez(const GorusIzdusumu& g, const Dikdortgen& alan, F&& f) const {
    if (dugumler.empty()) return;
    uint32_t yigin[128];
    int n = 0;
    yigin[n++] = 0;
    while (n > 0) {
        const BvhDugumu& d = dugumler[yigin[--n]];
        Dikdortgen r;
        bool hepsiOnde;
        KutuEkrani(g, d.kutu, r, hepsiOnde);
        if (hepsiOnde && (r.x1 < alan.x0 || r.x0 > alan.x1 || r.y1 < alan.y0 || r.y0 > alan.y1)) continue;
        if (hepsiOnde && r.x1 < r.x0) continue;  // hiçbir köşe görünmüyor
        if (d.sayi > 0) {
            for (uint32_t i = 0; i < d.sayi; ++i) f(ogeler[sira[d.sol + i]]);
            continue;
        }
        if (n + 2 > 128) {  // aşırı derin ağaç (olmamalı): kalan alt ağacı düz gez
            for (const uint32_t s : sira) f(ogeler[s]);
            return;
        }
        yigin[n++] = d.sol;
        yigin[n++] = d.sol + 1;
    }
}

bool SecmeDizini::Ic::EkranTesti(const Oge& o, const GorusIzdusumu& g, E2 m, double tol, SecmeVurusu& v) const {
    const SahneAnlik& s = *sahne;
    switch (o.tur) {
        case DUGUM:
        case MESNET: {
            const V3d p = s.dugumler[o.a].p;
            const K4 c = Kirp(g, p);
            if (!Onunde(c)) return false;
            const E2 e = Ekran(g, c);
            const double u = std::hypot(e.x - m.x, e.y - m.y);
            if (u > tol) return false;
            v = {o.kimlik, p, c.w, u};
            return true;
        }
        case CUBUK:
        case AKS: {
            const V3d p0 = o.tur == CUBUK ? s.dugumler[o.a].p : s.akslar[o.a].bas;
            const V3d p1 = o.tur == CUBUK ? s.dugumler[o.b].p : s.akslar[o.a].son;
            K4 a = Kirp(g, p0), b = Kirp(g, p1);
            double ta, tb;
            if (!ParcaKirp(a, b, ta, tb)) return false;
            const E2 ea = Ekran(g, a), eb = Ekran(g, b);
            double sp;
            const double u = NoktaParcaUzakligi(m, ea, eb, sp);
            if (u > tol) return false;
            // Perspektif doğru ara değer: ekran parametresinden kırpılmış parça üzerindeki dünya parametresine.
            const double ia = 1.0 / a.w, ib = 1.0 / b.w;
            const double tk = (sp * ib) / ((1.0 - sp) * ia + sp * ib);
            const double t = ta + (tb - ta) * tk;
            const V3d p = p0 + (p1 - p0) * t;
            v = {o.kimlik, p, a.w + (b.w - a.w) * tk, u};
            return true;
        }
        case PANEL: {
            std::vector<V3d> k;
            PanelKoseleri(o.a, k);
            std::vector<K4> c;
            c.reserve(k.size());
            for (const V3d& p : k) c.push_back(Kirp(g, p));
            // Yakın düzlemle kırp (Sutherland–Hodgman).
            std::vector<K4> kc;
            for (size_t i = 0; i < c.size(); ++i) {
                const K4 &a = c[i], &b = c[(i + 1) % c.size()];
                const double ha = std::min(Yari(a), a.w), hb = std::min(Yari(b), b.w);
                if (ha >= 0) kc.push_back(a);
                if ((ha >= 0) != (hb >= 0)) kc.push_back(Ara(a, b, ha / (ha - hb)));
            }
            if (kc.size() < 3) return false;
            std::vector<E2> e;
            e.reserve(kc.size());
            for (const K4& q : kc) {
                if (q.w <= 1e-12) return false;
                e.push_back(Ekran(g, q));
            }
            double u = 0;
            if (!CokgenIcinde(e, m)) {
                u = 1e300;
                for (size_t i = 0; i < e.size(); ++i) {
                    double sp;
                    u = std::min(u, NoktaParcaUzakligi(m, e[i], e[(i + 1) % e.size()], sp));
                }
                if (u > tol) return false;
            }
            // Derinlik: ışının panel düzlemiyle kesişimi (Newell normali).
            V3d nn{};
            for (size_t i = 0; i < k.size(); ++i) {
                const V3d &a = k[i], &b = k[(i + 1) % k.size()];
                nn.x += (a.y - b.y) * (a.z + b.z);
                nn.y += (a.z - b.z) * (a.x + b.x);
                nn.z += (a.x - b.x) * (a.y + b.y);
            }
            nn = Birim(nn);
            const Isin is = PikselIsini(g, m.x, m.y);
            const double pd = Nokta(is.yon, nn);
            V3d p = o.merkez;
            double derin = Uzunluk(o.merkez - g.goz);
            if (std::fabs(pd) > 1e-12) {
                const double t = Nokta(o.merkez - is.baslangic, nn) / pd;
                if (t > 0) {
                    p = is.baslangic + is.yon * t;
                    derin = t;
                }
            }
            v = {o.kimlik, p, derin, u};
            return true;
        }
    }
    return false;
}

bool SecmeDizini::Ic::PencereTesti(const Oge& o, const GorusIzdusumu& g, const Dikdortgen& r, PencereKipi kip) const {
    const SahneAnlik& s = *sahne;
    auto nokta = [&](V3d p, E2& e) {
        const K4 c = Kirp(g, p);
        if (!Onunde(c)) return false;
        e = Ekran(g, c);
        return true;
    };
    switch (o.tur) {
        case DUGUM:
        case MESNET: {
            E2 e;
            return nokta(s.dugumler[o.a].p, e) && r.Icinde(e);
        }
        case CUBUK:
        case AKS: {
            const V3d p0 = o.tur == CUBUK ? s.dugumler[o.a].p : s.akslar[o.a].bas;
            const V3d p1 = o.tur == CUBUK ? s.dugumler[o.b].p : s.akslar[o.a].son;
            if (kip == PencereKipi::TamIcinde) {
                E2 a, b;
                return nokta(p0, a) && nokta(p1, b) && r.Icinde(a) && r.Icinde(b);
            }
            K4 a = Kirp(g, p0), b = Kirp(g, p1);
            double ta, tb;
            if (!ParcaKirp(a, b, ta, tb)) return false;
            return ParcaDikdortgeneDeger(Ekran(g, a), Ekran(g, b), r);
        }
        case PANEL: {
            std::vector<V3d> k;
            PanelKoseleri(o.a, k);
            std::vector<E2> e;
            for (const V3d& p : k) {
                E2 q;
                if (!nokta(p, q)) {
                    if (kip == PencereKipi::TamIcinde) return false;
                    continue;
                }
                e.push_back(q);
            }
            if (e.empty()) return false;
            if (kip == PencereKipi::TamIcinde) return std::all_of(e.begin(), e.end(), [&](E2 q) { return r.Icinde(q); });
            for (size_t i = 0; i < e.size(); ++i)
                if (ParcaDikdortgeneDeger(e[i], e[(i + 1) % e.size()], r)) return true;
            return e.size() >= 3 && CokgenIcinde(e, {(r.x0 + r.x1) * 0.5, (r.y0 + r.y1) * 0.5});
        }
    }
    return false;
}

bool SecmeDizini::Ic::IsinTesti(const Oge& o, const Isin& is, double& t, V3d& p) const {
    const SahneAnlik& s = *sahne;
    const V3d O = is.baslangic, D = is.yon;
    auto kure = [&](V3d c, double r) {
        const V3d oc = O - c;
        const double b = Nokta(oc, D), cc = Nokta(oc, oc) - r * r, d = b * b - cc;
        if (d < 0) return false;
        double tt = -b - std::sqrt(d);
        if (tt < 0) tt = -b + std::sqrt(d);
        if (tt < 0) return false;
        t = tt;
        p = O + D * tt;
        return true;
    };
    switch (o.tur) {
        case DUGUM:
        case MESNET:
            return kure(s.dugumler[o.a].p, o.yaricap);
        case CUBUK:
        case AKS: {
            const V3d A = o.tur == CUBUK ? s.dugumler[o.a].p : s.akslar[o.a].bas;
            const V3d B = o.tur == CUBUK ? s.dugumler[o.b].p : s.akslar[o.a].son;
            // Işın ile parça arasındaki en yakın noktalar; uzaklık ≤ r ise vurur (kapsül yaklaşımı).
            const V3d u = D, v = B - A, w = O - A;
            const double a = Nokta(u, u), b = Nokta(u, v), c = Nokta(v, v), d = Nokta(u, w), e = Nokta(v, w);
            const double den = a * c - b * b;
            double sc, tc;
            if (den < 1e-14 * a * c) {
                tc = std::clamp(e / std::max(c, 1e-300), 0.0, 1.0);
                sc = std::max(0.0, Nokta(A + v * tc - O, u) / a);
            } else {
                tc = std::clamp((a * e - b * d) / den, 0.0, 1.0);
                sc = std::max(0.0, Nokta(A + v * tc - O, u) / a);
            }
            const V3d pi = O + u * sc, pc = A + v * tc;
            if (Uzunluk(pi - pc) > o.yaricap) return false;
            t = sc;
            p = pc;
            return true;
        }
        case PANEL: {
            std::vector<V3d> k;
            PanelKoseleri(o.a, k);
            V3d nn{};
            for (size_t i = 0; i < k.size(); ++i) {
                const V3d &a = k[i], &b = k[(i + 1) % k.size()];
                nn.x += (a.y - b.y) * (a.z + b.z);
                nn.y += (a.z - b.z) * (a.x + b.x);
                nn.z += (a.x - b.x) * (a.y + b.y);
            }
            nn = Birim(nn);
            const double pd = Nokta(D, nn);
            if (std::fabs(pd) < 1e-12) return false;
            const double tt = Nokta(k[0] - O, nn) / pd;
            if (tt < 0) return false;
            const V3d h = O + D * tt;
            // Baskın eksen dışındaki iki koordinatta çokgen içi.
            const double ax = std::fabs(nn.x), ay = std::fabs(nn.y), az = std::fabs(nn.z);
            auto iki = [&](V3d q) -> E2 {
                if (az >= ax && az >= ay) return {q.x, q.y};
                if (ay >= ax) return {q.x, q.z};
                return {q.y, q.z};
            };
            std::vector<E2> c;
            for (const V3d& q : k) c.push_back(iki(q));
            if (!CokgenIcinde(c, iki(h))) return false;
            t = tt;
            p = h;
            return true;
        }
    }
    return false;
}

SecmeDizini::SecmeDizini() : ic_(std::make_unique<Ic>()) {}
SecmeDizini::~SecmeDizini() = default;
SecmeDizini::SecmeDizini(SecmeDizini&&) noexcept = default;
SecmeDizini& SecmeDizini::operator=(SecmeDizini&&) noexcept = default;

void SecmeDizini::Kur(SahnePtr sahne) {
    ic_->sahne = sahne ? std::move(sahne) : BosSahne();
    ic_->Kur();
}
uint64_t SecmeDizini::SahneSurumu() const { return ic_->sahne->surum; }
const SahnePtr& SecmeDizini::Sahne() const { return ic_->sahne; }

namespace {
bool VurusOnce(const SecmeVurusu& a, OgeTuru ta, const SecmeVurusu& b, OgeTuru tb) {
    if (ta != tb) return ta < tb;
    if (a.ekranUzakligiPx != b.ekranUzakligiPx) return a.ekranUzakligiPx < b.ekranUzakligiPx;
    if (a.derinlik != b.derinlik) return a.derinlik < b.derinlik;
    return a.kimlik < b.kimlik;
}
OgeTuru TurOncelik(ElemanTuru t) {
    switch (t) {
        case ElemanTuru::Dugum: return DUGUM;
        case ElemanTuru::Mesnet: return MESNET;
        case ElemanTuru::Cubuk: return CUBUK;
        case ElemanTuru::Panel: return PANEL;
        default: return AKS;
    }
}
}  // namespace

std::vector<SecmeVurusu> SecmeDizini::Adaylar(const GorusIzdusumu& g, double px, double py, const SecmeAyari& a) const {
    std::vector<SecmeVurusu> o;
    const double tol = a.tolPx * std::max(0.25, g.dpiOlcek);
    const E2 m{px, py};
    ic_->EkranGez(g, {px - tol, py - tol, px + tol, py + tol}, [&](const Oge& og) {
        if (!Izinli(og.tur, a)) return;
        SecmeVurusu v;
        if (ic_->EkranTesti(og, g, m, tol, v)) o.push_back(v);
    });
    std::sort(o.begin(), o.end(), [](const SecmeVurusu& x, const SecmeVurusu& y) {
        return VurusOnce(x, TurOncelik(x.kimlik.tur), y, TurOncelik(y.kimlik.tur));
    });
    return o;
}

std::optional<SecmeVurusu> SecmeDizini::EnYakin(const GorusIzdusumu& g, double px, double py, const SecmeAyari& a) const {
    std::optional<SecmeVurusu> en;
    OgeTuru enTur = AKS;
    const double tol = a.tolPx * std::max(0.25, g.dpiOlcek);
    const E2 m{px, py};
    ic_->EkranGez(g, {px - tol, py - tol, px + tol, py + tol}, [&](const Oge& og) {
        if (!Izinli(og.tur, a)) return;
        if (en && og.tur > enTur) return;  // düşük öncelikli tür: test etmeye gerek yok
        SecmeVurusu v;
        if (!ic_->EkranTesti(og, g, m, tol, v)) return;
        if (!en || VurusOnce(v, og.tur, *en, enTur)) {
            en = v;
            enTur = og.tur;
        }
    });
    return en;
}

std::vector<ElemanKimligi> SecmeDizini::Pencere(const GorusIzdusumu& g, double x0, double y0, double x1, double y1,
                                                PencereKipi kip, const SecmeAyari& a) const {
    const Dikdortgen r{std::min(x0, x1), std::min(y0, y1), std::max(x0, x1), std::max(y0, y1)};
    std::vector<ElemanKimligi> o;
    ic_->EkranGez(g, r, [&](const Oge& og) {
        if (Izinli(og.tur, a) && ic_->PencereTesti(og, g, r, kip)) o.push_back(og.kimlik);
    });
    std::sort(o.begin(), o.end());
    o.erase(std::unique(o.begin(), o.end()), o.end());
    return o;
}

std::optional<SecmeVurusu> SecmeDizini::IsinVurusu(const Isin& is, const SecmeAyari& a) const {
    if (ic_->dugumler.empty()) return std::nullopt;
    const V3d D = is.yon, O = is.baslangic;
    const V3d inv{1.0 / (D.x != 0 ? D.x : 1e-300), 1.0 / (D.y != 0 ? D.y : 1e-300), 1.0 / (D.z != 0 ? D.z : 1e-300)};
    auto kutuVurur = [&](const Kutu3d& k, double enUzak) {
        double t0 = 0, t1 = enUzak;
        const double o[3] = {O.x, O.y, O.z}, iv[3] = {inv.x, inv.y, inv.z};
        const double lo[3] = {k.enKucuk.x, k.enKucuk.y, k.enKucuk.z}, hi[3] = {k.enBuyuk.x, k.enBuyuk.y, k.enBuyuk.z};
        for (int i = 0; i < 3; ++i) {
            double ta = (lo[i] - o[i]) * iv[i], tb = (hi[i] - o[i]) * iv[i];
            if (ta > tb) std::swap(ta, tb);
            t0 = std::max(t0, ta);
            t1 = std::min(t1, tb);
            if (t0 > t1) return false;
        }
        return true;
    };
    std::optional<SecmeVurusu> en;
    double enT = 1e300;
    uint32_t yigin[128];
    int n = 0;
    yigin[n++] = 0;
    while (n > 0) {
        const BvhDugumu& d = ic_->dugumler[yigin[--n]];
        if (!kutuVurur(d.kutu, enT)) continue;
        if (d.sayi > 0) {
            for (uint32_t i = 0; i < d.sayi; ++i) {
                const Oge& og = ic_->ogeler[ic_->sira[d.sol + i]];
                if (!Izinli(og.tur, a)) continue;
                double t;
                V3d p;
                if (ic_->IsinTesti(og, is, t, p) && t < enT) {
                    enT = t;
                    en = SecmeVurusu{og.kimlik, p, t, 0.0};
                }
            }
            continue;
        }
        if (n + 2 > 128) break;
        yigin[n++] = d.sol;
        yigin[n++] = d.sol + 1;
    }
    return en;
}

Kutu3d SecmeDizini::Sinir(const std::vector<ElemanKimligi>& kimlikler) const {
    Kutu3d k;
    for (const ElemanKimligi& e : kimlikler) k.Kapsa(ic_->sahne->Sinir(e));
    return k;
}

}  // namespace op4
