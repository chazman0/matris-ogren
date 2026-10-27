/* docs/ifc_disari.js (MatrisIFC) için Node testi — bağımlılık yok.
   Çalıştırma: node testler/js/ifc_disari.test.js   (testler/test_ifc_disari.py de çalıştırır)
   Başka betiklerden require edilirse yalnız ORNEKLER (örnek bina modelleri) dışa verilir; testler çalışmaz. */
"use strict";
const assert = require("assert");
const path = require("path");
const MatrisIFC = require(path.join(__dirname, "..", "..", "docs", "ifc_disari.js"));

// ---------------------------------------------------------------------------
// Örnek modeller
// ---------------------------------------------------------------------------
function temelBina() {
  return {
    tur: "bina", surum: 1, baslik: "Deneme çerçevesi (2×2 aks, 2 kat) — İĞŞÇÖÜ", sistem: "betonarme", birim: { kuvvet: "kN", uzunluk: "m" },
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 6 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 5 }] },
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3.5 }, { no: 2, ad: "Çatı", kot: 6.5 }],
    malzemeler: { C30: { kutuphane: "C30/37" }, B420C: { kutuphane: "B420C" } },
    kesitler: {
      S30x60: { tip: "dikdortgen", b: 0.30, h: 0.60, malzeme: "C30", donati: "B420C", pas: 0.03 },
      K25x50: { tip: "dikdortgen", b: 0.25, h: 0.50, malzeme: "C30", donati: "B420C", pas: 0.03 },
    },
    kolonlar: [
      { no: 1, aks: ["A", "1"], kat: 1, kesit: "S30x60", yon: "x" }, { no: 2, aks: ["B", "1"], kat: 1, kesit: "S30x60", yon: "y" },
      { no: 3, aks: ["A", "2"], kat: 1, kesit: "S30x60", yon: "x" }, { no: 4, aks: ["B", "2"], kat: 1, kesit: "S30x60", yon: "y" },
      { no: 5, aks: ["A", "1"], kat: 2, kesit: "S30x60", yon: "x" }, { no: 6, aks: ["B", "1"], kat: 2, kesit: "S30x60", yon: "y" },
      { no: 7, aks: ["A", "2"], kat: 2, kesit: "S30x60", yon: "x" }, { no: 8, aks: ["B", "2"], kat: 2, kesit: "S30x60", yon: "y" },
    ],
    kirisler: [1, 2].reduce(function (l, k) {
      return l.concat([
        { no: 10 * k + 1, kat: k, bas: ["A", "1"], son: ["B", "1"], kesit: "K25x50" }, { no: 10 * k + 2, kat: k, bas: ["A", "2"], son: ["B", "2"], kesit: "K25x50" },
        { no: 10 * k + 3, kat: k, bas: ["A", "1"], son: ["A", "2"], kesit: "K25x50" }, { no: 10 * k + 4, kat: k, bas: ["B", "2"], son: ["B", "1"], kesit: "K25x50" },
      ]);
    }, []),
    dosemeler: [{ no: 1, kat: 1, kose: [["A", "1"], ["B", "2"]], h: 0.15, kullanim: "konut" }, { no: 2, kat: 2, kose: [["A", "1"], ["B", "2"]], h: 0.12 }],
    temeller: { tip: "tekil", varsayilan: { B: 1.6, L: 1.8, h: 0.6 }, zemin: { q_em: 200, k0: 20000 }, mesnet: "elastik", ozel: [{ aks: ["B", "2"], B: 2.0, L: 2.2 }] },
  };
}

// surum 3: serbest düğümler, çubuklar (çapraz, makas, aşık, profil türleri, uç serbestliği), paneller, mesnetler; mütemadi temel
function serbestBina() {
  const b = temelBina();
  b.surum = 3;
  b.baslik = "Serbest 3B model (çelik çatı + çaprazlar)";
  b.malzemeler.S275 = { kutuphane: "S275" };
  Object.assign(b.kesitler, {
    IPE200: { tip: "profil", profil: "IPE 200", malzeme: "S275" },
    HEA160: { tip: "profil", profil: "HEA160", malzeme: "S275" },
    KUTU: { tip: "kutu", h: 0.10, b: 0.10, t: 0.005, malzeme: "S275" },
    BORU: { tip: "boru", D: 0.1143, t: 0.004, malzeme: "S275" },
    L70: { tip: "L", h: 0.07, b: 0.07, t: 0.007, malzeme: "S275" },
    UPN: { tip: "U", h: 0.16, b: 0.065, tw: 0.0075, tf: 0.0105, malzeme: "S275" },
    "2L60": { tip: "2L", h: 60, b: 60, t: 6, ara: 10, malzeme: "S275" },
  });
  b.dugumler = [{ no: 100001, X: 3.0, Y: 0.0, Z: 8.0, ad: "Mahya 1" }, { no: 100002, X: 3.0, Y: 5.0, Z: 8.0, ad: "Mahya 2" }];
  b.cubuklar = [
    { no: 1, i: { aks: ["A", "1"], kat: 2 }, j: { dugum: 100001 }, tur: "makas-ust", kesit: "HEA160", serbest: { i: ["My", "Mz"], j: ["My", "Mz"] } },
    { no: 2, i: { dugum: 100001 }, j: { aks: ["B", "1"], kat: 2 }, tur: "makas-ust", kesit: "HEA160" },
    { no: 3, i: { aks: ["A", "2"], kat: 2 }, j: { dugum: 100002 }, tur: "makas-ust", kesit: "HEA160" },
    { no: 4, i: { dugum: 100002 }, j: { aks: ["B", "2"], kat: 2 }, tur: "makas-ust", kesit: "HEA160" },
    { no: 5, i: { dugum: 100001 }, j: { dugum: 100002 }, tur: "asik", kesit: "UPN", aci: 90 },
    { no: 6, i: { aks: ["A", "1"], kat: 0 }, j: { aks: ["B", "1"], kat: 1 }, tur: "capraz", kesit: "BORU", yalniz_cekme: true },
    { no: 7, i: { aks: ["B", "1"], kat: 0 }, j: { aks: ["A", "1"], kat: 1 }, tur: "capraz", kesit: "KUTU" },
    { no: 8, i: { X: 3.0, Y: 0.0, Z: 6.5 }, j: { dugum: 100001 }, tur: "makas-dikme", kesit: "L70" },
    { no: 9, i: { X: 0.0, Y: 2.5, Z: 6.5 }, j: { X: 6.0, Y: 2.5, Z: 6.5 }, tur: "kiris", kesit: "IPE200" },
    { no: 10, i: { X: 0.0, Y: 2.5, Z: 6.5 }, j: { dugum: 100001 }, tur: "makas-diyagonal", kesit: "2L60" },
    { no: 11, i: { X: 9.0, Y: 0.0, Z: 0.0 }, j: { X: 9.0, Y: 0.0, Z: 3.5 }, tur: "kolon", kesit: "HEA160", aci: 90 },
  ];
  b.paneller = [
    { no: 1, kose: [{ aks: ["A", "1"], kat: 2 }, { dugum: 100001 }, { dugum: 100002 }, { aks: ["A", "2"], kat: 2 }], tur: "cati", kalinlik: 0, dagitim: "iki" },
    { no: 2, kose: [{ dugum: 100001 }, { aks: ["B", "1"], kat: 2 }, { aks: ["B", "2"], kat: 2 }, { dugum: 100002 }], tur: "cati", kalinlik: 0.1 },
    { no: 3, kose: [{ aks: ["A", "1"], kat: 0 }, { aks: ["B", "1"], kat: 0 }, { aks: ["B", "1"], kat: 1 }, { aks: ["A", "1"], kat: 1 }], tur: "cephe", kalinlik: 0 },
    { no: 4, kose: [{ aks: ["A", "2"], kat: 1 }, { aks: ["B", "2"], kat: 1 }, { X: 3.0, Y: 7.0, Z: 3.5 }], tur: "doseme", kalinlik: 0.15 },
  ];
  b.mesnetler = [{ dugum: { X: 9.0, Y: 0.0, Z: 0.0 }, ux: true, uy: true, uz: true, rx: false, ry: false, rz: false }];
  b.temeller = { tip: "surekli", mesnet: "ankastre", zemin: { q_em: 200, k0: 20000 },
    surekli: { yon: "xy", akslar: "tum", B: 1.2, h_tabla: 0.4, b_govde: 0.5, h_govde: 1.0, tasma: 0.5 } };
  return b;
}

function radyeBina() {
  const b = temelBina();
  b.baslik = "Kirişli radye örneği";
  b.temeller = { tip: "radye", zemin: { q_em: 150, k0: 15000 }, radye: { h: 0.8, tasma: 1.0, kiris: { b: 0.5, h: 1.2 } } };
  return b;
}

const ORNEKLER = { temel: temelBina, serbest: serbestBina, radye: radyeBina };
module.exports = { ORNEKLER: ORNEKLER };

// ---------------------------------------------------------------------------
// STEP sözdizimi denetimi (ifcopenshell olmadan)
// ---------------------------------------------------------------------------
function stepDenetle(metin) {
  const satirlar = metin.split("\n").filter(function (s) { return s.length; });
  assert.strictEqual(satirlar[0], "ISO-10303-21;");
  assert.strictEqual(satirlar[1], "HEADER;");
  assert.ok(satirlar.indexOf("FILE_SCHEMA(('IFC4'));") > 0, "FILE_SCHEMA IFC4");
  const veri = satirlar.indexOf("DATA;");
  assert.ok(veri > 0 && satirlar[veri - 1] === "ENDSEC;", "HEADER ENDSEC; ile kapanır, DATA; başlar");
  assert.strictEqual(satirlar[satirlar.length - 1], "END-ISO-10303-21;");
  assert.strictEqual(satirlar[satirlar.length - 2], "ENDSEC;");
  const tanimli = {}, refler = [], tipler = {}, gidler = {};
  satirlar.slice(veri + 1, satirlar.length - 2).forEach(function (s) {
    const m = /^#(\d+)=([A-Z0-9]+)\((.*)\);$/.exec(s);
    assert.ok(m, "varlık satırı biçimi: " + s.slice(0, 120));
    assert.ok(!tanimli[m[1]], "tekrarlı varlık #" + m[1]);
    tanimli[m[1]] = true;
    tipler[m[2]] = (tipler[m[2]] || 0) + 1;
    assert.ok(/^[\x20-\x7E]*$/.test(s), "STEP satırı yalnız yazdırılabilir ASCII: " + s.slice(0, 120));
    const metinsiz = m[3].replace(/'(?:[^']|'')*'/g, "''");
    let derinlik = 0;
    for (const c of metinsiz) { if (c === "(") derinlik++; if (c === ")") derinlik--; assert.ok(derinlik >= 0, "parantez dengesi"); }
    assert.strictEqual(derinlik, 0, "parantez dengesi: " + s.slice(0, 120));
    (metinsiz.match(/#\d+/g) || []).forEach(function (r) { refler.push(r.slice(1)); });
    const g = /^'([0-9A-Za-z_$]{22})',/.exec(m[3]);
    if (g) { assert.ok(!gidler[g[1]], "tekrarlı GlobalId " + g[1]); assert.ok("0123".indexOf(g[1][0]) >= 0); gidler[g[1]] = true; }
  });
  refler.forEach(function (r) { assert.ok(tanimli[r], "tanımsız başvuru #" + r); });
  return tipler;
}

// ---------------------------------------------------------------------------
// Testler
// ---------------------------------------------------------------------------
function testler() {
  const sonuclar = [];
  const test = function (ad, f) { f(); sonuclar.push(ad); };

  test("GlobalId: 22 karakter, IFC base64 alfabesi, deterministik, farklı anahtar → farklı kimlik", function () {
    const a = MatrisIFC.globalId("x|kolon:1"), b = MatrisIFC.globalId("x|kolon:1"), c = MatrisIFC.globalId("x|kolon:2");
    assert.strictEqual(a.length, 22);
    assert.ok(/^[0-3][0-9A-Za-z_$]{21}$/.test(a));
    assert.strictEqual(a, b);
    assert.notStrictEqual(a, c);
  });

  test("STEP metin kaçışı: Türkçe harfler \\X2\\, kesme işareti ikilenir", function () {
    assert.strictEqual(MatrisIFC.stepMetin("Çatı"), "\\X2\\00C7\\X0\\at\\X2\\0131\\X0\\");
    assert.strictEqual(MatrisIFC.stepMetin("a'b\\c"), "a''b\\\\c");
  });

  test("dosyaAdi: ASCII, .ifc uzantılı", function () {
    assert.strictEqual(MatrisIFC.dosyaAdi({ baslik: "2 katlı betonarme konut (3×2 aks)" }), "2_katli_betonarme_konut_3x2_aks.ifc");
    assert.strictEqual(MatrisIFC.dosyaAdi({}), "bina.ifc");
  });

  test("aks–kat modeli: katlar, eleman sayıları, profil, analiz modeli, sözdizimi", function () {
    const r = MatrisIFC.uretAyrintili(temelBina(), null, { zaman: "2026-01-01T00:00:00" });
    const t = stepDenetle(r.metin);
    assert.strictEqual(t.IFCBUILDINGSTOREY, 3);
    assert.strictEqual(t.IFCCOLUMN, 8);
    assert.strictEqual(t.IFCBEAM, 8);
    assert.strictEqual(t.IFCSLAB, 2);
    assert.strictEqual(t.IFCFOOTING, 4);
    assert.strictEqual(t.IFCSTRUCTURALCURVEMEMBER, 16);
    assert.strictEqual(t.IFCSTRUCTURALPOINTCONNECTION, 12);
    assert.strictEqual(t.IFCSTRUCTURALANALYSISMODEL, 1);
    assert.ok(t.IFCRECTANGLEPROFILEDEF >= 2);
    assert.ok(/IFCBOUNDARYNODECONDITION\('Elastik zemin[^;]*IFCLINEARSTIFFNESSMEASURE\(/.test(r.metin), "elastik mesnet yayı");
    assert.deepStrictEqual(r.uyarilar, []);
  });

  test("aynı model → aynı dosya; başlık değişince kimlikler değişir", function () {
    const a = MatrisIFC.uret(temelBina(), null, { zaman: "2026-01-01T00:00:00" });
    const b = MatrisIFC.uret(temelBina(), null, { zaman: "2026-01-01T00:00:00" });
    assert.strictEqual(a, b);
    const b2 = temelBina(); b2.baslik = "Başka proje";
    const c = MatrisIFC.uret(b2, null, { zaman: "2026-01-01T00:00:00" });
    const gid = function (m) { return /IFCPROJECT\('([^']+)'/.exec(m)[1]; };
    assert.notStrictEqual(gid(a), gid(c));
  });

  test("analiz: false → yapısal model yazılmaz", function () {
    const t = stepDenetle(MatrisIFC.uret(temelBina(), null, { analiz: false }));
    assert.ok(!t.IFCSTRUCTURALANALYSISMODEL && !t.IFCSTRUCTURALCURVEMEMBER);
    assert.strictEqual(t.IFCCOLUMN, 8);
  });

  test("surum 3: çubuklar, paneller, profil türleri, uç serbestlikleri, mütemadi temel", function () {
    const r = MatrisIFC.uretAyrintili(serbestBina(), null, { zaman: "2026-01-01T00:00:00" });
    const t = stepDenetle(r.metin);
    assert.deepStrictEqual(r.uyarilar, []);
    assert.strictEqual(t.IFCCOLUMN, 9);              // 8 aks–kat + 1 kolon çubuğu
    assert.strictEqual(t.IFCBEAM, 9);                // 8 + 1
    assert.strictEqual(t.IFCMEMBER, 9);
    assert.strictEqual(t.IFCSLAB, 2 + 2);            // 2 döşeme + çatı paneli (t > 0) + döşeme paneli
    assert.strictEqual(t.IFCCOVERING, 2);            // sac çatı + cephe kaplaması
    assert.strictEqual(t.IFCFOOTING, 4);             // 2 X + 2 Y temel kirişi
    assert.ok(/IFCFOOTING\([^;]*\.STRIP_FOOTING\.\);/.test(r.metin));
    ["IFCISHAPEPROFILEDEF", "IFCRECTANGLEHOLLOWPROFILEDEF", "IFCCIRCLEHOLLOWPROFILEDEF", "IFCLSHAPEPROFILEDEF", "IFCUSHAPEPROFILEDEF",
      "IFCARBITRARYCLOSEDPROFILEDEF"].forEach(function (p) { assert.ok(t[p] >= 1, p); });
    assert.ok(t.IFCLSHAPEPROFILEDEF >= 3, "L + 2L (iki profil)");
    assert.ok(/IFCSTRUCTURALCURVEMEMBER\([^;]*\.TENSION_MEMBER\./.test(r.metin), "yalnız çekme çaprazı");
    assert.ok(/IFCBOUNDARYNODECONDITION\('U\\X2\\00E7\\X0\\ serbestli\\X2\\011F\\X0\\i \(My, Mz\)'/.test(r.metin), "mafsallı uç");
    assert.ok(/IFCBOUNDARYNODECONDITION\('Mesnet',IFCBOOLEAN\(\.T\.\),IFCBOOLEAN\(\.T\.\),IFCBOOLEAN\(\.T\.\),IFCBOOLEAN\(\.F\.\)/.test(r.metin), "serbest düğüm mesneti");
    assert.ok(/IFCMEMBER\([^;]*\.PURLIN\.\);/.test(r.metin) && /IFCMEMBER\([^;]*\.BRACE\.\);/.test(r.metin) && /IFCMEMBER\([^;]*\.CHORD\.\);/.test(r.metin));
  });

  test("radye: IfcSlab BASESLAB + temel kirişleri (FOOTING_BEAM)", function () {
    const r = MatrisIFC.uretAyrintili(radyeBina(), null, {});
    const t = stepDenetle(r.metin);
    assert.ok(/IFCSLAB\([^;]*\.BASESLAB\.\);/.test(r.metin));
    assert.strictEqual(t.IFCFOOTING, 4);
    assert.strictEqual(t.IFCSLAB, 3);
  });

  test("veri ile: yük durumları, birleşimler (katsayı ilişkisi), D/C özelliği", function () {
    const b = temelBina();
    const veri = {
      kombinasyonlar: [{ ad: "1.4G+1.6Q", katsayilar: { G: 1.4, Q: 1.6 }, tur: "dayanim", kaynak: "TS 500 Denk. (6.3)", uygulandi: true },
        { ad: "G+Q+E", katsayilar: { G: 1, Q: 1, "EX+": 1 }, tur: "deprem", uygulandi: false }],
      durumlar: { G: {}, Q: {} },
      tasarim: { elemanlar: [{ tur: "kolon", no: 1, dc: 0.83, durum: "yeterli", belirleyen: { kontrol: "N–M", kombinasyon: "1.4G+1.6Q" } }] },
      yukler: { kirisler: [{ no: 11, kN_m: { oz: 3.0, duvar: 5.0, ek_G: 0, ek_Q: 1.0 } }], kolonlar: [{ no: 1, oz_kN: 15.75 }], dosemeler: [] },
    };
    const r = MatrisIFC.uretAyrintili(b, veri, {});
    const t = stepDenetle(r.metin);
    assert.strictEqual(t.IFCSTRUCTURALLOADCASE, 2);
    assert.strictEqual(t.IFCSTRUCTURALLOADGROUP, 1);
    assert.strictEqual(t.IFCRELASSIGNSTOGROUPBYFACTOR, 2);
    assert.ok(/IFCRELASSIGNSTOGROUPBYFACTOR\([^;]*,1\.4\);/.test(r.metin));
    assert.ok(/IFCPROPERTYSINGLEVALUE\('DC',\$,IFCRATIOMEASURE\(0\.83\),\$\)/.test(r.metin));
    assert.ok(/IFCSTRUCTURALLOADLINEARFORCE\('G \/ E\d+',\$,\$,-8\.,\$,\$,\$\)/.test(r.metin), "kiriş G yayılı yükü 3 + 5 kN/m");
    assert.ok(/IFCSTRUCTURALLOADSINGLEFORCE\('G \/ N1001',0\.,0\.,-15\.75,0\.,0\.,0\.\)/.test(r.metin), "kolon öz ağırlığı üst düğümde");
  });

  test("program adı geçmez (yalnız Matris Öğren)", function () {
    const m = MatrisIFC.uret(temelBina(), null, {});
    const satir = m.split("\n").filter(function (s) { return s.indexOf("FILE_NAME(") === 0; })[0];
    assert.ok(satir.indexOf("'" + MatrisIFC.stepMetin("Matris Öğren") + "'") > 0);
    assert.strictEqual(MatrisIFC.stepMetin("Matris Öğren"), "Matris \\X2\\00D6011F\\X0\\ren");
    assert.ok(!/IFCAPPLICATION|IFCOWNERHISTORY/.test(m));
  });

  return sonuclar;
}

if (require.main === module) {
  const s = testler();
  s.forEach(function (ad) { console.log("✔ " + ad); });
  console.log(s.length + " test geçti");
}
