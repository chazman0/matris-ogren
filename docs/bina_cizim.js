/* Matris Öğren — Bina sayfası aks tabanlı çizim ve düzenleme araçları (window.MatrisBinaCizim; node'da module.exports).
   Tasarım belgesi §19 (aks sistemi tabanlı modelleme), §12 (surum 3 listeleri), §17.1 (yüzen araç kutusu komutları).

   İlke (kullanıcı kararı): serbest koordinatla düğüm çizimi YOKTUR. Her düğüm bir aks kesişimi (X × Y × Z aksı; ek kartezyen /
   silindirik sistemler dahil) ya da mevcut bir çubuğun bölme / kesişim noktasıdır. Çizim araçları yalnız bunlara yakalar
   (MatrisOlcum.yakala kip "cizim" ve MatrisAks.enYakinKesisim / enYakinParca / gozBul). Üreteçlerin ve kopyalama işlemlerinin
   ürettiği ara noktalar işlem sonunda ModelOps.aksaBagla ve `serbestleriBagla` ile aks kesişimine ya da bölme düğümüne
   (iki aks kesişimi arasında parametrik oran) çevrilir; aks taşınınca birlikte taşınırlar.

   İki katman:
   1) SAF MANTIK (DOM yok, node testli): kolon çiftleri, çubuk türü, çakışan eleman denetimi, aks sihirbazı birleştirme, yeni model,
      beşik çerçeve / makas / kren yolu için gereken ek akslar ve üreteç parametreleri, serbest düğümlerin aksa bağlanması, mafsal /
      mesnet ön ayarları, mesnet ve yük kayıtları, seçim eşleme (genelleştirme sonrası), bölme noktaları, ekran → düzlem dönüşümü,
      aks ekleme konumu, işlem özeti.
   2) ARAYÜZ (tarayıcı): window.MatrisBina (docs/bina.js) hazır olunca kurulur: araç kutusu komutları (MatrisBina.komutBagla),
      sahne kipleri (kipKaydet), aks katmanı (MatrisAks.sahneKatmani, katmanKaydet sira < 0) ve yakalama/önizleme katmanı,
      aks balonu sürükleme (MatrisAks.balonSurukle), iletişim kutuları (kaplamaAc), sağ tık komutları (baglamKancasi).
   Bütün model değişiklikleri MatrisBina.binaAyarla ile tek geri al yığınından geçer. */
(function (kok, fabrika) {
  "use strict";
  let aksNode = null, opsNode = null;
  if (typeof module === "object" && module && module.exports && typeof require === "function") {
    try { aksNode = require("./aks_sistemi.js"); } catch (e) { aksNode = null; }
    try { opsNode = require("./model_ops.js"); } catch (e) { opsNode = null; }
  }
  const api = fabrika(function () { return (kok && kok.MatrisAks) || aksNode; }, function () { return (kok && kok.ModelOps) || opsNode; });
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) {
    kok.MatrisBinaCizim = api;
    if (typeof window !== "undefined" && typeof document !== "undefined") api.otomatikKur();
  }
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function (aksAl, opsAl) {
  "use strict";

  const TOL = 0.001;
  const D2R = Math.PI / 180;

  // ================================================================= küçük yardımcılar
  function kopya(o) { return o === undefined ? undefined : JSON.parse(JSON.stringify(o)); }
  function r6(v) { const r = Math.round(v * 1e6) / 1e6; return r === 0 ? 0 : r; }
  function sayi(s) {
    if (typeof s === "number") return isFinite(s) ? s : null;
    let t = String(s == null ? "" : s).trim().replace(/−/g, "-");
    if (/^[+-]?\d+,\d+$/.test(t)) t = t.replace(",", ".");
    if (!/^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/.test(t)) return null;
    const n = parseFloat(t);
    return isFinite(n) ? n : null;
  }
  function fmt(v, n) {
    if (typeof v !== "number" || !isFinite(v)) return "—";
    const k = Math.pow(10, n == null ? 2 : n);
    return (Math.round(v * k) / k).toFixed(n == null ? 2 : n).replace(".", ",").replace("-", "−");
  }
  function fmtK(v) { return typeof v === "number" && isFinite(v) ? String(r6(Math.round(v * 1000) / 1000)).replace(".", ",").replace("-", "−") : "—"; }
  function uzaklik(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); }
  function MA() { const m = aksAl(); if (!m) throw new Error("Aks sistemi modülü (aks_sistemi.js) yüklenmedi."); return m; }
  function MO() { const m = opsAl(); if (!m) throw new Error("Model işlemleri modülü (model_ops.js) yüklenmedi."); return m; }
  function liste(b, ad) { return b && Array.isArray(b[ad]) ? b[ad] : []; }
  function aksListesi(b, yon) {
    const l = yon === "z" ? (b.akslar && Array.isArray(b.akslar.z) && b.akslar.z.length ? b.akslar.z : MA().sistemler(b)[0].l.z) : (b.akslar && b.akslar[yon]) || [];
    return l.map(function (a) { return { ad: String(a.ad), konum: +a.konum, kat: a.kat }; }).sort(function (a, c) { return a.konum - c.konum; });
  }
  function aksAdi(b, yon, konum, tol) {
    const a = aksListesi(b, yon).filter(function (x) { return Math.abs(x.konum - konum) <= (tol == null ? TOL : tol); })[0];
    return a ? a.ad : null;
  }

  // ================================================================= çubuk türü, kolon çiftleri
  /** Geometriden çubuk türü: düşey → kolon, yatay → kiriş, eğik → diger (kullanıcı değiştirir). */
  function cubukTuru(Pi, Pj) {
    const L = uzaklik(Pi, Pj);
    if (L < 1e-9) return "diger";
    const yat = Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1]);
    if (yat <= 1e-6 * L) return "kolon";
    if (Math.abs(Pj[2] - Pi[2]) <= 1e-6 * L) return "kiris";
    return "diger";
  }
  /**
   * Hızlı kolon: plan görünümünde tıklanan kesişim REF'i ({aks, z, sistem?}) için [altREF, üstREF] çiftleri.
   * sec.tumu: en alttaki Z aksından bu Z aksına kadar bütün aralıklar (çoklu kat); değilse yalnız hemen alttaki Z aksına.
   */
  function kolonCiftleri(bina, ref, sec) {
    sec = sec || {};
    if (!ref || !Array.isArray(ref.aks) || ref.z == null) return [];
    const S = MA().sistemBul(bina, ref.sistem);
    const zl = S.l.z, i = zl.findIndex(function (z) { return String(z.ad) === String(ref.z); });
    if (i <= 0) return [];
    const yap = function (z) { const r = { aks: ref.aks.slice(), z: String(z.ad) }; if (ref.sistem && ref.sistem !== "GLOBAL") r.sistem = ref.sistem; return r; };
    const out = [];
    for (let k = sec.tumu ? 0 : i - 1; k < i; k++) out.push([yap(zl[k]), yap(zl[k + 1])]);
    return out;
  }
  /** Aynı iki düğüm arasındaki çubuk (REF anahtarı ya da konum, 1 mm). */
  function mevcutCubuk(bina, refI, refJ) {
    const A = MA();
    const ki = A.refAnahtar(bina, refI), kj = A.refAnahtar(bina, refJ);
    const cz = new A.Cozucu(bina);
    let Pi = null, Pj = null;
    try { Pi = cz.coz(refI); Pj = cz.coz(refJ); } catch (e) { Pi = Pj = null; }
    for (const c of liste(bina, "cubuklar")) {
      if (!c) continue;
      const a = A.refAnahtar(bina, c.i), b = A.refAnahtar(bina, c.j);
      if ((a === ki && b === kj) || (a === kj && b === ki)) return +c.no;
      if (Pi && Pj) {
        let Ci, Cj;
        try { Ci = cz.coz(c.i); Cj = cz.coz(c.j); } catch (e) { continue; }
        if ((uzaklik(Ci, Pi) < TOL && uzaklik(Cj, Pj) < TOL) || (uzaklik(Ci, Pj) < TOL && uzaklik(Cj, Pi) < TOL)) return +c.no;
      }
    }
    return null;
  }
  /** Aks–kat kolon/kirişiyle çakışma: yeni çubuk (Pi–Pj) mevcut aks–kat elemanının üzerinde mi (eş doğrusal, örtüşen). */
  function aksKatCakisan(geo, Pi, Pj) {
    if (!geo || !Array.isArray(geo.cubuklar)) return null;
    const L = uzaklik(Pi, Pj);
    if (L < TOL) return null;
    const d = [(Pj[0] - Pi[0]) / L, (Pj[1] - Pi[1]) / L, (Pj[2] - Pi[2]) / L];
    const izd = function (Q) { const v = [Q[0] - Pi[0], Q[1] - Pi[1], Q[2] - Pi[2]]; const t = v[0] * d[0] + v[1] * d[1] + v[2] * d[2]; return { t: t, d: Math.hypot(v[0] - t * d[0], v[1] - t * d[1], v[2] - t * d[2]) }; };
    for (const c of geo.cubuklar) {
      if (c.kaynak !== "kolon" && c.kaynak !== "kiris") continue;
      const a = izd(c.A), b = izd(c.B);
      if (a.d > TOL || b.d > TOL) continue;
      const lo = Math.max(0, Math.min(a.t, b.t)), hi = Math.min(L, Math.max(a.t, b.t));
      if (hi - lo > TOL) return { tur: c.kaynak, no: c.no };
    }
    return null;
  }

  // ================================================================= aks sihirbazı
  /**
   * Hızlı aks sihirbazının çıktısını mevcut modele uygular ("mevcut aksları değiştir"):
   *  - aynı adlı X/Y aksı: konumu güncellenir (bağlı elemanlar yapışık taşınır); yeni ad: eklenir; eksik ad: elemanlarla birlikte silinir;
   *  - Z: kata bağlı akslar kat numarasıyla eşlenir (eski ad korunur: "Saçak" gibi), kat dışı akslar adla.
   * Dönüş: {model, silinen: [{yon, ad, ozet}], uyarilar}
   */
  function aksSihirbazUygula(bina, akslar, katlar) {
    const A = MA();
    let m = kopya(bina);
    const uy = [], silinen = [];
    if (!m.akslar) m.akslar = { x: [], y: [] };
    ["x", "y"].forEach(function (yon) {
      const yeni = (akslar && akslar[yon]) || [], eski = (m.akslar[yon] || []).slice();
      const yeniAd = new Set(yeni.map(function (a) { return String(a.ad); }));
      eski.forEach(function (a) {
        if (yeniAd.has(String(a.ad))) return;
        const r = A.aksSil(m, { yon: yon, ad: a.ad, secenek: "elemanlarla" });
        if (r.silindi === false) { uy.push.apply(uy, r.uyarilar || []); return; }
        m = r.model;
        if (r.bagli && r.bagli.toplam) silinen.push({ yon: yon, ad: String(a.ad), ozet: r.bagli.ozet });
      });
      const l = m.akslar[yon] || (m.akslar[yon] = []);
      yeni.forEach(function (a) {
        const v = l.filter(function (x) { return String(x.ad) === String(a.ad); })[0];
        if (v) { v.konum = r6(+a.konum); ["tur", "gorunur", "balon"].forEach(function (k) { if (a[k] != null && v[k] == null) v[k] = a[k]; }); }
        else l.push(kopya(a));
      });
      l.sort(function (p, q) { return +p.konum - +q.konum; });
    });
    // Z aksları
    const eskiZ = (m.akslar.z && m.akslar.z.length ? m.akslar.z : A.sistemler(m)[0].l.z.map(function (a) { const o = { ad: a.ad, konum: a.konum }; if (a.kat != null) o.kat = a.kat; return o; })).map(kopya);
    const yeniZ = ((akslar && akslar.z) || []).map(kopya);
    const zSon = [];
    yeniZ.forEach(function (a) {
      let v = null;
      if (a.kat != null) v = eskiZ.filter(function (x) { return x.kat != null && +x.kat === +a.kat; })[0] || null;
      if (!v) v = eskiZ.filter(function (x) { return String(x.ad) === String(a.ad) && (x.kat == null) === (a.kat == null); })[0] || null;
      if (v) { eskiZ.splice(eskiZ.indexOf(v), 1); const o = { ad: String(v.ad), konum: r6(+a.konum) }; if (a.kat != null) o.kat = +a.kat; zSon.push(o); }
      else zSon.push(a);
    });
    // kalan eski Z aksları: bağlı eleman yoksa düşer, varsa korunur (uyarı)
    eskiZ.forEach(function (a) {
      let b = null;
      try { b = A.bagliElemanlar(m, { yon: "z", ad: a.ad }); } catch (e) { b = null; }
      if (b && b.cubuklar.length + b.paneller.length + b.mesnetler.length + b.dugumler.length > 0) {
        const o = { ad: String(a.ad), konum: +a.konum };
        zSon.push(o);
        uy.push("Z aksı " + a.ad + " sihirbazda yok ama " + b.ozet + " ona bağlı; aks korundu.");
      }
    });
    const adlar = new Set();
    zSon.forEach(function (a) { if (adlar.has(a.ad)) a.ad = A.benzersizAd(a.ad, Array.from(adlar)); adlar.add(a.ad); });
    m.akslar.z = zSon.sort(function (p, q) { return p.konum - q.konum; });
    // kaldırılan katların aks–kat elemanları
    const katNo = new Set(zSon.filter(function (a) { return a.kat != null; }).map(function (a) { return +a.kat; }));
    let n = 0;
    ["kolonlar", "kirisler", "dosemeler"].forEach(function (k) {
      const once = liste(m, k).length;
      if (!once) return;
      m[k] = m[k].filter(function (x) { const kat = x.kat == null ? 1 : +x.kat; return katNo.has(kat) && (k !== "kolonlar" || katNo.has(kat - 1)); });
      n += once - m[k].length;
    });
    if (n) silinen.push({ yon: "z", ad: "kat", ozet: n + " aks–kat elemanı (kaldırılan katlarda)" });
    m.katlar = A.katlarTuret(m.akslar, katlar || m.katlar);
    const s = A.katlariSenkronla(m);
    m = s.model;
    return { model: m, silinen: silinen, uyarilar: uy.concat(s.uyarilar || []) };
  }
  /**
   * Sihirbazdan yeni model: kütüphane bölümleri (malzeme, kesit, duvar, yük durumları, deprem, temel, analiz) eski modelden;
   * eleman listeleri boş. sistem: "betonarme" | "celik".
   */
  function yeniModel(eski, akslar, katlar, sec) {
    sec = sec || {};
    const e = eski || {};
    const m = {
      tur: "bina", surum: 3, baslik: sec.baslik || "Yeni aks modeli", sistem: sec.sistem === "celik" ? "celik" : (sec.sistem === "betonarme" ? "betonarme" : (e.sistem || "celik")),
      birim: { kuvvet: "kN", uzunluk: "m" },
      akslar: kopya(akslar), katlar: kopya(katlar),
      malzemeler: {}, kesitler: {}, duvarlar: kopya(e.duvarlar || {}),
      kolonlar: [], kirisler: [], dosemeler: [], ek_yukler: [],
      dugumler: [], cubuklar: [], paneller: [], mesnetler: [], uretecler: [],
    };
    ["yuk_durumlari", "deprem", "temeller", "analiz", "kombinasyon_kumesi"].forEach(function (k) { if (e[k] != null) m[k] = kopya(e[k]); });
    if (m.sistem === e.sistem) { m.malzemeler = kopya(e.malzemeler || {}); m.kesitler = kopya(e.kesitler || {}); }     // aynı sistem: kesit ve malzemeler korunur
    if (m.temeller && Array.isArray(m.temeller.ozel)) m.temeller.ozel = [];
    if (m.sistem !== e.sistem) delete m.kombinasyon_kumesi;
    return m;
  }

  // ================================================================= serbest düğümleri aksa bağlama (§19: ek adım)
  /**
   * ModelOps.aksaBagla'dan sonra serbest kalan {no, X, Y, Z} düğümlerini iki aks kesişimi arasında bölme düğümüne çevirir
   * (bölme kaydının cubuk_i / cubuk_j uçları aks kesişimi REF'idir; arada çubuk olması gerekmez):
   *   1) yatay: düğümün Z'sinde bir Z aksı ve Y'sinde bir Y aksı varsa iki komşu X aksı arasında (ya da X aksı varsa iki Y aksı arasında);
   *   2) düşey: X ve Y aksları varsa iki komşu Z aksı arasında.
   * Hiçbiri tutmazsa düğüm "kalan" listesine girer (kullanıcıya "oraya aks ekleyin" denir). Yalnız GLOBAL akslar.
   */
  function serbestleriBagla(model) {
    const m = kopya(model), A = MA();
    const xs = aksListesi(m, "x"), ys = aksListesi(m, "y"), zs = aksListesi(m, "z");
    const bul = function (l, v) { return l.filter(function (a) { return Math.abs(a.konum - v) <= TOL; })[0] || null; };
    const arasi = function (l, v) {
      for (let i = 0; i + 1 < l.length; i++) if (l[i].konum < v - TOL && l[i + 1].konum > v + TOL) return [l[i], l[i + 1]];
      return null;
    };
    const kalan = [], baglanan = [];
    liste(m, "dugumler").forEach(function (d) {
      if (!d || d.tur || d.X == null || d.Y == null || d.Z == null) return;
      const P = [+d.X, +d.Y, +d.Z];
      const ax = bul(xs, P[0]), ay = bul(ys, P[1]), az = bul(zs, P[2]);
      let ri = null, rj = null, t = null;
      if (az && ay) { const a = arasi(xs, P[0]); if (a) { ri = { aks: [a[0].ad, ay.ad], z: az.ad }; rj = { aks: [a[1].ad, ay.ad], z: az.ad }; t = (P[0] - a[0].konum) / (a[1].konum - a[0].konum); } }
      if (!ri && az && ax) { const a = arasi(ys, P[1]); if (a) { ri = { aks: [ax.ad, a[0].ad], z: az.ad }; rj = { aks: [ax.ad, a[1].ad], z: az.ad }; t = (P[1] - a[0].konum) / (a[1].konum - a[0].konum); } }
      if (!ri && ax && ay) { const a = arasi(zs, P[2]); if (a) { ri = { aks: [ax.ad, ay.ad], z: a[0].ad }; rj = { aks: [ax.ad, ay.ad], z: a[1].ad }; t = (P[2] - a[0].konum) / (a[1].konum - a[0].konum); } }
      if (!ri) { kalan.push(+d.no); return; }
      delete d.X; delete d.Y; delete d.Z;
      d.tur = "bolme"; d.cubuk_i = ri; d.cubuk_j = rj; d.oran = r6(t);
      baglanan.push(+d.no);
    });
    // doğrulama: yeni bölme düğümleri eski konumunda mı (aks sistemi tutarlılığı)
    if (baglanan.length) { try { const cz = new A.Cozucu(m); baglanan.forEach(function (no) { cz.coz({ dugum: no }); }); } catch (e) { return { model: model, baglanan: [], kalan: kalan.concat(baglanan) }; } }
    return { model: m, baglanan: baglanan, kalan: kalan };
  }
  /** ModelOps işlem sonucu → aks sistemine bağlanmış model ve birleşik uyarılar. */
  function aksaBaglaHepsi(model) {
    const O = MO();
    let m = model, uy = [];
    try { const r = O.aksaBagla(m); m = r.model; uy = (r.uyarilar || []).filter(function (u) { return !/serbest koordinatlı kaldı/.test(u); }); } catch (e) { uy.push(e.message); }
    const s = serbestleriBagla(m);
    if (s.kalan.length) uy.push(s.kalan.length + " düğüm hiçbir aks kesişimine ya da iki aks kesişimi arasındaki doğruya düşmüyor (" + s.kalan.slice(0, 6).join(", ") + (s.kalan.length > 6 ? "…" : "") + "); oraya aks ekleyin.");
    return { model: s.model, uyarilar: uy, kalan: s.kalan };
  }

  // ================================================================= üreteçler için ek akslar ve parametreler
  /** Konumda aks yoksa ekler (ad: verilen ya da otomatik). Dönüş: {model, ad, eklendi}. */
  function aksSagla(model, yon, konum, ad) {
    const v = aksAdi(model, yon, konum);
    if (v != null) return { model: model, ad: v, eklendi: false };
    const p = { yon: yon, konum: r6(konum) };
    if (ad && !aksListesi(model, yon).some(function (a) { return a.ad === ad; })) p.ad = ad;
    const r = MA().aksEkle(model, p);
    return { model: r.model, ad: r.eklenen, eklendi: true };
  }
  /**
   * Beşik çerçeve planı. p = {acikliklar: [[xa, xb], ...] (kolon X aksları), y: [Y aks adları] (çerçeve aksları, en az 1),
   *   taban: Z aksı adı, sacak: kot (m, mutlak), mahya: kot (m, mutlak), sacakAd?, mahyaAd?, kesitler: {kolon, mertek}, vute?: {boy, yukseklik},
   *   asik?: {aralik, kesit}, panel?: true | {...}, mesnet: "ankastre" | "mafsal" | "yok"}
   * Eksik saçak/mahya Z aksları ve açıklık ortasındaki mahya X aksları eklenir. Dönüş: {model, parametreler: [besikCerceveUret girdisi], eklenen: [metin], uyarilar}
   */
  function besikPlan(bina, p) {
    let m = kopya(bina);
    const eklenen = [], uy = [];
    const zt = aksListesi(m, "z").filter(function (a) { return a.ad === String(p.taban); })[0];
    if (!zt) throw new Error("Taban Z aksı “" + p.taban + "” yok.");
    const sacak = sayi(p.sacak), mahya = sayi(p.mahya);
    if (sacak == null || mahya == null || !(sacak > zt.konum) || !(mahya > sacak)) throw new Error("Saçak kotu tabandan, mahya kotu saçaktan yüksek olmalı.");
    let r = aksSagla(m, "z", sacak, p.sacakAd || "Saçak"); m = r.model; if (r.eklendi) eklenen.push("Z aksı " + r.ad + " (" + fmt(sacak) + " m)");
    r = aksSagla(m, "z", mahya, p.mahyaAd || "Mahya"); m = r.model; if (r.eklendi) eklenen.push("Z aksı " + r.ad + " (" + fmt(mahya) + " m)");
    const xs = aksListesi(m, "x"), xk = function (ad) { const a = xs.filter(function (x) { return x.ad === String(ad); })[0]; if (!a) throw new Error("X aksı “" + ad + "” yok."); return a.konum; };
    const ys = aksListesi(m, "y").filter(function (a) { return (p.y || []).map(String).indexOf(a.ad) >= 0; });
    if (!ys.length) throw new Error("En az bir çerçeve (Y) aksı seçin.");
    if (!(p.acikliklar || []).length) throw new Error("En az bir açıklık seçin.");
    (p.acikliklar || []).forEach(function (a) {
      const orta = (xk(a[0]) + xk(a[1])) / 2;
      const q = aksSagla(m, "x", orta, null); m = q.model;
      if (q.eklendi) eklenen.push("mahya X aksı " + q.ad + " (" + fmt(orta) + " m)");
    });
    const araliklar = []; for (let i = 1; i < ys.length; i++) araliklar.push(r6(ys[i].konum - ys[i - 1].konum));
    const esit = araliklar.every(function (a) { return Math.abs(a - araliklar[0]) < 1e-6; });
    const ortak = { sacak: r6(sacak - zt.konum), mahya: r6(mahya - zt.konum), kesitler: kopya(p.kesitler || {}), mesnet: p.mesnet || "ankastre", yon: [0, 1, 0] };
    if (p.vute && +p.vute.boy > 0) ortak.vute = { boy: +p.vute.boy, yukseklik: +p.vute.yukseklik || 0 };
    const parametreler = [];
    (p.acikliklar || []).forEach(function (a) {
      if (esit || ys.length === 1) {
        const o = Object.assign(kopya(ortak), { taban1: { aks: [String(a[0]), ys[0].ad], z: zt.ad }, taban2: { aks: [String(a[1]), ys[0].ad], z: zt.ad }, adet: ys.length, aralik: araliklar[0] || 0 });
        if (p.asik && ys.length >= 2) o.asik = { aralik: +p.asik.aralik, kesit: p.asik.kesit, uclar: p.asik.uclar !== false };
        if (p.panel && ys.length >= 2) o.panel = p.panel === true ? { tur: "cati", kalinlik: 0, g: 0.25, q: 0.4, kar: true, dagitim: p.asik ? "tek-13" : "tek-24" } : kopya(p.panel);
        parametreler.push(o);
      } else {
        ys.forEach(function (y) { parametreler.push(Object.assign(kopya(ortak), { taban1: { aks: [String(a[0]), y.ad], z: zt.ad }, taban2: { aks: [String(a[1]), y.ad], z: zt.ad }, adet: 1 })); });
      }
    });
    if (!esit && ys.length > 1 && (p.asik || p.panel)) uy.push("Çerçeve aks aralıkları eşit değil: aşık ve çatı paneli üretilmedi; Aşık aracıyla mertekleri seçerek ekleyin.");
    return { model: m, parametreler: parametreler, eklenen: eklenen, uyarilar: uy };
  }
  /**
   * Makas planı. p = {tip, bas: REF, son: REF (aynı Z aksında iki kesişim), yukseklik (m; beşik tiplerde mahya yüksekliği), goz, kesitler, uc_yukseklik?, mafsalli_govde?}
   * Eksik üst başlık / mahya Z aksı ve (beşik tiplerde) açıklık ortası aksı eklenir. Dönüş: {model, parametre, eklenen}
   */
  function makasPlan(bina, p) {
    let m = kopya(bina);
    const A = MA(), eklenen = [];
    const Pb = A.refKoordinat(m, p.bas), Ps = A.refKoordinat(m, p.son);
    if (Math.abs(Pb[2] - Ps[2]) > TOL) throw new Error("Makas mesnetleri aynı kotta (aynı Z aksında) olmalı.");
    const h = sayi(p.yukseklik);
    if (!(h > 0)) throw new Error("Makas yüksekliği pozitif olmalı (m).");
    const tip = String(p.tip || "pratt").toLowerCase();
    const besik = /besik|fink/.test(tip);
    let r = aksSagla(m, "z", Pb[2] + h, besik ? "Mahya" : "Makas üst"); m = r.model;
    if (r.eklendi) eklenen.push("Z aksı " + r.ad + " (" + fmt(Pb[2] + h) + " m)");
    if (besik) {
      const orta = [(Pb[0] + Ps[0]) / 2, (Pb[1] + Ps[1]) / 2];
      if (Math.abs(Pb[1] - Ps[1]) < TOL) { r = aksSagla(m, "x", orta[0]); m = r.model; if (r.eklendi) eklenen.push("mahya X aksı " + r.ad); }
      else if (Math.abs(Pb[0] - Ps[0]) < TOL) { r = aksSagla(m, "y", orta[1]); m = r.model; if (r.eklendi) eklenen.push("mahya Y aksı " + r.ad); }
    }
    const par = { tip: tip, bas: kopya(p.bas), son: kopya(p.son), goz: Math.round(+p.goz || 6), kesitler: kopya(p.kesitler || {}), mafsalli_govde: p.mafsalli_govde !== false };
    if (besik) { par.yukseklik = h; if (+p.uc_yukseklik > 0) par.uc_yukseklik = +p.uc_yukseklik; } else par.yukseklik = h;
    return { model: m, parametre: par, eklenen: eklenen };
  }
  /**
   * Kren yolu planı: kren kotunda Z aksı (yoksa "Kren") ve hat aksları üzerindeki kolon çubukları.
   * p = {hatlar: [X aks adı, X aks adı] (ya da Y), yon: "x" | "y" (hat aksının yönü), y: [aks adları] (hat boyunca kolon aksları), kot, konsol_boy, kesitler, kren}
   * Dönüş: {model, kolonlar: [[çubuk no, ...], [...]], eklenen, uyarilar}
   */
  function krenPlan(bina, p) {
    let m = kopya(bina);
    const A = MA(), eklenen = [], uy = [];
    const kot = sayi(p.kot);
    if (kot == null) throw new Error("Kren kotu sayı olmalı.");
    const r = aksSagla(m, "z", kot, "Kren"); m = r.model;
    if (r.eklendi) eklenen.push("Z aksı " + r.ad + " (" + fmt(kot) + " m)");
    const yon = p.yon === "y" ? "y" : "x";
    const cz = new A.Cozucu(m);
    const kolonlar = (p.hatlar || []).map(function (hat) {
      const l = [];
      liste(m, "cubuklar").forEach(function (c) {
        if (!c || (c.tur && c.tur !== "kolon")) return;
        let Pi, Pj;
        try { Pi = cz.coz(c.i); Pj = cz.coz(c.j); } catch (e) { return; }
        if (Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1]) > TOL) return;
        const lo = Math.min(Pi[2], Pj[2]), hi = Math.max(Pi[2], Pj[2]);
        if (kot < lo - TOL || kot > hi + TOL) return;
        const ax = aksAdi(m, yon, yon === "x" ? Pi[0] : Pi[1]), ay = aksAdi(m, yon === "x" ? "y" : "x", yon === "x" ? Pi[1] : Pi[0]);
        if (ax !== String(hat) || (Array.isArray(p.y) && p.y.length && p.y.map(String).indexOf(ay) < 0)) return;
        l.push(+c.no);
      });
      if (l.length < 2) uy.push(hat + " aksında kren kotunu kesen en az iki kolon çubuğu yok.");
      return l;
    }).filter(function (l) { return l.length >= 2; });
    return { model: m, kolonlar: kolonlar, eklenen: eklenen, uyarilar: uy };
  }

  // ================================================================= ön ayarlar, mesnet, yük
  const MAFSAL_ON_AYAR = Object.freeze({
    "iki-uc": { ad: "İki uç mafsallı (My, Mz)", i: ["My", "Mz"], j: ["My", "Mz"] },
    i: { ad: "Yalnız i ucu mafsallı", i: ["My", "Mz"], j: [] },
    j: { ad: "Yalnız j ucu mafsallı", i: [], j: ["My", "Mz"] },
    kafes: { ad: "Kafes çubuğu (T bir uçta + iki uç mafsal)", i: ["T", "My", "Mz"], j: ["My", "Mz"] },
    rijit: { ad: "Rijit (serbestlik yok)", i: [], j: [] },
  });
  const MESNET_ON_AYAR = Object.freeze({
    ankastre: { ad: "Ankastre", ux: true, uy: true, uz: true, rx: true, ry: true, rz: true },
    mafsal: { ad: "Sabit mafsal", ux: true, uy: true, uz: true, rx: false, ry: false, rz: false },
    "kayici-x": { ad: "Kayıcı (X serbest)", ux: false, uy: true, uz: true, rx: false, ry: false, rz: false },
    "kayici-y": { ad: "Kayıcı (Y serbest)", ux: true, uy: false, uz: true, rx: false, ry: false, rz: false },
    "kayici-xy": { ad: "Kayıcı (X, Y serbest)", ux: false, uy: false, uz: true, rx: false, ry: false, rz: false },
    kaldir: { ad: "Mesnedi kaldır" },
  });
  /** Düğüme mesnet ata / kaldır (aynı düğümdeki kayıt değişir). Dönüş: {model, eylem: "eklendi"|"degisti"|"kaldirildi"|"yok"} */
  function mesnetAta(bina, ref, onAyar) {
    const m = kopya(bina), A = MA();
    if (!Array.isArray(m.mesnetler)) m.mesnetler = [];
    const k = A.refAnahtar(m, ref);
    let P = null; try { P = A.refKoordinat(m, ref); } catch (e) { P = null; }
    const i = m.mesnetler.findIndex(function (s) {
      if (!s) return false;
      if (A.refAnahtar(m, s.dugum) === k) return true;
      if (!P) return false;
      try { return uzaklik(A.refKoordinat(m, s.dugum), P) < TOL; } catch (e) { return false; }
    });
    const o = MESNET_ON_AYAR[onAyar];
    if (!o) throw new Error("Mesnet türü tanımsız: " + onAyar);
    if (onAyar === "kaldir") { if (i < 0) return { model: m, eylem: "yok" }; m.mesnetler.splice(i, 1); return { model: m, eylem: "kaldirildi" }; }
    const kayit = { dugum: kopya(ref) };
    ["ux", "uy", "uz", "rx", "ry", "rz"].forEach(function (a) { kayit[a] = !!o[a]; });
    if (i >= 0) { m.mesnetler[i] = kayit; return { model: m, eylem: "degisti" }; }
    m.mesnetler.push(kayit);
    return { model: m, eylem: "eklendi" };
  }
  /**
   * Ek yük kaydı ekler (motor şeması §12.2; durum G, Q, S).
   * hedef: {tur: "cubuk", no} | {tur: "panel", no} | {tur: "dugum", ref}
   * yuk: cubuk → {durum, yon ("Z" | "X" | "Y" | "x′" | "y′" | "z′"), q1, q2?, izdusum?} yayılı (kN/m, yön boyunca; aşağı yük Z'de negatif) ya da {durum, yon, P, x, oransal?} tekil;
   *      panel → {durum, g?, q?} (kN/m²); dugum → {durum, FX?, FY?, FZ?, MX?, MY?, MZ?} (kN, kN·m)
   */
  function yukEkle(bina, hedef, yuk) {
    const m = kopya(bina);
    if (!Array.isArray(m.ek_yukler)) m.ek_yukler = [];
    const durum = String((yuk && yuk.durum) || "G").toUpperCase();
    if (["G", "Q", "S"].indexOf(durum) < 0) throw new Error("Ek yük durumu G, Q ya da S olmalı (rüzgâr ve deprem otomatik üretilir).");
    let r;
    if (hedef.tur === "cubuk") {
      const yon = String(yuk.yon || "Z");
      if (yuk.P != null) {
        const P = sayi(yuk.P), x = sayi(yuk.x);
        if (P == null || x == null) throw new Error("Tekil yük için P (kN) ve x (m ya da oran) sayı olmalı.");
        r = { tur: "cubuk", cubuk: +hedef.no, durum: durum, yon: yon, P: P, x: x, oransal: !!yuk.oransal };
      } else {
        const q1 = sayi(yuk.q1), q2 = yuk.q2 == null || yuk.q2 === "" ? q1 : sayi(yuk.q2);
        if (q1 == null || q2 == null) throw new Error("Yayılı yük q (kN/m) sayı olmalı.");
        r = { tur: "cubuk", cubuk: +hedef.no, durum: durum, yon: yon, q1: q1, q2: q2, x1: 0, x2: null, oransal: false, izdusum: !!yuk.izdusum };
      }
    } else if (hedef.tur === "panel") {
      const g = sayi(yuk.g) || 0, q = sayi(yuk.q) || 0;
      if (!g && !q) throw new Error("Panel yükü için g ya da q (kN/m²) girin.");
      r = { tur: "panel", panel: +hedef.no, durum: durum };
      if (g) r.g = g;
      if (q) r.q = q;
    } else if (hedef.tur === "dugum") {
      r = { tur: "dugum", dugum: kopya(hedef.ref), durum: durum };
      let var_ = false;
      ["FX", "FY", "FZ", "MX", "MY", "MZ"].forEach(function (a) { const v = sayi(yuk[a]); if (v) { r[a] = v; var_ = true; } });
      if (!var_) throw new Error("Düğüm yükü için en az bir bileşen (FX, FY, FZ, MX, MY, MZ) girin.");
    } else throw new Error("Yük hedefi çubuk, panel ya da düğüm olmalı.");
    m.ek_yukler.push(r);
    return { model: m, kayit: r };
  }

  // ================================================================= seçim
  /** Seçimden çubuk/panel numaraları ve aks–kat elemanları. */
  function secimAyir(secim) {
    const r = { cubuklar: [], paneller: [], aksKat: [], dugumler: [] };
    (secim || []).forEach(function (s) {
      if (s.tur === "cubuk") r.cubuklar.push(+s.no);
      else if (s.tur === "panel") r.paneller.push(+s.no);
      else if (s.tur === "dugum") r.dugumler.push(+s.no);
      else if (s.tur === "kolon" || s.tur === "kiris" || s.tur === "doseme") r.aksKat.push({ tur: s.tur, no: +s.no });
    });
    return r;
  }
  /** Genelleştirme sonrası seçim: aks–kat kolon/kiriş/döşeme → kaynak.aks_kat'tan üretilen çubuk/panel(ler). */
  function genelSecim(yeni, secim) {
    const out = [];
    (secim || []).forEach(function (s) {
      if (s.tur === "kolon" || s.tur === "kiris") {
        liste(yeni, "cubuklar").forEach(function (c) { if (c && c.kaynak && c.kaynak.aks_kat === s.tur && +c.kaynak.no === +s.no) out.push({ tur: "cubuk", no: +c.no }); });
      } else if (s.tur === "doseme") {
        liste(yeni, "paneller").forEach(function (p) { if (p && p.kaynak && p.kaynak.aks_kat === "doseme" && +p.kaynak.no === +s.no) out.push({ tur: "panel", no: +p.no }); });
      } else out.push({ tur: s.tur, no: s.no });
    });
    return out;
  }
  /** Çubuğun iç noktalarına düşen aks kesişimleri (Böl → "Aks kesişimlerinde"): [{ref, P, t, ad}] t sıralı. */
  function bolmeNoktalari(bina, cubukNo) {
    const A = MA();
    const c = liste(bina, "cubuklar").filter(function (x) { return x && +x.no === +cubukNo; })[0];
    if (!c) return [];
    let Pi, Pj;
    try { Pi = A.refKoordinat(bina, c.i); Pj = A.refKoordinat(bina, c.j); } catch (e) { return []; }
    const L = uzaklik(Pi, Pj);
    if (L < TOL) return [];
    const d = [(Pj[0] - Pi[0]) / L, (Pj[1] - Pi[1]) / L, (Pj[2] - Pi[2]) / L];
    const out = [];
    A.kesisimler(bina, { tur: "3b" }).forEach(function (k) {
      const v = [k.P[0] - Pi[0], k.P[1] - Pi[1], k.P[2] - Pi[2]], t = v[0] * d[0] + v[1] * d[1] + v[2] * d[2];
      if (t <= TOL || t >= L - TOL) return;
      if (Math.hypot(v[0] - t * d[0], v[1] - t * d[1], v[2] - t * d[2]) > TOL) return;
      out.push({ ref: k.ref, P: k.P, t: r6(t / L), ad: (k.sistem && k.sistem !== "GLOBAL" ? k.sistem + ": " : "") + k.adlar[0] + k.adlar[1] + " / " + k.adlar[2] });
    });
    return out.sort(function (a, b) { return a.t - b.t; });
  }

  // ================================================================= ekran ↔ düzlem, aks ekleme
  /**
   * Ekran noktası → bina noktası (düzlem: {i: 0|1|2, v} sabit koordinat). P(X, Y, Z) → [x, y] doğrusal (eşeksenli) izdüşüm.
   * Düzleme dik bakılıyorsa (iki taban vektörü ekranda paralel) null.
   */
  function ekrandanDuzleme(P, duzlem, nokta) {
    const i = duzlem.i, v = duzlem.v, eks = [0, 1, 2].filter(function (k) { return k !== i; });
    const nk = function (a, b) { const q = [0, 0, 0]; q[i] = v; q[eks[0]] = a; q[eks[1]] = b; return q; };
    const o = P.apply(null, nk(0, 0)), u = P.apply(null, nk(1, 0)), w = P.apply(null, nk(0, 1));
    const ux = u[0] - o[0], uy = u[1] - o[1], wx = w[0] - o[0], wy = w[1] - o[1];
    const det = ux * wy - uy * wx;
    if (Math.abs(det) < 1e-9 * (Math.hypot(ux, uy) * Math.hypot(wx, wy) + 1e-30)) return null;
    const dx = nokta[0] - o[0], dy = nokta[1] - o[1];
    const a = (dx * wy - dy * wx) / det, b = (ux * dy - uy * dx) / det;
    return nk(a, b);
  }
  /** Aks ekle: konum iki aksın arasındaysa ortasına ({arasina}), dışındaysa yakalama adımına yuvarlanmış konuma. */
  function aksEkleKonumu(bina, yon, deger) {
    const l = aksListesi(bina, yon);
    for (let i = 0; i + 1 < l.length; i++) if (deger > l[i].konum + TOL && deger < l[i + 1].konum - TOL) return { arasina: [l[i].ad, l[i + 1].ad], konum: r6((l[i].konum + l[i + 1].konum) / 2) };
    const adim = yon === "teta" ? 0.5 : 0.05;
    return { konum: r6(Math.round(deger / adim) * adim) };
  }

  // ================================================================= özet
  /** ModelOps / MatrisAks rapor özeti: "2 çubuk, 1 panel eklendi; 1 çubuk silindi" (+ uyarılar ayrı). */
  function ozet(r) {
    if (!r) return "";
    const p = [];
    const say = function (o, k) { return o && Array.isArray(o[k]) ? o[k].length : 0; };
    const ek = [], si = [], de = [];
    [["cubuklar", "çubuk"], ["paneller", "panel"], ["dugumler", "düğüm"]].forEach(function (x) {
      if (say(r.eklenen, x[0])) ek.push(say(r.eklenen, x[0]) + " " + x[1]);
      if (say(r.silinen, x[0])) si.push(say(r.silinen, x[0]) + " " + x[1]);
      if (say(r.degisen, x[0]) && x[0] !== "dugumler") de.push(say(r.degisen, x[0]) + " " + x[1]);
    });
    [["kolonlar", "kolon"], ["kirisler", "kiriş"], ["dosemeler", "döşeme"]].forEach(function (x) { if (say(r.silinen, x[0])) si.push(say(r.silinen, x[0]) + " " + x[1]); });
    if (ek.length) p.push(ek.join(", ") + " eklendi");
    if (de.length) p.push(de.join(", ") + " değişti");
    if (si.length) p.push(si.join(", ") + " kaldırıldı");
    return p.join("; ");
  }
  /** Çapraz tipine göre varsayılan seçenekler: dışmerkezde bağ kirişi e ≈ 0,15·L, diz çaprazında a ≈ 0,2·min(H, L). */
  function caprazSecenek(tip, goz, ek) {
    const s = Object.assign({ mafsalli_uclar: true }, ek || {});
    const P = goz && goz.P;
    if (P && P.length === 4) {
      const L = Math.max(uzaklik(P[0], P[1]), uzaklik(P[2], P[3])), H = Math.max(uzaklik(P[1], P[2]), uzaklik(P[3], P[0]));
      if ((tip === "dismerkez-tek" || tip === "dismerkez-ters-V") && s.e == null) s.e = r6(Math.round(Math.max(0.3, 0.15 * L) * 20) / 20);
      if (tip === "diz" && s.a == null) s.a = r6(Math.round(Math.max(0.3, 0.2 * Math.min(H, L)) * 20) / 20);
    }
    return s;
  }

  const SAF = {
    TOL: TOL, MAFSAL_ON_AYAR: MAFSAL_ON_AYAR, MESNET_ON_AYAR: MESNET_ON_AYAR,
    sayi: sayi, fmt: fmt, fmtK: fmtK, aksListesi: aksListesi, aksAdi: aksAdi,
    cubukTuru: cubukTuru, kolonCiftleri: kolonCiftleri, mevcutCubuk: mevcutCubuk, aksKatCakisan: aksKatCakisan,
    aksSihirbazUygula: aksSihirbazUygula, yeniModel: yeniModel, serbestleriBagla: serbestleriBagla, aksaBaglaHepsi: aksaBaglaHepsi,
    aksSagla: aksSagla, besikPlan: besikPlan, makasPlan: makasPlan, krenPlan: krenPlan,
    mesnetAta: mesnetAta, yukEkle: yukEkle, secimAyir: secimAyir, genelSecim: genelSecim, bolmeNoktalari: bolmeNoktalari,
    ekrandanDuzleme: ekrandanDuzleme, aksEkleKonumu: aksEkleKonumu, ozet: ozet, caprazSecenek: caprazSecenek,
  };

  // =================================================================================================================
  // ARAYÜZ (tarayıcı). MatrisBina hazır olunca kur(MB). Bu bölüm DOM'a bağlıdır; node testleri yalnız SAF'ı çalıştırır.
  // =================================================================================================================
  let kuruldu = false;
  function otomatikKur() {
    const dene = function () {
      const MB = window.MatrisBina;
      if (kuruldu || !MB) return false;
      if (!MB.hazir()) return false;
      kuruldu = true;
      try { kur(MB); } catch (e) { setTimeout(function () { throw e; }, 0); }
      return true;
    };
    if (dene()) return;
    window.addEventListener("matris-bina-hazir", function () { dene(); });
    // bina.js sonra yüklenirse (betik sırası) olay yine gelir; güvenlik için kısa yoklama
    let n = 0;
    const z = setInterval(function () { if (dene() || ++n > 600) clearInterval(z); }, 500);
  }

  function kacis(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function r1(v) { return Math.round(v * 10) / 10; }
  function secenekHtml(l, sec) { return l.map(function (o) { return '<option value="' + kacis(o[0]) + '"' + (String(o[0]) === String(sec) ? " selected" : "") + ">" + kacis(o[1]) + "</option>"; }).join(""); }
  function alan(etiket, ic, sinif) { return '<label class="bn-alan' + (sinif ? " " + sinif : "") + '"><span>' + kacis(etiket) + "</span>" + ic + "</label>"; }
  function girdi(ad, deger, ek) { return '<input class="girdi" data-a="' + ad + '" value="' + kacis(deger == null ? "" : deger) + '"' + (ek || "") + ">"; }
  function onay(ad, etiket, acik) { return '<label class="bn-onay"><input type="checkbox" data-a="' + ad + '"' + (acik ? " checked" : "") + "> " + kacis(etiket) + "</label>"; }
  function sec(ad, l, s) { return '<select class="girdi" data-a="' + ad + '">' + secenekHtml(l, s) + "</select>"; }
  function oku(kap) {
    const o = {};
    kap.querySelectorAll("[data-a]").forEach(function (el) { o[el.getAttribute("data-a")] = el.type === "checkbox" ? el.checked : el.value; });
    return o;
  }

  const KESIT_VARS = {
    celik: { kolon: ["HEA300", "HEA 300"], kiris: ["IPE300", "IPE 300"], capraz: ["HEA200", "HEA 200"], asik: ["IPE200", "IPE 200"], "makas-ust": ["HEA200", "HEA 200"],
      "makas-alt": ["HEA200", "HEA 200"], "makas-dikme": ["IPE200", "IPE 200"], "makas-diyagonal": ["IPE200", "IPE 200"], kren: ["HEB400", "HEB 400"], bag: ["IPE300", "IPE 300"], diger: ["IPE240", "IPE 240"] },
    betonarme: { kolon: ["S40x40", [0.4, 0.4]], kiris: ["K25x50", [0.25, 0.5]], diger: ["K25x50", [0.25, 0.5]] },
  };
  /** Türün varsayılan kesiti: modelde o türde en çok kullanılan; yoksa sisteme göre katalog kesiti (modele eklenir). */
  function kesitSagla(m, tur) {
    const say = {};
    liste(m, "cubuklar").forEach(function (c) { if (c && (c.tur || "diger") === tur && c.kesit && m.kesitler && m.kesitler[c.kesit]) say[c.kesit] = (say[c.kesit] || 0) + 1; });
    if (tur === "kolon") liste(m, "kolonlar").forEach(function (c) { if (c.kesit && m.kesitler[c.kesit]) say[c.kesit] = (say[c.kesit] || 0) + 1; });
    if (tur === "kiris") liste(m, "kirisler").forEach(function (c) { if (c.kesit && m.kesitler[c.kesit]) say[c.kesit] = (say[c.kesit] || 0) + 1; });
    const enCok = Object.keys(say).sort(function (a, b) { return say[b] - say[a]; })[0];
    if (enCok) return enCok;
    const celik = m.sistem === "celik", t = (celik ? KESIT_VARS.celik : KESIT_VARS.betonarme)[tur] || (celik ? KESIT_VARS.celik.diger : KESIT_VARS.betonarme.diger);
    if (!m.kesitler) m.kesitler = {};
    if (!m.kesitler[t[0]]) {
      const malz = Object.keys(m.malzemeler || {});
      if (celik) m.kesitler[t[0]] = { tip: "profil", profil: t[1], malzeme: malz.filter(function (k) { return /^S\d/.test(k); })[0] || "S275" };
      else m.kesitler[t[0]] = { tip: "dikdortgen", b: t[1][0], h: t[1][1], malzeme: malz.filter(function (k) { return /^C\d/.test(k); })[0] || "C30", donati: "B420C", pas: 0.03 };
      if (!m.malzemeler) m.malzemeler = {};
      if (celik && !m.malzemeler[m.kesitler[t[0]].malzeme]) m.malzemeler[m.kesitler[t[0]].malzeme] = { kutuphane: m.kesitler[t[0]].malzeme };
    }
    return t[0];
  }

  function kur(MB) {
    const MAk = window.MatrisAks, MOp = window.ModelOps, OL = window.MatrisOlcum, MAr = window.MatrisArac;
    if (!MAk || !MOp) return;
    const svg = MB.sahne();
    const S = { capraz: "X", panel: "doseme", mesnet: "ankastre", yuk: "G", aksYon: "x", zincir: null, ilk: null, yakalanan: null, parca: null, goz: null,
      surukle: null, seciliAks: null, aksOnizleme: null, sonUyari: "", ipucuEk: "", yapisik: true };
    const B = function () { return MB.bina(); };
    const bg = function () { return MB.izdusum(); };
    const px = function () { return MB.pxOlcek() || 1; };
    const toast = function (m) { MB.toast(m); };

    // ---------------------------------------------------------------- düzlem ve yakalama
    function duzlem() { return MB.duzlem() || { tur: "3b" }; }
    function duzlemSuzgeci() {
      const g = duzlem(), b = B();
      const k = function (yon, ad) { const a = aksListesi(b, yon).filter(function (x) { return x.ad === String(ad); })[0]; return a ? a.konum : null; };
      if (g.tur === "plan" && g.z != null) { const v = k("z", g.z); return v == null ? null : { Z: v, tol: 0.002 }; }
      if (g.tur === "cephe") { if (g.y != null) { const v = k("y", g.y); return v == null ? null : { Y: v, tol: 0.002 }; } if (g.x != null) { const v = k("x", g.x); return v == null ? null : { X: v, tol: 0.002 }; } }
      return null;
    }
    function duzlemSpek() {      // ekran → düzlem dönüşümü için {i, v}
      const s = duzlemSuzgeci();
      if (s && s.Z != null) return { i: 2, v: s.Z };
      if (s && s.Y != null) return { i: 1, v: s.Y };
      if (s && s.X != null) return { i: 0, v: s.X };
      const g = duzlem(), z = aksListesi(B(), "z").filter(function (a) { return a.ad === String(g.z); })[0];
      return { i: 2, v: z ? z.konum : 0 };
    }
    function yakala(p, ek) {
      const b = bg();
      if (!b || !p || !OL) return null;
      const s = Object.assign({ kip: "cizim", cevir: b.P3, tol: 16 * px(), duzlem: duzlemSuzgeci() }, ek || {});
      try { return OL.yakala(p, MB.geometri(), s); } catch (e) { return null; }
    }
    function parcaBul(p, suzgec) {
      const b = bg();
      if (!b || !p) return null;
      try {
        const l = MAk.aksParcalari(B(), duzlem()).filter(suzgec || function () { return true; });
        let en = null, ed = 12 * px();
        l.forEach(function (q) {
          const a = b.P(q.Pi[0], q.Pi[1], q.Pi[2]), c = b.P(q.Pj[0], q.Pj[1], q.Pj[2]);
          const dx = c[0] - a[0], dy = c[1] - a[1], L2 = dx * dx + dy * dy;
          let t = L2 > 0 ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2 : 0;
          if (t < 0.06 || t > 0.94) return;
          const d = Math.hypot(a[0] + dx * t - p[0], a[1] + dy * t - p[1]);
          if (d <= ed) { ed = d; en = q; }
        });
        return en;
      } catch (e) { return null; }
    }
    function gozBul(p) {
      const b = bg();
      if (!b || !p) return null;
      try { return MAk.gozBul(B(), duzlem(), p, { izdusum: b.P }); } catch (e) { return null; }
    }
    function kesisimBul(p) {
      const b = bg();
      if (!b || !p) return null;
      try { return MAk.enYakinKesisim(B(), duzlem(), p, { izdusum: b.P, tol: 16 * px() }); } catch (e) { return null; }
    }
    const dusey = function (q) { return Math.hypot(q.Pj[0] - q.Pi[0], q.Pj[1] - q.Pi[1]) < TOL; };
    const yatay = function (q) { return Math.abs(q.Pj[2] - q.Pi[2]) < TOL; };

    // ---------------------------------------------------------------- model işlemi uygula (tek geri al yığını)
    function hata(e) { toast((e && e.message) || String(e)); }
    /** fn(model) → ModelOps raporu; aks sistemine bağlar, binaAyarla ile uygular. sec: {bagla, secim(r, m), sessiz} */
    function uygula(fn, etiket, sc) {
      sc = sc || {};
      let r;
      try { r = fn(B()); } catch (e) { hata(e); return null; }
      if (!r || !r.model) return null;
      if (r.reddedildi) { S.sonUyari = (r.uyarilar || []).join(" "); toast(S.sonUyari || "İşlem uygulanmadı."); MB.ipucuYenile(); return null; }
      let m = r.model, uy = (r.uyarilar || []).slice();
      if (sc.bagla !== false) { try { const b = aksaBaglaHepsi(m); m = b.model; uy = uy.concat(b.uyarilar); } catch (e) { uy.push(e.message); } }
      const oz = ozet(r);
      S.sonUyari = uy.join(" ");
      const mesaj = (etiket || "") + (oz ? (etiket ? ": " : "") + oz : "") + (uy.length ? " — ⚠ " + uy.join(" ") : "");
      try { MB.binaAyarla(m, { etiket: mesaj || etiket || "Model güncellendi.", secim: sc.secim ? sc.secim(r, m) : undefined, sessiz: !!sc.sessiz && !uy.length }); }
      catch (e) { hata(e); return null; }
      MB.ipucuYenile();
      return r;
    }
    /** Seçim üzerinde işlem: aks–kat elemanları seçiliyse önce genelleştirilir (kullanıcıya bildirilir). fn(model, ayrik) → rapor */
    function secimli(etiket, fn, sc) {
      sc = sc || {};
      const secim = MB.secim();
      let ay = secimAyir(secim), m = B(), not = null;
      if (ay.aksKat.length) {
        try { const g = MOp.genellestir(m); m = g.model; not = "Aks–kat modeli genelleştirildi (" + (g.uyarilar || []).join(" ").replace(/^Aks–kat modeli genelleştirildi:\s*/, "") + ")."; ay = secimAyir(genelSecim(m, secim)); }
        catch (e) { hata(e); return null; }
      }
      if (!ay.cubuklar.length && !(sc.panel && ay.paneller.length)) { toast(sc.bos || "Önce çubuk seçin (Seç aracıyla dokunun; çoklu seçim için Shift)."); return null; }
      return uygula(function () { const r = fn(m, ay); if (not && r) r.uyarilar = [not].concat(r.uyarilar || []); return r; }, etiket, sc);
    }
    function cubukSecimiVar() { return MB.secim().some(function (s) { return s.tur === "cubuk" || s.tur === "kolon" || s.tur === "kiris"; }); }

    // ---------------------------------------------------------------- REF hazırla: çubuk kesişimi → iki çubuğu kesişimde böl
    function refHazirla(m, y) {
      if (!y || !y.ref) throw new Error("Yakalanacak nokta yok — aks kesişimine, düğüme ya da çubuk kesişimine dokunun.");
      if (y.ref.tur !== "kesisim") return { model: m, ref: y.ref };
      let mm = m;
      const cub = (y.cubuklar || []).map(String);
      if (cub.some(function (k) { return /^(kolon|kiris):/.test(k); })) mm = MOp.genellestir(mm).model;
      const nolar = [];
      const cz = new MAk.Cozucu(mm);
      liste(mm, "cubuklar").forEach(function (c) {
        let Pi, Pj; try { Pi = cz.coz(c.i); Pj = cz.coz(c.j); } catch (e) { return; }
        const L = uzaklik(Pi, Pj), t = ((y.P[0] - Pi[0]) * (Pj[0] - Pi[0]) + (y.P[1] - Pi[1]) * (Pj[1] - Pi[1]) + (y.P[2] - Pi[2]) * (Pj[2] - Pi[2])) / (L * L);
        const Q = [Pi[0] + (Pj[0] - Pi[0]) * t, Pi[1] + (Pj[1] - Pi[1]) * t, Pi[2] + (Pj[2] - Pi[2]) * t];
        if (t > 0 && t < 1 && uzaklik(Q, y.P) < TOL) nolar.push(+c.no);
      });
      if (nolar.length >= 2) mm = MOp.kesisimlerdeBol(mm, nolar).model;
      const aksRef = MAk.koordinattanRef(mm, y.P, { tol: TOL });
      if (aksRef) return { model: mm, ref: aksRef };
      const no = MOp.dugumBul(mm, y.P[0], y.P[1], y.P[2]);
      if (no == null || !(no >= 100001 && no < 800001)) throw new Error("Çubuk kesişiminde düğüm oluşturulamadı.");
      return { model: mm, ref: { dugum: no } };
    }
    /** İki nokta arasına çubuk (tür verilmezse geometriden). Aynı iki nokta arasında çubuk varsa kaldırır (sil: true ise). */
    function cubukCiz(yi, yj, tur, sc) {
      sc = sc || {};
      return uygula(function (m0) {
        let h = refHazirla(m0, yi), m = h.model, ri = h.ref;
        h = refHazirla(m, yj); m = h.model; const rj = h.ref;
        const Pi = MAk.refKoordinat(m, ri), Pj = MAk.refKoordinat(m, rj);
        if (uzaklik(Pi, Pj) < TOL) throw new Error("İki uç aynı nokta; çubuk çizilmedi.");
        const t = tur || cubukTuru(Pi, Pj);
        const var_ = mevcutCubuk(m, ri, rj);
        if (var_ != null) { if (sc.kaldir) return MOp.cubukSil(m, [var_]); throw new Error("Bu iki nokta arasında çubuk " + var_ + " zaten var."); }
        const c = aksKatCakisan(MB.geometri(), Pi, Pj);
        if (c) throw new Error("Burada aks–kat " + (c.tur === "kolon" ? "kolonu" : "kirişi") + " " + c.no + " var; çakışan çubuk çizilmedi.");
        const m2 = kopya(m), ks = kesitSagla(m2, t);
        return MOp.cubukCiz(m2, ri, rj, { tur: t, kesit: ks });
      }, sc.etiket || "Çubuk çizildi", { secim: function (r) { return r.no != null ? [{ tur: "cubuk", no: r.no }] : undefined; } });
    }
    /** Çok sayıda REF çifti (hızlı kolon/kiriş/çubuk sürükleme): mevcut olanlar atlanır. */
    function cubuklarCiz(ciftler, turFn, etiket) {
      if (!ciftler.length) return null;
      return uygula(function (m0) {
        let m = kopya(m0);
        const eklenen = [], atlanan = [];
        const geo = MB.geometri();
        ciftler.forEach(function (c) {
          const Pi = MAk.refKoordinat(m, c[0]), Pj = MAk.refKoordinat(m, c[1]);
          if (mevcutCubuk(m, c[0], c[1]) != null || aksKatCakisan(geo, Pi, Pj)) { atlanan.push(c); return; }
          const t = turFn ? turFn(Pi, Pj) : cubukTuru(Pi, Pj), ks = kesitSagla(m, t);
          const r = MOp.cubukCiz(m, c[0], c[1], { tur: t, kesit: ks });
          m = r.model;
          if (r.no != null) eklenen.push(r.no);
        });
        const r = { model: m, eklenen: { cubuklar: eklenen }, silinen: {}, degisen: {}, uyarilar: atlanan.length ? [atlanan.length + " yerde eleman zaten vardı; atlandı."] : [] };
        if (!eklenen.length) r.reddedildi = true;
        return r;
      }, etiket, { secim: function (r) { return (r.eklenen.cubuklar || []).map(function (no) { return { tur: "cubuk", no: no }; }); } });
    }

    // ---------------------------------------------------------------- katmanlar: aks (altta), çizim önizlemesi ve yakalama (üstte)
    function aksKatmani(bg_) {
      const ay = MB.ayar(), b = B();
      if (!ay.izgara || !b) return "";
      const g = Object.assign({}, duzlem());
      let model = b;
      if (!ay.aksBalon) {      // balonlar kapalı: yalnız çizgiler, ölçü ve kesişimler
        model = kopya(b);
        ["x", "y"].forEach(function (y) { (model.akslar[y] || []).forEach(function (a) { a.balon = "yok"; }); });
        (model.aks_sistemleri || []).forEach(function (s) { Object.keys(s).forEach(function (k) { if (Array.isArray(s[k]) && k !== "orijin") s[k].forEach(function (a) { if (a && typeof a === "object") a.balon = "yok"; }); }); });
      }
      try {
        const cizimde = !!MB.kip() && MB.kip() !== "sec" && MB.kip() !== "sil";
        const h = MAk.sahneKatmani(model, g, bg_.P, { balonR: ay.balonR || 11, olcu: ay.aksOlcu && !bg_.hafif, olcu3b: false, kesisim: !bg_.hafif && (g.tur !== "3b" || cizimde), secili: S.seciliAks, onizleme: S.aksOnizleme });
        // kot etiketleri (Z balonları) ve ek sistem balonları da gizlenir
        return ay.aksBalon ? h : h.replace(/<g class="aks-balon[^"]*"[^>]*>[\s\S]*?<\/g>/g, "");
      } catch (e) { return ""; }
    }
    MB.katmanKaydet("aks", aksKatmani, { sira: -10, bagla: function (g) { g.classList.toggle("bn-aks-kucuk", (MB.ayar().balonR || 11) < 10); } });
    function cizimKatmani(bg_) {
      if (!bg_) return "";
      let h = "";
      const P = bg_.P;
      const cizgi = function (A, Bb, sinif) { const a = P(A[0], A[1], A[2]), c = P(Bb[0], Bb[1], Bb[2]); return '<path class="' + sinif + '" d="M' + r1(a[0]) + "," + r1(a[1]) + " L" + r1(c[0]) + "," + r1(c[1]) + '"/>'; };
      (S.surukle && S.surukle.parcalar ? Array.from(S.surukle.parcalar.values()) : []).forEach(function (q) { h += cizgi(q.Pi, q.Pj, "bc-onizleme bc-onizleme-kalin"); });
      (S.surukle && S.surukle.gozler ? Array.from(S.surukle.gozler.values()) : []).forEach(function (g) { h += '<polygon class="bc-goz-onizleme" points="' + g.P.map(function (Q) { const a = P(Q[0], Q[1], Q[2]); return r1(a[0]) + "," + r1(a[1]); }).join(" ") + '"/>'; });
      (S.surukle && S.surukle.kesisimler ? Array.from(S.surukle.kesisimler.values()) : []).forEach(function (k) { const a = P(k.P[0], k.P[1], k.P[2]); h += '<circle class="bc-secili-nokta" cx="' + r1(a[0]) + '" cy="' + r1(a[1]) + '" r="' + r1(7 * bg_.s) + '"/>'; });
      if (S.parca) h += cizgi(S.parca.Pi, S.parca.Pj, "bc-onizleme bc-onizleme-kalin");
      if (S.goz) h += '<polygon class="bc-goz-onizleme" points="' + S.goz.P.map(function (Q) { const a = P(Q[0], Q[1], Q[2]); return r1(a[0]) + "," + r1(a[1]); }).join(" ") + '"/>';
      const bas = S.zincir || S.ilk;
      if (bas && bas.P) {
        const a = P(bas.P[0], bas.P[1], bas.P[2]);
        h += '<circle class="bc-secili-nokta" cx="' + r1(a[0]) + '" cy="' + r1(a[1]) + '" r="' + r1(6 * bg_.s) + '"/>';
        const hedef = S.yakalanan && S.yakalanan.P ? P(S.yakalanan.P[0], S.yakalanan.P[1], S.yakalanan.P[2]) : S.imlec;
        if (hedef) h += '<path class="bc-onizleme' + (S.ilk && !S.zincir ? " bc-onizleme-vektor" : "") + '" d="M' + r1(a[0]) + "," + r1(a[1]) + " L" + r1(hedef[0]) + "," + r1(hedef[1]) + '"/>';
      }
      if (S.aksCizgi) h += S.aksCizgi;
      if (S.yakalanan && OL) h += OL.yakalamaSvg(S.yakalanan, bg_.P3);
      return h;
    }
    MB.katmanKaydet("cizim", cizimKatmani, { sira: 40 });
    function tazele() { MB.katmanTazele("cizim"); }
    function temizle() { S.zincir = null; S.ilk = null; S.yakalanan = null; S.parca = null; S.goz = null; S.surukle = null; S.imlec = null; S.aksCizgi = ""; tazele(); }

    // aks balonu sürükleme (0,05 m adım; dokununca sayısal giriş) — elemanlar akslara adla bağlı, birlikte taşınır
    let balon = null;
    function svgNokta(e) {
      const m = svg.getScreenCTM && svg.getScreenCTM();
      if (!m) return [e.clientX, e.clientY];
      const q = svg.createSVGPoint(); q.x = e.clientX; q.y = e.clientY;
      const r = q.matrixTransform(m.inverse());
      return [r.x, r.y];
    }
    try {
      balon = MAk.balonSurukle(svg, {
        bina: function () { return B(); }, gorunum: function () { return duzlem(); },
        // yalnız Seç ve Aks taşı kiplerinde; başka bir araçta balona dokunuş o araca gider (Aks sil, Ayna…)
        etkin: function () { const k = MB.kip(); return !k || k === "sec" || k === "aks-tasi"; },
        izdusumAl: function () { const b = bg(); return b ? b.P : function () { return [0, 0]; }; },
        nokta: svgNokta,
        onizle: function (h) { S.aksOnizleme = h; S.seciliAks = h ? { sistem: h.sistem, yon: h.yon, ad: h.ad } : S.seciliAks; MB.katmanTazele("aks"); },
        degisti: function (m, r) { S.aksOnizleme = null; MB.binaAyarla(m, { etiket: "Aks " + ((r.tasinan || [])[0] || "") + " taşındı" + (r.uyarilar && r.uyarilar.length ? " — " + r.uyarilar.join(" ") : "") }); },
        hata: hata,
      });
    } catch (e) { balon = null; }
    function aksHedefiNoktada(e) {
      const l = document.elementsFromPoint ? document.elementsFromPoint(e.clientX, e.clientY) : [document.elementFromPoint(e.clientX, e.clientY)];
      for (const el of l) { const h = el && MAk.aksHedefi(el); if (h) return h; }
      return null;
    }

    // ---------------------------------------------------------------- kipler
    const KIP_IPUCU = {};
    function ipucu(id, temel) {
      return function () {
        const u = S.sonUyari ? " ⚠ " + S.sonUyari : "";
        return (typeof temel === "function" ? temel() : temel) + u;
      };
    }
    function kip(id, k, eski) {
      const tam = Object.assign({
        basla: function () { temizle(); S.sonUyari = ""; },
        bitir: function () { temizle(); },
        tus: function (e) {
          if (e.key === "Escape" && (S.zincir || S.ilk || S.surukle)) { temizle(); MB.ipucuYenile(); return true; }
          return false;
        },
      }, k);
      if (eski) tam.eskiMi = eski;
      tam.ipucu = ipucu(id, k.ipucu || "");
      MB.kipKaydet(id, tam);
      KIP_IPUCU[id] = k.ipucu;
    }
    function hover(fn) {
      return function (p, e) { S.imlec = p; if (!p) { S.yakalanan = null; S.parca = null; S.goz = null; tazele(); return; } fn(p, e); tazele(); };
    }

    // Çubuk çiz: kesişimden kesişime, zincir; Esc bitirir
    kip("cubuk-ciz", {
      ipucu: function () { return S.zincir ? "Sonraki noktaya dokunun (zincir sürer) — Esc ya da Enter bitirir." : "Çubuk çiz: aks kesişimine, düğüme ya da çubuk kesişimine dokunun (yalnız bunlara yakalanır)."; },
      hareket: hover(function (p) { S.yakalanan = yakala(p); }),
      dokun: function (p) {
        const y = yakala(p);
        if (!y) { toast("Yakalanacak nokta yok: aks kesişimi, düğüm ya da çubuk kesişimi seçin."); return; }
        if (!S.zincir) { S.zincir = y; tazele(); MB.ipucuYenile(); return; }
        const r = cubukCiz(S.zincir, y, null);
        S.zincir = r ? y : S.zincir;
        tazele(); MB.ipucuYenile();
      },
      tus: function (e) {
        if ((e.key === "Escape" || e.key === "Enter") && S.zincir) { S.zincir = null; tazele(); MB.ipucuYenile(); return true; }
        return false;
      },
    });
    // Eğik çubuk: farklı Z akslarındaki iki kesişim arası (mertek, makas üst başlığı)
    kip("egik-cubuk", {
      ipucu: function () { return S.ilk ? "İkinci noktaya dokunun: başka bir Z aksındaki kesişim (düşey olmayan)." : "Eğik çubuk: birinci kesişime dokunun (ör. saçak); sonra farklı Z aksındaki kesişime (ör. mahya)."; },
      hareket: hover(function (p) { S.yakalanan = yakala(p); }),
      dokun: function (p) {
        const y = yakala(p);
        if (!y) { toast("Aks kesişimine ya da düğüme dokunun."); return; }
        if (!S.ilk) { S.ilk = y; tazele(); MB.ipucuYenile(); return; }
        const a = S.ilk.P, c = y.P;
        if (Math.abs(a[2] - c[2]) < TOL) { toast("İki nokta aynı Z aksında: eğik çubuk için farklı kotta bir kesişim seçin (yatay çubuk için Hızlı kiriş)."); return; }
        if (Math.hypot(a[0] - c[0], a[1] - c[1]) < TOL) { toast("İki nokta aynı düşey üzerinde: kolon için Hızlı kolon aracını kullanın."); return; }
        cubukCiz(S.ilk, y, "kiris", { etiket: "Eğik çubuk çizildi" });
        S.ilk = null; tazele(); MB.ipucuYenile();
      },
    });
    // aks parçası kipleri (hızlı çubuk, hızlı kiriş, cephede hızlı kolon): dokun ya da sürükle (çoklu)
    function parcaKipi(id, suzgec, turFn, etiket, ipucuMetni, eski) {
      kip(id, {
        ipucu: ipucuMetni,
        hareket: hover(function (p) { S.parca = parcaBul(p, suzgec()); }),
        dokun: function (p) {
          const q = parcaBul(p, suzgec());
          if (!q) { toast("Bir aks parçasına (iki komşu kesişim arası) dokunun."); return; }
          const var_ = mevcutCubuk(B(), q.i, q.j);
          if (var_ != null) { uygula(function (m) { return MOp.cubukSil(m, [var_]); }, "Çubuk " + var_ + " kaldırıldı"); return; }
          cubuklarCiz([[q.i, q.j]], turFn, etiket);
        },
        surukleBasla: function (p) { const q = parcaBul(p, suzgec()); if (!q) return false; S.surukle = { parcalar: new Map([[JSON.stringify([q.i, q.j]), q]]) }; tazele(); return true; },
        surukle: function (p) { const q = parcaBul(p, suzgec()); if (q && S.surukle) { S.surukle.parcalar.set(JSON.stringify([q.i, q.j]), q); tazele(); } },
        surukleBitir: function () {
          const l = S.surukle ? Array.from(S.surukle.parcalar.values()) : [];
          S.surukle = null; tazele();
          cubuklarCiz(l.map(function (q) { return [q.i, q.j]; }), turFn, etiket);
        },
      }, eski);
    }
    parcaKipi("hizli-cubuk", function () { return null; }, null, "Hızlı çubuk",
      "Hızlı çubuk: bir aks parçasına dokunun (iki komşu kesişim arası; varsa kaldırır) ya da birden çok parça boyunca sürükleyin.");
    parcaKipi("kiris", function () { return yatay; }, function () { return "kiris"; }, "Hızlı kiriş",
      "Hızlı kiriş: etkin düzlemde yatay bir aks parçasına dokunun ya da sürükleyin (çoklu). Varolan kiriş çubuğuna dokunmak kaldırır.", function () { return MB.aksKatModu(); });
    // Hızlı kolon: planda kesişim (bu Z aksı ile altındaki), cephede düşey aks parçası; "Tüm katlara uygula" → en alttan bu Z aksına
    function kolonCiftleriNokta(p) {
      const g = duzlem();
      if (g.tur === "cephe") { const q = parcaBul(p, dusey); return q ? { ciftler: [[q.i, q.j]], parca: q } : null; }
      const k = kesisimBul(p);
      if (!k) return null;
      const ref = k.ref && k.ref.aks ? k.ref : null;
      if (!ref || ref.z == null) return null;
      return { ciftler: kolonCiftleri(B(), ref, { tumu: MB.tumKatlar() }), kesisim: k };
    }
    function kolonSurukle(p) {
      const k = kolonCiftleriNokta(p);
      if (!k || !S.surukle) return;
      k.ciftler.forEach(function (c) { S.surukle.ciftler.set(JSON.stringify(c), c); });
      if (k.kesisim) S.surukle.kesisimler.set(JSON.stringify(k.kesisim.ref), k.kesisim);
      if (k.parca) S.surukle.parcalar.set(JSON.stringify([k.parca.i, k.parca.j]), k.parca);
      tazele();
    }
    kip("kolon", {
      ipucu: function () { return duzlem().tur === "cephe" ? "Hızlı kolon (cephe): düşey bir aks parçasına dokunun ya da sürükleyin." : "Hızlı kolon: planda kesişime dokunun — bu Z aksı ile altındaki Z aksı arasına kolon (“Tüm katlara uygula”: en alttan bu düzleme); sürükleyerek çoklu."; },
      hareket: hover(function (p) { const k = kolonCiftleriNokta(p); S.parca = k && k.parca ? k.parca : null; S.yakalanan = k && k.kesisim ? { tur: "aks", ad: "Aks kesişimi", P: k.kesisim.P } : null; }),
      dokun: function (p) {
        const k = kolonCiftleriNokta(p);
        if (!k || !k.ciftler.length) { toast(duzlem().tur === "cephe" ? "Düşey bir aks parçasına dokunun." : "Bir aks kesişimine dokunun (en alttaki Z aksında kolon olmaz; düzlemi PgUp ile yukarı alın)."); return; }
        if (k.ciftler.length === 1) { const v = mevcutCubuk(B(), k.ciftler[0][0], k.ciftler[0][1]); if (v != null) { uygula(function (m) { return MOp.cubukSil(m, [v]); }, "Kolon çubuğu " + v + " kaldırıldı"); return; } }
        cubuklarCiz(k.ciftler, function () { return "kolon"; }, "Hızlı kolon");
      },
      surukleBasla: function (p) { const k = kolonCiftleriNokta(p); if (!k) return false; S.surukle = { ciftler: new Map(), kesisimler: new Map(), parcalar: new Map() }; kolonSurukle(p); return true; },
      surukle: kolonSurukle,
      surukleBitir: function () { const l = S.surukle ? Array.from(S.surukle.ciftler.values()) : []; S.surukle = null; tazele(); cubuklarCiz(l, function () { return "kolon"; }, "Hızlı kolon"); },
    }, function () { return MB.aksKatModu(); });

    // Hızlı panel: göze dokun (dört kesişim) → panel; tür seçeneği (döşeme / çatı / cephe; kalınlık 0 = sac)
    const PANEL_ON_AYAR = {
      doseme: { ad: "Döşeme (betonarme 14 cm)", oz: { tur: "doseme", kalinlik: 0.14, g: 1.5, kullanim: "konut", dagitim: "iki" } },
      "cati-sac": { ad: "Çatı (sac kaplama, kalınlık 0)", oz: { tur: "cati", kalinlik: 0, g: 0.25, q: 0.4, kullanim: "cati-gezilmeyen", kar: true, dagitim: "iki" } },
      "cephe-sac": { ad: "Cephe (sac kaplama, kalınlık 0)", oz: { tur: "cephe", kalinlik: 0, g: 0.15, dagitim: "iki" } },
      "cati-beton": { ad: "Çatı (betonarme 12 cm)", oz: { tur: "cati", kalinlik: 0.12, g: 1.5, q: 1.0, kullanim: "cati-gezilmeyen", kar: true, dagitim: "iki" } },
    };
    function panelYap(gozler) {
      if (!gozler.length) return;
      const oz = PANEL_ON_AYAR[S.panel] ? PANEL_ON_AYAR[S.panel].oz : PANEL_ON_AYAR.doseme.oz;
      uygula(function (m0) {
        let m = m0;
        const eklenen = [], uy = [];
        gozler.forEach(function (g) {
          const r = MOp.panelOlustur(m, g.koseler, kopya(oz));
          if (r.reddedildi) { uy.push.apply(uy, r.uyarilar || []); return; }
          m = r.model; eklenen.push(r.no); uy.push.apply(uy, (r.uyarilar || []).filter(function (u) { return uy.indexOf(u) < 0; }));
        });
        const r = { model: m, eklenen: { paneller: eklenen }, silinen: {}, degisen: {}, uyarilar: uy };
        if (!eklenen.length) r.reddedildi = true;
        return r;
      }, "Panel", { secim: function (r) { return (r.eklenen.paneller || []).map(function (no) { return { tur: "panel", no: no }; }); } });
    }
    function panelGozu(p, h) {
      if (h && h.kind === "nesne" && h.nesne === "panel") return null;
      return gozBul(p);
    }
    kip("doseme", {
      ipucu: function () { return "Hızlı panel (" + (PANEL_ON_AYAR[S.panel] || PANEL_ON_AYAR.doseme).ad + "): bir göze (dört kesişim arası) dokunun ya da gözler üzerinde sürükleyin. Tür: sağ tık / Alt+↓."; },
      hareket: hover(function (p) { S.goz = gozBul(p); }),
      dokun: function (p, e, h) { const g = panelGozu(p, h); if (!g) { toast("Bir göze dokunun (dört aks kesişimi arası)."); return; } panelYap([g]); },
      surukleBasla: function (p) { const g = gozBul(p); if (!g) return false; S.surukle = { gozler: new Map([[JSON.stringify(g.koseler), g]]) }; tazele(); return true; },
      surukle: function (p) { const g = gozBul(p); if (g && S.surukle) { S.surukle.gozler.set(JSON.stringify(g.koseler), g); tazele(); } },
      surukleBitir: function () { const l = S.surukle ? Array.from(S.surukle.gozler.values()) : []; S.surukle = null; tazele(); panelYap(l); },
    }, function () { return MB.aksKatModu() && S.panel === "doseme"; });

    // Hızlı çapraz: cephede (ya da planda / çatı panelinde) göze dokun → ModelOps.caprazUret (9 tip)
    // imlecin altındaki panel (SVG yığını; çubuklar üstte olsa da): eğik çatı gözü için
    function panelNoktada(e) {
      if (!e || e.clientX == null || !document.elementsFromPoint) return null;
      const l = document.elementsFromPoint(e.clientX, e.clientY);
      for (const el of l) if (el.getAttribute && el.getAttribute("data-tur") === "panel" && svg.contains(el)) return +el.getAttribute("data-no");
      return null;
    }
    function panelGozuNo(no) {
      const pn = liste(B(), "paneller").filter(function (x) { return +x.no === +no; })[0];
      if (!pn || pn.kose.length !== 4) return null;
      return { koseler: kopya(pn.kose), P: pn.kose.map(function (r) { return MB.refKoordinat(r); }), panel: pn.no };
    }
    function caprazGozu(p, h, e) {
      // 3B'de önce panel (çatı / cephe kaplaması gözü), plan ve cephede önce aks gözü
      const pn = duzlem().tur === "3b" ? panelNoktada(e) : null;
      if (pn != null) { const g = panelGozuNo(pn); if (g) return g; }
      const g = gozBul(p);
      if (g) return g;
      if (h && h.kind === "nesne" && h.nesne === "panel") return panelGozuNo(h.no);
      const pn2 = panelNoktada(e);
      return pn2 != null ? panelGozuNo(pn2) : null;
    }
    function caprazYap(gozler) {
      if (!gozler.length) return;
      const tip = S.capraz;
      uygula(function (m0) {
        let m = m0;
        const uy = [], eklenen = [];
        gozler.forEach(function (g) {
          const m2 = kopya(m), ks = kesitSagla(m2, "capraz");
          const r = MOp.caprazUret(m2, g.koseler, tip, caprazSecenek(tip, g, { kesit: ks }));
          m = r.model;
          (r.caprazlar || []).forEach(function (n) { eklenen.push(n); });
          (r.uyarilar || []).forEach(function (u) { if (uy.indexOf(u) < 0) uy.push(u); });
        });
        return { model: m, eklenen: { cubuklar: eklenen }, silinen: {}, degisen: {}, uyarilar: uy };
      }, (MAr && MAr.CAPRAZ_SECENEKLERI ? (MAr.CAPRAZ_SECENEKLERI.filter(function (s) { return s.id === tip; })[0] || { ad: tip }).ad : tip));
    }
    kip("hizli-capraz", {
      ipucu: function () { const t = MAr ? MAr.CAPRAZ_SECENEKLERI.filter(function (s) { return s.id === S.capraz; })[0] : null; return "Hızlı çapraz (" + (t ? t.ad : S.capraz) + "): cephede bir göze ya da çatı paneline dokunun; sürükleyerek çoklu. Tip: sağ tık / Alt+↓."; },
      hareket: hover(function (p) { S.goz = gozBul(p); }),
      dokun: function (p, e, h) { const g = caprazGozu(p, h, e); if (!g) { toast("Bir göze (cephede dört kesişim arası) ya da dört köşeli panele dokunun."); return; } caprazYap([g]); },
      surukleBasla: function (p) { const g = gozBul(p); if (!g) return false; S.surukle = { gozler: new Map([[JSON.stringify(g.koseler), g]]) }; tazele(); return true; },
      surukle: function (p) { const g = gozBul(p); if (g && S.surukle) { S.surukle.gozler.set(JSON.stringify(g.koseler), g); tazele(); } },
      surukleBitir: function () { const l = S.surukle ? Array.from(S.surukle.gozler.values()) : []; S.surukle = null; tazele(); caprazYap(l); },
    });

    // Mesnet: düğüme dokun → mesnet türü (seçenek)
    kip("mesnet", {
      ipucu: function () { return "Mesnet (" + MESNET_ON_AYAR[S.mesnet].ad + "): bir düğüme ya da aks kesişimine dokunun. Tür: sağ tık / Alt+↓."; },
      hareket: hover(function (p) { S.yakalanan = yakala(p, { turler: ["dugum", "aks"] }); }),
      dokun: function (p) {
        const y = yakala(p, { turler: ["dugum", "aks"] });
        if (!y || !y.ref) { toast("Bir düğüme ya da aks kesişimine dokunun."); return; }
        const tur = S.mesnet;
        uygula(function (m) {
          const r = mesnetAta(m, y.ref, tur);
          return { model: r.model, eklenen: {}, silinen: {}, degisen: {}, uyarilar: [], eylem: r.eylem, reddedildi: r.eylem === "yok" };
        }, MESNET_ON_AYAR[tur].ad + " — " + (y.etiket || ""), { bagla: false });
      },
    });

    // Yük ata: çubuk / panel / düğüm → küçük iletişim kutusu (durum G, Q, S)
    kip("yuk-ata", {
      ipucu: function () { return "Yük ata (" + S.yuk + "): çubuğa (yayılı / tekil), panele (kN/m²) ya da düğüme (kuvvet) dokunun. Durum: sağ tık / Alt+↓."; },
      hareket: hover(function (p) { S.yakalanan = yakala(p, { turler: ["dugum", "aks"] }); }),
      dokun: function (p, e, h) {
        // düğüm / aks kesişimi yakalandıysa (uç noktası) düğüm yükü; değilse dokunulan çubuk ya da panel
        const y = yakala(p, { turler: ["dugum", "aks"] });
        if (y && y.ref) { yukPenceresi({ tur: "dugum", ref: y.ref, etiket: y.etiket }); return; }
        if (h && h.kind === "nesne" && (h.nesne === "cubuk" || h.nesne === "panel")) { yukPenceresi({ tur: h.nesne, no: h.no }); return; }
        toast("Bir çubuğa, panele ya da düğüme dokunun.");
      },
    });

    // ---------------------------------------------------------------- aks kipleri
    function aksYonleri() {
      const g = duzlem();
      if (g.tur === "cephe") return g.y != null ? ["x", "z"] : ["y", "z"];
      return ["x", "y"];
    }
    function aksEkleOnizleme(p) {
      const yon = aksYonleri().indexOf(S.aksYon) >= 0 ? S.aksYon : aksYonleri()[0];
      const sp = duzlemSpek(), b = bg();
      const Q = b ? ekrandanDuzleme(b.P, sp, p) : null;
      if (!Q) return null;
      const i = { x: 0, y: 1, z: 2 }[yon], k = aksEkleKonumu(B(), yon, Q[i]);
      return { yon: yon, konum: k.konum, arasina: k.arasina, Q: Q, sp: sp };
    }
    kip("aks-ekle", {
      ipucu: function () { return "Aks ekle (" + (S.aksYon || "x").toUpperCase() + " yönü; seçenek: sağ tık / Alt+↓): iki aksın arasına dokunun → tam ortasına; dışına dokunun → o konuma (0,05 m adım)."; },
      hareket: hover(function (p) {
        const o = aksEkleOnizleme(p), b = bg();
        S.aksCizgi = "";
        if (!o || !b) return;
        // önizleme çizgisi: düzlemde, eklenecek konumda, mevcut aksların boyunca
        const yon = o.yon, i = { x: 0, y: 1, z: 2 }[yon], sp = o.sp, j = [0, 1, 2].filter(function (k) { return k !== i && k !== sp.i; })[0];
        const l = aksListesi(B(), ["x", "y", "z"][j]);
        if (!l.length) return;
        const A1 = [0, 0, 0], A2 = [0, 0, 0];
        A1[sp.i] = A2[sp.i] = sp.v; A1[i] = A2[i] = o.konum; A1[j] = l[0].konum - 1; A2[j] = l[l.length - 1].konum + 1;
        const a = b.P(A1[0], A1[1], A1[2]), c = b.P(A2[0], A2[1], A2[2]);
        S.aksCizgi = '<path class="bc-aks-onizleme" d="M' + r1(a[0]) + "," + r1(a[1]) + " L" + r1(c[0]) + "," + r1(c[1]) + '"/>' +
          '<text class="bc-aks-onizleme-t" x="' + r1(c[0] + 6) + '" y="' + r1(c[1]) + '">' + kacis(yon.toUpperCase() + " " + fmtK(o.konum) + " m" + (o.arasina ? " (" + o.arasina.join("–") + " ortası)" : "")) + "</text>";
      }),
      dokun: function (p) {
        const o = aksEkleOnizleme(p);
        if (!o) { toast("Bu görünümde düzleme dokunulamıyor; plan ya da cephe görünümüne geçin."); return; }
        let r;
        try { r = MAk.aksEkle(B(), o.arasina ? { yon: o.yon, arasina: o.arasina } : { yon: o.yon, konum: o.konum }); } catch (e) { hata(e); return; }
        S.aksCizgi = "";
        MB.binaAyarla(r.model, { etiket: o.yon.toUpperCase() + " aksı " + r.eklenen + " eklendi (" + fmtK(o.konum) + " m)." });
      },
    });
    function aksSilAkisi(h) {
      let r;
      try { r = MAk.aksSil(B(), { sistem: h.sistem, yon: h.yon, ad: h.ad }); } catch (e) { hata(e); return; }
      if (r.silindi) { MB.binaAyarla(r.model, { etiket: h.yon.toUpperCase() + " aksı " + h.ad + " silindi." + (r.uyarilar.length ? " " + r.uyarilar.join(" ") : "") }); return; }
      if (!r.onayGerekli) { toast((r.uyarilar || []).join(" ") || "Aks silinemedi."); return; }
      const k = MB.kaplamaAc("aks-sil", "Aks " + h.ad + " silinsin mi?", { kucuk: true, odak: "[data-aks-sil=elemanlarla]" });
      k.govde.innerHTML = '<p>' + kacis(h.yon.toUpperCase() + " aksı " + h.ad + "'ya bağlı " + r.bagli.ozet + " var.") + "</p>" +
        '<div class="dugmeler bc-dikey"><button type="button" class="dugme aks-tehlike" data-aks-sil="elemanlarla">Elemanlarla birlikte sil</button>' +
        (r.komsu ? '<button type="button" class="dugme" data-aks-sil="tasi">Bağlı elemanları en yakın aksa (' + kacis(r.komsu) + ") taşı</button>" : "") +
        '<button type="button" class="dugme" data-aks-sil="iptal">İptal</button></div>';
      k.govde.addEventListener("click", function (e) {
        const t = e.target.closest("[data-aks-sil]");
        if (!t) return;
        const s = t.getAttribute("data-aks-sil");
        MB.kaplamaKapat();
        if (s === "iptal") return;
        try {
          const q = MAk.aksSil(B(), { sistem: h.sistem, yon: h.yon, ad: h.ad, secenek: s });
          MB.binaAyarla(q.model, { etiket: "Aks " + h.ad + " silindi: " + (q.uyarilar || []).join(" ") });
        } catch (x) { hata(x); }
      });
    }
    kip("aks-sil", {
      ipucu: "Aks sil: bir aks çizgisine ya da balonuna dokunun (bağlı eleman varsa seçenek sorulur).",
      hareket: hover(function () {}),
      dokun: function (p, e) {
        const h = aksHedefiNoktada(e);
        if (!h) { toast("Bir aks çizgisine ya da balonuna dokunun."); return; }
        S.seciliAks = h; MB.katmanTazele("aks");
        aksSilAkisi(h);
      },
    });
    kip("aks-tasi", {
      ipucu: "Aks taşı: balonu sürükleyin (0,05 m adım) ya da aks çizgisine / balona dokunup yeni konumu yazın; bağlı düğüm ve elemanlar birlikte taşınır.",
      hareket: hover(function () {}),
      dokun: function (p, e) {
        const h = aksHedefiNoktada(e);
        if (!h) { toast("Bir aks çizgisine ya da balonuna dokunun."); return; }
        S.seciliAks = h; MB.katmanTazele("aks");
        if (balon && balon.ac) balon.ac(h, e.clientX, e.clientY);
      },
    });

    // ---------------------------------------------------------------- seçim + iki nokta (taşı, dizi, yapıştır), döndür, ayna
    function ikiNoktaKipi(id, ipucuMetni, hazirMi, bitir) {
      kip(id, {
        ipucu: function () { return S.ilk ? "Hedef noktaya dokunun (aks kesişimi / düğüm); öteleme = hedef − kaynak." : ipucuMetni; },
        hareket: hover(function (p) { S.yakalanan = yakala(p, { duzlem: null }); }),
        dokun: function (p) {
          const y = yakala(p, { duzlem: null });
          if (!y) { toast("Aks kesişimine ya da düğüme dokunun."); return; }
          if (!S.ilk) { const n = hazirMi(); if (n) { toast(n); return; } S.ilk = y; tazele(); MB.ipucuYenile(); return; }
          const d = [y.P[0] - S.ilk.P[0], y.P[1] - S.ilk.P[1], y.P[2] - S.ilk.P[2]];
          S.ilk = null; tazele();
          if (Math.hypot(d[0], d[1], d[2]) < TOL) { toast("Öteleme sıfır."); return; }
          bitir(d);
          MB.ipucuYenile();
        },
      });
    }
    const secimYok = function () { return cubukSecimiVar() || MB.secim().some(function (s) { return s.tur === "panel" || s.tur === "doseme"; }) ? null : "Önce taşınacak / çoğaltılacak elemanları seçin (Seç aracı)."; };
    function secimNesnesi(ay) { return { cubuklar: ay.cubuklar, paneller: ay.paneller }; }
    ikiNoktaKipi("tasi", "Taşı: önce elemanları seçin, sonra kaynak kesişime ve hedef kesişime dokunun (aks aralığı kadar ötelenir).", secimYok, function (d) {
      secimli("Taşındı", function (m, ay) { return MOp.tasi(m, secimNesnesi(ay), d[0], d[1], d[2]); }, { panel: true });
    });
    ikiNoktaKipi("dogrusal-dizi", "Doğrusal dizi: seçili elemanlar için kaynak kesişime, sonra bir aks aralığı ötedeki kesişime dokunun; sonra kopya sayısını girin.", secimYok, function (d) {
      const k = MB.kaplamaAc("dizi", "Doğrusal dizi", { kucuk: true, odak: "[data-a=adet]" });
      k.govde.innerHTML = '<p class="not">Öteleme: ΔX = ' + fmt(d[0]) + " m, ΔY = " + fmt(d[1]) + " m, ΔZ = " + fmt(d[2]) + " m (her kopya bir öteleme daha ileride).</p>" +
        alan("Kopya sayısı", girdi("adet", "1", ' inputmode="numeric"')) + '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Çoğalt</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const n = Math.round(sayi(oku(k.govde).adet) || 0);
        if (!(n >= 1 && n <= 50)) { toast("Kopya sayısı 1–50 olmalı."); return; }
        MB.kaplamaKapat();
        secimli(n + " kopya", function (m, ay) { return MOp.dogrusalDizi(m, secimNesnesi(ay), d[0], d[1], d[2], n); }, { panel: true });
      });
    });
    ikiNoktaKipi("yapistir", "Yapıştır: kaynak kesişime, sonra hedef kesişime dokunun; panodaki elemanlar ötelenerek kopyalanır.", function () {
      const pn = MB.pano();
      return pn && pn.s3 && pn.s3.cubuklar.length + pn.s3.paneller.length ? null : "Pano boş: önce elemanları seçip Kopyala (Ctrl+C).";
    }, function (d) {
      const pn = MB.pano();
      uygula(function (m) {
        const var_ = { cubuklar: pn.s3.cubuklar.filter(function (n) { return liste(m, "cubuklar").some(function (c) { return +c.no === n; }); }),
          paneller: pn.s3.paneller.filter(function (n) { return liste(m, "paneller").some(function (c) { return +c.no === n; }); }) };
        if (!var_.cubuklar.length && !var_.paneller.length) throw new Error("Panodaki elemanlar artık modelde yok.");
        return MOp.dogrusalDizi(m, var_, d[0], d[1], d[2], 1);
      }, "Yapıştırıldı");
    });
    kip("dondur", {
      ipucu: "Döndür: önce elemanları seçin, sonra dönme merkezi olacak kesişime dokunun (eksen düşey Z; açı sorulur).",
      hareket: hover(function (p) { S.yakalanan = yakala(p, { duzlem: null }); }),
      dokun: function (p) {
        const n = secimYok(); if (n) { toast(n); return; }
        const y = yakala(p, { duzlem: null });
        if (!y) { toast("Dönme merkezi için bir kesişime dokunun."); return; }
        const k = MB.kaplamaAc("dondur", "Döndür", { kucuk: true, odak: "[data-a=aci]" });
        k.govde.innerHTML = '<p class="not">Merkez: ' + kacis(y.etiket || "") + "</p>" + '<div class="bn-iki">' + alan("Açı (°, sağ el kuralı)", girdi("aci", "90", ' inputmode="decimal"')) +
          alan("Eksen", sec("eksen", [["Z", "Z (düşey)"], ["X", "X"], ["Y", "Y"]], "Z")) + "</div>" + onay("kopya", "Kopya olarak (asıllar yerinde kalır)", false) +
          alan("Kopya sayısı", girdi("adet", "1", ' inputmode="numeric"')) + '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Döndür</button></div>';
        k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
          const o = oku(k.govde), aci = sayi(o.aci);
          if (aci == null) { toast("Açı sayı olmalı."); return; }
          MB.kaplamaKapat();
          const yon = { X: [1, 0, 0], Y: [0, 1, 0], Z: [0, 0, 1] }[o.eksen] || [0, 0, 1];
          secimli("Döndürüldü (" + fmtK(aci) + "°)", function (m, ay) { return MOp.dondur(m, secimNesnesi(ay), { nokta: y.P, yon: yon }, aci, { kopya: !!o.kopya, adet: Math.max(1, Math.round(sayi(o.adet) || 1)) }); }, { panel: true });
        });
      },
    });
    kip("ayna", {
      ipucu: "Ayna: önce elemanları seçin, sonra yansıma düzlemi olacak aks çizgisine dokunun (X ya da Y aksı; cephede Z aksı da).",
      hareket: hover(function () {}),
      dokun: function (p, e) {
        const n = secimYok(); if (n) { toast(n); return; }
        const h = aksHedefiNoktada(e);
        if (!h || (h.sistem && h.sistem !== "GLOBAL")) { toast("Yansıma düzlemi için GLOBAL bir aks çizgisine ya da balonuna dokunun."); return; }
        const a = aksListesi(B(), h.yon).filter(function (x) { return x.ad === h.ad; })[0];
        if (!a) return;
        const d = {}; d[h.yon.toUpperCase()] = a.konum;
        const k = MB.kaplamaAc("ayna", "Ayna: " + h.yon.toUpperCase() + " aksı " + h.ad, { kucuk: true });
        k.govde.innerHTML = '<p class="not">Yansıma düzlemi ' + h.yon.toUpperCase() + " = " + fmt(a.konum) + " m.</p>" + onay("kopya", "Kopya olarak (asıllar yerinde kalır)", true) +
          '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Yansıt</button></div>';
        k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
          const o = oku(k.govde);
          MB.kaplamaKapat();
          secimli("Aynalandı", function (m, ay) { return MOp.ayna(m, secimNesnesi(ay), d, { kopya: !!o.kopya }); }, { panel: true });
        });
      },
    });

    // ---------------------------------------------------------------- önizleme SVG (cephe / plan): aks katmanı + çubuklar + paneller
    function onizlemeSvg(model, g, W, H, vurgu) {
      let ic = "";
      try {
        const f = MAk.uygunIzdusum(model, g, W, H, { balonR: 9 });
        ic += MAk.sahneKatmani(model, g, f, { balonR: 9, olcu: true, kesisim: false });
        const cz = new MAk.Cozucu(model), o = MAk.gorunumCoz(model, g);
        const icinde = function (P) {
          if (o.tur === "cephe") { const L = MAk.noktaSistem(o.ana, P[0], P[1], P[2]); return Math.abs(L[o.sabitYon === o.ana.yonler[0] ? 0 : 1] - o.sabit.konum) < 0.002; }
          return true;
        };
        liste(model, "paneller").forEach(function (p) {
          let K; try { K = p.kose.map(function (r) { return cz.coz(r); }); } catch (e) { return; }
          if (!K.every(icinde)) return;
          ic += '<polygon class="bc-oniz-panel" points="' + K.map(function (Q) { const a = f(Q[0], Q[1], Q[2]); return r1(a[0]) + "," + r1(a[1]); }).join(" ") + '"/>';
        });
        liste(model, "cubuklar").forEach(function (c) {
          let Pi, Pj; try { Pi = cz.coz(c.i); Pj = cz.coz(c.j); } catch (e) { return; }
          if (!icinde(Pi) || !icinde(Pj)) return;
          const a = f(Pi[0], Pi[1], Pi[2]), b = f(Pj[0], Pj[1], Pj[2]);
          const yeni = vurgu && vurgu.has(+c.no);
          ic += '<path class="bc-oniz-cubuk bc-oniz-' + kacis(c.tur || "diger") + (yeni ? " bc-oniz-yeni" : "") + '" d="M' + r1(a[0]) + "," + r1(a[1]) + " L" + r1(b[0]) + "," + r1(b[1]) + '"/>';
        });
      } catch (e) { ic = '<text x="12" y="24" class="bc-oniz-hata">' + kacis(e.message) + "</text>"; }
      return '<svg class="bc-onizleme-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Önizleme">' + ic + "</svg>";
    }
    function yenilerKumesi(once, sonra) {
      const a = new Set(liste(once, "cubuklar").map(function (c) { return +c.no; }));
      return new Set(liste(sonra, "cubuklar").map(function (c) { return +c.no; }).filter(function (n) { return !a.has(n); }));
    }
    // kesit seçici: modeldeki kesitler + türün varsayılanı (modelde yoksa "katalogdan eklenecek" diye en başta); seçili = varsayılan
    function kesitListesi(m, tur) {
      const l = Object.keys((m && m.kesitler) || {}).map(function (k) { return [k, k + (m.kesitler[k].profil ? " (" + m.kesitler[k].profil + ")" : m.kesitler[k].b ? " (" + Math.round(m.kesitler[k].b * 100) + "×" + Math.round(m.kesitler[k].h * 100) + ")" : "")]; });
      const v = kesitSagla(kopya(m), tur);
      if (!l.some(function (x) { return x[0] === v; })) l.unshift([v, v + " (katalogdan eklenir)"]);
      return l;
    }
    function kesitHazirla(m, ad, tur) {
      if (ad && m.kesitler && m.kesitler[ad]) return ad;
      return kesitSagla(m, tur);
    }
    function profilListesi() {
      const k = MB.kutuphane(), pr = (k && k.kesit_katalogu && k.kesit_katalogu.profiller) || {};
      const l = [];
      Object.keys(pr).forEach(function (a) { (pr[a] || []).forEach(function (p) { l.push(p); }); });
      return l;
    }

    // ---------------------------------------------------------------- aks iletişim kutuları
    function aksSihirbazi() {
      const b = B();
      const k = MB.kaplamaAc("aks-sihirbaz", "Hızlı aks sihirbazı", { genis: false });
      k.govde.innerHTML = '<div class="bc-sh-kip" role="radiogroup" aria-label="Uygulama biçimi">' +
        '<label class="bn-onay"><input type="radio" name="bc-sh-kip" value="degistir" checked> Mevcut aksları değiştir (elemanlar akslara yapışık taşınır)</label>' +
        '<label class="bn-onay"><input type="radio" name="bc-sh-kip" value="yeni"> Yeni model (elemansız; kesit ve malzemeler korunur)</label>' +
        '<label class="bn-alan bc-sh-sistem"><span>Yeni modelin sistemi</span><select class="girdi" data-a="sistem">' + secenekHtml([["celik", "Çelik"], ["betonarme", "Betonarme"]], b.sistem) + "</select></label></div>" +
        '<div class="bc-sh-kap"></div>';
      const kap = k.govde.querySelector(".bc-sh-kap");
      const sh = MAk.sihirbaz(kap, {
        bina: b, dugmeMetni: "Aksları uygula", iptal: function () { MB.kaplamaKapat(); },
        tamam: function (akslar, katlar) {
          const kipD = (k.govde.querySelector("input[name=bc-sh-kip]:checked") || {}).value;
          try {
            if (kipD === "yeni") {
              const m = yeniModel(B(), akslar, katlar, { sistem: oku(k.govde).sistem });
              MB.kaplamaKapat();
              MB.binaAyarla(m, { etiket: "Yeni aks modeli: " + akslar.x.length + " X × " + akslar.y.length + " Y × " + akslar.z.length + " Z aksı." });
              MB.duzlemSec("z", (akslar.z.filter(function (a) { return a.kat === 1; })[0] || akslar.z[akslar.z.length - 1]).ad);
            } else {
              const r = aksSihirbazUygula(B(), akslar, katlar);
              if (r.silinen.length && !window.confirm("Sihirbazda olmayan akslara bağlı elemanlar silinecek: " + r.silinen.map(function (s) { return s.yon.toUpperCase() + " " + s.ad + " (" + s.ozet + ")"; }).join("; ") + ". Devam?")) return;
              MB.kaplamaKapat();
              MB.binaAyarla(r.model, { etiket: "Akslar güncellendi." + (r.uyarilar.length ? " " + r.uyarilar.join(" ") : "") });
            }
          } catch (e) { hata(e); }
        },
      });
      k.temizle = function () { try { sh.kaldir(); } catch (e) { /* yoksay */ } };
    }
    let duzenleyici = null, duzBizden = false;
    function aksDuzenleyici(sekme) {
      const k = MB.kaplamaAc("aks-duzenle", "Aks verisi", { genis: true });
      const kap = document.createElement("div");
      k.govde.appendChild(kap);
      duzenleyici = MAk.duzenleyici(kap, {
        bina: B(), sekme: sekme || "x",
        degisti: function (m, r) {
          duzBizden = true;
          try { MB.binaAyarla(m, { etiket: (r && r.uyarilar && r.uyarilar.length ? r.uyarilar.join(" ") : ""), sessiz: true }); } catch (e) { hata(e); }
          duzBizden = false;
        },
        secim: function (h) { S.seciliAks = h; MB.katmanTazele("aks"); },
      });
      k.temizle = function () { try { duzenleyici.kaldir(); } catch (e) { /* yoksay */ } duzenleyici = null; S.seciliAks = null; MB.katmanTazele("aks"); };
    }
    MB.dinle("model", function () { if (duzenleyici && !duzBizden) { try { duzenleyici.guncelle(B()); } catch (e) { /* yoksay */ } } });
    function aksSistemiPenceresi() {
      const k = MB.kaplamaAc("aks-sistemi", "Ek aks sistemleri", { genis: false });
      const ciz = function () {
        const b = B(), l = b.aks_sistemleri || [];
        k.govde.innerHTML = (l.length ? '<table class="se-tablo bc-tablo"><thead><tr><th>Ad</th><th>Tür</th><th>Orijin (m)</th><th>Açı</th><th>Görünür</th><th></th></tr></thead><tbody>' + l.map(function (s) {
          return "<tr><td>" + kacis(s.ad) + "</td><td>" + (s.tur === "silindirik" ? "silindirik" : "kartezyen") + "</td><td>" + (s.orijin || [0, 0, 0]).map(fmtK).join("; ") + "</td><td>" + fmtK(+s.aci || 0) + "°</td>" +
            '<td><input type="checkbox" data-sis-gor="' + kacis(s.ad) + '"' + (s.gorunur !== false ? " checked" : "") + ' aria-label="' + kacis(s.ad) + ' görünür"></td><td><button type="button" class="se-sil" data-sis-sil="' + kacis(s.ad) + '" aria-label="Sil">✕</button></td></tr>';
        }).join("") + "</tbody></table>" : '<p class="not">Ek aks sistemi yok. GLOBAL akslar (X harf, Y sayı, Z kot) her zaman vardır.</p>') +
          "<h3>Yeni sistem</h3>" + '<div class="bn-iki">' + alan("Ad", girdi("ad", "KANAT-" + String.fromCharCode(65 + l.length))) + alan("Tür", sec("tur", [["kartezyen", "Kartezyen (döndürülmüş / ötelenmiş)"], ["silindirik", "Silindirik (R, θ)"]], "kartezyen")) + "</div>" +
          '<div class="bn-iki">' + alan("Orijin X; Y; Z (m)", girdi("orijin", "0 0 0")) + alan("Açı (°, Z çevresinde)", girdi("aci", "30", ' inputmode="decimal"')) + "</div>" +
          '<div class="bn-iki">' + alan("1. yön aksları (X ya da R)", girdi("u", "3@6")) + alan("2. yön aksları (Y ya da θ °)", girdi("v", "2@6")) + "</div>" +
          '<p class="not">Aralık sözdizimi: "3@6, 7.5" (aralıklar) ya da "0 6 12" (konumlar). Z aksları GLOBAL ile ortaktır.</p>' +
          '<div class="dugmeler"><button type="button" class="dugme ana" data-sis-ekle>Sistemi ekle</button></div>';
      };
      ciz();
      k.govde.addEventListener("change", function (e) {
        const t = e.target.closest("[data-sis-gor]");
        if (!t) return;
        try { MB.binaAyarla(MAk.sistemGuncelle(B(), t.getAttribute("data-sis-gor"), { gorunur: t.checked }).model, { sessiz: true }); } catch (x) { hata(x); }
      });
      k.govde.addEventListener("click", function (e) {
        const s = e.target.closest("[data-sis-sil]");
        if (s) {
          const ad = s.getAttribute("data-sis-sil");
          try {
            let r = MAk.sistemSil(B(), ad);
            if (r.onayGerekli) { if (!window.confirm(ad + " sistemine bağlı " + r.bagli.toplam + " kayıt var; elemanlarla birlikte silinsin mi?")) return; r = MAk.sistemSil(B(), ad, "elemanlarla"); }
            MB.binaAyarla(r.model, { etiket: ad + " sistemi silindi." }); ciz();
          } catch (x) { hata(x); }
          return;
        }
        if (!e.target.closest("[data-sis-ekle]")) return;
        const o = oku(k.govde);
        try {
          const or = String(o.orijin).trim().split(/[\s;]+/).map(sayi);
          if (or.length !== 3 || or.some(function (v) { return v == null; })) throw new Error("Orijin üç sayı olmalı: X Y Z.");
          const sl = o.tur === "silindirik";
          const uk = MAk.sozdizimiAyristir(o.u, { baslangic: sl ? 0 : 0 }).konumlar, vk = MAk.sozdizimiAyristir(o.v).konumlar;
          const s = { ad: o.ad, tur: o.tur, orijin: or, aci: sayi(o.aci) || 0 };
          const uAd = MAk.adlarUret(sl ? "r" : "x", uk.length), vAd = MAk.adlarUret(sl ? "teta" : "y", vk.length);
          s[sl ? "r" : "x"] = uk.map(function (v, i) { return { ad: uAd[i], konum: sl && i === 0 && v === 0 ? 0 : v }; });
          s[sl ? "teta" : "y"] = vk.map(function (v, i) { return { ad: vAd[i], konum: v }; });
          MB.binaAyarla(MAk.sistemEkle(B(), s).model, { etiket: s.ad + " aks sistemi eklendi." });
          ciz();
        } catch (x) { hata(x); }
      });
    }
    function aksGorunurlukPenceresi() {
      const k = MB.kaplamaAc("aks-gorunurluk", "Aks görünürlüğü", { genis: false });
      const ciz = function () {
        const b = B(), ay = MB.ayar();
        let h = '<div class="bc-satir">' + onay("balon", "Aks balonları", ay.aksBalon) + onay("olcu", "Aralık ölçü zinciri", ay.aksOlcu) + onay("izgara", "Aks ızgarası", ay.izgara) + "</div>";
        ["x", "y"].forEach(function (yon) {
          h += "<h3>" + yon.toUpperCase() + " aksları</h3><table class=\"se-tablo bc-tablo\"><thead><tr><th>Ad</th><th>Konum (m)</th><th>Görünür</th><th>Balon</th></tr></thead><tbody>" +
            (b.akslar[yon] || []).map(function (a) {
              return "<tr><td>" + kacis(a.ad) + "</td><td>" + fmtK(+a.konum) + '</td><td><input type="checkbox" data-gor="' + yon + "|" + kacis(a.ad) + '"' + (a.gorunur !== false ? " checked" : "") + ' aria-label="' + kacis(a.ad) + ' görünür"></td>' +
                '<td><select class="girdi kucuk" data-balon="' + yon + "|" + kacis(a.ad) + '" aria-label="' + kacis(a.ad) + ' balon yeri">' + secenekHtml([["bas", "Baş"], ["son", "Son"], ["iki", "İki uç"], ["yok", "Yok"]], a.balon || "bas") + "</select></td></tr>";
            }).join("") + "</tbody></table>";
        });
        k.govde.innerHTML = h;
      };
      ciz();
      k.govde.addEventListener("change", function (e) {
        const t = e.target;
        if (t.getAttribute("data-a")) {
          const o = oku(k.govde);
          MB.ayarla({ aksBalon: o.balon, aksOlcu: o.olcu });
          if (o.izgara !== MB.ayar().izgara && MAr && MAr.komut("izgara")) MAr.calistir("izgara");
          return;
        }
        const g = t.getAttribute("data-gor") || t.getAttribute("data-balon");
        if (!g) return;
        const p = g.split("|"), d = t.hasAttribute("data-gor") ? { gorunur: t.checked } : { balon: t.value };
        try { MB.binaAyarla(MAk.aksOzellik(B(), Object.assign({ yon: p[0], ad: p[1] }, d)).model, { sessiz: true }); } catch (x) { hata(x); }
      });
    }

    // ---------------------------------------------------------------- üreteç iletişim kutuları (parametre + önizleme)
    function ureticiPencere(tur, baslik, formHtml, hesapla, uygulaMetni) {
      const k = MB.kaplamaAc(tur, baslik, { genis: false });
      k.govde.innerHTML = '<div class="bc-uretec"><div class="bc-uretec-form">' + formHtml + '</div><div class="bc-uretec-oniz"><div class="bc-oniz-kap"></div><p class="not bc-oniz-not" aria-live="polite"></p></div></div>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-uret>' + kacis(uygulaMetni || "Üret") + '</button><button type="button" class="dugme" data-kaplama-kapat>Vazgeç</button></div>';
      let son = null, zam = 0;
      const onizle = function () {
        clearTimeout(zam);
        zam = setTimeout(function () {
          const not = k.govde.querySelector(".bc-oniz-not"), kap = k.govde.querySelector(".bc-oniz-kap");
          try {
            son = hesapla(oku(k.govde), B());
            const w = Math.min(560, Math.max(260, kap.clientWidth || 420));
            kap.innerHTML = onizlemeSvg(son.model, son.gorunum, w, Math.round(w * 0.55), yenilerKumesi(B(), son.model));
            not.className = "not bc-oniz-not";
            not.textContent = (son.ozet || "") + (son.uyarilar && son.uyarilar.length ? " ⚠ " + son.uyarilar.join(" ") : "");
          } catch (e) { son = null; kap.innerHTML = ""; not.className = "not bc-oniz-not bc-hata"; not.textContent = (e && e.message) || String(e); }
        }, 120);
      };
      k.govde.addEventListener("input", onizle);
      k.govde.addEventListener("change", onizle);
      k.govde.querySelector("[data-uret]").addEventListener("click", function () {
        let r;
        try { r = hesapla(oku(k.govde), B()); } catch (e) { hata(e); return; }
        MB.kaplamaKapat();
        uygula(function () { return r.rapor; }, baslik);
      });
      onizle();
      return k;
    }
    function aksSecenek(yon) { return aksListesi(B(), yon).map(function (a) { return [a.ad, a.ad + " (" + fmtK(a.konum) + ")"]; }); }
    function besikPenceresi() {
      const b = B(), xs = aksListesi(b, "x"), ys = aksListesi(b, "y"), zs = aksListesi(b, "z");
      const kolonX = xs.filter(function (a) { return a.ad.indexOf("'") < 0; });
      const zt = zs[0] || { ad: "", konum: 0 }, sac = zs.filter(function (a) { return /sa[çc]ak/i.test(a.ad); })[0] || zs[1] || { konum: zt.konum + 6 };
      const mah = zs.filter(function (a) { return /mahya/i.test(a.ad); })[0] || { konum: sac.konum + 1.5 };
      const celik = b.sistem === "celik";
      const form = '<fieldset class="bc-alanlar"><legend>Kolon aksları (açıklıklar ardışık iki aks arası)</legend><div class="bc-cipler">' + xs.map(function (a) {
        return '<label class="bn-onay"><input type="checkbox" data-a="kx_' + kacis(a.ad) + '"' + (kolonX.indexOf(a) >= 0 ? " checked" : "") + "> " + kacis(a.ad) + "</label>";
      }).join("") + "</div></fieldset>" +
        '<div class="bn-iki">' + alan("İlk çerçeve (Y aksı)", sec("y0", aksSecenek("y"), (ys[0] || {}).ad)) + alan("Son çerçeve (Y aksı)", sec("y1", aksSecenek("y"), (ys[ys.length - 1] || {}).ad)) + "</div>" +
        '<div class="bn-iki">' + alan("Taban (Z aksı)", sec("taban", aksSecenek("z"), zt.ad)) + alan("Mesnet", sec("mesnet", [["ankastre", "Ankastre"], ["mafsal", "Mafsallı"], ["yok", "Ekleme (temelden)"]], "ankastre")) + "</div>" +
        '<div class="bn-iki">' + alan("Saçak kotu (m)", girdi("sacak", fmtK(sac.konum).replace(",", "."), ' inputmode="decimal"')) + alan("Mahya kotu (m)", girdi("mahya", fmtK(mah.konum).replace(",", "."), ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Kolon kesiti", sec("kolon", kesitListesi(b, "kolon"), kesitSagla(kopya(b), "kolon"))) + alan("Mertek kesiti", sec("mertek", kesitListesi(b, "kiris"), kesitSagla(kopya(b), "kiris"))) + "</div>" +
        '<div class="bn-iki">' + alan("Vute boyu (m; 0 = vutesiz)", girdi("vuteBoy", celik ? "2" : "0", ' inputmode="decimal"')) + alan("Vute ek yüksekliği (m)", girdi("vuteH", "0.4", ' inputmode="decimal"')) + "</div>" +
        onay("asik", "Aşıklar", true) + '<div class="bn-iki">' + alan("Aşık aralığı (m)", girdi("asikAralik", "2.5", ' inputmode="decimal"')) + alan("Aşık kesiti", sec("asikKesit", kesitListesi(b, "asik"), kesitSagla(kopya(b), "asik"))) + "</div>" +
        onay("panel", "Çatı kaplaması (sac panel, kalınlık 0)", true) +
        '<p class="not">Eksik saçak / mahya Z aksları ve her açıklığın ortasındaki mahya X aksı kendiliğinden eklenir; düğümler aks kesişimi ya da mertek bölme noktasıdır.</p>';
      ureticiPencere("besik-cerceve", "Beşik çerçeve", form, function (o, m0) {
        const kx = xs.filter(function (a) { return o["kx_" + a.ad]; }).map(function (a) { return a.ad; });
        if (kx.length < 2) throw new Error("En az iki kolon aksı işaretleyin.");
        const yi = ys.findIndex(function (a) { return a.ad === o.y0; }), yj = ys.findIndex(function (a) { return a.ad === o.y1; });
        const yl = ys.slice(Math.min(yi, yj), Math.max(yi, yj) + 1).map(function (a) { return a.ad; });
        const acik = []; for (let i = 0; i + 1 < kx.length; i++) acik.push([kx[i], kx[i + 1]]);
        let m = kopya(m0);
        const kes = { kolon: kesitHazirla(m, o.kolon, "kolon"), mertek: kesitHazirla(m, o.mertek, "kiris") };
        const asikK = o.asik ? kesitHazirla(m, o.asikKesit, "asik") : null;
        const p = besikPlan(m, { acikliklar: acik, y: yl, taban: o.taban, sacak: sayi(o.sacak), mahya: sayi(o.mahya), kesitler: kes,
          vute: sayi(o.vuteBoy) > 0 ? { boy: sayi(o.vuteBoy), yukseklik: sayi(o.vuteH) || 0 } : null, asik: o.asik ? { aralik: sayi(o.asikAralik), kesit: asikK } : null,
          panel: !!o.panel, mesnet: o.mesnet });
        m = p.model;
        let uy = p.uyarilar.slice(), ilk = null, eklenen = [];
        p.parametreler.forEach(function (par) {
          const r = MOp.besikCerceveUret(m, par);
          if (!ilk) ilk = r;
          m = r.model;
          (r.uyarilar || []).forEach(function (u) { if (uy.indexOf(u) < 0) uy.push(u); });
          eklenen = eklenen.concat(r.eklenen.cubuklar || []);
        });
        const rapor = { model: m, eklenen: { cubuklar: eklenen }, silinen: {}, degisen: {}, uyarilar: (p.eklenen.length ? ["Eklenen akslar: " + p.eklenen.join(", ") + "."] : []).concat(uy) };
        return { model: m, rapor: rapor, gorunum: { tur: "cephe", y: yl[0] }, ozet: p.parametreler.length + " üreteç · " + eklenen.length + " çubuk" + (ilk && ilk.egim != null ? " · çatı eğimi " + fmt(ilk.egim, 1) + "°" : ""), uyarilar: uy };
      }, "Çerçeveleri üret");
    }
    function makasPenceresi() {
      const b = B(), xs = aksListesi(b, "x"), ys = aksListesi(b, "y"), zs = aksListesi(b, "z");
      const tipler = (MOp.MAKAS_TIPLERI || []).map(function (t) { return [t, { pratt: "Pratt", howe: "Howe", warren: "Warren", "warren-dikmeli": "Warren (dikmeli)", k: "K makas", fink: "Fink", "besik-pratt": "Beşik Pratt", "besik-howe": "Beşik Howe" }[t] || t]; });
      const zs0 = zs.filter(function (a) { return /sa[çc]ak/i.test(a.ad); })[0] || zs[zs.length - 1] || {};
      const form = alan("Makas tipi", sec("tip", tipler, "besik-pratt")) +
        '<div class="bn-iki">' + alan("Sol mesnet (X aksı)", sec("xa", aksSecenek("x"), (xs[0] || {}).ad)) + alan("Sağ mesnet (X aksı)", sec("xb", aksSecenek("x"), (xs[xs.length - 1] || {}).ad)) + "</div>" +
        '<div class="bn-iki">' + alan("İlk makas (Y aksı)", sec("y0", aksSecenek("y"), (ys[0] || {}).ad)) + alan("Son makas (Y aksı)", sec("y1", aksSecenek("y"), (ys[0] || {}).ad)) + "</div>" +
        '<div class="bn-iki">' + alan("Mesnet kotu (Z aksı)", sec("z", aksSecenek("z"), zs0.ad)) + alan("Yükseklik / mahya (m)", girdi("h", "2", ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Göz sayısı", girdi("goz", "8", ' inputmode="numeric"')) + alan("Uç yüksekliği (beşik; m)", girdi("uc", "0", ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Üst başlık", sec("ust", kesitListesi(b, "makas-ust"), kesitSagla(kopya(b), "makas-ust"))) + alan("Alt başlık", sec("alt", kesitListesi(b, "makas-alt"), kesitSagla(kopya(b), "makas-alt"))) + "</div>" +
        '<div class="bn-iki">' + alan("Dikme", sec("dikme", kesitListesi(b, "makas-dikme"), kesitSagla(kopya(b), "makas-dikme"))) + alan("Diyagonal", sec("diyagonal", kesitListesi(b, "makas-diyagonal"), kesitSagla(kopya(b), "makas-diyagonal"))) + "</div>" +
        onay("mafsal", "Gövde çubukları mafsallı (kafes)", true) + '<p class="not">Üst başlık / mahya Z aksı ve beşik tiplerde açıklık ortası aksı yoksa eklenir; ara düğümler bölme noktasıdır.</p>';
      ureticiPencere("makas", "Makas üreteci", form, function (o, m0) {
        const yi = ys.findIndex(function (a) { return a.ad === o.y0; }), yj = ys.findIndex(function (a) { return a.ad === o.y1; });
        const yl = ys.slice(Math.min(yi, yj), Math.max(yi, yj) + 1).map(function (a) { return a.ad; });
        if (o.xa === o.xb) throw new Error("Sol ve sağ mesnet farklı aks olmalı.");
        let m = kopya(m0), uy = [], ekl = [], eklAks = [];
        const kes = { ust: kesitHazirla(m, o.ust, "makas-ust"), alt: kesitHazirla(m, o.alt, "makas-alt"), dikme: kesitHazirla(m, o.dikme, "makas-dikme"), diyagonal: kesitHazirla(m, o.diyagonal, "makas-diyagonal") };
        yl.forEach(function (y) {
          const p = makasPlan(m, { tip: o.tip, bas: { aks: [o.xa, y], z: o.z }, son: { aks: [o.xb, y], z: o.z }, yukseklik: sayi(o.h), goz: sayi(o.goz), kesitler: kes, uc_yukseklik: sayi(o.uc) || 0, mafsalli_govde: !!o.mafsal });
          m = p.model; p.eklenen.forEach(function (x) { if (eklAks.indexOf(x) < 0) eklAks.push(x); });
          const r = MOp.makasUret(m, p.parametre);
          m = r.model; ekl = ekl.concat(r.eklenen.cubuklar || []);
          (r.uyarilar || []).forEach(function (u) { if (uy.indexOf(u) < 0) uy.push(u); });
        });
        return { model: m, rapor: { model: m, eklenen: { cubuklar: ekl }, silinen: {}, degisen: {}, uyarilar: (eklAks.length ? ["Eklenen akslar: " + eklAks.join(", ") + "."] : []).concat(uy) },
          gorunum: { tur: "cephe", y: yl[0] }, ozet: yl.length + " makas · " + ekl.length + " çubuk", uyarilar: uy };
      }, "Makasları üret");
    }
    function asikPenceresi() {
      const b = B(), ay = secimAyir(MB.secim());
      const hedefMetin = ay.paneller.length ? "Panel " + ay.paneller[0] : ay.cubuklar.length >= 2 ? ay.cubuklar.length + " mertek çubuğu" : null;
      if (!hedefMetin) { toast("Aşık için önce en az iki mertek çubuğunu (ya da bir çatı panelini) seçin."); return; }
      const form = '<p class="not">Hedef: ' + kacis(hedefMetin) + ' (seçim).</p><div class="bn-iki">' + alan("Aşık aralığı (m)", girdi("aralik", "1.5", ' inputmode="decimal"')) +
        alan("Aşık kesiti", sec("kesit", kesitListesi(b, "asik"), kesitSagla(kopya(b), "asik"))) + "</div>" + onay("uclar", "Saçak ve mahyada da aşık", true) + onay("mafsal", "Aşıklar mafsallı (basit kiriş)", true) +
        '<p class="not">Aşık noktaları mertek üzerinde bölme düğümüdür (aks taşınınca birlikte taşınır); aşık yerel ekseni çatı eğimine döndürülür.</p>';
      ureticiPencere("asik", "Aşık üreteci", form, function (o, m0) {
        const m = kopya(m0), ks = kesitHazirla(m, o.kesit, "asik");
        const hedef = ay.paneller.length ? { panel: ay.paneller[0] } : ay.cubuklar;
        const r = MOp.asikUret(m, hedef, sayi(o.aralik), ks, { uclar: !!o.uclar, mafsalli: !!o.mafsal });
        const zs = aksListesi(r.model, "z");
        return { model: r.model, rapor: r, gorunum: { tur: "plan", z: zs[zs.length - 1].ad }, ozet: (r.asiklar || []).length + " aşık · gerçek aralık " + fmt(r.aralik_gercek) + " m", uyarilar: r.uyarilar };
      }, "Aşıkları üret");
    }
    function krenPenceresi() {
      const b = B(), xs = aksListesi(b, "x"), zs = aksListesi(b, "z");
      const kz = zs.filter(function (a) { return /kren/i.test(a.ad); })[0];
      const form = '<div class="bn-iki">' + alan("1. kren hattı (X aksı)", sec("h1", aksSecenek("x"), (xs[0] || {}).ad)) + alan("2. kren hattı (X aksı)", sec("h2", aksSecenek("x"), (xs[2] || xs[1] || {}).ad)) + "</div>" +
        '<div class="bn-iki">' + alan("Kren kotu (m)", girdi("kot", kz ? fmtK(kz.konum).replace(",", ".") : "6", ' inputmode="decimal"')) + alan("Konsol boyu (m; 0 = kolona oturur)", girdi("konsol", "0.5", ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Kren kirişi", sec("kiris", kesitListesi(b, "kren"), kesitSagla(kopya(b), "kren"))) + alan("Konsol", sec("konsolK", kesitListesi(b, "kiris"), kesitSagla(kopya(b), "kiris"))) + "</div>" +
        "<h3>Kren</h3>" + '<div class="bn-iki">' + alan("P_maks (kN/tekerlek)", girdi("Pmaks", "80", ' inputmode="decimal"')) + alan("P_min (kN)", girdi("Pmin", "25", ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("H yanal (kN)", girdi("Hy", "8", ' inputmode="decimal"')) + alan("H fren (kN)", girdi("Hf", "6", ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Tekerlek aralığı (m)", girdi("ara", "3.5", ' inputmode="decimal"')) + alan("Dinamik katsayı", girdi("din", "1.25", ' inputmode="decimal"')) + "</div>" +
        '<p class="not">Kren kotunda Z aksı yoksa “Kren” adıyla eklenir; kolonlar bu kotta bölünür. Kren yükleri K yük durumunda (konum başına alt durum).</p>';
      ureticiPencere("kren-yolu", "Kren yolu", form, function (o, m0) {
        if (o.h1 === o.h2) throw new Error("İki farklı kren hattı aksı seçin.");
        const m = kopya(m0), kes = { kiris: kesitHazirla(m, o.kiris, "kren"), konsol: kesitHazirla(m, o.konsolK, "kiris") };
        const p = krenPlan(m, { hatlar: [o.h1, o.h2], yon: "x", kot: sayi(o.kot) });
        if (p.kolonlar.length < 2) throw new Error("Seçilen akslarda kren kotunu kesen kolon çubukları yok" + (p.uyarilar.length ? ": " + p.uyarilar.join(" ") : "") + " (aks–kat kolonları önce genelleştirilmeli: kolonları seçip Böl / Mafsal gibi bir değiştirme işlemi ya da Hızlı kolon ile çizin).");
        const kren = { tekerlek: { P_maks: sayi(o.Pmaks), P_min: sayi(o.Pmin), H_yanal: sayi(o.Hy), H_fren: sayi(o.Hf), aralik: sayi(o.ara), adet: 2 }, dinamik: sayi(o.din) || 1.25 };
        const r = MOp.krenYoluUret(p.model, p.kolonlar, sayi(o.kot), sayi(o.konsol) || 0, kes, kren);
        r.uyarilar = (p.eklenen.length ? ["Eklenen akslar: " + p.eklenen.join(", ") + "."] : []).concat(r.uyarilar || []);
        return { model: r.model, rapor: r, gorunum: { tur: "cephe", x: o.h1 }, ozet: (r.kirisler || []).length + " kren kirişi, " + (r.konsollar || []).length + " konsol", uyarilar: r.uyarilar };
      }, "Kren yolunu üret");
    }

    // ---------------------------------------------------------------- değiştirme iletişim kutuları
    function secimCubukSayisi() { const a = secimAyir(MB.secim()); return a.cubuklar.length + a.aksKat.filter(function (s) { return s.tur !== "doseme"; }).length; }
    function bolPenceresi() {
      if (!secimCubukSayisi()) { toast("Bölmek için çubuk seçin (Seç aracıyla dokunun)."); return; }
      const ay = secimAyir(MB.secim());
      const nok = ay.cubuklar.length === 1 ? bolmeNoktalari(B(), ay.cubuklar[0]) : [];
      const k = MB.kaplamaAc("bol", "Böl (" + secimCubukSayisi() + " çubuk)", { kucuk: true, odak: "[data-a=parca]" });
      k.govde.innerHTML = '<div class="bc-yontem" role="radiogroup" aria-label="Bölme yöntemi">' +
        '<label class="bn-onay"><input type="radio" name="bc-bol" value="parca" checked> Eşit parça</label>' + alan("Parça sayısı n", girdi("parca", "4", ' inputmode="numeric"')) +
        '<label class="bn-onay"><input type="radio" name="bc-bol" value="uzunluk"> Parça uzunluğu</label>' + '<div class="bn-iki">' + alan("Uzunluk (m)", girdi("uzunluk", "1.5", ' inputmode="decimal"')) + alan("Başlangıç", sec("bastan", [["bas", "i ucundan"], ["son", "j ucundan"]], "bas")) + "</div>" +
        '<label class="bn-onay"><input type="radio" name="bc-bol" value="oran"> Oranlarda (0–1, i ucundan)</label>' + alan("Oranlar", girdi("oranlar", "0.25 0.5")) +
        (nok.length ? '<label class="bn-onay"><input type="radio" name="bc-bol" value="nokta"> Aks kesişimlerinde</label><div class="bc-cipler">' + nok.map(function (n, i) { return onay("n" + i, n.ad + " (t = " + fmtK(n.t) + ")", true); }).join("") + "</div>" : "") +
        "</div>" + '<p class="not">Yeni düğümler bölme düğümüdür (ana çubuğun uçlarına göre oran; aks taşınınca birlikte taşınır). Yükler parçalara paylaştırılır.</p>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Böl</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const o = oku(k.govde), y = (k.govde.querySelector("input[name=bc-bol]:checked") || {}).value || "parca";
        let s;
        if (y === "parca") { const n = Math.round(sayi(o.parca) || 0); if (!(n >= 2 && n <= 100)) { toast("Parça sayısı 2–100 olmalı."); return; } s = { parca: n }; }
        else if (y === "uzunluk") { const u = sayi(o.uzunluk); if (!(u > 0)) { toast("Uzunluk pozitif olmalı."); return; } s = { uzunluk: u, bastan: o.bastan !== "son" }; }
        else if (y === "oran") { const l = String(o.oranlar).trim().split(/[\s;]+/).map(sayi).filter(function (v) { return v != null; }); if (!l.length) { toast("En az bir oran girin."); return; } s = { oranlar: l }; }
        else s = { noktalar: nok.filter(function (n, i) { return o["n" + i]; }).map(function (n) { return n.P; }) };
        MB.kaplamaKapat();
        secimli("Bölündü", function (m, a) {
          let mm = m, parca = [];
          a.cubuklar.forEach(function (no) { const r = MOp.bol(mm, no, s); mm = r.model; parca = parca.concat(r.parcalar || []); });
          return { model: mm, eklenen: { cubuklar: parca.filter(function (n) { return a.cubuklar.indexOf(n) < 0; }) }, silinen: {}, degisen: {}, uyarilar: [], parcalar: parca };
        }, { secim: function (r) { return (r.parcalar || []).map(function (no) { return { tur: "cubuk", no: no }; }); } });
      });
    }
    function birlestirIslem(nolar) {
      const sec0 = nolar ? null : MB.secim();
      const f = function (m, a) {
        const r = MOp.birlestir(m, nolar || a.cubuklar);
        const red = (r.reddedilen || []).map(function (x) { return "çubuk " + (x.cubuklar || []).join(", ") + ": " + x.sebep; });
        if (red.length) r.uyarilar = (r.uyarilar || []).concat(["Birleştirilmeyen: " + red.join("; ") + "."]);
        if (!(r.birlesen || []).length) r.reddedildi = true;
        return r;
      };
      if (nolar) return uygula(function (m) { return f(m, null); }, "Birleştirildi", { secim: function (r) { return (r.birlesen || []).map(function (x) { return { tur: "cubuk", no: x.no != null ? x.no : x }; }); } });
      void sec0;
      return secimli("Birleştirildi", f, { secim: function (r) { return (r.birlesen || []).map(function (x) { return { tur: "cubuk", no: x.no != null ? x.no : x }; }); } });
    }
    const SERB = ["N", "Vy", "Vz", "T", "My", "Mz"];
    function mafsalPenceresi(hedef) {
      if (hedef) MB.seciliAyarla([hedef]);
      if (!secimCubukSayisi()) { toast("Mafsal atamak için çubuk seçin."); return; }
      const k = MB.kaplamaAc("mafsal", "Uç serbestlikleri (" + secimCubukSayisi() + " çubuk)", { kucuk: true });
      k.govde.innerHTML = '<div class="bc-yontem" role="radiogroup" aria-label="Ön ayar">' + Object.keys(MAFSAL_ON_AYAR).map(function (id, i) {
        return '<label class="bn-onay"><input type="radio" name="bc-maf" value="' + id + '"' + (i === 0 ? " checked" : "") + "> " + kacis(MAFSAL_ON_AYAR[id].ad) + "</label>";
      }).join("") + '<label class="bn-onay"><input type="radio" name="bc-maf" value="ozel"> Özel</label></div>' +
        '<table class="se-tablo bc-tablo"><thead><tr><th>Uç</th>' + SERB.map(function (s) { return "<th>" + s + "</th>"; }).join("") + "</tr></thead><tbody>" +
        ["i", "j"].map(function (u) { return "<tr><td>" + u + "</td>" + SERB.map(function (s) { return '<td><input type="checkbox" data-a="' + u + "_" + s + '" aria-label="' + u + " ucu " + s + ' serbest"></td>'; }).join("") + "</tr>"; }).join("") +
        '</tbody></table><p class="not">İşaretli iç kuvvet o uçta sıfır (serbest). Mafsal = My + Mz. Aynı serbestlik iki uçta birden (N, T, Vy, Vz) mekanizma yapar.</p>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Uygula</button></div>';
      const kutular = function (on) { SERB.forEach(function (s) { ["i", "j"].forEach(function (u) { const c = k.govde.querySelector('[data-a="' + u + "_" + s + '"]'); c.checked = on[u].indexOf(s) >= 0; }); }); };
      kutular(MAFSAL_ON_AYAR["iki-uc"]);
      k.govde.addEventListener("change", function (e) {
        if (e.target.name === "bc-maf" && MAFSAL_ON_AYAR[e.target.value]) kutular(MAFSAL_ON_AYAR[e.target.value]);
        else if (e.target.getAttribute("data-a")) { const r = k.govde.querySelector('input[name=bc-maf][value="ozel"]'); if (r) r.checked = true; }
      });
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const o = oku(k.govde), ayar = { i: [], j: [] };
        SERB.forEach(function (s) { ["i", "j"].forEach(function (u) { if (o[u + "_" + s]) ayar[u].push(s); }); });
        MB.kaplamaKapat();
        secimli("Uç serbestlikleri atandı", function (m, a) { const r = MOp.serbestlikAta(m, a.cubuklar, ayar); r.degisen = { cubuklar: a.cubuklar }; return r; },
          { secim: function (r, mm) { void mm; return secimAyir(MB.secim()).cubuklar.length ? MB.secim() : undefined; } });
      });
    }
    function ozellikPenceresi() {
      const b = B(), ay = secimAyir(MB.secim());
      const c0 = ay.cubuklar.length ? liste(b, "cubuklar").filter(function (c) { return +c.no === ay.cubuklar[0]; })[0] : null;
      if (!secimCubukSayisi()) return false;
      const k = MB.kaplamaAc("ozellik-ata", "Özellik ata (" + secimCubukSayisi() + " çubuk)", { kucuk: true });
      const satir = function (ad, etiket, ic) { return '<div class="bc-oz-satir">' + onay("d_" + ad, etiket, false) + ic + "</div>"; };
      const turler = [["kolon", "Kolon"], ["kiris", "Kiriş"], ["capraz", "Çapraz"], ["makas-ust", "Makas üst başlık"], ["makas-alt", "Makas alt başlık"], ["makas-dikme", "Makas dikmesi"], ["makas-diyagonal", "Makas diyagonali"], ["asik", "Aşık"], ["kren", "Kren kirişi"], ["bag", "Bağ"], ["diger", "Diğer"]];
      k.govde.innerHTML = '<p class="not">İşaretli alanlar seçili bütün çubuklara uygulanır.</p>' +
        satir("kesit", "Kesit", sec("kesit", kesitListesi(b, "kiris"), c0 && c0.kesit)) + satir("tur", "Tür", sec("tur", turler, c0 ? c0.tur || "diger" : "diger")) +
        satir("aci", "Yerel eksen açısı (°)", girdi("aci", c0 && c0.aci != null ? c0.aci : 0, ' inputmode="decimal"')) + satir("grup", "Grup", girdi("grup", c0 && c0.grup || "")) +
        satir("Lb", "Lb (m; boş = otomatik)", girdi("Lb", c0 && c0.Lb != null ? c0.Lb : "", ' inputmode="decimal"')) + satir("K", "K güçlü / zayıf", girdi("K", c0 && Array.isArray(c0.K) ? c0.K.join(" ") : "1 1")) +
        satir("yc", "Yalnız çekme", onay("yalniz_cekme", "açık", !!(c0 && c0.yalniz_cekme))) +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Uygula</button></div>';
      k.govde.addEventListener("input", function (e) { const a = e.target.getAttribute("data-a"); if (a && a.indexOf("d_") !== 0) { const d = k.govde.querySelector('[data-a="d_' + (a === "yalniz_cekme" ? "yc" : a) + '"]'); if (d) d.checked = true; } });
      k.govde.addEventListener("change", function (e) { const a = e.target.getAttribute("data-a"); if (a && a.indexOf("d_") !== 0) { const d = k.govde.querySelector('[data-a="d_' + (a === "yalniz_cekme" ? "yc" : a) + '"]'); if (d) d.checked = true; } });
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const o = oku(k.govde), oz = {};
        try {
          if (o.d_kesit) oz.kesit = o.kesit;
          if (o.d_tur) oz.tur = o.tur;
          if (o.d_aci) { const v = sayi(o.aci); if (v == null) throw new Error("Açı sayı olmalı."); oz.aci = v; }
          if (o.d_grup) oz.grup = String(o.grup).trim() || null;
          if (o.d_Lb) { if (String(o.Lb).trim() === "") oz.Lb = null; else { const v = sayi(o.Lb); if (!(v > 0)) throw new Error("Lb pozitif olmalı."); oz.Lb = v; } }
          if (o.d_K) { const l = String(o.K).trim().split(/[\s;]+/).map(sayi); if (!l.length || l.some(function (v) { return !(v > 0); })) throw new Error("K iki pozitif sayı olmalı."); oz.K = [l[0], l[1] != null ? l[1] : l[0]]; }
          if (o.d_yc) oz.yalniz_cekme = o.yalniz_cekme ? true : null;
        } catch (e) { hata(e); return; }
        if (!Object.keys(oz).length) { toast("Değiştirilecek alanı işaretleyin."); return; }
        MB.kaplamaKapat();
        secimli("Özellikler atandı", function (m, a) { const r = MOp.ozellikAta(m, a.cubuklar, oz); r.degisen = { cubuklar: a.cubuklar }; return r; }, { bagla: false });
      });
      return true;
    }
    function kesitPenceresi() {
      if (!secimCubukSayisi()) { toast("Kesit değiştirmek için çubuk seçin."); return; }
      const b = B(), pl = profilListesi();
      const k = MB.kaplamaAc("kesit-degistir", "Kesit değiştir (" + secimCubukSayisi() + " çubuk)", { kucuk: true });
      k.govde.innerHTML = alan("Modeldeki kesit", sec("kesit", [["", "—"]].concat(kesitListesi(b, "kiris")), "")) +
        (b.sistem === "celik" && pl.length ? alan("ya da katalog profili", sec("profil", [["", "—"]].concat(pl.map(function (p) { return [p, p]; })), "")) : "") +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Uygula</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const o = oku(k.govde);
        let ad = o.kesit, tanim = null;
        if (o.profil) { ad = String(o.profil).replace(/\s+/g, ""); tanim = { tip: "profil", profil: o.profil, malzeme: Object.keys(b.malzemeler || {}).filter(function (x) { return /^S\d/.test(x); })[0] || "S275" }; }
        if (!ad) { toast("Bir kesit seçin."); return; }
        MB.kaplamaKapat();
        secimli("Kesit " + ad + " atandı", function (m, a) {
          const mm = kopya(m);
          if (tanim && !(mm.kesitler || {})[ad]) { mm.kesitler = mm.kesitler || {}; mm.kesitler[ad] = tanim; if (!mm.malzemeler) mm.malzemeler = {}; if (!mm.malzemeler[tanim.malzeme]) mm.malzemeler[tanim.malzeme] = { kutuphane: tanim.malzeme }; }
          const r = MOp.ozellikAta(mm, a.cubuklar, { kesit: ad }); r.degisen = { cubuklar: a.cubuklar }; return r;
        }, { bagla: false });
      });
    }
    function aciPenceresi() {
      if (!secimCubukSayisi()) { toast("Yerel eksen açısı için çubuk seçin."); return; }
      const k = MB.kaplamaAc("aci", "Yerel eksen açısı", { kucuk: true, odak: "[data-a=aci]" });
      k.govde.innerHTML = alan("Açı (°; x′ çevresinde, sağ el kuralı)", girdi("aci", "90", ' inputmode="decimal"')) + '<p class="not">0°: kesitin h boyutu (güçlü eksen) y′ doğrultusunda; kolonda 90° kesiti çevirir.</p>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Uygula</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const v = sayi(oku(k.govde).aci);
        if (v == null) { toast("Açı sayı olmalı."); return; }
        MB.kaplamaKapat();
        secimli("Açı " + fmtK(v) + "° atandı", function (m, a) { const r = MOp.ozellikAta(m, a.cubuklar, { aci: v }); r.degisen = { cubuklar: a.cubuklar }; return r; }, { bagla: false });
      });
    }
    function duzlemleBolPenceresi() {
      if (!secimCubukSayisi()) { toast("Düzlemle bölmek için çubuk seçin."); return; }
      const l = [];
      ["x", "y", "z"].forEach(function (y) { aksListesi(B(), y).forEach(function (a) { l.push([y + "|" + a.ad, y.toUpperCase() + " aksı " + a.ad + " (" + fmtK(a.konum) + " m)"]); }); });
      const k = MB.kaplamaAc("duzlemle-bol", "Düzlemle böl", { kucuk: true });
      k.govde.innerHTML = alan("Aks düzlemi", sec("d", l, l[0] && l[0][0])) + '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Böl</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const p = oku(k.govde).d.split("|"), a = aksListesi(B(), p[0]).filter(function (x) { return x.ad === p[1]; })[0];
        if (!a) return;
        const d = {}; d[p[0].toUpperCase()] = a.konum;
        MB.kaplamaKapat();
        secimli(p[0].toUpperCase() + " aksı " + a.ad + " düzleminde bölündü", function (m, ay) { return MOp.duzlemleBol(m, ay.cubuklar, d); });
      });
    }
    function dugumBirlestirPenceresi() {
      const k = MB.kaplamaAc("dugum-birlestir", "Düğümleri birleştir", { kucuk: true, odak: "[data-a=tol]" });
      k.govde.innerHTML = alan("Tolerans (m)", girdi("tol", "0.001", ' inputmode="decimal"')) + '<p class="not">Tolerans içindeki çakışık düğümler tek düğümde toplanır (aks kesişimi önceliklidir); sıfır boylu çubuklar silinir.</p>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Birleştir</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const t = sayi(oku(k.govde).tol);
        if (!(t > 0 && t <= 1)) { toast("Tolerans 0 ile 1 m arasında olmalı."); return; }
        MB.kaplamaKapat();
        uygula(function (m) { const r = MOp.dugumleriBirlestir(m, t); if (!(r.birlesen || []).length) { r.uyarilar = ["Birleştirilecek çakışık düğüm yok."]; r.reddedildi = true; } return r; }, "Düğümler birleştirildi");
      });
    }
    function yukPenceresi(h) {
      const b = B();
      const ad = h.tur === "cubuk" ? "Çubuk " + h.no : h.tur === "panel" ? "Panel " + h.no : "Düğüm " + (h.etiket || "");
      const k = MB.kaplamaAc("yuk", "Yük: " + ad, { kucuk: true });
      const mevcut = liste(b, "ek_yukler").map(function (y, i) { return [y, i]; }).filter(function (x) {
        const y = x[0];
        if (h.tur === "cubuk") return y.tur === "cubuk" && +y.cubuk === +h.no;
        if (h.tur === "panel") return y.tur === "panel" && +y.panel === +h.no;
        return y.tur === "dugum" && JSON.stringify(y.dugum) === JSON.stringify(h.ref);
      });
      let f = alan("Yük durumu", sec("durum", [["G", "G — sabit"], ["Q", "Q — hareketli"], ["S", "S — kar"]], S.yuk));
      if (h.tur === "cubuk") {
        f += alan("Biçim", sec("bicim", [["yayili", "Yayılı (kN/m)"], ["tekil", "Tekil (kN)"]], "yayili")) +
          '<div class="bn-iki">' + alan("Yön", sec("yon", [["Z", "Z (global, yukarı +)"], ["X", "X"], ["Y", "Y"], ["z′", "z′ (yerel)"], ["y′", "y′ (yerel)"], ["x′", "x′ (eksenel)"]], "Z")) + alan("q₁ ya da P (aşağı yük −)", girdi("q1", "-2", ' inputmode="decimal"')) + "</div>" +
          '<div class="bn-iki">' + alan("q₂ (boş = q₁)", girdi("q2", "", ' inputmode="decimal"')) + alan("Tekil yükün yeri x (m)", girdi("x", "", ' inputmode="decimal"')) + "</div>" + onay("izdusum", "Yatay izdüşüm başına (kar, hareketli)", false);
      } else if (h.tur === "panel") {
        f += '<div class="bn-iki">' + alan("Ek sabit g (kN/m²)", girdi("g", "0.5", ' inputmode="decimal"')) + alan("Ek hareketli q (kN/m²)", girdi("q", "", ' inputmode="decimal"')) + "</div>";
      } else {
        f += '<div class="bn-iki">' + alan("FX (kN)", girdi("FX", "", ' inputmode="decimal"')) + alan("FY (kN)", girdi("FY", "", ' inputmode="decimal"')) + "</div>" +
          '<div class="bn-iki">' + alan("FZ (kN; aşağı −)", girdi("FZ", "-10", ' inputmode="decimal"')) + alan("MZ (kN·m)", girdi("MZ", "", ' inputmode="decimal"')) + "</div>";
      }
      k.govde.innerHTML = (mevcut.length ? "<h3>Mevcut yükler</h3><ul class=\"bc-yukler\">" + mevcut.map(function (x) {
        const y = x[0];
        return "<li>" + kacis(y.durum + ": " + (y.tur === "cubuk" ? (y.P != null ? "P = " + fmtK(+y.P) + " kN (x = " + fmtK(+y.x) + ")" : "q = " + fmtK(+y.q1) + (y.q2 != null && +y.q2 !== +y.q1 ? "…" + fmtK(+y.q2) : "") + " kN/m, " + y.yon) :
          y.tur === "panel" ? (y.g ? "g = " + fmtK(+y.g) + " " : "") + (y.q ? "q = " + fmtK(+y.q) : "") + " kN/m²" : ["FX", "FY", "FZ", "MX", "MY", "MZ"].filter(function (a) { return y[a]; }).map(function (a) { return a + " = " + fmtK(+y[a]); }).join(", "))) +
          ' <button type="button" class="se-sil" data-yuk-sil="' + x[1] + '" aria-label="Yükü sil">✕</button></li>';
      }).join("") + "</ul>" : "") + "<h3>Yeni yük</h3>" + f + '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Ekle</button></div>';
      k.govde.addEventListener("click", function (e) {
        const s = e.target.closest("[data-yuk-sil]");
        if (s) {
          const i = +s.getAttribute("data-yuk-sil");
          const m = kopya(B()); m.ek_yukler.splice(i, 1);
          MB.kaplamaKapat(); MB.binaAyarla(m, { etiket: "Yük silindi." });
          return;
        }
        if (!e.target.closest("[data-tamam]")) return;
        const o = oku(k.govde);
        let yuk;
        if (h.tur === "cubuk") yuk = o.bicim === "tekil" ? { durum: o.durum, yon: o.yon, P: o.q1, x: o.x || 0 } : { durum: o.durum, yon: o.yon, q1: o.q1, q2: o.q2, izdusum: !!o.izdusum };
        else if (h.tur === "panel") yuk = { durum: o.durum, g: o.g, q: o.q };
        else yuk = { durum: o.durum, FX: o.FX, FY: o.FY, FZ: o.FZ, MZ: o.MZ };
        S.yuk = o.durum;
        let r;
        try { r = yukEkle(B(), h, yuk); } catch (x) { hata(x); return; }
        MB.kaplamaKapat();
        MB.binaAyarla(r.model, { etiket: ad + ": " + o.durum + " yükü eklendi." });
      });
    }
    // kesit önerisi (köprüde bina_kesit_oner varsa; genel model motoru)
    function kesitOner(hedef) {
      MB.motorS3().then(function (var_) {
        if (!var_) { toast("Kesit önerisi bu kurulumdaki motorda yok (genel model motoru gerekir); uygulamayı güncelleyin."); return; }
        const A = window.MatrisApp;
        const k = MB.kaplamaAc("kesit-oner", "Kesit önerisi", { kucuk: true });
        k.govde.innerHTML = '<p class="not bn-bekle" role="status"><span class="bn-donen" aria-hidden="true"></span> Çözüm ve öneri hesaplanıyor…</p>';
        const tur = hedef.tur === "kolon" || hedef.tur === "kiris" || hedef.tur === "cubuk" ? hedef.tur : "cubuk";
        const girdi_ = MB.cozumKimligi() ? { cozum_kimligi: MB.cozumKimligi(), hedef: [{ tur: tur, no: hedef.no }], bina: B() } : { bina: B(), hedef: [{ tur: tur, no: hedef.no }] };
        Promise.resolve(A.motorIstegi({ islem: "bina_kesit_oner", girdi: girdi_ })).then(function (y) {
          if (!k.govde.isConnected) return;
          if (!y || y.hata) { k.govde.innerHTML = '<p class="bc-hata">' + kacis((y && y.hata) || "Boş yanıt.") + "</p>"; return; }
          const l = y.oneriler || [];
          if (!l.length) { k.govde.innerHTML = '<p class="not">Öneri yok: kesit yeterli ya da hesaplanamadı.</p>'; return; }
          k.govde.innerHTML = l.map(function (o, i) {
            return '<div class="bc-oneri"><p><b>' + kacis((o.tur || "") + " " + (o.cubuk != null ? o.cubuk : "")) + "</b>: " + kacis(o.kesit || "?") + " → <b>" + kacis(o.oneri || "—") + "</b> (D/C " + fmt(o.dc_once) + " → " + fmt(o.dc_oneri) + ")</p>" +
              "<ul>" + (o.gerekce || []).map(function (g) { return "<li>" + kacis(g) + "</li>"; }).join("") + "</ul>" +
              (o.oneri && o.oneri !== o.kesit ? '<button type="button" class="dugme kucuk ana" data-oneri="' + i + '">Uygula</button>' : "") + "</div>";
          }).join("");
          k.govde.addEventListener("click", function (e) {
            const t = e.target.closest("[data-oneri]");
            if (!t) return;
            const o = l[+t.getAttribute("data-oneri")], b = B(), m = kopya(b);
            const profil = /^[A-Z]+\s*\d/.test(String(o.oneri)) && !/x/i.test(String(o.oneri).replace(/^[A-Z]+\s*/, "")) ? String(o.oneri) : null;
            let ad = String(o.oneri).replace(/\s+/g, "");
            if (!m.kesitler[ad]) {
              if (profil) m.kesitler[ad] = { tip: "profil", profil: profil, malzeme: (m.kesitler[o.kesit] || {}).malzeme || "S275" };
              else { const bh = String(o.oneri).split(/x/i).map(sayi); if (bh.length === 2 && bh.every(function (v) { return v > 0; })) { ad = "K" + bh[0] + "x" + bh[1]; m.kesitler[ad] = Object.assign({}, m.kesitler[o.kesit] || { tip: "dikdortgen", malzeme: "C30" }, { b: bh[0] / 100, h: bh[1] / 100 }); } }
            }
            MB.kaplamaKapat();
            if (hedef.tur === "kolon" || hedef.tur === "kiris") {
              const n = liste(m, hedef.tur === "kolon" ? "kolonlar" : "kirisler").filter(function (x) { return +x.no === +hedef.no; })[0];
              if (n) n.kesit = ad;
              MB.binaAyarla(m, { etiket: "Kesit " + ad + " uygulandı." });
            } else uygula(function () { const r = MOp.ozellikAta(m, [+o.cubuk || +hedef.no], { kesit: ad }); r.degisen = { cubuklar: [+hedef.no] }; return r; }, "Kesit " + ad + " uygulandı", { bagla: false });
          });
        }, function (e) { if (k.govde.isConnected) k.govde.innerHTML = '<p class="bc-hata">' + kacis((e && e.message) || String(e)) + "</p>"; });
      });
    }
    // bir çubuğun eş doğrusal, uç uca komşuları (sağ tık → Birleştir)
    function esDogrusalZincir(no) {
      const b = B(), cz = new MAk.Cozucu(b), l = liste(b, "cubuklar");
      const uc = new Map();
      l.forEach(function (c) { try { uc.set(+c.no, [cz.coz(c.i), cz.coz(c.j)]); } catch (e) { /* yoksay */ } });
      const u0 = uc.get(+no);
      if (!u0) return [no];
      const d = [u0[1][0] - u0[0][0], u0[1][1] - u0[0][1], u0[1][2] - u0[0][2]], L = Math.hypot(d[0], d[1], d[2]);
      const es = function (u) {
        const e = [u[1][0] - u[0][0], u[1][1] - u[0][1], u[1][2] - u[0][2]], M = Math.hypot(e[0], e[1], e[2]);
        const cr = Math.hypot(d[1] * e[2] - d[2] * e[1], d[2] * e[0] - d[0] * e[2], d[0] * e[1] - d[1] * e[0]);
        if (cr > 1e-6 * L * M) return false;
        const v = [u[0][0] - u0[0][0], u[0][1] - u0[0][1], u[0][2] - u0[0][2]];
        return Math.hypot(d[1] * v[2] - d[2] * v[1], d[2] * v[0] - d[0] * v[2], d[0] * v[1] - d[1] * v[0]) / L < TOL;
      };
      const sec_ = new Set([+no]);
      let degisti = true;
      while (degisti) {
        degisti = false;
        uc.forEach(function (u, n) {
          if (sec_.has(n) || !es(u)) return;
          for (const m of sec_) { const w = uc.get(m); if ([0, 1].some(function (a) { return [0, 1].some(function (c) { return uzaklik(u[a], w[c]) < TOL; }); })) { sec_.add(n); degisti = true; break; } }
        });
      }
      return Array.from(sec_);
    }

    // ---------------------------------------------------------------- araç kutusu komutları
    const kipK = function (id, ek) {
      return Object.assign({ tur: "kip", secili: function () { return MB.kip() === id; }, calistir: function () { if (MB.kip() === id) { temizle(); MB.ipucuYenile(); } else MB.kipAyarla(id); } }, ek || {});
    };
    const secimGerekli = function () { return cubukSecimiVar(); };
    function ycDurum() {
      const a = secimAyir(MB.secim()), b = B();
      if (!a.cubuklar.length) return false;
      return a.cubuklar.every(function (no) { const c = liste(b, "cubuklar").filter(function (x) { return +x.no === no; })[0]; return c && c.yalniz_cekme; });
    }
    const PANEL_SEC = Object.keys(PANEL_ON_AYAR).map(function (id) { return { id: id, ad: PANEL_ON_AYAR[id].ad, ikon: "hizli-panel" }; });
    const MESNET_SEC = Object.keys(MESNET_ON_AYAR).map(function (id) { return { id: id, ad: MESNET_ON_AYAR[id].ad, ikon: "mesnet" }; });
    const YUK_SEC = [{ id: "G", ad: "G — sabit yük", ikon: "yuk-ata" }, { id: "Q", ad: "Q — hareketli yük", ikon: "yuk-ata" }, { id: "S", ad: "S — kar yükü", ikon: "yuk-ata" }];
    const AKS_SEC = [{ id: "x", ad: "X aksı (harfli)", ikon: "aks-ekle" }, { id: "y", ad: "Y aksı (sayılı)", ikon: "aks-ekle" }, { id: "z", ad: "Z aksı (kot; cephede)", ikon: "aks-ekle" }];
    const secenekli = function (id, kipId, liste_, al, ver) {
      return kipK(kipId, { secenekler: liste_, secenek: al, secenekSec: function (v) { ver(v); if (MB.kip() !== kipId) MB.kipAyarla(kipId); MB.ipucuYenile(); } });
    };
    MB.komutBagla({
      // Aks
      "aks-sihirbaz": aksSihirbazi,
      "aks-duzenle": function () { aksDuzenleyici(); },
      "aks-ekle": secenekli("aks-ekle", "aks-ekle", AKS_SEC, function () { return S.aksYon; }, function (v) { S.aksYon = v; }),
      "aks-sil": kipK("aks-sil"),
      "aks-tasi": kipK("aks-tasi"),
      "aks-sistemi": aksSistemiPenceresi,
      "aks-gorunurluk": aksGorunurlukPenceresi,
      // Çizim (yalnız aks kesişimleri, düğümler ve bölme/kesişim noktaları)
      "cubuk-ciz": kipK("cubuk-ciz"),
      "hizli-cubuk": kipK("hizli-cubuk"),
      "hizli-kolon": kipK("kolon"),
      "hizli-kiris": kipK("kiris"),
      "hizli-capraz": secenekli("hizli-capraz", "hizli-capraz", (MAr && MAr.CAPRAZ_SECENEKLERI) || MOp.CAPRAZ_TIPLERI.map(function (t) { return { id: t, ad: t, ikon: "hizli-capraz" }; }), function () { return S.capraz; }, function (v) { S.capraz = v; }),
      "hizli-panel": secenekli("hizli-panel", "doseme", PANEL_SEC, function () { return S.panel; }, function (v) { S.panel = v; }),
      "egik-cubuk": kipK("egik-cubuk"),
      makas: makasPenceresi,
      "besik-cerceve": besikPenceresi,
      asik: { calistir: asikPenceresi, etkin: function () { const a = secimAyir(MB.secim()); return a.cubuklar.length >= 2 || a.paneller.length > 0; } },
      "kren-yolu": krenPenceresi,
      mesnet: secenekli("mesnet", "mesnet", MESNET_SEC, function () { return S.mesnet; }, function (v) { S.mesnet = v; }),
      "yuk-ata": secenekli("yuk-ata", "yuk-ata", YUK_SEC, function () { return S.yuk; }, function (v) { S.yuk = v; }),
      // Düzenleme
      tasi: kipK("tasi"), dondur: kipK("dondur"), ayna: kipK("ayna"), "dogrusal-dizi": kipK("dogrusal-dizi"),
      "ozellik-ata": { tur: "eylem", calistir: function () { if (!ozellikPenceresi()) MB.firca(); }, ipucu: "Seçili çubuklara kesit / tür / açı / grup / Lb / K / yalnız çekme atar; seçim yoksa kesit fırçası (aks–kat)." },
      mafsal: { calistir: function () { mafsalPenceresi(); }, etkin: secimGerekli },
      "yalniz-cekme": { tur: "anahtar", etkin: secimGerekli, secili: ycDurum, calistir: function () {
        const ac = !ycDurum();
        secimli(ac ? "Yalnız çekme açıldı" : "Yalnız çekme kapatıldı", function (m, a) { const r = MOp.ozellikAta(m, a.cubuklar, { yalniz_cekme: ac ? true : null }); r.degisen = { cubuklar: a.cubuklar }; return r; }, { bagla: false });
      } },
      // Değiştirme
      bol: { calistir: bolPenceresi, etkin: secimGerekli },
      "kesisimde-bol": { etkin: secimGerekli, calistir: function () {
        secimli("Kesişimlerde bölündü", function (m, a) { const r = MOp.kesisimlerdeBol(m, a.cubuklar); if (!r.kesisim_sayisi) { r.uyarilar = (r.uyarilar || []).concat(["Seçili çubuklar birbirini kesmiyor (en az iki kesişen çubuk seçin)."]); r.reddedildi = true; } return r; });
      } },
      "duzlemle-bol": { calistir: duzlemleBolPenceresi, etkin: secimGerekli },
      birlestir: { calistir: function () { birlestirIslem(); }, etkin: secimGerekli },
      "dugum-birlestir": dugumBirlestirPenceresi,
      "kesit-degistir": { calistir: kesitPenceresi, etkin: secimGerekli },
      aci: { calistir: aciPenceresi, etkin: secimGerekli },
      // masaüstü menüsünün aks komutları (araç kutusunda Aks grubuna eklenebilir)
      "aks-balon": { ad: "Aks balonları", ikon: "aks-gorunurluk", grup_varsayilan: "aks", tur: "anahtar", secili: function () { return MB.ayar().aksBalon; },
        calistir: function () { MB.ayarla({ aksBalon: !MB.ayar().aksBalon }); }, ipucu: "Aks balonlarını (daire içinde ad) gösterir / gizler." },
      "aks-olcu": { ad: "Aks ölçü zinciri", ikon: "olc-uzaklik", grup_varsayilan: "aks", tur: "anahtar", secili: function () { return MB.ayar().aksOlcu; },
        calistir: function () { MB.ayarla({ aksOlcu: !MB.ayar().aksOlcu }); }, ipucu: "Plan ve cephede aks aralığı ölçü zincirini gösterir / gizler." },
      "aks-yapisik": { ad: "Akslara yapışık", ikon: "aks-tasi", grup_varsayilan: "aks", tur: "anahtar", secili: function () { return true; },
        calistir: function () { toast("Düğümler aks kesişimine ya da bölme noktasına adla bağlıdır: aks taşınınca bağlı elemanlar her zaman birlikte taşınır."); },
        ipucu: "Elemanlar akslara yapışıktır (aks taşı → elemanlar da)." },
      yakalama: { ad: "Yakalama", ikon: "cubuk-ciz", grup_varsayilan: "cizim", tur: "anahtar", secili: function () { return true; },
        calistir: function () { toast("Yakalama her zaman açık: yalnız aks kesişimleri, düğümler ve bölme / çubuk kesişim noktaları (serbest nokta yok)."); },
        ipucu: "Çizim yalnız aks kesişimlerine, düğümlere ve bölme / kesişim noktalarına yakalanır." },
    });

    // ---------------------------------------------------------------- sağ tık komutları: böl, birleştir, mafsal, kesit öner
    let s3Destek = null;
    MB.baglamKancasi(function (h, k) {
      if (["cubuk", "kolon", "kiris"].indexOf(h.tur) < 0) return k;
      if (s3Destek == null) MB.motorS3().then(function (v) { s3Destek = v; });
      k.bol = function () { MB.seciliAyarla([{ tur: h.tur, no: h.no }]); bolPenceresi(); };
      k.birlestir = { calistir: function () { if (h.tur === "cubuk") birlestirIslem(esDogrusalZincir(h.no)); else { MB.seciliAyarla([{ tur: h.tur, no: h.no }]); birlestirIslem(); } } };
      k.mafsal = function () { mafsalPenceresi({ tur: h.tur, no: h.no }); };
      k["kesit-oner"] = { calistir: function () { kesitOner(h); }, etkin: s3Destek !== false };
      return k;
    });
    // model değişince bekleyen iki noktalı işlem / zincir geçersiz olabilir (geri al)
    MB.dinle("model", function (o) { if (o && (o.etiket === "geri-al" || o.etiket === "yinele")) temizle(); });
    MB.dinle("gorunum", function () { S.parca = null; S.goz = null; tazele(); });
    MB.aracYenile();
  }

  return Object.freeze(Object.assign({}, SAF, { otomatikKur: otomatikKur, kur: function (MB) { if (!kuruldu) { kuruldu = true; kur(MB); } } }));
});
