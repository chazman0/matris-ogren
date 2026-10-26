/* Matris Öğren - Sonlu eleman sayfası (#se).
   Motor (sonlu_eleman.py) web_kopru.py üzerinden "se_ornekler", "se_ornek" ve "se_coz" işlemleriyle çağrılır.
   Bu dosya yalnız arayüzdür: model düzenleme (tablolar + JSON), şekiller (SVG; 3B modeller aksonometrik izdüşümle),
   sonuç tabloları ve anlatım. app.js'ten window.MatrisApp ile yalnız motorIstegi, anlatimDersCiz, semaOlaylariBagla
   ve kacis kullanılır. */
(function () {
  "use strict";
  const A = window.MatrisApp;
  const kok = document.getElementById("se-kok");
  if (!A || !kok) return;
  const kacis = A.kacis;

  // ---------- Model türleri ----------
  const TIPLER = {
    yay:       { ad: "Yay (1B)",            oz: ["k"],                            mes: ["ux"],                                   yuk: ["Fx"],                                     xy: false, z: false, q: false, qz: false, yay: ["kx"],                                     zemin: false },
    cubuk:     { ad: "Eksenel çubuk (1B)",  oz: ["E", "A"],                       mes: ["ux"],                                   yuk: ["Fx"],                                     xy: false, z: false, q: false, qz: false, yay: ["kx"],                                     zemin: false },
    kafes:     { ad: "Kafes (2B)",          oz: ["E", "A"],                       mes: ["ux", "uy"],                             yuk: ["Fx", "Fy"],                               xy: true,  z: false, q: false, qz: false, yay: ["kx", "ky"],                               zemin: false },
    kiris:     { ad: "Kiriş",               oz: ["E", "I"],                       mes: ["uy", "rz"],                             yuk: ["Fy", "M"],                                xy: false, z: false, q: true,  qz: false, yay: ["ky", "kr"],                               zemin: true },
    cerceve:   { ad: "Çerçeve (2B)",        oz: ["E", "A", "I"],                  mes: ["ux", "uy", "rz"],                       yuk: ["Fx", "Fy", "M"],                          xy: true,  z: false, q: true,  qz: false, yay: ["kx", "ky", "kr"],                         zemin: true },
    kafes3b:   { ad: "Uzay kafes (3B)",     oz: ["E", "A"],                       mes: ["ux", "uy", "uz"],                       yuk: ["Fx", "Fy", "Fz"],                         xy: true,  z: true,  q: false, qz: false, yay: ["kx", "ky", "kz"],                         zemin: false },
    cerceve3b: { ad: "Uzay çerçeve (3B)",   oz: ["E", "G", "A", "Iy", "Iz", "J"], mes: ["ux", "uy", "uz", "rx", "ry", "rz"],     yuk: ["Fx", "Fy", "Fz", "Mx", "My", "Mz"],       xy: true,  z: true,  q: true,  qz: true,  yay: ["kx", "ky", "kz", "krx", "kry", "krz"],   zemin: false },
  };
  const TIP_SIRA = ["yay", "cubuk", "kafes", "kiris", "cerceve", "kafes3b", "cerceve3b"];
  const OZ_ETIKET = { k: "k (kN/m)", E: "E (kN/m²)", G: "G (kN/m²)", A: "A (m²)", I: "I (m⁴)", Iy: "Iy (m⁴)", Iz: "Iz (m⁴)", J: "J (m⁴)", zemin: "zemin kₛ (kN/m²)" };
  const OZ_VARSAYILAN = { k: "1000", E: "200e6", G: "80e6", A: "0.01", I: "1e-4", Iy: "1e-4", Iz: "1e-4", J: "2e-4" };
  const MES_ETIKET = { ux: "ux", uy: "uy", uz: "uz", rx: "rx", ry: "ry", rz: "rz" };
  const YUK_ETIKET = { Fx: "Fx (kN)", Fy: "Fy (kN)", Fz: "Fz (kN)", M: "M (kN·m)", Mx: "Mx (kN·m)", My: "My (kN·m)", Mz: "Mz (kN·m)" };
  const YAY_ETIKET = { kx: "kx (kN/m)", ky: "ky (kN/m)", kz: "kz (kN/m)", kr: "kr (kN·m/rad)", krx: "krx (kN·m/rad)", kry: "kry (kN·m/rad)", krz: "krz (kN·m/rad)" };
  const COK_ETIKET = { ux: "ux (m)", uy: "uy (m)", uz: "uz (m)", rx: "rx (rad)", ry: "ry (rad)", rz: "rz (rad)" };
  const YAY_SD = { kx: 0, ky: 1, kz: 2, kr: 2, krx: 3, kry: 4, krz: 5 };   // yay anahtarı -> yük bileşeni sırası (tip tablosundan)

  // ---------- Durum ----------
  let S = bosModel("kafes");     // düzenlenen model; alanlar yazıldığı gibi (metin) tutulur
  let SON = null;                // son çözüm: { y, veri }
  let cozuluyor = false;
  let basladi = false;
  let sonGenislik = 0;
  let zamanci = 0;
  let cizimGenislik = 600;       // o an çizilen SVG'nin genişliği (etiketleri kenarda tutmak için)
  let diyagramTuru = "M";
  let olcekYuzde = 100;
  let ornekler = [];
  const bakis = { fi: -32, psi: 22 };   // 3B bakış: Y etrafında dönme ve yukarıdan eğim (derece)
  const ref = {};

  function bosModel(tip) {
    return { tip: tip, baslik: "", aciklama: "", birim: { kuvvet: "kN", uzunluk: "m" }, dugumler: [], elemanlar: [], mesnetler: [], yukler: [], yayili: [], yaylar: [], cokmeler: [] };
  }

  // ---------- Küçük yardımcılar ----------
  const SAYI_RE = /^[+-]?(\d+([.,]\d*)?|[.,]\d+)([eE][+-]?\d+)?$/;
  function str(v) { return v == null ? "" : String(v); }
  function sayiOku(s) {
    if (typeof s === "number") return isFinite(s) ? s : null;
    const t = str(s).trim();
    if (!SAYI_RE.test(t)) return null;
    const n = parseFloat(t.replace(",", "."));
    return isFinite(n) ? n : null;
  }
  function tamSayi(s) {
    const t = str(s).trim();
    return /^[+-]?\d+$/.test(t) ? parseInt(t, 10) : null;
  }
  function bos(s) { return str(s).trim() === ""; }
  function fmt(v) {
    if (typeof v !== "number") return v == null ? "—" : str(v);
    if (!isFinite(v)) return "—";
    const a = Math.abs(v);
    if (a < 1e-9) return "0";
    let t;
    if (a >= 1e6 || a < 1e-3) t = v.toExponential(3).replace("e+", "e");
    else t = String(parseFloat(v.toPrecision(5)));
    return t.replace(".", ",").replace("-", "−");
  }
  function r1(v) { return Math.round(v * 10) / 10; }
  function pt(x, y) { return r1(x) + "," + r1(y); }
  function metinSvg(x, y, t, sinif, hiza) {
    return '<text x="' + r1(x) + '" y="' + r1(y) + '" class="' + sinif + '"' + (hiza ? ' text-anchor="' + hiza + '"' : "") + ">" + kacis(t) + "</text>";
  }
  function birimler(bm) {
    bm = bm || S.birim;
    return { f: (bm && bm.kuvvet) || "kN", l: (bm && bm.uzunluk) || "m" };
  }
  function genislik(el) {
    return Math.max(260, Math.floor(el.clientWidth) || 600);
  }
  function ucBoyut(tip) { return !!(TIPLER[tip] && TIPLER[tip].z); }

  // ---------- 3B izdüşüm (aksonometrik): dünya (x, y, z) -> çizim düzlemi (u, v) ----------
  function izdusum(x, y, z) {
    const f = bakis.fi * Math.PI / 180, p = bakis.psi * Math.PI / 180;
    const u = x * Math.cos(f) + z * Math.sin(f);
    const derin = -x * Math.sin(f) + z * Math.cos(f);      // izleyiciye doğru
    return [u, y * Math.cos(p) - derin * Math.sin(p)];
  }
  function duzlem(tip, x, y, z) { return ucBoyut(tip) ? izdusum(x, y, z || 0) : [x, y]; }
  function yon3(tip, v) {
    // dünya yön vektörü -> ekran birim vektörü (y aşağı)
    let dx, dy;
    if (ucBoyut(tip)) {
      const a = izdusum(0, 0, 0), b = izdusum(v[0], v[1], v[2] || 0);
      dx = b[0] - a[0]; dy = -(b[1] - a[1]);
    } else { dx = v[0]; dy = -v[1]; }
    const L = Math.hypot(dx, dy);
    return L > 1e-9 ? [dx / L, dy / L] : [0, -1];
  }
  function yerelEksen3(dx, dy, dz) {
    // Uzay çerçeve yerel eksenleri (satırlar x', y', z'): y' düşey düzlemde yukarı; düşey elemanda z' = Z (motorla aynı kural)
    const L = Math.hypot(dx, dy, dz) || 1, cx = dx / L, cy = dy / L, cz = dz / L;
    const D = Math.hypot(cx, cz);
    if (D < 1e-9) return [[0, cy, 0], [-cy, 0, 0], [0, 0, 1]];
    return [[cx, cy, cz], [-cx * cy / D, D, -cy * cz / D], [-cz / D, 0, cx / D]];
  }

  // ---------- Modelden geometri ----------
  function geometri(m) {
    const tp = TIPLER[m.tip];
    const d = {};
    m.dugumler.forEach(function (n) {
      const no = tamSayi(n.no), x = sayiOku(n.x), y = tp.xy ? sayiOku(n.y) : 0, z = tp.z ? sayiOku(n.z) : 0;
      if (no != null && x != null && y != null && z != null) d[no] = { no: no, x: x, y: y, z: z };
    });
    const e = [];
    m.elemanlar.forEach(function (el, k) {
      const a = d[tamSayi(el.i)], b = d[tamSayi(el.j)];
      if (a && b && a !== b && (a.x !== b.x || a.y !== b.y || a.z !== b.z)) {
        const zemin = tp.zemin && !bos(el.zemin) && sayiOku(el.zemin) !== 0 ? str(el.zemin).trim() : null;
        e.push({ no: tamSayi(el.no) != null ? tamSayi(el.no) : k + 1, a: a, b: b, zemin: zemin });
      }
    });
    return { d: d, e: e };
  }

  // ---------- Dünya -> ekran dönüşümü (1 birim = 1 px; SVG genişliği kadar viewBox) ----------
  function donusum(pts, W, o) {
    o = o || {};
    const pl = o.pl != null ? o.pl : 44, pu = o.pu != null ? o.pu : 54, pa = o.pa != null ? o.pa : 66;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    pts.forEach(function (p) {
      if (p[0] < x0) x0 = p[0]; if (p[0] > x1) x1 = p[0];
      if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1];
    });
    if (!isFinite(x0)) { x0 = 0; x1 = 1; y0 = 0; y1 = 0; }
    const dx = x1 - x0, dy = y1 - y0;
    const aw = Math.max(80, W - 2 * pl);
    const hMax = o.hMax || (W < 520 ? 320 : 380);
    let s;
    if (dx < 1e-9 && dy < 1e-9) s = 1;
    else if (dx < 1e-9) s = (hMax - pu - pa) / dy;
    else if (dy < 1e-9) s = aw / dx;
    else s = Math.min(aw / dx, (hMax - pu - pa) / dy);
    const ic = dy * s;
    const H = Math.max(o.minH || 0, pu + pa + ic + 8);
    const oy = pu + (H - pu - pa - ic) / 2;
    const ox = pl + (aw - dx * s) / 2;
    return { s: s, W: W, H: H, x: function (v) { return ox + (v - x0) * s; }, y: function (v) { return oy + (y1 - v) * s; } };
  }
  function svgSar(T, icerik, etiket) {
    cizimGenislik = T.W;
    return '<svg class="se-svg" viewBox="0 0 ' + r1(T.W) + " " + r1(T.H) + '" role="img" aria-label="' + kacis(etiket) + '" preserveAspectRatio="xMidYMid meet">' +
      "<title>" + kacis(etiket) + "</title>" + icerik + "</svg>";
  }
  function okBasi(tx, ty, dx, dy, sinif) {
    const L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, px = -uy, py = ux;
    return '<polygon class="' + sinif + '" points="' + pt(tx, ty) + " " + pt(tx - ux * 9 + px * 3.8, ty - uy * 9 + py * 3.8) + " " + pt(tx - ux * 9 - px * 3.8, ty - uy * 9 - py * 3.8) + '"/>';
  }
  function eksenTakimi(tip, T) {
    // 3B çizimlerde sol altta küçük X-Y-Z eksen takımı
    if (!ucBoyut(tip)) return "";
    const ox = 26, oy = T.H - 22;
    let s = "";
    [["X", [1, 0, 0]], ["Y", [0, 1, 0]], ["Z", [0, 0, 1]]].forEach(function (e) {
      const w = yon3(tip, e[1]);
      s += '<path class="se-eksen" d="M' + pt(ox, oy) + " L" + pt(ox + w[0] * 22, oy + w[1] * 22) + '"/>' + okBasi(ox + w[0] * 24, oy + w[1] * 24, w[0], w[1], "se-eksen-o") +
        metinSvg(ox + w[0] * 33, oy + w[1] * 33 + 4, e[0], "se-eksen-t", "middle");
    });
    return s;
  }

  // ---------- Mesnet sembolleri ----------
  function mesnetTuru(tip, m) {
    const ux = !!m.ux, uy = !!m.uy, uz = !!m.uz, rx = !!m.rx, ry = !!m.ry, rz = !!m.rz;
    if (tip === "yay" || tip === "cubuk") return ux ? "duvar" : null;
    if (tip === "kiris") return uy && rz ? "duvar" : uy ? "sabit" : rz ? "kare" : null;
    if (tip === "kafes") return ux && uy ? "sabit" : (ux || uy) ? "makara" : null;
    if (tip === "kafes3b") return ux && uy && uz ? "sabit" : (ux || uy || uz) ? "makara" : null;
    if (tip === "cerceve3b") {
      if (ux && uy && uz && rx && ry && rz) return "duvar";
      if (ux && uy && uz) return "sabit";
      if (ux || uy || uz) return "makara";
      return (rx || ry || rz) ? "kare" : null;
    }
    if (ux && uy && rz) return "duvar";
    if (ux && uy) return "sabit";
    if (ux || uy) return "makara";
    return rz ? "kare" : null;
  }
  function mesnetCiz(px, py, tur, a) {
    const p = [-a[1], a[0]];
    const q = function (u, v) { return pt(px + a[0] * u + p[0] * v, py + a[1] * u + p[1] * v); };
    const zemin = function (u, h) {
      let s = '<path class="se-mes-c" d="M' + q(u, -h) + " L" + q(u, h) + '"/>';
      for (let v = -h + 3; v <= h; v += 7) s += '<path class="se-mes-t" d="M' + q(u, v) + " L" + q(u + 7, v - 5) + '"/>';
      return s;
    };
    if (tur === "duvar") return zemin(0, 16);
    if (tur === "sabit") return '<path class="se-mes-f" d="M' + q(0, 0) + " L" + q(16, -11) + " L" + q(16, 11) + ' Z"/>' + zemin(16, 16);
    if (tur === "makara") {
      const c1 = [px + a[0] * 15.5 + p[0] * 6, py + a[1] * 15.5 + p[1] * 6], c2 = [px + a[0] * 15.5 - p[0] * 6, py + a[1] * 15.5 - p[1] * 6];
      return '<path class="se-mes-f" d="M' + q(0, 0) + " L" + q(12, -10) + " L" + q(12, 10) + ' Z"/>' +
        '<circle class="se-mes-f" cx="' + r1(c1[0]) + '" cy="' + r1(c1[1]) + '" r="3.5"/><circle class="se-mes-f" cx="' + r1(c2[0]) + '" cy="' + r1(c2[1]) + '" r="3.5"/>' + zemin(19.5, 16);
    }
    return '<rect class="se-mes-f" x="' + r1(px - 6) + '" y="' + r1(py - 6) + '" width="12" height="12"/>';
  }
  function yonSec(tip, m, tur, ortalama) {
    // mesnedin eleman tarafının tersine bakan birim vektör (ekran koordinatı)
    const uzun = Math.hypot(ortalama[0], ortalama[1]);
    let a = uzun > 0.35 ? [-ortalama[0] / uzun, -ortalama[1] / uzun] : [0, 1];
    if (ucBoyut(tip)) return [0, ortalama[1] > 0.35 ? -1 : 1];
    if (tur === "makara" || (tip === "kafes" && tur === "sabit")) {
      if (tur === "makara" && !(tip === "kiris")) {
        if (m.uy && !m.ux) a = [0, ortalama[1] > 0.35 ? -1 : 1];
        else if (m.ux && !m.uy) a = [ortalama[0] > 0.35 ? -1 : 1, 0];
      }
    }
    if (tip === "kiris" && tur !== "duvar") a = [0, 1];
    if (Math.abs(a[0]) > 0.94) a = [a[0] > 0 ? 1 : -1, 0];
    else if (Math.abs(a[1]) > 0.94) a = [0, a[1] > 0 ? 1 : -1];
    return a;
  }
  function mesnetleriCiz(tip, mesnetler, N, bagli, soluk) {
    let s = "";
    mesnetler.forEach(function (m) {
      const no = tamSayi(m.dugum), p = N[no];
      if (!p) return;
      const tur = mesnetTuru(tip, m);
      if (!tur) return;
      const v = bagli[no] || [];
      const ort = v.length ? [v.reduce(function (t, x) { return t + x[0]; }, 0) / v.length, v.reduce(function (t, x) { return t + x[1]; }, 0) / v.length] : [0, 0];
      const parca = mesnetCiz(p[0], p[1], tur, yonSec(tip, m, tur, ort));
      s += soluk ? '<g class="se-soluk">' + parca + "</g>" : parca;
    });
    return s;
  }
  function bagliYonler(kenarlar) {
    // kenarlar: [[noA, pA, noB, pB]] -> her düğümden komşularına ekran birim vektörleri
    const bagli = {};
    kenarlar.forEach(function (k) {
      const p = k[1], q = k[3], L = Math.hypot(q[0] - p[0], q[1] - p[1]) || 1;
      (bagli[k[0]] = bagli[k[0]] || []).push([(q[0] - p[0]) / L, (q[1] - p[1]) / L]);
      (bagli[k[2]] = bagli[k[2]] || []).push([-(q[0] - p[0]) / L, -(q[1] - p[1]) / L]);
    });
    return bagli;
  }

  // ---------- Yük, yay ve zemin sembolleri ----------
  function yukOku(s) {
    const t = str(s).trim();
    if (t === "") return null;
    const n = sayiOku(t);
    if (n != null) return n === 0 ? null : { isaret: n > 0 ? 1 : -1, etiket: fmt(Math.abs(n)) };
    return { isaret: t.charAt(0) === "-" ? -1 : 1, etiket: t.replace(/^[+-]\s*/, "") };
  }
  function kuvvetOku(px, py, dx, dy, etiket, sinifC, sinifO, sinifT) {
    sinifC = sinifC || "se-yuk-c"; sinifO = sinifO || "se-yuk-o"; sinifT = sinifT || "se-yuk-t";
    const L = 36, t0 = [px - dx * (L + 6), py - dy * (L + 6)], t1 = [px - dx * 6, py - dy * 6];
    let s = '<path class="' + sinifC + '" d="M' + pt(t0[0], t0[1]) + " L" + pt(t1[0] - dx * 2, t1[1] - dy * 2) + '"/>' + okBasi(t1[0], t1[1], dx, dy, sinifO);
    if (Math.abs(dx) > Math.abs(dy)) {
      const w = 6.6 * etiket.length, orta = (t0[0] + t1[0]) / 2;
      s += metinSvg(Math.max(4 + w / 2, Math.min(cizimGenislik - 4 - w / 2, orta)), t0[1] - 8, etiket, "se-etiket " + sinifT, "middle");
    } else s += metinSvg(Math.max(4 + 3.3 * etiket.length, Math.min(cizimGenislik - 4 - 3.3 * etiket.length, t0[0])), dy > 0 ? t0[1] - 6 : t0[1] + 14, etiket, "se-etiket " + sinifT, "middle");
    return s;
  }
  function momentOku(px, py, isaret, etiket, kayma) {
    const r = 17, d2r = Math.PI / 180;
    const nok = function (aci) { return [px + r * Math.cos(aci * d2r), py - r * Math.sin(aci * d2r)]; };
    const ccw = isaret > 0;
    const bas = ccw ? nok(-30) : nok(210), son = ccw ? nok(205) : nok(-25);
    const teg = ccw ? [-Math.sin(205 * d2r), -Math.cos(205 * d2r)] : [Math.sin(-25 * d2r), Math.cos(-25 * d2r)];
    const yol = "M" + pt(bas[0], bas[1]) + " A" + r + "," + r + " 0 1," + (ccw ? 0 : 1) + " " + pt(son[0], son[1]);
    return '<path class="se-yuk-c" d="' + yol + '"/>' + okBasi(son[0] + teg[0] * 4, son[1] + teg[1] * 4, teg[0], teg[1], "se-yuk-o") +
      metinSvg(px, py - r - 7 - (kayma || 0), etiket, "se-etiket se-yuk-t", "middle");
  }
  function yayiliOku(a, b, n, q, etiket, birim) {
    // a, b: ekran noktaları; n: yükün pozitif yönü (ekran birim vektörü); q > 0 n yönünde
    const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
    const fx = n[0] * q.isaret, fy = n[1] * q.isaret;   // kuvvet yönü
    const adet = Math.max(3, Math.min(14, Math.floor(L / 24)));
    const h = 28;
    let s = "";
    const bas = [a[0] - fx * h, a[1] - fy * h], son = [b[0] - fx * h, b[1] - fy * h];
    s += '<path class="se-yuk-c" d="M' + pt(bas[0], bas[1]) + " L" + pt(son[0], son[1]) + '"/>';
    for (let k = 0; k < adet; k++) {
      const t = adet === 1 ? 0.5 : k / (adet - 1);
      const px = a[0] + dx * t, py = a[1] + dy * t;
      s += '<path class="se-yuk-c" d="M' + pt(px - fx * h, py - fy * h) + " L" + pt(px - fx * 2, py - fy * 2) + '"/>' + okBasi(px, py, fx, fy, "se-yuk-o");
    }
    const etq = etiket + " = " + (q.isaret < 0 ? "−" : "") + q.etiket + (birim ? " " + birim : ""), yar = 3.3 * etq.length;
    const mx = Math.max(4 + yar, Math.min(cizimGenislik - 4 - yar, (bas[0] + son[0]) / 2 - fx * 8)), my = (bas[1] + son[1]) / 2 - fy * 8;
    s += metinSvg(mx, my + (Math.abs(fy) > 0.5 ? (fy > 0 ? -1 : 11) : 4), etq, "se-etiket se-yuk-t", "middle");
    return s;
  }
  function zikzak(a, b, gen) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, px = -uy, py = ux;
    const kol = Math.min(10, L * 0.2), hl = L - 2 * kol, z = Math.max(2, Math.min(7, Math.floor(hl / 8)));
    let d = "M" + pt(a[0], a[1]) + " L" + pt(a[0] + ux * kol, a[1] + uy * kol);
    for (let k = 0; k < 2 * z; k++) {
      const t = (k + 0.5) / (2 * z), o = (k % 2 === 0 ? 1 : -1) * gen;
      d += " L" + pt(a[0] + ux * (kol + hl * t) + px * o, a[1] + uy * (kol + hl * t) + py * o);
    }
    return d + " L" + pt(b[0] - ux * kol, b[1] - uy * kol) + " L" + pt(b[0], b[1]);
  }
  function yayCiz(tip, px, py, anahtar, deger, komsu) {
    // Elastik mesnet: öteleme yayı düğümden dışarı zikzak; dönme yayı küçük sarmal
    const et = anahtar + " = " + fmt(sayiOku(deger) != null ? sayiOku(deger) : deger);
    if (anahtar.charAt(1) === "r") {
      const r = 12;
      let d = "";
      for (let k = 0; k <= 24; k++) {
        const t = k / 24, aci = t * Math.PI * 1.7 + Math.PI * 0.4, rr = r * (0.35 + 0.65 * t);
        d += (k ? " L" : "M") + pt(px + rr * Math.cos(aci), py - rr * Math.sin(aci));
      }
      return '<path class="se-yay-c" d="' + d + '"/>' + metinSvg(px + 16, py + 22, et, "se-etiket se-yay-t", "start");
    }
    let w = anahtar === "kx" ? yon3(tip, [1, 0, 0]) : anahtar === "ky" ? yon3(tip, [0, -1, 0]) : yon3(tip, [0, 0, 1]);
    if (komsu.some(function (m) { return w[0] * m[0] + w[1] * m[1] > 0.6; })) w = [-w[0], -w[1]];
    const uc = [px + w[0] * 42, py + w[1] * 42], p = [-w[1], w[0]];
    let s = '<path class="se-yay-c" d="' + zikzak([px + w[0] * 5, py + w[1] * 5], uc, 6) + '"/>';
    s += '<path class="se-mes-c" d="M' + pt(uc[0] - p[0] * 9, uc[1] - p[1] * 9) + " L" + pt(uc[0] + p[0] * 9, uc[1] + p[1] * 9) + '"/>';
    const hiza = w[0] > 0.5 ? "start" : (w[0] < -0.5 ? "end" : "middle");
    s += metinSvg(uc[0] + w[0] * 10 + p[0] * 12, uc[1] + w[1] * 10 + p[1] * 12 + 4, et, "se-etiket se-yay-t", hiza);
    return s;
  }
  function zeminCiz(a, b, n, etiket) {
    // Winkler zemini: elemanın -y' tarafında küçük yaylar ve taralı zemin çizgisi
    const alt = [-n[0], -n[1]], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
    const adet = Math.max(2, Math.round(L / 30));
    let s = "";
    for (let k = 0; k < adet; k++) {
      const t = (k + 0.5) / adet, px = a[0] + dx * t, py = a[1] + dy * t;
      s += '<path class="se-yay-c" d="' + zikzak([px + alt[0] * 4, py + alt[1] * 4], [px + alt[0] * 24, py + alt[1] * 24], 4) + '"/>';
    }
    const p0 = [a[0] + alt[0] * 26, a[1] + alt[1] * 26], p1 = [b[0] + alt[0] * 26, b[1] + alt[1] * 26];
    s += '<path class="se-mes-c" d="M' + pt(p0[0], p0[1]) + " L" + pt(p1[0], p1[1]) + '"/>';
    const ux = dx / L, uy = dy / L;
    for (let x = 0; x <= L; x += 9) s += '<path class="se-mes-t" d="M' + pt(p0[0] + ux * x, p0[1] + uy * x) + " L" + pt(p0[0] + ux * (x - 5) + alt[0] * 6, p0[1] + uy * (x - 5) + alt[1] * 6) + '"/>';
    if (etiket) s += metinSvg((p0[0] + p1[0]) / 2 + alt[0] * 16, (p0[1] + p1[1]) / 2 + alt[1] * 16 + 4, etiket, "se-etiket se-yay-t", "middle");
    return s;
  }

  // ---------- Model şekli ----------
  function modelSekli(W) {
    cizimGenislik = W;
    const g = geometri(S), tip = S.tip, tp = TIPLER[tip], b = birimler();
    const dugumler = Object.keys(g.d).map(function (k) { return g.d[k]; });
    if (!dugumler.length || !g.e.length) {
      return '<p class="not se-bos">Şekil için en az iki düğüm ve bu düğümleri bağlayan bir eleman girin.</p>';
    }
    const T = donusum(dugumler.map(function (n) { return duzlem(tip, n.x, n.y, n.z); }), W, { minH: 150 });
    const N = {};
    dugumler.forEach(function (n) { const p = duzlem(tip, n.x, n.y, n.z); N[n.no] = [T.x(p[0]), T.y(p[1])]; });
    const yerelYon = function (e, eksen) {
      // elemanın yerel y' (eksen 1) ya da z' (eksen 2) yönünün ekran birim vektörü
      if (ucBoyut(tip)) {
        if (tip === "kafes3b") return yon3(tip, [0, 1, 0]);
        return yon3(tip, yerelEksen3(e.b.x - e.a.x, e.b.y - e.a.y, e.b.z - e.a.z)[eksen]);
      }
      const a = N[e.a.no], c = N[e.b.no], dx = c[0] - a[0], dy = c[1] - a[1], L = Math.hypot(dx, dy) || 1;
      return [dy / L, -dx / L];        // ekranda elemanın solu = yerel +y
    };
    let s = eksenTakimi(tip, T);
    // zemin
    g.e.forEach(function (e) {
      if (e.zemin == null) return;
      s += zeminCiz(N[e.a.no], N[e.b.no], yerelYon(e, 1), "kₛ = " + (sayiOku(e.zemin) != null ? fmt(sayiOku(e.zemin)) : e.zemin) + " " + b.f + "/" + b.l + "²");
    });
    // elemanlar
    g.e.forEach(function (e) {
      const a = N[e.a.no], c = N[e.b.no];
      if (tip === "yay") {
        s += '<path class="se-eleman se-yay" d="' + zikzak(a, c, 7) + '"/>';
      } else {
        s += '<path class="se-eleman' + (tip === "kafes" || tip === "kafes3b" ? " se-kafes" : "") + '" d="M' + pt(a[0], a[1]) + " L" + pt(c[0], c[1]) + '"/>';
      }
    });
    // yayılı yükler
    if (tp.q) {
      S.yayili.forEach(function (y) {
        const eno = tamSayi(y.eleman);
        if (eno == null) return;
        const e = g.e.filter(function (x) { return x.no === eno; })[0];
        if (!e) return;
        const q = yukOku(y.q), qz = tp.qz ? yukOku(y.qz) : null;
        if (q) s += yayiliOku(N[e.a.no], N[e.b.no], yerelYon(e, 1), q, "q", b.f + "/" + b.l);
        if (qz) s += yayiliOku(N[e.a.no], N[e.b.no], yerelYon(e, 2), qz, "qz", b.f + "/" + b.l);
      });
    }
    // mesnetler
    const bagli = bagliYonler(g.e.map(function (e) { return [e.a.no, N[e.a.no], e.b.no, N[e.b.no]]; }));
    s += mesnetleriCiz(tip, S.mesnetler, N, bagli, false);
    // yaylar (elastik mesnetler)
    S.yaylar.forEach(function (y) {
      const p = N[tamSayi(y.dugum)];
      if (!p) return;
      tp.yay.forEach(function (k) { if (!bos(y[k]) && sayiOku(y[k]) !== 0) s += yayCiz(tip, p[0], p[1], k, y[k], bagli[tamSayi(y.dugum)] || []); });
    });
    // mesnet çökmeleri
    S.cokmeler.forEach(function (c) {
      const p = N[tamSayi(c.dugum)];
      if (!p) return;
      tp.mes.forEach(function (k) {
        const v = yukOku(c[k]);
        if (!v) return;
        const et = k + " = " + (v.isaret < 0 ? "−" : "") + v.etiket;
        if (k.charAt(0) === "r") { s += momentOku(p[0], p[1], v.isaret, et); return; }
        const w = k === "ux" ? yon3(tip, [1, 0, 0]) : k === "uy" ? yon3(tip, [0, 1, 0]) : yon3(tip, [0, 0, 1]);
        // yer değiştirme oku düğümden hareket yönüne gider; biraz uzun tutulur ki etiketi düğüm numarasına değmesin
        s += kuvvetOku(p[0] + w[0] * v.isaret * 60, p[1] + w[1] * v.isaret * 60, w[0] * v.isaret, w[1] * v.isaret, et, "se-cok-c", "se-cok-o", "se-yay-t");
      });
    });
    // düğüm yükleri
    S.yukler.forEach(function (y) {
      const p = N[tamSayi(y.dugum)];
      if (!p) return;
      let kayma = 0;
      tp.yuk.forEach(function (k) {
        const v = yukOku(y[k]);
        if (!v) return;
        if (k.charAt(0) === "M") {
          const et = (tp.yuk.length > 3 ? k + " = " : "") + v.etiket + " " + b.f + "·" + b.l;
          s += momentOku(p[0], p[1], v.isaret, et, kayma); kayma += 13; return;
        }
        const w = k === "Fx" ? yon3(tip, [1, 0, 0]) : k === "Fy" ? yon3(tip, [0, 1, 0]) : yon3(tip, [0, 0, 1]);
        s += kuvvetOku(p[0], p[1], w[0] * v.isaret, w[1] * v.isaret, (tp.yuk.length > 3 ? k + " = " : "") + v.etiket + " " + b.f);
      });
    });
    // düğümler ve numaralar
    dugumler.forEach(function (n) {
      const p = N[n.no];
      s += '<circle class="se-dugum" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="' + (tip === "kafes" || tip === "kafes3b" ? 5 : 4) + '"/>';
      s += metinSvg(p[0] + 8, p[1] - 8, String(n.no), "se-no");
    });
    g.e.forEach(function (e) {
      const a = N[e.a.no], c = N[e.b.no], dx = c[0] - a[0], dy = c[1] - a[1], L = Math.hypot(dx, dy) || 1;
      s += metinSvg((a[0] + c[0]) / 2 + (dy / L) * 11, (a[1] + c[1]) / 2 - (dx / L) * 11 + 4, "e" + e.no, "se-eno", "middle");
    });
    return svgSar(T, s, "Yapı modeli: " + dugumler.length + " düğüm, " + g.e.length + " eleman" + (ucBoyut(tip) ? " (3B izdüşüm)" : ""));
  }

  // ---------- Deforme şekil ----------
  function yerDegistirme(tip, u) {
    u = u || [];
    const z = function (i) { return typeof u[i] === "number" ? u[i] : 0; };
    if (tip === "kafes") return [z(0), z(1), 0, 0, 0, 0];
    if (tip === "kiris") return [0, z(0), 0, 0, 0, z(1)];
    if (tip === "cerceve") return [z(0), z(1), 0, 0, 0, z(2)];
    if (tip === "kafes3b") return [z(0), z(1), z(2), 0, 0, 0];
    if (tip === "cerceve3b") return [z(0), z(1), z(2), z(3), z(4), z(5)];
    return [z(0), 0, 0, 0, 0, 0];
  }
  function sayisalMi(veri) {
    if (!veri || !veri.u || !veri.elemanlar) return false;
    if (!veri.u.every(function (x) { return typeof x === "number"; })) return false;
    return veri.elemanlar.every(function (e) {
      const d = e.diyagram;
      return d && d.x && [d.x, d.N, d.V, d.M].every(function (dz) { return dz.every(function (x) { return typeof x === "number"; }); });
    });
  }
  function hermite(xi, L, v1, t1, v2, t2) {
    const x2 = xi * xi, x3 = x2 * xi;
    return v1 * (1 - 3 * x2 + 2 * x3) + t1 * L * (xi - 2 * x2 + x3) + v2 * (3 * x2 - 2 * x3) + t2 * L * (-x2 + x3);
  }
  // Bir elemanın birim ölçekteki yer değiştirme örnekleri: {b: [X, Y, Z] taban, d: [dX, dY, dZ]} n+1 nokta
  function elemanEgrisi(e, nd, tip, n) {
    const a = nd[e.dugumler[0]], b = nd[e.dugumler[1]];
    const ua = yerDegistirme(tip, a.u), ub = yerDegistirme(tip, b.u);
    const L = e.L, out = [];
    const eg = tip === "kiris" || tip === "cerceve" || tip === "cerceve3b";
    const az = a.z || 0, bz = b.z || 0;
    if (tip === "cerceve3b" && e.lam) {
      const lam = e.lam;
      const yerel = function (u) { return [0, 1, 2].map(function (i) { return lam[i][0] * u[0] + lam[i][1] * u[1] + lam[i][2] * u[2]; }); };
      const da = yerel(ua), db = yerel(ub), ra = yerel([ua[3], ua[4], ua[5]]), rb = yerel([ub[3], ub[4], ub[5]]);
      for (let m = 0; m <= n; m++) {
        const xi = m / n;
        const ul = da[0] + (db[0] - da[0]) * xi;
        const vl = hermite(xi, L, da[1], ra[2], db[1], rb[2]);
        const wl = hermite(xi, L, da[2], -ra[1], db[2], -rb[1]);
        const d = [0, 1, 2].map(function (j) { return lam[0][j] * ul + lam[1][j] * vl + lam[2][j] * wl; });
        out.push({ b: [a.x + (b.x - a.x) * xi, a.y + (b.y - a.y) * xi, az + (bz - az) * xi], d: d });
      }
      return out;
    }
    const c = e.c, s = e.s;
    const ul1 = c * ua[0] + s * ua[1], vl1 = -s * ua[0] + c * ua[1], t1 = ua[5];
    const ul2 = c * ub[0] + s * ub[1], vl2 = -s * ub[0] + c * ub[1], t2 = ub[5];
    for (let m = 0; m <= n; m++) {
      const xi = m / n;
      let d;
      if (tip === "kafes3b") d = [ua[0] + (ub[0] - ua[0]) * xi, ua[1] + (ub[1] - ua[1]) * xi, ua[2] + (ub[2] - ua[2]) * xi];
      else {
        const ul = ul1 + (ul2 - ul1) * xi;
        const vl = eg ? hermite(xi, L, vl1, t1, vl2, t2) : vl1 + (vl2 - vl1) * xi;
        d = [c * ul - s * vl, s * ul + c * vl, 0];
      }
      out.push({ b: [a.x + (b.x - a.x) * xi, a.y + (b.y - a.y) * xi, az + (bz - az) * xi], d: d });
    }
    return out;
  }
  function deformeVeri(veri) {
    const tip = veri.tip, nd = {};
    veri.dugumler.forEach(function (d) { nd[d.no] = d; });
    const n = tip === "kiris" || tip === "cerceve" || tip === "cerceve3b" ? 20 : 1;
    const egriler = veri.elemanlar.map(function (e) { return elemanEgrisi(e, nd, tip, n); });
    let maks = 0, aralik = 0;
    const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    egriler.forEach(function (eg) {
      eg.forEach(function (p) {
        maks = Math.max(maks, Math.hypot(p.d[0], p.d[1], p.d[2]));
        for (let i = 0; i < 3; i++) { mn[i] = Math.min(mn[i], p.b[i]); mx[i] = Math.max(mx[i], p.b[i]); }
      });
    });
    for (let i = 0; i < 3; i++) aralik = Math.max(aralik, mx[i] - mn[i]);
    aralik = aralik || 1;
    return { tip: tip, nd: nd, egriler: egriler, maks: maks, otomatik: maks > 1e-15 ? 0.1 * aralik / maks : 1 };
  }
  function deformeSekli(veri, W, yuzde) {
    const dv = deformeVeri(veri), tip = veri.tip;
    const k = dv.otomatik * yuzde / 100, kSinir = dv.otomatik * 1.5;
    const birDim = tip === "yay" || tip === "cubuk";
    const pts = [];
    dv.egriler.forEach(function (eg) {
      eg.forEach(function (p) {
        pts.push(duzlem(tip, p.b[0], p.b[1], p.b[2]));
        pts.push(duzlem(tip, p.b[0] + kSinir * p.d[0], p.b[1] + kSinir * p.d[1], p.b[2] + kSinir * p.d[2]));
      });
    });
    const T = donusum(pts, W, birDim ? { minH: 190, pu: 40, pa: 60 } : { minH: 150 });
    const kayma = birDim ? 40 : 0;       // 1B modelde deforme çizgi özgün çizginin altına alınır
    const Y0 = birDim ? T.H * 0.34 : 0;
    const asil = function (b) { const p = duzlem(tip, b[0], b[1], b[2]); return [T.x(p[0]), birDim ? Y0 : T.y(p[1])]; };
    const ekran = function (b, d) { const p = duzlem(tip, b[0] + k * d[0], b[1] + k * d[1], b[2] + k * d[2]); return [T.x(p[0]), birDim ? Y0 + kayma : T.y(p[1])]; };
    let s = eksenTakimi(tip, T);
    // özgün yapı (soluk) ve mesnetler
    veri.elemanlar.forEach(function (e, i) {
      const eg = dv.egriler[i], A1 = asil(eg[0].b), B1 = asil(eg[eg.length - 1].b);
      s += '<path class="se-asil" d="M' + pt(A1[0], A1[1]) + " L" + pt(B1[0], B1[1]) + '"/>';
    });
    // deforme şekil
    veri.elemanlar.forEach(function (e, i) {
      let d = "";
      dv.egriler[i].forEach(function (p, m) { const q = ekran(p.b, p.d); d += (m ? " L" : "M") + pt(q[0], q[1]); });
      s += '<path class="se-def" d="' + d + '"/>';
    });
    veri.dugumler.forEach(function (n) {
      const u = yerDegistirme(tip, n.u);
      const q = ekran([n.x, n.y, n.z || 0], [u[0], u[1], u[2]]);
      const o = asil([n.x, n.y, n.z || 0]);
      if (birDim) s += '<path class="se-kilavuz" d="M' + pt(o[0], o[1]) + " L" + pt(q[0], q[1]) + '"/>';
      s += '<circle class="se-dugum se-dugum-d" cx="' + r1(q[0]) + '" cy="' + r1(q[1]) + '" r="4.5"/>';
      s += metinSvg(q[0] + 8, q[1] - 8, String(n.no), "se-no");
    });
    // mesnet sembolleri özgün konumda
    const N = {};
    veri.dugumler.forEach(function (n) { N[n.no] = asil([n.x, n.y, n.z || 0]); });
    const bagli = bagliYonler(veri.elemanlar.map(function (e) { return [e.dugumler[0], N[e.dugumler[0]], e.dugumler[1], N[e.dugumler[1]]]; }));
    s += mesnetleriCiz(tip, S.mesnetler, N, bagli, true);
    return { svg: svgSar(T, s, "Deforme şekil, ölçek ×" + fmt(k)), k: k };
  }

  // ---------- Diyagramlar ----------
  const DIYAGRAM = {
    N:  { ad: "Normal kuvvet N",   sinif: "se-dN", isaret: 1,  eksen: 1 },
    V:  { ad: "Kesme kuvveti V",   sinif: "se-dV", isaret: 1,  eksen: 1 },
    M:  { ad: "Eğilme momenti M",  sinif: "se-dM", isaret: -1, eksen: 1 },
    Vz: { ad: "Kesme kuvveti Vz",  sinif: "se-dV", isaret: 1,  eksen: 2 },
    My: { ad: "Eğilme momenti My", sinif: "se-dM", isaret: -1, eksen: 2 },
    T:  { ad: "Burulma momenti T", sinif: "se-dN", isaret: 1,  eksen: 2 },
  };
  function diyagramTurleri(tip) {
    return tip === "cerceve3b" ? ["N", "V", "M", "Vz", "My", "T"] : ["N", "V", "M"];
  }
  function diyagramSekli(veri, W, tur) {
    const tip = veri.tip, def = DIYAGRAM[tur], b = birimler(veri.birim);
    const nd = {};
    veri.dugumler.forEach(function (d) { nd[d.no] = d; });
    const pts = veri.dugumler.map(function (n) { return duzlem(tip, n.x, n.y, n.z || 0); });
    const T = donusum(pts, W, { minH: 190, pu: 72, pa: 72 });
    const N = {};
    veri.dugumler.forEach(function (n) { const p = duzlem(tip, n.x, n.y, n.z || 0); N[n.no] = [T.x(p[0]), T.y(p[1])]; });
    let gmaks = 0;
    veri.elemanlar.forEach(function (e) { (e.diyagram[tur] || []).forEach(function (v) { gmaks = Math.max(gmaks, Math.abs(v)); }); });
    const kD = gmaks > 1e-12 ? 38 / gmaks : 0;
    const yerelYon = function (e) {
      if (tip === "cerceve3b" && e.lam) return yon3(tip, e.lam[def.eksen]);
      if (tip === "kafes3b") return yon3(tip, [0, 1, 0]);
      return [-e.s, -e.c];       // ekran: +n (elemanın solu = yerel +y)
    };
    let s = eksenTakimi(tip, T);
    veri.elemanlar.forEach(function (e) {
      const a = N[e.dugumler[0]], c = N[e.dugumler[1]];
      s += '<path class="se-asil" d="M' + pt(a[0], a[1]) + " L" + pt(c[0], c[1]) + '"/>';
    });
    veri.elemanlar.forEach(function (e) {
      const a = N[e.dugumler[0]], c = N[e.dugumler[1]], d = e.diyagram, val = d[tur] || [];
      const ex = c[0] - a[0], ey = c[1] - a[1], Lp = Math.hypot(ex, ey) || 1, dx = ex / Lp, dy = ey / Lp;
      const n = yerelYon(e), nx = n[0], ny = n[1];
      const taban = [], ust = [];
      d.x.forEach(function (x, i) {
        const t = x / e.L, bx = a[0] + dx * t * Lp, by = a[1] + dy * t * Lp, o = def.isaret * (val[i] || 0) * kD;
        taban.push([bx, by]);
        ust.push([bx + nx * o, by + ny * o]);
      });
      if (!taban.length) return;
      let yol = "M" + pt(taban[0][0], taban[0][1]);
      ust.forEach(function (p) { yol += " L" + pt(p[0], p[1]); });
      for (let i = taban.length - 1; i >= 0; i--) yol += " L" + pt(taban[i][0], taban[i][1]);
      s += '<path class="se-dgm ' + def.sinif + '" d="' + yol + ' Z"/>';
      // en büyük mutlak değer etiketi
      let im = 0;
      val.forEach(function (v, i) { if (Math.abs(v) > Math.abs(val[im]) + 1e-12) im = i; });
      if (val.length && Math.abs(val[im]) > 1e-9 * Math.max(gmaks, 1e-9) && Math.abs(val[im]) > 1e-9) {
        const sg = def.isaret * val[im] >= 0 ? 1 : -1;
        let lx = ust[im][0] + nx * sg * 11, ly = ust[im][1] + ny * sg * 11;
        const kay = im === 0 ? 18 : im === val.length - 1 ? -18 : 0;
        lx += dx * kay; ly += dy * kay;
        s += metinSvg(lx, ly + 4, fmt(val[im]), "se-etiket", "middle");
      }
    });
    veri.dugumler.forEach(function (n) {
      const p = N[n.no];
      s += '<circle class="se-dugum" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="3.5"/>';
    });
    const momentMi = tur === "M" || tur === "My" || tur === "T";
    return svgSar(T, s, def.ad + " diyagramı (" + (momentMi ? b.f + "·" + b.l : b.f) + ")");
  }
  function enBuyuk(dizi) {
    let m = 0;
    (dizi || []).forEach(function (v) { if (Math.abs(v) > Math.abs(m)) m = v; });
    return m;
  }

  // ---------- Model tabloları ----------
  function girdiH(t, i, a, v, etiket, mod) {
    return '<td data-e="' + kacis(etiket) + '"><input class="se-g" type="text" inputmode="' + (mod || "decimal") + '" autocomplete="off" spellcheck="false" ' +
      'data-t="' + t + '" data-i="' + i + '" data-a="' + a + '" value="' + kacis(v) + '" aria-label="' + kacis(etiket + ", satır " + (i + 1)) + '"></td>';
  }
  function onayH(t, i, a, v, etiket) {
    return '<td data-e="' + kacis(etiket) + '"><label class="se-onay"><input type="checkbox" data-t="' + t + '" data-i="' + i + '" data-a="' + a + '"' + (v ? " checked" : "") +
      ' aria-label="' + kacis(etiket + ", satır " + (i + 1)) + '"><span>' + kacis(etiket) + "</span></label></td>";
  }
  function silH(t, i) {
    return '<td class="se-sil-h"><button type="button" class="se-sil" data-sil="' + t + ":" + i + '" aria-label="Satırı sil (' + (i + 1) + '. satır)" title="Satırı sil">✕</button></td>';
  }
  function tabloH(t, baslik, ipucu, basliklar, satirlar, ekleMetin) {
    return '<section class="se-bolum"><div class="se-bolum-ust"><h3>' + baslik + "</h3>" +
      '<button type="button" class="dugme kucuk" data-ekle="' + t + '">+ ' + ekleMetin + "</button></div>" +
      (ipucu ? '<p class="not se-ipucu">' + ipucu + "</p>" : "") +
      (satirlar.length
        ? '<table class="se-tablo"><thead><tr>' + basliklar.map(function (h) { return "<th>" + kacis(h) + "</th>"; }).join("") + "<th></th></tr></thead><tbody>" +
          satirlar.join("") + "</tbody></table>"
        : '<p class="not">Henüz satır yok.</p>') + "</section>";
  }
  function tablolariKur() {
    const tp = TIPLER[S.tip], uc = ucBoyut(S.tip);
    const dugum = S.dugumler.map(function (n, i) {
      return "<tr>" + girdiH("dugumler", i, "no", n.no, "no", "numeric") + girdiH("dugumler", i, "x", n.x, "x (m)") +
        (tp.xy ? girdiH("dugumler", i, "y", n.y, "y (m)") : "") + (tp.z ? girdiH("dugumler", i, "z", n.z, "z (m)") : "") + silH("dugumler", i) + "</tr>";
    });
    const eleman = S.elemanlar.map(function (e, i) {
      return "<tr>" + girdiH("elemanlar", i, "no", e.no, "no", "numeric") + girdiH("elemanlar", i, "i", e.i, "i. düğüm", "numeric") + girdiH("elemanlar", i, "j", e.j, "j. düğüm", "numeric") +
        tp.oz.map(function (p) { return girdiH("elemanlar", i, p, e[p], OZ_ETIKET[p], "text"); }).join("") +
        (tp.zemin ? girdiH("elemanlar", i, "zemin", e.zemin, OZ_ETIKET.zemin, "text") : "") + silH("elemanlar", i) + "</tr>";
    });
    const mesnet = S.mesnetler.map(function (m, i) {
      return "<tr>" + girdiH("mesnetler", i, "dugum", m.dugum, "düğüm", "numeric") +
        tp.mes.map(function (f) { return onayH("mesnetler", i, f, m[f], MES_ETIKET[f]); }).join("") + silH("mesnetler", i) + "</tr>";
    });
    const yuk = S.yukler.map(function (y, i) {
      return "<tr>" + girdiH("yukler", i, "dugum", y.dugum, "düğüm", "numeric") +
        tp.yuk.map(function (f) { return girdiH("yukler", i, f, y[f], YUK_ETIKET[f], "text"); }).join("") + silH("yukler", i) + "</tr>";
    });
    const yayili = S.yayili.map(function (y, i) {
      return "<tr>" + girdiH("yayili", i, "eleman", y.eleman, "eleman", "numeric") + girdiH("yayili", i, "q", y.q, tp.qz ? "q (y′, kN/m)" : "q (kN/m)", "text") +
        (tp.qz ? girdiH("yayili", i, "qz", y.qz, "qz (z′, kN/m)", "text") : "") + silH("yayili", i) + "</tr>";
    });
    const yaylar = S.yaylar.map(function (y, i) {
      return "<tr>" + girdiH("yaylar", i, "dugum", y.dugum, "düğüm", "numeric") +
        tp.yay.map(function (k) { return girdiH("yaylar", i, k, y[k], YAY_ETIKET[k], "text"); }).join("") + silH("yaylar", i) + "</tr>";
    });
    const cokmeler = S.cokmeler.map(function (c, i) {
      return "<tr>" + girdiH("cokmeler", i, "dugum", c.dugum, "düğüm", "numeric") +
        tp.mes.map(function (k) { return girdiH("cokmeler", i, k, c[k], COK_ETIKET[k], "text"); }).join("") + silH("cokmeler", i) + "</tr>";
    });
    let h = tabloH("dugumler", "Düğümler", uc ? "x sağa, y yukarı, z düzlemden dışa (sağ el kuralı)." : "", ["No", "x (m)"].concat(tp.xy ? ["y (m)"] : []).concat(tp.z ? ["z (m)"] : []), dugum, "Düğüm ekle");
    let elIp = "Her eleman iki düğümü bağlar" + (S.tip === "kiris" ? "; kiriş elemanlarında i. düğüm solda olmalı" : "") + ". E, A, I, k yerine sayı ya da harf (sembol) yazabilirsin.";
    if (tp.zemin) elIp += " Elastik zemine (Winkler) oturan temel kirişi için kₛ (birim boya zemin yayı, kN/m²) yaz; yoksa boş bırak.";
    if (S.tip === "cerceve3b") elIp += " Iz, yerel y′ yönündeki (düşey düzlemdeki) yüke karşı eğilme ataletidir; J burulma sabitidir.";
    h += tabloH("elemanlar", "Elemanlar", elIp, ["No", "i. düğüm", "j. düğüm"].concat(tp.oz.map(function (p) { return OZ_ETIKET[p]; })).concat(tp.zemin ? [OZ_ETIKET.zemin] : []), eleman, "Eleman ekle");
    h += tabloH("mesnetler", "Mesnetler", "İşaretli yön tutulur: ux, uy, uz ötelemeler; rx, ry, rz dönmeler." + ((tp.yay.length || tp.zemin) ? " Yalnız yay ya da zemine oturan yapıda mesnet olmayabilir." : ""), ["Düğüm"].concat(tp.mes.map(function (f) { return MES_ETIKET[f]; })), mesnet, "Mesnet ekle");
    h += tabloH("yukler", "Düğüm yükleri", uc ? "Fx, Fy, Fz eksen yönünde; Mx, My, Mz sağ el kuralıyla pozitiftir." : "Fx sağa, Fy yukarı, M saat yönünün tersine pozitiftir.", ["Düğüm"].concat(tp.yuk.map(function (f) { return YUK_ETIKET[f]; })), yuk, "Yük ekle");
    if (tp.q) h += tabloH("yayili", "Yayılı yükler", tp.qz ? "q elemanın yerel y′ (düşey düzlemde yukarı), qz yerel z′ (yatay) yönündedir; aşağı yük için negatif q yaz." : "q elemanın yerel y yönündedir (soldan sağa giden elemanda yukarı); aşağı yük için negatif yaz.", ["Eleman", tp.qz ? "q (y′)" : "q (kN/m)"].concat(tp.qz ? ["qz (z′)"] : []), yayili, "Yayılı yük ekle");
    h += tabloH("yaylar", "Elastik mesnetler (yaylar)", "Zemini ya da esnek bir mesnedi temsil eden yaylar: kx, ky, kz öteleme (kN/m), kr dönme (kN·m/rad) yayı. Rijitlik K'nın köşegenine eklenir.", ["Düğüm"].concat(tp.yay.map(function (k) { return YAY_ETIKET[k]; })), yaylar, "Yay ekle");
    h += tabloH("cokmeler", "Mesnet çökmeleri", "Verilen yer değiştirme: o serbestlik tutulu sayılır ve sıfır yerine bu değeri alır (örneğin uy = −0.01 → 10 mm oturma).", ["Düğüm"].concat(tp.mes.map(function (k) { return COK_ETIKET[k]; })), cokmeler, "Çökme ekle");
    ref.tablolar.innerHTML = h;
  }

  // ---------- Model <-> JSON ----------
  function tipAdiSade(t) {
    t = str(t).trim().toLowerCase().replace(/ç/g, "c").replace(/ı/g, "i").replace(/ş/g, "s").replace(/ğ/g, "g").replace(/ö/g, "o").replace(/ü/g, "u").replace(/[-_]/g, "");
    return t === "kafes3d" ? "kafes3b" : (t === "cerceve3d" ? "cerceve3b" : t);
  }
  function modelYukle(m) {
    if (!m || typeof m !== "object" || Array.isArray(m)) throw new Error("Model bir JSON nesnesi olmalı: {\"tip\": \"kafes\", \"dugumler\": [...], ...}.");
    const tip = tipAdiSade(m.tip);
    if (!TIPLER[tip]) throw new Error("Bilinmeyen model türü: " + str(m.tip) + ". Seçenekler: " + TIP_SIRA.join(", ") + ".");
    const s = bosModel(tip);
    s.baslik = str(m.baslik);
    s.aciklama = str(m.aciklama);
    if (m.birim && typeof m.birim === "object") s.birim = { kuvvet: str(m.birim.kuvvet) || "kN", uzunluk: str(m.birim.uzunluk) || "m" };
    const dz = function (v) { return Array.isArray(v) ? v : []; };
    dz(m.dugumler).forEach(function (n, k) { n = n || {}; s.dugumler.push({ no: str(n.no != null ? n.no : k + 1), x: str(n.x != null ? n.x : 0), y: str(n.y != null ? n.y : 0), z: str(n.z != null ? n.z : 0) }); });
    dz(m.elemanlar).forEach(function (e, k) {
      e = e || {};
      const d = dz(e.dugumler);
      s.elemanlar.push({ no: str(e.no != null ? e.no : k + 1), i: str(d[0]), j: str(d[1]), k: str(e.k), E: str(e.E), G: str(e.G), A: str(e.A), I: str(e.I), Iy: str(e.Iy), Iz: str(e.Iz), J: str(e.J), zemin: str(e.zemin) });
    });
    dz(m.mesnetler).forEach(function (x) { x = x || {}; s.mesnetler.push({ dugum: str(x.dugum), ux: !!x.ux, uy: !!x.uy, uz: !!x.uz, rx: !!x.rx, ry: !!x.ry, rz: !!x.rz }); });
    dz(m.yukler).forEach(function (y) {
      y = y || {};
      // motor gibi: "M" ile "Mz" aynı bileşendir; ikisi de verilmişse toplanır (sayısal değilse "+" ile birleştirilir)
      const mz = birlesikDeger(y.M, y.Mz);
      s.yukler.push({ dugum: str(y.dugum), Fx: str(y.Fx), Fy: str(y.Fy), Fz: str(y.Fz), M: tip === "cerceve3b" ? "" : mz, Mx: str(y.Mx), My: str(y.My), Mz: tip === "cerceve3b" ? mz : "" });
    });
    dz(m.yayili).forEach(function (y) { y = y || {}; s.yayili.push({ eleman: str(y.eleman), q: str(y.q), qz: str(y.qz) }); });
    dz(m.yaylar).forEach(function (y) {
      y = y || {};
      const o = { dugum: str(y.dugum) };
      Object.keys(YAY_ETIKET).forEach(function (k) { o[k] = str(y[k]); });
      const kr = birlesikDeger(y.kr, y.krz);   // "kr" ile "krz" aynı dönme yayıdır
      if (tip === "cerceve3b") { o.krz = kr; o.kr = ""; } else { o.kr = kr; o.krz = ""; }
      s.yaylar.push(o);
    });
    dz(m.cokmeler).forEach(function (c) {
      c = c || {};
      const o = { dugum: str(c.dugum) };
      Object.keys(COK_ETIKET).forEach(function (k) { o[k] = str(c[k]); });
      s.cokmeler.push(o);
    });
    return s;
  }
  function birlesikDeger(a, b) {
    // aynı bileşenin iki adı (M/Mz, kr/krz): biri boşsa öteki; ikisi de doluysa toplam
    const sa = str(a).trim(), sb = str(b).trim();
    if (!sa) return sb;
    if (!sb) return sa;
    const na = sayiOku(sa), nb = sayiOku(sb);
    if (na != null && nb != null) return String(na + nb);
    return "(" + sa + ")+(" + sb + ")";
  }
  function sayiyaDondur(t) {
    const n = sayiOku(t);
    return n != null ? n : str(t).trim();
  }
  function temizModel() {
    const tp = TIPLER[S.tip];
    const m = { tip: S.tip, baslik: S.baslik, aciklama: S.aciklama, birim: S.birim, dugumler: [], elemanlar: [], mesnetler: [], yukler: [] };
    S.dugumler.forEach(function (n) {
      const o = { no: sayiyaDondur(n.no), x: sayiyaDondur(n.x) };
      o.y = tp.xy ? sayiyaDondur(n.y) : 0;
      if (tp.z) o.z = sayiyaDondur(n.z);
      m.dugumler.push(o);
    });
    S.elemanlar.forEach(function (e) {
      const o = { no: sayiyaDondur(e.no), dugumler: [sayiyaDondur(e.i), sayiyaDondur(e.j)] };
      tp.oz.forEach(function (p) { o[p] = str(e[p]).trim(); });
      if (tp.zemin && !bos(e.zemin)) o.zemin = str(e.zemin).trim();
      m.elemanlar.push(o);
    });
    S.mesnetler.forEach(function (x) {
      const o = { dugum: sayiyaDondur(x.dugum) };
      let bir = false;
      tp.mes.forEach(function (f) { o[f] = !!x[f]; if (x[f]) bir = true; });
      if (bir) m.mesnetler.push(o);
    });
    S.yukler.forEach(function (y) {
      const o = { dugum: sayiyaDondur(y.dugum) };
      let bir = false;
      tp.yuk.forEach(function (f) { if (!bos(y[f])) { o[f] = sayiyaDondur(y[f]); bir = true; } });
      if (bir) m.yukler.push(o);
    });
    if (tp.q) {
      m.yayili = [];
      S.yayili.forEach(function (y) {
        if (bos(y.q) && bos(y.eleman) && bos(y.qz)) return;
        const o = { eleman: sayiyaDondur(y.eleman), q: bos(y.q) ? 0 : sayiyaDondur(y.q) };
        if (tp.qz && !bos(y.qz)) o.qz = sayiyaDondur(y.qz);
        m.yayili.push(o);
      });
      if (!m.yayili.length) delete m.yayili;
    }
    const yaylar = [];
    S.yaylar.forEach(function (y) {
      const o = { dugum: sayiyaDondur(y.dugum) };
      let bir = false;
      tp.yay.forEach(function (k) { if (!bos(y[k])) { o[k] = sayiyaDondur(y[k]); bir = true; } });
      if (bir) yaylar.push(o);
    });
    if (yaylar.length) m.yaylar = yaylar;
    const cokmeler = [];
    S.cokmeler.forEach(function (c) {
      const o = { dugum: sayiyaDondur(c.dugum) };
      let bir = false;
      tp.mes.forEach(function (k) { if (!bos(c[k])) { o[k] = sayiyaDondur(c[k]); bir = true; } });
      if (bir) cokmeler.push(o);
    });
    if (cokmeler.length) m.cokmeler = cokmeler;
    return m;
  }

  // ---------- Doğrulama (Türkçe, motorun kurallarının ön kontrolü) ----------
  function dogrula() {
    const tp = TIPLER[S.tip], h = [];
    const dn = {};
    if (S.dugumler.length < 2) h.push("Modelde en az iki düğüm olmalı.");
    S.dugumler.forEach(function (n, i) {
      const no = tamSayi(n.no);
      if (no == null) { h.push((i + 1) + ". düğümün numarası tam sayı olmalı (girilen: “" + str(n.no) + "”)."); return; }
      if (dn[no]) h.push("Düğüm " + no + " iki kez tanımlanmış; her numara bir kez kullanılabilir.");
      if (sayiOku(n.x) == null) h.push("Düğüm " + no + ": x koordinatı sayı olmalı (girilen: “" + str(n.x) + "”).");
      if (tp.xy && sayiOku(n.y) == null) h.push("Düğüm " + no + ": y koordinatı sayı olmalı (girilen: “" + str(n.y) + "”).");
      if (tp.z && sayiOku(n.z) == null) h.push("Düğüm " + no + ": z koordinatı sayı olmalı (girilen: “" + str(n.z) + "”).");
      dn[no] = { x: sayiOku(n.x), y: tp.xy ? sayiOku(n.y) : 0, z: tp.z ? sayiOku(n.z) : 0 };
    });
    const en = {}, bagli = {};
    let zeminVar = false;
    if (!S.elemanlar.length) h.push("Modelde en az bir eleman olmalı.");
    S.elemanlar.forEach(function (e, i) {
      const no = tamSayi(e.no);
      if (no == null) { h.push((i + 1) + ". elemanın numarası tam sayı olmalı (girilen: “" + str(e.no) + "”)."); return; }
      if (en[no]) h.push("Eleman " + no + " iki kez tanımlanmış.");
      en[no] = true;
      const a = tamSayi(e.i), b = tamSayi(e.j);
      if (a == null || b == null) { h.push("Eleman " + no + ": i. ve j. düğüm numaraları tam sayı olmalı."); }
      else {
        if (!dn[a]) h.push("Eleman " + no + " tanımsız bir düğüme bağlı: düğüm " + a + ". Tanımlı düğümler: " + Object.keys(dn).join(", ") + ".");
        if (!dn[b]) h.push("Eleman " + no + " tanımsız bir düğüme bağlı: düğüm " + b + ". Tanımlı düğümler: " + Object.keys(dn).join(", ") + ".");
        if (dn[a] && dn[b]) {
          bagli[a] = bagli[b] = true;
          const dx = dn[b].x - dn[a].x, dy = dn[b].y - dn[a].y, dz = dn[b].z - dn[a].z;
          if (dn[a].x != null && dn[b].x != null && dn[a].y != null && dn[b].y != null && dn[a].z != null && dn[b].z != null) {
            if (Math.hypot(dx, dy, dz) === 0) h.push("Eleman " + no + "'nin boyu sıfır: düğüm " + a + " ve düğüm " + b + " aynı noktada. Koordinatları düzeltin.");
            else if (S.tip === "kiris" && dx < 0) h.push("Eleman " + no + ": kiriş elemanları soldan sağa tanımlanmalı; düğüm sırasını [" + b + ", " + a + "] yapın.");
          }
        }
      }
      tp.oz.forEach(function (p) {
        const t = str(e[p]).trim();
        if (t === "") h.push("Eleman " + no + ": " + p + " değeri boş; bir sayı ya da harf (sembol) yazın.");
        else { const n = sayiOku(t); if (n != null && n <= 0) h.push("Eleman " + no + ": " + p + " pozitif olmalı (girilen: " + t + ")."); }
      });
      if (tp.zemin && !bos(e.zemin)) {
        const n = sayiOku(e.zemin);
        if (n != null && n < 0) h.push("Eleman " + no + ": zemin kₛ negatif olamaz (girilen: " + str(e.zemin).trim() + ").");
        if (n == null || n > 0) zeminVar = true;
      }
    });
    Object.keys(dn).forEach(function (k) {
      if (S.elemanlar.length && !bagli[k]) h.push("Düğüm " + k + " hiçbir elemana bağlı değil; bir elemana bağlayın ya da silin.");
    });
    let mesnetVar = false;
    S.mesnetler.forEach(function (m, i) {
      const no = tamSayi(m.dugum);
      if (no == null || !dn[no]) { h.push("Mesnet " + (i + 1) + ": düğüm numarası tanımlı bir düğüm olmalı (girilen: “" + str(m.dugum) + "”)."); return; }
      if (tp.mes.some(function (f) { return m[f]; })) mesnetVar = true;
    });
    let yayVar = false;
    S.yaylar.forEach(function (y, i) {
      const no = tamSayi(y.dugum);
      if (no == null || !dn[no]) { h.push("Yay " + (i + 1) + ": düğüm numarası tanımlı bir düğüm olmalı (girilen: “" + str(y.dugum) + "”)."); return; }
      tp.yay.forEach(function (k) {
        if (bos(y[k])) return;
        const n = sayiOku(y[k]);
        if (n != null && n < 0) h.push("Yay " + (i + 1) + ": " + k + " negatif olamaz (girilen: " + str(y[k]).trim() + ").");
        if (n == null || n > 0) yayVar = true;
      });
    });
    S.cokmeler.forEach(function (c, i) {
      const no = tamSayi(c.dugum);
      if (no == null || !dn[no]) { h.push("Mesnet çökmesi " + (i + 1) + ": düğüm numarası tanımlı bir düğüm olmalı (girilen: “" + str(c.dugum) + "”)."); return; }
      if (tp.mes.some(function (k) { return !bos(c[k]); })) mesnetVar = true;
      else h.push("Mesnet çökmesi " + (i + 1) + ": en az bir yer değiştirme değeri yazın (örneğin uy = -0.01).");
    });
    if (!mesnetVar && !yayVar && !zeminVar) h.push("En az bir mesnet (işaretli yön), yay ya da zemin gerekli; tutulmayan yapı rijit cisim olarak hareket eder.");
    S.yukler.forEach(function (y, i) {
      const no = tamSayi(y.dugum);
      if (no == null || !dn[no]) h.push("Yük " + (i + 1) + ": düğüm numarası tanımlı bir düğüm olmalı (girilen: “" + str(y.dugum) + "”).");
    });
    if (tp.q) {
      S.yayili.forEach(function (y, i) {
        const no = tamSayi(y.eleman);
        if (no == null || !en[no]) h.push("Yayılı yük " + (i + 1) + ": eleman numarası tanımlı bir eleman olmalı (girilen: “" + str(y.eleman) + "”).");
        else if (bos(y.q) && (!tp.qz || bos(y.qz))) h.push("Yayılı yük " + (i + 1) + ": q değeri boş.");
      });
    }
    return h;
  }

  // ---------- İskelet ve olaylar ----------
  function iskeletKur() {
    kok.innerHTML =
      '<div class="se-secimler">' +
        '<label class="alan" for="se-ornek">Hazır örnek</label><select id="se-ornek" class="girdi"><option>Yükleniyor…</option></select>' +
        '<label class="alan" for="se-tip">Model türü</label><select id="se-tip" class="girdi">' +
          TIP_SIRA.map(function (t) { return '<option value="' + t + '">' + kacis(TIPLER[t].ad) + "</option>"; }).join("") + "</select>" +
      "</div>" +
      '<p class="not se-aciklama" id="se-aciklama"></p>' +
      '<div class="se-bakis gizli" id="se-bakis">' +
        '<label for="se-bakis-fi">Döndür <input type="range" id="se-bakis-fi" min="-90" max="90" step="1" value="' + bakis.fi + '" aria-label="3B bakış: dönme"></label>' +
        '<label for="se-bakis-psi">Eğim <input type="range" id="se-bakis-psi" min="-10" max="70" step="1" value="' + bakis.psi + '" aria-label="3B bakış: eğim"></label>' +
        '<span class="not" id="se-bakis-d"></span></div>' +
      '<div class="se-sekil" id="se-model-sekil"></div>' +
      '<p class="not se-lejant" id="se-lejant">Mavi numara düğüm, e1, e2… eleman numarasıdır; kırmızı oklar yüklerdir, yeşil zikzaklar yay ve zemindir.</p>' +
      '<details class="katlanir se-duzen" id="se-duzen" open><summary>Modeli düzenle</summary><div id="se-tablolar"></div>' +
        '<details class="katlanir se-json"><summary>JSON olarak göster / yapıştır</summary>' +
          '<textarea id="se-json" class="girdi" rows="10" spellcheck="false" aria-label="Model JSON"></textarea>' +
          '<div class="dugmeler"><button type="button" class="dugme kucuk" id="se-json-uygula">JSON\'dan uygula</button></div>' +
          '<div id="se-json-hata"></div></details>' +
      "</details>" +
      '<div id="se-hata" aria-live="polite"></div>' +
      '<div class="dugmeler"><button type="button" class="dugme ana" id="se-coz">Çöz</button></div>' +
      '<div id="se-sonuc" aria-live="polite"></div>';
    ref.ornek = document.getElementById("se-ornek");
    ref.tip = document.getElementById("se-tip");
    ref.aciklama = document.getElementById("se-aciklama");
    ref.bakis = document.getElementById("se-bakis");
    ref.bakisD = document.getElementById("se-bakis-d");
    ref.sekil = document.getElementById("se-model-sekil");
    ref.tablolar = document.getElementById("se-tablolar");
    ref.json = document.getElementById("se-json");
    ref.jsonHata = document.getElementById("se-json-hata");
    ref.hata = document.getElementById("se-hata");
    ref.coz = document.getElementById("se-coz");
    ref.sonuc = document.getElementById("se-sonuc");
  }
  function hataGoster(kutu, mesajlar, baslik) {
    if (!mesajlar || !mesajlar.length) { kutu.innerHTML = ""; return; }
    kutu.innerHTML = '<div class="hata-kutu" role="alert">' + (baslik ? "<strong>" + kacis(baslik) + "</strong>" : "") +
      (mesajlar.length === 1 ? '<div class="se-hata-metin">' + kacis(mesajlar[0]) + "</div>"
        : '<ul class="se-hata-liste">' + mesajlar.map(function (m) { return "<li>" + kacis(m) + "</li>"; }).join("") + "</ul>") + "</div>";
  }
  function jsonSenkron() {
    if (document.activeElement === ref.json) return;
    ref.json.value = JSON.stringify(temizModel(), null, 2);
  }
  function bakisGoster() {
    const uc = ucBoyut(S.tip) || (SON && ucBoyut(SON.veri.tip));
    ref.bakis.classList.toggle("gizli", !uc);
    if (ref.bakisD) ref.bakisD.textContent = "φ = " + bakis.fi + "°, ψ = " + bakis.psi + "°";
  }
  function modelSekliniCiz() {
    bakisGoster();
    ref.sekil.innerHTML = modelSekli(genislik(ref.sekil));
  }
  function modelDegisti() {
    clearTimeout(zamanci);
    zamanci = setTimeout(function () {
      modelSekliniCiz();
      jsonSenkron();
      const e = document.getElementById("se-eski");
      if (e) e.classList.remove("gizli");
    }, 120);
  }
  function modeliGoster() {
    ref.tip.value = S.tip;
    ref.aciklama.textContent = (S.baslik ? S.baslik + ". " : "") + S.aciklama;
    tablolariKur();
    modelSekliniCiz();
    jsonSenkron();
    hataGoster(ref.hata, []);
    hataGoster(ref.jsonHata, []);
  }
  function sonucuTemizle() {
    SON = null;
    ref.sonuc.innerHTML = "";
  }
  function yeniSatir(t) {
    const son = function (d) { return d[d.length - 1]; };
    const tp = TIPLER[S.tip];
    if (t === "dugumler") {
      const mak = S.dugumler.reduce(function (m, n) { return Math.max(m, tamSayi(n.no) || 0); }, 0), s = son(S.dugumler);
      const x = s ? sayiOku(s.x) : null;
      S.dugumler.push({ no: String(mak + 1), x: x != null ? String(x + 1) : "0", y: s ? s.y : "0", z: s ? s.z : "0" });
    } else if (t === "elemanlar") {
      const mak = S.elemanlar.reduce(function (m, e) { return Math.max(m, tamSayi(e.no) || 0); }, 0), n = S.dugumler.length;
      const o = { no: String(mak + 1), i: n >= 2 ? S.dugumler[n - 2].no : "", j: n >= 1 ? S.dugumler[n - 1].no : "", k: "", E: "", G: "", A: "", I: "", Iy: "", Iz: "", J: "", zemin: "" };
      const onceki = son(S.elemanlar);
      tp.oz.forEach(function (p) { o[p] = onceki && onceki[p] ? onceki[p] : OZ_VARSAYILAN[p]; });
      if (tp.zemin && onceki) o.zemin = onceki.zemin || "";
      S.elemanlar.push(o);
    } else if (t === "mesnetler") {
      S.mesnetler.push({ dugum: S.dugumler.length ? S.dugumler[0].no : "", ux: tp.mes.indexOf("ux") >= 0, uy: tp.mes.indexOf("uy") >= 0, uz: tp.mes.indexOf("uz") >= 0, rx: false, ry: false, rz: false });
    } else if (t === "yukler") {
      S.yukler.push({ dugum: S.dugumler.length ? S.dugumler[S.dugumler.length - 1].no : "", Fx: "", Fy: "", Fz: "", M: "", Mx: "", My: "", Mz: "" });
    } else if (t === "yayili") {
      S.yayili.push({ eleman: S.elemanlar.length ? S.elemanlar[0].no : "", q: "-10", qz: "" });
    } else if (t === "yaylar") {
      const o = { dugum: S.dugumler.length ? S.dugumler[0].no : "" };
      Object.keys(YAY_ETIKET).forEach(function (k) { o[k] = ""; });
      o[tp.yay.indexOf("ky") >= 0 ? "ky" : tp.yay[0]] = "100000";
      S.yaylar.push(o);
    } else if (t === "cokmeler") {
      const o = { dugum: S.mesnetler.length ? S.mesnetler[S.mesnetler.length - 1].dugum : (S.dugumler.length ? S.dugumler[0].no : "") };
      Object.keys(COK_ETIKET).forEach(function (k) { o[k] = ""; });
      o[tp.mes.indexOf("uy") >= 0 ? "uy" : tp.mes[0]] = "-0.01";
      S.cokmeler.push(o);
    }
  }
  function tipDegistir(tip) {
    if (!TIPLER[tip] || tip === S.tip) return;
    const tp = TIPLER[tip];
    S.tip = tip;
    if (!tp.xy) S.dugumler.forEach(function (n) { n.y = "0"; });
    if (!tp.z) S.dugumler.forEach(function (n) { n.z = "0"; });
    S.elemanlar.forEach(function (e) { tp.oz.forEach(function (p) { if (bos(e[p])) e[p] = OZ_VARSAYILAN[p]; }); if (!tp.zemin) e.zemin = ""; });
    if (!tp.q) S.yayili = [];
    if (!tp.qz) S.yayili.forEach(function (y) { y.qz = ""; });
    S.mesnetler.forEach(function (m) { if (tip === "kiris" && !m.uy && m.ux) m.uy = true; });
    // düzlemdeki M / kr ile uzaydaki Mz / krz aynı bileşendir: tür değişince taşınır
    S.yukler.forEach(function (y) {
      if (tp.yuk.indexOf("Mz") >= 0) { if (bos(y.Mz) && !bos(y.M)) y.Mz = y.M; y.M = ""; }
      else if (tp.yuk.indexOf("M") >= 0) { if (bos(y.M) && !bos(y.Mz)) y.M = y.Mz; y.Mz = ""; }
    });
    S.yaylar.forEach(function (y) {
      if (tp.yay.indexOf("krz") >= 0) { if (bos(y.krz) && !bos(y.kr)) y.krz = y.kr; y.kr = ""; }
      else if (tp.yay.indexOf("kr") >= 0) { if (bos(y.kr) && !bos(y.krz)) y.kr = y.krz; y.krz = ""; }
    });
    sonucuTemizle();
    modeliGoster();
  }
  function ornekYukle(ad) {
    ref.aciklama.textContent = "Örnek yükleniyor…";
    return A.motorIstegi({ islem: "se_ornek", girdi: { ad: ad } }).then(function (y) {
      if (y.hata || !y.model) { hataGoster(ref.hata, [y.hata || "Örnek alınamadı."]); return; }
      S = modelYukle(y.model);
      sonucuTemizle();
      modeliGoster();
    }).catch(function (e) {
      hataGoster(ref.hata, ["Örnek yüklenemedi: " + (e && e.message ? e.message : e)]);
    });
  }
  function jsonUygula() {
    let m;
    try { m = JSON.parse(ref.json.value); }
    catch (e) { hataGoster(ref.jsonHata, ["JSON okunamadı: " + e.message + ". Virgül, tırnak ve parantezleri kontrol edin."]); return; }
    try { S = modelYukle(m); }
    catch (e) { hataGoster(ref.jsonHata, [e.message]); return; }
    sonucuTemizle();
    ref.ornek.value = "";
    modeliGoster();
  }

  // ---------- Çözüm ve sonuç ----------
  function coz() {
    if (cozuluyor) return;
    const hatalar = dogrula();
    hataGoster(ref.hata, hatalar, hatalar.length > 1 ? "Modelde düzeltilecek yerler var:" : "");
    if (hatalar.length) { ref.hata.scrollIntoView({ block: "nearest", behavior: "smooth" }); return; }
    cozuluyor = true;
    ref.coz.disabled = true;
    ref.coz.textContent = "Çözülüyor…";
    A.motorIstegi({ islem: "se_coz", girdi: { model: temizModel() } }).then(function (y) {
      if (y.hata) {
        sonucuTemizle();
        hataGoster(ref.hata, [y.hata], y.hata_turu === "motor" ? "Motor hatası" : "Model çözülemedi");
        return;
      }
      hataGoster(ref.hata, []);
      SON = { y: y, veri: y.veri };
      sonucuCiz();
      ref.sonuc.scrollIntoView({ block: "start", behavior: "smooth" });
    }).catch(function (e) {
      hataGoster(ref.hata, [(e && e.message) ? e.message : String(e)], "Çözüm çalıştırılamadı");
    }).then(function () {
      cozuluyor = false;
      ref.coz.disabled = false;
      ref.coz.textContent = "Çöz";
    });
  }
  function tabloSonuc(basliklar, satirlar) {
    return '<div class="se-tablo-kutu"><table class="se-sonuc-tablo"><thead><tr>' + basliklar.map(function (h) { return "<th>" + kacis(h) + "</th>"; }).join("") +
      "</tr></thead><tbody>" + satirlar.map(function (r) { return "<tr>" + r.map(function (c, i) { return (i ? "<td class=\"sayi\">" : "<th scope=\"row\">") + kacis(c) + (i ? "</td>" : "</th>"); }).join("") + "</tr>"; }).join("") + "</tbody></table></div>";
  }
  function sonucuCiz() {
    if (!SON) return;
    const v = SON.veri, tip = v.tip, tp = TIPLER[tip] || TIPLER[S.tip], b = birimler(v.birim), uc = ucBoyut(tip);
    const sayisal = sayisalMi(v);
    const mb = b.f + "·" + b.l;
    let h = '<div class="se-eski gizli" id="se-eski">Model değişti: aşağıdaki sonuçlar önceki modele aittir. Yeniden çözmek için “Çöz” düğmesine bas.</div>';
    h += '<div class="se-ozet"><span class="se-rozet">' + kacis(v.mod === "sayisal" ? "Sayısal çözüm" : v.mod === "kesin" ? "Kesin (rasyonel) çözüm" : "Sembolik çözüm") + "</span>" +
      '<span class="se-rozet">' + v.sd_sayisi + " serbestlik derecesi</span><span class=\"se-rozet\">" + v.elemanlar.length + " eleman</span>" +
      (uc ? '<span class="se-rozet">3 boyutlu</span>' : "") + "</div>";
    if (!sayisal) {
      h += '<p class="not">Girdi harf (sembol) içerdiği için sayısal şekil çizilmez; ifadeler aşağıdaki tablolarda ve adım adım anlatımdadır.</p>';
    } else {
      h += '<section class="se-bolum"><h3>Deforme şekil</h3><div class="se-olcek"><label for="se-olcek">Ölçek</label>' +
        '<input type="range" id="se-olcek" min="0" max="200" step="5" value="' + olcekYuzde + '" aria-label="Deformasyon ölçeği">' +
        '<output id="se-olcek-d" class="se-olcek-d"></output></div><div class="se-sekil" id="se-def-sekil"></div>' +
        '<p class="not">Soluk çizgi yük altındaki değil, özgün yapıdır; mavi çizgi büyütülmüş deforme şekildir (gerçek yer değiştirmeler çok küçüktür).' +
        (uc ? " 3B şekil yukarıdaki “Döndür / Eğim” kaydırıcılarıyla çevrilir." : "") + "</p></section>";
      const hepsi = diyagramTurleri(tip);
      const turler = hepsi.filter(function (t) {
        return v.elemanlar.some(function (e) { return (e.diyagram[t] || []).some(function (x) { return Math.abs(x) > 1e-9; }); });
      });
      if (turler.indexOf(diyagramTuru) < 0) diyagramTuru = turler.indexOf("M") >= 0 ? "M" : turler[0] || "N";
      h += '<section class="se-bolum"><h3>Kesit tesir diyagramları</h3><div class="se-seg" role="group" aria-label="Diyagram türü">' +
        hepsi.map(function (t) {
          return '<button type="button" class="se-seg-d" data-dgm="' + t + '" aria-pressed="' + (t === diyagramTuru) + '"' + (turler.indexOf(t) < 0 ? " disabled" : "") + ">" + kacis(DIYAGRAM[t].ad) + "</button>";
        }).join("") + '</div><div class="se-sekil" id="se-dgm-sekil"></div>' +
        '<p class="not" id="se-dgm-not"></p>';
      const kol = tip === "kiris" ? ["V", "M"] : (tip === "cerceve" ? ["N", "V", "M"] : (tip === "cerceve3b" ? ["N", "V", "M", "Vz", "My", "T"] : ["N"]));
      const kolAd = { N: "N (" + b.f + ")", V: "Vmaks (" + b.f + ")", M: "Mmaks (" + mb + ")", Vz: "Vz,maks (" + b.f + ")", My: "My,maks (" + mb + ")", T: "T (" + mb + ")" };
      const bas = ["Eleman", "L (" + b.l + ")"].concat(kol.map(function (t) { return kolAd[t]; })).concat(["Durum"]);
      const sat = v.elemanlar.map(function (e) {
        return ["e" + e.no, fmt(e.L)].concat(kol.map(function (t) { return t === "N" ? fmt(e.N) : fmt(enBuyuk(e.diyagram[t])); })).concat([e.durum || "—"]);
      });
      h += tabloSonuc(bas, sat);
      h += "</section>";
    }
    // Tepkiler
    const tkol = tp.yuk;
    const tepSat = (v.tepkiler || []).map(function (r) { return ["Düğüm " + r.dugum].concat(tkol.map(function (f) { return fmt(r[f]); })); });
    h += '<section class="se-bolum"><h3>Mesnet tepkileri</h3>' +
      (tepSat.length ? tabloSonuc(["Mesnet"].concat(tkol.map(function (f) { return f.charAt(0) === "M" ? f + " (" + mb + ")" : f + " (" + b.f + ")"; })), tepSat)
        : '<p class="not">Mesnet yok: yapıyı yaylar ve/veya zemin taşıyor.</p>');
    if (v.yaylar && v.yaylar.length) {
      h += "<h4>Yay (elastik mesnet) kuvvetleri</h4>" + tabloSonuc(["Yay", "k", "u", "Kuvvet = −k·u"], v.yaylar.map(function (y) {
        const uy = (function () { const d = v.dugumler.filter(function (n) { return n.no === y.dugum; })[0]; if (!d) return null; const i = (v.sd_etiketleri || []).indexOf(y.sd); return i >= 0 ? v.u[i] : null; })();
        return ["Düğüm " + y.dugum + " " + y.sd, fmt(y.k), fmt(uy), fmt(y.kuvvet) + " " + (y.bilesen.charAt(0) === "M" ? mb : b.f)];
      }));
    }
    if (v.cokmeler && v.cokmeler.length) {
      h += '<p class="not">Verilen yer değiştirmeler: ' + v.cokmeler.map(function (c) { return "düğüm " + c.dugum + " " + c.sd + " = " + fmt(c.deger); }).join(", ") + ". Tepkiler bu çökmeleri de içerir (K_fs·u_s).</p>";
    }
    const dn = v.denge || {};
    const dengeAnahtar = uc ? ["Fx", "Fy", "Fz", "Mx", "My", "Mz"] : ["Fx", "Fy", "M"];
    const dengeTamam = dengeAnahtar.every(function (k) { return dn[k] == null || typeof dn[k] !== "number" || Math.abs(dn[k]) < 1e-6; });
    h += '<p class="se-denge ' + (dengeTamam ? "tamam" : "sorun") + '"><strong>Denge kontrolü ' + (dengeTamam ? "sağlandı" : "sağlanmadı") + ":</strong> " +
      dengeAnahtar.map(function (k) { return "Σ" + k + " = " + fmt(dn[k]); }).join(", ") +
      " (dış yükler + tepkiler" + ((v.yaylar && v.yaylar.length) ? " + yay kuvvetleri" : "") + (v.elemanlar.some(function (e) { return e.zemin; }) ? " + zemin kuvvetleri" : "") + ")</p></section>";
    // Yer değiştirmeler
    const etik = v.sd_etiketleri || [];
    const yd = v.dugumler.map(function (n) {
      return ["Düğüm " + n.no, (n.sd || []).map(function (sd, i) { return (etik[sd - 1] || "sd" + sd) + " = " + fmt(n.u[i]); }).join(";  ")];
    });
    h += '<section class="se-bolum"><h3>Düğüm yer değiştirmeleri</h3>' +
      '<div class="se-tablo-kutu"><table class="se-sonuc-tablo"><tbody>' + yd.map(function (r) { return '<tr><th scope="row">' + kacis(r[0]) + "</th><td>" + kacis(r[1]) + "</td></tr>"; }).join("") + "</tbody></table></div>" +
      '<p class="not">Ötelemeler ' + kacis(b.l) + ", dönmeler radyan cinsindendir.</p></section>";
    // Anlatım
    h += '<details class="katlanir se-anlatim-kutu" id="se-anlatim-kutu"><summary>Adım adım çözüm anlatımı</summary><div class="anlatim se-anlatim" id="se-anlatim"></div></details>';
    ref.sonuc.innerHTML = h;
    const an = document.getElementById("se-anlatim");
    A.semaOlaylariBagla(an);
    const kutu = document.getElementById("se-anlatim-kutu");
    let cizildi = false;
    kutu.addEventListener("toggle", function () {
      if (kutu.open && !cizildi) { cizildi = true; A.anlatimDersCiz(SON.y, an); }
    });
    if (sayisal) { deformeyiCiz(); diyagramiCiz(); }
  }
  function deformeyiCiz() {
    const kap = document.getElementById("se-def-sekil");
    if (!kap || !SON || !sayisalMi(SON.veri)) return;
    const r = deformeSekli(SON.veri, genislik(kap), olcekYuzde);
    kap.innerHTML = r.svg;
    const d = document.getElementById("se-olcek-d");
    if (d) d.textContent = olcekYuzde === 0 ? "yük yok (özgün)" : "×" + fmt(r.k);
  }
  function diyagramiCiz() {
    const kap = document.getElementById("se-dgm-sekil");
    if (!kap || !SON || !sayisalMi(SON.veri)) return;
    kap.innerHTML = diyagramSekli(SON.veri, genislik(kap), diyagramTuru);
    const b = birimler(SON.veri.birim);
    const nt = document.getElementById("se-dgm-not");
    if (nt) nt.textContent = (diyagramTuru === "M" || diyagramTuru === "My")
      ? (diyagramTuru === "My" ? "My, elemanın yerel z′ yönünde ve çekilen lif tarafına çizilir; " : "M, çekilen (gerilen) lif tarafına çizilir; ") + "etiketler elemandaki en büyük mutlak değerdir (" + b.f + "·" + b.l + ")."
      : (diyagramTuru === "T" ? "Burulma momenti T eleman boyunca sabittir (" + b.f + "·" + b.l + ")." : "Etiketler her elemandaki en büyük mutlak değerdir (" + b.f + "). N çekme pozitiftir." + (diyagramTuru === "Vz" ? " Vz yerel z′ yönündeki kesme kuvvetidir." : ""));
    document.querySelectorAll("#se-sonuc .se-seg-d").forEach(function (d) { d.setAttribute("aria-pressed", String(d.dataset.dgm === diyagramTuru)); });
  }
  function cizimleriYenile() {
    modelSekliniCiz();
    deformeyiCiz();
    diyagramiCiz();
  }

  // ---------- Olaylar ----------
  function olaylariBagla() {
    kok.addEventListener("input", function (e) {
      const el = e.target;
      if (el.id === "se-olcek") { olcekYuzde = +el.value || 0; deformeyiCiz(); return; }
      if (el.id === "se-bakis-fi" || el.id === "se-bakis-psi") {
        bakis[el.id === "se-bakis-fi" ? "fi" : "psi"] = +el.value || 0;
        cizimleriYenile();
        return;
      }
      if (el.classList.contains("se-g")) {
        const dizi = S[el.dataset.t], i = +el.dataset.i;
        if (dizi && dizi[i]) { dizi[i][el.dataset.a] = el.value; modelDegisti(); }
      }
    });
    kok.addEventListener("change", function (e) {
      const el = e.target;
      if (el.id === "se-ornek") { if (el.value) ornekYukle(el.value); return; }
      if (el.id === "se-tip") { tipDegistir(el.value); return; }
      if (el.type === "checkbox" && el.dataset.t) {
        const dizi = S[el.dataset.t], i = +el.dataset.i;
        if (dizi && dizi[i]) { dizi[i][el.dataset.a] = el.checked; modelDegisti(); }
      }
    });
    kok.addEventListener("focusout", function (e) {
      if (e.target === ref.json) jsonSenkron();
    });
    kok.addEventListener("click", function (e) {
      const t = e.target.closest("button");
      if (!t) return;
      if (t.id === "se-coz") { coz(); return; }
      if (t.id === "se-json-uygula") { jsonUygula(); return; }
      if (t.dataset.ekle) { yeniSatir(t.dataset.ekle); tablolariKur(); modelDegisti(); return; }
      if (t.dataset.sil) {
        const p = t.dataset.sil.split(":");
        if (S[p[0]]) { S[p[0]].splice(+p[1], 1); tablolariKur(); modelDegisti(); }
        return;
      }
      if (t.dataset.dgm && !t.disabled) { diyagramTuru = t.dataset.dgm; diyagramiCiz(); }
    });
  }

  // ---------- Başlatma ----------
  function baslat() {
    iskeletKur();
    olaylariBagla();
    modeliGoster();
    ref.aciklama.textContent = "Örnekler motordan yükleniyor…";
    A.motorIstegi({ islem: "se_ornekler", girdi: {} }).then(function (y) {
      if (y.hata) { hataGoster(ref.hata, [y.hata]); return; }
      ornekler = y.ornekler || [];
      const grup = { yay: "Yay ve çubuk", cubuk: "Yay ve çubuk", kafes: "Düzlem kafes", kiris: "Kiriş ve temel kirişi", cerceve: "Düzlem çerçeve (kolon–kiriş–temel)", kafes3b: "Uzay kafes (3B)", cerceve3b: "Uzay çerçeve (3B)" };
      let h = '<option value="">Kendi modelim</option>', acik = null;
      ornekler.forEach(function (o) {
        const g = grup[o.tip] || o.tip;
        if (g !== acik) { if (acik) h += "</optgroup>"; h += '<optgroup label="' + kacis(g) + '">'; acik = g; }
        h += '<option value="' + kacis(o.ad) + '">' + kacis(o.baslik) + "</option>";
      });
      if (acik) h += "</optgroup>";
      ref.ornek.innerHTML = h;
      const ilk = ornekler.filter(function (o) { return o.ad === "kiris-basit-yayili"; })[0] || ornekler[0];
      if (ilk) { ref.ornek.value = ilk.ad; return ornekYukle(ilk.ad); }
    }).catch(function (e) {
      hataGoster(ref.hata, ["Sonlu eleman motoru yüklenemedi: " + (e && e.message ? e.message : e)]);
    });
  }
  function acilis() {
    if (typeof ResizeObserver !== "function") { basladi = true; baslat(); return; }
    let bekleyen = 0;
    new ResizeObserver(function () {
      const w = kok.clientWidth;
      if (!w) return;
      if (!basladi) { basladi = true; sonGenislik = w; baslat(); return; }
      if (Math.abs(w - sonGenislik) < 40) return;
      sonGenislik = w;
      cancelAnimationFrame(bekleyen);
      bekleyen = requestAnimationFrame(cizimleriYenile);
    }).observe(kok);
  }
  acilis();
})();
