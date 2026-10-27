/* docs/model_ops.js birim testleri — node'un yerleşik test koşucusu (bağımlılık yok).
   Çalıştırma: node --test testler/js/model_ops.test.js */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const M = require(path.join(__dirname, "..", "..", "docs", "model_ops.js"));

const YAKIN = 1e-6;
function yakin(a, b, tol, mesaj) {
  tol = tol == null ? YAKIN : tol;
  if (Array.isArray(a)) {
    assert.equal(a.length, b.length, mesaj);
    a.forEach(function (x, i) { yakin(x, b[i], tol, mesaj); });
    return;
  }
  assert.ok(Math.abs(a - b) <= tol, (mesaj || "") + ` beklenen ${b}, bulunan ${a}`);
}
function ic(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function dis(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function cubuk(model, no) { return model.cubuklar.find(function (c) { return c.no === no; }); }
function konum(model, ref) { return M.dugumKonumu(model, ref); }
function uclar(model, no) { const c = cubuk(model, no); return [konum(model, c.i), konum(model, c.j)]; }
function turSay(model, tur) { return model.cubuklar.filter(function (c) { return c.tur === tur; }).length; }
function dno(model, ref) { return M.dugumNo(model, ref); }

/** Düşey çerçeve gözü: A(0,0,0) B(6,0,0) C(6,0,4) D(0,0,4); kolonlar 1,2, kiriş 3 (D→C), alt bağ kirişi isteğe bağlı (4: A→B). */
function cerceve(altKiris) {
  const m = {
    tur: "bina", surum: 3,
    dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 6, Y: 0, Z: 0 }, { no: 100003, X: 6, Y: 0, Z: 4 }, { no: 100004, X: 0, Y: 0, Z: 4 }],
    cubuklar: [
      { no: 1, i: { dugum: 100001 }, j: { dugum: 100004 }, tur: "kolon", kesit: "HEB240", aci: 0 },
      { no: 2, i: { dugum: 100002 }, j: { dugum: 100003 }, tur: "kolon", kesit: "HEB240", aci: 0 },
      { no: 3, i: { dugum: 100004 }, j: { dugum: 100003 }, tur: "kiris", kesit: "IPE300", aci: 0 },
    ],
    mesnetler: [{ dugum: { dugum: 100001 }, ux: true, uy: true, uz: true, rx: true, ry: true, rz: true },
      { dugum: { dugum: 100002 }, ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }],
  };
  if (altKiris) m.cubuklar.push({ no: 4, i: { dugum: 100001 }, j: { dugum: 100002 }, tur: "kiris", kesit: "IPE300", aci: 0 });
  return m;
}
const GOZ = [{ dugum: 100001 }, { dugum: 100002 }, { dugum: 100003 }, { dugum: 100004 }];

/** Tek düz çubuk (0,0,0)→(L,0,0). */
function tekCubuk(L, ek) {
  return Object.assign({
    tur: "bina", surum: 3,
    dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: L, Y: 0, Z: 0 }],
    cubuklar: [{ no: 7, i: { dugum: 100001 }, j: { dugum: 100002 }, tur: "kiris", kesit: "IPE300", aci: 15, grup: "G1", yalniz_cekme: false,
      serbest: { i: ["My", "Mz"], j: ["T", "Mz"] } }],
  }, ek || {});
}

/** Aks–kat modeli: A–B–C (0, 5, 9) × 1–2 (0, 4), 2 kat; kiriş 1 A1→C1 (komşu olmayan akslar → 2 parça). */
function aksKat() {
  const kol = [];
  let n = 0;
  for (const k of [1, 2]) for (const x of ["A", "B", "C"]) for (const y of ["1", "2"]) kol.push({ no: ++n, aks: [x, y], kat: k, kesit: "S40x40", yon: (n % 2) ? "x" : "y" });
  const kir = [];
  let kn = 0;
  for (const k of [1, 2]) {
    kir.push({ no: ++kn, kat: k, bas: ["A", "1"], son: ["C", "1"], kesit: "K25x50", duvar: "tugla19" });
    kir.push({ no: ++kn, kat: k, bas: ["C", "2"], son: ["A", "2"], kesit: "K25x50" });
    for (const x of ["A", "B", "C"]) kir.push({ no: ++kn, kat: k, bas: [x, "1"], son: [x, "2"], kesit: "K25x50" });
  }
  const dos = [];
  let d = 0;
  for (const k of [1, 2]) { dos.push({ no: ++d, kat: k, kose: [["A", "1"], ["B", "2"]], h: 0.14, kullanim: "konut", g_ek: 1.5, q: null, dagitim: "otomatik" });
    dos.push({ no: ++d, kat: k, kose: [["B", "1"], ["C", "2"]], h: 0.14, kullanim: "konut", g_ek: 1.5, q: 3.5, dagitim: "tek" }); }
  return {
    tur: "bina", surum: 1,
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "C", konum: 9 }, { ad: "B", konum: 5 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }] },
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, kot: 3 }, { no: 2, kot: 6 }],
    kesitler: { S40x40: { tip: "dikdortgen", b: 0.4, h: 0.4 }, K25x50: { tip: "dikdortgen", b: 0.25, h: 0.5 } },
    kolonlar: kol, kirisler: kir, dosemeler: dos,
    ek_yukler: [{ tur: "kiris", kiris: 1, durum: "G", q: 2 }, { tur: "dugum", aks: ["B", "2"], kat: 2, durum: "Q", FZ: -10 }, { tur: "doseme", doseme: 2, g: 0.5, q: 0 }],
    temeller: { mesnet: "ankastre" },
  };
}

// ---------------------------------------------------------------------------- yerel eksenler
test("yerel eksenler: motor Kassimali kuralı (bina koordinatında) ve aci", function () {
  let e = M.yerelEksenVektor([0, 0, 0], [5, 0, 0], 0);
  yakin(e.y, [0, 0, 1]); yakin(e.z, [0, -1, 0]);
  e = M.yerelEksenVektor([0, 0, 0], [0, 0, 3], 0); // kolon: y′ = −X, z′ = −Y (§2)
  yakin(e.y, [-1, 0, 0]); yakin(e.z, [0, -1, 0]);
  e = M.yerelEksenVektor([0, 0, 0], [0, 0, 3], 90); // yon "y" eşdeğeri: güçlü eksen (y″) Y doğrultusunda
  yakin(e.y, [0, -1, 0]); yakin(e.z, [1, 0, 0]);
  e = M.yerelEksenVektor([0, 0, 3], [0, 0, 0], 0); // aşağı yönlü düşey
  yakin(e.y, [1, 0, 0]); yakin(e.z, [0, -1, 0]);
  // motorun λ'sı (motor koordinatı x=X, y=Z, z=−Y) ile karşılaştırma; rastgele eğik elemanlar, sağ el ve dik birimlik
  const rnd = (function () { let s = 7; return function () { s = (s * 16807) % 2147483647; return s / 2147483647 - 0.5; }; })();
  for (let k = 0; k < 50; k++) {
    const A = [rnd() * 10, rnd() * 10, rnd() * 10], B = [rnd() * 10, rnd() * 10, rnd() * 10];
    const ee = M.yerelEksenVektor(A, B, 0);
    const d = [B[0] - A[0], B[2] - A[2], -(B[1] - A[1])], L = Math.hypot(d[0], d[1], d[2]);
    const cx = d[0] / L, cy = d[1] / L, cz = d[2] / L, D = Math.hypot(cx, cz);
    const ym = [-cx * cy / D, D, -cy * cz / D], zm = [-cz / D, 0, cx / D];
    const bina = function (v) { return [v[0], -v[2], v[1]]; };
    yakin(ee.y, bina(ym), 1e-9); yakin(ee.z, bina(zm), 1e-9);
    yakin(dis(ee.x, ee.y), ee.z, 1e-9);
    const a = rnd() * 360, ea = M.yerelEksenVektor(A, B, a);
    yakin(ic(ea.y, ea.y), 1, 1e-9); yakin(ic(ea.y, ea.x), 0, 1e-9); yakin(dis(ea.x, ea.y), ea.z, 1e-9);
    yakin(ic(ea.y, ee.y), Math.cos(a * Math.PI / 180), 1e-9);
  }
});

test("uzunluk, eğim, yerelEksenler model üzerinden", function () {
  const m = { dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 4, Y: 0, Z: 3 }], cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 }, aci: 0 }] };
  yakin(M.uzunluk(m, 1), 5);
  yakin(M.egim(m, 1), Math.atan2(3, 4) * 180 / Math.PI);
  yakin(M.yerelEksenler(m, 1).y, [-0.6, 0, 0.8]);
});

// ---------------------------------------------------------------------------- düğümler
test("dugumEkle: 1 mm birleştirme toleransı ve serbest numaralama", function () {
  const m = tekCubuk(5);
  let r = M.dugumEkle(m, 0, 0, 0.0005);
  assert.equal(r.no, 100001); assert.deepEqual(r.eklenen.dugumler, []); assert.ok(r.uyarilar.length);
  r = M.dugumEkle(m, 0, 0, 0.002, "yeni");
  assert.equal(r.no, 100003); assert.deepEqual(r.eklenen.dugumler, [100003]);
  assert.equal(r.model.dugumler[2].ad, "yeni");
  assert.equal(M.dugumBul(r.model, 0, 0, 0.0021), 100003);
  assert.equal(M.dugumBul(r.model, 3, 3, 3), null);
  assert.equal(M.dugumEkle({}, 1, 2, 3).no, 100001);
});

test("dugumTasi: bağlı çubuklar izler; aks–kat düğümü önce genelleştirilir ve serbest düğüm olur", function () {
  const m = tekCubuk(5);
  const r = M.dugumTasi(m, 100002, 3, 0, 4);
  yakin(M.uzunluk(r.model, 7), 5);
  assert.deepEqual(r.degisen.dugumler, [100002]);
  const a = aksKat();
  const t = M.dugumTasi(a, { aks: ["A", "1"], kat: 0 }, -0.5, 0, 0);
  assert.equal(t.model.kolonlar.length, 0);
  assert.ok(t.no >= 100001);
  assert.ok(t.uyarilar.some(function (u) { return /genelleştirildi/.test(u); }));
  const kol = t.model.cubuklar.find(function (c) { return c.kaynak && c.kaynak.aks_kat === "kolon" && c.kaynak.no === 1; });
  assert.deepEqual(kol.i, { dugum: t.no });
  yakin(konum(t.model, kol.i), [-0.5, 0, 0]);
  // taban düğümü taşındı → açık mesnet (temeller.mesnet = ankastre)
  const ms = t.model.mesnetler.find(function (s) { return s.dugum.dugum === t.no; });
  assert.ok(ms && ms.rx && ms.uz);
  assert.ok(!t.model.dugumler.some(function (d) { return d.no === 1; }));
});

test("dugumleriBirlestir: tolerans, çubuk uçları yeniden bağlanır, sıfır boylu çubuk silinir", function () {
  const m = {
    dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 5, Y: 0, Z: 0 }, { no: 100003, X: 5.0005, Y: 0, Z: 0 }, { no: 100004, X: 5, Y: 3, Z: 0 },
      { no: 100005, X: 5.002, Y: 3, Z: 0 }, { no: 100006, X: 9, Y: 3, Z: 0 }],
    cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 } }, { no: 2, i: { dugum: 100003 }, j: { dugum: 100004 } },
      { no: 3, i: { dugum: 100002 }, j: { dugum: 100003 } }, { no: 4, i: { dugum: 100005 }, j: { dugum: 100006 } }],
    ek_yukler: [{ tur: "cubuk", cubuk: 3, durum: "G", yon: "Z", q1: -1, q2: -1 }],
  };
  const r = M.dugumleriBirlestir(m, 0.001);
  assert.deepEqual(r.birlesen, [[100003, 100002]]);
  assert.deepEqual(r.silinen.cubuklar, [3]);
  assert.deepEqual(cubuk(r.model, 2).i, { dugum: 100002 });
  assert.equal(r.model.ek_yukler.length, 0);
  assert.ok(r.model.dugumler.some(function (d) { return d.no === 100005; }), "2 mm aralık 1 mm toleransla birleşmez");
  const r2 = M.dugumleriBirlestir(m, 0.003);
  assert.equal(r2.birlesen.length, 2);
  assert.deepEqual(cubuk(r2.model, 4).i, { dugum: 100004 });
});

// ---------------------------------------------------------------------------- böl
test("bol {parca}: geometri, özellik aktarımı, serbestlikler yalnız dış uçlarda", function () {
  const m = tekCubuk(6);
  const r = M.bol(m, 7, { parca: 3 });
  assert.deepEqual(r.parcalar, [7, 8, 9]);
  assert.deepEqual(r.eklenen.cubuklar, [8, 9]);
  assert.equal(r.eklenen.dugumler.length, 2);
  r.parcalar.forEach(function (no) { yakin(M.uzunluk(r.model, no), 2); });
  yakin(uclar(r.model, 8)[0], [2, 0, 0]); yakin(uclar(r.model, 9)[0], [4, 0, 0]);
  for (const no of r.parcalar) {
    const c = cubuk(r.model, no);
    assert.equal(c.kesit, "IPE300"); assert.equal(c.tur, "kiris"); assert.equal(c.aci, 15); assert.equal(c.grup, "G1"); assert.equal(c.yalniz_cekme, false);
  }
  assert.deepEqual(cubuk(r.model, 7).serbest, { i: ["My", "Mz"] });
  assert.equal(cubuk(r.model, 8).serbest, undefined);
  assert.deepEqual(cubuk(r.model, 9).serbest, { j: ["T", "Mz"] });
});

test("bol {uzunluk, bastan}, {oranlar}, {noktalar}", function () {
  const m = tekCubuk(5);
  let r = M.bol(m, 7, { uzunluk: 2, bastan: true });
  assert.deepEqual(r.parcalar.map(function (n) { return Math.round(M.uzunluk(r.model, n) * 1e6) / 1e6; }), [2, 2, 1]);
  r = M.bol(m, 7, { uzunluk: 2, bastan: false });
  assert.deepEqual(r.parcalar.map(function (n) { return Math.round(M.uzunluk(r.model, n) * 1e6) / 1e6; }), [1, 2, 2]);
  r = M.bol(m, 7, { oranlar: [0.6, 0.25, 1.5] });
  assert.deepEqual(r.parcalar.map(function (n) { return Math.round(M.uzunluk(r.model, n) * 1e6) / 1e6; }), [1.25, 1.75, 2]);
  assert.ok(r.uyarilar.some(function (u) { return /1\.5/.test(u); }));
  r = M.bol(m, 7, { noktalar: [[1, 0, 0], [3, 0.0004, 0], [2, 1, 0]] });
  assert.equal(r.parcalar.length, 3);
  assert.ok(r.uyarilar.some(function (u) { return /üzerinde değil/.test(u); }));
  assert.throws(function () { M.bol(m, 99, { parca: 2 }); }, M.ModelHatasi);
  assert.throws(function () { M.bol(m, 7, {}); }, M.ModelHatasi);
});

test("bol: çubuk yükleri doğru x aralıklarıyla bölünür; kren yolu güncellenir", function () {
  const m = tekCubuk(6, {
    ek_yukler: [{ tur: "cubuk", cubuk: 7, durum: "G", yon: "Z", q1: -2, q2: -2, x1: 0, x2: null, oransal: false, izdusum: false },
      { tur: "cubuk", cubuk: 7, durum: "Q", yon: "Z", q1: 0, q2: -6, x1: 1, x2: 4, oransal: false },
      { tur: "cubuk", cubuk: 7, durum: "Q", yon: "y′", q1: -1, q2: -1, x1: 0.5, x2: 1, oransal: true }],
    kren: [{ no: 1, yol: [5, 7, 6] }],
  });
  const r = M.bol(m, 7, { parca: 2 });
  const y = r.model.ek_yukler;
  const g = y.filter(function (x) { return x.durum === "G"; });
  assert.deepEqual(g.map(function (x) { return [x.cubuk, x.x1, x.x2, x.q1, x.q2]; }), [[7, 0, null, -2, -2], [8, 0, null, -2, -2]]);
  const tr = y.filter(function (x) { return x.durum === "Q" && x.yon === "Z"; });
  assert.deepEqual(tr.map(function (x) { return [x.cubuk, x.x1, x.x2, x.q1, x.q2]; }), [[7, 1, null, 0, -4], [8, 0, 1, -4, -6]]);
  const ob = y.filter(function (x) { return x.yon === "y′"; });
  assert.deepEqual(ob.map(function (x) { return [x.cubuk, x.x1, x.x2, x.oransal]; }), [[8, 0, null, true]]);
  assert.deepEqual(r.model.kren[0].yol, [5, 7, 8, 6]);
});

test("kesisimlerdeBol: 3B çapraz kesişim, paralel ve eş doğrusal çubuklar, T birleşimi, aykırı doğrular", function () {
  const m = {
    dugumler: [{ no: 100001, X: 0, Y: 0, Z: 3 }, { no: 100002, X: 4, Y: 2, Z: 3 }, { no: 100003, X: 2, Y: 1, Z: 0 }, { no: 100004, X: 2, Y: 1, Z: 6 },
      { no: 100005, X: 0, Y: 1, Z: 0 }, { no: 100006, X: 0, Y: 1, Z: 6 }, { no: 100007, X: 0, Y: 5, Z: 0 }, { no: 100008, X: 0, Y: 5, Z: 3 },
      { no: 100009, X: 0, Y: 3, Z: 0 }, { no: 100010, X: 0, Y: 3, Z: 1.5 }],
    cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 }, kesit: "A" }, { no: 2, i: { dugum: 100003 }, j: { dugum: 100004 }, kesit: "B" },
      { no: 3, i: { dugum: 100005 }, j: { dugum: 100006 } }, { no: 4, i: { dugum: 100007 }, j: { dugum: 100008 } },
      { no: 5, i: { dugum: 100009 }, j: { dugum: 100010 } }],
  };
  const r = M.kesisimlerdeBol(m, [1, 2, 3, 4]);
  assert.equal(r.kesisim_sayisi, 1);
  assert.deepEqual(r.parcalar[1].length, 2); assert.deepEqual(r.parcalar[2].length, 2);
  assert.equal(r.parcalar[3], undefined, "paralel çubuk bölünmez");
  assert.equal(r.eklenen.dugumler.length, 1);
  yakin(konum(r.model, { dugum: r.eklenen.dugumler[0] }), [2, 1, 3]);
  yakin(M.uzunluk(r.model, 1), Math.sqrt(5));
  // T birleşimi: 6 numaralı çubuk (0,0,2)→(0,1,2) ucu 3 numaralının ortasına değer → yalnız 3 bölünür
  const t = JSON.parse(JSON.stringify(m));
  t.dugumler.push({ no: 100011, X: -1, Y: 1, Z: 2 }, { no: 100012, X: 0, Y: 1, Z: 2.0004 });
  t.cubuklar.push({ no: 6, i: { dugum: 100011 }, j: { dugum: 100012 } });
  const rt = M.kesisimlerdeBol(t, [3, 6]);
  assert.equal(rt.parcalar[3].length, 2); assert.equal(rt.parcalar[6], undefined);
  // eş doğrusal üst üste: uyarı, bölme yok
  const e = { dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 4, Y: 0, Z: 0 }, { no: 100003, X: 2, Y: 0, Z: 0 }, { no: 100004, X: 6, Y: 0, Z: 0 }],
    cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 } }, { no: 2, i: { dugum: 100003 }, j: { dugum: 100004 } }] };
  const re = M.kesisimlerdeBol(e, [1, 2]);
  assert.equal(re.model.cubuklar.length, 2); assert.ok(re.uyarilar.some(function (u) { return /eş doğrusal/.test(u); }));
  // aykırı (10 cm arayla geçen) doğrular kesişmez; 1 mm toleransın altındaki aralık kesişim sayılır
  const a = { dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 4, Y: 0, Z: 0 }, { no: 100003, X: 2, Y: -2, Z: 0.1 }, { no: 100004, X: 2, Y: 2, Z: 0.1 }],
    cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 } }, { no: 2, i: { dugum: 100003 }, j: { dugum: 100004 } }] };
  assert.equal(M.kesisimlerdeBol(a, [1, 2]).kesisim_sayisi, 0);
  a.dugumler[2].Z = 0.0008; a.dugumler[3].Z = 0.0008;
  assert.equal(M.kesisimlerdeBol(a, [1, 2]).kesisim_sayisi, 1);
});

test("duzlemleBol: Z = 2 düzlemi kolonları böler, yatay çubuğa dokunmaz", function () {
  const m = cerceve();
  const r = M.duzlemleBol(m, [1, 2, 3], { Z: 2.5 });
  assert.deepEqual(Object.keys(r.parcalar).sort(), ["1", "2"]);
  yakin(uclar(r.model, 1)[1], [0, 0, 2.5]);
  const r2 = M.duzlemleBol(m, [3], { nokta: [3, 0, 0], normal: [1, 0, 0] });
  yakin(M.uzunluk(r2.model, 3), 3);
});

// ---------------------------------------------------------------------------- birleştir
test("birlestir: bol sonrası geri birleştirme özgün çubuğu ve yükleri verir", function () {
  const m = tekCubuk(6, { ek_yukler: [{ tur: "cubuk", cubuk: 7, durum: "G", yon: "Z", q1: -2, q2: -2, x1: 0, x2: null, oransal: false, izdusum: false }] });
  const b = M.bol(m, 7, { parca: 3 });
  const j = M.birlestir(b.model, b.parcalar);
  assert.deepEqual(j.birlesen, [7]);
  assert.deepEqual(j.model.cubuklar, m.cubuklar);
  assert.deepEqual(j.model.dugumler, m.dugumler);
  assert.deepEqual(j.model.ek_yukler, m.ek_yukler);
  // trapez yük bölünüp birleşince iki parça kalır ama mutlak x aralıkları doğru
  const t = tekCubuk(6, { ek_yukler: [{ tur: "cubuk", cubuk: 7, durum: "Q", yon: "Z", q1: 0, q2: -6 }] });
  const tb = M.bol(t, 7, { parca: 2 });
  const tj = M.birlestir(tb.model, tb.parcalar);
  assert.deepEqual(tj.model.ek_yukler.map(function (y) { return [y.cubuk, y.x1, y.x2, y.q1, y.q2]; }), [[7, 0, 3, 0, -3], [7, 3, null, -3, -6]]);
});

test("birlestir: ters yönlü üye, yerel yük ve serbest uçlar", function () {
  const m = {
    dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 2, Y: 0, Z: 0 }, { no: 100003, X: 5, Y: 0, Z: 0 }],
    cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 }, kesit: "K", tur: "kiris", serbest: { i: ["My", "Mz"] } },
      { no: 2, i: { dugum: 100003 }, j: { dugum: 100002 }, kesit: "K", tur: "kiris", serbest: { i: ["Mz"] } }],
    ek_yukler: [{ tur: "cubuk", cubuk: 2, durum: "G", yon: "z′", q1: 1, q2: 3, x1: 0, x2: null }],
  };
  const r = M.birlestir(m, [2, 1]);
  assert.deepEqual(r.birlesen, [1]);
  const c = cubuk(r.model, 1);
  assert.deepEqual(c.j, { dugum: 100003 });
  assert.deepEqual(c.serbest, { i: ["My", "Mz"], j: ["Mz"] });
  assert.ok(!r.model.dugumler.some(function (d) { return d.no === 100002; }), "ara düğüm silinir");
  // ters üyede z′ ters döner: yük işareti ve x aralığı çevrilir
  assert.deepEqual(r.model.ek_yukler.map(function (y) { return [y.cubuk, y.yon, y.x1, y.x2, y.q1, y.q2]; }), [[1, "z′", 2, null, -3, -1]]);
});

test("birlestir: reddetme gerekçeleri", function () {
  const taban = function () {
    return {
      dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 2, Y: 0, Z: 0 }, { no: 100003, X: 5, Y: 0, Z: 0 }, { no: 100004, X: 2, Y: 0, Z: 3 }],
      cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 }, kesit: "K", tur: "kiris" }, { no: 2, i: { dugum: 100002 }, j: { dugum: 100003 }, kesit: "K", tur: "kiris" }],
    };
  };
  const dene = function (degistir, desen) {
    const m = taban(); degistir(m);
    const r = M.birlestir(m, [1, 2]);
    assert.deepEqual(r.birlesen, [], String(desen));
    assert.equal(r.model.cubuklar.length, m.cubuklar.length);
    assert.ok(r.uyarilar.some(function (u) { return desen.test(u); }), "gerekçe " + desen + " yok: " + r.uyarilar.join(" | "));
    assert.ok(r.reddedilen.length === 1);
  };
  dene(function (m) { m.cubuklar[1].kesit = "L"; }, /kesitler farklı/);
  dene(function (m) { m.cubuklar[1].tur = "capraz"; }, /türler farklı/);
  dene(function (m) { m.cubuklar[1].aci = 30; }, /aci/);
  dene(function (m) { m.dugumler[2].Z = 0.5; }, /eş doğrusal değil/);
  dene(function (m) { m.cubuklar.push({ no: 3, i: { dugum: 100002 }, j: { dugum: 100004 } }); }, /başka çubuk bağlı/);
  dene(function (m) { m.mesnetler = [{ dugum: { dugum: 100002 }, uz: true }]; }, /mesnet/);
  dene(function (m) { m.ek_yukler = [{ tur: "dugum", dugum: { dugum: 100002 }, durum: "G", FZ: -5 }]; }, /düğüm yükü/);
  dene(function (m) { m.cubuklar[0].serbest = { j: ["My", "Mz"] }; }, /uç serbestliği/);
  dene(function (m) { m.paneller = [{ no: 1, kose: [{ dugum: 100001 }, { dugum: 100002 }, { dugum: 100004 }] }]; }, /panel köşesi/);
  const d = taban(); d.cubuklar.push({ no: 3, i: { dugum: 100002 }, j: { dugum: 100004 }, kesit: "K", tur: "kiris" });
  const rd = M.birlestir(d, [1, 2, 3]);
  assert.ok(rd.uyarilar.some(function (u) { return /dallanma/.test(u); }));
  const tek = M.birlestir(taban(), [1]);
  assert.ok(tek.uyarilar.some(function (u) { return /en az iki/.test(u); }));
});

// ---------------------------------------------------------------------------- çiz / sil / özellik / serbestlik
test("cubukCiz, cubukZinciri, cubukSil (yetim düğüm temizliği), ozellikAta", function () {
  let r = M.cubukCiz({ tur: "bina" }, [0, 0, 0], { X: 3, Y: 0, Z: 0 }, { kesit: "IPE200", tur: "kiris" });
  assert.equal(r.no, 1); assert.equal(r.model.surum, 3); assert.equal(r.model.dugumler.length, 2);
  const tekrar = M.cubukCiz(r.model, [0, 0, 0], [3, 0, 0]);
  assert.ok(tekrar.reddedildi); assert.equal(tekrar.model.cubuklar.length, 1);
  assert.ok(M.cubukCiz(r.model, [0, 0, 0], [0, 0, 0.0005]).reddedildi);
  const z = M.cubukZinciri(r.model, [[3, 0, 0], [3, 0, 3], [0, 0, 3]], { tur: "kiris" });
  assert.deepEqual(z.nolar, [2, 3]);
  const s = M.cubukSil(z.model, [3]);
  assert.deepEqual(s.silinen.cubuklar, [3]); assert.equal(s.silinen.dugumler.length, 1);
  const o = M.ozellikAta(s.model, [1, 2], { kesit: "HEA200", aci: 90, yalniz_cekme: true });
  assert.equal(cubuk(o.model, 2).kesit, "HEA200"); assert.equal(cubuk(o.model, 1).aci, 90);
  assert.ok(o.uyarilar.some(function (u) { return /9\.6\.4\.3/.test(u); }));
  assert.throws(function () { M.ozellikAta(s.model, [1], { serbest: {} }); }, M.ModelHatasi);
});

test("serbestlikAta: hazır ayarlar, doğrulama ve mekanizma uyarısı", function () {
  const m = tekCubuk(5);
  let r = M.serbestlikAta(m, [7], M.MAFSAL_IKI_UC);
  assert.deepEqual(cubuk(r.model, 7).serbest, { i: ["My", "Mz"], j: ["My", "Mz"] });
  r = M.serbestlikAta(m, [7], M.KAFES_CUBUGU);
  assert.deepEqual(cubuk(r.model, 7).serbest, { i: ["T", "My", "Mz"], j: ["My", "Mz"] });
  assert.equal(r.uyarilar.length, 0);
  r = M.serbestlikAta(m, [7], M.MAFSAL_J);
  assert.deepEqual(cubuk(r.model, 7).serbest, { j: ["My", "Mz"] });
  r = M.serbestlikAta(m, [7], { i: [], j: [] });
  assert.equal(cubuk(r.model, 7).serbest, undefined);
  r = M.serbestlikAta(m, [7], { i: ["Mz", "T", "My"], j: ["T", "My", "Mz"] });
  assert.deepEqual(cubuk(r.model, 7).serbest.i, ["T", "My", "Mz"]);
  assert.ok(r.uyarilar.some(function (u) { return /mekanizma/.test(u); }));
  assert.throws(function () { M.serbestlikAta(m, [7], { i: ["Mx"] }); }, M.ModelHatasi);
});

// ---------------------------------------------------------------------------- kopyala / ayna / döndür / taşı
test("dogrusalDizi: konumlar, mesnet kopyası, yük kopyası", function () {
  const m = cerceve();
  m.ek_yukler = [{ tur: "cubuk", cubuk: 3, durum: "G", yon: "Z", q1: -3, q2: -3 }];
  const r = M.dogrusalDizi(m, [1, 2, 3], 0, 6, 0, 2);
  assert.equal(r.model.cubuklar.length, 9);
  assert.equal(r.model.dugumler.length, 12);
  assert.equal(r.model.mesnetler.length, 6);
  yakin(uclar(r.model, r.kopyalar[1].cubuklar[2])[0], [0, 12, 4]);
  assert.equal(r.model.ek_yukler.length, 3);
  // aynı yere ikinci kopya çakışır → atlanır
  const r2 = M.dogrusalDizi(r.model, [1], 0, 6, 0, 1);
  assert.equal(r2.model.cubuklar.length, 9); assert.ok(r2.uyarilar.length);
});

test("ayna: konum, yerel eksen açısının yansıması, panel sırası", function () {
  const m = { dugumler: [{ no: 100001, X: 1, Y: 0, Z: 0 }, { no: 100002, X: 3, Y: 1, Z: 2 }],
    cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 }, kesit: "L", aci: 25 }] };
  const r = M.ayna(m, [1], { X: 5 });
  const y = cubuk(r.model, 2);
  yakin(konum(r.model, y.i), [9, 0, 0]); yakin(konum(r.model, y.j), [7, 1, 2]);
  const e0 = M.yerelEksenler(m, 1), e1 = M.yerelEksenler(r.model, 2);
  yakin(e1.y, [-e0.y[0], e0.y[1], e0.y[2]], 1e-9);
  // eğik düzlem
  const r2 = M.ayna(m, [1], { nokta: [0, 0, 0], normal: [1, 1, 0] });
  const n = [Math.SQRT1_2, Math.SQRT1_2, 0], R = function (v) { const d = 2 * ic(v, n); return [v[0] - d * n[0], v[1] - d * n[1], v[2] - d * n[2]]; };
  yakin(M.yerelEksenler(r2.model, 2).y, R(e0.y), 1e-9);
  // yerinde ayna (kopya: false)
  const r3 = M.ayna(m, [1], { X: 5 }, { kopya: false });
  assert.equal(r3.model.cubuklar.length, 1);
  yakin(uclar(r3.model, 1)[0], [9, 0, 0]);
});

test("dondur: kopya ve yerinde döndürme, açı güncellemesi", function () {
  const m = cerceve();
  const r = M.dondur(m, [1, 2, 3], { nokta: [0, 0, 0], yon: [0, 0, 1] }, 90, { kopya: true });
  const k = r.kopyalar[0].cubuklar;
  assert.equal(k.length, 2, "dönme eksenindeki kolon 1'in kopyası kendisiyle çakışır, atlanır");
  assert.ok(r.uyarilar.some(function (u) { return /çakışıyor/.test(u); }));
  yakin(uclar(r.model, k[0])[0], [0, 6, 0]);
  // kolon güçlü ekseni (y″ = −X) Z etrafında 90° döner → −Y: aci = 90
  yakin(M.yerelEksenler(r.model, k[0]).y, [0, -1, 0], 1e-9);
  yakin(cubuk(r.model, k[0]).aci, 90, 1e-6);
  assert.equal(r.model.mesnetler.length, 3, "A düğümü dönme ekseninde (aynı düğüm), B kopyasına mesnet");
  const t = M.dondur(m, [3], "Z", 180);
  yakin(uclar(t.model, 3)[0], [0, 0, 4]); yakin(uclar(t.model, 3)[1], [-6, 0, 4]);
  assert.equal(cubuk(t.model, 2).i.dugum, 100002, "seçilmeyen kolon düğümü yerinde kalır mı? kiriş düğümü taşındı, kolon uzar");
  const ts = M.tasi(m, { dugumler: [{ dugum: 100003 }] }, 0, 0, 1);
  yakin(M.uzunluk(ts.model, 2), 5);
});

// ---------------------------------------------------------------------------- panel
test("panelOlustur: düzlemsellik ve dışbükeylik denetimi; panelKenarCubuklari", function () {
  const m = cerceve(true);
  let r = M.panelOlustur(m, GOZ, { tur: "cephe" });
  assert.equal(r.no, 1); assert.equal(r.model.paneller[0].tur, "cephe");
  yakin(r.geometri.alan, 24); yakin(r.geometri.egim, 90);
  const k = M.panelKenarCubuklari(r.model, 1);
  assert.deepEqual(k.map(function (x) { return x.tam; }), [true, true, true, true]);
  assert.deepEqual(k[0].cubuklar, [4]);
  r = M.panelOlustur(m, GOZ);
  const b = M.bol(r.model, 4, { parca: 2 });
  assert.deepEqual(M.panelKenarCubuklari(b.model, 1)[0].cubuklar, [4, 5]);
  const s = M.cubukSil(b.model, [5], { dugumleriTemizle: false });
  const ks = M.panelKenarCubuklari(s.model, 1)[0];
  assert.equal(ks.tam, false); assert.deepEqual(ks.bosluklar, [[3, 6]]);
  // düzlemsel değil
  const d = cerceve(); d.dugumler[2].Y = 0.2;
  const rd = M.panelOlustur(d, GOZ);
  assert.ok(rd.reddedildi); assert.ok(rd.uyarilar.some(function (u) { return /düzlemsel değil/.test(u); }));
  // dışbükey değil (ok ucu)
  const o = M.panelOlustur({}, [[0, 0, 0], [4, 0, 0], [1, 1, 0], [0, 4, 0]]);
  assert.ok(o.reddedildi); assert.ok(o.uyarilar.some(function (u) { return /dışbükey/.test(u); }));
  // kendini kesen
  const x = M.panelOlustur({}, [[0, 0, 0], [4, 4, 0], [4, 0, 0], [0, 4, 0]]);
  assert.ok(x.reddedildi);
  // kenarında çubuk yok uyarısı
  const u = M.panelOlustur(cerceve(), GOZ);
  assert.ok(u.uyarilar.some(function (v) { return /tam çubuk zinciri yok/.test(v); }));
});

// ---------------------------------------------------------------------------- çapraz üreteci
test("caprazUret X / tek: çapraz sayısı, uçlar mafsallı, köşe sırası önemsiz", function () {
  const m = cerceve();
  let r = M.caprazUret(m, GOZ, "X", { kesit: "L80" });
  assert.equal(r.caprazlar.length, 2);
  for (const no of r.caprazlar) { const c = cubuk(r.model, no); assert.equal(c.tur, "capraz"); assert.deepEqual(c.serbest, { i: ["My", "Mz"], j: ["My", "Mz"] }); assert.deepEqual(c.kaynak, { uretec: 1 }); }
  assert.equal(r.model.uretecler[0].tip, "X");
  const r2 = M.caprazUret(m, [GOZ[2], GOZ[0], GOZ[3], GOZ[1]].length && [GOZ[3], GOZ[2], GOZ[1], GOZ[0]], "tek-/", { kesit: "L80", mafsalli_uclar: false });
  yakin(uclar(r2.model, r2.caprazlar[0])[0], [0, 0, 0]); yakin(uclar(r2.model, r2.caprazlar[0])[1], [6, 0, 4]);
  assert.equal(cubuk(r2.model, r2.caprazlar[0]).serbest, undefined);
  const r3 = M.caprazUret(m, GOZ, "tek-\\", { kesit: "L80" });
  yakin(uclar(r3.model, r3.caprazlar[0])[0], [6, 0, 0]); yakin(uclar(r3.model, r3.caprazlar[0])[1], [0, 0, 4]);
  const r4 = M.caprazUret(m, GOZ, "X", { kesit: "L80", kesisim: "bagli", yalniz_cekme: true });
  assert.equal(r4.caprazlar.length, 4); assert.equal(r4.eklenen.dugumler.length, 1);
  yakin(konum(r4.model, { dugum: r4.eklenen.dugumler[0] }), [3, 0, 2]);
  assert.ok(r4.uyarilar.some(function (u) { return /9\.6\.4\.3/.test(u); }));
  assert.ok(cubuk(r4.model, r4.caprazlar[0]).yalniz_cekme);
  assert.throws(function () { M.caprazUret(m, GOZ, "Y"); }, M.ModelHatasi);
});

test("caprazUret ters-V / V: kiriş ortadan bölünür", function () {
  const r = M.caprazUret(cerceve(), GOZ, "ters-V", { kesit: "L80" });
  assert.equal(r.model.cubuklar.length, 6);
  const kirisler = r.model.cubuklar.filter(function (c) { return c.tur === "kiris"; });
  assert.equal(kirisler.length, 2);
  kirisler.forEach(function (c) { yakin(M.uzunluk(r.model, c.no), 3); assert.equal(c.kaynak, undefined); });
  for (const no of r.caprazlar) yakin(uclar(r.model, no)[1], [3, 0, 4]);
  assert.deepEqual(r.model.uretecler[0].bolunen, [[3, 4]]);
  const v = M.caprazUret(cerceve(true), GOZ, "V", { kesit: "L80" });
  for (const no of v.caprazlar) yakin(uclar(v.model, no)[0], [3, 0, 0]);
  assert.equal(turSay(v.model, "kiris"), 3);
  const vu = M.caprazUret(cerceve(false), GOZ, "V", { kesit: "L80" });
  assert.ok(vu.uyarilar.some(function (u) { return /kenarında çubuk yok/.test(u); }));
});

test("caprazUret K: kolon ortadan bölünür ve TBDY uyarısı", function () {
  const r = M.caprazUret(cerceve(), GOZ, "K", { kesit: "L80" });
  assert.equal(turSay(r.model, "kolon"), 3);
  for (const no of r.caprazlar) yakin(uclar(r.model, no)[1], [6, 0, 2]);
  assert.ok(r.uyarilar.some(function (u) { return /9\.6\.4\.2/.test(u); }));
  const s = M.caprazUret(cerceve(), GOZ, "K", { kesit: "L80", kolon: "sol" });
  for (const no of s.caprazlar) yakin(uclar(s.model, no)[1], [0, 0, 2]);
});

test("caprazUret dışmerkez: bağ kirişi boyu e", function () {
  const r = M.caprazUret(cerceve(), GOZ, "dismerkez-ters-V", { kesit: "HEA160", e: 1.0 });
  const bag = cubuk(r.model, r.bag_kirisi);
  assert.equal(bag.tur, "bag"); yakin(M.uzunluk(r.model, bag.no), 1.0);
  yakin(uclar(r.model, bag.no)[0], [2.5, 0, 4]);
  assert.equal(turSay(r.model, "kiris"), 2);
  const t = M.caprazUret(cerceve(), GOZ, "dismerkez-tek", { kesit: "HEA160", e: 0.8 });
  yakin(M.uzunluk(t.model, t.bag_kirisi), 0.8);
  yakin(uclar(t.model, t.caprazlar[0])[1], [5.2, 0, 4]);
  assert.ok(t.uyarilar.some(function (u) { return /1,6·Mp\/Vp/.test(u); }));
  assert.throws(function () { M.caprazUret(cerceve(), GOZ, "dismerkez-tek", { e: 7 }); }, M.ModelHatasi);
  // silinince bağ kirişi türü geri gelir ve kiriş yeniden birleşir
  const s = M.uretecSil(r.model, r.uretec);
  assert.deepEqual(s.model.cubuklar, cerceve().cubuklar);
  assert.deepEqual(s.model.dugumler, cerceve().dugumler);
});

test("caprazUret diz: köşeden a mesafesinde", function () {
  const r = M.caprazUret(cerceve(), GOZ, "diz", { kesit: "L60", a: 0.8 });
  assert.equal(r.caprazlar.length, 2);
  const u = uclar(r.model, r.caprazlar[0]);
  yakin(u[0], [0, 0, 3.2]); yakin(u[1], [0.8, 0, 4]);
  assert.equal(r.model.cubuklar.length, 3 + 4 + 2);
});

test("uretecGuncelle: eski üretim temizlenir, bölünen kiriş geri birleşir", function () {
  const m = cerceve();
  const x = M.caprazUret(m, GOZ, "X", { kesit: "L80" });
  const v = M.uretecGuncelle(x.model, 1, { tip: "ters-V" });
  assert.equal(turSay(v.model, "capraz"), 2); assert.equal(turSay(v.model, "kiris"), 2);
  assert.ok(v.model.cubuklar.filter(function (c) { return c.tur === "capraz"; }).every(function (c) { return M.yerelEksenler(v.model, c.no) && uclar(v.model, c.no)[1][0] === 3; }));
  assert.equal(v.model.uretecler.length, 1); assert.equal(v.model.uretecler[0].tip, "ters-V");
  const g = M.uretecGuncelle(v.model, 1, { tip: "X", secenek: { kesit: "L100" } });
  assert.equal(turSay(g.model, "kiris"), 1);
  assert.deepEqual(cubuk(g.model, 3), m.cubuklar[2]);
  assert.equal(g.model.dugumler.length, 4, "bölme düğümü silinir");
  assert.ok(g.model.cubuklar.filter(function (c) { return c.tur === "capraz"; }).every(function (c) { return c.kesit === "L100"; }));
  const s = M.uretecSil(g.model, 1);
  assert.deepEqual(s.model.cubuklar, m.cubuklar);
  assert.deepEqual(s.model.uretecler, []);
});

// ---------------------------------------------------------------------------- makas
test("makasUret: çubuk sayısı formülleri", function () {
  const p = function (tip, n, ek) { return M.makasUret({}, Object.assign({ tip: tip, bas: [0, 0, 0], son: [12, 0, 0], yukseklik: 1.5, goz: n, kesitler: { ust: "U", alt: "A", dikme: "D", diyagonal: "G" } }, ek || {})); };
  for (const n of [2, 4, 6, 8]) {
    assert.equal(p("pratt", n).model.cubuklar.length, 4 * n + 1, "Pratt " + n);
    assert.equal(p("howe", n).model.cubuklar.length, 4 * n + 1, "Howe " + n);
    assert.equal(p("warren", n).model.cubuklar.length, 4 * n - 1, "Warren " + n);
    assert.equal(p("warren-dikmeli", n).model.cubuklar.length, 4 * n + 1, "dikmeli Warren " + n);
    assert.equal(p("k", n).model.cubuklar.length, 6 * n, "K " + n);
    assert.equal(p("besik-pratt", n, { yukseklik: 2 }).model.cubuklar.length, 4 * n - 3, "beşik Pratt " + n);
    assert.equal(p("besik-howe", n, { yukseklik: 2, uc_yukseklik: 0.5 }).model.cubuklar.length, 4 * n + 1, "uçta yükseklikli beşik Howe " + n);
  }
  const pr = p("pratt", 6);
  assert.deepEqual(pr.sayilar, { "makas-ust": 6, "makas-alt": 6, "makas-dikme": 7, "makas-diyagonal": 6 });
  assert.equal(pr.model.dugumler.length, 14);
  assert.equal(p("fink", 0, { yukseklik: 3 }).model.cubuklar.length, 11);
  assert.throws(function () { p("pratt", 5); }, M.ModelHatasi);
  assert.throws(function () { p("kule", 4); }, M.ModelHatasi);
});

test("makasUret: geometri, mafsallı gövde, sürekli başlık, Pratt/Howe diyagonal yönü", function () {
  const r = M.makasUret({}, { tip: "pratt", bas: [0, 2, 5], son: [12, 2, 5], yukseklik: 1.5, goz: 6, kesitler: {} });
  for (const c of r.model.cubuklar) {
    const u = uclar(r.model, c.no);
    if (c.tur === "makas-ust") { yakin(u[0][2], 6.5); yakin(u[1][2], 6.5); assert.equal(c.serbest, undefined); }
    if (c.tur === "makas-alt") { yakin(u[0][2], 5); assert.equal(c.serbest, undefined); }
    if (c.tur === "makas-dikme" || c.tur === "makas-diyagonal") assert.deepEqual(c.serbest, M.MAFSAL_IKI_UC);
    if (c.tur === "makas-diyagonal") {
      // Pratt: diyagonaller ortaya doğru aşağı iner (üst uç dışta, alt uç içte)
      const alt = u[0][2] < u[1][2] ? u[0] : u[1], ust = u[0][2] < u[1][2] ? u[1] : u[0];
      assert.ok(Math.abs(alt[0] - 6) < Math.abs(ust[0] - 6) + 1e-9, "Pratt diyagonali");
    }
  }
  assert.ok(r.uyarilar.some(function (u) { return /kesit verilmedi/.test(u); }));
  const h = M.makasUret({}, { tip: "howe", bas: [0, 0, 0], son: [12, 0, 0], yukseklik: 1.5, goz: 6 });
  for (const c of h.model.cubuklar.filter(function (c) { return c.tur === "makas-diyagonal"; })) {
    const u = uclar(h.model, c.no), alt = u[0][2] < u[1][2] ? u[0] : u[1], ust = u[0][2] < u[1][2] ? u[1] : u[0];
    assert.ok(Math.abs(ust[0] - 6) < Math.abs(alt[0] - 6), "Howe diyagonali");
  }
  // beşik: mahya kotu ve eğimden mahya
  const b = M.makasUret({}, { tip: "besik-pratt", bas: [0, 0, 0], son: [12, 0, 0], egim: 15, goz: 6 });
  const zmax = Math.max.apply(null, b.model.dugumler.map(function (d) { return d.Z; }));
  yakin(zmax, 6 * Math.tan(15 * Math.PI / 180));
  // Y doğrultusunda açıklık; makas düzlemi Y–Z
  const y = M.makasUret({}, { tip: "warren", bas: [3, 0, 4], son: [3, 10, 4], yukseklik: 1, goz: 5 });
  assert.ok(y.model.dugumler.every(function (d) { return Math.abs(d.X - 3) < 1e-9; }));
});

// ---------------------------------------------------------------------------- beşik çerçeve, aşık
test("besikCerceveUret: mahya kotu, çoğaltma, vute, mesnet", function () {
  const r = M.besikCerceveUret({}, { taban1: [0, 0, 0], taban2: [20, 0, 0], sacak: 6, mahya: 8, kesitler: { kolon: "HEA300", mertek: "IPE360" },
    adet: 3, aralik: 6, vute: { boy: 2, yukseklik: 0.3 } });
  assert.equal(r.cerceveler.length, 3);
  yakin(r.mahya_kotu, 8);
  r.cerceveler.forEach(function (c, f) { yakin(konum(r.model, { dugum: c.mahya }), [10, 6 * f, 8]); });
  assert.equal(turSay(r.model, "kolon"), 6);
  assert.equal(turSay(r.model, "kiris"), 12);
  const vute = r.model.cubuklar.filter(function (c) { return c.grup === "VUTE"; });
  assert.equal(vute.length, 6);
  vute.forEach(function (c) { yakin(M.uzunluk(r.model, c.no), 2); assert.equal(c.kesit, "VUTE-IPE360"); });
  assert.equal(r.model.kesitler["VUTE-IPE360"].tip, "vute");
  assert.equal(r.model.mesnetler.length, 6);
  assert.equal(r.model.mesnetler[0].rx, false);
  yakin(r.egim, Math.atan2(2, 10) * 180 / Math.PI);
  const e = M.besikCerceveUret({}, { taban1: [0, 0, 0], taban2: [20, 0, 0], sacak: 6, egim: 10, mesnet: "ankastre" });
  yakin(e.mahya_kotu, 6 + 10 * Math.tan(10 * Math.PI / 180));
  assert.equal(e.model.mesnetler[0].rx, true);
  // Y doğrultusunda açıklıkta kolon güçlü ekseni çerçeve düzleminde (aci = 90)
  const y = M.besikCerceveUret({}, { taban1: [0, 0, 0], taban2: [0, 16, 0], sacak: 5, mahya: 7, kesitler: { kolon: "HEA", mertek: "IPE" } });
  const kol = y.model.cubuklar.find(function (c) { return c.tur === "kolon"; });
  yakin(Math.abs(M.yerelEksenler(y.model, kol.no).y[1]), 1, 1e-9);
});

test("besikCerceveUret aşık + panel: aşık aralığı, mahyada tek aşık, panel kenarları tam", function () {
  const r = M.besikCerceveUret({}, { taban1: [0, 0, 0], taban2: [20, 0, 0], sacak: 6, mahya: 8, kesitler: { kolon: "HEA300", mertek: "IPE360" },
    adet: 2, aralik: 6, asik: { aralik: 1.8, kesit: "C200" }, panel: { g: 0.2, q: 0.75, kar: true } });
  const Ls = Math.hypot(10, 2), m = Math.ceil(Ls / 1.8);
  assert.equal(turSay(r.model, "asik"), 2 * (m + 1) - 1);
  assert.equal(r.paneller.length, 2);
  for (const p of r.paneller) assert.ok(M.panelKenarCubuklari(r.model, p).every(function (k) { return k.tam; }));
  assert.equal(M.denetle(r.model).uyarilar.filter(function (u) { return u.kod === "panel-kenari"; }).length, 0);
  // uretecGuncelle (aralık değişimi) her şeyi yeniden üretir
  const g = M.uretecGuncelle(r.model, r.uretec, { asik: { aralik: 3 } });
  assert.equal(turSay(g.model, "asik"), 2 * (Math.ceil(Ls / 3) + 1) - 1);
  assert.equal(g.model.uretecler.length, 1);
});

test("asikUret: mertekler üzerinde eşit aralık, aci işareti (y″ = çatı normali)", function () {
  const a = 20 * Math.PI / 180, L = 8, h = L * Math.sin(a), b = L * Math.cos(a);
  const m = {
    dugumler: [{ no: 100001, X: 0, Y: 0, Z: 5 }, { no: 100002, X: b, Y: 0, Z: 5 + h }, { no: 100003, X: 0, Y: 6, Z: 5 }, { no: 100004, X: b, Y: 6, Z: 5 + h },
      { no: 100005, X: 0, Y: 12, Z: 5 }, { no: 100006, X: b, Y: 12, Z: 5 + h }],
    cubuklar: [{ no: 1, i: { dugum: 100002 }, j: { dugum: 100001 }, tur: "kiris", kesit: "IPE" }, { no: 2, i: { dugum: 100003 }, j: { dugum: 100004 }, tur: "kiris", kesit: "IPE" },
      { no: 3, i: { dugum: 100005 }, j: { dugum: 100006 }, tur: "kiris", kesit: "IPE" }],
  };
  const r = M.asikUret(m, [3, 1, 2], 1.5, "C160");
  assert.equal(r.bolum, Math.ceil(8 / 1.5));
  yakin(r.aralik_gercek, 8 / 6);
  assert.equal(r.asiklar.length, 2 * 7);
  assert.equal(turSay(r.model, "kiris"), 3 * 6, "mertekler aşık noktalarında bölünür");
  const n = [-Math.sin(a), 0, Math.cos(a)];
  for (const no of r.asiklar) {
    const c = cubuk(r.model, no);
    assert.equal(c.tur, "asik"); assert.deepEqual(c.serbest, M.MAFSAL_IKI_UC);
    yakin(c.aci, -20, 1e-6);
    yakin(M.yerelEksenler(r.model, no).y, n, 1e-9);
  }
  const zs = [...new Set(r.asiklar.map(function (no) { return Math.round(uclar(r.model, no)[0][2] * 1e6) / 1e6; }))].sort(function (x, y) { return x - y; });
  for (let k = 1; k < zs.length; k++) yakin(zs[k] - zs[k - 1], (8 / 6) * Math.sin(a), 1e-6);
  // panel hedefli
  const p = M.panelOlustur(m, [{ dugum: 100001 }, { dugum: 100005 }, { dugum: 100006 }, { dugum: 100002 }], { tur: "cati" });
  const rp = M.asikUret(p.model, { panel: p.no }, 2, "C160");
  assert.equal(rp.asiklar.length, 5);
  for (const no of rp.asiklar) yakin(M.yerelEksenler(rp.model, no).y, n, 1e-9);
  // silince mertekler geri birleşir
  const s = M.uretecSil(r.model, r.uretec);
  assert.deepEqual(s.model.cubuklar, m.cubuklar);
});

// ---------------------------------------------------------------------------- kren yolu, cephe
test("krenYoluUret: kolonlar kotta bölünür, konsol + kren kirişleri + kren kaydı; güncelleme temizler", function () {
  const m = { dugumler: [], cubuklar: [] };
  let model = m;
  for (const x of [0, 6, 12]) for (const y of [0, 20]) model = M.cubukCiz(model, [x, y, 0], [x, y, 9], { tur: "kolon", kesit: "HEB" }).model;
  const r = M.krenYoluUret(model, [[1, 3, 5], [2, 4, 6]], 7, 0.5, { kiris: "HEB300", konsol: "HEB200" }, { tekerlek: { P_maks: 80, P_min: 25, H_yanal: 8, H_fren: 6, aralik: 3.5, adet: 2 } });
  assert.equal(turSay(r.model, "kolon"), 12);
  assert.equal(r.konsollar.length, 6); assert.equal(r.kirisler.length, 4);
  r.konsollar.forEach(function (no) { yakin(M.uzunluk(r.model, no), 0.5); });
  const k1 = uclar(r.model, r.model.kren[0].yol[0]);
  yakin(k1[0], [0, 0.5, 7]); yakin(k1[1], [6, 0.5, 7]);
  const k2 = uclar(r.model, r.model.kren[1].yol[0]);
  yakin(k2[0][1], 19.5);
  assert.equal(r.model.kren.length, 2); assert.equal(r.model.kren[0].dinamik, 1.25);
  assert.deepEqual(cubuk(r.model, r.model.kren[0].yol[0]).serbest, M.MAFSAL_IKI_UC);
  const g = M.uretecGuncelle(r.model, r.uretec, { kot: 6 });
  assert.equal(turSay(g.model, "kolon"), 12); assert.equal(g.model.kren.length, 2);
  yakin(uclar(g.model, g.model.kren[0].yol[0])[0][2], 6);
  const s = M.uretecSil(g.model, r.uretec);
  assert.deepEqual(s.model.cubuklar, model.cubuklar);
  assert.deepEqual(s.model.kren, []);
});

test("cepheKirisleriUret: kuşaklar kolonları böler, aci duvar normaline", function () {
  let model = {};
  for (const x of [0, 6, 12]) model = M.cubukCiz(model, [x, 0, 0], [x, 0, 6], { tur: "kolon" }).model;
  const r = M.cepheKirisleriUret(model, { kolonlar: [3, 1, 2], aralik: 2, kesit: "C120" });
  assert.deepEqual(r.kotlar, [2, 4]);
  assert.equal(r.kusaklar.length, 4);
  for (const no of r.kusaklar) yakin(Math.abs(M.yerelEksenler(r.model, no).y[1]), 1, 1e-9);
  assert.equal(turSay(r.model, "kolon"), 9);
});

// ---------------------------------------------------------------------------- genelleştir
test("genellestir: aks–kat modeli çubuk/panel/düğüm kayıtlarına", function () {
  const a = aksKat();
  const r = M.genellestir(a);
  const g = r.model;
  assert.equal(g.surum, 3);
  assert.deepEqual([g.kolonlar.length, g.kirisler.length, g.dosemeler.length], [0, 0, 0]);
  assert.deepEqual(r.silinen.kolonlar.length, 12); assert.deepEqual(r.silinen.kirisler.length, 10); assert.deepEqual(r.silinen.dosemeler.length, 4);
  // 12 kolon + kat başına (A1→C1: 2 parça, C2→A2: 2 parça, 3 Y kirişi) = 12 + 2·7
  assert.equal(g.cubuklar.length, 26);
  assert.equal(g.paneller.length, 4);
  assert.equal(g.dugumler.length, 18);
  // numara kuralı 1000·kat + 20·ix + iy + 1 (akslar konuma göre sıralı: A=0, B=1, C=2)
  for (const d of g.dugumler) {
    const ix = ["A", "B", "C"].indexOf(d.aks[0]), iy = ["1", "2"].indexOf(d.aks[1]);
    assert.equal(d.no, 1000 * d.kat + 20 * ix + iy + 1);
    yakin(d.X, [0, 5, 9][ix]); yakin(d.Y, [0, 4][iy]); yakin(d.Z, [0, 3, 6][d.kat]);
  }
  const k1 = g.cubuklar.filter(function (c) { return c.kaynak.aks_kat === "kolon" && c.kaynak.no === 1; })[0];
  assert.deepEqual(k1.i, { aks: ["A", "1"], kat: 0 }); assert.deepEqual(k1.j, { aks: ["A", "1"], kat: 1 });
  assert.equal(k1.aci, 0); assert.equal(g.cubuklar.find(function (c) { return c.kaynak.aks_kat === "kolon" && c.kaynak.no === 2; }).aci, 90);
  const kp = g.cubuklar.filter(function (c) { return c.kaynak.aks_kat === "kiris" && c.kaynak.no === 2; });
  assert.equal(kp.length, 2);
  assert.deepEqual(kp[0].i, { aks: ["A", "2"], kat: 1 }, "kiriş küçük akstan büyüğe");
  assert.equal(g.cubuklar.find(function (c) { return c.kaynak.aks_kat === "kiris" && c.kaynak.no === 1; }).duvar, "tugla19");
  // döşeme → panel: köşe sırası, dağıtım, kar yalnız en üst katta
  const p1 = g.paneller.find(function (p) { return p.no === 1; }), p2 = g.paneller.find(function (p) { return p.no === 2; });
  assert.deepEqual(p1.kose, [{ aks: ["A", "1"], kat: 1 }, { aks: ["B", "1"], kat: 1 }, { aks: ["B", "2"], kat: 1 }, { aks: ["A", "2"], kat: 1 }]);
  assert.equal(p1.dagitim, "iki"); assert.equal(p2.dagitim, "tek-13"); assert.equal(p1.kalinlik, 0.14); assert.equal(p1.g, 1.5);
  assert.equal(p2.q, 3.5); assert.equal(p1.q, undefined); assert.equal(p1.kar, false);
  assert.equal(g.paneller.find(function (p) { return p.kat === 2; }).kar, true);
  // yükler
  const ky = g.ek_yukler.filter(function (y) { return y.tur === "cubuk"; });
  assert.equal(ky.length, 2); ky.forEach(function (y) { assert.equal(y.q1, -2); assert.equal(y.yon, "Z"); });
  assert.deepEqual(g.ek_yukler.find(function (y) { return y.tur === "dugum"; }).dugum, { aks: ["B", "2"], kat: 2 });
  assert.deepEqual(g.ek_yukler.find(function (y) { return y.tur === "panel"; }), { tur: "panel", panel: 2, g: 0.5, q: 0 });
  // panel kenarları ve denetim temiz
  for (const p of g.paneller) assert.ok(M.panelKenarCubuklari(g, p.no).every(function (k) { return k.tam; }));
  const d = M.denetle(g);
  assert.deepEqual(d.uyarilar, []);
  // ikinci kez genelleştirmek değiştirmez
  const r2 = M.genellestir(g);
  assert.deepEqual(r2.model, g);
});

// ---------------------------------------------------------------------------- denetle
test("denetle: yüzen düğüm, sıfır boy, çakışan çubuk, panel kenarı, mesnetsiz, mafsallı düğüm", function () {
  const m = {
    dugumler: [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 4, Y: 0, Z: 0 }, { no: 100003, X: 4, Y: 0, Z: 0.0002 }, { no: 100004, X: 9, Y: 9, Z: 9 },
      { no: 100005, X: 2, Y: 0, Z: 0 }, { no: 100006, X: 4, Y: 3, Z: 0 }],
    cubuklar: [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 } }, { no: 2, i: { dugum: 100002 }, j: { dugum: 100003 } },
      { no: 3, i: { dugum: 100005 }, j: { dugum: 100002 } }, { no: 4, i: { dugum: 100002 }, j: { dugum: 100006 }, serbest: { i: ["My", "Mz"] } }],
    paneller: [{ no: 1, kose: [{ dugum: 100001 }, { dugum: 100002 }, { dugum: 100006 }] }],
  };
  const d = M.denetle(m);
  const kod = new Set(d.uyarilar.map(function (u) { return u.kod; }));
  for (const k of ["yuzen-dugum", "sifir-boy", "cakisan-cubuk", "panel-kenari", "mesnetsiz"]) assert.ok(kod.has(k), k);
  assert.equal(d.gecerli, false);
  const f = M.serbestlikAta(cerceve(), [3], M.MAFSAL_IKI_UC).model;
  f.cubuklar[0].serbest = { j: ["My", "Mz"] };
  const df = M.denetle(f);
  assert.deepEqual(df.uyarilar.map(function (u) { return u.kod; }), ["mafsalli-dugum"]);
  assert.equal(df.uyarilar[0].dugum, 100004);
  assert.deepEqual(M.denetle(cerceve()).uyarilar, []);
  // bağsız parça
  const b = cerceve(); b.dugumler.push({ no: 100009, X: 20, Y: 0, Z: 0 }, { no: 100010, X: 22, Y: 0, Z: 0 });
  b.cubuklar.push({ no: 9, i: { dugum: 100009 }, j: { dugum: 100010 } });
  assert.ok(M.denetle(b).uyarilar.some(function (u) { return u.kod === "bagsiz-parca"; }));
});

// ---------------------------------------------------------------------------- saflık
test("saflık: hiçbir işlem girdi modelini değiştirmez", function () {
  const ornekler = [
    [cerceve(true), function (m) { return M.caprazUret(m, GOZ, "dismerkez-ters-V", { e: 1, kesit: "L" }); }],
    [cerceve(true), function (m) { return M.caprazUret(m, GOZ, "K", { kesit: "L" }); }],
    [cerceve(), function (m) { return M.bol(m, 3, { parca: 4 }); }],
    [cerceve(), function (m) { return M.kesisimlerdeBol(m, [1, 2, 3]); }],
    [cerceve(), function (m) { return M.duzlemleBol(m, [1, 2], { Z: 1 }); }],
    [cerceve(), function (m) { return M.dugumTasi(m, 100003, 6, 0, 5); }],
    [cerceve(), function (m) { return M.dugumleriBirlestir(m, 10); }],
    [cerceve(), function (m) { return M.dogrusalDizi(m, [1, 2, 3], 0, 5, 0, 3); }],
    [cerceve(), function (m) { return M.ayna(m, [1, 2, 3], { Y: 2 }); }],
    [cerceve(), function (m) { return M.dondur(m, [3], "Z", 45); }],
    [cerceve(), function (m) { return M.cubukSil(m, [3]); }],
    [cerceve(), function (m) { return M.dugumSil(m, [100003]); }],
    [cerceve(), function (m) { return M.serbestlikAta(m, [3], M.KAFES_CUBUGU); }],
    [cerceve(true), function (m) { return M.panelOlustur(m, GOZ); }],
    [cerceve(), function (m) { return M.makasUret(m, { tip: "pratt", bas: { dugum: 100004 }, son: { dugum: 100003 }, yukseklik: 1, goz: 4 }); }],
    [cerceve(), function (m) { return M.besikCerceveUret(m, { taban1: { dugum: 100001 }, taban2: { dugum: 100002 }, sacak: 3, mahya: 4, adet: 2, aralik: 5, asik: { aralik: 1 } }); }],
    [aksKat(), function (m) { return M.genellestir(m); }],
    [aksKat(), function (m) { return M.dugumTasi(m, { aks: ["B", "2"], kat: 1 }, 5, 4.5, 3); }],
    [aksKat(), function (m) { return M.caprazUret(m, [{ aks: ["A", "1"], kat: 0 }, { aks: ["B", "1"], kat: 0 }, { aks: ["B", "1"], kat: 1 }, { aks: ["A", "1"], kat: 1 }], "ters-V", { kesit: "L" }); }],
  ];
  for (const [m, f] of ornekler) {
    const once = structuredClone(m);
    const r = f(m);
    assert.deepEqual(m, once);
    assert.ok(r.model !== m);
    assert.ok(r.eklenen && r.silinen && Array.isArray(r.uyarilar));
    // sonuç modeli de ikinci işlemle değişmez (sonuç girdisi de saf)
    const once2 = structuredClone(r.model);
    M.denetle(r.model); M.genellestir(r.model);
    assert.deepEqual(r.model, once2);
  }
});

test("aks–kat modelinde çapraz: önce genelleştirilir, kiriş ortadan bölünür", function () {
  const r = M.caprazUret(aksKat(), [{ aks: ["A", "1"], kat: 0 }, { aks: ["B", "1"], kat: 0 }, { aks: ["B", "1"], kat: 1 }, { aks: ["A", "1"], kat: 1 }], "ters-V", { kesit: "L" });
  assert.equal(r.model.kirisler.length, 0);
  assert.equal(r.model.cubuklar.length, 26 + 1 + 2);
  for (const no of r.caprazlar) yakin(uclar(r.model, no)[1], [2.5, 0, 3]);
  // kiriş yükü bölünen parçalara geçti (A1→B1 parçası iki parçaya)
  const ky = r.model.ek_yukler.filter(function (y) { return y.tur === "cubuk"; });
  assert.equal(ky.length, 3);
});
