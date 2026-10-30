/* op4 — model çekirdeği C++ köprüsü (QuickJS tarafı; MIMARI §9.3, kabul B5). Sahibi: B (model-cekirdegi).
   C++ (kaynak/cekirdek_js/quickjs_cekirdek.cpp) cepheye (Op4Cekirdek) YALNIZ bu nesne üstünden girer:
     - parametreler JSON metni olarak gelir (C++ nlohmann ile üretir), küçük dönüşler JSON metnidir;
     - sahne ve öznitelik tablosu tipli dizilerle döner (C++ ArrayBuffer belleğini serileştirmeden okur);
     - kimlik listeleri Float64Array'de ElemanKimligi::Anahtar() değerleridir (tür·2^48 + alt·2^32 + no; 2^53'ün altında, kesin).
   node'da kullanılmaz; cephe node'da doğrudan sınanır (op4/testler/js/op4_cekirdek.test.js). */
(function (g) {
  "use strict";
  let c = null;

  function anahtarlar(l) {
    const a = new Float64Array((l || []).length);
    for (let i = 0; i < a.length; i++) a[i] = g.Op4Ops.kimlikAnahtari(l[i]);
    return a;
  }
  function rapor(r) {
    const o = {};
    for (const k of Object.keys(r)) if (k !== "eklenen" && k !== "silinen" && k !== "degisen") o[k] = r[k];
    return { json: JSON.stringify(o), eklenen: anahtarlar(r.eklenen), silinen: anahtarlar(r.silinen), degisen: anahtarlar(r.degisen) };
  }
  function cekirdek() {
    if (!c) throw new Error("Op4Kopru.kur çağrılmadı");
    return c;
  }

  g.Op4Kopru = {
    /** @param {string} ayarJson {geriAlAdim, geriAlMb} */
    kur: function (ayarJson) {
      const a = ayarJson ? JSON.parse(ayarJson) : {};
      c = g.Op4Cekirdek.olustur({ ModelOps: g.ModelOps, MatrisAks: g.MatrisAks, MatrisBinaCizim: g.MatrisBinaCizim, MatrisIFC: g.MatrisIFC,
        MatrisTablo: g.MatrisTablo, Op4Ops: g.Op4Ops }, { geriAlAdim: a.geriAlAdim, geriAlMb: a.geriAlMb, saat: function () { return Date.now(); } });
      return JSON.stringify({ islemler: c.islemler(), surum: g.Op4Cekirdek.SURUM, ops: g.Op4Ops.SURUM });
    },
    yeniBos: function (baslik) { return JSON.stringify(cekirdek().yeniBos(baslik ? { baslik: baslik } : {})); },
    yukle: function (metin, kaynak) { return JSON.stringify(cekirdek().yukle(metin, kaynak)); },
    uygula: function (islem, pJson) { return rapor(cekirdek().uygula(islem, pJson ? JSON.parse(pJson) : {})); },
    geriAl: function () { return rapor(cekirdek().geriAl()); },
    yinele: function () { return rapor(cekirdek().yinele()); },
    tabloUygula: function (dJson) { return rapor(cekirdek().tabloUygula(JSON.parse(dJson))); },
    durum: function () {
      const k = cekirdek();
      return JSON.stringify({ geri_al: k.geriAlBilgisi(), ozet: k.ozet(), sahne_surumu: k.sahneSurumu() });
    },
    /** Sahne: küçük kısımlar JSON (bilgi), dizi blokları tipli diziler. */
    sahne: function () {
      const s = cekirdek().sahne();
      const bilgi = { sahne_surumu: s.sahne_surumu, model_surumu: s.model_surumu, baslik: s.baslik, sistem: s.sistem,
        seviyeler: s.seviyeler, akslar: s.akslar, temeller: s.temeller, kesitler: s.kesitler, gruplar: s.gruplar, malzemeler: s.malzemeler };
      return { bilgi: JSON.stringify(bilgi), dugumler: s.dugumler, cubuklar: s.cubuklar, paneller: s.paneller, mesnetler: s.mesnetler };
    },
    oznitelik: function () { return cekirdek().oznitelikKodlu(); },
    denetle: function () { return JSON.stringify(cekirdek().denetle()); },
    metin: function () { return cekirdek().metin(); },
    sonucEsle: function (vJson) { return JSON.stringify(cekirdek().sonucEsle(vJson ? JSON.parse(vJson) : null)); },
    ifcDisari: function (sJson, vJson) {
      const r = cekirdek().ifcDisari(sJson ? JSON.parse(sJson) : {}, vJson ? JSON.parse(vJson) : null);
      const metin = r.metin || "";
      delete r.metin;
      return { json: JSON.stringify(r), metin: metin };
    },
  };
})(globalThis);
