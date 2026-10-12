/* Matris Öğren · etkileşim çekirdeği (docs/etkilesim.js)
 *
 * Ders sayfalarındaki etkileşimli çizimlerin ve alıştırmaların ortak altyapısı. Bağımlılığı yok;
 * KaTeX yüklüyse formülleri onunla basar, yoksa okunur düz metne düşer.
 *
 * KAYIT VE KURULUM
 *   Etkilesim.kaydet(ad, kurucu, { baslik, aciklama, varsayilan })
 *     kurucu(kok, param, E) içeriği kökün içine kurar, isteğe bağlı { yok_et() } döndürür.
 *     Başlığı çağıran çizer (galeri ya da ders sayfası); kurucu yalnız içeriği kurar.
 *   Etkilesim.kur(kok, ad, param)  param = varsayilan + param. Kurucu hata atarsa kökte "Etkileşim açılamadı" yazar.
 *     kok.dataset.durum: "hazir" | "hata" | "yok".
 *   Etkilesim.temizle(kok)         yok_et() çağırır, kökü boşaltır (iç içe kurulanlar da kapanır).
 *   Alıştırmalar "alistirma:<ad>" adıyla kaydedilir:
 *     E.kaydet("alistirma:carpim", (kok, p) => E.alistirmaKur(kok, p, uret), { baslik: "…" });
 *   İçerik dosyaları (etkilesim_matris.js, etkilesim_se.js) şu kalıbı izler:
 *     (function (E) { "use strict"; if (!E) return; E.kaydet("…", function (kok, p) { … }, { … }); })(window.Etkilesim);
 *
 * ÇİZİM YARDIMCILARI (SVG koordinatları kök <svg> viewBox birimidir)
 *   el(etiket, oz, ...cocuklar) / svg(etiket, oz, ...cocuklar)
 *     oz: class (metin | dizi), text, html (yalnız güvenilir içerik), style {…}, dataset {…}, on<olay>: işlev.
 *     fill / stroke / color değeri var(…) içeriyorsa style'a yazılır (iOS ve Firefox'ta da tema rengi çalışsın diye).
 *   sahne(gen, yuk, etiket) → <svg viewBox="0 0 gen yuk"> (telefonda küçülür).
 *   renk(aile) / zemin(aile): aile a | b | c | sil | cizgi ya da metin | soluk | ana | vurgu | kenar | kart.
 *     Ok şemasıyla aynı renk aileleri; açık ve koyu temada otomatik.
 *   ok(x1, y1, x2, y2, { renk, egri, kalinlik, bas, kesik, ciz, gecikme, etiket, sinif }) → <g>
 *     egri: ±0.2 gibi bükülme; ciz: çizilerek belirir; gecikme: saniye (sıralı oklar için).
 *   yazi(x, y, metin, { renk, hiza: "sol" | "orta" | "sag", kalin, boyut, sinif }) → <text>
 *   matrisCiz(A, { x, y, hucre, hucreY, bicim, izgara, parantez, yaziBoya, sinif })
 *     → { g, m, n, genislik, yukseklik, hucre(i, j) → {x, y, w, h, cx, cy}, boya(i, j, aile), satirBoya(i, aile),
 *         sutunBoya(j, aile), kutu(i0, j0, i1, j1, aile, { kesik, dolgu, kalinlik }), yaz(i, j, metin), sifirla() }
 *     i, j 0 tabanlıdır; hucre() koordinatları x, y kaydırması eklenmiş hâlde verir (oklar için).
 *   kaydirici({ etiket, min, max, adim, deger, birim, bicim, degisince }) → { kok, girdi, deger(), ayarla(v, sessiz) }
 *   dugme(metin, islev, { ana, baslik, aria, sinif }) → <button>  (ana: true dolu ana düğme)
 *   secici(secenekler, deger, degisince) → { kok, deger(), ayarla(v, sessiz) }; secenekler ["a", "b"] ya da [{ deger, etiket }]
 *   surukle(eleman, { svg, basla(p), tasi(p), birak(p), klavye(dx, dy) }) → kaldir()   p = { x, y } viewBox biriminde
 *   svgNokta(svg, olay) → { x, y }
 *   animasyon(kok, (t, dt) => …) → { durdur(), devam(), calisiyor(), sifirla() }; false döndürünce durur,
 *     ekran dışındayken bekler, kök sayfadan çıkınca kendiliğinden durur.
 *   hareketAzalt() true ise animasyonu atla, son kareyi çiz.
 *
 * MATEMATİK
 *   KaTeX makroları: \ka{…} \kb{…} \kc{…} \ksil{…} renkli yazı, \kutua{…} \kutub{…} \kutuc{…} \kutusil{…} renkli kutu.
 *   tex(kok, kaynak, blok), texDugum(kaynak, blok), metinDugum("metin $x^2$ ve **kalın** metin").
 *   Kesir: kesin rasyonel sayı (BigInt). Kesir.al(3 | "5/2" | "-2,5" | "1e-3"), Kesir.sayidan(0.3333) → 1/3.
 *     topla cikar carp bol us ters neg esit karsilastir isaret mutlak sayi tamMi toString tex ondalik.
 *   Mat: Kesir'lerden matris. Mat.al("1 2; 3 4" | "1, 2; 3, 4" | [[1, 2], [3, 4]] | [1, 2] (sütun)).
 *     m, n, g(i, j), satir, sutun, harita, topla, cikar, skaler, carp, transpoz, minor, kofaktor, iz, det, ters, coz,
 *     esit, tex({ vurgu: { "i,j": "kutua" } | (i, j, x) => makro, ortam, bicim }), metin, sayilar.
 *     Mat.birim(n), Mat.sifir(m, n), Mat.rastgele(rnd, m, n, alt, ust, sifirsiz).
 *   sayi(x, basamak = 4) / sayiTex(x): ondalık nokta "." (motorla aynı); çok büyük ya da küçük sayılar 1.2e-5
 *     ya da 1.2 \times 10^{-5}.
 *   rastgele(tohum) → { sayi(), tam(a, b), sec(d), sifirsiz(a, b), karistir(d) } (aynı tohum, aynı sorular).
 *
 * ALIŞTIRMA · alistirmaKur(kok, param, uret, { giris })
 *   uret(rnd, param) bir soru nesnesi ya da null döndürür (null ya da hata: başka tohumla en çok 20 deneme):
 *     { metin, tex, sekil, cevap (Mat | 2B dizi | sayı), etiket, alanlar: ["$u_2$", …],
 *       tolerans: "tam" (varsayılan) | "yaklasik" | sayı, ipucu (metin | dizi), aciklama,
 *       adimlar: [{ metin, tex } | metin], motor: { islem, girdi }, bicim(x), denetle(degerler) → { dogru, hucreler?, mesaj? } }
 *   "tam": kesin eşitlik ya da en az 3 anlamlı basamakla doğru yuvarlanmış ondalık kabul edilir.
 *   "yaklasik": ayrıca göreli hata ≤ 1e-3 (sayı verilirse o tolerans) kabul edilir.
 *   denetle: cevabı tek olmayan sorular için (ör. özvektör); degerler Kesir'lerden 2B dizidir.
 *   param.tohum verilirse sorular tekrarlanabilir.
 *
 * MOTOR
 *   Uygulama motorBagla(istek => Promise<yanit>, (yanit, hedef) => çiz) ile bağlar. istek web_kopru biçimindedir:
 *   { islem: "carp", girdi: { A: "1 2; 3 4", B: "5 6; 7 8" } } (ayarları uygulama ekler).
 *   Bağlı değilse "Adım adım çözüm" düğmesi sorunun yerel adımlarını gösterir.
 */
(function (pencere) {
  "use strict";
  if (pencere.Etkilesim && pencere.Etkilesim.surum) return; // iki kez yüklenirse kayıtları koru

  const SURUM = "1.0.0";
  const SVG_NS = "http://www.w3.org/2000/svg";
  const KAYIT = new Map();
  const MOTOR_YOK = "Adım adım çözüm uygulamanın içinde çalışır (motor bu sayfada yüklü değil).";
  const OKUNAMADI = "Okunamayan bir değer var. Tam sayı (−3), kesir (5/2) ya da ondalık (2.5 veya 2,5) yazabilirsin.";
  let E = null; // dışa açılan nesne; dosyanın sonunda doldurulur

  /* ------------------------------------------------------------------ kayıt */

  function kaydet(ad, kurucu, meta) {
    if (typeof ad !== "string" || !ad) throw new TypeError("kaydet: ad gerekli");
    if (typeof kurucu !== "function") throw new TypeError("kaydet: kurucu bir işlev olmalı");
    if (KAYIT.has(ad)) console.warn("Etkilesim: '" + ad + "' yeniden kaydediliyor");
    const m = Object.assign({ baslik: ad, aciklama: "", varsayilan: {} }, meta || {});
    KAYIT.set(ad, { ad, kurucu, meta: m });
  }

  function liste(onEk) {
    const adlar = Array.from(KAYIT.keys());
    return onEk ? adlar.filter(a => a.startsWith(onEk)) : adlar;
  }

  function bilgi(ad) {
    const k = KAYIT.get(ad);
    if (!k) return null;
    return {
      ad,
      baslik: k.meta.baslik,
      aciklama: k.meta.aciklama,
      varsayilan: Object.assign({}, k.meta.varsayilan),
      alistirma: ad.startsWith("alistirma:")
    };
  }

  function kur(kok, ad, param) {
    if (!kok) throw new TypeError("kur: kök eleman gerekli");
    temelStil();
    temizle(kok);
    kok.classList.add("kx-kok");
    kok.dataset.etkilesim = ad;
    const k = KAYIT.get(ad);
    if (!k) {
      kok.dataset.durum = "yok";
      kok.appendChild(el("p", { class: "kx-not" }, "Bu etkileşim bu sürümde yok: " + ad));
      return null;
    }
    const p = Object.assign({}, k.meta.varsayilan, param || {});
    try {
      const api = k.kurucu(kok, p, E) || {};
      kok._kx = api;
      kok.dataset.durum = "hazir";
      return api;
    } catch (h) {
      console.error("Etkilesim '" + ad + "' kurulamadı:", h);
      bosalt(kok);
      kok.dataset.durum = "hata";
      kok.appendChild(el("p", { class: "kx-hata" }, "Etkileşim açılamadı: " + hataMetni(h)));
      return null;
    }
  }

  function temizle(kok) {
    if (!kok) return;
    if (kok.querySelectorAll) {
      kok.querySelectorAll(".kx-kok").forEach(alt => { if (alt._kx) yokEt(alt); });
    }
    yokEt(kok);
    bosalt(kok);
    if (kok.dataset) delete kok.dataset.durum;
  }

  function yokEt(d) {
    const api = d._kx;
    d._kx = null;
    if (api && typeof api.yok_et === "function") {
      try { api.yok_et(); } catch (h) { console.warn("Etkilesim yok_et:", h); }
    }
  }

  function bosalt(d) {
    if (typeof d.replaceChildren === "function") d.replaceChildren();
    else d.textContent = "";
  }

  function hataMetni(h) {
    return h && h.message ? h.message : String(h);
  }

  /* ------------------------------------------------------------------ DOM */

  const RENK_OZ = new Set(["fill", "stroke", "color", "stop-color"]);

  function dugumMu(x) {
    return typeof Node !== "undefined" && x instanceof Node;
  }

  function kebap(ad) {
    return ad.startsWith("--") ? ad : ad.replace(/[A-Z]/g, h => "-" + h.toLowerCase());
  }

  function ozYaz(d, oz) {
    for (const ad of Object.keys(oz)) {
      const v = oz[ad];
      if (v === null || v === undefined || v === false) continue;
      if (ad === "class") {
        const s = Array.isArray(v) ? v.filter(Boolean).join(" ") : String(v);
        if (s) d.setAttribute("class", s);
      } else if (ad === "text") {
        d.textContent = String(v);
      } else if (ad === "html") {
        d.innerHTML = String(v); // yalnız güvenilir içerik (KaTeX çıktısı gibi)
      } else if (ad === "style" && typeof v === "object") {
        for (const k of Object.keys(v)) {
          const s = v[k];
          if (s === null || s === undefined || s === false) continue;
          d.style.setProperty(kebap(k), String(s));
        }
      } else if (ad === "dataset" && typeof v === "object") {
        Object.assign(d.dataset, v);
      } else if (ad.length > 2 && ad.startsWith("on") && typeof v === "function") {
        d.addEventListener(ad.slice(2).toLowerCase(), v);
      } else if (RENK_OZ.has(ad) && typeof v === "string" && v.indexOf("var(") >= 0) {
        d.style.setProperty(ad, v);
      } else {
        d.setAttribute(ad, v === true ? "" : String(v));
      }
    }
  }

  function cocukEkle(d, cocuklar) {
    for (const c of cocuklar) {
      if (c === null || c === undefined || c === false || c === true) continue;
      if (Array.isArray(c)) cocukEkle(d, c);
      else if (dugumMu(c)) d.appendChild(c);
      else d.appendChild(document.createTextNode(String(c)));
    }
  }

  function yap(d, oz, cocuklar) {
    if (oz !== null && oz !== undefined && (typeof oz !== "object" || Array.isArray(oz) || dugumMu(oz))) {
      cocuklar.unshift(oz);
      oz = null;
    }
    if (oz) ozYaz(d, oz);
    cocukEkle(d, cocuklar);
    return d;
  }

  function el(etiket, oz, ...cocuklar) {
    return yap(document.createElement(etiket), oz, cocuklar);
  }

  function svg(etiket, oz, ...cocuklar) {
    return yap(document.createElementNS(SVG_NS, etiket), oz, cocuklar);
  }

  function sahne(gen, yuk, etiket) {
    return svg("svg", {
      class: "kx-svg", viewBox: "0 0 " + gen + " " + yuk, width: gen, height: yuk,
      role: "img", "aria-label": etiket || null, preserveAspectRatio: "xMidYMid meet"
    });
  }

  /* ------------------------------------------------------------------ renkler */

  const AILELER = Object.freeze({ a: "#2563eb", b: "#d97706", c: "#059669", sil: "#dc2626", cizgi: "#64748b" });
  const ZEMINLER = Object.freeze({
    a: "rgba(37,99,235,.12)", b: "rgba(217,119,6,.14)", c: "rgba(5,150,105,.13)",
    sil: "rgba(220,38,38,.11)", cizgi: "rgba(100,116,139,.12)"
  });
  const TEMA = Object.freeze({
    metin: "var(--metin,#15213a)", soluk: "var(--soluk,#5b6b85)", ana: "var(--ana,#1e3a8a)",
    vurgu: "var(--vurgu,#0e9f8f)", kenar: "var(--cizgi,#d9e1ee)", kart: "var(--kart,#fff)",
    arka: "var(--arka,#f3f6fb)", "ana-acik": "var(--ana-acik,#e4ebfa)"
  });

  function renk(aile) {
    if (!aile) return "currentColor";
    if (AILELER[aile]) return "var(--sema-" + aile + "," + AILELER[aile] + ")";
    return TEMA[aile] || aile;
  }

  function zemin(aile) {
    if (ZEMINLER[aile]) return "var(--sema-" + aile + "-bg," + ZEMINLER[aile] + ")";
    if (aile === "ana") return TEMA["ana-acik"];
    return TEMA[aile] || aile || "transparent";
  }

  /* ------------------------------------------------------------------ SVG çizim */

  function yuvarla(n) {
    return Math.round(n * 100) / 100;
  }

  function ok(x1, y1, x2, y2, s) {
    s = s || {};
    const r = renk(s.renk || "a");
    const kal = s.kalinlik || 2, bas = s.bas || 7, egri = s.egri || 0;
    const dx = x2 - x1, dy = y2 - y1;
    let d, tx, ty, ox, oy;
    if (egri) {
      const cx = (x1 + x2) / 2 - dy * egri, cy = (y1 + y2) / 2 + dx * egri;
      d = "M" + yuvarla(x1) + " " + yuvarla(y1) + " Q" + yuvarla(cx) + " " + yuvarla(cy) + " " + yuvarla(x2) + " " + yuvarla(y2);
      tx = x2 - cx; ty = y2 - cy;
      ox = (x1 + 2 * cx + x2) / 4; oy = (y1 + 2 * cy + y2) / 4;
    } else {
      d = "M" + yuvarla(x1) + " " + yuvarla(y1) + " L" + yuvarla(x2) + " " + yuvarla(y2);
      tx = dx; ty = dy;
      ox = (x1 + x2) / 2; oy = (y1 + y2) / 2;
    }
    const L = Math.hypot(tx, ty) || 1, ux = tx / L, uy = ty / L;
    const cs = Math.cos(0.5), sn = Math.sin(0.5);
    const p1x = x2 - bas * (ux * cs - uy * sn), p1y = y2 - bas * (ux * sn + uy * cs);
    const p2x = x2 - bas * (ux * cs + uy * sn), p2y = y2 - bas * (-ux * sn + uy * cs);
    const ciz = !!s.ciz && !s.kesik && !hareketAzalt();
    const gecikme = s.gecikme || 0;
    const g = svg("g", { class: ["kx-ok-g", s.sinif] });
    g.appendChild(svg("path", {
      class: ["kx-ok", ciz && "kx-ciz"], d, fill: "none", "stroke-width": kal,
      pathLength: ciz ? 1 : null, "stroke-dasharray": s.kesik ? "5 4" : null,
      style: { stroke: r, animationDelay: ciz && gecikme ? gecikme + "s" : null }
    }));
    g.appendChild(svg("polyline", {
      class: ["kx-ok-uc", ciz && "kx-ciz-uc"], fill: "none", "stroke-width": kal,
      points: yuvarla(p1x) + "," + yuvarla(p1y) + " " + yuvarla(x2) + "," + yuvarla(y2) + " " + yuvarla(p2x) + "," + yuvarla(p2y),
      style: { stroke: r, animationDelay: ciz ? (gecikme + 0.55) + "s" : null }
    }));
    if (s.etiket !== undefined && s.etiket !== null && s.etiket !== "") {
      // eğri oklarda etiket bükülmenin dışına, düz oklarda okun üstüne
      const n = Math.hypot(dx, dy) || 1;
      const nx = egri ? (-dy / n) * Math.sign(egri) : dy / n;
      const ny = egri ? (dx / n) * Math.sign(egri) : -dx / n;
      g.appendChild(yazi(ox + nx * 11, oy + ny * 11, s.etiket, { renk: s.renk || "a", boyut: 12, sinif: "kx-ok-etiket" }));
    }
    return g;
  }

  function yazi(x, y, metin, s) {
    s = s || {};
    const hiza = s.hiza === "sol" ? "start" : s.hiza === "sag" ? "end" : "middle";
    return svg("text", {
      x: yuvarla(x), y: yuvarla(y), dy: "0.35em", "text-anchor": hiza, class: ["kx-yazi", s.sinif],
      style: { fill: s.renk ? renk(s.renk) : null, fontSize: s.boyut ? s.boyut + "px" : null, fontWeight: s.kalin ? 700 : null }
    }, String(metin));
  }

  function hucreMetni(x, bicim) {
    if (bicim) return String(bicim(x));
    return x instanceof Kesir ? x.toString() : String(x);
  }

  function matrisCiz(A, s) {
    s = Object.assign({ x: 0, y: 0, hucre: 44, hucreY: null, bicim: null, izgara: false, parantez: true, yaziBoya: false, sinif: null }, s || {});
    let veri;
    if (A instanceof Mat) veri = A.v;
    else if (Array.isArray(A) && A.length) veri = Array.isArray(A[0]) ? A : A.map(x => [x]);
    else veri = Mat.al(A).v;
    const m = veri.length, n = veri[0].length;
    const w = s.hucre, h = s.hucreY || s.hucre, pay = s.parantez ? 8 : 0;
    const gen = n * w + 2 * pay, yuk = m * h;
    const g = svg("g", { class: ["kx-matris", s.izgara && "izgarali", s.sinif], transform: "translate(" + yuvarla(s.x) + " " + yuvarla(s.y) + ")" });
    const zeminler = svg("g", { class: "kx-matris-zemin" });
    const yazilar = svg("g", { class: "kx-matris-yazi" });
    const kutular = svg("g", { class: "kx-matris-kutu" });
    const hucreler = [];
    for (let i = 0; i < m; i++) {
      const satir = [];
      for (let j = 0; j < n; j++) {
        const x0 = pay + j * w, y0 = i * h;
        const rect = svg("rect", { class: "kx-hucre", x: x0 + 1.5, y: y0 + 1.5, width: w - 3, height: h - 3, rx: 6 });
        const t = yazi(x0 + w / 2, y0 + h / 2, hucreMetni(veri[i][j], s.bicim), { sinif: "kx-hucre-yazi" });
        zeminler.appendChild(rect);
        yazilar.appendChild(t);
        satir.push({ rect, t });
      }
      hucreler.push(satir);
    }
    g.append(zeminler, yazilar);
    if (s.parantez) {
      g.appendChild(svg("path", { class: "kx-parantez", fill: "none", d: "M" + (pay - 1) + " 1 H2 V" + (yuk - 1) + " H" + (pay - 1) }));
      g.appendChild(svg("path", { class: "kx-parantez", fill: "none", d: "M" + (gen - pay + 1) + " 1 H" + (gen - 2) + " V" + (yuk - 1) + " H" + (gen - pay + 1) }));
    }
    g.appendChild(kutular);
    const api = {
      g, m, n, genislik: gen, yukseklik: yuk,
      hucre(i, j) {
        const x = s.x + pay + j * w, y = s.y + i * h;
        return { x, y, w, h, cx: x + w / 2, cy: y + h / 2 };
      },
      boya(i, j, aile) {
        const r = hucreler[i] && hucreler[i][j];
        if (!r) return;
        r.rect.style.fill = aile ? zemin(aile) : "";
        r.rect.style.stroke = aile ? renk(aile) : "";
        r.t.style.fill = aile && s.yaziBoya ? renk(aile) : "";
      },
      satirBoya(i, aile) { for (let j = 0; j < n; j++) api.boya(i, j, aile); },
      sutunBoya(j, aile) { for (let i = 0; i < m; i++) api.boya(i, j, aile); },
      kutu(i0, j0, i1, j1, aile, o) {
        o = o || {};
        const a = Math.min(i0, i1), b = Math.max(i0, i1), c = Math.min(j0, j1), d = Math.max(j0, j1);
        const r = svg("rect", {
          class: ["kx-blok", o.sinif], x: pay + c * w, y: a * h, width: (d - c + 1) * w, height: (b - a + 1) * h, rx: 8,
          "stroke-width": o.kalinlik || 2, "stroke-dasharray": o.kesik ? "6 4" : null,
          style: { stroke: renk(aile || "a"), fill: o.dolgu ? zemin(aile || "a") : "none" }
        });
        kutular.appendChild(r);
        return r;
      },
      yaz(i, j, metin) {
        const r = hucreler[i] && hucreler[i][j];
        if (r) r.t.textContent = hucreMetni(metin, null);
      },
      yaziDugumu(i, j) { return hucreler[i][j].t; },
      sifirla() {
        for (const satir of hucreler) {
          for (const r of satir) { r.rect.style.fill = ""; r.rect.style.stroke = ""; r.t.style.fill = ""; }
        }
        bosalt(kutular);
      }
    };
    return api;
  }

  /* ------------------------------------------------------------------ denetimler */

  function kaydirici(s) {
    s = Object.assign({ etiket: "", min: 0, max: 10, adim: 1, deger: 0, birim: "", bicim: null, degisince: null }, s || {});
    const girdi = el("input", { type: "range", min: s.min, max: s.max, step: s.adim, value: s.deger });
    const cikti = el("output", { class: "kx-k-deger" });
    const yaz = () => {
      const v = Number(girdi.value);
      cikti.textContent = (s.bicim ? s.bicim(v) : sayi(v)) + (s.birim ? " " + s.birim : "");
      girdi.setAttribute("aria-valuetext", cikti.textContent);
    };
    girdi.addEventListener("input", () => {
      yaz();
      if (s.degisince) s.degisince(Number(girdi.value));
    });
    const kok = el("label", { class: "kx-kaydirici" }, el("span", { class: "kx-k-etiket" }, metinDugum(s.etiket)), girdi, cikti);
    yaz();
    return {
      kok, girdi,
      deger: () => Number(girdi.value),
      ayarla(v, sessiz) {
        girdi.value = String(v);
        yaz();
        if (!sessiz && s.degisince) s.degisince(Number(girdi.value));
      }
    };
  }

  function dugme(metin, islev, s) {
    s = s || {};
    return el("button", {
      type: "button", class: ["kx-dugme", s.ana && "ana", s.sinif],
      title: s.baslik || null, "aria-label": s.aria || null, onclick: islev || null
    }, metin);
  }

  function secici(secenekler, deger, degisince) {
    const ogeler = secenekler.map(o => (o && typeof o === "object") ? o : { deger: o, etiket: String(o) });
    let simdiki = deger !== undefined ? deger : (ogeler[0] && ogeler[0].deger);
    const dugmeler = ogeler.map(o => el("button", {
      type: "button", class: "kx-secim", "aria-pressed": String(o.deger === simdiki), onclick: () => ayarla(o.deger)
    }, metinDugum(o.etiket)));
    const kok = el("div", { class: "kx-secici", role: "group" }, dugmeler);
    function ayarla(v, sessiz) {
      if (v === simdiki || !ogeler.some(o => o.deger === v)) return;
      simdiki = v;
      dugmeler.forEach((d, i) => d.setAttribute("aria-pressed", String(ogeler[i].deger === v)));
      if (!sessiz && degisince) degisince(v);
    }
    return { kok, deger: () => simdiki, ayarla };
  }

  /* ------------------------------------------------------------------ KaTeX */

  const MAKROLAR = Object.freeze({
    "\\ka": "\\htmlClass{kx-a}{#1}",
    "\\kb": "\\htmlClass{kx-b}{#1}",
    "\\kc": "\\htmlClass{kx-c}{#1}",
    "\\ksil": "\\htmlClass{kx-sil}{#1}",
    "\\kutua": "\\htmlClass{kx-kutu-a}{#1}",
    "\\kutub": "\\htmlClass{kx-kutu-b}{#1}",
    "\\kutuc": "\\htmlClass{kx-kutu-c}{#1}",
    "\\kutusil": "\\htmlClass{kx-kutu-sil}{#1}"
  });
  const MAKRO_ADLARI = new Set(["ka", "kb", "kc", "ksil", "kutua", "kutub", "kutuc", "kutusil"]);
  const ORTAMLAR = new Set(["bmatrix", "pmatrix", "vmatrix", "Bmatrix", "Vmatrix", "matrix"]);

  function katexSecenek(blok) {
    return {
      displayMode: !!blok,
      throwOnError: false,
      strict: "ignore",
      macros: Object.assign({}, MAKROLAR),
      trust: c => c.command === "\\htmlClass" && /^kx-[a-z-]+$/.test(c.class || "")
    };
  }

  function katexHazir() {
    return !!(pencere.katex && typeof pencere.katex.renderToString === "function");
  }

  function texHtml(kaynak, blok) {
    if (!katexHazir()) return null;
    try { return pencere.katex.renderToString(String(kaynak), katexSecenek(blok)); }
    catch (h) { return null; }
  }

  function tex(kok, kaynak, blok) {
    const h = texHtml(kaynak, blok);
    if (h !== null) {
      kok.innerHTML = h;
      kok.classList.remove("kx-tex-yedek");
    } else {
      kok.textContent = metinTex(kaynak);
      kok.classList.add("kx-tex-yedek");
    }
    return kok;
  }

  function texDugum(kaynak, blok) {
    return tex(el(blok ? "div" : "span", { class: blok ? "kx-tex-blok" : "kx-tex" }), kaynak, blok);
  }

  function metinDugum(metin) {
    if (dugumMu(metin)) return metin;
    const kap = el("span", { class: "kx-metin" });
    const s = metin === null || metin === undefined ? "" : String(metin);
    s.split(/(\$[^$]+\$)/).forEach(p => {
      if (!p) return;
      if (p.length > 2 && p[0] === "$" && p[p.length - 1] === "$") {
        kap.appendChild(texDugum(p.slice(1, -1), false));
        return;
      }
      p.split(/(\*\*[^*]+\*\*)/).forEach(q => {
        if (!q) return;
        if (q.length > 4 && q.startsWith("**") && q.endsWith("**")) kap.appendChild(el("strong", null, q.slice(2, -2)));
        else kap.appendChild(document.createTextNode(q));
      });
    });
    return kap;
  }

  const SEMBOLLER = {
    alpha: "α", beta: "β", gamma: "γ", delta: "δ", Delta: "Δ", epsilon: "ε", varepsilon: "ε", theta: "θ",
    lambda: "λ", mu: "μ", nu: "ν", pi: "π", sigma: "σ", Sigma: "Σ", phi: "φ", varphi: "φ", omega: "ω", Omega: "Ω",
    cdot: "·", times: "×", sum: "Σ", infty: "∞", le: "≤", leq: "≤", ge: "≥", geq: "≥", neq: "≠", ne: "≠",
    to: "→", rightarrow: "→", Rightarrow: "⇒", approx: "≈", pm: "±", partial: "∂", quad: " ", qquad: "  "
  };

  function metinTex(kaynak) {
    let s = String(kaynak === null || kaynak === undefined ? "" : kaynak);
    s = s.replace(/\\htmlClass\{[^}]*\}/g, "")
      .replace(/\\(?:ka|kb|kc|ksil|kutua|kutub|kutuc|kutusil|mathbf|mathrm|mathit|boldsymbol|textbf|text|operatorname)(?![a-zA-Z])/g, "")
      .replace(/\{\{([^{}]*)\}\}/g, "{$1}");
    for (let i = 0; i < 4; i++) s = s.replace(/\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g, "($1)/($2)");
    return s.replace(/\\begin\{[a-zA-Z]*\}/g, "[").replace(/\\end\{[a-zA-Z]*\}/g, "]")
      .replace(/\\\\/g, "; ").replace(/&/g, " ")
      .replace(/\\left|\\right/g, "")
      .replace(/\\[,;:! ]/g, " ")
      .replace(/\\([a-zA-Z]+)/g, (t, ad) => (SEMBOLLER[ad] !== undefined ? SEMBOLLER[ad] : ""))
      .replace(/\^\{?T\}?/g, "ᵀ")
      .replace(/[{}]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  /* ------------------------------------------------------------------ Kesir (kesin rasyonel) */

  function bobeb(a, b) {
    if (a < 0n) a = -a;
    if (b < 0n) b = -b;
    while (b) { const t = a % b; a = b; b = t; }
    return a;
  }

  function tamaCevir(x) {
    if (typeof x === "bigint") return x;
    if (typeof x === "number" && Number.isInteger(x)) return BigInt(x);
    if (typeof x === "string" && /^\s*[+-]?\d+\s*$/.test(x)) return BigInt(x.trim());
    throw new TypeError("Tam sayı bekleniyordu: " + x);
  }

  function bigBol(p, q) {
    const a = Number(p), b = Number(q);
    if (Number.isFinite(a) && Number.isFinite(b)) return a / b;
    const fazla = Math.max((p < 0n ? -p : p).toString().length, q.toString().length) - 300;
    if (fazla <= 0) return a / b;
    const d = 10n ** BigInt(fazla);
    return Number(p / d) / Number(q / d);
  }

  class Kesir {
    constructor(pay, payda) {
      let p = tamaCevir(pay);
      let q = payda === undefined ? 1n : tamaCevir(payda);
      if (q === 0n) throw new RangeError("Payda sıfır olamaz");
      if (q < 0n) { p = -p; q = -q; }
      const g = bobeb(p, q);
      this.pay = g > 1n ? p / g : p;
      this.payda = g > 1n ? q / g : q;
      Object.freeze(this);
    }

    static al(x) {
      if (x instanceof Kesir) return x;
      if (typeof x === "bigint") return new Kesir(x, 1n);
      if (typeof x === "number") {
        if (!Number.isFinite(x)) throw new RangeError("Sonlu bir sayı değil: " + x);
        return Number.isInteger(x) ? new Kesir(BigInt(x), 1n) : girdiCozumle(String(x)).deger;
      }
      if (typeof x === "string") return girdiCozumle(x).deger;
      if (x && typeof x === "object" && "pay" in x && "payda" in x) return new Kesir(x.pay, x.payda);
      throw new TypeError("Sayıya çevrilemedi: " + x);
    }

    static oku(metin) {
      return girdiCozumle(metin).deger;
    }

    static sayidan(x, enFazlaPayda) {
      const sinir = enFazlaPayda || 1e6;
      if (!Number.isFinite(x)) throw new RangeError("Sonlu bir sayı değil: " + x);
      if (Number.isInteger(x)) return new Kesir(BigInt(x), 1n);
      const isaret = x < 0 ? -1 : 1, hedef = Math.abs(x);
      let h0 = 0, h1 = 1, k0 = 1, k1 = 0, y = hedef;
      for (let i = 0; i < 40; i++) {
        const a = Math.floor(y);
        const h2 = a * h1 + h0, k2 = a * k1 + k0;
        if (k2 > sinir) break;
        h0 = h1; h1 = h2; k0 = k1; k1 = k2;
        const kalan = y - a;
        if (kalan < 1e-12 || Math.abs(hedef - h1 / k1) <= 1e-15 * hedef) break;
        y = 1 / kalan;
      }
      if (k1 === 0) return new Kesir(BigInt(Math.round(x)), 1n);
      return new Kesir(BigInt(isaret * h1), BigInt(k1));
    }

    topla(x) { const b = Kesir.al(x); return new Kesir(this.pay * b.payda + b.pay * this.payda, this.payda * b.payda); }
    cikar(x) { const b = Kesir.al(x); return new Kesir(this.pay * b.payda - b.pay * this.payda, this.payda * b.payda); }
    carp(x) { const b = Kesir.al(x); return new Kesir(this.pay * b.pay, this.payda * b.payda); }
    bol(x) {
      const b = Kesir.al(x);
      if (b.pay === 0n) throw new RangeError("Sıfıra bölme");
      return new Kesir(this.pay * b.payda, this.payda * b.pay);
    }
    us(k) {
      if (!Number.isInteger(k)) throw new TypeError("Üs tam sayı olmalı");
      if (k < 0) return this.ters().us(-k);
      return new Kesir(this.pay ** BigInt(k), this.payda ** BigInt(k));
    }
    ters() { return Kesir.BIR.bol(this); }
    neg() { return new Kesir(-this.pay, this.payda); }
    sifirMi() { return this.pay === 0n; }
    esit(x) { const b = Kesir.al(x); return this.pay === b.pay && this.payda === b.payda; }
    karsilastir(x) {
      const b = Kesir.al(x);
      const f = this.pay * b.payda - b.pay * this.payda;
      return f > 0n ? 1 : f < 0n ? -1 : 0;
    }
    isaret() { return this.pay > 0n ? 1 : this.pay < 0n ? -1 : 0; }
    mutlak() { return this.pay < 0n ? this.neg() : this; }
    sayi() { return bigBol(this.pay, this.payda); }
    tamMi() { return this.payda === 1n; }
    ondalik(basamak) { return sayi(this.sayi(), basamak); }
    toString() { return this.payda === 1n ? this.pay.toString() : this.pay.toString() + "/" + this.payda.toString(); }
    toJSON() { return this.toString(); }
    tex() {
      if (this.payda === 1n) return this.pay.toString();
      const neg = this.pay < 0n;
      return (neg ? "-" : "") + "\\frac{" + (neg ? -this.pay : this.pay).toString() + "}{" + this.payda.toString() + "}";
    }
  }
  Kesir.SIFIR = new Kesir(0n, 1n);
  Kesir.BIR = new Kesir(1n, 1n);

  /* Kullanıcı girdisini çözümler: "−3", "5/2", "2,5", "1.25e-3".
   * → { deger: Kesir, kesirli: "a/b" mi, yer: son basamağın onluk üssü, anlamli: anlamlı basamak sayısı } */
  function girdiCozumle(metin) {
    let s = String(metin === null || metin === undefined ? "" : metin).trim()
      .replace(/[−‒–—]/g, "-")
      .replace(/\s+/g, "");
    if (!s) throw new SyntaxError("Boş değer");
    const bolu = s.indexOf("/");
    if (bolu >= 0) {
      if (s.indexOf("/", bolu + 1) >= 0) throw new SyntaxError("Sayı okunamadı: " + metin);
      const a = girdiCozumle(s.slice(0, bolu)).deger, b = girdiCozumle(s.slice(bolu + 1)).deger;
      if (b.sifirMi()) throw new RangeError("Sıfıra bölme");
      return { deger: a.bol(b), kesirli: true, yer: 0, anlamli: Infinity };
    }
    if (/^[+-]?\d*,\d+$/.test(s)) s = s.replace(",", ".");
    const m = /^([+-]?)(\d*)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/.exec(s);
    if (!m || (!m[2] && !m[3])) throw new SyntaxError("Sayı okunamadı: " + metin);
    const tam = m[2] || "", ond = m[3] || "", us = m[4] ? parseInt(m[4], 10) : 0;
    if (Math.abs(us) > 300) throw new RangeError("Üs çok büyük: " + metin);
    let pay = BigInt((tam + ond) || "0");
    if (m[1] === "-") pay = -pay;
    const yer = us - ond.length;
    const deger = yer >= 0 ? new Kesir(pay * 10n ** BigInt(yer), 1n) : new Kesir(pay, 10n ** BigInt(-yer));
    const rakamlar = (tam + ond).replace(/^0+/, "");
    return { deger, kesirli: false, yer, anlamli: rakamlar.length || 1 };
  }

  /* ------------------------------------------------------------------ Mat */

  class Mat {
    constructor(satirlar) {
      if (!Array.isArray(satirlar) || !satirlar.length || !Array.isArray(satirlar[0]) || !satirlar[0].length) {
        throw new RangeError("Matris en az bir satır ve bir sütun içermeli");
      }
      const n = satirlar[0].length;
      this.v = Object.freeze(satirlar.map((r, i) => {
        if (!Array.isArray(r) || r.length !== n) throw new RangeError("Satırların eleman sayıları farklı (" + (i + 1) + ". satır)");
        return Object.freeze(r.map(x => Kesir.al(x)));
      }));
      this.m = satirlar.length;
      this.n = n;
      Object.freeze(this);
    }

    static al(x) {
      if (x instanceof Mat) return x;
      if (typeof x === "string") return Mat.oku(x);
      if (typeof x === "number" || typeof x === "bigint" || x instanceof Kesir) return new Mat([[x]]);
      if (Array.isArray(x)) {
        if (!x.length) throw new RangeError("Boş matris");
        return Array.isArray(x[0]) ? new Mat(x) : new Mat(x.map(e => [e]));
      }
      throw new TypeError("Matrise çevrilemedi: " + x);
    }

    /* Motorla aynı biçim: satırlar ";" ya da satır sonu; satır içinde virgül varsa virgül, yoksa boşluk. */
    static oku(metin) {
      let s = String(metin).trim();
      if (!s) throw new SyntaxError("Boş matris girdisi");
      if (s[0] === "[") s = s.replace(/^\[\s*\[?/, "").replace(/\]?\s*\]$/, "").replace(/\]\s*,\s*\[/g, ";");
      const satirlar = s.split(/[;\n]/).filter(r => r.trim()).map(r => {
        r = r.trim();
        const parca = r.indexOf(",") >= 0 ? r.split(",") : r.split(/\s+/);
        return parca.map(t => t.trim()).filter(Boolean).map(t => girdiCozumle(t).deger);
      });
      return new Mat(satirlar);
    }

    static birim(n) {
      return new Mat(Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 1n : 0n))));
    }

    static sifir(m, n) {
      const s = n === undefined ? m : n;
      return new Mat(Array.from({ length: m }, () => Array(s).fill(0n)));
    }

    static rastgele(rnd, m, n, alt, ust, sifirsiz) {
      const a = alt === undefined ? -5 : alt, b = ust === undefined ? 9 : ust;
      return new Mat(Array.from({ length: m }, () => Array.from({ length: n }, () => (sifirsiz ? rnd.sifirsiz(a, b) : rnd.tam(a, b)))));
    }

    boyut() { return [this.m, this.n]; }
    kare() { return this.m === this.n; }
    g(i, j) { return this.v[i][j]; }
    satir(i) { return this.v[i].slice(); }
    sutun(j) { return this.v.map(r => r[j]); }
    harita(f) { return new Mat(this.v.map((r, i) => r.map((x, j) => f(x, i, j)))); }

    _ayniBoyut(B, ad) {
      if (this.m !== B.m || this.n !== B.n) {
        throw new RangeError(ad + " için boyutlar aynı olmalı: " + this.m + "×" + this.n + " ile " + B.m + "×" + B.n);
      }
    }

    _kareMi(ad) {
      if (this.m !== this.n) throw new RangeError(ad + " yalnız kare matris için tanımlı (" + this.m + "×" + this.n + ")");
    }

    topla(B) { B = Mat.al(B); this._ayniBoyut(B, "Toplama"); return this.harita((x, i, j) => x.topla(B.v[i][j])); }
    cikar(B) { B = Mat.al(B); this._ayniBoyut(B, "Çıkarma"); return this.harita((x, i, j) => x.cikar(B.v[i][j])); }
    skaler(k) { const c = Kesir.al(k); return this.harita(x => x.carp(c)); }

    carp(B) {
      B = Mat.al(B);
      if (this.n !== B.m) {
        throw new RangeError("Çarpım tanımsız: " + this.m + "×" + this.n + " ile " + B.m + "×" + B.n + " (iç boyutlar " + this.n + " ≠ " + B.m + ")");
      }
      const R = [];
      for (let i = 0; i < this.m; i++) {
        const r = [];
        for (let j = 0; j < B.n; j++) {
          let t = Kesir.SIFIR;
          for (let k = 0; k < this.n; k++) t = t.topla(this.v[i][k].carp(B.v[k][j]));
          r.push(t);
        }
        R.push(r);
      }
      return new Mat(R);
    }

    transpoz() { return new Mat(Array.from({ length: this.n }, (_, j) => this.v.map(r => r[j]))); }

    minor(i, j) {
      if (this.m < 2 || this.n < 2) throw new RangeError("Minör için en az 2×2 matris gerekir");
      return new Mat(this.v.filter((_, a) => a !== i).map(r => r.filter((_, b) => b !== j)));
    }

    kofaktor(i, j) {
      const d = this.minor(i, j).det();
      return (i + j) % 2 ? d.neg() : d;
    }

    iz() {
      this._kareMi("İz");
      let t = Kesir.SIFIR;
      for (let i = 0; i < this.m; i++) t = t.topla(this.v[i][i]);
      return t;
    }

    det() {
      this._kareMi("Determinant");
      const n = this.m, a = this.v.map(r => r.slice());
      let d = Kesir.BIR;
      for (let k = 0; k < n; k++) {
        let p = k;
        while (p < n && a[p][k].sifirMi()) p++;
        if (p === n) return Kesir.SIFIR;
        if (p !== k) { const t = a[p]; a[p] = a[k]; a[k] = t; d = d.neg(); }
        d = d.carp(a[k][k]);
        for (let i = k + 1; i < n; i++) {
          if (a[i][k].sifirMi()) continue;
          const c = a[i][k].bol(a[k][k]);
          for (let j = k; j < n; j++) a[i][j] = a[i][j].cikar(c.carp(a[k][j]));
        }
      }
      return d;
    }

    _gaussJordan(B, tekilMesaj) {
      const n = this.m, a = this.v.map((r, i) => r.concat(B.v[i]));
      const w = a[0].length;
      for (let k = 0; k < n; k++) {
        let p = k;
        while (p < n && a[p][k].sifirMi()) p++;
        if (p === n) throw new RangeError(tekilMesaj);
        if (p !== k) { const t = a[p]; a[p] = a[k]; a[k] = t; }
        const piv = a[k][k];
        for (let j = k; j < w; j++) a[k][j] = a[k][j].bol(piv);
        for (let i = 0; i < n; i++) {
          if (i === k || a[i][k].sifirMi()) continue;
          const c = a[i][k];
          for (let j = k; j < w; j++) a[i][j] = a[i][j].cikar(c.carp(a[k][j]));
        }
      }
      return new Mat(a.map(r => r.slice(n)));
    }

    ters() {
      this._kareMi("Ters");
      return this._gaussJordan(Mat.birim(this.m), "Matris tekil (det = 0); tersi yok");
    }

    coz(b) {
      this._kareMi("Doğrusal sistem çözümü");
      b = Mat.al(b);
      if (b.m !== this.m) throw new RangeError("Sağ taraf " + this.m + " satırlı olmalı (şu an " + b.m + ")");
      return this._gaussJordan(b, "Katsayı matrisi tekil (det = 0); sistemin tek bir çözümü yok");
    }

    esit(B) {
      try { B = Mat.al(B); } catch (_) { return false; }
      if (this.m !== B.m || this.n !== B.n) return false;
      return this.v.every((r, i) => r.every((x, j) => x.esit(B.v[i][j])));
    }

    tex(s) {
      s = s || {};
      const ortam = ORTAMLAR.has(s.ortam) ? s.ortam : "bmatrix";
      const bicim = s.bicim || (x => x.tex());
      const vurgu = s.vurgu;
      const satirlar = this.v.map((r, i) => r.map((x, j) => {
        let t = bicim(x, i, j);
        const mak = typeof vurgu === "function" ? vurgu(i, j, x) : vurgu ? vurgu[i + "," + j] : null;
        if (mak && MAKRO_ADLARI.has(mak)) t = "\\" + mak + "{" + t + "}";
        return t;
      }).join(" & "));
      return "\\begin{" + ortam + "}" + satirlar.join(" \\\\ ") + "\\end{" + ortam + "}";
    }

    metin() { return this.v.map(r => r.map(x => x.toString()).join(" ")).join("; "); }
    sayilar() { return this.v.map(r => r.map(x => x.sayi())); }
    toString() { return this.metin(); }
    toJSON() { return this.metin(); }
  }

  function matrisMetni(A) {
    return Mat.al(A).metin();
  }

  /* ------------------------------------------------------------------ rastgele, sayı biçimi */

  function rastgele(tohum) {
    let a = (Number(tohum) >>> 0) || 1;
    function sayiUret() {
      a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
    const r = {
      sayi: sayiUret,
      tam(alt, ust) { return alt + Math.floor(sayiUret() * (ust - alt + 1)); },
      sec(d) { return d[Math.floor(sayiUret() * d.length)]; },
      sifirsiz(alt, ust) {
        if (alt === 0 && ust === 0) throw new RangeError("sifirsiz: aralıkta sıfırdan başka sayı yok");
        let x;
        do { x = r.tam(alt, ust); } while (x === 0);
        return x;
      },
      karistir(d) {
        const k = d.slice();
        for (let i = k.length - 1; i > 0; i--) {
          const j = Math.floor(sayiUret() * (i + 1));
          const t = k[i]; k[i] = k[j]; k[j] = t;
        }
        return k;
      }
    };
    return r;
  }

  function yeniTohum() {
    try {
      if (pencere.crypto && pencere.crypto.getRandomValues) {
        return (pencere.crypto.getRandomValues(new Uint32Array(1))[0] >>> 0) || 1;
      }
    } catch (_) { /* aşağıdaki yedeğe düş */ }
    return (Math.floor(Math.random() * 4294967296) >>> 0) || 1;
  }

  function sifirKirp(s) {
    return s.indexOf(".") >= 0 ? s.replace(/\.?0+$/, "") : s;
  }

  function sayi(x, basamak) {
    const b = basamak || 4;
    if (x instanceof Kesir) x = x.sayi();
    x = Number(x);
    if (!Number.isFinite(x)) return String(x);
    const a = Math.abs(x);
    if (a < 1e-12) return "0";
    if (a >= 1e7 || a < 1e-4) {
      const parca = x.toExponential(b - 1).split("e");
      return sifirKirp(parca[0]) + "e" + parseInt(parca[1], 10);
    }
    if (a >= Math.pow(10, b - 1)) return String(Math.round(x));
    return sifirKirp(x.toPrecision(b));
  }

  function sayiTex(x, basamak) {
    const s = sayi(x, basamak);
    const i = s.indexOf("e");
    return i < 0 ? s : s.slice(0, i) + " \\times 10^{" + s.slice(i + 1) + "}";
  }

  /* ------------------------------------------------------------------ etkileşim: sürükleme, animasyon */

  function hareketAzalt() {
    try { return !!(pencere.matchMedia && pencere.matchMedia("(prefers-reduced-motion: reduce)").matches); }
    catch (_) { return false; }
  }

  function svgNokta(kokSvg, olay) {
    const s = kokSvg.ownerSVGElement || kokSvg;
    const ctm = s.getScreenCTM && s.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const ters = ctm.inverse();
    if (typeof s.createSVGPoint === "function") {
      const p = s.createSVGPoint();
      p.x = olay.clientX;
      p.y = olay.clientY;
      const q = p.matrixTransform(ters);
      return { x: q.x, y: q.y };
    }
    const q = new DOMPoint(olay.clientX, olay.clientY).matrixTransform(ters);
    return { x: q.x, y: q.y };
  }

  function surukle(eleman, s) {
    s = s || {};
    const kokSvg = s.svg || eleman.ownerSVGElement || eleman;
    let aktif = null;
    const nokta = e => svgNokta(kokSvg, e);
    function bas(e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      aktif = e.pointerId;
      try { eleman.setPointerCapture(e.pointerId); } catch (_) { /* eski tarayıcı */ }
      eleman.classList.add("kx-surukleniyor");
      e.preventDefault();
      if (s.basla) s.basla(nokta(e), e);
    }
    function tasi(e) {
      if (aktif !== e.pointerId) return;
      e.preventDefault();
      if (s.tasi) s.tasi(nokta(e), e);
    }
    function birak(e) {
      if (aktif !== e.pointerId) return;
      aktif = null;
      eleman.classList.remove("kx-surukleniyor");
      try { eleman.releasePointerCapture(e.pointerId); } catch (_) { /* yok say */ }
      if (s.birak) s.birak(nokta(e), e);
    }
    const dokun = e => { if (e.cancelable) e.preventDefault(); };
    eleman.classList.add("kx-tutamak");
    eleman.style.touchAction = "none";
    eleman.addEventListener("pointerdown", bas);
    eleman.addEventListener("pointermove", tasi);
    eleman.addEventListener("pointerup", birak);
    eleman.addEventListener("pointercancel", birak);
    eleman.addEventListener("touchstart", dokun, { passive: false });
    let tus = null;
    if (typeof s.klavye === "function") {
      if (!eleman.hasAttribute("tabindex")) eleman.setAttribute("tabindex", "0");
      tus = e => {
        const yon = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
        if (!yon) return;
        e.preventDefault();
        const k = e.shiftKey ? 10 : 1;
        s.klavye(yon[0] * k, yon[1] * k, e);
      };
      eleman.addEventListener("keydown", tus);
    }
    return function kaldir() {
      eleman.removeEventListener("pointerdown", bas);
      eleman.removeEventListener("pointermove", tasi);
      eleman.removeEventListener("pointerup", birak);
      eleman.removeEventListener("pointercancel", birak);
      eleman.removeEventListener("touchstart", dokun, { passive: false });
      if (tus) eleman.removeEventListener("keydown", tus);
    };
  }

  function animasyon(kok, adim) {
    let calisiyor = false, gorunur = true, kimlik = 0, onceki = null, t = 0, bagliOldu = false, bekleme = 0, gozlemci = null;
    function gozlemciKur() {
      if (gozlemci || typeof IntersectionObserver === "undefined") return;
      gozlemci = new IntersectionObserver(kayitlar => {
        if (bagliOldu && !kok.isConnected) { durdur(); return; }
        gorunur = kayitlar.some(k => k.isIntersecting);
        if (gorunur) planla();
      });
      gozlemci.observe(kok);
    }
    function planla() {
      if (!kimlik && calisiyor) kimlik = pencere.requestAnimationFrame(kare);
    }
    function kare(zaman) {
      kimlik = 0;
      if (!calisiyor) return;
      if (kok.isConnected) bagliOldu = true;
      else if (bagliOldu || ++bekleme > 600) { durdur(); return; }
      if (!gorunur) { onceki = null; return; } // gözlemci görünür olunca yeniden başlatır
      const dt = onceki === null ? 0 : Math.min(0.1, (zaman - onceki) / 1000);
      onceki = zaman;
      t += dt;
      let sonuc;
      try { sonuc = adim(t, dt); } catch (h) { console.error("Etkilesim animasyon:", h); durdur(); return; }
      if (sonuc === false) { durdur(); return; }
      planla();
    }
    function durdur() {
      calisiyor = false;
      if (kimlik) { pencere.cancelAnimationFrame(kimlik); kimlik = 0; }
      if (gozlemci) { gozlemci.disconnect(); gozlemci = null; }
      onceki = null;
    }
    function devam() {
      if (calisiyor) return;
      calisiyor = true;
      bekleme = 0;
      bagliOldu = false;
      onceki = null;
      gozlemciKur();
      planla();
    }
    devam();
    return { durdur, devam, calisiyor: () => calisiyor, sifirla() { t = 0; onceki = null; } };
  }

  /* ------------------------------------------------------------------ cevap ızgarası ve denetim */

  function cevapIzgarasi(s) {
    s = s || {};
    const girdiler = [];
    const gonder = typeof s.gonder === "function" ? s.gonder : null;
    function girdiYap(aria) {
      const g = el("input", {
        type: "text", class: "kx-girdi", autocomplete: "off", autocapitalize: "off", autocorrect: "off",
        spellcheck: "false", enterkeyhint: "done", "aria-label": aria
      });
      g.addEventListener("input", () => g.classList.remove("dogru", "yanlis", "kaba", "gosterildi"));
      if (gonder) g.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); gonder(); } });
      return g;
    }
    let kok;
    if (s.etiketler && s.etiketler.length) {
      kok = el("div", { class: "kx-alanlar" });
      s.etiketler.forEach(et => {
        const g = girdiYap(metinTex(et) || "değer");
        girdiler.push([g]);
        kok.appendChild(el("label", { class: "kx-alan" }, el("span", { class: "kx-alan-etiket" }, metinDugum(et)), g));
      });
    } else {
      const m = s.satir || 1, n = s.sutun || 1;
      const parantez = s.parantez === undefined ? m * n > 1 : !!s.parantez;
      const izgara = el("div", { class: ["kx-izgara", parantez && "parantez"], style: { "--kx-sutun": n } });
      for (let i = 0; i < m; i++) {
        const satir = [];
        for (let j = 0; j < n; j++) {
          const g = girdiYap(m * n > 1 ? "satır " + (i + 1) + ", sütun " + (j + 1) : (metinTex(s.etiket) || "cevap"));
          satir.push(g);
          izgara.appendChild(g);
        }
        girdiler.push(satir);
      }
      kok = el("div", { class: "kx-izgara-kap" }, s.etiket ? el("span", { class: "kx-izgara-etiket" }, metinDugum(s.etiket)) : null, izgara);
    }
    const hepsi = () => girdiler.reduce((a, r) => a.concat(r), []);
    return {
      kok, girdiler,
      oku: () => girdiler.map(r => r.map(g => g.value.trim())),
      isaretle(durum) {
        girdiler.forEach((r, i) => r.forEach((g, j) => {
          g.classList.remove("dogru", "yanlis", "kaba");
          const d = durum && durum[i] && durum[i][j];
          if (d) g.classList.add(d);
        }));
      },
      temizle() {
        hepsi().forEach(g => { g.value = ""; g.readOnly = false; g.classList.remove("dogru", "yanlis", "kaba", "gosterildi"); });
      },
      doldur(degerler, o) {
        o = o || {};
        const D = degerler instanceof Mat ? degerler.v : degerler;
        const kaynak = D.reduce((a, r) => a.concat(Array.isArray(r) ? r : [r]), []);
        hepsi().forEach((g, k) => {
          const x = kaynak[k];
          if (x === undefined) return;
          g.value = o.bicim ? String(o.bicim(x)) : hucreMetni(x, null);
          g.classList.remove("dogru", "yanlis", "kaba");
          if (o.gosterildi !== false) g.classList.add("gosterildi");
        });
      },
      kilitle(k) { hepsi().forEach(g => { g.readOnly = k !== false; }); },
      odak() {
        const l = hepsi();
        const g = l.find(x => !x.value) || l[0];
        if (g) g.focus({ preventScroll: true });
      }
    };
  }

  function toleransSayi(t) {
    if (typeof t === "number" && t >= 0) return t;
    return t === "yaklasik" ? 1e-3 : 0;
  }

  function hucreDenetle(g, e, tol, olcek) {
    if (g.deger.esit(e)) return "dogru";
    const u = g.deger.sayi(), b = e.sayi();
    const fark = Math.abs(u - b);
    if (fark <= 1e-9 * Math.max(Math.abs(b), olcek)) return "dogru"; // kayan nokta gürültüsü
    let kaba = false;
    if (!g.kesirli) {
      const tamFark = g.deger.cikar(e).mutlak();
      const yarim = g.yer >= 0 ? new Kesir(10n ** BigInt(g.yer), 2n) : new Kesir(1n, 2n * 10n ** BigInt(-g.yer));
      if (tamFark.karsilastir(yarim) <= 0) {
        if (g.anlamli >= 3) return "dogru";
        kaba = true;
      }
    }
    if (tol > 0 && fark <= tol * Math.max(Math.abs(b), 1e-3 * olcek)) return "dogru";
    return kaba ? "kaba" : "yanlis";
  }

  /* ham: kullanıcı metinlerinden 2B dizi (cevapla aynı biçimde). → { dogru, kaba, okunamayan, hucreler } */
  function cevapDenetle(ham, cevap, tolerans) {
    const C = Mat.al(cevap);
    const tol = toleransSayi(tolerans);
    let olcek = 0;
    for (const r of C.v) for (const x of r) olcek = Math.max(olcek, Math.abs(x.sayi()));
    olcek = olcek || 1;
    let hepsiDogru = true, kaba = false, yanlis = false, okunamayan = false;
    const hucreler = C.v.map((r, i) => r.map((e, j) => {
      const metin = ham[i] && ham[i][j] !== undefined ? String(ham[i][j]) : "";
      let g;
      try { g = girdiCozumle(metin); } catch (_) { okunamayan = true; hepsiDogru = false; return "yanlis"; }
      const d = hucreDenetle(g, e, tol, olcek);
      if (d !== "dogru") hepsiDogru = false;
      if (d === "kaba") kaba = true;
      if (d === "yanlis") yanlis = true;
      return d;
    }));
    return { dogru: hepsiDogru, kaba: kaba && !yanlis && !okunamayan, okunamayan, hucreler };
  }

  /* ------------------------------------------------------------------ alıştırma */

  function adimListesi(adimlar) {
    const ol = el("ol");
    adimlar.forEach(a => {
      const li = el("li");
      if (typeof a === "string") {
        li.appendChild(metinDugum(a));
      } else if (a) {
        if (a.metin) li.appendChild(el("div", null, metinDugum(a.metin)));
        if (a.tex) li.appendChild(texDugum(a.tex, true));
        if (a.sekil && dugumMu(a.sekil)) li.appendChild(el("div", { class: "kx-sahne" }, a.sekil));
      }
      ol.appendChild(li);
    });
    return ol;
  }

  function alistirmaKur(kok, param, uret, meta) {
    temelStil();
    param = param || {};
    meta = meta || {};
    kok.classList.add("kx-kok");
    const tohumVar = param.tohum !== undefined && param.tohum !== null && param.tohum !== "";
    let tohum = tohumVar ? ((Number(param.tohum) >>> 0) || 1) : yeniTohum();
    const sonrakiTohum = t => ((Math.imul(t, 1664525) + 1013904223) >>> 0) || 1;
    let soru = null, cevap = null, izgara = null;
    let dogruSayisi = 0, deneme = 0, cozuldu = false, gosterildi = false, ipucuSira = 0;

    const soruKutusu = el("div", { class: "kx-soru" });
    const cevapKutusu = el("div", { class: "kx-cevap" });
    const geri = el("p", { class: "kx-geri", role: "status", "aria-live": "polite" });
    const ipucuKutusu = el("div", { class: "kx-ipucu", hidden: true });
    const cozumKutusu = el("div", { class: "kx-cozum", hidden: true });
    const adimKutusu = el("div", { class: "kx-adimlar", hidden: true });
    const sayac = el("span", { class: "kx-sayac" });
    const dKontrol = dugme("Kontrol et", () => kontrol(), { ana: true });
    const dIpucu = dugme("İpucu", () => ipucuGoster());
    const dCevap = dugme("Cevabı göster", () => cevabiGoster());
    const dAdim = dugme("Adım adım çözüm", () => adimlariGoster());
    const dYeni = dugme("Yeni soru", () => yeni());
    dAdim.setAttribute("aria-expanded", "false");
    const kap = el("div", { class: "kx-alistirma" },
      meta.giris ? el("p", { class: "kx-aciklama" }, metinDugum(meta.giris)) : null,
      soruKutusu, cevapKutusu,
      el("div", { class: "kx-satir kx-dugmeler" }, dKontrol, dIpucu, dCevap, dAdim, dYeni),
      geri, ipucuKutusu, cozumKutusu, adimKutusu,
      el("div", { class: "kx-alt" }, sayac));
    kok.appendChild(kap);

    function sayacYaz() {
      sayac.textContent = "Doğru: " + dogruSayisi + " / Deneme: " + deneme;
    }

    function mesaj(tur, metin) {
      geri.className = "kx-geri" + (tur ? " " + tur : "");
      bosalt(geri);
      if (metin) geri.appendChild(metinDugum(metin));
    }

    function cevapHazirla(s) {
      if (s.cevap === undefined || s.cevap === null) throw new Error("Sorunun cevabı yok");
      let C = Mat.al(s.cevap);
      if (s.alanlar && s.alanlar.length) {
        const duz = C.v.reduce((a, r) => a.concat(r), []);
        if (duz.length !== s.alanlar.length) throw new Error("alanlar ile cevap sayısı uyuşmuyor");
        C = new Mat(duz.map(x => [x]));
      }
      return C;
    }

    function uretVeHazirla() {
      let son = null;
      for (let k = 0; k < 20; k++) {
        try {
          const s = uret(rastgele(tohum), param);
          if (s) return { s, c: cevapHazirla(s) };
        } catch (h) {
          son = h;
        }
        tohum = sonrakiTohum(tohum);
      }
      throw son || new Error("Soru üretilemedi");
    }

    function ipucuListesi() {
      const i = soru && soru.ipucu;
      return !i ? [] : Array.isArray(i) ? i : [i];
    }

    function kurSoru() {
      const sonuc = uretVeHazirla();
      soru = sonuc.s;
      cevap = sonuc.c;
      cozuldu = false;
      gosterildi = false;
      ipucuSira = 0;
      bosalt(soruKutusu);
      bosalt(cevapKutusu);
      mesaj("", "");
      [ipucuKutusu, cozumKutusu, adimKutusu].forEach(k => { k.hidden = true; bosalt(k); });
      if (soru.metin) soruKutusu.appendChild(el("p", { class: "kx-soru-metin" }, metinDugum(soru.metin)));
      if (soru.tex) soruKutusu.appendChild(texDugum(soru.tex, true));
      if (soru.sekil) {
        const d = typeof soru.sekil === "function" ? soru.sekil() : soru.sekil;
        if (dugumMu(d)) soruKutusu.appendChild(el("div", { class: "kx-sahne kx-soru-sekil" }, d));
      }
      izgara = soru.alanlar && soru.alanlar.length
        ? cevapIzgarasi({ etiketler: soru.alanlar, gonder: kontrol })
        : cevapIzgarasi({ satir: cevap.m, sutun: cevap.n, etiket: soru.etiket, gonder: kontrol });
      cevapKutusu.appendChild(izgara.kok);
      dIpucu.hidden = !ipucuListesi().length;
      dIpucu.disabled = false;
      dIpucu.textContent = "İpucu";
      dAdim.hidden = !(soru.adimlar && soru.adimlar.length) && !soru.motor;
      dAdim.setAttribute("aria-expanded", "false");
      sayacYaz();
    }

    function ozelDenetim(ham) {
      const hucreler = ham.map(r => r.map(() => null));
      let okunamayan = false;
      const degerler = ham.map((r, i) => r.map((v, j) => {
        try { return girdiCozumle(v).deger; } catch (_) { okunamayan = true; hucreler[i][j] = "yanlis"; return null; }
      }));
      if (okunamayan) return { dogru: false, kaba: false, okunamayan, hucreler };
      let r;
      try { r = soru.denetle(degerler) || {}; } catch (h) { r = { dogru: false, mesaj: "Denetlenemedi: " + hataMetni(h) }; }
      return {
        dogru: !!r.dogru, kaba: false, okunamayan: false, mesaj: r.mesaj,
        hucreler: r.hucreler || ham.map(rr => rr.map(() => (r.dogru ? "dogru" : "yanlis")))
      };
    }

    function kontrol() {
      if (!soru || !izgara) return;
      const ham = izgara.oku();
      if (ham.some(r => r.some(v => v === ""))) {
        mesaj("uyari", "Önce boş kutuları doldur.");
        izgara.odak();
        return;
      }
      const sonuc = typeof soru.denetle === "function" ? ozelDenetim(ham) : cevapDenetle(ham, cevap, soru.tolerans);
      izgara.isaretle(sonuc.hucreler);
      if (sonuc.okunamayan) { mesaj("uyari", OKUNAMADI); return; }
      if (!cozuldu) deneme++;
      if (sonuc.dogru) {
        if (!cozuldu && !gosterildi) dogruSayisi++;
        cozuldu = true;
        mesaj("dogru", sonuc.mesaj || (gosterildi ? "Doğru. Cevap gösterilmişti; yeni bir soruyla kendini dene." : "Doğru! Tüm kutular tuttu."));
      } else if (sonuc.kaba) {
        mesaj("uyari", sonuc.mesaj || "Yuvarlaman doğru ama çok kaba: en az 3 anlamlı basamak ya da kesir yaz (ör. 0.333 ya da 1/3).");
      } else {
        const duz = sonuc.hucreler.reduce((a, r) => a.concat(r), []);
        const d = duz.filter(x => x === "dogru").length;
        mesaj("yanlis", sonuc.mesaj || (duz.length > 1
          ? d + " / " + duz.length + " kutu doğru. Kırmızı kutulara yeniden bak."
          : "Henüz doğru değil. İpucuna bakabilir ya da yeniden deneyebilirsin."));
      }
      sayacYaz();
    }

    function ipucuGoster() {
      const l = ipucuListesi();
      if (!l.length) return;
      if (ipucuSira < l.length) {
        ipucuKutusu.appendChild(el("p", null, metinDugum(l[ipucuSira])));
        ipucuSira++;
      }
      ipucuKutusu.hidden = false;
      if (ipucuSira >= l.length) {
        dIpucu.disabled = true;
        if (l.length > 1) dIpucu.textContent = "İpuçları açık";
      } else {
        dIpucu.textContent = "Sonraki ipucu";
      }
    }

    function cevabiGoster() {
      if (!soru || !izgara) return;
      gosterildi = true;
      const bicim = soru.bicim || (x => (x.tamMi() || x.payda <= 1000n ? x.toString() : sayi(x, 6)));
      izgara.doldur(cevap, { bicim });
      izgara.isaretle(null);
      bosalt(cozumKutusu);
      if (soru.aciklama) {
        cozumKutusu.appendChild(el("p", null, metinDugum(soru.aciklama)));
        cozumKutusu.hidden = false;
      }
      mesaj("uyari", "Cevap kesikli çerçeveyle kutulara yazıldı.");
    }

    function adimlariGoster() {
      if (!soru) return;
      if (!adimKutusu.hidden) {
        adimKutusu.hidden = true;
        dAdim.setAttribute("aria-expanded", "false");
        return;
      }
      adimKutusu.hidden = false;
      dAdim.setAttribute("aria-expanded", "true");
      if (adimKutusu.childNodes.length) return; // zaten çizildi
      const yerel = soru.adimlar && soru.adimlar.length ? soru.adimlar : null;
      if (soru.motor && motorVar()) {
        const bu = soru;
        motor(soru.motor, adimKutusu).then(y => {
          if (!y && yerel && bu === soru) adimKutusu.appendChild(adimListesi(yerel));
        });
        return;
      }
      if (yerel) { adimKutusu.appendChild(adimListesi(yerel)); return; }
      adimKutusu.appendChild(el("p", { class: "kx-not" }, MOTOR_YOK));
    }

    function yeni() {
      tohum = sonrakiTohum(tohum);
      try {
        kurSoru();
        izgara.odak();
      } catch (h) {
        mesaj("yanlis", "Soru üretilemedi: " + hataMetni(h));
      }
    }

    kurSoru(); // hata atarsa kur() yakalar ve "Etkileşim açılamadı" gösterir

    return {
      yok_et() { /* dinleyiciler elemanların üstünde; kök boşalınca gider */ },
      soru: () => soru,
      tohum: () => tohum,
      izgara: () => izgara,
      kontrol, yeni, cevabiGoster
    };
  }

  /* ------------------------------------------------------------------ motor bağlantısı */

  let MOTOR = null, CIZICI = null;

  function motorBagla(islev, cizici) {
    MOTOR = typeof islev === "function" ? islev : null;
    CIZICI = typeof cizici === "function" ? cizici : null;
  }

  function motorVar() {
    return !!MOTOR;
  }

  async function motor(istek, hedef) {
    if (!MOTOR) {
      if (hedef) { bosalt(hedef); hedef.appendChild(el("p", { class: "kx-not" }, MOTOR_YOK)); }
      return null;
    }
    if (hedef) { bosalt(hedef); hedef.appendChild(el("p", { class: "kx-not kx-bekle" }, "Çözüm hazırlanıyor…")); }
    try {
      const yanit = await MOTOR(istek);
      if (yanit && yanit.hata) throw new Error(yanit.hata);
      if (hedef) {
        bosalt(hedef);
        if (CIZICI) CIZICI(yanit, hedef);
        else hedef.appendChild(el("pre", { class: "kx-ham" }, JSON.stringify(yanit, null, 2)));
      }
      return yanit;
    } catch (h) {
      if (hedef) { bosalt(hedef); hedef.appendChild(el("p", { class: "kx-hata" }, "Çözüm alınamadı: " + hataMetni(h))); }
      return null;
    }
  }

  /* ------------------------------------------------------------------ stil */

  function stilEkle(id, css) {
    if (typeof document === "undefined") return null;
    let s = document.getElementById(id);
    if (s) return s;
    s = document.createElement("style");
    s.id = id;
    s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
    return s;
  }

  const TEMEL_CSS = [
    ".kx-kok{display:block;color:var(--metin,#15213a);line-height:1.55}",
    ".kx-kok *,.kx-kok *::before,.kx-kok *::after{box-sizing:border-box}",
    ".kx-kok [hidden]{display:none!important}",
    ".kx-svg{display:block;margin:0 auto;max-width:100%;height:auto;overflow:visible}",
    ".kx-kok svg text{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-size:13px;fill:currentColor}",
    ".kx-yazi{pointer-events:none}",
    ".kx-sahne{background:var(--kart,#fff);border:1px solid var(--cizgi,#d9e1ee);border-radius:12px;padding:12px;margin:8px 0}",
    ".kx-satir{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0}",
    ".kx-aciklama{color:var(--soluk,#5b6b85);font-size:.95em;margin:8px 0}",
    ".kx-dugme{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:40px;padding:0 14px;border-radius:10px;" +
      "border:1px solid var(--cizgi,#d9e1ee);background:var(--kart,#fff);color:var(--metin,#15213a);font:inherit;font-weight:600;" +
      "cursor:pointer;touch-action:manipulation;-webkit-tap-highlight-color:transparent}",
    ".kx-dugme:hover:not(:disabled){border-color:var(--ana,#1e3a8a)}",
    ".kx-dugme.ana{background:var(--ana,#1e3a8a);border-color:var(--ana,#1e3a8a);color:#fff}",
    ".kx-dugme.ana:hover:not(:disabled){background:var(--ana-koyu,#172e6e)}",
    ".kx-dugme:disabled{opacity:.5;cursor:default}",
    ".kx-kok :focus-visible{outline:2px solid var(--vurgu,#0e9f8f);outline-offset:2px}",
    ".kx-kaydirici{display:grid;grid-template-columns:1fr auto;grid-template-areas:'e d' 'g g';gap:2px 10px;align-items:center;margin:8px 0}",
    ".kx-k-etiket{grid-area:e;color:var(--soluk,#5b6b85);font-size:.92em}",
    ".kx-k-deger{grid-area:d;font-weight:600;font-variant-numeric:tabular-nums;text-align:right}",
    ".kx-kaydirici input[type=range]{grid-area:g;width:100%;min-height:32px;margin:0;accent-color:var(--ana,#1e3a8a)}",
    "@media (min-width:640px){.kx-kaydirici{grid-template-columns:minmax(110px,max-content) 1fr minmax(64px,max-content);grid-template-areas:'e g d'}}",
    ".kx-secici{display:inline-flex;flex-wrap:wrap;border:1px solid var(--cizgi,#d9e1ee);border-radius:10px;overflow:hidden;background:var(--kart,#fff)}",
    ".kx-secim{min-height:36px;padding:0 12px;border:0;background:transparent;color:var(--soluk,#5b6b85);font:inherit;cursor:pointer;touch-action:manipulation}",
    ".kx-secim+.kx-secim{border-left:1px solid var(--cizgi,#d9e1ee)}",
    ".kx-secim[aria-pressed=true]{background:var(--ana-acik,#e4ebfa);color:var(--ana,#1e3a8a);font-weight:600}",
    ".kx-not{color:var(--soluk,#5b6b85);font-style:italic;margin:8px 0}",
    ".kx-hata{color:var(--hata-cizgi,#e05252);background:var(--hata-arka,#fdecec);border-radius:8px;padding:8px 12px;margin:8px 0}",
    ".kx-tex-blok{display:block;max-width:100%;overflow-x:auto;overflow-y:hidden;padding:4px 0}",
    ".kx-tex-yedek{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.92em}",
    ".kx-a{color:var(--sema-a,#2563eb)}.kx-b{color:var(--sema-b,#d97706)}.kx-c{color:var(--sema-c,#059669)}",
    ".kx-sil{color:var(--sema-sil,#dc2626);opacity:.7}",
    ".kx-kutu-a,.kx-kutu-b,.kx-kutu-c,.kx-kutu-sil{border-radius:4px;padding:0 .18em}",
    ".kx-kutu-a{background:var(--sema-a-bg,rgba(37,99,235,.12));box-shadow:inset 0 0 0 1.5px var(--sema-a,#2563eb)}",
    ".kx-kutu-b{background:var(--sema-b-bg,rgba(217,119,6,.14));box-shadow:inset 0 0 0 1.5px var(--sema-b,#d97706)}",
    ".kx-kutu-c{background:var(--sema-c-bg,rgba(5,150,105,.13));box-shadow:inset 0 0 0 1.5px var(--sema-c,#059669)}",
    ".kx-kutu-sil{background:var(--sema-sil-bg,rgba(220,38,38,.11));box-shadow:inset 0 0 0 1.5px var(--sema-sil,#dc2626)}",
    ".kx-ok,.kx-ok-uc{stroke-linecap:round;stroke-linejoin:round}",
    ".kx-ciz{stroke-dasharray:1;stroke-dashoffset:1;animation:kx-ciz .7s ease-out forwards}",
    ".kx-ciz-uc{opacity:0;animation:kx-belir .25s ease-out .55s forwards}",
    "@keyframes kx-ciz{to{stroke-dashoffset:0}}",
    "@keyframes kx-belir{to{opacity:1}}",
    ".kx-hucre{fill:transparent;stroke:none;stroke-width:1.5;transition:fill .25s,stroke .25s}",
    ".kx-matris.izgarali .kx-hucre{stroke:var(--cizgi,#d9e1ee);stroke-width:1}",
    ".kx-hucre-yazi{font-variant-numeric:tabular-nums}",
    ".kx-parantez{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}",
    ".kx-blok{stroke-linejoin:round}",
    ".kx-tutamak{cursor:grab;touch-action:none}",
    ".kx-surukleniyor{cursor:grabbing}",
    ".kx-alistirma{display:grid;gap:10px}",
    ".kx-soru-metin{margin:0}",
    ".kx-cevap{max-width:100%;overflow-x:auto;padding:2px 0}",
    ".kx-izgara-kap{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px}",
    ".kx-izgara{display:inline-grid;grid-template-columns:repeat(var(--kx-sutun,2),minmax(56px,88px));gap:6px;padding:4px 12px;position:relative}",
    ".kx-izgara:not(.parantez){padding:0}",
    ".kx-izgara.parantez::before,.kx-izgara.parantez::after{content:'';position:absolute;top:0;bottom:0;width:8px;border:2px solid currentColor;opacity:.7}",
    ".kx-izgara.parantez::before{left:0;border-right:0;border-radius:6px 0 0 6px}",
    ".kx-izgara.parantez::after{right:0;border-left:0;border-radius:0 6px 6px 0}",
    ".kx-girdi{width:100%;min-width:0;min-height:42px;padding:6px 8px;border:1.5px solid var(--cizgi,#d9e1ee);border-radius:8px;" +
      "background:var(--kart,#fff);color:var(--metin,#15213a);font:inherit;font-size:16px;text-align:center;font-variant-numeric:tabular-nums}",
    ".kx-girdi:focus{outline:none;border-color:var(--ana,#1e3a8a);box-shadow:0 0 0 3px var(--ana-acik,#e4ebfa)}",
    ".kx-girdi.dogru{border-color:var(--sema-c,#059669);background:var(--sema-c-bg,rgba(5,150,105,.13))}",
    ".kx-girdi.yanlis{border-color:var(--sema-sil,#dc2626);background:var(--sema-sil-bg,rgba(220,38,38,.11))}",
    ".kx-girdi.kaba{border-color:var(--sema-b,#d97706);background:var(--sema-b-bg,rgba(217,119,6,.14))}",
    ".kx-girdi.gosterildi{border-style:dashed;color:var(--soluk,#5b6b85)}",
    ".kx-alanlar{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px 12px}",
    ".kx-alan{display:flex;align-items:center;gap:8px}",
    ".kx-alan .kx-girdi{flex:1}",
    ".kx-alan-etiket{white-space:nowrap}",
    ".kx-dugmeler{margin:2px 0}",
    ".kx-geri{min-height:1.5em;margin:0;font-weight:600}",
    ".kx-geri.dogru{color:var(--sema-c,#059669)}.kx-geri.yanlis{color:var(--sema-sil,#dc2626)}.kx-geri.uyari{color:var(--sema-b,#d97706)}",
    ".kx-ipucu,.kx-cozum,.kx-adimlar{border-left:3px solid var(--sema-b,#d97706);background:var(--sema-b-bg,rgba(217,119,6,.14));" +
      "border-radius:0 10px 10px 0;padding:8px 12px}",
    ".kx-cozum{border-left-color:var(--sema-c,#059669);background:var(--sema-c-bg,rgba(5,150,105,.13))}",
    ".kx-adimlar{border-left-color:var(--ana,#1e3a8a);background:var(--ana-acik,#e4ebfa);overflow-x:auto}",
    ".kx-ipucu p,.kx-cozum p{margin:4px 0}",
    ".kx-adimlar ol{margin:0;padding-left:1.4em}.kx-adimlar li{margin:6px 0}",
    ".kx-alt{display:flex;justify-content:flex-end;gap:8px;color:var(--soluk,#5b6b85);font-size:.85em}",
    "@media (prefers-reduced-motion:reduce){.kx-ciz{animation:none;stroke-dashoffset:0}.kx-ciz-uc{animation:none;opacity:1}.kx-hucre{transition:none}}"
  ].join("\n");

  function temelStil() {
    stilEkle("etkilesim-stil", TEMEL_CSS);
  }

  /* ------------------------------------------------------------------ dışa açılan nesne */

  E = Object.freeze({
    surum: SURUM,
    kaydet, liste, bilgi, kur, temizle,
    el, svg, sahne, ok, yazi, renk, zemin, AILELER, matrisCiz,
    kaydirici, dugme, secici,
    MAKROLAR, katexSecenek, tex, texHtml, texDugum, metinDugum, metinTex,
    Kesir, Mat, matrisMetni, girdiCozumle,
    rastgele, yeniTohum, sayi, sayiTex,
    svgNokta, surukle, animasyon, hareketAzalt,
    cevapIzgarasi, cevapDenetle, alistirmaKur,
    motorBagla, motorVar, motor,
    stilEkle
  });
  pencere.Etkilesim = E;
  if (typeof document !== "undefined" && document.head) temelStil();
})(typeof window !== "undefined" ? window : globalThis);
