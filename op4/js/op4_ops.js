/* op4 — yeni saf model işlemleri (MIMARI §9.6, §10.2–§10.4, §13.4; "F1 paket sözleşmeleri" §S26).
   Saf modül: DOM yok. QuickJS'te self.Op4Ops, node'da module.exports (UMD; docs/model_ops.js ile aynı kalıp).
   Sahibi: B (model-cekirdegi). İmzalar ve dönüş biçimleri JSDoc'tadır (sözleşme); TASLAK listesi boştur (F1 iş 1.3).

   Bağımlılıklar (QuickJS'te self üstünden, node'da require ile; bagimliliklarKur ile de verilebilir):
     MatrisAks (docs/aks_sistemi.js: sistemler, Cozucu, refAnahtar), ModelOps (docs/model_ops.js: genellestir,
     yerelEksenVektor), MatrisIFC (docs/ifc_disari.js: PROFILLER, basitProfil — kesit kütüphanesi).

   Eleman kimliği JS'te {tur, no, alt?} nesnesidir: tur kod adı ("cubuk", "panel", "dugum", "mesnet", "yuk", "aks",
   "aks_sistemi", "temel"), no tamsayı, alt varsayılan 0 (C++ ElemanKimligi; kaynak/cekirdek/kimlik.h). Sayısal kodlar
   KODLAR'dadır ve op4/veri/sahne_kodlari.json ile aynıdır (op4/testler/js/sozlesme.test.js denetler).

   Ortak çözümleme (cozumle): bütün işlevler modeli önce GENEL GÖRÜNÜME çevirir — aks–kat (surum 1) kolon / kiriş / döşemesi
   olan modelde ModelOps.genellestir çıktısı (kimlikler genelSecim'le eşlenen genel kimliklerdir, MIMARI §10.5), değilse
   modelin kendisi. Düğüm numaraları ModelOps'un iç numaralarıyla aynıdır: aks–kat 1000·kat + 20·ix + iy + 1, serbest /
   bölme / kesişim kayıtları kendi no'su, kat dışı Z aksı ve ek sistem kesişimleri 800001… (ModelOps Is.sanalDugumler sırası),
   koordinatlı başvurular 1 mm içindeki düğüm ya da en büyük kayıt no'sundan sonraki numara. Hiçbir işlev girdisini değiştirmez.
   Çağıran (cephe) aynı model için cozumle sonucunu `ek.cozum` ile yeniden kullanabilir. */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika(kok);
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.Op4Ops = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function (kok) {
  "use strict";

  const SURUM = "0.1.0";

  /** Sahne kod tabloları (op4/veri/sahne_kodlari.json ile birebir). Değerler değişmez, yalnız eklenir. */
  const KODLAR = Object.freeze({
    eleman_turu: Object.freeze({ yok: 0, cubuk: 1, panel: 2, dugum: 3, mesnet: 4, yuk: 5, aks: 6, aks_sistemi: 7, temel: 8, referans: 9, olcu: 10 }),
    cubuk_turu: Object.freeze({ diger: 0, kolon: 1, kiris: 2, capraz: 3, "makas-ust": 4, "makas-alt": 5, "makas-dikme": 6, "makas-diyagonal": 7, asik: 8, kren: 9, bag: 10 }),
    panel_turu: Object.freeze({ doseme: 0, cati: 1, cephe: 2, diger: 3 }),
    dugum_turu: Object.freeze({ aks_kat: 0, aks_kesisimi: 1, bolme: 2, kesisim: 3, serbest: 4 }),
    kesit_turu: Object.freeze({ bilinmiyor: 0, I: 1, KUTU: 2, BORU: 3, DIKDORTGEN: 4, DAIRE: 5, L: 6, "2L": 7, UPN: 8 }),
    mesnet_turu: Object.freeze({ diger: 0, ankastre: 1, mafsal: 2, kayici: 3, yay: 4 }),
    temel_turu: Object.freeze({ tekil: 0, surekli: 1, radye: 2 }),
    cubuk_bayraklari: Object.freeze({ yalniz_cekme: 1, serbest_dugume_bagli: 2, vute: 4, uretecten: 8 }),
    dugum_bayraklari: Object.freeze({ mesnetli: 1, baglantisiz: 2 }),
    panel_bayraklari: Object.freeze({ duzlemsel_degil: 1 }),
    serbestlik_sirasi: Object.freeze(["N", "Vy", "Vz", "T", "My", "Mz"]),
    mesnet_sirasi: Object.freeze(["ux", "uy", "uz", "rx", "ry", "rz"]),
  });

  /** Faz 1 öznitelik kimlikleri (op4/veri/oznitelikler.json; C++ oznitelik::*). Sıra C++ BosOznitelikTablosu ile aynıdır. */
  const OZNITELIK_IDLERI = Object.freeze(["tur", "no", "ad", "alt_tur", "kullanim_yeri", "kat", "seviye", "kesit", "profil",
    "malzeme", "sistem", "grup", "uzunluk", "egim", "aci", "kalinlik", "alan", "serbest_i", "serbest_j", "serbest_dugum",
    "x", "y", "z"]);
  /** Sütun türleri ve birimleri (oznitelikler.json "tur", "birim"). */
  const OZNITELIK_TURLERI = Object.freeze({
    tur: "enum", no: "sayi", ad: "metin", alt_tur: "enum", kullanim_yeri: "enum", kat: "liste", seviye: "metin", kesit: "metin",
    profil: "metin", malzeme: "metin", sistem: "enum", grup: "metin", uzunluk: "sayi", egim: "sayi", aci: "sayi", kalinlik: "sayi",
    alan: "sayi", serbest_i: "metin", serbest_j: "metin", serbest_dugum: "bool", x: "sayi", y: "sayi", z: "sayi",
  });
  const OZNITELIK_BIRIMLERI = Object.freeze({ uzunluk: "m", egim: "°", aci: "°", kalinlik: "m", alan: "m²", x: "m", y: "m", z: "m" });

  /** Henüz gövdesi doldurulmamış işlevler (F1 iş 1.3 ile boşaldı). */
  const TASLAK = Object.freeze([]);

  const TOL = 0.001;        // 1 mm (MIMARI §10.2)
  const TOL_YER = 0.01;     // 1 cm (MIMARI §10.3)
  const TOL_DUZLEM = 0.005; // panel düzlemsellik (ModelOps panelGeometri ile aynı)
  const ILK_SERBEST = 100001;
  const ILK_AKS_DUGUM = 800001;
  const SAHNE_YOK = 0xFFFFFFFF;
  const D2R = Math.PI / 180;
  const SERBESTLIKLER = KODLAR.serbestlik_sirasi;
  const MESNET_SIRASI = KODLAR.mesnet_sirasi;
  const AKS_PAYI = 1.5;     // aks çizgisi uzantısı (m), balon 0,5 m ötede (OrnekSahneAnlik ile aynı)

  class Op4Hatasi extends Error {
    constructor(mesaj) { super(mesaj); this.name = "Op4Hatasi"; }
  }

  // ---------------------------------------------------------------- bağımlılıklar
  const verilen = {};
  const YOLLAR = { MatrisAks: "../../docs/aks_sistemi.js", ModelOps: "../../docs/model_ops.js", MatrisIFC: "../../docs/ifc_disari.js" };
  function bag(ad, zorunlu) {
    if (verilen[ad]) return verilen[ad];
    if (kok && kok[ad]) return kok[ad];
    if (typeof self !== "undefined" && self[ad]) return self[ad];
    if (typeof require === "function") {
      try { verilen[ad] = require(YOLLAR[ad]); return verilen[ad]; } catch (e) { /* yok */ }
    }
    if (zorunlu !== false) throw new Op4Hatasi(ad + " modülü yüklenmedi (" + YOLLAR[ad] + ").");
    return null;
  }
  /** Bağımlılıkları açıkça verir (cephe olustur() ve sınamalar). */
  function bagimliliklarKur(b) { for (const k of Object.keys(b || {})) if (b[k]) verilen[k] = b[k]; }

  // ---------------------------------------------------------------- küçük yardımcılar
  function liste(m, ad) { return m && Array.isArray(m[ad]) ? m[ad] : []; }
  function uzaklik(a, b) { const dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2]; return Math.sqrt(dx * dx + dy * dy + dz * dz); }
  function r6(v) { const r = Math.round(v * 1e6) / 1e6; return r === 0 ? 0 : r; }
  function surumSayi(s) {
    if (typeof s === "boolean") return 1;
    if (typeof s === "number") return isFinite(s) ? Math.trunc(s) : 1;
    if (typeof s === "string" && /^\s*[+-]?\d+(\.\d+)?\s*$/.test(s)) return Math.trunc(parseFloat(s));
    return 1;
  }
  function aksKatElemanVar(m) { return liste(m, "kolonlar").length + liste(m, "kirisler").length + liste(m, "dosemeler").length > 0; }
  function aksSistemiVar(m) {
    return !!(m && ((m.akslar && Array.isArray(m.akslar.z) && m.akslar.z.length) || (Array.isArray(m.aks_sistemleri) && m.aks_sistemleri.length)));
  }
  function kimlikAnahtari(k) { return (KODLAR.eleman_turu[k.tur] || 0) * 281474976710656 + (k.alt || 0) * 4294967296 + (k.no >>> 0); }
  function kimlikSirala(l) { return l.sort(function (a, b) { return kimlikAnahtari(a) - kimlikAnahtari(b); }); }
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

  // ================================================================= ÇÖZÜMLEME (genel görünüm + düğüm numaraları)
  /** Genel görünüm: aks–kat elemanı varsa ModelOps.genellestir çıktısı, yoksa modelin kendisi. */
  function genelGorunum(model) {
    if (!aksKatElemanVar(model)) return { g: model, genellestirildi: false, uyarilar: [] };
    try {
      const r = bag("ModelOps").genellestir(model);
      return { g: r.model, genellestirildi: true, uyarilar: [] };
    } catch (e) {
      return { g: model, genellestirildi: false, uyarilar: ["Aks–kat elemanları genel görünüme çevrilemedi: " + e.message] };
    }
  }

  /** ModelOps Is.izgara ile aynı aks–kat ızgarası (yoksa null). */
  function izgaraKur(m) {
    const ak = m.akslar;
    let kt = m.katlar;
    const zKat = ak && Array.isArray(ak.z) ? ak.z.filter(function (a) { return a && a.kat != null && a.kat !== ""; }) : [];
    if ((!Array.isArray(kt) || !kt.length) && zKat.length) kt = zKat.map(function (a) { return { no: +a.kat, kot: +a.konum }; });
    if (!ak || !Array.isArray(ak.x) || !Array.isArray(ak.y) || !ak.x.length || !ak.y.length || !Array.isArray(kt) || !kt.length) return null;
    const sirala = function (l) { return l.map(function (a) { return { ad: String(a.ad), k: +a.konum }; }).sort(function (a, b) { return a.k - b.k; }); };
    const xs = sirala(ak.x), ys = sirala(ak.y);
    const katlar = new Map();
    kt.forEach(function (k, i) { katlar.set(k.no != null ? +k.no : i, +k.kot); });
    const zAd = new Map();
    zKat.forEach(function (a) { katlar.set(+a.kat, +a.konum); zAd.set(+a.kat, String(a.ad)); });
    return { xs: xs, ys: ys, katlar: katlar, zAd: zAd,
      ix: new Map(xs.map(function (a, i) { return [a.ad, i]; })), iy: new Map(ys.map(function (a, i) { return [a.ad, i]; })) };
  }

  /** Düğüm çözücü: REF → düğüm numarası ve konum (ModelOps Is.refNo / harita ile aynı numaralama). */
  function DugumCozucu(g) {
    this.g = g;
    this.MA = bag("MatrisAks");
    this.izg = izgaraKur(g);
    this.cz = new this.MA.Cozucu(g);
    this.kayit = new Map();
    let mx = ILK_SERBEST - 1;
    for (const d of liste(g, "dugumler")) if (d && d.no != null) { this.kayit.set(+d.no, d); if (+d.no > mx) mx = +d.no; }
    this.sonSerbest = mx;
    this.dugum = new Map();      // no → {no, P, tur, kayit}
    this._sanal = null;          // refAnahtar → no
    this._sanalP = null;         // no → {P, ref}
    this._sanalSon = ILK_AKS_DUGUM - 1;
    this._izgara = null;         // konum araması (koordinatlı REF) için
    this.S = null;
  }
  const DC = DugumCozucu.prototype;
  DC.sistemler = function () { if (!this.S) this.S = this.MA.sistemler(this.g); return this.S; };
  DC.izgaraNo = function (aks, kat) {
    const g = this.izg;
    if (!g || !Array.isArray(aks) || aks.length !== 2) return null;
    const ix = g.ix.get(String(aks[0])), iy = g.iy.get(String(aks[1])), k = kat == null ? 1 : +kat;
    if (ix == null || iy == null || !g.katlar.has(k)) return null;
    return 1000 * k + 20 * ix + iy + 1;
  };
  DC.izgaraKonumu = function (n) {
    const g = this.izg;
    if (!g || !(n > 0 && n < ILK_SERBEST)) return null;
    const kat = Math.floor(n / 1000), r = n - 1000 * kat - 1, ix = Math.floor(r / 20), iy = r % 20;
    if (r < 0 || ix >= g.xs.length || iy >= g.ys.length || !g.katlar.has(kat)) return null;
    return [g.xs[ix].k, g.ys[iy].k, g.katlar.get(kat)];
  };
  /** Is.sanalDugumler: ek sistemler önce, sonra GLOBAL (kat Z aksları hariç); her Z × u × v kesişimine sırayla numara. */
  DC.sanalKur = function () {
    if (this._sanal) return;
    this._sanal = new Map();
    this._sanalP = new Map();
    if (!aksSistemiVar(this.g)) return;
    const S = this.sistemler(), MA = this.MA, self = this;
    S.slice(1).concat(S.slice(0, 1)).forEach(function (s) {
      const yu = s.yonler[0], yv = s.yonler[1];
      s.l.z.forEach(function (z) {
        if (s.global && z.kat != null) return;
        s.l[yu].forEach(function (a) {
          s.l[yv].forEach(function (b) {
            const ref = s.global ? { aks: [a.ad, b.ad], z: z.ad } : { sistem: s.ad, aks: [a.ad, b.ad], z: z.ad };
            const no = ++self._sanalSon;
            self._sanal.set(MA.refAnahtar(self.g, ref), no);
            self._sanalP.set(no, { P: MA.sistemNokta(s, a.konum, b.konum, z.konum), ref: ref });
          });
        });
      });
    });
  };
  DC.aksRefNo = function (ref) {
    const g = this.izg;
    if ((!ref.sistem || ref.sistem === "GLOBAL") && ref.z != null && g) {
      for (const [kat, ad] of g.zAd) if (ad === String(ref.z)) { const n = this.izgaraNo(ref.aks, kat); if (n != null) return n; }
    }
    this.sanalKur();
    const k = this.MA.refAnahtar(this.g, ref);
    if (this._sanal.has(k)) return this._sanal.get(k);
    const P = this.cz.coz(ref);          // geçersizse AksHatasi
    const no = ++this._sanalSon;
    this._sanal.set(k, no);
    this._sanalP.set(no, { P: P, ref: ref });
    return no;
  };
  /** Bilinen bütün düğüm konumları içinde 1 mm'lik arama (koordinatlı REF; yalnız gerekince kurulur). */
  DC.bul = function (P) {
    if (!this._izgara) {
      const h = new Map(), self = this;
      const ekle = function (no, Q) {
        const k = Math.floor(Q[0] / TOL) + "," + Math.floor(Q[1] / TOL) + "," + Math.floor(Q[2] / TOL);
        if (!h.has(k)) h.set(k, []);
        h.get(k).push([no, Q]);
      };
      const g = this.izg;
      if (g) for (const [kat, kot] of g.katlar) for (let ix = 0; ix < g.xs.length; ix++) for (let iy = 0; iy < g.ys.length; iy++) ekle(1000 * kat + 20 * ix + iy + 1, [g.xs[ix].k, g.ys[iy].k, kot]);
      this.sanalKur();
      for (const [no, s] of this._sanalP) ekle(no, s.P);
      for (const no of this.kayit.keys()) { try { ekle(no, self.konum(no)); } catch (e) { /* çözülemeyen kayıt */ } }
      this._izgara = h;
    }
    let en = null, ed = TOL;
    const bx = Math.floor(P[0] / TOL), by = Math.floor(P[1] / TOL), bz = Math.floor(P[2] / TOL);
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (let c = -1; c <= 1; c++) {
      for (const [no, Q] of this._izgara.get((bx + a) + "," + (by + b) + "," + (bz + c)) || []) {
        const d = uzaklik(P, Q);
        if (d <= ed) { ed = d; en = no; }
      }
    }
    return en;
  };
  DC.koordinatNo = function (P) {
    const n = this.bul(P);
    if (n != null) return n;
    const no = ++this.sonSerbest;
    const Q = [r6(P[0]), r6(P[1]), r6(P[2])];
    this.dugum.set(no, { no: no, P: Q, tur: KODLAR.dugum_turu.serbest, kayit: null });
    const k = Math.floor(Q[0] / TOL) + "," + Math.floor(Q[1] / TOL) + "," + Math.floor(Q[2] / TOL);
    if (!this._izgara.has(k)) this._izgara.set(k, []);
    this._izgara.get(k).push([no, Q]);
    return no;
  };
  /** REF → düğüm numarası (geçersizse hata fırlatır). */
  DC.no = function (ref) {
    if (typeof ref === "string" && /^\d+$/.test(ref.trim())) ref = +ref;
    if (typeof ref === "number") {
      if (this.kayit.has(ref) || this.izgaraKonumu(ref) || this.dugum.has(ref)) return ref;
      this.sanalKur();
      if (this._sanalP.has(ref)) return ref;
      throw new Op4Hatasi("Düğüm " + ref + " modelde yok.");
    }
    if (Array.isArray(ref)) {
      if (ref.length !== 3 || !ref.every(function (v) { return v !== null && v !== "" && isFinite(+v); })) throw new Op4Hatasi("Koordinatlı düğüm [X, Y, Z] olmalı: " + JSON.stringify(ref));
      return this.koordinatNo(ref.map(Number));
    }
    if (ref && typeof ref === "object") {
      if (ref.dugum != null) return this.no(+ref.dugum);
      if (ref.aks != null && (ref.z != null || ref.sistem != null)) return this.aksRefNo(ref);
      if (ref.aks != null) {
        const n = this.izgaraNo(ref.aks, ref.kat);
        if (n == null) throw new Op4Hatasi("Aks–kat başvurusu geçersiz: " + JSON.stringify(ref));
        return n;
      }
      if (ref.X != null && ref.Y != null && ref.Z != null && [ref.X, ref.Y, ref.Z].every(function (v) { return isFinite(+v); })) return this.koordinatNo([+ref.X, +ref.Y, +ref.Z]);
    }
    throw new Op4Hatasi("Düğüm başvurusu anlaşılamadı: " + JSON.stringify(ref));
  };
  /** Numaralı düğümün konumu ve türü (önbellekli). */
  DC.dugumAl = function (no) {
    let d = this.dugum.get(no);
    if (d) return d;
    const T = KODLAR.dugum_turu, kayit = this.kayit.get(no) || null;
    let P = null, tur = T.serbest;
    if (kayit) {
      if (kayit.tur === "bolme") tur = T.bolme;
      else if (kayit.tur === "kesisim") tur = T.kesisim;
      else if (kayit.aks != null || kayit.kat != null || (no < ILK_SERBEST && this.izgaraKonumu(no))) tur = T.aks_kat;
      if (kayit.tur === "bolme" || kayit.tur === "kesisim") P = this.cz.coz({ dugum: no });
      else if (kayit.X != null) P = [+kayit.X, +kayit.Y, +kayit.Z];
      else P = this.izgaraKonumu(no);
      if (!P || !P.every(isFinite)) throw new Op4Hatasi("Düğüm " + no + " konumu çözülemedi.");
    } else if ((P = this.izgaraKonumu(no))) tur = T.aks_kat;
    else {
      this.sanalKur();
      const s = this._sanalP.get(no);
      if (!s) throw new Op4Hatasi("Düğüm " + no + " modelde yok.");
      P = s.P; tur = T.aks_kesisimi;
    }
    d = { no: no, P: P, tur: tur, kayit: kayit };
    this.dugum.set(no, d);
    return d;
  };
  DC.konum = function (no) { return this.dugumAl(no).P; };

  /**
   * Modelin ortak çözümlemesi: genel görünüm, kullanılan düğümler (no sıralı), çubuk / panel / mesnet bağları, seviyeler.
   * @param {Object} model bina JSON
   * @returns {Object} C — {g, genellestirildi, uyarilar, dugumler: [{no, P, tur, kayit}], dDizin: Map(no → dizin),
   *   cubuklar: [{c, i, j, tur}], paneller: [{p, kose: [dizin], tur}], mesnetler: [{d, maske, tur, ortuk}],
   *   seviyeler: [{ad, z, kat}], katlar: [{kat, z, ad}] (z sıralı), z0, temelTipi, temelMesnet}
   */
  function cozumle(model) {
    if (!model || typeof model !== "object" || Array.isArray(model)) throw new Op4Hatasi("Model bir bina JSON nesnesi olmalı.");
    const gg = genelGorunum(model), g = gg.g;
    const uy = gg.uyarilar.slice();
    const DCz = new DugumCozucu(g);
    const kul = new Map();     // düğüm no → kullanım sayısı (çubuk / panel)
    const no = function (ref, ne) {
      try { return DCz.no(ref); } catch (e) { uy.push(ne + ": " + e.message); return null; }
    };
    const cub = [];
    for (const c of liste(g, "cubuklar")) {
      if (!c || c.no == null) continue;
      const a = no(c.i, "Çubuk " + c.no + " i ucu"), b = no(c.j, "Çubuk " + c.no + " j ucu");
      if (a == null || b == null) continue;
      try { DCz.dugumAl(a); DCz.dugumAl(b); } catch (e) { uy.push("Çubuk " + c.no + ": " + e.message); continue; }
      kul.set(a, (kul.get(a) || 0) + 1); kul.set(b, (kul.get(b) || 0) + 1);
      cub.push({ c: c, a: a, b: b });
    }
    const pan = [];
    for (const p of liste(g, "paneller")) {
      if (!p || p.no == null || !Array.isArray(p.kose)) continue;
      const k = [];
      let tamam = p.kose.length >= 3;
      for (const r of p.kose) {
        const n = no(r, "Panel " + p.no + " köşesi");
        if (n == null) { tamam = false; break; }
        try { DCz.dugumAl(n); } catch (e) { uy.push("Panel " + p.no + ": " + e.message); tamam = false; break; }
        k.push(n);
      }
      if (!tamam) continue;
      for (const n of k) kul.set(n, (kul.get(n) || 0) + 1);
      pan.push({ p: p, k: k });
    }
    // açık mesnet kayıtları (motor _mesnetleri_oku: aynı düğümde VEYA; hepsi serbestse yok sayılır)
    const mes = new Map();
    for (const s of liste(g, "mesnetler")) {
      if (!s) continue;
      const n = no(s.dugum, "Mesnet");
      if (n == null) continue;
      try { DCz.dugumAl(n); } catch (e) { uy.push("Mesnet: " + e.message); continue; }
      let m = 0;
      MESNET_SIRASI.forEach(function (a, i) { if (s[a]) m |= 1 << i; });
      const yay = ["kx", "ky", "kz", "krx", "kry", "krz", "k"].some(function (a) { return +s[a] > 0; }) || !!s.yay;
      const o = mes.get(n);
      if (o) { o.maske |= m; o.yay = o.yay || yay; continue; }
      mes.set(n, { maske: m, yay: yay, kayit: s });
    }
    // düğüm kayıtları (bağlantısız olanlar da sahnede)
    for (const n of DCz.kayit.keys()) { try { DCz.dugumAl(n); } catch (e) { uy.push(e.message); } }
    // seviyeler
    let S0 = null;
    try { S0 = DCz.sistemler()[0]; } catch (e) { S0 = null; }
    const seviyeler = (S0 ? S0.l.z : []).map(function (a) { return { ad: String(a.ad), z: +a.konum, kat: a.kat != null ? +a.kat : -1 }; })
      .sort(function (a, b) { return a.z - b.z; });
    const katlar = seviyeler.filter(function (s) { return s.kat >= 0; }).map(function (s) { return { kat: s.kat, z: s.z, ad: s.ad }; });
    // temel kotu (Is.temelKotu): en küçük numaralı katın kotu; kat yoksa en alt GLOBAL Z aksı
    let z0 = null;
    if (DCz.izg && DCz.izg.katlar.size) { const k = Math.min.apply(null, [...DCz.izg.katlar.keys()]); z0 = DCz.izg.katlar.get(k); }
    else if (aksSistemiVar(g) && seviyeler.length) z0 = seviyeler[0].z;
    const temelMesnet = String((g.temeller && g.temeller.mesnet) || "ankastre").toLowerCase();
    const temelTipi = String((g.temeller && g.temeller.tip) || "tekil").trim().toLowerCase();
    // düğümler: no sıralı
    const dugumler = [...DCz.dugum.values()].sort(function (a, b) { return a.no - b.no; });
    const dDizin = new Map();
    dugumler.forEach(function (d, i) { dDizin.set(d.no, i); });
    const T = KODLAR.dugum_turu, MT = KODLAR.mesnet_turu;
    // mesnetler: açık kayıtlar + temel kuralı (C3; aks kesişimi düğümleri, en alt kat seviyesi)
    const mesnetler = [];
    for (const d of dugumler) {
      const m = mes.get(d.no);
      if (m) {
        if (!m.maske && !m.yay) continue;
        mesnetler.push({ d: dDizin.get(d.no), maske: m.maske, tur: m.yay ? MT.yay : mesnetTuru(m.maske), ortuk: false });
        continue;
      }
      if ((d.tur === T.aks_kat || d.tur === T.aks_kesisimi) && !(d.kayit && d.kayit.tur) && z0 != null && Math.abs(d.P[2] - z0) <= 1e-6 && kul.has(d.no)) {
        const maske = temelMesnet === "mafsal" ? 0x07 : temelMesnet === "elastik" ? 0x23 : 0x3F;
        mesnetler.push({ d: dDizin.get(d.no), maske: maske, tur: temelMesnet === "mafsal" ? MT.mafsal : temelMesnet === "elastik" ? MT.yay : MT.ankastre, ortuk: true });
      }
    }
    const cubuklar = cub.map(function (x) {
      return { c: x.c, i: dDizin.get(x.a), j: dDizin.get(x.b), tur: cubukAltTuru(x.c, dugumler[dDizin.get(x.a)].P, dugumler[dDizin.get(x.b)].P) };
    });
    const paneller = pan.map(function (x) { return { p: x.p, kose: x.k.map(function (n) { return dDizin.get(n); }), tur: panelAltTuru(x.p) }; });
    return { g: g, model: model, genellestirildi: gg.genellestirildi, uyarilar: uy, cozucu: DCz, dugumler: dugumler, dDizin: dDizin,
      kullanim: kul, cubuklar: cubuklar, paneller: paneller, mesnetler: mesnetler, seviyeler: seviyeler, katlar: katlar, z0: z0,
      temelTipi: temelTipi, temelMesnet: temelMesnet };
  }
  function mesnetTuru(m) {
    const MT = KODLAR.mesnet_turu;
    if (m === 0x3F) return MT.ankastre;
    if (m === 0x07) return MT.mafsal;
    if ((m & 0x04) && !(m & 0x38) && (m & 0x03) !== 0x03) return MT.kayici;
    return MT.diger;
  }
  const CUBUK_TURLERI = Object.keys(KODLAR.cubuk_turu);
  /** Çubuk alt türü: kayıttaki tur (bilinen); yoksa geometriden (düşey kolon, yatay kiriş, eğik diğer — bina_cizim cubukTuru). */
  function cubukAltTuru(c, Pi, Pj) {
    const t = String(c.tur == null ? "" : c.tur).trim().toLowerCase();
    if (t && CUBUK_TURLERI.indexOf(t) >= 0) return t;
    if (t) return "diger";
    const L = uzaklik(Pi, Pj);
    if (L < 1e-9) return "diger";
    if (Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1]) <= 1e-6 * L) return "kolon";
    if (Math.abs(Pj[2] - Pi[2]) <= 1e-6 * L) return "kiris";
    return "diger";
  }
  function panelAltTuru(p) {
    const t = String(p.tur == null ? "doseme" : p.tur).trim().toLowerCase();
    return t in KODLAR.panel_turu ? t : "diger";
  }
  function cozumAl(model, ek) { return ek && ek.cozum && ek.cozum.model === model ? ek.cozum : cozumle(model); }

  // ================================================================= KAT ÜYELİĞİ (§10.2)
  /** z'ye en yakın seviye adı. */
  function enYakinSeviye(sev, z) {
    let en = null, ed = Infinity;
    for (const s of sev) { const d = Math.abs(s.z - z); if (d < ed - 1e-12) { ed = d; en = s.ad; } }
    return en;
  }
  /** Yatay eleman kuralı: z_{k−1} + 1 mm < z ≤ z_k + 1 mm → k; üst katın üstü → üst kat; kat 0 ve altı → kat 0 (temel). */
  function katBul(katlar, z) {
    if (!katlar.length) return [];
    if (z <= katlar[0].z + TOL) return [katlar[0].kat];
    for (let i = 1; i < katlar.length; i++) if (z <= katlar[i].z + TOL) return [katlar[i].kat];
    return [katlar[katlar.length - 1].kat];
  }
  /** Kolon kuralı: alt–üst aralığının kestiği bütün katlar (z_{k−1} < z_üst ≤ z_k + 1 mm; kat aralığını aşan kolon birden çok). */
  function kolonKatlari(katlar, za, zu) {
    if (!katlar.length) return [];
    const alt = Math.min(za, zu), ust = Math.max(za, zu);
    const out = [];
    for (let i = 1; i < katlar.length; i++) {
      if (katlar[i].z > alt + TOL && katlar[i - 1].z < ust - TOL) out.push(katlar[i].kat);
    }
    if (!out.length) return katBul(katlar, ust);
    if (ust > katlar[katlar.length - 1].z + TOL && out[out.length - 1] !== katlar[katlar.length - 1].kat) out.push(katlar[katlar.length - 1].kat);
    return out;
  }
  function kolonMu(Pi, Pj) {
    const L = uzaklik(Pi, Pj);
    if (L < 1e-9) return false;
    return Math.abs(Pj[2] - Pi[2]) / L >= Math.cos(10 * D2R) - 1e-12;
  }

  /**
   * Kat ve seviye üyeliği (MIMARI §10.2; tolerans 1 mm). Surum 1 modelde genellestir görünümüne göre.
   * Düğüm: bir kat Z aksına 1 mm'den yakınsa o kat; değilse yatay eleman kuralı. Kolon (düşeyle ≤ 10°): kestiği katlar.
   * Yatay / eğik çubuk ve panel: üst ucunun (panelde en yüksek köşenin) kotuyla yatay eleman kuralı. Kat 0 temel katıdır.
   * @param {Object} model bina JSON
   * @param {{cozum?: Object}} [ek]
   * @returns {{seviyeler: Array<{ad: string, z: number, kat: number}>,
   *            dugum: Object<string, number[]>, cubuk: Object<string, number[]>, panel: Object<string, number[]>,
   *            seviye: {dugum: Object<string, string>, cubuk: Object<string, string>, panel: Object<string, string>}}}
   *   Anahtar eleman no'su (dize). Kat listesi boş = modelde kat seviyesi yok. Kat aralığını aşan kolon birden çok kat taşır.
   */
  function katUyeligi(model, ek) {
    const C = cozumAl(model, ek);
    const K = C.katlar, sev = C.seviyeler;
    const out = { seviyeler: sev.map(function (s) { return { ad: s.ad, z: s.z, kat: s.kat }; }), dugum: {}, cubuk: {}, panel: {},
      seviye: { dugum: {}, cubuk: {}, panel: {} } };
    for (const d of C.dugumler) {
      const z = d.P[2];
      let k = null;
      for (const s of K) if (Math.abs(s.z - z) <= TOL) { k = [s.kat]; break; }
      out.dugum[d.no] = k || katBul(K, z);
      const sv = enYakinSeviye(sev, z);
      if (sv != null) out.seviye.dugum[d.no] = sv;
    }
    for (const x of C.cubuklar) {
      const Pi = C.dugumler[x.i].P, Pj = C.dugumler[x.j].P;
      const zu = Math.max(Pi[2], Pj[2]);
      out.cubuk[x.c.no] = kolonMu(Pi, Pj) ? kolonKatlari(K, Pi[2], Pj[2]) : katBul(K, zu);
      const sv = enYakinSeviye(sev, zu);
      if (sv != null) out.seviye.cubuk[x.c.no] = sv;
    }
    for (const x of C.paneller) {
      let zu = -Infinity;
      for (const i of x.kose) zu = Math.max(zu, C.dugumler[i].P[2]);
      out.panel[x.p.no] = katBul(K, zu);
      const sv = enYakinSeviye(sev, zu);
      if (sv != null) out.seviye.panel[x.p.no] = sv;
    }
    return out;
  }

  // ================================================================= KULLANIM YERİ (§10.3)
  function cokgenAlani2(P) { let a = 0; for (let i = 0; i < P.length; i++) { const p = P[i], q = P[(i + 1) % P.length]; a += p[0] * q[1] - q[0] * p[1]; } return a / 2; }
  function noktaParcaUzakligi(p, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
    let t = L2 > 1e-24 ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2 : 0;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
  }
  /** Dışbükey zarf (monoton zincir; doğrusal noktalar atılır), saat yönünün tersine. */
  function disbukeyZarf(noktalar) {
    const p = noktalar.slice().sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    const tekil = [];
    for (const q of p) if (!tekil.length || Math.hypot(q[0] - tekil[tekil.length - 1][0], q[1] - tekil[tekil.length - 1][1]) > TOL_YER / 10) tekil.push(q);
    if (tekil.length < 3) return tekil;
    const cr = function (o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); };
    const alt = [], ust = [];
    for (const q of tekil) { while (alt.length >= 2 && cr(alt[alt.length - 2], alt[alt.length - 1], q) <= 1e-12) alt.pop(); alt.push(q); }
    for (let i = tekil.length - 1; i >= 0; i--) { const q = tekil[i]; while (ust.length >= 2 && cr(ust[ust.length - 2], ust[ust.length - 1], q) <= 1e-12) ust.pop(); ust.push(q); }
    alt.pop(); ust.pop();
    return alt.concat(ust);
  }
  /**
   * Bir katın plan zarfı: {parcalar: [[A, B]] (iç sol yanda), koseler: [[x, y]]}. Döşemeler varsa birleşimlerinin sınırı
   * (komşu döşemenin ters yönlü eş doğrusal kenarıyla örtülmeyen kenar parçaları), yoksa kolonların dışbükey zarfı.
   * Köşe: iç açısı < 170° olan sınır tepesi.
   */
  function zarfKur(dosemeler, kolonNoktalari) {
    const parcalar = [], koseler = [];
    const kenarlar = [];
    for (const P0 of dosemeler) {
      if (P0.length < 3) continue;
      const P = cokgenAlani2(P0) < 0 ? P0.slice().reverse() : P0;
      for (let i = 0; i < P.length; i++) {
        const a = P[i], b = P[(i + 1) % P.length], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (L > TOL_YER) kenarlar.push({ a: a, b: b, L: L, d: [(b[0] - a[0]) / L, (b[1] - a[1]) / L] });
      }
    }
    if (kenarlar.length) {
      // eş doğrusal kenar kovaları: doğrultu açısı (yönsüz) ve doğruya uzaklık
      const kova = new Map();
      const anahtar = function (e) {
        let ax = e.d[0], ay = e.d[1];
        if (ax < -1e-12 || (Math.abs(ax) <= 1e-12 && ay < 0)) { ax = -ax; ay = -ay; }
        const t = Math.round(Math.atan2(ay, ax) * 1e3), c = Math.round((-ay * e.a[0] + ax * e.a[1]) / TOL_YER);
        return [t, c];
      };
      kenarlar.forEach(function (e, i) {
        const k = anahtar(e);
        e.k = k;
        const s = k[0] + "|" + k[1];
        if (!kova.has(s)) kova.set(s, []);
        kova.get(s).push(i);
      });
      const dik = function (e, p) { return Math.abs(-e.d[1] * (p[0] - e.a[0]) + e.d[0] * (p[1] - e.a[1])); };
      kenarlar.forEach(function (e, i) {
        const ort = [];
        for (let dt = -1; dt <= 1; dt++) for (let dc = -1; dc <= 1; dc++) {
          for (const j of kova.get((e.k[0] + dt) + "|" + (e.k[1] + dc)) || []) {
            if (j === i) continue;
            const f = kenarlar[j];
            if (f.d[0] * e.d[0] + f.d[1] * e.d[1] > -0.9999) continue;     // ters yönlü değil
            if (dik(e, f.a) > TOL_YER || dik(e, f.b) > TOL_YER) continue;      // aynı doğru üstünde değil
            const ta = (f.a[0] - e.a[0]) * e.d[0] + (f.a[1] - e.a[1]) * e.d[1], tb = (f.b[0] - e.a[0]) * e.d[0] + (f.b[1] - e.a[1]) * e.d[1];
            const lo = Math.max(0, Math.min(ta, tb)), hi = Math.min(e.L, Math.max(ta, tb));
            if (hi - lo > TOL_YER) ort.push([lo, hi]);
          }
        }
        ort.sort(function (x, y) { return x[0] - y[0]; });
        let son = 0;
        const ekle = function (t0, t1) { if (t1 - t0 > TOL_YER) parcalar.push([[e.a[0] + e.d[0] * t0, e.a[1] + e.d[1] * t0], [e.a[0] + e.d[0] * t1, e.a[1] + e.d[1] * t1]]); };
        for (const o of ort) { if (o[0] > son) ekle(son, o[0]); son = Math.max(son, o[1]); }
        if (son < e.L) ekle(son, e.L);
      });
      // köşeler: bir parçanın bittiği ve diğerinin başladığı tepede sola dönüş > 10°
      const uclar = new Map();
      const tk = function (p) { return Math.round(p[0] / TOL_YER) + "," + Math.round(p[1] / TOL_YER); };
      parcalar.forEach(function (s, i) {
        for (const u of [[s[0], "bas"], [s[1], "son"]]) {
          const k = tk(u[0]);
          if (!uclar.has(k)) uclar.set(k, { p: u[0], bas: [], son: [] });
          uclar.get(k)[u[1]].push(i);
        }
      });
      for (const u of uclar.values()) {
        let kose = false;
        for (const i of u.son) for (const j of u.bas) {
          const a = parcalar[i], b = parcalar[j];
          const d1 = [a[1][0] - a[0][0], a[1][1] - a[0][1]], d2 = [b[1][0] - b[0][0], b[1][1] - b[0][1]];
          const donus = Math.atan2(d1[0] * d2[1] - d1[1] * d2[0], d1[0] * d2[0] + d1[1] * d2[1]);
          if (donus > 10 * D2R + 1e-9) kose = true;
        }
        if (kose) koseler.push(u.p);
      }
      return { parcalar: parcalar, koseler: koseler, kaynak: "doseme" };
    }
    const z = disbukeyZarf(kolonNoktalari);
    if (z.length <= 2) {
      for (const p of z) koseler.push(p);
      if (z.length === 2) parcalar.push([z[0], z[1]]);
      return { parcalar: parcalar, koseler: koseler, kaynak: "kolon" };
    }
    for (let i = 0; i < z.length; i++) {
      const o = z[(i + z.length - 1) % z.length], p = z[i], q = z[(i + 1) % z.length];
      parcalar.push([p, q]);
      const d1 = [p[0] - o[0], p[1] - o[1]], d2 = [q[0] - p[0], q[1] - p[1]];
      if (Math.atan2(d1[0] * d2[1] - d1[1] * d2[0], d1[0] * d2[0] + d1[1] * d2[1]) > 10 * D2R + 1e-9) koseler.push(p);
    }
    return { parcalar: parcalar, koseler: koseler, kaynak: "kolon" };
  }
  function zarftaMi(Z, p) { for (const s of Z.parcalar) if (noktaParcaUzakligi(p, s[0], s[1]) <= TOL_YER) return true; return false; }
  function koseMi(Z, p) { for (const q of Z.koseler) if (Math.hypot(p[0] - q[0], p[1] - q[1]) <= TOL_YER) return true; return false; }
  /** a–b doğru parçası zarf sınırı üstünde mi (iki uç ve orta nokta aynı sınır parçasında). */
  function zarfKenarindaMi(Z, a, b) {
    const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    for (const s of Z.parcalar) {
      const L = Math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]);
      if (L < 1e-12) continue;
      const ux = (s[1][0] - s[0][0]) / L, uy = (s[1][1] - s[0][1]) / L;
      const dik = function (p) { return Math.abs(-uy * (p[0] - s[0][0]) + ux * (p[1] - s[0][1])); };
      if (dik(a) <= TOL_YER && dik(b) <= TOL_YER && noktaParcaUzakligi(m, s[0], s[1]) <= TOL_YER) return true;
    }
    return false;
  }

  /**
   * Alt tür ve kullanım yeri (MIMARI §10.3; tolerans 1 cm). Kat zarfı: o kattaki döşeme panellerinin birleşimi, döşeme yoksa
   * kolonların dışbükey zarfı. Kolon: zarf köşesinde (iç açı < 170°) köşe, zarf kenarında kenar, değilse iç (üst ucunun
   * katında). Kiriş: bir ucu başka hiçbir taşıyıcıya ya da mesnede bağlı değilse konsol; zarf kenarı üstündeyse dış; değilse iç.
   * Döşeme: yalnız bir kenarı çubukla taşınıyorsa konsol; bir kenarı zarf üstündeyse kenar; değilse iç. Çapraz: plan izdüşümü
   * zarf kenarındaysa dış cephe, değilse iç. Cephe paneli: yatay normalinin baskın ekseni ve binanın ortasına göre ±x / ±y.
   * Düğüm: temel seviyesinde ya da mesnetliyse temel, bir kolonun üst ucuysa kolon üstü, değilse ara.
   * @param {Object} model
   * @param {{cozum?: Object, kat?: Object}} [ek]
   * @returns {{cubuk: Object<string, {alt_tur: string, yer: string}>, panel: Object<string, {alt_tur: string, yer: string}>,
   *            dugum: Object<string, {alt_tur: string, yer: string}>}}
   *   alt_tur: kolon | kiris | doseme | cati | cephe | capraz | makas-ust | makas-alt | makas-dikme | makas-diyagonal | asik
   *            | kren | bag | temel | mesnet | dugum | diger
   *   yer    : kolon kose|kenar|ic; kiriş dis|ic|konsol; döşeme ic|kenar|konsol; çapraz dis-cephe|ic; düğüm temel|kolon-ustu|ara;
   *            cephe +x|-x|+y|-y; sınıfsız ""
   */
  function kullanimYeri(model, ek) {
    const C = cozumAl(model, ek);
    const KU = ek && ek.kat ? ek.kat : katUyeligi(model, { cozum: C });
    const D = C.dugumler;
    const out = { cubuk: {}, panel: {}, dugum: {} };
    // komşuluk: düğüm dizini → çubuklar; mesnetli düğümler
    const komsu = new Map();
    C.cubuklar.forEach(function (x, k) {
      for (const n of [x.i, x.j]) { if (!komsu.has(n)) komsu.set(n, []); komsu.get(n).push(k); }
    });
    const mesnetli = new Set(C.mesnetler.map(function (m) { return m.d; }));
    const ciftler = new Map();
    C.cubuklar.forEach(function (x) { ciftler.set(Math.min(x.i, x.j) + "|" + Math.max(x.i, x.j), true); });
    // kat zarfları
    const sonKat = function (l) { return l && l.length ? l[l.length - 1] : null; };
    const katDoseme = new Map(), katKolon = new Map();
    C.paneller.forEach(function (x) {
      if (x.tur !== "doseme") return;
      const k = sonKat(KU.panel[x.p.no]);
      if (k == null) return;
      if (!katDoseme.has(k)) katDoseme.set(k, []);
      katDoseme.get(k).push(x.kose.map(function (i) { return D[i].P; }));
    });
    const kolonUst = new Set();
    C.cubuklar.forEach(function (x) {
      if (x.tur !== "kolon") return;
      const u = D[x.i].P[2] >= D[x.j].P[2] ? x.i : x.j;
      kolonUst.add(u);
      const k = sonKat(KU.cubuk[x.c.no]);
      if (k == null) return;
      if (!katKolon.has(k)) katKolon.set(k, []);
      katKolon.get(k).push(D[u].P);
    });
    const zarflar = new Map();
    const zarf = function (k) {
      if (k == null) return null;
      if (!zarflar.has(k)) zarflar.set(k, zarfKur(katDoseme.get(k) || [], katKolon.get(k) || []));
      return zarflar.get(k);
    };
    // bina ortası (plan; cephe yönü için)
    let mx = 0, my = 0;
    for (const d of D) { mx += d.P[0]; my += d.P[1]; }
    if (D.length) { mx /= D.length; my /= D.length; }

    C.cubuklar.forEach(function (x) {
      const Pi = D[x.i].P, Pj = D[x.j].P, k = sonKat(KU.cubuk[x.c.no]), Z = zarf(k);
      let yer = "";
      if (x.tur === "kolon") {
        const u = Pi[2] >= Pj[2] ? Pi : Pj;
        yer = !Z ? "" : koseMi(Z, u) ? "kose" : zarftaMi(Z, u) ? "kenar" : "ic";
      } else if (x.tur === "kiris") {
        const ucBos = [x.i, x.j].some(function (n) { return (komsu.get(n) || []).length <= 1 && !mesnetli.has(n); });
        yer = ucBos ? "konsol" : Z && zarfKenarindaMi(Z, Pi, Pj) ? "dis" : "ic";
      } else if (x.tur === "capraz") {
        yer = Z && zarfKenarindaMi(Z, Pi, Pj) ? "dis-cephe" : "ic";
      }
      out.cubuk[x.c.no] = { alt_tur: x.tur, yer: yer };
    });
    // döşeme kenarının çubukla taşınıp taşınmadığı: doğrudan çubuk ya da eş doğrusal çubuk zinciri
    const kenarTasinir = function (a, b) {
      if (ciftler.has(Math.min(a, b) + "|" + Math.max(a, b))) return true;
      const A = D[a].P, B = D[b].P, L = uzaklik(A, B);
      if (L < TOL) return false;
      let simdi = a, t = 0, adim = 0;
      while (simdi !== b && adim++ < 1000) {
        let ileri = null, it = t;
        for (const k of komsu.get(simdi) || []) {
          const x = C.cubuklar[k], o = x.i === simdi ? x.j : x.i, P = D[o].P;
          const v = [P[0] - A[0], P[1] - A[1], P[2] - A[2]];
          const tt = (v[0] * (B[0] - A[0]) + v[1] * (B[1] - A[1]) + v[2] * (B[2] - A[2])) / L;
          const dik = Math.sqrt(Math.max(0, v[0] * v[0] + v[1] * v[1] + v[2] * v[2] - tt * tt));
          if (dik <= TOL_YER && tt > it + TOL && tt <= L + TOL) { if (ileri == null || tt < it) { ileri = o; it = tt; } }
        }
        if (ileri == null) return false;
        simdi = ileri; t = it;
      }
      return simdi === b;
    };
    C.paneller.forEach(function (x) {
      let yer = "";
      const P = x.kose.map(function (i) { return D[i].P; });
      if (x.tur === "doseme") {
        const Z = zarf(sonKat(KU.panel[x.p.no]));
        let tasinan = 0, kenarda = false;
        for (let i = 0; i < x.kose.length; i++) {
          const a = x.kose[i], b = x.kose[(i + 1) % x.kose.length];
          if (kenarTasinir(a, b)) tasinan++;
          if (Z && zarfKenarindaMi(Z, D[a].P, D[b].P)) kenarda = true;
        }
        yer = tasinan === 1 ? "konsol" : kenarda ? "kenar" : "ic";
      } else if (x.tur === "cephe") {
        const n = newell(P);
        let cx = 0, cy = 0;
        for (const q of P) { cx += q[0]; cy += q[1]; }
        cx /= P.length; cy /= P.length;
        if (Math.abs(n[0]) >= Math.abs(n[1])) yer = cx >= mx ? "+x" : "-x";
        else yer = cy >= my ? "+y" : "-y";
      }
      out.panel[x.p.no] = { alt_tur: x.tur, yer: yer };
    });
    const z0 = C.z0;
    D.forEach(function (d, i) {
      const yer = (z0 != null && Math.abs(d.P[2] - z0) <= TOL) || mesnetli.has(i) ? "temel" : kolonUst.has(i) ? "kolon-ustu" : "ara";
      out.dugum[d.no] = { alt_tur: "dugum", yer: yer };
    });
    return out;
  }

  // ================================================================= KESİT ADI (§10.4)
  function kutuphane() {
    const IFC = bag("MatrisIFC", false);
    return IFC && IFC.PROFILLER ? IFC.PROFILLER : {};
  }
  /**
   * Kesit adı normalleştirme (MIMARI §10.4). Ortak sınama vektörleri: op4/testler/ortak/profil_adlari.json (JS, C++, Python).
   * Kütüphane: IPE / HEA / HEB (yapi_veri.PROFILLER = MatrisIFC.PROFILLER) ve motorun basit kesitleri (UPN n, L a x t,
   * L a x b x t, 2L, KUTU, BORU; MatrisIFC.basitProfil). RHS / SHS → KUTU, CHS → BORU yalnız ölçüyle.
   * @param {string} ad kullanıcının ya da IFC'nin yazdığı ad ("HE340A", "HE 340 A", "IPE300", "L100x10" …)
   * @returns {{ad: string|null, aile: string|null, durum: "tamam"|"kutuphanede_yok"|"anlasilmadi"}}
   *   ad: kütüphanedeki normal ad ("HEA 340"); aile: "HEA" | "HEB" | "IPE" | "UPN" | "L" | "KUTU" | "BORU" …
   */
  function profilAdiNormal(ad) {
    const yok = { ad: null, aile: null, durum: "anlasilmadi" };
    if (ad == null || typeof ad === "object") return yok;
    const s = String(ad).trim().replace(/ı/g, "I").replace(/i/g, "I").toUpperCase().replace(/[×*]/g, "X").replace(/,/g, ".").replace(/\s+/g, " ");
    if (!s) return yok;
    const sonuc = function (aile, normal, var_) { return var_ ? { ad: normal, aile: aile, durum: "tamam" } : { ad: null, aile: aile, durum: "kutuphanede_yok" }; };
    const K = kutuphane();
    let m = /^HE\s*-?\s*([ABM])\s*-?\s*(\d+)$/.exec(s) || null;
    let aile = null, n = null;
    if (m) { aile = "HE" + m[1]; n = +m[2]; }
    else if ((m = /^HE\s*-?\s*(\d+)\s*-?\s*([ABM])$/.exec(s))) { aile = "HE" + m[2]; n = +m[1]; }
    else if ((m = /^(IPE|IPN|HD|HL|HEAA)\s*-?\s*(\d+)$/.exec(s))) { aile = m[1]; n = +m[2]; }
    if (aile) { const normal = aile + " " + n; return sonuc(aile, normal, Object.prototype.hasOwnProperty.call(K, normal)); }
    const IFC = bag("MatrisIFC", false);
    const basit = function (aileB, normal) { return sonuc(aileB, normal, !!(IFC && IFC.basitProfil && IFC.basitProfil(normal))); };
    if ((m = /^(?:UPN|U)\s*-?\s*(\d+)$/.exec(s))) return basit("UPN", "UPN " + (+m[1]));
    const olcu = function (t) { return t.split(/\s*X\s*/).map(Number); };
    const yaz = function (l) { return l.map(function (v) { return String(+v); }).join("x"); };
    if ((m = /^(2L|L)\s*-?\s*(\d+(?:\.\d+)?(?:\s*X\s*\d+(?:\.\d+)?){1,2})\s*(?:\(?\s*S\s*=?\s*(\d+(?:\.\d+)?)\s*\)?)?$/.exec(s)) ||
        (m = /^(2L|L)\s*-?\s*(\d+\.\d+\.\d+)()$/.exec(s))) {
      let l = m[2].indexOf("X") >= 0 ? olcu(m[2]) : m[2].split(".").map(Number);
      if (l.length === 3 && l[0] === l[1]) l = [l[0], l[2]];
      const normal = m[1] + " " + yaz(l) + (m[1] === "2L" && m[3] ? " s=" + (+m[3]) : "");
      return basit(m[1], normal);
    }
    if ((m = /^(KUTU|RHS|SHS)\s*-?\s*(\d+(?:\.\d+)?(?:\s*X\s*\d+(?:\.\d+)?){1,2})$/.exec(s))) {
      let l = olcu(m[2]);
      if (l.length === 3 && l[0] === l[1]) l = [l[0], l[2]];
      return basit("KUTU", "KUTU " + yaz(l));
    }
    if ((m = /^(BORU|CHS)\s*-?\s*(\d+(?:\.\d+)?\s*X\s*\d+(?:\.\d+)?)$/.exec(s))) return basit("BORU", "BORU " + yaz(olcu(m[2])));
    if ((m = /^(HEA|HEB|HEM)$/.exec(s))) return { ad: null, aile: m[1], durum: "anlasilmadi" };
    return yok;
  }

  // ================================================================= ÖZNİTELİKLER
  function malzemeSistemi(model, ad) {
    if (ad == null || ad === "") return null;
    const k = model && model.malzemeler && model.malzemeler[ad];
    const kut = String((k && k.kutuphane) || ad).trim().toUpperCase();
    if (/^S\d/.test(kut)) return "celik";
    if (/^C\d/.test(kut)) return "betonarme";
    return null;
  }
  function serbestMetni(c, uc) {
    const l = c && c.serbest && Array.isArray(c.serbest[uc]) ? c.serbest[uc] : [];
    const s = new Set(l);
    const m = SERBESTLIKLER.filter(function (x) { return s.has(x); });
    return m.length ? m.join(",") : null;
  }
  function kesitMalzemesi(g, kesit) {
    const ks = g && g.kesitler;
    let k = ks && kesit != null ? ks[kesit] : null;
    if (k && String(k.tip || "").toLowerCase() === "vute" && !k.malzeme && ks[k.temel]) k = ks[k.temel];
    return k && k.malzeme ? String(k.malzeme) : null;
  }
  function kesitProfili(g, kesit) {
    const ks = g && g.kesitler;
    let k = ks && kesit != null ? ks[kesit] : null;
    if (k && String(k.tip || "").toLowerCase() === "vute" && ks[k.temel]) k = ks[k.temel];
    const r = profilAdiNormal(k && k.profil ? k.profil : kesit);
    return r.ad;
  }

  /**
   * Sütunlu öznitelik tablosu, Faz 1 alanları (OZNITELIK_IDLERI). C++ OznitelikTablosu'na birebir çevrilir.
   * Satırlar: çubuklar, paneller, düğümler, mesnetler (sahne sırası). Çubuk / panelde x, y, z ağırlık merkezidir.
   * @param {Object} model
   * @param {{cozum?: Object, kat?: Object, kullanim?: Object}} [ek] katUyeligi / kullanimYeri önceden hesaplandıysa
   * @returns {{satirlar: Array<{tur: string, no: number, alt?: number}>,
   *            sutunlar: Array<{id: string, tur: "sayi"|"metin"|"enum"|"bool"|"liste", birim?: string,
   *                             degerler: Array<number|string|boolean|number[]|null>}>}}
   *   Her sütunun degerler dizisi satirlar ile aynı uzunluktadır; değer yoksa null.
   */
  function oznitelikCikar(model, ek) {
    const C = cozumAl(model, ek);
    const KU = ek && ek.kat ? ek.kat : katUyeligi(model, { cozum: C });
    const KY = ek && ek.kullanim ? ek.kullanim : kullanimYeri(model, { cozum: C, kat: KU });
    const g = C.g, D = C.dugumler, T = KODLAR.dugum_turu;
    const satirlar = [];
    const s = {};
    for (const id of OZNITELIK_IDLERI) s[id] = [];
    const satir = function (tur, no, v) {
      satirlar.push({ tur: tur, no: no });
      for (const id of OZNITELIK_IDLERI) s[id].push(v[id] === undefined ? null : v[id]);
    };
    const sistemModel = g.sistem === "celik" || g.sistem === "betonarme" ? g.sistem : null;
    for (const x of C.cubuklar) {
      const c = x.c, Pi = D[x.i].P, Pj = D[x.j].P, no = +c.no;
      const L = uzaklik(Pi, Pj);
      const malz = kesitMalzemesi(g, c.kesit);
      const y = KY.cubuk[no] || {};
      satir("cubuk", no, {
        tur: "cubuk", no: no, ad: c.ad != null ? String(c.ad) : null, alt_tur: y.alt_tur || x.tur, kullanim_yeri: y.yer || null,
        kat: KU.cubuk[no] || [], seviye: KU.seviye.cubuk[no] != null ? KU.seviye.cubuk[no] : null,
        kesit: c.kesit != null ? String(c.kesit) : null, profil: c.kesit != null ? kesitProfili(g, c.kesit) : null, malzeme: malz,
        sistem: malzemeSistemi(g, malz) || sistemModel, grup: c.grup != null ? String(c.grup) : null,
        uzunluk: L, egim: Math.atan2(Pj[2] - Pi[2], Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1])) / D2R, aci: +c.aci || 0,
        serbest_i: serbestMetni(c, "i"), serbest_j: serbestMetni(c, "j"),
        serbest_dugum: D[x.i].tur === T.serbest || D[x.j].tur === T.serbest,
        x: (Pi[0] + Pj[0]) / 2, y: (Pi[1] + Pj[1]) / 2, z: (Pi[2] + Pj[2]) / 2,
      });
    }
    for (const x of C.paneller) {
      const p = x.p, no = +p.no, P = x.kose.map(function (i) { return D[i].P; });
      const n = newell(P);
      let cx = 0, cy = 0, cz = 0;
      for (const q of P) { cx += q[0]; cy += q[1]; cz += q[2]; }
      const y = KY.panel[no] || {};
      const malz = p.malzeme != null ? String(p.malzeme) : null;
      satir("panel", no, {
        tur: "panel", no: no, ad: p.ad != null ? String(p.ad) : null, alt_tur: y.alt_tur || x.tur, kullanim_yeri: y.yer || null,
        kat: KU.panel[no] || [], seviye: KU.seviye.panel[no] != null ? KU.seviye.panel[no] : null,
        malzeme: malz, sistem: malzemeSistemi(g, malz) || sistemModel,
        kalinlik: p.kalinlik != null && isFinite(+p.kalinlik) ? +p.kalinlik : null, alan: Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) / 2,
        serbest_dugum: x.kose.some(function (i) { return D[i].tur === T.serbest; }),
        x: cx / P.length, y: cy / P.length, z: cz / P.length,
      });
    }
    for (const d of D) {
      const y = KY.dugum[d.no] || {};
      satir("dugum", d.no, {
        tur: "dugum", no: d.no, ad: d.kayit && d.kayit.ad != null ? String(d.kayit.ad) : null, alt_tur: "dugum", kullanim_yeri: y.yer || null,
        kat: KU.dugum[d.no] || [], seviye: KU.seviye.dugum[d.no] != null ? KU.seviye.dugum[d.no] : null,
        serbest_dugum: d.tur === T.serbest, x: d.P[0], y: d.P[1], z: d.P[2],
      });
    }
    for (const m of C.mesnetler) {
      const d = D[m.d];
      satir("mesnet", d.no, {
        tur: "mesnet", no: d.no, alt_tur: "mesnet", kat: KU.dugum[d.no] || [], seviye: KU.seviye.dugum[d.no] != null ? KU.seviye.dugum[d.no] : null,
        x: d.P[0], y: d.P[1], z: d.P[2],
      });
    }
    return {
      satirlar: satirlar,
      sutunlar: OZNITELIK_IDLERI.map(function (id) {
        const o = { id: id, tur: OZNITELIK_TURLERI[id], degerler: s[id] };
        if (OZNITELIK_BIRIMLERI[id]) o.birim = OZNITELIK_BIRIMLERI[id];
        return o;
      }),
    };
  }

  /**
   * Öznitelik tablosunun C++ OznitelikTablosu düzeni (tipli diziler; köprü kopyasız okur): satır kimlikleri tür / alt / no
   * dizileri, sütunlar sayi (Float64Array; Bool 0/1, yoksa NaN) | kod (Uint32Array) + sozluk | liste_bas + liste_deger.
   * @param {Object} tablo oznitelikCikar çıktısı
   */
  function oznitelikKodla(tablo) {
    const n = tablo.satirlar.length;
    const tur = new Uint8Array(n), no = new Uint32Array(n), alt = new Uint16Array(n);
    tablo.satirlar.forEach(function (k, i) { tur[i] = KODLAR.eleman_turu[k.tur] || 0; no[i] = k.no >>> 0; alt[i] = k.alt || 0; });
    const sutunlar = tablo.sutunlar.map(function (c) {
      const o = { id: c.id, tur: c.tur, birim: c.birim || "" };
      if (c.tur === "sayi" || c.tur === "bool") {
        const a = new Float64Array(n);
        for (let i = 0; i < n; i++) { const v = c.degerler[i]; a[i] = v === null || v === undefined ? NaN : (typeof v === "boolean" ? (v ? 1 : 0) : +v); }
        o.sayi = a;
      } else if (c.tur === "liste") {
        const bas = new Uint32Array(n + 1), d = [];
        for (let i = 0; i < n; i++) { bas[i] = d.length; for (const v of c.degerler[i] || []) d.push(+v); }
        bas[n] = d.length;
        o.liste_bas = bas; o.liste_deger = Float64Array.from(d);
      } else {
        const sozluk = [], dizin = new Map(), kod = new Uint32Array(n);
        for (let i = 0; i < n; i++) {
          const v = c.degerler[i];
          if (v === null || v === undefined) { kod[i] = SAHNE_YOK; continue; }
          const t = String(v);
          let k = dizin.get(t);
          if (k === undefined) { k = sozluk.length; sozluk.push(t); dizin.set(t, k); }
          kod[i] = k;
        }
        o.kod = kod; o.sozluk = sozluk;
      }
      return o;
    });
    return { satir_tur: tur, satir_no: no, satir_alt: alt, sutunlar: sutunlar };
  }

  // ================================================================= SAHNE
  function kesitKaydi(g, ad) {
    const ks = (g && g.kesitler) || {};
    const k = ks[ad];
    const KT = KODLAR.kesit_turu;
    const o = { ad: String(ad), profil: "", tur: KT.bilinmiyor, malzeme: "", h: 0, b: 0, tw: 0, tf: 0, r: 0, vute: false };
    if (!k || typeof k !== "object") return o;
    let t = k;
    if (String(k.tip || "").toLowerCase() === "vute") { o.vute = true; if (ks[k.temel] && String((ks[k.temel].tip || "")).toLowerCase() !== "vute") t = ks[k.temel]; }
    o.malzeme = String(t.malzeme || k.malzeme || "");
    const tip = String(t.tip || "").toLowerCase();
    const sayi = function (v) { const x = +v; return isFinite(x) ? x : 0; };
    if (tip === "dikdortgen") { o.tur = KT.DIKDORTGEN; o.b = sayi(t.b); o.h = sayi(t.h); return o; }
    if (tip === "daire") { o.tur = KT.DAIRE; o.h = o.b = sayi(t.D != null ? t.D : t.d != null ? t.d : t.h); return o; }
    const pa = t.profil != null ? t.profil : (tip === "" || tip === "profil" ? ad : null);
    if (pa != null) {
      const n = profilAdiNormal(pa);
      o.profil = n.ad || "";
      const K = kutuphane();
      if (n.ad && K[n.ad]) { const v = K[n.ad]; o.tur = KT.I; o.h = v[0] / 1000; o.b = v[1] / 1000; o.tw = v[2] / 1000; o.tf = v[3] / 1000; o.r = v[4] / 1000; return o; }
      const IFC = bag("MatrisIFC", false);
      const bp = IFC && IFC.basitProfil ? IFC.basitProfil(n.ad || pa) : null;
      if (bp) {
        o.tur = { boru: KT.BORU, kutu: KT.KUTU, L: KT.L, "2L": KT["2L"], U: KT.UPN }[bp.tur] || KT.bilinmiyor;
        o.h = +bp.h || 0; o.b = +bp.b || 0;
        const b = bp.boyutlar || {};
        o.tw = +(b.tw || b.t || 0); o.tf = +(b.tf || b.t || 0); o.r = +(b.r || b.r_o || b.r1 || 0);
      }
      return o;
    }
    return o;
  }

  /**
   * Sahne (MIMARI §9.3 SAHNE içeriği; C++ SahneAnlik, kaynak/cekirdek/sahne.h). Tipli diziler QuickJS'ten C++'a sıfır
   * kopyayla geçer. Dizinler dugumler dizisine göredir (0 tabanlı). Akslar: her sistemin iki plan yönündeki aksları (Z aksları
   * seviyelerdedir; silindirik r çemberleri doğru parçası olmadığı için yoktur), en alt seviyede çizilir.
   * @param {Object} model
   * @param {number} sahneSurumu
   * @param {{cozum?: Object}} [ek]
   * @returns {{
   *   sahne_surumu: number, model_surumu: number, baslik: string, sistem: string, uyarilar: string[],
   *   seviyeler: Array<{ad: string, z: number, kat: number}>,
   *   akslar: Array<{kimlik: {tur: "aks", no: number, alt: number}, ad: string, sistem: string, eksen: 0|1|2,
   *                  bas: number[], son: number[], balon: number[]}>,
   *   dugumler: {no: Uint32Array, xyz: Float64Array, tur: Uint8Array, bayrak: Uint8Array},
   *   cubuklar: {no: Uint32Array, i: Uint32Array, j: Uint32Array, tur: Uint8Array, bayrak: Uint8Array,
   *              serbestlik: Uint16Array, kesit: Uint32Array, grup: Uint32Array, uretec: Uint32Array,
   *              aci: Float64Array, y_yerel: Float64Array},
   *   paneller: {no: Uint32Array, kose_bas: Uint32Array, kose_sayisi: Uint32Array, kose: Uint32Array, tur: Uint8Array,
   *              bayrak: Uint8Array, kalinlik: Float64Array},
   *   mesnetler: {dugum: Uint32Array, maske: Uint8Array, tur: Uint8Array},
   *   temeller: Array<{kimlik: Object, dugum: number, tur: number, B: number, L: number, h: number}>,
   *   kesitler: Array<{ad: string, profil: string, tur: number, malzeme: string, h: number, b: number, tw: number,
   *                    tf: number, r: number}>,
   *   gruplar: string[], malzemeler: string[]
   * }}  Yok anlamındaki dizin 0xFFFFFFFF (SAHNE_YOK).
   */
  function sahneCikar(model, sahneSurumu, ek) {
    const C = cozumAl(model, ek);
    const g = C.g, D = C.dugumler, MO = bag("ModelOps"), MA = bag("MatrisAks");
    const nd = D.length, nc = C.cubuklar.length, np = C.paneller.length, nm = C.mesnetler.length;
    // düğümler
    const dNo = new Uint32Array(nd), xyz = new Float64Array(3 * nd), dTur = new Uint8Array(nd), dBay = new Uint8Array(nd);
    const mesnetli = new Set(C.mesnetler.map(function (m) { return m.d; }));
    D.forEach(function (d, i) {
      dNo[i] = d.no; xyz[3 * i] = d.P[0]; xyz[3 * i + 1] = d.P[1]; xyz[3 * i + 2] = d.P[2]; dTur[i] = d.tur;
      let b = 0;
      if (mesnetli.has(i)) b |= KODLAR.dugum_bayraklari.mesnetli;
      if (!C.kullanim.has(d.no)) b |= KODLAR.dugum_bayraklari.baglantisiz;
      dBay[i] = b;
    });
    // kesitler, gruplar, malzemeler
    const kesitler = [], kDizin = new Map();
    const kesitEkle = function (ad) {
      const a = String(ad);
      if (kDizin.has(a)) return kDizin.get(a);
      const k = kesitKaydi(g, a);
      kDizin.set(a, kesitler.length);
      kesitler.push(k);
      return kesitler.length - 1;
    };
    for (const ad of Object.keys((g && g.kesitler) || {})) kesitEkle(ad);
    const gruplar = [], gDizin = new Map();
    const malzemeler = [], mDizin = new Set();
    const malzemeEkle = function (ad) { if (ad && !mDizin.has(ad)) { mDizin.add(ad); malzemeler.push(ad); } };
    for (const ad of Object.keys((g && g.malzemeler) || {})) malzemeEkle(ad);
    // çubuklar
    const cNo = new Uint32Array(nc), ci = new Uint32Array(nc), cj = new Uint32Array(nc), cTur = new Uint8Array(nc), cBay = new Uint8Array(nc);
    const cSer = new Uint16Array(nc), cKes = new Uint32Array(nc), cGrp = new Uint32Array(nc), cUre = new Uint32Array(nc);
    const cAci = new Float64Array(nc), cY = new Float64Array(3 * nc);
    const CB = KODLAR.cubuk_bayraklari, T = KODLAR.dugum_turu;
    C.cubuklar.forEach(function (x, k) {
      const c = x.c;
      cNo[k] = +c.no; ci[k] = x.i; cj[k] = x.j; cTur[k] = KODLAR.cubuk_turu[x.tur] || 0;
      let b = 0;
      if (c.yalniz_cekme) b |= CB.yalniz_cekme;
      if (D[x.i].tur === T.serbest || D[x.j].tur === T.serbest) b |= CB.serbest_dugume_bagli;
      let ser = 0;
      for (const uc of ["i", "j"]) {
        const l = c.serbest && Array.isArray(c.serbest[uc]) ? c.serbest[uc] : [];
        for (const s of l) { const q = SERBESTLIKLER.indexOf(s); if (q >= 0) ser |= 1 << ((uc === "j" ? 6 : 0) + q); }
      }
      cSer[k] = ser;
      if (c.kesit != null && c.kesit !== "") {
        const q = kesitEkle(c.kesit);
        cKes[k] = q;
        if (kesitler[q].vute) b |= CB.vute;
        malzemeEkle(kesitler[q].malzeme);
      } else cKes[k] = SAHNE_YOK;
      if (c.grup != null && c.grup !== "") {
        const a = String(c.grup);
        if (!gDizin.has(a)) { gDizin.set(a, gruplar.length); gruplar.push(a); }
        cGrp[k] = gDizin.get(a);
      } else cGrp[k] = SAHNE_YOK;
      const u = c.kaynak && c.kaynak.uretec != null ? +c.kaynak.uretec : 0;
      cUre[k] = u > 0 ? u : 0;
      if (u > 0) b |= CB.uretecten;
      cBay[k] = b;
      cAci[k] = +c.aci || 0;
      const e = MO.yerelEksenVektor(D[x.i].P, D[x.j].P, cAci[k]);
      if (e) { cY[3 * k] = e.y[0]; cY[3 * k + 1] = e.y[1]; cY[3 * k + 2] = e.y[2]; }
    });
    // paneller
    const pNo = new Uint32Array(np), pBas = new Uint32Array(np), pSay = new Uint32Array(np), pTur = new Uint8Array(np), pBay = new Uint8Array(np);
    const pKal = new Float64Array(np);
    let toplamKose = 0;
    for (const x of C.paneller) toplamKose += x.kose.length;
    const kose = new Uint32Array(toplamKose);
    let q = 0;
    C.paneller.forEach(function (x, k) {
      pNo[k] = +x.p.no; pBas[k] = q; pSay[k] = x.kose.length; pTur[k] = KODLAR.panel_turu[x.tur];
      for (const i of x.kose) kose[q++] = i;
      pKal[k] = isFinite(+x.p.kalinlik) ? +x.p.kalinlik : 0;
      // düzlemsellik (ModelOps panelGeometri: en büyük sapma > 5 mm)
      const P = x.kose.map(function (i) { return D[i].P; });
      const n = newell(P), A2 = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
      let sapma = 0;
      if (A2 > 1e-12) {
        let cx = 0, cy = 0, cz = 0;
        for (const p of P) { cx += p[0]; cy += p[1]; cz += p[2]; }
        cx /= P.length; cy /= P.length; cz /= P.length;
        for (const p of P) sapma = Math.max(sapma, Math.abs(((p[0] - cx) * n[0] + (p[1] - cy) * n[1] + (p[2] - cz) * n[2]) / A2));
      }
      pBay[k] = sapma > TOL_DUZLEM ? KODLAR.panel_bayraklari.duzlemsel_degil : 0;
      if (x.p.malzeme) malzemeEkle(String(x.p.malzeme));
    });
    // mesnetler, temeller
    const mD = new Uint32Array(nm), mM = new Uint8Array(nm), mT = new Uint8Array(nm);
    const temeller = [];
    const TT = KODLAR.temel_turu;
    const tem = g.temeller || {};
    const varsayilan = tem.varsayilan || {};
    const ozel = new Map();
    for (const o of Array.isArray(tem.ozel) ? tem.ozel : []) if (o && Array.isArray(o.aks)) ozel.set((o.sistem && o.sistem !== "GLOBAL" ? o.sistem + "|" : "") + o.aks.join("|"), o);
    C.mesnetler.forEach(function (m, k) {
      mD[k] = m.d; mM[k] = m.maske; mT[k] = m.tur;
      if (!m.ortuk) return;
      const d = D[m.d];
      let aks = null;
      if (d.tur === T.aks_kat) {
        const iz = C.cozucu.izg;
        if (iz) { const r = d.no - 1000 * Math.floor(d.no / 1000) - 1; const ix = Math.floor(r / 20), iy = r % 20; if (iz.xs[ix] && iz.ys[iy]) aks = iz.xs[ix].ad + "|" + iz.ys[iy].ad; }
      } else if (C.cozucu._sanalP && C.cozucu._sanalP.has(d.no)) {
        const ref = C.cozucu._sanalP.get(d.no).ref;
        aks = (ref.sistem && ref.sistem !== "GLOBAL" ? ref.sistem + "|" : "") + ref.aks.join("|");
      }
      const o = (aks && ozel.get(aks)) || {};
      const tur = C.temelTipi === "surekli" ? TT.surekli : C.temelTipi === "radye" ? TT.radye : TT.tekil;
      const sayi = function (a, b) { const v = +a; return isFinite(v) && v > 0 ? v : (isFinite(+b) && +b > 0 ? +b : 0); };
      temeller.push({ kimlik: { tur: "temel", no: d.no, alt: 0 }, dugum: m.d, tur: tur,
        B: sayi(o.B, varsayilan.B), L: sayi(o.L, varsayilan.L), h: sayi(o.h, varsayilan.h) });
    });
    // akslar
    const akslar = [];
    let z0 = C.seviyeler.length ? C.seviyeler[0].z : 0;
    if (C.z0 != null) z0 = C.z0;
    let S = [];
    try { S = MA.sistemler(g); } catch (e) { S = []; }
    S.forEach(function (s, si) {
      if (!s.global && s.gorunur === false) return;
      const yu = s.yonler[0], yv = s.yonler[1];
      const zk = s.zOrtak ? z0 : z0 - s.orijin[2];
      const kapsam = function (l) { if (!l.length) return [0, 0]; return [l[0].konum, l[l.length - 1].konum]; };
      const lu = s.l[yu] || [], lv = s.l[yv] || [];
      const cizgi = function (eksen, a, l0, l1, uYon) {
        const P = function (t) { return uYon ? MA.sistemNokta(s, a.konum, t, zk) : MA.sistemNokta(s, t, a.konum, zk); };
        const bas = P(l0), son = P(l1);
        const ilk = a.balon !== "son";
        const L = uzaklik(bas, son);
        const u = L > 1e-12 ? [(son[0] - bas[0]) / L, (son[1] - bas[1]) / L, (son[2] - bas[2]) / L] : [0, 0, 0];
        const balon = ilk ? [bas[0] - 0.5 * u[0], bas[1] - 0.5 * u[1], bas[2] - 0.5 * u[2]] : [son[0] + 0.5 * u[0], son[1] + 0.5 * u[1], son[2] + 0.5 * u[2]];
        akslar.push({ kimlik: { tur: "aks", alt: s.global ? 0 : si, no: eksen * 65536 + a._i }, ad: String(a.ad), sistem: String(s.ad), eksen: eksen,
          bas: bas, son: son, balon: balon });
      };
      if (s.tur === "silindirik") {
        const rmax = lu.length ? lu[lu.length - 1].konum : 1;
        lv.forEach(function (a) { cizgi(1, a, 0, rmax + AKS_PAYI, false); });
        return;
      }
      const ku = kapsam(lu), kv = kapsam(lv);
      lu.forEach(function (a) { cizgi(0, a, kv[0] - AKS_PAYI, kv[1] + AKS_PAYI, true); });
      lv.forEach(function (a) { cizgi(1, a, ku[0] - AKS_PAYI, ku[1] + AKS_PAYI, false); });
    });
    return {
      sahne_surumu: sahneSurumu || 0, model_surumu: surumSayi(model.surum), baslik: model.baslik != null ? String(model.baslik) : "",
      sistem: model.sistem != null ? String(model.sistem) : "celik", uyarilar: C.uyarilar.slice(),
      seviyeler: C.seviyeler.map(function (s) { return { ad: s.ad, z: s.z, kat: s.kat }; }), akslar: akslar,
      dugumler: { no: dNo, xyz: xyz, tur: dTur, bayrak: dBay },
      cubuklar: { no: cNo, i: ci, j: cj, tur: cTur, bayrak: cBay, serbestlik: cSer, kesit: cKes, grup: cGrp, uretec: cUre, aci: cAci, y_yerel: cY },
      paneller: { no: pNo, kose_bas: pBas, kose_sayisi: pSay, kose: kose, tur: pTur, bayrak: pBay, kalinlik: pKal },
      mesnetler: { dugum: mD, maske: mM, tur: mT },
      temeller: temeller,
      kesitler: kesitler.map(function (k) { return { ad: k.ad, profil: k.profil, tur: k.tur, malzeme: k.malzeme, h: k.h, b: k.b, tw: k.tw, tf: k.tf, r: k.r }; }),
      gruplar: gruplar, malzemeler: malzemeler,
    };
  }

  /**
   * İki sahne arasındaki eleman farkı (cephe IslemRaporu). Karşılaştırılan: çubuk (uç düğümleri ve konumları, tür, kesit
   * kaydı, açı, serbestlik, grup, bayrak), panel (köşeler, tür, kalınlık), düğüm (konum, tür, bayrak), mesnet (maske, tür),
   * aks (ad, uçlar), temel (tür, B, L, h). Kimlik listeleri sıralı ve tekrarsızdır.
   * @returns {{eklenen: Array, silinen: Array, degisen: Array}}
   */
  function sahneFarki(a, b) {
    const eklenen = [], silinen = [], degisen = [];
    const ayni3 = function (x, i, y, j) { return x[3 * i] === y[3 * j] && x[3 * i + 1] === y[3 * j + 1] && x[3 * i + 2] === y[3 * j + 2]; };
    const kesitAyni = function (ka, kb) {
      if (ka === SAHNE_YOK || kb === SAHNE_YOK) return ka === kb;
      const p = a.kesitler[ka], q = b.kesitler[kb];
      return p.ad === q.ad && p.profil === q.profil && p.tur === q.tur && p.malzeme === q.malzeme && p.h === q.h && p.b === q.b && p.tw === q.tw && p.tf === q.tf && p.r === q.r;
    };
    const grupAyni = function (ga, gb) { return (ga === SAHNE_YOK ? null : a.gruplar[ga]) === (gb === SAHNE_YOK ? null : b.gruplar[gb]); };
    const karsilastir = function (tur, noA, noB, ayni) {
      const m = new Map();
      for (let i = 0; i < noA.length; i++) m.set(noA[i], i);
      const gorulen = new Set();
      for (let j = 0; j < noB.length; j++) {
        const n = noB[j], i = m.get(n);
        gorulen.add(n);
        if (i === undefined) eklenen.push({ tur: tur, no: n });
        else if (!ayni(i, j)) degisen.push({ tur: tur, no: n });
      }
      for (let i = 0; i < noA.length; i++) if (!gorulen.has(noA[i])) silinen.push({ tur: tur, no: noA[i] });
    };
    const da = a.dugumler, db = b.dugumler;
    karsilastir("dugum", da.no, db.no, function (i, j) { return ayni3(da.xyz, i, db.xyz, j) && da.tur[i] === db.tur[j] && da.bayrak[i] === db.bayrak[j]; });
    const ca = a.cubuklar, cb = b.cubuklar;
    karsilastir("cubuk", ca.no, cb.no, function (i, j) {
      return da.no[ca.i[i]] === db.no[cb.i[j]] && da.no[ca.j[i]] === db.no[cb.j[j]] && ayni3(da.xyz, ca.i[i], db.xyz, cb.i[j]) &&
        ayni3(da.xyz, ca.j[i], db.xyz, cb.j[j]) && ca.tur[i] === cb.tur[j] && ca.bayrak[i] === cb.bayrak[j] && ca.serbestlik[i] === cb.serbestlik[j] &&
        ca.aci[i] === cb.aci[j] && ca.uretec[i] === cb.uretec[j] && kesitAyni(ca.kesit[i], cb.kesit[j]) && grupAyni(ca.grup[i], cb.grup[j]);
    });
    const pa = a.paneller, pb = b.paneller;
    karsilastir("panel", pa.no, pb.no, function (i, j) {
      if (pa.kose_sayisi[i] !== pb.kose_sayisi[j] || pa.tur[i] !== pb.tur[j] || pa.kalinlik[i] !== pb.kalinlik[j] || pa.bayrak[i] !== pb.bayrak[j]) return false;
      for (let k = 0; k < pa.kose_sayisi[i]; k++) {
        const x = pa.kose[pa.kose_bas[i] + k], y = pb.kose[pb.kose_bas[j] + k];
        if (da.no[x] !== db.no[y] || !ayni3(da.xyz, x, db.xyz, y)) return false;
      }
      return true;
    });
    const ma = a.mesnetler, mb = b.mesnetler;
    const mNoA = Uint32Array.from(ma.dugum, function (i) { return da.no[i]; }), mNoB = Uint32Array.from(mb.dugum, function (i) { return db.no[i]; });
    karsilastir("mesnet", mNoA, mNoB, function (i, j) { return ma.maske[i] === mb.maske[j] && ma.tur[i] === mb.tur[j]; });
    const ak = function (x) { return x.kimlik.alt * 4294967296 + x.kimlik.no; };
    const aa = new Map(a.akslar.map(function (x) { return [ak(x), x]; }));
    const bb = new Set();
    for (const x of b.akslar) {
      const k = ak(x), y = aa.get(k);
      bb.add(k);
      const id = { tur: "aks", no: x.kimlik.no, alt: x.kimlik.alt };
      if (!y) eklenen.push(id);
      else if (y.ad !== x.ad || y.sistem !== x.sistem || uzaklik(y.bas, x.bas) !== 0 || uzaklik(y.son, x.son) !== 0) degisen.push(id);
    }
    for (const x of a.akslar) if (!bb.has(ak(x))) silinen.push({ tur: "aks", no: x.kimlik.no, alt: x.kimlik.alt });
    const ta = new Map(a.temeller.map(function (t) { return [t.kimlik.no, t]; })), tb = new Set();
    for (const t of b.temeller) {
      const u = ta.get(t.kimlik.no);
      tb.add(t.kimlik.no);
      if (!u) eklenen.push({ tur: "temel", no: t.kimlik.no });
      else if (u.tur !== t.tur || u.B !== t.B || u.L !== t.L || u.h !== t.h) degisen.push({ tur: "temel", no: t.kimlik.no });
    }
    for (const t of a.temeller) if (!tb.has(t.kimlik.no)) silinen.push({ tur: "temel", no: t.kimlik.no });
    return { eklenen: kimlikSirala(eklenen), silinen: kimlikSirala(silinen), degisen: kimlikSirala(degisen) };
  }

  // ================================================================= SONUÇ EŞLEME
  /**
   * Çözüm sonucunun model elemanlarına eşlenmesi (MIMARI §4 çözüm akışı 3). C++ SonucEslemesi. Kaynak: veri.tasarim.elemanlar.
   * Genel model satırı "cubuk" alanıyla (çubuk no), aks–kat satırı {tur: kolon|kiris, no} ya da kaynak {aks_kat, no} ile genel
   * görünümdeki çubuk(lar)a eşlenir (aks–kat kirişinin her parçası aynı satırı alır); döşeme satırı panele.
   * @param {Object} model çözülen model
   * @param {Object} veri bina_coz yanıtındaki "veri" nesnesi
   * @param {{cozum?: Object}} [ek]
   * @returns {{elemanlar: Array<{kimlik: {tur: string, no: number}, dc: number, belirleyen: string, kombinasyon: string,
   *                              tasarim_satiri: number, fe_elemanlar: number[]}>, uyarilar: string[]}}
   *   elemanlar kimliğe göre sıralı; dc < 0 tasarım yok
   */
  function sonucEsle(model, veri, ek) {
    const uyarilar = [];
    const satirlar = veri && veri.tasarim && Array.isArray(veri.tasarim.elemanlar) ? veri.tasarim.elemanlar : [];
    if (!satirlar.length) return { elemanlar: [], uyarilar: veri && veri.tasarim ? [] : ["Çözüm verisinde tasarım (tasarim.elemanlar) yok."] };
    const C = cozumAl(model, ek);
    const cubukNo = new Set(), panelNo = new Set();
    const kaynakC = new Map(), kaynakP = new Map();
    for (const x of C.cubuklar) {
      cubukNo.add(+x.c.no);
      const k = x.c.kaynak;
      if (k && k.aks_kat) { const a = k.aks_kat + "|" + (+k.no); if (!kaynakC.has(a)) kaynakC.set(a, []); kaynakC.get(a).push(+x.c.no); }
    }
    for (const x of C.paneller) {
      panelNo.add(+x.p.no);
      const k = x.p.kaynak;
      if (k && k.aks_kat) { const a = k.aks_kat + "|" + (+k.no); if (!kaynakP.has(a)) kaynakP.set(a, []); kaynakP.get(a).push(+x.p.no); }
    }
    const sonuc = new Map();
    const koy = function (tur, no, r, i) {
      const k = tur + "|" + no;
      const dc = r.dc == null || !isFinite(+r.dc) ? -1 : +r.dc;
      const o = sonuc.get(k);
      if (o && o.dc >= dc) return;
      const b = r.belirleyen && typeof r.belirleyen === "object" ? r.belirleyen : {};
      sonuc.set(k, { kimlik: { tur: tur, no: no }, dc: dc, belirleyen: b.kontrol != null ? String(b.kontrol) : "",
        kombinasyon: b.kombinasyon != null ? String(b.kombinasyon) : "", tasarim_satiri: i,
        fe_elemanlar: Array.isArray(r.fe_elemanlar) ? r.fe_elemanlar.map(Number) : [] });
    };
    satirlar.forEach(function (r, i) {
      if (!r || typeof r !== "object") return;
      const ka = r.kaynak && r.kaynak.aks_kat ? r.kaynak.aks_kat + "|" + (+r.kaynak.no) : null;
      let bulundu = false;
      if (r.cubuk != null && cubukNo.has(+r.cubuk)) { koy("cubuk", +r.cubuk, r, i); bulundu = true; }
      else if (ka && (kaynakC.has(ka) || kaynakP.has(ka))) {
        for (const n of kaynakC.get(ka) || []) koy("cubuk", n, r, i);
        for (const n of kaynakP.get(ka) || []) koy("panel", n, r, i);
        bulundu = true;
      } else if ((r.tur === "kolon" || r.tur === "kiris") && r.cubuk == null && kaynakC.has(r.tur + "|" + (+r.no))) {
        for (const n of kaynakC.get(r.tur + "|" + (+r.no))) koy("cubuk", n, r, i);
        bulundu = true;
      } else if (r.tur === "doseme" && kaynakP.has("doseme|" + (+r.no))) {
        for (const n of kaynakP.get("doseme|" + (+r.no))) koy("panel", n, r, i);
        bulundu = true;
      } else if (r.tur === "panel" && panelNo.has(+r.no)) { koy("panel", +r.no, r, i); bulundu = true; }
      if (!bulundu) uyarilar.push("Tasarım satırı " + (i + 1) + " (" + (r.adres || (r.tur + " " + r.no)) + ") modelde eşlenemedi.");
    });
    return { elemanlar: kimlikSiralaE([...sonuc.values()]), uyarilar: uyarilar };
  }
  function kimlikSiralaE(l) { return l.sort(function (a, b) { return kimlikAnahtari(a.kimlik) - kimlikAnahtari(b.kimlik); }); }

  // ================================================================= BOŞ MODEL (§13.4)
  /**
   * Boş model "Adsız N" (MIMARI §13.4). Program her zaman bununla açılır.
   * @param {{baslik?: string, sistem?: "celik"|"betonarme"}} [secenek]
   * @returns {Object} bina JSON (surum 3); her çağrı yeni nesne
   */
  function bosModel(secenek) {
    const s = secenek || {};
    return {
      tur: "bina", surum: 3, baslik: s.baslik || "Adsız 1", sistem: s.sistem || "celik",
      birim: { kuvvet: "kN", uzunluk: "m" },
      akslar: { x: [], y: [], z: [{ ad: "±0.00", konum: 0, kat: 0 }] },
      katlar: [{ no: 0, ad: "±0.00", kot: 0 }],
      malzemeler: { C30: { kutuphane: "C30" }, B420C: { kutuphane: "B420C" }, S275: { kutuphane: "S275" }, S355: { kutuphane: "S355" } },
      kesitler: {}, dugumler: [], cubuklar: [], paneller: [], mesnetler: [], ek_yukler: [], uretecler: [],
      yuk_durumlari: { G: { acik: true }, Q: { acik: true } },
      deprem: { etkin: false },
      temeller: { tip: "tekil" },
    };
  }

  return {
    SURUM: SURUM, KODLAR: KODLAR, OZNITELIK_IDLERI: OZNITELIK_IDLERI, OZNITELIK_TURLERI: OZNITELIK_TURLERI,
    OZNITELIK_BIRIMLERI: OZNITELIK_BIRIMLERI, TASLAK: TASLAK, SAHNE_YOK: SAHNE_YOK, Op4Hatasi: Op4Hatasi,
    bagimliliklarKur: bagimliliklarKur, cozumle: cozumle, kimlikAnahtari: kimlikAnahtari,
    bosModel: bosModel, katUyeligi: katUyeligi, kullanimYeri: kullanimYeri, profilAdiNormal: profilAdiNormal,
    oznitelikCikar: oznitelikCikar, oznitelikKodla: oznitelikKodla, sahneCikar: sahneCikar, sahneFarki: sahneFarki, sonucEsle: sonucEsle,
  };
});
