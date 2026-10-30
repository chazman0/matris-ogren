// Sözleşme sınamaları: kimlik (S1), olay (S2), Türkçe yardımcılar (S6), seçim (S7), sahne (S4), kod tabloları.
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <unordered_set>

#include "cekirdek/kimlik.h"
#include "cekirdek/olay.h"
#include "cekirdek/sahne.h"
#include "cekirdek/secim.h"
#include "cekirdek/turkce.h"
#include "sinama_yardim.h"

using namespace op4;

TEST_CASE("S1 kimlik: metin gidiş-dönüşü, sıralama, karma") {
    const ElemanKimligi c = CubukKimligi(12), a{ElemanTuru::Aks, 1, 65538};
    CHECK(KimlikMetni(c) == "cubuk:12");
    CHECK(KimlikMetni(a) == "aks:65538/1");
    CHECK(KimlikCoz("cubuk:12") == c);
    CHECK(KimlikCoz("aks:65538/1") == a);
    CHECK_FALSE(KimlikCoz("cubuk:"));
    CHECK_FALSE(KimlikCoz("yok:1"));
    CHECK_FALSE(KimlikCoz("kiris:3"));
    CHECK_FALSE(KimlikCoz("cubuk:12/"));
    CHECK_FALSE(KimlikCoz("cubuk:-1"));
    CHECK(CubukKimligi(1) < PanelKimligi(0));  // tür önce
    CHECK(ElemanKimligi::AnahtardanKur(a.Anahtar()) == a);
    std::unordered_set<ElemanKimligi> k{c, a, c};
    CHECK(k.size() == 2);
    for (int t = 0; t < ELEMAN_TURU_SAYISI; ++t) {
        const auto tur = static_cast<ElemanTuru>(t);
        CHECK(TurKodundan(TurKodu(tur)) == tur);
    }
}

TEST_CASE("S2 olay: sıra ve yayın sırasında bırakma") {
    Olay<int> o;
    std::vector<int> g;
    Olay<int>::Abonelik b = 0;
    o.Abone([&](const int& x) { g.push_back(x); });
    b = o.Abone([&](const int& x) {
        g.push_back(x * 10);
        o.Birak(b);
    });
    o.Yay(1);
    o.Yay(2);
    CHECK(g == std::vector<int>{1, 10, 2});
    CHECK(o.AboneSayisi() == 1);
}

TEST_CASE("S6 Türkçe katlama, ondalık virgül, sayı okuma") {
    CHECK(TurkceKatla("ÇUBUK") == "cubuk");
    CHECK(TurkceKatla("İçe Aktar") == "ice aktar");
    CHECK(TurkceKatla("IŞIK ğüö") == "isik guo");
    CHECK(TurkceOnekMi("kol", "KOLON"));
    CHECK(OndalikVirgul(3.25, 2) == "3,25");
    CHECK(OndalikVirgul(2.0, 3) == "2");
    CHECK(OndalikVirgul(-0.0001, 2) == "0");
    CHECK(OndalikVirgul(1234.5678, 1) == "1234,6");
    double v = 0;
    CHECK(SayiOku(" 3,5 ", v));
    CHECK(v == doctest::Approx(3.5));
    CHECK(SayiOku("6000", v));
    CHECK_FALSE(SayiOku("3,5m", v));
}

TEST_CASE("S7 seçim: kipler, tek olay, ayıklama") {
    Secim s;
    int olay = 0;
    s.degisti.Abone([&] { ++olay; });
    const std::vector<ElemanKimligi> a{CubukKimligi(3), CubukKimligi(1), CubukKimligi(3), DugumKimligi(5)};
    s.Uygula(a, SecimKipi::Yeni);
    CHECK(s.Sayi() == 3);
    CHECK(olay == 1);
    CHECK(s.Liste().front() == CubukKimligi(1));
    s.Uygula(a, SecimKipi::Ekle);  // değişiklik yok → olay yok
    CHECK(olay == 1);
    s.Uygula(CubukKimligi(1), SecimKipi::Tersle);
    CHECK_FALSE(s.Iceriyor(CubukKimligi(1)));
    s.Uygula(std::vector<ElemanKimligi>{CubukKimligi(3), PanelKimligi(9)}, SecimKipi::IcindeSuz);
    CHECK(s.Liste() == std::vector<ElemanKimligi>{CubukKimligi(3)});
    s.Ayikla(std::vector<ElemanKimligi>{CubukKimligi(3)});
    CHECK(s.Bos());
    CHECK(s.Surum() == static_cast<uint64_t>(olay));
}

TEST_CASE("S4 sahne: örnek düzenek ve dizinler") {
    const SahnePtr s = OrnekSahneAnlik();
    CHECK(s->dugumler.size() == 8);
    CHECK(s->cubuklar.size() == 8);
    CHECK(s->paneller.empty());
    CHECK(s->mesnetler.size() == 4);
    CHECK(s->seviyeler.size() == 2);
    CHECK(s->akslar.size() == 4);
    CHECK(s->DugumDizini(1022).has_value());  // kat 1, ix 1, iy 1
    CHECK(s->Var(CubukKimligi(8)));
    CHECK_FALSE(s->Var(CubukKimligi(9)));
    const Kutu3d k = s->Sinir(CubukKimligi(1));
    CHECK(k.enBuyuk.z == doctest::Approx(3.5));
    CHECK(s->sinir.enBuyuk.x >= 6.0);
    for (const SahneCubugu& c : s->cubuklar) {
        CHECK(c.i < s->dugumler.size());
        CHECK(c.j < s->dugumler.size());
        CHECK(c.kesit < s->kesitler.size());
        CHECK(Uzunluk(c.yYerel) == doctest::Approx(1.0));
    }
    CHECK(BosSahne()->ElemanSayisi() == 0);
}

TEST_CASE("S4 kod tabloları op4/veri/sahne_kodlari.json ile aynı") {
    const auto j = nlohmann::json::parse(sinama::Op4Dosyasi("veri/sahne_kodlari.json"));
    for (int t = 0; t < ELEMAN_TURU_SAYISI; ++t)
        CHECK(j["eleman_turu"][TurKodu(static_cast<ElemanTuru>(t))].get<int>() == t);
    CHECK(j["eleman_turu"].size() == static_cast<size_t>(ELEMAN_TURU_SAYISI));
    const auto& c = j["cubuk_turu"];
    CHECK(c["diger"] == static_cast<int>(CubukTuru::Diger));
    CHECK(c["kolon"] == static_cast<int>(CubukTuru::Kolon));
    CHECK(c["kiris"] == static_cast<int>(CubukTuru::Kiris));
    CHECK(c["capraz"] == static_cast<int>(CubukTuru::Capraz));
    CHECK(c["makas-ust"] == static_cast<int>(CubukTuru::MakasUst));
    CHECK(c["makas-alt"] == static_cast<int>(CubukTuru::MakasAlt));
    CHECK(c["makas-dikme"] == static_cast<int>(CubukTuru::MakasDikme));
    CHECK(c["makas-diyagonal"] == static_cast<int>(CubukTuru::MakasDiyagonal));
    CHECK(c["asik"] == static_cast<int>(CubukTuru::Asik));
    CHECK(c["kren"] == static_cast<int>(CubukTuru::Kren));
    CHECK(c["bag"] == static_cast<int>(CubukTuru::Bag));
    CHECK(c.size() == 11);
    const auto& p = j["panel_turu"];
    CHECK(p["doseme"] == static_cast<int>(PanelTuru::Doseme));
    CHECK(p["cati"] == static_cast<int>(PanelTuru::Cati));
    CHECK(p["cephe"] == static_cast<int>(PanelTuru::Cephe));
    CHECK(p["diger"] == static_cast<int>(PanelTuru::Diger));
    const auto& d = j["dugum_turu"];
    CHECK(d["aks_kat"] == static_cast<int>(DugumTuru::AksKat));
    CHECK(d["aks_kesisimi"] == static_cast<int>(DugumTuru::AksKesisimi));
    CHECK(d["bolme"] == static_cast<int>(DugumTuru::Bolme));
    CHECK(d["kesisim"] == static_cast<int>(DugumTuru::Kesisim));
    CHECK(d["serbest"] == static_cast<int>(DugumTuru::Serbest));
    const auto& k = j["kesit_turu"];
    CHECK(k["I"] == static_cast<int>(KesitTuru::I));
    CHECK(k["KUTU"] == static_cast<int>(KesitTuru::Kutu));
    CHECK(k["BORU"] == static_cast<int>(KesitTuru::Boru));
    CHECK(k["DIKDORTGEN"] == static_cast<int>(KesitTuru::Dikdortgen));
    CHECK(k["DAIRE"] == static_cast<int>(KesitTuru::Daire));
    CHECK(k["L"] == static_cast<int>(KesitTuru::L));
    CHECK(k["2L"] == static_cast<int>(KesitTuru::CiftL));
    CHECK(k["UPN"] == static_cast<int>(KesitTuru::Upn));
    CHECK(j["mesnet_turu"]["yay"] == static_cast<int>(MesnetTuru::Yay));
    CHECK(j["temel_turu"]["radye"] == static_cast<int>(TemelTuru::Radye));
    CHECK(j["cubuk_bayraklari"]["yalniz_cekme"] == cubuk_bayragi::YALNIZ_CEKME);
    CHECK(j["cubuk_bayraklari"]["serbest_dugume_bagli"] == cubuk_bayragi::SERBEST_DUGUME_BAGLI);
    CHECK(j["cubuk_bayraklari"]["vute"] == cubuk_bayragi::VUTE);
    CHECK(j["cubuk_bayraklari"]["uretecten"] == cubuk_bayragi::URETECTEN);
    CHECK(j["dugum_bayraklari"]["mesnetli"] == dugum_bayragi::MESNETLI);
    CHECK(j["dugum_bayraklari"]["baglantisiz"] == dugum_bayragi::BAGLANTISIZ);
    CHECK(j["serbestlik_sirasi"][4] == "My");
    CHECK(SerbestlikBiti(true, 5) == (1u << 11));
}
