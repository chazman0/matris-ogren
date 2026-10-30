/* op4 — yeni saf model işlemleri (MIMARI §9.6, §10.2–§10.4, §13.4; "F1 paket sözleşmeleri" §S26).
   Saf modül: DOM yok. QuickJS'te self.Op4Ops, node'da module.exports (UMD; docs/model_ops.js ile aynı kalıp).
   Sahibi: B (model-cekirdegi). Bu dosya SÖZLEŞMEDİR: imzalar ve dönüş biçimleri JSDoc'tadır; gövdeler F1 iş 1.3'te
   doldurulur. Taslak gövdeler doğru BİÇİMDE boş sonuç döndürür (bosModel dışında), böylece cephe ve C++ köprüsü önceden
   bağlanabilir. Taslak olanlar TASLAK listesinde adlandırılır; uygulanan işlev listeden çıkarılır.

   Eleman kimliği JS'te {tur, no, alt?} nesnesidir: tur kod adı ("cubuk", "panel", "dugum", "mesnet", "yuk", "aks",
   "aks_sistemi", "temel"), no tamsayı, alt varsayılan 0 (C++ ElemanKimligi; kaynak/cekirdek/kimlik.h). Sayısal kodlar
   KODLAR'dadır ve op4/veri/sahne_kodlari.json ile aynıdır (op4/testler/js/sozlesme.test.js denetler). */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.Op4Ops = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function () {
  "use strict";

  const SURUM = "0.1.0-sozlesme";

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

  /** Faz 1 öznitelik kimlikleri (op4/veri/oznitelikler.json; C++ oznitelik::*). */
  const OZNITELIK_IDLERI = Object.freeze(["tur", "no", "ad", "alt_tur", "kullanim_yeri", "kat", "seviye", "kesit", "profil",
    "malzeme", "sistem", "grup", "uzunluk", "egim", "aci", "kalinlik", "alan", "serbest_i", "serbest_j", "serbest_dugum",
    "x", "y", "z"]);

  /** Henüz gövdesi doldurulmamış işlevler (B, F1 iş 1.3). */
  const TASLAK = Object.freeze(["katUyeligi", "kullanimYeri", "profilAdiNormal", "oznitelikCikar", "sahneCikar", "sonucEsle"]);

  class Op4Hatasi extends Error {
    constructor(mesaj) { super(mesaj); this.name = "Op4Hatasi"; }
  }

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

  /**
   * Kat ve seviye üyeliği (MIMARI §10.2; tolerans 1 mm). Surum 1 modelde genellestir görünümüne göre.
   * @param {Object} model bina JSON
   * @returns {{seviyeler: Array<{ad: string, z: number, kat: number}>,
   *            dugum: Object<string, number[]>, cubuk: Object<string, number[]>, panel: Object<string, number[]>,
   *            seviye: {dugum: Object<string, string>, cubuk: Object<string, string>, panel: Object<string, string>}}}
   *   Anahtar eleman no'su (dize). Kat listesi boş = temel / kat dışı. Kat aralığını aşan kolon birden çok kat taşır.
   */
  function katUyeligi(model) {
    void model;
    return { seviyeler: [], dugum: {}, cubuk: {}, panel: {}, seviye: { dugum: {}, cubuk: {}, panel: {} } };
  }

  /**
   * Alt tür ve kullanım yeri (MIMARI §10.3; tolerans 1 cm).
   * @param {Object} model
   * @returns {{cubuk: Object<string, {alt_tur: string, yer: string}>, panel: Object<string, {alt_tur: string, yer: string}>,
   *            dugum: Object<string, {alt_tur: string, yer: string}>}}
   *   alt_tur: kolon | kiris | doseme | cati | cephe | capraz | makas-ust | makas-alt | makas-dikme | makas-diyagonal | asik
   *            | kren | bag | temel | mesnet | dugum | diger
   *   yer    : kolon kose|kenar|ic; kiriş dis|ic|konsol; döşeme ic|kenar|konsol; çapraz dis-cephe|ic; düğüm temel|kolon-ustu|ara;
   *            cephe +x|-x|+y|-y; sınıfsız ""
   */
  function kullanimYeri(model) {
    void model;
    return { cubuk: {}, panel: {}, dugum: {} };
  }

  /**
   * Kesit adı normalleştirme (MIMARI §10.4). Ortak sınama vektörleri: op4/testler/ortak/profil_adlari.json (JS, C++, Python).
   * @param {string} ad kullanıcının ya da IFC'nin yazdığı ad ("HE340A", "HE 340 A", "IPE300", "L100x10" …)
   * @returns {{ad: string|null, aile: string|null, durum: "tamam"|"kutuphanede_yok"|"anlasilmadi"}}
   *   ad: kütüphanedeki normal ad ("HEA 340"); aile: "HEA" | "HEB" | "IPE" | "UPN" | "L" | "KUTU" | "BORU" …
   */
  function profilAdiNormal(ad) {
    void ad;
    return { ad: null, aile: null, durum: "anlasilmadi" };
  }

  /**
   * Sütunlu öznitelik tablosu, Faz 1 alanları (OZNITELIK_IDLERI). C++ OznitelikTablosu'na birebir çevrilir.
   * @param {Object} model
   * @param {{kat?: Object, kullanim?: Object}} [ek] katUyeligi / kullanimYeri önceden hesaplandıysa
   * @returns {{satirlar: Array<{tur: string, no: number, alt?: number}>,
   *            sutunlar: Array<{id: string, tur: "sayi"|"metin"|"enum"|"bool"|"liste", birim?: string,
   *                             degerler: Array<number|string|boolean|number[]|null>}>}}
   *   Her sütunun degerler dizisi satirlar ile aynı uzunluktadır; değer yoksa null.
   */
  function oznitelikCikar(model, ek) {
    void model; void ek;
    return { satirlar: [], sutunlar: OZNITELIK_IDLERI.map(function (id) { return { id: id, tur: "metin", degerler: [] }; }) };
  }

  /**
   * Sahne (MIMARI §9.3 SAHNE içeriği; C++ SahneAnlik, kaynak/cekirdek/sahne.h). Tipli diziler QuickJS'ten C++'a sıfır
   * kopyayla geçer. Dizinler dugumler dizisine göredir (0 tabanlı).
   * @param {Object} model
   * @param {number} sahneSurumu
   * @returns {{
   *   sahne_surumu: number, model_surumu: number, baslik: string, sistem: string,
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
  function sahneCikar(model, sahneSurumu) {
    return {
      sahne_surumu: sahneSurumu || 0, model_surumu: (model && model.surum) || 3,
      baslik: (model && model.baslik) || "", sistem: (model && model.sistem) || "celik",
      seviyeler: [], akslar: [],
      dugumler: { no: new Uint32Array(0), xyz: new Float64Array(0), tur: new Uint8Array(0), bayrak: new Uint8Array(0) },
      cubuklar: { no: new Uint32Array(0), i: new Uint32Array(0), j: new Uint32Array(0), tur: new Uint8Array(0), bayrak: new Uint8Array(0),
        serbestlik: new Uint16Array(0), kesit: new Uint32Array(0), grup: new Uint32Array(0), uretec: new Uint32Array(0),
        aci: new Float64Array(0), y_yerel: new Float64Array(0) },
      paneller: { no: new Uint32Array(0), kose_bas: new Uint32Array(0), kose_sayisi: new Uint32Array(0), kose: new Uint32Array(0),
        tur: new Uint8Array(0), bayrak: new Uint8Array(0), kalinlik: new Float64Array(0) },
      mesnetler: { dugum: new Uint32Array(0), maske: new Uint8Array(0), tur: new Uint8Array(0) },
      temeller: [], kesitler: [], gruplar: [], malzemeler: [],
    };
  }

  /**
   * Çözüm sonucunun model elemanlarına eşlenmesi (MIMARI §4 çözüm akışı 3). C++ SonucEslemesi.
   * @param {Object} model çözülen model
   * @param {Object} veri bina_coz yanıtındaki "veri" nesnesi
   * @returns {{elemanlar: Array<{kimlik: {tur: string, no: number}, dc: number, belirleyen: string, kombinasyon: string,
   *                              tasarim_satiri: number}>, uyarilar: string[]}}  elemanlar kimliğe göre sıralı; dc < 0 tasarım yok
   */
  function sonucEsle(model, veri) {
    void model; void veri;
    return { elemanlar: [], uyarilar: [] };
  }

  return {
    SURUM: SURUM, KODLAR: KODLAR, OZNITELIK_IDLERI: OZNITELIK_IDLERI, TASLAK: TASLAK, Op4Hatasi: Op4Hatasi,
    bosModel: bosModel, katUyeligi: katUyeligi, kullanimYeri: kullanimYeri, profilAdiNormal: profilAdiNormal,
    oznitelikCikar: oznitelikCikar, sahneCikar: sahneCikar, sonucEsle: sonucEsle,
  };
});
