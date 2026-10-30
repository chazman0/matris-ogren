// Model çekirdeği (B) — başarım (MIMARI §6.13, §9.5; kabul B7): celik-sanayi-4hol ve sentetik 5 bin / 20 bin çubukta uygula
// (C++ çağrısından sahne ve öznitelik anlıkları hazır olana dek) ≤ 100 / ≤ 300 ms. Ölçümler "OP4OLCUM senaryo=cekirdek …"
// satırlarıdır. Bütçe yalnız iyileştirilmiş QuickJS'te (GCC/Clang her zaman -O2; MSVC Release) ve temizleyicisiz derlemede
// zorunludur: MSVC Debug ve ASan/UBSan derlemelerinde yalnız ölçüm yazılır.
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <string>

#include "cekirdek_js_yardim.h"

using namespace op4;
using nlohmann::json;

namespace {

#if defined(__has_feature)
#if __has_feature(address_sanitizer) || __has_feature(undefined_behavior_sanitizer)
#define OP4_TEMIZLEYICI 1
#endif
#endif
#if defined(__SANITIZE_ADDRESS__)
#define OP4_TEMIZLEYICI 1
#endif
#if defined(_DEBUG) || defined(OP4_TEMIZLEYICI)
constexpr bool kButceZorunlu = false;
#else
constexpr bool kButceZorunlu = true;
#endif

// nx × ny göz, nk kat genel model: aks REF'li kolonlar, iki yönde kirişler, döşeme panelleri.
std::string SentetikModel(int nx, int ny, int nk) {
    json m = json::parse(sinama::Op4Dosyasi("testler/derlem/sablonlar/celik-cbf-3kat.json"));
    json xs = json::array(), ys = json::array(), zs = json::array(), katlar = json::array();
    auto ad = [](const char* on, int i) { return std::string(on) + std::to_string(i); };
    for (int i = 0; i <= nx; ++i) xs.push_back({{"ad", ad("X", i)}, {"konum", 6.0 * i}});
    for (int j = 0; j <= ny; ++j) ys.push_back({{"ad", ad("Y", j)}, {"konum", 5.0 * j}});
    for (int k = 0; k <= nk; ++k) {
        zs.push_back({{"ad", ad("Z", k)}, {"konum", 3.5 * k}, {"kat", k}});
        katlar.push_back({{"no", k}, {"ad", ad("Z", k)}, {"kot", 3.5 * k}});
    }
    m["baslik"] = "Sentetik " + std::to_string(nx) + "x" + std::to_string(ny) + "x" + std::to_string(nk);
    m["akslar"] = {{"x", xs}, {"y", ys}, {"z", zs}};
    m["katlar"] = katlar;
    m["dugumler"] = json::array();
    json c = json::array(), p = json::array();
    auto r = [&](int i, int j, int k) { return json{{"aks", {xs[i]["ad"], ys[j]["ad"]}}, {"z", zs[k]["ad"]}}; };
    int no = 1, pno = 1;
    for (int k = 1; k <= nk; ++k) {
        for (int i = 0; i <= nx; ++i)
            for (int j = 0; j <= ny; ++j) c.push_back({{"no", no++}, {"i", r(i, j, k - 1)}, {"j", r(i, j, k)}, {"tur", "kolon"}, {"kesit", "KOLON"}, {"kat", k}});
        for (int i = 0; i < nx; ++i)
            for (int j = 0; j <= ny; ++j) c.push_back({{"no", no++}, {"i", r(i, j, k)}, {"j", r(i + 1, j, k)}, {"tur", "kiris"}, {"kesit", "KIRIS"}, {"kat", k}});
        for (int i = 0; i <= nx; ++i)
            for (int j = 0; j < ny; ++j) c.push_back({{"no", no++}, {"i", r(i, j, k)}, {"j", r(i, j + 1, k)}, {"tur", "kiris"}, {"kesit", "KIRIS"}, {"kat", k}});
        for (int i = 0; i < nx; ++i)
            for (int j = 0; j < ny; ++j)
                p.push_back({{"no", pno++}, {"tur", "doseme"}, {"kalinlik", 0.12}, {"kat", k},
                             {"kose", {r(i, j, k), r(i + 1, j, k), r(i + 1, j + 1, k), r(i, j + 1, k)}}});
    }
    m["cubuklar"] = c;
    m["paneller"] = p;
    return m.dump();
}

double Ms(std::chrono::steady_clock::time_point t0) {
    return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
}

struct Olcum {
    double yukle = 0, baslik = 0, aks = 0, geriAl = 0;
};

Olcum Olc(ModelCekirdegi& c, const std::string& ad, const std::string& metin, double butce) {
    Olcum o;
    auto t0 = std::chrono::steady_clock::now();
    const YuklemeSonucu y = c.Yukle(metin, "sinama:" + ad);
    o.yukle = Ms(t0);
    REQUIRE_MESSAGE(y.basarili, y.hata);
    const SahnePtr s = c.Sahne();
    const size_t cubuk = s->cubuklar.size(), panel = s->paneller.size();
    // en iyi 3 ölçüm (ısınma ve zamanlayıcı gürültüsü)
    o.baslik = 1e9;
    for (int i = 0; i < 3; ++i) {
        t0 = std::chrono::steady_clock::now();
        const IslemRaporu r = c.Uygula(islem::BASLIK_DEGISTIR, R"({"baslik":"Başarım )" + std::to_string(i) + "\"}");
        o.baslik = std::min(o.baslik, Ms(t0));
        REQUIRE(r.ModelDegisti());
        REQUIRE(c.Sahne()->cubuklar.size() == cubuk);
        REQUIRE(c.Oznitelikler()->satirlar.size() >= cubuk + panel);
    }
    // geometriyi değiştiren işlem: ilk X aksı 0,5 m kayar (aksSihirbazi; bağlı elemanlar yapışık taşınır)
    json ak = json::parse(c.Metin())["akslar"];
    ak["x"][0]["konum"] = ak["x"][0]["konum"].get<double>() - 0.5;
    t0 = std::chrono::steady_clock::now();
    const IslemRaporu a = c.Uygula(islem::AKS_SIHIRBAZI, json{{"akslar", ak}}.dump());
    o.aks = Ms(t0);
    REQUIRE_MESSAGE(a.basarili, a.hata);
    CHECK(a.degisen.size() > 0);
    t0 = std::chrono::steady_clock::now();
    REQUIRE(c.GeriAl().ModelDegisti());
    o.geriAl = Ms(t0);
    std::printf("OP4OLCUM senaryo=cekirdek model=%s cubuk=%zu panel=%zu yukle_ms=%.1f uygula_ms=%.1f aks_ms=%.1f geri_al_ms=%.1f butce_ms=%.0f zorunlu=%d\n",
                ad.c_str(), cubuk, panel, o.yukle, o.baslik, o.aks, o.geriAl, butce, kButceZorunlu ? 1 : 0);
    if (kButceZorunlu) CHECK_MESSAGE(o.baslik <= butce, ad << ": uygula " << o.baslik << " ms > " << butce << " ms");
    return o;
}

}  // namespace

TEST_CASE("cekirdek_js B7: başarım — sanayi şablonu, sentetik 5 bin ve 20 bin çubuk") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    Olc(*c, "celik-sanayi-4hol", sinama::Sablon("celik-sanayi-4hol"), 100);
    Olc(*c, "sentetik-5bin", SentetikModel(10, 10, 15), 100);
    Olc(*c, "sentetik-20bin", SentetikModel(28, 19, 12), 300);
}
