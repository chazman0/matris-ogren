/* Masaüstü sürümünün saf kısımları (node --test; bağımlılık yok, masaüstü çatısı gerekmez):
   hazirla.js yardımcıları, motor worker'ının yerel Pyodide adresi, ön yükleme betiğinin açtığı yüzey (sahte çatı modülüyle),
   menü şablonu, ana süreç yardımcıları (dosya, son dosyalar, kurtarma, PDF bilgisi) ve uygulama dosyası sunucusu. */
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const vm = require("vm");
const Module = require("module");

const KOK = path.resolve(__dirname, "..", "..");
const MASAUSTU = path.join(KOK, "masaustu");
const DOCS = path.join(KOK, "docs");
const H = require(path.join(MASAUSTU, "hazirla.js"));
const Y = require(path.join(MASAUSTU, "lib", "yardimci.js"));
const S = require(path.join(MASAUSTU, "lib", "sunucu.js"));
const MENU = require(path.join(MASAUSTU, "lib", "menu.js"));

function geciciKlasor() { return fs.mkdtempSync(path.join(os.tmpdir(), "matris-masaustu-")); }

// ------------------------------------------------------------------ hazirla.js
test("hazirla: motorun Pyodide sürümü ve paketleri worker'dan okunur", function () {
  const metin = fs.readFileSync(path.join(DOCS, "motor.worker.js"), "utf8");
  assert.match(H.pyodideSurumu(metin), /^\d+\.\d+\.\d+$/);
  assert.deepEqual(H.yuklenenPaketler(metin), ["numpy", "sympy"]);
  assert.deepEqual(H.yuklenenPaketler('x.loadPackage("micropip"); y.loadPackage(["b", \'a\'])'), ["a", "b", "micropip"]);
  assert.throws(function () { H.pyodideSurumu("const X = 1;"); }, /PYODIDE_SURUM/);
  assert.throws(function () { H.yuklenenPaketler("nothing"); }, /loadPackage/);
});

test("hazirla: paket bağımlılıkları kilit dosyasından çözülür", function () {
  const kilit = { packages: {
    sympy: { name: "sympy", version: "1.14.0", file_name: "sympy-1.14.0-py3-none-any.whl", sha256: "AA", depends: ["mpmath"] },
    mpmath: { name: "mpmath", version: "1.4.1", file_name: "mpmath-1.4.1-py3-none-any.whl", sha256: "bb", depends: [] },
    numpy: { name: "numpy", version: "2.4.6", file_name: "numpy-2.4.6.whl", sha256: "cc", depends: [] },
    "typing-extensions": { name: "typing-extensions", version: "4", file_name: "te.whl", depends: [] },
    kotu: { name: "kotu", version: "1", file_name: "../kacis.whl", depends: [] },
    eksik: { name: "eksik", version: "1", file_name: "e.whl", depends: ["yok-boyle"] },
  } };
  const c = H.paketleriCoz(kilit, ["sympy", "numpy"]);
  assert.deepEqual(c.map(function (p) { return p.ad; }), ["mpmath", "numpy", "sympy"]);
  assert.equal(c.find(function (p) { return p.ad === "sympy"; }).sha256, "aa");
  assert.deepEqual(H.paketleriCoz(kilit, ["Typing_Extensions"]).map(function (p) { return p.ad; }), ["typing-extensions"]);
  assert.throws(function () { H.paketleriCoz(kilit, ["kotu"]); }, /Geçersiz paket dosya adı/);
  assert.throws(function () { H.paketleriCoz(kilit, ["eksik"]); }, /yok-boyle.*eksik gerektiriyor/);
});

test("hazirla: CDN kütüphaneleri bulunur, yerel adrese çevrilir; sabitlenmemiş adres reddedilir", function () {
  const html = fs.readFileSync(path.join(DOCS, "index.html"), "utf8");
  const a = H.cdnAdresleri(html);
  const yollar = a.map(function (x) { return x.yol; });
  assert.ok(yollar.some(function (y) { return /^katex@[\d.]+\/dist\/katex\.min\.css$/.test(y); }), yollar);
  assert.ok(yollar.some(function (y) { return /^katex@[\d.]+\/dist\/katex\.min\.js$/.test(y); }), yollar);
  assert.ok(yollar.some(function (y) { return /^marked@[\d.]+\//.test(y); }), yollar);
  const yeni = H.htmlYerellestir(html, a);
  assert.ok(yeni.indexOf("cdn.jsdelivr.net") < 0);
  assert.ok(yeni.indexOf('href="kutuphane/katex@') >= 0);
  assert.throws(function () { H.cdnAdresleri('<script src="https://cdn.jsdelivr.net/npm/katex/dist/katex.js">'); }, /sabitlenmemiş/);
  assert.throws(function () { H.cdnAdresleri('<script src="https://cdn.jsdelivr.net/npm/a@1.0/../../x.js">'); });
  assert.deepEqual(H.cssYaziTipleri("@font-face{src:url(fonts/A.woff2) format('woff2'),url(fonts/A.woff) format('woff')}" +
    "@font-face{src:url('fonts/B.woff2')}x{background:url(data:x.woff2)}y{src:url(https://e.com/c.woff2)}z{src:url(../d.woff2)}"),
  ["fonts/A.woff2", "fonts/B.woff2"]);
});

test("hazirla: dosya listesi atlanacak adları içermez", function () {
  const k = geciciKlasor();
  fs.mkdirSync(path.join(k, "a", "__pycache__"), { recursive: true });
  fs.writeFileSync(path.join(k, "a", "b.js"), "x");
  fs.writeFileSync(path.join(k, "a", "__pycache__", "c.pyc"), "x");
  fs.writeFileSync(path.join(k, "Thumbs.db"), "x");
  fs.writeFileSync(path.join(k, "z.txt"), "x");
  assert.deepEqual(H.dosyaListesi(k), ["a/b.js", "z.txt"]);
});

// ------------------------------------------------------------------ motor worker: Pyodide adresi
function workerAdresi(kaynak, workerUrl, onAyar) {
  const self = Object.assign({ location: { href: workerUrl }, postMessage: function () {} }, onAyar || {});
  const ctx = vm.createContext({ self: self, URL: URL, console: console });
  vm.runInContext(kaynak, ctx, { filename: "motor.worker.js" });
  return vm.runInContext("PYODIDE_URL", ctx);
}

test("worker: web'de CDN, yerel adres yalnız MATRIS_PYODIDE_URL ya da aynı kökenden sorgu ile", function () {
  const kaynak = fs.readFileSync(path.join(DOCS, "motor.worker.js"), "utf8");
  const surum = H.pyodideSurumu(kaynak);
  const cdn = "https://cdn.jsdelivr.net/pyodide/v" + surum + "/full/";
  assert.equal(workerAdresi(kaynak, "https://chazman0.github.io/matris-ogren/motor.worker.js"), cdn);
  assert.equal(workerAdresi(kaynak, "https://x.org/a/motor.worker.js", { MATRIS_PYODIDE_URL: "./pyodide" }), "https://x.org/a/pyodide/");
  assert.equal(workerAdresi(kaynak, "app://matris/motor.worker.js", { MATRIS_PYODIDE_URL: "./pyodide/" }), "app://matris/pyodide/");
  assert.equal(workerAdresi(kaynak, "http://127.0.0.1:8000/motor.worker.js?pyodide=/yerel/pyodide/"), "http://127.0.0.1:8000/yerel/pyodide/");
  // başka kökene yönlendirme sorgu ile yapılamaz
  assert.equal(workerAdresi(kaynak, "https://x.org/motor.worker.js?pyodide=https://kotu.example/p/"), cdn);
  // hazirla.js'in kopyaya eklediği satır yerel kopyayı seçer
  const kopya = H.workerYerellestir(kaynak, H.YEREL_PYODIDE);
  assert.equal(workerAdresi(kopya, "app://matris/motor.worker.js"), "app://matris/pyodide/");
  assert.ok(kopya.indexOf('"use strict";\nself.MATRIS_PYODIDE_URL = "./pyodide/";') >= 0);
  assert.throws(function () { H.workerYerellestir('"use strict";\nconst PYODIDE_URL = "x";', "./p/"); }, /desteklemiyor/);
});

// ------------------------------------------------------------------ ön yükleme betiği (sahte çatı modülüyle)
function preloadYukle(argv) {
  const kayit = { acilan: {}, invoke: [], send: [], on: {}, kaldirilan: [], pencere: {} };
  const sahte = {
    contextBridge: { exposeInMainWorld: function (ad, deger) { kayit.acilan[ad] = deger; } },
    ipcRenderer: {
      invoke: function (kanal, veri) { kayit.invoke.push([kanal, veri]); return Promise.resolve({ kanal: kanal }); },
      send: function (kanal, veri) { kayit.send.push([kanal, veri]); },
      on: function (kanal, h) { (kayit.on[kanal] = kayit.on[kanal] || []).push(h); },
      removeListener: function (kanal, h) { kayit.kaldirilan.push(kanal); kayit.on[kanal] = (kayit.on[kanal] || []).filter(function (x) { return x !== h; }); },
    },
    webUtils: { getPathForFile: function (f) { return f.yol || ""; } },
  };
  const eskiYukle = Module._load;
  const eskiPencere = global.window;
  const eskiArgv = process.argv;
  global.window = { addEventListener: function (ad, fn) { kayit.pencere[ad] = fn; } };
  process.argv = eskiArgv.concat(argv || []);
  Module._load = function (istek) { if (istek === "electron") return sahte; return eskiYukle.apply(this, arguments); };
  try {
    const yol = path.join(MASAUSTU, "preload.js");
    delete require.cache[require.resolve(yol)];
    require(yol);
  } finally {
    Module._load = eskiYukle;
    global.window = eskiPencere;
    process.argv = eskiArgv;
  }
  return kayit;
}

test("preload: yalnız dar ve dondurulmuş window.masaustu yüzeyi açılır", function () {
  const k = preloadYukle(["--matris-surum=1.2.3"]);
  assert.deepEqual(Object.keys(k.acilan), ["masaustu"]);
  const m = k.acilan.masaustu;
  assert.ok(Object.isFrozen(m));
  assert.deepEqual(Object.keys(m).sort(), ["ac", "degisti", "dosyaDinle", "harici", "hazir", "kaydet", "klasordeGoster", "komutDinle",
    "otomatikKayit", "pdfYazdir", "platform", "projeAc", "projeKaydet", "surum", "tamEkran", "yeni", "yeniPencere"]);
  assert.equal(m.surum, "1.2.3");
  assert.equal(m.platform, process.platform);
  assert.equal(preloadYukle([]).acilan.masaustu.surum, "0.0.0");
});

test("preload: kaydet/aç/proje/PDF istekleri normalleştirilir", async function () {
  const k = preloadYukle([]);
  const m = k.acilan.masaustu;
  await m.kaydet({ ad: "model.ifc", icerik: "ISO", filtreler: [{ ad: "IFC", uzantilar: ["ifc"] }, null], baslik: "Dışa aktar" });
  await m.kaydet({ ad: 5, icerik: new Uint8Array([1, 2, 3]).buffer });
  await m.kaydet({ icerik: new Uint8Array([9, 8, 7, 6]).subarray(1, 3) });
  await m.kaydet();
  await m.ac({ filtreler: [{ ad: "CSV", uzantilar: ["csv"] }], ikili: 1 });
  await m.projeKaydet({ ad: "p.matris", icerik: { toString: function () { return "{}"; } }, farkli: "evet" });
  await m.projeAc();
  await m.pdfYazdir({ html: "<h1>R</h1>" });
  const inv = k.invoke;
  assert.deepEqual(inv.map(function (x) { return x[0]; }), ["matris:kaydet", "matris:kaydet", "matris:kaydet", "matris:kaydet", "matris:ac",
    "matris:proje-kaydet", "matris:proje-ac", "matris:pdf"]);
  assert.deepEqual(inv[0][1], { ad: "model.ifc", icerik: "ISO", filtreler: [{ ad: "IFC", uzantilar: ["ifc"] }, { ad: "", uzantilar: [] }], baslik: "Dışa aktar" });
  assert.equal(inv[1][1].ad, "5");
  assert.ok(inv[1][1].icerik instanceof Uint8Array);
  assert.deepEqual(Array.from(inv[1][1].icerik), [1, 2, 3]);
  assert.deepEqual(Array.from(inv[2][1].icerik), [8, 7]);
  assert.deepEqual(inv[3][1], { ad: "", icerik: "", filtreler: [], baslik: "" });
  assert.deepEqual(inv[4][1], { filtreler: [{ ad: "CSV", uzantilar: ["csv"] }], ikili: true, baslik: "" });
  assert.deepEqual(inv[5][1], { ad: "p.matris", icerik: "{}", farkli: true });
  assert.deepEqual(inv[7][1], { html: "<h1>R</h1>", ad: "rapor" });
});

test("preload: pencere iletileri ve dinleyiciler", function () {
  const k = preloadYukle([]);
  const m = k.acilan.masaustu;
  m.degisti(1); m.yeni(); m.otomatikKayit(null, null); m.otomatikKayit("{}", "a.matris"); m.hazir(); m.tamEkran(); m.yeniPencere();
  m.harici("https://e.com"); m.klasordeGoster("/x/y.ifc");
  assert.deepEqual(k.send, [["matris:kirli", true], ["matris:yeni", undefined], ["matris:otomatik-kayit", { icerik: "", ad: "" }],
    ["matris:otomatik-kayit", { icerik: "{}", ad: "a.matris" }], ["matris:hazir", undefined], ["matris:tam-ekran", undefined],
    ["matris:yeni-pencere", undefined], ["matris:harici", "https://e.com"], ["matris:klasorde-goster", "/x/y.ifc"]]);
  const gelen = [];
  const birak = m.komutDinle(function (v) { gelen.push(v); });
  m.dosyaDinle(function (v) { gelen.push(v); });
  k.on["matris:komut"][0]({ sender: "x" }, { komut: "coz" });
  k.on["matris:dosya-acildi"][0]({}, { ad: "a.matris", icerik: "{}" });
  assert.deepEqual(gelen, [{ komut: "coz" }, { ad: "a.matris", icerik: "{}" }]);
  birak();
  assert.deepEqual(k.kaldirilan, ["matris:komut"]);
  assert.equal(k.on["matris:komut"].length, 0);
  assert.throws(function () { m.komutDinle("işlev değil"); }, TypeError);
});

function olay(secenek) {
  const o = Object.assign({ isTrusted: true, defaultPrevented: false, dataTransfer: { types: ["Files"], files: [], dropEffect: "none" } }, secenek || {});
  o.preventDefault = function () { o.defaultPrevented = true; };
  return o;
}

test("preload: sürükle-bırak yalnız gerçek bırakmalarda ve proje dosyalarında çalışır", function () {
  const k = preloadYukle([]);
  const uzerinde = olay();
  k.pencere.dragover(uzerinde);
  assert.ok(uzerinde.defaultPrevented);
  assert.equal(uzerinde.dataTransfer.dropEffect, "copy");
  const metin = olay({ dataTransfer: { types: ["text/plain"], files: [] } });
  k.pencere.dragover(metin);
  assert.ok(!metin.defaultPrevented);

  const dosyalar = [{ name: "a.matris", yol: "/p/a.matris" }, { name: "b.JSON", yol: "/p/b.JSON" }, { name: "c.txt", yol: "/p/c.txt" }, { name: "d.matris", yol: "" }];
  const birak = olay({ dataTransfer: { types: ["Files"], files: dosyalar } });
  k.pencere.drop(birak);
  assert.ok(birak.defaultPrevented);
  assert.deepEqual(k.send, [["matris:birakilan", ["/p/a.matris", "/p/b.JSON"]]]);

  const sahte = olay({ isTrusted: false, dataTransfer: { types: ["Files"], files: dosyalar } });
  k.pencere.drop(sahte);
  assert.ok(sahte.defaultPrevented);           // dosyaya "gitme" yine engellenir
  const islenmis = olay({ defaultPrevented: true, dataTransfer: { types: ["Files"], files: dosyalar } });
  k.pencere.drop(islenmis);
  const yalnizMetin = olay({ dataTransfer: { types: ["Files"], files: [{ name: "x.txt", yol: "/x.txt" }] } });
  k.pencere.drop(yalnizMetin);
  assert.equal(k.send.length, 1);
});

// ------------------------------------------------------------------ menü
function etiketler(ogeler, cikti) {
  (ogeler || []).forEach(function (o) { if (o.label) cikti.push(o.label); etiketler(o.submenu, cikti); });
  return cikti;
}

test("menü: Türkçe ana menüler, kısayollar ve komut bağlantısı", function () {
  ["linux", "win32"].forEach(function (p) {
    const s = MENU.menuSablonu({ platform: p, komut: function () {}, yerel: {} });
    assert.deepEqual(s.map(function (m) { return m.label.replace(/&/g, ""); }),
      ["Dosya", "Düzen", "Görünüm", "Çizim", "Aks", "Analiz", "Tasarım", "Rapor", "Yardım"]);
  });
  const mac = MENU.menuSablonu({ platform: "darwin", uygulamaAdi: "Matris Öğren", komut: function () {}, yerel: {} });
  assert.equal(mac[0].label, "Matris Öğren");
  assert.equal(mac[mac.length - 1].role, "windowMenu");

  ["linux", "win32", "darwin"].forEach(function (p) {
    const liste = MENU.komutListesi(p);
    const kisayol = {};
    liste.forEach(function (k) { if (k.kisayol) { assert.ok(!kisayol[k.kisayol], p + " yinelenen kısayol " + k.kisayol); kisayol[k.kisayol] = k; } });
    assert.equal(kisayol["CmdOrCtrl+S"].komut, "kaydet");
    assert.equal(kisayol["CmdOrCtrl+N"].komut, "yeni");
    assert.equal(kisayol["CmdOrCtrl+Z"].komut, "geri-al");
    assert.equal(kisayol[p === "darwin" ? "Shift+Cmd+Z" : "Ctrl+Y"].komut, "yinele");
    assert.equal(kisayol.F5.komut, "coz");
    ["Delete", "Esc", "PageUp", "PageDown"].forEach(function (t) { assert.ok(kisayol[t].sayfaTusu, t); });
    assert.equal(kisayol["CmdOrCtrl+Z"].sayfaTusu, p !== "darwin");
    // tek harfli (değiştiricisiz) kısayol yok: metin kutularına yazmayı bozmasın
    Object.keys(kisayol).forEach(function (h) { assert.ok(!/^[A-Za-z0-9]$/.test(h), h); });
  });
  const hepsi = MENU.menuSablonu({ platform: "linux", komut: function () {}, yerel: {}, sonDosyalar: ["/a/b&c.matris"] });
  const dosya = hepsi[0].submenu;
  assert.equal(dosya.find(function (o) { return o.id === "ac"; }).accelerator, "CmdOrCtrl+O");
  const son = dosya.find(function (o) { return o.id === "son-dosyalar"; }).submenu;
  assert.equal(son[0].label, "&1  /a/b&&c.matris");
  const gorunum = hepsi[2].submenu;
  assert.equal(gorunum.find(function (o) { return o.id === "tam-ekran"; }).accelerator, "F11");
  etiketler(MENU.menuSablonu({ platform: "darwin", komut: function () {}, yerel: {} }), []).concat(etiketler(hepsi, [])).forEach(function (e) {
    assert.ok(!/electron|chromium/i.test(e), e);
  });
});

test("menü: tıklama komutu pencereyle iletir; yerel işler çağrılır", function () {
  const gelen = [];
  const yerel = {};
  ["ac", "yeniPencere", "sonDosyaAc", "sonDosyalariTemizle", "kurtarmaKlasoru", "tamEkran", "kisayollar", "harici", "hakkinda"].forEach(function (ad) {
    yerel[ad] = function () { gelen.push([ad].concat(Array.from(arguments))); };
  });
  const s = MENU.menuSablonu({ platform: "linux", komut: function (ad, ek, p) { gelen.push(["komut", ad, ek, p]); }, yerel: yerel, sonDosyalar: ["/x.matris"] });
  const bul = function (id) {
    let sonuc = null;
    const gez = function (o) { o.forEach(function (x) { if (x.id === id) sonuc = x; if (x.submenu) gez(x.submenu); }); };
    gez(s);
    return sonuc;
  };
  bul("komut:kaydet").click(null, "P1");
  bul("komut:sayfa:bina").click(null, "P2");
  bul("ac").click(null, "P3");
  bul("son-dosyalar").submenu[0].click(null, "P4");
  bul("tam-ekran").click(null, "P5");
  assert.deepEqual(gelen, [["komut", "kaydet", null, "P1"], ["komut", "sayfa", { sayfa: "bina" }, "P2"], ["ac", "P3"], ["sonDosyaAc", "/x.matris", "P4"], ["tamEkran", "P5"]]);
  const metin = MENU.kisayolMetni("win32");
  assert.match(metin, /Ctrl\+S {2}— {2}Kaydet/);
  assert.match(metin, /F11 {2}— {2}Tam ekran/);
  assert.match(MENU.kisayolMetni("darwin"), /⌘S/);
  // menü kısayolları penceresi Bina sayfasının araç kısayollarına (komut kaydından üretilen listeler) yönlendirir
  assert.match(metin, /\n\nBina sayfasındaki araç kısayolları .*Klavye kısayolları kartı ya da Bina sayfasında \? tuşu\.$/);
});

// README "Komutlar" tablosu: | `komut` | ek alanlar | Menü | Kısayol | (dipnot işaretleri ¹ ² ³ ⁴ sayılmaz)
function readmeKomutlari() {
  const metin = fs.readFileSync(path.join(MASAUSTU, "README.md"), "utf8");
  const bas = metin.indexOf("### Komutlar\n");
  assert.ok(bas >= 0, "masaustu/README.md: ### Komutlar bölümü yok");
  const bolum = metin.slice(bas, metin.indexOf("\n### ", bas + 10));
  const satirlar = [];
  bolum.split("\n").forEach(function (s) {
    const m = /^\| `([a-z0-9-]+)` \|([^|]*)\|([^|]*)\|([^|]*)\|$/.exec(s);
    if (!m || m[1] === "komut") return;
    const ek = /sayfa: "([a-z]+)"/.exec(m[2]);
    satirlar.push({ komut: m[1], sayfa: ek ? ek[1] : null, menu: m[3].replace(/[¹²³⁴⁵]/g, "").trim(),
      kisayol: m[4].replace(/[`¹]/g, "").trim(), sayfaTusu: m[4].indexOf("¹") >= 0 });
  });
  return satirlar;
}

test("menü: README Komutlar tablosu komut listesiyle birebir (iki yönlü)", function () {
  const tablo = readmeKomutlari();
  const beklenen = MENU.komutListesi("linux").map(function (k) {
    return { komut: k.komut, sayfa: k.ek ? k.ek.sayfa : null, menu: k.menu + " › " + k.etiket,
      kisayol: String(k.kisayol || "").replace("CmdOrCtrl", "Ctrl"), sayfaTusu: !!k.sayfaTusu };
  });
  assert.ok(beklenen.length > 100, "komut listesi beklenenden kısa: " + beklenen.length);
  // sıra da aynı: tablo menü sırasını izler; eksik ya da fazla satır, yanlış etiket / kısayol farkı burada görünür
  assert.deepEqual(tablo, beklenen);
  // kimlik kümeleri her platformda eşit (macOS uygulama menüsünde yalnız "ayarlar" yinelenir)
  const kume = function (l) { return Array.from(new Set(l.map(function (k) { return k.komut; }))).sort(); };
  ["linux", "win32", "darwin"].forEach(function (p) { assert.deepEqual(kume(MENU.komutListesi(p)), kume(tablo), p); });
  // dosyadan CSV içe aktarma yok: İçe aktar menüsünde tablo öğesi yok, tablolar yapıştırmayla (Analiz › Tablolar)
  assert.ok(!tablo.some(function (k) { return k.komut === "csv-iceri"; }));
  const dosya = MENU.menuSablonu({ platform: "linux", komut: function () {}, yerel: {} })[0].submenu;
  const iceri = dosya.find(function (o) { return o.label === "İçe aktar"; }).submenu;
  assert.deepEqual(iceri.map(function (o) { return o.id; }), ["komut:json-iceri"]);
  assert.ok(tablo.some(function (k) { return k.komut === "tablolar" && /yapıştır/.test(k.menu) && k.kisayol === "Ctrl+T"; }));
});

// ------------------------------------------------------------------ ana süreç yardımcıları
test("yardımcı: .matris kaydet/aç gidiş-dönüş (atomik yazma, BOM, uzantı ve boyut denetimi)", function () {
  const k = geciciKlasor();
  const yol = path.join(k, "alt klasör", "Proje ğüş.matris");
  const icerik = JSON.stringify({ surum: 3, tur: "bina", ad: "Çelik depo", akslar: { x: [{ ad: "A", konum: 0 }] } });
  assert.equal(Y.atomikYaz(yol, icerik), Buffer.byteLength(icerik));
  assert.deepEqual(Y.projeOku(yol), { ad: "Proje ğüş.matris", yol: yol, icerik: icerik });
  fs.writeFileSync(yol, "﻿" + icerik, "utf8");
  assert.equal(Y.projeOku(yol).icerik, icerik);
  Y.atomikYaz(yol, Buffer.from("ikinci"));
  assert.equal(fs.readFileSync(yol, "utf8"), "ikinci");
  assert.deepEqual(fs.readdirSync(path.dirname(yol)), ["Proje ğüş.matris"]);   // geçici dosya kalmaz
  fs.writeFileSync(path.join(k, "x.txt"), "{}");
  assert.throws(function () { Y.projeOku(path.join(k, "x.txt")); }, /Yalnız \.matris ve \.json/);
  assert.throws(function () { Y.projeOku(path.join(k, "yok.matris")); });
  assert.ok(Y.projeDosyasiMi("a.MATRIS") && Y.projeDosyasiMi("b.json") && !Y.projeDosyasiMi("c.ifc") && !Y.projeDosyasiMi(null));
});

test("yardımcı: ayar deposu, son dosyalar, komut satırı, pencere sınırı", async function () {
  const k = geciciKlasor();
  const dosya = path.join(k, "ayarlar.json");
  fs.writeFileSync(dosya, "{bozuk");
  const d = Y.depo(dosya, { sonDosyalar: [], a: 1 });
  assert.equal(d.al("a"), 1);
  d.koy("a", 2);
  d.kaydetSimdi();
  assert.equal(JSON.parse(fs.readFileSync(dosya, "utf8")).a, 2);
  assert.equal(Y.depo(dosya, { a: 1 }).al("a"), 2);

  let liste = [];
  for (let i = 0; i < 12; i++) liste = Y.sonDosyaEkle(liste, path.join(k, "p" + i + ".matris"), 10);
  assert.equal(liste.length, 10);
  assert.equal(liste[0], path.join(k, "p11.matris"));
  liste = Y.sonDosyaEkle(liste, path.join(k, "p5.matris"), 10);
  assert.equal(liste[0], path.join(k, "p5.matris"));
  assert.equal(liste.filter(function (y) { return y === path.join(k, "p5.matris"); }).length, 1);

  fs.writeFileSync(path.join(k, "var.matris"), "{}");
  fs.writeFileSync(path.join(k, "var.json"), "{}");
  fs.writeFileSync(path.join(k, "resim.png"), "");
  assert.deepEqual(Y.dosyaArgumanlari(["/uygulama/MatrisOgren", "--no-sandbox", ".", "var.matris", "yok.matris", "resim.png", path.join(k, "var.json")], k),
    [path.join(k, "var.matris"), path.join(k, "var.json")]);

  const ekran = [{ x: 0, y: 0, width: 1920, height: 1040 }];
  assert.deepEqual(Y.pencereSiniri({ x: 100, y: 50, width: 1200, height: 800 }, ekran), { x: 100, y: 50, width: 1200, height: 800 });
  assert.deepEqual(Y.pencereSiniri({ x: 5000, y: 50, width: 1200, height: 800 }, ekran), { width: 1200, height: 800 });
  assert.deepEqual(Y.pencereSiniri(null, ekran, { width: 1440, height: 920 }), { width: 1440, height: 920 });
  assert.deepEqual(Y.pencereSiniri({ x: 0, y: 0, width: 50, height: 50 }, ekran), { width: 1400, height: 900 });
});

test("yardımcı: otomatik kayıt ve kurtarma kayıtları", function () {
  const k = path.join(geciciKlasor(), "kurtarma");
  const R = Y.kurtarma(k);
  R.yaz("eski", 1, { ad: "a.matris", yol: "/x/a.matris", icerik: "{\"a\":1}" });
  R.yaz("eski", 2, { ad: null, icerik: "{\"b\":2}" });
  R.yaz("simdi", 1, { ad: "c.matris", icerik: "{}" });
  fs.writeFileSync(path.join(k, "bozuk-1.json"), "{x");
  fs.writeFileSync(path.join(k, "bos-1.json"), JSON.stringify({ icerik: "" }));
  assert.equal(R.oku("eski", 1).icerik, "{\"a\":1}");
  assert.equal(R.oku("eski", 1).surum, 1);
  const artik = R.artiklar("simdi");
  assert.deepEqual(artik.map(function (a) { return a.icerik; }).sort(), ["{\"a\":1}", "{\"b\":2}"]);
  assert.ok(!fs.existsSync(path.join(k, "bozuk-1.json")) && !fs.existsSync(path.join(k, "bos-1.json")));
  R.at(artik[0]);
  assert.equal(R.artiklar("simdi").length, 1);
  R.sil("simdi", 1);
  assert.equal(R.oku("simdi", 1), null);
  assert.deepEqual(Y.kurtarma(path.join(k, "yok")).artiklar("x"), []);
});

test("yardımcı: iletişim kutusu süzgeçleri, güvenli ad, rapor başlığı, PDF üretici bilgisi", function () {
  assert.deepEqual(Y.suzgecler([{ ad: "IFC", uzantilar: [".ifc"] }, { ad: "kötü", uzantilar: ["a/b", "çok-uzun-uzanti-x"] }, null]),
    [{ name: "IFC", extensions: ["ifc"] }, { name: "Tüm dosyalar", extensions: ["*"] }]);
  assert.deepEqual(Y.suzgecler([]), [{ name: "Tüm dosyalar", extensions: ["*"] }]);
  assert.equal(Y.guvenliAd('a/b:c*?"<>|.matris'), "a_b_c_.matris");
  assert.equal(Y.guvenliAd("..gizli"), "gizli");
  assert.equal(Y.guvenliAd("", "proje"), "proje");

  assert.match(Y.htmlBasligiEkle("<html><head><style></style></head><body></body></html>", "Rapor <1>"), /<head><title>Rapor &lt;1&gt;<\/title><style>/);
  assert.equal(Y.htmlBasligiEkle("<html><head><title>Var</title></head></html>", "X"), "<html><head><title>Var</title></head></html>");
  assert.match(Y.htmlBasligiEkle("<p>x</p>", "R"), /^<!DOCTYPE html><html><head><meta charset="utf-8"><title>R<\/title><\/head><body><p>x<\/p>/);

  const pdf = "%PDF-1.4\n1 0 obj\n<</Title (Rapor)\n/Creator (Tarayici)\n/Producer (Motor/PDF m1)\n/CreationDate (D:2026)>>\nendobj\n" +
    "2 0 obj\n<</Type /Catalog>>\nendobj\nxref\n0 3\ntrailer\n<</Size 3\n/Root 2 0 R\n/Info 1 0 R>>\nstartxref\n0\n%%EOF\n";
  const temiz = Y.pdfUreticiBilgisiniSil(Buffer.from(pdf, "latin1")).toString("latin1");
  assert.equal(temiz.length, pdf.length);
  assert.ok(temiz.indexOf("/Creator") < 0 && temiz.indexOf("/Producer") < 0 && temiz.indexOf("/Title (Rapor)") > 0);
  assert.equal(temiz.indexOf("2 0 obj"), pdf.indexOf("2 0 obj"));
  const bilgisiz = Buffer.from("%PDF-1.4\n/Creator (x)\n", "latin1");
  assert.equal(Y.pdfUreticiBilgisiniSil(bilgisiz).toString("latin1"), "%PDF-1.4\n/Creator (x)\n");
});

// ------------------------------------------------------------------ uygulama dosyası sunucusu (app:// ve önizleme)
test("sunucu: yol çözümü kökten çıkamaz; içerik türleri; CSP satır içi betik özetleri", async function () {
  const k = geciciKlasor();
  fs.mkdirSync(path.join(k, "pyodide"));
  fs.writeFileSync(path.join(k, "index.html"), "<!doctype html><script>var a=1;</script><script src=x.js></script><p>ğ</p>");
  fs.writeFileSync(path.join(k, "pyodide", "pyodide.asm.wasm"), Buffer.from([0, 0x61, 0x73, 0x6d]));
  fs.writeFileSync(path.join(k, "pyodide", "pyodide.mjs"), "export {}");
  fs.writeFileSync(path.join(path.dirname(k), "gizli-" + path.basename(k) + ".txt"), "gizli");
  assert.equal(S.yolCozumle(k, "/"), path.join(k, "index.html"));
  assert.equal(S.yolCozumle(k, "/pyodide/pyodide.mjs?v=1#x"), path.join(k, "pyodide", "pyodide.mjs"));
  assert.equal(S.yolCozumle(k, "/../gizli.txt"), path.join(k, "gizli.txt"));    // normalleşir, kökte kalır
  assert.equal(S.yolCozumle(k, "/%2e%2e/%2e%2e/etc/passwd"), path.join(k, "etc", "passwd"));
  assert.equal(S.yolCozumle(k, "/a%00b"), null);
  assert.equal(S.yolCozumle(k, "/%E0%A4%A"), null);
  assert.equal(S.icerikTuru("a.wasm"), "application/wasm");
  assert.match(S.icerikTuru("a.mjs"), /^text\/javascript/);
  assert.equal(S.icerikTuru("a.whl"), "application/zip");
  assert.equal(S.icerikTuru("a.bilinmez"), "application/octet-stream");
  assert.deepEqual(S.satirIciBetikOzetleri('<script>var a=1;</script><script type="application/json">{}</script><script src="b.js"></script>'),
    ["'sha256-" + require("crypto").createHash("sha256").update("var a=1;").digest("base64") + "'"]);

  const y = await S.yanitUret(k, "app://matris/index.html");
  assert.equal(y.durum, 200);
  assert.match(y.basliklar["Content-Type"], /^text\/html/);
  assert.match(y.basliklar["Content-Security-Policy"], /default-src 'self'/);
  assert.match(y.basliklar["Content-Security-Policy"], /'wasm-unsafe-eval'/);
  assert.match(y.basliklar["Content-Security-Policy"], /'sha256-/);
  assert.doesNotMatch(y.basliklar["Content-Security-Policy"], /[ ']'unsafe-eval'|https?:/);
  const w = await S.yanitUret(k, "app://matris/pyodide/pyodide.asm.wasm");
  assert.equal(w.basliklar["Content-Type"], "application/wasm");
  assert.equal(w.basliklar["Content-Security-Policy"], undefined);
  assert.equal((await S.yanitUret(k, "app://matris/yok.js")).durum, 404);
  assert.equal((await S.yanitUret(k, "app://matris/pyodide")).durum, 404);
  assert.equal((await S.yanitUret(k, "app://matris/a%00")).durum, 403);
  assert.equal((await S.yanitUret(k, "::adres değil")).durum, 400);
});
