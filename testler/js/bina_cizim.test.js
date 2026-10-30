/* docs/bina_cizim.js birim testleri — node'un yerleşik test koşucusu (bağımlılık yok).
   Çalıştırma: node --test testler/js/bina_cizim.test.js
   Kapsam: aks tabanlı çizimin SAF mantığı (DOM yok): çubuk türü, hızlı kolon çiftleri, çakışma denetimleri, aks sihirbazının
   mevcut modele uygulanması, yeni model, serbest düğümlerin aksa bağlanması (serbest koordinatlı düğüm kalmaz),
   beşik çerçeve / makas / kren yolu planları, mesnet ve yük kayıtları, seçim eşleme, bölme noktaları, ekran → düzlem,
   aks ekleme konumu, işlem özeti, çapraz seçenekleri. */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const DOCS = path.join(__dirname, "..", "..", "docs");
const BC = require(path.join(DOCS, "bina_cizim.js"));
const A = require(path.join(DOCS, "aks_sistemi.js"));
const O = require(path.join(DOCS, "model_ops.js"));

function yakin(a, b, tol, mesaj) {
  tol = tol == null ? 1e-6 : tol;
  if (Array.isArray(a)) { assert.equal(a.length, b.length, mesaj); a.forEach(function (x, i) { yakin(x, b[i], tol, mesaj); }); return; }
  assert.ok(Math.abs(a - b) <= tol, (mesaj || "") + ` beklenen ${b}, bulunan ${a}`);
}
const G = function (x, y, z) { return { aks: [x, y], z: z }; };
const KESITLER = { HEA300: { tip: "profil", profil: "HEA 300", malzeme: "S275" }, IPE300: { tip: "profil", profil: "IPE 300", malzeme: "S275" } };

/** Boş çelik model: A–C (0, 6, 12) × 1–2 (0, 5); Z: ±0.00, +3.00, +6.00 (kat 0–2). */
function bos() {
  const ak = A.hizliAks({ x: "2@6", y: "1@5", z: "2@3" });
  return BC.yeniModel({ sistem: "celik", kesitler: KESITLER }, ak, A.katlarTuret(ak), { sistem: "celik" });
}
function cubukEkle(m, i, j, ek) {
  const c = JSON.parse(JSON.stringify(m));
  const no = c.cubuklar.reduce(function (e, x) { return Math.max(e, +x.no); }, 0) + 1;
  c.cubuklar.push(Object.assign({ no: no, i: i, j: j, kesit: "HEA300", tur: "kiris" }, ek || {}));
  return c;
}
function serbestYok(m) { return (m.dugumler || []).every(function (d) { return d.X == null && d.Y == null && d.Z == null; }); }

// ------------------------------------------------------------------ dışa açılan yüzey
test("modül: saf işlevler ve ön ayarlar node'da yüklenir; arayüz kurulumu ayrı", function () {
  ["cubukTuru", "kolonCiftleri", "mevcutCubuk", "aksKatCakisan", "aksSihirbazUygula", "yeniModel", "serbestleriBagla", "aksaBaglaHepsi",
    "aksSagla", "besikPlan", "makasPlan", "krenPlan", "mesnetAta", "yukEkle", "secimAyir", "genelSecim", "bolmeNoktalari",
    "ekrandanDuzleme", "aksEkleKonumu", "ozet", "caprazSecenek", "kur", "otomatikKur"].forEach(function (ad) { assert.equal(typeof BC[ad], "function", ad); });
  assert.ok(Object.isFrozen(BC));
  assert.ok(BC.MESNET_ON_AYAR.ankastre && BC.MESNET_ON_AYAR.kaldir && BC.MAFSAL_ON_AYAR["iki-uc"] && BC.MAFSAL_ON_AYAR.kafes);
});

// ------------------------------------------------------------------ çubuk türü, kolon çiftleri
test("çubuk türü geometriden: düşey kolon, yatay kiriş, eğik diğer", function () {
  assert.equal(BC.cubukTuru([0, 0, 0], [0, 0, 3]), "kolon");
  assert.equal(BC.cubukTuru([0, 0, 3], [6, 0, 3]), "kiris");
  assert.equal(BC.cubukTuru([0, 0, 3], [6, 5, 3]), "kiris");
  assert.equal(BC.cubukTuru([0, 0, 0], [6, 0, 3]), "diger");
  assert.equal(BC.cubukTuru([1, 1, 1], [1, 1, 1]), "diger");
});

test("hızlı kolon çiftleri: yalnız alttaki aralık ya da tüm katlar (en alttan)", function () {
  const m = bos();
  assert.deepEqual(BC.kolonCiftleri(m, G("B", "2", "+6.00")), [[G("B", "2", "+3.00"), G("B", "2", "+6.00")]]);
  assert.deepEqual(BC.kolonCiftleri(m, G("B", "2", "+6.00"), { tumu: true }),
    [[G("B", "2", "±0.00"), G("B", "2", "+3.00")], [G("B", "2", "+3.00"), G("B", "2", "+6.00")]]);
  assert.deepEqual(BC.kolonCiftleri(m, G("A", "1", "±0.00")), [], "en alttaki Z aksının altında kolon yok");
  assert.deepEqual(BC.kolonCiftleri(m, { aks: ["A", "1"] }), [], "z'siz REF");
});

test("mevcut çubuk: REF ya da konumla, iki yönde; çakışan aks–kat elemanı", function () {
  let m = bos();
  m = cubukEkle(m, G("A", "1", "+3.00"), G("B", "1", "+3.00"));
  const no = m.cubuklar[0].no;
  assert.equal(BC.mevcutCubuk(m, G("A", "1", "+3.00"), G("B", "1", "+3.00")), no);
  assert.equal(BC.mevcutCubuk(m, G("B", "1", "+3.00"), G("A", "1", "+3.00")), no);
  assert.equal(BC.mevcutCubuk(m, G("B", "1", "+3.00"), G("C", "1", "+3.00")), null);
  const geo = { cubuklar: [{ kaynak: "kiris", no: 4, A: [0, 0, 3], B: [6, 0, 3] }, { kaynak: "cubuk", no: 9, A: [0, 5, 3], B: [6, 5, 3] }] };
  assert.deepEqual(BC.aksKatCakisan(geo, [3, 0, 3], [12, 0, 3]), { tur: "kiris", no: 4 }, "örtüşen eş doğrusal");
  assert.equal(BC.aksKatCakisan(geo, [6, 0, 3], [12, 0, 3]), null, "yalnız uçta değen");
  assert.equal(BC.aksKatCakisan(geo, [0, 5, 3], [6, 5, 3]), null, "surum 3 çubuğu aks–kat elemanı sayılmaz");
});

// ------------------------------------------------------------------ aks sihirbazı, yeni model
test("yeni model: surum 3, boş listeler; kesitler yalnız aynı sistemde taşınır", function () {
  const ak = A.hizliAks({ x: "1@6", y: "1@5", z: "1@3" });
  const m = BC.yeniModel({ sistem: "celik", kesitler: KESITLER, deprem: { Ss: 1 } }, ak, A.katlarTuret(ak), { sistem: "celik" });
  assert.equal(m.surum, 3);
  assert.equal(m.sistem, "celik");
  ["kolonlar", "kirisler", "dosemeler", "dugumler", "cubuklar", "paneller", "mesnetler", "ek_yukler", "uretecler"].forEach(function (k) { assert.deepEqual(m[k], [], k); });
  assert.deepEqual(Object.keys(m.kesitler).sort(), ["HEA300", "IPE300"]);
  assert.deepEqual(m.deprem, { Ss: 1 });
  const b = BC.yeniModel({ sistem: "celik", kesitler: KESITLER }, ak, A.katlarTuret(ak), { sistem: "betonarme" });
  assert.equal(b.sistem, "betonarme");
  assert.deepEqual(b.kesitler, {}, "sistem değişince çelik kesitler taşınmaz");
});

test("aks sihirbazı mevcut modele: aynı ad konum değişir (eleman yapışık), eksik ad elemanlarıyla silinir, Z kat eşlemesi", function () {
  let m = bos();
  m = cubukEkle(m, G("A", "1", "+3.00"), G("B", "1", "+3.00"));
  m = cubukEkle(m, G("B", "1", "+3.00"), G("C", "1", "+3.00"));
  const ak = A.hizliAks({ x: "1@7", y: "1@5", z: "1@3.5, 3" });       // A@0, B@7 (C yok); Z: ±0.00, +3.50, +6.50
  const r = BC.aksSihirbazUygula(m, ak, A.katlarTuret(ak));
  assert.deepEqual(r.model.akslar.x.map(function (a) { return a.ad + "@" + a.konum; }), ["A@0", "B@7"]);
  assert.equal(r.model.cubuklar.length, 1, "C aksına bağlı çubuk silindi");
  assert.ok(r.silinen.some(function (s) { return s.yon === "x" && s.ad === "C"; }));
  // Z: kata bağlı akslar kat numarasıyla eşlenir; eski ad (+3.00) korunur, konum değişir
  const z = r.model.akslar.z;
  assert.deepEqual(z.map(function (a) { return a.kat; }), [0, 1, 2]);
  yakin(z[1].konum, 3.5);
  const P = A.refKoordinat(r.model, r.model.cubuklar[0].j);
  yakin(P, [7, 0, 3.5], 1e-9, "çubuk akslara yapışık taşındı");
  assert.deepEqual(r.model.katlar.map(function (k) { return k.kot; }), [0, 3.5, 6.5], "katlar Z akslarıyla eşit");
});

test("aks sihirbazı: kaldırılan katın aks–kat elemanları silinir; bağlı eleman taşıyan kat dışı Z aksı korunur", function () {
  const ak0 = A.hizliAks({ x: "1@6", y: "1@5", z: "2@3", ekZ: [{ ad: "Çatı", konum: 7.5 }] });
  let m = BC.yeniModel({ sistem: "celik", kesitler: KESITLER }, ak0, A.katlarTuret(ak0), { sistem: "celik" });
  m.kolonlar = [{ no: 1, kat: 1, aks: ["A", "1"], kesit: "HEA300" }, { no: 2, kat: 2, aks: ["A", "1"], kesit: "HEA300" }];
  m = cubukEkle(m, G("A", "1", "+6.00"), G("B", "1", "Çatı"));
  const ak = A.hizliAks({ x: "1@6", y: "1@5", z: "1@3" });          // 1 kat; Çatı ve +6.00 sihirbazda yok
  const r = BC.aksSihirbazUygula(m, ak, A.katlarTuret(ak));
  assert.deepEqual(r.model.kolonlar.map(function (k) { return k.no; }), [1], "2. kat kolonu silindi");
  const adlar = r.model.akslar.z.map(function (a) { return a.ad; });
  assert.ok(adlar.indexOf("Çatı") >= 0 && adlar.indexOf("+6.00") >= 0, "bağlı çubuğu olan Z aksları korundu: " + adlar);
  assert.ok(r.uyarilar.some(function (u) { return /Çatı/.test(u) && /korundu/.test(u); }));
});

// ------------------------------------------------------------------ serbest düğümler → aks
test("serbest düğümler iki aks kesişimi arasında bölme düğümüne çevrilir; konum korunur", function () {
  let m = bos();
  m.dugumler = [{ no: 1, X: 3, Y: 0, Z: 3 }, { no: 2, X: 0, Y: 2.5, Z: 6 }, { no: 3, X: 12, Y: 5, Z: 1.5 }, { no: 4, X: 3, Y: 2, Z: 1 }];
  const r = BC.serbestleriBagla(m);
  assert.deepEqual(r.baglanan.sort(), [1, 2, 3]);
  assert.deepEqual(r.kalan, [4], "hiçbir aks doğrusuna düşmeyen düğüm kalır");
  const d1 = r.model.dugumler[0];
  assert.equal(d1.tur, "bolme");
  assert.deepEqual([d1.cubuk_i, d1.cubuk_j, d1.oran], [G("A", "1", "+3.00"), G("B", "1", "+3.00"), 0.5]);
  const cz = new A.Cozucu(r.model);
  yakin(cz.coz({ dugum: 1 }), [3, 0, 3]);
  yakin(cz.coz({ dugum: 2 }), [0, 2.5, 6]);
  yakin(cz.coz({ dugum: 3 }), [12, 5, 1.5]);
  assert.equal(m.dugumler[0].X, 3, "girdi modeli değişmez");
});

test("aksa bağla (hepsi): kalan düğüm varsa 'aks ekleyin' uyarısı", function () {
  const m = bos();
  m.dugumler = [{ no: 7, X: 3, Y: 2, Z: 1 }];
  const r = BC.aksaBaglaHepsi(m);
  assert.deepEqual(r.kalan, [7]);
  assert.ok(r.uyarilar.some(function (u) { return /aks ekleyin/.test(u); }));
});

// ------------------------------------------------------------------ üreteç planları
test("aks sağla: konumda aks varsa adı, yoksa eklenir", function () {
  const m = bos();
  const a = BC.aksSagla(m, "x", 6);
  assert.deepEqual([a.ad, a.eklendi], ["B", false]);
  const b = BC.aksSagla(m, "z", 7.5, "Çatı");
  assert.deepEqual([b.ad, b.eklendi], ["Çatı", true]);
  assert.ok(b.model.akslar.z.some(function (z) { return z.ad === "Çatı" && z.konum === 7.5; }));
});

test("beşik çerçeve planı + üreteç: saçak/mahya Z aksları ve mahya X aksları eklenir, serbest düğüm kalmaz", function () {
  const ak = A.hizliAks({ x: "2@20", y: "3@6", z: "8" });
  let m = BC.yeniModel({ sistem: "celik", kesitler: KESITLER }, ak, A.katlarTuret(ak), { sistem: "celik" });
  m = A.aksYenidenAdlandir(m, { yon: "z", eski: "+8.00", yeni: "Saçak" }).model;
  const p = BC.besikPlan(m, { acikliklar: [["A", "B"], ["B", "C"]], y: ["1", "2", "3", "4"], taban: "±0.00", sacak: 8, mahya: 9.5,
    kesitler: { kolon: "HEA300", mertek: "IPE300" }, asik: { aralik: 2.5, kesit: "IPE300" }, panel: true, mesnet: "ankastre" });
  assert.equal(p.parametreler.length, 2, "eşit aralıklı çerçeveler: açıklık başına bir parametre");
  assert.deepEqual(p.model.akslar.x.map(function (a) { return a.ad + "@" + a.konum; }), ["A@0", "A'@10", "B@20", "B'@30", "C@40"]);
  assert.ok(p.model.akslar.z.some(function (z) { return z.ad === "Mahya" && z.konum === 9.5; }));
  assert.equal(p.model.akslar.z.filter(function (z) { return z.konum === 8; }).length, 1, "Saçak varken yeni saçak aksı eklenmez");
  assert.deepEqual([p.parametreler[0].sacak, p.parametreler[0].mahya, p.parametreler[0].adet, p.parametreler[0].aralik], [8, 9.5, 4, 6]);
  m = p.model;
  for (const par of p.parametreler) m = O.besikCerceveUret(m, par).model;
  const b = BC.aksaBaglaHepsi(m);
  assert.deepEqual(b.kalan, []);
  assert.ok(serbestYok(b.model), "bütün düğümler aks kesişimi ya da bölme düğümü");
  assert.ok(b.model.cubuklar.length > 40 && b.model.paneller.length > 0);
  assert.ok(b.model.cubuklar.some(function (c) { return c.tur === "asik"; }));
  assert.throws(function () { BC.besikPlan(m, { acikliklar: [["A", "B"]], y: ["1"], taban: "±0.00", sacak: 9, mahya: 8 }); }, /mahya/);
  assert.throws(function () { BC.besikPlan(m, { acikliklar: [["A", "B"]], y: [], taban: "±0.00", sacak: 8, mahya: 9 }); }, /çerçeve/);
});

test("beşik plan: eşit olmayan çerçeve aralıklarında çerçeve başına parametre ve aşık uyarısı", function () {
  const ak = A.hizliAks({ x: "1@20", y: "6, 8", z: "8" });
  const m = BC.yeniModel({ sistem: "celik", kesitler: KESITLER }, ak, A.katlarTuret(ak), { sistem: "celik" });
  const p = BC.besikPlan(m, { acikliklar: [["A", "B"]], y: ["1", "2", "3"], taban: "±0.00", sacak: 8, mahya: 10, kesitler: {}, asik: { aralik: 2, kesit: "IPE300" } });
  assert.equal(p.parametreler.length, 3);
  assert.ok(p.parametreler.every(function (q) { return q.adet === 1 && !q.asik; }));
  assert.ok(p.uyarilar.some(function (u) { return /eşit değil/.test(u); }));
});

test("makas planı: üst başlık / mahya Z aksı ve beşik tipte açıklık ortası aksı; kotlar eşit olmalı", function () {
  const m = bos();
  const p = BC.makasPlan(m, { tip: "besik-howe", bas: G("A", "1", "+6.00"), son: G("C", "1", "+6.00"), yukseklik: 1.5, goz: 8, kesitler: {} });
  assert.ok(p.model.akslar.z.some(function (z) { return z.ad === "Mahya" && z.konum === 7.5; }));
  assert.equal(BC.aksAdi(p.model, "x", 6), "B", "orta aks zaten var (B)");
  assert.deepEqual([p.parametre.tip, p.parametre.goz, p.parametre.yukseklik], ["besik-howe", 8, 1.5]);
  const q = BC.makasPlan(m, { tip: "pratt", bas: G("A", "1", "+6.00"), son: G("B", "1", "+6.00"), yukseklik: 1.2, goz: 6 });
  assert.ok(q.eklenen.some(function (e) { return /Makas üst/.test(e); }));
  let r = q.model;
  r = O.makasUret(r, q.parametre).model;
  assert.ok(serbestYok(BC.aksaBaglaHepsi(r).model));
  assert.throws(function () { BC.makasPlan(m, { tip: "pratt", bas: G("A", "1", "+3.00"), son: G("B", "1", "+6.00"), yukseklik: 1 }); }, /aynı kotta/);
  assert.throws(function () { BC.makasPlan(m, { tip: "pratt", bas: G("A", "1", "+6.00"), son: G("B", "1", "+6.00"), yukseklik: 0 }); }, /pozitif/);
});

test("kren planı: kren kotunda Z aksı ve hat üzerindeki kolon çubukları", function () {
  let m = bos();
  ["1", "2"].forEach(function (y) { ["A", "B", "C"].forEach(function (x) { m = cubukEkle(m, G(x, y, "±0.00"), G(x, y, "+6.00"), { tur: "kolon" }); }); });
  const r = BC.krenPlan(m, { hatlar: ["1", "2"], yon: "y", kot: 4.5 });
  assert.ok(r.model.akslar.z.some(function (z) { return z.ad === "Kren" && z.konum === 4.5; }));
  assert.deepEqual(r.kolonlar.map(function (l) { return l.length; }), [3, 3]);
  const s = BC.krenPlan(m, { hatlar: ["1"], yon: "y", kot: 9 });
  assert.deepEqual(s.kolonlar, []);
  assert.ok(s.uyarilar.length === 1);
});

// ------------------------------------------------------------------ mesnet, yük
test("mesnet ata: ekle, aynı düğümde değiştir, kaldır", function () {
  let m = bos();
  let r = BC.mesnetAta(m, G("A", "1", "±0.00"), "ankastre");
  assert.equal(r.eylem, "eklendi");
  assert.deepEqual(r.model.mesnetler[0], { dugum: G("A", "1", "±0.00"), ux: true, uy: true, uz: true, rx: true, ry: true, rz: true });
  r = BC.mesnetAta(r.model, G("A", "1", "±0.00"), "kayici-xy");
  assert.equal(r.eylem, "degisti");
  assert.deepEqual([r.model.mesnetler.length, r.model.mesnetler[0].ux, r.model.mesnetler[0].uz], [1, false, true]);
  r = BC.mesnetAta(r.model, G("A", "1", "±0.00"), "kaldir");
  assert.deepEqual([r.eylem, r.model.mesnetler.length], ["kaldirildi", 0]);
  assert.equal(BC.mesnetAta(r.model, G("A", "1", "±0.00"), "kaldir").eylem, "yok");
  assert.throws(function () { BC.mesnetAta(m, G("A", "1", "±0.00"), "bilinmez"); }, /tanımsız/);
});

test("yük ekle: çubuk yayılı / tekil, panel, düğüm; geçersiz durum ve boş yük reddedilir", function () {
  const m = bos();
  let r = BC.yukEkle(m, { tur: "cubuk", no: 3 }, { durum: "q", yon: "Z", q1: "-5" });
  assert.deepEqual(r.kayit, { tur: "cubuk", cubuk: 3, durum: "Q", yon: "Z", q1: -5, q2: -5, x1: 0, x2: null, oransal: false, izdusum: false });
  r = BC.yukEkle(r.model, { tur: "cubuk", no: 3 }, { durum: "G", yon: "Z", P: -10, x: 0.5, oransal: true });
  assert.deepEqual([r.kayit.P, r.kayit.x, r.kayit.oransal], [-10, 0.5, true]);
  r = BC.yukEkle(r.model, { tur: "panel", no: 1 }, { durum: "S", g: "0,75" });
  assert.deepEqual(r.kayit, { tur: "panel", panel: 1, durum: "S", g: 0.75 });
  r = BC.yukEkle(r.model, { tur: "dugum", ref: G("B", "2", "+6.00") }, { durum: "G", FZ: "−12" });
  assert.deepEqual(r.kayit, { tur: "dugum", dugum: G("B", "2", "+6.00"), durum: "G", FZ: -12 });
  assert.equal(r.model.ek_yukler.length, 4);
  assert.throws(function () { BC.yukEkle(m, { tur: "dugum", ref: G("A", "1", "+3.00") }, { durum: "E", FZ: 1 }); }, /G, Q ya da S/);
  assert.throws(function () { BC.yukEkle(m, { tur: "dugum", ref: G("A", "1", "+3.00") }, { durum: "G" }); }, /en az bir bileşen/);
  assert.throws(function () { BC.yukEkle(m, { tur: "panel", no: 1 }, { durum: "G" }); }, /g ya da q/);
});

// ------------------------------------------------------------------ seçim, bölme noktaları
test("seçim ayır ve genelleştirme sonrası seçim eşlemesi", function () {
  const s = [{ tur: "cubuk", no: 2 }, { tur: "kolon", no: 5 }, { tur: "panel", no: 1 }, { tur: "dugum", no: 9 }, { tur: "doseme", no: 3 }];
  assert.deepEqual(BC.secimAyir(s), { cubuklar: [2], paneller: [1], aksKat: [{ tur: "kolon", no: 5 }, { tur: "doseme", no: 3 }], dugumler: [9] });
  const yeni = { cubuklar: [{ no: 11, kaynak: { aks_kat: "kolon", no: 5 } }, { no: 12, kaynak: { aks_kat: "kolon", no: 5 } }, { no: 13, kaynak: { aks_kat: "kiris", no: 5 } }],
    paneller: [{ no: 4, kaynak: { aks_kat: "doseme", no: 3 } }] };
  assert.deepEqual(BC.genelSecim(yeni, s), [{ tur: "cubuk", no: 2 }, { tur: "cubuk", no: 11 }, { tur: "cubuk", no: 12 }, { tur: "panel", no: 1 }, { tur: "dugum", no: 9 }, { tur: "panel", no: 4 }]);
});

test("bölme noktaları: çubuğun iç noktalarına düşen aks kesişimleri, t sıralı", function () {
  let m = bos();
  m = cubukEkle(m, G("C", "1", "+3.00"), G("A", "1", "+3.00"));
  const l = BC.bolmeNoktalari(m, m.cubuklar[0].no);
  assert.equal(l.length, 1);
  assert.deepEqual(l[0].ref, G("B", "1", "+3.00"));
  yakin(l[0].t, 0.5);
  m = cubukEkle(m, G("A", "1", "±0.00"), G("A", "1", "+6.00"), { tur: "kolon" });
  const k = BC.bolmeNoktalari(m, m.cubuklar[1].no);
  assert.deepEqual(k.map(function (x) { return x.ref.z; }), ["+3.00"]);
  assert.deepEqual(BC.bolmeNoktalari(m, 999), []);
});

// ------------------------------------------------------------------ ekran ↔ düzlem, aks ekle, özet, çapraz
test("ekran → düzlem: doğrusal izdüşümün tersi; düzleme dik bakışta null", function () {
  const P = function (X, Y, Z) { return [10 + 20 * X - 5 * Y, 300 - 20 * Z + 8 * Y]; };     // eğik izdüşüm
  const Q = BC.ekrandanDuzleme(P, { i: 2, v: 3 }, P(4.5, 2, 3));
  yakin(Q, [4.5, 2, 3], 1e-9);
  const R = BC.ekrandanDuzleme(P, { i: 1, v: 0 }, P(7, 0, 1.25));
  yakin(R, [7, 0, 1.25], 1e-9);
  const plan = function (X, Y) { return [X * 10, -Y * 10]; };                                // plan: Z ekranda görünmez
  assert.equal(BC.ekrandanDuzleme(plan, { i: 0, v: 0 }, [0, 0]), null);
});

test("aks ekleme konumu: iki aks arasında ortası, dışında 0,05 m adıma yuvarlanır", function () {
  const m = bos();
  assert.deepEqual(BC.aksEkleKonumu(m, "x", 2.2), { arasina: ["A", "B"], konum: 3 });
  assert.deepEqual(BC.aksEkleKonumu(m, "x", 14.33), { konum: 14.35 });
  assert.deepEqual(BC.aksEkleKonumu(m, "z", 4), { arasina: ["+3.00", "+6.00"], konum: 4.5 });
  assert.deepEqual(BC.aksEkleKonumu(m, "y", -1.02), { konum: -1 });
});

test("işlem özeti ve çapraz seçenekleri", function () {
  assert.equal(BC.ozet({ eklenen: { cubuklar: [1, 2], paneller: [3] }, silinen: { cubuklar: [4], kolonlar: [1] }, degisen: { cubuklar: [5] } }),
    "2 çubuk, 1 panel eklendi; 1 çubuk değişti; 1 çubuk, 1 kolon kaldırıldı");
  assert.equal(BC.ozet(null), "");
  const goz = { P: [[0, 0, 0], [6, 0, 0], [6, 0, 3], [0, 0, 3]] };
  assert.deepEqual(BC.caprazSecenek("dismerkez-ters-V", goz), { mafsalli_uclar: true, e: 0.9 });
  assert.deepEqual(BC.caprazSecenek("diz", goz), { mafsalli_uclar: true, a: 0.6 });
  assert.deepEqual(BC.caprazSecenek("X", goz, { mafsalli_uclar: false }), { mafsalli_uclar: false });
});

test("sayı ve biçim: virgül / eksi işareti, kısa kot biçimi", function () {
  assert.equal(BC.sayi("2,5"), 2.5);
  assert.equal(BC.sayi("−3"), -3);
  assert.equal(BC.sayi("3 m"), null);
  assert.equal(BC.fmt(-1.5), "−1,50");
  assert.equal(BC.fmtK(7.5), "7,5");
});

// ------------------------------------------------------------------ genel model kapısı (C1), aks–kat yolları
/** Aks–kat (surum 1) betonarme modeli: A–B–C (0, 5, 9) × 1–2 (0, 4), 2 kat; her kesişimde kolon, X ve Y kirişleri, iki döşeme / kat. */
function aksKatModel(temelTip) {
  const kol = [], kir = [], dos = [];
  let n = 0, kn = 0, d = 0;
  for (const k of [1, 2]) for (const x of ["A", "B", "C"]) for (const y of ["1", "2"]) kol.push({ no: ++n, aks: [x, y], kat: k, kesit: "S40x40", yon: "x" });
  for (const k of [1, 2]) {
    for (const y of ["1", "2"]) kir.push({ no: ++kn, kat: k, bas: ["A", y], son: ["C", y], kesit: "K25x50", duvar: null });
    for (const x of ["A", "B", "C"]) kir.push({ no: ++kn, kat: k, bas: [x, "1"], son: [x, "2"], kesit: "K25x50", duvar: null });
    dos.push({ no: ++d, kat: k, kose: [["A", "1"], ["B", "2"]], h: 0.14, kullanim: "konut" }, { no: ++d, kat: k, kose: [["B", "1"], ["C", "2"]], h: 0.14, kullanim: "konut" });
  }
  return { tur: "bina", surum: 1, sistem: "betonarme",
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 5 }, { ad: "C", konum: 9 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }] },
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3 }, { no: 2, ad: "2. kat", kot: 6 }],
    kesitler: { S40x40: { tip: "dikdortgen", b: 0.4, h: 0.4, malzeme: "C30" }, K25x50: { tip: "dikdortgen", b: 0.25, h: 0.5, malzeme: "C30" } },
    duvarlar: { tugla19: { kutuphane: "tugla19" } },
    kolonlar: kol, kirisler: kir, dosemeler: dos, ek_yukler: [],
    temeller: Object.assign({ mesnet: "ankastre" }, temelTip ? { tip: temelTip } : {}) };
}

test("C1 genel model kuralı: sabit doğruluk tablosu (motor _serbest_mi ve bina.js s3Var ile aynı)", function () {
  const b = aksKatModel();
  const ek = function (o) { return Object.assign(JSON.parse(JSON.stringify(b)), o); };
  const tablo = [
    [b, false],
    [ek({ mesnetler: [{ dugum: { aks: ["B", "2"], z: "+3.00" }, ux: true, uy: true, uz: true }] }), true],
    [ek({ dugumler: [{ no: 100001, X: 0, Y: 0, Z: 3 }] }), true],
    [ek({ uretecler: [{ no: 1, tur: "makas", parametreler: {} }] }), true],
    [ek({ ek_yukler: [{ tur: "dugum", aks: ["B", "2"], kat: 1, durum: "G", FZ: -10 }] }), false],
    [ek({ ek_yukler: [{ tur: "dugum", dugum: { aks: ["B", "2"], z: "+3.00" }, durum: "G", FZ: -10 }] }), true],
    [ek({ ek_yukler: [{ tur: "cubuk", cubuk: 1, durum: "G", q: -1 }] }), true],
    [ek({ surum: 3 }), true],
    [ek({ cubuklar: [], mesnetler: [] }), false],
    [ek({ surum: "3" }), true],
    [ek({ ek_yukler: [{ tur: "kiris", kiris: 1, durum: "G", q: 2 }, { tur: "doseme", doseme: 1, g: 1 }] }), false],
  ];
  tablo.forEach(function (t, i) { assert.equal(BC.genelMi(t[0]), t[1], "satır " + (i + 1)); });
  // K2 ek doğruluk satırları (üç uygulamada aynı: yapi._serbest_mi, genelMi, bina.js s3Var)
  const k2 = [
    [ek({ ek_yukler: [{ tur: "Cubuk", cubuk: 1, durum: "G", q: -1 }] }), true, "tur 'Cubuk'"],
    [ek({ ek_yukler: [{ tur: " panel", panel: 1, durum: "G", p: 1 }] }), true, "tur ' panel'"],
    [ek({ ek_yukler: [{ tur: "PANEL", panel: 1, durum: "G", p: 1 }] }), true, "tur 'PANEL'"],
    [ek({ surum: "3.0" }), true, "surum '3.0'"],
    [ek({ surum: "3.5" }), true, "surum '3.5'"],
    [ek({ surum: "3a" }), false, "surum '3a'"],
    [ek({ surum: "0x3" }), false, "surum '0x3'"],
    [ek({ surum: "1e1" }), false, "surum '1e1'"],
    [ek({ surum: 2.9 }), false, "surum 2.9 (tam kısmı 2)"],
    [ek({ surum: 3.7 }), true, "surum 3.7"],
    [ek({ surum: " 3 " }), true, "surum ' 3 '"],
    [ek({ surum: true }), false, "surum true → 1"],
    [ek({ surum: null }), false, "surum null → 1"],
    [ek({ surum: Infinity }), false, "surum ∞ → 1"],
  ];
  k2.forEach(function (t) { assert.equal(BC.genelMi(t[0]), t[1], t[2]); });
  assert.deepEqual(["3.0", "3.5", "3a", "0x3", "1e1", 2.9, true, "-2", "+4.25", "", undefined].map(BC.surumSayi), [3, 3, 1, 1, 1, 2, 1, -2, 4, 1, 1]);
  assert.equal(BC.genelMi(bos()), true, "yeni aks modeli surum 3");
  assert.equal(BC.genelGecisGerekli(b), true);
  assert.equal(BC.genelGecisGerekli(bos()), false);
  assert.equal(BC.genelGecisGerekli(ek({ surum: 3 })), true, "aks–kat elemanı taşıyan surum 3 (karma) da çevrilir");
});

// K-1 (C11.7): genel model motoru mütemadi ve radye temeli de çözer — eski beklenti (temel tekile çevrilir, onay metni bunu söyler)
// motorun eski sınırını kodluyordu; kapı artık temelleri aynen bırakır
test("genelleştirme kapısı (C11): temeller aynen kalır (tekil, mütemadi, radye), temelDegisti false; onay metninde temel yan cümlesi yok", function () {
  for (const tip of ["radye", "surekli", "mütemadi"]) {
    const b = aksKatModel(tip);
    b.temeller.radye = { h: 0.6, tasma: 0.5, ag: 1 };
    const r = BC.genellestirHazirla(b);
    assert.equal(r.model.temeller.tip, tip, tip + " korunur");
    assert.deepEqual(r.model.temeller, b.temeller, "temeller kaydı aynen");
    assert.equal(r.temelDegisti, false);
    assert.equal(r.model.surum, 3);
    assert.equal(BC.genelMi(r.model), true);
    assert.equal(r.model.kolonlar.length + r.model.kirisler.length + r.model.dosemeler.length, 0);
    assert.ok(r.notlar.some(function (n) { return /genelleştirildi/.test(n); }));
    assert.ok(!r.notlar.some(function (n) { return /temel|Radye|Mütemadi/i.test(n); }), "temel notu yok: " + r.notlar.join(" | "));
    assert.equal((r.model.dugumler || []).length, 0, "koordinatlı aks–kat düğüm kaydı yazılmaz");
  }
  const t = BC.genellestirHazirla(aksKatModel());
  assert.equal(t.temelDegisti, false); assert.equal(t.model.temeller.tip, undefined);
  assert.equal(BC.genelGecisMetni(aksKatModel("surekli"), "Böl"), "Böl — Model genel (surum 3) modele çevrilecek: kolon/kiriş/döşemeler çubuk ve panel olur, adım adım anlatım kısalır. Devam edilsin mi?");
  ["surekli", "radye", undefined].forEach(function (tip) { assert.doesNotMatch(BC.genelGecisMetni(aksKatModel(tip), "Mesnet"), /temel/); });
  assert.match(BC.genelGecisMetni(aksKatModel()), /^Model genel/, "işlem adı yoksa ön ek yok");
});

test("yük ekle (aks–kat, C10): düğüm {aks, kat}, kiriş q (aşağı +), döşeme g/q; model çevrilmez; kolon ve döşemede kar reddedilir", function () {
  const b = aksKatModel();
  let r = BC.yukEkle(b, { tur: "dugum", ref: { aks: ["C", "2"], kat: 2 } }, { durum: "G", FZ: "-50" });
  assert.deepEqual(r.kayit, { tur: "dugum", aks: ["C", "2"], kat: 2, durum: "G", FZ: -50 });
  assert.equal(BC.genelMi(r.model), false, "aks–kat düğüm yükü modeli genel yapmaz");
  r = BC.yukEkle(r.model, { tur: "dugum", ref: { aks: ["B", "1"], z: "+3.00" } }, { durum: "Q", FX: 4 });
  assert.deepEqual(r.kayit, { tur: "dugum", aks: ["B", "1"], kat: 1, durum: "Q", FX: 4 }, "{aks, z} → kat");
  r = BC.yukEkle(r.model, { tur: "dugum", ref: { dugum: 2022 } }, { durum: "G", FZ: -1 });
  assert.deepEqual([r.kayit.aks, r.kayit.kat], [["B", "2"], 2], "aks–kat düğüm numarası 1000·kat + 20·ix + iy + 1");
  r = BC.yukEkle(r.model, { tur: "kiris", no: 1 }, { durum: "S", q1: "-3" });
  assert.deepEqual(r.kayit, { tur: "kiris", kiris: 1, durum: "S", q: 3 });
  r = BC.yukEkle(r.model, { tur: "kiris", no: 2 }, { durum: "Q", q: "2,5" });
  assert.deepEqual(r.kayit, { tur: "kiris", kiris: 2, durum: "Q", q: 2.5 });
  r = BC.yukEkle(r.model, { tur: "doseme", no: 1 }, { g: 1, q: "2" });
  assert.deepEqual(r.kayit, { tur: "doseme", doseme: 1, g: 1, q: 2 });
  assert.equal(r.model.ek_yukler.length, 6);
  assert.equal(BC.genelMi(r.model), false);
  assert.throws(function () { BC.yukEkle(b, { tur: "kolon", no: 1 }, { durum: "G", FZ: -1 }); }, /kolonuna ek yük verilemez/);
  assert.throws(function () { BC.yukEkle(b, { tur: "doseme", no: 1 }, { durum: "S", g: 1 }); }, /kar \(S\)/);
  assert.throws(function () { BC.yukEkle(b, { tur: "kiris", no: 1 }, { durum: "G", q1: -1, q2: -2 }); }, /düzgün yayılı/);
  assert.throws(function () { BC.yukEkle(b, { tur: "kiris", no: 1 }, { durum: "G", P: -5, x: 1 }); }, /tekil yük/);
  assert.throws(function () { BC.yukEkle(b, { tur: "kiris", no: 1 }, { durum: "G", yon: "X", q1: -1 }); }, /düşey/);
  assert.throws(function () { BC.yukEkle(b, { tur: "kiris", no: 99 }, { durum: "G", q: 1 }); }, /yok/);
  assert.throws(function () { BC.yukEkle(b, { tur: "dugum", ref: { sistem: "K", aks: ["A", "1"], z: "a" } }, { durum: "G", FZ: -1 }); }, /kat düzlemlerindeki/);
  // genel modelde panel yükü (C6): {durum, p}
  const g = bos();
  const p = BC.yukEkle(g, { tur: "panel", no: 1 }, { durum: "S", p: "0,8" });
  assert.deepEqual(p.kayit, { tur: "panel", panel: 1, durum: "S", p: 0.8 });
  assert.throws(function () { BC.yukEkle(g, { tur: "panel", no: 1 }, { durum: "G", p: "0" }); }, /sıfırdan farklı/);
});

test("mesnet (SAF): aks–kat düğümüne mesnet modeli genelleştirir (surum 3, temeller aynen — C11); kaldırmada çevirmez", function () {
  const b = aksKatModel("surekli");
  const r = BC.mesnetAta(b, { aks: ["C", "2"], kat: 2 }, "mafsal");
  assert.equal(r.eylem, "eklendi");
  assert.equal(r.genellesti, true);
  assert.equal(r.model.surum, 3);
  assert.equal(BC.genelMi(r.model), true);
  assert.equal(r.model.kolonlar.length, 0);
  assert.equal(r.model.temeller.tip, "surekli", "mütemadi temel korunur (eski beklenti tekildi: motorun eski sınırı)");
  assert.equal(r.temelDegisti, false);
  assert.deepEqual(r.model.mesnetler, [{ dugum: { aks: ["C", "2"], kat: 2 }, ux: true, uy: true, uz: true, rx: false, ry: false, rz: false }]);
  yakin(A.refKoordinat(r.model, r.model.mesnetler[0].dugum), [9, 4, 6]);
  // akslar.z tanımlıysa {aks, kat} → {aks, z}
  const z = aksKatModel(); z.akslar.z = [{ ad: "T", konum: 0, kat: 0 }, { ad: "K1", konum: 3, kat: 1 }, { ad: "K2", konum: 6, kat: 2 }];
  assert.deepEqual(BC.mesnetAta(z, { aks: ["C", "2"], kat: 2 }, "ankastre").model.mesnetler[0].dugum, { aks: ["C", "2"], z: "K2" });
  const k = BC.mesnetAta(b, { aks: ["C", "2"], kat: 2 }, "kaldir");
  assert.equal(k.eylem, "yok"); assert.equal(k.model.surum, 1); assert.equal(k.genellesti, false);
});

test("aksa bağla: genelleştirilmiş modelde yanlış 'aks ekleyin' yok; eski aks–kat kayıtları atlanır; kesişimdeki kayıt REF olur", function () {
  const g = BC.genellestirHazirla(aksKatModel()).model;
  const r = BC.aksaBaglaHepsi(g);
  assert.deepEqual(r.uyarilar, []); assert.deepEqual(r.kalan, []);
  // eski genelleştirmenin kayıtları ({no, X, Y, Z, aks, kat}) ve tam kesişimdeki koordinatlı kayıt
  const m = JSON.parse(JSON.stringify(g));
  m.dugumler = [{ no: 1001, X: 0, Y: 0, Z: 3, aks: ["A", "1"], kat: 1 }, { no: 100001, X: 5, Y: 4, Z: 6 }];
  m.cubuklar.push({ no: 99, i: { dugum: 100001 }, j: { aks: ["C", "2"], kat: 2 }, tur: "kiris", kesit: "K25x50" });
  m.mesnetler = [{ dugum: { dugum: 100001 }, ux: true, uy: true, uz: true }];
  const s = BC.serbestleriBagla(m);
  assert.deepEqual(s.kalan, []);
  assert.deepEqual(s.baglanan, [100001]);
  const c = s.model.cubuklar.find(function (x) { return x.no === 99; });
  assert.deepEqual(c.i, { aks: ["B", "2"], z: "+6.00" });
  assert.deepEqual(s.model.mesnetler[0].dugum, { aks: ["B", "2"], z: "+6.00" });
  assert.deepEqual(s.model.dugumler.map(function (d) { return d.no; }), [1001], "eski kayıt dokunulmadan kalır, kesişimdeki kayıt silinir");
  assert.ok(!BC.aksaBaglaHepsi(m).uyarilar.some(function (u) { return /aks ekleyin/.test(u); }));
});

test("aks–kat özellik yazımı (genelleştirmeden): kesit, grup, kolon açısı 0/90 → yon, kiriş duvarı ve duvar_h; desteklenmeyen alan → null", function () {
  const b = aksKatModel();
  let r = BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }, { tur: "kiris", no: 2 }], { kesit: "K25x50" });
  assert.equal(r.sayi, 2);
  assert.equal(r.model.kolonlar[0].kesit, "K25x50"); assert.equal(r.model.kirisler[1].kesit, "K25x50"); assert.equal(r.model.surum, 1);
  // NEW-4: grup ve kiriş duvar_h bina.js binaYukle'de korunur (c8d681c) ve aks–kat motoru duvar_h'yi okur → surum 1'de yazılır
  // (eski beklenti null'du: model gereksiz yere genel modele çevriliyordu)
  r = BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }], { kesit: "K25x50", grup: "G1" });
  assert.equal(r.model.kolonlar[0].grup, "G1"); assert.equal(r.model.surum, 1); assert.equal(BC.genelMi(r.model), false);
  assert.equal(BC.aksKatOzellikYaz(r.model, [{ tur: "kolon", no: 1 }], { grup: null }).model.kolonlar[0].grup, undefined, "boş grup kaldırılır");
  r = BC.aksKatOzellikYaz(b, [{ tur: "kiris", no: 1 }], { duvar_h: 2.5 });
  assert.equal(r.model.kirisler[0].duvar_h, 2.5); assert.equal(r.model.surum, 1); assert.equal(BC.genelMi(r.model), false);
  assert.equal(BC.aksKatOzellikYaz(r.model, [{ tur: "kiris", no: 1 }], { duvar_h: "" }).model.kirisler[0].duvar_h, undefined, "boş = kat yüksekliği");
  // karışık seçimde duvar alanları yalnız kirişe yazılır; kolon tek başına duvar alamaz; geçersiz yükseklik genel yola düşer
  r = BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }, { tur: "kiris", no: 1 }], { duvar_h: 1.5, grup: "G2" });
  assert.equal(r.sayi, 2); assert.equal(r.model.kirisler[0].duvar_h, 1.5); assert.equal(r.model.kolonlar[0].duvar_h, undefined);
  assert.equal(r.model.kolonlar[0].grup, "G2"); assert.equal(r.model.kirisler[0].grup, "G2");
  assert.equal(BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }], { duvar_h: 2 }), null);
  assert.equal(BC.aksKatOzellikYaz(b, [{ tur: "kiris", no: 1 }], { duvar_h: -1 }), null);
  r = BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }], { aci: 90 });
  assert.equal(r.model.kolonlar[0].yon, "y");
  assert.equal(BC.aksKatOzellikYaz(r.model, [{ tur: "kolon", no: 1 }], { aci: 180 }).model.kolonlar[0].yon, "x");
  r = BC.aksKatOzellikYaz(b, [{ tur: "kiris", no: 1 }], { duvar: "tugla19" });
  assert.equal(r.model.kirisler[0].duvar, "tugla19");
  assert.equal(BC.aksKatOzellikYaz(r.model, [{ tur: "kiris", no: 1 }], { duvar: null }).model.kirisler[0].duvar, null);
  assert.equal(BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }], { aci: 30 }), null);
  assert.equal(BC.aksKatOzellikYaz(b, [{ tur: "kiris", no: 1 }], { aci: 90 }), null);
  assert.equal(BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }], { duvar: "tugla19" }), null);
  assert.equal(BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }], { yalniz_cekme: true }), null);
  assert.equal(BC.aksKatOzellikYaz(b, [{ tur: "kolon", no: 1 }, { tur: "cubuk", no: 3 }], { kesit: "K25x50" }), null);
  assert.equal(BC.aksKatOzellikYaz(b, [], { kesit: "K25x50" }), null);
});

test("Düzlemle böl (NEW-5): yalnız seçimi iç noktasından kesen aks düzlemleri sunulur; aks–kat kirişini hiçbir aks düzlemi kesmez", function () {
  const g = BC.genellestirHazirla(aksKatModel()).model;
  const k1 = BC.genelSecim(g, [{ tur: "kiris", no: 1 }]).map(function (s) { return s.no; });
  assert.ok(k1.length >= 2, "A1–C1 kirişi B aksında parçalı");
  assert.deepEqual(BC.kesenDuzlemler(g, k1), [], "X aksı A / B / C parçaların uçlarından geçer: bölünecek yer yok");
  // ModelOps.duzlemleBol da aynı: kesmeyen düzlem hiçbir şey eklemez
  const r = O.duzlemleBol(g, k1, { X: 0 });
  assert.equal(BC.ozet(r), ""); assert.equal(JSON.stringify(r.model), JSON.stringify(g));
  // eğik çubuk A1/kat 1 → C2/kat 2: yalnız X aksı B (5 m) iç noktasından keser
  const m = JSON.parse(JSON.stringify(g));
  m.cubuklar.push({ no: 99, i: { aks: ["A", "1"], kat: 1 }, j: { aks: ["C", "2"], kat: 2 }, tur: "capraz" });
  assert.deepEqual(BC.kesenDuzlemler(m, [99]), [{ yon: "x", ad: "B", konum: 5, sayi: 1 }]);
  assert.equal(O.duzlemleBol(m, [99], { X: 5 }).eklenen.cubuklar.length, 1);
});

test("ileti çevirisi: genelleştirilmiş modelde çubuk numarasına aks–kat adresi eklenir", function () {
  const g = BC.genellestirHazirla(aksKatModel()).model;
  const k1 = g.cubuklar.filter(function (c) { return c.kaynak.aks_kat === "kiris" && c.kaynak.no === 1; });
  const kol = g.cubuklar.find(function (c) { return c.kaynak.aks_kat === "kolon" && c.kaynak.no === 3; });
  assert.equal(k1.length, 2);
  assert.equal(BC.cubukAksKatAdi(g, k1[1].no), "kiriş 1, 2. parça");
  assert.equal(BC.cubukAksKatAdi(g, kol.no), "kolon 3");
  assert.equal(BC.cubukAdlari(g, "Çubuk " + k1[0].no + ", " + kol.no + " birleştirilemedi; çubuk 999 yok."),
    "Çubuk " + k1[0].no + " (kiriş 1, 1. parça), " + kol.no + " (kolon 3) birleştirilemedi; çubuk 999 yok.");
  assert.equal(BC.cubukAdlari(bos(), "Çubuk 3 ve 4"), "Çubuk 3 ve 4");
});

test("yeni engeller: işlemin ürettiği sıfır boylu / çakışan çubuk ve bozuk panel; önceden var olanlar sayılmaz", function () {
  let m = bos();
  m = cubukEkle(m, G("A", "1", "+3.00"), G("B", "1", "+3.00"));
  assert.deepEqual(BC.yeniEngeller(m, m), []);
  const s = cubukEkle(m, G("A", "1", "+3.00"), G("B", "1", "+3.00"));
  const e = BC.yeniEngeller(m, s);
  assert.deepEqual(e.map(function (u) { return u.kod; }), ["cakisan-cubuk"]);
  assert.deepEqual(BC.yeniEngeller(s, s), [], "zaten var olan bulgu yeni sayılmaz");
  const z = cubukEkle(m, G("C", "1", "+3.00"), G("C", "1", "+3.00"));
  assert.deepEqual(BC.yeniEngeller(m, z).map(function (u) { return u.kod; }), ["sifir-boy"]);
  // bulgunun kimliği eleman(lar)dır, ileti değil: aynı çubuk çiftinin üst üste binmesi biçim değiştirse de yeni sayılmaz
  const u1 = cubukEkle(m, G("A", "1", "+3.00"), G("C", "1", "+3.00"));          // 1–2 eş doğrusal, üst üste (6 m)
  const u2 = JSON.parse(JSON.stringify(u1)); u2.cubuklar[0].j = G("C", "1", "+3.00");   // 1–2 artık aynı iki düğüm (12 m)
  assert.notEqual(BC.yeniEngeller(m, u1)[0].mesaj, BC.yeniEngeller(m, u2)[0].mesaj);
  assert.deepEqual(BC.yeniEngeller(u1, u2), []);
});

test("aks sil kapısı (ui-s3-13): yeni sıfır boy / çakışan çubuk / eksik düğüm ve çözümlenemeyen model engeldir; önceden bozuk olan sayılmaz", function () {
  const m = BC.genellestirHazirla(aksKatModel()).model;
  assert.deepEqual(BC.aksSilEngelleri(m, m), []);
  const s = JSON.parse(JSON.stringify(m));
  s.cubuklar[0].j = JSON.parse(JSON.stringify(s.cubuklar[0].i));                                   // sıfır boylu
  assert.deepEqual(BC.aksSilEngelleri(m, s).map(function (u) { return u.kod; }), ["sifir-boy"]);
  const e = JSON.parse(JSON.stringify(m));
  e.cubuklar[0].j = { dugum: 199999 };                                                           // olmayan düğüm
  const ee = BC.aksSilEngelleri(m, e);
  assert.ok(ee.length && ee.every(function (u) { return u.kod === "eksik-dugum"; }), JSON.stringify(ee));
  const k = JSON.parse(JSON.stringify(m)), r = k.cubuklar[0].i, q = k.cubuklar[0].j;
  k.dugumler = [{ no: 100001, tur: "kesisim", a: [r, q], b: [r, q] }];                           // paralel doğrular: denetim çözümleyemez
  k.cubuklar.push({ no: 999, i: r, j: { dugum: 100001 }, tur: "capraz" });
  assert.deepEqual(BC.aksSilEngelleri(m, k).map(function (u) { return u.kod; }), ["cozulemez"]);
  assert.deepEqual(BC.aksSilEngelleri(k, k), [], "önceden de çözümlenemiyorsa aks silmeyi engellemez");
});

test("taşıyan kenar: panel kenarı bulgusu dağıtıma göre motorun reddettiği kenarda mı (iki, tek-13, tek-24, yok, otomatik)", function () {
  // A1–B1–B2–A2 gözü (6 × 5) +3.00'te; 1. kenar A1–B1 çubuksuz
  let m = bos();
  m = cubukEkle(m, G("B", "1", "+3.00"), G("B", "2", "+3.00"));
  m = cubukEkle(m, G("B", "2", "+3.00"), G("A", "2", "+3.00"));
  m = cubukEkle(m, G("A", "2", "+3.00"), G("A", "1", "+3.00"));
  m.paneller = [{ no: 1, kose: [G("A", "1", "+3.00"), G("B", "1", "+3.00"), G("B", "2", "+3.00"), G("A", "2", "+3.00")], kalinlik: 0.12, dagitim: "iki" }];
  const bul = function (mm) { return O.denetle(mm).uyarilar.filter(function (u) { return u.kod === "panel-kenari"; }); };
  const u = bul(m);
  assert.equal(u.length, 1); assert.equal(u[0].kenar, 1);
  const dag = function (d) { const k = JSON.parse(JSON.stringify(m)); k.paneller[0].dagitim = d; return BC.tasiyanKenarMi(k, u[0]); };
  assert.equal(dag("iki"), true);
  assert.equal(dag("tek-13"), true);
  assert.equal(dag("tek-24"), false);
  assert.equal(dag("yok"), false);
  assert.equal(dag("otomatik"), true, "6 / 5 ≤ 2 → iki doğrultulu: bütün kenarlar taşır");
  assert.equal(dag("tek"), true, "tek: uzun kenarlar (1. ve 3., 6 m) taşır");
  assert.equal(BC.tasiyanKenarMi(m, { kod: "sifir-boy", panel: 1, kenar: 1 }), false);
});

// ------------------------------------------------------------------ kesit önerisi (C4)
test("kesit önerisi: IPE, BORU, KUTU, betonarme, vute ve C4 uygula; kesitler'de olmayan ad asla atanmaz", function () {
  const m = { tur: "bina", surum: 3, sistem: "celik", malzemeler: { S275: { kutuphane: "S275" } },
    kesitler: { "CAPRAZ-V": { tip: "profil", profil: "BORU 88.9x3.2", malzeme: "S275" }, MERTEK: { tip: "profil", profil: "IPE 400", malzeme: "S355" },
      VUTE: { tip: "vute", temel: "MERTEK", ek_yukseklik: 0.4, boy: 2 }, KIRIS: { tip: "profil", profil: "IPE 300", malzeme: "S275" } },
    cubuklar: [{ no: 32, tur: "capraz", kesit: "CAPRAZ-V" }, { no: 8, tur: "kiris", kesit: "VUTE" }, { no: 5, tur: "kiris", kesit: "KIRIS" }] };
  const gecerli = function (model, ad) {
    const k = model.kesitler[ad];
    assert.ok(k, "kesit " + ad + " tanımlı");
    if (k.tip === "profil") assert.ok(k.profil && k.malzeme && model.malzemeler[k.malzeme], ad);
    if (k.tip === "vute") assert.ok(model.kesitler[k.temel] && model.kesitler[k.temel].tip === "profil", "vute temeli " + k.temel);
    if (k.tip === "dikdortgen") assert.ok(k.b > 0 && k.h > 0, ad);
  };
  // çelik BORU (eski motor: uygula yok, sistem verilmemiş): ad boşluksuz, profil adı boşluklu
  let o = { cubuk: 32, tur: "capraz", kesit: "CAPRAZ-V", oneri: "BORU 168.3x6.3", degisim: "büyüt" };
  let r = BC.oneriUygula(m, o, { tur: "cubuk", no: 32 });
  assert.equal(r.ad, "BORU168.3x6.3"); gecerli(r.model, r.ad);
  assert.equal(r.model.kesitler[r.ad].profil, "BORU 168.3x6.3");
  assert.equal(r.model.cubuklar[0].kesit, r.ad);
  // KUTU, sistem çelik
  r = BC.oneriUygula(m, { cubuk: 32, tur: "capraz", kesit: "CAPRAZ-V", oneri: "KUTU 100x100x5", sistem: "celik", malzeme: "S355", degisim: "büyüt" }, null);
  assert.equal(r.ad, "KUTU100x100x5"); gecerli(r.model, r.ad); assert.equal(r.model.kesitler[r.ad].malzeme, "S355");
  // IPE kiriş
  r = BC.oneriUygula(m, { cubuk: 5, tur: "kiris", kesit: "KIRIS", oneri: "IPE 330", sistem: "celik", degisim: "büyüt" }, null);
  assert.equal(r.ad, "IPE330"); gecerli(r.model, r.ad);
  // vute: temel profil değişen yeni vute kartı, tip vute korunur
  r = BC.oneriUygula(m, { cubuk: 8, tur: "kiris", kesit: "VUTE", oneri: "IPE 330", sistem: "celik", malzeme: "S355", degisim: "küçült" }, null);
  assert.equal(r.ad, "VUTE-IPE330");
  assert.equal(r.model.kesitler["VUTE-IPE330"].tip, "vute"); assert.equal(r.model.kesitler["VUTE-IPE330"].temel, "IPE330");
  assert.equal(r.model.kesitler["VUTE-IPE330"].ek_yukseklik, 0.4); gecerli(r.model, r.ad);
  assert.equal(r.model.cubuklar[1].kesit, "VUTE-IPE330");
  // betonarme: b, h (m) → B30x50; dizgeden de
  const rc = { tur: "bina", surum: 1, kesitler: { S40x40: { tip: "dikdortgen", b: 0.4, h: 0.4, malzeme: "C30", donati: "B420C" } },
    kolonlar: [{ no: 2, aks: ["A", "1"], kat: 1, kesit: "S40x40" }], kirisler: [] };
  r = BC.oneriUygula(rc, { cubuk: 7, tur: "kolon", kesit: "S40x40", oneri: "30x30", sistem: "betonarme", b: 0.3, h: 0.3, malzeme: "C30", degisim: "küçült", kaynak: { aks_kat: "kolon", no: 2 } }, null);
  assert.equal(r.ad, "B30x30"); gecerli(r.model, r.ad);
  assert.equal(r.model.kesitler.B30x30.donati, "B420C", "donatı eski karttan");
  assert.equal(r.model.kolonlar[0].kesit, "B30x30", "aks–kat kolonuna yazıldı (kaynak)"); assert.deepEqual(r.hedef, { tur: "kolon", no: 2 });
  r = BC.oneriUygula(rc, { cubuk: 7, tur: "kolon", kesit: "S40x40", oneri: "35x45", degisim: "küçült" }, { tur: "kolon", no: 2 });
  assert.equal(r.ad, "B35x45"); assert.equal(r.model.kolonlar[0].kesit, "B35x45", "kaynak yoksa tıklanan hedef");
  // C4 uygula: {ad, tanim, yeni, ek_kesitler}
  r = BC.oneriUygula(m, { cubuk: 8, tur: "kiris", kesit: "VUTE", oneri: "IPE 360", sistem: "celik", degisim: "küçült",
    uygula: { ad: "VUTE-IPE360", tanim: { tip: "vute", temel: "IPE360", ek_yukseklik: 0.4, boy: 2 }, yeni: true, ek_kesitler: { IPE360: { tip: "profil", profil: "IPE 360", malzeme: "S275" } } } }, null);
  assert.equal(r.ad, "VUTE-IPE360"); gecerli(r.model, r.ad);
  // değişiklik yok / öneri yok / tanımsız ad → hata, model değişmez
  assert.throws(function () { BC.oneriUygula(m, { cubuk: 32, kesit: "CAPRAZ-V", oneri: "BORU 88.9x3.2", degisim: "aynı" }, null); }, /aynı/);
  assert.throws(function () { BC.oneriUygula(m, { cubuk: 32, kesit: "CAPRAZ-V", oneri: null }, null); }, /öneri yok/);
  assert.throws(function () { BC.oneriUygula(m, { cubuk: 32, kesit: "CAPRAZ-V", oneri: "X", degisim: "büyüt", uygula: { ad: "YOK", yeni: false } }, null); }, /tanımı gelmedi/);
  assert.throws(function () { BC.oneriUygula(m, { cubuk: 99, kesit: "KIRIS", oneri: "IPE 330", sistem: "celik", degisim: "büyüt" }, null); }, /modelde yok/);
  assert.throws(function () { BC.oneriUygula(rc, { cubuk: 7, kesit: "S40x40", oneri: "?", sistem: "betonarme", degisim: "büyüt" }, null); }, /okunamadı/);
  // Uygula düğmesi koşulu ve satır etiketi
  assert.equal(BC.oneriUygulanir({ oneri: "BORU 168.3x6.3", kesit: "CAPRAZ-V", degisim: "aynı" }), false);
  assert.equal(BC.oneriUygulanir({ oneri: "IPE 330", kesit: "VUTE", degisim: "küçült", uygula: null }), false);
  assert.equal(BC.oneriUygulanir({ oneri: "IPE 330", kesit: "IPE330", degisim: "büyüt" }), false);
  assert.equal(BC.oneriUygulanir({ oneri: "IPE 330", kesit: "KIRIS", degisim: "büyüt" }), true);
  assert.equal(BC.oneriEtiketi({ cubuk: 21, tur: "kiris", kaynak: { aks_kat: "kiris", no: 9 } }), "kiriş 9");
  assert.equal(BC.oneriEtiketi({ cubuk: 32, tur: "capraz", kaynak: null }), "Ç32 (çapraz)", "C18 (eski beklenti ham tür 'capraz 32' idi)");
});

test("kesit önerisi K1: donatı değişimi uygulanır (uygula.ad ile karşılaştırma), satır uygula.ad ve tahmini D/C gösterir; Hepsini özeti", function () {
  // "donatı": b × h aynı, gerekli ρ büyük → uygula.ad "B30x30-ρ%2.00" (kesit "30x30" adlı olsa da öneri adı farklıdır)
  const don = { cubuk: 1, tur: "kolon", kesit: "30x30", oneri: "30x30", sistem: "betonarme", b: 0.3, h: 0.3, degisim: "donatı", dc_once: 1.65, dc_oneri: 0.98, dc_sonra: 0.98,
    kaynak: { aks_kat: "kolon", no: 1 }, uygula: { ad: "B30x30-ρ%2.00", tanim: { tip: "dikdortgen", b: 0.3, h: 0.3, malzeme: "C30", donati: "B420C", donati_orani: 0.02 }, yeni: true } };
  assert.equal(BC.oneriUygulanir(don), true, "eski kural (oneri ≡ kesit) donatı önerisini gizliyordu");
  assert.equal(BC.oneriAdi(don), "B30x30-ρ%2.00");
  const rc = { tur: "bina", surum: 1, kesitler: { "30x30": { tip: "dikdortgen", b: 0.3, h: 0.3, malzeme: "C30", donati: "B420C" } }, kolonlar: [{ no: 1, aks: ["A", "1"], kat: 1, kesit: "30x30" }], kirisler: [] };
  const r = BC.oneriUygula(rc, don, null);
  assert.equal(r.ad, "B30x30-ρ%2.00");
  assert.equal(r.model.kolonlar[0].kesit, "B30x30-ρ%2.00");
  assert.equal(r.model.kesitler["B30x30-ρ%2.00"].donati_orani, 0.02);
  // uygula.ad mevcut kesitle aynıysa (motor zaten bu kartı önerdi) değişiklik yok
  assert.equal(BC.oneriUygulanir(Object.assign({}, don, { kesit: "B30x30-ρ%2.00" })), false);
  assert.equal(BC.oneriUygulanir(Object.assign({}, don, { uygula: null })), false, "motor uygula: null → uygulanmaz");
  assert.equal(BC.oneriUygulanir(Object.assign({}, don, { degisim: "aynı" })), false);
  // satır: uygula.ad, öneri ayraçta; D/C tahmini (mevcut iç kuvvetlerle); yeniden çözümde "yeniden çözümle" ve dc_sonra
  const st = BC.oneriSatiri(don, false);
  assert.equal(st.ad, "B30x30-ρ%2.00"); assert.equal(st.oneri, "30x30");
  assert.equal(st.dc, "1,65 → 0,98"); assert.equal(st.dcEtiket, "tahmini (mevcut iç kuvvetlerle)");
  const ct = BC.oneriSatiri({ kesit: "CAPRAZ-X", oneri: "BORU 168.3x6.3", dc_once: 18.4, dc_oneri: 0.64, dc_sonra: 1.36, uygula: { ad: "BORU168.3x6.3" } }, true);
  assert.equal(ct.oneri, "", "boşluk farkı ayrı yazılmaz"); assert.equal(ct.dc, "18,40 → 1,36"); assert.equal(ct.dcEtiket, "yeniden çözümle");
  // Hepsini özeti: dc_sonra > 1 → aşan çubuklar (büyükten küçüğe)
  const oz = BC.hepsiOzeti({ dc_sonra: 1.07, oneriler: [{ cubuk: 7, tur: "kolon", kaynak: { aks_kat: "kolon", no: 7 }, dc_sonra: 1.05 },
    { cubuk: 12, tur: "capraz", dc_sonra: 1.07 }, { cubuk: 3, tur: "kiris", dc_sonra: 0.9 }] });
  assert.equal(oz.asiyor, true); assert.equal(oz.dc, 1.07);
  assert.deepEqual(oz.asan, [{ etiket: "Ç12 (çapraz)", dc: 1.07 }, { etiket: "kolon 7", dc: 1.05 }]);
  assert.deepEqual(BC.hepsiOzeti({ dc_sonra: 0.99, oneriler: [{ cubuk: 1, dc_sonra: 0.99 }] }), { dc: 0.99, asan: [], asiyor: false });
  assert.equal(BC.hepsiOzeti({}).asiyor, false);
  // yinele yanıtının yeni uyarıları (motor: öteleme sınırı, yakınsamadı) — ilk yanıtta olanlar tekrar edilmez; aşanları arayüz listeler
  const ilk = { uyarilar: ["D/C önce, aks–kat motorunun tasarım tablosundan (görünen çözüm); öneri ve D/C sonra genel model motoruyla."] };
  const ikinci = { uyarilar: ilk.uyarilar.concat(["Kesit önerileri 3 turda yakınsamadı: kolon 7 (1,05) — son çözümde D/C > 1.", "Önerilen kesitlerle göreli kat ötelemesi sınırı (TBDY 2018 md. 4.9.1) aşılıyor: X yönü kat 1, 2."]) };
  const eu = BC.hepsiEkUyarilari(ikinci, ilk);
  assert.equal(eu.tum.length, 2);
  assert.deepEqual(eu.diger, [ikinci.uyarilar[2]]);
  assert.deepEqual(BC.hepsiEkUyarilari({}, null), { tum: [], diger: [] });
  // D/C metni 1'e çok yakınken "1,00 > 1" gibi çelişkili görünmez
  assert.equal(BC.dcFmt(0.9963), "0,996"); assert.equal(BC.dcFmt(1.004), "1,004"); assert.equal(BC.dcFmt(1), "1,00"); assert.equal(BC.dcFmt(1.36), "1,36");
  // çözüm verisinde elemanın D/C'si: genel model (cubuk), aks–kat (tur, no) ve genelleştirilmiş kaynağı
  const v = { tasarim: { elemanlar: [{ cubuk: 41, tur: "capraz", dc: 1.32 }, { tur: "kolon", no: 2, dc: 0.4 }, { cubuk: 9, tur: "kiris", kaynak: { aks_kat: "kiris", no: 3 }, dc: 0.7 }, { cubuk: 10, tur: "kiris", kaynak: { aks_kat: "kiris", no: 3 }, dc: 0.8 }] } };
  assert.equal(BC.elemanDc(v, { tur: "cubuk", no: 41 }), 1.32);
  assert.equal(BC.elemanDc(v, { tur: "kolon", no: 2 }), 0.4);
  assert.equal(BC.elemanDc(v, { tur: "kiris", no: 3 }), 0.8, "parçalı kirişin en büyüğü");
  assert.equal(BC.elemanDc(v, { tur: "cubuk", no: 99 }), null);
  assert.equal(BC.elemanDc(null, { tur: "cubuk", no: 41 }), null);
});

// ------------------------------------------------------------------ üreteç düzenleme
test("üreteç düzenle: kayıt bulma ve pencere başlangıç değerleri (makas, beşik, aşık, kren, çapraz)", function () {
  let m = bos();
  for (const x of ["A", "C"]) m = cubukEkle(m, G(x, "1", "±0.00"), G(x, "1", "+3.00"), { tur: "kolon" });
  const mk = O.makasUret(m, { tip: "pratt", bas: G("A", "1", "+3.00"), son: G("C", "1", "+3.00"), yukseklik: 1.5, goz: 4, kesitler: { ust: "HEA300" } });
  const k = BC.uretecKaydi(mk.model, { tur: "cubuk", no: mk.model.cubuklar.find(function (c) { return c.kaynak && c.kaynak.uretec; }).no });
  assert.equal(k.tur, "makas");
  assert.equal(BC.uretecKaydi(mk.model, 1), k);
  assert.equal(BC.uretecKaydi(mk.model, { tur: "cubuk", no: 1 }), null, "üreteçsiz çubuk");
  const f = BC.uretecFormu(mk.model, k);
  assert.deepEqual([f.tur, f.tip, f.xa, f.xb, f.y0, f.z, f.h, f.goz, f.ust, f.mafsal], ["makas", "pratt", "A", "C", "1", "+3.00", "1.5", "4", "HEA300", true]);
  // beşik çerçeve: mutlak saçak / mahya kotu
  const bp = BC.besikPlan(bos(), { acikliklar: [["A", "C"]], y: ["1", "2"], taban: "±0.00", sacak: 3, mahya: 4.5, kesitler: { kolon: "HEA300", mertek: "IPE300" }, asik: { aralik: 2 }, mesnet: "mafsal" });
  const bc = O.besikCerceveUret(bp.model, bp.parametreler[0]);
  const fb = BC.uretecFormu(bc.model, BC.uretecKaydi(bc.model, bc.uretec));
  assert.deepEqual([fb.kx, fb.y0, fb.y1, fb.taban, fb.sacak, fb.mahya, fb.mesnet, fb.asik, fb.kolon], [["A", "C"], "1", "2", "±0.00", "3", "4.5", "mafsal", true, "HEA300"]);
  // kren yolu, aşık ve çapraz
  const kr = { tur: "kren-yolu", no: 5, kolonlar: [[1, 2], [3, 4]], kot: 4.5, konsol_boy: 0.5, kesitler: { kiris: "HEB400" }, kren: { tekerlek: { P_maks: 80, P_min: 25, H_yanal: 8, H_fren: 6, aralik: 3.5 }, dinamik: 1.25 } };
  const fk = BC.uretecFormu(bos(), kr);
  assert.deepEqual([fk.kot, fk.konsol, fk.kiris, fk.Pmaks, fk.din, fk.hatSayisi], ["4.5", "0.5", "HEB400", "80", "1.25", 2]);
  assert.deepEqual(BC.uretecFormu(bos(), { tur: "asik", hedef: [3, 4], aralik: 1.5, kesit: "IPE200", secenek: { uclar: false } }),
    { tur: "asik", aralik: "1.5", kesit: "IPE200", uclar: false, mafsal: true, hedefMetin: "2 mertek çubuğu" });
  assert.equal(BC.uretecFormu(bos(), { tur: "capraz", tip: "V", secenek: { kesit: "L", mafsalli_uclar: false } }).mafsal, false);
  assert.ok(BC.uretecFormu(bos(), { tur: "cephe-kirisi" }).hata);
  assert.ok(BC.uretecFormu(bos(), { tur: "makas", bas: { dugum: 100001 }, son: { dugum: 100002 } }).hata, "aks adresiyle yazılmamış uç");
});

// ------------------------------------------------------------------ K-23: genel model kapısının işlem adları
test("K-23 kapı metni: her komutun ön eki işlem adıdır (geçmiş zamanlı sonuç etiketi değil); ad verilmezse ön ek yok", function () {
  const adlar = BC.GENEL_ISLEM_ADLARI;
  assert.ok(Object.isFrozen(adlar));
  ["tasi", "dondur", "ayna", "bol", "birlestir", "mafsal", "dugum-birlestir", "mesnet", "yuk-ata", "yapistir", "dogrusal-dizi", "uretec"].forEach(function (k) { assert.ok(adlar[k], k); });
  assert.deepEqual([adlar.tasi, adlar.dondur, adlar.ayna, adlar.bol, adlar.birlestir, adlar.mafsal, adlar["dugum-birlestir"], adlar.mesnet, adlar["yuk-ata"], adlar.yapistir, adlar["dogrusal-dizi"], adlar.uretec],
    ["Taşıma", "Döndürme", "Ayna", "Böl", "Birleştirme", "Mafsal", "Düğüm birleştir", "Mesnet", "Yük ata", "Yapıştır", "Dizi", "Üreteç"]);
  const b = aksKatModel();
  Object.keys(adlar).forEach(function (k) {
    const t = BC.genelGecisMetni(b, adlar[k]);
    const on = t.split(" — ")[0];
    assert.equal(on, adlar[k], k);
    // -dı/-di/-du/-dü/-tı/-ti… ya da -ldı ile biten (geçmiş zaman) ön ek yok: "Taşındı", "Birleştirildi", "Üreteç güncellendi"
    assert.doesNotMatch(on, /[dt][ıiuü]$/i, k + ": " + on);
  });
  ["Taşındı", "Birleştirildi", "Üreteç güncellendi (Makas)", "Döndürüldü (90°)"].forEach(function (eski) {
    assert.match(eski.replace(/\s*\(.*\)$/, ""), /[dt][ıiuü]$/i, "denetim deseni eski etiketleri yakalar: " + eski);
  });
  assert.equal(BC.genelGecisMetni(b, null).indexOf(" — "), -1);
});

// ------------------------------------------------------------------ K-24: ayraçlı çubuk listeleri
test("K-24 cubukAdlari: 'çubuk … (3, 9, 18)' ayraçlı listesindeki her numara aks–kat adını alır; ondalık ve birimli ayraç dokunulmaz", function () {
  const g = BC.genellestirHazirla(aksKatModel()).model;
  const ad = function (no) { return BC.cubukAksKatAdi(g, no); };
  const nolar = g.cubuklar.slice(0, 3).map(function (c) { return c.no; });
  const m = "ara düğüm 1001'e başka çubuk bağlı (" + nolar.join(", ") + ")";
  assert.equal(BC.cubukAdlari(g, m), "ara düğüm 1001'e başka çubuk bağlı (" + nolar.map(function (n) { return n + " (" + ad(n) + ")"; }).join(", ") + ")");
  assert.ok(nolar.every(function (n) { return ad(n); }), "aks–kat adları var");
  const u = "Üreteç 2 silinirken bölünen çubuklar (" + nolar[0] + ", " + nolar[1] + ") yeniden birleştirilemedi";
  assert.match(BC.cubukAdlari(g, u), new RegExp("\\(" + nolar[0] + " \\(" + ad(nolar[0]).replace(/[.()]/g, "\\$&") + "\\), " + nolar[1] + " \\("));
  // ilk desen (Çubuk 13, 14) eskisi gibi; iki desen birlikte de çift ek yapmaz
  const t = BC.cubukAdlari(g, "Çubuk " + nolar[0] + " sıfır boylu (0,50 mm); çubuk listesi (" + nolar[2] + ")");
  assert.equal(t, "Çubuk " + nolar[0] + " (" + ad(nolar[0]) + ") sıfır boylu (0,50 mm); çubuk listesi (" + nolar[2] + " (" + ad(nolar[2]) + "))");
  assert.equal(BC.cubukAdlari(g, "çubuk boyundan (0,5)"), "çubuk boyundan (0,5)", "ondalık sayı liste değil");
  assert.equal(BC.cubukAdlari(bos(), "başka çubuk bağlı (3, 9, 18)"), "başka çubuk bağlı (3, 9, 18)", "aks–kat kaynağı yoksa aynen");
});

// ------------------------------------------------------------------ K-25: öneri etiketleri (C18)
test("K-25 / C18 öneri etiketi: 11 türün Türkçe adı 'Ç{no} ({ad})'; aks–kat kaynağı 'kiriş 3' / 'kolon 2'; tasarım kaydı etiketi", function () {
  const beklenen = { kolon: "kolon", kiris: "kiriş", capraz: "çapraz", "makas-ust": "makas üst başlık", "makas-alt": "makas alt başlık", "makas-dikme": "makas dikmesi",
    "makas-diyagonal": "makas diyagonali", asik: "aşık", kren: "kren kirişi", bag: "bağ", diger: "diğer" };
  assert.deepEqual(Object.assign({}, BC.TUR_ADI), beklenen);
  Object.keys(beklenen).forEach(function (t, i) { assert.equal(BC.oneriEtiketi({ cubuk: 30 + i, tur: t }), "Ç" + (30 + i) + " (" + beklenen[t] + ")"); });
  assert.equal(BC.oneriEtiketi({ cubuk: 8, tur: "kiris" }), "Ç8 (kiriş)");
  assert.equal(BC.oneriEtiketi({ cubuk: 5, tur: "makas-ust" }), "Ç5 (makas üst başlık)");
  assert.equal(BC.oneriEtiketi({ cubuk: 21, tur: "kiris", kaynak: { aks_kat: "kiris", no: 3 } }), "kiriş 3");
  assert.equal(BC.oneriEtiketi({ cubuk: 7, tur: "kolon", kaynak: { aks_kat: "kolon", no: 2 } }), "kolon 2");
  assert.equal(BC.oneriEtiketi({ cubuk: 9 }), "Ç9");
  assert.equal(BC.oneriEtiketi({ cubuk: 9, tur: "yeni-tur" }), "Ç9 (yeni-tur)");
  assert.equal(BC.oneriEtiketi(null), "çubuk");
  ["capraz 32", "kiris 8"].forEach(function (eski) { assert.notEqual(BC.oneriEtiketi({ cubuk: +eski.split(" ")[1], tur: eski.split(" ")[0] }), eski); });
  assert.equal(BC.tasarimEtiketi({ cubuk: 41, tur: "capraz", dc: 1.3 }), "Ç41 (çapraz)");
  assert.equal(BC.tasarimEtiketi({ tur: "kolon", no: 2, dc: 1.1 }), "kolon 2");
  assert.equal(BC.tasarimEtiketi({ cubuk: 9, tur: "kiris", kaynak: { aks_kat: "kiris", no: 3 } }), "kiriş 3");
  assert.equal(BC.tasarimEtiketi({ ad: "Ç4 (bağ)", cubuk: 4, tur: "bag" }), "Ç4 (bağ)");
});

// ------------------------------------------------------------------ K-10: yaylı mesnet ön ayarı (C13)
test("K-10 yaylı mesnet: ön ayar, pencere değerleri (boş / ≤ 0 yazılmaz), kayıt yalnız yay anahtarları; sabit mesnetten yaya geçişte çakışan boolean kalkar", function () {
  assert.equal(BC.MESNET_ON_AYAR.yay.ad, "Yaylı (elastik)");
  assert.deepEqual(BC.YAY_ANAHTARLARI.map(function (y) { return y.etiket; }), ["k_x (kN/m)", "k_y (kN/m)", "k_z (kN/m)", "k_rx (kN·m/rad)", "k_ry (kN·m/rad)", "k_rz (kN·m/rad)"]);
  assert.deepEqual(Object.assign({}, BC.YAY_VARSAYILAN), { kz: 10000 }, "yalnız k_z dolu");
  assert.deepEqual(BC.yayDegerleri({ kx: "", ky: "-5", kz: "10000", krx: "0", kry: "2,5", krz: "abc" }), { kz: 10000, kry: 2.5 });
  assert.throws(function () { BC.yayDegerleri({ kx: "", kz: "0", krz: "-1" }); }, /en az bir yay rijitliği/);
  const m = bos();
  let r = BC.mesnetAta(m, G("A", "1", "±0.00"), "yay", { yay: { kz: 10000 } });
  assert.equal(r.eylem, "eklendi");
  assert.deepEqual(r.model.mesnetler[0], { dugum: G("A", "1", "±0.00"), kz: 10000 }, "boolean yok, yalnız verilen yay");
  r = BC.mesnetAta(m, G("A", "1", "±0.00"), "yay");
  assert.deepEqual(r.model.mesnetler[0], { dugum: G("A", "1", "±0.00"), kz: 10000 }, "varsayılan k_z = 10000");
  // ankastre mesnet yaya çevrilir: yaylı yönlerin (uz, ry) boolean'ı kalkar, ötekiler korunur (C13: bir yön hem tutulu hem yaylı olamaz)
  const a = BC.mesnetAta(m, G("B", "2", "±0.00"), "ankastre").model;
  r = BC.mesnetAta(a, G("B", "2", "±0.00"), "yay", { yay: { kz: 5000, kry: 800 } });
  assert.equal(r.eylem, "degisti");
  assert.deepEqual(r.model.mesnetler, [{ dugum: G("B", "2", "±0.00"), ux: true, uy: true, rx: true, rz: true, kz: 5000, kry: 800 }]);
  ["ux", "uy", "uz", "rx", "ry", "rz"].forEach(function (yon) { const y = BC.YAY_ANAHTARLARI.find(function (q) { return q.yon === yon; }); const s = r.model.mesnetler[0]; assert.ok(!(s[yon] && s[y.a] != null), yon + " hem tutulu hem yaylı değil"); });
  // yaydan sabit mesnete dönüş: yay anahtarları kalkar
  const g = BC.mesnetAta(r.model, G("B", "2", "±0.00"), "mafsal").model;
  assert.deepEqual(g.mesnetler[0], { dugum: G("B", "2", "±0.00"), ux: true, uy: true, uz: true, rx: false, ry: false, rz: false });
  // aks–kat modelinde aynı yol: model genelleştirilir (temeller aynen)
  const k = BC.mesnetAta(aksKatModel("radye"), { aks: ["B", "2"], kat: 0 }, "yay", { yay: { kz: 20000 } });
  assert.equal(k.genellesti, true); assert.equal(k.model.temeller.tip, "radye");
  assert.deepEqual(Object.keys(k.model.mesnetler[0]).sort(), ["dugum", "kz"]);
  assert.throws(function () { BC.mesnetAta(m, G("A", "1", "±0.00"), "yay", { yay: { kz: 0 } }); }, /en az bir yay/);
});

// ------------------------------------------------------------------ K-15: rijit diyafram sorusu (C14)
/** Depremli aks–kat modeli: döşemeler (h 0,14) kat 1 ve 2'de → genelleştirilince kalınlıklı paneller. */
function depremli(ek) { return Object.assign(aksKatModel(), { deprem: { etkin: true, SS: 1, S1: 0.3, zemin_sinifi: "ZC" } }, ek || {}); }

test("K-15 diyafram biçimi (yapi_serbest._diyafram_modu): rijit / esnek / en alt seviye / deprem yok; analiz.diyafram önce, döşemesiz seviye esnek", function () {
  const g = BC.genellestirHazirla(depremli()).model;
  const ref = BC.aksRefZ(g, { aks: ["C", "2"], kat: 1 });
  let d = BC.diyaframModu(g, ref);
  assert.deepEqual([d.mod, d.kat, d.katAdi], ["rijit", 1, BC.katSeviyeleri(g)[1].ad]);
  assert.equal(BC.diyaframModu(g, BC.aksRefZ(g, { aks: ["C", "2"], kat: 0 })), null, "en alt seviye");
  const yok = BC.genellestirHazirla(aksKatModel()).model;
  assert.equal(BC.diyaframModu(yok, BC.aksRefZ(yok, { aks: ["C", "2"], kat: 1 })), null, "deprem yok");
  // yuk_durumlari.E.acik da depremi açar
  assert.equal(BC.depremVar({ yuk_durumlari: { E: { acik: true } } }), true);
  assert.equal(BC.depremVar({ deprem: { SS: 1 } }), false, "kart var ama etkin değil");
  // analiz.diyafram (kat başına ya da dize) önce gelir
  const e1 = JSON.parse(JSON.stringify(g)); e1.analiz = { diyafram: { 1: "esnek" } };
  assert.equal(BC.diyaframModu(e1, ref).mod, "esnek");
  assert.equal(BC.diyaframModu(e1, BC.aksRefZ(e1, { aks: ["C", "2"], kat: 2 })).mod, "rijit", "öteki kat");
  const e2 = JSON.parse(JSON.stringify(g)); e2.analiz = { diyafram: "esnek" };
  assert.equal(BC.diyaframModu(e2, ref).mod, "esnek");
  const e3 = JSON.parse(JSON.stringify(g)); e3.deprem.diyafram = "esnek";
  assert.equal(BC.diyaframModu(e3, ref).mod, "esnek");
  // seviyede kalınlığı > 0 panel yok → esnek (sac çatı)
  const e4 = JSON.parse(JSON.stringify(g)); e4.paneller.forEach(function (p) { if (p.kat === 1) p.kalinlik = 0; });
  assert.equal(BC.diyaframModu(e4, ref).mod, "esnek");
  const e5 = JSON.parse(JSON.stringify(g)); e5.paneller.forEach(function (p) { if (p.kat === 1) delete p.kalinlik; });
  assert.equal(BC.diyaframModu(e5, ref).mod, "esnek", "kalınlığı verilmeyen panel motorda 0 sayılır");
});

test("K-15 Mesnet aracı sorusu ve seçenekleri: 'Olduğu gibi uygula', 'Yalnız düşey mesnet (uz, rx, ry)', 'Bu katın diyaframını esnek yap', 'Vazgeç'", function () {
  const b = depremli();
  const ref = { aks: ["C", "2"], kat: 1 };
  const q = BC.mesnetDiyaframSorusu(b, ref, "ankastre", { adres: "C2 / 1. kat" });
  assert.equal(q.baslik, "Rijit diyaframlı kat");
  assert.equal(q.metin, "C2 / 1. kat rijit diyaframlı " + q.katAdi + " seviyesinde. Yatay (ux, uy) ve rz mesnedi bu noktada bütün katın yatay hareketini tutar (diyafram bağı).");
  assert.deepEqual(q.secenekler.map(function (x) { return x[1]; }), ["Olduğu gibi uygula", "Yalnız düşey mesnet (uz, rx, ry)", "Bu katın diyaframını esnek yap", "Vazgeç"]);
  assert.equal(BC.mesnetDiyaframSorusu(b, { aks: ["C", "2"], kat: 0 }, "ankastre"), null, "temel seviyesi");
  assert.equal(BC.mesnetDiyaframSorusu(aksKatModel(), ref, "ankastre"), null, "deprem yok");
  assert.equal(BC.mesnetDiyaframSorusu(b, ref, "kaldir"), null);
  assert.equal(BC.mesnetDiyaframSorusu(b, ref, "yay", { yay: { kz: 1000 } }), null, "yalnız düşey yay: soru yok");
  assert.ok(BC.mesnetDiyaframSorusu(b, ref, "yay", { yay: { kx: 1000 } }), "yatay yay: soru");
  assert.equal(BC.mesnetDiyaframSorusu(b, ref, "kayici-xy"), null, "kayıcı (X, Y serbest) yalnız uz yazar → soru yok");
  assert.ok(BC.mesnetDiyaframSorusu(b, ref, "kayici-x"), "kayıcı (X serbest) uy yazar → soru");
  // aynen
  let r = BC.mesnetAta(b, ref, "ankastre", { diyafram: "aynen" });
  assert.deepEqual(r.model.mesnetler[0], { dugum: BC.aksRefZ(r.model, ref), ux: true, uy: true, uz: true, rx: true, ry: true, rz: true });
  // yalnız düşey
  r = BC.mesnetAta(b, ref, "ankastre", { diyafram: "dusey" });
  const s = r.model.mesnetler[0];
  assert.deepEqual([s.ux, s.uy, s.uz, s.rx, s.ry, s.rz], [false, false, true, true, true, false]);
  // esnek: ön ayar aynen, yalnız bu kat esnek (öteki katlar korunur)
  r = BC.mesnetAta(Object.assign(depremli(), { analiz: { diyafram: { 2: "rijit" } } }), ref, "ankastre", { diyafram: "esnek" });
  assert.deepEqual(r.model.analiz.diyafram, { 1: "esnek", 2: "rijit" });
  assert.equal(r.model.mesnetler[0].ux, true);
  assert.equal(BC.diyaframModu(r.model, r.model.mesnetler[0].dugum).mod, "esnek");
  assert.ok(r.notlar.some(function (n) { return /diyaframı esnek yapıldı/.test(n); }));
  // dize analiz.diyafram önce kat başına sözlüğe açılır
  const k = JSON.parse(JSON.stringify(BC.genellestirHazirla(depremli()).model)); k.analiz = { diyafram: "rijit" };
  BC.katDiyaframiEsnek(k, 2);
  assert.deepEqual(k.analiz.diyafram, { 1: "rijit", 2: "esnek" });
  // yaylı mesnette yalnız düşey: kx atılır, kz kalır
  r = BC.mesnetAta(b, ref, "yay", { yay: { kx: 500, kz: 1000 }, diyafram: "dusey" });
  assert.deepEqual(Object.keys(r.model.mesnetler[0]).sort(), ["dugum", "kz"]);
  assert.throws(function () { BC.mesnetAta(b, ref, "yay", { yay: { kx: 500 }, diyafram: "dusey" }); }, /Yalnız düşey yönlerde yay kalmadı/);
});

// ------------------------------------------------------------------ K-13 / K-32 / K-31 / K-27: kesit önerisi ekleri (C19)
test("K-13 parçalı aks–kat elemanı: satırda 'N parça', aks–kat kaydına bir kez; genelleştirilmiş modelde bütün parçalar; sahne vurgusu", function () {
  const o = { cubuk: 13, cubuklar: [13, 14], tur: "kiris", kesit: "K25x50", oneri: "25x60", sistem: "betonarme", b: 0.25, h: 0.6, degisim: "büyüt",
    dc_once: 1.2, dc_oneri: 0.95, kaynak: { aks_kat: "kiris", no: 1 }, uygula: { ad: "B25x60", tanim: { tip: "dikdortgen", b: 0.25, h: 0.6, malzeme: "C30" }, yeni: true } };
  assert.equal(BC.oneriSatiri(o, false).parca, "2 parça");
  assert.equal(BC.oneriSatiri(Object.assign({}, o, { cubuklar: [13] }), false).parca, "");
  assert.equal(BC.oneriSatiri(Object.assign({}, o, { grup: { kesit: "K25x50", tur: "kiris", uye: 4 } }), false).parca, "", "grup kaydının cubuklar'ı parça değil");
  // aks–kat model: kiriş 1 bir kez
  const b = aksKatModel();
  let r = BC.oneriUygula(b, o, null);
  assert.deepEqual(r.hedefler, [{ tur: "kiris", no: 1 }]);
  assert.equal(r.model.kirisler[0].kesit, "B25x60");
  assert.equal(r.model.kirisler.filter(function (k) { return k.kesit === "B25x60"; }).length, 1);
  assert.deepEqual(BC.oneriVurgusu(b, o), [{ tur: "kiris", no: 1 }]);
  // genelleştirilmiş model: kiriş 1'in parçaları çubuk; öneri bütün parçalara
  const g = BC.genellestirHazirla(b).model;
  const p = g.cubuklar.filter(function (c) { return c.kaynak && c.kaynak.aks_kat === "kiris" && c.kaynak.no === 1; }).map(function (c) { return c.no; });
  assert.equal(p.length, 2);
  const og = Object.assign({}, o, { cubuk: p[0], cubuklar: p });
  r = BC.oneriUygula(g, og, null);
  assert.deepEqual(r.hedefler, p.map(function (no) { return { tur: "cubuk", no: no }; }));
  assert.ok(p.every(function (no) { return r.model.cubuklar.find(function (c) { return c.no === no; }).kesit === "B25x60"; }));
  assert.deepEqual(BC.oneriVurgusu(g, og), p.map(function (no) { return { tur: "cubuk", no: no }; }));
  assert.throws(function () { BC.oneriUygula(g, Object.assign({}, og, { cubuklar: [p[0], 9999] }), null); }, /9999 modelde yok/);
  // gerçek D/C: parçaların en büyüğü
  const v = { tasarim: { elemanlar: [{ cubuk: p[0], tur: "kiris", dc: 0.8 }, { cubuk: p[1], tur: "kiris", dc: 0.93 }] } };
  assert.equal(BC.grupDcMaks(v, r.hedefler), 0.93);
});

test("K-32 kesit grubu: aynı (kesit, tür) ya da aynı grup adı; düğme metni 'Kesit grubuna uygula (N çubuk)'; grup kartı bütün üyelere tek seferde", function () {
  const b = aksKatModel();
  // aks–kat: 12 kolonun hepsi S40x40
  let u = BC.grupUyeleri(b, { tur: "kolon", no: 1 });
  assert.equal(u.length, 12);
  assert.ok(u.every(function (x) { return x.tur === "kolon"; }));
  assert.equal(BC.grupDugmeMetni(u), "Kesit grubuna uygula (12 çubuk)");
  // farklı kesitli kolon kendi grubunda tekse düğme yok
  const t = JSON.parse(JSON.stringify(b)); t.kesitler.S50x50 = { tip: "dikdortgen", b: 0.5, h: 0.5, malzeme: "C30" }; t.kolonlar[0].kesit = "S50x50";
  assert.deepEqual(BC.grupUyeleri(t, { tur: "kolon", no: 1 }), [{ tur: "kolon", no: 1 }]);
  assert.equal(BC.grupDugmeMetni(BC.grupUyeleri(t, { tur: "kolon", no: 1 })), "");
  assert.equal(BC.grupUyeleri(t, { tur: "kolon", no: 2 }).length, 11);
  // kiriş: kolonlar aynı kesitte olsa da tür farklı → ayrı grup
  assert.equal(BC.grupUyeleri(b, { tur: "kiris", no: 1 }).length, b.kirisler.length);
  // grup adı: türden bağımsız aynı gruptakiler
  const gr = JSON.parse(JSON.stringify(b)); gr.kolonlar[0].grup = "G1"; gr.kolonlar[5].grup = "G1"; gr.kirisler[2].grup = "G1";
  assert.deepEqual(BC.grupUyeleri(gr, { tur: "kolon", no: 1 }), [{ tur: "kolon", no: 1 }, { tur: "kolon", no: 6 }, { tur: "kiris", no: 3 }]);
  // genel model çubukları: (kesit, tür)
  let m = bos();
  m = cubukEkle(m, G("A", "1", "±0.00"), G("A", "1", "+3.00"), { tur: "kolon" });
  m = cubukEkle(m, G("B", "1", "±0.00"), G("B", "1", "+3.00"), { tur: "kolon" });
  m = cubukEkle(m, G("A", "1", "+3.00"), G("B", "1", "+3.00"));
  assert.deepEqual(BC.grupUyeleri(m, { tur: "cubuk", no: 1 }), [{ tur: "cubuk", no: 1 }, { tur: "cubuk", no: 2 }]);
  assert.deepEqual(BC.grupUyeleri(m, { tur: "cubuk", no: 3 }), [{ tur: "cubuk", no: 3 }]);
  assert.deepEqual(BC.grupUyeleri(m, { tur: "cubuk", no: 99 }), []);
  // grup kartı (C19 grup kaydı): kesit tanımı bir kez, bütün üyelere
  u = BC.grupUyeleri(b, { tur: "kolon", no: 1 });
  const o = { cubuk: 1, cubuklar: [1, 2, 3], tur: "kolon", kesit: "S40x40", oneri: "45x45", sistem: "betonarme", degisim: "büyüt", dc_once: 1.1, dc_oneri: 0.92,
    grup: { kesit: "S40x40", tur: "kolon", uye: 12 }, uygula: { ad: "B45x45-ρ%1.50", tanim: { tip: "dikdortgen", b: 0.45, h: 0.45, malzeme: "C30", donati_orani: 0.015 }, yeni: true } };
  const r = BC.grupUygula(b, o, u.concat([{ tur: "kolon", no: 99 }]));
  assert.equal(r.ad, "B45x45-ρ%1.50");
  assert.equal(r.hedefler.length, 12); assert.deepEqual(r.eksik, [{ tur: "kolon", no: 99 }]);
  assert.ok(r.model.kolonlar.every(function (k) { return k.kesit === "B45x45-ρ%1.50"; }));
  assert.equal(r.model.kesitler["B45x45-ρ%1.50"].donati_orani, 0.015);
  assert.equal(b.kolonlar[0].kesit, "S40x40", "girdi değişmez");
  assert.throws(function () { BC.grupUygula(b, o, [{ tur: "kolon", no: 99 }]); }, /modelde yok/);
  // grubun gerçek D/C'si: üyelerin en büyüğü
  const v = { tasarim: { elemanlar: [{ tur: "kolon", no: 1, dc: 0.71 }, { tur: "kolon", no: 7, dc: 0.93 }, { tur: "kiris", no: 1, dc: 1.4 }] } };
  assert.equal(BC.grupDcMaks(v, u), 0.93);
  assert.equal(BC.grupDcMaks(v, [{ tur: "kolon", no: 99 }]), null);
});

test("K-31 süre notu ve K-27 öteleme satırı", function () {
  assert.equal(BC.sureTahmini({ ozet: { cozum_sure_ms: 2500 } }, 3), "Hesaplanıyor: en çok 4 çözüm, yaklaşık 13 s");
  assert.equal(BC.sureTahmini({ ozet: { cozum_sure_ms: 200 } }, 3), "Hesaplanıyor: en çok 4 çözüm, yaklaşık 1 s");
  assert.equal(BC.sureTahmini(null, 3), "Hesaplanıyor: en çok 4 çözüm, yaklaşık birkaç saniye");
  assert.equal(BC.sureTahmini({ ozet: {} }, 3, 3000), "Hesaplanıyor: en çok 4 çözüm, yaklaşık 16 s", "görünen çözümün süresi yoksa ilk yanıtın sure_ms'i");
  assert.equal(BC.sureTahmini({ ozet: { cozum_sure_ms: 1000 } }, 1), "Hesaplanıyor: en çok 2 çözüm, yaklaşık 3 s");
  assert.equal(BC.sureMetni(4210), "Süre: 4,2 s");
  assert.equal(BC.sureMetni(12600), "Süre: 13 s");
  assert.equal(BC.sureMetni(null), ""); assert.equal(BC.sureMetni("x"), "");
  const ot = { sinir: 0.008, once: { X: [0.0050, 0.00656, 0.004], Y: [0.0060, 0.00616] }, sonra: { X: [0.0076, 0.0070], Y: [0.0072, 0.0060] } };
  assert.equal(BC.otelemeSatiri(ot), "Göreli kat ötelemesi (en büyük δ/h ÷ sınır): önce X 0,82 · Y 0,77 → sonra X 0,95 · Y 0,90");
  assert.equal(BC.otelemeSatiri({ sinir: 0.008, once: { X: [0.009] }, sonra: { X: [0.0096], Y: [] } }), "Göreli kat ötelemesi (en büyük δ/h ÷ sınır): önce X 1,13 → sonra X 1,20 ⚠");
  assert.equal(BC.otelemeSatiri(null), ""); assert.equal(BC.otelemeSatiri({ sinir: 0, once: {}, sonra: {} }), "");
});

test("K-22 makas planı: yanal_tutma seçeneği parametreye ve üreteç formuna geçer", function () {
  const m = bos();
  const p = BC.makasPlan(m, { tip: "pratt", bas: G("A", "1", "+6.00"), son: G("B", "1", "+6.00"), yukseklik: 1.2, goz: 4 });
  assert.equal(p.parametre.yanal_tutma, undefined, "verilmezse motor varsayılanı (uc-dikme)");
  const q = BC.makasPlan(m, { tip: "pratt", bas: G("A", "1", "+6.00"), son: G("B", "1", "+6.00"), yukseklik: 1.2, goz: 4, yanal_tutma: "yok" });
  assert.equal(q.parametre.yanal_tutma, "yok");
  const r = O.makasUret(q.model, q.parametre);
  const k = BC.uretecKaydi(r.model, r.uretec);
  assert.equal(BC.uretecFormu(r.model, k).yanal, "yok");
  const r2 = O.makasUret(p.model, p.parametre);
  assert.equal(BC.uretecFormu(r2.model, BC.uretecKaydi(r2.model, r2.uretec)).yanal, "uc-dikme");
});
