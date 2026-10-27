/* Matris Öğren — ölçüm geometrisi ve yakalama (window.MatrisOlcum; node'da module.exports). Tasarım belgesi §17.1 "Ölçme".
   Saf çekirdek (DOM yok): uzaklık, açı, alan, kot farkı, koordinat, eleman boyu; bina JSON'dan düğüm/çubuk geometrisi;
   yakalama (düğüm, orta nokta, kesişim, dik iz düşüm, çubuk üzeri, aks/ızgara). İsteğe bağlı SVG: ölçü çizgileri ve yakalama
   işaretleri — ekran dönüşümü `cevir(P) -> [x, y]` ile (Cizim3B izdüşümü için `cevirici(T, bakis)`).

   Koordinat: bina sistemi (X sağa, Y derinlik, Z yukarı; m). Açılar derece. Yakalama ekran kipinde (sec.cevir verilirse)
   tolerans piksel, aksi hâlde metre. Sayı biçimi uygulamayla aynı: ondalık virgül, eksi işareti "−". */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.MatrisOlcum = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function () {
  "use strict";

  const D2R = Math.PI / 180;
  const ONCELIK = { dugum: 0, aks: 0.6, kesisim: 1, orta: 2, dik: 3, cubuk: 4, izgara: 5, serbest: 9 };
  const YAKALAMA_ADI = { dugum: "Düğüm", aks: "Aks kesişimi", kesisim: "Kesişim", orta: "Orta nokta", dik: "Dik iz düşüm",
    cubuk: "Çubuk üzerinde", izgara: "Izgara", serbest: "Serbest" };
  const GEREKEN = { uzaklik: 2, aci: 3, alan: 3, kot: 2, koordinat: 1, boy: 2 };
  const KIP_ADI = { uzaklik: "Uzaklık", aci: "Açı", alan: "Alan", kot: "Kot farkı", koordinat: "Koordinat", boy: "Eleman boyu" };

  // ---------------------------------------------------------------- vektör
  function cikar(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function topla(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
  function olcek(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
  function ic(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function dis(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function boy(a) { return Math.sqrt(ic(a, a)); }
  function ara(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function mesafe(a, b) { return boy(cikar(a, b)); }
  function nokta(P) {
    const v = Array.isArray(P) ? P : (P && typeof P === "object" ? (P.P || [P.X, P.Y, P.Z]) : null);
    if (!v || v.length !== 3 || !v.every(function (x) { return x !== null && x !== "" && isFinite(+x); })) {
      throw new Error("Nokta [X, Y, Z] sayıları olmalı (girilen: " + JSON.stringify(P) + ").");
    }
    return [+v[0], +v[1], +v[2]];
  }
  function r9(v) { const r = Math.round(v * 1e9) / 1e9; return r === 0 ? 0 : r; }

  // ---------------------------------------------------------------- biçim
  /** Uygulama biçimi: sabit ondalık, virgül, "−". */
  function bicim(v, ondalik) {
    if (typeof v !== "number" || !isFinite(v)) return "—";
    const n = ondalik == null ? 3 : ondalik;
    let t = (Math.round(v * Math.pow(10, n)) / Math.pow(10, n)).toFixed(n);
    if (/^-0(\.0*)?$/.test(t)) t = t.slice(1);
    return t.replace(".", ",").replace("-", "−");
  }
  function isaretli(v, n) { return (v > 0 ? "+" : "") + bicim(v, n); }

  // ---------------------------------------------------------------- ölçümler (saf)
  function uzaklik(A, B) {
    A = nokta(A); B = nokta(B);
    const d = cikar(B, A), L = boy(d), yatay = Math.hypot(d[0], d[1]);
    return { tur: "uzaklik", noktalar: [A, B], L: L, dX: d[0], dY: d[1], dZ: d[2], yatay: yatay,
      egim: L > 1e-12 ? Math.atan2(d[2], yatay) / D2R : 0,
      // plan doğrultu açısı (X ekseninden saat yönünün tersine, derece)
      dogrultu: yatay > 1e-12 ? Math.atan2(d[1], d[0]) / D2R : null };
  }
  /** B köşesindeki açı (BA ile BC arası, 3B, 0–180°). Plan (XY) izdüşümündeki açı da verilir. */
  function aci(A, B, C) {
    A = nokta(A); B = nokta(B); C = nokta(C);
    const u = cikar(A, B), v = cikar(C, B), Lu = boy(u), Lv = boy(v);
    if (Lu < 1e-12 || Lv < 1e-12) throw new Error("Açı için köşe noktası diğer iki noktadan farklı olmalı.");
    const c = Math.max(-1, Math.min(1, ic(u, v) / (Lu * Lv)));
    const a = Math.atan2(boy(dis(u, v)), ic(u, v)) / D2R;
    let plan = null;
    if (Math.hypot(u[0], u[1]) > 1e-12 && Math.hypot(v[0], v[1]) > 1e-12) {
      plan = Math.abs(Math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]) / D2R);
    }
    return { tur: "aci", noktalar: [A, B, C], aci: a, cos: c, tumler: 180 - a, plan: plan, kollar: [Lu, Lv] };
  }
  /** Çokgen alanı (Newell; düzlemsel değilse ortalama düzleme göre), çevre, yatay izdüşüm alanı, normal, ağırlık merkezi. */
  function alan(P) {
    if (!Array.isArray(P) || P.length < 3) throw new Error("Alan için en az üç nokta gerekir.");
    const Q = P.map(nokta);
    let n = [0, 0, 0], cevre = 0;
    for (let i = 0; i < Q.length; i++) {
      const a = Q[i], b = Q[(i + 1) % Q.length];
      n = topla(n, [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]);
      cevre += mesafe(a, b);
    }
    const iki = boy(n), A = iki / 2;
    const birimN = iki > 1e-15 ? olcek(n, 1 / iki) : [0, 0, 1];
    // ağırlık merkezi: üçgen yelpazesi (alan ağırlıklı)
    let m = [0, 0, 0], top = 0;
    for (let i = 1; i < Q.length - 1; i++) {
      const t = boy(dis(cikar(Q[i], Q[0]), cikar(Q[i + 1], Q[0]))) / 2;
      m = topla(m, olcek(topla(topla(Q[0], Q[i]), Q[i + 1]), t / 3)); top += t;
    }
    if (top < 1e-15) { m = [0, 0, 0]; Q.forEach(function (q) { m = topla(m, olcek(q, 1 / Q.length)); }); }
    else m = olcek(m, 1 / top);
    let sapma = 0;
    Q.forEach(function (q) { sapma = Math.max(sapma, Math.abs(ic(cikar(q, Q[0]), birimN))); });
    return { tur: "alan", noktalar: Q, alan: A, cevre: cevre, izdusum: Math.abs(n[2]) / 2, normal: birimN, merkez: m,
      egim: Math.acos(Math.min(1, Math.abs(birimN[2]))) / D2R, duzlemsel: sapma <= 0.005, sapma: sapma };
  }
  function kotFarki(A, B) {
    A = nokta(A); B = nokta(B);
    return { tur: "kot", noktalar: [A, B], dZ: B[2] - A[2], ZA: A[2], ZB: B[2], yatay: Math.hypot(B[0] - A[0], B[1] - A[1]) };
  }
  function koordinat(A) { A = nokta(A); return { tur: "koordinat", noktalar: [A], X: A[0], Y: A[1], Z: A[2] }; }
  /** Eleman boyu: geometri çubuğu (anahtar "kolon:3" ya da nesne) ya da iki uç. */
  function elemanBoyu(geo, anahtar) {
    const c = typeof anahtar === "object" && anahtar && anahtar.A ? anahtar : cubukBul(geo, anahtar);
    if (!c) throw new Error("Çubuk bulunamadı: " + anahtar);
    const u = uzaklik(c.A, c.B);
    u.tur = "boy"; u.eleman = { tur: c.tur, no: c.no, anahtar: c.anahtar, etiket: c.etiket };
    return u;
  }

  /** Ölçüm sonucunun kısa okunur özeti (durum çubuğu, ipucu, pano). */
  function ozet(s) {
    if (!s) return "";
    switch (s.tur) {
      case "uzaklik": case "boy":
        return (s.tur === "boy" && s.eleman ? s.eleman.etiket + ": " : "") + "L = " + bicim(s.L) + " m  (ΔX " + bicim(s.dX) + ", ΔY " + bicim(s.dY) +
          ", ΔZ " + bicim(s.dZ) + "; yatay " + bicim(s.yatay) + " m, eğim " + bicim(s.egim, 2) + "°)";
      case "aci": return "Açı = " + bicim(s.aci, 2) + "°" + (s.plan != null && Math.abs(s.plan - s.aci) > 0.01 ? " (planda " + bicim(s.plan, 2) + "°)" : "");
      case "alan": return "Alan = " + bicim(s.alan, 3) + " m²  (çevre " + bicim(s.cevre) + " m; yatay izdüşüm " + bicim(s.izdusum, 3) + " m²" +
        (s.duzlemsel ? "" : "; düzlemsel değil, sapma " + bicim(s.sapma * 1000, 1) + " mm") + ")";
      case "kot": return "ΔZ = " + isaretli(s.dZ) + " m  (" + bicim(s.ZA) + " → " + bicim(s.ZB) + ")";
      case "koordinat": return "X = " + bicim(s.X) + ", Y = " + bicim(s.Y) + ", Z = " + bicim(s.Z) + " m";
      default: return "";
    }
  }

  // ---------------------------------------------------------------- bina JSON → geometri
  function sirala(l) {
    return (l || []).map(function (a) { return { ad: String(a.ad), k: +a.konum }; }).sort(function (a, b) { return a.k - b.k; });
  }
  /** Bina JSON'dan (surum 1–3) düğüm ve çubuk geometrisi. Aks–kat düğüm no = 1000·kat + 20·ix + iy + 1 (model_ops ile aynı). */
  function geometri(bina) {
    const b = bina || {};
    const xs = sirala(b.akslar && b.akslar.x), ys = sirala(b.akslar && b.akslar.y);
    const ix = new Map(xs.map(function (a, i) { return [a.ad, i]; })), iy = new Map(ys.map(function (a, i) { return [a.ad, i]; }));
    const kotlar = new Map();
    (b.katlar || []).forEach(function (k, i) { kotlar.set(k.no != null ? +k.no : i, +k.kot); });
    const dugumler = new Map(), cubuklar = [], paneller = [];
    function izgaraNo(aks, kat) {
      if (!Array.isArray(aks) || aks.length !== 2) return null;
      const a = ix.get(String(aks[0])), c = iy.get(String(aks[1])), k = kat == null ? 1 : +kat;
      if (a == null || c == null || !kotlar.has(k)) return null;
      return 1000 * k + 20 * a + c + 1;
    }
    function izgaraDugum(no) {
      if (dugumler.has(no)) return dugumler.get(no);
      const k = Math.floor(no / 1000), r = no % 1000 - 1, a = Math.floor(r / 20), c = r % 20;
      if (!kotlar.has(k) || !xs[a] || !ys[c]) return null;
      const d = { no: no, P: [xs[a].k, ys[c].k, kotlar.get(k)], etiket: xs[a].ad + ys[c].ad + "/k" + k, aks: [xs[a].ad, ys[c].ad], kat: k, izgara: true };
      dugumler.set(no, d);
      return d;
    }
    (b.dugumler || []).forEach(function (d) {
      if (!d || d.no == null || !isFinite(+d.X) || !isFinite(+d.Y) || !isFinite(+d.Z)) return;
      dugumler.set(+d.no, { no: +d.no, P: [+d.X, +d.Y, +d.Z], etiket: d.ad ? String(d.ad) : "D" + d.no, serbest: true });
    });
    function coz(ref) {
      if (ref == null) return null;
      if (typeof ref === "number" || (typeof ref === "string" && /^\d+$/.test(ref))) {
        const n = +ref;
        return dugumler.get(n) || (n < 100000 ? izgaraDugum(n) : null);
      }
      if (Array.isArray(ref)) return koordinatDugum(ref);
      if (typeof ref === "object") {
        if (ref.dugum != null) return coz(+ref.dugum);
        if (ref.aks != null) { const n = izgaraNo(ref.aks, ref.kat); return n == null ? null : izgaraDugum(n); }
        if (ref.X != null || ref.Y != null || ref.Z != null) return koordinatDugum([ref.X, ref.Y, ref.Z]);
      }
      return null;
    }
    function koordinatDugum(v) {
      let P;
      try { P = nokta(v); } catch (e) { return null; }
      for (const d of dugumler.values()) if (mesafe(d.P, P) <= 0.001) return d;
      return { no: null, P: P, etiket: "(" + bicim(P[0], 2) + "; " + bicim(P[1], 2) + "; " + bicim(P[2], 2) + ")" };
    }
    function ekle(tur, no, di, dj, kaynak, ek) {
      if (!di || !dj) return;
      cubuklar.push(Object.assign({ anahtar: kaynak + ":" + no, kaynak: kaynak, tur: tur, no: no, i: di.no, j: dj.no, A: di.P, B: dj.P,
        etiket: (kaynak === "kolon" ? "Kolon " : kaynak === "kiris" ? "Kiriş " : "Çubuk ") + no }, ek || {}));
    }
    (b.kolonlar || []).forEach(function (k) {
      const kat = +k.kat, a = izgaraNo(k.aks, kat - 1), u = izgaraNo(k.aks, kat);
      if (a == null || u == null) return;
      ekle("kolon", k.no, izgaraDugum(a), izgaraDugum(u), "kolon", { kat: kat, aks: k.aks, etiket: "Kolon " + k.no + " (S-" + k.aks.join("") + "/k" + kat + ")" });
    });
    (b.kirisler || []).forEach(function (k) {
      const a = izgaraNo(k.bas, k.kat), u = izgaraNo(k.son, k.kat);
      if (a == null || u == null) return;
      ekle("kiris", k.no, izgaraDugum(a), izgaraDugum(u), "kiris", { kat: +k.kat,
        etiket: "Kiriş " + k.no + " (K-" + (k.bas || []).join("") + "→" + (k.son || []).join("") + "/k" + k.kat + ")" });
    });
    (b.cubuklar || []).forEach(function (c) {
      if (!c || c.no == null) return;
      ekle(c.tur || "diger", c.no, coz(c.i), coz(c.j), "cubuk", { aci: +c.aci || 0 });
    });
    (b.dosemeler || []).forEach(function (d) {
      if (!Array.isArray(d.kose) || d.kose.length !== 2) return;
      const a = d.kose[0], c = d.kose[1];
      const ref = [[a[0], a[1]], [c[0], a[1]], [c[0], c[1]], [a[0], c[1]]].map(function (q) { const n = izgaraNo(q, d.kat); return n == null ? null : izgaraDugum(n); });
      if (ref.some(function (q) { return !q; })) return;
      paneller.push({ anahtar: "doseme:" + d.no, kaynak: "doseme", tur: "doseme", no: d.no, kose: ref.map(function (q) { return q.P; }), dugumler: ref.map(function (q) { return q.no; }) });
    });
    (b.paneller || []).forEach(function (p) {
      if (!p || !Array.isArray(p.kose)) return;
      const ref = p.kose.map(coz);
      if (ref.some(function (q) { return !q; })) return;
      paneller.push({ anahtar: "panel:" + p.no, kaynak: "panel", tur: p.tur || "doseme", no: p.no, kose: ref.map(function (q) { return q.P; }), dugumler: ref.map(function (q) { return q.no; }) });
    });
    return { dugumler: Array.from(dugumler.values()), cubuklar: cubuklar, paneller: paneller,
      izgara: { xs: xs, ys: ys, kotlar: Array.from(kotlar.entries()).map(function (e) { return { kat: e[0], kot: e[1] }; }) },
      coz: coz, izgaraNo: izgaraNo };
  }
  function cubukBul(geo, anahtar) {
    if (!geo) return null;
    const a = String(anahtar);
    return geo.cubuklar.find(function (c) { return c.anahtar === a; }) || null;
  }

  /** İki doğru parçasının 3B en yakın yaklaşımı; tol içinde kesişiyorsa {P, s, t}. */
  function parcaKesisim(P1, P2, Q1, Q2, tol) {
    tol = tol == null ? 0.001 : tol;
    const d1 = cikar(P2, P1), d2 = cikar(Q2, Q1), r = cikar(P1, Q1);
    const a = ic(d1, d1), e = ic(d2, d2), f = ic(d2, r);
    if (a < 1e-18 || e < 1e-18) return null;
    const c = ic(d1, r), b = ic(d1, d2), den = a * e - b * b;
    if (Math.abs(den) < 1e-14 * a * e) return null;   // paralel
    let s = (b * f - c * e) / den, t = (a * f - b * c) / den;
    const L1 = Math.sqrt(a), L2 = Math.sqrt(e);
    if (s < -tol / L1 || s > 1 + tol / L1 || t < -tol / L2 || t > 1 + tol / L2) return null;
    s = Math.max(0, Math.min(1, s)); t = Math.max(0, Math.min(1, t));
    const Ps = ara(P1, P2, s), Qt = ara(Q1, Q2, t);
    if (mesafe(Ps, Qt) > tol) return null;
    return { P: olcek(topla(Ps, Qt), 0.5), s: s, t: t };
  }
  /** Çubuk çiftlerinin uç olmayan kesişimleri (önbellekli). */
  function kesisimler(geo, tol) {
    if (geo._kesisim) return geo._kesisim;
    const l = [], c = geo.cubuklar, tl = tol == null ? 0.001 : tol;
    for (let i = 0; i < c.length; i++) {
      for (let j = i + 1; j < c.length; j++) {
        const k = parcaKesisim(c[i].A, c[i].B, c[j].A, c[j].B, tl);
        if (!k) continue;
        const uc1 = k.s * mesafe(c[i].A, c[i].B) <= tl || (1 - k.s) * mesafe(c[i].A, c[i].B) <= tl;
        const uc2 = k.t * mesafe(c[j].A, c[j].B) <= tl || (1 - k.t) * mesafe(c[j].A, c[j].B) <= tl;
        if (uc1 && uc2) continue;     // ortak uç = düğüm
        l.push({ P: k.P, cubuklar: [c[i].anahtar, c[j].anahtar] });
      }
    }
    try { Object.defineProperty(geo, "_kesisim", { value: l, enumerable: false, configurable: true }); } catch (e) { /* donmuş */ }
    return l;
  }
  /** P'nin AB doğru parçası üzerindeki dik izdüşümü (t ∈ [0, 1] ise). */
  function dikIzdusum(P, A, B) {
    const d = cikar(B, A), L2 = ic(d, d);
    if (L2 < 1e-18) return null;
    const t = ic(cikar(P, A), d) / L2;
    return { P: ara(A, B, t), t: t, ic: t >= -1e-9 && t <= 1 + 1e-9 };
  }

  // ---------------------------------------------------------------- yakalama
  /** Ekran (x, y) → Z = sabit düzleminde (X, Y) (cevir afin varsayılır; sonlu farkla tersine çevrilir). */
  function ekrandanDuzleme(x, y, cevir, Z) {
    const o = cevir([0, 0, Z]), ex = cevir([1, 0, Z]), ey = cevir([0, 1, Z]);
    const a = ex[0] - o[0], b = ey[0] - o[0], c = ex[1] - o[1], d = ey[1] - o[1], det = a * d - b * c;
    if (Math.abs(det) < 1e-9) return null;   // düzlem bakışa paralel (ör. ön görünüşte plan düzlemi)
    const u = x - o[0], v = y - o[1];
    return [(d * u - b * v) / det, (a * v - c * u) / det, Z];
  }
  function ekranUzak(p, q) { return Math.hypot(p[0] - q[0], p[1] - q[1]); }
  /** Ekrandaki en yakın parça noktası: oran t (afin izdüşüm oranı korur) ve uzaklık. */
  function ekranParca(p, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
    if (L2 < 1e-9) return { t: 0, d: ekranUzak(p, a) };
    let t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2;
    t = Math.max(0, Math.min(1, t));
    return { t: t, d: Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy) };
  }

  /**
   * En uygun yakalama noktası.
   *  hedef: ekran kipinde [x, y] (sec.cevir ile), yoksa bina noktası [X, Y, Z].
   *  sec: { cevir?, tol? (px: 14 | m: 0.25), turler? (dizi; varsayılan hepsi), onceki? (dik iz düşüm için [X,Y,Z]),
   *         izgara? {adim (m), Z (düzlem kotu)}, aks? (true: kullanılmayan aks kesişimleri de), haric? (anahtar kümesi) }
   *  dönüş: { tur, ad, P: [X,Y,Z], d, etiket, cubuk?, cubuklar?, dugum? } | null
   */
  function yakala(hedef, geo, sec) {
    sec = sec || {};
    const ekran = typeof sec.cevir === "function";
    const tol = sec.tol != null ? +sec.tol : (ekran ? 14 : 0.25);
    const izin = new Set(sec.turler || Object.keys(ONCELIK));
    const cv = ekran ? sec.cevir : null;
    const h = ekran ? [+hedef[0], +hedef[1]] : nokta(hedef);
    const uz = function (P) { return ekran ? ekranUzak(h, cv(P)) : mesafe(h, P); };
    let en = null;
    function aday(tur, P, ek) {
      const d = uz(P);
      if (d > tol) return;
      const puan = d / Math.max(tol, 1e-9) + 0.18 * ONCELIK[tur];
      if (!en || puan < en.puan) en = Object.assign({ tur: tur, ad: YAKALAMA_ADI[tur], P: P.slice(), d: d, puan: puan }, ek || {});
    }
    geo = geo || { dugumler: [], cubuklar: [] };
    if (izin.has("dugum")) geo.dugumler.forEach(function (n) { aday("dugum", n.P, { dugum: n.no, etiket: n.etiket }); });
    if (izin.has("aks") && sec.aks && geo.izgara) {
      const g = geo.izgara;
      g.kotlar.forEach(function (k) {
        g.xs.forEach(function (a) { g.ys.forEach(function (c) { aday("aks", [a.k, c.k, k.kot], { etiket: a.ad + c.ad + "/k" + k.kat }); }); });
      });
    }
    if (izin.has("orta")) geo.cubuklar.forEach(function (c) { aday("orta", ara(c.A, c.B, 0.5), { cubuk: c.anahtar, etiket: c.etiket + " ortası" }); });
    if (izin.has("kesisim")) kesisimler(geo).forEach(function (k) { aday("kesisim", k.P, { cubuklar: k.cubuklar, etiket: "Kesişim" }); });
    if (izin.has("dik") && sec.onceki) {
      const P0 = nokta(sec.onceki);
      geo.cubuklar.forEach(function (c) {
        const f = dikIzdusum(P0, c.A, c.B);
        if (f && f.ic && mesafe(f.P, P0) > 1e-6) aday("dik", f.P, { cubuk: c.anahtar, t: f.t, etiket: c.etiket + " üzerine dik" });
      });
    }
    if (izin.has("cubuk")) {
      geo.cubuklar.forEach(function (c) {
        let t;
        if (ekran) t = ekranParca(h, cv(c.A), cv(c.B)).t;
        else { const f = dikIzdusum(h, c.A, c.B); t = f ? Math.max(0, Math.min(1, f.t)) : 0; }
        aday("cubuk", ara(c.A, c.B, t), { cubuk: c.anahtar, t: t, etiket: c.etiket + " (" + bicim(t * mesafe(c.A, c.B), 2) + " m)" });
      });
    }
    if (izin.has("izgara") && sec.izgara && +sec.izgara.adim > 0) {
      const a = +sec.izgara.adim, Z = +sec.izgara.Z || 0;
      const Q = ekran ? ekrandanDuzleme(h[0], h[1], cv, Z) : [h[0], h[1], Z];
      if (Q) {
        const P = [r9(Math.round(Q[0] / a) * a), r9(Math.round(Q[1] / a) * a), Z];
        aday("izgara", P, { etiket: "Izgara (" + bicim(P[0], 2) + "; " + bicim(P[1], 2) + ")" });
      }
    }
    if (en) delete en.puan;
    return en;
  }

  // ---------------------------------------------------------------- ölçüm durum makinesi (saf)
  /**
   * Olcer(kip): noktaları toplar, gereken sayıya ulaşınca sonucu üretir ve listeye ekler.
   *  kip: "uzaklik" | "aci" | "alan" | "kot" | "koordinat" | "boy"
   *  nokta(P) -> sonuç | null;  bitir() (alan: ≥ 3 nokta) -> sonuç | null;  geriAl(); temizle() (Esc: önce bekleyen noktalar, sonra sonuçlar);
   *  eleman(geo, anahtar) -> boy sonucu (tek dokunuşla "eleman boyu").  sonuclar: tamamlanan ölçümler.  bekleyen: yarım noktalar.
   */
  function Olcer(kip) {
    this.kip = GEREKEN[kip] ? kip : "uzaklik";
    this.bekleyen = [];
    this.sonuclar = [];
  }
  Olcer.prototype.kipSec = function (kip) { if (GEREKEN[kip]) { this.kip = kip; this.bekleyen = []; } return this; };
  Olcer.prototype.gereken = function () { return GEREKEN[this.kip]; };
  Olcer.prototype.ipucu = function () {
    const n = this.bekleyen.length, k = this.kip;
    if (k === "koordinat") return "Sorgulanacak noktayı seçin.";
    if (k === "boy") return n ? "İkinci ucu seçin." : "Bir çubuğa dokunun (ya da iki uç seçin).";
    if (k === "aci") return ["Birinci kolun ucunu seçin.", "Köşe noktasını seçin.", "İkinci kolun ucunu seçin."][n] || "";
    if (k === "alan") return n < 3 ? "Çokgen köşesi " + (n + 1) + " (en az 3)." : "Köşe ekleyin; ilk noktaya dokunun ya da Enter ile bitirin.";
    return n ? "İkinci noktayı seçin." : "Birinci noktayı seçin.";
  };
  Olcer.prototype._bitir = function (s) { this.sonuclar.push(s); this.bekleyen = []; return s; };
  Olcer.prototype.nokta = function (P) {
    P = nokta(P);
    if (this.kip === "alan" && this.bekleyen.length >= 3 && mesafe(P, this.bekleyen[0]) < 1e-6) return this.bitir();
    this.bekleyen.push(P);
    const n = this.bekleyen.length, b = this.bekleyen;
    switch (this.kip) {
      case "koordinat": return this._bitir(koordinat(b[0]));
      case "uzaklik": return n === 2 ? this._bitir(uzaklik(b[0], b[1])) : null;
      case "boy": if (n === 2) { const s = uzaklik(b[0], b[1]); s.tur = "boy"; return this._bitir(s); } return null;
      case "kot": return n === 2 ? this._bitir(kotFarki(b[0], b[1])) : null;
      case "aci":
        if (n < 3) return null;
        try { return this._bitir(aci(b[0], b[1], b[2])); } catch (e) { this.bekleyen.pop(); return null; }
      default: return null;
    }
  };
  Olcer.prototype.bitir = function () {
    if (this.kip !== "alan" || this.bekleyen.length < 3) return null;
    return this._bitir(alan(this.bekleyen));
  };
  Olcer.prototype.eleman = function (geo, anahtar) { return this._bitir(elemanBoyu(geo, anahtar)); };
  Olcer.prototype.geriAl = function () {
    if (this.bekleyen.length) this.bekleyen.pop(); else this.sonuclar.pop();
    return this;
  };
  /** Esc: önce yarım ölçümü, ikinci basışta bütün sonuçları siler. Dönüş: bir şey silindiyse true. */
  Olcer.prototype.temizle = function (hepsi) {
    if (!hepsi && this.bekleyen.length) { this.bekleyen = []; return true; }
    const vardi = this.bekleyen.length > 0 || this.sonuclar.length > 0;
    this.bekleyen = []; this.sonuclar = [];
    return vardi;
  };
  /** Bekleyen noktalar + imleç (P) ile canlı önizleme sonucu (çizim için; listeye eklenmez). */
  Olcer.prototype.onizleme = function (P) {
    const b = this.bekleyen.slice();
    if (P) b.push(nokta(P));
    try {
      if (this.kip === "uzaklik" || this.kip === "boy") return b.length >= 2 ? Object.assign(uzaklik(b[0], b[1]), { gecici: true }) : null;
      if (this.kip === "kot") return b.length >= 2 ? Object.assign(kotFarki(b[0], b[1]), { gecici: true }) : null;
      if (this.kip === "aci") return b.length >= 3 ? Object.assign(aci(b[0], b[1], b[2]), { gecici: true }) :
        (b.length === 2 ? Object.assign(uzaklik(b[0], b[1]), { gecici: true, kol: true }) : null);
      if (this.kip === "alan") return b.length >= 3 ? Object.assign(alan(b), { gecici: true }) :
        (b.length === 2 ? Object.assign(uzaklik(b[0], b[1]), { gecici: true, kol: true }) : null);
    } catch (e) { return null; }
    return null;
  };
  /** Sonuçlar + önizleme SVG'si. */
  Olcer.prototype.svg = function (cevir, P, sec) {
    const parca = this.sonuclar.map(function (s, i) { return olcuSvg(s, cevir, Object.assign({ sira: i + 1 }, sec || {})); });
    const on = this.onizleme(P);
    if (on) parca.push(olcuSvg(on, cevir, sec));
    const b = this.bekleyen;
    b.forEach(function (q) { const p = cevir(q); parca.push('<circle class="olcum-nokta" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="3.5"/>'); });
    return '<g class="olcum-katman">' + parca.join("") + "</g>";
  };

  // ---------------------------------------------------------------- SVG
  function r1(v) { return Math.round(v * 10) / 10; }
  function kacis(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function cizgi(a, b, sinif) {
    return '<line class="' + sinif + '" x1="' + r1(a[0]) + '" y1="' + r1(a[1]) + '" x2="' + r1(b[0]) + '" y2="' + r1(b[1]) + '"/>';
  }
  function etiket(x, y, metin, sinif, aci) {
    const tr = aci ? ' transform="rotate(' + r1(aci) + " " + r1(x) + " " + r1(y) + ')"' : "";
    return '<text class="olcum-etiket' + (sinif ? " " + sinif : "") + '" x="' + r1(x) + '" y="' + r1(y) + '" text-anchor="middle" dominant-baseline="central"' + tr + ">" + kacis(metin) + "</text>";
  }
  /** Bina → ekran dönüştürücü: T = Cizim3B.donusum(...) sonucu, bakis = {fi, psi}; izdusum varsayılanı Cizim3B'ninkiyle aynıdır. */
  function cevirici(T, bakis, izdusumFn) {
    const iz = izdusumFn || (typeof window !== "undefined" && window.Cizim3B && window.Cizim3B.izdusum) || izdusum;
    return function (P) { const q = iz(P[0], P[1], P[2], bakis); return [T.x(q[0]), T.y(q[1])]; };
  }
  /** Cizim3B.izdusum ile özdeş aksonometri (node testleri ve Cizim3B'siz kullanım için). */
  function izdusum(X, Y, Z, b) {
    const f = b.fi * D2R, p = b.psi * D2R, z = -Y;
    const u = X * Math.cos(f) + z * Math.sin(f), derin = -X * Math.sin(f) + z * Math.cos(f);
    return [u, Z * Math.cos(p) - derin * Math.sin(p)];
  }
  /** Ekranda okunur açı (metin baş aşağı olmasın). */
  function okunurAci(dx, dy) {
    let a = Math.atan2(dy, dx) / D2R;
    if (a > 90) a -= 180; if (a < -90) a += 180;
    return a;
  }

  /**
   * Bir ölçüm sonucunun SVG'si (ölçü çizgisi, uzatma çizgileri, eğik kesme işaretleri, etiket).
   *  sec: { ofset (px, 16), sira (numara rozeti), ondalik (3) }
   */
  function olcuSvg(s, cevir, sec) {
    sec = sec || {};
    if (!s || !cevir) return "";
    const n = sec.ondalik == null ? 3 : sec.ondalik;
    const sinif = "olcum olcum-" + s.tur + (s.gecici ? " olcum-gecici" : "");
    const out = [];
    const P = s.noktalar.map(cevir);
    if (s.tur === "uzaklik" || s.tur === "boy") {
      const a = P[0], b = P[1], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
      if (L < 0.5) return '<g class="' + sinif + '">' + cizgi(a, b, "olcum-cizgi") + "</g>";
      let nx = -dy / L, ny = dx / L;
      if (ny > 0) { nx = -nx; ny = -ny; }     // ölçü çizgisi mümkünse yukarıda
      const o = s.kol ? 0 : (sec.ofset == null ? 16 : +sec.ofset);
      const a2 = [a[0] + nx * o, a[1] + ny * o], b2 = [b[0] + nx * o, b[1] + ny * o];
      if (o) { out.push(cizgi([a[0] + nx * 3, a[1] + ny * 3], [a2[0] + nx * 5, a2[1] + ny * 5], "olcum-uzatma")); out.push(cizgi([b[0] + nx * 3, b[1] + ny * 3], [b2[0] + nx * 5, b2[1] + ny * 5], "olcum-uzatma")); }
      out.push(cizgi(a2, b2, "olcum-cizgi"));
      if (!s.kol) {
        // 45° eğik kesme işaretleri (mimari ölçü)
        const tx = (dx / L + nx) * 4.5, ty = (dy / L + ny) * 4.5;
        [a2, b2].forEach(function (q) { out.push(cizgi([q[0] - tx, q[1] - ty], [q[0] + tx, q[1] + ty], "olcum-kesme")); });
        const m = [(a2[0] + b2[0]) / 2 + nx * 9, (a2[1] + b2[1]) / 2 + ny * 9];
        out.push(etiket(m[0], m[1], bicim(s.L, n) + " m", "", L > 60 ? okunurAci(dx, dy) : 0));
        if (Math.abs(s.dZ) > 1e-6 && Math.abs(s.yatay) > 1e-6 && L > 90) {
          out.push(etiket(m[0] - nx * 22, m[1] - ny * 22, "ΔZ " + bicim(s.dZ, 2) + " · " + bicim(s.egim, 1) + "°", "olcum-ikincil", okunurAci(dx, dy)));
        }
      }
    } else if (s.tur === "aci") {
      const B = P[1], u = [P[0][0] - B[0], P[0][1] - B[1]], v = [P[2][0] - B[0], P[2][1] - B[1]];
      const Lu = Math.hypot(u[0], u[1]), Lv = Math.hypot(v[0], v[1]);
      out.push(cizgi(B, P[0], "olcum-cizgi")); out.push(cizgi(B, P[2], "olcum-cizgi"));
      if (Lu > 1 && Lv > 1) {
        const R = Math.max(14, Math.min(34, Math.min(Lu, Lv) * 0.45));
        const a0 = Math.atan2(u[1], u[0]), a1 = Math.atan2(v[1], v[0]);
        let da = a1 - a0; while (da > Math.PI) da -= 2 * Math.PI; while (da < -Math.PI) da += 2 * Math.PI;
        const p0 = [B[0] + R * Math.cos(a0), B[1] + R * Math.sin(a0)], p1 = [B[0] + R * Math.cos(a1), B[1] + R * Math.sin(a1)];
        out.push('<path class="olcum-yay" d="M' + r1(p0[0]) + "," + r1(p0[1]) + " A" + r1(R) + "," + r1(R) + " 0 0 " + (da > 0 ? 1 : 0) + " " + r1(p1[0]) + "," + r1(p1[1]) + '"/>');
        const am = a0 + da / 2;
        out.push(etiket(B[0] + (R + 18) * Math.cos(am), B[1] + (R + 18) * Math.sin(am), bicim(s.aci, 1) + "°"));
      }
    } else if (s.tur === "alan") {
      out.push('<polygon class="olcum-alan-dolgu" points="' + P.map(function (p) { return r1(p[0]) + "," + r1(p[1]); }).join(" ") + '"/>');
      const m = cevir(s.merkez);
      out.push(etiket(m[0], m[1], bicim(s.alan, Math.max(2, n - 1)) + " m²"));
      if (!s.duzlemsel) out.push(etiket(m[0], m[1] + 16, "düzlemsel değil", "olcum-ikincil"));
    } else if (s.tur === "kot") {
      const A = s.noktalar[0], B = s.noktalar[1], Ak = cevir([A[0], A[1], B[2]]);
      out.push(cizgi(P[0], Ak, "olcum-cizgi")); out.push(cizgi(Ak, P[1], "olcum-uzatma"));
      [P[0], Ak].forEach(function (q) {   // kot üçgeni (ucu noktada)
        out.push('<path class="olcum-kot-isaret" d="M' + r1(q[0]) + "," + r1(q[1]) + " l-5,-8 h10 z\"/>");
      });
      const m = [(P[0][0] + Ak[0]) / 2, (P[0][1] + Ak[1]) / 2];
      out.push(etiket(m[0] + 10, m[1], "ΔZ " + isaretli(s.dZ, n) + " m", "olcum-sol"));
    } else if (s.tur === "koordinat") {
      const p = P[0];
      out.push(cizgi([p[0] - 7, p[1]], [p[0] + 7, p[1]], "olcum-cizgi")); out.push(cizgi([p[0], p[1] - 7], [p[0], p[1] + 7], "olcum-cizgi"));
      out.push(cizgi(p, [p[0] + 18, p[1] - 18], "olcum-uzatma"));
      out.push(etiket(p[0] + 22, p[1] - 30, "X " + bicim(s.X, n) + "  Y " + bicim(s.Y, n), "olcum-sol"));
      out.push(etiket(p[0] + 22, p[1] - 16, "Z " + bicim(s.Z, n) + " m", "olcum-sol"));
    }
    P.forEach(function (p) { out.push('<circle class="olcum-uc" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="2.6"/>'); });
    if (sec.sira && !s.gecici) {
      const p = P[P.length - 1];
      out.push('<g class="olcum-rozet"><circle cx="' + r1(p[0] + 10) + '" cy="' + r1(p[1] + 10) + '" r="7"/>' + etiket(p[0] + 10, p[1] + 10, String(sec.sira)) + "</g>");
    }
    return '<g class="' + sinif + '"><title>' + kacis((KIP_ADI[s.tur] || "") + ": " + ozet(s)) + "</title>" + out.join("") + "</g>";
  }

  /** Yakalama işareti: düğüm □, orta △, kesişim ×, dik ⊥, çubuk ⧗, ızgara +, aks ◇. */
  function yakalamaSvg(y, cevir) {
    if (!y || !cevir) return "";
    const p = cevir(y.P), x = r1(p[0]), z = r1(p[1]), s = 6;
    let g;
    switch (y.tur) {
      case "dugum": g = '<rect x="' + (x - s) + '" y="' + (z - s) + '" width="' + 2 * s + '" height="' + 2 * s + '"/>'; break;
      case "orta": g = '<path d="M' + x + "," + (z - s - 1) + " L" + (x + s + 1) + "," + (z + s) + " L" + (x - s - 1) + "," + (z + s) + ' Z"/>'; break;
      case "kesisim": g = '<path d="M' + (x - s) + "," + (z - s) + " L" + (x + s) + "," + (z + s) + " M" + (x + s) + "," + (z - s) + " L" + (x - s) + "," + (z + s) + '"/>'; break;
      case "dik": g = '<path d="M' + (x - s) + "," + (z + s) + " H" + (x + s) + " M" + x + "," + (z + s) + " V" + (z - s) + " M" + (x - s) + "," + (z + s - 4) + " h4 v4\"/>"; break;
      case "cubuk": g = '<path d="M' + (x - s) + "," + (z - s) + " L" + (x + s) + "," + (z - s) + " L" + (x - s) + "," + (z + s) + " L" + (x + s) + "," + (z + s) + ' Z"/>'; break;
      case "aks": g = '<path d="M' + x + "," + (z - s - 1) + " L" + (x + s + 1) + "," + z + " L" + x + "," + (z + s + 1) + " L" + (x - s - 1) + "," + z + ' Z"/>'; break;
      default: g = '<path d="M' + (x - s) + "," + z + " H" + (x + s) + " M" + x + "," + (z - s) + " V" + (z + s) + '"/>';
    }
    return '<g class="olcum-yakala olcum-yakala-' + y.tur + '">' + g +
      '<text class="olcum-yakala-ad" x="' + (x + 10) + '" y="' + (z + 18) + '">' + kacis(y.ad) + "</text></g>";
  }

  /** Ölçüm sonuçlarını hesap tablosuna yapıştırılabilir sekmeli metin (TSV) olarak. */
  function tsv(sonuclar) {
    const satir = [["No", "Tür", "Sonuç"].join("\t")];
    (sonuclar || []).forEach(function (s, i) { satir.push([i + 1, KIP_ADI[s.tur] || s.tur, ozet(s)].join("\t")); });
    return satir.join("\n");
  }

  return Object.freeze({
    ONCELIK: ONCELIK, YAKALAMA_ADI: YAKALAMA_ADI, KIP_ADI: KIP_ADI, GEREKEN: GEREKEN,
    bicim: bicim, uzaklik: uzaklik, aci: aci, alan: alan, kotFarki: kotFarki, koordinat: koordinat, elemanBoyu: elemanBoyu, ozet: ozet,
    geometri: geometri, cubukBul: cubukBul, parcaKesisim: parcaKesisim, kesisimler: kesisimler, dikIzdusum: dikIzdusum,
    ekrandanDuzleme: ekrandanDuzleme, yakala: yakala, Olcer: Olcer,
    izdusum: izdusum, cevirici: cevirici, olcuSvg: olcuSvg, yakalamaSvg: yakalamaSvg, tsv: tsv,
  });
});
