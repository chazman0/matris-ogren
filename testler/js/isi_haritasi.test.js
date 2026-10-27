/* docs/isi_haritasi.js saf yardımcılarının birim testleri — node'un yerleşik test koşucusu (bağımlılık yok).
   Çalıştırma: node --test testler/js/isi_haritasi.test.js */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const M = require(path.join(__dirname, "..", "..", "docs", "isi_haritasi.js"));

function yakin(a, b, tol, mesaj) {
  tol = tol == null ? 1e-9 : tol;
  if (Array.isArray(a) || ArrayBuffer.isView(a)) {
    assert.equal(a.length, b.length, mesaj);
    for (let i = 0; i < a.length; i++) yakin(a[i], b[i], tol, mesaj);
    return;
  }
  assert.ok(Math.abs(a - b) <= tol * Math.max(1, Math.abs(b)), (mesaj || "") + ` beklenen ${b}, bulunan ${a}`);
}
function alanVeMerkez(p) {
  let A = 0, cy = 0, cz = 0;
  for (let i = 0; i < p.length; i++) {
    const a = p[i], b = p[(i + 1) % p.length], c = a[0] * b[1] - b[0] * a[1];
    A += c; cy += (a[0] + b[0]) * c; cz += (a[1] + b[1]) * c;
  }
  A /= 2;
  return { A: A, y: cy / (6 * A), z: cz / (6 * A) };
}
function ucgenAlani(p, t) {
  let s = 0;
  for (let i = 0; i < t.length; i += 3) {
    const a = p[t[i]], b = p[t[i + 1]], c = p[t[i + 2]];
    s += Math.abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2;
  }
  return s;
}

/** X yönünde kiriş (0,0,3) → (5,0,3); y′ = +Z, z′ = −Y; 25×50 dikdörtgen; 6 istasyon. */
function kiris(ek) {
  const b = 0.25, h = 0.5, xs = [0, 1, 2, 3, 4, 5];
  const Mz = xs.map(function (x) { return 10 * x * (5 - x) / 2 - 20; });
  return Object.assign({
    no: 7, tur: "kiris", bina_no: 3, kat: 1, adres: "K-A1→B1/k1", i: [0, 0, 3], j: [5, 0, 3], L: 5,
    yerel: { x: [1, 0, 0], y: [0, 0, 1], z: [0, -1, 0] },
    kesit: { sekil: "dikdortgen", eksen: "y", dy: h, dz: b, h: h, b: b, A: b * h, Iz: b * h * h * h / 12, Iy: h * b * b * b / 12, Wz: b * h * h / 6, Wy: h * b * b / 6 },
    x: xs, u: xs.map(function (x) { return [0, 0, -0.001 * x * (5 - x) / 6.25]; }),
    u_abs: xs.map(function (x) { return 0.001 * x * (5 - x) / 6.25; }),
    N: xs.map(function () { return -12; }), Vy: xs.map(function (x) { return 25 - 10 * x; }), Vz: xs.map(function () { return 0; }),
    T: xs.map(function () { return 0; }), My: xs.map(function () { return 3; }), Mz: Mz,
    sigma_max: xs.map(function () { return 1; }), sigma_min: xs.map(function () { return -1; }), von_mises: xs.map(function () { return 1; }),
    tau_max: xs.map(function () { return 0.2; }), kullanim: null,
  }, ek || {});
}

test("sayı biçimi: ondalık virgül ve gerçek eksi", function () {
  assert.equal(M.fmt(-12.3456, 4), "−12,35");
  assert.equal(M.fmt(0), "0");
  assert.equal(M.fmt(null), "—");
  assert.equal(M.fmt(1.5e-5, 3), "1,50e−5");
});

test("renk ölçeği: 9 bant mavi → kırmızı, sürekli uçlar, iki yönlü sıfır ortada", function () {
  assert.deepEqual(M.renkAl(0, "klasik", true), [0, 0, 255]);
  assert.deepEqual(M.renkAl(1, "klasik", true), [255, 0, 0]);
  assert.deepEqual(M.renkAl(0.5, "klasik", true), [0, 255, 0]);              // 5. bant yeşil
  assert.deepEqual(M.renkAl(1 / 9 - 1e-9, "klasik", true), M.PALET.klasik[0]);
  assert.deepEqual(M.renkAl(1 / 9 + 1e-9, "klasik", true), M.PALET.klasik[1]);
  assert.deepEqual(M.renkAl(0, "klasik", false), [0, 0, 255]);
  assert.deepEqual(M.renkAl(1, "klasik", false), [255, 0, 0]);
  assert.deepEqual(M.renkAl(-3, "klasik", true), [0, 0, 255]);               // kırpılır
  assert.equal(M.renkHex([255, 16, 0]), "#ff1000");
  assert.deepEqual(M.aralikBelirle(-3, 7, true), [-7, 7]);
  assert.deepEqual(M.aralikBelirle(-3, 7, false), [-3, 7]);
  const d = M.aralikBelirle(5, 5, false);
  assert.ok(d[0] < 5 && d[1] > 5);
  const s = M.lejantSinirlari(0, 9);
  assert.equal(s.length, 10);
  yakin(s, [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]);
  assert.equal(M.dokuVerisi("klasik", true).length, 9 * 4);
  assert.equal(M.dokuVerisi("iki", false).length, 256 * 4);
  assert.equal(M.degerRengi(M.GECERSIZ, 0, 1, "klasik", true), null);
  // iki yönlü paletin ortası nötr gri (renk tonu yok)
  const orta = M.renkAl(0.5, "iki", true);
  assert.ok(Math.max.apply(null, orta) - Math.min.apply(null, orta) < 12);
});

test("renk kimliği: eleman no ↔ RGB gidiş-dönüş", function () {
  for (const id of [1, 255, 256, 65535, 70000, 0x700003, 0x7f0000]) {
    const c = M.kimlikRenk(id);
    assert.equal(M.renkKimlik(c[0], c[1], c[2]), id);
  }
});

test("kesit anahatları: alan, ağırlık merkezi ve eksen yönü", function () {
  const r = M.kesitAnahat({ sekil: "dikdortgen", dy: 0.5, dz: 0.3 });
  yakin(alanVeMerkez(r.parcalar[0].dis).A, 0.15);
  const h = 0.3, b = 0.15, tw = 0.0071, tf = 0.0107;
  const I = M.kesitAnahat({ sekil: "I", eksen: "y", h: h, b: b, tw: tw, tf: tf, dy: h, dz: b });
  const am = alanVeMerkez(I.parcalar[0].dis);
  yakin(am.A, 2 * b * tf + (h - 2 * tf) * tw, 1e-9);
  yakin([am.y, am.z], [0, 0], 1e-12);
  // derinlik y′ boyunca: y aralığı h, z aralığı b; eksen "z" iken takas
  const ys = I.parcalar[0].dis.map(function (q) { return q[0]; }), zs = I.parcalar[0].dis.map(function (q) { return q[1]; });
  yakin([Math.max.apply(null, ys) - Math.min.apply(null, ys), Math.max.apply(null, zs) - Math.min.apply(null, zs)], [h, b]);
  const Iz = M.kesitAnahat({ sekil: "I", eksen: "z", h: h, b: b, tw: tw, tf: tf, dy: b, dz: h });
  const zs2 = Iz.parcalar[0].dis.map(function (q) { return q[1]; });
  yakin(Math.max.apply(null, zs2) - Math.min.apply(null, zs2), h);
  // L, U, 2L ağırlık merkezi başlangıçta
  for (const k of [{ sekil: "L", b: 0.1, t: 0.01, dy: 0.1, dz: 0.1 }, { sekil: "U", h: 0.2, b: 0.075, tw: 0.0085, tf: 0.0115, dy: 0.2, dz: 0.075 }]) {
    const c = alanVeMerkez(M.kesitAnahat(k).parcalar[0].dis);
    yakin([c.y, c.z], [0, 0], 1e-9, k.sekil);
  }
  const L2 = M.kesitAnahat({ sekil: "2L", b: 0.1, t: 0.01, s: 0.01, dy: 0.1, dz: 0.21 });
  assert.equal(L2.parcalar.length, 2);
  const a1 = alanVeMerkez(L2.parcalar[0].dis), a2 = alanVeMerkez(L2.parcalar[1].dis);
  yakin((a1.A * a1.y + a2.A * a2.y) / (a1.A + a2.A), 0, 1e-9);
  yakin((a1.A * a1.z + a2.A * a2.z) / (a1.A + a2.A), 0, 1e-9);
  // kutu ve boru: iç halka aynı sayıda köşe
  const k = M.kesitAnahat({ sekil: "kutu", h: 0.2, b: 0.1, t: 0.006, dy: 0.2, dz: 0.1 });
  assert.equal(k.parcalar[0].ic.length, k.parcalar[0].dis.length);
  yakin(alanVeMerkez(k.parcalar[0].dis).A - alanVeMerkez(k.parcalar[0].ic).A, 0.2 * 0.1 - 0.188 * 0.088, 1e-9);
  const bo = M.kesitAnahat({ sekil: "boru", D: 0.1683, t: 0.0063 });
  assert.ok(bo.parcalar[0].puruzsuz && bo.parcalar[0].ic.length === bo.parcalar[0].dis.length);
  const t = M.kesitAnahat({ sekil: "I", h: 0.3, b: 0.15 }, true, 0.02);
  assert.equal(t.parcalar[0].dis.length, 6);
  // bütün anahatlar saat yönünün tersine (pozitif alan)
  for (const a of [r, I, Iz, k, L2]) a.parcalar.forEach(function (p) { assert.ok(M.isaretliAlan(p.dis) > 0); });
});

test("üçgenleme: içbükey I ve L çokgeninde toplam alan korunur", function () {
  for (const k of [{ sekil: "I", h: 0.3, b: 0.15, tw: 0.0071, tf: 0.0107, dy: 0.3, dz: 0.15 }, { sekil: "L", b: 0.1, t: 0.01, dy: 0.1, dz: 0.1 },
    { sekil: "U", h: 0.2, b: 0.075, tw: 0.0085, tf: 0.0115, dy: 0.2, dz: 0.075 }]) {
    const p = M.kesitAnahat(k).parcalar[0].dis, t = M.ucgenle(p);
    assert.equal(t.length, 3 * (p.length - 2), k.sekil);
    yakin(ucgenAlani(p, t), M.isaretliAlan(p), 1e-12, k.sekil);
  }
  assert.ok(M.cokgenIcinde([0, 0], [[-1, -1], [1, -1], [1, 1], [-1, 1]]));
  assert.ok(!M.cokgenIcinde([2, 0], [[-1, -1], [1, -1], [1, 1], [-1, 1]]));
});

test("lif gerilmesi işareti: Mz > 0 alt (−y′), My > 0 −z′ lifini çeker; tarafsız eksende σ = 0", function () {
  const k = { A: 0.125, Iy: 0.5 * Math.pow(0.25, 3) / 12, Iz: 0.25 * Math.pow(0.5, 3) / 12 };
  assert.ok(M.lifGerilmesi(k, 0, 0, 10, -0.25, 0) > 0 && M.lifGerilmesi(k, 0, 0, 10, 0.25, 0) < 0);
  assert.ok(M.lifGerilmesi(k, 0, 10, 0, 0, -0.1) > 0 && M.lifGerilmesi(k, 0, 10, 0, 0, 0.1) < 0);
  yakin(M.lifGerilmesi(k, 50, 0, 0, 0.1, 0.1), 50 / 0.125 / 1000);
  const N = -80, My = 6, Mz = 25;
  const te = M.tarafsizEksen(k, N, My, Mz);
  const seg = M.dogruKirp(te, -0.5, 0.5, -0.5, 0.5);
  assert.ok(seg);
  seg.forEach(function (p) { yakin(M.lifGerilmesi(k, N, My, Mz, p[0], p[1]), 0, 1e-9); });
  assert.equal(M.tarafsizEksen(k, 10, 0, 0), null);
  // dikdörtgende en dış lif = N/A + |My|/Wy + |Mz|/Wz
  const an = M.kesitAnahat({ sekil: "dikdortgen", dy: 0.5, dz: 0.25 });
  const u = M.kesitUcLifleri(an, k, N, My, Mz);
  yakin(u.cekme.s, (N / 0.125 + Math.abs(My) / (0.5 * 0.25 * 0.25 / 6) + Math.abs(Mz) / (0.25 * 0.5 * 0.5 / 6)) / 1000, 1e-9);
  assert.ok(u.cekme.y < 0 && u.cekme.z < 0);        // Mz > 0, My > 0: −y′, −z′ köşesi çekmede
  // von Mises lif: √(σ² + 3τ²)
  const e = kiris();
  const s = M.lifDegeri(e, 2, 0.25, 0, false), vm = M.lifDegeri(e, 2, 0.25, 0, true);
  yakin(vm, Math.sqrt(s * s + 3 * 0.2 * 0.2));
});

test("istasyon değerleri: yer değiştirme mm, eksik büyüklük null", function () {
  const e = kiris();
  yakin(M.istasyonDegeri(e, "u", 2), 0.001 * 6 / 6.25 * 1000);
  yakin(M.istasyonDegeri(e, "uZ", 2), -0.001 * 6 / 6.25 * 1000);
  assert.equal(M.istasyonDegeri(e, "kullanim", 1), null);
  yakin(M.istasyonDegeri(e, "Mz", 0), -20);
  const ex = M.ekstremumBul([e, kiris({ no: 8, Mz: [0, 0, 100, 0, 0, 0] })], "Mz", new Uint8Array([1, 0]));
  yakin(ex.max.deger, Math.max.apply(null, e.Mz));
  assert.equal(ex.max.el, 0);
  const ex2 = M.ekstremumBul([e, kiris({ no: 8, Mz: [0, 0, 100, 0, 0, 0] })], "Mz", null);
  assert.equal(ex2.max.el, 1);
  assert.equal(ex2.max.k, 2);
});

test("çubuk ağı: köşe sayısı, konumlar, ötelemeler, kimlik renkleri, seyrek ve bölünmüş halkalar", function () {
  const e = kiris(), els = [e, kiris({ no: 9, i: [5, 0, 3], j: [10, 0, 3] })];
  const ag = M.cubukAgi(els, {});
  const an = ag.anahatlar[0], ns = e.x.length;
  assert.equal(ag.kose, 2 * (an.sayi.kose * ns + 2 * an.sayi.kapakKose));
  assert.equal(an.sayi.kose, 8);                    // dikdörtgen: 4 kenar × 2 (keskin kenar normalleri)
  let mx = 0;
  for (let i = 0; i < ag.I.length; i++) mx = Math.max(mx, ag.I[i]);
  assert.ok(mx < ag.kose);
  for (let v = 0; v < ag.kose; v++) {
    const ei = ag.vEl[v], k = ag.vSt[v], el = els[ei], y = ag.vYZ[2 * v], z = ag.vYZ[2 * v + 1];
    const beklenen = [0, 1, 2].map(function (c) { return el.i[c] + el.x[k] * el.yerel.x[c] + y * el.yerel.y[c] + z * el.yerel.z[c]; });
    yakin(Array.from(ag.P.subarray(3 * v, 3 * v + 3)), beklenen, 1e-6);
    yakin(Array.from(ag.D.subarray(3 * v, 3 * v + 3)), el.u[k], 1e-9);
    assert.equal(M.renkKimlik(ag.K[4 * v], ag.K[4 * v + 1], ag.K[4 * v + 2]), ei + 1);
    assert.ok(Math.abs(y) <= 0.25 + 1e-9 && Math.abs(z) <= 0.125 + 1e-9);
  }
  // eleman başına indis aralıkları ardışık ve tam
  assert.equal(ag.araliklar[0].bas, 0);
  assert.equal(ag.araliklar[1].bas, ag.araliklar[0].say);
  assert.equal(ag.araliklar[0].say + ag.araliklar[1].say, ag.I.length);
  // seyrek: daha az köşe, son istasyon yine var
  const s = M.cubukAgi(els, { seyrek: 2 });
  assert.ok(s.kose < ag.kose);
  assert.ok(Array.from(s.vSt).indexOf(5) >= 0);
  // bölünmüş yan halkalar: daha çok köşe, kapaklar aynı
  const b = M.cubukAgi(els, { bol: 4 });
  assert.equal(b.anahatlar[0].sayi.kose, 4 * 8);
  assert.equal(b.anahatlar[0].sayi.kapakKose, an.sayi.kapakKose);
  // I profil kesiti ve tüp
  const ip = M.cubukAgi([kiris({ kesit: { sekil: "I", eksen: "y", h: 0.3, b: 0.15, tw: 0.0071, tf: 0.0107, dy: 0.3, dz: 0.15, A: 0.00538, Iz: 8.356e-5, Iy: 6.04e-6 } })], {});
  assert.equal(ip.anahatlar[0].sayi.kose, 24);
  const tup = M.cubukAgi(els, { tup: true, tupR: function () { return 0.05; } });
  assert.equal(tup.anahatlar[0].sayi.kose, 6);
  // değer doldurma: istasyon büyüklüğü ve lif gerilmesi, eksik veri GECERSIZ
  const V = new Float32Array(ag.kose);
  M.degerleriDoldur(ag, els, "Mz", V);
  for (let v = 0; v < ag.kose; v++) yakin(V[v], els[ag.vEl[v]].Mz[ag.vSt[v]], 1e-6);
  M.degerleriDoldur(ag, els, "kullanim", V);
  assert.equal(V[0], new Float32Array([M.GECERSIZ])[0]);
  M.degerleriDoldur(ag, els, "sigma_lif", V);
  for (let v = 0; v < ag.kose; v += 7) {
    const el = els[ag.vEl[v]], k = ag.vSt[v];
    yakin(V[v], M.lifGerilmesi(el.kesit, el.N[k], el.My[k], el.Mz[k], ag.vYZ[2 * v], ag.vYZ[2 * v + 1]), 1e-5);
  }
});

test("döşeme plağı ve radye ağları", function () {
  const pn = { z: 3, kose: [[0, 0, 3], [4, 0, 3], [4, 3, 3], [0, 3, 3]],
    izgara: { nx: 3, ny: 2, x: [0, 2, 4], y: [0, 3], w: [[0, 0.001, 0], [0, 0.002, 0]], mx: [[0, 1, 0], [0, 2, 0]], my: [[0, 1, 0], [0, 1, 0]] } };
  const a = M.plakAgi(pn, [[0, 0, -0.001], [0, 0, -0.001], [0, 0, -0.001], [0, 0, -0.001]], 0x700001);
  assert.equal(a.kose, 6);
  assert.equal(a.I.length, 6 * 2 * 1);
  yakin(a.D[3 * 4 + 2], -0.001 - 0.002, 1e-9);     // köşe çökmesi + plak sehimi (aşağı)
  assert.equal(M.renkKimlik(a.K[0], a.K[1], a.K[2]), 0x700001);
  yakin(M.plakDegeri(pn, "w", 1, 1), 2);           // mm
  yakin(M.plakDegeri(pn, "mx", 1, 1), 2);
  const r = { x: [0, 1, 2], y: [0, 1], z: 0, w: [[0.001, 0.002, null], [0.001, 0.001, 0.001]], p: [[15, 30, null], [15, 15, 15]] };
  const ra = M.radyeAgi(r, 0x7f0000);
  assert.equal(ra.I.length, 6);                   // eksik köşeli hücre atlanır
});

test("kamera: hedef ekran ortasında; standart görünümlerde eksen yönleri; sığdır kutuyu içine alır", function () {
  const kam = { hedef: [1, 2, 3], uzak: 20, yaw: M.STANDART["3b"].yaw, pitch: M.STANDART["3b"].pitch, fov: 35 * Math.PI / 180, orto: false, R: 5 };
  const km = M.kameraMatrisi(kam, 800, 600);
  yakin(M.izdusur(km, [1, 2, 3], 800, 600).slice(0, 2), [400, 300], 1e-6);
  function yon(ad, p) {
    const s = M.STANDART[ad];
    const k = { hedef: [0, 0, 0], uzak: 20, yaw: s.yaw, pitch: s.pitch, fov: 0.6, orto: s.orto, R: 5 };
    const m = M.kameraMatrisi(k, 800, 600), o = M.izdusur(m, [0, 0, 0], 800, 600), q = M.izdusur(m, p, 800, 600);
    return [q[0] - o[0], q[1] - o[1]];
  }
  assert.ok(yon("plan", [1, 0, 0])[0] > 0);        // plan: +X sağa
  assert.ok(yon("plan", [0, 1, 0])[1] < 0);        //        +Y yukarı (ekranda y aşağı artar)
  assert.ok(yon("on", [1, 0, 0])[0] > 0 && yon("on", [0, 0, 1])[1] < 0);   // ön: +X sağa, +Z yukarı
  assert.ok(yon("yan", [0, 1, 0])[0] > 0 && yon("yan", [0, 0, 1])[1] < 0); // yan: +Y sağa, +Z yukarı
  for (const ad of ["3b", "plan", "on", "yan"]) {
    const s = M.STANDART[ad];
    const k = { hedef: [0, 0, 0], uzak: 1, yaw: s.yaw, pitch: s.pitch, fov: 35 * Math.PI / 180, orto: s.orto, asp: 800 / 600 };
    const mn = [0, 0, 0], mx = [20, 8, 12];
    M.sigdir(k, mn, mx);
    const m = M.kameraMatrisi(k, 800, 600);
    for (let i = 0; i < 8; i++) {
      const p = M.izdusur(m, [i & 1 ? mx[0] : mn[0], i & 2 ? mx[1] : mn[1], i & 4 ? mx[2] : mn[2]], 800, 600);
      assert.ok(p && p[0] >= -1 && p[0] <= 801 && p[1] >= -1 && p[1] <= 601, ad + " köşe " + i + " ekran dışında: " + p);
    }
  }
});

test("süzgeçler: kat listesi, akslar (bina ya da koordinat), aks üstünde", function () {
  const alan = { elemanlar: [kiris(), kiris({ no: 8, kat: 2 })], dugumler: [{ X: 0, Y: 0 }, { X: 5, Y: 0 }, { X: 5, Y: 4 }] };
  const k = M.katListesi(alan, { katlar: [{ no: 1, ad: "1. kat" }] });
  assert.deepEqual(k.map(function (x) { return x.no; }), [1, 2]);
  assert.ok(k[0].ad.indexOf("1. kat") >= 0);
  const a1 = M.aksListesi(alan, { akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 5 }], y: [{ ad: "1", konum: 0 }] } });
  assert.equal(a1.length, 3);
  const a2 = M.aksListesi(alan, null);
  assert.equal(a2.filter(function (a) { return a.yon === "x"; }).length, 2);
  assert.ok(M.aksUstunde(kiris(), { yon: "y", konum: 0 }));
  assert.ok(!M.aksUstunde(kiris(), { yon: "x", konum: 0 }));
});
