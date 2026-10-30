/* docs/olcum.js birim testleri — node'un yerleşik test koşucusu (bağımlılık yok).
   Çalıştırma: node --test testler/js/olcum.test.js */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const O = require(path.join(__dirname, "..", "..", "docs", "olcum.js"));

function yakin(a, b, tol, m) {
  tol = tol == null ? 1e-9 : tol;
  if (Array.isArray(a)) { assert.equal(a.length, b.length, m); a.forEach(function (x, i) { yakin(x, b[i], tol, m); }); return; }
  assert.ok(Math.abs(a - b) <= tol, (m || "") + ` beklenen ${b}, bulunan ${a}`);
}

/** Aks–kat binası: A–B–C (0, 5, 9) × 1–2 (0, 4), katlar 0/3/6; iki kat kolon, kirişler, iki döşeme. */
function aksKat() {
  const kol = [];
  let n = 0;
  for (const k of [1, 2]) for (const x of ["A", "B", "C"]) for (const y of ["1", "2"]) kol.push({ no: ++n, aks: [x, y], kat: k, kesit: "S40x40", yon: "x" });
  return {
    tur: "bina", surum: 1,
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 5 }, { ad: "C", konum: 9 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }] },
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3 }, { no: 2, ad: "Çatı", kot: 6 }],
    kolonlar: kol,
    kirisler: [{ no: 1, kat: 1, bas: ["A", "1"], son: ["B", "1"] }, { no: 2, kat: 1, bas: ["B", "1"], son: ["C", "1"] }, { no: 3, kat: 1, bas: ["A", "2"], son: ["C", "2"] }],
    dosemeler: [{ no: 1, kat: 1, kose: [["A", "1"], ["B", "2"]] }],
  };
}
/** §19 aks sistemi: X (A,B,C), Y (1,2), Z (±0.00 kat 0, Saçak kat 1, Mahya serbest), döndürülmüş ek sistem, bölme ve kesişim düğümleri. */
function aks19() {
  return {
    tur: "bina", surum: 3,
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 6 }, { ad: "C", konum: 12 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 5, gorunur: false }],
      z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "Saçak", konum: 6, kat: 1 }, { ad: "Mahya", konum: 7.5 }] },
    aks_sistemleri: [
      { ad: "KANAT", tur: "kartezyen", orijin: [20, 0, 0], aci: 90, x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 4 }], y: [{ ad: "1", konum: 0 }], z: null },
      { ad: "KUBBE", tur: "silindirik", orijin: [0, 30, 1], aci: 0, r: [{ ad: "R1", konum: 5 }], teta: [{ ad: "T1", konum: 0 }, { ad: "T2", konum: 90 }], z: [{ ad: "Z0", konum: 0 }] },
    ],
    dugumler: [
      { no: 100001, tur: "bolme", cubuk_i: { aks: ["A", "1"], z: "Saçak" }, cubuk_j: { aks: ["C", "1"], z: "Saçak" }, oran: 0.25 },
      { no: 100002, tur: "kesisim", a: [{ aks: ["A", "1"], kat: 0 }, { aks: ["B", "1"], z: "Saçak" }], b: [{ aks: ["B", "1"], kat: 0 }, { aks: ["A", "1"], z: "Saçak" }] },
      { no: 100003, tur: "bolme", cubuk_i: { dugum: 100001 }, cubuk_j: { aks: ["C", "1"], z: "Saçak" }, oran: 0.5 },
      { no: 100004, tur: "bolme", cubuk_i: { dugum: 100005 }, cubuk_j: { aks: ["C", "1"], z: "Saçak" }, oran: 0.5 },
      { no: 100005, tur: "bolme", cubuk_i: { dugum: 100004 }, cubuk_j: { aks: ["C", "1"], z: "Saçak" }, oran: 0.5 },
    ],
    cubuklar: [
      { no: 12, i: { aks: ["A", "1"], z: "Saçak" }, j: { aks: ["C", "1"], z: "Saçak" }, tur: "kiris" },
      { no: 13, i: { dugum: 100001 }, j: { aks: ["B", "1"], z: "Mahya" }, tur: "capraz" },
      { no: 14, i: { aks: ["A", "1"], kat: 0 }, j: { aks: ["B", "1"], z: "Saçak" }, tur: "capraz" },
      { no: 15, i: { aks: ["B", "1"], kat: 0 }, j: { aks: ["A", "1"], z: "Saçak" }, tur: "capraz" },
      { no: 16, i: { sistem: "KANAT", aks: ["A", "1"], z: "±0.00" }, j: { sistem: "KANAT", aks: ["B", "1"], z: "Mahya" } },
      { no: 17, i: { X: 50, Y: 0, Z: 0 }, j: { X: 51, Y: 0, Z: 0 } },
    ],
  };
}

test("biçim: ondalık virgül, eksi işareti, −0 yok", function () {
  assert.equal(O.bicim(1.5), "1,500");
  assert.equal(O.bicim(-2.25, 1), "−2,3");
  assert.equal(O.bicim(-0.0001), "0,000");
  assert.equal(O.bicim(NaN), "—");
});

test("uzaklık, açı, alan, kot farkı, koordinat", function () {
  const u = O.uzaklik([0, 0, 0], [3, 4, 12]);
  yakin(u.L, 13); yakin(u.yatay, 5); yakin(u.egim, Math.atan2(12, 5) * 180 / Math.PI); yakin(u.dogrultu, Math.atan2(4, 3) * 180 / Math.PI);
  const a = O.aci([1, 0, 0], [0, 0, 0], [0, 0, 1]);
  yakin(a.aci, 90); yakin(a.tumler, 90);
  assert.equal(a.plan, null);   // ikinci kol düşey: plan açısı yok
  yakin(O.aci([1, 0, 0], [0, 0, 0], [1, 1, 0]).aci, 45);
  assert.throws(function () { O.aci([0, 0, 0], [0, 0, 0], [1, 0, 0]); }, /köşe/);
  const s = O.alan([[0, 0, 0], [6, 0, 0], [6, 4, 0], [0, 4, 0]]);
  yakin(s.alan, 24); yakin(s.cevre, 20); yakin(s.izdusum, 24); yakin(s.merkez, [3, 2, 0]); assert.equal(s.duzlemsel, true);
  const e = O.alan([[0, 0, 0], [4, 0, 0], [4, 0, 3]]);   // düşey üçgen
  yakin(e.alan, 6); yakin(e.izdusum, 0); yakin(e.egim, 90);
  assert.equal(O.alan([[0, 0, 0], [1, 0, 0], [1, 1, 0.2], [0, 1, 0]]).duzlemsel, false);
  const k = O.kotFarki([0, 0, 1], [5, 0, -2]);
  yakin(k.dZ, -3); yakin(k.yatay, 5);
  assert.match(O.ozet(k), /ΔZ = −3,000 m/);
  assert.match(O.ozet(O.koordinat([1, 2, 3])), /X = 1,000, Y = 2,000, Z = 3,000 m/);
  assert.match(O.ozet(u), /^L = 13,000 m/);
  assert.throws(function () { O.uzaklik([0, 0], [1, 1, 1]); }, /Nokta/);
});

test("aks verisi: katlar'dan Z aksları türetilir; akslar.z ve kat eşlemesi", function () {
  const v = O.aksVerisi(aksKat());
  assert.deepEqual(v.sistemler[0].zs.map(function (z) { return z.ad; }), ["Temel", "1. kat", "Çatı"]);
  assert.equal(v.katZ.get(2).k, 6);
  const w = O.aksVerisi(aks19());
  assert.deepEqual(w.sistemler.map(function (s) { return s.ad; }), ["GLOBAL", "KANAT", "KUBBE"]);
  assert.equal(w.katZ.get(1).ad, "Saçak");
  assert.equal(w.katZ.has(2), false);
});

test("aks kesişimleri: her sistemde X × Y × Z, adres ve REF; görünmez akslar dışarıda", function () {
  const b = aks19();
  const l = O.aksKesisimleri(b, { aks: null });
  // GLOBAL: 3 × 1 (2 görünmez) × 3 = 9; KANAT: 2 × 1 × 3 (GLOBAL z) = 6; KUBBE: 1 × 2 × 1 = 2
  assert.equal(l.length, 17);
  assert.equal(O.aksKesisimleri(b, { aks: null, gizli: true }).length, 26);
  const bs = l.find(function (k) { return k.etiket === "B-1 / Saçak"; });
  assert.deepEqual(bs.ref, { aks: ["B", "1"], kat: 1 });
  yakin(bs.P, [6, 0, 6]);
  const bm = l.find(function (k) { return k.etiket === "B-1 / Mahya"; });
  assert.deepEqual(bm.ref, { aks: ["B", "1"], z: "Mahya" });
  const kb = l.find(function (k) { return k.etiket === "KANAT: B-1 / Mahya"; });
  yakin(kb.P, [20, 4, 7.5], 1e-9);                 // 90° döndürülmüş: yerel x → global Y
  assert.deepEqual(kb.ref, { sistem: "KANAT", aks: ["B", "1"], z: "Mahya" });
  const t2 = l.find(function (k) { return k.etiket === "KUBBE: R1-T2 / Z0"; });
  yakin(t2.P, [0, 35, 1], 1e-9);                   // silindirik: r = 5, θ = 90°, orijin z = 1 (+ kendi Z aksı)
});

test("aks kesişimleri: MatrisAks (aks_sistemi.js) varsa ondan alınır", function () {
  const sahte = { kesisimler: function () { return [{ P: [1, 2, 3], etiket: "X-9 / Kren", ref: { aks: ["X", "9"], z: "Kren" } }, { X: 4, Y: 5, Z: 6, adres: "Y" }, null]; } };
  const l = O.aksKesisimleri(aks19(), { aks: sahte });
  assert.equal(l.length, 2);
  assert.equal(l[0].etiket, "X-9 / Kren");
  yakin(l[1].P, [4, 5, 6]);
});

test("geometri: aks–kat düğüm numarası 1000·kat + 20·ix + iy + 1, kolon/kiriş uçları, döşeme köşeleri", function () {
  const g = O.geometri(aksKat(), { aks: null });
  const k1 = O.cubukBul(g, "kolon:1");
  yakin(k1.A, [0, 0, 0]); yakin(k1.B, [0, 0, 3]);
  assert.equal(k1.i, "n1"); assert.equal(k1.j, "n1001");
  const k3 = O.cubukBul(g, "kiris:3");
  yakin(k3.A, [0, 4, 3]); yakin(k3.B, [9, 4, 3]);
  const d = g.dugumler.find(function (n) { return n.no === 2042; });   // kat 2, C (ix 2), 2 (iy 1) → 2000 + 40 + 1 + 1
  yakin(d.P, [9, 4, 6]);
  assert.equal(d.etiket, "C-2 / Çatı");
  assert.equal(g.paneller.length, 1);
  yakin(g.paneller[0].kose, [[0, 0, 3], [5, 0, 3], [5, 4, 3], [0, 4, 3]]);
  assert.equal(g.coz(1021).etiket, "B-1 / 1. kat");
  assert.equal(g.izgaraNo(["C", "2"], 2), 2042);
});

test("geometri §19: Z aksı adıyla REF, ek sistem, bölme/kesişim düğümleri (yinelemeli), döngü güvenli", function () {
  const g = O.geometri(aks19(), { aks: null });
  const b1 = g.dugumler.find(function (n) { return n.no === 100001; });
  yakin(b1.P, [3, 0, 6]);
  assert.equal(b1.tur, "bolme");
  assert.equal(b1.etiket, "bölme: çubuk 12, t=0,25");
  const k2 = g.dugumler.find(function (n) { return n.no === 100002; });
  yakin(k2.P, [3, 0, 3]);
  assert.equal(k2.tur, "kesisim");
  yakin(g.dugumler.find(function (n) { return n.no === 100003; }).P, [7.5, 0, 6]);   // bölmenin bölmesi
  assert.equal(g.dugumler.some(function (n) { return n.no === 100004 || n.no === 100005; }), false);   // döngülü tanım
  yakin(O.cubukBul(g, "cubuk:13").B, [6, 0, 7.5]);
  yakin(O.cubukBul(g, "cubuk:16").B, [20, 4, 7.5]);
  assert.equal(O.cubukBul(g, "cubuk:13").etiket, "Çapraz 13");
  // koordinatlı REF (geriye uyum) okunur ama yakalama düğümü olmaz
  yakin(O.cubukBul(g, "cubuk:17").A, [50, 0, 0]);
  assert.equal(g.dugumler.some(function (n) { return n.tur === "koordinat"; }), false);
  assert.equal(g.coz({ aks: ["Q", "1"], z: "Saçak" }), null);
  assert.equal(g.coz({ sistem: "YOK", aks: ["A", "1"], z: "Saçak" }), null);
});

test("çubuk kesişimleri: ortak uç kesişim sayılmaz", function () {
  const g = O.geometri(aks19(), { aks: null });
  const k = O.kesisimler(g);
  const anah = k.map(function (x) { return x.cubuklar.slice().sort().join("×"); }).sort();
  assert.ok(anah.indexOf("cubuk:14×cubuk:15") >= 0);
  const x = k.find(function (q) { return q.cubuklar.indexOf("cubuk:14") >= 0 && q.cubuklar.indexOf("cubuk:15") >= 0; });
  yakin(x.P, [3, 0, 3], 1e-9);
  assert.equal(O.parcaKesisim([0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]), null);   // paralel
  yakin(O.dogruKesisim([0, 0, 0], [1, 0, 0], [5, -1, 0], [5, 1, 0]), [5, 0, 0]);    // doğru (uzatılmış) kesişimi
});

test("yakalama — çizim kipi: yalnız aks kesişimi, düğüm ve çubuk kesişimi (orta nokta/çubuk üzeri yok)", function () {
  const g = O.geometri(aks19(), { aks: null });
  // kirişin (12) ortası (6, 0, 6) aynı zamanda B-1/Saçak aks kesişimi; düğüm de var → düğüm önce
  const y1 = O.yakala([6.05, 0, 6.02], g, { kip: "cizim" });
  assert.equal(y1.tur, "dugum");
  assert.deepEqual(y1.ref, { aks: ["B", "1"], kat: 1 });
  // C-1/Mahya: düğüm yok, aks kesişimi var
  const y2 = O.yakala([12.1, 0, 7.45], g, { kip: "cizim" });
  assert.equal(y2.tur, "aks");
  assert.deepEqual(y2.ref, { aks: ["C", "1"], z: "Mahya" });
  assert.equal(y2.etiket, "C-1 / Mahya");
  // kirişin üzerindeki serbest bir nokta: çizimde yakalanmaz
  assert.equal(O.yakala([10, 0, 6], g, { kip: "cizim", tol: 0.3 }), null);
  // aynı nokta ölçümde "çubuk üzerinde"
  const y3 = O.yakala([10, 0, 6.1], g, { kip: "olcum", tol: 0.3 });
  assert.equal(y3.tur, "cubuk"); yakin(y3.P, [10, 0, 6]);
  // çapraz kesişimi (14 × 15): kayıtlı kesişim düğümü 100002 var → düğüm
  const y4 = O.yakala([3, 0, 3.05], g, { kip: "cizim" });
  assert.equal(y4.tur, "dugum"); assert.equal(y4.dugum, 100002); assert.deepEqual(y4.ref, { dugum: 100002 });
  // kayıtlı düğümü olmayan çubuk kesişimi: yeni kesişim düğümü kaydı REF'i
  const b = aks19(); b.dugumler = b.dugumler.filter(function (d) { return d.no !== 100002; });
  const y5 = O.yakala([3, 0, 3.05], O.geometri(b, { aks: null }), { kip: "cizim" });
  assert.equal(y5.tur, "kesisim");
  assert.deepEqual(y5.ref, { tur: "kesisim", a: [{ aks: ["A", "1"], kat: 0 }, { aks: ["B", "1"], kat: 1 }], b: [{ aks: ["B", "1"], kat: 0 }, { aks: ["A", "1"], kat: 1 }] });
  // düzlem süzgeci: yalnız Saçak (Z = 6) düzlemi
  assert.equal(O.yakala([3, 0, 3.05], g, { kip: "cizim", duzlem: { Z: 6 } }), null);
  assert.equal(O.yakala([12.1, 0, 7.45], g, { kip: "cizim", aks: false }), null);
});

test("yakalama — ölçüm kipi: orta nokta, dik iz düşüm, ekran toleransı (px)", function () {
  const g = O.geometri(aksKat(), { aks: null });
  const y = O.yakala([2.5, 0.02, 3.01], g, { kip: "olcum" });
  assert.equal(y.tur, "orta"); yakin(y.P, [2.5, 0, 3]);
  const d = O.yakala([2.2, 0, 3.05], g, { kip: "olcum", onceki: [2.2, 0, 0], turler: ["dik"] });
  assert.equal(d.tur, "dik"); yakin(d.P, [2.2, 0, 3]);
  // ekran kipi: 1 m = 50 px, plan bakışı
  const T = { x: function (v) { return 100 + 50 * v; }, y: function (v) { return 500 - 50 * v; } };
  const cv = O.cevirici(T, { fi: 0, psi: 90 });
  const p = cv([5, 4, 3]);
  const e = O.yakala([p[0] + 6, p[1] - 5], g, { cevir: cv, kip: "cizim", duzlem: { Z: 3 } });
  assert.equal(e.tur, "dugum"); yakin(e.P, [5, 4, 3]);
  assert.equal(O.yakala([p[0] + 30, p[1]], g, { cevir: cv, kip: "cizim", duzlem: { Z: 3 } }), null);
});

test("cevirici: Cizim3B ile aynı aksonometri; ekrandan düzleme ters dönüşüm", function () {
  const b = { fi: -32, psi: 22 };
  const q = O.izdusum(2, 3, 4, b);
  const f = -32 * Math.PI / 180, s = 22 * Math.PI / 180, z = -3;
  yakin(q, [2 * Math.cos(f) + z * Math.sin(f), 4 * Math.cos(s) - (-2 * Math.sin(f) + z * Math.cos(f)) * Math.sin(s)], 1e-12);
  const T = { x: function (v) { return 10 + 20 * v; }, y: function (v) { return 300 - 20 * v; } };
  const cv = O.cevirici(T, b);
  const ek = cv([2, 3, 1.5]);
  yakin(O.ekrandanDuzleme(ek[0], ek[1], cv, 1.5), [2, 3, 1.5], 1e-9);
  assert.equal(O.ekrandanDuzleme(0, 0, O.cevirici(T, { fi: 0, psi: 0 }), 0), null);   // ön görünüşte plan düzlemi
});

test("Olcer: uzaklık, açı, alan (ilk noktaya dokununca kapanır), Esc ve geri al, eleman boyu, önizleme", function () {
  const m = new O.Olcer("uzaklik");
  assert.equal(m.nokta([0, 0, 0]), null);
  assert.match(m.ipucu(), /İkinci/);
  const s = m.nokta([3, 4, 0]);
  yakin(s.L, 5);
  assert.equal(m.sonuclar.length, 1);
  m.kipSec("aci");
  m.nokta([1, 0, 0]); m.nokta([0, 0, 0]);
  yakin(m.onizleme([0, 2, 0]).aci, 90);
  yakin(m.nokta([0, 1, 0]).aci, 90);
  m.kipSec("alan");
  [[0, 0, 0], [2, 0, 0], [2, 2, 0]].forEach(function (P) { m.nokta(P); });
  assert.match(m.ipucu(), /Enter/);
  yakin(m.nokta([0, 0, 0]).alan, 2);   // ilk noktaya dokunmak kapatır
  m.nokta([5, 5, 5]);
  assert.equal(m.temizle(), true);      // önce yarım ölçüm
  assert.equal(m.bekleyen.length, 0); assert.equal(m.sonuclar.length, 3);
  m.geriAl();
  assert.equal(m.sonuclar.length, 2);
  const g = O.geometri(aksKat(), { aks: null });
  const b = m.eleman(g, "kiris:3");
  assert.equal(b.tur, "boy"); yakin(b.L, 9); assert.match(O.ozet(b), /^Kiriş 3/);
  assert.equal(m.temizle(true), true);
  assert.equal(m.sonuclar.length, 0);
  assert.equal(m.temizle(true), false);
  assert.throws(function () { O.elemanBoyu(g, "kiris:99"); }, /bulunamadı/);
});

test("SVG: ölçü çizgisi etiketleri, rozet, yakalama işaretleri; metin kaçışlı", function () {
  const cv = function (P) { return [P[0] * 40, -P[2] * 40 + 400]; };
  const m = new O.Olcer("uzaklik");
  m.nokta([0, 0, 0]); m.nokta([5, 0, 0]);
  m.kipSec("kot"); m.nokta([0, 0, 0]); m.nokta([0, 0, 3]);
  m.kipSec("koordinat"); m.nokta([1, 2, 3]);
  const s = m.svg(cv);
  assert.match(s, /class="olcum-katman"/);
  assert.match(s, />5,000 m</);
  assert.match(s, /ΔZ \+3,000 m/);
  assert.match(s, /olcum-rozet/);
  for (const tur of ["dugum", "aks", "kesisim", "orta", "dik", "cubuk"]) {
    const y = O.yakalamaSvg({ tur: tur, P: [1, 0, 1], ad: "<b>" + O.YAKALAMA_ADI[tur] }, cv);
    assert.match(y, new RegExp("olcum-yakala-" + tur));
    assert.ok(y.indexOf("<b>") < 0 && y.indexOf("&lt;b&gt;") > 0);
  }
  const a = O.olcuSvg(O.aci([1, 0, 0], [0, 0, 0], [0, 0, 1]), cv);
  assert.match(a, /90,0°/);
  assert.match(O.olcuSvg(O.alan([[0, 0, 0], [2, 0, 0], [2, 0, 2], [0, 0, 2]]), cv), /4,00 m²/);
});

test("Arac (DOM'suz denetleyici): hareket → yakalama, dokun → sonuç, tuşlar, katmana çizim", function () {
  const g = O.geometri(aksKat(), { aks: null });
  const T = { x: function (v) { return 100 + 50 * v; }, y: function (v) { return 500 - 50 * v; } };
  const cv = O.cevirici(T, { fi: 0, psi: 0 });   // ön görünüş: X sağa, Z yukarı
  const katman = { innerHTML: "" };
  const olaylar = [], ipuclari = [];
  const a = new O.Arac({ geo: function () { return g; }, cevir: cv, katman: katman, kip: "uzaklik",
    degisti: function (arac, s) { olaylar.push(s); }, ipucu: function (m) { ipuclari.push(m); } });
  const p0 = cv([0, 0, 0]), p1 = cv([9, 0, 6]);
  assert.equal(a.hareket([p0[0] + 3, p0[1] - 2]).tur, "dugum");
  assert.match(katman.innerHTML, /olcum-yakala-dugum/);
  assert.equal(a.dokun([p0[0] + 3, p0[1] - 2]), null);
  const s = a.dokun([p1[0] - 2, p1[1] + 3]);
  yakin(s.L, Math.hypot(9, 6));
  assert.match(katman.innerHTML, /10,817 m/);
  assert.equal(olaylar[olaylar.length - 1], s);
  assert.match(ipuclari[ipuclari.length - 1], /^L = 10,817/);
  assert.equal(a.dokun([5000, 5000]), null);   // boşluk: yakalama yok
  assert.match(ipuclari[ipuclari.length - 1], /Yakalanacak nokta yok/);
  a.kipSec("alan");
  [[0, 0, 0], [5, 0, 0], [5, 0, 3]].forEach(function (P) { const q = cv(P); a.dokun([q[0], q[1]]); });
  const al = a.tus("Enter") && a.olcer.sonuclar[a.olcer.sonuclar.length - 1];
  yakin(al.alan, 7.5);
  a.kipSec("boy");
  const q = cv([2.5, 0, 3]);
  const b = a.dokun([q[0] + 1, q[1] + 1]);
  assert.equal(b.tur, "boy"); yakin(b.L, 5);   // kirişin ortasına tek dokunuş: eleman boyu
  assert.equal(a.tus("Backspace"), true);      // son sonucu geri al
  assert.equal(a.olcer.sonuclar.length, 2);
  a.dokun([q[0] + 1, q[1] + 1]);               // boy kipinde yarım ölçüm yok; yeni eleman boyu
  const p2 = cv([0, 0, 3]); a.kipSec("uzaklik"); a.dokun([p2[0], p2[1]]);
  assert.equal(a.tus("Escape"), true);         // Esc 1: yarım ölçüm silinir, sonuçlar kalır
  assert.equal(a.olcer.bekleyen.length, 0); assert.equal(a.olcer.sonuclar.length, 3);
  assert.equal(a.tus("Escape"), true);         // Esc 2: bütün sonuçlar
  assert.equal(a.olcer.sonuclar.length, 0);
  assert.equal(a.tus("Escape"), false);
  assert.match(a.tsv(), /^No\tTür\tSonuç$/);
});

test("Arac escSonuclariKorur (bina sayfası): Esc yalnız yarım ölçümü siler, tamamlanan ölçüler kalır; temizle() hepsini siler", function () {
  const g = O.geometri(aksKat(), { aks: null });
  const T = { x: function (v) { return 100 + 50 * v; }, y: function (v) { return 500 - 50 * v; } };
  const cv = O.cevirici(T, { fi: 0, psi: 0 });
  const katman = { innerHTML: "" };
  const a = new O.Arac({ geo: function () { return g; }, cevir: cv, katman: katman, kip: "uzaklik", escSonuclariKorur: true });
  const p0 = cv([0, 0, 0]), p1 = cv([9, 0, 6]);
  a.dokun([p0[0], p0[1]]);
  a.dokun([p1[0], p1[1]]);
  assert.equal(a.olcer.sonuclar.length, 1);
  assert.equal(a.olcer.bekleyen.length, 0);
  assert.equal(a.tus("Escape"), false);          // yarım ölçüm yok: işlenmez (sayfa Esc'i kipten çıkar)
  assert.equal(a.olcer.sonuclar.length, 1);      // tamamlanan ölçü kalır
  assert.match(katman.innerHTML, /10,817 m/);
  assert.equal(a.tus("Escape"), false);          // ikinci Esc de sonuçları silmez
  assert.equal(a.olcer.sonuclar.length, 1);
  a.dokun([p0[0], p0[1]]);                       // yarım ölçüm
  assert.equal(a.olcer.bekleyen.length, 1);
  assert.equal(a.tus("Escape"), true);           // yalnız yarım ölçüm silinir
  assert.equal(a.olcer.bekleyen.length, 0);
  assert.equal(a.olcer.sonuclar.length, 1);
  a.temizle();                                   // "Ölçüleri temizle"
  assert.equal(a.olcer.sonuclar.length, 0);
  assert.doesNotMatch(katman.innerHTML, /10,817 m/);
});

test("TSV: başlık ve satırlar", function () {
  const t = O.tsv([O.uzaklik([0, 0, 0], [1, 0, 0]), O.kotFarki([0, 0, 0], [0, 0, 2])]);
  const s = t.split("\n");
  assert.equal(s[0], "No\tTür\tSonuç");
  assert.match(s[1], /^1\tUzaklık\tL = 1,000 m/);
  assert.match(s[2], /^2\tKot farkı\tΔZ = \+2,000 m/);
});
