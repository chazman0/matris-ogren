// op4 C — Ayarlar › Görüntü › Yazı boyutu (S18 arayuz.yazi_boyutu; tema_belirtec.h YAZI_BOYUTLARI): ayar dosyası
// gidiş-dönüşü (varsayılan "orta", bilinmeyen değer "orta"ya düşer, bilinmeyen anahtarlar korunur) ve çarpanların yazı
// ölçeğini tam piksele düşürmesi. tema.h ImGui'ye bağlı olmadığından sınamaya doğrudan katılır.
#include <doctest/doctest.h>

#include <cmath>
#include <nlohmann/json.hpp>
#include <string>

#include "../../kaynak/arayuz/tema.h"
#include "cekirdek/ayarlar.h"

using namespace op4;
namespace b = op4::tema::belirtec;

TEST_CASE("yazı boyutu: ayar gidiş-dönüşü; varsayılan ve bilinmeyen değer orta; bilinmeyen anahtarlar korunur") {
    CHECK(Ayarlar{}.arayuz.yaziBoyutu == "orta");
    std::string hata;
    for (const char* kod : {"kucuk", "orta", "buyuk"}) {
        Ayarlar a;
        a.arayuz.yaziBoyutu = kod;
        Ayarlar o;
        REQUIRE(AyarlariOku(AyarlariYaz(a), o, hata));
        CHECK(o.arayuz.yaziBoyutu == kod);
        CHECK(AyarlariYaz(o) == AyarlariYaz(a));
    }
    // Eski dosya (anahtar yok) ve bozuk değer "orta"; başka anahtarlar ve bilinmeyen üst düzey gruplar korunur.
    Ayarlar o;
    REQUIRE(AyarlariOku(R"({"bicim": 1, "arayuz": {"yogunluk": "siki"}, "gelecek": {"x": [1, 2]}})", o, hata));
    CHECK(o.arayuz.yaziBoyutu == "orta");
    CHECK(o.arayuz.yogunluk == "siki");
    REQUIRE(AyarlariOku(R"({"arayuz": {"yazi_boyutu": "dev"}})", o, hata));
    CHECK(o.arayuz.yaziBoyutu == "orta");
    REQUIRE(AyarlariOku(R"({"arayuz": {"yazi_boyutu": "buyuk"}, "gelecek": {"x": [1, 2]}})", o, hata));
    const nlohmann::json j = nlohmann::json::parse(AyarlariYaz(o));
    CHECK(j["arayuz"]["yazi_boyutu"] == "buyuk");
    CHECK(j["gelecek"]["x"] == nlohmann::json::array({1, 2}));
    // Eskimiş "tema" alanı da gidiş-dönüşte korunur.
    REQUIRE(AyarlariOku(R"({"arayuz": {"tema": "acik"}})", o, hata));
    CHECK(nlohmann::json::parse(AyarlariYaz(o))["arayuz"]["tema"] == "acik");
}

TEST_CASE("yazı boyutu: çarpanlar belirteçlerden; gövde yazısı 1×'te 11 / 12 / 14 px, her DPI'da sıralı ve okunur") {
    REQUIRE(b::YAZI_BOYUTU_SAYISI == 3);
    CHECK(tema::YaziCarpani("orta") == 1.0f);
    CHECK(tema::YaziCarpani("bilinmeyen") == 1.0f);
    const float k = tema::YaziCarpani("kucuk"), o = tema::YaziCarpani("orta"), u = tema::YaziCarpani("buyuk");
    CHECK(k < o);
    CHECK(o < u);
    // Gövde (12 px) 100 % DPI'da tam piksele düşer (yuvarlama gerekmez).
    const float govde = b::Y.govde.boy;
    CHECK(std::fabs(govde * k - 11.0f) < 1e-3f);
    CHECK(std::fabs(govde * o - 12.0f) < 1e-3f);
    CHECK(std::fabs(govde * u - 14.0f) < 1e-3f);
    // Ciz::Yazi boyutu DPI × çarpandan sonra tam piksele yuvarlar: yaygın DPI ölçeklerinde gövde Küçük < Orta < Büyük
    // kalır, en küçük rol (rozet / bölüm 9 px) Küçük'te 8 px'in altına inmez.
    const b::YaziRolu roller[] = {b::Y.sayfa, b::Y.pencere, b::Y.baslik, b::Y.govde, b::Y.govde_orta, b::Y.govde_kalin,
                                  b::Y.etiket, b::Y.etiket_ince, b::Y.kucuk, b::Y.rozet, b::Y.bolum};
    for (const float dpi : {1.0f, 1.25f, 1.5f, 1.75f, 2.0f}) {
        CAPTURE(dpi);
        const float gk = std::round(govde * dpi * k), go = std::round(govde * dpi * o), gu = std::round(govde * dpi * u);
        CHECK(gk < go);
        CHECK(go < gu);
        for (const b::YaziRolu& r : roller) {
            CHECK(std::round(r.boy * dpi * k) >= 8.0f);
            CHECK(std::round(r.boy * dpi * k) <= std::round(r.boy * dpi * u));
        }
    }
}

TEST_CASE("en küçük istemci alanı: Atölye yerleşiminin alt sınırı (tasarim.md §9) Sıkı modüllerine sığar") {
    const tema::Olculer e{};  // eşikler varsayılan üye değerleridir (tema.h)
    const b::Olcu& s = b::OLCU_SIKI;
    CHECK(e.enAzGenislik == 1024.0f);
    CHECK(e.enAzYukseklik == 640.0f);
    // Tek panel (model ağacı pencere şeridinde): ray + Özellikler + pencere şeridi yanında görünüm ≥ %60 (§9.8).
    CHECK(e.enAzGenislik < e.tekPanelEsigi);
    CHECK(e.enAzGenislik - (s.ray + s.ozel + s.pencere_seridi) >= 0.6f * e.enAzGenislik);
    // Dikeyde üst bant, görünüm sekmeleri, rıhtım, komut satırı ve durum çubuğundan sonra görünüme ≥ 300 px kalır.
    const float ust = s.baslik + s.sekme + s.serit + s.gsekme, alt = s.rihtim_sekme + s.rihtim + s.komut + s.durum;
    CHECK(e.enAzYukseklik - ust - alt >= 300.0f);
}
