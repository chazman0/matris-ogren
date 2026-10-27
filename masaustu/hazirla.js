#!/usr/bin/env node
/* Matris Öğren masaüstü — hazırlık betiği.

   Web uygulaması (../docs) masaüstü sürümünün TEK kaynağıdır. Bu betik:
     1. ../docs içeriğini eksiksiz olarak uygulama/ klasörüne kopyalar,
     2. hesap motorunun (docs/motor.worker.js) kullandığı Pyodide sürümünü (PYODIDE_SURUM) ve yüklediği paketleri
        (loadPackage([...])) okur; paketlerin bağımlılıklarını Pyodide kilit dosyasından (pyodide-lock.json) çözer;
        çekirdek dosyaları ve paket tekerleklerini indirip (SHA-256 denetimiyle) uygulama/pyodide/ altına koyar,
     3. HTML sayfalarının CDN'den aldığı kütüphaneleri (formül dizgisi ve markdown) uygulama/kutuphane/ altına indirip
        sayfalardaki adresleri yerel adreslerle değiştirir,
     4. kopyadaki motor.worker.js'e yerel Pyodide adresini (self.MATRIS_PYODIDE_URL) ekler,
     5. uygulama/masaustu.json bilgi dosyasını ve paketleyicinin kullandığı build/icon.png simgesini yazar.
   Sonuç: uygulama/ klasörü ağ bağlantısı olmadan tam çalışır. İndirilenler .onbellek/ altında saklanır; sürüm
   değişmedikçe yeniden indirilmez.

   Kullanım:
     node hazirla.js                         hazırla (varsayılan çıktı: uygulama/, önbellek: .onbellek/)
     node hazirla.js --cikti DIZIN           başka klasöre hazırla
     node hazirla.js --onbellek DIZIN        başka önbellek klasörü
     node hazirla.js --ag-yok                hiçbir şey indirme; yalnız önbellekte olanı kullan
     node hazirla.js --sunucu [--port 8765]  hazırlanmış klasörü masaüstü sürümündeki başlıklarla (CSP dahil) yerelde sun
   Çıkış kodları: 0 başarılı, 1 hata, 3 ağ hatası (indirme yapılamadı). */
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");

const BURASI = __dirname;
const DOCS = path.resolve(BURASI, "..", "docs");
const VARSAYILAN_CIKTI = path.join(BURASI, "uygulama");
const VARSAYILAN_ONBELLEK = path.join(BURASI, ".onbellek");
const SIMGE_HEDEF = path.join(BURASI, "build", "icon.png");
const CDN = "https://cdn.jsdelivr.net/";
const CDN_NPM = CDN + "npm/";
const ATLANAN = new Set([".DS_Store", "Thumbs.db", "desktop.ini", "__pycache__", ".ipynb_checkpoints"]);
// Pyodide çekirdeği: ESM yükleyici, derlenmiş çalışma zamanı, standart kütüphane, paket kilit dosyası.
const PYODIDE_CEKIRDEK = ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"];
const AG_HATASI_KODU = 3;
const YEREL_PYODIDE = "./pyodide/";

class AgHatasi extends Error {
  constructor(mesaj) { super(mesaj); this.name = "AgHatasi"; }
}

// ---------------------------------------------------------------- saf yardımcılar (testler doğrudan çağırır)

// docs/motor.worker.js → "314.0.7"
function pyodideSurumu(workerMetni) {
  const m = /const\s+PYODIDE_SURUM\s*=\s*["']([0-9][0-9A-Za-z.+-]*)["']/.exec(String(workerMetni || ""));
  if (!m) throw new Error("motor.worker.js içinde PYODIDE_SURUM bulunamadı.");
  return m[1];
}

// Motorun yüklediği paketler: loadPackage(["sympy", "numpy"]) ve loadPackage("x") çağrıları → sıralı, tekrarsız.
function yuklenenPaketler(workerMetni) {
  const metin = String(workerMetni || "");
  const adlar = new Set();
  const dizi = /loadPackage\(\s*\[([^\]]*)\]/g;
  let m;
  while ((m = dizi.exec(metin)) !== null) {
    m[1].replace(/["']([A-Za-z0-9_.-]+)["']/g, function (_t, ad) { adlar.add(ad); return ""; });
  }
  const tek = /loadPackage\(\s*["']([A-Za-z0-9_.-]+)["']/g;
  while ((m = tek.exec(metin)) !== null) adlar.add(m[1]);
  if (!adlar.size) throw new Error("motor.worker.js içinde loadPackage(...) çağrısı bulunamadı.");
  return Array.from(adlar).sort();
}

function paketAdiNormal(ad) {
  return String(ad).toLowerCase().replace(/[_.]+/g, "-");
}

// Kilit dosyasından paketleri bağımlılıklarıyla birlikte çözer → [{ad, surum, dosya, sha256}] (ada göre sıralı).
function paketleriCoz(kilit, istenen) {
  const paketler = (kilit && kilit.packages) || {};
  const dizin = {};
  Object.keys(paketler).forEach(function (anahtar) {
    dizin[paketAdiNormal(anahtar)] = anahtar;
    if (paketler[anahtar] && paketler[anahtar].name) dizin[paketAdiNormal(paketler[anahtar].name)] = anahtar;
  });
  const sonuc = new Map();
  const ziyaret = function (ad, zincir) {
    const anahtar = dizin[paketAdiNormal(ad)];
    if (!anahtar) throw new Error("Pyodide kilit dosyasında paket yok: " + ad + (zincir.length ? " (" + zincir.join(" → ") + " gerektiriyor)" : ""));
    if (sonuc.has(anahtar)) return;
    const p = paketler[anahtar];
    if (!p.file_name || /[\\/]|^\./.test(p.file_name)) throw new Error("Geçersiz paket dosya adı: " + anahtar);
    sonuc.set(anahtar, { ad: anahtar, surum: p.version || "", dosya: p.file_name, sha256: (p.sha256 || "").toLowerCase() });
    (p.depends || []).forEach(function (b) { ziyaret(b, zincir.concat([anahtar])); });
  };
  (istenen || []).forEach(function (ad) { ziyaret(ad, []); });
  return Array.from(sonuc.values()).sort(function (a, b) { return a.ad.localeCompare(b.ad); });
}

// HTML'deki CDN kütüphane adresleri: https://cdn.jsdelivr.net/npm/<paket>@<sürüm>/<yol>
// → [{url, yol: "<paket>@<sürüm>/<yol>", yerel: "kutuphane/<paket>@<sürüm>/<yol>"}]
function cdnAdresleri(html) {
  const bulunan = new Map();
  const desen = /https:\/\/cdn\.jsdelivr\.net\/npm\/([^"'\s<>()]+)/g;
  let m;
  while ((m = desen.exec(String(html || ""))) !== null) {
    const yol = m[1];
    if (!/^(@[a-z0-9._-]+\/)?[a-z0-9._-]+@[0-9][0-9A-Za-z.+-]*\/[A-Za-z0-9._/-]+$/i.test(yol) || yol.indexOf("..") >= 0) {
      throw new Error("Tanınmayan ya da sürümü sabitlenmemiş CDN adresi: " + m[0]);
    }
    if (!bulunan.has(m[0])) bulunan.set(m[0], { url: m[0], yol: yol, yerel: "kutuphane/" + yol });
  }
  return Array.from(bulunan.values());
}

// CSS'teki göreli yazı tipi adresleri (yalnız woff2: tarayıcı listedeki ilk desteklenen biçimi kullanır).
function cssYaziTipleri(css) {
  const bulunan = new Set();
  const desen = /url\(\s*["']?([^"')]+?\.woff2)["']?\s*\)/g;
  let m;
  while ((m = desen.exec(String(css || ""))) !== null) {
    const u = m[1];
    if (/^(data:|https?:|\/)/i.test(u) || u.indexOf("..") >= 0) continue;
    bulunan.add(u);
  }
  return Array.from(bulunan).sort();
}

function htmlYerellestir(html, adresler) {
  let sonuc = String(html);
  adresler.forEach(function (a) { sonuc = sonuc.split(a.url).join(a.yerel); });
  return sonuc;
}

// Kopyadaki worker'a yerel Pyodide adresi eklenir (web sürümündeki kaynak dosya değişmez).
function workerYerellestir(metin, adres) {
  const kaynak = String(metin);
  if (kaynak.indexOf("MATRIS_PYODIDE_URL") < 0) {
    throw new Error("docs/motor.worker.js yerel Pyodide adresini (self.MATRIS_PYODIDE_URL) desteklemiyor.");
  }
  const satir = "self.MATRIS_PYODIDE_URL = " + JSON.stringify(adres || YEREL_PYODIDE) +
    ";   // masaustu/hazirla.js ekledi: Pyodide uygulamayla birlikte gelir (çevrimdışı)\n";
  const yer = kaynak.search(/["']use strict["'];?[^\n]*\n/);
  if (yer < 0) return satir + kaynak;
  const son = kaynak.indexOf("\n", yer) + 1;
  return kaynak.slice(0, son) + satir + kaynak.slice(son);
}

function ozet(veri) {
  return crypto.createHash("sha256").update(veri).digest("hex");
}

// Klasördeki dosyaların göreli yolları (POSIX ayırıcı, sıralı); atlanan adlar hariç.
function dosyaListesi(kok) {
  const sonuc = [];
  const gez = function (dizin, onek) {
    fs.readdirSync(dizin, { withFileTypes: true }).forEach(function (g) {
      if (ATLANAN.has(g.name) || /\.pyc$/.test(g.name)) return;
      const tam = path.join(dizin, g.name);
      const goreli = onek ? onek + "/" + g.name : g.name;
      if (g.isDirectory()) gez(tam, goreli);
      else if (g.isFile()) sonuc.push(goreli);
    });
  };
  gez(kok, "");
  return sonuc.sort();
}

// ---------------------------------------------------------------- indirme

function bekle(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

function atomikYaz(hedef, veri) {
  fs.mkdirSync(path.dirname(hedef), { recursive: true });
  const gecici = hedef + "." + process.pid + ".indiriliyor";
  fs.writeFileSync(gecici, veri);
  fs.renameSync(gecici, hedef);
}

// url → hedef (önbellek). sha256 verilirse denetlenir; önbellekteki dosya da aynı denetimden geçer.
async function indir(is, secenek) {
  const s = secenek || {};
  if (fs.existsSync(is.hedef)) {
    const veri = fs.readFileSync(is.hedef);
    if (veri.length && (!is.sha256 || ozet(veri) === is.sha256)) return "önbellek";
  }
  if (s.agYok) throw new AgHatasi("Önbellekte yok ve indirme kapalı (--ag-yok): " + is.url);
  let sonHata = null;
  for (let deneme = 1; deneme <= 3; deneme++) {
    try {
      let r;
      try {
        r = await fetch(is.url, { redirect: "follow", signal: AbortSignal.timeout(180000) });
      } catch (e) {
        throw new AgHatasi(is.url + " alınamadı: " + (e && e.cause && e.cause.message ? e.cause.message : (e && e.message) || e));
      }
      if (r.status === 404) throw new Error(is.url + " bulunamadı (404).");
      if (!r.ok) throw new AgHatasi(is.url + " alınamadı (HTTP " + r.status + ").");
      const veri = Buffer.from(await r.arrayBuffer());
      if (!veri.length) throw new AgHatasi(is.url + " boş geldi.");
      if (is.sha256 && ozet(veri) !== is.sha256) throw new Error(is.url + " SHA-256 özeti kilit dosyasıyla uyuşmuyor.");
      atomikYaz(is.hedef, veri);
      return "indirildi";
    } catch (e) {
      sonHata = e;
      if (!(e instanceof AgHatasi)) throw e;
      if (deneme < 3) await bekle(800 * deneme);
    }
  }
  throw sonHata;
}

async function hepsiniIndir(isler, secenek) {
  const sayac = { "önbellek": 0, "indirildi": 0 };
  let sira = 0;
  const calisan = async function () {
    while (sira < isler.length) {
      const is = isler[sira++];
      sayac[await indir(is, secenek)]++;
    }
  };
  await Promise.all(Array.from({ length: Math.min(4, isler.length) }, calisan));
  return sayac;
}

// ---------------------------------------------------------------- hazırlık

function kopyala(kaynak, hedef) {
  fs.mkdirSync(path.dirname(hedef), { recursive: true });
  fs.copyFileSync(kaynak, hedef);
}

async function hazirla(secenek) {
  const s = Object.assign({ cikti: VARSAYILAN_CIKTI, onbellek: VARSAYILAN_ONBELLEK, agYok: false, gunluk: console.log }, secenek || {});
  // Paketleyici simgesi yalnız varsayılan çıktı hazırlanırken yazılır (başka klasöre deneme hazırlığı build/'e dokunmaz).
  if (s.simge === undefined) s.simge = path.resolve(s.cikti) === VARSAYILAN_CIKTI;
  const yaz = s.gunluk;
  if (!fs.existsSync(path.join(DOCS, "index.html"))) throw new Error("Web uygulaması bulunamadı: " + DOCS);
  const cikti = path.resolve(s.cikti);
  const onbellek = path.resolve(s.onbellek);
  if (cikti === DOCS || DOCS.startsWith(cikti + path.sep)) throw new Error("Çıktı klasörü docs'u kapsayamaz: " + cikti);

  // 1) Motorun Pyodide sürümü ve paketleri
  const workerMetni = fs.readFileSync(path.join(DOCS, "motor.worker.js"), "utf8");
  const surum = pyodideSurumu(workerMetni);
  const istenen = yuklenenPaketler(workerMetni);
  const taban = CDN + "pyodide/v" + surum + "/full/";
  const pyoOnbellek = path.join(onbellek, "pyodide-" + surum);
  yaz("Pyodide " + surum + " · motor paketleri: " + istenen.join(", "));

  let sayac = await hepsiniIndir(PYODIDE_CEKIRDEK.map(function (ad) {
    return { url: taban + ad, hedef: path.join(pyoOnbellek, ad) };
  }), s);
  const kilit = JSON.parse(fs.readFileSync(path.join(pyoOnbellek, "pyodide-lock.json"), "utf8"));
  const paketler = paketleriCoz(kilit, istenen);
  const s2 = await hepsiniIndir(paketler.map(function (p) {
    return { url: taban + p.dosya, hedef: path.join(pyoOnbellek, p.dosya), sha256: p.sha256 || null };
  }), s);
  yaz("  çekirdek + " + paketler.length + " paket (" + paketler.map(function (p) { return p.ad + " " + p.surum; }).join(", ") +
    "): " + (sayac["indirildi"] + s2["indirildi"]) + " indirildi, " + (sayac["önbellek"] + s2["önbellek"]) + " önbellekten");
  const wasm = fs.readFileSync(path.join(pyoOnbellek, "pyodide.asm.wasm"));
  if (wasm.readUInt32BE(0) !== 0x0061736d) throw new Error("pyodide.asm.wasm geçerli bir WebAssembly dosyası değil.");

  // 2) HTML sayfalarının CDN kütüphaneleri (+ CSS yazı tipleri)
  const sayfalar = fs.readdirSync(DOCS).filter(function (ad) { return /\.html?$/i.test(ad); }).sort();
  const sayfaAdresleri = {};
  const kutuphane = new Map();
  sayfalar.forEach(function (ad) {
    const adresler = cdnAdresleri(fs.readFileSync(path.join(DOCS, ad), "utf8"));
    sayfaAdresleri[ad] = adresler;
    adresler.forEach(function (a) { kutuphane.set(a.yol, a); });
  });
  const npmOnbellek = path.join(onbellek, "npm");
  const kutIsleri = Array.from(kutuphane.values()).map(function (a) {
    return { url: a.url, hedef: path.join(npmOnbellek, a.yol), yol: a.yol };
  });
  sayac = await hepsiniIndir(kutIsleri, s);
  const ekIsler = [];
  kutIsleri.forEach(function (is) {
    if (!/\.css$/i.test(is.yol)) return;
    const klasor = path.posix.dirname(is.yol);
    cssYaziTipleri(fs.readFileSync(is.hedef, "utf8")).forEach(function (u) {
      const yol = path.posix.normalize(klasor + "/" + u);
      ekIsler.push({ url: CDN_NPM + yol, hedef: path.join(npmOnbellek, yol), yol: yol });
    });
  });
  const s3 = await hepsiniIndir(ekIsler, s);
  const kutDosyalari = kutIsleri.concat(ekIsler);
  yaz("Kütüphaneler: " + kutIsleri.map(function (k) { return k.yol.split("/")[0]; }).filter(function (v, i, d) { return d.indexOf(v) === i; }).join(", ") +
    " (+" + ekIsler.length + " yazı tipi): " + (sayac["indirildi"] + s3["indirildi"]) + " indirildi");

  // 3) Çıktı: önce geçici klasöre kur, sonra eskisinin yerine koy (yarım kalmış çıktı olmaz)
  const gecici = cikti + ".hazirlaniyor";
  fs.rmSync(gecici, { recursive: true, force: true });
  const docsDosyalari = dosyaListesi(DOCS);
  docsDosyalari.forEach(function (g) { kopyala(path.join(DOCS, g), path.join(gecici, g)); });

  const pyoDosyalari = PYODIDE_CEKIRDEK.concat(paketler.map(function (p) { return p.dosya; }));
  pyoDosyalari.forEach(function (ad) { kopyala(path.join(pyoOnbellek, ad), path.join(gecici, "pyodide", ad)); });
  kutDosyalari.forEach(function (k) { kopyala(k.hedef, path.join(gecici, "kutuphane", k.yol)); });

  sayfalar.forEach(function (ad) {
    if (!sayfaAdresleri[ad].length) return;
    const yol = path.join(gecici, ad);
    fs.writeFileSync(yol, htmlYerellestir(fs.readFileSync(yol, "utf8"), sayfaAdresleri[ad]), "utf8");
  });
  const workerYolu = path.join(gecici, "motor.worker.js");
  fs.writeFileSync(workerYolu, workerYerellestir(fs.readFileSync(workerYolu, "utf8"), YEREL_PYODIDE), "utf8");

  let paket = {};
  try { paket = JSON.parse(fs.readFileSync(path.join(BURASI, "package.json"), "utf8")); } catch (e) { /* yoksay */ }
  let icerikSurumu = null;
  try { icerikSurumu = JSON.parse(fs.readFileSync(path.join(DOCS, "surum.json"), "utf8")).surum || null; } catch (e) { /* yoksay */ }
  const bilgi = {
    uygulama: paket.version || null,
    icerik_surumu: icerikSurumu,
    hazirlanma: new Date().toISOString(),
    pyodide: {
      surum: surum,
      adres: YEREL_PYODIDE,
      cekirdek: PYODIDE_CEKIRDEK.slice(),
      paketler: paketler.map(function (p) { return { ad: p.ad, surum: p.surum, dosya: p.dosya }; }),
    },
    kutuphaneler: kutDosyalari.map(function (k) { return k.yol; }).sort(),
    docs_dosyalari: docsDosyalari.length,
  };
  fs.writeFileSync(path.join(gecici, "masaustu.json"), JSON.stringify(bilgi, null, 1) + "\n", "utf8");

  fs.rmSync(cikti, { recursive: true, force: true });
  fs.renameSync(gecici, cikti);

  // 4) Paketleyici simgesi (docs/icons'tan)
  if (s.simge) {
    const simge = path.join(DOCS, "icons", "icon-512.png");
    if (fs.existsSync(simge)) kopyala(simge, SIMGE_HEDEF);
  }

  const boyut = dosyaListesi(cikti).reduce(function (t, g) { return t + fs.statSync(path.join(cikti, g)).size; }, 0);
  const goreli = path.relative(process.cwd(), cikti);
  yaz("✔ " + (goreli && !goreli.startsWith("..") && !path.isAbsolute(goreli) ? goreli : cikti) + path.sep + " hazır: " + docsDosyalari.length + " uygulama dosyası, " + pyoDosyalari.length +
    " Pyodide dosyası, " + kutDosyalari.length + " kütüphane dosyası; toplam " + (boyut / 1048576).toFixed(1) + " MB");
  return bilgi;
}

// ---------------------------------------------------------------- yerel önizleme sunucusu

function sunucuBaslat(kok, port) {
  const http = require("http");
  const sunucu = require("./lib/sunucu");
  if (!fs.existsSync(path.join(kok, "index.html"))) throw new Error("Önce hazırlayın (node hazirla.js): " + kok);
  const srv = http.createServer(function (istek, yanit) {
    if (istek.method !== "GET" && istek.method !== "HEAD") { yanit.writeHead(405); yanit.end(); return; }
    sunucu.yanitUret(kok, "http://yerel" + istek.url).then(function (y) {
      yanit.writeHead(y.durum, y.basliklar);
      yanit.end(istek.method === "HEAD" ? undefined : y.govde);
    }, function (e) { yanit.writeHead(500); yanit.end(String(e)); });
  });
  srv.listen(port, "127.0.0.1", function () {
    console.log("Önizleme: http://127.0.0.1:" + srv.address().port + "/  (durdurmak için Ctrl+C)");
  });
  return srv;
}

// ---------------------------------------------------------------- komut satırı

function argumanlar(argv) {
  const s = { cikti: VARSAYILAN_CIKTI, onbellek: VARSAYILAN_ONBELLEK, agYok: false, sunucu: false, port: 8765 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--cikti") s.cikti = path.resolve(argv[++i]);
    else if (a === "--onbellek") s.onbellek = path.resolve(argv[++i]);
    else if (a === "--ag-yok") s.agYok = true;
    else if (a === "--sunucu") s.sunucu = true;
    else if (a === "--port") s.port = parseInt(argv[++i], 10) || 0;
    else if (a === "-h" || a === "--yardim" || a === "--help") s.yardim = true;
    else throw new Error("Bilinmeyen seçenek: " + a);
  }
  return s;
}

async function ana() {
  // Vekil sunucu (HTTPS_PROXY) arkasında Node'un yerleşik fetch'i vekili ancak NODE_USE_ENV_PROXY=1 ile kullanır (Node ≥ 22.21).
  if ((process.env.HTTPS_PROXY || process.env.https_proxy) && !process.env.NODE_USE_ENV_PROXY) {
    const r = spawnSync(process.execPath, ["--disable-warning=UNDICI-EHPA"].concat(process.argv.slice(1)), { stdio: "inherit", env: Object.assign({}, process.env, { NODE_USE_ENV_PROXY: "1" }) });
    process.exit(r.status === null ? 1 : r.status);
  }
  let s;
  try { s = argumanlar(process.argv.slice(2)); } catch (e) { console.error(e.message); process.exit(1); }
  if (s.yardim) {
    console.log(fs.readFileSync(__filename, "utf8").split("*/")[0].replace(/^#!.*\n\/\*\s?/, ""));
    return;
  }
  if (s.sunucu) { sunucuBaslat(s.cikti, s.port); return; }
  try {
    await hazirla(s);
  } catch (e) {
    console.error("✘ " + (e && e.message ? e.message : e));
    if (e instanceof AgHatasi) {
      console.error("  İnternet bağlantısını denetleyin; vekil sunucu kullanıyorsanız HTTPS_PROXY ayarlı olmalı.");
      process.exit(AG_HATASI_KODU);
    }
    process.exit(1);
  }
}

module.exports = {
  pyodideSurumu: pyodideSurumu, yuklenenPaketler: yuklenenPaketler, paketleriCoz: paketleriCoz, cdnAdresleri: cdnAdresleri,
  cssYaziTipleri: cssYaziTipleri, htmlYerellestir: htmlYerellestir, workerYerellestir: workerYerellestir, dosyaListesi: dosyaListesi,
  hazirla: hazirla, AgHatasi: AgHatasi, PYODIDE_CEKIRDEK: PYODIDE_CEKIRDEK, YEREL_PYODIDE: YEREL_PYODIDE, AG_HATASI_KODU: AG_HATASI_KODU,
};

if (require.main === module) ana();
