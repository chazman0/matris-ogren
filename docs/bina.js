/* Matris Öğren — Bina sayfası (#bina): 3B bina düzenleyici (aks–kat sistemi), yük akışı, deforme şekil, diyagramlar, anlatım.
   Motor (yapi.py) web_kopru.py üzerinden "bina_coz", "bina_sablonlar", "bina_sablon", "bina_kutuphane" işlemleriyle çağrılır.
   Bu dosya yalnız arayüzdür; 3B çizim yardımcıları cizim3b.js'ten (window.Cizim3B), ortak yüzey app.js'ten (window.MatrisApp) gelir.
   Veri şeması: tasarım belgesi §3 (bina JSON) ve §4 (çıktı "veri"); alan adları bağlayıcıdır. */
(function () {
  "use strict";
  const A = window.MatrisApp, C = window.Cizim3B;
  const kok = document.getElementById("bina-kok");
  if (!A || !C || !kok) return;
  const kacis = A.kacis;
  const r1 = C.r1, pt = C.pt;

  // ---------- Yerleşik kütüphane (motor yüklenmeden ekran çizilebilsin; motor "bina_kutuphane" gelince değişir) ----------
  const YERLESIK_KUTUPHANE = {
    malzemeler: {
      beton: [{ ad: "C20/25", fck: 20, Ec: 28000, gamma: 25 }, { ad: "C25/30", fck: 25, Ec: 30000, gamma: 25 }, { ad: "C30/37", fck: 30, Ec: 32000, gamma: 25 },
              { ad: "C35/45", fck: 35, Ec: 33000, gamma: 25 }, { ad: "C40/50", fck: 40, Ec: 34000, gamma: 25 }],
      donati: [{ ad: "B420C", fyk: 420, Es: 200000 }],
      celik: [{ ad: "S235", Fy: 235, Fu: 360, E: 200000, G: 77200, gamma: 78.5 }, { ad: "S275", Fy: 275, Fu: 430, E: 200000, G: 77200, gamma: 78.5 }, { ad: "S355", Fy: 355, Fu: 510, E: 200000, G: 77200, gamma: 78.5 }],
    },
    kesit_katalogu: {
      dikdortgen_onerileri: [{ ad: "S30x30", b: 0.30, h: 0.30, kullanim: "kolon" }, { ad: "S40x40", b: 0.40, h: 0.40, kullanim: "kolon" }, { ad: "S30x60", b: 0.30, h: 0.60, kullanim: "kolon" },
                             { ad: "K25x50", b: 0.25, h: 0.50, kullanim: "kiris" }, { ad: "K30x60", b: 0.30, h: 0.60, kullanim: "kiris" }],
      profiller: { IPE: ["IPE 200", "IPE 240", "IPE 270", "IPE 300", "IPE 360", "IPE 400", "IPE 450", "IPE 500"], HEA: ["HEA 200", "HEA 240", "HEA 300", "HEA 400"], HEB: ["HEB 200", "HEB 240", "HEB 300", "HEB 400"] },
      profil_ozellikleri: {
        "IPE 200": { h: 200, b: 100, A: 28.48, Iy: 1943, Iz: 142.4, g: 22.4 }, "IPE 240": { h: 240, b: 120, A: 39.12, Iy: 3892, Iz: 283.6, g: 30.7 },
        "IPE 270": { h: 270, b: 135, A: 45.95, Iy: 5790, Iz: 419.9, g: 36.1 }, "IPE 300": { h: 300, b: 150, A: 53.81, Iy: 8356, Iz: 603.8, g: 42.2 },
        "IPE 360": { h: 360, b: 170, A: 72.73, Iy: 16270, Iz: 1043, g: 57.1 }, "IPE 400": { h: 400, b: 180, A: 84.46, Iy: 23130, Iz: 1318, g: 66.3 },
        "IPE 450": { h: 450, b: 190, A: 98.82, Iy: 33740, Iz: 1676, g: 77.6 }, "IPE 500": { h: 500, b: 200, A: 115.5, Iy: 48200, Iz: 2142, g: 90.7 },
        "HEA 200": { h: 190, b: 200, A: 53.83, Iy: 3692, Iz: 1336, g: 42.3 }, "HEA 240": { h: 230, b: 240, A: 76.84, Iy: 7763, Iz: 2769, g: 60.3 },
        "HEA 300": { h: 290, b: 300, A: 112.5, Iy: 18260, Iz: 6310, g: 88.3 }, "HEA 400": { h: 390, b: 300, A: 159, Iy: 45070, Iz: 8564, g: 125 },
        "HEB 200": { h: 200, b: 200, A: 78.08, Iy: 5696, Iz: 2003, g: 61.3 }, "HEB 240": { h: 240, b: 240, A: 106, Iy: 11260, Iz: 3923, g: 83.2 },
        "HEB 300": { h: 300, b: 300, A: 149.1, Iy: 25170, Iz: 8563, g: 117 }, "HEB 400": { h: 400, b: 300, A: 197.8, Iy: 57680, Iz: 10820, g: 155 },
      },
    },
    kullanim_siniflari: [
      { ad: "konut", etiket: "Konut (oda, koridor)", q: 2.0, kaynak: "TS 498:2021 Çizelge 6" }, { ad: "ofis", etiket: "Büro", q: 2.0, kaynak: "TS 498:2021 Çizelge 6" },
      { ad: "derslik", etiket: "Derslik", q: 3.5, kaynak: "TS 498:2021 Çizelge 6" }, { ad: "koridor", etiket: "Umuma açık koridor", q: 5.0, kaynak: "TS 498:2021 Çizelge 6" },
      { ad: "merdiven", etiket: "Merdiven (konut)", q: 3.5, kaynak: "TS 498:2021 Çizelge 6" }, { ad: "balkon", etiket: "Balkon (≤ 10 m²)", q: 5.0, kaynak: "TS 498:2021 Çizelge 6" },
      { ad: "magaza", etiket: "Mağaza", q: 5.0, kaynak: "TS 498:2021 Çizelge 6" }, { ad: "depo", etiket: "Depo / arşiv", q: 5.0, kaynak: "TS 498:2021 Çizelge 6" },
      { ad: "garaj", etiket: "Garaj (≤ 2,5 t)", q: 5.0, kaynak: "TS 498:2021 Çizelge 6" }, { ad: "cati-gezilen", etiket: "Çatı (zaman zaman kullanılan)", q: 2.0, kaynak: "TS 498:2021 Çizelge 6" },
      { ad: "cati-gezilmeyen", etiket: "Çatı (gezilmeyen)", q: 1.0, kaynak: "TS 498:2021 md. 15", dogrulandi: false },
    ],
    duvarlar: [{ ad: "tugla-delikli-19", etiket: "Delikli tuğla 19 cm (sıvalı)", w: 2.70 }, { ad: "tugla-delikli-13", etiket: "Delikli tuğla 13,5 cm (sıvalı)", w: 2.15 }, { ad: "gazbeton-20", etiket: "Gazbeton 20 cm (sıvalı)", w: 2.20 }],
    kaplamalar: [{ ad: "sap-seramik-siva", etiket: "Şap + seramik + tavan sıvası", g: 1.5 }, { ad: "parke", etiket: "Şap + parke + sıva", g: 1.2 }, { ad: "mermer", etiket: "Şap + mermer + sıva", g: 2.0 }],
    kombinasyon_kumeleri: ["ts500", "cythye_ydkt", "cythye_gkt"],
    sablonlar: [{ ad: "betonarme-2kat-3x2", baslik: "2 katlı betonarme konut (3×2 aks)", sistem: "betonarme" }, { ad: "celik-1kat-depo", baslik: "Çelik tek katlı depo (IPE/HEB)", sistem: "celik" }],
    dogrulanmamis: [],
  };
  const GAMMA_B = 25, GAMMA_S = 78.5;
  const ARACLAR = [["sec", "↖", "Seç", "S"], ["kolon", "▯", "Kolon", "K"], ["kiris", "─", "Kiriş", "R"], ["doseme", "▦", "Döşeme", "D"], ["duvar", "▤", "Duvar", "W"], ["sil", "✕", "Sil", "Del"]];
  const GORUNUM_AD = { "3b": "3B", plan: "Plan", on: "Ön", yan: "Yan" };
  const DIYAGRAM = {
    N: { ad: "N", uzun: "Normal kuvvet N", sinif: "se-dN", isaret: 1, eksen: 1 }, V: { ad: "V", uzun: "Kesme V", sinif: "se-dV", isaret: 1, eksen: 1 },
    M: { ad: "M", uzun: "Eğilme momenti M", sinif: "se-dM", isaret: -1, eksen: 1 }, Vz: { ad: "Vz", uzun: "Kesme Vz", sinif: "se-dV", isaret: 1, eksen: 2 },
    My: { ad: "My", uzun: "Eğilme momenti My", sinif: "se-dM", isaret: -1, eksen: 2 }, T: { ad: "T", uzun: "Burulma T", sinif: "se-dN", isaret: 1, eksen: 2 },
  };
  const TASLAK_ANAHTAR = "bina.taslak";
  const GECMIS_EN_FAZLA = 50;

  // ---------- Durum ----------
  let B = null;                         // bina JSON (§3)
  let KUT = YERLESIK_KUTUPHANE;         // kütüphane (motor ya da yerleşik)
  let SON = null;                       // son çözüm yanıtı {y, veri}
  let sonEski = false;                  // model çözümden sonra değişti
  const D = {
    kat: 1, arac: "sec", gorunum: "3b", secim: [], tumKatlar: false, firca: null, kirisBas: null,
    sekme: "akis", akisDurum: "G", akisHedef: null, oynat: 0, diyagram: "M", diyagramDurum: "1.4G+1.6Q", aksFiltre: "", deformeDurum: "G+Q", olcek: 100,
    hafif: false, sankeySecim: null, formul: null, cozuluyor: false, panelSekme: "nesne",
  };
  const gecmis = { geri: [], ileri: [] };
  const ref = {};
  let kamera = null, jest = null, hedefler = [], zamanci = 0, taslakZ = 0, cizimW = 600, cizimH = 400;

  // ---------- Küçük yardımcılar ----------
  function fmt(v, n) {
    if (typeof v !== "number") return v == null ? "—" : String(v);
    if (!isFinite(v)) return "—";
    const a = Math.abs(v);
    if (a < 1e-9) return "0";
    let t;
    if (a >= 1e6 || a < 1e-3) t = v.toExponential(n || 3).replace("e+", "e");
    else t = String(parseFloat(v.toPrecision(n || 4)));
    return t.replace(".", ",").replace("-", "−");
  }
  function f1(v) { return typeof v === "number" && isFinite(v) ? (Math.round(v * 10) / 10).toFixed(1).replace(".", ",").replace("-", "−") : "—"; }
  function f2(v) { return typeof v === "number" && isFinite(v) ? (Math.round(v * 100) / 100).toFixed(2).replace(".", ",").replace("-", "−") : "—"; }
  function sayiOku(s) {
    if (typeof s === "number") return isFinite(s) ? s : null;
    const t = String(s == null ? "" : s).trim().replace(",", ".");
    if (!/^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/.test(t)) return null;
    const n = parseFloat(t);
    return isFinite(n) ? n : null;
  }
  function kopya(o) { return JSON.parse(JSON.stringify(o)); }
  function metinSvg(x, y, t, sinif, hiza, ek) { return C.metin(x, y, t, sinif, hiza, ek); }
  function secenekler(liste, secili) {
    return liste.map(function (o) { return '<option value="' + kacis(o[0]) + '"' + (String(o[0]) === String(secili) ? " selected" : "") + ">" + kacis(o[1]) + "</option>"; }).join("");
  }
  function tabloH(basliklar, satirlar, sinif) {
    return '<div class="se-tablo-kutu"><table class="se-sonuc-tablo ' + (sinif || "") + '"><thead><tr>' + basliklar.map(function (h) { return "<th>" + kacis(h) + "</th>"; }).join("") +
      "</tr></thead><tbody>" + satirlar.map(function (r) {
        const ek = r.ek || "";
        return "<tr" + ek + ">" + r.map(function (c, i) { return (i ? '<td class="sayi">' : '<th scope="row">') + (typeof c === "string" && c.charAt(0) === "<" ? c : kacis(c)) + (i ? "</td>" : "</th>"); }).join("") + "</tr>";
      }).join("") + "</tbody></table></div>";
  }
  function hataGoster(kutu, mesajlar, baslik) {
    if (!kutu) return;
    if (!mesajlar || !mesajlar.length) { kutu.innerHTML = ""; return; }
    kutu.innerHTML = '<div class="hata-kutu" role="alert">' + (baslik ? "<strong>" + kacis(baslik) + "</strong>" : "") +
      (mesajlar.length === 1 ? '<div class="se-hata-metin">' + kacis(mesajlar[0]) + "</div>" : '<ul class="se-hata-liste">' + mesajlar.map(function (m) { return "<li>" + kacis(m) + "</li>"; }).join("") + "</ul>") + "</div>";
  }
  function katex(tex) { return A.katexHtml ? A.katexHtml(tex, true) : "<code>" + kacis(tex) + "</code>"; }
  function azHareket() { return C.azHareket(); }

  // ---------- Kesit ve malzeme özellikleri ----------
  function Jdik(b, h) {
    if (b > h) { const t = b; b = h; h = t; }
    const beta = 1 / 3 - 0.21 * (b / h) * (1 - Math.pow(b, 4) / (12 * Math.pow(h, 4)));
    return beta * b * b * b * h;
  }
  function profilBul(ad) {
    const po = (KUT.kesit_katalogu && KUT.kesit_katalogu.profil_ozellikleri) || {};
    return po[ad] || YERLESIK_KUTUPHANE.kesit_katalogu.profil_ozellikleri[ad] || null;
  }
  // Bir kesit kaydından (B.kesitler[ad]) sayısal özellikler: m, m², m⁴
  function kesitOz(ad) {
    const k = B.kesitler[ad];
    if (!k) return null;
    if (k.tip === "profil") {
      const p = profilBul(k.profil) || { h: 300, b: 150, A: 50, Iy: 8000, Iz: 600, g: 40 };
      return { tip: "profil", ad: ad, profil: k.profil, b: p.b / 1000, h: p.h / 1000, A: p.A / 1e4, Iy: p.Iz / 1e8, Iz: p.Iy / 1e8, J: 1e-7, g: p.g / 100, malzeme: k.malzeme, celik: true };
    }
    const b = +k.b || 0.3, h = +k.h || 0.5;
    return { tip: "dikdortgen", ad: ad, b: b, h: h, A: b * h, Iy: h * b * b * b / 12, Iz: b * h * h * h / 12, J: Jdik(b, h), Wpl: b * h * h / 4, malzeme: k.malzeme, celik: false };
  }
  function malzemeKart(ad) {
    const m = (B.malzemeler || {})[ad], ka = m && m.kutuphane ? m.kutuphane : ad;
    const ml = KUT.malzemeler || {};
    const bul = function (liste) { return (liste || []).filter(function (x) { return x.ad === ka || x.ad === ad; })[0]; };
    const c = bul(ml.beton); if (c) return Object.assign({ tur: "beton" }, c);
    const s = bul(ml.celik); if (s) return Object.assign({ tur: "celik" }, s);
    const d = bul(ml.donati); if (d) return Object.assign({ tur: "donati" }, d);
    return { tur: "?", ad: ka };
  }
  function kullanimQ(ad) {
    const k = (KUT.kullanim_siniflari || []).filter(function (x) { return x.ad === ad; })[0];
    return k ? k.q : 2.0;
  }
  function duvarW(anahtar) {
    const d = (B.duvarlar || {})[anahtar];
    const ka = d && d.kutuphane ? d.kutuphane : anahtar;
    const k = (KUT.duvarlar || []).filter(function (x) { return x.ad === ka; })[0];
    return k ? k.w : (d && typeof d.w === "number" ? d.w : 2.7);
  }

  // ---------- Model yardımcıları ----------
  function aksX(ad) { const a = B.akslar.x.filter(function (x) { return x.ad === ad; })[0]; return a ? +a.konum : null; }
  function aksY(ad) { const a = B.akslar.y.filter(function (x) { return x.ad === ad; })[0]; return a ? +a.konum : null; }
  function katKot(no) { const k = B.katlar.filter(function (x) { return x.no === no; })[0]; return k ? +k.kot : null; }
  function katAd(no) { const k = B.katlar.filter(function (x) { return x.no === no; })[0]; return k ? k.ad : "kat " + no; }
  function katH(no) { const a = katKot(no), b = katKot(no - 1); return a != null && b != null ? a - b : 3; }
  function ustKat() { return B.katlar.length ? Math.max.apply(null, B.katlar.map(function (k) { return k.no; })) : 0; }
  function aksEsit(a, b) { return a && b && a[0] === b[0] && a[1] === b[1]; }
  function adres(aks) { return aks[0] + aks[1]; }
  function kolonBul(aks, kat) { return B.kolonlar.filter(function (c) { return c.kat === kat && aksEsit(c.aks, aks); })[0] || null; }
  function kirisBul(p, q, kat) {
    return B.kirisler.filter(function (k) { return k.kat === kat && ((aksEsit(k.bas, p) && aksEsit(k.son, q)) || (aksEsit(k.bas, q) && aksEsit(k.son, p))); })[0] || null;
  }
  function dosemeBul(kose, kat) { return B.dosemeler.filter(function (d) { return d.kat === kat && aksEsit(d.kose[0], kose); })[0] || null; }
  function nesneBul(tur, no) {
    const l = tur === "kolon" ? B.kolonlar : tur === "kiris" ? B.kirisler : tur === "doseme" ? B.dosemeler : [];
    return l.filter(function (x) { return x.no === no; })[0] || null;
  }
  function yeniNo(liste) { return liste.reduce(function (m, x) { return Math.max(m, +x.no || 0); }, 0) + 1; }
  function aksSirala(p, q) {
    // kiriş küçük akstan büyük aksa (A→B, 1→2)
    const ix = B.akslar.x.map(function (a) { return a.ad; }), iy = B.akslar.y.map(function (a) { return a.ad; });
    if (p[1] === q[1]) return ix.indexOf(p[0]) <= ix.indexOf(q[0]) ? [p, q] : [q, p];
    return iy.indexOf(p[1]) <= iy.indexOf(q[1]) ? [p, q] : [q, p];
  }
  function ayniDogru(p, q) { return !aksEsit(p, q) && (p[0] === q[0] || p[1] === q[1]); }
  function kirisUzunluk(k) {
    return Math.hypot(aksX(k.son[0]) - aksX(k.bas[0]), aksY(k.son[1]) - aksY(k.bas[1]));
  }
  // Bir aks doğrusu üzerindeki kirişin kapsadığı bütün komşu aks çiftleri (kiriş komşu olmayan akslar arasında olabilir)
  function kirisParcalari(k) {
    const out = [];
    if (k.bas[1] === k.son[1]) {
      const ix = B.akslar.x.map(function (a) { return a.ad; }), i0 = ix.indexOf(k.bas[0]), i1 = ix.indexOf(k.son[0]);
      for (let i = Math.min(i0, i1); i < Math.max(i0, i1); i++) out.push([[ix[i], k.bas[1]], [ix[i + 1], k.bas[1]]]);
    } else {
      const iy = B.akslar.y.map(function (a) { return a.ad; }), j0 = iy.indexOf(k.bas[1]), j1 = iy.indexOf(k.son[1]);
      for (let j = Math.min(j0, j1); j < Math.max(j0, j1); j++) out.push([[k.bas[0], iy[j]], [k.bas[0], iy[j + 1]]]);
    }
    return out;
  }
  // Komşu aks çifti (p, q) o katta bir kirişle (ya da bir kirişin parçasıyla) örtülü mü?
  function kenarKirisi(p, q, kat) {
    for (let i = 0; i < B.kirisler.length; i++) {
      const k = B.kirisler[i];
      if (k.kat !== kat) continue;
      const parca = kirisParcalari(k);
      for (let j = 0; j < parca.length; j++) {
        if ((aksEsit(parca[j][0], p) && aksEsit(parca[j][1], q)) || (aksEsit(parca[j][0], q) && aksEsit(parca[j][1], p))) return k;
      }
    }
    return null;
  }
  function hucreler() {
    const out = [];
    for (let i = 0; i < B.akslar.x.length - 1; i++) for (let j = 0; j < B.akslar.y.length - 1; j++) {
      out.push({ kose: [[B.akslar.x[i].ad, B.akslar.y[j].ad], [B.akslar.x[i + 1].ad, B.akslar.y[j + 1].ad]] });
    }
    return out;
  }
  // Hücrenin dört kenarı: [{ad, p, q}] (kuzey = büyük Y)
  function hucreKenarlari(kose) {
    const a1 = kose[0][0], b1 = kose[0][1], a2 = kose[1][0], b2 = kose[1][1];
    return [{ ad: "güney", p: [a1, b1], q: [a2, b1] }, { ad: "kuzey", p: [a1, b2], q: [a2, b2] }, { ad: "batı", p: [a1, b1], q: [a1, b2] }, { ad: "doğu", p: [a2, b1], q: [a2, b2] }];
  }
  function eksikKenarlar(kose, kat) {
    return hucreKenarlari(kose).filter(function (e) { return !kenarKirisi(e.p, e.q, kat); }).map(function (e) { return e.ad; });
  }
  function kesisimler() {
    const out = [];
    B.akslar.x.forEach(function (a) { B.akslar.y.forEach(function (b) { out.push([a.ad, b.ad]); }); });
    return out;
  }
  function sdTahmini() {
    const dugum = {};
    B.kolonlar.forEach(function (c) { dugum[adres(c.aks) + "/" + (c.kat - 1)] = 1; dugum[adres(c.aks) + "/" + c.kat] = 1; });
    B.kirisler.forEach(function (k) { kirisParcalari(k).forEach(function (p) { dugum[adres(p[0]) + "/" + k.kat] = 1; dugum[adres(p[1]) + "/" + k.kat] = 1; }); });
    const temel = Object.keys(dugum).filter(function (k) { return /\/0$/.test(k); }).length;
    return Math.max(0, (Object.keys(dugum).length - temel) * 6);
  }

  // ---------- Şablon / sihirbaz ----------
  function aralikOku(metin) {
    return String(metin || "").split(/[\s,;]+/).map(function (t) { return sayiOku(t); }).filter(function (v) { return v != null && v > 0; });
  }
  function harf(i) { return i < 26 ? String.fromCharCode(65 + i) : "A" + String.fromCharCode(65 + i - 26); }
  function binaUret(p) {
    const celik = p.sistem === "celik";
    const xs = p.x && p.x.length ? p.x : [5, 4], ys = p.y && p.y.length ? p.y : [4];
    const ax = [], ay = [];
    let kx = 0; ax.push({ ad: "A", konum: 0 }); xs.forEach(function (d, i) { kx += d; ax.push({ ad: harf(i + 1), konum: +kx.toFixed(3) }); });
    let ky = 0; ay.push({ ad: "1", konum: 0 }); ys.forEach(function (d, i) { ky += d; ay.push({ ad: String(i + 2), konum: +ky.toFixed(3) }); });
    const n = Math.max(1, Math.min(12, +p.katSayisi || 2)), h = +p.katH || 3;
    const katlar = [{ no: 0, ad: "Temel", kot: 0 }];
    for (let k = 1; k <= n; k++) katlar.push({ no: k, ad: k === n ? "Çatı" : k + ". kat", kot: +(k * h).toFixed(3) });
    const kolonAd = p.kolonAd || (celik ? "HEB300" : "S40x40"), kirisAd = p.kirisAd || (celik ? "IPE300" : "K25x50");
    const kesitler = {};
    if (celik) {
      kesitler[kolonAd] = { tip: "profil", profil: p.kolonProfil || "HEB 300", malzeme: "S275" };
      kesitler[kirisAd] = { tip: "profil", profil: p.kirisProfil || "IPE 300", malzeme: "S275" };
    } else {
      kesitler[kolonAd] = { tip: "dikdortgen", b: p.kolonB || 0.40, h: p.kolonH || 0.40, malzeme: "C30", donati: "B420C", pas: 0.03 };
      kesitler[kirisAd] = { tip: "dikdortgen", b: p.kirisB || 0.25, h: p.kirisH || 0.50, malzeme: "C30", donati: "B420C", pas: 0.03 };
    }
    const duvarKip = p.duvar || "dis", duvarTip = p.duvarTip || "tugla-delikli-19";
    const kolonlar = [], kirisler = [], dosemeler = [];
    for (let k = 1; k <= n; k++) {
      ax.forEach(function (a) { ay.forEach(function (b) { kolonlar.push({ no: kolonlar.length + 1, aks: [a.ad, b.ad], kat: k, kesit: kolonAd, yon: "x" }); }); });
      const duvarVar = function (dis) { return duvarKip === "hepsi" || (duvarKip === "dis" && dis); };
      ay.forEach(function (b, j) {
        for (let i = 0; i < ax.length - 1; i++) {
          const dis = (j === 0 || j === ay.length - 1) && k < n;
          kirisler.push({ no: kirisler.length + 1, kat: k, bas: [ax[i].ad, b.ad], son: [ax[i + 1].ad, b.ad], kesit: kirisAd, duvar: duvarVar(dis) && k < n ? "duvar1" : null });
        }
      });
      ax.forEach(function (a, i) {
        for (let j = 0; j < ay.length - 1; j++) {
          const dis = (i === 0 || i === ax.length - 1) && k < n;
          kirisler.push({ no: kirisler.length + 1, kat: k, bas: [a.ad, ay[j].ad], son: [a.ad, ay[j + 1].ad], kesit: kirisAd, duvar: duvarVar(dis) && k < n ? "duvar1" : null });
        }
      });
      for (let i = 0; i < ax.length - 1; i++) for (let j = 0; j < ay.length - 1; j++) {
        dosemeler.push({ no: dosemeler.length + 1, kat: k, kose: [[ax[i].ad, ay[j].ad], [ax[i + 1].ad, ay[j + 1].ad]], h: p.dosemeH || 0.14,
          kullanim: k === n ? (p.catiKullanim || "cati-gezilen") : (p.kullanim || "konut"), g_ek: p.gEk != null ? p.gEk : 1.5, q: null, dagitim: "otomatik" });
      }
    }
    const malzemeler = celik ? { S275: { kutuphane: "S275" } } : { C30: { kutuphane: "C30/37" }, B420C: { kutuphane: "B420C" } };
    return {
      tur: "bina", surum: 1, baslik: p.baslik || (n + " katlı " + (celik ? "çelik" : "betonarme") + " bina (" + xs.length + "×" + ys.length + " aks)"),
      aciklama: p.aciklama || "Sihirbazla üretildi.", sistem: celik ? "celik" : "betonarme", birim: { kuvvet: "kN", uzunluk: "m" },
      akslar: { x: ax, y: ay }, katlar: katlar, malzemeler: malzemeler, kesitler: kesitler,
      kolonlar: kolonlar, kirisler: kirisler, dosemeler: dosemeler,
      duvarlar: duvarKip === "yok" ? {} : { duvar1: { kutuphane: duvarTip } },
      ek_yukler: [],
      temeller: { tip: "tekil", varsayilan: { B: 1.6, L: 1.6, h: 0.6 }, zemin: { q_em: 200, k0: 20000 }, mesnet: "ankastre", ozel: [] },
      yuk_durumlari: { G: { acik: true }, Q: { acik: true }, S: { acik: false }, W: { acik: false }, E: { acik: false } },
      deprem: { SS: 1.0, S1: 0.3, zemin_sinifi: "ZC", DD: "DD-2", BKS: 1, I: 1.0, tasiyici: celik ? "celik-cerceve-yuksek" : "betonarme-cerceve-yuksek", R: 8, D: 3, n: 0.3, Ct: celik ? 0.1 : 0.1, periyot: "ampirik", diyafram: "rijit", dismerkezlik: 0.05 },
      kombinasyon_kumesi: celik ? "cythye_ydkt" : "ts500", analiz: { catlamis_rijitlik: false, diyagram_nokta: 11 },
    };
  }
  const YERLESIK_SABLON = {
    "betonarme-2kat-3x2": function () { return binaUret({ sistem: "betonarme", x: [5, 4], y: [4], katSayisi: 2, katH: 3, baslik: "2 katlı betonarme konut (3×2 aks)", aciklama: "A–B–C / 1–2 aksları, 3 m kat yüksekliği, S40x40 kolon, K25x50 kiriş, 14 cm döşeme, dış duvarlar delikli tuğla." }); },
    "celik-1kat-depo": function () { return binaUret({ sistem: "celik", x: [6, 6, 6], y: [8], katSayisi: 1, katH: 6, dosemeH: 0.10, gEk: 0.5, catiKullanim: "cati-gezilmeyen", duvar: "yok", baslik: "Çelik tek katlı depo (IPE/HEB)", aciklama: "3×1 aks, 6 m kat yüksekliği; HEB 300 kolon, IPE 300 kiriş, hafif çatı döşemesi." }); },
  };

  // ---------- Doğrulama ----------
  function dogrula() {
    const uyari = [], hata = [];
    if (!B.akslar.x.length || !B.akslar.y.length) hata.push("En az bir X ve bir Y aksı gerekli.");
    if (B.akslar.x.length > 12 || B.akslar.y.length > 12) hata.push("En çok 12×12 aks desteklenir; modeli küçültün.");
    if (B.katlar.length > 13) hata.push("En çok 12 kat desteklenir.");
    if (!B.kolonlar.length) hata.push("Hiç kolon yok: Kolon aracıyla etkin katın aks kesişimlerine dokunun.");
    B.kolonlar.forEach(function (c) {
      if (!B.kesitler[c.kesit]) hata.push("Kolon " + adres(c.aks) + "/k" + c.kat + ": kesit “" + c.kesit + "” tanımsız.");
      const ustKiris = B.kirisler.some(function (k) { return k.kat === c.kat && kirisParcalari(k).some(function (p) { return aksEsit(p[0], c.aks) || aksEsit(p[1], c.aks); }); });
      if (!ustKiris) uyari.push({ tur: "kolon", no: c.no, kat: c.kat, metin: "Yüzen kolon " + adres(c.aks) + "/k" + c.kat + ": üstünde kiriş yok." });
      if (c.kat > 1 && !kolonBul(c.aks, c.kat - 1)) uyari.push({ tur: "kolon", no: c.no, kat: c.kat, metin: "Kolon " + adres(c.aks) + "/k" + c.kat + " altında kolon yok (kiriş üstünde oturur: sürekli kiriş değilse mekanizma)." });
    });
    B.kirisler.forEach(function (k) {
      if (!B.kesitler[k.kesit]) hata.push("Kiriş " + adres(k.bas) + "→" + adres(k.son) + "/k" + k.kat + ": kesit “" + k.kesit + "” tanımsız.");
      if (!ayniDogru(k.bas, k.son)) hata.push("Kiriş " + adres(k.bas) + "→" + adres(k.son) + ": uçlar aynı aks doğrusunda olmalı.");
      if (k.duvar && !B.duvarlar[k.duvar]) hata.push("Kiriş " + adres(k.bas) + "→" + adres(k.son) + ": duvar türü “" + k.duvar + "” tanımsız.");
      const uclar = [k.bas, k.son].map(function (a) { return kolonBul(a, k.kat) || B.kirisler.some(function (o) { return o !== k && o.kat === k.kat && kirisParcalari(o).some(function (p) { return aksEsit(p[0], a) || aksEsit(p[1], a); }); }); });
      if (!uclar[0] && !uclar[1]) uyari.push({ tur: "kiris", no: k.no, kat: k.kat, metin: "Kolonsuz kiriş " + adres(k.bas) + "→" + adres(k.son) + "/k" + k.kat + ": iki ucu da boşta." });
    });
    B.dosemeler.forEach(function (d) {
      const eksik = eksikKenarlar(d.kose, d.kat);
      if (eksik.length) uyari.push({ tur: "doseme", no: d.no, kat: d.kat, metin: "Yüzen döşeme " + adres(d.kose[0]) + "/" + adres(d.kose[1]) + "/k" + d.kat + ": " + eksik.join(", ") + " kenarında kiriş yok." });
    });
    const sd = sdTahmini();
    if (sd > 1500) hata.push("Serbestlik derecesi " + sd + " > 1500: modeli küçültün (daha az kat ya da aks).");
    return { uyari: uyari, hata: hata };
  }

  // ---------- Geri/ileri ve taslak ----------
  function anlikGoruntu() { return JSON.stringify(B); }
  let sonAnlik = "";
  function degisti(etiket) {
    // her düzenleme: geçmişe yaz, taslağı kaydet, sahneyi/panelleri yenile
    const simdi = anlikGoruntu();
    if (simdi !== sonAnlik) {
      gecmis.geri.push(sonAnlik || simdi);
      if (gecmis.geri.length > GECMIS_EN_FAZLA) gecmis.geri.shift();
      gecmis.ileri = [];
      sonAnlik = simdi;
    }
    if (SON) sonEski = true;
    taslakKaydet();
    yenile();
  }
  function geriAl() {
    if (!gecmis.geri.length) return;
    gecmis.ileri.push(anlikGoruntu());
    B = JSON.parse(gecmis.geri.pop());
    sonAnlik = anlikGoruntu();
    D.secim = []; D.kirisBas = null;
    if (SON) sonEski = true;
    taslakKaydet(); yenile();
  }
  function ileriAl() {
    if (!gecmis.ileri.length) return;
    gecmis.geri.push(anlikGoruntu());
    B = JSON.parse(gecmis.ileri.pop());
    sonAnlik = anlikGoruntu();
    D.secim = []; D.kirisBas = null;
    if (SON) sonEski = true;
    taslakKaydet(); yenile();
  }
  function taslakYaz() { try { if (B) localStorage.setItem(TASLAK_ANAHTAR, JSON.stringify(B)); } catch (e) { /* özel pencere ya da engelli depolama */ } }
  function taslakKaydet() {
    clearTimeout(taslakZ);
    taslakZ = setTimeout(function () { taslakZ = 0; taslakYaz(); }, 400);
  }
  window.addEventListener("pagehide", function () { if (taslakZ) { clearTimeout(taslakZ); taslakZ = 0; taslakYaz(); } });
  function taslakOku() {
    try { const t = localStorage.getItem(TASLAK_ANAHTAR); return t ? JSON.parse(t) : null; } catch (e) { return null; }
  }
  // Dışarıdan gelen bina JSON'unu (şablon, dosya, taslak) doğrulayıp normalize eder
  function binaYukle(m) {
    if (!m || typeof m !== "object" || Array.isArray(m)) throw new Error("Bina bir JSON nesnesi olmalı ({\"tur\": \"bina\", \"akslar\": …}).");
    if (m.tur && m.tur !== "bina") throw new Error("Bu JSON bir bina modeli değil (tur = “" + m.tur + "”). Sonlu eleman modelleri için Sonlu eleman sayfasını kullanın.");
    const b = kopya(m);
    b.tur = "bina"; b.surum = 1;
    b.akslar = b.akslar || { x: [], y: [] };
    ["x", "y"].forEach(function (e) {
      b.akslar[e] = (b.akslar[e] || []).map(function (a, i) { return { ad: String(a.ad != null ? a.ad : (e === "x" ? harf(i) : i + 1)), konum: +a.konum || 0 }; }).sort(function (p, q) { return p.konum - q.konum; });
    });
    b.katlar = (b.katlar || []).map(function (k, i) { return { no: k.no != null ? +k.no : i, ad: String(k.ad || (i ? i + ". kat" : "Temel")), kot: +k.kot || 0 }; }).sort(function (p, q) { return p.no - q.no; });
    if (!b.katlar.length) b.katlar = [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3 }];
    b.malzemeler = b.malzemeler || {}; b.kesitler = b.kesitler || {}; b.duvarlar = b.duvarlar || {};
    b.kolonlar = (b.kolonlar || []).map(function (c, i) { return { no: c.no != null ? +c.no : i + 1, aks: [String(c.aks[0]), String(c.aks[1])], kat: +c.kat || 1, kesit: String(c.kesit || ""), yon: c.yon === "y" ? "y" : "x" }; });
    b.kirisler = (b.kirisler || []).map(function (k, i) { return { no: k.no != null ? +k.no : i + 1, kat: +k.kat || 1, bas: [String(k.bas[0]), String(k.bas[1])], son: [String(k.son[0]), String(k.son[1])], kesit: String(k.kesit || ""), duvar: k.duvar || null }; });
    b.dosemeler = (b.dosemeler || []).map(function (d, i) {
      return { no: d.no != null ? +d.no : i + 1, kat: +d.kat || 1, kose: [[String(d.kose[0][0]), String(d.kose[0][1])], [String(d.kose[1][0]), String(d.kose[1][1])]], h: +d.h || 0.14,
        kullanim: String(d.kullanim || "konut"), g_ek: d.g_ek != null ? +d.g_ek : 1.5, q: d.q == null ? null : +d.q, dagitim: d.dagitim || "otomatik", kaplama: d.kaplama || null };
    });
    b.ek_yukler = Array.isArray(b.ek_yukler) ? b.ek_yukler : [];
    b.temeller = Object.assign({ tip: "tekil", varsayilan: { B: 1.6, L: 1.6, h: 0.6 }, zemin: { q_em: 200, k0: 20000 }, mesnet: "ankastre", ozel: [] }, b.temeller || {});
    b.yuk_durumlari = b.yuk_durumlari || { G: { acik: true }, Q: { acik: true } };
    b.sistem = b.sistem === "celik" ? "celik" : "betonarme";
    b.birim = b.birim || { kuvvet: "kN", uzunluk: "m" };
    b.kombinasyon_kumesi = b.kombinasyon_kumesi || (b.sistem === "celik" ? "cythye_ydkt" : "ts500");
    b.analiz = b.analiz || { catlamis_rijitlik: false, diyagram_nokta: 11 };
    return b;
  }
  function binayiAyarla(m, kaynak) {
    B = binaYukle(m);
    if (sonAnlik) gecmis.geri.push(sonAnlik);
    gecmis.ileri = [];
    sonAnlik = anlikGoruntu();
    D.secim = []; D.kirisBas = null; D.akisHedef = null; D.firca = null;
    D.kat = Math.min(Math.max(1, D.kat), ustKat());
    SON = null; sonEski = false;
    if (kamera) kamera.sifirla();
    taslakKaydet();
    yenile();
    if (kaynak) A.toast(kaynak);
  }

  // ---------- 3B sahne ----------
  function sahneBoyutla() {
    const kap = ref.sahneKutu;
    const w = Math.max(260, Math.floor(kap.clientWidth) || 600);
    const h = window.innerWidth < 700 ? w : Math.max(320, Math.min(540, Math.round(w * 0.6)));
    cizimW = w; cizimH = h;
    if (!kamera) kamera = new C.Kamera(w, h); else kamera.boyut(w, h);
    ref.svg.setAttribute("width", w); ref.svg.setAttribute("height", h);
  }
  function sinir() {
    const xs = B.akslar.x.map(function (a) { return +a.konum; }), ys = B.akslar.y.map(function (a) { return +a.konum; });
    const zs = B.katlar.map(function (k) { return +k.kot; });
    const th = (B.temeller.varsayilan && +B.temeller.varsayilan.h) || 0.6;
    return { x0: Math.min.apply(null, xs), x1: Math.max.apply(null, xs), y0: Math.min.apply(null, ys), y1: Math.max.apply(null, ys), z0: Math.min.apply(null, zs) - th, z1: Math.max.apply(null, zs) };
  }
  function katlarHedef() {
    return D.tumKatlar ? B.katlar.filter(function (k) { return k.no >= 1; }).map(function (k) { return k.no; }) : [D.kat];
  }
  function secildiMi(tur, no) { return D.secim.some(function (s) { return s.tur === tur && s.no === no; }); }
  function sahneCiz() {
    const svg = ref.svg;
    if (!svg || !B) return;
    const b = kamera.bakis, W = cizimW, H = cizimH, sn = sinir();
    const pts = [];
    [sn.x0 - 1.2, sn.x1 + 0.6].forEach(function (X) { [sn.y0 - 1.2, sn.y1 + 0.6].forEach(function (Y) { [sn.z0, sn.z1 + 0.8].forEach(function (Z) { pts.push(C.izdusum(X, Y, Z, b)); }); }); });
    const T = C.donusum(pts, W, H, { pl: 30, pu: 24, pa: 28 });
    const P = function (X, Y, Z) { const q = C.izdusum(X, Y, Z, b); return [T.x(q[0]), T.y(q[1])]; };
    const sahne = new C.Sahne();
    const s = kamera.pxOlcek(svg) || 1;     // 1 ekran px = s viewBox birimi
    const rHedef = (jest && jest.kaba({ pointerType: "touch" }) ? 26 : 22) * s;
    hedefler = [];
    const hafif = D.hafif, kat = D.kat, kot = katKot(kat), celik = B.sistem === "celik";
    const uyarilar = sonUyarilar || [];
    const uyariVar = function (tur, no) { return uyarilar.some(function (u) { return u.tur === tur && u.no === no; }); };

    // zemin ızgarası ve aks adları (katman 0)
    const izgara = function (Z, sinif) {
      B.akslar.x.forEach(function (a) { const p = P(+a.konum, sn.y0 - 0.6, Z), q = P(+a.konum, sn.y1 + 0.6, Z); sahne.ekle(-1e9, C.cizgi(p, q, sinif), 0); });
      B.akslar.y.forEach(function (a) { const p = P(sn.x0 - 0.6, +a.konum, Z), q = P(sn.x1 + 0.6, +a.konum, Z); sahne.ekle(-1e9, C.cizgi(p, q, sinif), 0); });
    };
    izgara(0, "b3-izgara");
    if (kat >= 1 && kot != null && kot !== 0) izgara(kot, "b3-izgara b3-izgara-kat");
    if (!hafif) {
      const ze = kat >= 1 && kot != null ? kot : 0;
      B.akslar.x.forEach(function (a) { const p = P(+a.konum, sn.y0 - 1.0, ze); sahne.ekle(1e9, metinSvg(p[0], p[1] + 4, a.ad, "b3-aks-t", "middle", ' data-aks-x="' + kacis(a.ad) + '"'), 2); });
      B.akslar.y.forEach(function (a) { const p = P(sn.x1 + 1.0, +a.konum, ze); sahne.ekle(1e9, metinSvg(p[0], p[1] + 4, a.ad, "b3-aks-t", "middle", ' data-aks-y="' + kacis(a.ad) + '"'), 2); });
      B.katlar.forEach(function (k) {
        const p = P(sn.x0 - 1.0, sn.y1 + 0.3, +k.kot);
        sahne.ekle(1e9, metinSvg(p[0], p[1] + 4, k.ad + " " + (k.kot >= 0 ? "+" : "") + f2(+k.kot), "b3-kot-t" + (k.no === kat ? " b3-kot-etkin" : ""), "end"), 2);
      });
    }
    // temeller (kat 1 kolonlarının altında) ve mesnetler
    const th = (B.temeller.varsayilan && +B.temeller.varsayilan.h) || 0.6;
    B.kolonlar.forEach(function (c) {
      if (c.kat !== 1) return;
      const X = aksX(c.aks[0]), Y = aksY(c.aks[1]);
      if (X == null || Y == null) return;
      const oz = (B.temeller.ozel || []).filter(function (o) { return aksEsit(o.aks, c.aks); })[0] || {};
      const Bt = +oz.B || +B.temeller.varsayilan.B || 1.6, Lt = +oz.L || +B.temeller.varsayilan.L || 1.6, z0 = katKot(0) || 0;
      const hayalet = kat !== 0 ? " b3-hayalet" : "";
      C.prizma(sahne, T, b, [X, Y, z0 - th], [X, Y, z0], [Bt / 2, 0, 0], [0, Lt / 2, 0], "b3-temel" + hayalet, ' data-tur="temel" data-no="' + c.no + '"', 1);
      if (!hafif) C.mesnet(sahne, T, b, [X, Y, z0 - th], B.temeller.mesnet, ' class="b3-mesnet' + hayalet + '"');
    });
    // kolonlar
    B.kolonlar.forEach(function (c) {
      const X = aksX(c.aks[0]), Y = aksY(c.aks[1]), z1 = katKot(c.kat), z0 = katKot(c.kat - 1);
      const ko = kesitOz(c.kesit);
      if (X == null || Y == null || z1 == null || z0 == null) return;
      const bX = ko ? (c.yon === "y" ? ko.b : ko.h) : 0.4, bY = ko ? (c.yon === "y" ? ko.h : ko.b) : 0.4;
      const sinif = "b3-kolon " + (ko && ko.celik ? "b3-celik" : "b3-beton") + (c.kat !== kat ? " b3-hayalet" : "") + (secildiMi("kolon", c.no) ? " b3-secili" : "") + (uyariVar("kolon", c.no) ? " b3-uyarili" : "");
      const ekr = C.prizma(sahne, T, b, [X, Y, z0], [X, Y, z1], [bX / 2, 0, 0], [0, bY / 2, 0], sinif, ' data-tur="kolon" data-no="' + c.no + '"', 1);
      if (c.kat === kat) {
        hedefler.push({ tur: "dogru", a: P(X, Y, z0), b: P(X, Y, z1), r: 14 * s, kind: "nesne", nesne: "kolon", no: c.no });
        if (!hafif && uyariVar("kolon", c.no)) { const p = P(X, Y, (z0 + z1) / 2); sahne.ekle(1e9, rozet(p[0] + 12, p[1]), 2); }
      }
      void ekr;
    });
    // kirişler ve duvarlar
    B.kirisler.forEach(function (k) {
      const X1 = aksX(k.bas[0]), Y1 = aksY(k.bas[1]), X2 = aksX(k.son[0]), Y2 = aksY(k.son[1]), Z = katKot(k.kat);
      const ko = kesitOz(k.kesit);
      if (X1 == null || Y1 == null || X2 == null || Y2 == null || Z == null) return;
      const bb = ko ? ko.b : 0.25, hh = ko ? ko.h : 0.5, yatayX = Y1 === Y2;
      const e1 = yatayX ? [0, bb / 2, 0] : [bb / 2, 0, 0];
      const sinif = "b3-kiris " + (ko && ko.celik ? "b3-celik" : "b3-beton") + (k.kat !== kat ? " b3-hayalet" : "") + (secildiMi("kiris", k.no) ? " b3-secili" : "") + (uyariVar("kiris", k.no) ? " b3-uyarili" : "");
      C.prizma(sahne, T, b, [X1, Y1, Z - hh / 2], [X2, Y2, Z - hh / 2], e1, [0, 0, hh / 2], sinif, ' data-tur="kiris" data-no="' + k.no + '"', 1);
      if (k.duvar && !hafif) {
        const ust = katKot(k.kat + 1) != null ? katKot(k.kat + 1) - hh : Z + 1.0;
        const kose = [[X1, Y1, Z], [X2, Y2, Z], [X2, Y2, ust], [X1, Y1, ust]];
        C.dortgen(sahne, T, b, kose, "b3-duvar" + (k.kat !== kat ? " b3-hayalet" : ""), ' data-tur="duvar" data-no="' + k.no + '"', 1);
      }
      if (k.kat === kat) {
        hedefler.push({ tur: "dogru", a: P(X1, Y1, Z), b: P(X2, Y2, Z), r: 14 * s, kind: "nesne", nesne: "kiris", no: k.no });
        if (!hafif && uyariVar("kiris", k.no)) { const p = P((X1 + X2) / 2, (Y1 + Y2) / 2, Z); sahne.ekle(1e9, rozet(p[0], p[1] - 14), 2); }
      }
    });
    // döşemeler
    B.dosemeler.forEach(function (d) {
      const X1 = aksX(d.kose[0][0]), Y1 = aksY(d.kose[0][1]), X2 = aksX(d.kose[1][0]), Y2 = aksY(d.kose[1][1]), Z = katKot(d.kat);
      if (X1 == null || Y1 == null || X2 == null || Y2 == null || Z == null) return;
      const kose = [[X1, Y1, Z], [X2, Y1, Z], [X2, Y2, Z], [X1, Y2, Z]];
      const sinif = "b3-doseme" + (d.kat !== kat ? " b3-hayalet" : "") + (secildiMi("doseme", d.no) ? " b3-secili" : "") + (uyariVar("doseme", d.no) ? " b3-uyarili" : "");
      const ekr = C.dortgen(sahne, T, b, kose, sinif, ' data-tur="doseme" data-no="' + d.no + '"', 1);
      if (d.kat === kat) {
        hedefler.push({ tur: "cokgen", pts: ekr, kind: "nesne", nesne: "doseme", no: d.no });
        if (!hafif) {
          const m = P((X1 + X2) / 2, (Y1 + Y2) / 2, Z);
          sahne.ekle(C.derinlik((X1 + X2) / 2, (Y1 + Y2) / 2, Z, b) + 1e-3, metinSvg(m[0], m[1] + 4, "D" + d.no, "b3-doseme-t", "middle"), 1);
          if (uyariVar("doseme", d.no)) sahne.ekle(1e9, rozet(m[0] + 18, m[1] - 10), 2);
        }
      }
    });
    // dokunma hedefleri: etkin katın aks kesişimleri ve hücreleri
    if (kat >= 1 && kot != null && !hafif) {
      const kes = kesisimler();
      kes.forEach(function (aks) {
        const X = aksX(aks[0]), Y = aksY(aks[1]), p = P(X, Y, kot);
        let sinif = "b3-hedef";
        if (D.kirisBas) sinif += aksEsit(D.kirisBas, aks) ? " b3-hedef-bas" : (ayniDogru(D.kirisBas, aks) ? " b3-hedef-aday" : " b3-hedef-soluk");
        else if (D.arac === "kolon") sinif += kolonBul(aks, kat) ? " b3-hedef-dolu" : " b3-hedef-bos";
        else if (D.arac === "kiris") sinif += " b3-hedef-aday";
        sahne.ekle(1e9, '<circle class="' + sinif + '" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="' + r1(6 * s) + '" data-kesisim="' + kacis(aks.join("|")) + '"/>', 2);
        hedefler.push({ tur: "daire", x: p[0], y: p[1], r: rHedef, kind: "kesisim", aks: aks });
      });
      hucreler().forEach(function (h) {
        const X1 = aksX(h.kose[0][0]), Y1 = aksY(h.kose[0][1]), X2 = aksX(h.kose[1][0]), Y2 = aksY(h.kose[1][1]);
        const ekr = [P(X1, Y1, kot), P(X2, Y1, kot), P(X2, Y2, kot), P(X1, Y2, kot)];
        const dolu = dosemeBul(h.kose[0], kat), eksik = eksikKenarlar(h.kose, kat);
        if (D.arac === "doseme" && !dolu) {
          const m = P((X1 + X2) / 2, (Y1 + Y2) / 2, kot);
          if (eksik.length) sahne.ekle(1e9, C.cokgen(ekr, "b3-hucre-eksik"), 2);
          else sahne.ekle(1e9, '<g class="b3-hucre-arti"><circle cx="' + r1(m[0]) + '" cy="' + r1(m[1]) + '" r="' + r1(11 * s) + '"/>' + metinSvg(m[0], m[1] + 4.5 * s, "+", "b3-hucre-t", "middle") + "</g>", 2);
        }
        hedefler.unshift({ tur: "cokgen", pts: ekr, kind: "hucre", kose: h.kose, eksik: eksik });
      });
    }
    // çözüm sonrası yük akışı vurgusu
    if (SON && !sonEski && D.sekme === "akis" && D.akisHedef && !hafif && typeof akisVurguCiz === "function") akisVurguCiz(sahne, P, b, s);
    const vb = kamera.viewBox().split(" ").map(Number);
    const eksen = eksenTakimi(vb, b);
    svg.setAttribute("viewBox", kamera.viewBox());
    svg.innerHTML = '<defs><pattern id="b3-tarama" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" class="b3-tarama-c"/></pattern></defs>' +
      sahne.html() + eksen + '<path id="bn-gecici" class="b3-gecici" d=""/>';
  }
  function rozet(x, y) {
    return '<g class="b3-rozet"><circle cx="' + r1(x) + '" cy="' + r1(y) + '" r="8"/>' + metinSvg(x, y + 4, "!", "b3-rozet-t", "middle") + "</g>";
  }
  function eksenTakimi(vb, b) {
    const ox = vb[0] + 26, oy = vb[1] + vb[3] - 22;
    let s = "";
    [["X", [1, 0, 0]], ["Y", [0, 1, 0]], ["Z", [0, 0, 1]]].forEach(function (e) {
      const w = C.yon(e[1], b);
      s += '<path class="se-eksen" d="M' + pt(ox, oy) + " L" + pt(ox + w[0] * 22, oy + w[1] * 22) + '"/>' + C.okBasi(ox + w[0] * 24, oy + w[1] * 24, w[0], w[1], "se-eksen-o") +
        metinSvg(ox + w[0] * 33, oy + w[1] * 33 + 4, e[0], "se-eksen-t", "middle");
    });
    return '<g class="b3-eksen">' + s + "</g>";
  }
  let cizimBekliyor = 0;
  function sahneYenile() {
    if (cizimBekliyor) return;
    cizimBekliyor = requestAnimationFrame(function () { cizimBekliyor = 0; sahneCiz(); });
  }

  // ---------- Jestler ve araçlar ----------
  function jestleriKur() {
    const svg = ref.svg;
    jest = C.jestler(svg, {
      nokta: function (e) { return kamera.svgNokta(svg, e.clientX, e.clientY); },
      pxOlcek: function () { return kamera.pxOlcek(svg); },
      kipSec: function (e) { return (e.shiftKey || (e.buttons & 4) || kamera.gorunum !== "3b" && kamera.gorunum !== "serbest") ? "kaydir" : "dondur"; },
      dondur: function (dfi, dpsi) { kamera.dondur(dfi, dpsi); D.hafif = true; gorunumDugmeleri(); sahneYenile(); },
      kaydir: function (dx, dy) { kamera.kaydir(dx, dy); svg.setAttribute("viewBox", kamera.viewBox()); },
      yakinlastir: function (k, p) { kamera.yakinlastir(k, p[0], p[1]); svg.setAttribute("viewBox", kamera.viewBox()); },
      hareketBitti: function () { if (D.hafif) { D.hafif = false; sahneYenile(); } },
      dokun: function (p) { aracUygula(C.vurus(hedefler, p[0], p[1]), p); },
      uzunBas: function (p) {
        const h = C.vurus(hedefler, p[0], p[1]);
        if (h && h.kind === "nesne") { D.secim = [{ tur: h.nesne, no: h.no }]; D.panelSekme = "nesne"; yenile(); panelAc(); }
      },
      surukleBasla: function (p) {
        if (D.arac !== "kiris") return false;
        const h = C.vurus(hedefler, p[0], p[1]);
        if (!h || h.kind !== "kesisim") return false;
        D.kirisBas = h.aks; sahneCiz(); return true;
      },
      surukle: function (p) {
        const g = document.getElementById("bn-gecici"), h0 = hedefler.filter(function (h) { return h.kind === "kesisim" && aksEsit(h.aks, D.kirisBas); })[0];
        if (g && h0) g.setAttribute("d", "M" + pt(h0.x, h0.y) + " L" + pt(p[0], p[1]));
      },
      surukleBitir: function (p) {
        const h = p ? C.vurus(hedefler, p[0], p[1]) : null;
        if (h && h.kind === "kesisim" && D.kirisBas && ayniDogru(D.kirisBas, h.aks)) { const bas = D.kirisBas; D.kirisBas = null; kirisEkle(bas, h.aks); }
        else { D.kirisBas = null; sahneCiz(); }
      },
    });
  }
  function aracUygula(h, p) {
    void p;
    if (!h) {
      if (D.kirisBas) { D.kirisBas = null; sahneCiz(); return; }
      if (D.secim.length) { D.secim = []; yenile(); }
      if (D.akisHedef) { D.akisHedef = null; sahneCiz(); }
      return;
    }
    if (h.kind === "formul") { formulGoster(h.key); return; }
    if (h.kind === "kesisim") {
      if (D.arac === "kolon") { kolonToggle(h.aks); return; }
      if (D.arac === "kiris") {
        if (!D.kirisBas) { D.kirisBas = h.aks; sahneCiz(); return; }
        if (aksEsit(D.kirisBas, h.aks)) { D.kirisBas = null; sahneCiz(); return; }
        if (!ayniDogru(D.kirisBas, h.aks)) { A.toast("Kiriş uçları aynı aks doğrusunda olmalı (" + adres(D.kirisBas) + " ile aynı harf ya da aynı sayı)."); return; }
        const bas = D.kirisBas; D.kirisBas = null; kirisEkle(bas, h.aks); return;
      }
      const c = kolonBul(h.aks, D.kat);
      if (c && (D.arac === "sec" || D.arac === "sil")) { nesneDokun("kolon", c.no); return; }
      if (D.arac === "doseme" || D.arac === "duvar") A.toast(D.arac === "doseme" ? "Döşeme için hücrenin ortasındaki + işaretine dokunun." : "Duvar için bir kirişe dokunun.");
      return;
    }
    if (h.kind === "hucre") {
      if (D.arac === "doseme") { dosemeToggle(h.kose, h.eksik); return; }
      const d = dosemeBul(h.kose[0], D.kat);
      if (d && (D.arac === "sec" || D.arac === "sil")) { nesneDokun("doseme", d.no); return; }
      if (D.arac === "sec" && D.secim.length) { D.secim = []; yenile(); }
      return;
    }
    if (h.kind === "nesne") nesneDokun(h.nesne, h.no);
  }
  function nesneDokun(tur, no) {
    const n = nesneBul(tur, no);
    if (!n) return;
    if (D.arac === "sil") { nesneSil(tur, no); return; }
    if (D.arac === "duvar") { if (tur === "kiris") duvarToggle(n); else A.toast("Duvar yalnız kirişe atanır."); return; }
    if (D.arac === "kolon" && tur === "kolon") { kolonToggle(n.aks); return; }
    if (D.arac === "doseme" && tur === "doseme") { dosemeToggle(n.kose, []); return; }
    if (D.arac === "kiris") { A.toast("Kiriş çizmek için iki aks kesişimine art arda dokunun ya da birinden ötekine sürükleyin."); return; }
    // Seç: fırça varsa kesit ata; değilse seçim (ikinci dokunma çoklu seçim)
    if (D.firca && (tur === "kolon" || tur === "kiris")) {
      katlarHedef().forEach(function (k) {
        const hedef = tur === "kolon" ? B.kolonlar.filter(function (c) { return c.kat === k && aksEsit(c.aks, n.aks); }) : B.kirisler.filter(function (x) { return x.kat === k && aksEsit(x.bas, n.bas) && aksEsit(x.son, n.son); });
        hedef.forEach(function (x) { x.kesit = D.firca; });
      });
      A.toast(D.firca + " atandı.");
      degisti();
      return;
    }
    if (SON && !sonEski && D.sekme === "akis") { D.akisHedef = { tur: tur, no: no }; D.secim = [{ tur: tur, no: no }]; akisYenile(); yenile(); return; }
    if (secildiMi(tur, no)) D.secim = D.secim.filter(function (s) { return !(s.tur === tur && s.no === no); });
    else if (D.secim.length && D.secim[0].tur === tur) D.secim.push({ tur: tur, no: no });
    else D.secim = [{ tur: tur, no: no }];
    D.panelSekme = "nesne";
    yenile();
  }
  function varsayilanKesit(tur) {
    if (D.firca && B.kesitler[D.firca]) return D.firca;
    const liste = tur === "kolon" ? B.kolonlar : B.kirisler, say = {};
    liste.forEach(function (x) { say[x.kesit] = (say[x.kesit] || 0) + 1; });
    const adlar = Object.keys(say).sort(function (a, b) { return say[b] - say[a]; });
    if (adlar.length && B.kesitler[adlar[0]]) return adlar[0];
    const on = tur === "kolon" ? "S" : "K";
    const mevcut = Object.keys(B.kesitler).filter(function (k) { return k.charAt(0).toUpperCase() === on || (B.kesitler[k].tip === "profil" && (tur === "kolon" ? /HE/.test(B.kesitler[k].profil) : /IPE/.test(B.kesitler[k].profil))); });
    if (mevcut.length) return mevcut[0];
    const ad = B.sistem === "celik" ? (tur === "kolon" ? "HEB300" : "IPE300") : (tur === "kolon" ? "S40x40" : "K25x50");
    if (!B.kesitler[ad]) {
      B.kesitler[ad] = B.sistem === "celik" ? { tip: "profil", profil: tur === "kolon" ? "HEB 300" : "IPE 300", malzeme: Object.keys(B.malzemeler)[0] || "S275" }
        : { tip: "dikdortgen", b: tur === "kolon" ? 0.4 : 0.25, h: tur === "kolon" ? 0.4 : 0.5, malzeme: Object.keys(B.malzemeler)[0] || "C30", donati: "B420C", pas: 0.03 };
    }
    return ad;
  }
  function varsayilanDuvar() {
    const k = Object.keys(B.duvarlar);
    if (k.length) return k[0];
    B.duvarlar.duvar1 = { kutuphane: "tugla-delikli-19" };
    return "duvar1";
  }
  function kolonToggle(aks) {
    let eklendi = 0, silindi = 0;
    katlarHedef().forEach(function (k) {
      const c = kolonBul(aks, k);
      if (c) { B.kolonlar = B.kolonlar.filter(function (x) { return x !== c; }); silindi++; }
      else { B.kolonlar.push({ no: yeniNo(B.kolonlar), aks: aks.slice(), kat: k, kesit: varsayilanKesit("kolon"), yon: "x" }); eklendi++; }
    });
    if (silindi) D.secim = D.secim.filter(function (s) { return s.tur !== "kolon" || nesneBul("kolon", s.no); });
    degisti();
  }
  function kirisEkle(p, q) {
    const uc = aksSirala(p, q);
    let silindi = 0;
    katlarHedef().forEach(function (k) {
      const v = kirisBul(uc[0], uc[1], k);
      if (v) { B.kirisler = B.kirisler.filter(function (x) { return x !== v; }); silindi++; }
      else B.kirisler.push({ no: yeniNo(B.kirisler), kat: k, bas: uc[0].slice(), son: uc[1].slice(), kesit: varsayilanKesit("kiris"), duvar: null });
    });
    if (silindi) A.toast("Aynı uçlardaki kiriş kaldırıldı (tekrar dokunma siler).");
    degisti();
  }
  function dosemeToggle(kose, eksik) {
    if (eksik && eksik.length && !dosemeBul(kose[0], D.kat)) { A.toast("Bu hücrenin " + eksik.join(", ") + " kenarında kiriş yok; önce kirişleri çizin."); return; }
    katlarHedef().forEach(function (k) {
      const d = dosemeBul(kose[0], k);
      if (d) { B.dosemeler = B.dosemeler.filter(function (x) { return x !== d; }); return; }
      if (eksikKenarlar(kose, k).length) return;
      const ornek = B.dosemeler.filter(function (x) { return x.kat === k; })[0] || B.dosemeler[0];
      B.dosemeler.push({ no: yeniNo(B.dosemeler), kat: k, kose: [kose[0].slice(), kose[1].slice()], h: ornek ? ornek.h : 0.14, kullanim: ornek ? ornek.kullanim : "konut", g_ek: ornek ? ornek.g_ek : 1.5, q: null, dagitim: "otomatik", kaplama: ornek ? ornek.kaplama || null : null });
    });
    degisti();
  }
  function dosemeleriDoldur() {
    let n = 0;
    katlarHedef().forEach(function (k) {
      hucreler().forEach(function (h) {
        if (dosemeBul(h.kose[0], k) || eksikKenarlar(h.kose, k).length) return;
        const ornek = B.dosemeler.filter(function (x) { return x.kat === k; })[0] || B.dosemeler[0];
        B.dosemeler.push({ no: yeniNo(B.dosemeler), kat: k, kose: [h.kose[0].slice(), h.kose[1].slice()], h: ornek ? ornek.h : 0.14, kullanim: ornek ? ornek.kullanim : "konut", g_ek: ornek ? ornek.g_ek : 1.5, q: null, dagitim: "otomatik", kaplama: ornek ? ornek.kaplama || null : null });
        n++;
      });
    });
    A.toast(n ? n + " döşeme eklendi." : "Dört kenarı kirişli boş hücre yok.");
    if (n) degisti();
  }
  function duvarToggle(k) {
    const yeni = k.duvar ? null : varsayilanDuvar();
    katlarHedef().forEach(function (kat) {
      B.kirisler.forEach(function (x) { if (x.kat === kat && aksEsit(x.bas, k.bas) && aksEsit(x.son, k.son)) x.duvar = yeni; });
    });
    degisti();
  }
  function nesneSil(tur, no) {
    const n = nesneBul(tur, no);
    if (!n) return;
    katlarHedef().forEach(function (k) {
      if (tur === "kolon") B.kolonlar = B.kolonlar.filter(function (c) { return !(c.kat === k && aksEsit(c.aks, n.aks)); });
      else if (tur === "kiris") B.kirisler = B.kirisler.filter(function (x) { return !(x.kat === k && aksEsit(x.bas, n.bas) && aksEsit(x.son, n.son)); });
      else B.dosemeler = B.dosemeler.filter(function (d) { return !(d.kat === k && aksEsit(d.kose[0], n.kose[0])); });
    });
    D.secim = D.secim.filter(function (s) { return nesneBul(s.tur, s.no); });
    degisti();
  }
  function secimiSil() {
    if (!D.secim.length) return;
    const l = D.secim.slice();
    D.secim = [];
    l.forEach(function (s) {
      if (s.tur === "kolon") B.kolonlar = B.kolonlar.filter(function (c) { return c.no !== s.no; });
      else if (s.tur === "kiris") B.kirisler = B.kirisler.filter(function (k) { return k.no !== s.no; });
      else if (s.tur === "doseme") B.dosemeler = B.dosemeler.filter(function (d) { return d.no !== s.no; });
    });
    degisti();
  }
  function ayniTurdenSec() {
    if (!D.secim.length) return;
    const tur = D.secim[0].tur, liste = tur === "kolon" ? B.kolonlar : tur === "kiris" ? B.kirisler : B.dosemeler;
    D.secim = liste.filter(function (x) { return x.kat === D.kat; }).map(function (x) { return { tur: tur, no: x.no }; });
    yenile();
  }
  // ---------- Katlar ----------
  function katEkle(kopyala) {
    const ust = ustKat(), h = katH(ust) || 3, yeni = ust + 1;
    if (yeni > 12) { A.toast("En çok 12 kat."); return; }
    B.katlar.forEach(function (k) { if (k.no === ust && k.ad === "Çatı") k.ad = ust + ". kat"; });
    B.katlar.push({ no: yeni, ad: "Çatı", kot: +(katKot(ust) + h).toFixed(3) });
    if (kopyala) {
      B.kolonlar.filter(function (c) { return c.kat === ust; }).forEach(function (c) { B.kolonlar.push(Object.assign(kopya(c), { no: yeniNo(B.kolonlar), kat: yeni })); });
      B.kirisler.filter(function (k) { return k.kat === ust; }).forEach(function (k) { B.kirisler.push(Object.assign(kopya(k), { no: yeniNo(B.kirisler), kat: yeni })); });
      B.dosemeler.filter(function (d) { return d.kat === ust; }).forEach(function (d) { B.dosemeler.push(Object.assign(kopya(d), { no: yeniNo(B.dosemeler), kat: yeni })); });
    }
    D.kat = yeni;
    degisti();
  }
  function katSil(no) {
    if (no < 1 || B.katlar.length <= 2) { A.toast("En az bir kat kalmalı."); return; }
    const ust = ustKat();
    if (no !== ust && !window.confirm(katAd(no) + " ve üstündeki katlar bir alt kota kayar; bu kattaki elemanlar silinir. Devam?")) return;
    const h = katH(no);
    B.kolonlar = B.kolonlar.filter(function (c) { return c.kat !== no; }).map(function (c) { if (c.kat > no) c.kat--; return c; });
    B.kirisler = B.kirisler.filter(function (k) { return k.kat !== no; }).map(function (k) { if (k.kat > no) k.kat--; return k; });
    B.dosemeler = B.dosemeler.filter(function (d) { return d.kat !== no; }).map(function (d) { if (d.kat > no) d.kat--; return d; });
    B.katlar = B.katlar.filter(function (k) { return k.no !== no; }).map(function (k) { if (k.no > no) { k.no--; k.kot = +(k.kot - h).toFixed(3); } return k; });
    D.kat = Math.min(D.kat, ustKat());
    degisti();
  }
  function katKopyalaAlttan() {
    const alt = D.kat - 1;
    if (alt < 1) { A.toast("Altta kopyalanacak kat yok."); return; }
    ["kolonlar", "kirisler", "dosemeler"].forEach(function (l) {
      B[l] = B[l].filter(function (x) { return x.kat !== D.kat; });
      B[l].filter(function (x) { return x.kat === alt; }).forEach(function (x) { B[l].push(Object.assign(kopya(x), { no: yeniNo(B[l]), kat: D.kat })); });
    });
    degisti();
  }

  // ---------- İskelet ----------
  function iskeletKur() {
    kok.innerHTML =
      '<div class="bn-ust">' +
        '<div class="bn-ust-grup"><label class="bn-gizli-etiket" for="bn-sablon">Şablon</label><select id="bn-sablon" class="girdi bn-sablon" aria-label="Şablon"><option value="">Şablon…</option></select>' +
          '<button type="button" class="dugme kucuk" id="bn-sihirbaz">Sihirbaz</button><button type="button" class="dugme kucuk" id="bn-json">JSON ⇅</button>' +
          '<button type="button" class="dugme kucuk bn-ikon" id="bn-geri" title="Geri al (Ctrl+Z)" aria-label="Geri al">↶</button><button type="button" class="dugme kucuk bn-ikon" id="bn-ileri" title="İleri al (Ctrl+Y)" aria-label="İleri al">↷</button></div>' +
        '<div class="bn-ust-grup bn-katlar" id="bn-katlar" role="group" aria-label="Katlar"></div>' +
        '<div class="bn-ust-grup bn-gorunum" id="bn-gorunum" role="group" aria-label="Görünüm"></div>' +
      "</div>" +
      '<div class="bn-govde">' +
        '<div class="bn-arac" id="bn-arac" role="toolbar" aria-label="Araçlar"></div>' +
        '<div class="bn-sahne-kutu" id="bn-sahne-kutu"><svg id="bn-svg" class="bn-svg" role="img" aria-label="3B bina sahnesi" preserveAspectRatio="xMidYMid meet"></svg>' +
          '<div class="bn-sahne-ust" id="bn-sahne-ust"></div>' +
          '<div class="bn-sahne-alt"><label class="bn-onay"><input type="checkbox" id="bn-tum-katlar"> Tüm katlara uygula</label>' +
            '<button type="button" class="dugme kucuk" id="bn-doldur">Döşemeleri doldur</button><button type="button" class="dugme kucuk" id="bn-kat-kopyala">Alt katı kopyala</button></div>' +
          '<div id="bn-formul" class="bn-formul gizli"></div>' +
        "</div>" +
        '<details class="bn-panel" id="bn-panel" open><summary>Özellikler</summary><div class="bn-panel-sekmeler" id="bn-panel-sekmeler"></div><div class="bn-panel-icerik" id="bn-panel-icerik"></div></details>' +
      "</div>" +
      '<div class="bn-durum" id="bn-durum"></div>' +
      '<div id="bn-uyarilar" aria-live="polite"></div>' +
      '<div class="bn-hat-kutu"><div class="bn-hat" id="bn-hat"></div><button type="button" class="dugme ana bn-coz" id="bn-coz">Çöz ▶</button></div>' +
      '<div id="bn-hata" aria-live="polite"></div>' +
      '<div class="bn-sonuc" id="bn-sonuc"></div>' +
      '<dialog id="bn-sihirbaz-dlg" class="bn-dlg"><form method="dialog" id="bn-sihirbaz-form"></form></dialog>' +
      '<dialog id="bn-json-dlg" class="bn-dlg"><h2>Bina JSON</h2><textarea id="bn-json-metin" class="girdi" rows="14" spellcheck="false" aria-label="Bina JSON"></textarea><div id="bn-json-hata"></div>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" id="bn-json-uygula">JSON\'dan uygula</button><button type="button" class="dugme" id="bn-json-kopyala">Kopyala</button>' +
        '<button type="button" class="dugme" id="bn-json-indir">İndir</button><label class="dugme bn-dosya">Dosyadan yükle<input type="file" id="bn-json-dosya" accept=".json,application/json"></label>' +
        '<button type="button" class="dugme" id="bn-json-kapat">Kapat</button></div></dialog>';
    ["sablon", "sihirbaz", "json", "geri", "ileri", "katlar", "gorunum", "arac", "sahne-kutu", "svg", "sahne-ust", "tum-katlar", "doldur", "kat-kopyala", "formul", "panel", "panel-sekmeler", "panel-icerik",
      "durum", "uyarilar", "hat", "coz", "hata", "sonuc", "sihirbaz-dlg", "sihirbaz-form", "json-dlg", "json-metin", "json-hata", "json-uygula", "json-kopyala", "json-indir", "json-dosya", "json-kapat"].forEach(function (id) {
      ref[id.replace(/-([a-z])/g, function (_, c) { return c.toUpperCase(); })] = document.getElementById("bn-" + id);
    });
    if (window.innerWidth < 700) ref.panel.removeAttribute("open");
  }
  function panelAc() { ref.panel.open = true; if (window.innerWidth < 700) ref.panel.scrollIntoView({ block: "start", behavior: azHareket() ? "auto" : "smooth" }); }
  let sonUyarilar = [];

  function yenile() {
    sonUyarilar = dogrula().uyari;
    ustCubukCiz();
    sahneCiz();
    panelCiz();
    durumCiz();
    hatCiz();
    if (ref.sonuc && sonEski && !ref.sonuc.querySelector(".bn-eski:not(.gizli)")) { const e = ref.sonuc.querySelector(".bn-eski"); if (e) e.classList.remove("gizli"); }
  }
  function ustCubukCiz() {
    ref.katlar.innerHTML = '<span class="bn-etiket">Kat:</span>' + B.katlar.map(function (k) {
      return '<button type="button" class="bn-cip' + (k.no === D.kat ? " aktif" : "") + '" data-kat="' + k.no + '" aria-pressed="' + (k.no === D.kat) + '">' + kacis(k.ad) + "</button>";
    }).join("") + '<div class="bn-menu"><button type="button" class="bn-cip bn-cip-ekle" id="bn-kat-ekle" aria-haspopup="true">+Kat ▾</button>' +
      '<div class="bn-menu-liste gizli" id="bn-kat-menu"><button type="button" data-kat-islem="kopyala">Üsttekini kopyala</button><button type="button" data-kat-islem="bos">Boş kat</button><button type="button" data-kat-islem="sil">Son katı sil</button></div></div>';
    gorunumDugmeleri();
    ref.arac.innerHTML = ARACLAR.map(function (a) {
      return '<button type="button" class="bn-arac-d' + (D.arac === a[0] ? " aktif" : "") + '" data-arac="' + a[0] + '" aria-pressed="' + (D.arac === a[0]) + '" title="' + kacis(a[2] + " (" + a[3] + ")") + '"><span class="bn-arac-sim" aria-hidden="true">' + a[1] + '</span><span class="bn-arac-ad">' + kacis(a[2]) + "</span></button>";
    }).join("") + '<button type="button" class="bn-arac-d' + (D.panelSekme === "kutuphane" ? " aktif" : "") + '" data-arac="kutuphane" title="Kütüphane"><span class="bn-arac-sim" aria-hidden="true">📚</span><span class="bn-arac-ad">Kütüphane</span></button>';
    ref.tumKatlar.checked = D.tumKatlar;
    ref.geri.disabled = !gecmis.geri.length; ref.ileri.disabled = !gecmis.ileri.length;
    const ipucu = { sec: "Nesneye dokun: seç (ikinci dokunma çoklu seçim); uzun bas: özellikler. Sürükle: döndür; tekerlek/iki parmak: yakınlaştır.",
      kolon: "Etkin katın aks kesişimine (○) dokun: kolon ekle/kaldır.", kiris: "İki kesişime art arda dokun ya da sürükle: kiriş. Arada kolon yoksa sürekli kiriş.",
      doseme: "Hücredeki + işaretine dokun: döşeme. Kırmızı kesikli hücrenin bir kenarında kiriş yok.", duvar: "Kirişe dokun: duvar ekle/kaldır (türü panelde).", sil: "Nesneye dokun: sil." };
    ref.sahneUst.innerHTML = '<span class="bn-ipucu">' + kacis(ipucu[D.arac] || "") + "</span>" + (D.firca ? '<span class="bn-firca">Fırça: ' + kacis(D.firca) + ' <button type="button" class="bn-firca-kapat" id="bn-firca-kapat" aria-label="Fırçayı bırak">✕</button></span>' : "");
  }
  function gorunumDugmeleri() {
    const g = kamera ? kamera.gorunum : "3b";
    ref.gorunum.innerHTML = '<span class="bn-etiket">Görünüm:</span>' + Object.keys(GORUNUM_AD).map(function (k) {
      return '<button type="button" class="bn-cip' + (g === k ? " aktif" : "") + '" data-gorunum="' + k + '" aria-pressed="' + (g === k) + '">' + GORUNUM_AD[k] + "</button>";
    }).join("") + '<button type="button" class="bn-cip bn-ikon" data-gorunum="sifirla" title="Yakınlaştırmayı sıfırla" aria-label="Yakınlaştırmayı sıfırla">⟲</button>';
  }
  function durumCiz() {
    const nk = B.kolonlar.length, nr = B.kirisler.length, nd = B.dosemeler.length, nkat = B.katlar.length - 1;
    ref.durum.textContent = nk + " kolon · " + nr + " kiriş · " + nd + " döşeme · " + nkat + " kat · " + (SON && !sonEski && SON.veri.ag ? SON.veri.ag.sd_sayisi + " SD" : sdTahmini() + " SD (tahmin)") +
      (B.akslar.x.length && B.akslar.y.length ? " · " + B.akslar.x.length + "×" + B.akslar.y.length + " aks" : "");
    const u = sonUyarilar;
    ref.uyarilar.innerHTML = u.length ? '<div class="bn-uyari-kutu"><strong>⚠ ' + u.length + " uyarı:</strong> " + u.slice(0, 4).map(function (x) { return '<span class="bn-uyari-satir" data-uyari-kat="' + x.kat + '">' + kacis(x.metin) + "</span>"; }).join(" ") + (u.length > 4 ? " …" : "") + "</div>" : "";
  }
  // ---------- Özellik paneli ----------
  function panelCiz() {
    const sekmeler = [["nesne", D.secim.length ? "Seçili (" + D.secim.length + ")" : "Nesne"], ["akslar", "Akslar"], ["bina", "Bina / temel"], ["kutuphane", "Kütüphane"]];
    ref.panelSekmeler.innerHTML = sekmeler.map(function (s) { return '<button type="button" class="bn-psek' + (D.panelSekme === s[0] ? " aktif" : "") + '" data-psek="' + s[0] + '">' + kacis(s[1]) + "</button>"; }).join("");
    let h = "";
    if (D.panelSekme === "nesne") h = nesnePaneli();
    else if (D.panelSekme === "akslar") h = aksPaneli();
    else if (D.panelSekme === "bina") h = binaPaneli();
    else h = kutuphanePaneli();
    ref.panelIcerik.innerHTML = h;
  }
  function kesitSecenekleri(tur, secili) {
    const l = Object.keys(B.kesitler).map(function (k) { const o = kesitOz(k); return [k, k + (o ? (o.tip === "profil" ? " (" + o.profil + ")" : " (" + Math.round(o.b * 100) + "×" + Math.round(o.h * 100) + " cm)") : "")]; });
    return secenekler(l.concat([["__yeni", "Yeni kesit…"]]), secili);
  }
  function alanH(etiket, icerik) { return '<label class="bn-alan"><span>' + kacis(etiket) + "</span>" + icerik + "</label>"; }
  function nesnePaneli() {
    if (!D.secim.length) return '<p class="not">Sahnede bir nesneye dokunun (Seç aracı). Kolon, kiriş ve döşeme özellikleri burada düzenlenir.</p>';
    const s0 = D.secim[0], n = nesneBul(s0.tur, s0.no);
    if (!n) return "";
    const cok = D.secim.length > 1 ? '<p class="not">' + D.secim.length + " nesne seçili; değişiklik hepsine uygulanır.</p>" : "";
    let h = "";
    if (s0.tur === "kolon") {
      h += '<h3 class="bn-pbaslik">Kolon S-' + kacis(adres(n.aks)) + "/k" + n.kat + "</h3>" + cok;
      h += alanH("Kesit", '<select class="girdi" data-oz="kesit">' + kesitSecenekleri("kolon", n.kesit) + "</select>");
      h += alanH("Yön (güçlü boyut)", '<select class="girdi" data-oz="yon">' + secenekler([["x", "X (h boyutu X yönünde)"], ["y", "Y (h boyutu Y yönünde)"]], n.yon) + "</select>");
      h += kesitKarti(n.kesit);
    } else if (s0.tur === "kiris") {
      h += '<h3 class="bn-pbaslik">Kiriş K-' + kacis(adres(n.bas) + "→" + adres(n.son)) + "/k" + n.kat + " · L = " + f2(kirisUzunluk(n)) + " m</h3>" + cok;
      h += alanH("Kesit", '<select class="girdi" data-oz="kesit">' + kesitSecenekleri("kiris", n.kesit) + "</select>");
      const dl = [["", "Duvar yok"]].concat(Object.keys(B.duvarlar).map(function (k) { const kk = B.duvarlar[k].kutuphane || k; const kt = (KUT.duvarlar || []).filter(function (x) { return x.ad === kk; })[0]; return [k, (kt ? kt.etiket : kk) + " (" + f2(duvarW(k)) + " kN/m²)"]; })).concat([["__yeni", "Başka duvar türü…"]]);
      h += alanH("Duvar", '<select class="girdi" data-oz="duvar">' + secenekler(dl, n.duvar || "") + "</select>");
      const ekG = B.ek_yukler.filter(function (e) { return e.tur === "kiris" && e.kiris === n.no && e.durum === "G"; }).reduce(function (t, e) { return t + (+e.q || 0); }, 0);
      const ekQ = B.ek_yukler.filter(function (e) { return e.tur === "kiris" && e.kiris === n.no && e.durum === "Q"; }).reduce(function (t, e) { return t + (+e.q || 0); }, 0);
      h += '<div class="bn-iki">' + alanH("Ek yük G (kN/m, aşağı +)", '<input class="girdi" inputmode="decimal" data-oz="ekG" value="' + kacis(ekG || "") + '">') + alanH("Ek yük Q (kN/m)", '<input class="girdi" inputmode="decimal" data-oz="ekQ" value="' + kacis(ekQ || "") + '">') + "</div>";
      h += kesitKarti(n.kesit);
    } else {
      h += '<h3 class="bn-pbaslik">Döşeme D-' + kacis(adres(n.kose[0]) + "/" + adres(n.kose[1])) + "/k" + n.kat + "</h3>" + cok;
      const lx = Math.abs(aksX(n.kose[1][0]) - aksX(n.kose[0][0])), ly = Math.abs(aksY(n.kose[1][1]) - aksY(n.kose[0][1])), m = Math.max(lx, ly) / Math.min(lx, ly);
      h += '<p class="not">lₓ = ' + f2(lx) + " m, l_y = " + f2(ly) + " m, m = " + f2(m) + (m <= 2 ? " ≤ 2 → çift doğrultulu" : " > 2 → tek doğrultulu") + "</p>";
      h += '<div class="bn-iki">' + alanH("Kalınlık h (m)", '<input class="girdi" inputmode="decimal" data-oz="h" value="' + kacis(n.h) + '">') +
        alanH("Ek sabit yük g_ek (kN/m²)", '<input class="girdi" inputmode="decimal" data-oz="g_ek" value="' + kacis(n.g_ek) + '">') + "</div>";
      h += alanH("Kullanım sınıfı (TS 498 q)", '<select class="girdi" data-oz="kullanim">' + secenekler((KUT.kullanim_siniflari || []).map(function (k) { return [k.ad, k.etiket + " — q = " + f1(k.q) + " kN/m²" + (k.dogrulandi === false ? " (doğrulanacak)" : "")]; }), n.kullanim) + "</select>");
      h += alanH("Kaplama takımı (g_ek önerisi)", '<select class="girdi" data-oz="kaplama">' + secenekler([["", "—"]].concat((KUT.kaplamalar || []).map(function (k) { return [k.ad, k.etiket + " (" + f2(k.g) + " kN/m²)"]; })), n.kaplama || "") + "</select>");
      h += '<div class="bn-iki">' + alanH("q (kN/m²; boş = sınıf değeri)", '<input class="girdi" inputmode="decimal" data-oz="q" value="' + (n.q == null ? "" : kacis(n.q)) + '">') +
        alanH("Dağıtım", '<select class="girdi" data-oz="dagitim">' + secenekler([["otomatik", "Otomatik (m ≤ 2 çift)"], ["cift", "Çift doğrultulu"], ["tek", "Tek doğrultulu"]], n.dagitim) + "</select>") + "</div>";
      h += '<p class="not">g = 25·h + g_ek = ' + f2(GAMMA_B * (+n.h || 0) + (+n.g_ek || 0)) + " kN/m²; q = " + f2(n.q != null ? +n.q : kullanimQ(n.kullanim)) + " kN/m²</p>";
    }
    h += '<div class="dugmeler"><button type="button" class="dugme kucuk" id="bn-ayni-tur">Aynı türden tümünü seç (bu kat)</button><button type="button" class="dugme kucuk" id="bn-secim-sil">Seçileni sil</button>' +
      (SON && !sonEski ? '<button type="button" class="dugme kucuk ana" id="bn-yuk-yolu">Yük yolunu izle</button>' : "") + "</div>";
    return h;
  }
  function kesitKarti(ad) {
    const o = kesitOz(ad);
    if (!o) return "";
    const m = malzemeKart(o.malzeme);
    let h = '<div class="bn-kart"><b>' + kacis(ad) + "</b> · " + (o.tip === "profil" ? kacis(o.profil) : Math.round(o.b * 100) + "×" + Math.round(o.h * 100) + " cm") + " · " + kacis(o.malzeme) +
      (m.fck != null ? " (f_ck = " + m.fck + " MPa, E_c = " + fmt(m.Ec) + " MPa)" : m.Fy != null ? " (F_y = " + m.Fy + " MPa, E = " + fmt(m.E) + " MPa)" : "") + "<br>" +
      "A = " + fmt(o.A) + " m² · I_y = " + fmt(o.Iy) + " m⁴ · I_z = " + fmt(o.Iz) + " m⁴ · J ≈ " + fmt(o.J) + " m⁴</div>";
    return h;
  }
  function aksPaneli() {
    const tablo = function (e, baslik) {
      return '<section class="se-bolum"><div class="se-bolum-ust"><h3>' + baslik + '</h3><button type="button" class="dugme kucuk" data-aks-ekle="' + e + '">+ aks</button></div>' +
        '<table class="se-tablo"><thead><tr><th>Ad</th><th>Konum (m)</th><th></th></tr></thead><tbody>' + B.akslar[e].map(function (a, i) {
          return '<tr><td data-e="Ad"><input class="se-g" data-aks="' + e + '" data-i="' + i + '" data-a="ad" value="' + kacis(a.ad) + '" aria-label="Aks adı"></td>' +
            '<td data-e="Konum (m)"><input class="se-g" inputmode="decimal" data-aks="' + e + '" data-i="' + i + '" data-a="konum" value="' + kacis(a.konum) + '" aria-label="Aks konumu"></td>' +
            '<td class="se-sil-h"><button type="button" class="se-sil" data-aks-sil="' + e + ":" + i + '" aria-label="Aksı sil">✕</button></td></tr>';
        }).join("") + "</tbody></table></section>";
    };
    return '<p class="not">Harfli akslar X (sağa), sayılı akslar Y (derinlik). “+ aks” son aralığı kopyalar; aks silinince bağlı elemanlar da silinir.</p>' + tablo("x", "X aksları (A, B, C…)") + tablo("y", "Y aksları (1, 2, 3…)") +
      '<section class="se-bolum"><h3>Katlar</h3><table class="se-tablo"><thead><tr><th>No</th><th>Ad</th><th>Kot (m)</th><th></th></tr></thead><tbody>' + B.katlar.map(function (k, i) {
        return '<tr><td data-e="No">' + k.no + '</td><td data-e="Ad"><input class="se-g" data-kat-i="' + i + '" data-a="ad" value="' + kacis(k.ad) + '" aria-label="Kat adı"></td>' +
          '<td data-e="Kot (m)"><input class="se-g" inputmode="decimal" data-kat-i="' + i + '" data-a="kot" value="' + kacis(k.kot) + '"' + (k.no === 0 ? " disabled" : "") + ' aria-label="Kat kotu"></td>' +
          '<td class="se-sil-h">' + (k.no >= 1 ? '<button type="button" class="se-sil" data-kat-sil="' + k.no + '" aria-label="Katı sil">✕</button>' : "") + "</td></tr>";
      }).join("") + "</tbody></table></section>";
  }
  function binaPaneli() {
    const t = B.temeller, z = t.zemin || {}, v = t.varsayilan || {};
    return alanH("Başlık", '<input class="girdi" data-bina="baslik" value="' + kacis(B.baslik || "") + '">') +
      alanH("Sistem", '<select class="girdi" data-bina="sistem">' + secenekler([["betonarme", "Betonarme (TS 500)"], ["celik", "Çelik (ÇYTHYE)"]], B.sistem) + "</select>") +
      '<h3 class="bn-pbaslik">Temel ve zemin</h3>' +
      alanH("Temel tipi", '<select class="girdi" data-temel="tip">' + secenekler([["tekil", "Tekil temel"]], t.tip) + "</select>") +
      '<div class="bn-uc">' + alanH("B (m)", '<input class="girdi" inputmode="decimal" data-temel-v="B" value="' + kacis(v.B) + '">') + alanH("L (m)", '<input class="girdi" inputmode="decimal" data-temel-v="L" value="' + kacis(v.L) + '">') + alanH("h (m)", '<input class="girdi" inputmode="decimal" data-temel-v="h" value="' + kacis(v.h) + '">') + "</div>" +
      '<div class="bn-iki">' + alanH("q_em (kN/m²)", '<input class="girdi" inputmode="decimal" data-zemin="q_em" value="' + kacis(z.q_em) + '">') + alanH("k₀ (kN/m³)", '<input class="girdi" inputmode="decimal" data-zemin="k0" value="' + kacis(z.k0) + '">') + "</div>" +
      alanH("Mesnet modeli", '<select class="girdi" data-temel="mesnet">' + secenekler([["ankastre", "Ankastre"], ["mafsal", "Mafsal (ux, uy, uz)"], ["elastik", "Elastik (k₀ ile yaylar)"]], t.mesnet) + "</select>") +
      alanH("Kombinasyon kümesi", '<select class="girdi" data-bina="kombinasyon_kumesi">' + secenekler([["ts500", "TS 500"], ["cythye_ydkt", "ÇYTHYE YDKT"], ["cythye_gkt", "ÇYTHYE GKT"]], B.kombinasyon_kumesi) + "</select>") +
      '<p class="not">Deprem (TBDY 2018) parametreleri Dilim 2’de hesaba girer; JSON’da saklanır. Uygulama öğretim ve ön boyutlandırma içindir, tasarım aracı değildir.</p>';
  }
  function kutuphanePaneli() {
    const ml = KUT.malzemeler || {};
    let h = '<h3 class="bn-pbaslik">Malzemeler</h3><div class="bn-kartlar">';
    (ml.beton || []).forEach(function (m) { h += '<div class="bn-kart"><b>' + kacis(m.ad) + "</b> f_ck = " + m.fck + " MPa · E_c = " + fmt(m.Ec) + " MPa · γ = " + m.gamma + " kN/m³" + (m.dogrulandi === false ? ' <span class="se-rozet">doğrulanacak</span>' : "") + "</div>"; });
    (ml.celik || []).forEach(function (m) { h += '<div class="bn-kart"><b>' + kacis(m.ad) + "</b> F_y = " + m.Fy + " MPa · F_u = " + m.Fu + " MPa · E = " + fmt(m.E) + " MPa" + (m.dogrulandi === false ? ' <span class="se-rozet">doğrulanacak</span>' : "") + "</div>"; });
    (ml.donati || []).forEach(function (m) { h += '<div class="bn-kart"><b>' + kacis(m.ad) + "</b> f_yk = " + m.fyk + " MPa · E_s = " + fmt(m.Es) + " MPa" + (m.dogrulandi === false ? ' <span class="se-rozet">doğrulanacak</span>' : "") + "</div>"; });
    h += "</div>";
    h += '<h3 class="bn-pbaslik">Kesitler (bu bina)</h3><div class="bn-kartlar">';
    Object.keys(B.kesitler).forEach(function (ad) {
      const o = kesitOz(ad);
      if (!o) return;
      h += '<div class="bn-kart' + (D.firca === ad ? " bn-kart-firca" : "") + '"><b>' + kacis(ad) + "</b> " + (o.tip === "profil" ? kacis(o.profil) : Math.round(o.b * 100) + "×" + Math.round(o.h * 100) + " cm") + " · " + kacis(o.malzeme) +
        "<br><small>A = " + fmt(o.A) + " m², I_y = " + fmt(o.Iy) + ", I_z = " + fmt(o.Iz) + ", J ≈ " + fmt(o.J) + " m⁴" + (o.tip === "profil" ? "" : " — I = b·h³/12, J ≈ β·b³·h") + "</small>" +
        '<div class="dugmeler"><button type="button" class="dugme kucuk" data-firca="' + kacis(ad) + '">' + (D.firca === ad ? "Fırçayı bırak" : "Fırça") + '</button><button type="button" class="dugme kucuk" data-kesit-sil="' + kacis(ad) + '">Sil</button></div></div>';
    });
    h += "</div>";
    h += '<h3 class="bn-pbaslik">Yeni kesit</h3><div class="bn-yeni-kesit">' +
      '<div class="bn-iki">' + alanH("Ad", '<input class="girdi" id="bn-yk-ad" placeholder="örn. S30x60">') + alanH("Tip", '<select class="girdi" id="bn-yk-tip">' + secenekler([["dikdortgen", "Dikdörtgen (cm)"], ["profil", "Çelik profil"]], B.sistem === "celik" ? "profil" : "dikdortgen") + "</select>") + "</div>" +
      '<div class="bn-uc" id="bn-yk-dik"' + (B.sistem === "celik" ? ' style="display:none"' : "") + ">" + alanH("b (cm)", '<input class="girdi" inputmode="decimal" id="bn-yk-b" value="30">') + alanH("h (cm)", '<input class="girdi" inputmode="decimal" id="bn-yk-h" value="60">') +
        alanH("Malzeme", '<select class="girdi" id="bn-yk-malz">' + secenekler((ml.beton || []).map(function (m) { return [m.ad, m.ad]; }), "C30/37") + "</select>") + "</div>" +
      '<div class="bn-iki" id="bn-yk-prof"' + (B.sistem === "celik" ? "" : ' style="display:none"') + ">" + alanH("Profil", '<select class="girdi" id="bn-yk-profil">' + Object.keys((KUT.kesit_katalogu || {}).profiller || {}).map(function (g) {
        return '<optgroup label="' + g + '">' + ((KUT.kesit_katalogu.profiller[g]) || []).map(function (p) { return '<option value="' + kacis(p) + '">' + kacis(p) + "</option>"; }).join("") + "</optgroup>"; }).join("") + "</select>") +
        alanH("Çelik", '<select class="girdi" id="bn-yk-celik">' + secenekler((ml.celik || []).map(function (m) { return [m.ad, m.ad]; }), "S275") + "</select>") + "</div>" +
      '<div class="dugmeler"><button type="button" class="dugme kucuk ana" id="bn-yk-ekle">Kesiti ekle</button></div></div>';
    h += '<h3 class="bn-pbaslik">Duvar türleri</h3><div class="bn-kartlar">' + (KUT.duvarlar || []).map(function (d) { return '<div class="bn-kart">' + kacis(d.etiket) + " · " + f2(d.w) + " kN/m²</div>"; }).join("") + "</div>";
    h += '<h3 class="bn-pbaslik">Hareketli yükler (TS 498:2021 Çizelge 6)</h3>' + tabloH(["Sınıf", "q (kN/m²)", "Kaynak"], (KUT.kullanim_siniflari || []).map(function (k) { return [k.etiket, f1(k.q), k.kaynak || ""]; }));
    return h;
  }
  function yeniKesitEkle() {
    const ad = (document.getElementById("bn-yk-ad").value || "").trim().replace(/\s+/g, "");
    const tip = document.getElementById("bn-yk-tip").value;
    if (!ad) { A.toast("Kesite bir ad verin."); return; }
    if (B.kesitler[ad]) { A.toast("Bu ad kullanılıyor."); return; }
    if (tip === "profil") {
      const p = document.getElementById("bn-yk-profil").value, c = document.getElementById("bn-yk-celik").value;
      if (!B.malzemeler[c]) B.malzemeler[c] = { kutuphane: c };
      B.kesitler[ad] = { tip: "profil", profil: p, malzeme: c };
    } else {
      const b = sayiOku(document.getElementById("bn-yk-b").value), h = sayiOku(document.getElementById("bn-yk-h").value);
      if (!b || !h || b <= 0 || h <= 0) { A.toast("b ve h pozitif sayı olmalı (cm)."); return; }
      const m = document.getElementById("bn-yk-malz").value, mad = m.split("/")[0];
      if (!B.malzemeler[mad]) B.malzemeler[mad] = { kutuphane: m };
      if (!B.malzemeler.B420C) B.malzemeler.B420C = { kutuphane: "B420C" };
      B.kesitler[ad] = { tip: "dikdortgen", b: b / 100, h: h / 100, malzeme: mad, donati: "B420C", pas: 0.03 };
    }
    D.firca = ad;
    A.toast(ad + " eklendi; fırça etkin: elemanlara dokununca atanır.");
    degisti();
  }
  // ---------- Sihirbaz ----------
  function sihirbazAc() {
    const celik = B.sistem === "celik";
    const xs = B.akslar.x.slice(1).map(function (a, i) { return +(a.konum - B.akslar.x[i].konum).toFixed(2); }).join(" ");
    const ys = B.akslar.y.slice(1).map(function (a, i) { return +(a.konum - B.akslar.y[i].konum).toFixed(2); }).join(" ");
    ref.sihirbazForm.innerHTML = "<h2>Bina sihirbazı</h2>" +
      alanH("Sistem", '<select class="girdi" name="sistem">' + secenekler([["betonarme", "Betonarme"], ["celik", "Çelik"]], B.sistem) + "</select>") +
      '<div class="bn-iki">' + alanH("X aralıkları (m)", '<input class="girdi" name="x" value="' + kacis(xs || "5 4") + '" placeholder="5 4 5">') + alanH("Y aralıkları (m)", '<input class="girdi" name="y" value="' + kacis(ys || "4") + '" placeholder="4 4">') + "</div>" +
      '<div class="bn-iki">' + alanH("Kat sayısı", '<input class="girdi" name="katSayisi" inputmode="numeric" value="' + ustKat() + '">') + alanH("Kat yüksekliği (m)", '<input class="girdi" name="katH" inputmode="decimal" value="' + kacis(katH(1) || 3) + '">') + "</div>" +
      '<div class="bn-iki bn-sih-dik"' + (celik ? ' style="display:none"' : "") + ">" + alanH("Kolon b×h (cm)", '<input class="girdi" name="kolon" value="40 40">') + alanH("Kiriş b×h (cm)", '<input class="girdi" name="kiris" value="25 50">') + "</div>" +
      '<div class="bn-iki bn-sih-prof"' + (celik ? "" : ' style="display:none"') + ">" + alanH("Kolon profili", '<input class="girdi" name="kolonProfil" value="HEB 300">') + alanH("Kiriş profili", '<input class="girdi" name="kirisProfil" value="IPE 300">') + "</div>" +
      '<div class="bn-iki">' + alanH("Döşeme kalınlığı (m)", '<input class="girdi" name="dosemeH" inputmode="decimal" value="0.14">') + alanH("Kullanım", '<select class="girdi" name="kullanim">' + secenekler((KUT.kullanim_siniflari || []).map(function (k) { return [k.ad, k.etiket]; }), "konut") + "</select>") + "</div>" +
      '<div class="bn-iki">' + alanH("Duvar", '<select class="girdi" name="duvar">' + secenekler([["dis", "Dış kirişlerde"], ["hepsi", "Bütün kirişlerde"], ["yok", "Yok"]], "dis") + "</select>") +
        alanH("Duvar türü", '<select class="girdi" name="duvarTip">' + secenekler((KUT.duvarlar || []).map(function (d) { return [d.ad, d.etiket]; }), "tugla-delikli-19") + "</select>") + "</div>" +
      '<div class="dugmeler"><button type="submit" class="dugme ana" value="tamam">Binayı üret</button><button type="button" class="dugme" value="iptal" id="bn-sih-iptal">Vazgeç</button></div>';
    const dlg = ref.sihirbazDlg;
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
  }
  function sihirbazUret() {
    const f = ref.sihirbazForm, v = function (ad) { const el = f.elements[ad]; return el ? el.value : ""; };
    const cift = function (t, d1, d2) { const a = aralikOku(t); return a.length >= 2 ? [a[0] / 100, a[1] / 100] : [d1, d2]; };
    const kol = cift(v("kolon"), 0.4, 0.4), kir = cift(v("kiris"), 0.25, 0.5);
    const p = { sistem: v("sistem"), x: aralikOku(v("x")), y: aralikOku(v("y")), katSayisi: parseInt(v("katSayisi"), 10) || 1, katH: sayiOku(v("katH")) || 3,
      kolonB: kol[0], kolonH: kol[1], kirisB: kir[0], kirisH: kir[1], kolonProfil: v("kolonProfil"), kirisProfil: v("kirisProfil"),
      dosemeH: sayiOku(v("dosemeH")) || 0.14, kullanim: v("kullanim"), duvar: v("duvar"), duvarTip: v("duvarTip") };
    if (p.sistem === "betonarme") { p.kolonAd = "S" + Math.round(kol[0] * 100) + "x" + Math.round(kol[1] * 100); p.kirisAd = "K" + Math.round(kir[0] * 100) + "x" + Math.round(kir[1] * 100); }
    else { p.kolonAd = p.kolonProfil.replace(/\s+/g, ""); p.kirisAd = p.kirisProfil.replace(/\s+/g, ""); }
    binayiAyarla(binaUret(p), "Bina üretildi: " + p.x.length + "×" + p.y.length + " aks, " + p.katSayisi + " kat.");
    ref.sablon.value = "";
  }
  // ---------- JSON ----------
  function jsonAc() {
    ref.jsonMetin.value = JSON.stringify(B, null, 2);
    hataGoster(ref.jsonHata, []);
    const dlg = ref.jsonDlg;
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
  }
  function jsonUygula() {
    let m;
    try { m = JSON.parse(ref.jsonMetin.value); }
    catch (e) { hataGoster(ref.jsonHata, ["JSON okunamadı: " + e.message]); return; }
    try { binayiAyarla(m, "JSON uygulandı."); }
    catch (e) { hataGoster(ref.jsonHata, [e.message]); return; }
    ref.sablon.value = "";
    if (ref.jsonDlg.close) ref.jsonDlg.close(); else ref.jsonDlg.removeAttribute("open");
  }
  function jsonIndir() {
    const blob = new Blob([JSON.stringify(B, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = (B.baslik || "bina").replace(/[^\wğüşöçıİĞÜŞÖÇ-]+/g, "_") + ".json";
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }
  // ---------- Şablonlar ----------
  let sablonlar = YERLESIK_KUTUPHANE.sablonlar.slice();
  function sablonListesi() {
    ref.sablon.innerHTML = '<option value="">Şablon…</option>' + sablonlar.map(function (s) { return '<option value="' + kacis(s.ad) + '">' + kacis(s.baslik) + "</option>"; }).join("");
  }
  function sablonYukle(ad) {
    if (!ad) return Promise.resolve();
    const yerel = function () {
      if (YERLESIK_SABLON[ad]) { binayiAyarla(YERLESIK_SABLON[ad](), "Şablon yüklendi (yerleşik)."); return; }
      A.toast("Şablon bulunamadı: " + ad);
    };
    return A.motorIstegi({ islem: "bina_sablon", girdi: { ad: ad } }).then(function (y) {
      if (!y || y.hata || !y.bina) { yerel(); return; }
      binayiAyarla(y.bina, "Şablon yüklendi: " + (y.bina.baslik || ad));
    }, yerel);
  }
  function kutuphaneyiAl() {
    return A.motorIstegi({ islem: "bina_kutuphane", girdi: {} }).then(function (y) {
      if (!y || y.hata) return;
      KUT = Object.assign({}, YERLESIK_KUTUPHANE, y);
      if (!KUT.kesit_katalogu || !KUT.kesit_katalogu.profil_ozellikleri) KUT.kesit_katalogu = Object.assign({}, YERLESIK_KUTUPHANE.kesit_katalogu, KUT.kesit_katalogu || {});
      if (Array.isArray(y.sablonlar) && y.sablonlar.length) { sablonlar = y.sablonlar; sablonListesi(); }
      if (B) panelCiz();
    }, function () { /* motor yok: yerleşik kütüphane */ });
  }
  function sablonlariAl() {
    return A.motorIstegi({ islem: "bina_sablonlar", girdi: {} }).then(function (y) {
      if (y && !y.hata && Array.isArray(y.sablonlar) && y.sablonlar.length) { sablonlar = y.sablonlar; sablonListesi(); }
    }, function () { /* yerleşik */ });
  }

  // ---------- Hesap hattı ve çözüm ----------
  const HAT = [["Yükler", 2], ["Yük durumları G Q", 6], ["Kombinasyonlar", 9], ["Zarf", 9], ["Tasarım (yakında)", 0]];
  function hatCiz() {
    const tamam = SON && !sonEski;
    ref.hat.innerHTML = HAT.map(function (h, i) {
      const pasif = h[1] === 0;
      return (i ? '<span class="bn-hat-ok" aria-hidden="true">→</span>' : "") + '<button type="button" class="bn-hat-adim' + (tamam && !pasif ? " tamam" : "") + (pasif ? " pasif" : "") + '" data-adim="' + h[1] + '"' + (pasif ? " disabled" : "") + ">" +
        (tamam && !pasif ? "✓ " : "") + kacis(h[0]) + (i === 2 && tamam ? " " + Object.keys(SON.veri.sonuclar || {}).length : "") + "</button>";
    }).join("");
    ref.coz.disabled = D.cozuluyor;
    ref.coz.textContent = D.cozuluyor ? "Çözülüyor…" : "Çöz ▶";
  }
  function coz() {
    if (D.cozuluyor) return;
    const dg = dogrula();
    hataGoster(ref.hata, dg.hata, dg.hata.length > 1 ? "Modelde düzeltilecek yerler var:" : "");
    if (dg.hata.length) { ref.hata.scrollIntoView({ block: "nearest", behavior: "smooth" }); return; }
    if (dg.uyari.length && !window.confirm(dg.uyari.length + " uyarı var (ör. " + dg.uyari[0].metin + "). Yine de çözülsün mü?")) return;
    D.cozuluyor = true; hatCiz();
    A.motorIstegi({ islem: "bina_coz", girdi: { bina: kopya(B) } }).then(function (y) {
      if (!y || y.hata) { SON = null; hataGoster(ref.hata, [y && y.hata ? y.hata : "Boş yanıt."], y && y.hata_turu === "ic" ? "Motor hatası" : "Bina çözülemedi"); sonucuTemizle(); return; }
      if (!y.veri || !y.veri.ag || !y.veri.durumlar) { hataGoster(ref.hata, ["Motor yanıtında “veri.ag” ya da “veri.durumlar” yok (şema §4)."], "Beklenmeyen yanıt"); return; }
      hataGoster(ref.hata, []);
      SON = { y: y, veri: y.veri }; sonEski = false; D.akisHedef = null; D.sankeySecim = null; D.sekme = "akis";
      if (!(D.diyagramDurum in (y.veri.sonuclar || {})) && D.diyagramDurum !== "zarf" && !(D.diyagramDurum in y.veri.durumlar)) D.diyagramDurum = Object.keys(y.veri.sonuclar || {})[0] || "G";
      if (!(D.deformeDurum in (y.veri.sonuclar || {})) && !(D.deformeDurum in y.veri.durumlar)) D.deformeDurum = Object.keys(y.veri.sonuclar || {})[0] || "G";
      sonucuCiz();
      yenile();
      ref.sonuc.scrollIntoView({ block: "start", behavior: azHareket() ? "auto" : "smooth" });
    }).catch(function (e) {
      hataGoster(ref.hata, [(e && e.message) ? e.message : String(e)], "Çözüm çalıştırılamadı");
    }).then(function () { D.cozuluyor = false; hatCiz(); });
  }
  function sonucuTemizle() { SON = null; sonEski = false; D.akisHedef = null; ref.sonuc.innerHTML = ""; }
  // ---------- Sonuç yardımcıları ----------
  function V() { return SON ? SON.veri : null; }
  function kisaAl(ad) { const v = V(); if (!v) return null; return (v.sonuclar && v.sonuclar[ad]) || (v.durumlar && v.durumlar[ad]) || null; }
  function kisaToplam(adlar) {
    // G+Q gibi toplamlar için durumları toplar (doğrusallık)
    const v = V(), l = adlar.map(kisaAl).filter(Boolean);
    if (!l.length) return null;
    if (l.length === 1) return l[0];
    const o = { dugumler: [], tepkiler: [], elemanlar: [], denge: {} };
    l[0].dugumler.forEach(function (n, i) { const c = Object.assign({}, n); ["uX", "uY", "uZ", "rX", "rY", "rZ"].forEach(function (k) { c[k] = l.reduce(function (t, s) { return t + (s.dugumler[i][k] || 0); }, 0); }); o.dugumler.push(c); });
    l[0].tepkiler.forEach(function (n, i) { const c = Object.assign({}, n); ["FX", "FY", "FZ", "MX", "MY", "MZ"].forEach(function (k) { c[k] = l.reduce(function (t, s) { return t + (s.tepkiler[i][k] || 0); }, 0); }); o.tepkiler.push(c); });
    l[0].elemanlar.forEach(function (e, i) {
      const c = { no: e.no, x: e.x, enb: {} };
      ["N", "V", "M", "Vz", "My", "T"].forEach(function (k) { c[k] = (e[k] || []).map(function (_, j) { return l.reduce(function (t, s) { return t + (s.elemanlar[i][k][j] || 0); }, 0); }); c.enb[k] = enBuyuk(c[k]); });
      c.uc_kuvvetleri = (e.uc_kuvvetleri || []).map(function (_, j) { return l.reduce(function (t, s) { return t + (s.elemanlar[i].uc_kuvvetleri[j] || 0); }, 0); });
      o.elemanlar.push(c);
    });
    Object.keys(l[0].denge || {}).forEach(function (k) { o.denge[k] = l.reduce(function (t, s) { return t + (s.denge[k] || 0); }, 0); });
    void v;
    return o;
  }
  function durumKisa(ad) { return ad === "G+Q" && !(V().sonuclar && V().sonuclar["G+Q"]) ? kisaToplam(["G", "Q"]) : kisaAl(ad); }
  function enBuyuk(dizi) { let m = 0; (dizi || []).forEach(function (v) { if (Math.abs(v) > Math.abs(m)) m = v; }); return m; }
  function agEleman(tur, kaynakNo) { return (V().ag.elemanlar || []).filter(function (e) { return e.tur === tur && e.kaynak_no === kaynakNo; }); }
  function agDugum(no) { return (V().ag.dugumler || []).filter(function (d) { return d.no === no; })[0]; }
  function elSonuc(kisa, no) { return (kisa.elemanlar || []).filter(function (e) { return e.no === no; })[0]; }
  function akisDeger(objG, objQ) {
    const d = D.akisDurum;
    const g = +objG || 0, q = +objQ || 0;
    return d === "G" ? g : d === "Q" ? q : g + q;
  }
  function kolonAdres(no) { const c = nesneBul("kolon", no) || (V() && V().bina.kolonlar.filter(function (x) { return x.no === no; })[0]); return c ? "S-" + adres(c.aks) + "/k" + c.kat : "S" + no; }
  function kirisAdres(no) { const k = nesneBul("kiris", no) || (V() && V().bina.kirisler.filter(function (x) { return x.no === no; })[0]); return k ? "K-" + adres(k.bas) + "→" + adres(k.son) + "/k" + k.kat : "K" + no; }
  function dosemeAdres(no) { const d = nesneBul("doseme", no) || (V() && V().bina.dosemeler.filter(function (x) { return x.no === no; })[0]); return d ? "D-" + adres(d.kose[0]) + "/" + adres(d.kose[1]) + "/k" + d.kat : "D" + no; }
  // Sankey kenarlarından (K→S) kiriş ucunun kolona verdiği kuvvet
  function ucKuvveti(kirisNo, kolonNo) {
    const v = V(), l = (v.akis && v.akis.sankey) || [];
    let g = 0, q = 0;
    l.forEach(function (e) { if (e.kaynak === "K" + kirisNo && e.hedef.indexOf("S" + kolonNo + "/") === 0) { if (e.durum === "G") g += e.kN; else if (e.durum === "Q") q += e.kN; } });
    return akisDeger(g, q);
  }
  // ---------- Yük akışı zinciri ----------
  function akisZinciri(hedef) {
    const v = V(), vb = v.bina, z = { dosemeler: [], kirisler: [], kolonlar: [], temeller: [] };
    if (!hedef) return z;
    const kolonZinciri = function (c) {
      let k = c;
      while (k) {
        if (z.kolonlar.indexOf(k.no) < 0) z.kolonlar.push(k.no);
        if (k.kat === 1 && z.temeller.indexOf(k.no) < 0) z.temeller.push(k.no);
        k = vb.kolonlar.filter(function (x) { return aksEsit(x.aks, k.aks) && x.kat === k.kat - 1; })[0];
      }
    };
    const kirisEkle = function (kno) {
      if (z.kirisler.indexOf(kno) >= 0) return;
      z.kirisler.push(kno);
      const k = vb.kirisler.filter(function (x) { return x.no === kno; })[0];
      if (!k) return;
      [k.bas, k.son].forEach(function (a) { const c = vb.kolonlar.filter(function (x) { return aksEsit(x.aks, a) && x.kat === k.kat; })[0]; if (c) kolonZinciri(c); });
    };
    if (hedef.tur === "doseme") {
      const d = (v.yukler.dosemeler || []).filter(function (x) { return x.no === hedef.no; })[0];
      if (d) { z.dosemeler.push(d.no); d.paylar.forEach(function (p) { if (p.sekil !== "yok") kirisEkle(p.kiris_no); }); }
    } else if (hedef.tur === "kiris") kirisEkle(hedef.no);
    else if (hedef.tur === "kolon") { const c = vb.kolonlar.filter(function (x) { return x.no === hedef.no; })[0]; if (c) kolonZinciri(c); }
    return z;
  }
  function akisVurguCiz(sahne, P, b, s) {
    const v = V(), vb = v.bina, z = akisZinciri(D.akisHedef);
    const formulHedef = function (p, key) { hedefler.unshift({ tur: "daire", x: p[0], y: p[1], r: 20 * s, kind: "formul", key: key }); };
    const durumEk = D.akisDurum === "G" ? "" : D.akisDurum === "Q" ? " (Q)" : " (G+Q)";
    // döşemeler: turuncu + 45° çizgiler
    z.dosemeler.forEach(function (no) {
      const d = vb.dosemeler.filter(function (x) { return x.no === no; })[0], yd = v.yukler.dosemeler.filter(function (x) { return x.no === no; })[0];
      if (!d || !yd) return;
      const X1 = aksX(d.kose[0][0]), Y1 = aksY(d.kose[0][1]), X2 = aksX(d.kose[1][0]), Y2 = aksY(d.kose[1][1]), Z = katKot(d.kat) + 0.01;
      const kose = [[X1, Y1, Z], [X2, Y1, Z], [X2, Y2, Z], [X1, Y2, Z]];
      dortgenP(sahne, P, b, kose, "b3-akis-doseme", "", 2);
      let cz = "";
      const lk = Math.min(X2 - X1, Y2 - Y1) / 2;
      if (yd.tip === "cift") {
        const kk = [[X1, Y1, 1, 1], [X2, Y1, -1, 1], [X2, Y2, -1, -1], [X1, Y2, 1, -1]];
        kk.forEach(function (k) { cz += C.cizgi(P(k[0], k[1], Z), P(k[0] + k[2] * lk, k[1] + k[3] * lk, Z), "b3-akis-cizgi"); });
        if (X2 - X1 >= Y2 - Y1) cz += C.cizgi(P(X1 + lk, (Y1 + Y2) / 2, Z), P(X2 - lk, (Y1 + Y2) / 2, Z), "b3-akis-cizgi");
        else cz += C.cizgi(P((X1 + X2) / 2, Y1 + lk, Z), P((X1 + X2) / 2, Y2 - lk, Z), "b3-akis-cizgi");
      } else {
        const n = 4;
        for (let i = 1; i < n; i++) {
          if (X2 - X1 >= Y2 - Y1) cz += C.cizgi(P(X1 + (X2 - X1) * i / n, Y1, Z), P(X1 + (X2 - X1) * i / n, Y2, Z), "b3-akis-cizgi");
          else cz += C.cizgi(P(X1, Y1 + (Y2 - Y1) * i / n, Z), P(X2, Y1 + (Y2 - Y1) * i / n, Z), "b3-akis-cizgi");
        }
      }
      sahne.ekle(1e9, cz, 2);
      const m = P((X1 + X2) / 2, (Y1 + Y2) / 2, Z);
      const et = (D.akisDurum === "Q" ? "q = " + f2(yd.q) : D.akisDurum === "G" ? "g = " + f2(yd.g) : "g+q = " + f2(yd.g + yd.q)) + " kN/m²";
      sahne.ekle(1e9, etiketKutu(m[0], m[1] + 14, et, "b3-akis-et"), 2);
      formulHedef([m[0], m[1] + 10], "doseme:" + no);
    });
    // kiriş yük şekilleri (paylar) ve kiriş toplamı
    let tepeMaks = 0;
    const paylar = [];
    (v.yukler.dosemeler || []).forEach(function (yd) {
      yd.paylar.forEach(function (p) {
        if (z.kirisler.indexOf(p.kiris_no) < 0 || p.sekil === "yok") return;
        if (z.dosemeler.length && z.dosemeler.indexOf(yd.no) < 0 && D.akisHedef.tur === "doseme") return;
        const w = akisDeger(p.tepe_g, p.tepe_q);
        tepeMaks = Math.max(tepeMaks, w);
        paylar.push({ d: yd, p: p, w: w });
      });
    });
    const olcek = tepeMaks > 0 ? 0.7 / tepeMaks : 0;
    paylar.forEach(function (o) {
      const k = vb.kirisler.filter(function (x) { return x.no === o.p.kiris_no; })[0];
      if (!k) return;
      const X1 = aksX(k.bas[0]), Y1 = aksY(k.bas[1]), X2 = aksX(k.son[0]), Y2 = aksY(k.son[1]), Z = katKot(k.kat) + 0.02;
      const L = Math.hypot(X2 - X1, Y2 - Y1), ux = (X2 - X1) / L, uy = (Y2 - Y1) / L, lk = Math.min(o.d.lx, o.d.ly);
      const hw = o.w * olcek;
      let prof;
      if (o.p.sekil === "ucgen") prof = [[0, 0], [L / 2, hw], [L, 0]];
      else if (o.p.sekil === "trapez") prof = [[0, 0], [lk / 2, hw], [L - lk / 2, hw], [L, 0]];
      else prof = [[0, 0], [0, hw], [L, hw], [L, 0]];
      const ekr = prof.map(function (q) { return P(X1 + ux * q[0], Y1 + uy * q[0], Z + q[1]); });
      sahne.ekle(1e9, C.cokgen(ekr, "b3-akis-yuk"), 2);
      const m = P(X1 + ux * L / 2, Y1 + uy * L / 2, Z + hw);
      sahne.ekle(1e9, etiketKutu(m[0], m[1] - 8, (o.p.sekil === "ucgen" ? "▲ " : o.p.sekil === "trapez" ? "▬ " : "▭ ") + f2(o.w) + " kN/m", "b3-akis-et"), 2);
      formulHedef([m[0], m[1] - 12], "pay:" + o.d.no + ":" + o.p.kiris_no);
    });
    // kiriş toplam yükü (hedef kiriş ise) ve uç kuvvetleri → kolon okları
    z.kirisler.forEach(function (kno) {
      const k = vb.kirisler.filter(function (x) { return x.no === kno; })[0], yk = (v.yukler.kirisler || []).filter(function (x) { return x.no === kno; })[0];
      if (!k || !yk) return;
      const X1 = aksX(k.bas[0]), Y1 = aksY(k.bas[1]), X2 = aksX(k.son[0]), Y2 = aksY(k.son[1]), Z = katKot(k.kat);
      sahne.ekle(1e9, C.cizgi(P(X1, Y1, Z), P(X2, Y2, Z), "b3-akis-kiris"), 2);
      if (D.akisHedef.tur === "kiris") {
        const q = akisDeger(yk.G.doseme + yk.G.duvar + yk.G.oz + yk.G.ek, yk.Q.doseme + yk.Q.ek);
        const m = P((X1 + X2) / 2, (Y1 + Y2) / 2, Z - 0.6);
        sahne.ekle(1e9, etiketKutu(m[0], m[1], "q = " + f2(q) + " kN/m · " + f1(akisDeger(yk.G.toplam_kN, yk.Q.toplam_kN)) + " kN", "b3-akis-et"), 2);
        formulHedef(m, "kiris:" + kno);
      }
      [k.bas, k.son].forEach(function (a) {
        const c = vb.kolonlar.filter(function (x) { return aksEsit(x.aks, a) && x.kat === k.kat; })[0];
        if (!c) return;
        const X = aksX(a[0]), Y = aksY(a[1]), R = ucKuvveti(kno, c.no);
        const p0 = P(X, Y, Z + 0.9), p1 = P(X, Y, Z + 0.15);
        sahne.ekle(1e9, C.ok(p0, p1, "b3-akis-ok-c", "b3-akis-ok-o", "", ""), 2);
        sahne.ekle(1e9, etiketKutu(p0[0], p0[1] - 8, f1(R) + " kN", "b3-akis-et"), 2);
        formulHedef([p0[0], p0[1] - 10], "uc:" + kno + ":" + c.no);
      });
    });
    // kolon şeridi: kümülatif N
    z.kolonlar.forEach(function (cno) {
      const c = vb.kolonlar.filter(function (x) { return x.no === cno; })[0], ak = (v.akis.kolonlar || []).filter(function (x) { return x.no === cno; })[0];
      if (!c || !ak) return;
      const X = aksX(c.aks[0]), Y = aksY(c.aks[1]), z0 = katKot(c.kat - 1), z1 = katKot(c.kat);
      sahne.ekle(1e9, C.ok(P(X, Y, z1 - 0.3), P(X, Y, z0 + 0.35), "b3-akis-kolon", "b3-akis-ok-o", "", ""), 2);
      const m = P(X, Y, (z0 + z1) / 2);
      sahne.ekle(1e9, etiketKutu(m[0] + 14, m[1], "N = " + f1(akisDeger(ak.N_kum_G, ak.N_kum_Q)) + " kN", "b3-akis-et", "start"), 2);
      formulHedef([m[0] + 30, m[1]], "kolon:" + cno);
    });
    // temeller
    z.temeller.forEach(function (cno) {
      const t = (v.akis.temeller || []).filter(function (x) { return x.kolon_no === cno; })[0];
      if (!t) return;
      const X = aksX(t.aks[0]), Y = aksY(t.aks[1]), th = (vb.temeller.varsayilan && vb.temeller.varsayilan.h) || 0.6, zt = (katKot(0) || 0) - th;
      // basınç trapezi (X doğrultusunda B genişliğinde): σmin … σmax
      const sm = Math.max(t.sigma_max, 1e-9), hs = 0.5;
      const pts = [P(X - t.B / 2, Y, zt), P(X + t.B / 2, Y, zt), P(X + t.B / 2, Y, zt - hs * t.sigma_max / sm), P(X - t.B / 2, Y, zt - hs * Math.max(0, t.sigma_min) / sm)];
      sahne.ekle(1e9, C.cokgen(pts, "b3-akis-temel"), 2);
      const m = P(X, Y, zt - hs - 0.35);
      sahne.ekle(1e9, etiketKutu(m[0], m[1] + 4, "σ = " + f1(t.sigma_max) + " kN/m² · D/C " + f2(t.DC), "b3-akis-et"), 2);
      formulHedef(m, "temel:" + cno);
    });
  }
  function etiketKutu(x, y, t, sinif, hiza) {
    const w = 6.4 * t.length + 10, h = 18, ax = hiza === "start" ? x - 5 : x - w / 2;
    return '<g class="b3-etiket-kutu ' + sinif + '"><rect x="' + r1(ax) + '" y="' + r1(y - 13) + '" width="' + r1(w) + '" height="' + h + '" rx="5"/>' + metinSvg(hiza === "start" ? x : x, y, t, "b3-etiket-t", hiza || "middle") + "</g>";
  }
  // C.dortgen T yerine P (X,Y,Z→ekran) kullanan sürüm (akış vurgusu için)
  function dortgenP(sahne, P, b, kose, sinif, ek, katman) {
    const mer = [0, 0, 0];
    kose.forEach(function (k) { mer[0] += k[0] / kose.length; mer[1] += k[1] / kose.length; mer[2] += k[2] / kose.length; });
    const ekr = kose.map(function (k) { return P(k[0], k[1], k[2]); });
    sahne.ekle(C.derinlik(mer[0], mer[1], mer[2], b), C.cokgen(ekr, sinif, ek), katman);
    return ekr;
  }
  // ---------- Formül kartı ----------
  function formulGoster(key) {
    const v = V(); if (!v) return;
    const p = key.split(":"), tur = p[0];
    let baslik = "", tex = "", not = "", adim = 3;
    if (tur === "doseme") {
      const d = v.yukler.dosemeler.filter(function (x) { return x.no === +p[1]; })[0], vb = v.bina.dosemeler.filter(function (x) { return x.no === +p[1]; })[0];
      if (!d) return;
      baslik = dosemeAdres(d.no) + " — döşeme yükleri (TS 498:2021)";
      tex = "g = \\gamma_b h + g_{ek} = 25\\cdot" + f2(vb ? vb.h : 0).replace(",", "{,}") + " + " + f2(vb ? vb.g_ek : 0).replace(",", "{,}") + " = " + f2(d.g).replace(",", "{,}") + "\\ \\text{kN/m}^2,\\quad q = " + f2(d.q).replace(",", "{,}") + "\\ \\text{kN/m}^2";
      not = "l_k = " + f2(Math.min(d.lx, d.ly)) + " m, l_u = " + f2(Math.max(d.lx, d.ly)) + " m, m = l_u/l_k = " + f2(d.m) + (d.tip === "cift" ? " ≤ 2 → çift doğrultulu (45° kuralı)" : " > 2 → tek doğrultulu") + ". Toplam G = " + f1(d.G_toplam) + " kN, Q = " + f1(d.Q_toplam) + " kN.";
      adim = 2;
    } else if (tur === "pay") {
      const d = v.yukler.dosemeler.filter(function (x) { return x.no === +p[1]; })[0];
      const pay = d && d.paylar.filter(function (x) { return x.kiris_no === +p[2]; })[0];
      if (!pay) return;
      const pp = D.akisDurum === "Q" ? d.q : D.akisDurum === "G" ? d.g : d.g + d.q, lk = Math.min(d.lx, d.ly), w = akisDeger(pay.tepe_g, pay.tepe_q);
      baslik = dosemeAdres(d.no) + " → " + kirisAdres(pay.kiris_no) + " (" + (pay.sekil === "ucgen" ? "üçgen, kısa kenar" : pay.sekil === "trapez" ? "trapez, uzun kenar" : "düzgün") + ")";
      tex = "w = \\frac{p\\,l_k}{2} = \\frac{" + f2(pp).replace(",", "{,}") + "\\cdot" + f2(lk).replace(",", "{,}") + "}{2} = " + f2(w).replace(",", "{,}") + "\\ \\text{kN/m}";
      if (pay.sekil === "ucgen") tex += ",\\quad q_{eM} = \\frac{p\\,l_k}{3} = " + f2(akisDeger(pay.q_eM_g, pay.q_eM_q)).replace(",", "{,}") + ",\\quad q_{eV} = \\frac{p\\,l_k}{4} = " + f2(akisDeger(pay.q_eV_g, pay.q_eV_q)).replace(",", "{,}");
      else if (pay.sekil === "trapez") tex += ",\\quad q_{eM} = \\frac{p\\,l_k}{2}\\left(1-\\frac{1}{3m^2}\\right) = " + f2(akisDeger(pay.q_eM_g, pay.q_eM_q)).replace(",", "{,}") + ",\\quad q_{eV} = \\frac{p\\,l_k}{2}\\left(1-\\frac{1}{2m}\\right) = " + f2(akisDeger(pay.q_eV_g, pay.q_eV_q)).replace(",", "{,}");
      not = "Kirişe giden toplam: " + f1(akisDeger(pay.toplam_G, pay.toplam_Q)) + " kN. Eşdeğer düzgün yükler yalnız el hesabı içindir; FE'ye gerçek şekil (parçalı doğrusal yük) gider. TS 500 md. 11.4.3.";
    } else if (tur === "kiris") {
      const yk = v.yukler.kirisler.filter(function (x) { return x.no === +p[1]; })[0];
      if (!yk) return;
      const q = akisDeger(yk.G.doseme + yk.G.duvar + yk.G.oz + yk.G.ek, yk.Q.doseme + yk.Q.ek), L = yk.L;
      baslik = kirisAdres(yk.no) + " — yük dökümü ve el hesabı";
      tex = "q = q_{d} + q_{duvar} + q_{öz} + q_{ek} = " + [yk.G.doseme, yk.G.duvar, yk.G.oz, yk.G.ek].map(function (x) { return f2(D.akisDurum === "Q" ? 0 : x).replace(",", "{,}"); }).join(" + ") + (D.akisDurum !== "G" ? " + " + f2(yk.Q.doseme + yk.Q.ek).replace(",", "{,}") + "\\,(Q)" : "") + " = " + f2(q).replace(",", "{,}") + "\\ \\text{kN/m}";
      tex += "\\\\ R \\approx \\frac{qL}{2} = " + f1(q * L / 2).replace(",", "{,}") + "\\ \\text{kN},\\quad M_{orta} \\approx \\frac{qL^2}{8} = " + f1(q * L * L / 8).replace(",", "{,}") + "\\ \\text{kN·m}";
      const e = agEleman("kiris", yk.no)[0], ks = e && durumKisa(D.akisDurum), es = ks && elSonuc(ks, e.no);
      if (es) not = "FE (bu durum): M_maks = " + f1(enBuyuk(es.M)) + " kN·m, V_maks = " + f1(enBuyuk(es.V)) + " kN. Basit kiriş değeri ile fark süreklilik ve uç ankastreliğinden gelir.";
      adim = 4;
    } else if (tur === "uc") {
      const R = ucKuvveti(+p[1], +p[2]), yk = v.yukler.kirisler.filter(function (x) { return x.no === +p[1]; })[0];
      baslik = kirisAdres(+p[1]) + " ucu → " + kolonAdres(+p[2]);
      tex = "R_{FE} = " + f1(R).replace(",", "{,}") + "\\ \\text{kN}" + (yk ? ",\\qquad R_{basit} = \\frac{qL}{2} = " + f1(akisDeger(yk.el_hesabi.R_G, yk.el_hesabi.R_Q)).replace(",", "{,}") + "\\ \\text{kN}" : "");
      not = "Kiriş uç kesmesi kolona düşey yük olarak iner; FE değeri sürekliliği hesaba katar."; adim = 8;
    } else if (tur === "kolon") {
      const ak = v.akis.kolonlar.filter(function (x) { return x.no === +p[1]; })[0];
      if (!ak) return;
      baslik = kolonAdres(ak.no) + " — kolon birikimi";
      tex = "N_{kat} = " + f1(akisDeger(ak.N_G, ak.N_Q)).replace(",", "{,}") + "\\ \\text{kN},\\quad N_{küm} = \\sum_{üst\\ katlar} N_{kat} = " + f1(akisDeger(ak.N_kum_G, ak.N_kum_Q)).replace(",", "{,}") + "\\ \\text{kN}";
      tex += "\\\\ N_{trib} = \\sum (g+q)A_{trib} + \\text{kiriş/duvar payları} + \\text{kolon öz} = " + f1(akisDeger(ak.N_trib_G, ak.N_trib_Q)).replace(",", "{,}") + "\\ \\text{kN}" + (ak.A_trib != null ? "\\quad (A_{trib} = " + f2(ak.A_trib).replace(",", "{,}") + "\\ \\text{m}^2)" : "");
      not = "Fark: " + f1(ak.fark_yuzde) + " % (FE − yük alanı). Yük alanı yöntemi rijitlik ve sürekliliği görmez; FE komşu açıklıkların paylaşımını hesaplar."; adim = 8;
    } else if (tur === "temel") {
      const t = v.akis.temeller.filter(function (x) { return x.kolon_no === +p[1]; })[0];
      if (!t) return;
      baslik = "Temel T-" + adres(t.aks) + " — taban basıncı (servis G+Q)";
      tex = "\\sigma_{max,min} = \\frac{N}{BL} \\pm \\frac{6M_X}{BL^2} \\pm \\frac{6M_Y}{LB^2} = \\frac{" + f1(t.N_servis).replace(",", "{,}") + "}{" + f2(t.B).replace(",", "{,}") + "\\cdot" + f2(t.L).replace(",", "{,}") + "} \\pm \\ldots = " + f1(t.sigma_max).replace(",", "{,}") + "\\ /\\ " + f1(t.sigma_min).replace(",", "{,}") + "\\ \\text{kN/m}^2";
      tex += "\\\\ e_X = " + f2(t.e_X).replace(",", "{,}") + "\\ \\text{m},\\ e_Y = " + f2(t.e_Y).replace(",", "{,}") + "\\ \\text{m}" + (t.cekirdek_icinde ? "\\ (\\le B/6: \\text{çekirdek içinde})" : "\\ (\\text{çekirdek dışında!})") + ",\\quad D/C = \\frac{\\sigma_{max}}{q_{em}} = " + f2(t.DC).replace(",", "{,}");
      not = "q_em = " + f1(t.q_em) + " kN/m². Temel ebatları: B = " + f2(t.B) + " m, L = " + f2(t.L) + " m."; adim = 8;
    }
    D.formul = key;
    ref.formul.classList.remove("gizli");
    ref.formul.innerHTML = '<div class="bn-formul-ust"><b>' + kacis(baslik) + '</b><button type="button" class="bn-firca-kapat" id="bn-formul-kapat" aria-label="Kapat">✕</button></div>' + katex(tex) + (not ? '<p class="not">' + kacis(not) + "</p>" : "") +
      '<button type="button" class="dugme kucuk" data-adim="' + adim + '">Anlatımda gör</button>';
  }
  // ---------- Oynat ----------
  function oynatToggle() {
    const v = V(); if (!v) return;
    if (D.oynat) { clearTimeout(D.oynat); D.oynat = 0; akisKontrol(); return; }
    const liste = (v.yukler.dosemeler || []).map(function (d) { return d.no; });
    if (!liste.length) { A.toast("Döşeme yok."); return; }
    let i = 0;
    const adim = function () {
      D.akisHedef = { tur: "doseme", no: liste[i] }; D.secim = [{ tur: "doseme", no: liste[i] }];
      const d = v.bina.dosemeler.filter(function (x) { return x.no === liste[i]; })[0];
      if (d && d.kat !== D.kat) D.kat = d.kat;
      sahneCiz(); akisKontrol(); sankeyCiz();
      i++;
      if (i < liste.length) D.oynat = setTimeout(adim, azHareket() ? 2500 : 1600); else { D.oynat = 0; akisKontrol(); }
    };
    D.oynat = 1; adim();
  }
  function akisKontrol() {
    const o = document.getElementById("bn-oynat");
    if (o) o.textContent = D.oynat ? "⏸ Durdur" : "▶ Oynat";
  }
  function akisYenile() { sankeyCiz(); const k = document.getElementById("bn-akis-tablolar"); if (k) k.innerHTML = akisTablolari(); }
  // ---------- Akış şeması (Sankey) ----------
  function sankeyCiz() {
    const kap = document.getElementById("bn-sankey");
    if (!kap || !V()) return;
    kap.innerHTML = sankeyHtml(Math.max(560, (kap.clientWidth || 600) - 12));
  }
  function sankeyHtml(W) {
    const v = V(), ed = {};
    (v.akis.sankey || []).forEach(function (e) {
      if (D.akisDurum !== "G+Q" && e.durum !== D.akisDurum) return;
      const k = e.kaynak + ">" + e.hedef;
      ed[k] = ed[k] || { kaynak: e.kaynak, hedef: e.hedef, kN: 0 };
      ed[k].kN += e.kN;
    });
    const kenarlar = Object.keys(ed).map(function (k) { return ed[k]; }).filter(function (e) { return e.kN > 1e-6; });
    if (!kenarlar.length) return '<p class="not">Bu durum için akış verisi yok.</p>';
    const ust = ustKatV(v);
    const sutun = function (id) {
      if (id.charAt(0) === "D") return 0;
      if (id.charAt(0) === "K") return 1;
      if (id.charAt(0) === "S") { const m = /\/k(\d+)/.exec(id); return 2 + (m ? ust - (+m[1]) : 0); }
      if (id.charAt(0) === "T") return 2 + ust;
      return 3 + ust;
    };
    const dugum = {};
    kenarlar.forEach(function (e) {
      [e.kaynak, e.hedef].forEach(function (id) { dugum[id] = dugum[id] || { id: id, s: sutun(id), giren: 0, cikan: 0 }; });
      dugum[e.kaynak].cikan += e.kN; dugum[e.hedef].giren += e.kN;
    });
    const sutunlar = [];
    Object.keys(dugum).forEach(function (id) { const n = dugum[id]; n.akis = Math.max(n.giren, n.cikan); (sutunlar[n.s] = sutunlar[n.s] || []).push(n); });
    const nS = sutunlar.length, H = 360, bosluk = 6, pl = 58, pr = 70, gw = 14;
    let maksToplam = 0;
    sutunlar.forEach(function (l) { if (!l) return; l.sort(function (a, b) { return a.id.localeCompare(b.id, "tr", { numeric: true }); }); const t = l.reduce(function (s, n) { return s + n.akis; }, 0) ; maksToplam = Math.max(maksToplam, t + 0); });
    const olcek = (H - 40 - bosluk * 8) / (maksToplam || 1);
    const sx = function (s) { return pl + (nS > 1 ? s * (W - pl - pr) / (nS - 1) : 0); };
    let svg = "";
    sutunlar.forEach(function (l, s) {
      if (!l) return;
      const toplamH = l.reduce(function (t, n) { return t + n.akis * olcek; }, 0) + bosluk * (l.length - 1);
      let y = 20 + (H - 40 - toplamH) / 2;
      l.forEach(function (n) { n.x = sx(s); n.y = y; n.h = Math.max(2, n.akis * olcek); n.gy = n.y; n.cy = n.y; y += n.h + bosluk; });
    });
    const basliklar = ["Döşemeler", "Kirişler"]; for (let k = ust; k >= 1; k--) basliklar.push("Kolon k" + k); basliklar.push("Temeller", "Zemin");
    basliklar.forEach(function (bsl, s) { if (sutunlar[s]) svg += metinSvg(sx(s) + gw / 2, 12, bsl, "bn-sankey-bsl", "middle"); });
    const secim = D.sankeySecim;
    kenarlar.sort(function (a, b) { return a.kaynak.localeCompare(b.kaynak, "tr", { numeric: true }); });
    kenarlar.forEach(function (e) {
      const a = dugum[e.kaynak], b = dugum[e.hedef], w = Math.max(1.2, e.kN * olcek);
      const x0 = a.x + gw, x1 = b.x, y0 = a.cy, y1 = b.gy;
      a.cy += w; b.gy += w;
      const cx = (x0 + x1) / 2;
      const d = "M" + pt(x0, y0) + " C" + pt(cx, y0) + " " + pt(cx, y1) + " " + pt(x1, y1) + " L" + pt(x1, y1 + w) + " C" + pt(cx, y1 + w) + " " + pt(cx, y0 + w) + " " + pt(x0, y0 + w) + " Z";
      const ilgili = !secim || e.kaynak === secim || e.hedef === secim;
      svg += '<path class="bn-sankey-bant' + (secim ? (ilgili ? " aktif" : " soluk") : "") + '" d="' + d + '"><title>' + kacis(e.kaynak + " → " + e.hedef + ": " + f1(e.kN) + " kN") + "</title></path>";
    });
    Object.keys(dugum).forEach(function (id) {
      const n = dugum[id];
      const ad = id.charAt(0) === "D" ? "D" + id.slice(1) : id.charAt(0) === "K" ? "K" + id.slice(1) : id.charAt(0) === "S" ? "S" + id.slice(1).replace(/\/k\d+/, "") : id.indexOf("T-") === 0 ? id.slice(2) : id;
      svg += '<g class="bn-sankey-dugum' + (secim === id ? " aktif" : "") + '" data-sankey="' + kacis(id) + '" tabindex="0" role="button" aria-label="' + kacis(id + " " + f1(n.akis) + " kN") + '"><rect x="' + r1(n.x) + '" y="' + r1(n.y) + '" width="' + gw + '" height="' + r1(n.h) + '" rx="2"/>' +
        metinSvg(n.s === 0 ? n.x - 4 : n.x + gw + 4, n.y + n.h / 2 + 4, ad + " " + f1(n.akis), "bn-sankey-t", n.s === 0 ? "end" : "start") + "</g>";
    });
    return '<svg class="se-svg bn-sankey-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Yük akışı şeması (' + kacis(D.akisDurum) + ')">' + svg + "</svg>";
  }
  function ustKatV(v) { return v.bina.katlar.reduce(function (m, k) { return Math.max(m, k.no); }, 0); }
  // ---------- Korunum ve tablolar ----------
  function korunumHtml() {
    const v = V(), d = D.akisDurum;
    const al = function (anahtar) { const g = v.akis.korunum.G || {}, q = v.akis.korunum.Q || {}; return akisDeger(g[anahtar], q[anahtar]); };
    const kirisGirdi = (v.yukler.kirisler || []).reduce(function (t, k) { return t + akisDeger(k.G.toplam_kN, k.Q.toplam_kN); }, 0);
    const a = al("dosemeler") + al("duvarlar") + al("kiris_oz") + (al("ek") || 0), c = al("toplam"), dd = al("kolon_taban"), e = al("temel");
    const sayilar = [["Döşeme + duvar + kiriş öz + ek", a], ["Kiriş girdisi (Σ q·L)", kirisGirdi], ["+ kolon öz = toplam", c], ["Σ kolon tabanı N", dd], ["Σ temel tepkisi", e]];
    const tol = 0.01 * Math.max(1, Math.abs(c));
    const tamam = Math.abs(a - kirisGirdi) < tol && Math.abs(c - dd) < tol && Math.abs(dd - e) < tol;
    return '<div class="bn-korunum ' + (tamam ? "tamam" : "sorun") + '"><b>Korunum (' + kacis(d) + "): " + (tamam ? "✓ beş sayı eşit" : "⚠ fark var") + "</b><div class=\"bn-korunum-sayilar\">" +
      sayilar.map(function (s) { return '<span><small>' + kacis(s[0]) + "</small><b>" + f1(s[1]) + " kN</b></span>"; }).join('<span class="bn-korunum-es" aria-hidden="true">=</span>') + "</div></div>";
  }
  function akisTablolari() {
    const v = V(), ust = ustKatV(v);
    let h = "<h4>Kolonlar (kN; basınç +)</h4>" + tabloH(["Kolon", "Kat", "N_kat G", "N_kat Q", "N_küm G", "N_küm Q", "Yük alanı G+Q", "Fark %"], (v.akis.kolonlar || []).slice().sort(function (a, b) { return b.kat - a.kat || a.no - b.no; }).map(function (k) {
      return [kolonAdres(k.no), String(k.kat), f1(k.N_G), f1(k.N_Q), f1(k.N_kum_G), f1(k.N_kum_Q), f1((k.N_trib_G || 0) + (k.N_trib_Q || 0)), f1(k.fark_yuzde)];
    }));
    h += "<h4>Temeller (servis G+Q)</h4>" + tabloH(["Temel", "B×L (m)", "N (kN)", "M_X", "M_Y", "σ_max", "σ_min", "e_X / e_Y", "D/C"], (v.akis.temeller || []).map(function (t) {
      const r = ["T-" + adres(t.aks), f2(t.B) + "×" + f2(t.L), f1(t.N_servis), f1(t.MX), f1(t.MY), f1(t.sigma_max), f1(t.sigma_min), f2(t.e_X) + " / " + f2(t.e_Y) + (t.cekirdek_icinde ? "" : " (!)"), '<b class="' + (t.DC > 1 ? "bn-kotu" : "bn-iyi") + '">' + f2(t.DC) + "</b>"];
      return r;
    }));
    h += "<h4>Kat toplamları</h4>" + tabloH(["Kat", "Kot (m)", "h (m)", "G (kN)", "Q (kN)", "w = G + nQ"], (v.yukler.katlar || []).slice().sort(function (a, b) { return b.kat - a.kat; }).map(function (k) { return [katAdV(v, k.kat), f2(k.kot), f2(k.h), f1(k.G), f1(k.Q), f1(k.w)]; }));
    void ust;
    return h;
  }
  function katAdV(v, no) { const k = v.bina.katlar.filter(function (x) { return x.no === no; })[0]; return k ? k.ad : "kat " + no; }

  // ---------- Sonuç bölümü ----------
  const SEKMELER = [["akis", "Yük akışı"], ["deforme", "Deforme"], ["diyagram", "Diyagramlar"], ["tablolar", "Tablolar"], ["anlatim", "Anlatım"]];
  let anlatimCizildi = false;
  function sonucuCiz() {
    const v = V();
    if (!v) { ref.sonuc.innerHTML = ""; return; }
    anlatimCizildi = false;
    const o = v.ozet || {};
    let h = '<div class="bn-eski se-eski' + (sonEski ? "" : " gizli") + '">Model değişti: aşağıdaki sonuçlar önceki modele aittir. Yeniden çözmek için “Çöz” düğmesine basın.</div>';
    h += '<div class="se-ozet"><span class="se-rozet">' + (o.sd_sayisi != null ? o.sd_sayisi : v.ag.sd_sayisi) + " SD</span><span class=\"se-rozet\">" + (o.eleman != null ? o.eleman : v.ag.elemanlar.length) + " eleman</span>" +
      '<span class="se-rozet">ΣG = ' + f1(o.toplam_G != null ? o.toplam_G : v.yukler.toplam.G) + " kN</span><span class=\"se-rozet\">ΣQ = " + f1(o.toplam_Q != null ? o.toplam_Q : v.yukler.toplam.Q) + " kN</span>" +
      (o.en_buyuk_temel_DC != null ? '<span class="se-rozet">Temel D/C maks ' + f2(o.en_buyuk_temel_DC) + "</span>" : "") + "</div>";
    if (o.uyarilar && o.uyarilar.length) h += '<div class="bn-uyari-kutu">' + o.uyarilar.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    h += '<div class="bn-sekmeler" role="tablist">' + SEKMELER.map(function (s) { return '<button type="button" role="tab" class="bn-sekme' + (D.sekme === s[0] ? " aktif" : "") + '" data-sekme="' + s[0] + '" aria-selected="' + (D.sekme === s[0]) + '">' + s[1] + "</button>"; }).join("") + "</div>";
    h += '<div class="bn-sekme-icerik" id="bn-sekme-icerik"></div>';
    ref.sonuc.innerHTML = h;
    sekmeCiz();
  }
  function sekmeCiz() {
    const kap = document.getElementById("bn-sekme-icerik");
    if (!kap || !V()) return;
    document.querySelectorAll("#bn-sonuc .bn-sekme").forEach(function (b) { b.classList.toggle("aktif", b.dataset.sekme === D.sekme); b.setAttribute("aria-selected", String(b.dataset.sekme === D.sekme)); });
    if (D.oynat) { clearTimeout(D.oynat); D.oynat = 0; }
    if (D.sekme === "akis") kap.innerHTML = akisSekmesi();
    else if (D.sekme === "deforme") kap.innerHTML = deformeSekmesi();
    else if (D.sekme === "diyagram") kap.innerHTML = diyagramSekmesi();
    else if (D.sekme === "tablolar") kap.innerHTML = tablolarSekmesi();
    else kap.innerHTML = anlatimSekmesi();
    if (D.sekme === "akis") sankeyCiz();
    else if (D.sekme === "deforme") deformeyiCiz();
    else if (D.sekme === "diyagram") diyagramiCiz();
    else if (D.sekme === "anlatim") anlatimiCiz();
    sahneCiz();
  }
  function durumSecici(id, secili, zarf) {
    const v = V(), l = [];
    Object.keys(v.durumlar || {}).forEach(function (k) { l.push([k, "Durum " + k]); });
    if (!(v.sonuclar && v.sonuclar["G+Q"]) && v.durumlar.G && v.durumlar.Q) l.push(["G+Q", "G+Q (toplam)"]);
    Object.keys(v.sonuclar || {}).forEach(function (k) { l.push([k, "Kombinasyon " + k]); });
    if (zarf) l.push(["zarf", "Zarf (max/min)"]);
    return '<select class="girdi bn-secici" id="' + id + '" aria-label="Yük durumu / kombinasyon">' + secenekler(l, secili) + "</select>";
  }
  function akisSekmesi() {
    return '<div class="bn-akis-ust"><div class="se-seg" role="group" aria-label="Yük durumu">' + ["G", "Q", "G+Q"].map(function (d) { return '<button type="button" class="se-seg-d" data-akis-durum="' + d + '" aria-pressed="' + (D.akisDurum === d) + '">' + d + "</button>"; }).join("") + "</div>" +
      '<div class="dugmeler"><button type="button" class="dugme kucuk" id="bn-oynat">▶ Oynat</button><span class="not">3B sahnede bir döşeme, kiriş ya da kolona dokun: yük yolu vurgulanır; ok ve etiketlere dokununca formül kartı açılır.</span></div></div>' +
      korunumHtml() + '<h4>Akış şeması (bant genişliği ∝ kN; düğüme dokun: yalnız ilgili bantlar)</h4><div class="se-sekil bn-sankey" id="bn-sankey" data-adim="8"></div>' +
      '<div id="bn-akis-tablolar">' + akisTablolari() + "</div>";
  }
  // ---------- Deforme ----------
  function deformeSekmesi() {
    return '<div class="bn-satir">' + durumSecici("bn-def-durum", D.deformeDurum, false) + '<div class="se-olcek"><label for="bn-olcek">Ölçek</label><input type="range" id="bn-olcek" min="0" max="200" step="5" value="' + D.olcek + '" aria-label="Deformasyon ölçeği"><output id="bn-olcek-d" class="se-olcek-d"></output></div></div>' +
      '<div class="se-sekil" id="bn-def-sekil"></div><p class="not">Soluk çizgi özgün yapı, mavi eğri büyütülmüş deforme şekildir (Hermite kübik; dönmeler eleman yerel ekseninde). Bakış açısı 3B sahneyle aynıdır.</p>';
  }
  function hermite(xi, L, v1, t1, v2, t2) {
    const x2 = xi * xi, x3 = x2 * xi;
    return v1 * (1 - 3 * x2 + 2 * x3) + t1 * L * (xi - 2 * x2 + x3) + v2 * (3 * x2 - 2 * x3) + t2 * L * (-x2 + x3);
  }
  function elemanEgrisi(e, nd, uu, n) {
    const a = nd[e.dugumler[0]], b = nd[e.dugumler[1]], ua = uu[e.dugumler[0]], ub = uu[e.dugumler[1]];
    const lam = e.lam, L = e.L, out = [];
    const yerel = function (u) { return [0, 1, 2].map(function (i) { return lam[i][0] * u[0] + lam[i][1] * u[1] + lam[i][2] * u[2]; }); };
    const da = yerel([ua.uX, ua.uY, ua.uZ]), db = yerel([ub.uX, ub.uY, ub.uZ]), ra = yerel([ua.rX, ua.rY, ua.rZ]), rb = yerel([ub.rX, ub.rY, ub.rZ]);
    for (let m = 0; m <= n; m++) {
      const xi = m / n;
      const ul = da[0] + (db[0] - da[0]) * xi;
      const vl = hermite(xi, L, da[1], ra[2], db[1], rb[2]);
      const wl = hermite(xi, L, da[2], -ra[1], db[2], -rb[1]);
      const d = [0, 1, 2].map(function (j) { return lam[0][j] * ul + lam[1][j] * vl + lam[2][j] * wl; });
      out.push({ b: [a.X + (b.X - a.X) * xi, a.Y + (b.Y - a.Y) * xi, a.Z + (b.Z - a.Z) * xi], d: d });
    }
    return out;
  }
  function deformeyiCiz() {
    const kap = document.getElementById("bn-def-sekil"), v = V();
    if (!kap || !v) return;
    const ks = durumKisa(D.deformeDurum);
    if (!ks) { kap.innerHTML = '<p class="not se-bos">Bu durum için sonuç yok.</p>'; return; }
    const W = Math.max(260, kap.clientWidth || 600), H = Math.max(260, Math.round(W * 0.55)), b = kamera.bakis;
    const nd = {}, uu = {};
    v.ag.dugumler.forEach(function (d) { nd[d.no] = d; });
    ks.dugumler.forEach(function (d) { uu[d.no] = d; });
    const egriler = v.ag.elemanlar.map(function (e) { return e.lam ? elemanEgrisi(e, nd, uu, 16) : null; });
    let maks = 0, aralik = 1;
    const sn = sinir(); aralik = Math.max(sn.x1 - sn.x0, sn.y1 - sn.y0, sn.z1 - sn.z0) || 1;
    egriler.forEach(function (eg) { if (eg) eg.forEach(function (p) { maks = Math.max(maks, Math.hypot(p.d[0], p.d[1], p.d[2])); }); });
    const oto = maks > 1e-15 ? 0.08 * aralik / maks : 1, k = oto * D.olcek / 100;
    const pts = [];
    v.ag.dugumler.forEach(function (d) { pts.push(C.izdusum(d.X, d.Y, d.Z, b)); const u = uu[d.no]; if (u) pts.push(C.izdusum(d.X + oto * 1.5 * u.uX, d.Y + oto * 1.5 * u.uY, d.Z + oto * 1.5 * u.uZ, b)); });
    const T = C.donusum(pts, W, H, { pl: 30, pu: 24, pa: 30 });
    const P = function (X, Y, Z) { const q = C.izdusum(X, Y, Z, b); return [T.x(q[0]), T.y(q[1])]; };
    let s = "";
    v.ag.elemanlar.forEach(function (e) { const a = nd[e.dugumler[0]], c = nd[e.dugumler[1]]; s += C.cizgi(P(a.X, a.Y, a.Z), P(c.X, c.Y, c.Z), "se-asil"); });
    v.ag.elemanlar.forEach(function (e, i) {
      const eg = egriler[i];
      if (!eg) return;
      let d = "";
      eg.forEach(function (p, m) { const q = P(p.b[0] + k * p.d[0], p.b[1] + k * p.d[1], p.b[2] + k * p.d[2]); d += (m ? " L" : "M") + pt(q[0], q[1]); });
      s += '<path class="se-def' + (e.tur === "kolon" ? " bn-def-kolon" : "") + '" d="' + d + '"/>';
    });
    v.ag.dugumler.forEach(function (d) { const u = uu[d.no] || { uX: 0, uY: 0, uZ: 0 }; const q = P(d.X + k * u.uX, d.Y + k * u.uY, d.Z + k * u.uZ); s += '<circle class="se-dugum se-dugum-d" cx="' + r1(q[0]) + '" cy="' + r1(q[1]) + '" r="3"/>'; });
    let enb = 0, enbNo = null;
    ks.dugumler.forEach(function (d) { const m = Math.hypot(d.uX, d.uY, d.uZ); if (m > enb) { enb = m; enbNo = d.no; } });
    kap.innerHTML = '<svg class="se-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Deforme şekil"><title>Deforme şekil, ölçek ×' + kacis(fmt(k)) + "</title>" + s + "</svg>";
    const o = document.getElementById("bn-olcek-d");
    if (o) o.textContent = (D.olcek === 0 ? "özgün" : "×" + fmt(k)) + (enbNo != null ? " · u_maks = " + fmt(enb * 1000) + " mm (" + (agDugum(enbNo) || {}).adres + ")" : "");
  }
  // ---------- Diyagramlar ----------
  function diyagramSekmesi() {
    const v = V();
    const akslar = [["", "Bütün akslar"]].concat(v.bina.akslar.x.map(function (a) { return ["x:" + a.ad, "Yalnız aks " + a.ad]; })).concat(v.bina.akslar.y.map(function (a) { return ["y:" + a.ad, "Yalnız aks " + a.ad]; }));
    return '<div class="se-seg" role="group" aria-label="Diyagram türü">' + Object.keys(DIYAGRAM).map(function (t) { return '<button type="button" class="se-seg-d" data-dgm="' + t + '" aria-pressed="' + (D.diyagram === t) + '">' + DIYAGRAM[t].uzun + "</button>"; }).join("") + "</div>" +
      '<div class="bn-satir">' + durumSecici("bn-dgm-durum", D.diyagramDurum, true) + '<select class="girdi bn-secici" id="bn-aks-filtre" aria-label="Aks filtresi">' + secenekler(akslar, D.aksFiltre) + "</select></div>" +
      '<div class="se-sekil" id="bn-dgm-sekil"></div><p class="not" id="bn-dgm-not"></p><div id="bn-eleman-kart"></div>';
  }
  function elemanFiltre(e) {
    if (!D.aksFiltre) return true;
    const v = V(), p = D.aksFiltre.split(":"), a = agDugum(e.dugumler[0]), b = agDugum(e.dugumler[1]);
    void v;
    const i = p[0] === "x" ? 0 : 1;
    return a && b && a.aks[i] === p[1] && b.aks[i] === p[1];
  }
  function diyagramiCiz() {
    const kap = document.getElementById("bn-dgm-sekil"), v = V();
    if (!kap || !v) return;
    document.querySelectorAll("#bn-sonuc .se-seg-d[data-dgm]").forEach(function (d) { d.setAttribute("aria-pressed", String(d.dataset.dgm === D.diyagram)); });
    const tur = D.diyagram, def = DIYAGRAM[tur], zarf = D.diyagramDurum === "zarf", ks = zarf ? null : durumKisa(D.diyagramDurum);
    if (!zarf && !ks) { kap.innerHTML = '<p class="not se-bos">Bu durum için sonuç yok.</p>'; return; }
    const W = Math.max(260, kap.clientWidth || 600), H = Math.max(260, Math.round(W * 0.55)), b = kamera.bakis;
    const nd = {}; v.ag.dugumler.forEach(function (d) { nd[d.no] = d; });
    const T = C.donusum(v.ag.dugumler.map(function (d) { return C.izdusum(d.X, d.Y, d.Z, b); }), W, H, { pl: 40, pu: 40, pa: 40 });
    const P = function (X, Y, Z) { const q = C.izdusum(X, Y, Z, b); return [T.x(q[0]), T.y(q[1])]; };
    const elemanlar = v.ag.elemanlar.filter(elemanFiltre);
    let gmaks = 0;
    const degerler = function (e) {
      if (zarf) {
        const z = (v.zarf && v.zarf.elemanlar || []).filter(function (x) { return x.no === e.no; })[0];
        return z ? { maks: z[tur + "_max"], min: z[tur + "_min"] } : null;
      }
      const es = elSonuc(ks, e.no);
      return es ? { x: es.x, v: es[tur] || [] } : null;
    };
    elemanlar.forEach(function (e) { const d = degerler(e); if (!d) return; if (zarf) gmaks = Math.max(gmaks, Math.abs(d.maks), Math.abs(d.min)); else d.v.forEach(function (x) { gmaks = Math.max(gmaks, Math.abs(x)); }); });
    const kD = gmaks > 1e-12 ? 34 / gmaks : 0;
    let s = "";
    v.ag.elemanlar.forEach(function (e) { const a = nd[e.dugumler[0]], c = nd[e.dugumler[1]]; s += C.cizgi(P(a.X, a.Y, a.Z), P(c.X, c.Y, c.Z), "se-asil" + (elemanFiltre(e) ? "" : " b3-hayalet")); });
    const hedef = [];
    elemanlar.forEach(function (e) {
      const a = nd[e.dugumler[0]], c = nd[e.dugumler[1]], d = degerler(e);
      if (!d || !e.lam) return;
      const n = C.yon(e.lam[def.eksen], b), A1 = P(a.X, a.Y, a.Z), B1 = P(c.X, c.Y, c.Z);
      hedef.push({ tur: "dogru", a: A1, b: B1, r: 12, no: e.no });
      const ciz = function (xs, vs, sinif) {
        const taban = [], ust = [];
        xs.forEach(function (x, i) { const t = x / e.L, bx = A1[0] + (B1[0] - A1[0]) * t, by = A1[1] + (B1[1] - A1[1]) * t, o = def.isaret * (vs[i] || 0) * kD; taban.push([bx, by]); ust.push([bx + n[0] * o, by + n[1] * o]); });
        let yol = "M" + pt(taban[0][0], taban[0][1]);
        ust.forEach(function (p) { yol += " L" + pt(p[0], p[1]); });
        for (let i = taban.length - 1; i >= 0; i--) yol += " L" + pt(taban[i][0], taban[i][1]);
        s += '<path class="se-dgm ' + sinif + '" d="' + yol + ' Z" data-eleman="' + e.no + '"/>';
        let im = 0; vs.forEach(function (val, i) { if (Math.abs(val) > Math.abs(vs[im]) + 1e-12) im = i; });
        if (vs.length && Math.abs(vs[im]) > 1e-6) { const sg = def.isaret * vs[im] >= 0 ? 1 : -1; s += metinSvg(ust[im][0] + n[0] * sg * 10, ust[im][1] + n[1] * sg * 10 + 4, fmt(vs[im], 3), "se-etiket", "middle"); }
      };
      if (zarf) { ciz([0, e.L], [d.maks, d.maks], def.sinif + " bn-zarf-maks"); ciz([0, e.L], [d.min, d.min], def.sinif + " bn-zarf-min"); }
      else ciz(d.x, d.v, def.sinif);
    });
    kap.innerHTML = '<svg class="se-svg bn-dgm-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + kacis(def.uzun + " diyagramı") + '">' + s + "</svg>";
    kap.__hedef = hedef; kap.__W = W; kap.__H = H;
    const nt = document.getElementById("bn-dgm-not");
    if (nt) nt.textContent = (zarf ? "Zarf: koyu ton en büyük, açık ton en küçük değer (1,4G+1,6Q ve G+Q). " : "") + (tur === "M" || tur === "My" ? "Moment çekilen lif tarafına çizilir; " : "") + "etiketler elemandaki en büyük mutlak değerdir (" + (tur === "M" || tur === "My" || tur === "T" ? "kN·m" : "kN") + "). Elemana dokun: kesit tesir kartı.";
  }
  function elemanKarti(no) {
    const v = V(), kap = document.getElementById("bn-eleman-kart"), e = v.ag.elemanlar.filter(function (x) { return x.no === no; })[0];
    if (!kap || !e) return;
    const zarfMi = D.diyagramDurum === "zarf", ks = zarfMi ? durumKisa(Object.keys(v.sonuclar || {})[0] || "G") : durumKisa(D.diyagramDurum), es = ks && elSonuc(ks, e.no);
    if (!es) { kap.innerHTML = ""; return; }
    const ad = e.tur === "kolon" ? kolonAdres(e.kaynak_no) : kirisAdres(e.kaynak_no) + (e.parca > 1 || agEleman("kiris", e.kaynak_no).length > 1 ? " (parça " + e.parca + ")" : "");
    const W = Math.max(260, Math.min(640, kap.clientWidth || 500)), H = 230, pl = 36, L = e.L, sx = (W - 2 * pl) / L;
    const yk = e.tur === "kiris" ? (v.yukler.kirisler || []).filter(function (x) { return x.no === e.kaynak_no; })[0] : null;
    let s = "";
    const dgm = function (y0, vs, def, sinif, baslik) {
      let g = 0; vs.forEach(function (x) { g = Math.max(g, Math.abs(x)); });
      const k = g > 1e-12 ? 26 / g : 0;
      let yol = "M" + pt(pl, y0);
      es.x.forEach(function (x, i) { yol += " L" + pt(pl + x * sx, y0 - def.isaret * vs[i] * k); });
      yol += " L" + pt(pl + L * sx, y0) + " Z";
      s += '<path class="se-asil" d="M' + pt(pl, y0) + " L" + pt(pl + L * sx, y0) + '"/><path class="se-dgm ' + sinif + '" d="' + yol + '"/>' + metinSvg(4, y0 + 4, baslik, "se-eno", "start") + metinSvg(W - 4, y0 - 30, fmt(enBuyuk(vs), 3), "se-etiket", "end");
    };
    if (yk) {
      const q = yk.G.doseme + yk.G.duvar + yk.G.oz + yk.G.ek;
      for (let i = 0; i <= 8; i++) { const x = pl + L * sx * i / 8; s += '<path class="se-yuk-c" d="M' + pt(x, 18) + " L" + pt(x, 40) + '"/>' + C.okBasi(x, 42, 0, 1, "se-yuk-o", 7); }
      s += '<path class="se-yuk-c" d="M' + pt(pl, 18) + " L" + pt(pl + L * sx, 18) + '"/>' + metinSvg(W / 2, 12, "q_G = " + f2(q) + " kN/m" + (yk.Q.doseme + yk.Q.ek ? ", q_Q = " + f2(yk.Q.doseme + yk.Q.ek) + " kN/m" : ""), "se-etiket se-yuk-t", "middle");
    }
    s += '<path class="se-eleman" d="M' + pt(pl, 46) + " L" + pt(pl + L * sx, 46) + '"/>' + metinSvg(pl, 62, "0", "se-eno", "middle") + metinSvg(pl + L * sx, 62, "L = " + f2(L) + " m", "se-eno", "middle");
    dgm(110, es.V, DIYAGRAM.V, "se-dV", "V (kN)");
    dgm(190, es.M, DIYAGRAM.M, "se-dM", "M (kN·m)");
    const enb = es.enb || {};
    kap.innerHTML = '<div class="bn-kart"><b>' + kacis(ad) + "</b> · e" + e.no + " · " + kacis(e.kesit) + " · " + (zarfMi ? kacis(Object.keys(v.sonuclar || {})[0] || "G") : kacis(D.diyagramDurum)) +
      '<div class="se-sekil"><svg class="se-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Eleman kesit tesirleri">' + s + "</svg></div>" +
      '<p class="not">N = ' + fmt(enb.N, 3) + " kN · V_maks = " + fmt(enb.V, 3) + " kN · M_maks = " + fmt(enb.M, 3) + " kN·m · Vz = " + fmt(enb.Vz, 3) + " · My = " + fmt(enb.My, 3) + " · T = " + fmt(enb.T, 3) + "</p></div>";
  }
  // ---------- Tablolar ----------
  function tablolarSekmesi() {
    const v = V();
    let h = '<div class="bn-satir">' + durumSecici("bn-tablo-durum", D.deformeDurum, false) + "</div>";
    const ks = durumKisa(D.deformeDurum);
    if (ks) {
      h += "<h4>Mesnet tepkileri (bina koordinatı; kN, kN·m)</h4>" + tabloH(["Düğüm", "FX", "FY", "FZ", "MX", "MY", "MZ"], (ks.tepkiler || []).map(function (t) { const d = agDugum(t.dugum); return [(d ? d.adres : t.dugum), f1(t.FX), f1(t.FY), f1(t.FZ), f1(t.MX), f1(t.MY), f1(t.MZ)]; }));
      const dn = ks.denge || {}, tamam = ["FX", "FY", "FZ", "MX", "MY", "MZ"].every(function (k) { return dn[k] == null || Math.abs(dn[k]) < 1e-4; });
      h += '<p class="se-denge ' + (tamam ? "tamam" : "sorun") + '"><strong>Denge ' + (tamam ? "sağlandı" : "sağlanmadı") + ":</strong> " + ["FX", "FY", "FZ", "MX", "MY", "MZ"].map(function (k) { return "Σ" + k + " = " + fmt(dn[k], 3); }).join(", ") + "</p>";
    }
    h += "<h4>Kiriş yük dökümü (kN/m; toplam kN)</h4>" + tabloH(["Kiriş", "L", "G döşeme", "G duvar", "G öz", "G ek", "ΣG (kN)", "Q döşeme", "Q ek", "ΣQ (kN)", "R_G≈qL/2", "M_G≈qL²/8"], (v.yukler.kirisler || []).map(function (k) {
      return [kirisAdres(k.no), f2(k.L), f2(k.G.doseme), f2(k.G.duvar), f2(k.G.oz), f2(k.G.ek), f1(k.G.toplam_kN), f2(k.Q.doseme), f2(k.Q.ek), f1(k.Q.toplam_kN), f1(k.el_hesabi.R_G), f1(k.el_hesabi.M_G)];
    }));
    h += "<h4>Döşeme payları (TS 500 11.4.3)</h4>" + tabloH(["Döşeme", "lx×ly", "m", "Tip", "g / q", "Kiriş", "Kenar", "Şekil", "Tepe G", "Tepe Q", "q_eM G", "q_eV G", "Toplam G", "Toplam Q"], [].concat.apply([], (v.yukler.dosemeler || []).map(function (d) {
      return d.paylar.map(function (p, i) { return [i ? "" : dosemeAdres(d.no), i ? "" : f2(d.lx) + "×" + f2(d.ly), i ? "" : f2(d.m), i ? "" : d.tip, i ? "" : f2(d.g) + " / " + f2(d.q), kirisAdres(p.kiris_no), p.kenar, p.sekil, f2(p.tepe_g), f2(p.tepe_q), f2(p.q_eM_g), f2(p.q_eV_g), f1(p.toplam_G), f1(p.toplam_Q)]; });
    })));
    h += "<h4>Kombinasyonlar</h4>" + tabloH(["Ad", "Katsayılar", "Tür", "Kaynak", "Uygulandı"], (v.kombinasyonlar || []).map(function (k) {
      return [k.ad, Object.keys(k.katsayilar || {}).map(function (d) { return k.katsayilar[d] + d; }).join(" + "), k.tur || "", k.kaynak || "", k.uygulandi ? "✓" : "— " + (k.neden || "")];
    }));
    h += "<h4>Ağ</h4>" + tabloH(["Eleman", "Tür", "Kaynak", "Kat", "L (m)", "Kesit", "Düğümler"], (v.ag.elemanlar || []).map(function (e) { return ["e" + e.no, e.tur, e.tur === "kolon" ? kolonAdres(e.kaynak_no) : kirisAdres(e.kaynak_no), String(e.kat), f2(e.L), e.kesit, e.dugumler.join(" → ")]; }));
    return h;
  }
  // ---------- Anlatım ----------
  function anlatimSekmesi() {
    return '<div class="dugmeler"><button type="button" class="dugme kucuk" id="bn-se-ac">G durumunu Sonlu eleman sayfasında aç</button></div><div class="anlatim se-anlatim" id="bn-anlatim"><p class="not">Anlatım hazırlanıyor…</p></div>';
  }
  function anlatimiCiz() {
    const an = document.getElementById("bn-anlatim");
    if (!an || !SON) return;
    if (!an.__bagli) { A.semaOlaylariBagla(an); an.__bagli = true; }
    A.anlatimDersCiz(SON.y, an);
    anlatimCizildi = true;
    an.querySelectorAll("h3, h4").forEach(function (h) { const m = /^\s*(\d+)\./.exec(h.textContent || ""); if (m) h.setAttribute("data-adim-baslik", m[1]); });
  }
  function adimaGit(no) {
    if (!SON || !no) return;
    D.sekme = "anlatim"; sekmeCiz();
    const an = document.getElementById("bn-anlatim");
    const h = an && an.querySelector('[data-adim-baslik="' + no + '"]');
    (h || an || ref.sonuc).scrollIntoView({ block: "start", behavior: azHareket() ? "auto" : "smooth" });
  }
  function seAc() {
    const v = V();
    if (!v || !v.fe_model) { A.toast("Yanıtta fe_model yok."); return; }
    if (typeof A.seModelYukle !== "function") { A.toast("Sonlu eleman sayfası bağlantısı bu sürümde yok."); return; }
    try { A.seModelYukle(kopya(v.fe_model)); } catch (e) { A.toast("Model aktarılamadı: " + (e && e.message ? e.message : e)); }
  }

  // ---------- Olaylar ----------
  function olaylariBagla() {
    kok.addEventListener("click", function (e) {
      const t = e.target.closest("button, [data-sankey]");
      if (!t || !kok.contains(t)) return;
      const ds = t.dataset;
      if (ds.kat != null) { D.kat = +ds.kat; D.kirisBas = null; yenile(); return; }
      if (t.id === "bn-kat-ekle") { document.getElementById("bn-kat-menu").classList.toggle("gizli"); return; }
      if (ds.katIslem) { document.getElementById("bn-kat-menu").classList.add("gizli"); if (ds.katIslem === "sil") katSil(ustKat()); else katEkle(ds.katIslem === "kopyala"); return; }
      if (ds.gorunum) {
        if (ds.gorunum === "sifirla") { kamera.sifirla(); ref.svg.setAttribute("viewBox", kamera.viewBox()); return; }
        kamera.git(ds.gorunum, function (k, bitti) { D.hafif = !bitti; sahneYenile(); if (bitti) { gorunumDugmeleri(); if (D.sekme === "deforme") deformeyiCiz(); if (D.sekme === "diyagram") diyagramiCiz(); } });
        gorunumDugmeleri(); return;
      }
      if (ds.arac) { if (ds.arac === "kutuphane") { D.panelSekme = "kutuphane"; panelAc(); } else { D.arac = ds.arac; D.kirisBas = null; } yenile(); return; }
      if (t.id === "bn-geri") { geriAl(); return; }
      if (t.id === "bn-ileri") { ileriAl(); return; }
      if (t.id === "bn-sihirbaz") { sihirbazAc(); return; }
      if (t.id === "bn-sih-iptal") { ref.sihirbazDlg.close ? ref.sihirbazDlg.close() : ref.sihirbazDlg.removeAttribute("open"); return; }
      if (t.id === "bn-json") { jsonAc(); return; }
      if (t.id === "bn-json-uygula") { jsonUygula(); return; }
      if (t.id === "bn-json-kopyala") { if (navigator.clipboard) navigator.clipboard.writeText(ref.jsonMetin.value).then(function () { A.toast("Kopyalandı."); }, function () { A.toast("Kopyalanamadı."); }); return; }
      if (t.id === "bn-json-indir") { jsonIndir(); return; }
      if (t.id === "bn-json-kapat") { ref.jsonDlg.close ? ref.jsonDlg.close() : ref.jsonDlg.removeAttribute("open"); return; }
      if (t.id === "bn-doldur") { dosemeleriDoldur(); return; }
      if (t.id === "bn-kat-kopyala") { katKopyalaAlttan(); return; }
      if (t.id === "bn-firca-kapat") { D.firca = null; yenile(); return; }
      if (t.id === "bn-formul-kapat") { ref.formul.classList.add("gizli"); D.formul = null; return; }
      if (ds.psek) { D.panelSekme = ds.psek; ustCubukCiz(); panelCiz(); return; }
      if (t.id === "bn-ayni-tur") { ayniTurdenSec(); return; }
      if (t.id === "bn-secim-sil") { secimiSil(); return; }
      if (t.id === "bn-yuk-yolu") { if (D.secim.length) { D.akisHedef = D.secim[0]; D.sekme = "akis"; sonucuCiz(); sahneCiz(); ref.sahneKutu.scrollIntoView({ block: "nearest" }); } return; }
      if (ds.aksEkle) { aksEkle(ds.aksEkle); return; }
      if (ds.aksSil) { const p = ds.aksSil.split(":"); aksSil(p[0], +p[1]); return; }
      if (ds.katSil) { katSil(+ds.katSil); return; }
      if (ds.firca) { D.firca = D.firca === ds.firca ? null : ds.firca; D.arac = "sec"; yenile(); return; }
      if (ds.kesitSil) { kesitSil(ds.kesitSil); return; }
      if (t.id === "bn-yk-ekle") { yeniKesitEkle(); return; }
      if (t.id === "bn-coz") { coz(); return; }
      if (ds.adim != null && !t.disabled) { adimaGit(+ds.adim); return; }
      if (ds.sekme) { D.sekme = ds.sekme; sekmeCiz(); return; }
      if (ds.akisDurum) { D.akisDurum = ds.akisDurum; sekmeCiz(); return; }
      if (t.id === "bn-oynat") { oynatToggle(); return; }
      if (ds.sankey != null) { D.sankeySecim = D.sankeySecim === ds.sankey ? null : ds.sankey; sankeyCiz(); return; }
      if (ds.dgm) { D.diyagram = ds.dgm; diyagramiCiz(); return; }
      if (t.id === "bn-se-ac") { seAc(); return; }
    });
    kok.addEventListener("keydown", function (e) {
      const t = e.target.closest("[data-sankey]");
      if (t && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); D.sankeySecim = D.sankeySecim === t.dataset.sankey ? null : t.dataset.sankey; sankeyCiz(); }
    });
    kok.addEventListener("change", function (e) {
      const el = e.target, ds = el.dataset;
      if (el.id === "bn-sablon") { if (el.value) sablonYukle(el.value); return; }
      if (el.id === "bn-tum-katlar") { D.tumKatlar = el.checked; return; }
      if (ds.oz) { ozellikDegistir(ds.oz, el.value); return; }
      if (ds.bina) { B[ds.bina] = el.value; degisti(); return; }
      if (ds.temel) { B.temeller[ds.temel] = el.value; degisti(); return; }
      if (ds.temelV) { const n = sayiOku(el.value); if (n != null && n > 0) { B.temeller.varsayilan[ds.temelV] = n; degisti(); } return; }
      if (ds.zemin) { const n = sayiOku(el.value); if (n != null && n > 0) { B.temeller.zemin[ds.zemin] = n; degisti(); } return; }
      if (ds.aks) { aksDegistir(ds.aks, +ds.i, ds.a, el.value); return; }
      if (ds.katI != null) { katDegistir(+ds.katI, ds.a, el.value); return; }
      if (el.id === "bn-yk-tip") { document.getElementById("bn-yk-dik").style.display = el.value === "profil" ? "none" : ""; document.getElementById("bn-yk-prof").style.display = el.value === "profil" ? "" : "none"; return; }
      if (el.id === "bn-def-durum") { D.deformeDurum = el.value; deformeyiCiz(); return; }
      if (el.id === "bn-tablo-durum") { D.deformeDurum = el.value; sekmeCiz(); return; }
      if (el.id === "bn-dgm-durum") { D.diyagramDurum = el.value; diyagramiCiz(); return; }
      if (el.id === "bn-aks-filtre") { D.aksFiltre = el.value; diyagramiCiz(); return; }
      if (el.name === "sistem" && el.form === ref.sihirbazForm) { ref.sihirbazForm.querySelector(".bn-sih-dik").style.display = el.value === "celik" ? "none" : ""; ref.sihirbazForm.querySelector(".bn-sih-prof").style.display = el.value === "celik" ? "" : "none"; }
    });
    kok.addEventListener("input", function (e) {
      const el = e.target;
      if (el.id === "bn-olcek") { D.olcek = +el.value || 0; deformeyiCiz(); }
    });
    ref.sihirbazForm.addEventListener("submit", function (e) { e.preventDefault(); sihirbazUret(); ref.sihirbazDlg.close ? ref.sihirbazDlg.close() : ref.sihirbazDlg.removeAttribute("open"); });
    ref.jsonDosya.addEventListener("change", function () {
      const f = ref.jsonDosya.files && ref.jsonDosya.files[0];
      if (!f) return;
      const okuyucu = new FileReader();
      okuyucu.onload = function () { ref.jsonMetin.value = String(okuyucu.result || ""); jsonUygula(); };
      okuyucu.readAsText(f);
      ref.jsonDosya.value = "";
    });
    // diyagram SVG'sinde elemana dokun → kart
    kok.addEventListener("pointerup", function (e) {
      const kap = e.target.closest ? e.target.closest("#bn-dgm-sekil") : null;
      if (!kap || !kap.__hedef) return;
      const svg = kap.querySelector("svg"), r = svg.getBoundingClientRect();
      const s = Math.min(r.width / kap.__W, r.height / kap.__H) || 1;
      const x = (e.clientX - r.left - (r.width - kap.__W * s) / 2) / s, y = (e.clientY - r.top - (r.height - kap.__H * s) / 2) / s;
      const h = C.vurus(kap.__hedef, x, y);
      if (h) elemanKarti(h.no);
    });
    document.addEventListener("click", function (e) {
      const m = document.getElementById("bn-kat-menu");
      if (m && !m.classList.contains("gizli") && !e.target.closest(".bn-menu")) m.classList.add("gizli");
    });
    document.addEventListener("keydown", function (e) {
      const sayfa = document.getElementById("sayfa-bina");
      if (!sayfa || !sayfa.classList.contains("aktif")) return;
      const t = e.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
      if (document.querySelector("dialog[open]")) return;
      const k = e.key;
      if ((e.ctrlKey || e.metaKey) && (k === "z" || k === "Z")) { e.preventDefault(); if (e.shiftKey) ileriAl(); else geriAl(); return; }
      if ((e.ctrlKey || e.metaKey) && (k === "y" || k === "Y")) { e.preventDefault(); ileriAl(); return; }
      if ((e.ctrlKey || e.metaKey) && k === "Enter") { e.preventDefault(); coz(); return; }
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const kisayol = { s: "sec", k: "kolon", r: "kiris", d: "doseme", w: "duvar" };
      const kl = k.toLowerCase();
      if (kisayol[kl]) { D.arac = kisayol[kl]; D.kirisBas = null; yenile(); return; }
      if (k === "Delete" || k === "Backspace") { if (D.secim.length) { e.preventDefault(); secimiSil(); } else { D.arac = "sil"; yenile(); } return; }
      if (k === "Escape") { D.kirisBas = null; D.secim = []; D.firca = null; yenile(); }
    });
    window.addEventListener("hashchange", hashKontrol);
  }
  function ozellikDegistir(ad, deger) {
    if (!D.secim.length) return;
    const tur = D.secim[0].tur;
    if (deger === "__yeni") { D.panelSekme = "kutuphane"; A.toast("Kütüphanede “Yeni kesit” ya da duvar türü ekleyin; fırçayla atayın."); yenile(); return; }
    D.secim.forEach(function (s) {
      const n = nesneBul(s.tur, s.no);
      if (!n || s.tur !== tur) return;
      if (ad === "kesit") n.kesit = deger;
      else if (ad === "yon") n.yon = deger === "y" ? "y" : "x";
      else if (ad === "duvar") n.duvar = deger || null;
      else if (ad === "ekG" || ad === "ekQ") {
        const durum = ad === "ekG" ? "G" : "Q", q = sayiOku(deger);
        B.ek_yukler = B.ek_yukler.filter(function (e) { return !(e.tur === "kiris" && e.kiris === n.no && e.durum === durum); });
        if (q) B.ek_yukler.push({ tur: "kiris", kiris: n.no, durum: durum, q: q });
      } else if (ad === "h" || ad === "g_ek") { const v = sayiOku(deger); if (v != null && v >= 0) n[ad] = v; }
      else if (ad === "q") { const v = sayiOku(deger); n.q = v == null ? null : v; }
      else if (ad === "kullanim") n.kullanim = deger;
      else if (ad === "dagitim") n.dagitim = deger;
      else if (ad === "kaplama") { n.kaplama = deger || null; const kp = (KUT.kaplamalar || []).filter(function (x) { return x.ad === deger; })[0]; if (kp) n.g_ek = kp.g; }
    });
    degisti();
  }
  function aksEkle(e) {
    const l = B.akslar[e], n = l.length;
    const son = n ? +l[n - 1].konum : 0, aralik = n >= 2 ? +l[n - 1].konum - +l[n - 2].konum : (e === "x" ? 5 : 4);
    const ad = e === "x" ? harf(n) : String(n + 1);
    if (l.some(function (a) { return a.ad === ad; })) { A.toast("Aks adı çakışıyor: " + ad); return; }
    l.push({ ad: ad, konum: +(son + aralik).toFixed(3) });
    degisti();
  }
  function aksSil(e, i) {
    const a = B.akslar[e][i];
    if (!a) return;
    const bagli = B.kolonlar.filter(function (c) { return c.aks[e === "x" ? 0 : 1] === a.ad; }).length + B.kirisler.filter(function (k) { return k.bas[e === "x" ? 0 : 1] === a.ad || k.son[e === "x" ? 0 : 1] === a.ad; }).length;
    if (bagli && !window.confirm("Aks " + a.ad + " silinince bağlı " + bagli + " eleman da silinir. Devam?")) return;
    const ix = e === "x" ? 0 : 1;
    B.akslar[e].splice(i, 1);
    B.kolonlar = B.kolonlar.filter(function (c) { return c.aks[ix] !== a.ad; });
    B.kirisler = B.kirisler.filter(function (k) { return k.bas[ix] !== a.ad && k.son[ix] !== a.ad; });
    B.dosemeler = B.dosemeler.filter(function (d) { return d.kose[0][ix] !== a.ad && d.kose[1][ix] !== a.ad; });
    degisti();
  }
  function aksDegistir(e, i, alan, deger) {
    const a = B.akslar[e][i];
    if (!a) return;
    if (alan === "konum") { const n = sayiOku(deger); if (n == null) { A.toast("Konum sayı olmalı."); panelCiz(); return; } a.konum = Math.round(n * 20) / 20; B.akslar[e].sort(function (p, q) { return p.konum - q.konum; }); }
    else {
      const yeni = String(deger).trim();
      if (!yeni || B.akslar[e].some(function (x, j) { return j !== i && x.ad === yeni; })) { A.toast("Aks adı boş ya da çakışıyor."); panelCiz(); return; }
      const ix = e === "x" ? 0 : 1, eski = a.ad;
      a.ad = yeni;
      B.kolonlar.forEach(function (c) { if (c.aks[ix] === eski) c.aks[ix] = yeni; });
      B.kirisler.forEach(function (k) { if (k.bas[ix] === eski) k.bas[ix] = yeni; if (k.son[ix] === eski) k.son[ix] = yeni; });
      B.dosemeler.forEach(function (d) { if (d.kose[0][ix] === eski) d.kose[0][ix] = yeni; if (d.kose[1][ix] === eski) d.kose[1][ix] = yeni; });
      (B.temeller.ozel || []).forEach(function (o) { if (o.aks[ix] === eski) o.aks[ix] = yeni; });
    }
    degisti();
  }
  function katDegistir(i, alan, deger) {
    const k = B.katlar[i];
    if (!k) return;
    if (alan === "ad") k.ad = String(deger).trim() || k.ad;
    else { const n = sayiOku(deger); if (n == null || (i > 0 && n <= B.katlar[i - 1].kot) || (i < B.katlar.length - 1 && n >= B.katlar[i + 1].kot)) { A.toast("Kot komşu katların arasında olmalı."); panelCiz(); return; } k.kot = n; }
    degisti();
  }
  function kesitSil(ad) {
    const kullanim = B.kolonlar.filter(function (c) { return c.kesit === ad; }).length + B.kirisler.filter(function (k) { return k.kesit === ad; }).length;
    if (kullanim) { A.toast("Bu kesit " + kullanim + " elemanda kullanılıyor; önce başka kesit atayın."); return; }
    delete B.kesitler[ad];
    if (D.firca === ad) D.firca = null;
    degisti();
  }
  function hashKontrol() {
    let h = (location.hash || "").replace(/^#/, "");
    try { h = decodeURIComponent(h); } catch (e) { /* olduğu gibi */ }
    const m = /^bina\/sablon\/(.+)$/.exec(h);
    if (!m) return;
    A.sayfaGoster("bina", true);
    const ad = m[1];
    if (ref.sablon) ref.sablon.value = ad;
    sablonYukle(ad);
  }

  // ---------- Başlatma ----------
  let basladi = false, sonGenislik = 0;
  function baslat() {
    iskeletKur();
    sablonListesi();
    sahneBoyutla();
    jestleriKur();
    olaylariBagla();
    const taslak = taslakOku();
    let yuklendi = false;
    if (taslak) { try { B = binaYukle(taslak); yuklendi = true; } catch (e) { yuklendi = false; } }
    if (!yuklendi) B = YERLESIK_SABLON["betonarme-2kat-3x2"]();
    sonAnlik = anlikGoruntu();
    D.kat = Math.min(Math.max(1, ustKat()), D.kat);
    yenile();
    kutuphaneyiAl();
    sablonlariAl();
    hashKontrol();
  }
  function acilis() {
    const ilk = function () { basladi = true; sonGenislik = kok.clientWidth; baslat(); };
    if (typeof ResizeObserver !== "function") { ilk(); return; }
    let bekleyen = 0;
    new ResizeObserver(function () {
      const w = kok.clientWidth;
      if (!w) return;
      if (!basladi) { ilk(); return; }
      if (Math.abs(w - sonGenislik) < 24) return;
      sonGenislik = w;
      cancelAnimationFrame(bekleyen);
      bekleyen = requestAnimationFrame(function () { sahneBoyutla(); sahneCiz(); if (SON) { sankeyCiz(); deformeyiCiz(); diyagramiCiz(); } });
    }).observe(kok);
  }
  acilis();
})();
