/* Matris Öğren — eleman bilgisi: sağ tık bağlam menüsü ve iğnelenebilir bilgi denetçisi (window.MatrisBilgi; node'da module.exports).
   Tasarım belgesi §17.2 (§19 aks adresleri).

   Saf çekirdek (DOM yok, node testli): bilgi(hedef, bina, veri?, sec?) → sekmeli model
     { tur, no, turAdi, baslik, adres, alt, ozet, sekmeler: [{id, ad, bolumler}], durumlar, durum, cozumVar, ham }
     bölüm: { baslik?, satirlar?: [[ad, değer, birim?]], tablo?: {basliklar, satirlar}, svg?, not?, uyari? }
   Sekmeler: Geometri, Kesit ve malzeme, Bağlantı, Yükler, İç kuvvetler (durum / kombinasyon / zarf; N, V, M küçük diyagramları),
   Yer değiştirme, Tasarım, Metraj, Yük yolu — düğüm, mesnet, döşeme/panel ve temel için uygun alt küme.
   Veri: bina JSON + çözüm `veri` (yapi.bina_coz şeması §4) istemcide türetilir; isteğe bağlı köprü `paket`
   ({sekmeler: {sekmeId: [bölüm]}, uyarilar}) "Motor ayrıntısı" olarak eklenir. Çözüm yoksa analiz sekmeleri "Önce çözün" der.

   DOM (tarayıcı):
     menuAc(olay, {tur, no, bina, veri?, komutlar?, denetci?, kapsayici?}) — sağ tık / uzun basma / Shift+F10 menüsü.
       komutlar: {ozellikler, bol, birlestir, mafsal, "kesit-oner", "isi-haritasi", "yuk-akisi", tasarim, gizle, yalit, sil, bilgi?}
       her biri fn(hedef) ya da {calistir(hedef), etkin?: bool | fn}; verilmeyen uygun öğe soluk görünür. "Bilgi" denetçiyi açar.
     denetci(kapsayici, {tur, no, bina, veri?, paket?, paketIste?(hedef) → Promise<paket>, sekme?, durum?, konum?, raporaEkle?(kayit), eski?})
       — sürüklenebilir, iğnelenebilir, çok sekmeli pencere; iğnelenmemiş pencere bir sonraki denetçi çağrısında yeniden kullanılır,
       iğnelenenler kalır (karşılaştırma). "Kopyala" (TSV) ve "Rapora ekle" (geri çağrı) düğmeleri.
     bagla(oge, {bul(olay) → {tur, no} | null, bina(), veri(), komutlar?(hedef), secili?() → hedef, konum?(hedef) → {x, y}, uzunBasma?})
       — sahneye sağ tık, dokunmatikte ~500 ms uzun basma ve klavyeyle (ContextMenu / Shift+F10) menü bağlar. */
(function (kok, fabrika) {
  "use strict";
  let olcumNode = null;
  if (typeof module === "object" && module && module.exports && typeof require === "function") {
    try { olcumNode = require("./olcum.js"); } catch (e) { olcumNode = null; }
  }
  const api = fabrika(function () { return (kok && kok.MatrisOlcum) || olcumNode; });
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.MatrisBilgi = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function (olcumAl) {
  "use strict";

  const D2R = Math.PI / 180;
  const CELIK_YOGUNLUK = 7850;     // kg/m³ (donatı ve yapı çeliği)
  const TUR_ADI = { kolon: "Kolon", kiris: "Kiriş", cubuk: "Çubuk", doseme: "Döşeme", panel: "Panel", dugum: "Düğüm", mesnet: "Mesnet", temel: "Temel" };
  const CUBUK_TUR_ADI = { kolon: "Kolon", kiris: "Kiriş", capraz: "Çapraz", "makas-ust": "Makas üst başlık", "makas-alt": "Makas alt başlık",
    "makas-dikme": "Makas dikmesi", "makas-diyagonal": "Makas diyagonali", asik: "Aşık", kren: "Kren kirişi", bag: "Bağ", diger: "Çubuk" };
  const SEKME_ADI = { geometri: "Geometri", kesit: "Kesit ve malzeme", baglanti: "Bağlantı", yukler: "Yükler", ic: "İç kuvvetler",
    yer: "Yer değiştirme", tepki: "Mesnet tepkileri", tasarim: "Tasarım", metraj: "Metraj", yol: "Yük yolu", zemin: "Zemin" };
  const KUVVET = ["N", "V", "M", "Vz", "My", "T"];
  const KUVVET_AD = { N: "Normal kuvvet N", V: "Kesme V (y′)", M: "Moment M (z′, güçlü eksen)", Vz: "Kesme Vz (z′)", My: "Moment My (y′, zayıf eksen)", T: "Burulma T" };
  const KUVVET_BIRIM = { N: "kN", V: "kN", M: "kN·m", Vz: "kN", My: "kN·m", T: "kN·m" };
  const UC_BASLIK = ["N", "Vy", "Vz", "T", "My", "Mz"];

  // ================================================================= biçim
  function f(v, n) {
    if (v == null || typeof v !== "number" || !isFinite(v)) return "—";
    const k = n == null ? 2 : n;
    const q = Math.pow(10, k);
    let t = (Math.sign(v) * Math.round(Math.abs(v) * q) / q).toFixed(k);
    if (/^-0(\.0*)?$/.test(t)) t = t.slice(1);
    return t.replace(".", ",").replace("-", "−");
  }
  /** Büyüklüğe göre ondalık (3 anlamlı basamak civarı). */
  function fa(v) {
    if (v == null || typeof v !== "number" || !isFinite(v)) return "—";
    const a = Math.abs(v);
    if (a === 0) return "0";
    if (a >= 1000) return f(v, 0);
    if (a >= 100) return f(v, 1);
    if (a >= 10) return f(v, 2);
    if (a >= 0.01) return f(v, 3);
    return v.toExponential(2).replace(".", ",").replace("-", "−").replace("e", "·10^").replace("+", "");
  }
  function kacis(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function evet(b) { return b ? "evet" : "hayır"; }
  function vek(v, n) { return "(" + v.map(function (x) { return f(x, n == null ? 3 : n); }).join("; ") + ")"; }
  function cikar(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function boy(a) { return Math.hypot(a[0], a[1], a[2]); }

  // ================================================================= bağlam (bina + veri)
  function sayiNo(no) { return typeof no === "string" && /^\d+$/.test(no) ? +no : no; }
  /** Bina, çözüm ve geometriyi bir kez hazırlar (aynı bina/veri için önbellekli). */
  const onbellek = typeof WeakMap === "function" ? new WeakMap() : null;
  function baglam(bina, veri, sec) {
    const anahtar = bina || veri || {};
    const eskisi = onbellek && onbellek.get(anahtar);
    if (eskisi && eskisi.veri === (veri || null) && !(sec && sec.yeni)) return eskisi;
    const O = olcumAl();
    const b = bina || (veri && veri.bina) || {};
    let geo = null;
    if (O) { try { geo = O.geometri(b); } catch (e) { geo = null; } }
    const v = veri || null;
    const ag = v && v.ag ? v.ag : null;
    const dugum = new Map();
    if (ag) (ag.dugumler || []).forEach(function (d) { dugum.set(+d.no, d); });
    const c = { bina: b, veri: v, ag: ag, geo: geo, O: O, dugum: dugum, nb: (v && v.bina) || {}, kut: (v && v.kutuphane_ozeti) || {} };
    if (onbellek && typeof anahtar === "object") onbellek.set(anahtar, c);
    return c;
  }
  function bul(liste, no) { return (liste || []).find(function (x) { return x && String(x.no) === String(no); }) || null; }
  /** Bina elemanının FE parçaları (ag.elemanlar; parça sırasıyla). Genel model (surum 3) çözümünde her FE elemanı "cubuk" alanında
   *  çubuk numarasını taşır (türü kolon/kiriş/çapraz… olsa da); genelleştirilmiş ya da karma modelde aks–kat kolon/kiriş, kaynak
   *  {aks_kat, no} ile bulunur. */
  function feParcalari(c, tur, no) {
    if (!c.ag) return [];
    const s = String(no);
    const kayit = tur === "kolon" || tur === "kiris" ? tasarimKaydi(c, tur, no) : null;     // karma model: kaynak → çubuk no
    const cno = kayit && kayit.cubuk != null && kayit.kaynak && kayit.kaynak.aks_kat === tur ? String(kayit.cubuk) : null;
    return (c.ag.elemanlar || []).filter(function (e) {
      const k = e.kaynak && typeof e.kaynak === "object" ? e.kaynak : null;
      if (tur === "cubuk") {
        if (e.cubuk != null) return String(e.cubuk) === s;
        return k && k.tur ? k.tur === "cubuk" && String(k.no) === s : e.kaynak_tur === "cubuk" && String(e.kaynak_no) === s;
      }
      if (cno != null && e.cubuk != null) return String(e.cubuk) === cno;
      if (k && k.aks_kat) return k.aks_kat === tur && String(k.no) === s;
      if (k && k.tur) return k.tur === tur && String(k.no) === s;
      if (e.cubuk != null) return false;          // genel çözümün kendi çubuğu (aks–kat elemanı değil)
      return e.tur === tur && String(e.kaynak_no) === s && !e.kaynak_tur;
    }).sort(function (a, b) { return (a.parca || 1) - (b.parca || 1); });
  }
  function dugumAdresi(c, no) {
    const d = c.dugum.get(+no);
    if (d && d.aks && c.geo) {
      const g = c.geo.dugumler.find(function (x) { return x.no === +no; });
      if (g) return g.etiket;
    }
    if (c.geo) { const g = c.geo.dugumler.find(function (x) { return x.no === +no; }); if (g) return g.etiket; }
    return d && d.adres ? d.adres : "D" + no;
  }
  function geoCubuk(c, tur, no) {
    if (!c.geo) return null;
    const kaynak = tur === "kolon" ? "kolon" : tur === "kiris" ? "kiris" : "cubuk";
    return c.geo.cubuklar.find(function (x) { return x.anahtar === kaynak + ":" + no; }) || null;
  }
  function geoDugum(c, anahtar) { return c.geo ? c.geo.dugumler.find(function (x) { return x.anahtar === anahtar; }) || null : null; }

  // ---- durumlar, kombinasyonlar, zarf
  /** Seçilebilecek çözüm adları: yük durumları, kombinasyonlar (hazır ya da süperpozisyonla), zarf. */
  function durumListesi(v) {
    if (!v) return [];
    const l = [];
    const d = v.durumlar || {}, s = v.sonuclar || {};
    Object.keys(d).forEach(function (ad) { l.push({ ad: ad, etiket: "Durum " + ad, tur: "durum" }); });
    (v.kombinasyonlar || []).forEach(function (k) {
      if (!k || !k.uygulandi) return;
      if (s[k.ad] || superpozisyonMu(v, k)) l.push({ ad: k.ad, etiket: k.ad + (k.tur === "servis" ? " (servis)" : ""), tur: "kombinasyon", kaynak: k.kaynak });
    });
    Object.keys(s).forEach(function (ad) { if (!l.some(function (x) { return x.ad === ad; })) l.push({ ad: ad, etiket: ad, tur: "kombinasyon" }); });
    if (v.zarf && Array.isArray(v.zarf.elemanlar) && v.zarf.elemanlar.length) l.push({ ad: "Zarf", etiket: "Zarf (dayanım + servis)", tur: "zarf" });
    return l;
  }
  function superpozisyonMu(v, k) {
    const d = v.durumlar || {};
    return !!(k.katsayilar && Object.keys(k.katsayilar).length && Object.keys(k.katsayilar).every(function (n) { return d[n] && Array.isArray(d[n].elemanlar); }));
  }
  /** KISA çözüm: sonuclar / durumlar ya da kombinasyon katsayılarıyla süperpozisyon (doğrusal çözüm). */
  function kisa(v, ad) {
    if (!v || !ad || ad === "Zarf") return null;
    if (v.sonuclar && v.sonuclar[ad]) return v.sonuclar[ad];
    if (v.durumlar && v.durumlar[ad]) return v.durumlar[ad];
    const k = (v.kombinasyonlar || []).find(function (x) { return x.ad === ad; });
    if (!k || !superpozisyonMu(v, k)) return null;
    v._sup = v._sup || {};
    if (v._sup[ad]) return v._sup[ad];
    const adlar = Object.keys(k.katsayilar), ilk = v.durumlar[adlar[0]];
    const top = { elemanlar: [], dugumler: [], tepkiler: [], superpozisyon: true };
    const toplaDizi = function (sec_) {
      return function (x, i) { let s = 0; adlar.forEach(function (n) { const q = sec_(v.durumlar[n]); if (q && q[i] != null) s += k.katsayilar[n] * q[i]; }); return s; };
    };
    ilk.elemanlar.forEach(function (e, ei) {
      const out = { no: e.no, x: (e.x || []).slice() };
      KUVVET.forEach(function (a) { if (Array.isArray(e[a])) out[a] = e[a].map(toplaDizi(function (d) { return d.elemanlar[ei] && d.elemanlar[ei][a]; })); });
      if (Array.isArray(e.uc_kuvvetleri)) out.uc_kuvvetleri = e.uc_kuvvetleri.map(toplaDizi(function (d) { return d.elemanlar[ei] && d.elemanlar[ei].uc_kuvvetleri; }));
      top.elemanlar.push(out);
    });
    const alanlar = function (liste, anah, al) {
      (ilk[liste] || []).forEach(function (r, i) {
        const o_ = {}; o_[anah] = r[anah];
        al.forEach(function (a) { let s = 0; adlar.forEach(function (n) { const q = (v.durumlar[n][liste] || [])[i]; if (q) s += k.katsayilar[n] * (+q[a] || 0); }); o_[a] = s; });
        top[liste].push(o_);
      });
    };
    alanlar("dugumler", "no", ["uX", "uY", "uZ", "rX", "rY", "rZ"]);
    alanlar("tepkiler", "dugum", ["FX", "FY", "FZ", "MX", "MY", "MZ"]);
    try { Object.defineProperty(v, "_sup", { value: v._sup, enumerable: false, configurable: true, writable: true }); } catch (e) { /* yoksay */ }
    v._sup[ad] = top;
    return top;
  }
  function varsayilanDurum(v) {
    const l = durumListesi(v);
    if (!l.length) return null;
    const g = v.gosterilecek && v.gosterilecek[0];
    if (g && l.some(function (x) { return x.ad === g; })) return g;
    const k = l.find(function (x) { return x.tur === "kombinasyon"; });
    return (k || l[0]).ad;
  }
  /** Bina elemanının birleşik istasyon dizileri (parçalar uç uca). */
  function istasyonlar(K, fe) {
    if (!K) return null;
    const out = { x: [], N: [], V: [], M: [], Vz: [], My: [], T: [] };
    let ofs = 0, bulundu = false;
    fe.forEach(function (e) {
      const r_ = (K.elemanlar || []).find(function (x) { return x.no === e.no; });
      if (!r_ || !Array.isArray(r_.x)) { ofs += +e.L || 0; return; }
      bulundu = true;
      r_.x.forEach(function (x, i) {
        out.x.push(ofs + x);
        KUVVET.forEach(function (a) { out[a].push(Array.isArray(r_[a]) && r_[a][i] != null ? +r_[a][i] : 0); });
      });
      ofs += +e.L || (r_.x.length ? r_.x[r_.x.length - 1] : 0);
    });
    return bulundu ? out : null;
  }
  function ucKuvvetleri(K, fe) {
    if (!K || !fe.length) return null;
    const ilk = (K.elemanlar || []).find(function (x) { return x.no === fe[0].no; });
    const son = (K.elemanlar || []).find(function (x) { return x.no === fe[fe.length - 1].no; });
    if (!ilk || !son || !Array.isArray(ilk.uc_kuvvetleri) || !Array.isArray(son.uc_kuvvetleri)) return null;
    return { i: ilk.uc_kuvvetleri.slice(0, 6), j: son.uc_kuvvetleri.slice(6, 12) };
  }
  function ekstremum(x, d) {
    if (!d || !d.length) return null;
    let mx = 0, mn = 0;
    for (let i = 1; i < d.length; i++) { if (d[i] > d[mx]) mx = i; if (d[i] < d[mn]) mn = i; }
    return { max: d[mx], xmax: x[mx], min: d[mn], xmin: x[mn], mutlak: Math.max(Math.abs(d[mx]), Math.abs(d[mn])) };
  }
  /** Zarf: veri.zarf (FE elemanları üzerinden en büyük/en küçük ve belirleyen kombinasyon). */
  function zarfOzet(v, fe) {
    if (!v || !v.zarf) return null;
    const z = (v.zarf.elemanlar || []).filter(function (e) { return fe.some(function (x) { return x.no === e.no; }); });
    if (!z.length) return null;
    const out = {};
    KUVVET.forEach(function (a) {
      let mx = null, mn = null, bmx = null, bmn = null;
      z.forEach(function (e) {
        const q = e[a + "_max"], w = e[a + "_min"];
        if (q != null && (mx == null || q > mx)) { mx = q; bmx = e.belirleyen && e.belirleyen[a + "_max"]; }
        if (w != null && (mn == null || w < mn)) { mn = w; bmn = e.belirleyen && e.belirleyen[a + "_min"]; }
      });
      out[a] = { max: mx, min: mn, bmax: bmx, bmin: bmn };
    });
    return out;
  }
  /** Zarf eğrileri: uygulanan bütün kombinasyonların istasyon başına en büyük/en küçüğü. */
  function zarfEgrileri(v, fe) {
    const l = durumListesi(v).filter(function (d) { return d.tur === "kombinasyon"; });
    let out = null;
    l.forEach(function (d) {
      const s = istasyonlar(kisa(v, d.ad), fe);
      if (!s) return;
      if (!out) { out = { x: s.x.slice(), ust: {}, alt: {} }; KUVVET.forEach(function (a) { out.ust[a] = s[a].slice(); out.alt[a] = s[a].slice(); }); return; }
      if (s.x.length !== out.x.length) return;
      KUVVET.forEach(function (a) { s[a].forEach(function (q, i) { if (q > out.ust[a][i]) out.ust[a][i] = q; if (q < out.alt[a][i]) out.alt[a][i] = q; }); });
    });
    return out;
  }
  /**
   * Uç düğümlerini birleştiren doğruya göre en büyük bağıl sehim: v″ = κ = M/(EI), v(0) = v(L) = 0; κ istasyonlar arasında doğrusal
   * kabul edilerek kesin integral (Euler–Bernoulli; kesme şekil değiştirmesi ihmal). Dönüş {delta (m, işaretli), x}.
   */
  function bagilSehim(x, M, EI) {
    if (!x || x.length < 2 || !(EI > 0)) return null;
    const n = x.length, k = M.map(function (m) { return m / EI; });
    const th = [0], w = [0];
    for (let i = 0; i < n - 1; i++) {
      const h = x[i + 1] - x[i];
      th.push(th[i] + h * (k[i] + k[i + 1]) / 2);
      w.push(w[i] + th[i] * h + h * h * (2 * k[i] + k[i + 1]) / 6);
    }
    const L = x[n - 1] - x[0];
    if (!(L > 0)) return null;
    const th0 = -w[n - 1] / L;
    let en = 0, ex = x[0];
    for (let i = 0; i < n; i++) {
      const vi = w[i] + th0 * (x[i] - x[0]);
      if (Math.abs(vi) > Math.abs(en)) { en = vi; ex = x[i]; }
    }
    return { delta: en, x: ex };
  }

  // ---- kesit ve malzeme
  function dikdortgenOzellik(b, h) {
    const kisa_ = Math.min(b, h), uzun = Math.max(b, h), oran = kisa_ / uzun;
    const beta = 1 / 3 - 0.21 * oran * (1 - Math.pow(oran, 4) / 12);
    return { A: b * h, Iguclu: b * h * h * h / 12, Izayif: h * b * b * b / 12, J: beta * kisa_ * kisa_ * kisa_ * uzun,
      Wel: b * h * h / 6, Welz: h * b * b / 6, Wpl: b * h * h / 4, Wplz: h * b * b / 4 };
  }
  /** Kesit özellikleri (m birimleri): çözüm kütüphanesi > bina kesiti (dikdörtgen formülle) > yok. */
  function kesitOzellik(c, ad) {
    const k = (c.kut.kesitler || {})[ad], bk = (c.bina.kesitler || {})[ad] || {};
    const tip = (k && k.tip) || bk.tip || null;
    const out = { ad: ad, tip: tip, profil: (k && k.profil) || bk.profil || null, malzeme: (k && k.malzeme) || bk.malzeme || null, donati: bk.donati || null, pas: bk.pas };
    const b = k && k.b != null ? +k.b : (bk.b != null ? +bk.b : null), h = k && k.h != null ? +k.h : (bk.h != null ? +bk.h : null);
    out.b = b; out.h = h;
    if (k && k.A != null) {
      out.A = +k.A; out.Iguclu = +k.Iy; out.Izayif = +k.Iz; out.J = +k.J; out.Wpl = k.Wpl != null ? +k.Wpl : null; out.kaynak = "çözüm kütüphanesi";
      if (tip === "dikdortgen" && b && h) { const d = dikdortgenOzellik(b, h); out.Wel = d.Wel; out.Welz = d.Welz; out.Wplz = d.Wplz; }
    } else if (tip === "dikdortgen" && b && h) {
      Object.assign(out, dikdortgenOzellik(b, h)); out.kaynak = "b, h ile formülden";
    }
    if (out.A > 0) { out.iy = Math.sqrt(out.Iguclu / out.A); out.iz = Math.sqrt(out.Izayif / out.A); }
    return out;
  }
  function malzemeOzellik(c, ad) {
    if (!ad) return null;
    const m = (c.kut.malzemeler || {})[ad], bm = (c.bina.malzemeler || {})[ad] || {};
    const kut = (m && m.kutuphane) || bm.kutuphane || ad;
    const out = { ad: ad, kutuphane: kut, tur: m && m.tur };
    if (m) {
      out.E = m.E_kNm2 != null ? m.E_kNm2 / 1000 : null; out.G = m.G_kNm2 != null ? m.G_kNm2 / 1000 : null; out.gamma = m.gamma;
      ["fck", "fyk", "Fy", "Fu"].forEach(function (a) { if (m[a] != null) out[a] = +m[a]; });
      out.kaynak = "çözüm kütüphanesi";
      return out;
    }
    // çözüm yoksa adından: C30/37 → fck 30, Ec = 3250√fck + 14000 (TS 500); S275 → Fy 275, E = 200000 (ÇYTHYE)
    const cm = /^C(\d+)\//i.exec(kut), sm = /^S(\d{3})/i.exec(kut), bm2 = /^B(\d{3})/i.exec(kut);
    if (cm) Object.assign(out, { tur: "beton", fck: +cm[1], E: 3250 * Math.sqrt(+cm[1]) + 14000, gamma: 25, kaynak: "adından (TS 500 Denk. 3.2)" });
    else if (sm) Object.assign(out, { tur: "celik", Fy: +sm[1], E: 200000, G: 77200, gamma: 78.5, kaynak: "adından (ÇYTHYE md. 2.3)" });
    else if (bm2) Object.assign(out, { tur: "donati", fyk: +bm2[1], E: 200000, kaynak: "adından" });
    return out;
  }

  // ================================================================= MODEL ÜRETİMİ
  /**
   * Eleman bilgi modeli. hedef = {tur: "kolon"|"kiris"|"cubuk"|"doseme"|"panel"|"dugum"|"mesnet"|"temel", no}.
   *  sec: { durum? (iç kuvvet/yer değiştirme için çözüm adı ya da "Zarf"), paket?, eski? (çözüm güncel değil uyarısı) }
   */
  function bilgi(hedef, bina, veri, sec) {
    sec = sec || {};
    if (!hedef || !hedef.tur) throw new Error("Eleman bilgisi: hedef {tur, no} gerekli.");
    const c = baglam(bina, veri);
    const tur = hedef.tur, no = sayiNo(hedef.no);
    let m;
    if (tur === "kolon" || tur === "kiris" || tur === "cubuk") m = cubukModeli(c, tur, no, sec);
    else if (tur === "dugum" || tur === "mesnet") m = dugumModeli(c, tur, no, sec);
    else if (tur === "doseme" || tur === "panel") m = panelModeli(c, tur, no, sec);
    else if (tur === "temel" && hedef.alt) m = yayiliTemelModeli(c, hedef, sec);
    else if (tur === "temel") m = temelModeli(c, no, sec);
    else throw new Error("Eleman bilgisi: bilinmeyen tür “" + tur + "”.");
    m.cozumVar = !!(c.veri && c.veri.durumlar);
    if (sec.eski && m.cozumVar) m.uyari = "Çözüm modelin son hâline ait değil; analiz sekmeleri eski sonucu gösterir.";
    if (sec.paket) paketBirlestir(m, sec.paket);
    m.sekmeler = m.sekmeler.filter(function (s) { return s.bolumler.length; });
    return m;
  }
  function onceCozun(ad) { return { not: "Önce çözün: " + ad + " çözümden sonra görünür.", cozum: true }; }
  function satir(ad, deger, birim) { return [ad, deger, birim || ""]; }

  // ---- çubuk (kolon, kiriş, genel çubuk)
  function cubukModeli(c, tur, no, sec) {
    const ham = { tur: tur, no: no };
    const kayit = bul(tur === "kolon" ? c.bina.kolonlar : tur === "kiris" ? c.bina.kirisler : c.bina.cubuklar, no);
    const norm = bul(tur === "kolon" ? c.nb.kolonlar : tur === "kiris" ? c.nb.kirisler : c.nb.cubuklar, no) || {};
    if (!kayit && !norm.no) throw new Error(TUR_ADI[tur] + " " + no + " modelde yok.");
    const k = Object.assign({}, kayit || {}, norm);
    const fe = feParcalari(c, tur, no);
    const g = geoCubuk(c, tur, no);
    // uçlar
    let Pi = null, Pj = null, ai = "", aj = "", ni = null, nj = null;
    if (fe.length && c.dugum.size) {
      ni = fe[0].dugumler[0]; nj = fe[fe.length - 1].dugumler[1];
      const di = c.dugum.get(+ni), dj = c.dugum.get(+nj);
      if (di && dj) { Pi = [di.X, di.Y, di.Z]; Pj = [dj.X, dj.Y, dj.Z]; ai = dugumAdresi(c, ni); aj = dugumAdresi(c, nj); }
    }
    if (!Pi && g) {
      Pi = g.A; Pj = g.B;
      const gi = geoDugum(c, g.i), gj = geoDugum(c, g.j);
      ai = gi ? gi.etiket : ""; aj = gj ? gj.etiket : "";
      ni = gi && gi.no != null ? gi.no : null; nj = gj && gj.no != null ? gj.no : null;
    }
    const altTur = tur === "cubuk" ? (k.tur || "diger") : tur;
    const turAdi = tur === "cubuk" ? (CUBUK_TUR_ADI[altTur] || "Çubuk") : TUR_ADI[tur];
    const m = { tur: tur, no: no, turAdi: turAdi, baslik: turAdi + " " + no, adres: k.adres || (ai && aj ? ai + " → " + aj : ""), sekmeler: [], ham: ham };
    // ---- Geometri
    const geoB = [];
    const L = Pi && Pj ? boy(cikar(Pj, Pi)) : (+k.L || null);
    ham.L = L;
    if (Pi && Pj) {
      const d = cikar(Pj, Pi), yatay = Math.hypot(d[0], d[1]);
      ham.egim = Math.atan2(d[2], yatay) / D2R;
      geoB.push({ baslik: "Konum", satirlar: [
        satir("Aks adresi", ai + " → " + aj),
        k.adres ? satir("Eleman adresi", k.adres) : null,
        satir("Boy L", f(L, 3), "m"), satir("Yatay izdüşüm", f(yatay, 3), "m"), satir("Eğim (yataydan)", f(ham.egim, 2), "°"),
        satir("Doğrultu kosinüsleri", vek(d.map(function (x) { return L > 0 ? x / L : 0; }), 4)),
        satir("Yerel eksen açısı (aci)", f(aciDegeri(k, tur), 1), "°"),
        (k.kat != null ? satir("Kat", String(k.kat)) : null),
      ].filter(Boolean) });
      geoB.push({ baslik: "Uç düğümleri", tablo: { basliklar: ["Uç", "Düğüm", "Adres", "X (m)", "Y (m)", "Z (m)"],
        satirlar: [["i", ni != null ? String(ni) : "—", ai, f(Pi[0], 3), f(Pi[1], 3), f(Pi[2], 3)], ["j", nj != null ? String(nj) : "—", aj, f(Pj[0], 3), f(Pj[1], 3), f(Pj[2], 3)]] } });
      const eks = yerelEksen(c, fe, Pi, Pj, aciDegeri(k, tur));
      if (eks) geoB.push({ baslik: "Yerel eksenler (bina koordinatında)", satirlar: [satir("x′ (eleman ekseni)", vek(eks[0])), satir("y′", vek(eks[1])), satir("z′", vek(eks[2]))] });
    } else geoB.push({ not: "Geometri çözülemedi (uç düğüm başvuruları geçersiz)." });
    const bagli = bagliElemanlar(c, tur, no, fe, g);
    if (bagli.length) geoB.push({ baslik: "Bağlı elemanlar", satirlar: bagli.map(function (x) { return satir(x.uc + " ucunda", x.ad); }) });
    if (fe.length > 1) geoB.push({ baslik: "Sonlu eleman parçaları", tablo: { basliklar: ["Parça", "Eleman", "L (m)", "Düğümler"],
      satirlar: fe.map(function (e) { return [String(e.parca || 1), "e" + e.no, f(+e.L, 3), e.dugumler.join(" → ")]; }) } });
    m.sekmeler.push({ id: "geometri", ad: SEKME_ADI.geometri, bolumler: geoB });
    // ---- Kesit ve malzeme
    const ks = k.kesit ? kesitOzellik(c, k.kesit) : null;
    const tasarimK = tasarimKaydi(c, tur, no);
    const kesB = [];
    if (ks) {
      ham.A = ks.A; ham.kesit = ks.ad;
      const s = [satir("Kesit", ks.ad + (ks.profil ? " (" + ks.profil + ")" : "")), satir("Tip", ks.tip === "profil" ? "çelik profil" : ks.tip === "dikdortgen" ? "dikdörtgen" : (ks.tip || "—"))];
      if (tur === "kolon" && k.bX != null) s.push(satir("Boyutlar bX × bY", f(k.bX * 100, 0) + " × " + f(k.bY * 100, 0), "cm"), satir("Yön (güçlü boyut)", k.yon === "y" ? "Y doğrultusunda" : "X doğrultusunda"));
      else if (ks.b != null && ks.h != null) s.push(satir("Boyutlar b × h", f(ks.b * 100, 1) + " × " + f(ks.h * 100, 1), "cm"));
      s.push(satir("Alan A", fa(ks.A * 1e4), "cm²"), satir("I (güçlü eksen)", fa(ks.Iguclu * 1e8), "cm⁴"), satir("I (zayıf eksen)", fa(ks.Izayif * 1e8), "cm⁴"),
        satir("Burulma sabiti J", fa(ks.J * 1e8), "cm⁴"));
      if (ks.Wel != null) s.push(satir("W elastik (güçlü / zayıf)", fa(ks.Wel * 1e6) + " / " + fa(ks.Welz * 1e6), "cm³"));
      if (ks.Wpl != null) s.push(satir("W plastik (güçlü)", fa(ks.Wpl * 1e6), "cm³"));
      if (ks.iy != null) s.push(satir("Atalet yarıçapı i (güçlü / zayıf)", f(ks.iy * 100, 2) + " / " + f(ks.iz * 100, 2), "cm"));
      if (L && ks.iz > 0) s.push(satir("Narinlik L/i (zayıf)", f(L / ks.iz, 1)));
      if (tasarimK && tasarimK.ozet && tasarimK.ozet.sinif) s.push(satir("Kesit sınıfı", String(tasarimK.ozet.sinif)));
      if (fe.length && fe[0].rijitlik_carpani != null) s.push(satir("Rijitlik çarpanı (çatlamış kesit)", f(+fe[0].rijitlik_carpani, 2)));
      if (ks.kaynak) s.push(satir("Özelliklerin kaynağı", ks.kaynak));
      kesB.push({ baslik: "Kesit", satirlar: s });
    } else kesB.push({ not: "Kesit atanmamış." });
    const ml = malzemeOzellik(c, (ks && ks.malzeme) || k.malzeme);
    if (ml) kesB.push({ baslik: "Malzeme", satirlar: malzemeSatirlari(ml) });
    const dn = ks && ks.donati ? malzemeOzellik(c, ks.donati) : null;
    if (dn) kesB.push({ baslik: "Donatı", satirlar: malzemeSatirlari(dn).concat(ks.pas != null ? [satir("Paspayı", f(ks.pas * 1000, 0), "mm")] : []) });
    m.sekmeler.push({ id: "kesit", ad: SEKME_ADI.kesit, bolumler: kesB });
    // ---- Bağlantı
    const bagB = [];
    const serb = k.serbest || null;
    const serbMetin = function (l) { return l && l.length ? l.join(", ") + " serbest" : "rijit (sürekli)"; };
    bagB.push({ baslik: "Uç serbestlikleri (yerel)", satirlar: [satir("i ucu", serbMetin(serb && serb.i)), satir("j ucu", serbMetin(serb && serb.j)),
      satir("Yalnız çekme", evet(!!k.yalniz_cekme))] });
    const mes = [[ni, "i"], [nj, "j"]].map(function (q) { const s = mesnetBul(c, q[0]); return s ? satir(q[1] + " ucunda mesnet", s) : null; }).filter(Boolean);
    if (mes.length) bagB.push({ baslik: "Mesnet", satirlar: mes });
    const tm = tur === "kolon" ? temelKaydi(c, no) : null;
    if (tm) bagB.push({ baslik: "Temel", satirlar: [satir("Temel", "T-" + (tm.aks || []).join("") + " · " + f(tm.B, 2) + " × " + f(tm.L, 2) + " m"), satir("Mesnet modeli", (c.nb.temeller || c.bina.temeller || {}).mesnet || "—")] });
    m.sekmeler.push({ id: "baglanti", ad: SEKME_ADI.baglanti, bolumler: bagB });
    // ---- Yükler
    m.sekmeler.push({ id: "yukler", ad: SEKME_ADI.yukler, bolumler: cubukYukleri(c, tur, no, k, ham) });
    // ---- İç kuvvetler + yer değiştirme
    const durumlar = durumListesi(c.veri);
    const durum = sec.durum && durumlar.some(function (d) { return d.ad === sec.durum; }) ? sec.durum : varsayilanDurum(c.veri);
    m.durumlar = durumlar; m.durum = durum;
    m.sekmeler.push({ id: "ic", ad: SEKME_ADI.ic, secici: true, bolumler: icKuvvetBolumleri(c, fe, durum, ham) });
    m.sekmeler.push({ id: "yer", ad: SEKME_ADI.yer, secici: true, bolumler: yerDegistirmeBolumleri(c, fe, durum, ni, nj, ks, ml, L, ham) });
    // ---- Tasarım
    m.sekmeler.push({ id: "tasarim", ad: SEKME_ADI.tasarim, bolumler: tasarimBolumleri(c, tasarimK, ham) });
    // ---- Metraj
    m.sekmeler.push({ id: "metraj", ad: SEKME_ADI.metraj, bolumler: cubukMetraj(c, tur, k, ks, ml, L, tasarimK, ham) });
    // ---- Yük yolu
    m.sekmeler.push({ id: "yol", ad: SEKME_ADI.yol, bolumler: yukYoluBolumleri(c, sankeyKimligi(c, tur, no, k), ham) });
    // özet
    const ozet = [];
    if (ks) ozet.push({ ad: "Kesit", deger: ks.ad });
    if (L) ozet.push({ ad: "L", deger: f(L, 2) + " m" });
    if (tasarimK && tasarimK.dc != null) ozet.push({ ad: "D/C", deger: f(+tasarimK.dc, 2), dc: +tasarimK.dc });
    m.ozet = ozet;
    m.alt = ozet.map(function (o) { return o.ad === "Kesit" ? o.deger : o.ad + " " + o.deger; }).join(" · ");
    return m;
  }
  function aciDegeri(k, tur) { if (k.aci != null) return +k.aci; if (tur === "kolon") return k.yon === "y" ? 90 : 0; return 0; }
  function yerelEksen(c, fe, Pi, Pj, aci) {
    if (fe.length && Array.isArray(fe[0].lam) && fe[0].lam.length === 3) return fe[0].lam.map(function (r_) { return r_.map(Number); });
    const MO = typeof window !== "undefined" ? window.ModelOps : (typeof require === "function" ? (function () { try { return require("./model_ops.js"); } catch (e) { return null; } })() : null);
    if (MO && MO.yerelEksenVektor) { try { const e = MO.yerelEksenVektor(Pi, Pj, aci || 0); return [e.x || e[0], e.y || e[1], e.z || e[2]]; } catch (e) { return null; } }
    return null;
  }
  function malzemeSatirlari(ml) {
    const s = [satir("Malzeme", ml.kutuphane + (ml.ad !== ml.kutuphane ? " (" + ml.ad + ")" : ""))];
    if (ml.fck != null) s.push(satir("f_ck", f(ml.fck, 0), "MPa"));
    if (ml.fyk != null) s.push(satir("f_yk", f(ml.fyk, 0), "MPa"));
    if (ml.Fy != null) s.push(satir("F_y", f(ml.Fy, 0), "MPa"));
    if (ml.Fu != null) s.push(satir("F_u", f(ml.Fu, 0), "MPa"));
    if (ml.E != null) s.push(satir("E", f(ml.E, 0), "MPa"));
    if (ml.G != null) s.push(satir("G", f(ml.G, 0), "MPa"));
    if (ml.gamma != null) s.push(satir("Birim hacim ağırlığı γ", f(ml.gamma, 1), "kN/m³"));
    if (ml.kaynak) s.push(satir("Kaynak", ml.kaynak));
    return s;
  }
  function mesnetBul(c, no) {
    if (no == null) return null;
    if (c.ag) { const s = (c.ag.mesnetler || []).find(function (x) { return +x.dugum === +no; }); if (s) return s.tip || "mesnet"; }
    return null;
  }
  function bagliElemanlar(c, tur, no, fe, g) {
    const out = [];
    if (c.ag && fe.length) {
      const uc = { i: fe[0].dugumler[0], j: fe[fe.length - 1].dugumler[1] };
      Object.keys(uc).forEach(function (u) {
        const ad = new Set();
        (c.ag.elemanlar || []).forEach(function (e) {
          if (fe.some(function (x) { return x.no === e.no; })) return;
          if (e.dugumler.indexOf(uc[u]) < 0) return;
          ad.add((TUR_ADI[e.tur] || CUBUK_TUR_ADI[e.tur] || "Eleman") + " " + (e.kaynak_no != null ? e.kaynak_no : e.no) + (e.adres ? " (" + e.adres + ")" : ""));
        });
        if (ad.size) out.push({ uc: u, ad: Array.from(ad).join(", ") });
      });
      return out;
    }
    if (c.geo && g) {
      [["i", g.i], ["j", g.j]].forEach(function (q) {
        const ad = c.geo.cubuklar.filter(function (x) { return x !== g && (x.i === q[1] || x.j === q[1]); }).map(function (x) { return x.etiket; });
        if (ad.length) out.push({ uc: q[0], ad: ad.join(", ") });
      });
    }
    return out;
  }
  /** Tasarım kaydı. Genel model kayıtları {tur: kolon|kiris|capraz…, no, cubuk, kaynak?}: "cubuk" hedefi çubuk numarasıyla; aks–kat
   *  kolon/kiriş önce kaynağı ({aks_kat, no}) eşleşen kayıtla (genelleştirilmiş / karma model), yoksa tür ve numarayla bulunur. */
  function tasarimKaydi(c, tur, no) {
    const t = c.veri && c.veri.tasarim;
    if (!t) return null;
    const l = t.elemanlar || [], s = String(no);
    if (tur === "cubuk") return l.find(function (e) { return e.cubuk != null ? String(e.cubuk) === s : e.tur === "cubuk" && String(e.no) === s; }) || null;
    return l.find(function (e) { return e.kaynak && e.kaynak.aks_kat === tur && String(e.kaynak.no) === s; }) ||
      l.find(function (e) { return e.tur === tur && String(e.no) === s; }) || null;
  }
  /** Genel çözümde (veri.model "genel") aks–kat kolon/kiriş — karma model: aks–kat elemanları genel motorda çözüldü — çözümdeki çubuk
   *  numarası: tasarım kaydının ya da akış kolon kaydının kaynağı ({aks_kat, no}) üzerinden; bulunamazsa null. */
  function genelCubukNo(c, tur, no) {
    const v = c.veri;
    if (!v || v.model !== "genel" || (tur !== "kolon" && tur !== "kiris")) return null;
    const s = String(no), es = function (x) { return !!x && !!x.kaynak && x.kaynak.aks_kat === tur && String(x.kaynak.no) === s; };
    const t = ((v.tasarim && v.tasarim.elemanlar) || []).find(function (e) { return es(e) && e.cubuk != null; });
    if (t) return t.cubuk;
    const k = tur === "kolon" ? ((v.akis && v.akis.kolonlar) || []).find(es) : null;
    return k ? k.no : null;
  }
  /** Kolonun tekil temeli. veri.akis.temeller'de B'siz kayıtlar (eski genel model çözümünde açık mesnetler) temel değildir: atlanır. */
  function temelKaydi(c, kolonNo) {
    const tl = (c.nb.temeller && c.nb.temeller.liste) || [];
    const t = tl.find(function (x) { return String(x.kolon_no) === String(kolonNo) && x.B != null; });
    const a = c.veri && c.veri.akis ? (c.veri.akis.temeller || []).find(function (x) { return x && x.B != null && String(x.kolon_no) === String(kolonNo); }) : null;
    if (!t && !a) return null;
    return Object.assign({}, t || {}, a || {});
  }
  function cubukYukleri(c, tur, no, k, ham) {
    const out = [];
    const v = c.veri;
    // genel model (surum 3): veri.yukler.cubuklar (G/Q/S: öz, panel, duvar, ek, toplam kN); panel payları veri.akis.sankey'den (P → Ç).
    // Karma modelde (aks–kat kolon/kiriş, genel çözüm) kaydın çubuk numarasıyla okunur.
    const cno = tur === "cubuk" ? no : genelCubukNo(c, tur, no);
    if (cno != null && v && v.yukler && Array.isArray(v.yukler.cubuklar)) {
      const y = v.yukler.cubuklar.find(function (x) { return String(x.no) === String(cno); });
      if (y) {
        const G = y.G || {}, Q = y.Q || {}, S = y.S || {};
        const sat = [["Öz ağırlık", G.oz, Q.oz, S.oz], ["Panelden", G.panel, Q.panel, S.panel], ["Duvar", G.duvar, Q.duvar, S.duvar], ["Ek yük", G.ek, Q.ek, S.ek],
          ["Toplam", G.toplam_kN, Q.toplam_kN, S.toplam_kN]];
        const karVar = sat.some(function (r_) { return r_[3]; });
        out.push({ baslik: "Çubuğa gelen yükler (toplam, kN)", tablo: { basliklar: ["Kaynak", "G", "Q"].concat(karVar ? ["S"] : []),
          satirlar: sat.filter(function (r_, i) { return i === 4 || r_[1] || r_[2] || r_[3]; }).map(function (r_) {
            return [r_[0], f(+r_[1] || 0, 2), f(+r_[2] || 0, 2)].concat(karVar ? [f(+r_[3] || 0, 2)] : []); }) } });
        ham.yuk = { G: +G.toplam_kN || 0, Q: +Q.toplam_kN || 0, S: +S.toplam_kN || 0 };
        if (y.L > 0) out.push({ baslik: "Ortalama çizgisel yük", satirlar: [satir("q_G = ΣG / L", f((+G.toplam_kN || 0) / y.L, 2), "kN/m"), satir("q_Q = ΣQ / L", f((+Q.toplam_kN || 0) / y.L, 2), "kN/m")] });
      }
      const pay = new Map();
      ((v.akis && v.akis.sankey) || []).forEach(function (e) {
        if (e.hedef !== "Ç" + cno) return;
        if (!pay.has(e.kaynak)) pay.set(e.kaynak, { G: 0, Q: 0, S: 0 });
        const r_ = pay.get(e.kaynak); if (r_[e.durum] != null) r_[e.durum] += +e.kN || 0;
      });
      if (pay.size) {
        const qVar = Array.from(pay.values()).some(function (r_) { return r_.Q || r_.S; });
        out.push({ baslik: "Panellerden aktarılan paylar (kN)", tablo: { basliklar: ["Panel", "G"].concat(qVar ? ["Q", "S"] : []),
          satirlar: Array.from(pay.keys()).map(function (a) { const r_ = pay.get(a); return [a, f(r_.G, 2)].concat(qVar ? [f(r_.Q, 2), f(r_.S, 2)] : []); }) },
          notlar: qVar ? [] : ["Hareketli (Q) ve kar (S) yükleri panelden aynı kenar paylarıyla dağıtılır."] });
        ham.panelPay = Array.from(pay.values()).reduce(function (t, r_) { return t + r_.G; }, 0);
      }
      // kolon türü çubuk: kattan ve birikimli eksenel kuvvet (veri.akis.kolonlar; no = çubuk no)
      const ak = ((v.akis && v.akis.kolonlar) || []).find(function (x) { return String(x.no) === String(cno); });
      if (ak) {
        out.push({ baslik: "Kolon yükleri", satirlar: [satir("Bu kattan N (G / Q)", f(ak.N_G, 2) + " / " + f(ak.N_Q, 2), "kN"),
          satir("Birikimli N (G / Q)", f(ak.N_kum_G, 2) + " / " + f(ak.N_kum_Q, 2), "kN")] });
        ham.N_kum = { G: ak.N_kum_G, Q: ak.N_kum_Q };
      }
    }
    if (tur === "kiris" && cno == null && v && v.yukler) {
      const y = (v.yukler.kirisler || []).find(function (x) { return String(x.no) === String(no); });
      if (y) {
        const G = y.G || {}, Q = y.Q || {}, S = y.S || {};
        const sat = [["Döşemeden", G.doseme, Q.doseme, S.doseme], ["Duvar", G.duvar, null, null], ["Öz ağırlık", G.oz, null, null], ["Ek yük", G.ek, Q.ek, S.ek],
          ["Toplam", G.toplam_kN, Q.toplam_kN, S.toplam_kN]];
        const karVar = sat.some(function (r_) { return r_[3]; });
        out.push({ baslik: "Kirişe gelen yükler (toplam, kN)", tablo: { basliklar: ["Kaynak", "G", "Q"].concat(karVar ? ["S"] : []),
          satirlar: sat.map(function (r_) { return [r_[0], f(r_[1], 2), r_[2] == null ? "—" : f(r_[2], 2)].concat(karVar ? [r_[3] == null ? "—" : f(r_[3], 2)] : []); }) } });
        ham.yuk = { G: G.toplam_kN, Q: Q.toplam_kN };
        if (y.kN_m) {
          const q = y.kN_m;
          out.push({ baslik: "Çizgisel yükler", satirlar: [satir("Öz ağırlık", f(q.oz, 2), "kN/m"), satir("Duvar", f(q.duvar, 2), "kN/m"),
            satir("Eşdeğer düzgün (moment) G / Q", f(q.q_eM_G, 2) + " / " + f(q.q_eM_Q, 2), "kN/m"), satir("Eşdeğer düzgün (kesme) G / Q", f(q.q_eV_G, 2) + " / " + f(q.q_eV_Q, 2), "kN/m")] });
        }
        if (y.el_hesabi) {
          const e = y.el_hesabi;
          out.push({ baslik: "El hesabı (basit kiriş)", satirlar: [satir("Uç tepkisi R G / Q", f(e.R_G, 2) + " / " + f(e.R_Q, 2), "kN"), satir("Açıklık momenti M G / Q", f(e.M_G, 2) + " / " + f(e.M_Q, 2), "kN·m")] });
        }
      }
      const paylar = [];
      (v.yukler.dosemeler || []).forEach(function (d) {
        (d.paylar || []).forEach(function (p_) {
          if (String(p_.kiris_no) === String(no)) paylar.push(["D" + d.no, (p_.kenar_ad || "") + (p_.kenar ? " (" + (p_.kenar === "kisa" ? "kısa" : "uzun") + ")" : ""),
            p_.sekil === "ucgen" ? "üçgen" : p_.sekil === "trapez" ? "trapez" : p_.sekil === "duzgun" ? "düzgün" : (p_.sekil || "—"), f(p_.tepe_g, 2), f(p_.tepe_q, 2), f(p_.toplam_G, 2), f(p_.toplam_Q, 2)]);
        });
      });
      if (paylar.length) out.push({ baslik: "Döşemeden aktarılan paylar", tablo: { basliklar: ["Döşeme", "Kenar", "Şekil", "Tepe g (kN/m)", "Tepe q (kN/m)", "G (kN)", "Q (kN)"], satirlar: paylar } });
    }
    if (tur === "kolon" && cno == null && v) {
      const yk = v.yukler ? (v.yukler.kolonlar || []).find(function (x) { return String(x.no) === String(no); }) : null;
      const ak = v.akis ? (v.akis.kolonlar || []).find(function (x) { return String(x.no) === String(no); }) : null;
      const s = [];
      if (yk) s.push(satir("Öz ağırlık", f(yk.oz_kN, 2), "kN"));
      if (ak) {
        s.push(satir("Bu kattan N (G / Q)", f(ak.N_G, 2) + " / " + f(ak.N_Q, 2), "kN"), satir("Birikimli N (G / Q)", f(ak.N_kum_G, 2) + " / " + f(ak.N_kum_Q, 2), "kN"));
        if (ak.A_trib != null) s.push(satir("Yük alanı (el hesabı)", f(ak.A_trib, 2), "m²"), satir("Yük alanıyla N (G / Q)", f(ak.N_trib_G, 2) + " / " + f(ak.N_trib_Q, 2), "kN"),
          satir("Sonlu eleman ile fark", f(ak.fark_yuzde, 1), "%"));
        ham.N_kum = { G: ak.N_kum_G, Q: ak.N_kum_Q };
      }
      if (s.length) out.push({ baslik: "Kolon yükleri", satirlar: s });
    }
    const ek = (c.bina.ek_yukler || []).filter(function (y) {
      return (tur === "kiris" && y.tur === "kiris" && String(y.kiris) === String(no)) || (y.tur === "cubuk" && tur === "cubuk" && String(y.cubuk) === String(no));
    });
    if (ek.length) out.push({ baslik: "Tanımlı ek yükler", tablo: { basliklar: ["Durum", "Yön", "q1", "q2", "Aralık", "Birim"],
      satirlar: ek.map(function (y) { return [y.durum || "—", y.yon || "aşağı", f(y.q1 != null ? +y.q1 : +y.q, 2), f(y.q2 != null ? +y.q2 : +y.q, 2),
        y.x1 != null || y.x2 != null ? f(+y.x1 || 0, 2) + "–" + (y.x2 == null ? "L" : f(+y.x2, 2)) : "tüm boy", "kN/m"]; }) } });
    if (!out.length) out.push(c.veri ? { not: "Bu elemana tanımlı yük yok." } : onceCozun("Döşeme payları, öz ağırlık ve duvar yükleri"));
    return out;
  }
  function icKuvvetBolumleri(c, fe, durum, ham) {
    if (!c.veri || !c.veri.durumlar) return [onceCozun("İç kuvvetler")];
    if (!fe.length) return [{ not: "Bu eleman çözüm ağında bulunamadı (model çözümden sonra değişmiş olabilir)." }];
    const out = [];
    if (durum === "Zarf") {
      const z = zarfOzet(c.veri, fe);
      if (!z) return [{ not: "Zarf bu eleman için yok." }];
      out.push({ baslik: "Zarf (uygulanan kombinasyonlar)", tablo: { basliklar: ["Büyüklük", "En büyük", "Belirleyen", "En küçük", "Belirleyen"],
        satirlar: KUVVET.map(function (a) { return [a + " (" + KUVVET_BIRIM[a] + ")", f(z[a].max, 2), z[a].bmax || "—", f(z[a].min, 2), z[a].bmin || "—"]; }) } });
      ham.zarf = z;
      const e = zarfEgrileri(c.veri, fe);
      if (e) out.push({ baslik: "Zarf diyagramları", svg: ["N", "V", "M"].map(function (a) { return diyagramSvg(e.x, e.ust[a], a, { alt: e.alt[a] }); }).join("") });
      return out;
    }
    const K = kisa(c.veri, durum);
    const s = istasyonlar(K, fe);
    if (!s) return [{ not: "“" + durum + "” için bu elemanın sonucu yok." }];
    const ext = {};
    KUVVET.forEach(function (a) { ext[a] = ekstremum(s.x, s[a]); });
    ham.ext = ext; ham.istasyon = s; ham.durum = durum;
    out.push({ baslik: "Diyagramlar — " + durum, svg: ["N", "V", "M"].map(function (a) { return diyagramSvg(s.x, s[a], a); }).join("") });
    out.push({ baslik: "En büyük ve en küçük değerler", tablo: { basliklar: ["Büyüklük", "En büyük", "x (m)", "En küçük", "x (m)"],
      satirlar: KUVVET.map(function (a) { const e = ext[a]; return [a + " (" + KUVVET_BIRIM[a] + ")", f(e.max, 2), f(e.xmax, 2), f(e.min, 2), f(e.xmin, 2)]; }) } });
    const uc = ucKuvvetleri(K, fe);
    if (uc) out.push({ baslik: "Uç kuvvetleri (yerel eksen, elemana etkiyen)", tablo: { basliklar: ["Bileşen", "i ucu", "j ucu"],
      satirlar: UC_BASLIK.map(function (b, k) { return [b + (b === "T" || b === "My" || b === "Mz" ? " (kN·m)" : " (kN)"), f(uc.i[k], 2), f(uc.j[k], 2)]; }) } });
    const zayif = ["Vz", "My", "T"].some(function (a) { return ext[a].mutlak > 1e-3; });
    if (zayif) out.push({ baslik: "Zayıf eksen ve burulma", acilir: true, svg: ["Vz", "My", "T"].map(function (a) { return diyagramSvg(s.x, s[a], a); }).join("") });
    if (K.superpozisyon) out.push({ not: "Bu kombinasyon yük durumlarının katsayılı toplamıyla (doğrusal süperpozisyon) hesaplandı." });
    return out;
  }
  function yerDegistirmeBolumleri(c, fe, durum, ni, nj, ks, ml, L, ham) {
    if (!c.veri || !c.veri.durumlar) return [onceCozun("Yer değiştirmeler")];
    if (durum === "Zarf") return [{ not: "Yer değiştirme için bir yük durumu ya da kombinasyon seçin (zarf yalnız iç kuvvetler için)." }];
    const K = kisa(c.veri, durum);
    if (!K) return [{ not: "“" + durum + "” için sonuç yok." }];
    const out = [];
    const sat = [];
    [[ni, "i"], [nj, "j"]].forEach(function (q) {
      const d = (K.dugumler || []).find(function (x) { return +x.no === +q[0]; });
      if (d) sat.push([q[1] + " (" + q[0] + ")", f(d.uX * 1000, 3), f(d.uY * 1000, 3), f(d.uZ * 1000, 3), f(d.rX * 1000, 4), f(d.rY * 1000, 4), f(d.rZ * 1000, 4)]);
    });
    if (sat.length) out.push({ baslik: "Uç düğümleri — " + durum + " (bina koordinatı)", tablo: { basliklar: ["Uç", "uX (mm)", "uY (mm)", "uZ (mm)", "rX (mrad)", "rY (mrad)", "rZ (mrad)"], satirlar: sat } });
    const s = istasyonlar(K, fe);
    if (s && ks && ml && ml.E && ks.Iguclu) {
      const c_ = fe[0] && fe[0].rijitlik_carpani != null ? +fe[0].rijitlik_carpani : 1;
      const E = ml.E * 1000 * c_;   // kN/m²
      const a = bagilSehim(s.x, s.M, E * ks.Iguclu), b = bagilSehim(s.x, s.My, E * ks.Izayif);
      const en = [a, b].filter(Boolean).sort(function (p_, q) { return Math.abs(q.delta) - Math.abs(p_.delta); })[0];
      if (en) {
        ham.sehim = { guclu: a ? a.delta : null, zayif: b ? b.delta : null, en: en.delta, x: en.x };
        const oran = Math.abs(en.delta) > 1e-9 && L ? L / Math.abs(en.delta) : null;
        out.push({ baslik: "Açıklık içi bağıl sehim", satirlar: [
          satir("Güçlü eksen (M ile)", a ? f(a.delta * 1000, 3) : "—", "mm"), satir("Zayıf eksen (My ile)", b ? f(b.delta * 1000, 3) : "—", "mm"),
          satir("En büyük |δ|", f(Math.abs(en.delta) * 1000, 3) + "  (x = " + f(en.x, 2) + " m)", "mm"), satir("L/δ", oran ? (oran > 1e5 ? "> 100000" : f(oran, 0)) : "—"),
          satir("Eğilme rijitliği EI (güçlü)", fa(E * ks.Iguclu), "kN·m²"),
        ], notlar: ["Uç düğümleri birleştiren doğruya göre; κ = M/EI iki kez integrallenir (kesme şekil değiştirmesi ihmal)" + (c_ !== 1 ? "; çatlamış kesit çarpanı " + f(c_, 2) : "") + "."] });
      }
    }
    if (!out.length) out.push({ not: "Bu elemanın uç düğümleri sonuçta yok." });
    return out;
  }
  const OZET_ADI = { As_ust_cm2: ["Üst donatı A_s", "cm²"], As_alt_cm2: ["Alt donatı A_s", "cm²"], oneri_ust: ["Üst donatı önerisi", ""], oneri_alt: ["Alt donatı önerisi", ""],
    etriye: ["Etriye", ""], Md_mesnet: ["M_d (mesnet)", "kN·m"], Md_aciklik: ["M_d (açıklık)", "kN·m"], Vd: ["V_d", "kN"], d_m: ["Faydalı yükseklik d", "m"],
    rho: ["Donatı oranı ρ", ""], As_toplam_cm2: ["Boyuna donatı A_s", "cm²"], N_max_kN: ["N_d (en büyük)", "kN"], N_sinir_TBDY_kN: ["TBDY N sınırı", "kN"],
    sinif: ["Kesit sınıfı", ""], Mn_kNm: ["M_n", "kN·m"], Pn_kN: ["P_n", "kN"], Vn_kN: ["V_n", "kN"], b: ["b", "m"], h: ["h", "m"], oneri: ["Öneri", ""],
    K: ["K (güçlü / zayıf)", ""], Tc_kN: ["T_c = T_n/Ω (çekme)", "kN"], Pc_kN: ["P_c = P_n/Ω (basınç)", "kN"], narinlik_basinc: ["KL/i (basınç)", ""], narinlik_cekme: ["L/i (çekme)", ""],
    yalniz_cekme: ["Yalnız çekme", ""], L_m: ["L", "m"], N_kN: ["N (belirleyen)", "kN"], kontrol: ["Kontrol", ""], profil: ["Profil", ""], yontem: ["Yöntem", ""] };
  function tasarimBolumleri(c, t, ham) {
    if (!c.veri || !c.veri.durumlar) return [onceCozun("Tasarım kontrolleri")];
    if (!t) return [{ not: "Bu çözümde bu eleman için tasarım kontrolü yok (tasarım modülü yüklenmemiş ya da eleman türü kapsam dışı)." }];
    ham.dc = t.dc;
    const out = [{ baslik: "Özet", satirlar: [satir("Talep/kapasite D/C", f(+t.dc, 3)), satir("Durum", t.durum || "—"),
      satir("Belirleyen", t.belirleyen ? (t.belirleyen.kontrol || "—") + (t.belirleyen.kombinasyon ? " · " + t.belirleyen.kombinasyon : "") : "—"),
      satir("Yöntem", t.sistem === "celik" ? ((c.veri.tasarim.yontem || {}).celik || "çelik") : ((c.veri.tasarim.yontem || {}).betonarme || "betonarme"))], dc: +t.dc }];
    if (Array.isArray(t.kontroller) && t.kontroller.length) {
      out.push({ baslik: "Kontroller (" + t.kontroller.length + ")", kontroller: t.kontroller.map(function (k) {
        return { ad: k.ad, talep: fa(+k.talep), kapasite: fa(+k.kapasite), birim: k.birim || "", dc: +k.dc, saglandi: k.saglandi !== false,
          kombinasyon: k.kombinasyon || "", kaynak: k.kaynak || "" };
      }) });
    }
    if (t.ozet) {
      const s = [];
      Object.keys(t.ozet).forEach(function (a) {
        const v = t.ozet[a], ad = OZET_ADI[a] || [a, ""];
        if (v == null) return;
        const ogeMetin = function (x) { return typeof x === "number" ? fa(x) : typeof x === "boolean" ? evet(x) : String(x); };
        if (Array.isArray(v)) { if (v.length && v.every(function (x) { return x == null || typeof x !== "object"; })) s.push(satir(ad[0], v.map(ogeMetin).join(" / "), ad[1])); return; }
        if (typeof v === "object") return;     // iç içe ayrıntı nesneleri (tasarım sekmesi tabloda gösterir)
        s.push(satir(ad[0], ogeMetin(v), ad[1]));
      });
      if (s.length) out.push({ baslik: "Donatı ve kapasite özeti", satirlar: s });
    }
    return out;
  }
  function etriyeAgirlik(et, b, h, pas, L) {
    const m = /Φ\s*(\d+)\s*\/\s*(\d+)/.exec(String(et || ""));
    if (!m || !(b > 0) || !(h > 0) || !(L > 0)) return null;
    const fi = +m[1] / 1000, s = +m[2] / 100, c = pas != null ? +pas : 0.03;
    const adet = Math.ceil(L / s) + 1, boy_ = 2 * ((b - 2 * c) + (h - 2 * c)) + 2 * 10 * fi;
    return { adet: adet, kg: adet * boy_ * Math.PI * fi * fi / 4 * CELIK_YOGUNLUK };
  }
  function cubukMetraj(c, tur, k, ks, ml, L, t, ham) {
    if (!ks || !L) return [{ not: "Metraj için kesit ve boy gerekli." }];
    const celik = (ml && (ml.tur === "celik" || ml.Fy != null)) || ks.tip === "profil";
    const out = [], s = [];
    if (celik) {
      const kgm = ks.A * CELIK_YOGUNLUK, kg = kgm * L;
      const U = ks.tip === "profil" && ks.b && ks.h ? 2 * ks.h + 4 * ks.b : (ks.b && ks.h ? 2 * (ks.b + ks.h) : null);
      s.push(satir("Birim ağırlık", f(kgm, 2), "kg/m"), satir("Çelik", f(kg, 1), "kg"));
      if (U) s.push(satir("Boya alanı (yaklaşık)", f(U * L, 2), "m²"));
      ham.metraj = { celik_kg: kg, boya_m2: U ? U * L : null };
      out.push({ baslik: "Çelik", satirlar: s, notlar: ["Ağırlık A·7850 kg/m³; boya alanı dış çevreden (yuvarlatma ve gövde kalınlığı ihmal)."] });
    } else {
      let b = ks.b, h = ks.h;
      if (tur === "kolon" && k.bX != null) { b = k.bX; h = k.bY; }
      const V = ks.A * L;
      const kalip = tur === "kolon" ? 2 * (b + h) * L : (b + 2 * h) * L;
      s.push(satir("Beton", f(V, 3), "m³"), satir("Kalıp", f(kalip, 2), "m²"));
      const met = { beton_m3: V, kalip_m2: kalip };
      if (t && t.ozet) {
        const As = t.ozet.As_toplam_cm2 != null ? +t.ozet.As_toplam_cm2 : ((+t.ozet.As_ust_cm2 || 0) + (+t.ozet.As_alt_cm2 || 0));
        if (As > 0) { met.boyuna_kg = As * 1e-4 * L * CELIK_YOGUNLUK; s.push(satir("Boyuna donatı (hesap A_s)", f(met.boyuna_kg, 1), "kg")); }
        const et = etriyeAgirlik(t.ozet.etriye, b, h, ks.pas, L);
        if (et) { met.etriye_kg = et.kg; s.push(satir("Etriye (" + t.ozet.etriye + ", " + et.adet + " adet)", f(et.kg, 1), "kg")); }
      }
      ham.metraj = met;
      out.push({ baslik: "Betonarme", satirlar: s, notlar: ["Brüt aks boyu üzerinden; " + (tur === "kolon" ? "kalıp dört yüz" : "kalıp alt + iki yan yüz, döşeme kesişimi düşülmedi") + ". Donatı tasarımdaki gerekli A_s ile (bindirme ve kanca payı yok)."] });
    }
    return out;
  }
  /** Yük akışı şemasındaki düğüm kimliği (veri.akis.sankey): D{no}, K{no}, S{no}/k{kat}, T-{aks}; genel model P{panel}, Ç{çubuk}. */
  function sankeyKimligi(c, tur, no, k) {
    if (tur === "cubuk") return "Ç" + no;
    const cno = genelCubukNo(c, tur, no);          // karma model: genel çözümde aks–kat kolon/kiriş çubuk olarak akar
    if (cno != null) return "Ç" + cno;
    if (tur === "panel") return "P" + no;
    if (tur === "kiris") return "K" + no;
    if (tur === "doseme") return "D" + no;
    if (tur === "kolon") return "S" + no + "/k" + (k && k.kat != null ? k.kat : "");
    if (tur === "temel") return k && k.aks ? "T-" + k.aks.join("") : null;
    return null;
  }
  function sankeyAdi(id) {
    let m = /^D(\d+)$/.exec(id); if (m) return "Döşeme " + m[1];
    m = /^K(\d+)$/.exec(id); if (m) return "Kiriş " + m[1];
    m = /^S(\d+)\/k(\d+)$/.exec(id); if (m) return "Kolon " + m[1] + " (kat " + m[2] + ")";
    m = /^T-(.+)$/.exec(id); if (m) return "Temel " + m[1];
    m = /^P(\d+)$/.exec(id); if (m) return "Panel " + m[1];
    m = /^Ç(\d+)$/.exec(id); if (m) return "Çubuk " + m[1];
    if (id === "Z" || /^Z/.test(id)) return "Zemin";
    return id;
  }
  function yukYoluBolumleri(c, id, ham) {
    if (!c.veri || !c.veri.akis) return [onceCozun("Yük yolu")];
    if (!id) return [{ not: "Bu eleman türü için yük akışı şeması yok (eleman yükü doğrudan sonlu eleman çözümünden okunur)." }];
    const sk = c.veri.akis.sankey || [];
    const grup = function (liste, anah) {
      const m = new Map();
      liste.forEach(function (s) { const a = s[anah]; if (!m.has(a)) m.set(a, { ad: a, G: 0, Q: 0, S: 0, diger: 0 }); const r_ = m.get(a); if (r_[s.durum] != null) r_[s.durum] += +s.kN; else r_.diger += +s.kN; });
      return Array.from(m.values());
    };
    const gelen = grup(sk.filter(function (s) { return s.hedef === id; }), "kaynak"), giden = grup(sk.filter(function (s) { return s.kaynak === id; }), "hedef");
    if (!gelen.length && !giden.length) return [{ not: "Yük akışı şemasında bu eleman yok." }];
    const top = function (l, a) { return l.reduce(function (s, r_) { return s + r_[a]; }, 0); };
    ham.yol = { gelenG: top(gelen, "G"), gelenQ: top(gelen, "Q"), gidenG: top(giden, "G"), gidenQ: top(giden, "Q") };
    const out = [];
    out.push({ baslik: "Akış şeması (G + Q, kN)", svg: akisSvg(gelen, id, giden) });
    const sat = gelen.map(function (r_) { return ["← gelen", sankeyAdi(r_.ad), f(r_.G, 2), f(r_.Q, 2)]; })
      .concat(giden.map(function (r_) { return ["→ giden", sankeyAdi(r_.ad), f(r_.G, 2), f(r_.Q, 2)]; }));
    sat.push(["Σ gelen", "", f(ham.yol.gelenG, 2), f(ham.yol.gelenQ, 2)], ["Σ giden", "", f(ham.yol.gidenG, 2), f(ham.yol.gidenQ, 2)]);
    out.push({ baslik: "Aktarılan yükler (kN)", tablo: { basliklar: ["Yön", "Eleman", "G", "Q"], satirlar: sat } });
    const fark = ham.yol.gidenG - ham.yol.gelenG;
    if (gelen.length && giden.length && Math.abs(fark) > 0.01) out.push({ not: "Giden − gelen (G) = " + f(fark, 2) + " kN: elemanın kendi yükü (öz ağırlık, duvar, ek yük) ve sürekliliğin yeniden dağıttığı pay." });
    return out;
  }

  // ---- düğüm / mesnet
  function dugumModeli(c, tur, no, sec) {
    const ham = { tur: tur, no: no };
    const d = c.dugum.get(+no);
    const g = c.geo ? c.geo.dugumler.find(function (x) { return String(x.no) === String(no) || x.anahtar === String(no); }) : null;
    if (!d && !g) throw new Error("Düğüm " + no + " modelde yok.");
    const P = d ? [d.X, d.Y, d.Z] : g.P;
    const adres = g ? g.etiket : (d && d.adres) || "";
    const mesnet = mesnetBul(c, no);
    const turAdi = tur === "mesnet" || mesnet ? "Mesnet" : "Düğüm";
    const m = { tur: tur, no: no, turAdi: turAdi, baslik: turAdi + " " + no, adres: adres, sekmeler: [], ham: ham };
    ham.P = P;
    const geoB = [{ baslik: "Konum", satirlar: [satir("Aks adresi", adres || "—"), d && d.adres && d.adres !== adres ? satir("Motor adresi", d.adres) : null,
      satir("X", f(P[0], 3), "m"), satir("Y", f(P[1], 3), "m"), satir("Z (kot)", f(P[2], 3), "m"), d && d.kat != null ? satir("Kat", String(d.kat)) : null,
      g && g.tur === "bolme" ? satir("Bölme oranı t", f(g.oran, 3)) : null].filter(Boolean) }];
    const bagli = [];
    if (c.ag) (c.ag.elemanlar || []).forEach(function (e) { if (e.dugumler.indexOf(+no) >= 0) bagli.push((TUR_ADI[e.tur] || CUBUK_TUR_ADI[e.tur] || "Eleman") + " " + e.kaynak_no + " (e" + e.no + (e.adres ? ", " + e.adres : "") + ")"); });
    else if (c.geo && g) c.geo.cubuklar.forEach(function (x) { if (x.i === g.anahtar || x.j === g.anahtar) bagli.push(x.etiket); });
    if (bagli.length) geoB.push({ baslik: "Bağlı çubuklar (" + bagli.length + ")", satirlar: bagli.map(function (b, i) { return satir(String(i + 1), b); }) });
    m.sekmeler.push({ id: "geometri", ad: SEKME_ADI.geometri, bolumler: geoB });
    const bagB = [{ baslik: "Mesnet ve diyafram", satirlar: [satir("Mesnet", mesnet || "yok (serbest düğüm)"), d && d.efendi != null ? satir("Rijit diyafram efendi düğümü", evet(!!d.efendi)) : null].filter(Boolean) }];
    m.sekmeler.push({ id: "baglanti", ad: SEKME_ADI.baglanti, bolumler: bagB });
    // düğüm yükleri
    const yk = (c.bina.ek_yukler || []).filter(function (y) {
      if (y.tur !== "dugum") return false;
      if (y.dugum != null) return String(y.dugum.dugum != null ? y.dugum.dugum : y.dugum) === String(no);
      return d && d.aks && y.aks && String(y.aks) === String(d.aks) && +y.kat === +d.kat;
    });
    m.sekmeler.push({ id: "yukler", ad: SEKME_ADI.yukler, bolumler: yk.length ? [{ baslik: "Düğüm yükleri", tablo: { basliklar: ["Durum", "FX", "FY", "FZ (kN)", "MX", "MY", "MZ (kN·m)"],
      satirlar: yk.map(function (y) { return [y.durum || "—", f(+y.FX || 0, 2), f(+y.FY || 0, 2), f(+y.FZ || 0, 2), f(+y.MX || 0, 2), f(+y.MY || 0, 2), f(+y.MZ || 0, 2)]; }) } }] : [{ not: "Bu düğüme tanımlı tekil yük yok." }] });
    const durumlar = durumListesi(c.veri).filter(function (x) { return x.tur !== "zarf"; });
    m.durumlar = durumlar; m.durum = null;
    if (c.veri && c.veri.durumlar) {
      const sat = [], tsat = [];
      durumlar.forEach(function (x) {
        const K = kisa(c.veri, x.ad);
        if (!K) return;
        const u = (K.dugumler || []).find(function (q) { return +q.no === +no; });
        if (u) sat.push([x.ad, f(u.uX * 1000, 3), f(u.uY * 1000, 3), f(u.uZ * 1000, 3), f(u.rX * 1000, 4), f(u.rY * 1000, 4), f(u.rZ * 1000, 4)]);
        const t = (K.tepkiler || []).find(function (q) { return +q.dugum === +no; });
        if (t) { tsat.push([x.ad, f(t.FX, 2), f(t.FY, 2), f(t.FZ, 2), f(t.MX, 2), f(t.MY, 2), f(t.MZ, 2)]); if (!ham.tepki) ham.tepki = {}; ham.tepki[x.ad] = t; }
      });
      if (tsat.length) m.sekmeler.push({ id: "tepki", ad: SEKME_ADI.tepki, bolumler: [{ baslik: "Tepkiler (bina koordinatı)", tablo: { basliklar: ["Durum", "FX (kN)", "FY (kN)", "FZ (kN)", "MX", "MY", "MZ (kN·m)"], satirlar: tsat } }] });
      m.sekmeler.push({ id: "yer", ad: SEKME_ADI.yer, bolumler: sat.length ? [{ baslik: "Yer değiştirmeler (bina koordinatı)", tablo: { basliklar: ["Durum", "uX (mm)", "uY (mm)", "uZ (mm)", "rX (mrad)", "rY (mrad)", "rZ (mrad)"], satirlar: sat } }] : [{ not: "Bu düğüm çözüm ağında yok." }] });
    } else m.sekmeler.push({ id: "yer", ad: SEKME_ADI.yer, bolumler: [onceCozun("Yer değiştirmeler ve mesnet tepkileri")] });
    if (tur === "mesnet" || mesnet) {   // mesnette tepkiler sekmesi Geometri'den hemen sonra
      const i = m.sekmeler.findIndex(function (s) { return s.id === "tepki"; });
      if (i > 1) m.sekmeler.splice(1, 0, m.sekmeler.splice(i, 1)[0]);
    }
    m.ozet = [{ ad: "Konum", deger: "(" + f(P[0], 2) + "; " + f(P[1], 2) + "; " + f(P[2], 2) + ")" }].concat(mesnet ? [{ ad: "Mesnet", deger: mesnet }] : []);
    m.alt = m.ozet.map(function (o) { return o.deger; }).join(" · ");
    return m;
  }

  // ---- döşeme / panel
  function panelModeli(c, tur, no, sec) {
    const ham = { tur: tur, no: no };
    const kayit = bul(tur === "doseme" ? c.bina.dosemeler : c.bina.paneller, no);
    const norm = tur === "doseme" ? bul(c.nb.dosemeler, no) : null;
    if (!kayit && !norm) throw new Error(TUR_ADI[tur] + " " + no + " modelde yok.");
    const k = Object.assign({}, kayit || {}, norm || {});
    const yk = tur === "doseme" && c.veri && c.veri.yukler ? (c.veri.yukler.dosemeler || []).find(function (x) { return String(x.no) === String(no); }) : null;
    const gp = c.geo ? c.geo.paneller.find(function (x) { return x.anahtar === tur + ":" + no; }) : null;
    const m = { tur: tur, no: no, turAdi: TUR_ADI[tur], baslik: TUR_ADI[tur] + " " + no, adres: k.adres || "", sekmeler: [], ham: ham };
    const geoB = [];
    let alanS = null;
    if (gp && c.O) { try { alanS = c.O.alan(gp.kose); } catch (e) { alanS = null; } }
    const s = [];
    if (tur === "doseme" && Array.isArray(k.kose)) s.push(satir("Köşe aksları", k.kose.map(function (q) { return q.join(""); }).join(" – ") + " / kat " + k.kat));
    if (yk) s.push(satir("Kısa kenar l_k", f(yk.lx, 3), "m"), satir("Uzun kenar l_u", f(yk.ly, 3), "m"), satir("m = l_u / l_k", f(yk.m, 3)),
      satir("Çalışma", yk.tip === "cift" ? "çift doğrultulu (m ≤ 2)" : "tek doğrultulu"));
    const A = yk ? +yk.alan : (alanS ? alanS.alan : null);
    ham.alan = A;
    if (A != null) s.push(satir("Alan", f(A, 3), "m²"));
    if (alanS) s.push(satir("Çevre", f(alanS.cevre, 3), "m"), satir("Eğim", f(alanS.egim, 2), "°"), satir("Yatay izdüşüm alanı", f(alanS.izdusum, 3), "m²"));
    if (gp) s.push(satir("Kot (ağırlık merkezi)", f(alanS ? alanS.merkez[2] : gp.kose[0][2], 3), "m"));
    geoB.push({ baslik: "Geometri", satirlar: s });
    if (gp) {
      const adlar = (gp.dugumler || []).map(function (an) { const n = geoDugum(c, an); return n ? n.etiket : ""; });
      geoB.push({ baslik: "Köşeler", tablo: { basliklar: ["Köşe", "Adres", "X (m)", "Y (m)", "Z (m)"],
        satirlar: gp.kose.map(function (P, i) { return [String(i + 1), adlar[i] || "", f(P[0], 3), f(P[1], 3), f(P[2], 3)]; }) } });
    }
    m.sekmeler.push({ id: "geometri", ad: SEKME_ADI.geometri, bolumler: geoB });
    const h = tur === "doseme" ? +k.h : +k.kalinlik;
    m.sekmeler.push({ id: "kesit", ad: SEKME_ADI.kesit, bolumler: [{ baslik: "Plak", satirlar: [satir("Kalınlık", h > 0 ? f(h * 100, 1) : "0 (taşıyıcı olmayan kaplama)", h > 0 ? "cm" : ""),
      satir("Tür", tur === "doseme" ? "betonarme döşeme" : (k.tur || "panel")), h > 0 ? satir("Malzeme", "betonarme (γ = 25 kN/m³)") : null].filter(Boolean) }] });
    const yb = [];
    if (yk) {
      yb.push({ baslik: "Alan yükleri", satirlar: [satir("Plak öz ağırlığı", f(yk.g_plak, 2), "kN/m²"), satir("Ek sabit yük (kaplama)", f(yk.g_ek, 2), "kN/m²"),
        satir("Toplam sabit g", f(yk.g, 2), "kN/m²"), satir("Hareketli q", f(yk.q, 2), "kN/m²"), yk.q_kaynak ? satir("q kaynağı", yk.q_kaynak) : null,
        satir("Toplam G / Q", f(yk.G_toplam, 2) + " / " + f(yk.Q_toplam, 2), "kN"), satir("Dağıtım", k.dagitim || "otomatik")].filter(Boolean) });
      ham.yuk = { G: yk.G_toplam, Q: yk.Q_toplam };
    } else if (tur === "panel" && c.veri && c.veri.yukler && (c.veri.yukler.paneller || []).some(function (x) { return String(x.no) === String(no); })) {
      // genel model çözümü: panelin yüzey yükleri, toplamları ve taşıyıcı kenar payları (veri.yukler.paneller)
      const yp = c.veri.yukler.paneller.find(function (x) { return String(x.no) === String(no); });
      yb.push({ baslik: "Panel yükleri (çözüm)", satirlar: [satir("Sabit g", f(+yp.g || 0, 2), "kN/m²"), satir("Hareketli q", f(+yp.q || 0, 2), "kN/m²"), satir("Kar s", f(+yp.s || 0, 2), "kN/m²"),
        satir("Alan", f(+yp.alan || 0, 3), "m²"), satir("Eğim", f(+yp.egim || 0, 2), "°"), satir("Toplam G / Q / S", f(+yp.G_toplam || 0, 2) + " / " + f(+yp.Q_toplam || 0, 2) + " / " + f(+yp.S_toplam || 0, 2), "kN"),
        satir("Dağıtım", yp.dagitim || "iki"), yp.q_kaynak ? satir("q kaynağı", yp.q_kaynak) : null].filter(Boolean) });
      const kn = (yp.kenarlar || []).filter(function (x) { return x.sekil !== "yok"; });
      if (kn.length) yb.push({ baslik: "Taşıyıcı kenarlara paylar", tablo: { basliklar: ["Kenar", "Çubuk(lar)", "Şekil", "Pay alanı (m²)"],
        satirlar: kn.map(function (x) { return [String(x.kenar), (x.cubuklar || []).map(function (n) { return "Ç" + n; }).join(", "), x.sekil === "ucgen" ? "üçgen" : x.sekil === "trapez" ? "trapez" : x.sekil === "duzgun" ? "düzgün" : (x.sekil || "—"), f(+x.pay || 0, 2)]; }) } });
      ham.yuk = { G: yp.G_toplam, Q: yp.Q_toplam, S: yp.S_toplam };
    } else if (tur === "panel") {
      yb.push({ baslik: "Panel yükleri", satirlar: [satir("Ek sabit g (yüzey)", f(+k.g || 0, 2), "kN/m²"), satir("Hareketli q (izdüşüm)", f(+k.q || 0, 2), "kN/m²"),
        satir("Kar", evet(!!k.kar)), satir("Rüzgâr", k.ruzgar ? JSON.stringify(k.ruzgar.cp) : "yok"), satir("Dağıtım", k.dagitim || "iki")] });
    } else {
      yb.push({ baslik: "Alan yükleri", satirlar: [satir("Kullanım", k.kullanim || "—"), satir("Ek sabit yük", f(+k.g_ek || 0, 2), "kN/m²"),
        satir("Hareketli q", k.q == null ? "kullanım sınıfından" : f(+k.q, 2), k.q == null ? "" : "kN/m²")] });
      yb.push(onceCozun("Kirişlere aktarılan paylar"));
    }
    m.sekmeler.push({ id: "yukler", ad: SEKME_ADI.yukler, bolumler: yb });
    const yol = [];
    if (yk && Array.isArray(yk.paylar) && yk.paylar.length) {
      yol.push({ baslik: "Kirişlere paylar (TS 500 md. 11.4.3)", tablo: { basliklar: ["Kiriş", "Kenar", "Şekil", "Tepe g", "Tepe q (kN/m)", "G (kN)", "Q (kN)"],
        satirlar: yk.paylar.map(function (p_) { return ["K" + p_.kiris_no, (p_.kenar_ad || "") + " (" + (p_.kenar === "kisa" ? "kısa" : "uzun") + ")",
          p_.sekil === "ucgen" ? "üçgen" : p_.sekil === "trapez" ? "trapez" : p_.sekil === "duzgun" ? "düzgün" : "—", f(p_.tepe_g, 2), f(p_.tepe_q, 2), f(p_.toplam_G, 2), f(p_.toplam_Q, 2)]; }) } });
      ham.paylarG = yk.paylar.reduce(function (s_, p_) { return s_ + (+p_.toplam_G || 0); }, 0);
    }
    yukYoluBolumleri(c, tur === "doseme" ? "D" + no : "P" + no, ham).forEach(function (b) { if (!b.cozum || !yol.length) yol.push(b); });
    m.sekmeler.push({ id: "yol", ad: SEKME_ADI.yol, bolumler: yol });
    if (h > 0 && A != null) {
      ham.metraj = { beton_m3: h * A, kalip_m2: A };
      m.sekmeler.push({ id: "metraj", ad: SEKME_ADI.metraj, bolumler: [{ baslik: "Betonarme", satirlar: [satir("Beton", f(h * A, 3), "m³"), satir("Kalıp", f(A, 2), "m²")],
        notlar: ["Brüt plak alanı (kiriş kesişimleri düşülmedi)."] }] });
    } else if (A != null) {
      ham.metraj = { kaplama_m2: A };
      m.sekmeler.push({ id: "metraj", ad: SEKME_ADI.metraj, bolumler: [{ baslik: "Kaplama", satirlar: [satir("Kaplama alanı", f(A, 2), "m²")] }] });
    }
    m.ozet = [h > 0 ? { ad: "h", deger: f(h * 100, 0) + " cm" } : null, A != null ? { ad: "A", deger: f(A, 2) + " m²" } : null].filter(Boolean);
    m.alt = m.ozet.map(function (o) { return o.ad + " " + o.deger; }).join(" · ");
    return m;
  }

  // ---- temel
  function temelModeli(c, kolonNo, sec) {
    const ham = { tur: "temel", no: kolonNo };
    const t = temelKaydi(c, kolonNo);
    const tb = c.nb.temeller || c.bina.temeller || {};
    const kolon = bul(c.bina.kolonlar, kolonNo) || {};
    const aks = (t && t.aks) || kolon.aks || null;
    if (!t && !aks) throw new Error("Temel (kolon " + kolonNo + ") modelde yok.");
    const B = t && t.B != null ? +t.B : (tb.varsayilan || {}).B, L = t && t.L != null ? +t.L : (tb.varsayilan || {}).L;
    const h = t && t.h != null ? +t.h : (tb.varsayilan || {}).h;
    const ad = "T-" + (aks ? aks.join("") : kolonNo);
    const m = { tur: "temel", no: kolonNo, turAdi: "Temel", baslik: "Temel " + (aks ? aks.join("") : kolonNo), adres: ad, sekmeler: [], ham: ham };
    m.sekmeler.push({ id: "geometri", ad: SEKME_ADI.geometri, bolumler: [{ baslik: "Tekil temel", satirlar: [satir("Aks", aks ? aks.join("-") : "—"), satir("Kolon", String(kolonNo)),
      satir("B × L", f(B, 2) + " × " + f(L, 2), "m"), satir("Yükseklik h", f(h, 2), "m"), satir("Taban alanı", f(B * L, 3), "m²"), satir("Tip", tb.tip || "tekil")] }] });
    const z = tb.zemin || {};
    m.sekmeler.push({ id: "zemin", ad: SEKME_ADI.zemin, bolumler: [{ baslik: "Zemin ve mesnet", satirlar: [satir("Emniyet gerilmesi q_em", f(+z.q_em, 0), "kN/m²"),
      satir("Yatak katsayısı k₀", f(+z.k0, 0), "kN/m³"), satir("Mesnet modeli", tb.mesnet || "—")] }] });
    if (t && t.N_G != null) {
      m.sekmeler.push({ id: "yukler", ad: SEKME_ADI.yukler, bolumler: [{ baslik: "Temele gelen (servis)", satirlar: [satir("N (G / Q)", f(t.N_G, 2) + " / " + f(t.N_Q, 2), "kN"),
        satir("Temel öz ağırlığı", f(t.N_temel, 2), "kN"), satir("N servis", f(t.N_servis, 2), "kN"), satir("MX / MY", f(t.MX, 2) + " / " + f(t.MY, 2), "kN·m")] }] });
      m.sekmeler.push({ id: "tasarim", ad: SEKME_ADI.tasarim, bolumler: [{ baslik: "Taban basıncı (TS 500 emniyet)", satirlar: [satir("σ_max", f(t.sigma_max, 2), "kN/m²"),
        satir("σ_min", f(t.sigma_min, 2), "kN/m²"), satir("Dışmerkezlik e_X / e_Y", f(t.e_X, 3) + " / " + f(t.e_Y, 3), "m"), satir("Çekirdek içinde (e ≤ B/6)", evet(!!t.cekirdek_icinde)),
        satir("D/C = σ_max / q_em", f(t.DC, 3))], dc: +t.DC }] });
      ham.dc = t.DC; ham.N_servis = t.N_servis;
    } else m.sekmeler.push({ id: "yukler", ad: SEKME_ADI.yukler, bolumler: [onceCozun("Temel yükleri ve taban basıncı")] });
    if (B && L && h) {
      ham.metraj = { beton_m3: B * L * h, kalip_m2: 2 * (B + L) * h };
      m.sekmeler.push({ id: "metraj", ad: SEKME_ADI.metraj, bolumler: [{ baslik: "Betonarme", satirlar: [satir("Beton", f(B * L * h, 3), "m³"), satir("Kalıp (yan yüzler)", f(2 * (B + L) * h, 2), "m²")] }] });
    }
    m.sekmeler.push({ id: "yol", ad: SEKME_ADI.yol, bolumler: yukYoluBolumleri(c, aks ? "T-" + aks.join("") : null, ham) });
    m.ozet = [{ ad: "B×L", deger: f(B, 2) + "×" + f(L, 2) + " m" }].concat(t && t.DC != null ? [{ ad: "D/C", deger: f(+t.DC, 2), dc: +t.DC }] : []);
    m.alt = m.ozet.map(function (o) { return o.ad + " " + o.deger; }).join(" · ");
    return m;
  }

  // ---- mütemadi temel kirişi, radye ve kirişli radyenin aks kirişi (veri.temel; temel.py ızgarası)
  /**
   * hedef = {tur: "temel", alt: "surekli" | "radye-kirisi" | "radye", no (sahne sırası, 1'den), aks?, yon? ("x": X doğrultulu, y aksı
   * üzerinde; "y": Y doğrultulu, x aksı üzerinde)}. Çözümsüz: bina temeller tanımından geometri; çözümde hat, düğüm basınçları ve tasarım.
   */
  function yayiliTemelModeli(c, hedef, sec) {
    const alt = hedef.alt, tb = c.nb.temeller || c.bina.temeller || {}, t = c.veri && c.veri.temel && c.veri.temel.tip ? c.veri.temel : null;
    const ham = { tur: "temel", alt: alt, no: hedef.no };
    const zm = tb.zemin || (c.bina.temeller || {}).zemin || {};
    const dug = new Map(); ((t && t.dugumler) || []).forEach(function (d) { dug.set(+d.no, d); });
    const durumAdi = t ? (t.belirleyen_servis || "G+Q") + " (servis)" : "";
    if (alt === "radye") {
      const r = tb.radye || {}, k = r.kiris && typeof r.kiris === "object" ? r.kiris : null, mp = (t && t.model && t.model.plak) || null;
      const m = { tur: "temel", no: hedef.no, turAdi: "Radye", baslik: "Radye temel", adres: k ? "kirişli radye" : "kirişsiz radye", sekmeler: [], ham: ham };
      const alan = mp ? +mp.alan : null, h = r.h != null ? +r.h : (mp ? +mp.h : null);
      m.sekmeler.push({ id: "geometri", ad: SEKME_ADI.geometri, bolumler: [{ baslik: "Radye plak", satirlar: [satir("Kalınlık h", f(h, 2), "m"), satir("Taşma", f(+r.tasma, 2), "m"),
        satir("Izgara aralığı", f(+r.ag, 2), "m"), mp ? satir("Plak sınırları X", f(+mp.X0, 2) + " … " + f(+mp.X1, 2), "m") : null, mp ? satir("Plak sınırları Y", f(+mp.Y0, 2) + " … " + f(+mp.Y1, 2), "m") : null,
        alan != null ? satir("Taban alanı", f(alan, 2), "m²") : null, satir("Aks kirişleri", k ? f(+k.b, 2) + " × " + f(+k.h, 2) + " m" : "yok")].filter(Boolean) }] });
      m.sekmeler.push({ id: "zemin", ad: SEKME_ADI.zemin, bolumler: [{ baslik: "Zemin" + (durumAdi ? " — " + durumAdi : ""), satirlar: [satir("Emniyet gerilmesi q_em", f(+zm.q_em, 0), "kN/m²"),
        satir("Yatak katsayısı k₀", f(+((t && t.model && t.model.k0) || zm.k0), 0), "kN/m³")].concat(t ? [satir("Taban basıncı σ_maks", f(+t.p_maks, 2), "kN/m²"), satir("Taban basıncı σ_min", f(+t.p_min, 2), "kN/m²"),
        satir("Oturma maks / min", f(+t.oturma_maks_mm, 2) + " / " + f(+t.oturma_min_mm, 2), "mm"), satir("Farklı oturma", String(t.farkli_oturma_metin || "—")), satir("Zemin D/C (σ_maks / q_em)", f(+t.DC_zemin, 3))] : []),
        dc: t ? +t.DC_zemin : null }].concat(t ? [] : [onceCozun("Taban basıncı ve oturma")]) });
      if (t) {
        const ser = (t.tasarim || []).filter(function (x) { return x.tur === "radye-serit"; });
        const kir = (t.tasarim || []).filter(function (x) { return x.tur === "temel-kirisi"; });
        const tbl = [];
        if (ser.length) tbl.push({ baslik: "Radye donatısı (m başına)", tablo: { basliklar: ["Doğrultu", "M alt / üst (kN·m/m)", "A_s alt / üst (cm²/m)", "Öneri alt / üst", "D/C"], dcSutun: 4,
          satirlar: ser.map(function (x) { return [x.yon === "y" ? "Y" : "X", f(+x.M_alt_m, 1) + " / " + f(+x.M_ust_m, 1), f(+x.As_alt_cm2_m, 2) + " / " + f(+x.As_ust_cm2_m, 2), (x.oneri_alt || "—") + " / " + (x.oneri_ust || "—"), f(+x.dc, 2)]; }) } });
        if (kir.length) tbl.push({ baslik: "Aks kirişleri", tablo: { basliklar: ["Aks", "b × h (m)", "M_d alt / üst", "V_d", "D/C"], dcSutun: 4,
          satirlar: kir.map(function (x) { return [String(x.hat), f(+x.b, 2) + " × " + f(+x.h, 2), f(+x.Md_alt, 1) + " / " + f(+x.Md_ust, 1), f(+x.Vd, 1), f(+x.dc, 2)]; }) } });
        const kon = (t.zemin_kontrolleri || []).concat(t.kontroller || []);
        if (kon.length) tbl.push({ baslik: "Zemin ve boyut kontrolleri", kontroller: kon.map(temelKontrolu) });
        if (t.en_buyuk_dc != null) tbl.unshift({ baslik: "Özet", satirlar: [satir("Temel D/C maks (zemin + kesit + zımbalama)", f(+t.en_buyuk_dc, 3))], dc: +t.en_buyuk_dc });
        m.sekmeler.push({ id: "tasarim", ad: SEKME_ADI.tasarim, bolumler: tbl });
        ham.dc = t.en_buyuk_dc; ham.p_maks = t.p_maks;
      }
      if (alan != null && h) {
        ham.metraj = { beton_m3: alan * h };
        m.sekmeler.push({ id: "metraj", ad: SEKME_ADI.metraj, bolumler: [{ baslik: "Betonarme", satirlar: [satir("Plak betonu", f(alan * h, 2), "m³")], notlar: k ? ["Aks kirişlerinin plak üstündeki hacmi ayrıca eklenir."] : [] }] });
      }
      m.ozet = [h != null ? { ad: "h", deger: f(h, 2) + " m" } : null, t ? { ad: "σ_maks", deger: f(+t.p_maks, 1) + " kN/m²" } : null, t && t.en_buyuk_dc != null ? { ad: "D/C", deger: f(+t.en_buyuk_dc, 2), dc: +t.en_buyuk_dc } : null].filter(Boolean);
      m.alt = m.ozet.map(function (o_) { return o_.ad + " " + o_.deger; }).join(" · ");
      return m;
    }
    // mütemadi temel kirişi ya da kirişli radyenin aks kirişi: aks çizgisi (hat)
    const hat = t ? (t.hatlar || []).find(function (x) { return hedef.aks != null && String(x.ad) === String(hedef.aks) && (!hedef.yon || x.yon === hedef.yon); }) : null;
    const tas = t ? (t.tasarim || []).find(function (x) { return x.tur === "temel-kirisi" && hedef.aks != null && String(x.hat) === String(hedef.aks) && (!hedef.yon || !x.yon || x.yon === hedef.yon); }) : null;
    const ks = alt === "surekli" ? (tb.surekli || {}) : ((tb.radye || {}).kiris || {});
    const yonAdi = hedef.yon === "y" ? "Y doğrultusunda" : hedef.yon === "x" ? "X doğrultusunda" : "—";
    const ad = "TK-" + (hedef.aks != null ? hedef.aks : hedef.no);
    const m = { tur: "temel", no: hedef.no, turAdi: alt === "surekli" ? "Temel kirişi" : "Radye kirişi", baslik: (alt === "surekli" ? "Mütemadi temel kirişi " : "Radye aks kirişi ") + (hedef.aks != null ? hedef.aks : hedef.no),
      adres: ad, sekmeler: [], ham: ham };
    const geoS = [satir("Aks", hedef.aks != null ? String(hedef.aks) : "—"), satir("Doğrultu", yonAdi)];
    if (hat) geoS.push(satir("Boy (taşmalar dahil)", f(+hat.L, 2), "m"), satir("Başlangıç / bitiş", f(+hat.bas, 2) + " / " + f(+hat.son, 2), "m"));
    if (alt === "surekli") geoS.push(satir("Tabla B × h_tabla", f(+ks.B, 2) + " × " + f(+ks.h_tabla, 2), "m"), satir("Gövde b × h (toplam)", f(+ks.b_govde, 2) + " × " + f(+ks.h_govde, 2), "m"), satir("Uç taşma", f(+ks.tasma, 2), "m"));
    else geoS.push(satir("Kiriş b × h (plak dahil)", f(+ks.b, 2) + " × " + f(+ks.h, 2), "m"));
    const geoB = [{ baslik: "Geometri", satirlar: geoS }];
    if (hat && Array.isArray(hat.kolonlar) && hat.kolonlar.length) {
      const kl = ((t && t.kolonlar) || []);
      geoB.push({ baslik: "Oturan kolonlar (" + hat.kolonlar.length + ")", satirlar: hat.kolonlar.map(function (kn) { const x = kl.find(function (q) { return String(q.kolon_no) === String(kn); }); return satir("Kolon " + kn, x ? (x.adres || "") + (x.N_servis != null ? " · N = " + f(+x.N_servis, 1) + " kN" : "") : ""); }) });
    }
    m.sekmeler.push({ id: "geometri", ad: SEKME_ADI.geometri, bolumler: geoB });
    if (hat && dug.size) {
      const dl = (hat.dugumler || []).map(function (n) { return dug.get(+n); }).filter(Boolean);
      const pv = dl.map(function (d) { return +d.p_kNm2; }), wv = dl.map(function (d) { return +d.w_mm; });
      const pm = pv.length ? Math.max.apply(null, pv) : null, pn = pv.length ? Math.min.apply(null, pv) : null, wm = wv.length ? Math.max.apply(null, wv) : null;
      ham.p_maks = pm;
      m.sekmeler.push({ id: "zemin", ad: SEKME_ADI.zemin, bolumler: [{ baslik: "Zemin — " + durumAdi, satirlar: [satir("Taban basıncı p_maks", f(pm, 2), "kN/m²"), satir("Taban basıncı p_min", f(pn, 2), "kN/m²"),
        satir("Oturma maks", f(wm, 2), "mm"), satir("Emniyet gerilmesi q_em", f(+zm.q_em, 0), "kN/m²"), satir("Zemin D/C (p_maks / q_em)", zm.q_em ? f(pm / +zm.q_em, 3) : "—"),
        satir("Yatak katsayısı k₀", f(+((t.model && t.model.k0) || zm.k0), 0), "kN/m³")], dc: zm.q_em ? pm / +zm.q_em : null, notlar: pn != null && pn < 0 ? ["p < 0: temel zeminden ayrılıyor (Winkler yayı çekme taşımaz)."] : [] }] });
    } else m.sekmeler.push({ id: "zemin", ad: SEKME_ADI.zemin, bolumler: [{ baslik: "Zemin", satirlar: [satir("Emniyet gerilmesi q_em", f(+zm.q_em, 0), "kN/m²"), satir("Yatak katsayısı k₀", f(+zm.k0, 0), "kN/m³")] }, onceCozun("Taban basıncı ve oturma")] });
    if (tas) {
      const tb2 = [{ baslik: "Özet", satirlar: [satir("D/C", f(+tas.dc, 3)), satir("Durum", tas.durum || "—"), satir("b × h", f(+tas.b, 2) + " × " + f(+tas.h, 2), "m"),
        satir("M_d alt / üst", f(+tas.Md_alt, 1) + " / " + f(+tas.Md_ust, 1), "kN·m"), satir("A_s alt / üst", f(+tas.As_alt_cm2, 2) + " / " + f(+tas.As_ust_cm2, 2), "cm²"),
        satir("Donatı önerisi alt / üst", (tas.oneri_alt || "—") + " / " + (tas.oneri_ust || "—")), satir("V_d", f(+tas.Vd, 1), "kN"), tas.etriye ? satir("Etriye", tas.etriye) : null].filter(Boolean), dc: +tas.dc }];
      if (Array.isArray(tas.kontroller) && tas.kontroller.length) tb2.push({ baslik: "Kontroller (" + tas.kontroller.length + ")", kontroller: tas.kontroller.map(temelKontrolu) });
      m.sekmeler.push({ id: "tasarim", ad: SEKME_ADI.tasarim, bolumler: tb2 });
      ham.dc = tas.dc;
    } else if (!t) m.sekmeler.push({ id: "tasarim", ad: SEKME_ADI.tasarim, bolumler: [onceCozun("Temel kirişi tasarımı")] });
    if (hat && alt === "surekli" && ks.B) {
      const A = (+ks.B) * (+ks.h_tabla || 0) + (+ks.b_govde || 0) * Math.max(0, (+ks.h_govde || 0) - (+ks.h_tabla || 0));
      ham.metraj = { beton_m3: A * (+hat.L) };
      m.sekmeler.push({ id: "metraj", ad: SEKME_ADI.metraj, bolumler: [{ baslik: "Betonarme", satirlar: [satir("Kesit alanı (ters T)", f(A, 3), "m²"), satir("Beton", f(A * (+hat.L), 2), "m³")],
        notlar: ["Kesişimlerde ortak hacim bir kez sayılmalıdır (temel modeli düzeltir; burada brüt)."] }] });
    }
    m.ozet = [tas ? { ad: "D/C", deger: f(+tas.dc, 2), dc: +tas.dc } : null, ham.p_maks != null ? { ad: "p_maks", deger: f(ham.p_maks, 1) + " kN/m²" } : null].filter(Boolean);
    m.alt = m.ozet.map(function (o_) { return o_.ad + " " + o_.deger; }).join(" · ");
    return m;
  }
  function temelKontrolu(k) {
    return { ad: k.ad + (k.kosul ? " (koşul)" : ""), talep: fa(+k.talep), kapasite: fa(+k.kapasite), birim: k.birim || "", dc: +k.dc, saglandi: k.saglandi !== false, kombinasyon: k.kombinasyon || "", kaynak: k.kaynak || "" };
  }

  /** Köprü paketi: {sekmeler: {sekmeId: [bölüm]}, sekme_adlari?, uyarilar?} — sekmelere "Motor ayrıntısı" olarak eklenir. */
  function paketBirlestir(m, paket) {
    if (!paket || typeof paket !== "object") return m;
    const sk = paket.sekmeler || {};
    Object.keys(sk).forEach(function (id) {
      const bl = Array.isArray(sk[id]) ? sk[id] : [];
      if (!bl.length) return;
      let s = m.sekmeler.find(function (x) { return x.id === id; });
      if (!s) { s = { id: id, ad: (paket.sekme_adlari && paket.sekme_adlari[id]) || SEKME_ADI[id] || id, bolumler: [] }; m.sekmeler.push(s); }
      s.bolumler = s.bolumler.filter(function (b) { return !b.cozum; });
      bl.forEach(function (b, i) { s.bolumler.push(Object.assign({}, b, { motor: true, baslik: (i === 0 ? "Motor ayrıntısı — " : "") + (b.baslik || "") })); });
    });
    if (Array.isArray(paket.uyarilar) && paket.uyarilar.length) m.uyari = (m.uyari ? m.uyari + " " : "") + paket.uyarilar.join(" ");
    m.paket = true;
    return m;
  }

  // ================================================================= SVG
  function r1(v) { return Math.round(v * 10) / 10; }
  /** Küçük iç kuvvet diyagramı (eleman ekseni yatay). sec.alt verilirse iki tonlu zarf. */
  function diyagramSvg(x, d, ad, sec) {
    sec = sec || {};
    const W = 300, H = 78, sol = 36, sag = 12, ust = 15, alt = 15;
    const L = x[x.length - 1] - x[0] || 1;
    const tum = sec.alt ? d.concat(sec.alt) : d;
    const mx = Math.max(1e-9, Math.max.apply(null, tum.map(Math.abs)));
    const yOrta = ust + (H - ust - alt) / 2, olc = (H - ust - alt) / 2 / mx;
    const isaret = ad === "M" || ad === "My" ? -1 : 1;   // moment çekme tarafına (aşağı pozitif) çizilir
    const X = function (v) { return sol + (v - x[0]) / L * (W - sol - sag); };
    const Yd = function (v) { return yOrta - isaret * v * olc; };
    const yol = function (dd) {
      return "M" + r1(X(x[0])) + "," + r1(yOrta) + " " + dd.map(function (v, i) { return "L" + r1(X(x[i])) + "," + r1(Yd(v)); }).join(" ") + " L" + r1(X(x[x.length - 1])) + "," + r1(yOrta) + "Z";
    };
    const sinif = "bilgi-d bilgi-d" + (ad === "N" || ad === "T" ? "N" : ad === "V" || ad === "Vz" ? "V" : "M");
    let g = '<svg class="bilgi-diyagram" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + kacis((KUVVET_AD[ad] || ad) + " diyagramı") + '">';
    g += '<text class="bilgi-d-ad" x="4" y="' + r1(yOrta) + '">' + kacis(ad) + '</text><text class="bilgi-d-birim" x="4" y="' + r1(yOrta + 12) + '">' + kacis(KUVVET_BIRIM[ad] || "") + "</text>";
    g += '<path class="' + sinif + '" d="' + yol(d) + '"/>';
    if (sec.alt) g += '<path class="' + sinif + ' bilgi-d-alt" d="' + yol(sec.alt) + '"/>';
    g += '<line class="bilgi-d-eksen" x1="' + sol + '" y1="' + r1(yOrta) + '" x2="' + (W - sag) + '" y2="' + r1(yOrta) + '"/>';
    const etiket = function (v, xx) {
      if (Math.abs(v) < mx * 0.02) return "";
      const yy = Yd(v), yuk = yy < yOrta;
      const ty = Math.max(10, Math.min(H - 3, yuk ? yy - 3 : yy + 11));
      return '<text class="bilgi-d-deger" x="' + r1(Math.max(sol + 16, Math.min(W - sag - 16, X(xx)))) + '" y="' + r1(ty) + '" text-anchor="middle">' + kacis(f(v, 1)) + "</text>";
    };
    const ust_ = sec.alt ? sec.alt.map(function (q, i) { return Math.max(q, d[i]); }) : d, alt_ = sec.alt ? sec.alt.map(function (q, i) { return Math.min(q, d[i]); }) : d;
    const eu = ekstremum(x, ust_), ea = ekstremum(x, alt_);
    g += etiket(eu.max, eu.xmax);
    if (Math.abs(ea.min - eu.max) > mx * 0.05 && !(Math.abs(ea.xmin - eu.xmax) < L * 0.12 && Math.sign(ea.min) === Math.sign(eu.max))) g += etiket(ea.min, ea.xmin);
    return g + "</svg>";
  }
  /** Yük yolu şeması: gelenler → eleman → gidenler (bant kalınlığı ∝ G + Q). */
  function akisSvg(gelen, ad, giden) {
    const W = 320, sat = Math.max(gelen.length, giden.length, 1), H = Math.max(64, 18 + sat * 22);
    const top = function (r_) { return r_.G + r_.Q + r_.S + r_.diger; };
    const mx = Math.max(1e-9, Math.max.apply(null, gelen.concat(giden).map(top)));
    const cx = W / 2, cy = H / 2;
    let g = '<svg class="bilgi-akis" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Yük yolu: ' + kacis(ad) + '">';
    const sira = function (l, sol) {
      l.forEach(function (r_, i) {
        const y = l.length === 1 ? cy : 12 + i * (H - 24) / (l.length - 1);
        const x = sol ? 70 : W - 70, w = 1.5 + 7 * top(r_) / mx;
        g += '<path class="bilgi-akis-bant" stroke-width="' + r1(w) + '" d="M' + (sol ? x : cx + 34) + "," + r1(sol ? y : cy) + " C" + r1((x + cx) / 2) + "," + r1(sol ? y : cy) + " " + r1((x + cx) / 2) + "," + r1(sol ? cy : y) + " " + (sol ? cx - 34 : x) + "," + r1(sol ? cy : y) + '"/>';
        g += '<text class="bilgi-akis-et" x="' + (sol ? x - 4 : x + 4) + '" y="' + r1(y + 4) + '" text-anchor="' + (sol ? "end" : "start") + '">' + kacis(r_.ad === "Z" ? "Zemin" : r_.ad) + "</text>";
        g += '<text class="bilgi-akis-kn" x="' + (sol ? x - 4 : x + 4) + '" y="' + r1(y + 15) + '" text-anchor="' + (sol ? "end" : "start") + '">' + kacis(f(top(r_), 1)) + " kN</text>";
      });
    };
    sira(gelen, true); sira(giden, false);
    g += '<rect class="bilgi-akis-kutu" x="' + (cx - 34) + '" y="' + (cy - 12) + '" width="68" height="24" rx="6"/>';
    g += '<text class="bilgi-akis-ad" x="' + cx + '" y="' + (cy + 4) + '" text-anchor="middle">' + kacis(ad) + "</text>";
    return g + "</svg>";
  }

  // ================================================================= TSV, kısa özet
  /** Modelin (ya da tek sekmenin) hesap tablosuna yapıştırılabilir sekmeli metni. */
  function tsv(m, sekmeId) {
    const sat = [[m.baslik, m.adres || ""].join("\t")];
    m.sekmeler.forEach(function (s) {
      if (sekmeId && s.id !== sekmeId) return;
      sat.push("", "[" + s.ad + "]" + (s.secici && m.durum ? "\t" + m.durum : ""));
      s.bolumler.forEach(function (b) {
        if (b.baslik) sat.push(b.baslik);
        if (b.satirlar) b.satirlar.forEach(function (r_) { sat.push(r_.map(duzMetin).join("\t")); });
        if (b.tablo) { sat.push(b.tablo.basliklar.map(duzMetin).join("\t")); b.tablo.satirlar.forEach(function (r_) { sat.push(r_.map(duzMetin).join("\t")); }); }
        if (b.kontroller) {
          sat.push(["Kontrol", "Talep", "Kapasite", "Birim", "D/C", "Sağlandı", "Kombinasyon", "Kaynak"].join("\t"));
          b.kontroller.forEach(function (k) { sat.push([k.ad, k.talep, k.kapasite, k.birim, f(k.dc, 3), evet(k.saglandi), k.kombinasyon, k.kaynak].map(duzMetin).join("\t")); });
        }
        if (b.not) sat.push(duzMetin(b.not));
        (b.notlar || []).forEach(function (n) { sat.push(duzMetin(n)); });
      });
    });
    return sat.join("\n");
  }
  function duzMetin(v) { return String(v == null ? "" : v).replace(/[\t\n]+/g, " ").replace(/−/g, "-"); }
  function ozet(hedef, bina, veri) {
    try { const m = bilgi(hedef, bina, veri); return m.baslik + (m.adres ? " — " + m.adres : "") + (m.alt ? " · " + m.alt : ""); }
    catch (e) { return (TUR_ADI[hedef && hedef.tur] || "Eleman") + " " + (hedef ? hedef.no : ""); }
  }

  // ================================================================= DOM: HTML çizimi
  function bolumHtml(b) {
    let h = '<section class="bilgi-bolum' + (b.motor ? " bilgi-motor" : "") + (b.cozum ? " bilgi-cozum-yok" : "") + '">';
    const ic = [];
    if (b.satirlar) {
      ic.push('<table class="bilgi-anahtar"><tbody>' + b.satirlar.map(function (r_) {
        return "<tr><th scope=\"row\">" + kacis(r_[0]) + "</th><td>" + kacis(r_[1]) + (r_[2] ? ' <span class="bilgi-birim">' + kacis(r_[2]) + "</span>" : "") + "</td></tr>";
      }).join("") + "</tbody></table>");
    }
    if (b.tablo) {
      const dcS = b.tablo.dcSutun;
      ic.push('<div class="bilgi-tablo-kap"><table class="bilgi-tablo"><thead><tr>' + b.tablo.basliklar.map(function (x) { return '<th scope="col">' + kacis(x) + "</th>"; }).join("") +
        "</tr></thead><tbody>" + b.tablo.satirlar.map(function (r_) {
          return "<tr>" + r_.map(function (x, i) {
            let s = "";
            if (i === dcS) { const v = parseFloat(String(x).replace(",", ".").replace("−", "-")); s = ' class="bilgi-dc ' + dcSinif(v) + '"'; }
            if (x === "✗") s = ' class="bilgi-kotu"'; else if (x === "✓") s = ' class="bilgi-iyi"';
            return "<td" + s + ">" + kacis(x) + "</td>";
          }).join("") + "</tr>";
        }).join("") + "</tbody></table></div>");
    }
    if (b.kontroller) {
      ic.push('<ol class="bilgi-kontroller">' + b.kontroller.map(function (k) {
        return '<li class="' + (k.saglandi ? "" : "bilgi-k-red") + '"><div class="bilgi-k-ust"><span class="bilgi-k-ad">' + kacis(k.ad) + '</span><b class="bilgi-dc ' + dcSinif(k.dc) + '">' +
          kacis(f(k.dc, 2)) + (k.saglandi ? ' <span class="bilgi-iyi">✓</span>' : ' <span class="bilgi-kotu">✗</span>') + "</b></div>" +
          '<div class="bilgi-k-alt">' + kacis(k.talep + " / " + k.kapasite + (k.birim ? " " + k.birim : "")) + (k.kombinasyon ? " · " + kacis(k.kombinasyon) : "") + "</div>" +
          (k.kaynak ? '<div class="bilgi-k-kaynak">' + kacis(k.kaynak) + "</div>" : "") + "</li>";
      }).join("") + "</ol>");
    }
    if (b.svg) ic.push('<div class="bilgi-svg">' + b.svg + "</div>");
    if (b.not) ic.push('<p class="bilgi-not">' + kacis(b.not) + "</p>");
    (b.notlar || []).forEach(function (n) { ic.push('<p class="bilgi-not">' + kacis(n) + "</p>"); });
    if (b.dc != null && isFinite(b.dc)) ic.unshift('<div class="bilgi-dc-cubuk ' + dcSinif(b.dc) + '" role="meter" aria-valuemin="0" aria-valuemax="1.5" aria-valuenow="' + b.dc + '" aria-label="D/C ' + f(b.dc, 2) + '"><span style="width:' + Math.min(100, b.dc / 1.5 * 100).toFixed(1) + '%"></span><b>D/C ' + f(b.dc, 2) + "</b></div>");
    if (b.acilir) h += "<details><summary>" + kacis(b.baslik || "") + "</summary>" + ic.join("") + "</details>";
    else h += (b.baslik ? "<h4>" + kacis(b.baslik) + "</h4>" : "") + ic.join("");
    return h + "</section>";
  }
  function dcSinif(v) { return !isFinite(v) ? "" : v > 1 ? "dc-k" : v > 0.9 ? "dc-t" : v > 0.7 ? "dc-s" : "dc-y"; }

  // ---- ikon (araç kutusu ikonlarıyla aynı dil; yoksa yalın)
  function ikon(ad) {
    const A = typeof window !== "undefined" ? window.MatrisArac : null;
    if (A && A.IKON && A.IKON[ad]) return A.ikonSvg(ad, "bilgi-ikon");
    const ic = IKONLAR[ad];
    return ic ? '<svg class="bilgi-ikon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + ic + "</svg>" : "";
  }
  const IKONLAR = {
    bilgi: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    igne: '<path d="M9 4h6l-1 6 3 3H7l3-3z"/><path d="M12 13v8"/>',
    kopya: '<rect x="8.5" y="8.5" width="12" height="12" rx="2"/><path d="M16 8.5V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16h3"/>',
    rapor: '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 13h7M12.5 9.5v7"/>',
    kapat: '<path d="M6 6l12 12M18 6L6 18"/>',
    gizle: '<path d="M3 12s3.4-6 9-6 9 6 9 6-3.4 6-9 6-9-6-9-6z"/><path d="M4 20L20 4"/>',
  };

  // ---- bağlam menüsü
  const MENU = [
    { id: "bilgi", ad: "Bilgi", ikon: "bilgi", turler: null, kisayol: "Enter" },
    { id: "ozellikler", ad: "Özellikler…", ikon: "ozellik-ata", turler: null },
    { ayrac: true },
    { id: "bol", ad: "Böl…", ikon: "bol", turler: ["kolon", "kiris", "cubuk"] },
    { id: "birlestir", ad: "Birleştir", ikon: "birlestir", turler: ["kolon", "kiris", "cubuk"] },
    { id: "mafsal", ad: "Mafsal…", ikon: "mafsal", turler: ["kolon", "kiris", "cubuk"] },
    { id: "kesit-oner", ad: "Kesit öner ve uygula", ikon: "kesit-degistir", turler: ["kolon", "kiris", "cubuk"] },
    { ayrac: true },
    { id: "isi-haritasi", ad: "Isı haritasında incele", ikon: "isi-haritasi", turler: ["kolon", "kiris", "cubuk", "doseme", "panel", "temel"] },
    { id: "yuk-akisi", ad: "Yük akışını göster", ikon: "yuk-akisi", turler: ["kolon", "kiris", "cubuk", "doseme", "temel", "panel"] },
    { id: "tasarim", ad: "Tasarım ayrıntısı", ikon: "tasarim-dc", turler: ["kolon", "kiris", "cubuk", "temel"] },
    { ayrac: true },
    { id: "gizle", ad: "Gizle", ikon: "gizle", turler: null },
    { id: "yalit", ad: "Yalıt", ikon: "yalit", turler: null },
    { id: "sil", ad: "Sil", ikon: "sil", turler: ["kolon", "kiris", "cubuk", "doseme", "panel", "dugum", "mesnet"], tehlike: true },
  ];
  /** Bir tür için menü öğeleri ve durumları (saf; test edilir). komutlar: {id: fn | {calistir, etkin}}. */
  function menuOgeleri(tur, komutlar) {
    komutlar = komutlar || {};
    const out = [];
    MENU.forEach(function (o_) {
      if (o_.ayrac) { if (out.length && !out[out.length - 1].ayrac) out.push({ ayrac: true }); return; }
      if (o_.turler && o_.turler.indexOf(tur) < 0) return;
      const k = komutlar[o_.id];
      const fn = typeof k === "function" ? k : (k && typeof k.calistir === "function" ? k.calistir : null);
      let etkin = !!fn || o_.id === "bilgi";
      if (k && typeof k === "object" && k.etkin != null) etkin = etkin && (typeof k.etkin === "function" ? !!k.etkin() : !!k.etkin);
      // devre dışı öğenin nedeni (komut nesnesinde neden: metin ya da işlev → metin | null); ipucu olarak gösterilir
      let neden = null;
      if (!etkin && k && typeof k === "object" && k.neden != null) { try { neden = typeof k.neden === "function" ? k.neden() : String(k.neden); } catch (e) { neden = null; } }
      out.push({ id: o_.id, ad: (k && k.ad) || o_.ad, ikon: o_.ikon, etkin: etkin, calistir: fn, tehlike: !!o_.tehlike, kisayol: o_.kisayol || "", neden: neden || "" });
    });
    while (out.length && out[out.length - 1].ayrac) out.pop();
    return out;
  }

  let acikMenu = null;
  function menuKapat(odak) {
    if (!acikMenu) return;
    const m = acikMenu; acikMenu = null;
    document.removeEventListener("pointerdown", m.disari, true);
    window.removeEventListener("blur", m.blur);
    if (m.el.parentNode) m.el.parentNode.removeChild(m.el);
    if (odak !== false && m.donus && m.donus.focus) { try { m.donus.focus({ preventScroll: true }); } catch (e) { /* yoksay */ } }
  }
  /**
   * Bağlam menüsü. olay: MouseEvent/PointerEvent ya da {x, y} (istemci px). sec: {tur, no, bina, veri?, komutlar?, denetci? (denetçi
   * seçenekleri), kapsayici?, donus? (kapanınca odak)}. Dönüş: menü öğesi.
   */
  function menuAc(olay, sec) {
    if (typeof document === "undefined") throw new Error("MatrisBilgi.menuAc yalnız tarayıcıda çalışır.");
    sec = sec || {};
    menuKapat(false);
    if (olay && olay.preventDefault) olay.preventDefault();
    const hedef = hedefKopya(sec);
    let model = null;
    try { model = bilgi(hedef, sec.bina, sec.veri); } catch (e) { model = null; }
    const m = document.createElement("div");
    m.className = "bilgi-menu";
    m.setAttribute("role", "menu");
    m.setAttribute("aria-label", (model ? model.baslik : "Eleman") + " menüsü");
    let h = '<div class="bilgi-menu-baslik"><b>' + kacis(model ? model.baslik : (TUR_ADI[sec.tur] || "") + " " + sec.no) + "</b>" +
      (model && model.adres ? "<span>" + kacis(model.adres) + "</span>" : "") + "</div>";
    if (model && model.ozet && model.ozet.length) {
      h += '<div class="bilgi-menu-cipler">' + model.ozet.map(function (o_) { return '<span class="bilgi-cip' + (o_.dc != null ? " bilgi-dc " + dcSinif(o_.dc) : "") + '">' + kacis(o_.ad + " " + o_.deger) + "</span>"; }).join("") + "</div>";
    }
    const ogeler = menuOgeleri(sec.tur, sec.komutlar);
    ogeler.forEach(function (o_, i) {
      if (o_.ayrac) { h += '<div class="bilgi-menu-ayrac" role="separator"></div>'; return; }
      h += '<button type="button" class="bilgi-menu-oge' + (o_.tehlike ? " tehlike" : "") + '" role="menuitem" data-i="' + i + '"' + (o_.etkin ? "" : ' aria-disabled="true"') +
        (!o_.etkin && o_.neden ? ' title="' + kacis(o_.neden) + '"' : "") + ">" +
        ikon(o_.ikon) + "<span>" + kacis(o_.ad) + "</span>" + (o_.kisayol ? '<kbd>' + kacis(o_.kisayol) + "</kbd>" : "") + "</button>";
    });
    m.innerHTML = h;
    m.addEventListener("click", function (e) {
      const b = e.target.closest(".bilgi-menu-oge");
      if (!b || b.getAttribute("aria-disabled") === "true") return;
      const o_ = ogeler[+b.getAttribute("data-i")];
      menuKapat(false);
      if (o_.id === "bilgi" && !o_.calistir) denetci(sec.kapsayici || null, Object.assign({}, sec.denetci || {}, hedefKopya(sec), { bina: sec.bina, veri: sec.veri,
        konum: { x: konum.x, y: konum.y } }));
      else if (o_.calistir) o_.calistir(hedef, e);
    });
    m.addEventListener("keydown", function (e) {
      const l = Array.from(m.querySelectorAll(".bilgi-menu-oge:not([aria-disabled])"));
      const i = l.indexOf(document.activeElement);
      if (e.key === "ArrowDown") { (l[(i + 1) % l.length] || l[0]).focus(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { (l[(i - 1 + l.length) % l.length] || l[0]).focus(); e.preventDefault(); }
      else if (e.key === "Home") { l[0].focus(); e.preventDefault(); }
      else if (e.key === "End") { l[l.length - 1].focus(); e.preventDefault(); }
      else if (e.key === "Escape" || e.key === "Tab") { menuKapat(); e.preventDefault(); }
    });
    // tam ekranda (Fullscreen API) yalnız tam ekran öğesinin alt ağacı görünür: menü oraya
    (sec.kapsayici || document.fullscreenElement || document.webkitFullscreenElement || document.body).appendChild(m);
    const konum = olay && olay.clientX != null ? { x: olay.clientX, y: olay.clientY } : (olay && olay.x != null ? { x: olay.x, y: olay.y } : { x: 40, y: 40 });
    const vw = window.innerWidth, vh = window.innerHeight, r_ = m.getBoundingClientRect();
    m.style.left = Math.round(Math.max(4, Math.min(konum.x, vw - r_.width - 4))) + "px";
    m.style.top = Math.round(Math.max(4, Math.min(konum.y, vh - r_.height - 4))) + "px";
    const kayit = { el: m, donus: sec.donus || document.activeElement, disari: function (e) { if (!m.contains(e.target)) menuKapat(false); }, blur: function () { menuKapat(false); } };
    acikMenu = kayit;
    setTimeout(function () {
      document.addEventListener("pointerdown", kayit.disari, true);
      window.addEventListener("blur", kayit.blur);
      const ilk = m.querySelector(".bilgi-menu-oge:not([aria-disabled])");
      if (ilk) ilk.focus({ preventScroll: true });
    }, 0);
    return m;
  }

  /** Hedefin kimlik alanları: {tur, no} ve yayılı temelde alt ("surekli" | "radye" | "radye-kirisi"), aks, yon. */
  function hedefKopya(h) {
    const o_ = { tur: h.tur, no: h.no };
    ["alt", "aks", "yon"].forEach(function (a) { if (h[a] != null) o_[a] = h[a]; });
    return o_;
  }

  // ---- denetçi pencereleri
  const pencereler = [];
  let zSira = 40;
  function mobilMi() { try { return window.matchMedia("(max-width: 639px)").matches; } catch (e) { return false; } }
  /**
   * Bilgi denetçisi (yüzen, sekmeli, iğnelenebilir). Aynı eleman açıksa öne gelir; iğnelenmemiş pencere yeniden kullanılır.
   * Dönüş: {el, hedef, kapat(), yenile({bina?, veri?, paket?}), sekmeSec(id), igne(bool), model}.
   */
  function denetci(kapsayici, sec) {
    if (typeof document === "undefined") throw new Error("MatrisBilgi.denetci yalnız tarayıcıda çalışır.");
    sec = Object.assign({}, sec || {});
    const hedef = hedefKopya(sec);
    hedef.no = sayiNo(hedef.no);
    const ayni = pencereler.find(function (p_) { return p_.hedef.tur === hedef.tur && String(p_.hedef.no) === String(hedef.no) && (p_.hedef.alt || "") === (hedef.alt || ""); });
    if (ayni) { ayni.yenile(sec); ayni.one(); return ayni; }
    const bos = pencereler.find(function (p_) { return !p_.igneli; });
    if (bos) { bos.hedefDegistir(hedef, sec); bos.one(); return bos; }
    const p_ = new Pencere(kapsayici || document.body, hedef, sec);
    pencereler.push(p_);
    return p_;
  }
  function Pencere(kap, hedef, sec) {
    const self = this;
    this.kap = kap; this.hedef = hedef; this.sec = sec; this.igneli = !!sec.igneli; this.sekme = sec.sekme || "geometri"; this.durum = sec.durum || null;
    const el = document.createElement("section");
    el.className = "bilgi-pencere";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "false");
    el.tabIndex = -1;
    el.innerHTML = '<header class="bilgi-ust"><div class="bilgi-baslik"><span class="bilgi-tur"></span><h3></h3><span class="bilgi-alt"></span></div>' +
      '<div class="bilgi-araclar">' +
      '<button type="button" class="bilgi-dugme bilgi-igne" aria-pressed="false" title="İğnele: yeni elemanı açınca bu pencere kalsın" aria-label="İğnele">' + ikon("igne") + "</button>" +
      '<button type="button" class="bilgi-dugme bilgi-kopyala" title="Kopyala (TSV, hesap tablosuna yapıştırılır)" aria-label="Kopyala">' + ikon("kopya") + "</button>" +
      '<button type="button" class="bilgi-dugme bilgi-rapor" title="Rapora ekle" aria-label="Rapora ekle">' + ikon("rapor") + "</button>" +
      '<button type="button" class="bilgi-dugme bilgi-kapat" title="Kapat (Esc)" aria-label="Kapat">' + ikon("kapat") + "</button></div></header>" +
      '<div class="bilgi-uyari" hidden></div><div class="bilgi-sekmeler" role="tablist"></div><div class="bilgi-govde" role="tabpanel" tabindex="0"></div>' +
      '<div class="bilgi-durum" role="status" aria-live="polite"></div>';
    this.el = el;
    kap.appendChild(el);
    // konum: tıklanan yerin yanı (elemanı örtmeden) ya da sağ üstten basamaklı
    const n = pencereler.length;
    this.yerlestir(sec.konum || null, n);
    this.one();
    el.addEventListener("click", function (e) {
      const t = e.target;
      const sk = t.closest(".bilgi-sekme");
      if (sk) { self.sekmeSec(sk.getAttribute("data-sekme")); return; }
      if (t.closest(".bilgi-kapat")) { self.kapat(); return; }
      if (t.closest(".bilgi-igne")) { self.igne(!self.igneli); return; }
      if (t.closest(".bilgi-kopyala")) { self.kopyala(); return; }
      if (t.closest(".bilgi-rapor")) { self.raporaEkle(); return; }
    });
    el.addEventListener("change", function (e) {
      if (e.target.classList.contains("bilgi-durum-sec")) { self.durum = e.target.value; self.ciz(); const s = self.el.querySelector(".bilgi-durum-sec"); if (s) s.focus(); }
    });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { self.kapat(); e.stopPropagation(); return; }
      const sk = e.target.closest && e.target.closest(".bilgi-sekme");
      if (!sk) return;
      const l = Array.from(el.querySelectorAll(".bilgi-sekme")), i = l.indexOf(sk);
      let j = null;
      if (e.key === "ArrowRight") j = (i + 1) % l.length; else if (e.key === "ArrowLeft") j = (i - 1 + l.length) % l.length;
      else if (e.key === "Home") j = 0; else if (e.key === "End") j = l.length - 1;
      if (j != null) { self.sekmeSec(l[j].getAttribute("data-sekme")); el.querySelector('.bilgi-sekme[data-sekme="' + l[j].getAttribute("data-sekme") + '"]').focus(); e.preventDefault(); }
    });
    el.addEventListener("pointerdown", function () { self.one(); });
    this._surukle();
    this.ciz();
    this._paketIste();
    setTimeout(function () { try { el.focus({ preventScroll: true }); } catch (e) { /* yoksay */ } }, 0);
  }
  const PP = Pencere.prototype;
  PP.one = function () { this.el.style.zIndex = String(++zSira + 1000); };
  /** Pencereyi tıklanan noktanın sağına (sığmazsa soluna) koyar ve görünür alana sığdırır. */
  PP.yerlestir = function (k, n) {
    if (mobilMi()) return;
    const vw = window.innerWidth, vh = window.innerHeight, w = this.el.offsetWidth || 412, h = this.el.offsetHeight || 420;
    let x, y;
    if (k) { x = k.x + 18; if (x + w > vw - 8) x = k.x - w - 18; y = k.y - 60; }
    else { x = vw - w - 16 - (n || 0) * 24; y = 64 + (n || 0) * 28; }
    this.el.style.left = Math.round(Math.max(8, Math.min(x, vw - w - 8))) + "px";
    this.el.style.top = Math.round(Math.max(8, Math.min(y, vh - h - 8))) + "px";
  };
  PP.hedefDegistir = function (hedef, sec) {
    this.hedef = hedef; this.sec = Object.assign({}, sec); this.durum = sec.durum || this.durum;
    if (sec.konum) this.yerlestir(sec.konum);
    if (sec.sekme) this.sekme = sec.sekme;
    this.ciz();
    this._paketIste();
  };
  PP.yenile = function (sec) {
    Object.keys(sec || {}).forEach(function (a) { if (a !== "tur" && a !== "no" && sec[a] !== undefined) this.sec[a] = sec[a]; }, this);
    this.ciz();
  };
  PP._paketIste = function () {
    const self = this, h = this.hedef;
    if (typeof this.sec.paketIste !== "function" || this.sec.paket || this.sec.eski) return;
    let s;
    try { s = this.sec.paketIste(h); } catch (e) { this._durumYaz(""); return; }
    if (s == null) { this._durumYaz(""); return; }       // bu eleman / çözüm için motor ayrıntısı yok
    this._durumYaz("Motor ayrıntısı isteniyor…");
    Promise.resolve(s).then(function (p_) {
      if (self.hedef !== h) return;
      if (p_) { self.sec.paket = p_; self.ciz(); }
      self._durumYaz("");
    }, function (e) { if (self.hedef === h) self._durumYaz("Motor ayrıntısı alınamadı: " + (e && e.message ? e.message : e)); });
  };
  PP._durumYaz = function (m) { const d = this.el.querySelector(".bilgi-durum"); if (d) d.textContent = m; };
  PP.ciz = function () {
    let m;
    try { m = bilgi(this.hedef, this.sec.bina, this.sec.veri, { durum: this.durum, paket: this.sec.paket, eski: this.sec.eski }); }
    catch (e) {
      this.model = null;
      this.el.querySelector(".bilgi-tur").textContent = TUR_ADI[this.hedef.tur] || "";
      this.el.querySelector("h3").textContent = String(this.hedef.no);
      this.el.querySelector(".bilgi-sekmeler").innerHTML = "";
      this.el.querySelector(".bilgi-govde").innerHTML = '<p class="bilgi-not">' + kacis(e.message) + "</p>";
      return;
    }
    this.model = m;
    if (m.durum) this.durum = m.durum;
    this.el.setAttribute("aria-label", m.baslik + " bilgisi");
    this.el.querySelector(".bilgi-tur").textContent = m.turAdi;
    this.el.querySelector("h3").textContent = (m.adres || m.baslik);
    this.el.querySelector(".bilgi-alt").textContent = m.baslik + (m.alt ? " · " + m.alt : "");
    const u = this.el.querySelector(".bilgi-uyari");
    u.hidden = !m.uyari; u.textContent = m.uyari || "";
    this.el.querySelector(".bilgi-rapor").hidden = typeof this.sec.raporaEkle !== "function";
    const self = this;
    if (!m.sekmeler.some(function (s) { return s.id === self.sekme; })) this.sekme = m.sekmeler[0] ? m.sekmeler[0].id : null;
    const pid = "bilgi-" + Math.random().toString(36).slice(2, 8);
    this.el.querySelector(".bilgi-sekmeler").innerHTML = m.sekmeler.map(function (s) {
      const ak = s.id === self.sekme;
      return '<button type="button" class="bilgi-sekme' + (ak ? " aktif" : "") + (s.bolumler.every(function (b) { return b.cozum; }) ? " soluk" : "") + '" role="tab" id="' + pid + "-" + s.id +
        '" aria-selected="' + ak + '" tabindex="' + (ak ? 0 : -1) + '" data-sekme="' + s.id + '">' + kacis(s.ad) + "</button>";
    }).join("");
    const s = m.sekmeler.find(function (x) { return x.id === self.sekme; });
    const g = this.el.querySelector(".bilgi-govde");
    g.setAttribute("aria-labelledby", pid + "-" + this.sekme);
    let h = "";
    if (s && s.secici && m.durumlar && m.durumlar.length) {
      h += '<label class="bilgi-durum-etiket"><span>Sonuç</span><select class="bilgi-durum-sec">' + m.durumlar.map(function (d) {
        return '<option value="' + kacis(d.ad) + '"' + (d.ad === m.durum ? " selected" : "") + ">" + kacis(d.etiket) + "</option>";
      }).join("") + "</select></label>";
    }
    h += s ? s.bolumler.map(bolumHtml).join("") : "";
    g.innerHTML = h;
    this.el.classList.toggle("igneli", this.igneli);
    this.el.querySelector(".bilgi-igne").setAttribute("aria-pressed", String(this.igneli));
  };
  PP.sekmeSec = function (id) { this.sekme = id; this.ciz(); };
  PP.igne = function (v) { this.igneli = !!v; this.ciz(); this._durumYaz(this.igneli ? "İğnelendi: başka eleman yeni pencerede açılır." : ""); };
  PP.kopyala = function () {
    if (!this.model) return;
    const metin = tsv(this.model), self = this;
    const bitti = function () { self._durumYaz("Kopyalandı (sekmeli metin)."); };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(metin).then(bitti, function () { yedek(); }); return; }
    } catch (e) { /* yedek */ }
    yedek();
    function yedek() {
      const t = document.createElement("textarea");
      t.value = metin; t.setAttribute("readonly", ""); t.style.position = "fixed"; t.style.opacity = "0";
      document.body.appendChild(t); t.select();
      try { document.execCommand("copy"); bitti(); } catch (e) { self._durumYaz("Kopyalanamadı."); }
      document.body.removeChild(t);
    }
  };
  PP.raporaEkle = function () {
    if (!this.model || typeof this.sec.raporaEkle !== "function") return;
    const s = this.model.sekmeler.find(function (x) { return x.id === this.sekme; }, this);
    this.sec.raporaEkle({ tur: this.hedef.tur, no: this.hedef.no, baslik: this.model.baslik, adres: this.model.adres, sekme: this.sekme,
      sekmeAdi: s ? s.ad : "", durum: this.model.durum, tsv: tsv(this.model, this.sekme), html: s ? s.bolumler.map(bolumHtml).join("") : "", model: this.model });
    this._durumYaz("Rapora eklendi: " + this.model.baslik + (s ? " — " + s.ad : ""));
  };
  PP.kapat = function () {
    const i = pencereler.indexOf(this);
    if (i >= 0) pencereler.splice(i, 1);
    if (this.el.parentNode) this.el.parentNode.removeChild(this.el);
    if (typeof this.sec.kapaninca === "function") this.sec.kapaninca(this.hedef);
  };
  PP._surukle = function () {
    const self = this, ust = this.el.querySelector(".bilgi-ust");
    ust.addEventListener("pointerdown", function (e) {
      if (e.target.closest("button") || mobilMi() || (e.button !== 0 && e.pointerType === "mouse")) return;
      const r_ = self.el.getBoundingClientRect(), bx = e.clientX, by = e.clientY;
      try { ust.setPointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
      self.el.classList.add("tasiniyor");
      const hareket = function (ev) {
        const vw = window.innerWidth, vh = window.innerHeight;
        self.el.style.left = Math.round(Math.max(-r_.width + 80, Math.min(vw - 80, r_.left + ev.clientX - bx))) + "px";
        self.el.style.top = Math.round(Math.max(0, Math.min(vh - 40, r_.top + ev.clientY - by))) + "px";
      };
      const birak = function () {
        self.el.classList.remove("tasiniyor");
        ust.removeEventListener("pointermove", hareket); ust.removeEventListener("pointerup", birak); ust.removeEventListener("pointercancel", birak);
      };
      ust.addEventListener("pointermove", hareket); ust.addEventListener("pointerup", birak); ust.addEventListener("pointercancel", birak);
      e.preventDefault();
    });
  };
  function hepsiniKapat(igneliDe) { pencereler.slice().forEach(function (p_) { if (igneliDe || !p_.igneli) p_.kapat(); }); }
  /** Açık pencerelerin verisini tazeler (yeni çözüm ya da model değişince); güncel çözümde motor ayrıntısı (paketIste) yeniden istenir. */
  function tazele(bina, veri, ek) {
    pencereler.forEach(function (p_) {
      p_.yenile(Object.assign({ bina: bina, veri: veri, paket: null }, ek || {}));
      if (veri && !(ek && ek.eski)) p_._paketIste();
    });
  }

  /** Uzun basmadan sonra tarayıcının ürettiği tek tıklamayı (450 ms içinde) yutar. */
  function tikYut() {
    const yut = function (ev) { ev.stopPropagation(); ev.preventDefault(); document.removeEventListener("click", yut, true); };
    document.addEventListener("click", yut, true);
    setTimeout(function () { document.removeEventListener("click", yut, true); }, 450);
  }

  // ---- sahneye bağlama
  /**
   * oge: sahne (SVG ya da kapsayıcı). sec: { bul(olay) → {tur, no} | null, bina(), veri(), komutlar?(hedef), secili?() → hedef,
   * konum?(hedef) → {x, y} (klavye menüsünün yeri), uzunBasma? (true), denetci? (denetçi seçenekleri), kapsayici? }. Dönüş {kaldir()}.
   */
  function bagla(oge, sec) {
    sec = sec || {};
    const ac = function (olay, hedef) {
      menuAc(olay, Object.assign(hedefKopya(hedef), { bina: sec.bina ? sec.bina() : null, veri: sec.veri ? sec.veri() : null,
        komutlar: sec.komutlar ? sec.komutlar(hedef) : {}, denetci: typeof sec.denetci === "function" ? sec.denetci(hedef) : sec.denetci, kapsayici: sec.kapsayici, donus: oge }));
    };
    const sagTik = function (e) {
      const h = sec.bul(e);
      if (!h) return;
      e.preventDefault();
      ac(e, h);
    };
    let uzunZ = 0, bas = null, uzunAcildi = false;
    const asagi = function (e) {
      if (e.pointerType === "mouse" || sec.uzunBasma === false) return;
      bas = { x: e.clientX, y: e.clientY, e: e };
      uzunAcildi = false;
      clearTimeout(uzunZ);
      uzunZ = setTimeout(function () {
        uzunZ = 0;
        const h = sec.bul(bas.e);
        if (h) { uzunAcildi = true; ac({ x: bas.x, y: bas.y }, h); }
      }, 500);
    };
    const hareket = function (e) { if (uzunZ && bas && Math.hypot(e.clientX - bas.x, e.clientY - bas.y) > 10) { clearTimeout(uzunZ); uzunZ = 0; } };
    const yukari = function () {
      if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
      if (uzunAcildi) { uzunAcildi = false; tikYut(); }   // parmak kalkınca gelen tıklama menü öğesini tetiklemesin
    };
    const tus = function (e) {
      if (!(e.key === "ContextMenu" || (e.key === "F10" && e.shiftKey))) return;
      const h = sec.secili ? sec.secili() : null;
      if (!h) return;
      e.preventDefault();
      const r_ = oge.getBoundingClientRect();
      const k = sec.konum ? sec.konum(h) : null;
      ac(k || { x: r_.left + r_.width / 2, y: r_.top + r_.height / 2 }, h);
    };
    oge.addEventListener("contextmenu", sagTik);
    oge.addEventListener("pointerdown", asagi);
    oge.addEventListener("pointermove", hareket);
    oge.addEventListener("pointerup", yukari);
    oge.addEventListener("pointercancel", yukari);
    oge.addEventListener("keydown", tus);
    return { kaldir: function () {
      oge.removeEventListener("contextmenu", sagTik); oge.removeEventListener("pointerdown", asagi); oge.removeEventListener("pointermove", hareket);
      oge.removeEventListener("pointerup", yukari); oge.removeEventListener("pointercancel", yukari); oge.removeEventListener("keydown", tus);
    } };
  }

  return Object.freeze({
    TUR_ADI: TUR_ADI, SEKME_ADI: SEKME_ADI, MENU: MENU,
    bilgi: bilgi, tsv: tsv, ozet: ozet, menuOgeleri: menuOgeleri, durumListesi: durumListesi, kisa: kisa, istasyonlar: istasyonlar,
    bagilSehim: bagilSehim, kesitOzellik: kesitOzellik, malzemeOzellik: malzemeOzellik, dikdortgenOzellik: dikdortgenOzellik,
    paketBirlestir: paketBirlestir, diyagramSvg: diyagramSvg, bolumHtml: bolumHtml, bicim: f,
    menuAc: menuAc, menuKapat: menuKapat, denetci: denetci, pencereler: function () { return pencereler.slice(); }, hepsiniKapat: hepsiniKapat, tazele: tazele,
    bagla: bagla,
  });
});
