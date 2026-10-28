/* Matris Öğren — model işlemleri (serbest 3B modelleme, bina JSON surum 3; tasarım belgesi §12).
   Saf modül: DOM yok. Tarayıcıda window.ModelOps, node'da module.exports (UMD).

   Bütün düzenleme işlevleri SAFTIR: girdi modeli değiştirilmez; sonuç yeni bir modeldir ve bir değişiklik raporu taşır:
     { model, eklenen: {dugumler, cubuklar, paneller}, silinen: {dugumler, cubuklar, paneller[, kolonlar, kirisler, dosemeler]},
       degisen: {dugumler, cubuklar, paneller}, uyarilar: [metin], ...işleme özgü alanlar }
   Rapordaki listeler numaradır (önceki/sonraki model farkından hesaplanır; geri/ileri yığını için modeli saklamak yeter).
   Geçersiz girdi (olmayan çubuk, anlaşılmayan REF, eksik parametre) ModelHatasi fırlatır; geometrik ret (birleştirilemeyen
   zincir, düzlemsel olmayan panel…) hata değil, model değişmeden dönen `uyarilar`dır.

   Koordinat: bina sistemi X sağa, Y derinlik, Z yukarı (§2). Birim m. Uzunluk toleransı varsayılan 1 mm (TOL).
   Düğüm başvurusu (REF): {"dugum": no} | {"aks": ["A","1"], "kat": k} | {"X":..,"Y":..,"Z":..}; ayrıca kolaylık için
   sayı (düğüm no) ya da [X, Y, Z] dizisi kabul edilir. Aks–kat düğüm no = 1000·kat + 20·ix + iy + 1 (ix, iy: konuma göre
   sıralı aks sırası); serbest düğümler 100001'den başlar. İşlemler aks–kat düğümlerini {"aks","kat"} REF'iyle, serbest
   düğümleri {"dugum": no} REF'iyle yazar; koordinatlı REF'ler işlem başında düğüme çevrilir (1 mm içinde varsa ona bağlanır).

   Yerel eksenler motorla aynıdır (sonlu_eleman._lam3b, Kassimali kuralı, bina koordinatına çevrilmiş):
     x′ = i→j birim; yatay bileşen D = √(x′X² + x′Y²) > 0 ise y′ = (−x′X·x′Z/D, −x′Y·x′Z/D, D) (elemanı içeren düşey
     düzlemde yukarı), z′ = (x′Y/D, −x′X/D, 0) = x′ × y′ (yatay); düşey elemanda (D = 0) y′ = (−sgn x′Z, 0, 0), z′ = (0, −1, 0).
     `aci` (derece) x′ etrafında sağ el kuralıyla döndürür: y″ = cos a·y′ + sin a·z′, z″ = −sin a·y′ + cos a·z′.
     Varsayım (motor ajanıyla aynı olmalı): aci = 0'da kesitin h boyutu (güçlü eksen, I_güçlü = Iz_m) y′ doğrultusundadır.
     Bu yüzden aks–kat kolonu yon "x" → aci 0, yon "y" → aci 90 olur (§2: kolonda y′ = −X_bina, z′ = −Y_bina). */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.ModelOps = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function () {
  "use strict";

  const TOL = 0.001;
  const ILK_SERBEST_DUGUM = 100001;
  const SERBESTLIKLER = ["N", "Vy", "Vz", "T", "My", "Mz"];
  const MAFSAL_IKI_UC = Object.freeze({ i: Object.freeze(["My", "Mz"]), j: Object.freeze(["My", "Mz"]) });
  const MAFSAL_I = Object.freeze({ i: Object.freeze(["My", "Mz"]), j: Object.freeze([]) });
  const MAFSAL_J = Object.freeze({ i: Object.freeze([]), j: Object.freeze(["My", "Mz"]) });
  const KAFES_CUBUGU = Object.freeze({ i: Object.freeze(["T", "My", "Mz"]), j: Object.freeze(["My", "Mz"]) });
  const CAPRAZ_TIPLERI = Object.freeze(["X", "tek-/", "tek-\\", "V", "ters-V", "K", "dismerkez-tek", "dismerkez-ters-V", "diz"]);
  const MAKAS_TIPLERI = Object.freeze(["pratt", "howe", "warren", "warren-dikmeli", "k", "fink", "besik-pratt", "besik-howe"]);
  const LISTELER = ["dugumler", "cubuklar", "paneller", "mesnetler", "kren", "ek_yukler", "uretecler"];
  const D2R = Math.PI / 180;
  const ILK_AKS_DUGUM = 800001;          // §19 aks kesişimi düğümleri (kat dışı Z aksları, ek sistemler): işlem içi numara, REF'i adla yazılır

  class ModelHatasi extends Error {
    constructor(mesaj) { super(mesaj); this.name = "ModelHatasi"; }
  }

  /** §19 aks sistemi çözücüsü (docs/aks_sistemi.js, window.MatrisAks). Yoksa null; aks REF'leri yalnız aks–kat biçiminde çözülür. */
  let aksModulu_ = undefined;
  function aksModulu() {
    if (aksModulu_ !== undefined && aksModulu_ !== null) return aksModulu_;
    aksModulu_ = null;
    if (typeof window !== "undefined" && window.MatrisAks) aksModulu_ = window.MatrisAks;
    else if (typeof self !== "undefined" && self.MatrisAks) aksModulu_ = self.MatrisAks;
    else if (typeof require === "function") { try { aksModulu_ = require("./aks_sistemi.js"); } catch (e) { aksModulu_ = null; } }
    return aksModulu_;
  }
  function aksGerekli() {
    const MA = aksModulu();
    if (!MA) throw new ModelHatasi("Aks sistemi başvurusu için aks_sistemi.js yüklenmeli.");
    return MA;
  }
  function aksSistemiVar(m) {
    return !!(m && ((m.akslar && Array.isArray(m.akslar.z) && m.akslar.z.length) || (Array.isArray(m.aks_sistemleri) && m.aks_sistemleri.length)));
  }
  /** {"aks": [..], "z": ad} ya da {"sistem": ad, ...}: §19.2 aks kesişimi REF'i (eski {"aks", "kat"} değil). */
  function yeniAksRef(r) { return !!(r && typeof r === "object" && r.aks != null && (r.z != null || r.sistem != null)); }

  /** Sözleşme K2: surum sayısı — bool → 1; sonlu sayı → tam kısmı; tam/ondalık sayı dizesi → tam kısmı; öteki ("3a", "1e1") → 1. */
  function surumSayi(s) {
    if (typeof s === "boolean") return 1;
    if (typeof s === "number") return isFinite(s) ? Math.trunc(s) : 1;
    if (typeof s === "string" && /^\s*[+-]?\d+(\.\d+)?\s*$/.test(s)) return Math.trunc(parseFloat(s));
    return 1;
  }

  // ---------------------------------------------------------------- vektör yardımcıları
  function topla(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
  function cikar(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function olcek(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
  function ic(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function dis(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function boy(a) { return Math.sqrt(ic(a, a)); }
  function birim(a) { const L = boy(a); return L > 1e-15 ? olcek(a, 1 / L) : [0, 0, 0]; }
  function uzaklik(a, b) { return boy(cikar(a, b)); }
  function ara(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function r6(v) { const r = Math.round(v * 1e6) / 1e6; return r === 0 ? 0 : r; }
  function r9(v) { const r = Math.round(v * 1e9) / 1e9; return r === 0 ? 0 : r; }
  function fmt(v, b) { return (Math.round(v * Math.pow(10, b || 0)) / Math.pow(10, b || 0)).toString(); }
  function kopya(o) {
    if (o === undefined) return undefined;
    if (typeof structuredClone === "function") return structuredClone(o);
    return JSON.parse(JSON.stringify(o));
  }
  function nokta3(P, ad) {
    const v = Array.isArray(P) ? P : (P && typeof P === "object" ? [P.X, P.Y, P.Z] : null);
    if (!v || v.length !== 3 || !v.every(function (x) { return x !== null && x !== "" && isFinite(+x); })) {
      throw new ModelHatasi((ad || "Nokta") + " [X, Y, Z] sayıları olmalı (girilen: " + JSON.stringify(P) + ").");
    }
    return [+v[0], +v[1], +v[2]];
  }
  /** P noktasının A–B doğrusuna uzaklığı ve A'dan itibaren oran t (0 = A, 1 = B). */
  function dogruyaUzaklik(P, A, B) {
    const d = cikar(B, A), L2 = ic(d, d);
    if (L2 < 1e-24) return { d: uzaklik(P, A), t: 0 };
    const t = ic(cikar(P, A), d) / L2;
    return { d: uzaklik(P, ara(A, B, t)), t: t };
  }
  /** Newell normali (alanın iki katı uzunlukta). */
  function newell(P) {
    const n = [0, 0, 0];
    for (let k = 0; k < P.length; k++) {
      const a = P[k], b = P[(k + 1) % P.length];
      n[0] += (a[1] - b[1]) * (a[2] + b[2]);
      n[1] += (a[2] - b[2]) * (a[0] + b[0]);
      n[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }
    return n;
  }
  /** Rodrigues dönme matrisi uygulayıcısı (eksen birim, θ radyan). */
  function donmeR(eksen, teta) {
    const k = birim(eksen), c = Math.cos(teta), s = Math.sin(teta);
    return function (v) {
      const kv = dis(k, v), kd = ic(k, v);
      return [v[0] * c + kv[0] * s + k[0] * kd * (1 - c), v[1] * c + kv[1] * s + k[1] * kd * (1 - c), v[2] * c + kv[2] * s + k[2] * kd * (1 - c)];
    };
  }
  function duzlemCoz(d) {
    if (!d || typeof d !== "object") throw new ModelHatasi('Düzlem {"X": x0} | {"Y": y0} | {"Z": z0} | {"nokta": [..], "normal": [..]} olmalı.');
    if (d.normal != null) {
      const n = birim(nokta3(d.normal, "Düzlem normali"));
      if (boy(n) < 0.5) throw new ModelHatasi("Düzlem normali sıfır olamaz.");
      return { p0: nokta3(d.nokta || [0, 0, 0], "Düzlem noktası"), n: n };
    }
    for (const [k, i] of [["X", 0], ["Y", 1], ["Z", 2]]) {
      if (d[k] != null && isFinite(+d[k])) { const p0 = [0, 0, 0], n = [0, 0, 0]; p0[i] = +d[k]; n[i] = 1; return { p0: p0, n: n }; }
    }
    throw new ModelHatasi('Düzlem anlaşılamadı: ' + JSON.stringify(d) + ' — {"X": 5} ya da {"nokta": [..], "normal": [..]} verin.');
  }

  // ---------------------------------------------------------------- yerel eksenler (motor kuralı)
  function yerelEksenVektor(Pi, Pj, aci) {
    const d = cikar(nokta3(Pj), nokta3(Pi)), L = boy(d);
    if (L < 1e-12) return null;
    const x = olcek(d, 1 / L), D = Math.hypot(x[0], x[1]);
    let y, z;
    if (D < 1e-9) {
      const cy = x[2] > 0 ? 1 : -1;
      y = [-cy, 0, 0]; z = [0, -1, 0];
    } else {
      y = [-x[0] * x[2] / D, -x[1] * x[2] / D, D];
      z = [x[1] / D, -x[0] / D, 0];
    }
    const a = (+aci || 0) * D2R;
    if (a) {
      const c = Math.cos(a), s = Math.sin(a);
      const y2 = topla(olcek(y, c), olcek(z, s)), z2 = topla(olcek(y, -s), olcek(z, c));
      y = y2; z = z2;
    }
    return { x: x, y: y, z: z };
  }
  /** y″ ekseni hedef vektöre paralel olacak `aci` (derece). serbestIsaret: hedefin yönü önemsizse (−90, 90] aralığına indirir. */
  function aciHedef(Pi, Pj, hedef, serbestIsaret) {
    const e = yerelEksenVektor(Pi, Pj, 0);
    let a = Math.atan2(ic(hedef, e.z), ic(hedef, e.y)) / D2R;
    if (serbestIsaret) { if (a > 90 + 1e-9) a -= 180; if (a <= -90 + 1e-9) a += 180; }
    return r9(a);
  }

  // ---------------------------------------------------------------- uç serbestliği / yük yardımcıları
  function serbestUc(c, uc) { return c && c.serbest && Array.isArray(c.serbest[uc]) ? c.serbest[uc].slice() : []; }
  function serbestSirala(l) {
    const s = new Set(l || []);
    return SERBESTLIKLER.filter(function (x) { return s.has(x); });
  }
  function serbestYaz(c, i, j) {
    const s = {}, si = serbestSirala(i), sj = serbestSirala(j);
    if (si.length) s.i = si;
    if (sj.length) s.j = sj;
    if (s.i || s.j) c.serbest = s; else delete c.serbest;
  }
  function ozellikKopya(c) {
    const o = {};
    for (const k of Object.keys(c)) if (k !== "no" && k !== "i" && k !== "j" && k !== "serbest") o[k] = kopya(c[k]);
    return o;
  }
  function yukQ(y) {
    const q1 = y.q1 != null ? +y.q1 : (y.q != null ? +y.q : 0);
    const q2 = y.q2 != null ? +y.q2 : q1;
    return [q1, q2];
  }
  /** Çubuk yükünün mutlak [x1, x2] aralığı (m). */
  function yukAraligi(y, L) {
    if (y.oransal) return [(y.x1 == null ? 0 : +y.x1) * L, (y.x2 == null ? 1 : +y.x2) * L];
    return [y.x1 == null ? 0 : +y.x1, y.x2 == null ? L : +y.x2];
  }
  function tekilMi(y) { return y.x != null && y.x1 == null && y.q1 == null && y.q == null; }
  function yerelYon(yon) {
    const m = /^([xyz])['′]$/.exec(String(yon || ""));
    return m ? m[1] : null;
  }
  const GLOBAL_YON = { X: [1, 0, 0], Y: [0, 1, 0], Z: [0, 0, 1] };

  // ================================================================= Çalışma bağlamı
  function Is(model, sec) {
    if (!model || typeof model !== "object" || Array.isArray(model)) throw new ModelHatasi("Model bir bina JSON nesnesi olmalı.");
    this.once = model;
    this.m = kopya(model);
    this.tol = sec && +sec.tol > 0 ? +sec.tol : TOL;
    this.uy = [];
    this.kaynak = null;
    for (const k of LISTELER) if (!Array.isArray(this.m[k])) this.m[k] = [];
    this._h = null; this._cb = null; this._izg = undefined;
    this._sonDg = null; this._sonCb = null;
    this.koordinatlariCoz();
  }
  const P_ = Is.prototype;

  P_.uyar = function (m) { if (this.uy.indexOf(m) < 0) this.uy.push(m); };

  // ---- ızgara (aks–kat)
  P_.izgara = function () {
    if (this._izg !== undefined) return this._izg;
    const ak = this.m.akslar;
    let kt = this.m.katlar;
    const zKat = ak && Array.isArray(ak.z) ? ak.z.filter(function (a) { return a && a.kat != null && a.kat !== ""; }) : [];
    if ((!Array.isArray(kt) || !kt.length) && zKat.length) kt = zKat.map(function (a) { return { no: +a.kat, kot: +a.konum }; });
    if (!ak || !Array.isArray(ak.x) || !Array.isArray(ak.y) || !ak.x.length || !ak.y.length || !Array.isArray(kt) || !kt.length) {
      this._izg = null; return null;
    }
    const sirala = function (l) { return l.map(function (a) { return { ad: String(a.ad), k: +a.konum }; }).sort(function (a, b) { return a.k - b.k; }); };
    const xs = sirala(ak.x), ys = sirala(ak.y);
    const katlar = new Map();
    kt.forEach(function (k, i) { katlar.set(k.no != null ? +k.no : i, +k.kot); });
    const zAd = new Map();
    zKat.forEach(function (a) { katlar.set(+a.kat, +a.konum); zAd.set(+a.kat, String(a.ad)); });   // tek kaynak: akslar.z
    this._izg = { xs: xs, ys: ys, katlar: katlar, zAd: zAd,
      ix: new Map(xs.map(function (a, i) { return [a.ad, i]; })), iy: new Map(ys.map(function (a, i) { return [a.ad, i]; })) };
    return this._izg;
  };
  P_.izgaraNo = function (aks, kat) {
    const g = this.izgara();
    if (!g || !Array.isArray(aks) || aks.length !== 2) return null;
    const ix = g.ix.get(String(aks[0])), iy = g.iy.get(String(aks[1])), k = kat == null ? 1 : +kat;
    if (ix == null || iy == null || !g.katlar.has(k)) return null;
    return 1000 * k + 20 * ix + iy + 1;
  };
  P_.harita = function () {
    if (this._h) return this._h;
    const h = new Map(), g = this.izgara();
    this.sanalDugumler(h);
    if (g) {
      for (const [kat, kot] of g.katlar) {
        for (let ix = 0; ix < g.xs.length; ix++) {
          for (let iy = 0; iy < g.ys.length; iy++) {
            const no = 1000 * kat + 20 * ix + iy + 1;
            h.set(no, { no: no, X: g.xs[ix].k, Y: g.ys[iy].k, Z: kot, izgara: true, aks: [g.xs[ix].ad, g.ys[iy].ad], kat: kat, kayit: null });
          }
        }
      }
    }
    let cz = null;
    for (const d of this.m.dugumler) {
      if (!d || d.no == null) continue;
      const e = h.get(+d.no);
      let X = +d.X, Y = +d.Y, Z = +d.Z;
      if (d.tur === "bolme" || d.tur === "kesisim") {
        // §19.2 parametrik düğüm: konum ana çubuğun uçlarından (aks taşınınca birlikte taşınır)
        const MA = aksGerekli();
        if (!cz) cz = new MA.Cozucu(this.m);
        let P;
        try { P = cz.coz({ dugum: +d.no }); } catch (x) { throw new ModelHatasi(x.message); }
        X = P[0]; Y = P[1]; Z = P[2];
      }
      h.set(+d.no, { no: +d.no, X: X, Y: Y, Z: Z, izgara: !!(e && e.izgara), aks: e ? e.aks : null, kat: e ? e.kat : null, kayit: d, aksRef: e ? e.aksRef : null });
    }
    this._h = h;
    return h;
  };
  /** §19: kat dışı GLOBAL Z akslarındaki ve ek sistemlerdeki bütün aks kesişimleri (sanal düğüm; numara işlem içidir, REF adla yazılır). */
  P_.sanalDugumler = function (h) {
    this._sanal = new Map();
    this._sanalSon = ILK_AKS_DUGUM - 1;
    if (!aksSistemiVar(this.m)) return;
    const MA = aksGerekli();
    const S = MA.sistemler(this.m);
    const self = this;
    // ek sistemler önce: aynı konumda GLOBAL kesişim varsa (bul eşitlikte sonrakini seçer) GLOBAL tercih edilir
    S.slice(1).concat(S.slice(0, 1)).forEach(function (s) {
      const yu = s.yonler[0], yv = s.yonler[1];
      s.l.z.forEach(function (z) {
        if (s.global && z.kat != null) return;             // kat Z aksları: aks–kat düğümleri (1000·kat + 20·ix + iy + 1)
        s.l[yu].forEach(function (a) {
          s.l[yv].forEach(function (b) {
            const ref = s.global ? { aks: [a.ad, b.ad], z: z.ad } : { sistem: s.ad, aks: [a.ad, b.ad], z: z.ad };
            self.sanalEkle(h, ref, MA.sistemNokta(s, a.konum, b.konum, z.konum), MA.refAnahtar(self.m, ref));
          });
        });
      });
    });
  };
  P_.sanalEkle = function (h, ref, P, anahtar) {
    const no = ++this._sanalSon;
    h.set(no, { no: no, X: P[0], Y: P[1], Z: P[2], izgara: true, aks: ref.aks.slice(), kat: null, kayit: null, aksRef: ref });
    this._sanal.set(anahtar, no);
    return no;
  };
  /** §19.2 aks REF'i → düğüm numarası (GLOBAL kat Z aksı → aks–kat numarası; diğerleri sanal aks düğümü). */
  P_.aksRefNo = function (ref) {
    const MA = aksGerekli();
    const g = this.izgara();
    if (!ref.sistem && ref.z != null && g) {
      for (const [kat, ad] of g.zAd) {
        if (ad === String(ref.z)) { const n = this.izgaraNo(ref.aks, kat); if (n != null) return n; }
      }
    }
    const h = this.harita();
    const k = MA.refAnahtar(this.m, ref);
    if (this._sanal.has(k)) return this._sanal.get(k);
    let P;
    try { P = MA.refKoordinat(this.m, ref); } catch (x) { throw new ModelHatasi("Aks başvurusu geçersiz: " + x.message); }
    return this.sanalEkle(h, JSON.parse(JSON.stringify(ref)), P, k);
  };
  P_.kon = function (no) {
    const d = this.harita().get(+no);
    if (!d) throw new ModelHatasi("Düğüm " + no + " modelde yok.");
    return [d.X, d.Y, d.Z];
  };
  P_.bul = function (P, tol, haric) {
    let best = null, bd = tol == null ? this.tol : tol;
    for (const d of this.harita().values()) {
      if (haric && haric.has(d.no)) continue;
      const dx = d.X - P[0], dy = d.Y - P[1], dz = d.Z - P[2];
      if (Math.abs(dx) > bd || Math.abs(dy) > bd || Math.abs(dz) > bd) continue;
      const dd = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (dd <= bd) { bd = dd; best = d.no; }
    }
    return best;
  };
  P_.yeniDugumNo = function () {
    if (this._sonDg == null) {
      let mx = ILK_SERBEST_DUGUM - 1;
      for (const d of this.m.dugumler) if (d && +d.no > mx) mx = +d.no;
      this._sonDg = mx;
    }
    return ++this._sonDg;
  };
  P_.dugumEkle = function (P, ad) {
    const n = this.bul(P);
    if (n != null) return n;
    const no = this.yeniDugumNo();
    const r = { no: no, X: r6(P[0]), Y: r6(P[1]), Z: r6(P[2]) };
    if (ad) r.ad = String(ad);
    if (this.kaynak) r.kaynak = Object.assign({}, this.kaynak);
    this.m.dugumler.push(r);
    this.harita().set(no, { no: no, X: r.X, Y: r.Y, Z: r.Z, izgara: false, aks: null, kat: null, kayit: r });
    return no;
  };
  P_.refNo = function (ref, olustur) {
    if (olustur === undefined) olustur = true;
    if (typeof ref === "string" && /^\d+$/.test(ref.trim())) ref = +ref;
    if (typeof ref === "number") {
      if (!this.harita().has(ref)) throw new ModelHatasi("Düğüm " + ref + " modelde yok.");
      return ref;
    }
    let P = null;
    if (Array.isArray(ref)) P = nokta3(ref, "Koordinatlı düğüm");
    else if (ref && typeof ref === "object") {
      if (ref.dugum != null) return this.refNo(+ref.dugum, olustur);
      if (yeniAksRef(ref)) return this.aksRefNo(ref);
      if (ref.aks != null) {
        const no = this.izgaraNo(ref.aks, ref.kat);
        if (no == null) throw new ModelHatasi("Aks–kat başvurusu geçersiz: " + JSON.stringify(ref) + " (aks adı ya da kat tanımsız).");
        return no;
      }
      if (ref.X != null || ref.Y != null || ref.Z != null) P = nokta3([ref.X, ref.Y, ref.Z], "Koordinatlı düğüm");
    }
    if (!P) throw new ModelHatasi("Düğüm başvurusu anlaşılamadı: " + JSON.stringify(ref) +
      ' — {"dugum": no}, {"aks": ["A","1"], "kat": k} ya da {"X":..,"Y":..,"Z":..} olmalı.');
    const n = this.bul(P);
    if (n != null || !olustur) return n;
    return this.dugumEkle(P);
  };
  P_.refYaz = function (no) {
    const d = this.harita().get(+no);
    if (d && d.aksRef) return JSON.parse(JSON.stringify(d.aksRef));
    if (d && d.izgara) {
      const g = this.izgara();
      if (g && g.zAd.has(d.kat)) return { aks: d.aks.slice(), z: g.zAd.get(d.kat) };
      return { aks: d.aks.slice(), kat: d.kat };
    }
    return { dugum: +no };
  };
  function koordinatRef(r) {
    return Array.isArray(r) || (r && typeof r === "object" && r.dugum == null && r.aks == null && (r.X != null || r.Y != null || r.Z != null));
  }
  P_.koordinatlariCoz = function () {
    const m = this.m, self = this;
    const coz = function (r) { return koordinatRef(r) ? self.refYaz(self.refNo(r)) : r; };
    for (const c of m.cubuklar) { if (c) { c.i = coz(c.i); c.j = coz(c.j); } }
    for (const p of m.paneller) if (p && Array.isArray(p.kose)) p.kose = p.kose.map(coz);
    for (const s of m.mesnetler) if (s) s.dugum = coz(s.dugum);
    for (const y of m.ek_yukler) if (y && y.tur === "dugum" && y.dugum != null) y.dugum = coz(y.dugum);
  };

  // ---- çubuklar
  P_.cubukHarita = function () {
    if (!this._cb) { this._cb = new Map(); for (const c of this.m.cubuklar) if (c) this._cb.set(+c.no, c); }
    return this._cb;
  };
  P_.cubukBul = function (no) { return this.cubukHarita().get(+no) || null; };
  P_.cubuk = function (no) {
    const c = this.cubukBul(no);
    if (!c) throw new ModelHatasi("Çubuk " + no + " modelde yok.");
    return c;
  };
  P_.uclar = function (c) { return [this.refNo(c.i, false), this.refNo(c.j, false)]; };
  P_.cubukUzunluk = function (c) { const u = this.uclar(c); return uzaklik(this.kon(u[0]), this.kon(u[1])); };
  P_.cubukEksen = function (c) { const u = this.uclar(c); return yerelEksenVektor(this.kon(u[0]), this.kon(u[1]), +c.aci || 0); };
  P_.yeniCubukNo = function () {
    if (this._sonCb == null) { let mx = 0; for (const c of this.m.cubuklar) if (c && +c.no > mx) mx = +c.no; this._sonCb = mx; }
    return ++this._sonCb;
  };
  P_.yeniNo = function (liste, ek) {
    let mx = 0;
    for (const x of liste) if (x && +x.no > mx) mx = +x.no;
    for (const x of ek || []) if (x && +x.no > mx) mx = +x.no;
    return mx + 1;
  };
  P_.ekCubuk = function (oz, ni, nj) {
    const r = { no: this.yeniCubukNo(), i: this.refYaz(ni), j: this.refYaz(nj) };
    for (const k of Object.keys(oz || {})) if (!(k in r) && oz[k] !== undefined) r[k] = oz[k];
    if (this.kaynak && !r.kaynak) r.kaynak = Object.assign({}, this.kaynak);
    this.m.cubuklar.push(r);
    this.cubukHarita().set(r.no, r);
    return r.no;
  };
  P_.ciftBul = function (a, b) {
    for (const c of this.m.cubuklar) {
      const u = this.uclar(c);
      if ((u[0] === a && u[1] === b) || (u[0] === b && u[1] === a)) return +c.no;
    }
    return null;
  };
  /** Üreteçler için: aynı iki düğüm arasında çubuk varsa yenisini eklemez. */
  P_.ekCubukTekil = function (oz, ni, nj) {
    if (ni === nj) return null;
    const v = this.ciftBul(ni, nj);
    return v != null ? v : this.ekCubuk(oz, ni, nj);
  };
  P_.cubukSilIc = function (no) {
    no = +no;
    const c = this.cubuk(no);
    const u = this.uclar(c);
    this.m.cubuklar.splice(this.m.cubuklar.indexOf(c), 1);
    this.cubukHarita().delete(no);
    this.m.ek_yukler = this.m.ek_yukler.filter(function (y) { return !(y && y.tur === "cubuk" && +y.cubuk === no); });
    for (const k of this.m.kren) {
      if (k && Array.isArray(k.yol) && k.yol.indexOf(no) >= 0) {
        k.yol = k.yol.filter(function (x) { return +x !== no; });
        this.uyar("Kren " + k.no + " yolundan çubuk " + no + " çıkarıldı; yol listesini denetleyin.");
      }
    }
    return u;
  };

  // ---- bağlantılar
  P_.aksKatVar = function () {
    const m = this.m;
    return ((m.kolonlar || []).length + (m.kirisler || []).length + (m.dosemeler || []).length) > 0;
  };
  P_.kirisParcalari = function (k) {
    const g = this.izgara();
    if (!g || !Array.isArray(k.bas) || !Array.isArray(k.son)) return [];
    const kat = k.kat == null ? 1 : +k.kat;
    const bx = g.ix.get(String(k.bas[0])), by = g.iy.get(String(k.bas[1])), sx = g.ix.get(String(k.son[0])), sy = g.iy.get(String(k.son[1]));
    if (bx == null || by == null || sx == null || sy == null || !g.katlar.has(kat)) return [];
    const no = function (ix, iy) { return 1000 * kat + 20 * ix + iy + 1; };
    const p = [];
    if (by === sy && bx !== sx) { for (let i = Math.min(bx, sx); i < Math.max(bx, sx); i++) p.push([no(i, by), no(i + 1, by)]); }
    else if (bx === sx && by !== sy) { for (let i = Math.min(by, sy); i < Math.max(by, sy); i++) p.push([no(bx, i), no(bx, i + 1)]); }
    return p;
  };
  P_.dosemeKoseleri = function (d) {
    const g = this.izgara();
    if (!g || !Array.isArray(d.kose) || d.kose.length !== 2) return null;
    const a = d.kose[0], b = d.kose[1];
    const xa = g.ix.get(String(a[0])), ya = g.iy.get(String(a[1])), xb = g.ix.get(String(b[0])), yb = g.iy.get(String(b[1]));
    if ([xa, ya, xb, yb].some(function (v) { return v == null; })) return null;
    const x0 = Math.min(xa, xb), x1 = Math.max(xa, xb), y0 = Math.min(ya, yb), y1 = Math.max(ya, yb);
    return { x0: x0, x1: x1, y0: y0, y1: y1, g: g };
  };
  P_.aksKatDugumleri = function () {
    const say = new Map(), self = this;
    if (!this.izgara()) return say;
    const art = function (n) { if (n != null) say.set(n, (say.get(n) || 0) + 1); };
    for (const c of this.m.kolonlar || []) { art(this.izgaraNo(c.aks, +c.kat - 1)); art(this.izgaraNo(c.aks, +c.kat)); }
    for (const k of this.m.kirisler || []) for (const p of this.kirisParcalari(k)) { art(p[0]); art(p[1]); }
    for (const d of this.m.dosemeler || []) {
      const k = this.dosemeKoseleri(d);
      if (!k) continue;
      const kat = d.kat == null ? 1 : +d.kat;
      [[k.x0, k.y0], [k.x1, k.y0], [k.x1, k.y1], [k.x0, k.y1]].forEach(function (q) { art(1000 * kat + 20 * q[0] + q[1] + 1); });
    }
    void self;
    return say;
  };
  /** Aks–kat elemanlarının (kolon, kiriş parçası) düğüm çiftleri: bağlanırlık denetimi için. */
  P_.aksKatKenarlari = function () {
    const l = [];
    for (const c of this.m.kolonlar || []) { const a = this.izgaraNo(c.aks, +c.kat - 1), b = this.izgaraNo(c.aks, +c.kat); if (a != null && b != null) l.push([a, b]); }
    for (const k of this.m.kirisler || []) for (const p of this.kirisParcalari(k)) l.push(p);
    return l;
  };
  P_.yukDugumu = function (y) {
    if (!y || y.tur !== "dugum") return null;
    try {
      if (y.dugum != null) return this.refNo(y.dugum, false);
      if (y.aks != null) return this.izgaraNo(y.aks, y.kat == null ? 1 : y.kat);
    } catch (e) { return null; }
    return null;
  };
  P_.baglantilar = function () {
    const b = new Map();
    const al = function (n) { if (!b.has(n)) b.set(n, { cubuk: [], panel: [], mesnet: [], yuk: [], aksKat: 0 }); return b.get(n); };
    for (const c of this.m.cubuklar) {
      try { const u = this.uclar(c); al(u[0]).cubuk.push({ no: +c.no, uc: "i" }); al(u[1]).cubuk.push({ no: +c.no, uc: "j" }); } catch (e) { /* denetle bildirir */ }
    }
    for (const p of this.m.paneller) {
      for (const r of (p && p.kose) || []) { try { al(this.refNo(r, false)).panel.push(+p.no); } catch (e) { /* */ } }
    }
    for (const s of this.m.mesnetler) { try { al(this.refNo(s.dugum, false)).mesnet.push(s); } catch (e) { /* */ } }
    for (const y of this.m.ek_yukler) { const n = this.yukDugumu(y); if (n != null) al(n).yuk.push(y); }
    for (const [n, k] of this.aksKatDugumleri()) al(n).aksKat += k;
    return b;
  };
  P_.mesnetKaydi = function (n) {
    for (const s of this.m.mesnetler) { try { if (this.refNo(s.dugum, false) === n) return s; } catch (e) { /* */ } }
    return null;
  };
  /** En alt kat seviyesinin kotu (motorla aynı: en küçük numaralı katın kotu; kat yoksa en alt GLOBAL Z aksı). */
  P_.temelKotu = function () {
    if (this._z0 !== undefined) return this._z0;
    let z0 = null;
    const g = this.izgara();
    if (g && g.katlar.size) { const k = Math.min.apply(null, [...g.katlar.keys()]); z0 = g.katlar.get(k); }
    else if (aksSistemiVar(this.m)) {
      try { const z = aksGerekli().sistemler(this.m)[0].l.z; if (z.length) z0 = Math.min.apply(null, z.map(function (a) { return +a.konum; })); } catch (e) { z0 = null; }
    }
    this._z0 = z0;
    return z0;
  };
  /**
   * Temel kuralı (sözleşme C3; motor yapi_serbest._mesnetleri_oku ile aynı): EN ALT kat seviyesindeki her aks kesişimi düğümü
   * (GLOBAL aks–kat ızgarası ya da herhangi bir aks sisteminin kesişimi) temeller.mesnet ile mesnetlidir. Bölme / kesişim ve
   * koordinatlı (serbest) düğümler hiçbir zaman.
   */
  P_.izgaraTaban = function (n) {
    const d = this.harita().get(n);
    if (!d || !d.izgara || (d.kayit && d.kayit.tur)) return false;
    const z0 = this.temelKotu();
    return z0 != null && Math.abs(d.Z - z0) <= 1e-6;
  };
  P_.mesnetli = function (n, donme) {
    const s = this.mesnetKaydi(n);
    if (s) return donme ? !!(s.rx && s.ry && s.rz) : !!(s.ux || s.uy || s.uz || s.rx || s.ry || s.rz);
    if (this.izgaraTaban(n)) return donme ? this.temelTipi() !== "mafsal" : true;
    return false;
  };
  P_.temelTipi = function () {
    const t = this.m.temeller && this.m.temeller.mesnet;
    return t ? String(t).toLowerCase() : "ankastre";
  };
  P_.temelMesnetKaydi = function (n) {
    const tip = this.temelTipi(), r = tip !== "mafsal";
    if (tip === "elastik") this.uyar("Düğüm " + n + ": elastik temel serbest düğüme taşınamaz; ankastre mesnet yazıldı.");
    return { dugum: this.refYaz(n), ux: true, uy: true, uz: true, rx: r, ry: r, rz: r };
  };
  P_.yetimSil = function (adaylar) {
    const bag = this.baglantilar();
    for (const n of new Set(adaylar)) {
      const b = bag.get(n);
      if (b && (b.cubuk.length || b.panel.length || b.mesnet.length || b.yuk.length || b.aksKat)) continue;
      const i = this.m.dugumler.findIndex(function (d) { return d && +d.no === n; });
      if (i >= 0) { this.m.dugumler.splice(i, 1); this._h = null; }
    }
  };
  /** Düğüm başvurularını eşlemeye göre yeniden yazar (eski no → yeni no). */
  P_.refDegistir = function (esle) {
    const self = this;
    const yeni = function (ref) {
      if (ref == null) return ref;
      let n;
      try { n = self.refNo(ref, false); } catch (e) { return ref; }
      return n != null && esle.has(n) ? self.refYaz(esle.get(n)) : ref;
    };
    for (const c of this.m.cubuklar) { c.i = yeni(c.i); c.j = yeni(c.j); }
    for (const p of this.m.paneller) if (Array.isArray(p.kose)) p.kose = p.kose.map(yeni);
    for (const s of this.m.mesnetler) s.dugum = yeni(s.dugum);
    for (const d of this.m.dugumler) {
      if (d && d.tur === "bolme") { d.cubuk_i = yeni(d.cubuk_i); d.cubuk_j = yeni(d.cubuk_j); }
      else if (d && d.tur === "kesisim") { if (Array.isArray(d.a)) d.a = d.a.map(yeni); if (Array.isArray(d.b)) d.b = d.b.map(yeni); }
    }
    for (const y of this.m.ek_yukler) {
      if (!y || y.tur !== "dugum") continue;
      if (y.dugum != null) y.dugum = yeni(y.dugum);
      else if (y.aks != null) {
        const n = this.izgaraNo(y.aks, y.kat == null ? 1 : y.kat);
        if (n != null && esle.has(n)) { delete y.aks; delete y.kat; y.dugum = this.refYaz(esle.get(n)); }
      }
    }
    // üreteç kayıtlarının REF parametreleri (çapraz goz; makas bas/son; beşik taban1/taban2): birleşen / silinen düğüme başvuru kalmaz
    for (const u of this.m.uretecler) {
      if (!u) continue;
      if (Array.isArray(u.goz)) u.goz = u.goz.map(yeni);
      for (const a of ["bas", "son", "taban1", "taban2"]) if (u[a] != null && typeof u[a] === "object" && !Array.isArray(u[a])) u[a] = yeni(u[a]);
    }
  };

  // ---- sonuç
  P_.bitir = function (ek) {
    const m = this.m, once = this.once;
    if ((m.cubuklar.length || m.paneller.length || m.dugumler.length) && !(surumSayi(m.surum) >= 3)) m.surum = 3;
    for (const k of LISTELER) if (!(k in once) && Array.isArray(m[k]) && m[k].length === 0) delete m[k];
    const sonuc = { model: m, eklenen: {}, silinen: {}, degisen: {}, uyarilar: this.uy };
    for (const k of ["dugumler", "cubuklar", "paneller"]) {
      const a = new Map(), b = new Map();
      for (const x of once[k] || []) if (x && x.no != null) a.set(+x.no, JSON.stringify(x));
      for (const x of m[k] || []) if (x && x.no != null) b.set(+x.no, JSON.stringify(x));
      sonuc.eklenen[k] = [...b.keys()].filter(function (n) { return !a.has(n); });
      sonuc.silinen[k] = [...a.keys()].filter(function (n) { return !b.has(n); });
      sonuc.degisen[k] = [...b.keys()].filter(function (n) { return a.has(n) && a.get(n) !== b.get(n); });
    }
    for (const k of ["kolonlar", "kirisler", "dosemeler"]) {
      const l = once[k] || [];
      const kalan = new Set((m[k] || []).map(function (x) { return +x.no; }));
      const sil = l.filter(function (x) { return !kalan.has(+x.no); }).map(function (x) { return +x.no; });
      if (sil.length) sonuc.silinen[k] = sil;
    }
    return Object.assign(sonuc, ek || {});
  };

  // ================================================================= genelleştirme (aks–kat → çubuk/panel)
  P_.genellestirIc = function () {
    const m = this.m;
    if (!this.aksKatVar()) return false;
    const g = this.izgara();
    if (!g) throw new ModelHatasi("Aks–kat elemanları var ama akslar/katlar tanımsız; genelleştirilemez.");
    const self = this;
    const sirali = function (l) { return (l || []).slice().sort(function (a, b) { return ((+a.kat || 1) - (+b.kat || 1)) || (+a.no - +b.no); }); };
    const ekstra = function (x, bilinen) { const o = {}; for (const k of Object.keys(x)) if (bilinen.indexOf(k) < 0) o[k] = kopya(x[k]); return o; };
    const ustKat = Math.max.apply(null, [...g.katlar.keys()]);
    let nk = 0, np = 0, nd = 0;
    for (const c of sirali(m.kolonlar)) {
      const kat = c.kat == null ? 1 : +c.kat;
      const a = this.izgaraNo(c.aks, kat - 1), b = this.izgaraNo(c.aks, kat);
      if (a == null || b == null) throw new ModelHatasi("Kolon " + c.no + ": aks ya da kat geçersiz; genelleştirilemez.");
      const oz = Object.assign({ tur: "kolon", kesit: c.kesit, aci: String(c.yon || "x").toLowerCase() === "y" ? 90 : 0, kat: kat },
        ekstra(c, ["no", "aks", "kat", "kesit", "yon"]), { kaynak: { aks_kat: "kolon", no: +c.no } });
      this.ekCubuk(oz, a, b); nk++;
    }
    const kirisCubuk = new Map();
    for (const k of sirali(m.kirisler)) {
      const parcalar = this.kirisParcalari(k);
      if (!parcalar.length) throw new ModelHatasi("Kiriş " + k.no + ": uçları aynı aks çizgisinde değil ya da tanımsız; genelleştirilemez.");
      const nolar = parcalar.map(function (p, i) {
        return self.ekCubuk(Object.assign({ tur: "kiris", kesit: k.kesit, aci: 0, kat: k.kat == null ? 1 : +k.kat },
          ekstra(k, ["no", "kat", "bas", "son", "kesit"]), { kaynak: { aks_kat: "kiris", no: +k.no, parca: i + 1 } }), p[0], p[1]);
      });
      np += nolar.length;
      kirisCubuk.set(+k.no, nolar);
    }
    const panelNo = new Map();
    const dolu = new Set(m.paneller.map(function (p) { return +p.no; }));
    for (const d of sirali(m.dosemeler)) {
      const k = this.dosemeKoseleri(d);
      const kat = d.kat == null ? 1 : +d.kat;
      if (!k || k.x1 - k.x0 < 1 || k.y1 - k.y0 < 1 || !g.katlar.has(kat)) throw new ModelHatasi("Döşeme " + d.no + ": köşeler geçersiz; genelleştirilemez.");
      const koseler = [[k.x0, k.y0], [k.x1, k.y0], [k.x1, k.y1], [k.x0, k.y1]].map(function (q) { return 1000 * kat + 20 * q[0] + q[1] + 1; });
      const dx = g.xs[k.x1].k - g.xs[k.x0].k, dy = g.ys[k.y1].k - g.ys[k.y0].k;
      const tek = dx >= dy - 1e-9 ? "tek-13" : "tek-24";
      const mod = String(d.dagitim || "otomatik").toLowerCase();
      const oran = Math.max(dx, dy) / Math.min(dx, dy);
      const dagitim = mod === "cift" ? "iki" : mod === "tek" ? tek : (oran <= 2 + 1e-9 ? "iki" : tek);
      let no = +d.no;
      if (!(no > 0) || dolu.has(no)) no = this.yeniNo(m.paneller, [...dolu].map(function (x) { return { no: x }; }));
      dolu.add(no);
      const p = { no: no, kose: koseler.map(function (n) { return self.refYaz(n); }), tur: "doseme",
        kalinlik: d.h != null ? +d.h : 0.12, g: d.g_ek != null ? d.g_ek : (d.kaplama != null ? d.kaplama : 0) };
      if (d.q != null) p.q = d.q;
      p.kullanim = d.kullanim || "konut";
      p.kar = kat === ustKat;
      p.dagitim = dagitim;
      p.kat = kat;
      Object.assign(p, ekstra(d, ["no", "kat", "kose", "h", "g_ek", "kaplama", "q", "kullanim", "dagitim"]));
      p.kaynak = { aks_kat: "doseme", no: +d.no };
      m.paneller.push(p);
      panelNo.set(+d.no, no);
      nd++;
    }
    // ek yükler
    const yeniYuk = [];
    for (const y of m.ek_yukler) {
      if (y && y.tur === "kiris" && kirisCubuk.has(+y.kiris)) {
        const q = -(+y.q || 0);
        for (const cn of kirisCubuk.get(+y.kiris)) {
          yeniYuk.push({ tur: "cubuk", cubuk: cn, durum: y.durum || "G", yon: "Z", q1: q, q2: q, x1: 0, x2: null, oransal: false, izdusum: false });
        }
      } else if (y && y.tur === "dugum" && y.aks != null && y.dugum == null) {
        const r = Object.assign({}, y);
        const n = this.izgaraNo(y.aks, y.kat == null ? 1 : y.kat);
        delete r.aks; delete r.kat;
        r.dugum = n != null ? this.refYaz(n) : { aks: y.aks, kat: y.kat };
        const sira = { tur: r.tur, dugum: r.dugum };
        yeniYuk.push(Object.assign(sira, r));
      } else if (y && y.tur === "doseme" && panelNo.has(+y.doseme)) {
        const r = Object.assign({ tur: "panel", panel: panelNo.get(+y.doseme) }, y);
        r.tur = "panel"; delete r.doseme;
        yeniYuk.push(r);
      } else yeniYuk.push(y);
    }
    m.ek_yukler = yeniYuk;
    // aks–kat düğümleri için kayıt YAZILMAZ: bütün başvurular aks REF'idir ({aks, z} ya da {aks, kat}; numara 1000·kat + 20·ix + iy + 1
    // akslardan çözülür). Eskiden yazılan {no, X, Y, Z, aks, kat} kayıtları aks taşınınca izlemiyor, "aks ekleyin" uyarısı üretiyordu.
    m.kolonlar = []; m.kirisler = []; m.dosemeler = [];
    m.surum = 3;
    this._h = null;
    this.uyar("Aks–kat modeli genelleştirildi: " + nk + " kolon, " + np + " kiriş parçası → çubuk; " + nd + " döşeme → panel.");
    return true;
  };

  // ================================================================= bölme
  P_.yukleriBol = function (eskiNo, araliklar) {
    const L = araliklar[araliklar.length - 1][2];
    const sonuc = [];
    for (const y of this.m.ek_yukler) {
      if (!(y && y.tur === "cubuk" && +y.cubuk === eskiNo)) { sonuc.push(y); continue; }
      if (tekilMi(y)) {
        const x = y.oransal ? +y.x * L : +y.x;
        const p = araliklar.find(function (a) { return x <= a[2] + 1e-9; }) || araliklar[araliklar.length - 1];
        const r = kopya(y); r.cubuk = p[0];
        r.x = y.oransal ? r9((x - p[1]) / (p[2] - p[1])) : r6(x - p[1]);
        sonuc.push(r); continue;
      }
      const xs = yukAraligi(y, L), qs = yukQ(y);
      const qx = function (x) { return xs[1] - xs[0] < 1e-12 ? qs[0] : qs[0] + (qs[1] - qs[0]) * (x - xs[0]) / (xs[1] - xs[0]); };
      for (const a of araliklar) {
        const lo = Math.max(xs[0], a[1]), hi = Math.min(xs[1], a[2]);
        if (hi - lo <= 1e-9) continue;
        const r = kopya(y); delete r.q;
        r.cubuk = a[0];
        r.q1 = r9(qx(lo)); r.q2 = r9(qx(hi));
        const Lp = a[2] - a[1];
        if (y.oransal) { r.x1 = r9((lo - a[1]) / Lp); r.x2 = r9((hi - a[1]) / Lp); }
        else { r.x1 = r6(lo - a[1]); r.x2 = r6(hi - a[1]); }
        if (Math.abs(lo - a[1]) < 1e-9) r.x1 = 0;
        if (Math.abs(hi - a[2]) < 1e-9) r.x2 = null;
        sonuc.push(r);
      }
    }
    this.m.ek_yukler = sonuc;
  };
  P_.krenBol = function (cno, parcalar, ni, nj) {
    for (const k of this.m.kren) {
      if (!k || !Array.isArray(k.yol)) continue;
      const i = k.yol.map(Number).indexOf(cno);
      if (i < 0) continue;
      const self = this;
      const uc = function (no) { const c = self.cubukBul(no); return c ? self.uclar(c) : []; };
      let ters = false;
      if (i > 0) { const u = uc(k.yol[i - 1]); if (u.indexOf(nj) >= 0 && u.indexOf(ni) < 0) ters = true; }
      if (!ters && i < k.yol.length - 1) { const u = uc(k.yol[i + 1]); if (u.indexOf(ni) >= 0 && u.indexOf(nj) < 0) ters = true; }
      k.yol.splice.apply(k.yol, [i, 1].concat(ters ? parcalar.slice().reverse() : parcalar));
    }
  };
  /** Çubuğu i'den itibaren t oranlarında (0 < t < 1) böler; parça numaraları i→j sırasıyla (ilk parça eski numarayı korur). */
  P_.bolIc = function (cno, ts, kayit) {
    cno = +cno;
    const c = this.cubuk(cno);
    const u = this.uclar(c), ni = u[0], nj = u[1];
    const Pi = this.kon(ni), Pj = this.kon(nj), L = uzaklik(Pi, Pj), e = birim(cikar(Pj, Pi));
    const tol = this.tol;
    const tl = [...new Set(ts.map(Number))].filter(function (t) { return isFinite(t) && t * L > tol && (1 - t) * L > tol; }).sort(function (a, b) { return a - b; });
    const zincir = [ni], xs = [0];
    for (const t of tl) {
      const n = this.dugumEkle(ara(Pi, Pj, t));
      if (n === zincir[zincir.length - 1] || n === nj || n === ni) continue;
      const x = ic(cikar(this.kon(n), Pi), e);
      if (x - xs[xs.length - 1] <= tol || L - x <= tol) continue;
      zincir.push(n); xs.push(x);
    }
    zincir.push(nj); xs.push(L);
    if (zincir.length === 2) return [cno];
    const serb = { i: serbestUc(c, "i"), j: serbestUc(c, "j") };
    const oz = ozellikKopya(c);
    c.j = this.refYaz(zincir[1]);
    serbestYaz(c, serb.i, null);
    const parcalar = [cno], yeniler = [];
    for (let k = 1; k < zincir.length - 1; k++) {
      const r = { no: this.yeniCubukNo(), i: this.refYaz(zincir[k]), j: this.refYaz(zincir[k + 1]) };
      Object.assign(r, kopya(oz));
      if (k === zincir.length - 2) serbestYaz(r, null, serb.j);
      yeniler.push(r); parcalar.push(r.no);
      this.cubukHarita().set(r.no, r);
    }
    const idx = this.m.cubuklar.indexOf(c);
    this.m.cubuklar.splice.apply(this.m.cubuklar, [idx + 1, 0].concat(yeniler));
    this.yukleriBol(cno, parcalar.map(function (no, k) { return [no, xs[k], xs[k + 1]]; }));
    this.krenBol(cno, parcalar, ni, nj);
    if (kayit) kayit.bolunen.push(parcalar.slice());
    return parcalar;
  };
  /** Noktalarda böler (noktalar çubuk doğrusuna tol içinde olmalı). */
  P_.bolNoktalarla = function (cno, noktalar, kayit) {
    const c = this.cubuk(cno), u = this.uclar(c), Pi = this.kon(u[0]), Pj = this.kon(u[1]);
    const ts = [];
    for (const P of noktalar) {
      const r = dogruyaUzaklik(P, Pi, Pj);
      if (r.d > this.tol) { this.uyar("Nokta [" + P.map(function (v) { return fmt(v, 3); }).join(", ") + "] çubuk " + cno + " üzerinde değil (uzaklık " + fmt(r.d * 1000, 1) + " mm); atlandı."); continue; }
      ts.push(r.t);
    }
    return this.bolIc(cno, ts, kayit);
  };
  /** P noktasında düğüm sağlar; P'den geçen (iç noktası olan) çubukları böler. Dönüş {no, bolundu}. */
  P_.noktadaBol = function (P, kayit) {
    const tol = this.tol, adaylar = [];
    const mevcut = this.bul(P);
    for (const c of this.m.cubuklar) {
      const u = this.uclar(c);
      if (mevcut != null && (u[0] === mevcut || u[1] === mevcut)) continue;
      const A = this.kon(u[0]), B = this.kon(u[1]), L = uzaklik(A, B);
      if (L <= tol) continue;
      const r = dogruyaUzaklik(P, A, B);
      if (r.d <= tol && r.t * L > tol && (1 - r.t) * L > tol) adaylar.push([+c.no, r.t]);
    }
    for (const a of adaylar) this.bolIc(a[0], [a[1]], kayit);
    const n = this.bul(P);
    return { no: n != null ? n : this.dugumEkle(P), bolundu: adaylar.length > 0 };
  };
  /**
   * Taşıma / kopyalamanın YENİ açtığı uç düğümleri mevcut bir çubuğun iç noktasına düşüyorsa o çubuk orada bölünür: bağlantısız
   * (çubuğun üstünde duran ama ona bağlı olmayan) düğüm mafsallı uçlarda mekanizma olur, motor çözmez (ör. ters V çaprazını
   * bölünmemiş bir kirişin altına taşımak). haric: bölünmeyecek çubuk numaraları (taşınan seçim). Dönüş: bölünen çubuk numaraları.
   */
  P_.uclardaBol = function (dugumler, haric) {
    const tol = this.tol, bolunen = [];
    for (const n of new Set(dugumler)) {
      let P;
      try { P = this.kon(n); } catch (e) { continue; }
      for (const c of this.m.cubuklar.slice()) {
        if (haric && haric.has(+c.no)) continue;
        let u;
        try { u = this.uclar(c); } catch (e) { continue; }
        if (u[0] === n || u[1] === n) continue;
        const A = this.kon(u[0]), B = this.kon(u[1]), L = uzaklik(A, B);
        if (L <= tol) continue;
        const r = dogruyaUzaklik(P, A, B);
        if (r.d > tol || r.t * L <= tol || (1 - r.t) * L <= tol) continue;
        const parca = this.bolIc(+c.no, [r.t]);
        if (parca.length > 1) { bolunen.push(+c.no); this.uyar("Çubuk " + c.no + ", yeni uç düğümü " + n + " üzerine düştüğü için orada bölündü (bağlantı)."); }
      }
    }
    return bolunen;
  };

  // ================================================================= zincirler ve birleştirme
  P_.zincirler = function (nolar) {
    const set = [...new Set(nolar.map(Number))];
    const uc = new Map(), komsu = new Map();
    for (const no of set) {
      const u = this.uclar(this.cubuk(no));
      uc.set(no, u);
      for (const n of u) { if (!komsu.has(n)) komsu.set(n, []); komsu.get(n).push(no); }
    }
    const gorulen = new Set(), sonuc = [];
    for (const bas of set) {
      if (gorulen.has(bas)) continue;
      const comp = [], yigin = [bas];
      gorulen.add(bas);
      while (yigin.length) {
        const c = yigin.pop(); comp.push(c);
        for (const n of uc.get(c)) for (const d of komsu.get(n)) if (!gorulen.has(d)) { gorulen.add(d); yigin.push(d); }
      }
      comp.sort(function (a, b) { return a - b; });
      const dset = new Set();
      comp.forEach(function (c) { uc.get(c).forEach(function (n) { dset.add(n); }); });
      if (comp.some(function (c) { return uc.get(c)[0] === uc.get(c)[1]; })) { sonuc.push({ cubuklar: comp, hata: "sıfır boylu çubuk var" }); continue; }
      const dallanan = [...dset].filter(function (n) { return komsu.get(n).length > 2; });
      if (dallanan.length) { sonuc.push({ cubuklar: comp, hata: "düğüm " + dallanan.join(", ") + " üzerinde dallanma var (zincir değil)" }); continue; }
      const ucDg = [...dset].filter(function (n) { return komsu.get(n).length === 1; });
      if (ucDg.length !== 2) { sonuc.push({ cubuklar: comp, hata: "çubuklar kapalı halka oluşturuyor" }); continue; }
      const yuru = function (s) {
        const sira = [], dg = [s];
        let n = s, onceki = null;
        for (;;) {
          const c = komsu.get(n).find(function (x) { return x !== onceki; });
          if (c == null) break;
          const u = uc.get(c), ters = u[0] !== n;
          sira.push({ no: c, ters: ters });
          n = ters ? u[0] : u[1];
          dg.push(n); onceki = c;
          if (komsu.get(n).length < 2) break;
        }
        return { sira: sira, dugumler: dg };
      };
      const anahtar = comp[0];
      let w = yuru(ucDg[0]);
      if (w.sira.find(function (s) { return s.no === anahtar; }).ters) w = yuru(ucDg[1]);
      sonuc.push({ cubuklar: comp, sira: w.sira, dugumler: w.dugumler, anahtar: anahtar, hata: null });
    }
    return sonuc;
  };
  function yukBirlestir(liste, L) {
    const anahtar = function (y) { return JSON.stringify(Object.assign({}, y, { x1: 0, x2: 0, q1: 0, q2: 0, x: 0 })); };
    const tekil = liste.filter(tekilMi), yay = liste.filter(function (y) { return !tekilMi(y); });
    yay.sort(function (a, b) { const ka = anahtar(a), kb = anahtar(b); return ka < kb ? -1 : ka > kb ? 1 : a.x1 - b.x1; });
    const out = [];
    for (const y of yay) {
      const s = out[out.length - 1];
      if (s && anahtar(s) === anahtar(y) && Math.abs(s.x2 - y.x1) < 1e-6 && Math.abs(s.q1 - s.q2) < 1e-9 &&
          Math.abs(y.q1 - y.q2) < 1e-9 && Math.abs(s.q2 - y.q1) < 1e-9) { s.x2 = y.x2; continue; }
      out.push(y);
    }
    for (const y of out) {
      y.x1 = Math.abs(y.x1) < 1e-6 ? 0 : r6(y.x1);
      y.x2 = Math.abs(y.x2 - L) < 1e-6 ? null : r6(y.x2);
      y.q1 = r9(y.q1); y.q2 = r9(y.q2);
    }
    for (const y of tekil) y.x = r6(y.x);
    return out.concat(tekil);
  }
  /** Zincir üyesinin yükünü birleşik çubuğa taşır (ofs: üyenin başlangıcı, ters: üye zincire ters yönde). */
  function yukTasi(y, Lm, ofs, ters, e, E) {
    const r = kopya(y); delete r.q;
    let isaret = 1;
    const ly = yerelYon(y.yon);
    if (ly) {
      const v = e[ly];
      const adaylar = [["x", E.x], ["y", E.y], ["z", E.z]];
      const bul = adaylar.find(function (a) { return Math.abs(Math.abs(ic(v, a[1])) - 1) < 1e-6; });
      if (!bul) return null;
      isaret = ic(v, bul[1]) > 0 ? 1 : -1;
      r.yon = bul[0] + String(y.yon).slice(1);
    }
    if (tekilMi(y)) {
      const x = y.oransal ? +y.x * Lm : +y.x;
      r.x = ofs + (ters ? Lm - x : x); r.oransal = false;
      for (const k of ["P", "F", "q"]) if (r[k] != null) r[k] = +r[k] * isaret;
      return r;
    }
    let xs = yukAraligi(y, Lm), qs = yukQ(y);
    if (ters) { xs = [Lm - xs[1], Lm - xs[0]]; qs = [qs[1], qs[0]]; }
    r.x1 = ofs + xs[0]; r.x2 = ofs + xs[1]; r.q1 = qs[0] * isaret; r.q2 = qs[1] * isaret; r.oransal = false;
    return r;
  }
  P_.birlestirIc = function (nolar, sessiz) {
    const sonuc = { yeni: [], red: [] }, self = this;
    for (const z of this.zincirler(nolar)) {
      const red = function (sebep) {
        sonuc.red.push({ cubuklar: z.cubuklar, sebep: sebep });
        if (!sessiz) self.uyar("Çubuk " + z.cubuklar.join(", ") + " birleştirilemedi: " + sebep + ".");
      };
      if (z.hata) { red(z.hata); continue; }
      if (z.cubuklar.length < 2) { red("birleştirmek için uç uca en az iki çubuk gerekir"); continue; }
      const cs = z.sira.map(function (s) { return self.cubuk(s.no); });
      const ilk = this.cubuk(z.anahtar);
      const sebep = new Set();
      for (const c of cs) {
        if (String(c.kesit == null ? "" : c.kesit) !== String(ilk.kesit == null ? "" : ilk.kesit)) sebep.add("kesitler farklı (" + cs.map(function (x) { return x.no + ": " + (x.kesit || "—"); }).join(", ") + ")");
        if (String(c.tur || "") !== String(ilk.tur || "")) sebep.add("türler farklı (" + cs.map(function (x) { return x.no + ": " + (x.tur || "—"); }).join(", ") + ")");
        if (!!c.yalniz_cekme !== !!ilk.yalniz_cekme) sebep.add("yalnız-çekme özelliği farklı");
      }
      const P = z.dugumler.map(function (n) { return self.kon(n); });
      const A = P[0], B = P[P.length - 1], L = uzaklik(A, B), u = birim(cikar(B, A));
      let onceki = 0;
      for (let k = 1; k < P.length; k++) {
        if (k < P.length - 1) {
          const d = dogruyaUzaklik(P[k], A, B).d;
          if (d > this.tol) sebep.add("düğüm " + z.dugumler[k] + " A–B doğrusu üzerinde değil (sapma " + fmt(d * 1000, 1) + " mm; eş doğrusal değil)");
        }
        const x = ic(cikar(P[k], A), u);
        if (x <= onceki + this.tol * 0.5) sebep.add("zincir kendi üzerine dönüyor");
        onceki = x;
      }
      const E = yerelEksenVektor(A, B, +ilk.aci || 0);
      const eksenler = cs.map(function (c) { return self.cubukEksen(c); });
      if (E && eksenler.some(function (e) { return !e || Math.abs(ic(e.y, E.y)) < 1 - 1e-6; })) sebep.add("yerel eksen açıları (aci) uyuşmuyor");
      const bag = this.baglantilar();
      for (let k = 1; k < z.dugumler.length - 1; k++) {
        const n = z.dugumler[k], b = bag.get(n);
        const diger = b.cubuk.filter(function (x) { return z.cubuklar.indexOf(x.no) < 0; }).map(function (x) { return x.no; });
        if (diger.length) sebep.add("ara düğüm " + n + "'e başka çubuk bağlı (" + [...new Set(diger)].join(", ") + ")");
        if (b.panel.length) sebep.add("ara düğüm " + n + " panel köşesi (panel " + [...new Set(b.panel)].join(", ") + ")");
        if (b.mesnet.length || this.izgaraTaban(n)) sebep.add("ara düğüm " + n + "'de mesnet var");
        if (b.yuk.length) sebep.add("ara düğüm " + n + "'de düğüm yükü var");
        if (b.aksKat) sebep.add("ara düğüm " + n + "'e aks–kat elemanı bağlı");
        const s1 = z.sira[k - 1], s2 = z.sira[k];
        if (serbestUc(this.cubuk(s1.no), s1.ters ? "i" : "j").length || serbestUc(this.cubuk(s2.no), s2.ters ? "j" : "i").length) {
          sebep.add("ara düğüm " + n + "'de uç serbestliği (mafsal) var; iç uçlar sürekli olmalı");
        }
      }
      if (sebep.size) { red([...sebep].join("; ")); continue; }
      // yükler
      const yukler = [];
      let ofs = 0, yukRed = false;
      z.sira.forEach(function (s, k) {
        const c = cs[k], u2 = self.uclar(c), Lm = uzaklik(self.kon(u2[0]), self.kon(u2[1]));
        for (const y of self.m.ek_yukler) {
          if (!(y && y.tur === "cubuk" && +y.cubuk === s.no)) continue;
          const t = yukTasi(y, Lm, ofs, s.ters, eksenler[k], E);
          if (t) { t.cubuk = z.anahtar; yukler.push(t); } else yukRed = true;
        }
        ofs += Lm;
      });
      if (yukRed) { red("bir çubuk yükünün yerel yönü birleşik çubuğa taşınamıyor"); continue; }
      const ilkS = z.sira[0], sonS = z.sira[z.sira.length - 1];
      const si = serbestUc(this.cubuk(ilkS.no), ilkS.ters ? "j" : "i"), sj = serbestUc(this.cubuk(sonS.no), sonS.ters ? "i" : "j");
      const uyeler = new Set(z.cubuklar);
      this.m.ek_yukler = this.m.ek_yukler.filter(function (y) { return !(y && y.tur === "cubuk" && uyeler.has(+y.cubuk)); });
      for (const k of this.m.kren) {
        if (!k || !Array.isArray(k.yol)) continue;
        const i = k.yol.findIndex(function (x) { return uyeler.has(+x); });
        if (i < 0) continue;
        const kalan = k.yol.filter(function (x) { return !uyeler.has(+x); });
        kalan.splice(i, 0, z.anahtar);
        k.yol = kalan;
      }
      for (const no of z.cubuklar) if (no !== z.anahtar) this.cubukSilIc(no);
      ilk.i = this.refYaz(z.dugumler[0]); ilk.j = this.refYaz(z.dugumler[z.dugumler.length - 1]);
      serbestYaz(ilk, si, sj);
      this.m.ek_yukler = this.m.ek_yukler.concat(yukBirlestir(yukler, L));
      this.yetimSil(z.dugumler.slice(1, -1));
      sonuc.yeni.push(z.anahtar);
    }
    return sonuc;
  };

  // ================================================================= taşıma / kopyalama
  P_.dugumuTasiIc = function (n, P) {
    const d = this.harita().get(n);
    if (!d) throw new ModelHatasi("Düğüm " + n + " modelde yok.");
    if (uzaklik([d.X, d.Y, d.Z], P) <= this.tol) return n;
    // hedefte mevcut düğüm (aks kesişimi dahil): başvurular ona yazılır (aks kesişiminde {aks, z} REF'i)
    const o = this.bul(P, this.tol, new Set([n]));
    if (o != null) {
      const tabanMesnet = this.izgaraTaban(n) && !this.mesnetKaydi(n) && !this.mesnetli(o);
      this.refDegistir(new Map([[n, o]]));
      const i = this.m.dugumler.findIndex(function (x) { return x && +x.no === n; });
      if (i >= 0) this.m.dugumler.splice(i, 1);
      this._h = null;
      if (tabanMesnet && this.baglantilar().get(o)) this.m.mesnetler.push(this.temelMesnetKaydi(o));
      this.uyar("Düğüm " + n + " hedefteki düğüm " + o + " ile birleşti.");
      return o;
    }
    if (d.izgara) {
      const tabanMesnet = this.izgaraTaban(n) && !this.mesnetKaydi(n);
      const yeni = this.yeniDugumNo();
      const r = { no: yeni, X: r6(P[0]), Y: r6(P[1]), Z: r6(P[2]) };
      if (d.kayit && d.kayit.ad) r.ad = d.kayit.ad;
      this.m.dugumler.push(r);
      this._h = null;
      this.refDegistir(new Map([[n, yeni]]));
      const i = this.m.dugumler.findIndex(function (x) { return +x.no === n; });
      if (i >= 0) this.m.dugumler.splice(i, 1);
      this._h = null;
      const bag = this.baglantilar().get(yeni);
      if (tabanMesnet && bag && (bag.cubuk.length || bag.panel.length)) {
        this.m.mesnetler.push(this.temelMesnetKaydi(yeni));
        this.uyar("Temel düğümü " + n + " taşındı: aks–kat temel kuralı yerine açık mesnet kaydı yazıldı (düğüm " + yeni + ").");
      }
      this.uyar("Aks–kat düğümü " + n + " taşındı; aks dışına çıktığı için serbest düğüm " + yeni + " oldu.");
      return yeni;
    }
    if (d.kayit.tur === "bolme" || d.kayit.tur === "kesisim") {
      this.uyar("Düğüm " + n + " " + (d.kayit.tur === "bolme" ? "bölme" : "kesişim") + " düğümüydü; taşındığı için serbest koordinatlı oldu (aksaBagla ile yeniden bağlayın).");
      ["tur", "cubuk_i", "cubuk_j", "oran", "a", "b"].forEach(function (k) { delete d.kayit[k]; });
    }
    d.kayit.X = r6(P[0]); d.kayit.Y = r6(P[1]); d.kayit.Z = r6(P[2]);
    this._h = null;
    return n;
  };
  P_.secimCoz = function (secim) {
    const self = this;
    if (Array.isArray(secim)) return { dugumler: [], cubuklar: secim.map(Number), paneller: [] };
    if (secim && typeof secim === "object") {
      return { dugumler: (secim.dugumler || []).map(function (r) { return self.refNo(r); }),
        cubuklar: (secim.cubuklar || []).map(Number), paneller: (secim.paneller || []).map(Number) };
    }
    throw new ModelHatasi('Seçim çubuk numaraları dizisi ya da {"dugumler", "cubuklar", "paneller"} nesnesi olmalı.');
  };
  P_.panel = function (no) {
    const p = this.m.paneller.find(function (x) { return +x.no === +no; });
    if (!p) throw new ModelHatasi("Panel " + no + " modelde yok.");
    return p;
  };
  /** Dönüşüm altında yeni aci: eski y″ ekseninin R ile döndürülmüş hali yeni y″ olur. */
  P_.yeniAci = function (eskiEksen, Pa, Pb, R) {
    const ry = R(eskiEksen.y), en = yerelEksenVektor(Pa, Pb, 0);
    return r9(Math.atan2(ic(ry, en.z), ic(ry, en.y)) / D2R);
  };
  function yansimaMi(R) { return ic(dis(R([1, 0, 0]), R([0, 1, 0])), R([0, 0, 1])) < 0; }
  function yukDonustur(y, R) {
    const r = kopya(y);
    if (!R) return r;
    const ters = yansimaMi(R);
    if (y.tur === "cubuk") {
      const ly = yerelYon(y.yon);
      if (ly) {
        if (ly === "z" && ters) { for (const k of ["q1", "q2", "q", "P", "F"]) if (r[k] != null) r[k] = -r[k]; }
        return r;
      }
      const g = GLOBAL_YON[String(y.yon || "Z").toUpperCase()];
      if (!g) return null;
      const v = R(g);
      for (const ad of ["X", "Y", "Z"]) {
        const d = ic(v, GLOBAL_YON[ad]);
        if (Math.abs(Math.abs(d) - 1) < 1e-6) {
          r.yon = ad;
          if (d < 0) for (const k of ["q1", "q2", "q", "P", "F"]) if (r[k] != null) r[k] = -r[k];
          return r;
        }
      }
      return null;
    }
    if (y.tur === "dugum") {
      const F = R([+y.FX || 0, +y.FY || 0, +y.FZ || 0]), M = olcek(R([+y.MX || 0, +y.MY || 0, +y.MZ || 0]), ters ? -1 : 1);
      [["FX", F[0]], ["FY", F[1]], ["FZ", F[2]], ["MX", M[0]], ["MY", M[1]], ["MZ", M[2]]].forEach(function (a) {
        if (r[a[0]] != null || Math.abs(a[1]) > 1e-12) r[a[0]] = r9(a[1]);
      });
      return r;
    }
    return r;
  }
  function mesnetDonustur(s, R) {
    const r = kopya(s);
    if (!R) return r;
    const t = [!!s.ux, !!s.uy, !!s.uz], d = [!!s.rx, !!s.ry, !!s.rz];
    const ayni = function (l) { return l[0] === l[1] && l[1] === l[2]; };
    if (ayni(t) && ayni(d)) return r;
    const per = [0, 1, 2].map(function (i) {
      const e = [0, 0, 0]; e[i] = 1;
      const v = R(e);
      return [0, 1, 2].find(function (k) { return Math.abs(Math.abs(v[k]) - 1) < 1e-6; });
    });
    if (per.some(function (x) { return x == null; })) return null;
    const ta = ["ux", "uy", "uz"], da = ["rx", "ry", "rz"];
    for (let i = 0; i < 3; i++) { r[ta[per[i]]] = t[i]; r[da[per[i]]] = d[i]; }
    return r;
  }
  P_.kopyalaIc = function (s, f, R, sec) {
    sec = sec || {};
    const self = this, esle = new Map(), cesle = new Map(), yeniP = [];
    const yeniDg = [];
    const yd = function (n) {
      if (!esle.has(n)) { const P = f(self.kon(n)), var_ = self.bul(P); esle.set(n, var_ != null ? var_ : self.dugumEkle(P)); if (var_ == null) yeniDg.push(esle.get(n)); }
      return esle.get(n);
    };
    for (const no of s.cubuklar) {
      const c = this.cubuk(no), u = this.uclar(c);
      const na = yd(u[0]), nb = yd(u[1]);
      if (na === nb) { this.uyar("Çubuk " + no + " kopyası sıfır boylu olurdu; atlandı."); continue; }
      const var_ = this.ciftBul(na, nb);
      if (var_ != null) { this.uyar("Çubuk " + no + " kopyası mevcut çubuk " + var_ + " ile çakışıyor; atlandı."); continue; }
      const oz = ozellikKopya(c);
      delete oz.kaynak;
      if (c.serbest) oz.serbest = kopya(c.serbest);
      if (R) oz.aci = this.yeniAci(this.cubukEksen(c), this.kon(na), this.kon(nb), R);
      cesle.set(+no, this.ekCubuk(oz, na, nb));
    }
    for (const no of s.paneller) {
      const p = this.panel(no);
      let kose = p.kose.map(function (r) { return yd(self.refNo(r, false)); });
      if (R && yansimaMi(R)) kose = kose.reverse();
      const oz = kopya(p); delete oz.no; delete oz.kose; delete oz.kaynak;
      const yeni = Object.assign({ no: this.yeniNo(this.m.paneller, this.m.dosemeler), kose: kose.map(function (n) { return self.refYaz(n); }) }, oz);
      this.m.paneller.push(yeni);
      yeniP.push([+no, yeni.no]);
    }
    for (const n of s.dugumler) yd(n);
    if (sec.yukler !== false) {
      const pesle = new Map(yeniP), secDg = new Set(s.dugumler);
      for (const y of this.m.ek_yukler.slice()) {
        if (!y) continue;
        let hedef = null;
        if (y.tur === "cubuk" && cesle.has(+y.cubuk)) hedef = ["cubuk", cesle.get(+y.cubuk)];
        else if (y.tur === "panel" && pesle.has(+y.panel)) hedef = ["panel", pesle.get(+y.panel)];
        else if (y.tur === "dugum") { const n = this.yukDugumu(y); if (n != null && secDg.has(n) && esle.get(n) !== n) hedef = ["dugum", esle.get(n)]; }
        if (!hedef) continue;
        const r = yukDonustur(y, R);
        if (!r) { this.uyar("Bir yük dönüşüm altında eksen doğrultusuna gelmediği için kopyalanmadı."); continue; }
        if (hedef[0] === "dugum") { delete r.aks; delete r.kat; r.dugum = this.refYaz(hedef[1]); } else r[hedef[0]] = hedef[1];
        this.m.ek_yukler.push(r);
      }
    }
    if (sec.mesnetler !== false) {
      for (const [eski, yeni] of esle) {
        if (eski === yeni || !this.mesnetli(eski) || this.mesnetli(yeni)) continue;
        const kay = this.mesnetKaydi(eski);
        const r = mesnetDonustur(kay ? kay : this.temelMesnetKaydi(eski), R);
        if (!r) { this.uyar("Düğüm " + eski + " mesnedi dönüşüm altında eksenlere gelmediği için kopyalanmadı."); continue; }
        delete r.kaynak;
        r.dugum = this.refYaz(yeni);
        this.m.mesnetler.push(r);
      }
    }
    // kopyanın yeni uçları mevcut bir çubuğun iç noktasına düşüyorsa o çubuk orada bölünür (kopyaların kendisi hariç)
    this.uclardaBol(yeniDg, new Set(cesle.values()));
    return { cubuklar: [...cesle.values()], paneller: yeniP.map(function (x) { return x[1]; }), dugumler: [...new Set(esle.values())] };
  };
  /** Yeni serbest düğüm kaydı (konumda başka düğüm olsa da: taşınırken yerini boşaltacak düğümün konumu için). */
  P_.dugumZorla = function (P) {
    const no = this.yeniDugumNo();
    const r = { no: no, X: r6(P[0]), Y: r6(P[1]), Z: r6(P[2]) };
    this.m.dugumler.push(r);
    this.harita().set(no, { no: no, X: r.X, Y: r.Y, Z: r.Z, izgara: false, aks: null, kat: null, kayit: r });
    return no;
  };
  /** Bölme / kesişim kayıtlarının dayandığı düğümler (bu düğümler yerinde kalmalı: bağımlı düğüm onlarla tanımlı). */
  P_.dayanakDugumler = function () {
    const self = this, out = new Set();
    const ekle = function (r) { try { const n = self.refNo(r, false); if (n != null) out.add(n); } catch (e) { /* yoksay */ } };
    for (const d of this.m.dugumler) {
      if (d && d.tur === "bolme") { ekle(d.cubuk_i); ekle(d.cubuk_j); }
      else if (d && d.tur === "kesisim") { (d.a || []).forEach(ekle); (d.b || []).forEach(ekle); }
    }
    return out;
  };
  /**
   * Taşı / döndür / ayna (kopyasız) — "koparak taşıma": seçilen çubuk ve panellerin uçları f ile hedefe yazılır; seçilmeyen
   * elemanlarla (aks–kat elemanları, bölme düğümlerinin dayanakları dahil) paylaşılan düğümler YERİNDE kalır. Hedef mevcut bir
   * düğüme (aks kesişimi dahil) düşüyorsa o düğüm kullanılır, değilse yeni düğüm kaydı açılır. Yalnız seçime ait düğümler silinir;
   * açık mesnetleri ve düğüm yükleri hedefe taşınır (mesnetli düğümün hedefine kopya işlemlerindeki gibi mesnet yazılır).
   * Çubuk ve panel numaraları, yükleri, kren yolları korunur. Açıkça seçilen düğümler (s.dugumler) yerinde taşınır.
   * Ret (dönüş {red: [metin]}, model değiştirilmemiş sayılır): sıfır boylu çubuk, hedefte mevcut çubukla aynı iki düğüm ya da
   * eş doğrusal üst üste binme, bozuk / mevcut panelle aynı köşeli panel.
   * Dönüş: Map(eski düğüm → yeni düğüm).
   */
  P_.tasiIc = function (s, f, R) {
    const self = this, tol = this.tol, esle = new Map();
    // açıkça seçilen düğümler: düğümün kendisi taşınır (bağlı her şey izler)
    const acik = [...new Set(s.dugumler)].map(function (n) { return [n, f(self.kon(n))]; });
    for (const a of acik) esle.set(a[0], this.dugumuTasiIc(a[0], a[1]));
    const acikEsle = new Map(esle);
    const secC = new Set(s.cubuklar.map(Number)), secP = new Set(s.paneller.map(Number));
    const cs = [...secC].map(function (no) { return self.cubuk(no); });
    const ps = [...secP].map(function (no) { return self.panel(no); });
    const dg = new Set();
    for (const c of cs) this.uclar(c).forEach(function (n) { dg.add(n); });
    for (const p of ps) p.kose.forEach(function (r) { dg.add(self.refNo(r, false)); });
    for (const v of esle.values()) dg.delete(v);
    if (!dg.size) { this.uretecIzle(secC, secP, acikEsle, f, R, []); return esle; }
    // paylaşılan düğümler: seçilmeyen çubuk / panel uçları, aks–kat elemanları, bölme / kesişim dayanakları
    const paylasilan = this.dayanakDugumler();
    for (const c of this.m.cubuklar) if (!secC.has(+c.no)) { try { this.uclar(c).forEach(function (n) { paylasilan.add(n); }); } catch (e) { /* yoksay */ } }
    for (const p of this.m.paneller) if (!secP.has(+p.no)) { for (const r of p.kose || []) { try { paylasilan.add(this.refNo(r, false)); } catch (e) { /* yoksay */ } } }
    for (const n of this.aksKatDugumleri().keys()) paylasilan.add(n);
    const P0 = new Map(), T = new Map();
    for (const n of dg) { P0.set(n, this.kon(n)); T.set(n, f(this.kon(n))); }
    const kendi = new Set([...dg].filter(function (n) { return !paylasilan.has(n); }));
    // yerini boşaltan düğümler (seçime ait serbest kayıtlar): hedef aramasında yok sayılır
    const bosalan = new Set([...kendi].filter(function (n) { const d = self.harita().get(n); return d && !d.izgara && uzaklik(T.get(n), P0.get(n)) > tol; }));
    const mesnetliOnce = new Map([...dg].map(function (n) { return [n, self.mesnetli(n)]; }));
    const eksen = new Map(cs.map(function (c) { return [c, self.cubukEksen(c)]; }));
    const hedef = new Map(), yeniDg = [];
    for (const n of dg) {
      if (uzaklik(T.get(n), P0.get(n)) <= tol) { hedef.set(n, n); continue; }
      const o = this.bul(T.get(n), tol, bosalan);
      if (o != null) hedef.set(n, o);
      else { const z = this.dugumZorla(T.get(n)); yeniDg.push(z); hedef.set(n, z); }
    }
    // ret denetimleri
    const red = [];
    const ciftAnahtar = function (a, b) { return a < b ? a + "-" + b : b + "-" + a; };
    const digerleri = [];
    const ciftler = new Map();
    for (const c of this.m.cubuklar) {
      if (secC.has(+c.no)) continue;
      let u; try { u = this.uclar(c); } catch (e) { continue; }
      ciftler.set(ciftAnahtar(u[0], u[1]), +c.no);
      digerleri.push({ no: +c.no, A: this.kon(u[0]), B: this.kon(u[1]) });
    }
    const yeniUc = new Map();
    for (const c of cs) {
      const u = this.uclar(c), a = hedef.get(u[0]), b = hedef.get(u[1]);
      yeniUc.set(c, [a, b]);
      if (a === b) { red.push("Çubuk " + c.no + " taşınınca iki ucu aynı düğüme (" + a + ") düşüyor; sıfır boylu çubuk olurdu."); continue; }
      const k = ciftAnahtar(a, b);
      if (ciftler.has(k)) { red.push("Çubuk " + c.no + " hedefte çubuk " + ciftler.get(k) + " ile çakışıyor (aynı iki düğüm)."); continue; }
      ciftler.set(k, +c.no);
      const A = T.get(u[0]), B = T.get(u[1]), L = uzaklik(A, B);
      for (const o of digerleri) {
        const ra = dogruyaUzaklik(o.A, A, B), rb = dogruyaUzaklik(o.B, A, B);
        if (ra.d > tol || rb.d > tol) continue;
        const lo = Math.max(0, Math.min(ra.t, rb.t)), hi = Math.min(1, Math.max(ra.t, rb.t));
        if ((hi - lo) * L > tol) { red.push("Çubuk " + c.no + " hedefte çubuk " + o.no + " ile eş doğrusal üst üste biniyor."); break; }
      }
    }
    const panelAnahtar = function (l) { return l.slice().sort(function (a, b) { return a - b; }).join(","); };
    const panelSet = new Set(this.m.paneller.filter(function (p) { return !secP.has(+p.no); }).map(function (p) {
      try { return panelAnahtar(p.kose.map(function (r) { return self.refNo(r, false); })); } catch (e) { return ""; }
    }));
    const yeniKose = new Map();
    for (const p of ps) {
      let k = p.kose.map(function (r) { return hedef.get(self.refNo(r, false)); });
      if (R && yansimaMi(R)) k = k.reverse();
      yeniKose.set(p, k);
      if (new Set(k).size !== k.length) { red.push("Panel " + p.no + " taşınınca köşeleri çakışıyor."); continue; }
      const g = panelGeometri(p.kose.map(function (r) { return T.get(self.refNo(r, false)); }), 0.005);
      if (!g.ok) { red.push("Panel " + p.no + " taşınınca bozuluyor: " + g.sebep + "."); continue; }
      if (panelSet.has(panelAnahtar(k))) red.push("Panel " + p.no + " hedefte aynı köşeli bir panelle çakışıyor.");
    }
    if (red.length) return { red: red };
    // uygula: çubuk ve panel uçları
    for (const c of cs) {
      const u = yeniUc.get(c);
      c.i = this.refYaz(u[0]); c.j = this.refYaz(u[1]);
      if (R) { const e = eksen.get(c); if (e) c.aci = this.yeniAci(e, this.kon(u[0]), this.kon(u[1]), R); }
    }
    for (const p of ps) p.kose = yeniKose.get(p).map(function (n) { return self.refYaz(n); });
    // mesnetler ve düğüm yükleri (üretecin mesnet kopyaları izlenir: kayıt elemanlarla taşınırsa kopya yine üretecindir)
    const tasinanMesnet = [];
    for (const n of dg) {
      const t = hedef.get(n);
      esle.set(n, t);
      if (t === n) continue;
      if (mesnetliOnce.get(n) && !this.mesnetli(t)) {
        const kay = this.mesnetKaydi(n);
        const r = mesnetDonustur(kay ? kay : this.temelMesnetKaydi(n), R);
        if (r) {
          const u = r.kaynak && r.kaynak.uretec != null ? +r.kaynak.uretec : null;
          delete r.kaynak; r.dugum = this.refYaz(t); this.m.mesnetler.push(r);
          if (u != null) tasinanMesnet.push({ r: r, uretec: u });
        }
        else this.uyar("Düğüm " + n + " mesnedi dönüşüm altında eksenlere gelmediği için taşınmadı.");
      }
      if (!kendi.has(n)) continue;
      this.m.mesnetler = this.m.mesnetler.filter(function (sk) { try { return self.refNo(sk.dugum, false) !== n; } catch (e) { return true; } });
      const yeniY = [];
      for (const y of this.m.ek_yukler) {
        if (this.yukDugumu(y) !== n) { yeniY.push(y); continue; }
        const r = yukDonustur(y, R);
        if (!r) { this.uyar("Düğüm " + n + " yükü dönüşüm altında eksen doğrultusuna gelmediği için kaldırıldı."); continue; }
        delete r.aks; delete r.kat; r.dugum = this.refYaz(t);
        yeniY.push(r);
      }
      this.m.ek_yukler = yeniY;
    }
    this._h = null;
    this.yetimSil([...kendi].filter(function (n) { return hedef.get(n) !== n; }));
    // yeni uç düğümü seçilmeyen bir çubuğun iç noktasına düştüyse o çubuk orada bölünür (bağlantısız düğüm mekanizma olurdu)
    this.uclardaBol(yeniDg, secC);
    this.uretecIzle(secC, secP, acikEsle, f, R, tasinanMesnet);
    return esle;
  };
  /** Üretecin (kaynak.uretec === no) çubuk ve panel geometrisinin imzası (1 mm; uç sırası ve eleman numarası önemsiz). */
  P_.uretecImzasi = function (no) {
    const self = this, k = function (n) { return self.kon(n).map(function (v) { return Math.round(v * 1e3); }).join(","); };
    const ait = function (x) { return !!(x && x.kaynak && x.kaynak.uretec != null && +x.kaynak.uretec === +no); };
    const l = [];
    for (const c of this.m.cubuklar) if (ait(c)) { const u = this.uclar(c), a = k(u[0]), b = k(u[1]); l.push("c:" + (a < b ? a + "|" + b : b + "|" + a)); }
    for (const p of this.m.paneller) if (ait(p)) l.push("p:" + p.kose.map(function (r) { return k(self.refNo(r, false)); }).sort().join("|"));
    return l.sort().join(";");
  };
  /**
   * URETEC-TASI — taşı / döndür / ayna (kopyasız) üreteç elemanlarını etkilediyse kayıt (bina.uretecler) tutarlı bırakılır; yoksa
   * Üreteci düzenle elemanları sessizce ESKİ yerde yeniden üretirdi:
   *  - üretecin bütün çubuk ve panelleri seçildiyse (katı hareket) kaydın REF parametreleri (çapraz goz; makas bas/son; beşik çerçeve
   *    taban1/taban2) aynı dönüşümle hedef düğüme yazılır (makas "yukari", beşik "yon" vektörleri de döner); açıkça taşınan düğüme dayanan
   *    REF o düğümü izler. Kayıt yeni yerde yeniden üretildiğinde (kuru çalıştırma) elemanlarla aynı çubuk / panel geometrisini veriyorsa
   *    kayıt izler (not düşülür);
   *  - vermiyorsa (kısmi taşıma, düğüm taşımasıyla şekli bozulan eleman, simetrik olmayan çaprazın aynası, dönüştürülemeyen aşık / kren /
   *    cephe kayıtları) taşınan ya da şekli değişen elemanlar üreteçten ayrılır (kaynak.uretec silinir) ve not düşülür; üretecin çubuğu /
   *    paneli kalmadıysa kayıt silinir, kalan düğüm / mesnet / kren kayıtları da ayrılır.
   */
  P_.uretecIzle = function (secC, secP, acikEsle, f, R, tasinanMesnet) {
    const self = this;
    if (!this.m.uretecler.length && !this.m.cubuklar.some(function (c) { return c && c.kaynak && c.kaynak.uretec != null; })) return;
    const acikHedef = new Set([...acikEsle].filter(function (e) { return e[0] !== e[1]; }).map(function (e) { return e[1]; }));
    const etkC = new Set(secC), etkP = new Set(secP);
    if (acikHedef.size) {
      for (const c of this.m.cubuklar) { try { if (this.uclar(c).some(function (n) { return acikHedef.has(n); })) etkC.add(+c.no); } catch (e) { /* yoksay */ } }
      for (const p of this.m.paneller) { try { if (p.kose.some(function (r) { return acikHedef.has(self.refNo(r, false)); })) etkP.add(+p.no); } catch (e) { /* yoksay */ } }
    }
    const nolar = new Set();
    for (const c of this.m.cubuklar) if (etkC.has(+c.no) && c.kaynak && c.kaynak.uretec != null) nolar.add(+c.kaynak.uretec);
    for (const p of this.m.paneller) if (etkP.has(+p.no) && p.kaynak && p.kaynak.uretec != null) nolar.add(+p.kaynak.uretec);
    const ALAN = { capraz: ["goz"], makas: ["bas", "son"], "besik-cerceve": ["taban1", "taban2"] };
    const kaynakSil = function (x) { if (!x || !x.kaynak) return; delete x.kaynak.uretec; if (!Object.keys(x.kaynak).length) delete x.kaynak; };
    for (const no of [...nolar].sort(function (a, b) { return a - b; })) {
      const ait = function (x) { return !!(x && x.kaynak && x.kaynak.uretec != null && +x.kaynak.uretec === no); };
      const kayit = this.m.uretecler.find(function (u) { return u && +u.no === no; }) || null;
      const cub = this.m.cubuklar.filter(ait), pan = this.m.paneller.filter(ait);
      const kati = cub.every(function (c) { return secC.has(+c.no); }) && pan.every(function (p) { return secP.has(+p.no); });
      let izledi = false;
      if (kayit && ALAN[kayit.tur]) {
        const yedek = kopya(kayit);
        let degisti = false;
        try {
          const yeniRef = function (r) {
            const n = self.refNo(r, false);
            if (n == null) throw new ModelHatasi("REF");
            let t = n;
            if (acikHedef.has(n)) { degisti = true; return r; }        // düğüm taşıması (refDegistir) REF'i zaten yeni düğüme yazdı
            if (acikEsle.has(n)) t = acikEsle.get(n);
            else if (kati) { t = self.bul(f(self.kon(n))); if (t == null) throw new ModelHatasi("hedef"); }
            if (t === n) return r;
            degisti = true;
            return self.refYaz(t);
          };
          for (const a of ALAN[kayit.tur]) if (kayit[a] != null) kayit[a] = Array.isArray(kayit[a]) ? kayit[a].map(yeniRef) : yeniRef(kayit[a]);
          if (kati && R && kayit.tur === "makas") kayit.yukari = R(nokta3(kayit.yukari || [0, 0, 1], "yukari")).map(r9);
          if (kati && R && kayit.tur === "besik-cerceve" && kayit.yon) kayit.yon = R(nokta3(kayit.yon, "yon")).map(r9);
          if (kati) for (const t of tasinanMesnet) if (t.uretec === no) t.r.kaynak = { uretec: no };
          if (degisti) {
            const once = this.uretecImzasi(no);
            const r = uretecGuncelle(this.m, no, {});
            izledi = once === new Is(r.model).uretecImzasi(no);
          }
        } catch (e) { izledi = false; }
        if (!izledi) {
          Object.keys(kayit).forEach(function (k) { delete kayit[k]; });
          Object.assign(kayit, yedek);
          for (const t of tasinanMesnet) if (t.uretec === no) delete t.r.kaynak;
        }
      }
      if (izledi) { this.uyar("Üreteç " + no + " (" + kayit.tur + ") kaydı " + (kati ? "elemanlarıyla birlikte taşındı" : "taşınan düğümü izledi") + ": Üreteci düzenle onları yeni yerde üretir."); continue; }
      const ayrC = cub.filter(function (c) { return etkC.has(+c.no); }).map(function (c) { return +c.no; });
      const ayrP = pan.filter(function (p) { return etkP.has(+p.no); }).map(function (p) { return +p.no; });
      cub.forEach(function (c) { if (etkC.has(+c.no)) kaynakSil(c); });
      pan.forEach(function (p) { if (etkP.has(+p.no)) kaynakSil(p); });
      const kalan = this.m.cubuklar.some(ait) || this.m.paneller.some(ait);
      if (!kalan) {
        this.m.dugumler.forEach(function (d) { if (ait(d)) kaynakSil(d); });
        this.m.mesnetler.forEach(function (sk) { if (ait(sk)) kaynakSil(sk); });
        this.m.kren.forEach(function (k) { if (ait(k)) kaynakSil(k); });
        this.m.uretecler = this.m.uretecler.filter(function (u) { return u !== kayit; });
      }
      const ad = [ayrC.length ? "Çubuk " + ayrC.join(", ") : "", ayrP.length ? "panel " + ayrP.join(", ") : ""].filter(Boolean).join(", ");
      this.uyar(ad + (secC.size || secP.size ? " taşındığı" : " şekli değiştiği") + " için üreteçten (kayıt " + no + ") ayrıldı: Üreteci düzenle artık onları yeniden üretmez" +
        (kalan ? "." : "; üretecin başka elemanı kalmadığı için kaydı silindi."));
    }
  };

  // ================================================================= paneller
  function panelGeometri(P, tolD) {
    const n2 = newell(P), A2 = boy(n2);
    if (P.length < 3) return { ok: false, sebep: "en az üç köşe gerekir" };
    let cevre = 0;
    for (let k = 0; k < P.length; k++) cevre += uzaklik(P[k], P[(k + 1) % P.length]);
    if (A2 / 2 < 1e-9 * Math.max(1, cevre * cevre)) return { ok: false, sebep: "alan sıfır (köşeler bir doğru üzerinde)" };
    const n = olcek(n2, 1 / A2);
    const c = olcek(P.reduce(topla, [0, 0, 0]), 1 / P.length);
    let sapma = 0;
    for (const p of P) sapma = Math.max(sapma, Math.abs(ic(cikar(p, c), n)));
    if (sapma > tolD) return { ok: false, sebep: "düzlemsel değil (en büyük sapma " + fmt(sapma * 1000, 1) + " mm > " + fmt(tolD * 1000, 1) + " mm)", normal: n, sapma: sapma };
    let donus = 0, esDogrusal = 0;
    for (let k = 0; k < P.length; k++) {
      const a = cikar(P[(k + 1) % P.length], P[k]), b = cikar(P[(k + 2) % P.length], P[(k + 1) % P.length]);
      const cr = ic(dis(a, b), n), dt = ic(a, b);
      if (Math.abs(cr) <= 1e-9 * boy(a) * boy(b)) { esDogrusal++; if (dt < 0) return { ok: false, sebep: "kenar geri dönüyor" }; continue; }
      if (cr < 0) return { ok: false, sebep: "dışbükey değil (köşe " + ((k + 1) % P.length + 1) + " içe dönük)", normal: n };
      donus += Math.atan2(cr, dt);
    }
    if (Math.abs(donus - 2 * Math.PI) > 1e-6) return { ok: false, sebep: "kenarlar kendini kesiyor", normal: n };
    return { ok: true, normal: n, alan: A2 / 2, sapma: sapma, esDogrusal: esDogrusal,
      egim: r9(Math.acos(Math.min(1, Math.abs(n[2]))) / D2R) };
  }
  P_.panelKenarlari = function (p) {
    const self = this;
    const nolar = p.kose.map(function (r) { return self.refNo(r, false); });
    const tol = this.tol;
    const veri = this.m.cubuklar.map(function (c) { const u = self.uclar(c); return { no: +c.no, A: self.kon(u[0]), B: self.kon(u[1]) }; });
    return nolar.map(function (a, k) {
      const b = nolar[(k + 1) % nolar.length], A = self.kon(a), B = self.kon(b), L = uzaklik(A, B);
      const parca = [];
      for (const v of veri) {
        const ra = dogruyaUzaklik(v.A, A, B), rb = dogruyaUzaklik(v.B, A, B);
        if (ra.d > tol || rb.d > tol) continue;
        const t0 = Math.min(ra.t, rb.t), t1 = Math.max(ra.t, rb.t);
        if (t1 * L <= tol || (1 - t0) * L <= tol || (t1 - t0) * L <= tol) continue;
        parca.push([Math.max(0, t0), Math.min(1, t1), v.no]);
      }
      parca.sort(function (x, y) { return x[0] - y[0]; });
      const bosluk = [];
      let son = 0;
      for (const q of parca) { if ((q[0] - son) * L > tol) bosluk.push([r9(son * L), r9(q[0] * L)]); son = Math.max(son, q[1]); }
      if ((1 - son) * L > tol) bosluk.push([r9(son * L), r9(L)]);
      return { kenar: k + 1, dugumler: [a, b], uzunluk: r9(L), cubuklar: parca.map(function (q) { return q[2]; }), tam: bosluk.length === 0, bosluklar: bosluk };
    });
  };

  // ================================================================= üreteç altyapısı
  P_.uretecBasla = function (tur, param, zorunluNo) {
    const no = zorunluNo || this.yeniNo(this.m.uretecler);
    const kayit = Object.assign({ no: no, tur: tur }, kopya(param), { bolunen: [], tur_degisen: [] });
    this.m.uretecler.push(kayit);
    this.kaynak = { uretec: no };
    return kayit;
  };
  P_.uretecBitir = function (kayit) {
    this.kaynak = null;
    if (!kayit.bolunen.length) delete kayit.bolunen;
    if (!kayit.tur_degisen.length) delete kayit.tur_degisen;
  };
  function kesitOz(k) { return k != null && k !== "" ? { kesit: k } : {}; }
  function mafsalOz(evet) { return evet ? { serbest: { i: ["My", "Mz"], j: ["My", "Mz"] } } : {}; }
  P_.kesitUyar = function (k, ad) { if (k == null || k === "") this.uyar(ad + " için kesit verilmedi; çubuklar kesitsiz eklendi (çözümden önce kesit atayın)."); };
  P_.uretecSilIc = function (no) {
    no = +no;
    const kayit = this.m.uretecler.find(function (u) { return +u.no === no; });
    if (!kayit) throw new ModelHatasi("Üreteç " + no + " modelde yok.");
    const ait = function (x) { return x && x.kaynak && +x.kaynak.uretec === no; };
    this.m.kren = this.m.kren.filter(function (k) { return !ait(k); });       // önce üretecin kren kayıtları (yol uyarısı olmasın)
    for (const c of this.m.cubuklar.filter(ait)) this.cubukSilIc(+c.no);
    const silP = new Set(this.m.paneller.filter(ait).map(function (p) { return +p.no; }));
    this.m.paneller = this.m.paneller.filter(function (p) { return !silP.has(+p.no); });
    this.m.ek_yukler = this.m.ek_yukler.filter(function (y) { return !(y && y.tur === "panel" && silP.has(+y.panel)); });
    this.m.mesnetler = this.m.mesnetler.filter(function (s) { return !ait(s); });
    for (const d of kayit.tur_degisen || []) { const c = this.cubukBul(d.cubuk); if (c) c.tur = d.tur; }
    // aynı özgün çubuğun art arda bölünmesiyle oluşan gruplar ortak üyeden birleştirilir ([3,4] + [4,5] → [3,4,5])
    const birlesikGruplar = [];
    for (const grup of kayit.bolunen || []) {
      const ortak = birlesikGruplar.filter(function (g) { return grup.some(function (x) { return g.has(x); }); });
      const yeni = new Set(grup);
      for (const g of ortak) { g.forEach(function (x) { yeni.add(x); }); birlesikGruplar.splice(birlesikGruplar.indexOf(g), 1); }
      birlesikGruplar.push(yeni);
    }
    for (const grup of birlesikGruplar) {
      const var_ = [...grup].filter(function (x) { return this.cubukBul(x); }, this);
      if (var_.length >= 2) {
        const r = this.birlestirIc(var_, true);
        if (r.red.length) this.uyar("Üreteç " + no + " silinirken bölünen çubuklar (" + var_.join(", ") + ") yeniden birleştirilemedi: " + r.red[0].sebep + ".");
      }
    }
    this.yetimSil(this.m.dugumler.filter(ait).map(function (d) { return +d.no; }));
    this.m.uretecler = this.m.uretecler.filter(function (u) { return u !== kayit; });
    return kayit;
  };

  // ---------------------------------------------------------------- çapraz
  P_.gozSirala = function (nolar) {
    const self = this, P = nolar.map(function (n) { return self.kon(n); });
    const n = newell(P);
    if (boy(n) < 1e-9) throw new ModelHatasi("Göz köşeleri bir doğru üzerinde; çapraz gözü dört köşeli düzlemsel bir çerçeve olmalı.");
    const dusey = Math.abs(n[2]) < 0.3 * boy(n);
    if (!dusey) return { s: nolar.slice(), dusey: false };
    let enIyi = 0, ez = Infinity;
    for (let k = 0; k < 4; k++) { const z = P[k][2] + P[(k + 1) % 4][2]; if (z < ez - 1e-9) { ez = z; enIyi = k; } }
    let a = enIyi, b = (enIyi + 1) % 4;
    const h = cikar(P[b], P[a]), eksen = Math.abs(h[0]) >= Math.abs(h[1]) ? 0 : 1;
    if (P[b][eksen] < P[a][eksen]) { const t = a; a = b; b = t; }
    const komsu = function (k, haric) { return [(k + 1) % 4, (k + 3) % 4].find(function (x) { return x !== haric; }); };
    return { s: [nolar[a], nolar[b], nolar[komsu(b, a)], nolar[komsu(a, b)]], dusey: true };
  };
  P_.caprazIc = function (goz, tip, sec, zorunluNo) {
    sec = Object.assign({ mafsalli_uclar: true, yalniz_cekme: false, kesit: null, e: null, a: null, kesisim: "serbest", kolon: "sag", taraf: "iki" }, sec || {});
    if (CAPRAZ_TIPLERI.indexOf(tip) < 0) throw new ModelHatasi("Çapraz tipi " + JSON.stringify(tip) + " tanımsız; seçenekler: " + CAPRAZ_TIPLERI.join(", ") + ".");
    if (!Array.isArray(goz) || goz.length !== 4) throw new ModelHatasi("Çapraz gözü dört köşe düğümüyle verilmeli.");
    let nolar = goz.map(function (r) { return this.refNo(r); }, this);
    if (new Set(nolar).size !== 4) throw new ModelHatasi("Göz köşeleri dört farklı düğüm olmalı.");
    const bolmeli = ["V", "ters-V", "K", "dismerkez-tek", "dismerkez-ters-V", "diz"].indexOf(tip) >= 0;
    if (bolmeli && this.aksKatVar()) this.genellestirIc();
    const gz = this.gozSirala(nolar), s = gz.s;
    const A = s[0], B = s[1], C = s[2], D = s[3];
    const self = this;
    const kayit = this.uretecBasla("capraz", { goz: s.map(function (n) { return self.refYaz(n); }), tip: tip, secenek: sec }, zorunluNo);
    this.kesitUyar(sec.kesit, "Çapraz");
    const oz = Object.assign({ tur: "capraz" }, kesitOz(sec.kesit), sec.yalniz_cekme ? { yalniz_cekme: true } : {}, mafsalOz(sec.mafsalli_uclar !== false));
    const cap = function (a, b) { return self.ekCubukTekil(Object.assign(kopya(oz)), a, b); };
    const kenar = function (a, b, t) {
      const r = self.noktadaBol(ara(self.kon(a), self.kon(b), t), kayit);
      if (!r.bolundu && self.bul(ara(self.kon(a), self.kon(b), t)) === r.no && !self.ciftVarMi(r.no)) {
        self.uyar("Düğüm " + a + "–" + b + " kenarında çubuk yok; bölme düğümü " + r.no + " çubuksuz kaldı (kenar elemanını çizin).");
      }
      return r.no;
    };
    const Lk = function (a, b) { return uzaklik(self.kon(a), self.kon(b)); };
    const bagIsaretle = function (a, b) {
      const no = self.ciftBul(a, b);
      if (no == null) { self.uyar("Bağ kirişi (" + a + "–" + b + ") kenarında çubuk yok; bağ kirişi işaretlenemedi."); return null; }
      const c = self.cubuk(no);
      kayit.tur_degisen.push({ cubuk: no, tur: c.tur || "kiris" });
      c.tur = "bag";
      return no;
    };
    const eklenen = [];
    const ekle = function (a, b) { const n = cap(a, b); if (n != null) eklenen.push(n); };
    let bag = null;
    if (tip === "X") {
      if (sec.kesisim === "bagli") {
        const PA = this.kon(A), PC = this.kon(C), PB = this.kon(B), PD = this.kon(D);
        const r = parcaKesisim(PA, PC, PB, PD, Math.max(this.tol, 1e-6 + 1e-3 * uzaklik(PA, PC)));
        const M = r && !r.paralel ? this.dugumEkle(r.P) : this.dugumEkle(ara(PA, PC, 0.5));
        ekle(A, M); ekle(M, C); ekle(B, M); ekle(M, D);
      } else { ekle(A, C); ekle(B, D); }
    } else if (tip === "tek-/") ekle(A, C);
    else if (tip === "tek-\\") ekle(B, D);
    else if (tip === "V") {
      const M = kenar(A, B, 0.5); ekle(M, D); ekle(M, C);
      // temel seviyesindeki tepe bölme noktasıdır: temel kuralı (C3) bölme düğümüne mesnet vermez → açık mafsal mesnet
      const z0 = this.temelKotu(), d = this.harita().get(M);
      if (z0 != null && d && !d.izgara && Math.abs(d.Z - z0) <= this.tol && !this.mesnetli(M)) {
        this.m.mesnetler.push({ dugum: this.refYaz(M), ux: true, uy: true, uz: true, rx: false, ry: false, rz: false, kaynak: { uretec: kayit.no } });
        this.uyar("V çaprazın tepesi (düğüm " + M + ") temel seviyesinde bir bölme noktası; temel mesnedi yalnız aks kesişimlerine verildiği için buraya mafsal mesnet eklendi.");
      }
    }
    else if (tip === "ters-V") { const M = kenar(D, C, 0.5); ekle(A, M); ekle(B, M); }
    else if (tip === "K") {
      if (sec.kolon === "sol") { const M = kenar(A, D, 0.5); ekle(B, M); ekle(C, M); }
      else { const M = kenar(B, C, 0.5); ekle(A, M); ekle(D, M); }
      this.uyar("K çapraz düzeni TBDY 2018 9.6.4.2 / 9.7.4.2 uyarınca deprem yüklerini taşıyan sistem olarak kullanılamaz; yalnız statik/rüzgâr bağı olarak kullanın.");
    } else if (tip === "dismerkez-tek") {
      const L = Lk(D, C), e = +sec.e;
      if (!(e > 0 && e < L)) throw new ModelHatasi("dismerkez-tek: e (bağ kirişi boyu, m) 0 ile kiriş boyu " + fmt(L, 3) + " arasında olmalı.");
      if (sec.taraf === "sol") { const E = kenar(D, C, e / L); ekle(B, E); bag = bagIsaretle(D, E); }
      else { const E = kenar(D, C, 1 - e / L); ekle(A, E); bag = bagIsaretle(E, C); }
      this.uyar("Dışmerkez çapraz: kolona bitişik bağ kirişi için e ≤ 1,6·Mp/Vp (ÇYTHYE / TBDY 2018 Denk. 9.22) koşulunu bağ kirişi kesitiyle denetleyin (e = " + fmt(e, 3) + " m).");
    } else if (tip === "dismerkez-ters-V") {
      const L = Lk(D, C), e = +sec.e;
      if (!(e > 0 && e < L)) throw new ModelHatasi("dismerkez-ters-V: e (bağ kirişi boyu, m) 0 ile kiriş boyu " + fmt(L, 3) + " arasında olmalı.");
      const E1 = kenar(D, C, 0.5 - e / (2 * L)), E2 = kenar(D, C, 0.5 + e / (2 * L));
      ekle(A, E1); ekle(B, E2);
      bag = bagIsaretle(E1, E2);
    } else if (tip === "diz") {
      const a = +sec.a;
      if (!(a > 0)) throw new ModelHatasi("diz: a (köşeden uzaklık, m) pozitif olmalı.");
      if (sec.taraf !== "sag") {
        if (a >= Lk(D, A) || a >= Lk(D, C)) throw new ModelHatasi("diz: a köşeye bağlanan elemanlardan uzun.");
        const P1 = kenar(D, A, a / Lk(D, A)), P2 = kenar(D, C, a / Lk(D, C)); ekle(P1, P2);
      }
      if (sec.taraf !== "sol") {
        if (a >= Lk(C, B) || a >= Lk(C, D)) throw new ModelHatasi("diz: a köşeye bağlanan elemanlardan uzun.");
        const Q1 = kenar(C, B, a / Lk(C, B)), Q2 = kenar(C, D, a / Lk(C, D)); ekle(Q1, Q2);
      }
    }
    if (sec.yalniz_cekme) {
      this.uyar("Yalnız çekme çaprazı: TBDY 2018 9.6.4.3 uyarınca süneklik düzeyi yüksek (SDY) sistemlerde kullanılamaz; sınırlı süneklikte (SDS) KL/i ≤ 300 ile izinlidir.");
    }
    this.uretecBitir(kayit);
    return { uretec: kayit.no, caprazlar: eklenen, bag_kirisi: bag, kose: { A: A, B: B, C: C, D: D } };
  };
  P_.ciftVarMi = function (n) { return this.m.cubuklar.some(function (c) { const u = this.uclar(c); return u[0] === n || u[1] === n; }, this); };

  // ---------------------------------------------------------------- makas
  P_.makasIc = function (p, zorunluNo) {
    p = Object.assign({ goz: 6, yukari: [0, 0, 1], uc_yukseklik: 0, kesitler: {}, mafsalli_govde: true }, p || {});
    const tip = String(p.tip || "").toLowerCase();
    if (MAKAS_TIPLERI.indexOf(tip) < 0) throw new ModelHatasi("Makas tipi " + JSON.stringify(p.tip) + " tanımsız; seçenekler: " + MAKAS_TIPLERI.join(", ") + ".");
    if (p.bas == null || p.son == null) throw new ModelHatasi("makasUret: açıklığın iki mesnet noktası 'bas' ve 'son' (REF ya da [X,Y,Z]) verilmeli.");
    const self = this;
    const S = this.refNo(p.bas), E = this.refNo(p.son);
    const PS = this.kon(S), PE = this.kon(E), L = uzaklik(PS, PE);
    if (L <= this.tol) throw new ModelHatasi("makasUret: açıklık sıfır.");
    const u = birim(cikar(PE, PS)), up = nokta3(p.yukari, "yukari");
    const w = birim(cikar(up, olcek(u, ic(up, u))));
    if (boy(w) < 0.5) throw new ModelHatasi("makasUret: 'yukari' doğrultusu açıklık doğrultusuna paralel olamaz.");
    const besik = tip === "besik-pratt" || tip === "besik-howe" || tip === "fink";
    let h = null, hm = null;
    if (besik) {
      hm = p.yukseklik != null ? +p.yukseklik : (p.egim != null ? (L / 2) * Math.tan(+p.egim * D2R) : null);
      if (!(hm > 0)) throw new ModelHatasi("makasUret (" + tip + "): mahya yüksekliği 'yukseklik' ya da eğim 'egim' (derece) verilmeli.");
    } else {
      h = +p.yukseklik;
      if (!(h > 0)) throw new ModelHatasi("makasUret (" + tip + "): 'yukseklik' (m) pozitif olmalı.");
    }
    const n = Math.round(+p.goz);
    if (tip !== "fink") {
      if (!(n >= 2)) throw new ModelHatasi("makasUret: göz sayısı en az 2 olmalı.");
      if (["pratt", "howe", "k", "besik-pratt", "besik-howe"].indexOf(tip) >= 0 && n % 2) throw new ModelHatasi("makasUret (" + tip + "): göz sayısı çift olmalı (simetrik düzen).");
    }
    const kayit = this.uretecBasla("makas", Object.assign({}, p, { bas: this.refYaz(S), son: this.refYaz(E), tip: tip }), zorunluNo);
    const ks = p.kesitler || {};
    ["ust", "alt", "dikme", "diyagonal"].forEach(function (k) { self.kesitUyar(ks[k], "Makas " + k); });
    const sayac = { "makas-ust": 0, "makas-alt": 0, "makas-dikme": 0, "makas-diyagonal": 0 };
    const kes = { "makas-ust": ks.ust, "makas-alt": ks.alt, "makas-dikme": ks.dikme, "makas-diyagonal": ks.diyagonal };
    const ekle = function (tur, a, b) {
      if (a === b) return;
      const govde = tur === "makas-dikme" || tur === "makas-diyagonal";
      const no = self.ekCubukTekil(Object.assign({ tur: tur }, kesitOz(kes[tur]), mafsalOz(govde && p.mafsalli_govde !== false)), a, b);
      if (no != null) sayac[tur]++;
    };
    const nok = function (x, z) { return self.dugumEkle(topla(topla(PS, olcek(u, x)), olcek(w, z))); };
    const d = L / n;
    const Bn = [], Tn = [];
    if (tip !== "fink") for (let k = 0; k <= n; k++) Bn.push(k === 0 ? S : k === n ? E : nok(k * d, 0));
    const paralel = ["pratt", "howe", "warren-dikmeli", "k"].indexOf(tip) >= 0;
    if (paralel) for (let k = 0; k <= n; k++) Tn.push(nok(k * d, h));
    const altBaslik = function () { for (let k = 0; k < n; k++) ekle("makas-alt", Bn[k], Bn[k + 1]); };
    if (tip === "pratt" || tip === "howe" || tip === "warren-dikmeli") {
      altBaslik();
      for (let k = 0; k < n; k++) ekle("makas-ust", Tn[k], Tn[k + 1]);
      for (let k = 0; k <= n; k++) ekle("makas-dikme", Bn[k], Tn[k]);
      for (let k = 0; k < n; k++) {
        const sol = k < n / 2;
        if (tip === "pratt") { if (sol) ekle("makas-diyagonal", Bn[k + 1], Tn[k]); else ekle("makas-diyagonal", Bn[k], Tn[k + 1]); }
        else if (tip === "howe") { if (sol) ekle("makas-diyagonal", Bn[k], Tn[k + 1]); else ekle("makas-diyagonal", Bn[k + 1], Tn[k]); }
        else { if (k % 2 === 0) ekle("makas-diyagonal", Bn[k], Tn[k + 1]); else ekle("makas-diyagonal", Bn[k + 1], Tn[k]); }
      }
    } else if (tip === "warren") {
      altBaslik();
      const M = [];
      for (let k = 0; k < n; k++) M.push(nok((k + 0.5) * d, h));
      for (let k = 0; k < n - 1; k++) ekle("makas-ust", M[k], M[k + 1]);
      for (let k = 0; k < n; k++) { ekle("makas-diyagonal", Bn[k], M[k]); ekle("makas-diyagonal", Bn[k + 1], M[k]); }
    } else if (tip === "k") {
      altBaslik();
      for (let k = 0; k < n; k++) ekle("makas-ust", Tn[k], Tn[k + 1]);
      const M = [null];
      for (let k = 1; k < n; k++) M.push(nok(k * d, h / 2));
      ekle("makas-dikme", Bn[0], Tn[0]); ekle("makas-dikme", Bn[n], Tn[n]);
      for (let k = 1; k < n; k++) { ekle("makas-dikme", Bn[k], M[k]); ekle("makas-dikme", M[k], Tn[k]); }
      for (let k = 0; k < n; k++) {
        if (k < n / 2) { ekle("makas-diyagonal", Tn[k], M[k + 1]); ekle("makas-diyagonal", Bn[k], M[k + 1]); }
        else { ekle("makas-diyagonal", M[k], Tn[k + 1]); ekle("makas-diyagonal", M[k], Bn[k + 1]); }
      }
    } else if (tip === "besik-pratt" || tip === "besik-howe") {
      const h0 = +p.uc_yukseklik || 0;
      const H = [];
      for (let k = 0; k <= n; k++) H.push(h0 + (hm - h0) * (1 - Math.abs(2 * k / n - 1)));
      for (let k = 0; k <= n; k++) Tn.push(H[k] > this.tol ? nok(k * d, H[k]) : Bn[k]);
      altBaslik();
      for (let k = 0; k < n; k++) ekle("makas-ust", Tn[k], Tn[k + 1]);
      for (let k = 0; k <= n; k++) if (H[k] > this.tol) ekle("makas-dikme", Bn[k], Tn[k]);
      for (let k = 0; k < n; k++) {
        if (H[k] <= this.tol || H[k + 1] <= this.tol) continue;
        const sol = k < n / 2;
        if (tip === "besik-pratt") { if (sol) ekle("makas-diyagonal", Bn[k + 1], Tn[k]); else ekle("makas-diyagonal", Bn[k], Tn[k + 1]); }
        else { if (sol) ekle("makas-diyagonal", Bn[k], Tn[k + 1]); else ekle("makas-diyagonal", Bn[k + 1], Tn[k]); }
      }
    } else if (tip === "fink") {
      if (+p.uc_yukseklik) this.uyar("Fink makası üçgen (uç yüksekliği 0) üretilir; uc_yukseklik yok sayıldı.");
      const B1 = nok(L / 3, 0), B2 = nok(2 * L / 3, 0), R = nok(L / 2, hm), TL = nok(L / 4, hm / 2), TR = nok(3 * L / 4, hm / 2);
      ekle("makas-ust", S, TL); ekle("makas-ust", TL, R); ekle("makas-ust", R, TR); ekle("makas-ust", TR, E);
      ekle("makas-alt", S, B1); ekle("makas-alt", B1, B2); ekle("makas-alt", B2, E);
      ekle("makas-diyagonal", B1, TL); ekle("makas-diyagonal", B1, R); ekle("makas-diyagonal", B2, R); ekle("makas-diyagonal", B2, TR);
    }
    this.uretecBitir(kayit);
    return { uretec: kayit.no, sayilar: sayac, acilik: r9(L), mahya: hm != null ? r9(hm) : null };
  };

  // ---------------------------------------------------------------- aşık (ortak)
  /** cizgiler: [[başDüğüm, sonDüğüm], ...] (saçak → mahya, yan yana sıralı); her çizgi boyunca eşit aralıklı aşık noktaları. */
  P_.asikCizgileri = function (cizgiler, aralik, kesit, sec, kayit) {
    sec = sec || {};
    const self = this;
    if (!(+aralik > 0)) throw new ModelHatasi("Aşık aralığı pozitif olmalı (m).");
    if (cizgiler.length < 2) throw new ModelHatasi("Aşık için en az iki mertek (ya da panelin iki eğik kenarı) gerekir.");
    const Lmax = Math.max.apply(null, cizgiler.map(function (c) { return uzaklik(self.kon(c[0]), self.kon(c[1])); }));
    const m = Math.max(1, Math.ceil(Lmax / +aralik - 1e-9));
    const uclar = sec.uclar !== false;
    const ks = [];
    for (let k = uclar ? 0 : 1; k <= (uclar ? m : m - 1); k++) ks.push(k);
    const noktalar = cizgiler.map(function (c) {
      const A = self.kon(c[0]), B = self.kon(c[1]);
      return ks.map(function (k) { return k === 0 ? c[0] : k === m ? c[1] : self.noktadaBol(ara(A, B, k / m), kayit).no; });
    });
    const asiklar = [];
    for (let l = 0; l < cizgiler.length - 1; l++) {
      const A0 = this.kon(cizgiler[l][0]), A1 = this.kon(cizgiler[l][1]), B0 = this.kon(cizgiler[l + 1][0]);
      // çatı normali: mertek doğrultusu × aşık doğrultusu; yukarı bakacak (ya da verilen 'normal' tarafına) çevrilir
      let nrm = birim(dis(cikar(A1, A0), cikar(B0, A0)));
      if (sec.normal) { if (ic(nrm, nokta3(sec.normal, "normal")) < 0) nrm = olcek(nrm, -1); }
      else if (nrm[2] < 0) nrm = olcek(nrm, -1);
      for (let k = 0; k < ks.length; k++) {
        const a = noktalar[l][k], b = noktalar[l + 1][k];
        if (a === b) continue;
        const aci = aciHedef(this.kon(a), this.kon(b), nrm, false);
        const no = this.ekCubukTekil(Object.assign({ tur: sec.tur || "asik" }, kesitOz(kesit), { aci: aci }, mafsalOz(sec.mafsalli !== false)), a, b);
        if (no != null) asiklar.push(no);
      }
    }
    return { asiklar: [...new Set(asiklar)], aralik_gercek: r9(Lmax / m), bolum: m };
  };
  /** Seçili çubukları eş doğrusal zincirlere ayırır; her zincir [alt uç, üst uç] düğüm çifti (Z küçük olan baş). */
  P_.cizgilereAyir = function (nolar) {
    const self = this, cz = [];
    for (const z of this.zincirler(nolar)) {
      if (z.hata) throw new ModelHatasi("Mertek seçimi (" + z.cubuklar.join(", ") + ") zincir değil: " + z.hata + ".");
      let a = z.dugumler[0], b = z.dugumler[z.dugumler.length - 1];
      for (const n of z.dugumler.slice(1, -1)) if (dogruyaUzaklik(this.kon(n), this.kon(a), this.kon(b)).d > this.tol) throw new ModelHatasi("Mertek zinciri " + z.cubuklar.join(", ") + " düz değil.");
      if (this.kon(a)[2] > this.kon(b)[2] + 1e-9) { const t = a; a = b; b = t; }
      cz.push([a, b]);
    }
    if (cz.length < 2) return cz;
    const bas = cz.map(function (c) { return self.kon(c[0]); });
    const u = birim(cikar(self.kon(cz[0][1]), bas[0]));
    let yon = null, en = -1;
    for (const p of bas) { const v = cikar(p, bas[0]), dik = cikar(v, olcek(u, ic(v, u))); if (boy(dik) > en) { en = boy(dik); yon = birim(dik); } }
    // sıralama (ve aşık i→j) yönü pozitif eksen yönüne çevrilir: belirlenimli aci işareti
    const bk = [0, 1, 2].find(function (i) { return Math.abs(yon[i]) > 1e-9; });
    if (bk != null && yon[bk] < 0) yon = olcek(yon, -1);
    return cz.map(function (c, i) { return [c, ic(cikar(bas[i], bas[0]), yon)]; }).sort(function (a, b) { return a[1] - b[1]; }).map(function (x) { return x[0]; });
  };
  P_.asikIc = function (hedef, aralik, kesit, sec, zorunluNo) {
    sec = sec || {};
    let cizgiler, normal = null;
    if (Array.isArray(hedef) || (hedef && Array.isArray(hedef.mertekler))) {
      cizgiler = this.cizgilereAyir(Array.isArray(hedef) ? hedef : hedef.mertekler);
    } else if (hedef && hedef.panel != null) {
      const self = this, p = this.panel(hedef.panel);
      const k = p.kose.map(function (r) { return self.refNo(r, false); });
      if (k.length !== 4) throw new ModelHatasi("Aşık üretimi için panel dört köşeli olmalı.");
      const P = k.map(function (n) { return self.kon(n); });
      const dz = function (a, b) { return Math.abs(P[a][2] - P[b][2]); };
      let e1 = [0, 3], e2 = [1, 2];
      if (dz(0, 1) + dz(2, 3) > dz(0, 3) + dz(1, 2) + 1e-9) { e1 = [0, 1]; e2 = [3, 2]; }
      const yon = function (e) { return P[e[0]][2] <= P[e[1]][2] + 1e-9 ? [k[e[0]], k[e[1]]] : [k[e[1]], k[e[0]]]; };
      cizgiler = [yon(e1), yon(e2)];
      normal = birim(newell(P));
      if (normal[2] < 0) normal = olcek(normal, -1);
    } else throw new ModelHatasi('asikUret: hedef mertek çubuk numaraları dizisi ya da {"panel": no} olmalı.');
    const kayit = this.uretecBasla("asik", { hedef: kopya(hedef), aralik: +aralik, kesit: kesit, secenek: sec }, zorunluNo);
    this.kesitUyar(kesit, "Aşık");
    const r = this.asikCizgileri(cizgiler, aralik, kesit, Object.assign({}, sec, normal ? { normal: normal } : {}), kayit);
    this.uretecBitir(kayit);
    return Object.assign({ uretec: kayit.no }, r);
  };

  // ---------------------------------------------------------------- beşik çerçeve
  P_.besikIc = function (p, zorunluNo) {
    p = Object.assign({ adet: 1, aralik: 6, mesnet: "mafsal", kesitler: {} }, p || {});
    const self = this;
    if (p.taban1 == null || p.taban2 == null) throw new ModelHatasi("besikCerceveUret: iki kolon tabanı 'taban1' ve 'taban2' (REF ya da [X,Y,Z]) verilmeli.");
    const b1 = this.refNo(p.taban1), b2 = this.refNo(p.taban2);
    const P1 = this.kon(b1), P2 = this.kon(b2);
    const yatay = [P2[0] - P1[0], P2[1] - P1[1], 0], L = boy(yatay);
    if (L <= this.tol) throw new ModelHatasi("besikCerceveUret: açıklık sıfır.");
    if (Math.abs(P1[2] - P2[2]) > this.tol) this.uyar("Kolon tabanları farklı kotta; saçaklar kendi tabanlarından, mahya ortalama taban kotundan ölçüldü.");
    const u = birim(yatay);
    const sacak = +p.sacak;
    if (!(sacak > 0)) throw new ModelHatasi("besikCerceveUret: 'sacak' (saçak yüksekliği, m) pozitif olmalı.");
    let mahya = p.mahya != null ? +p.mahya : (p.egim != null ? sacak + (L / 2) * Math.tan(+p.egim * D2R) : null);
    if (!(mahya > sacak)) throw new ModelHatasi("besikCerceveUret: mahya yüksekliği ('mahya', m) saçaktan büyük olmalı ya da pozitif eğim ('egim', derece) verilmeli.");
    const adet = Math.max(1, Math.round(+p.adet || 1)), aralik = +p.aralik || 0;
    if (adet > 1 && !(aralik > 0)) throw new ModelHatasi("besikCerceveUret: birden çok çerçeve için 'aralik' (m) pozitif olmalı.");
    const v = p.yon ? birim(nokta3(p.yon, "yon")) : birim([-u[1], u[0], 0]);
    const ks = p.kesitler || {};
    const kayit = this.uretecBasla("besik-cerceve", Object.assign({}, p, { taban1: this.refYaz(b1), taban2: this.refYaz(b2), mahya: r9(mahya) }), zorunluNo);
    this.kesitUyar(ks.kolon, "Kolon"); this.kesitUyar(ks.mertek, "Mertek");
    let vuteKesit = null;
    const vute = p.vute && +p.vute.boy > 0 ? p.vute : null;
    if (vute) {
      vuteKesit = ks.vute || vute.kesit || ("VUTE-" + (ks.mertek || "mertek"));
      if (!this.m.kesitler || typeof this.m.kesitler !== "object") this.m.kesitler = {};
      if (!this.m.kesitler[vuteKesit]) {
        this.m.kesitler[vuteKesit] = { tip: "vute", temel: ks.mertek || null, ek_yukseklik: +vute.yukseklik || 0, boy: +vute.boy };
        this.uyar("Vute kesiti '" + vuteKesit + "' {tip: \"vute\", temel, ek_yukseklik} olarak eklendi; motor bu kesit tipini tanımıyorsa eşdeğer (daha yüksek) bir profil atayın.");
      }
    }
    const zt = (P1[2] + P2[2]) / 2, orta = olcek(topla(P1, P2), 0.5);
    const cerceveler = [];
    const rijit = String(p.mesnet).toLowerCase() === "ankastre";
    for (let f = 0; f < adet; f++) {
      const off = olcek(v, f * aralik);
      const t1 = f === 0 ? b1 : this.dugumEkle(topla(P1, off)), t2 = f === 0 ? b2 : this.dugumEkle(topla(P2, off));
      const e1 = this.dugumEkle(topla(topla(P1, off), [0, 0, sacak])), e2 = this.dugumEkle(topla(topla(P2, off), [0, 0, sacak]));
      const R = [orta[0] + off[0], orta[1] + off[1], zt + mahya];
      const r = this.dugumEkle(R, f === 0 ? "Mahya" : null);
      const kolonlar = [t1, t2].map(function (t, i) {
        const ust = i ? e2 : e1;
        return self.ekCubukTekil(Object.assign({ tur: "kolon" }, kesitOz(ks.kolon), { aci: aciHedef(self.kon(t), self.kon(ust), u, true) }), t, ust);
      });
      const mertek = function (e) {
        const zin = [];
        if (vute) {
          const Ls = uzaklik(self.kon(e), self.kon(r));
          if (+vute.boy >= Ls) throw new ModelHatasi("besikCerceveUret: vute boyu mertek boyundan küçük olmalı.");
          const V = self.dugumEkle(ara(self.kon(e), self.kon(r), +vute.boy / Ls));
          zin.push(self.ekCubukTekil(Object.assign({ tur: "kiris", kesit: vuteKesit, grup: "VUTE" }), e, V));
          zin.push(self.ekCubukTekil(Object.assign({ tur: "kiris" }, kesitOz(ks.mertek), { grup: "MERTEK" }), V, r));
        } else zin.push(self.ekCubukTekil(Object.assign({ tur: "kiris" }, kesitOz(ks.mertek), { grup: "MERTEK" }), e, r));
        return zin;
      };
      const sol = mertek(e1), sag = mertek(e2);
      if (p.mesnet && String(p.mesnet).toLowerCase() !== "yok") {
        for (const t of [t1, t2]) {
          if (this.mesnetli(t)) continue;
          this.m.mesnetler.push({ dugum: this.refYaz(t), ux: true, uy: true, uz: true, rx: rijit, ry: rijit, rz: rijit, kaynak: { uretec: kayit.no } });
        }
      }
      cerceveler.push({ taban: [t1, t2], sacak: [e1, e2], mahya: r, kolonlar: kolonlar, mertekler: [sol, sag] });
    }
    let asiklar = [];
    if (p.asik) {
      if (adet < 2) this.uyar("Aşık için en az iki çerçeve gerekir (adet ≥ 2); aşık üretilmedi.");
      else {
        for (const yan of [0, 1]) {
          const cz = cerceveler.map(function (c) { return [c.sacak[yan], c.mahya]; });
          asiklar = asiklar.concat(this.asikCizgileri(cz, +p.asik.aralik, p.asik.kesit, p.asik, kayit).asiklar);
        }
        this.kesitUyar(p.asik.kesit, "Aşık");
      }
    }
    const paneller = [];
    if (p.panel) {
      if (adet < 2) this.uyar("Çatı paneli için en az iki çerçeve gerekir; panel üretilmedi.");
      else {
        for (let f = 0; f < adet - 1; f++) {
          for (const yan of [0, 1]) {
            const a = cerceveler[f], b = cerceveler[f + 1];
            let kose = [a.sacak[yan], b.sacak[yan], b.mahya, a.mahya];
            if (newell(kose.map(function (n) { return self.kon(n); }))[2] < 0) kose = kose.reverse();
            const oz = Object.assign({ tur: "cati", kalinlik: 0, dagitim: "tek-24" }, p.panel === true ? {} : kopya(p.panel));
            const pr = Object.assign({ no: this.yeniNo(this.m.paneller, this.m.dosemeler), kose: kose.map(function (n) { return self.refYaz(n); }) }, oz, { kaynak: { uretec: kayit.no } });
            this.m.paneller.push(pr);
            paneller.push(pr.no);
          }
        }
        if (!p.asik) this.uyar("Çatı panellerinin saçak ve mahya kenarlarında çubuk yok; aşık (asik) seçeneğini açın ya da kenar çubuklarını çizin.");
      }
    }
    this.uretecBitir(kayit);
    return { uretec: kayit.no, cerceveler: cerceveler, asiklar: asiklar, paneller: paneller, mahya_kotu: r9(zt + mahya),
      egim: r9(Math.atan2(mahya - sacak, L / 2) / D2R) };
  };

  // ---------------------------------------------------------------- kren yolu
  P_.kolonNoktasi = function (cno, kot, kayit) {
    const c = this.cubuk(cno), u = this.uclar(c), A = this.kon(u[0]), B = this.kon(u[1]);
    if (Math.abs(B[2] - A[2]) < 1e-9) throw new ModelHatasi("Çubuk " + cno + " yatay; kot ile kesişmiyor.");
    const t = (kot - A[2]) / (B[2] - A[2]);
    if (t < -1e-9 || t > 1 + 1e-9) throw new ModelHatasi("Kot " + kot + " çubuk " + cno + " boyunca değil (Z " + fmt(Math.min(A[2], B[2]), 3) + "…" + fmt(Math.max(A[2], B[2]), 3) + ").");
    return this.noktadaBol(ara(A, B, t), kayit).no;
  };
  function cizgiSirasi(P) {
    if (P.length < 2) return { sira: P.map(function (_, i) { return i; }), yon: [1, 0, 0] };
    let a = 0, b = 1, en = -1;
    for (let i = 0; i < P.length; i++) for (let j = i + 1; j < P.length; j++) { const d = uzaklik(P[i], P[j]); if (d > en) { en = d; a = i; b = j; } }
    let yon = birim(cikar(P[b], P[a]));
    if (yon[0] < -1e-9 || (Math.abs(yon[0]) <= 1e-9 && yon[1] < 0)) yon = olcek(yon, -1);
    const sira = P.map(function (_, i) { return i; }).sort(function (i, j) { return ic(P[i], yon) - ic(P[j], yon); });
    return { sira: sira, yon: yon };
  }
  P_.krenIc = function (kolonlar, kot, konsolBoy, kesitler, kren, zorunluNo) {
    kren = kren || {}; kesitler = kesitler || {};
    if (!Array.isArray(kolonlar) || !kolonlar.length) throw new ModelHatasi("krenYoluUret: kolon çubuk numaraları verilmeli.");
    const hatlar = Array.isArray(kolonlar[0]) ? kolonlar : [kolonlar];
    if (hatlar.some(function (h) { return h.length < 2; })) throw new ModelHatasi("krenYoluUret: her kren hattında en az iki kolon olmalı.");
    if (!isFinite(+kot)) throw new ModelHatasi("krenYoluUret: kot (m) sayı olmalı.");
    const self = this, kb = +konsolBoy || 0;
    const kayit = this.uretecBasla("kren-yolu", { kolonlar: kopya(kolonlar), kot: +kot, konsol_boy: kb, kesitler: kopya(kesitler), kren: kopya(kren) }, zorunluNo);
    this.kesitUyar(kesitler.kiris, "Kren kirişi");
    if (kb > 0) this.kesitUyar(kesitler.konsol, "Konsol");
    const hatDugum = hatlar.map(function (h) { return h.map(function (c) { return self.kolonNoktasi(+c, +kot, kayit); }); });
    const merkez = hatDugum.map(function (l) { return olcek(l.map(function (n) { return self.kon(n); }).reduce(topla, [0, 0, 0]), 1 / l.length); });
    const sonuc = { uretec: kayit.no, konsollar: [], kirisler: [], kren: [] };
    hatDugum.forEach(function (l, hi) {
      const P = l.map(function (n) { return self.kon(n); });
      const cs = cizgiSirasi(P), yon = cs.yon;
      let kd = null;
      if (kren.konsol_yon) { const k = nokta3(kren.konsol_yon.length === 2 ? kren.konsol_yon.concat([0]) : kren.konsol_yon, "konsol_yon"); kd = birim([k[0], k[1], 0]); }
      else if (hatlar.length === 2) {
        const v = cikar(merkez[1 - hi], merkez[hi]), dik = cikar(v, olcek(yon, ic(v, yon)));
        kd = birim([dik[0], dik[1], 0]);
      } else {
        kd = birim(dis([0, 0, 1], yon));
        if (kb > 0) self.uyar("Konsol yönü verilmedi (kren.konsol_yon); hat doğrultusuna dik +yön alındı: [" + kd.map(function (x) { return fmt(x, 3); }).join(", ") + "].");
      }
      const uc = cs.sira.map(function (i) {
        if (!(kb > 0)) return l[i];
        const K = self.dugumEkle(topla(P[i], olcek(kd, kb)));
        const no = self.ekCubukTekil(Object.assign({ tur: "kiris" }, kesitOz(kesitler.konsol), { grup: "KREN-KONSOL" }), l[i], K);
        if (no != null) sonuc.konsollar.push(no);
        return K;
      });
      const yol = [];
      for (let k = 0; k < uc.length - 1; k++) {
        const no = self.ekCubukTekil(Object.assign({ tur: "kren" }, kesitOz(kesitler.kiris), mafsalOz(kren.basit !== false)), uc[k], uc[k + 1]);
        if (no != null) { yol.push(no); sonuc.kirisler.push(no); }
      }
      const kr = { no: self.yeniNo(self.m.kren), yol: yol };
      if (kren.tekerlek) kr.tekerlek = kopya(kren.tekerlek);
      else self.uyar("Kren tekerlek yükleri (kren.tekerlek: P_maks, P_min, H_yanal, H_fren, aralik, adet) verilmedi.");
      kr.dinamik = kren.dinamik != null ? +kren.dinamik : 1.25;
      kr.konum_sayisi = kren.konum_sayisi != null ? +kren.konum_sayisi : 9;
      kr.kaynak = { uretec: kayit.no };
      self.m.kren.push(kr);
      sonuc.kren.push(kr.no);
    });
    this.uretecBitir(kayit);
    return sonuc;
  };

  // ---------------------------------------------------------------- cephe kuşakları
  P_.cepheIc = function (p, zorunluNo) {
    p = Object.assign({ mafsalli: true }, p || {});
    if (!Array.isArray(p.kolonlar) || p.kolonlar.length < 2) throw new ModelHatasi("cepheKirisleriUret: en az iki kolon (çubuk no) verilmeli.");
    const self = this;
    const kol = p.kolonlar.map(function (c) { const u = self.uclar(self.cubuk(c)); return { no: +c, A: self.kon(u[0]), B: self.kon(u[1]) }; });
    let kotlar = Array.isArray(p.kotlar) ? p.kotlar.map(Number) : null;
    if (!kotlar) {
      const ar = +p.aralik;
      if (!(ar > 0)) throw new ModelHatasi("cepheKirisleriUret: 'kotlar' listesi ya da 'aralik' (m) verilmeli.");
      const alt = Math.max.apply(null, kol.map(function (k) { return Math.min(k.A[2], k.B[2]); }));
      const ust = Math.min.apply(null, kol.map(function (k) { return Math.max(k.A[2], k.B[2]); }));
      kotlar = [];
      for (let z = alt + ar; z < ust - this.tol; z += ar) kotlar.push(r6(z));
    }
    const kayit = this.uretecBasla("cephe-kirisi", Object.assign({}, p, { kotlar: kotlar }), zorunluNo);
    this.kesitUyar(p.kesit, "Cephe kuşağı");
    const taban = kol.map(function (k) { return k.A[2] < k.B[2] ? k.A : k.B; });
    const cs = cizgiSirasi(taban), yon = cs.yon;
    let nrm = birim(dis(yon, [0, 0, 1]));
    if (p.normal) { const sn = nokta3(p.normal, "normal"); if (ic(nrm, sn) < 0) nrm = olcek(nrm, -1); }
    const kusaklar = [];
    for (const z of kotlar) {
      const dg = [];
      for (const i of cs.sira) {
        const k = kol[i];
        if (z <= Math.min(k.A[2], k.B[2]) + this.tol || z >= Math.max(k.A[2], k.B[2]) - this.tol) { this.uyar("Kot " + z + " kolon " + k.no + " boyunca değil; atlandı."); dg.push(null); continue; }
        // kolon önceki kotlarda bölünmüş olabilir: nokta özgün kolon doğrusundan hesaplanır
        dg.push(this.noktadaBol(ara(k.A, k.B, (z - k.A[2]) / (k.B[2] - k.A[2])), kayit).no);
      }
      for (let k = 0; k < dg.length - 1; k++) {
        if (dg[k] == null || dg[k + 1] == null) continue;
        const no = this.ekCubukTekil(Object.assign({ tur: p.tur || "asik" }, kesitOz(p.kesit), { aci: aciHedef(this.kon(dg[k]), this.kon(dg[k + 1]), nrm, false), grup: "CEPHE-KUSAGI" }, mafsalOz(p.mafsalli !== false)), dg[k], dg[k + 1]);
        if (no != null) kusaklar.push(no);
      }
    }
    this.uretecBitir(kayit);
    return { uretec: kayit.no, kusaklar: kusaklar, kotlar: kotlar };
  };

  // ================================================================= kesişim geometrisi
  function parcaKesisim(P1, P2, Q1, Q2, tol) {
    const d1 = cikar(P2, P1), d2 = cikar(Q2, Q1), r = cikar(P1, Q1);
    const a = ic(d1, d1), e = ic(d2, d2), b = ic(d1, d2), c = ic(d1, r), f = ic(d2, r);
    const den = a * e - b * b;
    const L1 = Math.sqrt(a), L2 = Math.sqrt(e);
    if (den <= 1e-12 * a * e) {
      const dq = dogruyaUzaklik(Q1, P1, P2).d;
      if (dq > tol) return { paralel: true, esDogrusal: false };
      const t1 = dogruyaUzaklik(Q1, P1, P2).t, t2 = dogruyaUzaklik(Q2, P1, P2).t;
      const lo = Math.max(0, Math.min(t1, t2)), hi = Math.min(1, Math.max(t1, t2));
      return { paralel: true, esDogrusal: true, ortusme: (hi - lo) * L1 > tol };
    }
    const s = (b * f - c * e) / den, t = (a * f - b * c) / den;
    const Ps = ara(P1, P2, s), Qt = ara(Q1, Q2, t);
    if (uzaklik(Ps, Qt) > tol) return null;
    if (s < -tol / L1 || s > 1 + tol / L1 || t < -tol / L2 || t > 1 + tol / L2) return null;
    return { paralel: false, P: olcek(topla(Ps, Qt), 0.5), s: s, t: t, L1: L1, L2: L2 };
  }

  // ================================================================= DIŞA AÇIK İŞLEVLER
  // ---- okuma
  function dugumKonumu(model, ref) {
    const is = new Is(model);
    if (koordinatRef(ref)) return Array.isArray(ref) ? nokta3(ref) : nokta3([ref.X, ref.Y, ref.Z]);
    try { return is.kon(is.refNo(ref, false)); } catch (e) { return null; }
  }
  function dugumBul(model, X, Y, Z, tol) {
    const is = new Is(model);
    return is.bul(nokta3([X, Y, Z]), tol == null ? TOL : +tol);
  }
  function dugumNo(model, ref) { const is = new Is(model); return is.refNo(ref, false); }
  function uzunluk(model, cubukNo) { const is = new Is(model); return is.cubukUzunluk(is.cubuk(cubukNo)); }
  /** Eğim (derece): yataydan, j ucu i'den yüksekse pozitif. */
  function egim(model, cubukNo) {
    const is = new Is(model), c = is.cubuk(cubukNo), u = is.uclar(c), A = is.kon(u[0]), B = is.kon(u[1]);
    return Math.atan2(B[2] - A[2], Math.hypot(B[0] - A[0], B[1] - A[1])) / D2R;
  }
  function yerelEksenler(model, cubukNo) { const is = new Is(model); return is.cubukEksen(is.cubuk(cubukNo)); }
  function panelKenarCubuklari(model, panel, sec) {
    const is = new Is(model, sec);
    const p = typeof panel === "object" && panel ? panel : is.panel(panel);
    return is.panelKenarlari(p);
  }
  function panelGeometrisi(model, panel, sec) {
    const is = new Is(model, sec);
    const p = typeof panel === "object" && panel ? panel : is.panel(panel);
    return panelGeometri(p.kose.map(function (r) { return is.kon(is.refNo(r, false)); }), (sec && sec.tol_duzlem) || 0.005);
  }

  // ---- genelleştir
  function genellestir(model) {
    const is = new Is(model);
    is.genellestirIc();
    is.m.surum = 3;
    return is.bitir();
  }

  // ---- düğüm
  function dugumEkle(model, X, Y, Z, ad) {
    const is = new Is(model);
    const P = nokta3([X, Y, Z]);
    const var_ = is.bul(P);
    if (var_ != null) is.uyar("Bu konumda (1 mm içinde) düğüm " + var_ + " var; yeni düğüm eklenmedi.");
    const no = is.dugumEkle(P, ad);
    return is.bitir({ no: no });
  }
  function dugumTasi(model, no, X, Y, Z) {
    const is = new Is(model);
    const n = is.refNo(no, false);
    if (n == null) throw new ModelHatasi("Taşınacak düğüm bulunamadı: " + JSON.stringify(no));
    const P = nokta3([X, Y, Z]);
    if (is.harita().get(n).izgara && is.aksKatVar()) is.genellestirIc();
    const yeni = is.dugumuTasiIc(n, P);
    const o = is.bul(P, is.tol, new Set([yeni]));
    if (o != null) is.uyar("Düğüm " + yeni + " yeni konumunda düğüm " + o + " ile çakışıyor; dugumleriBirlestir ile birleştirin.");
    for (const c of is.m.cubuklar) { const u = is.uclar(c); if ((u[0] === yeni || u[1] === yeni) && is.cubukUzunluk(c) <= is.tol) is.uyar("Çubuk " + c.no + " sıfır boylu oldu."); }
    return is.bitir({ no: yeni });
  }
  function dugumSil(model, nolar) {
    const is = new Is(model);
    const sil = new Set((Array.isArray(nolar) ? nolar : [nolar]).map(function (r) { return is.refNo(r, false); }));
    const etkilenen = [];
    for (const c of is.m.cubuklar.slice()) { const u = is.uclar(c); if (sil.has(u[0]) || sil.has(u[1])) etkilenen.push.apply(etkilenen, is.cubukSilIc(+c.no)); }
    const silP = new Set(is.m.paneller.filter(function (p) { return p.kose.some(function (r) { return sil.has(is.refNo(r, false)); }); }).map(function (p) { return +p.no; }));
    is.m.paneller = is.m.paneller.filter(function (p) { return !silP.has(+p.no); });
    is.m.ek_yukler = is.m.ek_yukler.filter(function (y) { return !(y && ((y.tur === "panel" && silP.has(+y.panel)) || (y.tur === "dugum" && sil.has(is.yukDugumu(y))))); });
    is.m.mesnetler = is.m.mesnetler.filter(function (s) { try { return !sil.has(is.refNo(s.dugum, false)); } catch (e) { return true; } });
    for (const n of sil) {
      if (is.harita().get(n) && is.harita().get(n).izgara && is.aksKatDugumleri().has(n)) is.uyar("Düğüm " + n + " aks–kat elemanlarınca kullanılıyor; yalnız serbest elemanları silindi.");
      const i = is.m.dugumler.findIndex(function (d) { return +d.no === n; });
      if (i >= 0 && !is.aksKatDugumleri().has(n)) is.m.dugumler.splice(i, 1);
    }
    is._h = null;
    is.yetimSil(etkilenen.filter(function (n) { return !sil.has(n); }));
    return is.bitir();
  }
  function dugumleriBirlestir(model, tol) {
    const is = new Is(model);
    const t = tol == null ? TOL : +tol;
    const kayitlar = is.m.dugumler.filter(function (d) { return d && d.no != null; }).map(function (d) { return +d.no; });
    const ata = new Map(kayitlar.map(function (n) { return [n, n]; }));
    const kok = function (n) { while (ata.get(n) !== n) { ata.set(n, ata.get(ata.get(n))); n = ata.get(n); } return n; };
    const h = is.harita();
    const hucre = new Map(), boyut = Math.max(t, 1e-9);
    const anahtar = function (P) { return P.map(function (v) { return Math.floor(v / boyut); }); };
    for (const n of kayitlar) {
      const d = h.get(n), k = anahtar([d.X, d.Y, d.Z]);
      for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (let c = -1; c <= 1; c++) {
        for (const o of hucre.get((k[0] + a) + "," + (k[1] + b) + "," + (k[2] + c)) || []) {
          const e = h.get(o);
          if (Math.hypot(d.X - e.X, d.Y - e.Y, d.Z - e.Z) <= t) { const r1 = kok(n), r2 = kok(o); if (r1 !== r2) ata.set(r1, r2); }
        }
      }
      const kk = k.join(",");
      if (!hucre.has(kk)) hucre.set(kk, []);
      hucre.get(kk).push(n);
    }
    // ızgara düğümleriyle eşleşme (kayıtsız aks–kat düğümleri temsilci olur)
    const izg = new Map();
    for (const n of kayitlar) {
      const d = h.get(n);
      if (d.izgara) { izg.set(kok(n), n); continue; }
      let g = null, gd = t;
      for (const e of h.values()) { if (!e.izgara || e.kayit) continue; const dd = Math.hypot(d.X - e.X, d.Y - e.Y, d.Z - e.Z); if (dd <= gd) { gd = dd; g = e.no; } }
      if (g != null && !izg.has(kok(n))) izg.set(kok(n), g);
    }
    const gruplar = new Map();
    for (const n of kayitlar) { const r = kok(n); if (!gruplar.has(r)) gruplar.set(r, []); gruplar.get(r).push(n); }
    const esle = new Map(), birlesen = [];
    for (const [r, l] of gruplar) {
      const temsil = izg.has(r) ? izg.get(r) : Math.min.apply(null, l);
      if (l.length < 2 && temsil === l[0]) continue;
      for (const n of l) if (n !== temsil) { esle.set(n, temsil); birlesen.push([n, temsil]); }
    }
    if (esle.size) {
      is.refDegistir(esle);
      is.m.dugumler = is.m.dugumler.filter(function (d) { return !esle.has(+d.no); });
      is._h = null;
      // sıfır boylu çubuklar
      for (const c of is.m.cubuklar.slice()) { const u = is.uclar(c); if (u[0] === u[1]) { is.cubukSilIc(+c.no); is.uyar("Çubuk " + c.no + " birleştirme sonrası sıfır boylu kaldı; silindi."); } }
      // paneller
      for (const p of is.m.paneller.slice()) {
        const k = p.kose.map(function (r) { return is.refNo(r, false); });
        const tekil = k.filter(function (n, i) { return n !== k[(i + 1) % k.length]; });
        if (tekil.length < 3) { is.m.paneller.splice(is.m.paneller.indexOf(p), 1); is.uyar("Panel " + p.no + " köşeleri birleşti (< 3 köşe); silindi."); }
        else if (tekil.length < k.length) p.kose = tekil.map(function (n) { return is.refYaz(n); });
      }
      // mesnetler: aynı düğümde birden çok kayıt → birleşik (VEYA)
      const ms = new Map();
      for (const s of is.m.mesnetler) {
        const n = is.refNo(s.dugum, false);
        if (!ms.has(n)) { ms.set(n, s); continue; }
        const a = ms.get(n);
        for (const k of ["ux", "uy", "uz", "rx", "ry", "rz"]) a[k] = !!(a[k] || s[k]);
      }
      is.m.mesnetler = [...ms.values()];
      const ciftler = new Map();
      for (const c of is.m.cubuklar) {
        const u = is.uclar(c).slice().sort(function (a, b) { return a - b; }).join("-");
        if (ciftler.has(u)) is.uyar("Çubuk " + ciftler.get(u) + " ve " + c.no + " aynı iki düğümü bağlıyor (çakışan çubuk).");
        else ciftler.set(u, c.no);
      }
    }
    return is.bitir({ birlesen: birlesen });
  }

  // ---- çubuk
  function cubukCiz(model, refI, refJ, ozellik) {
    const is = new Is(model);
    const a = is.refNo(refI), b = is.refNo(refJ);
    if (a === b) { is.uyar("Çubuğun iki ucu aynı düğüm (sıfır boy); çizilmedi."); return reddet(model, is.uy); }
    const v = is.ciftBul(a, b);
    if (v != null) { is.uyar("Bu iki düğüm arasında çubuk " + v + " zaten var; çizilmedi."); return reddet(model, is.uy); }
    const oz = Object.assign({}, ozellik || {});
    delete oz.no; delete oz.i; delete oz.j;
    if (oz.tur == null) oz.tur = "diger";
    const no = is.ekCubuk(oz, a, b);
    return is.bitir({ no: no });
  }
  function cubukZinciri(model, refler, ozellik) {
    const is = new Is(model);
    if (!Array.isArray(refler) || refler.length < 2) throw new ModelHatasi("Çubuk zinciri için en az iki nokta gerekir.");
    const dg = refler.map(function (r) { return is.refNo(r); });
    const oz = Object.assign({ tur: "diger" }, ozellik || {});
    delete oz.no; delete oz.i; delete oz.j;
    const nolar = [];
    for (let k = 0; k < dg.length - 1; k++) {
      if (dg[k] === dg[k + 1]) { is.uyar("Ardışık iki nokta aynı düğüm; atlandı."); continue; }
      const v = is.ciftBul(dg[k], dg[k + 1]);
      if (v != null) { is.uyar("Düğüm " + dg[k] + "–" + dg[k + 1] + " arasında çubuk " + v + " zaten var; atlandı."); continue; }
      nolar.push(is.ekCubuk(kopya(oz), dg[k], dg[k + 1]));
    }
    return is.bitir({ nolar: nolar });
  }
  function cubukSil(model, nolar, sec) {
    const is = new Is(model);
    const ad = [];
    for (const no of Array.isArray(nolar) ? nolar : [nolar]) ad.push.apply(ad, is.cubukSilIc(+no));
    if (!sec || sec.dugumleriTemizle !== false) is.yetimSil(ad);
    return is.bitir();
  }
  function panelSil(model, nolar) {
    const is = new Is(model);
    const sil = new Set((Array.isArray(nolar) ? nolar : [nolar]).map(Number));
    sil.forEach(function (n) { is.panel(n); });
    const ad = [];
    is.m.paneller = is.m.paneller.filter(function (p) { if (sil.has(+p.no)) { p.kose.forEach(function (r) { ad.push(is.refNo(r, false)); }); return false; } return true; });
    is.m.ek_yukler = is.m.ek_yukler.filter(function (y) { return !(y && y.tur === "panel" && sil.has(+y.panel)); });
    is.yetimSil(ad);
    return is.bitir();
  }
  const OZELLIK_ADLARI = ["kesit", "tur", "aci", "yalniz_cekme", "grup", "Lb", "K", "kat", "duvar", "duvar_h"];
  /** Kesit/tür/açı/yalnız-çekme/grup/Lb/K/kat/duvar (duvarlar sözlüğündeki ad)/duvar_h (m; boş = kat yüksekliği) fırçası; null değer alanı kaldırır. */
  function ozellikAta(model, nolar, ozellik) {
    const is = new Is(model);
    for (const no of Array.isArray(nolar) ? nolar : [nolar]) {
      const c = is.cubuk(no);
      for (const k of Object.keys(ozellik || {})) {
        if (OZELLIK_ADLARI.indexOf(k) < 0) throw new ModelHatasi("ozellikAta: '" + k + "' atanamaz; izinli: " + OZELLIK_ADLARI.join(", ") + " (uç serbestliği için serbestlikAta).");
        if (ozellik[k] === null) delete c[k]; else c[k] = kopya(ozellik[k]);
      }
    }
    if (ozellik && ozellik.yalniz_cekme) is.uyar("Yalnız çekme çubuğu: TBDY 2018 9.6.4.3 uyarınca SDY sistemlerde kullanılamaz; SDS'de KL/i ≤ 300 ile izinlidir. Yalnız çekme elemanı varsa kombinasyonlar yinelemeli çözülür (süperpozisyon geçersiz).");
    return is.bitir();
  }
  function serbestlikAta(model, nolar, ayar) {
    const is = new Is(model);
    ayar = ayar || {};
    for (const uc of ["i", "j"]) {
      for (const s of ayar[uc] || []) if (SERBESTLIKLER.indexOf(s) < 0) throw new ModelHatasi("Uç serbestliği '" + s + "' tanımsız; seçenekler: " + SERBESTLIKLER.join(", ") + ".");
    }
    for (const no of Array.isArray(nolar) ? nolar : [nolar]) {
      const c = is.cubuk(no);
      serbestYaz(c, ayar.i, ayar.j);
      const i = serbestUc(c, "i"), j = serbestUc(c, "j");
      const iki = SERBESTLIKLER.filter(function (s) { return ["N", "T", "Vy", "Vz"].indexOf(s) >= 0 && i.indexOf(s) >= 0 && j.indexOf(s) >= 0; });
      if (iki.length) is.uyar("Çubuk " + c.no + ": " + iki.join(", ") + " iki uçta da serbest → çubuk mekanizması (kararsız). Kafes çubuğu için KAFES_CUBUGU (T yalnız bir uçta) kullanın.");
      if ((i.indexOf("Vy") >= 0 && j.indexOf("Mz") >= 0 && i.indexOf("Mz") >= 0) || (j.indexOf("Vy") >= 0 && i.indexOf("Mz") >= 0 && j.indexOf("Mz") >= 0) ||
          (i.indexOf("Vz") >= 0 && j.indexOf("My") >= 0 && i.indexOf("My") >= 0) || (j.indexOf("Vz") >= 0 && i.indexOf("My") >= 0 && j.indexOf("My") >= 0)) {
        is.uyar("Çubuk " + c.no + ": kesme ve iki uç momenti birlikte serbest → çubuk mekanizması.");
      }
    }
    return is.bitir();
  }

  // ---- böl
  function bol(model, cubukNo, sec) {
    sec = sec || {};
    const is = new Is(model, sec);
    const c = is.cubuk(cubukNo), u = is.uclar(c), Pi = is.kon(u[0]), Pj = is.kon(u[1]), L = uzaklik(Pi, Pj);
    if (L <= is.tol) throw new ModelHatasi("Çubuk " + cubukNo + " sıfır boylu; bölünemez.");
    let ts;
    if (sec.parca != null) {
      const n = Math.round(+sec.parca);
      if (!(n >= 2)) throw new ModelHatasi("bol: parca en az 2 olmalı.");
      ts = []; for (let k = 1; k < n; k++) ts.push(k / n);
    } else if (sec.uzunluk != null) {
      const s = +sec.uzunluk;
      if (!(s > is.tol)) throw new ModelHatasi("bol: uzunluk pozitif olmalı (m).");
      if (s >= L - is.tol) is.uyar("Parça uzunluğu (" + s + " m) çubuk boyundan (" + fmt(L, 3) + " m) küçük değil; bölünmedi.");
      ts = [];
      for (let k = 1; k * s < L - is.tol; k++) ts.push(sec.bastan === false ? 1 - k * s / L : k * s / L);
    } else if (Array.isArray(sec.oranlar)) {
      ts = [];
      for (const t of sec.oranlar.map(Number)) { if (t > 0 && t < 1) ts.push(t); else is.uyar("Oran " + t + " (0, 1) aralığında değil; atlandı."); }
    } else if (Array.isArray(sec.noktalar)) {
      const parcalar = is.bolNoktalarla(+cubukNo, sec.noktalar.map(function (p) { return nokta3(p, "Bölme noktası"); }));
      return is.bitir({ parcalar: parcalar });
    } else throw new ModelHatasi("bol: {parca: n}, {uzunluk: m, bastan}, {oranlar: [...]} ya da {noktalar: [[X,Y,Z], ...]} verilmeli.");
    const parcalar = is.bolIc(+cubukNo, ts);
    return is.bitir({ parcalar: parcalar });
  }
  function kesisimlerdeBol(model, cubukNolari, sec) {
    const is = new Is(model, sec);
    const nolar = [...new Set((cubukNolari || []).map(Number))];
    const veri = nolar.map(function (no) { const u = is.uclar(is.cubuk(no)); return { no: no, A: is.kon(u[0]), B: is.kon(u[1]) }; });
    const nok = new Map();
    const ekle = function (no, P) { if (!nok.has(no)) nok.set(no, []); nok.get(no).push(P); };
    let sayi = 0;
    for (let i = 0; i < veri.length; i++) {
      for (let j = i + 1; j < veri.length; j++) {
        const a = veri[i], b = veri[j];
        const r = parcaKesisim(a.A, a.B, b.A, b.B, is.tol);
        if (!r) continue;
        if (r.paralel) {
          if (r.esDogrusal && r.ortusme) is.uyar("Çubuk " + a.no + " ve " + b.no + " eş doğrusal ve üst üste; kesişimde bölünmedi (birlestir ya da dugumleriBirlestir kullanın).");
          continue;
        }
        const icA = r.s * r.L1 > is.tol && (1 - r.s) * r.L1 > is.tol, icB = r.t * r.L2 > is.tol && (1 - r.t) * r.L2 > is.tol;
        if (icA) ekle(a.no, r.P);
        if (icB) ekle(b.no, r.P);
        if (icA || icB) sayi++;
      }
    }
    const parcalar = {};
    for (const [no, pts] of nok) parcalar[no] = is.bolNoktalarla(no, pts);
    return is.bitir({ parcalar: parcalar, kesisim_sayisi: sayi });
  }
  function duzlemleBol(model, cubukNolari, duzlem, sec) {
    const is = new Is(model, sec);
    const d = duzlemCoz(duzlem), parcalar = {};
    for (const no of [...new Set((cubukNolari || []).map(Number))]) {
      const u = is.uclar(is.cubuk(no)), si = ic(cikar(is.kon(u[0]), d.p0), d.n), sj = ic(cikar(is.kon(u[1]), d.p0), d.n);
      if ((si > is.tol && sj < -is.tol) || (si < -is.tol && sj > is.tol)) parcalar[no] = is.bolIc(no, [si / (si - sj)]);
    }
    return is.bitir({ parcalar: parcalar });
  }

  // ---- birleştir
  function birlestir(model, cubukNolari, sec) {
    const is = new Is(model, sec);
    const r = is.birlestirIc((cubukNolari || []).map(Number), false);
    return is.bitir({ birlesen: r.yeni, reddedilen: r.red });
  }

  // ---- kopyala / taşı / ayna / döndür
  function dogrusalDizi(model, secim, dX, dY, dZ, adet, sec) {
    const is = new Is(model, sec);
    const s = is.secimCoz(secim), d = nokta3([dX, dY, dZ], "Öteleme");
    const n = adet == null ? 1 : Math.round(+adet);
    if (!(n >= 1)) throw new ModelHatasi("dogrusalDizi: adet en az 1 olmalı.");
    if (boy(d) <= is.tol) throw new ModelHatasi("dogrusalDizi: öteleme sıfır.");
    const kopyalar = [];
    for (let k = 1; k <= n; k++) kopyalar.push(is.kopyalaIc(s, function (P) { return topla(P, olcek(d, k)); }, null, sec));
    return is.bitir({ kopyalar: kopyalar });
  }
  /** Kopyasız taşıma sonucu: ret varsa model değişmeden (reddet), yoksa rapor. */
  function tasiSonuc(model, is, esle) {
    if (esle && esle.red) return reddet(model, is.uy.concat(esle.red));
    return is.bitir({ dugum_esleme: [...esle] });
  }
  function tasi(model, secim, dX, dY, dZ, sec) {
    const is = new Is(model, sec);
    const s = is.secimCoz(secim), d = nokta3([dX, dY, dZ], "Öteleme");
    return tasiSonuc(model, is, is.tasiIc(s, function (P) { return topla(P, d); }, null));
  }
  function ayna(model, secim, duzlem, sec) {
    sec = Object.assign({ kopya: true }, sec || {});
    const is = new Is(model, sec);
    const s = is.secimCoz(secim), d = duzlemCoz(duzlem);
    const R = function (v) { return cikar(v, olcek(d.n, 2 * ic(v, d.n))); };
    const f = function (P) { return cikar(P, olcek(d.n, 2 * ic(cikar(P, d.p0), d.n))); };
    if (sec.kopya) return is.bitir({ kopya: is.kopyalaIc(s, f, R, sec) });
    return tasiSonuc(model, is, is.tasiIc(s, f, R));
  }
  /** eksen: {nokta: [..], yon: [..]} ya da "X"|"Y"|"Z" (orijinden geçen); aci derece, sağ el kuralı. */
  function dondur(model, secim, eksen, aci, sec) {
    sec = Object.assign({ kopya: false, adet: 1 }, sec || {});
    const is = new Is(model, sec);
    const s = is.secimCoz(secim);
    let p0 = [0, 0, 0], yon;
    if (typeof eksen === "string" && GLOBAL_YON[eksen.toUpperCase()]) yon = GLOBAL_YON[eksen.toUpperCase()];
    else if (eksen && eksen.yon) { yon = nokta3(eksen.yon, "Eksen yönü"); if (eksen.nokta) p0 = nokta3(eksen.nokta, "Eksen noktası"); }
    else throw new ModelHatasi('dondur: eksen "X"|"Y"|"Z" ya da {"nokta": [..], "yon": [..]} olmalı.');
    if (boy(yon) < 1e-12) throw new ModelHatasi("dondur: eksen yönü sıfır.");
    const yap = function (k) { const R = donmeR(yon, (+aci || 0) * k * D2R); return { R: R, f: function (P) { return topla(p0, R(cikar(P, p0))); } }; };
    if (sec.kopya) {
      const kopyalar = [];
      for (let k = 1; k <= Math.max(1, Math.round(+sec.adet)); k++) { const t = yap(k); kopyalar.push(is.kopyalaIc(s, t.f, t.R, sec)); }
      return is.bitir({ kopyalar: kopyalar });
    }
    const t = yap(1);
    return tasiSonuc(model, is, is.tasiIc(s, t.f, t.R));
  }

  // ---- panel
  function reddet(model, uyarilar) {
    return { model: kopya(model), eklenen: { dugumler: [], cubuklar: [], paneller: [] }, silinen: { dugumler: [], cubuklar: [], paneller: [] },
      degisen: { dugumler: [], cubuklar: [], paneller: [] }, uyarilar: uyarilar, reddedildi: true };
  }
  function panelOlustur(model, dugumRefleri, ozellik, sec) {
    sec = sec || {};
    const is = new Is(model, sec);
    if (!Array.isArray(dugumRefleri) || dugumRefleri.length < 3) throw new ModelHatasi("Panel için en az üç köşe gerekir.");
    const nolar = dugumRefleri.map(function (r) { return is.refNo(r); });
    if (new Set(nolar).size !== nolar.length) { is.uyar("Panel köşeleri tekrarlı düğüm içeriyor; panel oluşturulmadı."); return reddet(model, is.uy); }
    const g = panelGeometri(nolar.map(function (n) { return is.kon(n); }), sec.tol_duzlem || 0.005);
    if (!g.ok) { is.uyar("Panel oluşturulmadı: " + g.sebep + "."); return reddet(model, is.uy); }
    if (g.esDogrusal) is.uyar("Panelde " + g.esDogrusal + " köşe komşu kenarlarla eş doğrusal (kenar üzerinde ara düğüm).");
    const anah = nolar.slice().sort(function (a, b) { return a - b; }).join(",");
    for (const p of is.m.paneller) {
      const k = p.kose.map(function (r) { return is.refNo(r, false); }).sort(function (a, b) { return a - b; }).join(",");
      if (k === anah) { is.uyar("Aynı köşelerle panel " + p.no + " zaten var; oluşturulmadı."); return reddet(model, is.uy); }
    }
    const oz = Object.assign({ tur: "doseme", dagitim: "iki" }, ozellik || {});
    delete oz.no; delete oz.kose;
    const p = Object.assign({ no: is.yeniNo(is.m.paneller, is.m.dosemeler), kose: nolar.map(function (n) { return is.refYaz(n); }) }, oz);
    is.m.paneller.push(p);
    const eksik = is.panelKenarlari(p).filter(function (k) { return !k.tam; });
    if (eksik.length) is.uyar("Panel " + p.no + ": " + eksik.map(function (k) { return k.kenar + ". kenar (" + k.dugumler.join("–") + ")"; }).join(", ") + " üzerinde tam çubuk zinciri yok; yük aktarılamaz (§12.3).");
    return is.bitir({ no: p.no, geometri: g });
  }

  // ---- üreteçler
  function caprazUret(model, goz, tip, secenek) {
    const is = new Is(model, secenek);
    const r = is.caprazIc(goz, tip, secenek);
    return is.bitir(r);
  }
  function makasUret(model, parametre) {
    const is = new Is(model, parametre);
    return is.bitir(is.makasIc(parametre));
  }
  function besikCerceveUret(model, parametre) {
    const is = new Is(model, parametre);
    return is.bitir(is.besikIc(parametre));
  }
  function asikUret(model, hedef, aralik, kesit, secenek) {
    const is = new Is(model, secenek);
    return is.bitir(is.asikIc(hedef, aralik, kesit, secenek));
  }
  function krenYoluUret(model, kolonlar, kot, konsol_boy, kesitler, kren) {
    const is = new Is(model);
    return is.bitir(is.krenIc(kolonlar, kot, konsol_boy, kesitler, kren));
  }
  function cepheKirisleriUret(model, parametre) {
    const is = new Is(model, parametre);
    return is.bitir(is.cepheIc(parametre));
  }
  function uretecSil(model, uretecNo) {
    const is = new Is(model);
    is.uretecSilIc(uretecNo);
    return is.bitir();
  }
  function birlesik(eski, yeni) {
    const r = Object.assign({}, eski);
    for (const k of Object.keys(yeni || {})) {
      const v = yeni[k];
      r[k] = v && typeof v === "object" && !Array.isArray(v) && eski[k] && typeof eski[k] === "object" && !Array.isArray(eski[k]) ? Object.assign({}, eski[k], v) : v;
    }
    return r;
  }
  function uretecGuncelle(model, uretecNo, yeniParametreler) {
    const is = new Is(model);
    const eski = is.uretecSilIc(uretecNo);
    const p = birlesik(eski, yeniParametreler);
    delete p.no; delete p.bolunen; delete p.tur_degisen;
    const no = +uretecNo;
    let r;
    if (eski.tur === "capraz") r = is.caprazIc(p.goz, p.tip, p.secenek, no);
    else if (eski.tur === "makas") r = is.makasIc(p, no);
    else if (eski.tur === "besik-cerceve") { delete p.mahya_kotu; if (yeniParametreler && yeniParametreler.egim != null && yeniParametreler.mahya == null) delete p.mahya; r = is.besikIc(p, no); }
    else if (eski.tur === "asik") r = is.asikIc(p.hedef, p.aralik, p.kesit, p.secenek, no);
    else if (eski.tur === "kren-yolu") r = is.krenIc(p.kolonlar, p.kot, p.konsol_boy, p.kesitler, p.kren, no);
    else if (eski.tur === "cephe-kirisi") { if (yeniParametreler && yeniParametreler.aralik != null && yeniParametreler.kotlar == null) delete p.kotlar; r = is.cepheIc(p, no); }
    else throw new ModelHatasi("Üreteç türü '" + eski.tur + "' yeniden üretilemiyor.");
    return is.bitir(r);
  }

  // ---- doğrulama
  /**
   * §19: serbest koordinatlı düğümleri aks sistemine bağlar. Her {no, X, Y, Z} kaydı:
   *   1) tol içinde bir aks kesişimine düşüyorsa (GLOBAL ya da ek sistem) bütün başvuruları o kesişimin aks REF'ine çevrilir, kayıt silinir;
   *   2) değilse, uçları aksa bağlı (ya da zaten parametrik) bir çubuğun üzerindeyse {tur: "bolme", cubuk_i, cubuk_j, oran} olur;
   *   3) ikisi de değilse serbest kalır (raporda "kalan").
   * Dönüş: rapor + {baglanan: [{no, ref}], bolme: [no], kalan: [no]}.
   */
  function aksaBagla(model, tol) {
    const MA = aksGerekli();
    const is = new Is(model, tol != null ? { tol: +tol } : null);
    const t = is.tol;
    const serbest = function (d) { return d && d.no != null && !d.tur && d.X != null && !(is.harita().get(+d.no) || {}).izgara; };
    const baglanan = [], bolme = [], kalan = [];
    // 1) aks kesişimleri
    const esle = new Map();
    for (const d of is.m.dugumler) {
      if (!serbest(d)) continue;
      const ref = MA.koordinattanRef(is.m, [+d.X, +d.Y, +d.Z], { tol: t });
      if (!ref) continue;
      esle.set(+d.no, is.refNo(ref));
      baglanan.push({ no: +d.no, ref: ref });
    }
    if (esle.size) {
      is.refDegistir(esle);
      is.m.dugumler = is.m.dugumler.filter(function (d) { return !(d && esle.has(+d.no)); });
      is._h = null;
    }
    // 2) çubuk üzerindeki noktalar → bölme düğümü (uçları aksa bağlı ya da parametrik çubuklar; kendisine dayanmayan)
    const yeniBolme = new Set();
    const sabitMi = function (no) { const e = is.harita().get(no); return !!e && !yeniBolme.has(no) && (e.izgara || !!(e.kayit && e.kayit.tur)); };
    // bölünmüş çubuk zinciri: düğümden iki zıt yöndeki eş doğrusal komşular boyunca sabit (aksa bağlı) uçlara yürünür → ana çubuğun uçları
    const kom = new Map();
    for (const c of is.m.cubuklar) {
      let u;
      try { u = is.uclar(c); } catch (e) { continue; }
      if (u[0] == null || u[1] == null) continue;
      if (!kom.has(u[0])) kom.set(u[0], []);
      if (!kom.has(u[1])) kom.set(u[1], []);
      kom.get(u[0]).push(u[1]); kom.get(u[1]).push(u[0]);
    }
    const yuru = function (onceki, simdi, v) {
      for (let guv = 0; !sabitMi(simdi); guv++) {
        if (guv > 10000) return null;
        const Ps = is.kon(simdi);
        let sonraki = null;
        for (const k of kom.get(simdi) || []) { if (k !== onceki && ic(birim(cikar(is.kon(k), Ps)), v) > 1 - 1e-6) { sonraki = k; break; } }
        if (sonraki == null) return null;
        onceki = simdi; simdi = sonraki;
      }
      return simdi;
    };
    let ilerledi = true;
    while (ilerledi) {
      ilerledi = false;
      for (const d of is.m.dugumler) {
        if (!serbest(d)) continue;
        const P = [+d.X, +d.Y, +d.Z];
        let en = null;
        for (const c of is.m.cubuklar) {
          let u;
          try { u = is.uclar(c); } catch (e) { continue; }
          if (u[0] === +d.no || u[1] === +d.no || !sabitMi(u[0]) || !sabitMi(u[1])) continue;
          const A = is.kon(u[0]), B = is.kon(u[1]), r = dogruyaUzaklik(P, A, B), L = uzaklik(A, B);
          if (r.d > t || r.t * L <= t || (1 - r.t) * L <= t) continue;
          if (!en || r.d < en.d) en = { d: r.d, t: r.t, u: u };
        }
        const kl = kom.get(+d.no) || [];
        for (let i = 0; !en && i < kl.length; i++) {
          for (let j = i + 1; !en && j < kl.length; j++) {
            const va = birim(cikar(is.kon(kl[i]), P)), vb = birim(cikar(is.kon(kl[j]), P));
            if (ic(va, vb) > -1 + 1e-6) continue;
            const ea = yuru(+d.no, kl[i], va), eb = yuru(+d.no, kl[j], vb);
            if (ea == null || eb == null || ea === eb) continue;
            const r = dogruyaUzaklik(P, is.kon(ea), is.kon(eb));
            en = { d: r.d, t: r.t, u: [ea, eb] };
          }
        }
        if (!en) continue;
        const ri = is.refYaz(en.u[0]), rj = is.refYaz(en.u[1]);
        for (const k of ["X", "Y", "Z"]) delete d[k];
        d.tur = "bolme"; d.cubuk_i = ri; d.cubuk_j = rj; d.oran = r9(en.t);
        bolme.push(+d.no); yeniBolme.add(+d.no);
        is._h = null;
        ilerledi = true;
      }
    }
    for (const d of is.m.dugumler) if (serbest(d)) kalan.push(+d.no);
    if (kalan.length) is.uyar(kalan.length + " düğüm hiçbir aks kesişimine ya da çubuğa düşmüyor; serbest koordinatlı kaldı (" + kalan.slice(0, 8).join(", ") + (kalan.length > 8 ? "…" : "") + "). Gerekirse oraya aks ekleyin.");
    return is.bitir({ baglanan: baglanan, bolme: bolme, kalan: kalan });
  }

  function denetle(model, sec) {
    const is = new Is(model, sec);
    const m = is.m, u = [], tol = is.tol;
    const ekle = function (kod, mesaj, ek) { u.push(Object.assign({ kod: kod, mesaj: mesaj }, ek || {})); };
    const gecerli = [];
    for (const c of m.cubuklar) {
      try { const uc = is.uclar(c); if (uc[0] == null || uc[1] == null) throw new Error(); gecerli.push({ c: c, a: uc[0], b: uc[1], A: is.kon(uc[0]), B: is.kon(uc[1]) }); }
      catch (e) { ekle("eksik-dugum", "Çubuk " + c.no + " olmayan bir düğüme bağlı.", { cubuk: +c.no }); }
    }
    const bag = is.baglantilar();
    for (const d of m.dugumler) {
      const b = bag.get(+d.no);
      if (!b || (!b.cubuk.length && !b.panel.length && !b.aksKat)) ekle("yuzen-dugum", "Düğüm " + d.no + " hiçbir çubuğa ya da panele bağlı değil (yüzen düğüm).", { dugum: +d.no });
    }
    for (const g of gecerli) if (uzaklik(g.A, g.B) <= tol) ekle("sifir-boy", "Çubuk " + g.c.no + " sıfır boylu (" + fmt(uzaklik(g.A, g.B) * 1000, 2) + " mm).", { cubuk: +g.c.no });
    for (let i = 0; i < gecerli.length; i++) {
      for (let j = i + 1; j < gecerli.length; j++) {
        const a = gecerli[i], b = gecerli[j];
        if ((a.a === b.a && a.b === b.b) || (a.a === b.b && a.b === b.a)) { ekle("cakisan-cubuk", "Çubuk " + a.c.no + " ve " + b.c.no + " aynı iki düğümü bağlıyor.", { cubuklar: [+a.c.no, +b.c.no] }); continue; }
        const ra = dogruyaUzaklik(b.A, a.A, a.B), rb = dogruyaUzaklik(b.B, a.A, a.B), L = uzaklik(a.A, a.B);
        if (ra.d > tol || rb.d > tol || L <= tol) continue;
        const lo = Math.max(0, Math.min(ra.t, rb.t)), hi = Math.min(1, Math.max(ra.t, rb.t));
        if ((hi - lo) * L > tol) ekle("cakisan-cubuk", "Çubuk " + a.c.no + " ve " + b.c.no + " eş doğrusal ve üst üste (" + fmt((hi - lo) * L, 3) + " m).", { cubuklar: [+a.c.no, +b.c.no] });
      }
    }
    for (const p of m.paneller) {
      let k;
      try { k = is.panelKenarlari(p); } catch (e) { ekle("eksik-dugum", "Panel " + p.no + " olmayan bir düğüme bağlı.", { panel: +p.no }); continue; }
      const g = panelGeometri(p.kose.map(function (r) { return is.kon(is.refNo(r, false)); }), (sec && sec.tol_duzlem) || 0.005);
      if (!g.ok) ekle("panel-geometri", "Panel " + p.no + ": " + g.sebep + ".", { panel: +p.no });
      for (const e of k) if (!e.tam) ekle("panel-kenari", "Panel " + p.no + " " + e.kenar + ". kenarında (" + e.dugumler.join("–") + ") çubuk yok ya da zincir eksik (" + e.bosluklar.map(function (b) { return fmt(b[0], 3) + "–" + fmt(b[1], 3) + " m"; }).join(", ") + ").", { panel: +p.no, kenar: e.kenar });
    }
    // bağlanırlık ve mesnet
    const kenarlar = gecerli.map(function (g) { return [g.a, g.b]; }).concat(is.aksKatKenarlari());
    const ata = new Map();
    const kok = function (n) { if (!ata.has(n)) ata.set(n, n); while (ata.get(n) !== n) { ata.set(n, ata.get(ata.get(n))); n = ata.get(n); } return n; };
    for (const e of kenarlar) { const r1 = kok(e[0]), r2 = kok(e[1]); if (r1 !== r2) ata.set(r1, r2); }
    const parca = new Map();
    for (const n of ata.keys()) { const r = kok(n); if (!parca.has(r)) parca.set(r, []); parca.get(r).push(n); }
    const mesnetli = function (n) { return is.mesnetli(n); };
    const hepsi = [...parca.values()];
    if (hepsi.length && !hepsi.some(function (l) { return l.some(mesnetli); })) ekle("mesnetsiz", "Yapıda hiç mesnet yok (mesnetler listesi boş, aks–kat temel düğümü de kullanılmıyor).");
    else if (hepsi.length > 1) {
      for (const l of hepsi) if (!l.some(mesnetli)) ekle("bagsiz-parca", "Düğüm " + l.slice(0, 6).join(", ") + (l.length > 6 ? "…" : "") + " içeren parça yapının geri kalanına bağlı değil ve mesnetsiz.", { dugumler: l });
    }
    for (const [n, b] of bag) {
      if (!b.cubuk.length || b.aksKat || is.mesnetli(n, true)) continue;
      const hepsiMafsal = b.cubuk.every(function (x) { const s = serbestUc(is.cubukBul(x.no), x.uc); return s.indexOf("My") >= 0 && s.indexOf("Mz") >= 0; });
      if (hepsiMafsal) ekle("mafsalli-dugum", "Düğüm " + n + "'e bağlı bütün çubuk uçları mafsallı (My, Mz serbest): düğüm dönmesi tutulmuyor — mekanizma şüphesi. Bir çubuğu sürekli bırakın.", { dugum: n });
    }
    return { gecerli: u.length === 0, uyarilar: u,
      ozet: { dugum: m.dugumler.length, cubuk: m.cubuklar.length, panel: m.paneller.length, mesnet: m.mesnetler.length, parca: hepsi.length } };
  }

  return Object.freeze({
    TOL: TOL, ILK_SERBEST_DUGUM: ILK_SERBEST_DUGUM, SERBESTLIKLER: SERBESTLIKLER, MAFSAL_IKI_UC: MAFSAL_IKI_UC, MAFSAL_I: MAFSAL_I,
    MAFSAL_J: MAFSAL_J, KAFES_CUBUGU: KAFES_CUBUGU, CAPRAZ_TIPLERI: CAPRAZ_TIPLERI, MAKAS_TIPLERI: MAKAS_TIPLERI, ModelHatasi: ModelHatasi,
    // okuma / geometri
    dugumKonumu: dugumKonumu, dugumBul: dugumBul, dugumNo: dugumNo, uzunluk: uzunluk, egim: egim, yerelEksenler: yerelEksenler,
    yerelEksenVektor: yerelEksenVektor, aciHedef: aciHedef, panelKenarCubuklari: panelKenarCubuklari, panelGeometrisi: panelGeometrisi,
    parcaKesisim: parcaKesisim, denetle: denetle, aksaBagla: aksaBagla,
    // düzenleme
    genellestir: genellestir, dugumEkle: dugumEkle, dugumTasi: dugumTasi, dugumSil: dugumSil, dugumleriBirlestir: dugumleriBirlestir,
    cubukCiz: cubukCiz, cubukZinciri: cubukZinciri, cubukSil: cubukSil, ozellikAta: ozellikAta, serbestlikAta: serbestlikAta,
    bol: bol, kesisimlerdeBol: kesisimlerdeBol, duzlemleBol: duzlemleBol, birlestir: birlestir,
    tasi: tasi, dogrusalDizi: dogrusalDizi, ayna: ayna, dondur: dondur, panelOlustur: panelOlustur, panelSil: panelSil,
    // üreteçler
    caprazUret: caprazUret, makasUret: makasUret, besikCerceveUret: besikCerceveUret, asikUret: asikUret, krenYoluUret: krenYoluUret,
    cepheKirisleriUret: cepheKirisleriUret, uretecSil: uretecSil, uretecGuncelle: uretecGuncelle,
  });
});
