/* Matris Öğren — IFC dışa aktarım (IFC4, ISO 10303-21 STEP fiziksel dosya).
   window.MatrisIFC = { uret(bina, veri?, secenek?) -> string, uretAyrintili(...) -> {metin, uyarilar, sayac}, dosyaAdi(bina) }
   Node'da: const MatrisIFC = require("./ifc_disari.js").

   Bağımlılık yok, DOM yok. Bina koordinatı (X sağa, Y derinlik, Z yukarı) doğrudan IFC'ye gider (IFC de Z yukarı);
   motor (cerceve3b, Y yukarı) eksenine DEĞİL. Uzunluk metre, açı radyan, kuvvet kN.

   Üretilenler:
   - Mekânsal yapı: IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey (her kat, kat 0 = temel seviyesi).
   - Fiziksel model (IfcExtrudedAreaSolid katılar): kolon → IfcColumn, kiriş → IfcBeam, çapraz/makas/aşık/kren/… → IfcMember,
     döşeme/çatı → IfcSlab (FLOOR/ROOF; kalınlık 0 → IfcCovering), cephe → IfcPlate/IfcCovering,
     temel → IfcFooting (PAD_FOOTING, STRIP_FOOTING, FOOTING_BEAM) ya da IfcSlab BASESLAB (radye).
     Kesitler: dikdörtgen → IfcRectangleProfileDef, IPE/HEA/HEB → IfcIShapeProfileDef, kutu → IfcRectangleHollowProfileDef,
     boru → IfcCircleHollowProfileDef, dolu daire → IfcCircleProfileDef, L → IfcLShapeProfileDef, U/UPN → IfcUShapeProfileDef,
     2L → iki IfcLShapeProfileDef katısı.
   - Malzeme (IfcMaterial, IfcMaterialProfileSet/Usage), Pset_*Common, Pset_ConcreteElementGeneral, Pset_MatrisOgren (D/C).
   - Yapısal analiz modeli (secenek.analiz, varsayılan açık): IfcStructuralAnalysisModel, IfcStructuralPointConnection +
     IfcBoundaryNodeCondition, IfcStructuralCurveMember (IfcEdge/IfcVertexPoint), IfcRelConnectsStructuralMember (uç serbestlikleri),
     IfcStructuralLoadCase / IfcStructuralLoadGroup (birleşimler, IfcRelAssignsToGroupByFactor), veri varsa G ve Q yükleri
     (IfcStructuralLinearAction / IfcStructuralCurveAction POLYGONAL, IfcStructuralPointAction).
   - GlobalId: 22 karakter IFC base64, (proje tohumu + nesne anahtarı) özetinden — aynı modelden aynı kimlikler. */
(function (kok, fabrika) {
  "use strict";
  const M = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = M;
  if (kok) kok.MatrisIFC = M;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : null), function () {
  "use strict";

  const SURUM = "1.0";
  const UYGULAMA = "Matris Öğren — ifc_disari.js " + SURUM;

  // IPE / HEA / HEB: [h, b, tw, tf, r] (mm) — yapi_veri.PROFILLER ile aynı değerler
  const PROFILLER = {
    "IPE 80": [80, 46, 3.8, 5.2, 5], "IPE 100": [100, 55, 4.1, 5.7, 7], "IPE 120": [120, 64, 4.4, 6.3, 7],
    "IPE 140": [140, 73, 4.7, 6.9, 7], "IPE 160": [160, 82, 5, 7.4, 9], "IPE 180": [180, 91, 5.3, 8, 9],
    "IPE 200": [200, 100, 5.6, 8.5, 12], "IPE 220": [220, 110, 5.9, 9.2, 12], "IPE 240": [240, 120, 6.2, 9.8, 15],
    "IPE 270": [270, 135, 6.6, 10.2, 15], "IPE 300": [300, 150, 7.1, 10.7, 15], "IPE 330": [330, 160, 7.5, 11.5, 18],
    "IPE 360": [360, 170, 8, 12.7, 18], "IPE 400": [400, 180, 8.6, 13.5, 21], "IPE 450": [450, 190, 9.4, 14.6, 21],
    "IPE 500": [500, 200, 10.2, 16, 21], "IPE 550": [550, 210, 11.1, 17.2, 24], "IPE 600": [600, 220, 12, 19, 24],
    "HEA 100": [96, 100, 5, 8, 12], "HEA 120": [114, 120, 5, 8, 12], "HEA 140": [133, 140, 5.5, 8.5, 12],
    "HEA 160": [152, 160, 6, 9, 15], "HEA 180": [171, 180, 6, 9.5, 15], "HEA 200": [190, 200, 6.5, 10, 18],
    "HEA 220": [210, 220, 7, 11, 18], "HEA 240": [230, 240, 7.5, 12, 21], "HEA 260": [250, 260, 7.5, 12.5, 24],
    "HEA 280": [270, 280, 8, 13, 24], "HEA 300": [290, 300, 8.5, 14, 27], "HEA 320": [310, 300, 9, 15.5, 27],
    "HEA 340": [330, 300, 9.5, 16.5, 27], "HEA 360": [350, 300, 10, 17.5, 27], "HEA 400": [390, 300, 11, 19, 27],
    "HEA 450": [440, 300, 11.5, 21, 27], "HEA 500": [490, 300, 12, 23, 27], "HEA 550": [540, 300, 12.5, 24, 27],
    "HEA 600": [590, 300, 13, 25, 27], "HEB 100": [100, 100, 6, 10, 12], "HEB 120": [120, 120, 6.5, 11, 12],
    "HEB 140": [140, 140, 7, 12, 12], "HEB 160": [160, 160, 8, 13, 15], "HEB 180": [180, 180, 8.5, 14, 15],
    "HEB 200": [200, 200, 9, 15, 18], "HEB 220": [220, 220, 9.5, 16, 18], "HEB 240": [240, 240, 10, 17, 21],
    "HEB 260": [260, 260, 10, 17.5, 24], "HEB 280": [280, 280, 10.5, 18, 24], "HEB 300": [300, 300, 11, 19, 27],
    "HEB 320": [320, 300, 11.5, 20.5, 27], "HEB 340": [340, 300, 12, 21.5, 27], "HEB 360": [360, 300, 12.5, 22.5, 27],
    "HEB 400": [400, 300, 13.5, 24, 27], "HEB 450": [450, 300, 14, 26, 27], "HEB 500": [500, 300, 14.5, 28, 27],
    "HEB 550": [550, 300, 15, 29, 27], "HEB 600": [600, 300, 15.5, 30, 27],
  };

  // çubuk türü → IFC sınıfı ve PredefinedType (§12.2 "tur" listesi)
  const CUBUK_SINIF = {
    "kolon": ["IFCCOLUMN", "COLUMN"], "kiris": ["IFCBEAM", "BEAM"], "capraz": ["IFCMEMBER", "BRACE"],
    "makas-ust": ["IFCMEMBER", "CHORD"], "makas-alt": ["IFCMEMBER", "CHORD"], "makas-dikme": ["IFCMEMBER", "POST"],
    "makas-diyagonal": ["IFCMEMBER", "MEMBER"], "asik": ["IFCMEMBER", "PURLIN"], "kren": ["IFCMEMBER", "MEMBER"],
    "bag": ["IFCMEMBER", "STRUT"], "diger": ["IFCMEMBER", "MEMBER"],
  };
  const CUBUK_AD = {
    "kolon": "Kolon", "kiris": "Kiriş", "capraz": "Çapraz", "makas-ust": "Makas üst başlık", "makas-alt": "Makas alt başlık",
    "makas-dikme": "Makas dikmesi", "makas-diyagonal": "Makas diyagonali", "asik": "Aşık", "kren": "Kren kirişi", "bag": "Bağ çubuğu",
    "diger": "Çubuk",
  };

  // ======================================================================
  // Küçük yardımcılar
  // ======================================================================
  function sayi(v, varsayilan) { const x = +v; return (v === null || v === undefined || v === "" || !isFinite(x)) ? varsayilan : x; }
  function dizi(v) { return Array.isArray(v) ? v : []; }
  function sozluk(v) { return v && typeof v === "object" && !Array.isArray(v) ? v : {}; }

  // ---- vektörler ----
  function vfark(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function vtop(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
  function volc(a, k) { return [a[0] * k, a[1] * k, a[2] * k]; }
  function vic(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function vdis(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function vboy(a) { return Math.sqrt(vic(a, a)); }
  function vbirim(a) { const L = vboy(a); return L > 0 ? volc(a, 1 / L) : [0, 0, 0]; }

  // ---- deterministik GlobalId (cyrb128 özeti → 128 bit → 22 karakter IFC base64) ----
  const ALFABE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";
  function ozet128(s) {
    let h1 = 1779033703, h2 = 3144134277, h3 = 1013904242, h4 = 2773480762;
    for (let i = 0; i < s.length; i++) {
      const k = s.charCodeAt(i);
      h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
      h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
      h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
      h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
    }
    h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067);
    h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233);
    h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213);
    h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);
    h1 ^= (h2 ^ h3 ^ h4); h2 ^= h1; h3 ^= h1; h4 ^= h1;
    return [h1 >>> 0, h2 >>> 0, h3 >>> 0, h4 >>> 0];
  }
  function globalId(anahtar) {
    const h = ozet128(String(anahtar));
    let bit = "";
    h.forEach(function (w) { bit += ("00000000000000000000000000000000" + w.toString(2)).slice(-32); });
    // UUID sürüm 4 / RFC 4122 varyant bitleri (bilgi amaçlı; IFC zorunlu tutmaz)
    bit = bit.slice(0, 48) + "0100" + bit.slice(52, 64) + "10" + bit.slice(66);
    let s = ALFABE[parseInt(bit.slice(0, 2), 2)];
    for (let i = 2; i < 128; i += 6) s += ALFABE[parseInt(bit.slice(i, i + 6), 2)];
    return s;
  }

  // ---- STEP biçimlendirme ----
  // Metin: ' → '', \ → \\, ASCII dışı → \X2\HHHH\X0\ (UCS-2; BMP dışı → \X4\HHHHHHHH\X0\)
  function stepMetin(s) {
    s = String(s === null || s === undefined ? "" : s);
    let out = "", buf = [];
    const kapat = function () {
      if (!buf.length) return;
      const x4 = buf.some(function (c) { return c > 0xFFFF; });
      out += x4 ? "\\X4\\" + buf.map(function (c) { return ("00000000" + c.toString(16).toUpperCase()).slice(-8); }).join("") + "\\X0\\"
        : "\\X2\\" + buf.map(function (c) { return ("0000" + c.toString(16).toUpperCase()).slice(-4); }).join("") + "\\X0\\";
      buf = [];
    };
    for (const ch of s) {
      const c = ch.codePointAt(0);
      if (c >= 0x20 && c <= 0x7E) {
        kapat();
        out += ch === "'" ? "''" : (ch === "\\" ? "\\\\" : ch);
      } else if (c === 0x0A || c === 0x0D || c === 0x09) {
        kapat(); out += " ";
      } else {
        buf.push(c);
      }
    }
    kapat();
    return out;
  }
  function S(s) { return "'" + stepMetin(s) + "'"; }
  function R(x) {
    x = +x;
    if (!isFinite(x)) throw new Error("IFC: sonlu olmayan sayı");
    let v = parseFloat(x.toPrecision(12));
    if (Object.is(v, -0) || Math.abs(v) < 1e-12) v = 0;
    let s = String(v);
    if (s.indexOf("e") >= 0) {
      const p = s.split("e");
      let m = p[0];
      if (m.indexOf(".") < 0) m += ".";
      return m + "E" + p[1].replace("+", "");
    }
    return s.indexOf(".") < 0 ? s + "." : s;
  }
  function I(n) { return { _ham: String(Math.round(+n)) }; }
  function E(ad) { return { _ham: "." + ad + "." }; }
  function T(tip, v) { return { _ham: tip + "(" + bicim(v) + ")" }; }
  function B(b) { return { _ham: b ? ".T." : ".F." }; }
  function bicim(v) {
    if (v === null || v === undefined) return "$";
    if (typeof v === "number") return R(v);
    if (typeof v === "boolean") return v ? ".T." : ".F.";
    if (Array.isArray(v)) return "(" + v.map(bicim).join(",") + ")";
    if (typeof v === "object" && v._ham !== undefined) return v._ham;
    if (typeof v === "string") {
      if (/^#\d+$/.test(v) || v === "*") return v;     // varlık başvurusu ya da türetilmiş
      return S(v);                                      // düz metin
    }
    throw new Error("IFC: biçimlenemeyen değer " + v);
  }

  function Yazici() {
    this.satirlar = [];
    this.n = 0;
    this.on = {};
    this.sayac = {};
  }
  Yazici.prototype.ekle = function (tip, alanlar) {
    const no = ++this.n;
    this.satirlar.push("#" + no + "=" + tip + "(" + alanlar.map(bicim).join(",") + ");");
    this.sayac[tip] = (this.sayac[tip] || 0) + 1;
    return "#" + no;
  };
  Yazici.prototype.tek = function (anahtar, tip, alanlar) {   // aynı içerikli küçük varlıkları (nokta, doğrultu) paylaş
    if (!this.on[anahtar]) this.on[anahtar] = this.ekle(tip, alanlar);
    return this.on[anahtar];
  };

  function asciiAd(s) {
    const tablo = { "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U", "×": "x", "→": "-" };
    return String(s || "").replace(/[çÇğĞıİöÖşŞüÜ×→]/g, function (c) { return tablo[c]; })
      .normalize("NFKD").replace(/[̀-ͯ]/g, "");
  }
  function dosyaAdi(bina) {
    const b = sozluk(bina);
    const kok = asciiAd(b.baslik || "bina").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 60) || "bina";
    return kok + ".ifc";
  }

  // ======================================================================
  // Bina modelini çözümleme (aks–kat + surum 3 serbest katman)
  // ======================================================================
  function modelHazirla(bina, veri, uyarilar) {
    const ag = veri && veri.ag && Array.isArray(veri.ag.dugumler) && Array.isArray(veri.ag.elemanlar) ? veri.ag : null;
    const kut = sozluk(veri && veri.kutuphane_ozeti);
    const Bm = {
      bina: bina, veri: veri || null, ag: ag,
      baslik: String(bina.baslik || (veri && veri.baslik) || "Bina modeli"),
      sistem: String(bina.sistem || (veri && veri.sistem) || "betonarme"),
      malzemeler: Object.assign({}, sozluk(kut.malzemeler), sozluk(bina.malzemeler)),
      kesitler: Object.assign({}, sozluk(kut.kesitler), sozluk(bina.kesitler)),
    };
    const ak = sozluk(bina.akslar);
    Bm.ax = dizi(ak.x).map(function (a) { return { ad: String(a.ad), konum: sayi(a.konum, 0) }; }).sort(function (a, b) { return a.konum - b.konum; });
    Bm.ay = dizi(ak.y).map(function (a) { return { ad: String(a.ad), konum: sayi(a.konum, 0) }; }).sort(function (a, b) { return a.konum - b.konum; });
    Bm.ixAd = {}; Bm.iyAd = {};
    Bm.ax.forEach(function (a, i) { Bm.ixAd[a.ad] = i; });
    Bm.ay.forEach(function (a, i) { Bm.iyAd[a.ad] = i; });
    Bm.katlar = dizi(bina.katlar).map(function (k, i) {
      const no = k.no === undefined ? i : +k.no;
      return { no: no, ad: String(k.ad || (no ? no + ". kat" : "Temel")), kot: sayi(k.kot, 0) };
    }).sort(function (a, b) { return a.no - b.no; });
    if (!Bm.katlar.length) Bm.katlar = [{ no: 0, ad: "Temel", kot: 0 }];
    Bm.kat = {};
    Bm.katlar.forEach(function (k) { Bm.kat[k.no] = k; });
    Bm.nk = Bm.katlar[Bm.katlar.length - 1].no;
    Bm.kot0 = Bm.katlar[0].kot;
    return Bm;
  }

  function aksXY(Bm, aks) {
    if (!Array.isArray(aks) || aks.length < 2) return null;
    const ix = Bm.ixAd[String(aks[0])], iy = Bm.iyAd[String(aks[1])];
    if (ix === undefined || iy === undefined) return null;
    return { ix: ix, iy: iy, X: Bm.ax[ix].konum, Y: Bm.ay[iy].konum };
  }
  function katKot(Bm, k) { return Bm.kat[k] ? Bm.kat[k].kot : null; }
  function aksDugumNo(kat, ix, iy) { return 1000 * kat + 20 * ix + iy + 1; }   // yapi._dugum_no ile aynı kural

  // Kat (IfcBuildingStorey) seçimi: z'ye ≤ 0,3 m yakın seviye; değilse altındaki en yakın seviye
  function seviyeBul(Bm, z) {
    let en = Bm.katlar[0];
    Bm.katlar.forEach(function (k) {
      if (Math.abs(k.kot - z) <= 0.3 || k.kot <= z + 1e-9) {
        if (Math.abs(k.kot - z) <= 0.3 || k.kot > en.kot) en = k;
      }
    });
    let yakin = null;
    Bm.katlar.forEach(function (k) { if (Math.abs(k.kot - z) <= 0.3 && (!yakin || Math.abs(k.kot - z) < Math.abs(yakin.kot - z))) yakin = k; });
    return (yakin || en).no;
  }

  // ---- düğümler (analiz modeli ve REF çözümü) ----
  function DugumKumesi(Bm) {
    this.Bm = Bm;
    this.liste = [];
    this.no = {};
    this.serbestSira = 100000;
  }
  DugumKumesi.prototype.ekle = function (no, X, Y, Z, ad) {
    if (this.no[no]) return this.no[no];
    const d = { no: no, X: X, Y: Y, Z: Z, ad: ad || ("N" + no) };
    this.liste.push(d);
    this.no[no] = d;
    if (no >= this.serbestSira) this.serbestSira = no;
    return d;
  };
  DugumKumesi.prototype.konumda = function (X, Y, Z) {
    for (let i = 0; i < this.liste.length; i++) {
      const d = this.liste[i];
      if (Math.abs(d.X - X) <= 1e-3 && Math.abs(d.Y - Y) <= 1e-3 && Math.abs(d.Z - Z) <= 1e-3) return d;
    }
    return null;
  };
  DugumKumesi.prototype.aksDugum = function (ix, iy, kat) {
    const Bm = this.Bm, kot = katKot(Bm, kat);
    if (kot === null || !Bm.ax[ix] || !Bm.ay[iy]) return null;
    const no = aksDugumNo(kat, ix, iy);
    if (this.no[no]) return this.no[no];
    return this.ekle(no, Bm.ax[ix].konum, Bm.ay[iy].konum, kot, Bm.ax[ix].ad + Bm.ay[iy].ad + "/k" + kat);
  };
  // §12.1 REF: {"dugum": no} | {"aks": [..], "kat": k} | {"X", "Y", "Z"}
  DugumKumesi.prototype.ref = function (r) {
    const Bm = this.Bm;
    if (r === null || r === undefined) return null;
    if (typeof r === "number") r = { dugum: r };
    if (Array.isArray(r) && r.length === 3) r = { X: r[0], Y: r[1], Z: r[2] };
    if (typeof r !== "object") return null;
    if (r.dugum !== undefined) {
      const no = +r.dugum;
      if (this.no[no]) return this.no[no];
      const serbest = dizi(Bm.bina.dugumler).filter(function (d) { return +d.no === no; })[0];
      if (serbest) return this.ekle(no, sayi(serbest.X, 0), sayi(serbest.Y, 0), sayi(serbest.Z, 0), serbest.ad || ("N" + no));
      if (no > 0 && no < 100000) {
        const kat = Math.floor(no / 1000), kalan = no % 1000 - 1, ix = Math.floor(kalan / 20), iy = kalan % 20;
        return this.aksDugum(ix, iy, kat);
      }
      return null;
    }
    if (r.aks !== undefined) {
      const a = aksXY(Bm, r.aks);
      if (!a) return null;
      return this.aksDugum(a.ix, a.iy, r.kat === undefined ? 0 : +r.kat);
    }
    if (r.X !== undefined || r.Y !== undefined || r.Z !== undefined) {
      const X = sayi(r.X, 0), Y = sayi(r.Y, 0), Z = sayi(r.Z, 0);
      const var_ = this.konumda(X, Y, Z);
      if (var_) return var_;
      return this.ekle(this.serbestSira + 1, X, Y, Z);
    }
    return null;
  };

  // ======================================================================
  // Kesit ve malzeme çözümleme
  // ======================================================================
  function metre(v) { const x = +v; return isFinite(x) ? (x > 5 ? x / 1000 : x) : null; }   // > 5 → mm girilmiş say
  function profilAdi(ad) {
    let p = String(ad || "").trim().toUpperCase().replace(/\s+/g, " ");
    if (p && p.indexOf(" ") < 0) {
      ["IPE", "HEA", "HEB"].forEach(function (on) { if (p.indexOf(on) === 0 && p.length > on.length) p = on + " " + p.slice(on.length); });
    }
    return p;
  }

  function kesitCoz(Bm, ad, uyarilar) {
    const k = Bm.kesitler[ad];
    const sonuc = { ad: String(ad || "?"), malzeme: null, donati: null, pas: null };
    if (!k) {
      uyarilar.push("Kesit '" + ad + "' tanımsız; 0,30 × 0,30 m dikdörtgen varsayıldı.");
      return Object.assign(sonuc, { tur: "dikdortgen", b: 0.3, h: 0.3 });
    }
    sonuc.malzeme = k.malzeme || null;
    sonuc.donati = k.donati || null;
    sonuc.pas = k.pas === undefined ? null : sayi(k.pas, null);
    const tip = String(k.tip || "dikdortgen").toLowerCase();
    if (tip === "profil" || k.profil) {
      const pad = profilAdi(k.profil || ad);
      const p = PROFILLER[pad];
      sonuc.profil = pad;
      if (p) return Object.assign(sonuc, { tur: "I", h: p[0] / 1000, b: p[1] / 1000, tw: p[2] / 1000, tf: p[3] / 1000, r: p[4] / 1000 });
      if (k.tw && k.tf && k.b && k.h) {
        return Object.assign(sonuc, { tur: "I", h: metre(k.h), b: metre(k.b), tw: metre(k.tw), tf: metre(k.tf), r: k.r ? metre(k.r) : null });
      }
      const ozel = profilTipiCoz(pad, k);
      if (ozel) return Object.assign(sonuc, ozel);
      uyarilar.push("Profil '" + pad + "' tabloda yok; b × h dikdörtgen katı ile gösterildi.");
      return Object.assign(sonuc, { tur: "dikdortgen", b: metre(k.b) || 0.2, h: metre(k.h) || 0.3 });
    }
    const ozel = profilTipiCoz(tip, k);
    if (ozel) return Object.assign(sonuc, ozel);
    return Object.assign(sonuc, { tur: "dikdortgen", b: metre(k.b) || 0.3, h: metre(k.h) || 0.3 });
  }
  // kutu / boru / daire / L / U / 2L kesitleri (surum 3 kütüphanesi için; alanlar m, > 5 ise mm sayılır)
  function profilTipiCoz(tip, k) {
    const t = String(tip || "").toLowerCase().replace(/\s+/g, "");
    const h = metre(k.h), b = metre(k.b), kal = metre(k.t), D = metre(k.D !== undefined ? k.D : k.d);
    if (/^(kutu|shs|rhs|box)/.test(t) && h && b && kal) return { tur: "kutu", h: h, b: b, t: kal };
    if (/^(boru|chs|pipe)/.test(t) && D && kal) return { tur: "boru", D: D, t: kal };
    if (/^(daire|yuvarlak|circle)/.test(t) && D) return { tur: "daire", D: D };
    if (/^2l/.test(t) && h && (b || h) && kal) return { tur: "2L", h: h, b: b || h, t: kal, ara: metre(k.ara) || 0.01 };
    if (/^(l|kosebent)/.test(t) && h && (b || h) && kal) return { tur: "L", h: h, b: b || h, t: kal };
    if (/^(u|upn|npu)/.test(t) && h && b) return { tur: "U", h: h, b: b, tw: metre(k.tw) || kal || 0.006, tf: metre(k.tf) || kal || 0.009 };
    return null;
  }

  function malzemeBilgi(Bm, ad) {
    const m = sozluk(Bm.malzemeler[ad]);
    const kut = String(m.kutuphane || ad || "Malzeme");
    let tur = m.tur || null;
    if (!tur) tur = /^C\d/i.test(kut) ? "beton" : (/^S\d/i.test(kut) ? "celik" : (/^B\d/i.test(kut) ? "donati" : "?"));
    return { ad: kut, anahtar: ad, tur: tur };
  }
  function betonMalzeme(Bm) {
    const anahtarlar = Object.keys(Bm.malzemeler);
    for (let i = 0; i < anahtarlar.length; i++) {
      const m = malzemeBilgi(Bm, anahtarlar[i]);
      if (m.tur === "beton") return m;
    }
    return { ad: "C30/37", anahtar: null, tur: "beton" };
  }

  // Derinlik (profil Y) doğrultusu: kolon yon x → X, yon y → Y; yatay çubuk → yukarı; düşey çubuk → −X (§2: y′ = −X);
  // çubuk "aci" (derece) x′ ekseni etrafında döndürür (Rodrigues).
  function derinlikYonu(t, aci) {
    let d;
    if (Math.abs(t[2]) > 0.999) d = [-1, 0, 0];
    else d = vbirim(vfark([0, 0, 1], volc(t, t[2])));
    const a = sayi(aci, 0) * Math.PI / 180;
    if (a) d = vbirim(vtop(volc(d, Math.cos(a)), volc(vdis(t, d), Math.sin(a))));
    return d;
  }

  // ======================================================================
  // Üretici
  // ======================================================================
  function Uretici(bina, veri, secenek) {
    this.uyarilar = [];
    this.s = Object.assign({ analiz: true, yukler: true, sonuclar: true }, sozluk(secenek));
    this.Bm = modelHazirla(bina, veri, this.uyarilar);
    const proje = sozluk(this.s.proje);
    this.tohum = String(this.s.tohum || proje.ad || this.Bm.baslik);
    this.w = new Yazici();
    this.kullanilanId = {};
  }
  Uretici.prototype.gid = function (anahtar) {
    let a = this.tohum + "|" + anahtar, g = globalId(a), k = 0;
    while (this.kullanilanId[g]) { k += 1; g = globalId(a + "#" + k); }
    this.kullanilanId[g] = true;
    return g;
  };
  Uretici.prototype.nokta = function (p) {
    const k = [R(p[0]), R(p[1]), R(p[2])];
    return this.w.tek("P" + k.join(","), "IFCCARTESIANPOINT", [[+p[0], +p[1], +p[2]]]);
  };
  Uretici.prototype.nokta2 = function (p) {
    return this.w.tek("P2" + R(p[0]) + "," + R(p[1]), "IFCCARTESIANPOINT", [[+p[0], +p[1]]]);
  };
  Uretici.prototype.yon = function (v) {
    const u = vbirim(v).map(function (x) { return Math.abs(x) < 1e-12 ? 0 : x; });
    return this.w.tek("D" + u.map(R).join(","), "IFCDIRECTION", [u]);
  };
  Uretici.prototype.eksen3 = function (konum, z, x) {
    return this.w.ekle("IFCAXIS2PLACEMENT3D", [this.nokta(konum), z ? this.yon(z) : null, x ? this.yon(x) : null]);
  };
  Uretici.prototype.yerlesim = function (ust, konum, z, x) {
    return this.w.ekle("IFCLOCALPLACEMENT", [ust || null, this.eksen3(konum, z, x)]);
  };
  Uretici.prototype.sekil = function (katilar) {
    const rep = this.w.ekle("IFCSHAPEREPRESENTATION", [this.ctxBody, "Body", "SweptSolid", katilar]);
    return this.w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [rep]]);
  };
  Uretici.prototype.uzat = function (profil, uzunluk, konum2) {
    return this.w.ekle("IFCEXTRUDEDAREASOLID", [profil, konum2 || null, this.yon([0, 0, 1]), uzunluk]);
  };

  // ---- başlangıç: proje, birimler, bağlamlar, mekânsal yapı ----
  Uretici.prototype.basla = function () {
    const w = this.w, Bm = this.Bm, proje = sozluk(this.s.proje);
    const m = w.ekle("IFCSIUNIT", ["*", E("LENGTHUNIT"), null, E("METRE")]);
    const m2 = w.ekle("IFCSIUNIT", ["*", E("AREAUNIT"), null, E("SQUARE_METRE")]);
    const m3 = w.ekle("IFCSIUNIT", ["*", E("VOLUMEUNIT"), null, E("CUBIC_METRE")]);
    const rad = w.ekle("IFCSIUNIT", ["*", E("PLANEANGLEUNIT"), null, E("RADIAN")]);
    const kN = w.ekle("IFCSIUNIT", ["*", E("FORCEUNIT"), E("KILO"), E("NEWTON")]);
    const tur = function (birim, us) { return w.ekle("IFCDERIVEDUNITELEMENT", [birim, I(us)]); };
    const tureyen = function (elemanlar, tip) { return w.ekle("IFCDERIVEDUNIT", [elemanlar, E(tip), null]); };
    const kNm = tureyen([tur(kN, 1), tur(m, -1)], "LINEARFORCEUNIT");
    const kNm2 = tureyen([tur(kN, 1), tur(m, -2)], "PLANARFORCEUNIT");
    const kNxm = tureyen([tur(kN, 1), tur(m, 1)], "TORQUEUNIT");
    const kNmm = tureyen([tur(kN, 1), tur(m, 1), tur(m, -1)], "LINEARMOMENTUNIT");
    const kyay = tureyen([tur(kN, 1), tur(m, -1)], "LINEARSTIFFNESSUNIT");
    const kdon = tureyen([tur(kN, 1), tur(m, 1), tur(rad, -1)], "ROTATIONALSTIFFNESSUNIT");
    const birimler = w.ekle("IFCUNITASSIGNMENT", [[m, m2, m3, rad, kN, kNm, kNm2, kNxm, kNmm, kyay, kdon]]);
    const dunya = this.eksen3([0, 0, 0], null, null);
    this.ctx = w.ekle("IFCGEOMETRICREPRESENTATIONCONTEXT", [null, "Model", I(3), 1e-5, dunya, null]);
    this.ctxBody = w.ekle("IFCGEOMETRICREPRESENTATIONSUBCONTEXT", ["Body", "Model", "*", "*", "*", "*", this.ctx, null, E("MODEL_VIEW"), null]);
    this.ctxRef = w.ekle("IFCGEOMETRICREPRESENTATIONSUBCONTEXT", ["Reference", "Model", "*", "*", "*", "*", this.ctx, null, E("GRAPH_VIEW"), null]);
    this.proje = w.ekle("IFCPROJECT", [this.gid("proje"), null, proje.ad || Bm.baslik, String(Bm.bina.aciklama || "").slice(0, 500) || null,
      null, Bm.baslik, null, [this.ctx], birimler]);
    this.ySite = this.yerlesim(null, [0, 0, 0]);
    const adres = [proje.yer, proje.ilce, proje.il].filter(Boolean).join(", ");
    const parsel = [proje.ada ? "Ada " + proje.ada : "", proje.parsel ? "Parsel " + proje.parsel : ""].filter(Boolean).join(" / ");
    this.site = w.ekle("IFCSITE", [this.gid("arsa"), null, "Arsa", adres || null, null, this.ySite, null, null, E("ELEMENT"),
      null, null, null, parsel || null, null]);
    this.yBina = this.yerlesim(this.ySite, [0, 0, 0]);
    this.yapi = w.ekle("IFCBUILDING", [this.gid("bina"), null, Bm.baslik, (Bm.sistem === "celik" ? "Çelik" : "Betonarme") + " taşıyıcı sistem",
      null, this.yBina, null, null, E("ELEMENT"), null, null, null]);
    w.ekle("IFCRELAGGREGATES", [this.gid("rel:proje-arsa"), null, null, null, this.proje, [this.site]]);
    w.ekle("IFCRELAGGREGATES", [this.gid("rel:arsa-bina"), null, null, null, this.site, [this.yapi]]);
    this.katlar = {};
    const katlar = [];
    const self = this;
    Bm.katlar.forEach(function (k) {
      const y = self.yerlesim(self.yBina, [0, 0, k.kot]);
      const kat = w.ekle("IFCBUILDINGSTOREY", [self.gid("kat:" + k.no), null, k.ad, k.no === 0 ? "Temel seviyesi (kat 0)" : "Kat " + k.no + " döşeme seviyesi",
        null, y, null, null, E("ELEMENT"), k.kot]);
      self.katlar[k.no] = { ref: kat, yer: y, kot: k.kot, elemanlar: [] };
      katlar.push(kat);
    });
    w.ekle("IFCRELAGGREGATES", [this.gid("rel:bina-katlar"), null, null, null, this.yapi, katlar]);
    // malzeme ve profil önbellekleri
    this.malz = {};
    this.profil = {};
    this.profilSet = {};
    this.profilKullanim = {};
    this.malzIliski = {};      // malzeme ref → [eleman]
    this.fizik = {};           // "kolon:1" → eleman ref (yapısal üyeyle ilişki için)
  };

  Uretici.prototype.malzeme = function (bilgi) {
    if (!this.malz[bilgi.ad]) {
      const kat = bilgi.tur === "beton" ? "concrete" : (bilgi.tur === "celik" ? "steel" : (bilgi.tur === "donati" ? "steel" : null));
      this.malz[bilgi.ad] = this.w.ekle("IFCMATERIAL", [bilgi.ad, bilgi.tur === "beton" ? "Beton (TS 500)" : (bilgi.tur === "celik" ? "Yapı çeliği (ÇYTHYE)" : null), kat]);
    }
    return this.malz[bilgi.ad];
  };
  Uretici.prototype.malzemeBagla = function (malzRef, eleman) {
    (this.malzIliski[malzRef] = this.malzIliski[malzRef] || []).push(eleman);
  };

  // Profil tanımı (kesit adı başına bir kez). Dönüş: {ref, derinlik, ekRef (2L ikinci katı için)}
  Uretici.prototype.profilTanimi = function (k) {
    const anahtar = k.ad;
    if (this.profil[anahtar]) return this.profil[anahtar];
    const w = this.w, ad = k.profil || k.ad;
    let ref, derinlik = k.h || k.D || 0.3, ek = null;
    if (k.tur === "I") {
      ref = w.ekle("IFCISHAPEPROFILEDEF", [E("AREA"), ad, null, k.b, k.h, k.tw, k.tf, k.r || null, null, null]);
    } else if (k.tur === "kutu") {
      ref = w.ekle("IFCRECTANGLEHOLLOWPROFILEDEF", [E("AREA"), ad, null, k.b, k.h, k.t, null, null]);
    } else if (k.tur === "boru") {
      ref = w.ekle("IFCCIRCLEHOLLOWPROFILEDEF", [E("AREA"), ad, null, k.D / 2, k.t]);
      derinlik = k.D;
    } else if (k.tur === "daire") {
      ref = w.ekle("IFCCIRCLEPROFILEDEF", [E("AREA"), ad, null, k.D / 2]);
      derinlik = k.D;
    } else if (k.tur === "L") {
      ref = w.ekle("IFCLSHAPEPROFILEDEF", [E("AREA"), ad, null, k.h, k.b, k.t, null, null, null]);
    } else if (k.tur === "2L") {
      // iki köşebent sırt sırta: ara/2 + b/2 kadar kaydırılmış iki profil, ikincisi aynalı (x → −x)
      const kay = k.ara / 2 + k.b / 2;
      const p1 = w.ekle("IFCAXIS2PLACEMENT2D", [this.nokta2([kay, 0]), null]);
      const p2 = w.ekle("IFCAXIS2PLACEMENT2D", [this.nokta2([-kay, 0]), w.ekle("IFCDIRECTION", [[-1, 0]])]);
      ref = w.ekle("IFCLSHAPEPROFILEDEF", [E("AREA"), ad + " (1)", p1, k.h, k.b, k.t, null, null, null]);
      ek = w.ekle("IFCLSHAPEPROFILEDEF", [E("AREA"), ad + " (2)", p2, k.h, k.b, k.t, null, null, null]);
    } else if (k.tur === "U") {
      ref = w.ekle("IFCUSHAPEPROFILEDEF", [E("AREA"), ad, null, k.h, k.b, k.tw, k.tf, null, null, null]);
    } else {
      ref = w.ekle("IFCRECTANGLEPROFILEDEF", [E("AREA"), ad, null, k.b, k.h]);
    }
    this.profil[anahtar] = { ref: ref, derinlik: derinlik, ek: ek };
    return this.profil[anahtar];
  };
  // IfcMaterialProfileSet (kesit başına) ve IfcMaterialProfileSetUsage (kesit + kardinal nokta başına)
  Uretici.prototype.profilKullanimi = function (k, kardinal) {
    const anahtar = k.ad + "|" + kardinal;
    if (this.profilKullanim[anahtar]) return this.profilKullanim[anahtar];
    if (!this.profilSet[k.ad]) {
      const pt = this.profilTanimi(k);
      const mz = this.malzeme(malzemeBilgi(this.Bm, k.malzeme));
      const mp = this.w.ekle("IFCMATERIALPROFILE", [k.ad, null, mz, pt.ref, null, null]);
      this.profilSet[k.ad] = this.w.ekle("IFCMATERIALPROFILESET", [k.ad, null, [mp], null]);
    }
    this.profilKullanim[anahtar] = this.w.ekle("IFCMATERIALPROFILESETUSAGE", [this.profilSet[k.ad], I(kardinal), null]);
    return this.profilKullanim[anahtar];
  };

  // ---- özellik kümeleri ----
  Uretici.prototype.pset = function (anahtar, ad, ozellikler, nesneler) {
    const w = this.w;
    const props = [];
    ozellikler.forEach(function (o) {
      if (o[1] === null || o[1] === undefined) return;
      props.push(w.ekle("IFCPROPERTYSINGLEVALUE", [o[0], null, o[1], null]));
    });
    if (!props.length) return;
    const ps = w.ekle("IFCPROPERTYSET", [this.gid("pset:" + anahtar + ":" + ad), null, ad, null, props]);
    w.ekle("IFCRELDEFINESBYPROPERTIES", [this.gid("rel:pset:" + anahtar + ":" + ad), null, null, null, nesneler, ps]);
  };
  Uretici.prototype.tasarimBul = function (tur, no) {
    const tas = this.Bm.veri && this.Bm.veri.tasarim;
    if (!tas || !Array.isArray(tas.elemanlar)) return null;
    for (let i = 0; i < tas.elemanlar.length; i++) {
      const e = tas.elemanlar[i];
      if (e && e.tur === tur && +e.no === +no) return e;
    }
    return null;
  };
  Uretici.prototype.ortakPsetler = function (anahtar, ref, sinif, k, ek) {
    const mb = k ? malzemeBilgi(this.Bm, k.malzeme) : betonMalzeme(this.Bm);
    const common = { IFCCOLUMN: "Pset_ColumnCommon", IFCBEAM: "Pset_BeamCommon", IFCMEMBER: "Pset_MemberCommon", IFCSLAB: "Pset_SlabCommon",
      IFCFOOTING: "Pset_FootingCommon", IFCPLATE: "Pset_PlateCommon", IFCCOVERING: "Pset_CoveringCommon" }[sinif];
    const ozel = [["Reference", T("IFCIDENTIFIER", k ? k.ad : (ek.referans || ""))]];
    if (sinif !== "IFCCOVERING") ozel.push(["LoadBearing", T("IFCBOOLEAN", sinif !== "IFCPLATE" || !!ek.tasiyici)]);
    if (ek.dis !== undefined && sinif !== "IFCFOOTING") ozel.push(["IsExternal", T("IFCBOOLEAN", !!ek.dis)]);
    if (ek.aciklik && (sinif === "IFCBEAM" || sinif === "IFCMEMBER")) ozel.push(["Span", T("IFCPOSITIVELENGTHMEASURE", ek.aciklik)]);
    if (common) this.pset(anahtar, common, ozel, [ref]);
    if (mb.tur === "beton") {
      const donati = k && k.donati ? malzemeBilgi(this.Bm, k.donati).ad : null;
      this.pset(anahtar, "Pset_ConcreteElementGeneral", [
        ["StrengthClass", T("IFCLABEL", mb.ad)],
        ["ReinforcementStrengthClass", donati ? T("IFCLABEL", donati) : null],
        ["ConcreteCover", k && k.pas ? T("IFCPOSITIVELENGTHMEASURE", k.pas) : null],
      ], [ref]);
    }
    const mo = [
      ["Adres", ek.adres ? T("IFCLABEL", ek.adres) : null],
      ["Tur", ek.tur ? T("IFCLABEL", ek.tur) : null],
      ["No", ek.no !== undefined ? T("IFCINTEGER", I(ek.no)) : null],
      ["Kat", ek.kat !== undefined ? T("IFCINTEGER", I(ek.kat)) : null],
      ["Kesit", k ? T("IFCLABEL", k.ad) : null],
      ["Profil", k && k.profil ? T("IFCLABEL", k.profil) : null],
      ["Malzeme", T("IFCLABEL", mb.ad)],
      ["Yon", ek.yon ? T("IFCLABEL", ek.yon) : null],
    ].concat(ek.ozel || []);
    if (this.s.sonuclar && ek.tasarimTur) {
      const t = this.tasarimBul(ek.tasarimTur, ek.no);
      if (t && t.dc !== null && t.dc !== undefined && isFinite(+t.dc)) {
        mo.push(["DC", T("IFCRATIOMEASURE", +t.dc)]);
        if (t.belirleyen && t.belirleyen.kombinasyon) mo.push(["BelirleyenBirlesim", T("IFCLABEL", t.belirleyen.kombinasyon)]);
        if (t.belirleyen && t.belirleyen.kontrol) mo.push(["BelirleyenKontrol", T("IFCLABEL", t.belirleyen.kontrol)]);
        if (t.durum) mo.push(["TasarimDurumu", T("IFCLABEL", t.durum)]);
      } else if (t && t.durum) {
        mo.push(["TasarimDurumu", T("IFCLABEL", t.durum)]);
      }
    }
    this.pset(anahtar, "Pset_MatrisOgren", mo, [ref]);
  };

  // ---- çubuk katısı (kolon, kiriş, IfcMember) ----
  // p1, p2: global uçlar; d: derinlik doğrultusu; kardinal: 8 = üst orta (kiriş üstü düğüm çizgisinde), 5 = ağırlık merkezi
  Uretici.prototype.cubukEleman = function (o) {
    const w = this.w, kat = this.katlar[o.kat] || this.katlar[this.Bm.katlar[0].no];
    const L = vboy(vfark(o.p2, o.p1));
    if (!(L > 1e-6)) { this.uyarilar.push(o.ad + ": sıfır uzunluklu çubuk atlandı."); return null; }
    const t = vbirim(vfark(o.p2, o.p1));
    const d = o.d;
    const x = vdis(d, t);
    const pt = this.profilTanimi(o.k);
    let bas = o.p1;
    if (o.kardinal === 8) bas = vtop(bas, volc(d, -pt.derinlik / 2));
    const yerel = [bas[0], bas[1], bas[2] - kat.kot];
    const yer = this.yerlesim(kat.yer, yerel, t, x);
    const katilar = [this.uzat(pt.ref, L)];
    if (pt.ek) katilar.push(this.uzat(pt.ek, L));
    const sek = this.sekil(katilar);
    const ref = w.ekle(o.sinif, [this.gid(o.anahtar), null, o.ad, o.aciklama || null, o.k.ad, yer, sek, o.etiket || null, E(o.tip)]);
    kat.elemanlar.push(ref);
    const kul = this.profilKullanimi(o.k, o.kardinal);
    this.malzemeBagla(kul, ref);
    this.ortakPsetler(o.anahtar, ref, o.sinif, o.k, o.ek || {});
    this.fizik[o.anahtar] = ref;
    return ref;
  };

  // ---- yatay dikdörtgen plak / temel katısı (merkez cx, cy; üst kot zUst; kalınlık h) ----
  Uretici.prototype.kutuEleman = function (o) {
    const w = this.w, kat = this.katlar[o.kat] || this.katlar[this.Bm.katlar[0].no];
    const prof = w.ekle("IFCRECTANGLEPROFILEDEF", [E("AREA"), o.profilAd || null, null, o.dx, o.dy]);
    const yer = this.yerlesim(kat.yer, [o.cx, o.cy, o.zUst - o.h - kat.kot]);
    const sek = this.sekil([this.uzat(prof, o.h)]);
    const ref = w.ekle(o.sinif, [this.gid(o.anahtar), null, o.ad, o.aciklama || null, o.nesneTipi || null, yer, sek, o.etiket || null, E(o.tip)]);
    kat.elemanlar.push(ref);
    this.malzemeBagla(this.malzeme(o.malzeme), ref);
    this.ortakPsetler(o.anahtar, ref, o.sinif, null, o.ek || {});
    this.fizik[o.anahtar] = ref;
    return ref;
  };

  // ---- genel düzlemsel çokgen plak (surum 3 paneller) ----
  Uretici.prototype.cokgenEleman = function (o) {
    const w = this.w, kat = this.katlar[o.kat] || this.katlar[this.Bm.katlar[0].no];
    const P = o.noktalar;
    let n = [0, 0, 0];
    for (let i = 0; i < P.length; i++) {          // Newell normali
      const a = P[i], b = P[(i + 1) % P.length];
      n = vtop(n, [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]);
    }
    if (vboy(n) < 1e-9) { this.uyarilar.push(o.ad + ": köşeler bir düzlem tanımlamıyor; atlandı."); return null; }
    n = vbirim(n);
    const yatayMi = Math.abs(n[2]) > 0.2;
    if (yatayMi && n[2] < 0) n = volc(n, -1);
    const x = vbirim(vfark(P[1], P[0]));
    const y = vdis(n, x);
    const o2 = P.map(function (p) { const r = vfark(p, P[0]); return [vic(r, x), vic(r, y)]; });
    const self = this;
    const pts = o2.map(function (p) { return self.nokta2(p); });
    pts.push(pts[0]);
    const egri = w.ekle("IFCPOLYLINE", [pts]);
    const prof = w.ekle("IFCARBITRARYCLOSEDPROFILEDEF", [E("AREA"), o.profilAd || null, egri]);
    const kalin = o.h;
    // yatay plakta üst yüz köşe düzleminde (döşeme üstü = kot); eğik/düşey plakta orta düzlem
    const kay = yatayMi ? -kalin : -kalin / 2;
    const bas = vtop(P[0], volc(n, kay));
    const yer = this.yerlesim(kat.yer, [bas[0], bas[1], bas[2] - kat.kot], n, x);
    const sek = this.sekil([this.uzat(prof, kalin)]);
    const ref = w.ekle(o.sinif, [this.gid(o.anahtar), null, o.ad, o.aciklama || null, o.nesneTipi || null, yer, sek, o.etiket || null, E(o.tip)]);
    kat.elemanlar.push(ref);
    this.malzemeBagla(this.malzeme(o.malzeme), ref);
    this.ortakPsetler(o.anahtar, ref, o.sinif, null, o.ek || {});
    this.fizik[o.anahtar] = ref;
    return ref;
  };

  // ======================================================================
  // Fiziksel model
  // ======================================================================
  Uretici.prototype.fiziksel = function () {
    const Bm = this.Bm, bina = Bm.bina, self = this;
    const sonX = Bm.ax.length - 1, sonY = Bm.ay.length - 1;
    // --- kolonlar (aks–kat) ---
    dizi(bina.kolonlar).forEach(function (c, i) {
      const a = aksXY(Bm, c.aks), kat = c.kat === undefined ? 1 : +c.kat;
      const z0 = katKot(Bm, kat - 1), z1 = katKot(Bm, kat);
      if (!a || z0 === null || z1 === null) { self.uyarilar.push("Kolon " + (c.no || i + 1) + ": aks/kat bulunamadı; atlandı."); return; }
      const no = c.no === undefined ? i + 1 : c.no;
      const k = kesitCoz(Bm, c.kesit, self.uyarilar);
      const yon = String(c.yon || "x").toLowerCase() === "y" ? "y" : "x";
      const adres = c.adres || ("S-" + Bm.ax[a.ix].ad + Bm.ay[a.iy].ad + "/k" + kat);
      self.cubukEleman({ sinif: "IFCCOLUMN", tip: "COLUMN", anahtar: "kolon:" + no, ad: adres, etiket: "S" + no, kat: kat - 1,
        aciklama: "Kolon " + no + " (" + k.ad + ", güçlü eksen " + yon.toUpperCase() + " doğrultusunda)",
        p1: [a.X, a.Y, z0], p2: [a.X, a.Y, z1], d: yon === "x" ? [1, 0, 0] : [0, 1, 0], kardinal: 5, k: k,
        ek: { adres: adres, tur: "kolon", no: no, kat: kat, yon: yon, dis: a.ix === 0 || a.ix === sonX || a.iy === 0 || a.iy === sonY, tasarimTur: "kolon" } });
    });
    // --- kirişler (aks–kat; üstü kat kotunda, aşağı sarkık — 3B çizimle aynı) ---
    dizi(bina.kirisler).forEach(function (kr, i) {
      const a = aksXY(Bm, kr.bas), b = aksXY(Bm, kr.son), kat = kr.kat === undefined ? 1 : +kr.kat, z = katKot(Bm, kat);
      const no = kr.no === undefined ? i + 1 : kr.no;
      if (!a || !b || z === null) { self.uyarilar.push("Kiriş " + no + ": aks/kat bulunamadı; atlandı."); return; }
      let p = a, q = b;
      if (b.ix < a.ix || b.iy < a.iy) { p = b; q = a; }
      const k = kesitCoz(Bm, kr.kesit, self.uyarilar);
      const adres = kr.adres || ("K-" + Bm.ax[p.ix].ad + Bm.ay[p.iy].ad + "→" + Bm.ax[q.ix].ad + Bm.ay[q.iy].ad + "/k" + kat);
      const dis = (p.iy === q.iy && (p.iy === 0 || p.iy === sonY)) || (p.ix === q.ix && (p.ix === 0 || p.ix === sonX));
      const L = vboy(vfark([q.X, q.Y, 0], [p.X, p.Y, 0]));
      self.cubukEleman({ sinif: "IFCBEAM", tip: "BEAM", anahtar: "kiris:" + no, ad: adres, etiket: "K" + no, kat: kat,
        aciklama: "Kiriş " + no + " (" + k.ad + ")" + (kr.duvar ? "; üzerinde duvar: " + kr.duvar : ""),
        p1: [p.X, p.Y, z], p2: [q.X, q.Y, z], d: [0, 0, 1], kardinal: 8, k: k,
        ek: { adres: adres, tur: "kiris", no: no, kat: kat, dis: dis, aciklik: L, tasarimTur: "kiris",
          ozel: kr.duvar ? [["Duvar", T("IFCLABEL", String(kr.duvar))]] : [] } });
    });
    // --- döşemeler (üstü kat kotunda) ---
    const beton = betonMalzeme(Bm);
    dizi(bina.dosemeler).forEach(function (d, i) {
      const no = d.no === undefined ? i + 1 : d.no;
      const kose = dizi(d.kose);
      const a = aksXY(Bm, kose[0]), b = aksXY(Bm, kose[1]), kat = d.kat === undefined ? 1 : +d.kat, z = katKot(Bm, kat);
      if (!a || !b || z === null) { self.uyarilar.push("Döşeme " + no + ": köşe/kat bulunamadı; atlandı."); return; }
      const x0 = Math.min(a.X, b.X), x1 = Math.max(a.X, b.X), y0 = Math.min(a.Y, b.Y), y1 = Math.max(a.Y, b.Y);
      const h = sayi(d.h, 0.12);
      const cati = kat === Bm.nk;
      const adres = d.adres || ("D-" + Bm.ax[Math.min(a.ix, b.ix)].ad + Bm.ay[Math.min(a.iy, b.iy)].ad + "/" + Bm.ax[Math.max(a.ix, b.ix)].ad + Bm.ay[Math.max(a.iy, b.iy)].ad + "/k" + kat);
      self.kutuEleman({ sinif: "IFCSLAB", tip: cati ? "ROOF" : "FLOOR", anahtar: "doseme:" + no, ad: adres, etiket: "D" + no, kat: kat,
        aciklama: "Döşeme " + no + " (h = " + Math.round(h * 100) + " cm, " + (d.kullanim || "konut") + ")",
        nesneTipi: "Plak döşeme", profilAd: "D" + no, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, dx: x1 - x0, dy: y1 - y0, zUst: z, h: h,
        malzeme: beton,
        ek: { adres: adres, tur: "doseme", no: no, kat: kat, dis: cati, referans: "D" + no,
          ozel: [["Kalinlik", T("IFCPOSITIVELENGTHMEASURE", h)], ["Kullanim", d.kullanim ? T("IFCLABEL", d.kullanim) : null],
            ["q", d.q !== null && d.q !== undefined && isFinite(+d.q) ? T("IFCPLANARFORCEMEASURE", +d.q) : null],
            ["g_ek", isFinite(+d.g_ek) && typeof d.g_ek !== "string" ? T("IFCPLANARFORCEMEASURE", +d.g_ek) : (typeof d.g_ek === "string" ? T("IFCLABEL", d.g_ek) : null)],
            ["Dagitim", d.dagitim ? T("IFCLABEL", d.dagitim) : null]] } });
    });
    // --- surum 3: çubuklar ---
    dizi(bina.cubuklar).forEach(function (c, i) {
      const no = c.no === undefined ? i + 1 : c.no;
      const di = self.dug.ref(c.i), dj = self.dug.ref(c.j);
      if (!di || !dj) { self.uyarilar.push("Çubuk " + no + ": uç düğümü çözülemedi; atlandı."); return; }
      const tur = CUBUK_SINIF[c.tur] ? c.tur : "diger";
      const sin = CUBUK_SINIF[tur];
      let p1 = [di.X, di.Y, di.Z], p2 = [dj.X, dj.Y, dj.Z];
      if (tur === "kolon" && p2[2] < p1[2]) { const g = p1; p1 = p2; p2 = g; }
      const t = vbirim(vfark(p2, p1));
      const d = derinlikYonu(t, c.aci);
      const k = kesitCoz(Bm, c.kesit, self.uyarilar);
      const yatay = Math.abs(t[2]) < 1e-6;
      const kat = c.kat !== undefined ? +c.kat : null;
      const zKat = tur === "kolon" ? seviyeBul(Bm, Math.min(p1[2], p2[2])) : (kat !== null && Bm.kat[kat] ? kat : seviyeBul(Bm, Math.max(p1[2], p2[2])));
      const ad = (CUBUK_AD[tur] || "Çubuk") + " Ç" + no + (c.grup ? " (" + c.grup + ")" : "");
      self.cubukEleman({ sinif: sin[0], tip: sin[1], anahtar: "cubuk:" + no, ad: ad, etiket: "C" + no, kat: zKat,
        aciklama: (CUBUK_AD[tur] || "Çubuk") + " " + no + " (" + k.ad + (c.aci ? ", açı " + c.aci + "°" : "") + ")",
        p1: p1, p2: p2, d: d, kardinal: (tur === "kiris" && yatay) ? 8 : 5, k: k,
        ek: { adres: "C" + no, tur: c.tur || "diger", no: no, kat: kat === null ? undefined : kat, aciklik: vboy(vfark(p2, p1)), tasarimTur: "cubuk",
          ozel: [["Aci", c.aci ? T("IFCPLANEANGLEMEASURE", sayi(c.aci, 0) * Math.PI / 180) : null], ["Grup", c.grup ? T("IFCLABEL", c.grup) : null],
            ["YalnizCekme", c.yalniz_cekme ? T("IFCBOOLEAN", true) : null]] } });
    });
    // --- surum 3: paneller ---
    dizi(bina.paneller).forEach(function (p, i) {
      const no = p.no === undefined ? i + 1 : p.no;
      const kos = dizi(p.kose).map(function (r) { return self.dug.ref(r); });
      if (kos.length < 3 || kos.some(function (x) { return !x; })) { self.uyarilar.push("Panel " + no + ": köşeler çözülemedi; atlandı."); return; }
      const P = kos.map(function (x) { return [x.X, x.Y, x.Z]; });
      const tur = String(p.tur || "doseme");
      const h = sayi(p.kalinlik, 0);
      let sinif, tip;
      if (h > 0) {
        if (tur === "cephe") { sinif = "IFCPLATE"; tip = "NOTDEFINED"; } else { sinif = "IFCSLAB"; tip = tur === "cati" ? "ROOF" : "FLOOR"; }
      } else {
        sinif = "IFCCOVERING"; tip = tur === "cephe" ? "CLADDING" : (tur === "cati" ? "ROOFING" : "FLOORING");
      }
      const zmax = Math.max.apply(null, P.map(function (x) { return x[2]; }));
      const ad = { doseme: "Döşeme paneli", cati: "Çatı paneli", cephe: "Cephe paneli" }[tur] || "Panel";
      self.cokgenEleman({ sinif: sinif, tip: tip, anahtar: "panel:" + no, ad: ad + " P" + no, etiket: "P" + no, kat: seviyeBul(Bm, zmax),
        aciklama: h > 0 ? ad + " (t = " + Math.round(h * 1000) / 10 + " cm)" : ad + " (taşıyıcı olmayan kaplama; 1 cm gösterim kalınlığı)",
        noktalar: P, h: h > 0 ? h : 0.01, malzeme: h > 0 ? beton : { ad: "Kaplama (sac)", tur: "celik" }, profilAd: "P" + no,
        ek: { adres: "P" + no, tur: "panel-" + tur, no: no, referans: "P" + no, dis: tur !== "doseme", tasiyici: h > 0,
          ozel: [["Kalinlik", T("IFCLENGTHMEASURE", h)], ["Kullanim", p.kullanim ? T("IFCLABEL", p.kullanim) : null],
            ["Dagitim", p.dagitim ? T("IFCLABEL", p.dagitim) : null]] } });
    });
    this.temeller(beton);
  };

  // ---- temeller (§3 tekil, §13 sürekli / radye) ----
  Uretici.prototype.temeller = function (beton) {
    const Bm = this.Bm, self = this, t = sozluk(Bm.bina.temeller);
    const tip = String(t.tip || "tekil").toLowerCase();
    const z0 = Bm.kot0;
    const tabanlar = this.kolonTabanlari();
    if (tip === "surekli" || tip === "mutemadi") {
      const s = Object.assign({ yon: "xy", akslar: "tum", B: 1.2, h_tabla: 0.4, b_govde: 0.5, h_govde: 1.0, tasma: 0.5 }, sozluk(t.surekli));
      const Bt = sayi(s.B, 1.2), ht = sayi(s.h_tabla, 0.4), bg = sayi(s.b_govde, 0.5), hg = Math.max(sayi(s.h_govde, 1.0), ht);
      const tas = sayi(s.tasma, 0.5);
      const yonlar = String(s.yon || "xy").toLowerCase();
      const secili = function (ad) { return s.akslar === "tum" || !Array.isArray(s.akslar) || s.akslar.map(String).indexOf(String(ad)) >= 0; };
      // ters T kesit: tabla (B × h_tabla) altta, gövde (b_govde) toplam yükseklik h_govde; profil Y yukarı, üst = 0
      const w = this.w;
      const kp = [[-Bt / 2, -hg], [Bt / 2, -hg], [Bt / 2, -hg + ht], [bg / 2, -hg + ht], [bg / 2, 0], [-bg / 2, 0], [-bg / 2, -hg + ht], [-Bt / 2, -hg + ht]];
      const ptsT = (ht > 0 && bg < Bt) ? kp : [[-Math.max(Bt, bg) / 2, -hg], [Math.max(Bt, bg) / 2, -hg], [Math.max(Bt, bg) / 2, 0], [-Math.max(Bt, bg) / 2, 0]];
      const pl = ptsT.map(function (p) { return self.nokta2(p); });
      pl.push(pl[0]);
      const profil = w.ekle("IFCARBITRARYCLOSEDPROFILEDEF", [E("AREA"), "Temel kirişi (ters T) B=" + Bt + " h=" + hg, w.ekle("IFCPOLYLINE", [pl])]);
      const serit = function (anahtar, ad, p1, p2) {
        const kat = self.katlar[Bm.katlar[0].no];
        const tt = vbirim(vfark(p2, p1)), d = [0, 0, 1], x = vdis(d, tt), L = vboy(vfark(p2, p1));
        const yer = self.yerlesim(kat.yer, [p1[0], p1[1], p1[2] - kat.kot], tt, x);
        const ref = w.ekle("IFCFOOTING", [self.gid(anahtar), null, ad, "Mütemadi (sürekli) temel kirişi", "Ters T temel kirişi", yer,
          self.sekil([self.uzat(profil, L)]), null, E("STRIP_FOOTING")]);
        kat.elemanlar.push(ref);
        self.malzemeBagla(self.malzeme(beton), ref);
        self.ortakPsetler(anahtar, ref, "IFCFOOTING", null, { adres: ad, tur: "temel-kirisi", referans: ad,
          ozel: [["B", T("IFCPOSITIVELENGTHMEASURE", Bt)], ["h_tabla", T("IFCLENGTHMEASURE", ht)], ["b_govde", T("IFCPOSITIVELENGTHMEASURE", bg)],
            ["h_govde", T("IFCPOSITIVELENGTHMEASURE", hg)]] });
      };
      const xs = Bm.ax.map(function (a) { return a.konum; }), ys = Bm.ay.map(function (a) { return a.konum; });
      if (yonlar.indexOf("x") >= 0) Bm.ay.forEach(function (a) {      // X yönünde: sayılı aks çizgileri boyunca
        if (!secili(a.ad)) return;
        serit("temel-x:" + a.ad, "TK-" + a.ad, [xs[0] - tas, a.konum, z0], [xs[xs.length - 1] + tas, a.konum, z0]);
      });
      if (yonlar.indexOf("y") >= 0) Bm.ax.forEach(function (a) {      // Y yönünde: harfli aks çizgileri boyunca
        if (!secili(a.ad)) return;
        serit("temel-y:" + a.ad, "TK-" + a.ad, [a.konum, ys[0] - tas, z0], [a.konum, ys[ys.length - 1] + tas, z0]);
      });
      return;
    }
    if (tip === "radye") {
      const r = Object.assign({ h: 0.8, tasma: 1.0, kiris: null }, sozluk(t.radye));
      const h = sayi(r.h, 0.8), tas = sayi(r.tasma, 1.0);
      const xs = Bm.ax.map(function (a) { return a.konum; }), ys = Bm.ay.map(function (a) { return a.konum; });
      const x0 = xs[0] - tas, x1 = xs[xs.length - 1] + tas, y0 = ys[0] - tas, y1 = ys[ys.length - 1] + tas;
      this.kutuEleman({ sinif: "IFCSLAB", tip: "BASESLAB", anahtar: "radye", ad: "Radye temel", etiket: "R", kat: Bm.katlar[0].no,
        aciklama: "Radye (plak) temel, h = " + h + " m", nesneTipi: "Radye", profilAd: "Radye",
        cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, dx: x1 - x0, dy: y1 - y0, zUst: z0, h: h, malzeme: beton,
        ek: { adres: "Radye", tur: "radye", referans: "Radye", dis: true, ozel: [["Kalinlik", T("IFCPOSITIVELENGTHMEASURE", h)]] } });
      if (r.kiris && sayi(r.kiris.b, 0) > 0 && sayi(r.kiris.h, 0) > 0) {
        const k = { ad: "Radye kirişi " + r.kiris.b + "x" + r.kiris.h, tur: "dikdortgen", b: +r.kiris.b, h: +r.kiris.h, malzeme: beton.anahtar };
        const kiris = function (anahtar, ad, p1, p2) {
          self.cubukEleman({ sinif: "IFCFOOTING", tip: "FOOTING_BEAM", anahtar: anahtar, ad: ad, kat: Bm.katlar[0].no, aciklama: "Kirişli radye: temel kirişi",
            p1: p1, p2: p2, d: [0, 0, 1], kardinal: 8, k: k, ek: { adres: ad, tur: "radye-kirisi" } });
        };
        Bm.ay.forEach(function (a) { kiris("radye-kiris-x:" + a.ad, "RK-" + a.ad, [xs[0], a.konum, z0], [xs[xs.length - 1], a.konum, z0]); });
        Bm.ax.forEach(function (a) { kiris("radye-kiris-y:" + a.ad, "RK-" + a.ad, [a.konum, ys[0], z0], [a.konum, ys[ys.length - 1], z0]); });
      }
      return;
    }
    // tekil (varsayılan): her kolon tabanının altında B (X) × L (Y) × h, üstü temel kotunda
    const vars = Object.assign({ B: 1.5, L: 1.5, h: 0.6 }, sozluk(t.varsayilan));
    const ozel = {};
    dizi(t.ozel).concat(dizi(t.liste)).forEach(function (o) { if (o && o.aks) ozel[String(o.aks[0]) + "|" + String(o.aks[1])] = o; });
    const h = sayi(vars.h, 0.6);
    tabanlar.forEach(function (tb) {
      const o = ozel[tb.anahtarAks] || {};
      const Bt = sayi(o.B, sayi(vars.B, 1.5)), Lt = sayi(o.L, sayi(vars.L, 1.5));
      self.kutuEleman({ sinif: "IFCFOOTING", tip: "PAD_FOOTING", anahtar: "temel:" + tb.anahtar, ad: "T-" + tb.ad, etiket: "T" + tb.ad,
        kat: Bm.katlar[0].no, aciklama: "Tekil temel " + Bt + " × " + Lt + " × " + h + " m", nesneTipi: "Tekil temel", profilAd: "T" + Bt + "x" + Lt,
        cx: tb.X, cy: tb.Y, dx: Bt, dy: Lt, zUst: tb.Z, h: h, malzeme: beton,
        ek: { adres: "T-" + tb.ad, tur: "tekil-temel", referans: "T-" + tb.ad,
          ozel: [["B", T("IFCPOSITIVELENGTHMEASURE", Bt)], ["L", T("IFCPOSITIVELENGTHMEASURE", Lt)], ["h", T("IFCPOSITIVELENGTHMEASURE", h)]] } });
    });
  };
  // Temel seviyesine inen kolonların taban noktaları (aks–kat kolonları + surum 3 kolon çubukları)
  Uretici.prototype.kolonTabanlari = function () {
    const Bm = this.Bm, self = this, sonuc = [], gor = {};
    dizi(Bm.bina.kolonlar).forEach(function (c) {
      if ((c.kat === undefined ? 1 : +c.kat) !== 1) return;
      const a = aksXY(Bm, c.aks);
      if (!a) return;
      const ad = Bm.ax[a.ix].ad + Bm.ay[a.iy].ad;
      if (gor[ad]) return;
      gor[ad] = true;
      sonuc.push({ anahtar: ad, anahtarAks: Bm.ax[a.ix].ad + "|" + Bm.ay[a.iy].ad, ad: ad, X: a.X, Y: a.Y, Z: Bm.kot0 });
    });
    dizi(Bm.bina.cubuklar).forEach(function (c) {
      if (c.tur !== "kolon") return;
      const di = self.dug.ref(c.i), dj = self.dug.ref(c.j);
      if (!di || !dj) return;
      const alt = di.Z <= dj.Z ? di : dj;
      if (Math.abs(alt.Z - Bm.kot0) > 1e-3) return;
      const ad = alt.ad && alt.ad.indexOf("/k0") > 0 ? alt.ad.replace("/k0", "") : "N" + alt.no;
      if (gor[ad]) return;
      gor[ad] = true;
      let anahtarAks = "";
      Bm.ax.forEach(function (x) { Bm.ay.forEach(function (y) { if (Math.abs(x.konum - alt.X) < 1e-3 && Math.abs(y.konum - alt.Y) < 1e-3) anahtarAks = x.ad + "|" + y.ad; }); });
      sonuc.push({ anahtar: ad, anahtarAks: anahtarAks, ad: ad, X: alt.X, Y: alt.Y, Z: alt.Z });
    });
    return sonuc;
  };

  // ======================================================================
  // Yapısal analiz modeli
  // ======================================================================
  // Analiz ağı: veri.ag varsa ondan; yoksa bina JSON'dan (aks–kat kolon/kiriş parçaları + surum 3 çubuklar)
  Uretici.prototype.analizAgi = function () {
    const Bm = this.Bm, self = this, dug = this.dug;
    const elemanlar = [], mesnetler = [];
    const kolonNo = {}, kirisNo = {}, cubukNo = {};
    dizi(Bm.bina.kolonlar).forEach(function (c, i) { kolonNo[c.no === undefined ? i + 1 : c.no] = c; });
    dizi(Bm.bina.kirisler).forEach(function (k, i) { kirisNo[k.no === undefined ? i + 1 : k.no] = k; });
    dizi(Bm.bina.cubuklar).forEach(function (c, i) { cubukNo[c.no === undefined ? i + 1 : c.no] = c; });
    const kaynakBilgi = function (tur, no) {
      if (tur === "kolon" && kolonNo[no]) return { kesit: kolonNo[no].kesit, yon: String(kolonNo[no].yon || "x").toLowerCase() };
      if (tur === "kiris" && kirisNo[no]) return { kesit: kirisNo[no].kesit };
      if (cubukNo[no]) return { kesit: cubukNo[no].kesit, aci: cubukNo[no].aci, serbest: cubukNo[no].serbest, yalniz_cekme: cubukNo[no].yalniz_cekme, tur: cubukNo[no].tur };
      return {};
    };
    if (Bm.ag) {
      const efendi = {};
      Bm.ag.dugumler.forEach(function (d) {
        if (d.efendi) { efendi[d.no] = true; return; }
        dug.ekle(+d.no, sayi(d.X, 0), sayi(d.Y, 0), sayi(d.Z, 0), d.adres || ("N" + d.no));
      });
      Bm.ag.elemanlar.forEach(function (e) {
        const kay = sozluk(e.kaynak);
        const tur = e.tur || kay.tur || "diger";
        const kno = e.kaynak_no !== undefined ? e.kaynak_no : kay.no;
        const kb = kaynakBilgi(kay.tur === "cubuk" ? "cubuk" : tur, kno);
        const dd = dizi(e.dugumler);
        if (dd.length < 2 || efendi[dd[0]] || efendi[dd[1]]) return;
        elemanlar.push({ no: e.no, i: dug.no[dd[0]], j: dug.no[dd[1]], tur: tur, kaynakTur: kay.tur === "cubuk" ? "cubuk" : tur, kaynakNo: kno,
          parca: e.parca, kesit: e.kesit || kb.kesit, yon: kb.yon, aci: e.aci !== undefined ? e.aci : kb.aci, serbest: e.serbest || kb.serbest,
          yalniz_cekme: e.yalniz_cekme || kb.yalniz_cekme, adres: e.adres });
      });
      const tem = sozluk(Bm.bina.temeller);
      const k0 = sayi(sozluk(tem.zemin).k0, 20000);
      const tbl = {};
      dizi(tem.liste).concat(dizi(tem.ozel)).forEach(function (o) { if (o && o.aks) tbl[o.aks[0] + "|" + o.aks[1]] = o; });
      dizi(Bm.ag.mesnetler).forEach(function (m) {
        const d = dug.no[m.dugum];
        if (!d) return;
        if (m.ux !== undefined || m.rx !== undefined) { mesnetler.push({ d: d, serbestlik: m }); return; }
        const ag = Bm.ag.dugumler.filter(function (x) { return x.no === m.dugum; })[0] || {};
        const o = ag.aks ? (tbl[ag.aks[0] + "|" + ag.aks[1]] || {}) : {};
        const v = sozluk(tem.varsayilan);
        mesnetler.push({ d: d, tip: m.tip || tem.mesnet || "ankastre", B: sayi(m.B, sayi(o.B, sayi(v.B, 1.5))), L: sayi(m.L, sayi(o.L, sayi(v.L, 1.5))), k0: k0 });
      });
    } else {
      let eno = 0;
      dizi(Bm.bina.kolonlar).slice().sort(function (a, b) { return (a.kat - b.kat) || (a.no - b.no); }).forEach(function (c) {
        const a = aksXY(Bm, c.aks), kat = c.kat === undefined ? 1 : +c.kat;
        if (!a) return;
        const i = dug.aksDugum(a.ix, a.iy, kat - 1), j = dug.aksDugum(a.ix, a.iy, kat);
        if (!i || !j) return;
        eno += 1;
        elemanlar.push({ no: eno, i: i, j: j, tur: "kolon", kaynakTur: "kolon", kaynakNo: c.no, parca: 1, kesit: c.kesit, yon: String(c.yon || "x").toLowerCase() });
      });
      dizi(Bm.bina.kirisler).slice().sort(function (a, b) { return (a.kat - b.kat) || (a.no - b.no); }).forEach(function (k) {
        const a = aksXY(Bm, k.bas), b = aksXY(Bm, k.son), kat = k.kat === undefined ? 1 : +k.kat;
        if (!a || !b) return;
        let parca = 0;
        if (a.iy === b.iy) {
          for (let ix = Math.min(a.ix, b.ix); ix < Math.max(a.ix, b.ix); ix++) {
            eno += 1; parca += 1;
            elemanlar.push({ no: eno, i: dug.aksDugum(ix, a.iy, kat), j: dug.aksDugum(ix + 1, a.iy, kat), tur: "kiris", kaynakTur: "kiris", kaynakNo: k.no, parca: parca, kesit: k.kesit });
          }
        } else if (a.ix === b.ix) {
          for (let iy = Math.min(a.iy, b.iy); iy < Math.max(a.iy, b.iy); iy++) {
            eno += 1; parca += 1;
            elemanlar.push({ no: eno, i: dug.aksDugum(a.ix, iy, kat), j: dug.aksDugum(a.ix, iy + 1, kat), tur: "kiris", kaynakTur: "kiris", kaynakNo: k.no, parca: parca, kesit: k.kesit });
          }
        }
      });
      dizi(Bm.bina.cubuklar).forEach(function (c, n) {
        const i = dug.ref(c.i), j = dug.ref(c.j);
        if (!i || !j) return;
        eno += 1;
        elemanlar.push({ no: eno, i: i, j: j, tur: c.tur || "diger", kaynakTur: "cubuk", kaynakNo: c.no === undefined ? n + 1 : c.no, parca: 1, kesit: c.kesit,
          aci: c.aci, serbest: c.serbest, yalniz_cekme: c.yalniz_cekme });
      });
      const tem = sozluk(Bm.bina.temeller);
      const v = sozluk(tem.varsayilan), k0 = sayi(sozluk(tem.zemin).k0, 20000);
      const tbl = {};
      dizi(tem.ozel).concat(dizi(tem.liste)).forEach(function (o) { if (o && o.aks) tbl[o.aks[0] + "|" + o.aks[1]] = o; });
      const tabanda = {};
      elemanlar.forEach(function (e) {
        [e.i, e.j].forEach(function (d) {
          if (!d || Math.abs(d.Z - Bm.kot0) > 1e-3 || tabanda[d.no]) return;
          tabanda[d.no] = true;
          let o = {};
          Bm.ax.forEach(function (x) { Bm.ay.forEach(function (y) { if (Math.abs(x.konum - d.X) < 1e-3 && Math.abs(y.konum - d.Y) < 1e-3) o = tbl[x.ad + "|" + y.ad] || {}; }); });
          mesnetler.push({ d: d, tip: String(tem.mesnet || "ankastre"), B: sayi(o.B, sayi(v.B, 1.5)), L: sayi(o.L, sayi(v.L, 1.5)), k0: k0 });
        });
      });
    }
    // surum 3 serbest düğüm mesnetleri (aks–kat temel kuralına ek)
    dizi(Bm.bina.mesnetler).forEach(function (m) {
      const d = dug.ref(m.dugum);
      if (!d) return;
      for (let i = mesnetler.length - 1; i >= 0; i--) if (mesnetler[i].d === d) mesnetler.splice(i, 1);
      mesnetler.push({ d: d, serbestlik: m });
    });
    elemanlar.forEach(function (e) {
      const t = vbirim(vfark([e.j.X, e.j.Y, e.j.Z], [e.i.X, e.i.Y, e.i.Z]));
      if (e.tur === "kolon" && e.yon) e.d = e.yon === "y" ? [0, 1, 0] : [1, 0, 0];
      else e.d = derinlikYonu(t, e.aci);
      e.t = t;
    });
    return { elemanlar: elemanlar.filter(function (e) { return e.i && e.j && e.i !== e.j; }), mesnetler: mesnetler };
  };

  Uretici.prototype.yapisal = function () {
    const w = this.w, Bm = this.Bm, self = this;
    const ag = this.analizAgi();
    if (!ag.elemanlar.length) { this.uyarilar.push("Analiz modelinde çubuk yok; IfcStructuralAnalysisModel yazılmadı."); return; }
    const yer = this.yerlesim(this.yBina, [0, 0, 0]);
    this.yYapisal = yer;
    const dugumler = {};
    ag.elemanlar.forEach(function (e) { dugumler[e.i.no] = e.i; dugumler[e.j.no] = e.j; });
    // mesnet koşulları
    const kosullar = {};
    const kosul = function (anahtar, ad, tx, ty, tz, rx, ry, rz) {
      if (!kosullar[anahtar]) {
        const v = function (x) { return typeof x === "boolean" ? T("IFCBOOLEAN", x) : (x === null ? null : T(x[0], x[1])); };
        kosullar[anahtar] = w.ekle("IFCBOUNDARYNODECONDITION", [ad, v(tx), v(ty), v(tz), v(rx), v(ry), v(rz)]);
      }
      return kosullar[anahtar];
    };
    const mesnetKosulu = {};
    ag.mesnetler.forEach(function (m) {
      let ref;
      if (m.serbestlik) {
        const s = m.serbestlik, b = function (a) { return !!s[a]; };
        ref = kosul("S" + ["ux", "uy", "uz", "rx", "ry", "rz"].map(function (a) { return b(a) ? 1 : 0; }).join(""), "Mesnet",
          b("ux"), b("uy"), b("uz"), b("rx"), b("ry"), b("rz"));
      } else if (m.tip === "mafsal") {
        ref = kosul("mafsal", "Mafsal (ux, uy, uz tutulu)", true, true, true, false, false, false);
      } else if (m.tip === "elastik") {
        const kz = m.k0 * m.B * m.L, krx = m.k0 * m.B * Math.pow(m.L, 3) / 12, kry = m.k0 * m.L * Math.pow(m.B, 3) / 12;
        ref = kosul("el:" + R(kz) + R(krx) + R(kry), "Elastik zemin (k0 = " + m.k0 + " kN/m³, " + m.B + " × " + m.L + " m)",
          true, true, ["IFCLINEARSTIFFNESSMEASURE", kz], ["IFCROTATIONALSTIFFNESSMEASURE", krx], ["IFCROTATIONALSTIFFNESSMEASURE", kry], true);
      } else {
        ref = kosul("ankastre", "Ankastre", true, true, true, true, true, true);
      }
      mesnetKosulu[m.d.no] = ref;
    });
    // düğümler → IfcStructuralPointConnection (paylaşılan IfcVertexPoint)
    const tepe = {}, baglanti = {};
    const uyeler = [];
    Object.keys(dugumler).map(Number).sort(function (a, b) { return a - b; }).forEach(function (no) {
      const d = dugumler[no];
      const vp = w.ekle("IFCVERTEXPOINT", [self.nokta([d.X, d.Y, d.Z])]);
      tepe[no] = vp;
      const rep = w.ekle("IFCTOPOLOGYREPRESENTATION", [self.ctxRef, "Reference", "Vertex", [vp]]);
      const sek = w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [rep]]);
      baglanti[no] = w.ekle("IFCSTRUCTURALPOINTCONNECTION", [self.gid("yd:" + no), null, d.ad || ("N" + no), mesnetKosulu[no] ? "Mesnet düğümü" : null,
        null, yer, sek, mesnetKosulu[no] || null, null]);
      uyeler.push(baglanti[no]);
    });
    // çubuklar → IfcStructuralCurveMember
    this.yapisalUye = {};
    const fizikIliski = {};
    ag.elemanlar.forEach(function (e) {
      const ed = w.ekle("IFCEDGE", [tepe[e.i.no], tepe[e.j.no]]);
      const rep = w.ekle("IFCTOPOLOGYREPRESENTATION", [self.ctxRef, "Reference", "Edge", [ed]]);
      const sek = w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [rep]]);
      const sb = sozluk(e.serbest);
      const mafsalli = function (u) { const s = dizi(sb[u]); return s.indexOf("My") >= 0 && s.indexOf("Mz") >= 0; };
      let tip = "RIGID_JOINED_MEMBER";
      if (e.yalniz_cekme) tip = "TENSION_MEMBER";
      else if (mafsalli("i") && mafsalli("j")) tip = "PIN_JOINED_MEMBER";
      const ad = (e.adres || ((CUBUK_AD[e.tur] || "Çubuk") + " " + e.kaynakNo + (e.parca > 1 || e.tur === "kiris" ? " / parça " + e.parca : ""))) + " [E" + e.no + "]";
      const uye = w.ekle("IFCSTRUCTURALCURVEMEMBER", [self.gid("yc:" + e.no), null, ad, e.kesit ? "Kesit " + e.kesit : null, null, yer, sek, E(tip), self.yon(e.d)]);
      self.yapisalUye[e.no] = { ref: uye, e: e };
      uyeler.push(uye);
      if (e.kesit) {
        const k = kesitCoz(Bm, e.kesit, []);
        self.malzemeBagla(self.profilKullanimi(k, 5), uye);
      }
      // uç bağlantıları ve serbestlikleri (yerel x′ = çubuk, y′ = derinlik, z′ = x′ × y′)
      [["i", e.i], ["j", e.j]].forEach(function (uc) {
        const s = dizi(sb[uc[0]]);
        let kos = null, ks = null;
        if (s.length) {
          const tut = function (a) { return T("IFCBOOLEAN", s.indexOf(a) < 0); };
          kos = w.ekle("IFCBOUNDARYNODECONDITION", ["Uç serbestliği (" + s.join(", ") + ")", tut("N"), tut("Vy"), tut("Vz"), tut("T"), tut("My"), tut("Mz")]);
          ks = self.eksen3([uc[1].X, uc[1].Y, uc[1].Z], vdis(e.t, e.d), e.t);
        }
        w.ekle("IFCRELCONNECTSSTRUCTURALMEMBER", [self.gid("ycb:" + e.no + ":" + uc[0]), null, null, null, uye, baglanti[uc[1].no], kos, null, null, ks]);
      });
      const fk = (e.kaynakTur || e.tur) + ":" + e.kaynakNo;
      if (self.fizik[fk]) (fizikIliski[fk] = fizikIliski[fk] || []).push(uye);
    });
    // fiziksel eleman ↔ analitik üye
    Object.keys(fizikIliski).forEach(function (fk) {
      w.ekle("IFCRELASSIGNSTOPRODUCT", [self.gid("rel:analitik:" + fk), null, null, null, fizikIliski[fk], null, self.fizik[fk]]);
    });
    // yük grupları ve birleşimler
    const gruplar = this.yukGruplari();
    this.model = w.ekle("IFCSTRUCTURALANALYSISMODEL", [this.gid("analiz-modeli"), null, Bm.baslik + " — analiz modeli",
      "Sonlu eleman çubuk modeli (12 SD/eleman, Kassimali yerel eksenleri); bina koordinatı X, Y, Z (Z yukarı)", null, E("LOADING_3D"), null,
      gruplar.length ? gruplar : null, null, yer]);
    w.ekle("IFCRELASSIGNSTOGROUP", [this.gid("rel:model-uyeler"), null, null, null, uyeler, null, this.model]);
    w.ekle("IFCRELSERVICESBUILDINGS", [this.gid("rel:model-bina"), null, null, null, this.model, [this.yapi]]);
    if (this.s.yukler !== false) this.yukler(baglanti);
  };

  function eylemTipi(ad) {
    const a = String(ad);
    if (a === "G" || a.indexOf("G~") === 0) return ["PERMANENT_G", "DEAD_LOAD_G", "Sabit yük (G)"];
    if (a === "Q") return ["VARIABLE_Q", "LIVE_LOAD_Q", "Hareketli yük (Q)"];
    if (a === "S") return ["VARIABLE_Q", "SNOW_S", "Kar yükü (S)"];
    if (a[0] === "W") return ["VARIABLE_Q", "WIND_W", "Rüzgâr yükü (" + a + ")"];
    if (a[0] === "E") return ["EXTRAORDINARY_A", "EARTHQUAKE_E", "Deprem etkisi (" + a + ")"];
    if (a === "T") return ["VARIABLE_Q", "TEMPERATURE_T", "Sıcaklık / büzülme / oturma (T)"];
    if (a === "K") return ["VARIABLE_Q", "NOTDEFINED", "Kren yükü (K)"];
    return ["NOTDEFINED", "NOTDEFINED", a];
  }
  Uretici.prototype.yukGruplari = function () {
    const w = this.w, Bm = this.Bm, self = this, veri = Bm.veri;
    const durumlar = [];
    const ekle = function (ad) { if (ad && durumlar.indexOf(ad) < 0) durumlar.push(ad); };
    ekle("G"); ekle("Q");
    const birlesimler = [];
    if (veri) {
      Object.keys(sozluk(veri.durumlar)).forEach(ekle);
      dizi(veri.kombinasyonlar).forEach(function (k) {
        if (!k || !k.uygulandi || k.tur === "drift") return;
        Object.keys(sozluk(k.katsayilar)).forEach(ekle);
        birlesimler.push(k);
      });
    } else {
      const yd = sozluk(Bm.bina.yuk_durumlari);
      if (sozluk(yd.S).acik) ekle("S");
      if (sozluk(yd.W).acik) ekle("W");
      if (sozluk(yd.E).acik || sozluk(Bm.bina.deprem).etkin) ekle("E");
    }
    this.durumRef = {};
    const liste = [];
    durumlar.forEach(function (ad) {
      const et = eylemTipi(ad);
      const r = w.ekle("IFCSTRUCTURALLOADCASE", [self.gid("yd:durum:" + ad), null, ad, et[2], null, E("LOAD_CASE"), E(et[0]), E(et[1]), 1.0, null, null]);
      self.durumRef[ad] = r;
      liste.push(r);
    });
    birlesimler.forEach(function (k) {
      const amac = k.tur === "servis" ? "SLS" : (k.tur === "deprem" ? "ULS (deprem)" : "ULS");
      const r = w.ekle("IFCSTRUCTURALLOADGROUP", [self.gid("yd:birlesim:" + k.ad), null, k.ad, k.kaynak || null, null, E("LOAD_COMBINATION"),
        E("NOTDEFINED"), E("NOTDEFINED"), 1.0, amac]);
      liste.push(r);
      Object.keys(sozluk(k.katsayilar)).forEach(function (d) {
        const f = +k.katsayilar[d];
        if (!isFinite(f) || !self.durumRef[d]) return;
        w.ekle("IFCRELASSIGNSTOGROUPBYFACTOR", [self.gid("rel:birlesim:" + k.ad + ":" + d), null, null, null, [self.durumRef[d]], null, r, f]);
      });
    });
    return liste;
  };

  // G ve Q yüklerini veri'den yeniden kur: kiriş parçasına (yayılı, kN/m, aşağı +) ve düğüme (tekil) — yalnız veri varsa
  Uretici.prototype.yukler = function (baglanti) {
    const Bm = this.Bm, veri = Bm.veri, w = this.w, self = this;
    if (!veri || !veri.yukler) return;
    const Y = veri.yukler;
    const yayili = {};     // eleman no → {G: [şekil], Q: [şekil]}; şekil = [[x1, x2, w1, w2], ...] (kN/m, aşağı +)
    const ekle = function (eno, durum, sekil) {
      const r = yayili[eno] = yayili[eno] || { G: [], Q: [] };
      r[durum].push(sekil);
    };
    const parcaElemanlari = {};   // kiriş no → [{eleman, L}]
    Object.keys(this.yapisalUye).forEach(function (no) {
      const e = self.yapisalUye[no].e;
      if (e.tur !== "kiris") return;
      (parcaElemanlari[e.kaynakNo] = parcaElemanlari[e.kaynakNo] || []).push({ no: +no, L: vboy(vfark([e.j.X, e.j.Y, e.j.Z], [e.i.X, e.i.Y, e.i.Z])) });
    });
    dizi(Y.kirisler).forEach(function (r) {
      const kn = sozluk(r.kN_m);
      const g = sayi(kn.oz, 0) + sayi(kn.duvar, 0) + sayi(kn.ek_G, 0), q = sayi(kn.ek_Q, 0);
      dizi(parcaElemanlari[r.no]).forEach(function (p) {
        if (g) ekle(p.no, "G", [[0, p.L, g, g]]);
        if (q) ekle(p.no, "Q", [[0, p.L, q, q]]);
      });
    });
    dizi(Y.dosemeler).forEach(function (d) {
      dizi(d.paylar).forEach(function (p) {
        if (!self.yapisalUye[p.eleman]) return;
        const pb = dizi(p.parcalar_birim);
        if (!pb.length) return;
        if (sayi(p.tepe_g, 0)) ekle(p.eleman, "G", pb.map(function (s) { return [s[0], s[1], s[2] * p.tepe_g, s[3] * p.tepe_g]; }));
        if (sayi(p.tepe_q, 0)) ekle(p.eleman, "Q", pb.map(function (s) { return [s[0], s[1], s[2] * p.tepe_q, s[3] * p.tepe_q]; }));
      });
    });
    const atananlar = { G: [], Q: [] };
    const fdeger = function (sekil, x) {
      for (let i = 0; i < sekil.length; i++) {
        const s = sekil[i];
        if (x >= s[0] - 1e-9 && x <= s[1] + 1e-9) return s[1] - s[0] > 1e-12 ? s[2] + (s[3] - s[2]) * (x - s[0]) / (s[1] - s[0]) : s[2];
      }
      return 0;
    };
    Object.keys(yayili).map(Number).sort(function (a, b) { return a - b; }).forEach(function (eno) {
      ["G", "Q"].forEach(function (durum) {
        const sekiller = yayili[eno][durum];
        if (!sekiller.length || !self.durumRef[durum]) return;
        const xs = [];
        sekiller.forEach(function (sk) { sk.forEach(function (s) { xs.push(s[0], s[1]); }); });
        const kirik = xs.map(function (x) { return Math.round(x * 1e6) / 1e6; }).sort(function (a, b) { return a - b; })
          .filter(function (x, i, a) { return i === 0 || x - a[i - 1] > 1e-6; });
        const deg = kirik.map(function (x) { return sekiller.reduce(function (t, sk) { return t + fdeger(sk, x); }, 0); });
        const uye = self.yapisalUye[eno].ref;
        let eylem;
        const ad = durum + " / E" + eno;
        if (deg.every(function (v) { return Math.abs(v - deg[0]) < 1e-9; })) {
          const yk = w.ekle("IFCSTRUCTURALLOADLINEARFORCE", [ad, null, null, -deg[0], null, null, null]);
          eylem = w.ekle("IFCSTRUCTURALLINEARACTION", [self.gid("ye:" + durum + ":" + eno), null, ad, "Düzgün yayılı yük (kN/m)", null, self.yYapisal, null,
            yk, E("GLOBAL_COORDS"), null, E("TRUE_LENGTH"), E("CONST")]);
        } else {
          const yukler = deg.map(function (v, i) { return w.ekle("IFCSTRUCTURALLOADLINEARFORCE", [ad + " @" + R(kirik[i]), null, null, -v, null, null, null]); });
          const yap = w.ekle("IFCSTRUCTURALLOADCONFIGURATION", [ad, yukler, kirik.map(function (x) { return [x]; })]);
          eylem = w.ekle("IFCSTRUCTURALCURVEACTION", [self.gid("ye:" + durum + ":" + eno), null, ad, "Parçalı doğrusal yayılı yük (TS 500 45° dağıtımı dahil, kN/m)",
            null, self.yYapisal, null, yap, E("GLOBAL_COORDS"), null, E("TRUE_LENGTH"), E("POLYGONAL")]);
        }
        w.ekle("IFCRELCONNECTSSTRUCTURALACTIVITY", [self.gid("rel:ye:" + durum + ":" + eno), null, null, null, uye, eylem]);
        atananlar[durum].push(eylem);
      });
    });
    // tekil düğüm yükleri: kolon öz ağırlığı (G, üst düğüm) ve ek düğüm yükleri
    const tekil = {};     // "durum|dugum" → [FX, FY, FZ, MX, MY, MZ]
    const tekilEkle = function (durum, dno, v) {
      if (!baglanti[dno] || !self.durumRef[durum]) return;
      const a = durum + "|" + dno, r = tekil[a] = tekil[a] || [0, 0, 0, 0, 0, 0];
      for (let i = 0; i < 6; i++) r[i] += v[i];
    };
    const kolonUst = {};
    Object.keys(this.yapisalUye).forEach(function (no) {
      const e = self.yapisalUye[no].e;
      if (e.tur === "kolon") kolonUst[e.kaynakNo] = e.j.Z >= e.i.Z ? e.j.no : e.i.no;
    });
    dizi(Y.kolonlar).forEach(function (c) {
      if (kolonUst[c.no] !== undefined && sayi(c.oz_kN, 0)) tekilEkle("G", kolonUst[c.no], [0, 0, -c.oz_kN, 0, 0, 0]);
    });
    dizi(Bm.bina.ek_yukler).forEach(function (y) {
      if (!y || y.tur !== "dugum") return;
      let d = null;
      if (y.dugum !== undefined) d = self.dug.ref(y.dugum);
      else {
        const a = aksXY(Bm, y.aks);
        if (a) d = self.dug.no[aksDugumNo(y.kat === undefined ? 1 : +y.kat, a.ix, a.iy)];
      }
      if (!d) return;
      tekilEkle(String(y.durum || "G").toUpperCase(), d.no, ["FX", "FY", "FZ", "MX", "MY", "MZ"].map(function (a) { return sayi(y[a], 0); }));
    });
    Object.keys(tekil).sort().forEach(function (a) {
      const p = a.split("|"), durum = p[0], dno = +p[1], v = tekil[a];
      const ad = durum + " / N" + dno;
      const yk = w.ekle("IFCSTRUCTURALLOADSINGLEFORCE", [ad, v[0], v[1], v[2], v[3], v[4], v[5]]);
      const eylem = w.ekle("IFCSTRUCTURALPOINTACTION", [self.gid("yt:" + a), null, ad, "Tekil düğüm yükü (kN, kN·m)", null, self.yYapisal, null, yk,
        E("GLOBAL_COORDS"), null]);
      w.ekle("IFCRELCONNECTSSTRUCTURALACTIVITY", [self.gid("rel:yt:" + a), null, null, null, baglanti[dno], eylem]);
      (atananlar[durum] = atananlar[durum] || []).push(eylem);
    });
    Object.keys(atananlar).forEach(function (durum) {
      if (!atananlar[durum].length || !self.durumRef[durum]) return;
      w.ekle("IFCRELASSIGNSTOGROUP", [self.gid("rel:durum-yukler:" + durum), null, null, null, atananlar[durum], null, self.durumRef[durum]]);
    });
  };

  // ---- bitiş: kat içerme ve malzeme ilişkileri ----
  Uretici.prototype.bitir = function () {
    const w = this.w, self = this;
    Object.keys(this.katlar).forEach(function (no) {
      const k = self.katlar[no];
      if (k.elemanlar.length) w.ekle("IFCRELCONTAINEDINSPATIALSTRUCTURE", [self.gid("rel:kat-icerik:" + no), null, null, null, k.elemanlar, k.ref]);
    });
    Object.keys(this.malzIliski).forEach(function (m) {
      w.ekle("IFCRELASSOCIATESMATERIAL", [self.gid("rel:malzeme:" + m), null, null, null, self.malzIliski[m], m]);
    });
  };

  Uretici.prototype.metin = function () {
    const proje = sozluk(this.s.proje);
    let zaman = this.s.zaman || this.s.tarih;
    if (!zaman) {
      const d = new Date();
      zaman = d.toISOString().slice(0, 19);
    }
    const ad = this.s.dosya_adi || dosyaAdi(this.Bm.bina);
    const bas = [
      "ISO-10303-21;",
      "HEADER;",
      "FILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2, StructuralAnalysisView]'),'2;1');",
      "FILE_NAME(" + [S(ad), S(String(zaman).slice(0, 19)), "(" + S(proje.hazirlayan || "") + ")", "(" + S(proje.kurum || "") + ")",
        S(UYGULAMA), S("Matris Öğren"), S("")].join(",") + ");",
      "FILE_SCHEMA(('IFC4'));",
      "ENDSEC;",
      "DATA;",
    ];
    return bas.concat(this.w.satirlar, ["ENDSEC;", "END-ISO-10303-21;", ""]).join("\n");
  };

  function uretAyrintili(bina, veri, secenek) {
    if ((!bina || typeof bina !== "object") && veri && veri.bina) bina = veri.bina;
    if (typeof bina === "string") bina = JSON.parse(bina);
    if (!bina || typeof bina !== "object") throw new Error("MatrisIFC.uret: bina modeli (sözlük) gerekli.");
    const U = new Uretici(bina, veri || null, secenek);
    U.dug = new DugumKumesi(U.Bm);
    U.basla();
    U.fiziksel();
    if (U.s.analiz !== false) U.yapisal();
    U.bitir();
    return { metin: U.metin(), uyarilar: U.uyarilar, sayac: Object.assign({}, U.w.sayac), dosya_adi: U.s.dosya_adi || dosyaAdi(bina) };
  }
  function uret(bina, veri, secenek) { return uretAyrintili(bina, veri, secenek).metin; }

  return { uret: uret, uretAyrintili: uretAyrintili, dosyaAdi: dosyaAdi, globalId: globalId, stepMetin: stepMetin, PROFILLER: PROFILLER, SURUM: SURUM };
});
