// docs/tablo_editoru.js saf mantığı (MatrisTablo._ic) — node'un yerleşik test koşucusu: node --test testler/js/tablo_editoru.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const M = require(path.join(__dirname, "..", "..", "docs", "tablo_editoru.js"));
const I = M._ic;

function ornekBina() {
  return {
    tur: "bina", surum: 3,
    akslar: {
      x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 5 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }],
      z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "+3.00", konum: 3, kat: 1 }, { ad: "Mahya", konum: 4.5 }],
    },
    aks_sistemleri: [
      { ad: "KANAT", tur: "kartezyen", orijin: [5, 0, 0], aci: 30, x: [{ ad: "K1", konum: 0 }], y: [{ ad: "a", konum: 0 }], z: null },
      { ad: "KUBBE", tur: "silindirik", orijin: [0, 0, 3], aci: 0, r: [{ ad: "R1", konum: 2 }], teta: [{ ad: "T1", konum: 0 }], z: [{ ad: "taban", konum: 0 }] },
    ],
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3 }],
    kolonlar: [{ no: 1, aks: ["A", "1"], kat: 1, kesit: "S" }, { no: 2, aks: ["B", "2"], kat: 1, kesit: "S" }],
    kirisler: [{ no: 1, kat: 1, bas: ["A", "1"], son: ["B", "1"], kesit: "K" }],
    dosemeler: [{ no: 1, kat: 1, kose: [["A", "1"], ["B", "2"]], h: 0.12 }],
    ek_yukler: [{ tur: "dugum", aks: ["A", "2"], kat: 1, FZ: -10 }],
    temeller: { ozel: [{ aks: ["A", "1"], B: 2, L: 2 }] },
    dugumler: [{ no: 100001, tur: "bolme", cubuk_i: { aks: ["A", "1"], z: "Mahya" }, cubuk_j: { aks: ["B", "1"], z: "Mahya" }, oran: 0.5 }],
    cubuklar: [
      { no: 1, i: { aks: ["A", "1"], z: "+3.00" }, j: { aks: ["A", "2"], z: "Mahya" } },
      { no: 2, i: { sistem: "KANAT", aks: ["K1", "a"], z: "+3.00" }, j: { sistem: "KANAT", aks: ["K1", "a"], z: "Mahya" } },
      { no: 3, i: { sistem: "KUBBE", aks: ["R1", "T1"], z: "taban" }, j: { dugum: 100001 } },
    ],
  };
}

test("yolAl / yolAta: anahtar, sıra, eksi sıra, seçici, _olustur, çoklu yol", () => {
  const b = ornekBina();
  assert.equal(I.yolAl(b, ["katlar", { no: 1 }, "kot"]), 3);
  assert.equal(I.yolAl(b, ["katlar", -1, "ad"]), "1. kat");
  assert.equal(I.yolAl(b, ["katlar", 0, "yok"]), null);
  assert.throws(() => I.yolAl(b, ["katlar", { no: 9 }, "kot"]), /eşleşen eleman yok/);
  I.yolAta(b, ["kolonlar", { no: 2 }, "kesit"], "S2");
  assert.equal(b.kolonlar[1].kesit, "S2");
  I.yolAta(b, ["temeller", "ozel", { aks: ["B", "2"], _olustur: true }, "B"], 2.5);
  assert.deepEqual(b.temeller.ozel[1], { aks: ["B", "2"], B: 2.5 });
  I.yolAta(b, ["metraj", "donati_orani", "kolon"], 150);       // ara sözlükler oluşur
  assert.equal(b.metraj.donati_orani.kolon, 150);
  I.yolAta(b, [["akslar", "z", { ad: "+3.00" }, "konum"], ["katlar", { no: 1 }, "kot"]], 3.2);
  assert.equal(b.akslar.z[1].konum, 3.2);
  assert.equal(b.katlar[1].kot, 3.2);
  assert.equal(I.yolAl(b, [["katlar", { no: 1 }, "kot"], ["x"]]), 3.2);
  assert.throws(() => I.yolAta(b, ["katlar", { no: 1 }], 1), /son adımı seçici/);
  assert.throws(() => I.yolAta(b, ["katlar", 7, "kot"], 1), /sırası 7 yok/);
  assert.equal(I.cokluYol([["a"], ["b"]]), true);
  assert.equal(I.cokluYol(["a", { no: 1 }]), false);
});

test("degisiklikleriUygula: kopya üzerinde, düz yazımlar önce, aks adları sonra", () => {
  const b = ornekBina();
  const once = JSON.stringify(b);
  const y = I.degisiklikleriUygula(b, [
    { yol: ["akslar", "x", { ad: "A" }, "ad"], deger: "AX", bag: { islem: "aks_ad", yon: "x", sistem: null } },
    { yol: ["akslar", "x", { ad: "A" }, "konum"], deger: -1 },          // eski adla seçici: ad değişikliğinden önce uygulanır
  ]);
  assert.equal(JSON.stringify(b), once, "girdi değişmedi");
  assert.deepEqual(y.akslar.x[0], { ad: "AX", konum: -1 });
  assert.deepEqual(y.kolonlar[0].aks, ["AX", "1"]);
  assert.deepEqual(y.kirisler[0].bas, ["AX", "1"]);
  assert.deepEqual(y.dosemeler[0].kose[0], ["AX", "1"]);
  assert.deepEqual(y.ek_yukler[0].aks, ["AX", "2"]);
  assert.deepEqual(y.temeller.ozel[0].aks, ["AX", "1"]);
  assert.deepEqual(y.cubuklar[0].i.aks, ["AX", "1"]);
  assert.deepEqual(y.dugumler[0].cubuk_i.aks, ["AX", "1"]);
  assert.deepEqual(y.cubuklar[1].i.aks, ["K1", "a"], "başka sistemin aksı değişmez");
});

test("aks yeniden adlandırma: Y ve Z aksları, sistem aksları, sistem adı", () => {
  let y = I.degisiklikleriUygula(ornekBina(), [{ yol: ["akslar", "y", { ad: "1" }, "ad"], deger: "1A", bag: { islem: "aks_ad", yon: "y", sistem: null } }]);
  assert.deepEqual(y.kolonlar[0].aks, ["A", "1A"]);
  assert.deepEqual(y.kirisler[0].son, ["B", "1A"]);
  assert.deepEqual(y.dosemeler[0].kose, [["A", "1A"], ["B", "2"]]);
  // GLOBAL Z: z'si null olan sistemin REF'leri de GLOBAL Z adını kullanır
  y = I.degisiklikleriUygula(ornekBina(), [{ yol: ["akslar", "z", { ad: "Mahya" }, "ad"], deger: "Tepe", bag: { islem: "aks_ad", yon: "z", sistem: null } }]);
  assert.equal(y.cubuklar[0].j.z, "Tepe");
  assert.equal(y.cubuklar[1].j.z, "Tepe");
  assert.equal(y.dugumler[0].cubuk_i.z, "Tepe");
  // sistem kendi Z aksı + silindirik θ aksı
  y = I.degisiklikleriUygula(ornekBina(), [
    { yol: ["aks_sistemleri", { ad: "KUBBE" }, "z", { ad: "taban" }, "ad"], deger: "alt", bag: { islem: "aks_ad", yon: "z", sistem: "KUBBE" } },
    { yol: ["aks_sistemleri", { ad: "KUBBE" }, "teta", { ad: "T1" }, "ad"], deger: "T0", bag: { islem: "aks_ad", yon: "teta", sistem: "KUBBE" } },
    { yol: ["aks_sistemleri", { ad: "KUBBE" }, "ad"], deger: "KUBBE-2", bag: { islem: "sistem_ad" } },
  ]);
  assert.deepEqual(y.cubuklar[2].i, { sistem: "KUBBE-2", aks: ["R1", "T0"], z: "alt" });
  assert.equal(y.aks_sistemleri[1].ad, "KUBBE-2");
  assert.equal(y.cubuklar[0].i.z, "+3.00");
  // hatalar: aynı ad, boş ad, GLOBAL
  assert.throws(() => I.degisiklikleriUygula(ornekBina(), [{ yol: ["akslar", "x", { ad: "A" }, "ad"], deger: "B", bag: { islem: "aks_ad", yon: "x" } }]), /zaten var/);
  assert.throws(() => I.degisiklikleriUygula(ornekBina(), [{ yol: ["akslar", "x", { ad: "A" }, "ad"], deger: " ", bag: { islem: "aks_ad", yon: "x" } }]), /boş/);
  assert.throws(() => I.degisiklikleriUygula(ornekBina(), [{ yol: ["aks_sistemleri", { ad: "KANAT" }, "ad"], deger: "GLOBAL", bag: { islem: "sistem_ad" } }]), /GLOBAL/);
});

test("sayiOku: Türkçe ve İngilizce ondalık, binlik, eksi işareti, üs", () => {
  const ok = { "1,5": 1.5, "1.5": 1.5, "1.234,5": 1234.5, "1,234.5": 1234.5, "1 234,5": 1234.5, "−2,25": -2.25, "-0,0001": -0.0001,
    "1e-3": 0.001, "2,5E2": 250, ".5": 0.5, "1.234.567": 1234567, "%10": 10, "+3": 3 };
  for (const [m, v] of Object.entries(ok)) assert.equal(I.sayiOku(m), v, m);
  for (const m of ["", "abc", "1,2,3a", "1-2", "--1"]) assert.ok(Number.isNaN(I.sayiOku(m)), m);
  assert.equal(I.sayiOku(7), 7);
});

test("degerCevir: sayı, metin, bool, seçim (değer/etiket/sayı), boş", () => {
  assert.deepEqual(I.degerCevir("0,16", { tur: "sayi" }), { deger: 0.16 });
  assert.ok(I.degerCevir("", { tur: "sayi" }).hata);
  assert.deepEqual(I.degerCevir("", { tur: "sayi", bos_olur: true }), { deger: null });
  assert.deepEqual(I.degerCevir("%10", { tur: "sayi", birim: "oran" }), { deger: 0.1 });
  assert.deepEqual(I.degerCevir("10%", { tur: "sayi", birim: "%" }), { deger: 10 });
  assert.ok(I.degerCevir("2.5", { tur: "sayi", ondalik: 0 }).hata);
  assert.ok(I.degerCevir("x1", { tur: "sayi" }).hata);
  assert.deepEqual(I.degerCevir("  Çatı ", { tur: "metin" }), { deger: "Çatı" });
  assert.deepEqual(I.degerCevir("", { tur: "metin", bos_olur: true }), { deger: null });
  for (const m of ["evet", "EVET", "Doğru", "1", "✓", "x", "Açık", "true"]) assert.deepEqual(I.degerCevir(m, { tur: "bool" }), { deger: true }, m);
  for (const m of ["hayır", "HAYIR", "yanlış", "0", "–", "", "kapalı", "false"]) assert.deepEqual(I.degerCevir(m, { tur: "bool" }), { deger: false }, m);
  assert.ok(I.degerCevir("belki", { tur: "bool" }).hata);
  const sec = { tur: "secim", secenekler: ["betonarme", "celik"] };
  assert.deepEqual(I.degerCevir("Çelik", sec), { deger: "celik" });       // Türkçe harf katlama
  assert.ok(I.degerCevir("ahşap", sec).hata);
  const duvar = { tur: "secim", secenekler: [{ deger: null, etiket: "(duvar yok)" }, "tugla19"], bos_olur: true };
  assert.deepEqual(I.degerCevir("(duvar yok)", duvar), { deger: null });
  assert.deepEqual(I.degerCevir("", duvar), { deger: null });
  assert.deepEqual(I.degerCevir("TUGLA19", duvar), { deger: "tugla19" });
  assert.deepEqual(I.degerCevir("2", { tur: "secim", secenekler: [1, 2, 3] }), { deger: 2 });
  assert.deepEqual(I.degerCevir(true, { tur: "bool" }), { deger: true });
});

test("bicimle: ondalık önerisi, tam sayı, küçük sayı, bool, seçim etiketi, ondalık virgül", () => {
  assert.equal(I.bicimle(3.14159, { ondalik: 2 }), "3.14");
  assert.equal(I.bicimle(-0.0001, { ondalik: 2 }), "0.00");
  assert.equal(I.bicimle(12, {}), "12");
  assert.equal(I.bicimle(2.5, {}, true), "2,5");
  assert.equal(I.bicimle(1.23456789, {}), "1.2346");
  assert.equal(I.bicimle(1.5e-6, {}), "1.500e-06");
  assert.equal(I.bicimle(null, {}), "");
  assert.equal(I.bicimle(true, {}), "✓");
  assert.equal(I.bicimle(false, {}), "–");
  assert.equal(I.bicimle(null, { secenekler: [{ deger: null, etiket: "(yok)" }] }), "");
  assert.equal(I.bicimle("tugla19", { secenekler: [{ deger: "tugla19", etiket: "Tuğla 19" }] }), "Tuğla 19");
  assert.equal(I.bicimle(1000, { ondalik: 0 }), "1000");
});

test("hucreTuru ve duzenlenebilir: satıra özgü hücre türü, yol zorunlu", () => {
  const s = { ad: "deger", baslik: "Değer", tur: "sayi", duzenlenebilir: true, ondalik: 3 };
  const r1 = { degerler: { deger: "celik" }, yol: { deger: ["sistem"] }, hucre: { deger: { tur: "secim", secenekler: ["betonarme", "celik"] } } };
  const r2 = { degerler: { deger: 1.2 } };
  assert.equal(I.hucreTuru(r1, s).tur, "secim");
  assert.equal(I.hucreTuru(r1, s).ondalik, 3);
  assert.equal(I.hucreTuru(r2, s).tur, "sayi");
  assert.equal(I.duzenlenebilir(r1, s), true);
  assert.equal(I.duzenlenebilir(r2, s), false);
  assert.equal(I.duzenlenebilir(r1, Object.assign({}, s, { duzenlenebilir: false })), false);
});

const T = {
  ad: "t", baslik: "Deneme", grup: "Model",
  sutunlar: [{ ad: "ad", baslik: "Ad", tur: "metin" }, { ad: "x", baslik: "X", birim: "m", tur: "sayi", ondalik: 2, duzenlenebilir: true },
    { ad: "dc", baslik: "D/C", tur: "sayi", vurgu: "dc" }, { ad: "b", baslik: "Var", tur: "bool" }],
  satirlar: [
    { degerler: { ad: "çam", x: 3, dc: 0.5, b: true }, yol: { x: ["l", 0, "x"] } },
    { degerler: { ad: "Ağaç", x: null, dc: 1.2, b: false }, yol: { x: ["l", 1, "x"] } },
    { degerler: { ad: "ıhlamur", x: -1.5, dc: 1.0, b: true } },
    { degerler: { ad: "Σ", x: 1.5, dc: null, b: null }, ozet: true },
    { degerler: { ad: "Zeytin; \"yaşlı\"", x: 10, dc: 0.99, b: false }, yol: { x: ["l", 2, "x"] } },
  ],
  toplam: { x: 11.5 },
};

test("sirala: boşlar ve özet satırları sonda, kararlı, Türkçe sıra", () => {
  const idx = [0, 1, 2, 3, 4];
  assert.deepEqual(I.sirala(T.satirlar, idx, "x", "artan"), [2, 0, 4, 1, 3]);
  assert.deepEqual(I.sirala(T.satirlar, idx, "x", "azalan"), [4, 0, 2, 1, 3]);
  assert.deepEqual(I.sirala(T.satirlar, idx, "ad", "artan"), [1, 0, 2, 4, 3]);          // Ağaç < çam < ıhlamur < Zeytin
  assert.deepEqual(I.sirala(T.satirlar, idx, null, null), idx);
  assert.deepEqual(I.sirala(T.satirlar, idx, "b", "artan"), [1, 4, 0, 2, 3]);
});

test("süzgeç: içerir, karşılaştırma, aralık, değil, ya da, boş/dolu, bool", () => {
  const f = (s) => I.suz(T, s);
  assert.deepEqual(f({ ad: "a" }), [0, 1, 2, 4]);
  assert.deepEqual(f({ ad: "AGAC" }), [1]);                 // Türkçe harf ve büyük harf duyarsız
  assert.deepEqual(f({ x: ">0" }), [0, 3, 4]);
  assert.deepEqual(f({ x: "<=-1,5" }), [2]);
  assert.deepEqual(f({ x: "-2..3" }), [0, 2, 3]);
  assert.deepEqual(f({ x: "boş" }), [1]);
  assert.deepEqual(f({ x: "dolu", dc: ">1" }), []);
  assert.deepEqual(f({ dc: ">1" }), [1]);
  assert.deepEqual(f({ ad: "!a" }), [3]);
  assert.deepEqual(f({ ad: "çam|zeytin" }), [0, 4]);
  assert.deepEqual(f({ b: "evet" }), [0, 2]);
  assert.deepEqual(f({ x: "=10" }), [4]);
  assert.deepEqual(f({ ad: "=çam" }), [0]);
  assert.deepEqual(f({ x: "<>3" }), [1, 2, 3, 4]);
  assert.deepEqual(f({ x: "  " }), [0, 1, 2, 3, 4]);
});

test("toplamHesapla ve D/C aşımı", () => {
  assert.deepEqual(I.toplamHesapla(T, [0, 1, 2, 3, 4]), { x: 11.5 });     // özet satırı dahil edilmez
  assert.deepEqual(I.toplamHesapla(T, [1]), {});
  assert.equal(I.dcAsimi(1.2, { vurgu: "dc" }), true);
  assert.equal(I.dcAsimi(1.0, { vurgu: "dc" }), false);
  assert.equal(I.dcAsimi(5, {}), false);
});

test("CSV: BOM, ; ayırıcı, tırnaklama, ondalık virgül, toplam satırı; bölümlü tek CSV", () => {
  const csv = I.csvUret(T, { ayirici: ";", ondalikVirgul: true });
  assert.ok(csv.startsWith("﻿"));
  const sat = csv.slice(1).split("\r\n");
  assert.equal(sat[0], "Ad;X [m];D/C;Var");
  assert.equal(sat[1], "çam;3;0,5;evet");
  assert.equal(sat[2], "Ağaç;;1,2;hayır");
  assert.equal(sat[5], '"Zeytin; ""yaşlı""";10;0,99;hayır');
  assert.equal(sat[6], "Toplam;11,5;;");
  const nokta = I.csvUret(T, { ayirici: ",", ondalikVirgul: false, idx: [2] });
  assert.equal(nokta.slice(1).split("\r\n")[1], "ıhlamur,-1.5,1,evet");
  assert.equal(nokta.slice(1).split("\r\n")[2], "Toplam,-1.5,,");          // görünen satırların toplamı
  const virgulVirgul = I.csvUret(T, { ayirici: ",", ondalikVirgul: true, idx: [4] });
  assert.equal(virgulVirgul.slice(1).split("\r\n")[1], '"Zeytin; ""yaşlı""",10,"0,99",hayır');
  const tum = I.tumunuCsv([T, Object.assign({}, T, { ad: "u", baslik: "İkinci" })], { ayirici: ";" });
  assert.equal((tum.match(/Tablo: /g) || []).length, 2);
  assert.ok(tum.includes("Tablo: İkinci;Model;u\r\nAd;X [m];D/C;Var"));
  assert.equal(I.disaDeger(1e-7, {}, false), "1E-7");
  assert.equal(I.disaDeger(0.1 + 0.2, {}, false), "0.3");
});

test("TSV: ayrıştırma (tırnaklı sekme/satır sonu, CRLF, boş hücre) ve üretme", () => {
  assert.deepEqual(I.tsvAyristir("1\t2\r\n3\t4\r\n"), [["1", "2"], ["3", "4"]]);
  assert.deepEqual(I.tsvAyristir("a\t\tc"), [["a", "", "c"]]);
  assert.deepEqual(I.tsvAyristir('"x\ty"\t"çok\nsatır"\t"""t"""\n5'), [["x\ty", "çok\nsatır", '"t"'], ["5"]]);
  assert.deepEqual(I.tsvAyristir("tek"), [["tek"]]);
  assert.deepEqual(I.tsvAyristir(""), []);
  assert.deepEqual(I.tsvAyristir("﻿1,5\n"), [["1,5"]]);
  assert.equal(I.tsvUret([["a", "b\tc"], ["1", ""]]), 'a\t"b\tc"\r\n1\t');
  const geri = I.tsvAyristir(I.tsvUret([["x\ny", 'q"'], ["", "z"]]));
  assert.deepEqual(geri, [["x\ny", 'q"'], ["", "z"]]);
});

test("yapistirmaPlani: etkin hücreden itibaren, salt okunur atlanır, hata raporu, 1×1 ile aralığı doldurma", () => {
  const gor = [0, 1, 2, 3, 4], sut = T.sutunlar;
  let p = I.yapistirmaPlani(T, gor, sut, 0, 1, [["1,5"], ["2"], ["3"], ["x"], ["5"]]);
  assert.deepEqual(p.degisiklikler.map((d) => [d.satir, d.deger]), [[0, 1.5], [1, 2], [4, 5]]);
  assert.deepEqual(p.degisiklikler[0].yol, ["l", 0, "x"]);
  assert.equal(p.degisiklikler[0].ilk, 3);
  assert.equal(p.atlanan, 2);            // satır 3 (yol yok) ve 4. (özet, yol yok)
  assert.equal(p.hatalar.length, 0);
  p = I.yapistirmaPlani(T, gor, sut, 0, 1, [["abc", "1"]]);
  assert.equal(p.hatalar.length, 1);
  assert.match(p.hatalar[0], /Satır 1, X: sayı okunamadı/);
  assert.equal(p.atlanan, 1);            // D/C salt okunur
  p = I.yapistirmaPlani(T, gor, sut, 0, 1, [["7"]], { r0: 0, r1: 4, c0: 1, c1: 1 });
  assert.deepEqual(p.degisiklikler.map((d) => d.satir), [0, 1, 4]);
  p = I.yapistirmaPlani(T, gor, sut, 4, 3, [["1", "2"], ["3"]]);
  assert.equal(p.atlanan, 3);            // tablo dışı + salt okunur
});

test("Duzenleme: yol anahtarı, ilk değere dönünce silinir, geri al yığını, değişiklik listesi", () => {
  const d = new I.Duzenleme();
  d.ekle([{ yol: ["a"], deger: 1, ilk: 0, tablo: "t1" }]);
  d.ekle([{ yol: ["b", { no: 1 }, "x"], deger: "k", ilk: "j", tablo: "t2" }, { yol: ["a"], deger: 2, ilk: 99, tablo: "t1" }]);
  assert.equal(d.sayi(), 2);
  assert.equal(d.deger(["a"]).deger, 2);
  assert.equal(d.deger(["a"]).ilk, 0, "ilk değer ilk düzenlemeden kalır");
  assert.deepEqual(Array.from(d.tablolar()).sort(), ["t1", "t2"]);
  d.ekle([{ yol: ["a"], deger: 0, ilk: 2 }]);          // ilk değere dönüş: bekleyenden çıkar
  assert.equal(d.deger(["a"]), undefined);
  assert.equal(d.geriAl(), true);
  assert.equal(d.deger(["a"]).deger, 2);
  assert.equal(d.geriAl(), true);
  assert.equal(d.deger(["a"]).deger, 1);
  assert.equal(d.deger(["b", { no: 1 }, "x"]), undefined);
  d.ekle([{ yol: ["c"], deger: "y", ilk: "x", bag: { islem: "aks_ad", yon: "x" } }]);
  assert.deepEqual(d.degisiklikler(), [{ yol: ["a"], deger: 1 }, { yol: ["c"], deger: "y", bag: { islem: "aks_ad", yon: "x" } }]);
  assert.equal(d.geriAl(), true);
  assert.equal(d.geriAl(), true);
  assert.equal(d.geriAl(), false);
  assert.equal(d.sayi(), 0);
});

test("yardımcılar: grup sırası, yol metni, katlama, eşitlik, sütun genişliği", () => {
  const g = I.gruplu([{ ad: "m", grup: "Metraj" }, { ad: "a", grup: "Model" }, { ad: "x", grup: "Özel" }, { ad: "b", grup: "Model" }]);
  assert.deepEqual(g.map((x) => [x[0], x[1].map((t) => t.ad)]), [["Model", ["a", "b"]], ["Metraj", ["m"]], ["Özel", ["x"]]]);
  assert.equal(I.yolMetni(["katlar", { no: 2 }, "kot"]), "katlar › [no = 2] › kot");
  assert.equal(I.yolMetni([["a", 0], ["b"]]), "a › [0]  +  b");
  assert.equal(I.katla("KAPALI Işık Ğ"), "kapali isik g");
  assert.ok(I.esit({ a: [1, { b: 2 }] }, { a: [1, { b: 2 }] }));
  assert.ok(!I.esit(1, true));
  assert.ok(I.esit(null, undefined));
  const w = I.sutunGenisligi(T, T.sutunlar[0]);
  assert.ok(w >= 64 && w <= 340, String(w));
  assert.equal(typeof M.ac, "function");
});
