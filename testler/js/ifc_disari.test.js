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

test("§13 temeller: radye (BASESLAB + plak kenarına uzanan FOOTING_BEAM), seçili akslarda mütemadi, ters T kesit", function () {
  const r = uret(O.radye());
  assert.match(r.metin, /IFCSLAB\([^\n]*\.BASESLAB\.\);/);
  assert.equal(r.tipler.IFCFOOTING, 4);
  assert.match(r.metin, /IFCFOOTING\([^\n]*\.FOOTING_BEAM\.\);/);
  assert.equal(r.tipler.IFCSLAB, 3);
  assert.match(r.metin, /IFCRECTANGLEPROFILEDEF\(\.AREA\.,'RK 0\.5x1\.2',\$,0\.5,1\.2\)/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('Kalinlik',\$,IFCPOSITIVELENGTHMEASURE\(0\.8\),\$\)/);
  const s = uret(O.surekli());
  assert.equal(s.tipler.IFCFOOTING, 1);
  assert.match(s.metin, /IFCFOOTING\('[^']+',#\d+,'TK-1',[^\n]*\.STRIP_FOOTING\.\);/);
  // b_govde = B ve h_tabla = 0 → dikdörtgen kesit
  assert.match(s.metin, /IFCRECTANGLEPROFILEDEF\(\.AREA\.,'TK 0\.8x0\.9',\$,0\.8,0\.9\)/);
  // ters T (serbest örnek: B 1,2, tabla 0,4, gövde 0,5 × 1,0): IfcTShapeProfileDef 180° döndürülmüş (başlık = tabla altta)
  const t = uret(O.serbest());
  assert.match(t.metin, /IFCTSHAPEPROFILEDEF\(\.AREA\.,'TK 1\.2\/0\.4-0\.5\/1',#\d+,1\.,1\.2,0\.5,0\.4,\$,\$,\$,\$,\$\)/);
  assert.match(t.metin, /IFCDIRECTION\(\(-1\.,0\.\)\)/);
  // "tum" seçiminde zemin kat kolonu olmayan aks atlanır; hat uçları = uç kolonlar ± taşma
  const b = O.surekli();
  b.akslar.x.push({ ad: "C", konum: 9 });
  b.temeller.surekli = { yon: "xy", akslar: "tum", B: 1.0, h_tabla: 0.3, b_govde: 0.4, h_govde: 0.8, tasma: 0.5 };
  const u = uret(b);
  assert.equal(u.tipler.IFCFOOTING, 4);       // 1, 2 (X) + A, B (Y); C aksında kolon yok
  assert.deepEqual(u.uyarilar, []);
});

// Sentetik veri.temel (temel.py şeması): A–B arasında 1 aksı boyunca tek mütemadi temel hattı (ağ 3 m), iki kolon
function surekliVeri(yatay) {
  const n = [[50001, -0.4], [1, 0], [50002, 3], [21, 6], [50003, 6.4]];
  const A = [0.48, 1.32, 3.6, 1.32, 0.48];
  return {
    ag: {
      dugumler: n.map(function (d) { return { no: d[0], X: d[1], Y: 0, Z: 0, adres: d[0] > 50000 ? "T(" + d[1] + "; 0)" : (d[0] === 1 ? "A1/k0" : "B1/k0") }; })
        .concat([{ no: 1001, X: 0, Y: 0, Z: 3.5, adres: "A1/k1" }, { no: 1021, X: 6, Y: 0, Z: 3.5, adres: "B1/k1" }]),
      elemanlar: [{ no: 1, dugumler: [1, 1001], tur: "kolon", kaynak_no: 1, kesit: "S30x60" }, { no: 2, dugumler: [21, 1021], tur: "kolon", kaynak_no: 2, kesit: "S30x60" }]
        .concat([0, 1, 2, 3].map(function (i) {
          return { no: 64 + i, dugumler: [n[i][0], n[i + 1][0]], tur: "temel-kirisi", kaynak_no: 1, parca: i + 1, kesit: "TK", adres: "TK-1 p" + (i + 1),
            lam: [[1, 0, 0], [0, 0, 1], [0, -1, 0]] };
        })),
      mesnetler: [],
    },
    temel: {
      tip: "surekli", q_em: 200, p_maks: 80, DC_zemin: 0.4, oturma_maks_mm: 4,
      model: { k0: 20000, yatay: yatay || "tutulu", kh_oran: yatay === "yay" ? 0.3 : null, kesit: { B: 1.2, h_tabla: 0.3, b_govde: 0.4, h_govde: 0.9 } },
      dugumler: n.map(function (d, i) { return { no: d[0], X: d[1], Y: 0, A: A[i] }; }),
      elemanlar: [0, 1, 2, 3].map(function (i) { return { no: 64 + i, tur: "temel-kirisi", yon: "x", dugumler: [n[i][0], n[i + 1][0]], b: 0.4, h: 0.9 }; }),
      hatlar: [{ ad: "1", yon: "x", no: 1, sabit: 0, bas: -0.4, son: 6.4, elemanlar: [64, 65, 66, 67], dugumler: n.map(function (d) { return d[0]; }) }],
      tasarim: [{ tur: "temel-kirisi", hat: "1", dc: 0.42, durum: "yeterli" }],
    },
  };
}
function surekliTekHat() {
  const b = O.temel();
  b.kolonlar = b.kolonlar.filter(function (c) { return c.no === 1 || c.no === 2; });
  b.kirisler = [b.kirisler[0]];
  b.dosemeler = [];
  b.temeller = { tip: "surekli", zemin: { q_em: 200, k0: 20000 }, surekli: { yon: "x", akslar: ["1"], B: 1.2, h_tabla: 0.3, b_govde: 0.4, h_govde: 0.9, tasma: 0.4 } };
  return b;
}

test("veri.temel (mütemadi): temel kirişi analitik üyeleri, Winkler yayları k_z = k0·A ve dönme yayı k0·B³/12·l", function () {
  const r = MatrisIFC.uretAyrintili(surekliTekHat(), surekliVeri(), ZAMAN);
  const t = stepDenetle(r.metin).tipler;
  assert.deepEqual(r.uyarilar, []);
  assert.equal(t.IFCFOOTING, 1);
  assert.equal(t.IFCSTRUCTURALCURVEMEMBER, 2 + 4);
  assert.equal(t.IFCSTRUCTURALPOINTCONNECTION, 7);
  // yaylar: A1 (A = 1,32): k_z = 26400; l_etki = 0,2 + 1,5 = 1,7 → k_θ = 20000·1,2³/12·1,7 = 4896; X, Y ve düşey eksen etrafında dönme tutulu
  assert.match(r.metin, /IFCBOUNDARYNODECONDITION\('Zemin yay[^']*',IFCBOOLEAN\(\.T\.\),IFCBOOLEAN\(\.T\.\),IFCLINEARSTIFFNESSMEASURE\(26400\.\),IFCROTATIONALSTIFFNESSMEASURE\(4896\.\),IFCBOOLEAN\(\.F\.\),IFCBOOLEAN\(\.T\.\)\);/);
  assert.match(r.metin, /IFCLINEARSTIFFNESSMEASURE\(72000\.\)/);           // orta düğüm A = 3,6
  const kos = (r.metin.match(/IFCSTRUCTURALPOINTCONNECTION\([^\n]*,#\d+,\$\);/g) || []);
  assert.equal(kos.length, 5, "beş temel düğümünün hepsi yaylı");
  // ters T profil ve fiziksel ↔ analitik ilişki
  assert.match(r.metin, /IFCTSHAPEPROFILEDEF\(\.AREA\.,'TK 1\.2\/0\.3-0\.4\/0\.9'/);
  assert.match(r.metin, /IFCSTRUCTURALCURVEMEMBER\([^\n]*'TK-1 p2 \[E65\]'/);
  // zemin özellikleri ve hat D/C'si fiziksel temel kirişinde
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('k0',\$,IFCMODULUSOFSUBGRADEREACTIONMEASURE\(20000\.\),\$\)/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('DC',\$,IFCRATIOMEASURE\(0\.42\),\$\)/);
  assert.match(r.metin, /IFCDERIVEDUNIT\([^\n]*\.MODULUSOFSUBGRADEREACTIONUNIT\.,\$\)/);
  const fiz = /#(\d+)=IFCFOOTING\('[^']+',#\d+,'TK-1',/.exec(r.metin)[1];
  assert.match(r.metin, new RegExp("IFCRELASSIGNSTOPRODUCT\\([^\\n]*,\\((#\\d+,){3}#\\d+\\),\\$,#" + fiz + "\\);"), "4 temel kirişi parçası → 1 fiziksel temel kirişi");
});

test("veri.temel (yatay: yay): yatay yaylar k_h = kh_oran·k_z, düşey eksen etrafında dönme serbest", function () {
  const r = MatrisIFC.uretAyrintili(surekliTekHat(), surekliVeri("yay"), ZAMAN);
  stepDenetle(r.metin);
  assert.match(r.metin, /IFCBOUNDARYNODECONDITION\('Zemin yay[^']*',IFCLINEARSTIFFNESSMEASURE\(7920\.\),IFCLINEARSTIFFNESSMEASURE\(7920\.\),IFCLINEARSTIFFNESSMEASURE\(26400\.\),[^\n]*,IFCBOOLEAN\(\.F\.\)\);/);
});

test("veri.temel tekil ise mevcut davranış: kolon tabanlarında mesnet, tekil temel", function () {
  const veri = { temel: { tip: "tekil", dugumler: [], elemanlar: [], tasarim: [] } };
  const a = MatrisIFC.uret(O.temel(), veri, ZAMAN), b = MatrisIFC.uret(O.temel(), null, ZAMAN);
  assert.equal(a, b);
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

// ---------------------------------------------------------------------------
// Genel model (surum 3): motorun kesit dili (basitProfil, C9), vute, kesit uyarıları, G/Q/S yükleri
// ---------------------------------------------------------------------------
test("basitProfil: motorun ad dilbilgisi (BORU/KUTU/L/2L/UPN; x, X, ×; büyük/küçük harf; virgül), mm → m", function () {
  const B = MatrisIFC.basitProfil;
  const boru = B("BORU 168.3x6.3");
  assert.equal(boru.tur, "boru");
  assert.equal(boru.ad, "BORU 168.3x6.3");
  const d = 0.1683 - 2 * 0.0063;
  assert.ok(Math.abs(boru.A - Math.PI / 4 * (0.1683 * 0.1683 - d * d)) < 1e-15);
  assert.ok(Math.abs(boru.Iy - Math.PI / 64 * (Math.pow(0.1683, 4) - Math.pow(d, 4))) < 1e-18);
  assert.equal(boru.Iy, boru.Iz);
  assert.ok(Math.abs(boru.J - 2 * boru.Iy) < 1e-18);
  assert.deepEqual(boru.boyutlar, { D: 0.1683, t: 0.0063 });
  assert.equal(boru.h, 0.1683);
  // yazım çeşitleri aynı sonuç
  ["boru 168,3 × 6,3", "BORU168.3X6.3", "  Boru  168.3x6.3 ", "CHS 168.3*6.3"].forEach(function (a) { assert.deepEqual(B(a), boru, a); });
  const kare = B("KUTU 150x8");
  assert.equal(kare.ad, "KUTU 150x150x8");
  assert.equal(kare.tur, "kutu");
  assert.ok(Math.abs(kare.Iy - kare.Iz) < 1e-18);
  assert.deepEqual(kare.boyutlar, { h: 0.15, b: 0.15, t: 0.008, r_o: 0.012, r_i: 0.008 });   // sıcak: r_o = 1,5t, r_i = t
  assert.deepEqual(B("kutu 150×150×8"), kare);
  const rhs = B("KUTU 200x100x6");
  assert.ok(rhs.Iy > rhs.Iz, "Iy güçlü eksen (H doğrultusunda)");
  assert.equal(rhs.h, 0.2);
  assert.equal(rhs.b, 0.1);
  const L = B("L 100x10");
  assert.equal(L.ad, "L 100x100x10");
  assert.deepEqual(B("L 100x100x10"), L);
  assert.equal(L.boyutlar.r1, 0.012);           // EN 10056-1 kök yarıçapı, uç r1/2
  assert.equal(L.boyutlar.r2, 0.006);
  const Le = B("L 100x50x8");                    // farklı kollu (keskin köşe)
  assert.equal(Le.tur, "L");
  assert.equal(Le.h, 0.1);
  assert.equal(Le.b, 0.05);
  assert.ok(Le.Iy > Le.Iz);
  const L2 = B("2L 70x7 s=10");
  assert.equal(L2.tur, "2L");
  assert.equal(L2.ad, "2L 70x70x7 s=10");
  assert.ok(Math.abs(L2.b - 0.15) < 1e-12, "dış genişlik 2b + s");
  assert.deepEqual(B("2l 70X7"), L2, "s varsayılanı 10 mm");
  assert.deepEqual(B("2L 70x70x7 (s=10)"), L2);
  assert.ok(B("2L 70x7 s=20").Iz > L2.Iz, "aralık büyüyünce Iz büyür");
  const U = B("UPN 200");
  assert.equal(U.tur, "U");
  assert.deepEqual([U.h, U.b, U.boyutlar.tw, U.boyutlar.tf], [0.2, 0.075, 0.0085, 0.0115]);
  assert.deepEqual(B("upn200"), U);
  // tanınmayanlar → null
  [null, undefined, "", {}, 12, "IPE 300", "HEA 200", "UPN 210", "UPN 200.5", "BORU 100", "BORU 100x60", "KUTU 10x6", "L 20x12",
    "2L 100x50x8 s=10", "XYZ 1x2", "BORU 168.3.1x6", "KUTU 100x50x5x3", "L 100x0"].forEach(function (a) {
    assert.equal(B(a), null, String(a));
  });
});

// Küçük surum 3 modeli: tek çubuk (0,0,3) → (2,0,3), kesit verilen sözlük
function tekCubuk(kesitler, kesit, ek) {
  return Object.assign({
    tur: "bina", surum: 3, baslik: "Tek çubuk", sistem: "celik",
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 2 }], y: [{ ad: "1", konum: 0 }], z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "+3", konum: 3, kat: 1 }] },
    katlar: [{ no: 0, ad: "±0.00", kot: 0 }, { no: 1, ad: "+3", kot: 3 }],
    malzemeler: { S275: { kutuphane: "S275" } }, kesitler: kesitler,
    cubuklar: [{ no: 1, i: { X: 0, Y: 0, Z: 3 }, j: { X: 2, Y: 0, Z: 3 }, tur: "kiris", kesit: kesit }],
    mesnetler: [{ dugum: { X: 0, Y: 0, Z: 3 }, ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }],
    temeller: { tip: "tekil", varsayilan: { B: 1, L: 1, h: 0.5 } },
  }, ek || {});
}

test("vute: temel I profil + derin uç profili (h + ek, üst yüz hizalı) ile IfcExtrudedAreaSolidTapered, kalan boy sabit; Pset_MatrisVute", function () {
  const kes = { MERTEK: { tip: "profil", profil: "IPE 300", malzeme: "S275" }, VUTE: { tip: "vute", temel: "MERTEK", ek_yukseklik: 0.3, boy: 1.0 } };
  const r = uret(tekCubuk(kes, "VUTE"));
  const t = r.tipler;
  assert.deepEqual(r.uyarilar, []);
  assert.doesNotMatch(r.metin, /IFCRECTANGLEPROFILEDEF\(\.AREA\.,'VUTE'/);
  assert.equal(t.IFCEXTRUDEDAREASOLIDTAPERED, 1);
  // temel profil ve derin uç (OverallDepth 0,6; −ek/2 = −0,15 kaydırılmış → üst yüz +0,15'te kalır)
  assert.match(r.metin, /IFCISHAPEPROFILEDEF\(\.AREA\.,'IPE 300',\$,0\.15,0\.3,0\.0071,0\.0107,0\.015,\$,\$\)/);
  const derin = /#(\d+)=IFCISHAPEPROFILEDEF\(\.AREA\.,'IPE 300 \(vute derin u\\X2\\00E7\\X0\\, h = 0\.6 m\)',(#\d+),0\.15,0\.6,/.exec(r.metin);
  assert.ok(derin, "derin uç profili");
  const yer = r.varlik[derin[2].slice(1)].govde;
  assert.equal(nokta(r.varlik, /^(#\d+)/.exec(yer)[1]).join(","), "0,-0.15");
  // derin uç i: sivri katı 0 → 1 m (derin → temel), kalan 1 m sabit kesitli katı z = 1'de
  const sivri = /IFCEXTRUDEDAREASOLIDTAPERED\((#\d+),\$,#\d+,1\.,(#\d+)\)/.exec(r.metin);
  assert.ok(sivri);
  assert.equal(sivri[1], "#" + derin[1]);
  assert.match(r.metin, /IFCSHAPEREPRESENTATION\(#\d+,'Body','AdvancedSweptSolid',\(#\d+,#\d+\)\)/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('TemelProfil',\$,IFCLABEL\('IPE 300'\),\$\)/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('EkYukseklik',\$,IFCLENGTHMEASURE\(0\.3\),\$\)/);
  assert.match(r.metin, /IFCPROPERTYSINGLEVALUE\('DerinUcYuksekligi',\$,IFCPOSITIVELENGTHMEASURE\(0\.6\),\$\)/);
  // derin uç j: önce sabit kesit (0 → 1), sonra sivri katı z = 1'de (temel → derin)
  const kj = JSON.parse(JSON.stringify(kes));
  kj.VUTE.derin_uc = "j";
  const rj = uret(tekCubuk(kj, "VUTE"));
  const sj = /IFCEXTRUDEDAREASOLIDTAPERED\((#\d+),(#\d+),#\d+,1\.,(#\d+)\)/.exec(rj.metin);
  assert.ok(sj);
  assert.match(rj.varlik[sj[3].slice(1)].govde, /vute derin/);
  assert.equal(nokta(rj.varlik, /^(#\d+)/.exec(rj.varlik[sj[2].slice(1)].govde)[1]).join(","), "0,0,1");
  // boy verilmezse çubuk boyunca; temel kesit tanımsızsa tek uyarı ve 0,30 × 0,30
  const kb = JSON.parse(JSON.stringify(kes));
  delete kb.VUTE.boy;
  assert.match(uret(tekCubuk(kb, "VUTE")).metin, /IFCEXTRUDEDAREASOLIDTAPERED\(#\d+,\$,#\d+,2\.,#\d+\)/);
  const ky = { VUTE: { tip: "vute", temel: "YOK", ek_yukseklik: 0.3 } };
  const ry = uret(tekCubuk(ky, "VUTE"));
  assert.equal(ry.uyarilar.length, 1);
  assert.match(ry.uyarilar[0], /Vute kesiti 'VUTE': temel kesit 'YOK' tanımsız/);
});

test("kesit dili: basit kesit adları, {tip, boyutlar (mm)}, 2L → IfcCompositeProfileDef; tanınmayan profil uyarısı ad başına bir kez (adetle)", function () {
  const kes = {
    BORU: { tip: "profil", profil: "BORU 114.3x4", malzeme: "S275" }, KARE: { tip: "profil", profil: "KUTU 150x8", malzeme: "S275" },
    RHS: { tip: "kutu", boyutlar: { H: 200, B: 100, t: 6 }, malzeme: "S275" }, KORNIYER: { tip: "profil", profil: "L 100x10", malzeme: "S275" },
    CIFT: { tip: "profil", profil: "2L 70x7 s=10", malzeme: "S275" }, UPN: { tip: "profil", profil: "UPN 200", malzeme: "S275" },
    CIFT2: { tip: "2L", boyutlar: { b: 60, t: 6 }, malzeme: "S275" }, BILINMEYEN: { tip: "profil", profil: "XYZ 99", malzeme: "S275" },
    EKSIK: { tip: "boru", malzeme: "S275" },
  };
  const m = tekCubuk(kes, "BORU");
  const adlar = Object.keys(kes);
  m.cubuklar = adlar.map(function (k, i) { return { no: i + 1, i: { X: 0, Y: i, Z: 3 }, j: { X: 2, Y: i, Z: 3 }, tur: "kiris", kesit: k }; });
  [1, 2, 3].forEach(function (n) { m.cubuklar.push({ no: 20 + n, i: { X: 0, Y: 20 + n, Z: 3 }, j: { X: 2, Y: 20 + n, Z: 3 }, tur: "bag", kesit: "BILINMEYEN" }); });
  const r = uret(m);
  assert.match(r.metin, /IFCCIRCLEHOLLOWPROFILEDEF\(\.AREA\.,'BORU 114\.3x4',\$,0\.05715,0\.004\)/);
  assert.match(r.metin, /IFCRECTANGLEHOLLOWPROFILEDEF\(\.AREA\.,'KUTU 150x8',\$,0\.15,0\.15,0\.008,0\.008,0\.012\)/);
  assert.match(r.metin, /IFCRECTANGLEHOLLOWPROFILEDEF\(\.AREA\.,'KUTU 200x100x6',\$,0\.1,0\.2,0\.006,0\.006,0\.009\)/);
  assert.match(r.metin, /IFCLSHAPEPROFILEDEF\(\.AREA\.,'L 100x10',\$,0\.1,0\.1,0\.01,0\.012,0\.006,\$\)/);
  assert.match(r.metin, /IFCUSHAPEPROFILEDEF\(\.AREA\.,'UPN 200',\$,0\.2,0\.075,0\.0085,0\.0115,0\.0115,0\.00575,0\.0798/);
  // 2L: iki L (ikincisi +90° döndürülmüş, Depth/Width yer değiştirmiş = birincinin aynası) tek bileşik profilde; malzeme profili onu gösterir
  const c = /#(\d+)=IFCCOMPOSITEPROFILEDEF\(\.AREA\.,'2L 70x7 s=10',\((#\d+),(#\d+)\),'2L'\)/.exec(r.metin);
  assert.ok(c);
  assert.match(r.varlik[c[2].slice(1)].govde, /^\.AREA\.,'2L 70x7 s=10 \(1\)',#\d+,0\.07,0\.07,0\.007,0\.009,0\.0045,\$$/);
  const p2 = /^\.AREA\.,'2L 70x7 s=10 \(2\)',(#\d+),/.exec(r.varlik[c[3].slice(1)].govde);
  assert.match(r.varlik[p2[1].slice(1)].govde, /^#\d+,(#\d+)$/);
  assert.equal(r.varlik[/,(#\d+)$/.exec(r.varlik[p2[1].slice(1)].govde)[1].slice(1)].govde, "(0.,1.)");
  assert.match(r.metin, new RegExp("IFCMATERIALPROFILE\\('CIFT',\\$,#\\d+,#" + c[1] + ",\\$,\\$\\)"));
  assert.match(r.metin, /IFCCOMPOSITEPROFILEDEF\(\.AREA\.,'2L 60x60x6 s=10',/);      // boyutlar biçimi: s varsayılanı
  // uyarılar: tanınmayan ad 4 çubukta → tek satır; ölçüsü eksik boru → tek satır
  assert.deepEqual(r.uyarilar, ["Profil 'XYZ 99' tabloda yok; b × h dikdörtgen katı ile gösterildi (4 eleman).",
    "Kesit 'EKSIK' (tip boru): ölçüler eksik ya da tutarsız; b × h dikdörtgen katı ile gösterildi."]);
});

test("kesit uyarıları metin başına tek satır (aynı profilli iki kesit adı, temel kesiti tanınmayan vute); tip 'basit' + boyutlar; kutu köşe yarıçapı IFC sınırında", function () {
  const kes = {
    A: { tip: "profil", profil: "XYZ 300", malzeme: "S275" }, B: { tip: "profil", profil: "XYZ 300", malzeme: "S275" },
    V: { tip: "vute", temel: "A", ek_yukseklik: 0.3 },
    BK: { tip: "basit", boyutlar: { H: 200, B: 100, t: 6 }, malzeme: "S275" }, BB: { tip: "basit", boyutlar: { D: 114.3, t: 4 }, malzeme: "S275" },
    BU: { tip: "basit", boyutlar: { h: 200, b: 75, tw: 8.5, tf: 11.5 }, malzeme: "S275" }, BL: { tip: "basit", boyutlar: { b: 100, t: 10 }, malzeme: "S275" },
    B2: { tip: "basit", boyutlar: { b: 70, t: 7, s: 12 }, malzeme: "S275" }, TUHAF: { tip: "xyz", boyutlar: { b: 70, t: 7 }, malzeme: "S275" },
    KALIN: { tip: "profil", profil: "KUTU 40x40x12", malzeme: "S275" },
  };
  const m = tekCubuk(kes, "A");
  m.cubuklar = ["A", "A", "B", "V", "V", "V", "BK", "BB", "BU", "BL", "B2", "TUHAF", "KALIN"].map(function (k, i) {
    return { no: i + 1, i: { X: 0, Y: i, Z: 3 }, j: { X: 2, Y: i, Z: 3 }, tur: "kiris", kesit: k };
  });
  const r = uret(m);
  assert.deepEqual(r.uyarilar, ["Profil 'XYZ 300' tabloda yok; b × h dikdörtgen katı ile gösterildi (6 eleman).",
    "Kesit 'TUHAF' (tip xyz): ölçüler eksik ya da tutarsız; b × h dikdörtgen katı ile gösterildi."]);
  assert.match(r.metin, /IFCRECTANGLEHOLLOWPROFILEDEF\(\.AREA\.,'KUTU 200x100x6',\$,0\.1,0\.2,0\.006,0\.006,0\.009\)/);
  assert.match(r.metin, /IFCCIRCLEHOLLOWPROFILEDEF\(\.AREA\.,'BORU 114\.3x4',\$,0\.05715,0\.004\)/);
  assert.match(r.metin, /IFCUSHAPEPROFILEDEF\(\.AREA\.,'U 200x75x8\.5x11\.5',\$,0\.2,0\.075,0\.0085,0\.0115,/);
  assert.match(r.metin, /IFCLSHAPEPROFILEDEF\(\.AREA\.,'L 100x100x10',\$,0\.1,0\.1,0\.01,0\.012,0\.006,\$\)/);
  assert.match(r.metin, /IFCCOMPOSITEPROFILEDEF\(\.AREA\.,'2L 70x70x7 s=12',/);
  // KUTU 40x40x12: r_i = t = 12 mm > b/2 − t = 8 mm → 8 mm (IfcRectangleHollowProfileDef ValidInnerRadius); r_o = 18 ≤ 20
  assert.match(r.metin, /IFCRECTANGLEHOLLOWPROFILEDEF\(\.AREA\.,'KUTU 40x40x12',\$,0\.04,0\.04,0\.012,0\.008,0\.018\)/);
});

// Sentetik genel model çözümü (yapi_serbest veri şeması): z = 3 m'de 6 × 4 m tek doğrultulu (tek-13) panel. 1. kenar (0,0)→(6,0)
// iki çubuklu zincir: Ç1 (0→3) ve Ç2 (6→3, kenara ters; FE parçası E2 çubuğa da ters). 3. kenar (6,4)→(0,4): Ç3 (0→6, kenara ters,
// iki FE parçası E3, E4); birim yük kenar boyunca 1 → 3 (Ç3'ün i ucunda 3). g = 2, q = 3 kN/m². Öz ağırlık 0,2 kN/m.
function genelSentetik() {
  const lam = function (x) { return [x, [0, 0, 1], [x[1], -x[0], 0]]; };
  const bina = {
    tur: "bina", surum: 3, baslik: "Sentetik genel model", sistem: "celik",
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 6 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }],
      z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "+3", konum: 3, kat: 1 }] },
    katlar: [{ no: 0, ad: "±0.00", kot: 0 }, { no: 1, ad: "+3", kot: 3 }],
    malzemeler: { S275: { kutuphane: "S275" } }, kesitler: { K: { tip: "profil", profil: "IPE 200", malzeme: "S275" } },
    cubuklar: [
      { no: 1, i: { X: 0, Y: 0, Z: 3 }, j: { X: 3, Y: 0, Z: 3 }, tur: "kiris", kesit: "K" },
      { no: 2, i: { X: 6, Y: 0, Z: 3 }, j: { X: 3, Y: 0, Z: 3 }, tur: "kiris", kesit: "K" },
      { no: 3, i: { X: 0, Y: 4, Z: 3 }, j: { X: 6, Y: 4, Z: 3 }, tur: "kiris", kesit: "K" },
    ],
    paneller: [{ no: 1, kose: [{ X: 0, Y: 0, Z: 3 }, { X: 6, Y: 0, Z: 3 }, { X: 6, Y: 4, Z: 3 }, { X: 0, Y: 4, Z: 3 }], tur: "doseme", kalinlik: 0, dagitim: "tek-13" }],
    ek_yukler: [{ tur: "cubuk", cubuk: 3, durum: "Q", q: -2, x1: 1, x2: 2 }, { tur: "cubuk", cubuk: 2, durum: "G", x: 1, P: -5 },
      { tur: "cubuk", cubuk: 1, durum: "G", yon: "X", q: 1.5 }],
    temeller: { tip: "tekil", varsayilan: { B: 1, L: 1, h: 0.5 } },
  };
  const d = [[1, 0, 0], [2, 3, 0], [3, 6, 0], [4, 0, 4], [5, 3, 4], [6, 6, 4]];
  const veri = {
    ag: {
      dugumler: d.map(function (x) { return { no: x[0], X: x[1], Y: x[2], Z: 3, adres: "N" + x[0] }; }),
      elemanlar: [{ no: 1, dugumler: [1, 2], cubuk: 1, kaynak_no: 1, tur: "kiris", kesit: "K", lam: lam([1, 0, 0]) },
        { no: 2, dugumler: [2, 3], cubuk: 2, kaynak_no: 2, tur: "kiris", kesit: "K", lam: lam([1, 0, 0]) },
        { no: 3, dugumler: [4, 5], cubuk: 3, kaynak_no: 3, parca: 1, tur: "kiris", kesit: "K", lam: lam([1, 0, 0]) },
        { no: 4, dugumler: [5, 6], cubuk: 3, kaynak_no: 3, parca: 2, tur: "kiris", kesit: "K", lam: lam([1, 0, 0]) }],
      cubuklar: [{ no: 1, i: 1, j: 2, fe: [1] }, { no: 2, i: 3, j: 2, fe: [2] }, { no: 3, i: 4, j: 6, fe: [3, 4] }],
      paneller: [{ no: 1, kose: [1, 3, 6, 4], dagitim: "tek-13", kenarlar: [{ kenar: 1, dugumler: [1, 3], cubuklar: [1, 2] },
        { kenar: 2, dugumler: [3, 6], cubuklar: [] }, { kenar: 3, dugumler: [6, 4], cubuklar: [3] }, { kenar: 4, dugumler: [4, 1], cubuklar: [] }]}],
      mesnetler: [{ dugum: 1, ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }],
    },
    yukler: {
      dosemeler: [], kirisler: [], kolonlar: [],
      paneller: [{ no: 1, alan: 24, dagitim: "tek-13", G_toplam: 48, Q_toplam: 72, S_toplam: 0, kenarlar: [
        { kenar: 1, cubuklar: [1, 2], pay: 12, sekil: "duzgun", parcalar_birim: [[0, 6, 2, 2]] }, { kenar: 2, cubuklar: [], pay: 0, sekil: "yok" },
        { kenar: 3, cubuklar: [3], pay: 12, sekil: "dogrusal", parcalar_birim: [[0, 6, 1, 3]] }, { kenar: 4, cubuklar: [], pay: 0, sekil: "yok" }] }],
      cubuklar: [{ no: 1, L: 3, G: { oz: 0.6, panel: 12, toplam_kN: 12.6 }, Q: { panel: 18, toplam_kN: 18 } },
        { no: 2, L: 3, G: { oz: 0.6, panel: 12, ek: 5, toplam_kN: 17.6 }, Q: { panel: 18, toplam_kN: 18 } },
        { no: 3, L: 6, G: { oz: 1.2, panel: 24, toplam_kN: 25.2 }, Q: { panel: 36, ek: 2, toplam_kN: 38 } }],
      toplam: { G: 55.4, Q: 74 },
    },
    durumlar: { G: {}, Q: {} }, kombinasyonlar: [],
  };
  return { bina: bina, veri: veri };
}
// Eylemlerin yük durumu başına düşey toplamı (kN, aşağı +); üye boyları sentetik modelden (E1, E2, E3, E4: 3 m)
function dusey(r) {
  const v = r.varlik, top = {};
  const alan = function (g) { return g.replace(/'(?:[^']|'')*'/g, "''").split(","); };
  Object.keys(v).forEach(function (n) {
    const e = v[n];
    if (e.tip !== "IFCRELASSIGNSTOGROUP") return;
    const m = /,\(([^)]*)\),\$,(#\d+)$/.exec(e.govde);
    if (v[m[2].slice(1)].tip !== "IFCSTRUCTURALLOADCASE") return;          // analiz modeli üyeleri vb.
    const durum = /^'[^']+',#\d+,'([^']+)'/.exec(v[m[2].slice(1)].govde)[1];
    m[1].split(",").forEach(function (a) {
      const x = v[a.slice(1)], yk = v[/(#\d+),\.GLOBAL_COORDS\./.exec(x.govde)[1].slice(1)];
      let s;
      if (x.tip === "IFCSTRUCTURALPOINTACTION") s = -Number(alan(yk.govde)[3]);
      else if (x.tip === "IFCSTRUCTURALLINEARACTION") s = -Number(alan(yk.govde)[3] === "$" ? 0 : alan(yk.govde)[3]) * 3;
      else {
        const k = /^'[^']*',\(([^)]*)\),\((.*)\)$/.exec(yk.govde);
        const f = k[1].split(",").map(function (q) { const z = alan(v[q.slice(1)].govde)[3]; return z === "$" ? 0 : -Number(z); });
        const xs = k[2].replace(/[()]/g, "").split(",").map(Number);
        s = 0;
        for (let i = 0; i + 1 < xs.length; i++) s += (xs[i + 1] - xs[i]) * (f[i] + f[i + 1]) / 2;
      }
      top[durum] = (top[durum] || 0) + s;
    });
  });
  return top;
}
function konfig(r, ad) {     // yayılı yük eylemi → [[x, FZ], ...] (CONST ise [[0, FZ], [3, FZ]])
  const v = r.varlik;
  const e = Object.keys(v).map(function (n) { return v[n]; }).filter(function (x) {
    return /^IFCSTRUCTURAL(CURVE|LINEAR)ACTION$/.test(x.tip) && x.govde.indexOf(",'" + ad + "',") > 0;
  })[0];
  if (!e) return null;
  const yk = v[/(#\d+),\.GLOBAL_COORDS\./.exec(e.govde)[1].slice(1)];
  const z = function (g) { return Number(g.replace(/'(?:[^']|'')*'/g, "''").split(",")[3]); };
  if (yk.tip === "IFCSTRUCTURALLOADLINEARFORCE") return [[0, z(yk.govde)], [3, z(yk.govde)]];
  const k = /^'[^']*',\(([^)]*)\),\((.*)\)$/.exec(yk.govde);
  const xs = k[2].replace(/[()]/g, "").split(",").map(Number);
  return k[1].split(",").map(function (q, i) { return [xs[i], z(v[q.slice(1)].govde)]; });
}

test("genel model yükleri: kenar → çubuk zinciri (ters çubuk, iki FE parçası), öz ağırlık, kısmi ve tekil ek yük, toplamlar", function () {
  const s = genelSentetik();
  const r = MatrisIFC.uretAyrintili(s.bina, s.veri, ZAMAN);
  Object.assign(r, stepDenetle(r.metin));
  assert.deepEqual(r.uyarilar, []);
  const top = dusey(r);
  assert.ok(Math.abs(top.G - 55.4) < 1e-9, "G " + top.G);
  assert.ok(Math.abs(top.Q - 74) < 1e-9, "Q " + top.Q);
  // Ç3 (kenar 3'e ters): çubuk boyunca G = 2·(3 − x/3) + 0,2 → E3: 6,2 → 4,2; E4: 4,2 → 2,2 (kN/m aşağı)
  assert.deepEqual(konfig(r, "G / E3").map(function (p) { return [p[0], +p[1].toFixed(9)]; }), [[0, -6.2], [3, -4.2]]);
  assert.deepEqual(konfig(r, "G / E4").map(function (p) { return [p[0], +p[1].toFixed(9)]; }), [[0, -4.2], [3, -2.2]]);
  // Q / E3: panel 3·(3 − x/3) + [1, 2] aralığında 2 kN/m ek yük → sıçramalar x = 1 ve 2'de (± 0,5 mm)
  const q3 = konfig(r, "Q / E3");
  assert.deepEqual(q3.map(function (p) { return p[0]; }), [0, 0.9995, 1.0005, 1.9995, 2.0005, 3]);
  assert.ok(Math.abs(q3[0][1] + 9) < 1e-9 && Math.abs(q3[2][1] + (9 - 1.0005 + 2)) < 1e-9 && Math.abs(q3[5][1] + 6) < 1e-9);
  // Ç2 (6 → 3) tekil ek yükü i ucundan 1 m → (5, 0, 3); E2 üyesi (3 → 6) çubuğa ters: üyenin i ucundan 2 m
  const pa = /#(\d+)=IFCSTRUCTURALPOINTACTION\('[^']{22}',#\d+,'G \/ E2 @2\.',[^\n]*,#\d+,(#\d+),(#\d+),\.GLOBAL_COORDS\.,\$\);/.exec(r.metin);
  assert.ok(pa, "çubuk üzerinde tekil yük");
  assert.equal(r.varlik[pa[3].slice(1)].govde, "'G / E2 @2.',0.,0.,-5.,0.,0.,0.");
  // konum: IfcProductDefinitionShape → IfcTopologyRepresentation (Reference, Vertex) → IfcVertexPoint → (5, 0, 3)
  const tek = function (ref) { return r.varlik[ref.slice(1)]; };
  const temsil = tek(/\((#\d+)\)$/.exec(tek(pa[2]).govde)[1]);
  assert.equal(temsil.tip, "IFCTOPOLOGYREPRESENTATION");
  assert.match(temsil.govde, /,'Reference','Vertex',\(#\d+\)$/);
  const tepe = tek(/\((#\d+)\)$/.exec(temsil.govde)[1]);
  assert.equal(tepe.tip, "IFCVERTEXPOINT");
  assert.equal(nokta(r.varlik, tepe.govde).join(","), "5,0,3");
  // yatay (X) ek yük ayrı doğrultu grubunda
  assert.match(r.metin, /IFCSTRUCTURALLOADLINEARFORCE\('G \/ E1 \(\+X\)',1\.5,\$,\$,\$,\$,\$\)/);
  // eski çözüm (veri.ag.paneller yok): panel payı çubuk toplamından düzgün eşdeğer, toplam aynı, bilgi uyarısı
  const e = genelSentetik();
  delete e.veri.ag.paneller;
  const re_ = MatrisIFC.uretAyrintili(e.bina, e.veri, ZAMAN);
  Object.assign(re_, stepDenetle(re_.metin));
  assert.ok(Math.abs(dusey(re_).G - 55.4) < 1e-9);
  assert.equal(re_.uyarilar.length, 1);
  assert.match(re_.uyarilar[0], /düzgün yayılı eşdeğer/);
});
