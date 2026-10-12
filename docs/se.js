/* Matris Öğren - Sonlu eleman sayfası (#se).
   Motor (sonlu_eleman.py) web_kopru.py üzerinden "se_ornekler", "se_ornek" ve "se_coz" işlemleriyle çağrılır.
   Bu dosya yalnız arayüzdür: model düzenleme (tablolar + JSON), şekiller (SVG), sonuç tabloları ve anlatım.
   app.js'ten window.MatrisApp ile yalnız motorIstegi, anlatimDersCiz, semaOlaylariBagla ve kacis kullanılır. */
(function () {
  "use strict";
  const A = window.MatrisApp;
  const kok = document.getElementById("se-kok");
  if (!A || !kok) return;
  const kacis = A.kacis;

  // ---------- Model türleri ----------
  const TIPLER = {
    yay:     { ad: "Yay (1B)",          oz: ["k"],           mes: ["ux"],             yuk: ["Fx"],             xy: false, q: false },
    cubuk:   { ad: "Eksenel çubuk (1B)", oz: ["E", "A"],      mes: ["ux"],             yuk: ["Fx"],             xy: false, q: false },
    kafes:   { ad: "Kafes (2B)",         oz: ["E", "A"],      mes: ["ux", "uy"],       yuk: ["Fx", "Fy"],       xy: true,  q: false },
    kiris:   { ad: "Kiriş",              oz: ["E", "I"],      mes: ["uy", "rz"],       yuk: ["Fy", "M"],        xy: false, q: true },
    cerceve: { ad: "Çerçeve (2B)",       oz: ["E", "A", "I"], mes: ["ux", "uy", "rz"], yuk: ["Fx", "Fy", "M"],  xy: true,  q: true },
  };
  const TIP_SIRA = ["yay", "cubuk", "kafes", "kiris", "cerceve"];
  const OZ_ETIKET = { k: "k (kN/m)", E: "E (kN/m²)", A: "A (m²)", I: "I (m⁴)" };
  const OZ_VARSAYILAN = { k: "1000", E: "200e6", A: "0.01", I: "1e-4" };
  const MES_ETIKET = { ux: "ux", uy: "uy", rz: "rz" };
  const YUK_ETIKET = { Fx: "Fx (kN)", Fy: "Fy (kN)", M: "M (kN·m)" };

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
  const ref = {};

  function bosModel(tip) {
    return { tip: tip, baslik: "", aciklama: "", birim: { kuvvet: "kN", uzunluk: "m" }, dugumler: [], elemanlar: [], mesnetler: [], yukler: [], yayili: [] };
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

  // ---------- Modelden geometri ----------
  function geometri(m) {
    const xy = TIPLER[m.tip].xy;
    const d = {};
    m.dugumler.forEach(function (n) {
      const no = tamSayi(n.no), x = sayiOku(n.x), y = xy ? sayiOku(n.y) : 0;
      if (no != null && x != null && y != null) d[no] = { no: no, x: x, y: y };
    });
    const e = [];
    m.elemanlar.forEach(function (el, k) {
      const a = d[tamSayi(el.i)], b = d[tamSayi(el.j)];
      if (a && b && a !== b && (a.x !== b.x || a.y !== b.y)) e.push({ no: tamSayi(el.no) != null ? tamSayi(el.no) : k + 1, a: a, b: b });
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

  // ---------- Mesnet sembolleri ----------
  function mesnetTuru(tip, m) {
    const ux = !!m.ux, uy = !!m.uy, rz = !!m.rz;
    if (tip === "yay" || tip === "cubuk") return ux ? "duvar" : null;
    if (tip === "kiris") return uy && rz ? "duvar" : uy ? "sabit" : rz ? "kare" : null;
    if (tip === "kafes") return ux && uy ? "sabit" : (ux || uy) ? "makara" : null;
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

  // ---------- Yük sembolleri ----------
  function yukOku(s) {
    const t = str(s).trim();
    if (t === "") return null;
    const n = sayiOku(t);
    if (n != null) return n === 0 ? null : { isaret: n > 0 ? 1 : -1, etiket: fmt(Math.abs(n)) };
    return { isaret: t.charAt(0) === "-" ? -1 : 1, etiket: t.replace(/^[+-]\s*/, "") };
  }
  function kuvvetOku(px, py, dx, dy, etiket) {
    const L = 36, t0 = [px - dx * (L + 6), py - dy * (L + 6)], t1 = [px - dx * 6, py - dy * 6];
    let s = '<path class="se-yuk-c" d="M' + pt(t0[0], t0[1]) + " L" + pt(t1[0] - dx * 2, t1[1] - dy * 2) + '"/>' + okBasi(t1[0], t1[1], dx, dy, "se-yuk-o");
    if (Math.abs(dx) > Math.abs(dy)) {
      const w = 6.6 * etiket.length, orta = (t0[0] + t1[0]) / 2;
      s += metinSvg(Math.max(4 + w / 2, Math.min(cizimGenislik - 4 - w / 2, orta)), t0[1] - 8, etiket, "se-etiket se-yuk-t", "middle");
    } else s += metinSvg(Math.max(4 + 3.3 * etiket.length, Math.min(cizimGenislik - 4 - 3.3 * etiket.length, t0[0])), dy > 0 ? t0[1] - 6 : t0[1] + 14, etiket, "se-etiket se-yuk-t", "middle");
    return s;
  }
  function momentOku(px, py, isaret, etiket) {
    const r = 17, d2r = Math.PI / 180;
    const nok = function (aci) { return [px + r * Math.cos(aci * d2r), py - r * Math.sin(aci * d2r)]; };
    const ccw = isaret > 0;
    const bas = ccw ? nok(-30) : nok(210), son = ccw ? nok(205) : nok(-25);
    const teg = ccw ? [-Math.sin(205 * d2r), -Math.cos(205 * d2r)] : [Math.sin(-25 * d2r), Math.cos(-25 * d2r)];
    const yol = "M" + pt(bas[0], bas[1]) + " A" + r + "," + r + " 0 1," + (ccw ? 0 : 1) + " " + pt(son[0], son[1]);
    return '<path class="se-yuk-c" d="' + yol + '"/>' + okBasi(son[0] + teg[0] * 4, son[1] + teg[1] * 4, teg[0], teg[1], "se-yuk-o") +
      metinSvg(px, py - r - 7, etiket, "se-etiket se-yuk-t", "middle");
  }
  function yayiliOku(a, b, T, q, kuvvetBirim) {
    // a, b: ekran noktaları; yön: yerel +y (elemanın solu); q > 0 yerel +y yönünde
    const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
    const ux = dx / L, uy = dy / L;
    const nx = uy, ny = -ux;                  // ekranda elemanın solu (dünya n = (-s, c) -> ekran (-s, -c) ile aynı)
    const fx = nx * q.isaret, fy = ny * q.isaret;   // kuvvet yönü
    const n = Math.max(3, Math.min(14, Math.floor(L / 24)));
    const h = 28;
    let s = "";
    const bas = [a[0] - fx * h, a[1] - fy * h], son = [b[0] - fx * h, b[1] - fy * h];
    s += '<path class="se-yuk-c" d="M' + pt(bas[0], bas[1]) + " L" + pt(son[0], son[1]) + '"/>';
    for (let k = 0; k < n; k++) {
      const t = n === 1 ? 0.5 : k / (n - 1);
      const px = a[0] + dx * t, py = a[1] + dy * t;
      s += '<path class="se-yuk-c" d="M' + pt(px - fx * h, py - fy * h) + " L" + pt(px - fx * 2, py - fy * 2) + '"/>' + okBasi(px, py, fx, fy, "se-yuk-o");
    }
    const etq = "q = " + (q.isaret < 0 ? "−" : "") + q.etiket + " " + kuvvetBirim + "/m", yar = 3.3 * etq.length;
    const mx = Math.max(4 + yar, Math.min(cizimGenislik - 4 - yar, (bas[0] + son[0]) / 2 - fx * 8)), my = (bas[1] + son[1]) / 2 - fy * 8;
    s += metinSvg(mx, my + (Math.abs(fy) > 0.5 ? (fy > 0 ? -1 : 11) : 4), etq, "se-etiket se-yuk-t", "middle");
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
    const T = donusum(dugumler.map(function (n) { return [n.x, n.y]; }), W, { minH: 150 });
    const N = {};
    dugumler.forEach(function (n) { N[n.no] = [T.x(n.x), T.y(n.y)]; });
    let s = "";
    // elemanlar
    g.e.forEach(function (e) {
      const a = N[e.a.no], c = N[e.b.no];
      if (tip === "yay") {
        const dx = c[0] - a[0], dy = c[1] - a[1], L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, px = -uy, py = ux;
        const bas = Math.min(L * 0.2, 18), hl = L - 2 * bas, z = 8;
        let d = "M" + pt(a[0], a[1]) + " L" + pt(a[0] + ux * bas, a[1] + uy * bas);
        for (let k = 0; k < z; k++) {
          const t = (k + 0.5) / z, o = (k % 2 === 0 ? 1 : -1) * 7;
          d += " L" + pt(a[0] + ux * (bas + hl * t) + px * o, a[1] + uy * (bas + hl * t) + py * o);
        }
        d += " L" + pt(c[0] - ux * bas, c[1] - uy * bas) + " L" + pt(c[0], c[1]);
        s += '<path class="se-eleman se-yay" d="' + d + '"/>';
      } else {
        s += '<path class="se-eleman' + (tip === "kafes" ? " se-kafes" : "") + '" d="M' + pt(a[0], a[1]) + " L" + pt(c[0], c[1]) + '"/>';
      }
    });
    // yayılı yükler
    if (tp.q) {
      S.yayili.forEach(function (y) {
        const q = yukOku(y.q), eno = tamSayi(y.eleman);
        if (!q || eno == null) return;
        const e = g.e.filter(function (x) { return x.no === eno; })[0];
        if (!e) return;
        s += yayiliOku(N[e.a.no], N[e.b.no], T, q, b.f);
      });
    }
    // mesnetler
    const bagli = {};
    g.e.forEach(function (e) {
      [[e.a, e.b], [e.b, e.a]].forEach(function (cift) {
        const p = N[cift[0].no], q = N[cift[1].no], L = Math.hypot(q[0] - p[0], q[1] - p[1]) || 1;
        (bagli[cift[0].no] = bagli[cift[0].no] || []).push([(q[0] - p[0]) / L, (q[1] - p[1]) / L]);
      });
    });
    S.mesnetler.forEach(function (m) {
      const no = tamSayi(m.dugum), p = N[no];
      if (!p) return;
      const tur = mesnetTuru(tip, m);
      if (!tur) return;
      const v = bagli[no] || [];
      const ort = v.length ? [v.reduce(function (t, x) { return t + x[0]; }, 0) / v.length, v.reduce(function (t, x) { return t + x[1]; }, 0) / v.length] : [0, 0];
      s += mesnetCiz(p[0], p[1], tur, yonSec(tip, m, tur, ort));
    });
    // düğüm yükleri
    S.yukler.forEach(function (y) {
      const p = N[tamSayi(y.dugum)];
      if (!p) return;
      const fx = tp.yuk.indexOf("Fx") >= 0 ? yukOku(y.Fx) : null, fy = tp.yuk.indexOf("Fy") >= 0 ? yukOku(y.Fy) : null, m = tp.yuk.indexOf("M") >= 0 ? yukOku(y.M) : null;
      if (fx) s += kuvvetOku(p[0], p[1], fx.isaret, 0, fx.etiket + " " + b.f);
      if (fy) s += kuvvetOku(p[0], p[1], 0, -fy.isaret, fy.etiket + " " + b.f);
      if (m) s += momentOku(p[0], p[1], m.isaret, m.etiket + " " + b.f + "·" + b.l);
    });
    // düğümler ve numaralar
    dugumler.forEach(function (n) {
      const p = N[n.no];
      s += '<circle class="se-dugum" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="' + (tip === "kafes" ? 5 : 4) + '"/>';
      s += metinSvg(p[0] + 8, p[1] - 8, String(n.no), "se-no");
    });
    g.e.forEach(function (e) {
      const a = N[e.a.no], c = N[e.b.no], dx = c[0] - a[0], dy = c[1] - a[1], L = Math.hypot(dx, dy) || 1;
      s += metinSvg((a[0] + c[0]) / 2 + (dy / L) * 11, (a[1] + c[1]) / 2 - (dx / L) * 11 + 4, "e" + e.no, "se-eno", "middle");
    });
    return svgSar(T, s, "Yapı modeli: " + dugumler.length + " düğüm, " + g.e.length + " eleman");
  }

  // ---------- Deforme şekil ----------
  function yerDegistirme(tip, u) {
    u = u || [];
    const z = function (i) { return typeof u[i] === "number" ? u[i] : 0; };
    if (tip === "kafes") return [z(0), z(1), 0];
    if (tip === "kiris") return [0, z(0), z(1)];
    if (tip === "cerceve") return [z(0), z(1), z(2)];
    return [z(0), 0, 0];
  }
  function sayisalMi(veri) {
    if (!veri || !veri.u || !veri.elemanlar) return false;
    if (!veri.u.every(function (x) { return typeof x === "number"; })) return false;
    return veri.elemanlar.every(function (e) {
      const d = e.diyagram;
      return d && d.x && [d.x, d.N, d.V, d.M].every(function (dz) { return dz.every(function (x) { return typeof x === "number"; }); });
    });
  }
  // Bir elemanın birim ölçekteki yer değiştirme örnekleri: [gx, gy] (dünya), n+1 nokta
  function elemanEgrisi(e, nd, tip, n) {
    const a = nd[e.dugumler[0]], b = nd[e.dugumler[1]];
    const ua = yerDegistirme(tip, a.u), ub = yerDegistirme(tip, b.u);
    const c = e.c, s = e.s, L = e.L;
    const eg = tip === "kiris" || tip === "cerceve";
    const ul1 = c * ua[0] + s * ua[1], vl1 = -s * ua[0] + c * ua[1], t1 = ua[2];
    const ul2 = c * ub[0] + s * ub[1], vl2 = -s * ub[0] + c * ub[1], t2 = ub[2];
    const out = [];
    for (let m = 0; m <= n; m++) {
      const xi = m / n, x2 = xi * xi, x3 = x2 * xi;
      const ul = ul1 + (ul2 - ul1) * xi;
      const vl = eg ? vl1 * (1 - 3 * x2 + 2 * x3) + t1 * L * (xi - 2 * x2 + x3) + vl2 * (3 * x2 - 2 * x3) + t2 * L * (-x2 + x3) : vl1 + (vl2 - vl1) * xi;
      out.push([c * ul - s * vl, s * ul + c * vl, a.x + (b.x - a.x) * xi, a.y + (b.y - a.y) * xi]);
    }
    return out;
  }
  function deformeVeri(veri) {
    const tip = veri.tip, nd = {};
    veri.dugumler.forEach(function (d) { nd[d.no] = d; });
    const n = tip === "kiris" || tip === "cerceve" ? 20 : 1;
    const egriler = veri.elemanlar.map(function (e) { return elemanEgrisi(e, nd, tip, n); });
    let maks = 0, x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    egriler.forEach(function (eg) {
      eg.forEach(function (p) {
        maks = Math.max(maks, Math.hypot(p[0], p[1]));
        x0 = Math.min(x0, p[2]); x1 = Math.max(x1, p[2]); y0 = Math.min(y0, p[3]); y1 = Math.max(y1, p[3]);
      });
    });
    const aralik = Math.max(x1 - x0, y1 - y0) || 1;
    return { tip: tip, nd: nd, egriler: egriler, maks: maks, otomatik: maks > 1e-15 ? 0.1 * aralik / maks : 1 };
  }
  function deformeSekli(veri, W, yuzde) {
    const dv = deformeVeri(veri), tip = veri.tip;
    const k = dv.otomatik * yuzde / 100, kSinir = dv.otomatik * 1.5;
    const birDim = tip === "yay" || tip === "cubuk";
    const pts = [];
    dv.egriler.forEach(function (eg) { eg.forEach(function (p) { pts.push([p[2], p[3]]); pts.push([p[2] + kSinir * p[0], p[3] + kSinir * p[1]]); }); });
    const T = donusum(pts, W, birDim ? { minH: 190, pu: 40, pa: 60 } : { minH: 150 });
    const kayma = birDim ? 40 : 0;       // 1B modelde deforme çizgi özgün çizginin altına alınır
    const Y0 = birDim ? T.H * 0.34 : 0;
    const ekran = function (x, y, dx, dy) { return [T.x(x + k * dx), (birDim ? Y0 + kayma : T.y(y + k * dy))]; };
    let s = "";
    // özgün yapı (soluk) ve mesnetler
    veri.elemanlar.forEach(function (e, i) {
      const eg = dv.egriler[i], a = eg[0], c = eg[eg.length - 1];
      const A1 = [T.x(a[2]), birDim ? Y0 : T.y(a[3])], B1 = [T.x(c[2]), birDim ? Y0 : T.y(c[3])];
      s += '<path class="se-asil" d="M' + pt(A1[0], A1[1]) + " L" + pt(B1[0], B1[1]) + '"/>';
    });
    // deforme şekil
    veri.elemanlar.forEach(function (e, i) {
      const eg = dv.egriler[i];
      let d = "";
      eg.forEach(function (p, m) {
        const q = ekran(p[2], p[3], p[0], p[1]);
        d += (m ? " L" : "M") + pt(q[0], q[1]);
      });
      s += '<path class="se-def" d="' + d + '"/>';
    });
    veri.dugumler.forEach(function (n) {
      const u = yerDegistirme(tip, n.u);
      const q = ekran(n.x, n.y, u[0], u[1]);
      const o = [T.x(n.x), birDim ? Y0 : T.y(n.y)];
      if (birDim) s += '<path class="se-kilavuz" d="M' + pt(o[0], o[1]) + " L" + pt(q[0], q[1]) + '"/>';
      s += '<circle class="se-dugum se-dugum-d" cx="' + r1(q[0]) + '" cy="' + r1(q[1]) + '" r="4.5"/>';
      s += metinSvg(q[0] + 8, q[1] - 8, String(n.no), "se-no");
    });
    // mesnet sembolleri özgün konumda
    const bagli = {};
    veri.elemanlar.forEach(function (e, i) {
      const eg = dv.egriler[i], a = eg[0], c = eg[eg.length - 1];
      const p = [T.x(a[2]), birDim ? Y0 : T.y(a[3])], q = [T.x(c[2]), birDim ? Y0 : T.y(c[3])], L = Math.hypot(q[0] - p[0], q[1] - p[1]) || 1;
      (bagli[e.dugumler[0]] = bagli[e.dugumler[0]] || []).push([(q[0] - p[0]) / L, (q[1] - p[1]) / L]);
      (bagli[e.dugumler[1]] = bagli[e.dugumler[1]] || []).push([-(q[0] - p[0]) / L, -(q[1] - p[1]) / L]);
    });
    S.mesnetler.forEach(function (m) {
      const no = tamSayi(m.dugum), n = dv.nd[no];
      if (!n) return;
      const tur = mesnetTuru(tip, m);
      if (!tur) return;
      const v = bagli[no] || [];
      const ort = v.length ? [v.reduce(function (t, x) { return t + x[0]; }, 0) / v.length, v.reduce(function (t, x) { return t + x[1]; }, 0) / v.length] : [0, 0];
      s += '<g class="se-soluk">' + mesnetCiz(T.x(n.x), birDim ? Y0 : T.y(n.y), tur, yonSec(tip, m, tur, ort)) + "</g>";
    });
    return { svg: svgSar(T, s, "Deforme şekil, ölçek ×" + fmt(k)), k: k };
  }

  // ---------- Diyagramlar ----------
  const DIYAGRAM = {
    N: { ad: "Normal kuvvet N", sinif: "se-dN", isaret: 1 },
    V: { ad: "Kesme kuvveti V", sinif: "se-dV", isaret: 1 },
    M: { ad: "Eğilme momenti M", sinif: "se-dM", isaret: -1 },
  };
  function diyagramSekli(veri, W, tur) {
    const tip = veri.tip, def = DIYAGRAM[tur], b = birimler(veri.birim);
    const nd = {};
    veri.dugumler.forEach(function (d) { nd[d.no] = d; });
    const pts = veri.dugumler.map(function (n) { return [n.x, n.y]; });
    const T = donusum(pts, W, { minH: 190, pu: 72, pa: 72 });
    let gmaks = 0;
    veri.elemanlar.forEach(function (e) { e.diyagram[tur].forEach(function (v) { gmaks = Math.max(gmaks, Math.abs(v)); }); });
    const kD = gmaks > 1e-12 ? 38 / gmaks : 0;
    let s = "";
    veri.elemanlar.forEach(function (e) {
      const a = nd[e.dugumler[0]], d = e.diyagram;
      const px = T.x(a.x), py = T.y(a.y), dx = e.c, dy = -e.s, nx = -e.s, ny = -e.c;   // ekran: eleman yönü ve +n (sol)
      s += '<path class="se-asil" d="M' + pt(px, py) + " L" + pt(px + dx * e.L * T.s, py + dy * e.L * T.s) + '"/>';
    });
    veri.elemanlar.forEach(function (e) {
      const a = nd[e.dugumler[0]], d = e.diyagram, val = d[tur];
      const px = T.x(a.x), py = T.y(a.y), dx = e.c, dy = -e.s, nx = -e.s, ny = -e.c;
      const taban = [], ust = [];
      d.x.forEach(function (x, i) {
        const bx = px + dx * x * T.s, by = py + dy * x * T.s, o = def.isaret * val[i] * kD;
        taban.push([bx, by]);
        ust.push([bx + nx * o, by + ny * o]);
      });
      let yol = "M" + pt(taban[0][0], taban[0][1]);
      ust.forEach(function (p) { yol += " L" + pt(p[0], p[1]); });
      for (let i = taban.length - 1; i >= 0; i--) yol += " L" + pt(taban[i][0], taban[i][1]);
      s += '<path class="se-dgm ' + def.sinif + '" d="' + yol + ' Z"/>';
      // en büyük mutlak değer etiketi
      let im = 0;
      val.forEach(function (v, i) { if (Math.abs(v) > Math.abs(val[im]) + 1e-12) im = i; });
      if (Math.abs(val[im]) > 1e-9 * Math.max(gmaks, 1e-9) && Math.abs(val[im]) > 1e-9) {
        const sg = def.isaret * val[im] >= 0 ? 1 : -1;
        let ex = ust[im][0] + nx * sg * 11, ey = ust[im][1] + ny * sg * 11;
        const kay = im === 0 ? 18 : im === val.length - 1 ? -18 : 0;
        ex += dx * kay; ey += dy * kay;
        s += metinSvg(ex, ey + 4, fmt(val[im]), "se-etiket", "middle");
      }
    });
    veri.dugumler.forEach(function (n) {
      s += '<circle class="se-dugum" cx="' + r1(T.x(n.x)) + '" cy="' + r1(T.y(n.y)) + '" r="3.5"/>';
    });
    return svgSar(T, s, def.ad + " diyagramı (" + (tur === "M" ? b.f + "·" + b.l : b.f) + ")");
  }
  function enBuyuk(dizi) {
    let m = 0;
    dizi.forEach(function (v) { if (Math.abs(v) > Math.abs(m)) m = v; });
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
    const tp = TIPLER[S.tip];
    const dugum = S.dugumler.map(function (n, i) {
      return "<tr>" + girdiH("dugumler", i, "no", n.no, "no", "numeric") + girdiH("dugumler", i, "x", n.x, "x (m)") +
        (tp.xy ? girdiH("dugumler", i, "y", n.y, "y (m)") : "") + silH("dugumler", i) + "</tr>";
    });
    const eleman = S.elemanlar.map(function (e, i) {
      return "<tr>" + girdiH("elemanlar", i, "no", e.no, "no", "numeric") + girdiH("elemanlar", i, "i", e.i, "i. düğüm", "numeric") + girdiH("elemanlar", i, "j", e.j, "j. düğüm", "numeric") +
        tp.oz.map(function (p) { return girdiH("elemanlar", i, p, e[p], OZ_ETIKET[p], "text"); }).join("") + silH("elemanlar", i) + "</tr>";
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
      return "<tr>" + girdiH("yayili", i, "eleman", y.eleman, "eleman", "numeric") + girdiH("yayili", i, "q", y.q, "q (kN/m)", "text") + silH("yayili", i) + "</tr>";
    });
    let h = tabloH("dugumler", "Düğümler", "", ["No", "x (m)"].concat(tp.xy ? ["y (m)"] : []), dugum, "Düğüm ekle");
    h += tabloH("elemanlar", "Elemanlar", "Her eleman iki düğümü bağlar" + (S.tip === "kiris" ? "; kiriş elemanlarında i. düğüm solda olmalı" : "") + ". E, A, I, k yerine sayı ya da harf (sembol) yazabilirsin.",
      ["No", "i. düğüm", "j. düğüm"].concat(tp.oz.map(function (p) { return OZ_ETIKET[p]; })), eleman, "Eleman ekle");
    h += tabloH("mesnetler", "Mesnetler", "İşaretli yön tutulur: ux yatay, uy düşey, rz dönme.", ["Düğüm"].concat(tp.mes.map(function (f) { return MES_ETIKET[f]; })), mesnet, "Mesnet ekle");
    h += tabloH("yukler", "Düğüm yükleri", "Fx sağa, Fy yukarı, M saat yönünün tersine pozitiftir.", ["Düğüm"].concat(tp.yuk.map(function (f) { return YUK_ETIKET[f]; })), yuk, "Yük ekle");
    if (tp.q) h += tabloH("yayili", "Yayılı yükler", "q elemanın yerel y yönündedir (soldan sağa giden elemanda yukarı); aşağı yük için negatif yaz.", ["Eleman", "q (kN/m)"], yayili, "Yayılı yük ekle");
    ref.tablolar.innerHTML = h;
  }

  // ---------- Model <-> JSON ----------
  function tipAdiSade(t) {
    return str(t).trim().toLowerCase().replace(/ç/g, "c").replace(/ı/g, "i").replace(/ş/g, "s").replace(/ğ/g, "g").replace(/ö/g, "o").replace(/ü/g, "u");
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
    dz(m.dugumler).forEach(function (n, k) { n = n || {}; s.dugumler.push({ no: str(n.no != null ? n.no : k + 1), x: str(n.x != null ? n.x : 0), y: str(n.y != null ? n.y : 0) }); });
    dz(m.elemanlar).forEach(function (e, k) {
      e = e || {};
      const d = dz(e.dugumler);
      s.elemanlar.push({ no: str(e.no != null ? e.no : k + 1), i: str(d[0]), j: str(d[1]), k: str(e.k), E: str(e.E), A: str(e.A), I: str(e.I) });
    });
    dz(m.mesnetler).forEach(function (x) { x = x || {}; s.mesnetler.push({ dugum: str(x.dugum), ux: !!x.ux, uy: !!x.uy, rz: !!x.rz }); });
    dz(m.yukler).forEach(function (y) { y = y || {}; s.yukler.push({ dugum: str(y.dugum), Fx: str(y.Fx), Fy: str(y.Fy), M: str(y.M) }); });
    dz(m.yayili).forEach(function (y) { y = y || {}; s.yayili.push({ eleman: str(y.eleman), q: str(y.q) }); });
    return s;
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
      m.dugumler.push(o);
    });
    S.elemanlar.forEach(function (e) {
      const o = { no: sayiyaDondur(e.no), dugumler: [sayiyaDondur(e.i), sayiyaDondur(e.j)] };
      tp.oz.forEach(function (p) { o[p] = str(e[p]).trim(); });
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
      tp.yuk.forEach(function (f) { if (str(y[f]).trim() !== "") { o[f] = sayiyaDondur(y[f]); bir = true; } });
      if (bir) m.yukler.push(o);
    });
    if (tp.q) {
      m.yayili = [];
      S.yayili.forEach(function (y) {
        if (str(y.q).trim() === "" && str(y.eleman).trim() === "") return;
        m.yayili.push({ eleman: sayiyaDondur(y.eleman), q: sayiyaDondur(y.q) });
      });
      if (!m.yayili.length) delete m.yayili;
    }
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
      dn[no] = { x: sayiOku(n.x), y: tp.xy ? sayiOku(n.y) : 0 };
    });
    const en = {}, bagli = {};
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
          const dx = dn[b].x - dn[a].x, dy = dn[b].y - dn[a].y;
          if (dn[a].x != null && dn[b].x != null && dn[a].y != null && dn[b].y != null) {
            if (Math.hypot(dx, dy) === 0) h.push("Eleman " + no + "'nin boyu sıfır: düğüm " + a + " ve düğüm " + b + " aynı noktada. Koordinatları düzeltin.");
            else if (S.tip === "kiris" && dx < 0) h.push("Eleman " + no + ": kiriş elemanları soldan sağa tanımlanmalı; düğüm sırasını [" + b + ", " + a + "] yapın.");
          }
        }
      }
      tp.oz.forEach(function (p) {
        const t = str(e[p]).trim();
        if (t === "") h.push("Eleman " + no + ": " + p + " değeri boş; bir sayı ya da harf (sembol) yazın.");
        else { const n = sayiOku(t); if (n != null && n <= 0) h.push("Eleman " + no + ": " + p + " pozitif olmalı (girilen: " + t + ")."); }
      });
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
    if (!mesnetVar) h.push("En az bir mesnet (işaretli yön) gerekli; mesnetsiz yapı rijit cisim olarak hareket eder.");
    S.yukler.forEach(function (y, i) {
      const no = tamSayi(y.dugum);
      if (no == null || !dn[no]) h.push("Yük " + (i + 1) + ": düğüm numarası tanımlı bir düğüm olmalı (girilen: “" + str(y.dugum) + "”).");
    });
    if (tp.q) {
      S.yayili.forEach(function (y, i) {
        const no = tamSayi(y.eleman);
        if (no == null || !en[no]) h.push("Yayılı yük " + (i + 1) + ": eleman numarası tanımlı bir eleman olmalı (girilen: “" + str(y.eleman) + "”).");
        else if (str(y.q).trim() === "") h.push("Yayılı yük " + (i + 1) + ": q değeri boş.");
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
      '<div class="se-sekil" id="se-model-sekil"></div>' +
      '<p class="not se-lejant">Mavi numara düğüm, e1, e2… eleman numarasıdır; kırmızı oklar yüklerdir.</p>' +
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
  function modelSekliniCiz() {
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
    if (t === "dugumler") {
      const mak = S.dugumler.reduce(function (m, n) { return Math.max(m, tamSayi(n.no) || 0); }, 0), s = son(S.dugumler);
      const x = s ? sayiOku(s.x) : null;
      S.dugumler.push({ no: String(mak + 1), x: x != null ? String(x + 1) : "0", y: s ? s.y : "0" });
    } else if (t === "elemanlar") {
      const mak = S.elemanlar.reduce(function (m, e) { return Math.max(m, tamSayi(e.no) || 0); }, 0), n = S.dugumler.length;
      const o = { no: String(mak + 1), i: n >= 2 ? S.dugumler[n - 2].no : "", j: n >= 1 ? S.dugumler[n - 1].no : "", k: "", E: "", A: "", I: "" };
      const onceki = son(S.elemanlar);
      TIPLER[S.tip].oz.forEach(function (p) { o[p] = onceki && onceki[p] ? onceki[p] : OZ_VARSAYILAN[p]; });
      S.elemanlar.push(o);
    } else if (t === "mesnetler") {
      S.mesnetler.push({ dugum: S.dugumler.length ? S.dugumler[0].no : "", ux: true, uy: TIPLER[S.tip].mes.indexOf("uy") >= 0, rz: false });
    } else if (t === "yukler") {
      S.yukler.push({ dugum: S.dugumler.length ? S.dugumler[S.dugumler.length - 1].no : "", Fx: "", Fy: "", M: "" });
    } else if (t === "yayili") {
      S.yayili.push({ eleman: S.elemanlar.length ? S.elemanlar[0].no : "", q: "-10" });
    }
  }
  function tipDegistir(tip) {
    if (!TIPLER[tip] || tip === S.tip) return;
    const tp = TIPLER[tip];
    S.tip = tip;
    if (!tp.xy) S.dugumler.forEach(function (n) { n.y = "0"; });
    S.elemanlar.forEach(function (e) { tp.oz.forEach(function (p) { if (!str(e[p]).trim()) e[p] = OZ_VARSAYILAN[p]; }); });
    if (!tp.q) S.yayili = [];
    S.mesnetler.forEach(function (m) { if (tip === "kiris" && !m.uy && m.ux) m.uy = true; });
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
    const v = SON.veri, tip = v.tip, tp = TIPLER[tip] || TIPLER[S.tip], b = birimler(v.birim);
    const sayisal = sayisalMi(v);
    let h = '<div class="se-eski gizli" id="se-eski">Model değişti: aşağıdaki sonuçlar önceki modele aittir. Yeniden çözmek için “Çöz” düğmesine bas.</div>';
    h += '<div class="se-ozet"><span class="se-rozet">' + kacis(v.mod === "sayisal" ? "Sayısal çözüm" : v.mod === "kesin" ? "Kesin (rasyonel) çözüm" : "Sembolik çözüm") + "</span>" +
      '<span class="se-rozet">' + v.sd_sayisi + " serbestlik derecesi</span><span class=\"se-rozet\">" + v.elemanlar.length + " eleman</span></div>";
    if (!sayisal) {
      h += '<p class="not">Girdi harf (sembol) içerdiği için sayısal şekil çizilmez; ifadeler aşağıdaki tablolarda ve adım adım anlatımdadır.</p>';
    } else {
      h += '<section class="se-bolum"><h3>Deforme şekil</h3><div class="se-olcek"><label for="se-olcek">Ölçek</label>' +
        '<input type="range" id="se-olcek" min="0" max="200" step="5" value="' + olcekYuzde + '" aria-label="Deformasyon ölçeği">' +
        '<output id="se-olcek-d" class="se-olcek-d"></output></div><div class="se-sekil" id="se-def-sekil"></div>' +
        '<p class="not">Soluk çizgi yük altındaki değil, özgün yapıdır; mavi çizgi büyütülmüş deforme şekildir (gerçek yer değiştirmeler çok küçüktür).</p></section>';
      const turler = ["N", "V", "M"].filter(function (t) {
        return v.elemanlar.some(function (e) { return e.diyagram[t].some(function (x) { return Math.abs(x) > 1e-9; }); });
      });
      if (turler.indexOf(diyagramTuru) < 0) diyagramTuru = turler.indexOf("M") >= 0 ? "M" : turler[0] || "N";
      h += '<section class="se-bolum"><h3>Kesit tesir diyagramları</h3><div class="se-seg" role="group" aria-label="Diyagram türü">' +
        ["N", "V", "M"].map(function (t) {
          return '<button type="button" class="se-seg-d" data-dgm="' + t + '" aria-pressed="' + (t === diyagramTuru) + '"' + (turler.indexOf(t) < 0 ? " disabled" : "") + ">" + kacis(DIYAGRAM[t].ad) + "</button>";
        }).join("") + '</div><div class="se-sekil" id="se-dgm-sekil"></div>' +
        '<p class="not" id="se-dgm-not"></p>';
      const kol = tip === "kiris" ? ["V", "M"] : (tip === "cerceve" ? ["N", "V", "M"] : ["N"]);
      const bas = ["Eleman", "L (" + b.l + ")"].concat(kol.map(function (t) { return t === "M" ? "Mmaks (" + b.f + "·" + b.l + ")" : (t === "V" ? "Vmaks (" + b.f + ")" : "N (" + b.f + ")"); })).concat(["Durum"]);
      const sat = v.elemanlar.map(function (e) {
        return ["e" + e.no, fmt(e.L)].concat(kol.map(function (t) { return t === "N" ? fmt(e.N) : fmt(enBuyuk(e.diyagram[t])); })).concat([e.durum || "—"]);
      });
      h += tabloSonuc(bas, sat);
      h += "</section>";
    }
    // Tepkiler
    const tkol = tp.yuk.filter(function (f) { return f !== undefined; });
    const tepSat = (v.tepkiler || []).map(function (r) { return ["Düğüm " + r.dugum].concat(tkol.map(function (f) { return fmt(r[f]); })); });
    h += '<section class="se-bolum"><h3>Mesnet tepkileri</h3>' +
      tabloSonuc(["Mesnet"].concat(tkol.map(function (f) { return f === "M" ? "M (" + b.f + "·" + b.l + ")" : f + " (" + b.f + ")"; })), tepSat);
    const dn = v.denge || {};
    const dengeTamam = ["Fx", "Fy", "M"].every(function (k) { return dn[k] == null || typeof dn[k] !== "number" || Math.abs(dn[k]) < 1e-6; });
    h += '<p class="se-denge ' + (dengeTamam ? "tamam" : "sorun") + '"><strong>Denge kontrolü ' + (dengeTamam ? "sağlandı" : "sağlanmadı") + ":</strong> ΣFx = " + fmt(dn.Fx) + ", ΣFy = " + fmt(dn.Fy) + ", ΣM = " + fmt(dn.M) +
      " (dış yükler + tepkiler)</p></section>";
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
    if (nt) nt.textContent = diyagramTuru === "M"
      ? "M, çekilen (gerilen) lif tarafına çizilir; etiketler elemandaki en büyük mutlak değerdir (" + b.f + "·" + b.l + ")."
      : "Etiketler her elemandaki en büyük mutlak değerdir (" + b.f + "). N çekme pozitiftir.";
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
      ref.ornek.innerHTML = '<option value="">Kendi modelim</option>' + ornekler.map(function (o) {
        return '<option value="' + kacis(o.ad) + '">' + kacis(o.baslik) + "</option>";
      }).join("");
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
