// Model çekirdeği (B) — eşdeğerlik derlemi (MIMARI §9.5, D35; kabul B5, B6).
//   1. op4/testler/derlem/derlem.jsonl'deki her (işlem, girdi, çıktı) üçlüsü, ürünün gömülü JS kaynaklarıyla kurulan QuickJS
//      ortamında yeniden oynatılır; çıktı node'un kaydıyla aynı olmalıdır: sayılarda bağıl 1e-12
//      (|a − b| ≤ 1e-12 · max(1, |a|, |b|)), diğer alanlar birebir (karşılaştırma C++'ta, nlohmann ağaçları üstünde).
//   2. 9 şablon C++ köprüsünden (ModelCekirdegi) açılır: Sahne() sayıları node'da ModelOps.genellestir'den sayılanlarla,
//      sahne dizileri node'un Op4Ops.sahneCikar çıktısıyla aynıdır; Metin() node'un kanonik metniyle bayt bayt aynıdır ve
//      gidiş-dönüşte değişmez; IfcDisari() node'daki cephe çıktısıyla bayt bayt aynıdır.
// Derlem node'da üretilir: node op4/testler/js/derlem_uret.js (docs/ modülleri değişince yeniden).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "cekirdek_js/js_ortami.h"
#include "cekirdek_js_yardim.h"

using namespace op4;
using nlohmann::json;

namespace {

constexpr double kTol = 1e-12;

struct Derlem {
    json ust;
    std::vector<std::string> satirlar;  // üçlüler (ham JSON satırları)
    std::vector<json> kayitlar;
};

const Derlem& DerlemAl() {
    static const Derlem d = [] {
        Derlem r;
        std::istringstream s(sinama::Op4Dosyasi("testler/derlem/derlem.jsonl"));
        std::string satir;
        bool ilk = true;
        while (std::getline(s, satir)) {
            if (satir.empty()) continue;
            if (ilk) {
                r.ust = json::parse(satir);
                ilk = false;
                continue;
            }
            r.kayitlar.push_back(json::parse(satir));
            r.satirlar.push_back(std::move(satir));
        }
        return r;
    }();
    return d;
}

bool SayiMi(const json& j) { return j.is_number(); }

// İlk farkın yolu ve açıklaması; eşitse boş.
std::string Fark(const json& a, const json& b, const std::string& yol = "") {
    if (SayiMi(a) && SayiMi(b)) {
        const double x = a.get<double>(), y = b.get<double>();
        if (x == y || std::abs(x - y) <= kTol * std::max({1.0, std::abs(x), std::abs(y)})) return {};
        char t[96];
        std::snprintf(t, sizeof(t), ": %.17g ≠ %.17g", x, y);
        return yol + t;
    }
    if (a.type() != b.type()) return yol + ": tür " + std::string(a.type_name()) + " ≠ " + b.type_name();
    if (a.is_array()) {
        if (a.size() != b.size()) return yol + ": uzunluk " + std::to_string(a.size()) + " ≠ " + std::to_string(b.size());
        for (size_t i = 0; i < a.size(); ++i)
            if (std::string f = Fark(a[i], b[i], yol + "[" + std::to_string(i) + "]"); !f.empty()) return f;
        return {};
    }
    if (a.is_object()) {
        if (a.size() != b.size()) return yol + ": anahtar sayısı " + std::to_string(a.size()) + " ≠ " + std::to_string(b.size());
        for (auto i = a.begin(); i != a.end(); ++i) {
            const auto k = b.find(i.key());
            if (k == b.end()) return yol + ": '" + i.key() + "' yok";
            if (std::string f = Fark(i.value(), *k, yol + "." + i.key()); !f.empty()) return f;
        }
        return {};
    }
    if (a == b) return {};
    return yol + ": " + a.dump().substr(0, 100) + " ≠ " + b.dump().substr(0, 100);
}

// Ürünün gömülü kaynaklarıyla QuickJS ortamı + derlem_ortak.js + şablon / sonuç metinleri.
class DerlemOrtami {
public:
    DerlemOrtami() : o_(Ayar()) {
        std::string hata;
        kuruldu_ = o_.Kur(hata);
        REQUIRE_MESSAGE(kuruldu_, hata);
        std::string r;
        REQUIRE_MESSAGE(o_.Degerlendir(sinama::Op4Dosyasi("testler/derlem/derlem_ortak.js"), "op4/testler/derlem/derlem_ortak.js", r, hata),
                        hata);
        const char* kurulum = R"JS(
globalThis.__derlem = {
  baglam: { sablonlar: {}, sonuclar: {} },
  M: { ModelOps: self.ModelOps, MatrisAks: self.MatrisAks, MatrisBinaCizim: self.MatrisBinaCizim, MatrisIFC: self.MatrisIFC,
       MatrisTablo: self.MatrisTablo, Op4Ops: self.Op4Ops, Op4Cekirdek: self.Op4Cekirdek },
  koy: function (tur, ad, metin) { this.baglam[tur][ad] = metin; },
  calistir: function (satir) {
    let r;
    try { r = DerlemOrtak.calistir(this.M, JSON.parse(satir), this.baglam); } catch (e) { r = { hata: String(e) + (e && e.stack ? "\n" + e.stack : "") }; }
    return JSON.stringify(r);
  },
  ozet: function (metin) { return JSON.stringify(DerlemOrtak.metinOzeti(metin)); },
};
DerlemOrtak.saatSabitle(globalThis);
)JS";
        REQUIRE_MESSAGE(o_.Degerlendir(kurulum, "derlem_kurulum", r, hata), hata);
        const Derlem& d = DerlemAl();
        for (const auto& ad : d.ust["sablonlar"])
            Koy("sablonlar", ad.get<std::string>(), sinama::Sablon(ad.get<std::string>()));
        for (const auto& ad : d.ust["sonuclar"])
            Koy("sonuclar", ad.get<std::string>(), sinama::Op4Dosyasi("testler/derlem/sonuclar/" + ad.get<std::string>() + ".json"));
    }
    json Calistir(const std::string& satir, std::string& hata) {
        std::string r;
        if (!o_.CagirMetin("__derlem.calistir", {satir}, r, hata)) return nullptr;
        return json::parse(r);
    }
    json Ozet(const std::string& metin) {
        std::string r, hata;
        REQUIRE_MESSAGE(o_.CagirMetin("__derlem.ozet", {metin}, r, hata), hata);
        return json::parse(r);
    }

private:
    static JsOrtamiAyari Ayar() {
        JsOrtamiAyari a;
        a.deterministikSaat = true;
        return a;
    }
    void Koy(const char* tur, const std::string& ad, const std::string& metin) {
        std::string r, hata;
        REQUIRE_MESSAGE(o_.CagirMetin("__derlem.koy", {tur, ad, metin}, r, hata), hata);
    }
    JsOrtami o_;
    bool kuruldu_ = false;
};

// Kodlanmış tipli dizi {"$t": …, "v": […]} → değerler.
std::vector<double> Tipli(const json& j) {
    std::vector<double> v;
    for (const json& x : j.at("v")) v.push_back(x.is_number() ? x.get<double>() : std::nan(""));
    return v;
}

const json* SablonKaydi(const std::string& m, const std::string& f, const std::string& sablon, size_t argSayisi = 0) {
    for (const json& k : DerlemAl().kayitlar) {
        if (k["m"] != m || k["f"] != f) continue;  // kaynak sınama da olabilir (aynı üçlü tekrar yazılmaz)
        const json& a = k["a"];
        if (a.empty()) continue;
        const json& a0 = a[0];
        const bool eslesir = (a0.is_object() && a0.value("$sablon", "") == sablon) ||
                             (a0.is_object() && a0.contains("model") && a0["model"].is_object() && a0["model"].value("$sablon", "") == sablon);
        if (eslesir && (argSayisi == 0 || a.size() == argSayisi)) return &k;
    }
    return nullptr;
}

// Şablonun cephe senaryosunda `yontem` adımının (n'inci) çıktısı.
const json* SenaryoAdimi(const std::string& sablon, const std::string& yontem, int n = 0) {
    for (const json& k : DerlemAl().kayitlar) {
        if (k["m"] != "$senaryo" || k["f"] != "cephe") continue;
        const json& adimlar = k["a"][0]["adimlar"];
        if (adimlar.empty() || adimlar[0].size() < 2 || !adimlar[0][1].is_object() || adimlar[0][1].value("$sablonMetin", "") != sablon)
            continue;
        for (size_t i = 0; i < adimlar.size(); ++i)
            if (adimlar[i][0] == yontem && n-- == 0) return &k["s"][i];
    }
    return nullptr;
}

}  // namespace

TEST_CASE("cekirdek_js B6: eşdeğerlik derlemi — her üçlü QuickJS'te node çıktısıyla aynı (sayılarda bağıl 1e-12)") {
    const Derlem& d = DerlemAl();
    REQUIRE(d.kayitlar.size() > 1000);
    CHECK(d.ust["sayi"].get<size_t>() == d.kayitlar.size());
    DerlemOrtami o;
    std::map<std::string, int> islev, kaynak;
    std::vector<std::string> farklar;
    size_t oynanan = 0, yalnizNode = 0;
    const auto t0 = std::chrono::steady_clock::now();
    for (size_t i = 0; i < d.kayitlar.size(); ++i) {
        const json& k = d.kayitlar[i];
        const std::string ad = k["m"].get<std::string>() + "." + k["f"].get<std::string>();
        if (k.value("q", "") == "node") {
            ++yalnizNode;
            continue;
        }
        std::string hata;
        const json r = o.Calistir(d.satirlar[i], hata);
        ++oynanan;
        ++islev[ad];
        ++kaynak[k.value("k", "?")];
        std::string f;
        if (r.is_null()) f = "çağrı başarısız: " + hata.substr(0, 300);
        else if (r.contains("hata")) f = "oynatma hatası: " + r["hata"].get<std::string>().substr(0, 300);
        else {
            json beklenen = json::object();
            if (k.contains("s")) beklenen["s"] = k["s"];
            else beklenen["h"] = k["h"];
            f = Fark(beklenen, r);
        }
        if (!f.empty()) farklar.push_back("#" + std::to_string(i + 1) + " " + ad + " (" + k.value("k", "?") + ")" + f);
    }
    const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    std::printf("OP4OLCUM senaryo=cekirdek_derlem ucluler=%zu islev=%zu yalniz_node=%zu fark=%zu sure_ms=%.0f\n", oynanan, islev.size(),
                yalnizNode, farklar.size(), ms);
    for (size_t i = 0; i < farklar.size() && i < 25; ++i) MESSAGE(farklar[i]);
    CHECK(farklar.empty());
    CHECK(oynanan + yalnizNode == d.kayitlar.size());
    CHECK(islev.size() >= 150);                       // derlem bütün çekirdek modüllerini geniş kapsar
    for (const char* m : {"sablon", "testler/js/model_ops.test.js", "testler/js/aks_sistemi.test.js", "testler/js/bina_cizim.test.js",
                          "testler/js/ifc_disari.test.js", "testler/js/tablo_editoru.test.js", "op4/testler/js/op4_ops.test.js"})
        CHECK_MESSAGE(kaynak[m] > 0, m);
}

TEST_CASE("cekirdek_js B5: 9 şablon C++ köprüsünden — sayılar ModelOps ile, sahne dizileri node ile, Metin() ve IFC bayt bayt aynı") {
    auto c = sinama::CekirdekKur();
    REQUIRE(c);
    DerlemOrtami o;
    const std::string sec = R"({"uygulama":{"ad":"op4","surum":"0.1.0","firma":"Opus Fortis"},"zaman":"2026-10-30T12:00:00"})";
    for (const std::string& ad : sinama::SablonAdlari()) {
        CAPTURE(ad);
        const std::string metin = sinama::Sablon(ad);
        const YuklemeSonucu y = c->Yukle(metin, "sablon:" + ad);
        REQUIRE_MESSAGE(y.basarili, y.hata);
        const SahnePtr s = c->Sahne();

        // (1) sayılar: node'da ModelOps.genellestir + dugumNo ile sayılan
        const json* say = SablonKaydi("$senaryo", "sayilar", ad);
        REQUIRE(say);
        CHECK(s->dugumler.size() == (*say)["s"]["dugum"].get<size_t>());
        CHECK(s->cubuklar.size() == (*say)["s"]["cubuk"].get<size_t>());
        CHECK(s->paneller.size() == (*say)["s"]["panel"].get<size_t>());
        CHECK(y.ozet.cubuk + y.ozet.panel > 0);

        // (2) sahne dizileri: node'un Op4Ops.sahneCikar(şablon, 1) çıktısı
        const json* sc = SablonKaydi("Op4Ops", "sahneCikar", ad, 2);
        REQUIRE(sc);
        const json& n = (*sc)["s"];
        const std::vector<double> dno = Tipli(n["dugumler"]["no"]), xyz = Tipli(n["dugumler"]["xyz"]);
        REQUIRE(dno.size() == s->dugumler.size());
        for (size_t i = 0; i < dno.size(); ++i) {
            CHECK(s->dugumler[i].no == dno[i]);
            CHECK(s->dugumler[i].p.x == doctest::Approx(xyz[3 * i]).epsilon(kTol));
            CHECK(s->dugumler[i].p.y == doctest::Approx(xyz[3 * i + 1]).epsilon(kTol));
            CHECK(s->dugumler[i].p.z == doctest::Approx(xyz[3 * i + 2]).epsilon(kTol));
        }
        const std::vector<double> cno = Tipli(n["cubuklar"]["no"]), ci = Tipli(n["cubuklar"]["i"]), cj = Tipli(n["cubuklar"]["j"]),
                                  ctur = Tipli(n["cubuklar"]["tur"]), cser = Tipli(n["cubuklar"]["serbestlik"]),
                                  ckes = Tipli(n["cubuklar"]["kesit"]), cy = Tipli(n["cubuklar"]["y_yerel"]);
        REQUIRE(cno.size() == s->cubuklar.size());
        for (size_t i = 0; i < cno.size(); ++i) {
            const SahneCubugu& x = s->cubuklar[i];
            CHECK(x.no == cno[i]);
            CHECK(x.i == ci[i]);
            CHECK(x.j == cj[i]);
            CHECK(static_cast<double>(x.tur) == ctur[i]);
            CHECK(x.serbestlik == cser[i]);
            CHECK(x.kesit == ckes[i]);
            CHECK(x.yYerel.x == doctest::Approx(cy[3 * i]).epsilon(kTol));
            CHECK(x.yYerel.z == doctest::Approx(cy[3 * i + 2]).epsilon(kTol));
        }
        const std::vector<double> pno = Tipli(n["paneller"]["no"]), pkose = Tipli(n["paneller"]["kose"]);
        REQUIRE(pno.size() == s->paneller.size());
        REQUIRE(pkose.size() == s->panelKoseleri.size());
        for (size_t i = 0; i < pkose.size(); ++i) CHECK(s->panelKoseleri[i] == pkose[i]);
        const std::vector<double> md = Tipli(n["mesnetler"]["dugum"]), mm = Tipli(n["mesnetler"]["maske"]);
        REQUIRE(md.size() == s->mesnetler.size());
        for (size_t i = 0; i < md.size(); ++i) {
            CHECK(s->mesnetler[i].dugum == md[i]);
            CHECK(s->mesnetler[i].maske == mm[i]);
        }
        CHECK(s->temeller.size() == n["temeller"].size());
        CHECK(s->akslar.size() == n["akslar"].size());
        CHECK(s->seviyeler.size() == n["seviyeler"].size());
        CHECK(s->kesitler.size() == n["kesitler"].size());

        // (3) Metin(): node'da JSON.stringify(JSON.parse(şablon)) ile aynı (özet), gidiş-dönüşte bayt bayt aynı
        const std::string m1 = c->Metin();
        const json* oz = SenaryoAdimi(ad, "metinOzeti");
        REQUIRE(oz);
        CHECK(o.Ozet(m1) == *oz);
        REQUIRE(c->Yukle(m1, "kurtarma").basarili);
        CHECK(c->Metin() == m1);

        // (4) IFC: cephe senaryosundaki ifcDisari / ifcOzeti ile aynı. Senaryodaki model: genel modele dönüştürülmüş (aks–kat
        //     şablonlarında; genel şablon olduğu gibi kalır) ve başlığı "Derlem <ad>".
        const IslemRaporu g = c->Uygula(islem::GENELLESTIR, R"({"onay":true})");
        REQUIRE_MESSAGE(g.basarili, g.hata);
        REQUIRE(c->Uygula(islem::BASLIK_DEGISTIR, json{{"baslik", "Derlem " + ad}}.dump()).basarili);
        const IfcSonucu ifc = c->IfcDisari(sec, "");
        REQUIRE_MESSAGE(ifc.basarili, ifc.hata);
        if (const json* tam = SenaryoAdimi(ad, "ifcDisari")) {
            CHECK(ifc.metin == (*tam)["metin"].get<std::string>());
            CHECK(ifc.dosyaAdi == (*tam)["dosya_adi"].get<std::string>());
        } else {
            const json* io = SenaryoAdimi(ad, "ifcOzeti");
            REQUIRE(io);
            CHECK(o.Ozet(ifc.metin) == (*io)["metin"]);
            CHECK(ifc.dosyaAdi == (*io)["dosya_adi"].get<std::string>());
        }
    }
}
