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

// ------------------------------------------------------------------ CSV dosyası içe aktarma (sözleşme C23)
// Gerçek tablolara benzer küçük tablolar: anahtarlı (katlar: "no"), anahtarı düzenlenebilir sütunla kurulan (akslar: sistem + yön
// + ad), seçim / evet-hayır hücreli ve toplam satırlı tablo.
function csvTablolari() {
  const kat = (no, ad, kot, h) => ({ degerler: { no: no, ad: ad, kot: kot, h: h }, yol: { ad: ["katlar", { no: no }, "ad"], kot: ["katlar", { no: no }, "kot"] } });
  const aks = (yon, ad, konum) => ({
    degerler: { sistem: "GLOBAL", yon: yon, ad: ad, konum: konum, gorunur: true },
    yol: { ad: ["akslar", yon.toLowerCase(), { ad: ad }, "ad"], konum: ["akslar", yon.toLowerCase(), { ad: ad }, "konum"], gorunur: ["akslar", yon.toLowerCase(), { ad: ad }, "gorunur"] },
    bag: { ad: { islem: "aks_ad", yon: yon.toLowerCase(), sistem: null } },
  });
  return [
    { ad: "katlar", baslik: "Katlar", grup: "Model", sutunlar: [
      { ad: "no", baslik: "Kat", tur: "sayi", ondalik: 0 }, { ad: "ad", baslik: "Ad", tur: "metin", duzenlenebilir: true },
      { ad: "kot", baslik: "Kot", birim: "m", tur: "sayi", ondalik: 2, duzenlenebilir: true }, { ad: "h", baslik: "Kat yüksekliği", birim: "m", tur: "sayi", ondalik: 2 }],
      satirlar: [kat(0, "Temel", 0, null), kat(1, "1. kat", 3, 3), kat(2, "Çatı", 6.25, 3.25)] },
    { ad: "akslar", baslik: "Akslar", grup: "Model", sutunlar: [
      { ad: "sistem", baslik: "Aks sistemi", tur: "metin" }, { ad: "yon", baslik: "Doğrultu", tur: "metin" },
      { ad: "ad", baslik: "Aks adı", tur: "metin", duzenlenebilir: true }, { ad: "konum", baslik: "Konum", birim: "m", tur: "sayi", ondalik: 3, duzenlenebilir: true },
      { ad: "gorunur", baslik: "Görünür", tur: "bool", duzenlenebilir: true }],
      satirlar: [aks("X", "A", 0), aks("X", "B", 5.5), aks("Y", "1", 0), aks("Y", "2", 4)] },
    { ad: "dosemeler", baslik: "Döşemeler; plaklar", grup: "Model", sutunlar: [
      { ad: "no", baslik: "No", tur: "sayi", ondalik: 0 }, { ad: "kullanim", baslik: "Kullanım", tur: "secim", duzenlenebilir: true,
        secenekler: [{ deger: "konut", etiket: "Konut" }, { deger: "ofis", etiket: "Ofis; büro" }] },
      { ad: "h", baslik: "Kalınlık", birim: "m", tur: "sayi", ondalik: 3, duzenlenebilir: true }, { ad: "alan", baslik: "Alan", birim: "m²", tur: "sayi" },
      { ad: "not", baslik: "Not", tur: "metin", duzenlenebilir: true, bos_olur: true }],
      satirlar: [
        { degerler: { no: 1, kullanim: "konut", h: 0.12, alan: 20.5, not: "çok\nsatırlı; \"tırnaklı\"" }, yol: { kullanim: ["dosemeler", { no: 1 }, "kullanim"], h: ["dosemeler", { no: 1 }, "h"], not: ["dosemeler", { no: 1 }, "not"] } },
        { degerler: { no: 2, kullanim: "ofis", h: 0.1 + 0.2, alan: 1 / 3, not: null }, yol: { kullanim: ["dosemeler", { no: 2 }, "kullanim"], h: ["dosemeler", { no: 2 }, "h"], not: ["dosemeler", { no: 2 }, "not"] } },
        { degerler: { no: 3, kullanim: "konut", h: 0.15, alan: 12, not: null } },          // yolsuz: salt okunur satır
      ],
      toplam: { alan: 20.5 + 1 / 3 + 12 } },
  ];
}

test("csvAyristir: BOM, CRLF/LF/CR, tırnaklı ayırıcı ve satır sonu, kaçışlı tırnak, sondaki satır sonu, sep= satırı", () => {
  assert.deepEqual(I.csvAyristir("﻿a;b\r\n1;2\r\n"), [["a", "b"], ["1", "2"]]);
  assert.deepEqual(I.csvAyristir('"x;y";"çok\r\nsatır";"""t"""\n;\r5'), [["x;y", "çok\nsatır", '"t"'], ["", ""], ["5"]]);
  assert.deepEqual(I.csvAyristir("a;b\n\n\nc;d"), [["a", "b"], [""], [""], ["c", "d"]]);
  assert.deepEqual(I.csvAyristir(""), []);
  assert.deepEqual(I.csvAyristir("sep=,\na;b,c\n"), [["a;b", "c"]]);
  assert.deepEqual(I.csvAyristir("a,b;c", { ayirici: "," }), [["a", "b;c"]]);
  assert.deepEqual(I.csvAyristir('"kapanmayan;tırnak\nsürer'), [["kapanmayan;tırnak\nsürer"]]);
});

test("csvAyiriciBul: ilk dolu satırda tırnak dışındaki ; , sekme; eşitlikte ;", () => {
  assert.equal(I.csvAyiriciBul("a;b;c\n1,2,3,4,5"), ";");
  assert.equal(I.csvAyiriciBul("a,b,c\n1;2"), ",");
  assert.equal(I.csvAyiriciBul("﻿\n\n  \na\tb\tc"), "\t");
  assert.equal(I.csvAyiriciBul('"a;b;c",d'), ",");               // tırnak içindeki ; sayılmaz
  assert.equal(I.csvAyiriciBul("a;b,c"), ";");
  assert.equal(I.csvAyiriciBul("tek"), ";");
  assert.equal(I.csvAyiriciBul("sep=\t\na;b;c"), "\t");
  // ayrıştırıcı ayırıcıyı kendisi bulur: virgüllü ve sekmeli dosyalar
  assert.deepEqual(I.csvAyristir('Ad,Değer\n"1,5",x'), [["Ad", "Değer"], ["1,5", "x"]]);
  assert.deepEqual(I.csvAyristir("Ad\tDeğer\n1,5\tx\n"), [["Ad", "Değer"], ["1,5", "x"]]);
});

test("csvMetniCoz: UTF-8 (BOM'lu/BOM'suz), geçersiz UTF-8 ise Türkçe Windows kod sayfası", () => {
  assert.equal(I.csvMetniCoz(new TextEncoder().encode("﻿şğı;İ")), "şğı;İ");
  assert.equal(I.csvMetniCoz(new TextEncoder().encode("Çatı")), "Çatı");
  assert.equal(I.csvMetniCoz(new Uint8Array([0xC7, 0x61, 0x74, 0xFD, 0x3B, 0xFE, 0xF0])), "Çatı;şğ");     // 1254 baytları
  assert.equal(I.csvMetniCoz("﻿metin"), "metin");
  assert.equal(I.csvMetniCoz(new Uint8Array([0x61, 0x62]).buffer), "ab");
});

test("CSV içe aktarma gidiş-dönüş: csvUret / tumunuCsv → csvAyristir → plan değişikliksiz (ondalık virgüllü ve virgülsüz)", () => {
  const tl = csvTablolari();
  for (const ay of [";", ",", "\t"]) {
    for (const ov of [true, false]) {
      for (const t of tl) {
        const p = I.csvIceAktarPlani(tl, t.ad, I.csvAyristir(I.csvUret(t, { ayirici: ay, ondalikVirgul: ov })), { ondalikVirgul: ov });
        assert.deepEqual([p.degisiklikler, p.hatalar, p.atlanan], [[], [], 0], t.ad + " " + JSON.stringify(ay) + " " + ov);
        assert.deepEqual(p.tablolar, [t.ad]);
      }
      const tum = I.csvIceAktarPlani(tl, "katlar", I.csvAyristir(I.tumunuCsv(tl, { ayirici: ay, ondalikVirgul: ov })), { ondalikVirgul: ov });
      assert.deepEqual([tum.degisiklikler, tum.hatalar, tum.atlanan], [[], [], 0], "bölümlü " + JSON.stringify(ay) + " " + ov);
      assert.deepEqual(tum.tablolar, ["katlar", "akslar", "dosemeler"]);
    }
  }
  // ondalık işareti seçeneği dosyadakinden farklı olsa da değişiklik çıkmaz
  const t = tl[0];
  const p = I.csvIceAktarPlani(tl, "katlar", I.csvAyristir(I.csvUret(t, { ondalikVirgul: true })), { ondalikVirgul: false });
  assert.deepEqual(p.degisiklikler, []);
  // süzülmüş / sıralanmış dışa aktarım (anahtarlı tablo) da değişikliksiz
  const s = I.csvIceAktarPlani(tl, "katlar", I.csvAyristir(I.csvUret(t, { idx: [2, 0] })), {});
  assert.deepEqual([s.degisiklikler, s.hatalar], [[], []]);
  assert.equal(I.csvOzetMetni(s), "CSV: değişiklik yok (dosyadaki değerler tablolarla aynı).");
});

test("CSV içe aktarma: tek değişen hücre doğru yol ve değerle tek değişiklik; seçim etiketi, evet/hayır, metin, aks adı bağı", () => {
  const tl = csvTablolari();
  let m = I.csvAyristir(I.csvUret(tl[0], {}));
  m[3][2] = "6,5";                                              // Çatı kotu 6,25 → 6,5
  let p = I.csvIceAktarPlani(tl, "katlar", m, { ondalikVirgul: true });
  assert.deepEqual(p.degisiklikler, [{ tablo: "katlar", satir: 2, sutun: "kot", yol: ["katlar", { no: 2 }, "kot"], deger: 6.5, ilk: 6.25 }]);
  assert.deepEqual(p.hatalar, []);
  assert.equal(I.csvOzetMetni(p), "CSV: 1 değişiklik bekliyor (Uygula), 0 uyarı");
  // uygulanınca bina değişir (yapıştırma ile aynı yol)
  const bina = { katlar: [{ no: 0, kot: 0 }, { no: 1, kot: 3 }, { no: 2, kot: 6.25 }] };
  assert.equal(I.degisiklikleriUygula(bina, p.degisiklikler).katlar[2].kot, 6.5);

  m = I.csvAyristir(I.csvUret(tl[2], { ayirici: "," , ondalikVirgul: false }));
  assert.equal(m[1][4], "çok\nsatırlı; \"tırnaklı\"");        // tırnaklı alan: ayırıcı ve satır sonu
  m[1][1] = "ofis; BÜRO"; m[2][2] = "0.25"; m[2][4] = "yeni not";
  p = I.csvIceAktarPlani(tl, "dosemeler", m, { ondalikVirgul: false });
  assert.deepEqual(p.degisiklikler.map((d) => [d.satir, d.sutun, d.deger]), [[0, "kullanim", "ofis"], [1, "h", 0.25], [1, "not", "yeni not"]]);

  m = I.csvAyristir(I.csvUret(tl[1], {}));
  m[2][2] = "B1"; m[4][4] = "hayır";
  p = I.csvIceAktarPlani(tl, "akslar", m, {});
  assert.deepEqual(p.degisiklikler.map((d) => [d.satir, d.sutun, d.deger, d.bag ? d.bag.islem : null]), [[1, "ad", "B1", "aks_ad"], [3, "gorunur", false, null]]);
  assert.deepEqual(p.hatalar, []);
});

test("CSV içe aktarma: bilinmeyen ve düzenlenemez sütunlar, salt okunur satır, hatalı değer, toplam satırı, yinelenen satır", () => {
  const tl = csvTablolari();
  let m = I.csvAyristir(I.csvUret(tl[2], {}));
  assert.equal(m[m.length - 1][0], "Toplam");
  m[0].push("Renk"); m[1].push("kırmızı");
  m[1][3] = "99";                                               // Alan salt okunur
  m[3][2] = "0,2";                                              // satır 3 yolsuz: salt okunur hücre
  m[2][2] = "kalın";                                            // sayı değil
  let p = I.csvIceAktarPlani(tl, "dosemeler", m, {});
  assert.deepEqual(p.degisiklikler, []);
  assert.ok(p.hatalar.includes("Sütun bulunamadı: Renk"), p.hatalar);
  assert.ok(p.hatalar.includes("Düzenlenemez sütun: Alan [m²] (1 hücre farklı, atlandı)"), p.hatalar);
  assert.ok(p.hatalar.some((h) => /^Satır 3, Kalınlık: sayı okunamadı: "kalın"$/.test(h)), p.hatalar);
  assert.ok(p.hatalar.some((h) => /^1 salt okunur hücre farklı, atlandı/.test(h)), p.hatalar);
  assert.equal(p.atlanan, 2);
  assert.equal(I.csvOzetMetni(p), "CSV: değişiklik yok, 4 uyarı");

  m = I.csvAyristir(I.csvUret(tl[0], {}));
  m.push(["7", "Yeni", "9"], ["1", "1. kat", "3,5"]);           // tabloda olmayan kat, yinelenen kat
  m[0][1] = "AD"; m[0][2] = " kot [M] ";                        // büyük/küçük harf ve boşluk duyarsız başlık
  p = I.csvIceAktarPlani(tl, "katlar", m, {});
  assert.deepEqual(p.degisiklikler, []);
  assert.ok(p.hatalar.includes("Satır 5: tabloda karşılığı yok (Kat = 7)."), p.hatalar);
  assert.ok(p.hatalar.includes("Satır 6: aynı tablo satırı dosyada yineleniyor; yalnız ilki kullanıldı."), p.hatalar);
  m = [["Kat", "Kot [m]", "Kot [m]"], ["1", "4", "5"]];
  p = I.csvIceAktarPlani(tl, "katlar", m, {});
  assert.deepEqual(p.degisiklikler.map((d) => d.deger), [4]);
  assert.deepEqual(p.hatalar, ["Sütun yinelenmiş: Kot [m] (yalnız ilki kullanıldı)"]);
});

test("CSV içe aktarma: anahtarsız sırada satırlar yalnız dosya tablonun sırasını izliyorsa yazılır; aks adı değişen satır sırayla", () => {
  const tl = csvTablolari();
  const ak = tl[1];
  // ters sıralı dışa aktarım: akslar sistem + yön + ad anahtarıyla doğru satıra yazılır
  let m = I.csvAyristir(I.csvUret(ak, { idx: [3, 2, 1, 0] }));
  m[1][3] = "4,5";
  let p = I.csvIceAktarPlani(tl, "akslar", m, {});
  assert.deepEqual(p.degisiklikler.map((d) => [d.satir, d.deger]), [[3, 4.5]]);
  // ters sırada ad değiştirilen satır: sıra tutmadığı için yazılmaz (yanlış aksa yazmaktansa)
  m = I.csvAyristir(I.csvUret(ak, { idx: [3, 2, 1, 0] }));
  m[1][2] = "2B";
  p = I.csvIceAktarPlani(tl, "akslar", m, {});
  assert.deepEqual(p.degisiklikler, []);
  assert.deepEqual(p.hatalar, ["Satır 2: tabloda karşılığı yok (Aks sistemi = GLOBAL, Doğrultu = Y, Aks adı = 2B)."]);
  // anahtar sütunu dosyada yoksa satırlar sırayla eşlenir; salt okunur hücre uymazsa hiçbiri yazılmaz
  m = [["Doğrultu", "Konum [m]"], ["X", "1"], ["Y", "2"], ["X", "3"], ["Y", "4"]];
  p = I.csvIceAktarPlani(tl, "akslar", m, {});
  assert.deepEqual(p.degisiklikler, []);
  assert.equal(p.hatalar.length, 1);
  assert.match(p.hatalar[0], /^Satır 3: salt okunur sütunlar \(Doğrultu\) tablodaki 2\. satırla uyuşmuyor; .* 3 satır atlandı/);       // (Y, 4) anahtarla bulunur
  m = [["Doğrultu", "Konum [m]"], ["X", "1"], ["X", "5,5"], ["Y", "0"]];       // (X, 5,5) ve (Y, 0) anahtarla yerinde: sıra tutar
  p = I.csvIceAktarPlani(tl, "akslar", m, {});
  assert.deepEqual(p.degisiklikler.map((d) => [d.satir, d.deger]), [[0, 1]]);
  assert.deepEqual(p.hatalar, []);
  m = [["Doğrultu", "Görünür"], ["X", "hayır"], ["X", "evet"], ["Y", "evet"]];   // benzersiz önek yok: yalnız sırayla
  p = I.csvIceAktarPlani(tl, "akslar", m, {});
  assert.deepEqual(p.degisiklikler.map((d) => [d.satir, d.sutun, d.deger]), [[0, "gorunur", false]]);
  assert.deepEqual(p.hatalar, ["Satır sayısı farklı (dosyada 3, tabloda 4); satırlar sırayla eşlendi."]);
});

test("CSV içe aktarma: bölümlü dosya tablolara adla eşlenir; bilinmeyen tablo, başlığı etkin tabloya uymayan tek tablo", () => {
  const tl = csvTablolari();
  let m = I.csvAyristir(I.tumunuCsv([tl[2], tl[0]], { ayirici: ";", ondalikVirgul: true }));
  const satir = m.findIndex((r) => r[0] === "1" && r[1] === "1. kat");
  assert.ok(satir > 0);
  m[satir][1] = "Zemin üstü";
  m.push(["Tablo: Yok tablo", "Model", "yok"], ["A", "B"], ["1", "2"]);
  let p = I.csvIceAktarPlani(tl, "akslar", m, { ondalikVirgul: true });
  assert.deepEqual(p.degisiklikler.map((d) => [d.tablo, d.satir, d.sutun, d.deger]), [["katlar", 1, "ad", "Zemin üstü"]]);
  assert.deepEqual(p.hatalar, ["Satır " + (m.length - 2) + ": tablo bulunamadı: Yok tablo (yok)"]);
  assert.deepEqual(p.tablolar, ["dosemeler", "katlar"]);
  assert.equal(p.atlanan, 2);
  // bölümlü dosyada uyarılar tablonun adıyla başlar; ad hücresi yoksa başlıkla bulunur
  m = [["Tablo: Katlar", "Model"], ["Kat", "Kot [m]", "Renk"], ["0", "0"]];
  p = I.csvIceAktarPlani(tl, null, m, {});
  assert.deepEqual(p.hatalar, ["“Katlar”, sütun bulunamadı: Renk"]);
  // tek tablolu dosya etkin tabloya uymuyorsa başlıkları en çok uyan tabloya
  m = I.csvAyristir(I.csvUret(tl[0], {}));
  m[2][1] = "Birinci";
  p = I.csvIceAktarPlani(tl, "akslar", m, {});
  assert.deepEqual(p.degisiklikler.map((d) => [d.tablo, d.deger]), [["katlar", "Birinci"]]);
  assert.deepEqual(p.hatalar, []);
  assert.deepEqual(p.notlar, ["Dosya “Katlar” tablosuna aktarıldı (başlıklar ve satırlar etkin tablo “Akslar” yerine ona uyuyor)."]);
  // aynı başlıklı tablolar (Genel / Temel parametreleri…): satırları anahtarla en çok bulunan, sonra dosya adındaki tablo
  const par = (ad, baslik, adlar) => ({ ad: ad, baslik: baslik, grup: "Model", sutunlar: [{ ad: "parametre", baslik: "Parametre", tur: "metin" },
    { ad: "deger", baslik: "Değer", tur: "sayi", duzenlenebilir: true }], satirlar: adlar.map((a, i) => ({ degerler: { parametre: a, deger: i }, yol: { deger: [ad, a] } })) });
  const pt = [par("genel", "Genel", ["a", "b"]), par("temel_parametreleri", "Temel parametreleri", ["q", "k"]), par("metraj", "Metraj", ["a", "b"])];
  m = I.csvAyristir(I.csvUret(pt[1], {})); m[2][1] = "7";
  p = I.csvIceAktarPlani(pt, "genel", m, {});
  assert.deepEqual(p.degisiklikler.map((d) => [d.tablo, d.yol, d.deger]), [["temel_parametreleri", ["temel_parametreleri", "k"], 7]]);
  m = I.csvAyristir(I.csvUret(pt[2], {})); m[1][1] = "5";
  assert.deepEqual(I.csvIceAktarPlani(pt, "genel", m, {}).degisiklikler.map((d) => d.tablo), ["genel"]);           // eşitlikte etkin tablo
  p = I.csvIceAktarPlani(pt, "genel", m, { dosyaAdi: "C:\\İndirilenler\\Bina_1_metraj.csv" });
  assert.deepEqual(p.degisiklikler.map((d) => d.tablo), ["metraj"]);                                                // dosya adındaki tablo
  p = I.csvIceAktarPlani(tl, "akslar", [["Renk", "Boy"], ["a", "b"]], {});
  assert.deepEqual(p.hatalar, ["Sütun bulunamadı: Renk", "Sütun bulunamadı: Boy"]);
  assert.deepEqual(I.csvIceAktarPlani(tl, null, [["Renk"]], {}).hatalar, ["Başlık satırı hiçbir tabloya uymuyor (tanınan sütun yok)."]);
  assert.deepEqual(I.csvIceAktarPlani(tl, "katlar", [[""], ["", " "]], {}).hatalar, ["CSV dosyasında satır yok."]);
  // aynı model alanı iki tabloda farklı değerle
  const iki = csvTablolari();
  iki.push(Object.assign({}, iki[0], { ad: "katlar2", baslik: "Katlar 2" }));
  m = I.csvAyristir(I.tumunuCsv([iki[0], iki[3]], {}));
  m[3][2] = "3,1";
  m[m.findIndex((r, i) => i > 6 && r[0] === "1")][2] = "3,2";
  p = I.csvIceAktarPlani(iki, null, m, {});
  assert.deepEqual(p.degisiklikler.map((d) => d.deger), [3.1, 3.2]);
  assert.deepEqual(p.hatalar, ["Aynı model alanı (katlar › [no = 1] › kot) dosyada iki kez farklı değerle var; sonuncusu kullanıldı."]);
});

test("CSV içe aktarma planı Duzenleme'ye yapıştırma gibi eklenir (tek geri al adımı)", () => {
  const tl = csvTablolari();
  const m = I.csvAyristir(I.csvUret(tl[0], {}));
  m[1][1] = "Bodrum"; m[2][2] = "3,1";
  const p = I.csvIceAktarPlani(tl, "katlar", m, {});
  const d = new I.Duzenleme();
  assert.equal(d.ekle(p.degisiklikler), 2);
  assert.equal(d.sayi(), 2);
  assert.deepEqual(Array.from(d.tablolar()), ["katlar"]);
  assert.equal(d.deger(["katlar", { no: 1 }, "kot"]).deger, 3.1);
  assert.equal(d.geriAl(), true);
  assert.equal(d.sayi(), 0);
  assert.equal(M.surum, "1.1.0");
});
