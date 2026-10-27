/* Matris Öğren — Python motoru. Pyodide (WebAssembly içinde CPython + sympy + numpy) bu ayrı iş
   parçacığında çalışır; hesap sırasında arayüz donmaz. Sayfa ile JSON mesajlarıyla konuşur:
   gelen: {tur:"baslat"} | {tur:"istek", id, istek}
   giden: {tur:"durum", metin, oran} | {tur:"hazir", surum} | {tur:"hata", mesaj} | {tur:"yanit", id, yanit} */
"use strict";

const PYODIDE_SURUM = "314.0.7";
const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_SURUM + "/full/";
// Pyodide'nin yerel kopyası (masaüstü sürümü, çevrimdışı denemeler): önce worker adresindeki ?pyodide=… sorgu
// parametresi (yalnız aynı kökenden bir adres), sonra self.MATRIS_PYODIDE_URL. İkisi de yoksa web sürümündeki gibi CDN.
const PYODIDE_URL = pyodideAdresi();

function pyodideAdresi() {
  const klasor = function (adres) { return adres.endsWith("/") ? adres : adres + "/"; };
  try {
    const burasi = new URL(self.location.href);
    const sorgu = burasi.searchParams.get("pyodide");
    if (sorgu) {
      const u = new URL(sorgu, burasi);
      if (u.origin === burasi.origin) return klasor(u.href);
    }
    if (typeof self.MATRIS_PYODIDE_URL === "string" && self.MATRIS_PYODIDE_URL) return klasor(new URL(self.MATRIS_PYODIDE_URL, burasi).href);
  } catch (e) { /* geçersiz adres: CDN kullanılır */ }
  return PYODIDE_CDN;
}

let pyodide = null;
let kopru = null;
let hazirSoz = null;

function bildir(tur, veri) {
  self.postMessage(Object.assign({ tur: tur }, veri || {}));
}

async function dosyaAl(ad) {
  const r = await fetch(ad, { cache: "no-cache" });
  if (!r.ok) throw new Error(ad + " alınamadı (" + r.status + ")");
  return r.text();
}

async function hazirla() {
  bildir("durum", { metin: "Python motoru indiriliyor…", oran: 5 });
  // Bu worker "module" türünde açılır (app.js). Pyodide'nin klasik yükleyicisi pyodide.js worker içinde
  // artık var olmayan pyodide.asm.js'i aradığından (404) ESM yükleyici pyodide.mjs kullanılır.
  const pyodideModulu = await import(PYODIDE_URL + "pyodide.mjs");
  pyodide = await pyodideModulu.loadPyodide({ indexURL: PYODIDE_URL });
  bildir("durum", { metin: "sympy ve numpy yükleniyor…", oran: 45 });
  await pyodide.loadPackage(["sympy", "numpy"], { messageCallback: function () {}, errorCallback: function () {} });
  bildir("durum", { metin: "matris_ogren hazırlanıyor…", oran: 85 });
  // İsteğe bağlı modüller (eski kurulumlarda yok): alınamazsa motor onlarsız çalışır (ders örnekleri "se" adını,
  // Bina sayfası "bina_*" işlemlerini bulamaz; arayüz yerleşik şablon/kütüphaneyle çizilir). tasarim.py: kesit tahkikleri
  // (TS 500, ÇYTHYE); rapor.py: statik hesap raporu (bina_rapor); temel.py: mütemadi ve radye temel (Winkler);
  // tablolar.py: tablo editörü ve metraj (bina_tablolar); alan.py: ısı haritası alanları (bina_alan).
  const ISTEGE_BAGLI = ["sonlu_eleman.py", "yapi_veri.py", "yapi.py", "tasarim.py", "rapor.py", "temel.py", "tablolar.py", "alan.py"];
  const istege = function (ad) { return dosyaAl(ad).catch(function () { return null; }); };
  const dosyalar = await Promise.all([dosyaAl("matris_ogren.py"), dosyaAl("web_kopru.py")].concat(ISTEGE_BAGLI.map(istege)));
  pyodide.FS.writeFile("/home/pyodide/matris_ogren.py", dosyalar[0], { encoding: "utf8" });
  pyodide.FS.writeFile("/home/pyodide/web_kopru.py", dosyalar[1], { encoding: "utf8" });
  ISTEGE_BAGLI.forEach(function (ad, i) {
    if (dosyalar[i + 2] !== null) pyodide.FS.writeFile("/home/pyodide/" + ad, dosyalar[i + 2], { encoding: "utf8" });
  });
  pyodide.runPython("import sys\nif '/home/pyodide' not in sys.path:\n    sys.path.insert(0, '/home/pyodide')");
  kopru = pyodide.pyimport("web_kopru");
  const surum = JSON.parse(kopru.surum_json());
  surum.pyodide = PYODIDE_SURUM;
  bildir("hazir", { surum: surum });
}

self.onmessage = async function (e) {
  const m = e.data || {};
  if (m.tur === "baslat") {
    if (!hazirSoz) {
      hazirSoz = hazirla().catch(function (err) {
        kopru = null;
        bildir("hata", { mesaj: "Python motoru yüklenemedi: " + (err && err.message ? err.message : String(err)) });
      });
    }
    return;
  }
  if (m.tur === "istek") {
    let yanit;
    try {
      if (hazirSoz) await hazirSoz;
      if (!kopru) throw new Error("Motor hazır değil.");
      yanit = JSON.parse(kopru.calistir(JSON.stringify(m.istek || {})));
    } catch (err) {
      yanit = { hata: "Motor hatası: " + (err && err.message ? err.message : String(err)), hata_turu: "ic" };
    }
    bildir("yanit", { id: m.id, yanit: yanit });
  }
};
