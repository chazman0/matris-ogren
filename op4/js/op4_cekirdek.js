/* op4 — model çekirdeği CEPHESİ (MIMARI §9.3; "F1 paket sözleşmeleri" §S27). QuickJS-ng içinde model otoritesidir;
   C++ ModelCekirdegi (op4/kaynak/cekirdek/model_cekirdegi.h) her yöntemi aynı adla çağırır ve sonucu C++ yapılarına çevirir.
   QuickJS'te self.Op4Cekirdek, node'da module.exports (UMD). Sahibi: B (model-cekirdegi). İmzalar, dönüş biçimleri ve hata
   kuralları JSDoc'tadır (sözleşme); TASLAK listesi boştur (F1 iş 1.3).

   Bağımlılıklar (QuickJS ön yüklemesi globalThis.self = globalThis ile UMD modüllerini self üstüne kurar; node'da require):
     ModelOps (docs/model_ops.js), MatrisAks (docs/aks_sistemi.js), MatrisBinaCizim (docs/bina_cizim.js),
     MatrisIFC (docs/ifc_disari.js), MatrisTablo (docs/tablo_editoru.js), Op4Ops (op4/js/op4_ops.js).

   Çağrı kuralı (C++ köprüsü): parametreler düz nesnedir (C++ JSON metnini JSON.parse ile verir); dönüşler düz nesne ve
   tipli dizilerdir. Eleman kimliği {tur, no, alt?} (op4_ops.js). Hata kuralı: geçersiz girdi (ModelOps.ModelHatasi,
   MatrisAks.AksHatasi, Op4Ops.Op4Hatasi) → {basarili: false, hata}; geometrik ret → {basarili: true, uyarilar: [...]} ve model
   değişmez; başka istisna → fırlatılır (C++ "İç hata" olarak yakalar ve günlüğe yazar).

   Model değişmezdir: hiçbir yöntem model nesnesini yerinde değiştirmez; her işlem yeni bir model nesnesi üretir (docs/
   işlemleri zaten saftır). Sahne ve öznitelik tabloları model nesnesine bağlı önbellektedir (aynı model → aynı anlık).

   Geri al (MIMARI §9.4): değişmez anlık yığını (önceki model nesnesi saklanır; kopya yok); sınır 100 adım ya da 512 MB
   (ayar; bayt modelin eleman sayısından kestirilir); dosyaya kaydedilmez; seçim ve görünüm kapsam dışıdır. Her başarılı ve
   modeli değiştiren uygula() tek adımdır. */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika(kok);
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.Op4Cekirdek = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function (kok) {
  "use strict";

  const SURUM = "0.1.0";

  /**
   * uygula() beyaz listesi, Faz 1 (C++ islem:: sabitleri). Faz 3–4'te ModelOps / MatrisAks / MatrisBinaCizim / Op4Ops
   * işlemleri eklenir (MIMARI §12.4). Listede olmayan ad → {basarili: false, hata: "Bilinmeyen işlem: …"}.
   *   hizliAks       {x: number[] (aralıklar m) | sözdizimi ("3@6") | {adet, aralik}, y: …, z: number[] (kat yükseklikleri m)
   *                   | sözdizimi, taban?: number (temel kotu), ekZ?: [{ad, konum}], ilkX?: "A", ilkY?: "1", balon?}
   *                  → MatrisAks.hizliAks + MatrisBinaCizim.aksSihirbazUygula (mevcut akslar değişir; elemanlar yapışık taşınır)
   *   aksSihirbazi   MatrisBinaCizim.aksSihirbazUygula(bina, akslar, katlar) parametreleri {akslar, katlar?}
   *   baslikDegistir {baslik: string}
   *   genellestir    {onay?: true} → aks–kat modelini genel modele çevirir (C1: onaysız çağrı gecis_onayi döndürür)
   */
  const ISLEMLER = Object.freeze(["hizliAks", "aksSihirbazi", "baslikDegistir", "genellestir"]);
  /** Geri al menüsündeki adlar ("Geri al: Hızlı aks"). */
  const ISLEM_ADLARI = Object.freeze({ hizliAks: "Hızlı aks", aksSihirbazi: "Aks sihirbazı", baslikDegistir: "Başlık değiştir",
    genellestir: "Genel modele dönüştür", tabloUygula: "Tablo düzenleme" });

  /** Henüz gövdesi doldurulmamış yöntemler (F1 iş 1.3 ile boşaldı). */
  const TASLAK = Object.freeze([]);

  function modul(ad, yol) {
    if (kok && kok[ad]) return kok[ad];
    if (typeof require === "function") { try { return require(yol); } catch (e) { return null; } }
    return null;
  }

  /**
   * @typedef {{tur: string, no: number, alt?: number}} ElemanKimligi
   * @typedef {{baslik: string, surum: number, sistem: string, dugum: number, cubuk: number, panel: number, kat: number,
   *            aks: number, bos: boolean}} ModelOzeti
   * @typedef {{islem: string, basarili: boolean, hata?: string, uyarilar: string[], eklenen: ElemanKimligi[],
   *            silinen: ElemanKimligi[], degisen: ElemanKimligi[], icerik_degisti: boolean, sahne_surumu: number,
   *            gecis_onayi?: {metin: string}}} IslemRaporu
   *   eklenen / silinen / degisen kimliğe göre sıralı ve tekrarsızdır (önceki ve sonraki sahnenin farkı; surum 1 modelde genel
   *   görünüm kimlikleri). icerik_degisti: model metni değişti (eleman listeleri boş olsa da: başlık, kesit tablosu …).
   *   gecis_onayi doluysa model DEĞİŞMEMİŞTİR: UI sorar, onaylanırsa aynı işlem parametrelere onay: true eklenerek çağrılır.
   */

  /**
   * Yeni bir çekirdek örneği (pencere başına bir; C++ tek örnek kullanır, node sınamaları birden çok).
   * @param {{ModelOps?, MatrisAks?, MatrisBinaCizim?, MatrisIFC?, MatrisTablo?, Op4Ops?}} [bagimliliklar]
   * @param {{geriAlAdim?: number, geriAlMb?: number, saat?: () => number}} [ayar]
   */
  function olustur(bagimliliklar, ayar) {
    const B = bagimliliklar || {};
    const OP = B.Op4Ops || modul("Op4Ops", "./op4_ops.js");
    const MO = B.ModelOps || modul("ModelOps", "../../docs/model_ops.js");
    const MA = B.MatrisAks || modul("MatrisAks", "../../docs/aks_sistemi.js");
    const BC = B.MatrisBinaCizim || modul("MatrisBinaCizim", "../../docs/bina_cizim.js");
    const IFC = B.MatrisIFC || modul("MatrisIFC", "../../docs/ifc_disari.js");
    const TB = B.MatrisTablo || modul("MatrisTablo", "../../docs/tablo_editoru.js");
    OP.bagimliliklarKur({ ModelOps: MO, MatrisAks: MA, MatrisIFC: IFC });
    const A = Object.assign({ geriAlAdim: 100, geriAlMb: 512 }, ayar || {});
    const saat = typeof A.saat === "function" ? A.saat : function () { return Date.now(); };

    let model = OP.bosModel();
    let sahneSurumu = 0;
    let gecmis = [], ileri = [];       // [{model, ad, bayt}]
    let turev = null;                   // {model, cozum, sahne, kat, kullanim, oznitelik, kodlu}

    // ---------------------------------------------------------------- türetilmiş veri (model nesnesine bağlı önbellek)
    function turetilmis() {
      if (turev && turev.model === model) return turev;
      turev = { model: model, cozum: OP.cozumle(model) };
      return turev;
    }
    function sahneAl() {
      const t = turetilmis();
      if (!t.sahne) t.sahne = OP.sahneCikar(model, sahneSurumu, { cozum: t.cozum });
      if (t.sahne.sahne_surumu !== sahneSurumu) t.sahne.sahne_surumu = sahneSurumu;
      return t.sahne;
    }
    function oznitelikAl() {
      const t = turetilmis();
      if (!t.oznitelik) {
        if (!t.kat) t.kat = OP.katUyeligi(model, { cozum: t.cozum });
        if (!t.kullanim) t.kullanim = OP.kullanimYeri(model, { cozum: t.cozum, kat: t.kat });
        t.oznitelik = OP.oznitelikCikar(model, { cozum: t.cozum, kat: t.kat, kullanim: t.kullanim });
      }
      return t.oznitelik;
    }
    function ozetKur() {
      const say = function (k) { return Array.isArray(model[k]) ? model[k].length : 0; };
      const ak = model.akslar || {};
      const o = {
        baslik: model.baslik || "", surum: +model.surum || 1, sistem: model.sistem || "celik",
        dugum: say("dugumler"), cubuk: say("cubuklar") + say("kolonlar") + say("kirisler"),
        panel: say("paneller") + say("dosemeler"), kat: say("katlar"),
        aks: (Array.isArray(ak.x) ? ak.x.length : 0) + (Array.isArray(ak.y) ? ak.y.length : 0), bos: false,
      };
      o.bos = o.dugum + o.cubuk + o.panel === 0;
      return o;
    }
    /** Geri al yığını için kestirilen bayt (eleman sayısından; JSON metni çıkarmadan). */
    function bayt(m) {
      let n = 0;
      for (const k of ["dugumler", "cubuklar", "paneller", "mesnetler", "ek_yukler", "uretecler", "kolonlar", "kirisler", "dosemeler", "kren"]) {
        if (Array.isArray(m[k])) n += m[k].length;
      }
      return 16384 + 320 * n;
    }
    function rapor(islem) {
      return { islem: islem, basarili: false, uyarilar: [], eklenen: [], silinen: [], degisen: [], icerik_degisti: false, sahne_surumu: sahneSurumu };
    }
    function hataRaporu(islem, hata) { const r = rapor(islem); r.hata = hata; return r; }
    function girdiHatasiMi(e) {
      return !!e && (e.name === "ModelHatasi" || e.name === "AksHatasi" || e.name === "Op4Hatasi" ||
        (MO && e instanceof MO.ModelHatasi) || (OP && e instanceof OP.Op4Hatasi) || (MA && MA.AksHatasi && e instanceof MA.AksHatasi));
    }
    function sinirla() {
      const adim = Math.max(1, Math.floor(+A.geriAlAdim || 100)), sinir = (+A.geriAlMb > 0 ? +A.geriAlMb : 512) * 1048576;
      while (gecmis.length > adim) gecmis.shift();
      let t = 0;
      for (const g of gecmis) t += g.bayt;
      while (gecmis.length > 1 && t > sinir) t -= gecmis.shift().bayt;
    }
    /** Yeni modeli uygular: fark raporu, geri al adımı, sahne sürümü. */
    function gec(islem, yeni, uyarilar, yigin) {
      const r = rapor(islem);
      r.basarili = true;
      r.uyarilar = uyarilar || [];
      if (yeni === model) return r;
      const eski = sahneAl();
      const onceki = model;
      model = yeni;
      sahneSurumu++;
      const f = OP.sahneFarki(eski, sahneAl());
      r.eklenen = f.eklenen; r.silinen = f.silinen; r.degisen = f.degisen;
      r.icerik_degisti = true;
      r.sahne_surumu = sahneSurumu;
      if (yigin === "geri") ileri.push({ model: onceki, ad: gecmis.pop().ad, bayt: bayt(onceki) });
      else if (yigin === "ileri") gecmis.push({ model: onceki, ad: ileri.pop().ad, bayt: bayt(onceki) });
      else { gecmis.push({ model: onceki, ad: ISLEM_ADLARI[islem] || islem, bayt: bayt(onceki) }); ileri = []; sinirla(); }
      return r;
    }

    // ---------------------------------------------------------------- işlemler (saf: model → {model, uyarilar})
    function sayilar(l, ad) {
      if (!Array.isArray(l)) return null;
      return l.map(function (v, i) {
        const x = typeof v === "number" ? v : MA.sayiOku(v);
        if (!(isFinite(x) && x > 0)) throw new OP.Op4Hatasi(ad + "[" + i + "] sıfırdan büyük bir sayı olmalı (girilen: " + JSON.stringify(v) + ").");
        return x;
      });
    }
    function konumlar(araliklar, taban) {
      const k = [taban];
      for (const a of araliklar) k.push(Math.round((k[k.length - 1] + a) * 1e6) / 1e6);
      return k;
    }
    const UYGULA = {
      hizliAks: function (m, p) {
        if (p.x == null || p.y == null || p.z == null) throw new OP.Op4Hatasi("Hızlı aks: x, y (aks aralıkları) ve z (kat yükseklikleri) gerekli.");
        const taban = p.taban != null ? +p.taban : 0;
        const q = { ilkX: p.ilkX || (p.adlar && p.adlar.x), ilkY: p.ilkY || (p.adlar && p.adlar.y), balon: p.balon, ekZ: p.ekZ, taban: taban };
        const x = sayilar(p.x, "x"), y = sayilar(p.y, "y"), z = sayilar(p.z, "z");
        q.x = x ? konumlar(x, 0) : p.x;
        q.y = y ? konumlar(y, 0) : p.y;
        q.z = z ? konumlar(z, taban) : p.z;
        const ak = MA.hizliAks(q);
        const katlar = MA.katlarTuret(ak, m.katlar);
        const r = BC.aksSihirbazUygula(m, ak, katlar);
        const uy = (r.uyarilar || []).slice();
        for (const s of r.silinen || []) uy.push(s.yon.toUpperCase() + " " + s.ad + " aksıyla birlikte silindi: " + s.ozet + ".");
        return { model: r.model, uyarilar: uy };
      },
      aksSihirbazi: function (m, p) {
        if (!p.akslar || typeof p.akslar !== "object") throw new OP.Op4Hatasi("aksSihirbazi: akslar {x, y, z} gerekli.");
        const r = BC.aksSihirbazUygula(m, p.akslar, p.katlar || MA.katlarTuret(p.akslar, m.katlar));
        const uy = (r.uyarilar || []).slice();
        for (const s of r.silinen || []) uy.push(s.yon.toUpperCase() + " " + s.ad + " aksıyla birlikte silindi: " + s.ozet + ".");
        return { model: r.model, uyarilar: uy };
      },
      baslikDegistir: function (m, p) {
        const b = p.baslik == null ? "" : String(p.baslik).trim();
        if (!b) throw new OP.Op4Hatasi("Başlık boş olamaz.");
        if (b === m.baslik) return { model: m, uyarilar: [] };
        return { model: Object.assign({}, m, { baslik: b }), uyarilar: [] };
      },
      genellestir: function (m) {
        if (!BC.genelGecisGerekli(m)) return { model: m, uyarilar: ["Model zaten genel (surum 3) model; dönüştürülecek aks–kat elemanı yok."] };
        const g = BC.genellestirHazirla(m);
        return { model: g.model, uyarilar: g.notlar || [] };
      },
    };
    /** C1 kapısı: bu işlem aks–kat modelini genel modele çevirir mi (onay ister). */
    const GENEL_GEREKLI = { genellestir: true };

    function yuklendi(m, uyarilar) {
      model = m;
      sahneSurumu++;
      gecmis = []; ileri = [];
      turev = null;
      const uy = (uyarilar || []).slice();
      if (!BC.genelMi(m)) uy.push("Aks–kat (surum " + (+m.surum || 1) + ") model genel görünümle gösteriliyor; ilk genel model düzenlemesinde dönüştürme onayı istenir.");
      const s = sahneAl();
      for (const u of s.uyarilar || []) uy.push(u);
      return { basarili: true, ozet: ozetKur(), uyarilar: uy, surum: +m.surum || 1 };
    }

    return {
      /**
       * Boş model "Adsız N"; geri al yığını sıfırlanır.
       * @param {{baslik?: string, sistem?: string}} [secenek]
       * @returns {{basarili: boolean, ozet: ModelOzeti, uyarilar: string[]}}
       */
      yeniBos: function (secenek) {
        const r = yuklendi(OP.bosModel(secenek), []);
        return { basarili: true, ozet: r.ozet, uyarilar: [] };
      },
      /**
       * Bina JSON metnini yükler (surum 1 ya da 3; .matris / bina_sablon yanıtı sarmalayıcıları açılır); geri al sıfırlanır.
       * Sahne çıkarılamayan başvurular uyarı olarak döner (model yine yüklenir).
       * @param {string} binaMetni
       * @param {string} kaynak "dosya:<yol>" | "sablon:<ad>" | "kurtarma"
       * @returns {{basarili: boolean, hata?: string, ozet?: ModelOzeti, uyarilar: string[], surum?: number}}
       */
      yukle: function (binaMetni, kaynak) {
        let m;
        try { m = typeof binaMetni === "string" ? JSON.parse(binaMetni) : binaMetni; } catch (e) { return { basarili: false, hata: "Bina modeli okunamadı (geçerli JSON değil): " + kaynak, uyarilar: [] }; }
        if (m && m.bina && typeof m.bina === "object" && !Array.isArray(m.bina)) m = m.bina;
        if (!m || typeof m !== "object" || Array.isArray(m) || m.tur !== "bina") return { basarili: false, hata: "Dosya bir bina modeli değil (\"tur\": \"bina\" yok): " + kaynak, uyarilar: [] };
        const eski = { model: model, sahneSurumu: sahneSurumu, gecmis: gecmis, ileri: ileri, turev: turev };
        try {
          return yuklendi(m, []);
        } catch (e) {
          model = eski.model; sahneSurumu = eski.sahneSurumu; gecmis = eski.gecmis; ileri = eski.ileri; turev = eski.turev;
          if (girdiHatasiMi(e)) return { basarili: false, hata: "Bina modeli açılamadı (" + kaynak + "): " + e.message, uyarilar: [] };
          throw e;
        }
      },
      /**
       * Beyaz listedeki bir işlemi uygular (tek geri al adımı).
       * @param {string} islem ISLEMLER'den
       * @param {Object} parametreler
       * @returns {IslemRaporu}
       */
      uygula: function (islem, parametreler) {
        if (ISLEMLER.indexOf(islem) < 0) return hataRaporu(islem, "Bilinmeyen işlem: " + islem);
        const p = parametreler && typeof parametreler === "object" ? parametreler : {};
        if (GENEL_GEREKLI[islem] && !p.onay && BC.genelGecisGerekli(model)) {
          const r = rapor(islem);
          r.basarili = true;
          r.gecis_onayi = { metin: BC.genelGecisMetni(model, ISLEM_ADLARI[islem]) };
          return r;
        }
        let s;
        try { s = UYGULA[islem](model, p); } catch (e) {
          if (girdiHatasiMi(e)) return hataRaporu(islem, e.message);
          throw e;
        }
        return gec(islem, s.model, s.uyarilar);
      },
      /** @returns {IslemRaporu} */
      geriAl: function () {
        if (!gecmis.length) return hataRaporu("geriAl", "Geri alınacak işlem yok");
        return gec("geriAl", gecmis[gecmis.length - 1].model, [], "geri");
      },
      /** @returns {IslemRaporu} */
      yinele: function () {
        if (!ileri.length) return hataRaporu("yinele", "Yinelenecek işlem yok");
        return gec("yinele", ileri[ileri.length - 1].model, [], "ileri");
      },
      /** @returns {{geri_alinabilir: boolean, yinelenebilir: boolean, geri_al_adi: string, yinele_adi: string, adim: number, yine_adim: number}} */
      geriAlBilgisi: function () {
        return { geri_alinabilir: gecmis.length > 0, yinelenebilir: ileri.length > 0,
          geri_al_adi: gecmis.length ? gecmis[gecmis.length - 1].ad : "", yinele_adi: ileri.length ? ileri[ileri.length - 1].ad : "",
          adim: gecmis.length, yine_adim: ileri.length };
      },
      /** @returns {string[]} beyaz liste */
      islemler: function () { return ISLEMLER.slice(); },
      /** @returns {Object} Op4Ops.sahneCikar biçimi (tipli diziler); aynı model → aynı nesne */
      sahne: function () { return sahneAl(); },
      /** @returns {Object} Op4Ops.oznitelikCikar biçimi */
      oznitelikler: function () { return oznitelikAl(); },
      /** @returns {Object} Op4Ops.oznitelikKodla biçimi (C++ köprüsü; tipli diziler) */
      oznitelikKodlu: function () {
        const t = turetilmis();
        if (!t.kodlu) t.kodlu = OP.oznitelikKodla(oznitelikAl());
        return t.kodlu;
      },
      /** @returns {number} */
      sahneSurumu: function () { return sahneSurumu; },
      /** @returns {ModelOzeti} */
      ozet: function () { return ozetKur(); },
      /**
       * ModelOps.denetle (genel görünümde) + serbest düğüm sayısı (MIMARI §10.1).
       * @returns {{gecerli: boolean, uyarilar: string[], eleman_uyarilari: Array<{kimlik: ElemanKimligi, metin: string}>, serbest_dugum: number}}
       */
      denetle: function () {
        const t = turetilmis();
        let d;
        try { d = MO.denetle(t.cozum.g); } catch (e) {
          if (girdiHatasiMi(e)) return { gecerli: false, uyarilar: [e.message], eleman_uyarilari: [], serbest_dugum: 0 };
          throw e;
        }
        const uy = [], el = [];
        for (const u of d.uyarilar || []) {
          const metin = typeof u === "string" ? u : String(u.mesaj || u.metin || "");
          uy.push(metin);
          if (!u || typeof u !== "object") continue;
          const ekle = function (tur, no) { if (no != null && isFinite(+no)) el.push({ kimlik: { tur: tur, no: +no }, metin: metin }); };
          ekle("cubuk", u.cubuk); ekle("panel", u.panel); ekle("dugum", u.dugum);
          for (const n of u.cubuklar || []) ekle("cubuk", n);
          for (const n of u.dugumler || []) ekle("dugum", n);
        }
        const s = sahneAl();
        let serbest = 0;
        for (let i = 0; i < s.dugumler.tur.length; i++) if (s.dugumler.tur[i] === OP.KODLAR.dugum_turu.serbest) serbest++;
        return { gecerli: !!d.gecerli, uyarilar: uy, eleman_uyarilari: el, serbest_dugum: serbest };
      },
      /**
       * Kanonik bina JSON metni (kaydetme ve çözüm girdisi): aynı model → aynı metin (anahtar sırası korunur, boşluk yok).
       * @returns {string}
       */
      metin: function () { return JSON.stringify(model); },
      /**
       * @param {Object} veri bina_coz "veri" nesnesi
       * @returns {{basarili: boolean, hata?: string, elemanlar: Array, uyarilar: string[]}} Op4Ops.sonucEsle biçimi
       */
      sonucEsle: function (veri) {
        if (!veri || typeof veri !== "object") return { basarili: false, hata: "Çözüm verisi (veri) bir nesne olmalı.", elemanlar: [], uyarilar: [] };
        const r = OP.sonucEsle(model, veri, { cozum: turetilmis().cozum });
        return { basarili: true, elemanlar: r.elemanlar, uyarilar: r.uyarilar };
      },
      /**
       * IFC4 dışa aktarma (docs/ifc_disari.js uretAyrintili; MIMARI §14.1). zaman verilmezse çekirdek saati (sınamada
       * deterministik) kullanılır; uygulama verilirse dosya başlığı ve IfcApplication / IfcOrganization onu taşır.
       * @param {{analiz?: boolean, yukler?: boolean, dc?: boolean, uygulama?: {ad: string, surum: string, firma: string}, zaman?: string,
       *          tohum?: string, proje?: Object, izgara?: string|boolean}} secenek
       * @param {Object|null} veri son bina_coz "veri"si (D/C için) ya da null
       * @returns {{basarili: boolean, hata?: string, metin?: string, dosya_adi?: string, uyarilar: string[]}}
       */
      ifcDisari: function (secenek, veri) {
        const s = secenek || {};
        const zaman = s.zaman || new Date(saat()).toISOString().slice(0, 19);
        const q = { zaman: zaman, analiz: s.analiz !== false, yukler: !!s.yukler && !!veri, sonuclar: !!s.dc && !!veri };
        for (const k of ["tohum", "proje", "izgara", "dosya_adi"]) if (s[k] != null) q[k] = s[k];
        let r;
        try { r = IFC.uretAyrintili(model, veri || null, q); } catch (e) {
          return { basarili: false, hata: "IFC dışa aktarılamadı: " + e.message, uyarilar: [] };
        }
        let metin = r.metin;
        if (s.uygulama && s.uygulama.ad) metin = uygulamaKimligi(IFC, metin, s.uygulama);
        return { basarili: true, metin: metin, dosya_adi: r.dosya_adi, uyarilar: r.uyarilar || [] };
      },
      /**
       * Tablo düzenleyici değişiklikleri (MatrisTablo._ic.degisiklikleriUygula: tablolar.degisiklikleri_uygula ile aynı anlam).
       * Tek geri al adımı.
       * @param {Array<{yol: Array, deger: *, bag?: Array}>} degisiklikler
       * @returns {IslemRaporu}
       */
      tabloUygula: function (degisiklikler) {
        if (!Array.isArray(degisiklikler)) return hataRaporu("tabloUygula", "Değişiklik listesi bir dizi olmalı.");
        let yeni;
        try { yeni = TB._ic.degisiklikleriUygula(model, degisiklikler); } catch (e) {
          return hataRaporu("tabloUygula", "Tablo değişikliği uygulanamadı: " + e.message);
        }
        if (JSON.stringify(yeni) === JSON.stringify(model)) return gec("tabloUygula", model, ["Değişiklik modelde fark oluşturmadı."]);
        return gec("tabloUygula", yeni, []);
      },
    };
  }

  /** IFC başlığındaki ve sahiplik geçmişindeki uygulama kimliğini değiştirir (docs/ifc_disari.js "Matris Öğren" yazar). */
  function uygulamaKimligi(IFC, metin, u) {
    const S = function (x) { return "'" + IFC.stepMetin(String(x)) + "'"; };
    const eskiAd = S("Matris Öğren"), eskiTam = S("Matris Öğren " + IFC.SURUM);
    const ad = String(u.ad), surum = String(u.surum || ""), firma = String(u.firma || u.ad);
    const satirlar = metin.split("\n");
    let org = null;
    for (let i = 0; i < satirlar.length; i++) {
      const s = satirlar[i];
      if (s.indexOf("FILE_NAME(") === 0) satirlar[i] = s.replace(eskiTam + "," + eskiAd, S(ad + (surum ? " " + surum : "")) + "," + S(ad));
      else if (org == null && /^#\d+=IFCORGANIZATION\(\$,/.test(s) && s.indexOf(eskiAd) > 0) {
        org = s.slice(0, s.indexOf("="));
        satirlar[i] = s.replace(eskiAd, S(firma));
      } else if (/^#\d+=IFCAPPLICATION\(/.test(s)) {
        satirlar[i] = s.replace(/IFCAPPLICATION\((#\d+),'[^']*',.*\);$/, function (_, o) { return "IFCAPPLICATION(" + o + "," + S(surum) + "," + S(ad) + "," + S(ad) + ");"; });
      }
    }
    return satirlar.join("\n");
  }

  return { SURUM: SURUM, ISLEMLER: ISLEMLER, ISLEM_ADLARI: ISLEM_ADLARI, TASLAK: TASLAK, olustur: olustur };
});
