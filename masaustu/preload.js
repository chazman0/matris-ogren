/* Matris Öğren masaüstü — ön yükleme betiği (yalıtılmış bağlam, sandbox).
   Sayfaya yalnız dar bir `window.masaustu` yüzeyi açılır; Node ve dosya sistemi sayfaya hiç verilmez.
   Sayfa tarafında bunu docs/masaustu_kopru.js sarar (window.MatrisDosya ve masaustu-* olayları).

   Sandbox içinde çalıştığı için tek dosyadır (yerel modül yüklenemez). Testler bu dosyayı sahte bir çatı modülüyle
   bir vm bağlamında çalıştırıp açılan yüzeyi inceler (testler/js/masaustu.test.js). */
"use strict";

const { contextBridge, ipcRenderer, webUtils } = require("electron");

const PROJE_UZANTISI = /\.(matris|json)$/i;

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
  return x instanceof Uint8Array || x instanceof ArrayBuffer || ArrayBuffer.isView(x);
}

function icerikNormal(x) {
  if (ikiliMi(x)) return x instanceof ArrayBuffer ? new Uint8Array(x) : new Uint8Array(x.buffer, x.byteOffset, x.byteLength);
  return String(x == null ? "" : x);
}

// Kaydet/aç iletişim kutusu süzgeçleri: [{ad, uzantilar: ["ifc"]}] (ana süreç ayrıca temizler)
function filtreNormal(liste) {
  return (Array.isArray(liste) ? liste : []).slice(0, 12).map(function (f) {
    return { ad: String((f && f.ad) || ""), uzantilar: (f && Array.isArray(f.uzantilar) ? f.uzantilar : []).map(String) };
  });
}

// Bina sayfasının kısayol listesi (sözleşme C22) → ana süreç: [{tus, ad, grup}], en çok 400 satır, alanlar en çok 120 karakterlik
// metin (tus ve ad dolu); uymayan satır atılır, denetim karakterleri boşluk olur. lib/menu.js kisayolListesiTemizle ile aynı kural
// (testler ikisini karşılaştırır); ana süreç gelen listeyi ayrıca temizler.
function kisayolListesiTemizle(liste) {
  const sonuc = [];
  if (!Array.isArray(liste)) return sonuc;
  const n = Math.min(liste.length, 4000);
  for (let i = 0; i < n && sonuc.length < 400; i++) {
    const s = liste[i];
    if (!s || typeof s !== "object") continue;
    const alan = [s.tus, s.ad, s.grup];
    if (!alan.every(function (x) { return typeof x === "string" && x.length <= 120; })) continue;
    const temiz = alan.map(function (x) { return x.replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]+/g, " ").trim(); });
    if (!temiz[0] || !temiz[1]) continue;
    sonuc.push({ tus: temiz[0], ad: temiz[1], grup: temiz[2] });
  }
  return sonuc;
}

const masaustu = {
  surum: argDegeri("matris-surum") || "0.0.0",
  platform: process.platform,

  // Dışa aktarma: {ad, icerik: string|Uint8Array|ArrayBuffer, filtreler, baslik} → Promise<{ad, yol} | null (vazgeçildi)>
  kaydet: function (secenek) {
    const s = secenek || {};
    return ipcRenderer.invoke("matris:kaydet", {
      ad: String(s.ad || ""), icerik: icerikNormal(s.icerik), filtreler: filtreNormal(s.filtreler), baslik: String(s.baslik || ""),
    });
  },
  // İçe alma: {filtreler, ikili, baslik} → Promise<{ad, yol, icerik: string|Uint8Array} | null>
  ac: function (secenek) {
    const s = secenek || {};
    return ipcRenderer.invoke("matris:ac", { filtreler: filtreNormal(s.filtreler), ikili: !!s.ikili, baslik: String(s.baslik || "") });
  },
  // Proje (.matris): {ad, icerik, farkli} → Promise<{ad, yol} | null>. Pencerenin dosyası biliniyorsa ve farkli değilse
  // iletişim kutusu açılmadan doğrudan o dosyaya yazılır (Ctrl+S).
  projeKaydet: function (secenek) {
    const s = secenek || {};
    return ipcRenderer.invoke("matris:proje-kaydet", { ad: String(s.ad || ""), icerik: String(s.icerik == null ? "" : s.icerik), farkli: !!s.farkli });
  },
  // Proje aç iletişim kutusu → Promise<{ad, yol, icerik} | null>; pencere bu dosyaya bağlanır, son dosyalara eklenir.
  projeAc: function () { return ipcRenderer.invoke("matris:proje-ac"); },
  // Rapor: tam HTML → yerel PDF (A4). {html, ad} → Promise<{ad, yol} | null>
  pdfYazdir: function (secenek) {
    const s = secenek || {};
    return ipcRenderer.invoke("matris:pdf", { html: String(s.html || ""), ad: String(s.ad || "rapor") });
  },
  // Bu oturumda kaydedilmiş bir dosyayı dosya yöneticisinde gösterir (başka yollar yok sayılır).
  klasordeGoster: function (yol) { ipcRenderer.send("matris:klasorde-goster", String(yol || "")); },

  // Pencere durumu
  degisti: function (kirli) { ipcRenderer.send("matris:kirli", !!kirli); },
  yeni: function () { ipcRenderer.send("matris:yeni"); },
  otomatikKayit: function (icerik, ad) { ipcRenderer.send("matris:otomatik-kayit", { icerik: String(icerik == null ? "" : icerik), ad: String(ad || "") }); },
  hazir: function () { ipcRenderer.send("matris:hazir"); },
  tamEkran: function () { ipcRenderer.send("matris:tam-ekran"); },
  yeniPencere: function () { ipcRenderer.send("matris:yeni-pencere"); },
  harici: function (url) { ipcRenderer.send("matris:harici", String(url || "")); },
  // Yardım › Klavye kısayolları penceresi için Bina sayfasının kısayolları: [{tus, ad, grup}] (temizlenir; boş liste = liste yok)
  kisayollar: function (liste) { ipcRenderer.send("matris:kisayollar", kisayolListesiTemizle(liste)); },

  // Ana süreçten gelenler: menü komutları ({komut, ...ek}) ve açılan dosyalar ({ad, yol, icerik, kurtarma?}).
  // Dönen işlev dinleyiciyi bırakır.
  komutDinle: function (fn) { return dinleyici("matris:komut", fn); },
  dosyaDinle: function (fn) { return dinleyici("matris:dosya-acildi", fn); },
};

contextBridge.exposeInMainWorld("masaustu", Object.freeze(masaustu));

// ---- Sürükle-bırak: pencereye bırakılan .matris / .json dosyaları açılır.
// Yalnız gerçek kullanıcı bırakmaları (isTrusted) işlenir; dosya yolu bu yalıtılmış bağlamda alınır ve sayfaya verilmez.
// Sayfadaki bir bırakma alanı olayı kendisi işlediyse (preventDefault) dokunulmaz. Diğer dosyalar yok sayılır
// (pencerenin dosyaya "gitmesi" engellenir).
function dosyaSurukleniyor(e) {
  const turler = e && e.dataTransfer && e.dataTransfer.types;
  return !!turler && Array.prototype.indexOf.call(turler, "Files") >= 0;
}

window.addEventListener("dragover", function (e) {
  if (!dosyaSurukleniyor(e) || e.defaultPrevented) return;
  e.preventDefault();
  try { e.dataTransfer.dropEffect = "copy"; } catch (err) { /* yoksay */ }
});

window.addEventListener("drop", function (e) {
  if (!dosyaSurukleniyor(e) || e.defaultPrevented) return;
  e.preventDefault();
  if (!e.isTrusted) return;
  const yollar = [];
  Array.prototype.forEach.call(e.dataTransfer.files || [], function (dosya) {
    if (!PROJE_UZANTISI.test(dosya.name || "")) return;
    let yol = "";
    try { yol = webUtils.getPathForFile(dosya) || ""; } catch (err) { yol = ""; }
    if (yol) yollar.push(yol);
  });
  if (yollar.length) ipcRenderer.send("matris:birakilan", yollar.slice(0, 16));
});
