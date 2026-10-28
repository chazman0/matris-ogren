/* docs/ifc_disari.js (MatrisIFC) testleri için örnek bina modelleri — test değil, yalnız veri.
   testler/js/ifc_disari.test.js (node --test) ve testler/test_ifc_disari.py (Node ile üretip ifcopenshell ile açar) kullanır.
   Her işlev yeni (bağımsız) bir model döndürür. */
"use strict";
const path = require("node:path");

// Aks–kat modeli (surum 1): 2×2 aks, 2 kat, betonarme, tekil temel (elastik mesnet)
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

// surum 3 (§12): serbest düğümler, çubuklar (makas, aşık, çapraz, profil türleri, uç serbestliği), paneller, mesnetler; mütemadi temel
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

// §13 kirişli radye
function radyeBina() {
  const b = temelBina();
  b.baslik = "Kirişli radye örneği";
  b.temeller = { tip: "radye", zemin: { q_em: 150, k0: 15000 }, radye: { h: 0.8, tasma: 1.0, kiris: { b: 0.5, h: 1.2 } } };
  return b;
}

// §13 mütemadi temel yalnız X doğrultusunda, seçili akslarda; dikdörtgen kesit (b_govde = B, h_tabla = 0)
function surekliBina() {
  const b = temelBina();
  b.baslik = "Mütemadi temel (yalnız 1 aksı)";
  b.temeller = { tip: "surekli", zemin: { q_em: 200, k0: 20000 }, surekli: { yon: "x", akslar: ["1"], B: 0.8, h_tabla: 0, b_govde: 0.8, h_govde: 0.9, tasma: 0.4 } };
  return b;
}

// §19 aks sistemi tabanlı model: Z aksları (kat + saçak + mahya), aks REF'leri {"aks", "z"}, bölme ve kesişim düğümleri,
// döndürülmüş kartezyen ek sistem (KANAT-B) ve kendi Z aksları olan silindirik sistem (KUBBE). Tek katlı çelik hal + ek yapılar.
function aksSistemiBina() {
  const z = function (aks, zad) { return { aks: aks, z: zad }; };
  const b = {
    tur: "bina", surum: 3, baslik: "Aks sistemi örneği (çelik hal, kanat ve köşk)", sistem: "celik",
    akslar: {
      x: [{ ad: "A", konum: 0 }, { ad: "M", konum: 5, tur: "ikincil" }, { ad: "B", konum: 10 }],
      y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 6 }, { ad: "3", konum: 12 }],
      z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "Saçak", konum: 6.0, kat: 1 }, { ad: "Mahya", konum: 7.5 }],
    },
    // kat 1'in kotu Z aksından gelir (6,0 m); buradaki 5,0 m eski değer (tek kaynak akslar.z)
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "Saçak seviyesi", kot: 5.0 }],
    aks_sistemleri: [
      { ad: "KANAT-B", tur: "kartezyen", orijin: [25, 0, 0], aci: 30,
        x: [{ ad: "P", konum: 0 }, { ad: "R", konum: 6 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 5 }], z: null },
      { ad: "KUBBE", tur: "silindirik", orijin: [5, 18, 0], aci: 0,
        r: [{ ad: "R1", konum: 3 }], teta: [{ ad: "T1", konum: 0 }, { ad: "T2", konum: 120 }, { ad: "T3", konum: 240 }],
        z: [{ ad: "Taban", konum: 0 }, { ad: "Tepe", konum: 2.5 }] },
    ],
    malzemeler: { S275: { kutuphane: "S275" }, C30: { kutuphane: "C30/37" } },
    kesitler: {
      HEA300: { tip: "profil", profil: "HEA 300", malzeme: "S275" }, IPE330: { tip: "profil", profil: "IPE 330", malzeme: "S275" },
      IPE200: { tip: "profil", profil: "IPE 200", malzeme: "S275" }, BORU: { tip: "boru", D: 0.0889, t: 0.004, malzeme: "S275" },
      KUTU: { tip: "kutu", h: 0.15, b: 0.15, t: 0.006, malzeme: "S275" },
    },
    dugumler: [
      // aşık noktaları: mertek ortaları (bölme düğümü; akslar taşınınca birlikte taşınır)
      { no: 100001, tur: "bolme", cubuk_i: z(["A", "1"], "Saçak"), cubuk_j: z(["M", "1"], "Mahya"), oran: 0.5 },
      { no: 100002, tur: "bolme", cubuk_i: z(["A", "2"], "Saçak"), cubuk_j: z(["M", "2"], "Mahya"), oran: 0.5 },
      { no: 100003, tur: "bolme", cubuk_i: z(["A", "3"], "Saçak"), cubuk_j: z(["M", "3"], "Mahya"), oran: 0.5 },
      // A aksı cephesinde X çaprazının kesişim noktası (0, 3, 3)
      { no: 100010, tur: "kesisim", a: [z(["A", "1"], "±0.00"), z(["A", "2"], "Saçak")], b: [z(["A", "2"], "±0.00"), z(["A", "1"], "Saçak")] },
    ],
    cubuklar: [],
    paneller: [
      { no: 1, kose: [z(["A", "1"], "Saçak"), z(["M", "1"], "Mahya"), z(["M", "3"], "Mahya"), z(["A", "3"], "Saçak")], tur: "cati", kalinlik: 0 },
      { no: 2, kose: [z(["M", "1"], "Mahya"), z(["B", "1"], "Saçak"), z(["B", "3"], "Saçak"), z(["M", "3"], "Mahya")], tur: "cati", kalinlik: 0 },
    ],
    temeller: { tip: "tekil", varsayilan: { B: 1.2, L: 1.2, h: 0.5 }, zemin: { q_em: 200, k0: 20000 }, mesnet: "mafsal" },
  };
  let n = 0;
  const cb = function (i, j, tur, kesit, ek) { b.cubuklar.push(Object.assign({ no: ++n, i: i, j: j, tur: tur, kesit: kesit }, ek || {})); };
  ["1", "2", "3"].forEach(function (y) {     // portal çerçeveler: kolonlar ve eğik kirişler (mertek)
    cb(z(["A", y], "±0.00"), z(["A", y], "Saçak"), "kolon", "HEA300");
    cb(z(["B", y], "±0.00"), z(["B", y], "Saçak"), "kolon", "HEA300", { aci: 90 });
    cb(z(["A", y], "Saçak"), z(["M", y], "Mahya"), "kiris", "IPE330");
    cb(z(["M", y], "Mahya"), z(["B", y], "Saçak"), "kiris", "IPE330");
  });
  cb({ dugum: 100001 }, { dugum: 100002 }, "asik", "IPE200");
  cb({ dugum: 100002 }, { dugum: 100003 }, "asik", "IPE200");
  // X çaprazı kesişimde bölünmüş: dört çubuk
  cb(z(["A", "1"], "±0.00"), { dugum: 100010 }, "capraz", "BORU", { yalniz_cekme: true });
  cb({ dugum: 100010 }, z(["A", "2"], "Saçak"), "capraz", "BORU", { yalniz_cekme: true });
  cb(z(["A", "2"], "±0.00"), { dugum: 100010 }, "capraz", "BORU", { yalniz_cekme: true });
  cb({ dugum: 100010 }, z(["A", "1"], "Saçak"), "capraz", "BORU", { yalniz_cekme: true });
  // KANAT-B: 4 kolon (±0.00 → Saçak, GLOBAL Z aksları), Saçak seviyesinde 4 kiriş
  const k = function (aks, zad) { return { sistem: "KANAT-B", aks: aks, z: zad }; };
  [["P", "1"], ["R", "1"], ["R", "2"], ["P", "2"]].forEach(function (a) { cb(k(a, "±0.00"), k(a, "Saçak"), "kolon", "KUTU"); });
  cb(k(["P", "1"], "Saçak"), k(["R", "1"], "Saçak"), "kiris", "IPE200");
  cb(k(["P", "2"], "Saçak"), k(["R", "2"], "Saçak"), "kiris", "IPE200");
  cb(k(["P", "1"], "Saçak"), k(["P", "2"], "Saçak"), "kiris", "IPE200");
  cb(k(["R", "1"], "Saçak"), k(["R", "2"], "Saçak"), "kiris", "IPE200");
  // KUBBE: 3 kolon (Taban → Tepe, sistemin kendi Z aksları) ve Tepe'de halka kirişler
  const s = function (t, zad) { return { sistem: "KUBBE", aks: ["R1", t], z: zad }; };
  ["T1", "T2", "T3"].forEach(function (t) { cb(s(t, "Taban"), s(t, "Tepe"), "kolon", "BORU"); });
  [["T1", "T2"], ["T2", "T3"], ["T3", "T1"]].forEach(function (p) { cb(s(p[0], "Tepe"), s(p[1], "Tepe"), "kiris", "IPE200"); });
  return b;
}

// surum 3, motorun (yapi_serbest) kesit dilinde: IPE/HEA adları, basit kesit adları ("BORU 114.3x4", "KUTU 150x8", "L 100x10",
// "2L 70x7 s=10", "UPN 200"), {tip: "kutu", boyutlar (mm)} ve iki uçta vute (temel MERTEK). 10 m açıklıklı iki çerçeveli beşik çatı:
// mertek kenarı iki çubuklu zincir (vute + mertek; B tarafında vute ters yönde), dağıtımı "yok" olan cephe paneli, ek yükler.
// Motorla çözülebilir (testler/test_ifc_disari.py yapi.bina_coz ile çözüp yükleri karşılaştırır).
function genelKesitBina() {
  const z = function (aks, zad) { return { aks: aks, z: zad }; };
  const b = {
    tur: "bina", surum: 3, baslik: "Genel model kesit dili (beşik çatılı çelik çerçeve)", sistem: "celik", birim: { kuvvet: "kN", uzunluk: "m" },
    akslar: {
      x: [{ ad: "A", konum: 0 }, { ad: "M", konum: 5 }, { ad: "B", konum: 10 }],
      y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 6 }],
      z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "Saçak", konum: 5.0, kat: 1 }, { ad: "Mahya", konum: 6.0 }],
    },
    katlar: [{ no: 0, ad: "±0.00", kot: 0 }, { no: 1, ad: "Saçak", kot: 5.0 }],
    malzemeler: { S275: { kutuphane: "S275" } },
    kesitler: {
      KOLON: { tip: "profil", profil: "HEA 240", malzeme: "S275" },
      MERTEK: { tip: "profil", profil: "IPE 300", malzeme: "S275" },
      VUTE: { tip: "vute", temel: "MERTEK", ek_yukseklik: 0.3, boy: 1.5 },
      ASIK: { tip: "profil", profil: "UPN 200", malzeme: "S275" },
      CAPRAZ: { tip: "profil", profil: "BORU 114.3x4", malzeme: "S275" },
      CEPHE_CAPRAZ: { tip: "profil", profil: "KUTU 150x8", malzeme: "S275" },
      GERGI: { tip: "profil", profil: "L 100x10", malzeme: "S275" },
      GERGI2: { tip: "profil", profil: "2L 70x7 s=10", malzeme: "S275" },
      SACAK: { tip: "kutu", boyutlar: { H: 200, B: 100, t: 6 }, malzeme: "S275" },
    },
    // vute uçları: mertek boyunca saçaktan 1,5 m (L_mertek = √26 m)
    dugumler: [],
    cubuklar: [],
    paneller: [],
    mesnetler: [],
    ek_yukler: [],
    temeller: { tip: "tekil", varsayilan: { B: 1.5, L: 1.5, h: 0.6 }, zemin: { q_em: 200, k0: 20000 }, mesnet: "mafsal", ozel: [] },
    yuk_durumlari: { G: { acik: true }, Q: { acik: true }, S: { acik: true, bolge: 2, rakim: 500 }, W: { acik: false }, E: { acik: false } },
    deprem: { etkin: false },
    kombinasyon_kumesi: "cythye_ydkt",
    analiz: { diyagram_nokta: 9 },
  };
  const oran = 1.5 / Math.sqrt(26);
  let n = 0;
  const cb = function (i, j, tur, kesit, ek) { b.cubuklar.push(Object.assign({ no: ++n, i: i, j: j, tur: tur, kesit: kesit }, ek || {})); return n; };
  ["1", "2"].forEach(function (y, k) {
    const va = 100001 + 2 * k, vb = 100002 + 2 * k;
    b.dugumler.push({ no: va, tur: "bolme", cubuk_i: z(["A", y], "Saçak"), cubuk_j: z(["M", y], "Mahya"), oran: oran, ad: "Vute ucu A" + y },
      { no: vb, tur: "bolme", cubuk_i: z(["B", y], "Saçak"), cubuk_j: z(["M", y], "Mahya"), oran: oran, ad: "Vute ucu B" + y });
    cb(z(["A", y], "±0.00"), z(["A", y], "Saçak"), "kolon", "KOLON", { kat: 1 });
    cb(z(["B", y], "±0.00"), z(["B", y], "Saçak"), "kolon", "KOLON", { kat: 1 });
    cb(z(["A", y], "Saçak"), { dugum: va }, "kiris", "VUTE");
    cb({ dugum: va }, z(["M", y], "Mahya"), "kiris", "MERTEK");
    cb(z(["M", y], "Mahya"), { dugum: vb }, "kiris", "MERTEK");
    cb(z(["B", y], "Saçak"), { dugum: vb }, "kiris", "VUTE");       // derin uç (i) saçakta; panel kenarı M → B yönünde: ters
  });
  cb(z(["A", "1"], "Saçak"), z(["A", "2"], "Saçak"), "asik", "ASIK");
  cb(z(["M", "1"], "Mahya"), z(["M", "2"], "Mahya"), "asik", "ASIK");
  cb(z(["B", "1"], "Saçak"), z(["B", "2"], "Saçak"), "asik", "SACAK");
  cb(z(["A", "1"], "±0.00"), z(["A", "2"], "Saçak"), "capraz", "CAPRAZ", { yalniz_cekme: true });
  cb(z(["A", "2"], "±0.00"), z(["A", "1"], "Saçak"), "capraz", "CAPRAZ", { yalniz_cekme: true });
  cb(z(["B", "1"], "±0.00"), z(["B", "2"], "Saçak"), "capraz", "CEPHE_CAPRAZ");
  cb(z(["A", "1"], "Saçak"), z(["B", "1"], "Saçak"), "bag", "GERGI");
  const gergi2 = cb(z(["A", "2"], "Saçak"), z(["B", "2"], "Saçak"), "bag", "GERGI2");
  b.paneller.push(
    { no: 1, kose: [z(["A", "1"], "Saçak"), z(["M", "1"], "Mahya"), z(["M", "2"], "Mahya"), z(["A", "2"], "Saçak")], tur: "cati", kalinlik: 0, g: 0.3, q: 0.5, kar: true, dagitim: "tek-13" },
    { no: 2, kose: [z(["M", "1"], "Mahya"), z(["B", "1"], "Saçak"), z(["B", "2"], "Saçak"), z(["M", "2"], "Mahya")], tur: "cati", kalinlik: 0, g: 0.3, q: 0.5, kar: true, dagitim: "tek-13" },
    { no: 3, kose: [z(["A", "1"], "±0.00"), z(["B", "1"], "±0.00"), z(["B", "1"], "Saçak"), z(["A", "1"], "Saçak")], tur: "cephe", kalinlik: 0, g: 0.2, q: 0, kar: false, dagitim: "yok" });
  b.ek_yukler.push(
    { tur: "cubuk", cubuk: 4, durum: "Q", q1: -1.0, q2: -3.0, x1: 0.5, x2: 3.0 },
    { tur: "cubuk", cubuk: gergi2, durum: "G", x: 0.5, P: -6.0, oransal: true },
    { tur: "dugum", dugum: z(["M", "1"], "Mahya"), durum: "Q", FZ: -4.0 });
  return b;
}

// model_ops.genellestir ile aks–kat modelinden üretilmiş surum 3 modeli (kolon/kiriş → çubuk, döşeme → panel; kaynak.aks_kat)
function genelBina() {
  const MO = require(path.join(__dirname, "..", "..", "docs", "model_ops.js"));
  const b = temelBina();
  b.temeller = { tip: "tekil", varsayilan: { B: 1.6, L: 1.6, h: 0.6 }, zemin: { q_em: 200, k0: 20000 }, mesnet: "ankastre" };
  const m = MO.genellestir(b).model;
  m.baslik = "Genelleştirilmiş model (model_ops)";
  return m;
}

module.exports = { temel: temelBina, serbest: serbestBina, radye: radyeBina, surekli: surekliBina, aks: aksSistemiBina, genel: genelBina,
  genel_kesit: genelKesitBina };
