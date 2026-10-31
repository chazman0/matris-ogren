// op4/js/op4_onyukleme.js (QuickJS ön yüklemesi; B, MIMARI §9.2, kabul B2) — node vm bağlamında sınanır: öykünmeler
// (__op4_oykunme_zorla) aynı bağlamın yerli V8 / ICU işlevleriyle karşılaştırılır. QuickJS'te aynı dosya ctest
// cekirdek_js_ortam ve eşdeğerlik derlemiyle (cekirdek_js_derlem) sınanır.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const ONYUKLEME = path.join(__dirname, "..", "..", "js", "op4_onyukleme.js");
const H = require(path.join(__dirname, "harman_uret.js"));

/** vm bağlamında değerlendirir; dönüş bu bağlamın değerine çevrilir (başka bağlamın dizileri deepStrictEqual'da eşit sayılmaz). */
const calis = (kod, b) => { const r = vm.runInContext("JSON.stringify(" + kod + ")", b); return r === undefined ? undefined : JSON.parse(r); };

/** Ön yüklemeyi yeni bir bağlamda çalıştırır; öykünmeden önceki yerli işlevler `yerli` altında. */
function baglam(ek) {
  const gunluk = [];
  const b = vm.createContext(Object.assign({ __op4_gunluk: (d, m) => gunluk.push([d, m]), __op4_oykunme_zorla: true }, ek || {}));
  vm.runInContext("globalThis.yerli = { localeCompare: String.prototype.localeCompare, lower: String.prototype.toLocaleLowerCase, upper: String.prototype.toLocaleUpperCase };" +
    "globalThis.window = {}; globalThis.document = {};", b);
  vm.runInContext(fs.readFileSync(ONYUKLEME, "utf8"), b, { filename: "op4/js/op4_onyukleme.js" });
  return { b: b, gunluk: gunluk };
}

test("ön yükleme: self, window / document yok, console → günlük, deterministik saat", () => {
  const { b, gunluk } = baglam({ __op4_deterministik: true });
  assert.equal(vm.runInContext("self === globalThis && typeof window === 'undefined' && typeof document === 'undefined'", b), true);
  vm.runInContext("console.log('a', {b: 1}); console.warn(new TypeError('x')); console.error('e'); console.debug('d')", b);
  assert.deepEqual(gunluk, [["bilgi", 'a {"b":1}'], ["uyari", "TypeError: x"], ["hata", "e"], ["ayrinti", "d"]]);
  assert.deepEqual(calis("[Date.now(), Date.now()]", b), [Date.UTC(2026, 0, 1), Date.UTC(2026, 0, 1) + 1]);
  // Intl varken (öykünme zorlanmadan) yerli işlevlere dokunulmaz
  const yerli = vm.createContext({});
  vm.runInContext("globalThis.lc = String.prototype.localeCompare;", yerli);
  vm.runInContext(fs.readFileSync(ONYUKLEME, "utf8"), yerli);
  assert.equal(vm.runInContext("String.prototype.localeCompare === lc && typeof self === 'object'", yerli), true);
});

test("harmanlama tablosu ICU'dan güncel (node op4/testler/js/harman_uret.js)", (t) => {
  const m = fs.readFileSync(ONYUKLEME, "utf8");
  const a = m.indexOf(H.BAS), s = m.indexOf(H.SON);
  assert.ok(a > 0 && s > a);
  const icu = H.gomuluIcu(m.slice(a, s));
  assert.ok(icu, "tabloda ICU sürümü yok");
  // başka ICU sürümünde tablo birebir aynı olmayabilir; davranış yine aşağıdaki sınamayla ICU'ya karşı denetlenir
  if (icu !== process.versions.icu) { t.skip("tablo ICU " + icu + " ile üretildi, bu node ICU " + process.versions.icu); return; }
  assert.equal(m.slice(a + H.BAS.length, s), H.gomulu());
});

test("localeCompare öykünmesi ICU ile aynı sırayı verir (tr numeric/base — tablo_editoru sıralaması — ve varsayılanlar)", () => {
  const { b } = baglam();
  const sozcukler = ["", "a", "A", "â", "Â", "b", "c", "C", "ç", "Ç", "d", "g", "ğ", "Ğ", "h", "ı", "I", "i", "İ", "j", "o", "ö", "Ö",
    "s", "ş", "Ş", "u", "ü", "Ü", "z", "Z", "é", "ß", "ss", "æ", "ae", " ", "-", "_", ".", ",", "(", "/", "#", "%", "+", "=", "°", "²",
    "0", "00", "01", "1", "2", "9", "10", "011", "100", "1.5", "1,5", "x2", "x10", "K101", "K12", "K9", "k9", "S1-2", "S1-10",
    "HEA 300", "HEA 280", "HEB 300", "IPE 270", "IPE270", "Ağırlık", "ağırlık", "AĞIRLIK", "Işık", "ışık", "İzmir", "izmir", "Izmir",
    "Çatı", "çatı", "catı", "Öteleme", "oteleme", "Üst kat", "ust kat", "Şerit", "serit", "Temel", "temel", "kiriş", "Kiriş", "kiris",
    "D/C", "d/c", "2. kat", "10. kat", "A-1", "A1", "A10", "A2", "B 1", "B1", "Kolon 1", "Kolon 10", "Kolon 2", "Kolon", "Σ", "α", "β",
    "Δx", "€", "—", "–", "…", "“x”", "’", "x́", "x­"];
  const ikililer = [];
  for (const x of sozcukler) for (const y of sozcukler) ikililer.push([x, y]);
  // rastgele (belirlenimci) karışımlar
  let t = 12345;
  const r = () => (t = (Math.imul(t, 1103515245) + 12345) >>> 0) / 4294967296;
  const harfler = "aAâbcçÇdeEgğĞhıIiİoöÖsşŞuüÜzZ0123456789 -_.,/";
  for (let n = 0; n < 4000; n++) {
    const s = () => { let q = ""; const L = 1 + Math.floor(r() * 6); for (let i = 0; i < L; i++) q += harfler[Math.floor(r() * harfler.length)]; return q; };
    ikililer.push([s(), s()]);
  }
  vm.runInContext("globalThis.__ikililer = " + JSON.stringify(ikililer), b);
  const durumlar = [["'tr'", "{numeric: true, sensitivity: 'base'}"], ["'tr'", "undefined"], ["'tr'", "{sensitivity: 'accent'}"],
    ["'tr'", "{numeric: true}"], ["undefined", "undefined"], ["'en'", "{sensitivity: 'base'}"], ["'en-US'", "{numeric: true}"]];
  for (const [yerel, sec] of durumlar) {
    const fark = calis("(function () { const f = []; for (const [x, y] of __ikililer) {" +
      " const a = Math.sign(x.localeCompare(y, " + yerel + ", " + sec + ")), e = Math.sign(yerli.localeCompare.call(x, y, " + yerel + ", " + sec + "));" +
      " if (a !== e) f.push(JSON.stringify([x, y, a, e])); } return f; })()", b);
    assert.deepEqual(fark.slice(0, 12), [], yerel + " " + sec + ": " + fark.length + " / " + ikililer.length + " ikili farklı");
  }
});

test("toLocaleLowerCase / toLocaleUpperCase('tr') öykünmesi ICU ile aynı", () => {
  const { b } = baglam();
  const ornek = ["IŞIK", "İzmir", "ılık", "istanbul", "ÇĞİÖŞÜ", "çğıöşü", "Iİıi", "ABC", "x", "", "Kiriş K101"];
  for (const s of ornek) {
    for (const y of ["'tr'", "'tr-TR'", "['tr']", "'en'", "undefined"]) {
      const a = calis("[" + JSON.stringify(s) + ".toLocaleLowerCase(" + y + "), " + JSON.stringify(s) + ".toLocaleUpperCase(" + y + ")]", b);
      const e = calis("[yerli.lower.call(" + JSON.stringify(s) + ", " + y + "), yerli.upper.call(" + JSON.stringify(s) + ", " + y + ")]", b);
      assert.deepEqual(a, e, s + " " + y);
    }
  }
});

test("TextDecoder öykünmesi node (WHATWG) ile aynı: utf-8 (fatal, BOM, bozuk diziler) ve windows-1254", () => {
  const { b } = baglam({ TextDecoder: undefined });
  const diziler = [[], [0x41], [0xef, 0xbb, 0xbf, 0x41], [0xef, 0xbb, 0xbf], [0xc3, 0xa7, 0xc4, 0x9f, 0xc4, 0xb1], [0xff], [0xc3],
    [0xe0, 0x80, 0x80], [0xed, 0xa0, 0x80], [0xf4, 0x90, 0x80, 0x80], [0xf0, 0x9f, 0x98, 0x80], [0x80, 0x41], [0xc3, 0x41],
    [0xe2, 0x82], [0xe2, 0x82, 0xac], [0x61, 0xf0, 0x9f, 0x98], [0xc0, 0xaf]];
  const tum = []; for (let i = 0; i < 256; i++) tum.push(i);
  diziler.push(tum);
  for (const d of diziler) {
    for (const [etiket, sec] of [["utf-8", {}], ["utf-8", { fatal: true }], ["utf8", { ignoreBOM: true }], ["windows-1254", {}],
      ["iso-8859-9", {}], ["cp1254", {}]]) {
      let e, a;
      try { e = new TextDecoder(etiket, sec).decode(new Uint8Array(d)); } catch (x) { e = x.name + ": " + x.message; }
      a = vm.runInContext("(function () { try { return new TextDecoder(" + JSON.stringify(etiket) + ", " + JSON.stringify(sec) +
        ").decode(new Uint8Array(" + JSON.stringify(d) + ")); } catch (x) { return x.name + ': ' + x.message; } })()", b);
      assert.equal(a, e, etiket + " " + JSON.stringify(sec) + " " + JSON.stringify(d).slice(0, 40));
    }
  }
  const h = vm.runInContext("(function () { try { new TextDecoder('xyz'); } catch (x) { return x.name + ': ' + x.message; } })()", b);
  let e; try { new TextDecoder("xyz"); } catch (x) { e = x.name + ": " + x.message; }
  assert.equal(h, e);
  assert.equal(vm.runInContext("new TextDecoder().encoding + new TextDecoder('Latin5').encoding", b), "utf-8windows-1254");
});
