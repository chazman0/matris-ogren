// Eşdeğerlik derlemi (B; MIMARI §9.5, D35; kabul B6) — node tarafı: op4/testler/derlem/derlem.jsonl'deki her üçlü bugünkü
// docs/ ve op4/js modülleriyle node'da yeniden oynatılır ve kayıtlı çıktıyla aynı olmalıdır (aynı kural: sayılarda bağıl 1e-12).
// Düşerse modüller derlem üretildikten sonra davranış değiştirmiştir: `node op4/testler/js/derlem_uret.js` ile yeniden
// üretin (C++ cekirdek_js_derlem.cpp aynı derlemi QuickJS'te oynatır).
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const DEPO = path.resolve(__dirname, "..", "..", "..");
const DERLEM = path.join(DEPO, "op4", "testler", "derlem");
const D = require(path.join(DERLEM, "derlem_ortak.js"));

function yukle() {
  const satirlar = fs.readFileSync(path.join(DERLEM, "derlem.jsonl"), "utf8").split("\n").filter(Boolean);
  const ust = JSON.parse(satirlar[0]);
  const baglam = { sablonlar: {}, sonuclar: {} };
  for (const ad of ust.sablonlar) baglam.sablonlar[ad] = fs.readFileSync(path.join(DERLEM, "sablonlar", ad + ".json"), "utf8");
  for (const ad of ust.sonuclar) baglam.sonuclar[ad] = fs.readFileSync(path.join(DERLEM, "sonuclar", ad + ".json"), "utf8");
  return { ust: ust, kayitlar: satirlar.slice(1).map((s) => JSON.parse(s)), baglam: baglam };
}

test("derlem: üst bilgi, kapsam (9 şablon, sınama kaynakları, bütün çekirdek modülleri)", () => {
  const { ust, kayitlar } = yukle();
  assert.equal(ust.bicim, D.BICIM);
  assert.equal(ust.sayi, kayitlar.length);
  assert.equal(ust.sablonlar.length, 9);
  const kaynak = new Set(kayitlar.map((k) => k.k));
  for (const s of ["sablon", "testler/js/model_ops.test.js", "testler/js/aks_sistemi.test.js", "testler/js/bina_cizim.test.js",
    "testler/js/ifc_disari.test.js", "testler/js/tablo_editoru.test.js", "op4/testler/js/op4_ops.test.js"]) assert.ok(kaynak.has(s), s);
  const modul = new Set(kayitlar.map((k) => k.m));
  for (const m of ["ModelOps", "MatrisAks", "MatrisBinaCizim", "MatrisIFC", "MatrisTablo", "Op4Ops", "$senaryo"]) assert.ok(modul.has(m), m);
  // her şablonun cephe senaryosu var
  const senaryo = kayitlar.filter((k) => k.m === "$senaryo" && k.f === "cephe").map((k) => JSON.stringify(k.a[0].adimlar[0]));
  for (const ad of ust.sablonlar) assert.ok(senaryo.some((s) => s.includes('"' + ad + '"')), ad);
});

test("derlem: her üçlü bugünkü modüllerle node'da aynı çıktıyı verir (yeniden üretmek gerekirse ileti söyler)", () => {
  const { ust, kayitlar, baglam } = yukle();
  const M = {
    ModelOps: require(path.join(DEPO, "docs", "model_ops.js")), MatrisAks: require(path.join(DEPO, "docs", "aks_sistemi.js")),
    MatrisBinaCizim: require(path.join(DEPO, "docs", "bina_cizim.js")), MatrisIFC: require(path.join(DEPO, "docs", "ifc_disari.js")),
    MatrisTablo: require(path.join(DEPO, "docs", "tablo_editoru.js")), Op4Ops: require(path.join(DEPO, "op4", "js", "op4_ops.js")),
    Op4Cekirdek: require(path.join(DEPO, "op4", "js", "op4_cekirdek.js")),
  };
  M.Op4Ops.bagimliliklarKur({ ModelOps: M.ModelOps, MatrisAks: M.MatrisAks, MatrisIFC: M.MatrisIFC });
  const degisen = Object.keys(ust.moduller).filter((d) =>
    crypto.createHash("sha256").update(fs.readFileSync(path.join(DEPO, d))).digest("hex") !== ust.moduller[d]);
  const geri = D.saatSabitle(globalThis);
  const farklar = [];
  try {
    for (const k of kayitlar) {
      let r;
      try { r = D.calistir(M, k, baglam); } catch (e) { r = { hata: String(e) }; }
      const f = D.fark(k.s !== undefined ? { s: k.s } : { h: k.h }, r);
      if (f) farklar.push(k.m + "." + k.f + " (" + k.k + ")" + f);
    }
  } finally { geri(); }
  assert.deepEqual(farklar.slice(0, 10), [],
    farklar.length + " üçlü farklı; derlem üretildikten sonra değişen modüller: " + (degisen.join(", ") || "yok") +
    ". Yeniden üretin: node op4/testler/js/derlem_uret.js");
});

test("derlem ortak kodu: kodla / çöz gidiş-dönüşü ve karşılaştırma kuralı", () => {
  const x = { a: [1, undefined, NaN, -Infinity], t: new Float64Array([1.5, NaN]), u: new Uint32Array([4294967295]), $d: "dolar", s: "ş" };
  const k = D.kodla(x);
  assert.deepEqual(JSON.parse(JSON.stringify(k)), k);
  const c = D.coz(k, {});
  assert.deepEqual(c.a, [1, undefined, NaN, -Infinity]);
  assert.ok(c.t instanceof Float64Array && c.t[0] === 1.5 && Number.isNaN(c.t[1]));
  assert.ok(c.u instanceof Uint32Array && c.u[0] === 4294967295);
  assert.equal(c.$d, "dolar");
  assert.throws(() => D.kodla({ f: () => 1 }), D.Atla);
  assert.throws(() => D.kodla(new Map()), D.Atla);
  const d = {}; d.d = d;
  assert.throws(() => D.kodla(d), D.Atla);
  assert.equal(D.fark({ a: 1 + 1e-13 }, { a: 1 }), null);
  assert.equal(D.fark({ a: 1e-13 }, { a: 0 }), null);
  assert.match(D.fark({ a: 1 + 1e-11 }, { a: 1 }), /^\.a: /);
  assert.match(D.fark({ a: "x" }, { a: "y" }), /^\.a: /);
  assert.match(D.fark([1, 2], [1]), /uzunluk/);
  assert.deepEqual(D.metinOzeti("op4"), D.metinOzeti("op4"));
  assert.notDeepEqual(D.metinOzeti("op4a"), D.metinOzeti("op4b"));
  const geri = D.saatSabitle(globalThis);
  try {
    assert.equal(Date.now(), D.SABIT_SAAT);
    assert.equal(new Date().getTime(), D.SABIT_SAAT);
    assert.equal(new Date(0).getTime(), 0);
    assert.ok(new Date() instanceof Date);
  } finally { geri(); }
  assert.notEqual(Date.now(), D.SABIT_SAAT);
});
