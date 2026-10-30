/* op4 — QuickJS ön yüklemesi (MIMARI §9.2; kabul B2). Yalnız op4'ün gömülü QuickJS-ng bağlamında, docs/ modüllerinden ÖNCE
   çalışır (node'da kullanılmaz). Sahibi: B (model-cekirdegi).
     - globalThis.self = globalThis: UMD sarmalayıcıları birbirini self üstünden bulur (docs/model_ops.js:56).
     - window ve document TANIMSIZ bırakılır: docs/ modüllerinin DOM katmanları kurulmaz (bina_cizim.js:35).
     - structuredClone yoksa C++ sürümü (__op4_klon; kaynak/cekirdek_js/js_ortami.cpp) bağlanır: model_ops.js kopya() onu kullanır.
     - console.* → op4 günlüğü (__op4_gunluk(düzey, metin)).
     - Deterministik saat (__op4_deterministik): Date.now 2026-01-01T00:00:00Z'den her çağrıda 1 ms ilerler (senaryolar,
       eşdeğerlik derlemi).
     - Türkçe yerel ayarlı harf dönüşümü: ICU'suz QuickJS'te toLocaleLowerCase("tr") / toLocaleUpperCase("tr") V8 ile aynı
       sonucu verir (I → ı, İ → i; i → İ). Başka yerel ayarlar yerelden bağımsız dönüşümdür (node'un varsayılan "en" yereli gibi). */
(function (g) {
  "use strict";
  g.self = g;
  delete g.window;
  delete g.document;

  const yaz = typeof g.__op4_gunluk === "function" ? g.__op4_gunluk : function () { /* günlük yok */ };
  function metin(a) {
    return Array.prototype.map.call(a, function (x) {
      if (typeof x === "string") return x;
      if (x instanceof Error) return x.name + ": " + x.message;
      try { const j = JSON.stringify(x); return j === undefined ? String(x) : j; } catch (e) { return String(x); }
    }).join(" ");
  }
  g.console = {
    log: function () { yaz("bilgi", metin(arguments)); },
    info: function () { yaz("bilgi", metin(arguments)); },
    debug: function () { yaz("ayrinti", metin(arguments)); },
    warn: function () { yaz("uyari", metin(arguments)); },
    error: function () { yaz("hata", metin(arguments)); },
  };

  if (typeof g.structuredClone !== "function" && typeof g.__op4_klon === "function") g.structuredClone = g.__op4_klon;

  if (g.__op4_deterministik === true) {
    let t = Date.UTC(2026, 0, 1, 0, 0, 0);
    Date.now = function () { return t++; };
  }

  const turkce = function (y) {
    const s = Array.isArray(y) ? y[0] : y;
    return typeof s === "string" && /^(tr|az)(-|_|$)/i.test(s);
  };
  Object.defineProperty(String.prototype, "toLocaleLowerCase", {
    value: function (y) { const s = String(this); return turkce(y) ? s.replace(/İ/g, "i").replace(/I/g, "ı").toLowerCase() : s.toLowerCase(); },
    writable: true, configurable: true, enumerable: false,
  });
  Object.defineProperty(String.prototype, "toLocaleUpperCase", {
    value: function (y) { const s = String(this); return turkce(y) ? s.replace(/i/g, "İ").toUpperCase() : s.toUpperCase(); },
    writable: true, configurable: true, enumerable: false,
  });
})(globalThis);
