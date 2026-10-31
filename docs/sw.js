/* Matris Öğren — servis çalışanı (çevrimdışı çalışma ve güncelleme).
   SURUM damgasını web_yap.py yazar; değişince eski uygulama önbelleği atılır.
   CDN önbelleği (Pyodide, sympy/numpy tekerlekleri, KaTeX, marked) ayrı tutulur; sürümler değişmedikçe kalır. */
"use strict";

const SURUM = "ecb879a346";
const PYODIDE_SURUM = "314.0.7";
const KATEX_SURUM = "0.19.0";
const MARKED_SURUM = "18.1.0";

const KABUK_ONBELLEK = "matris-ogren-kabuk-" + SURUM;
const CDN_ONBELLEK = "matris-ogren-cdn-p" + PYODIDE_SURUM + "-k" + KATEX_SURUM + "-m" + MARKED_SURUM;
const CDN = "https://cdn.jsdelivr.net/";

const KABUK = [
  "./", "./index.html", "./style.css", "./app.js", "./motor.worker.js", "./web_kopru.py", "./matris_ogren.py",
  "./sonlu_eleman.py", "./yapi.py", "./yapi_veri.py", "./tasarim.py", "./rapor.py", "./temel.py", "./tablolar.py", "./alan.py", "./yapi_serbest.py", "./etkilesim.js", "./etkilesim_matris.js", "./etkilesim_se.js", "./etkilesim_yapi.js", "./se.js",
  "./model_ops.js", "./aks_sistemi.js", "./olcum.js", "./arac_kutusu.js", "./eleman_bilgi.js", "./cizim3b.js", "./ifc_disari.js", "./tablo_editoru.js", "./isi_haritasi.js", "./bina.js", "./bina_cizim.js", "./masaustu_kopru.js", "./galeri.html",
  "./dersler.json", "./surum.json", "./manifest.webmanifest",
  "./icons/icon.svg", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/icon-512-maskable.png",
  "./icons/apple-touch-icon.png",
];

// Çevrimdışı formül gösterimi için en çok kullanılan KaTeX yazı tipleri (küçük dosyalar).
const KATEX_YAZI = ["KaTeX_Main-Regular", "KaTeX_Main-Bold", "KaTeX_Main-Italic", "KaTeX_Math-Italic",
  "KaTeX_Math-BoldItalic", "KaTeX_Size1-Regular", "KaTeX_Size2-Regular", "KaTeX_Size3-Regular",
  "KaTeX_Size4-Regular", "KaTeX_AMS-Regular", "KaTeX_Caligraphic-Regular"]
  .map(function (ad) { return CDN + "npm/katex@" + KATEX_SURUM + "/dist/fonts/" + ad + ".woff2"; });
const CDN_ON = [
  CDN + "npm/katex@" + KATEX_SURUM + "/dist/katex.min.css",
  CDN + "npm/katex@" + KATEX_SURUM + "/dist/katex.min.js",
  CDN + "npm/marked@" + MARKED_SURUM + "/lib/marked.umd.js",
].concat(KATEX_YAZI);

self.addEventListener("install", function (e) {
  e.waitUntil((async function () {
    const kabuk = await caches.open(KABUK_ONBELLEK);
    await Promise.all(KABUK.map(async function (u) {
      try {
        const r = await fetch(new Request(u, { cache: "reload" }));
        if (r.ok) await kabuk.put(u, r);
      } catch (err) { /* çevrimdışı ya da eksik dosya: atla */ }
    }));
    const cdn = await caches.open(CDN_ONBELLEK);
    await Promise.all(CDN_ON.map(async function (u) {
      if (await cdn.match(u)) return;
      try { const r = await fetch(u); if (r.ok) await cdn.put(u, r); } catch (err) { /* çevrimdışı */ }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", function (e) {
  e.waitUntil((async function () {
    const adlar = await caches.keys();
    await Promise.all(adlar
      .filter(function (k) { return k.indexOf("matris-ogren-") === 0 && k !== KABUK_ONBELLEK && k !== CDN_ONBELLEK; })
      .map(function (k) { return caches.delete(k); }));
    await self.clients.claim();
  })());
});

self.addEventListener("message", function (e) {
  if (e.data && e.data.tur === "atla") self.skipWaiting();
});

self.addEventListener("fetch", function (e) {
  const istek = e.request;
  if (istek.method !== "GET") return;
  const url = new URL(istek.url);

  if (url.origin === self.location.origin) {
    // Uygulama kabuğu: önce önbellek, yoksa ağ (ve önbelleğe al); çevrimdışı gezinmede index.html.
    e.respondWith((async function () {
      const kabuk = await caches.open(KABUK_ONBELLEK);
      const bulunan = await kabuk.match(istek, { ignoreSearch: true });
      if (bulunan) return bulunan;
      try {
        const r = await fetch(istek);
        if (r.ok) kabuk.put(istek, r.clone());
        return r;
      } catch (err) {
        if (istek.mode === "navigate") {
          const sayfa = await kabuk.match("./index.html");
          if (sayfa) return sayfa;
        }
        throw err;
      }
    })());
    return;
  }

  if (url.href.indexOf(CDN) === 0) {
    // Pyodide, tekerlekler, KaTeX, marked: önce önbellek; ilk kez ağdan alınıp saklanır.
    e.respondWith((async function () {
      const cdn = await caches.open(CDN_ONBELLEK);
      const bulunan = await cdn.match(istek);
      if (bulunan) return bulunan;
      const r = await fetch(istek);
      if (r.ok) cdn.put(istek, r.clone());
      return r;
    })());
  }
});
