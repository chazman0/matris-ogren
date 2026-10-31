/* op4 — QuickJS ön yüklemesi (MIMARI §9.2; kabul B2). Yalnız op4'ün gömülü QuickJS-ng bağlamında, docs/ modüllerinden ÖNCE
   çalışır (node'da kullanılmaz; op4/testler/js/onyukleme.test.js onu bir node vm bağlamında ICU'ya karşı sınar). Sahibi: B.
     - globalThis.self = globalThis: UMD sarmalayıcıları birbirini self üstünden bulur (docs/model_ops.js:56).
     - window ve document TANIMSIZ bırakılır: docs/ modüllerinin DOM katmanları kurulmaz (bina_cizim.js:35).
     - structuredClone yoksa C++ sürümü (__op4_klon; kaynak/cekirdek_js/js_ortami.cpp) bağlanır: model_ops.js kopya() onu kullanır.
     - console.* → op4 günlüğü (__op4_gunluk(düzey, metin)).
     - Deterministik saat (__op4_deterministik): Date.now 2026-01-01T00:00:00Z'den her çağrıda 1 ms ilerler (senaryolar,
       eşdeğerlik derlemi).
   ICU'suz motor (Intl yok) için V8 / ICU ile aynı sonucu veren öykünmeler (eşdeğerlik derleminin bulduğu ayrılıklar):
     - toLocaleLowerCase("tr") / toLocaleUpperCase("tr"): I → ı, İ → i; i → İ (docs/tablo_editoru.js katla). Başka yerel
       ayarlar yerelden bağımsız dönüşümdür (node'un varsayılan "en" yereli gibi).
     - localeCompare(b, yerel, {numeric, sensitivity}): ICU tr ve kök harmanlamasının karakter tablosuyla (HARMAN; node'un
       ICU'sundan op4/testler/js/harman_uret.js üretir) üç düzeyli karşılaştırma: temel harf, aksan, büyük/küçük; numeric'te
       rakam dizileri sayı değeriyle (baştaki sıfırlar yok sayılır). docs/tablo_editoru.js sıralaması bunu kullanır.
     - TextDecoder("utf-8" {fatal, ignoreBOM} | "windows-1254" ve WHATWG etiketleri): CSV içe aktarma (csvMetniCoz).
   __op4_oykunme_zorla === true ise öykünmeler Intl olsa da kurulur (yalnız sınama). */
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

  const oykun = typeof g.Intl === "undefined" || g.__op4_oykunme_zorla === true;
  if (!oykun) return;
  function tanimla(nesne, ad, deger) {
    Object.defineProperty(nesne, ad, { value: deger, writable: true, configurable: true, enumerable: false });
  }

  // ---------------------------------------------------------------- Türkçe büyük / küçük harf
  const turkce = function (y) {
    const s = Array.isArray(y) ? y[0] : y;
    return typeof s === "string" && /^(tr|az)(-|_|$)/i.test(s);
  };
  tanimla(String.prototype, "toLocaleLowerCase", function (y) {
    const s = String(this);
    return turkce(y) ? s.replace(/İ/g, "i").replace(/I/g, "ı").toLowerCase() : s.toLowerCase();
  });
  tanimla(String.prototype, "toLocaleUpperCase", function (y) {
    const s = String(this);
    return turkce(y) ? s.replace(/i/g, "İ").toUpperCase() : s.toUpperCase();
  });

  // ---------------------------------------------------------------- harmanlama (localeCompare)
  // HARMAN_TABLOSU_BAS (op4/testler/js/harman_uret.js üretir; elle değiştirmeyin)
  const HARMAN = {
    icu: "77.1",
    tr: "9:1.1.1,a:2.1.1,d:3.1.1,w:4.1.1,4g:4.1.2,2n:5.1.1,19:6.1.1,6c3:7.1.1,6c4:8.1.1,18:9.1.1,1n:a.1.1,1m:b.1.1,x:c.1.1,4h:d.1.1,1r:e.1.1,5b:f.1.1,1a:g.1.1,6cm:h.1.1,53:i.1.1,13:j.1.1,6c8:j.2.1,6c9:j.3.1,y:k.1.1,6cc:k.2.1,6cd:k.3.1,4r:l.1.1,57:m.1.1,14:n.1.1,15:o.1.1,2j:p.1.1,2l:q.1.1,3f:r.1.1,3h:s.1.1,4n:t.1.1,52:u.1.1,1s:v.1.1,16:w.1.1,1b:x.1.1,2k:y.1.1,12:z.1.1,z:10.1.1,11:11.1.1,6cw:12.1.1,6ci:13.1.1,6cy:14.1.1,6cz:15.1.1,2o:16.1.1,50:17.1.1,2m:18.1.1,4v:19.1.1,4o:1a.1.1,54:1b.1.1,4w:1c.1.1,4p:1d.1.1,4u:1e.1.1,17:1f.1.1,4x:1g.1.1,6v:1h.1.1,5z:1i.1.1,1o:1j.1.1,1p:1k.1.1,1q:1l.1.1,4s:1m.1.1,3g:1n.1.1,4m:1o.1.1,3i:1p.1.1,6qa:1q.1.1,6qm:1r.1.1,6sk:1s.1.1,6sl:1t.1.1,4k:1u.1.1,4i:1v.1.1,10:1w.1.1,4j:1x.1.1,4l:1y.1.1,6gc:1z.1.1,1c:20.1.1,1d:21.1.1,55:21.1.2,59:22.1.1,58:23.1.1,1e:24.1.1,4y:24.1.2,1f:25.1.1,4z:25.1.2,5a:26.1.1,1g:27.1.1,1h:28.1.1,1i:29.1.1,1j:2a.1.1,1k:2b.1.1,1l:2c.1.1,2p:2d.1.1,1t:2d.1.2,4q:2d.1.3,69:2d.2.1,5d:2d.2.2,68:2d.3.1,5c:2d.3.2,77:2d.4.1,76:2d.4.2,6a:2d.5.1,5e:2d.5.2,6d:2d.6.1,5h:2d.6.2,6c:2d.7.1,5g:2d.7.2,6b:2d.8.1,5f:2d.8.2,79:2d.9.1,78:2d.9.2,75:2d.a.1,74:2d.a.2,6e:2e.1.1,5i:2e.1.2,2q:2f.1.1,1u:2f.1.2,2r:2g.1.1,1v:2g.1.2,7b:2g.2.1,7a:2g.2.2,7d:2g.3.1,7c:2g.3.2,7h:2g.4.1,7g:2g.4.2,7f:2g.5.1,7e:2g.5.2,6f:2h.1.1,5j:2h.1.2,2s:2i.1.1,1w:2i.1.2,7j:2i.2.1,7i:2i.2.2,7l:2i.3.1,7k:2i.3.2,6o:2i.4.1,5s:2i.4.2,2t:2j.1.1,1x:2j.1.2,6h:2j.2.1,5l:2j.2.2,6g:2j.3.1,5k:2j.3.2,7p:2j.4.1,7o:2j.4.2,6i:2j.5.1,5m:2j.5.2,7v:2j.6.1,7u:2j.6.2,6j:2j.7.1,5n:2j.7.2,7r:2j.8.1,7q:2j.8.2,7t:2j.9.1,7s:2j.9.2,7n:2j.a.1,7m:2j.a.2,2u:2k.1.1,1y:2k.1.2,2v:2l.1.1,1z:2l.1.2,7x:2l.2.1,7w:2l.2.2,81:2l.3.1,80:2l.3.2,83:2l.4.1,82:2l.4.2,7z:2m.1.1,7y:2m.1.2,2w:2n.1.1,20:2n.1.2,85:2n.2.1,84:2n.2.2,87:2n.3.1,86:2n.3.2,8h:2o.1.1,21:2o.1.2,5p:2o.2.1,5o:2o.3.1,8c:2o.4.1,5q:2o.5.1,5r:2o.6.1,88:2o.7.1,8e:2o.8.1,8a:2o.9.1,2x:2p.1.1,8g:2p.1.2,6l:2p.2.1,6k:2p.3.1,8d:2p.4.1,6m:2p.5.1,6n:2p.6.1,89:2p.7.1,8f:2p.8.1,8b:2p.9.1,8j:2q.1.1,8i:2q.1.2,2y:2r.1.1,22:2r.1.2,8l:2r.2.1,8k:2r.2.2,2z:2s.1.1,23:2s.1.2,8n:2s.2.1,8m:2s.2.2,30:2t.1.1,24:2t.1.2,8q:2t.2.1,8p:2t.2.2,8u:2t.3.1,8t:2t.3.2,8s:2t.4.1,8r:2t.4.2,8y:2t.5.1,8x:2t.5.2,8w:2t.6.1,8v:2t.6.2,31:2u.1.1,25:2u.1.2,32:2v.1.1,26:2v.1.2,90:2v.2.1,8z:2v.2.2,94:2v.3.1,93:2v.3.2,6p:2v.4.1,5t:2v.4.2,92:2v.5.1,91:2v.5.2,97:2w.1.1,96:2w.1.2,33:2x.1.1,27:2x.1.2,56:2x.1.3,6r:2x.2.1,5v:2x.2.2,6q:2x.3.1,5u:2x.3.2,9b:2x.4.1,9a:2x.4.2,6s:2x.5.1,5w:2x.5.2,9d:2x.6.1,9c:2x.6.2,6t:2x.7.1,5x:2x.7.2,6w:2x.8.1,60:2x.8.2,99:2x.9.1,98:2x.9.2,9f:2y.1.1,9e:2y.1.2,6u:2z.1.1,5y:2z.1.2,34:30.1.1,28:30.1.2,35:31.1.1,29:31.1.2,8o:32.1.1,36:33.1.1,2a:33.1.2,9h:33.2.1,9g:33.2.2,9l:33.3.1,9k:33.3.2,9j:33.4.1,9i:33.4.2,37:34.1.1,2b:34.1.2,9n:34.2.1,9m:34.2.2,9p:34.3.1,9o:34.3.2,9t:34.4.1,9s:34.4.2,an:34.5.1,67:35.1.1,9r:36.1.1,9q:36.1.2,38:37.1.1,2c:37.1.2,9x:37.2.1,9w:37.2.2,9v:37.3.1,9u:37.3.2,6jm:38.1.1,9z:39.1.1,9y:39.1.2,39:3a.1.1,2d:3a.1.2,6y:3a.2.1,62:3a.2.2,6x:3a.3.1,61:3a.3.2,a5:3a.4.1,a4:3a.4.2,6z:3a.5.1,63:3a.5.2,a7:3a.6.1,a6:3a.6.2,a9:3a.7.1,a8:3a.7.2,a1:3a.8.1,a0:3a.8.2,ab:3a.9.1,aa:3a.9.2,a3:3a.a.1,a2:3a.a.2,70:3b.1.1,64:3b.1.2,3a:3c.1.1,2e:3c.1.2,3b:3d.1.1,2f:3d.1.2,ad:3d.2.1,ac:3d.2.2,3c:3e.1.1,2g:3e.1.2,3d:3f.1.1,2h:3f.1.2,71:3f.2.1,65:3f.2.2,af:3f.3.1,ae:3f.3.2,73:3f.4.1,ag:3f.4.2,3e:3g.1.1,2i:3g.1.2,ai:3g.2.1,ah:3g.2.2,am:3g.3.1,al:3g.3.2,ak:3g.4.1,aj:3g.4.2,72:3h.1.1,66:3h.1.2,95:3i.1.1,q9:3j.1.1,qa:3k.1.1,qb:3l.1.1,qc:3m.1.1,pg:3m.1.2,qj:3n.1.1,qk:3o.1.1,51:3o.1.2,qo:3p.1.1,qr:3q.1.1,pv:3q.1.2,qu:3r.1.1",
    kok: "9:1.1.1,a:2.1.1,d:3.1.1,w:4.1.1,4g:4.1.2,2n:5.1.1,19:6.1.1,6c3:7.1.1,6c4:8.1.1,18:9.1.1,1n:a.1.1,1m:b.1.1,x:c.1.1,4h:d.1.1,1r:e.1.1,5b:f.1.1,1a:g.1.1,6cm:h.1.1,53:i.1.1,13:j.1.1,6c8:j.2.1,6c9:j.3.1,y:k.1.1,6cc:k.2.1,6cd:k.3.1,4r:l.1.1,57:m.1.1,14:n.1.1,15:o.1.1,2j:p.1.1,2l:q.1.1,3f:r.1.1,3h:s.1.1,4n:t.1.1,52:u.1.1,1s:v.1.1,16:w.1.1,1b:x.1.1,2k:y.1.1,12:z.1.1,z:10.1.1,11:11.1.1,6cw:12.1.1,6ci:13.1.1,6cy:14.1.1,6cz:15.1.1,2o:16.1.1,50:17.1.1,2m:18.1.1,4v:19.1.1,4o:1a.1.1,54:1b.1.1,4w:1c.1.1,4p:1d.1.1,4u:1e.1.1,17:1f.1.1,4x:1g.1.1,6v:1h.1.1,5z:1i.1.1,1o:1j.1.1,1p:1k.1.1,1q:1l.1.1,4s:1m.1.1,3g:1n.1.1,4m:1o.1.1,3i:1p.1.1,6qa:1q.1.1,6qm:1r.1.1,6sk:1s.1.1,6sl:1t.1.1,4k:1u.1.1,4i:1v.1.1,10:1w.1.1,4j:1x.1.1,4l:1y.1.1,6gc:1z.1.1,1c:20.1.1,1d:21.1.1,55:21.1.2,59:22.1.1,58:23.1.1,1e:24.1.1,4y:24.1.2,1f:25.1.1,4z:25.1.2,5a:26.1.1,1g:27.1.1,1h:28.1.1,1i:29.1.1,1j:2a.1.1,1k:2b.1.1,1l:2c.1.1,2p:2d.1.1,1t:2d.1.2,4q:2d.1.3,69:2d.2.1,5d:2d.2.2,68:2d.3.1,5c:2d.3.2,77:2d.4.1,76:2d.4.2,6a:2d.5.1,5e:2d.5.2,6d:2d.6.1,5h:2d.6.2,6c:2d.7.1,5g:2d.7.2,6b:2d.8.1,5f:2d.8.2,79:2d.9.1,78:2d.9.2,75:2d.a.1,74:2d.a.2,6e:2e.1.1,5i:2e.1.2,2q:2f.1.1,1u:2f.1.2,2r:2g.1.1,1v:2g.1.2,7b:2g.2.1,7a:2g.2.2,7d:2g.3.1,7c:2g.3.2,7h:2g.4.1,7g:2g.4.2,7f:2g.5.1,7e:2g.5.2,6f:2g.6.1,5j:2g.6.2,2s:2h.1.1,1w:2h.1.2,7j:2h.2.1,7i:2h.2.2,7l:2h.3.1,7k:2h.3.2,6o:2h.4.1,5s:2h.4.2,2t:2i.1.1,1x:2i.1.2,6h:2i.2.1,5l:2i.2.2,6g:2i.3.1,5k:2i.3.2,7p:2i.4.1,7o:2i.4.2,6i:2i.5.1,5m:2i.5.2,7v:2i.6.1,7u:2i.6.2,6j:2i.7.1,5n:2i.7.2,7r:2i.8.1,7q:2i.8.2,7t:2i.9.1,7s:2i.9.2,7n:2i.a.1,7m:2i.a.2,2u:2j.1.1,1y:2j.1.2,2v:2k.1.1,1z:2k.1.2,7z:2k.2.1,7y:2k.2.2,7x:2k.3.1,7w:2k.3.2,81:2k.4.1,80:2k.4.2,83:2k.5.1,82:2k.5.2,2w:2l.1.1,20:2l.1.2,85:2l.2.1,84:2l.2.2,87:2l.3.1,86:2l.3.2,2x:2m.1.1,21:2m.1.2,6l:2m.2.1,5p:2m.2.2,6k:2m.3.1,5o:2m.3.2,8d:2m.4.1,8c:2m.4.2,6m:2m.5.1,5q:2m.5.2,6n:2m.6.1,5r:2m.6.2,89:2m.7.1,88:2m.7.2,8g:2m.8.1,8f:2m.9.1,8e:2m.9.2,8b:2m.a.1,8a:2m.a.2,8j:2n.1.1,8i:2n.1.2,8h:2o.1.1,2y:2p.1.1,22:2p.1.2,8l:2p.2.1,8k:2p.2.2,2z:2q.1.1,23:2q.1.2,8n:2q.2.1,8m:2q.2.2,30:2r.1.1,24:2r.1.2,8q:2r.2.1,8p:2r.2.2,8u:2r.3.1,8t:2r.3.2,8s:2r.4.1,8r:2r.4.2,8y:2r.5.1,8x:2r.5.2,8w:2r.6.1,8v:2r.6.2,31:2s.1.1,25:2s.1.2,32:2t.1.1,26:2t.1.2,90:2t.2.1,8z:2t.2.2,94:2t.3.1,93:2t.3.2,6p:2t.4.1,5t:2t.4.2,92:2t.5.1,91:2t.5.2,97:2u.1.1,96:2u.1.2,33:2v.1.1,27:2v.1.2,56:2v.1.3,6r:2v.2.1,5v:2v.2.2,6q:2v.3.1,5u:2v.3.2,9b:2v.4.1,9a:2v.4.2,6s:2v.5.1,5w:2v.5.2,6u:2v.6.1,5y:2v.6.2,9d:2v.7.1,9c:2v.7.2,6t:2v.8.1,5x:2v.8.2,6w:2v.9.1,60:2v.9.2,99:2v.a.1,98:2v.a.2,9f:2w.1.1,9e:2w.1.2,34:2x.1.1,28:2x.1.2,35:2y.1.1,29:2y.1.2,8o:2z.1.1,36:30.1.1,2a:30.1.2,9h:30.2.1,9g:30.2.2,9l:30.3.1,9k:30.3.2,9j:30.4.1,9i:30.4.2,37:31.1.1,2b:31.1.2,9n:31.2.1,9m:31.2.2,9p:31.3.1,9o:31.3.2,9t:31.4.1,9s:31.4.2,9r:31.5.1,9q:31.5.2,an:31.6.1,67:32.1.1,38:33.1.1,2c:33.1.2,9x:33.2.1,9w:33.2.2,9v:33.3.1,9u:33.3.2,6jm:34.1.1,9z:35.1.1,9y:35.1.2,39:36.1.1,2d:36.1.2,6y:36.2.1,62:36.2.2,6x:36.3.1,61:36.3.2,a5:36.4.1,a4:36.4.2,6z:36.5.1,63:36.5.2,a7:36.6.1,a6:36.6.2,70:36.7.1,64:36.7.2,a9:36.8.1,a8:36.8.2,a1:36.9.1,a0:36.9.2,ab:36.a.1,aa:36.a.2,a3:36.b.1,a2:36.b.2,3a:37.1.1,2e:37.1.2,3b:38.1.1,2f:38.1.2,ad:38.2.1,ac:38.2.2,3c:39.1.1,2g:39.1.2,3d:3a.1.1,2h:3a.1.2,71:3a.2.1,65:3a.2.2,af:3a.3.1,ae:3a.3.2,73:3a.4.1,ag:3a.4.2,3e:3b.1.1,2i:3b.1.2,ai:3b.2.1,ah:3b.2.2,am:3b.3.1,al:3b.3.2,ak:3b.4.1,aj:3b.4.2,72:3c.1.1,66:3c.1.2,95:3d.1.1,q9:3e.1.1,qa:3f.1.1,qb:3g.1.1,qc:3h.1.1,pg:3h.1.2,qj:3i.1.1,qk:3j.1.1,51:3j.1.2,qo:3k.1.1,qr:3l.1.1,pv:3l.1.2,qu:3m.1.1",
  };
  // HARMAN_TABLOSU_SON
  const tablolar = {};
  function tabloAl(ad) {
    let t = tablolar[ad];
    if (!t) {
      t = new Map();
      for (const x of HARMAN[ad].split(",")) {
        if (!x) continue;
        const i = x.indexOf(":"), w = x.slice(i + 1).split(".");
        t.set(parseInt(x.slice(0, i), 36), [parseInt(w[0], 36), parseInt(w[1], 36), parseInt(w[2], 36)]);
      }
      tablolar[ad] = t;
    }
    return t;
  }
  const ACILIM = { 0xdf: "ss", 0xe6: "ae", 0xc6: "AE", 0x153: "oe", 0x152: "OE" };   // ICU açılımları (ß = ss …)
  const BILINMEYEN = 0x10000;
  function yoksayilir(c) {
    return (c < 0x20 && c !== 0x09 && c !== 0x0a && c !== 0x0d) || (c >= 0x7f && c <= 0x9f) || c === 0xad ||
      (c >= 0x200b && c <= 0x200f) || c === 0xfeff;
  }
  /** Üç düzeyin ağırlık dizileri: P (birincil), S (ikincil), U (üçüncül). */
  function harmanAnahtari(s, ad, sayisal) {
    const T = tabloAl(ad), P = [], S = [], U = [];
    const sifir = T.get(0x30);
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      if (sayisal && c >= 0x30 && c <= 0x39) {
        let j = i;
        while (j < s.length && s.charCodeAt(j) >= 0x30 && s.charCodeAt(j) <= 0x39) j++;
        let k = i;
        while (k < j && s.charCodeAt(k) === 0x30) k++;
        P.push(sifir[0], j - k);
        S.push(1, 1); U.push(1, 1);
        for (let q = k; q < j; q++) { P.push(s.charCodeAt(q) - 0x2f); S.push(1); U.push(1); }
        i = j - 1;
        continue;
      }
      if (ACILIM[c]) {
        const a = ACILIM[c];
        for (let q = 0; q < a.length; q++) { const w = T.get(a.charCodeAt(q)); P.push(w[0]); S.push(w[1] + (q ? 0 : 8)); U.push(w[2]); }
        continue;
      }
      const w = T.get(c);
      if (w) { P.push(w[0]); S.push(w[1]); U.push(w[2]); continue; }
      if (c >= 0x300 && c <= 0x36f) { S.push(0x100 + c - 0x300); continue; }   // birleşen aksan: yalnız ikincil
      if (yoksayilir(c)) continue;
      P.push(BILINMEYEN + c); S.push(1); U.push(1);
    }
    return { P: P, S: S, U: U };
  }
  function diziKarsilastir(a, b) {
    const n = a.length < b.length ? a.length : b.length;
    for (let i = 0; i < n; i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
    return a.length === b.length ? 0 : (a.length < b.length ? -1 : 1);
  }
  function harmanla(a, b, yerel, secenek) {
    const y = Array.isArray(yerel) ? yerel[0] : yerel, o = secenek || {};
    const ad = typeof y === "string" && /^(tr|az)(-|_|$)/i.test(y) ? "tr" : "kok";
    const sayisal = o.numeric === true || (typeof y === "string" && /-u(-[a-z0-9]+)*-kn(-true)?(-|$)/i.test(y));
    const duyarlik = o.sensitivity || "variant";
    if (a === b) return 0;
    const A = harmanAnahtari(a, ad, sayisal), B = harmanAnahtari(b, ad, sayisal);
    let r = diziKarsilastir(A.P, B.P);
    if (r) return r;
    if (duyarlik === "accent" || duyarlik === "variant") { r = diziKarsilastir(A.S, B.S); if (r) return r; }
    if (duyarlik === "case" || duyarlik === "variant") { r = diziKarsilastir(A.U, B.U); if (r) return r; }
    return 0;
  }
  tanimla(String.prototype, "localeCompare", function (b, yerel, secenek) {
    return harmanla(String(this), String(b), yerel, secenek);
  });

  // ---------------------------------------------------------------- TextDecoder (WHATWG Encoding; utf-8, windows-1254)
  if (typeof g.TextDecoder !== "function" || g.__op4_oykunme_zorla === true) {
    const ETIKETLER = {
      "unicode-1-1-utf-8": "utf-8", "unicode11utf8": "utf-8", "unicode20utf8": "utf-8", "utf-8": "utf-8", "utf8": "utf-8",
      "x-unicode20utf8": "utf-8", "cp1254": "windows-1254", "csisolatin5": "windows-1254", "iso-8859-9": "windows-1254",
      "iso-ir-148": "windows-1254", "iso8859-9": "windows-1254", "iso88599": "windows-1254", "iso_8859-9": "windows-1254",
      "iso_8859-9:1989": "windows-1254", "l5": "windows-1254", "latin5": "windows-1254", "windows-1254": "windows-1254",
      "x-cp1254": "windows-1254",
    };
    // windows-1254 0x80–0x9F (WHATWG index); 0xA0–0xFF Latin-1, altı Türkçe harf dışında
    const W1254_80 = [0x20ac, 0x81, 0x201a, 0x192, 0x201e, 0x2026, 0x2020, 0x2021, 0x2c6, 0x2030, 0x160, 0x2039, 0x152, 0x8d, 0x8e,
      0x8f, 0x90, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2013, 0x2014, 0x2dc, 0x2122, 0x161, 0x203a, 0x153, 0x9d, 0x9e, 0x178];
    const W1254_TR = { 0xd0: 0x11e, 0xdd: 0x130, 0xde: 0x15e, 0xf0: 0x11f, 0xfd: 0x131, 0xfe: 0x15f };
    const kodNoktalari = function (l) {
      let s = "";
      for (let i = 0; i < l.length; i += 4096) s += String.fromCodePoint.apply(null, l.slice(i, i + 4096));
      return s;
    };
    class TextDecoder {
      constructor(etiket, secenek) {
        const e = String(etiket === undefined ? "utf-8" : etiket).trim().toLowerCase();
        const ad = Object.prototype.hasOwnProperty.call(ETIKETLER, e) ? ETIKETLER[e] : null;
        if (!ad) throw new RangeError("The \"" + etiket + "\" encoding is not supported");
        this._ad = ad;
        this._fatal = !!(secenek && secenek.fatal);
        this._bomYok = !!(secenek && secenek.ignoreBOM);
      }
      get encoding() { return this._ad; }
      get fatal() { return this._fatal; }
      get ignoreBOM() { return this._bomYok; }
      decode(girdi) {
        let u;
        if (girdi === undefined || girdi === null) u = new Uint8Array(0);
        else if (girdi instanceof ArrayBuffer) u = new Uint8Array(girdi);
        else if (ArrayBuffer.isView(girdi)) u = new Uint8Array(girdi.buffer, girdi.byteOffset, girdi.byteLength);
        else throw new TypeError("The \"input\" argument must be an instance of ArrayBuffer or ArrayBufferView");
        const out = [];
        if (this._ad === "windows-1254") {
          for (let i = 0; i < u.length; i++) { const b = u[i]; out.push(b < 0x80 ? b : b < 0xa0 ? W1254_80[b - 0x80] : (W1254_TR[b] || b)); }
          return kodNoktalari(out);
        }
        const fatal = this._fatal;
        const hata = function () {
          if (fatal) throw new TypeError("The encoded data was not valid for encoding utf-8");
          out.push(0xfffd);
        };
        let cp = 0, gerekli = 0, gorulen = 0, alt = 0x80, ust = 0xbf;
        for (let i = 0; i < u.length; i++) {
          const b = u[i];
          if (gerekli === 0) {
            if (b <= 0x7f) out.push(b);
            else if (b >= 0xc2 && b <= 0xdf) { gerekli = 1; cp = b & 0x1f; }
            else if (b >= 0xe0 && b <= 0xef) { if (b === 0xe0) alt = 0xa0; if (b === 0xed) ust = 0x9f; gerekli = 2; cp = b & 0x0f; }
            else if (b >= 0xf0 && b <= 0xf4) { if (b === 0xf0) alt = 0x90; if (b === 0xf4) ust = 0x8f; gerekli = 3; cp = b & 0x07; }
            else hata();
            continue;
          }
          if (b < alt || b > ust) {
            cp = gerekli = gorulen = 0; alt = 0x80; ust = 0xbf;
            hata();
            i--;                    // bayt yeniden işlenir
            continue;
          }
          alt = 0x80; ust = 0xbf;
          cp = (cp << 6) | (b & 0x3f);
          if (++gorulen === gerekli) { out.push(cp); cp = gerekli = gorulen = 0; }
        }
        if (gerekli) hata();
        if (!this._bomYok && out.length && out[0] === 0xfeff) out.shift();
        return kodNoktalari(out);
      }
    }
    g.TextDecoder = TextDecoder;
  }
})(globalThis);
