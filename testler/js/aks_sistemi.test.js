/* docs/aks_sistemi.js birim testleri — node'un yerleşik test koşucusu (bağımlılık yok).
   Çalıştırma: node --test testler/js/aks_sistemi.test.js
   Kapsam: saf mantık (sözdizimi, adlar, sistemler, REF çözücü, görünüm geometrisi, aks düzenlemenin modele etkisi,
   kat ↔ Z eşlemesi, eski model yükseltme, hızlı aks), SVG katmanı (metin) ve model_ops ile birlikte çalışma. */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const A = require(path.join(__dirname, "..", "..", "docs", "aks_sistemi.js"));
const M = require(path.join(__dirname, "..", "..", "docs", "model_ops.js"));

function yakin(a, b, tol, mesaj) {
  tol = tol == null ? 1e-6 : tol;
  if (Array.isArray(a)) { assert.equal(a.length, b.length, mesaj); a.forEach(function (x, i) { yakin(x, b[i], tol, mesaj); }); return; }
  assert.ok(Math.abs(a - b) <= tol, (mesaj || "") + ` beklenen ${b}, bulunan ${a}`);
}
function dondurulmus(o) { return JSON.stringify(o); }

/** Örnek bina: A–D (0, 6, 12, 19.5) × 1–3 (0, 5, 10); Z: ±0.00 (kat 0), +4.50 (kat 1), +8.00 (kat 2), Saçak 9, Mahya 10.5. */
function ornek() {
  const ak = A.hizliAks({ x: "2@6, 7.5", y: "2@5", z: "1@4.5, 3.5", ekZ: [{ ad: "Saçak", konum: 9 }, { ad: "Mahya", konum: 10.5 }] });
  return { tur: "bina", surum: 3, akslar: ak, katlar: A.katlarTuret(ak), cubuklar: [], paneller: [], mesnetler: [], dugumler: [], ek_yukler: [] };
}
/** Ek sistemli örnek: KANAT (kartezyen, orijin (30, 0), 30°) ve KUBBE (silindirik, orijin (−20, 5)). */
function sistemli() {
  let b = ornek();
  b = A.sistemEkle(b, { ad: "KANAT", tur: "kartezyen", orijin: [30, 0, 0], aci: 30, x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 6 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }] }).model;
  b = A.sistemEkle(b, { ad: "KUBBE", tur: "silindirik", orijin: [-20, 5, 0], r: [{ ad: "R1", konum: 4 }, { ad: "R2", konum: 8 }], teta: [0, 90, 180, 270].map(function (t, i) { return { ad: "T" + (i + 1), konum: t }; }) }).model;
  return b;
}
const G = function (x, y, z) { return { aks: [x, y], z: z }; };

// ------------------------------------------------------------------ sözdizimi
test("aralık sözdizimi: n@a terimleri, tek aralık, ondalık nokta", function () {
  const r = A.sozdizimiAyristir("3@6, 2@7.5, 5");
  assert.equal(r.tur, "aralik");
  assert.deepEqual(r.araliklar, [6, 6, 6, 7.5, 7.5, 5]);
  assert.deepEqual(r.konumlar, [0, 6, 12, 18, 25.5, 33, 38]);
  assert.deepEqual(A.sozdizimiAyristir("5").konumlar, [0, 5]);
  assert.deepEqual(A.sozdizimiAyristir("2@3", { baslangic: 1.5 }).konumlar, [1.5, 4.5, 7.5]);
  assert.deepEqual(A.sozdizimiAyristir("2×4; 3*2").araliklar, [4, 4, 2, 2, 2]);
});
test("konum sözdizimi: boşlukla ayrılmış artan sayılar; tekrarlar atılır", function () {
  const r = A.sozdizimiAyristir("0 6 12 19.5");
  assert.equal(r.tur, "konum");
  assert.deepEqual(r.konumlar, [0, 6, 12, 19.5]);
  assert.deepEqual(r.araliklar, [6, 6, 7.5]);
  assert.deepEqual(A.sozdizimiAyristir("-3 0 4,5").konumlar, [-3, 0, 4.5]);
  // artan değilse aralık sayılır
  assert.equal(A.sozdizimiAyristir("6 6 6").tur, "aralik");
  // açık kip
  const k = A.sozdizimiAyristir("12 0 6", { kip: "konum" });
  assert.deepEqual(k.konumlar, [0, 6, 12]);
  assert.equal(A.sozdizimiAyristir("0 6 6 12", { kip: "konum" }).uyarilar.length, 1);
});
test("Türkçe ondalık virgül toleransı", function () {
  assert.deepEqual(A.sozdizimiAyristir("7,5").araliklar, [7.5]);
  assert.deepEqual(A.sozdizimiAyristir("2@7,5; 3").araliklar, [7.5, 7.5, 3]);
  assert.deepEqual(A.sozdizimiAyristir("3@6, 2@7,5, 5").araliklar, [6, 6, 6, 7.5, 7.5, 5]);
  assert.deepEqual(A.sozdizimiAyristir("3@6,2@7,5").araliklar, [6, 6, 6, 7.5, 7.5]);
  assert.deepEqual(A.sozdizimiAyristir("6,7,8").araliklar, [6, 7, 8]);
  assert.deepEqual(A.sozdizimiAyristir("1@4.5, 3@3,2").araliklar, [4.5, 3.2, 3.2, 3.2]);
});
test("sözdizimi hataları öğretici", function () {
  assert.throws(function () { A.sozdizimiAyristir(""); }, /boş/);
  assert.throws(function () { A.sozdizimiAyristir("3@x"); }, /anlaşılamadı/);
  assert.throws(function () { A.sozdizimiAyristir("3@0"); }, /sıfırdan büyük/);
  assert.throws(function () { A.sozdizimiAyristir("2@6 0 4", { kip: "konum" }); }, /adet@aralık/);
  assert.throws(function () { A.sozdizimiAyristir("abc"); }, function (e) { return e instanceof A.AksHatasi; });
});
test("konum ↔ aralık ve kısa sözdizimi yazımı (gidiş-dönüş)", function () {
  assert.deepEqual(A.konumdanAralik([0, 6, 12, 19.5]), [6, 6, 7.5]);
  assert.deepEqual(A.araliktanKonum([6, 6, 7.5], 2), [2, 8, 14, 21.5]);
  assert.equal(A.sozdizimiYaz([0, 6, 12, 18, 25.5]), "3@6, 7.5");
  assert.equal(A.sozdizimiYaz([2, 5, 9]), "2 5 9");
  for (const t of ["3@6, 2@7.5, 5", "4.25", "2@3, 1, 2@3"]) {
    const k = A.sozdizimiAyristir(t).konumlar;
    assert.deepEqual(A.sozdizimiAyristir(A.sozdizimiYaz(k)).konumlar, k, t);
  }
});

// ------------------------------------------------------------------ adlar
test("ad üretme: A…Z, AA…; sayılar; ilk ad; benzersiz ad; kot adı", function () {
  assert.equal(A.adlarUret("x", 28).slice(24).join(","), "Y,Z,AA,AB");
  assert.equal(A.harfAdi(701), "ZZ");
  assert.equal(A.harfIndeks("AA"), 26);
  assert.equal(A.harfIndeks("ZZ"), 701);
  assert.equal(A.harfIndeks("1"), -1);
  assert.deepEqual(A.adlarUret("y", 3), ["1", "2", "3"]);
  assert.deepEqual(A.adlarUret("x", 3, "C"), ["C", "D", "E"]);
  assert.deepEqual(A.adlarUret("y", 2, "7"), ["7", "8"]);
  assert.deepEqual(A.adlarUret("x", 2, "1"), ["1", "2"]);
  assert.deepEqual(A.adlarUret("teta", 2), ["T1", "T2"]);
  assert.throws(function () { A.adlarUret("x", 2, "?"); }, /anlaşılamadı/);
  assert.equal(A.benzersizAd("A", ["A", "A'"]), "A''");
  assert.equal(A.kotAdi(0), "±0.00");
  assert.equal(A.kotAdi(3.2), "+3.20");
  assert.equal(A.kotAdi(-1.5), "-1.50");
  assert.equal(A.sonrakiAd([{ ad: "A" }, { ad: "B" }], "x"), "C");
  assert.equal(A.sonrakiAd([{ ad: "1" }, { ad: "4" }], "y"), "5");
});

// ------------------------------------------------------------------ hızlı aks, katlar, yükseltme
test("hızlı aks: adet+aralık, kat adedi + ek Z aksları; katlar türetilir", function () {
  const ak = A.hizliAks({ x: { adet: 4, aralik: 6 }, y: "2@5", katlar: { adet: 3, yukseklik: 3.2 }, ekZ: ["Saçak=10.1", { ad: "Mahya", konum: "11,6" }], ilkX: "B" });
  assert.deepEqual(ak.x.map(function (a) { return a.ad; }), ["B", "C", "D", "E"]);
  assert.deepEqual(ak.x.map(function (a) { return a.konum; }), [0, 6, 12, 18]);
  assert.equal(ak.x[0].tur, "ana"); assert.equal(ak.x[0].gorunur, true); assert.equal(ak.x[0].balon, "bas");
  assert.deepEqual(ak.z.map(function (a) { return [a.ad, a.konum, a.kat]; }),
    [["±0.00", 0, 0], ["+3.20", 3.2, 1], ["+6.40", 6.4, 2], ["+9.60", 9.6, 3], ["Saçak", 10.1, undefined], ["Mahya", 11.6, undefined]]);
  const k = A.katlarTuret(ak);
  assert.deepEqual(k.map(function (x) { return [x.no, x.ad, x.kot]; }), [[0, "Temel", 0], [1, "1. kat", 3.2], [2, "2. kat", 6.4], [3, "3. kat", 9.6]]);
  const z2 = A.hizliAks({ z: "1@4.5, 3@3.2", taban: -1 }).z;
  assert.deepEqual(z2.map(function (a) { return a.konum; }), [-1, 3.5, 6.7, 9.9, 13.1]);
  assert.throws(function () { A.hizliAks({ katlar: { adet: 1, yukseklik: 3 }, ekZ: [{ ad: "X", konum: 3 }] }); }, /aynı kotta/);
});
test("eski model yükseltme (surum 1 → 3): Z aksları katlardan, aks–kat elemanları aynen", function () {
  const eski = { tur: "bina", surum: 1, akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 5 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }] },
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3 }, { no: 2, ad: "Çatı", kot: 6 }],
    kolonlar: [{ no: 1, aks: ["A", "1"], kat: 1, kesit: "S40x40", yon: "x" }], kirisler: [{ no: 1, kat: 1, bas: ["A", "1"], son: ["B", "1"], kesit: "K25x50" }] };
  const once = dondurulmus(eski);
  const r = A.yukselt(eski);
  assert.equal(dondurulmus(eski), once, "girdi değişmemeli");
  assert.equal(r.model.surum, 3);
  assert.deepEqual(r.model.akslar.z, [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "+3.00", konum: 3, kat: 1 }, { ad: "+6.00", konum: 6, kat: 2 }]);
  assert.deepEqual(r.model.kolonlar, eski.kolonlar);
  assert.deepEqual(r.model.kirisler, eski.kirisler);
  assert.deepEqual(r.model.katlar, eski.katlar);
  assert.ok(r.uyarilar.some(function (u) { return /yükseltildi/.test(u); }));
  // akslar.z olmasa da çözücü katlardan türetir
  yakin(A.refKoordinat(eski, G("B", "2", "+6.00")), [5, 4, 6]);
  yakin(A.refKoordinat(eski, { aks: ["B", "2"], kat: 1 }), [5, 4, 3]);
});
test("kat ↔ Z aksı: Z aksı taşınınca kat kotu da değişir (tek kaynak akslar.z)", function () {
  const b = ornek();
  assert.equal(A.katKotu(b, 2), 8);
  assert.equal(A.zAksiKati(b, "+4.50"), 1);
  assert.equal(A.zAksiKati(b, "Saçak"), null);
  assert.equal(A.katZAksi(b, 1).ad, "+4.50");
  const r = A.aksTasi(b, { yon: "z", ad: "+4.50", konum: 5 });
  assert.equal(r.model.katlar.find(function (k) { return k.no === 1; }).kot, 5);
  assert.equal(A.katKotu(r.model, 1), 5);
  // katlarda olup Z'de olmayan kat → Z aksı eklenir; Z'de kat olup katlarda olmayan → kat eklenir
  const c = JSON.parse(JSON.stringify(b));
  c.katlar.push({ no: 3, ad: "Çatı", kot: 12 });
  c.akslar.z.find(function (a) { return a.ad === "Mahya"; }).kat = 4;
  const s = A.katlariSenkronla(c);
  assert.ok(s.model.akslar.z.some(function (a) { return a.kat === 3 && a.konum === 12; }));
  assert.ok(s.model.katlar.some(function (k) { return k.no === 4 && k.kot === 10.5; }));
  assert.ok(s.uyarilar.some(function (u) { return /artan/.test(u); }), "kat 4 (10.5) kat 3'ün (12) altında: uyarı");
});

// ------------------------------------------------------------------ REF çözücü
test("REF → koordinat: GLOBAL, eski {aks, kat}, kayıtsız aks–kat numarası, serbest", function () {
  const b = ornek();
  yakin(A.refKoordinat(b, G("D", "3", "Saçak")), [19.5, 10, 9]);
  yakin(A.refKoordinat(b, { aks: ["B", "2"], kat: 2 }), [6, 5, 8]);
  yakin(A.refKoordinat(b, { dugum: 1000 * 1 + 20 * 2 + 1 + 1 }), [12, 5, 4.5]);   // C2 kat 1
  yakin(A.refKoordinat(b, [1, 2, 3]), [1, 2, 3]);
  yakin(A.refKoordinat(b, { X: 1, Y: 2, Z: 3 }), [1, 2, 3]);
  assert.throws(function () { A.refKoordinat(b, G("Q", "1", "Saçak")); }, /X aksı "Q"/);
  assert.throws(function () { A.refKoordinat(b, { aks: ["A", "1"] }); }, /Z aksı eksik/);
  assert.throws(function () { A.refKoordinat(b, { dugum: 123456 }); }, /modelde yok/);
  assert.equal(A.refKoordinatGuvenli(b, { foo: 1 }), null);
});
test("REF → koordinat: döndürülmüş/ötelenmiş kartezyen ve silindirik sistem; ters dönüşüm", function () {
  const b = sistemli();
  const c = Math.cos(Math.PI / 6), s = Math.sin(Math.PI / 6);
  yakin(A.refKoordinat(b, { sistem: "KANAT", aks: ["B", "2"], z: "+8.00" }), [30 + 6 * c - 4 * s, 6 * s + 4 * c, 8]);
  yakin(A.refKoordinat(b, { sistem: "KUBBE", aks: ["R2", "T2"], z: "Mahya" }), [-20, 13, 10.5]);
  yakin(A.refKoordinat(b, { sistem: "KUBBE", aks: ["R1", "T3"], z: "±0.00" }), [-24, 5, 0]);
  const S = A.sistemBul(b, "KANAT");
  const P = A.sistemNokta(S, 2.5, -1.25, 3);
  yakin(A.noktaSistem(S, P[0], P[1], P[2]), [2.5, -1.25, 3]);
  const K = A.sistemBul(b, "KUBBE");
  yakin(A.noktaSistem(K, -20, 1, 2), [4, 270, 2]);
  // kendi Z listesi olan sistem: kot = orijin Z + konum
  const b2 = A.sistemEkle(ornek(), { ad: "ASMA", orijin: [0, 0, 2], x: [{ ad: "A", konum: 0 }], y: [{ ad: "1", konum: 0 }], z: [{ ad: "Z1", konum: 1.5 }] }).model;
  yakin(A.refKoordinat(b2, { sistem: "ASMA", aks: ["A", "1"], z: "Z1" }), [0, 0, 3.5]);
  assert.throws(function () { A.refKoordinat(b, { sistem: "YOK", aks: ["A", "1"], z: "±0.00" }); }, /aks sistemi yok/);
});
test("bölme ve kesişim düğümleri yinelemeli çözülür; döngü yakalanır", function () {
  const b = ornek();
  b.dugumler = [
    { no: 100001, tur: "bolme", cubuk_i: G("A", "1", "+4.50"), cubuk_j: G("D", "1", "+4.50"), oran: 0.25 },
    { no: 100002, tur: "bolme", cubuk_i: { dugum: 100001 }, cubuk_j: G("A", "1", "+4.50"), oran: 0.5 },
    { no: 100003, tur: "kesisim", a: [G("A", "1", "±0.00"), G("B", "1", "+4.50")], b: [G("B", "1", "±0.00"), G("A", "1", "+4.50")] },
    { no: 100004, tur: "bolme", cubuk_i: { dugum: 100005 }, cubuk_j: G("A", "1", "±0.00"), oran: 0.5 },
    { no: 100005, tur: "bolme", cubuk_i: { dugum: 100004 }, cubuk_j: G("A", "1", "±0.00"), oran: 0.5 },
  ];
  yakin(A.refKoordinat(b, { dugum: 100001 }), [4.875, 0, 4.5]);
  yakin(A.refKoordinat(b, 100002), [2.4375, 0, 4.5]);
  yakin(A.refKoordinat(b, { dugum: 100003 }), [3, 0, 2.25]);
  assert.throws(function () { A.refKoordinat(b, { dugum: 100004 }); }, /Döngüsel/);
  // aks taşınınca bölme düğümü birlikte taşınır (parametrik)
  const t = A.aksTasi(b, { yon: "x", ad: "D", konum: 23.5 }).model;
  yakin(A.refKoordinat(t, { dugum: 100001 }), [5.875, 0, 4.5]);
  // paralel doğrular → kesişim yok
  b.dugumler.push({ no: 100006, tur: "kesisim", a: [G("A", "1", "±0.00"), G("B", "1", "±0.00")], b: [G("A", "2", "±0.00"), G("B", "2", "±0.00")] });
  assert.throws(function () { A.refKoordinat(b, { dugum: 100006 }); }, /paralel/);
  yakin(A.dogruKesisimi([0, 0, 0], [1, 0, 0], [0, 1, 1], [0, 2, 1]), [0, 0, 0.5]);
});
test("koordinat → aks REF (en yakın kesişim, tolerans içinde; önce GLOBAL)", function () {
  const b = sistemli();
  assert.deepEqual(A.koordinattanRef(b, [12, 5, 9]), G("C", "2", "Saçak"));
  assert.equal(A.koordinattanRef(b, [12.01, 5, 9]), null);
  assert.deepEqual(A.koordinattanRef(b, [12.01, 5, 9], { tol: 0.02 }), G("C", "2", "Saçak"));
  const P = A.refKoordinat(b, { sistem: "KANAT", aks: ["B", "1"], z: "+4.50" });
  assert.deepEqual(A.koordinattanRef(b, P), { sistem: "KANAT", aks: ["B", "1"], z: "+4.50" });
  assert.deepEqual(A.koordinattanRef(b, [-20, -3, 0]), { sistem: "KUBBE", aks: ["R2", "T4"], z: "±0.00" });
  assert.equal(A.refAnahtar(b, { aks: ["A", "1"], kat: 1 }), A.refAnahtar(b, G("A", "1", "+4.50")));
});

// ------------------------------------------------------------------ görünüm geometrisi
test("görünüm düzlemi: kesişimler, aks parçaları, gözler (plan/cephe/3B)", function () {
  const b = ornek();
  const plan = { tur: "plan", z: "Saçak" };
  const k = A.kesisimler(b, plan);
  assert.equal(k.length, 12);
  assert.ok(k.every(function (x) { return x.P[2] === 9 && x.ref.z === "Saçak"; }));
  const p = A.aksParcalari(b, plan);
  assert.equal(p.length, 4 * 2 + 3 * 3);
  assert.ok(p.some(function (x) { return x.aks.yon === "x" && x.aks.ad === "B" && x.i.aks[1] === "2" && x.j.aks[1] === "3"; }));
  const g = A.gozler(b, plan);
  assert.equal(g.length, 3 * 2);
  assert.deepEqual(g[0].koseler, [G("A", "1", "Saçak"), G("B", "1", "Saçak"), G("B", "2", "Saçak"), G("A", "2", "Saçak")]);
  const cephe = { tur: "cephe", y: "1" };
  assert.equal(A.kesisimler(b, cephe).length, 4 * 5);
  const gc = A.gozler(b, cephe);
  assert.equal(gc.length, 3 * 4);
  yakin(gc[0].P, [[0, 0, 0], [6, 0, 0], [6, 0, 4.5], [0, 0, 4.5]]);
  assert.equal(A.aksParcalari(b, { tur: "cephe", x: "B" }).length, 3 * 4 + 5 * 2);
  assert.equal(A.kesisimler(b, { tur: "3b" }).length, 4 * 3 * 5);
  assert.throws(function () { A.kesisimler(b, { tur: "cephe" }); }, /aksı seçilmeli/);
  // PgUp/PgDn
  assert.equal(A.gorunumKomsu(b, plan, 1).z, "Mahya");
  assert.equal(A.gorunumKomsu(b, { tur: "plan", z: "Mahya" }, 1).z, "Mahya");
  assert.equal(A.gorunumKomsu(b, cephe, 1).y, "2");
  // plan görünümünde ek sistemler de (aynı Z akslarını paylaşan)
  const bs = sistemli();
  assert.equal(A.kesisimler(bs, { tur: "plan", z: "±0.00" }).length, 12 + 4 + 8);
  assert.equal(A.kesisimler(bs, { tur: "plan", z: "±0.00", sistem: "KANAT", yalnizSistem: true }).length, 4);
  // silindirik: tam çember → kapanış yayları
  assert.equal(A.aksParcalari(bs, { tur: "plan", z: "±0.00", sistem: "KUBBE", yalnizSistem: true }).filter(function (x) { return x.yay; }).length, 8);
});
test("en yakın kesişim (ekran izdüşümü ve 3B), en yakın aks parçası, göz bulma", function () {
  const b = ornek();
  const g = { tur: "plan", z: "+4.50" };
  const iz = function (X, Y) { return [10 * X, 200 - 10 * Y]; };     // 10 px/m plan
  const r = A.enYakinKesisim(b, g, [121, 151], { izdusum: iz });
  assert.deepEqual(r.ref, G("C", "2", "+4.50"));
  yakin(r.uzaklik, Math.SQRT2);
  assert.equal(A.enYakinKesisim(b, g, [150, 150], { izdusum: iz }), null);
  assert.deepEqual(A.enYakinKesisim(b, g, [6.1, 9.9, 4.5]).ref, G("B", "3", "+4.50"));
  const p = A.enYakinParca(b, g, [90, 152], { izdusum: iz });
  assert.equal(p.parca.aks.ad, "2");
  assert.deepEqual([p.parca.i.aks[0], p.parca.j.aks[0]], ["B", "C"]);
  const goz = A.gozBul(b, g, [150, 175], { izdusum: iz });
  assert.deepEqual(goz.adlar, ["C–D", "1–2", "+4.50"]);
  // bölme düğümlerine de yakalanır
  b.dugumler = [{ no: 100001, tur: "bolme", cubuk_i: G("A", "1", "+4.50"), cubuk_j: G("B", "1", "+4.50"), oran: 0.5 }];
  const d = A.enYakinKesisim(b, g, [31, 200], { izdusum: iz });
  assert.deepEqual(d.ref, { dugum: 100001 });
  assert.equal(d.tur, "bolme");
  assert.equal(A.duzlemDugumleri(b, { tur: "plan", z: "Saçak" }).length, 0);
});

// ------------------------------------------------------------------ aks düzenleme
/** Aksa bağlı birkaç eleman. */
function elemanli() {
  const b = ornek();
  b.cubuklar = [
    { no: 1, i: G("B", "1", "±0.00"), j: G("B", "1", "+4.50"), tur: "kolon" },
    { no: 2, i: G("A", "1", "+4.50"), j: G("B", "1", "+4.50"), tur: "kiris" },
    { no: 3, i: G("C", "1", "+4.50"), j: G("D", "1", "+4.50"), tur: "kiris" },
    { no: 4, i: G("C", "1", "+4.50"), j: { dugum: 100001 }, tur: "capraz" },
  ];
  b.dugumler = [{ no: 100001, tur: "bolme", cubuk_i: G("A", "1", "+4.50"), cubuk_j: G("B", "1", "+4.50"), oran: 0.5 }, { no: 100002, X: 6, Y: 5, Z: 4.5 }];
  b.paneller = [{ no: 1, kose: [G("A", "1", "+4.50"), G("B", "1", "+4.50"), G("B", "2", "+4.50"), G("A", "2", "+4.50")], tur: "doseme" }];
  b.mesnetler = [{ dugum: G("B", "1", "±0.00"), ux: true, uy: true, uz: true }];
  b.ek_yukler = [{ tur: "dugum", dugum: G("B", "1", "+4.50"), durum: "Q", FZ: -10 }, { tur: "cubuk", cubuk: 3, durum: "G", q1: -2 }];
  b.kolonlar = [{ no: 1, aks: ["B", "2"], kat: 1, kesit: "S40x40", yon: "x" }];
  b.kirisler = [{ no: 1, kat: 1, bas: ["A", "3"], son: ["B", "3"], kesit: "K25x50" }];
  return b;
}
test("aks taşı: adla bağlı elemanlar yapışık (model aynı), sonrakileri kaydır, serbest düğüm de taşınır", function () {
  const b = elemanli(), once = dondurulmus(b);
  const r = A.aksTasi(b, { yon: "x", ad: "B", konum: 7 });
  assert.equal(dondurulmus(b), once, "girdi değişmemeli");
  assert.deepEqual(r.model.cubuklar, b.cubuklar);
  yakin(A.refKoordinat(r.model, b.cubuklar[1].j), [7, 0, 4.5]);
  yakin(A.refKoordinat(r.model, { dugum: 100001 }), [3.5, 0, 4.5]);
  assert.deepEqual(r.model.dugumler[1], { no: 100002, X: 7, Y: 5, Z: 4.5 });
  assert.ok(r.uyarilar.some(function (u) { return /serbest koordinatlı düğüm/.test(u); }));
  const y = A.aksTasi(b, { yon: "x", ad: "B", konum: 7, yapisik: false });
  assert.deepEqual(y.model.dugumler[1], b.dugumler[1]);
  const k = A.aksTasi(b, { yon: "x", ad: "B", konum: 7, kaydir: true });
  assert.deepEqual(k.model.akslar.x.map(function (a) { return a.konum; }), [0, 7, 13, 20.5]);
  assert.deepEqual(k.tasinan, ["B", "C", "D"]);
  const s = A.aksTasi(b, { yon: "x", ad: "B", konum: 14 });
  assert.ok(s.uyarilar.some(function (u) { return /sırası değişti/.test(u); }));
  const m = A.aksTasi(b, { yon: "x", ad: "B", konum: 11.9 });
  assert.ok(m.uyarilar.some(function (u) { return /en az 0,30 m/.test(u); }));
  assert.throws(function () { A.aksTasi(b, { yon: "x", ad: "B", konum: "on" }); }, /sayı/);
});
test("aralık değiştir: önceki aksa göre; kaydır seçeneği", function () {
  const b = ornek();
  const r = A.aralikDegistir(b, { yon: "x", ad: "C", aralik: "7,5" });
  assert.deepEqual(r.model.akslar.x.map(function (a) { return a.konum; }), [0, 6, 13.5, 19.5]);
  const k = A.aralikDegistir(b, { yon: "x", ad: "C", aralik: 7.5, kaydir: true });
  assert.deepEqual(k.model.akslar.x.map(function (a) { return a.konum; }), [0, 6, 13.5, 21]);
  assert.throws(function () { A.aralikDegistir(b, { yon: "x", ad: "A", aralik: 2 }); }, /İlk aksın/);
  assert.throws(function () { A.aralikDegistir(b, { yon: "x", ad: "B", aralik: -1 }); }, /sıfırdan büyük/);
});
test("aks ekle: sona (sonraki harf, son aralık), araya (A'), Z'de kot adı; çakışma reddi", function () {
  const b = ornek();
  const s = A.aksEkle(b, { yon: "x" });
  assert.equal(s.eklenen, "E");
  assert.equal(s.model.akslar.x[4].konum, 27);
  const a = A.aksEkle(b, { yon: "x", arasina: ["B", "C"] });
  assert.equal(a.eklenen, "B'");
  assert.equal(a.model.akslar.x.find(function (x) { return x.ad === "B'"; }).konum, 9);
  assert.deepEqual(a.model.akslar.x.map(function (x) { return x.ad; }), ["A", "B", "B'", "C", "D"]);
  const y = A.aksEkle(b, { yon: "y", konum: 7 });
  assert.equal(y.eklenen, "2'");
  const z = A.aksEkle(b, { yon: "z", konum: 6.2 });
  assert.equal(z.eklenen, "+6.20");
  assert.equal(A.aksEkle(b, { yon: "z", konum: 7, ad: "Kren" }).eklenen, "Kren");
  assert.throws(function () { A.aksEkle(b, { yon: "x", konum: 6 }); }, /zaten bir aks/);
  assert.throws(function () { A.aksEkle(b, { yon: "x", konum: 3, ad: "A" }); }, /benzersiz/);
  const c = A.aksCogalt(b, { yon: "y", ad: "3", ofset: 2.5, adet: 2 });
  assert.deepEqual(c.eklenen, ["4", "5"]);
  assert.deepEqual(c.model.akslar.y.map(function (x) { return x.konum; }), [0, 5, 10, 12.5, 15]);
});
test("yeniden adlandır: bütün REF'ler ve aks–kat elemanları güncellenir", function () {
  const b = elemanli();
  const r = A.aksYenidenAdlandir(b, { yon: "x", eski: "B", yeni: "B1" });
  const m = r.model;
  assert.deepEqual(m.cubuklar[0].i, G("B1", "1", "±0.00"));
  assert.deepEqual(m.cubuklar[1].j, G("B1", "1", "+4.50"));
  assert.deepEqual(m.dugumler[0].cubuk_j, G("B1", "1", "+4.50"));
  assert.deepEqual(m.paneller[0].kose[1], G("B1", "1", "+4.50"));
  assert.deepEqual(m.mesnetler[0].dugum, G("B1", "1", "±0.00"));
  assert.deepEqual(m.ek_yukler[0].dugum, G("B1", "1", "+4.50"));
  assert.deepEqual(m.kolonlar[0].aks, ["B1", "2"]);
  assert.deepEqual(m.kirisler[0].son, ["B1", "3"]);
  assert.throws(function () { A.aksYenidenAdlandir(b, { yon: "x", eski: "B", yeni: "C" }); }, /benzersiz/);
  // Z aksı: GLOBAL Z'yi paylaşan ek sistem REF'leri de
  let bs = sistemli();
  bs.cubuklar = [{ no: 1, i: { sistem: "KANAT", aks: ["A", "1"], z: "Saçak" }, j: G("A", "1", "Saçak"), tur: "kiris" }];
  bs = A.aksYenidenAdlandir(bs, { yon: "z", eski: "Saçak", yeni: "SAÇAK" }).model;
  assert.equal(bs.cubuklar[0].i.z, "SAÇAK");
  assert.equal(bs.cubuklar[0].j.z, "SAÇAK");
  // ek sistemin X aksı: yalnız o sistemin REF'leri
  const bk = A.aksYenidenAdlandir(Object.assign(sistemli(), { cubuklar: [{ no: 1, i: { sistem: "KANAT", aks: ["A", "1"], z: "±0.00" }, j: G("A", "1", "±0.00") }] }), { sistem: "KANAT", yon: "x", eski: "A", yeni: "K" }).model;
  assert.deepEqual(bk.cubuklar[0].i.aks, ["K", "1"]);
  assert.deepEqual(bk.cubuklar[0].j.aks, ["A", "1"]);
});
test("yeniden harfle: konum sırasıyla A, B, C… (yer değiştiren adlar dahil)", function () {
  let b = elemanli();
  b = A.aksTasi(b, { yon: "x", ad: "A", konum: 15 }).model;    // sıra: B(6) C(12) A(15) D(19.5)
  const r = A.yenidenHarfle(b, { yon: "x" });
  assert.deepEqual(r.esleme, { B: "A", C: "B", A: "C" });
  assert.deepEqual(r.model.cubuklar[0].i, G("A", "1", "±0.00"));       // eski B
  assert.deepEqual(r.model.cubuklar[1].i, G("C", "1", "+4.50"));       // eski A
  assert.deepEqual(r.model.kolonlar[0].aks, ["A", "2"]);
  yakin(A.refKoordinat(r.model, r.model.cubuklar[1].i), A.refKoordinat(b, b.cubuklar[1].i));
  const z = A.yenidenHarfle(ornek(), { yon: "z" });
  assert.deepEqual(z.model.akslar.z.map(function (a) { return a.ad; }), ["±0.00", "+4.50", "+8.00", "+9.00", "+10.50"]);
});
test("aks sil: bağlı eleman raporu, onay, elemanlarla, en yakın aksa taşı, iptal", function () {
  const b = elemanli(), once = dondurulmus(b);
  const bag = A.bagliElemanlar(b, { yon: "x", ad: "B" });
  assert.deepEqual(bag.cubuklar, [1, 2, 4]);          // 4: bölme düğümü 100001 üzerinden dolaylı
  assert.deepEqual(bag.dugumler, [100001]);
  assert.deepEqual(bag.paneller, [1]);
  assert.deepEqual(bag.mesnetler, [0]);
  assert.deepEqual(bag.ek_yukler, [0]);
  assert.deepEqual(bag.kolonlar, [1]);
  assert.deepEqual(bag.kirisler, [1]);
  assert.match(bag.ozet, /3 çubuk/);
  const o = A.aksSil(b, { yon: "x", ad: "B" });
  assert.equal(o.onayGerekli, true);
  assert.equal(o.silindi, false);
  assert.equal(o.komsu, "A");
  assert.deepEqual(o.hedef, { sistem: "GLOBAL", yon: "x", ad: "B" });
  assert.deepEqual(o.secenekler, ["elemanlarla", "tasi", "iptal"]);
  assert.equal(dondurulmus(o.model), once);
  assert.equal(A.aksSil(b, { yon: "x", ad: "B", secenek: "iptal" }).silindi, false);
  const e = A.aksSil(b, { yon: "x", ad: "B", secenek: "elemanlarla" }).model;
  assert.deepEqual(e.akslar.x.map(function (a) { return a.ad; }), ["A", "C", "D"]);
  assert.deepEqual(e.cubuklar.map(function (c) { return c.no; }), [3]);
  assert.deepEqual(e.dugumler.map(function (d) { return d.no; }), [100002]);
  assert.equal(e.paneller.length, 0); assert.equal(e.mesnetler.length, 0); assert.equal(e.kolonlar.length, 0); assert.equal(e.kirisler.length, 0);
  assert.deepEqual(e.ek_yukler, [b.ek_yukler[1]]);
  const t = A.aksSil(b, { yon: "x", ad: "B", secenek: "tasi" });
  assert.equal(t.silindi, true);
  assert.deepEqual(t.model.cubuklar.map(function (c) { return c.no; }), [1, 3, 4], "A1–A1 olan kiriş 2 sıfır boylu: silinir");
  assert.deepEqual(t.model.cubuklar[0].i, G("A", "1", "±0.00"));
  assert.equal(t.model.paneller.length, 0, "köşeleri çakışan panel silinir");
  assert.deepEqual(t.model.kolonlar[0].aks, ["A", "2"]);
  assert.equal(t.model.kirisler.length, 0, "başı ve sonu aynı aksa düşen kiriş silinir");
  assert.ok(t.uyarilar.some(function (u) { return /sıfır|aynı kesişime/.test(u); }));
  // bağsız aks doğrudan silinir
  const d = A.aksSil(b, { yon: "y", ad: "3", secenek: undefined });
  assert.equal(d.onayGerekli, true, "kiriş 1 (A3–B3) bağlı");
  const z = A.aksSil(b, { yon: "z", ad: "Mahya" });
  assert.equal(z.silindi, true);
  assert.ok(!z.model.akslar.z.some(function (a) { return a.ad === "Mahya"; }));
  // kata bağlı ve elemanlı Z aksı silinmez
  const k = A.aksSil(b, { yon: "z", ad: "+4.50", secenek: "elemanlarla" });
  assert.equal(k.silindi, false);
  assert.match(k.uyarilar[0], /Katlar/);
  // elemansız kat Z aksı: kat da kalkar
  const kz = A.aksSil(ornek(), { yon: "z", ad: "+8.00" });
  assert.equal(kz.silindi, true);
  assert.ok(!kz.model.katlar.some(function (x) { return x.no === 2; }));
});
test("aks sil 'en yakın aksa taşı': iki aksta da eleman varsa çakışan çubuk / panel / kiriş / döşeme kalmaz; yükler kalana aktarılır", function () {
  const b = ornek();      // X: A 0, B 6, C 12, D 19.5; Y: 1 0, 2 5, 3 10; Z: ±0.00, +4.50, +8.00 …
  b.cubuklar = [];
  let n = 0;
  const cb = function (i, j, tur) { b.cubuklar.push({ no: ++n, i: i, j: j, tur: tur }); return n; };
  for (const x of ["B", "C"]) { cb(G(x, "1", "±0.00"), G(x, "1", "+4.50"), "kolon"); cb(G(x, "2", "±0.00"), G(x, "2", "+4.50"), "kolon"); cb(G(x, "1", "+4.50"), G(x, "2", "+4.50"), "kiris"); }
  const ab = cb(G("A", "1", "+4.50"), G("B", "1", "+4.50"), "kiris"), bc = cb(G("B", "1", "+4.50"), G("C", "1", "+4.50"), "kiris");
  b.paneller = [{ no: 1, kose: [G("A", "1", "+4.50"), G("B", "1", "+4.50"), G("B", "2", "+4.50"), G("A", "2", "+4.50")], tur: "doseme" },
    { no: 2, kose: [G("A", "1", "+4.50"), G("C", "1", "+4.50"), G("C", "2", "+4.50"), G("A", "2", "+4.50")], tur: "doseme" }];
  b.mesnetler = [{ dugum: G("B", "1", "±0.00"), ux: true, uy: true, uz: true, rx: false, ry: false, rz: false },
    { dugum: G("C", "1", "±0.00"), ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }];
  b.ek_yukler = [{ tur: "cubuk", cubuk: 6, durum: "G", q1: -3 }, { tur: "cubuk", cubuk: bc, durum: "Q", q1: -1 }, { tur: "panel", panel: 2, durum: "G", p: 1 }];
  b.kren = [{ no: 1, yol: [3, 6] }];
  b.kolonlar = [{ no: 1, aks: ["B", "2"], kat: 1 }, { no: 2, aks: ["C", "2"], kat: 1 }];
  b.kirisler = [{ no: 1, kat: 1, bas: ["B", "1"], son: ["B", "3"] }, { no: 2, kat: 1, bas: ["C", "1"], son: ["C", "3"] }];
  b.dosemeler = [{ no: 1, kat: 1, kose: [["A", "1"], ["B", "2"]] }, { no: 2, kat: 1, kose: [["A", "1"], ["C", "2"]] }];
  b.ek_yukler.push({ tur: "kiris", kiris: 2, durum: "G", q: 2 }, { tur: "doseme", doseme: 2, g: 1, q: 0 });
  const t = A.aksSil(b, { yon: "x", ad: "C", secenek: "tasi" });
  assert.equal(t.silindi, true);
  const m = t.model;
  const anahtar = function (r) { return A.refAnahtar(m, r); };
  const cift = new Set(), kose = new Set();
  for (const c of m.cubuklar) {
    const k = [anahtar(c.i), anahtar(c.j)].sort().join("#");
    assert.ok(!cift.has(k), "çakışan çubuk: " + k);
    assert.notEqual(anahtar(c.i), anahtar(c.j), "sıfır boylu çubuk " + c.no);
    cift.add(k);
  }
  for (const p of m.paneller) { const k = p.kose.map(anahtar).sort().join("#"); assert.ok(!kose.has(k), "çakışan panel"); kose.add(k); }
  assert.equal(m.cubuklar.length, 4, "B kolonları + B kirişi + AB kirişi kalır");
  assert.ok(!m.cubuklar.some(function (c) { return c.no === bc; }), "B–C kirişi sıfır boylu oldu: silindi");
  assert.deepEqual(m.paneller.map(function (p) { return p.no; }), [1]);
  // yükler: çakışan kopyanınki kalana aktarıldı, silinenlerinki atıldı; kren yolu yeniden yazıldı
  assert.deepEqual(m.ek_yukler.filter(function (y) { return y.tur === "cubuk"; }).map(function (y) { return y.cubuk; }), [3]);
  assert.deepEqual(m.ek_yukler.filter(function (y) { return y.tur === "panel"; }).map(function (y) { return y.panel; }), [1]);
  assert.deepEqual(m.kren[0].yol, [3]);
  // mesnetler aynı düğümde birleşti (serbestlikler VEYA)
  assert.equal(m.mesnetler.length, 1);
  assert.deepEqual([m.mesnetler[0].rx, m.mesnetler[0].ry, m.mesnetler[0].rz], [true, true, true]);
  // aks–kat: aynı kesişime düşen kolon, aynı aralığı tekrarlayan kiriş ve döşeme silinir; yükleri kalana
  assert.deepEqual(m.kolonlar.map(function (c) { return c.no; }), [1]);
  assert.deepEqual(m.kirisler.map(function (c) { return c.no; }), [1]);
  assert.deepEqual(m.dosemeler.map(function (c) { return c.no; }), [1]);
  assert.deepEqual(m.ek_yukler.filter(function (y) { return y.tur === "kiris"; }).map(function (y) { return y.kiris; }), [1]);
  assert.deepEqual(m.ek_yukler.filter(function (y) { return y.tur === "doseme"; }).map(function (y) { return y.doseme; }), [1]);
  assert.ok(t.uyarilar.some(function (u) { return /Aynı iki kesişimi bağlayan/.test(u); }), t.uyarilar.join(" "));
  // ModelOps denetimi: çakışan çubuk yok
  assert.deepEqual(M.denetle(m).uyarilar.filter(function (u) { return u.kod === "cakisan-cubuk" || u.kod === "sifir-boy"; }), []);
});
/**
 * V çaprazlı iki katlı çerçeve (ui-s3-13): X A 0, B 6, C 12; Y 1 0, 2 6; Z ±0.00, +3.50, +7.00. Üst kattaki V çaprazının tepesi
 * B1–C1/+3.50 kirişinin ortasındaki bölme düğümü 100001 (kiriş 14 + 27 olarak bölünmüş; üreteç 2). Kren yolu 15 → 16 (+3.50, Y 2).
 */
function vCerceve() {
  const ak = A.hizliAks({ x: "2@6", y: "6", z: "2@3.5" });
  const b = { tur: "bina", surum: 3, akslar: ak, katlar: A.katlarTuret(ak), cubuklar: [], paneller: [], mesnetler: [], dugumler: [], ek_yukler: [], kesitler: {} };
  const Z = ak.z.map(function (z) { return z.ad; });      // ["±0.00", "+3.50", "+7.00"]
  let n = 0;
  const cb = function (i, j, tur, ek) { const c = Object.assign({ no: ++n, i: i, j: j, tur: tur, kesit: tur === "kolon" ? "HEA300" : "IPE300" }, ek || {}); b.cubuklar.push(c); return c; };
  for (const x of ["A", "B", "C"]) for (const y of ["1", "2"]) { cb(G(x, y, Z[0]), G(x, y, Z[1]), "kolon"); cb(G(x, y, Z[1]), G(x, y, Z[2]), "kolon"); }   // 1–12
  for (const z of [Z[1], Z[2]]) {
    for (const y of ["1", "2"]) { cb(G("A", y, z), G("B", y, z), "kiris"); cb(G("B", y, z), G("C", y, z), "kiris"); }
    for (const x of ["A", "B", "C"]) cb(G(x, "1", z), G(x, "2", z), "kiris");
  }                                                                                                                  // 13–26 (kat başına 7)
  // B1–C1/+3.50 kirişi (14) V tepesinde bölünmüş: 14 = B1 → 100001, 27 = 100001 → C1
  b.cubuklar[13].j = { dugum: 100001 };
  cb({ dugum: 100001 }, G("C", "1", Z[1]), "kiris");                                                                  // 27
  b.dugumler.push({ no: 100001, tur: "bolme", cubuk_i: G("B", "1", Z[1]), cubuk_j: G("C", "1", Z[1]), oran: 0.5, kaynak: { uretec: 2 } });
  const mafsal = { serbest: { i: ["My", "Mz"], j: ["My", "Mz"] }, kaynak: { uretec: 2 }, kesit: "HEA200" };
  cb({ dugum: 100001 }, G("B", "1", Z[2]), "capraz", mafsal);                                                        // 28
  cb({ dugum: 100001 }, G("C", "1", Z[2]), "capraz", mafsal);                                                        // 29
  b.uretecler = [{ no: 2, tur: "capraz", goz: [G("B", "1", Z[1]), G("C", "1", Z[1]), G("C", "1", Z[2]), G("B", "1", Z[2])], tip: "V", secenek: { kesit: "HEA200" }, bolunen: [[14, 27]] }];
  b.paneller = [Z[1], Z[2]].map(function (z, k) { return { no: k + 1, kose: [G("B", "1", z), G("C", "1", z), G("C", "2", z), G("B", "2", z)], tur: "doseme", dagitim: "iki", kalinlik: 0.14, g: 1.5 }; });
  ["A", "B", "C"].forEach(function (x) { ["1", "2"].forEach(function (y) { b.mesnetler.push({ dugum: G(x, y, Z[0]), ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }); }); });
  b.kren = [{ no: 1, yol: [15, 16] }];
  return b;
}
test("aks sil 'taşı' (ui-s3-13): bölme düğümü (V tepesi) silinen gözdeyse çöker; sıfır boylu ve üst üste binen çubuk kalmaz", function () {
  const b = vCerceve(), once = dondurulmus(b);
  assert.deepEqual(M.denetle(b).uyarilar.filter(function (u) { return u.kod !== "mafsalli-dugum"; }), [], "başlangıç modeli temiz");
  const engel = function (m) { return M.denetle(m).uyarilar.filter(function (u) { return ["sifir-boy", "cakisan-cubuk", "panel-geometri", "eksik-dugum"].indexOf(u.kod) >= 0; }); };
  // 1) X aksı C → B: bölme düğümünün iki dayanağı B1/+3.50'ye düşer
  const t = A.aksSil(b, { yon: "x", ad: "C", secenek: "tasi" });
  assert.equal(t.silindi, true);
  assert.equal(dondurulmus(b), once, "girdi değişmemeli");
  assert.deepEqual(engel(t.model), [], t.uyarilar.join(" "));
  assert.ok(!t.model.dugumler.some(function (d) { return d.no === 100001; }), "çöken bölme düğümü silinir");
  const nolar = t.model.cubuklar.map(function (c) { return c.no; });
  for (const no of [14, 27]) assert.ok(nolar.indexOf(no) < 0, "B1–B1 olan kiriş parçası " + no + " silinir");
  for (const no of [28, 29]) assert.ok(nolar.indexOf(no) < 0, "kolon 6 üstüne düşen çapraz " + no + " silinir");
  assert.ok(t.uyarilar.some(function (u) { return /bölme\/kesişim düğümü o noktaya birleştirildi \(100001\)/.test(u); }), t.uyarilar.join(" "));
  assert.ok(t.uyarilar.some(function (u) { return /28 → 6/.test(u) && /29 → 6/.test(u); }), t.uyarilar.join(" "));
  assert.ok(!(t.model.uretecler || []).some(function (u) { return u.no === 2; }), "elemanı kalmayan üreteç kaydı silinir");
  // REF'ler hep çözülür (silinen düğüme başvuru kalmaz)
  const cz = new A.Cozucu(t.model);
  t.model.cubuklar.forEach(function (c) { cz.coz(c.i); cz.coz(c.j); });
  // 2) Y aksı 1 → 2: B1–C1 kiriş parçaları (14, 27) B2–C2 kirişi 16'nın üstüne düşer → 16 bölme düğümünde bölünüp parçalarla birleşir
  const y = vCerceve();
  y.ek_yukler = [{ tur: "cubuk", cubuk: 16, durum: "G", yon: "Z", q1: -2, q2: -2, x1: 0, x2: null, oransal: false },
    { tur: "cubuk", cubuk: 16, durum: "Q", yon: "Z", q1: -1, q2: -4, x1: 1, x2: 4, oransal: false }];
  const u = A.aksSil(y, { yon: "y", ad: "1", secenek: "tasi" });
  assert.deepEqual(engel(u.model), [], u.uyarilar.join(" "));
  assert.ok(u.model.dugumler.some(function (d) { return d.no === 100001; }), "bölme düğümü çökmez (dayanakları B2 ve C2)");
  assert.ok(!u.model.cubuklar.some(function (c) { return c.no === 16; }), "16, 14 + 27 zinciriyle üst üste: bölünüp birleştirilir");
  assert.ok(u.uyarilar.some(function (x) { return /16 → 14 \+ 27/.test(x); }), u.uyarilar.join(" "));
  const yk = function (no) { return u.model.ek_yukler.filter(function (x) { return x.cubuk === no; }).map(function (x) { return [x.durum, x.x1, x.x2, x.q1, x.q2]; }); };
  assert.deepEqual(yk(14), [["G", 0, null, -2, -2], ["Q", 1, null, -1, -3]], "16'nın yükleri parçalara oranlanarak dağıtılır");
  assert.deepEqual(yk(27), [["G", 0, null, -2, -2], ["Q", 0, 1, -3, -4]]);
  assert.deepEqual(u.model.kren[0].yol, [13, 14, 27], "kren yolu: 15 → 13 (kopya), 16 → 14, 27 (sırasıyla)");
  // 3) Z aksı +7.00 → +3.50: V çaprazları kirişin üstüne yatar; üst kat kirişi 21 (B1–C1) bölme düğümünde bölünüp birleşir; üreteç ayrılır
  const z = A.aksSil(vCerceve(), { yon: "z", ad: "+7.00", secenek: "tasi" });
  assert.equal(z.silindi, true);
  assert.deepEqual(engel(z.model), [], z.uyarilar.join(" "));
  assert.ok(!z.model.cubuklar.some(function (c) { return c.no === 21; }));
  assert.ok(!(z.model.uretecler || []).some(function (x) { return x.no === 2; }), "gözü çöken üreteç kaydı kalmaz");
  assert.ok(!z.model.cubuklar.concat(z.model.dugumler).some(function (x) { return x.kaynak && x.kaynak.uretec === 2; }), "elemanlar üreteçten ayrılır");
  assert.ok(z.uyarilar.some(function (x) { return /üreteçten ayrıldı/.test(x); }), z.uyarilar.join(" "));
  // 4) elemanlarla: bölme düğümü (dolaylı bağlı) ve üreteç kaydı da gider
  const e = A.aksSil(vCerceve(), { yon: "x", ad: "C", secenek: "elemanlarla" });
  assert.deepEqual(engel(e.model), []);
  assert.ok(!(e.model.uretecler || []).length, "elemanları silinen üreteç kaydı kalmaz");
  assert.ok(!e.model.dugumler.length);
});
test("aks sil 'taşı': çakışan çubuklardan doğrultusu değişmeyen kalır — üstüne yatan mafsallı çapraz kolonun yerini almaz (dizi sırası ne olursa olsun)", function () {
  const b = vCerceve();
  // kullanıcı çaprazları kolonlardan önce çizmiş gibi: çaprazlar dizinin başında
  b.cubuklar = b.cubuklar.filter(function (c) { return c.tur === "capraz"; }).concat(b.cubuklar.filter(function (c) { return c.tur !== "capraz"; }));
  const t = A.aksSil(b, { yon: "x", ad: "C", secenek: "tasi" });
  const c6 = cubukBul(t.model, 6);
  assert.ok(c6, "B1 üst kolonu (6) kalır: " + t.uyarilar.join(" "));
  assert.equal(c6.tur, "kolon"); assert.equal(c6.kesit, "HEA300"); assert.equal(c6.serbest, undefined);
  assert.ok(!t.model.cubuklar.some(function (c) { return c.tur === "capraz"; }), "B1 doğrusuna yatan çaprazlar silinir");
  assert.ok(t.uyarilar.some(function (u) { return /28 → 6/.test(u) && /29 → 6/.test(u) && /10 → 6/.test(u); }), t.uyarilar.join(" "));
  // eş doğrusal bölmede de: uzun kolonun parçası, üstüne binen kısa çaprazın yerine kalır
  const u = vCerceve();
  u.cubuklar = u.cubuklar.filter(function (c) { return c.no !== 5 && c.no !== 6; });
  u.cubuklar.unshift({ no: 5, i: G("B", "1", "±0.00"), j: G("B", "1", "+7.00"), tur: "kolon", kesit: "HEA300" });
  u.cubuklar.unshift({ no: 40, i: G("C", "1", "+3.50"), j: G("B", "1", "+7.00"), tur: "capraz", kesit: "HEA200", serbest: { i: ["My", "Mz"], j: ["My", "Mz"] } });
  const w = A.aksSil(u, { yon: "x", ad: "C", secenek: "tasi" });
  assert.deepEqual(M.denetle(w.model).uyarilar.filter(function (x) { return x.kod === "cakisan-cubuk" || x.kod === "sifir-boy"; }), [], w.uyarilar.join(" "));
  assert.ok(!w.model.cubuklar.some(function (c) { return c.tur === "capraz"; }), w.uyarilar.join(" "));
  const kolonB1 = w.model.cubuklar.filter(function (c) { return c.tur === "kolon" && [c.i, c.j].every(function (r) { return r.aks && r.aks[0] === "B" && r.aks[1] === "1"; }); });
  assert.deepEqual(kolonB1.map(function (c) { return [c.i.z, c.j.z]; }).sort(), [["+3.50", "+7.00"], ["±0.00", "+3.50"]], "kolon 5 B1/+3.50'te bölünür, iki parçası da kolon");
});
test("aks sil 'taşı': doğruları paralel kalan kesişim düğümü (X çaprazı gözü tek doğruya iner) çöker; kata bağlı Z aksında {aks, kat} REF'leri de taşınır", function () {
  const b = ornek();      // Y: 1 0, 2 5, 3 10; Z: ±0.00 (kat 0), +4.50 (kat 1), +8.00 (kat 2)
  const z0 = "±0.00", z1 = "+4.50";
  b.cubuklar = [{ no: 1, i: G("A", "1", z0), j: G("A", "1", z1), tur: "kolon" }, { no: 2, i: G("A", "2", z0), j: G("A", "2", z1), tur: "kolon" },
    { no: 3, i: G("A", "1", z1), j: G("A", "2", z1), tur: "kiris" },
    { no: 4, i: G("A", "1", z0), j: { dugum: 100001 }, tur: "capraz" }, { no: 5, i: { dugum: 100001 }, j: G("A", "2", z1), tur: "capraz" },
    { no: 6, i: G("A", "2", z0), j: { dugum: 100001 }, tur: "capraz" }, { no: 7, i: { dugum: 100001 }, j: G("A", "1", z1), tur: "capraz" }];
  b.dugumler = [{ no: 100001, tur: "kesisim", a: [G("A", "1", z0), G("A", "2", z1)], b: [G("A", "2", z0), G("A", "1", z1)] }];
  b.mesnetler = [{ dugum: G("A", "1", z0), ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }, { dugum: G("A", "2", z0), ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }];
  const t = A.aksSil(b, { yon: "y", ad: "1", secenek: "tasi" });
  assert.equal(t.silindi, true);
  const d = M.denetle(t.model);          // fırlatmamalı (eskiden: "Kesişim düğümü 100001: doğrular paralel")
  assert.deepEqual(d.uyarilar.filter(function (u) { return ["sifir-boy", "cakisan-cubuk", "eksik-dugum"].indexOf(u.kod) >= 0; }), [], t.uyarilar.join(" "));
  assert.ok(!t.model.dugumler.some(function (x) { return x.no === 100001; }));
  assert.deepEqual(t.model.cubuklar.map(function (c) { return c.no; }), [1], "kolon 2 kolon 1 ile çakıştı; çaprazlar kolonun üstüne düştü; kiriş sıfır boylu");
  assert.ok(t.uyarilar.some(function (u) { return /paralel/.test(u); }), t.uyarilar.join(" "));
  // {aks, kat} REF'li (Z aksı adı yazılmamış) genel model: kat 1'in Z aksı silinince REF'ler komşu Z aksına (adla) taşınır
  const k = ornek();
  k.cubuklar = [{ no: 1, i: { aks: ["A", "1"], kat: 0 }, j: { aks: ["A", "1"], kat: 1 }, tur: "kolon" }, { no: 2, i: { aks: ["A", "1"], kat: 1 }, j: { aks: ["A", "1"], kat: 2 }, tur: "kolon" },
    { no: 3, i: { aks: ["A", "1"], kat: 1 }, j: { aks: ["B", "1"], kat: 1 }, tur: "kiris" }];
  const u = A.aksSil(k, { yon: "z", ad: "+4.50", secenek: "tasi" });
  assert.equal(u.silindi, true);
  assert.deepEqual(M.denetle(u.model).uyarilar.filter(function (x) { return x.kod === "eksik-dugum" || x.kod === "sifir-boy"; }), [], u.uyarilar.join(" "));
  assert.ok(u.model.cubuklar.every(function (c) { return [c.i, c.j].every(function (r) { return r.kat !== 1; }); }), "silinen katın REF'i kalmaz");
  // kat 1 kaldırıldı; üstteki kat (+8.00) 1 numarasını alır (motor kat numaralarını 0'dan ardışık ister) — eski beklenti "kat 1 yok"tu
  assert.deepEqual(u.model.katlar.map(function (x) { return [x.no, x.kot]; }), [[0, 0], [1, 8]]);
  yakin(A.refKoordinat(u.model, cubukBul(u.model, 1).j), [0, 0, 8]);
});
/** Çubuk no ile. */
function cubukBul(m, no) { return m.cubuklar.find(function (c) { return c.no === no; }); }
test("aks sil: kata bağlı Z aksı silinince kat numaraları 0'dan ardışık kalır (katlar, Z aksları, {aks, kat} REF'leri, eleman kat alanları)", function () {
  // ornek(): Z ±0.00 (kat 0), +4.50 (kat 1), +8.00 (kat 2), Saçak 9, Mahya 10.5 — her katta A1 kolonu, +8.00'de A1–B1 kirişi ve panel
  const k = ornek(), z = ["±0.00", "+4.50", "+8.00"];
  k.cubuklar = [
    { no: 1, i: G("A", "1", z[0]), j: G("A", "1", z[1]), tur: "kolon", kat: 1 },
    { no: 2, i: { aks: ["A", "1"], kat: 1 }, j: { aks: ["A", "1"], kat: 2 }, tur: "kolon", kat: 2 },
    { no: 3, i: G("A", "1", z[2]), j: G("B", "1", z[2]), tur: "kiris", kat: 2 },
    { no: 4, i: G("A", "1", z[1]), j: G("B", "1", z[1]), tur: "kiris", kat: 1 },
    { no: 5, i: G("A", "1", "Saçak"), j: G("B", "1", "Saçak"), tur: "kiris" }];
  k.paneller = [{ no: 1, kose: [G("A", "1", z[2]), G("B", "1", z[2]), G("B", "2", z[2]), G("A", "2", z[2])], tur: "doseme", kat: 2 }];
  k.ek_yukler = [{ tur: "dugum", aks: ["A", "1"], kat: 2, durum: "G", FZ: -5 }];
  k.kolonlar = [{ no: 1, aks: ["C", "3"], kat: 0 }];
  const zKat = function (m) { return m.akslar.z.filter(function (a) { return a.kat != null; }).map(function (a) { return [a.ad, a.kat]; }); };
  // 1) taşı (+4.50 → komşu +8.00): kat 1 kalkar, kat 2 → 1; silinen katı taşıyan elemanlar (kat: 1) hedef kata (+8.00 → yeni 1)
  const t = A.aksSil(k, { yon: "z", ad: z[1], secenek: "tasi" });
  assert.equal(t.silindi, true);
  assert.deepEqual(t.model.katlar.map(function (x) { return x.no; }), [0, 1]);
  assert.deepEqual(zKat(t.model), [["±0.00", 0], ["+8.00", 1]]);
  assert.equal(cubukBul(t.model, 3).kat, 1, "+8.00 kirişi: kat 2 → 1");
  assert.equal(cubukBul(t.model, 1).kat, 1, "kolon 1 (±0.00 → +8.00'e uzadı): silinen kat 1 → hedef kat (yeni 1)");
  assert.equal(t.model.paneller[0].kat, 1);
  assert.equal(t.model.ek_yukler[0].kat, 1, "aks–kat düğüm yükü de kayar");
  assert.equal(t.model.kolonlar[0].kat, 0, "alttaki kat numarası değişmez");
  t.model.cubuklar.forEach(function (c) { [c.i, c.j].forEach(function (r) { assert.ok(r.kat == null || r.kat <= 1, JSON.stringify(r)); }); });
  yakin(A.refKoordinat(t.model, { aks: ["A", "1"], kat: 1 }), [0, 0, 8], 1e-9, "kat 1 artık +8.00");
  assert.ok(t.uyarilar.some(function (u) { return /numarası bir azaldı/.test(u); }), t.uyarilar.join(" "));
  // 2) elemanlarla: silinen kata ait açık kat alanı kalırsa kaldırılır (motor katı geometriden bulur)
  const e = A.aksSil(k, { yon: "z", ad: z[1], secenek: "elemanlarla" });
  assert.deepEqual(e.model.katlar.map(function (x) { return x.no; }), [0, 1]);
  assert.deepEqual(zKat(e.model), [["±0.00", 0], ["+8.00", 1]]);
  assert.deepEqual(e.model.cubuklar.map(function (c) { return [c.no, c.kat]; }), [[3, 1], [5, undefined]]);
  // 3) en üst kat: numara kayması yok
  const u = A.aksSil(k, { yon: "z", ad: z[2], secenek: "tasi" });
  assert.deepEqual(u.model.katlar.map(function (x) { return x.no; }), [0, 1]);
  assert.ok(!u.uyarilar.some(function (x) { return /numarası bir azaldı/.test(x); }), u.uyarilar.join(" "));
  // girdi değişmez
  assert.equal(k.cubuklar[2].kat, 2);
});
test("aks sil 'taşı': ters yönlü kopyanın yükü aynalanarak aktarılır; üreteç REF'leri (makas bas/son) de taşınır", function () {
  const b = ornek();      // X: A 0, B 6, C 12, D 19.5
  b.cubuklar = [{ no: 1, i: G("A", "1", "+4.50"), j: G("B", "1", "+4.50"), tur: "kiris" }, { no: 2, i: G("C", "1", "+4.50"), j: G("A", "1", "+4.50"), tur: "kiris" },
    { no: 3, i: G("C", "2", "+4.50"), j: G("D", "2", "+4.50"), tur: "makas-alt", kaynak: { uretec: 1 } }];
  b.ek_yukler = [{ tur: "cubuk", cubuk: 2, durum: "Q", yon: "Z", q1: -1, q2: -3, x1: 0, x2: 0.25, oransal: true }];
  b.uretecler = [{ no: 1, tur: "makas", tip: "pratt", bas: G("C", "2", "+4.50"), son: G("D", "2", "+4.50"), yukseklik: 1, goz: 4 }];
  const t = A.aksSil(b, { yon: "x", ad: "C", secenek: "tasi" });
  assert.deepEqual(t.model.cubuklar.map(function (c) { return c.no; }), [1, 3]);
  const y = t.model.ek_yukler[0];
  assert.equal(y.cubuk, 1);
  assert.deepEqual([y.x1, y.x2, y.q1, y.q2], [0.75, null, -3, -1], "çubuk 2 (B → A) çubuk 1'e (A → B) göre ters: konum ve şiddet aynalanır");
  assert.deepEqual(t.model.uretecler[0].bas, G("B", "2", "+4.50"), "makas açıklığı REF'i komşu aksa taşınır");
  // yeniden adlandırma da üreteç REF'lerini izler
  const r = A.aksYenidenAdlandir(b, { yon: "x", eski: "D", yeni: "E" });
  assert.deepEqual(r.model.uretecler[0].son, G("E", "2", "+4.50"));
});
test("görsel özellikler ve sıralama", function () {
  const b = ornek();
  const r = A.aksOzellik(b, { yon: "x", ad: "B", ozellik: { tur: "ikincil", gorunur: false, balon: "iki" } });
  const a = r.model.akslar.x[1];
  assert.deepEqual([a.tur, a.gorunur, a.balon], ["ikincil", false, "iki"]);
  assert.throws(function () { A.aksOzellik(b, { yon: "x", ad: "B", ozellik: { balon: "ust" } }); }, /Balon/);
  const z = A.aksOzellik(b, { yon: "z", ad: "Saçak", ozellik: { kat: 3 } });
  assert.ok(z.model.katlar.some(function (k) { return k.no === 3 && k.kot === 9; }));
  assert.throws(function () { A.aksOzellik(b, { yon: "z", ad: "Saçak", ozellik: { kat: 1 } }); }, /başka bir Z/);
  const c = JSON.parse(JSON.stringify(b));
  c.akslar.x.reverse();
  assert.deepEqual(A.aksSirala(c, { yon: "x" }).model.akslar.x.map(function (x) { return x.ad; }), ["A", "B", "C", "D"]);
});
test("ek sistemler: ekle (varsayılanlar), güncelle (ad değişince REF'ler), sil (bağlı kayıt onayı)", function () {
  let b = ornek();
  b = A.sistemEkle(b, { ad: "S", tur: "silindirik" }).model;
  const s = b.aks_sistemleri[0];
  assert.deepEqual(s.r.map(function (x) { return x.konum; }), [5, 10]);
  assert.deepEqual(s.teta.map(function (x) { return x.konum; }), [0, 30, 60, 90]);
  assert.equal(s.z, null);
  assert.throws(function () { A.sistemEkle(b, { ad: "S" }); }, /zaten var/);
  assert.throws(function () { A.sistemEkle(b, { ad: "GLOBAL" }); }, /ayrılmıştır/);
  b.cubuklar = [{ no: 1, i: { sistem: "S", aks: ["R1", "T1"], z: "±0.00" }, j: { sistem: "S", aks: ["R2", "T1"], z: "±0.00" } }];
  const g = A.sistemGuncelle(b, "S", { ad: "HALKA", aci: 15, orijin: [1, 2, 0] }).model;
  assert.equal(g.cubuklar[0].i.sistem, "HALKA");
  yakin(A.refKoordinat(g, g.cubuklar[0].j), [1 + 10 * Math.cos(15 * Math.PI / 180), 2 + 10 * Math.sin(15 * Math.PI / 180), 0]);
  const o = A.sistemSil(g, "HALKA");
  assert.equal(o.onayGerekli, true);
  assert.deepEqual(o.bagli.cubuklar, [1]);
  const e = A.sistemSil(g, "HALKA", "elemanlarla").model;
  assert.equal(e.aks_sistemleri.length, 0);
  assert.equal(e.cubuklar.length, 0);
  assert.throws(function () { A.sistemSil(g, "GLOBAL"); }, /silinemez/);
});
test("saf işlevler girdiyi değiştirmez", function () {
  const b = elemanli();
  b.aks_sistemleri = sistemli().aks_sistemleri;
  const once = dondurulmus(b);
  A.aksTasi(b, { yon: "y", ad: "2", konum: 6, kaydir: true });
  A.aksEkle(b, { yon: "x", arasina: ["A", "B"] });
  A.aksSil(b, { yon: "x", ad: "B", secenek: "tasi" });
  A.aksSil(b, { yon: "x", ad: "B", secenek: "elemanlarla" });
  A.aksYenidenAdlandir(b, { yon: "x", eski: "A", yeni: "Z" });
  A.yenidenHarfle(b, { yon: "y", ilk: "5" });
  A.aksOzellik(b, { yon: "x", ad: "A", ozellik: { tur: "ikincil" } });
  A.sistemGuncelle(b, "KANAT", { ad: "K2" });
  A.sistemSil(b, "KUBBE", "elemanlarla");
  A.katlariSenkronla(b); A.yukselt(b);
  assert.equal(dondurulmus(b), once);
});

// ------------------------------------------------------------------ SVG katmanı ve sürükleme
test("sahne katmanı: balonlar, ölçü zinciri, kesişimler; cephede Z etiketleri; NaN yok", function () {
  const b = sistemli();
  const iz = function (X, Y, Z) { return [100 + 10 * X, 300 - 10 * Y - 0 * Z]; };
  const s = A.sahneKatmani(b, { tur: "plan", z: "±0.00" }, iz, { secili: { yon: "x", ad: "C" } });
  assert.ok(s.startsWith('<g class="aks-katman">'));
  assert.equal((s.match(/class="aks-balon /g) || []).length, 4 + 3 + 2 + 2 + 4 + 2, "GLOBAL 7, KANAT 4, KUBBE 4 θ + 2 R");
  assert.ok(s.includes('data-aks-sistem="GLOBAL" data-aks-yon="x" data-aks-ad="C"'));
  assert.ok(/aks-balon aks-s0 aks-secili/.test(s));
  assert.ok(s.includes(">6,00<") && s.includes(">7,50<") && s.includes(">19,50<"), "aralık ve toplam ölçüsü");
  assert.equal((s.match(/class="aks-kesisim/g) || []).length, 12 + 4 + 8);
  assert.ok(!/NaN|undefined/.test(s));
  const ref = JSON.parse(s.match(/data-aks-ref="([^"]+)"/)[1].replace(/&quot;/g, '"'));
  assert.ok(A.aksRefMi(ref));
  const c = A.sahneKatmani(b, { tur: "cephe", y: "1" }, function (X, Y, Z) { return [100 + 10 * X, 300 - 10 * Z]; });
  assert.equal((c.match(/aks-zbalon/g) || []).length, 5);
  assert.ok(c.includes("Saçak  +9,00") && c.includes(">±0,00<"));
  const d = A.sahneKatmani(b, { tur: "3b", z: "Saçak" }, function (X, Y, Z) { return [100 + 10 * X - 5 * Y, 300 - 10 * Z + 3 * Y]; });
  assert.equal((d.match(/aks-zbalon/g) || []).length, 5);
  assert.ok(!/NaN/.test(d));
  // gizli aks çizilmez; ikincil kesikli sınıfta
  const h = A.aksOzellik(ornek(), { yon: "x", ad: "B", ozellik: { gorunur: false } }).model;
  assert.ok(!A.sahneKatmani(h, { tur: "plan" }, iz).includes('data-aks-ad="B"'));
  const i2 = A.aksOzellik(ornek(), { yon: "x", ad: "B", ozellik: { tur: "ikincil" } }).model;
  assert.ok(A.sahneKatmani(i2, { tur: "plan" }, iz).includes("aks-cizgi aks-ikincil"));
  // önizleme (sürükleme): aks geçici konumda
  const on = A.sahneKatmani(ornek(), { tur: "plan" }, iz, { onizleme: { sistem: "GLOBAL", yon: "x", ad: "B", konum: 8 } });
  assert.ok(on.includes(">8,00<"));
  assert.equal(A.sahneKatmani(ornek(), { tur: "plan", z: "YOK" }, iz), '<g class="aks-katman"></g>');
});
test("balon sürükleme: ekran farkı → konum, 0,05 m yakalama; kenar payları; uygun izdüşüm", function () {
  const b = ornek();
  const iz = function (X, Y) { return [10 * X, 200 - 10 * Y]; };
  assert.equal(A.surukleKonum(b, { yon: "x", ad: "B" }, iz, [60, 0], [77.3, 40]), 7.75);
  assert.equal(A.surukleKonum(b, { yon: "y", ad: "2" }, iz, [0, 150], [0, 141.2]), 5.9);
  assert.equal(A.surukleKonum(b, { yon: "x", ad: "B" }, iz, [60, 0], [61.2, 0], { adim: 0.5 }), 6);
  assert.equal(A.yuvarla(7.7749, 0.05), 7.75);
  const kp = A.kenarPaylari(b, { tur: "cephe", y: "1" });
  assert.ok(kp.sag > kp.ust && kp.alt > kp.ust);
  const f = A.uygunIzdusum(b, { tur: "plan" }, 600, 400);
  const p0 = f(0, 0, 0), p1 = f(19.5, 10, 0);
  assert.ok(p0[0] >= kp.sol - 1e-9 || p0[0] > 0);
  assert.ok(p1[0] <= 600 && p1[1] >= 0 && p0[1] <= 400 && p0[1] > p1[1]);
});

// ------------------------------------------------------------------ model_ops ile birlikte
test("model_ops: aks REF'li çubuk, kat dışı Z aksı (sanal düğüm), REF adla geri yazılır", function () {
  let b = ornek();
  let r = M.cubukCiz(b, G("A", "1", "±0.00"), G("A", "1", "Saçak"), { tur: "kolon" });
  b = r.model;
  assert.deepEqual(b.cubuklar[0].i, G("A", "1", "±0.00"));
  assert.deepEqual(b.cubuklar[0].j, G("A", "1", "Saçak"));
  yakin(M.uzunluk(b, 1), 9);
  yakin(M.dugumKonumu(b, G("B", "3", "Mahya")), [6, 10, 10.5]);
  assert.equal(M.dugumNo(b, G("A", "1", "+4.50")), 1001, "kat Z aksı aks–kat numarası");
  assert.ok(M.dugumNo(b, G("A", "1", "Saçak")) >= 800001, "kat dışı Z aksı: sanal aks düğümü");
  // koordinatlı REF aks kesişimine düşerse aks REF'ine çevrilir
  r = M.cubukCiz(b, [19.5, 10, 4.5], [19.5, 10, 10.5]);
  assert.deepEqual(r.model.cubuklar[1].i, G("D", "3", "+4.50"));
  assert.deepEqual(r.model.cubuklar[1].j, G("D", "3", "Mahya"));
  // eski {aks, kat} REF'i de geçerli
  r = M.cubukCiz(b, { aks: ["B", "1"], kat: 0 }, { aks: ["B", "1"], kat: 1 });
  yakin(M.uzunluk(r.model, 2), 4.5);
  // Z aksı taşınınca çubuk boyu değişir (yapışık), model REF'leri aynı
  const t = A.aksTasi(b, { yon: "z", ad: "Saçak", konum: 9.6 }).model;
  yakin(M.uzunluk(t, 1), 9.6);
  // ek sistem REF'i
  const bs = sistemli();
  const k = M.cubukCiz(bs, { sistem: "KANAT", aks: ["A", "1"], z: "±0.00" }, { sistem: "KANAT", aks: ["B", "1"], z: "±0.00" }).model;
  yakin(M.uzunluk(k, 1), 6);
  assert.equal(k.cubuklar[0].i.sistem, "KANAT");
  assert.throws(function () { M.cubukCiz(b, G("Q", "1", "Saçak"), G("A", "1", "Saçak")); }, /Aks başvurusu geçersiz/);
});
test("model_ops.aksaBagla: kesişime düşen düğüm aks REF'i, bölünmüş çubuktaki düğüm bölme düğümü olur", function () {
  let b = ornek();
  b = M.cubukCiz(b, G("A", "1", "Saçak"), G("D", "1", "Saçak"), { tur: "kiris" }).model;
  b = M.bol(b, 1, { parca: 3 }).model;                          // serbest düğümler (6.5, 0, 9) ve (13, 0, 9)
  b.dugumler.push({ no: 100010, X: 12, Y: 5, Z: 9 });            // C2 Saçak kesişimi
  b = M.cubukCiz(b, { dugum: 100010 }, G("C", "3", "Saçak")).model;
  b.dugumler.push({ no: 100011, X: 40, Y: 40, Z: 0 });           // hiçbir yere düşmeyen
  const r = M.aksaBagla(b);
  assert.deepEqual(r.baglanan.map(function (x) { return x.no; }), [100010]);
  assert.deepEqual(r.bolme.sort(), [100001, 100002]);
  assert.deepEqual(r.kalan, [100011]);
  const m = r.model;
  assert.ok(!m.dugumler.some(function (d) { return d.no === 100010; }));
  assert.deepEqual(m.cubuklar.find(function (c) { return c.no === 4; }).i, G("C", "2", "Saçak"));
  const d1 = m.dugumler.find(function (d) { return d.no === 100001; });
  assert.equal(d1.tur, "bolme");
  assert.deepEqual([d1.cubuk_i, d1.cubuk_j], [G("A", "1", "Saçak"), G("D", "1", "Saçak")]);
  yakin(d1.oran, 1 / 3, 1e-8);
  assert.equal(d1.X, undefined);
  // aks taşınınca bölme düğümleri ve çubuklar birlikte
  const t = A.aksTasi(m, { yon: "x", ad: "D", konum: 22.5 }).model;
  yakin(M.dugumKonumu(t, { dugum: 100002 }), [15, 0, 9], 1e-5);
  const t2 = A.aksTasi(m, { yon: "z", ad: "Saçak", konum: 9.5 }).model;
  yakin(M.dugumKonumu(t2, { dugum: 100001 })[2], 9.5);
  assert.deepEqual(M.denetle(m).uyarilar.filter(function (u) { return u.kod === "eksik-dugum"; }), []);
  // bölme düğümü taşınırsa serbest olur (uyarıyla)
  const s = M.dugumTasi(m, 100001, 6.5, 0.5, 9);
  assert.equal(s.model.dugumler.find(function (d) { return d.no === 100001; }).tur, undefined);
  assert.ok(s.uyarilar.some(function (u) { return /bölme düğümüydü/.test(u); }));
});
test("model_ops: gözden çapraz üretimi ve kat Z aksı adıyla REF yazımı", function () {
  const b = ornek();
  const goz = A.gozler(b, { tur: "cephe", y: "1" })[0];
  const r = M.caprazUret(b, goz.koseler, "X", { kesit: "L80x8" });
  const c = r.model.cubuklar.filter(function (x) { return x.tur === "capraz"; });
  assert.equal(c.length, 2);
  assert.deepEqual(c[0].i, G("A", "1", "±0.00"));
  assert.deepEqual(c[0].j, G("B", "1", "+4.50"));
  // akslar.z varken aks–kat düğümleri {aks, z} olarak yazılır; yoksa {aks, kat}
  const eski = { tur: "bina", akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 5 }], y: [{ ad: "1", konum: 0 }] }, katlar: [{ no: 0, kot: 0 }, { no: 1, kot: 3 }] };
  assert.deepEqual(M.cubukCiz(eski, [0, 0, 0], [0, 0, 3]).model.cubuklar[0].j, { aks: ["A", "1"], kat: 1 });
  const yeni = A.yukselt(eski).model;
  assert.deepEqual(M.cubukCiz(yeni, [0, 0, 0], [0, 0, 3]).model.cubuklar[0].j, { aks: ["A", "1"], z: "+3.00" });
});
