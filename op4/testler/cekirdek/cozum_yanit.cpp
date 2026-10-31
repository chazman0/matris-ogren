// op4 C++ sınamaları (D) — bina_coz yanıt çözümü gerçek köprü çıktılarına karşı (sözleşme S19; kabul D7, D8). Fikstür:
// op4/testler/cekirdek/cozum_yanitlar.zip = `python3 -I op4/araclar/sablon_dok.py --yanit-fikstur <zip>` (docs/web_kopru
// calistir, 3 şablon: betonarme-tek-aciklik ve celik-1kat-depo aks–kat, celik-cbf-3kat genel model; ayrıca girdi hatası).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cmath>

#include "dosya_sahte.h"

using namespace op4;
using namespace op4::sinama;
using nlohmann::json;

namespace {

const std::vector<ZipOkunanGirdi>& Fiksturler() {
    static const std::vector<ZipOkunanGirdi> g = [] {
        std::vector<ZipOkunanGirdi> o;
        std::string hata;
        const std::string zip = Op4Dosyasi("testler/cekirdek/cozum_yanitlar.zip");
        REQUIRE_MESSAGE(ZipCoz(zip, o, hata), hata);
        return o;
    }();
    return g;
}

std::string Fikstur(const std::string& ad) {
    for (const ZipOkunanGirdi& g : Fiksturler())
        if (g.ad == ad) return g.veri;
    FAIL("fikstür yok: " << ad);
    return {};
}

const char* const kSablonlar[] = {"betonarme-tek-aciklik", "celik-1kat-depo", "celik-cbf-3kat"};

}  // namespace

TEST_CASE("S19 CozumYanitiniCoz: üç şablonun gerçek bina_coz yanıtı") {
    for (const char* ad : kSablonlar) {
        CAPTURE(ad);
        const std::string yanit = Fikstur(std::string(ad) + ".yanit.json");
        const json j = json::parse(yanit);
        const json& v = j["veri"];
        SonucOzeti o;
        std::string veri, hata;
        REQUIRE_MESSAGE(CozumYanitiniCoz(yanit, o, veri, hata), hata);
        // Python'daki değerlerle birebir (aynı metinden okunur; bağıl fark 0 ≤ 1e-9).
        CHECK(o.cozumKimligi == v["cozum_kimligi"].get<std::string>());
        CHECK(o.cozumKimligi.rfind("bina-", 0) == 0);
        CHECK(o.sdSayisi == v["ozet"]["sd_sayisi"].get<size_t>());
        CHECK(o.kombinasyonSayisi == v["ozet"]["kombinasyon_sayisi"].get<size_t>());
        CHECK(o.enBuyukDc == v["ozet"]["en_buyuk_dc"].get<double>());
        CHECK(o.enBuyukDc == v["tasarim"]["en_buyuk_dc"].get<double>());
        CHECK(o.ozetMetni == j["sonuc_metin"].get<std::string>());
        CHECK(o.sureMs == j["sure_ms"].get<double>());
        size_t asan = 0;
        for (const json& e : v["tasarim"]["elemanlar"]) asan += e["dc"].get<double>() > 1.0;
        CHECK(o.asanSayisi == asan);
        // veri metni yeniden kodlanmadan ham alt metin olarak çıkar ve aynı JSON'dur.
        CHECK(yanit.find(veri) != std::string::npos);
        CHECK(json::parse(veri) == v);
        // ΣG, ΣQ (sonuc_metin'den) = veri.ozet.toplam_G / toplam_Q.
        const CozumToplamlari t = OzetToplamlari(o);
        CHECK(t.G == doctest::Approx(v["ozet"]["toplam_G"].get<double>()).epsilon(1e-12));
        CHECK(t.Q == doctest::Approx(v["ozet"]["toplam_Q"].get<double>()).epsilon(1e-12));
    }
}

TEST_CASE("S19 yedek eşleme (genel model): tasarım satırları çubuk kimliğine, en büyük D/C elemanı") {
    const std::string yanit = Fikstur("celik-cbf-3kat.yanit.json");
    SonucOzeti o;
    std::string veri, hata;
    REQUIRE(CozumYanitiniCoz(yanit, o, veri, hata));
    const json t = json::parse(veri)["tasarim"];
    SonucEslemesi e = TasarimdanEsle(veri);
    REQUIRE(e.basarili);
    CHECK(e.elemanlar.size() == t["elemanlar"].size());
    EslemeyiYerlestir(o, std::move(e));
    REQUIRE_FALSE(o.elemanlar.empty());
    CHECK(std::is_sorted(o.elemanlar.begin(), o.elemanlar.end(),
                         [](const ElemanSonucu& a, const ElemanSonucu& b) { return a.kimlik < b.kimlik; }));
    double enBuyuk = -1;
    uint32_t enBuyukCubuk = 0;
    for (const json& x : t["elemanlar"])
        if (x["dc"].get<double>() > enBuyuk) {
            enBuyuk = x["dc"].get<double>();
            enBuyukCubuk = x["cubuk"].get<uint32_t>();
        }
    CHECK(o.enBuyukDcElemani == CubukKimligi(enBuyukCubuk));
    CHECK(o.enBuyukDc == enBuyuk);
    const DcDagilimi d = DcDagilimiHesapla(o);
    CHECK(d.yesil + d.sari + d.turuncu + d.kirmizi + d.yok == o.elemanlar.size());
    const auto b = BoyamaKur(o, 3);
    CHECK(b->renkler.size() == o.elemanlar.size());
    CHECK(b->cozumKimligi == o.cozumKimligi);

    // Aks–kat modelinde yedek eşleme yapılmaz (çekirdeğin işi), uyarı yazılır.
    const SonucEslemesi a = TasarimdanEsle(json::parse(Fikstur("betonarme-tek-aciklik.yanit.json"))["veri"].dump());
    CHECK(a.basarili);
    CHECK(a.elemanlar.empty());
    REQUIRE(a.uyarilar.size() == 1);
    CHECK(a.uyarilar[0].find("eşlenemedi") != std::string::npos);
}

TEST_CASE("S19 hata, iptal ve bozuk yanıtlar") {
    SonucOzeti o;
    std::string veri, hata;
    CHECK_FALSE(CozumYanitiniCoz(Fikstur("hata.yanit.json"), o, veri, hata));
    CHECK(hata.find("Malzeme yok") == 0);
    CHECK_FALSE(CozumYanitiniCoz(R"({"hata":"İşlem iptal edildi.","hata_turu":"iptal"})", o, veri, hata));
    CHECK(hata == "İşlem iptal edildi.");
    CHECK_FALSE(CozumYanitiniCoz("{yarım", o, veri, hata));
    CHECK(hata.find("okunamadı") != std::string::npos);
    CHECK_FALSE(CozumYanitiniCoz(R"({"hata":null,"ad":"x"})", o, veri, hata));
    CHECK(hata.find("\"veri\"") != std::string::npos);
    CHECK(veri.empty());
}

TEST_CASE("S19 sonuc/ozet.json gidiş-dönüşü") {
    SonucOzeti o;
    std::string veri, hata;
    REQUIRE(CozumYanitiniCoz(Fikstur("celik-cbf-3kat.yanit.json"), o, veri, hata));
    EslemeyiYerlestir(o, TasarimdanEsle(veri));
    o.tarih = "2026-10-31T12:00:00Z";
    o.motorSurumu = "9.9.9";
    o.sahneSurumu = 42;
    o.elemanlar.push_back({CubukKimligi(999999), std::nan(""), "", "", -1});  // NaN → null → tasarım yok
    const std::string j = SonucOzetiJson(o);
    SonucOzeti g;
    REQUIRE_MESSAGE(SonucOzetiOku(j, g, hata), hata);
    CHECK(g.cozumKimligi == o.cozumKimligi);
    CHECK(g.tarih == o.tarih);
    CHECK(g.motorSurumu == o.motorSurumu);
    CHECK(g.sahneSurumu == 42);
    CHECK(g.sdSayisi == o.sdSayisi);
    CHECK(g.kombinasyonSayisi == o.kombinasyonSayisi);
    CHECK(g.enBuyukDc == o.enBuyukDc);
    CHECK(g.enBuyukDcElemani == o.enBuyukDcElemani);
    CHECK(g.asanSayisi == o.asanSayisi);
    CHECK(g.ozetMetni == o.ozetMetni);
    CHECK(g.uyarilar == o.uyarilar);
    REQUIRE(g.elemanlar.size() == o.elemanlar.size());
    for (size_t i = 0; i + 1 < g.elemanlar.size(); ++i) {
        CHECK(g.elemanlar[i].kimlik == o.elemanlar[i].kimlik);
        CHECK(g.elemanlar[i].dc == o.elemanlar[i].dc);
        CHECK(g.elemanlar[i].belirleyen == o.elemanlar[i].belirleyen);
        CHECK(g.elemanlar[i].tasarimSatiri == o.elemanlar[i].tasarimSatiri);
    }
    CHECK(g.elemanlar.back().dc == -1);
    CHECK(SonucOzetiJson(g) != "{}");
    CHECK_FALSE(SonucOzetiOku("{}", g, hata));
    CHECK_FALSE(SonucOzetiOku(R"({"bicim":9,"cozum_kimligi":"x"})", g, hata));
    CHECK(hata.find("daha yeni") != std::string::npos);
}

TEST_CASE("Sayı ve süre yazımı (Türkçe, Stüdyo)") {
    CHECK(SayiMetni(2714.76, 2) == "2 714,76");
    CHECK(SayiMetni(480.0, 2) == "480");
    CHECK(SayiMetni(-1234567.5, 1) == "-1 234 567,5");
    CHECK(SayiMetni(216, 0) == "216");
    CHECK(SayiMetni(std::nan(""), 2) == "—");
    CHECK(SureMetni(850) == "850 ms");
    CHECK(SureMetni(3420) == "3,4 s");
    CHECK(SureMetni(125000) == "2 dk 05 s");
}
