/* Matris Öğren — IFC dışa aktarım (IFC4, ISO 10303-21 STEP fiziksel dosya; tasarım belgesi §14.2).
   window.MatrisIFC = {
     uret(bina, veri?, secenek?) -> string                     // .ifc dosyasının metni
     uretAyrintili(bina, veri?, secenek?) -> {metin, uyarilar, sayac: {IFC varlık türü: adet}, dosya_adi}
     dosyaAdi(bina) -> "baslik_ascii.ifc"
     indir(bina, veri?, secenek?) -> {dosya_adi, bayt, uyarilar}   // yalnız tarayıcıda: Blob ile indirme başlatır
     basitProfil(ad) -> {tur, ad, boyutlar, h, b, A, Iy, Iz, J} | null   // motorun basit kesit adları (aşağıda; arayüz de kullanır)
   }
   Node'da: const MatrisIFC = require("./ifc_disari.js"). UMD; bağımlılık yok; DOM yalnız indir() içinde.
   bina: bina JSON (surum 1/2 aks–kat; surum 3 dugumler/cubuklar/paneller/mesnetler; §19 akslar.z ve aks_sistemleri) ya da JSON metni.
   veri: yapi.bina_coz(...).veri (isteğe bağlı): ag (motor düğüm/eleman ağı), yukler, durumlar, kombinasyonlar, tasarim (D/C).
   secenek: {analiz: true (yapısal analiz modeli), yukler: true (G/Q yükleri, veri gerekir), sonuclar: true (D/C özellikleri),
             izgara: "kat" | "tek" | false (aks ızgaraları), zaman: "YYYY-MM-DDTHH:MM:SS" (UTC; verilirse dosya belirlenimci),
             tohum (GlobalId kökü; varsayılan proje adı/başlık), dosya_adi, proje: {ad, yer, il, ilce, ada, parsel, hazirlayan, kurum},
             uygulama: {ad, surum, firma, tam_ad} (dosyayı yazan uygulama; verilmezse "Matris Öğren" — web çıktısı değişmez)}

   Bina koordinatı (X sağa, Y derinlik, Z yukarı) doğrudan IFC'ye gider (IFC de Z yukarı); motor (cerceve3b, Y yukarı) eksenine DEĞİL.
   Uzunluk metre, açı radyan, kuvvet kN.

   Üretilenler:
   - Mekânsal yapı: IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey (her kat, Elevation; kat kotu §19'da Z aksından).
   - Aks ızgaraları: IfcGrid + IfcGridAxis (UAxes = X aksları, VAxes = Y aksları) her Z aksı seviyesinde; ek aks sistemleri
     (döndürülmüş/ötelenmiş kartezyen: RECTANGULAR; silindirik: RADIAL, r çemberleri + θ doğrultuları) ayrı ızgaralar.
     Kat olmayan Z aksları (saçak, mahya…) binada Pset_MatrisOgren_ZAkslari.
   - Fiziksel model (IfcExtrudedAreaSolid katılar): kolon → IfcColumn, kiriş → IfcBeam, çapraz/makas/aşık/kren/… → IfcMember,
     döşeme/çatı → IfcSlab (FLOOR/ROOF; kalınlık 0 → IfcCovering), cephe → IfcPlate/IfcCovering,
     temel → IfcFooting (PAD_FOOTING, STRIP_FOOTING, FOOTING_BEAM) ya da IfcSlab BASESLAB (radye).
     Kesitler: dikdörtgen → IfcRectangleProfileDef, IPE/HEA/HEB → IfcIShapeProfileDef, kutu → IfcRectangleHollowProfileDef,
     boru → IfcCircleHollowProfileDef, dolu daire → IfcCircleProfileDef, L → IfcLShapeProfileDef, U/UPN → IfcUShapeProfileDef,
     2L → iki IfcLShapeProfileDef'li IfcCompositeProfileDef (sırt sırta, aralık ara).
     Kesit kaydı biçimleri (motor yapi_serbest._kesit_kart ile aynı sırada): {tip: "profil", profil: "IPE 300"}; motorun basit kesit
     adları {profil: "BORU 168.3x6.3" | "KUTU 150x8" | "KUTU 200x100x6" | "L 100x10" | "2L 70x7 s=10" | "UPN 200"} (mm; köşe
     yarıçapları ve A, Iy, Iz, J tasarim.kesit_ozellik ile aynı → basitProfil); {tip: "kutu"|"boru"|"L"|"2L"|"U", boyutlar: {.. mm}};
     üst düzey ölçüler {tip: "boru", D, t} (m; > 5 ise mm); {tip: "vute", temel, ek_yukseklik, boy, derin_uc}: temel kesitin profili,
     vute boyunca IfcExtrudedAreaSolidTapered (derin uçta h + ek_yukseklik, üst yüz hizalı, alta büyür; temel kesit I, dikdörtgen,
     kutu ya da U) + Pset_MatrisVute. Boru/dolu daire/L/2L temelli vutede konik profil yok: temel kesitli düz katı + Pset ve uyarı.
     Tanımsız/eksik kesit uyarıları kesit adı başına bir kez, kullanım sayısıyla.
   - Malzeme (IfcMaterial, IfcMaterialProfileSet/Usage), Pset_*Common, Pset_ConcreteElementGeneral, Pset_MatrisOgren (D/C).
   - Yapısal analiz modeli (secenek.analiz, varsayılan açık): IfcStructuralAnalysisModel, IfcStructuralPointConnection +
     IfcBoundaryNodeCondition, IfcStructuralCurveMember (IfcEdge/IfcVertexPoint), IfcRelConnectsStructuralMember (uç serbestlikleri),
     IfcStructuralLoadCase / IfcStructuralLoadGroup (birleşimler, IfcRelAssignsToGroupByFactor), veri varsa yükler
     (IfcStructuralLinearAction / IfcStructuralCurveAction POLYGONAL, IfcStructuralPointAction): aks–kat G, Q ve S (kiriş yükleri,
     döşeme payları, kolon öz ağırlığı; kar çatı katı döşeme paylarından, veri.kar.s); surum 3 G, Q ve S (veri.yukler.cubuklar öz
     ağırlık/duvar, veri.yukler.paneller kenar dağılımları, bina.ek_yukler çubuk/düğüm yükleri; ayrıntı: genelYukler); iki modelde
     rüzgâr (W±X/W±Y), deprem (EX±/EY±; EZ = G_carpani × G) ve kren (K…) eylemleri veri.yukler.eylemler'den (rijit diyafram efendi
     düğümü "Kat k diyafram merkezi" bağlantısı ve kat düğümlerine rijit bağlarıyla; efendi bir kat düğümüyle çakışıyorsa merkez o
     düğüm) ve mütemadi/radye temel öz ağırlığı veri.temel.oz_yuk'tan (yükler ayrıntısı: yukler).
     Analiz üyesi ↔ fiziksel eleman (IfcRelAssignsToProduct) ve D/C (Pset_MatrisOgren) surum 3'te motorun çubuk no'suyla eşlenir.
   - Düğüm başvuruları (REF): §12.1 {"dugum"} | {"aks", "kat"} | {"X", "Y", "Z"}; §19.2 {"aks", "z"} | {"sistem", "aks", "z"} ve
     dugumler kayıtlarında "bolme" (cubuk_i, cubuk_j, oran) ve "kesisim" (a, b doğruları) düğümleri. Aynı konumdaki (1 mm) REF'ler tek düğüm.
   - Sahiplik: IfcOwnerHistory + IfcApplication. Uygulama kimliği varsayılan "Matris Öğren" (SURUM); secenek.uygulama.ad
     verilirse (op4 yerel programı) IfcApplication (Version = surum, ApplicationFullName = tam_ad || ad,
     ApplicationIdentifier = ad), geliştirici IfcOrganization (firma || ad) ve FILE_NAME (ön işlemci "ad surum",
     kaynak sistem tam_ad || ad) onu taşır.
   - GlobalId: 22 karakter IFC base64, (proje tohumu + nesne anahtarı) özetinden — aynı modelden aynı kimlikler. */
(function (kok, fabrika) {
  "use strict";
  const M = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = M;
  if (kok) kok.MatrisIFC = M;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : null), function () {
  "use strict";

  const SURUM = "1.1";
  const UYGULAMA_AD = "Matris Öğren";
  const UYGULAMA = UYGULAMA_AD + " " + SURUM;

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
  function sy(x) { return String(parseFloat((+x).toFixed(3))); }      // metin içinde kısa sayı (3 ondalık)
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
    // IfcRoot varlıklarına (ilk alan GlobalId) sahiplik geçmişi (IfcOwnerHistory) kendiliğinden bağlanır
    if (this.sahip && alanlar.length > 1 && alanlar[0] && alanlar[0]._gid && alanlar[1] === null) alanlar[1] = this.sahip;
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
  // Aks listesi: [{ad, konum, kat?}] konuma göre sıralı (aynı ad iki kez verilirse ilki geçerli)
  function aksListesi(l) {
    const gor = {};
    return dizi(l).filter(function (a) { return a && a.ad !== undefined && a.ad !== null; }).map(function (a) {
      const k = { ad: String(a.ad), konum: sayi(a.konum, 0) };
      if (a.kat !== undefined && a.kat !== null && isFinite(+a.kat)) k.kat = +a.kat;
      return k;
    }).filter(function (a) { if (gor[a.ad]) return false; gor[a.ad] = true; return true; })
      .sort(function (a, b) { return a.konum - b.konum; });
  }
  function adSozluk(l) { const s = {}; l.forEach(function (a, i) { s[a.ad] = i; }); return s; }

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
    Bm.ax = aksListesi(ak.x);
    Bm.ay = aksListesi(ak.y);
    Bm.ixAd = adSozluk(Bm.ax);
    Bm.iyAd = adSozluk(Bm.ay);
    // Katlar (§19.1): kat seviyeleri Z akslarının alt kümesidir; akslar.z[i].kat = n → kat n'nin kotu o aksın konumu (tek kaynak).
    const az = aksListesi(ak.z);
    const katlar = {};
    dizi(bina.katlar).forEach(function (k, i) {
      const no = k.no === undefined ? i : +k.no;
      katlar[no] = { no: no, ad: String(k.ad || (no ? no + ". kat" : "Temel")), kot: sayi(k.kot, 0) };
    });
    az.forEach(function (z) {
      if (z.kat === undefined) return;
      if (katlar[z.kat]) katlar[z.kat].kot = z.konum;
      else katlar[z.kat] = { no: z.kat, ad: z.ad, kot: z.konum };
    });
    Bm.katlar = Object.keys(katlar).map(function (n) { return katlar[n]; }).sort(function (a, b) { return a.no - b.no; });
    if (!Bm.katlar.length && az.length) {                 // kat eşlemesi yok: her Z aksı bir seviye
      Bm.katlar = az.map(function (z, i) { return { no: i, ad: z.ad, kot: z.konum }; });
      az.forEach(function (z, i) { z.kat = i; });
    }
    if (!Bm.katlar.length) Bm.katlar = [{ no: 0, ad: "Temel", kot: 0 }];
    Bm.kat = {};
    Bm.katlar.forEach(function (k) { Bm.kat[k.no] = k; });
    Bm.nk = Bm.katlar[Bm.katlar.length - 1].no;
    Bm.kot0 = Bm.katlar[0].kot;
    // Z aksları: verilmemişse katlardan türetilir (eski dosyalar); kat seviyesi olmayan Z aksları (saçak, mahya, kren…) korunur
    Bm.az = az.length ? az : Bm.katlar.map(function (k) { return { ad: k.ad, konum: k.kot, kat: k.no }; });
    Bm.izAd = adSozluk(Bm.az);
    // Ek aks sistemleri (§19.1): kartezyen (döndürülmüş/ötelenmiş) ve silindirik
    Bm.sistemler = {};
    Bm.sistemSira = [];
    dizi(bina.aks_sistemleri).forEach(function (s, i) {
      if (!s || typeof s !== "object") return;
      const ad = String(s.ad || ("SİSTEM-" + (i + 1)));
      if (ad === "GLOBAL" || Bm.sistemler[ad]) { uyarilar.push("Aks sistemi '" + ad + "' iki kez tanımlı ya da ayrılmış ad; atlandı."); return; }
      const tur = String(s.tur || "kartezyen").toLowerCase() === "silindirik" ? "silindirik" : "kartezyen";
      const o = dizi(s.orijin);
      const S_ = { ad: ad, tur: tur, orijin: [sayi(o[0], 0), sayi(o[1], 0), sayi(o[2], 0)], aci: sayi(s.aci, 0),
        u: aksListesi(tur === "silindirik" ? s.r : s.x), v: aksListesi(tur === "silindirik" ? s.teta : s.y),
        z: Array.isArray(s.z) && s.z.length ? aksListesi(s.z) : null };
      S_.iuAd = adSozluk(S_.u); S_.ivAd = adSozluk(S_.v); S_.izAd = S_.z ? adSozluk(S_.z) : null;
      Bm.sistemler[ad] = S_;
      Bm.sistemSira.push(S_);
    });
    return Bm;
  }
  // Ek sistemin yerel düzlem noktası (u, v) → global (X, Y); kartezyende u = x, v = y; silindirikte u = r, v = θ (derece)
  function sistemXY(S_, u, v) {
    let x = u, y = v;
    if (S_.tur === "silindirik") { const t = v * Math.PI / 180; x = u * Math.cos(t); y = u * Math.sin(t); }
    const a = S_.aci * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
    return [S_.orijin[0] + c * x - s * y, S_.orijin[1] + s * x + c * y];
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
  // Düğümler konuma göre tekildir: aynı konumda (1 mm) ikinci bir numara gelirse ilk düğümün takma adı olur
  // (aks–kat düğümü, serbest düğüm kaydı ve §19 aks REF'i aynı noktada buluşabilir; analiz modelinde tek düğüm).
  function DugumKumesi(Bm, uyarilar) {
    this.Bm = Bm;
    this.uyarilar = uyarilar || [];
    this.liste = [];
    this.no = {};
    this.izgara = {};
    this.serbestSira = 100000;
    this.kayit = {};
    const self = this;
    dizi(Bm.bina.dugumler).forEach(function (d) { if (d && d.no !== undefined && !self.kayit[+d.no]) self.kayit[+d.no] = d; });
    Object.keys(this.kayit).forEach(function (n) { if (+n > self.serbestSira) self.serbestSira = +n; });
    this.cozuluyor = {};
  }
  DugumKumesi.prototype.anahtar = function (X, Y, Z) { return Math.round(X * 1000) + "|" + Math.round(Y * 1000) + "|" + Math.round(Z * 1000); };
  DugumKumesi.prototype.ekle = function (no, X, Y, Z, ad) {
    if (this.no[no]) return this.no[no];
    const var_ = this.konumda(X, Y, Z);
    if (var_) { this.no[no] = var_; return var_; }
    const d = { no: no, X: X, Y: Y, Z: Z, ad: ad || ("N" + no) };
    this.liste.push(d);
    this.no[no] = d;
    const k = this.anahtar(X, Y, Z);
    (this.izgara[k] = this.izgara[k] || []).push(d);
    if (no >= this.serbestSira) this.serbestSira = no;
    return d;
  };
  DugumKumesi.prototype.konumda = function (X, Y, Z) {
    const x = Math.round(X * 1000), y = Math.round(Y * 1000), z = Math.round(Z * 1000);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) for (let k = -1; k <= 1; k++) {
      const l = this.izgara[(x + i) + "|" + (y + j) + "|" + (z + k)];
      if (!l) continue;
      for (let n = 0; n < l.length; n++) {
        const d = l[n];
        if (Math.abs(d.X - X) <= 1e-3 && Math.abs(d.Y - Y) <= 1e-3 && Math.abs(d.Z - Z) <= 1e-3) return d;
      }
    }
    return null;
  };
  DugumKumesi.prototype.serbest = function (X, Y, Z, ad) {
    const var_ = this.konumda(X, Y, Z);
    if (var_) return var_;
    return this.ekle(this.serbestSira + 1, X, Y, Z, ad);
  };
  DugumKumesi.prototype.aksDugum = function (ix, iy, kat) {
    const Bm = this.Bm, kot = katKot(Bm, kat);
    if (kot === null || !Bm.ax[ix] || !Bm.ay[iy]) return null;
    const no = aksDugumNo(kat, ix, iy);
    if (this.no[no]) return this.no[no];
    return this.ekle(no, Bm.ax[ix].konum, Bm.ay[iy].konum, kot, Bm.ax[ix].ad + Bm.ay[iy].ad + "/k" + kat);
  };
  // Z seviyesi: {"kat": k} | {"z": ad (Z aksı; sistemin kendi Z aksları varsa onlar, yoksa GLOBAL)} | yok → kat 1.
  // Dönüş: {Z, kat (Z aksı bir kat seviyesiyse), ad}
  DugumKumesi.prototype.zSeviye = function (r, S_) {
    const Bm = this.Bm;
    if (r.kat !== undefined && r.kat !== null) {
      const k = +r.kat, kot = katKot(Bm, k);
      return kot === null ? null : { Z: kot, kat: k, ad: "k" + k };
    }
    if (r.z !== undefined && r.z !== null) {
      const ad = String(r.z);
      if (S_ && S_.z) {
        if (S_.izAd[ad] !== undefined) return { Z: S_.orijin[2] + S_.z[S_.izAd[ad]].konum, kat: undefined, ad: ad };
      } else if (Bm.izAd[ad] !== undefined) {
        const z = Bm.az[Bm.izAd[ad]];
        return { Z: z.konum, kat: z.kat, ad: ad };
      }
      if (typeof r.z === "number" && isFinite(r.z)) return { Z: (S_ && S_.z ? S_.orijin[2] : 0) + r.z, kat: undefined, ad: String(r.z) };
      return null;
    }
    const kot = katKot(Bm, 1);
    return kot === null ? null : { Z: kot, kat: 1, ad: "k1" };
  };
  // Düğüm kaydı → konum (§12.1 koordinatlı kayıt; §19.2 aks REF'li kayıt, "bolme" ve "kesisim" düğümleri; yinelemeli)
  DugumKumesi.prototype.kayitCoz = function (no) {
    const Bm = this.Bm, d = this.kayit[no], self = this;
    if (!d) return null;
    if (this.cozuluyor[no]) { this.uyarilar.push("Düğüm " + no + ": döngüsel bölme/kesişim tanımı; atlandı."); return null; }
    this.cozuluyor[no] = true;
    try {
      const ad = d.ad ? String(d.ad) : null;
      const tur = String(d.tur || "").toLowerCase();
      if (tur === "bolme") {
        const a = this.ref(d.cubuk_i), b = this.ref(d.cubuk_j), t = sayi(d.oran, 0.5);
        if (!a || !b) { this.uyarilar.push("Bölme düğümü " + no + ": ana çubuğun uçları çözülemedi."); return null; }
        return this.ekle(no, a.X + (b.X - a.X) * t, a.Y + (b.Y - a.Y) * t, a.Z + (b.Z - a.Z) * t, ad);
      }
      if (tur === "kesisim") {
        const a = dizi(d.a).map(function (r) { return self.ref(r); }), b = dizi(d.b).map(function (r) { return self.ref(r); });
        if (a.length < 2 || b.length < 2 || a.concat(b).some(function (x) { return !x; })) {
          this.uyarilar.push("Kesişim düğümü " + no + ": doğruların uçları çözülemedi."); return null;
        }
        const P = kesisimNoktasi([a[0].X, a[0].Y, a[0].Z], [a[1].X, a[1].Y, a[1].Z], [b[0].X, b[0].Y, b[0].Z], [b[1].X, b[1].Y, b[1].Z]);
        if (!P) { this.uyarilar.push("Kesişim düğümü " + no + ": doğrular paralel; atlandı."); return null; }
        return this.ekle(no, P[0], P[1], P[2], ad);
      }
      if (d.aks !== undefined || d.sistem !== undefined) {
        const r = this.ref({ aks: d.aks, sistem: d.sistem, kat: d.kat, z: d.z });
        if (r) { if (!this.no[no]) this.no[no] = r; return r; }
      }
      if (d.X !== undefined || d.Y !== undefined || d.Z !== undefined) return this.ekle(no, sayi(d.X, 0), sayi(d.Y, 0), sayi(d.Z, 0), ad);
      this.uyarilar.push("Düğüm " + no + ": konumu anlaşılamadı; atlandı.");
      return null;
    } finally {
      delete this.cozuluyor[no];
    }
  };
  // REF: §12.1 {"dugum": no} | {"aks": [x, y], "kat": k} | {"X", "Y", "Z"};
  //      §19.2 {"aks": [x, y], "z": "Saçak"} | {"sistem": "KANAT-B", "aks": [x, y], "z": ..} | silindirik {"sistem", "aks": [r, θ], "z"}.
  DugumKumesi.prototype.ref = function (r) {
    const Bm = this.Bm;
    if (r === null || r === undefined) return null;
    if (typeof r === "string" && /^\d+$/.test(r.trim())) r = +r;
    if (typeof r === "number") r = { dugum: r };
    if (Array.isArray(r) && r.length === 3) r = { X: r[0], Y: r[1], Z: r[2] };
    if (typeof r !== "object") return null;
    if (r.dugum !== undefined && r.dugum !== null) {
      if (typeof r.dugum === "object") return this.ref(r.dugum);
      const no = +r.dugum;
      if (this.no[no]) return this.no[no];
      if (this.kayit[no]) return this.kayitCoz(no);
      if (no > 0 && no < 100000) {
        const kat = Math.floor(no / 1000), kalan = no % 1000 - 1, ix = Math.floor(kalan / 20), iy = kalan % 20;
        return this.aksDugum(ix, iy, kat);
      }
      return null;
    }
    if (r.aks !== undefined && r.aks !== null) {
      const sis = r.sistem === undefined || r.sistem === null || r.sistem === "GLOBAL" ? null : Bm.sistemler[String(r.sistem)];
      if (r.sistem !== undefined && r.sistem !== null && r.sistem !== "GLOBAL" && !sis) {
        this.uyarilar.push("Aks sistemi '" + r.sistem + "' tanımsız (REF " + JSON.stringify(r) + ").");
        return null;
      }
      const z = this.zSeviye(r, sis);
      if (!z) return null;
      if (!sis) {
        const a = aksXY(Bm, r.aks);
        if (!a) return null;
        if (z.kat !== undefined && Bm.kat[z.kat] && Math.abs(Bm.kat[z.kat].kot - z.Z) < 1e-9) return this.aksDugum(a.ix, a.iy, z.kat);
        return this.serbest(a.X, a.Y, z.Z, Bm.ax[a.ix].ad + Bm.ay[a.iy].ad + "/" + z.ad);
      }
      const aks = dizi(r.aks), iu = sis.iuAd[String(aks[0])], iv = sis.ivAd[String(aks[1])];
      if (iu === undefined || iv === undefined) return null;
      const P = sistemXY(sis, sis.u[iu].konum, sis.v[iv].konum);
      return this.serbest(P[0], P[1], z.Z, sis.ad + ":" + sis.u[iu].ad + sis.v[iv].ad + "/" + z.ad);
    }
    if (r.X !== undefined || r.Y !== undefined || r.Z !== undefined) return this.serbest(sayi(r.X, 0), sayi(r.Y, 0), sayi(r.Z, 0));
    return null;
  };
  // İki doğrunun (A1A2, B1B2) en yakın noktalarının ortası; paralelse null
  function kesisimNoktasi(A1, A2, B1, B2) {
    const u = vfark(A2, A1), v = vfark(B2, B1), w0 = vfark(A1, B1);
    const a = vic(u, u), b = vic(u, v), c = vic(v, v), d = vic(u, w0), e = vic(v, w0);
    const D = a * c - b * b;
    if (Math.abs(D) < 1e-12 * Math.max(1, a * c)) return null;
    const s = (b * e - c * d) / D, t = (a * e - b * d) / D;
    const P = vtop(A1, volc(u, s)), Q = vtop(B1, volc(v, t));
    return volc(vtop(P, Q), 0.5);
  }

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

  // ======================================================================
  // Basit çelik kesitler: motorun (tasarim.kesit_ozellik) ad dilbilgisi ve parça toplama hesabı
  // ======================================================================
  // basitProfil(ad) → {tur: "boru"|"kutu"|"L"|"2L"|"U", ad (motorun yazdığı biçim), boyutlar (m), h, b (m; dış ölçüler),
  //                    A (m²), Iy, Iz (m⁴; Iy yatay y ekseni etrafında = tasarim.kesit_ozellik ile aynı), J (m⁴)} | null.
  // Dilbilgisi (büyük/küçük harf duyarsız; x, X, × ya da *; ondalık nokta ya da virgül; ölçüler mm):
  //   "BORU D x t" (CHS) | "KUTU a x t" (kare) | "KUTU h x b x t" (RHS/SHS) | "L a x t" | "L a x a x t" | "2L a x t s=g" | "UPN n".
  //   Motorla aynı (tasarim._ad_coz): korniyer yalnız eşit kollu ("L 100x80x8" → null); UPN boyu int(round(n)) ile tabloda aranır.
  // boyutlar: boru {D, t}; kutu {h, b, t, r_o, r_i}; L {h (düşey kol), b (yatay kol), t, r1, r2}; 2L {h, b, t, s, r1, r2};
  //           U {h, b, tw, tf, r, r2, egim}. Köşe yarıçapları motordaki gibi: kutu sıcak r_o = 1,5t, r_i = t (EN 10210-2);
  //           korniyer kök r1 (EN 10056-1 tablosu), uç r2 = r1/2; UPN r = tf, r2 = tf/2, başlık iç yüz eğimi %8.
  const UPN_TABLO = { 80: [45, 6, 8], 100: [50, 6, 8.5], 120: [55, 7, 9], 140: [60, 7, 10], 160: [65, 7.5, 10.5], 180: [70, 8, 11],
    200: [75, 8.5, 11.5], 220: [80, 9, 12.5], 240: [85, 9.5, 13], 260: [90, 10, 14], 280: [95, 10, 15], 300: [100, 10, 16] };   // h: [b, tw, tf] mm
  const L_KOK = { "40|4": 6, "45|5": 7, "50|5": 7, "50|6": 7, "60|6": 8, "65|7": 9, "70|7": 9, "75|8": 10, "80|8": 10, "90|9": 11,
    "100|10": 12, "120|12": 13, "150|15": 16, "160|16": 17, "180|18": 18, "200|20": 18 };                                     // "b|t": r1 mm
  const IKI_L_ARA = 10;            // mm, çift korniyer varsayılan bayrak levhası aralığı (motorla aynı)
  const VUTE_KONIK = { I: true, dikdortgen: true, kutu: true, U: true };   // derin uç profili olan (konik katılı) vute temel türleri
  const BASIT_TIP = { KUTU: "kutu", RHS: "kutu", SHS: "kutu", BORU: "boru", CHS: "boru", L: "L", KORNIYER: "L", "2L": "2L",
    CIFT_KORNIYER: "2L", U: "U", UPN: "U" };

  // Parça toplama (X yatay, Z düşey; mm): dikdörtgen, köşe kavisi (kare − çeyrek daire), üçgen; s = +1 ekle, −1 çıkar
  const KAVIS_C = (10 - 3 * Math.PI) / (12 - 3 * Math.PI);
  function pDik(xa, xb, za, zb, s) {
    const x0 = Math.min(xa, xb), x1 = Math.max(xa, xb), z0 = Math.min(za, zb), z1 = Math.max(za, zb), w = x1 - x0, h = z1 - z0;
    return { s: s === undefined ? 1 : s, A: w * h, cx: (x0 + x1) / 2, cz: (z0 + z1) / 2, Iy0: w * h * h * h / 12, Iz0: h * w * w * w / 12 };
  }
  function pKavis(px, pz, sx, sz, r, s) {
    if (!(r > 0)) return null;
    const a = (1 - Math.PI / 4) * r * r, c = KAVIS_C * r, I0 = Math.pow(r, 4) * (1 - 5 * Math.PI / 16) - a * c * c;
    return { s: s, A: a, cx: px + sx * c, cz: pz + sz * c, Iy0: I0, Iz0: I0 };
  }
  function pUcgen(p1, p2, p3, s) {
    const x1 = p1[0], z1 = p1[1], x2 = p2[0], z2 = p2[1], x3 = p3[0], z3 = p3[1];
    const A = Math.abs((x2 - x1) * (z3 - z1) - (x3 - x1) * (z2 - z1)) / 2, cx = (x1 + x2 + x3) / 3, cz = (z1 + z2 + z3) / 3;
    const zz = A / 6 * (z1 * z1 + z2 * z2 + z3 * z3 + z1 * z2 + z2 * z3 + z1 * z3);
    const xx = A / 6 * (x1 * x1 + x2 * x2 + x3 * x3 + x1 * x2 + x2 * x3 + x1 * x3);
    return { s: s, A: A, cx: cx, cz: cz, Iy0: zz - A * cz * cz, Iz0: xx - A * cx * cx };
  }
  function pToplam(P) {
    P = P.filter(function (p) { return p && p.A > 0; });
    let A = 0, Sx = 0, Sz = 0;
    P.forEach(function (p) { A += p.s * p.A; Sx += p.s * p.A * p.cx; Sz += p.s * p.A * p.cz; });
    const cx = Sx / A, cz = Sz / A;
    let Iy = 0, Iz = 0;
    P.forEach(function (p) { Iy += p.s * (p.Iy0 + p.A * (p.cz - cz) * (p.cz - cz)); Iz += p.s * (p.Iz0 + p.A * (p.cx - cx) * (p.cx - cx)); });
    return { A: A, Iy: Iy, Iz: Iz };
  }
  // Korniyer: sırtı X = x0 (düşey kol dış yüzü), alt yüzü Z = 0; yatay kol yon (±1) yönüne uzanır. a: düşey kol, b: yatay kol
  function korniyerParcalari(a, b, t, r1, r2, x0, yon) {
    const X = function (x) { return x0 + yon * x; };
    return [pDik(X(0), X(t), 0, a), pDik(X(t), X(b), 0, t), pKavis(X(t), t, yon, 1, r1, 1),
      pKavis(X(t), a, -yon, -1, r2, -1), pKavis(X(b), t, -yon, -1, r2, -1)];
  }
  function sad(x) { return String(parseFloat((+x).toFixed(2))); }       // motorun ad biçimi (_f(x, 2))

  // tur + boyutlar (mm) → kesit sonucu (yukarıdaki biçim) | null (tutarsız ölçü)
  function basitHesap(tur, b) {
    const n = function (v) { const x = +v; return v !== null && v !== undefined && v !== "" && isFinite(x) && x > 0 ? x : null; };
    const r = function (v, vars) { const x = +v; return v !== null && v !== undefined && v !== "" && isFinite(x) && x >= 0 ? x : vars; };
    let A, Iy, Iz, J, ad, h, bb, boy;
    if (tur === "kutu") {
      const H = n(b.H !== undefined ? b.H : b.h), B = n(b.B !== undefined ? b.B : b.b), t = n(b.t);
      if (!H || !B || !t) return null;
      const soguk = String(b.imalat || "sicak").toLowerCase() === "soguk", td = soguk ? 0.93 * t : t;
      let ro0 = 1.5 * td, ri0 = td;
      if (soguk) { const k = t <= 6 ? [2, 1] : (t <= 10 ? [2.5, 1.5] : [3, 2]); ro0 = k[0] * td; ri0 = k[1] * td; }
      const ro = r(b.r_o, ro0), ri = r(b.r_i, ri0);
      if (2 * td >= Math.min(H, B)) return null;
      const P = [pDik(0, B, 0, H), pDik(td, B - td, td, H - td, -1)];
      [[0, 0, 1, 1], [B, 0, -1, 1], [0, H, 1, -1], [B, H, -1, -1]].forEach(function (c) { P.push(pKavis(c[0], c[1], c[2], c[3], ro, -1)); });
      [[td, td, 1, 1], [B - td, td, -1, 1], [td, H - td, 1, -1], [B - td, H - td, -1, -1]].forEach(function (c) { P.push(pKavis(c[0], c[1], c[2], c[3], ri, 1)); });
      const T = pToplam(P);
      A = T.A; Iy = T.Iy; Iz = T.Iz;
      const Rc = (ro + ri) / 2, p = 2 * ((B - td) + (H - td)) - 2 * Rc * (4 - Math.PI), Ah = (B - td) * (H - td) - Rc * Rc * (4 - Math.PI);
      J = td * td * td * p / 3 + 4 * Ah * Ah * td / p;
      ad = "KUTU " + sad(H) + "x" + sad(B) + "x" + sad(t); h = H; bb = B;
      boy = { h: H, b: B, t: t, r_o: ro, r_i: ri };
    } else if (tur === "boru") {
      const D = n(b.D !== undefined ? b.D : b.d), t = n(b.t);
      if (!D || !t) return null;
      const td = String(b.imalat || "sicak").toLowerCase() === "soguk" ? 0.93 * t : t, d = D - 2 * td;
      if (2 * td >= D) return null;
      A = Math.PI / 4 * (D * D - d * d); Iy = Iz = Math.PI / 64 * (Math.pow(D, 4) - Math.pow(d, 4)); J = 2 * Iy;
      ad = "BORU " + sad(D) + "x" + sad(t); h = bb = D;
      boy = { D: D, t: t };
    } else if (tur === "L" || tur === "2L") {
      const bk = n(b.b), ak = n(b.h !== undefined ? b.h : b.b), t = n(b.t);
      if (!bk || !ak || !t || t >= Math.min(ak, bk) / 2) return null;
      if (tur === "2L" && Math.abs(ak - bk) > 1e-9) return null;              // çift korniyer yalnız eşit kollu (motor gibi)
      const esit = Math.abs(ak - bk) < 1e-9;
      const r1 = r(b.r1, esit ? (L_KOK[Math.round(bk) + "|" + Math.round(t)] || 0) : 0), r2 = r(b.r2, r1 / 2);
      if (tur === "L") {
        const L1 = pToplam(korniyerParcalari(ak, bk, t, r1, r2, 0, 1));
        A = L1.A; Iy = L1.Iy; Iz = L1.Iz;
        J = (ak - t / 2 + bk - t / 2) * t * t * t / 3;
        ad = "L " + sad(ak) + "x" + sad(bk) + "x" + sad(t); h = ak; bb = bk;
        boy = { h: ak, b: bk, t: t, r1: r1, r2: r2 };
      } else {
        const s = r(b.s, IKI_L_ARA);
        const T = pToplam(korniyerParcalari(bk, bk, t, r1, r2, s / 2, 1).concat(korniyerParcalari(bk, bk, t, r1, r2, -s / 2, -1)));
        A = T.A; Iy = T.Iy; Iz = T.Iz;
        J = 2 * (2 * (bk - t / 2) * t * t * t / 3);
        ad = "2L " + sad(bk) + "x" + sad(bk) + "x" + sad(t) + " s=" + sad(s); h = bk; bb = 2 * bk + s;
        boy = { h: bk, b: bk, t: t, s: s, r1: r1, r2: r2 };
      }
    } else if (tur === "U") {
      const hh = n(b.h), b_ = n(b.b), tw = n(b.tw), tf = n(b.tf);
      if (!hh || !b_ || !tw || !tf) return null;
      const egim = r(b.egim, 0), rr = r(b.r, tf), r2 = r(b.r2, b.egim !== undefined ? rr / 2 : 0);
      const yar = (b_ - tw) / 2, tuc = tf - egim * yar, tkok = tf + egim * yar;
      if (2 * tkok >= hh || tw >= b_ || tuc <= 0) return null;
      const T = pToplam([pDik(0, tw, 0, hh), pDik(tw, b_, 0, tuc), pDik(tw, b_, hh - tuc, hh),
        pUcgen([tw, tuc], [tw, tkok], [b_, tuc], 1), pUcgen([tw, hh - tuc], [tw, hh - tkok], [b_, hh - tuc], 1),
        pKavis(tw, tkok, 1, 1, rr, 1), pKavis(tw, hh - tkok, 1, -1, rr, 1), pKavis(b_, tuc, -1, -1, r2, -1), pKavis(b_, hh - tuc, -1, 1, r2, -1)]);
      A = T.A; Iy = T.Iy; Iz = T.Iz;
      const bp = b_ - tw / 2, hp = hh - tf;
      J = (2 * bp * tf * tf * tf + hp * tw * tw * tw) / 3;
      ad = b.ad ? String(b.ad) : "U " + sad(hh) + "x" + sad(b_) + "x" + sad(tw) + "x" + sad(tf); h = hh; bb = b_;
      boy = { h: hh, b: b_, tw: tw, tf: tf, r: rr, r2: r2, egim: egim };
    } else {
      return null;
    }
    const mm = {};
    Object.keys(boy).forEach(function (k) { mm[k] = k === "egim" ? boy[k] : boy[k] / 1000; });
    return { tur: tur, ad: ad, boyutlar: mm, h: h / 1000, b: bb / 1000, A: A * 1e-6, Iy: Iy * 1e-12, Iz: Iz * 1e-12, J: J * 1e-12 };
  }

  // Motorun basit kesit adı ("BORU 168.3x6.3", "KUTU 150x8", "KUTU 200x100x6", "L 100x10", "2L 70x7 s=10", "UPN 200") → kesit | null
  function basitProfil(ad) {
    if (ad === null || ad === undefined || typeof ad === "object") return null;
    const s = String(ad).trim().toUpperCase().replace(/[×*]/g, "X").replace(/,/g, ".").split(/\s+/).join(" ");
    const m = /^(2L|KUTU|RHS|SHS|BORU|CHS|L|UPN)\s*([0-9.]+(?:\s*X\s*[0-9.]+)*)\s*(?:\(?\s*S\s*=?\s*([0-9.]+)\s*\)?)?$/.exec(s);
    if (!m) return null;
    const n = m[2].split(/\s*X\s*/).map(Number);
    if (n.some(function (x) { return !(isFinite(x) && x > 0); })) return null;
    const tur = BASIT_TIP[m[1]];
    if (tur === "kutu" && (n.length === 2 || n.length === 3)) return basitHesap(tur, n.length === 2 ? { H: n[0], B: n[0], t: n[1] } : { H: n[0], B: n[1], t: n[2] });
    if (tur === "boru" && n.length === 2) return basitHesap(tur, { D: n[0], t: n[1] });
    if ((tur === "L" || tur === "2L") && (n.length === 2 || n.length === 3)) {
      if (n.length === 3 && n[0] !== n[1]) return null;                   // motor: "yalnız eşit kollu korniyer desteklenir"
      const b = { h: n[0], b: n[0], t: n[n.length - 1] };
      if (tur === "2L") b.s = m[3] !== undefined ? +m[3] : IKI_L_ARA;
      return basitHesap(tur, b);
    }
    if (tur === "U" && n.length === 1) {
      // motor gibi int(round(n)): Python round() yarımda çifte yuvarlar ("UPN 200.4" → UPN 200, "UPN 200.5" → UPN 200)
      const h = yuvarlaCifte(n[0]), u = UPN_TABLO[h];
      if (!u) return null;
      return basitHesap("U", { h: h, b: u[0], tw: u[1], tf: u[2], r: u[2], r2: u[2] / 2, egim: 0.08, ad: "UPN " + h });
    }
    return null;
  }
  // Python round(x) (ondalıksız): en yakın tamsayı, tam yarıda çift olana (banker yuvarlaması)
  function yuvarlaCifte(x) {
    const f = Math.floor(x), d = x - f;
    return d > 0.5 ? f + 1 : (d < 0.5 ? f : (f % 2 === 0 ? f : f + 1));
  }
  // Motorun {tip, boyutlar (mm)} biçimi: kutu {H, B, t}, boru {D, t}, L {b, t}, 2L {b, t, s}, U {h, b, tw, tf} → kesit | null
  // tip "basit" (motorun iç kesit kartındaki genel ad): tür ölçü adlarından (D → boru; tw, tf → U; s → 2L; H/B → kutu; b, t → L)
  function basitBoyutlar(tip, boyutlar) {
    if (!boyutlar || typeof boyutlar !== "object") return null;
    const b = Object.assign({}, boyutlar);
    let tur = BASIT_TIP[String(tip || "").trim().toUpperCase().replace(/\s+/g, "_").replace(/İ/g, "I")];
    if (!tur && String(tip || "").trim().toLowerCase() === "basit") {
      const v = function (a) { return b[a] !== undefined && b[a] !== null && b[a] !== ""; };
      tur = v("D") || v("d") ? "boru" : (v("tw") && v("tf") ? "U" : (v("s") ? "2L" : (v("H") || v("B") ? "kutu" : (v("b") && v("t") ? "L" : null))));
    }
    if (!tur) return null;
    if (tur === "2L" && b.s === undefined) b.s = IKI_L_ARA;
    return basitHesap(tur, b);
  }
  // basitProfil/basitBoyutlar sonucu → IFC profil alanları (m)
  function basitKesit(p) {
    const b = p.boyutlar;
    if (p.tur === "boru") return { tur: "boru", D: b.D, t: b.t, basit: p };
    if (p.tur === "kutu") return { tur: "kutu", h: b.h, b: b.b, t: b.t, ro: b.r_o || null, ri: b.r_i || null, basit: p };
    if (p.tur === "L") return { tur: "L", h: b.h, b: b.b, t: b.t, r1: b.r1 || null, r2: b.r2 || null, basit: p };
    if (p.tur === "2L") return { tur: "2L", h: b.h, b: b.b, t: b.t, ara: b.s, r1: b.r1 || null, r2: b.r2 || null, basit: p };
    return { tur: "U", h: b.h, b: b.b, tw: b.tw, tf: b.tf, r1: b.r || null, r2: b.r2 || null, egim: b.egim || 0, basit: p };
  }

  // Kesit kaydı → IFC kesit nesnesi. Sıra (motor _kesit_kart ile aynı): vute → profil adı (IPE/HEA/HEB tablosu, açık I ölçüleri,
  // basit kesit adı) → boyutlar (mm) → üst düzey ölçüler (m; kutu/boru/daire/L/2L/U) → dikdörtgen.
  function kesitCoz(Bm, ad, uyarilar, yol) {
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
    if (tip === "vute") {
      // vute: temel kesit + derin uçta ek yükseklik (boy boyunca doğrusal azalır); temel kesitin biçimi, ölçüleri Pset_MatrisVute'de
      const temel = String(k.temel === undefined || k.temel === null ? "" : k.temel).trim();
      yol = yol || {};
      const tk = Bm.kesitler[temel];
      if (!tk || yol[temel] || String(tk.tip || "").toLowerCase() === "vute") {
        uyarilar.push("Vute kesiti '" + ad + "': temel kesit '" + temel + "' tanımsız ya da yine vute; 0,30 × 0,30 m dikdörtgen varsayıldı.");
        return Object.assign(sonuc, { tur: "dikdortgen", b: 0.3, h: 0.3 });
      }
      yol[String(ad)] = true;
      const t = kesitCoz(Bm, temel, uyarilar, yol);
      const boy = sayi(k.boy, null), ek = Math.max(0, sayi(k.ek_yukseklik, 0));
      if (ek > 1e-6 && !VUTE_KONIK[t.tur]) {
        uyarilar.push("vute temel kesiti " + temel + ": konik katı yazılmadı (bu kesit için konik profil yok); temel kesitli düz katı ve " +
          "Pset_MatrisVute yazıldı.");
      }
      return Object.assign({}, t, { ad: sonuc.ad, malzeme: k.malzeme || t.malzeme, vute: { temel: temel, temelProfil: t.profil || t.ad,
        ek_yukseklik: ek, boy: boy !== null && boy > 0 ? boy : null,
        derin_uc: String(k.derin_uc || "i").trim().toLowerCase() === "j" ? "j" : "i" } });
    }
    if (tip === "profil" || k.profil) {
      const pad = profilAdi(k.profil || ad);
      const p = PROFILLER[pad];
      sonuc.profil = pad;
      if (p) return Object.assign(sonuc, { tur: "I", h: p[0] / 1000, b: p[1] / 1000, tw: p[2] / 1000, tf: p[3] / 1000, r: p[4] / 1000 });
      if (k.tw && k.tf && k.b && k.h) {
        return Object.assign(sonuc, { tur: "I", h: metre(k.h), b: metre(k.b), tw: metre(k.tw), tf: metre(k.tf), r: k.r ? metre(k.r) : null });
      }
      const bp = basitProfil(k.profil || ad);
      if (bp) {
        sonuc.profil = String(k.profil || ad).trim().split(/\s+/).join(" ");
        return Object.assign(sonuc, basitKesit(bp));
      }
      const ozel = profilTipiCoz(pad, k);
      if (ozel) return Object.assign(sonuc, ozel);
      uyarilar.push("Profil '" + pad + "' tabloda yok; b × h dikdörtgen katı ile gösterildi.");
      return Object.assign(sonuc, { tur: "dikdortgen", b: metre(k.b) || 0.2, h: metre(k.h) || 0.3 });
    }
    if (k.boyutlar && typeof k.boyutlar === "object") {
      const bb = basitBoyutlar(tip, k.boyutlar);
      if (bb) { sonuc.profil = bb.ad; return Object.assign(sonuc, basitKesit(bb)); }
    }
    const ozel = profilTipiCoz(tip, k);
    if (ozel) return Object.assign(sonuc, ozel);
    if (BASIT_TIP[tip.toUpperCase().replace(/\s+/g, "_")] || (tip !== "dikdortgen" && k.boyutlar && typeof k.boyutlar === "object")) {
      uyarilar.push("Kesit '" + ad + "' (tip " + tip + "): ölçüler eksik ya da tutarsız; b × h dikdörtgen katı ile gösterildi.");
    }
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

  // Derinlik (profil Y, kesitin h boyutu) doğrultusu = motorun yerel y′ ekseni (model_ops.yerelEksenler ile aynı kural):
  // eğik/yatay çubukta çubuğu içeren düşey düzlemde yukarı; düşey çubukta (−sgn x′Z, 0, 0) (§2: yukarı kolonda y′ = −X);
  // "aci" (derece) x′ ekseni etrafında sağ el kuralıyla döndürür: y″ = cos a·y′ + sin a·z′ (z′ = x′ × y′).
  function derinlikYonu(t, aci) {
    let d;
    if (Math.hypot(t[0], t[1]) < 1e-9) d = [t[2] > 0 ? -1 : 1, 0, 0];
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
    this.kesitOnbellek = {};
    this.kesitUyari = {};          // kesit uyarısı metni → {i: uyarilar'daki yeri, adet: kullanan eleman sayısı}
  }
  // Kesit çözümü (ad başına bir kez). Kesit uyarıları metin başına bir kez yazılır (aynı profili kullanan farklı kesit adları ve
  // temel kesitinin uyarısını taşıyan vute de aynı satırda toplanır); birden çok elemanda kullanılmışsa sonunda adet eklenir
  // ("… gösterildi (26 eleman)."). say === false: analiz modeli çağrısı (sayılmaz, uyarı yazmaz).
  Uretici.prototype.kesit = function (ad, say) {
    const a = String(ad);
    let c = this.kesitOnbellek[a];
    if (!c) {
      const u = [];
      const k = kesitCoz(this.Bm, ad, u);
      c = this.kesitOnbellek[a] = { k: k, uyarilar: u.filter(function (m, i) { return u.indexOf(m) === i; }) };
    }
    if (say !== false) {
      c.uyarilar.forEach(function (m) {
        let x = this.kesitUyari[m];
        if (!x) { x = this.kesitUyari[m] = { i: this.uyarilar.length, adet: 0 }; this.uyarilar.push(m); }
        x.adet += 1;
      }, this);
    }
    return c.k;
  };
  Uretici.prototype.kesitUyarilariniKapat = function () {
    Object.keys(this.kesitUyari).forEach(function (m) {
      const x = this.kesitUyari[m];
      if (x.adet >= 2) this.uyarilar[x.i] = m.replace(/\.$/, "") + " (" + x.adet + " eleman).";
    }, this);
  };
  Uretici.prototype.gid = function (anahtar) {
    let a = this.tohum + "|" + anahtar, g = globalId(a), k = 0;
    while (this.kullanilanId[g]) { k += 1; g = globalId(a + "#" + k); }
    this.kullanilanId[g] = true;
    return { _ham: "'" + g + "'", _gid: true };
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
  Uretici.prototype.sekil = function (katilar, tip) {
    const rep = this.w.ekle("IFCSHAPEREPRESENTATION", [this.ctxBody, "Body", tip || "SweptSolid", katilar]);
    return this.w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [rep]]);
  };
  Uretici.prototype.uzat = function (profil, uzunluk, konum2) {
    return this.w.ekle("IFCEXTRUDEDAREASOLID", [profil, konum2 || null, this.yon([0, 0, 1]), uzunluk]);
  };

  // Dosyayı yazan uygulama: secenek.uygulama {ad, surum, firma, tam_ad} (ad verilmişse), yoksa "Matris Öğren" + SURUM.
  // onislemci = FILE_NAME preprocessor_version ("ad surum"), tam_ad = originating_system ve ApplicationFullName.
  Uretici.prototype.uygulamaKimligi = function () {
    const u = sozluk(this.s.uygulama);
    if (u.ad == null || String(u.ad) === "") {
      return { ad: UYGULAMA_AD, surum: SURUM, firma: UYGULAMA_AD, tam_ad: UYGULAMA_AD, onislemci: UYGULAMA };
    }
    const ad = String(u.ad), surum = u.surum == null ? "" : String(u.surum);
    return { ad: ad, surum: surum, firma: u.firma ? String(u.firma) : ad, tam_ad: u.tam_ad ? String(u.tam_ad) : ad,
      onislemci: ad + (surum ? " " + surum : "") };
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
    const kyatak = tureyen([tur(kN, 1), tur(m, -3)], "MODULUSOFSUBGRADEREACTIONUNIT");     // zemin yatak katsayısı k0 (kN/m³)
    const birimler = w.ekle("IFCUNITASSIGNMENT", [[m, m2, m3, rad, kN, kNm, kNm2, kNxm, kNmm, kyay, kdon, kyatak]]);
    // Sahiplik geçmişi: uygulama kimliği (varsayılan "Matris Öğren"; secenek.uygulama verilirse o)
    const uk = this.uygulamaKimligi();
    const gelistirici = w.ekle("IFCORGANIZATION", [null, uk.firma, null, null, null]);
    const uygulama = w.ekle("IFCAPPLICATION", [gelistirici, uk.surum, uk.tam_ad, uk.ad]);
    const kisi = w.ekle("IFCPERSON", [null, proje.hazirlayan ? String(proje.hazirlayan) : "Kullanıcı", null, null, null, null, null, null]);
    const kurum = proje.kurum ? w.ekle("IFCORGANIZATION", [null, String(proje.kurum), null, null, null]) : gelistirici;
    const kullanici = w.ekle("IFCPERSONANDORGANIZATION", [kisi, kurum, null]);
    const zd = this.zamanDamgasi();
    w.sahip = w.ekle("IFCOWNERHISTORY", [kullanici, uygulama, null, E("ADDED"), I(zd), kullanici, uygulama, I(zd)]);
    const dunya = this.eksen3([0, 0, 0], null, null);
    this.ctx = w.ekle("IFCGEOMETRICREPRESENTATIONCONTEXT", [null, "Model", I(3), 1e-5, dunya, null]);
    this.ctxBody = w.ekle("IFCGEOMETRICREPRESENTATIONSUBCONTEXT", ["Body", "Model", "*", "*", "*", "*", this.ctx, null, E("MODEL_VIEW"), null]);
    this.ctxRef = w.ekle("IFCGEOMETRICREPRESENTATIONSUBCONTEXT", ["Reference", "Model", "*", "*", "*", "*", this.ctx, null, E("GRAPH_VIEW"), null]);
    this.ctxPlan = w.ekle("IFCGEOMETRICREPRESENTATIONSUBCONTEXT", ["FootPrint", "Model", "*", "*", "*", "*", this.ctx, null, E("MODEL_VIEW"), null]);
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
    this.zAkslariPset();
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

  // ---- aks ızgaraları (§19): IfcGrid + IfcGridAxis; UAxes = X aksları (ya da r), VAxes = Y aksları (ya da θ) ----
  // secenek.izgara: "kat" (varsayılan; her Z aksı seviyesinde bir ızgara, o seviyenin katında) | "tek" (en alt seviyede tek) | false
  Uretici.prototype.izgaralar = function () {
    const kip = this.s.izgara === undefined || this.s.izgara === true ? "kat" : this.s.izgara;
    if (!kip) return;
    const Bm = this.Bm, self = this;
    const sistemler = [{ ad: "GLOBAL", tur: "kartezyen", orijin: [0, 0, 0], aci: 0, u: Bm.ax, v: Bm.ay, z: null }].concat(Bm.sistemSira);
    sistemler.forEach(function (S_) {
      if (!S_.u.length || !S_.v.length) {
        if (S_.u.length || S_.v.length) self.uyarilar.push("Aks sistemi " + S_.ad + ": ızgara için iki doğrultuda da aks gerekir; IfcGrid yazılmadı.");
        return;
      }
      let seviyeler = S_.z ? S_.z.map(function (z) { return { ad: z.ad, Z: S_.orijin[2] + z.konum }; })
        : Bm.az.map(function (z) { return { ad: z.ad, Z: z.konum }; });
      if (kip === "tek") seviyeler = [seviyeler.reduce(function (a, b) { return b.Z < a.Z ? b : a; })];
      seviyeler.forEach(function (sv) { self.izgara(S_, sv); });
    });
  };
  Uretici.prototype.izgara = function (S_, sv) {
    const w = this.w, self = this, Bm = this.Bm;
    const kat = this.katlar[seviyeBul(Bm, sv.Z)];
    const pay = 1.5;     // aks çizgisi uç taşması (m)
    const egriler = [];
    const eksen = function (aks, egri, liste) {
      egriler.push(egri);
      liste.push(w.ekle("IFCGRIDAXIS", [aks.ad, egri, true]));
    };
    const U = [], V = [];
    let tip;
    if (S_.tur === "silindirik") {
      tip = "RADIAL";
      const rmax = Math.max.apply(null, S_.u.map(function (a) { return Math.abs(a.konum); })) + pay;
      const merkez = w.ekle("IFCAXIS2PLACEMENT2D", [this.nokta2([0, 0]), null]);
      S_.u.forEach(function (a) {
        if (Math.abs(a.konum) < 1e-6) { self.uyarilar.push("Silindirik sistem " + S_.ad + ": r = 0 aksı (" + a.ad + ") çember olamaz; atlandı."); return; }
        eksen(a, w.ekle("IFCCIRCLE", [merkez, Math.abs(a.konum)]), U);
      });
      S_.v.forEach(function (a) {
        const t = a.konum * Math.PI / 180;
        eksen(a, w.ekle("IFCPOLYLINE", [[self.nokta2([0, 0]), self.nokta2([rmax * Math.cos(t), rmax * Math.sin(t)])]]), V);
      });
      if (!U.length) return;
    } else {
      tip = "RECTANGULAR";
      const u0 = S_.u[0].konum - pay, u1 = S_.u[S_.u.length - 1].konum + pay;
      const v0 = S_.v[0].konum - pay, v1 = S_.v[S_.v.length - 1].konum + pay;
      S_.u.forEach(function (a) { eksen(a, w.ekle("IFCPOLYLINE", [[self.nokta2([a.konum, v0]), self.nokta2([a.konum, v1])]]), U); });
      S_.v.forEach(function (a) { eksen(a, w.ekle("IFCPOLYLINE", [[self.nokta2([u0, a.konum]), self.nokta2([u1, a.konum])]]), V); });
    }
    const aci = S_.aci * Math.PI / 180;
    const yer = this.yerlesim(kat.yer, [S_.orijin[0], S_.orijin[1], sv.Z - kat.kot], S_.aci ? [0, 0, 1] : null, S_.aci ? [Math.cos(aci), Math.sin(aci), 0] : null);
    const rep = w.ekle("IFCSHAPEREPRESENTATION", [this.ctxPlan, "FootPrint", "GeometricCurveSet", [w.ekle("IFCGEOMETRICCURVESET", [egriler])]]);
    const sek = w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [rep]]);
    const ad = "Akslar" + (S_.ad === "GLOBAL" ? "" : " " + S_.ad) + " — " + sv.ad;
    const aciklama = (S_.tur === "silindirik" ? "Silindirik aks sistemi (U: r çemberleri, V: θ doğrultuları)" : "Aks sistemi (U: X aksları, V: Y aksları)") +
      ", kot " + sy(sv.Z) + " m" + (S_.aci ? ", dönme " + S_.aci + "°" : "");
    const g = w.ekle("IFCGRID", [this.gid("izgara:" + S_.ad + ":" + sv.ad), null, ad, aciklama, null, yer, sek, U, V, null, E(tip)]);
    kat.elemanlar.push(g);
    return g;
  };
  // Z aksları (kat seviyesi olmayanlar dahil: saçak, mahya, kren…) binada bir özellik kümesi olarak
  Uretici.prototype.zAkslariPset = function () {
    const Bm = this.Bm;
    if (!dizi(sozluk(Bm.bina.akslar).z).length) return;
    this.pset("bina", "Pset_MatrisOgren_ZAkslari", Bm.az.map(function (z) { return [z.ad, T("IFCLENGTHMEASURE", z.konum)]; }), [this.yapi]);
  };

  // Profil tanımı (kesit adı başına bir kez). Dönüş: {ref, derinlik, derin (vute derin uç profili; yoksa null)}
  Uretici.prototype.profilTanimi = function (k) {
    const anahtar = k.ad;
    if (this.profil[anahtar]) return this.profil[anahtar];
    const w = this.w, ad = k.profil || k.ad;
    let ref, derinlik = k.h || k.D || 0.3, derin = null, kutuR = null;
    if (k.tur === "I") {
      ref = w.ekle("IFCISHAPEPROFILEDEF", [E("AREA"), ad, null, k.b, k.h, k.tw, k.tf, k.r || null, null, null]);
    } else if (k.tur === "kutu") {
      // köşe yarıçapları IFC kurallarına sığdırılır (r_i ≤ min(b, h)/2 − t, r_o ≤ min(b, h)/2; kalın et/küçük kutu)
      const yari = Math.min(k.b, k.h) / 2, ri = k.ri ? Math.min(k.ri, yari - k.t) : 0, ro = k.ro ? Math.min(k.ro, yari) : 0;
      kutuR = [ri > 0 ? ri : null, ro > 0 ? ro : null];
      ref = w.ekle("IFCRECTANGLEHOLLOWPROFILEDEF", [E("AREA"), ad, null, k.b, k.h, k.t, kutuR[0], kutuR[1]]);
    } else if (k.tur === "boru") {
      ref = w.ekle("IFCCIRCLEHOLLOWPROFILEDEF", [E("AREA"), ad, null, k.D / 2, k.t]);
      derinlik = k.D;
    } else if (k.tur === "daire") {
      ref = w.ekle("IFCCIRCLEPROFILEDEF", [E("AREA"), ad, null, k.D / 2]);
      derinlik = k.D;
    } else if (k.tur === "L") {
      ref = w.ekle("IFCLSHAPEPROFILEDEF", [E("AREA"), ad, null, k.h, k.b, k.t, k.r1 || null, k.r2 || null, null]);
    } else if (k.tur === "2L") {
      // iki korniyer sırt sırta (aralık ara): tek IfcCompositeProfileDef. (1): sırtı x = +ara/2'de, yatay kolu +x yönünde;
      // (2): (1)'in y eksenine göre aynası = Depth/Width yer değiştirmiş L'nin +90° döndürülmüşü (yatay kolu −x yönünde, ikisi de altta)
      const kay = k.ara / 2 + k.b / 2;
      const p1 = w.ekle("IFCAXIS2PLACEMENT2D", [this.nokta2([kay, 0]), null]);
      const p2 = w.ekle("IFCAXIS2PLACEMENT2D", [this.nokta2([-kay, 0]), w.ekle("IFCDIRECTION", [[0, 1]])]);
      const l1 = w.ekle("IFCLSHAPEPROFILEDEF", [E("AREA"), ad + " (1)", p1, k.h, k.b, k.t, k.r1 || null, k.r2 || null, null]);
      const l2 = w.ekle("IFCLSHAPEPROFILEDEF", [E("AREA"), ad + " (2)", p2, k.b, k.h, k.t, k.r1 || null, k.r2 || null, null]);
      ref = w.ekle("IFCCOMPOSITEPROFILEDEF", [E("AREA"), ad, [l1, l2], "2L"]);
    } else if (k.tur === "tersT") {
      // ters T temel kesiti: IfcTShapeProfileDef'in başlığı +y'dedir; 180° döndürülür → tabla (B × h_tabla) altta, gövde üstte
      const p = w.ekle("IFCAXIS2PLACEMENT2D", [this.nokta2([0, 0]), w.ekle("IFCDIRECTION", [[-1, 0]])]);
      ref = w.ekle("IFCTSHAPEPROFILEDEF", [E("AREA"), ad, p, k.hg, k.B, k.bg, k.ht, null, null, null, null, null]);
      derinlik = k.hg;
    } else if (k.tur === "U") {
      ref = w.ekle("IFCUSHAPEPROFILEDEF", [E("AREA"), ad, null, k.h, k.b, k.tw, k.tf, k.r1 || null, k.r2 || null, k.egim ? Math.atan(k.egim) : null]);
    } else {
      ref = w.ekle("IFCRECTANGLEPROFILEDEF", [E("AREA"), ad, null, k.b, k.h]);
    }
    // vute: derin uç profili (aynı tür; başlıklar/et aynı, gövde ek yükseklik kadar uzun — motorun _derin_kesit yaklaşımı:
    // I kaynaklı I, dikdörtgen b × (h + ek), kutu ve U derinliği h + ek; kutuda köşe yarıçapları temel profilinkiyle aynı).
    // Üst yüz temel profille aynı hizada kalsın diye −ek/2 kaydırılır (vute alta doğru büyür). Boru, dolu daire, L ve 2L'nin
    // konik karşılığı yok: temel kesitli düz katı (uyarı kesitCoz'da).
    if (k.vute && k.vute.ek_yukseklik > 1e-6 && VUTE_KONIK[k.tur]) {
      const dh = k.vute.ek_yukseklik;
      const yer = w.ekle("IFCAXIS2PLACEMENT2D", [this.nokta2([0, -dh / 2]), null]);
      const dad = ad + " (vute derin uç, h = " + sy(k.h + dh) + " m)";
      if (k.tur === "I") derin = w.ekle("IFCISHAPEPROFILEDEF", [E("AREA"), dad, yer, k.b, k.h + dh, k.tw, k.tf, k.r || null, null, null]);
      else if (k.tur === "kutu") derin = w.ekle("IFCRECTANGLEHOLLOWPROFILEDEF", [E("AREA"), dad, yer, k.b, k.h + dh, k.t, kutuR[0], kutuR[1]]);
      else if (k.tur === "U") {
        derin = w.ekle("IFCUSHAPEPROFILEDEF", [E("AREA"), dad, yer, k.h + dh, k.b, k.tw, k.tf, k.r1 || null, k.r2 || null,
          k.egim ? Math.atan(k.egim) : null]);
      } else derin = w.ekle("IFCRECTANGLEPROFILEDEF", [E("AREA"), dad, yer, k.b, k.h + dh]);
    }
    this.profil[anahtar] = { ref: ref, derinlik: derinlik, derin: derin };
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
  // surum 3 motor kaydı ("cubuk" alanı çubuk no'su; aynı çubuğa birden çok kayıt düşerse D/C'si en büyüğü)
  Uretici.prototype.tasarimCubukBul = function (no) {
    const tas = this.Bm.veri && this.Bm.veri.tasarim;
    if (!tas || !Array.isArray(tas.elemanlar)) return null;
    let en = null;
    tas.elemanlar.forEach(function (e) {
      if (!e || e.cubuk === undefined || e.cubuk === null || +e.cubuk !== +no) return;
      if (!en || (isFinite(+e.dc) && e.dc !== null && !(isFinite(+en.dc) && en.dc !== null && +en.dc >= +e.dc))) en = e;
    });
    return en;
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
      const t = (ek.tasarimCubuk !== undefined ? this.tasarimCubukBul(ek.tasarimCubuk) : null) ||
        this.tasarimBul(ek.tasarimTur, ek.tasarimNo !== undefined ? ek.tasarimNo : ek.no);
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
    const v = o.k.vute;
    let katilar, temsil = "SweptSolid", boy = null;
    if (v) boy = Math.min(v.boy > 0 ? v.boy : L, L);
    if (v && pt.derin && boy > 1e-6) {
      // vute boyu (derin uçtan) IfcExtrudedAreaSolidTapered: derin uç profilinden temel profile; kalan boy sabit kesitli
      const self = this, kalan = L - boy;
      const sivri = function (p0, p1, z0, uz) {
        return w.ekle("IFCEXTRUDEDAREASOLIDTAPERED", [p0, z0 ? self.eksen3([0, 0, z0], null, null) : null, self.yon([0, 0, 1]), uz, p1]);
      };
      if (v.derin_uc === "j") {
        katilar = (kalan > 1e-6 ? [this.uzat(pt.ref, kalan)] : []).concat([sivri(pt.ref, pt.derin, kalan > 1e-6 ? kalan : 0, boy)]);
      } else {
        katilar = [sivri(pt.derin, pt.ref, 0, boy)].concat(kalan > 1e-6 ? [this.uzat(pt.ref, kalan, this.eksen3([0, 0, boy], null, null))] : []);
      }
      temsil = "AdvancedSweptSolid";
    } else {
      katilar = [this.uzat(pt.ref, L)];
    }
    const sek = this.sekil(katilar, temsil);
    const ref = w.ekle(o.sinif, [this.gid(o.anahtar), null, o.ad, o.aciklama || null, o.k.ad, yer, sek, o.etiket || null, E(o.tip)]);
    kat.elemanlar.push(ref);
    const kul = this.profilKullanimi(o.k, o.kardinal);
    this.malzemeBagla(kul, ref);
    this.ortakPsetler(o.anahtar, ref, o.sinif, o.k, o.ek || {});
    if (v) {
      this.pset(o.anahtar, "Pset_MatrisVute", [
        ["TemelKesit", T("IFCLABEL", v.temel)], ["TemelProfil", T("IFCLABEL", v.temelProfil)],
        ["EkYukseklik", T("IFCLENGTHMEASURE", v.ek_yukseklik)], ["Boy", T("IFCPOSITIVELENGTHMEASURE", boy)],
        ["DerinUc", T("IFCLABEL", v.derin_uc)],
        ["DerinUcYuksekligi", (o.k.h || o.k.D) ? T("IFCPOSITIVELENGTHMEASURE", (o.k.h || o.k.D) + v.ek_yukseklik) : null],
      ], [ref]);
    }
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
      const k = self.kesit(c.kesit);
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
      const k = self.kesit(kr.kesit);
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
      const k = self.kesit(c.kesit);
      const yatay = Math.abs(t[2]) < 1e-6;
      const kat = c.kat !== undefined ? +c.kat : null;
      const zKat = tur === "kolon" ? seviyeBul(Bm, Math.min(p1[2], p2[2])) : (kat !== null && Bm.kat[kat] ? kat : seviyeBul(Bm, Math.max(p1[2], p2[2])));
      // aks–kat modelinden genelleştirilmiş çubuk (model_ops.genellestir: kaynak.aks_kat) → tasarım kaydı bina kolon/kiriş no'suyla
      const kay = sozluk(c.kaynak), akTur = kay.aks_kat === "kolon" || kay.aks_kat === "kiris" ? kay.aks_kat : null;
      const ad = (CUBUK_AD[tur] || "Çubuk") + " Ç" + no + (c.grup ? " (" + c.grup + ")" : "") +
        (akTur ? " [" + (akTur === "kolon" ? "kolon " : "kiriş ") + kay.no + (kay.parca ? "/" + kay.parca : "") + "]" : "");
      self.cubukEleman({ sinif: sin[0], tip: sin[1], anahtar: "cubuk:" + no, ad: ad, etiket: "C" + no, kat: zKat,
        aciklama: (CUBUK_AD[tur] || "Çubuk") + " " + no + " (" + k.ad + (c.aci ? ", açı " + c.aci + "°" : "") + ")",
        p1: p1, p2: p2, d: d, kardinal: (tur === "kiris" && yatay) ? 8 : 5, k: k,
        ek: { adres: "C" + no, tur: c.tur || "diger", no: no, kat: kat === null ? undefined : kat, aciklik: vboy(vfark(p2, p1)),
          tasarimTur: akTur || "cubuk", tasarimNo: akTur ? kay.no : no, tasarimCubuk: no,
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
  // veri.temel (temel.py; mütemadi/radye) varsa temel hatları, plak sınırları ve kesitler oradan; yoksa bina.temeller'den
  // (motorla aynı kurallar: "tum" seçiminde zemin kat kolonu olmayan aks atlanır; hat uçları = uç kolonlar ± taşma).
  Uretici.prototype.veriTemel = function () {
    const vt = this.Bm.veri && this.Bm.veri.temel;
    if (!vt || typeof vt !== "object") return null;
    const tip = String(vt.tip || "").toLowerCase();
    return (tip === "surekli" || tip === "radye") && Array.isArray(vt.dugumler) && vt.dugumler.length ? vt : null;
  };
  // Ters T kesit nesnesi (tabla B × h_tabla, gövde b_govde, toplam yükseklik h_govde); tabla yoksa dikdörtgen
  Uretici.prototype.tersTKesit = function (Bt, ht, bg, hg, malzeme) {
    const g = function (x) { return sy(x); };
    if (!(ht > 0) || bg >= Bt - 1e-9 || ht >= hg - 1e-9) {
      const b = Math.max(Bt, bg);
      return { ad: "TK " + g(b) + "x" + g(hg), tur: "dikdortgen", b: b, h: hg, malzeme: malzeme };
    }
    return { ad: "TK " + g(Bt) + "/" + g(ht) + "-" + g(bg) + "/" + g(hg), tur: "tersT", B: Bt, ht: ht, bg: bg, hg: hg, malzeme: malzeme };
  };
  // Zemin özellikleri ve tasarım D/C'si (Pset_MatrisOgren alanları)
  Uretici.prototype.temelOzellik = function (vt, dc) {
    const o = [];
    if (vt) {
      const md = sozluk(vt.model);
      if (isFinite(+vt.q_em)) o.push(["q_em", T("IFCPLANARFORCEMEASURE", +vt.q_em)]);
      if (isFinite(+md.k0)) o.push(["k0", T("IFCMODULUSOFSUBGRADEREACTIONMEASURE", +md.k0)]);
      if (isFinite(+vt.p_maks)) o.push(["p_maks", T("IFCPLANARFORCEMEASURE", +vt.p_maks)]);
      if (isFinite(+vt.DC_zemin)) o.push(["DC_zemin", T("IFCRATIOMEASURE", +vt.DC_zemin)]);
      if (isFinite(+vt.oturma_maks_mm)) o.push(["Oturma_maks", T("IFCLENGTHMEASURE", +vt.oturma_maks_mm / 1000)]);
    }
    if (this.s.sonuclar && dc && isFinite(+dc.dc)) {
      o.push(["DC", T("IFCRATIOMEASURE", +dc.dc)]);
      if (dc.durum) o.push(["TasarimDurumu", T("IFCLABEL", String(dc.durum))]);
    }
    return o;
  };
  Uretici.prototype.temeller = function (beton) {
    const Bm = this.Bm, self = this, t = sozluk(Bm.bina.temeller);
    const tip = String(t.tip || "tekil").toLowerCase();
    const z0 = Bm.kot0, kat0 = Bm.katlar[0].no;
    const tabanlar = this.kolonTabanlari();
    const vt = this.veriTemel();
    const md = vt ? sozluk(vt.model) : {};
    const malz = beton.anahtar || beton.ad;
    const tasarimlar = vt ? dizi(vt.tasarim) : [];
    const enDc = function (l) { return l.filter(function (x) { return x && isFinite(+x.dc); }).sort(function (a, b) { return b.dc - a.dc; })[0] || null; };
    // hat (yon, sabit, bas, son) → temel kirişi / radye kirişi çubuğu (üstü temel kotunda)
    const hatCubugu = function (h, sinif, tip_, k, ad, aciklama, ozel) {
      const p1 = h.yon === "x" ? [h.bas, h.sabit, z0] : [h.sabit, h.bas, z0];
      const p2 = h.yon === "x" ? [h.son, h.sabit, z0] : [h.sabit, h.son, z0];
      self.cubukEleman({ sinif: sinif, tip: tip_, anahtar: "temel-hat:" + h.no, ad: ad, etiket: ad, kat: kat0, aciklama: aciklama,
        p1: p1, p2: p2, d: [0, 0, 1], kardinal: 8, k: k, ek: { adres: ad, tur: tip_ === "STRIP_FOOTING" ? "temel-kirisi" : "radye-kirisi", ozel: ozel } });
    };
    if (tip === "surekli" || tip === "mutemadi" || tip === "mütemadi" || tip === "sürekli") {
      const s = Object.assign({ yon: "xy", akslar: "tum", B: 1.2, h_tabla: 0.4, b_govde: 0.5, h_govde: 1.0, tasma: 0.5 }, sozluk(t.surekli));
      const ks = sozluk(md.kesit);
      const Bt = sayi(ks.B, sayi(s.B, 1.2)), ht = sayi(ks.h_tabla, sayi(s.h_tabla, 0.4)), bg = sayi(ks.b_govde, sayi(s.b_govde, 0.5));
      const hg = Math.max(sayi(ks.h_govde, sayi(s.h_govde, 1.0)), ht);
      const k = this.tersTKesit(Bt, ht, bg, hg, malz);
      let hatlar;
      if (vt && dizi(vt.hatlar).length) {
        hatlar = dizi(vt.hatlar).map(function (h) { return { no: h.no, ad: String(h.ad), yon: h.yon, sabit: +h.sabit, bas: +h.bas, son: +h.son }; });
      } else {
        const tas = sayi(s.tasma, 0.5), yonlar = String(s.yon || "xy").toLowerCase();
        const liste = Array.isArray(s.akslar) ? s.akslar.map(String) : null;
        hatlar = [];
        const ekle = function (yon, a) {
          if (liste && liste.indexOf(a.ad) < 0) return;
          const kol = tabanlar.filter(function (tb) { return Math.abs((yon === "x" ? tb.Y : tb.X) - a.konum) < 1e-6; })
            .map(function (tb) { return yon === "x" ? tb.X : tb.Y; });
          if (!kol.length) {
            if (liste) self.uyarilar.push("Mütemadi temel: " + a.ad + " aksında zemin kat kolonu yok; temel kirişi yazılmadı.");
            return;
          }
          const bas = Math.min.apply(null, kol) - tas, son = Math.max.apply(null, kol) + tas;
          if (son - bas > 1e-6) hatlar.push({ no: hatlar.length + 1, ad: a.ad, yon: yon, sabit: a.konum, bas: bas, son: son });
        };
        if (yonlar.indexOf("x") >= 0) Bm.ay.forEach(function (a) { ekle("x", a); });     // X yönünde: sayılı aks çizgileri boyunca
        if (yonlar.indexOf("y") >= 0) Bm.ax.forEach(function (a) { ekle("y", a); });     // Y yönünde: harfli aks çizgileri boyunca
      }
      hatlar.forEach(function (h) {
        const dc = enDc(tasarimlar.filter(function (x) { return x.tur === "temel-kirisi" && String(x.hat) === h.ad; }));
        hatCubugu(h, "IFCFOOTING", "STRIP_FOOTING", k, "TK-" + h.ad,
          "Mütemadi (sürekli) temel kirişi, " + (k.tur === "tersT" ? "ters T" : "dikdörtgen") + " kesit, " + h.yon.toUpperCase() + " doğrultusu",
          [["B", T("IFCPOSITIVELENGTHMEASURE", Bt)], ["h_tabla", T("IFCLENGTHMEASURE", k.tur === "tersT" ? ht : 0)],
            ["b_govde", T("IFCPOSITIVELENGTHMEASURE", bg)], ["h_govde", T("IFCPOSITIVELENGTHMEASURE", hg)]].concat(self.temelOzellik(vt, dc)));
      });
      return;
    }
    if (tip === "radye") {
      const r = Object.assign({ h: 0.8, tasma: 1.0, kiris: null }, sozluk(t.radye));
      const h = sayi(md.h, sayi(r.h, 0.8)), tas = sayi(r.tasma, 1.0);
      const xs = Bm.ax.map(function (a) { return a.konum; }), ys = Bm.ay.map(function (a) { return a.konum; });
      const pl = sozluk(md.plak);
      const x0 = sayi(pl.X0, xs[0] - tas), x1 = sayi(pl.X1, xs[xs.length - 1] + tas);
      const y0 = sayi(pl.Y0, ys[0] - tas), y1 = sayi(pl.Y1, ys[ys.length - 1] + tas);
      this.kutuEleman({ sinif: "IFCSLAB", tip: "BASESLAB", anahtar: "radye", ad: "Radye temel", etiket: "R", kat: kat0,
        aciklama: "Radye (plak) temel, h = " + sy(h) + " m", nesneTipi: "Radye", profilAd: "Radye",
        cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, dx: x1 - x0, dy: y1 - y0, zUst: z0, h: h, malzeme: beton,
        ek: { adres: "Radye", tur: "radye", referans: "Radye", dis: true,
          ozel: [["Kalinlik", T("IFCPOSITIVELENGTHMEASURE", h)]].concat(this.temelOzellik(vt, enDc(tasarimlar))) } });
      const kir = vt ? (md.kiris && typeof md.kiris === "object" ? md.kiris : null) : r.kiris;
      if (kir && sayi(kir.b, 0) > 0 && sayi(kir.h, 0) > 0) {
        const k = { ad: "RK " + sy(kir.b) + "x" + sy(kir.h), tur: "dikdortgen", b: +kir.b, h: +kir.h, malzeme: malz };
        let hatlar;
        if (vt && dizi(vt.hatlar).length) {
          hatlar = dizi(vt.hatlar).filter(function (x) { return x.kirisli; })
            .map(function (x) { return { no: x.no, ad: String(x.ad), yon: x.yon, sabit: +x.sabit, bas: +x.bas, son: +x.son }; });
        } else {
          hatlar = Bm.ay.map(function (a, i) { return { no: "x" + (i + 1), ad: a.ad, yon: "x", sabit: a.konum, bas: x0, son: x1 }; })
            .concat(Bm.ax.map(function (a, i) { return { no: "y" + (i + 1), ad: a.ad, yon: "y", sabit: a.konum, bas: y0, son: y1 }; }));
        }
        hatlar.forEach(function (hh) {
          const dc = enDc(tasarimlar.filter(function (x) { return x.tur === "temel-kirisi" && String(x.hat) === hh.ad; }));
          hatCubugu(hh, "IFCFOOTING", "FOOTING_BEAM", k, "RK-" + hh.ad, "Kirişli radye: temel kirişi (plak dahil yükseklik " + sy(kir.h) + " m)",
            [["b", T("IFCPOSITIVELENGTHMEASURE", +kir.b)], ["h", T("IFCPOSITIVELENGTHMEASURE", +kir.h)]].concat(self.temelOzellik(null, dc)));
        });
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
      // ad: aks kesişimi adı (seviye eki atılır: "A1/k0" → "A1", "KANAT-B:P1/±0.00" → "KANAT-B:P1"); yoksa düğüm no
      const ad = alt.ad && alt.ad.lastIndexOf("/") > 0 ? alt.ad.slice(0, alt.ad.lastIndexOf("/")) : "N" + alt.no;
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
  // Temel ağı elemanının kesiti (temel.py ile aynı): mütemadi temel kirişi ters T (model.kesit); radye şeridi b × h
  // (b = şerit genişliği, kenarda yarım); kirişli radyede aks şeridi ters T (tabla = şerit b × radye h, gövde = kiriş b × h)
  Uretici.prototype.temelElemanKesiti = function (vt, x, tur) {
    const md = sozluk(vt.model), malz = betonMalzeme(this.Bm);
    const m = malz.anahtar || malz.ad;
    x = x || {};
    if (String(vt.tip) === "surekli") {
      const ks = sozluk(md.kesit);
      return this.tersTKesit(sayi(ks.B, sayi(x.b, 1)), sayi(ks.h_tabla, 0), sayi(ks.b_govde, sayi(x.b, 1)), sayi(ks.h_govde, sayi(x.h, 1)), m);
    }
    const b = sayi(x.b, sayi(md.ag, 1)), h = sayi(md.h, sayi(x.h, 0.5));
    if (tur === "temel-kirisi" && md.kiris && typeof md.kiris === "object") {
      const kb = sayi(md.kiris.b, b), kh = sayi(md.kiris.h, h);
      return b >= kb ? this.tersTKesit(b, h, kb, kh, m) : { ad: "RK " + sy(kb) + "x" + sy(kh), tur: "dikdortgen", b: kb, h: kh, malzeme: m };
    }
    return { ad: "RŞ " + sy(b) + "x" + sy(h), tur: "dikdortgen", b: b, h: h, malzeme: m };
  };
  // Zemin yayları (temel.py ağ kuralı): k_z = k0·A (A: düğüm etki alanı, veri.temel.dugumler[].A); yatay "tutulu" ise X, Y
  // ötelemeleri ve düşey eksen etrafında dönme tutulu, "yay" ise k_h = kh_oran·k_z; mütemadide kiriş ekseni etrafında dönme yayı
  // k_θ = k0·B³/12·l_etki (l_etki: hat üzerindeki komşu düğümlere yarı uzaklıkların toplamı). Dönüş: [{dugum, ux..rz, k0, A}]
  Uretici.prototype.zeminYaylari = function (vt) {
    const md = sozluk(vt.model), k0 = sayi(md.k0, sayi(sozluk(sozluk(this.Bm.bina.temeller).zemin).k0, 20000));
    const tutulu = String(md.yatay || "tutulu") !== "yay", kh = sayi(md.kh_oran, 0);
    const kon = {}, krX = {}, krY = {};
    vt.dugumler.forEach(function (d) { kon[d.no] = d; });
    if (String(vt.tip) === "surekli") {
      const Bt = sayi(sozluk(md.kesit).B, 0);
      dizi(vt.hatlar).forEach(function (h) {
        const ns = dizi(h.dugumler).filter(function (n) { return kon[n]; });
        const c = function (n) { return h.yon === "x" ? +kon[n].X : +kon[n].Y; };
        const hedef = h.yon === "x" ? krX : krY;
        ns.forEach(function (n, i) {
          const l = (i > 0 ? (c(n) - c(ns[i - 1])) / 2 : 0) + (i < ns.length - 1 ? (c(ns[i + 1]) - c(n)) / 2 : 0);
          hedef[n] = (hedef[n] || 0) + k0 * Math.pow(Bt, 3) / 12 * Math.abs(l);
        });
      });
    }
    return vt.dugumler.filter(function (d) { return +d.A > 0; }).map(function (d) {
      const kz = k0 * d.A;
      return { dugum: d.no, k0: k0, A: +d.A, ux: tutulu ? true : (kh > 0 ? kh * kz : false), uy: tutulu ? true : (kh > 0 ? kh * kz : false), uz: kz,
        rx: krX[d.no] > 0 ? krX[d.no] : false, ry: krY[d.no] > 0 ? krY[d.no] : false, rz: tutulu };
    });
  };

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
      const vt = this.veriTemel();
      const temelEl = {};
      if (vt) dizi(vt.elemanlar).forEach(function (x) { temelEl[x.no] = x; });
      Bm.ag.elemanlar.forEach(function (e) {
        const kay = sozluk(e.kaynak);
        const tur = e.tur || kay.tur || "diger";
        const kno = e.kaynak_no !== undefined ? e.kaynak_no : kay.no;
        const temel = tur === "temel-kirisi" || tur === "radye-serit";
        const kb = temel ? {} : kaynakBilgi(kay.tur === "cubuk" ? "cubuk" : tur, kno);
        const dd = dizi(e.dugumler);
        if (dd.length < 2 || efendi[dd[0]] || efendi[dd[1]]) return;
        // motorun yerel eksenleri (lam: satırlar x′, y′, z′ bina koordinatında) varsa derinlik y′'den alınır
        const lam = dizi(e.lam), ly = dizi(lam[1]);
        const dLam = ly.length === 3 && ly.every(function (x) { return isFinite(+x); }) && vboy(ly.map(Number)) > 0.5 ? vbirim(ly.map(Number)) : null;
        const kayit = { no: e.no, i: dug.no[dd[0]], j: dug.no[dd[1]], tur: tur, kaynakTur: kay.tur === "cubuk" ? "cubuk" : tur, kaynakNo: kno,
          parca: e.parca, kesit: e.kesit || kb.kesit, yon: kb.yon, aci: e.aci !== undefined ? e.aci : kb.aci, serbest: e.serbest || kb.serbest,
          yalniz_cekme: e.yalniz_cekme || kb.yalniz_cekme, adres: e.adres, dLam: dLam,
          // surum 3: motorun çubuk no'su (bir çubuk birden çok FE parçası olabilir) ve yerel eksenler (satırlar x′, y′, z′)
          cubuk: e.cubuk !== undefined && e.cubuk !== null ? +e.cubuk : (kay.tur === "cubuk" ? kno : undefined),
          lam: lam.length === 3 && lam.every(function (r) { return dizi(r).length === 3 && dizi(r).every(function (x) { return isFinite(+x); }); })
            ? lam.map(function (r) { return r.map(Number); }) : null };
        if (temel) {
          // temel kirişi / radye şeridi (temel.py ağı): kesit veri.temel'den, fiziksel karşılık temel hattı ya da radye plağı
          kayit.kesitObj = self.temelElemanKesiti(vt, temelEl[e.no], tur);
          kayit.kesit = kayit.kesitObj.ad;
          kayit.fizikAnahtar = tur === "radye-serit" ? "radye" : "temel-hat:" + kno;
        }
        elemanlar.push(kayit);
      });
      const tem = sozluk(Bm.bina.temeller);
      const k0 = sayi(sozluk(tem.zemin).k0, 20000);
      const tbl = {};
      dizi(tem.liste).concat(dizi(tem.ozel)).forEach(function (o) { if (o && o.aks) tbl[o.aks[0] + "|" + o.aks[1]] = o; });
      if (vt) this.zeminYaylari(vt).forEach(function (m) { const d = dug.no[m.dugum]; if (d) mesnetler.push({ d: d, yay: m }); });
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
          aci: c.aci, serbest: c.serbest, yalniz_cekme: c.yalniz_cekme, cubuk: c.no === undefined ? n + 1 : +c.no });
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
      // aks–kat kolonu: motor eksenleri sabit tutup Iy/Iz'yi takas eder (§2), bu yüzden kesit yönü "yon"dan
      if (e.tur === "kolon" && e.yon) e.d = e.yon === "y" ? [0, 1, 0] : [1, 0, 0];
      else if (e.dLam && Math.abs(vic(e.dLam, t)) < 1e-6) e.d = e.dLam;
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
      if (m.yay) {
        const y = m.yay;
        const bil = function (v, tip) { return typeof v === "number" ? [tip, v] : !!v; };
        const deg = [bil(y.ux, "IFCLINEARSTIFFNESSMEASURE"), bil(y.uy, "IFCLINEARSTIFFNESSMEASURE"), bil(y.uz, "IFCLINEARSTIFFNESSMEASURE"),
          bil(y.rx, "IFCROTATIONALSTIFFNESSMEASURE"), bil(y.ry, "IFCROTATIONALSTIFFNESSMEASURE"), bil(y.rz, "IFCROTATIONALSTIFFNESSMEASURE")];
        const anahtar = "yay:" + deg.map(function (v) { return Array.isArray(v) ? R(v[1]) : (v ? "T" : "F"); }).join(",");
        ref = kosul(anahtar, "Zemin yayı (Winkler): k_z = k0·A = " + sy(y.k0) + " × " + sy(y.A) + " = " + sy(y.uz) + " kN/m",
          deg[0], deg[1], deg[2], deg[3], deg[4], deg[5]);
      } else if (m.serbestlik) {
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
    this.diyaframMerkezleri(yer, baglanti, uyeler, tepe);
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
      if (e.kesitObj || e.kesit) {
        const k = e.kesitObj || self.kesit(e.kesit, false);
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
      // fiziksel karşılık: temel hattı/radye; surum 3 çubuğu (motor ağında tur "kolon"/"kiris" olsa da fiziksel anahtar "cubuk:no"); aks–kat
      const fk = e.fizikAnahtar || (e.cubuk !== undefined && self.fizik["cubuk:" + e.cubuk] ? "cubuk:" + e.cubuk : (e.kaynakTur || e.tur) + ":" + e.kaynakNo);
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

  // Rijit diyafram efendi düğümleri (C16): eylem (kat kuvveti, burulma momenti) taşıyan her efendi düğüm "Kat k diyafram merkezi"
  // IfcStructuralPointConnection'ı olur (veri.ag.dugumler, yoksa veri.ag.diyaframlar konumunda; baglanti[efendi no]). IFC4'te
  // diyafram kısıtı varlığı yok ve her yapısal bağlantı en az bir üyeye bağlı olmalı (IfcStructuralConnection.ConnectsStructuralMembers
  // SET [1:?]); motorun modeli birebir şöyle yazılır: efendi düğümün yalnız ux, uy, rz serbestliği var (uz, rx, ry tutulu koşul) ve
  // kat düğümlerine (veri.ag.diyaframlar[].dugumler) kesitsiz rijit bağ üyeleriyle bağlanır; bağın kat düğümü ucunda düşey kesme,
  // burulma ve yatay eksenli eğilme serbest (Vy, T, Mz) — bağ yalnız yatay ötelemeyi ve düşey eksen etrafında dönmeyi aktarır.
  // Efendi düğüm bir kat düğümüyle çakışıyorsa (1 mm; simetrik planda ortadaki kolon) ayrı merkez bağlantısı yazılmaz: aynı konumda
  // iki bağlantı olur, ortak düğüm diyaframa bağlanmaz ve düğümleri birleştiren okuyucuda merkezin uz, rx, ry koşulu kat düğümünü
  // mesnetlerdi. Merkez o kat düğümünün kendi bağlantısıdır (eylemler ona, rijit bağlar ondan öteki kat düğümlerine).
  Uretici.prototype.diyaframMerkezleri = function (yer, baglanti, uyeler, tepe) {
    const Bm = this.Bm, w = this.w, self = this, dug = this.dug;
    const Y = Bm.veri && Bm.veri.yukler;
    this.diyaframNo = {};
    if (!Bm.ag || this.s.yukler === false || !Y || !Y.eylemler || typeof Y.eylemler !== "object") return;
    const efendi = {}, diy = {}, gerekli = {};
    Bm.ag.dugumler.forEach(function (d) { if (d && d.efendi) efendi[+d.no] = d; });
    dizi(Bm.ag.diyaframlar).forEach(function (d) { if (d && d.ana !== undefined && d.ana !== null) diy[+d.ana] = d; });
    Object.keys(Y.eylemler).forEach(function (dr) {
      dizi(sozluk(Y.eylemler[dr]).dugumler).forEach(function (n) {
        const no = n ? +n.dugum : NaN;
        if ((efendi[no] || diy[no]) && !baglanti[no]) gerekli[no] = true;
      });
    });
    let kosul = null, ucKosul = null;
    Object.keys(gerekli).map(Number).sort(function (a, b) { return a - b; }).forEach(function (no) {
      const d = efendi[no] || {}, g = diy[no] || {};
      const P = [sayi(d.X, sayi(g.X, NaN)), sayi(d.Y, sayi(g.Y, NaN)), sayi(d.Z, sayi(g.Z, NaN))];
      if (!P.every(isFinite)) return;               // konumsuz: yükü "karşılığı olmayan düğüm" sayılır
      // bağlanacak kat düğümleri (analiz modelinde olan); efendiyle çakışan kat düğümü (ortak) merkezin kendisi olur
      const gor = {}, kole = [];
      let ortak = null;
      dizi(g.dugumler).forEach(function (n) {
        const x = dug.no[+n];
        if (!x || !baglanti[x.no] || gor[x.no]) return;
        gor[x.no] = true;
        if (!ortak && vboy(vfark([x.X, x.Y, x.Z], P)) < 1e-3) ortak = x;
        else kole.push(x);
      });
      if (!kole.length && !ortak) return;
      const km = d.kat !== undefined && d.kat !== null ? d.kat : (/(\d+)/.exec(String(g.ad || "")) || [])[1];
      const kat = km !== undefined && km !== null ? "Kat " + km : "Diyafram " + no;
      if (kole.length && !ucKosul) {
        ucKosul = w.ekle("IFCBOUNDARYNODECONDITION", ["Diyafram bağı ucu (Vy, T, Mz serbest)", T("IFCBOOLEAN", true), T("IFCBOOLEAN", false),
          T("IFCBOOLEAN", true), T("IFCBOOLEAN", false), T("IFCBOOLEAN", true), T("IFCBOOLEAN", false)]);
      }
      let merkez, vp, Pm = P;
      if (ortak) {
        merkez = baglanti[ortak.no];
        vp = tepe[ortak.no];
        Pm = [ortak.X, ortak.Y, ortak.Z];
      } else {
        if (!kosul) {
          kosul = w.ekle("IFCBOUNDARYNODECONDITION", ["Diyafram merkezi (uz, rx, ry tutulu; ux, uy, rz kat düğümlerine rijit bağlı)",
            T("IFCBOOLEAN", false), T("IFCBOOLEAN", false), T("IFCBOOLEAN", true), T("IFCBOOLEAN", true), T("IFCBOOLEAN", true), T("IFCBOOLEAN", false)]);
        }
        vp = w.ekle("IFCVERTEXPOINT", [self.nokta(P)]);
        const rep = w.ekle("IFCTOPOLOGYREPRESENTATION", [self.ctxRef, "Reference", "Vertex", [vp]]);
        const sek = w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [rep]]);
        merkez = w.ekle("IFCSTRUCTURALPOINTCONNECTION", [self.gid("yd:" + no), null, kat + " diyafram merkezi",
          "Rijit diyafram efendi düğümü N" + no + " (kütle merkezi; " + kole.length + " kat düğümüne rijit bağlı)", null, yer, sek, kosul, null]);
        uyeler.push(merkez);
      }
      baglanti[no] = merkez;
      self.diyaframNo[no] = true;
      kole.forEach(function (x) {
        const t = vbirim(vfark([x.X, x.Y, x.Z], Pm)), dd = derinlikYonu(t, 0);
        const ed = w.ekle("IFCEDGE", [vp, tepe[x.no]]);
        const r2 = w.ekle("IFCTOPOLOGYREPRESENTATION", [self.ctxRef, "Reference", "Edge", [ed]]);
        const s2 = w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [r2]]);
        const uye = w.ekle("IFCSTRUCTURALCURVEMEMBER", [self.gid("ydb:" + no + ":" + x.no), null, kat + " diyafram bağı → " + (x.ad || "N" + x.no),
          "Rijit diyafram bağı (kesitsiz kinematik bağ; yatay öteleme ve düşey eksen etrafında dönme aktarır)", null, yer, s2,
          E("RIGID_JOINED_MEMBER"), self.yon(dd)]);
        uyeler.push(uye);
        w.ekle("IFCRELCONNECTSSTRUCTURALMEMBER", [self.gid("ydbb:" + no + ":" + x.no + ":i"), null, null, null, uye, merkez, null, null, null, null]);
        w.ekle("IFCRELCONNECTSSTRUCTURALMEMBER", [self.gid("ydbb:" + no + ":" + x.no + ":j"), null, null, null, uye, baglanti[x.no], ucKosul, null, null,
          self.eksen3([x.X, x.Y, x.Z], vdis(t, dd), t)]);
      });
    });
  };

  function eylemTipi(ad) {
    const a = String(ad);
    if (a === "G" || a.indexOf("G~") === 0) return ["PERMANENT_G", "DEAD_LOAD_G", "Sabit yük (G)"];
    if (a === "Q") return ["VARIABLE_Q", "LIVE_LOAD_Q", "Hareketli yük (Q)"];
    if (a === "S") return ["VARIABLE_Q", "SNOW_S", "Kar yükü (S)"];
    if (a[0] === "W") return ["VARIABLE_Q", "WIND_W", "Rüzgâr yükü (" + a + ")"];
    if (a[0] === "E") return ["EXTRAORDINARY_A", "EARTHQUAKE_E", "Deprem etkisi (" + a + ")"];
    if (a === "T") return ["VARIABLE_Q", "TEMPERATURE_T", "Sıcaklık / büzülme / oturma (T)"];
    if (a[0] === "K") return ["VARIABLE_Q", "NOTDEFINED", "Kren yükü (" + a + ")"];       // K ve kren alt durumları (K1.1a…)
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
      Object.keys(sozluk(sozluk(veri.yukler).eylemler)).forEach(ekle);     // eylemi olan her durumun yük durumu var (C16)
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

  // Yükler (yalnız veri varsa). Aks–kat: G, Q ve S, veri.yukler.kirisler/dosemeler/kolonlar'dan kiriş parçasına (yayılı, kN/m, aşağı +)
  // ve düğüme (tekil); kar yalnız çatı katı (veri.kar.kat) döşeme paylarında, tepe s·lx/2 (motordaki gibi). surum 3 (genel model):
  // G, Q ve S, veri.yukler.cubuklar/paneller ve bina.ek_yukler'den (genelYukler).
  // Rüzgâr, deprem ve kren (C16): veri.yukler.eylemler[durum] o durumun yük durumuna — cubuklar[].yayili/tekil (genel model; bina
  // eksenlerinde q·vek, FE parçalarına bölünür), dugumler[].F düğüme (rijit diyafram efendi düğümü kendi bağlantısında:
  // diyaframMerkezleri); EZ = G_carpani × (bütün G eylemleri). eylemler_not ya da eylemler yoksa bu etkiler yalnız yük
  // durumu/birleşim olarak kalır (uyarı). Temel öz ağırlığı (C11, mütemadi/radye): veri.temel.oz_yuk G eylemleri olarak temel
  // analiz üyelerine (q) ve temel düğümlerine (P); eski çözümde γ·A yaklaşığı (uyarı).
  // Yayılı yükler analiz üyesi × yük durumu × doğrultu başına bir IfcStructuralLinearAction (düzgün) ya da IfcStructuralCurveAction
  // (POLYGONAL; konumlar üyenin i ucundan, m).
  const ASAGI = [0, 0, -1];
  const ASAGI_ANAHTAR = ASAGI.map(R).join(",");
  Uretici.prototype.yukler = function (baglanti) {
    const Bm = this.Bm, veri = Bm.veri, w = this.w, self = this;
    if (!veri || !veri.yukler) return;
    const Y = veri.yukler;
    const yayili = {};     // eleman no → durum → [{sekil, vek, kaynak}]; şekil = [[x1, x2, w1, w2], ...] (kN/m, vek doğrultusunda +)
    const ekle = function (eno, durum, sekil, vek, kaynak) {
      const r = yayili[eno] = yayili[eno] || {};
      (r[durum] = r[durum] || []).push({ sekil: sekil, vek: vek || ASAGI, kaynak: kaynak || null });
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
      // kar ek yükü (kirişe S durumunda düzgün yayılı ek yük): kN_m'de yok, toplamı S.ek (kN) = q·L
      const L = sayi(r.L, 0), s = L > 0 ? sayi(sozluk(r.S).ek, 0) / L : 0;
      dizi(parcaElemanlari[r.no]).forEach(function (p) {
        if (g) ekle(p.no, "G", [[0, p.L, g, g]]);
        if (q) ekle(p.no, "Q", [[0, p.L, q, q]]);
        if (s) ekle(p.no, "S", [[0, p.L, s, s]]);
      });
    });
    // kar (S): yalnız çatı katı (veri.kar.kat) döşemelerinde s = μ·Ce·Ct·Sk (kN/m²); döşeme payının tepe değeri motordaki gibi s·lx/2
    // (G ve Q payıyla aynı birim şekil, parcalar_birim)
    const kar = sozluk(veri.kar), sKar = sayi(kar.s, 0);
    dizi(Y.dosemeler).forEach(function (d) {
      const tepeS = sKar > 0 && kar.kat !== undefined && +d.kat === +kar.kat ? sKar * sayi(d.lx, 0) / 2 : 0;
      dizi(d.paylar).forEach(function (p) {
        if (!self.yapisalUye[p.eleman]) return;
        const pb = dizi(p.parcalar_birim);
        if (!pb.length) return;
        if (sayi(p.tepe_g, 0)) ekle(p.eleman, "G", pb.map(function (s) { return [s[0], s[1], s[2] * p.tepe_g, s[3] * p.tepe_g]; }));
        if (sayi(p.tepe_q, 0)) ekle(p.eleman, "Q", pb.map(function (s) { return [s[0], s[1], s[2] * p.tepe_q, s[3] * p.tepe_q]; }));
        const ts = sayi(p.tepe_s, tepeS);
        if (ts) ekle(p.eleman, "S", pb.map(function (s) { return [s[0], s[1], s[2] * ts, s[3] * ts]; }));
      });
    });
    // tekil düğüm yükleri: kolon öz ağırlığı (G, üst düğüm), ek düğüm yükleri, dağıtımsız panel payları, eylemler, temel öz ağırlığı
    const tekil = {};     // "durum|dugum" → [FX, FY, FZ, MX, MY, MZ]
    const tekilEkle = function (durum, dno, v) {
      if (!baglanti[dno] || !self.durumRef[durum]) return;
      const a = durum + "|" + dno, r = tekil[a] = tekil[a] || [0, 0, 0, 0, 0, 0];
      for (let i = 0; i < 6; i++) r[i] += v[i];
    };
    const uyeTekil = [];  // çubuk üzerindeki tekil yükler (surum 3 ek yükleri, kren tekerlekleri): {eno, durum, x, P, F}
    const genel = dizi(Y.cubuklar).length > 0;
    if (genel) this.genelYukler(Y, ekle, tekilEkle, uyeTekil);
    // düğüm no (veri.ag / bina REF numarası) → baglanti anahtarı (aynı konumdaki düğümler tek bağlantı; efendi düğüm kendi bağlantısı)
    const dugumAnahtar = function (dno) {
      const d = self.dug.no[dno];
      if (d && baglanti[d.no]) return d.no;
      return baglanti[dno] ? dno : null;
    };
    // --- rüzgâr / deprem / kren düğüm eylemleri (C16; aks–kat ve genel) ---
    const eyl = Y.eylemler && typeof Y.eylemler === "object" && !Array.isArray(Y.eylemler) ? Y.eylemler : null;
    let eylemDugumEksik = 0;
    if (eyl) {
      Object.keys(eyl).forEach(function (dr) {
        if (!self.durumRef[dr]) return;
        dizi(sozluk(eyl[dr]).dugumler).forEach(function (n) {
          const F = [0, 1, 2, 3, 4, 5].map(function (i) { return sayi(dizi(n && n.F)[i], 0); });
          if (F.every(function (x) { return !x; })) return;
          const k = n ? dugumAnahtar(+n.dugum) : null;
          if (k === null) { eylemDugumEksik += 1; return; }
          tekilEkle(dr, k, F);
        });
      });
    }
    this.temelOzYukleri(ekle, tekilEkle, dugumAnahtar);
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
    // --- EZ = G_carpani × G (TBDY Denk. 4.10): bütün G eylemleri (temel öz ağırlığı dahil) ölçeklenip EZ yük durumuna ---
    const ezC = eyl && self.durumRef.EZ ? sayi(sozluk(eyl.EZ).G_carpani, null) : null;
    if (ezC) {
      const ezKaynak = "düşey deprem (EZ = " + sy(ezC) + " × G)";
      Object.keys(yayili).forEach(function (eno) {
        const r = yayili[eno];
        dizi(r.G).forEach(function (k) {
          (r.EZ = r.EZ || []).push({ sekil: k.sekil.map(function (x) { return [x[0], x[1], x[2] * ezC, x[3] * ezC]; }), vek: k.vek, kaynak: ezKaynak });
        });
      });
      Object.keys(tekil).filter(function (a) { return a.indexOf("G|") === 0; }).forEach(function (a) {
        tekilEkle("EZ", +a.slice(2), tekil[a].map(function (x) { return x * ezC; }));
      });
      uyeTekil.filter(function (t) { return t.durum === "G"; }).forEach(function (t) {
        uyeTekil.push({ eno: t.eno, durum: "EZ", x: t.x, P: t.P, F: volc(t.F, ezC), kaynak: ezKaynak });
      });
    }
    // eylemi yazılamayan rüzgâr / deprem / kren durumları: yük durumu/birleşim olarak kalırlar
    const yanal = Object.keys(this.durumRef).filter(function (d) { return /^(W|EX|EY|EZ|EH|K)/.test(d); });
    if (yanal.length) {
      if (Y.eylemler_not || !eyl) {
        this.uyarilar.push("IFC yükleri: rüzgâr, deprem ve kren etkileri yük durumu/birleşim olarak vardır, eylem olarak yazılmadı (" +
          (Y.eylemler_not ? String(Y.eylemler_not).replace(/\.$/, "") : "çözümde eylem kayıtları yok; binayı yeniden çözün") + ").");
      } else {
        const yok = yanal.filter(function (d) { return !eyl[d]; });
        if (yok.length) {
          this.uyarilar.push("IFC yükleri: " + yok.join(", ") + " durum" + (yok.length > 1 ? "larının" : "unun") + " eylemi çözümde yok; " +
            "yalnız yük durumu/birleşim olarak yazıldı.");
        }
      }
    }
    if (eylemDugumEksik) {
      this.uyarilar.push("IFC yükleri: " + eylemDugumEksik + " düğüm eyleminin (rüzgâr/deprem/kren) analiz modelinde karşılığı (düğüm) " +
        "bulunamadı; yazılmadı.");
    }
    const atananlar = { G: [], Q: [] };
    const fdeger = function (sekil, x) {
      for (let i = 0; i < sekil.length; i++) {
        const s = sekil[i];
        if (x >= s[0] - 1e-9 && x <= s[1] + 1e-9) return s[1] - s[0] > 1e-12 ? s[2] + (s[3] - s[2]) * (x - s[0]) / (s[1] - s[0]) : s[2];
      }
      return 0;
    };
    const kirikNoktalar = function (sekiller) {
      const xs = [];
      sekiller.forEach(function (sk) { sk.forEach(function (s) { xs.push(s[0], s[1]); }); });
      return xs.map(function (x) { return Math.round(x * 1e6) / 1e6; }).sort(function (a, b) { return a - b; })
        .filter(function (x, i, a) { return i === 0 || x - a[i - 1] > 1e-6; });
    };
    // surum 3: sıçramalı toplam (kenar ya da ek yük parçası çubuğun ortasında başlayıp bitebilir) — sıçramada iki nokta (x ∓ ε, ε ≤ 0,5 mm);
    // üye uçları (0, L) her zaman kırık nokta: kısmi yük düzgün (CONST) eylem sanılmasın
    const sicramali = function (sekiller, L) {
      const kirik = kirikNoktalar(sekiller.concat([[[0, L, 0, 0]]])), tol = 2e-6;
      const sinir = function (x, taraf) {
        let t = 0;
        sekiller.forEach(function (sk) {
          for (let i = 0; i < sk.length; i++) {
            const s = sk[i];
            if (s[1] - s[0] <= 1e-9) continue;
            const ic = taraf < 0 ? (x > s[0] + tol && x <= s[1] + tol) : (x >= s[0] - tol && x < s[1] - tol);
            if (ic) { t += s[2] + (s[3] - s[2]) * (Math.min(Math.max(x, s[0]), s[1]) - s[0]) / (s[1] - s[0]); break; }
          }
        });
        return t;
      };
      const P = [];
      kirik.forEach(function (x, i) {
        const sol = i > 0 ? sinir(x, -1) : null, sag = i < kirik.length - 1 ? sinir(x, 1) : null;
        if (sol === null) P.push([x, sag]);
        else if (sag === null || Math.abs(sol - sag) <= 1e-9 * Math.max(1, Math.abs(sol), Math.abs(sag))) P.push([x, sol]);
        else {
          // x ∓ ε'daki gerçek değerler: ε boyunca rampa, basamağın alanını (ve toplam yükü) korur
          const e = Math.min(5e-4, (x - kirik[i - 1]) / 4, (kirik[i + 1] - x) / 4);
          P.push([x - e, sinir(x - e, -1)], [x + e, sinir(x + e, 1)]);
        }
      });
      return P;
    };
    const KAYNAK_SIRA = ["öz ağırlık", "duvar", "panel payı", "panel payı (düzgün eşdeğer)", "ek yük", "temel öz ağırlığı", "rüzgâr",
      "deprem", "kren"];
    const yonAdi = function (v) {
      const eks = ["X", "Y", "Z"];
      for (let i = 0; i < 3; i++) if (Math.abs(Math.abs(v[i]) - 1) < 1e-9) return (v[i] > 0 ? "+" : "−") + eks[i];
      return "doğrultu (" + v.map(sy).join("; ") + ")";
    };
    Object.keys(yayili).map(Number).sort(function (a, b) { return a - b; }).forEach(function (eno) {
      const r = yayili[eno];
      ["G", "Q", "S"].filter(function (d) { return r[d]; }).concat(Object.keys(r).filter(function (d) { return ["G", "Q", "S"].indexOf(d) < 0; }).sort())
        .forEach(function (durum) {
          const kayitlar = r[durum];
          if (!kayitlar.length || !self.durumRef[durum]) return;
          const gruplar = [], gAnahtar = {};     // doğrultu grupları (ilk görülme sırasıyla)
          kayitlar.forEach(function (k) {
            const a = k.vek.map(R).join(",");
            if (!gAnahtar[a]) { gAnahtar[a] = { anahtar: a, vek: k.vek, sekiller: [], kaynaklar: [] }; gruplar.push(gAnahtar[a]); }
            gAnahtar[a].sekiller.push(k.sekil);
            if (k.kaynak && gAnahtar[a].kaynaklar.indexOf(k.kaynak) < 0) gAnahtar[a].kaynaklar.push(k.kaynak);
          });
          gruplar.forEach(function (g) {
            const asagi = g.anahtar === ASAGI_ANAHTAR;
            let noktalar;
            if (genel) {
              const e = self.yapisalUye[eno].e;
              noktalar = sicramali(g.sekiller, vboy(vfark([e.j.X, e.j.Y, e.j.Z], [e.i.X, e.i.Y, e.i.Z])));
              if (noktalar.every(function (p) { return Math.abs(p[1]) < 1e-12; })) return;
            } else {
              const kirik = kirikNoktalar(g.sekiller);
              noktalar = kirik.map(function (x) { return [x, g.sekiller.reduce(function (t, sk) { return t + fdeger(sk, x); }, 0)]; });
            }
            const uye = self.yapisalUye[eno].ref;
            const ad = durum + " / E" + eno + (asagi ? "" : " (" + yonAdi(g.vek) + ")");
            const kimlik = durum + ":" + eno + (asagi ? "" : ":" + g.anahtar);
            const kuvvet = function (ad_, v) {
              const c = g.vek.map(function (x) { return Math.abs(x) < 1e-12 ? null : v * x; });
              return w.ekle("IFCSTRUCTURALLOADLINEARFORCE", [ad_, c[0], c[1], c[2], null, null, null]);
            };
            const sira = KAYNAK_SIRA.filter(function (k) { return g.kaynaklar.indexOf(k) >= 0; })
              .concat(g.kaynaklar.filter(function (k) { return KAYNAK_SIRA.indexOf(k) < 0; }));
            const kaynak = sira.length ? ": " + sira.join(" + ") : "";
            let eylem;
            if (noktalar.every(function (p) { return Math.abs(p[1] - noktalar[0][1]) < 1e-9; })) {
              const yk = kuvvet(ad, noktalar[0][1]);
              eylem = w.ekle("IFCSTRUCTURALLINEARACTION", [self.gid("ye:" + kimlik), null, ad, "Düzgün yayılı yük (kN/m)" + kaynak, null, self.yYapisal, null,
                yk, E("GLOBAL_COORDS"), null, E("TRUE_LENGTH"), E("CONST")]);
            } else {
              const yukler = noktalar.map(function (p) { return kuvvet(ad + " @" + R(p[0]), p[1]); });
              const yap = w.ekle("IFCSTRUCTURALLOADCONFIGURATION", [ad, yukler, noktalar.map(function (p) { return [p[0]]; })]);
              eylem = w.ekle("IFCSTRUCTURALCURVEACTION", [self.gid("ye:" + kimlik), null, ad,
                genel ? "Parçalı doğrusal yayılı yük (kN/m)" + kaynak : "Parçalı doğrusal yayılı yük (TS 500 45° dağıtımı dahil, kN/m)",
                null, self.yYapisal, null, yap, E("GLOBAL_COORDS"), null, E("TRUE_LENGTH"), E("POLYGONAL")]);
            }
            w.ekle("IFCRELCONNECTSSTRUCTURALACTIVITY", [self.gid("rel:ye:" + kimlik), null, null, null, uye, eylem]);
            (atananlar[durum] = atananlar[durum] || []).push(eylem);
          });
        });
    });
    Object.keys(tekil).sort().forEach(function (a) {
      const p = a.split("|"), durum = p[0], dno = +p[1], v = tekil[a];
      const ad = durum + " / N" + dno;
      const yk = w.ekle("IFCSTRUCTURALLOADSINGLEFORCE", [ad, v[0], v[1], v[2], v[3], v[4], v[5]]);
      const eylem = w.ekle("IFCSTRUCTURALPOINTACTION", [self.gid("yt:" + a), null, ad,
        self.diyaframNo && self.diyaframNo[dno] ? "Diyafram merkezinde kat kuvveti ve burulma momenti (kN, kN·m)" : "Tekil düğüm yükü (kN, kN·m)",
        null, self.yYapisal, null, yk,
        E("GLOBAL_COORDS"), null]);
      w.ekle("IFCRELCONNECTSSTRUCTURALACTIVITY", [self.gid("rel:yt:" + a), null, null, null, baglanti[dno], eylem]);
      (atananlar[durum] = atananlar[durum] || []).push(eylem);
    });
    // çubuk üzerindeki tekil yükler: üyeye bağlı IfcStructuralPointAction, konumu IfcVertexPoint (Reference/Vertex) ile
    uyeTekil.forEach(function (t, i) {
      if (!self.durumRef[t.durum] || !self.yapisalUye[t.eno]) return;
      const ad = t.durum + " / E" + t.eno + " @" + R(t.x), kimlik = t.durum + ":" + t.eno + ":" + (i + 1);
      const vp = w.ekle("IFCVERTEXPOINT", [self.nokta(t.P)]);
      const rep = w.ekle("IFCTOPOLOGYREPRESENTATION", [self.ctxRef, "Reference", "Vertex", [vp]]);
      const sek = w.ekle("IFCPRODUCTDEFINITIONSHAPE", [null, null, [rep]]);
      const yk = w.ekle("IFCSTRUCTURALLOADSINGLEFORCE", [ad, t.F[0], t.F[1], t.F[2], 0, 0, 0]);
      const eylem = w.ekle("IFCSTRUCTURALPOINTACTION", [self.gid("ytc:" + kimlik), null, ad, "Çubuk üzerinde tekil yük (kN" +
        (t.kaynak ? "; " + t.kaynak : "") + "); üyenin i ucundan " + sy(t.x) + " m",
        null, self.yYapisal, sek, yk, E("GLOBAL_COORDS"), null]);
      w.ekle("IFCRELCONNECTSSTRUCTURALACTIVITY", [self.gid("rel:ytc:" + kimlik), null, null, null, self.yapisalUye[t.eno].ref, eylem]);
      (atananlar[t.durum] = atananlar[t.durum] || []).push(eylem);
    });
    Object.keys(atananlar).forEach(function (durum) {
      if (!atananlar[durum].length || !self.durumRef[durum]) return;
      w.ekle("IFCRELASSIGNSTOGROUP", [self.gid("rel:durum-yukler:" + durum), null, null, null, atananlar[durum], null, self.durumRef[durum]]);
    });
  };

  // Temel öz ağırlığı (C11; mütemadi / radye, iki model): veri.temel.oz_yuk = {elemanlar: [{no: FE no, q (kN/m, aşağı +)}],
  // dugumler: [{dugum, P (kN, aşağı +; kesişim düzeltmesi eksi olabilir)}], W} → G durumunda temel analiz üyelerine düzgün yayılı
  // (IfcStructuralLinearAction) ve temel düğümlerine tekil (IfcStructuralPointAction); Σq·L + ΣP = W. oz_yuk yoksa (eski çözüm):
  // temel üyelerine γ·A (veri.temel kesiti: ters T / dikdörtgen; radyede iki doğrultunun şeritleri plağı ikişer kez kapladığından
  // plak payı yarım), uyarıyla.
  Uretici.prototype.temelOzYukleri = function (ekle, tekilEkle, dugumAnahtar) {
    const vt = this.veriTemel(), self = this;
    if (!vt || !this.durumRef.G) return;
    const boy = function (e) { return vboy(vfark([e.j.X, e.j.Y, e.j.Z], [e.i.X, e.i.Y, e.i.Z])); };
    const oz = vt.oz_yuk && typeof vt.oz_yuk === "object" && (Array.isArray(vt.oz_yuk.elemanlar) || Array.isArray(vt.oz_yuk.dugumler)) ? vt.oz_yuk : null;
    if (oz) {
      let eksik = 0;
      dizi(oz.elemanlar).forEach(function (x) {
        const q = sayi(x && x.q, 0), u = x ? self.yapisalUye[x.no] : null;
        if (!q) return;
        if (!u) { eksik += 1; return; }
        const L = boy(u.e);
        ekle(+x.no, "G", [[0, L, q, q]], ASAGI, "temel öz ağırlığı");
      });
      dizi(oz.dugumler).forEach(function (x) {
        const P = sayi(x && x.P, 0);
        if (!P) return;
        const k = dugumAnahtar(+x.dugum);
        if (k === null) { eksik += 1; return; }
        tekilEkle("G", k, [0, 0, -P, 0, 0, 0]);
      });
      if (eksik) {
        this.uyarilar.push("IFC yükleri: temel öz ağırlığının " + eksik + " kaydının (veri.temel.oz_yuk) analiz modelinde karşılığı (temel " +
          "elemanı/düğümü) bulunamadı; yazılmadı.");
      }
      return;
    }
    const malz = betonMalzeme(this.Bm), gam = sayi(sozluk(this.Bm.malzemeler[malz.anahtar]).gamma, 25);
    const radye = String(vt.tip) === "radye", md = sozluk(vt.model);
    let n = 0;
    Object.keys(this.yapisalUye).map(Number).sort(function (a, b) { return a - b; }).forEach(function (no) {
      const e = self.yapisalUye[no].e, k = e.kesitObj;
      if ((e.tur !== "temel-kirisi" && e.tur !== "radye-serit") || !k) return;
      let A, plak = 0;
      if (k.tur === "tersT") { A = k.B * k.ht + k.bg * (k.hg - k.ht); plak = k.B * k.ht; } else { A = k.b * k.h; plak = k.b * k.h; }
      if (radye) {
        if (e.tur === "radye-serit") A -= plak / 2;
        else if (k.tur === "tersT") A -= plak / 2;
        else A -= Math.min(sayi(md.ag, 0) * sayi(md.h, 0), plak) / 2;      // RK b × h: plak payı ≈ ağ aralığı × plak kalınlığı
      }
      const q = gam * A;
      if (!(q > 0)) return;
      ekle(no, "G", [[0, boy(e), q, q]], ASAGI, "temel öz ağırlığı");
      n += 1;
    });
    if (n) {
      this.uyarilar.push("IFC yükleri: çözümde temel öz ağırlığı yükleri yok (veri.temel.oz_yuk; eski çözüm): " + n + " temel " +
        (radye ? "şeridi/kirişi" : "kirişi") + " analiz üyesine γ·A = " + sy(gam) + " kN/m³ × kesit alanı yazıldı" +
        (radye ? "; radye plağının öz ağırlığı yaklaşıktır (iki doğrultunun şeritlerine yarı yarıya)" : "; kesişimlerde ortak tabla hacmi iki kez sayılır") +
        ". Binayı yeniden çözün.");
    }
  };

  // surum 3 (genel model) yükleri → analiz üyelerine (FE parçaları), G, Q, S:
  // - öz ağırlık ve duvar: veri.yukler.cubuklar[].<durum>.oz / duvar toplamından düzgün yayılı (vute çubuğu birden çok FE parçasıysa
  //   parçalara, motorun parça kesitleri gibi A(h_orta)·boy ile orantılı);
  // - panel payı: veri.yukler.paneller[].kenarlar[].parcalar_birim (birim yüzey yükünün kenar boyunca dağılımı) × panel yoğunluğu
  //   (<durum>_toplam / alan; Q ve S eğik panelde cos α içerir). Kenar → çubuk eşlemesi veri.ag.paneller kenar düğümlerinden, motordaki
  //   kenar zinciri kuralıyla (u kenar başından; çubuğun i ucu kenarın sonuna yakınsa ters). Eşlenemeyen kalan (eski çözüm, eksik geometri)
  //   çubuğun panel toplamından düzgün eşdeğer olarak; dağıtımı "yok" olan panelin yükü köşe düğümlerine eşit tekil pay;
  // - ek yükler (bina.ek_yukler): tur "cubuk" yayılı (q, q1–q2, x1–x2; global X/Y/Z ya da yerel x′/y′/z′; oransal; izdusum) ya da
  //   tekil (x, P); tur "dugum" ortak düğüm yükü yolundan; tur "panel" panelin g/q/s yoğunluğuna katılmış olduğundan ayrıca yazılmaz;
  // - rüzgâr / deprem / kren çubuk eylemleri (veri.yukler.eylemler[durum].cubuklar; C16): yayılı q·vek ve tekil P·vek, aynı kurallarla.
  Uretici.prototype.genelYukler = function (Y, ekle, tekilEkle, uyeTekil) {
    const Bm = this.Bm, self = this, ag = Bm.ag || {}, dug = this.dug;
    const konum = function (d) { return [d.X, d.Y, d.Z]; };
    const durumVar = function (d) { return !!self.durumRef[d]; };
    const agCubuk = {}, binaCubuk = {}, parca = {};
    dizi(ag.cubuklar).forEach(function (c) { if (c && c.no !== undefined) agCubuk[+c.no] = c; });
    dizi(Bm.bina.cubuklar).forEach(function (c, i) { if (c) binaCubuk[c.no === undefined ? i + 1 : +c.no] = c; });
    Object.keys(this.yapisalUye).forEach(function (no) {
      const e = self.yapisalUye[no].e;
      if (e.cubuk !== undefined && e.cubuk !== null) (parca[e.cubuk] = parca[e.cubuk] || []).push({ eno: +no, e: e });
    });
    // çubuk: i ve j uçları, birim doğrultu x, yerel eksenler, analiz üyeleri (çubuk boyunca x0–x1; ters: üyenin i ucu çubuğun j tarafında)
    const onbellek = {};
    const bilgi = function (cno) {
      if (onbellek[cno] !== undefined) return onbellek[cno];
      const uy = parca[cno];
      if (!uy || !uy.length) return (onbellek[cno] = null);
      const ac = agCubuk[cno], bc = binaCubuk[cno];
      let Pi = null, Pj = null;
      if (ac && dug.no[ac.i] && dug.no[ac.j]) { Pi = konum(dug.no[ac.i]); Pj = konum(dug.no[ac.j]); }
      else if (bc) { const a = dug.ref(bc.i), b = dug.ref(bc.j); if (a && b) { Pi = konum(a); Pj = konum(b); } }
      if (!Pi) {
        const s = uy.slice().sort(function (a, b) { return (a.e.parca || 0) - (b.e.parca || 0); });
        Pi = konum(s[0].e.i); Pj = konum(s[s.length - 1].e.j);
      }
      const L = vboy(vfark(Pj, Pi));
      if (!(L > 1e-9)) return (onbellek[cno] = null);
      const x = vbirim(vfark(Pj, Pi));
      const parcalar = uy.map(function (u) {
        const a = vic(vfark(konum(u.e.i), Pi), x), b = vic(vfark(konum(u.e.j), Pi), x);
        return { eno: u.eno, e: u.e, x0: Math.min(a, b), x1: Math.max(a, b), ters: a > b };
      }).sort(function (a, b) { return a.x0 - b.x0; });
      const e0 = parcalar[0].e;
      let lam = e0.lam && !parcalar[0].ters ? e0.lam : null;
      if (!lam) { const y = e0.d || derinlikYonu(x, 0); lam = [x, y, vdis(x, y)]; }
      return (onbellek[cno] = { Pi: Pi, L: L, x: x, parcalar: parcalar, lam: lam, kesit: (ac && ac.kesit) || (bc && bc.kesit) || e0.kesit });
    };
    const eksik = {};
    // çubuk boyunca yük parçaları [[x1, x2, q1, q2]] (çubuğun i ucundan) → üyelerin kendi i uçlarından şekilleri; dönüş: toplam (kN)
    const cubugaYayili = function (cno, durum, parcalar, vek, kaynak) {
      const b = bilgi(cno);
      if (!b) { eksik[cno] = true; return 0; }
      let top = 0;
      b.parcalar.forEach(function (p) {
        const sk = [];
        parcalar.forEach(function (s) {
          const lo = Math.max(s[0], p.x0), hi = Math.min(s[1], p.x1);
          if (hi - lo <= 1e-9) return;
          const f = function (x) { return s[1] - s[0] > 1e-12 ? s[2] + (s[3] - s[2]) * (x - s[0]) / (s[1] - s[0]) : s[2]; };
          const ql = f(lo), qh = f(hi);
          if (Math.abs(ql) < 1e-12 && Math.abs(qh) < 1e-12) return;
          sk.push(p.ters ? [p.x1 - hi, p.x1 - lo, qh, ql] : [lo - p.x0, hi - p.x0, ql, qh]);
          top += (ql + qh) / 2 * (hi - lo);
        });
        if (sk.length) ekle(p.eno, durum, sk, vek, kaynak);
      });
      return top;
    };
    // öz ağırlık parçaları: vute çubuğu birden çok FE parçasıysa A(h_orta)·boy ile orantılı (motor: başlıklar aynı, gövde uzar)
    const ozParcalari = function (b, oz) {
      const duz = [[0, b.L, oz / b.L, oz / b.L]];
      const k = b.parcalar.length > 1 && b.kesit !== undefined ? self.kesit(b.kesit, false) : null;
      if (!k || !k.vute) return duz;
      const v = k.vute, L = b.L, boy = v.boy && v.boy < L ? v.boy : L, h0 = k.h || 0;
      const alan = function (h) {
        if (k.tur === "I") return 2 * k.b * k.tf + (h - 2 * k.tf) * k.tw + (4 - Math.PI) * Math.pow(k.r || 0, 2);
        return k.tur === "dikdortgen" ? k.b * h : h;
      };
      const a = b.parcalar.map(function (p) {
        const xm = (p.x0 + p.x1) / 2, s_ = v.derin_uc === "j" ? L - xm : xm;
        return alan(h0 + v.ek_yukseklik * Math.max(0, 1 - s_ / boy)) * (p.x1 - p.x0);
      });
      const top = a.reduce(function (t, x) { return t + x; }, 0);
      if (!(top > 0)) return duz;
      return b.parcalar.map(function (p, i) { const q = oz * a[i] / top / (p.x1 - p.x0); return [p.x0, p.x1, q, q]; });
    };
    // --- paneller ---
    const agPanel = {}, binaPanel = {};
    dizi(ag.paneller).forEach(function (p) { if (p && p.no !== undefined) agPanel[+p.no] = p; });
    dizi(Bm.bina.paneller).forEach(function (p, i) { if (p) binaPanel[p.no === undefined ? i + 1 : +p.no] = p; });
    const atanan = {};        // "çubuk|durum" → kenar dağılımından yazılan panel payı (kN)
    dizi(Y.paneller).forEach(function (p) {
      const A = sayi(p.alan, 0);
      if (!(A > 0)) return;
      const yog = {};
      ["G", "Q", "S"].forEach(function (d) { const v = sayi(p[d + "_toplam"], 0) / A; if (Math.abs(v) > 1e-12 && durumVar(d)) yog[d] = v; });
      const durumlar = Object.keys(yog);
      if (!durumlar.length) return;
      const ap = agPanel[+p.no];
      if (String(p.dagitim) === "yok") {
        // köşe düğümleri: çözüm ağından (veri.ag.paneller); eski çözümde binanın köşe REF'lerinden
        const kose = ap ? dizi(ap.kose).map(function (n) { return dug.no[n]; })
          : dizi(sozluk(binaPanel[+p.no]).kose).map(function (r) { return dug.ref(r); });
        kose.forEach(function (d) {
          if (d) durumlar.forEach(function (dr) { tekilEkle(dr, d.no, [0, 0, -yog[dr] * A / kose.length, 0, 0, 0]); });
        });
        return;
      }
      dizi(p.kenarlar).forEach(function (k) {
        const pb = dizi(k.parcalar_birim).filter(function (s) { return dizi(s).length === 4 && +s[1] - +s[0] > 1e-9; });
        if (!pb.length || !ap) return;
        const ak = dizi(ap.kenarlar).filter(function (x) { return x && +x.kenar === +k.kenar; })[0];
        const kd = ak ? dizi(ak.dugumler) : [];
        const da = dug.no[kd[0]], db = dug.no[kd[1]];
        if (!da || !db) return;
        const Pa = konum(da), Le = vboy(vfark(konum(db), Pa));
        if (!(Le > 1e-9)) return;
        const eh = vbirim(vfark(konum(db), Pa));
        const zincir = dizi(ak.cubuklar).concat(dizi(k.cubuklar)).filter(function (c, i, l) { return l.indexOf(c) === i; });
        zincir.forEach(function (cno) {
          const b = bilgi(+cno);
          if (!b) return;
          const Pj = vtop(b.Pi, volc(b.x, b.L));
          const ui = vic(vfark(b.Pi, Pa), eh), uj = vic(vfark(Pj, Pa), eh);
          const sapma = Math.max(vboy(vfark(b.Pi, vtop(Pa, volc(eh, ui)))), vboy(vfark(Pj, vtop(Pa, volc(eh, uj)))));
          if (sapma > 1e-3) return;                                  // kenar doğrultusunda değil
          const ua = Math.min(Math.max(Math.min(ui, uj), 0), Le), ub = Math.min(Math.max(Math.max(ui, uj), 0), Le), ters = ui > uj;
          const sk = [];
          pb.forEach(function (s) {
            const u0 = +s[0], u1 = +s[1], f0 = +s[2], f1 = +s[3];
            const lo = Math.max(u0, ua), hi = Math.min(u1, ub);
            if (hi - lo <= 1e-9) return;
            const fl = f0 + (f1 - f0) * (lo - u0) / (u1 - u0), fh = f0 + (f1 - f0) * (hi - u0) / (u1 - u0);
            let x1, x2, q1, q2;
            if (!ters) { x1 = lo - ua; x2 = hi - ua; q1 = fl; q2 = fh; } else { x1 = ub - hi; x2 = ub - lo; q1 = fh; q2 = fl; }
            x1 = Math.max(0, Math.min(x1, b.L)); x2 = Math.max(0, Math.min(x2, b.L));
            if (x2 - x1 > 1e-9 && (q1 || q2)) sk.push([x1, x2, q1, q2]);
          });
          if (!sk.length) return;
          durumlar.forEach(function (dr) {
            const top = cubugaYayili(+cno, dr, sk.map(function (s) { return [s[0], s[1], s[2] * yog[dr], s[3] * yog[dr]]; }), ASAGI, "panel payı");
            atanan[+cno + "|" + dr] = (atanan[+cno + "|" + dr] || 0) + top;
          });
        });
      });
    });
    // --- çubuk toplamları: öz ağırlık, duvar, kenar dağılımıyla eşlenemeyen panel payı ---
    let fazlaPanel = 0, duzgunPanel = 0;
    const ekCozum = {};       // "çubuk|durum" → çözümdeki ek yük düşey toplamı (kN, aşağı +)
    dizi(Y.cubuklar).forEach(function (r) {
      const cno = +r.no;
      ["G", "Q", "S"].forEach(function (dr) {
        const x = sozluk(r[dr]);
        if (!durumVar(dr) || !Object.keys(x).length) return;
        if (sayi(x.ek, 0)) ekCozum[cno + "|" + dr] = +x.ek;
        const b = bilgi(cno);
        if (!b) { if (sayi(x.toplam_kN, 0)) eksik[cno] = true; return; }
        const oz = sayi(x.oz, 0), duvar = sayi(x.duvar, 0), panel = sayi(x.panel, 0);
        if (oz) cubugaYayili(cno, dr, ozParcalari(b, oz), ASAGI, "öz ağırlık");
        if (duvar) cubugaYayili(cno, dr, [[0, b.L, duvar / b.L, duvar / b.L]], ASAGI, "duvar");
        const kalan = panel - (atanan[cno + "|" + dr] || 0), tol = 1e-6 + 1e-4 * Math.abs(panel);
        if (kalan > tol) { cubugaYayili(cno, dr, [[0, b.L, kalan / b.L, kalan / b.L]], ASAGI, "panel payı (düzgün eşdeğer)"); duzgunPanel += 1; }
        else if (kalan < -tol) fazlaPanel += 1;
      });
    });
    // --- ek çubuk yükleri (motor _ek_yukleri_oku ile aynı okuma) ---
    const ekYazilan = {};
    const sayiVar = function (v) { return v !== undefined && v !== null && v !== ""; };
    dizi(Bm.bina.ek_yukler).forEach(function (y, n) {
      if (!y || typeof y !== "object" || String(y.tur || "").trim().toLowerCase() !== "cubuk") return;
      const dr = String(y.durum || "G").trim().toUpperCase(), cno = Math.round(sayi(y.cubuk, NaN));
      if (!durumVar(dr) || !isFinite(cno)) return;
      const b = bilgi(cno);
      if (!b) { eksik[cno] = true; return; }
      const yon = String(y.yon || "Z").trim();
      const yerel = ["x", "y", "z"].indexOf(yon) >= 0 || /[′']$/.test(yon);
      const ey = yerel ? yon.replace(/[′']/g, "").toLowerCase() : yon.toUpperCase();
      const v0 = yerel ? (["x", "y", "z"].indexOf(ey) >= 0 ? b.lam["xyz".indexOf(ey)] : null) : ({ X: [1, 0, 0], Y: [0, 1, 0], Z: [0, 0, 1] }[ey] || null);
      if (!v0) { self.uyarilar.push((n + 1) + ". ek yük: yön '" + yon + "' anlaşılamadı; IFC'ye yazılmadı."); return; }
      // +Z yönlü yük −Z (aşağı) doğrultusunda ters işaretle: aynı üyedeki öz ağırlık / panel yüküyle tek eylemde toplanır
      const yukari = Math.abs(v0[0]) < 1e-12 && Math.abs(v0[1]) < 1e-12 && v0[2] > 0;
      const vek = yukari ? ASAGI : v0, isaret = yukari ? -1 : 1;
      const olc = y.oransal ? b.L : 1, a = cno + "|" + dr;
      if (sayiVar(y.x) && !sayiVar(y.x1) && !sayiVar(y.q1) && !sayiVar(y.q)) {
        const P = sayi(sayiVar(y.P) ? y.P : y.F, 0) * isaret, x = Math.min(Math.max(sayi(y.x, 0) * olc, 0), b.L);
        const p = b.parcalar.filter(function (q) { return x >= q.x0 - 1e-9 && x <= q.x1 + 1e-9; })[0];
        if (!p || !P) return;
        uyeTekil.push({ eno: p.eno, durum: dr, x: p.ters ? p.x1 - x : x - p.x0, P: vtop(b.Pi, volc(b.x, x)), F: volc(vek, P) });
        ekYazilan[a] = (ekYazilan[a] || 0) - P * vek[2];
        return;
      }
      const carpan = y.izdusum && !yerel ? Math.sqrt(Math.max(0, 1 - Math.pow(vic(b.x, v0), 2))) : 1;
      const q1h = sayiVar(y.q1) ? y.q1 : (sayiVar(y.q) ? y.q : 0), q2h = sayiVar(y.q2) ? y.q2 : q1h;
      const q1 = sayi(q1h, 0) * carpan * isaret, q2 = sayi(q2h, 0) * carpan * isaret;
      const x1 = Math.max(0, sayi(y.x1, 0) * olc), x2 = sayiVar(y.x2) ? Math.min(b.L, sayi(y.x2, 0) * olc) : b.L;
      if (!(x2 - x1 > 1e-9) || (!q1 && !q2)) return;
      cubugaYayili(cno, dr, [[x1, x2, q1, q2]], vek, "ek yük");
      ekYazilan[a] = (ekYazilan[a] || 0) - (q1 + q2) / 2 * (x2 - x1) * vek[2];
    });
    // --- rüzgâr / deprem / kren çubuk eylemleri (C16): veri.yukler.eylemler[durum].cubuklar = [{no, yayili: [{x1, x2, q1, q2, vek}],
    //     tekil: [{x, P, vek}]}]; x çubuğun i ucundan (m), q (kN/m) ve P (kN) bina eksenlerindeki birim vek doğrultusunda.
    //     Yayılı yükler FE parçalarına bölünür (öz ağırlık / panel payı gibi; +Z yönlüsü −Z'de ters işaretle), aynı noktadaki tekil
    //     yükler (kren tekerleğinin düşey, yanal ve fren kuvvetleri) tek nokta eyleminde toplanır ---
    const eyl = Y.eylemler && typeof Y.eylemler === "object" && !Array.isArray(Y.eylemler) ? Y.eylemler : {};
    const vekOku = function (v) {
      const x = dizi(v).map(Number);
      return x.length === 3 && x.every(isFinite) && vboy(x) > 1e-9 ? x : null;
    };
    const kaynakAdi = function (dr) { return dr[0] === "W" ? "rüzgâr" : (dr[0] === "K" ? "kren" : "deprem"); };
    const eylemTekil = {};
    let vekHatali = 0;
    Object.keys(eyl).forEach(function (dr) {
      if (!durumVar(dr)) return;
      dizi(sozluk(eyl[dr]).cubuklar).forEach(function (c) {
        const cno = Math.round(sayi(c && c.no, NaN));
        const yay = dizi(c && c.yayili), tek = dizi(c && c.tekil);
        if (!isFinite(cno) || (!yay.length && !tek.length)) return;
        const b = bilgi(cno);
        if (!b) { eksik[cno] = true; return; }
        const kes = function (x) { return Math.min(Math.max(x, 0), b.L); };
        yay.forEach(function (y) {
          const v0 = vekOku(y && y.vek);
          if (!v0) { vekHatali += 1; return; }
          const yukari = Math.abs(v0[0]) < 1e-12 && Math.abs(v0[1]) < 1e-12 && v0[2] > 0;
          const vek = yukari ? volc(v0, -1) : v0, isaret = yukari ? -1 : 1;
          const x1 = kes(sayi(y.x1, 0)), x2 = kes(sayi(y.x2, b.L));
          const q1 = sayi(y.q1, 0) * isaret, q2 = sayi(y.q2, sayi(y.q1, 0)) * isaret;
          if (!(x2 - x1 > 1e-9) || (!q1 && !q2)) return;
          cubugaYayili(cno, dr, [[x1, x2, q1, q2]], vek, kaynakAdi(dr));
        });
        tek.forEach(function (t) {
          const v = vekOku(t && t.vek), P = sayi(t && t.P, 0);
          if (!v) { vekHatali += 1; return; }
          if (!P) return;
          const x = kes(sayi(t.x, 0));
          const p = b.parcalar.filter(function (q) { return x >= q.x0 - 1e-9 && x <= q.x1 + 1e-9; })[0];
          if (!p) return;
          const xl = p.ters ? p.x1 - x : x - p.x0, a = dr + "|" + p.eno + "|" + Math.round(xl * 1e6);
          let r = eylemTekil[a];
          if (!r) {
            r = eylemTekil[a] = { eno: p.eno, durum: dr, x: xl, P: vtop(b.Pi, volc(b.x, x)), F: [0, 0, 0], kaynak: dr[0] === "K" ? "kren tekerleği" : kaynakAdi(dr) };
            uyeTekil.push(r);
          }
          r.F = vtop(r.F, volc(v, P));
        });
      });
    });
    if (vekHatali) self.uyarilar.push("IFC yükleri: " + vekHatali + " rüzgâr/deprem/kren çubuk eyleminin doğrultusu (vek) anlaşılamadı; yazılmadı.");
    let ekFarkli = 0;
    Object.keys(ekCozum).concat(Object.keys(ekYazilan)).filter(function (a, i, l) { return l.indexOf(a) === i; }).forEach(function (a) {
      const c = ekCozum[a] || 0, m = ekYazilan[a] || 0;
      if (Math.abs(c - m) > 1e-3 + 1e-3 * Math.abs(c)) ekFarkli += 1;
    });
    const eksikler = Object.keys(eksik).map(Number).sort(function (a, b) { return a - b; });
    if (eksikler.length) {
      self.uyarilar.push("IFC yükleri: " + eksikler.length + " çubuğun analiz modelinde karşılığı (FE parçası) bulunamadı; bu çubukların yükleri yazılmadı (Ç" +
        eksikler.slice(0, 8).join(", Ç") + (eksikler.length > 8 ? ", …" : "") + ").");
    }
    if (duzgunPanel) {
      self.uyarilar.push("IFC yükleri: " + duzgunPanel + " çubuk/durumda panel payının kenar dağılımı çözümde bulunamadı (eski çözüm ya da eksik kenar " +
        "geometrisi); çubuğun panel toplamı düzgün yayılı eşdeğer olarak yazıldı (toplam aynı, dağılım yaklaşık).");
    }
    if (fazlaPanel) self.uyarilar.push("IFC yükleri: " + fazlaPanel + " çubuk/durumda kenar dağılımından yazılan panel payı çözümdeki toplamdan büyük; çözümü yenileyin.");
    if (ekFarkli) self.uyarilar.push("IFC yükleri: " + ekFarkli + " çubuk/durumda yazılan ek çubuk yükünün düşey toplamı çözümdekinden farklı (bina.ek_yukler çözümden sonra değişmiş olabilir).");
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

  // Dosya zamanı: secenek.zaman ("YYYY-MM-DDTHH:MM:SS", UTC) verilirse o (aynı model + aynı zaman → aynı dosya), yoksa şimdi
  Uretici.prototype.zamanMetni = function () {
    if (!this._zaman) {
      const z = String(this.s.zaman || this.s.tarih || "");
      const t = z ? Date.parse(/[zZ]$|[+-]\d\d:?\d\d$/.test(z) || z.length <= 10 ? z : z + "Z") : NaN;
      this._zaman = isFinite(t) ? new Date(t).toISOString().slice(0, 19) : new Date().toISOString().slice(0, 19);
    }
    return this._zaman;
  };
  Uretici.prototype.zamanDamgasi = function () { return Math.floor(Date.parse(this.zamanMetni() + "Z") / 1000); };

  Uretici.prototype.metin = function () {
    const proje = sozluk(this.s.proje);
    const uk = this.uygulamaKimligi();
    const zaman = this.zamanMetni();
    const ad = this.s.dosya_adi || dosyaAdi(this.Bm.bina);
    const bas = [
      "ISO-10303-21;",
      "HEADER;",
      "FILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2, StructuralAnalysisView]'),'2;1');",
      "FILE_NAME(" + [S(ad), S(String(zaman).slice(0, 19)), "(" + S(proje.hazirlayan || "") + ")", "(" + S(proje.kurum || "") + ")",
        S(uk.onislemci), S(uk.tam_ad), S("")].join(",") + ");",
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
    U.dug = new DugumKumesi(U.Bm, U.uyarilar);
    U.basla();
    U.izgaralar();
    U.fiziksel();
    if (U.s.analiz !== false) U.yapisal();
    U.bitir();
    U.kesitUyarilariniKapat();
    return { metin: U.metin(), uyarilar: U.uyarilar, sayac: Object.assign({}, U.w.sayac), dosya_adi: U.s.dosya_adi || dosyaAdi(bina) };
  }
  function uret(bina, veri, secenek) { return uretAyrintili(bina, veri, secenek).metin; }

  // Tarayıcıda .ifc indirme kısa yolu (arayüzdeki "IFC" düğmesi için)
  function indir(bina, veri, secenek) {
    if (typeof document === "undefined" || typeof Blob === "undefined" || typeof URL === "undefined" || !URL.createObjectURL) {
      throw new Error("MatrisIFC.indir yalnız tarayıcıda çalışır; başka ortamda uret() kullanın.");
    }
    const r = uretAyrintili(bina, veri, secenek);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([r.metin], { type: "application/x-step" }));
    a.download = r.dosya_adi;
    a.style.display = "none";
    (document.body || document.documentElement).appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    return { dosya_adi: r.dosya_adi, bayt: r.metin.length, uyarilar: r.uyarilar };
  }

  return { uret: uret, uretAyrintili: uretAyrintili, dosyaAdi: dosyaAdi, indir: indir, globalId: globalId, stepMetin: stepMetin,
    basitProfil: basitProfil, PROFILLER: PROFILLER, SURUM: SURUM };
});
