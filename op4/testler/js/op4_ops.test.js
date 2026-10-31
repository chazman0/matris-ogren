// op4/js/op4_ops.js sınamaları (B, F1 iş 1.3; MIMARI §10.2–§10.4, kabul B3). Çalıştırma: node --test op4/testler/js/*.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const OP4 = path.join(__dirname, "..", "..");
const DOCS = path.join(OP4, "..", "docs");
const O = require(path.join(OP4, "js", "op4_ops.js"));
const MO = require(path.join(DOCS, "model_ops.js"));
const SABLON = path.join(OP4, "testler", "derlem", "sablonlar");
const sablon = (ad) => JSON.parse(fs.readFileSync(path.join(SABLON, ad + ".json"), "utf8"));
const SABLONLAR = fs.readdirSync(SABLON).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5)).sort();

/** n × m göz, k kat genel model (aks REF'li kolon / kiriş, isteğe bağlı döşemeler). */
/** Çözümlemedeki kolonlar: {no, P (üst uç)}. */
function kolonlar(C) {
  const l = [];
  for (let k = 0; k < C.nc; k++) {
    if (C.ctur[k] !== O.KODLAR.cubuk_turu.kolon) continue;
    const u = C.xyz[3 * C.ci[k] + 2] >= C.xyz[3 * C.cj[k] + 2] ? C.ci[k] : C.cj[k];
    l.push({ no: +C.cel[k].no, P: [C.xyz[3 * u], C.xyz[3 * u + 1], C.xyz[3 * u + 2]] });
  }
  return l;
}

function izgaraModel(nx, ny, nk, sec) {
  sec = sec || {};
  const xs = [], ys = [], zs = [];
  for (let i = 0; i <= nx; i++) xs.push({ ad: String.fromCharCode(65 + i), konum: 6 * i });
  for (let j = 0; j <= ny; j++) ys.push({ ad: String(j + 1), konum: 5 * j });
  for (let k = 0; k <= nk; k++) zs.push({ ad: k === 0 ? "±0.00" : "+" + (3 * k).toFixed(2), konum: 3 * k, kat: k });
  const m = O.bosModel({ baslik: "Izgara" });
  m.akslar = { x: xs, y: ys, z: zs };
  m.katlar = zs.map((z) => ({ no: z.kat, ad: z.ad, kot: z.konum }));
  m.kesitler = { KOLON: { tip: "profil", profil: "HEA 340", malzeme: "S355" }, KIRIS: { tip: "profil", profil: "IPE 300", malzeme: "S275" } };
  const r = (a, b, z) => ({ aks: [a, b], z: z });
  let no = 1, pno = 1;
  for (let k = 1; k <= nk; k++) {
    for (const x of xs) for (const y of ys) m.cubuklar.push({ no: no++, i: r(x.ad, y.ad, zs[k - 1].ad), j: r(x.ad, y.ad, zs[k].ad), tur: "kolon", kesit: "KOLON" });
    for (let i = 0; i < nx; i++) for (const y of ys) m.cubuklar.push({ no: no++, i: r(xs[i].ad, y.ad, zs[k].ad), j: r(xs[i + 1].ad, y.ad, zs[k].ad), tur: "kiris", kesit: "KIRIS" });
    for (const x of xs) for (let j = 0; j < ny; j++) m.cubuklar.push({ no: no++, i: r(x.ad, ys[j].ad, zs[k].ad), j: r(x.ad, ys[j + 1].ad, zs[k].ad), tur: "kiris", kesit: "KIRIS" });
    if (sec.doseme !== false) {
      for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
        m.paneller.push({ no: pno++, tur: "doseme", kalinlik: 0.15, kose: [r(xs[i].ad, ys[j].ad, zs[k].ad), r(xs[i + 1].ad, ys[j].ad, zs[k].ad), r(xs[i + 1].ad, ys[j + 1].ad, zs[k].ad), r(xs[i].ad, ys[j + 1].ad, zs[k].ad)] });
      }
    }
  }
  return m;
}

test("TASLAK boş: bütün Faz 1 işlevleri uygulandı (B3)", () => {
  assert.deepEqual([...O.TASLAK], []);
});

test("profilAdiNormal: ortak vektörlerin hepsi (MIMARI §10.4)", () => {
  const v = JSON.parse(fs.readFileSync(path.join(OP4, "testler", "ortak", "profil_adlari.json"), "utf8")).vektorler;
  for (const x of v) {
    const r = O.profilAdiNormal(x.girdi);
    assert.equal(r.ad, x.ad, x.girdi);
    assert.equal(r.aile, x.aile, x.girdi);
    assert.equal(r.durum, x.durum, x.girdi);
  }
});

test("profilAdiNormal: kütüphane sınırı, basit kesitler, RHS/SHS/CHS ölçüyle", () => {
  assert.deepEqual(O.profilAdiNormal("HEA 345"), { ad: null, aile: "HEA", durum: "kutuphanede_yok" });
  assert.deepEqual(O.profilAdiNormal("IPE 600"), { ad: "IPE 600", aile: "IPE", durum: "tamam" });
  assert.deepEqual(O.profilAdiNormal("IPN 200"), { ad: null, aile: "IPN", durum: "kutuphanede_yok" });
  assert.deepEqual(O.profilAdiNormal("UPN 90"), { ad: null, aile: "UPN", durum: "kutuphanede_yok" });
  assert.deepEqual(O.profilAdiNormal("RHS 200x100x6"), { ad: "KUTU 200x100x6", aile: "KUTU", durum: "tamam" });
  assert.deepEqual(O.profilAdiNormal("SHS 150x150x8"), { ad: "KUTU 150x8", aile: "KUTU", durum: "tamam" });
  assert.deepEqual(O.profilAdiNormal("CHS 168,3 x 6,3"), { ad: "BORU 168.3x6.3", aile: "BORU", durum: "tamam" });
  assert.deepEqual(O.profilAdiNormal("BORU 168.3x6.3"), { ad: "BORU 168.3x6.3", aile: "BORU", durum: "tamam" });
  assert.deepEqual(O.profilAdiNormal("2L 70x7 s=10"), { ad: "2L 70x7 s=10", aile: "2L", durum: "tamam" });
  assert.deepEqual(O.profilAdiNormal("L 100x10"), { ad: "L 100x10", aile: "L", durum: "tamam" });
  assert.deepEqual(O.profilAdiNormal("L 100.100.10"), { ad: "L 100x10", aile: "L", durum: "tamam" });
  // eşit olmayan kollu korniyer motorda yok (docs/ifc_disari.js basitProfil: "yalnız eşit kollu korniyer desteklenir")
  assert.deepEqual(O.profilAdiNormal("L 100x50x6"), { ad: null, aile: "L", durum: "kutuphanede_yok" });
  assert.equal(O.profilAdiNormal("RHS").durum, "anlasilmadi");
  assert.equal(O.profilAdiNormal(null).durum, "anlasilmadi");
  assert.equal(O.profilAdiNormal({}).durum, "anlasilmadi");
  // kütüphane = docs/ifc_disari.js PROFILLER = yapi_veri.PROFILLER (56 I/H profil)
  const py = fs.readFileSync(path.join(OP4, "..", "yapi_veri.py"), "utf8");
  const adlar = [...py.matchAll(/^\s*"((?:IPE|HEA|HEB) \d+)":\s*_P\(/gm)].map((m) => m[1]);
  assert.equal(adlar.length, 56);
  for (const a of adlar) assert.equal(O.profilAdiNormal(a.replace(" ", "")).ad, a, a);
});

test("katUyeligi: kolon kat aralığı, çok katlı kolon, yatay eleman, temel ve üst sınır (MIMARI §10.2)", () => {
  const m = izgaraModel(1, 1, 2);
  const zs = m.akslar.z;
  m.akslar.z.push({ ad: "Mahya", konum: 7.5 });     // kat dışı Z aksı
  m.cubuklar.push({ no: 100, i: { aks: ["A", "1"], z: zs[0].ad }, j: { aks: ["A", "1"], z: zs[2].ad }, tur: "kolon" });   // 0 → 6 m
  m.cubuklar.push({ no: 101, i: { aks: ["A", "1"], z: zs[0].ad }, j: { aks: ["B", "1"], z: zs[0].ad }, tur: "kiris" });   // temel kirişi
  m.cubuklar.push({ no: 102, i: { aks: ["A", "1"], z: zs[2].ad }, j: { aks: ["B", "1"], z: "Mahya" }, tur: "diger" });    // eğik, üst uç 7,5
  m.cubuklar.push({ no: 103, i: { aks: ["A", "2"], z: zs[2].ad }, j: { aks: ["A", "2"], z: "Mahya" }, tur: "kolon" });    // üst katın üstü
  const k = O.katUyeligi(m);
  assert.deepEqual(k.seviyeler.map((s) => [s.ad, s.z, s.kat]), [["±0.00", 0, 0], ["+3.00", 3, 1], ["+6.00", 6, 2], ["Mahya", 7.5, -1]]);
  assert.deepEqual(k.cubuk[1], [1]);
  assert.deepEqual(k.cubuk[100], [1, 2]);
  assert.deepEqual(k.cubuk[101], [0]);
  assert.deepEqual(k.cubuk[102], [2]);
  assert.deepEqual(k.cubuk[103], [2]);
  assert.equal(k.seviye.cubuk[102], "Mahya");
  // düğüm: kat seviyesinde → o kat; kat dışı (Mahya) → yatay kural (üst katın üstü → üst kat)
  const C = O.cozumle(m);
  const no = (ref) => C.cozucu.no(ref);
  assert.deepEqual(k.dugum[no({ aks: ["A", "1"], z: "±0.00" })], [0]);
  assert.deepEqual(k.dugum[no({ aks: ["B", "2"], z: "+3.00" })], [1]);
  assert.deepEqual(k.dugum[no({ aks: ["B", "1"], z: "Mahya" })], [2]);
  assert.equal(k.seviye.dugum[no({ aks: ["B", "1"], z: "Mahya" })], "Mahya");
  // panel: en yüksek köşenin kotu
  assert.deepEqual(k.panel[1], [1]);
  assert.deepEqual(k.panel[2], [2]);
});

test("katUyeligi: 1 mm toleransı ve kat seviyesi olmayan model", () => {
  const m = izgaraModel(1, 1, 1, { doseme: false });
  m.dugumler = [{ no: 100001, X: 0, Y: 0, Z: 3.0009 }, { no: 100002, X: 0, Y: 0, Z: 3.0011 }];
  const k = O.katUyeligi(m);
  assert.deepEqual(k.dugum[100001], [1]);
  assert.deepEqual(k.dugum[100002], [1]);   // üst katın üstü → üst kat
  const bos = O.bosModel();
  bos.akslar.z = [];
  bos.katlar = [];
  bos.dugumler = [{ no: 100001, X: 1, Y: 2, Z: 3 }];
  assert.deepEqual(O.katUyeligi(bos).dugum[100001], []);
});

test("kullanimYeri: döşeme zarfı — köşe / kenar / iç kolon, dış / iç kiriş, kenar / iç döşeme, düğüm sınıfları (MIMARI §10.3)", () => {
  const m = izgaraModel(3, 3, 1);
  const C = O.cozumle(m);
  const u = O.kullanimYeri(m, { cozum: C });
  const kolonYer = {};
  for (const x of kolonlar(C)) kolonYer[x.P[0] / 6 + "," + x.P[1] / 5] = u.cubuk[x.no].yer;
  for (const [k, y] of Object.entries(kolonYer)) {
    const [i, j] = k.split(",").map(Number);
    const kenar = i === 0 || i === 3 || j === 0 || j === 3, kose = (i === 0 || i === 3) && (j === 0 || j === 3);
    assert.equal(y, kose ? "kose" : kenar ? "kenar" : "ic", k);
  }
  const say = (o, alt) => Object.values(o).filter((v) => v.alt_tur === alt).reduce((s, v) => { s[v.yer] = (s[v.yer] || 0) + 1; return s; }, {});
  assert.deepEqual(say(u.cubuk, "kiris"), { dis: 12, ic: 12 });
  assert.deepEqual(say(u.panel, "doseme"), { kenar: 8, ic: 1 });
  assert.deepEqual(say(u.dugum, "dugum"), { temel: 16, "kolon-ustu": 16 });
});

test("kullanimYeri: L planlı döşeme zarfında iç köşe kenar sayılır; döşemesiz katta kolonların dışbükey zarfı", () => {
  const m = izgaraModel(2, 2, 1);
  m.paneller = m.paneller.filter((p) => p.no !== 4);   // sağ üst göz boş → L plan
  const u = O.kullanimYeri(m);
  const C = O.cozumle(m);
  const yer = (x, y) => {
    for (const c of kolonlar(C)) if (c.P[0] === x && c.P[1] === y) return u.cubuk[c.no].yer;
    return null;
  };
  assert.equal(yer(6, 5), "kenar");      // iç (içbükey) köşe: iç açı 270° → köşe değil
  assert.equal(yer(12, 5), "kose");
  assert.equal(yer(6, 10), "kose");
  assert.equal(yer(12, 10), "ic");       // döşeme zarfının dışında kalan kolon: zarf üstünde değil
  const d = izgaraModel(2, 1, 1, { doseme: false });
  const ud = O.kullanimYeri(d), Cd = O.cozumle(d);
  const yd = {};
  for (const c of kolonlar(Cd)) yd[c.P[0] + "," + c.P[1]] = ud.cubuk[c.no].yer;
  assert.deepEqual(yd, { "0,0": "kose", "0,5": "kose", "6,0": "kenar", "6,5": "kenar", "12,0": "kose", "12,5": "kose" });
});

test("kullanimYeri: konsol kiriş, konsol döşeme, çapraz dış cephe / iç, cephe paneli ±x / ±y", () => {
  const m = izgaraModel(1, 1, 1, { doseme: false });
  m.akslar.x.push({ ad: "C", konum: 8 });
  const z = "+3.00";
  m.cubuklar.push({ no: 50, i: { aks: ["B", "1"], z: z }, j: { aks: ["C", "1"], z: z }, tur: "kiris" });
  m.cubuklar.push({ no: 51, i: { aks: ["A", "1"], z: "±0.00" }, j: { aks: ["B", "1"], z: z }, tur: "capraz" });
  m.dugumler.push({ no: 100001, tur: "bolme", cubuk_i: { aks: ["A", "1"], z: z }, cubuk_j: { aks: ["B", "2"], z: z }, oran: 0.5 });
  m.cubuklar.push({ no: 52, i: { aks: ["A", "1"], z: "±0.00" }, j: { dugum: 100001 }, tur: "capraz" });
  m.paneller.push({ no: 2, tur: "cephe", kose: [{ aks: ["A", "1"], z: "±0.00" }, { aks: ["B", "1"], z: "±0.00" }, { aks: ["B", "1"], z: z }, { aks: ["A", "1"], z: z }] });
  m.paneller.push({ no: 3, tur: "cephe", kose: [{ aks: ["A", "2"], z: "±0.00" }, { aks: ["A", "1"], z: "±0.00" }, { aks: ["A", "1"], z: z }, { aks: ["A", "2"], z: z }] });
  const u = O.kullanimYeri(m);
  assert.equal(u.cubuk[50].yer, "konsol");
  assert.equal(u.cubuk[51].yer, "dis-cephe");
  assert.equal(u.cubuk[52].yer, "ic");
  assert.equal(u.panel[2].yer, "-y");
  assert.equal(u.panel[3].yer, "-x");
  assert.equal(u.dugum[100001].yer, "ara");
  // döşeme varsa zarf döşemelerin birleşimidir: B–C konsol döşemesi yalnız B aksı kirişince taşınır
  const k = izgaraModel(1, 1, 1, { doseme: false });
  k.akslar.x.push({ ad: "C", konum: 8 });
  k.cubuklar.push({ no: 51, i: { aks: ["A", "1"], z: "±0.00" }, j: { aks: ["B", "1"], z: z }, tur: "capraz" });
  k.paneller.push({ no: 1, tur: "doseme", kose: [{ aks: ["B", "1"], z: z }, { aks: ["C", "1"], z: z }, { aks: ["C", "2"], z: z }, { aks: ["B", "2"], z: z }] });
  const u2 = O.kullanimYeri(k);
  assert.equal(u2.panel[1].yer, "konsol");
  assert.equal(u2.cubuk[51].yer, "ic");        // A–B çaprazı döşeme zarfının (B–C) kenarında değil
});

test("sahneCikar: 9 şablonun sayıları ve düğüm numaraları ModelOps ile aynı", () => {
  const beklenen = {
    "betonarme-tek-aciklik": [8, 8, 1, 4], "betonarme-2kat-3x2": [18, 26, 4, 6], "betonarme-3kat-3x3": [36, 63, 12, 9],
    "celik-1kat-depo": [12, 13, 2, 6], "betonarme-4kat-4x3": [60, 116, 24, 12], "betonarme-3kat-surekli-temel": [36, 63, 12, 9],
    "betonarme-4kat-radye": [60, 116, 24, 12], "celik-sanayi-4hol": [232, 423, 124, 43], "celik-cbf-3kat": [55, 119, 18, 12],
  };
  assert.deepEqual(SABLONLAR, Object.keys(beklenen).sort());
  for (const ad of SABLONLAR) {
    const m = sablon(ad);
    const C = O.cozumle(m);
    const s = O.sahneCikar(m, 7, { cozum: C });
    assert.deepEqual([s.dugumler.no.length, s.cubuklar.no.length, s.paneller.no.length, s.mesnetler.dugum.length], beklenen[ad], ad);
    assert.equal(s.sahne_surumu, 7);
    assert.equal(s.model_surumu, +m.surum, ad);
    assert.deepEqual(s.uyarilar, [], ad);
    assert.ok(s.dugumler.xyz instanceof Float64Array && s.cubuklar.i instanceof Uint32Array && s.cubuklar.serbestlik instanceof Uint16Array);
    assert.equal(s.dugumler.xyz.length, 3 * s.dugumler.no.length);
    assert.equal(s.cubuklar.y_yerel.length, 3 * s.cubuklar.no.length);
    // düğüm numaraları ve konumları ModelOps'un iç numaralarıyla aynı (genel görünümde)
    const g = C.g;
    for (let k = 0; k < g.cubuklar.length; k += 7) {
      const c = g.cubuklar[k], idx = s.cubuklar.no.indexOf(+c.no);
      assert.equal(s.dugumler.no[s.cubuklar.i[idx]], MO.dugumNo(g, c.i), ad + " çubuk " + c.no);
      assert.equal(s.dugumler.no[s.cubuklar.j[idx]], MO.dugumNo(g, c.j), ad + " çubuk " + c.no);
      const P = MO.dugumKonumu(g, c.j), q = 3 * s.cubuklar.j[idx];
      assert.deepEqual([s.dugumler.xyz[q], s.dugumler.xyz[q + 1], s.dugumler.xyz[q + 2]], P);
      const e = MO.yerelEksenler(g, c.no);
      for (let a = 0; a < 3; a++) assert.ok(Math.abs(s.cubuklar.y_yerel[3 * idx + a] - e.y[a]) < 1e-12);
    }
    // dizinler sınırlar içinde; kesit / grup dizini ya da SAHNE_YOK
    for (let i = 0; i < s.cubuklar.no.length; i++) {
      assert.ok(s.cubuklar.i[i] < s.dugumler.no.length && s.cubuklar.j[i] < s.dugumler.no.length);
      assert.ok(s.cubuklar.kesit[i] === O.SAHNE_YOK || s.cubuklar.kesit[i] < s.kesitler.length);
    }
    for (let i = 0; i < s.paneller.kose.length; i++) assert.ok(s.paneller.kose[i] < s.dugumler.no.length);
  }
});

test("sahneCikar: aks–kat modeli genel görünümle; kolon / kiriş türleri, mafsal maskesi, akslar ve temeller", () => {
  const m = sablon("celik-1kat-depo");
  const s = O.sahneCikar(m, 1);
  const K = O.KODLAR;
  const tur = Array.from(s.cubuklar.tur);
  assert.equal(tur.filter((t) => t === K.cubuk_turu.kolon).length, 6);
  assert.equal(tur.filter((t) => t === K.cubuk_turu.kiris).length, 7);
  // temeller.mesnet "mafsal" → ux, uy, uz
  assert.deepEqual([...new Set(s.mesnetler.maske)], [0x07]);
  assert.deepEqual([...new Set(s.mesnetler.tur)], [K.mesnet_turu.mafsal]);
  assert.equal(s.temeller.length, 6);
  assert.deepEqual([s.temeller[0].B, s.temeller[0].L, s.temeller[0].h], [1.5, 1.5, 0.6]);
  // akslar: 3 X + 2 Y, aks kimliği eksen·65536 + sıra, ±1,5 m uzantı
  assert.equal(s.akslar.length, 5);
  const B = s.akslar.find((a) => a.ad === "B");
  assert.deepEqual(B.kimlik, { tur: "aks", alt: 0, no: 1 });
  assert.deepEqual([B.bas, B.son], [[6, -1.5, 0], [6, 7.5, 0]]);
  const iki = s.akslar.find((a) => a.ad === "2");
  assert.equal(iki.kimlik.no, 65536 + 1);
  // kesitler: I profil ölçüleri m
  const kes = s.kesitler.find((k) => k.ad === "IPE300");
  assert.deepEqual([kes.profil, kes.tur, kes.h, kes.b], ["IPE 300", K.kesit_turu.I, 0.3, 0.15]);
  assert.equal(s.dugumler.bayrak.filter((b) => b & K.dugum_bayraklari.mesnetli).length, 6);
});

test("sahneCikar: sanayi şablonu — ek Z aksı düğümleri 800001…, serbestlik maskesi, vute bayrağı, cephe ve çatı panelleri", () => {
  const m = sablon("celik-sanayi-4hol");
  const s = O.sahneCikar(m, 1);
  const K = O.KODLAR;
  const sanal = Array.from(s.dugumler.no).filter((n) => n >= 800001);
  assert.ok(sanal.length > 0);
  for (const n of sanal) assert.equal(s.dugumler.tur[Array.from(s.dugumler.no).indexOf(n)], K.dugum_turu.aks_kesisimi);
  const i = Array.from(s.cubuklar.no).indexOf(218);       // rüzgâr kolonu: j ucu N, My, Mz serbest
  assert.equal(s.cubuklar.serbestlik[i], (1 << 6) | (1 << 10) | (1 << 11));
  assert.ok(Array.from(s.cubuklar.bayrak).some((b) => b & K.cubuk_bayraklari.vute));
  const pt = Array.from(s.paneller.tur);
  assert.equal(pt.filter((t) => t === K.panel_turu.cati).length, 96);
  assert.equal(pt.filter((t) => t === K.panel_turu.cephe).length, 28);
  assert.ok(Array.from(s.dugumler.tur).includes(K.dugum_turu.bolme));
});

test("sahneCikar: koordinatlı başvuru, serbest düğüm bayrağı, bağlantısız düğüm, açık mesnet kayıtları", () => {
  const m = O.bosModel();
  m.dugumler = [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 0, Y: 0, Z: 3 }, { no: 100007, X: 9, Y: 9, Z: 9 }];
  m.cubuklar = [{ no: 1, i: { dugum: 100001 }, j: [4, 0, 3], tur: "kiris" }, { no: 2, i: { dugum: 100002 }, j: { X: 4, Y: 0, Z: 3.0004 } }];
  m.mesnetler = [{ dugum: { dugum: 100001 }, ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }, { dugum: 100001, ux: true }, { dugum: { dugum: 100002 } }];
  const s = O.sahneCikar(m, 1);
  const K = O.KODLAR;
  assert.deepEqual(Array.from(s.dugumler.no), [100001, 100002, 100007, 100008]);   // koordinatlı uç: yeni no; 0,4 mm uzaktaki ikinci uç aynı düğüm
  assert.equal(s.cubuklar.j[0], s.cubuklar.j[1]);
  assert.equal(s.cubuklar.tur[1], K.cubuk_turu.kolon === s.cubuklar.tur[1] ? K.cubuk_turu.kolon : K.cubuk_turu.kiris);
  assert.ok(s.cubuklar.bayrak[0] & K.cubuk_bayraklari.serbest_dugume_bagli);
  assert.ok(s.dugumler.bayrak[2] & K.dugum_bayraklari.baglantisiz);
  assert.deepEqual(Array.from(s.mesnetler.maske), [0x3F]);          // tamamen serbest kayıt yok sayılır, aynı düğüm VEYA
  assert.deepEqual(Array.from(s.mesnetler.tur), [K.mesnet_turu.ankastre]);
});

test("oznitelikCikar: 23 sütun, satırlar, değerler ve kodlu biçim", () => {
  const m = sablon("celik-cbf-3kat");
  const t = O.oznitelikCikar(m);
  assert.deepEqual(t.sutunlar.map((c) => c.id), [...O.OZNITELIK_IDLERI]);
  const ids = JSON.parse(fs.readFileSync(path.join(OP4, "veri", "oznitelikler.json"), "utf8")).oznitelikler;
  for (const c of t.sutunlar) {
    const s = ids.find((x) => x.id === c.id);
    assert.equal(c.tur, s.tur, c.id);
    assert.equal(c.birim || undefined, s.birim, c.id);
    assert.equal(c.degerler.length, t.satirlar.length, c.id);
  }
  const s = O.sahneCikar(m, 1);
  assert.equal(t.satirlar.length, s.cubuklar.no.length + s.paneller.no.length + s.dugumler.no.length + s.mesnetler.dugum.length);
  const sut = (id) => t.sutunlar.find((c) => c.id === id).degerler;
  const satir = (tur, no) => t.satirlar.findIndex((k) => k.tur === tur && k.no === no);
  const r = satir("cubuk", 1);                 // A1 kolonu ±0.00 → +3.50, KOLON = HEB 240 S355
  assert.equal(sut("alt_tur")[r], "kolon");
  assert.equal(sut("kesit")[r], "KOLON");
  assert.equal(sut("profil")[r], "HEB 240");
  assert.equal(sut("malzeme")[r], "S355");
  assert.equal(sut("sistem")[r], "celik");
  assert.equal(sut("uzunluk")[r], 3.5);
  assert.equal(sut("egim")[r], 90);
  assert.deepEqual(sut("kat")[r], [1]);
  assert.equal(sut("kullanim_yeri")[r], "kose");
  assert.equal(sut("seviye")[r], "+3.50");
  assert.deepEqual([sut("x")[r], sut("y")[r], sut("z")[r]], [0, 0, 1.75]);
  const p = satir("panel", 1);
  assert.equal(sut("alan")[p], 36);
  assert.equal(sut("kalinlik")[p], 0.12);
  assert.equal(sut("alt_tur")[p], "doseme");
  const c = t.satirlar.findIndex((k, i) => k.tur === "cubuk" && sut("serbest_i")[i] != null);
  assert.ok(c >= 0, "mafsallı çapraz");
  assert.match(sut("serbest_i")[c], /^(N,|Vy,|Vz,|T,)*My,Mz$/);
  // kodlu biçim
  const k = O.oznitelikKodla(t);
  assert.equal(k.satir_no.length, t.satirlar.length);
  const kat = k.sutunlar.find((x) => x.id === "kat");
  assert.equal(kat.liste_bas.length, t.satirlar.length + 1);
  assert.deepEqual(Array.from(kat.liste_deger.slice(kat.liste_bas[r], kat.liste_bas[r + 1])), [1]);
  const kes = k.sutunlar.find((x) => x.id === "kesit");
  assert.equal(kes.sozluk[kes.kod[r]], "KOLON");
  assert.equal(kes.kod[satir("dugum", s.dugumler.no[0])], O.SAHNE_YOK);
  const sb = k.sutunlar.find((x) => x.id === "serbest_dugum");
  assert.ok(sb.sayi instanceof Float64Array);
  assert.ok(Number.isNaN(sb.sayi[satir("mesnet", s.dugumler.no[s.mesnetler.dugum[0]])]));
});

test("sahneFarki: eklenen / silinen / değişen kimlikler sıralı", () => {
  const m = izgaraModel(1, 1, 1, { doseme: false });
  const a = O.sahneCikar(m, 1);
  const m2 = JSON.parse(JSON.stringify(m));
  m2.cubuklar = m2.cubuklar.filter((c) => c.no !== 2);
  m2.cubuklar.find((c) => c.no === 5).kesit = "KOLON";
  m2.cubuklar.push({ no: 99, i: { aks: ["A", "1"], z: "+3.00" }, j: { aks: ["B", "2"], z: "+3.00" }, tur: "capraz" });
  const f = O.sahneFarki(a, O.sahneCikar(m2, 2));
  assert.deepEqual(f.eklenen, [{ tur: "cubuk", no: 99 }]);
  // A2 kolonu silinince taban düğümü (no 2) kullanılmaz olur: düğüm, temel mesnedi ve tekil temel de sahneden çıkar
  assert.deepEqual(f.silinen, [{ tur: "cubuk", no: 2 }, { tur: "dugum", no: 2 }, { tur: "mesnet", no: 2 }, { tur: "temel", no: 2 }]);
  assert.deepEqual(f.degisen, [{ tur: "cubuk", no: 5 }]);
  const f0 = O.sahneFarki(a, O.sahneCikar(m, 3));
  assert.deepEqual([f0.eklenen, f0.silinen, f0.degisen], [[], [], []]);
});

test("sonucEsle: aks–kat ve genel model tasarım satırları elemanlara eşlenir", () => {
  for (const ad of ["betonarme-tek-aciklik", "betonarme-2kat-3x2", "celik-1kat-depo", "celik-cbf-3kat"]) {
    const m = sablon(ad);
    const v = JSON.parse(fs.readFileSync(path.join(OP4, "testler", "derlem", "sonuclar", ad + ".json"), "utf8"));
    const r = O.sonucEsle(m, v);
    assert.deepEqual(r.uyarilar, [], ad);
    const s = O.sahneCikar(m, 1);
    assert.equal(r.elemanlar.length, s.cubuklar.no.length, ad);     // her çubuk bir tasarım satırına
    const anahtar = r.elemanlar.map((e) => O.kimlikAnahtari(e.kimlik));
    assert.deepEqual(anahtar, [...anahtar].sort((a, b) => a - b), ad + " sıralı");
    for (const e of r.elemanlar) {
      const satir = v.tasarim.elemanlar[e.tasarim_satiri];
      assert.equal(e.dc, satir.dc);
      assert.equal(e.belirleyen, satir.belirleyen.kontrol);
      assert.equal(e.kombinasyon, satir.belirleyen.kombinasyon);
    }
  }
  const m = sablon("celik-cbf-3kat");
  const r = O.sonucEsle(m, { tasarim: { elemanlar: [{ no: 999, tur: "kolon", cubuk: 999, dc: 0.5 }, { no: 1, tur: "kolon", cubuk: 1, dc: null }] } });
  assert.equal(r.uyarilar.length, 1);
  assert.deepEqual(r.elemanlar.map((e) => [e.kimlik.no, e.dc]), [[1, -1]]);
  assert.equal(O.sonucEsle(m, {}).uyarilar.length, 1);
});

test("girdi değişmez: işlevler modeli yerinde değiştirmez", () => {
  for (const ad of ["betonarme-3kat-3x3", "celik-sanayi-4hol"]) {
    const m = sablon(ad), once = JSON.stringify(m);
    const C = O.cozumle(m);
    O.sahneCikar(m, 1, { cozum: C });
    O.oznitelikCikar(m, { cozum: C });
    O.sonucEsle(m, { tasarim: { elemanlar: [] } }, { cozum: C });
    assert.equal(JSON.stringify(m), once, ad);
  }
});

test("katUyeligi + kullanimYeri: betonarme-3kat-3x3 — her katta 4 köşe, 4 kenar, 1 iç kolon (4 × 3 köşe kolon); dış / iç kiriş; temel düğümleri", () => {
  const m = sablon("betonarme-3kat-3x3");
  const C = O.cozumle(m);
  const k = O.katUyeligi(m, { cozum: C }), u = O.kullanimYeri(m, { cozum: C });
  const sayac = {};
  for (let i = 0; i < C.nc; i++) {
    const no = C.cel[i].no, y = u.cubuk[no];
    if (y.alt_tur !== "kolon" && y.alt_tur !== "kiris") continue;
    assert.equal(k.cubuk[no].length, 1, "çubuk " + no);
    const a = y.alt_tur + "|" + k.cubuk[no][0] + "|" + y.yer;
    sayac[a] = (sayac[a] || 0) + 1;
  }
  for (const kat of [1, 2, 3]) {
    assert.equal(sayac["kolon|" + kat + "|kose"], 4, "kat " + kat);
    assert.equal(sayac["kolon|" + kat + "|kenar"], 4, "kat " + kat);
    assert.equal(sayac["kolon|" + kat + "|ic"], 1, "kat " + kat);
    assert.equal(sayac["kiris|" + kat + "|dis"], 8, "kat " + kat);   // 3 × 3 aks (2 × 2 göz): her kenarda 2 parça
    assert.equal(sayac["kiris|" + kat + "|ic"], 4, "kat " + kat);
  }
  const kose = Object.keys(sayac).filter((a) => /^kolon\|\d\|kose$/.test(a)).reduce((t, a) => t + sayac[a], 0);
  assert.equal(kose, 4 * 3);
  // temel seviyesindeki 9 düğüm "temel", kolon üst uçları "kolon-ustu"
  const dy = Object.values(u.dugum).map((x) => x.yer);
  assert.equal(dy.filter((y) => y === "temel").length, 9);
  assert.equal(dy.filter((y) => y === "kolon-ustu").length, 27);
  for (const [no, kl] of Object.entries(k.dugum)) assert.equal(kl.length, 1, "düğüm " + no);
  assert.deepEqual(k.seviyeler.map((s) => s.kat), [0, 1, 2, 3]);
});
