/* op4 — eşdeğerlik derleminin ortak kodu (MIMARI §9.5, D35; kabul B6). Sahibi: B (model-cekirdegi).
   Aynı dosya üç yerde çalışır: node'da derlem üretimi (op4/testler/js/derlem_uret.js) ve yeniden oynatma sınaması
   (op4/testler/js/derlem.test.js), QuickJS-ng'de C++ sınaması (op4/testler/cekirdek/cekirdek_js_derlem.cpp). node'da
   module.exports, QuickJS'te self.DerlemOrtak (UMD).

   Derlem: op4/testler/derlem/derlem.jsonl. İlk satır üst bilgi, sonraki her satır bir (işlem, girdi, çıktı) üçlüsüdür:
     {"m": modül ("ModelOps", "MatrisAks", "MatrisBinaCizim", "MatrisIFC", "MatrisTablo", "Op4Ops" ya da "$senaryo"),
      "f": işlev yolu ("genellestir", "_ic.degisiklikleriUygula", senaryoda "cephe"), "a": [kodlanmış bağımsız değişkenler],
      "s": kodlanmış dönüş | "h": {ad, mesaj?} (fırlatılan istisna), "k": kaynak ("testler/js/model_ops.test.js", "sablon"),
      "q": "node" yalnız node'da oynatılır (QuickJS'te çok yavaş; C++ yalnız çıktısını okur)}
   Kodlama JSON'un taşıyamadıklarını etiketler: undefined {"$u":1}, NaN / ±Infinity {"$s":"NaN"}, tipli dizi
   {"$t":"Float64Array","v":[…]}, "$" ile başlayan anahtarlı nesne {"$o":{…}}; şablon girdileri {"$sablon": ad} (nesne) ve
   {"$sablonMetin": ad} (dosya metni), çözüm verisi {"$sonuc": ad} başvurusudur (derlem/sablonlar, derlem/sonuclar).
   Karşılaştırma kodlanmış ağaçlar üstündedir: sayılar bağıl 1e-12 (|a − b| ≤ 1e-12 · max(1, |a|, |b|)), diğer her şey birebir.
   Saat: üretim ve oynatma Date.now / new Date()'i SABIT_SAAT'e sabitler (zaman damgası taşıyan çıktılar karşılaştırılabilsin). */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.DerlemOrtak = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const BICIM = 1;
  const SABIT_SAAT = Date.UTC(2026, 0, 2, 3, 4, 5);
  const TOL = 1e-12;
  const TIPLI = ["Int8Array", "Uint8Array", "Uint8ClampedArray", "Int16Array", "Uint16Array", "Int32Array", "Uint32Array",
    "Float32Array", "Float64Array"];
  /** Mesajı motordan bağımsız olan (modüllerin kendi) istisnaları: adıyla birlikte mesajı da karşılaştırılır. */
  const MODEL_HATALARI = ["ModelHatasi", "AksHatasi", "Op4Hatasi", "IFCHatasi"];
  const MODULLER = ["ModelOps", "MatrisAks", "MatrisBinaCizim", "MatrisIFC", "MatrisTablo", "Op4Ops", "Op4Cekirdek"];

  /** Kodlanamayan değer: üçlü derleme alınmaz (işlev, Map, sınıf örneği, döngü …). */
  class Atla extends Error {
    constructor(neden) { super(neden); this.name = "Atla"; }
  }

  function duzNesneMi(x) {
    const p = Object.getPrototypeOf(x);
    return p === Object.prototype || p === null;
  }
  function tipliAdi(x) {
    if (!ArrayBuffer.isView(x) || x instanceof DataView) return null;
    for (const t of TIPLI) if (typeof globalThis[t] === "function" && x instanceof globalThis[t]) return t;
    return null;
  }

  /** Değer → JSON'a yazılabilir etiketli ağaç. Kodlanamayanda Atla fırlatır. */
  function kodla(x, yigin) {
    if (x === undefined) return { $u: 1 };
    if (x === null || typeof x === "boolean" || typeof x === "string") return x;
    if (typeof x === "number") return isFinite(x) ? x : { $s: String(x) };
    if (typeof x !== "object") throw new Atla(typeof x);
    yigin = yigin || [];
    if (yigin.indexOf(x) >= 0) throw new Atla("döngü");
    const t = tipliAdi(x);
    if (t) {
      const v = new Array(x.length);
      for (let i = 0; i < x.length; i++) v[i] = kodla(x[i]);
      return { $t: t, v: v };
    }
    yigin.push(x);
    try {
      if (Array.isArray(x)) {
        const d = new Array(x.length);
        for (let i = 0; i < x.length; i++) d[i] = kodla(x[i], yigin);
        return d;
      }
      if (!duzNesneMi(x)) throw new Atla("sınıf örneği (" + ((x.constructor && x.constructor.name) || "?") + ")");
      const o = {};
      let dolar = false;
      for (const k of Object.keys(x)) {
        if (k.charAt(0) === "$") dolar = true;
        o[k] = kodla(x[k], yigin);
      }
      return dolar ? { $o: o } : o;
    } finally {
      yigin.pop();
    }
  }

  /**
   * Etiketli ağaç → değer. baglam: {sablonlar: {ad: metin}, sonuclar: {ad: metin}} — başvurular her çözümde YENİ nesne üretir
   * (işlevler girdiyi değiştirse de sonraki üçlü etkilenmez).
   */
  function coz(x, baglam) {
    if (x === null || typeof x !== "object") return x;
    if (Array.isArray(x)) return x.map(function (e) { return coz(e, baglam); });
    if (x.$u === 1 && Object.keys(x).length === 1) return undefined;
    if (typeof x.$s === "string") return Number(x.$s);
    if (typeof x.$t === "string") {
      const T = globalThis[x.$t];
      return T.from(x.v.map(function (e) { return coz(e, baglam); }));
    }
    if (typeof x.$sablon === "string") return JSON.parse(metinAl(baglam, "sablonlar", x.$sablon));
    if (typeof x.$sablonMetin === "string") return metinAl(baglam, "sablonlar", x.$sablonMetin);
    if (typeof x.$sonuc === "string") return JSON.parse(metinAl(baglam, "sonuclar", x.$sonuc));
    const kaynak = x.$o && typeof x.$o === "object" ? x.$o : x;
    const o = {};
    for (const k of Object.keys(kaynak)) o[k] = coz(kaynak[k], baglam);
    return o;
  }
  function metinAl(baglam, tur, ad) {
    const t = baglam && baglam[tur] && baglam[tur][ad];
    if (typeof t !== "string") throw new Error("Derlem başvurusu çözülemedi: " + tur + "/" + ad);
    return t;
  }

  /** İstisnanın kaydı: modül hatalarında ad + mesaj, motor hatalarında (TypeError …) yalnız ad. */
  function istisna(e) {
    const ad = e && e.name ? String(e.name) : "Error";
    return MODEL_HATALARI.indexOf(ad) >= 0 ? { ad: ad, mesaj: String(e.message) } : { ad: ad };
  }

  /**
   * Date.now ve bağımsız değişkensiz new Date() / Date() SABIT_SAAT'i döndürür. Geri dönüş işlevi eski Date'i kurar.
   * @param {Object} g globalThis
   */
  function saatSabitle(g) {
    const Asil = g.Date;
    function SabitDate() {
      if (!(this instanceof SabitDate)) return new Asil(SABIT_SAAT).toString();
      const a = Array.prototype.slice.call(arguments);
      return a.length ? new (Function.prototype.bind.apply(Asil, [null].concat(a)))() : new Asil(SABIT_SAAT);
    }
    SabitDate.prototype = Asil.prototype;
    SabitDate.now = function () { return SABIT_SAAT; };
    SabitDate.UTC = Asil.UTC;
    SabitDate.parse = Asil.parse;
    g.Date = SabitDate;
    return function () { g.Date = Asil; };
  }

  function islevBul(M, m, f) {
    let sahip = M[m], fn = sahip;
    if (!fn) throw new Error("Derlem modülü yok: " + m);
    for (const p of f.split(".")) { sahip = fn; fn = fn[p]; }
    if (typeof fn !== "function") throw new Error("Derlem işlevi yok: " + m + "." + f);
    return { sahip: sahip, fn: fn };
  }

  // ---------------------------------------------------------------- cephe senaryoları
  /** Cephe dönüşlerini kodlanabilir yapar (aynı nesne iki kez görülürse kopya; tipli diziler korunur). */
  function cepheDonusu(r) {
    return JSON.parse(JSON.stringify(r, function (k, v) {
      if (ArrayBuffer.isView(v)) { const t = tipliAdi(v); return { $t: t, v: Array.prototype.slice.call(v).map(function (e) { return isFinite(e) ? e : { $s: String(e) }; }) }; }
      if (typeof v === "number" && !isFinite(v)) return { $s: String(v) };
      return v;
    }));
  }
  /** Metnin kısa özeti (uzunluk + iki tohumlu FNV-1a, UTF-16 birimleri üstünde; iki motorda aynı). */
  function metinOzeti(s) {
    let a = 0x811c9dc5, b = 0x01000193 ^ 0x5bd1e995;
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      a = Math.imul(a ^ c, 0x01000193) >>> 0;
      b = Math.imul(b ^ c, 0x01000193) >>> 0;
      b = (b ^ (b >>> 13)) >>> 0;
    }
    return { uzunluk: s.length, fnv: ("0000000" + a.toString(16)).slice(-8) + ("0000000" + b.toString(16)).slice(-8) };
  }
  /**
   * Op4Cekirdek cephesinde bir adım dizisi: {adimlar: [[yöntem, ...kodlanmış bağımsız değişkenler]], ayar?}. Her adımın dönüşü
   * (istisnada {$istisna}) sırayla döner. "metinOzeti" adımı metin()'in yalnız özetini döndürür (derlem boyu). Cephe
   * çekirdeğin bağımlılıklarını M'den alır; saat SABIT_SAAT.
   */
  function cepheSenaryosu(M, girdi, baglam) {
    const ayar = Object.assign({}, girdi.ayar || {}, { saat: function () { return SABIT_SAAT; } });
    const c = M.Op4Cekirdek.olustur(M, ayar);
    const out = [];
    for (const adim of girdi.adimlar) {
      const yontem = adim[0], a = adim.slice(1).map(function (x) { return coz(x, baglam); });
      let r;
      try {
        if (yontem === "metinOzeti") r = metinOzeti(c.metin());
        else if (yontem === "ifcOzeti") { r = cepheDonusu(c.ifcDisari.apply(c, a)); if (typeof r.metin === "string") r.metin = metinOzeti(r.metin); }
        else r = cepheDonusu(c[yontem].apply(c, a));
      } catch (e) { r = { $istisna: istisna(e) }; }
      out.push(r === undefined ? { $u: 1 } : r);
    }
    return out;
  }
  /** MatrisIFC.uretAyrintili; metin yalnız özetiyle (büyük şablonlarda derlem boyu). girdi: {model, veri, secenek}. */
  function ifcSenaryosu(M, girdi) {
    const r = M.MatrisIFC.uretAyrintili(girdi.model, girdi.veri === undefined ? null : girdi.veri, girdi.secenek);
    return Object.assign({}, r, { metin: metinOzeti(r.metin) });
  }
  /**
   * ModelOps'a göre genel görünümün eleman sayıları: çubuk ve panel ModelOps.genellestir çıktısından, düğüm genellestir
   * modelinin çubuk / panel / mesnet başvurularının ModelOps.dugumNo numaraları ve düğüm kayıtlarıyla. C++ sahnesinin sayıları
   * bununla karşılaştırılır (kabul B5). YALNIZ node'da oynatılır (kayıtta q: "node"): dugumNo her çağrıda modeli yeniden
   * çözümler, QuickJS'te büyük şablonda dakikalar sürer.
   */
  function sayilarSenaryosu(M, girdi) {
    const MO = M.ModelOps, g = MO.genellestir(girdi.model).model;
    const refs = new Map(), no = new Set();
    const ekle = function (r) { const k = JSON.stringify(r); if (!refs.has(k)) refs.set(k, r); };
    for (const c of g.cubuklar || []) { ekle(c.i); ekle(c.j); }
    for (const p of g.paneller || []) for (const k of p.kose || []) ekle(k);
    for (const m of g.mesnetler || []) if (m) ekle(m.dugum);
    for (const d of g.dugumler || []) if (d && d.no != null) no.add(+d.no);
    for (const r of refs.values()) no.add(MO.dugumNo(g, r));
    return { dugum: no.size, cubuk: (g.cubuklar || []).length, panel: (g.paneller || []).length };
  }
  const SENARYOLAR = { cephe: cepheSenaryosu, ifc: ifcSenaryosu, sayilar: sayilarSenaryosu };

  /**
   * Tek üçlüyü çalıştırır; çıktıyı derlem biçiminde döndürür: {s} ya da {h}.
   * @param {Object} M modüller {ModelOps, MatrisAks, …}
   * @param {{m: string, f: string, a: Array}} kayit
   * @param {Object} baglam sablonlar / sonuclar metinleri
   */
  function calistir(M, kayit, baglam) {
    const a = coz(kayit.a, baglam);
    if (kayit.m === "$senaryo") return { s: kodla(SENARYOLAR[kayit.f](M, a[0], baglam)) };
    const i = islevBul(M, kayit.m, kayit.f);
    let r;
    try { r = i.fn.apply(i.sahip, a); } catch (e) { return { h: istisna(e) }; }
    return { s: kodla(r) };
  }

  /** Karşılaştırma (node tarafı; C++ aynı kuralı nlohmann ile uygular). İlk farkın yolunu ya da null döndürür. */
  function fark(a, b, yol) {
    yol = yol || "";
    if (typeof a === "number" && typeof b === "number") {
      return a === b || Math.abs(a - b) <= TOL * Math.max(1, Math.abs(a), Math.abs(b)) ? null : yol + ": " + a + " ≠ " + b;
    }
    if (a === null || b === null || typeof a !== "object" || typeof b !== "object") return a === b ? null : yol + ": " + JSON.stringify(a).slice(0, 80) + " ≠ " + JSON.stringify(b).slice(0, 80);
    if (Array.isArray(a) !== Array.isArray(b)) return yol + ": dizi / nesne";
    if (Array.isArray(a)) {
      if (a.length !== b.length) return yol + ": uzunluk " + a.length + " ≠ " + b.length;
      for (let i = 0; i < a.length; i++) { const f = fark(a[i], b[i], yol + "[" + i + "]"); if (f) return f; }
      return null;
    }
    const ka = Object.keys(a).sort(), kb = Object.keys(b).sort();
    if (ka.join("\u0001") !== kb.join("\u0001")) return yol + ": anahtarlar " + ka.join(",").slice(0, 120) + " ≠ " + kb.join(",").slice(0, 120);
    for (const k of ka) { const f = fark(a[k], b[k], yol + "." + k); if (f) return f; }
    return null;
  }

  return {
    BICIM: BICIM, SABIT_SAAT: SABIT_SAAT, TOL: TOL, MODULLER: MODULLER, Atla: Atla,
    kodla: kodla, coz: coz, istisna: istisna, saatSabitle: saatSabitle, calistir: calistir, fark: fark, metinOzeti: metinOzeti,
    SENARYOLAR: SENARYOLAR,
  };
});
