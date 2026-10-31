// Model çekirdeği (B) — QuickJS ortamı ve ön yükleme sınamaları (MIMARI §9.2; kabul B1, B2).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cstdio>
#include <string>
#include <vector>

#include "cekirdek_js/js_gomulu.h"
#include "cekirdek_js/js_ortami.h"
#include "sinama_yardim.h"

using namespace op4;
using nlohmann::json;

namespace {

struct Ortam {
    std::vector<std::string> gunluk;
    JsOrtami o;
    explicit Ortam(JsOrtamiAyari a = {}) : o(Ayar(std::move(a), gunluk)) {}
    static JsOrtamiAyari Ayar(JsOrtamiAyari a, std::vector<std::string>& g) {
        a.gunluk = [&g](std::string_view s) { g.emplace_back(s); };
        return a;
    }
    json Js(const std::string& kod) {
        std::string s, hata;
        REQUIRE_MESSAGE(o.Degerlendir(kod, "sinama.js", s, hata), hata);
        return s.empty() ? json() : json::parse(s);
    }
};

}  // namespace

TEST_CASE("cekirdek_js B2: gömülü dosyalar sırayla yüklenir, derleme süresi ölçülür") {
    size_t n = 0;
    const GomuluJs* d = GomuluJsDosyalari(n);
    std::vector<std::string> adlar;
    for (size_t i = 0; i < n; ++i) {
        adlar.emplace_back(d[i].ad);
        CHECK(d[i].veri[d[i].boyut] == 0);  // JS_Eval sıfır sonlu girdi ister
        // gömülü içerik depodaki dosyanın aynısıdır
        CHECK_MESSAGE(sinama::DepoDosyasi(d[i].ad) == std::string(reinterpret_cast<const char*>(d[i].veri), d[i].boyut), d[i].ad);
    }
    CHECK(adlar == std::vector<std::string>{"op4/js/op4_onyukleme.js", "docs/aks_sistemi.js", "docs/model_ops.js", "docs/bina_cizim.js",
                                            "docs/ifc_disari.js", "docs/tablo_editoru.js", "op4/js/op4_ops.js", "op4/js/op4_cekirdek.js",
                                            "op4/js/op4_kopru.js"});
    Ortam t;
    std::string hata;
    REQUIRE_MESSAGE(t.o.Kur(hata), hata);
    CHECK(t.o.YuklenenDosyalar() == adlar);
    CHECK(t.o.DerlemeMs() > 0);
    CHECK(t.o.YuklenenBayt() > 500000);
    std::printf("OP4OLCUM senaryo=cekirdek cekirdek_derleme_ms=%.1f dosya=%zu bayt=%zu bellek_kb=%zu\n", t.o.DerlemeMs(),
                t.o.YuklenenDosyalar().size(), t.o.YuklenenBayt(), t.o.BellekKullanimi() / 1024);
}

TEST_CASE("cekirdek_js B2: ön yükleme — self, window / document yok, modüller self üstünde") {
    Ortam t;
    std::string hata;
    REQUIRE_MESSAGE(t.o.Kur(hata), hata);
    const json j = t.Js(
        "({self: self === globalThis, window: typeof window, document: typeof document,"
        " moduller: ['ModelOps','MatrisAks','MatrisBinaCizim','MatrisIFC','MatrisTablo','Op4Ops','Op4Cekirdek','Op4Kopru']"
        ".map(function (a) { return typeof self[a]; }), klon: typeof structuredClone})");
    CHECK(j["self"] == true);
    CHECK(j["window"] == "undefined");
    CHECK(j["document"] == "undefined");
    for (const json& m : j["moduller"]) CHECK(m == "object");
    CHECK(j["klon"] == "function");
    CHECK(t.Js("Op4Ops.TASLAK.length + Op4Cekirdek.TASLAK.length") == 0);
}

TEST_CASE("cekirdek_js B2: structuredClone (C++) — derin kopya, paylaşılan başvuru, döngü, tipli dizi, Date; desteklenmeyen tür hata") {
    Ortam t;
    std::string hata;
    REQUIRE_MESSAGE(t.o.Kur(hata), hata);
    const json j = t.Js(R"((function () {
      var ortak = {a: 1};
      var o = {x: [1, 2, {y: "ş"}], u: undefined, n: null, f: 1.5, b: true, o1: ortak, o2: ortak, t: new Float64Array([1.25, 2]),
               d: new Date(Date.UTC(2026, 9, 30)), bos: {}, "0": "sıfır"};
      o.kendi = o;
      var k = structuredClone(o);
      var hata = function (v) { try { structuredClone(v); return "yok"; } catch (e) { return e.name; } };
      return {ayri: k !== o && k.x !== o.x && k.x[2] !== o.x[2], y: k.x[2].y, uVar: "u" in k && k.u === undefined, n: k.n, f: k.f, b: k.b,
              paylasim: k.o1 === k.o2 && k.o1 !== ortak, dongu: k.kendi === k, tipli: k.t instanceof Float64Array && k.t !== o.t && k.t[0] === 1.25,
              tarih: k.d instanceof Date && k.d.getTime() === o.d.getTime() && k.d !== o.d, anahtarlar: Object.keys(k).join(","),
              islev: hata(function () {}), harita: hata(new Map()), kume: hata(new Set([1])), sembol: hata(Symbol("s")),
              derin: hata((function () { var d = {}, x = d; for (var i = 0; i < 1500; i++) { x.a = {}; x = x.a; } return d; })()),
              sig: (function () { var d = {}, x = d; for (var i = 0; i < 500; i++) { x.a = {}; x = x.a; } return !!structuredClone(d).a.a; })(),
              ilkel: structuredClone(5) + structuredClone("a")};
    })())");
    CHECK(j["ayri"] == true);
    CHECK(j["y"] == "ş");
    CHECK(j["uVar"] == true);
    CHECK(j["n"].is_null());
    CHECK(j["f"] == 1.5);
    CHECK(j["paylasim"] == true);
    CHECK(j["dongu"] == true);
    CHECK(j["tipli"] == true);
    CHECK(j["tarih"] == true);
    CHECK(j["anahtarlar"] == "0,x,u,n,f,b,o1,o2,t,d,bos,kendi");
    CHECK(j["islev"] == "DataCloneError");
    CHECK(j["harita"] == "DataCloneError");
    CHECK(j["kume"] == "DataCloneError");
    CHECK(j["sembol"] == "DataCloneError");
    CHECK(j["derin"] == "RangeError");  // yerel yığın koruması (1000 düzey)
    CHECK(j["sig"] == true);
    CHECK(j["ilkel"] == "5a");
}

TEST_CASE("cekirdek_js B2: console → günlük, deterministik Date.now, Türkçe yerel ayarlı harf dönüşümü") {
    JsOrtamiAyari a;
    a.deterministikSaat = true;
    Ortam t(a);
    std::string hata;
    REQUIRE_MESSAGE(t.o.Kur(hata), hata);
    t.Js("console.log('merhaba', {a: 1}); console.warn('dikkat'); console.error(new TypeError('bozuk'))");
    REQUIRE(t.gunluk.size() >= 3);
    CHECK(t.gunluk[t.gunluk.size() - 3] == "[js bilgi] merhaba {\"a\":1}");
    CHECK(t.gunluk[t.gunluk.size() - 2] == "[js uyari] dikkat");
    CHECK(t.gunluk[t.gunluk.size() - 1] == "[js hata] TypeError: bozuk");
    const json s = t.Js("[Date.now(), Date.now()]");
    CHECK(s[0] == 1767225600000.0);
    CHECK(s[1] == 1767225600001.0);
    const json tr = t.Js("['IİıiŞ'.toLocaleLowerCase('tr'), 'iıIş'.toLocaleUpperCase('tr-TR'), 'I'.toLocaleLowerCase('en'), 'İ'.toLocaleLowerCase('tr').length]");
    CHECK(tr[0] == "ıiıiş");
    CHECK(tr[1] == "İIIŞ");
    CHECK(tr[2] == "i");
    CHECK(tr[3] == 1);
    Ortam g;  // deterministik değil: gerçek saat
    REQUIRE(g.o.Kur(hata));
    CHECK(g.Js("Date.now()").get<double>() > 1767225600000.0 + 86400000.0 * 30);
}

TEST_CASE("cekirdek_js B2: hata yığınında dosya adı ve satır; süre sınırı sonsuz döngüyü keser; geliştirici kipi") {
    JsOrtamiAyari a;
    a.cagriSiniriSn = 0.3;
    Ortam t(a);
    std::string hata, s;
    REQUIRE_MESSAGE(t.o.Kur(hata), hata);
    CHECK_FALSE(t.o.Degerlendir("ModelOps.cubukSil({tur: 'bina'}, 999)", "sinama.js", s, hata));
    CHECK(hata.find("ModelHatasi") != std::string::npos);
    CHECK(hata.find("docs/model_ops.js:") != std::string::npos);
    CHECK_FALSE(t.o.Degerlendir("for (;;) {}", "dongu.js", s, hata));
    CHECK(t.o.Degerlendir("1 + 1", "sonra.js", s, hata));  // ortam kesintiden sonra kullanılabilir
    CHECK(s == "2");
    CHECK(t.o.CagirMetin("Op4Ops.profilAdiNormal", {"HE340A"}, s, hata));
    CHECK(json::parse(s)["ad"] == "HEA 340");
    CHECK_FALSE(t.o.CagirMetin("Op4Ops.yokBoyle", {}, s, hata));
    CHECK(hata.find("JS işlevi yok") != std::string::npos);
    // geliştirici kipi: aynı dosyalar depo kökünden okunur
    JsOrtamiAyari d;
    d.jsDizini = OP4_DEPO_DIZINI;
    Ortam dk(d);
    REQUIRE_MESSAGE(dk.o.Kur(hata), hata);
    CHECK(dk.o.YuklenenBayt() == t.o.YuklenenBayt());
    JsOrtamiAyari y;
    y.jsDizini = "/olmayan/klasor";
    Ortam yk(y);
    CHECK_FALSE(yk.o.Kur(hata));
    CHECK(hata.find("okunamadı") != std::string::npos);
}

TEST_CASE("cekirdek_js B2: ICU'suz motorda öykünmeler — localeCompare (tr, numeric, sensitivity), TextDecoder (utf-8, windows-1254)") {
    Ortam t;
    std::string hata;
    REQUIRE_MESSAGE(t.o.Kur(hata), hata);
    CHECK(t.Js("typeof Intl") == "undefined");  // QuickJS-ng: öykünmeler kurulu olmalı (node'da onyukleme.test.js ICU'ya karşı sınar)
    const json s = t.Js(R"((function () {
      var B = {numeric: true, sensitivity: "base"};
      var l = ["K10", "k9", "K101", "Çatı", "catı", "ığdır", "İzmir", "Işık", "a", "A", "ç", "d", "2. kat", "10. kat", "01", "1"];
      return {sira: l.slice().sort(function (a, b) { return a.localeCompare(b, "tr", B); }),
              esit: ["K9".localeCompare("k9", "tr", B), "01".localeCompare("1", "tr", B), "â".localeCompare("a", "tr", B)],
              varsayilan: ["a".localeCompare("A", "tr"), "ç".localeCompare("d", "tr"), "ç".localeCompare("d", "en"), "ı".localeCompare("i", "tr")]};
    })())");
    CHECK(s["sira"] == json::array({"01", "1", "2. kat", "10. kat", "a", "A", "catı", "ç", "Çatı", "d", "ığdır", "Işık", "İzmir",
                                    "k9", "K10", "K101"}));
    CHECK(s["esit"] == json::array({0, 0, 0}));
    CHECK(s["varsayilan"] == json::array({-1, -1, -1, -1}));
    const json d = t.Js(R"((function () {
      var u = new Uint8Array([0xef, 0xbb, 0xbf, 0x41, 0xc3, 0xa7]), w = new Uint8Array([0xd0, 0xdd, 0xde, 0xf0, 0xfd, 0xfe, 0x80]);
      var f; try { new TextDecoder("utf-8", {fatal: true}).decode(new Uint8Array([0xff])); f = "yok"; } catch (e) { f = e.name; }
      return [new TextDecoder().decode(u), new TextDecoder("utf-8", {ignoreBOM: true}).decode(u).length, new TextDecoder("windows-1254").decode(w),
              f, new TextDecoder().decode(new Uint8Array([0x61, 0xc3])), MatrisTablo._ic.csvMetniCoz(w)];
    })())");
    CHECK(d[0] == "Aç");
    CHECK(d[1] == 3);
    CHECK(d[2] == "ĞİŞğış€");
    CHECK(d[3] == "TypeError");
    CHECK(d[4] == "a\xEF\xBF\xBD");
    CHECK(d[5] == "ĞİŞğış€");  // docs/tablo_editoru.js: UTF-8 değilse windows-1254
}
