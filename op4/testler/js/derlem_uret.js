#!/usr/bin/env node
/* op4 — eşdeğerlik derlemi üreteci (MIMARI §9.5, D35; kabul B6). Sahibi: B (model-cekirdegi).
   Çalıştırma (depo kökünden): node op4/testler/js/derlem_uret.js   → op4/testler/derlem/derlem.jsonl

   (işlem, girdi, çıktı) üçlüleri iki kaynaktan gelir:
     1. Mevcut node sınamaları: testler/js/{model_ops,aks_sistemi,bina_cizim,ifc_disari,tablo_editoru}.test.js ve
        op4/testler/js/{op4_ops,op4_cekirdek,sozlesme}.test.js bu süreçte koşturulur; çekirdek modüllerinin (docs/model_ops.js,
        aks_sistemi.js, bina_cizim.js, ifc_disari.js, tablo_editoru.js, op4/js/op4_ops.js) dışa açık işlevlerine yapılan
        en dıştaki çağrılar kaydedilir (iç içe çağrılar ve kodlanamayan girdiler — işlev, Map, sınıf örneği — alınmaz).
     2. 9 şablon (op4/testler/derlem/sablonlar; yapi.bina_sablon dökümü): Op4Ops sahne / kat / kullanım yeri / öznitelik /
        sonuç eşleme, ModelOps genellestir / denetle, MatrisBinaCizim genel geçiş, MatrisIFC dışa aktarma ve cephe (Op4Cekirdek)
        senaryoları.
   Her üçlü yazılmadan önce node'da kodlanmış girdiden YENİDEN çalıştırılır; aynı çıktıyı vermeyen (zamana, rastgeleliğe ya
   da nesne kimliğine bağlı) üçlü atılır. Saat üretimde ve oynatmada sabittir (DerlemOrtak.SABIT_SAAT).
   docs/ modülleri değiştikçe yeniden üretilir; op4/testler/js/derlem.test.js derlemin node davranışıyla aynı olduğunu
   denetler, C++ cekirdek_js_derlem.cpp aynı üçlüleri QuickJS'te oynatır (bağıl 1e-12). */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const Module = require("node:module");

const DEPO = path.resolve(__dirname, "..", "..", "..");
const OP4 = path.join(DEPO, "op4");
const DERLEM = path.join(OP4, "testler", "derlem");
const D = require(path.join(DERLEM, "derlem_ortak.js"));

// Boy sınırları (derlem depoda kalır; hedef ≈ 3 MB): sınamalardan gelen üçlülerde tek üçlü ve işlev başına toplam; şablon
// üçlülerinde tek üçlü.
const SINAMA_UCLU_SINIRI = 16 * 1024;
const SINAMA_ISLEV_BAYT = 24 * 1024;
const SINAMA_ISLEV_ADET = 40;
const SABLON_UCLU_SINIRI = 1024 * 1024;
const KUCUK_SABLONLAR = ["betonarme-tek-aciklik", "celik-1kat-depo"];   // IFC metni tam saklanır

const KAYITLI = {
  [path.join(DEPO, "docs", "model_ops.js")]: "ModelOps",
  [path.join(DEPO, "docs", "aks_sistemi.js")]: "MatrisAks",
  [path.join(DEPO, "docs", "bina_cizim.js")]: "MatrisBinaCizim",
  [path.join(DEPO, "docs", "ifc_disari.js")]: "MatrisIFC",
  [path.join(DEPO, "docs", "tablo_editoru.js")]: "MatrisTablo",
  [path.join(OP4, "js", "op4_ops.js")]: "Op4Ops",
};
const SINAMALAR = [
  "testler/js/model_ops.test.js", "testler/js/aks_sistemi.test.js", "testler/js/bina_cizim.test.js",
  "testler/js/ifc_disari.test.js", "testler/js/tablo_editoru.test.js",
  "op4/testler/js/op4_ops.test.js", "op4/testler/js/op4_cekirdek.test.js", "op4/testler/js/sozlesme.test.js",
];

// ---------------------------------------------------------------- şablonlar ve çözüm verileri (başvurular)
const SABLONLAR = fs.readdirSync(path.join(DERLEM, "sablonlar")).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5)).sort();
const SONUCLAR = fs.readdirSync(path.join(DERLEM, "sonuclar")).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5)).sort();
const baglam = { sablonlar: {}, sonuclar: {} };
const kanonik = new Map();     // JSON.stringify(nesne) → başvuru
for (const ad of SABLONLAR) {
  baglam.sablonlar[ad] = fs.readFileSync(path.join(DERLEM, "sablonlar", ad + ".json"), "utf8");
  kanonik.set(JSON.stringify(JSON.parse(baglam.sablonlar[ad])), { $sablon: ad });
}
for (const ad of SONUCLAR) {
  baglam.sonuclar[ad] = fs.readFileSync(path.join(DERLEM, "sonuclar", ad + ".json"), "utf8");
  kanonik.set(JSON.stringify(JSON.parse(baglam.sonuclar[ad])), { $sonuc: ad });
}
function girdiKodla(args) {
  return args.map(function (x) {
    if (x && typeof x === "object" && !Array.isArray(x) && (x.tur === "bina" || x.tasarim)) {
      const r = kanonik.get(JSON.stringify(x));
      if (r) return r;
    }
    return D.kodla(x);
  });
}

// ---------------------------------------------------------------- kayıt (sınamalar koşarken)
const kayitlar = [];
const gorulen = new Set();
const islevSayisi = new Map(), islevBayt = new Map();
let derinlik = 0, kayitAcik = true, kaynak = "";
const atlanan = { kodlanamaz: 0, buyuk: 0, tekrar: 0, sinir: 0 };

function kaydet(m, f, args, sonuc, hata) {
  let a;
  try { a = girdiKodla(args); } catch (e) { if (e instanceof D.Atla) { atlanan.kodlanamaz++; return; } throw e; }
  const ak = JSON.stringify(a);
  const anahtar = m + "|" + f + "|" + crypto.createHash("sha1").update(ak).digest("hex");
  if (gorulen.has(anahtar)) { atlanan.tekrar++; return; }
  const sablon = kaynak === "sablon";
  const n = islevSayisi.get(m + "." + f) || 0, bayt = islevBayt.get(m + "." + f) || 0;
  if (!sablon && (n >= SINAMA_ISLEV_ADET || bayt >= SINAMA_ISLEV_BAYT)) { atlanan.sinir++; return; }
  let k;
  try { k = hata ? { m: m, f: f, a: a, h: D.istisna(hata), k: kaynak } : { m: m, f: f, a: a, s: D.kodla(sonuc), k: kaynak }; } catch (e) {
    if (e instanceof D.Atla) { atlanan.kodlanamaz++; return; }
    throw e;
  }
  const metin = JSON.stringify(k);
  if (metin.length > (sablon ? SABLON_UCLU_SINIRI : SINAMA_UCLU_SINIRI)) { atlanan.buyuk++; return; }
  gorulen.add(anahtar);
  islevSayisi.set(m + "." + f, n + 1);
  if (!sablon) islevBayt.set(m + "." + f, bayt + metin.length);
  kayitlar.push(k);
}

function sar(m, yol, fn, sahip) {
  return function () {
    if (derinlik > 0 || !kayitAcik) return fn.apply(sahip, arguments);
    // girdi çağrıdan ÖNCE kodlanır (işlev girdiyi değiştirebilir)
    const args = Array.prototype.slice.call(arguments);
    let once = null;
    try { once = girdiKodla(args); } catch (e) { once = null; }
    derinlik++;
    let r, h = null;
    try { r = fn.apply(sahip, arguments); } catch (e) { h = e; } finally { derinlik--; }
    if (once) kaydet(m, yol, once.map((x) => D.coz(x, baglam)), r, h);
    else atlanan.kodlanamaz++;
    if (h) throw h;
    return r;
  };
}
/** Modül dışa aktarımının kaydeden kopyası: işlevler (büyük harfli kurucular hariç) ve bir düzey iç içe işlev nesneleri. */
function kaydeden(m, api) {
  const o = {};
  if (Object.isFrozen(api)) process.nextTick(function () { Object.freeze(o); });
  for (const k of Object.keys(api)) {
    const v = api[k];
    if (typeof v === "function" && !/^[A-ZÇĞİÖŞÜ]/.test(k)) o[k] = sar(m, k, v, api);
    else if (v && typeof v === "object" && !Array.isArray(v) && Object.keys(v).some((x) => typeof v[x] === "function")) {
      const ic = {};
      for (const x of Object.keys(v)) ic[x] = typeof v[x] === "function" && !/^[A-ZÇĞİÖŞÜ]/.test(x) ? sar(m, k + "." + x, v[x], v) : v[x];
      o[k] = ic;
    } else o[k] = v;
  }
  return o;
}
const sarilmis = new Map();
const asilYukle = Module._load;
Module._load = function (istek, ust, ana) {
  const r = asilYukle.apply(this, arguments);
  let dosya = null;
  try { dosya = Module._resolveFilename(istek, ust, ana); } catch (e) { dosya = null; }
  const ad = dosya && KAYITLI[dosya];
  if (!ad || !r || typeof r !== "object") return r;
  if (!sarilmis.has(dosya)) sarilmis.set(dosya, kaydeden(ad, r));
  return sarilmis.get(dosya);
};

// gerçek (kaydetmeyen) modüller: şablon üçlüleri ve yeniden oynatma
const ASIL = {};
for (const [dosya, ad] of Object.entries(KAYITLI)) ASIL[ad] = asilYukle(dosya, module, false);
ASIL.Op4Cekirdek = asilYukle(path.join(OP4, "js", "op4_cekirdek.js"), module, false);
ASIL.Op4Ops.bagimliliklarKur({ ModelOps: ASIL.ModelOps, MatrisAks: ASIL.MatrisAks, MatrisIFC: ASIL.MatrisIFC });

D.saatSabitle(globalThis);
const test = require("node:test");
for (const s of SINAMALAR) {
  // her sınama dosyası kendi kaynağıyla etiketlenir: dosyanın bütün sınamaları bitene dek (sırayla koşarlar)
  test.describe("derlem: " + s, { concurrency: false }, function () {
    test.before(function () { kaynak = s; });
    require(path.join(DEPO, s));
  });
}

// ---------------------------------------------------------------- şablon üçlüleri
function sablonUcluleri() {
  kaynak = "sablon";
  derinlik = 0;
  const zaman = "2026-10-30T12:00:00";
  const uygulama = { ad: "op4", surum: "0.1.0", firma: "Opus Fortis" };
  const ekle = function (m, f, args) {
    const fn = ASIL[m][f];
    let r, h = null;
    try { r = fn.apply(ASIL[m], args); } catch (e) { h = e; }
    kaydet(m, f, args, r, h);
  };
  for (const ad of SABLONLAR) {
    const T = () => JSON.parse(baglam.sablonlar[ad]);
    const S = SONUCLAR.includes(ad) ? () => JSON.parse(baglam.sonuclar[ad]) : null;
    ekle("Op4Ops", "sahneCikar", [T(), 1]);
    senaryo({ model: { $sablon: ad } }, "sayilar", { q: "node" });
    ekle("Op4Ops", "katUyeligi", [T()]);
    ekle("Op4Ops", "kullanimYeri", [T()]);
    ekle("Op4Ops", "oznitelikCikar", [T()]);
    if (S) ekle("Op4Ops", "sonucEsle", [T(), S()]);
    ekle("ModelOps", "genellestir", [T()]);
    const g = ASIL.ModelOps.genellestir(T()).model;
    ekle("ModelOps", "denetle", [g]);
    if (KUCUK_SABLONLAR.includes(ad)) ekle("Op4Ops", "sahneCikar", [g, 2]);
    ekle("MatrisBinaCizim", "genelGecisGerekli", [T()]);
    ekle("MatrisBinaCizim", "genelGecisMetni", [T(), "Genel modele dönüştür"]);
    if (KUCUK_SABLONLAR.includes(ad)) ekle("MatrisBinaCizim", "genellestirHazirla", [T()]);
    // IFC: küçük şablonlarda tam metin, ötekilerde metin özeti (uzunluk + FNV; birebir eşitlik)
    const kucuk = KUCUK_SABLONLAR.includes(ad);
    if (kucuk) ekle("MatrisIFC", "uretAyrintili", [T(), null, { zaman: zaman }]);
    else senaryo({ model: { $sablon: ad }, veri: null, secenek: { zaman: zaman } }, "ifc");
    if (S) senaryo({ model: { $sablon: ad }, veri: { $sonuc: ad }, secenek: { zaman: zaman, yukler: true, sonuclar: true } }, "ifc");
    // cephe senaryosu: yükle, oku, C1 geçişi, geri al / yinele, aks taşıma, başlık, IFC, sonuç eşleme
    const ak = JSON.parse(JSON.stringify(T().akslar));
    if (ak && Array.isArray(ak.x) && ak.x.length) ak.x[0].konum = +ak.x[0].konum - 0.5;
    // tam dökümler (sahne, öznitelik, IFC) bir kez; tekrarlarda metin özeti
    const adimlar = [
      ["yukle", { $sablonMetin: ad }, "sablon:" + ad], ["ozet"], ["metinOzeti"], ["oznitelikKodlu"], ["denetle"], ["geriAlBilgisi"],
      ["uygula", "genellestir", {}], ["uygula", "genellestir", { onay: true }], ["metin"], ["geriAl"], ["metinOzeti"], ["yinele"],
      ["geriAlBilgisi"], ["uygula", "aksSihirbazi", D.kodla({ akslar: ak })], ["sahne"], ["metinOzeti"], ["geriAl"],
      ["uygula", "baslikDegistir", { baslik: "Derlem " + ad }], ["ozet"],
      [kucuk ? "ifcDisari" : "ifcOzeti", { uygulama: uygulama, zaman: zaman }, null],
    ];
    if (S) adimlar.push(["sonucEsle", { $sonuc: ad }]);
    adimlar.push(["geriAlBilgisi"]);
    senaryo({ adimlar: adimlar }, "cephe");
  }
  // boş modelden hızlı aks, aks sihirbazı, tablo düzenleme, hatalar
  senaryo({ ayar: { geriAlAdim: 3 }, adimlar: [
    ["yeniBos", { baslik: "Adsız 1" }], ["sahne"], ["uygula", "hizliAks", { x: [6, 6], y: [5], z: [3.5, 3] }], ["sahne"],
    ["oznitelikler"], ["metin"], ["uygula", "hizliAks", { x: "3@6", y: [5, 5], z: [3], taban: -1 }], ["sahne"], ["metin"],
    ["uygula", "hizliAks", { x: [0], y: [5], z: [3] }], ["uygula", "hizliAks", {}], ["uygula", "yokBoyle", {}],
    ["uygula", "baslikDegistir", { baslik: "  " }], ["uygula", "baslikDegistir", { baslik: "Sınama" }],
    ["tabloUygula", [{ yol: ["baslik"], deger: "Tablo" }]], ["metin"], ["geriAlBilgisi"], ["geriAl"], ["geriAl"], ["geriAl"],
    ["geriAl"], ["yinele"], ["metin"], ["yukle", "{bozuk", "dosya:x.json"], ["yukle", "{\"tur\":\"matris\"}", "dosya:y.json"],
    ["denetle"], ["ifcDisari", { zaman: zaman }, null],
  ] }, "cephe");
}
function senaryo(girdi, tur, ek) {
  const kayit = Object.assign({ m: "$senaryo", f: tur, a: [girdi] }, ek || {});
  let r;
  try { r = D.calistir(ASIL, kayit, baglam); } catch (e) { throw new Error("cephe senaryosu çalışmadı: " + e.stack); }
  const k = Object.assign(kayit, r, { k: "sablon" });
  const metin = JSON.stringify(k);
  if (metin.length > 2 * SABLON_UCLU_SINIRI) { atlanan.buyuk++; return; }
  kayitlar.push(k);
}

// ---------------------------------------------------------------- doğrulama ve yazma
let yazildi = false;
process.on("beforeExit", function () {
  if (yazildi) return;
  yazildi = true;
  kayitAcik = false;
  sablonUcluleri();
  // yeniden oynatma: aynı çıktıyı vermeyen üçlü atılır
  const tutarli = [], atilan = {};
  for (const k of kayitlar) {
    let r;
    try { r = D.calistir(ASIL, k, baglam); } catch (e) { r = { hata: String(e) }; }
    const f = D.fark(k.s !== undefined ? { s: k.s } : { h: k.h }, r);
    if (f) { const a = k.m + "." + k.f; atilan[a] = (atilan[a] || 0) + 1; continue; }
    tutarli.push(k);
  }
  const ozet = {};
  for (const dosya of Object.keys(KAYITLI).concat([path.join(OP4, "js", "op4_cekirdek.js")]))
    ozet[path.relative(DEPO, dosya).split(path.sep).join("/")] = crypto.createHash("sha256").update(fs.readFileSync(dosya)).digest("hex");
  const sayim = {};
  for (const k of tutarli) sayim[k.m + "." + k.f] = (sayim[k.m + "." + k.f] || 0) + 1;
  const ust = { bicim: D.BICIM, uretici: "op4/testler/js/derlem_uret.js", node: process.version, sayi: tutarli.length,
    moduller: ozet, sablonlar: SABLONLAR, sonuclar: SONUCLAR, islevler: sayim };
  const satirlar = [JSON.stringify(ust)].concat(tutarli.map((k) => JSON.stringify(k)));
  const hedef = path.join(DERLEM, "derlem.jsonl");
  fs.writeFileSync(hedef, satirlar.join("\n") + "\n");
  process.stderr.write("derlem: " + tutarli.length + " üçlü, " + Object.keys(sayim).length + " işlev → " + path.relative(DEPO, hedef) +
    " (" + Math.round(fs.statSync(hedef).size / 1024) + " KB)\n" +
    "  atlanan: " + JSON.stringify(atlanan) + "\n  yeniden oynatmada farklı (atıldı): " + JSON.stringify(atilan) + "\n");
});
