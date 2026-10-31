/* Matris Öğren — 3B sahne yardımcıları (window.Cizim3B). Bağımsız modül; bina.js kullanır.
   Bina koordinatı: X sağa (harfli akslar), Y plan derinliği (sayılı akslar), Z yukarı (kot).
   İzdüşüm se.js'teki aksonometri ile aynı φ/ψ kabulüdür: ekran = izdusum_se(x = X, y = Z, z = −Y).
   Her şey SVG metni olarak üretilir (1 birim = 1 px; yakınlaştırma/kaydırma viewBox ile). */
(function () {
  "use strict";

  const GORUNUMLER = {
    "3b": { fi: -32, psi: 22 },
    plan: { fi: 0, psi: 90 },
    on: { fi: 0, psi: 0 },
    yan: { fi: -90, psi: 0 },
  };
  const D2R = Math.PI / 180;

  function kacis(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function r1(v) { return Math.round(v * 10) / 10; }
  function pt(x, y) { return r1(x) + "," + r1(y); }
  function azHareket() {
    try { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); } catch (e) { return false; }
  }

  // ---------- İzdüşüm ----------
  // Bina (X, Y, Z) -> çizim düzlemi (u, v); v yukarı. se.js: u = x cos φ + z sin φ, derin = −x sin φ + z cos φ, v = y cos ψ − derin sin ψ
  function izdusum(X, Y, Z, b) {
    const f = b.fi * D2R, p = b.psi * D2R;
    const z = -Y;
    const u = X * Math.cos(f) + z * Math.sin(f);
    const derin = -X * Math.sin(f) + z * Math.cos(f);
    return [u, Z * Math.cos(p) - derin * Math.sin(p)];
  }
  // İzleyiciye doğru derinlik (büyük = yakın): ressam sıralaması için
  function derinlik(X, Y, Z, b) {
    const f = b.fi * D2R, p = b.psi * D2R;
    const derin = -X * Math.sin(f) + (-Y) * Math.cos(f);
    return Z * Math.sin(p) + derin * Math.cos(p);
  }
  // İzleyiciye bakan birim vektör (bina koordinatında): yüz görünürlüğü için
  function bakisVektoru(b) {
    const f = b.fi * D2R, p = b.psi * D2R;
    return [-Math.sin(f) * Math.cos(p), -Math.cos(f) * Math.cos(p), Math.sin(p)];
  }
  // Dünya yön vektörü -> ekran birim vektörü (y aşağı)
  function yon(v, b) {
    const a = izdusum(0, 0, 0, b), c = izdusum(v[0], v[1], v[2], b);
    const dx = c[0] - a[0], dy = -(c[1] - a[1]), L = Math.hypot(dx, dy);
    return L > 1e-9 ? [dx / L, dy / L] : [0, -1];
  }

  // ---------- Dünya -> ekran dönüşümü (se.js donusum kalıbı; W×H kutuya sığdır) ----------
  function donusum(pts, W, H, o) {
    o = o || {};
    const pl = o.pl != null ? o.pl : 40, pu = o.pu != null ? o.pu : 36, pa = o.pa != null ? o.pa : 36;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    pts.forEach(function (p) {
      if (p[0] < x0) x0 = p[0]; if (p[0] > x1) x1 = p[0];
      if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1];
    });
    if (!isFinite(x0)) { x0 = -1; x1 = 1; y0 = -1; y1 = 1; }
    const dx = Math.max(x1 - x0, 1e-6), dy = Math.max(y1 - y0, 1e-6);
    const aw = Math.max(60, W - 2 * pl), ah = Math.max(60, H - pu - pa);
    const s = Math.min(aw / dx, ah / dy);
    const ox = pl + (aw - dx * s) / 2, oy = pu + (ah - dy * s) / 2;
    return { s: s, W: W, H: H, x: function (v) { return ox + (v - x0) * s; }, y: function (v) { return oy + (y1 - v) * s; } };
  }

  // ---------- Kamera: bakış (φ, ψ) + viewBox (yakınlaştırma / kaydırma) ----------
  function Kamera(W, H) {
    this.bakis = { fi: GORUNUMLER["3b"].fi, psi: GORUNUMLER["3b"].psi };
    this.gorunum = "3b";
    this.W = W; this.H = H;
    this.z = 1; this.px = 0; this.py = 0;    // viewBox = [px, py, W/z, H/z]
    this._anim = 0;
  }
  Kamera.prototype.viewBox = function () {
    return [r1(this.px), r1(this.py), r1(this.W / this.z), r1(this.H / this.z)].join(" ");
  };
  Kamera.prototype.sifirla = function () { this.z = 1; this.px = 0; this.py = 0; };
  Kamera.prototype.boyut = function (W, H) {
    if (W === this.W && H === this.H) return;
    const cx = this.px + this.W / this.z / 2, cy = this.py + this.H / this.z / 2;
    this.W = W; this.H = H;
    this.px = cx - W / this.z / 2; this.py = cy - H / this.z / 2;
  };
  Kamera.prototype.yakinlastir = function (k, cx, cy) {
    // cx, cy: viewBox koordinatında sabit kalacak nokta
    const z0 = this.z, z1 = Math.max(0.4, Math.min(8, z0 * k));
    if (cx == null) { cx = this.px + this.W / z0 / 2; cy = this.py + this.H / z0 / 2; }
    this.px = cx - (cx - this.px) * z0 / z1;
    this.py = cy - (cy - this.py) * z0 / z1;
    this.z = z1;
  };
  Kamera.prototype.kaydir = function (dx, dy) { this.px -= dx; this.py -= dy; };
  Kamera.prototype.dondur = function (dfi, dpsi) {
    this.bakis.fi = ((this.bakis.fi + dfi + 180) % 360 + 360) % 360 - 180;
    this.bakis.psi = Math.max(-10, Math.min(90, this.bakis.psi + dpsi));
    this.gorunum = "serbest";
  };
  // Görünüm geçişi 200 ms (azaltılmış hareket: anında); her karede cb(kamera) çağrılır
  Kamera.prototype.git = function (ad, cb, sure) {
    const hedef = GORUNUMLER[ad];
    if (!hedef) return;
    this.gorunum = ad;
    if (this._anim) { cancelAnimationFrame(this._anim); this._anim = 0; }
    const self = this, b0 = { fi: this.bakis.fi, psi: this.bakis.psi };
    let dfi = hedef.fi - b0.fi;
    if (dfi > 180) dfi -= 360; else if (dfi < -180) dfi += 360;
    const dpsi = hedef.psi - b0.psi;
    sure = sure == null ? 200 : sure;
    if (azHareket() || sure <= 0 || (Math.abs(dfi) < 1e-9 && Math.abs(dpsi) < 1e-9)) {
      this.bakis.fi = hedef.fi; this.bakis.psi = hedef.psi; this.sifirla();
      if (cb) cb(this, true);
      return;
    }
    const t0 = performance.now();
    this.sifirla();
    const kare = function (t) {
      const u = Math.min(1, (t - t0) / sure), e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      self.bakis.fi = b0.fi + dfi * e; self.bakis.psi = b0.psi + dpsi * e;
      self._anim = u < 1 ? requestAnimationFrame(kare) : 0;
      if (u >= 1) { self.bakis.fi = hedef.fi; self.bakis.psi = hedef.psi; }
      if (cb) cb(self, u >= 1);
    };
    this._anim = requestAnimationFrame(kare);
  };
  // İstemci (clientX/Y) -> viewBox koordinatı
  Kamera.prototype.svgNokta = function (svg, cx, cy) {
    const r = svg.getBoundingClientRect();
    if (!r.width || !r.height) return [0, 0];
    const vw = this.W / this.z, vh = this.H / this.z;
    // preserveAspectRatio xMidYMid meet: ölçek = min(r.width/vw, r.height/vh)
    const s = Math.min(r.width / vw, r.height / vh);
    const ox = (r.width - vw * s) / 2, oy = (r.height - vh * s) / 2;
    return [this.px + (cx - r.left - ox) / s, this.py + (cy - r.top - oy) / s];
  };
  // Ekran pikseli başına viewBox birimi (dokunma yarıçapını sabit px tutmak için)
  Kamera.prototype.pxOlcek = function (svg) {
    const r = svg.getBoundingClientRect();
    if (!r.width) return 1;
    const vw = this.W / this.z, vh = this.H / this.z;
    return 1 / Math.min(r.width / vw, r.height / vh);
  };

  // ---------- Sahne: derinlik sıralı parçalar (ressam algoritması) ----------
  function Sahne() { this.parcalar = []; this.n = 0; }
  Sahne.prototype.ekle = function (derin, svg, katman) {
    // katman: 0 arka plan (ızgara), 1 gövde, 2 üst (etiket, hedef); aynı katmanda derinliğe göre
    this.parcalar.push({ d: derin, k: katman == null ? 1 : katman, s: svg, i: this.n++ });
  };
  Sahne.prototype.html = function () {
    return this.parcalar.sort(function (a, b) { return a.k - b.k || a.d - b.d || a.i - b.i; }).map(function (p) { return p.s; }).join("");
  };

  // ---------- Çizim parçaları ----------
  function metin(x, y, t, sinif, hiza, ek) {
    return '<text x="' + r1(x) + '" y="' + r1(y) + '" class="' + sinif + '"' + (hiza ? ' text-anchor="' + hiza + '"' : "") + (ek || "") + ">" + kacis(t) + "</text>";
  }
  function cokgen(pts, sinif, ek) {
    return '<polygon class="' + sinif + '" points="' + pts.map(function (p) { return pt(p[0], p[1]); }).join(" ") + '"' + (ek || "") + "/>";
  }
  function cizgi(a, b, sinif, ek) {
    return '<path class="' + sinif + '" d="M' + pt(a[0], a[1]) + " L" + pt(b[0], b[1]) + '"' + (ek || "") + "/>";
  }
  function okBasi(tx, ty, dx, dy, sinif, boy) {
    boy = boy || 9;
    const L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, px = -uy, py = ux, g = boy * 0.42;
    return '<polygon class="' + sinif + '" points="' + pt(tx, ty) + " " + pt(tx - ux * boy + px * g, ty - uy * boy + py * g) + " " + pt(tx - ux * boy - px * g, ty - uy * boy - py * g) + '"/>';
  }
  // a -> b ok (ekran noktaları), etiket orta noktada
  function ok(a, b, sinifC, sinifO, etiket, sinifT, ek) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
    let s = '<path class="' + sinifC + '" d="M' + pt(a[0], a[1]) + " L" + pt(b[0] - ux * 3, b[1] - uy * 3) + '"' + (ek || "") + "/>" + okBasi(b[0], b[1], ux, uy, sinifO);
    if (etiket) {
      const px = -uy, py = ux;
      s += metin((a[0] + b[0]) / 2 + px * 10, (a[1] + b[1]) / 2 + py * 10 + 4, etiket, sinifT || "b3-etiket", "middle", ek);
    }
    return s;
  }
  // Ekranda P noktasından w yönünde boy px'lik kuvvet oku (ucu P'de)
  function kuvvetOku(P, w, boy, sinifC, sinifO, etiket, sinifT, ek) {
    const a = [P[0] - w[0] * boy, P[1] - w[1] * boy];
    return ok(a, P, sinifC, sinifO, etiket, sinifT, ek);
  }

  // Prizma: p1 -> p2 ekseni; e1, e2 kesit yarı-vektörleri (bina koordinatında, birbirine dik).
  // Görünen yüzler (yüz merkezi prizma merkezinden izleyiciye yakınsa) çizilir; her yüz kendi derinliğiyle sahneye girer.
  // T: donusum; b: bakış; sinif: temel sınıf (yüzlere " b3-yuz-ust|yan|on" eklenir); ek: ortak öznitelikler (data-*).
  function prizma(sahne, T, b, p1, p2, e1, e2, sinif, ek, katman) {
    const kose = [];
    [p1, p2].forEach(function (p) {
      [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(function (s) {
        kose.push([p[0] + s[0] * e1[0] + s[1] * e2[0], p[1] + s[0] * e1[1] + s[1] * e2[1], p[2] + s[0] * e1[2] + s[1] * e2[2]]);
      });
    });
    const mer = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2];
    const dM = derinlik(mer[0], mer[1], mer[2], b);
    const yuzler = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]];
    const ekr = kose.map(function (k) { const q = izdusum(k[0], k[1], k[2], b); return [T.x(q[0]), T.y(q[1])]; });
    const g = bakisVektoru(b);
    const out = [];
    yuzler.forEach(function (f) {
      const c = [0, 1, 2].map(function (i) { return (kose[f[0]][i] + kose[f[1]][i] + kose[f[2]][i] + kose[f[3]][i]) / 4; });
      const n = [c[0] - mer[0], c[1] - mer[1], c[2] - mer[2]];
      const gor = n[0] * g[0] + n[1] * g[1] + n[2] * g[2];
      if (gor <= 1e-9) return;
      const nL = Math.hypot(n[0], n[1], n[2]) || 1;
      const ust = n[2] / nL > 0.7 ? "ust" : (Math.abs(n[0]) >= Math.abs(n[1]) ? "yan" : "on");
      out.push({ d: derinlik(c[0], c[1], c[2], b), s: cokgen(f.map(function (i) { return ekr[i]; }), sinif + " b3-yuz b3-yuz-" + ust, ek) });
    });
    out.sort(function (x, y) { return x.d - y.d; });
    // bir prizmanın yüzleri birlikte (merkez derinliğiyle) sıralanır; kendi içinde uzak yüz önce
    sahne.ekle(dM, '<g class="b3-prizma">' + out.map(function (o) { return o.s; }).join("") + "</g>", katman);
    return ekr;
  }
  // Dört köşeli yatay levha (döşeme): köşeler bina koordinatında sıralı
  function dortgen(sahne, T, b, koseler, sinif, ek, katman) {
    const mer = [0, 0, 0];
    koseler.forEach(function (k) { mer[0] += k[0] / koseler.length; mer[1] += k[1] / koseler.length; mer[2] += k[2] / koseler.length; });
    const ekr = koseler.map(function (k) { const q = izdusum(k[0], k[1], k[2], b); return [T.x(q[0]), T.y(q[1])]; });
    sahne.ekle(derinlik(mer[0], mer[1], mer[2], b), cokgen(ekr, sinif, ek), katman);
    return ekr;
  }
  // Mesnet simgesi (kolon tabanı): ankastre = taralı çizgi, mafsal = üçgen, elastik = zikzak
  // tur: "ankastre" | "mafsal" | "elastik" (yay); baslik verilirse simgenin ipucu (<title>)
  function mesnet(sahne, T, b, P, tur, ek, baslik) {
    const q = izdusum(P[0], P[1], P[2], b), x = T.x(q[0]), y = T.y(q[1]);
    let s = "";
    if (tur === "mafsal") {
      s += '<path class="b3-mes-f" d="M' + pt(x, y) + " L" + pt(x - 9, y + 12) + " L" + pt(x + 9, y + 12) + ' Z"/>';
      s += '<path class="b3-mes-c" d="M' + pt(x - 14, y + 13) + " L" + pt(x + 14, y + 13) + '"/>';
    } else if (tur === "elastik") {
      let d = "M" + pt(x, y);
      for (let k = 0; k < 6; k++) d += " L" + pt(x + (k % 2 ? 5 : -5), y + 2 + k * 2.2);
      d += " L" + pt(x, y + 15);
      s += '<path class="b3-yay-c" d="' + d + '"/><path class="b3-mes-c" d="M' + pt(x - 14, y + 16) + " L" + pt(x + 14, y + 16) + '"/>';
    } else {
      s += '<path class="b3-mes-c" d="M' + pt(x - 14, y + 1) + " L" + pt(x + 14, y + 1) + '"/>';
      for (let v = -12; v <= 12; v += 6) s += '<path class="b3-mes-t" d="M' + pt(x + v, y + 1) + " L" + pt(x + v - 5, y + 7) + '"/>';
    }
    const ip = baslik ? "<title>" + String(baslik).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }) + "</title>" : "";
    // ek içinde class="…" verilirse (Winkler yayı, soluk kat) b3-mesnet sınıfıyla birleştirilir (ikinci class özniteliği yok sayılırdı)
    let sinif = "b3-mesnet";
    const ek2 = String(ek || "").replace(/\s*class="([^"]*)"/, function (m, c) { sinif = (" " + c + " ").indexOf(" b3-mesnet ") >= 0 ? c : "b3-mesnet " + c; return ""; });
    sahne.ekle(derinlik(P[0], P[1], P[2], b) - 1e-3, '<g class="' + sinif + '"' + ek2 + ">" + ip + s + "</g>", 1);
    return [x, y];
  }

  // ---------- Vuruş testi ----------
  // hedefler: [{tur: "daire", x, y, r, ...}, {tur: "cokgen", pts: [[x,y],...], ...}, {tur: "dogru", a: [x,y], b: [x,y], r, ...}]
  // En yakın daire önce, sonra doğru, sonra çokgen (içinde olan).
  function vurus(hedefler, x, y) {
    let enIyi = null, enK = Infinity;
    hedefler.forEach(function (h) {
      if (h.tur === "daire") {
        const d = Math.hypot(h.x - x, h.y - y);
        if (d <= h.r && d < enK) { enK = d; enIyi = h; }
      }
    });
    if (enIyi) return enIyi;
    hedefler.forEach(function (h) {
      if (h.tur === "dogru") {
        const d = noktaDogru(x, y, h.a, h.b);
        if (d <= h.r && d < enK) { enK = d; enIyi = h; }
      }
    });
    if (enIyi) return enIyi;
    for (let i = hedefler.length - 1; i >= 0; i--) {
      const h = hedefler[i];
      if (h.tur === "cokgen" && icinde(h.pts, x, y)) return h;
    }
    return null;
  }
  function noktaDogru(x, y, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
    let t = L2 > 0 ? ((x - a[0]) * dx + (y - a[1]) * dy) / L2 : 0;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(a[0] + dx * t - x, a[1] + dy * t - y);
  }
  function icinde(pts, x, y) {
    let ic = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const xi = pts[i][0], yi = pts[i][1], xj = pts[j][0], yj = pts[j][1];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) ic = !ic;
    }
    return ic;
  }

  // ---------- Jest yöneticisi (Pointer Events tek yol) ----------
  // h: { nokta(e) -> [x, y] viewBox; dokun(p, e); uzunBas(p, e); surukleBasla(p, e) -> true ise sürükleme "çizgi" kipi;
  //      surukle(p, e); surukleBitir(p, e); dondur(dfi, dpsi); kaydir(dx, dy) (viewBox birimi); yakinlastir(k, p); hareketBitti() }
  function jestler(el, h) {
    const isaretler = new Map();
    let kip = null;           // null | "bekle" | "dondur" | "kaydir" | "cizgi" | "iki"
    let bas = null, son = null, zaman = 0, uzunZ = 0, ikiUzak = 0, ikiOrta = null, hareketEtti = false;
    const ESIK = 8, UZUN = 520;
    const kaba = function (e) { return e.pointerType === "touch"; };
    function temizle() {
      if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
      kip = null; bas = null; son = null; hareketEtti = false;
    }
    function ikiOku() {
      const v = Array.from(isaretler.values());
      ikiUzak = Math.hypot(v[0][0] - v[1][0], v[0][1] - v[1][1]) || 1;
      ikiOrta = [(v[0][0] + v[1][0]) / 2, (v[0][1] + v[1][1]) / 2];
    }
    function down(e) {
      if (e.button != null && e.button !== 0 && e.pointerType === "mouse") return;
      const p = h.nokta(e);
      isaretler.set(e.pointerId, p);
      try { el.setPointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
      if (isaretler.size === 2) {
        if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
        kip = "iki"; ikiOku(); return;
      }
      if (isaretler.size > 2) return;
      bas = p; son = p; zaman = performance.now(); hareketEtti = false;
      kip = "bekle";
      if (h.uzunBas) {
        uzunZ = setTimeout(function () {
          uzunZ = 0;
          if (kip === "bekle" && !hareketEtti) { kip = "uzun"; h.uzunBas(bas, e); }
        }, UZUN);
      }
      e.preventDefault();
    }
    function move(e) {
      if (!isaretler.has(e.pointerId)) return;
      const p = h.nokta(e);
      isaretler.set(e.pointerId, p);
      if (kip === "iki" && isaretler.size === 2) {
        const u0 = ikiUzak, o0 = ikiOrta;
        ikiOku();
        if (h.yakinlastir && Math.abs(ikiUzak / u0 - 1) > 0.002) h.yakinlastir(ikiUzak / u0, o0);
        if (h.kaydir) h.kaydir(ikiOrta[0] - o0[0], ikiOrta[1] - o0[1]);
        e.preventDefault();
        return;
      }
      if (!bas || kip === "uzun" || kip === null) return;
      const dx = p[0] - son[0], dy = p[1] - son[1];
      if (kip === "bekle") {
        const esik = ESIK * (h.pxOlcek ? h.pxOlcek() : 1);
        if (Math.hypot(p[0] - bas[0], p[1] - bas[1]) < esik) return;
        hareketEtti = true;
        if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
        if (h.surukleBasla && h.surukleBasla(bas, e)) kip = "cizgi";
        else kip = (h.kipSec ? h.kipSec(e) : "dondur");
      }
      if (kip === "cizgi") { if (h.surukle) h.surukle(p, e); }
      else if (kip === "kaydir") { if (h.kaydir) h.kaydir(dx, dy); }
      else if (kip === "dondur") {
        const r = el.getBoundingClientRect(), k = r.width ? 360 / Math.max(240, r.width) : 0.5;
        const s = h.pxOlcek ? h.pxOlcek() : 1;
        if (h.dondur) h.dondur(dx / s * k * 0.9, dy / s * k * 0.6);
      }
      son = p;
      e.preventDefault();
    }
    function up(e) {
      if (!isaretler.has(e.pointerId)) return;
      isaretler.delete(e.pointerId);
      try { el.releasePointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
      if (kip === "iki") { if (isaretler.size < 2) { temizle(); if (h.hareketBitti) h.hareketBitti(); } return; }
      const p = h.nokta(e);
      if (kip === "bekle" && !hareketEtti) { temizle(); if (h.dokun) h.dokun(p, e); return; }
      if (kip === "cizgi") { temizle(); if (h.surukleBitir) h.surukleBitir(p, e); return; }
      const k = kip;
      temizle();
      if ((k === "dondur" || k === "kaydir") && h.hareketBitti) h.hareketBitti();
    }
    function cancel(e) {
      isaretler.delete(e.pointerId);
      if (kip === "cizgi" && h.surukleBitir) h.surukleBitir(null, e);
      temizle();
      if (h.hareketBitti) h.hareketBitti();
    }
    function wheel(e) {
      if (!h.yakinlastir) return;
      e.preventDefault();
      const p = h.nokta(e);
      h.yakinlastir(e.deltaY < 0 ? 1.15 : 1 / 1.15, p);
    }
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", cancel);
    el.addEventListener("wheel", wheel, { passive: false });
    el.addEventListener("contextmenu", function (e) { if (kaba(e) || kip) e.preventDefault(); });
    return {
      kaldir: function () {
        el.removeEventListener("pointerdown", down); el.removeEventListener("pointermove", move);
        el.removeEventListener("pointerup", up); el.removeEventListener("pointercancel", cancel);
        el.removeEventListener("wheel", wheel);
      },
      kaba: kaba,
    };
  }

  window.Cizim3B = Object.freeze({
    GORUNUMLER: GORUNUMLER, izdusum: izdusum, derinlik: derinlik, bakisVektoru: bakisVektoru, yon: yon,
    donusum: donusum, Kamera: Kamera, Sahne: Sahne,
    metin: metin, cokgen: cokgen, cizgi: cizgi, okBasi: okBasi, ok: ok, kuvvetOku: kuvvetOku,
    prizma: prizma, dortgen: dortgen, mesnet: mesnet,
    vurus: vurus, noktaDogru: noktaDogru, icinde: icinde, jestler: jestler,
    pt: pt, r1: r1, kacis: kacis, azHareket: azHareket,
  });
})();
