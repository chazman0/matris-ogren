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
    const zAdTers = new Map();   // Z aksı adı → kat no'ları (zAd sırasıyla)
    for (const [kat, ad] of zAd) { if (!zAdTers.has(ad)) zAdTers.set(ad, []); zAdTers.get(ad).push(kat); }
    return { xs: xs, ys: ys, katlar: katlar, zAd: zAd, zAdTers: zAdTers,
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
    const a0 = aks[0], a1 = aks[1];
    const ix = g.ix.get(typeof a0 === "string" ? a0 : String(a0)), iy = g.iy.get(typeof a1 === "string" ? a1 : String(a1)), k = kat == null ? 1 : +kat;
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
      const katlar = g.zAdTers.get(typeof ref.z === "string" ? ref.z : String(ref.z));
      if (katlar) for (let q = 0; q < katlar.length; q++) { const n = this.izgaraNo(ref.aks, katlar[q]); if (n != null) return n; }
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
   * Modelin ortak çözümlemesi (tipli dizi düzeninde; sahne, kat, kullanım yeri ve öznitelik bunu paylaşır).
   * @param {Object} model bina JSON
   * @returns {Object} C — {model, g (genel görünüm), genellestirildi, uyarilar, cozucu,
   *   nd, dno: Uint32Array (sıralı düğüm no), xyz: Float64Array, dtur: Uint8Array, dkayit: Array, dDizin: Map(no → dizin),
   *   kul: Uint8Array (çubuk / panel kullanıyor), nc, cel: Array (çubuk kayıtları), ci, cj: Uint32Array, ctur: Uint8Array (kod),
   *   np, pel: Array, pbas, psay, pkose: Uint32Array, ptur: Uint8Array, nm, md: Uint32Array, mmaske, mtur, mortuk: Uint8Array,
   *   seviyeler: [{ad, z, kat}], katlar: [{kat, z, ad}] (z sıralı), z0, temelTipi, temelMesnet}
   */
  function cozumle(model) {
    if (!model || typeof model !== "object" || Array.isArray(model)) throw new Op4Hatasi("Model bir bina JSON nesnesi olmalı.");
    const gg = genelGorunum(model), g = gg.g;
    const uy = gg.uyarilar.slice();
    const DCz = new DugumCozucu(g);
    // çubuklar
    const cl = liste(g, "cubuklar");
    const cRec = [], cA = [], cB = [];
    for (let k = 0; k < cl.length; k++) {
      const c = cl[k];
      if (!c || c.no == null) continue;
      let a, b;
      try { a = DCz.no(c.i); } catch (e) { uy.push("Çubuk " + c.no + " i ucu: " + e.message); continue; }
      try { b = DCz.no(c.j); } catch (e) { uy.push("Çubuk " + c.no + " j ucu: " + e.message); continue; }
      try { DCz.dugumAl(a); DCz.dugumAl(b); } catch (e) { uy.push("Çubuk " + c.no + ": " + e.message); continue; }
      cRec.push(c); cA.push(a); cB.push(b);
    }
    // paneller
    const pl = liste(g, "paneller");
    const pRec = [], pNo = [], pSay = [];
    for (let k = 0; k < pl.length; k++) {
      const p = pl[k];
      if (!p || p.no == null || !Array.isArray(p.kose) || p.kose.length < 3) continue;
      const bas = pNo.length;
      let tamam = true;
      for (let q = 0; q < p.kose.length; q++) {
        let n;
        try { n = DCz.no(p.kose[q]); DCz.dugumAl(n); } catch (e) { uy.push("Panel " + p.no + " köşesi: " + e.message); tamam = false; break; }
        pNo.push(n);
      }
      if (!tamam) { pNo.length = bas; continue; }
      pRec.push(p); pSay.push(p.kose.length);
    }
    // açık mesnet kayıtları (motor _mesnetleri_oku: aynı düğümde VEYA; hepsi serbestse yok sayılır)
    const mes = new Map();
    const ml = liste(g, "mesnetler");
    for (let k = 0; k < ml.length; k++) {
      const s = ml[k];
      if (!s) continue;
      let n;
      try { n = DCz.no(s.dugum); DCz.dugumAl(n); } catch (e) { uy.push("Mesnet: " + e.message); continue; }
      let m = 0;
      for (let i = 0; i < 6; i++) if (s[MESNET_SIRASI[i]]) m |= 1 << i;
      const yay = !!s.yay || +s.kx > 0 || +s.ky > 0 || +s.kz > 0 || +s.krx > 0 || +s.kry > 0 || +s.krz > 0 || +s.k > 0;
      const o = mes.get(n);
      if (o) { o.maske |= m; o.yay = o.yay || yay; } else mes.set(n, { maske: m, yay: yay });
    }
    // düğüm kayıtları (bağlantısız olanlar da sahnede)
    for (const n of DCz.kayit.keys()) { try { DCz.dugumAl(n); } catch (e) { uy.push(e.message); } }
    // düğüm dizileri (no sıralı)
    const nd = DCz.dugum.size;
    const sirali = new Float64Array(nd);
    let q = 0;
    for (const n of DCz.dugum.keys()) sirali[q++] = n;
    sirali.sort();
    const dno = new Uint32Array(nd), xyz = new Float64Array(3 * nd), dtur = new Uint8Array(nd), dkayit = new Array(nd), dDizin = new Map();
    for (let i = 0; i < nd; i++) {
      const d = DCz.dugum.get(sirali[i]);
      dno[i] = d.no; xyz[3 * i] = d.P[0]; xyz[3 * i + 1] = d.P[1]; xyz[3 * i + 2] = d.P[2]; dtur[i] = d.tur; dkayit[i] = d.kayit;
      dDizin.set(d.no, i);
    }
    const kul = new Uint8Array(nd);
    const nc = cRec.length, ci = new Uint32Array(nc), cj = new Uint32Array(nc), ctur = new Uint8Array(nc);
    for (let k = 0; k < nc; k++) {
      const i = dDizin.get(cA[k]), j = dDizin.get(cB[k]);
      ci[k] = i; cj[k] = j; kul[i] = 1; kul[j] = 1;
      ctur[k] = cubukTurKodu(cRec[k], xyz, i, j);
    }
    const np = pRec.length, pbas = new Uint32Array(np), psay = new Uint32Array(np), pkose = new Uint32Array(pNo.length), ptur = new Uint8Array(np);
    let b = 0;
    for (let k = 0; k < np; k++) {
      pbas[k] = b; psay[k] = pSay[k];
      for (let t = 0; t < pSay[k]; t++) { const i = dDizin.get(pNo[b]); pkose[b++] = i; kul[i] = 1; }
      ptur[k] = panelTurKodu(pRec[k]);
    }
    // seviyeler ve katlar
    let S0 = null;
    try { S0 = DCz.sistemler()[0]; } catch (e) { S0 = null; }
    const seviyeler = (S0 ? S0.l.z : []).map(function (a) { return { ad: String(a.ad), z: +a.konum, kat: a.kat != null ? +a.kat : -1 }; })
      .sort(function (x, y) { return x.z - y.z; });
    const katlar = seviyeler.filter(function (s) { return s.kat >= 0; }).map(function (s) { return { kat: s.kat, z: s.z, ad: s.ad }; });
    // temel kotu (Is.temelKotu): en küçük numaralı katın kotu; kat yoksa en alt GLOBAL Z aksı
    let z0 = null;
    if (DCz.izg && DCz.izg.katlar.size) { let k0 = Infinity; for (const k of DCz.izg.katlar.keys()) if (k < k0) k0 = k; z0 = DCz.izg.katlar.get(k0); }
    else if (aksSistemiVar(g) && seviyeler.length) z0 = seviyeler[0].z;
    const temelMesnet = String((g.temeller && g.temeller.mesnet) || "ankastre").toLowerCase();
    const temelTipi = String((g.temeller && g.temeller.tip) || "tekil").trim().toLowerCase();
    // mesnetler: açık kayıtlar + temel kuralı (C3; aks kesişimi düğümleri, en alt kat seviyesi, kullanılan)
    const T = KODLAR.dugum_turu, MT = KODLAR.mesnet_turu;
    const mD = [], mM = [], mT = [], mO = [];
    const ortukMaske = temelMesnet === "mafsal" ? 0x07 : temelMesnet === "elastik" ? 0x23 : 0x3F;
    const ortukTur = temelMesnet === "mafsal" ? MT.mafsal : temelMesnet === "elastik" ? MT.yay : MT.ankastre;
    for (let i = 0; i < nd; i++) {
      const m = mes.get(dno[i]);
      if (m) {
        if (!m.maske && !m.yay) continue;
        mD.push(i); mM.push(m.maske); mT.push(m.yay ? MT.yay : mesnetTuru(m.maske)); mO.push(0);
        continue;
      }
      const t = dtur[i];
      if ((t === T.aks_kat || t === T.aks_kesisimi) && !(dkayit[i] && dkayit[i].tur) && z0 != null && Math.abs(xyz[3 * i + 2] - z0) <= 1e-6 && kul[i]) {
        mD.push(i); mM.push(ortukMaske); mT.push(ortukTur); mO.push(1);
      }
    }
    return { model: model, g: g, genellestirildi: gg.genellestirildi, uyarilar: uy, cozucu: DCz,
      nd: nd, dno: dno, xyz: xyz, dtur: dtur, dkayit: dkayit, dDizin: dDizin, kul: kul,
      nc: nc, cel: cRec, ci: ci, cj: cj, ctur: ctur, np: np, pel: pRec, pbas: pbas, psay: psay, pkose: pkose, ptur: ptur,
      nm: mD.length, md: Uint32Array.from(mD), mmaske: Uint8Array.from(mM), mtur: Uint8Array.from(mT), mortuk: Uint8Array.from(mO),
      seviyeler: seviyeler, katlar: katlar, z0: z0, temelTipi: temelTipi, temelMesnet: temelMesnet };
  }
  function mesnetTuru(m) {
    const MT = KODLAR.mesnet_turu;
    if (m === 0x3F) return MT.ankastre;
    if (m === 0x07) return MT.mafsal;
    if ((m & 0x04) && !(m & 0x38) && (m & 0x03) !== 0x03) return MT.kayici;
    return MT.diger;
  }
  const CUBUK_TURLERI = Object.keys(KODLAR.cubuk_turu);   // kod sırasıyla
  const PANEL_TURLERI = Object.keys(KODLAR.panel_turu);
  /** Çubuk alt türü kodu: kayıttaki tur (bilinen); yoksa geometriden (düşey kolon, yatay kiriş, eğik diğer — bina_cizim cubukTuru). */
  const turOnbellek = new Map();   // kayıttaki tur dizesi → kod (birkaç farklı değer)
  function cubukTurKodu(c, xyz, i, j) {
    const K = KODLAR.cubuk_turu;
    if (c.tur != null && c.tur !== "") {
      let k = turOnbellek.get(c.tur);
      if (k === undefined) {
        const t = (typeof c.tur === "string" ? c.tur : String(c.tur)).trim().toLowerCase();
        k = !t ? -1 : Object.prototype.hasOwnProperty.call(K, t) ? K[t] : K.diger;
        if (typeof c.tur === "string") turOnbellek.set(c.tur, k);
      }
      if (k >= 0) return k;
    }
    const dx = xyz[3 * j] - xyz[3 * i], dy = xyz[3 * j + 1] - xyz[3 * i + 1], dz = xyz[3 * j + 2] - xyz[3 * i + 2];
    const L = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (L < 1e-9) return K.diger;
    if (Math.hypot(dx, dy) <= 1e-6 * L) return K.kolon;
    if (Math.abs(dz) <= 1e-6 * L) return K.kiris;
    return K.diger;
  }
  const panelTurOnbellek = new Map();
  function panelTurKodu(p) {
    let k = panelTurOnbellek.get(p.tur);
    if (k === undefined) {
      const t = p.tur == null ? "doseme" : String(p.tur).trim().toLowerCase();
      k = Object.prototype.hasOwnProperty.call(KODLAR.panel_turu, t) ? KODLAR.panel_turu[t] : KODLAR.panel_turu.diger;
      if (p.tur == null || typeof p.tur === "string") panelTurOnbellek.set(p.tur, k);
    }
    return k;
  }
  function cozumAl(model, ek) { return ek && ek.cozum && ek.cozum.model === model ? ek.cozum : cozumle(model); }

  // ================================================================= KAT ÜYELİĞİ (§10.2)
  /**
   * Kat üyeliğinin iç (tipli dizi) biçimi: düğüm ve panel tek kat (dKat, pKat; −1 = kat seviyesi yok), çubuk kat listesi
   * (cBas / cDeger, CSR), seviye dizinleri (dSev, cSev, pSev; −1 = yok; seviyeler dizisine).
   */
  function katHesapla(C) {
    const K = C.katlar, sev = C.seviyeler, nK = K.length, nS = sev.length;
    const kz = new Float64Array(nK), kno = new Int32Array(nK), sz = new Float64Array(nS);
    for (let i = 0; i < nK; i++) { kz[i] = K[i].z; kno[i] = K[i].kat; }
    for (let i = 0; i < nS; i++) sz[i] = sev[i].z;
    const katBul = function (z) {       // yatay eleman kuralı
      if (!nK) return -1;
      for (let i = 0; i < nK; i++) if (z <= kz[i] + TOL) return kno[i];
      return kno[nK - 1];
    };
    const sevBul = function (z) {
      let en = -1, ed = Infinity;
      for (let i = 0; i < nS; i++) { const d = Math.abs(sz[i] - z); if (d < ed - 1e-12) { ed = d; en = i; } }
      return en;
    };
    const xyz = C.xyz, nd = C.nd, nc = C.nc, np = C.np;
    const dKat = new Int32Array(nd), dSev = new Int32Array(nd);
    for (let i = 0; i < nd; i++) {
      const z = xyz[3 * i + 2];
      let k = -2;
      for (let q = 0; q < nK; q++) if (Math.abs(kz[q] - z) <= TOL) { k = kno[q]; break; }
      dKat[i] = k === -2 ? katBul(z) : k;
      dSev[i] = sevBul(z);
    }
    const cBas = new Uint32Array(nc + 1), deger = [], cSev = new Int32Array(nc);
    const cos10 = Math.cos(10 * D2R) - 1e-12;
    for (let k = 0; k < nc; k++) {
      cBas[k] = deger.length;
      const i = C.ci[k], j = C.cj[k];
      const zi = xyz[3 * i + 2], zj = xyz[3 * j + 2];
      const dx = xyz[3 * j] - xyz[3 * i], dy = xyz[3 * j + 1] - xyz[3 * i + 1], dz = zj - zi;
      const L = Math.sqrt(dx * dx + dy * dy + dz * dz);
      const zu = zi > zj ? zi : zj;
      cSev[k] = sevBul(zu);
      if (!nK) continue;
      if (L >= 1e-9 && Math.abs(dz) / L >= cos10) {
        // kolon: alt–üst aralığının kestiği katlar
        const alt = zi < zj ? zi : zj, ust = zu, bas = deger.length;
        for (let q = 1; q < nK; q++) if (kz[q] > alt + TOL && kz[q - 1] < ust - TOL) deger.push(kno[q]);
        if (deger.length === bas) deger.push(katBul(ust));
        else if (ust > kz[nK - 1] + TOL && deger[deger.length - 1] !== kno[nK - 1]) deger.push(kno[nK - 1]);
      } else deger.push(katBul(zu));
    }
    cBas[nc] = deger.length;
    const pKat = new Int32Array(np), pSev = new Int32Array(np);
    for (let k = 0; k < np; k++) {
      let zu = -Infinity;
      const b = C.pbas[k], s = C.psay[k];
      for (let t = 0; t < s; t++) { const z = xyz[3 * C.pkose[b + t] + 2]; if (z > zu) zu = z; }
      pKat[k] = katBul(zu);
      pSev[k] = sevBul(zu);
    }
    return { dKat: dKat, dSev: dSev, cBas: cBas, cDeger: Int32Array.from(deger), cSev: cSev, pKat: pKat, pSev: pSev };
  }
  function katAl(C, ek) { return ek && ek.katIc && ek.cozum === C ? ek.katIc : katHesapla(C); }

  /**
   * Kat ve seviye üyeliği (MIMARI §10.2; tolerans 1 mm). Surum 1 modelde genellestir görünümüne göre.
   * Düğüm: bir kat Z aksına 1 mm'den yakınsa o kat; değilse yatay eleman kuralı. Kolon (düşeyle ≤ 10°): alt–üst aralığının
   * kestiği bütün katlar (z_{k−1} < z_üst ≤ z_k + 1 mm). Yatay / eğik çubuk ve panel: üst ucunun (panelde en yüksek köşenin)
   * kotuyla yatay eleman kuralı (z_{k−1} + 1 mm < z ≤ z_k + 1 mm → k; üst katın üstü → üst kat; kat 0 ve altı → kat 0, temel).
   * @param {Object} model bina JSON
   * @param {{cozum?: Object}} [ek]
   * @returns {{seviyeler: Array<{ad: string, z: number, kat: number}>,
   *            dugum: Object<string, number[]>, cubuk: Object<string, number[]>, panel: Object<string, number[]>,
   *            seviye: {dugum: Object<string, string>, cubuk: Object<string, string>, panel: Object<string, string>}}}
   *   Anahtar eleman no'su (dize). Kat listesi boş = modelde kat seviyesi yok. Kat aralığını aşan kolon birden çok kat taşır.
   */
  function katUyeligi(model, ek) {
    const C = cozumAl(model, ek), K = katAl(C, ek), sev = C.seviyeler;
    const out = { seviyeler: sev.map(function (s) { return { ad: s.ad, z: s.z, kat: s.kat }; }), dugum: {}, cubuk: {}, panel: {},
      seviye: { dugum: {}, cubuk: {}, panel: {} } };
    for (let i = 0; i < C.nd; i++) {
      out.dugum[C.dno[i]] = K.dKat[i] >= 0 ? [K.dKat[i]] : [];
      if (K.dSev[i] >= 0) out.seviye.dugum[C.dno[i]] = sev[K.dSev[i]].ad;
    }
    for (let k = 0; k < C.nc; k++) {
      const no = +C.cel[k].no;
      out.cubuk[no] = Array.from(K.cDeger.subarray(K.cBas[k], K.cBas[k + 1]));
      if (K.cSev[k] >= 0) out.seviye.cubuk[no] = sev[K.cSev[k]].ad;
    }
    for (let k = 0; k < C.np; k++) {
      const no = +C.pel[k].no;
      out.panel[no] = K.pKat[k] >= 0 ? [K.pKat[k]] : [];
      if (K.pSev[k] >= 0) out.seviye.panel[no] = sev[K.pSev[k]].ad;
    }
    return out;
  }

  // ================================================================= KULLANIM YERİ (§10.3)
  /** Kullanım yeri kodları (iç biçim; 0 = sınıfsız ""). */
  const YERLER = Object.freeze(["", "kose", "kenar", "ic", "dis", "konsol", "dis-cephe", "temel", "kolon-ustu", "ara", "+x", "-x", "+y", "-y"]);
  const Y = {};
  YERLER.forEach(function (a, i) { Y[a] = i; });

  function noktaParcaUzakligi(px, py, ax, ay, bx, by) {
    const dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy;
    let t = L2 > 1e-24 ? ((px - ax) * dx + (py - ay) * dy) / L2 : 0;
    if (t < 0) t = 0; else if (t > 1) t = 1;
    return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
  }
  /** Dışbükey zarf (monoton zincir; doğrusal noktalar atılır), saat yönünün tersine; düz [x, y, …] dizisi. */
  function disbukeyZarf(duz) {
    const p = [];
    for (let i = 0; i < duz.length; i += 2) p.push([duz[i], duz[i + 1]]);
    p.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
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
   * Kat plan zarfı: sınır parçaları (iç sol yanda) ve köşeler, ızgara dizinli (sorgu sabit zamanlı). Döşemeler varsa birleşimlerinin
   * sınırı (komşu döşemenin ters yönlü eş doğrusal kenarıyla örtülmeyen kenar parçaları), yoksa kolonların dışbükey zarfı.
   * Köşe: iç açısı < 170° olan sınır tepesi (sola dönüş > 10°).
   * @param {Array<number[]>} dosemeler her döşeme için düz [x0, y0, x1, y1, …]
   * @param {number[]} kolonlar düz [x, y, …]
   */
  function Zarf(dosemeler, kolonlar) {
    const par = [];      // düz [ax, ay, bx, by, …]
    const kose = [];     // düz [x, y, …]
    this.kaynak = dosemeler.length ? "doseme" : "kolon";
    if (dosemeler.length) {
      const ex = [], ey = [], ux = [], uy = [], el = [];
      for (const P0 of dosemeler) {
        const n = P0.length / 2;
        if (n < 3) continue;
        let a2 = 0;
        for (let i = 0; i < n; i++) { const j = (i + 1) % n; a2 += P0[2 * i] * P0[2 * j + 1] - P0[2 * j] * P0[2 * i + 1]; }
        for (let s = 0; s < n; s++) {
          const i = a2 < 0 ? n - 1 - s : s, j = a2 < 0 ? (n - 1 - s + n - 1) % n : (s + 1) % n;
          const ax = P0[2 * i], ay = P0[2 * i + 1], bx = P0[2 * j], by = P0[2 * j + 1], L = Math.hypot(bx - ax, by - ay);
          if (L <= TOL_YER) continue;
          ex.push(ax); ey.push(ay); ux.push((bx - ax) / L); uy.push((by - ay) / L); el.push(L);
        }
      }
      // tam ters eşi olan kenar (ızgaradaki komşu döşemelerin ortak kenarı) bütünüyle örtülüdür: karma tabloyla elenir; kalanlar
      // (T birleşimleri, kısmi örtüşmeler) eş doğrusal kovalarda karşılaştırılır. Geçerli (örtüşmeyen) döşemelerde tam eşli bir
      // kenar başka hiçbir kenarı örtmez.
      const ucAnahtar = function (x, y) { return Math.round(x / TOL_YER) + "," + Math.round(y / TOL_YER); };
      const yonlu = new Set(), ka = [], kb = [];
      for (let i = 0; i < el.length; i++) {
        ka.push(ucAnahtar(ex[i], ey[i])); kb.push(ucAnahtar(ex[i] + ux[i] * el[i], ey[i] + uy[i] * el[i]));
        yonlu.add(ka[i] + "|" + kb[i]);
      }
      const kalan = [];
      for (let i = 0; i < el.length; i++) if (!yonlu.has(kb[i] + "|" + ka[i])) kalan.push(i);
      // eş doğrusal kenar kovaları: yönsüz doğrultu açısı ve doğruya uzaklık (sayısal anahtar)
      const m = el.length, kova = new Map(), kt = new Float64Array(m), kc = new Float64Array(m);
      for (let q0 = 0; q0 < kalan.length; q0++) {
        const i = kalan[q0];
        let ax = ux[i], ay = uy[i];
        if (ax < -1e-12 || (Math.abs(ax) <= 1e-12 && ay < 0)) { ax = -ax; ay = -ay; }
        kt[i] = Math.round(Math.atan2(ay, ax) * 1e3);
        kc[i] = Math.round((-ay * ex[i] + ax * ey[i]) / TOL_YER);
        const a = (kt[i] + 4000) * 1e9 + kc[i] + 4e8;
        let l = kova.get(a);
        if (!l) { l = []; kova.set(a, l); }
        l.push(i);
      }
      const ort = [];
      for (let q0 = 0; q0 < kalan.length; q0++) {
        const i = kalan[q0];
        ort.length = 0;
        for (let dt = -1; dt <= 1; dt++) for (let dc = -1; dc <= 1; dc++) {
          const l = kova.get((kt[i] + dt + 4000) * 1e9 + kc[i] + dc + 4e8);
          if (!l) continue;
          for (let q = 0; q < l.length; q++) {
            const j = l[q];
            if (j === i || ux[j] * ux[i] + uy[j] * uy[i] > -0.9999) continue;   // ters yönlü değil
            const jbx = ex[j] + ux[j] * el[j], jby = ey[j] + uy[j] * el[j];
            if (Math.abs(-uy[i] * (ex[j] - ex[i]) + ux[i] * (ey[j] - ey[i])) > TOL_YER) continue;
            if (Math.abs(-uy[i] * (jbx - ex[i]) + ux[i] * (jby - ey[i])) > TOL_YER) continue;
            const ta = (ex[j] - ex[i]) * ux[i] + (ey[j] - ey[i]) * uy[i], tb = (jbx - ex[i]) * ux[i] + (jby - ey[i]) * uy[i];
            const lo = Math.max(0, Math.min(ta, tb)), hi = Math.min(el[i], Math.max(ta, tb));
            if (hi - lo > TOL_YER) ort.push(lo, hi);
          }
        }
        // örtülmeyen aralıklar
        const sirali = [];
        for (let q = 0; q < ort.length; q += 2) sirali.push([ort[q], ort[q + 1]]);
        sirali.sort(function (x, y) { return x[0] - y[0]; });
        let son = 0;
        for (const o of sirali) {
          if (o[0] - son > TOL_YER) par.push(ex[i] + ux[i] * son, ey[i] + uy[i] * son, ex[i] + ux[i] * o[0], ey[i] + uy[i] * o[0]);
          if (o[1] > son) son = o[1];
        }
        if (el[i] - son > TOL_YER) par.push(ex[i] + ux[i] * son, ey[i] + uy[i] * son, ex[i] + ux[i] * el[i], ey[i] + uy[i] * el[i]);
      }
      // köşeler: bir parçanın bittiği ve diğerinin başladığı tepede sola dönüş > 10°
      const uclar = new Map();
      const np = par.length / 4;
      for (let i = 0; i < np; i++) {
        for (let u = 0; u < 2; u++) {
          const x = par[4 * i + 2 * u], y = par[4 * i + 2 * u + 1];
          const a = (Math.round(x / TOL_YER) + 1e7) * 4e7 + Math.round(y / TOL_YER) + 1e7;
          let e = uclar.get(a);
          if (!e) { e = { x: x, y: y, bas: [], son: [] }; uclar.set(a, e); }
          (u === 0 ? e.bas : e.son).push(i);
        }
      }
      for (const e of uclar.values()) {
        let k = false;
        for (let s = 0; s < e.son.length && !k; s++) for (let b = 0; b < e.bas.length && !k; b++) {
          const i = e.son[s], j = e.bas[b];
          const d1x = par[4 * i + 2] - par[4 * i], d1y = par[4 * i + 3] - par[4 * i + 1], d2x = par[4 * j + 2] - par[4 * j], d2y = par[4 * j + 3] - par[4 * j + 1];
          if (Math.atan2(d1x * d2y - d1y * d2x, d1x * d2x + d1y * d2y) > 10 * D2R + 1e-9) k = true;
        }
        if (k) kose.push(e.x, e.y);
      }
    } else {
      const z = disbukeyZarf(kolonlar);
      if (z.length <= 2) {
        for (const p of z) kose.push(p[0], p[1]);
        if (z.length === 2) par.push(z[0][0], z[0][1], z[1][0], z[1][1]);
      } else {
        for (let i = 0; i < z.length; i++) {
          const o = z[(i + z.length - 1) % z.length], p = z[i], q = z[(i + 1) % z.length];
          par.push(p[0], p[1], q[0], q[1]);
          const d1x = p[0] - o[0], d1y = p[1] - o[1], d2x = q[0] - p[0], d2y = q[1] - p[1];
          if (Math.atan2(d1x * d2y - d1y * d2x, d1x * d2x + d1y * d2y) > 10 * D2R + 1e-9) kose.push(p[0], p[1]);
        }
      }
    }
    this.par = par; this.kose = kose;
    // ızgara dizini
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (let i = 0; i < par.length; i += 2) { if (par[i] < x0) x0 = par[i]; if (par[i] > x1) x1 = par[i]; if (par[i + 1] < y0) y0 = par[i + 1]; if (par[i + 1] > y1) y1 = par[i + 1]; }
    for (let i = 0; i < kose.length; i += 2) { if (kose[i] < x0) x0 = kose[i]; if (kose[i] > x1) x1 = kose[i]; if (kose[i + 1] < y0) y0 = kose[i + 1]; if (kose[i + 1] > y1) y1 = kose[i + 1]; }
    if (!(x0 <= x1)) { x0 = y0 = 0; x1 = y1 = 1; }
    this.x0 = x0 - 1; this.y0 = y0 - 1;
    this.h = Math.max(1, Math.max(x1 - x0, y1 - y0) / 48);
    this.pHucre = new Map(); this.kHucre = new Map();
    for (let i = 0; i < par.length / 4; i++) {
      const ax = par[4 * i], ay = par[4 * i + 1], bx = par[4 * i + 2], by = par[4 * i + 3];
      this.ekle(this.pHucre, i, Math.min(ax, bx) - TOL_YER, Math.min(ay, by) - TOL_YER, Math.max(ax, bx) + TOL_YER, Math.max(ay, by) + TOL_YER);
    }
    for (let i = 0; i < kose.length / 2; i++) this.ekle(this.kHucre, i, kose[2 * i] - TOL_YER, kose[2 * i + 1] - TOL_YER, kose[2 * i] + TOL_YER, kose[2 * i + 1] + TOL_YER);
  }
  Zarf.prototype.ekle = function (h, i, ax, ay, bx, by) {
    const c0 = Math.floor((ax - this.x0) / this.h), c1 = Math.floor((bx - this.x0) / this.h);
    const r0 = Math.floor((ay - this.y0) / this.h), r1 = Math.floor((by - this.y0) / this.h);
    for (let c = c0; c <= c1; c++) for (let r = r0; r <= r1; r++) {
      const a = (c + 65536) * 262144 + r + 65536;
      let l = h.get(a);
      if (!l) { l = []; h.set(a, l); }
      l.push(i);
    }
  };
  Zarf.prototype.hucre = function (h, x, y) {
    return h.get((Math.floor((x - this.x0) / this.h) + 65536) * 262144 + Math.floor((y - this.y0) / this.h) + 65536);
  };
  Zarf.prototype.uzerinde = function (x, y) {
    const l = this.hucre(this.pHucre, x, y), p = this.par;
    if (l) for (let q = 0; q < l.length; q++) { const i = l[q]; if (noktaParcaUzakligi(x, y, p[4 * i], p[4 * i + 1], p[4 * i + 2], p[4 * i + 3]) <= TOL_YER) return true; }
    return false;
  };
  Zarf.prototype.koseMi = function (x, y) {
    const l = this.hucre(this.kHucre, x, y), k = this.kose;
    if (l) for (let q = 0; q < l.length; q++) { const i = l[q]; if (Math.hypot(x - k[2 * i], y - k[2 * i + 1]) <= TOL_YER) return true; }
    return false;
  };
  /** a–b doğru parçası zarf sınırı üstünde mi (iki uç doğru üstünde, orta nokta aynı sınır parçasında). */
  Zarf.prototype.kenarda = function (ax, ay, bx, by) {
    const mx = (ax + bx) / 2, my = (ay + by) / 2;
    const l = this.hucre(this.pHucre, mx, my), p = this.par;
    if (!l) return false;
    for (let q = 0; q < l.length; q++) {
      const i = l[q], sx = p[4 * i], sy = p[4 * i + 1], ex = p[4 * i + 2], ey = p[4 * i + 3];
      const L = Math.hypot(ex - sx, ey - sy);
      if (L < 1e-12) continue;
      const vx = (ex - sx) / L, vy = (ey - sy) / L;
      if (Math.abs(-vy * (ax - sx) + vx * (ay - sy)) <= TOL_YER && Math.abs(-vy * (bx - sx) + vx * (by - sy)) <= TOL_YER &&
          noktaParcaUzakligi(mx, my, sx, sy, ex, ey) <= TOL_YER) return true;
    }
    return false;
  };

  /** Kullanım yerinin iç biçimi: cYer, pYer, dYer (YERLER kodları). */
  function yerHesapla(C, K) {
    const xyz = C.xyz, nd = C.nd, nc = C.nc, np = C.np, ci = C.ci, cj = C.cj;
    const CT = KODLAR.cubuk_turu, PT = KODLAR.panel_turu;
    // komşuluk (CSR): düğüm → çubuklar
    const der = new Uint32Array(nd + 1);
    for (let k = 0; k < nc; k++) { der[ci[k] + 1]++; der[cj[k] + 1]++; }
    for (let i = 0; i < nd; i++) der[i + 1] += der[i];
    const komsu = new Uint32Array(der[nd]), dolu = der.slice(0, nd);
    for (let k = 0; k < nc; k++) { komsu[dolu[ci[k]]++] = k; komsu[dolu[cj[k]]++] = k; }
    const mesnetli = new Uint8Array(nd);
    for (let m = 0; m < C.nm; m++) mesnetli[C.md[m]] = 1;
    const cift = new Set();
    for (let k = 0; k < nc; k++) { const a = ci[k] < cj[k] ? ci[k] : cj[k], b = ci[k] < cj[k] ? cj[k] : ci[k]; cift.add(a * 2097152 + b); }
    const sonKatC = function (k) { return K.cBas[k + 1] > K.cBas[k] ? K.cDeger[K.cBas[k + 1] - 1] : -1; };
    // kat zarfları (tembel)
    const katDoseme = new Map(), katKolon = new Map(), kolonUst = new Uint8Array(nd);
    for (let k = 0; k < np; k++) {
      if (C.ptur[k] !== PT.doseme || K.pKat[k] < 0) continue;
      const b = C.pbas[k], s = C.psay[k], P = new Array(2 * s);
      for (let t = 0; t < s; t++) { const i = C.pkose[b + t]; P[2 * t] = xyz[3 * i]; P[2 * t + 1] = xyz[3 * i + 1]; }
      let l = katDoseme.get(K.pKat[k]);
      if (!l) { l = []; katDoseme.set(K.pKat[k], l); }
      l.push(P);
    }
    for (let k = 0; k < nc; k++) {
      if (C.ctur[k] !== CT.kolon) continue;
      const u = xyz[3 * ci[k] + 2] >= xyz[3 * cj[k] + 2] ? ci[k] : cj[k];
      kolonUst[u] = 1;
      const kt = sonKatC(k);
      if (kt < 0) continue;
      let l = katKolon.get(kt);
      if (!l) { l = []; katKolon.set(kt, l); }
      l.push(xyz[3 * u], xyz[3 * u + 1]);
    }
    const zarflar = new Map();
    const zarf = function (k) {
      if (k < 0) return null;
      let z = zarflar.get(k);
      if (!z) { z = new Zarf(katDoseme.get(k) || [], katKolon.get(k) || []); zarflar.set(k, z); }
      return z;
    };
    let mx = 0, my = 0;
    for (let i = 0; i < nd; i++) { mx += xyz[3 * i]; my += xyz[3 * i + 1]; }
    if (nd) { mx /= nd; my /= nd; }
    // çubuklar
    const cYer = new Uint8Array(nc);
    for (let k = 0; k < nc; k++) {
      const t = C.ctur[k];
      if (t !== CT.kolon && t !== CT.kiris && t !== CT.capraz) continue;
      const i = ci[k], j = cj[k], Z = zarf(sonKatC(k));
      if (t === CT.kolon) {
        const u = xyz[3 * i + 2] >= xyz[3 * j + 2] ? i : j;
        cYer[k] = !Z ? 0 : Z.koseMi(xyz[3 * u], xyz[3 * u + 1]) ? Y.kose : Z.uzerinde(xyz[3 * u], xyz[3 * u + 1]) ? Y.kenar : Y.ic;
      } else if (t === CT.kiris) {
        const bos = (der[i + 1] - der[i] <= 1 && !mesnetli[i]) || (der[j + 1] - der[j] <= 1 && !mesnetli[j]);
        cYer[k] = bos ? Y.konsol : Z && Z.kenarda(xyz[3 * i], xyz[3 * i + 1], xyz[3 * j], xyz[3 * j + 1]) ? Y.dis : Y.ic;
      } else cYer[k] = Z && Z.kenarda(xyz[3 * i], xyz[3 * i + 1], xyz[3 * j], xyz[3 * j + 1]) ? Y["dis-cephe"] : Y.ic;
    }
    // döşeme kenarının çubukla taşınıp taşınmadığı: doğrudan çubuk ya da eş doğrusal çubuk zinciri
    const kenarTasinir = function (a, b) {
      if (cift.has((a < b ? a : b) * 2097152 + (a < b ? b : a))) return true;
      const Ax = xyz[3 * a], Ay = xyz[3 * a + 1], Az = xyz[3 * a + 2];
      const ux = xyz[3 * b] - Ax, uy = xyz[3 * b + 1] - Ay, uz = xyz[3 * b + 2] - Az, L = Math.sqrt(ux * ux + uy * uy + uz * uz);
      if (L < TOL) return false;
      let simdi = a, t = 0, adim = 0;
      while (simdi !== b && adim++ < 1000) {
        let ileri = -1, it = t;
        for (let q = der[simdi]; q < der[simdi + 1]; q++) {
          const k = komsu[q], o = ci[k] === simdi ? cj[k] : ci[k];
          const vx = xyz[3 * o] - Ax, vy = xyz[3 * o + 1] - Ay, vz = xyz[3 * o + 2] - Az;
          const tt = (vx * ux + vy * uy + vz * uz) / L;
          const dik = Math.sqrt(Math.max(0, vx * vx + vy * vy + vz * vz - tt * tt));
          if (dik <= TOL_YER && tt > t + TOL && tt <= L + TOL && (ileri < 0 || tt < it)) { ileri = o; it = tt; }
        }
        if (ileri < 0) return false;
        simdi = ileri; t = it;
      }
      return simdi === b;
    };
    const pYer = new Uint8Array(np);
    for (let k = 0; k < np; k++) {
      const b = C.pbas[k], s = C.psay[k];
      if (C.ptur[k] === PT.doseme) {
        const Z = zarf(K.pKat[k]);
        let tasinan = 0, kenarda = false;
        for (let t = 0; t < s; t++) {
          const a = C.pkose[b + t], c = C.pkose[b + (t + 1) % s];
          if (kenarTasinir(a, c)) tasinan++;
          if (!kenarda && Z && Z.kenarda(xyz[3 * a], xyz[3 * a + 1], xyz[3 * c], xyz[3 * c + 1])) kenarda = true;
        }
        pYer[k] = tasinan === 1 ? Y.konsol : kenarda ? Y.kenar : Y.ic;
      } else if (C.ptur[k] === PT.cephe) {
        let n0 = 0, n1 = 0, cx = 0, cy = 0;
        for (let t = 0; t < s; t++) {
          const a = C.pkose[b + t], c = C.pkose[b + (t + 1) % s];
          n0 += (xyz[3 * a + 1] - xyz[3 * c + 1]) * (xyz[3 * a + 2] + xyz[3 * c + 2]);
          n1 += (xyz[3 * a + 2] - xyz[3 * c + 2]) * (xyz[3 * a] + xyz[3 * c]);
          cx += xyz[3 * a]; cy += xyz[3 * a + 1];
        }
        cx /= s; cy /= s;
        pYer[k] = Math.abs(n0) >= Math.abs(n1) ? (cx >= mx ? Y["+x"] : Y["-x"]) : (cy >= my ? Y["+y"] : Y["-y"]);
      }
    }
    const dYer = new Uint8Array(nd), z0 = C.z0;
    for (let i = 0; i < nd; i++) dYer[i] = (z0 != null && Math.abs(xyz[3 * i + 2] - z0) <= TOL) || mesnetli[i] ? Y.temel : kolonUst[i] ? Y["kolon-ustu"] : Y.ara;
    return { cYer: cYer, pYer: pYer, dYer: dYer };
  }
  function yerAl(C, K, ek) { return ek && ek.yerIc && ek.cozum === C ? ek.yerIc : yerHesapla(C, K); }

  /**
   * Alt tür ve kullanım yeri (MIMARI §10.3; tolerans 1 cm). Kat zarfı: o kattaki döşeme panellerinin birleşimi, döşeme yoksa
   * kolonların dışbükey zarfı. Kolon: zarf köşesinde (iç açı < 170°) köşe, zarf kenarında kenar, değilse iç (üst ucunun
   * katında). Kiriş: bir ucu başka hiçbir taşıyıcıya ya da mesnede bağlı değilse konsol; zarf kenarı üstündeyse dış; değilse iç.
   * Döşeme: yalnız bir kenarı çubukla taşınıyorsa konsol; bir kenarı zarf üstündeyse kenar; değilse iç. Çapraz: plan izdüşümü
   * zarf kenarındaysa dış cephe, değilse iç. Cephe paneli: yatay normalinin baskın ekseni ve binanın ortasına göre ±x / ±y.
   * Düğüm: temel seviyesinde ya da mesnetliyse temel, bir kolonun üst ucuysa kolon üstü, değilse ara.
   * @param {Object} model
   * @param {{cozum?: Object}} [ek]
   * @returns {{cubuk: Object<string, {alt_tur: string, yer: string}>, panel: Object<string, {alt_tur: string, yer: string}>,
   *            dugum: Object<string, {alt_tur: string, yer: string}>}}
   *   alt_tur: kolon | kiris | doseme | cati | cephe | capraz | makas-ust | makas-alt | makas-dikme | makas-diyagonal | asik
   *            | kren | bag | temel | mesnet | dugum | diger
   *   yer    : kolon kose|kenar|ic; kiriş dis|ic|konsol; döşeme ic|kenar|konsol; çapraz dis-cephe|ic; düğüm temel|kolon-ustu|ara;
   *            cephe +x|-x|+y|-y; sınıfsız ""
   */
  function kullanimYeri(model, ek) {
    const C = cozumAl(model, ek), K = katAl(C, ek), Yi = yerAl(C, K, ek);
    const out = { cubuk: {}, panel: {}, dugum: {} };
    for (let k = 0; k < C.nc; k++) out.cubuk[C.cel[k].no] = { alt_tur: CUBUK_TURLERI[C.ctur[k]], yer: YERLER[Yi.cYer[k]] };
    for (let k = 0; k < C.np; k++) out.panel[C.pel[k].no] = { alt_tur: PANEL_TURLERI[C.ptur[k]], yer: YERLER[Yi.pYer[k]] };
    for (let i = 0; i < C.nd; i++) out.dugum[C.dno[i]] = { alt_tur: "dugum", yer: YERLER[Yi.dYer[i]] };
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
  function kesitBilgisi(g, kesit, onbellek) {
    let o = onbellek.get(kesit);
    if (o) return o;
    const ks = g && g.kesitler;
    let k = ks ? ks[kesit] : null;
    if (k && String(k.tip || "").toLowerCase() === "vute" && ks[k.temel]) k = ks[k.temel];
    const malzeme = k && k.malzeme ? String(k.malzeme) : null;
    o = { profil: profilAdiNormal(k && k.profil ? k.profil : kesit).ad, malzeme: malzeme, sistem: malzemeSistemi(g, malzeme) };
    onbellek.set(kesit, o);
    return o;
  }
  /** Metin / enum sütunu kurucusu (sözlüklü). */
  function SozlukSutunu(n) { this.kod = new Uint32Array(n).fill(SAHNE_YOK); this.sozluk = []; this.dizin = new Map(); }
  SozlukSutunu.prototype.koy = function (satir, v) {
    if (v === null || v === undefined) return;
    const t = typeof v === "string" ? v : String(v);
    let k = this.dizin.get(t);
    if (k === undefined) { k = this.sozluk.length; this.sozluk.push(t); this.dizin.set(t, k); }
    this.kod[satir] = k;
  };
  const SERBEST_METIN = (function () {
    const l = [];
    for (let m = 0; m < 64; m++) {
      const s = [];
      for (let q = 0; q < 6; q++) if (m & (1 << q)) s.push(SERBESTLIKLER[q]);
      l.push(s.length ? s.join(",") : null);
    }
    return l;
  })();
  function serbestMaskesi(c) {
    let ser = 0;
    if (c && c.serbest) {
      for (let u = 0; u < 2; u++) {
        const l = c.serbest[u ? "j" : "i"];
        if (!Array.isArray(l)) continue;
        for (let q = 0; q < l.length; q++) { const b = SERBESTLIKLER.indexOf(l[q]); if (b >= 0) ser |= 1 << ((u ? 6 : 0) + b); }
      }
    }
    return ser;
  }

  /**
   * Öznitelik tablosunun C++ OznitelikTablosu düzeni (tipli diziler; köprü kopyasız okur). Satırlar: çubuklar, paneller,
   * düğümler, mesnetler (sahne sırası). Sütunlar OZNITELIK_IDLERI sırasıyla: sayi / bool → sayi (Float64Array; Bool 0/1, yoksa
   * NaN); metin / enum → kod (Uint32Array; yoksa 0xFFFFFFFF) + sozluk; liste → liste_bas (n + 1) + liste_deger.
   * @returns {{satir_tur: Uint8Array, satir_no: Uint32Array, satir_alt: Uint16Array, sutunlar: Array<{id, tur, birim, sayi?,
   *            kod?, sozluk?, liste_bas?, liste_deger?}>}}
   */
  function oznitelikHesapla(C, K, Yi) {
    const g = C.g, xyz = C.xyz, nd = C.nd, nc = C.nc, np = C.np, nm = C.nm;
    const n = nc + np + nd + nm;
    const ET = KODLAR.eleman_turu, T = KODLAR.dugum_turu;
    const satir_tur = new Uint8Array(n), satir_no = new Uint32Array(n), satir_alt = new Uint16Array(n);
    const sayi = function () { return new Float64Array(n).fill(NaN); };
    const s = {
      tur: new SozlukSutunu(n), no: sayi(), ad: new SozlukSutunu(n), alt_tur: new SozlukSutunu(n), kullanim_yeri: new SozlukSutunu(n),
      seviye: new SozlukSutunu(n), kesit: new SozlukSutunu(n), profil: new SozlukSutunu(n), malzeme: new SozlukSutunu(n),
      sistem: new SozlukSutunu(n), grup: new SozlukSutunu(n), uzunluk: sayi(), egim: sayi(), aci: sayi(), kalinlik: sayi(), alan: sayi(),
      serbest_i: new SozlukSutunu(n), serbest_j: new SozlukSutunu(n), serbest_dugum: sayi(), x: sayi(), y: sayi(), z: sayi(),
    };
    for (const a of ["cubuk", "panel", "dugum", "mesnet"]) s.tur.koy(0, a);          // sabit sözlük sırası
    s.tur.kod[0] = SAHNE_YOK;
    const katBas = new Uint32Array(n + 1), katDeger = [];
    const sistemModel = g.sistem === "celik" || g.sistem === "betonarme" ? g.sistem : null;
    const kesitler = new Map();
    let r = 0;
    for (let k = 0; k < nc; k++, r++) {
      const c = C.cel[k], i = C.ci[k], j = C.cj[k];
      satir_tur[r] = ET.cubuk; satir_no[r] = +c.no;
      s.tur.kod[r] = 0; s.no[r] = +c.no;
      if (c.ad != null) s.ad.koy(r, c.ad);
      s.alt_tur.koy(r, CUBUK_TURLERI[C.ctur[k]]);
      if (Yi.cYer[k]) s.kullanim_yeri.koy(r, YERLER[Yi.cYer[k]]);
      katBas[r] = katDeger.length;
      for (let q = K.cBas[k]; q < K.cBas[k + 1]; q++) katDeger.push(K.cDeger[q]);
      if (K.cSev[k] >= 0) s.seviye.koy(r, C.seviyeler[K.cSev[k]].ad);
      if (c.kesit != null) {
        const kb = kesitBilgisi(g, c.kesit, kesitler);
        s.kesit.koy(r, c.kesit); s.profil.koy(r, kb.profil); s.malzeme.koy(r, kb.malzeme); s.sistem.koy(r, kb.sistem || sistemModel);
      } else s.sistem.koy(r, sistemModel);
      if (c.grup != null) s.grup.koy(r, c.grup);
      const xi = xyz[3 * i], yi = xyz[3 * i + 1], zi = xyz[3 * i + 2], xj = xyz[3 * j], yj = xyz[3 * j + 1], zj = xyz[3 * j + 2];
      const dx = xj - xi, dy = yj - yi, dz = zj - zi;
      s.uzunluk[r] = Math.sqrt(dx * dx + dy * dy + dz * dz);
      s.egim[r] = Math.atan2(dz, Math.hypot(dx, dy)) / D2R;
      s.aci[r] = +c.aci || 0;
      const ser = serbestMaskesi(c);
      s.serbest_i.koy(r, SERBEST_METIN[ser & 63]); s.serbest_j.koy(r, SERBEST_METIN[(ser >> 6) & 63]);
      s.serbest_dugum[r] = C.dtur[i] === T.serbest || C.dtur[j] === T.serbest ? 1 : 0;
      s.x[r] = (xi + xj) / 2; s.y[r] = (yi + yj) / 2; s.z[r] = (zi + zj) / 2;
    }
    for (let k = 0; k < np; k++, r++) {
      const p = C.pel[k], b = C.pbas[k], ns = C.psay[k];
      satir_tur[r] = ET.panel; satir_no[r] = +p.no;
      s.tur.kod[r] = 1; s.no[r] = +p.no;
      if (p.ad != null) s.ad.koy(r, p.ad);
      s.alt_tur.koy(r, PANEL_TURLERI[C.ptur[k]]);
      if (Yi.pYer[k]) s.kullanim_yeri.koy(r, YERLER[Yi.pYer[k]]);
      katBas[r] = katDeger.length;
      if (K.pKat[k] >= 0) katDeger.push(K.pKat[k]);
      if (K.pSev[k] >= 0) s.seviye.koy(r, C.seviyeler[K.pSev[k]].ad);
      const malz = p.malzeme != null ? String(p.malzeme) : null;
      s.malzeme.koy(r, malz);
      s.sistem.koy(r, malzemeSistemi(g, malz) || sistemModel);
      if (p.kalinlik != null && isFinite(+p.kalinlik)) s.kalinlik[r] = +p.kalinlik;
      let n0 = 0, n1 = 0, n2 = 0, cx = 0, cy = 0, cz = 0, serbest = 0;
      for (let t = 0; t < ns; t++) {
        const a = C.pkose[b + t], e = C.pkose[b + (t + 1) % ns];
        const ax = xyz[3 * a], ay = xyz[3 * a + 1], az = xyz[3 * a + 2], ex = xyz[3 * e], ey = xyz[3 * e + 1], ez = xyz[3 * e + 2];
        n0 += (ay - ey) * (az + ez); n1 += (az - ez) * (ax + ex); n2 += (ax - ex) * (ay + ey);
        cx += ax; cy += ay; cz += az;
        if (C.dtur[a] === T.serbest) serbest = 1;
      }
      s.alan[r] = Math.sqrt(n0 * n0 + n1 * n1 + n2 * n2) / 2;
      s.serbest_dugum[r] = serbest;
      s.x[r] = cx / ns; s.y[r] = cy / ns; s.z[r] = cz / ns;
    }
    for (let i = 0; i < nd; i++, r++) {
      const d = C.dkayit[i];
      satir_tur[r] = ET.dugum; satir_no[r] = C.dno[i];
      s.tur.kod[r] = 2; s.no[r] = C.dno[i];
      if (d && d.ad != null) s.ad.koy(r, d.ad);
      s.alt_tur.koy(r, "dugum");
      if (Yi.dYer[i]) s.kullanim_yeri.koy(r, YERLER[Yi.dYer[i]]);
      katBas[r] = katDeger.length;
      if (K.dKat[i] >= 0) katDeger.push(K.dKat[i]);
      if (K.dSev[i] >= 0) s.seviye.koy(r, C.seviyeler[K.dSev[i]].ad);
      s.serbest_dugum[r] = C.dtur[i] === T.serbest ? 1 : 0;
      s.x[r] = xyz[3 * i]; s.y[r] = xyz[3 * i + 1]; s.z[r] = xyz[3 * i + 2];
    }
    for (let m = 0; m < nm; m++, r++) {
      const i = C.md[m];
      satir_tur[r] = ET.mesnet; satir_no[r] = C.dno[i];
      s.tur.kod[r] = 3; s.no[r] = C.dno[i];
      s.alt_tur.koy(r, "mesnet");
      katBas[r] = katDeger.length;
      if (K.dKat[i] >= 0) katDeger.push(K.dKat[i]);
      if (K.dSev[i] >= 0) s.seviye.koy(r, C.seviyeler[K.dSev[i]].ad);
      s.x[r] = xyz[3 * i]; s.y[r] = xyz[3 * i + 1]; s.z[r] = xyz[3 * i + 2];
    }
    katBas[n] = katDeger.length;
    return {
      satir_tur: satir_tur, satir_no: satir_no, satir_alt: satir_alt,
      sutunlar: OZNITELIK_IDLERI.map(function (id) {
        const tur = OZNITELIK_TURLERI[id], o = { id: id, tur: tur, birim: OZNITELIK_BIRIMLERI[id] || "" };
        if (tur === "liste") { o.liste_bas = katBas; o.liste_deger = Float64Array.from(katDeger); }
        else if (tur === "sayi" || tur === "bool") o.sayi = s[id];
        else { o.kod = s[id].kod; o.sozluk = s[id].sozluk; }
        return o;
      }),
    };
  }
  /** Kodlu tablodan genel biçim (oznitelikCikar dönüşü). */
  function oznitelikCoz(t) {
    const n = t.satir_no.length, turAdi = Object.keys(KODLAR.eleman_turu);
    const satirlar = new Array(n);
    for (let i = 0; i < n; i++) satirlar[i] = { tur: turAdi[t.satir_tur[i]], no: t.satir_no[i] };
    return {
      satirlar: satirlar,
      sutunlar: t.sutunlar.map(function (c) {
        const d = new Array(n);
        for (let i = 0; i < n; i++) {
          if (c.tur === "sayi") d[i] = Number.isNaN(c.sayi[i]) ? null : c.sayi[i];
          else if (c.tur === "bool") d[i] = Number.isNaN(c.sayi[i]) ? null : c.sayi[i] !== 0;
          else if (c.tur === "liste") d[i] = Array.from(c.liste_deger.subarray(c.liste_bas[i], c.liste_bas[i + 1]));
          else d[i] = c.kod[i] === SAHNE_YOK ? null : c.sozluk[c.kod[i]];
        }
        const o = { id: c.id, tur: c.tur, degerler: d };
        if (c.birim) o.birim = c.birim;
        return o;
      }),
    };
  }

  /**
   * Sütunlu öznitelik tablosu, Faz 1 alanları (OZNITELIK_IDLERI). C++ OznitelikTablosu'na birebir çevrilir.
   * Satırlar: çubuklar, paneller, düğümler, mesnetler (sahne sırası). Çubuk / panelde x, y, z ağırlık merkezidir (panelde
   * köşelerin ortalaması); egim yatayla işaretli açı (j ucu yüksekse +), alan Newell normalinin yarısı.
   * @param {Object} model
   * @param {{cozum?: Object}} [ek]
   * @returns {{satirlar: Array<{tur: string, no: number, alt?: number}>,
   *            sutunlar: Array<{id: string, tur: "sayi"|"metin"|"enum"|"bool"|"liste", birim?: string,
   *                             degerler: Array<number|string|boolean|number[]|null>}>}}
   *   Her sütunun degerler dizisi satirlar ile aynı uzunluktadır; değer yoksa null.
   */
  function oznitelikCikar(model, ek) {
    const C = cozumAl(model, ek), K = katAl(C, ek);
    return oznitelikCoz(oznitelikHesapla(C, K, yerAl(C, K, ek)));
  }

  /**
   * Genel biçimli tablonun (oznitelikCikar) kodlu düzene çevrilmesi (oznitelikHesapla ile aynı biçim).
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
        const sz = new SozlukSutunu(n);
        for (let i = 0; i < n; i++) sz.koy(i, c.degerler[i]);
        o.kod = sz.kod; o.sozluk = sz.sozluk;
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
   * seviyelerdedir; silindirik r çemberleri doğru parçası olmadığı için yoktur), en alt seviyede çizilir. y_yerel ModelOps
   * yerelEksenVektor ile aynı hesaptır (motor kuralı).
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
   * }}  Yok anlamındaki dizin 0xFFFFFFFF (SAHNE_YOK). Tipli diziler çözümlemeyle paylaşılır: değiştirilmemelidir.
   */
  function sahneCikar(model, sahneSurumu, ek) {
    const C = cozumAl(model, ek);
    const g = C.g, xyz = C.xyz, MA = bag("MatrisAks");
    const nd = C.nd, nc = C.nc, np = C.np, nm = C.nm;
    const T = KODLAR.dugum_turu, CB = KODLAR.cubuk_bayraklari;
    // düğüm bayrakları
    const dBay = new Uint8Array(nd);
    for (let i = 0; i < nd; i++) if (!C.kul[i]) dBay[i] = KODLAR.dugum_bayraklari.baglantisiz;
    for (let m = 0; m < nm; m++) dBay[C.md[m]] |= KODLAR.dugum_bayraklari.mesnetli;
    // kesitler, gruplar, malzemeler
    const kesitler = [], kDizin = new Map();
    const kesitEkle = function (ad) {
      const a = typeof ad === "string" ? ad : String(ad);
      let q = kDizin.get(a);
      if (q === undefined) { q = kesitler.length; kDizin.set(a, q); kesitler.push(kesitKaydi(g, a)); }
      return q;
    };
    for (const ad of Object.keys((g && g.kesitler) || {})) kesitEkle(ad);
    const gruplar = [], gDizin = new Map();
    const malzemeler = [], mVar = new Set();
    const malzemeEkle = function (ad) { if (ad && !mVar.has(ad)) { mVar.add(ad); malzemeler.push(ad); } };
    for (const ad of Object.keys((g && g.malzemeler) || {})) malzemeEkle(ad);
    // çubuklar
    const cNo = new Uint32Array(nc), cBay = new Uint8Array(nc), cSer = new Uint16Array(nc), cKes = new Uint32Array(nc);
    const cGrp = new Uint32Array(nc), cUre = new Uint32Array(nc), cAci = new Float64Array(nc), cY = new Float64Array(3 * nc);
    for (let k = 0; k < nc; k++) {
      const c = C.cel[k], i = C.ci[k], j = C.cj[k];
      cNo[k] = +c.no;
      let b = 0;
      if (c.yalniz_cekme) b |= CB.yalniz_cekme;
      if (C.dtur[i] === T.serbest || C.dtur[j] === T.serbest) b |= CB.serbest_dugume_bagli;
      cSer[k] = serbestMaskesi(c);
      if (c.kesit != null && c.kesit !== "") {
        const q = kesitEkle(c.kesit);
        cKes[k] = q;
        if (kesitler[q].vute) b |= CB.vute;
        malzemeEkle(kesitler[q].malzeme);
      } else cKes[k] = SAHNE_YOK;
      if (c.grup != null && c.grup !== "") {
        const a = String(c.grup);
        let q = gDizin.get(a);
        if (q === undefined) { q = gruplar.length; gDizin.set(a, q); gruplar.push(a); }
        cGrp[k] = q;
      } else cGrp[k] = SAHNE_YOK;
      const u = c.kaynak && c.kaynak.uretec != null ? +c.kaynak.uretec : 0;
      if (u > 0) { cUre[k] = u; b |= CB.uretecten; }
      cBay[k] = b;
      const aci = +c.aci || 0;
      cAci[k] = aci;
      // ModelOps.yerelEksenVektor ile aynı işlem sırası (bit düzeyinde aynı sonuç)
      const d0 = xyz[3 * j] - xyz[3 * i], d1 = xyz[3 * j + 1] - xyz[3 * i + 1], d2 = xyz[3 * j + 2] - xyz[3 * i + 2];
      const L = Math.sqrt(d0 * d0 + d1 * d1 + d2 * d2);
      if (L < 1e-12) continue;
      const s = 1 / L, x0 = d0 * s, x1 = d1 * s, x2 = d2 * s, D = Math.hypot(x0, x1);
      let y0, y1, y2, z0, z1, z2;
      if (D < 1e-9) { const cy = x2 > 0 ? 1 : -1; y0 = -cy; y1 = 0; y2 = 0; z0 = 0; z1 = -1; z2 = 0; }
      else { y0 = -x0 * x2 / D; y1 = -x1 * x2 / D; y2 = D; z0 = x1 / D; z1 = -x0 / D; z2 = 0; }
      const a = aci * D2R;
      if (a) { const co = Math.cos(a), si = Math.sin(a); cY[3 * k] = y0 * co + z0 * si; cY[3 * k + 1] = y1 * co + z1 * si; cY[3 * k + 2] = y2 * co + z2 * si; }
      else { cY[3 * k] = y0; cY[3 * k + 1] = y1; cY[3 * k + 2] = y2; }
    }
    // paneller
    const pNo = new Uint32Array(np), pBay = new Uint8Array(np), pKal = new Float64Array(np);
    for (let k = 0; k < np; k++) {
      const p = C.pel[k], b = C.pbas[k], ns = C.psay[k];
      pNo[k] = +p.no;
      pKal[k] = isFinite(+p.kalinlik) ? +p.kalinlik : 0;
      // düzlemsellik (ModelOps panelGeometri: en büyük sapma > 5 mm)
      let n0 = 0, n1 = 0, n2 = 0, cx = 0, cy = 0, cz = 0;
      for (let t = 0; t < ns; t++) {
        const a = C.pkose[b + t], e = C.pkose[b + (t + 1) % ns];
        n0 += (xyz[3 * a + 1] - xyz[3 * e + 1]) * (xyz[3 * a + 2] + xyz[3 * e + 2]);
        n1 += (xyz[3 * a + 2] - xyz[3 * e + 2]) * (xyz[3 * a] + xyz[3 * e]);
        n2 += (xyz[3 * a] - xyz[3 * e]) * (xyz[3 * a + 1] + xyz[3 * e + 1]);
        cx += xyz[3 * a]; cy += xyz[3 * a + 1]; cz += xyz[3 * a + 2];
      }
      const A2 = Math.sqrt(n0 * n0 + n1 * n1 + n2 * n2);
      let sapma = 0;
      if (A2 > 1e-12) {
        cx /= ns; cy /= ns; cz /= ns;
        for (let t = 0; t < ns; t++) {
          const a = C.pkose[b + t];
          const v = Math.abs(((xyz[3 * a] - cx) * n0 + (xyz[3 * a + 1] - cy) * n1 + (xyz[3 * a + 2] - cz) * n2) / A2);
          if (v > sapma) sapma = v;
        }
      }
      pBay[k] = sapma > TOL_DUZLEM ? KODLAR.panel_bayraklari.duzlemsel_degil : 0;
      if (p.malzeme) malzemeEkle(String(p.malzeme));
    }
    // temeller (temel kuralıyla mesnetlenen aks kesişimi düğümleri)
    const temeller = [];
    const TT = KODLAR.temel_turu;
    const tem = g.temeller || {};
    const varsayilan = tem.varsayilan || {};
    const ozel = new Map();
    for (const o of Array.isArray(tem.ozel) ? tem.ozel : []) if (o && Array.isArray(o.aks)) ozel.set((o.sistem && o.sistem !== "GLOBAL" ? o.sistem + "|" : "") + o.aks.join("|"), o);
    const temelTur = C.temelTipi === "surekli" ? TT.surekli : C.temelTipi === "radye" ? TT.radye : TT.tekil;
    const olcu = function (a, b) { const v = +a; return isFinite(v) && v > 0 ? v : (isFinite(+b) && +b > 0 ? +b : 0); };
    for (let m = 0; m < nm; m++) {
      if (!C.mortuk[m]) continue;
      const i = C.md[m], no = C.dno[i];
      let aks = null;
      if (C.dtur[i] === T.aks_kat) {
        const iz = C.cozucu.izg;
        if (iz) { const r = no - 1000 * Math.floor(no / 1000) - 1; const ix = Math.floor(r / 20), iy = r % 20; if (iz.xs[ix] && iz.ys[iy]) aks = iz.xs[ix].ad + "|" + iz.ys[iy].ad; }
      } else if (C.cozucu._sanalP && C.cozucu._sanalP.has(no)) {
        const ref = C.cozucu._sanalP.get(no).ref;
        aks = (ref.sistem && ref.sistem !== "GLOBAL" ? ref.sistem + "|" : "") + ref.aks.join("|");
      }
      const o = (aks && ozel.get(aks)) || {};
      temeller.push({ kimlik: { tur: "temel", no: no, alt: 0 }, dugum: i, tur: temelTur,
        B: olcu(o.B, varsayilan.B), L: olcu(o.L, varsayilan.L), h: olcu(o.h, varsayilan.h) });
    }
    // akslar
    const akslar = [];
    const z0 = C.z0 != null ? C.z0 : (C.seviyeler.length ? C.seviyeler[0].z : 0);
    let S = [];
    try { S = MA.sistemler(g); } catch (e) { S = []; }
    S.forEach(function (s, si) {
      if (!s.global && s.gorunur === false) return;
      const yu = s.yonler[0], yv = s.yonler[1];
      const zk = s.zOrtak ? z0 : z0 - s.orijin[2];
      const kapsam = function (l) { return l.length ? [l[0].konum, l[l.length - 1].konum] : [0, 0]; };
      const lu = s.l[yu] || [], lv = s.l[yv] || [];
      const cizgi = function (eksen, a, l0, l1, uYon) {
        const P = function (t) { return uYon ? MA.sistemNokta(s, a.konum, t, zk) : MA.sistemNokta(s, t, a.konum, zk); };
        const bas = P(l0), son = P(l1);
        const L = uzaklik(bas, son);
        const u = L > 1e-12 ? [(son[0] - bas[0]) / L, (son[1] - bas[1]) / L, (son[2] - bas[2]) / L] : [0, 0, 0];
        const balon = a.balon !== "son" ? [bas[0] - 0.5 * u[0], bas[1] - 0.5 * u[1], bas[2] - 0.5 * u[2]] : [son[0] + 0.5 * u[0], son[1] + 0.5 * u[1], son[2] + 0.5 * u[2]];
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
      dugumler: { no: C.dno, xyz: xyz, tur: C.dtur, bayrak: dBay },
      cubuklar: { no: cNo, i: C.ci, j: C.cj, tur: C.ctur, bayrak: cBay, serbestlik: cSer, kesit: cKes, grup: cGrp, uretec: cUre, aci: cAci, y_yerel: cY },
      paneller: { no: pNo, kose_bas: C.pbas, kose_sayisi: C.psay, kose: C.pkose, tur: C.ptur, bayrak: pBay, kalinlik: pKal },
      mesnetler: { dugum: C.md, maske: C.mmaske, tur: C.mtur },
      temeller: temeller,
      kesitler: kesitler.map(function (k) { return { ad: k.ad, profil: k.profil, tur: k.tur, malzeme: k.malzeme, h: k.h, b: k.b, tw: k.tw, tf: k.tf, r: k.r }; }),
      gruplar: gruplar, malzemeler: malzemeler,
    };
  }

  /**
   * İki sahne arasındaki eleman farkı (cephe IslemRaporu). Karşılaştırılan: çubuk (uç düğümleri ve konumları, tür, kesit
   * kaydı, açı, serbestlik, grup, bayrak, üreteç), panel (köşeler, tür, kalınlık, bayrak), düğüm (konum, tür, bayrak), mesnet
   * (maske, tür), aks (ad, sistem, uçlar), temel (tür, B, L, h). Kimlik listeleri sıralı ve tekrarsızdır.
   * @returns {{eklenen: Array, silinen: Array, degisen: Array}}
   */
  function sahneFarki(a, b) {
    const yeniL = function () { return { cubuk: [], panel: [], dugum: [], mesnet: [], aks: [], temel: [] }; };
    const E = yeniL(), Sl = yeniL(), Dg = yeniL();
    const eklenen = { push: function (k) { E[k.tur].push(k.tur === "aks" ? k.alt * 4294967296 + k.no : k.no); } };
    const silinen = { push: function (k) { Sl[k.tur].push(k.tur === "aks" ? k.alt * 4294967296 + k.no : k.no); } };
    const degisen = { push: function (k) { Dg[k.tur].push(k.tur === "aks" ? k.alt * 4294967296 + k.no : k.no); } };
    const liste = function (L) {
      const out = [];
      for (const tur of ["cubuk", "panel", "dugum", "mesnet", "aks", "temel"]) {
        const v = Float64Array.from(L[tur]).sort();
        for (let i = 0; i < v.length; i++) {
          if (i && v[i] === v[i - 1]) continue;
          out.push(tur === "aks" ? { tur: tur, no: v[i] % 4294967296, alt: Math.floor(v[i] / 4294967296) } : { tur: tur, no: v[i] });
        }
      }
      return out;
    };
    if (a === b) return { eklenen: [], silinen: [], degisen: [] };
    const da = a.dugumler, db = b.dugumler, xa = da.xyz, xb = db.xyz;
    // kesit kayıtlarının eşdeğerliği (a dizini → b dizini)
    const kesitAyni = new Map();
    const kes = function (ka, kb) {
      if (ka === SAHNE_YOK || kb === SAHNE_YOK) return ka === kb;
      const anahtar = ka * 4294967296 + kb;
      let r = kesitAyni.get(anahtar);
      if (r === undefined) {
        const p = a.kesitler[ka], q = b.kesitler[kb];
        r = p.ad === q.ad && p.profil === q.profil && p.tur === q.tur && p.malzeme === q.malzeme && p.h === q.h && p.b === q.b && p.tw === q.tw && p.tf === q.tf && p.r === q.r;
        kesitAyni.set(anahtar, r);
      }
      return r;
    };
    const ayniNokta = function (i, j) { return xa[3 * i] === xb[3 * j] && xa[3 * i + 1] === xb[3 * j + 1] && xa[3 * i + 2] === xb[3 * j + 2]; };
    // düğümler
    const dm = new Map();
    for (let i = 0; i < da.no.length; i++) dm.set(da.no[i], i);
    const dGor = new Uint8Array(da.no.length);
    for (let j = 0; j < db.no.length; j++) {
      const i = dm.get(db.no[j]);
      if (i === undefined) { eklenen.push({ tur: "dugum", no: db.no[j] }); continue; }
      dGor[i] = 1;
      if (!ayniNokta(i, j) || da.tur[i] !== db.tur[j] || da.bayrak[i] !== db.bayrak[j]) degisen.push({ tur: "dugum", no: db.no[j] });
    }
    for (let i = 0; i < da.no.length; i++) if (!dGor[i]) silinen.push({ tur: "dugum", no: da.no[i] });
    // çubuklar
    const ca = a.cubuklar, cb = b.cubuklar, cm = new Map();
    for (let i = 0; i < ca.no.length; i++) cm.set(ca.no[i], i);
    const cGor = new Uint8Array(ca.no.length);
    for (let j = 0; j < cb.no.length; j++) {
      const i = cm.get(cb.no[j]);
      if (i === undefined) { eklenen.push({ tur: "cubuk", no: cb.no[j] }); continue; }
      cGor[i] = 1;
      const ai = ca.i[i], aj = ca.j[i], bi = cb.i[j], bj = cb.j[j];
      const ga = ca.grup[i], gb = cb.grup[j];
      const ayni = da.no[ai] === db.no[bi] && da.no[aj] === db.no[bj] && ayniNokta(ai, bi) && ayniNokta(aj, bj) && ca.tur[i] === cb.tur[j] &&
        ca.bayrak[i] === cb.bayrak[j] && ca.serbestlik[i] === cb.serbestlik[j] && ca.aci[i] === cb.aci[j] && ca.uretec[i] === cb.uretec[j] &&
        kes(ca.kesit[i], cb.kesit[j]) && (ga === SAHNE_YOK ? null : a.gruplar[ga]) === (gb === SAHNE_YOK ? null : b.gruplar[gb]);
      if (!ayni) degisen.push({ tur: "cubuk", no: cb.no[j] });
    }
    for (let i = 0; i < ca.no.length; i++) if (!cGor[i]) silinen.push({ tur: "cubuk", no: ca.no[i] });
    // paneller
    const pa = a.paneller, pb = b.paneller, pm = new Map();
    for (let i = 0; i < pa.no.length; i++) pm.set(pa.no[i], i);
    const pGor = new Uint8Array(pa.no.length);
    for (let j = 0; j < pb.no.length; j++) {
      const i = pm.get(pb.no[j]);
      if (i === undefined) { eklenen.push({ tur: "panel", no: pb.no[j] }); continue; }
      pGor[i] = 1;
      let ayni = pa.kose_sayisi[i] === pb.kose_sayisi[j] && pa.tur[i] === pb.tur[j] && pa.kalinlik[i] === pb.kalinlik[j] && pa.bayrak[i] === pb.bayrak[j];
      for (let k = 0; ayni && k < pa.kose_sayisi[i]; k++) {
        const x = pa.kose[pa.kose_bas[i] + k], y = pb.kose[pb.kose_bas[j] + k];
        if (da.no[x] !== db.no[y] || !ayniNokta(x, y)) ayni = false;
      }
      if (!ayni) degisen.push({ tur: "panel", no: pb.no[j] });
    }
    for (let i = 0; i < pa.no.length; i++) if (!pGor[i]) silinen.push({ tur: "panel", no: pa.no[i] });
    // mesnetler
    const ma = a.mesnetler, mb = b.mesnetler, mm = new Map();
    for (let i = 0; i < ma.dugum.length; i++) mm.set(da.no[ma.dugum[i]], i);
    const mGor = new Uint8Array(ma.dugum.length);
    for (let j = 0; j < mb.dugum.length; j++) {
      const no = db.no[mb.dugum[j]], i = mm.get(no);
      if (i === undefined) { eklenen.push({ tur: "mesnet", no: no }); continue; }
      mGor[i] = 1;
      if (ma.maske[i] !== mb.maske[j] || ma.tur[i] !== mb.tur[j]) degisen.push({ tur: "mesnet", no: no });
    }
    for (let i = 0; i < ma.dugum.length; i++) if (!mGor[i]) silinen.push({ tur: "mesnet", no: da.no[ma.dugum[i]] });
    // akslar
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
    // temeller
    const ta = new Map(a.temeller.map(function (t) { return [t.kimlik.no, t]; })), tb = new Set();
    for (const t of b.temeller) {
      const u = ta.get(t.kimlik.no);
      tb.add(t.kimlik.no);
      if (!u) eklenen.push({ tur: "temel", no: t.kimlik.no });
      else if (u.tur !== t.tur || u.B !== t.B || u.L !== t.L || u.h !== t.h) degisen.push({ tur: "temel", no: t.kimlik.no });
    }
    for (const t of a.temeller) if (!tb.has(t.kimlik.no)) silinen.push({ tur: "temel", no: t.kimlik.no });
    return { eklenen: liste(E), silinen: liste(Sl), degisen: liste(Dg) };
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
    for (const c of C.cel) {
      cubukNo.add(+c.no);
      const k = c.kaynak;
      if (k && k.aks_kat) { const a = k.aks_kat + "|" + (+k.no); if (!kaynakC.has(a)) kaynakC.set(a, []); kaynakC.get(a).push(+c.no); }
    }
    for (const p of C.pel) {
      panelNo.add(+p.no);
      const k = p.kaynak;
      if (k && k.aks_kat) { const a = k.aks_kat + "|" + (+k.no); if (!kaynakP.has(a)) kaynakP.set(a, []); kaynakP.get(a).push(+p.no); }
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
    YERLER: YERLER, bagimliliklarKur: bagimliliklarKur, cozumle: cozumle, kimlikAnahtari: kimlikAnahtari,
    bosModel: bosModel, katUyeligi: katUyeligi, kullanimYeri: kullanimYeri, profilAdiNormal: profilAdiNormal,
    oznitelikCikar: oznitelikCikar, oznitelikKodla: oznitelikKodla, sahneCikar: sahneCikar, sahneFarki: sahneFarki, sonucEsle: sonucEsle,
    // iç (tipli dizi) biçimler: cephe aynı model için önbellekler
    katHesapla: katHesapla, yerHesapla: yerHesapla, oznitelikHesapla: oznitelikHesapla, oznitelikCoz: oznitelikCoz,
  };
});
