/* Matris Öğren masaüstü — ön yükleme betiği (yalıtılmış bağlam, sandbox).
   Sayfaya yalnız dar ve dondurulmuş bir `window.masaustu` yüzeyi açılır; Node/dosya sistemi sayfaya hiç verilmez.
   Sayfa tarafındaki kullanım docs/masaustu_kopru.js içindedir (window.MatrisDosya bunu sarar). */
"use strict";

const { contextBridge, ipcRenderer, webUtils } = require("electron");

function argDegeri(ad) {
  const on = "--" + ad + "=";
  const a = (process.argv || []).find(function (x) { return typeof x === "string" && x.indexOf(on) === 0; });
  return a ? a.slice(on.length) : "";
}

function dinleyici(kanal, fn) {
  if (typeof fn !== "function") throw new TypeError("Dinleyici bir işlev olmalı.");
  const h = function (_olay, deger) { fn(deger); };
  ipcRenderer.on(kanal, h);
  return function birak() { ipcRenderer.removeListener(kanal, h); };
}

function ikiliMi(x) {
  return x instanceof Uint8Array || x instanceof ArrayBuffer;
}

const masaustu = {
  surum: argDegeri("matris-surum") || "0.0.0",
  platform: process.platform,
  // Pyodide yerel kopyası (çevrimdışı): uygulama ile birlikte gelir, CDN'e gidilmez.
  pyodideURL: argDegeri("matris-pyodide") || "app://matris/pyodide/",

  // Dışa aktarma: {ad, icerik: string|Uint8Array|ArrayBuffer, filtreler: [{ad, uzantilar}]} → {ad, yol} | null (vazgeçildi)
  kaydet: function (secenek) {
    const s = secenek || {};
    const icerik = ikiliMi(s.icerik) ? new Uint8Array(s.icerik) : String(s.icerik == null ? "" : s.icerik);
    return ipcRenderer.invoke("matris:kaydet", { ad: String(s.ad || ""), icerik: icerik, filtreler: s.filtreler || [], baslik: s.baslik || "" });
  },
  // İçe alma: {filtreler, ikili} → {ad, yol, icerik} | null
  ac: function (secenek) {
    const s = secenek || {};
    return ipcRenderer.invoke("matris:ac", { filtreler: s.filtreler || [], ikili: !!s.ikili, baslik: s.baslik || "" });
  },
  // Proje (.matris): {ad, icerik, farkli} → {ad, yol} | null. Pencerenin dosyası biliniyorsa ve farkli değilse doğrudan yazar.
  projeKaydet: function (secenek) {
    const s = secenek || {};
    return ipcRenderer.invoke("matris:proje-kaydet", { ad: String(s.ad || ""), icerik: String(s.icerik == null ? "" : s.icerik), farkli: !!s.farkli });
  },
  projeAc: function () { return ipcRenderer.invoke("matris:proje-ac"); },
  // Sürükle-bırak: bırakılan File nesnesinin yolu → main okur (yalnız .matris/.json)
  dosyaYolu: function (dosya) { try { return webUtils.getPathForFile(dosya) || ""; } catch (e) { return ""; } },
  yolAc: function (yol) { return ipcRenderer.invoke("matris:yol-ac", String(yol || "")); },
  // Rapor: tam HTML → yerel PDF (A4). {html, ad} → {ad, yol} | null
  pdfYazdir: function (secenek) {
    const s = secenek || {};
    return ipcRenderer.invoke("matris:pdf", { html: String(s.html || ""), ad: String(s.ad || "rapor") });
  },
  // Pencere durumu
  degisti: function (kirli) { ipcRenderer.send("matris:kirli", !!kirli); },
  yeni: function () { ipcRenderer.send("matris:yeni"); },
  otomatikKayit: function (icerik, ad) { ipcRenderer.send("matris:otomatik-kayit", { icerik: String(icerik == null ? "" : icerik), ad: String(ad || "") }); },
  hazir: function () { ipcRenderer.send("matris:hazir"); },
  tamEkran: function () { ipcRenderer.send("matris:tam-ekran"); },
  yeniPencere: function () { ipcRenderer.send("matris:yeni-pencere"); },
  harici: function (url) { ipcRenderer.send("matris:harici", String(url || "")); },
  // Ana süreçten gelenler: menü komutları ({komut, ...ek}) ve açılan dosyalar ({ad, yol, icerik, kurtarma?})
  komutDinle: function (fn) { return dinleyici("matris:komut", fn); },
  dosyaDinle: function (fn) { return dinleyici("matris:dosya-acildi", fn); },
};

contextBridge.exposeInMainWorld("masaustu", Object.freeze(masaustu));
