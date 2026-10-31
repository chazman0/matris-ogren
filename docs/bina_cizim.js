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
   Bütün model değişiklikleri MatrisBina.binaAyarla ile tek geri al yığınından geçer.

   Genel model kapısı (sözleşme C1): aks–kat (surum 1) modelini genel modele (surum 3) çeviren her yol — seçimli değiştirme
   işlemleri, mesnet, çubuk/çapraz/panel çizimi, üreteçler — önce kullanıcıya sorar (genelModeleGec → genellestirHazirla;
   temeller aynen kalır: genel model motoru tekil, mütemadi ve radye temeli çözer — sözleşme C11). Model çevirmeden yapılabilenler
   aks–kat biçiminde yazılır: ek yükler (C10: düğüm, kiriş,
   döşeme), kolon/kiriş kesit, kolon yönü, kiriş duvarı. Motorun her zaman reddettiği yeni bozukluk üreten işlem uygulanmaz. */
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
   * Tam bir aks kesişimindeki koordinatlı kayıt (X, Y ve Z aksları üstünde) kesişim REF'ine çevrilir: başvuruları {aks, z} olur,
   * kayıt silinir. Eski genelleştirmenin {no, X, Y, Z, aks, kat} aks–kat düğüm kayıtları atlanır (numaraları akslardan çözülür).
   */
  function serbestleriBagla(model) {
    const m = kopya(model), A = MA();
    const xs = aksListesi(m, "x"), ys = aksListesi(m, "y"), zs = aksListesi(m, "z");
    const bul = function (l, v) { return l.filter(function (a) { return Math.abs(a.konum - v) <= TOL; })[0] || null; };
    const arasi = function (l, v) {
      for (let i = 0; i + 1 < l.length; i++) if (l[i].konum < v - TOL && l[i + 1].konum > v + TOL) return [l[i], l[i + 1]];
      return null;
    };
    const kalan = [], baglanan = [], kesisim = new Map();
    liste(m, "dugumler").forEach(function (d) {
      if (!d || d.tur || d.X == null || d.Y == null || d.Z == null) return;
      if (d.aks != null || d.kat != null) return;
      const P = [+d.X, +d.Y, +d.Z];
      const ax = bul(xs, P[0]), ay = bul(ys, P[1]), az = bul(zs, P[2]);
      if (ax && ay && az) { kesisim.set(+d.no, { aks: [ax.ad, ay.ad], z: az.ad }); return; }
      let ri = null, rj = null, t = null;
      if (az && ay) { const a = arasi(xs, P[0]); if (a) { ri = { aks: [a[0].ad, ay.ad], z: az.ad }; rj = { aks: [a[1].ad, ay.ad], z: az.ad }; t = (P[0] - a[0].konum) / (a[1].konum - a[0].konum); } }
      if (!ri && az && ax) { const a = arasi(ys, P[1]); if (a) { ri = { aks: [ax.ad, a[0].ad], z: az.ad }; rj = { aks: [ax.ad, a[1].ad], z: az.ad }; t = (P[1] - a[0].konum) / (a[1].konum - a[0].konum); } }
      if (!ri && ax && ay) { const a = arasi(zs, P[2]); if (a) { ri = { aks: [ax.ad, ay.ad], z: a[0].ad }; rj = { aks: [ax.ad, ay.ad], z: a[1].ad }; t = (P[2] - a[0].konum) / (a[1].konum - a[0].konum); } }
      if (!ri) { kalan.push(+d.no); return; }
      delete d.X; delete d.Y; delete d.Z;
      d.tur = "bolme"; d.cubuk_i = ri; d.cubuk_j = rj; d.oran = r6(t);
      baglanan.push(+d.no);
    });
    // tam kesişimdeki kayıtlar: başvurular kesişim REF'ine, kayıt silinir
    if (kesisim.size) {
      A.refleriGez(m, function (r) {
        const no = typeof r === "number" ? r : (r && typeof r === "object" && r.dugum != null ? +r.dugum : null);
        return no != null && kesisim.has(no) ? kopya(kesisim.get(no)) : r;
      });
      m.dugumler = m.dugumler.filter(function (d) { return !(d && kesisim.has(+d.no)); });
      kesisim.forEach(function (v, no) { baglanan.push(no); });
    }
    // doğrulama: yeni bölme düğümleri eski konumunda mı (aks sistemi tutarlılığı)
    const bolme = baglanan.filter(function (no) { return !kesisim.has(no); });
    if (bolme.length) { try { const cz = new A.Cozucu(m); bolme.forEach(function (no) { cz.coz({ dugum: no }); }); } catch (e) { return { model: model, baglanan: [], kalan: kalan.concat(baglanan) }; } }
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
   * Makas planı. p = {tip, bas: REF, son: REF (aynı Z aksında iki kesişim), yukseklik (m; beşik tiplerde mahya yüksekliği), goz, kesitler, uc_yukseklik?, mafsalli_govde?,
   *   yanal_tutma? ("uc-dikme" varsayılan: uç dikmeleri / ilk-son diyagonaller rijit, düzlem dışı mekanizma olmaz | "yok": bütün gövde mafsallı)}
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
    if (p.yanal_tutma != null && p.yanal_tutma !== "") par.yanal_tutma = String(p.yanal_tutma) === "yok" ? "yok" : "uc-dikme";
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

  // ================================================================= genel model kapısı (aks–kat → surum 3)
  /**
   * Sözleşme C1 / K2 — tek "genel model" kuralı (motor yapi._serbest_mi ve bina.js s3Var ile aynı): surumSayi(surum) ≥ 3, ya da cubuklar / paneller /
   * dugumler / mesnetler / uretecler listelerinden biri dolu, ya da bir ek yükün `dugum` değeri REF nesnesi ya da türü (kırpılmış, küçük
   * harfe çevrilmiş) cubuk / panel.
   * Aks–kat düğüm yükü {tur: "dugum", aks: [x, y], kat} genel sayılmaz.
   */
  function genelMi(b) {
    if (!b || typeof b !== "object" || Array.isArray(b)) return false;
    if (surumSayi(b.surum) >= 3) return true;
    if (["cubuklar", "paneller", "dugumler", "mesnetler", "uretecler"].some(function (k) { return Array.isArray(b[k]) && b[k].length > 0; })) return true;
    return liste(b, "ek_yukler").some(function (y) {
      if (!y || typeof y !== "object" || Array.isArray(y)) return false;
      const d = y.dugum, t = String(y.tur == null ? "" : y.tur).trim().toLowerCase();
      return (!!d && typeof d === "object" && !Array.isArray(d)) || t === "cubuk" || t === "panel";
    });
  }
  /**
   * Sözleşme K2 — surum alanının sayısı (motor yapi._serbest_mi ve bina.js s3Var / binaYukle ile aynı): bool → 1; sonlu sayı → tam kısmı
   * (2.9 → 2); /^\s*[+-]?\d+(\.\d+)?\s*$/ dizesi → tam kısmı ("3.0" → 3, " 3.5 " → 3); öteki her şey → 1 ("3a", "0x3", "1e1", null).
   */
  function surumSayi(s) {
    if (typeof s === "boolean") return 1;
    if (typeof s === "number") return isFinite(s) ? Math.trunc(s) : 1;
    if (typeof s === "string" && /^\s*[+-]?\d+(\.\d+)?\s*$/.test(s)) return Math.trunc(parseFloat(s));
    return 1;
  }
  /** Modelde aks–kat elemanı (kolon / kiriş / döşeme) var mı. */
  function aksKatElemanVar(b) { return liste(b, "kolonlar").length + liste(b, "kirisler").length + liste(b, "dosemeler").length > 0; }
  /** Genel model gerektiren bir işlemden önce modelin çevrilmesi (ve kullanıcıya sorulması) gerekiyor mu. */
  function genelGecisGerekli(b) { return !!b && (!genelMi(b) || aksKatElemanVar(b)); }
  /**
   * Çevirme onayı metni. islem: işlemin ADI (ad / eylem adı: "Taşıma", "Mesnet", "Böl" — GENEL_ISLEM_ADLARI; geçmiş zamanlı sonuç
   * etiketi değil); verilmezse ön ek yazılmaz. Temel tipi (tekil / mütemadi / radye) çevirmede değişmez (C11), metinde geçmez.
   */
  function genelGecisMetni(b, islem) {
    void b;
    return (islem ? islem + " — " : "") + "Model genel (surum 3) modele çevrilecek: kolon/kiriş/döşemeler çubuk ve panel olur, adım adım anlatım kısalır. Devam edilsin mi?";
  }
  /**
   * Genel model kapısının işlem adları (K-23): her komutun onay metnindeki ön eki — ad ya da eylem adı ("Taşıma"), geçmiş zamanlı
   * sonuç etiketi ("Taşındı") değil. Arayüz kapıdan geçen her uygula() / secimli() çağrısına bunlardan birini sc.genel olarak verir.
   */
  const GENEL_ISLEM_ADLARI = Object.freeze({
    tasi: "Taşıma", dondur: "Döndürme", ayna: "Ayna", "dogrusal-dizi": "Dizi", yapistir: "Yapıştır", bol: "Böl", "kesisimde-bol": "Kesişimde böl",
    "duzlemle-bol": "Düzlemle böl", birlestir: "Birleştirme", mafsal: "Mafsal", "dugum-birlestir": "Düğüm birleştir", mesnet: "Mesnet", "yuk-ata": "Yük ata",
    "ozellik-ata": "Özellik ata", "kesit-degistir": "Kesit değiştir", aci: "Yerel eksen açısı", "yalniz-cekme": "Yalnız çekme",
    "cubuk-ciz": "Çubuk çiz", "egik-cubuk": "Eğik çubuk", "hizli-cubuk": "Hızlı çubuk", "hizli-kolon": "Hızlı kolon", "hizli-kiris": "Hızlı kiriş",
    "hizli-panel": "Hızlı panel", "hizli-capraz": "Hızlı çapraz", makas: "Makas üreteci", "besik-cerceve": "Beşik çerçeve", asik: "Aşık üreteci",
    "kren-yolu": "Kren yolu", uretec: "Üreteç",
  });
  /**
   * ModelOps.genellestir'in arayüz sarmalı: aks–kat elemanları çubuk/panel olur (surum 3). temeller aynen kalır (sözleşme C11: genel
   * model motoru mütemadi ve radye temeli de çözer). Dönüş: {model, notlar: [metin], temelDegisti: false (API uyumu), rapor}
   */
  function genellestirHazirla(model) {
    const r = MO().genellestir(model);
    const m = r.model, notlar = [];
    const g = (r.uyarilar || []).filter(function (u) { return /genelleştirildi/.test(u); });
    if (g.length) notlar.push(g.join(" "));
    else if (!genelMi(model)) notlar.push("Model genel (surum 3) modele çevrildi.");
    m.surum = 3;
    return { model: m, notlar: notlar, temelDegisti: false, rapor: r };
  }
  /** Aks–kat düğüm adresi {aks: [x, y], kat} (GLOBAL kat düzlemindeki kesişim); değilse null. ref: {aks, kat} | {aks, z} | {dugum: no < 100001} */
  function aksKatAdresi(bina, ref) {
    if (typeof ref === "number") ref = { dugum: ref };
    if (!ref || typeof ref !== "object" || (ref.sistem && ref.sistem !== "GLOBAL")) return null;
    const katVar = function (k) { const l = liste(bina, "katlar"); return isFinite(k) && (!l.length || l.some(function (x) { return +x.no === +k; })); };
    if (Array.isArray(ref.aks) && ref.aks.length === 2) {
      let kat = null;
      if (ref.kat != null) kat = +ref.kat;
      else if (ref.z != null) { try { kat = MA().zAksiKati(bina, ref.z); } catch (e) { kat = null; } }
      if (kat == null || !katVar(kat)) return null;
      const xs = aksListesi(bina, "x"), ys = aksListesi(bina, "y");
      if (!xs.some(function (a) { return a.ad === String(ref.aks[0]); }) || !ys.some(function (a) { return a.ad === String(ref.aks[1]); })) return null;
      return { aks: [String(ref.aks[0]), String(ref.aks[1])], kat: +kat };
    }
    if (ref.dugum != null) {
      const n = +ref.dugum;
      if (!(n > 0 && n < 100001)) return null;
      const kat = Math.floor(n / 1000), r = n - 1000 * kat - 1, ix = Math.floor(r / 20), iy = r % 20;
      const xs = aksListesi(bina, "x"), ys = aksListesi(bina, "y");
      if (r < 0 || !xs[ix] || !ys[iy] || !katVar(kat)) return null;
      return { aks: [xs[ix].ad, ys[iy].ad], kat: kat };
    }
    return null;
  }
  /** {aks, kat} REF'i → {aks, z} (katın Z aksı adıyla; modelde akslar.z varsa — yoksa {aks, kat} her yerde geçerlidir); öbürleri aynen. */
  function aksRefZ(bina, ref) {
    if (!ref || typeof ref !== "object" || !Array.isArray(ref.aks) || ref.kat == null || ref.z != null) return kopya(ref);
    if (!(bina && bina.akslar && Array.isArray(bina.akslar.z) && bina.akslar.z.length)) return kopya(ref);
    let z = null;
    try { z = MA().katZAksi(bina, ref.kat); } catch (e) { z = null; }
    if (!z) return kopya(ref);
    const r = { aks: ref.aks.map(String), z: String(z.ad) };
    if (ref.sistem && ref.sistem !== "GLOBAL") r.sistem = ref.sistem;
    return r;
  }
  /** Genelleştirilmiş modelde çubuğun aks–kat adı ("kiriş 3", "kolon 2", çok parçalıysa "kiriş 1, 2. parça"); yoksa null. */
  function cubukAksKatAdi(model, no) {
    const l = liste(model, "cubuklar"), c = l.filter(function (x) { return x && +x.no === +no; })[0];
    const k = c && c.kaynak;
    if (!k || (k.aks_kat !== "kolon" && k.aks_kat !== "kiris")) return null;
    const ad = (k.aks_kat === "kolon" ? "kolon " : "kiriş ") + k.no;
    const parca = l.filter(function (x) { return x && x.kaynak && x.kaynak.aks_kat === k.aks_kat && +x.kaynak.no === +k.no; }).length;
    return parca > 1 && k.parca != null ? ad + ", " + k.parca + ". parça" : ad;
  }
  /**
   * İletideki çubuk numaralarının yanına aks–kat adresi: "Çubuk 13, 14 …" → "Çubuk 13 (kiriş 1), 14 (kiriş 2) …"; ayraçlı liste de
   * ("başka çubuk bağlı (3, 9, 18)" → "(3 (kiriş 1), 9 (…), 18 (…))"; "çubuk" sözcüğünden sonra en çok 40 ayraçsız karakter). Listede
   * virgülden sonra boşluk aranır: ondalık sayı ("(0,5 mm)") liste sayılmaz.
   */
  function cubukAdlari(model, metin) {
    const adla = function (n) { const a = cubukAksKatAdi(model, n); return a ? n + " (" + a + ")" : n; };
    return String(metin == null ? "" : metin)
      .replace(/([Çç]ubuk(?:lar)?\s+)(\d+(?:\s*(?:,|ve|–)\s*\d+)*)/g, function (t, bas, l) { return bas + l.replace(/\d+/g, adla); })
      .replace(/([Çç]ubuk[^()\n]{0,40}\()(\d+(?:\s*,\s+\d+)*)(\))/g, function (t, bas, l, son) { return bas + l.replace(/\d+/g, adla) + son; });
  }
  /**
   * Aks–kat kolon/kiriş seçimine GENELLEŞTİRMEDEN özellik yazar (bina.js Özellikler paneli gibi): kesit, grup, kolonda açı 0/90 → yon
   * "x"/"y", kirişte duvar ve duvar yüksekliği (duvar_h; kolonlara yazılmaz). bina.js binaYukle aks–kat elemanlarının ek alanlarını
   * (kiriş duvar_h parapeti, grup) korur ve aks–kat motoru kiriş duvar_h'sini okur; bu yüzden bunlar surum 1'de kalır. Tür, Lb, K,
   * yalnız çekme ve 0° / 90° dışı açı genel model (çubuk) özelliğidir: seçimde başka tür ya da bu alanlardan biri varsa null (işlem
   * genel modelde yapılır). Boş değer (null / "") alanı kaldırır. Dönüş: {model, sayi} (yazılan eleman sayısı)
   */
  function aksKatOzellikYaz(model, secim, oz) {
    const s = secim || [];
    if (!s.length || !s.every(function (x) { return x.tur === "kolon" || x.tur === "kiris"; })) return null;
    const anahtarlar = Object.keys(oz || {});
    if (!anahtarlar.length) return null;
    const kolonVar = s.some(function (x) { return x.tur === "kolon"; }), kirisVar = s.some(function (x) { return x.tur === "kiris"; });
    for (const k of anahtarlar) {
      if (k === "kesit" || k === "grup") continue;
      if (k === "aci") {
        const a = ((+oz.aci % 180) + 180) % 180;
        if (!isFinite(a) || (kolonVar && Math.abs(a) > 1e-9 && Math.abs(a - 90) > 1e-9) || (kirisVar && Math.abs(a) > 1e-9)) return null;
        continue;
      }
      if ((k === "duvar" || k === "duvar_h") && kirisVar) continue;
      return null;
    }
    if ("duvar_h" in oz && oz.duvar_h != null && oz.duvar_h !== "" && !(isFinite(+oz.duvar_h) && +oz.duvar_h > 0)) return null;
    const m = kopya(model);
    let n = 0;
    s.forEach(function (x) {
      const e = liste(m, x.tur === "kolon" ? "kolonlar" : "kirisler").filter(function (y) { return +y.no === +x.no; })[0];
      if (!e) return;
      let yazildi = false;
      anahtarlar.forEach(function (k) {
        const v = oz[k], bos = v == null || v === "";
        if ((k === "duvar" || k === "duvar_h") && x.tur !== "kiris") return;       // duvar alanları yalnız kirişe
        yazildi = true;
        if (k === "aci") { if (x.tur === "kolon") e.yon = Math.abs(((+v % 180) + 180) % 180 - 90) < 1e-9 ? "y" : "x"; }
        else if (k === "duvar") e.duvar = bos ? null : String(v);
        else if (k === "duvar_h") { if (bos) delete e.duvar_h; else e.duvar_h = +v; }
        else if (k === "grup") { if (bos) delete e.grup; else e.grup = String(v); }
        else e[k] = String(v);
      });
      if (yazildi) n++;
    });
    return { model: m, sayi: n };
  }
  /** Bu kodlu denetim bulguları motorca her zaman reddedilir: işlem bunları YENİ üretiyorsa uygulanmaz. */
  const ENGEL_KODLARI = Object.freeze(["sifir-boy", "panel-geometri", "cakisan-cubuk"]);
  /**
   * Bulgunun kimliği: ilgili eleman (çubuk / çubuk çifti / panel ve kenarı / düğüm) — ileti metni değil: önceden bozuk olan elemanın
   * ölçüsü değişse de (boşluk aralığı, üst üste binme boyu, düğüm numarası) bulgu "yeni" sayılmaz. Eleman bilgisi yoksa ileti.
   */
  function bulguAnahtari(u) {
    const l = [u.cubuk, Array.isArray(u.cubuklar) ? u.cubuklar.slice().sort(function (x, y) { return x - y; }).join(",") : null, u.panel, u.kenar, u.dugum];
    return l.some(function (v) { return v != null; }) ? u.kod + "|" + l.map(function (v) { return v == null ? "" : v; }).join("|") : u.kod + "|" + u.mesaj;
  }
  /** sonra modelinde olup once modelinde olmayan denetim bulguları ([{kod, mesaj, …}]); kodlar verilmezse engelleyiciler (ENGEL_KODLARI). */
  function yeniEngeller(once, sonra, kodlar) {
    kodlar = kodlar || ENGEL_KODLARI;
    const O = MO(), suz = function (m) { return O.denetle(m).uyarilar.filter(function (u) { return kodlar.indexOf(u.kod) >= 0; }); };
    let b;
    try { b = suz(sonra); } catch (e) { return []; }
    if (!b.length) return [];
    let a = [];
    try { a = suz(once).map(bulguAnahtari); } catch (e) { a = []; }
    const eski = new Set(a);
    return b.filter(function (u) { return !eski.has(bulguAnahtari(u)); });
  }
  /**
   * "panel-kenari" bulgusu panelin TAŞIYAN kenarında mı (yapi_serbest._panelleri_oku ile aynı kural): dağıtım "iki" → bütün
   * kenarlar, "tek-13" → 1. ve 3., "tek-24" → 2. ve 4., "yok" → hiçbiri; "otomatik" / "cift" / "tek" dört köşede kenar boylarından
   * çözülür (uzun / kısa ≤ 2 → iki doğrultulu, değilse uzun kenarlara tek doğrultulu). Taşıyan kenarında çubuk zinciri eksik panel
   * motorca her zaman reddedilir (bina.js s3Dogrula da hata sayar); taşımayan kenardaki eksik yalnız bilgidir.
   */
  function tasiyanKenarMi(model, u) {
    if (!u || u.kod !== "panel-kenari") return false;
    const p = liste(model, "paneller").filter(function (x) { return x && +x.no === +u.panel; })[0];
    if (!p || !Array.isArray(p.kose)) return false;
    let dag = String(p.dagitim || "iki").trim().toLowerCase();
    if (dag === "otomatik" || dag === "cift" || dag === "tek") {
      let P = null;
      if (p.kose.length === 4) { try { P = p.kose.map(function (r) { return MO().dugumKonumu(model, r); }); } catch (e) { P = null; } }
      if (!P) dag = "iki";
      else {
        const l13 = (uzaklik(P[0], P[1]) + uzaklik(P[2], P[3])) / 2, l24 = (uzaklik(P[1], P[2]) + uzaklik(P[3], P[0])) / 2;
        const tek = l13 >= l24 - 1e-9 ? "tek-13" : "tek-24", oran = Math.max(l13, l24) / Math.max(Math.min(l13, l24), 1e-9);
        dag = dag === "cift" ? "iki" : dag === "tek" ? tek : (oran <= 2 + 1e-9 ? "iki" : tek);
      }
    }
    const k = +u.kenar;
    if (dag === "iki") return true;
    if (dag === "tek-13") return k === 1 || k === 3;
    if (dag === "tek-24") return k === 2 || k === 4;
    return false;
  }

  /**
   * Aks silme sonucunda (MatrisAks.aksSil) motorun her zaman reddettiği YENİ bozukluklar — uygula() kapısıyla aynı kural: sıfır boy,
   * bozuk panel, çakışan çubuk ve panelin taşıyan kenarında eksik çubuk zinciri; ayrıca olmayan düğüme başvuru (eksik-dugum) ve
   * denetimin hiç çözümleyemediği model (ör. doğruları paralel kesişim düğümü). Boşsa silme uygulanabilir.
   */
  function aksSilEngelleri(once, sonra) {
    try { MO().denetle(sonra); } catch (e) {
      let onceBozuk = false;
      try { MO().denetle(once); } catch (x) { onceBozuk = true; }
      return onceBozuk ? [] : [{ kod: "cozulemez", mesaj: "Model çözümlenemiyor: " + ((e && e.message) || String(e)) }];
    }
    return yeniEngeller(once, sonra, ENGEL_KODLARI.concat(["panel-kenari", "eksik-dugum"])).filter(function (u) { return ENGEL_KODLARI.indexOf(u.kod) >= 0 || u.kod === "eksik-dugum" || tasiyanKenarMi(sonra, u); });
  }

  // ================================================================= kesit önerisi (bina_kesit_oner, sözleşme C4)
  /**
   * Çubuk türlerinin Türkçe adları (sözleşme C18; bina.js CUBUK_TURLERI'nin küçük harflisi, motorun yapi_serbest.TUR_ADI'siyle aynı):
   * motor adresi "Ç{no} ({ad})" bunlarla yazılır. Makine alanı `tur` değişmez.
   */
  const TUR_ADI = Object.freeze({ kolon: "kolon", kiris: "kiriş", capraz: "çapraz", "makas-ust": "makas üst başlık", "makas-alt": "makas alt başlık",
    "makas-dikme": "makas dikmesi", "makas-diyagonal": "makas diyagonali", asik: "aşık", kren: "kren kirişi", bag: "bağ", diger: "diğer" });
  /**
   * Öneri satırının adı (C18): aks–kat kaynağı varsa "kolon 2" / "kiriş 3", yoksa "Ç32 (çapraz)" (türü bilinmiyorsa "Ç32"; çubuk
   * numarası yoksa türün adı).
   */
  function oneriEtiketi(o) {
    if (o && o.kaynak && o.kaynak.aks_kat) return (o.kaynak.aks_kat === "kiris" ? "kiriş" : o.kaynak.aks_kat) + " " + o.kaynak.no;
    const tur = o && o.tur != null && o.tur !== "" ? String(o.tur) : null;
    const ad = tur ? (TUR_ADI[tur] || tur) : null;
    if (!o || o.cubuk == null) return ad || "çubuk";
    return "Ç" + o.cubuk + (ad ? " (" + ad + ")" : "");
  }
  /**
   * Çözümün tasarım kaydının adı (veri.tasarim.elemanlar[]): motorun adı (ad) varsa o; yoksa öneri satırıyla aynı kural (aks–kat
   * kaynağı "kiriş 3", genel model çubuğu "Ç32 (çapraz)", aks–kat çözümünün kaydı "kolon 2").
   */
  function tasarimEtiketi(e) {
    if (!e) return "";
    if (e.ad) return String(e.ad);
    if (e.cubuk == null && (e.tur === "kolon" || e.tur === "kiris")) return (e.tur === "kiris" ? "kiriş" : "kolon") + " " + e.no;
    return oneriEtiketi({ cubuk: e.cubuk != null ? e.cubuk : e.no, tur: e.tur === "cubuk" ? null : e.tur, kaynak: e.kaynak });
  }
  /**
   * Öneri uygulanabilir mi (sözleşme K1): öneri var, değişim "aynı" değil, motor uygulamayı reddetmemiş (uygula null değil) ve modele
   * atanacak ad — motorun `uygula.ad`ı (ör. "B30x30-ρ%2.00": yalnız donatı değişse de b × h aynı olsa da farklıdır), yoksa öneri — mevcut
   * kesitten farklı. ("30x30" adlı bir kesitte "donatı" önerisi de böylece uygulanır.)
   */
  function oneriUygulanir(o) {
    if (!o || !o.oneri || o.degisim === "aynı" || o.uygula === null) return false;
    return boslukSiz(oneriAdi(o)) !== boslukSiz(o.kesit);
  }
  /** Önerinin modele atanacak adı: motorun uygula.ad'ı (K1), yoksa öneri. */
  function oneriAdi(o) { return o && o.uygula && o.uygula.ad ? String(o.uygula.ad) : (o && o.oneri != null ? String(o.oneri) : ""); }
  function boslukSiz(s) { return String(s == null ? "" : s).replace(/\s+/g, ""); }
  /**
   * Öneri satırı (K1): "kolon 1: S45x45 → B30x30-ρ%2.00 (30x30)" — uygula.ad gösterilir (öneri ondan farklıysa ayraçta), D/C "tahmini
   * (mevcut iç kuvvetlerle)" etiketlidir; yinele ile yeniden çözüldüyse "yeniden çözümle". Parçalı aks–kat elemanının önerisi (C19
   * `cubuklar`, grup kaydı değil) "N parça" taşır. Dönüş: {ad, oneri, dc, dcEtiket, parca} (metin).
   */
  function oneriSatiri(o, yeniden) {
    const ad = oneriAdi(o), on = o && o.oneri != null ? String(o.oneri) : "";
    const dcS = yeniden && o.dc_sonra != null ? o.dc_sonra : o.dc_oneri;
    const n = o && Array.isArray(o.cubuklar) && !(o.grup && typeof o.grup === "object") ? o.cubuklar.length : 0;
    return { ad: ad || "—", oneri: on && boslukSiz(on) !== boslukSiz(ad) ? on : "",
      dc: fmt(o.dc_once) + " → " + fmt(dcS), dcEtiket: yeniden ? "yeniden çözümle" : "tahmini (mevcut iç kuvvetlerle)", parca: n > 1 ? n + " parça" : "" };
  }
  /**
   * "Hepsini uygula" (yinele) yanıtının özeti (K1): dc = son çözümün D/C maks (dc_sonra); asan = son çözümde D/C > 1 kalan çubuklar
   * (öneri satırlarının dc_sonra'sı; büyükten küçüğe) {etiket, dc}; asiyor = dc > 1.
   */
  function hepsiOzeti(y) {
    const dc = y && y.dc_sonra != null && isFinite(+y.dc_sonra) ? +y.dc_sonra : null;
    const asan = ((y && y.oneriler) || []).filter(function (o) { return o && o.dc_sonra != null && +o.dc_sonra > 1 + 1e-9; })
      .sort(function (a, b) { return b.dc_sonra - a.dc_sonra; }).map(function (o) { return { etiket: oneriEtiketi(o), dc: +o.dc_sonra }; });
    return { dc: dc, asan: asan, asiyor: dc != null && dc > 1 + 1e-9 };
  }
  /**
   * "Hepsini uygula" (yinele) yanıtının ilk yanıtta olmayan uyarıları (K1: motor yinele turlarında ekler — "… turda yakınsamadı …",
   * göreli kat ötelemesi sınırı, …): {tum, diger}; diger "yakınsamadı" uyarısı dışındakiler (aşan çubukları arayüz kendisi listeler).
   */
  function hepsiEkUyarilari(y2, y) {
    const once = (y && y.uyarilar) || [];
    const tum = ((y2 && y2.uyarilar) || []).filter(function (u) { return u && once.indexOf(u) < 0; }).map(String);
    return { tum: tum, diger: tum.filter(function (u) { return !/turda yakınsamadı/.test(u); }) };
  }
  /**
   * "Hepsini uygula" yanıtının açıklamasında ilk yanıtta olmayan ek (motor yinele turlarının özeti — ör. K-27: "0. turda göreli kat
   * ötelemesi … sınırın %90'ını aşacağından şu gruplar küçültülmedi: …"). Model hiç değişmediyse kullanıcı nedenini buradan öğrenir.
   * Öteleme satırı (otelemeSatiri) ayrıca yazılıyorsa (otelemeVar) motorun "Göreli kat ötelemesi (…): öneriden önce …; sonra …."
   * cümlesi tekrar edilmez. Ek yoksa "".
   */
  function hepsiAciklamaEki(y2, y, otelemeVar) {
    const a2 = String((y2 && y2.aciklama) || ""), a1 = String((y && y.aciklama) || "");
    if (!a2 || !a1 || a2.length <= a1.length || a2.slice(0, a1.length) !== a1) return "";
    let ek = a2.slice(a1.length);
    if (otelemeVar) ek = ek.replace(/\s*Göreli kat ötelemesi \([^)]*\): öneriden önce [^;]*; sonra [^.]*\./, "");
    return ek.trim();
  }
  /**
   * "Hepsini uygula" bekleme notu (K-31): "Hesaplanıyor: en çok 4 çözüm, yaklaşık N s" — N = görünen çözümün süresi
   * (veri.ozet.cozum_sure_ms; yoksa yedekMs: ilk öneri yanıtının sure_ms'i) × (yinele + 1) × 1,3 / 1000, yuvarlanmış (en az 1);
   * süre bilinmiyorsa "yaklaşık birkaç saniye".
   */
  function sureTahmini(veri, yinele, yedekMs) {
    const n = Math.max(0, Math.round(+yinele || 0)) + 1;
    const ms = veri && veri.ozet && +veri.ozet.cozum_sure_ms > 0 ? +veri.ozet.cozum_sure_ms : (+yedekMs > 0 ? +yedekMs : null);
    const s = ms != null ? Math.max(1, Math.round(ms * n * 1.3 / 1000)) : null;
    return "Hesaplanıyor: en çok " + n + " çözüm, yaklaşık " + (s != null ? s + " s" : "birkaç saniye");
  }
  /** Yanıtın motor süresi (K-31, C19 sure_ms): "Süre: 4,2 s" (10 s ve üstü tam saniye; 0,05 s'den kısa "< 0,1 s"); süre yoksa "". */
  function sureMetni(ms) {
    if (ms == null || ms === "" || !isFinite(+ms) || +ms < 0) return "";
    const s = +ms / 1000;
    return "Süre: " + (s < 0.05 ? "< " + fmt(0.1, 1) : s < 10 ? fmt(s, 1) : String(Math.round(s))) + " s";
  }
  /**
   * Yinele yanıtının göreli kat ötelemesi satırı (K-27, C19 oteleme {sinir, once: {X: [δ/h], Y}, sonra}): her yönün en büyük δ/h'si
   * sınıra bölünür — "Göreli kat ötelemesi (en büyük δ/h ÷ sınır): önce X 0,82 · Y 0,77 → sonra X 0,95 · Y 0,90"; öneriden sonra
   * sınırı aşan yön varsa sonuna " ⚠". Yanıtta öteleme yoksa "".
   */
  function otelemeSatiri(ot) {
    if (!ot || typeof ot !== "object" || !ot.once || !ot.sonra || !(+ot.sinir > 0)) return "";
    const s = +ot.sinir;
    const en = function (l) { const v = (Array.isArray(l) ? l : []).map(function (x) { return Math.abs(+x); }).filter(isFinite); return v.length ? Math.max.apply(null, v) / s : null; };
    const yaz = function (o) { return ["X", "Y"].map(function (d) { const r = en(o[d]); return r == null ? null : d + " " + fmt(r); }).filter(Boolean).join(" · "); };
    const a = yaz(ot.once), b = yaz(ot.sonra);
    if (!a && !b) return "";
    const asan = ["X", "Y"].some(function (d) { const r = en(ot.sonra[d]); return r != null && r > 1 + 1e-9; });
    return "Göreli kat ötelemesi (en büyük δ/h ÷ sınır): önce " + (a || "—") + " → sonra " + (b || "—") + (asan ? " ⚠" : "");
  }
  /**
   * Kesit grubu (K-32): tıklanan elemanla aynı (kesit, tür) — eleman bir grup adı taşıyorsa aynı grup — çubuklar ve aks–kat
   * kolon/kirişleri (kendisi dahil, model sırasıyla): [{tur: "cubuk" | "kolon" | "kiris", no}]. Motorun "Hepsini uygula" grup kuralıyla
   * (yapi_serbest._oneri_uygula: aynı kesit ve tür) aynıdır; aks–kat kolonu "kolon", kirişi "kiris" türündedir. Kesitsiz eleman: [].
   */
  function grupUyeleri(model, hedef) {
    if (!hedef || hedef.no == null) return [];
    const t = hedef.tur === "kolon" || hedef.tur === "kiris" ? hedef.tur : "cubuk";
    const k = liste(model, t === "kolon" ? "kolonlar" : t === "kiris" ? "kirisler" : "cubuklar").filter(function (x) { return x && +x.no === +hedef.no; })[0];
    if (!k || k.kesit == null || k.kesit === "") return [];
    const grupAdi = function (x) { return x && x.grup != null && String(x.grup).trim() !== "" ? String(x.grup).trim() : null; };
    const kesit = String(k.kesit), tur = t === "cubuk" ? String(k.tur || "diger") : t, grup = grupAdi(k);
    const es = function (x, xTur) { if (!x) return false; return grup ? grupAdi(x) === grup : String(x.kesit == null ? "" : x.kesit) === kesit && xTur === tur; };
    const out = [];
    liste(model, "kolonlar").forEach(function (x) { if (es(x, "kolon")) out.push({ tur: "kolon", no: +x.no }); });
    liste(model, "kirisler").forEach(function (x) { if (es(x, "kiris")) out.push({ tur: "kiris", no: +x.no }); });
    liste(model, "cubuklar").forEach(function (x) { if (es(x, String((x && x.tur) || "diger"))) out.push({ tur: "cubuk", no: +x.no }); });
    return out;
  }
  /** Tek öneri penceresinin grup düğmesi metni (K-32): grupta tıklanan elemandan başka üye varsa "Kesit grubuna uygula (N çubuk)", yoksa "". */
  function grupDugmeMetni(uyeler) {
    const n = Array.isArray(uyeler) ? uyeler.length : 0;
    return n >= 2 ? "Kesit grubuna uygula (" + n + " çubuk)" : "";
  }
  /**
   * Grup önerisi uygulanamıyorsa (oneriUygulanir false) iletisi (K-32): önerilen kesit mevcutla aynıysa "Kesit grubu değişmedi: …";
   * motor öneri vermediyse ya da uygulamayı reddettiyse (uygula null) "Kesit grubu uygulanamadı: …" ve gerekçenin son satırı.
   */
  function grupUygulanmazMetni(o, n) {
    const dc = o && o.dc_oneri != null ? "; D/C maks " + dcFmt(+o.dc_oneri) + " tahmini" : "";
    const ayni = !!o && (o.degisim === "aynı" || (!!o.oneri && o.uygula !== null && boslukSiz(oneriAdi(o)) === boslukSiz(o.kesit)));
    if (ayni) return "Kesit grubu değişmedi: önerilen kesit mevcut kesitle aynı (" + n + " çubuk" + dc + ").";
    const g = o && Array.isArray(o.gerekce) && o.gerekce.length ? String(o.gerekce[o.gerekce.length - 1]) : "";
    return "Kesit grubu uygulanamadı: motor grup için uygulanabilir bir kesit vermedi (" + n + " çubuk" + dc + ")." + (g ? " " + g : "");
  }
  /** Çözümde grup üyelerinin en büyük D/C'si (elemanDc; parçalı aks–kat elemanında parçaların en büyüğü); hiçbiri yoksa null. */
  function grupDcMaks(veri, uyeler) {
    const l = (uyeler || []).map(function (u) { return elemanDc(veri, u); }).filter(function (v) { return v != null; });
    return l.length ? Math.max.apply(null, l) : null;
  }
  /**
   * Önerinin sahnede vurgulanacak elemanları (K-13): parçalı aks–kat elemanının bütün parçaları (C19 `cubuklar`) modelde çubuksa
   * onlar; değilse aks–kat kaynağı (kolon / kiriş, model surum 1'de tek eleman); yoksa önerinin çubuğu. Seçim listesi [{tur, no}].
   */
  function oneriVurgusu(model, o) {
    if (!o) return [];
    const varC = function (no) { return liste(model, "cubuklar").some(function (c) { return c && +c.no === +no; }); };
    const parca = Array.isArray(o.cubuklar) ? o.cubuklar.filter(varC).map(function (no) { return { tur: "cubuk", no: +no }; }) : [];
    if (parca.length) return parca;
    const k = o.kaynak;
    if (k && (k.aks_kat === "kolon" || k.aks_kat === "kiris") && liste(model, k.aks_kat === "kolon" ? "kolonlar" : "kirisler").some(function (x) { return x && +x.no === +k.no; })) return [{ tur: k.aks_kat, no: +k.no }];
    return o.cubuk != null && varC(o.cubuk) ? [{ tur: "cubuk", no: +o.cubuk }] : [];
  }
  /** D/C metni: 1'e 0,005'ten yakınsa (yuvarlama "1,00" gösterip 1'in hangi yanında olduğunu gizlerdi) üç ondalık. */
  function dcFmt(v) { return typeof v === "number" && isFinite(v) && Math.abs(v - 1) < 0.005 && Math.abs(v - 1) > 1e-9 ? fmt(v, 3) : fmt(v); }
  /** Çözüm verisinde bir elemanın D/C'si: hedef {tur: "cubuk" | "kolon" | "kiris", no}; yoksa null. */
  function elemanDc(veri, hedef) {
    const l = veri && veri.tasarim && Array.isArray(veri.tasarim.elemanlar) ? veri.tasarim.elemanlar : [];
    if (!hedef) return null;
    const e = l.filter(function (x) {
      if (!x) return false;
      if (hedef.tur === "cubuk") return +x.cubuk === +hedef.no || (x.tur === "cubuk" && +x.no === +hedef.no);
      return (x.cubuk == null && x.tur === hedef.tur && +x.no === +hedef.no) || (!!x.kaynak && x.kaynak.aks_kat === hedef.tur && +x.kaynak.no === +hedef.no);
    });
    const dcs = e.map(function (x) { return +x.dc; }).filter(isFinite);
    return dcs.length ? Math.max.apply(null, dcs) : null;
  }
  /**
   * Önerinin modeldeki kesit adı ve eklenecek kesit tanımları (yapi_serbest._oneri_kesit ile aynı adlandırma). C4 `uygula` varsa
   * doğrudan o; yoksa öneri sistemine göre: çelik → {tip: "profil", profil: öneri} (vute kesitinde temel profil değişen yeni vute
   * kartı "<eski>-<profil>"), betonarme → b × h (m) dikdörtgen "B30x50". Dönüş: {ad, ekle: {ad: tanım}} ya da {hata}.
   */
  function oneriKesiti(o, kesitler) {
    kesitler = kesitler || {};
    if (!o || !o.oneri) return { hata: "Bu çubuk için öneri yok." };
    if (o.degisim === "aynı") return { hata: "Önerilen kesit mevcut kesitle aynı; değişiklik yok." };
    const ekle = {};
    if (o.uygula && o.uygula.ad) {
      Object.keys(o.uygula.ek_kesitler || {}).forEach(function (k) { if (!kesitler[k]) ekle[k] = kopya(o.uygula.ek_kesitler[k]); });
      if (!kesitler[o.uygula.ad]) {
        if (!o.uygula.tanim) return { hata: "Önerilen kesit “" + o.uygula.ad + "” modelde yok ve tanımı gelmedi." };
        ekle[o.uygula.ad] = kopya(o.uygula.tanim);
      }
      return { ad: String(o.uygula.ad), ekle: ekle };
    }
    const eski = kesitler[o.kesit] || {};
    const bh = /^\s*(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*$/i.exec(String(o.oneri));
    const sistem = o.sistem || (eski.tip === "profil" || eski.tip === "vute" ? "celik" : (o.b && o.h) || bh ? "betonarme" : "celik");
    if (sistem === "betonarme") {
      let b = +o.b, h = +o.h;
      if (!(b > 0 && h > 0) && bh) { b = sayi(bh[1]) / 100; h = sayi(bh[2]) / 100; }
      if (!(b > 0 && h > 0)) return { hata: "Betonarme önerisinin boyutları (b, h) okunamadı: " + o.oneri + "." };
      const malz = o.malzeme || eski.malzeme || "C30";
      const tanim = Object.assign({}, eski.tip === "dikdortgen" ? eski : { tip: "dikdortgen" }, { b: r6(b), h: r6(h), malzeme: malz });
      if (eski.tip !== "dikdortgen") { tanim.tip = "dikdortgen"; delete tanim.profil; delete tanim.temel; }
      let ad = "B" + Math.round(b * 100) + "x" + Math.round(h * 100);
      const v = kesitler[ad];
      if (v && (v.tip !== "dikdortgen" || Math.abs(+v.b - tanim.b) > 1e-9 || Math.abs(+v.h - tanim.h) > 1e-9 || v.malzeme !== malz)) ad = ad + "-" + malz;
      if (!kesitler[ad]) ekle[ad] = tanim;
      return { ad: ad, ekle: ekle };
    }
    const malz = o.malzeme || eski.malzeme || ((kesitler[eski.temel] || {}).malzeme) || "S275";
    let ad = boslukSiz(o.oneri);
    const v = kesitler[ad];
    if (v && (boslukSiz(v.profil) !== ad || (v.malzeme && v.malzeme !== malz))) ad = ad + "-" + malz;
    const tanim = { tip: "profil", profil: String(o.oneri), malzeme: malz };
    if (eski.tip === "vute") {
      const temel = String(eski.temel);
      if (boslukSiz((kesitler[temel] || {}).profil) === boslukSiz(o.oneri)) return { hata: "Vute temel profili zaten " + o.oneri + "; değişiklik yok." };
      if (!kesitler[ad]) ekle[ad] = tanim;
      const vad = String(o.kesit) + "-" + ad;
      if (!kesitler[vad]) ekle[vad] = Object.assign({}, kopya(eski), { temel: ad });
      return { ad: vad, ekle: ekle };
    }
    if (!kesitler[ad]) ekle[ad] = tanim;
    return { ad: ad, ekle: ekle };
  }
  /** Önerinin kesit tanımlarını modele (yerinde) ekler; atanacak adı döndürür. kesitler'de olmayan bir ad ASLA atanmaz (hata). */
  function oneriKesitleriEkle(m, o) {
    if (!m.kesitler || typeof m.kesitler !== "object") m.kesitler = {};
    const k = oneriKesiti(o, m.kesitler);
    if (k.hata) throw new Error(k.hata);
    Object.keys(k.ekle).forEach(function (ad) {
      if (!m.kesitler[ad]) m.kesitler[ad] = kopya(k.ekle[ad]);
      const t = m.kesitler[ad];
      if (t && t.tip === "profil" && t.malzeme) { if (!m.malzemeler) m.malzemeler = {}; if (!m.malzemeler[t.malzeme]) m.malzemeler[t.malzeme] = { kutuphane: t.malzeme }; }
    });
    if (!m.kesitler[k.ad]) throw new Error("Kesit “" + k.ad + "” tanımlanamadı; atanmadı.");
    return k.ad;
  }
  /**
   * Öneriyi modele uygular (kopya): kesit tanımları eklenir, hedefe atanır — aks–kat kolon/kiriş (öneri kaynağı ya da tıklanan
   * hedef) modelde varsa BİR KEZ kolonlar/kirisler[].kesit (parçalı elemanın bütün parçaları bu kayıttan türer; K-13), değilse
   * çubuklar: önerinin bütün parçaları (C19 `cubuklar`, genelleştirilmiş modelde aks–kat elemanının çubukları) ya da cubuklar[o.cubuk].
   * Dönüş: {model, ad, hedef: {tur, no}, hedefler: [{tur, no}]}
   */
  function oneriUygula(model, o, hedef) {
    const m = kopya(model);
    const ad = oneriKesitleriEkle(m, o);
    const kay = o.kaynak && (o.kaynak.aks_kat === "kolon" || o.kaynak.aks_kat === "kiris") ? o.kaynak
      : (hedef && (hedef.tur === "kolon" || hedef.tur === "kiris") ? { aks_kat: hedef.tur, no: hedef.no } : null);
    if (kay) {
      const e = liste(m, kay.aks_kat === "kolon" ? "kolonlar" : "kirisler").filter(function (x) { return +x.no === +kay.no; })[0];
      if (e) { e.kesit = ad; const h = { tur: kay.aks_kat, no: +kay.no }; return { model: m, ad: ad, hedef: h, hedefler: [h] }; }
    }
    const tek = o.cubuk != null ? +o.cubuk : (hedef && hedef.tur === "cubuk" ? +hedef.no : null);
    const grupKaydi = !!(o.grup && typeof o.grup === "object");
    const nolar = !grupKaydi && Array.isArray(o.cubuklar) && o.cubuklar.length ? o.cubuklar.map(Number) : (tek == null ? [] : [tek]);
    const cs = nolar.map(function (no) { return liste(m, "cubuklar").filter(function (x) { return x && +x.no === no; })[0] || null; });
    const yok = nolar.filter(function (no, i) { return !cs[i]; });
    if (!nolar.length || yok.length) throw new Error("Çubuk " + (yok.length ? yok.join(", ") : tek) + " modelde yok; öneri uygulanamadı.");
    cs.forEach(function (c) { c.kesit = ad; });
    const hl = nolar.map(function (no) { return { tur: "cubuk", no: no }; });
    return { model: m, ad: ad, hedef: hl[0], hedefler: hl };
  }
  /**
   * Grup önerisini (K-32, C19 grup kaydı: tek zarf kartı `uygula`) bütün üyelere tek seferde uygular (kopya; arayüzde tek geri al
   * adımı): kesit tanımları bir kez eklenir; aks–kat üyelerde kolonlar/kirisler[].kesit, çubuklarda cubuklar[].kesit. Modelde
   * bulunmayan üye atlanır (eksik); hiçbiri yoksa hata. Dönüş: {model, ad, hedefler, eksik}
   */
  function grupUygula(model, o, uyeler) {
    const m = kopya(model);
    const ad = oneriKesitleriEkle(m, o);
    const hedefler = [], eksik = [];
    (uyeler || []).forEach(function (u) {
      const l = u.tur === "kolon" ? "kolonlar" : u.tur === "kiris" ? "kirisler" : "cubuklar";
      const e = liste(m, l).filter(function (x) { return x && +x.no === +u.no; })[0];
      if (e) { e.kesit = ad; hedefler.push({ tur: u.tur === "kolon" || u.tur === "kiris" ? u.tur : "cubuk", no: +u.no }); } else eksik.push(u);
    });
    if (!hedefler.length) throw new Error("Grubun elemanları modelde yok; öneri uygulanamadı.");
    return { model: m, ad: ad, hedefler: hedefler, eksik: eksik };
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
    // yaylı mesnet (sözleşme C13): rijitlikler "Yaylı mesnet" penceresinden (mesnetAta sec.yay); bina eksenlerinde, > 0
    yay: { ad: "Yaylı (elastik)", yay: true },
    kaldir: { ad: "Mesnedi kaldır" },
  });
  /** Yaylı mesnet anahtarları (C13; bina eksenleri), tuttukları yön, pencere etiketi ve birimi. */
  const YAY_ANAHTARLARI = Object.freeze([
    { a: "kx", yon: "ux", etiket: "k_x (kN/m)", ad: "k_x", birim: "kN/m" }, { a: "ky", yon: "uy", etiket: "k_y (kN/m)", ad: "k_y", birim: "kN/m" },
    { a: "kz", yon: "uz", etiket: "k_z (kN/m)", ad: "k_z", birim: "kN/m" }, { a: "krx", yon: "rx", etiket: "k_rx (kN·m/rad)", ad: "k_rx", birim: "kN·m/rad" },
    { a: "kry", yon: "ry", etiket: "k_ry (kN·m/rad)", ad: "k_ry", birim: "kN·m/rad" }, { a: "krz", yon: "rz", etiket: "k_rz (kN·m/rad)", ad: "k_rz", birim: "kN·m/rad" },
  ]);
  const YAY_VARSAYILAN = Object.freeze({ kz: 10000 });
  /**
   * "Yaylı mesnet" penceresinin değerleri → {kx?, …, krz?}: boş ya da ≤ 0 alan yazılmaz (C13: her anahtar > 0 ya da yok). Dolu ama
   * sayı olmayan alan hata verir (yazım yanlışı o yönü sessizce serbest bırakmasın: "5 000" binlik ayraçlı yazılmış olabilir). Hiç
   * pozitif alan yoksa hata (pencere kapanmaz).
   */
  function yayDegerleri(o) {
    const r = {};
    YAY_ANAHTARLARI.forEach(function (y) {
      const ham = o && o[y.a] != null ? o[y.a] : "", v = sayi(ham);
      if (v == null && String(ham).trim() !== "") throw new Error("Yaylı mesnet: " + y.etiket + " alanı sayı değil (“" + String(ham).trim() + "”); ondalık için virgül ya da nokta kullanın, binlik ayraç yazmayın.");
      if (v != null && v > 0) r[y.a] = v;
    });
    if (!Object.keys(r).length) throw new Error("Yaylı mesnet için en az bir yay rijitliği girin (k_x … k_rz; pozitif sayı, kN/m ya da kN·m/rad).");
    return r;
  }
  /** Rijit diyafram sorusunun doğurduğu yönler (C14): ux, uy, rz ve bunların yayları kx, ky, krz bütün katın yatay hareketini tutar. */
  const DIYAFRAM_YONLERI = Object.freeze(["ux", "uy", "rz", "kx", "ky", "krz"]);
  function depremVar(b) {
    const E = b && b.yuk_durumlari && typeof b.yuk_durumlari.E === "object" && !Array.isArray(b.yuk_durumlari.E) ? b.yuk_durumlari.E : {};
    const d = b && b.deprem && typeof b.deprem === "object" && !Array.isArray(b.deprem) ? b.deprem : {};
    return !!E.acik || !!d.etkin;
  }
  /** Modelin kat seviyeleri (yapi_serbest._model_oku ile aynı): kat işaretli GLOBAL Z aksları; yoksa katlar listesi. [{no, ad, kot}] */
  function katSeviyeleri(b) {
    const z = b && b.akslar && Array.isArray(b.akslar.z) ? b.akslar.z.filter(function (a) { return a && a.kat != null && a.kat !== ""; }) : [];
    const l = z.length ? z.map(function (a) { return { no: +a.kat, ad: String(a.ad), kot: +a.konum }; })
      : liste(b, "katlar").map(function (k, i) { return { no: k.no != null ? +k.no : i, ad: String(k.ad || (k.no ? k.no + ". kat" : "Temel")), kot: +k.kot }; });
    return l.filter(function (k) { return isFinite(k.no) && isFinite(k.kot); }).sort(function (a, c) { return a.no - c.no; });
  }
  /**
   * Düğümün kat seviyesinin diyafram biçimi (sözleşme C14; yapi_serbest._diyafram_modu ile aynı kural). Düğüm bir kat kotunda
   * (1e-4 m) değilse, en alt seviyedeyse ya da deprem tanımlı değilse null. Biçim: analiz.diyafram[String(kat)] (ya da dize
   * analiz.diyafram) önce; yoksa deprem.diyafram (varsayılan "rijit"); "rijit" istenen seviyede kalınlığı > 0 olan ve bütün
   * köşeleri bu seviyede bulunan panel yoksa "esnek". Dönüş: {mod: "rijit" | "esnek", kat, katAdi, kaynak} | null
   */
  function diyaframModu(b, ref) {
    if (!b || !depremVar(b)) return null;
    let P = null;
    try { P = MA().refKoordinat(b, ref); } catch (e) { P = null; }
    if (!P) return null;
    const kl = katSeviyeleri(b);
    if (kl.length < 2) return null;
    const kat = kl.filter(function (k) { return Math.abs(P[2] - k.kot) < 1e-4; })[0];
    if (!kat || kat.no === kl[0].no) return null;
    const an = b.analiz && b.analiz.diyafram;
    let v = null;
    if (an && typeof an === "object" && !Array.isArray(an) && an[String(kat.no)] != null) v = String(an[String(kat.no)]).trim().toLowerCase();
    else if (typeof an === "string") v = an.trim().toLowerCase();
    if (v === "rijit" || v === "esnek") return { mod: v, kat: kat.no, katAdi: kat.ad, kaynak: "analiz.diyafram" };
    const istek = String((b.deprem && b.deprem.diyafram) || "rijit").trim().toLowerCase();
    if (istek !== "rijit") return { mod: istek === "esnek" ? "esnek" : istek, kat: kat.no, katAdi: kat.ad, kaynak: "deprem.diyafram" };
    const dosemeli = liste(b, "paneller").some(function (p) {
      if (!p || p.kalinlik == null || !(+p.kalinlik > 0) || !Array.isArray(p.kose) || !p.kose.length) return false;
      try { return p.kose.every(function (r) { return Math.abs(MA().refKoordinat(b, r)[2] - kat.kot) < 1e-4; }); } catch (e) { return false; }
    });
    return dosemeli ? { mod: "rijit", kat: kat.no, katAdi: kat.ad, kaynak: "deprem.diyafram" }
      : { mod: "esnek", kat: kat.no, katAdi: kat.ad, kaynak: "seviyede betonarme döşeme paneli yok" };
  }
  /**
   * Mesnet aracının rijit diyafram sorusu (K-15, C14): ön ayar ux, uy ya da rz (yaylı mesnette kx, ky, krz) yazıyorsa ve düğüm
   * rijit diyaframlı bir kat seviyesindeyse {baslik: "Rijit diyaframlı kat", metin, kat, katAdi, secenekler}; değilse null. Model
   * aks–kat ise genelleştirilmiş kopyasında bakılır (aks–kat döşemeleri panel olur). adres verilmezse REF'ten.
   */
  function mesnetDiyaframSorusu(bina, ref, onAyar, sec) {
    sec = sec || {};
    const o = MESNET_ON_AYAR[onAyar];
    if (!o || onAyar === "kaldir") return null;
    const yayl = o.yay ? (sec.yay || {}) : {};
    if (!DIYAFRAM_YONLERI.some(function (a) { return o.yay ? yayl[a] != null && +yayl[a] > 0 : !!o[a]; })) return null;
    let m = bina, r = ref;
    if (genelGecisGerekli(bina)) { try { m = genellestirHazirla(bina).model; r = aksRefZ(m, ref); } catch (e) { m = bina; } }
    const d = diyaframModu(m, r);
    if (!d || d.mod !== "rijit") return null;
    const adres = sec.adres || refAdi(r);
    return { baslik: "Rijit diyaframlı kat", kat: d.kat, katAdi: d.katAdi,
      metin: adres + " rijit diyaframlı " + d.katAdi + " seviyesinde. Yatay (ux, uy) ve rz mesnedi bu noktada bütün katın yatay hareketini tutar (diyafram bağı).",
      secenekler: [["aynen", "Olduğu gibi uygula"], ["dusey", "Yalnız düşey mesnet (uz, rx, ry)"], ["esnek", "Bu katın diyaframını esnek yap"], ["vazgec", "Vazgeç"]] };
  }
  /** REF'in kısa adı: "C2 / +3.50" (sistemli "KANAT: A1 / +3.00"), düğüm no ya da metin. */
  function refAdi(ref) {
    if (ref && typeof ref === "object" && Array.isArray(ref.aks)) return (ref.sistem && ref.sistem !== "GLOBAL" ? ref.sistem + ": " : "") + ref.aks.join("") + " / " + (ref.z != null ? ref.z : "kat " + ref.kat);
    if (ref && typeof ref === "object" && ref.dugum != null) return "Düğüm " + ref.dugum;
    return typeof ref === "number" ? "Düğüm " + ref : String(ref == null ? "" : ref);
  }
  /** analiz.diyafram'da bu kat seviyesini esnek yapar; dize analiz.diyafram önce kat başına sözlüğe açılır (öteki katlar korunur). */
  function katDiyaframiEsnek(m, kat) {
    if (!m.analiz || typeof m.analiz !== "object" || Array.isArray(m.analiz)) m.analiz = {};
    let an = m.analiz.diyafram;
    if (typeof an === "string") {
      const v = an.trim().toLowerCase(), d = {};
      katSeviyeleri(m).slice(1).forEach(function (k) { d[String(k.no)] = v; });
      an = d;
    } else if (!an || typeof an !== "object" || Array.isArray(an)) an = {};
    else an = Object.assign({}, an);
    an[String(kat)] = "esnek";
    m.analiz.diyafram = an;
  }
  /**
   * Düğüme mesnet ata / kaldır (aynı düğümdeki kayıt değişir). Mesnet genel model kaydıdır (sözleşme C1): aks–kat modeline mesnet
   * eklenirken model önce genelleştirilir (genellestirHazirla: surum 3; temeller aynen) ve {aks, kat} REF'i {aks, z} olur.
   * sec: {yay: {kx…krz} ("yay" ön ayarı; yayDegerleri), diyafram: "aynen" | "dusey" | "esnek" (mesnetDiyaframSorusu yanıtı)}.
   *   - "yay": kayıt {dugum, <verilen yay anahtarları>}; düğümde açık mesnet kaydı varsa onun yaysız yönlerdeki tutulu serbestlikleri
   *     korunur, yaylı yönlerin boolean'ı yazılmaz (C13: bir yön hem tutulu hem yaylı olamaz).
   *   - diyafram "dusey": yalnız uz, rx, ry (ve kz, krx, kry) yazılır; "esnek": ön ayar aynen, analiz.diyafram[kat] = "esnek".
   * Dönüş: {model, eylem: "eklendi"|"degisti"|"kaldirildi"|"yok", notlar: [metin], genellesti, temelDegisti (her zaman false)}
   */
  function mesnetAta(bina, ref, onAyar, sec) {
    sec = sec || {};
    const o = MESNET_ON_AYAR[onAyar];
    if (!o) throw new Error("Mesnet türü tanımsız: " + onAyar);
    const yay = o.yay ? yayDegerleri(sec.yay || YAY_VARSAYILAN) : null;
    let m = kopya(bina), notlar = [], genellesti = false;
    const A = MA();
    if (onAyar !== "kaldir" && genelGecisGerekli(bina)) {
      const g = genellestirHazirla(bina);
      m = g.model; notlar = g.notlar; genellesti = true;
      ref = aksRefZ(m, ref);
    }
    const sonuc = function (eylem) { return { model: m, eylem: eylem, notlar: notlar, genellesti: genellesti, temelDegisti: false }; };
    if (!Array.isArray(m.mesnetler)) m.mesnetler = [];
    const k = A.refAnahtar(m, ref);
    let P = null; try { P = A.refKoordinat(m, ref); } catch (e) { P = null; }
    const i = m.mesnetler.findIndex(function (s) {
      if (!s) return false;
      if (A.refAnahtar(m, s.dugum) === k) return true;
      if (!P) return false;
      try { return uzaklik(A.refKoordinat(m, s.dugum), P) < TOL; } catch (e) { return false; }
    });
    if (onAyar === "kaldir") { if (i < 0) return sonuc("yok"); m.mesnetler.splice(i, 1); return sonuc("kaldirildi"); }
    const kayit = { dugum: kopya(ref) };
    const dusey = sec.diyafram === "dusey";
    if (yay) {
      const eski = i >= 0 ? m.mesnetler[i] : null;
      YAY_ANAHTARLARI.forEach(function (y) { if (eski && !(y.a in yay) && eski[y.yon] === true && !(dusey && DIYAFRAM_YONLERI.indexOf(y.yon) >= 0)) kayit[y.yon] = true; });
      YAY_ANAHTARLARI.forEach(function (y) { if (y.a in yay && !(dusey && DIYAFRAM_YONLERI.indexOf(y.a) >= 0)) kayit[y.a] = yay[y.a]; });
      if (!YAY_ANAHTARLARI.some(function (y) { return y.a in kayit; })) throw new Error("Yalnız düşey yönlerde yay kalmadı (k_z, k_rx, k_ry boş): yaylı mesnet yazılmadı.");
    } else ["ux", "uy", "uz", "rx", "ry", "rz"].forEach(function (a) { kayit[a] = !!o[a] && !(dusey && DIYAFRAM_YONLERI.indexOf(a) >= 0); });
    if (sec.diyafram === "esnek") {
      const d = diyaframModu(m, ref);
      if (d) { katDiyaframiEsnek(m, d.kat); notlar = notlar.concat([d.katAdi + " seviyesinin diyaframı esnek yapıldı (analiz.diyafram)."]); }
    }
    if (i >= 0) { m.mesnetler[i] = kayit; return sonuc("degisti"); }
    m.mesnetler.push(kayit);
    return sonuc("eklendi");
  }
  /**
   * Ek yük kaydı ekler (durum G, Q, S).
   * Genel model (surum 3, §12.2):
   *   hedef {tur: "cubuk", no}: yuk {durum, yon ("Z" | "X" | "Y" | "x′" | "y′" | "z′"), q1, q2?, izdusum?} yayılı (kN/m, yön boyunca; aşağı
   *     yük Z'de negatif) ya da {durum, yon, P, x, oransal?} tekil;
   *   hedef {tur: "panel", no}: yuk {durum, p} (kN/m², düşey, aşağı +; sözleşme C6) — eski biçim {g?, q?} de kabul edilir;
   *   hedef {tur: "dugum", ref}: yuk {durum, FX?, FY?, FZ?, MX?, MY?, MZ?} (kN, kN·m; global, FZ < 0 aşağı) → {tur: "dugum", dugum: REF, …}.
   * Aks–kat modeli (sözleşme C10, yapi.py ek yükleri; model genelleştirilmez):
   *   hedef {tur: "dugum", ref}: kat düzlemindeki GLOBAL kesişim → {tur: "dugum", aks: [x, y], kat, durum, FX…MZ};
   *   hedef {tur: "kiris", no}: yalnız düzgün yayılı düşey yük → {tur: "kiris", kiris, durum, q} (q aşağı +; yuk.q ya da yuk.q1 = −q);
   *   hedef {tur: "doseme", no}: {g?, q?} (kN/m²; kar yok) → {tur: "doseme", doseme, g, q};
   *   hedef {tur: "kolon"}: ek yük verilemez (üst düğüme düğüm yükü).
   */
  function yukEkle(bina, hedef, yuk) {
    const m = kopya(bina);
    if (!Array.isArray(m.ek_yukler)) m.ek_yukler = [];
    yuk = yuk || {};
    const durum = String(yuk.durum || "G").toUpperCase();
    if (["G", "Q", "S"].indexOf(durum) < 0) throw new Error("Ek yük durumu G, Q ya da S olmalı (rüzgâr ve deprem otomatik üretilir).");
    let r;
    if (hedef.tur === "kolon") throw new Error("Aks–kat kolonuna ek yük verilemez; kolonun üst düğümüne düğüm yükü verin.");
    if (hedef.tur === "kiris") {
      if (!liste(m, "kirisler").some(function (k) { return +k.no === +hedef.no; })) throw new Error("Kiriş " + hedef.no + " modelde yok.");
      if (yuk.P != null && yuk.P !== "") throw new Error("Aks–kat kirişine tekil yük verilemez; düzgün yayılı düşey yük (q, kN/m) girin ya da tekil yükü düğüme verin.");
      if (yuk.yon != null && String(yuk.yon).toUpperCase() !== "Z") throw new Error("Aks–kat kirişine yalnız düşey (global Z) yayılı yük verilir.");
      let q;
      if (yuk.q != null && yuk.q !== "") q = sayi(yuk.q);
      else {
        const q1 = sayi(yuk.q1), q2 = yuk.q2 == null || yuk.q2 === "" ? q1 : sayi(yuk.q2);
        if (q1 == null || q2 == null) throw new Error("Yayılı yük q (kN/m) sayı olmalı.");
        if (Math.abs(q1 - q2) > 1e-12) throw new Error("Aks–kat kirişine yalnız düzgün yayılı yük verilir (q₁ = q₂).");
        q = -q1;
      }
      if (q == null || !q) throw new Error("Kiriş yükü q (kN/m, aşağı +) sıfırdan farklı bir sayı olmalı.");
      r = { tur: "kiris", kiris: +hedef.no, durum: durum, q: q };
    } else if (hedef.tur === "doseme") {
      if (!liste(m, "dosemeler").some(function (d) { return +d.no === +hedef.no; })) throw new Error("Döşeme " + hedef.no + " modelde yok.");
      if (durum === "S") throw new Error("Döşemeye kar (S) ek yükü verilemez; g (sabit) ya da q (hareketli) kN/m² girin.");
      const g = sayi(yuk.g) || 0, q = sayi(yuk.q) || 0;
      if (!g && !q) throw new Error("Döşeme yükü için g ya da q (kN/m²) girin.");
      r = { tur: "doseme", doseme: +hedef.no, g: g, q: q };
    } else if (hedef.tur === "cubuk") {
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
      if (yuk.p != null && yuk.p !== "") {
        const p = sayi(yuk.p);
        if (p == null || !p) throw new Error("Panel yükü p (kN/m², aşağı +) sıfırdan farklı bir sayı olmalı.");
        r = { tur: "panel", panel: +hedef.no, durum: durum, p: p };
      } else {
        const g = sayi(yuk.g) || 0, q = sayi(yuk.q) || 0;
        if (!g && !q) throw new Error("Panel yükü için p (kN/m²; eski biçimde g ya da q) girin.");
        r = { tur: "panel", panel: +hedef.no, durum: durum };
        if (g) r.g = g;
        if (q) r.q = q;
      }
    } else if (hedef.tur === "dugum") {
      const bil = {};
      let var_ = false;
      ["FX", "FY", "FZ", "MX", "MY", "MZ"].forEach(function (a) { const v = sayi(yuk[a]); if (v) { bil[a] = v; var_ = true; } });
      if (!var_) throw new Error("Düğüm yükü için en az bir bileşen (FX, FY, FZ, MX, MY, MZ) girin.");
      if (!genelMi(bina)) {
        const a = aksKatAdresi(bina, hedef.ref);
        if (!a) throw new Error("Aks–kat modelinde düğüm yükü yalnız kat düzlemlerindeki aks kesişimlerine verilir (kat dışı Z aksı ya da ek aks sistemi için önce modeli genel modele çevirin).");
        r = Object.assign({ tur: "dugum", aks: a.aks, kat: a.kat, durum: durum }, bil);
      } else r = Object.assign({ tur: "dugum", dugum: kopya(hedef.ref), durum: durum }, bil);
    } else throw new Error("Yük hedefi çubuk, panel, düğüm, kiriş ya da döşeme olmalı.");
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
  /**
   * Seçili çubukları (genel model; GLOBAL aks düzlemleri) İÇ noktalarından kesen X / Y / Z aks düzlemleri — Düzlemle böl penceresi
   * yalnız bunları sunar (uçtan geçen düzlem bölmez; ModelOps.duzlemleBol ile aynı tol). Dönüş: [{yon, ad, konum, sayi}] (sayi: kestiği çubuk)
   */
  function kesenDuzlemler(model, nolar) {
    const cz = new (MA().Cozucu)(model), set = new Set((nolar || []).map(Number)), uclar = [];
    liste(model, "cubuklar").forEach(function (c) { if (!c || !set.has(+c.no)) return; try { uclar.push([cz.coz(c.i), cz.coz(c.j)]); } catch (e) { /* çözülemeyen uç: atlanır */ } });
    const out = [];
    ["x", "y", "z"].forEach(function (yon, i) {
      aksListesi(model, yon).forEach(function (a) {
        const n = uclar.filter(function (u) { const si = u[0][i] - a.konum, sj = u[1][i] - a.konum; return (si > TOL && sj < -TOL) || (si < -TOL && sj > TOL); }).length;
        if (n) out.push({ yon: yon, ad: a.ad, konum: a.konum, sayi: n });
      });
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

  // ================================================================= üreteç düzenleme (ModelOps.uretecGuncelle)
  const DUZENLENIR_URETEC = Object.freeze(["makas", "besik-cerceve", "asik", "kren-yolu", "capraz"]);
  /** Çubuğun / panelin (kaynak.uretec) ya da numarası verilen üretecin kaydı (bina.uretecler); yoksa null. hedef: {tur, no} | no */
  function uretecKaydi(bina, hedef) {
    let no = null;
    if (typeof hedef === "number" || (typeof hedef === "string" && /^\d+$/.test(hedef))) no = +hedef;
    else if (hedef && (hedef.tur === "cubuk" || hedef.tur === "panel")) {
      const x = liste(bina, hedef.tur === "cubuk" ? "cubuklar" : "paneller").filter(function (c) { return c && +c.no === +hedef.no; })[0];
      if (x && x.kaynak && x.kaynak.uretec != null) no = +x.kaynak.uretec;
    }
    if (no == null) return null;
    return liste(bina, "uretecler").filter(function (u) { return u && +u.no === no; })[0] || null;
  }
  /**
   * Üreteç kaydından düzenleme penceresinin başlangıç değerleri (pencerelerin alan adlarıyla). Desteklenmeyen tür ya da aks
   * adresiyle yazılmamış uçlar için {hata}. Değerler metin/boolean (form alanları).
   */
  function uretecFormu(bina, kayit) {
    if (!kayit) return { hata: "Üreteç kaydı yok." };
    const tur = String(kayit.tur || "");
    if (DUZENLENIR_URETEC.indexOf(tur) < 0) return { hata: "“" + tur + "” üreteci bu pencerede düzenlenemiyor." };
    const ks = kayit.kesitler || {}, sKot = function (v) { return v == null ? "" : String(r6(+v)); };
    const aksZ = function (ref) {
      if (!ref || !Array.isArray(ref.aks) || (ref.sistem && ref.sistem !== "GLOBAL")) return null;
      const z = ref.z != null ? String(ref.z) : (ref.kat != null ? (function () { try { const a = MA().katZAksi(bina, ref.kat); return a ? String(a.ad) : null; } catch (e) { return null; } })() : null);
      return z == null ? null : { x: String(ref.aks[0]), y: String(ref.aks[1]), z: z };
    };
    const zKonum = function (ad) { const a = aksListesi(bina, "z").filter(function (x) { return x.ad === String(ad); })[0]; return a ? a.konum : null; };
    if (tur === "makas") {
      const a = aksZ(kayit.bas), b = aksZ(kayit.son);
      if (!a || !b || a.y !== b.y || a.z !== b.z) return { hata: "Makas mesnetleri aynı Y aksı ve Z aksındaki iki aks kesişimi değil; düzenlenemiyor (silip yeniden üretin)." };
      return { tur: tur, tip: String(kayit.tip || "pratt"), xa: a.x, xb: b.x, y0: a.y, y1: a.y, z: a.z, h: sKot(kayit.yukseklik), goz: String(kayit.goz || 6),
        uc: sKot(kayit.uc_yukseklik || 0), ust: ks.ust || "", alt: ks.alt || "", dikme: ks.dikme || "", diyagonal: ks.diyagonal || "", mafsal: kayit.mafsalli_govde !== false,
        yanal: kayit.yanal_tutma === "yok" ? "yok" : "uc-dikme" };
    }
    if (tur === "besik-cerceve") {
      const a = aksZ(kayit.taban1), b = aksZ(kayit.taban2);
      if (!a || !b || a.y !== b.y || a.z !== b.z) return { hata: "Çerçeve tabanları aynı Y ve Z aksındaki iki aks kesişimi değil; düzenlenemiyor (silip yeniden üretin)." };
      const ys = aksListesi(bina, "y"), i = ys.findIndex(function (y) { return y.ad === a.y; });
      const adet = Math.max(1, Math.round(+kayit.adet || 1));
      const y1 = ys[Math.min(ys.length - 1, i + adet - 1)] || ys[i];
      const z0 = zKonum(a.z) || 0;
      const v = kayit.vute && +kayit.vute.boy > 0 ? kayit.vute : null;
      return { tur: tur, kx: [a.x, b.x], y0: a.y, y1: y1 ? y1.ad : a.y, taban: a.z, mesnet: String(kayit.mesnet || "ankastre"),
        sacak: sKot(z0 + (+kayit.sacak || 0)), mahya: sKot(z0 + (+kayit.mahya || 0)), kolon: ks.kolon || "", mertek: ks.mertek || "",
        vuteBoy: sKot(v ? v.boy : 0), vuteH: sKot(v ? v.yukseklik : 0.4), asik: !!kayit.asik, asikAralik: sKot(kayit.asik ? kayit.asik.aralik : 2.5),
        asikKesit: kayit.asik ? kayit.asik.kesit || "" : "", panel: !!kayit.panel };
    }
    if (tur === "asik") {
      const s = kayit.secenek || {};
      return { tur: tur, aralik: sKot(kayit.aralik), kesit: kayit.kesit || "", uclar: s.uclar !== false, mafsal: s.mafsalli !== false,
        hedefMetin: kayit.hedef && kayit.hedef.panel != null ? "Panel " + kayit.hedef.panel : (Array.isArray(kayit.hedef) ? kayit.hedef : (kayit.hedef && kayit.hedef.mertekler) || []).length + " mertek çubuğu" };
    }
    if (tur === "kren-yolu") {
      const t = (kayit.kren && kayit.kren.tekerlek) || {};
      return { tur: tur, kot: sKot(kayit.kot), konsol: sKot(kayit.konsol_boy || 0), kiris: ks.kiris || "", konsolK: ks.konsol || "",
        Pmaks: sKot(t.P_maks), Pmin: sKot(t.P_min), Hy: sKot(t.H_yanal), Hf: sKot(t.H_fren), ara: sKot(t.aralik),
        din: sKot(kayit.kren && kayit.kren.dinamik != null ? kayit.kren.dinamik : 1.25), hatSayisi: Array.isArray(kayit.kolonlar) && Array.isArray(kayit.kolonlar[0]) ? kayit.kolonlar.length : 1 };
    }
    const s = kayit.secenek || {};
    return { tur: tur, tip: String(kayit.tip || "X"), kesit: s.kesit || "", mafsal: s.mafsalli_uclar !== false, yalniz_cekme: !!s.yalniz_cekme };
  }

  const SAF = {
    TOL: TOL, MAFSAL_ON_AYAR: MAFSAL_ON_AYAR, MESNET_ON_AYAR: MESNET_ON_AYAR, DUZENLENIR_URETEC: DUZENLENIR_URETEC,
    sayi: sayi, fmt: fmt, fmtK: fmtK, aksListesi: aksListesi, aksAdi: aksAdi,
    cubukTuru: cubukTuru, kolonCiftleri: kolonCiftleri, mevcutCubuk: mevcutCubuk, aksKatCakisan: aksKatCakisan,
    aksSihirbazUygula: aksSihirbazUygula, yeniModel: yeniModel, serbestleriBagla: serbestleriBagla, aksaBaglaHepsi: aksaBaglaHepsi,
    aksSagla: aksSagla, besikPlan: besikPlan, makasPlan: makasPlan, krenPlan: krenPlan,
    mesnetAta: mesnetAta, yukEkle: yukEkle, secimAyir: secimAyir, genelSecim: genelSecim, bolmeNoktalari: bolmeNoktalari,
    // yaylı mesnet (C13) ve rijit diyafram sorusu (C14)
    YAY_ANAHTARLARI: YAY_ANAHTARLARI, YAY_VARSAYILAN: YAY_VARSAYILAN, yayDegerleri: yayDegerleri, katSeviyeleri: katSeviyeleri, depremVar: depremVar,
    diyaframModu: diyaframModu, mesnetDiyaframSorusu: mesnetDiyaframSorusu, katDiyaframiEsnek: katDiyaframiEsnek, refAdi: refAdi,
    ekrandanDuzleme: ekrandanDuzleme, aksEkleKonumu: aksEkleKonumu, ozet: ozet, caprazSecenek: caprazSecenek, kesenDuzlemler: kesenDuzlemler,
    // genel model kapısı (C1) ve aks–kat yolları
    genelMi: genelMi, surumSayi: surumSayi, aksKatElemanVar: aksKatElemanVar, genelGecisGerekli: genelGecisGerekli, genelGecisMetni: genelGecisMetni, GENEL_ISLEM_ADLARI: GENEL_ISLEM_ADLARI,
    genellestirHazirla: genellestirHazirla, aksKatAdresi: aksKatAdresi, aksRefZ: aksRefZ, cubukAksKatAdi: cubukAksKatAdi, cubukAdlari: cubukAdlari,
    aksKatOzellikYaz: aksKatOzellikYaz, ENGEL_KODLARI: ENGEL_KODLARI, yeniEngeller: yeniEngeller, tasiyanKenarMi: tasiyanKenarMi, aksSilEngelleri: aksSilEngelleri,
    // kesit önerisi (C4)
    TUR_ADI: TUR_ADI, oneriEtiketi: oneriEtiketi, tasarimEtiketi: tasarimEtiketi, oneriUygulanir: oneriUygulanir, oneriAdi: oneriAdi, oneriSatiri: oneriSatiri,
    hepsiOzeti: hepsiOzeti, hepsiEkUyarilari: hepsiEkUyarilari, hepsiAciklamaEki: hepsiAciklamaEki, dcFmt: dcFmt, elemanDc: elemanDc, oneriKesiti: oneriKesiti, oneriUygula: oneriUygula,
    // kesit önerisi ekleri (C19): parçalı eleman, kesit grubu, süre, öteleme
    sureTahmini: sureTahmini, sureMetni: sureMetni, otelemeSatiri: otelemeSatiri, grupUyeleri: grupUyeleri, grupDugmeMetni: grupDugmeMetni, grupUygulanmazMetni: grupUygulanmazMetni,
    grupDcMaks: grupDcMaks, grupUygula: grupUygula, oneriVurgusu: oneriVurgusu,
    // üreteç düzenleme
    uretecKaydi: uretecKaydi, uretecFormu: uretecFormu,
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
    if (!MAk || !MOp) {
      // aks tabanlı araçlar kurulamaz: hangi dosyanın eksik olduğu söylenir (araç kutusundaki "bağlı değil" ipucu yanıltmasın)
      const eksik = [!MAk ? "aks_sistemi.js (MatrisAks)" : null, !MOp ? "model_ops.js (ModelOps)" : null].filter(Boolean).join(" ve ");
      const metin = "Aks tabanlı çizim araçları kurulamadı: " + eksik + " yüklenmedi; sayfayı yenileyin (çevrimdışı önbellek eksik olabilir).";
      try { console.warn(metin); } catch (e) { /* yoksay */ }
      try { MB.toast(metin); } catch (e) { /* yoksay */ }
      return;
    }
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
    /**
     * Genel model kapısı: model aks–kat (C1'e göre genel değil) ya da aks–kat elemanı taşıyorsa kullanıcıya sorulur; onaylanırsa
     * genellestirHazirla (surum 3; temeller aynen — C11), vazgeçilirse null ve "İşlem iptal edildi." Gerekmiyorsa model aynen.
     * islemAdi: GENEL_ISLEM_ADLARI'ndan işlem adı (onay metninin ön eki; verilmezse ön ek yok). Dönüş: {model, notlar, temelDegisti, cevrildi} | null
     */
    function genelModeleGec(m, islemAdi) {
      if (!genelGecisGerekli(m)) return { model: m, notlar: [], temelDegisti: false, cevrildi: false };
      if (!window.confirm(genelGecisMetni(m, islemAdi))) { toast("İşlem iptal edildi."); return null; }
      const g = genellestirHazirla(m);
      g.cevrildi = true;
      return g;
    }
    /**
     * fn(model) → ModelOps raporu; aks sistemine bağlar, binaAyarla ile uygular (tek geri al yığını).
     * sc: {bagla (false: aksaBaglaHepsi yok), secim(r, m), sessiz, genel (işlem adı — GENEL_ISLEM_ADLARI — ya da true: önce genel model
     *      kapısı; onay metninin ön eki yalnız işlem adıdır, geçmiş zamanlı `etiket` değil), notlar: [metin],
     *      model (fn'e verilecek model; varsayılan B() — secimli genelleştirilmiş modeli verir)}
     * Ret: rapor reddedildiyse ya da sonuç motorun her zaman reddettiği YENİ bir bozukluk (sıfır boy, bozuk panel, çakışan çubuk)
     * içeriyorsa model değişmez, neden bildirilir. Model değişmediyse "Değişiklik yok" (ya da işlemin uyarısı) bildirilir.
     */
    function uygula(fn, etiket, sc) {
      sc = sc || {};
      let m0 = sc.model || B(), notlar = (sc.notlar || []).slice(), cevrildi = !!sc.cevrildi;
      if (sc.genel) {
        let g;
        try { g = genelModeleGec(m0, typeof sc.genel === "string" ? sc.genel : (sc.islem || null)); } catch (e) { hata(e); return null; }
        if (!g) return null;
        m0 = g.model; notlar = notlar.concat(g.notlar); cevrildi = cevrildi || !!g.cevrildi;
      }
      let r;
      try { r = fn(m0); } catch (e) { hata(e); return null; }
      if (!r || !r.model) return null;
      const adla = function (l, mm) { return (l || []).map(function (u) { return cubukAdlari(mm, u); }); };
      if (r.reddedildi) { S.sonUyari = adla(r.uyarilar, m0).join(" "); toast(S.sonUyari || "İşlem uygulanmadı."); MB.ipucuYenile(); return null; }
      let m = r.model, uy = notlar.concat(adla(r.uyarilar, r.model));
      if (sc.bagla !== false) { try { const b = aksaBaglaHepsi(m); m = b.model; uy = uy.concat(b.uyarilar); } catch (e) { uy.push(e.message); } }
      // yeni bozukluklar işlemden önceki modele göre (kapıdan geçtiyse genelleştirilmiş model; numaralar aynı)
      const yeni = yeniEngeller(m0, m, ENGEL_KODLARI.concat(["panel-kenari"]));
      // motorun her zaman reddettikleri: sıfır boy, bozuk panel, çakışan çubuk ve panelin TAŞIYAN kenarında eksik çubuk zinciri
      const engel = yeni.filter(function (u) { return ENGEL_KODLARI.indexOf(u.kod) >= 0 || tasiyanKenarMi(m, u); });
      // taşımayan kenarda çubuk kalmadıysa uygulanır ama söylenir
      yeni.filter(function (u) { return u.kod === "panel-kenari" && engel.indexOf(u) < 0; }).slice(0, 2).forEach(function (u) { uy.push(u.mesaj); });
      if (engel.length) {
        S.sonUyari = "İşlem uygulanmadı (motor bu modeli çözmez): " + adla(engel.slice(0, 3).map(function (u) { return u.mesaj + (u.kod === "panel-kenari" ? " (taşıyan kenar)" : ""); }), m).join(" ") +
          (engel.length > 3 ? " … (+" + (engel.length - 3) + ")" : "") +
          (engel.some(function (u) { return u.kod === "cakisan-cubuk"; }) ? " Üst üste binen mevcut elemanı önce silin ya da işlemi başka yerde yapın." : "") +
          (engel.some(function (u) { return u.kod === "panel-kenari"; }) ? " Panel yükü kenarındaki çubuklara aktarılır: elemanı kopya olarak taşıyın (Doğrusal dizi / kopyalı Döndür, Ayna), paneli de seçin ya da panelin dağıtımını değiştirin." : "");
        toast(S.sonUyari); MB.ipucuYenile(); return null;
      }
      const oz = ozet(r);
      // kapı modeli çevirdi ama işlem hiçbir şeyi değiştirmediyse (ör. düzlem çubukları uçlarından geçiyor; özellik zaten aynı — rapor
      // degisen'i doldursa da) çevrilmiş model uygulanmaz
      if (cevrildi && JSON.stringify(m) === JSON.stringify(m0)) {
        S.sonUyari = "Değişiklik yok: işlem seçili elemanları değiştirmedi; model genel modele çevrilmedi."; toast(S.sonUyari); MB.ipucuYenile(); return null;
      }
      S.sonUyari = uy.join(" ");
      const mesaj = (etiket || "") + (oz ? (etiket ? ": " : "") + oz : "") + (uy.length ? " — ⚠ " + uy.join(" ") : "");
      let degisti;
      try { degisti = MB.binaAyarla(m, { etiket: mesaj || etiket || "Model güncellendi.", secim: sc.secim ? sc.secim(r, m) : undefined, sessiz: !!sc.sessiz && !uy.length }); }
      catch (e) { hata(e); return null; }
      if (degisti === false) toast(S.sonUyari || "Değişiklik yok.");
      MB.ipucuYenile();
      return r;
    }
    /**
     * Seçim üzerinde işlem: aks–kat elemanları seçiliyse önce genel model kapısı (onay; reddedilen işlemde model aynen kalır).
     * fn(model, ayrik) → rapor. İletilerdeki çubuk numaralarına aks–kat adresi eklenir (uygula). sc.genel: kapının işlem adı
     * (GENEL_ISLEM_ADLARI; etiket geçmiş zamanlı sonuç iletisidir, onay metnine yazılmaz).
     */
    function secimli(etiket, fn, sc) {
      sc = sc || {};
      const secim = MB.secim();
      let ay = secimAyir(secim), m = B(), notlar = [];
      const cubukVar = ay.cubuklar.length || ay.aksKat.some(function (s) { return s.tur !== "doseme"; });
      const panelVar = ay.paneller.length || ay.aksKat.some(function (s) { return s.tur === "doseme"; });
      if (!cubukVar && !(sc.panel && panelVar)) { toast(sc.bos || "Önce çubuk seçin (Seç aracıyla dokunun; çoklu seçim için Shift)."); return null; }
      let cevrildi = false;
      if (ay.aksKat.length) {
        // kuru çalıştırma (sorulmadan): işlem genelleştirilmiş modelde reddediliyor ya da hiçbir şeyi değiştirmiyorsa model çevrilmez
        let r0, m0;
        try { m0 = genellestirHazirla(m).model; const a0 = secimAyir(genelSecim(m0, secim)); r0 = a0.cubuklar.length || (sc.panel && a0.paneller.length) ? fn(m0, a0) : null; }
        catch (e) { hata(e); return null; }
        if (r0 && r0.reddedildi) { S.sonUyari = (r0.uyarilar || []).map(function (u) { return cubukAdlari(m0, u); }).join(" ") || "İşlem uygulanmadı."; toast(S.sonUyari); MB.ipucuYenile(); return null; }
        // model aynen kaldıysa (rapor degisen'i doldursa da: ör. Lb zaten otomatik) değişiklik yok — çevirmenin anlamı yok
        if (r0 && r0.model && JSON.stringify(r0.model) === JSON.stringify(m0)) {
          S.sonUyari = "Değişiklik yok: işlem seçili elemanları değiştirmiyor" + ((r0.uyarilar || []).length ? " (" + r0.uyarilar.join(" ") + ")" : "") + "; model genel modele çevrilmedi.";
          toast(S.sonUyari); MB.ipucuYenile(); return null;
        }
        let g;
        try { g = genelModeleGec(m, typeof sc.genel === "string" ? sc.genel : null); } catch (e) { hata(e); return null; }
        if (!g) return null;
        m = g.model; notlar = g.notlar; ay = secimAyir(genelSecim(m, secim)); cevrildi = !!g.cevrildi;
      }
      if (!ay.cubuklar.length && !(sc.panel && ay.paneller.length)) { toast(sc.bos || "Önce çubuk seçin (Seç aracıyla dokunun; çoklu seçim için Shift)."); return null; }
      return uygula(function (mm) { return fn(mm, ay); }, etiket, Object.assign({}, sc, { genel: false, notlar: notlar, model: m, cevrildi: cevrildi }));
    }
    function cubukSecimiVar() { return MB.secim().some(function (s) { return s.tur === "cubuk" || s.tur === "kolon" || s.tur === "kiris"; }); }
    const SECIM_NEDENI = "Önce bir çubuk, kolon ya da kiriş seçin.";
    /** Aks–kat kolon/kiriş seçimine genelleştirmeden özellik yazar (true: uygulandı; false: genel modelde yapılmalı). m: temel model (varsayılan B()) */
    function aksKatOzellik(etiket, oz, m) {
      const r = aksKatOzellikYaz(m || B(), MB.secim(), oz);
      if (!r) return false;
      uygula(function () { return { model: r.model, eklenen: {}, silinen: {}, degisen: {}, uyarilar: [] }; }, etiket + " (" + r.sayi + " aks–kat elemanı)", { bagla: false });
      return true;
    }

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
    /** İki nokta arasına çubuk (tür verilmezse geometriden). Aynı iki nokta arasında çubuk varsa kaldırır (sil: true ise). sc.islem: kapının işlem adı. */
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
      }, sc.etiket || "Çubuk çizildi", { genel: sc.islem || GENEL_ISLEM_ADLARI["cubuk-ciz"], secim: function (r) { return r.no != null ? [{ tur: "cubuk", no: r.no }] : undefined; } });
    }
    /** Çok sayıda REF çifti (hızlı kolon/kiriş/çubuk sürükleme): mevcut olanlar atlanır. etiket: işlem adı (GENEL_ISLEM_ADLARI; kapının ön eki da odur). */
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
      }, etiket, { genel: etiket, secim: function (r) { return (r.eklenen.cubuklar || []).map(function (no) { return { tur: "cubuk", no: no }; }); } });
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
        cubukCiz(S.ilk, y, "kiris", { etiket: "Eğik çubuk çizildi", islem: GENEL_ISLEM_ADLARI["egik-cubuk"] });
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
    parcaKipi("hizli-cubuk", function () { return null; }, null, GENEL_ISLEM_ADLARI["hizli-cubuk"],
      "Hızlı çubuk: bir aks parçasına dokunun (iki komşu kesişim arası; varsa kaldırır) ya da birden çok parça boyunca sürükleyin.");
    parcaKipi("kiris", function () { return yatay; }, function () { return "kiris"; }, GENEL_ISLEM_ADLARI["hizli-kiris"],
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
        cubuklarCiz(k.ciftler, function () { return "kolon"; }, GENEL_ISLEM_ADLARI["hizli-kolon"]);
      },
      surukleBasla: function (p) { const k = kolonCiftleriNokta(p); if (!k) return false; S.surukle = { ciftler: new Map(), kesisimler: new Map(), parcalar: new Map() }; kolonSurukle(p); return true; },
      surukle: kolonSurukle,
      surukleBitir: function () { const l = S.surukle ? Array.from(S.surukle.ciftler.values()) : []; S.surukle = null; tazele(); cubuklarCiz(l, function () { return "kolon"; }, GENEL_ISLEM_ADLARI["hizli-kolon"]); },
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
      }, "Panel", { genel: GENEL_ISLEM_ADLARI["hizli-panel"], secim: function (r) { return (r.eklenen.paneller || []).map(function (no) { return { tur: "panel", no: no }; }); } });
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
        const r = { model: m, eklenen: { cubuklar: eklenen }, silinen: {}, degisen: {}, uyarilar: uy };
        if (!eklenen.length) r.reddedildi = true;
        return r;
      }, (MAr && MAr.CAPRAZ_SECENEKLERI ? (MAr.CAPRAZ_SECENEKLERI.filter(function (s) { return s.id === tip; })[0] || { ad: tip }).ad : tip), { genel: GENEL_ISLEM_ADLARI["hizli-capraz"] });
    }
    kip("hizli-capraz", {
      ipucu: function () { const t = MAr ? MAr.CAPRAZ_SECENEKLERI.filter(function (s) { return s.id === S.capraz; })[0] : null; return "Hızlı çapraz (" + (t ? t.ad : S.capraz) + "): cephede bir göze ya da çatı paneline dokunun; sürükleyerek çoklu. Tip: sağ tık / Alt+↓."; },
      hareket: hover(function (p) { S.goz = gozBul(p); }),
      dokun: function (p, e, h) { const g = caprazGozu(p, h, e); if (!g) { toast("Bir göze (cephede dört kesişim arası) ya da dört köşeli panele dokunun."); return; } caprazYap([g]); },
      surukleBasla: function (p) { const g = gozBul(p); if (!g) return false; S.surukle = { gozler: new Map([[JSON.stringify(g.koseler), g]]) }; tazele(); return true; },
      surukle: function (p) { const g = gozBul(p); if (g && S.surukle) { S.surukle.gozler.set(JSON.stringify(g.koseler), g); tazele(); } },
      surukleBitir: function () { const l = S.surukle ? Array.from(S.surukle.gozler.values()) : []; S.surukle = null; tazele(); caprazYap(l); },
    });

    // Mesnet: düğüme dokun → mesnet türü (seçenek). Mesnet genel model kaydıdır (C1): aks–kat modelinde önce genel model kapısı
    // (onay; temeller aynen — C11). "Yaylı (elastik)" önce rijitlik penceresini açar (C13); ux/uy/rz yazan ön ayar rijit diyaframlı
    // kat seviyesindeyse önce "Rijit diyaframlı kat" sorulur (C14).
    function mesnetYaz(y, tur, sec) {
      return uygula(function (m) {
        const r = mesnetAta(m, aksRefZ(m, y.ref), tur, sec);
        return { model: r.model, eklenen: {}, silinen: {}, degisen: {}, uyarilar: r.eylem === "yok" ? ["Bu düğümde açık mesnet kaydı yok."] : r.notlar, eylem: r.eylem, reddedildi: r.eylem === "yok" };
      }, MESNET_ON_AYAR[tur].ad + " — " + (y.etiket || ""), { bagla: false, genel: tur !== "kaldir" ? GENEL_ISLEM_ADLARI.mesnet : false });
    }
    function mesnetDiyaframli(y, tur, sec) {
      let q = null;
      try { q = mesnetDiyaframSorusu(B(), y.ref, tur, Object.assign({ adres: y.etiket }, sec || {})); } catch (e) { q = null; }
      if (!q) { mesnetYaz(y, tur, sec); return; }
      const k = MB.kaplamaAc("mesnet-diyafram", q.baslik, { kucuk: true, odak: "[data-diyafram=dusey]" });
      k.govde.innerHTML = '<p class="bc-diyafram-metin">' + kacis(q.metin) + "</p>" + '<div class="dugmeler bc-dikey" role="group" aria-label="' + kacis(q.baslik) + '">' +
        q.secenekler.map(function (x) { return '<button type="button" class="dugme' + (x[0] === "dusey" ? " ana" : "") + '" data-diyafram="' + kacis(x[0]) + '">' + kacis(x[1]) + "</button>"; }).join("") + "</div>";
      k.govde.addEventListener("click", function (e) {
        const t = e.target.closest("[data-diyafram]");
        if (!t) return;
        const s_ = t.getAttribute("data-diyafram");
        MB.kaplamaKapat();
        if (s_ === "vazgec") { toast("İşlem iptal edildi."); return; }
        mesnetYaz(y, tur, Object.assign({}, sec || {}, { diyafram: s_ }));
      });
    }
    function yayPenceresi(y) {
      const k = MB.kaplamaAc("mesnet-yay", "Yaylı mesnet", { kucuk: true, odak: "[data-a=kz]" });
      k.govde.innerHTML = '<p class="not">' + kacis((y.etiket || refAdi(y.ref)) + ": bina eksenlerinde yay rijitlikleri. Boş ya da ≤ 0 alan yazılmaz; yaysız yönlerde düğümün mevcut açık mesnet kaydının tutulu serbestlikleri korunur (kayıt yoksa serbesttir).") + "</p>" +
        '<div class="bn-iki">' + YAY_ANAHTARLARI.map(function (a) { return alan(a.etiket, girdi(a.a, YAY_VARSAYILAN[a.a] != null ? String(YAY_VARSAYILAN[a.a]) : "", ' inputmode="decimal"')); }).join("") + "</div>" +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Uygula</button><button type="button" class="dugme" data-kaplama-kapat>Vazgeç</button></div>';
      const tamam = function () {
        let v;
        try { v = yayDegerleri(oku(k.govde)); } catch (x) { hata(x); return; }
        MB.kaplamaKapat();
        mesnetDiyaframli(y, "yay", { yay: v });
      };
      k.govde.querySelector("[data-tamam]").addEventListener("click", tamam);
      k.govde.addEventListener("keydown", function (e) { if (e.key === "Enter" && e.target && e.target.matches && e.target.matches("input")) { e.preventDefault(); tamam(); } });
    }
    kip("mesnet", {
      ipucu: function () { return "Mesnet (" + MESNET_ON_AYAR[S.mesnet].ad + "): bir düğüme ya da aks kesişimine dokunun. Tür: sağ tık / Alt+↓."; },
      hareket: hover(function (p) { S.yakalanan = yakala(p, { turler: ["dugum", "aks"] }); }),
      dokun: function (p) {
        const y = yakala(p, { turler: ["dugum", "aks"] });
        if (!y || !y.ref) { toast("Bir düğüme ya da aks kesişimine dokunun."); return; }
        const tur = S.mesnet, b0 = B();
        if (tur === "kaldir" && !liste(b0, "mesnetler").length) { toast("Modelde açık mesnet kaydı yok" + (genelMi(b0) ? "." : " (aks–kat modelinde temel mesnetleri kendiliğinden)." )); return; }
        if (tur === "yay") { yayPenceresi(y); return; }
        mesnetDiyaframli(y, tur);
      },
    });

    // Yük ata: çubuk / panel / düğüm → küçük iletişim kutusu (durum G, Q, S). Aks–kat modelinde (C10) kiriş ve döşeme de; model çevrilmez.
    kip("yuk-ata", {
      ipucu: function () {
        return genelMi(B()) ? "Yük ata (" + S.yuk + "): çubuğa (yayılı / tekil), panele (kN/m²) ya da düğüme (kuvvet) dokunun. Durum: sağ tık / Alt+↓."
          : "Yük ata (" + S.yuk + "): kirişe (düzgün yayılı), döşemeye (g / q kN/m²) ya da kat düzlemindeki düğüme (kuvvet) dokunun. Durum: sağ tık / Alt+↓.";
      },
      hareket: hover(function (p) { S.yakalanan = yakala(p, { turler: ["dugum", "aks"] }); }),
      dokun: function (p, e, h) {
        // düğüm / aks kesişimi yakalandıysa (uç noktası) düğüm yükü; değilse dokunulan çubuk, panel, kiriş ya da döşeme
        const b = B();
        const y = yakala(p, { turler: ["dugum", "aks"] });
        if (y && y.ref) {
          if (!genelMi(b) && !aksKatAdresi(b, y.ref)) { toast("Aks–kat modelinde düğüm yükü yalnız kat düzlemlerindeki aks kesişimlerine verilir."); return; }
          yukPenceresi({ tur: "dugum", ref: y.ref, etiket: y.etiket }); return;
        }
        if (h && h.kind === "nesne") {
          if (h.nesne === "kolon") { toast("Aks–kat kolonuna ek yük verilemez; kolonun üst düğümüne düğüm yükü verin."); return; }
          if (["cubuk", "panel", "kiris", "doseme"].indexOf(h.nesne) >= 0) { yukPenceresi({ tur: h.nesne, no: h.no }); return; }
        }
        toast("Bir çubuğa, kirişe, panele, döşemeye ya da düğüme dokunun.");
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
          const m0 = B(), q = MAk.aksSil(m0, { sistem: h.sistem, yon: h.yon, ad: h.ad, secenek: s });
          if (!q.silindi) { toast((q.uyarilar || []).join(" ") || "Aks silinemedi."); return; }
          // uygula() ile aynı kapı: motorun her zaman reddettiği YENİ bozukluk (sıfır boy, çakışan çubuk, bozuk panel, taşıyan kenarı
          // eksik panel) kaldıysa aks silinmez — ayıklama (aks_sistemi bozuklariAyikla) bunları gidermeliydi; gideremediyse söylenir
          const engel = aksSilEngelleri(m0, q.model);
          if (engel.length) {
            S.sonUyari = "Aks " + h.ad + " silinmedi (motor bu modeli çözmez): " + engel.slice(0, 3).map(function (u) { return cubukAdlari(q.model, u.mesaj); }).join(" ") +
              (engel.length > 3 ? " … (+" + (engel.length - 3) + ")" : "") +
              (s === "tasi" ? " — “Elemanlarla birlikte sil” seçeneğini kullanın ya da çakışan elemanları önce düzenleyin."
                : engel.some(function (u) { return u.kod === "panel-kenari"; }) ? " — taşıyan kenarının çubukları silinen paneller kalıyordu: önce o panelleri silin" + (r.komsu ? " ya da “en yakın aksa taşı”yı kullanın." : ".")
                  : (r.komsu ? " — “en yakın aksa taşı”yı kullanın ya da elemanları önce düzenleyin." : " — elemanları önce düzenleyin."));
            toast(S.sonUyari); MB.ipucuYenile(); return;
          }
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
      secimli("Taşındı", function (m, ay) { return MOp.tasi(m, secimNesnesi(ay), d[0], d[1], d[2]); }, { panel: true, genel: GENEL_ISLEM_ADLARI.tasi });
    });
    ikiNoktaKipi("dogrusal-dizi", "Doğrusal dizi: seçili elemanlar için kaynak kesişime, sonra bir aks aralığı ötedeki kesişime dokunun; sonra kopya sayısını girin.", secimYok, function (d) {
      const k = MB.kaplamaAc("dizi", "Doğrusal dizi", { kucuk: true, odak: "[data-a=adet]" });
      k.govde.innerHTML = '<p class="not">Öteleme: ΔX = ' + fmt(d[0]) + " m, ΔY = " + fmt(d[1]) + " m, ΔZ = " + fmt(d[2]) + " m (her kopya bir öteleme daha ileride).</p>" +
        alan("Kopya sayısı", girdi("adet", "1", ' inputmode="numeric"')) + '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Çoğalt</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const n = Math.round(sayi(oku(k.govde).adet) || 0);
        if (!(n >= 1 && n <= 50)) { toast("Kopya sayısı 1–50 olmalı."); return; }
        MB.kaplamaKapat();
        secimli(n + " kopya", function (m, ay) { return MOp.dogrusalDizi(m, secimNesnesi(ay), d[0], d[1], d[2], n); }, { panel: true, genel: GENEL_ISLEM_ADLARI["dogrusal-dizi"] });
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
      }, "Yapıştırıldı", { islem: GENEL_ISLEM_ADLARI.yapistir });
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
          secimli("Döndürüldü (" + fmtK(aci) + "°)", function (m, ay) { return MOp.dondur(m, secimNesnesi(ay), { nokta: y.P, yon: yon }, aci, { kopya: !!o.kopya, adet: Math.max(1, Math.round(sayi(o.adet) || 1)) }); }, { panel: true, genel: GENEL_ISLEM_ADLARI.dondur });
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
          secimli("Aynalandı", function (m, ay) { return MOp.ayna(m, secimNesnesi(ay), d, { kopya: !!o.kopya }); }, { panel: true, genel: GENEL_ISLEM_ADLARI.ayna });
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
            '<td><input type="checkbox" data-sis-gor="' + kacis(s.ad) + '"' + (s.gorunur !== false ? " checked" : "") + ' aria-label="' + kacis(s.ad) + ' görünür"></td>' +
            '<td><button type="button" class="dugme kucuk" data-sis-duzenle="' + kacis(s.ad) + '" aria-label="' + kacis(s.ad) + ' sistemini düzenle">Düzenle</button> <button type="button" class="se-sil" data-sis-sil="' + kacis(s.ad) + '" aria-label="Sil">✕</button></td></tr>';
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
        const dz = e.target.closest("[data-sis-duzenle]");
        if (dz) { aksDuzenleyici("s:" + dz.getAttribute("data-sis-duzenle")); return; }      // orijin, açı ve aksları aks verisi tablosunda
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
    /**
     * Üreteç penceresi: form + canlı önizleme. hesapla(o, model) → {model, rapor, gorunum, ozet, uyarilar}. Uygulamada genel model
     * kapısından geçilir (aks–kat modeli onayla genelleştirilir) ve hesapla çevrilmiş modelle yeniden çalışır.
     * duzen: {no} ise mevcut üreteç düzenlenir (hesapla ModelOps.uretecGuncelle raporu döndürür).
     */
    function ureticiPencere(tur, baslik, formHtml, hesapla, uygulaMetni, duzen) {
      const k = MB.kaplamaAc(tur, duzen ? baslik + " — düzenle (üreteç " + duzen.no + ")" : baslik, { genis: false });
      k.govde.innerHTML = '<div class="bc-uretec"><div class="bc-uretec-form">' + formHtml + '</div><div class="bc-uretec-oniz"><div class="bc-oniz-kap"></div><p class="not bc-oniz-not" aria-live="polite"></p></div></div>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-uret>' + kacis(duzen ? "Üreteci güncelle" : uygulaMetni || "Üret") + '</button><button type="button" class="dugme" data-kaplama-kapat>Vazgeç</button></div>';
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
        const o = oku(k.govde);
        try { hesapla(o, B()); } catch (e) { hata(e); return; }
        MB.kaplamaKapat();
        uygula(function (m0) { return hesapla(o, m0).rapor; }, duzen ? "Üreteç güncellendi (" + baslik + ")" : baslik, { genel: duzen ? GENEL_ISLEM_ADLARI.uretec : baslik });
      });
      onizle();
      return k;
    }
    function aksSecenek(yon) { return aksListesi(B(), yon).map(function (a) { return [a.ad, a.ad + " (" + fmtK(a.konum) + ")"]; }); }
    /** Kesit seçeneği: verilen ad modelde yoksa listenin başına eklenir (düzenlemede üretecin kesiti korunur). */
    function kesitSecenek(b, tur, ad) {
      const l = kesitListesi(b, tur);
      if (ad && !l.some(function (x) { return x[0] === ad; })) l.unshift([ad, ad]);
      return l;
    }
    function besikPenceresi(duzen) {
      const b = B(), xs = aksListesi(b, "x"), ys = aksListesi(b, "y"), zs = aksListesi(b, "z"), f = duzen ? duzen.f : null;
      const kolonX = f ? xs.filter(function (a) { return f.kx.indexOf(a.ad) >= 0; }) : xs.filter(function (a) { return a.ad.indexOf("'") < 0; });
      const zt = zs[0] || { ad: "", konum: 0 }, sac = zs.filter(function (a) { return /sa[çc]ak/i.test(a.ad); })[0] || zs[1] || { konum: zt.konum + 6 };
      const mah = zs.filter(function (a) { return /mahya/i.test(a.ad); })[0] || { konum: sac.konum + 1.5 };
      const celik = b.sistem === "celik";
      const v = function (ad, vars) { return f && f[ad] != null ? f[ad] : vars; };
      const form = '<fieldset class="bc-alanlar"><legend>Kolon aksları (açıklıklar ardışık iki aks arası' + (f ? "; düzenlemede tek açıklık" : "") + ')</legend><div class="bc-cipler">' + xs.map(function (a) {
        return '<label class="bn-onay"><input type="checkbox" data-a="kx_' + kacis(a.ad) + '"' + (kolonX.indexOf(a) >= 0 ? " checked" : "") + "> " + kacis(a.ad) + "</label>";
      }).join("") + "</div></fieldset>" +
        '<div class="bn-iki">' + alan("İlk çerçeve (Y aksı)", sec("y0", aksSecenek("y"), v("y0", (ys[0] || {}).ad))) + alan("Son çerçeve (Y aksı)", sec("y1", aksSecenek("y"), v("y1", (ys[ys.length - 1] || {}).ad))) + "</div>" +
        '<div class="bn-iki">' + alan("Taban (Z aksı)", sec("taban", aksSecenek("z"), v("taban", zt.ad))) + alan("Mesnet", sec("mesnet", [["ankastre", "Ankastre"], ["mafsal", "Mafsallı"], ["yok", "Ekleme (temelden)"]], v("mesnet", "ankastre"))) + "</div>" +
        '<div class="bn-iki">' + alan("Saçak kotu (m)", girdi("sacak", v("sacak", fmtK(sac.konum).replace(",", ".")), ' inputmode="decimal"')) + alan("Mahya kotu (m)", girdi("mahya", v("mahya", fmtK(mah.konum).replace(",", ".")), ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Kolon kesiti", sec("kolon", kesitSecenek(b, "kolon", f && f.kolon), v("kolon", kesitSagla(kopya(b), "kolon")))) + alan("Mertek kesiti", sec("mertek", kesitSecenek(b, "kiris", f && f.mertek), v("mertek", kesitSagla(kopya(b), "kiris")))) + "</div>" +
        '<div class="bn-iki">' + alan("Vute boyu (m; 0 = vutesiz)", girdi("vuteBoy", v("vuteBoy", celik ? "2" : "0"), ' inputmode="decimal"')) + alan("Vute ek yüksekliği (m)", girdi("vuteH", v("vuteH", "0.4"), ' inputmode="decimal"')) + "</div>" +
        onay("asik", "Aşıklar", f ? f.asik : true) + '<div class="bn-iki">' + alan("Aşık aralığı (m)", girdi("asikAralik", v("asikAralik", "2.5"), ' inputmode="decimal"')) + alan("Aşık kesiti", sec("asikKesit", kesitSecenek(b, "asik", f && f.asikKesit), v("asikKesit", kesitSagla(kopya(b), "asik")))) + "</div>" +
        onay("panel", "Çatı kaplaması (sac panel, kalınlık 0)", f ? f.panel : true) +
        '<p class="not">Eksik saçak / mahya Z aksları ve her açıklığın ortasındaki mahya X aksı kendiliğinden eklenir; düğümler aks kesişimi ya da mertek bölme noktasıdır.</p>';
      ureticiPencere("besik-cerceve", GENEL_ISLEM_ADLARI["besik-cerceve"], form, function (o, m0) {
        const kx = xs.filter(function (a) { return o["kx_" + a.ad]; }).map(function (a) { return a.ad; });
        if (kx.length < 2) throw new Error("En az iki kolon aksı işaretleyin.");
        if (duzen && kx.length !== 2) throw new Error("Üreteç düzenlenirken tek açıklık (iki kolon aksı) işaretleyin.");
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
        if (duzen) {
          if (p.parametreler.length !== 1) throw new Error("Çerçeve aks aralıkları eşit değil; düzenlemede tek üreteç güncellenebilir (silip yeniden üretin).");
          const par = Object.assign({ vute: null, asik: null, panel: null }, p.parametreler[0]);
          if (!par.asik) par.asik = null;
          const r = MOp.uretecGuncelle(m, duzen.no, par);
          ilk = r; m = r.model;
          (r.uyarilar || []).forEach(function (u) { if (uy.indexOf(u) < 0) uy.push(u); });
          eklenen = r.eklenen.cubuklar || [];
          r.uyarilar = (p.eklenen.length ? ["Eklenen akslar: " + p.eklenen.join(", ") + "."] : []).concat(uy);
          return { model: m, rapor: r, gorunum: { tur: "cephe", y: yl[0] }, ozet: "Üreteç " + duzen.no + " · " + eklenen.length + " yeni çubuk" + (r.egim != null ? " · çatı eğimi " + fmt(r.egim, 1) + "°" : ""), uyarilar: uy };
        }
        p.parametreler.forEach(function (par) {
          const r = MOp.besikCerceveUret(m, par);
          if (!ilk) ilk = r;
          m = r.model;
          (r.uyarilar || []).forEach(function (u) { if (uy.indexOf(u) < 0) uy.push(u); });
          eklenen = eklenen.concat(r.eklenen.cubuklar || []);
        });
        const rapor = { model: m, eklenen: { cubuklar: eklenen }, silinen: {}, degisen: {}, uyarilar: (p.eklenen.length ? ["Eklenen akslar: " + p.eklenen.join(", ") + "."] : []).concat(uy) };
        return { model: m, rapor: rapor, gorunum: { tur: "cephe", y: yl[0] }, ozet: p.parametreler.length + " üreteç · " + eklenen.length + " çubuk" + (ilk && ilk.egim != null ? " · çatı eğimi " + fmt(ilk.egim, 1) + "°" : ""), uyarilar: uy };
      }, "Çerçeveleri üret", duzen);
    }
    function makasPenceresi(duzen) {
      const b = B(), xs = aksListesi(b, "x"), ys = aksListesi(b, "y"), zs = aksListesi(b, "z"), f = duzen ? duzen.f : null;
      const v = function (ad, vars) { return f && f[ad] != null ? f[ad] : vars; };
      const tipler = (MOp.MAKAS_TIPLERI || []).map(function (t) { return [t, { pratt: "Pratt", howe: "Howe", warren: "Warren", "warren-dikmeli": "Warren (dikmeli)", k: "K makas", fink: "Fink", "besik-pratt": "Beşik Pratt", "besik-howe": "Beşik Howe" }[t] || t]; });
      const zs0 = zs.filter(function (a) { return /sa[çc]ak/i.test(a.ad); })[0] || zs[zs.length - 1] || {};
      const form = alan("Makas tipi", sec("tip", tipler, v("tip", "besik-pratt"))) +
        '<div class="bn-iki">' + alan("Sol mesnet (X aksı)", sec("xa", aksSecenek("x"), v("xa", (xs[0] || {}).ad))) + alan("Sağ mesnet (X aksı)", sec("xb", aksSecenek("x"), v("xb", (xs[xs.length - 1] || {}).ad))) + "</div>" +
        (f ? '<p class="not">Makas Y aksı: ' + kacis(f.y0) + " (düzenlemede değişmez).</p>" + '<input type="hidden" data-a="y0" value="' + kacis(f.y0) + '"><input type="hidden" data-a="y1" value="' + kacis(f.y0) + '">'
          : '<div class="bn-iki">' + alan("İlk makas (Y aksı)", sec("y0", aksSecenek("y"), (ys[0] || {}).ad)) + alan("Son makas (Y aksı)", sec("y1", aksSecenek("y"), (ys[0] || {}).ad)) + "</div>") +
        '<div class="bn-iki">' + alan("Mesnet kotu (Z aksı)", sec("z", aksSecenek("z"), v("z", zs0.ad))) + alan("Yükseklik / mahya (m)", girdi("h", v("h", "2"), ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Göz sayısı", girdi("goz", v("goz", "8"), ' inputmode="numeric"')) + alan("Uç yüksekliği (beşik; m)", girdi("uc", v("uc", "0"), ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Üst başlık", sec("ust", kesitSecenek(b, "makas-ust", f && f.ust), v("ust", kesitSagla(kopya(b), "makas-ust")))) + alan("Alt başlık", sec("alt", kesitSecenek(b, "makas-alt", f && f.alt), v("alt", kesitSagla(kopya(b), "makas-alt")))) + "</div>" +
        '<div class="bn-iki">' + alan("Dikme", sec("dikme", kesitSecenek(b, "makas-dikme", f && f.dikme), v("dikme", kesitSagla(kopya(b), "makas-dikme")))) + alan("Diyagonal", sec("diyagonal", kesitSecenek(b, "makas-diyagonal", f && f.diyagonal), v("diyagonal", kesitSagla(kopya(b), "makas-diyagonal")))) + "</div>" +
        onay("mafsal", "Gövde çubukları mafsallı (kafes)", f ? f.mafsal : true) +
        alan("Düzlem dışı tutma (mafsallı gövdede)", sec("yanal", [["uc-dikme", "Uç dikmeleri rijit (paralel başlıklı ve K makasta mekanizma olmaz)"], ["yok", "Yok (bütün gövde mafsallı)"]], v("yanal", "uc-dikme"))) +
        '<p class="not">Üst başlık / mahya Z aksı ve beşik tiplerde açıklık ortası aksı yoksa eklenir; ara düğümler bölme noktasıdır. Üst başlığın düzlem dışı burkulma boyu, aşık ya da düzlem dışı bağ yoksa bütün açıklıktır.</p>';
      ureticiPencere("makas", GENEL_ISLEM_ADLARI.makas, form, function (o, m0) {
        const yi = ys.findIndex(function (a) { return a.ad === o.y0; }), yj = ys.findIndex(function (a) { return a.ad === o.y1; });
        const yl = ys.slice(Math.min(yi, yj), Math.max(yi, yj) + 1).map(function (a) { return a.ad; });
        if (o.xa === o.xb) throw new Error("Sol ve sağ mesnet farklı aks olmalı.");
        let m = kopya(m0), uy = [], ekl = [], eklAks = [];
        const kes = { ust: kesitHazirla(m, o.ust, "makas-ust"), alt: kesitHazirla(m, o.alt, "makas-alt"), dikme: kesitHazirla(m, o.dikme, "makas-dikme"), diyagonal: kesitHazirla(m, o.diyagonal, "makas-diyagonal") };
        let rapor = null;
        yl.forEach(function (y) {
          const p = makasPlan(m, { tip: o.tip, bas: { aks: [o.xa, y], z: o.z }, son: { aks: [o.xb, y], z: o.z }, yukseklik: sayi(o.h), goz: sayi(o.goz), kesitler: kes, uc_yukseklik: sayi(o.uc) || 0,
            mafsalli_govde: !!o.mafsal, yanal_tutma: o.yanal === "yok" ? "yok" : "uc-dikme" });
          m = p.model; p.eklenen.forEach(function (x) { if (eklAks.indexOf(x) < 0) eklAks.push(x); });
          if (duzen && !(sayi(o.uc) > 0)) delete p.parametre.uc_yukseklik;
          const r = duzen ? MOp.uretecGuncelle(m, duzen.no, Object.assign({ uc_yukseklik: 0 }, p.parametre)) : MOp.makasUret(m, p.parametre);
          if (duzen) rapor = r;
          m = r.model; ekl = ekl.concat(r.eklenen.cubuklar || []);
          (r.uyarilar || []).forEach(function (u) { if (uy.indexOf(u) < 0) uy.push(u); });
        });
        const uyT = (eklAks.length ? ["Eklenen akslar: " + eklAks.join(", ") + "."] : []).concat(uy);
        if (rapor) rapor.uyarilar = uyT;
        return { model: m, rapor: rapor || { model: m, eklenen: { cubuklar: ekl }, silinen: {}, degisen: {}, uyarilar: uyT },
          gorunum: { tur: "cephe", y: yl[0] }, ozet: (duzen ? "Üreteç " + duzen.no : yl.length + " makas") + " · " + ekl.length + (duzen ? " yeni çubuk" : " çubuk"), uyarilar: uy };
      }, "Makasları üret", duzen);
    }
    function asikPenceresi(duzen) {
      const b = B(), ay = secimAyir(MB.secim()), f = duzen ? duzen.f : null;
      const hedefMetin = f ? f.hedefMetin : ay.paneller.length ? "Panel " + ay.paneller[0] : ay.cubuklar.length >= 2 ? ay.cubuklar.length + " mertek çubuğu" : null;
      if (!hedefMetin) { toast("Aşık için önce en az iki mertek çubuğunu (ya da bir çatı panelini) seçin."); return; }
      const v = function (ad, vars) { return f && f[ad] != null ? f[ad] : vars; };
      const form = '<p class="not">Hedef: ' + kacis(hedefMetin) + (f ? " (üretecin hedefi)" : " (seçim)") + '.</p><div class="bn-iki">' + alan("Aşık aralığı (m)", girdi("aralik", v("aralik", "1.5"), ' inputmode="decimal"')) +
        alan("Aşık kesiti", sec("kesit", kesitSecenek(b, "asik", f && f.kesit), v("kesit", kesitSagla(kopya(b), "asik")))) + "</div>" + onay("uclar", "Saçak ve mahyada da aşık", f ? f.uclar : true) + onay("mafsal", "Aşıklar mafsallı (basit kiriş)", f ? f.mafsal : true) +
        '<p class="not">Aşık noktaları mertek üzerinde bölme düğümüdür (aks taşınınca birlikte taşınır); aşık yerel ekseni çatı eğimine döndürülür.</p>';
      ureticiPencere("asik", GENEL_ISLEM_ADLARI.asik, form, function (o, m0) {
        const m = kopya(m0), ks = kesitHazirla(m, o.kesit, "asik");
        let r;
        if (duzen) r = MOp.uretecGuncelle(m, duzen.no, { aralik: sayi(o.aralik), kesit: ks, secenek: { uclar: !!o.uclar, mafsalli: !!o.mafsal } });
        else {
          const hedef = ay.paneller.length ? { panel: ay.paneller[0] } : ay.cubuklar;
          r = MOp.asikUret(m, hedef, sayi(o.aralik), ks, { uclar: !!o.uclar, mafsalli: !!o.mafsal });
        }
        const zs = aksListesi(r.model, "z");
        return { model: r.model, rapor: r, gorunum: { tur: "plan", z: zs[zs.length - 1].ad }, ozet: (r.asiklar || []).length + " aşık · gerçek aralık " + fmt(r.aralik_gercek) + " m", uyarilar: r.uyarilar };
      }, "Aşıkları üret", duzen);
    }
    function krenPenceresi(duzen) {
      const b = B(), xs = aksListesi(b, "x"), zs = aksListesi(b, "z"), f = duzen ? duzen.f : null;
      const v = function (ad, vars) { return f && f[ad] != null && f[ad] !== "" ? f[ad] : vars; };
      const kz = zs.filter(function (a) { return /kren/i.test(a.ad); })[0];
      // varsayılan kren kotu: "Kren" Z aksı; yoksa tabandan saçağa (ya da en üst kata) yüksekliğin ~3/4'ü (kolonları keser)
      const tepe = zs.filter(function (a) { return /sa[çc]ak/i.test(a.ad); })[0] || zs.filter(function (a) { return a.kat != null; }).slice(-1)[0] || zs[zs.length - 1];
      const kotVars = kz ? kz.konum : zs.length && tepe ? r6(zs[0].konum + Math.round(0.75 * (tepe.konum - zs[0].konum) / 0.05) * 0.05) : 6;
      const form = (f ? '<p class="not">Kren hatları ve kolonları üretecin kaydındaki gibi kalır (' + f.hatSayisi + " hat).</p>"
          : '<div class="bn-iki">' + alan("1. kren hattı (X aksı)", sec("h1", aksSecenek("x"), (xs[0] || {}).ad)) + alan("2. kren hattı (X aksı)", sec("h2", aksSecenek("x"), (xs[2] || xs[1] || {}).ad)) + "</div>") +
        '<div class="bn-iki">' + alan("Kren kotu (m)", girdi("kot", v("kot", String(kotVars)), ' inputmode="decimal"')) + alan("Konsol boyu (m; 0 = kolona oturur)", girdi("konsol", v("konsol", "0.5"), ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Kren kirişi", sec("kiris", kesitSecenek(b, "kren", f && f.kiris), v("kiris", kesitSagla(kopya(b), "kren")))) + alan("Konsol", sec("konsolK", kesitSecenek(b, "kiris", f && f.konsolK), v("konsolK", kesitSagla(kopya(b), "kiris")))) + "</div>" +
        "<h3>Kren</h3>" + '<div class="bn-iki">' + alan("P_maks (kN/tekerlek)", girdi("Pmaks", v("Pmaks", "80"), ' inputmode="decimal"')) + alan("P_min (kN)", girdi("Pmin", v("Pmin", "25"), ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("H yanal (kN)", girdi("Hy", v("Hy", "8"), ' inputmode="decimal"')) + alan("H fren (kN)", girdi("Hf", v("Hf", "6"), ' inputmode="decimal"')) + "</div>" +
        '<div class="bn-iki">' + alan("Tekerlek aralığı (m)", girdi("ara", v("ara", "3.5"), ' inputmode="decimal"')) + alan("Dinamik katsayı", girdi("din", v("din", "1.25"), ' inputmode="decimal"')) + "</div>" +
        '<p class="not">Kren kotunda Z aksı yoksa “Kren” adıyla eklenir; kolonlar bu kotta bölünür. Kren yükleri K yük durumunda (konum başına alt durum).' + (genelGecisGerekli(b) ? " Aks–kat modelinde kren yolu çubuk kolon gerektirir: uygularken model genel modele çevrilir (onay sorulur)." : "") + "</p>";
      ureticiPencere("kren-yolu", GENEL_ISLEM_ADLARI["kren-yolu"], form, function (o, m0) {
        let m = kopya(m0);
        const not = [];
        // aks–kat kolonları kren kotunda bölünemez: önizlemede genelleştirilmiş kopya (uygulamada genel model kapısı sorar)
        if (genelGecisGerekli(m)) { m = genellestirHazirla(m).model; not.push("Model genel (surum 3) modele çevrilecek: kren yolu çubuk kolon gerektirir."); }
        const kes = { kiris: kesitHazirla(m, o.kiris, "kren"), konsol: kesitHazirla(m, o.konsolK, "kiris") };
        const kren = { tekerlek: { P_maks: sayi(o.Pmaks), P_min: sayi(o.Pmin), H_yanal: sayi(o.Hy), H_fren: sayi(o.Hf), aralik: sayi(o.ara), adet: 2 }, dinamik: sayi(o.din) || 1.25 };
        let r, eklenen = [];
        if (duzen) {
          const kot = sayi(o.kot);
          if (kot == null) throw new Error("Kren kotu sayı olmalı.");
          const a = aksSagla(m, "z", kot, "Kren"); m = a.model;
          if (a.eklendi) eklenen.push("Z aksı " + a.ad + " (" + fmt(kot) + " m)");
          r = MOp.uretecGuncelle(m, duzen.no, { kot: kot, konsol_boy: sayi(o.konsol) || 0, kesitler: kes, kren: kren });
        } else {
          if (o.h1 === o.h2) throw new Error("İki farklı kren hattı aksı seçin.");
          const p = krenPlan(m, { hatlar: [o.h1, o.h2], yon: "x", kot: sayi(o.kot) });
          if (p.kolonlar.length < 2) throw new Error("Seçilen akslarda kren kotunu kesen kolon çubukları yok" + (p.uyarilar.length ? ": " + p.uyarilar.join(" ").replace(/\.$/, "") : "") + ". Kren hatlarında (X aksları) kren kotunun altından üstüne uzanan kolonlar olmalı; yoksa Hızlı kolon ile çizin.");
          eklenen = p.eklenen;
          r = MOp.krenYoluUret(p.model, p.kolonlar, sayi(o.kot), sayi(o.konsol) || 0, kes, kren);
        }
        r.uyarilar = (eklenen.length ? ["Eklenen akslar: " + eklenen.join(", ") + "."] : []).concat(r.uyarilar || []);
        return { model: r.model, rapor: r, gorunum: f ? { tur: "3b" } : { tur: "cephe", x: o.h1 }, ozet: (r.kirisler || []).length + " kren kirişi, " + (r.konsollar || []).length + " konsol", uyarilar: not.concat(r.uyarilar) };
      }, "Kren yolunu üret", duzen);
    }
    /** Çapraz üretecini düzenle: tip, kesit, mafsallı uçlar (göz aynı). */
    function caprazDuzenlePenceresi(duzen) {
      const b = B(), f = duzen.f, kayit = uretecKaydi(b, duzen.no);
      const tipler = ((MAr && MAr.CAPRAZ_SECENEKLERI) || MOp.CAPRAZ_TIPLERI.map(function (t) { return { id: t, ad: t }; })).map(function (t) { return [t.id, t.ad]; });
      const form = alan("Çapraz tipi", sec("tip", tipler, f.tip)) + alan("Kesit", sec("kesit", kesitSecenek(b, "capraz", f.kesit), f.kesit || kesitSagla(kopya(b), "capraz"))) +
        onay("mafsal", "Uçlar mafsallı", f.mafsal) + '<p class="not">Çaprazın gözü (dört köşe) aynı kalır; bölünen kenar elemanları yeniden birleştirilip yeni tipe göre bölünür.</p>';
      ureticiPencere("hizli-capraz", "Çapraz", form, function (o, m0) {
        const m = kopya(m0), ks = kesitHazirla(m, o.kesit, "capraz");
        let P = null;
        try { P = (kayit.goz || []).map(function (r) { return MAk.refKoordinat(m, r); }); } catch (e) { P = null; }
        const s = caprazSecenek(o.tip, P ? { P: P } : null, { kesit: ks, mafsalli_uclar: !!o.mafsal });
        const r = MOp.uretecGuncelle(m, duzen.no, { tip: o.tip, secenek: s });
        let g = null;
        if (P && P.length === 4) {
          const dz = Math.max.apply(null, P.map(function (q) { return q[2]; })) - Math.min.apply(null, P.map(function (q) { return q[2]; }));
          if (dz > TOL) { const ya = aksAdi(m, "y", P[0][1]), xa = aksAdi(m, "x", P[0][0]); g = Math.abs(P[0][1] - P[1][1]) < TOL && ya ? { tur: "cephe", y: ya } : xa ? { tur: "cephe", x: xa } : null; }
          else { const za = aksAdi(m, "z", P[0][2]); g = za ? { tur: "plan", z: za } : null; }
        }
        return { model: r.model, rapor: r, gorunum: g || { tur: "3b" }, ozet: "Üreteç " + duzen.no + " · " + (r.caprazlar || []).length + " çapraz", uyarilar: r.uyarilar };
      }, "Güncelle", duzen);
    }
    /** Üreteç kaydını uygun pencerede düzenleme kipinde açar (B.uretecler[no]). */
    function uretecDuzenle(kayit) {
      if (!kayit) { toast("Önce üreteçle oluşturulmuş bir çubuk ya da panel seçin (makas, beşik çerçeve, aşık, kren yolu, çapraz)."); return; }
      const f = uretecFormu(B(), kayit);
      if (f.hata) { toast(f.hata); return; }
      const d = { no: +kayit.no, f: f };
      if (f.tur === "makas") makasPenceresi(d);
      else if (f.tur === "besik-cerceve") besikPenceresi(d);
      else if (f.tur === "asik") asikPenceresi(d);
      else if (f.tur === "kren-yolu") krenPenceresi(d);
      else caprazDuzenlePenceresi(d);
    }
    function seciliUretec() {
      const b = B();
      for (const s of MB.secim()) { if (s.tur === "cubuk" || s.tur === "panel") { const k = uretecKaydi(b, s); if (k) return k; } }
      return null;
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
        }, { genel: GENEL_ISLEM_ADLARI.bol, secim: function (r) { return (r.parcalar || []).map(function (no) { return { tur: "cubuk", no: no }; }); } });
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
      if (nolar) return uygula(function (m) { return f(m, null); }, "Birleştirildi", { islem: GENEL_ISLEM_ADLARI.birlestir, secim: function (r) { return (r.birlesen || []).map(function (x) { return { tur: "cubuk", no: x.no != null ? x.no : x }; }); } });
      void sec0;
      return secimli("Birleştirildi", f, { genel: GENEL_ISLEM_ADLARI.birlestir, secim: function (r) { return (r.birlesen || []).map(function (x) { return { tur: "cubuk", no: x.no != null ? x.no : x }; }); } });
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
          { genel: GENEL_ISLEM_ADLARI.mafsal, secim: function (r, mm) { void mm; return secimAyir(MB.secim()).cubuklar.length ? MB.secim() : undefined; } });
      });
    }
    function ozellikPenceresi() {
      const b = B(), ay = secimAyir(MB.secim());
      const ak0 = !ay.cubuklar.length && ay.aksKat.length ? ay.aksKat.filter(function (s) { return s.tur !== "doseme"; })[0] : null;
      const c0 = ay.cubuklar.length ? liste(b, "cubuklar").filter(function (c) { return +c.no === ay.cubuklar[0]; })[0]
        : ak0 ? liste(b, ak0.tur === "kolon" ? "kolonlar" : "kirisler").filter(function (c) { return +c.no === +ak0.no; })[0] : null;
      if (!secimCubukSayisi()) return false;
      const k = MB.kaplamaAc("ozellik-ata", "Özellik ata (" + secimCubukSayisi() + (ay.aksKat.length && !ay.cubuklar.length ? " eleman)" : " çubuk)"), { kucuk: true });
      const satir = function (ad, etiket, ic) { return '<div class="bc-oz-satir">' + onay("d_" + ad, etiket, false) + ic + "</div>"; };
      const turler = [["kolon", "Kolon"], ["kiris", "Kiriş"], ["capraz", "Çapraz"], ["makas-ust", "Makas üst başlık"], ["makas-alt", "Makas alt başlık"], ["makas-dikme", "Makas dikmesi"], ["makas-diyagonal", "Makas diyagonali"], ["asik", "Aşık"], ["kren", "Kren kirişi"], ["bag", "Bağ"], ["diger", "Diğer"]];
      const duvarlar = [["", "Yok"]].concat(Object.keys(b.duvarlar || {}).map(function (d) { return [d, d]; }));
      const aci0 = c0 ? (c0.aci != null ? c0.aci : c0.yon === "y" ? 90 : 0) : 0;
      k.govde.innerHTML = '<p class="not">İşaretli alanlar seçili bütün çubuklara uygulanır.' + (ay.aksKat.length && !ay.cubuklar.length ? " Aks–kat kolon/kirişinde kesit, grup, kolon açısı (0° / 90°), kiriş duvarı ve duvar yüksekliği modeli çevirmeden yazılır (duvar alanları yalnız kirişlere); tür, Lb, K, yalnız çekme ve başka açılar modeli genel modele çevirir." : "") + "</p>" +
        satir("kesit", "Kesit", sec("kesit", kesitListesi(b, "kiris"), c0 && c0.kesit)) + satir("tur", "Tür", sec("tur", turler, c0 ? c0.tur || (ak0 ? ak0.tur : "diger") : "diger")) +
        satir("aci", "Yerel eksen açısı (°)", girdi("aci", aci0, ' inputmode="decimal"')) + satir("grup", "Grup", girdi("grup", c0 && c0.grup || "")) +
        satir("Lb", "Lb (m; boş = otomatik)", girdi("Lb", c0 && c0.Lb != null ? c0.Lb : "", ' inputmode="decimal"')) + satir("K", "K güçlü / zayıf", girdi("K", c0 && Array.isArray(c0.K) ? c0.K.join(" ") : "1 1")) +
        satir("duvar", "Duvar (kiriş üstü)", sec("duvar", duvarlar, c0 && c0.duvar || "")) + satir("duvar_h", "Duvar yüksekliği (m; boş = kat yüksekliği)", girdi("duvar_h", c0 && c0.duvar_h != null ? c0.duvar_h : "", ' inputmode="decimal"')) +
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
          if (o.d_duvar) oz.duvar = o.duvar ? String(o.duvar) : null;
          if (o.d_duvar_h) { if (String(o.duvar_h).trim() === "") oz.duvar_h = null; else { const v = sayi(o.duvar_h); if (!(v > 0)) throw new Error("Duvar yüksekliği pozitif olmalı (m)."); oz.duvar_h = v; } }
        } catch (e) { hata(e); return; }
        if (!Object.keys(oz).length) { toast("Değiştirilecek alanı işaretleyin."); return; }
        MB.kaplamaKapat();
        if (aksKatOzellik("Özellikler atandı", oz)) return;
        secimli("Özellikler atandı", function (m, a) { const r = MOp.ozellikAta(m, a.cubuklar, oz); r.degisen = { cubuklar: a.cubuklar }; return r; }, { bagla: false, genel: GENEL_ISLEM_ADLARI["ozellik-ata"] });
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
        const kesitEkle = function (m) {
          const mm = kopya(m);
          if (tanim && !(mm.kesitler || {})[ad]) { mm.kesitler = mm.kesitler || {}; mm.kesitler[ad] = tanim; if (!mm.malzemeler) mm.malzemeler = {}; if (!mm.malzemeler[tanim.malzeme]) mm.malzemeler[tanim.malzeme] = { kutuphane: tanim.malzeme }; }
          return mm;
        };
        // aks–kat kolon/kiriş seçimi: kolonlar/kirisler[].kesit (model çevrilmez)
        if (aksKatOzellik("Kesit " + ad + " atandı", { kesit: ad }, kesitEkle(B()))) return;
        secimli("Kesit " + ad + " atandı", function (m, a) {
          const r = MOp.ozellikAta(kesitEkle(m), a.cubuklar, { kesit: ad }); r.degisen = { cubuklar: a.cubuklar }; return r;
        }, { bagla: false, genel: GENEL_ISLEM_ADLARI["kesit-degistir"] });
      });
    }
    function aciPenceresi() {
      if (!secimCubukSayisi()) { toast("Yerel eksen açısı için çubuk seçin."); return; }
      const k = MB.kaplamaAc("aci", "Yerel eksen açısı", { kucuk: true, odak: "[data-a=aci]" });
      k.govde.innerHTML = alan("Açı (°; x′ çevresinde, sağ el kuralı)", girdi("aci", "90", ' inputmode="decimal"')) + '<p class="not">0°: kesitin h boyutu (güçlü eksen) y′ doğrultusunda; kolonda 90° kesiti çevirir. Aks–kat kolonunda 0° / 90° kolon yönünü (x / y) değiştirir; başka açılar modeli genel modele çevirir.</p>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Uygula</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const v = sayi(oku(k.govde).aci);
        if (v == null) { toast("Açı sayı olmalı."); return; }
        MB.kaplamaKapat();
        if (aksKatOzellik("Açı " + fmtK(v) + "° atandı", { aci: v })) return;
        secimli("Açı " + fmtK(v) + "° atandı", function (m, a) { const r = MOp.ozellikAta(m, a.cubuklar, { aci: v }); r.degisen = { cubuklar: a.cubuklar }; return r; }, { bagla: false, genel: GENEL_ISLEM_ADLARI.aci });
      });
    }
    function duzlemleBolPenceresi() {
      if (!secimCubukSayisi()) { toast("Düzlemle bölmek için çubuk seçin."); return; }
      // yalnız seçimi iç noktasından kesen aks düzlemleri (aks–kat seçimi genelleştirilmiş kopyada ölçülür; model çevrilmez)
      let mk = B(), ay = secimAyir(MB.secim()), kesen;
      try {
        if (ay.aksKat.length) { mk = genellestirHazirla(mk).model; ay = secimAyir(genelSecim(mk, MB.secim())); }
        kesen = kesenDuzlemler(mk, ay.cubuklar);
      } catch (e) { hata(e); return; }
      if (!kesen.length) { toast("Seçili çubukları kesen aks düzlemi yok (aks düzlemleri çubukları uçlarından geçiyor); bölünecek yer yok. Belirli bir noktada bölmek için Böl'ü kullanın."); return; }
      const l = kesen.map(function (a) { return [a.yon + "|" + a.ad, a.yon.toUpperCase() + " aksı " + a.ad + " (" + fmtK(a.konum) + " m; " + a.sayi + " çubuğu keser)"]; });
      const k = MB.kaplamaAc("duzlemle-bol", "Düzlemle böl", { kucuk: true });
      k.govde.innerHTML = alan("Aks düzlemi", sec("d", l, l[0] && l[0][0])) + '<div class="dugmeler"><button type="button" class="dugme ana" data-tamam>Böl</button></div>';
      k.govde.querySelector("[data-tamam]").addEventListener("click", function () {
        const p = oku(k.govde).d.split("|"), a = aksListesi(B(), p[0]).filter(function (x) { return x.ad === p[1]; })[0];
        if (!a) return;
        const d = {}; d[p[0].toUpperCase()] = a.konum;
        MB.kaplamaKapat();
        secimli(p[0].toUpperCase() + " aksı " + a.ad + " düzleminde bölündü", function (m, ay) { return MOp.duzlemleBol(m, ay.cubuklar, d); }, { genel: GENEL_ISLEM_ADLARI["duzlemle-bol"] });
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
        uygula(function (m) { const r = MOp.dugumleriBirlestir(m, t); if (!(r.birlesen || []).length) { r.uyarilar = ["Birleştirilecek çakışık düğüm yok."]; r.reddedildi = true; } return r; }, "Düğümler birleştirildi", { islem: GENEL_ISLEM_ADLARI["dugum-birlestir"] });
      });
    }
    function yukPenceresi(h) {
      const b = B(), aksKat = !genelMi(b);
      const ad = { cubuk: "Çubuk " + h.no, panel: "Panel " + h.no, kiris: "Kiriş " + h.no, doseme: "Döşeme " + h.no }[h.tur] || "Düğüm " + (h.etiket || "");
      const k = MB.kaplamaAc("yuk", "Yük: " + ad, { kucuk: true });
      const adres = h.tur === "dugum" ? aksKatAdresi(b, h.ref) : null;
      let anahtar = null;
      if (h.tur === "dugum") { try { anahtar = MAk.refAnahtar(b, h.ref); } catch (e) { anahtar = null; } }
      const mevcut = liste(b, "ek_yukler").map(function (y, i) { return [y, i]; }).filter(function (x) {
        const y = x[0];
        if (!y) return false;
        if (h.tur === "cubuk") return y.tur === "cubuk" && +y.cubuk === +h.no;
        if (h.tur === "panel") return y.tur === "panel" && +y.panel === +h.no;
        if (h.tur === "kiris") return y.tur === "kiris" && +y.kiris === +h.no;
        if (h.tur === "doseme") return y.tur === "doseme" && +y.doseme === +h.no;
        if (y.tur !== "dugum") return false;
        if (y.dugum != null) { try { return anahtar != null && MAk.refAnahtar(b, y.dugum) === anahtar; } catch (e) { return false; } }
        return !!adres && Array.isArray(y.aks) && String(y.aks) === String(adres.aks) && +(y.kat == null ? 1 : y.kat) === adres.kat;
      });
      const durumSec = alan("Yük durumu", sec("durum", [["G", "G — sabit"], ["Q", "Q — hareketli"], ["S", "S — kar"]], S.yuk));
      let f = "";
      if (h.tur === "cubuk") {
        f = durumSec + alan("Biçim", sec("bicim", [["yayili", "Yayılı (kN/m)"], ["tekil", "Tekil (kN)"]], "yayili")) +
          '<div class="bn-iki">' + alan("Yön", sec("yon", [["Z", "Z (global, yukarı +)"], ["X", "X"], ["Y", "Y"], ["z′", "z′ (yerel)"], ["y′", "y′ (yerel)"], ["x′", "x′ (eksenel)"]], "Z")) + alan("q₁ ya da P (aşağı yük −)", girdi("q1", "-2", ' inputmode="decimal"')) + "</div>" +
          '<div class="bn-iki">' + alan("q₂ (boş = q₁)", girdi("q2", "", ' inputmode="decimal"')) + alan("Tekil yükün yeri x (m)", girdi("x", "", ' inputmode="decimal"')) + "</div>" + onay("izdusum", "Yatay izdüşüm başına (kar, hareketli)", false);
      } else if (h.tur === "kiris") {
        f = durumSec + alan("Düzgün yayılı düşey yük q (kN/m; aşağı +)", girdi("q", "2", ' inputmode="decimal"')) +
          '<p class="not">Aks–kat kirişine yalnız kiriş boyunca düzgün yayılı düşey yük verilir. Tekil yükü kirişin ucundaki düğüme verin; eğik ya da yerel yönlü yük için modeli genel modele çevirin.</p>';
      } else if (h.tur === "doseme") {
        f = '<div class="bn-iki">' + alan("Ek sabit g (kN/m²)", girdi("g", "0.5", ' inputmode="decimal"')) + alan("Ek hareketli q (kN/m²)", girdi("q", "", ' inputmode="decimal"')) + "</div>" +
          '<p class="not">g sabit (G), q hareketli (Q) yüke eklenir; kar yükü (S) yük durumlarından kendiliğinden hesaplanır.</p>';
      } else if (h.tur === "panel") {
        f = durumSec + alan("Düşey yayılı yük p (kN/m²; aşağı +)", girdi("p", "0.5", ' inputmode="decimal"')) +
          '<p class="not">p seçilen yük durumuna (G, Q ya da S) eklenir ve panelin dağıtım kuralıyla kenar çubuklarına aktarılır.</p>';
      } else {
        f = durumSec + '<div class="bn-iki">' + alan("FX (kN)", girdi("FX", "", ' inputmode="decimal"')) + alan("FY (kN)", girdi("FY", "", ' inputmode="decimal"')) + "</div>" +
          '<div class="bn-iki">' + alan("FZ (kN; aşağı −)", girdi("FZ", "-10", ' inputmode="decimal"')) + alan("MZ (kN·m)", girdi("MZ", "", ' inputmode="decimal"')) + "</div>" +
          (aksKat && adres ? '<p class="not">Aks–kat düğüm yükü: ' + kacis(adres.aks.join("") + ", kat " + adres.kat) + " (global eksenler).</p>" : "");
      }
      const yukMetni = function (y) {
        if (y.tur === "cubuk") return y.P != null ? "P = " + fmtK(+y.P) + " kN (x = " + fmtK(+y.x) + ")" : "q = " + fmtK(+(y.q1 != null ? y.q1 : y.q)) + (y.q2 != null && +y.q2 !== +y.q1 ? "…" + fmtK(+y.q2) : "") + " kN/m, " + (y.yon || "Z");
        if (y.tur === "kiris") return "q = " + fmtK(+y.q) + " kN/m (aşağı)";
        if (y.tur === "panel" && y.p != null) return "p = " + fmtK(+y.p) + " kN/m²";
        if (y.tur === "panel" || y.tur === "doseme") return ((+y.g ? "g = " + fmtK(+y.g) + " " : "") + (+y.q ? "q = " + fmtK(+y.q) : "")).trim() + " kN/m²";
        return ["FX", "FY", "FZ", "MX", "MY", "MZ"].filter(function (a) { return y[a]; }).map(function (a) { return a + " = " + fmtK(+y[a]); }).join(", ");
      };
      k.govde.innerHTML = (mevcut.length ? "<h3>Mevcut yükler</h3><ul class=\"bc-yukler\">" + mevcut.map(function (x) {
        const y = x[0];
        return "<li>" + kacis((y.tur === "doseme" ? "" : (y.durum || "G") + ": ") + yukMetni(y)) +
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
        else if (h.tur === "kiris") yuk = { durum: o.durum, q: o.q };
        else if (h.tur === "doseme") yuk = { g: o.g, q: o.q };
        else if (h.tur === "panel") yuk = { durum: o.durum, p: o.p };
        else yuk = { durum: o.durum, FX: o.FX, FY: o.FY, FZ: o.FZ, MZ: o.MZ };
        if (o.durum) S.yuk = o.durum;
        let r;
        try { r = yukEkle(B(), h, yuk); } catch (x) { hata(x); return; }
        MB.kaplamaKapat();
        MB.binaAyarla(r.model, { etiket: ad + ": " + (h.tur === "doseme" ? "ek" : o.durum) + " yükü eklendi." });
      });
    }
    // kesit önerisi (köprüde bina_kesit_oner; genel model motoru — sözleşme C4, C19). hedef: {tur: "cubuk"|"kolon"|"kiris", no} | null (bütün çubuklar)
    let s3Destek = null;
    function kesitOner(hedef) {
      MB.motorS3().then(function (var_) {
        s3Destek = var_;
        if (!var_) { toast("Kesit önerisi bu kurulumdaki motorda yok (genel model motoru gerekir); uygulamayı güncelleyin."); return; }
        const A = window.MatrisApp;
        const hepsi = !hedef;
        const k = MB.kaplamaAc("kesit-oner", hepsi ? "Kesit önerileri (bütün çubuklar)" : "Kesit önerisi", hepsi ? { genis: true } : { kucuk: true });
        k.govde.innerHTML = '<p class="not bn-bekle" role="status"><span class="bn-donen" aria-hidden="true"></span> Çözüm ve öneri hesaplanıyor…</p>';
        const tur = hepsi ? null : (hedef.tur === "kolon" || hedef.tur === "kiris" || hedef.tur === "cubuk" ? hedef.tur : "cubuk");
        const istek = function (ek) {
          const g = MB.cozumKimligi() ? { cozum_kimligi: MB.cozumKimligi(), bina: B() } : { bina: B() };
          g.hedef = hepsi ? "hepsi" : [{ tur: tur, no: hedef.no }];
          return Promise.resolve(A.motorIstegi({ islem: "bina_kesit_oner", girdi: Object.assign(g, ek || {}) }));
        };
        // tıklanan elemanın kesit grubu (K-32): aynı (kesit, tür) ya da aynı grup adındaki çubuklar ve aks–kat kolon/kirişleri
        const uyeler = hepsi ? [] : grupUyeleri(B(), { tur: tur, no: hedef.no });
        const satir = function (o, i, l) {
          const r = oneriSatiri(o, false), j = l.indexOf(o);
          return '<div class="bc-oneri"><p><b>' + kacis(oneriEtiketi(o)) + "</b>" +
            (r.parca ? ' <button type="button" class="dugme kucuk bc-oneri-parca" data-oneri-goster="' + j + '" title="Parçaları sahnede seç">' + kacis(r.parca) + "</button>" : "") +
            ": " + kacis(o.kesit || "?") + " → <b>" + kacis(r.ad) + "</b>" + (r.oneri ? " (" + kacis(r.oneri) + ")" : "") +
            (o.degisim ? ' <span class="not">' + kacis(o.degisim) + "</span>" : "") +
            " · D/C " + kacis(r.dc) + ' <span class="not">' + kacis(r.dcEtiket) + "</span></p>" +
            "<ul>" + (o.gerekce || []).map(function (g) { return "<li>" + kacis(g) + "</li>"; }).join("") + "</ul>" +
            (oneriUygulanir(o) ? '<button type="button" class="dugme kucuk ana" data-oneri="' + j + '">Uygula</button>' : "") + "</div>";
        };
        const notlar = function (y) {
          return (y.aciklama ? '<p class="not bc-oneri-aciklama">' + kacis(y.aciklama) + "</p>" : "") +
            ((y.uyarilar || []).length ? '<ul class="bc-oneri-uyari">' + y.uyarilar.map(function (u) { return '<li class="not">' + kacis(u) + "</li>"; }).join("") + "</ul>" : "");
        };
        const sureNotu = function (metin) {
          let n = k.govde.querySelector(".bc-oneri-sure");
          if (!n) { n = document.createElement("p"); n.className = "not bn-bekle bc-oneri-sure"; n.setAttribute("role", "status"); k.govde.insertBefore(n, k.govde.firstChild); }
          n.innerHTML = '<span class="bn-donen" aria-hidden="true"></span> ' + kacis(metin);
        };
        const ekMetin = function (y2) { return [otelemeSatiri(y2 && y2.oteleme), sureMetni(y2 && y2.sure_ms)].filter(Boolean).join(" · "); };
        // Hepsini uygula sonrası: binaAyarla + yeniden çöz (görünen sonuç taze olsun); D/C > 1 kaldıysa ⚠ ve aşan çubuklar; motorun
        // yinele turlarında eklediği uyarılar (göreli kat ötelemesi sınırı, hiç tur uygulanamadı…) da söylenir (hepsiEkUyarilari);
        // göreli kat ötelemesi önce / sonra (K-27) ve motor süresi (K-31) sonuç iletisinin sonundadır
        const hepsiUygula = function (y2, y) {
          const oz = hepsiOzeti(y2), ek = hepsiEkUyarilari(y2, y), son = ekMetin(y2);
          const deg = (y2.turlar || []).reduce(function (t, x) { return t + ((x.degisen || []).length); }, 0);
          const asanMetin = oz.asan.slice(0, 6).map(function (a) { return a.etiket + " (" + dcFmt(a.dc) + ")"; }).join(", ") + (oz.asan.length > 6 ? " … (+" + (oz.asan.length - 6) + ")" : "");
          const etiket = "Kesit önerileri uygulandı" + (deg ? " (" + deg + " kesit grubu değişti" + (oz.dc != null ? "; D/C maks " + dcFmt(oz.dc) : "") + ")" : "") +
            (oz.asiyor ? " — ⚠ D/C maks " + dcFmt(oz.dc) + " > 1, öneriler yetmedi" + (asanMetin ? ": " + asanMetin : "") + "." : ".");
          MB.kaplamaKapat();
          if (MB.binaAyarla(y2.bina, { etiket: etiket }) === false) {
            // neden (ör. öteleme koruması küçültmeyi engelledi) motorun yinele açıklamasındadır: ilk yanıtta olmayan kısmı söylenir
            const neden = hepsiAciklamaEki(y2, y, !!otelemeSatiri(y2 && y2.oteleme));
            S.sonUyari = "Kesit önerileri modeli değiştirmedi." + (neden ? " " + neden : "") + (ek.tum.length ? " ⚠ " + ek.tum.join(" ") : "") + (son ? " " + son + "." : "");
            toast(S.sonUyari); MB.ipucuYenile(); return;
          }
          S.sonUyari = oz.asiyor ? etiket : "";
          Promise.resolve(MB.coz()).then(function (ok) {
            if (!ok) return;
            const v = MB.veri(), dcM = v && v.tasarim ? v.tasarim.en_buyuk_dc : null;
            const ekM = (ek.diger.length ? " ⚠ " + ek.diger.join(" ") : "") + (son ? " " + son + "." : "");
            if (dcM != null && +dcM > 1 + 1e-9) {
              const asan = ((v.tasarim.elemanlar) || []).filter(function (e) { return e && +e.dc > 1 + 1e-9; }).sort(function (a, b) { return b.dc - a.dc; });
              S.sonUyari = "⚠ Yeniden çözüm: D/C maks " + dcFmt(+dcM) + " > 1 — " + asan.length + " eleman aşıyor (" +
                asan.slice(0, 6).map(function (e) { return tasarimEtiketi(e) + " " + dcFmt(+e.dc); }).join(", ") + (asan.length > 6 ? " …" : "") +
                "). Bu elemanların kesitini elle büyütün ya da Kesit öner'i yeniden çalıştırın." + ekM;
            } else if (dcM != null) S.sonUyari = ek.diger.length ? "Kesit önerileri uygulandı ve model yeniden çözüldü: D/C maks " + dcFmt(+dcM) + "." + ekM : "";
            else return;
            toast(S.sonUyari || "Kesit önerileri uygulandı ve model yeniden çözüldü: D/C maks " + dcFmt(+dcM) + "." + ekM); MB.ipucuYenile();
          }, hata);
        };
        // Kesit grubuna uygula (K-32): grup isteği (C19 grup: true, hedef = üyeler, yinele 1) → zarf kartı bütün üyelere tek geri al
        // adımında; model yeniden çözülür ve grubun gerçek D/C maksimumu söylenir. Grup kaydı gelmezse (eski motor) yinele yanıtının
        // uygulanmış modeli (bina) kullanılır.
        const grupAkisi = function (d, y) {
          d.disabled = true; d.textContent = "Grup hesaplanıyor ve yeniden çözülüyor…";
          sureNotu(sureTahmini(MB.veri(), 1, y && y.sure_ms));
          Promise.resolve(A.motorIstegi({ islem: "bina_kesit_oner", girdi: Object.assign(MB.cozumKimligi() ? { cozum_kimligi: MB.cozumKimligi(), bina: B() } : { bina: B() },
            { hedef: uyeler.map(function (u) { return { tur: u.tur, no: u.no }; }), grup: true, yinele: 1 }) })).then(function (y3) {
            MB.kaplamaKapat();
            if (!y3 || y3.hata) { toast((y3 && y3.hata) || "Boş yanıt."); return; }
            const o3 = (y3.oneriler || [])[0] || null, gk = !!(o3 && o3.grup && typeof o3.grup === "object");
            let model = null, ad = null, n = uyeler.length;
            if (gk) {
              if (!oneriUygulanir(o3)) { toast(grupUygulanmazMetni(o3, n) + (sureMetni(y3.sure_ms) ? " " + sureMetni(y3.sure_ms) + "." : "")); return; }
              let r;
              try { r = grupUygula(B(), o3, uyeler); } catch (x) { hata(x); return; }
              model = r.model; ad = r.ad; n = r.hedefler.length;
            } else if (y3.bina) model = y3.bina;
            else { toast("Bu kurulumdaki motor kesit grubu önerisini vermedi; önerileri tek tek uygulayın."); return; }
            const dcT = gk && o3.dc_oneri != null ? "; D/C maks " + dcFmt(+o3.dc_oneri) + " tahmini" : "";
            const sonuc = uygula(function () { return { model: model, eklenen: {}, silinen: {}, degisen: { cubuklar: uyeler.filter(function (u) { return u.tur === "cubuk"; }).map(function (u) { return u.no; }) }, uyarilar: [] }; },
              "Kesit grubuna uygulandı" + (ad ? ": " + ad : "") + " (" + n + " çubuk" + dcT + ")", { bagla: false, secim: function () { return uyeler.map(function (u) { return { tur: u.tur, no: u.no }; }); } });
            if (!sonuc) return;
            Promise.resolve(MB.coz()).then(function (ok) {
              if (!ok) return;
              let dc = grupDcMaks(MB.veri(), uyeler);
              if (dc == null && o3 && o3.dc_sonra != null) dc = +o3.dc_sonra;
              if (dc == null) return;
              const sm = sureMetni(y3.sure_ms);
              const asar = dc > 1 + 1e-9;
              S.sonUyari = asar ? "⚠ Grubun gerçek D/C maks: " + dcFmt(dc) + " > 1 — kesit değişince iç kuvvetler yeniden dağıldı; bir üst kesit deneyin ya da Kesit öner'i yeniden çalıştırın." + (sm ? " " + sm + "." : "") : "";
              toast(S.sonUyari || "Grubun gerçek D/C maks: " + dcFmt(dc) + (sm ? " · " + sm : "") + "."); MB.ipucuYenile();
            }, hata);
          }, function (x) { MB.kaplamaKapat(); hata(x); });
        };
        istek().then(function (y) {
          if (!k.govde.isConnected) return;
          if (!y || y.hata) { k.govde.innerHTML = '<p class="bc-hata">' + kacis((y && y.hata) || "Boş yanıt.") + "</p>"; return; }
          const l = y.oneriler || [];
          const uygulanir = l.filter(oneriUygulanir);
          // aşan ama uygulanabilir önerisi olmayan çubuklar (ör. ailede yeterli profil yok) da listelenir: "yeterli" denmez
          const asanUygulanmaz = l.filter(function (o) { return !oneriUygulanir(o) && o.dc_once != null && +o.dc_once > 1 + 1e-9; });
          const gorunen = hepsi ? uygulanir.concat(asanUygulanmaz) : l;
          let h = "";
          if (!l.length) h = '<p class="not">Öneri yok: kesit yeterli ya da hesaplanamadı.</p>';
          else if (hepsi && !uygulanir.length && asanUygulanmaz.length) h = '<p class="bc-hata">Uygulanabilir kesit önerisi yok, ama ' + asanUygulanmaz.length + " çubukta D/C > 1 (aşağıda; gerekçeye bakın — kesiti elle değiştirin).</p>";
          else if (!gorunen.length) h = '<p class="not">Değiştirilecek kesit yok: ' + l.length + " çubuğun kesiti yeterli ve ekonomik (öneri mevcut kesitle aynı).</p>";
          if (hepsi && uygulanir.length) {
            h += '<p class="not">' + uygulanir.length + " çubuk için kesit değişikliği önerildi" + (l.length > uygulanir.length ? " (" + (l.length - uygulanir.length) + " çubukta değişiklik yok" + (asanUygulanmaz.length ? ", " + asanUygulanmaz.length + "'i D/C > 1 ama önerisi uygulanamıyor" : "") + ")" : "") +
              '. “Hepsini uygula” önerileri uygular, model yeniden çözülerek en çok 3 tur düzeltilir (aynı kesit ve türdeki çubuklara grubun en ağır önerisi verilir) ve sonuç gösterilir.</p>' +
              '<div class="dugmeler"><button type="button" class="dugme ana" data-oneri-hepsi>Hepsini uygula</button></div>';
          }
          h += gorunen.map(function (o, i) { return satir(o, i, l); }).join("");
          const gm = grupDugmeMetni(uyeler);
          if (gm) h += '<div class="dugmeler"><button type="button" class="dugme" data-oneri-grup>' + kacis(gm) + "</button></div>" +
            '<p class="not">Kesit grubu: aynı kesit ve türdeki çubuklar ve aks–kat elemanları (eleman bir grup adı taşıyorsa aynı gruptakiler); grubun zarf kesiti hepsine uygulanır ve model yeniden çözülür.</p>';
          h += notlar(y);
          k.govde.innerHTML = h;
          // tek öneri parçalı aks–kat elemanınınsa (K-13) bütün parçaları sahnede seçilir
          if (!hepsi && l.length === 1 && oneriSatiri(l[0], false).parca) { const v = oneriVurgusu(B(), l[0]); if (v.length) MB.seciliAyarla(v); }
          k.govde.addEventListener("click", function (e) {
            const gs = e.target.closest("[data-oneri-goster]");
            if (gs) { const v = oneriVurgusu(B(), l[+gs.getAttribute("data-oneri-goster")]); if (v.length) MB.seciliAyarla(v); return; }
            const gd = e.target.closest("[data-oneri-grup]");
            if (gd) { grupAkisi(gd, y); return; }
            if (e.target.closest("[data-oneri-hepsi]")) {
              const d = e.target.closest("[data-oneri-hepsi]");
              d.disabled = true; d.textContent = "Uygulanıyor ve yeniden çözülüyor…";
              sureNotu(sureTahmini(MB.veri(), 3, y.sure_ms));
              istek({ yinele: 3 }).then(function (y2) {
                if (!y2 || y2.hata || !y2.bina) {
                  // yanıt bina taşımıyorsa öneriler tek tek uygulanır (yeniden çözülmeden)
                  let m = B(), n = 0;
                  const hatalar = [];
                  uygulanir.forEach(function (o) { try { m = oneriUygula(m, o, null).model; n++; } catch (x) { hatalar.push(oneriEtiketi(o) + ": " + x.message); } });
                  MB.kaplamaKapat();
                  if (!n) { toast((y2 && y2.hata) || hatalar.join(" ") || "Öneriler uygulanamadı."); return; }
                  MB.binaAyarla(m, { etiket: "Kesit önerileri uygulandı (" + n + " çubuk; D/C mevcut iç kuvvetlerle tahmin — yeniden çözün)." + (hatalar.length ? " ⚠ " + hatalar.join(" ") : "") });
                  return;
                }
                hepsiUygula(y2, y);
              }, function (x) { MB.kaplamaKapat(); hata(x); });
              return;
            }
            const t = e.target.closest("[data-oneri]");
            if (!t) return;
            const o = l[+t.getAttribute("data-oneri")];
            let r;
            try { r = oneriUygula(B(), o, hedef); } catch (x) { hata(x); return; }
            MB.kaplamaKapat();
            const parca = oneriSatiri(o, false).parca;
            const sonuc = uygula(function () { return { model: r.model, eklenen: {}, silinen: {}, degisen: { cubuklar: r.hedefler.filter(function (x) { return x.tur === "cubuk"; }).map(function (x) { return x.no; }) }, uyarilar: [] }; },
              "Kesit " + r.ad + " uygulandı (" + oneriEtiketi(o) + (parca ? ", " + parca : "") + "; D/C " + fmt(o.dc_oneri) + " tahmini, mevcut iç kuvvetlerle)",
              { bagla: false, secim: parca ? function (rr, mm) { const v = oneriVurgusu(mm, o); return v.length ? v : undefined; } : undefined });
            if (!sonuc) return;
            // tahmin mevcut iç kuvvetlerle: rijitlik değişince kuvvetler yeniden dağılır — yeniden çözüp gerçek D/C söylenir
            Promise.resolve(MB.coz()).then(function (ok) {
              if (!ok) return;
              const dcY = grupDcMaks(MB.veri(), r.hedefler);
              if (dcY == null) return;
              if (dcY > 1 + 1e-9) {
                S.sonUyari = "⚠ Yeniden çözümde " + oneriEtiketi(o) + " D/C = " + dcFmt(dcY) + " > 1 (tahmin " + dcFmt(o.dc_oneri) + "): kesit değişince iç kuvvetler yeniden dağıldı; bir üst kesit deneyin ya da Kesit öner'i yeniden çalıştırın.";
                toast(S.sonUyari); MB.ipucuYenile();
              } else toast("Kesit " + r.ad + " uygulandı; yeniden çözümde " + oneriEtiketi(o) + " D/C = " + dcFmt(dcY) + " (tahmin " + dcFmt(o.dc_oneri) + ").");
            }, hata);
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
    const secimNedeni = function () { return cubukSecimiVar() ? null : SECIM_NEDENI; };
    /** Yalnız çekme yalnız çapraz / bağ türü çubuklara: seçimin her öğesi çubuk ve türü kolon / kiriş değil. */
    function ycUygun() {
      const s = MB.secim(), b = B();
      return s.length > 0 && s.every(function (x) {
        if (x.tur !== "cubuk") return false;
        const c = liste(b, "cubuklar").filter(function (y) { return +y.no === +x.no; })[0];
        return !!c && c.tur !== "kolon" && c.tur !== "kiris";
      });
    }
    function ycNedeni() {
      if (ycUygun()) return null;
      return MB.secim().some(function (x) { return x.tur === "cubuk" || x.tur === "kolon" || x.tur === "kiris"; }) ? "Yalnız çapraz/bağ çubuklarında kullanılır" : "Önce bir çapraz ya da bağ çubuğu seçin.";
    }
    function ycDurum() {
      if (!ycUygun()) return false;
      const a = secimAyir(MB.secim()), b = B();
      return a.cubuklar.every(function (no) { const c = liste(b, "cubuklar").filter(function (x) { return +x.no === no; })[0]; return c && c.yalniz_cekme; });
    }
    const PANEL_SEC = Object.keys(PANEL_ON_AYAR).map(function (id) { return { id: id, ad: PANEL_ON_AYAR[id].ad, ikon: "hizli-panel" }; });
    const MESNET_SEC = Object.keys(MESNET_ON_AYAR).map(function (id) { return { id: id, ad: MESNET_ON_AYAR[id].ad, ikon: "mesnet" }; });
    const YUK_SEC = [{ id: "G", ad: "G — sabit yük", ikon: "yuk-ata" }, { id: "Q", ad: "Q — hareketli yük", ikon: "yuk-ata" }, { id: "S", ad: "S — kar yükü", ikon: "yuk-ata" }];
    const AKS_SEC = [{ id: "x", ad: "X aksı (harfli)", ikon: "aks-ekle" }, { id: "y", ad: "Y aksı (sayılı)", ikon: "aks-ekle" }, { id: "z", ad: "Z aksı (kot; cephede)", ikon: "aks-ekle" }];
    const secenekli = function (id, kipId, liste_, al, ver) {
      return kipK(kipId, { secenekler: liste_, secenek: al, secenekSec: function (v) { ver(v); if (MB.kip() !== kipId) MB.kipAyarla(kipId); MB.ipucuYenile(); } });
    };
    const oneriHedefi = function () { return MB.secim().filter(function (x) { return x.tur === "cubuk" || x.tur === "kolon" || x.tur === "kiris"; })[0] || null; };
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
      makas: function () { makasPenceresi(); },
      "besik-cerceve": function () { besikPenceresi(); },
      asik: { calistir: function () { asikPenceresi(); }, etkin: function () { const a = secimAyir(MB.secim()); return a.cubuklar.length >= 2 || a.paneller.length > 0; },
        neden: function () { const a = secimAyir(MB.secim()); return a.cubuklar.length >= 2 || a.paneller.length > 0 ? null : "Önce en az iki mertek çubuğu ya da bir çatı paneli seçin."; } },
      "kren-yolu": function () { krenPenceresi(); },
      "uretec-duzenle": { ad: "Üreteci düzenle", ikon: "makas", grup_varsayilan: "cizim", tur: "eylem",
        etkin: function () { return !!seciliUretec(); },
        neden: function () { return seciliUretec() ? null : "Önce üreteçle oluşturulmuş bir çubuk ya da panel seçin (makas, beşik çerçeve, aşık, kren yolu, çapraz)."; },
        calistir: function () { uretecDuzenle(seciliUretec()); },
        ipucu: "Seçili elemanı üreten üretecin (makas, beşik çerçeve, aşık, kren yolu, çapraz) parametrelerini düzenler; üretilen elemanlar yeniden üretilir." },
      mesnet: secenekli("mesnet", "mesnet", MESNET_SEC, function () { return S.mesnet; }, function (v) { S.mesnet = v; }),
      "yuk-ata": secenekli("yuk-ata", "yuk-ata", YUK_SEC, function () { return S.yuk; }, function (v) { S.yuk = v; }),
      // Düzenleme
      tasi: kipK("tasi"), dondur: kipK("dondur"), ayna: kipK("ayna"), "dogrusal-dizi": kipK("dogrusal-dizi"),
      "ozellik-ata": { tur: "eylem", calistir: function () { if (!ozellikPenceresi()) MB.firca(); }, ipucu: "Seçili çubuklara kesit / tür / açı / grup / Lb / K / duvar / yalnız çekme atar; seçim yoksa kesit fırçası (aks–kat)." },
      mafsal: { calistir: function () { mafsalPenceresi(); }, etkin: secimGerekli, neden: secimNedeni },
      "yalniz-cekme": { tur: "anahtar", etkin: ycUygun, secili: ycDurum, neden: ycNedeni, calistir: function () {
        if (!ycUygun()) { toast(ycNedeni()); return; }
        const ac = !ycDurum();
        secimli(ac ? "Yalnız çekme açıldı" : "Yalnız çekme kapatıldı", function (m, a) { const r = MOp.ozellikAta(m, a.cubuklar, { yalniz_cekme: ac ? true : null }); r.degisen = { cubuklar: a.cubuklar }; return r; }, { bagla: false, genel: GENEL_ISLEM_ADLARI["yalniz-cekme"] });
      }, ipucu: "Seçili çapraz / bağ çubuklarını yalnız çekme çubuğu yapar (basınçta devre dışı; kolon ve kirişte kullanılmaz)." },
      // Değiştirme
      bol: { calistir: bolPenceresi, etkin: secimGerekli, neden: secimNedeni },
      "kesisimde-bol": { etkin: secimGerekli, neden: secimNedeni, calistir: function () {
        secimli("Kesişimlerde bölündü", function (m, a) { const r = MOp.kesisimlerdeBol(m, a.cubuklar); if (!r.kesisim_sayisi) { r.uyarilar = (r.uyarilar || []).concat(["Seçili çubuklar birbirini kesmiyor (en az iki kesişen çubuk seçin)."]); r.reddedildi = true; } return r; }, { genel: GENEL_ISLEM_ADLARI["kesisimde-bol"] });
      } },
      "duzlemle-bol": { calistir: duzlemleBolPenceresi, etkin: secimGerekli, neden: secimNedeni },
      birlestir: { calistir: function () { birlestirIslem(); }, etkin: secimGerekli, neden: secimNedeni },
      "dugum-birlestir": dugumBirlestirPenceresi,
      "kesit-degistir": { calistir: kesitPenceresi, etkin: secimGerekli, neden: secimNedeni },
      aci: { calistir: aciPenceresi, etkin: secimGerekli, neden: secimNedeni },
      // Tasarım: seçili çubuk / kolon / kiriş için (seçim yoksa bütün çubuklar) kesit önerisi (masaüstü menüsü Tasarım › Kesit öner ve uygula)
      "kesit-oner": { ad: "Kesit öner ve uygula", ikon: "kesit-degistir", grup_varsayilan: "degistirme", tur: "eylem",
        etkin: function () { return s3Destek !== false; },
        neden: function () { return s3Destek === false ? "Bu kurulumdaki hesap motoru kesit önerisini desteklemiyor; uygulamayı güncelleyin." : null; },
        calistir: function () { kesitOner(oneriHedefi()); },
        ipucu: "Seçili çubuk / kolon / kiriş için kesit önerisi (seçim yoksa bütün çubuklar; “Hepsini uygula” yeniden çözer)." },
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

    // ---------------------------------------------------------------- sağ tık komutları: böl, birleştir, mafsal, kesit öner, üreteci düzenle
    MB.baglamKancasi(function (h, k) {
      if (["cubuk", "kolon", "kiris", "panel"].indexOf(h.tur) < 0) return k;
      const uk = uretecKaydi(B(), h);
      if (uk) k["uretec-duzenle"] = { ad: "Üreteci düzenle…", calistir: function () { uretecDuzenle(uk); } };
      if (h.tur === "panel") return k;
      if (s3Destek == null) MB.motorS3().then(function (v) { s3Destek = v; });
      k.bol = function () { MB.seciliAyarla([{ tur: h.tur, no: h.no }]); bolPenceresi(); };
      // aks–kat kolon/kirişi tek parçadır: birleştirilecek komşusu yok (genel modelde çubuk zinciri birleştirilir)
      k.birlestir = h.tur === "cubuk" ? { calistir: function () { birlestirIslem(esDogrusalZincir(h.no)); } }
        : { calistir: function () { toast("Aks–kat elemanı tek parçadır; birleştirilecek komşu çubuk yok."); }, etkin: false, neden: "Aks–kat elemanı tek parçadır" };
      k.mafsal = function () { mafsalPenceresi({ tur: h.tur, no: h.no }); };
      k["kesit-oner"] = { calistir: function () { kesitOner({ tur: h.tur, no: h.no }); }, etkin: s3Destek !== false };
      return k;
    });
    // model değişince bekleyen iki noktalı işlem / zincir geçersiz olabilir (geri al)
    MB.dinle("model", function (o) { if (o && (o.etiket === "geri-al" || o.etiket === "yinele")) temizle(); });
    MB.dinle("gorunum", function () { S.parca = null; S.goz = null; tazele(); });
    MB.aracYenile();
  }

  return Object.freeze(Object.assign({}, SAF, { otomatikKur: otomatikKur, kur: function (MB) { if (!kuruldu) { kuruldu = true; kur(MB); } } }));
});
