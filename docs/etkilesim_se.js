/* Matris Öğren · sonlu eleman etkileşimleri ve alıştırmaları (docs/etkilesim_se.js)
 *
 * Çekirdek (etkilesim.js) yüklendikten sonra çalışır; bağımlılığı yoktur. Bütün hesaplar düz JS ile yapılır.
 * Renkler yalnız E.renk() / E.zemin() ile (var(--sema-*)) verilir: açık ve koyu tema otomatik.
 *
 * ETKİLEŞİMLER (BICIM.md 6.2)
 *   yay-sistemi    yaylar, 2x2 eleman matrisleri ve global K'daki parselleri
 *   cubuk-sekil    doğrusal N1, N2; u1, u2 ile şekil değiştirmiş çubuk; k, gerilme
 *   kafes-aci      açı ile c, s ve 4x4 matristeki c^2, cs, s^2 deseni
 *   dof-haritasi   düğüm serbestlikleri, elemanın K'daki parseli, mesnet, Kff / Kfs bölümleri, mekanizma uyarısı
 *   kiris-sekil    Hermite N1-N4 ve elastik eğri
 *   esdeger-yuk    yayılı ve tekil yükün eşdeğer düğüm kuvvetleri
 *   kiris-nvm      kesme ve moment diyagramları (basit, konsol, ankastre-mafsallı)
 *   cerceve-k      6x6 çerçeve elemanı: eksenel (mavi) ve eğilme (turuncu) parseller, dönüşüm
 *   modal-titresim kat kütleleri, det(K - w^2 M) = 0, mod şekilleri
 *   uzay-kafes-cubuk uzay kafes çubuğu: φ, ψ açılarıyla cx, cy, cz; 6x6 global matriste c·cᵀ deseni (ton = |değer|)
 *   uzay-cerceve-k   12x12 uzay çerçeve elemanı: eksenel, iki eğilme ve burulma parselleri; λ ile global dönüşüm
 *
 * ALIŞTIRMALAR (BICIM.md 7): alistirma:cubuk-k, kafes-k, birlestir, sinir-kosulu, yay-seri
 *
 * Birimler: kuvvet kN, uzunluk m (aksi belirtilmedikçe). Düğüm serbestlikleri 1'den numaralanır.
 */
(function () {
  "use strict";
  var E = typeof window !== "undefined" ? window.Etkilesim : (typeof globalThis !== "undefined" ? globalThis.Etkilesim : undefined);
  if (!E) return;

  const el = E.el, svg = E.svg, sahne = E.sahne, ok = E.ok, yazi = E.yazi, renk = E.renk, zemin = E.zemin;
  const kaydirici = E.kaydirici, dugme = E.dugme, secici = E.secici, surukle = E.surukle, animasyon = E.animasyon;
  const hareketAzalt = E.hareketAzalt, texDugum = E.texDugum, metinDugum = E.metinDugum;
  const Kesir = E.Kesir, Mat = E.Mat, sayi = E.sayi, sayiTex = E.sayiTex;

  /* ================================================================== genel yardımcılar */

  const AILE3 = ["a", "b", "c"];
  const MAKRO3 = ["kutua", "kutub", "kutuc"];
  const aileOf = i => AILE3[((i % 3) + 3) % 3];

  function r2(x) { return Math.round(x * 100) / 100; }
  function kenet(x, alt, ust) { return x < alt ? alt : x > ust ? ust : x; }
  function toplam(d) { let t = 0; for (let i = 0; i < d.length; i++) t += d[i]; return t; }

  /* Parametre okuma: bozuk ya da eksik değerde varsayılana düşer (etkileşim hiçbir zaman çökmez). */
  function sayiP(x, vars, alt, ust) {
    let v = typeof x === "string" ? Number(x.replace(",", ".")) : Number(x);
    if (x === null || x === undefined || x === "" || !isFinite(v)) v = vars;
    if (alt !== undefined && v < alt) v = alt;
    if (ust !== undefined && v > ust) v = ust;
    return v;
  }
  function listeP(x, vars, alt, ust, enAz, enCok) {
    let l = x;
    if (typeof l === "string") l = l.split(/[\s,;]+/).filter(Boolean);
    if (!Array.isArray(l)) l = vars;
    l = l.map(v => Number(typeof v === "string" ? v.replace(",", ".") : v)).filter(v => isFinite(v) && v >= alt && v <= ust);
    if (l.length < enAz) l = vars.slice();
    return l.slice(0, enCok);
  }

  /* Matris hücresi için kısa sayı: 0.75, 12.3, 1230, 2.5e5 */
  function kisa(x) {
    if (!isFinite(x)) return "-";
    const a = Math.abs(x);
    if (a < 1e-9) return "0";
    if (a >= 1e4 || a < 1e-2) {
      const p = x.toExponential(1).split("e");
      return p[0].replace(/\.0$/, "") + "e" + parseInt(p[1], 10);
    }
    return String(+x.toPrecision(3));
  }
  function kat(x, basamak) { // katsayı: 0.75, -0.433
    const v = +(+x).toFixed(basamak === undefined ? 3 : basamak);
    return String(Object.is(v, -0) ? 0 : v);
  }
  function guzel(x) { // kaydırıcı üst sınırı için 1, 2, 5, 10 ... basamağı
    if (!(x > 0)) return 1;
    const us = Math.pow(10, Math.floor(Math.log10(x)));
    const f = x / us;
    return us * (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10);
  }
  function bos(d) { while (d.firstChild) d.removeChild(d.firstChild); }

  /* ------------------------------------------------------------------ sayısal doğrusal cebir */

  function sifirMat(n, m) { return Array.from({ length: n }, () => new Array(m === undefined ? n : m).fill(0)); }
  function devrik(A) { return A[0].map((_, j) => A.map(r => r[j])); }
  function carpMat(A, B) {
    const R = sifirMat(A.length, B[0].length);
    for (let i = 0; i < A.length; i++) for (let k = 0; k < B.length; k++) {
      const a = A[i][k];
      if (a === 0) continue;
      for (let j = 0; j < B[0].length; j++) R[i][j] += a * B[k][j];
    }
    return R;
  }
  function enBuyuk(A) { let t = 0; for (const r of A) for (const x of r) t = Math.max(t, Math.abs(x)); return t; }

  /* Kısmi eksen seçmeli Gauss; tekilse null. */
  function coz(A, b) {
    const n = A.length;
    if (!n) return [];
    const M = A.map((r, i) => r.slice().concat([b[i]]));
    const ol = enBuyuk(A) || 1;
    for (let k = 0; k < n; k++) {
      let p = k;
      for (let i = k + 1; i < n; i++) if (Math.abs(M[i][k]) > Math.abs(M[p][k])) p = i;
      if (Math.abs(M[p][k]) < 1e-10 * ol) return null;
      if (p !== k) { const t = M[p]; M[p] = M[k]; M[k] = t; }
      for (let i = k + 1; i < n; i++) {
        const c = M[i][k] / M[k][k];
        if (c === 0) continue;
        for (let j = k; j <= n; j++) M[i][j] -= c * M[k][j];
      }
    }
    const x = new Array(n).fill(0);
    for (let i = n - 1; i >= 0; i--) {
      let s = M[i][n];
      for (let j = i + 1; j < n; j++) s -= M[i][j] * x[j];
      x[i] = s / M[i][i];
    }
    return x;
  }

  /* Sayısal mertebe (tam eksen seçmeli). */
  function mertebe(A, goreli) {
    const n = A.length;
    if (!n) return 0;
    const M = A.map(r => r.slice());
    const m = M[0].length;
    const tol = (goreli || 1e-9) * (enBuyuk(A) || 1);
    let r = 0;
    for (let k = 0; k < m && r < n; k++) {
      let p = r;
      for (let i = r + 1; i < n; i++) if (Math.abs(M[i][k]) > Math.abs(M[p][k])) p = i;
      if (Math.abs(M[p][k]) <= tol) continue;
      const t = M[p]; M[p] = M[r]; M[r] = t;
      for (let i = r + 1; i < n; i++) {
        const c = M[i][k] / M[r][k];
        if (c === 0) continue;
        for (let j = k; j < m; j++) M[i][j] -= c * M[r][j];
      }
      r++;
    }
    return r;
  }

  /* Simetrik özdeğer problemi (Jacobi). → { deg: artan, vek: sütun vektörleri vek[i][j] } */
  function ozdegerSim(S) {
    const n = S.length;
    const a = S.map(r => r.slice());
    const v = sifirMat(n);
    for (let i = 0; i < n; i++) v[i][i] = 1;
    const ol = enBuyuk(S) || 1;
    for (let tur = 0; tur < 80; tur++) {
      let sapma = 0;
      for (let p = 0; p < n - 1; p++) for (let q = p + 1; q < n; q++) sapma += a[p][q] * a[p][q];
      if (sapma < 1e-26 * ol * ol) break;
      for (let p = 0; p < n - 1; p++) for (let q = p + 1; q < n; q++) {
        const apq = a[p][q];
        if (Math.abs(apq) < 1e-300) continue;
        const th = (a[q][q] - a[p][p]) / (2 * apq);
        const t = (th >= 0 ? 1 : -1) / (Math.abs(th) + Math.sqrt(th * th + 1));
        const c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (let k = 0; k < n; k++) { const x = a[k][p], y = a[k][q]; a[k][p] = c * x - s * y; a[k][q] = s * x + c * y; }
        for (let k = 0; k < n; k++) { const x = a[p][k], y = a[q][k]; a[p][k] = c * x - s * y; a[q][k] = s * x + c * y; }
        for (let k = 0; k < n; k++) { const x = v[k][p], y = v[k][q]; v[k][p] = c * x - s * y; v[k][q] = s * x + c * y; }
      }
    }
    const sira = Array.from({ length: n }, (_, i) => i).sort((i, j) => a[i][i] - a[j][j]);
    return { deg: sira.map(i => a[i][i]), vek: Array.from({ length: n }, (_, r) => sira.map(c => v[r][c])) };
  }

  /* ------------------------------------------------------------------ sonlu eleman çekirdeği */

  function yayK(k) { return [[k, -k], [-k, k]]; }

  function kafesK(EAL, c, s) {
    const a = EAL * c * c, b = EAL * c * s, d = EAL * s * s;
    return [[a, b, -a, -b], [b, d, -b, -d], [-a, -b, a, b], [-b, -d, b, d]];
  }

  function kirisK(EI, L) {
    const a = EI / (L * L * L);
    return [
      [12 * a, 6 * L * a, -12 * a, 6 * L * a],
      [6 * L * a, 4 * L * L * a, -6 * L * a, 2 * L * L * a],
      [-12 * a, -6 * L * a, 12 * a, -6 * L * a],
      [6 * L * a, 2 * L * L * a, -6 * L * a, 4 * L * L * a]
    ];
  }

  /* Eksenel ve eğilme katkıları ayrı: yerel eksende [u1 v1 t1 u2 v2 t2] */
  function cerceveEksenel(EA, L) {
    const a = EA / L, K = sifirMat(6);
    K[0][0] = a; K[0][3] = -a; K[3][0] = -a; K[3][3] = a;
    return K;
  }
  function cerceveEgilme(EI, L) {
    const k4 = kirisK(EI, L), K = sifirMat(6), ix = [1, 2, 4, 5];
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) K[ix[i]][ix[j]] = k4[i][j];
    return K;
  }
  function topla2(A, B) { return A.map((r, i) => r.map((x, j) => x + B[i][j])); }
  function donusum6(c, s) {
    return [[c, s, 0, 0, 0, 0], [-s, c, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, c, s, 0], [0, 0, 0, -s, c, 0], [0, 0, 0, 0, 0, 1]];
  }
  function globalYap(kl, c, s) { const T = donusum6(c, s); return carpMat(devrik(T), carpMat(kl, T)); }

  /* Hermite şekil fonksiyonları, x = xi * L */
  function hermite(xi, L) {
    const x2 = xi * xi, x3 = x2 * xi;
    return [1 - 3 * x2 + 2 * x3, L * (xi - 2 * x2 + x3), 3 * x2 - 2 * x3, L * (x3 - x2)];
  }

  /* Birleştirme: elemanlar [{ K, dof: [0 tabanlı] }] → n x n */
  function birlestirK(n, elemanlar) {
    const K = sifirMat(n);
    elemanlar.forEach(e => {
      for (let a = 0; a < e.dof.length; a++) for (let b = 0; b < e.dof.length; b++) K[e.dof[a]][e.dof[b]] += e.K[a][b];
    });
    return K;
  }

  /* ------------------------------------------------------------------ sonlu eleman modeli (BICIM.md 8.3) */

  const SD = { yay: 1, cubuk: 1, kafes: 2, kiris: 2, cerceve: 3 };
  const MESNET_ALAN = {
    yay: ["ux"], cubuk: ["ux"], kafes: ["ux", "uy"], kiris: ["uy", "rz"], cerceve: ["ux", "uy", "rz"]
  };
  const MESNET_DONGU = {
    yay: [[], ["ux"]],
    cubuk: [[], ["ux"]],
    kafes: [[], ["ux", "uy"], ["uy"], ["ux"]],
    kiris: [[], ["uy"], ["uy", "rz"]],
    cerceve: [[], ["ux", "uy"], ["ux", "uy", "rz"], ["uy"]]
  };

  function noktalar(l) { return l.map((p, i) => ({ no: i + 1, x: p[0], y: p[1] })); }
  function mes(d, ...a) { return { dugum: d, ux: a.indexOf("ux") >= 0, uy: a.indexOf("uy") >= 0, rz: a.indexOf("rz") >= 0 }; }

  const HAZIR = {
    "kafes-iki-cubuk": {
      tip: "kafes", baslik: "İki çubuklu kafes",
      dugumler: noktalar([[0, 0], [6, 0], [3, 4]]),
      elemanlar: [{ no: 1, dugumler: [1, 3], E: 200e6, A: 0.001 }, { no: 2, dugumler: [2, 3], E: 200e6, A: 0.001 }],
      mesnetler: [mes(1, "ux", "uy"), mes(2, "ux", "uy")],
      yukler: [{ dugum: 3, Fx: 0, Fy: -10 }]
    },
    "kafes-uc-cubuk": {
      tip: "kafes", baslik: "Üç çubuklu kafes",
      dugumler: noktalar([[0, 0], [3, 0], [6, 0], [3, 4]]),
      elemanlar: [{ no: 1, dugumler: [1, 4], E: 200e6, A: 0.001 }, { no: 2, dugumler: [2, 4], E: 200e6, A: 0.002 }, { no: 3, dugumler: [3, 4], E: 200e6, A: 0.001 }],
      mesnetler: [mes(1, "ux", "uy"), mes(2, "ux", "uy"), mes(3, "ux", "uy")],
      yukler: [{ dugum: 4, Fx: 10, Fy: -20 }]
    },
    "pratt": {
      tip: "kafes", baslik: "Pratt kafes köprü",
      dugumler: noktalar([[0, 0], [3, 0], [6, 0], [9, 0], [12, 0], [3, 3], [6, 3], [9, 3]]),
      elemanlar: [[1, 2], [2, 3], [3, 4], [4, 5], [6, 7], [7, 8], [1, 6], [5, 8], [2, 6], [3, 7], [4, 8], [6, 3], [8, 3]]
        .map((d, i) => ({ no: i + 1, dugumler: d, E: 200e6, A: 0.002 })),
      mesnetler: [mes(1, "ux", "uy"), mes(5, "uy")],
      yukler: [{ dugum: 2, Fy: -10 }, { dugum: 3, Fy: -10 }, { dugum: 4, Fy: -10 }]
    },
    "portal": {
      tip: "cerceve", baslik: "Portal çerçeve",
      dugumler: noktalar([[0, 0], [0, 4], [6, 4], [6, 0]]),
      elemanlar: [{ no: 1, dugumler: [1, 2], E: 200e6, A: 0.01, I: 1e-4 }, { no: 2, dugumler: [2, 3], E: 200e6, A: 0.01, I: 2e-4 },
        { no: 3, dugumler: [4, 3], E: 200e6, A: 0.01, I: 1e-4 }],
      mesnetler: [mes(1, "ux", "uy", "rz"), mes(4, "ux", "uy", "rz")],
      yukler: [{ dugum: 2, Fx: 20 }], yayili: [{ eleman: 2, q: -10 }]
    },
    "kiris-iki-eleman": {
      tip: "kiris", baslik: "İki elemanlı kiriş",
      dugumler: noktalar([[0, 0], [3, 0], [6, 0]]),
      elemanlar: [{ no: 1, dugumler: [1, 2], E: 200e6, I: 2e-5 }, { no: 2, dugumler: [2, 3], E: 200e6, I: 2e-5 }],
      mesnetler: [mes(1, "uy"), mes(3, "uy")],
      yukler: [], yayili: [{ eleman: 1, q: -12 }, { eleman: 2, q: -12 }]
    }
  };
  HAZIR["kafes-pratt-kopru"] = HAZIR.pratt;
  HAZIR["cerceve-portal"] = HAZIR.portal;
  HAZIR["kiris-basit-yayili"] = HAZIR["kiris-iki-eleman"];
  const HAZIR_SIRA = [
    ["kafes-iki-cubuk", "İki çubuk"], ["kafes-uc-cubuk", "Üç çubuk"], ["pratt", "Pratt"], ["portal", "Portal"], ["kiris-iki-eleman", "Kiriş"]
  ];

  /* Şema nesnesini içerde kullanılan biçime çevirir. Geçersizse hata atar. */
  function modelHazirla(m) {
    if (!m || typeof m !== "object") throw new Error("model nesne olmalı");
    const tip = String(m.tip || "");
    if (!SD[tip]) throw new Error("bilinmeyen model tipi: " + tip);
    const d = SD[tip];
    const dug = (m.dugumler || []).map(q => ({ no: Number(q.no), x: Number(q.x) || 0, y: Number(q.y) || 0 }));
    if (dug.length < 2) throw new Error("en az iki düğüm gerekli");
    const poz = new Map();
    dug.forEach((q, i) => poz.set(q.no, i));
    const nd = dug.length, n = nd * d;
    const eler = (m.elemanlar || []).map((e, i) => {
      const a = poz.get(Number(e.dugumler && e.dugumler[0])), b = poz.get(Number(e.dugumler && e.dugumler[1]));
      if (a === undefined || b === undefined || a === b) throw new Error("eleman " + (i + 1) + " düğümleri geçersiz");
      return { no: e.no !== undefined ? Number(e.no) : i + 1, a, b, E: Number(e.E), A: Number(e.A), I: Number(e.I), k: Number(e.k) };
    });
    if (!eler.length) throw new Error("en az bir eleman gerekli");
    const mesnet = new Array(n).fill(false);
    const alanlar = MESNET_ALAN[tip];
    (m.mesnetler || []).forEach(s => {
      const q = poz.get(Number(s.dugum));
      if (q === undefined) return;
      alanlar.forEach((al, c) => { if (s[al]) mesnet[q * d + c] = true; });
    });
    const yuk = new Array(n).fill(0);
    (m.yukler || []).forEach(y => {
      const q = poz.get(Number(y.dugum));
      if (q === undefined) return;
      if (tip === "kafes" || tip === "cerceve") { yuk[q * d] += Number(y.Fx) || 0; yuk[q * d + 1] += Number(y.Fy) || 0; if (tip === "cerceve") yuk[q * d + 2] += Number(y.M) || 0; }
      else if (tip === "kiris") { yuk[q * d] += Number(y.Fy) || 0; yuk[q * d + 1] += Number(y.M) || 0; }
      else yuk[q * d] += Number(y.Fx) || 0;
    });
    const mod = { tip, d, baslik: m.baslik || "", dugum: dug, nd, n, eleman: eler, mesnet, yuk, yayili: m.yayili || [], poz };
    // eleman matrisleri
    mod.eleman.forEach((e, i) => {
      const p = dug[e.a], q = dug[e.b];
      const dx = q.x - p.x, dy = q.y - p.y, L = Math.hypot(dx, dy);
      if (!(L > 0)) throw new Error("eleman " + (i + 1) + " uzunluğu sıfır");
      const c = dx / L, s = dy / L;
      let Ke;
      if (tip === "yay") Ke = yayK(isFinite(e.k) ? e.k : e.E * e.A / L);
      else if (tip === "cubuk") Ke = yayK(e.E * e.A / L);
      else if (tip === "kafes") Ke = kafesK(e.E * e.A / L, c, s);
      else if (tip === "kiris") Ke = kirisK(e.E * e.I, L);
      else Ke = globalYap(topla2(cerceveEksenel(e.E * e.A, L), cerceveEgilme(e.E * e.I, L)), c, s);
      if (Ke.some(r => r.some(x => !isFinite(x)))) throw new Error("eleman " + (i + 1) + " rijitlikleri sayı değil");
      e.L = L; e.c = c; e.s = s; e.K = Ke;
      e.dof = [];
      for (let t = 0; t < d; t++) e.dof.push(e.a * d + t);
      for (let t = 0; t < d; t++) e.dof.push(e.b * d + t);
    });
    mod.K = birlestirK(n, mod.eleman);
    return mod;
  }

  /* ------------------------------------------------------------------ DOM ve SVG yardımcıları */

  const CSS = [
    ".ks-kap{display:grid;gap:10px;min-width:0;max-width:100%}",
    ".ks-kap>*{min-width:0}",
    ".ks-sahne{background:var(--kart,#fff);border:1px solid var(--cizgi,#d9e1ee);border-radius:12px;padding:8px;overflow:hidden}",
    ".ks-svg{display:block;margin:0 auto;max-width:100%;height:auto;overflow:visible}",
    ".ks-iki{display:flex;flex-wrap:wrap;gap:10px}",
    ".ks-iki>*{flex:1 1 300px;min-width:0}",
    ".ks-ayar{display:grid;grid-template-columns:minmax(0,1fr);gap:0 20px}",
    "@media (min-width:640px){.ks-ayar{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}",
    ".ks-ayar .kx-kaydirici{margin:6px 0}",
    ".ks-satir{display:flex;flex-wrap:wrap;gap:8px;align-items:center}",
    ".ks-formul{min-width:0;max-width:100%;overflow-x:auto;overflow-y:hidden;font-size:.95em}",
    ".ks-formul .kx-tex-blok{margin:2px 0;padding:2px 0}",
    ".ks-bilgi{margin:0;padding:8px 12px;border-radius:10px;background:var(--ana-acik,#e4ebfa);color:var(--metin,#15213a);font-size:.93em}",
    ".ks-uyari{margin:0;padding:8px 12px;border-left:3px solid var(--sema-sil,#dc2626);border-radius:0 10px 10px 0;" +
      "background:var(--sema-sil-bg,rgba(220,38,38,.11));font-size:.93em}",
    ".ks-tamam{margin:0;padding:8px 12px;border-left:3px solid var(--sema-c,#059669);border-radius:0 10px 10px 0;" +
      "background:var(--sema-c-bg,rgba(5,150,105,.13));font-size:.93em}",
    ".ks-not{margin:0;color:var(--soluk,#5b6b85);font-size:.88em}",
    ".ks-chip{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:2px 10px;border-radius:10px;border:1.5px solid var(--cizgi,#d9e1ee);" +
      "background:var(--kart,#fff);color:var(--metin,#15213a);font:inherit;cursor:pointer;touch-action:manipulation;max-width:100%;overflow:auto}",
    ".ks-chip[aria-pressed=true]{border-color:var(--ana,#1e3a8a);box-shadow:0 0 0 2px var(--ana-acik,#e4ebfa)}",
    ".ks-chip .katex{font-size:.88em}",
    ".ks-tik{cursor:pointer}",
    ".ks-tik rect,.ks-tik line,.ks-tik circle,.ks-tik path{pointer-events:all}",
    ".ks-soluk{opacity:.42}",
    ".kx-kok svg text.ks-halo{paint-order:stroke;stroke:var(--kart,#fff);stroke-width:3px;stroke-linejoin:round}",
    ".ks-sahne svg :focus-visible{outline:2px solid var(--vurgu,#0e9f8f);outline-offset:2px}",
    ".ks-hucre-yazi{font-variant-numeric:tabular-nums}",
    ".ks-anahat{fill:none;stroke-linecap:round;stroke-linejoin:round}",
    "@media (prefers-reduced-motion:reduce){.ks-kap *{transition:none!important}}"
  ].join("\n");

  function stil() { E.stilEkle("etkilesim-se-stil", CSS); }

  function cerceveKur(kok) {
    stil();
    const k = el("div", { class: "ks-kap" });
    kok.appendChild(k);
    return k;
  }
  function kart() { return el("div", { class: "ks-sahne" }, Array.prototype.slice.call(arguments)); }
  function sv(gen, yuk, etiket) { const s = sahne(gen, yuk, etiket); s.classList.add("ks-svg"); return s; }
  function svBoyut(s, gen, yuk) {
    s.setAttribute("viewBox", "0 0 " + gen + " " + yuk);
    s.setAttribute("width", gen);
    s.setAttribute("height", yuk);
  }
  function formulKutu() { return el("div", { class: "ks-formul" }); }
  function texYaz(kutu, kaynak, blok) { E.tex(kutu, kaynak, blok !== false); }

  function cizgi(x1, y1, x2, y2, o) {
    o = o || {};
    return svg("line", {
      x1: r2(x1), y1: r2(y1), x2: r2(x2), y2: r2(y2), stroke: renk(o.renk || "metin"), "stroke-width": o.kal || 1.5,
      "stroke-dasharray": o.kesik ? (o.kesik === true ? "5 4" : o.kesik) : null, "stroke-linecap": "round", opacity: o.opak === undefined ? null : o.opak, class: o.sinif
    });
  }
  function yol(d, o) {
    o = o || {};
    return svg("path", {
      d, fill: o.dolgu ? zemin(o.dolgu) : "none", stroke: o.renk === null ? "none" : renk(o.renk || "metin"), "stroke-width": o.kal || 1.5,
      "stroke-dasharray": o.kesik ? (o.kesik === true ? "5 4" : o.kesik) : null, "stroke-linecap": "round", "stroke-linejoin": "round",
      opacity: o.opak === undefined ? null : o.opak, class: o.sinif
    });
  }
  function daire(cx, cy, r, o) {
    o = o || {};
    return svg("circle", {
      cx: r2(cx), cy: r2(cy), r, fill: o.dolgu ? (o.dolguHam || zemin(o.dolgu)) : "none", stroke: o.renk ? renk(o.renk) : "none",
      "stroke-width": o.kal || 1.5, class: o.sinif
    });
  }
  function dikdortgen(x, y, w, h, o) {
    o = o || {};
    return svg("rect", {
      x: r2(x), y: r2(y), width: r2(Math.max(0, w)), height: r2(Math.max(0, h)), rx: o.rx === undefined ? 0 : o.rx,
      fill: o.dolgu ? (o.dolguHam || zemin(o.dolgu)) : "none", stroke: o.renk ? renk(o.renk) : "none", "stroke-width": o.kal || 1.5,
      "stroke-dasharray": o.kesik ? "5 4" : null, class: o.sinif
    });
  }
  function yaziH(x, y, metin, o) { // halolu yazı
    o = Object.assign({}, o);
    o.sinif = ["ks-halo", o.sinif].filter(Boolean).join(" ");
    return yazi(x, y, metin, o);
  }

  function yayYolu(x1, y1, x2, y2, adet, genlik) {
    const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
    const bas = Math.min(14, L * 0.18), ic = Math.max(1, L - 2 * bas);
    const pts = [[x1, y1], [x1 + ux * bas, y1 + uy * bas]];
    for (let i = 0; i < adet; i++) {
      const t = bas + ic * (i + 0.5) / adet, sg = i % 2 ? -1 : 1;
      pts.push([x1 + ux * t + nx * genlik * sg, y1 + uy * t + ny * genlik * sg]);
    }
    pts.push([x2 - ux * bas, y2 - uy * bas]);
    pts.push([x2, y2]);
    return "M" + pts.map(q => r2(q[0]) + " " + r2(q[1])).join(" L");
  }

  /* Moment oku: ccw true ise saat yönünün tersi. Yarıçap r, merkez (cx, cy). */
  function momentOku(cx, cy, r, ccw, aile, kal) {
    const g = svg("g", { class: "ks-moment" });
    const n = 26, pts = [];
    const t0 = ccw ? 40 : 140, dt = ccw ? -250 : 250;
    for (let i = 0; i <= n; i++) {
      const t = (t0 + dt * i / n) * Math.PI / 180;
      pts.push([cx + r * Math.cos(t), cy + r * Math.sin(t)]);
    }
    g.appendChild(yol("M" + pts.map(q => r2(q[0]) + " " + r2(q[1])).join(" L"), { renk: aile, kal: kal || 2.2 }));
    const a = pts[n - 1], b = pts[n];
    const ux = b[0] - a[0], uy = b[1] - a[1], u = Math.hypot(ux, uy) || 1;
    g.appendChild(ok(b[0] - ux / u * 3, b[1] - uy / u * 3, b[0], b[1], { renk: aile, kalinlik: kal || 2.2, bas: 7 }));
    return g;
  }

  /* Mesnet simgesi (düğümün altında / yanında). */
  function mesnetSimge(x, y, ux, uy, rz, renkAile) {
    const g = svg("g", { class: "ks-mesnet" });
    const r = renkAile || "metin";
    if (ux && uy && rz) {
      g.appendChild(dikdortgen(x - 11, y + 4, 22, 7, { dolgu: "cizgi", renk: r, kal: 1.4 }));
      for (let i = -9; i <= 9; i += 6) g.appendChild(cizgi(x + i, y + 11, x + i - 5, y + 17, { renk: r, kal: 1 }));
    } else if (ux && uy) {
      g.appendChild(yol("M" + x + " " + (y + 5) + " L" + (x - 9) + " " + (y + 18) + " L" + (x + 9) + " " + (y + 18) + " Z", { renk: r, dolgu: "cizgi", kal: 1.4 }));
      g.appendChild(cizgi(x - 12, y + 19, x + 12, y + 19, { renk: r, kal: 1.4 }));
    } else if (uy) {
      g.appendChild(yol("M" + x + " " + (y + 5) + " L" + (x - 8) + " " + (y + 15) + " L" + (x + 8) + " " + (y + 15) + " Z", { renk: r, dolgu: "cizgi", kal: 1.4 }));
      g.appendChild(daire(x - 4, y + 18, 2.8, { renk: r, kal: 1.2 }));
      g.appendChild(daire(x + 4, y + 18, 2.8, { renk: r, kal: 1.2 }));
      g.appendChild(cizgi(x - 12, y + 21.5, x + 12, y + 21.5, { renk: r, kal: 1.4 }));
    } else if (ux) {
      g.appendChild(yol("M" + (x - 5) + " " + y + " L" + (x - 15) + " " + (y - 8) + " L" + (x - 15) + " " + (y + 8) + " Z", { renk: r, dolgu: "cizgi", kal: 1.4 }));
      g.appendChild(cizgi(x - 19, y - 12, x - 19, y + 12, { renk: r, kal: 1.4 }));
    } else if (rz) {
      g.appendChild(daire(x, y, 11, { renk: r, kal: 1.4 }));
      g.appendChild(cizgi(x - 6, y - 6, x + 6, y + 6, { renk: r, kal: 1.2 }));
    }
    return g;
  }

  /* Tablo: sayı ya da metin hücreli matris. Hücre renkleri aile adı ya da aile dizisi (şerit) olabilir.
   * o: { x, y, w, h, metin(i, j), aile(i, j), soluk(i, j), tikla(i, j, olay), boyut, ust: [..], sol: [..], parantez } */
  function tablo(m, n, o) {
    o = o || {};
    const w = o.w || 44, h = o.h || Math.round(w * 0.78), pay = o.parantez === false ? 0 : 7;
    const ox = o.x || 0, oy = o.y || 0;
    const g = svg("g", { class: "ks-tablo", transform: "translate(" + r2(ox) + " " + r2(oy) + ")" });
    const zem = svg("g"), ust = svg("g");
    const rects = [], yazilar = [];
    for (let i = 0; i < m; i++) {
      rects.push([]); yazilar.push([]);
      for (let j = 0; j < n; j++) {
        const x0 = pay + j * w, y0 = i * h;
        const a = o.aile ? o.aile(i, j) : null;
        const liste = Array.isArray(a) ? a : (a ? [a] : []);
        const hg = svg("g", { class: o.tikla ? "ks-tik" : null });
        if (liste.length > 1) {
          const sw = (w - 2) / liste.length;
          liste.forEach((f, q) => hg.appendChild(svg("rect", { x: r2(x0 + 1 + q * sw), y: y0 + 1, width: r2(sw), height: h - 2, fill: zemin(f) })));
          hg.appendChild(svg("rect", { x: x0 + 1, y: y0 + 1, width: w - 2, height: h - 2, rx: 4, fill: "none", stroke: renk(liste[0]), "stroke-width": 1.3 }));
        } else {
          hg.appendChild(svg("rect", {
            x: x0 + 1, y: y0 + 1, width: w - 2, height: h - 2, rx: 4,
            fill: liste.length ? zemin(liste[0]) : "none", stroke: liste.length ? renk(liste[0]) : renk("kenar"), "stroke-width": liste.length ? 1.4 : 0.8
          }));
        }
        const soluk = o.soluk ? o.soluk(i, j) : false;
        const t = yazi(x0 + w / 2, y0 + h / 2, o.metin ? o.metin(i, j) : "", { boyut: o.boyut || 11, sinif: ["ks-hucre-yazi", soluk && "ks-soluk"].filter(Boolean).join(" ") });
        hg.appendChild(t);
        if (o.tikla) hg.addEventListener("click", ev => o.tikla(i, j, ev));
        zem.appendChild(hg);
        rects[i].push(hg);
        yazilar[i].push(t);
      }
    }
    g.appendChild(zem);
    if (pay) {
      const yuk = m * h, gen = n * w + 2 * pay;
      g.appendChild(svg("path", { class: "ks-anahat", stroke: "currentColor", "stroke-width": 1.5, d: "M" + (pay - 1) + " 1 H2 V" + (yuk - 1) + " H" + (pay - 1) }));
      g.appendChild(svg("path", { class: "ks-anahat", stroke: "currentColor", "stroke-width": 1.5, d: "M" + (gen - pay + 1) + " 1 H" + (gen - 2) + " V" + (yuk - 1) + " H" + (gen - pay + 1) }));
    }
    if (o.ust) o.ust.forEach((s, j) => g.appendChild(yazi(pay + j * w + w / 2, -9, s, { boyut: 10, renk: "soluk" })));
    if (o.sol) o.sol.forEach((s, i) => g.appendChild(yazi(pay - 12, i * h + h / 2, s, { boyut: 10, renk: "soluk", hiza: "sag" })));
    g.appendChild(ust);
    return {
      g, rects, yazilar, w, h,
      genislik: n * w + 2 * pay, yukseklik: m * h, pay,
      hucre(i, j) { const x = ox + pay + j * w, y = oy + i * h; return { x, y, w, h, cx: x + w / 2, cy: y + h / 2 }; },
      kutu(i0, j0, i1, j1, aile, k) {
        k = k || {};
        const r = svg("rect", {
          x: pay + Math.min(j0, j1) * w + 0.5, y: Math.min(i0, i1) * h + 0.5, width: (Math.abs(j1 - j0) + 1) * w - 1, height: (Math.abs(i1 - i0) + 1) * h - 1,
          rx: 6, fill: k.dolgu ? zemin(aile) : "none", stroke: renk(aile), "stroke-width": k.kal || 2, "stroke-dasharray": k.kesik ? "6 4" : null, "pointer-events": "none"
        });
        ust.appendChild(r);
        return r;
      }
    };
  }

  function dugmeSatiri() {
    return el("div", { class: "ks-satir" }, Array.prototype.slice.call(arguments));
  }

  function sl(etiket, min, max, adim, deger, birim, f, bicim) {
    return kaydirici({ etiket, min, max, adim, deger, birim, bicim: bicim || (v => String(+(+v).toPrecision(4))), degisince: f });
  }
  function tutamak(aile, aria) {
    return svg("circle", {
      r: 11, cx: 0, cy: 0, fill: zemin(aile), stroke: renk(aile), "stroke-width": 2.4, role: "button", "aria-label": aria, tabindex: 0,
      style: { cursor: "grab" }
    });
  }
  function tutKonum(t, x, y) { t.setAttribute("cx", r2(x)); t.setAttribute("cy", r2(y)); }
  function duvarCiz(xSag, y0, y1) {
    const g = svg("g");
    g.appendChild(dikdortgen(xSag - 10, y0, 10, y1 - y0, { dolgu: "cizgi", renk: "metin", kal: 1.4 }));
    for (let y = y0 + 4; y < y1 - 6; y += 10) g.appendChild(cizgi(xSag - 10, y + 8, xSag - 18, y, { renk: "metin", kal: 1 }));
    return g;
  }
  function eksenOku(x1, y1, x2, y2, etiket, aile) {
    const g = svg("g");
    g.appendChild(ok(x1, y1, x2, y2, { renk: aile || "soluk", kalinlik: 1.6, bas: 6 }));
    if (etiket) g.appendChild(yazi(x2 + (x2 > x1 ? 9 : x2 < x1 ? -9 : 0), y2 + (y2 < y1 ? -9 : y2 > y1 ? 9 : 0), etiket, { renk: aile || "soluk", boyut: 11 }));
    return g;
  }

  /* ================================================================== 1. yay-sistemi */

  const MAK = ["\\ka", "\\kb", "\\kc"];

  E.kaydet("yay-sistemi", function (kok, p) {
    const kap = cerceveKur(kok);
    let ks = listeP(p.k, [1000, 2000], 1, 1e7, 1, 5);
    let P = sayiP(p.P, 10, 0.01, 1e6);
    let duzen = p.duzen === "paralel" ? "paralel" : "seri";
    let sec = -1, f = 1, anim = null, odak = null, g = null;
    const W = 560, H = 170, X0 = 48;
    const sd = sv(W, H, "Yay sistemi şeması");
    const sk = sv(300, 200, "Global rijitlik matrisi K ve yay parselleri");
    const formul = formulKutu();
    const ayarlar = el("div", { class: "ks-ayar" });
    const butonlar = dugmeSatiri();

    function hesap() {
      const n = ks.length;
      let K, u;
      if (duzen === "seri") {
        K = birlestirK(n + 1, ks.map((k, i) => ({ K: yayK(k), dof: [i, i + 1] })));
        const Kff = K.slice(1).map(r => r.slice(1));
        const F = new Array(n).fill(0); F[n - 1] = P;
        u = [0].concat(coz(Kff, F) || new Array(n).fill(0));
      } else {
        const t = toplam(ks);
        K = yayK(t); u = [0, P / t];
      }
      const kEq = duzen === "seri" ? 1 / toplam(ks.map(k => 1 / k)) : toplam(ks);
      return { n, K, u, kEq, N: K.length };
    }
    let h = hesap();
    const olcek = 60 / Math.max(Math.abs(h.u[h.u.length - 1]), 1e-12);
    const kay = v => kenet(v * olcek * f, -70, 70);
    const kapsar = (e, i, j) => duzen === "paralel" || ((i === e || i === e + 1) && (j === e || j === e + 1));

    function yukCiz(x, y) {
      bos(g.yuk);
      g.yuk.appendChild(ok(x, y, x + 52, y, { renk: "sil", kalinlik: 3.4, bas: 10 }));
      g.yuk.appendChild(yaziH(x + 26, y - 17, "P = " + kisa(P) + " kN", { renk: "sil", boyut: 12, kalin: true }));
    }
    function konum() {
      if (!g) return;
      if (duzen === "seri") {
        const n = ks.length;
        const xs = h.u.map((u, i) => X0 + i * g.d + kay(u));
        xs.forEach((x, i) => { g.dugum[i].setAttribute("cx", r2(x)); g.numara[i].setAttribute("x", r2(x)); });
        ks.forEach((k, e) => {
          g.yay[e].setAttribute("d", yayYolu(xs[e], g.Y, xs[e + 1], g.Y, 7, 9));
          g.ad[e].setAttribute("x", r2((xs[e] + xs[e + 1]) / 2));
        });
        yukCiz(xs[n] + 14, g.Y);
      } else {
        const xp = X0 + 330 + kay(h.u[1]);
        g.plaka.setAttribute("x", r2(xp));
        ks.forEach((k, e) => g.yay[e].setAttribute("d", yayYolu(X0, g.ys[e], xp, g.ys[e], 9, 8)));
        g.dugum[1].setAttribute("cx", r2(xp + 5)); g.numara[1].setAttribute("x", r2(xp + 5));
        yukCiz(xp + 22, H / 2);
      }
    }
    function sec_(e) { sec = sec === e ? -1 : e; odak = "y" + e; ciz(); }

    function ciz() {
      h = hesap();
      const n = ks.length, N = h.N;
      bos(sd);
      g = { yay: [], ad: [], dugum: [], numara: [], yuk: svg("g"), d: Math.min(100, 340 / n), Y: H / 2, ys: [] };
      const sec_g = svg("g");
      if (duzen === "seri") {
        sd.appendChild(duvarCiz(X0 - 12, 40, 130));
        ks.forEach((k, e) => {
          const a = aileOf(e);
          const yol_ = svg("path", {
            fill: "none", stroke: renk(a), "stroke-width": sec === e ? 4.2 : 2.8, "stroke-linecap": "round", "stroke-linejoin": "round",
            opacity: sec < 0 || sec === e ? 1 : 0.45
          });
          sd.appendChild(yol_); g.yay.push(yol_);
          const t = yaziH(0, g.Y - 24, "k" + (e + 1) + " = " + kisa(k), { renk: a, boyut: 11, kalin: true });
          sd.appendChild(t); g.ad.push(t);
        });
        for (let i = 0; i <= n; i++) {
          const c = daire(0, g.Y, 11, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 2 });
          sd.appendChild(c); g.dugum.push(c);
          const t = yazi(0, g.Y, String(i + 1), { boyut: 11, kalin: true });
          sd.appendChild(t); g.numara.push(t);
        }
        ks.forEach((k, e) => {
          sec_g.appendChild(svg("rect", {
            x: X0 + e * g.d + 12, y: 40, width: g.d - 24, height: 90, fill: "transparent", class: "ks-tik", tabindex: 0, role: "button",
            "aria-label": "Yay " + (e + 1) + " parselini vurgula", dataset: { id: "y" + e },
            onclick: () => sec_(e), onkeydown: ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); sec_(e); } }
          }));
        });
      } else {
        sd.appendChild(duvarCiz(X0, 10, 160));
        const plaka = dikdortgen(0, 10, 10, 150, { dolgu: "a", renk: "a", kal: 1.6 });
        sd.appendChild(plaka); g.plaka = plaka;
        ks.forEach((k, e) => {
          g.ys.push(24 + (e + 0.5) * (H - 48) / n);
          const a = aileOf(e);
          const yol_ = svg("path", {
            fill: "none", stroke: renk(a), "stroke-width": sec === e ? 4.2 : 2.8, "stroke-linecap": "round", "stroke-linejoin": "round",
            opacity: sec < 0 || sec === e ? 1 : 0.45
          });
          sd.appendChild(yol_); g.yay.push(yol_);
          sd.appendChild(yaziH(X0 + 28, g.ys[e] - 11, "k" + (e + 1), { renk: a, boyut: 10, kalin: true }));
        });
        [X0 - 5, 0].forEach((x, i) => {
          const c = daire(x, 10, 9, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 1.8 });
          sd.appendChild(c); g.dugum.push(c);
          const t = yazi(x, 10, String(i + 1), { boyut: 10, kalin: true });
          sd.appendChild(t); g.numara.push(t);
        });
        g.dugum[0].setAttribute("cx", X0 + 5); g.numara[0].setAttribute("x", X0 + 5);
        ks.forEach((k, e) => {
          sec_g.appendChild(svg("rect", {
            x: X0 + 30, y: g.ys[e] - 12, width: 250, height: 24, fill: "transparent", class: "ks-tik", tabindex: 0, role: "button",
            "aria-label": "Yay " + (e + 1) + " parselini vurgula", dataset: { id: "y" + e },
            onclick: () => sec_(e), onkeydown: ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); sec_(e); } }
          }));
        });
      }
      sd.appendChild(g.yuk);
      sd.appendChild(sec_g);
      konum();

      // K matrisi
      const w = N > 4 ? 42 : 54, hh = 32;
      const T = tablo(N, N, {
        x: 36, y: 24, w, h: hh, boyut: 11,
        metin: (i, j) => kisa(h.K[i][j]),
        aile: (i, j) => { const l = []; ks.forEach((_, e) => { if (kapsar(e, i, j)) l.push(aileOf(e)); }); return l; },
        soluk: (i, j) => h.K[i][j] === 0 || (sec >= 0 && !kapsar(sec, i, j)),
        ust: Array.from({ length: N }, (_, j) => "u" + (j + 1)), sol: Array.from({ length: N }, (_, i) => "u" + (i + 1))
      });
      bos(sk);
      sk.appendChild(T.g);
      if (sec >= 0) {
        if (duzen === "seri") T.kutu(sec, sec, sec + 1, sec + 1, aileOf(sec), { kal: 2.6 });
        else T.kutu(0, 0, 1, 1, aileOf(sec), { kal: 2.6 });
      }
      svBoyut(sk, 36 + T.genislik + 8, 24 + T.yukseklik + 28);
      T.g.appendChild(yazi(T.genislik / 2 + 0, T.yukseklik + 15, "K  [kN/m]", { renk: "soluk", boyut: 11 }));

      const bicim = v => kisa(v);
      let tx;
      if (duzen === "seri") {
        tx = "\\begin{aligned}k_{eq}&=\\left(\\sum_i \\frac{1}{k_i}\\right)^{-1}=" + bicim(h.kEq) + "\\ \\text{kN/m}\\\\" +
          "u_{" + (n + 1) + "}&=\\frac{P}{k_{eq}}=" + bicim(h.u[n] * 1000) + "\\ \\text{mm},\\qquad R_1=-P=" + bicim(-P) + "\\ \\text{kN}\\end{aligned}";
      } else {
        tx = "\\begin{aligned}k_{eq}&=\\sum_i k_i=" + bicim(h.kEq) + "\\ \\text{kN/m}\\\\" +
          "u_{2}&=\\frac{P}{k_{eq}}=" + bicim(h.u[1] * 1000) + "\\ \\text{mm},\\qquad R_1=-P=" + bicim(-P) + "\\ \\text{kN}\\end{aligned}";
      }
      texYaz(formul, tx);
      if (odak) {
        const x = sd.querySelector('[data-id="' + odak + '"]');
        odak = null;
        if (x) x.focus({ preventScroll: true });
      }
    }

    function ayarYap() {
      bos(ayarlar);
      ayarlar.appendChild(sl("$P$", 0.5, Math.max(50, P * 2), 0.5, P, "kN", v => { P = v; ciz(); }).kok);
      ks.forEach((k, i) => {
        ayarlar.appendChild(sl("$k_" + (i + 1) + "$", 100, Math.max(5000, k * 2), 100, k, "kN/m", v => { ks[i] = v; ciz(); }, v => String(Math.round(v))).kok);
      });
    }
    function oyna() {
      if (anim) anim.durdur();
      anim = null;
      if (hareketAzalt()) { f = 1; konum(); return; }
      f = 0;
      anim = animasyon(kap, t => {
        if (t > 3.4) { f = 1; konum(); return false; }
        f = 1 - Math.exp(-2.6 * t) * Math.cos(9 * t);
        konum();
      });
    }

    const sDuzen = secici([{ deger: "seri", etiket: "Seri" }, { deger: "paralel", etiket: "Paralel" }], duzen, v => {
      duzen = v; sec = -1; ayarYap(); ciz(); oyna();
    });
    butonlar.appendChild(sDuzen.kok);
    butonlar.appendChild(dugme("+ yay", () => {
      if (ks.length >= 5) return;
      ks.push(ks[ks.length - 1] || 1000); sec = -1; ayarYap(); ciz(); oyna();
    }, { baslik: "Yay ekle (en çok 5)" }));
    butonlar.appendChild(dugme("− yay", () => {
      if (ks.length <= 1) return;
      ks.pop(); sec = -1; ayarYap(); ciz(); oyna();
    }, { baslik: "Yay çıkar (en az 1)" }));
    butonlar.appendChild(dugme("Yükü yeniden uygula", () => oyna(), { ana: true }));

    kap.appendChild(el("div", { class: "ks-iki" }, kart(sd), kart(sk)));
    kap.appendChild(butonlar);
    kap.appendChild(ayarlar);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ks-not" }, "Bir yaya dokun: 2×2 matrisinin K'daki parseli vurgulanır. Ortak düğümde iki renk yan yana görünür ve değerler toplanır."));
    ayarYap();
    ciz();
    oyna();
    return { yok_et() { if (anim) anim.durdur(); } };
  }, {
    baslik: "Yay sistemi: eleman matrisleri K'da toplanır",
    aciklama: "Her yayın 2x2 matrisi kendi renginde; ortak düğümde parseller üst üste biner. Rijitlikleri ve yükü değiştir, yer değiştirmeyi izle.",
    varsayilan: { k: [1000, 2000], P: 10, duzen: "seri" }
  });

  /* ================================================================== 2. cubuk-sekil */

  E.kaydet("cubuk-sekil", function (kok, p) {
    const kap = cerceveKur(kok);
    const Em = sayiP(p.E, 200e6, 1, 1e12), A = sayiP(p.A, 0.001, 1e-9, 100), L = sayiP(p.L, 2, 0.01, 1000), P = sayiP(p.P, 100, 0, 1e9);
    const EA = Em * A, k = EA / L;
    let delta = P * L / EA * 1000; // mm
    if (!(delta > 1e-9) || !isFinite(delta)) delta = 1;
    const aralik = 2 * delta;
    let u1 = 0, u2 = delta, xi = 0.5;
    const W = 560, H = 290, X0 = 70, LP = 400, Yb = 66, s = 38 / aralik;
    const sd = sv(W, H, "Doğrusal çubuk elemanı: şekil fonksiyonları ve şekil değiştirmiş çubuk");
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const h1 = tutamak("a", "Sol düğüm yer değiştirmesi u1"), h2 = tutamak("b", "Sağ düğüm yer değiştirmesi u2");
    const hx = tutamak("c", "ξ konumu");
    tut.appendChild(h1); tut.appendChild(h2); tut.appendChild(hx);
    const formul = formulKutu(), formul2 = formulKutu();
    const bil = (v, b) => String(+v.toPrecision(b || 3));
    const sl1 = sl("$u_1$", -aralik, aralik, aralik / 200, u1, "mm", v => { u1 = v; ciz(); }, v => kat(v, 4));
    const sl2 = sl("$u_2$", -aralik, aralik, aralik / 200, u2, "mm", v => { u2 = v; ciz(); }, v => kat(v, 4));
    const sl3 = sl("$\\xi=x/L$", 0, 1, 0.01, xi, "", v => { xi = v; ciz(); }, v => kat(v, 2));

    function ciz() {
      bos(dyn);
      const eps = (u2 - u1) / (L * 1000);
      const aile = Math.abs(eps) < 1e-12 ? "cizgi" : eps > 0 ? "c" : "sil";
      // hayalet çubuk
      dyn.appendChild(dikdortgen(X0, Yb - 14, LP, 28, { renk: "soluk", kal: 1.2, kesik: true }));
      dyn.appendChild(yaziH(X0 + LP / 2, Yb - 28, "Yükleme öncesi (L = " + bil(L) + " m)", { renk: "soluk", boyut: 11 }));
      // şekil değiştirmiş çubuk
      const ust = [], alt = [];
      for (let i = 0; i <= 20; i++) {
        const x = i / 20, ux = (1 - x) * u1 + x * u2;
        const px = X0 + x * LP + s * ux;
        ust.push(r2(px) + " " + (Yb - 14 + 38)); alt.push(r2(px) + " " + (Yb + 14 + 38));
      }
      const poly = [];
      for (let i = 0; i <= 20; i++) { const x = i / 20, ux = (1 - x) * u1 + x * u2; poly.push([X0 + x * LP + s * ux, Yb - 14]); }
      for (let i = 20; i >= 0; i--) { const x = i / 20, ux = (1 - x) * u1 + x * u2; poly.push([X0 + x * LP + s * ux, Yb + 14]); }
      dyn.appendChild(svg("path", {
        d: "M" + poly.map(q => r2(q[0]) + " " + r2(q[1])).join(" L") + " Z", fill: zemin(aile), stroke: renk(aile), "stroke-width": 2.2, "stroke-linejoin": "round"
      }));
      // kuvvet okları f1, f2
      const f1 = k * (u1 - u2) / 1000, f2 = -f1;
      const fmax = k * aralik * 2 / 1000 || 1;
      const x1 = X0 + s * u1, x2 = X0 + LP + s * u2;
      const uz = f => 6 + 54 * Math.min(1, Math.abs(f) / fmax);
      if (Math.abs(f1) > 1e-9 * fmax) dyn.appendChild(ok(x1, Yb + 36, x1 + Math.sign(f1) * uz(f1), Yb + 36, { renk: "sil", kalinlik: 3, bas: 9, etiket: "f1" }));
      if (Math.abs(f2) > 1e-9 * fmax) dyn.appendChild(ok(x2, Yb + 36, x2 + Math.sign(f2) * uz(f2), Yb + 36, { renk: "sil", kalinlik: 3, bas: 9, etiket: "f2" }));
      dyn.appendChild(yaziH(x1, Yb + 52 + 4, "1", { boyut: 11, renk: "a", kalin: true }));
      dyn.appendChild(yaziH(x2, Yb + 56, "2", { boyut: 11, renk: "b", kalin: true }));
      // ξ işareti çubuk üstünde
      const ux = (1 - xi) * u1 + xi * u2, xp = X0 + xi * LP + s * ux;
      dyn.appendChild(daire(xp, Yb, 4.5, { dolgu: "c", dolguHam: renk("c") }));
      const xc = X0 + xi * LP;
      dyn.appendChild(cizgi(xc, Yb + 16, xc, 258, { renk: "c", kal: 1.2, kesik: true }));
      // N1, N2 grafiği
      const Y1 = 178, Y0 = 252;
      dyn.appendChild(cizgi(X0, Y0, X0 + LP, Y0, { renk: "soluk", kal: 1.2 }));
      dyn.appendChild(cizgi(X0, Y1, X0, Y0, { renk: "soluk", kal: 1.2 }));
      dyn.appendChild(cizgi(X0, Y1, X0 + LP, Y1, { renk: "kenar", kal: 1, kesik: true }));
      dyn.appendChild(yazi(X0 - 8, Y1, "1", { hiza: "sag", boyut: 11, renk: "soluk" }));
      dyn.appendChild(yazi(X0 - 8, Y0, "0", { hiza: "sag", boyut: 11, renk: "soluk" }));
      dyn.appendChild(yazi(X0, Y0 + 14, "ξ = 0", { boyut: 11, renk: "soluk" }));
      dyn.appendChild(yazi(X0 + LP, Y0 + 14, "ξ = 1", { boyut: 11, renk: "soluk" }));
      dyn.appendChild(cizgi(X0, Y1, X0 + LP, Y0, { renk: "a", kal: 3 }));
      dyn.appendChild(cizgi(X0, Y0, X0 + LP, Y1, { renk: "b", kal: 3 }));
      dyn.appendChild(yaziH(X0 + 36, Y1 + 12, "N1 = 1 − ξ", { renk: "a", boyut: 12, kalin: true, hiza: "sol" }));
      dyn.appendChild(yaziH(X0 + LP - 36, Y1 + 12, "N2 = ξ", { renk: "b", boyut: 12, kalin: true, hiza: "sag" }));
      const N1 = 1 - xi, N2 = xi;
      dyn.appendChild(daire(xc, Y0 - N1 * (Y0 - Y1), 5, { dolgu: "a", dolguHam: renk("a") }));
      dyn.appendChild(daire(xc, Y0 - N2 * (Y0 - Y1), 5, { dolgu: "b", dolguHam: renk("b") }));
      dyn.appendChild(yaziH(xc + (xi > 0.7 ? -8 : 8), Y0 - N1 * (Y0 - Y1) - 10, kat(N1, 2), { renk: "a", boyut: 11, hiza: xi > 0.7 ? "sag" : "sol" }));
      dyn.appendChild(yaziH(xc + (xi > 0.7 ? -8 : 8), Y0 - N2 * (Y0 - Y1) - 10, kat(N2, 2), { renk: "b", boyut: 11, hiza: xi > 0.7 ? "sag" : "sol" }));
      // tutamaklar
      tutKonum(h1, x1, Yb); tutKonum(h2, x2, Yb); tutKonum(hx, xc, Y1 - 14);

      const sigma = Em * eps / 1000, Nn = Em * eps * A;
      texYaz(formul, "\\begin{aligned}u(\\xi)&=\\ka{N_1}\\,u_1+\\kb{N_2}\\,u_2=\\ka{" + kat(N1, 2) + "}\\,(" + kisa(u1) + ")+\\kb{" + kat(N2, 2) + "}\\,(" + kisa(u2) + ")=" + kisa(ux) + "\\ \\text{mm}\\\\" +
        "\\varepsilon&=\\frac{u_2-u_1}{L}=" + kisa(eps * 1e3) + "\\times10^{-3},\\quad \\sigma=E\\varepsilon=" + kisa(sigma) + "\\ \\text{MPa},\\quad N=\\sigma A=" + kisa(Nn) + "\\ \\text{kN}" +
        (Math.abs(eps) < 1e-12 ? "" : (eps > 0 ? "\\ \\text{(çekme)}" : "\\ \\text{(basınç)}")) + "\\end{aligned}");
      texYaz(formul2, "\\begin{bmatrix}f_1\\\\f_2\\end{bmatrix}=\\underbrace{\\frac{EA}{L}}_{" + kisa(k) + "\\,\\text{kN/m}}\\begin{bmatrix}1&-1\\\\-1&1\\end{bmatrix}\\begin{bmatrix}\\ka{" + kisa(u1) + "}\\\\\\kb{" + kisa(u2) + "}\\end{bmatrix}\\!\\cdot 10^{-3}=\\begin{bmatrix}" + kisa(f1) + "\\\\" + kisa(f2) + "\\end{bmatrix}\\text{kN}");
    }

    surukle(h1, { svg: sd, tasi: q => { u1 = kenet((q.x - X0) / s, -aralik, aralik); sl1.ayarla(u1, true); ciz(); }, klavye: dx => { u1 = kenet(u1 + dx * aralik / 100, -aralik, aralik); sl1.ayarla(u1, true); ciz(); } });
    surukle(h2, { svg: sd, tasi: q => { u2 = kenet((q.x - X0 - LP) / s, -aralik, aralik); sl2.ayarla(u2, true); ciz(); }, klavye: dx => { u2 = kenet(u2 + dx * aralik / 100, -aralik, aralik); sl2.ayarla(u2, true); ciz(); } });
    surukle(hx, { svg: sd, tasi: q => { xi = kenet((q.x - X0) / LP, 0, 1); sl3.ayarla(xi, true); ciz(); }, klavye: dx => { xi = kenet(xi + dx / 100, 0, 1); sl3.ayarla(xi, true); ciz(); } });

    kap.appendChild(kart(sd));
    kap.appendChild(el("div", { class: "ks-ayar" }, sl1.kok, sl2.kok, sl3.kok));
    kap.appendChild(dugmeSatiri(
      dugme("Sıfırla", () => { u1 = 0; u2 = delta; xi = 0.5; sl1.ayarla(u1, true); sl2.ayarla(u2, true); sl3.ayarla(xi, true); ciz(); }, { baslik: "Başlangıç: u1 = 0, u2 = PL/EA" }),
      dugme("Rijit hareket", () => { u1 = delta; u2 = delta; sl1.ayarla(u1, true); sl2.ayarla(u2, true); ciz(); }, { baslik: "u1 = u2: şekil değişmez, kuvvet sıfır" }),
      dugme("Basınç", () => { u1 = delta; u2 = 0; sl1.ayarla(u1, true); sl2.ayarla(u2, true); ciz(); }, { baslik: "u1 > u2: çubuk kısalır" })));
    kap.appendChild(formul);
    kap.appendChild(formul2);
    kap.appendChild(el("p", { class: "ks-not" }, "Mavi ve turuncu daireleri / çubuk uçlarını sürükle. E = " + kisa(Em) + " kN/m², A = " + bil(A) + " m², L = " + bil(L) + " m, P = " + bil(P) + " kN için u₂ = PL/EA = " + bil(delta) + " mm."));
    ciz();
  }, {
    baslik: "Çubuk elemanı: doğrusal şekil fonksiyonları",
    aciklama: "u1 ve u2 ile çubuğu şekil değiştir; N1, N2 ve k = EA/L ile f = k u ilişkisini gör.",
    varsayilan: { E: 200e6, A: 0.001, L: 2, P: 100 }
  });

  /* ================================================================== 3. kafes-aci */

  E.kaydet("kafes-aci", function (kok, p) {
    const kap = cerceveKur(kok);
    const Em = sayiP(p.E, 200e6, 1, 1e12), A = sayiP(p.A, 0.001, 1e-9, 100), L = sayiP(p.L, 5, 0.01, 1000);
    const EAL = Em * A / L;
    let aci = ((sayiP(p.aci, 30) % 360) + 360) % 360;
    let gorunum = "katsayi";
    const CX = 150, CY = 150, R = 110;
    const sd = sv(300, 300, "Kafes çubuğu: açıyı sürükleyerek değiştir");
    const sm = sv(320, 240, "Kafes elemanı 4x4 rijitlik matrisi");
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const hd = tutamak("b", "Çubuğun ucu: açı");
    tut.appendChild(hd);
    const formul = formulKutu(), formul2 = formulKutu();
    const slA = sl("$\\theta$", 0, 360, 0.01, aci, "°", v => { aci = v; ciz(); }, v => String(+v.toFixed(2)));
    const cc = () => Math.cos(aci * Math.PI / 180), ss = () => Math.sin(aci * Math.PI / 180);
    const pt = (c, s_) => (Math.abs(c) < 5e-10 ? 0 : c) + "," + s_;

    function ciz() {
      bos(dyn);
      const c = cc(), s_ = ss();
      const cz = Math.abs(c) < 1e-10 ? 0 : c, sz = Math.abs(s_) < 1e-10 ? 0 : s_;
      const nx = CX + R * c, ny = CY - R * s_;
      dyn.appendChild(eksenOku(30, CY, 276, CY, "x"));
      dyn.appendChild(eksenOku(CX, 270, CX, 24, "y"));
      // izdüşümler
      dyn.appendChild(cizgi(CX, CY, nx, CY, { renk: "a", kal: 3, kesik: true }));
      dyn.appendChild(cizgi(nx, CY, nx, ny, { renk: "c", kal: 3, kesik: true }));
      if (Math.abs(R * c) > 22) dyn.appendChild(yaziH(CX + R * c / 2, CY + (s_ >= 0 ? 14 : -14), "c = " + kat(cz, 3), { renk: "a", boyut: 12, kalin: true }));
      if (Math.abs(R * s_) > 22) dyn.appendChild(yaziH(nx + (c >= 0 ? 16 : -16), (CY + ny) / 2, "s = " + kat(sz, 3), { renk: "c", boyut: 12, kalin: true, hiza: c >= 0 ? "sol" : "sag" }));
      // çubuk
      dyn.appendChild(cizgi(CX, CY, nx, ny, { renk: "metin", kal: 5 }));
      // açı yayı
      const yay = [];
      const ad = Math.max(1, Math.round(aci / 5));
      for (let i = 0; i <= ad; i++) { const t = (aci * i / ad) * Math.PI / 180; yay.push(r2(CX + 34 * Math.cos(t)) + " " + r2(CY - 34 * Math.sin(t))); }
      if (aci > 0.5) dyn.appendChild(yol("M" + yay.join(" L"), { renk: "b", kal: 2.4 }));
      const am = aci / 2 * Math.PI / 180;
      if (aci > 14 && aci < 346) dyn.appendChild(yaziH(CX + 52 * Math.cos(am), CY - 52 * Math.sin(am), "θ", { renk: "b", boyut: 13, kalin: true }));
      // düğümler
      dyn.appendChild(daire(CX, CY, 8, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 2.2 }));
      dyn.appendChild(yazi(CX, CY, "1", { boyut: 10, kalin: true }));
      dyn.appendChild(yaziH(CX - 20, CY + 24, "u1, v1", { renk: "soluk", boyut: 11 }));
      dyn.appendChild(yaziH(nx + (c >= 0 ? 20 : -20), ny + (s_ >= 0 ? -22 : 22), "u2, v2", { renk: "soluk", boyut: 11 }));
      tutKonum(hd, nx, ny);

      // matris
      bos(sm);
      const kt = kafesK(1, c, s_);
      const deger = (i, j) => gorunum === "katsayi" ? kat(kt[i][j], 3) : kisa(EAL * kt[i][j]);
      const T = tablo(4, 4, {
        x: 36, y: 24, w: 62, h: 40, boyut: 12,
        metin: deger,
        aile: (i, j) => (i % 2 === 0 && j % 2 === 0) ? "a" : (i % 2 === 1 && j % 2 === 1) ? "c" : "b",
        soluk: (i, j) => Math.abs(kt[i][j]) < 5e-10,
        ust: ["u1", "v1", "u2", "v2"], sol: ["u1", "v1", "u2", "v2"]
      });
      sm.appendChild(T.g);
      [[0, 0], [0, 2], [2, 0], [2, 2]].forEach(b => { T.kutu(b[0], b[1], b[0] + 1, b[1] + 1, "kenar", { kesik: true, kal: 1.6 }); });
      svBoyut(sm, 36 + T.genislik + 10, 24 + T.yukseklik + 28);
      sm.appendChild(yazi(36 + T.genislik / 2, 24 + T.yukseklik + 16, gorunum === "katsayi" ? "k / (EA/L)" : "k  [kN/m]", { renk: "soluk", boyut: 11 }));

      let not = "";
      if (Math.abs(sz) < 1e-9) not = "Yatay çubuk: yalnızca u terimleri dolu (s = 0).";
      else if (Math.abs(cz) < 1e-9) not = "Düşey çubuk: yalnızca v terimleri dolu (c = 0).";
      else if (Math.abs(Math.abs(cz) - Math.abs(sz)) < 1e-6) not = "45° gibi simetrik açıda c² = cs = s² = ½.";
      texYaz(formul, "c=\\cos\\theta=" + kat(cz, 4) + ",\\quad s=\\sin\\theta=" + kat(sz, 4) + ",\\quad \\frac{EA}{L}=" + kisa(EAL) + "\\ \\text{kN/m}" +
        (not ? "\\quad\\text{" + not.replace(/%/g, "") + "}" : ""));
    }
    texYaz(formul2, "\\mathbf k=\\frac{EA}{L}\\begin{bmatrix}\\ka{c^2}&\\kb{cs}&-\\ka{c^2}&-\\kb{cs}\\\\ \\kb{cs}&\\kc{s^2}&-\\kb{cs}&-\\kc{s^2}\\\\ -\\ka{c^2}&-\\kb{cs}&\\ka{c^2}&\\kb{cs}\\\\ -\\kb{cs}&-\\kc{s^2}&\\kb{cs}&\\kc{s^2}\\end{bmatrix}");

    function ayar(v) { aci = ((v % 360) + 360) % 360; slA.ayarla(aci, true); ciz(); }
    surukle(hd, {
      svg: sd,
      tasi: q => {
        let a = Math.atan2(CY - q.y, q.x - CX) * 180 / Math.PI;
        if (a < 0) a += 360;
        const yakin = Math.round(a / 15) * 15;
        a = Math.abs(a - yakin) < 2 ? yakin % 360 : Math.round(a * 10) / 10;
        ayar(a);
      },
      klavye: dx => ayar(aci + dx)
    });
    const sg = secici([{ deger: "katsayi", etiket: "Katsayı" }, { deger: "kNm", etiket: "kN/m" }], gorunum, v => { gorunum = v; ciz(); });
    const hizli = dugmeSatiri();
    [[0, "0°"], [30, "30°"], [45, "45°"], [60, "60°"], [90, "90°"], [36.87, "3-4-5 (36,87°)"], [135, "135°"]].forEach(a => hizli.appendChild(dugme(a[1], () => ayar(a[0]))));
    kap.appendChild(el("div", { class: "ks-iki" }, kart(sd), kart(sm)));
    kap.appendChild(el("div", { class: "ks-ayar" }, slA.kok, el("div", { class: "ks-satir" }, sg.kok)));
    kap.appendChild(hizli);
    kap.appendChild(formul);
    kap.appendChild(formul2);
    kap.appendChild(el("p", { class: "ks-not" }, "Çubuğun ucunu sürükle (15°'ye yakınsa yapışır). Mavi: c², turuncu: cs, yeşil: s². Her 2×2 parsel aynı desenin işaretli tekrarıdır."));
    ciz();
  }, {
    baslik: "Kafes elemanı: açı ve 4x4 matris",
    aciklama: "Açıyı değiştirince c, s ve c², cs, s² desenindeki matris değerleri anında değişir.",
    varsayilan: { E: 200e6, A: 0.001, L: 5, aci: 30 }
  });

  function egriYol(f, n) { // f(t) → [x, y], t 0..1
    const pts = [];
    for (let i = 0; i <= n; i++) { const q = f(i / n); pts.push(r2(q[0]) + " " + r2(q[1])); }
    return "M" + pts.join(" L");
  }

  /* ================================================================== 4. dof-haritasi */

  E.kaydet("dof-haritasi", function (kok, p) {
    const kap = cerceveKur(kok);
    const gecerli = x => typeof x === "string" && !!HAZIR[x];
    let ozel = null, uyari = "";
    if (p.model && typeof p.model === "object") {
      try { ozel = modelHazirla(p.model); } catch (h) { uyari = "Verilen model okunamadı (" + (h && h.message ? h.message : h) + "); hazır örnek gösteriliyor."; }
    }
    let ad = ozel ? "ozel" : gecerli(p.model) ? p.model : gecerli(p.hazir) ? p.hazir : "kafes-iki-cubuk";
    if (!ozel && !uyari && p.model && typeof p.model === "string" && !gecerli(p.model)) uyari = "Bilinmeyen model adı: " + p.model + "; hazır örnek gösteriliyor.";
    let mdl = ozel || modelHazirla(HAZIR[ad]);
    let sec = -1, bolum = false, odak = null, ms = [];

    const W = 320, H = 250;
    const sd = sv(W, H, "Düğümler, serbestlik numaraları ve mesnetler");
    const sk = sv(340, 300, "Global rijitlik matrisi K ve eleman parseli");
    const chipler = el("div", { class: "ks-satir" });
    const durum = el("p", { class: "ks-bilgi" });
    const uyariKutu = el("p", { class: "ks-uyari" });
    const formul = formulKutu();
    const bilgi = el("p", { class: "ks-not" });

    function msBaslat() {
      ms = [];
      for (let q = 0; q < mdl.nd; q++) ms.push(Array.from({ length: mdl.d }, (_, c) => !!mdl.mesnet[q * mdl.d + c]));
    }
    function dongu(q) {
      const al = MESNET_ALAN[mdl.tip], pre = MESNET_DONGU[mdl.tip];
      const mevcut = pre.findIndex(pr => al.every((a, c) => (pr.indexOf(a) >= 0) === ms[q][c]));
      const yeni = pre[(mevcut + 1) % pre.length];
      ms[q] = al.map(a => yeni.indexOf(a) >= 0);
    }
    function chipleriKur() {
      bos(chipler);
      mdl.eleman.forEach((e, i) => {
        chipler.appendChild(el("button", { type: "button", class: "ks-chip", "aria-pressed": "false", onclick: () => elemanSec(i) }, "Eleman " + e.no));
      });
    }
    function elemanSec(i) { sec = sec === i ? -1 : i; ciz(); }

    function ciz() {
      const d = mdl.d, N = mdl.n;
      const sabit = Array.from({ length: N }, (_, i) => ms[Math.floor(i / d)][i % d]);
      const serbest = [], tutulu = [];
      for (let i = 0; i < N; i++) (sabit[i] ? tutulu : serbest).push(i);
      const nf = serbest.length, ns = tutulu.length;
      const perm = bolum ? serbest.concat(tutulu) : Array.from({ length: N }, (_, i) => i);
      const e = sec >= 0 ? mdl.eleman[sec] : null;
      const esKume = e ? new Set(e.dof) : null;
      Array.prototype.forEach.call(chipler.children, (c, i) => c.setAttribute("aria-pressed", String(i === sec)));

      /* ---- model çizimi ---- */
      bos(sd);
      let minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
      mdl.dugum.forEach(q => { minx = Math.min(minx, q.x); maxx = Math.max(maxx, q.x); miny = Math.min(miny, q.y); maxy = Math.max(maxy, q.y); });
      const bw = Math.max(maxx - minx, 1e-9), bh = maxy - miny, M = 44;
      let sc = (W - 2 * M) / bw;
      if (bh > 1e-9) sc = Math.min(sc, (H - 2 * M - 24) / bh);
      sc = Math.min(sc, 90);
      const px = x => (W - bw * sc) / 2 + (x - minx) * sc;
      const py = y => H / 2 - 8 + bh * sc / 2 - (y - miny) * sc;
      const sagTik = [], elTik = [];
      mdl.eleman.forEach((el_, i) => {
        const a = mdl.dugum[el_.a], b = mdl.dugum[el_.b];
        const secili = i === sec, aile = aileOf(i);
        sd.appendChild(cizgi(px(a.x), py(a.y), px(b.x), py(b.y), { renk: secili ? aile : "metin", kal: secili ? 5.5 : 3, opak: sec >= 0 && !secili ? 0.5 : 1 }));
        const mx = (px(a.x) + px(b.x)) / 2, my = (py(a.y) + py(b.y)) / 2;
        let nx = -(py(b.y) - py(a.y)), ny = px(b.x) - px(a.x);
        const nl = Math.hypot(nx, ny) || 1; nx /= nl; ny /= nl;
        if (ny > 0) { nx = -nx; ny = -ny; }
        sd.appendChild(yaziH(mx + nx * 12, my + ny * 12, "e" + el_.no, { renk: secili ? aile : "soluk", boyut: 11, kalin: true }));
        elTik.push(svg("line", {
          x1: r2(px(a.x)), y1: r2(py(a.y)), x2: r2(px(b.x)), y2: r2(py(b.y)), stroke: "transparent", "stroke-width": 22, "stroke-linecap": "round",
          class: "ks-tik", tabindex: 0, role: "button", "aria-label": "Eleman " + el_.no + " parselini göster", dataset: { id: "e" + i },
          onclick: () => { odak = "e" + i; elemanSec(i); },
          onkeydown: ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); odak = "e" + i; elemanSec(i); } }
        }));
      });
      mdl.dugum.forEach((q, qi) => {
        const x = px(q.x), y = py(q.y), m = ms[qi];
        const al = MESNET_ALAN[mdl.tip];
        const ux = al.indexOf("ux") >= 0 && m[al.indexOf("ux")], uy = al.indexOf("uy") >= 0 && m[al.indexOf("uy")], rz = al.indexOf("rz") >= 0 && m[al.indexOf("rz")];
        if (ux || uy || rz) sd.appendChild(mesnetSimge(x, y, ux, uy, rz, "sil"));
        sd.appendChild(daire(x, y, 5.5, { dolgu: "ana", dolguHam: renk("metin"), renk: "metin", kal: 1 }));
        // serbestlik etiketleri
        const sag = x > W * 0.6, x0 = sag ? x - 9 - d * 19 + 2 : x + 9;
        for (let c = 0; c < d; c++) {
          const no = qi * d + c, cx = x0 + c * 19 + 8.5, cy = y - 18;
          sd.appendChild(dikdortgen(cx - 8.5, cy - 7, 17, 14, { rx: 4, dolgu: "kart", dolguHam: "var(--kart,#fff)", renk: sabit[no] ? "sil" : "soluk", kal: 1.2 }));
          sd.appendChild(yazi(cx, cy, String(no + 1), { boyut: 9.5, kalin: true, renk: sabit[no] ? "sil" : "metin" }));
        }
        sagTik.push(svg("circle", {
          cx: r2(x), cy: r2(y), r: 17, fill: "transparent", class: "ks-tik", tabindex: 0, role: "button",
          "aria-label": "Düğüm " + q.no + " mesnet türünü değiştir", dataset: { id: "n" + qi },
          onclick: () => { dongu(qi); odak = "n" + qi; ciz(); },
          onkeydown: ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); dongu(qi); odak = "n" + qi; ciz(); } }
        }));
      });
      elTik.forEach(t => sd.appendChild(t));
      sagTik.forEach(t => sd.appendChild(t));

      /* ---- K matrisi ---- */
      const kMax = enBuyuk(mdl.K) || 1;
      const w = N <= 4 ? 54 : N <= 6 ? 44 : N <= 8 ? 36 : N <= 10 ? 30 : N <= 12 ? 24 : 18;
      const hh = N <= 4 ? 34 : N <= 6 ? 30 : N <= 8 ? 26 : N <= 10 ? 22 : N <= 12 ? 20 : 18;
      const goster = N <= 8;
      const deger = (i, j) => mdl.K[perm[i]][perm[j]];
      const T = tablo(N, N, {
        x: 30, y: 22, w, h: hh, boyut: N <= 6 ? 11 : 9,
        metin: (i, j) => goster ? kisa(deger(i, j)) : "",
        aile: (i, j) => {
          const iN = perm[i], jN = perm[j], dolu = Math.abs(deger(i, j)) > 1e-9 * kMax;
          if (e) return esKume.has(iN) && esKume.has(jN) ? aileOf(sec) : (dolu ? "cizgi" : null);
          if (!dolu) return null;
          return sabit[iN] || sabit[jN] ? "sil" : "cizgi";
        },
        soluk: (i, j) => {
          const iN = perm[i], jN = perm[j];
          if (e) return !(esKume.has(iN) && esKume.has(jN));
          return Math.abs(deger(i, j)) <= 1e-9 * kMax;
        },
        ust: perm.map(i => String(i + 1)), sol: perm.map(i => String(i + 1))
      });
      bos(sk);
      sk.appendChild(T.g);
      if (bolum && nf > 0 && ns > 0) {
        T.kutu(0, 0, nf - 1, nf - 1, "a", { kal: 2.8 });
        T.kutu(0, nf, nf - 1, N - 1, "b", { kal: 2.4 });
        T.kutu(nf, 0, N - 1, nf - 1, "b", { kal: 2.4 });
        T.kutu(nf, nf, N - 1, N - 1, "sil", { kal: 2.4, kesik: true });
      }
      svBoyut(sk, 30 + T.genislik + 10, 22 + T.yukseklik + 10);

      /* ---- açıklamalar ---- */
      let rk = 0;
      if (nf > 0) rk = mertebe(serbest.map(i => serbest.map(j => mdl.K[i][j])), 1e-9);
      let msg, sinif;
      if (nf === 0) { msg = "Bütün serbestlikler tutulu: çözülecek bilinmeyen kalmadı."; sinif = "ks-bilgi"; }
      else if (rk < nf) {
        msg = "Mekanizma uyarısı: Kff'nin mertebesi " + rk + ", serbestlik sayısı " + nf + ". " + (nf - rk) + " hareket mesnetle engellenmemiş; Kff tekil, çözüm yok.";
        sinif = "ks-uyari";
      } else { msg = "Mesnetler yeterli: Kff " + nf + "×" + nf + " ve tekil değil (mertebe " + rk + "). Sistem çözülebilir."; sinif = "ks-tamam"; }
      durum.className = sinif;
      durum.textContent = msg;
      let tx;
      if (bolum && nf > 0 && ns > 0) {
        tx = "\\begin{bmatrix}\\kutua{K_{ff}}&\\kutub{K_{fs}}\\\\ \\kutub{K_{sf}}&\\kutusil{K_{ss}}\\end{bmatrix}\\begin{bmatrix}u_f\\\\ 0\\end{bmatrix}=\\begin{bmatrix}F_f\\\\ R_s\\end{bmatrix}\\ \\Rightarrow\\ \\kutua{K_{ff}}\\,u_f=F_f,\\quad n_f=" + nf + ",\\ n_s=" + ns;
      } else {
        tx = "\\mathbf K\\,\\mathbf u=\\mathbf F,\\qquad n=" + N + ",\\ n_s=" + ns + "\\ \\text{(tutulu)}";
      }
      if (e) {
        tx = "\\" + MAKRO3[sec % 3] + "{\\mathbf k_{" + e.no + "}}\\ \\text{eleman " + e.no + " (düğüm " + mdl.dugum[e.a].no + "→" + mdl.dugum[e.b].no + ")}:\\ \\text{serbestlik }[" + e.dof.map(x => x + 1).join(",") + "]\\ \\Rightarrow\\ \\mathbf K\\mathrel{+}=\\mathbf k_{" + e.no + "}\\quad\\text{(" + e.dof.length + "×" + e.dof.length + " parsel)}";
      }
      texYaz(formul, tx);
      const adlar = { yay: "u", cubuk: "u", kafes: "u, v", kiris: "v, θ", cerceve: "u, v, θ" }[mdl.tip];
      bilgi.textContent = "Düğüm başına serbestlik: " + adlar + ". Bir düğüme dokun: mesnet türü değişir (kırmızı etiket = tutulu). Bir elemana dokun: K'daki " + (2 * d) + "×" + (2 * d) + " parseli yanar.";
      if (odak) {
        const x = sd.querySelector('[data-id="' + odak + '"]');
        odak = null;
        if (x) x.focus({ preventScroll: true });
      }
    }

    function modelDegistir(yeni, adi) {
      ad = adi; mdl = yeni; sec = -1; msBaslat(); chipleriKur(); ciz();
    }
    const secenekler = HAZIR_SIRA.map(h => ({ deger: h[0], etiket: h[1] }));
    if (ozel) secenekler.unshift({ deger: "ozel", etiket: "Verilen model" });
    const sModel = secici(secenekler, ad, v => {
      try { modelDegistir(v === "ozel" ? ozel : modelHazirla(HAZIR[v]), v); } catch (h) { uyariKutu.textContent = String(h && h.message || h); }
    });
    const sBolum = secici([{ deger: "dogal", etiket: "Doğal sıra" }, { deger: "bolum", etiket: "Kff · Kfs bölümleri" }], "dogal", v => { bolum = v === "bolum"; ciz(); });

    if (uyari) { uyariKutu.textContent = uyari; kap.appendChild(uyariKutu); }
    kap.appendChild(el("div", { class: "ks-satir" }, sModel.kok));
    kap.appendChild(el("div", { class: "ks-iki" }, kart(sd), kart(sk)));
    kap.appendChild(chipler);
    kap.appendChild(dugmeSatiri(sBolum.kok, dugme("Mesnetleri sıfırla", () => { msBaslat(); ciz(); }, { baslik: "Modelin ilk mesnetlerine dön" })));
    kap.appendChild(durum);
    kap.appendChild(formul);
    kap.appendChild(bilgi);
    msBaslat();
    chipleriKur();
    ciz();
  }, {
    baslik: "Serbestlik numaraları ve K'nın parselleri",
    aciklama: "Düğümlerin serbestlik numaralarını, elemanın K içindeki yerini ve mesnetlerin Kff / Kfs bölümlerini göster.",
    varsayilan: { hazir: "kafes-iki-cubuk" }
  });

  /* ================================================================== 5. kiris-sekil */

  E.kaydet("kiris-sekil", function (kok, p) {
    const kap = cerceveKur(kok);
    const L = sayiP(p.L, 4, 0.1, 100);
    let d = [0, 12, 18, -6]; // v1 (mm), t1 (mrad), v2 (mm), t2 (mrad)
    let xi = 0.5, bilesen = true;
    const W = 440, H = 300, X0 = 50, LP = 340, Yb = 84, Dref = 30, s = 60 / Dref, Y0n = 252, bn = 70;
    const sd = sv(W, H, "Kiriş elemanı: Hermite şekil fonksiyonları ve elastik eğri");
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const h1 = tutamak("a", "Sol düğümün düşey yer değiştirmesi v1"), h2 = tutamak("c", "Sağ düğümün düşey yer değiştirmesi v2");
    tut.appendChild(h1); tut.appendChild(h2);
    const formul = formulKutu();
    const AIL = ["a", "b", "c", "sil"];
    const MK = ["\\ka", "\\kb", "\\kc", "\\ksil"];
    const sls = [
      sl("$v_1$", -30, 30, 0.5, d[0], "mm", v => { d[0] = v; ciz(); }),
      sl("$\\theta_1$", -20, 20, 0.5, d[1], "mrad", v => { d[1] = v; ciz(); }),
      sl("$v_2$", -30, 30, 0.5, d[2], "mm", v => { d[2] = v; ciz(); }),
      sl("$\\theta_2$", -20, 20, 0.5, d[3], "mrad", v => { d[3] = v; ciz(); })
    ];
    const slX = sl("$\\xi=x/L$", 0, 1, 0.01, xi, "", v => { xi = v; ciz(); }, v => kat(v, 2));
    const Nf = t => { const n = hermite(t, L); return [n[0], n[1], n[2], n[3]]; };
    const uMm = t => { const n = Nf(t); return n[0] * d[0] + n[1] * d[1] + n[2] * d[2] + n[3] * d[3]; };
    const yPx = u => Yb - kenet(s * u, -85, 85);

    function ciz() {
      bos(dyn);
      // eksen ve mesnet cizgileri
      dyn.appendChild(cizgi(X0, Yb, X0 + LP, Yb, { renk: "soluk", kal: 1.2, kesik: true }));
      if (bilesen) {
        for (let q = 0; q < 4; q++) {
          dyn.appendChild(yol(egriYol(t => [X0 + t * LP, yPx(Nf(t)[q] * d[q])], 50), { renk: AIL[q], kal: 1.6, kesik: true, opak: 0.85 }));
        }
      }
      dyn.appendChild(yol(egriYol(t => [X0 + t * LP, yPx(uMm(t))], 80), { renk: "metin", kal: 3.6 }));
      // teğetler
      [[0, 1], [1, 3]].forEach(c => {
        const x = X0 + c[0] * LP, y = yPx(c[0] ? d[2] : d[0]), egim = -s * d[c[1]] * L / LP, dx = 28;
        dyn.appendChild(cizgi(x - dx, y - egim * dx, x + dx, y + egim * dx, { renk: c[0] ? "sil" : "b", kal: 2.2 }));
      });
      dyn.appendChild(yaziH(X0 - 8, Yb - 4, "v", { renk: "soluk", boyut: 11, hiza: "sag" }));
      // ξ işareti
      const xc = X0 + xi * LP, yc = yPx(uMm(xi));
      dyn.appendChild(cizgi(xc, 28, xc, Y0n + 20, { renk: "soluk", kal: 1, kesik: true }));
      dyn.appendChild(daire(xc, yc, 5, { dolgu: "ana", dolguHam: renk("metin"), renk: "kart", kal: 1.5 }));
      // N grafiği
      dyn.appendChild(cizgi(X0, Y0n, X0 + LP, Y0n, { renk: "soluk", kal: 1.2 }));
      dyn.appendChild(cizgi(X0, Y0n - bn, X0 + LP, Y0n - bn, { renk: "kenar", kal: 1, kesik: true }));
      dyn.appendChild(yazi(X0 - 8, Y0n - bn, "1", { hiza: "sag", boyut: 11, renk: "soluk" }));
      dyn.appendChild(yazi(X0 - 8, Y0n, "0", { hiza: "sag", boyut: 11, renk: "soluk" }));
      const ad = ["N1", "N2/L", "N3", "N4/L"];
      for (let q = 0; q < 4; q++) {
        const f = t => { const n = Nf(t)[q]; return Y0n - bn * (q % 2 ? n / L : n); };
        dyn.appendChild(yol(egriYol(t => [X0 + t * LP, f(t)], 50), { renk: AIL[q], kal: 2.8 }));
        const n = Nf(xi)[q] / (q % 2 ? L : 1);
        dyn.appendChild(daire(xc, Y0n - bn * n, 4.5, { dolgu: AIL[q], dolguHam: renk(AIL[q]) }));
      }
      [[0.04, 0, 1], [0.28, 1, -1], [0.96, 2, -1], [0.72, 3, 1]].forEach(c => {
        const n = Nf(c[0])[c[1]] / (c[1] % 2 ? L : 1);
        dyn.appendChild(yaziH(X0 + c[0] * LP + (c[2] > 0 ? 6 : -6), Y0n - bn * n - 11, ad[c[1]], { renk: AIL[c[1]], boyut: 11, kalin: true, hiza: c[2] > 0 ? "sol" : "sag" }));
      });
      dyn.appendChild(yazi(X0, Y0n + 16, "ξ = 0", { boyut: 11, renk: "soluk" }));
      dyn.appendChild(yazi(X0 + LP, Y0n + 16, "ξ = 1", { boyut: 11, renk: "soluk" }));
      tutKonum(h1, X0, yPx(d[0])); tutKonum(h2, X0 + LP, yPx(d[2]));

      const n = Nf(xi), u = uMm(xi);
      const tr = q => "\\" + MK[q].slice(1) + "{" + kat(n[q], 3) + "\\cdot(" + kisa([d[0], d[1], d[2], d[3]][q]) + ")}";
      texYaz(formul, "\\begin{aligned}v(\\xi)&=\\ka{N_1}v_1+\\kb{N_2}\\theta_1+\\kc{N_3}v_2+\\ksil{N_4}\\theta_2\\\\" +
        "&=" + tr(0) + "+" + tr(1) + "+" + tr(2) + "+" + tr(3) + "=" + kisa(u) + "\\ \\text{mm}\\end{aligned}");
    }
    function ayar(i, v) { d[i] = v; sls[i].ayarla(v, true); ciz(); }
    surukle(h1, { svg: sd, tasi: q => ayar(0, kenet(Math.round((Yb - q.y) / s * 2) / 2, -30, 30)), klavye: (dx, dy) => ayar(0, kenet(d[0] - dy, -30, 30)) });
    surukle(h2, { svg: sd, tasi: q => ayar(2, kenet(Math.round((Yb - q.y) / s * 2) / 2, -30, 30)), klavye: (dx, dy) => ayar(2, kenet(d[2] - dy, -30, 30)) });

    function tek(i) {
      d = [0, 0, 0, 0];
      d[i] = i % 2 ? 15 : 20;
      sls.forEach((x, k) => x.ayarla(d[k], true));
      ciz();
    }
    const sBil = secici([{ deger: "ac", etiket: "Bileşenler açık" }, { deger: "kapa", etiket: "Kapalı" }], "ac", v => { bilesen = v === "ac"; ciz(); });
    kap.appendChild(kart(sd));
    kap.appendChild(dugmeSatiri(
      dugme("Yalnız v₁", () => tek(0), { baslik: "v1 = 20 mm, diğerleri 0: N1 şekli" }),
      dugme("Yalnız θ₁", () => tek(1), { baslik: "θ1 = 15 mrad: N2 şekli" }),
      dugme("Yalnız v₂", () => tek(2), { baslik: "v2 = 20 mm: N3 şekli" }),
      dugme("Yalnız θ₂", () => tek(3), { baslik: "θ2 = 15 mrad: N4 şekli" }),
      dugme("Sıfırla", () => { d = [0, 12, 18, -6]; sls.forEach((x, k) => x.ayarla(d[k], true)); ciz(); })));
    kap.appendChild(el("div", { class: "ks-ayar" }, sls[0].kok, sls[1].kok, sls[2].kok, sls[3].kok, slX.kok));
    kap.appendChild(el("div", { class: "ks-satir" }, sBil.kok));
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ks-not" }, "L = " + kisa(L) + " m. Düğüm noktalarını yukarı-aşağı sürükle (v₁, v₂). Kesikli renkli eğriler her serbestliğin katkısıdır: " +
      "mavi N₁v₁, turuncu N₂θ₁, yeşil N₃v₂, kırmızı N₄θ₂. Eğri bunların toplamıdır. Düşey ölçek abartılıdır; çizgiler düğümlerdeki dönmeyi (teğet) gösterir."));
    ciz();
  }, {
    baslik: "Kiriş elemanı: Hermite şekil fonksiyonları",
    aciklama: "v1, θ1, v2, θ2 ile elastik eğriyi kur; her serbestliğin N1-N4 katkısını gör.",
    varsayilan: { L: 4 }
  });

  function detNum(A) {
    const n = A.length, M = A.map(r => r.slice());
    let d = 1;
    for (let k = 0; k < n; k++) {
      let q = k;
      for (let i = k + 1; i < n; i++) if (Math.abs(M[i][k]) > Math.abs(M[q][k])) q = i;
      if (M[q][k] === 0) return 0;
      if (q !== k) { const t = M[q]; M[q] = M[k]; M[k] = t; d = -d; }
      d *= M[k][k];
      for (let i = k + 1; i < n; i++) {
        const c = M[i][k] / M[k][k];
        for (let j = k; j < n; j++) M[i][j] -= c * M[k][j];
      }
    }
    return d;
  }
  function temizle(A, goreli) { // gürültü düzeyindeki değerleri sıfırlar
    const tol = (goreli || 1e-9) * (enBuyuk(A) || 1);
    return A.map(r => r.map(x => (Math.abs(x) <= tol ? 0 : x)));
  }
  const SAG = (x, xa) => x > xa ? "sol" : "sag";

  /* ================================================================== 6. esdeger-yuk */

  E.kaydet("esdeger-yuk", function (kok, p) {
    const kap = cerceveKur(kok);
    let L = sayiP(p.L, 4, 0.5, 50), q = sayiP(p.q, 10, 0, 1e4), P = sayiP(p.P, 20, 0, 1e5);
    let xa = kenet(sayiP(p.a, L * 0.4, 0, L) / L, 0, 1);
    const W = 440, H = 276, X0 = 50, LP = 340, Y1 = 90, Y2 = 212;
    const sd = sv(W, H, "Yayılı ve tekil yükün eşdeğer düğüm kuvvetleri");
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const hp = tutamak("b", "Tekil yükün konumu a");
    tut.appendChild(hp);
    const formul = formulKutu();

    function kirisCiz(y) {
      dyn.appendChild(cizgi(X0, y, X0 + LP, y, { renk: "metin", kal: 5 }));
      [0, 1].forEach(k => {
        dyn.appendChild(daire(X0 + k * LP, y, 5, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 1.8 }));
        dyn.appendChild(yaziH(X0 + k * LP, y + 19, String(k + 1), { boyut: 11, kalin: true, renk: "soluk" }));
      });
    }
    function ciz() {
      bos(dyn);
      const a = xa * L, xp = X0 + xa * LP;
      const n = hermite(xa, L);
      const fq = [-q * L / 2, -q * L * L / 12, -q * L / 2, q * L * L / 12];
      const fP = n.map(x => -P * x);
      const f = fq.map((x, i) => x + fP[i]);

      /* gerçek yükleme */
      kirisCiz(Y1);
      if (q > 0) {
        dyn.appendChild(cizgi(X0, Y1 - 36, X0 + LP, Y1 - 36, { renk: "a", kal: 2 }));
        for (let i = 0; i <= 10; i++) dyn.appendChild(ok(X0 + LP * i / 10, Y1 - 36, X0 + LP * i / 10, Y1 - 6, { renk: "a", kalinlik: 1.5, bas: 6 }));
        dyn.appendChild(yaziH(X0 + LP / 2, Y1 - 46, "q = " + kisa(q) + " kN/m", { renk: "a", boyut: 11, kalin: true }));
      }
      if (P > 0) {
        dyn.appendChild(ok(xp, Y1 - 62, xp, Y1 - 6, { renk: "b", kalinlik: 3, bas: 10 }));
        dyn.appendChild(yaziH(xp + (xa > 0.7 ? -12 : 12), Y1 - 44, "P = " + kisa(P) + " kN", { renk: "b", boyut: 11, kalin: true, hiza: xa > 0.7 ? "sag" : "sol" }));
      }
      dyn.appendChild(cizgi(X0, Y1 + 34, xp, Y1 + 34, { renk: "b", kal: 1.2 }));
      dyn.appendChild(cizgi(X0, Y1 + 29, X0, Y1 + 39, { renk: "b", kal: 1.2 }));
      dyn.appendChild(cizgi(xp, Y1 + 29, xp, Y1 + 39, { renk: "b", kal: 1.2 }));
      dyn.appendChild(yaziH((X0 + xp) / 2 + (xa < 0.12 ? 22 : 0), Y1 + 46, "a = " + kisa(a) + " m", { renk: "b", boyut: 11 }));
      dyn.appendChild(yazi(X0 + LP, Y1 + 46, "L = " + kisa(L) + " m", { renk: "soluk", boyut: 11, hiza: "sag" }));

      /* eşdeğer düğüm yükleri */
      dyn.appendChild(cizgi(X0 - 24, 128, X0 + LP + 24, 128, { renk: "kenar", kal: 1, kesik: true }));
      dyn.appendChild(yazi(X0 - 24, 119, "Eşdeğer düğüm yükleri", { renk: "soluk", boyut: 11, hiza: "sol", kalin: true }));
      kirisCiz(Y2);
      const sc = (q * L + P) || 1;
      [0, 2].forEach(k => {
        const F = f[k], x = X0 + (k ? LP : 0);
        if (Math.abs(F) < 1e-9 * sc) return;
        const len = 18 + 40 * Math.min(1.2, Math.abs(F) / sc);
        const yu = F < 0 ? Y2 - 6 - len : Y2 + 6 + len;
        dyn.appendChild(ok(x, yu, x, F < 0 ? Y2 - 6 : Y2 + 6, { renk: "c", kalinlik: 2.8, bas: 9 }));
        dyn.appendChild(yaziH(x + (k ? -9 : 9), yu + (F < 0 ? 4 : -4), "F" + (k ? 2 : 1) + " = " + kisa(F), { renk: "c", boyut: 11, kalin: true, hiza: k ? "sag" : "sol" }));
      });
      [1, 3].forEach(k => {
        const Mm = f[k], x = X0 + (k === 3 ? LP : 0);
        if (Math.abs(Mm) < 1e-9 * sc * L) return;
        dyn.appendChild(momentOku(x, Y2, 17, Mm > 0, "sil", 2.4));
        dyn.appendChild(yaziH(x + (k === 3 ? -22 : 22), Y2 - 22, "M" + (k === 3 ? 2 : 1) + " = " + kisa(Mm), { renk: "sil", boyut: 11, kalin: true, hiza: k === 3 ? "sag" : "sol" }));
      });
      tutKonum(hp, xp, Y1 - 70);

      const kol = arr => "\\begin{bmatrix}" + arr.map(x => kisa(x)).join("\\\\") + "\\end{bmatrix}";
      texYaz(formul, "\\begin{aligned}\\mathbf f&=\\ka{\\mathbf f_q}+\\kb{\\mathbf f_P}=\\ka{" + kol(fq) + "}+\\kb{" + kol(fP) + "}=\\kc{" + kol(f) + "}\\\\" +
        "\\ka{\\mathbf f_q}&=\\left[-\\tfrac{qL}{2},\\,-\\tfrac{qL^2}{12},\\,-\\tfrac{qL}{2},\\,+\\tfrac{qL^2}{12}\\right]^T,\\qquad \\kb{\\mathbf f_P}=-P\\,[N_1,N_2,N_3,N_4]^T_{\\xi=" + kat(xa, 2) + "}\\\\" +
        "F_1+F_2&=" + kisa(f[0] + f[2]) + "\\ \\text{kN}=-(qL+P)\\qquad(\\text{kN},\\ \\text{kN}\\!\\cdot\\!\\text{m})\\end{aligned}");
    }
    const slQ = sl("$q$", 0, guzel(Math.max(q * 2, 50)), 0.5, q, "kN/m", v => { q = v; ciz(); });
    const slP = sl("$P$", 0, guzel(Math.max(P * 2, 100)), 1, P, "kN", v => { P = v; ciz(); });
    const slA = sl("$a/L$", 0, 1, 0.01, xa, "", v => { xa = v; ciz(); }, v => kat(v, 2));
    const slL = sl("$L$", 0.5, Math.max(12, Math.ceil(L * 2)), 0.1, L, "m", v => { L = v; ciz(); });
    function ayarA(v) { xa = kenet(Math.round(v * 100) / 100, 0, 1); slA.ayarla(xa, true); ciz(); }
    surukle(hp, { svg: sd, tasi: pt => ayarA((pt.x - X0) / LP), klavye: dx => ayarA(xa + dx / 100) });

    kap.appendChild(kart(sd));
    kap.appendChild(el("div", { class: "ks-ayar" }, slQ.kok, slP.kok, slA.kok, slL.kok));
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ks-not" }, "Turuncu P okunun üstündeki yuvarlağı sürükle: yükün konumu a değişir ve yük iki düğüme N₁…N₄ ağırlıklarıyla dağılır. " +
      "Yük bir düğüme yaklaştıkça o düğümün payı büyür. Bunlar ankastre uç tepkilerinin işaret değiştirmişidir."));
    ciz();
  }, {
    baslik: "Eşdeğer düğüm yükleri",
    aciklama: "Eleman içindeki yayılı ve tekil yükü iki düğümün kuvvet ve momentlerine çevir.",
    varsayilan: { q: 10, L: 4, P: 20, a: 1.5 }
  });

  /* ================================================================== 7. kiris-nvm */

  E.kaydet("kiris-nvm", function (kok, p) {
    const kap = cerceveKur(kok);
    let L = sayiP(p.L, 6, 0.5, 100), q = sayiP(p.q, 12, 0, 1e4), P = sayiP(p.P, 0, 0, 1e5);
    let xa = kenet(sayiP(p.a, L / 2, 0, L) / L, 0, 1), xc = 0.5;
    let tip = ["basit", "konsol", "ankastre-mafsalli"].indexOf(p.mesnet) >= 0 ? p.mesnet : "basit";
    const W = 440, H = 352, X0 = 50, LP = 340, Yb = 88, Yv = 186, Ym = 290, AMP = 40;
    const sd = sv(W, H, "Kiriş yükü, kesme kuvveti ve eğilme momenti diyagramları");
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const hp = tutamak("b", "Tekil yükün konumu a");
    tut.appendChild(hp);
    const formul = formulKutu();
    const px = x => X0 + x / L * LP;

    function tepki() {
      const a = xa * L;
      let RB = 0, MA = 0;
      if (tip === "basit") RB = (q * L * L / 2 + P * a) / L;
      else if (tip === "ankastre-mafsalli") RB = 3 * q * L / 8 + P * a * a * (3 * L - a) / (2 * L * L * L);
      const RA = q * L + P - RB;
      if (tip !== "basit") MA = q * L * L / 2 + P * a - RB * L;
      return { RA, RB, MA, a };
    }
    const Vf = (x, sonra, r) => r.RA - q * x - (sonra ? P : 0);
    const Mf = (x, r) => -r.MA + r.RA * x - q * x * x / 2 - (x > r.a ? P * (x - r.a) : 0);

    function ciz() {
      bos(dyn);
      const r = tepki(), a = r.a, xp = px(a);
      // örnekleme
      const N = 160, nok = [];
      let eklendi = false;
      for (let i = 0; i <= N; i++) {
        const x = L * i / N;
        if (!eklendi && x >= a) { nok.push({ x: a, s: false }); nok.push({ x: a, s: true }); eklendi = true; if (x === a) continue; }
        nok.push({ x, s: x > a });
      }
      let vMax = -Infinity, vMin = Infinity, xvMax = 0, xvMin = 0, mMax = -Infinity, mMin = Infinity, xmMax = 0, xmMin = 0;
      nok.concat(Array.from({ length: 401 }, (_, i) => ({ x: L * i / 400, s: L * i / 400 > a }))).forEach(o => {
        const v = Vf(o.x, o.s, r), m = Mf(o.x, r);
        if (v > vMax) { vMax = v; xvMax = o.x; }
        if (v < vMin) { vMin = v; xvMin = o.x; }
        if (m > mMax) { mMax = m; xmMax = o.x; }
        if (m < mMin) { mMin = m; xmMin = o.x; }
      });
      const vAbs = Math.max(Math.abs(vMax), Math.abs(vMin)), mAbs = Math.max(Math.abs(mMax), Math.abs(mMin));
      const vs = vAbs > 1e-9 ? AMP / vAbs : 0, ms_ = mAbs > 1e-9 ? AMP / mAbs : 0;

      // kiriş, mesnetler, yükler
      dyn.appendChild(cizgi(X0, Yb, X0 + LP, Yb, { renk: "metin", kal: 5 }));
      if (tip === "basit") {
        dyn.appendChild(mesnetSimge(X0, Yb, true, true, false, "metin"));
        dyn.appendChild(mesnetSimge(X0 + LP, Yb, false, true, false, "metin"));
      } else {
        dyn.appendChild(duvarCiz(X0, Yb - 24, Yb + 24));
        if (tip === "ankastre-mafsalli") dyn.appendChild(mesnetSimge(X0 + LP, Yb, false, true, false, "metin"));
      }
      if (q > 0) {
        dyn.appendChild(cizgi(X0, Yb - 30, X0 + LP, Yb - 30, { renk: "a", kal: 2 }));
        for (let i = 0; i <= 10; i++) dyn.appendChild(ok(X0 + LP * i / 10, Yb - 30, X0 + LP * i / 10, Yb - 6, { renk: "a", kalinlik: 1.4, bas: 5 }));
        dyn.appendChild(yaziH(X0 + LP / 2, Yb - 40, "q = " + kisa(q) + " kN/m", { renk: "a", boyut: 11, kalin: true }));
      }
      if (P > 0) {
        dyn.appendChild(ok(xp, Yb - 56, xp, Yb - 6, { renk: "b", kalinlik: 3, bas: 10 }));
        dyn.appendChild(yaziH(xp + (xa > 0.7 ? -12 : 12), Yb - 44, "P = " + kisa(P) + " kN", { renk: "b", boyut: 11, kalin: true, hiza: xa > 0.7 ? "sag" : "sol" }));
      }
      tutKonum(hp, xp, Yb - 62);

      // V diyagramı
      dyn.appendChild(yazi(X0 - 8, Yv - AMP - 8, "V [kN]", { renk: "soluk", boyut: 11, hiza: "sol", kalin: true }));
      dyn.appendChild(cizgi(X0, Yv, X0 + LP, Yv, { renk: "soluk", kal: 1.2 }));
      const vYol = "M" + X0 + " " + Yv + " L" + nok.map(o => r2(px(o.x)) + " " + r2(Yv - vs * Vf(o.x, o.s, r))).join(" L") + " L" + (X0 + LP) + " " + Yv + " Z";
      dyn.appendChild(yol(vYol, { dolgu: "a", renk: "a", kal: 1.8 }));
      // M diyagramı (çekilen lif tarafı: sehim yönü aşağı)
      dyn.appendChild(yazi(X0 - 8, Ym - AMP - 8, "M [kN·m]  (çekilen lif tarafına çizili)", { renk: "soluk", boyut: 11, hiza: "sol", kalin: true }));
      dyn.appendChild(cizgi(X0, Ym, X0 + LP, Ym, { renk: "soluk", kal: 1.2 }));
      const mn = [];
      for (let i = 0; i <= 200; i++) { const x = L * i / 200; mn.push(r2(px(x)) + " " + r2(Ym + ms_ * Mf(x, r))); }
      dyn.appendChild(yol("M" + X0 + " " + Ym + " L" + mn.join(" L") + " L" + (X0 + LP) + " " + Ym + " Z", { dolgu: "b", renk: "b", kal: 1.8 }));

      // uç değerler
      function isaret(x, y, metin, yon, aile) {
        dyn.appendChild(daire(px(x), y, 3.6, { dolgu: aile, dolguHam: renk(aile) }));
        const hz = x / L > 0.78 ? "sag" : x / L < 0.22 ? "sol" : undefined;
        dyn.appendChild(yaziH(px(x) + (hz === "sag" ? -6 : hz === "sol" ? 6 : 0), y + yon * 13, metin, { renk: aile, boyut: 10.5, kalin: true, hiza: hz }));
      }
      if (vAbs > 1e-9) {
        const vb = Math.abs(vMax) >= Math.abs(vMin) ? [xvMax, vMax] : [xvMin, vMin];
        isaret(vb[0], Yv - vs * vb[1], "V=" + kisa(vb[1]), vb[1] >= 0 ? -1 : 1, "a");
      }
      if (mMax > 1e-9) isaret(xmMax, Ym + ms_ * mMax, "M=" + kisa(mMax), 1, "b");
      if (mMin < -1e-9) isaret(xmMin, Ym + ms_ * mMin, "M=" + kisa(mMin), -1, "b");

      // imleç
      const xcm = xc * L, sc_ = xcm > a;
      dyn.appendChild(cizgi(px(xcm), Yb + 24, px(xcm), Ym + AMP + 6, { renk: "soluk", kal: 1, kesik: true }));
      dyn.appendChild(daire(px(xcm), Yv - vs * Vf(xcm, sc_, r), 4.5, { dolgu: "ana", dolguHam: renk("metin"), renk: "kart", kal: 1.4 }));
      dyn.appendChild(daire(px(xcm), Ym + ms_ * Mf(xcm, r), 4.5, { dolgu: "ana", dolguHam: renk("metin"), renk: "kart", kal: 1.4 }));
      dyn.appendChild(yazi(X0, Ym + AMP + 22, "x = 0", { renk: "soluk", boyut: 11 }));
      dyn.appendChild(yazi(X0 + LP, Ym + AMP + 22, "x = " + kisa(L) + " m", { renk: "soluk", boyut: 11, hiza: "sag" }));

      const bn = "\\ \\text{kN}", bm = "\\ \\text{kN}\\!\\cdot\\!\\text{m}";
      texYaz(formul, "\\begin{aligned}R_A&=" + kisa(r.RA) + bn + (tip !== "basit" ? ",\\quad M_A=" + kisa(r.MA) + bm : "") + (tip !== "konsol" ? ",\\quad R_B=" + kisa(r.RB) + bn : "") + "\\\\" +
        "|V|_{\\max}&=" + kisa(vAbs) + bn + ",\\quad M_{\\max}=" + kisa(mMax > 1e-9 ? mMax : 0) + bm + (mMin < -1e-9 ? ",\\quad M_{\\min}=" + kisa(mMin) + bm : "") + "\\\\" +
        "x&=" + kat(xcm, 2) + "\\ \\text{m}:\\quad V=" + kisa(Vf(xcm, sc_, r)) + bn + ",\\quad M=" + kisa(Mf(xcm, r)) + bm + "\\end{aligned}");
    }
    const sTip = secici([{ deger: "basit", etiket: "Basit" }, { deger: "konsol", etiket: "Konsol" }, { deger: "ankastre-mafsalli", etiket: "Ankastre-mafsallı" }], tip, v => { tip = v; ciz(); });
    const slL = sl("$L$", 1, Math.max(20, Math.ceil(L * 2)), 0.5, L, "m", v => { L = v; ciz(); });
    const slQ = sl("$q$", 0, guzel(Math.max(q * 2, 40)), 0.5, q, "kN/m", v => { q = v; ciz(); });
    const slP = sl("$P$", 0, guzel(Math.max(P * 2, 100)), 1, P, "kN", v => { P = v; ciz(); });
    const slA = sl("$a/L$", 0, 1, 0.01, xa, "", v => { xa = v; ciz(); }, v => kat(v, 2));
    const slX = sl("$x/L$ (okuma)", 0, 1, 0.01, xc, "", v => { xc = v; ciz(); }, v => kat(v, 2));
    function ayarA(v) { xa = kenet(Math.round(v * 100) / 100, 0, 1); slA.ayarla(xa, true); ciz(); }
    surukle(hp, { svg: sd, tasi: pt => ayarA((pt.x - X0) / LP), klavye: dx => ayarA(xa + dx / 100) });

    kap.appendChild(el("div", { class: "ks-satir" }, sTip.kok));
    kap.appendChild(kart(sd));
    kap.appendChild(el("div", { class: "ks-ayar" }, slL.kok, slQ.kok, slP.kok, slA.kok, slX.kok));
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ks-not" }, "Turuncu P okunun üstündeki yuvarlağı sürükle: tekil yük gezer, V diyagramında basamak, M diyagramında kırılma onunla birlikte kayar. " +
      "Kesme kuvveti eğrisinin sıfır geçtiği yerde moment en büyüktür (dM/dx = V)."));
    ciz();
  }, {
    baslik: "Kiriş kesme ve moment diyagramları",
    aciklama: "Mesnet türünü seç, yükü sürükle; V ve M diyagramları ile en büyük değerler anında güncellenir.",
    varsayilan: { L: 6, P: 0, a: 3, q: 12, mesnet: "basit" }
  });

  /* ================================================================== 8. cerceve-k */

  E.kaydet("cerceve-k", function (kok, p) {
    const kap = cerceveKur(kok);
    const Em = sayiP(p.E, 2e8, 1, 1e12);
    let A = sayiP(p.A, 0.01, 1e-6, 10), I = sayiP(p.I, 8e-5, 1e-10, 1), L = sayiP(p.L, 4, 0.2, 100);
    let aci = Math.round(kenet(sayiP(p.aci, 30, 0, 180), 0, 180)), gor = "global";
    const sd = sv(230, 200, "Çerçeve elemanı ve yerel ile global eksenler");
    const sm = sv(360, 250, "6x6 çerçeve eleman rijitlik matrisi");
    const O = { x: 62, y: 156 }, R = 120;
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const hk = tutamak("b", "Elemanın açısı");
    tut.appendChild(hk);
    const formul = formulKutu();
    let slAci;

    function ciz() {
      const rad = aci * Math.PI / 180, c = Math.cos(rad), s = Math.sin(rad);
      const EA = Em * A, EI = Em * I;
      const ka = cerceveEksenel(EA, L), kb = cerceveEgilme(EI, L);
      let ma = ka, mb = kb;
      if (gor === "global") { ma = globalYap(ka, c, s); mb = globalYap(kb, c, s); }
      const tol = 1e-9 * Math.max(enBuyuk(ma), enBuyuk(mb), 1e-300);
      ma = ma.map(r => r.map(x => (Math.abs(x) <= tol ? 0 : x)));
      mb = mb.map(r => r.map(x => (Math.abs(x) <= tol ? 0 : x)));
      const top = ma.map((r, i) => r.map((x, j) => x + mb[i][j]));

      /* şema */
      bos(dyn);
      const ex = O.x + R * c, ey = O.y - R * s;
      dyn.appendChild(eksenOku(O.x, O.y, O.x + 52, O.y, "X", "soluk"));
      dyn.appendChild(eksenOku(O.x, O.y, O.x, O.y - 52, "Y", "soluk"));
      if (aci > 1) {
        const arc = [];
        for (let t = 0; t <= aci; t += Math.max(1, aci / 24)) arc.push(r2(O.x + 36 * Math.cos(t * Math.PI / 180)) + " " + r2(O.y - 36 * Math.sin(t * Math.PI / 180)));
        arc.push(r2(O.x + 36 * c) + " " + r2(O.y - 36 * s));
        dyn.appendChild(yol("M" + arc.join(" L"), { renk: "vurgu", kal: 1.8 }));
        const mid = rad / 2;
        dyn.appendChild(yaziH(O.x + 56 * Math.cos(mid) + 4, O.y - 56 * Math.sin(mid), "α=" + aci + "°", { renk: "vurgu", boyut: 11, kalin: true, hiza: "sol" }));
      }
      dyn.appendChild(cizgi(O.x, O.y, ex, ey, { renk: "metin", kal: 5 }));
      dyn.appendChild(ok(O.x + 8 * c, O.y - 8 * s, O.x + 66 * c, O.y - 66 * s, { renk: "a", kalinlik: 2.4, bas: 8 }));
      dyn.appendChild(yaziH(O.x + 80 * c - 8 * s, O.y - 80 * s - 8 * c, "x'", { renk: "a", boyut: 12, kalin: true }));
      dyn.appendChild(ok(O.x - 8 * s, O.y - 8 * c, O.x - 54 * s, O.y - 54 * c, { renk: "b", kalinlik: 2.4, bas: 8 }));
      dyn.appendChild(yaziH(O.x - 66 * s, O.y - 66 * c, "y'", { renk: "b", boyut: 12, kalin: true }));
      [[O.x, O.y, "1"], [ex, ey, "2"]].forEach((n, i) => {
        dyn.appendChild(daire(n[0], n[1], 6, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 2 }));
        dyn.appendChild(yaziH(n[0] + (i ? 14 : -12), n[1] + 16, n[2], { boyut: 11, kalin: true, renk: "soluk" }));
      });
      dyn.appendChild(yaziH(O.x + R * c / 2 + 10 * s + 6, O.y - R * s / 2 + 10 * c + 10, "L=" + kisa(L) + " m", { renk: "soluk", boyut: 11 }));
      tutKonum(hk, ex, ey);

      /* matris */
      const Tb = tablo(6, 6, {
        x: 34, y: 26, w: 48, h: 28, boyut: 10,
        metin: (i, j) => kisa(top[i][j]),
        aile: (i, j) => { const l = []; if (ma[i][j] !== 0) l.push("a"); if (mb[i][j] !== 0) l.push("b"); return l; },
        soluk: (i, j) => top[i][j] === 0,
        ust: gor === "global" ? ["U1", "V1", "Θ1", "U2", "V2", "Θ2"] : ["u1", "v1", "θ1", "u2", "v2", "θ2"],
        sol: gor === "global" ? ["U1", "V1", "Θ1", "U2", "V2", "Θ2"] : ["u1", "v1", "θ1", "u2", "v2", "θ2"]
      });
      bos(sm);
      sm.appendChild(Tb.g);
      const yl = 26 + Tb.yukseklik + 18;
      [["a", "eksenel EA/L", 34], ["b", "eğilme EI", 140], ["ab", "ikisi birlikte", 228]].forEach(o => {
        if (o[0] === "ab") {
          sm.appendChild(svg("rect", { x: o[2], y: yl - 7, width: 7, height: 14, fill: zemin("a") }));
          sm.appendChild(svg("rect", { x: o[2] + 7, y: yl - 7, width: 7, height: 14, fill: zemin("b") }));
          sm.appendChild(svg("rect", { x: o[2], y: yl - 7, width: 14, height: 14, rx: 3, fill: "none", stroke: renk("a"), "stroke-width": 1.2 }));
        } else sm.appendChild(dikdortgen(o[2], yl - 7, 14, 14, { rx: 3, dolgu: o[0], renk: o[0], kal: 1.2 }));
        sm.appendChild(yazi(o[2] + 20, yl, o[1], { hiza: "sol", boyut: 11, renk: "soluk" }));
      });
      svBoyut(sm, 34 + Tb.genislik + 6, yl + 14);

      const bn = (g) => kisa(g);
      texYaz(formul, "\\begin{aligned}\\ka{\\tfrac{EA}{L}}&=" + bn(EA / L) + ",\\quad \\kb{\\tfrac{12EI}{L^3}}=" + bn(12 * EI / (L * L * L)) + ",\\quad \\kb{\\tfrac{6EI}{L^2}}=" + bn(6 * EI / (L * L)) +
        ",\\quad \\kb{\\tfrac{4EI}{L}}=" + bn(4 * EI / L) + ",\\quad \\kb{\\tfrac{2EI}{L}}=" + bn(2 * EI / L) + "\\\\" +
        (gor === "global"
          ? "\\mathbf K_e&=\\mathbf T^T\\mathbf k\\,\\mathbf T,\\qquad c=\\cos\\alpha=" + kat(c, 3) + ",\\ s=\\sin\\alpha=" + kat(s, 3)
          : "\\mathbf k&:\\ \\text{elemanın kendi (yerel) ekseninde}\\ x'\\text{ boyunca uzanır}") + "\\end{aligned}");
    }
    const sGor = secici([{ deger: "yerel", etiket: "Yerel k" }, { deger: "global", etiket: "Global T'kT" }], gor, v => { gor = v; ciz(); });
    slAci = sl("$\\alpha$", 0, 180, 1, aci, "°", v => { aci = Math.round(v); ciz(); });
    const slL = sl("$L$", 0.5, Math.max(10, Math.ceil(L * 2)), 0.1, L, "m", v => { L = v; ciz(); });
    const slA = sl("$A$", 10, Math.max(500, Math.ceil(A * 2e4)), 5, A * 1e4, "cm²", v => { A = v / 1e4; ciz(); }, v => String(Math.round(v)));
    const slI = sl("$I$", 1000, Math.max(100000, Math.ceil(I * 2e8)), 500, I * 1e8, "cm⁴", v => { I = v / 1e8; ciz(); }, v => String(Math.round(v)));
    function ayarAci(d) { aci = Math.round(kenet(d, 0, 180)); slAci.ayarla(aci, true); ciz(); }
    surukle(hk, {
      svg: sd,
      tasi: pt => {
        let d = Math.atan2(O.y - pt.y, pt.x - O.x) * 180 / Math.PI;
        if (d < -90) d = 180; else if (d < 0) d = 0;
        ayarAci(d);
      },
      klavye: dx => ayarAci(aci - dx)
    });

    kap.appendChild(el("div", { class: "ks-satir" }, sGor.kok));
    kap.appendChild(el("div", { class: "ks-iki" }, kart(sd), kart(sm)));
    kap.appendChild(el("div", { class: "ks-ayar" }, slAci.kok, slL.kok, slA.kok, slI.kok));
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ks-not" }, "Elemanın ucundaki yuvarlağı sürükle ya da α kaydırıcısını oynat. Yerel kipte eksenel (mavi) ve eğilme (turuncu) parselleri ayrıdır; " +
      "global kipte TᵀkT bu iki parseli karıştırır ve çift renkli hücreler belirir."));
    ciz();
  }, {
    baslik: "Çerçeve elemanı: 6x6 rijitlik matrisi",
    aciklama: "Eksenel ve eğilme parsellerini renkli gör; açıyı değiştirip global matrisin nasıl karıştığını izle.",
    varsayilan: { E: 2e8, A: 0.01, I: 8e-5, L: 4, aci: 30 }
  });

  /* ================================================================== 9. modal-titresim */

  function modalCoz(ms, ks) {
    const n = ms.length, K = sifirMat(n), M = ms.slice();
    for (let i = 0; i < n; i++) {
      K[i][i] += ks[i];
      if (i + 1 < n) { K[i][i] += ks[i + 1]; K[i][i + 1] -= ks[i + 1]; K[i + 1][i] -= ks[i + 1]; }
    }
    const S = K.map((r, i) => r.map((x, j) => x / Math.sqrt(M[i] * M[j])));
    const e = ozdegerSim(S);
    const modlar = e.deg.map((lam, m) => {
      const l = Math.max(lam, 0), w = Math.sqrt(l);
      let phi = M.map((mi, i) => e.vek[i][m] / Math.sqrt(mi));
      const mx = Math.max.apply(null, phi.map(Math.abs)) || 1;
      phi = phi.map(x => x / mx);
      const ust = phi[n - 1];
      if (ust < 0 || (Math.abs(ust) < 1e-9 && phi.find(x => Math.abs(x) > 1e-9) < 0)) phi = phi.map(x => -x);
      return { lam: l, w, f: w / (2 * Math.PI), T: w > 0 ? 2 * Math.PI / w : Infinity, phi };
    });
    return { K, M, modlar };
  }

  E.kaydet("modal-titresim", function (kok, p) {
    const kap = cerceveKur(kok);
    const n0 = Math.min(4, Math.max(1, Math.max(Array.isArray(p.m) ? p.m.length : 0, Array.isArray(p.k) ? p.k.length : 0, 2)));
    let ms = listeP(p.m, [100, 100], 0.01, 1e9, 1, 4), ks = listeP(p.k, [30000, 30000], 0.01, 1e12, 1, 4);
    const n = Math.min(4, Math.max(ms.length, ks.length, 1));
    while (ms.length < n) ms.push(ms[ms.length - 1]);
    while (ks.length < n) ks.push(ks[ks.length - 1]);
    ms = ms.slice(0, n); ks = ks.slice(0, n);
    void n0;
    let mod = 0, sol = modalCoz(ms, ks), anim = null;
    const W = 440, H = 250, XC = 118, Yg = 224, GEN = 44, GENK = 34, AMP = 24;
    const sd = sv(W, H, "Kat kütleleri, yaylar ve mod şekli animasyonu");
    const statik = svg("g"), slabs = [], cols = [];
    sd.appendChild(statik);
    const formul = formulKutu();
    const ayarlar = el("div", { class: "ks-ayar" });
    const modSec = el("div", { class: "ks-satir" });
    const hF = Math.min(54, 176 / n);
    const sy = i => Yg - (i + 1) * hF; // kat levhasının üst kenarı

    function iskelet() {
      bos(statik);
      slabs.length = 0; cols.length = 0;
      statik.appendChild(cizgi(XC - 70, Yg, XC + 70, Yg, { renk: "metin", kal: 2 }));
      for (let x = XC - 66; x <= XC + 60; x += 12) statik.appendChild(cizgi(x + 8, Yg, x, Yg + 9, { renk: "metin", kal: 1 }));
      for (let i = 0; i < n; i++) {
        const a = aileOf(i);
        statik.appendChild(yaziH(XC - GEN - AMP - 6, (i === 0 ? Yg : sy(i - 1) + 9) - hF / 2 + 4, "k" + (i + 1), { renk: "soluk", boyut: 10.5, hiza: "sag", kalin: true }));
        statik.appendChild(yaziH(XC + GEN + AMP + 6, sy(i) + 5, "m" + (i + 1) + "=" + kisa(ms[i]) + " t", { renk: a, boyut: 10.5, hiza: "sol", kalin: true }));
        [-1, 1].forEach(sg => {
          const l = svg("line", { stroke: renk("metin"), "stroke-width": 3, "stroke-linecap": "round" });
          statik.appendChild(l); cols.push({ l, sg, i });
        });
      }
      for (let i = 0; i < n; i++) {
        const r = svg("rect", { height: 9, width: GEN * 2, rx: 3, y: sy(i), fill: zemin(aileOf(i)), stroke: renk(aileOf(i)), "stroke-width": 2 });
        statik.appendChild(r); slabs.push(r);
      }
    }
    function konum(t) {
      const mo = sol.modlar[mod], s = t === null ? 1 : Math.sin(t);
      const sh = i => (i < 0 ? 0 : AMP * mo.phi[i] * s);
      slabs.forEach((r, i) => r.setAttribute("x", r2(XC - GEN + sh(i))));
      cols.forEach(c => {
        const y1 = c.i === 0 ? Yg : sy(c.i - 1) + 9, y2 = sy(c.i);
        c.l.setAttribute("x1", r2(XC + c.sg * GENK + sh(c.i - 1))); c.l.setAttribute("y1", y1);
        c.l.setAttribute("x2", r2(XC + c.sg * GENK + sh(c.i))); c.l.setAttribute("y2", y2);
      });
    }

    const dg = svg("g");
    sd.appendChild(dg);
    function grafik() {
      bos(dg);
      const mo = sol.modlar[mod], wmax = sol.modlar[n - 1].w, wr = wmax * 1.25 || 1;
      const gx = 270, gw = 160, gy = 70, ga = 46;
      dg.appendChild(yazi(gx, 14, "det(K − ω²M) / det(K)", { hiza: "sol", boyut: 11, renk: "soluk", kalin: true }));
      dg.appendChild(cizgi(gx, gy, gx + gw, gy, { renk: "soluk", kal: 1.2 }));
      const d0 = detNum(sol.K) || 1, pts = [];
      for (let i = 0; i <= 240; i++) {
        const w = wr * i / 240, D = detNum(sol.K.map((r, a) => r.map((x, b) => x - (a === b ? w * w * sol.M[a] : 0)))) / d0;
        pts.push(r2(gx + gw * i / 240) + " " + r2(gy - ga * kenet(D, -1.15, 1.15)));
      }
      dg.appendChild(yol("M" + pts.join(" L"), { renk: "metin", kal: 2 }));
      sol.modlar.forEach((m, i) => {
        const x = gx + gw * m.w / wr, ac = i === mod;
        dg.appendChild(cizgi(x, gy - ga, x, gy + ga, { renk: aileOf(i), kal: ac ? 1.8 : 1, kesik: true, opak: ac ? 1 : 0.55 }));
        dg.appendChild(daire(x, gy, ac ? 5 : 3.6, { dolgu: aileOf(i), dolguHam: renk(aileOf(i)), renk: "kart", kal: 1 }));
        dg.appendChild(yaziH(x, gy + ga + 12, "ω" + (i + 1), { renk: aileOf(i), boyut: 11, kalin: true }));
      });
      dg.appendChild(yazi(gx + gw, gy + ga + 26, "ω [rad/s] →", { hiza: "sag", boyut: 10.5, renk: "soluk" }));
      const t0 = 178;
      dg.appendChild(yaziH(gx, t0, "Mod " + (mod + 1), { hiza: "sol", boyut: 12, kalin: true, renk: aileOf(mod) }));
      dg.appendChild(yazi(gx, t0 + 17, "ω = " + kisa(mo.w) + " rad/s", { hiza: "sol", boyut: 11.5 }));
      dg.appendChild(yazi(gx, t0 + 33, "f = " + kisa(mo.f) + " Hz", { hiza: "sol", boyut: 11.5 }));
      dg.appendChild(yazi(gx, t0 + 49, "T = " + kisa(mo.T) + " s", { hiza: "sol", boyut: 11.5 }));
    }
    function matTex(A) { return "\\begin{bmatrix}" + A.map(r => r.map(x => kisa(x)).join("&")).join("\\\\") + "\\end{bmatrix}"; }
    function yaz() {
      const mo = sol.modlar[mod];
      const tab = "\\begin{array}{c|ccc}\\text{mod}&\\omega\\,[\\text{rad/s}]&f\\,[\\text{Hz}]&T\\,[\\text{s}]\\\\\\hline " +
        sol.modlar.map((m, i) => "\\" + MAK[i % 3].slice(1) + "{" + (i + 1) + "}&" + kisa(m.w) + "&" + kisa(m.f) + "&" + kisa(m.T)).join("\\\\") + "\\end{array}";
      texYaz(formul, "\\begin{aligned}\\mathbf K&=" + matTex(sol.K) + ",\\quad \\mathbf M=\\mathrm{diag}(" + ms.map(kisa).join(",") + ")\\\\" +
        "&\\det(\\mathbf K-\\omega^2\\mathbf M)=0\\ \\Rightarrow\\ " + tab + "\\\\" +
        "\\boldsymbol\\varphi_{" + (mod + 1) + "}&=\\left[" + mo.phi.map(x => kat(x, 3)).join(",\\ ") + "\\right]^T\\end{aligned}");
    }
    function hepsi() { sol = modalCoz(ms, ks); iskelet(); konum(0); grafik(); yaz(); modSec.firstChild && secimYenile(); }
    let sMod = null;
    function secimYenile() { /* mod seçici sayısı sabit (n); yalnız etiketler değişmez */ }
    function ayarYap() {
      bos(ayarlar);
      ms.forEach((m, i) => ayarlar.appendChild(sl("$m_" + (i + 1) + "$", 1, guzel(Math.max(ms[i] * 3, 300)), 1, m, "t", v => { ms[i] = v; hepsi(); }, v => String(Math.round(v))).kok));
      ks.forEach((k, i) => ayarlar.appendChild(sl("$k_" + (i + 1) + "$", 100, guzel(Math.max(ks[i] * 3, 100000)), 100, k, "kN/m", v => { ks[i] = v; hepsi(); }, v => String(Math.round(v))).kok));
    }
    sMod = secici(Array.from({ length: n }, (_, i) => ({ deger: String(i), etiket: "Mod " + (i + 1) })), "0", v => { mod = Number(v) || 0; konum(0); grafik(); yaz(); });
    modSec.appendChild(sMod.kok);

    kap.appendChild(modSec);
    kap.appendChild(kart(sd));
    kap.appendChild(el("div", { class: "ks-ayar" }, ayarlar));
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ks-not" }, "Kütleleri t, yay rijitliklerini kN/m olarak değiştir. Animasyon, seçili modun şeklidir (genlik abartılı, hız gösterim içindir). " +
      "OMA bağlantısı: yapının ortam titreşiminden okunan frekans ve mod şekilleri, bu hesapla bulunan ω ve φ değerleriyle karşılaştırılır; ölçülen modlar modeli güncellemek için kullanılır."));
    iskelet(); konum(0); grafik(); yaz(); ayarYap();
    if (!hareketAzalt()) {
      anim = animasyon(kap, t => {
        const w1 = sol.modlar[0].w || 1, wv = Math.min(10, 2.6 * (sol.modlar[mod].w / w1));
        konum(t * wv);
      });
    }
    return { yok_et() { if (anim) anim.durdur(); } };
  }, {
    baslik: "Kat kütleleri ve modal titreşim",
    aciklama: "Çok katlı kesmeli binanın doğal frekansları ve mod şekilleri; kütle ve rijitlik değişince canlı güncellenir.",
    varsayilan: { m: [100, 100], k: [30000, 30000] }
  });

  /* ================================================================== 10. uzay-kafes-cubuk */

  /* 3B yardımcıları: aksonometrik izdüşüm (motorla aynı bakış: Y etrafında -32°, yukarıdan 22°) ve yerel eksen matrisi λ. */
  const BAKIS_FI = -32 * Math.PI / 180, BAKIS_PSI = 22 * Math.PI / 180;
  function izdus(x, y, z) { // → [u, v], v yukarı
    const u = x * Math.cos(BAKIS_FI) + z * Math.sin(BAKIS_FI);
    const derin = -x * Math.sin(BAKIS_FI) + z * Math.cos(BAKIS_FI);
    return [u, y * Math.cos(BAKIS_PSI) - derin * Math.sin(BAKIS_PSI)];
  }
  /* Yatay açı fi (X'ten Z'ye doğru) ve düşey açı psi (yatay düzlemden yukarı), derece → doğrultu kosinüsleri [cx, cy, cz] */
  function kosinusler(fi, psi) {
    const f = fi * Math.PI / 180, s = psi * Math.PI / 180;
    return [Math.cos(s) * Math.cos(f), Math.sin(s), Math.cos(s) * Math.sin(f)].map(x => (Math.abs(x) < 1e-12 ? 0 : x));
  }
  /* λ (satırlar x', y', z'): y' elemanı içeren düşey düzlemde yukarı, z' = x' × y' yatay; düşey elemanda z' = Z (motordaki _lam3b ile aynı). */
  function lam3b(cx, cy, cz) {
    const D = Math.hypot(cx, cz);
    if (D < 1e-9) return [[0, cy, 0], [-cy, 0, 0], [0, 0, 1]];
    return [[cx, cy, cz], [-cx * cy / D, D, -cy * cz / D], [-cz / D, 0, cx / D]];
  }
  function T12(lam) {
    const T = sifirMat(12);
    for (let b = 0; b < 4; b++) for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) T[3 * b + i][3 * b + j] = lam[i][j];
    return T;
  }
  function donustur(K, T) { return carpMat(devrik(T), carpMat(K, T)); }
  /* 12x12 uzay çerçeve yerel matrisi dört blok hâlinde: a eksenel (EA/L), b eğilme x'y' (EIz), c eğilme x'z' (EIy), t burulma (GJ/L).
   * Sıra u, v, w, θx, θy, θz (i ucu), aynısı (j ucu); motordaki _k_cerceve3b ile aynı. */
  function cerceve3bBloklar(E, G, A, Iy, Iz, J, L) {
    const a = sifirMat(12), b = sifirMat(12), c = sifirMat(12), t = sifirMat(12);
    const koy = (M, i, j, v) => { M[i][j] = v; M[j][i] = v; };
    const ea = E * A / L, gj = G * J / L, bz = E * Iz / (L * L * L), by = E * Iy / (L * L * L);
    koy(a, 0, 0, ea); koy(a, 0, 6, -ea); koy(a, 6, 6, ea);
    koy(t, 3, 3, gj); koy(t, 3, 9, -gj); koy(t, 9, 9, gj);
    koy(b, 1, 1, 12 * bz); koy(b, 1, 5, 6 * L * bz); koy(b, 1, 7, -12 * bz); koy(b, 1, 11, 6 * L * bz);
    koy(b, 5, 5, 4 * L * L * bz); koy(b, 5, 7, -6 * L * bz); koy(b, 5, 11, 2 * L * L * bz);
    koy(b, 7, 7, 12 * bz); koy(b, 7, 11, -6 * L * bz); koy(b, 11, 11, 4 * L * L * bz);
    koy(c, 2, 2, 12 * by); koy(c, 2, 4, -6 * L * by); koy(c, 2, 8, -12 * by); koy(c, 2, 10, -6 * L * by);
    koy(c, 4, 4, 4 * L * L * by); koy(c, 4, 8, 6 * L * by); koy(c, 4, 10, 2 * L * L * by);
    koy(c, 8, 8, 12 * by); koy(c, 8, 10, 6 * L * by); koy(c, 10, 10, 4 * L * L * by);
    return { a, b, c, t };
  }
  /* Uç tutamağının sürüklenmesi: yatay sürükleme φ'yi, düşey sürükleme ψ'yi değiştirir (izdüşümde X sağa, Y yukarı). */
  function aciSurukle(hd, sd, oku, ayar) {
    let bas = null;
    surukle(hd, {
      svg: sd,
      basla: pt => { const a = oku(); bas = { x: pt.x, y: pt.y, fi: a[0], psi: a[1] }; },
      tasi: pt => {
        if (!bas) { const a = oku(); bas = { x: pt.x, y: pt.y, fi: a[0], psi: a[1] }; }
        ayar(bas.fi - (pt.x - bas.x) * 1.2, bas.psi - (pt.y - bas.y) * 1.2);
      },
      birak: () => { bas = null; },
      klavye: (dx, dy) => { const a = oku(); ayar(a[0] - dx, a[1] - dy); }
    });
  }
  function globalEksenler(dyn, O, pr, boy) {
    [[1, 0, 0, "X"], [0, 1, 0, "Y"], [0, 0, 1, "Z"]].forEach(a => {
      const e = pr(a[0] * boy, a[1] * boy, a[2] * boy);
      dyn.appendChild(eksenOku(O.x, O.y, e[0], e[1], a[3], "soluk"));
    });
  }

  E.kaydet("uzay-kafes-cubuk", function (kok, p) {
    const kap = cerceveKur(kok);
    const Em = sayiP(p.E, 200e6, 1, 1e12), A = sayiP(p.A, 0.001, 1e-9, 100);
    let L = sayiP(p.L, 5, 0.1, 1000);
    let fi = ((sayiP(p.fi, 35) % 360) + 360) % 360, psi = kenet(sayiP(p.psi, 30), -90, 90);
    let gorunum = "katsayi";
    const W = 300, H = 262, O = { x: 150, y: 128 }, R = 116;
    const sd = sv(W, H, "Uzay kafes çubuğu: yatay açı φ ve düşey açı ψ ile doğrultu");
    const sm = sv(340, 260, "Uzay kafes elemanı 6x6 global rijitlik matrisi");
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const hd = tutamak("b", "Çubuğun ucu: yatay sürükleme φ, düşey sürükleme ψ");
    tut.appendChild(hd);
    const formul = formulKutu(), formul2 = formulKutu();
    const pr = (x, y, z) => { const q = izdus(x, y, z); return [O.x + R * q[0], O.y - R * q[1]]; };
    const AIL = ["a", "b", "c"];
    let slFi, slPsi;

    function ciz() {
      bos(dyn);
      const c = kosinusler(fi, psi), EAL = Em * A / L;
      globalEksenler(dyn, O, pr, 1.12);
      /* bileşen kutusu: X boyunca cx (mavi), Z boyunca cz (yeşil), düşey cy (turuncu); düşey düzlem izi */
      const Px = pr(c[0], 0, 0), Pf = pr(c[0], 0, c[2]), Pj = pr(c[0], c[1], c[2]);
      dyn.appendChild(yol("M" + O.x + " " + O.y + " L" + r2(Pf[0]) + " " + r2(Pf[1]) + " L" + r2(Pj[0]) + " " + r2(Pj[1]) + " Z", { dolgu: "b", renk: null }));
      dyn.appendChild(cizgi(O.x, O.y, Px[0], Px[1], { renk: "a", kal: 3, kesik: true }));
      dyn.appendChild(cizgi(Px[0], Px[1], Pf[0], Pf[1], { renk: "c", kal: 3, kesik: true }));
      dyn.appendChild(cizgi(Pf[0], Pf[1], Pj[0], Pj[1], { renk: "b", kal: 3, kesik: true }));
      dyn.appendChild(cizgi(O.x, O.y, Pf[0], Pf[1], { renk: "soluk", kal: 1, kesik: "2 3" }));
      dyn.appendChild(cizgi(O.x, O.y, Pj[0], Pj[1], { renk: "metin", kal: 5 }));
      dyn.appendChild(daire(O.x, O.y, 6, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 2 }));
      dyn.appendChild(yaziH(O.x - 12, O.y - 11, "1", { boyut: 11, kalin: true, renk: "soluk" }));
      dyn.appendChild(yaziH(Pj[0] + 15, Pj[1] - 13, "2", { boyut: 11, kalin: true, renk: "soluk" }));
      if (Math.abs(c[0]) > 0.22) dyn.appendChild(yaziH((O.x + Px[0]) / 2, (O.y + Px[1]) / 2 + 14, "cx = " + kat(c[0], 2), { renk: "a", boyut: 11, kalin: true }));
      if (Math.abs(c[2]) > 0.22) dyn.appendChild(yaziH((Px[0] + Pf[0]) / 2 + (c[2] > 0 ? -10 : 10), (Px[1] + Pf[1]) / 2 + (c[2] > 0 ? 14 : -12), "cz = " + kat(c[2], 2), { renk: "c", boyut: 11, kalin: true }));
      if (Math.abs(c[1]) > 0.22) dyn.appendChild(yaziH(Pf[0] + (c[0] >= 0 ? 9 : -9), (Pf[1] + Pj[1]) / 2, "cy = " + kat(c[1], 2), { renk: "b", boyut: 11, kalin: true, hiza: c[0] >= 0 ? "sol" : "sag" }));
      dyn.appendChild(yaziH(W / 2, H - 9, "L = " + kisa(L) + " m,  φ = " + Math.round(fi) + "°,  ψ = " + Math.round(psi) + "°", { renk: "soluk", boyut: 11 }));
      tutKonum(hd, Pj[0], Pj[1]);

      /* 6x6 matris: B = c cᵀ, k = (EA/L)[B -B; -B B]; hücre tonu |değer| ile */
      bos(sm);
      const K6 = sifirMat(6);
      for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
        const b = c[i] * c[j];
        K6[i][j] = b; K6[i + 3][j + 3] = b; K6[i][j + 3] = -b; K6[i + 3][j] = -b;
      }
      const Tb = tablo(6, 6, {
        x: 34, y: 24, w: 46, h: 32, boyut: 11,
        metin: (i, j) => gorunum === "katsayi" ? kat(K6[i][j], 2) : kisa(EAL * K6[i][j]),
        aile: (i, j) => { const q1 = i % 3, q2 = j % 3; return q1 === q2 ? AIL[q1] : [AIL[q1], AIL[q2]]; },
        soluk: (i, j) => Math.abs(K6[i][j]) < 5e-3,
        ust: ["u1", "v1", "w1", "u2", "v2", "w2"], sol: ["u1", "v1", "w1", "u2", "v2", "w2"]
      });
      for (let i = 0; i < 6; i++) for (let j = 0; j < 6; j++) {
        const q1 = i % 3, q2 = j % 3, fam = q1 === q2 ? [AIL[q1]] : [AIL[q1], AIL[q2]];
        const ton = 0.06 + 0.5 * Math.abs(K6[i][j]);
        let n = 0;
        Tb.rects[i][j].querySelectorAll("rect").forEach(rc => {
          if (rc.getAttribute("fill") === "none") return;
          rc.style.fill = renk(fam[Math.min(n, fam.length - 1)]);
          rc.style.fillOpacity = String(+ton.toFixed(3));
          n++;
        });
      }
      [[0, 0], [0, 3], [3, 0], [3, 3]].forEach(b => { Tb.kutu(b[0], b[1], b[0] + 2, b[1] + 2, "kenar", { kesik: true, kal: 1.6 }); });
      sm.appendChild(Tb.g);
      sm.appendChild(yazi(34 + Tb.genislik / 2, 24 + Tb.yukseklik + 16, gorunum === "katsayi" ? "k / (EA/L)" : "k  [kN/m]", { renk: "soluk", boyut: 11 }));
      svBoyut(sm, 34 + Tb.genislik + 8, 24 + Tb.yukseklik + 28);

      let not = "";
      if (Math.abs(c[0]) < 1e-9 && Math.abs(c[2]) < 1e-9) not = "Düşey çubuk: yalnız v terimleri dolu.";
      else if (Math.abs(c[2]) < 1e-9) not = "Düzlem kafes (c_z = 0): 13. dersin c^2, cs, s^2 deseni.";
      else if (Math.abs(c[1]) < 1e-9) not = "Yatay çubuk: v satırları boş, u ve w dolu.";
      texYaz(formul, "\\ka{c_x}=" + kat(c[0], 3) + ",\\quad \\kb{c_y}=" + kat(c[1], 3) + ",\\quad \\kc{c_z}=" + kat(c[2], 3) + ",\\quad L=" + kisa(L) + "\\ \\text{m},\\quad \\frac{EA}{L}=" + kisa(EAL) + "\\ \\text{kN/m}" +
        (not ? "\\quad\\text{" + not + "}" : ""));
    }
    texYaz(formul2, "\\mathbf k=\\frac{EA}{L}\\begin{bmatrix}\\mathbf B&-\\mathbf B\\\\-\\mathbf B&\\mathbf B\\end{bmatrix},\\qquad " +
      "\\mathbf B=\\mathbf c\\,\\mathbf c^T=\\begin{bmatrix}\\ka{c_x^2}&c_xc_y&c_xc_z\\\\ c_xc_y&\\kb{c_y^2}&c_yc_z\\\\ c_xc_z&c_yc_z&\\kc{c_z^2}\\end{bmatrix}");

    function ayar(f, s_) {
      fi = ((Math.round(f) % 360) + 360) % 360; psi = kenet(Math.round(s_), -90, 90);
      slFi.ayarla(fi, true); slPsi.ayarla(psi, true); ciz();
    }
    slFi = sl("$\\varphi$ (yatay açı)", 0, 360, 1, fi, "°", v => { fi = v; ciz(); }, v => String(Math.round(v)));
    slPsi = sl("$\\psi$ (düşey açı)", -90, 90, 1, psi, "°", v => { psi = v; ciz(); }, v => String(Math.round(v)));
    const slL = sl("$L$", 0.5, Math.max(10, Math.ceil(L * 2)), 0.1, L, "m", v => { L = v; ciz(); });
    aciSurukle(hd, sd, () => [fi, psi], ayar);
    const sg = secici([{ deger: "katsayi", etiket: "Katsayı" }, { deger: "kNm", etiket: "kN/m" }], gorunum, v => { gorunum = v; ciz(); });
    const hizli = dugmeSatiri();
    [["X ekseni", 0, 0], ["Y ekseni", 0, 90], ["Z ekseni", 90, 0], ["3-4-5 düzlemde", 0, 53.13], ["Tripod 1. çubuk", 180, 36.87], ["(2, 1, 2)", 45, 19.47]]
      .forEach(a => hizli.appendChild(dugme(a[0], () => ayar(a[1], a[2]))));
    kap.appendChild(el("div", { class: "ks-iki" }, kart(sd), kart(sm)));
    kap.appendChild(el("div", { class: "ks-ayar" }, slFi.kok, slPsi.kok, slL.kok, el("div", { class: "ks-satir" }, sg.kok)));
    kap.appendChild(hizli);
    kap.appendChild(formul);
    kap.appendChild(formul2);
    kap.appendChild(el("p", { class: "ks-not" }, "Çubuğun ucunu sürükle: yatay hareket φ'yi, düşey hareket ψ'yi değiştirir. Mavi cx, turuncu cy, yeşil cz; iki renkli hücreler " +
      "çapraz çarpımlardır (cx·cy gibi). Hücre ne kadar koyuysa |değer| o kadar büyüktür; köşegenin toplamı her zaman 1'dir."));
    ciz();
  }, {
    baslik: "Uzay kafes çubuğu: doğrultu kosinüsleri ve 6x6 matris",
    aciklama: "Yatay ve düşey açıyla çubuğu uzayda döndür; cx, cy, cz ve 6x6 global matrisin c·cᵀ deseni anında değişir.",
    varsayilan: { E: 200e6, A: 0.001, L: 5, fi: 35, psi: 30 }
  });

  /* ================================================================== 11. uzay-cerceve-k */

  E.kaydet("uzay-cerceve-k", function (kok, p) {
    const kap = cerceveKur(kok);
    let Em = sayiP(p.E, 2e8, 1e3, 1e12), G = sayiP(p.G, 8e7, 1e3, 1e12);
    let A = sayiP(p.A, 0.01, 1e-6, 10), Iy = sayiP(p.Iy, 1e-4, 1e-10, 1), Iz = sayiP(p.Iz, 2e-4, 1e-10, 1), J = sayiP(p.J, 2e-4, 1e-10, 1);
    let L = sayiP(p.L, 4, 0.2, 100);
    let fi = ((sayiP(p.fi, 30) % 360) + 360) % 360, psi = kenet(sayiP(p.psi, 20), -90, 90);
    let gor = p.gorunum === "global" ? "global" : "yerel";
    const W = 250, H = 240, O = { x: 112, y: 134 }, R = 98;
    const sd = sv(W, H, "Uzay çerçeve elemanı ve yerel eksenleri x', y', z'");
    const sm = sv(400, 320, "12x12 uzay çerçeve eleman rijitlik matrisi");
    const dyn = svg("g"), tut = svg("g");
    sd.appendChild(dyn); sd.appendChild(tut);
    const hd = tutamak("b", "Elemanın j ucu: yatay sürükleme φ, düşey sürükleme ψ");
    tut.appendChild(hd);
    const formul = formulKutu();
    const pr = (x, y, z) => { const q = izdus(x, y, z); return [O.x + R * q[0], O.y - R * q[1]]; };
    const ETIK = ["u1", "v1", "w1", "θx1", "θy1", "θz1", "u2", "v2", "w2", "θx2", "θy2", "θz2"];
    const AIL = ["a", "b", "c", "sil"];
    let slFi, slPsi;

    function ciz() {
      const c = kosinusler(fi, psi), lam = lam3b(c[0], c[1], c[2]), dusey = Math.hypot(c[0], c[2]) < 1e-9;
      const bl = cerceve3bBloklar(Em, G, A, Iy, Iz, J, L);
      let parcalar = [bl.a, bl.b, bl.c, bl.t];
      if (gor === "global") { const T = T12(lam); parcalar = parcalar.map(M => donustur(M, T)); }
      const tol = 1e-9 * Math.max(enBuyuk(parcalar[0]), enBuyuk(parcalar[1]), enBuyuk(parcalar[2]), enBuyuk(parcalar[3]), 1e-300);
      parcalar = parcalar.map(M => M.map(r => r.map(x => (Math.abs(x) <= tol ? 0 : x))));
      const top = sifirMat(12);
      parcalar.forEach(M => { for (let i = 0; i < 12; i++) for (let j = 0; j < 12; j++) top[i][j] += M[i][j]; });

      /* sahne: eleman, düşey düzlem izi, yerel eksenler */
      bos(dyn);
      globalEksenler(dyn, O, pr, 0.58);
      const Pj = pr(c[0], c[1], c[2]), Pf = pr(c[0], 0, c[2]), Pm = pr(0.52 * c[0], 0.52 * c[1], 0.52 * c[2]);
      if (!dusey) {
        dyn.appendChild(yol("M" + O.x + " " + O.y + " L" + r2(Pf[0]) + " " + r2(Pf[1]) + " L" + r2(Pj[0]) + " " + r2(Pj[1]) + " Z", { dolgu: "b", renk: null }));
        dyn.appendChild(cizgi(O.x, O.y, Pf[0], Pf[1], { renk: "soluk", kal: 1, kesik: "2 3" }));
        dyn.appendChild(cizgi(Pf[0], Pf[1], Pj[0], Pj[1], { renk: "soluk", kal: 1, kesik: "2 3" }));
      }
      dyn.appendChild(cizgi(O.x, O.y, Pj[0], Pj[1], { renk: "metin", kal: 5 }));
      const qy = izdus(lam[1][0], lam[1][1], lam[1][2]), ny = Math.hypot(qy[0], qy[1]) || 1;
      [["a", "x'", 0.3], ["b", "y'", 0.44], ["c", "z'", 0.44]].forEach((o, k) => {
        const q = izdus(lam[k][0], lam[k][1], lam[k][2]);
        const e = [Pm[0] + o[2] * R * q[0], Pm[1] - o[2] * R * q[1]];
        const d = [e[0] - Pm[0], e[1] - Pm[1]], n = Math.hypot(d[0], d[1]) || 1;
        dyn.appendChild(ok(Pm[0], Pm[1], e[0], e[1], { renk: o[0], kalinlik: 2.4, bas: 8 }));
        // x' etiketi elemanın üstüne değil, y' okunun ters tarafına (yana) yazılır
        const et = k === 0 ? [e[0] - 11 * qy[0] / ny, e[1] + 11 * qy[1] / ny] : [e[0] + 10 * d[0] / n, e[1] + 10 * d[1] / n];
        dyn.appendChild(yaziH(et[0], et[1], o[1], { renk: o[0], boyut: 12, kalin: true }));
      });
      dyn.appendChild(daire(O.x, O.y, 5.5, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 2 }));
      dyn.appendChild(yaziH(O.x - 12, O.y - 11, "i", { boyut: 11, kalin: true, renk: "soluk" }));
      dyn.appendChild(yaziH(Pj[0] + 15, Pj[1] - 13, "j", { boyut: 11, kalin: true, renk: "soluk" }));
      dyn.appendChild(yaziH(W / 2, H - 10, "L = " + kisa(L) + " m,  φ = " + Math.round(fi) + "°,  ψ = " + Math.round(psi) + "°" + (dusey ? "  (düşey: z' = Z)" : ""), { renk: "soluk", boyut: 11 }));
      tutKonum(hd, Pj[0], Pj[1]);

      /* 12x12 matris: her parsel kendi ailesinde; global kipte karışan hücreler şeritli */
      bos(sm);
      const Tb = tablo(12, 12, {
        x: 28, y: 22, w: 29, h: 20, boyut: 7.5,
        metin: (i, j) => kisa(top[i][j]),
        aile: (i, j) => AIL.filter((f, k) => parcalar[k][i][j] !== 0),
        soluk: (i, j) => top[i][j] === 0,
        ust: ETIK, sol: ETIK
      });
      [[0, 0], [0, 6], [6, 0], [6, 6]].forEach(b => { Tb.kutu(b[0], b[1], b[0] + 5, b[1] + 5, "kenar", { kesik: true, kal: 1.4 }); });
      sm.appendChild(Tb.g);
      const yl = 22 + Tb.yukseklik + 16;
      [["a", "eksenel EA/L", 28, 0], ["b", "eğilme x'y' (EIz)", 200, 0], ["c", "eğilme x'z' (EIy)", 28, 1], ["sil", "burulma GJ/L", 200, 1]].forEach(o => {
        const y = yl + o[3] * 18;
        sm.appendChild(dikdortgen(o[2], y - 7, 14, 14, { rx: 3, dolgu: o[0], renk: o[0], kal: 1.2 }));
        sm.appendChild(yazi(o[2] + 20, y, o[1], { hiza: "sol", boyut: 11, renk: "soluk" }));
      });
      svBoyut(sm, 28 + Tb.genislik + 6, yl + 30);

      const bn = kisa;
      let tex = "\\begin{aligned}\\ka{\\tfrac{EA}{L}}&=" + bn(Em * A / L) + ",\\quad \\ksil{\\tfrac{GJ}{L}}=" + bn(G * J / L) + "\\\\" +
        "\\kb{\\tfrac{12EI_z}{L^3}}&=" + bn(12 * Em * Iz / (L * L * L)) + ",\\ \\kb{\\tfrac{6EI_z}{L^2}}=" + bn(6 * Em * Iz / (L * L)) + ",\\ \\kb{\\tfrac{4EI_z}{L}}=" + bn(4 * Em * Iz / L) + "\\\\" +
        "\\kc{\\tfrac{12EI_y}{L^3}}&=" + bn(12 * Em * Iy / (L * L * L)) + ",\\ \\kc{\\tfrac{6EI_y}{L^2}}=" + bn(6 * Em * Iy / (L * L)) + ",\\ \\kc{\\tfrac{4EI_y}{L}}=" + bn(4 * Em * Iy / L);
      if (gor === "global") {
        const satir = r => r.map(x => kat(x, 3)).join("&");
        tex += "\\\\ c_x&=" + kat(c[0], 3) + ",\\ c_y=" + kat(c[1], 3) + ",\\ c_z=" + kat(c[2], 3) + (dusey ? ":\\ \\text{düşey eleman, } z'=Z" : "") +
          "\\\\ \\boldsymbol\\lambda&=\\begin{bmatrix}" + satir(lam[0]) + "\\\\" + satir(lam[1]) + "\\\\" + satir(lam[2]) + "\\end{bmatrix},\\quad " +
          "\\mathbf K_e=\\mathbf T^T\\mathbf k\\,\\mathbf T,\\ \\mathbf T=\\operatorname{diag}(\\boldsymbol\\lambda,\\boldsymbol\\lambda,\\boldsymbol\\lambda,\\boldsymbol\\lambda)";
      } else tex += "\\\\ \\mathbf k&:\\ \\text{elemanın kendi ekseninde; } x'z'\\text{ bloğunda } 6L \\text{ terimleri ters işaretli } (\\theta_y=-dw/dx)";
      texYaz(formul, tex + "\\end{aligned}");
    }
    function ayar(f, s_) {
      fi = ((Math.round(f) % 360) + 360) % 360; psi = kenet(Math.round(s_), -90, 90);
      slFi.ayarla(fi, true); slPsi.ayarla(psi, true); ciz();
    }
    const sGor = secici([{ deger: "yerel", etiket: "Yerel k" }, { deger: "global", etiket: "Global T'kT" }], gor, v => { gor = v; ciz(); });
    const yuvarla = v => String(Math.round(v));
    const slE = sl("$E$", 1, Math.max(400, Math.ceil(Em / 1e6 * 2)), 1, Em / 1e6, "GPa", v => { Em = v * 1e6; ciz(); }, yuvarla);
    const slG = sl("$G$", 1, Math.max(200, Math.ceil(G / 1e6 * 2)), 1, G / 1e6, "GPa", v => { G = v * 1e6; ciz(); }, yuvarla);
    const slA = sl("$A$", 10, Math.max(500, Math.ceil(A * 2e4)), 5, A * 1e4, "cm²", v => { A = v / 1e4; ciz(); }, yuvarla);
    const slIy = sl("$I_y$", 100, Math.max(100000, Math.ceil(Iy * 2e8)), 100, Iy * 1e8, "cm⁴", v => { Iy = v / 1e8; ciz(); }, yuvarla);
    const slIz = sl("$I_z$", 100, Math.max(100000, Math.ceil(Iz * 2e8)), 100, Iz * 1e8, "cm⁴", v => { Iz = v / 1e8; ciz(); }, yuvarla);
    const slJ = sl("$J$", 100, Math.max(100000, Math.ceil(J * 2e8)), 100, J * 1e8, "cm⁴", v => { J = v / 1e8; ciz(); }, yuvarla);
    const slL = sl("$L$", 0.5, Math.max(10, Math.ceil(L * 2)), 0.1, L, "m", v => { L = v; ciz(); });
    slFi = sl("$\\varphi$ (yatay açı)", 0, 360, 1, fi, "°", v => { fi = v; ciz(); }, yuvarla);
    slPsi = sl("$\\psi$ (düşey açı)", -90, 90, 1, psi, "°", v => { psi = v; ciz(); }, yuvarla);
    aciSurukle(hd, sd, () => [fi, psi], ayar);
    const hizli = dugmeSatiri();
    [["Yatay kiriş (X)", 0, 0], ["Kolon (Y)", 0, 90], ["Z yönünde kiriş", 90, 0], ["Eğik", 30, 20]].forEach(a => hizli.appendChild(dugme(a[0], () => ayar(a[1], a[2]))));
    kap.appendChild(el("div", { class: "ks-satir" }, sGor.kok));
    kap.appendChild(el("div", { class: "ks-iki" }, kart(sd), kart(sm)));
    kap.appendChild(el("div", { class: "ks-ayar" }, slE.kok, slG.kok, slA.kok, slIy.kok, slIz.kok, slJ.kok, slL.kok, slFi.kok, slPsi.kok));
    kap.appendChild(hizli);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ks-not" }, "Yerel kipte dört parsel ayrıdır: mavi eksenel, turuncu x'y' eğilmesi (EIz), yeşil x'z' eğilmesi (EIy), kırmızı burulma. " +
      "Global kipte TᵀkT parselleri karıştırır; şeritli hücreler birden çok parçanın toplamıdır. Elemanı kolon yapınca (ψ = 90°) z' = Z kalır, y' = −X olur."));
    ciz();
  }, {
    baslik: "Uzay çerçeve elemanı: 12x12 rijitlik matrisi",
    aciklama: "Eksenel, iki eğilme ve burulma parsellerini renkli gör; yön açılarıyla λ ve global matrisin nasıl karıştığını izle.",
    varsayilan: { E: 2e8, G: 8e7, A: 0.01, Iy: 1e-4, Iz: 2e-4, J: 2e-4, L: 4, fi: 30, psi: 20 }
  });

  /* ================================================================== alıştırmalar */

  const zorlukOku = p => kenet(Math.round(Number(p && p.zorluk) || 1), 1, 3);
  const alistirma = uret => function (kok, p) {
    return E.alistirmaKur(kok, p, (rnd, pp) => uret(rnd, zorlukOku(pp), pp));
  };
  const aKS = x => Kesir.al(x);
  const aKt = x => aKS(x).tex();
  const aKm = (n, m) => Array.from({ length: n }, () => Array.from({ length: m }, () => Kesir.SIFIR));
  const aKol = dizi => "\\begin{bmatrix}" + dizi.join("\\\\") + "\\end{bmatrix}";
  const aVurgu = aile => () => aile;
  const aListe = d => d.join(",\\,");
  const BR = " \\text{ kN/m}";

  /* Yay listesinden K: spr = [[k, a, b]] (1 tabanlı düğümler) */
  function aYayMat(spr, n) {
    const K = aKm(n, n);
    spr.forEach(s => {
      const k = aKS(s[0]), a = s[1] - 1, b = s[2] - 1;
      K[a][a] = K[a][a].topla(k); K[b][b] = K[b][b].topla(k);
      K[a][b] = K[a][b].cikar(k); K[b][a] = K[b][a].cikar(k);
    });
    return new Mat(K);
  }
  const aAlt = (K, sat, sut) => new Mat(sat.map(i => sut.map(j => K.v[i][j])));
  const aSutun = dizi => new Mat(dizi.map(x => [aKS(x)]));

  /* ---- cubuk-k ---- */
  const E_ETIKET = { "2e8": "2\\cdot10^{8}", "3e7": "3\\cdot10^{7}" };
  E.kaydet("alistirma:cubuk-k", alistirma((rnd, z) => {
    let k, metin, adim1, motorG;
    if (z === 1) {
      const L = rnd.sec([1, 2, 4, 5]), k0 = rnd.sec([1000, 2000, 2500, 3000, 4000, 5000]), EA = k0 * L;
      k = aKS(k0);
      metin = "Eksenel rijitliği $EA=" + EA + "$ kN, boyu $L=" + L + "$ m olan çubuk elemanın $\\mathbf k$ matrisini yaz (birim kN/m).";
      adim1 = "k=\\frac{EA}{L}=\\frac{" + EA + "}{" + L + "}=" + k0 + BR;
      motorG = { E: String(EA), A: "1", L: String(L) };
    } else if (z === 2) {
      const Es = rnd.sec(["2e8", "3e7"]), As = rnd.sec(["0.001", "0.002", "0.004", "0.005"]), L = rnd.sec([2, 4, 5]);
      k = Kesir.oku(Es).carp(Kesir.oku(As)).bol(L);
      metin = "Elastisite modülü $E=" + E_ETIKET[Es] + "$ kN/m², kesit alanı $A=" + As + "$ m², boyu $L=" + L + "$ m olan çubuk elemanın $\\mathbf k$ matrisini yaz (birim kN/m).";
      adim1 = "k=\\frac{EA}{L}=\\frac{" + E_ETIKET[Es] + "\\cdot" + As + "}{" + L + "}=" + aKt(k) + BR;
      motorG = { E: String(Kesir.oku(Es).sayi()), A: As, L: String(L) };
    } else {
      const Eg = rnd.sec([200, 210, 30, 35]), Ac = rnd.sec([10, 12, 15, 20, 25, 40]), L = rnd.sec([2, 4, 5, 8]);
      k = new Kesir(BigInt(Eg * 100 * Ac), BigInt(L));
      metin = "Elastisite modülü $E=" + Eg + "$ GPa, kesit alanı $A=" + Ac + "$ cm², boyu $L=" + L + "$ m olan çubuk elemanın $\\mathbf k$ matrisini kN/m biriminde yaz.";
      adim1 = "E=" + Eg + "\\text{ GPa}=" + Eg + "\\cdot10^{6}\\text{ kN/m}^2,\\quad A=" + Ac + "\\text{ cm}^2=" + Ac + "\\cdot10^{-4}\\text{ m}^2\\ \\Rightarrow\\ k=\\frac{EA}{L}=\\frac{" + (Eg * 1e6) + "\\cdot" + String(Ac * 1e-4) + "}{" + L + "}=" + aKt(k) + BR;
      motorG = { E: String(Eg * 1e6), A: String(Ac * 1e-4), L: String(L) };
    }
    const kn = k.neg();
    const C = new Mat([[k, kn], [kn, k]]);
    return {
      metin, etiket: "k =", cevap: C, tolerans: "tam",
      ipucu: ["Önce rijitlik: $k=EA/L$. Birimlere dikkat: kN ve m.",
        "Matris: $\\mathbf k=k\\begin{bmatrix}1&-1\\\\-1&1\\end{bmatrix}$, yani köşegen $+k$, köşegen dışı $-k$."],
      aciklama: "$k=EA/L$ bulunur; köşegen $+k$, köşegen dışı $-k$ yazılır. Satır toplamları sıfırdır: çubuk bir bütün olarak kayarsa kuvvet doğmaz.",
      adimlar: [
        { metin: "Önce çubuğun eksenel rijitliğini hesapla.", tex: adim1 },
        { metin: "Köşegene $+k$, köşegen dışına $-k$ yaz.", tex: "\\mathbf k=\\ka{k}\\begin{bmatrix}1&-1\\\\-1&1\\end{bmatrix}=" + C.tex({ vurgu: (i, j) => (i === j ? "ka" : "kb") }) },
        { metin: "Kontrol: her satırın toplamı sıfır olmalı (rijit cisim hareketi)." }
      ],
      motor: { islem: "cubuk_eleman", girdi: motorG }
    };
  }), { baslik: "Çubuk elemanının k matrisi", aciklama: "Verilen E, A, L ile 2x2 eleman rijitlik matrisini yaz.", varsayilan: { zorluk: 1 } });

  /* ---- kafes-k ---- */
  const KAFES_Z = {
    1: [[1, 0], [0, 1]],
    2: [[1, 1], [-1, 1], [3, 4], [4, 3]],
    3: [[3, 4], [4, 3], [-3, 4], [3, -4], [5, 12], [12, 5], [-5, 12], [6, 8], [8, 6], [-4, 3]]
  };
  E.kaydet("alistirma:kafes-k", alistirma((rnd, z) => {
    const cf = rnd.sec(KAFES_Z[z]), dx = cf[0], dy = cf[1], den = dx * dx + dy * dy, Lh = Math.sqrt(den);
    const tamKare = Number.isInteger(Lh);
    let q;
    if (z === 1) q = rnd.sec([1000, 2000, 3000, 5000]);
    else if (z === 2) q = den === 2 ? rnd.sec([500, 1000, 1500]) : rnd.sec([40, 80, 120, 200]);
    else q = rnd.sec([10, 20, 40]);
    const k0 = q * den;
    const deg = Math.round(((Math.atan2(dy, dx) * 180 / Math.PI) + 360) % 360 * 100) / 100;
    let metin;
    if (z === 3) {
      const x1 = rnd.tam(0, 2), y1 = rnd.tam(0, 2);
      metin = "Kafes elemanının düğüm 1'i $(" + x1 + ",\\," + y1 + ")$ m, düğüm 2'si $(" + (x1 + dx) + ",\\," + (y1 + dy) + ")$ m noktasında; $L=" + Lh + "$ m ve $EA=" + (k0 * Lh) + "$ kN. Global eksenlerde 4x4 $\\mathbf k$ matrisini yaz (SD sırası $u_1,v_1,u_2,v_2$; kN/m).";
    } else {
      const ek = z === 2 && !(dx === 1 && dy === 1) && dx > 0 ? " ($\\tan\\alpha=" + (dy > dx ? dy + "/" + dx : dy + "/" + dx) + "$)" : "";
      metin = "Kafes elemanı $x$ ekseniyle $\\alpha=" + deg + "^\\circ$ açı yapıyor" + ek + "; $EA/L=" + k0 + "$ kN/m. Global eksenlerde 4x4 $\\mathbf k$ matrisini yaz (SD sırası $u_1,v_1,u_2,v_2$; kN/m).";
    }
    const val = (a, b) => (a === b ? (a === 0 ? dx * dx : dy * dy) : dx * dy);
    const M = aKm(4, 4).map((r, i) => r.map((_, j) => aKS(((i < 2) === (j < 2) ? 1 : -1) * q * val(i % 2, j % 2))));
    const C = new Mat(M);
    const cT = tamKare ? aKt(aKS(dx).bol(Lh)) : (dx < 0 ? "-" : "") + "\\frac{\\sqrt2}{2}";
    const sT = tamKare ? aKt(aKS(dy).bol(Lh)) : (dy < 0 ? "-" : "") + "\\frac{\\sqrt2}{2}";
    const fr = n => aKt(new Kesir(BigInt(n), BigInt(den)));
    const adimlar = [];
    if (z === 3) adimlar.push({ metin: "Boyu ve rijitliği bul.", tex: "L=\\sqrt{" + dx + "^2+" + dy + "^2}=" + Lh + "\\text{ m},\\qquad \\frac{EA}{L}=\\frac{" + (k0 * Lh) + "}{" + Lh + "}=" + k0 + BR });
    adimlar.push({ metin: "Yön kosinüslerini bul: $c=\\cos\\alpha$, $s=\\sin\\alpha$.", tex: "c=" + cT + ",\\qquad s=" + sT });
    adimlar.push({
      metin: "Üç terimi hesapla ve $EA/L$ ile çarp.",
      tex: "\\ka{c^2}=" + fr(dx * dx) + ",\\quad \\kb{cs}=" + fr(dx * dy) + ",\\quad \\kc{s^2}=" + fr(dy * dy) +
        "\\ \\Rightarrow\\ \\ka{" + (q * dx * dx) + "},\\ \\kb{" + (q * dx * dy) + "},\\ \\kc{" + (q * dy * dy) + "}"
    });
    adimlar.push({
      metin: "Deseni yerleştir: $c^2$ (köşegen, tek SD), $cs$ (karma), $s^2$ (köşegen, çift SD); karşı uçta işaret değişir.",
      tex: C.tex({ vurgu: (i, j) => ((i % 2) === (j % 2) ? ((i % 2) === 0 ? "ka" : "kc") : "kb") })
    });
    const tamAci = (dx === 1 && dy === 0) || (dx === 0 && dy === 1) || (dx === 1 && dy === 1) || (dx === -1 && dy === 1);
    return {
      metin, etiket: "k =", cevap: C, tolerans: "tam",
      ipucu: ["Önce $c=\\cos\\alpha$ ve $s=\\sin\\alpha$. " + (z === 3 ? "Koordinat farklarını $L$'ye böl." : "Bilinen üçgenlerden oku."),
        "$\\mathbf k=\\dfrac{EA}{L}\\begin{bmatrix}c^2&cs&-c^2&-cs\\\\cs&s^2&-cs&-s^2\\\\-c^2&-cs&c^2&cs\\\\-cs&-s^2&cs&s^2\\end{bmatrix}$"],
      aciklama: "Matris $\\dfrac{EA}{L}$ ile $c^2$, $cs$, $s^2$ üç terimlik desenin çarpımıdır; ikinci uç için işaretler ters döner.",
      adimlar,
      motor: tamAci ? { islem: "kafes_eleman", girdi: { E: String(k0), A: "1", L: "1", aci: String(dx === 1 && dy === 0 ? 0 : dx === 0 ? 90 : dx === 1 ? 45 : 135) } } : undefined
    };
  }), { baslik: "Açılı kafes elemanının k matrisi", aciklama: "c ve s değerlerinden 4x4 global eleman matrisini kur.", varsayilan: { zorluk: 1 } });

  /* ---- birlestir ---- */
  const BIRL_Z = {
    1: [{ n: 3, e: [[1, 2], [2, 3]] }],
    2: [{ n: 4, e: [[1, 2], [2, 3], [3, 4]] }, { n: 3, e: [[1, 3], [3, 2]] }, { n: 2, e: [[1, 2], [1, 2]] }, { n: 3, e: [[2, 1], [1, 3]] }],
    3: [{ n: 4, e: [[1, 4], [4, 2], [2, 3]] }, { n: 3, e: [[1, 2], [2, 3], [1, 3]] }, { n: 3, e: [[1, 2], [2, 3], [2, 3]] },
      { n: 4, e: [[1, 3], [2, 3], [3, 4]] }, { n: 4, e: [[3, 1], [1, 4], [4, 2]] }]
  };
  E.kaydet("alistirma:birlestir", alistirma((rnd, z) => {
    const duz = rnd.sec(BIRL_Z[z]), n = duz.n;
    const ks = duz.e.map(() => rnd.sec([500, 1000, 2000, 3000, 4000]));
    const G = duz.e.map((d, e) => {
      const k = aKS(ks[e]), A = aKm(n, n);
      const a = d[0] - 1, b = d[1] - 1;
      A[a][a] = k; A[b][b] = k; A[a][b] = k.neg(); A[b][a] = k.neg();
      return new Mat(A);
    });
    let T = G[0];
    for (let e = 1; e < G.length; e++) T = T.topla(G[e]);
    const kapsa = aKm(n, n).map(r => r.map(() => 0));
    duz.e.forEach(d => { [d[0] - 1, d[1] - 1].forEach(i => [d[0] - 1, d[1] - 1].forEach(j => { kapsa[i][j]++; })); });
    const lok = k => new Mat([[aKS(k), aKS(-k)], [aKS(-k), aKS(k)]]);
    const soruTex = "\\small\\begin{aligned}" + duz.e.map((d, e) =>
      "\\mathbf k^{(" + (e + 1) + ")}&=" + lok(ks[e]).tex({ vurgu: aVurgu(["ka", "kb", "kc"][e % 3]) }) + ",\\quad \\text{SD}\\ (" + d[0] + ",\\," + d[1] + ")").join("\\\\") + "\\end{aligned}";
    const adimlar = duz.e.map((d, e) => ({
      metin: (e + 1) + ". elemanı ($\\mathrm{SD}\\ " + d[0] + "$ ve $" + d[1] + "$) " + n + "x" + n + " matrise yerleştir: dört değer $(" + d[0] + "," + d[0] + "),(" + d[0] + "," + d[1] + "),(" + d[1] + "," + d[0] + "),(" + d[1] + "," + d[1] + ")$ hücrelerine gider.",
      tex: G[e].tex({ vurgu: (i, j, x) => (x.sifirMi() ? null : ["ka", "kb", "kc"][e % 3]) })
    }));
    adimlar.push({
      metin: "Hepsini üst üste topla. Ortak SD'nin köşegen hücresinde (ve ortak çift hücrelerde) iki katkı toplanır; bunlar ayrı renkte.",
      tex: T.tex({ vurgu: (i, j) => (kapsa[i][j] > 1 ? "ksil" : kapsa[i][j] === 1 ? "ka" : null) })
    });
    return {
      metin: "Aşağıdaki " + duz.e.length + " yay elemanı, verilen global serbestlik derecelerine (SD) bağlanıyor. Toplam " + n + " SD'li sistemin $\\mathbf K$ matrisini yaz.",
      tex: soruTex, etiket: "K =", cevap: T, tolerans: "tam",
      ipucu: ["Her eleman, kendi SD numaralarının kesiştiği hücrelere eklenir. İki yay aynı hücreye düşerse değerler toplanır.",
        "Önce $\\mathbf K$'yi sıfırla doldur; sonra eleman eleman ekle. Köşegen dışı değerin işareti $-k$'dır."],
      aciklama: "Doğrudan rijitlik yöntemi: her elemanın matrisi global matrise kendi SD numaralarıyla eklenir. Bir SD'ye bağlanan elemanların katkıları köşegende toplanır.",
      adimlar,
      motor: { islem: "birlestir", girdi: { elemanlar: duz.e.map((d, e) => ({ k: lok(ks[e]).metin(), dof: d.join(" ") })), n: String(n) } }
    };
  }), { baslik: "Eleman matrislerini birleştir", aciklama: "İki ya da üç yay elemanının K'ya eklenmesi.", varsayilan: { zorluk: 1 } });

  /* ---- sinir-kosulu ---- */
  const SINIR_Z = {
    1: [{ n: 3, s: [[1, 2], [2, 3]], f: [1] }, { n: 3, s: [[1, 2], [2, 3]], f: [3] }],
    2: [{ n: 4, s: [[1, 2], [2, 3], [3, 4]], f: [1] }, { n: 4, s: [[1, 2], [2, 3], [3, 4]], f: [4] }, { n: 3, s: [[1, 2], [2, 3]], f: [1, 3] }],
    3: [{ n: 4, s: [[1, 2], [2, 3], [3, 4]], f: [1, 4] }, { n: 4, s: [[1, 2], [2, 3], [3, 4], [2, 4]], f: [1] }, { n: 4, s: [[1, 2], [2, 3], [1, 3], [3, 4]], f: [1, 2] }]
  };
  E.kaydet("alistirma:sinir-kosulu", alistirma((rnd, z) => {
    const d = rnd.sec(SINIR_Z[z]), n = d.n, sabit = d.f.map(x => x - 1);
    const serbest = [];
    for (let i = 0; i < n; i++) if (sabit.indexOf(i) < 0) serbest.push(i);
    const spr = d.s.map(s => [rnd.sec([1000, 2000, 3000, 4000]), s[0], s[1]]);
    const K = aYayMat(spr, n);
    const yuk = serbest.map(() => rnd.sec(z === 1 ? [0, 10, 20, 40] : [0, 10, 20, 30, 50]));
    if (yuk.every(x => x === 0)) yuk[yuk.length - 1] = 20;
    const Kff = aAlt(K, serbest, serbest), Ff = aSutun(yuk);
    const U = Kff.coz(Ff);
    const Fdizi = [], Ftam = [];
    for (let i = 0; i < n; i++) {
      const j = serbest.indexOf(i);
      Fdizi.push(j < 0 ? "R_{" + (i + 1) + "}" : String(yuk[j]));
      Ftam.push(j < 0 ? "0" : String(yuk[j]));
    }
    const Kt = K.tex({ vurgu: aVurgu("ka") });
    const sabitMetin = d.f.length === 1 ? "SD " + d.f[0] + " tutulu" : "SD " + d.f.join(" ve ") + " tutulu";
    const donusum = Array.from({ length: n }, (_, i) => sabit.indexOf(i) >= 0 ? "0" : "u_{" + (i + 1) + "}");
    return {
      metin: "Yay sisteminin rijitlik matrisi ve yük vektörü verilmiş (K kN/m, F kN). " + sabitMetin + " ($u=0$); $R$ tepkilerdir. Serbest SD'lerin yer değiştirmelerini bul (m).",
      tex: "\\begin{aligned}\\mathbf K&=" + Kt + "\\\\ \\mathbf K\\mathbf u&=\\mathbf F:\\quad \\mathbf u=" + aKol(donusum) + ",\\ \\mathbf F=" + aKol(Fdizi) + "\\end{aligned}",
      alanlar: serbest.map(i => "$u_{" + (i + 1) + "}$ [m]"), cevap: U, tolerans: "tam",
      ipucu: ["Tutulu SD'nin yer değiştirmesi sıfır: ilgili satır ve sütun hesaba girmez (tepki sonra bulunur).",
        "Kalan küçük sistemi $\\mathbf K_{ff}\\mathbf u_f=\\mathbf F_f$ çöz."],
      aciklama: "Tutulu SD'lerin satır ve sütunları silinir; kalan $\\mathbf K_{ff}\\mathbf u_f=\\mathbf F_f$ sistemi çözülür.",
      adimlar: [
        { metin: "Tutulu SD'lerin satır ve sütunlarını çıkar (ayrı renkli hücreler); geriye serbest SD'ler kalır.", tex: K.tex({ vurgu: (i, j) => (sabit.indexOf(i) >= 0 || sabit.indexOf(j) >= 0 ? "ksil" : "ka") }) },
        { metin: "Küçültülmüş sistem $\\mathbf K_{ff}\\mathbf u_f=\\mathbf F_f$.", tex: Kff.tex({ vurgu: aVurgu("ka") }) + aKol(serbest.map(i => "u_{" + (i + 1) + "}")) + "=" + Ff.tex({ vurgu: aVurgu("kb") }) },
        { metin: "Çöz (Gauss yok etme ya da ters matris).", tex: "\\mathbf u_f=\\mathbf K_{ff}^{-1}\\mathbf F_f=" + U.tex({ vurgu: aVurgu("kc") }) + "\\text{ m}" }
      ],
      motor: { islem: "sinir_kosulu", girdi: { K: K.metin(), F: Ftam.join("; "), sabit: d.f.join(" "), bilinmeyen: "u" } }
    };
  }), { baslik: "Sınır koşulunu uygula", aciklama: "Tutulu serbestlik derecelerini at, kalan sistemi çöz.", varsayilan: { zorluk: 1 } });

  /* ---- yay-seri ---- */
  function yayZincirSekil(ks, sabitSag, yuk) { // yuk: {dugum (1 tabanlı), P}
    return function () {
      stil();
      const m = ks.length, W = 440, H = 150, X0 = 40, X1 = 392, Y = 62;
      const s = sv(W, H, "Seri yaylardan oluşan sistem şeması");
      const dx = (X1 - X0) / m;
      s.appendChild(duvarCiz(X0, Y - 28, Y + 28));
      if (sabitSag) s.appendChild(svg("g", { transform: "translate(" + (2 * X1) + " 0) scale(-1 1)" }, duvarCiz(X1, Y - 28, Y + 28)));
      for (let i = 0; i < m; i++) {
        const xa = X0 + i * dx, xb = xa + dx;
        s.appendChild(yol(yayYolu(xa, Y, xb, Y, 6, 9), { renk: aileOf(i), kal: 2.2 }));
        s.appendChild(yaziH((xa + xb) / 2, Y - 20, "k" + (i + 1) + " = " + ks[i], { renk: aileOf(i), boyut: 11, kalin: true }));
      }
      for (let i = 0; i <= m; i++) {
        const x = X0 + i * dx;
        s.appendChild(daire(x, Y, 5.5, { dolguHam: "var(--kart,#fff)", renk: "metin", kal: 2 }));
        s.appendChild(yaziH(x, Y + 22, String(i + 1), { renk: "soluk", boyut: 11, kalin: true }));
      }
      const xy = X0 + (yuk.dugum - 1) * dx, sag = yuk.dugum < m + 1 || !sabitSag;
      void sag;
      s.appendChild(cizgi(xy, Y + 6, xy, Y + 42, { renk: "sil", kal: 1, kesik: true }));
      s.appendChild(ok(xy, Y + 42, xy + 50, Y + 42, { renk: "sil", kalinlik: 2.8, bas: 9 }));
      s.appendChild(yaziH(xy + 54, Y + 46, "P = " + yuk.P + " kN", { renk: "sil", boyut: 11, kalin: true, hiza: "sol" }));
      return s;
    };
  }
  E.kaydet("alistirma:yay-seri", alistirma((rnd, z) => {
    const m = z === 1 ? 2 : 3, n = m + 1;
    const ks = Array.from({ length: m }, () => rnd.sec([1000, 2000, 2500, 4000, 5000]));
    const P = rnd.sec([10, 20, 50, 100]);
    const iki = z === 3;
    const sabit = iki ? [0, n - 1] : [0];
    const yukDugum = iki ? rnd.sec([2, 3]) : n;
    const K = aYayMat(ks.map((k, i) => [k, i + 1, i + 2]), n);
    const serbest = [];
    for (let i = 0; i < n; i++) if (sabit.indexOf(i) < 0) serbest.push(i);
    const F = serbest.map(i => (i === yukDugum - 1 ? P : 0));
    const Kff = aAlt(K, serbest, serbest), Ff = aSutun(F);
    const Uf = Kff.coz(Ff);
    const u = aKm(n, 1).map(r => r[0]);
    serbest.forEach((i, j) => { u[i] = Uf.v[j][0]; });
    const R = sabit.map(s => K.v[s].reduce((a, kij, j) => a.topla(kij.carp(u[j])), Kesir.SIFIR));
    const cevapDizi = serbest.map(i => u[i]).concat(R);
    const alanlar = serbest.map(i => "$u_{" + (i + 1) + "}$ [m]").concat(sabit.map(s => "$R_{" + (s + 1) + "}$ [kN]"));
    const adimlar = [];
    if (!iki) {
      adimlar.push({ metin: "Seride her yaydan aynı kuvvet geçer: dış yük her yaya iletilir.", tex: "N_1=N_2" + (m > 2 ? "=N_3" : "") + "=P=" + P + "\\text{ kN}" });
      adimlar.push({
        metin: "Her yayın uzaması $\\delta_i=P/k_i$.",
        tex: "\\begin{aligned}" + ks.map((k, i) => MAK[i % 3] + "{\\delta_" + (i + 1) + "}&=\\frac{" + P + "}{" + k + "}=" + aKt(aKS(P).bol(k)) + "\\text{ m}").join("\\\\") + "\\end{aligned}"
      });
      adimlar.push({
        metin: "Yer değiştirmeler uzamaların birikimidir ($u_1=0$).",
        tex: "\\begin{aligned}" + Array.from({ length: m }, (_, i) => "u_{" + (i + 2) + "}&=" + (i === 0 ? "\\delta_1" : "u_" + (i + 1) + "+\\delta_" + (i + 1)) + "=" + aKt(u[i + 1])).join("\\\\") + "\\end{aligned}"
      });
      adimlar.push({ metin: "Tepki: denge $R_1+P=0$.", tex: "R_1=-P=" + aKt(R[0]) + "\\text{ kN}" });
    } else {
      adimlar.push({ metin: "Her iki uç tutulu: yalnız $u_2$ ve $u_3$ bilinmiyor. Tutulu SD'leri atarak $\\mathbf K_{ff}$'yi kur.", tex: Kff.tex({ vurgu: aVurgu("ka") }) + aKol(["u_2", "u_3"]) + "=" + Ff.tex({ vurgu: aVurgu("kb") }) });
      adimlar.push({ metin: "Çöz.", tex: "\\mathbf u_f=" + Uf.tex({ vurgu: aVurgu("kc") }) + "\\text{ m}" });
      adimlar.push({ metin: "Tepkiler: tutulu satırlar. $R_1=-k_1u_2$, $R_4=-k_3u_3$.", tex: "R_1=" + aKt(R[0]) + ",\\quad R_4=" + aKt(R[1]) + "\\text{ kN}" });
      adimlar.push({ metin: "Kontrol: tepkiler dış yükü dengelemeli.", tex: "R_1+R_4+P=" + aKt(R[0].topla(R[1]).topla(P)) });
    }
    return {
      metin: iki
        ? "Üç yay seri bağlı; iki uç da duvara bağlı. " + yukDugum + ". düğümde $P=" + P + "$ kN yük var (pozitif yön sağa). Serbest düğümlerin yer değiştirmelerini ve iki tepkiyi bul."
        : "Sol ucu duvara bağlı " + m + " yay seri bağlı; son düğümde sağa doğru $P=" + P + "$ kN çekme kuvveti var. Düğümlerin yer değiştirmelerini ve sol tepkiyi bul (pozitif yön sağa, birimler kN ve m).",
      sekil: yayZincirSekil(ks, iki, { dugum: yukDugum, P }),
      alanlar, cevap: cevapDizi, tolerans: "tam",
      ipucu: iki
        ? ["Bilinmeyenler $u_2,u_3$: $\\mathbf K_{ff}=\\begin{bmatrix}k_1+k_2&-k_2\\\\-k_2&k_2+k_3\\end{bmatrix}$.", "Tepki $R_1=-k_1u_2$, $R_4=-k_3u_3$."]
        : ["Seri yaylarda her yaya aynı kuvvet ($P$) iner; uzama $\\delta=P/k$.", "Yer değiştirmeler uzamaların toplamıdır; tepki dış yükü dengeler: $R_1=-P$."],
      aciklama: iki ? "Tutulu uçlar çıkarılınca 2x2 sistem kalır; tepkiler tutulu satırlardan bulunur ve yükü dengeler." : "Seri yayda her yaya aynı kuvvet iner; uzamalar toplanır. Tepki, dış yükü dengeler.",
      adimlar,
      motor: { islem: "sinir_kosulu", girdi: { K: K.metin(), F: Array.from({ length: n }, (_, i) => (i === yukDugum - 1 ? String(P) : "0")).join("; "), sabit: sabit.map(x => x + 1).join(" "), bilinmeyen: "u" } }
    };
  }), { baslik: "Seri yaylar", aciklama: "Seri yay zincirinde düğüm yer değiştirmeleri ve tepki.", varsayilan: { zorluk: 1 } });
})();
