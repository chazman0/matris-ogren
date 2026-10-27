/* docs/ifc_disari.js (MatrisIFC, IFC4 STEP dışa aktarım) birim testleri — node'un yerleşik test koşucusu (bağımlılık yok).
   Çalıştırma: node --test testler/js/ifc_disari.test.js   (testler/test_ifc_disari.py de çalıştırır)
   Örnek modeller: testler/js/ifc_ornekler.js */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const MatrisIFC = require(path.join(__dirname, "..", "..", "docs", "ifc_disari.js"));
const O = require(path.join(__dirname, "ifc_ornekler.js"));

const ZAMAN = { zaman: "2026-01-01T00:00:00" };

// ---------------------------------------------------------------------------
// STEP fiziksel dosya denetimi (ifcopenshell olmadan): satır biçimi, parantez dengesi, ASCII, başvurular, GlobalId tekliği.
// Dönüş: {tip: adet} ve satırlar (#n → {tip, govde}).
// ---------------------------------------------------------------------------
function stepDenetle(metin) {
  const satirlar = metin.split("\n").filter(function (s) { return s.length; });
  assert.equal(satirlar[0], "ISO-10303-21;");
  assert.equal(satirlar[1], "HEADER;");
  assert.ok(satirlar.indexOf("FILE_SCHEMA(('IFC4'));") > 0, "FILE_SCHEMA IFC4");
  const veri = satirlar.indexOf("DATA;");
  assert.ok(veri > 0 && satirlar[veri - 1] === "ENDSEC;", "HEADER ENDSEC; ile kapanır, DATA; başlar");
  assert.equal(satirlar[satirlar.length - 1], "END-ISO-10303-21;");
  assert.equal(satirlar[satirlar.length - 2], "ENDSEC;");
  const tanimli = {}, refler = [], tipler = {}, gidler = {}, varlik = {};
  satirlar.slice(veri + 1, satirlar.length - 2).forEach(function (s) {
    const m = /^#(\d+)=([A-Z0-9]+)\((.*)\);$/.exec(s);
    assert.ok(m, "varlık satırı biçimi: " + s.slice(0, 120));
    assert.ok(!tanimli[m[1]], "tekrarlı varlık #" + m[1]);
    tanimli[m[1]] = true;
    varlik[m[1]] = { tip: m[2], govde: m[3] };
    tipler[m[2]] = (tipler[m[2]] || 0) + 1;
    assert.ok(/^[\x20-\x7E]*$/.test(s), "STEP satırı yalnız yazdırılabilir ASCII: " + s.slice(0, 120));
    const metinsiz = m[3].replace(/'(?:[^']|'')*'/g, "''");
    let derinlik = 0;
    for (const c of metinsiz) { if (c === "(") derinlik++; if (c === ")") derinlik--; assert.ok(derinlik >= 0, "parantez dengesi"); }
    assert.equal(derinlik, 0, "parantez dengesi: " + s.slice(0, 120));
    (metinsiz.match(/#\d+/g) || []).forEach(function (r) { refler.push(r.slice(1)); });
    const g = /^'([0-9A-Za-z_$]{22})',#\d+,/.exec(m[3]);
    if (g) { assert.ok(!gidler[g[1]], "tekrarlı GlobalId " + g[1]); assert.ok("0123".indexOf(g[1][0]) >= 0); gidler[g[1]] = true; }
  });
  refler.forEach(function (r) { assert.ok(tanimli[r], "tanımsız başvuru #" + r); });
  return { tipler: tipler, varlik: varlik };
}
function uret(model, secenek) {
  const r = MatrisIFC.uretAyrintili(model, null, Object.assign({}, ZAMAN, secenek || {}));
  return Object.assign(r, stepDenetle(r.metin));
}
function say(t, ad) { return t[ad] || 0; }
// IfcCartesianPoint #n → [x, y, z]
function nokta(v, ref) { const m = /^\(([^)]*)\)$/.exec(v[ref.slice(1)].govde); return m[1].split(",").map(Number); }

// ---------------------------------------------------------------------------
test("GlobalId: 22 karakter, IFC base64 alfabesi, deterministik, farklı anahtar → farklı kimlik", function () {
  const a = MatrisIFC.globalId("x|kolon:1"), b = MatrisIFC.globalId("x|kolon:1"), c = MatrisIFC.globalId("x|kolon:2");
  assert.equal(a.length, 22);
  assert.match(a, /^[0-3][0-9A-Za-z_$]{21}$/);
  assert.equal(a, b);
  assert.notEqual(a, c);
});

test("STEP metin kaçışı: Türkçe harfler \\X2\\, kesme işareti ve ters bölü ikilenir", function () {
  assert.equal(MatrisIFC.stepMetin("Çatı"), "\\X2\\00C7\\X0\\at\\X2\\0131\\X0\\");
  assert.equal(MatrisIFC.stepMetin("a'b\\c"), "a''b\\\\c");
  assert.equal(MatrisIFC.stepMetin("±0.00"), "\\X2\\00B1\\X0\\0.00");
});

test("dosyaAdi: ASCII, .ifc uzantılı", function () {
  assert.equal(MatrisIFC.dosyaAdi({ baslik: "2 katlı betonarme konut (3×2 aks)" }), "2_katli_betonarme_konut_3x2_aks.ifc");
  assert.equal(MatrisIFC.dosyaAdi({ baslik: "Çelik Ağıl / Şube" }), "celik_agil_sube.ifc");
  assert.equal(MatrisIFC.dosyaAdi({}), "bina.ifc");
});

test("aks–kat modeli: katlar, eleman sayıları, profil, analiz modeli, elastik mesnet", function () {
  const r = uret(O.temel());
  const t = r.tipler;
  assert.deepEqual(r.uyarilar, []);
  assert.equal(t.IFCPROJECT, 1);
  assert.equal(t.IFCSITE, 1);
  assert.equal(t.IFCBUILDING, 1);
  assert.equal(t.IFCBUILDINGSTOREY, 3);
  assert.equal(t.IFCCOLUMN, 8);
  assert.equal(t.IFCBEAM, 8);
  assert.equal(t.IFCSLAB, 2);
  assert.equal(t.IFCFOOTING, 4);
  assert.equal(t.IFCSTRUCTURALCURVEMEMBER, 16);
  assert.equal(t.IFCSTRUCTURALPOINTCONNECTION, 12);
  assert.equal(t.IFCSTRUCTURALANALYSISMODEL, 1);
  assert.ok(t.IFCRECTANGLEPROFILEDEF >= 2);
  assert.ok(t.IFCEXTRUDEDAREASOLID >= 22);
  assert.match(r.metin, /IFCBOUNDARYNODECONDITION\('Elastik zemin[^\n]*IFCLINEARSTIFFNESSMEASURE\(/, "elastik mesnet yayı");
  assert.match(r.metin, /IFCSLAB\([^\n]*\.ROOF\.\);/, "en üst kat döşemesi çatı");
  assert.match(r.metin, /IFCFOOTING\([^\n]*\.PAD_FOOTING\.\);/);
  assert.match(r.metin, /IFCPROPERTYSET\('[^']{22}',#\d+,'Pset_ColumnCommon'/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('StrengthClass',\$,IFCLABEL\('C30\/37'\),\$\)/);
  assert.match(r.metin, /IFCMATERIAL\('C30\/37',[^\n]*'concrete'\);/);
});

test("birimler: metre, radyan, kN; tek proje bağlamı", function () {
  const m = MatrisIFC.uret(O.temel(), null, ZAMAN);
  assert.match(m, /IFCSIUNIT\(\*,\.LENGTHUNIT\.,\$,\.METRE\.\)/);
  assert.match(m, /IFCSIUNIT\(\*,\.PLANEANGLEUNIT\.,\$,\.RADIAN\.\)/);
  assert.match(m, /IFCSIUNIT\(\*,\.FORCEUNIT\.,\.KILO\.,\.NEWTON\.\)/);
  assert.match(m, /IFCDERIVEDUNIT\([^\n]*\.LINEARFORCEUNIT\.,\$\)/);
});

test("geometri: kolon yon x → güçlü boyut X'te; kiriş üstü kat kotunda (kardinal 8)", function () {
  const r = uret(O.temel());
  const v = r.varlik;
  // S-A1/k1 kolonu (yon x): yerleşim ekseni Z yukarı, RefDirection (profil X) = −Y → profil Y (h = 0,60) global X'te
  const kolon = Object.keys(v).map(function (k) { return v[k]; }).filter(function (e) { return e.tip === "IFCCOLUMN" && e.govde.indexOf("'S-A1/k1'") > 0; })[0];
  assert.ok(kolon);
  const yer = /,(#\d+),(#\d+),'S1'/.exec(kolon.govde);
  const eks = /,(#\d+)$/.exec(v[yer[1].slice(1)].govde)[1];
  const p = /^(#\d+),(#\d+),(#\d+)$/.exec(v[eks.slice(1)].govde);
  assert.equal(v[p[2].slice(1)].govde, "(0.,0.,1.)");
  assert.equal(v[p[3].slice(1)].govde, "(0.,-1.,0.)");
  // kiriş 21 (K-A1→B1/k2): uzatma başlangıcı üst orta → yerel başlangıç z = −h/2 değil, üst = kat kotu: nokta (0, 0, −0.25) kata göre
  assert.match(r.metin, /IFCRECTANGLEPROFILEDEF\(\.AREA\.,'K25x50',\$,0\.25,0\.5\)/);
  assert.match(r.metin, /IFCCARTESIANPOINT\(\(0\.,0\.,-0\.25\)\)/);
});

test("aynı model + aynı zaman → aynı dosya; başlık değişince kimlikler değişir", function () {
  const a = MatrisIFC.uret(O.temel(), null, ZAMAN);
  const b = MatrisIFC.uret(O.temel(), null, ZAMAN);
  assert.equal(a, b);
  const b2 = O.temel(); b2.baslik = "Başka proje";
  const c = MatrisIFC.uret(b2, null, ZAMAN);
  const gid = function (m) { return /IFCPROJECT\('([^']+)'/.exec(m)[1]; };
  assert.notEqual(gid(a), gid(c));
  // secenek.tohum ile kimlik kökü sabitlenebilir
  const d = MatrisIFC.uret(b2, null, Object.assign({ tohum: O.temel().baslik }, ZAMAN));
  assert.equal(gid(a), gid(d));
});

test("analiz: false → yapısal model yazılmaz", function () {
  const t = uret(O.temel(), { analiz: false }).tipler;
  assert.ok(!t.IFCSTRUCTURALANALYSISMODEL && !t.IFCSTRUCTURALCURVEMEMBER);
  assert.equal(t.IFCCOLUMN, 8);
});

test("aks ızgarası: IfcGrid her Z seviyesinde (UAxes = X, VAxes = Y), 'tek' ve false seçenekleri", function () {
  const r = uret(O.temel());
  assert.equal(r.tipler.IFCGRID, 3);
  assert.equal(r.tipler.IFCGRIDAXIS, 3 * 4);
  assert.match(r.metin, /IFCGRIDAXIS\('A',#\d+,\.T\.\)/);
  assert.match(r.metin, /IFCGRIDAXIS\('2',#\d+,\.T\.\)/);
  assert.match(r.metin, /IFCGRID\([^\n]*,\(#\d+,#\d+\),\(#\d+,#\d+\),\$,\.RECTANGULAR\.\);/);
  assert.match(r.metin, /IFCSHAPEREPRESENTATION\(#\d+,'FootPrint','GeometricCurveSet',/);
  assert.equal(uret(O.temel(), { izgara: "tek" }).tipler.IFCGRID, 1);
  assert.equal(say(uret(O.temel(), { izgara: false }).tipler, "IFCGRID"), 0);
});

test("surum 3: çubuklar, paneller, profil türleri, uç serbestlikleri, mütemadi temel", function () {
  const r = uret(O.serbest());
  const t = r.tipler;
  assert.deepEqual(r.uyarilar, []);
  assert.equal(t.IFCCOLUMN, 9);              // 8 aks–kat + 1 kolon çubuğu
  assert.equal(t.IFCBEAM, 9);                // 8 + 1
  assert.equal(t.IFCMEMBER, 9);
  assert.equal(t.IFCSLAB, 2 + 2);            // 2 döşeme + çatı paneli (t > 0) + döşeme paneli
  assert.equal(t.IFCCOVERING, 2);            // sac çatı + cephe kaplaması
  assert.equal(t.IFCFOOTING, 4);             // 2 X + 2 Y temel kirişi
  assert.match(r.metin, /IFCFOOTING\([^\n]*\.STRIP_FOOTING\.\);/);
  ["IFCISHAPEPROFILEDEF", "IFCRECTANGLEHOLLOWPROFILEDEF", "IFCCIRCLEHOLLOWPROFILEDEF", "IFCLSHAPEPROFILEDEF", "IFCUSHAPEPROFILEDEF",
    "IFCARBITRARYCLOSEDPROFILEDEF"].forEach(function (p) { assert.ok(t[p] >= 1, p); });
  assert.ok(t.IFCLSHAPEPROFILEDEF >= 3, "L + 2L (iki profil)");
  assert.match(r.metin, /IFCISHAPEPROFILEDEF\(\.AREA\.,'HEA 160',\$,0\.16,0\.152,0\.006,0\.009,0\.015,\$,\$\)/, "HEA160 → 'HEA 160' tablo ölçüleri");
  assert.match(r.metin, /IFCSTRUCTURALCURVEMEMBER\([^\n]*\.TENSION_MEMBER\./, "yalnız çekme çaprazı");
  assert.match(r.metin, /IFCBOUNDARYNODECONDITION\('U\\X2\\00E7\\X0\\ serbestli\\X2\\011F\\X0\\i \(My, Mz\)'/, "mafsallı uç");
  assert.match(r.metin, /IFCBOUNDARYNODECONDITION\('Mesnet',IFCBOOLEAN\(\.T\.\),IFCBOOLEAN\(\.T\.\),IFCBOOLEAN\(\.T\.\),IFCBOOLEAN\(\.F\.\)/, "serbest düğüm mesneti");
  assert.match(r.metin, /IFCMEMBER\([^\n]*\.PURLIN\.\);/);
  assert.match(r.metin, /IFCMEMBER\([^\n]*\.BRACE\.\);/);
  assert.match(r.metin, /IFCMEMBER\([^\n]*\.CHORD\.\);/);
  assert.match(r.metin, /IFCCOVERING\([^\n]*\.ROOFING\.\);/);
  assert.match(r.metin, /IFCCOVERING\([^\n]*\.CLADDING\.\);/);
  assert.match(r.metin, /IFCRELASSIGNSTOPRODUCT\(/, "fiziksel eleman ↔ analitik üye");
});

test("§13 temeller: radye (BASESLAB + FOOTING_BEAM), seçili akslarda mütemadi (dikdörtgen kesit)", function () {
  const r = uret(O.radye());
  assert.match(r.metin, /IFCSLAB\([^\n]*\.BASESLAB\.\);/);
  assert.equal(r.tipler.IFCFOOTING, 4);
  assert.match(r.metin, /IFCFOOTING\([^\n]*\.FOOTING_BEAM\.\);/);
  assert.equal(r.tipler.IFCSLAB, 3);
  const s = uret(O.surekli());
  assert.equal(s.tipler.IFCFOOTING, 1);
  assert.match(s.metin, /IFCFOOTING\('[^']+',#\d+,'TK-1',[^\n]*\.STRIP_FOOTING\.\);/);
  // b_govde = B ve h_tabla = 0 → dörtgen kesit (4 köşe + kapanış)
  assert.match(s.metin, /IFCPOLYLINE\(\((#\d+,){4}#\d+\)\)/);
});

test("§19 aks sistemi: Z aksları, {aks, z} REF'leri, bölme/kesişim düğümleri, döndürülmüş ve silindirik sistemler", function () {
  const r = uret(O.aks());
  const t = r.tipler;
  assert.deepEqual(r.uyarilar, []);
  assert.equal(t.IFCBUILDINGSTOREY, 2);
  assert.match(r.metin, /IFCBUILDINGSTOREY\('[^']+',#\d+,'Sa\\X2\\00E7\\X0\\ak seviyesi',[^\n]*,6\.\);/, "kat kotu Z aksından (6,0 m)");
  assert.equal(t.IFCCOLUMN, 6 + 4 + 3);
  assert.equal(t.IFCBEAM, 6 + 4 + 3);
  assert.equal(t.IFCMEMBER, 2 + 4);
  assert.equal(t.IFCCOVERING, 2);
  assert.equal(t.IFCFOOTING, 13);
  assert.equal(t.IFCSTRUCTURALPOINTCONNECTION, 15 + 3 + 1 + 8 + 6);
  assert.equal(t.IFCSTRUCTURALCURVEMEMBER, 32);
  // ızgaralar: GLOBAL ve KANAT-B üç Z aksında (±0.00, Saçak, Mahya), KUBBE kendi iki Z aksında
  assert.equal(t.IFCGRID, 3 + 3 + 2);
  assert.equal(t.IFCGRIDAXIS, 3 * 6 + 3 * 4 + 2 * 4);
  assert.match(r.metin, /IFCGRID\([^\n]*\.RADIAL\.\);/);
  assert.ok(t.IFCCIRCLE >= 2);
  // kat seviyesi olmayan Z aksları binada özellik olarak
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('Mahya',\$,IFCLENGTHMEASURE\(7\.5\),\$\)/);
  // kesişim düğümü (0, 3, 3), bölme düğümü (2.5, 0, 6.75), KANAT-B R2 = orijin + R(30°)·(6, 5), KUBBE T2 = (5 + 3 cos120°, 18 + 3 sin120°)
  const pc = Object.keys(r.varlik).map(function (k) { return r.varlik[k]; }).filter(function (e) { return e.tip === "IFCVERTEXPOINT"; })
    .map(function (e) { return nokta(r.varlik, e.govde); });
  const var_ = function (P) { return pc.some(function (q) { return Math.abs(q[0] - P[0]) < 1e-6 && Math.abs(q[1] - P[1]) < 1e-6 && Math.abs(q[2] - P[2]) < 1e-6; }); };
  const c30 = Math.cos(Math.PI / 6), s30 = 0.5;
  [[0, 3, 3], [2.5, 0, 6.75], [2.5, 12, 6.75], [25 + 6 * c30 - 5 * s30, 6 * s30 + 5 * c30, 6], [5 + 3 * Math.cos(2 * Math.PI / 3), 18 + 3 * Math.sin(2 * Math.PI / 3), 2.5]]
    .forEach(function (P) { assert.ok(var_(P), "düğüm " + P.join(", ")); });
  // aynı noktadaki farklı REF'ler tek düğüm: A1 ±0.00 hem kolon tabanı hem çapraz ucu
  assert.equal(pc.filter(function (q) { return q[0] === 0 && q[1] === 0 && q[2] === 0; }).length, 1);
  assert.match(r.metin, /IFCFOOTING\('[^']+',#\d+,'T-KANAT-B:P1',/);
});

test("§19: aks taşınınca bölme düğümü ve ona bağlı aşık birlikte taşınır", function () {
  const m = O.aks();
  m.akslar.z[2].konum = 8.5;                 // Mahya 7,5 → 8,5
  const r = uret(m, { analiz: true });
  const pc = Object.keys(r.varlik).map(function (k) { return r.varlik[k]; }).filter(function (e) { return e.tip === "IFCVERTEXPOINT"; })
    .map(function (e) { return nokta(r.varlik, e.govde); });
  assert.ok(pc.some(function (q) { return q[0] === 2.5 && q[1] === 6 && Math.abs(q[2] - 7.25) < 1e-9; }));
});

test("§19: tanımsız sistem/aks REF'i uyarı verir, dosya yine geçerli", function () {
  const m = O.aks();
  m.cubuklar.push({ no: 99, i: { sistem: "YOK", aks: ["A", "1"], z: "Saçak" }, j: { aks: ["Q", "1"], z: "Saçak" }, tur: "kiris", kesit: "IPE200" });
  const r = uret(m);
  assert.ok(r.uyarilar.some(function (u) { return /YOK/.test(u); }));
  assert.ok(r.uyarilar.some(function (u) { return /Çubuk 99/.test(u); }));
  assert.equal(r.tipler.IFCBEAM, 13);
});

test("model_ops.genellestir çıktısı (kaynak.aks_kat): aks–kat modeliyle aynı sayılar, D/C kolon no'suyla eşlenir", function () {
  const veri = { tasarim: { elemanlar: [{ tur: "kolon", no: 1, dc: 0.61, durum: "yeterli", belirleyen: { kontrol: "N–M", kombinasyon: "1.4G+1.6Q" } }] } };
  const r = MatrisIFC.uretAyrintili(O.genel(), veri, ZAMAN);
  const t = stepDenetle(r.metin).tipler;
  assert.deepEqual(r.uyarilar, []);
  assert.equal(t.IFCCOLUMN, 8);
  assert.equal(t.IFCBEAM, 8);
  assert.equal(t.IFCSLAB, 2);
  assert.equal(t.IFCFOOTING, 4);
  assert.equal(t.IFCSTRUCTURALCURVEMEMBER, 16);
  assert.equal(t.IFCSTRUCTURALPOINTCONNECTION, 12);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('DC',\$,IFCRATIOMEASURE\(0\.61\),\$\)/);
});

test("veri ile: yük durumları, birleşimler (katsayı ilişkisi), D/C özelliği, yayılı ve tekil yükler", function () {
  const veri = {
    kombinasyonlar: [{ ad: "1.4G+1.6Q", katsayilar: { G: 1.4, Q: 1.6 }, tur: "dayanim", kaynak: "TS 500 Denk. (6.3)", uygulandi: true },
      { ad: "G+Q+E", katsayilar: { G: 1, Q: 1, "EX+": 1 }, tur: "deprem", uygulandi: false }],
    durumlar: { G: {}, Q: {} },
    tasarim: { elemanlar: [{ tur: "kolon", no: 1, dc: 0.83, durum: "yeterli", belirleyen: { kontrol: "N–M", kombinasyon: "1.4G+1.6Q" } }] },
    yukler: { kirisler: [{ no: 11, kN_m: { oz: 3.0, duvar: 5.0, ek_G: 0, ek_Q: 1.0 } }], kolonlar: [{ no: 1, oz_kN: 15.75 }],
      dosemeler: [{ no: 1, paylar: [{ eleman: 10, tepe_g: 5.0, tepe_q: 2.0, parcalar_birim: [[0, 2.5, 0, 1], [2.5, 5, 1, 0]] }] }] },
  };
  const r = MatrisIFC.uretAyrintili(O.temel(), veri, ZAMAN);
  const t = stepDenetle(r.metin).tipler;
  assert.equal(t.IFCSTRUCTURALLOADCASE, 2);
  assert.equal(t.IFCSTRUCTURALLOADGROUP, 1);
  assert.equal(t.IFCRELASSIGNSTOGROUPBYFACTOR, 2);
  assert.match(r.metin, /IFCRELASSIGNSTOGROUPBYFACTOR\([^\n]*,1\.4\);/);
  assert.match(r.metin, /IFCSTRUCTURALLOADGROUP\([^\n]*'1\.4G\+1\.6Q'[^\n]*\.LOAD_COMBINATION\.[^\n]*'ULS'\);/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('DC',\$,IFCRATIOMEASURE\(0\.83\),\$\)/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('BelirleyenBirlesim',\$,IFCLABEL\('1\.4G\+1\.6Q'\),\$\)/);
  assert.match(r.metin, /IFCSTRUCTURALLOADLINEARFORCE\('G \/ E\d+',\$,\$,-8\.,\$,\$,\$\)/, "kiriş G yayılı yükü 3 + 5 kN/m");
  assert.match(r.metin, /IFCSTRUCTURALLOADSINGLEFORCE\('G \/ N1001',0\.,0\.,-15\.75,0\.,0\.,0\.\)/, "kolon öz ağırlığı üst düğümde");
  assert.match(r.metin, /IFCSTRUCTURALCURVEACTION\([^\n]*\.POLYGONAL\.\);/, "döşeme payı üçgen (parçalı doğrusal)");
  assert.match(r.metin, /IFCSTRUCTURALLOADCONFIGURATION\(/);
});

test("yük grupları çözümsüz: bina yük durumlarından (G, Q + açık S/W/E)", function () {
  const b = O.temel();
  b.yuk_durumlari = { G: { acik: true }, Q: { acik: true }, S: { acik: true }, W: { acik: false }, E: { acik: true } };
  const t = uret(b).tipler;
  assert.equal(t.IFCSTRUCTURALLOADCASE, 4);
});

test("uygulama alanları yalnız 'Matris Öğren': FILE_NAME ve IfcApplication; sahiplik geçmişi her köke bağlı", function () {
  const m = MatrisIFC.uret(O.temel(), null, ZAMAN);
  const ad = MatrisIFC.stepMetin("Matris Öğren");
  assert.equal(ad, "Matris \\X2\\00D6011F\\X0\\ren");
  const satir = m.split("\n").filter(function (s) { return s.indexOf("FILE_NAME(") === 0; })[0];
  assert.ok(satir.indexOf(",'" + ad + "','')") > 0, satir);
  const uyg = m.split("\n").filter(function (s) { return /=IFCAPPLICATION\(/.test(s); });
  assert.equal(uyg.length, 1);
  assert.match(uyg[0], new RegExp("IFCAPPLICATION\\(#\\d+,'[0-9.]+','" + ad.replace(/\\/g, "\\\\") + "','" + ad.replace(/\\/g, "\\\\") + "'\\);"));
  const org = /IFCAPPLICATION\(#(\d+),/.exec(uyg[0])[1];
  assert.ok(m.indexOf("#" + org + "=IFCORGANIZATION($,'" + ad + "',$,$,$);") >= 0);
  assert.match(m, /IFCOWNERHISTORY\(#\d+,#\d+,\$,\.ADDED\.,1767225600,#\d+,#\d+,1767225600\);/);
  const sahipsiz = m.split("\n").filter(function (s) { return /^#\d+=IFC[A-Z]+\('[0-9A-Za-z_$]{22}',\$,/.test(s); });
  assert.deepEqual(sahipsiz, []);
});

test("girdi: JSON metni de kabul edilir; bina yoksa veri.bina kullanılır; bozuk girdi hata verir", function () {
  const a = MatrisIFC.uret(JSON.stringify(O.temel()), null, ZAMAN);
  const b = MatrisIFC.uret(null, { bina: O.temel() }, ZAMAN);
  assert.equal(a, b);
  assert.throws(function () { MatrisIFC.uret(null, null); }, /bina modeli/);
});

test("indir: tarayıcı dışında hata; tarayıcıda (sahte belge) Blob bağlantısı .ifc adıyla tıklanır", function () {
  assert.throws(function () { MatrisIFC.indir(O.temel()); }, /tarayıcı/);
  const tiklanan = [];
  globalThis.document = {
    body: { appendChild: function () {} },
    createElement: function () {
      return { style: {}, click: function () { tiklanan.push([this.download, this.href]); }, remove: function () {} };
    },
  };
  try {
    const r = MatrisIFC.indir(O.temel(), null, ZAMAN);
    assert.equal(r.dosya_adi, MatrisIFC.dosyaAdi(O.temel()));
    assert.equal(r.bayt, MatrisIFC.uret(O.temel(), null, ZAMAN).length);
    assert.deepEqual(r.uyarilar, []);
    assert.equal(tiklanan.length, 1);
    assert.equal(tiklanan[0][0], r.dosya_adi);
    assert.match(tiklanan[0][1], /^blob:/);
  } finally {
    delete globalThis.document;
  }
});
