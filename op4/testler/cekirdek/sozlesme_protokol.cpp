// Sözleşme sınamaları: hesap motoru tel protokolü (S12) ve motor hizmeti yönlendirmesi / taslak istemci (S13).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include "cekirdek/motor_hizmeti.h"
#include "cekirdek/motor_protokol.h"
#include "sinama_yardim.h"

using namespace op4;
using namespace op4::motor_protokolu;
using nlohmann::json;

TEST_CASE("S12 ortak vektörler: C++ kodlayıcı Python ile bayt bayt aynı, çözücü alanları geri verir") {
    const json d = json::parse(sinama::Op4Dosyasi("testler/ortak/motor_protokol.json"));
    REQUIRE(d["vektorler"].size() >= 10);
    for (const json& v : d["vektorler"]) {
        const std::string tur = v["tur"], beklenen = v["govde"];
        const json& g = v["girdi"];
        CAPTURE(v["ad"].get<std::string>());
        std::string uretilen;
        if (tur == "istek") uretilen = IstekIletisi(g["id"], g["islem"].get<std::string>(), g["istek_json"].get<std::string>());
        else if (tur == "iptal") uretilen = IptalIletisi(g["id"]);
        else if (tur == "kapat") uretilen = KapatIletisi();
        else if (tur == "hazir")
            uretilen = HazirIletisi(g["rol"].get<std::string>(), g["basarili"], g["pid"], g["python"].get<std::string>(),
                                    g["sure_ms"], g["surum_json"].get<std::string>(), g["hata"].get<std::string>());
        else if (tur == "durum") uretilen = DurumIletisi(g["metin"].get<std::string>(), g["oran"]);
        else if (tur == "ilerleme") uretilen = IlerlemeIletisi(g["id"], g["metin"].get<std::string>(), g["oran"]);
        else if (tur == "gunluk") uretilen = GunlukIletisi(g["duzey"].get<std::string>(), g["metin"].get<std::string>());
        else if (tur == "yanit") uretilen = YanitIletisi(g["id"], g["sure_ms"], g["calistir_metni"].get<std::string>());
        CHECK(uretilen == beklenen);

        GelenIleti i;
        std::string hata;
        if (tur == "yanit") {
            REQUIRE(IletiCoz(beklenen, i, hata));
            CHECK(i.tur == IletiTuru::Yanit);
            CHECK(i.id == g["id"].get<uint64_t>());
            CHECK(i.yanit == g["calistir_metni"].get<std::string>());
        } else if (tur == "hazir") {
            REQUIRE(IletiCoz(beklenen, i, hata));
            CHECK(i.tur == IletiTuru::Hazir);
            CHECK(i.basarili == g["basarili"].get<bool>());
            CHECK(i.pid == g["pid"].get<long long>());
            CHECK(i.hata == g["hata"].get<std::string>());
            CHECK(json::parse(i.surum) == json::parse(g["surum_json"].get<std::string>().empty() ? "{}" : g["surum_json"].get<std::string>()));
        } else if (tur == "durum" || tur == "ilerleme" || tur == "gunluk") {
            REQUIRE(IletiCoz(beklenen, i, hata));
            CHECK(i.metin == g["metin"].get<std::string>());
        }
    }
    CHECK(HataYaniti("İşlem iptal edildi.", "iptal") == d["hata_yaniti_iptal"].get<std::string>());
}

TEST_CASE("S12 çerçeve: kısmi okuma, birden çok çerçeve, bozuk uzunluk") {
    std::string akis;
    REQUIRE(CerceveEkle(akis, "{\"tur\":\"kapat\"}"));
    REQUIRE(CerceveEkle(akis, IptalIletisi(5)));
    CHECK_FALSE(CerceveEkle(akis, ""));
    std::string tampon, govde;
    for (size_t i = 0; i < 6; ++i) tampon += akis[i];
    CHECK(CerceveAl(tampon, govde) == CerceveDurumu::Eksik);
    tampon = akis;
    REQUIRE(CerceveAl(tampon, govde) == CerceveDurumu::Tamam);
    CHECK(govde == "{\"tur\":\"kapat\"}");
    REQUIRE(CerceveAl(tampon, govde) == CerceveDurumu::Tamam);
    CHECK(govde == "{\"tur\":\"iptal\",\"id\":5}");
    CHECK(tampon.empty());
    std::string bozuk("\0\0\0\0x", 5);
    CHECK(CerceveAl(bozuk, govde) == CerceveDurumu::Bozuk);
    std::string buyuk("\xff\xff\xff\xff", 4);
    CHECK(CerceveAl(buyuk, govde) == CerceveDurumu::Bozuk);
    GelenIleti i;
    std::string hata;
    CHECK_FALSE(IletiCoz("{\"tur\":\"yanit\",\"id\":1,\"sure_ms\":0.0}", i, hata));
    CHECK(IletiCoz("{\"tur\":\"gelecekte\"}", i, hata));
    CHECK(i.tur == IletiTuru::Bilinmiyor);
    CHECK(JsonKacis("a\"b\\c\n\x01") == "a\\\"b\\\\c\\n\\u0001");
}

TEST_CASE("S13 yönlendirme tablosu (MIMARI §8.3)") {
    CHECK(MotorRoluSec("bina_coz") == MotorRolu::Ana);
    CHECK(MotorRoluSec("bina_kimlik") == MotorRolu::Ana);
    CHECK(MotorRoluSec("bina_tablolar") == MotorRolu::Ana);
    CHECK(MotorRoluSec("bina_sablon") == MotorRolu::Yardimci);
    CHECK(MotorRoluSec("bina_sablonlar") == MotorRolu::Yardimci);
    CHECK(MotorRoluSec("determinant") == MotorRolu::Yardimci);
    CHECK(MotorRoluSec("se_coz") == MotorRolu::Yardimci);
    CHECK(MotorRoluSec("bilinmeyen") == MotorRolu::Yardimci);
}

TEST_CASE("S13 Y1: taslak istemci de her isteğe tam bir yanıt verir") {
    auto m = MotorIstemcisiOlustur();
    m->Baslat(MotorAyari{});
    CHECK(m->Durum().hazir);
    int cagri = 0;
    MotorYaniti son;
    const IstekNo no = m->Gonder("bina_coz", "{}", "{}", [&](const MotorYaniti& y) {
        ++cagri;
        son = y;
    });
    CHECK(no != 0);
    CHECK(cagri == 0);  // işleyici yalnız Pompala içinde
    CHECK(m->Pompala() == 1);
    CHECK(m->Pompala() == 0);
    CHECK(cagri == 1);
    CHECK(son.no == no);
    CHECK(son.durum == YanitDurumu::MotorHatasi);
    CHECK(son.hataTuru == "motor_yok");
    CHECK(json::parse(son.yanit)["hata_turu"] == "motor_yok");
}
