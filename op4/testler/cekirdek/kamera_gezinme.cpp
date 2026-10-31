// C (arayuz-goruntu) sınamaları — görünüm kamerası ve gezinme (MIMARI §7.2, §7.4 K1/K3/K4, §25 fare eşlemesi).
#include <doctest/doctest.h>

#include <cmath>
#include <cstdio>
#include <random>

#include "cekirdek/gezinme.h"
#include "cekirdek/kamera.h"

using namespace op4;

namespace {

constexpr double G = 1280, Y = 720;

GorunumKamerasi Kamera3B() {
    GorunumKamerasi k;
    k.d.hedef = {9, 12, 5};
    k.d.uzaklik = 55;
    k.d.sapma = -127 * DERECE;
    k.d.egim = 23 * DERECE;
    return k;
}

double Kayma(const GorunumKamerasi& k, V3d P, double mx, double my) {
    double x, y;
    if (!k.Izdusum(G, Y).Izdusur(P, x, y)) return 1e9;
    return std::hypot(x - mx, y - my);
}

bool AyniKamera(const KameraDurumu& a, const KameraDurumu& b, double tol) {
    return std::fabs(a.hedef.x - b.hedef.x) <= tol && std::fabs(a.hedef.y - b.hedef.y) <= tol &&
           std::fabs(a.hedef.z - b.hedef.z) <= tol && std::fabs(a.uzaklik - b.uzaklik) <= tol &&
           std::fabs(a.sapma - b.sapma) <= tol && std::fabs(a.egim - b.egim) <= tol &&
           std::fabs(a.ortoYukseklik - b.ortoYukseklik) <= tol;
}

}  // namespace

TEST_CASE("kamera: izdüşüm ve analitik ışın tutarlı; eksenler dik") {
    GorunumKamerasi k = Kamera3B();
    const GorusIzdusumu g = k.Izdusum(G, Y);
    double x, y;
    REQUIRE(g.Izdusur(k.d.hedef, x, y));
    CHECK(x == doctest::Approx(G / 2).epsilon(1e-9));
    CHECK(y == doctest::Approx(Y / 2).epsilon(1e-9));
    CHECK(std::fabs(Nokta(k.Sag(), k.Ileri())) < 1e-12);
    CHECK(std::fabs(Nokta(k.Yukari(), k.Ileri())) < 1e-12);
    CHECK(k.Yukari().z > 0);
    // Piksel ışını (ters matris) ile çalışma düzlemi noktası aynı yerde.
    const V3d p = CalismaDuzlemiNoktasi(k, 300, 500, G, Y);
    CHECK(std::fabs(p.z) < 1e-9);
    REQUIRE(g.Izdusur(p, x, y));
    CHECK(std::hypot(x - 300, y - 500) < 1e-6);
    const Isin i = PikselIsini(g, 300, 500);
    const double t = -i.baslangic.z / i.yon.z;
    const V3d q = i.baslangic + i.yon * t;
    CHECK(Uzunluk(q - p) < 1e-6);
}

TEST_CASE("K1 kaydırma: 300 adımlık rastgele yolda P imleçte (≤ 0,5 px), son konum yoldan bağımsız") {
    for (int kip = 0; kip < 2; ++kip) {
        CAPTURE(kip);
        GorunumKamerasi k = Kamera3B();
        if (kip == 1) StandartYonUygula(k, StandartYon::Plan);
        const double mx0 = 640.3, my0 = 361.7;
        const V3d P = CalismaDuzlemiNoktasi(k, mx0, my0, G, Y);
        KameraSuruklemesi s;
        s.Basla(k, SuruklemeTuru::Kaydir, mx0, my0, P, G, Y);
        std::mt19937 r(42 + kip);
        std::uniform_real_distribution<double> d(-9.0, 9.0);
        double mx = mx0, my = my0, enBuyuk = 0;
        for (int i = 0; i < 300; ++i) {
            mx = std::clamp(mx + d(r), 20.0, G - 20);
            my = std::clamp(my + d(r), 20.0, Y - 20);
            s.Guncelle(k, mx, my);
            enBuyuk = std::max(enBuyuk, Kayma(k, P, mx, my));
        }
        CHECK(enBuyuk <= 0.5);
        CHECK(enBuyuk < 1e-6);  // mutlak çapa: kayma yalnız yuvarlama hatası
        const KameraDurumu yoldan = k.d;
        GorunumKamerasi k2 = Kamera3B();
        if (kip == 1) StandartYonUygula(k2, StandartYon::Plan);
        KameraSuruklemesi s2;
        s2.Basla(k2, SuruklemeTuru::Kaydir, mx0, my0, P, G, Y);
        s2.Guncelle(k2, mx, my);
        CHECK(AyniKamera(yoldan, k2.d, 1e-9));
        std::printf("OP4OLCUM senaryo=kamera_k1 kip=%s en_buyuk_kayma_px=%.3g\n", kip ? "plan" : "3b", enBuyuk);
    }
}

TEST_CASE("K3 yakınlaştırma: imlecin altındaki nokta sabit (perspektif ve ortografik, kesirli tekerlek)") {
    for (int kip = 0; kip < 2; ++kip) {
        GorunumKamerasi k = Kamera3B();
        if (kip == 1) StandartYonUygula(k, StandartYon::Plan);
        const double mx = 211.0, my = 533.0;
        const V3d P = CalismaDuzlemiNoktasi(k, mx, my, G, Y);
        double enBuyuk = 0;
        for (const double adim : {1.0, 2.0, 0.37, -1.5, 3.0, -0.25, 5.0}) {
            Yakinlas(k, adim, P);
            enBuyuk = std::max(enBuyuk, Kayma(k, P, mx, my));
        }
        CAPTURE(kip);
        CHECK(enBuyuk <= 0.5);
        CHECK(enBuyuk < 1e-6);
    }
    // Sınır: P'ye en az 0,05 m.
    GorunumKamerasi k = Kamera3B();
    const V3d P = k.d.hedef;
    for (int i = 0; i < 200; ++i) Yakinlas(k, 3.0, P);
    CHECK(Uzunluk(k.Goz() - P) >= 0.05 - 1e-12);
}

TEST_CASE("K4 döndürme: merkez P ekranda sabit (≤ 0,5 px); eğim sınırı; Δsapma = −k·Δx") {
    GorunumKamerasi k = Kamera3B();
    const double mx0 = 700, my0 = 300;
    const V3d P = CalismaDuzlemiNoktasi(k, mx0, my0, G, Y);
    double px0, py0;
    REQUIRE(k.Izdusum(G, Y).Izdusur(P, px0, py0));
    KameraSuruklemesi s;
    s.Basla(k, SuruklemeTuru::Dondur, mx0, my0, P, G, Y);
    std::mt19937 r(7);
    std::uniform_real_distribution<double> d(-15.0, 15.0);
    double mx = mx0, my = my0, enBuyuk = 0;
    for (int i = 0; i < 300; ++i) {
        mx += d(r);
        my += d(r);
        s.Guncelle(k, mx, my);
        enBuyuk = std::max(enBuyuk, Kayma(k, P, px0, py0));
        CHECK(std::fabs(k.d.egim) <= KameraSuruklemesi::EGIM_SINIRI + 1e-12);
    }
    CHECK(enBuyuk <= 0.5);
    std::printf("OP4OLCUM senaryo=kamera_k4 en_buyuk_kayma_px=%.3g\n", enBuyuk);
    GorunumKamerasi k2 = Kamera3B();
    KameraSuruklemesi s2;
    s2.Basla(k2, SuruklemeTuru::Dondur, 100, 100, P, G, Y);
    s2.Guncelle(k2, 140, 100);
    CHECK(k2.d.sapma - Kamera3B().d.sapma == doctest::Approx(-40 * KameraSuruklemesi::DONME_K));
    s2.Guncelle(k2, 100, 100 + 100000);  // aşırı eğim kırpılır
    CHECK(k2.d.egim == doctest::Approx(KameraSuruklemesi::EGIM_SINIRI));
}

TEST_CASE("standart görünümler ve sığdır") {
    GorunumKamerasi k;
    StandartYonUygula(k, StandartYon::Plan);
    CHECK(k.d.ortografik);
    CHECK(k.Sag().x == doctest::Approx(1));
    CHECK(k.Yukari().y == doctest::Approx(1));
    StandartYonUygula(k, StandartYon::On);
    CHECK(k.Sag().x == doctest::Approx(1));
    CHECK(k.Yukari().z == doctest::Approx(1));
    StandartYonUygula(k, StandartYon::Yan);
    CHECK(k.Sag().y == doctest::Approx(1));
    CHECK(k.Yukari().z == doctest::Approx(1));
    Kutu3d kutu;
    kutu.Kapsa(V3d{0, 0, 0});
    kutu.Kapsa(V3d{18, 24, 13.5});
    for (const StandartYon y : {StandartYon::Izometrik, StandartYon::Plan, StandartYon::On, StandartYon::Yan}) {
        CAPTURE(static_cast<int>(y));
        StandartYonUygula(k, y);
        k.Sigdir(kutu, G, Y);
        const GorusIzdusumu g = k.Izdusum(G, Y);
        double x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
        for (int i = 0; i < 8; ++i) {
            const V3d p{(i & 1) ? 18.0 : 0.0, (i & 2) ? 24.0 : 0.0, (i & 4) ? 13.5 : 0.0};
            double x, yy;
            REQUIRE(g.Izdusur(p, x, yy));
            x0 = std::min(x0, x);
            x1 = std::max(x1, x);
            y0 = std::min(y0, yy);
            y1 = std::max(y1, yy);
        }
        CHECK(x0 >= -0.5);
        CHECK(x1 <= G + 0.5);
        CHECK(y0 >= -0.5);
        CHECK(y1 <= Y + 0.5);
        CHECK(std::max(x1 - x0, (y1 - y0) * G / Y) > 0.7 * G);  // görüş alanını dolduruyor
    }
}

TEST_CASE("kamera JSON gidiş-dönüşü") {
    GorunumKamerasi k = Kamera3B();
    k.d.ortografik = true;
    k.d.ortoYukseklik = 33.5;
    KameraDurumu o;
    REQUIRE(KameraJsonOku(KameraJson(k.d), o));
    CHECK(AyniKamera(o, k.d, 1e-9));
    CHECK(o.ortografik);
    CHECK_FALSE(KameraJsonOku("bozuk", o));
}

TEST_CASE("gezinme: sol sürükle kaydırır, Shift + sol döndürür, eşik, tık ve pencere seçimi (op4 eşlemesi)") {
    GorunumKamerasi k = Kamera3B();
    Gezinme gz;
    gz.Boyut(G, Y);
    int tik = 0;
    SecimKipi sonKip = SecimKipi::Yeni;
    int pencere = 0;
    PencereKipi sonPk = PencereKipi::TamIcinde;
    gz.baglanti.tikla = [&](double, double, SecimKipi s) {
        ++tik;
        sonKip = s;
    };
    gz.baglanti.pencere = [&](double, double, double, double, PencereKipi pk, SecimKipi s) {
        ++pencere;
        sonPk = pk;
        sonKip = s;
    };
    // Eşik altı hareket + bırak = tık (yeni seçim); kamera değişmez.
    const KameraDurumu c0 = k.d;
    gz.Bas(k, FareTusu::Sol, 400, 300, {});
    gz.Hareket(k, 402, 301, {});
    gz.Birak(k, FareTusu::Sol, 402, 301, {});
    CHECK(tik == 1);
    CHECK(sonKip == SecimKipi::Yeni);
    CHECK(AyniKamera(c0, k.d, 0));
    // Ctrl + tık tersler, Shift + tık çıkarır.
    gz.Bas(k, FareTusu::Sol, 400, 300, {true, false, false});
    gz.Birak(k, FareTusu::Sol, 400, 300, {true, false, false});
    CHECK(sonKip == SecimKipi::Tersle);
    gz.Bas(k, FareTusu::Sol, 400, 300, {false, true, false});
    gz.Birak(k, FareTusu::Sol, 400, 300, {false, true, false});
    CHECK(sonKip == SecimKipi::Cikar);
    CHECK(tik == 3);
    // Sol sürükle: kaydır; basış noktasının altındaki nokta imleci izler.
    const V3d P = CalismaDuzlemiNoktasi(k, 400, 300, G, Y);
    gz.Bas(k, FareTusu::Sol, 400, 300, {});
    for (int i = 1; i <= 40; ++i) gz.Hareket(k, 400 + 3 * i, 300 + i, {});
    CHECK(gz.Surukluyor());
    CHECK(gz.Tur() == SuruklemeTuru::Kaydir);
    CHECK(Kayma(k, P, 520, 340) < 1e-6);
    gz.Birak(k, FareTusu::Sol, 520, 340, {});
    CHECK_FALSE(gz.Surukluyor());
    CHECK(tik == 3);
    CHECK(c0.sapma == k.d.sapma);
    // Shift + sol sürükle: döndür.
    const double s0 = k.d.sapma;
    gz.Bas(k, FareTusu::Sol, 500, 300, {false, true, false});
    gz.Hareket(k, 560, 300, {false, true, false});
    CHECK(gz.Tur() == SuruklemeTuru::Dondur);
    gz.Birak(k, FareTusu::Sol, 560, 300, {false, true, false});
    CHECK(k.d.sapma == doctest::Approx(s0 - 60 * KameraSuruklemesi::DONME_K));
    // Ctrl + sol sürükle: pencere seçimi (soldan sağa tam içinde, sağdan sola değen); kamera değişmez.
    const KameraDurumu c1 = k.d;
    gz.Bas(k, FareTusu::Sol, 100, 100, {true, false, false});
    gz.Hareket(k, 300, 250, {true, false, false});
    CHECK(gz.PencereSeciyor());
    gz.Birak(k, FareTusu::Sol, 300, 250, {true, false, false});
    CHECK(pencere == 1);
    CHECK(sonPk == PencereKipi::TamIcinde);
    CHECK(sonKip == SecimKipi::Ekle);
    gz.Bas(k, FareTusu::Sol, 300, 100, {true, true, false});
    gz.Hareket(k, 100, 250, {true, true, false});
    gz.Birak(k, FareTusu::Sol, 100, 250, {true, true, false});
    CHECK(pencere == 2);
    CHECK(sonPk == PencereKipi::Degen);
    CHECK(sonKip == SecimKipi::Cikar);
    CHECK(AyniKamera(c1, k.d, 0));
    // Orta sürükle eşiksiz kaydırır; plan görünümünde (döndürme kilitli) Shift + sol da kaydırır.
    gz.Bas(k, FareTusu::Orta, 600, 400, {});
    gz.Hareket(k, 601, 400, {});
    CHECK(gz.Tur() == SuruklemeTuru::Kaydir);
    gz.Birak(k, FareTusu::Orta, 601, 400, {});
    gz.donmeKilitli = true;
    gz.Bas(k, FareTusu::Sol, 600, 400, {false, true, false});
    gz.Hareket(k, 650, 400, {false, true, false});
    CHECK(gz.Tur() == SuruklemeTuru::Kaydir);
    gz.Birak(k, FareTusu::Sol, 650, 400, {false, true, false});
}

TEST_CASE("gezinme: DPI ölçekli eşik, sürüklemede Shift değişimi kesintisiz, orta çift tık sığdırır") {
    GorunumKamerasi k = Kamera3B();
    Gezinme gz;
    gz.Boyut(G, Y);
    gz.dpiOlcek = 2.0;
    int tik = 0, sig = 0;
    gz.baglanti.tikla = [&](double, double, SecimKipi) { ++tik; };
    gz.baglanti.sigdir = [&] { ++sig; };
    gz.Bas(k, FareTusu::Sol, 400, 300, {});
    gz.Hareket(k, 406, 300, {});  // 6 px < 8 px (4 × 2)
    CHECK_FALSE(gz.Surukluyor());
    gz.Birak(k, FareTusu::Sol, 406, 300, {});
    CHECK(tik == 1);
    gz.Bas(k, FareTusu::Sol, 400, 300, {});
    gz.Hareket(k, 420, 300, {});
    CHECK(gz.Tur() == SuruklemeTuru::Kaydir);
    double x, y;
    gz.Hareket(k, 440, 300, {false, true, false});  // Shift basıldı: o anki konumdan döndürmeye geçer
    CHECK(gz.Tur() == SuruklemeTuru::Dondur);
    REQUIRE(gz.Cekirdek());
    const V3d c = *gz.Cekirdek();
    REQUIRE(k.Izdusum(G, Y).Izdusur(c, x, y));
    CHECK(std::hypot(x - 440, y - 300) < 1e-6);  // yeni çekirdek imlecin altında; sıçrama yok
    gz.Birak(k, FareTusu::Sol, 440, 300, {false, true, false});
    gz.CiftTik(k, FareTusu::Orta, 10, 10);
    CHECK(sig == 1);
}
