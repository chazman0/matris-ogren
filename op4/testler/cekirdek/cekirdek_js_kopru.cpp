// Model çekirdeği (B) — C++ köprüsü sınamaları (sözleşme S11; MIMARI §9.3, §9.4; kabul B4, B5).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cmath>
#include <map>
#include <set>
#include <string>

#include "cekirdek/hizmetler.h"
#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/proje_belgesi.h"
#include "cekirdek/secim.h"
#include "cekirdek/sonuc.h"
#include "cekirdek_js_yardim.h"

using namespace op4;
using nlohmann::json;

TEST_CASE("cekirdek_js B5: ModelCekirdegiOlustur QuickJS çekirdeğini döndürür; boş model, beyaz liste") {
    std::vector<std::string> gunluk;
    auto c = sinama::CekirdekKur(&gunluk);
    REQUIRE(c);
    bool olcum = false;
    for (const std::string& s : gunluk) olcum = olcum || s.rfind("OP4OLCUM cekirdek_derleme_ms=", 0) == 0;
    CHECK(olcum);
    CHECK(c->IslemAdlari() == std::vector<std::string>{islem::HIZLI_AKS, islem::AKS_SIHIRBAZI, islem::BASLIK_DEGISTIR, islem::GENELLESTIR});
    const YuklemeSonucu y = c->YeniBos("Adsız 1");
    REQUIRE(y.basarili);
    CHECK(y.ozet.baslik == "Adsız 1");
    CHECK(y.ozet.bos);
    const SahnePtr s = c->Sahne();
    REQUIRE(s);
    CHECK(s->baslik == "Adsız 1");
    CHECK(s->ElemanSayisi() == 0);
    REQUIRE(s->seviyeler.size() == 1);
    CHECK(s->seviyeler[0].ad == "±0.00");
    CHECK(s->surum == c->SahneSurumu());
    CHECK(c->Oznitelikler()->sutunlar.size() == BosOznitelikTablosu()->sutunlar.size());
    CHECK(c->Oznitelikler()->satirlar.empty());
    const json m = json::parse(c->Metin());
    CHECK(m["tur"] == "bina");
    CHECK(m["surum"] == 3);
    CHECK_FALSE(c->GeriAlBilgisi().geriAlinabilir);
}

TEST_CASE("cekirdek_js B5: 9 şablonun sahnesi — sayılar JS ile aynı, dizinler tutarlı, sınır kutuları dolu") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    // node'daki op4_ops.test.js ile aynı beklenen değerler (düğüm, çubuk, panel, mesnet)
    const std::map<std::string, std::array<size_t, 4>> beklenen = {
        {"betonarme-tek-aciklik", {8, 8, 1, 4}},   {"betonarme-2kat-3x2", {18, 26, 4, 6}},          {"betonarme-3kat-3x3", {36, 63, 12, 9}},
        {"celik-1kat-depo", {12, 13, 2, 6}},        {"betonarme-4kat-4x3", {60, 116, 24, 12}},      {"betonarme-3kat-surekli-temel", {36, 63, 12, 9}},
        {"betonarme-4kat-radye", {60, 116, 24, 12}}, {"celik-sanayi-4hol", {232, 423, 124, 43}},   {"celik-cbf-3kat", {55, 119, 18, 12}},
    };
    uint64_t onceki = c->SahneSurumu();
    for (const std::string& ad : sinama::SablonAdlari()) {
        CAPTURE(ad);
        const YuklemeSonucu y = c->Yukle(sinama::Sablon(ad), "sablon:" + ad);
        REQUIRE_MESSAGE(y.basarili, y.hata);
        const SahnePtr s = c->Sahne();
        CHECK(s->surum > onceki);
        onceki = s->surum;
        const auto& b = beklenen.at(ad);
        CHECK(s->dugumler.size() == b[0]);
        CHECK(s->cubuklar.size() == b[1]);
        CHECK(s->paneller.size() == b[2]);
        CHECK(s->mesnetler.size() == b[3]);
        CHECK_FALSE(s->sinir.Bos());
        CHECK(s->modelSurumu == json::parse(sinama::Sablon(ad))["surum"].get<int>());
        for (const SahneCubugu& x : s->cubuklar) {
            REQUIRE(x.i < s->dugumler.size());
            REQUIRE(x.j < s->dugumler.size());
            CHECK(s->Var(CubukKimligi(x.no)));
            CHECK(std::abs(Uzunluk(x.yYerel) - 1.0) < 1e-9);
            CHECK((x.kesit == SAHNE_YOK || x.kesit < s->kesitler.size()));
        }
        for (const SahnePaneli& p : s->paneller) {
            CHECK(p.koseSayisi >= 3);
            CHECK(s->Var(PanelKimligi(p.no)));
        }
        // öznitelik tablosu: her eleman bir satır, aynı sahne sürümü
        const OznitelikPtr t = c->Oznitelikler();
        CHECK(t->sahneSurumu == s->surum);
        CHECK(t->satirlar.size() == s->cubuklar.size() + s->paneller.size() + s->dugumler.size() + s->mesnetler.size());
        CHECK(t->sutunlar.size() == 23);
        for (const SahneCubugu& x : s->cubuklar) CHECK(t->Satir(CubukKimligi(x.no)).has_value());
        CHECK(y.ozet.baslik == json::parse(sinama::Sablon(ad))["baslik"].get<std::string>());
    }
}

TEST_CASE("cekirdek_js B5: sahne ayrıntıları — aks–kat görünümü, kolon kesiti, mafsal temel, akslar, seviyeler") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    REQUIRE(c->Yukle(sinama::Sablon("celik-1kat-depo"), "s").basarili);
    const SahnePtr s = c->Sahne();
    size_t kolon = 0, kiris = 0;
    for (const SahneCubugu& x : s->cubuklar) {
        if (x.tur == CubukTuru::Kolon) {
            ++kolon;
            REQUIRE(x.kesit < s->kesitler.size());
            CHECK(s->kesitler[x.kesit].ad == "HEB240");
            CHECK(s->kesitler[x.kesit].profil == "HEB 240");
            CHECK(s->kesitler[x.kesit].tur == KesitTuru::I);
            CHECK(s->kesitler[x.kesit].h == doctest::Approx(0.24));
        }
        if (x.tur == CubukTuru::Kiris) ++kiris;
    }
    CHECK(kolon == 6);
    CHECK(kiris == 7);
    for (const SahneMesnedi& m : s->mesnetler) {
        CHECK(m.maske == 0x07);
        CHECK(m.tur == MesnetTuru::Mafsal);
        CHECK((s->dugumler[m.dugum].bayrak & dugum_bayragi::MESNETLI));
    }
    REQUIRE(s->temeller.size() == 6);
    CHECK(s->temeller[0].tur == TemelTuru::Tekil);
    CHECK(s->temeller[0].B == doctest::Approx(1.5));
    CHECK(s->Var(s->temeller[0].kimlik));
    REQUIRE(s->akslar.size() == 5);
    CHECK(s->akslar[1].ad == "B");
    CHECK(s->akslar[1].kimlik == ElemanKimligi{ElemanTuru::Aks, 0, 1});
    CHECK(s->akslar[1].bas.x == doctest::Approx(6));
    CHECK(s->akslar[1].bas.y == doctest::Approx(-1.5));
    CHECK(s->Var(s->akslar[1].kimlik));
    REQUIRE(s->seviyeler.size() == 2);
    CHECK(s->seviyeler[1].kat == 1);
    CHECK(s->seviyeler[1].z == doctest::Approx(5.0));
    // aks–kat düğüm numarası 1000·kat + 20·ix + iy + 1
    CHECK(s->DugumDizini(1000 + 20 * 2 + 1 + 1).has_value());
}

TEST_CASE("cekirdek_js B4/B5: işlemler, rapor, geri al / yinele ve ortak akış (ModelIslemiUygula)") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    Hizmetler h;
    BetikliIletisimKutulari il;
    GunlukBildirimleri bl(nullptr);
    ProjeBelgesi belge;
    Secim secim;
    GorunumDurumu gorunum;
    SonucDurumu sonuc;
    h.cekirdek = c.get();
    h.iletisim = &il;
    h.bildirim = &bl;
    h.belge = &belge;
    h.secim = &secim;
    h.gorunum = &gorunum;
    h.sonuc = &sonuc;
    int sahneOlay = 0;
    h.sahneDegisti.Abone([&] { ++sahneOlay; });
    ModelYuklendi(h, c->YeniBos("Adsız 1"));

    IslemRaporu r = ModelIslemiUygula(h, islem::HIZLI_AKS, R"({"x":[6,6],"y":[5],"z":[3.5,3]})");
    REQUIRE_MESSAGE(r.basarili, r.hata);
    CHECK(r.icerikDegisti);
    CHECK(r.ModelDegisti());
    CHECK(r.eklenen.size() == 5);
    for (const ElemanKimligi& k : r.eklenen) CHECK(k.tur == ElemanTuru::Aks);
    CHECK(r.sahneSurumu == c->SahneSurumu());
    CHECK(belge.Kirli());
    CHECK(c->Sahne()->akslar.size() == 5);
    CHECK(c->Sahne()->seviyeler.size() == 3);
    CHECK(c->GeriAlBilgisi().geriAlAdi == "Hızlı aks");
    CHECK(c->Ozet().aks == 5);

    r = ModelIslemiUygula(h, islem::BASLIK_DEGISTIR, R"({"baslik":"Depo"})");
    CHECK(r.ModelDegisti());
    CHECK(r.eklenen.empty());
    CHECK(c->Sahne()->baslik == "Depo");
    CHECK(c->GeriAlBilgisi().adim == 2);

    r = ModelIslemiUygula(h, "yokBoyle", "{}");
    CHECK_FALSE(r.basarili);
    CHECK(r.hata.find("Bilinmeyen işlem") != std::string::npos);
    r = ModelIslemiUygula(h, islem::HIZLI_AKS, "{}");
    CHECK_FALSE(r.basarili);

    r = GeriAlUygula(h);
    CHECK(r.ModelDegisti());
    CHECK(c->Sahne()->baslik == "Adsız 1");
    CHECK(c->GeriAlBilgisi().yineleAdi == "Başlık değiştir");
    r = GeriAlUygula(h);
    CHECK(r.silinen.size() == 5);
    CHECK(c->Sahne()->akslar.empty());
    r = GeriAlUygula(h);
    CHECK_FALSE(r.basarili);
    r = YineleUygula(h);
    CHECK(r.eklenen.size() == 5);
    CHECK(sahneOlay >= 5);
}

TEST_CASE("cekirdek_js B4: C1 genel modele geçiş — Vazgeç modeli değiştirmez, Dönüştür aks–kat modelini çevirir") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    Hizmetler h;
    BetikliIletisimKutulari il;
    GunlukBildirimleri bl(nullptr);
    ProjeBelgesi belge;
    h.cekirdek = c.get();
    h.iletisim = &il;
    h.bildirim = &bl;
    h.belge = &belge;
    REQUIRE(c->Yukle(sinama::Sablon("betonarme-3kat-surekli-temel"), "s").basarili);
    const std::string once = c->Metin();
    const size_t cubuk = c->Sahne()->cubuklar.size();
    il.yanitlar = {"1"};
    IslemRaporu r = ModelIslemiUygula(h, islem::GENELLESTIR, "{}");
    CHECK_FALSE(r.basarili);
    CHECK(il.sorulanlar.size() == 1);
    CHECK(c->Metin() == once);
    CHECK_FALSE(belge.Kirli());
    il.yanitlar = {"0"};
    r = ModelIslemiUygula(h, islem::GENELLESTIR, "{}");
    REQUIRE_MESSAGE(r.basarili, r.hata);
    CHECK_FALSE(r.gecisOnayi);
    CHECK(r.ModelDegisti());
    CHECK(belge.Kirli());
    const json m = json::parse(c->Metin());
    CHECK(m["surum"] == 3);
    CHECK(m["kolonlar"].empty());
    CHECK(m["temeller"]["tip"] == "tekil");
    CHECK(c->Sahne()->cubuklar.size() == cubuk);  // genel görünüm kimlikleri dönüşümde korunur
    for (const ElemanKimligi& k : r.degisen) CHECK(k.tur == ElemanTuru::Temel);
    bool uyari = false;
    for (const std::string& u : r.uyarilar) uyari = uyari || u.find("Mütemadi (sürekli) temel tekil temele çevrildi") != std::string::npos;
    CHECK(uyari);
}

TEST_CASE("cekirdek_js B4: kanonik metin, yükleme hataları, geri al sınırı") {
    auto c = sinama::CekirdekKur(nullptr, 2);
    REQUIRE(c);
    REQUIRE(c->Yukle(sinama::Sablon("celik-cbf-3kat"), "s").basarili);
    const std::string m1 = c->Metin();
    CHECK(c->Metin() == m1);
    REQUIRE(c->Yukle(m1, "kurtarma").basarili);
    CHECK(c->Metin() == m1);
    const uint64_t surum = c->SahneSurumu();
    YuklemeSonucu y = c->Yukle("{bozuk", "dosya:x.json");
    CHECK_FALSE(y.basarili);
    CHECK(y.hata.find("geçerli JSON değil") != std::string::npos);
    y = c->Yukle(R"({"tur":"matris"})", "dosya:y.json");
    CHECK_FALSE(y.basarili);
    CHECK(c->Metin() == m1);
    CHECK(c->SahneSurumu() == surum);
    for (int i = 0; i < 4; ++i) CHECK(c->Uygula(islem::BASLIK_DEGISTIR, R"({"baslik":"B)" + std::to_string(i) + "\"}").basarili);
    CHECK(c->GeriAlBilgisi().adim == 2);
    // sarmalayıcı: bina_sablon yanıtı {"ad", "bina"}
    const std::string sarili = std::string(R"({"ad":"x","bina":)") + sinama::Sablon("celik-1kat-depo") + "}";
    CHECK(c->Yukle(sarili, "sablon:celik-1kat-depo").basarili);
    CHECK(c->Ozet().cubuk == 13);
    CHECK(c->Ozet().surum == 1);
}

TEST_CASE("cekirdek_js B5: öznitelikler — gezgin alanları, ortak özellikler, gösterim") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    REQUIRE(c->Yukle(sinama::Sablon("betonarme-3kat-3x3"), "s").basarili);
    const OznitelikPtr t = c->Oznitelikler();
    const SahnePtr s = c->Sahne();
    std::vector<ElemanKimligi> kolonlar;
    std::map<std::string, int> yer;
    for (const SahneCubugu& x : s->cubuklar) {
        if (x.tur != CubukTuru::Kolon) continue;
        kolonlar.push_back(CubukKimligi(x.no));
        const auto r = t->Satir(CubukKimligi(x.no));
        REQUIRE(r);
        CHECK(t->Metin(*r, oznitelik::ALT_TUR) == std::optional<std::string_view>("kolon"));
        ++yer[std::string(*t->Metin(*r, oznitelik::KULLANIM_YERI))];
        CHECK(t->Liste(*r, oznitelik::KAT).size() == 1);
        CHECK(t->Sayi(*r, oznitelik::UZUNLUK) == doctest::Approx(3.2));
        CHECK(t->Metin(*r, oznitelik::SISTEM) == std::optional<std::string_view>("betonarme"));
    }
    CHECK(kolonlar.size() == 27);
    CHECK(yer["kose"] == 12);
    CHECK(yer["kenar"] == 12);
    CHECK(yer["ic"] == 3);
    const auto o = OrtakOzellikler(*t, kolonlar);
    std::map<std::string, std::string> om(o.begin(), o.end());
    CHECK(om[oznitelik::ALT_TUR] == "kolon");
    CHECK(om[oznitelik::UZUNLUK] == "3,2 m");
    CHECK(om[oznitelik::KULLANIM_YERI] == "(çeşitli)");
    CHECK(om[oznitelik::KAT] == "(çeşitli)");
    CHECK(om[oznitelik::KESIT] == "S45x45");
    const auto r = t->Satir(kolonlar[0]);
    CHECK(t->Gosterim(*r, *t->Sutun(oznitelik::KAT)) == "1");
}

TEST_CASE("cekirdek_js B5: denetle, sonuç eşleme, IFC dışa aktarma") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    for (const std::string ad : {"betonarme-tek-aciklik", "celik-cbf-3kat"}) {
        CAPTURE(ad);
        REQUIRE(c->Yukle(sinama::Sablon(ad), "s").basarili);
        const DenetimSonucu d = c->Denetle();
        CHECK(d.serbestDugum == 0);
        const SonucEslemesi e = c->SonucEsle(sinama::Op4Dosyasi("testler/derlem/sonuclar/" + ad + ".json"));
        REQUIRE_MESSAGE(e.basarili, e.hata);
        CHECK(e.uyarilar.empty());
        CHECK(e.elemanlar.size() == c->Sahne()->cubuklar.size());
        for (size_t i = 1; i < e.elemanlar.size(); ++i) CHECK(e.elemanlar[i - 1].kimlik < e.elemanlar[i].kimlik);
        for (const ElemanSonucu& x : e.elemanlar) {
            CHECK(x.kimlik.tur == ElemanTuru::Cubuk);
            CHECK(x.dc > 0);
            CHECK(x.tasarimSatiri >= 0);
            CHECK_FALSE(x.belirleyen.empty());
        }
    }
    const std::string sec = R"({"uygulama":{"ad":"op4","surum":"0.1.0","firma":"Opus Fortis"},"zaman":"2026-10-30T12:00:00"})";
    const IfcSonucu a = c->IfcDisari(sec, "");
    REQUIRE_MESSAGE(a.basarili, a.hata);
    CHECK(a.metin.rfind("ISO-10303-21;", 0) == 0);
    CHECK(a.metin.find("IFCAPPLICATION(") != std::string::npos);
    CHECK(a.metin.find("'op4'") != std::string::npos);
    CHECK(a.metin.find("'Opus Fortis'") != std::string::npos);
    CHECK(a.dosyaAdi.size() > 4);
    CHECK(c->IfcDisari(sec, "").metin == a.metin);
    const IfcSonucu z = c->IfcDisari("{}", "");  // deterministik saat: ilk Date.now 2026-01-01T00:00:00Z'den
    CHECK(z.metin.find("'2026-01-01T00:00:") != std::string::npos);
    // boş model: denetle "model_dolu" koşulu dışında da çalışır
    c->YeniBos("Adsız 1");
    CHECK(c->Denetle().uyarilar.empty());
    CHECK_FALSE(c->SonucEsle("null").basarili);
}
