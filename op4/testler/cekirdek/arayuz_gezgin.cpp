// C (arayuz-goruntu) sınamaları — model gezgini ağacı (sözleşme S10; MIMARI §5.6; kabul C7).
#include <doctest/doctest.h>

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <functional>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <string>

#include <nlohmann/json.hpp>

#include "cekirdek/gezgin.h"
#include "cekirdek/oznitelik.h"
#include "cekirdek/sahne.h"
#include "sinama_yardim.h"

using namespace op4;

namespace {

// Basit tablo kurucu: (kimlik, alt_tur, kullanim_yeri, katlar).
struct Kayit {
    ElemanKimligi k;
    std::string altTur, yer;
    std::vector<double> katlar;
};

OznitelikTablosu Tablo(const std::vector<Kayit>& kayitlar) {
    OznitelikTablosu t;
    OznitelikSutunu alt{oznitelik::ALT_TUR, OznitelikTuru::Enum, "", {}, {}, {}, {}, {}};
    OznitelikSutunu yer{oznitelik::KULLANIM_YERI, OznitelikTuru::Enum, "", {}, {}, {}, {}, {}};
    OznitelikSutunu kat{oznitelik::KAT, OznitelikTuru::Liste, "", {}, {}, {}, {0}, {}};
    auto kod = [](OznitelikSutunu& s, const std::string& v) {
        if (v.empty()) {
            s.kod.push_back(OZNITELIK_YOK);
            return;
        }
        for (uint32_t i = 0; i < s.sozluk.size(); ++i)
            if (s.sozluk[i] == v) {
                s.kod.push_back(i);
                return;
            }
        s.sozluk.push_back(v);
        s.kod.push_back(static_cast<uint32_t>(s.sozluk.size() - 1));
    };
    for (const Kayit& r : kayitlar) {
        t.satirlar.push_back(r.k);
        kod(alt, r.altTur);
        kod(yer, r.yer);
        for (const double k : r.katlar) kat.listeDeger.push_back(k);
        kat.listeBas.push_back(static_cast<uint32_t>(kat.listeDeger.size()));
    }
    t.sutunlar = {alt, yer, kat};
    t.DizinleriKur();
    return t;
}

const GezginDugumu* Bul(const GezginDugumu& d, const std::string& anahtar) {
    if (d.anahtar == anahtar) return &d;
    for (const GezginDugumu& c : d.cocuklar)
        if (const GezginDugumu* b = Bul(c, anahtar)) return b;
    return nullptr;
}

// Her düğümde: elemanlar sıralı + tekrarsız, sayi == elemanlar.size(), çocukların birleşimi ⊆ ebeveyn.
void Tutarli(const GezginDugumu& d) {
    CAPTURE(d.anahtar);
    CHECK(d.sayi == d.elemanlar.size());
    CHECK(std::is_sorted(d.elemanlar.begin(), d.elemanlar.end()));
    CHECK(std::adjacent_find(d.elemanlar.begin(), d.elemanlar.end()) == d.elemanlar.end());
    for (const GezginDugumu& c : d.cocuklar) {
        for (const ElemanKimligi& e : c.elemanlar) CHECK(std::binary_search(d.elemanlar.begin(), d.elemanlar.end(), e));
        Tutarli(c);
    }
}

}  // namespace

TEST_CASE("gezgin: kat → alt tür → kullanım yeri, sayılar; çok katlı kolon her katında; kat dışı düğümü") {
    std::vector<Kayit> r;
    // Kat 1: 4 kolon (2 köşe, 1 kenar, 1 iç), 3 kiriş (dış, iç, iç); kat 2: aynı kolonlardan 2'si sürer (kat [1, 2])
    r.push_back({CubukKimligi(1), "kolon", "kose", {1}});
    r.push_back({CubukKimligi(2), "kolon", "kose", {1, 2}});
    r.push_back({CubukKimligi(3), "kolon", "kenar", {1}});
    r.push_back({CubukKimligi(4), "kolon", "ic", {1, 2}});
    r.push_back({CubukKimligi(10), "kiris", "dis", {1}});
    r.push_back({CubukKimligi(11), "kiris", "ic", {1}});
    r.push_back({CubukKimligi(12), "kiris", "ic", {1}});
    r.push_back({CubukKimligi(20), "kiris", "dis", {2}});
    r.push_back({PanelKimligi(1), "doseme", "ic", {2}});
    r.push_back({DugumKimligi(1), "dugum", "temel", {}});
    r.push_back({DugumKimligi(2), "dugum", "ara", {1}});
    r.push_back({CubukKimligi(30), "capraz", "", {2}});
    const OznitelikTablosu t = Tablo(r);

    const GezginDugumu kok = GezginAgaciKur(t);
    CHECK(kok.anahtar == "proje");
    CHECK(kok.sayi == r.size());  // proje toplamı tekrarsız
    Tutarli(kok);
    const GezginDugumu* katlar = Bul(kok, "katlar");
    REQUIRE(katlar);
    REQUIRE(katlar->cocuklar.size() == 2);
    CHECK(katlar->cocuklar[0].anahtar == "kat:2");  // üst kat önce
    CHECK(katlar->cocuklar[1].anahtar == "kat:1");
    CHECK(katlar->cocuklar[0].baslik == "Kat 2");
    const GezginDugumu* k1 = Bul(kok, "kat:1");
    REQUIRE(k1);
    CHECK(k1->sayi == 8);  // 4 kolon + 3 kiriş + 1 düğüm
    REQUIRE(k1->cocuklar.size() == 3);
    CHECK(k1->cocuklar[0].baslik == "Kolonlar");  // görüntü sırası
    CHECK(k1->cocuklar[1].baslik == "Kirişler");
    CHECK(k1->cocuklar[2].baslik == "Düğümler");
    const GezginDugumu* kose = Bul(kok, "kat:1/alt_tur:kolon/kullanim_yeri:kose");
    REQUIRE(kose);
    CHECK(kose->baslik == "Köşe");
    CHECK(kose->sayi == 2);
    CHECK(Bul(kok, "kat:1/alt_tur:kiris/kullanim_yeri:ic")->sayi == 2);
    // Kat 2: kat aralığını aşan 2 kolon da görünür.
    CHECK(Bul(kok, "kat:2/alt_tur:kolon")->sayi == 2);
    CHECK(Bul(kok, "kat:2")->sayi == 5);
    // Kullanım yeri boş, tek sınıf: yaprak yok (doğrudan tür düğümü).
    CHECK(Bul(kok, "kat:2/alt_tur:capraz")->cocuklar.empty());
    // Kata atanmamış: "Temel ve kat dışı".
    const GezginDugumu* disi = Bul(kok, "kat:-");
    REQUIRE(disi);
    CHECK(disi->baslik == "Temel ve kat dışı");
    CHECK(disi->sayi == 1);
    // "Katlar" düğümünün elemanları kat dışını içermez.
    CHECK(katlar->sayi == r.size() - 1);
}

TEST_CASE("gezgin: sahne seviyelerinden kat kotu ve kök başlığı; boş tablo") {
    auto s = std::make_shared<SahneAnlik>();
    s->baslik = "Depo Binası – Tokat OSB";
    s->seviyeler = {{"±0.00", 0.0, 0}, {"+4.50", 4.5, 1}, {"+9.00", 9.0, 2}};
    const OznitelikTablosu t = Tablo({{CubukKimligi(1), "kolon", "kose", {0, 1}}, {CubukKimligi(2), "kiris", "dis", {2}}});
    const GezginDugumu kok = GezginAgaciKur(t, s.get());
    CHECK(kok.baslik == "Depo Binası – Tokat OSB");
    const GezginDugumu* z = Bul(kok, "kat:0");
    REQUIRE(z);
    CHECK(z->baslik == "Zemin");
    CHECK(z->bilgi == "±0,00");
    CHECK(Bul(kok, "kat:2")->bilgi == "+9,00");
    CHECK(Bul(kok, "kat:1")->bilgi == "+4,50");
    const GezginDugumu bos = GezginAgaciKur(*BosOznitelikTablosu());
    CHECK(bos.sayi == 0);
    CHECK(bos.cocuklar.empty());
}

// Node'daki op4_ops.katUyeligi / kullanimYeri / oznitelikCikar ile şablonlar üzerinde karşılaştırma. B'nin işlevleri
// (Op4Ops.TASLAK) ya da D'nin şablonları (op4/veri/sablonlar/dizin.json) henüz yoksa atlanır.
TEST_CASE("gezgin: şablonlarda sayılar node'daki katUyeligi / kullanimYeri ile aynı") {
    const std::string dizin = sinama::Op4Dosyasi("veri/sablonlar/dizin.json");
    const std::string ops = sinama::Op4Dosyasi("js/op4_ops.js");
    if (dizin.empty() || ops.find("\"katUyeligi\", \"kullanimYeri\"") != std::string::npos ||
        std::system("node --version > /dev/null 2>&1") != 0) {
        MESSAGE("atlandı: şablonlar ya da B'nin katUyeligi / kullanimYeri uygulaması henüz yok");
        return;
    }
    const nlohmann::json d = nlohmann::json::parse(dizin, nullptr, false);
    REQUIRE_FALSE(d.is_discarded());
    const nlohmann::json liste = d.is_array() ? d : d.value("sablonlar", nlohmann::json::array());
    int sinanan = 0;
    for (const nlohmann::json& s : liste) {
        const std::string dosya = s.value("dosya", std::string());
        if (dosya.empty()) continue;
        CAPTURE(dosya);
        // Node: model → oznitelikCikar (satırlar + sütunlar) ve beklenen (kat, alt tür, yer) sayıları.
        const std::string betik = "op4_gezgin_sinama.js";  // ctest çalışma klasörü (derleme klasörü)
        {
            std::ofstream f(betik);
            f << "const O=require(process.argv[2]);const fs=require('fs');"
                 "let m=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));if(m.bina)m=m.bina;"
                 "const ku=O.katUyeligi(m),yu=O.kullanimYeri(m),t=O.oznitelikCikar(m,{kat:ku,kullanim:yu});"
                 "const say={};const ekle=(a)=>{say[a]=(say[a]||0)+1;};"
                 "for(const tur of ['cubuk','panel']){for(const no in yu[tur]||{}){const k=(ku[tur]||{})[no]||[];"
                 "for(const kat of new Set(k)){ekle('kat:'+kat+'/alt_tur:'+yu[tur][no].alt_tur);}}}"
                 "process.stdout.write(JSON.stringify({tablo:t,say:say}));";
        }
        const std::string cikti = "op4_gezgin_sinama.json";
        const std::string komut = "node \"" + betik + "\" \"" + std::string(OP4_KAYNAK_DIZINI) + "/js/op4_ops.js\" \"" +
                                  std::string(OP4_KAYNAK_DIZINI) + "/veri/sablonlar/" + dosya + "\" > \"" + cikti + "\"";
        REQUIRE(std::system(komut.c_str()) == 0);
        std::ifstream f(cikti);
        std::stringstream ss;
        ss << f.rdbuf();
        std::remove(betik.c_str());
        std::remove(cikti.c_str());
        const nlohmann::json j = nlohmann::json::parse(ss.str(), nullptr, false);
        REQUIRE_FALSE(j.is_discarded());
        // JS tablosu → OznitelikTablosu (yalnız gezginin okuduğu üç sütun).
        std::vector<Kayit> r;
        const auto& satirlar = j["tablo"]["satirlar"];
        std::map<std::string, const nlohmann::json*> sut;
        for (const auto& c : j["tablo"]["sutunlar"]) sut[c["id"].get<std::string>()] = &c["degerler"];
        for (size_t i = 0; i < satirlar.size(); ++i) {
            Kayit k;
            const auto tur = TurKodundan(satirlar[i]["tur"].get<std::string>());
            if (!tur) continue;
            k.k = {*tur, 0, satirlar[i]["no"].get<uint32_t>()};
            if (sut.count("alt_tur") && (*sut["alt_tur"])[i].is_string()) k.altTur = (*sut["alt_tur"])[i];
            if (sut.count("kullanim_yeri") && (*sut["kullanim_yeri"])[i].is_string()) k.yer = (*sut["kullanim_yeri"])[i];
            if (sut.count("kat") && (*sut["kat"])[i].is_array())
                for (const auto& v : (*sut["kat"])[i]) k.katlar.push_back(v.get<double>());
            r.push_back(k);
        }
        const GezginDugumu kok = GezginAgaciKur(Tablo(r));
        Tutarli(kok);
        for (const auto& [anahtar, sayi] : j["say"].items()) {
            CAPTURE(anahtar);
            const GezginDugumu* n = Bul(kok, anahtar);
            REQUIRE(n);
            CHECK(n->sayi == sayi.get<size_t>());
        }
        ++sinanan;
    }
    MESSAGE("sınanan şablon: " << sinanan);
}
