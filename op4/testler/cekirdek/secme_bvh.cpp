// C (arayuz-goruntu) sınamaları — CPU BVH seçme dizini (sözleşme S8; MIMARI §6.9, §7.1; kabul C6).
#include <doctest/doctest.h>

#include <chrono>
#include <cmath>
#include <cstdio>
#include <memory>
#include <random>

#include "cekirdek/kamera.h"
#include "cekirdek/secme.h"

using namespace op4;

namespace {

// nx × ny açıklıklı, nz katlı çerçeve: düğümler, kolonlar, iki yönde kirişler, zeminde mesnetler, en üstte döşeme panelleri.
SahnePtr Cerceve(int nx, int ny, int nz, double a = 6.0, double h = 4.0, bool panel = true) {
    auto s = std::make_shared<SahneAnlik>();
    s->surum = 7;
    s->baslik = "Sınama çerçevesi";
    auto dno = [&](int i, int j, int k) { return static_cast<uint32_t>((k * (ny + 1) + j) * (nx + 1) + i); };
    for (int k = 0; k <= nz; ++k)
        for (int j = 0; j <= ny; ++j)
            for (int i = 0; i <= nx; ++i) {
                SahneDugumu d;
                d.no = dno(i, j, k) + 1;
                d.p = {i * a, j * a, k * h};
                s->dugumler.push_back(d);
            }
    uint32_t no = 1;
    auto cubuk = [&](uint32_t i, uint32_t j, CubukTuru t) {
        SahneCubugu c;
        c.no = no++;
        c.i = i;
        c.j = j;
        c.tur = t;
        s->cubuklar.push_back(c);
    };
    for (int k = 0; k < nz; ++k)
        for (int j = 0; j <= ny; ++j)
            for (int i = 0; i <= nx; ++i) cubuk(dno(i, j, k), dno(i, j, k + 1), CubukTuru::Kolon);
    for (int k = 1; k <= nz; ++k)
        for (int j = 0; j <= ny; ++j)
            for (int i = 0; i <= nx; ++i) {
                if (i < nx) cubuk(dno(i, j, k), dno(i + 1, j, k), CubukTuru::Kiris);
                if (j < ny) cubuk(dno(i, j, k), dno(i, j + 1, k), CubukTuru::Kiris);
            }
    for (int j = 0; j <= ny; ++j)
        for (int i = 0; i <= nx; ++i) s->mesnetler.push_back({dno(i, j, 0), 0x3F, MesnetTuru::Ankastre});
    if (panel) {
        uint32_t pno = 1;
        for (int j = 0; j < ny; ++j)
            for (int i = 0; i < nx; ++i) {
                SahnePaneli p;
                p.no = pno++;
                p.koseBas = static_cast<uint32_t>(s->panelKoseleri.size());
                p.koseSayisi = 4;
                for (const uint32_t d : {dno(i, j, nz), dno(i + 1, j, nz), dno(i + 1, j + 1, nz), dno(i, j + 1, nz)})
                    s->panelKoseleri.push_back(d);
                s->paneller.push_back(p);
            }
    }
    s->DizinleriKur();
    return s;
}

GorunumKamerasi Plan(const SahneAnlik& s, double g, double y) {
    GorunumKamerasi k;
    StandartYonUygula(k, StandartYon::Plan);
    k.Sigdir(s.sinir, g, y);
    return k;
}

}  // namespace

TEST_CASE("BVH: imlecin altındaki çubuk, 4 px tolerans (DPI ölçekli), düğüm önceliği") {
    const SahnePtr s = Cerceve(3, 2, 2, 6.0, 4.0, false);
    SecmeDizini d;
    d.Kur(s);
    CHECK(d.SahneSurumu() == 7);
    GorunumKamerasi k;
    StandartYonUygula(k, StandartYon::On);
    k.Sigdir(s->sinir, 1000, 600);
    GorusIzdusumu g = k.Izdusum(1000, 600);
    // Ön görünümde (x, z) kiriş: kat 1, x = 6..12 (i = 1), y = 0 — ortasının ekran konumu.
    double x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    REQUIRE(g.Izdusur({6, 0, 4}, x0, y0));
    REQUIRE(g.Izdusur({12, 0, 4}, x1, y1));
    const double mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
    SecmeAyari a;
    auto v = d.EnYakin(g, mx, my + 3.5, a);
    REQUIRE(v);
    CHECK(v->kimlik.tur == ElemanTuru::Cubuk);
    const SahneCubugu& c = s->cubuklar[*s->CubukDizini(v->kimlik.no)];
    CHECK(s->dugumler[c.i].p.z == 4);
    CHECK(s->dugumler[c.j].p.z == 4);
    CHECK(v->ekranUzakligiPx == doctest::Approx(3.5).epsilon(1e-6));
    CHECK(std::fabs(v->nokta.z - 4.0) < 1e-6);
    // Ön görünümde aynı x–z doğrusundaki kirişlerden en öndeki (y = 0) seçilir.
    CHECK(s->dugumler[c.i].p.y == 0);
    // Tolerans dışı → yok; DPI 2'de tolerans 8 px.
    CHECK_FALSE(d.EnYakin(g, mx, my + 5.0, a));
    g.dpiOlcek = 2.0;
    CHECK(d.EnYakin(g, mx, my + 5.0, a));
    g.dpiOlcek = 1.0;
    // Düğüm önceliği: kiriş ucunun 2 px yakınında düğüm seçilir.
    v = d.EnYakin(g, x0 + 2, y0, a);
    REQUIRE(v);
    CHECK(v->kimlik.tur == ElemanTuru::Dugum);
    // Seçilebilirlik süzgeci: düğümler kapalıysa çubuk.
    a.dugumler = false;
    v = d.EnYakin(g, x0 + 2, y0, a);
    REQUIRE(v);
    CHECK(v->kimlik.tur == ElemanTuru::Cubuk);
    // Adaylar: aynı noktadaki bütün elemanlar EnYakin sırasıyla.
    a.dugumler = true;
    const auto aday = d.Adaylar(g, x0, y0, a);
    REQUIRE(aday.size() >= 3);
    CHECK(aday.front().kimlik.tur == ElemanTuru::Dugum);
    CHECK(aday.back().kimlik.tur == ElemanTuru::Cubuk);
}

TEST_CASE("BVH: pencere seçimi — soldan sağa tam içinde, sağdan sola değen") {
    const SahnePtr s = Cerceve(3, 2, 2, 6.0, 4.0, false);
    SecmeDizini d;
    d.Kur(s);
    GorunumKamerasi k;
    StandartYonUygula(k, StandartYon::On);
    k.Sigdir(s->sinir, 1000, 600);
    const GorusIzdusumu g = k.Izdusum(1000, 600);
    double ax = 0, ay = 0, bx = 0, by = 0;
    REQUIRE(g.Izdusur({-1, 0, 4.5}, ax, ay));  // sol üst: x −1, z 4,5
    REQUIRE(g.Izdusur({7, 0, -0.5}, bx, by));   // sağ alt: x 7, z −0,5
    SecmeAyari a;
    a.dugumler = false;
    a.mesnetler = false;
    const auto tam = d.Pencere(g, ax, ay, bx, by, PencereKipi::TamIcinde, a);
    const auto degen = d.Pencere(g, ax, ay, bx, by, PencereKipi::Degen, a);
    // Tam içinde: x = 0 ve x = 6 kolonları (3 y aksı × 1 kat = 6) + kat 1'de x 0–6 kirişleri (y 0..2: 3) + kat 1 y yönü
    // kirişleri x = 0 ve 6'da (ekranda tek noktaya izdüşer ama içinde) 2 × 2 = 4 → 13.
    CHECK(tam.size() == 13);
    CHECK(degen.size() > tam.size());
    for (const ElemanKimligi& e : tam) CHECK(std::binary_search(degen.begin(), degen.end(), e));
    // Sıralı ve tekrarsız.
    CHECK(std::is_sorted(degen.begin(), degen.end()));
    CHECK(std::adjacent_find(degen.begin(), degen.end()) == degen.end());
}

TEST_CASE("BVH: panel çokgeni, ışın vuruşu ve kameranın arkasına taşan çubuk") {
    const SahnePtr s = Cerceve(2, 2, 1);
    SecmeDizini d;
    d.Kur(s);
    GorunumKamerasi k = Plan(*s, 800, 600);
    const GorusIzdusumu g = k.Izdusum(800, 600);
    double px = 0, py = 0;
    REQUIRE(g.Izdusur({3, 3, 4}, px, py));  // ilk döşeme panelinin ortası
    SecmeAyari a;
    const auto v = d.EnYakin(g, px, py, a);
    REQUIRE(v);
    CHECK(v->kimlik == PanelKimligi(1));
    CHECK(v->nokta.z == doctest::Approx(4.0));
    // Işın vuruşu: plandan aşağı bakan ışın önce panele vurur.
    const auto iv = d.IsinVurusu(PikselIsini(g, px, py), a);
    REQUIRE(iv);
    CHECK(iv->kimlik == PanelKimligi(1));
    // Paneller kapalıyken kolonun ucundaki düğüme (ya da kolona) ulaşır.
    a.paneller = false;
    double cx = 0, cy = 0;
    REQUIRE(g.Izdusur({6, 6, 4}, cx, cy));
    const auto iv2 = d.IsinVurusu(PikselIsini(g, cx, cy), a);
    REQUIRE(iv2);
    CHECK(iv2->nokta.z == doctest::Approx(4.0).epsilon(0.05));
    // Perspektif: göz bir kirişin üstünde, kiriş kameranın arkasına uzanıyor; yine de seçilebilir.
    GorunumKamerasi p;
    p.d.hedef = {3, 0, 4};  // y = 0 aksındaki x kirişi (0 → 6) gözün arkasına (x ≈ 5,95) uzanır
    p.d.uzaklik = 3;
    p.d.sapma = 0;
    p.d.egim = 10 * DERECE;
    const GorusIzdusumu gp = p.Izdusum(800, 600);
    double qx = 0, qy = 0;
    REQUIRE(gp.Izdusur({3, 0, 4}, qx, qy));
    SecmeAyari b;
    b.dugumler = b.paneller = b.mesnetler = false;
    const auto vp = d.EnYakin(gp, qx, qy, b);
    REQUIRE(vp);
    CHECK(vp->kimlik.tur == ElemanTuru::Cubuk);
}

TEST_CASE("BVH başarımı: 100 bin elemanda üzerine gelme (MIMARI §6.13, ≤ 1 ms)") {
    // 50 × 40 × 16: ~ 35 bin düğüm + ~ 100 bin çubuk.
    const SahnePtr s = Cerceve(50, 40, 16, 6.0, 4.0, false);
    REQUIRE(s->cubuklar.size() + s->dugumler.size() > 100000);
    SecmeDizini d;
    const auto t0 = std::chrono::steady_clock::now();
    d.Kur(s);
    const double kurMs = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    GorunumKamerasi k;
    StandartYonUygula(k, StandartYon::Izometrik);
    k.Sigdir(s->sinir, 1920, 1080);
    const GorusIzdusumu g = k.Izdusum(1920, 1080);
    std::mt19937 r(3);
    std::uniform_real_distribution<double> ux(0, 1920), uy(0, 1080);
    SecmeAyari a;
    int bulunan = 0;
    const int N = 400;
    const auto t1 = std::chrono::steady_clock::now();
    for (int i = 0; i < N; ++i)
        if (d.EnYakin(g, ux(r), uy(r), a)) ++bulunan;
    const double ortMs = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t1).count() / N;
    std::printf("OP4OLCUM senaryo=bvh eleman=%zu kur_ms=%.1f uzerine_gelme_ort_ms=%.4f bulunan=%d/%d\n",
                s->cubuklar.size() + s->dugumler.size(), kurMs, ortMs, bulunan, N);
    CHECK(bulunan > 0);
#if defined(NDEBUG) && !defined(__SANITIZE_ADDRESS__)
    CHECK(ortMs <= 1.0);
#else
    CHECK(ortMs <= 25.0);  // hata ayıklama / denetleyicili derlemede gevşek sınır; asıl bütçe sürüm derlemesinde
#endif
}
