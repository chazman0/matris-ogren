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
