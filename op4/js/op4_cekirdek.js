/* op4 — model çekirdeği CEPHESİ (MIMARI §9.3; "F1 paket sözleşmeleri" §S27). QuickJS-ng içinde model otoritesidir;
   C++ ModelCekirdegi (op4/kaynak/cekirdek/model_cekirdegi.h) her yöntemi aynı adla çağırır ve sonucu C++ yapılarına çevirir.
   QuickJS'te self.Op4Cekirdek, node'da module.exports (UMD). Sahibi: B (model-cekirdegi). Bu dosya SÖZLEŞMEDİR: imzalar,
   dönüş biçimleri ve hata kuralları JSDoc'tadır; gövdeler F1 iş 1.3'te doldurulur (TASLAK listesi).

   Bağımlılıklar (QuickJS ön yüklemesi globalThis.self = globalThis ile UMD modüllerini self üstüne kurar; node'da require):
     ModelOps (docs/model_ops.js), MatrisAks (docs/aks_sistemi.js), MatrisBinaCizim (docs/bina_cizim.js),
     MatrisIFC (docs/ifc_disari.js), MatrisTablo (docs/tablo_editoru.js), Op4Ops (op4/js/op4_ops.js).

   Çağrı kuralı (C++ köprüsü): parametreler düz nesnedir (C++ JSON metnini JSON.parse ile verir); dönüşler düz nesne ve
   tipli dizilerdir. Eleman kimliği {tur, no, alt?} (op4_ops.js). Hata kuralı: geçersiz girdi (ModelOps.ModelHatasi,
   Op4Ops.Op4Hatasi) → {basarili: false, hata}; geometrik ret → {basarili: true, uyarilar: [...]} ve model değişmez; başka
   istisna → fırlatılır (C++ "İç hata" olarak yakalar ve günlüğe yazar).

   Geri al (MIMARI §9.4): değişmez anlık yığını; sınır 100 adım ya da 512 MB (ayarlanır); dosyaya kaydedilmez; seçim ve
   görünüm kapsam dışıdır. Her başarılı ve modeli değiştiren uygula() tek adımdır. */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika(kok);
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.Op4Cekirdek = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function (kok) {
  "use strict";

  const SURUM = "0.1.0-sozlesme";

  /**
   * uygula() beyaz listesi, Faz 1 (C++ islem:: sabitleri). Faz 3–4'te ModelOps / MatrisAks / MatrisBinaCizim / Op4Ops
   * işlemleri eklenir (MIMARI §12.4). Listede olmayan ad → {basarili: false, hata: "Bilinmeyen işlem: …"}.
   *   hizliAks       {x: number[] (aralıklar m), y: number[], z: number[] (kat yükseklikleri m), adlar?: {x?, y?}}
   *                  → MatrisAks.hizliAks + MatrisBinaCizim.aksSihirbazUygula
   *   aksSihirbazi   MatrisBinaCizim.aksSihirbazUygula(bina, akslar, katlar) parametreleri {akslar, katlar}
   *   baslikDegistir {baslik: string}
   *   genellestir    {} → aks–kat modelini genel modele çevirir (C1; onay: true ile)
   */
  const ISLEMLER = Object.freeze(["hizliAks", "aksSihirbazi", "baslikDegistir", "genellestir"]);

  /** Henüz gövdesi doldurulmamış yöntemler (B, F1 iş 1.3). */
  const TASLAK = Object.freeze(["uygula", "geriAl", "yinele", "sahne", "oznitelikler", "sonucEsle", "denetle", "ifcDisari", "tabloUygula"]);

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
   *            silinen: ElemanKimligi[], degisen: ElemanKimligi[], sahne_surumu: number,
   *            gecis_onayi?: {metin: string}}} IslemRaporu
   *   eklenen / silinen / degisen kimliğe göre sıralı ve tekrarsızdır (ModelOps raporundan; surum 1 modelde genel görünüm).
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
    const A = Object.assign({ geriAlAdim: 100, geriAlMb: 512 }, ayar || {});
    void A;
    let model = OP.bosModel();
    let sahneSurumu = 0;

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
    function bosRapor(islem, hata) {
      return { islem: islem, basarili: false, hata: hata, uyarilar: [], eklenen: [], silinen: [], degisen: [], sahne_surumu: sahneSurumu };
    }

    return {
      /**
       * Boş model "Adsız N"; geri al yığını sıfırlanır.
       * @param {{baslik?: string}} [secenek]
       * @returns {{basarili: boolean, ozet: ModelOzeti, uyarilar: string[]}}
       */
      yeniBos: function (secenek) {
        model = OP.bosModel(secenek);
        sahneSurumu++;
        return { basarili: true, ozet: ozetKur(), uyarilar: [] };
      },
      /**
       * Bina JSON metnini yükler (surum 1 ya da 3; .matris / bina_sablon yanıtı sarmalayıcıları açılır); geri al sıfırlanır.
       * @param {string} binaMetni
       * @param {string} kaynak "dosya:<yol>" | "sablon:<ad>" | "kurtarma"
       * @returns {{basarili: boolean, hata?: string, ozet?: ModelOzeti, uyarilar: string[], surum?: number}}
       */
      yukle: function (binaMetni, kaynak) {
        let m;
        try { m = JSON.parse(binaMetni); } catch (e) { return { basarili: false, hata: "Bina modeli okunamadı (geçerli JSON değil): " + kaynak, uyarilar: [] }; }
        if (m && m.bina && typeof m.bina === "object") m = m.bina;
        if (!m || m.tur !== "bina") return { basarili: false, hata: "Dosya bir bina modeli değil (\"tur\": \"bina\" yok): " + kaynak, uyarilar: [] };
        model = m;
        sahneSurumu++;
        return { basarili: true, ozet: ozetKur(), uyarilar: [], surum: +m.surum || 1 };
      },
      /**
       * Beyaz listedeki bir işlemi uygular (tek geri al adımı).
       * @param {string} islem ISLEMLER'den
       * @param {Object} parametreler
       * @returns {IslemRaporu}
       */
      uygula: function (islem, parametreler) {
        void parametreler;
        if (ISLEMLER.indexOf(islem) < 0) return bosRapor(islem, "Bilinmeyen işlem: " + islem);
        return bosRapor(islem, "İşlem henüz bağlanmadı (F1 iş 1.3): " + islem);
      },
      /** @returns {IslemRaporu} */
      geriAl: function () { return bosRapor("geriAl", "Geri alınacak işlem yok"); },
      /** @returns {IslemRaporu} */
      yinele: function () { return bosRapor("yinele", "Yinelenecek işlem yok"); },
      /** @returns {{geri_alinabilir: boolean, yinelenebilir: boolean, geri_al_adi: string, yinele_adi: string, adim: number, yine_adim: number}} */
      geriAlBilgisi: function () { return { geri_alinabilir: false, yinelenebilir: false, geri_al_adi: "", yinele_adi: "", adim: 0, yine_adim: 0 }; },
      /** @returns {string[]} beyaz liste */
      islemler: function () { return ISLEMLER.slice(); },
      /** @returns {Object} Op4Ops.sahneCikar biçimi (tipli diziler) */
      sahne: function () { return OP.sahneCikar(model, sahneSurumu); },
      /** @returns {Object} Op4Ops.oznitelikCikar biçimi */
      oznitelikler: function () { return OP.oznitelikCikar(model); },
      /** @returns {number} */
      sahneSurumu: function () { return sahneSurumu; },
      /** @returns {ModelOzeti} */
      ozet: function () { return ozetKur(); },
      /**
       * ModelOps.denetle (+ serbest düğüm sayısı, MIMARI §10.1).
       * @returns {{gecerli: boolean, uyarilar: string[], eleman_uyarilari: Array<{kimlik: ElemanKimligi, metin: string}>, serbest_dugum: number}}
       */
      denetle: function () { return { gecerli: true, uyarilar: [], eleman_uyarilari: [], serbest_dugum: 0 }; },
      /**
       * Kanonik bina JSON metni (kaydetme ve çözüm girdisi): aynı model → aynı metin (anahtar sırası korunur, boşluk yok).
       * @returns {string}
       */
      metin: function () { return JSON.stringify(model); },
      /**
       * @param {Object} veri bina_coz "veri" nesnesi
       * @returns {{basarili: boolean, hata?: string, elemanlar: Array, uyarilar: string[]}} Op4Ops.sonucEsle biçimi
       */
      sonucEsle: function (veri) { void veri; return { basarili: false, hata: "Sonuç eşleme henüz bağlanmadı (F1 iş 1.3).", elemanlar: [], uyarilar: [] }; },
      /**
       * IFC4 dışa aktarma (docs/ifc_disari.js uretAyrintili; MIMARI §14.1).
       * @param {{analiz?: boolean, yukler?: boolean, dc?: boolean, uygulama?: {ad: string, surum: string, firma: string}, zaman?: string}} secenek
       * @param {Object|null} veri son bina_coz "veri"si (D/C için) ya da null
       * @returns {{basarili: boolean, hata?: string, metin?: string, dosya_adi?: string, uyarilar: string[]}}
       */
      ifcDisari: function (secenek, veri) { void secenek; void veri; return { basarili: false, hata: "IFC dışa aktarma henüz bağlanmadı (F1 iş 1.3).", uyarilar: [] }; },
      /**
       * Tablo düzenleyici değişiklikleri (Faz 5; MatrisTablo._ic.degisiklikleriUygula). Tek geri al adımı.
       * @param {Array<Object>} degisiklikler
       * @returns {IslemRaporu}
       */
      tabloUygula: function (degisiklikler) { void degisiklikler; return bosRapor("tabloUygula", "Tablo düzenleme Faz 5'te."); },
    };
  }

  return { SURUM: SURUM, ISLEMLER: ISLEMLER, TASLAK: TASLAK, olustur: olustur };
});
