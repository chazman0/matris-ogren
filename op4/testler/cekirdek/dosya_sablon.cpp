// op4 C++ sınamaları (D) — şablon dökümü (op4/veri/sablonlar/, araclar/sablon_dok.py; kabul D6) ve web sürümü
// dosyalarının içe aktarılması: her şablon .json ve .matris olarak açılınca B'nin Yukle'sine doğrudan verilmiş metinle
// aynı model metnini verir; uygulama kabuğu + B'nin çekirdek modülü + D akışları tümleşik (kabul D3).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cstdlib>
#if !defined(_WIN32)
#include <sys/wait.h>
#endif

#include "cekirdek/kabuk.h"
#include "cekirdek/proje_dosyasi.h"
#include "dosya_sahte.h"

using namespace op4;
using namespace op4::sinama;
using nlohmann::json;
using ojson = nlohmann::ordered_json;

namespace {

std::vector<std::string> SablonAdlari() {
    const json d = json::parse(Op4Dosyasi("veri/sablonlar/dizin.json"));
    std::vector<std::string> o;
    for (const json& s : d["sablonlar"]) o.push_back(s["ad"].get<std::string>());
    return o;
}

std::unique_ptr<ModelCekirdegi> BCekirdegi() {
    CekirdekAyari a;
    a.deterministikSaat = true;
    std::string hata;
    auto c = ModelCekirdegiOlustur(a, hata);
    REQUIRE_MESSAGE(c, hata);
    return c;
}

// Web sürümünün projeKaydet çıktısı: JSON.stringify({tur, surum, uygulama, kaydedildi, bina, gorunum, arac_yerlesimi},
// null, 1) — bina iç içe girintili.
std::string WebMatris(const std::string& sablon) {
    ojson p = ojson::object();
    p["tur"] = "matris-proje";
    p["surum"] = 1;
    p["uygulama"] = "web sürümü";
    p["kaydedildi"] = "2026-10-30T08:00:00.000Z";
    p["bina"] = ojson::parse(sablon);
    p["gorunum"] = {{"mod", "3b"}, {"etiketler", true}};
    p["arac_yerlesimi"] = nullptr;
    return p.dump(1);
}

std::string DTestKurtarma;
DosyaIslemleri* DTestDosya = nullptr;

void DTestModulu(Hizmetler& h, ModulOrtami& o) {
    DosyaIslemleriAyari a;
    a.kurtarmaDizini = DTestKurtarma;
    a.sabitZaman = "2026-10-31T12:00:00Z";
    auto d = std::make_shared<DosyaIslemleri>(h, a);
    d->Kur();
    DTestDosya = o.Tut(d);
    auto c = std::make_shared<CozumAkisi>(h);
    c->Kur();
    o.Tut(c);
}

}  // namespace

TEST_CASE("D6 şablon dökümü: dizin.json ve 9 şablon; her biri bina JSON'u") {
    std::string hata;
    const std::vector<SablonBilgisi> d = SablonDizini(std::string(OP4_KAYNAK_DIZINI) + "/veri", hata);
    REQUIRE_MESSAGE(d.size() == 9, hata);
    for (const SablonBilgisi& s : d) {
        CAPTURE(s.ad);
        CHECK_FALSE(s.baslik.empty());
        CHECK_FALSE(s.aciklama.empty());
        CHECK((s.sistem == "celik" || s.sistem == "betonarme"));
        CHECK(s.kat >= 1);
        CHECK(s.dosya == s.ad + ".json");
        const json b = json::parse(Op4Dosyasi("veri/sablonlar/" + s.dosya));
        CHECK(b["tur"] == "bina");
    }
}

TEST_CASE("D6 döküm güncel (python3 -I op4/araclar/sablon_dok.py --denetle)") {
#ifdef OP4_PYTHON
    std::string komut = std::string("\"") + OP4_PYTHON + "\" -I -X utf8 \"" + OP4_KAYNAK_DIZINI + "/araclar/sablon_dok.py\" --denetle";
#if defined(_WIN32)
    komut = "\"" + komut + "\"";  // cmd /c ilk ve son tırnağı atar
#endif
    const int r = std::system(komut.c_str());
#if defined(_WIN32)
    const int kod = r;
#else
    const int kod = WIFEXITED(r) ? WEXITSTATUS(r) : -1;
#endif
    if (kod == 3) {
        MESSAGE("hesap motoru (numpy, sympy) bu Python'da yok: döküm denetimi atlandı");
        return;
    }
    CHECK_MESSAGE(kod == 0, "şablon dökümü güncel değil: python3 -I op4/araclar/sablon_dok.py");
#else
    MESSAGE("Python bulunamadı: döküm denetimi atlandı");
#endif
}

TEST_CASE("D3 her web şablonu .json ve .matris olarak içe aktarılınca B'nin Yukle'siyle aynı model metni") {
    GeciciDizin d;
    auto ref = BCekirdegi();
    auto alici = BCekirdegi();
    for (const std::string& ad : SablonAdlari()) {
        CAPTURE(ad);
        const std::string sablon = DOrtam::Sablon(ad);
        REQUIRE(ref->Yukle(sablon, "sablon:" + ad).basarili);
        const std::string beklenen = ref->Metin();
        for (const std::string& uzanti : {std::string(".json"), std::string(".matris")}) {
            CAPTURE(uzanti);
            const std::string yol = d.Yol("web " + ad + uzanti);
            DosyaYaz(yol, uzanti == ".json" ? sablon : WebMatris(sablon));
            const OkumaSonucu o = ProjeOku(yol);
            REQUIRE_MESSAGE(o.basarili, o.hata);
            CHECK(o.bicim == (uzanti == ".json" ? DosyaBicimi::BinaJson : DosyaBicimi::Matris));
            const YuklemeSonucu y = alici->Yukle(*o.icerik.Al(proje_yolu::MODEL), "dosya:" + yol);
            REQUIRE_MESSAGE(y.basarili, y.hata);
            CHECK(alici->Metin() == beklenen);
        }
    }
}

TEST_CASE("D1/D3 uygulama kabuğu + B çekirdek modülü + D akışları: şablon → kaydet → aç, .matris / .json, Türkçe yol") {
    GeciciDizin d;
    DTestKurtarma = d.Kur("kurtarma");
    UygulamaKabugu k;
    KabukAyari a;
    a.bilgi.surum = "0.1.0";
    a.bilgi.veriDizini = std::string(OP4_KAYNAK_DIZINI) + "/veri";
    a.bilgi.ayarDizini = d.Kur("ayarlar");
    a.bilgi.testKipi = true;
    a.ortam.testKipi = true;
    a.moduller = {{"cekirdek", "B", &CekirdekModuluKur}, {"dosya-sinama", "D", &DTestModulu}};
    std::string hata;
    REQUIRE_MESSAGE(k.Kur(std::move(a), hata), hata);
    Hizmetler& h = k.H();
    REQUIRE(DTestDosya);
    CHECK(h.belge->PencereBasligi() == "op4 — Adsız 1");
    BetikliIletisimKutulari il;
    h.iletisim = &il;
    auto ref = BCekirdegi();
    const std::string klasor = d.Kur("Proje ŞĞİı");
    for (const std::string& ad : SablonAdlari()) {
        CAPTURE(ad);
        REQUIRE(h.komutlar->Calistir("dosya.yeni_sablon", h, KomutKaynagi::KomutSatiri, ad));
        REQUIRE(ref->Yukle(DOrtam::Sablon(ad), "sablon").basarili);
        const std::string metin = h.cekirdek->Metin();
        CHECK(metin == ref->Metin());
        const std::string yol = klasor + "/" + ad + ".op4";
        REQUIRE(h.komutlar->Calistir("dosya.farkli_kaydet", h, KomutKaynagi::KomutSatiri, yol));
        CHECK(h.belge->Yol() == yol);
        const OkumaSonucu o = ProjeOku(yol);
        REQUIRE(o.basarili);
        CHECK(*o.icerik.Al(proje_yolu::MODEL) == metin);  // model/bina.json = Metin() (bayt bayt)
        REQUIRE(h.komutlar->Calistir("dosya.yeni", h, KomutKaynagi::Menu));
        REQUIRE(h.komutlar->Calistir("dosya.ac", h, KomutKaynagi::KomutSatiri, yol));
        CHECK(h.cekirdek->Metin() == metin);
        CHECK_FALSE(h.belge->Kirli());
        // Web sürümüne ve geri.
        const std::string web = klasor + "/" + ad + ".matris";
        REQUIRE(h.komutlar->Calistir("dosya.bina_disa", h, KomutKaynagi::KomutSatiri, web));
        REQUIRE(h.komutlar->Calistir("dosya.ice_aktar", h, KomutKaynagi::KomutSatiri, web));
        CHECK(h.cekirdek->Metin() == metin);
        CHECK(h.belge->Yol().empty());
        CHECK(h.belge->Ad() == ad);  // içe aktarılan belge kaynak dosyanın gövdesiyle görünür (S15)
    }
    // D10 IFC: B'nin QuickJS çekirdeği (docs/ifc_disari.js secenek.uygulama) uygulama kimliğini dosyaya yazar.
    const std::string ifc = klasor + "/yapı.ifc";
    REQUIRE(h.komutlar->Calistir("dosya.ifc_disa", h, KomutKaynagi::KomutSatiri, ifc));
    const std::string m = DosyaIcerigi(ifc);
    const std::string tam = "op4 \\X2\\00B7\\X0\\ Opus Fortis";  // "op4 · Opus Fortis" (STEP kaçışı)
    CHECK(m.find(",'op4 0.1.0','" + tam + "','');\n") != std::string::npos);  // FILE_NAME
    CHECK(m.find(",'0.1.0','" + tam + "','op4');\n") != std::string::npos);   // IFCAPPLICATION
    CHECK(m.find("=IFCAPPLICATION(") != std::string::npos);
    CHECK(m.find("=IFCORGANIZATION($,'Opus Fortis',$,$,$);") != std::string::npos);
    CHECK(m.find("Matris \\X2\\00D6011F\\X0\\ren") == std::string::npos);  // web varsayılanı ("Matris Öğren") yok
    CHECK(m.find("'2026-10-31T12:00:00'") != std::string::npos);
    k.Kapat();
    DTestDosya = nullptr;
}
