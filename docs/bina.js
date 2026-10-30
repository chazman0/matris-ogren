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
  const YERLESIM_ANAHTAR = "bina.yerlesim";   // araç çubuğu / özellik paneli daraltma, çekmece yüksekliği (görüntüleyene özel kolaylık)
  // Temel tipleri (tasarım §13): varsayılanlar
  const TEMEL_VARS = {
    surekli: { yon: "xy", akslar: "tum", B: 1.2, h_tabla: 0.40, b_govde: 0.50, h_govde: 1.00, tasma: 0.5, ag: 0.5 },
    radye: { h: 0.80, tasma: 1.0, ag: 0.5, kiris: null },
    kiris: { b: 0.50, h: 1.20 },
    zemin: { q_em: 200, k0: 20000 },
  };
  const TEMEL_TIP_AD = { tekil: "Tekil", surekli: "Mütemadi (sürekli)", radye: "Radye" };
  const GECMIS_EN_FAZLA = 50;

  // ---------- TBDY 2018 (değerler arastirma_tbdy2018.json'dan; Tablo 2.1, 2.2, 3.1, 3.2, 3.3, 4.1, 4.3; md. 4.7.3.4) ----------
  // UI'daki yerel hesap yalnız canlı önizleme ve motor yokken içindir; bağlayıcı değerler motordan (bina_deprem / bina_coz) gelir.
  const TBDY = {
    FS: { SS: [0.25, 0.5, 0.75, 1.0, 1.25, 1.5], ZA: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], ZB: [0.9, 0.9, 0.9, 0.9, 0.9, 0.9], ZC: [1.3, 1.3, 1.2, 1.2, 1.2, 1.2], ZD: [1.6, 1.4, 1.2, 1.1, 1.0, 1.0], ZE: [2.4, 1.7, 1.3, 1.1, 0.9, 0.8] },
    F1: { S1: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], ZA: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], ZB: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], ZC: [1.5, 1.5, 1.5, 1.5, 1.5, 1.4], ZD: [2.4, 2.2, 2.0, 1.9, 1.8, 1.7], ZE: [4.2, 3.3, 2.8, 2.4, 2.2, 2.0] },
    I: { 1: 1.5, 2: 1.2, 3: 1.0 },
    BKS: [[1, "BKS 1 — hastane, okul, itfaiye, yurt, müze… (I = 1,5)"], [2, "BKS 2 — AVM, spor tesisi, sinema, ibadethane (I = 1,2)"], [3, "BKS 3 — konut, işyeri, otel, endüstri (I = 1,0)"]],
    n: [[0.3, "n = 0,3 — konut, işyeri, otel, hastane, otopark"], [0.6, "n = 0,6 — okul, yurt, spor, sinema, lokanta, mağaza"], [0.8, "n = 0,8 — depo, antrepo"]],
    Ct: [[0.1, "C_t = 0,10 — yalnız betonarme çerçeve"], [0.08, "C_t = 0,08 — çelik çerçeve / çaprazlı çelik çerçeve"], [0.07, "C_t = 0,07 — diğer bütün binalar"]],
    zemin: ["ZA", "ZB", "ZC", "ZD", "ZE"],
    TL: 6.0,
  };
  // Tablo 4.1'den UI için seçilmiş alt küme (motor kütüphanesi `tasiyici_sistemler` gelince onun listesi kullanılır)
  const YERLESIK_TASIYICI = [
    { ad: "betonarme-cerceve-yuksek", etiket: "A11 — Tamamı moment aktaran SDY betonarme çerçeve", R: 8, D: 3, BYS_izin: "≥ 3", sistem: "betonarme" },
    { ad: "betonarme-perde-bosluksuz", etiket: "A13 — Tamamı SDY boşluksuz betonarme perde", R: 6, D: 2.5, BYS_izin: "≥ 2", sistem: "betonarme" },
    { ad: "betonarme-perde-cerceve", etiket: "A15 — SDY çerçeve + SDY boşluksuz perde", R: 7, D: 2.5, BYS_izin: "≥ 2", sistem: "betonarme" },
    { ad: "betonarme-cerceve-sinirli", etiket: "A31 — Tamamı SDS betonarme çerçeve (yalnız DTS 3, 4)", R: 4, D: 2.5, BYS_izin: "≥ 7", sistem: "betonarme" },
    { ad: "betonarme-tek-katli-mafsalli", etiket: "A16 — Tek katlı, çatısı mafsallı SDY kolonlar (H ≤ 12 m)", R: 3, D: 2, BYS_izin: "–", sistem: "betonarme" },
    { ad: "celik-cerceve-yuksek", etiket: "C11 — Tamamı moment aktaran SDY çelik çerçeve", R: 8, D: 3, BYS_izin: "≥ 3", sistem: "celik" },
    { ad: "celik-dismerkez-capraz", etiket: "C12 — SDY dışmerkez çaprazlı / burkulması önlenmiş çaprazlı çerçeve", R: 8, D: 2.5, BYS_izin: "≥ 2", sistem: "celik" },
    { ad: "celik-merkezi-capraz", etiket: "C13 — Tamamı SDY merkezi çaprazlı çelik çerçeve", R: 5, D: 2, BYS_izin: "≥ 4", sistem: "celik" },
    { ad: "celik-cerceve-sinirli", etiket: "C31 — Tamamı moment aktaran SDS çelik çerçeve", R: 4, D: 2.5, BYS_izin: "≥ 7", sistem: "celik" },
    { ad: "celik-tek-katli-mafsalli", etiket: "C16 — Tek katlı, çatısı mafsallı SDY çelik kolonlar (H ≤ 12 m)", R: 4, D: 2, BYS_izin: "–", sistem: "celik" },
  ];
  const YUK_DURUM_AD = { G: "G sabit", Q: "Q hareketli", S: "S kar", W: "W rüzgâr", E: "E deprem" };
  function tasiyiciListesi() { return (KUT.tasiyici_sistemler && KUT.tasiyici_sistemler.length) ? KUT.tasiyici_sistemler : YERLESIK_TASIYICI; }
  function tasiyiciBul(ad) { return tasiyiciListesi().filter(function (t) { return t.ad === ad; })[0] || null; }
  function araDeger(xs, ys, x) {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
    for (let i = 0; i < xs.length - 1; i++) if (x >= xs[i] && x <= xs[i + 1]) { const t = (x - xs[i]) / (xs[i + 1] - xs[i]); return ys[i] + t * (ys[i + 1] - ys[i]); }
    return ys[ys.length - 1];
  }
  // Yatay elastik tasarım spektrumu S_ae(T) (Denk. 2.2) ve azaltma katsayısı R_a(T) (Denk. 4.1)
  function tbdySae(T, p) {
    if (T <= p.TA) return (0.4 + 0.6 * T / p.TA) * p.SDS;
    if (T <= p.TB) return p.SDS;
    if (T <= p.TL) return p.SD1 / T;
    return p.SD1 * p.TL / (T * T);
  }
  function tbdyRa(T, p) { return T > p.TB ? p.R / p.I : p.D + (p.R / p.I - p.D) * T / p.TB; }
  // Deprem girdisinden spektrum parametreleri (S_DS, S_D1, T_A, T_B; Denk. 2.1, 2.3)
  function spektrumParametreleri(dep, dd3) {
    const zs = TBDY.FS[dep.zemin_sinifi] ? dep.zemin_sinifi : "ZC";
    const SS = dd3 ? (+dep.SS_DD3 || 0) : (+dep.SS || 0), S1 = dd3 ? (+dep.S1_DD3 || 0) : (+dep.S1 || 0);
    const FS = araDeger(TBDY.FS.SS, TBDY.FS[zs], SS), F1 = araDeger(TBDY.F1.S1, TBDY.F1[zs], S1);
    const SDS = SS * FS, SD1 = S1 * F1;
    const I = TBDY.I[+dep.BKS] || +dep.I || 1.0;
    return { SS: SS, S1: S1, FS: FS, F1: F1, SDS: SDS, SD1: SD1, TA: SDS > 0 ? 0.2 * SD1 / SDS : 0, TB: SDS > 0 ? SD1 / SDS : 0, TL: TBDY.TL, I: I, R: +dep.R || 8, D: +dep.D || 3 };
  }
  function dtsHesapla(SDS, BKS) { const t = SDS >= 0.75 ? "1" : SDS >= 0.5 ? "2" : SDS >= 0.33 ? "3" : "4"; return t + (+BKS === 1 ? "a" : ""); }
  function bysHesapla(HN, DTS) {
    // Tablo 3.3: DTS 1,1a,2,2a ve DTS 3,3a,4,4a sütunları
    const d = /^[12]/.test(String(DTS));
    const sinir = d ? [[7, 8], [10.5, 7], [17.5, 6], [28, 5], [42, 4], [56, 3], [70, 2]] : [[10.5, 8], [17.5, 7], [28, 6], [42, 5], [56, 4], [70, 3], [91, 2]];
    for (let i = 0; i < sinir.length; i++) if (HN <= sinir[i][0]) return sinir[i][1];
    return 1;
  }
  // Kat ağırlıkları tahmini (UI; motor yokken önizleme): w_i = G_i + n·Q_i (Denk. 4.16)
  function katAgirlikTahmini() {
    const n = (B.deprem && +B.deprem.n) || 0.3, out = [];
    B.katlar.filter(function (k) { return k.no >= 1; }).forEach(function (k) {
      let G = 0, Q = 0;
      B.dosemeler.filter(function (d) { return d.kat === k.no; }).forEach(function (d) {
        const lx = Math.abs(aksX(d.kose[1][0]) - aksX(d.kose[0][0])), ly = Math.abs(aksY(d.kose[1][1]) - aksY(d.kose[0][1]));
        if (!isFinite(lx) || !isFinite(ly)) return;
        G += lx * ly * (GAMMA_B * (+d.h || 0) + (+d.g_ek || 0)); Q += lx * ly * (d.q != null ? +d.q : kullanimQ(d.kullanim));
      });
      B.kirisler.filter(function (x) { return x.kat === k.no; }).forEach(function (x) {
        const o = kesitOz(x.kesit), L = kirisUzunluk(x); if (!o || !isFinite(L)) return;
        const m = malzemeKart(o.malzeme), gam = m.gamma || (o.celik ? GAMMA_S : GAMMA_B);
        G += gam * o.A * L;
        // duvar: verilmişse duvar_h (çatıda parapet), yoksa ara katta kat yüksekliği − kiriş
        if (x.duvar && x.duvar_h != null && x.duvar_h !== "") G += duvarW(x.duvar) * Math.max(0, +x.duvar_h || 0) * L;
        else if (x.duvar && k.no < ustKat()) G += duvarW(x.duvar) * Math.max(0, katH(k.no + 1) - o.h) * L;
      });
      B.kolonlar.filter(function (c) { return c.kat === k.no; }).forEach(function (c) {
        const o = kesitOz(c.kesit); if (!o) return;
        const m = malzemeKart(o.malzeme), gam = m.gamma || (o.celik ? GAMMA_S : GAMMA_B);
        G += gam * o.A * katH(c.kat);
      });
      out.push({ kat: k.no, H: +k.kot, h: katH(k.no), G: G, Q: Q, w_i: G + n * Q, m_i: (G + n * Q) / 9.81 });
    });
    return out;
  }
  // Eşdeğer deprem yükü tahmini (md. 4.7): spektrum, T_pA, S_aR, V_tE, ΔF_N, F_i, V_i — şekli `veri.deprem` ile aynı (tahmin: true)
  function depremTahmini() {
    const dep = B.deprem || {}, p = spektrumParametreleri(dep), p3 = spektrumParametreleri(dep, true);
    const katlar = katAgirlikTahmini(), N = katlar.length, HN = N ? katlar[N - 1].H : 0;
    const Ct = +dep.Ct || 0.1, TpA = Ct * Math.pow(Math.max(HN, 0.01), 0.75), Tp = TpA;
    const Sae = tbdySae(Tp, p), Ra = tbdyRa(Tp, p), SaR = Ra > 0 ? Sae / Ra : 0;
    const W = katlar.reduce(function (t, k) { return t + k.w_i; }, 0);
    const VtE = W * SaR, VtEmin = 0.04 * p.I * p.SDS * W, Vt = Math.max(VtE, VtEmin), dFN = 0.0075 * N * Vt;
    const swh = katlar.reduce(function (t, k) { return t + k.w_i * k.H; }, 0) || 1;
    let kum = 0;
    const kat = katlar.map(function (k, i) { return Object.assign({}, k, { F_x: (Vt - dFN) * k.w_i * k.H / swh + (i === N - 1 ? dFN : 0) }); });
    for (let i = N - 1; i >= 0; i--) { kum += kat[i].F_x; kat[i].V_x = kum; kat[i].F_y = kat[i].F_x; kat[i].V_y = kum; }
    const spek = [];
    for (let T = 0; T <= 3.0001; T += T < 0.6 ? 0.02 : 0.1) { const s = tbdySae(T, p); spek.push([+T.toFixed(3), s, s / tbdyRa(T, p)]); }
    const DTS = dtsHesapla(p.SDS, dep.BKS), BYS = bysHesapla(HN, DTS);
    const Sae3 = tbdySae(Tp, p3), lam = Sae > 0 && p3.SDS > 0 ? Sae3 / Sae : null;
    return { tahmin: true, FS: p.FS, F1: p.F1, SDS: p.SDS, SD1: p.SD1, TA: p.TA, TB: p.TB, TL: p.TL, SDS_DD3: p3.SDS, SD1_DD3: p3.SD1, DTS: DTS, BYS: BYS, I: p.I, R: p.R, D: p.D, n: +dep.n || 0.3, HN: HN,
      TpA: TpA, Tp: Tp, Tp_yontem: "ampirik", Sae_Tp: Sae, Ra: Ra, SaR: SaR, W_t: W, m_t: W / 9.81, VtE: VtE, VtE_min: VtEmin, dFN: dFN, lambda: lam, katlar: kat, spektrum: spek,
      uyarilar: [], uygulanabilir: BYS >= 4 };
  }

  // ---------- Durum ----------
  let B = null;                         // bina JSON (§3)
  let KUT = YERLESIK_KUTUPHANE;         // kütüphane (motor ya da yerleşik)
  let SON = null;                       // son çözüm yanıtı {y, veri}
  let sonEski = false;                  // model çözümden sonra değişti
  let ONIZLEME = null;                  // deprem kartı canlı önizlemesi {deprem, kaynak: "motor"|"tahmin"}
  let onizlemeZ = 0, onizlemeSira = 0;  // 400 ms gecikme ve yarış koruması
  const KOMB_BEKLEYEN = {};             // tembel kombinasyon / tam durum istekleri (ad → Promise)
  const TASARIM_AYR = {};               // bina_eleman_tasarim yanıtları ("tur:no" → yanıt | Promise)
  const D = {
    kat: 1, arac: "sec", gorunum: "3b", secim: [], tumKatlar: false, firca: null, kirisBas: null,
    sekme: "akis", akisDurum: "G", akisHedef: null, oynat: 0, diyagram: "M", diyagramDurum: "1.4G+1.6Q", aksFiltre: "", deformeDurum: "G+Q", olcek: 100,
    hafif: false, sankeySecim: null, formul: null, cozuluyor: false, panelSekme: "nesne", depremYon: "x", depremOk: true,
    dcGorunum: true, tasarimSecim: null, tasarimFiltre: "", nmEksen: "x",
    aracKapali: false, panelKapali: false, tamEkran: false, gercekTam: false, cekmeceH: 0, cekmeceKapali: true, temelHarita: "p", sonRadyeKiris: null,
    panelW: 0, sonucYer: "alt", sonucW: 0, yuzen: { arac: null, panel: null },
    // görünüm süzgeçleri ve gösterim (araç kutusu Görünüm komutları; .matris projesinde saklanır)
    gizli: {}, yalit: null, katSuzgec: null, telKafes: false, etiketler: false, izgara: true, cephe: { x: null, y: null },
    // §19 aks tabanlı modelleme: plan düzleminin Z aksı (null: etkin katın Z aksı; "Mahya" gibi kat dışı Z aksları da olabilir)
    zAks: null, aksOlcu: true, aksBalon: true,
  };
  (function () {
    try {
      const y = JSON.parse(localStorage.getItem(YERLESIM_ANAHTAR) || "{}") || {};
      const nk = function (k) { return k && isFinite(+k.x) && isFinite(+k.y) ? { x: +k.x, y: +k.y } : null; };
      D.aracKapali = !!y.arac; D.panelKapali = !!y.panel; D.cekmeceH = +y.cekmece || 0;
      D.panelW = +y.panelW > 0 ? +y.panelW : 0; D.sonucW = +y.sonucW > 0 ? +y.sonucW : 0; D.sonucYer = y.sonucYer === "sag" ? "sag" : "alt";
      if (y.yuzen) D.yuzen = { arac: nk(y.yuzen.arac), panel: nk(y.yuzen.panel) };
    } catch (e) { /* depolama yok */ }
  })();
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
  // Motorun basit kesit adları (BORU 168.3x6.3, KUTU 150x8, L 100x10, 2L 70x7 s=10, UPN 200): MatrisIFC.basitProfil (sözleşme C9;
  // m, m², m⁴, Iy güçlü eksen). Modül ya da işlev yoksa null.
  function basitProfil(ad) {
    const M = window.MatrisIFC;
    if (!M || typeof M.basitProfil !== "function" || !ad) return null;
    try { const p = M.basitProfil(ad); return p && p.A > 0 ? p : null; } catch (e) { return null; }
  }
  // Bir kesit kaydından (B.kesitler[ad]) sayısal özellikler: m, m², m⁴ (Iy zayıf, Iz güçlü eksen). Vute (tip "vute": temel kesit +
  // ek_yukseklik / boy uç büyütmesi) temel kesitin özelliklerini taşır (malzeme, çelik/beton); profil alanı okunur bir etiket olur
  // (ör. "IPE 400 + vute 0,4 m / 2 m"). derin: vute → vute zincirine karşı özyineleme sınırı (kesitBoyut gibi).
  function kesitOz(ad, derin) {
    const k = B.kesitler[ad];
    if (!k) return null;
    if (k.tip === "vute") {
      if ((derin || 0) > 3) return null;
      const t = kesitOz(k.temel, (derin || 0) + 1);
      if (!t) return null;
      return Object.assign({}, t, { tip: "vute", ad: ad, temel: k.temel, temelTip: t.tip,
        profil: kesitEtiketi(t) + " + vute " + fmt(+k.ek_yukseklik || 0) + " m / " + fmt(+k.boy || 0) + " m" });
    }
    if (k.tip === "profil" && !profilBul(k.profil)) {
      const bp = basitProfil(k.profil);
      if (bp) return { tip: "profil", ad: ad, profil: k.profil, b: +bp.b, h: +bp.h, A: +bp.A, Iy: +bp.Iz, Iz: +bp.Iy, J: +bp.J || 0, g: +bp.A * GAMMA_S, malzeme: k.malzeme, celik: true };
    }
    if (k.tip === "profil") {
      const p = profilBul(k.profil) || { h: 300, b: 150, A: 50, Iy: 8000, Iz: 600, g: 40 };
      return { tip: "profil", ad: ad, profil: k.profil, b: p.b / 1000, h: p.h / 1000, A: p.A / 1e4, Iy: p.Iz / 1e8, Iz: p.Iy / 1e8, J: (p.It || 10) / 1e8, g: p.g / 100, malzeme: k.malzeme, celik: true };
    }
    const b = +k.b || 0.3, h = +k.h || 0.5;
    return { tip: "dikdortgen", ad: ad, b: b, h: h, A: b * h, Iy: h * b * b * b / 12, Iz: b * h * h * h / 12, J: Jdik(b, h), Wpl: b * h * h / 4, malzeme: k.malzeme, celik: false };
  }
  // kesitOz sonucunun kısa etiketi: profil adı (vute: "temel + vute …"), dikdörtgende b×h cm
  function kesitEtiketi(o) {
    if (!o) return "";
    return o.tip === "profil" || o.tip === "vute" ? String(o.profil || o.ad || "") : Math.round(o.b * 100) + "×" + Math.round(o.h * 100) + " cm";
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
    if (tur === "mesnet") return (B.mesnetler || [])[+no - 1] || null;          // mesnetler numarasız: sıra (1'den)
    const l = tur === "kolon" ? B.kolonlar : tur === "kiris" ? B.kirisler : tur === "doseme" ? B.dosemeler :
      tur === "cubuk" ? B.cubuklar || [] : tur === "panel" ? B.paneller || [] : tur === "dugum" ? B.dugumler || [] : [];
    return l.filter(function (x) { return x && +x.no === +no; })[0] || null;
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
    let ek = 0;
    if (s3Var()) {      // genel model: çubuk uçlarındaki ayrı noktalar (temel kotundakiler hariç)
      const kot0 = B.katlar.length ? +B.katlar[0].kot : 0, gor = {};
      (B.cubuklar || []).forEach(function (c) { [c.i, c.j].forEach(function (r) { const P = refP(r); if (P && Math.abs(P[2] - kot0) > 1e-6) gor[P.map(function (v) { return v.toFixed(3); }).join(",")] = 1; }); });
      ek = Object.keys(gor).length * 6;
    }
    return Math.max(0, (Object.keys(dugum).length - temel) * 6) + ek;
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
      tur: "bina", surum: 1, baslik: p.baslik || (n + " katlı " + (celik ? "çelik" : "betonarme") + " bina (" + (xs.length + 1) + "×" + (ys.length + 1) + " aks)"),
      aciklama: p.aciklama || "Sihirbazla üretildi.", sistem: celik ? "celik" : "betonarme", birim: { kuvvet: "kN", uzunluk: "m" },
      akslar: { x: ax, y: ay }, katlar: katlar, malzemeler: malzemeler, kesitler: kesitler,
      kolonlar: kolonlar, kirisler: kirisler, dosemeler: dosemeler,
      duvarlar: duvarKip === "yok" ? {} : { duvar1: { kutuphane: duvarTip } },
      ek_yukler: [],
      temeller: { tip: "tekil", varsayilan: { B: 1.6, L: 1.6, h: 0.6 }, zemin: { q_em: 200, k0: 20000 }, mesnet: "ankastre", ozel: [] },
      yuk_durumlari: { G: { acik: true }, Q: { acik: true }, S: { acik: false, bolge: 1, rakim: 100, mu: 0.8 }, W: { acik: false, C: 1.2 }, E: { acik: false } },
      deprem: { SS: 1.0, S1: 0.3, SS_DD3: 0.4, S1_DD3: 0.12, zemin_sinifi: "ZC", DD: "DD-2", BKS: 3, I: 1.0, tasiyici: celik ? "celik-cerceve-yuksek" : "betonarme-cerceve-yuksek", R: 8, D: 3, n: 0.3, Ct: celik ? 0.08 : 0.1, periyot: "ampirik", diyafram: "rijit", dismerkezlik: 0.05, dolgu: "bitisik" },
      kombinasyon_kumesi: celik ? "cythye_ydkt" : "ts500", analiz: { catlamis_rijitlik: !celik, diyagram_nokta: 11 },   // TBDY 4.5.8.1: betonarmede çatlamış kesit
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
    // aks–kat motoru sınırları (12×12 aks, 12 kat); genel model motorunun aks sınırı yok, yalnız SD sınırı (aşağıda, 2000)
    if (!s3Var()) {
      if (B.akslar.x.length > 12 || B.akslar.y.length > 12) hata.push("En çok 12×12 aks desteklenir; modeli küçültün.");
      if (B.katlar.length > 13) hata.push("En çok 12 kat desteklenir.");
    }
    if (!B.kolonlar.length && !(B.cubuklar || []).length) hata.push("Hiç kolon yok: Kolon aracıyla etkin katın aks kesişimlerine dokunun.");
    if (s3Var()) s3Dogrula(hata, uyari);
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
    const sd = sdTahmini(), sdSinir = s3Var() ? 2000 : 1500;      // genel model motoru 2000 SD'ye izin verir
    if (sd > sdSinir) hata.push("Serbestlik derecesi " + sd + " > " + sdSinir + ": modeli küçültün (" + (s3Var() ? "daha seyrek aşık / bölme, daha az çerçeve" : "daha az kat ya da aks") + ").");
    return { uyari: uyari, hata: hata };
  }

  // genel model denetimi: kesit, çözülemeyen düğüm başvurusu (hata); ModelOps.denetle bulguları (uyarı). Anlık görüntü başına önbellek.
  const s3DenetimOnbellek = { anahtar: null, hata: [], uyari: [] };
  function s3Dogrula(hata, uyari) {
    const a = sonAnlik || anlikGoruntu();
    if (s3DenetimOnbellek.anahtar !== a) {
      const h = [], u = [];
      (B.cubuklar || []).forEach(function (c) {
        if (!c) return;
        if (!c.kesit) h.push("Çubuk " + c.no + ": kesit atanmamış (Seç → Özellikler ya da Değiştirme → Kesit değiştir).");
        else if (!B.kesitler[c.kesit]) h.push("Çubuk " + c.no + ": kesit “" + c.kesit + "” tanımsız.");
        if (!refP(c.i) || !refP(c.j)) h.push("Çubuk " + c.no + ": ucu tanımsız bir aksa ya da düğüme bağlı.");
      });
      (B.paneller || []).forEach(function (p) { if (p && Array.isArray(p.kose) && p.kose.some(function (r) { return !refP(r); })) h.push("Panel " + p.no + ": köşesi tanımsız bir aksa ya da düğüme bağlı."); });
      const MO = window.ModelOps;
      if (MO && MO.denetle && !h.length) {
        try {
          const TASIYAN = { iki: null, "tek-13": [1, 3], "tek-24": [2, 4], yok: [] };
          (MO.denetle(B).uyarilar || []).forEach(function (x) {
            if (x.kod === "sifir-boy" || x.kod === "panel-geometri") { h.push(x.mesaj + " Motor bu modeli çözmez; elemanı silin ya da uçlarını düzeltin."); return; }
            if (x.kod === "panel-kenari") {      // motor yalnız taşıyan kenarlarda çubuk zinciri ister (dağıtım türüne göre)
              const pn = (B.paneller || []).filter(function (q) { return +q.no === +x.panel; })[0], t = TASIYAN[(pn && pn.dagitim) || "iki"];
              if (t && t.indexOf(+x.kenar) < 0) return;
              if (t !== undefined) { h.push(x.mesaj + " (taşıyan kenar; dağıtımı değiştirin ya da kenar çubuğunu çizin)"); return; }
            }
            const tur = x.cubuk != null ? "cubuk" : x.panel != null ? "panel" : x.dugum != null ? "dugum" : x.cubuklar ? "cubuk" : null;
            const no = x.cubuk != null ? x.cubuk : x.panel != null ? x.panel : x.dugum != null ? x.dugum : x.cubuklar ? x.cubuklar[0] : null;
            u.push({ tur: tur, no: no, kat: null, metin: x.mesaj });
          });
        } catch (e) { u.push({ tur: null, no: null, kat: null, metin: "Genel model denetlenemedi: " + e.message }); }
      }
      s3DenetimOnbellek.anahtar = a; s3DenetimOnbellek.hata = h; s3DenetimOnbellek.uyari = u;
    }
    s3DenetimOnbellek.hata.forEach(function (m) { hata.push(m); });
    s3DenetimOnbellek.uyari.forEach(function (m) { uyari.push(m); });
  }

  // ---------- Geri/ileri ve taslak ----------
  function anlikGoruntu() { return JSON.stringify(B); }
  let sonAnlik = "";
  function degisti(etiket) {
    // her düzenleme: geçmişe yaz, taslağı kaydet, sahneyi/panelleri yenile
    zKatSenkron(B);
    const simdi = anlikGoruntu();
    if (simdi !== sonAnlik) {
      gecmis.geri.push(sonAnlik || simdi);
      if (gecmis.geri.length > GECMIS_EN_FAZLA) gecmis.geri.shift();
      gecmis.ileri = [];
      sonAnlik = simdi;
    }
    if (SON) sonEski = true;
    taslakKaydet();
    modelDegisti(etiket || "");
    yenile();
  }
  function geriAl() {
    if (!gecmis.geri.length) return;
    gecmis.ileri.push(anlikGoruntu());
    B = JSON.parse(gecmis.geri.pop());
    sonAnlik = anlikGoruntu();
    D.secim = []; D.kirisBas = null;
    D.kat = Math.min(Math.max(0, D.kat), ustKat());
    if (SON) sonEski = true;
    taslakKaydet(); modelDegisti("geri-al"); yenile();
  }
  function ileriAl() {
    if (!gecmis.ileri.length) return;
    gecmis.geri.push(anlikGoruntu());
    B = JSON.parse(gecmis.ileri.pop());
    sonAnlik = anlikGoruntu();
    D.secim = []; D.kirisBas = null;
    D.kat = Math.min(Math.max(0, D.kat), ustKat());
    if (SON) sonEski = true;
    taslakKaydet(); modelDegisti("yinele"); yenile();
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
    // surum 3 listeleri (çubuk/panel/aks sistemi) korunur (K2: tam kısım, 2.9 → 2). Çok uzun rakam dizisi sonsuz verir (≥ 3: genel):
    // JSON'a null yazılıp aks–kat'a dönmesin diye 3
    const sv = surumSayi(m.surum);
    b.tur = "bina"; b.surum = isFinite(sv) ? Math.max(1, sv) : sv > 0 ? 3 : 1;
    b.akslar = b.akslar || { x: [], y: [] };
    ["x", "y"].forEach(function (e) {
      // §19.1 ek alanları (tur, gorunur, balon) korunur
      b.akslar[e] = (b.akslar[e] || []).map(function (a, i) { return Object.assign({}, a, { ad: String(a.ad != null ? a.ad : (e === "x" ? harf(i) : i + 1)), konum: +a.konum || 0 }); }).sort(function (p, q) { return p.konum - q.konum; });
    });
    b.katlar = (b.katlar || []).map(function (k, i) { return { no: k.no != null ? +k.no : i, ad: String(k.ad || (i ? i + ". kat" : "Temel")), kot: +k.kot || 0 }; }).sort(function (p, q) { return p.no - q.no; });
    if (!b.katlar.length) b.katlar = [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3 }];
    b.malzemeler = b.malzemeler || {}; b.kesitler = b.kesitler || {}; b.duvarlar = b.duvarlar || {};
    // aks–kat elemanlarının ek alanları (kiriş duvar_h parapeti, grup, …) korunur; tanınan alanlar normalleştirilir
    b.kolonlar = (b.kolonlar || []).map(function (c, i) { return Object.assign({}, c, { no: c.no != null ? +c.no : i + 1, aks: [String(c.aks[0]), String(c.aks[1])], kat: +c.kat || 1, kesit: String(c.kesit || ""), yon: c.yon === "y" ? "y" : "x" }); });
    b.kirisler = (b.kirisler || []).map(function (k, i) { return Object.assign({}, k, { no: k.no != null ? +k.no : i + 1, kat: +k.kat || 1, bas: [String(k.bas[0]), String(k.bas[1])], son: [String(k.son[0]), String(k.son[1])], kesit: String(k.kesit || ""), duvar: k.duvar || null }); });
    b.dosemeler = (b.dosemeler || []).map(function (d, i) {
      return Object.assign({}, d, { no: d.no != null ? +d.no : i + 1, kat: +d.kat || 1, kose: [[String(d.kose[0][0]), String(d.kose[0][1])], [String(d.kose[1][0]), String(d.kose[1][1])]], h: +d.h || 0.14,
        kullanim: String(d.kullanim || "konut"), g_ek: d.g_ek != null ? +d.g_ek : 1.5, q: d.q == null ? null : +d.q, dagitim: d.dagitim || "otomatik", kaplama: d.kaplama || null });
    });
    b.ek_yukler = Array.isArray(b.ek_yukler) ? b.ek_yukler : [];
    b.temeller = temelNormalize(b.temeller);
    b.sistem = b.sistem === "celik" ? "celik" : "betonarme";
    // Dilim 2 girdileri: yük durumları (S: bölge/rakım/μ, W: C), deprem (TBDY 2018), analiz
    const yd = b.yuk_durumlari || {};
    const acikMi = function (k, v) { return !!(yd[k] && yd[k].acik !== undefined ? yd[k].acik : v); };
    b.yuk_durumlari = {
      G: { acik: true }, Q: { acik: acikMi("Q", true) },
      S: { acik: acikMi("S", false), bolge: Math.min(9, Math.max(1, parseInt((yd.S || {}).bolge, 10) || 1)), rakim: +((yd.S || {}).rakim) || 100, mu: (yd.S || {}).mu != null ? +(yd.S || {}).mu : 0.8 },
      W: { acik: acikMi("W", false), C: (yd.W || {}).C != null ? +(yd.W || {}).C : 1.2 },
      E: { acik: acikMi("E", false) },
    };
    const dp = b.deprem || {}, celik = b.sistem === "celik";
    const varsTasiyici = tasiyiciBul(dp.tasiyici) ? dp.tasiyici : (celik ? "celik-cerceve-yuksek" : "betonarme-cerceve-yuksek");
    const ts = tasiyiciBul(varsTasiyici);
    b.deprem = {
      SS: dp.SS != null ? +dp.SS : 1.0, S1: dp.S1 != null ? +dp.S1 : 0.3, SS_DD3: dp.SS_DD3 != null ? +dp.SS_DD3 : 0.4, S1_DD3: dp.S1_DD3 != null ? +dp.S1_DD3 : 0.12,
      zemin_sinifi: TBDY.FS[dp.zemin_sinifi] ? dp.zemin_sinifi : "ZC", DD: dp.DD || "DD-2", BKS: TBDY.I[+dp.BKS] ? +dp.BKS : 3, I: 1.0,
      tasiyici: varsTasiyici, R: dp.R != null ? +dp.R : (ts ? ts.R : 8), D: dp.D != null ? +dp.D : (ts ? ts.D : 3), n: dp.n != null ? +dp.n : 0.3, Ct: dp.Ct != null ? +dp.Ct : (celik ? 0.08 : 0.1),
      periyot: dp.periyot === "rayleigh" ? "rayleigh" : "ampirik", diyafram: dp.diyafram === "esnek" ? "esnek" : "rijit", dismerkezlik: dp.dismerkezlik != null ? +dp.dismerkezlik : 0.05, dolgu: dp.dolgu === "esnek" ? "esnek" : "bitisik",
    };
    b.deprem.I = TBDY.I[b.deprem.BKS];
    b.birim = b.birim || { kuvvet: "kN", uzunluk: "m" };
    b.kombinasyon_kumesi = b.kombinasyon_kumesi || (b.sistem === "celik" ? "cythye_ydkt" : "ts500");
    b.analiz = Object.assign({ catlamis_rijitlik: b.sistem !== "celik", diyagram_nokta: 11 }, b.analiz || {});   // TBDY 4.5.8.1: betonarmede varsayılan çatlamış
    b.analiz.catlamis_rijitlik = b.analiz.catlamis_rijitlik == null ? b.sistem !== "celik" : !!b.analiz.catlamis_rijitlik;
    if (b.analiz.celik_Lb != null && b.analiz.celik_Lb !== "boy") b.analiz.celik_Lb = "otomatik";
    zKatSenkron(b);
    return b;
  }
  // §19.1 tek kaynak akslar.z: eski modellerde (surum 1/2) Z aksları katlardan türetilir (MatrisAks.yukselt / katlariSenkronla);
  // kata bağlı Z aksının konumu kat kotudur. surum alanına dokunulmaz (aks–kat modeli aks–kat motorunda çözülmeye devam eder).
  function zKatSenkron(b) {
    const M = window.MatrisAks;
    if (!M || !M.katlariSenkronla || !b || !b.akslar) return b;
    try {
      const r = M.katlariSenkronla(b);
      b.akslar.z = r.model.akslar.z;
      b.katlar = r.model.katlar.map(function (k, i) { return { no: k.no != null ? +k.no : i, ad: String(k.ad || (i ? i + ". kat" : "Temel")), kot: +k.kot || 0 }; });
    } catch (e) { /* bozuk aks verisi: olduğu gibi */ }
    return b;
  }
  // Sözleşme K2 — surum alanının sayısı (motor yapi._surum_sayi ve bina_cizim.js surumSayi ile aynı): bool → 1; sonlu sayı → tam kısmı
  // (2.9 → 2); /^\s*[+-]?\d+(\.\d+)?\s*$/ dizesi → tam kısmı ("3.0" → 3, " 3.5 " → 3); öteki her şey → 1 ("3a", "0x3", "1e1", null).
  function surumSayi(s) {
    if (typeof s === "boolean") return 1;
    if (typeof s === "number") return isFinite(s) ? Math.trunc(s) : 1;
    if (typeof s === "string" && /^\s*[+-]?\d+(\.\d+)?\s*$/.test(s)) return Math.trunc(parseFloat(s));
    return 1;
  }
  // Genel model (surum 3) mı — motorun yönlendirme kuralıyla birebir (sözleşme C1 / K2; yapi._serbest_mi):
  // surumSayi(surum) ≥ 3, ya da boş olmayan cubuklar / paneller / dugumler / mesnetler / uretecler listesi, ya da "dugum" alanı nesne
  // (REF) olan ya da türü (kırpılmış, küçük harfe çevrilmiş) cubuk / panel olan bir ek yük. Aks–kat düğüm yükü {tur: "dugum", aks: [x, y],
  // kat} genel model saymaz.
  const S3_LISTELER = ["cubuklar", "paneller", "dugumler", "mesnetler", "uretecler"];
  function s3Var(b) {
    b = b || B;
    if (!b || typeof b !== "object" || Array.isArray(b)) return false;
    if (surumSayi(b.surum) >= 3) return true;
    if (S3_LISTELER.some(function (k) { return Array.isArray(b[k]) && b[k].length > 0; })) return true;
    return (Array.isArray(b.ek_yukler) ? b.ek_yukler : []).some(function (y) {
      if (!y || typeof y !== "object" || Array.isArray(y)) return false;
      const t = String(y.tur == null ? "" : y.tur).trim().toLowerCase();
      return (!!y.dugum && typeof y.dugum === "object" && !Array.isArray(y.dugum)) || t === "cubuk" || t === "panel";
    });
  }
  // Z aksları (konum sıralı; MatrisAks yoksa katlardan)
  function zAkslari() {
    if (B && B.akslar && Array.isArray(B.akslar.z) && B.akslar.z.length) return B.akslar.z.slice().sort(function (a, b) { return +a.konum - +b.konum; });
    return (B ? B.katlar : []).map(function (k) { return { ad: k.ad, konum: +k.kot, kat: k.no }; });
  }
  function zAksBul(ad) { return zAkslari().filter(function (a) { return String(a.ad) === String(ad); })[0] || null; }
  // kat düzenlemelerinde (kat ekle / sil / kot) akslar.z de güncellenir
  function zKatEkle(no, kot) {
    if (!B.akslar || !Array.isArray(B.akslar.z)) return;
    const var_ = B.akslar.z.filter(function (a) { return a.kat == null && Math.abs(+a.konum - kot) < 0.001; })[0];
    if (var_) { var_.kat = no; return; }
    const M = window.MatrisAks, adlar = B.akslar.z.map(function (a) { return String(a.ad); });
    const ad = M ? M.benzersizAd(M.kotAdi(kot), adlar) : "Z" + no;
    B.akslar.z.push({ ad: ad, konum: +(+kot).toFixed(6), kat: no });
    B.akslar.z.sort(function (a, b) { return +a.konum - +b.konum; });
  }
  function zKatSil(no, h) {
    if (!B.akslar || !Array.isArray(B.akslar.z)) return;
    const z = B.akslar.z.filter(function (a) { return +a.kat === no; })[0];
    const kot = z ? +z.konum : null;
    const M = window.MatrisAks;
    let kullaniliyor = false;
    if (z && M && s3Var()) {
      try { const r = M.bagliElemanlar(B, { yon: "z", ad: z.ad }); kullaniliyor = r.cubuklar.length + r.paneller.length + r.mesnetler.length + r.dugumler.length > 0; }
      catch (e) { kullaniliyor = true; }
    }
    if (z) { if (kullaniliyor) delete z.kat; else B.akslar.z.splice(B.akslar.z.indexOf(z), 1); }
    B.akslar.z.forEach(function (a) {
      if (a.kat != null && +a.kat > no) { a.kat = +a.kat - 1; a.konum = +(+a.konum - h).toFixed(6); }
      else if (a.kat == null && kot != null && +a.konum > kot + 1e-6 && !kullaniliyor) a.konum = +(+a.konum - h).toFixed(6);
    });
  }
  function zKatKot(no, kot) {
    if (!B.akslar || !Array.isArray(B.akslar.z)) return;
    B.akslar.z.forEach(function (a) { if (+a.kat === no) a.konum = +(+kot).toFixed(6); });
    B.akslar.z.sort(function (a, b) { return +a.konum - +b.konum; });
  }
  // temeller: tip tekil | surekli | radye; yalnız seçili tipin (ve önceden girilmiş olanların) alt nesnesi tutulur
  function temelNormalize(t0) {
    const t = Object.assign({ tip: "tekil", varsayilan: { B: 1.6, L: 1.6, h: 0.6 }, mesnet: "ankastre", ozel: [] }, t0 || {});
    t.tip = TEMEL_TIP_AD[t.tip] ? t.tip : "tekil";
    t.varsayilan = Object.assign({ B: 1.6, L: 1.6, h: 0.6 }, t.varsayilan || {});
    t.zemin = Object.assign({}, TEMEL_VARS.zemin, t.zemin || {});
    if (t.tip === "surekli" || t.surekli) {
      const s = Object.assign({}, TEMEL_VARS.surekli, t.surekli || {});
      s.yon = s.yon === "x" || s.yon === "y" ? s.yon : "xy";
      s.akslar = Array.isArray(s.akslar) ? s.akslar.map(String) : "tum";
      ["B", "h_tabla", "b_govde", "h_govde", "tasma", "ag"].forEach(function (k) { const n = +s[k]; s[k] = isFinite(n) && n >= 0 ? n : TEMEL_VARS.surekli[k]; });
      t.surekli = s;
    }
    if (t.tip === "radye" || t.radye) {
      const r = Object.assign({}, TEMEL_VARS.radye, t.radye || {});
      ["h", "tasma", "ag"].forEach(function (k) { const n = +r[k]; r[k] = isFinite(n) && n >= 0 ? n : TEMEL_VARS.radye[k]; });
      r.kiris = r.kiris && typeof r.kiris === "object" ? Object.assign({}, TEMEL_VARS.kiris, r.kiris) : null;
      t.radye = r;
    }
    return t;
  }
  function binayiAyarla(m, kaynak) {
    B = binaYukle(m);
    // şablon / proje / yeni model: önceki modelin eleman pencereleri anlamını yitirir (iğnelenenler kalır, "cozum" olayıyla tazelenir)
    const MB = modul("MatrisBilgi");
    if (MB && MB.hepsiniKapat) { try { MB.hepsiniKapat(); } catch (e) { /* yoksay */ } }
    if (sonAnlik) gecmis.geri.push(sonAnlik);
    gecmis.ileri = [];
    sonAnlik = anlikGoruntu();
    D.secim = []; D.kirisBas = null; D.akisHedef = null; D.firca = null;
    D.kat = Math.min(Math.max(1, D.kat), ustKat());
    SON = null; sonEski = false; RAPOR = null;
    D.gizli = {}; D.yalit = null; D.katSuzgec = null;
    if (kamera) kamera.sifirla();
    if (ref.sonuc) sonucuTemizle();
    taslakKaydet();
    modelDegisti(kaynak || "");
    yenile();
    olayYay("cozum", null);
    if (kaynak) A.toast(kaynak);
  }

  // ---------- 3B sahne ----------
  // Sahne boyu. Normal kip: genişlik kutudan, yükseklik pencerenin kalanı (100dvh − üst çubuk − alt gezinti − Bina üst şeridi − sahne altı);
  // tam ekran: SVG kutusunun tamamı (çekmece ve şerit dışında kalan alan). Değişti mi döndürür.
  function sahneBoyutla() {
    let w, h;
    if (D.tamEkran) {
      w = Math.max(200, Math.floor(ref.svgKutu.clientWidth) || window.innerWidth);
      h = Math.max(150, Math.floor(ref.svgKutu.clientHeight) || window.innerHeight);
    } else {
      w = Math.max(260, Math.floor(ref.svgKutu.clientWidth || ref.sahneKutu.clientWidth) || 600);
      h = normalYukseklik(w);
    }
    const degisti = w !== cizimW || h !== cizimH;
    cizimW = w; cizimH = h;
    // kullanıcı yakınlaştırıp kaydırmadıysa (kamera yalın) bina yeni boyuta yeniden sığar; yoksa görünüm merkezi korunur
    const yalin = kamera && kamera.z === 1 && kamera.px === 0 && kamera.py === 0;
    if (!kamera) kamera = new C.Kamera(w, h); else { kamera.boyut(w, h); if (yalin) kamera.sifirla(); }
    ref.svg.setAttribute("width", w); ref.svg.setAttribute("height", h);
    kok.style.setProperty("--bn-sahne-h", h + "px");
    return degisti;
  }
  function gorunurYukseklik(sec, sabitMi) {
    const el = document.querySelector(sec);
    if (!el) return 0;
    const cs = getComputedStyle(el);
    if (cs.display === "none" || (sabitMi && cs.position !== "sticky" && cs.position !== "fixed")) return 0;
    return el.getBoundingClientRect().height;
  }
  function normalYukseklik(w) {
    const vh = window.innerHeight || document.documentElement.clientHeight || 800, dar = window.innerWidth < 700;
    const ust = gorunurYukseklik("header.ust", true), nav = gorunurYukseklik(".alt-nav", true);
    const serit = (kok.querySelector(".bn-ust") || { offsetHeight: 0 }).offsetHeight + 10;
    const alt = ref.sahneAlt ? ref.sahneAlt.offsetHeight : 44;
    const arac = dar && !aracYon ? (ref.arac.offsetHeight || 48) + 10 : 0;     // araç kutuları etkinse eski çubuk gizli
    // sayfa başından sahneye kadar olan pay (başlık satırı dahil): açılışta bütün düzenleyici kaydırmadan görünsün
    const ustPay = Math.max(ust + serit, ref.svgKutu.getBoundingClientRect().top + (window.scrollY || 0));
    const kalan = Math.floor(vh - nav - ustPay - alt - arac - 14);
    if (vh < 520) return Math.max(220, Math.floor(vh - nav - alt - 16));          // yatay telefon: sahne görünüme sığsın (üst çubuk kayar)
    if (dar) return Math.round(Math.max(280, Math.min(kalan, w * 1.35)));
    return Math.max(380, kalan);
  }
  // ---------- Yerleşim: daraltılabilir araç çubuğu / özellik paneli, panel genişliği, sonuç yeri (alt / sağ), tam ekran, yüzen paneller ----------
  // Panel ve sonuç sütunu genişliği sürüklenerek (ayırıcı; klavyede ok tuşları) ayarlanır; değerler görüntüleyene özel (localStorage).
  const PANEL_W = { min: 240, max: 640, adim: 24 }, SONUC_W = { min: 300, max: 960, adim: 32 };
  function genisMi() { return window.innerWidth >= 900; }
  function sonucSagMi() { return D.sonucYer === "sag" && genisMi(); }
  function yerlesimKaydet() {
    try {
      localStorage.setItem(YERLESIM_ANAHTAR, JSON.stringify({ arac: D.aracKapali, panel: D.panelKapali, cekmece: D.cekmeceH, panelW: D.panelW, sonucYer: D.sonucYer, sonucW: D.sonucW, yuzen: D.yuzen }));
    } catch (e) { /* depolama yok */ }
  }
  // aç/kapa düğmesi: erişilebilir ad sabit, durum aria-pressed'de; ipucu (title) yapılacak işi söyler
  function dugmeDurum(el, basili, ad, baslik) { if (!el) return; el.setAttribute("aria-pressed", String(basili)); el.setAttribute("aria-label", ad); el.title = baslik; }
  function yerlesimUygula() {
    kok.classList.toggle("bn-arac-kapali", D.aracKapali);
    kok.classList.toggle("bn-panel-kapali", D.panelKapali);
    kok.classList.toggle("bn-sonuc-sag", D.sonucYer === "sag");
    if (D.panelW) kok.style.setProperty("--bn-panel-w", D.panelW + "px"); else kok.style.removeProperty("--bn-panel-w");
    if (D.sonucW) kok.style.setProperty("--bn-sonuc-w", D.sonucW + "px"); else kok.style.removeProperty("--bn-sonuc-w");
    // araç kutuları etkinken (eski araç çubuğu gizli) ☰ yüzen araç kutularını gösterir / gizler
    if (aracYon) { const g = !(ref.aracKatman && ref.aracKatman.hidden); dugmeDurum(ref.aracAc, g, "Araç kutuları", g ? "Araç kutularını gizle" : "Araç kutularını göster"); }
    else dugmeDurum(ref.aracAc, !D.aracKapali, "Araç çubuğu", D.aracKapali ? "Araç çubuğunu aç" : "Araç çubuğunu daralt");
    // telefonda tam ekran: araç şeridi özellik çekmecesinin başlığının üstünde kalsın (etiketler kırpılmasın)
    const oz = ref.panel && ref.panel.querySelector("summary");
    if (oz) kok.style.setProperty("--bn-panel-ozet-h", Math.ceil(oz.getBoundingClientRect().height || 44) + "px");
    dugmeDurum(ref.panelAc, !D.panelKapali, "Özellik paneli", D.panelKapali ? "Özellik panelini aç" : "Özellik panelini daralt");
    dugmeDurum(ref.sonucYer, D.sonucYer === "sag", "Sonuçlar sağ panelde", D.sonucYer === "sag" ? "Sonuçları alt çekmeceye al" : "Sonuçları sağ panele al");
    dugmeDurum(ref.tam, D.tamEkran, "Tam ekran", D.tamEkran ? "Tam ekrandan çık (Esc, F)" : "Tam ekran (F)");
    if (ref.tam) ref.tam.textContent = D.tamEkran ? "✕" : "⛶";
    if (ref.cekmece) { ref.cekmece.setAttribute("role", sonucSagMi() ? "complementary" : "region"); ref.cekmece.setAttribute("aria-label", "Hesap ve sonuçlar"); }
    yerlesimKaydet();
    if (D.tamEkran) { cekmeceUygula(); yuzenUygula(); }
    boyutDegisti(false);
    ayiracGuncelle();
  }
  // Boyut değişince sahneyi yeniden ölç ve çiz; sigdir: kamerayı sıfırla (bina yeniden sığdırılır; yön değişimi, tam ekrana giriş/çıkış)
  function boyutDegisti(sigdir) {
    if (!B || !kamera) return;
    const d = sahneBoyutla();
    if (sigdir) kamera.sifirla();
    if (d || sigdir) sahneYenile();
  }
  function sonucYerDegistir() {
    D.sonucYer = D.sonucYer === "sag" ? "alt" : "sag";
    if (D.tamEkran && D.sonucYer === "sag") D.cekmeceKapali = false;
    yerlesimUygula();
    requestAnimationFrame(function () { boyutDegisti(false); sonucBoyutlari(); });
  }
  // ---------- Ayırıcılar (panel genişliği, sağ sonuç sütunu genişliği) ----------
  function panelGenislik() { return Math.round(ref.panel.getBoundingClientRect().width) || 320; }
  function sonucGenislik() { return Math.round(ref.cekmece.getBoundingClientRect().width) || 420; }
  function sinirla(x, s, ust) { return Math.max(s.min, Math.min(Math.min(s.max, ust || s.max), Math.round(x))); }
  function ayiracGuncelle() {
    const p = ref.panelAyirac, s = ref.sonucAyirac;
    if (p) {
      p.setAttribute("aria-valuemin", PANEL_W.min); p.setAttribute("aria-valuemax", PANEL_W.max); p.setAttribute("aria-valuenow", D.panelW || panelGenislik());
      // tam ekranda yüzen panelin sol kenarına yapışır (panel taşınabilir); normal kipte CSS konumlar
      const goster = D.tamEkran && !D.panelKapali && ref.panel.open && window.innerWidth >= 700;
      p.classList.toggle("bn-ayirac-yuzen", goster);
      if (goster) {
        p.style.left = Math.round(ref.panel.offsetLeft - 5) + "px"; p.style.top = Math.round(ref.panel.offsetTop + 10) + "px"; p.style.height = Math.max(24, ref.panel.offsetHeight - 20) + "px";
      } else { p.style.left = ""; p.style.top = ""; p.style.height = ""; }
    }
    if (s) { s.setAttribute("aria-valuemin", SONUC_W.min); s.setAttribute("aria-valuemax", SONUC_W.max); s.setAttribute("aria-valuenow", D.sonucW || sonucGenislik()); }
  }
  // Bir ayırıcıyı sürükle/klavye ile işlet: oku() başlangıç genişliği, yaz(w) uygular; yön −1: tutamak sağdaki panelin sol kenarında
  function ayiracKur(el, s, oku, yaz, bitti) {
    let bas = null;
    el.addEventListener("pointerdown", function (e) {
      if (e.button != null && e.button !== 0) return;
      bas = { x: e.clientX, w: oku(), id: e.pointerId };
      try { el.setPointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
      el.classList.add("suruklen");
      e.preventDefault();
    });
    el.addEventListener("pointermove", function (e) {
      if (!bas || e.pointerId !== bas.id) return;
      yaz(sinirla(bas.w - (e.clientX - bas.x), s, Math.round(window.innerWidth * 0.6)));
    });
    const son = function (e) { if (!bas || e.pointerId !== bas.id) return; bas = null; el.classList.remove("suruklen"); bitti(); };
    el.addEventListener("pointerup", son);
    el.addEventListener("pointercancel", son);
    el.addEventListener("dblclick", function () { yaz(0); bitti(); });
    el.addEventListener("keydown", function (e) {
      const k = e.key;
      if (k !== "ArrowLeft" && k !== "ArrowRight" && k !== "Home" && k !== "End") return;
      e.preventDefault();
      const w = oku(), ust = Math.round(window.innerWidth * 0.6);
      yaz(k === "Home" ? s.min : k === "End" ? sinirla(s.max, s, ust) : sinirla(w + (k === "ArrowLeft" ? s.adim : -s.adim), s, ust));
      bitti();
    });
  }
  function ayiraclariKur() {
    ayiracKur(ref.panelAyirac, PANEL_W, function () { return D.panelW || panelGenislik(); }, function (w) {
      const eski = D.tamEkran && D.yuzen.panel ? panelGenislik() : 0;
      D.panelW = w;
      if (w) kok.style.setProperty("--bn-panel-w", w + "px"); else kok.style.removeProperty("--bn-panel-w");
      // taşınmış yüzen panelde sağ kenar yerinde kalsın
      if (eski && D.yuzen.panel) { D.yuzen.panel.x += eski - panelGenislik(); yuzenUygula(); }
      ayiracGuncelle();
    }, function () { yerlesimKaydet(); boyutDegisti(false); });
    ayiracKur(ref.sonucAyirac, SONUC_W, function () { return D.sonucW || sonucGenislik(); }, function (w) {
      D.sonucW = w;
      if (w) kok.style.setProperty("--bn-sonuc-w", w + "px"); else kok.style.removeProperty("--bn-sonuc-w");
      ayiracGuncelle();
    }, function () { yerlesimKaydet(); boyutDegisti(false); sonucBoyutlari(); });
  }
  // ---------- Yüzen paneller (tam ekran): araç kutusu ve özellik paneli tutamağından sürüklenir; konum sahne kutusuna göre ----------
  function yuzenOge(ad) { return ad === "arac" ? ref.arac : ref.panel; }
  function yuzenUygula() {
    ["arac", "panel"].forEach(function (ad) {
      const el = yuzenOge(ad), k = D.tamEkran && window.innerWidth >= 700 ? D.yuzen[ad] : null;
      if (!el) return;
      if (!k) { el.style.left = ""; el.style.top = ""; el.style.right = ""; el.classList.remove("bn-tasindi"); return; }
      const kap = ref.govde, W = kap.clientWidth, H = kap.clientHeight, w = el.offsetWidth || 60, h = Math.min(el.offsetHeight || 40, H);
      const x = Math.max(0, Math.min(W - Math.min(w, W), k.x)), y = Math.max(0, Math.min(H - Math.min(h, 48), k.y));
      el.style.left = Math.round(x) + "px"; el.style.top = Math.round(y) + "px"; el.style.right = "auto";
      el.classList.add("bn-tasindi");
    });
  }
  function yuzenJesti() {
    let bas = null;
    kok.addEventListener("pointerdown", function (e) {
      if (!D.tamEkran || window.innerWidth < 700 || (e.button != null && e.button !== 0)) return;
      const t = e.target.closest ? e.target.closest("[data-yuzen-tasi], .bn-panel > summary") : null;
      if (!t || !kok.contains(t)) return;
      const ad = t.dataset.yuzenTasi || "panel", el = yuzenOge(ad), r = el.getBoundingClientRect(), g = ref.govde.getBoundingClientRect();
      bas = { ad: ad, el: el, x: e.clientX, y: e.clientY, x0: r.left - g.left, y0: r.top - g.top, oynadi: false, id: e.pointerId, t: t };
    });
    kok.addEventListener("pointermove", function (e) {
      if (!bas || e.pointerId !== bas.id) return;
      const dx = e.clientX - bas.x, dy = e.clientY - bas.y;
      if (!bas.oynadi) {
        if (Math.abs(dx) + Math.abs(dy) < 6) return;
        bas.oynadi = true;
        try { bas.t.setPointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
        bas.el.classList.add("suruklen");
      }
      D.yuzen[bas.ad] = { x: bas.x0 + dx, y: bas.y0 + dy };
      yuzenUygula();
      if (bas.ad === "panel") ayiracGuncelle();
    });
    const son = function (e) {
      if (!bas || e.pointerId !== bas.id) return;
      const b = bas; bas = null;
      b.el.classList.remove("suruklen");
      if (b.oynadi) {
        yerlesimKaydet();
        // sürükleme sonrası summary'nin tık olayı paneli aç/kapamasın
        if (b.t.tagName === "SUMMARY") { const yut = function (ev) { ev.preventDefault(); ev.stopPropagation(); }; b.t.addEventListener("click", yut, { capture: true, once: true }); setTimeout(function () { b.t.removeEventListener("click", yut, { capture: true }); }, 0); }
      }
    };
    kok.addEventListener("pointerup", son);
    kok.addEventListener("pointercancel", son);
    ref.panel.addEventListener("toggle", function () { if (D.tamEkran) { yuzenUygula(); ayiracGuncelle(); } });
  }
  // ---------- Tam ekran ----------
  function tamEkranOgesi() { return document.fullscreenElement || document.webkitFullscreenElement || null; }
  function tamEkranDegistir() { if (D.tamEkran) tamEkranKapat(); else tamEkranAc(); }
  // Bildirim (toast) sayfa gövdesinde: öğe tam ekranında görünmez; tam ekranda düzenleyicinin içine taşınır, çıkışta yerine döner
  let toastYeri = null;
  function toastTasi(ice) {
    const t = document.getElementById("toast");
    if (!t) return;
    if (ice && t.parentNode !== kok) { toastYeri = { ana: t.parentNode, sonraki: t.nextSibling }; kok.appendChild(t); }
    else if (!ice && toastYeri && t.parentNode === kok) { toastYeri.ana.insertBefore(t, toastYeri.sonraki && toastYeri.sonraki.parentNode === toastYeri.ana ? toastYeri.sonraki : null); toastYeri = null; }
  }
  // Tam ekran: Fullscreen API ile düzenleyici kapsayıcısı (sahne + araçlar + paneller + çekmece) tam ekran olur; her durumda
  // "sözde tam ekran" düzeni de uygulanır (sabit konumlu, görünümü kaplayan kip; üst başlık ve alt gezinti gizli).
  // API yoksa (iPhone Safari) ya da reddedilirse yalnız sözde kip kalır (data-tam-kip="sahte").
  function tamEkranAc() {
    if (D.tamEkran) return;
    D.tamEkran = true; D.gercekTam = false;
    kok.classList.add("bn-tam"); document.body.classList.add("bn-tam-ekran");
    // dar ya da alçak ekranda yüzen özellik paneli kapalı başlar (sahne görünsün)
    ref.panel.open = !(window.innerWidth < 700 || window.innerHeight < 520);
    toastTasi(true);
    const f = kok.requestFullscreen || kok.webkitRequestFullscreen;
    kok.dataset.tamKip = f ? "api" : "sahte";
    if (f) {
      try {
        const p = f.call(kok, { navigationUI: "hide" });
        if (p && typeof p.then === "function") p.then(function () { D.gercekTam = !!tamEkranOgesi(); }, function () { D.gercekTam = false; kok.dataset.tamKip = "sahte"; });
        else D.gercekTam = !!tamEkranOgesi();
      } catch (e) { D.gercekTam = false; kok.dataset.tamKip = "sahte"; }
    }
    yerlesimUygula();
    requestAnimationFrame(function () { boyutDegisti(true); cekmeceUygula(); yuzenUygula(); ayiracGuncelle(); sonucBoyutlari(); });
  }
  function tamEkranKapat() {
    if (!D.tamEkran) return;
    D.tamEkran = false;
    const gercek = tamEkranOgesi();
    D.gercekTam = false;
    if (gercek) { const f = document.exitFullscreen || document.webkitExitFullscreen; try { const p = f && f.call(document); if (p && p.catch) p.catch(function () {}); } catch (e) { /* yoksay */ } }
    kok.classList.remove("bn-tam"); document.body.classList.remove("bn-tam-ekran");
    delete kok.dataset.tamKip;
    toastTasi(false);
    ref.cekmece.style.height = "";
    ref.cekmece.classList.remove("kapali");
    if (window.innerWidth >= 900) ref.panel.open = true;
    yuzenUygula();
    yerlesimUygula();
    boyutDegisti(true);
    sonucBoyutlari();
    if (ref.tam) ref.tam.focus({ preventScroll: true });
  }
  function tamEkranOlayi() {
    if (tamEkranOgesi()) { D.gercekTam = true; return; }
    if (D.gercekTam) { D.gercekTam = false; tamEkranKapat(); }   // tarayıcının kendi Esc'i ya da sistem hareketiyle çıkış
  }
  // Çekmece (tam ekran): hesap hattı + sonuç sekmeleri; tutamak sürüklenerek yükseklik, dokunarak aç/kapat
  function cekmeceMin() { return Math.round((ref.cekmeceTutamak.offsetHeight || 22) + (kok.querySelector(".bn-hat-kutu").offsetHeight || 48) + 12); }
  function cekmeceUygula() {
    if (!D.tamEkran) return;
    if (sonucSagMi()) { ref.cekmece.style.height = ""; ref.cekmece.classList.remove("kapali"); ref.cekmeceTutamak.setAttribute("aria-expanded", "true"); return; }
    const H = kok.clientHeight || window.innerHeight, enFazla = Math.round(H * 0.85), min = cekmeceMin();
    const h = D.cekmeceKapali ? min : Math.max(min, Math.min(enFazla, D.cekmeceH || Math.round(H * 0.42)));
    ref.cekmece.style.height = h + "px";
    ref.cekmece.classList.toggle("kapali", !!D.cekmeceKapali);
    ref.cekmeceTutamak.setAttribute("aria-expanded", String(!D.cekmeceKapali));
  }
  function cekmeceAc() { if (D.tamEkran && D.cekmeceKapali) { D.cekmeceKapali = false; cekmeceUygula(); } }
  function cekmeceJesti() {
    const t = ref.cekmeceTutamak;
    let bas = null;
    t.addEventListener("pointerdown", function (e) {
      if (!D.tamEkran || sonucSagMi()) return;
      bas = { y: e.clientY, h: ref.cekmece.getBoundingClientRect().height, oynadi: false, id: e.pointerId };
      try { t.setPointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
      e.preventDefault();
    });
    t.addEventListener("pointermove", function (e) {
      if (!bas || e.pointerId !== bas.id) return;
      const dy = e.clientY - bas.y;
      if (!bas.oynadi && Math.abs(dy) < 6) return;
      bas.oynadi = true;
      const H = kok.clientHeight || window.innerHeight, min = cekmeceMin();
      const h = Math.max(min, Math.min(Math.round(H * 0.85), Math.round(bas.h - dy)));
      D.cekmeceKapali = h <= min + 4;
      if (!D.cekmeceKapali) D.cekmeceH = h;
      ref.cekmece.style.height = h + "px";
      ref.cekmece.classList.toggle("kapali", D.cekmeceKapali);
    });
    const bitir = function (e) {
      if (!bas || e.pointerId !== bas.id) return;
      const oynadi = bas.oynadi;
      bas = null;
      if (!oynadi) D.cekmeceKapali = !D.cekmeceKapali;
      cekmeceUygula();
      yerlesimKaydet();
      if (!D.cekmeceKapali) sonucBoyutlari();
    };
    t.addEventListener("pointerup", bitir);
    t.addEventListener("pointercancel", bitir);
    t.addEventListener("keydown", function (e) {
      if (!D.tamEkran || sonucSagMi()) return;
      const H = kok.clientHeight || window.innerHeight;
      if (e.key === "ArrowUp" || e.key === "ArrowDown") {
        e.preventDefault();
        D.cekmeceKapali = false;
        D.cekmeceH = Math.max(cekmeceMin(), Math.min(Math.round(H * 0.85), (D.cekmeceH || Math.round(H * 0.42)) + (e.key === "ArrowUp" ? 40 : -40)));
        cekmeceUygula(); yerlesimKaydet();
      } else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); D.cekmeceKapali = !D.cekmeceKapali; cekmeceUygula(); }
    });
  }
  // sonuç çizimleri kendi kapsayıcı genişliğine göre çizilir: boyut değişince yeniden
  function sonucBoyutlari() { if (!SON) return; sankeyCiz(); deformeyiCiz(); diyagramiCiz(); depremCiz(); nmCiz(); temelHaritaCiz(); }
  function sinir() {
    const xs = B.akslar.x.map(function (a) { return +a.konum; }), ys = B.akslar.y.map(function (a) { return +a.konum; });
    const zs = B.katlar.map(function (k) { return +k.kot; });
    zAkslari().forEach(function (a) { if (isFinite(+a.konum)) zs.push(+a.konum); });       // kat dışı Z aksları (saçak, mahya, kren)
    const M = window.MatrisAks;
    if (M && Array.isArray(B.aks_sistemleri) && B.aks_sistemleri.length) {                // ek aks sistemleri (döndürülmüş, silindirik)
      try { M.kesisimler(B, { tur: "3b" }).forEach(function (k) { xs.push(k.P[0]); ys.push(k.P[1]); zs.push(k.P[2]); }); } catch (e) { /* bozuk sistem */ }
    }
    [xs, ys, zs].forEach(function (l) { if (!l.length) l.push(0); });
    const th = temelDerinlik();
    return { x0: Math.min.apply(null, xs), x1: Math.max.apply(null, xs), y0: Math.min.apply(null, ys), y1: Math.max.apply(null, ys), z0: Math.min.apply(null, zs) - th, z1: Math.max.apply(null, zs) };
  }
  // ---------- Temel geometrisi (3B çizim ve temel planı; tanım §13) ----------
  // Toplam temel derinliği (temel üstü = kat 0 kotu): tekil h; mütemadi h_govde (tabla dahil toplam kiriş yüksekliği); radye max(h, kiriş h)
  function temelDerinlik() {
    const t = B.temeller;
    if (t.tip === "surekli" && t.surekli) return Math.max(0.1, +t.surekli.h_govde || 1);
    if (t.tip === "radye" && t.radye) return Math.max(0.1, +t.radye.h || 0.8, t.radye.kiris ? +t.radye.kiris.h || 0 : 0);
    return (t.varsayilan && +t.varsayilan.h) || 0.6;
  }
  function temelSecili(ad) { const s = B.temeller.surekli; return !s || s.akslar === "tum" || s.akslar.indexOf(ad) >= 0; }
  /**
   * Temel tabanları (temele oturan noktalar): [{X, Y, aks: [x aksı, y aksı] | null}]. Aks–kat modelinde 1. kat kolonları; genel modelde
   * ayrıca temel kotunda bir aks kesişimine (her aks sistemi; sözleşme C3) uç veren çubuklar, açık mesnetli (mesnetler) düğümler hariç.
   * GLOBAL aks adı 1 mm içinde eşlenir; eşlenmeyen (ek aks sistemi, ızgara dışı) tabanın aksı null.
   */
  function temelTabanlari() {
    const out = [], gor = new Set();
    const anahtar = function (X, Y) { return X.toFixed(3) + "," + Y.toFixed(3); };
    const ekle = function (X, Y, aks) { const k = anahtar(X, Y); if (gor.has(k)) return; gor.add(k); out.push({ X: X, Y: Y, aks: aks }); };
    B.kolonlar.forEach(function (c) {
      if (c.kat !== 1) return;
      const X = aksX(c.aks[0]), Y = aksY(c.aks[1]);
      if (X != null && Y != null) ekle(X, Y, [c.aks[0], c.aks[1]]);
    });
    if ((B.cubuklar || []).length && s3Var()) {
      const kot0 = B.katlar.length ? +B.katlar[0].kot : 0, ozel = new Set();
      (B.mesnetler || []).forEach(function (m) { const Q = refP(m && m.dugum); if (Q) ozel.add(anahtar(Q[0], Q[1]) + "," + Q[2].toFixed(3)); });
      const globalAd = function (l, v) { const a = l.filter(function (x) { return Math.abs(+x.konum - v) <= 1e-3; })[0]; return a ? a.ad : null; };
      B.cubuklar.forEach(function (c) {
        if (!c) return;
        [c.i, c.j].forEach(function (r) {
          const Q = refP(r);
          if (!Q || Math.abs(Q[2] - kot0) > 1e-6 || !aksKesisimRefMi(r) || ozel.has(anahtar(Q[0], Q[1]) + "," + Q[2].toFixed(3))) return;
          const ax = globalAd(B.akslar.x, Q[0]), ay = globalAd(B.akslar.y, Q[1]);
          ekle(Q[0], Q[1], ax && ay ? [ax, ay] : null);
        });
      });
    }
    return out;
  }
  // güncel çözümün temel ayrıntısı (motorun temel geometrisi: hatlar, plak) — yalnız modeldeki temel tipiyle çözülmüşse
  function cozumTemeli() {
    const v = SON && !sonEski ? SON.veri : null, t = v && v.temel;
    return t && t.tip && t.tip === (B.temeller && B.temeller.tip) ? t : null;
  }
  // Aks çizgisi boyunca temel tabanlarının uç konumları (yon "x": y aksı üzerinde X'ler; "y": x aksı üzerinde Y'ler)
  function aksKolonUclari(yon, ad, tabanlar) {
    const l = (tabanlar || temelTabanlari()).filter(function (t) { return t.aks && t.aks[yon === "x" ? 1 : 0] === ad; })
      .map(function (t) { return yon === "x" ? t.X : t.Y; });
    return l.length >= 2 ? [Math.min.apply(null, l), Math.max.apply(null, l)] : null;
  }
  // Mütemadi temel kirişleri: yon "x" → X doğrultusunda, y akslarında (1, 2, …); "y" → Y doğrultusunda, x akslarında (A, B, …); uç kolondan
  // "tasma" kadar konsol. Güncel çözüm varsa motorun kurduğu hatlar (veri.temel.hatlar).
  function temelKirisleri(tasmali) {
    const ct = cozumTemeli();
    if (ct && ct.tip === "surekli" && Array.isArray(ct.hatlar) && ct.hatlar.length && tasmali !== false) {
      return ct.hatlar.filter(function (h) { return isFinite(+h.sabit) && isFinite(+h.bas) && isFinite(+h.son); })
        .map(function (h) { return { yon: h.yon === "y" ? "y" : "x", aks: String(h.ad), konum: +h.sabit, bas: +h.bas, son: +h.son, no: h.no }; });
    }
    const t = B.temeller, s = t.surekli || TEMEL_VARS.surekli, l = [], tb = temelTabanlari();
    const ekle = function (yon, a) {
      if (!temelSecili(a.ad)) return;
      const u = aksKolonUclari(yon, a.ad, tb);
      if (!u) return;
      const ts = tasmali === false ? 0 : +s.tasma || 0;
      l.push({ yon: yon, aks: a.ad, konum: +a.konum, bas: u[0] - ts, son: u[1] + ts });
    };
    if (s.yon !== "y") B.akslar.y.forEach(function (a) { ekle("x", a); });
    if (s.yon !== "x") B.akslar.x.forEach(function (a) { ekle("y", a); });
    return l;
  }
  // Radye plağı: GLOBAL aks zarfı + taşma (kirişsiz radyede ızgara dışı tabanlar da zarfa girer); güncel çözüm varsa motorun plağı
  function radyeSinir() {
    const ct = cozumTemeli(), pk = ct && ct.tip === "radye" && ct.model && ct.model.plak;
    if (pk && [pk.X0, pk.X1, pk.Y0, pk.Y1].every(function (v) { return isFinite(+v); })) return { x0: +pk.X0, x1: +pk.X1, y0: +pk.Y0, y1: +pk.Y1 };
    const r = B.temeller.radye || TEMEL_VARS.radye, ts = +r.tasma || 0;
    const xs = B.akslar.x.map(function (a) { return +a.konum; }), ys = B.akslar.y.map(function (a) { return +a.konum; });
    if (!r.kiris) temelTabanlari().forEach(function (t) { if (!t.aks) { xs.push(t.X); ys.push(t.Y); } });
    if (!xs.length || !ys.length) return null;
    return { x0: Math.min.apply(null, xs) - ts, x1: Math.max.apply(null, xs) + ts, y0: Math.min.apply(null, ys) - ts, y1: Math.max.apply(null, ys) + ts };
  }
  // kirişli radyenin aks kirişleri: güncel çözümde motorun kirişli hatları (plak boyunca), yoksa uç tabanlar arası
  function radyeKirisleri(tabanlar) {
    const ct = cozumTemeli();
    if (ct && ct.tip === "radye" && Array.isArray(ct.hatlar) && ct.hatlar.some(function (h) { return h.kirisli; })) {
      return ct.hatlar.filter(function (h) { return h.kirisli; }).map(function (h) { return { yon: h.yon === "y" ? "y" : "x", aks: String(h.ad), konum: +h.sabit, bas: +h.bas, son: +h.son }; });
    }
    const l = [];
    B.akslar.y.forEach(function (a) { const u = aksKolonUclari("x", a.ad, tabanlar); if (u) l.push({ yon: "x", aks: a.ad, konum: +a.konum, bas: u[0], son: u[1] }); });
    B.akslar.x.forEach(function (a) { const u = aksKolonUclari("y", a.ad, tabanlar); if (u) l.push({ yon: "y", aks: a.ad, konum: +a.konum, bas: u[0], son: u[1] }); });
    return l;
  }
  // Temelleri sahneye ekler (tekil / mütemadi ters T / radye plak + kirişli radye kirişleri); temel planında ölçü etiketleri
  function temelleriCiz(sahne, T, b, P, s, kat, hafif, plan) {
    const t = B.temeller, z0 = katKot(0) || 0, hay = kat !== 0 ? " b3-hayalet" : "", tip = t.tip;
    const kol1 = B.kolonlar.filter(function (c) { return c.kat === 1 && aksX(c.aks[0]) != null && aksY(c.aks[1]) != null; });
    const tabanlar = tip === "tekil" ? [] : temelTabanlari();
    const etiket = function (X, Y, Z, metin) { const p = P(X, Y, Z); sahne.ekle(1e9, C.metin(p[0], p[1] + 4, metin, "b3-temel-t", "middle"), 2); };
    // yayılı temel parçaları sağ tık / uzun basma / bilgi için data-no taşır: mütemadi kiriş temelKirisleri() sırası, radye 1,
    // radye aks kirişi (y aksları, sonra x aksları) sırası; hedef = {tur: "temel", alt, no, aks, yon}
    const serit = function (yon, konum, a, bb, gen, zAlt, zUst, sinif, ek, hd) {
      const p1 = yon === "x" ? [a, konum] : [konum, a], p2 = yon === "x" ? [bb, konum] : [konum, bb], zm = (zAlt + zUst) / 2;
      C.prizma(sahne, T, b, [p1[0], p1[1], zm], [p2[0], p2[1], zm], yon === "x" ? [0, gen / 2, 0] : [gen / 2, 0, 0], [0, 0, (zUst - zAlt) / 2], sinif, ek, 1);
      if (kat === 0) hedefler.push(Object.assign({ tur: "dogru", a: P(p1[0], p1[1], zUst), b: P(p2[0], p2[1], zUst), r: 12 * s, kind: "temel" }, hd || {}));
    };
    if (tip === "surekli") {
      const sk = t.surekli || TEMEL_VARS.surekli, zt = z0 - sk.h_govde, hg = Math.max(0, sk.h_govde - sk.h_tabla);
      temelKirisleri().forEach(function (k, i) {
        const ek = ' data-tur="temel-kirisi" data-no="' + (i + 1) + '" data-aks="' + kacis(k.aks) + '" data-yon="' + k.yon + '"', hd = { alt: "surekli", no: i + 1, aks: k.aks, yon: k.yon };
        if (!(k.son - k.bas > 1e-6)) return;
        if (sk.h_tabla > 0) serit(k.yon, k.konum, k.bas, k.son, sk.B, zt, zt + sk.h_tabla, "b3-temel b3-temel-tabla" + hay, ek, hd);
        if (hg > 0) serit(k.yon, k.konum, k.bas, k.son, sk.b_govde, zt + sk.h_tabla, z0, "b3-temel b3-temel-govde" + hay, ek, hd);
        if (plan && !hafif) etiket(k.yon === "x" ? (k.bas + k.son) / 2 : k.konum, k.yon === "x" ? k.konum : (k.bas + k.son) / 2, z0, "TK-" + k.aks + " · B " + f2(sk.B));
      });
    } else if (tip === "radye") {
      const r = t.radye || TEMEL_VARS.radye, e = radyeSinir();
      if (e) {
        const hk = r.kiris ? +r.kiris.h : 0, zb = z0 - Math.max(r.h, hk), zp = zb + r.h;
        C.prizma(sahne, T, b, [(e.x0 + e.x1) / 2, (e.y0 + e.y1) / 2, zb], [(e.x0 + e.x1) / 2, (e.y0 + e.y1) / 2, zp], [(e.x1 - e.x0) / 2, 0, 0], [0, (e.y1 - e.y0) / 2, 0], "b3-temel b3-radye" + hay, ' data-tur="radye" data-no="1"', 1);
        if (kat === 0) hedefler.push({ tur: "cokgen", pts: [P(e.x0, e.y0, zp), P(e.x1, e.y0, zp), P(e.x1, e.y1, zp), P(e.x0, e.y1, zp)], kind: "temel", alt: "radye", no: 1 });
        if (r.kiris) {
          radyeKirisleri(tabanlar).forEach(function (k, i) {
            const ek = ' data-tur="radye-kirisi" data-no="' + (i + 1) + '" data-aks="' + kacis(k.aks) + '" data-yon="' + k.yon + '"';
            serit(k.yon, k.konum, k.bas, k.son, +r.kiris.b, zp, z0, "b3-temel b3-radye-kiris" + hay, ek, { alt: "radye-kirisi", no: i + 1, aks: k.aks, yon: k.yon });
          });
        }
        if (plan && !hafif) {
          etiket((e.x0 + e.x1) / 2, e.y0 + 0.35, z0, "Radye h " + f2(r.h) + " m" + (r.kiris ? " · kiriş " + f2(r.kiris.b) + "×" + f2(r.kiris.h) : ""));
          etiket((e.x0 + e.x1) / 2, e.y1 + 0.45, z0, f2(e.x1 - e.x0) + " m");
        }
      }
    } else {
      const th = temelDerinlik();
      kol1.forEach(function (c) {
        const X = aksX(c.aks[0]), Y = aksY(c.aks[1]);
        const oz = (t.ozel || []).filter(function (o) { return aksEsit(o.aks, c.aks); })[0] || {};
        const Bt = +oz.B || +t.varsayilan.B || 1.6, Lt = +oz.L || +t.varsayilan.L || 1.6;
        C.prizma(sahne, T, b, [X, Y, z0 - th], [X, Y, z0], [Bt / 2, 0, 0], [0, Lt / 2, 0], "b3-temel" + hay, ' data-tur="temel" data-no="' + c.no + '"', 1);
        if (kat === 0) hedefler.push({ tur: "daire", x: P(X, Y, z0)[0], y: P(X, Y, z0)[1], r: 18 * s, kind: "temel", no: c.no });
        if (!hafif && !plan) C.mesnet(sahne, T, b, [X, Y, z0 - th], t.mesnet, ' class="b3-mesnet' + hay + '"');
        if (plan && !hafif) etiket(X, Y - Lt / 2 - 0.3, z0, f2(Bt) + "×" + f2(Lt));
      });
      return;
    }
    // Winkler zemini (mütemadi / radye): temel tabanlarının (kolon altları; genel modelde temele oturan aks kesişimleri) altında yay simgesi
    if (!hafif && !plan) { const zb = z0 - temelDerinlik(); tabanlar.forEach(function (q) { C.mesnet(sahne, T, b, [q.X, q.Y, zb], "elastik", ' class="b3-mesnet b3-winkler' + hay + '"'); }); }
  }
  function katlarHedef() {
    return D.tumKatlar ? B.katlar.filter(function (k) { return k.no >= 1; }).map(function (k) { return k.no; }) : [D.kat];
  }
  function secildiMi(tur, no) { return D.secim.some(function (s) { return s.tur === tur && s.no === no; }); }
  let sonSinir = "";
  function sahneCiz() {
    const svg = ref.svg;
    if (!svg || !B) return;
    const b = kamera.bakis, W = cizimW, H = cizimH, sn = sinir();
    const snK = JSON.stringify(sn);
    if (snK !== sonSinir) { sonSinir = snK; kamera.sifirla(); }      // bina sınırları değişti: yeniden sığdır
    const pts = [];
    [sn.x0 - 1.4, sn.x1 + 1.4].forEach(function (X) { [sn.y0 - 1.2, sn.y1 + 0.6].forEach(function (Y) { [sn.z0, sn.z1 + 0.3].forEach(function (Z) { pts.push(C.izdusum(X, Y, Z, b)); }); }); });
    // §19 aks katmanı (balonlar, ölçü zinciri) plan ve cephede kenar payı ister; yüzen araç kutularının kenar şeritleri de payı büyütür
    // (sığdırılan model kutuların altında kalmaz). Sol ve sağ pay ayrı: C.donusum simetrik paylıdır, sağ pay öteleme ile verilir.
    const aksK = aksKatmaniVar(), kp = { sol: 0, sag: 0, ust: 0, alt: 0 };
    if (aksK && /^(plan|on|yan)$/.test(kamera.gorunum) && window.MatrisAks && window.MatrisAks.kenarPaylari) {
      try { Object.assign(kp, window.MatrisAks.kenarPaylari(B, aksGorunumu(), { balonR: aksBalonR(), olcu: D.aksOlcu })); } catch (e) { /* varsayılan paylar */ }
    }
    const ap = aracPaylari();
    const kenar = function (arac, aks, taban) { return arac > 0 ? arac + Math.max(14, aks || 0) : Math.max(taban, aks || 0); };
    let pl = kenar(ap.sol, kp.sol, 40), pr = kenar(ap.sag, kp.sag, 40), pu = kenar(ap.ust, kp.ust, 44), pa = kenar(ap.alt, kp.alt, 40);
    // 3B'de aks balonları ve kot etiketleri modelden sabit px uzaklıkta çizilir: sığdırma kutusunun dünya payı (1,2 m × ölçek) yetmezse
    // eksik px kenar payına eklenir (küçük pencerede balonlar araç kutularının altına girmez). Plan ve cephe MatrisAks.kenarPaylari ile.
    if (aksK && kamera.gorunum === "3b") {
      const R = aksBalonR(), T1 = C.donusum(pts, Math.max(1, W - pl - pr), H, { pl: 0, pu: pu, pa: pa }), dunya = 1.2 * T1.s;
      const gerek = { sol: 3.6 * R + 4, ust: 3.6 * R + 4, alt: 3.6 * R + 4, sag: Math.max(3.6 * R + 4, 0.8 * R + 62) };
      const ek = function (k) { return Math.max(0, gerek[k] - dunya); };
      if (["sol", "sag", "ust", "alt"].some(function (k) { return ek(k) > 14; })) {
        pl = kenar(ap.sol, ek("sol"), 40); pr = kenar(ap.sag, ek("sag"), 40); pu = kenar(ap.ust, ek("ust"), 44); pa = kenar(ap.alt, ek("alt"), 40);
      }
    }
    // paylar çizim alanının en çok %70'ini alır (dar ekranda model küçülür ama görünür ve kutuların dışında kalır)
    if (pl + pr > 0.7 * W) { const f = 0.7 * W / (pl + pr); pl *= f; pr *= f; }
    if (pu + pa > 0.7 * H) { const f = 0.7 * H / (pu + pa); pu *= f; pa *= f; }
    // sığdırma dikdörtgeni (svg px): testler ve eksen takımı (izdusum().alan)
    const alan = { x: Math.round(pl), y: Math.round(pu), w: Math.round(W - pl - pr), h: Math.round(H - pu - pa) };
    const pm = Math.min(pl, pr), T0 = C.donusum(pts, W - pl - pr + 2 * pm, H, { pl: pm, pu: pu, pa: pa }), ox = pl - pm;
    const T = ox ? { s: T0.s, W: W, H: H, x: function (v) { return T0.x(v) + ox; }, y: T0.y } : T0;
    const P = function (X, Y, Z) { const q = C.izdusum(X, Y, Z, b); return [T.x(q[0]), T.y(q[1])]; };
    const sahne = new C.Sahne();
    const s = kamera.pxOlcek(svg) || 1;     // 1 ekran px = s viewBox birimi
    const rHedef = (jest && jest.kaba({ pointerType: "touch" }) ? 26 : 22) * s;
    hedefler = [];
    const hafif = D.hafif, kat = D.kat, kot = katKot(kat), celik = B.sistem === "celik";
    const uyarilar = sonUyarilar || [];
    const uyariVar = function (tur, no) { return uyarilar.some(function (u) { return u.tur === tur && u.no === no; }); };
    // D/C görünümü (Tasarım sekmesi): kolon/kiriş D/C rengiyle, bütün katlar tam renk ve dokunulabilir; döşeme/duvar soluk
    const dcG = dcAktif(), dcSn = function (tur, no) { const e = kayitSahneden(tur, no); return " b3-dc b3-dc-" + (e ? dcSinif(e.dc) : "yok"); };

    // zemin ızgarası ve aks adları (katman 0)
    const izgara = function (Z, sinif) {
      B.akslar.x.forEach(function (a) { const p = P(+a.konum, sn.y0 - 0.6, Z), q = P(+a.konum, sn.y1 + 0.6, Z); sahne.ekle(-1e9, C.cizgi(p, q, sinif), 0); });
      B.akslar.y.forEach(function (a) { const p = P(sn.x0 - 0.6, +a.konum, Z), q = P(sn.x1 + 0.6, +a.konum, Z); sahne.ekle(-1e9, C.cizgi(p, q, sinif), 0); });
    };
    // aks katmanı (MatrisAks.sahneKatmani) varsa ızgara, aks adları ve kot etiketlerini o çizer (balon, ölçü zinciri, kesişimler)
    if (D.izgara && !aksK) {
      izgara(0, "b3-izgara");
      if (kat >= 1 && kot != null && kot !== 0) izgara(kot, "b3-izgara b3-izgara-kat");
    }
    if (!hafif && !aksK) {
      const ze = kat >= 1 && kot != null ? kot : 0;
      if (D.izgara) {
        B.akslar.x.forEach(function (a) { const p = P(+a.konum, sn.y0 - 1.0, ze); sahne.ekle(1e9, metinSvg(p[0], p[1] + 4, a.ad, "b3-aks-t", "middle", ' data-aks-x="' + kacis(a.ad) + '"'), 2); });
        B.akslar.y.forEach(function (a) { const p = P(sn.x1 + 1.0, +a.konum, ze); sahne.ekle(1e9, metinSvg(p[0], p[1] + 4, a.ad, "b3-aks-t", "middle", ' data-aks-y="' + kacis(a.ad) + '"'), 2); });
      }
      B.katlar.forEach(function (k) {
        if (kamera.gorunum === "plan" && k.no !== kat) return;      // planda bütün kotlar üst üste düşer: yalnız etkin kat
        const p = P(sn.x0 - 1.0, sn.y1 + 0.3, +k.kot);
        sahne.ekle(1e9, metinSvg(p[0], p[1] + 4, k.ad + " " + (k.kot >= 0 ? "+" : "") + f2(+k.kot), "b3-kot-t" + (k.no === kat ? " b3-kot-etkin" : ""), "end"), 2);
      });
    }
    // temeller (kat 1 kolonlarının altında; tip §13) ve mesnetler. Temel planı: Temel katı + Plan görünümü (üst katların kiriş/döşemesi çizilmez)
    const temelPlani = kat === 0 && kamera.gorunum === "plan";
    temelleriCiz(sahne, T, b, P, s, kat, hafif, temelPlani);
    // kolonlar
    B.kolonlar.forEach(function (c) {
      if (temelPlani && c.kat !== 1) return;
      if (!gorunurMu("kolon", c.no, c.kat)) return;
      const X = aksX(c.aks[0]), Y = aksY(c.aks[1]), z1 = katKot(c.kat), z0 = katKot(c.kat - 1);
      const ko = kesitOz(c.kesit);
      if (X == null || Y == null || z1 == null || z0 == null) return;
      const bX = ko ? (c.yon === "y" ? ko.b : ko.h) : 0.4, bY = ko ? (c.yon === "y" ? ko.h : ko.b) : 0.4;
      const sinif = "b3-kolon " + (dcG ? dcSn("kolon", c.no) : (ko && ko.celik ? "b3-celik" : "b3-beton") + (c.kat !== kat ? " b3-hayalet" : "")) + (secildiMi("kolon", c.no) ? " b3-secili" : "") + (uyariVar("kolon", c.no) ? " b3-uyarili" : "");
      const ekr = D.telKafes ? sahne.ekle(C.derinlik(X, Y, (z0 + z1) / 2, b), C.cizgi(P(X, Y, z0), P(X, Y, z1), "b3-tel " + sinif, ' data-tur="kolon" data-no="' + c.no + '"'), 1)
        : C.prizma(sahne, T, b, [X, Y, z0], [X, Y, z1], [bX / 2, 0, 0], [0, bY / 2, 0], sinif, ' data-tur="kolon" data-no="' + c.no + '"', 1);
      if (D.etiketler && !hafif) { const m = P(X, Y, (z0 + z1) / 2); sahne.ekle(1e9, metinSvg(m[0] + 7, m[1] - 4, "S" + c.no + " " + c.kesit, "b3-etiket-el", "start"), 2); }
      if (dcG && c.kat !== kat) hedefler.push({ tur: "dogru", a: P(X, Y, z0), b: P(X, Y, z1), r: 12 * s, kind: "nesne", nesne: "kolon", no: c.no });
      if (c.kat === kat) {
        hedefler.push({ tur: "dogru", a: P(X, Y, z0), b: P(X, Y, z1), r: 14 * s, kind: "nesne", nesne: "kolon", no: c.no });
        if (!hafif && uyariVar("kolon", c.no)) { const p = P(X, Y, (z0 + z1) / 2); sahne.ekle(1e9, rozet(p[0] + 12, p[1]), 2); }
      }
      void ekr;
    });
    // kirişler ve duvarlar
    B.kirisler.forEach(function (k) {
      if (temelPlani) return;
      if (!gorunurMu("kiris", k.no, k.kat)) return;
      const X1 = aksX(k.bas[0]), Y1 = aksY(k.bas[1]), X2 = aksX(k.son[0]), Y2 = aksY(k.son[1]), Z = katKot(k.kat);
      const ko = kesitOz(k.kesit);
      if (X1 == null || Y1 == null || X2 == null || Y2 == null || Z == null) return;
      const bb = ko ? ko.b : 0.25, hh = ko ? ko.h : 0.5, yatayX = Y1 === Y2;
      const e1 = yatayX ? [0, bb / 2, 0] : [bb / 2, 0, 0];
      const sinif = "b3-kiris " + (dcG ? dcSn("kiris", k.no) : (ko && ko.celik ? "b3-celik" : "b3-beton") + (k.kat !== kat ? " b3-hayalet" : "")) + (secildiMi("kiris", k.no) ? " b3-secili" : "") + (uyariVar("kiris", k.no) ? " b3-uyarili" : "");
      if (D.telKafes) sahne.ekle(C.derinlik((X1 + X2) / 2, (Y1 + Y2) / 2, Z, b), C.cizgi(P(X1, Y1, Z), P(X2, Y2, Z), "b3-tel " + sinif, ' data-tur="kiris" data-no="' + k.no + '"'), 1);
      else C.prizma(sahne, T, b, [X1, Y1, Z - hh / 2], [X2, Y2, Z - hh / 2], e1, [0, 0, hh / 2], sinif, ' data-tur="kiris" data-no="' + k.no + '"', 1);
      if (D.etiketler && !hafif) { const m = P((X1 + X2) / 2, (Y1 + Y2) / 2, Z); sahne.ekle(1e9, metinSvg(m[0], m[1] - 8, "K" + k.no + " " + k.kesit, "b3-etiket-el", "middle"), 2); }
      if (k.duvar && !hafif && !D.telKafes) {
        // duvar_h verilmişse (çatı parapeti) o yükseklikte; yoksa motor kuralı: üst kata kadar (kat yüksekliği − kiriş)
        const ust = k.duvar_h != null && k.duvar_h !== "" && +k.duvar_h > 0 ? Z + +k.duvar_h : katKot(k.kat + 1) != null ? katKot(k.kat + 1) - hh : Z + 1.0;
        const kose = [[X1, Y1, Z], [X2, Y2, Z], [X2, Y2, ust], [X1, Y1, ust]];
        C.dortgen(sahne, T, b, kose, "b3-duvar" + (k.kat !== kat || dcG ? " b3-hayalet" : ""), ' data-tur="duvar" data-no="' + k.no + '"', 1);
      }
      if (dcG && k.kat !== kat) hedefler.push({ tur: "dogru", a: P(X1, Y1, Z), b: P(X2, Y2, Z), r: 12 * s, kind: "nesne", nesne: "kiris", no: k.no });
      if (k.kat === kat) {
        hedefler.push({ tur: "dogru", a: P(X1, Y1, Z), b: P(X2, Y2, Z), r: 14 * s, kind: "nesne", nesne: "kiris", no: k.no });
        if (!hafif && uyariVar("kiris", k.no)) { const p = P((X1 + X2) / 2, (Y1 + Y2) / 2, Z); sahne.ekle(1e9, rozet(p[0], p[1] - 14), 2); }
      }
    });
    // döşemeler
    B.dosemeler.forEach(function (d) {
      if (temelPlani) return;
      if (!gorunurMu("doseme", d.no, d.kat)) return;
      const X1 = aksX(d.kose[0][0]), Y1 = aksY(d.kose[0][1]), X2 = aksX(d.kose[1][0]), Y2 = aksY(d.kose[1][1]), Z = katKot(d.kat);
      if (X1 == null || Y1 == null || X2 == null || Y2 == null || Z == null) return;
      const kose = [[X1, Y1, Z], [X2, Y1, Z], [X2, Y2, Z], [X1, Y2, Z]];
      const sinif = "b3-doseme" + (D.telKafes ? " b3-tel-doseme" : "") + (d.kat !== kat || dcG ? " b3-hayalet" : "") + (secildiMi("doseme", d.no) ? " b3-secili" : "") + (uyariVar("doseme", d.no) ? " b3-uyarili" : "");
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
    // §12/§19 genel model: çubuklar, paneller, mesnetler, bölme/kesişim düğümleri, ek yükler
    if (s3Var()) s3Ciz(sahne, T, b, P, s, hafif, dcG, temelPlani);
    // dokunma hedefleri: etkin katın aks kesişimleri ve hücreleri
    // (D/C görünümünde Seç aracıyla kesişim/hücre hedefleri konmaz: dokunuş doğrudan kolon/kirişe gider, bütün katlarda;
    //  plan düzlemi kat dışı bir Z aksındaysa ya da aks tabanlı çizim kipi etkinse aks–kat hedefleri konmaz)
    const aksKatModeli = !(+B.surum >= 3) || B.kolonlar.length + B.kirisler.length + B.dosemeler.length > 0;
    if (kat >= 1 && kot != null && !hafif && !(dcG && D.arac === "sec") && duzlemKatMi() && !aktifKip() && aksKatModeli) {
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
    // deprem: kat kuvveti okları ve kütle merkezi (Deprem sekmesi ya da EX/EY durumu seçiliyken)
    if (SON && !sonEski && !hafif && depremVar() && typeof depremVurguCiz === "function") depremVurguCiz(sahne, P, b, s);
    const vb = kamera.viewBox().split(" ").map(Number);
    const eksen = eksenTakimi(vb, b, alan, W, H);
    svg.setAttribute("viewBox", kamera.viewBox());
    svg.innerHTML = '<defs><pattern id="b3-tarama" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" class="b3-tarama-c"/></pattern>' +
      '<pattern id="b3-dc-desen" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)"><rect width="7" height="7" class="b3-dc-desen-z"/><line x1="0" y1="0" x2="0" y2="7" class="b3-dc-desen-c"/></pattern></defs>' +
      sahne.html() + eksen + '<path id="bn-gecici" class="b3-gecici" d=""/>';
    SAHNE_BAGLAM = { P: P, P3: function (Q) { return P(Q[0], Q[1], Q[2]); }, T: T, bakis: { fi: b.fi, psi: b.psi }, s: s, W: W, H: H, gorunum: kamera.gorunum, kat: kat, bina: B, hafif: hafif, alan: alan };
    katmanlariCiz();
    dcLejantCiz();
    olayYay("ciz", SAHNE_BAGLAM);
  }
  function rozet(x, y) {
    return '<g class="b3-rozet"><circle cx="' + r1(x) + '" cy="' + r1(y) + '" r="8"/>' + metinSvg(x, y + 4, "!", "b3-rozet-t", "middle") + "</g>";
  }

  // ---------- §12/§19 genel model (surum 3) çizimi ----------
  // REF → koordinat (MatrisAks.Cozucu; model anlık görüntüsü başına önbellek). Çözülemeyen REF null (eleman çizilmez, denetim uyarır).
  const s3Onbellek = { anahtar: null, cz: null, konum: new Map() };
  function s3Cozucu() {
    const M = window.MatrisAks;
    if (!M || !B) return null;
    const a = sonAnlik || anlikGoruntu();
    if (s3Onbellek.anahtar !== a) {
      s3Onbellek.anahtar = a; s3Onbellek.konum = new Map();
      try { s3Onbellek.cz = new M.Cozucu(B); } catch (e) { s3Onbellek.cz = null; }
    }
    return s3Onbellek.cz;
  }
  function refP(ref) {
    const cz = s3Cozucu();
    if (!cz || ref == null) return null;
    const k = typeof ref === "object" ? JSON.stringify(ref) : String(ref);
    if (s3Onbellek.konum.has(k)) return s3Onbellek.konum.get(k);
    let P = null;
    try { P = cz.coz(ref); } catch (e) { P = null; }
    s3Onbellek.konum.set(k, P);
    return P;
  }
  function aksKatmaniVar() { return KATMANLAR.some(function (k) { return k.ad === "aks"; }); }
  // aks balonu yarıçapı (viewBox birimi): dar sahnede küçük (balonlar ızgarayı örtmesin)
  function aksBalonR() { return cizimW < 520 ? 7.5 : 11; }
  // çizim boyutları: profil (mm → m), dikdörtgen, vute (temel + ek yükseklik), katalog dışı boru/kutu (addaki ilk sayı)
  function kesitBoyut(ad, derin) {
    const k = B.kesitler[ad];
    if (!k || (derin || 0) > 3) return null;
    if (k.tip === "vute") { const t = kesitBoyut(k.temel, (derin || 0) + 1) || { b: 0.18, h: 0.4, celik: true }; return { b: t.b, h: t.h + (+k.ek_yukseklik || 0) / 2, celik: t.celik }; }
    if (k.tip === "profil") {
      const p = profilBul(k.profil);
      if (p) return { b: p.b / 1000, h: p.h / 1000, celik: true };
      const bp = basitProfil(k.profil);
      if (bp) return { b: +bp.b, h: +bp.h, celik: true };
      const m = /(\d+(?:[.,]\d+)?)/.exec(String(k.profil || ""));
      const d = m ? parseFloat(m[1].replace(",", ".")) / 1000 : 0.15;
      return { b: d, h: d, celik: true };
    }
    const o = kesitOz(ad);
    return o ? { b: o.b, h: o.h, celik: !!o.celik } : null;
  }
  // etkin düzlem (plan: Z, önden cephe: Y, yandan kesit: X); 3B'de null. Düzlemdeki elemanlar tam, öbürleri soluk çizilir.
  function s3Duzlem() {
    const g = kamera ? kamera.gorunum : "3b";
    if (g === "plan") { const z = zAksBul(duzlemZ()); return z ? { i: 2, v: +z.konum } : null; }
    if (g === "on") { const y = aksY(cepheAks("y")); return y != null ? { i: 1, v: y } : null; }
    if (g === "yan") { const x = aksX(cepheAks("x")); return x != null ? { i: 0, v: x } : null; }
    return null;
  }
  function s3Duzlemde(dz, noktalar, hepsi) {
    if (!dz) return true;
    const ic = function (P) { return Math.abs(P[dz.i] - dz.v) < 0.002; };
    return hepsi ? noktalar.every(ic) : noktalar.some(ic);
  }
  // genel çözümde çubuk numarası → sahne anahtarı (sahnede o çubuk yoksa kaydın aks–kat kaynağı: karma model)
  function cubuktanSahne(cno) {
    if (nesneBul("cubuk", cno)) return { tur: "cubuk", no: cno };
    const r = dcKaydiCubuk(cno), k = r && r.kaynak && r.kaynak.aks_kat ? r.kaynak : null;
    return k && nesneBul(k.aks_kat, +k.no) ? { tur: k.aks_kat, no: +k.no } : { tur: "cubuk", no: cno };
  }
  function dcKaydiCubuk(no) {
    const v = V();
    if (!v || !v.tasarim) return null;
    return (v.tasarim.elemanlar || []).filter(function (e) { return e.cubuk === no || (e.tur === "cubuk" && e.no === no); })[0] || null;
  }
  const CUBUK_TURLERI = [["kolon", "Kolon"], ["kiris", "Kiriş"], ["capraz", "Çapraz"], ["makas-ust", "Makas üst başlık"], ["makas-alt", "Makas alt başlık"],
    ["makas-dikme", "Makas dikmesi"], ["makas-diyagonal", "Makas diyagonali"], ["asik", "Aşık"], ["kren", "Kren kirişi"], ["bag", "Bağ"], ["diger", "Diğer"]];
  function s3Ciz(sahne, T, b, P, s, hafif, dcG, temelPlani) {
    const MO = window.ModelOps, dz = s3Duzlem(), kot0 = B.katlar.length ? +B.katlar[0].kot : 0;
    const uyari = function (tur, no) { return (sonUyarilar || []).some(function (u) { return u.tur === tur && u.no === no; }); };
    const ozelMesnet = new Set();
    (B.mesnetler || []).forEach(function (m) { const Q = refP(m && m.dugum); if (Q) ozelMesnet.add(Q.map(function (v) { return v.toFixed(3); }).join(",")); });
    const tabanlar = new Map();
    // paneller (yarı saydam; kalınlık 0 = sac kaplama: ince kesikli kenar)
    (B.paneller || []).forEach(function (p) {
      if (!p || !Array.isArray(p.kose) || temelPlani || !gorunurMu("panel", p.no, p.kat)) return;
      const K = p.kose.map(refP);
      if (K.some(function (Q) { return !Q; })) return;
      const icinde = s3Duzlemde(dz, K, true);
      const sinif = "b3-panel b3-panel-" + (p.tur || "doseme") + (+p.kalinlik > 0 ? "" : " b3-sac") + (icinde ? "" : " b3-hayalet") + (secildiMi("panel", p.no) ? " b3-secili" : "") + (D.telKafes ? " b3-tel-doseme" : "");
      const ekr = C.dortgen(sahne, T, b, K, sinif, ' data-tur="panel" data-no="' + p.no + '"', 1);
      if (icinde) hedefler.push({ tur: "cokgen", pts: ekr, kind: "nesne", nesne: "panel", no: p.no });
      if (!hafif && (D.etiketler || uyari("panel", p.no))) {
        const m = [0, 1, 2].map(function (i) { return K.reduce(function (t, Q) { return t + Q[i]; }, 0) / K.length; }), q = P(m[0], m[1], m[2]);
        if (D.etiketler) sahne.ekle(1e9, metinSvg(q[0], q[1] + 4, "P" + p.no, "b3-doseme-t", "middle"), 2);
        if (uyari("panel", p.no)) sahne.ekle(1e9, rozet(q[0] + 16, q[1] - 10), 2);
      }
    });
    // çubuklar: kesit prizması (yerel eksenler motor kuralıyla; aci), tel kafeste eksen çizgisi
    (B.cubuklar || []).forEach(function (c) {
      if (!c || temelPlani || !gorunurMu("cubuk", c.no, c.kat)) return;
      const Pi = refP(c.i), Pj = refP(c.j);
      if (!Pi || !Pj) return;
      const L = Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1], Pj[2] - Pi[2]);
      if (L < 1e-6) return;
      const icinde = s3Duzlemde(dz, [Pi, Pj], dz && dz.i !== 2);
      const kb = kesitBoyut(c.kesit), celik = kb ? kb.celik : B.sistem === "celik";
      const tur = c.tur || "diger";
      let sinif = "b3-cubuk b3-cubuk-" + tur + " " + (dcG ? (function () { const e = dcKaydiCubuk(c.no); return "b3-dc b3-dc-" + (e ? dcSinif(e.dc) : "yok"); })() : (celik ? "b3-celik" : "b3-beton")) +
        (icinde ? "" : " b3-hayalet") + (secildiMi("cubuk", c.no) ? " b3-secili" : "") + (uyari("cubuk", c.no) ? " b3-uyarili" : "") + (c.yalniz_cekme ? " b3-yc" : "") + (kb ? "" : " b3-kesitsiz");
      const ek = ' data-tur="cubuk" data-no="' + c.no + '"';
      const ex = MO && MO.yerelEksenVektor ? MO.yerelEksenVektor(Pi, Pj, +c.aci || 0) : null;
      if (D.telKafes || !kb || !ex || hafif && L > 0) {
        sahne.ekle(C.derinlik((Pi[0] + Pj[0]) / 2, (Pi[1] + Pj[1]) / 2, (Pi[2] + Pj[2]) / 2, b), C.cizgi(P(Pi[0], Pi[1], Pi[2]), P(Pj[0], Pj[1], Pj[2]), "b3-tel " + sinif, ek), 1);
      } else {
        const h2 = Math.max(0.05, kb.h) / 2, b2 = Math.max(0.04, kb.b) / 2;
        C.prizma(sahne, T, b, Pi, Pj, ex.y.map(function (v) { return v * h2; }), ex.z.map(function (v) { return v * b2; }), sinif, ek, 1);
      }
      const a = P(Pi[0], Pi[1], Pi[2]), q = P(Pj[0], Pj[1], Pj[2]);
      if (icinde || !dz) hedefler.push({ tur: "dogru", a: a, b: q, r: 12 * s, kind: "nesne", nesne: "cubuk", no: c.no });
      // çubuk üstündeki duvar (yükseklik duvar_h ya da üstteki Z aksına kadar, kesit yüksekliği düşülür)
      if (c.duvar && !hafif && !D.telKafes) {
        const zAlt = Math.max(Pi[2], Pj[2]), ustZ = zAkslari().map(function (x) { return +x.konum; }).filter(function (z) { return z > zAlt + 1e-6; }).sort(function (x, y) { return x - y; })[0];
        const hd = c.duvar_h != null ? +c.duvar_h : ustZ != null ? ustZ - zAlt - (kb ? kb.h : 0) : 1.0;
        if (hd > 0.05) C.dortgen(sahne, T, b, [Pi, Pj, [Pj[0], Pj[1], Pj[2] + hd], [Pi[0], Pi[1], Pi[2] + hd]], "b3-duvar" + (icinde && !dcG ? "" : " b3-hayalet"), ' data-tur="cubuk" data-no="' + c.no + '"', 1);
      }
      if (!hafif) {
        // uç serbestliği: momentler serbest (mafsal) → içi boş daire; yalnız çekme → kesikli eksen
        const ekrBoy = Math.hypot(q[0] - a[0], q[1] - a[1]) / s;
        ["i", "j"].forEach(function (u) {
          const sb = c.serbest && Array.isArray(c.serbest[u]) ? c.serbest[u] : [];
          if (!sb.length || ekrBoy < 34 || (dz && !icinde)) return;
          const t = Math.min(0.35, 0.6 / L), Q = u === "i" ? [Pi[0] + (Pj[0] - Pi[0]) * t, Pi[1] + (Pj[1] - Pi[1]) * t, Pi[2] + (Pj[2] - Pi[2]) * t] : [Pj[0] + (Pi[0] - Pj[0]) * t, Pj[1] + (Pi[1] - Pj[1]) * t, Pj[2] + (Pi[2] - Pj[2]) * t];
          const w = P(Q[0], Q[1], Q[2]), mafsal = sb.indexOf("My") >= 0 && sb.indexOf("Mz") >= 0;
          sahne.ekle(C.derinlik(Q[0], Q[1], Q[2], b) + 0.5, '<circle class="b3-mafsal' + (mafsal ? "" : " b3-mafsal-kismi") + (icinde ? "" : " b3-hayalet") + '" cx="' + r1(w[0]) + '" cy="' + r1(w[1]) + '" r="' + r1((dz ? 3.6 : 2.8) * s) + '"/>', 2);
        });
        if (c.yalniz_cekme) sahne.ekle(C.derinlik((Pi[0] + Pj[0]) / 2, (Pi[1] + Pj[1]) / 2, (Pi[2] + Pj[2]) / 2, b) + 0.4, C.cizgi(a, q, "b3-yc-c" + (icinde ? "" : " b3-hayalet")), 2);
        if (D.etiketler) { const m = P((Pi[0] + Pj[0]) / 2, (Pi[1] + Pj[1]) / 2, (Pi[2] + Pj[2]) / 2); sahne.ekle(1e9, metinSvg(m[0] + 6, m[1] - 6, "C" + c.no + (c.kesit ? " " + c.kesit : ""), "b3-etiket-el", "start"), 2); }
        if (uyari("cubuk", c.no)) { const m = P((Pi[0] + Pj[0]) / 2, (Pi[1] + Pj[1]) / 2, (Pi[2] + Pj[2]) / 2); sahne.ekle(1e9, rozet(m[0] + 12, m[1]), 2); }
        // temel kotundaki aks kesişimi uçları (her aks sistemi): temel mesnedi (sözleşme C3; bölme/kesişim/koordinat düğümü değil)
        [[c.i, Pi], [c.j, Pj]].forEach(function (u) { if (Math.abs(u[1][2] - kot0) < 1e-6 && aksKesisimRefMi(u[0])) tabanlar.set(u[1].map(function (v) { return v.toFixed(3); }).join(","), u[1]); });
      }
    });
    if (!hafif) {
      const tip = B.temeller && B.temeller.mesnet === "mafsal" ? "mafsal" : B.temeller && B.temeller.mesnet === "elastik" ? "elastik" : "ankastre";
      // temel tabanlarının mesnet simgesi yalnız tekil temelde (C3 nokta mesnetleri); mütemadi / radyede tabanlar Winkler ağına oturur
      // (temelleriCiz yay simgesi çizer). Güncel çözüm varsa motorun kurduğu temel mesnetleri (veri.ag.mesnetler), yoksa aynı kural (C3)
      if (!B.temeller || !B.temeller.tip || B.temeller.tip === "tekil") {
        const cm = s3CozumMesnetleri();
        if (cm) cm.forEach(function (m) { const k = m.Q.map(function (v) { return v.toFixed(3); }).join(","); if (!ozelMesnet.has(k) && !s3AksKatKolonTabani(m.Q)) C.mesnet(sahne, T, b, m.Q, m.tip, ' data-s3-taban="1"'); });
        else tabanlar.forEach(function (Q, k) { if (!ozelMesnet.has(k) && !s3AksKatKolonTabani(Q)) C.mesnet(sahne, T, b, Q, tip, ' data-s3-taban="1"'); });
      }
      // açık mesnetler (mesnetler listesi); yay rijitliği (kx … krz; sözleşme C13) verilen mesnet yay simgesiyle, ipucunda rijitlikler
      (B.mesnetler || []).forEach(function (m, i) {
        const Q = refP(m && m.dugum);
        if (!Q) return;
        const tum = m.ux && m.uy && m.uz, don = m.rx && m.ry && m.rz, yay = mesnetYaylari(m);
        const tur = yay.length ? "elastik" : tum && don ? "ankastre" : "mafsal";
        const ek = ' data-tur="mesnet" data-no="' + (i + 1) + '"' + (yay.length ? ' data-yay="1"' : "") + (secildiMi("mesnet", i + 1) ? ' data-secili="1"' : "");
        const w = C.mesnet(sahne, T, b, Q, tur, ek, yay.length ? "Yaylı mesnet " + (i + 1) + ": " + yay.join(", ") : null);
        if (!tum && !yay.length) sahne.ekle(1e9, '<path class="b3-kayici" d="M' + pt(w[0] - 12, w[1] + 17) + " L" + pt(w[0] + 12, w[1] + 17) + '"/>', 2);
        hedefler.push({ tur: "daire", x: w[0], y: w[1] + 6 * s, r: 12 * s, kind: "nesne", nesne: "mesnet", no: i + 1 });
      });
      // bölme / kesişim düğümleri (yakalama noktaları; seçilebilir): plan / cephede ya da bir çizim aracı etkinken
      const dugumGoster = !!dz || D.etiketler || (!!aktifKip() && /^(cubuk-ciz|egik-cubuk|mesnet|yuk-ata|tasi|dondur|dogrusal-dizi|yapistir|olc-)/.test(D.arac));
      (B.dugumler || []).forEach(function (d) {
        if (!dugumGoster || !d || (d.tur !== "bolme" && d.tur !== "kesisim")) return;
        const Q = refP({ dugum: d.no });
        if (!Q || !s3Duzlemde(dz, [Q], true)) return;
        const w = P(Q[0], Q[1], Q[2]);
        sahne.ekle(C.derinlik(Q[0], Q[1], Q[2], b) + 0.6, '<rect class="b3-bolme' + (d.tur === "kesisim" ? " b3-bolme-kesisim" : "") + (secildiMi("dugum", d.no) ? " b3-secili" : "") + '" x="' + r1(w[0] - 2.6 * s) + '" y="' + r1(w[1] - 2.6 * s) + '" width="' + r1(5.2 * s) + '" height="' + r1(5.2 * s) + '" transform="rotate(45 ' + r1(w[0]) + " " + r1(w[1]) + ')" data-tur="dugum" data-no="' + d.no + '"/>', 2);
        hedefler.unshift({ tur: "daire", x: w[0], y: w[1], r: 9 * s, kind: "nesne", nesne: "dugum", no: d.no });
      });
      if (D.etiketler || D.arac === "yuk-ata") s3YukleriCiz(sahne, P, b, s);
    }
  }
  // açık mesnedin yay rijitlikleri (bina eksenleri; sözleşme C13): ["k_z = 10 000 kN/m", …]; yaysız mesnette []
  const MESNET_YAY = [["kx", "k_x", "kN/m"], ["ky", "k_y", "kN/m"], ["kz", "k_z", "kN/m"], ["krx", "k_rx", "kN·m/rad"], ["kry", "k_ry", "kN·m/rad"], ["krz", "k_rz", "kN·m/rad"]];
  function mesnetYaylari(m) {
    return MESNET_YAY.filter(function (k) { return m && m[k[0]] != null && m[k[0]] !== "" && isFinite(+m[k[0]]) && +m[k[0]] > 0; })
      .map(function (k) { return k[1] + " = " + (+m[k[0]]).toLocaleString("tr-TR", { maximumFractionDigits: 3 }) + " " + k[2]; });
  }
  // REF bir aks kesişimi mi ({aks, z} / {aks, kat} / {sistem, aks, z}; ya da aks adresi taşıyan düğüm kaydı) — bölme, kesişim ve
  // koordinat düğümleri temel mesnedi almaz (sözleşme C3)
  function aksKesisimRefMi(r) {
    if (!r || typeof r !== "object") return false;
    if (Array.isArray(r.aks)) return r.z != null || r.kat != null;
    if (r.dugum != null) { const d = nesneBul("dugum", +r.dugum); return !!(d && Array.isArray(d.aks) && d.tur !== "bolme" && d.tur !== "kesisim"); }
    return false;
  }
  // güncel genel çözümün temel mesnetleri (açık mesnetler hariç; onlar mesnetler listesinden çizilir): [{Q: [X, Y, Z], tip}] | null
  function s3CozumMesnetleri() {
    const v = SON && !sonEski ? SON.veri : null;
    if (!v || v.model !== "genel" || !v.ag || !Array.isArray(v.ag.mesnetler)) return null;
    const nd = {}; (v.ag.dugumler || []).forEach(function (d) { nd[d.no] = d; });
    return v.ag.mesnetler.filter(function (m) { return m.kaynak !== "mesnetler" && nd[m.dugum]; }).map(function (m) {
      const d = nd[m.dugum];
      return { Q: [d.X, d.Y, d.Z], tip: m.tip === "mafsal" || m.tip === "elastik" ? m.tip : "ankastre" };
    });
  }
  // aks–kat kolonunun tabanı zaten temel olarak çizilir
  function s3AksKatKolonTabani(Q) {
    return B.kolonlar.some(function (c) { return c.kat === 1 && Math.abs(aksX(c.aks[0]) - Q[0]) < 1e-3 && Math.abs(aksY(c.aks[1]) - Q[1]) < 1e-3; });
  }
  // ek yükler: çubukta yayılı/tekil (global ya da yerel yönde ok), düğümde kuvvet, panelde yüzey yükü etiketi
  function s3YukleriCiz(sahne, P, b, s) {
    const MO = window.ModelOps;
    (B.ek_yukler || []).forEach(function (y) {
      if (!y) return;
      const sinif = "b3-ekyuk b3-ekyuk-" + String(y.durum || "G").toUpperCase();
      if (y.tur === "cubuk") {
        const c = (B.cubuklar || []).filter(function (x) { return +x.no === +y.cubuk; })[0];
        const Pi = c && refP(c.i), Pj = c && refP(c.j);
        if (!Pi || !Pj) return;
        let v = { X: [1, 0, 0], Y: [0, 1, 0], Z: [0, 0, 1] }[String(y.yon || "Z").toUpperCase()];
        if (!v && MO) { const ex = MO.yerelEksenVektor(Pi, Pj, +c.aci || 0), k = String(y.yon || "").charAt(0); v = ex && ex[k] ? ex[k] : [0, 0, 1]; }
        const q = y.q1 != null ? +y.q1 : y.q != null ? +y.q : y.P != null ? +y.P : 0;
        if (!q) return;
        const w = C.yon(v.map(function (x) { return x * Math.sign(q); }), b);
        const ts = y.x != null && y.x1 == null && y.q1 == null ? [+y.x / (y.oransal ? 1 : Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1], Pj[2] - Pi[2]))] : [0.15, 0.5, 0.85];
        ts.forEach(function (t, k) {
          const Q = [Pi[0] + (Pj[0] - Pi[0]) * t, Pi[1] + (Pj[1] - Pi[1]) * t, Pi[2] + (Pj[2] - Pi[2]) * t], u = P(Q[0], Q[1], Q[2]);
          sahne.ekle(1e9, C.kuvvetOku(u, w, 22 * s, sinif + "-c", sinif + "-o", k === 1 || ts.length === 1 ? f2(Math.abs(q)) + (ts.length === 1 ? " kN" : " kN/m") : "", "b3-ekyuk-t"), 2);
        });
      } else if (y.tur === "dugum") {
        const Q = refP(y.dugum);
        if (!Q) return;
        const F = [+y.FX || 0, +y.FY || 0, +y.FZ || 0], Fb = Math.hypot(F[0], F[1], F[2]);
        if (Fb < 1e-12) return;
        const u = P(Q[0], Q[1], Q[2]), w = C.yon(F.map(function (x) { return x / Fb; }), b);
        sahne.ekle(1e9, C.kuvvetOku(u, w, 30 * s, sinif + "-c", sinif + "-o", f2(Fb) + " kN", "b3-ekyuk-t"), 2);
      } else if (y.tur === "panel") {
        const p = (B.paneller || []).filter(function (x) { return +x.no === +y.panel; })[0];
        const K = p && Array.isArray(p.kose) ? p.kose.map(refP) : null;
        if (!K || K.some(function (Q) { return !Q; })) return;
        const m = [0, 1, 2].map(function (i) { return K.reduce(function (t, Q) { return t + Q[i]; }, 0) / K.length; }), u = P(m[0], m[1], m[2]);
        sahne.ekle(1e9, metinSvg(u[0], u[1] + 16, String(y.durum || "G") + ": " + (y.g ? "g " + f2(+y.g) : "") + (y.q ? " q " + f2(+y.q) : "") + " kN/m²", "b3-ekyuk-t", "middle"), 2);
      }
    });
  }
  // eksen takımı sığdırma dikdörtgeninin sol alt köşesinde (görünüm kutusunun köşesi araç kutularının köşe düğmelerinin altında kalır)
  function eksenTakimi(vb, b, alan, W, H) {
    const ox = alan && W ? vb[0] + (alan.x + 30) * vb[2] / W : vb[0] + 26, oy = alan && H ? vb[1] + (alan.y + alan.h - 30) * vb[3] / H : vb[1] + vb[3] - 22;
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
      dokun: function (p, e) {
        const k = aktifKip(), h = C.vurus(hedefler, p[0], p[1]);
        if (k && k.dokun) {      // kayıtlı kip (ölçüm; bina_cizim.js çizim araçları)
          // aks–kat kiriş / döşeme / kolon vuruş hedefleri yalnız etkin katta: başka kattaki elemana dokunulduysa, elemana uygulanması
          // güvenli kipler (yük ata: yük penceresi açar) o elemanı alır; kat adı iletide söylenir
          const d = !(h && h.kind === "nesne") && KAT_DISI_KIPLER[D.arac] && !dugumYakalanir(p) ? digerKatElemani(e) : null;
          if (d && KAT_DISI_KIPLER[D.arac].indexOf(d.tur) >= 0) {
            A.toast(digerKatAdi(d) + " — etkin kat " + katAd(D.kat) + "; " + KIP_ADI_KAT[D.arac] + " bu elemana uygulanıyor.");
            k.dokun(p, e, { kind: "nesne", nesne: d.tur, no: d.no, kat: d.kat }); return;
          }
          // kipin uygulamadığı türler (yük ata: aks–kat kolonu) kipe verilir: genel "bir elemana dokunun" yerine nedenini söyler
          if (d && (KAT_DISI_ILET[D.arac] || []).indexOf(d.tur) >= 0) { k.dokun(p, e, { kind: "nesne", nesne: d.tur, no: d.no, kat: d.kat }); return; }
          k.dokun(p, e, h); return;
        }
        aracUygula(h, p, e);
      },
      // uzun basma tek kaynak (Cizim3B): bağlam menüsü; MatrisBilgi yoksa seç + özellik paneli
      uzunBas: function (p, e) { uzunBasmaMenusu(p, e); },
      surukleBasla: function (p, e) {
        const k = aktifKip();
        if (k) { kipSurukle = !!(k.surukleBasla && k.surukleBasla(p, e)); return kipSurukle; }
        if (D.arac !== "kiris") return false;
        const h = C.vurus(hedefler, p[0], p[1]);
        if (!h || h.kind !== "kesisim") return false;
        D.kirisBas = h.aks; sahneCiz(); return true;
      },
      surukle: function (p, e) {
        if (kipSurukle) { const k = aktifKip(); if (k && k.surukle) k.surukle(p, e); return; }
        const g = document.getElementById("bn-gecici"), h0 = hedefler.filter(function (h) { return h.kind === "kesisim" && aksEsit(h.aks, D.kirisBas); })[0];
        if (g && h0) g.setAttribute("d", "M" + pt(h0.x, h0.y) + " L" + pt(p[0], p[1]));
      },
      surukleBitir: function (p, e) {
        if (kipSurukle) { kipSurukle = false; const k = aktifKip(); if (k && k.surukleBitir) k.surukleBitir(p, e); return; }
        const h = p ? C.vurus(hedefler, p[0], p[1]) : null;
        if (h && h.kind === "kesisim" && D.kirisBas && ayniDogru(D.kirisBas, h.aks)) { const bas = D.kirisBas; D.kirisBas = null; kirisEkle(bas, h.aks); }
        else { D.kirisBas = null; sahneCiz(); }
      },
    });
  }
  // fare sahne üstünde gezinirken (düğme basılı değil) etkin kipin hareket(p) işlevi: yakalama önizlemesi (ölçüm, bina_cizim.js çizimi)
  let kipSurukle = false, hoverIstek = 0, hoverSon = null;
  function hoverKur() {
    const svg = ref.svg;
    svg.addEventListener("pointermove", function (e) {
      const k = aktifKip();
      if (!k || !k.hareket || e.buttons || e.pointerType === "touch") return;
      hoverSon = e;
      if (hoverIstek) return;
      hoverIstek = requestAnimationFrame(function () { hoverIstek = 0; const k2 = aktifKip(); if (k2 && k2.hareket && hoverSon) k2.hareket(kamera.svgNokta(svg, hoverSon.clientX, hoverSon.clientY), hoverSon); });
    });
    svg.addEventListener("pointerleave", function (e) { const k = aktifKip(); if (k && k.hareket && e.pointerType !== "touch") k.hareket(null, e); });
  }
  // Başka kattaki elemanı kendi kipinde alabilen kipler (elemana uygulanması güvenli: yalnız pencere açar) ve kabul ettikleri türler
  const KAT_DISI_KIPLER = { "yuk-ata": ["kiris", "doseme"] };
  const KIP_ADI_KAT = { "yuk-ata": "Yük ata" };
  const KAT_DISI_ILET = { "yuk-ata": ["kolon"] };
  // aks–kat kolon / kiriş / döşeme vuruş hedefleri (C.vurus) yalnız etkin kattadır; dokunulan noktada DOM'da başka kata ait bir
  // eleman (duvar → kirişi) varsa {tur, no, kat}
  function digerKatElemani(e) {
    if (!e || e.clientX == null || !ref.svg || typeof document.elementFromPoint !== "function") return null;
    let el = null;
    try { el = document.elementFromPoint(e.clientX, e.clientY); } catch (x) { el = null; }
    const t = el && el.closest ? el.closest("[data-tur][data-no]") : null;
    if (!t || !ref.svg.contains(t)) return null;
    const tur = t.getAttribute("data-tur") === "duvar" ? "kiris" : t.getAttribute("data-tur"), no = +t.getAttribute("data-no");
    if (["kolon", "kiris", "doseme"].indexOf(tur) < 0 || !isFinite(no)) return null;
    const n = nesneBul(tur, no);
    if (!n || n.kat == null || +n.kat === D.kat) return null;
    return { tur: tur, no: no, kat: +n.kat };
  }
  // Yük ata önce düğüm / aks kesişimi yakalar (bina_cizim.js yuk-ata dokun; düğüm yükü penceresi): nokta bir düğüme yakınsa başka
  // kattaki elemana yönlendirilmez ("bu elemana uygulanıyor" iletisi ardından düğüm penceresi açılmasın). Düzlem süzgeci yok: 3B'de
  // kipin yakalamasıyla aynı, düzlem görünümlerinde onun üst kümesi (yönlendirme yalnız kesin elemana dokunuşta)
  function dugumYakalanir(p) {
    const O = modul("MatrisOlcum"), sb = SAHNE_BAGLAM;
    if (!O || typeof O.yakala !== "function" || !sb || !p) return false;
    try { const y = O.yakala(p, olcumGeo(), { kip: "cizim", cevir: sb.P3, tol: 16 * pxOlcek(), turler: ["dugum", "aks"] }); return !!(y && y.ref); }
    catch (x) { return false; }
  }
  function digerKatAdi(d) {
    return ({ kolon: "Kolon ", kiris: "Kiriş ", doseme: "Döşeme " }[d.tur] || "") + d.no + " “" + katAd(d.kat) + "” katında (kat " + d.kat + ")";
  }
  // etkin kattaki elemanlara uygulanan bir araçla başka kattaki elemana dokunulduğunda: o katı etkinleştirme iletisi
  function digerKatIletisi(d, arac) {
    A.toast(digerKatAdi(d) + "; " + arac + " yalnız etkin kattaki (" + katAd(D.kat) + ") elemanlara uygulanır. O katı etkinleştirin: üstteki kat düğmesi ya da PgUp / PgDn.");
  }
  // sayfa araçları: başka kattaki hangi elemanlar için ileti verilir (Seç'te geniş döşeme hayaletleri boşluğa dokunuşu bozmasın diye yok)
  const KAT_ARACLARI = { sec: { ad: "Seç", turler: ["kolon", "kiris"] }, sil: { ad: "Sil", turler: ["kolon", "kiris", "doseme"] }, duvar: { ad: "Duvar", turler: ["kiris"] } };
  function aracUygula(h, p, e) {
    void p;
    if (!h) {
      // başka kattaki elemana dokunuldu: sessizce hiçbir şey yapmamak yerine o katı etkinleştirmeyi söyle (seçimi bırakan
      // dokunuşlarda ileti gösterilmez; fırça da etkin kata uygulanır)
      const ka = KAT_ARACLARI[D.arac], d = ka && !D.kirisBas && !D.secim.length && !D.akisHedef ? digerKatElemani(e) : null;
      if (d && ka.turler.indexOf(d.tur) >= 0) { digerKatIletisi(d, D.firca && D.arac === "sec" ? "Kesit fırçası" : ka.ad); return; }
      if (D.kirisBas) { D.kirisBas = null; sahneCiz(); return; }
      if (D.secim.length) { D.secim = []; yenile(); }
      if (D.akisHedef) { D.akisHedef = null; sahneCiz(); }
      return;
    }
    if (h.kind === "formul") { formulGoster(h.key); return; }
    if (h.kind === "temel") { if (D.arac === "sec" || D.arac === "sil") { D.panelSekme = "bina"; yenile(); panelAc(); } return; }
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
    if (h.kind === "nesne") nesneDokun(h.nesne, h.no, e);
  }
  function nesneDokun(tur, no, e) {
    const n = nesneBul(tur, no);
    if (!n) return;
    if (D.firca && tur === "cubuk" && D.arac === "sec") { n.kesit = D.firca; A.toast(D.firca + " atandı."); degisti(); return; }
    if (D.arac === "sil") { nesneSil(tur, no); return; }
    if (D.arac === "duvar") {
      if (tur === "kiris") duvarToggle(n);
      else if (tur === "cubuk" && DUVARLI_CUBUK.indexOf(n.tur || "diger") >= 0) { if (n.duvar) { delete n.duvar; delete n.duvar_h; } else n.duvar = varsayilanDuvar(); degisti(); }
      else A.toast("Duvar kirişe (genel modelde kiriş, bağ ya da diğer türdeki çubuğa) atanır.");
      return;
    }
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
    if (SON && !sonEski && D.sekme === "tasarim" && tasarimVar() && (tur === "kolon" || tur === "kiris" || tur === "cubuk")) {
      const r = kayitSahneden(tur, no);
      if (r) { tasarimSec(r.tur, r.no, false); return; }
      A.toast("Bu eleman için tasarım kaydı yok.");
    }
    if (SON && !sonEski && D.sekme === "akis") { D.akisHedef = { tur: tur, no: no }; D.secim = [{ tur: tur, no: no }]; akisYenile(); yenile(); return; }
    if (secildiMi(tur, no)) D.secim = D.secim.filter(function (s) { return !(s.tur === tur && s.no === no); });
    else if (D.secim.length && (D.secim[0].tur === tur || (e && (e.shiftKey || e.ctrlKey || e.metaKey)))) D.secim.push({ tur: tur, no: no });
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
  // surum 3 elemanlarını sil (ModelOps: bağlı yükler ve yetim düğümler de gider); B yerinde güncellenir
  function s3Sil(liste) {
    const MO = window.ModelOps, l = liste.filter(function (s) { return ["cubuk", "panel", "dugum", "mesnet"].indexOf(s.tur) >= 0; });
    if (!l.length) return [];
    const nolar = function (tur) { return l.filter(function (s) { return s.tur === tur; }).map(function (s) { return +s.no; }); };
    const ms = new Set(nolar("mesnet"));
    if (ms.size) B.mesnetler = (B.mesnetler || []).filter(function (m, i) { return !ms.has(i + 1); });
    let m = B, uy = [];
    const uygula = function (f) { const r = f(m); if (r && r.model) { m = r.model; uy = uy.concat(r.uyarilar || []); } };
    if (MO) {
      const pn = nolar("panel").filter(function (n) { return nesneBul("panel", n); }), cn = nolar("cubuk").filter(function (n) { return nesneBul("cubuk", n); }), dn = nolar("dugum").filter(function (n) { return nesneBul("dugum", n); });
      try {
        if (pn.length) uygula(function (x) { return MO.panelSil(x, pn); });
        if (cn.length) uygula(function (x) { return MO.cubukSil(x, cn); });
        if (dn.length) uygula(function (x) { return MO.dugumSil(x, dn.map(function (n) { return { dugum: n }; })); });
      } catch (e) { A.toast(e.message); }
      if (m !== B) { Object.keys(m).forEach(function (k) { B[k] = m[k]; }); }
    } else {
      const cs = new Set(nolar("cubuk")), ps = new Set(nolar("panel"));
      B.cubuklar = (B.cubuklar || []).filter(function (c) { return !cs.has(+c.no); });
      B.paneller = (B.paneller || []).filter(function (p) { return !ps.has(+p.no); });
    }
    return uy;
  }
  function nesneSil(tur, no) {
    const n = nesneBul(tur, no);
    if (!n) return;
    if (["cubuk", "panel", "dugum", "mesnet"].indexOf(tur) >= 0) {
      const uy = s3Sil([{ tur: tur, no: no }]);
      D.secim = D.secim.filter(function (s) { return nesneBul(s.tur, s.no); });
      degisti();
      if (uy.length) A.toast(uy.join(" "));
      return;
    }
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
    const uy = s3Sil(l);
    degisti();
    if (uy.length) A.toast(uy.join(" "));
  }
  function ayniTurdenSec() {
    if (!D.secim.length) return;
    const tur = D.secim[0].tur;
    if (tur === "cubuk" || tur === "panel") {      // genel model: aynı türden (çubukta aynı tür alanı) bütün elemanlar
      const n0 = nesneBul(tur, D.secim[0].no), l = tur === "cubuk" ? B.cubuklar || [] : B.paneller || [];
      D.secim = l.filter(function (x) { return x && (x.tur || "") === ((n0 && n0.tur) || ""); }).map(function (x) { return { tur: tur, no: x.no }; });
      yenile(); return;
    }
    const liste = tur === "kolon" ? B.kolonlar : tur === "kiris" ? B.kirisler : B.dosemeler;
    D.secim = liste.filter(function (x) { return x.kat === D.kat; }).map(function (x) { return { tur: tur, no: x.no }; });
    yenile();
  }
  // ---------- Katlar ----------
  function katEkle(kopyala) {
    const ust = ustKat(), h = katH(ust) || 3, yeni = ust + 1;
    if (yeni > 12 && !s3Var()) { A.toast("En çok 12 kat (aks–kat modeli)."); return; }
    B.katlar.forEach(function (k) { if (k.no === ust && k.ad === "Çatı") k.ad = ust + ". kat"; });
    B.katlar.push({ no: yeni, ad: "Çatı", kot: +(katKot(ust) + h).toFixed(3) });
    zKatEkle(yeni, +(katKot(ust) + h).toFixed(3));
    let parapet = 0;
    if (kopyala) {
      B.kolonlar.filter(function (c) { return c.kat === ust; }).forEach(function (c) { B.kolonlar.push(Object.assign(kopya(c), { no: yeniNo(B.kolonlar), kat: yeni })); });
      B.kirisler.filter(function (k) { return k.kat === ust; }).forEach(function (k) { B.kirisler.push(Object.assign(kopya(k), { no: yeniNo(B.kirisler), kat: yeni })); });
      B.dosemeler.filter(function (d) { return d.kat === ust; }).forEach(function (d) { B.dosemeler.push(Object.assign(kopya(d), { no: yeniNo(B.dosemeler), kat: yeni })); });
      // eski çatı artık ara kat: parapet yüksekliği (duvar_h) yeni çatının kopyalarında kalır, eski çatıda kat yüksekliğinde duvar
      parapet = parapetKaldir(ust);
    }
    // boş kat: üst kat boşken eski çatı fiilen çatıdır, parapetleri (duvar_h) kalır; "Alt katı kopyala" onları yeni çatıya taşır.
    // Yeni kat elle kurulursa bu kirişlerde duvar parapet yüksekliğinde kalır: söylenir
    const kalan = kopyala ? 0 : B.kirisler.filter(function (k) { return k.kat === ust && k.duvar_h != null; }).length;
    D.kat = yeni;
    degisti();
    if (parapet) A.toast(parapetNotu(parapet));
    else if (kalan) {
      A.toast("“" + katAd(ust) + "” katındaki " + kalan + " kirişte çatı parapeti (duvar_h) duruyor. “Alt katı kopyala” onu yeni çatıya taşır; yeni katı elle " +
        "kurarsanız bu kirişlerin duvar yüksekliğini Tablolar › Duvar yükleri'nde boşaltın (boş = kat yüksekliği).");
    }
  }
  // Çatı kirişlerindeki duvar_h (şablonda 1,0 m parapet) o kat ara kat olunca anlamını yitirir: kaldırılır, duvar kat yüksekliğinde
  // (kat yüksekliği − kiriş) hesaplanır. Kaldırılan kiriş sayısı.
  function parapetKaldir(kat) {
    let n = 0;
    B.kirisler.forEach(function (k) { if (k.kat === kat && k.duvar_h != null) { delete k.duvar_h; n++; } });
    return n;
  }
  function parapetNotu(n) {
    return n + " eski çatı kirişinin parapet yüksekliği (duvar_h) kaldırıldı; bu kirişlerde duvar artık kat yüksekliğinde.";
  }
  function katSil(no) {
    if (no < 1 || B.katlar.length <= 2) { A.toast("En az bir kat kalmalı."); return; }
    const ust = ustKat();
    if (no !== ust && !window.confirm(katAd(no) + " ve üstündeki katlar bir alt kota kayar; bu kattaki elemanlar silinir. Devam?")) return;
    const h = katH(no);
    const geri = no === ust && no > 1 ? parapetGeriTasi(no, no - 1) : 0;
    // silinen çatının adı ("Çatı") alttaki katın kendiliğinden adı ("2. kat") yerine geçer (+Kat'ın yeniden adlandırmasının tersi)
    const catiAdi = no === ust ? (B.katlar.filter(function (k) { return k.no === no; })[0] || {}).ad : null;
    if (catiAdi === "Çatı") B.katlar.forEach(function (k) { if (k.no === no - 1 && k.ad === (no - 1) + ". kat") k.ad = "Çatı"; });
    zKatSil(no, h);
    B.kolonlar = B.kolonlar.filter(function (c) { return c.kat !== no; }).map(function (c) { if (c.kat > no) c.kat--; return c; });
    B.kirisler = B.kirisler.filter(function (k) { return k.kat !== no; }).map(function (k) { if (k.kat > no) k.kat--; return k; });
    B.dosemeler = B.dosemeler.filter(function (d) { return d.kat !== no; }).map(function (d) { if (d.kat > no) d.kat--; return d; });
    B.katlar = B.katlar.filter(function (k) { return k.no !== no; }).map(function (k) { if (k.no > no) { k.no--; k.kot = +(k.kot - h).toFixed(3); } return k; });
    D.kat = Math.min(D.kat, ustKat());
    degisti();
    if (geri) A.toast(geri + " kirişe silinen çatının parapet yüksekliği (duvar_h) geri verildi; “" + katAd(ustKat()) + "” yeniden çatı.");
  }
  // En üst kat (çatı) silinince alttaki kat çatı olur: silinen çatıdaki parapetli (duvar_h) kirişlerle aynı akstaki, duvarlı ve duvar_h'si
  // olmayan kirişlere aynı parapet yüksekliği verilir (+Kat → Üsttekini kopyala'nın tersi). Değişen kiriş sayısı.
  function parapetGeriTasi(cati, alt) {
    let n = 0;
    B.kirisler.forEach(function (k) {
      if (k.kat !== cati || k.duvar_h == null || k.duvar_h === "") return;
      const a = kirisBul(k.bas, k.son, alt);
      if (a && a.duvar && (a.duvar_h == null || a.duvar_h === "")) { a.duvar_h = k.duvar_h; n++; }
    });
    return n;
  }
  // kirişin aks açıklığı anahtarı (uçların sırası fark etmez): "A|1–B|1"
  function aciklikAnahtari(k) { return [k.bas.join("|"), k.son.join("|")].sort().join("–"); }
  function katKopyalaAlttan() {
    const alt = D.kat - 1;
    if (alt < 1) { A.toast("Altta kopyalanacak kat yok."); return; }
    const enUst = D.kat === ustKat(), dolu = ["kolonlar", "kirisler", "dosemeler"].some(function (l) { return B[l].some(function (x) { return x.kat === D.kat; }); });
    // boş en üst kata kopyalanıyorsa alttaki kat o ana dek fiilen çatıydı: parapetleri (duvar_h) yeni çatıya taşınır
    const altCatiydi = enUst && !dolu;
    // dolu çatı alttaki katın kopyasıyla değişir: önce sorulur; çatı kirişlerinin duvarı (parapet: duvar, duvar_h) aks açıklığına
    // göre saklanır ve kopyadaki aynı açıklıktaki kirişlere geri verilir (çatıda duvar kat yüksekliğine çıkmaz)
    if (enUst && dolu && !window.confirm("Çatı katı alttaki katın kopyasıyla değişecek. Devam edilsin mi?")) return;
    const catiDuvar = new Map();
    if (enUst && dolu) B.kirisler.forEach(function (k) { if (k.kat === D.kat) catiDuvar.set(aciklikAnahtari(k), { duvar: k.duvar, duvar_h: k.duvar_h }); });
    ["kolonlar", "kirisler", "dosemeler"].forEach(function (l) {
      B[l] = B[l].filter(function (x) { return x.kat !== D.kat; });
      B[l].filter(function (x) { return x.kat === alt; }).forEach(function (x) { B[l].push(Object.assign(kopya(x), { no: yeniNo(B[l]), kat: D.kat })); });
    });
    let korunan = 0;
    if (catiDuvar.size) {
      B.kirisler.forEach(function (k) {
        if (k.kat !== D.kat) return;
        const e = catiDuvar.get(aciklikAnahtari(k));
        if (!e) return;
        k.duvar = e.duvar == null ? null : e.duvar;
        if (e.duvar_h != null && e.duvar_h !== "") { k.duvar_h = e.duvar_h; korunan++; } else delete k.duvar_h;
      });
    }
    const parapet = altCatiydi ? parapetKaldir(alt) : 0;
    degisti();
    if (parapet) A.toast(parapetNotu(parapet));
    else if (korunan) A.toast("Çatı parapetleri korundu (" + korunan + " kiriş).");
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
        '<div class="bn-ust-grup bn-cikti" id="bn-cikti" role="group" aria-label="Proje ve çıktılar">' +
          '<button type="button" class="dugme kucuk" id="bn-proje-kaydet" title="Projeyi .matris dosyası olarak kaydet (bina, görünüm, araç kutusu yerleşimi)">💾 Kaydet</button>' +
          '<button type="button" class="dugme kucuk" id="bn-proje-ac" title="Proje (.matris) ya da bina JSON dosyası aç">📂 Aç</button>' +
          '<button type="button" class="dugme kucuk" data-cikti="rapor" title="Statik hesap raporu: önizleme, yazdır / PDF, HTML indir (çözüm yoksa önce çözer)">📄 Statik Rapor</button>' +
          '<button type="button" class="dugme kucuk" data-cikti="tablolar" title="Model, yük, analiz, tasarım ve metraj tabloları; düzenleme ve CSV">▦ Tablolar</button>' +
          '<button type="button" class="dugme kucuk" data-cikti="isi" title="Gerilme, iç kuvvet ve yer değiştirme ısı haritası (çözüm yoksa önce çözer)">🌡 Isı haritası</button>' +
          '<button type="button" class="dugme kucuk" data-cikti="ifc" title="IFC4 yapı modeli olarak dışa aktar">⬇ IFC</button></div>' +
      "</div>" +
      '<div class="bn-govde" id="bn-govde">' +
        '<div class="bn-arac" id="bn-arac" role="toolbar" aria-label="Araçlar" aria-orientation="vertical"></div>' +
        '<div class="bn-sahne-kutu" id="bn-sahne-kutu"><div class="bn-svg-kutu" id="bn-svg-kutu"><svg id="bn-svg" class="bn-svg" role="img" tabindex="0" aria-label="3B bina sahnesi (seçili eleman için Shift+F10: bağlam menüsü)" preserveAspectRatio="xMidYMid meet"></svg>' +
          '<div class="bn-sahne-ust" id="bn-sahne-ust"></div>' +
          '<div class="bn-sahne-dugmeler" role="toolbar" aria-label="Yerleşim">' +
            '<button type="button" class="bn-sd bn-sd-arac" id="bn-arac-ac" aria-pressed="false" title="Araç çubuğunu daralt / aç">☰</button>' +
            '<button type="button" class="bn-sd bn-sd-panel" id="bn-panel-ac" aria-pressed="false" title="Özellik panelini daralt / aç">▤</button>' +
            '<button type="button" class="bn-sd bn-sd-sonuc" id="bn-sonuc-yer" aria-pressed="false" title="Sonuçları sağ panele al">◨</button>' +
            '<button type="button" class="bn-sd bn-sd-tam" id="bn-tam" aria-pressed="false" title="Tam ekran (F)" aria-label="Tam ekran" aria-keyshortcuts="F">⛶</button></div>' +
          '<div class="bn-arac-katman" id="bn-arac-katman"></div>' +
          '<div class="bn-sahne-alt" id="bn-sahne-alt"><label class="bn-onay"><input type="checkbox" id="bn-tum-katlar"> Tüm katlara uygula</label>' +
            '<button type="button" class="dugme kucuk" id="bn-doldur">Döşemeleri doldur</button><button type="button" class="dugme kucuk" id="bn-kat-kopyala">Alt katı kopyala</button></div>' +
          "</div>" +
          '<div class="bn-dc-lejant" id="bn-dc-lejant" hidden></div>' +
          '<div id="bn-formul" class="bn-formul gizli"></div>' +
        "</div>" +
        '<details class="bn-panel" id="bn-panel" open><summary>Özellikler</summary><div class="bn-panel-sekmeler" id="bn-panel-sekmeler"></div><div class="bn-panel-icerik" id="bn-panel-icerik"></div></details>' +
        '<div class="bn-ayirac bn-panel-ayirac" id="bn-panel-ayirac" role="separator" aria-orientation="vertical" tabindex="0" aria-label="Özellik paneli genişliği" title="Sürükle: panel genişliği · çift tık: varsayılan"></div>' +
      "</div>" +
      '<div class="bn-ayirac bn-sonuc-ayirac" id="bn-sonuc-ayirac" role="separator" aria-orientation="vertical" tabindex="0" aria-label="Sonuç paneli genişliği" title="Sürükle: sonuç paneli genişliği · çift tık: varsayılan"></div>' +
      '<div class="bn-cekmece" id="bn-cekmece">' +
      '<button type="button" class="bn-cekmece-tutamak" id="bn-cekmece-tutamak" aria-label="Sonuç çekmecesi: dokun aç/kapat, sürükle yüksekliği ayarla" aria-expanded="false"><span aria-hidden="true"></span></button>' +
      '<div class="bn-durum" id="bn-durum"></div>' +
      '<div id="bn-uyarilar" class="bn-uyarilar" aria-live="polite"></div>' +
      '<div class="bn-hat-kutu"><div class="bn-hat" id="bn-hat"></div><button type="button" class="dugme ana bn-coz" id="bn-coz">Çöz ▶</button></div>' +
      '<div class="bn-ilerleme" id="bn-ilerleme" aria-live="polite" hidden></div>' +
      '<div id="bn-hata" class="bn-hata" aria-live="polite"></div>' +
      '<div class="bn-sonuc" id="bn-sonuc"></div>' +
      "</div>" +
      '<dialog id="bn-sihirbaz-dlg" class="bn-dlg"><form method="dialog" id="bn-sihirbaz-form"></form></dialog>' +
      '<dialog id="bn-json-dlg" class="bn-dlg"><h2>Bina JSON</h2><textarea id="bn-json-metin" class="girdi" rows="14" spellcheck="false" aria-label="Bina JSON"></textarea><div id="bn-json-hata"></div>' +
        '<div class="dugmeler"><button type="button" class="dugme ana" id="bn-json-uygula">JSON\'dan uygula</button><button type="button" class="dugme" id="bn-json-kopyala">Kopyala</button>' +
        '<button type="button" class="dugme" id="bn-json-indir">İndir</button><label class="dugme bn-dosya">Dosyadan yükle<input type="file" id="bn-json-dosya" accept=".json,application/json"></label>' +
        '<button type="button" class="dugme" id="bn-json-kapat">Kapat</button></div></dialog>';
    ["sablon", "sihirbaz", "json", "geri", "ileri", "katlar", "gorunum", "cikti", "proje-kaydet", "proje-ac", "arac-katman", "govde", "arac", "sahne-kutu", "svg-kutu", "sahne-alt", "tam", "arac-ac", "panel-ac", "sonuc-yer", "panel-ayirac", "sonuc-ayirac", "cekmece", "cekmece-tutamak", "svg", "sahne-ust", "tum-katlar", "doldur", "kat-kopyala", "formul", "panel", "panel-sekmeler", "panel-icerik",
      "durum", "uyarilar", "hat", "coz", "hata", "sonuc", "sihirbaz-dlg", "sihirbaz-form", "json-dlg", "json-metin", "json-hata", "json-uygula", "json-kopyala", "json-indir", "json-dosya", "json-kapat"].forEach(function (id) {
      ref[id.replace(/-([a-z])/g, function (_, c) { return c.toUpperCase(); })] = document.getElementById("bn-" + id);
    });
    if (window.innerWidth < 700) ref.panel.removeAttribute("open");
  }
  function panelAc() {
    if (D.panelKapali) { D.panelKapali = false; yerlesimUygula(); }
    ref.panel.open = true;
    if (window.innerWidth < 700 && !D.tamEkran) ref.panel.scrollIntoView({ block: "start", behavior: azHareket() ? "auto" : "smooth" });
  }
  let sonUyarilar = [];

  function yenile() {
    sonUyarilar = dogrula().uyari;
    ustCubukCiz();
    sahneCiz();
    panelCiz();
    durumCiz();
    hatCiz();
    if (ref.sonuc && sonEski && !ref.sonuc.querySelector(".bn-eski:not(.gizli)")) { const e = ref.sonuc.querySelector(".bn-eski"); if (e) e.classList.remove("gizli"); }
    secimDegistiMi();
    aracYenile();
  }
  function ustCubukCiz() {
    ref.katlar.innerHTML = '<span class="bn-etiket">Kat:</span>' + B.katlar.map(function (k) {
      return '<button type="button" class="bn-cip' + (k.no === D.kat ? " aktif" : "") + '" data-kat="' + k.no + '" aria-pressed="' + (k.no === D.kat) + '">' + kacis(k.ad) + "</button>";
    }).join("") + '<div class="bn-menu"><button type="button" class="bn-cip bn-cip-ekle" id="bn-kat-ekle" aria-haspopup="true">+Kat ▾</button>' +
      '<div class="bn-menu-liste gizli" id="bn-kat-menu"><button type="button" data-kat-islem="kopyala">Üsttekini kopyala</button><button type="button" data-kat-islem="bos">Boş kat</button><button type="button" data-kat-islem="sil">Son katı sil</button></div></div>';
    gorunumDugmeleri();
    // genel modelde aks–kat çizim araçları (Kolon, Kiriş, Döşeme) ve aks–kat düğmeleri (Döşemeleri doldur, Alt katı kopyala) gizli
    const s3 = s3Var();
    if (ref.doldur) ref.doldur.hidden = s3;
    if (ref.katKopyala) ref.katKopyala.hidden = s3;
    ref.arac.innerHTML = '<span class="bn-yuzen-tutamak" data-yuzen-tasi="arac" title="Araç kutusunu taşı" aria-hidden="true"></span>' + ARACLAR.filter(function (a) { return !s3 || ["kolon", "kiris", "doseme"].indexOf(a[0]) < 0; }).map(function (a) {
      return '<button type="button" class="bn-arac-d' + (D.arac === a[0] ? " aktif" : "") + '" data-arac="' + a[0] + '" aria-pressed="' + (D.arac === a[0]) + '" title="' + kacis(a[2] + " (" + a[3] + ")") + '"><span class="bn-arac-sim" aria-hidden="true">' + a[1] + '</span><span class="bn-arac-ad">' + kacis(a[2]) + "</span></button>";
    }).join("") + '<button type="button" class="bn-arac-d' + (D.panelSekme === "kutuphane" ? " aktif" : "") + '" data-arac="kutuphane" title="Kütüphane"><span class="bn-arac-sim" aria-hidden="true">📚</span><span class="bn-arac-ad">Kütüphane</span></button>';
    ref.tumKatlar.checked = D.tumKatlar;
    ref.geri.disabled = !gecmis.geri.length; ref.ileri.disabled = !gecmis.ileri.length;
    const ipucu = { sec: "Nesneye dokun: seç (ikinci dokunma çoklu seçim); " + (modul("MatrisBilgi") ? "sağ tık ya da uzun bas: eleman bilgisi ve komutlar" : "uzun bas: özellikler") + ". Sürükle: döndür; tekerlek/iki parmak: yakınlaştır.",
      kolon: "Etkin katın aks kesişimine (○) dokun: kolon ekle/kaldır.", kiris: "İki kesişime art arda dokun ya da sürükle: kiriş. Arada kolon yoksa sürekli kiriş.",
      doseme: "Hücredeki + işaretine dokun: döşeme. Kırmızı kesikli hücrenin bir kenarında kiriş yok.", duvar: "Kirişe (genel modelde kiriş/bağ çubuğuna) dokun: duvar ekle/kaldır (türü panelde).", sil: "Nesneye dokun: sil." };
    const kipM = kipIpucu();
    ref.sahneUst.innerHTML = '<span class="bn-ipucu">' + kacis(kipM != null ? kipM : D.kat === 0 ? TEMEL_TIP_AD[B.temeller.tip] + " temel. Plan görünümü temel planını gösterir; temele dokun: Bina / temel ayarları." : ipucu[D.arac] || "") + "</span>" + (D.firca ? '<span class="bn-firca">Fırça: ' + kacis(D.firca) + ' <button type="button" class="bn-firca-kapat" id="bn-firca-kapat" aria-label="Fırçayı bırak">✕</button></span>' : "");
  }
  function gorunumDugmeleri() {
    const g = kamera ? kamera.gorunum : "3b";
    const odak = document.activeElement && document.activeElement.id === "bn-duzlem";
    ref.gorunum.innerHTML = '<span class="bn-etiket">Görünüm:</span>' + Object.keys(GORUNUM_AD).map(function (k) {
      return '<button type="button" class="bn-cip' + (g === k ? " aktif" : "") + '" data-gorunum="' + k + '" aria-pressed="' + (g === k) + '">' + GORUNUM_AD[k] + "</button>";
    }).join("") + '<button type="button" class="bn-cip bn-ikon" data-gorunum="sifirla" title="Yakınlaştırmayı sıfırla" aria-label="Yakınlaştırmayı sıfırla">⟲</button>' + duzlemSecici(g);
    if (odak) { const s = document.getElementById("bn-duzlem"); if (s) s.focus({ preventScroll: true }); }
  }
  // Düzlem seçici (§19.3): plan / 3B'de Z aksı (kat dışı saçak, mahya, kren dahil), önden cephede Y aksı, yandan kesitte X aksı. PgUp / PgDn de gezer.
  function duzlemSecici(g) {
    if (!B) return "";
    const ag = aksGorunumu();
    let tur, liste, secili, etiket;
    if (ag.tur === "cephe") {
      tur = ag.x != null ? "x" : "y"; secili = ag[tur];
      liste = (B.akslar[tur] || []).map(function (a) { return [String(a.ad), (tur === "x" ? "X " : "Y ") + a.ad + " (" + f2(+a.konum) + " m)"]; });
      etiket = tur === "x" ? "Kesit aksı (X)" : "Cephe aksı (Y)";
    } else {
      tur = "z"; secili = ag.z;
      liste = zAkslari().map(function (a) {
        const k = a.kat != null ? B.katlar.filter(function (x) { return x.no === +a.kat; })[0] : null;
        const kotAd = window.MatrisAks && window.MatrisAks.kotAdi ? window.MatrisAks.kotAdi(+a.konum) : null;
        return [String(a.ad), (String(a.ad) === kotAd ? String(a.ad).replace(".", ",") : a.ad + " " + ((+a.konum >= 0 ? "+" : "") + f2(+a.konum))) + (k && k.ad !== a.ad && k.ad !== kotAd ? " · " + k.ad : "")];
      });
      etiket = g === "plan" ? "Plan düzlemi (Z aksı)" : "Etkin Z aksı";
    }
    if (!liste.length) return "";
    return '<label class="bn-duzlem" title="' + kacis(etiket + " — PgUp / PgDn ile komşu aksa geçilir") + '"><span class="bn-etiket">Düzlem:</span>' +
      '<select class="girdi bn-duzlem-sec" id="bn-duzlem" data-duzlem-tur="' + tur + '" aria-label="' + kacis(etiket) + '">' + secenekler(liste, secili) + "</select></label>";
  }
  function durumCiz() {
    const nk = B.kolonlar.length, nr = B.kirisler.length, nd = B.dosemeler.length, nkat = B.katlar.length - 1;
    // genel model (surum 3): çubuk / panel sayıları önce; aks–kat elemanları yalnız varsa
    const s3 = s3Var() || +B.surum >= 3 ? (B.cubuklar || []).length + " çubuk · " + (B.paneller || []).length + " panel · " + (nk + nr + nd ? nk + " kolon · " + nr + " kiriş · " + nd + " döşeme · " : "") : nk + " kolon · " + nr + " kiriş · " + nd + " döşeme · ";
    const nz = zAkslari().length;
    ref.durum.textContent = s3 + nkat + " kat · " + (SON && !sonEski && SON.veri.ag ? SON.veri.ag.sd_sayisi + " SD" : sdTahmini() + " SD (tahmin)") +
      (B.akslar.x.length && B.akslar.y.length ? " · " + B.akslar.x.length + "×" + B.akslar.y.length + (s3Var() || nz > B.katlar.length ? "×" + nz : "") + " aks" : "");
    const u = sonUyarilar;
    ref.uyarilar.innerHTML = u.length ? '<div class="bn-uyari-kutu"><strong>⚠ ' + u.length + " uyarı:</strong> " + u.slice(0, 4).map(function (x) { return '<span class="bn-uyari-satir" data-uyari-kat="' + x.kat + '">' + kacis(x.metin) + "</span>"; }).join(" ") + (u.length > 4 ? " …" : "") + "</div>" : "";
  }
  // ---------- Özellik paneli ----------
  function panelCiz() {
    const sekmeler = [["nesne", D.secim.length ? "Seçili (" + D.secim.length + ")" : "Nesne"], ["akslar", "Akslar"], ["bina", "Bina / temel"], ["yukler", "Yükler"], ["deprem", "Deprem"], ["kutuphane", "Kütüphane"]];
    ref.panelSekmeler.innerHTML = sekmeler.map(function (s) { return '<button type="button" class="bn-psek' + (D.panelSekme === s[0] ? " aktif" : "") + '" data-psek="' + s[0] + '">' + kacis(s[1]) + "</button>"; }).join("");
    let h = "";
    if (D.panelSekme === "nesne") h = nesnePaneli();
    else if (D.panelSekme === "akslar") h = aksPaneli();
    else if (D.panelSekme === "bina") h = binaPaneli();
    else if (D.panelSekme === "yukler") h = yukPaneli();
    else if (D.panelSekme === "deprem") h = depremPaneli();
    else h = kutuphanePaneli();
    ref.panelIcerik.innerHTML = h;
    if (D.panelSekme === "deprem") spektrumOnizle(true);
  }
  // ---------- Yükler sekmesi (yük durumları G Q S W E, kombinasyon kümesi) ----------
  function yukPaneli() {
    const yd = B.yuk_durumlari, kume = KUT.kombinasyon_kumeleri;
    const kumeListe = Array.isArray(kume) ? kume.map(function (k) { return [k, { ts500: "TS 500 + TBDY 4.4.4", cythye_ydkt: "ÇYTHYE YDKT + TBDY 9.2.5", cythye_gkt: "ÇYTHYE GKT + TBDY 9.2.5" }[k] || k]; })
      : Object.keys(kume || {}).map(function (k) { return [k, kume[k].ad || k]; });
    const anahtar = function (k, ek, ipucu) {
      return '<div class="bn-anahtar"><label class="bn-onay"><input type="checkbox" data-yd="' + k + '" data-yd-alan="acik"' + (yd[k].acik ? " checked" : "") + (k === "G" ? " disabled" : "") + "> <b>" + kacis(YUK_DURUM_AD[k]) + "</b></label>" +
        (ipucu ? '<span class="not">' + kacis(ipucu) + "</span>" : "") + (ek || "") + "</div>";
    };
    let h = '<h3 class="bn-pbaslik">Yük durumları (her biri ayrı çözülen yük deseni)</h3>';
    h += anahtar("G", "", "Öz ağırlık, döşeme kaplaması, duvarlar (TS 498:2021 md. 5–9).");
    h += anahtar("Q", "", "Kullanım sınıfından (Çizelge 6) ya da döşeme q değerinden.");
    h += anahtar("S", '<div class="bn-uc bn-anahtar-alan"' + (yd.S.acik ? "" : ' style="display:none"') + ">" +
      alanH("Kar bölgesi (Ek 2)", '<select class="girdi" data-yd="S" data-yd-alan="bolge">' + secenekler([1, 2, 3, 4, 5, 6, 7, 8, 9].map(function (b) { return [b, "Bölge " + b]; }), yd.S.bolge) + "</select>") +
      alanH("Rakım (m)", '<input class="girdi" inputmode="numeric" data-yd="S" data-yd-alan="rakim" value="' + kacis(yd.S.rakim) + '">') +
      alanH("μ (çatı şekil katsayısı)", '<input class="girdi" inputmode="decimal" data-yd="S" data-yd-alan="mu" value="' + kacis(yd.S.mu) + '">') + "</div>",
      "Çatı döşemelerine s = μ·S_k; S_k TS 498:2021 md. 11 Çizelge 3 (bölge × rakım).");
    h += anahtar("W", '<div class="bn-iki bn-anahtar-alan"' + (yd.W.acik ? "" : ' style="display:none"') + ">" +
      alanH("C (Çizelge 5; kapalı yapı 1,2)", '<input class="girdi" inputmode="decimal" data-yd="W" data-yd-alan="C" value="' + kacis(yd.W.C) + '">') +
      '<p class="not">q yüksekliğe göre Çizelge 4 (0,5 / 0,8 / 1,1 / 1,3 kN/m²); W = C·q·A kat seviyelerine, ±X ve ±Y.</p></div>', "TS 498:2021 md. 14; dört doğrultu (W+X, W−X, W+Y, W−Y).");
    h += anahtar("E", "", "TBDY 2018 eşdeğer deprem yükü (md. 4.7): EX±, EY± (±%5 dışmerkezlik) ve EZ ≈ (2/3)·S_DS·G. Girdiler “Deprem” sekmesinde.");
    h += '<h3 class="bn-pbaslik">Kombinasyonlar</h3>' + alanH("Kombinasyon kümesi", '<select class="girdi" data-bina="kombinasyon_kumesi">' + secenekler(kumeListe.length ? kumeListe : [["ts500", "TS 500 + TBDY 4.4.4"], ["cythye_ydkt", "ÇYTHYE YDKT + TBDY 9.2.5"], ["cythye_gkt", "ÇYTHYE GKT + TBDY 9.2.5"]], B.kombinasyon_kumesi) + "</select>");
    const acik = Object.keys(yd).filter(function (k) { return yd[k].acik; });
    h += '<p class="not">Açık durumlar: <b>' + kacis(acik.join(" ")) + "</b>. Kapalı durumu içeren kombinasyonlar tabloda “uygulanmadı” olarak listelenir; çözümde yalnız açık durumlar hesaplanır. Deprem kombinasyonları TBDY Denk. (4.11)/(4.12) ile ±EX ± 0,3EY (ve tersi) doğrultu birleştirmeleriyle açılır.</p>";
    return h;
  }
  // ---------- Deprem sekmesi (TBDY 2018 girdileri + canlı spektrum önizlemesi) ----------
  function depremPaneli() {
    const dp = B.deprem, ts = tasiyiciBul(dp.tasiyici), celik = B.sistem === "celik";
    const tasList = tasiyiciListesi().filter(function (t) { return !t.sistem || t.sistem === B.sistem; });
    const liste = tasList.length ? tasList : tasiyiciListesi();
    const g = function (ad, etiket, deger, ek) { return alanH(etiket, '<input class="girdi" inputmode="decimal" data-dep="' + ad + '" value="' + kacis(deger) + '"' + (ek || "") + ">"); };
    let h = '<h3 class="bn-pbaslik">Deprem yer hareketi (DD-2, tasarım düzeyi)</h3>' +
      '<p class="not">S_S ve S_1 harita spektral ivme katsayıları AFAD Türkiye Deprem Tehlike Haritası’ndan (tdth.afad.gov.tr) koordinatla okunur (TBDY 2018 md. 2.3.2); DD-3 değerleri göreli kat ötelemesi λ oranı içindir (md. 4.9.1.4).</p>' +
      '<div class="bn-iki">' + g("SS", "S_S (DD-2)", dp.SS) + g("S1", "S_1 (DD-2)", dp.S1) + "</div>" +
      '<div class="bn-iki">' + g("SS_DD3", "S_S (DD-3)", dp.SS_DD3) + g("S1_DD3", "S_1 (DD-3)", dp.S1_DD3) + "</div>" +
      '<div class="bn-iki">' + alanH("Yerel zemin sınıfı (Tablo 16.1)", '<select class="girdi" data-dep="zemin_sinifi">' + secenekler(TBDY.zemin.map(function (z) { return [z, z + (z === "ZA" ? " — sert kaya" : z === "ZB" ? " — kaya" : z === "ZC" ? " — çok sıkı kum / sert kil" : z === "ZD" ? " — orta sıkı kum / katı kil" : " — gevşek kum / yumuşak kil")]; }), dp.zemin_sinifi) + "</select>") +
      alanH("Bina kullanım sınıfı (Tablo 3.1)", '<select class="girdi" data-dep="BKS">' + secenekler(TBDY.BKS, dp.BKS) + "</select>") + "</div>" +
      '<h3 class="bn-pbaslik">Taşıyıcı sistem (Tablo 4.1)</h3>' +
      alanH("Taşıyıcı sistem → R, D", '<select class="girdi" data-dep="tasiyici">' + secenekler(liste.map(function (t) { return [t.ad, t.etiket + " (R = " + t.R + ", D = " + t.D + ")"]; }), dp.tasiyici) + "</select>") +
      '<div class="bn-uc">' + g("R", "R (Tablo 4.1)", dp.R, ts ? " readonly" : "") + g("D", "D (Tablo 4.1)", dp.D, ts ? " readonly" : "") + alanH("I (Tablo 3.1)", '<input class="girdi" value="' + kacis(dp.I) + '" readonly>') + "</div>" +
      (ts ? '<p class="not">İzin verilen BYS: ' + kacis(ts.BYS_izin) + (celik ? "; TBDY Bölüm 9" : "; TBDY Bölüm 7") + ".</p>" : "") +
      '<div class="bn-iki">' + alanH("Hareketli yük katılım n (Tablo 4.3)", '<select class="girdi" data-dep="n">' + secenekler(TBDY.n, dp.n) + "</select>") +
        alanH("C_t (Denk. 4.27)", '<select class="girdi" data-dep="Ct">' + secenekler(TBDY.Ct, dp.Ct) + "</select>") + "</div>" +
      '<div class="bn-iki">' + alanH("Hakim periyot T_p", '<select class="girdi" data-dep="periyot">' + secenekler([["ampirik", "Ampirik T_pA = C_t·H_N^(3/4) (4.7.3.3)"], ["rayleigh", "Rayleigh (Denk. 4.26), ≤ 1,4·T_pA"]], dp.periyot) + "</select>") +
        alanH("Diyafram", '<select class="girdi" data-dep="diyafram">' + secenekler([["rijit", "Rijit (efendi–köle)"], ["esnek", "Esnek (kat kuvveti düğümlere kütleyle)"]], dp.diyafram) + "</select>") + "</div>" +
      '<div class="bn-iki">' + g("dismerkezlik", "Ek dışmerkezlik (4.5.10.2; 0,05)", dp.dismerkezlik) +
        alanH("Dolgu duvar (4.9.1.3)", '<select class="girdi" data-dep="dolgu">' + secenekler([["bitisik", "Çerçeveye bitişik gevrek dolgu (0,008κ)"], ["esnek", "Esnek derzli / bağımsız (0,016κ)"]], dp.dolgu) + "</select>") + "</div>" +
      '<label class="bn-onay"><input type="checkbox" data-analiz="catlamis_rijitlik"' + (B.analiz.catlamis_rijitlik ? " checked" : "") + "> Çatlamış (etkin) kesit rijitliği — TBDY 4.5.8, Tablo 4.2: kiriş 0,35·EI, kolon 0,70·EI. Betonarmede zorunlu (4.5.8.1); iki K ile çözülür: deprem birleşimleri (E ve onlara giren G, Q, S) çatlamış, deprem dışı birleşimler (1,4G + 1,6Q, rüzgâr, servis) brüt kesitle (4.5.8.3)</label>" +
      (!B.analiz.catlamis_rijitlik && B.sistem !== "celik" ? '<p class="bn-uyari-kutu">Çatlamış kesit kapalı: TBDY 4.5.8.1’e aykırı — deprem hesabı brüt kesitle yapılır (periyot kısa, öteleme küçük çıkar).</p>' : "") +
      (B.yuk_durumlari.E.acik ? "" : '<p class="bn-uyari-kutu">E yük durumu kapalı: deprem çözümde hesaba girmez. “Yükler” sekmesinden açın.</p>') +
      '<h3 class="bn-pbaslik">Spektrum önizlemesi</h3><div class="bn-spek" id="bn-spek-on"><p class="not">Hesaplanıyor…</p></div><div id="bn-spek-tablo"></div>';
    return h;
  }
  // Canlı önizleme: 400 ms gecikmeyle motor `bina_deprem` (çözümsüz hızlı yol); gelene kadar yerel tahmin
  function spektrumOnizle(hemen) {
    clearTimeout(onizlemeZ);
    const kap = document.getElementById("bn-spek-on");
    if (!kap) return;
    const sira = ++onizlemeSira;
    const yerel = function () { try { ONIZLEME = { deprem: depremTahmini(), kaynak: "tahmin" }; } catch (e) { ONIZLEME = null; } onizlemeCiz(); };
    if (hemen) yerel();
    onizlemeZ = setTimeout(function () {
      onizlemeZ = 0;
      if (!hemen) yerel();
      A.motorIstegi({ islem: "bina_deprem", girdi: { bina: kopya(B) } }).then(function (y) {
        if (sira !== onizlemeSira) return;
        if (!y || y.hata || !y.deprem) { if (y && y.hata) onizlemeNot(y.hata); return; }
        ONIZLEME = { deprem: y.deprem, kaynak: "motor" };
        onizlemeCiz();
      }, function () { /* motor yok: yerel tahmin kalır */ });
    }, 400);
  }
  function onizlemeNot(m) { const t = document.getElementById("bn-spek-tablo"); if (t) t.innerHTML += '<p class="not">Motor: ' + kacis(m) + "</p>"; }
  function onizlemeCiz() {
    const kap = document.getElementById("bn-spek-on"), tb = document.getElementById("bn-spek-tablo");
    if (!kap) return;
    if (!ONIZLEME || !ONIZLEME.deprem) { kap.innerHTML = '<p class="not">Önizleme hesaplanamadı.</p>'; return; }
    const d = ONIZLEME.deprem, W = Math.max(240, (kap.clientWidth || 280) - 8);
    kap.innerHTML = spektrumSvg(d, W, Math.round(W * 0.62), true) + '<p class="not">' + (ONIZLEME.kaynak === "motor" ? "Motor (bina_deprem)" : "Yerel tahmin (motor yanıtı bekleniyor / yok)") +
      ": S_DS = " + f2(d.SDS) + ", S_D1 = " + f2(d.SD1) + ", T_A = " + f2(d.TA) + " s, T_B = " + f2(d.TB) + " s, T_p = " + f2(d.Tp) + " s, S_aR(T_p) = " + fmt(d.SaR, 3) + " g</p>";
    if (tb) tb.innerHTML = depremMiniTablo(d);
  }
  function depremMiniTablo(d) {
    const kat = (d.katlar || []).slice().sort(function (a, b) { return b.kat - a.kat; });
    return '<div class="bn-kart"><b>V_tE = ' + f1(d.VtE) + " kN</b> (min " + f1(d.VtE_min) + " kN; Denk. 4.19) · ΔF_N = " + f2(d.dFN) + " kN · H_N = " + f2(d.HN) + " m · DTS " + kacis(d.DTS) + " · BYS " + kacis(d.BYS) + "</div>" +
      tabloH(["Kat", "H (m)", "w_i (kN)", "F_i (kN)", "V_i (kN)"], kat.map(function (k) { return [katAd(k.kat), f2(k.H), f1(k.w_i), f1(k.F_x), f1(k.V_x)]; }), "bn-mini");
  }
  // Spektrum SVG: S_ae(T) ve S_aR(T) eğrileri, T_A / T_B kesikli, T_p işareti (mini ve büyük)
  function spektrumSvg(d, W, H, mini) {
    const spek = d.spektrum || [], pl = mini ? 34 : 46, pr = 12, pu = mini ? 12 : 18, pa = mini ? 26 : 34;
    if (!spek.length) return '<p class="not">Spektrum verisi yok.</p>';
    const Tmax = Math.max(1, spek[spek.length - 1][0]), Smax = Math.max.apply(null, spek.map(function (p) { return p[1]; })) * 1.08 || 1;
    const X = function (T) { return pl + T / Tmax * (W - pl - pr); }, Y = function (s) { return H - pa - s / Smax * (H - pa - pu); };
    let s = '<path class="se-eksen" d="M' + pt(pl, Y(0)) + " L" + pt(W - pr, Y(0)) + " M" + pt(pl, Y(0)) + " L" + pt(pl, pu) + '"/>';
    for (let T = 0; T <= Tmax + 1e-9; T += Tmax > 2 ? 0.5 : 0.25) s += '<path class="bn-spek-izgara" d="M' + pt(X(T), Y(0)) + " L" + pt(X(T), Y(0) + 4) + '"/>' + metinSvg(X(T), Y(0) + 15, f2(T).replace(",00", ""), "bn-spek-t", "middle");
    const adimS = Smax > 1.2 ? 0.5 : 0.25;
    for (let v = 0; v <= Smax + 1e-9; v += adimS) s += '<path class="bn-spek-izgara" d="M' + pt(pl - 4, Y(v)) + " L" + pt(W - pr, Y(v)) + '"/>' + metinSvg(pl - 6, Y(v) + 4, f2(v), "bn-spek-t", "end");
    const yol = function (i) { let d2 = ""; spek.forEach(function (p, j) { d2 += (j ? " L" : "M") + pt(X(p[0]), Y(p[i])); }); return d2; };
    s += '<path class="bn-spek-sae" d="' + yol(1) + '"/><path class="bn-spek-sar" d="' + yol(2) + '"/>';
    // köşe periyotları: kesikli çizgi; etiketler yalnız büyük çizimde (mini çizimde altındaki notta yazılır)
    [["TA", d.TA, "T_A"], ["TB", d.TB, "T_B"]].forEach(function (k, i) {
      if (!(k[1] > 0)) return;
      s += '<path class="bn-spek-kose" d="M' + pt(X(k[1]), Y(0)) + " L" + pt(X(k[1]), pu) + '"/>' + (mini ? "" : metinSvg(X(k[1]) + 3, pu + 10 + 12 * i, k[2] + " = " + f2(k[1]) + " s", "bn-spek-t", "start"));
    });
    if (d.Tp > 0) {
      const sae = d.Sae_Tp != null ? d.Sae_Tp : tbdySae(d.Tp, { TA: d.TA, TB: d.TB, TL: d.TL || 6, SDS: d.SDS, SD1: d.SD1 });
      s += '<path class="bn-spek-tp" d="M' + pt(X(d.Tp), Y(0)) + " L" + pt(X(d.Tp), Y(sae)) + '"/><circle class="bn-spek-tp-n" cx="' + r1(X(d.Tp)) + '" cy="' + r1(Y(sae)) + '" r="4"/>' +
        '<circle class="bn-spek-tp-n bn-spek-tp-r" cx="' + r1(X(d.Tp)) + '" cy="' + r1(Y(d.SaR || 0)) + '" r="4"/>' +
        metinSvg(X(d.Tp) + 8, Y(sae) + (mini ? 16 : 18), mini ? "T_p = " + f2(d.Tp) + " s" : "T_p = " + f2(d.Tp) + " s · S_ae(T_p) = " + f2(sae) + " g", "bn-spek-t bn-spek-vurgu", "start") +
        (mini ? "" : metinSvg(X(d.Tp) + 8, Y(d.SaR || 0) + 14, "S_aR = S_ae/R_a = " + fmt(d.SaR, 3) + " g", "bn-spek-t bn-spek-vurgu", "start"));
    }
    if (!mini) {
      s += '<g class="bn-spek-leg">' + '<path class="bn-spek-sae" d="M' + pt(W - pr - 120, pu + 6) + " L" + pt(W - pr - 96, pu + 6) + '"/>' + metinSvg(W - pr - 92, pu + 10, "S_ae(T) elastik", "bn-spek-t", "start") +
        '<path class="bn-spek-sar" d="M' + pt(W - pr - 120, pu + 20) + " L" + pt(W - pr - 96, pu + 20) + '"/>' + metinSvg(W - pr - 92, pu + 24, "S_aR(T) = S_ae/R_a", "bn-spek-t", "start") + "</g>";
    }
    s += metinSvg(W / 2, H - 4, "T (s)", "bn-spek-t", "middle") + metinSvg(mini ? 4 : 10, pu + 6, "g", "bn-spek-t", "start");
    return '<svg class="se-svg bn-spek-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Tasarım spektrumu S_ae ve S_aR"><title>S_DS = ' + kacis(f2(d.SDS)) + ", S_D1 = " + kacis(f2(d.SD1)) + "</title>" + s + "</svg>";
  }
  function kesitSecenekleri(tur, secili) {
    const l = Object.keys(B.kesitler).map(function (k) { const o = kesitOz(k); return [k, k + (o ? " (" + kesitEtiketi(o) + ")" : "")]; });
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
    } else if (s0.tur === "cubuk" || s0.tur === "panel" || s0.tur === "mesnet" || s0.tur === "dugum") {
      h += s3Paneli(s0.tur, n, cok);
      return h + '<div class="dugmeler"><button type="button" class="dugme kucuk" id="bn-ayni-tur">Aynı türden tümünü seç</button><button type="button" class="dugme kucuk" id="bn-secim-sil">Seçileni sil</button></div>';
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
  // ---------- Genel model (surum 3) özellik paneli: çubuk, panel, mesnet, bölme/kesişim düğümü ----------
  function refMetin(r) {
    if (r == null) return "—";
    if (typeof r === "number") return "D" + r;
    if (r.dugum != null) { const d = nesneBul("dugum", +r.dugum); return (d && d.tur === "bolme" ? "bölme " : d && d.tur === "kesisim" ? "kesişim " : "düğüm ") + r.dugum + (d && d.ad ? " (" + d.ad + ")" : ""); }
    if (Array.isArray(r.aks)) return (r.sistem ? r.sistem + ": " : "") + r.aks.join("") + " / " + (r.z != null ? r.z : r.kat != null ? zAksiAdi(+r.kat) : "?");
    if (r.X != null) return "(" + f2(+r.X) + "; " + f2(+r.Y) + "; " + f2(+r.Z) + ")";
    return JSON.stringify(r);
  }
  const PANEL_TURLERI = [["doseme", "Döşeme"], ["cati", "Çatı"], ["cephe", "Cephe"]];
  const DUVARLI_CUBUK = ["kiris", "bag", "diger"];     // duvar yükü taşıyabilen çubuk türleri (motor çubuk.duvar, duvar_h)
  function duvarSecenekleri() {
    const l = [["", "Duvar yok"]].concat(Object.keys(B.duvarlar || {}).map(function (k) { const kk = B.duvarlar[k].kutuphane || k; const kt = (KUT.duvarlar || []).filter(function (x) { return x.ad === kk; })[0]; return [k, (kt ? kt.etiket : kk) + " (" + f2(duvarW(k)) + " kN/m²)"]; }));
    if (Object.keys(B.duvarlar || {}).length) return l;
    // modelde duvar türü yok: kütüphanenin varsayılan tuğla duvarı eklenir (ad ve birim ağırlık bir kez)
    const v = (KUT.duvarlar || []).filter(function (x) { return x.ad === "tugla-delikli-19"; })[0];
    return l.concat([["__varsayilan", "Duvar ekle: " + (v ? v.etiket + " (" + f2(v.w) + " kN/m²)" : "delikli tuğla 19 cm")]]);
  }
  const DAGITIM_3 = [["iki", "İki doğrultulu (açıortay)"], ["tek-13", "Tek doğrultulu (1–3 kenarları taşır)"], ["tek-24", "Tek doğrultulu (2–4 kenarları taşır)"], ["yok", "Dağıtma (yalnız kütle)"]];
  const SERBEST_ADI = { N: "N", Vy: "Vy", Vz: "Vz", T: "T", My: "My", Mz: "Mz" };
  function s3Paneli(tur, n, cok) {
    let h = "";
    if (tur === "cubuk") {
      const Pi = refP(n.i), Pj = refP(n.j), L = Pi && Pj ? Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1], Pj[2] - Pi[2]) : null;
      const egim = Pi && Pj ? Math.atan2(Pj[2] - Pi[2], Math.hypot(Pj[0] - Pi[0], Pj[1] - Pi[1])) * 180 / Math.PI : null;
      const turAd = (CUBUK_TURLERI.filter(function (t) { return t[0] === (n.tur || "diger"); })[0] || ["", "Çubuk"])[1];
      h += '<h3 class="bn-pbaslik">' + kacis(turAd) + " C" + n.no + (L != null ? " · L = " + f2(L) + " m" : "") + (egim != null && Math.abs(egim) > 0.05 && Math.abs(Math.abs(egim) - 90) > 0.05 ? " · eğim " + f1(egim) + "°" : "") + "</h3>" + cok;
      h += '<p class="not">i: ' + kacis(refMetin(n.i)) + " → j: " + kacis(refMetin(n.j)) + "</p>";
      h += '<div class="bn-iki">' + alanH("Tür", '<select class="girdi" data-oz3="tur">' + secenekler(CUBUK_TURLERI, n.tur || "diger") + "</select>") +
        alanH("Kesit", '<select class="girdi" data-oz3="kesit">' + secenekler([["", "— (kesit yok)"]].concat(Object.keys(B.kesitler).map(function (k) { const o = kesitOz(k), t = B.kesitler[k] || {}; return [k, k + (t.profil || t.tip === "vute" ? " (" + (o ? kesitEtiketi(o) : t.profil || t.tip) + ")" : "")]; })).concat([["__yeni", "Yeni kesit…"]]), n.kesit || "") + "</select>") + "</div>";
      h += '<div class="bn-iki">' + alanH("Yerel eksen açısı (°)", '<input class="girdi" inputmode="decimal" data-oz3="aci" value="' + kacis(n.aci != null ? n.aci : 0) + '">') +
        alanH("Grup", '<input class="girdi" data-oz3="grup" value="' + kacis(n.grup || "") + '">') + "</div>";
      const K = Array.isArray(n.K) ? n.K : [null, null];
      h += '<div class="bn-iki">' + alanH("Lb (m; boş = otomatik)", '<input class="girdi" inputmode="decimal" data-oz3="Lb" value="' + kacis(n.Lb != null ? n.Lb : "") + '">') +
        alanH("K güçlü / zayıf (boş = 1)", '<input class="girdi" data-oz3="K" value="' + kacis(K[0] != null ? K.join(" ") : "") + '" placeholder="1 1">') + "</div>";
      h += '<label class="bn-onay"><input type="checkbox" data-oz3="yalniz_cekme"' + (n.yalniz_cekme ? " checked" : "") + "> Yalnız çekme (basınçta devre dışı)</label>";
      const sb = function (u) { const l = n.serbest && n.serbest[u] || []; return l.length ? l.map(function (x) { return SERBEST_ADI[x] || x; }).join(", ") : "—"; };
      h += '<p class="not">Uç serbestlikleri: i: ' + kacis(sb("i")) + " · j: " + kacis(sb("j")) + ' <button type="button" class="dugme kucuk" data-s3-komut="mafsal">Mafsal…</button></p>';
      if (DUVARLI_CUBUK.indexOf(n.tur || "diger") >= 0) {
        h += '<div class="bn-iki">' + alanH("Duvar (çubuk üstünde)", '<select class="girdi" data-oz3="duvar">' + secenekler(duvarSecenekleri(), n.duvar || "") + "</select>") +
          (n.duvar ? alanH("Duvar yüksekliği (m; boş = kat yüksekliği − kesit)", '<input class="girdi" inputmode="decimal" data-oz3="duvar_h" value="' + kacis(n.duvar_h != null ? n.duvar_h : "") + '">') : "") + "</div>";
      }
      if (n.kaynak && n.kaynak.uretec != null) {
        const u = (B.uretecler || []).filter(function (x) { return +x.no === +n.kaynak.uretec; })[0];
        h += '<p class="not">Üreteç ' + kacis(n.kaynak.uretec) + (u ? " (" + kacis(u.tur) + ")" : "") + ' ile üretildi. <button type="button" class="dugme kucuk" data-s3-uretec-sil="' + kacis(n.kaynak.uretec) + '">Üreteci ve ürettiklerini sil</button></p>';
      }
      if (n.kaynak && n.kaynak.aks_kat) h += '<p class="not">Aks–kat ' + kacis(n.kaynak.aks_kat) + " " + kacis(n.kaynak.no) + " elemanından genelleştirildi.</p>";
      if (n.kesit) h += kesitKarti(n.kesit);
    } else if (tur === "panel") {
      h += '<h3 class="bn-pbaslik">Panel P' + n.no + " · " + kacis((PANEL_TURLERI.filter(function (t) { return t[0] === (n.tur || "doseme"); })[0] || ["", "Panel"])[1]) + "</h3>" + cok;
      h += '<p class="not">Köşeler: ' + kacis(n.kose.map(refMetin).join(" → ")) + "</p>";
      h += '<div class="bn-iki">' + alanH("Tür", '<select class="girdi" data-oz3="tur">' + secenekler(PANEL_TURLERI, n.tur || "doseme") + "</select>") +
        alanH("Kalınlık (m; 0 = sac kaplama)", '<input class="girdi" inputmode="decimal" data-oz3="kalinlik" value="' + kacis(n.kalinlik != null ? n.kalinlik : 0) + '">') + "</div>";
      h += '<div class="bn-iki">' + alanH("Ek sabit yük g (kN/m², yüzeye)", '<input class="girdi" inputmode="decimal" data-oz3="g" value="' + kacis(n.g != null ? n.g : "") + '">') +
        alanH("Hareketli q (kN/m², izdüşüme)", '<input class="girdi" inputmode="decimal" data-oz3="q" value="' + kacis(n.q != null ? n.q : "") + '">') + "</div>";
      h += alanH("Kullanım sınıfı (TS 498)", '<select class="girdi" data-oz3="kullanim">' + secenekler([["", "—"]].concat((KUT.kullanim_siniflari || []).map(function (k) { return [k.ad, k.etiket + " — q = " + f1(k.q) + " kN/m²"]; })), n.kullanim || "") + "</select>");
      h += alanH("Yük dağıtımı", '<select class="girdi" data-oz3="dagitim">' + secenekler(DAGITIM_3, n.dagitim || "iki") + "</select>");
      h += '<label class="bn-onay"><input type="checkbox" data-oz3="kar"' + (n.kar ? " checked" : "") + "> Kar yükü (S; eğimden μ₁)</label>";
    } else if (tur === "mesnet") {
      h += '<h3 class="bn-pbaslik">Mesnet ' + D.secim[0].no + "</h3>" + cok + '<p class="not">Düğüm: ' + kacis(refMetin(n.dugum)) + "</p>";
      h += '<div class="bn-mesnet-izin">' + ["ux", "uy", "uz", "rx", "ry", "rz"].map(function (k) { return '<label class="bn-onay"><input type="checkbox" data-oz3="' + k + '"' + (n[k] ? " checked" : "") + "> " + k + "</label>"; }).join("") + "</div>";
      h += '<p class="not">İşaretli serbestlik tutulur (u: öteleme, r: dönme; bina eksenleri X, Y, Z).</p>';
    } else {
      h += '<h3 class="bn-pbaslik">' + (n.tur === "bolme" ? "Bölme" : n.tur === "kesisim" ? "Kesişim" : "") + " düğümü " + n.no + "</h3>";
      const Q = refP({ dugum: n.no });
      if (n.tur === "bolme") h += '<p class="not">' + kacis(refMetin(n.cubuk_i)) + " → " + kacis(refMetin(n.cubuk_j)) + ", oran t = " + kacis(String(n.oran)) + "</p>";
      if (Q) h += '<p class="not">X = ' + f2(Q[0]) + " m, Y = " + f2(Q[1]) + " m, Z = " + f2(Q[2]) + " m (akslar taşınınca birlikte taşınır)</p>";
    }
    return h;
  }
  function s3OzellikDegistir(ad, el) {
    const tur = D.secim.length ? D.secim[0].tur : null;
    if (!tur) return;
    const deger = el.type === "checkbox" ? el.checked : el.value;
    const nolar = D.secim.filter(function (x) { return x.tur === tur; }).map(function (x) { return +x.no; });
    if (tur === "cubuk") {
      if (ad === "kesit" && deger === "__yeni") { D.panelSekme = "kutuphane"; A.toast("Kütüphanede “Yeni kesit” ekleyin; sonra burada seçin."); yenile(); return; }
      // duvar ve duvar yüksekliği yerinde yazılır (ModelOps.ozellikAta bu alanları tanımayabilir)
      if (ad === "duvar" || ad === "duvar_h") {
        let v = null;
        if (ad === "duvar") v = deger === "__varsayilan" ? varsayilanDuvar() : (deger || null);
        else if (String(deger).trim() !== "") { v = sayiOku(deger); if (v == null || v <= 0) { A.toast("Duvar yüksekliği pozitif bir sayı olmalı (m)."); panelCiz(); return; } }
        nolar.forEach(function (no) {
          const c = nesneBul("cubuk", no);
          if (!c || DUVARLI_CUBUK.indexOf(c.tur || "diger") < 0) return;
          if (v == null) { delete c[ad]; if (ad === "duvar") delete c.duvar_h; } else c[ad] = v;
        });
        degisti();
        return;
      }
      const oz = {};
      if (ad === "aci" || ad === "Lb") { const v = sayiOku(deger); if (deger === "" && ad === "Lb") oz.Lb = null; else if (v == null) { A.toast("Sayı girin."); panelCiz(); return; } else oz[ad] = v; }
      else if (ad === "K") { const l = String(deger).trim() ? String(deger).trim().split(/[\s;]+/).map(sayiOku) : []; if (l.length && l.some(function (v) { return v == null || v <= 0; })) { A.toast("K iki pozitif sayı olmalı (ör. 1 0,7)."); panelCiz(); return; } oz.K = l.length ? [l[0], l[1] != null ? l[1] : l[0]] : null; }
      else if (ad === "yalniz_cekme") oz.yalniz_cekme = deger ? true : null;
      else if (ad === "grup") oz.grup = String(deger).trim() || null;
      else oz[ad] = deger || null;
      const MO = window.ModelOps;
      if (MO) {
        let r;
        try { r = MO.ozellikAta(B, nolar, oz); } catch (e) { A.toast(e.message); return; }
        binaAyarla(r.model, { normalize: false, etiket: r.uyarilar && r.uyarilar.length ? r.uyarilar.join(" ") : "" });
        return;
      }
      nolar.forEach(function (no) { const c = nesneBul("cubuk", no); Object.keys(oz).forEach(function (k) { if (oz[k] === null) delete c[k]; else c[k] = oz[k]; }); });
    } else if (tur === "panel") {
      nolar.forEach(function (no) {
        const p = nesneBul("panel", no);
        if (!p) return;
        if (ad === "kalinlik" || ad === "g" || ad === "q") { const v = sayiOku(deger); if (deger === "" && ad !== "kalinlik") delete p[ad]; else if (v != null && v >= 0) p[ad] = v; }
        else if (ad === "kar") p.kar = !!deger;
        else if (ad === "kullanim") { if (deger) p.kullanim = deger; else delete p.kullanim; }
        else p[ad] = deger;
      });
    } else if (tur === "mesnet") {
      nolar.forEach(function (no) { const m = nesneBul("mesnet", no); if (m) m[ad] = !!deger; });
    }
    degisti();
  }
  function kesitKarti(ad) {
    const o = kesitOz(ad);
    if (!o) return "";
    const m = malzemeKart(o.malzeme);
    let h = '<div class="bn-kart"><b>' + kacis(ad) + "</b> · " + kacis(kesitEtiketi(o)) + (o.malzeme ? " · " + kacis(o.malzeme) : "") +
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
    return alanH("Başlık", '<input class="girdi" data-bina="baslik" value="' + kacis(B.baslik || "") + '">') +
      alanH("Sistem", '<select class="girdi" data-bina="sistem">' + secenekler([["betonarme", "Betonarme (TS 500)"], ["celik", "Çelik (ÇYTHYE)"]], B.sistem) + "</select>") +
      '<h3 class="bn-pbaslik">Temel ve zemin</h3>' + temelAlanlari() +
      '<h3 class="bn-pbaslik">Kesit tahkiki</h3>' +
      alanH("Çelik kiriş yanal burulmalı burkulma boyu L_b (ÇYTHYE 9.2)", '<select class="girdi" data-analiz-sec="celik_Lb">' + secenekler([["otomatik", "Otomatik — döşemeli kirişte üst başlık tutulu (L_b = 0)"], ["boy", "Eleman boyu (L_b = L; tutulma yok)"]], (B.analiz && B.analiz.celik_Lb) || "otomatik") + "</select>") +
      (B.sistem === "celik" ? "" : '<p class="not">Yalnız çelik elemanlarda kullanılır; betonarme tahkik TS 500 ile yapılır.</p>') +
      '<p class="not">Yük durumları ve kombinasyon kümesi “Yükler” sekmesinde, TBDY 2018 deprem girdileri “Deprem” sekmesinde. Uygulama öğretim ve ön boyutlandırma içindir, tasarım aracı değildir.</p>';
  }
  // genel modelde temel (sözleşme C11.5): mütemadi / radye GLOBAL aks çizgileri üzerinde; tekil temel en alt seviyedeki aks kesişimlerinde
  const TEMEL_S3_NOTU = "Genel modelde temel kirişleri GLOBAL X/Y aks çizgileri boyunca (temel kotunda kolonu olan akslarda), radye GLOBAL aks zarfı + taşma üzerinde kurulur. Ek aks sistemindeki kolon tabanları yalnız kirişsiz radyede ağa katılır; mütemadi ve kirişli radyede onlara 'mesnetler' ile mesnet verin.";
  const TEMEL_S3_TEKIL = "Genel modelde en alt seviyedeki aks kesişimleri tekil temel mesnetidir.";
  // Temel tipi seçici + tipe göre alanlar (tasarım §13). data-temel-a="<alt nesne>.<alan>" sayısal alanlar; m cinsinden.
  function sayiAlan(etiket, yol, deger, ipucu) {
    return alanH(etiket, '<input class="girdi" inputmode="decimal" data-temel-a="' + yol + '" value="' + kacis(deger != null ? deger : "") + '"' + (ipucu ? ' title="' + kacis(ipucu) + '"' : "") + ">");
  }
  function temelAlanlari() {
    const t = B.temeller, z = t.zemin || {}, v = t.varsayilan || {};
    const s3 = s3Var();      // genel model: mütemadi / radye GLOBAL aks çizgileri üzerinde (sözleşme C11)
    let h = '<div class="se-seg bn-temel-tip" role="radiogroup" aria-label="Temel tipi">' + ["tekil", "surekli", "radye"].map(function (k) {
      return '<button type="button" class="se-seg-d" role="radio" data-temel-tip="' + k + '" aria-checked="' + (t.tip === k) + '" aria-pressed="' + (t.tip === k) + '">' + TEMEL_TIP_AD[k] + "</button>";
    }).join("") + "</div>" + (s3 ? '<p class="not bn-temel-s3-not">' + kacis(t.tip !== "tekil" ? TEMEL_S3_NOTU : TEMEL_S3_TEKIL) + "</p>" : "");
    if (t.tip === "surekli") {
      const s = t.surekli || TEMEL_VARS.surekli;
      const yonAks = s.yon === "x" ? B.akslar.y : s.yon === "y" ? B.akslar.x : B.akslar.y.concat(B.akslar.x);
      h += '<p class="not">Kolonlar aks çizgileri boyunca uzanan ters T temel kirişlerine oturur; zemin Winkler yaylarıyla (k₀) modellenir.</p>' +
        alanH("Kiriş doğrultusu", '<select class="girdi" data-temel-a="surekli.yon">' + secenekler([["x", "X doğrultusunda (aks " + B.akslar.y.map(function (a) { return a.ad; }).join(", ") + ")"], ["y", "Y doğrultusunda (aks " + B.akslar.x.map(function (a) { return a.ad; }).join(", ") + ")"], ["xy", "İki doğrultuda (ızgara)"]], s.yon) + "</select>") +
        '<div class="bn-alan"><span>Akslar</span><div class="bn-cipler" role="group" aria-label="Temel kirişi aksları">' +
          '<button type="button" class="bn-cip' + (s.akslar === "tum" ? " aktif" : "") + '" data-temel-aks="__tum" aria-pressed="' + (s.akslar === "tum") + '">Tümü</button>' +
          yonAks.map(function (a) { const sec = s.akslar !== "tum" && s.akslar.indexOf(a.ad) >= 0; return '<button type="button" class="bn-cip' + (sec ? " aktif" : "") + '" data-temel-aks="' + kacis(a.ad) + '" aria-pressed="' + sec + '">' + kacis(a.ad) + "</button>"; }).join("") +
        "</div></div>" +
        '<div class="bn-uc">' + sayiAlan("Tabla B (m)", "surekli.B", s.B) + sayiAlan("h tabla (m)", "surekli.h_tabla", s.h_tabla) + sayiAlan("Taşma (m)", "surekli.tasma", s.tasma, "Uç kolondan konsol boyu") + "</div>" +
        '<div class="bn-uc">' + sayiAlan("Gövde b (m)", "surekli.b_govde", s.b_govde) + sayiAlan("Gövde h (m)", "surekli.h_govde", s.h_govde, "Toplam kiriş yüksekliği (tabla dahil)") + sayiAlan("Ağ aralığı (m)", "surekli.ag", s.ag, "Eleman bölme aralığı") + "</div>" +
        '<p class="not bn-ipucu-not">Gövde h toplam kiriş yüksekliğidir (tabla dahil). b gövde = B ve h tabla = 0 → dikdörtgen kesit. TS 500: h ≥ L/10, tabla ≥ 200 mm.</p>';
    } else if (t.tip === "radye") {
      const r = t.radye || TEMEL_VARS.radye, k = r.kiris;
      h += '<p class="not">Plak iki doğrultulu ızgara (grillage) ile, zemin düğüm yaylarıyla (k₀ · etki alanı) modellenir.</p>' +
        '<div class="bn-uc">' + sayiAlan("Kalınlık h (m)", "radye.h", r.h, "TS 500: radye ≥ 300 mm") + sayiAlan("Taşma (m)", "radye.tasma", r.tasma, "Dış aks dışına taşma") + sayiAlan("Ağ aralığı (m)", "radye.ag", r.ag, "Izgara aralığı") + "</div>" +
        '<label class="bn-onay"><input type="checkbox" data-temel-kiris="1"' + (k ? " checked" : "") + "> Kirişli radye (aks çizgilerinde temel kirişleri)</label>" +
        (k ? '<div class="bn-iki">' + sayiAlan("Kiriş b (m)", "radye.kiris.b", k.b) + sayiAlan("Kiriş h (m)", "radye.kiris.h", k.h, "Toplam yükseklik (plak dahil); kirişler plağın üstünde") + "</div>" : "");
    } else {
      h += '<div class="bn-uc">' + alanH("B (m)", '<input class="girdi" inputmode="decimal" data-temel-v="B" value="' + kacis(v.B) + '">') + alanH("L (m)", '<input class="girdi" inputmode="decimal" data-temel-v="L" value="' + kacis(v.L) + '">') + alanH("h (m)", '<input class="girdi" inputmode="decimal" data-temel-v="h" value="' + kacis(v.h) + '">') + "</div>" +
        alanH("Mesnet modeli", '<select class="girdi" data-temel="mesnet">' + secenekler([["ankastre", "Ankastre"], ["mafsal", "Mafsal (ux, uy, uz)"], ["elastik", "Elastik (k₀ ile yaylar)"]], t.mesnet) + "</select>");
    }
    h += '<h4 class="bn-palt">Zemin</h4><div class="bn-uc">' + alanH("q_em (kN/m²)", '<input class="girdi" inputmode="decimal" data-zemin="q_em" value="' + kacis(z.q_em) + '" title="TS 500 emniyet gerilmesi (servis G+Q)">') +
      alanH("k₀ (kN/m³)", '<input class="girdi" inputmode="decimal" data-zemin="k0" value="' + kacis(z.k0) + '" title="Yatak katsayısı (Winkler)">') +
      alanH("γ zemin (kN/m³)", '<input class="girdi" inputmode="decimal" data-zemin="gamma" value="' + kacis(z.gamma != null ? z.gamma : 18) + '">') + "</div>" +
      '<details class="bn-ayrinti bn-k0-ipucu"><summary>k₀ için tipik aralıklar</summary><table class="se-sonuc-tablo bn-mini-tablo"><thead><tr><th>Zemin</th><th>k₀ (kN/m³)</th></tr></thead><tbody>' +
        [["Gevşek kum", "4 800 – 16 000"], ["Orta sıkı kum", "9 600 – 80 000"], ["Sıkı kum", "64 000 – 128 000"], ["Killi orta sıkı kum", "32 000 – 80 000"], ["Siltli orta sıkı kum", "24 000 – 48 000"],
         ["Kil, q_u ≤ 200 kPa", "12 000 – 24 000"], ["Kil, 200 < q_u ≤ 800 kPa", "24 000 – 48 000"], ["Kil, q_u > 800 kPa", "> 48 000"]].map(function (r) { return "<tr><td>" + r[0] + '</td><td class="sayi">' + r[1] + "</td></tr>"; }).join("") +
      '</tbody></table><p class="not">Bowles (1996) Tablo 9-1 plaka yükleme değerleri; temel boyutuna göre küçültülmeli. Öğretim içindir.</p></details>';
    return h;
  }
  function temelTipSec(tip) {
    if (!TEMEL_TIP_AD[tip] || B.temeller.tip === tip) return;
    B.temeller.tip = tip;
    B.temeller = temelNormalize(B.temeller);
    degisti(TEMEL_TIP_AD[tip] + " temel");
    D.panelSekme = "bina"; panelCiz();
  }
  function temelAlanDegistir(yol, el) {
    const p = yol.split("."), t = B.temeller;
    if (p[0] === "surekli" && p[1] === "yon") { t.surekli.yon = el.value; t.surekli.akslar = "tum"; degisti(); panelCiz(); return; }
    const n = sayiOku(el.value), sifirOlur = p[1] === "h_tabla" || p[1] === "tasma";
    if (n == null || n < 0 || (!sifirOlur && n === 0)) { A.toast("Pozitif bir sayı girin (m)."); panelCiz(); return; }
    let o = t[p[0]];
    if (p.length === 3) o = o && o[p[1]];
    if (!o) return;
    o[p[p.length - 1]] = n;
    if (p[0] === "surekli" && t.surekli.h_tabla >= t.surekli.h_govde) A.toast("Tabla kalınlığı toplam yükseklikten (gövde h) küçük olmalı.");
    if (p[0] === "surekli" && t.surekli.b_govde > t.surekli.B) A.toast("Gövde genişliği tabla genişliğinden (B) büyük olamaz.");
    degisti();
  }
  function temelAksSec(ad) {
    const s = B.temeller.surekli;
    if (!s) return;
    const tum = (s.yon === "x" ? B.akslar.y : s.yon === "y" ? B.akslar.x : B.akslar.y.concat(B.akslar.x)).map(function (a) { return a.ad; });
    if (ad === "__tum") s.akslar = "tum";
    else {
      let l = s.akslar === "tum" ? tum.slice() : s.akslar.slice();
      const i = l.indexOf(ad);
      if (i >= 0) l.splice(i, 1); else l.push(ad);
      l = tum.filter(function (x) { return l.indexOf(x) >= 0; });
      if (!l.length) { A.toast("En az bir aks seçili olmalı."); return; }
      s.akslar = l.length === tum.length ? "tum" : l;
    }
    degisti(); panelCiz();
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
      h += '<div class="bn-kart' + (D.firca === ad ? " bn-kart-firca" : "") + '"><b>' + kacis(ad) + "</b> " + kacis(kesitEtiketi(o)) + (o.malzeme ? " · " + kacis(o.malzeme) : "") +
        "<br><small>A = " + fmt(o.A) + " m², I_y = " + fmt(o.Iy) + ", I_z = " + fmt(o.Iz) + ", J ≈ " + fmt(o.J) + " m⁴" +
        (o.tip === "vute" ? " — temel kesitin (" + kacis(o.temel) + ") özellikleri; uçlarda doğrusal büyütme" : o.tip === "profil" ? "" : " — I = b·h³/12, J ≈ β·b³·h") + "</small>" +
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
        alanH("Duvar türü", '<select class="girdi" name="duvarTip">' + secenekler((KUT.duvarlar || []).map(function (d) { return [d.ad, d.etiket + " (" + f2(d.w) + " kN/m²)"]; }), "tugla-delikli-19") + "</select>") + "</div>" +
      '<div class="bn-iki">' + alanH("Temel tipi", '<select class="girdi" name="temelTip">' + secenekler([["tekil", "Tekil"], ["surekli", "Mütemadi (sürekli, iki doğrultu)"], ["radye", "Radye"]], B.temeller.tip) + "</select>") +
        alanH("Zemin q_em (kN/m²)", '<input class="girdi" name="qem" inputmode="decimal" value="' + kacis(B.temeller.zemin.q_em) + '">') + "</div>" +
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
    const yeni = binaUret(p), qem = sayiOku(v("qem"));
    yeni.temeller = temelNormalize({ tip: v("temelTip") || "tekil", zemin: { q_em: qem && qem > 0 ? qem : B.temeller.zemin.q_em, k0: B.temeller.zemin.k0 } });
    binayiAyarla(yeni, "Bina üretildi: " + yeni.akslar.x.length + "×" + yeni.akslar.y.length + " aks, " + p.katSayisi + " kat, " + TEMEL_TIP_AD[yeni.temeller.tip].toLocaleLowerCase("tr") + " temel.");
    sablonSeciciAyarla("");
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
    sablonSeciciAyarla("");
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
  let sablonlar = YERLESIK_KUTUPHANE.sablonlar.slice(), sablonlarSoz = null;
  // seçicide gösterilen yüklü şablon: seçenekler motordan sonra gelir (soğuk açılışta #bina/sablon/<ad>); liste dolunca uygulanır
  let sablonSecili = "";
  function sablonSeciciAyarla(ad) {
    sablonSecili = ad || "";
    if (!ref.sablon) return;
    ref.sablon.value = sablonSecili;
    if (ref.sablon.value !== sablonSecili) ref.sablon.value = "";
  }
  function sablonListesi() {
    ref.sablon.innerHTML = '<option value="">Şablon…</option>' + sablonlar.map(function (s) { return '<option value="' + kacis(s.ad) + '">' + kacis(s.baslik) + "</option>"; }).join("");
    sablonSeciciAyarla(sablonSecili);
  }
  // sec.adres: istek adres çubuğundan (#bina/sablon/<ad>) geldi; bilinmeyen adda adres #bina olur
  function sablonYukle(ad, sec) {
    if (!ad) return Promise.resolve();
    const yerel = function () {
      if (YERLESIK_SABLON[ad]) { binayiAyarla(YERLESIK_SABLON[ad](), "Şablon yüklendi (yerleşik)."); sablonSeciciAyarla(ad); return; }
      // bilinmeyen ad: yüklü model ve seçici olduğu gibi kalır; adlar listesi (motorun listesi gelince) söylenir
      sablonSeciciAyarla(sablonSecili);
      if (sec && sec.adres) { try { history.replaceState(history.state, "", location.pathname + location.search + "#bina"); } catch (e) { /* yoksay */ } }
      Promise.resolve(sablonlarSoz).then(null, function () { /* yerleşik liste */ }).then(function () {
        A.toast("Şablon bulunamadı: " + ad + ". Şablonlar: " + sablonlar.map(function (x) { return x.ad; }).join(", "));
      });
    };
    return A.motorIstegi({ islem: "bina_sablon", girdi: { ad: ad } }).then(function (y) {
      if (!y || y.hata || !y.bina) { yerel(); return; }
      binayiAyarla(y.bina, "Şablon yüklendi: " + (y.bina.baslik || ad));
      sablonSeciciAyarla(ad);
    }, yerel);
  }
  // Motorun "bina_kutuphane" yanıtını (malzemeler/kullanım/duvar/kaplama sözlükleri; §6) arayüzün liste biçimine çevirir.
  function kutuphaneNormalize(y) {
    const k = Object.assign({}, YERLESIK_KUTUPHANE);
    const ml = y.malzemeler || {};
    if (Array.isArray(ml.beton) || Array.isArray(ml.celik) || Array.isArray(ml.donati)) k.malzemeler = ml;
    else {
      const b = [], c = [], d = [];
      Object.keys(ml).forEach(function (ad) {
        const m = ml[ad] || {}, o = { ad: ad, dogrulandi: m.dogrulandi, kaynak: m.kaynak };
        if (m.tur === "celik") { Object.assign(o, { Fy: m.Fy, Fu: m.Fu, E: m.E_MPa, G: m.G_MPa, gamma: m.gamma }); c.push(o); }
        else if (m.tur === "donati") { Object.assign(o, { fyk: m.fyk, Es: m.E_MPa }); d.push(o); }
        else { Object.assign(o, { fck: m.fck, Ec: m.E_MPa, gamma: m.gamma, fctk: m.fctk }); b.push(o); }
      });
      k.malzemeler = { beton: b, celik: c, donati: d };
    }
    k.kesit_katalogu = Object.assign({}, YERLESIK_KUTUPHANE.kesit_katalogu, y.kesit_katalogu || {});
    const sozlukListe = function (v, cevir) {
      if (Array.isArray(v)) return v;
      if (v && typeof v === "object") return Object.keys(v).map(function (ad) { return cevir(ad, v[ad] || {}); });
      return null;
    };
    k.kullanim_siniflari = sozlukListe(y.kullanim_siniflari, function (ad, x) { return { ad: ad, etiket: x.ad || ad, q: x.deger, kaynak: x.kaynak, dogrulandi: x.dogrulandi, azaltma_grubu: x.azaltma_grubu }; }) || k.kullanim_siniflari;
    // motorun duvar adı birim ağırlığı da taşır ("… sıva (2,70 kN/m²)"): etiket yalnız ad; değer her yerde bir kez eklenir (duvarW)
    k.duvarlar = sozlukListe(y.duvarlar, function (ad, x) {
      return { ad: ad, etiket: String(x.ad || ad).replace(/\s*\([^()]*kN\/m²\)\s*$/, "") || ad, w: x.deger, kaynak: x.kaynak, dogrulandi: x.dogrulandi };
    }) || k.duvarlar;
    k.kaplamalar = sozlukListe(y.kaplamalar, function (ad, x) { return { ad: ad, etiket: x.ad || ad, g: x.deger, kaynak: x.kaynak, dogrulandi: x.dogrulandi }; }) || k.kaplamalar;
    if (Array.isArray(y.kombinasyon_kumeleri)) k.kombinasyon_kumeleri = y.kombinasyon_kumeleri;
    if (Array.isArray(y.sablonlar) && y.sablonlar.length) k.sablonlar = y.sablonlar;
    k.dogrulanmamis = Array.isArray(y.dogrulanmamis) ? y.dogrulanmamis : [];
    k.sinirlar = y.sinirlar || null;
    // Dilim 2: taşıyıcı sistemler (Tablo 4.1) — liste [{ad, etiket, R, D, BYS_izin}] ya da sözlük {ad: {...}}
    const ts = sozlukListe(y.tasiyici_sistemler, function (ad, x) { return Object.assign({ ad: ad, etiket: x.etiket || x.ad || x.tanim || ad }, x); });
    if (ts && ts.length && ts.every(function (t) { return t.ad && t.R != null && t.D != null; })) k.tasiyici_sistemler = ts;
    return k;
  }
  function kutuphaneyiAl() {
    return A.motorIstegi({ islem: "bina_kutuphane", girdi: {} }).then(function (y) {
      if (!y || y.hata) return;
      KUT = kutuphaneNormalize(y);
      if (Array.isArray(KUT.sablonlar) && KUT.sablonlar.length) { sablonlar = KUT.sablonlar; sablonListesi(); }
      if (B) panelCiz();
    }, function () { /* motor yok: yerleşik kütüphane */ });
  }
  function sablonlariAl() {
    return (sablonlarSoz = A.motorIstegi({ islem: "bina_sablonlar", girdi: {} }).then(function (y) {
      if (y && !y.hata && Array.isArray(y.sablonlar) && y.sablonlar.length) { sablonlar = y.sablonlar; sablonListesi(); }
    }, function () { /* yerleşik */ }));
  }

  // ---------- Hesap hattı ve çözüm ----------
  // Hesap hattı: Yükler → Yük durumları (açık durumlar) → Kombinasyonlar (N) → Zarf → Tasarım (D/C maks); çözümden sonra kutular yeşil.
  // Kutu [etiket, anlatım adımı, sekme?, ek sınıf]; adım 0 = pasif. Tasarım kutusu Tasarım sekmesini açar (veri.tasarim varsa).
  function kombSayisi(v) {
    return (v.zarf && v.zarf.kombinasyon_sayisi) || (v.kombinasyonlar || []).filter(function (k) { return k.uygulandi && k.tur !== "drift"; }).length || Object.keys(v.sonuclar || {}).length;
  }
  function driftSayisi(v) {
    return (v.ozet && v.ozet.drift_kombinasyon_sayisi) || (v.kombinasyonlar || []).filter(function (k) { return k.uygulandi && k.tur === "drift"; }).length;
  }
  function dcSinif(dc) { return dc == null || !isFinite(dc) ? "yok" : dc < 0.7 ? "y" : dc < 0.9 ? "s" : dc <= 1.0 ? "t" : "k"; }
  // Anlatım adım numaraları motorun gerçek başlıklarından ("### 7. Adım: TBDY 2018 eşdeğer deprem yükü") eşlenir; çözüm yokken varsayılan
  const ADIM_ANAHTAR = {
    yukler: [/^Yükler/i, 2], doseme: [/Döşemeden/i, 3], kiris: [/Kiriş yük/i, 4], durumlar: [/^Yük durumları/i, 6], deprem: [/eşdeğer deprem|deprem yükü/i, 7],
    akis: [/kolondan temele|Kirişten kolona/i, 9], komb: [/^Kombinasyon/i, 10], tahkik: [/Kesit tahkik/i, 12],
  };
  function adimNo(anahtar) {
    const a = ADIM_ANAHTAR[anahtar];
    if (!a) return +anahtar || 0;
    if (SON && SON.y && Array.isArray(SON.y.bloklar)) {
      if (!SON.adimlar) {
        SON.adimlar = [];
        SON.y.bloklar.forEach(function (b) {
          if (b.tur !== "md") return;
          String(b.icerik || "").split("\n").forEach(function (l) { const m = /^#{2,4}\s*(\d+)\.\s*(?:Adım:)?\s*(.*)$/.exec(l.trim()); if (m) SON.adimlar.push([+m[1], m[2]]); });
        });
      }
      const h = SON.adimlar.filter(function (x) { return a[0].test(x[1]); })[0];
      if (h) return h[0];
    }
    return a[1];
  }
  function hatAdimlari() {
    const tamam = SON && !sonEski, v = tamam ? SON.veri : null;
    let durumlar;
    if (v && v.durumlar) {
      const harf = {}; Object.keys(v.durumlar).forEach(function (k) { harf[k.charAt(0)] = 1; });
      durumlar = ["G", "Q", "S", "W", "E"].filter(function (k) { return harf[k]; }).join(" ") + " (" + Object.keys(v.durumlar).length + ")";
    } else durumlar = Object.keys(B.yuk_durumlari || {}).filter(function (k) { return B.yuk_durumlari[k].acik; }).join(" ");
    const nKomb = v ? kombSayisi(v) : "", nDrift = v ? driftSayisi(v) : 0;
    const t = v && v.tasarim, dcM = t ? (t.en_buyuk_dc != null ? t.en_buyuk_dc : Math.max.apply(null, (t.elemanlar || []).map(function (e) { return e.dc || 0; }).concat([0]))) : null;
    const tasarim = t ? ["Tasarım · D/C maks " + f2(dcM), adimNo("tahkik"), "tasarim", " bn-hat-dc bn-dc-" + dcSinif(dcM)] : [v ? "Tasarım (motor güncellemesiyle)" : "Tasarım", 0];
    return [["Yükler", adimNo("yukler")], ["Yük durumları " + durumlar, adimNo("durumlar")], ["Kombinasyonlar" + (nKomb ? " " + nKomb : "") + (nDrift ? " (+" + nDrift + " öteleme)" : ""), adimNo("komb")], ["Zarf", adimNo("komb")], tasarim];
  }
  // Çözüm ilerleme göstergesi (Pyodide'de çözüm + kesit tahkiki birkaç saniye sürebilir): geçen süre ve aşama metni
  let ilerlemeZ = 0, ilerlemeT0 = 0;
  function ilerlemeCiz() {
    const el = document.getElementById("bn-ilerleme");
    if (!el) return;
    if (!D.cozuluyor) { el.hidden = true; el.innerHTML = ""; clearInterval(ilerlemeZ); ilerlemeZ = 0; return; }
    const sn = (Date.now() - ilerlemeT0) / 1000, yd = B.yuk_durumlari || {};
    const is = "yük durumları (" + Object.keys(yd).filter(function (k) { return yd[k].acik; }).join(", ") + "), kombinasyonlar, zarf, kesit tahkikleri ve anlatım";
    el.hidden = false;
    el.innerHTML = '<div class="bn-ilerleme-cubuk" role="progressbar" aria-label="Çözüm sürüyor" aria-valuetext="' + kacis(sn.toFixed(1)) + ' s"><span></span></div>' +
      '<span class="not">Çözülüyor… ' + sn.toFixed(1).replace(".", ",") + " s — " + kacis(is) + " hesaplanıyor" + (sn > 3 ? "; tarayıcıda (Pyodide) birkaç saniye sürebilir" : "") + ".</span>";
  }
  function ilerlemeBaslat() { ilerlemeT0 = Date.now(); clearInterval(ilerlemeZ); ilerlemeZ = setInterval(ilerlemeCiz, 250); ilerlemeCiz(); }
  function hatCiz() {
    const tamam = SON && !sonEski;
    ref.hat.innerHTML = hatAdimlari().map(function (h, i) {
      const pasif = h[1] === 0;
      return (i ? '<span class="bn-hat-ok" aria-hidden="true">→</span>' : "") + '<button type="button" class="bn-hat-adim' + (tamam && !pasif ? " tamam" : "") + (pasif ? " pasif" : "") + (h[3] || "") + '" data-adim="' + h[1] + '"' +
        (h[2] ? ' data-hat-sekme="' + h[2] + '"' : "") + (pasif ? " disabled" : "") + ">" + (tamam && !pasif ? "✓ " : "") + kacis(h[0]) + "</button>";
    }).join("");
    ref.coz.disabled = D.cozuluyor;
    ref.coz.textContent = D.cozuluyor ? "Çözülüyor…" : "Çöz ▶";
    ref.coz.setAttribute("aria-busy", String(!!D.cozuluyor));
    ilerlemeCiz();
  }
  // Çözüm: Promise<bool> döner (rapor / ısı haritası "çözüm yoksa önce çöz" için); çözüm sürerken çağrılırsa aynı sözü verir
  let cozumSozu = null, sonCozumHatasi = "";
  function coz() {
    if (D.cozuluyor) return cozumSozu || Promise.resolve(false);
    const dg = dogrula();
    sonCozumHatasi = "";
    hataGoster(ref.hata, dg.hata, dg.hata.length > 1 ? "Modelde düzeltilecek yerler var:" : "");
    if (dg.hata.length) { sonCozumHatasi = dg.hata.join(" "); ref.hata.scrollIntoView({ block: "nearest", behavior: "smooth" }); return Promise.resolve(false); }
    if (dg.uyari.length && !window.confirm(dg.uyari.length + " uyarı var (ör. " + dg.uyari[0].metin + "). Yine de çözülsün mü?")) { sonCozumHatasi = "Çözüm, uyarılar nedeniyle iptal edildi."; return Promise.resolve(false); }
    D.cozuluyor = true; ilerlemeBaslat(); hatCiz(); aracYenile();
    const cozulen = kopya(B), cozulenAnlik = anlikGoruntu(), s3 = s3Var(cozulen);
    // genel model (surum 3): motorun desteği yoklanır; desteklemeyen motor çubuk/panelleri sessizce atlamasın (öğretici hata)
    cozumSozu = (s3 ? motorS3Yokla() : Promise.resolve(true)).then(function (destek) {
      if (!destek) return { hata: S3_MOTOR_YOK, hata_turu: "girdi" };
      return A.motorIstegi({ islem: "bina_coz", girdi: { bina: cozulen } });
    }).then(function (y) {
      // yönlendirme uyuşmazlığı (model genel ama motor aks–kat çözdü): yalnız bu çözüm reddedilir; motor desteği (MOTOR_S3) yalnız
      // motorS3Yokla'nın "Bilinmeyen işlem" yoklamasıyla kapanır — yoksa oturumun geri kalanında bütün genel modeller reddedilirdi
      if (y && !y.hata && s3 && y.veri && y.veri.model !== "genel") y = { hata: S3_YONLENDIRME, hata_turu: "girdi" };
      else if (y && !y.hata && s3) MOTOR_S3 = true;
      if (!y || y.hata) { cekmeceAc(); SON = null; sonCozumHatasi = y && y.hata ? y.hata : "Boş yanıt."; hataGoster(ref.hata, [sonCozumHatasi], y && y.hata_turu === "ic" ? "Motor hatası" : "Bina çözülemedi"); sonucuTemizle(); return false; }
      if (!y.veri || !y.veri.ag || !y.veri.durumlar) { sonCozumHatasi = "Motor yanıtında “veri.ag” ya da “veri.durumlar” yok (şema §4)."; hataGoster(ref.hata, [sonCozumHatasi], "Beklenmeyen yanıt"); return false; }
      hataGoster(ref.hata, []);
      // çözüm sürerken model değiştiyse (şablon yüklendi, düzenlendi) sonuçlar önceki modele aittir
      SON = { y: y, veri: y.veri, bina: cozulen }; sonEski = anlikGoruntu() !== cozulenAnlik; D.akisHedef = null; D.sankeySecim = null; D.sekme = "akis"; D.tasarimSecim = null;
      Object.keys(KOMB_BEKLEYEN).forEach(function (k) { delete KOMB_BEKLEYEN[k]; });
      Object.keys(KOMB_HATA).forEach(function (k) { delete KOMB_HATA[k]; });
      Object.keys(TASARIM_AYR).forEach(function (k) { delete TASARIM_AYR[k]; });
      if (y.veri.ozet && y.veri.ozet.sonuclar_tembel) A.toast("Büyük model: kombinasyon sonuçları yanıta yazılmadı; önce G durumu gösteriliyor, kombinasyonlar seçince motordan alınır.");
      if (!(D.diyagramDurum in (y.veri.sonuclar || {})) && D.diyagramDurum !== "zarf" && !(D.diyagramDurum in y.veri.durumlar)) D.diyagramDurum = Object.keys(y.veri.sonuclar || {})[0] || "G";
      if (!(D.deformeDurum in (y.veri.sonuclar || {})) && !(D.deformeDurum in y.veri.durumlar)) D.deformeDurum = Object.keys(y.veri.sonuclar || {})[0] || "G";
      if (!(["G", "Q", "G+Q", "S", "W"].indexOf(D.akisDurum) >= 0) || (D.akisDurum === "S" && !y.veri.durumlar.S)) D.akisDurum = "G";
      cekmeceAc();
      sonucuCiz();
      yenile();
      if (!KAPLAMA.el) ref.sonuc.scrollIntoView({ block: "start", behavior: azHareket() ? "auto" : "smooth" });
      RAPOR = null;
      olayYay("cozum", { cozum_kimligi: y.veri.cozum_kimligi || null });
      return !sonEski;
    }).catch(function (e) {
      sonCozumHatasi = (e && e.message) ? e.message : String(e);
      hataGoster(ref.hata, [sonCozumHatasi], "Çözüm çalıştırılamadı");
      return false;
    }).then(function (ok) { D.cozuluyor = false; cozumSozu = null; hatCiz(); aracYenile(); if (KAPLAMA.tur === "tablolar") tablolarTazeleGecikmeli(0); return ok; });
    return cozumSozu;
  }
  function sonucuTemizle() { SON = null; sonEski = false; D.akisHedef = null; ref.sonuc.innerHTML = ""; }
  // Motorun genel model (surum 3, köprüde bina_kesit_oner) desteği: bir kez yoklanır (aks–kat akışında hiç istek gitmez)
  const S3_MOTOR_YOK = "Bu kurulumdaki hesap motoru genel (surum 3) modeli çözmüyor: aks tabanlı çubuk, panel, mesnet ve ek yükler hesaba " +
    "katılamaz. Çizim, düzenleme, kaydetme, tablolar ve IFC dışa aktarımı çalışır; çözüm için uygulamayı güncelleyin (genel model motoru gerekir). " +
    "Aks–kat modelleri (kolon, kiriş, döşeme) bu motorla çözülmeye devam eder.";
  const S3_YONLENDIRME = "Hesap motoru bu modeli aks–kat modeli olarak çözdü; mesnet, çubuk, panel ve düğüm yükü kayıtları hesaba katılmadı. Uygulamayı güncelleyin.";
  let MOTOR_S3 = null;
  function motorS3Yokla() {
    if (MOTOR_S3 != null) return Promise.resolve(MOTOR_S3);
    return Promise.resolve(A.motorIstegi({ islem: "bina_kesit_oner", girdi: {} })).then(function (y) {
      MOTOR_S3 = !(y && y.hata && /Bilinmeyen işlem/i.test(String(y.hata)));
      return MOTOR_S3;
    }, function () { return true; });     // motor hiç yüklenemediyse asıl çözüm isteği hatayı gösterir
  }
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
  // Yük akışı durum değeri: G, Q, G+Q; motor S/W verisi verdiyse (üçüncü/dördüncü bağımsız değişken) S ve W
  function akisDeger(objG, objQ, objS, objW) {
    const d = D.akisDurum;
    const g = +objG || 0, q = +objQ || 0;
    if (d === "S") return +objS || 0;
    if (d === "W") return +objW || 0;
    return d === "G" ? g : d === "Q" ? q : g + q;
  }
  // Kiriş yük dökümü: motorda G/Q alt alanları kN toplamdır (kN/m değerleri kN_m'de); burada kN/m'ye çevrilir.
  function kirisKNm(yk, durum) {
    const L = yk.L || 1, G = yk.G || {}, Q = yk.Q || {};
    const g = { doseme: (G.doseme || 0) / L, duvar: (G.duvar || 0) / L, oz: (G.oz || 0) / L, ek: (G.ek || 0) / L, toplam: (G.toplam_kN || 0) / L };
    const q = { doseme: (Q.doseme || 0) / L, duvar: 0, oz: 0, ek: (Q.ek || 0) / L, toplam: (Q.toplam_kN || 0) / L };
    if (durum === "G") return g;
    if (durum === "Q") return q;
    const o = {}; Object.keys(g).forEach(function (k) { o[k] = g[k] + q[k]; }); return o;
  }
  function kolonAdres(no) { const c = nesneBul("kolon", no) || (V() && V().bina.kolonlar.filter(function (x) { return x.no === no; })[0]); return c ? "S-" + adres(c.aks) + "/k" + c.kat : "S" + no; }
  function kirisAdres(no) { const k = nesneBul("kiris", no) || (V() && V().bina.kirisler.filter(function (x) { return x.no === no; })[0]); return k ? "K-" + adres(k.bas) + "→" + adres(k.son) + "/k" + k.kat : "K" + no; }
  function dosemeAdres(no) { const d = nesneBul("doseme", no) || (V() && V().bina.dosemeler.filter(function (x) { return x.no === no; })[0]); return d ? "D-" + adres(d.kose[0]) + "/" + adres(d.kose[1]) + "/k" + d.kat : "D" + no; }
  // Sankey kenarlarından (K→S) kiriş ucunun kolona verdiği kuvvet
  function ucKuvveti(kirisNo, kolonNo) {
    const v = V(), l = (v.akis && v.akis.sankey) || [];
    const t = {};
    l.forEach(function (e) { if (e.kaynak === "K" + kirisNo && e.hedef.indexOf("S" + kolonNo + "/") === 0) t[e.durum] = (t[e.durum] || 0) + (+e.kN || 0); });
    return akisDeger(t.G, t.Q, t.S, t.W);
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
    else if (hedef.tur === "kolon" || (hedef.tur === "temel" && !hedef.alt)) { const c = vb.kolonlar.filter(function (x) { return x.no === hedef.no; })[0]; if (c) kolonZinciri(c); }   // temel no = kat 1 kolon no
    return z;
  }
  // ---------- Genel model (surum 3) yük yolu ----------
  // panel → (sankey P→Ç) taşıyıcı çubuklar → her çubuğun alt uç(lar)ından aşağı: önce kolon türü çubuklar, yoksa aşağı inen herhangi
  // bir çubuk (çapraz), o da yoksa (çubuğun uç düğümünde) aynı kottaki taşıyıcı çubuk (ikincil kiriş → ana kiriş) → mesnet düğümleri
  function s3AkisZinciri(hedef) {
    const v = V(), ag = (v && v.ag) || {}, z = { paneller: [], cubuklar: [], kolonlar: [], mesnetler: [] };
    if (!hedef || !v) return z;
    const nd = {}, mesnet = {}, dugEl = {}, cubEl = {}, cubTur = {};
    (ag.dugumler || []).forEach(function (d) { nd[d.no] = d; });
    (ag.mesnetler || []).forEach(function (m) { mesnet[m.dugum] = m; });
    (ag.elemanlar || []).forEach(function (e) {
      if (e.cubuk == null || !Array.isArray(e.dugumler)) return;
      (cubEl[e.cubuk] = cubEl[e.cubuk] || []).push(e);
      e.dugumler.forEach(function (n) { (dugEl[n] = dugEl[n] || []).push(e); });
    });
    ((v.bina && v.bina.cubuklar) || []).forEach(function (c) { cubTur[c.no] = c.tur || "diger"; });
    const kolonMu = function (e) { return cubTur[e.cubuk] === "kolon" || e.tur === "kolon"; };
    const ziyaret = {}, kuyruk = [];
    const ekle = function (cno, kolon) { if (ziyaret[cno] || !cubEl[cno]) return; ziyaret[cno] = 1; (kolon ? z.kolonlar : z.cubuklar).push(cno); kuyruk.push(cno); };
    let bas = null;
    if (hedef.tur === "panel") {
      z.paneller.push(hedef.no);
      ((v.akis && v.akis.sankey) || []).forEach(function (e) { if (e.kaynak === "P" + hedef.no) { const c = +String(e.hedef).slice(1); if (isFinite(c)) ekle(c, false); } });
    } else if (hedef.tur === "cubuk") bas = hedef.no;
    else if (hedef.tur === "kolon" || hedef.tur === "kiris") { const r = kayitSahneden(hedef.tur, hedef.no); if (r && r.cubuk != null) bas = r.cubuk; }
    if (bas != null) ekle(+bas, (cubEl[bas] || []).some(kolonMu));
    for (let n = 0; kuyruk.length && n < 4000; n++) {
      const cno = kuyruk.shift(), els = cubEl[cno] || [];
      const say = {};
      els.forEach(function (e) { e.dugumler.forEach(function (d) { say[d] = (say[d] || 0) + 1; }); });
      const dugumler = Object.keys(say).map(Number).filter(function (d) { return nd[d]; });
      if (!dugumler.length) continue;
      const zMin = Math.min.apply(null, dugumler.map(function (d) { return nd[d].Z; }));
      dugumler.forEach(function (d) {
        if (nd[d].Z > zMin + 1e-6) return;                      // yük çubuğun alt ucundan (yatay çubukta bütün düğümlerinden) çıkar
        if (mesnet[d]) { if (z.mesnetler.indexOf(d) < 0) z.mesnetler.push(d); return; }
        const komsu = (dugEl[d] || []).filter(function (e) { return e.cubuk !== cno; });
        const asagi = komsu.filter(function (e) { const o = e.dugumler[0] === d ? e.dugumler[1] : e.dugumler[0]; return nd[o] && nd[o].Z < nd[d].Z - 1e-6; });
        const kolon = asagi.filter(kolonMu);
        let sec = kolon.length ? kolon : asagi;
        // uç düğümde aşağı inen çubuk yoksa: aynı kottaki taşıyıcıya (çubuğun ara bölme düğümünden yatay yayılma yok)
        if (!sec.length && say[d] === 1) sec = komsu.filter(function (e) { const o = e.dugumler[0] === d ? e.dugumler[1] : e.dugumler[0]; return nd[o] && Math.abs(nd[o].Z - nd[d].Z) < 1e-6; });
        sec.forEach(function (e) { ekle(e.cubuk, kolonMu(e)); });
      });
    }
    return z;
  }
  // genel model yük yolu vurgusu: panel (yarı saydam), taşıyıcı çubuklar ve kolonlar (FE düğüm koordinatlarıyla), mesnetler; etiketler formül kartı açar
  function s3AkisVurguCiz(sahne, P, b, s) {
    const v = V(), ag = v.ag || {}, z = s3AkisZinciri(D.akisHedef), d = D.akisDurum;
    const nd = {}; (ag.dugumler || []).forEach(function (x) { nd[x.no] = x; });
    const etk = [];
    const etiket = function (x, y, t, key, hiza) { etk.push({ x: x, y: y, t: t, key: key, hiza: hiza || "middle" }); };
    z.paneller.forEach(function (no) {
      const p = (B.paneller || []).filter(function (x) { return +x.no === +no; })[0], yp = ((v.yukler && v.yukler.paneller) || []).filter(function (x) { return x.no === no; })[0];
      const K = p && Array.isArray(p.kose) ? p.kose.map(refP) : null;
      if (!K || K.some(function (Q) { return !Q; })) return;
      dortgenP(sahne, P, b, K, "b3-akis-doseme", "", 2);
      if (!yp) return;
      const m = [0, 1, 2].map(function (i) { return K.reduce(function (t, Q) { return t + Q[i]; }, 0) / K.length; }), q = P(m[0], m[1], m[2]);
      const w = d === "Q" ? yp.q : d === "S" ? yp.s : d === "G" ? yp.g : (yp.g || 0) + (yp.q || 0);
      etiket(q[0], q[1] + 16, "P" + no + " · " + (d === "G+Q" ? "g+q" : d.toLowerCase()) + "=" + f1(w), "s3panel:" + no);
    });
    const cizgi = function (cno, sinif) {
      const els = (ag.elemanlar || []).filter(function (e) { return e.cubuk === cno; });
      let ust = null, alt = null;
      els.forEach(function (e) {
        const a = nd[e.dugumler[0]], c = nd[e.dugumler[1]];
        if (!a || !c) return;
        sahne.ekle(1e9, C.cizgi(P(a.X, a.Y, a.Z), P(c.X, c.Y, c.Z), sinif), 2);
        [a, c].forEach(function (x) { if (!ust || x.Z > ust.Z) ust = x; if (!alt || x.Z < alt.Z) alt = x; });
      });
      return { ust: ust, alt: alt };
    };
    const yukC = {}; ((v.yukler && v.yukler.cubuklar) || []).forEach(function (y) { yukC[y.no] = y; });
    const hedefCubuk = D.akisHedef && D.akisHedef.tur === "cubuk" ? +D.akisHedef.no : null;
    z.cubuklar.forEach(function (cno) {
      const u = cizgi(cno, "b3-akis-kiris");
      if (!u.ust || !u.alt) return;
      // etiket: hedef çubuk ve panelin doğrudan yüklediği çubuklar (kalabalık olmasın)
      if (cno !== hedefCubuk && !(z.paneller.length && z.cubuklar.indexOf(cno) < 8)) return;
      const y = yukC[cno];
      if (!y) return;
      const m = P((u.ust.X + u.alt.X) / 2, (u.ust.Y + u.alt.Y) / 2, (u.ust.Z + u.alt.Z) / 2 - 0.4);
      etiket(m[0], m[1] + 4, "Ç" + cno + " · " + f1(akisDeger((y.G || {}).toplam_kN, (y.Q || {}).toplam_kN, (y.S || {}).toplam_kN)) + " kN", "s3cubuk:" + cno);
    });
    const akK = {}; ((v.akis && v.akis.kolonlar) || []).forEach(function (k) { akK[k.no] = k; });
    z.kolonlar.forEach(function (cno) {
      const u = cizgi(cno, "b3-akis-kolon");
      if (!u.ust || !u.alt) return;
      sahne.ekle(1e9, C.ok(P(u.ust.X, u.ust.Y, u.ust.Z - 0.3), P(u.alt.X, u.alt.Y, u.alt.Z + 0.35), "b3-akis-kolon", "b3-akis-ok-o", "", ""), 2);
      const ak = akK[cno];
      if (!ak) return;
      const m = P(u.alt.X, u.alt.Y, (u.ust.Z + u.alt.Z) / 2);
      etiket(m[0] + 14, m[1] + 4, "N=" + f1(akisDeger(ak.N_kum_G, ak.N_kum_Q)), "s3kolon:" + cno, "start");
    });
    const tem = {}; tekilTemeller(v).forEach(function (t) { tem[t.dugum] = t; });
    const acik = {}; acikMesnetler(v).forEach(function (m) { acik[m.dugum] = m; });
    z.mesnetler.forEach(function (dn) {
      const x = nd[dn];
      if (!x) return;
      const p = P(x.X, x.Y, x.Z);
      sahne.ekle(1e9, '<circle class="b3-akis-mesnet" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="' + r1(7 * s) + '"/>', 2);
      const t = tem[dn], m = acik[dn];
      if (t) etiket(p[0], p[1] + 22, "σ=" + f1(t.sigma_max) + " · D/C " + f2(t.DC), "s3mesnet:" + dn);
      else if (m) etiket(p[0], p[1] + 22, "R=" + f1(akisDeger(m.N_G, m.N_Q)), "s3mesnet:" + dn);
    });
    etiketYerlestir(etk).forEach(function (e) {
      sahne.ekle(1e9, etiketKutu(e.x, e.y, e.t, "b3-akis-et", e.hiza), 2);
      hedefler.unshift({ tur: "daire", x: e.hiza === "start" ? e.x + e.w / 2 - 5 : e.x, y: e.y - 4, r: Math.max(14, e.w / 2) * s, kind: "formul", key: e.key });
    });
  }
  function akisVurguCiz(sahne, P, b, s) {
    if (V().model === "genel") { s3AkisVurguCiz(sahne, P, b, s); return; }
    const v = V(), vb = v.bina, z = akisZinciri(D.akisHedef);
    const formulHedef = function (p, key, r) { hedefler.unshift({ tur: "daire", x: p[0], y: p[1], r: (r || 20) * s, kind: "formul", key: key }); };
    const etk = [];
    const etiket = function (x, y, t, key, hiza) { etk.push({ x: x, y: y, t: t, key: key, hiza: hiza || "middle" }); };
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
      const et = D.akisDurum === "Q" ? "q=" + f1(yd.q) : D.akisDurum === "G" ? "g=" + f1(yd.g) : "g+q=" + f1(yd.g + yd.q);
      etiket(m[0], m[1] + 16, et, "doseme:" + no);
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
      etiket(m[0], m[1] - 10, (o.p.sekil === "ucgen" ? "▲" : o.p.sekil === "trapez" ? "▬" : "▭") + "w=" + f1(o.w), "pay:" + o.d.no + ":" + o.p.kiris_no);
    });
    // kiriş toplam yükü (hedef kiriş ise) ve uç kuvvetleri → kolon okları
    z.kirisler.forEach(function (kno) {
      const k = vb.kirisler.filter(function (x) { return x.no === kno; })[0], yk = (v.yukler.kirisler || []).filter(function (x) { return x.no === kno; })[0];
      if (!k || !yk) return;
      const X1 = aksX(k.bas[0]), Y1 = aksY(k.bas[1]), X2 = aksX(k.son[0]), Y2 = aksY(k.son[1]), Z = katKot(k.kat);
      sahne.ekle(1e9, C.cizgi(P(X1, Y1, Z), P(X2, Y2, Z), "b3-akis-kiris"), 2);
      if (D.akisHedef.tur === "kiris") {
        const q = kirisKNm(yk, D.akisDurum).toplam;
        const m = P((X1 + X2) / 2, (Y1 + Y2) / 2, Z - 0.6);
        etiket(m[0], m[1] + 4, "q=" + f1(q) + " · " + f1(akisDeger(yk.G.toplam_kN, yk.Q.toplam_kN)) + " kN", "kiris:" + kno);
      }
      [k.bas, k.son].forEach(function (a) {
        const c = vb.kolonlar.filter(function (x) { return aksEsit(x.aks, a) && x.kat === k.kat; })[0];
        if (!c) return;
        const X = aksX(a[0]), Y = aksY(a[1]), R = ucKuvveti(kno, c.no);
        const p0 = P(X, Y, Z + 0.9), p1 = P(X, Y, Z + 0.15);
        sahne.ekle(1e9, C.ok(p0, p1, "b3-akis-ok-c", "b3-akis-ok-o", "", ""), 2);
        etiket(p0[0] + 10, p0[1] - 6, "R=" + f1(R), "uc:" + kno + ":" + c.no, "start");
      });
    });
    // kolon şeridi: kümülatif N
    z.kolonlar.forEach(function (cno) {
      const c = vb.kolonlar.filter(function (x) { return x.no === cno; })[0], ak = (v.akis.kolonlar || []).filter(function (x) { return x.no === cno; })[0];
      if (!c || !ak) return;
      const X = aksX(c.aks[0]), Y = aksY(c.aks[1]), z0 = katKot(c.kat - 1), z1 = katKot(c.kat);
      sahne.ekle(1e9, C.ok(P(X, Y, z1 - 0.3), P(X, Y, z0 + 0.35), "b3-akis-kolon", "b3-akis-ok-o", "", ""), 2);
      const m = P(X, Y, (z0 + z1) / 2);
      etiket(m[0] + 14, m[1] + 4, "N=" + f1(akisDeger(ak.N_kum_G, ak.N_kum_Q)), "kolon:" + cno, "start");
    });
    // temeller
    z.temeller.forEach(function (cno) {
      const t = tekilTemeller(v).filter(function (x) { return x.kolon_no === cno; })[0];
      if (!t || !Array.isArray(t.aks)) return;
      const X = aksX(t.aks[0]), Y = aksY(t.aks[1]), th = (vb.temeller.varsayilan && vb.temeller.varsayilan.h) || 0.6, zt = (katKot(0) || 0) - th;
      // basınç trapezi (X doğrultusunda B genişliğinde): σmin … σmax
      const sm = Math.max(t.sigma_max, 1e-9), hs = 0.5;
      const pts = [P(X - t.B / 2, Y, zt), P(X + t.B / 2, Y, zt), P(X + t.B / 2, Y, zt - hs * t.sigma_max / sm), P(X - t.B / 2, Y, zt - hs * Math.max(0, t.sigma_min) / sm)];
      sahne.ekle(1e9, C.cokgen(pts, "b3-akis-temel"), 2);
      const m = P(X, Y, zt - hs - 0.35);
      etiket(m[0], m[1] + 8, "σ=" + f1(t.sigma_max) + " · D/C " + f2(t.DC), "temel:" + cno);
    });
    // etiketler: önce kutu ölçüleri, sonra basit çarpışma önleme (çakışanlar dikey açılır), sonra sahneye ve vuruş listesine
    etiketYerlestir(etk).forEach(function (e) {
      sahne.ekle(1e9, etiketKutu(e.x, e.y, e.t, "b3-akis-et", e.hiza), 2);
      formulHedef([e.hiza === "start" ? e.x + e.w / 2 - 5 : e.x, e.y - 4], e.key, Math.max(14, e.w / 2));
    });
  }
  function etiketYerlestir(etk) {
    const h = 17;
    etk.forEach(function (e) { e.w = 6.0 * e.t.length + 10; });
    const kutu = function (e) { return { x0: e.hiza === "start" ? e.x - 5 : e.x - e.w / 2, y0: e.y - 12, x1: (e.hiza === "start" ? e.x - 5 : e.x - e.w / 2) + e.w, y1: e.y - 12 + h }; };
    etk.sort(function (a, b) { return a.y - b.y || a.x - b.x; });
    for (let tur = 0; tur < 3; tur++) {
      let degisti = false;
      for (let i = 0; i < etk.length; i++) {
        for (let j = 0; j < i; j++) {
          const a = kutu(etk[j]), b = kutu(etk[i]);
          if (b.x0 < a.x1 - 1 && b.x1 > a.x0 + 1 && b.y0 < a.y1 - 1 && b.y1 > a.y0 + 1) { etk[i].y += a.y1 - b.y0 + 2; degisti = true; }
        }
      }
      if (!degisti) break;
    }
    return etk;
  }
  function etiketKutu(x, y, t, sinif, hiza) {
    const w = 6.0 * t.length + 10, h = 17, ax = hiza === "start" ? x - 5 : x - w / 2;
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
    let baslik = "", tex = "", not = "", adim = "doseme";
    if (tur === "doseme") {
      const d = v.yukler.dosemeler.filter(function (x) { return x.no === +p[1]; })[0], vb = v.bina.dosemeler.filter(function (x) { return x.no === +p[1]; })[0];
      if (!d) return;
      baslik = dosemeAdres(d.no) + " — döşeme yükleri (TS 498:2021)";
      tex = "g = \\gamma_b h + g_{ek} = 25\\cdot" + f2(vb ? vb.h : 0).replace(",", "{,}") + " + " + f2(vb ? vb.g_ek : 0).replace(",", "{,}") + " = " + f2(d.g).replace(",", "{,}") + "\\ \\text{kN/m}^2,\\quad q = " + f2(d.q).replace(",", "{,}") + "\\ \\text{kN/m}^2";
      not = "l_k = " + f2(Math.min(d.lx, d.ly)) + " m, l_u = " + f2(Math.max(d.lx, d.ly)) + " m, m = l_u/l_k = " + f2(d.m) + (d.tip === "cift" ? " ≤ 2 → çift doğrultulu (45° kuralı)" : " > 2 → tek doğrultulu") + ". Toplam G = " + f1(d.G_toplam) + " kN, Q = " + f1(d.Q_toplam) + " kN.";
      adim = "yukler";
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
      const kg = kirisKNm(yk, "G"), kq = kirisKNm(yk, "Q"), q = kirisKNm(yk, D.akisDurum).toplam, L = yk.L;
      baslik = kirisAdres(yk.no) + " — yük dökümü ve el hesabı";
      tex = "q = q_{d} + q_{duvar} + q_{öz} + q_{ek} = " + [kg.doseme, kg.duvar, kg.oz, kg.ek].map(function (x) { return f2(D.akisDurum === "Q" ? 0 : x).replace(",", "{,}"); }).join(" + ") + (D.akisDurum !== "G" ? " + " + f2(kq.doseme + kq.ek).replace(",", "{,}") + "\\,(Q)" : "") + " = " + f2(q).replace(",", "{,}") + "\\ \\text{kN/m}";
      tex += "\\\\ R \\approx \\frac{qL}{2} = " + f1(q * L / 2).replace(",", "{,}") + "\\ \\text{kN},\\quad M_{orta} \\approx \\frac{qL^2}{8} = " + f1(q * L * L / 8).replace(",", "{,}") + "\\ \\text{kN·m}";
      const e = agEleman("kiris", yk.no)[0], ks = e && durumKisa(D.akisDurum), es = ks && elSonuc(ks, e.no);
      if (es) not = "FE (bu durum): M_maks = " + f1(enBuyuk(es.M)) + " kN·m, V_maks = " + f1(enBuyuk(es.V)) + " kN. Basit kiriş değeri ile fark süreklilik ve uç ankastreliğinden gelir.";
      adim = "kiris";
    } else if (tur === "uc") {
      const R = ucKuvveti(+p[1], +p[2]), yk = v.yukler.kirisler.filter(function (x) { return x.no === +p[1]; })[0];
      baslik = kirisAdres(+p[1]) + " ucu → " + kolonAdres(+p[2]);
      tex = "R_{FE} = " + f1(R).replace(",", "{,}") + "\\ \\text{kN}" + (yk ? ",\\qquad R_{basit} = \\frac{qL}{2} = " + f1(akisDeger(yk.el_hesabi.R_G, yk.el_hesabi.R_Q)).replace(",", "{,}") + "\\ \\text{kN}" : "");
      not = "Kiriş uç kesmesi kolona düşey yük olarak iner; FE değeri sürekliliği hesaba katar."; adim = "akis";
    } else if (tur === "kolon") {
      const ak = v.akis.kolonlar.filter(function (x) { return x.no === +p[1]; })[0];
      if (!ak) return;
      baslik = kolonAdres(ak.no) + " — kolon birikimi";
      tex = "N_{kat} = " + f1(akisDeger(ak.N_G, ak.N_Q)).replace(",", "{,}") + "\\ \\text{kN},\\quad N_{küm} = \\sum_{üst\\ katlar} N_{kat} = " + f1(akisDeger(ak.N_kum_G, ak.N_kum_Q)).replace(",", "{,}") + "\\ \\text{kN}";
      tex += "\\\\ N_{trib} = \\sum (g+q)A_{trib} + \\text{kiriş/duvar payları} + \\text{kolon öz} = " + f1(akisDeger(ak.N_trib_G, ak.N_trib_Q)).replace(",", "{,}") + "\\ \\text{kN}" + (ak.A_trib != null ? "\\quad (A_{trib} = " + f2(ak.A_trib).replace(",", "{,}") + "\\ \\text{m}^2)" : "");
      not = "Fark: " + f1(ak.fark_yuzde) + " % (FE − yük alanı). Yük alanı yöntemi rijitlik ve sürekliliği görmez; FE komşu açıklıkların paylaşımını hesaplar."; adim = "akis";
    } else if (tur === "temel") {
      const t = tekilTemeller(v).filter(function (x) { return x.kolon_no === +p[1]; })[0];
      if (!t) return;
      baslik = "Temel " + temelEtiketi(t) + " — taban basıncı (servis G+Q)";
      tex = "\\sigma_{max,min} = \\frac{N}{BL} \\pm \\frac{6M_X}{BL^2} \\pm \\frac{6M_Y}{LB^2} = \\frac{" + f1(t.N_servis).replace(",", "{,}") + "}{" + f2(t.B).replace(",", "{,}") + "\\cdot" + f2(t.L).replace(",", "{,}") + "} \\pm \\ldots = " + f1(t.sigma_max).replace(",", "{,}") + "\\ /\\ " + f1(t.sigma_min).replace(",", "{,}") + "\\ \\text{kN/m}^2";
      tex += "\\\\ e_X = " + f2(t.e_X).replace(",", "{,}") + "\\ \\text{m},\\ e_Y = " + f2(t.e_Y).replace(",", "{,}") + "\\ \\text{m}" + (t.cekirdek_icinde ? "\\ (\\le B/6: \\text{çekirdek içinde})" : "\\ (\\text{çekirdek dışında!})") + ",\\quad D/C = \\frac{\\sigma_{max}}{q_{em}} = " + f2(t.DC).replace(",", "{,}");
      not = "q_em = " + f1(t.q_em) + " kN/m². Temel ebatları: B = " + f2(t.B) + " m, L = " + f2(t.L) + " m."; adim = "akis";
    } else if (tur === "s3panel") {
      // genel model paneli: yüzey yükleri ve taşıyıcı kenar payları (veri.yukler.paneller)
      const yp = ((v.yukler && v.yukler.paneller) || []).filter(function (x) { return x.no === +p[1]; })[0];
      if (!yp) return;
      baslik = "Panel P" + yp.no + " — yükler ve kenar payları";
      tex = "G = g\\,A = " + f2(yp.g).replace(",", "{,}") + "\\cdot" + f2(yp.alan).replace(",", "{,}") + " = " + f1(yp.G_toplam).replace(",", "{,}") + "\\ \\text{kN},\\quad Q = " + f1(yp.Q_toplam).replace(",", "{,}") +
        "\\ \\text{kN}" + (yp.S_toplam ? ",\\quad S = " + f1(yp.S_toplam).replace(",", "{,}") + "\\ \\text{kN}" : "");
      not = "Dağıtım: " + (yp.dagitim || "iki") + "; eğim " + f1(yp.egim) + "°. Kenar payları (m²): " + (yp.kenarlar || []).map(function (k) { return k.kenar + ": " + f2(k.pay) + " → Ç" + (k.cubuklar || []).join(", Ç") + (k.sekil && k.sekil !== "yok" ? " (" + k.sekil + ")" : ""); }).join(" · ") +
        (yp.q_kaynak ? ". q: " + yp.q_kaynak : "") + ".";
      adim = "yukler";
    } else if (tur === "s3cubuk") {
      const y = ((v.yukler && v.yukler.cubuklar) || []).filter(function (x) { return x.no === +p[1]; })[0];
      if (!y) return;
      const G = y.G || {}, Q = y.Q || {}, S = y.S || {};
      baslik = "Çubuk Ç" + y.no + " — yük dökümü (L = " + f2(y.L) + " m)";
      tex = "G = G_{öz} + G_{panel} + G_{duvar} + G_{ek} = " + [G.oz, G.panel, G.duvar, G.ek].map(function (x) { return f1(+x || 0).replace(",", "{,}"); }).join(" + ") + " = " + f1(G.toplam_kN).replace(",", "{,}") + "\\ \\text{kN}" +
        ",\\quad Q = " + f1(+Q.toplam_kN || 0).replace(",", "{,}") + "\\ \\text{kN}" + (S.toplam_kN ? ",\\quad S = " + f1(S.toplam_kN).replace(",", "{,}") + "\\ \\text{kN}" : "");
      // panel payları durum durum (motor hangi durumlar için P → Ç bandı verdiyse)
      // yalnız panel → çubuk kenarları (sözleşme C15: tur "panel-cubuk"; tursuz eski kayıt da öyle); çubuktan / düğüm yükünden gelenler ayrı
      const pay = ((v.akis && v.akis.sankey) || []).filter(function (e) { return e.hedef === "Ç" + y.no && +e.kN > 1e-9 && (e.tur == null || e.tur === "panel-cubuk"); }), payD = {};
      pay.forEach(function (e) { (payD[e.durum] = payD[e.durum] || []).push(e); });
      const payMetni = Object.keys(payD).sort(function (a, b) { return "GQSW".indexOf(a.charAt(0)) - "GQSW".indexOf(b.charAt(0)); }).map(function (d) {
        return "Panel payları (" + d + "): " + payD[d].map(function (e) { return e.kaynak + " " + f1(e.kN) + " kN"; }).join(", ") + ". ";
      }).join("");
      not = payMetni + "q_G = G/L = " + f2((+G.toplam_kN || 0) / (y.L || 1)) + " kN/m.";
      adim = "yukler";
    } else if (tur === "s3kolon") {
      const ak = ((v.akis && v.akis.kolonlar) || []).filter(function (x) { return x.no === +p[1]; })[0];
      if (!ak) return;
      baslik = "Kolon " + akisKolonAdi(ak) + " — kolon birikimi";
      tex = "N_{kat} = " + f1(akisDeger(ak.N_G, ak.N_Q)).replace(",", "{,}") + "\\ \\text{kN},\\quad N_{küm} = " + f1(akisDeger(ak.N_kum_G, ak.N_kum_Q)).replace(",", "{,}") + "\\ \\text{kN}";
      not = "N_küm kolonun alt ucundaki eksenel kuvvettir (sonlu eleman); N_kat üstündeki kolonların payı düşülmüş kısmıdır."; adim = "akis";
    } else if (tur === "s3mesnet") {
      const dn = +p[1], t = tekilTemeller(v).filter(function (x) { return x.dugum === dn; })[0], m = acikMesnetler(v).filter(function (x) { return x.dugum === dn; })[0];
      if (t) {
        baslik = "Temel " + temelEtiketi(t) + " — taban basıncı (servis G+Q)";
        tex = "\\sigma_{max} = \\frac{N}{BL} + \\frac{6M_X}{BL^2} + \\frac{6M_Y}{LB^2} = " + f1(t.sigma_max).replace(",", "{,}") + "\\ \\text{kN/m}^2,\\quad D/C = \\frac{\\sigma_{max}}{q_{em}} = " + f2(t.DC).replace(",", "{,}");
        not = "N = " + f1(t.N_servis) + " kN (temel öz ağırlığı dahil), B × L = " + f2(t.B) + " × " + f2(t.L) + " m, q_em = " + f1(t.q_em) + " kN/m².";
      } else if (m) {
        baslik = "Mesnet " + (m.adres || dugumAdresV(v, dn)) + " — tepki (" + (m.tip ? mesnetTipEtiketi(v, m) : "mesnet") + ")";
        tex = "R_Z = N_G + N_Q = " + f1(m.N_G).replace(",", "{,}") + " + " + f1(m.N_Q).replace(",", "{,}") + " = " + f1((+m.N_G || 0) + (+m.N_Q || 0)).replace(",", "{,}") + "\\ \\text{kN}";
        not = "Açık mesnet temel değildir: taban basıncı tahkiki yapılmaz.";
      } else return;
      adim = "akis";
    }
    D.formul = key;
    ref.formul.classList.remove("gizli");
    ref.formul.innerHTML = '<div class="bn-formul-ust"><b>' + kacis(baslik) + '</b><button type="button" class="bn-firca-kapat" id="bn-formul-kapat" aria-label="Kapat">✕</button></div>' + katex(tex) + (not ? '<p class="not">' + kacis(not) + "</p>" : "") +
      '<button type="button" class="dugme kucuk" data-adim="' + adimNo(adim) + '">Anlatımda gör</button>';
  }
  // ---------- Oynat ----------
  function oynatToggle() {
    const v = V(); if (!v) return;
    if (D.oynat) { clearTimeout(D.oynat); D.oynat = 0; akisKontrol(); return; }
    // genel modelde paneller (yalnız yük dağıtanlar), aks–kat modelinde döşemeler sırayla
    const genel = v.model === "genel", tur = genel ? "panel" : "doseme";
    const liste = genel ? (v.yukler.paneller || []).filter(function (p) { return p.dagitim !== "yok"; }).map(function (p) { return p.no; }) : (v.yukler.dosemeler || []).map(function (d) { return d.no; });
    if (!liste.length) { A.toast(genel ? "Yük dağıtan panel yok." : "Döşeme yok."); return; }
    let i = 0;
    const adim = function () {
      D.akisHedef = { tur: tur, no: liste[i] }; D.secim = [{ tur: tur, no: liste[i] }];
      const d = genel ? null : v.bina.dosemeler.filter(function (x) { return x.no === liste[i]; })[0];
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
  // Seçili akış durumunun (G, Q, S, W ya da "G+Q" gibi birleşim) kenar durumları
  function akisDurumKumesi(d) { return String(d || "G").split("+").map(function (x) { return x.trim(); }).filter(Boolean); }
  function sankeyHtml(W) {
    const v = V(), ed = {}, kume = akisDurumKumesi(D.akisDurum), varDurum = {};
    // kenarlar durumlarına göre (genel okuma: motor hangi durumlar için bant verdiyse); birleşimde ("G+Q") her durumun bantları toplanır
    (v.akis.sankey || []).forEach(function (e) {
      if (+e.kN > 1e-6) varDurum[e.durum] = true;
      if (kume.indexOf(e.durum) < 0) return;
      const k = e.kaynak + ">" + e.hedef;
      ed[k] = ed[k] || { kaynak: e.kaynak, hedef: e.hedef, kN: 0, d: {} };
      ed[k].kN += +e.kN || 0;
      ed[k].d[e.durum] = (ed[k].d[e.durum] || 0) + (+e.kN || 0);
    });
    const kenarlar = Object.keys(ed).map(function (k) { return ed[k]; }).filter(function (e) { return e.kN > 1e-6; });
    const eksik = kume.filter(function (d) { return !varDurum[d]; });
    const genelNot = v.model === "genel" && Object.keys(varDurum).length ?
      "Genel modelde motor bu yük durumu (" + eksik.join(", ") + ") için akış bandı üretmedi; panel ve çubuk payları Tablolar › Panel yükleri ve Çubuk yükleri tablolarında." : "";
    if (!kenarlar.length) return '<p class="not bn-akis-yok">' + kacis(genelNot || "Bu durum için akış verisi yok.") + "</p>";
    // birleşimde bir durumun bandı yoksa şema yalnız ötekileri gösterir: bunu söyle
    let kismiNot = eksik.length ? '<p class="not bn-akis-kismi">' + kacis("Şema yalnız " + kume.filter(function (d) { return varDurum[d]; }).join(" + ") + " bantlarını gösteriyor; " +
      eksik.join(", ") + " için akış verisi yok" + (genelNot ? " (Tablolar › Panel yükleri)" : "") + ".") + "</p>" : "";
    // motor durum başına kenar sayısını sınırladıysa (en büyükler kaldı; sözleşme C15 sankey_kesildi) söylenir
    const kesildi = v.akis.sankey_kesildi && typeof v.akis.sankey_kesildi === "object" ? kume.reduce(function (t, d) { return t + (+v.akis.sankey_kesildi[d] || 0); }, 0) : 0;
    if (kesildi > 0) kismiNot += '<p class="not bn-akis-kesildi">' + kacis("Akış şemasında en büyük kenarlar gösterildi (" + kesildi + " kenar atlandı).") + "</p>";
    const ust = ustKatV(v);
    // aks–kat şeması D → K → S/N (kat kat) → T → Z; genel model (P panel → Ç çubuk, motor başka önek de verebilir) sütunları grafikteki
    // düzeye göre (kaynaksız düğüm 0; her kenar hedefi en az kaynağının bir sağı), P her zaman 0, Ç en az 1
    const AKS_KAT_ONEK = { D: 1, K: 1, S: 1, N: 1, T: 1, Z: 1 };
    const genelSema = v.model === "genel" || kenarlar.some(function (e) { return !AKS_KAT_ONEK[e.kaynak.charAt(0)] || !AKS_KAT_ONEK[e.hedef.charAt(0)]; });
    const duzey = {}, gs = genelSema ? genelSankeyDuzeni(v, kenarlar) : null;
    if (gs) Object.assign(duzey, gs.duzey);
    const sutun = function (id) {
      if (genelSema) return duzey[id] || 0;
      if (id.charAt(0) === "D") return 0;
      if (id.charAt(0) === "K") return 1;
      if (id.charAt(0) === "S" || id.charAt(0) === "N") { const m = /\/k(\d+)/.exec(id); return 2 + (m ? ust - (+m[1]) : 0); }
      if (id.charAt(0) === "T") return 2 + ust;
      return 3 + ust;
    };
    const dugum = {};
    kenarlar.forEach(function (e) {
      [e.kaynak, e.hedef].forEach(function (id) { dugum[id] = dugum[id] || { id: id, s: sutun(id), giren: 0, cikan: 0 }; });
      dugum[e.kaynak].cikan += e.kN; dugum[e.hedef].giren += e.kN;
    });
    const katBul = function (id) {
      if (gs) return gs.kat(id);
      // D{no}, K{no} → bina kat numarası (kat kat gruplama); S/N düğümlerinde /k<kat>
      const m = /\/k(\d+)/.exec(id);
      if (m) return +m[1];
      const no = parseInt(id.slice(1), 10), liste = id.charAt(0) === "D" ? v.bina.dosemeler : id.charAt(0) === "K" ? v.bina.kirisler : null;
      const n = liste && liste.filter(function (x) { return x.no === no; })[0];
      return n ? n.kat : 0;
    };
    const sutunlar = [];
    Object.keys(dugum).forEach(function (id) { const n = dugum[id]; n.akis = Math.max(n.giren, n.cikan); n.kat = katBul(id); (sutunlar[n.s] = sutunlar[n.s] || []).push(n); });
    const enCok = sutunlar.reduce(function (m, l) { return Math.max(m, l ? l.length : 0); }, 0);
    const nS = sutunlar.length, bosluk = enCok > 24 ? 3 : 6, katBoslugu = 12, pl = 58, pr = 70, gw = 14;
    const H = Math.max(360, Math.min(960, enCok * (enCok > 24 ? 12 : 16) + 80));
    // kalabalık şemada (40+ kirişli aks–kat binası; genel modelde bir sütunda 30'dan çok düğüm) eleman etiketleri yalnız seçilince
    const cokKiris = genelSema ? enCok > 30 : (v.bina.kirisler || []).length >= 40;
    const yogunMu = function (id) { return genelSema || id.charAt(0) === "D" || id.charAt(0) === "K"; };
    let maksToplam = 0, maksBosluk = 0;
    sutunlar.forEach(function (l) {
      if (!l) return;
      l.sort(function (a, b) { return b.kat - a.kat || a.id.localeCompare(b.id, "tr", { numeric: true }); });
      const t = l.reduce(function (s, n) { return s + n.akis; }, 0);
      let katSayisi = 0; l.forEach(function (n, i) { if (i && n.kat !== l[i - 1].kat) katSayisi++; });
      maksToplam = Math.max(maksToplam, t); maksBosluk = Math.max(maksBosluk, bosluk * (l.length - 1) + katBoslugu * katSayisi);
    });
    const olcek = (H - 40 - maksBosluk) / (maksToplam || 1);
    const sx = function (s) { return pl + (nS > 1 ? s * (W - pl - pr) / (nS - 1) : 0); };
    let svg = "";
    sutunlar.forEach(function (l, s) {
      if (!l) return;
      let toplamH = 0;
      l.forEach(function (n, i) { toplamH += Math.max(2, n.akis * olcek) + (i ? bosluk + (n.kat !== l[i - 1].kat ? katBoslugu : 0) : 0); });
      let y = 20 + (H - 40 - toplamH) / 2;
      l.forEach(function (n, i) { if (i && n.kat !== l[i - 1].kat) y += katBoslugu; n.x = sx(s); n.y = y; n.h = Math.max(2, n.akis * olcek); n.gy = n.y; n.cy = n.y; y += n.h + bosluk; });
    });
    if (cokKiris) svg += metinSvg(W / 2, H - 6, (genelSema ? "Panel ve çubuk" : "Kiriş ve döşeme") + " etiketleri için bir düğüme dokunun.", "bn-sankey-not", "middle");
    if (gs) {
      // grup başlığı grubun sütunlarının ortasında (bir grup birden çok sütun: kirişten kirişe, üst kolondan alt kolona aktarım)
      gs.gruplar.forEach(function (g) { svg += metinSvg((sx(g.ilk) + sx(g.son)) / 2 + gw / 2, 12, g.ad, "bn-sankey-bsl", "middle"); });
    } else {
      const basliklar = ["Döşemeler", "Kirişler"];
      for (let k = ust; k >= 1; k--) basliklar.push("Kolon k" + k);
      basliklar.push("Temeller", "Zemin");
      basliklar.forEach(function (bsl, s) { if (sutunlar[s]) svg += metinSvg(sx(s) + gw / 2, 12, bsl, "bn-sankey-bsl", "middle"); });
    }
    const dAd = function (id) { return gs ? gs.ad(id) : id; };
    const durumMetni = function (e) {
      const ks = Object.keys(e.d || {});
      return ks.length > 1 ? " (" + ks.map(function (d) { return d + " " + f1(e.d[d]); }).join(" + ") + ")" : " (" + (ks[0] || D.akisDurum) + ")";
    };
    const secim = D.sankeySecim;
    kenarlar.sort(function (a, b) { return a.kaynak.localeCompare(b.kaynak, "tr", { numeric: true }); });
    kenarlar.forEach(function (e) {
      const a = dugum[e.kaynak], b = dugum[e.hedef], w = Math.max(1.2, e.kN * olcek);
      const x0 = a.x + gw, x1 = b.x, y0 = a.cy, y1 = b.gy;
      a.cy += w; b.gy += w;
      const cx = (x0 + x1) / 2;
      const d = "M" + pt(x0, y0) + " C" + pt(cx, y0) + " " + pt(cx, y1) + " " + pt(x1, y1) + " L" + pt(x1, y1 + w) + " C" + pt(cx, y1 + w) + " " + pt(cx, y0 + w) + " " + pt(x0, y0 + w) + " Z";
      const ilgili = !secim || e.kaynak === secim || e.hedef === secim;
      svg += '<path class="bn-sankey-bant' + (secim ? (ilgili ? " aktif" : " soluk") : "") + '" d="' + d + '"><title>' + kacis(dAd(e.kaynak) + " → " + dAd(e.hedef) + ": " + f1(e.kN) + " kN" + durumMetni(e)) + "</title></path>";
    });
    const bagli = {};
    if (secim) kenarlar.forEach(function (e) { if (e.kaynak === secim) bagli[e.hedef] = 1; if (e.hedef === secim) bagli[e.kaynak] = 1; });
    Object.keys(dugum).forEach(function (id) {
      const n = dugum[id];
      const ad = gs ? gs.ad(id) : id.charAt(0) === "S" ? "S" + id.slice(1).replace(/\/k\d+/, "") : id.indexOf("T-") === 0 ? id.slice(2) : id.indexOf("N-") === 0 ? id.slice(2).replace(/\/k\d+/, "") : id;
      // 40+ kirişli binada döşeme/kiriş etiketleri yalnız seçili düğüm ve komşuları için gösterilir
      const etiketGoster = !(cokKiris && yogunMu(id)) || secim === id || bagli[id];
      svg += '<g class="bn-sankey-dugum' + (secim === id ? " aktif" : "") + '" data-sankey="' + kacis(id) + '" tabindex="0" role="button" aria-label="' + kacis(id + " " + f1(n.akis) + " kN") + '"><rect x="' + r1(n.x) + '" y="' + r1(n.y) + '" width="' + gw + '" height="' + r1(n.h) + '" rx="2"><title>' + kacis(ad + " " + f1(n.akis) + " kN (" + D.akisDurum + ")") + "</title></rect>" +
        (etiketGoster ? metinSvg(n.s === 0 ? n.x - 4 : n.x + gw + 4, n.y + n.h / 2 + 3.5, ad + " " + f1(n.akis), "bn-sankey-t", n.s === 0 ? "end" : "start") : "") + "</g>";
    });
    return kismiNot + '<svg class="se-svg bn-sankey-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Yük akışı şeması (' + kacis(D.akisDurum) + ')">' + svg + "</svg>";
  }
  function ustKatV(v) { return v.bina.katlar.reduce(function (m, k) { return Math.max(m, k.no); }, 0); }
  /**
   * Genel model akış şeması düzeni (sözleşme C15): sütunlar paneller ve düğüm yükleri (P, D) → yatay çubuklar → düşey ve eğik çubuklar
   * (|ΔZ| > 0,5·L) → mesnetler (M). Aynı gruptaki aktarım zincirleri (kirişten kirişe, üst kolondan alt kolona) grubun içinde sağa doğru
   * alt sütunlara dizilir. Dönüş: {duzey: {id: sütun}, gruplar: [{ad, ilk, son}], kat(id), ad(id)}; çubuk adları Türkçe tür adıyla.
   */
  function genelSankeyDuzeni(v, kenarlar) {
    const ag = v.ag || {}, nd = {}, cb = {}, pn = {};
    (ag.dugumler || []).forEach(function (d) { nd[d.no] = d; });
    (ag.cubuklar || []).forEach(function (c) { cb[c.no] = c; });
    ((v.yukler && v.yukler.paneller) || []).forEach(function (p) { pn[p.no] = p; });
    const no = function (id) { return parseInt(String(id).slice(1), 10); };
    const grup = function (id) {
      const o = id.charAt(0);
      if (o === "P" || o === "D") return 0;
      if (o === "M") return 3;
      const c = o === "Ç" ? cb[no(id)] : null, a = c && nd[c.i], b = c && nd[c.j];
      if (a && b) {
        const L = +c.L > 0 ? +c.L : Math.hypot(b.X - a.X, b.Y - a.Y, b.Z - a.Z);
        if (L > 0 && Math.abs(b.Z - a.Z) > 0.5 * L) return 2;
      }
      return 1;
    };
    const ids = {};
    kenarlar.forEach(function (e) { ids[e.kaynak] = grup(e.kaynak); ids[e.hedef] = grup(e.hedef); });
    const ic = {};
    Object.keys(ids).forEach(function (id) { ic[id] = 0; });
    for (let tur = 0, degisti = true; degisti && tur < 24; tur++) {
      degisti = false;
      kenarlar.forEach(function (e) {
        const g = ids[e.hedef];
        if ((g === 1 || g === 2) && ids[e.kaynak] === g && ic[e.hedef] < ic[e.kaynak] + 1 && ic[e.kaynak] < 8) { ic[e.hedef] = ic[e.kaynak] + 1; degisti = true; }
      });
    }
    // her grubun alt sütun sayısı; boş grup sütun almaz
    const n = [0, 0, 0, 0];
    Object.keys(ids).forEach(function (id) { const g = ids[id]; n[g] = Math.max(n[g], (g === 1 || g === 2 ? ic[id] : 0) + 1); });
    const bas = [0, n[0], n[0] + n[1], n[0] + n[1] + n[2]];
    const duzey = {};
    Object.keys(ids).forEach(function (id) { const g = ids[id]; duzey[id] = bas[g] + (g === 1 || g === 2 ? ic[id] : 0); });
    const varP = Object.keys(ids).some(function (id) { return id.charAt(0) === "P"; }), varD = Object.keys(ids).some(function (id) { return id.charAt(0) === "D"; });
    const AD = [varP && varD ? "Paneller ve düğüm yükleri" : varD ? "Düğüm yükleri" : "Paneller", "Yatay çubuklar", "Düşey ve eğik çubuklar", "Mesnetler"];
    const gruplar = [];
    [0, 1, 2, 3].forEach(function (g) { if (n[g]) gruplar.push({ ad: AD[g], ilk: bas[g], son: bas[g] + n[g] - 1 }); });
    return {
      duzey: duzey, gruplar: gruplar,
      kat: function (id) {
        const o = id.charAt(0), k = no(id);
        if (o === "Ç") return cb[k] ? +cb[k].kat || 0 : 0;
        if (o === "D" || o === "M") return nd[k] ? +nd[k].kat || 0 : 0;
        if (o === "P") return pn[k] ? +pn[k].kat || 0 : 0;
        return 0;
      },
      ad: function (id) {
        const o = id.charAt(0), k = no(id);
        if (o === "Ç") return cb[k] ? adresTurkce("Ç" + k + " (" + (cb[k].tur || "diger") + ")") : id;
        if (o === "M") return nd[k] && nd[k].adres ? "M " + nd[k].adres : id;
        if (o === "D") return nd[k] && nd[k].adres ? "D " + nd[k].adres : id;
        return id;
      },
    };
  }
  // ---------- Korunum ve tablolar ----------
  function korunumHtml() {
    const v = V(), d = D.akisDurum;
    const kr = (v.akis && v.akis.korunum) || {};
    const al = function (anahtar) { const g = kr.G || {}, q = kr.Q || {}, s = kr.S || {}; return akisDeger(g[anahtar], q[anahtar], s[anahtar]); };
    // genel model (surum 3): panel + çubuk öz + duvar + ek = toplam = Σ kolon tabanı (yaylar dahil) = Σ mesnet tepkisi (+ yay); aks–kat
    // anahtarları (döşeme, kiriş öz, kiriş girdisi) bu çözümde yoktur
    if (v.model === "genel" || (kr.G && kr.G.paneller != null)) {
      // mütemadi / radye: temel kirişi / plak öz ağırlığı (temel_oz) toplamdadır; tabanlar Winkler ağına oturur (zemin yayları "yay"da)
      const to = al("temel_oz") || 0;
      const a = al("paneller") + al("cubuk_oz") + al("duvarlar") + (al("ek") || 0) + to, c = al("toplam"), dd = al("kolon_taban"), e = al("temel"), yay = al("yay") || 0;
      const sayilar = [["Panel + çubuk öz + duvar + ek" + (Math.abs(to) > 1e-9 ? " + temel öz" : ""), a], ["Toplam yük", c], ["Σ kolon tabanı N" + (Math.abs(yay) > 1e-9 ? " (yaylar dahil)" : ""), dd],
        [Math.abs(yay) > 1e-9 ? "Σ mesnet tepkisi " + f1(e) + " + yay " + f1(yay) : "Σ mesnet tepkisi", e + yay]];
      const tol = 0.01 * Math.max(1, Math.abs(c));
      const tamam = Math.abs(a - c) < tol && Math.abs(c - dd) < tol && Math.abs(dd - e - yay) < tol;
      return '<div class="bn-korunum ' + (tamam ? "tamam" : "sorun") + '"><b>Korunum (' + kacis(d) + "): " + (tamam ? "✓ dört sayı eşit" : "⚠ fark var") + "</b><div class=\"bn-korunum-sayilar\">" +
        sayilar.map(function (s) { return '<span><small>' + kacis(s[0]) + "</small><b>" + f1(s[1]) + " kN</b></span>"; }).join('<span class="bn-korunum-es" aria-hidden="true">=</span>') + "</div></div>";
    }
    const kirisGirdi = (v.yukler.kirisler || []).reduce(function (t, k) { return t + akisDeger(k.G.toplam_kN, k.Q.toplam_kN); }, 0);
    const a = al("dosemeler") + al("duvarlar") + al("kiris_oz") + (al("ek") || 0), c = al("toplam"), dd = al("kolon_taban"), e = al("temel");
    // mütemadi / radye: temel kirişi / plak öz ağırlığı modelde (temel_oz); toplam onu içerir, kolon tabanı içermez
    const to = al("temel_oz") || 0, tm = to > 1e-9;
    const sayilar = tm ? [["Döşeme + duvar + kiriş öz + ek", a], ["Kiriş girdisi (Σ q·L)", kirisGirdi], ["+ kolon öz = üst yapı", c - to], ["Σ kolon tabanı N", dd], ["+ temel öz " + f1(to) + " = Σ zemin yayı", e]]
      : [["Döşeme + duvar + kiriş öz + ek", a], ["Kiriş girdisi (Σ q·L)", kirisGirdi], ["+ kolon öz = toplam", c], ["Σ kolon tabanı N", dd], ["Σ temel tepkisi", e]];
    const tol = 0.01 * Math.max(1, Math.abs(c));
    const tamam = Math.abs(a - kirisGirdi) < tol && Math.abs(c - to - dd) < tol && Math.abs(dd + to - e) < tol;
    return '<div class="bn-korunum ' + (tamam ? "tamam" : "sorun") + '"><b>Korunum (' + kacis(d) + "): " + (tamam ? (tm ? "✓ zincir tutarlı (temel öz ağırlığı dahil)" : "✓ beş sayı eşit") : "⚠ fark var") + "</b><div class=\"bn-korunum-sayilar\">" +
      sayilar.map(function (s) { return '<span><small>' + kacis(s[0]) + "</small><b>" + f1(s[1]) + " kN</b></span>"; }).join('<span class="bn-korunum-es" aria-hidden="true">=</span>') + "</div></div>";
  }
  function akisTablolari() {
    const v = V(), ust = ustKatV(v);
    const genel = v.model === "genel";
    // genel modelde kolon = tür "kolon" olan çubuk (no çubuk numarası; adres üst düğümün aks adresi); yük alanı karşılaştırması yok
    let h = "<h4>Kolonlar (kN; basınç +)</h4>" + tabloH(["Kolon", "Kat", "N_kat G", "N_kat Q", "N_küm G", "N_küm Q"].concat(genel ? [] : ["Yük alanı G+Q", "Fark %"]),
      (v.akis.kolonlar || []).slice().sort(function (a, b) { return (b.kat || 0) - (a.kat || 0) || a.no - b.no; }).map(function (k) {
        return [akisKolonAdi(k), k.kat != null ? String(k.kat) : "—", f1(k.N_G), f1(k.N_Q), f1(k.N_kum_G), f1(k.N_kum_Q)].concat(genel ? [] : [f1((k.N_trib_G || 0) + (k.N_trib_Q || 0)), f1(k.fark_yuzde)]);
      }));
    if (tekilTemeller(v).length) h += "<h4>Temeller (servis G+Q)</h4>" + tekilTemelTablosu(v);
    h += mesnetTepkiTablosu(v);
    h += "<h4>Kat toplamları</h4>" + tabloH(["Kat", "Kot (m)", "h (m)", "G (kN)", "Q (kN)", "w = G + nQ"], (v.yukler.katlar || []).slice().sort(function (a, b) { return b.kat - a.kat; }).map(function (k) { return [katAdV(v, k.kat), f2(k.kot), f2(k.h), f1(k.G), f1(k.Q), f1(k.w)]; }));
    void ust;
    return h;
  }
  // akış kolon kaydının adı: genel çözümde "Ç<no> · <üst düğüm adresi>", aks–kat çözümünde S-<aks>/k<kat>
  function akisKolonAdi(k) {
    const v = V();
    if (v && v.model === "genel") return "Ç" + k.no + (k.adres ? " · " + k.adres : "");
    return kolonAdres(k.no);
  }
  function katAdV(v, no) { const k = v.bina.katlar.filter(function (x) { return x.no === no; })[0]; return k ? k.ad : "kat " + no; }

  // ---------- Sonuç bölümü ----------
  const SEKMELER = [["akis", "Yük akışı"], ["deprem", "Deprem"], ["deforme", "Deforme"], ["diyagram", "Diyagramlar"], ["tablolar", "Tablolar"], ["tasarim", "Tasarım"], ["temel", "Temel"], ["anlatim", "Anlatım"]];
  function temelVar() { const v = V(); return !!(v && v.temel && Array.isArray(v.temel.dugumler) && v.temel.dugumler.length); }
  let anlatimCizildi = false;
  function depremVar() { const v = V(); return !!(v && v.deprem && v.deprem.katlar); }
  function sonucuCiz() {
    const v = V();
    if (!v) { ref.sonuc.innerHTML = ""; return; }
    anlatimCizildi = false;
    const o = v.ozet || {};
    if (D.sekme === "deprem" && !depremVar()) D.sekme = "akis";
    let h = '<div class="bn-eski se-eski' + (sonEski ? "" : " gizli") + '">Model değişti: aşağıdaki sonuçlar önceki modele aittir. Yeniden çözmek için “Çöz” düğmesine basın.</div>';
    h += '<div class="se-ozet"><span class="se-rozet">' + (o.sd_sayisi != null ? o.sd_sayisi : v.ag.sd_sayisi) + " SD</span><span class=\"se-rozet\">" + (o.eleman != null ? o.eleman : v.ag.elemanlar.length) + " eleman</span>" +
      '<span class="se-rozet">ΣG = ' + f1(o.toplam_G != null ? o.toplam_G : v.yukler.toplam.G) + " kN</span><span class=\"se-rozet\">ΣQ = " + f1(o.toplam_Q != null ? o.toplam_Q : v.yukler.toplam.Q) + " kN</span>" +
      '<span class="se-rozet">' + Object.keys(v.durumlar || {}).length + " durum · " + ((v.kombinasyonlar || []).filter(function (k) { return k.uygulandi && k.tur !== "drift"; }).length || Object.keys(v.sonuclar || {}).length) + " kombinasyon</span>" +
      (depremVar() ? '<span class="se-rozet">V_tE = ' + f1(v.deprem.VtE) + " kN</span>" : "") +
      (o.en_buyuk_temel_DC != null ? '<span class="se-rozet">Temel D/C maks ' + f2(o.en_buyuk_temel_DC) + "</span>" : "") +
      (v.tasarim ? '<span class="se-rozet bn-dc-rozet bn-dc-' + dcSinif(v.tasarim.en_buyuk_dc) + '">Eleman D/C maks ' + f2(v.tasarim.en_buyuk_dc) + "</span>" : "") + "</div>";
    h += '<div class="bn-cikti-satir" role="group" aria-label="Çıktılar"><button type="button" class="dugme kucuk" data-cikti="rapor">📄 Statik Rapor</button>' +
      (modul("MatrisTablo") ? '<button type="button" class="dugme kucuk" data-cikti="tablolar">▦ Tablolar</button>' : "") +
      (modul("MatrisIsi") ? '<button type="button" class="dugme kucuk" data-cikti="isi">🌡 Isı haritası</button>' : "") +
      (modul("MatrisIFC") ? '<button type="button" class="dugme kucuk" data-cikti="ifc">⬇ IFC</button>' : "") + "</div>";
    if (o.uyarilar && o.uyarilar.length) h += '<div class="bn-uyari-kutu">' + o.uyarilar.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    h += '<div class="bn-sekmeler" role="tablist">' + SEKMELER.filter(function (s) { return s[0] !== "deprem" || depremVar(); }).map(function (s) { return '<button type="button" role="tab" class="bn-sekme' + (D.sekme === s[0] ? " aktif" : "") + '" data-sekme="' + s[0] + '" aria-selected="' + (D.sekme === s[0]) + '">' + s[1] + "</button>"; }).join("") + "</div>";
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
    else if (D.sekme === "deprem") kap.innerHTML = depremSekmesi();
    else if (D.sekme === "deforme") kap.innerHTML = deformeSekmesi();
    else if (D.sekme === "diyagram") kap.innerHTML = diyagramSekmesi();
    else if (D.sekme === "tablolar") kap.innerHTML = tablolarSekmesi();
    else if (D.sekme === "tasarim") kap.innerHTML = tasarimSekmesi();
    else if (D.sekme === "temel") kap.innerHTML = temelSekmesi();
    else kap.innerHTML = anlatimSekmesi();
    if (D.sekme === "akis") sankeyCiz();
    else if (D.sekme === "deprem") depremCiz();
    else if (D.sekme === "deforme") deformeyiCiz();
    else if (D.sekme === "diyagram") diyagramiCiz();
    else if (D.sekme === "anlatim") anlatimiCiz();
    else if (D.sekme === "tasarim") tasarimAyrintiCiz();
    else if (D.sekme === "temel") temelHaritaCiz();
    sahneCiz();
  }
  // Durum / kombinasyon seçici: yük durumları, kombinasyon aileleri (optgroup), öteleme (drift) kombinasyonları, zarf.
  // "⇣": tam dizileri yanıtta yok, seçince motordan (bina_kombinasyon) alınır.
  function durumSecici(id, secili, zarf) {
    const v = V(), gruplar = [], var_ = {}, gAd = {};
    const grup = function (baslik) { if (!gAd[baslik]) { gAd[baslik] = { baslik: baslik, l: [] }; gruplar.push(gAd[baslik]); } return gAd[baslik]; };
    const ekle = function (g, k, ad) { if (var_[k]) return; var_[k] = 1; g.l.push([k, ad]); };
    const gd = grup("Yük durumları");
    Object.keys(v.durumlar || {}).forEach(function (k) { ekle(gd, k, "Durum " + k + (ince(v.durumlar[k]) ? " ⇣" : "")); });
    if (!(v.sonuclar && v.sonuclar["G+Q"]) && v.durumlar.G && v.durumlar.Q) ekle(gd, "G+Q", "G+Q (toplam)");
    Object.keys(v.sonuclar || {}).forEach(function (k) {
      const t = (v.kombinasyonlar || []).filter(function (x) { return x.ad === k; })[0];
      ekle(grup(t ? kombAile(t) : "Kombinasyonlar"), k, k);
    });
    (v.kombinasyonlar || []).forEach(function (k) {
      if (!k.uygulandi || v.durumlar[k.ad]) return;
      ekle(grup(kombAile(k)), k.ad, k.ad + (hazirMi(k.ad) ? "" : " ⇣"));
    });
    if (zarf) ekle(grup("Zarf"), "zarf", "Zarf (max/min, " + kombSayisi(v) + " kombinasyon)");
    return '<select class="girdi bn-secici" id="' + id + '" aria-label="Yük durumu / kombinasyon">' + gruplar.filter(function (g) { return g.l.length; }).map(function (g) {
      return '<optgroup label="' + kacis(g.baslik) + '">' + secenekler(g.l, secili) + "</optgroup>";
    }).join("") + "</select>";
  }
  function kombAile(k) {
    const tur = { dayanim: "Dayanım", deprem: "Deprem", servis: "Servis", drift: "Öteleme (drift)" }[k.tur] || k.tur || "Kombinasyon";
    return tur + (k.aile && k.aile !== k.ad ? ": " + k.aile : "");
  }
  // İnce kayıt (S/W/E durumları): u yok, diyagram dizileri yok; yalnız uç kuvvetleri, enb, düğüm/tepki (motor §4 sapma notu b)
  function ince(k) { return !!k && (k.diyagram === false || !(k.elemanlar && k.elemanlar.length && Array.isArray(k.elemanlar[0].M))); }
  // Seçilen ad diyagram/deforme için hazır mı (tam diziler yanıtta / önbellekte)?
  function hazirMi(ad) {
    const v = V();
    if (!v) return false;
    if (ad === "zarf") return true;
    if (ad === "G+Q" && !(v.sonuclar && v.sonuclar["G+Q"])) return !!v.durumlar.G && !ince(v.durumlar.G) && !!v.durumlar.Q && !ince(v.durumlar.Q);
    const k = (v.sonuclar && v.sonuclar[ad]) || (v.durumlar && v.durumlar[ad]);
    return !!k && !ince(k);
  }
  const KOMB_HATA = {};     // ad → kullanıcıya gösterilen neden (tekrar istek atılmaz; yeniden çözümde sıfırlanır)
  // Tam dizileri motordan `bina_kombinasyon {cozum_kimligi, ad, katsayilar, bina}` ile alır: yanıtta olmayan kombinasyon ya da ince durum
  // (tek durum: katsayilar {"EX+": 1}). Sonuç önbelleğe yazılır (kombinasyon → veri.sonuclar, durum → veri.durumlar). cb(hazır: bool)
  function kombinasyonHazirla(ad, cb) {
    const v = V();
    if (!v || hazirMi(ad)) { cb(true); return; }
    if (KOMB_HATA[ad]) { cb(false); return; }
    const durumMu = !!(v.durumlar && v.durumlar[ad]);
    const tanim = durumMu ? { ad: ad, katsayilar: {} } : (v.kombinasyonlar || []).filter(function (k) { return k.ad === ad; })[0];
    if (durumMu) tanim.katsayilar[ad] = 1;
    if (!tanim) { KOMB_HATA[ad] = "Kombinasyon tanımı yanıtta yok: " + ad; cb(false); return; }
    if (!KOMB_BEKLEYEN[ad]) {
      const sonSON = SON;
      const girdi = { cozum_kimligi: v.cozum_kimligi || null, ad: ad, katsayilar: tanim.katsayilar, bina: SON.bina || kopya(B) };
      KOMB_BEKLEYEN[ad] = A.motorIstegi({ islem: "bina_kombinasyon", girdi: girdi }).then(function (y) {
        if (SON !== sonSON) return false;
        if (!y || y.hata || !y.sonuc || ince(y.sonuc)) {
          // motor yoksa / çözüm bellekte değilse: doğrusallıkla durumlardan yerel birleşim — durumlar tam diziliyse
          const neden = (y && y.hata) || "yanıt yok";
          const yerel = durumMu ? { hata: "ince durumun tam dizileri yalnız motordan alınabilir" } : kisaBirlesim(tanim.katsayilar);
          if (yerel.hata) { KOMB_HATA[ad] = ad + " alınamadı (" + neden + "); yerel birleşim devre dışı: " + yerel.hata + "."; A.toast(KOMB_HATA[ad]); return false; }
          yerel.yerel = true;
          A.toast(ad + ": motor yanıtı yok (" + neden + "); G/Q durumlarından yerel birleşim gösteriliyor.");
          v.sonuclar = v.sonuclar || {}; v.sonuclar[ad] = yerel;
          return true;
        }
        if (durumMu) v.durumlar[ad] = y.sonuc;
        else { v.sonuclar = v.sonuclar || {}; v.sonuclar[ad] = y.sonuc; }
        return true;
      }, function (e) { KOMB_HATA[ad] = ad + " alınamadı: " + (e && e.message ? e.message : e); A.toast(KOMB_HATA[ad]); return false; });
    }
    KOMB_BEKLEYEN[ad].then(function (ok) { delete KOMB_BEKLEYEN[ad]; cb(!!ok); });
  }
  // Çizimden önce: hazır değilse kutuda bekleme notu, motor isteği; gelince (ya da hata) yeniden çiz
  function hazirDegilse(kap, ad, ciz) {
    if (hazirMi(ad)) return false;
    if (KOMB_HATA[ad]) { kap.innerHTML = '<p class="not se-bos bn-komb-hata">' + kacis(KOMB_HATA[ad]) + "</p>"; return true; }
    kap.innerHTML = '<p class="not se-bos">' + kacis(ad) + " motordan alınıyor…</p>";
    kombinasyonHazirla(ad, function () { if (kap.isConnected) { ciz(); sahneCiz(); } });
    return true;
  }
  // Durumların doğrusal birleşimi (u_komb = Σγ_i u_i; iç kuvvetler aynı katsayılarla). Durumlardan biri ince ise {hata}: boş dizi üretilmez.
  function kisaBirlesim(katsayilar) {
    const v = V(), adlar = Object.keys(katsayilar || {});
    const eksik = adlar.filter(function (k) { return !(v.durumlar && v.durumlar[k]); });
    if (!adlar.length || eksik.length) return { hata: "yanıtta olmayan durum: " + (eksik.join(", ") || "—") };
    const inceler = adlar.filter(function (k) { return ince(v.durumlar[k]); });
    if (inceler.length) return { hata: inceler.join(", ") + " durumları yanıtta yalnız uç kuvvetleriyle (ince) geldi" };
    const l = adlar.map(function (k) { return v.durumlar[k]; }), c = adlar.map(function (k) { return +katsayilar[k] || 0; });
    const o = { dugumler: [], tepkiler: [], elemanlar: [], denge: {} };
    l[0].dugumler.forEach(function (n, i) { const d = { no: n.no }; ["uX", "uY", "uZ", "rX", "rY", "rZ"].forEach(function (k) { d[k] = l.reduce(function (t, s, j) { return t + c[j] * ((s.dugumler[i] || {})[k] || 0); }, 0); }); o.dugumler.push(d); });
    l[0].tepkiler.forEach(function (n, i) { const d = { dugum: n.dugum }; ["FX", "FY", "FZ", "MX", "MY", "MZ"].forEach(function (k) { d[k] = l.reduce(function (t, s, j) { return t + c[j] * ((s.tepkiler[i] || {})[k] || 0); }, 0); }); o.tepkiler.push(d); });
    l[0].elemanlar.forEach(function (e, i) {
      const d = { no: e.no, x: e.x, enb: {} };
      ["N", "V", "M", "Vz", "My", "T"].forEach(function (k) { d[k] = (e[k] || []).map(function (_, m) { return l.reduce(function (t, s, j) { return t + c[j] * (((s.elemanlar[i] || {})[k] || [])[m] || 0); }, 0); }); d.enb[k] = enBuyuk(d[k]); });
      d.uc_kuvvetleri = (e.uc_kuvvetleri || []).map(function (_, m) { return l.reduce(function (t, s, j) { return t + c[j] * (((s.elemanlar[i] || {}).uc_kuvvetleri || [])[m] || 0); }, 0); });
      o.elemanlar.push(d);
    });
    Object.keys(l[0].denge || {}).forEach(function (k) { o.denge[k] = l.reduce(function (t, s, j) { return t + c[j] * (s.denge[k] || 0); }, 0); });
    return o;
  }
  // ---------- Deprem sekmesi ----------
  function depremSekmesi() {
    const v = V(), d = v.deprem, yon = D.depremYon;
    const K = d.kaynaklar || {};
    const kay = function (k) { return K[k] ? '<small class="bn-kaynak">' + kacis(K[k]) + "</small>" : ""; };
    const par = function (ad, deger, k) { return '<div class="bn-param"><span>' + ad + "</span><b>" + deger + "</b>" + kay(k) + "</div>"; };
    let h = "";
    if (d.uyarilar && d.uyarilar.length) h += '<div class="bn-uyari-kutu">' + d.uyarilar.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    const U = d.uygulanabilirlik || {};
    const uNot = (U.kosul_duzenli ? " Koşul: " + U.kosul_duzenli + "." : "") + (U.not ? " " + U.not : "");
    if (d.uygulanabilir === false) h += '<div class="hata-kutu" role="alert">Eşdeğer deprem yükü yöntemi bu bina için uygulanamaz (' + kacis(U.kaynak || "TBDY Tablo 4.4") + ": DTS " + kacis(d.DTS) + ", BYS " + kacis(d.BYS) + ", η_bi > 2,0 ya da B2 düzensizliği). Modal hesap gerekir; sonuçlar yalnız öğretim içindir." + kacis(uNot) + "</div>";
    else h += '<p class="bn-iyi-kutu">✓ Eşdeğer deprem yükü yöntemi uygulanabilir (' + kacis(U.kaynak || "Tablo 4.4") + ": DTS " + kacis(d.DTS) + ", BYS " + kacis(d.BYS) +
      (U.esik_duzenli != null ? "; eşik BYS ≥ " + kacis(U.esik_duzenli) + " (düzenli) / ≥ " + kacis(U.esik_diger) + " (diğer)" : "") + ")." + kacis(uNot) + "</p>";
    if (d.tahmin) h += '<p class="not">Değerler çözümsüz önizlemedir (tahmin); çözüm sonrası kat ötelemeleri ve η_bi motor çözümünden gelir.</p>';
    h += '<div class="bn-satir"><div class="se-seg" role="group" aria-label="Deprem doğrultusu">' + ["x", "y"].map(function (y) { return '<button type="button" class="se-seg-d" data-dep-yon="' + y + '" aria-pressed="' + (yon === y) + '">E' + y.toUpperCase() + "</button>"; }).join("") + "</div>" +
      '<label class="bn-onay"><input type="checkbox" id="bn-dep-ok"' + (D.depremOk ? " checked" : "") + "> 3B’de kat kuvveti okları ve kütle merkezi</label></div>";
    h += '<h4>Tasarım spektrumu (TBDY 2018 md. 2.3, 4.2)</h4><div class="se-sekil bn-spek-buyuk" id="bn-spek-buyuk" data-adim="' + adimNo("deprem") + '"></div>';
    h += '<h4>Parametreler</h4><div class="bn-param-grid">' +
      par("S_S / S_1", f2(v.bina.deprem ? v.bina.deprem.SS : d.SS) + " / " + f2(v.bina.deprem ? v.bina.deprem.S1 : d.S1), "SS") + par("Zemin · F_S / F_1", kacis((v.bina.deprem || {}).zemin_sinifi || "") + " · " + f2(d.FS) + " / " + f2(d.F1), "SDS") +
      par("S_DS / S_D1", f2(d.SDS) + " / " + f2(d.SD1), "SD1") + par("T_A / T_B / T_L (s)", f2(d.TA) + " / " + f2(d.TB) + " / " + f1(d.TL), "TA") +
      par("DTS / BYS", kacis(d.DTS) + " / " + kacis(d.BYS), "DTS") + par("I / R / D", f1(d.I) + " / " + f1(d.R) + " / " + f1(d.D), "R") +
      par("n · H_N", f1(d.n) + " · " + f2(d.HN) + " m", "TpA") + par("T_pA / T_p", f2(d.TpA) + " / " + f2(d.Tp) + " s (" + kacis(d.Tp_yontem || "ampirik") + ")", "TpA") +
      par("S_ae(T_p) / R_a / S_aR", f2(d.Sae_Tp) + " / " + f2(d.Ra) + " / " + fmt(d.SaR, 3) + " g", "SaR") + par("m_t · W_t", (d.m_t != null ? f1(d.m_t) + " t · " : "") + f1(d.W_t != null ? d.W_t : (d.katlar || []).reduce(function (t, k) { return t + (k.w_i || 0); }, 0)) + " kN", "VtE") +
      par("V_tE (≥ min)", f1(d.VtE) + " kN (min " + f1(d.VtE_min) + ")", "VtE") + par("ΔF_N", f2(d.dFN) + " kN", "dFN") +
      (d.lambda != null ? par("λ (DD-3 / DD-2)", fmt(d.lambda, 3), "oran") : "") + (d.theta_sinir != null ? par("θ_II sınırı", fmt(d.theta_sinir, 3), "theta") : "") + "</div>";
    // doğrultu ayrıntıları (motor: veri.deprem.X / .Y — T_p, Rayleigh, V_tE, D_b, η_max, M_o)
    const Yd = d[yon.toUpperCase()] || {}, YON = "E" + yon.toUpperCase();
    if (d.X || d.Y) {
      h += "<h4>" + YON + " doğrultusu</h4><div class=\"bn-param-grid\">" +
        par("T_p (" + YON + ")", f2(Yd.Tp != null ? Yd.Tp : d.Tp) + " s (" + kacis(Yd.Tp_yontem || d.Tp_yontem || "ampirik") + ")", "TpA") +
        (Yd.Tp_rayleigh != null ? par("Rayleigh T (Denk. 4.26)", f2(Yd.Tp_rayleigh) + " s" + (Yd.Tp_rayleigh_sinirli != null && Math.abs(Yd.Tp_rayleigh_sinirli - Yd.Tp_rayleigh) > 1e-6 ? " → " + f2(Yd.Tp_rayleigh_sinirli) + " s (≤ 1,4·T_pA)" : ""), "Tp") : "") +
        par("S_aR / R_a", fmt(Yd.SaR != null ? Yd.SaR : d.SaR, 3) + " g / " + f2(Yd.Ra != null ? Yd.Ra : d.Ra), "SaR") +
        par("V_tE (" + YON + ")", f1(Yd.VtE != null ? Yd.VtE : d.VtE) + " kN" + (Yd.alt_sinir_etkin ? " (alt sınır etkin)" : ""), "VtE") +
        (Yd.D_b != null ? par("Dışmerkezlik büyütme D_b (Denk. 4.29)", f2(Yd.D_b) + " · e = " + f2(Yd.e_oran != null ? Yd.e_oran : d.e_oran) + "·B", "D_b") : "") +
        (Yd.eta_max != null ? par("η_b,maks (Tablo 3.6)", f2(Yd.eta_max) + (Yd.eta_max > 1.2 ? " — A1 burulma düzensizliği" : " ≤ 1,2"), "eta") : "") +
        (Yd.Mo != null ? par("Devrilme momenti M_o", f1(Yd.Mo) + " kN·m", "Mo") : "") +
        (Yd.theta_max != null ? par("θ_II,maks / sınır", fmt(Yd.theta_max, 3) + " / " + fmt(Yd.theta_sinir != null ? Yd.theta_sinir : d.theta_sinir, 3), "theta") : "") +
        (d.EZ_katsayi != null ? par("EZ katsayısı (düşey deprem)", f2(d.EZ_katsayi) + " · G (≈ (2/3)·S_DS)", "EZ") : "") + "</div>";
      if (Yd.rayleigh && Yd.rayleigh.length) h += '<details class="bn-ayrinti"><summary>Rayleigh periyodu verisi (' + YON + "; birim kuvvetler F_f, ötelemeler d_f)</summary>" +
        tabloH(["Kat", "m_i (t)", "F_fi", "d_fi (mm)"], Yd.rayleigh.slice().sort(function (a, b) { return b.kat - a.kat; }).map(function (r) { return [katAdV(v, r.kat), f2(r.m), fmt(r.F_f, 3), fmt(r.d_f * 1000, 3)]; }), "bn-mini") + "</details>";
    }
    const kat = (d.katlar || []).slice().sort(function (a, b) { return b.kat - a.kat; });
    const F = "F_" + yon, Vk = "V_" + yon, dk = "d_" + yon, dl = "delta_" + yon, or = "oran_" + yon, eta = "eta_b" + yon, th = "theta_" + yon;
    const ekVar = kat.some(function (k) { return k["e_" + yon] != null; });
    h += '<h4>Kat kuvvetleri F_i ve kat kesmesi V_i (' + YON + "; Denk. 4.23)</h4>" +
      '<div class="bn-iki-kolon"><div class="se-sekil" id="bn-kat-kuvvet"></div>' +
      tabloH(["Kat", "H (m)", "w_i (kN)", "m_i (t)", "F_i (kN)", "V_i (kN)"].concat(ekVar ? ["e_i (m)", "M_bi (kN·m)"] : []), kat.map(function (k) {
        return [katAdV(v, k.kat), f2(k.H), f1(k.w_i), f2(k.m_i), f1(k[F]), f1(k[Vk])].concat(ekVar ? [f2(k["e_" + yon]), f1(k["Mb_" + yon])] : []);
      })) + "</div>";
    h += '<h4>Göreli kat ötelemesi (md. 4.9.1) · burulma η_bi (Tablo 3.6) · ikinci mertebe θ_II (md. 4.9.2)</h4>' +
      tabloH(["Kat", "h (m)", "d_i (mm)", "Δ_i (mm)", "δ_i = (R/I)Δ_i (mm)", "λ·δ_i/h_i", "Sınır", "η_bi", "θ_II", "Uygun"], kat.map(function (k) {
        // doğrultuya özgü uygunluk (uygun_x / uygun_y; yoksa genel) ve sınır (veri.deprem.X.sinir; yoksa kat / genel)
        const sinirK = Yd.sinir != null ? Yd.sinir : k.sinir != null ? k.sinir : d.sinir_oran;
        const uyg = k["uygun_" + yon] != null ? k["uygun_" + yon] : k.uygun;
        const s = { ek: uyg === false || (k[or] != null && sinirK != null && k[or] > sinirK + 1e-12) ? ' class="bn-drift-asim"' : "" };
        const dEt = k["delta_etkin_" + yon] != null ? k["delta_etkin_" + yon] : (k[dl] || 0) * (d.R / d.I);
        const r = [katAdV(v, k.kat), f2(k.h != null ? k.h : (k.H - (kat.filter(function (x) { return x.kat === k.kat - 1; })[0] || { H: 0 }).H)), f2((k[dk] || 0) * 1000), f2((k[dl] || 0) * 1000), f2(dEt * 1000),
          fmt(k[or], 3), fmt(sinirK, 3), k[eta] != null ? f2(k[eta]) + (k[eta] > 1.2 ? " (A1!)" : "") : "—", fmt(k[th], 3), s.ek ? "✗" : "✓"];
        r.ek = s.ek;
        return r;
      }));
    h += '<p class="not">δ_i etkin öteleme (Denk. 4.33); sınır gevrek dolgu için 0,008κ, esnek dolgu için 0,016κ (Denk. 4.34; κ betonarme 1,0, çelik 0,5); λ = S_ae(T_p; DD-3)/S_ae(T_p; DD-2). η_bi > 1,2 → A1 burulma düzensizliği, dışmerkezlik D_bi = (η_bi/1,2)² ile büyütülür (Denk. 4.29). θ_II ≤ 0,12·D/(C_h·R) ise ikinci mertebe etkileri ihmal edilebilir (Denk. 4.36). Kırmızı satır: sınır aşımı.</p>';
    return h;
  }
  function depremCiz() {
    const v = V(), d = v && v.deprem;
    if (!d) return;
    const kap = document.getElementById("bn-spek-buyuk");
    if (kap) { const W = Math.max(280, Math.min(760, kap.clientWidth || 600)); kap.innerHTML = spektrumSvg(d, W, Math.round(W * 0.5), false); }
    const kk = document.getElementById("bn-kat-kuvvet");
    if (kk) kk.innerHTML = katKuvvetSvg(d, Math.max(260, Math.min(420, kk.clientWidth || 320)));
  }
  // Yan görünüş: katlar yatay çizgi, F_i okları (uzunluk ∝ F) ve basamaklı kat kesmesi V_i (üçgen diyagram)
  function katKuvvetSvg(d, W) {
    const yon = D.depremYon, kat = (d.katlar || []).slice().sort(function (a, b) { return a.kat - b.kat; });
    if (!kat.length) return "";
    const HN = Math.max.apply(null, kat.map(function (k) { return k.H; })) || 1, H = 240, pu = 26, pa = 24, x0 = 80, gw = Math.min(90, (W - x0 - 60) * 0.3);
    const Fmaks = Math.max.apply(null, kat.map(function (k) { return Math.abs(k["F_" + yon] || 0); })) || 1, Vmaks = Math.max.apply(null, kat.map(function (k) { return Math.abs(k["V_" + yon] || 0); })) || 1;
    const Y = function (z) { return H - pa - z / HN * (H - pa - pu); }, okBoy = x0 - 14, xv0 = x0 + gw + 30, vw = Math.max(40, W - xv0 - 12);
    let s = '<path class="se-eksen" d="M' + pt(x0 - 6, Y(0)) + " L" + pt(x0 + gw + 6, Y(0)) + '"/>';
    for (let i = 0; i < 4; i++) s += '<path class="b3-mes-t" d="M' + pt(x0 - 6 + i * (gw + 12) / 3, Y(0)) + " L" + pt(x0 - 12 + i * (gw + 12) / 3, Y(0) + 7) + '"/>';
    s += '<path class="bn-fk-kolon" d="M' + pt(x0, Y(0)) + " L" + pt(x0, Y(HN)) + " M" + pt(x0 + gw, Y(0)) + " L" + pt(x0 + gw, Y(HN)) + '"/>';
    let onceki = 0;
    kat.forEach(function (k) {
      const y = Y(k.H), F = k["F_" + yon] || 0, Vv = k["V_" + yon] || 0;
      s += '<path class="bn-fk-kat" d="M' + pt(x0, y) + " L" + pt(x0 + gw, y) + '"/>';
      const boy = okBoy * Math.abs(F) / Fmaks;
      s += C.ok([x0 - 4 - boy, y], [x0 - 4, y], "bn-fk-ok-c", "bn-fk-ok-o", "", "") + metinSvg(Math.max(38, x0 - 4 - boy / 2), y - 7, "F" + k.kat + " = " + f1(F), "bn-fk-t", "middle");
      // kat kesmesi: alt kattan bu kata kadar sabit V (etiket çubuğun içinde)
      const yAlt = Y(onceki), w = vw * Math.abs(Vv) / Vmaks;
      s += '<rect class="bn-fk-v" x="' + r1(xv0) + '" y="' + r1(y) + '" width="' + r1(w) + '" height="' + r1(yAlt - y) + '"/>' + metinSvg(xv0 + 5, (y + yAlt) / 2 + 4, "V" + k.kat + " = " + f1(Vv), "bn-fk-t", "start");
      onceki = k.H;
    });
    s += metinSvg(x0 + gw / 2, H - 4, "Kat kuvvetleri F_i (kN)", "bn-fk-t", "middle") + metinSvg(xv0 + vw / 2, H - 4, "Kat kesmesi V_i (kN)", "bn-fk-t", "middle");
    return '<svg class="se-svg bn-fk-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Kat kuvvetleri ve kat kesmesi">' + s + "</svg>";
  }
  // 3B sahnede kat kuvveti okları (kütle merkezinde) ve kütle merkezi işareti; EX/EY durumu seçiliyken ya da Deprem sekmesinde
  function depremYonSec() {
    const ad = D.sekme === "diyagram" ? D.diyagramDurum : D.sekme === "deforme" || D.sekme === "tablolar" ? D.deformeDurum : null;
    const m = ad && /^E([XY])([+-])/.exec(ad);
    if (m) return { yon: m[1].toLowerCase(), isaret: m[2] === "-" ? -1 : 1 };
    if (D.sekme === "deprem") return { yon: D.depremYon, isaret: 1 };
    return null;
  }
  function depremVurguCiz(sahne, P, b, s) {
    const v = V(), d = v.deprem, sec = depremYonSec();
    if (!d || !sec || !D.depremOk) return;
    const km = {}; (v.kutle_merkezi || []).forEach(function (k) { km[k.kat] = k; });
    const sn = sinir(), XM = (sn.x0 + sn.x1) / 2, YM = (sn.y0 + sn.y1) / 2;
    const Fmaks = Math.max.apply(null, (d.katlar || []).map(function (k) { return Math.abs(k["F_" + sec.yon] || 0); })) || 1;
    const boyMaks = 0.45 * Math.max(sn.x1 - sn.x0, sn.y1 - sn.y0, 3);
    (d.katlar || []).forEach(function (k) {
      const c = km[k.kat] || { X: XM, Y: YM }, Z = katKot(k.kat);
      if (Z == null) return;
      const F = (k["F_" + sec.yon] || 0) * sec.isaret, boy = boyMaks * Math.abs(F) / Fmaks, yon = F >= 0 ? 1 : -1;
      const ucX = sec.yon === "x" ? c.X - yon * 0.2 : c.X, ucY = sec.yon === "y" ? c.Y - yon * 0.2 : c.Y;
      const basX = sec.yon === "x" ? ucX - yon * boy : ucX, basY = sec.yon === "y" ? ucY - yon * boy : ucY;
      const p0 = P(basX, basY, Z), p1 = P(ucX, ucY, Z);
      sahne.ekle(1e9, C.ok(p0, p1, "b3-dep-ok-c", "b3-dep-ok-o", "", "") + etiketKutu(p0[0], p0[1] - 10, "F" + k.kat + " = " + f1(Math.abs(F)) + " kN", "b3-dep-et", "middle"), 2);
      const m = P(c.X, c.Y, Z);
      sahne.ekle(1e9, '<g class="b3-km"><circle cx="' + r1(m[0]) + '" cy="' + r1(m[1]) + '" r="' + r1(6 * s) + '"/><path d="M' + pt(m[0] - 9 * s, m[1]) + " L" + pt(m[0] + 9 * s, m[1]) + " M" + pt(m[0], m[1] - 9 * s) + " L" + pt(m[0], m[1] + 9 * s) + '"/></g>' +
        metinSvg(m[0] + 10 * s, m[1] + 14 * s, "KM" + k.kat, "b3-km-t", "start"), 2);
    });
  }
  function akisSekmesi() {
    const v = V(), durumlar = ["G", "Q", "G+Q"];
    if (v.durumlar && v.durumlar.S) durumlar.push("S");
    if (v.durumlar && Object.keys(v.durumlar).some(function (k) { return k.charAt(0) === "W"; })) durumlar.push("W");
    return '<div class="bn-akis-ust"><div class="se-seg" role="group" aria-label="Yük durumu">' + durumlar.map(function (d) { return '<button type="button" class="se-seg-d" data-akis-durum="' + d + '" aria-pressed="' + (D.akisDurum === d) + '">' + d + "</button>"; }).join("") + "</div>" +
      (D.akisDurum === "S" || D.akisDurum === "W" ? '<span class="not">' + (D.akisDurum === "S" ? "Kar: çatı döşemelerine s = μ·S_k (kN/m²); akış değerleri motor S verisi verdiyse gösterilir." : "Rüzgâr: kat seviyelerine yatay kuvvet; düşey akış yok, kat kuvvetleri Tablolar sekmesinde.") + "</span>" : "") +
      '<div class="dugmeler"><button type="button" class="dugme kucuk" id="bn-oynat">▶ Oynat</button><span class="not">3B sahnede ' + (v.model === "genel" ? "bir panele ya da çubuğa" : "bir döşeme, kiriş ya da kolona") + " dokun: yük yolu vurgulanır; ok ve etiketlere dokununca formül kartı açılır.</span></div></div>" +
      korunumHtml() + '<h4>Akış şeması (bant genişliği ∝ kN; düğüme dokun: yalnız ilgili bantlar)</h4><div class="se-sekil bn-sankey" id="bn-sankey" data-adim="' + adimNo("akis") + '"></div>' +
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
    if (hazirDegilse(kap, D.deformeDurum, deformeyiCiz)) return;
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
  // Aks filtresi. Temel kirişi elemanının ara düğümleri aks kesişiminde değildir: eleman kaynağında aks çizgisini (hat) ve
  // doğrultusunu taşır (kaynak.hat, kaynak.yon); X doğrultulu kiriş y aksı üzerindedir.
  // veri.ag.elemanlar kaynak taşımaz: aks çizgisi veri.temel.elemanlar'dan (no → kaynak.hat, yon) okunur
  let temelHatOnbellek = null;
  function temelHat(e) {
    let k = e.kaynak;
    if (!k || k.hat == null) {
      const v = V();
      if (!temelHatOnbellek || temelHatOnbellek.v !== v) {
        const m = {};
        ((v && v.temel && v.temel.elemanlar) || []).forEach(function (x) { m[x.no] = { hat: x.kaynak && x.kaynak.hat != null ? x.kaynak.hat : x.hat, yon: x.yon || (x.kaynak && x.kaynak.yon) }; });
        temelHatOnbellek = { v: v, m: m };
      }
      k = temelHatOnbellek.m[e.no] || {};
    }
    return { hat: k.hat != null ? k.hat : e.hat != null ? e.hat : e.aks, yon: k.yon || e.yon };
  }
  function elemanFiltre(e) {
    if (e.tur === "radye-serit") return false;              // radye ızgara şeritleri diyagramda çizilmez (Temel sekmesinde)
    if (!D.aksFiltre) return true;
    const p = D.aksFiltre.split(":"), i = p[0] === "x" ? 0 : 1;
    if (e.tur === "temel-kirisi") { const h = temelHat(e); return h.hat != null && String(h.hat) === p[1] && (!h.yon || h.yon === (i === 0 ? "y" : "x")); }
    const a = agDugum(e.dugumler[0]), b = agDugum(e.dugumler[1]);
    return !!(a && b && a.aks && b.aks && a.aks[i] === p[1] && b.aks[i] === p[1]);
  }
  // FE elemanının adı: genel çözümde çubuk adresi (Ç32, türüyle); aks–kat kolon/kiriş adresleri (bulunamazsa motorun adresi)
  function elemanAdi(e) {
    if (e.cubuk != null) return "Ç" + e.cubuk + (e.tur ? " (" + cubukTurAdi(e.tur).toLocaleLowerCase("tr") + ")" : "");
    if (e.tur === "kolon") { const a = kolonAdres(e.kaynak_no); return /^S\d+$/.test(a) && e.adres ? e.adres : a; }
    if (e.tur === "temel-kirisi") return e.adres || ("TK-" + (temelHat(e).hat != null ? temelHat(e).hat : e.kaynak_no));
    if (e.tur === "radye-serit") return e.adres || ("RŞ" + e.no);
    const a = kirisAdres(e.kaynak_no);
    return /^K\d+$/.test(a) && e.adres ? e.adres : a;
  }
  // sayısal gürültü: ölçeğin milyonda birinden küçük değer sıfırdır (diyagram etiketlerinde "−1,663e-6" yazılmaz)
  function kucukSifir(v, olcek) { return Math.abs(v) < Math.max(1e-6 * Math.abs(olcek || 0), 1e-9) ? 0 : v; }
  function diyagramiCiz() {
    const kap = document.getElementById("bn-dgm-sekil"), v = V();
    if (!kap || !v) return;
    document.querySelectorAll("#bn-sonuc .se-seg-d[data-dgm]").forEach(function (d) { d.setAttribute("aria-pressed", String(d.dataset.dgm === D.diyagram)); });
    if (hazirDegilse(kap, D.diyagramDurum, diyagramiCiz)) { const nt0 = document.getElementById("bn-dgm-not"); if (nt0) nt0.textContent = ""; return; }
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
        const ve = vs.length ? kucukSifir(vs[im], gmaks) : 0;
        if (ve !== 0) { const sg = def.isaret * ve >= 0 ? 1 : -1; s += metinSvg(ust[im][0] + n[0] * sg * 10, ust[im][1] + n[1] * sg * 10 + 4, fmt(ve, 3), "se-etiket", "middle"); }
      };
      if (zarf) { ciz([0, e.L], [d.maks, d.maks], def.sinif + " bn-zarf-maks"); ciz([0, e.L], [d.min, d.min], def.sinif + " bn-zarf-min"); }
      else ciz(d.x, d.v, def.sinif);
    });
    kap.innerHTML = '<svg class="se-svg bn-dgm-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + kacis(def.uzun + " diyagramı") + '">' + s + "</svg>";
    kap.__hedef = hedef; kap.__W = W; kap.__H = H;
    const nt = document.getElementById("bn-dgm-not");
    let zarfNot = "";
    if (zarf) {
      const say = {};
      (v.zarf && v.zarf.elemanlar || []).forEach(function (z) { const bl = z.belirleyen || {}; [tur + "_max", tur + "_min"].forEach(function (k) { if (bl[k]) say[bl[k]] = (say[bl[k]] || 0) + 1; }); });
      const sira = Object.keys(say).sort(function (a, b) { return say[b] - say[a]; });
      const nK = (v.zarf && v.zarf.kombinasyon_sayisi) || (v.kombinasyonlar || []).filter(function (k) { return k.uygulandi && k.tur !== "drift"; }).length || Object.keys(v.sonuclar || {}).length;
      zarfNot = "Zarf (" + nK + " kombinasyon): koyu ton en büyük, açık ton en küçük değer. Belirleyen kombinasyon" + (sira.length ? "lar: " + sira.slice(0, 4).map(function (a) { return a + " (" + say[a] + " eleman)"; }).join(", ") + (sira.length > 4 ? ", …" : "") : " bilgisi yok") + ". ";
    }
    if (nt) nt.textContent = zarfNot + (tur === "M" || tur === "My" ? "Moment çekilen lif tarafına çizilir; " : "") + "etiketler elemandaki en büyük mutlak değerdir (" + (tur === "M" || tur === "My" || tur === "T" ? "kN·m" : "kN") + "). Elemana dokun: kesit tesir kartı" + (zarf ? " (belirleyen kombinasyonlar kartta)" : "") + ".";
  }
  function elemanKarti(no) {
    const v = V(), kap = document.getElementById("bn-eleman-kart"), e = v.ag.elemanlar.filter(function (x) { return x.no === no; })[0];
    if (!kap || !e) return;
    const zarfMi = D.diyagramDurum === "zarf", ks = zarfMi ? durumKisa(Object.keys(v.sonuclar || {})[0] || "G") : durumKisa(D.diyagramDurum), es = ks && elSonuc(ks, e.no);
    if (!es) { kap.innerHTML = ""; return; }
    const ad = elemanAdi(e) + (e.tur === "kiris" && (e.parca > 1 || agEleman("kiris", e.kaynak_no).length > 1) ? " (parça " + e.parca + ")" : "");
    const W = Math.max(260, Math.min(640, kap.clientWidth || 500)), H = 230, pl = 36, L = e.L, sx = (W - 2 * pl) / L;
    // yük: aks–kat kirişinde kiriş yük dökümü, genel modelde kolon dışındaki çubuğun yük dökümü (veri.yukler.cubuklar; aynı alanlar)
    const yk = e.cubuk != null ? (e.tur !== "kolon" ? (v.yukler.cubuklar || []).filter(function (x) { return x.no === e.cubuk; })[0] : null)
      : e.tur === "kiris" ? (v.yukler.kirisler || []).filter(function (x) { return x.no === e.kaynak_no; })[0] : null;
    // sayısal gürültü ölçeği: elemanın en büyük |N|, |V|, |M| değeri, en az 1000 (eşik 0,001 kN · kN·m)
    const ref0 = Math.max(1e3, Math.abs(enBuyuk(es.N || [])), Math.abs(enBuyuk(es.V || [])), Math.abs(enBuyuk(es.M || [])));
    let s = "";
    const dgm = function (y0, vs, def, sinif, baslik) {
      let g = 0; vs.forEach(function (x) { g = Math.max(g, Math.abs(x)); });
      const k = g > 1e-12 ? 26 / g : 0;
      let yol = "M" + pt(pl, y0);
      es.x.forEach(function (x, i) { yol += " L" + pt(pl + x * sx, y0 - def.isaret * vs[i] * k); });
      yol += " L" + pt(pl + L * sx, y0) + " Z";
      s += '<path class="se-asil" d="M' + pt(pl, y0) + " L" + pt(pl + L * sx, y0) + '"/><path class="se-dgm ' + sinif + '" d="' + yol + '"/>' + metinSvg(4, y0 + 4, baslik, "se-eno", "start") + metinSvg(W - 4, y0 - 30, fmt(kucukSifir(enBuyuk(vs), ref0), 3), "se-etiket", "end");
    };
    if (yk) {
      const q = kirisKNm(yk, "G").toplam, qq = kirisKNm(yk, "Q").toplam;
      for (let i = 0; i <= 8; i++) { const x = pl + L * sx * i / 8; s += '<path class="se-yuk-c" d="M' + pt(x, 18) + " L" + pt(x, 40) + '"/>' + C.okBasi(x, 42, 0, 1, "se-yuk-o", 7); }
      s += '<path class="se-yuk-c" d="M' + pt(pl, 18) + " L" + pt(pl + L * sx, 18) + '"/>' + metinSvg(W / 2, 12, "q_G = " + f2(q) + " kN/m" + (qq ? ", q_Q = " + f2(qq) + " kN/m" : ""), "se-etiket se-yuk-t", "middle");
    }
    s += '<path class="se-eleman" d="M' + pt(pl, 46) + " L" + pt(pl + L * sx, 46) + '"/>' + metinSvg(pl, 62, "0", "se-eno", "middle") + metinSvg(pl + L * sx, 62, "L = " + f2(L) + " m", "se-eno", "middle");
    dgm(110, es.V, DIYAGRAM.V, "se-dV", "V (kN)");
    dgm(190, es.M, DIYAGRAM.M, "se-dM", "M (kN·m)");
    const enb = es.enb || {};
    let zarfH = "";
    if (zarfMi) {
      const z = (v.zarf && v.zarf.elemanlar || []).filter(function (x) { return x.no === e.no; })[0];
      if (z) zarfH = tabloH(["Tesir", "En büyük", "Belirleyen", "En küçük", "Belirleyen"], ["N", "V", "M", "Vz", "My", "T"].map(function (k) { const bl = z.belirleyen || {}; return [k, fmt(z[k + "_max"], 3), bl[k + "_max"] || "—", fmt(z[k + "_min"], 3), bl[k + "_min"] || "—"]; }), "bn-mini");
    }
    kap.innerHTML = '<div class="bn-kart"><b>' + kacis(ad) + "</b> · e" + e.no + " · " + kacis(e.kesit) + " · " + (zarfMi ? "zarf (şema: " + kacis(Object.keys(v.sonuclar || {})[0] || "G") + ")" : kacis(D.diyagramDurum)) + (ks && ks.yerel ? ' <span class="se-rozet">yerel birleşim</span>' : "") +
      '<div class="se-sekil"><svg class="se-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Eleman kesit tesirleri">' + s + "</svg></div>" +
      '<p class="not">N = ' + fmt(kucukSifir(enb.N, ref0), 3) + " kN · V_maks = " + fmt(kucukSifir(enb.V, ref0), 3) + " kN · M_maks = " + fmt(kucukSifir(enb.M, ref0), 3) + " kN·m · Vz = " + fmt(kucukSifir(enb.Vz, ref0), 3) + " · My = " + fmt(kucukSifir(enb.My, ref0), 3) + " · T = " + fmt(kucukSifir(enb.T, ref0), 3) + "</p>" + zarfH + "</div>";
  }
  // ---------- Tablolar ----------
  function tablolarSekmesi() {
    const v = V();
    let h = '<div class="bn-satir">' + durumSecici("bn-tablo-durum", D.deformeDurum, false) +
      (modul("MatrisTablo") ? '<button type="button" class="dugme kucuk" data-cikti="tablolar">▦ Bütün tablolar ve metraj (düzenle, CSV, rapora ekle)</button>' : "") + "</div>";
    const ks = durumKisa(D.deformeDurum);
    if (!ks && D.deformeDurum !== "zarf") {
      h += '<p class="not" id="bn-tablo-bekle">' + kacis(KOMB_HATA[D.deformeDurum] || D.deformeDurum + " motordan alınıyor…") + "</p>";
      if (!KOMB_HATA[D.deformeDurum]) setTimeout(function () { kombinasyonHazirla(D.deformeDurum, function () { if (D.sekme === "tablolar") sekmeCiz(); }); }, 0);
    }
    if (ks) {
      h += "<h4>Mesnet tepkileri (bina koordinatı; kN, kN·m)</h4>" + tabloH(["Düğüm", "FX", "FY", "FZ", "MX", "MY", "MZ"], (ks.tepkiler || []).map(function (t) { const d = agDugum(t.dugum); return [(d ? d.adres : t.dugum), f1(t.FX), f1(t.FY), f1(t.FZ), f1(t.MX), f1(t.MY), f1(t.MZ)]; }));
      const dn = ks.denge || {}, tamam = ["FX", "FY", "FZ", "MX", "MY", "MZ"].every(function (k) { return dn[k] == null || Math.abs(dn[k]) < 1e-4; });
      h += '<p class="se-denge ' + (tamam ? "tamam" : "sorun") + '"><strong>Denge ' + (tamam ? "sağlandı" : "sağlanmadı") + ":</strong> " + ["FX", "FY", "FZ", "MX", "MY", "MZ"].map(function (k) { return "Σ" + k + " = " + fmt(dn[k], 3); }).join(", ") + "</p>";
    }
    if (v.model === "genel") h += s3YukTablolari(v);
    else h += "<h4>Kiriş yük dökümü (kN toplam; q = Σ/L kN/m)</h4>" + tabloH(["Kiriş", "L (m)", "G döşeme", "G duvar", "G öz", "G ek", "ΣG (kN)", "q_G (kN/m)", "Q döşeme", "Q ek", "ΣQ (kN)", "q_Q (kN/m)", "R_G≈qL/2", "M_G≈qL²/8"], (v.yukler.kirisler || []).map(function (k) {
      return [kirisAdres(k.no), f2(k.L), f1(k.G.doseme), f1(k.G.duvar), f1(k.G.oz), f1(k.G.ek), f1(k.G.toplam_kN), f2(kirisKNm(k, "G").toplam), f1(k.Q.doseme), f1(k.Q.ek), f1(k.Q.toplam_kN), f2(kirisKNm(k, "Q").toplam), f1(k.el_hesabi.R_G), f1(k.el_hesabi.M_G)];
    }));
    if (v.model !== "genel") h += "<h4>Döşeme payları (TS 500 11.4.3)</h4>" + tabloH(["Döşeme", "lx×ly", "m", "Tip", "g / q", "Kiriş", "Kenar", "Şekil", "Tepe G", "Tepe Q", "q_eM G", "q_eV G", "Toplam G", "Toplam Q"], [].concat.apply([], (v.yukler.dosemeler || []).map(function (d) {
      return d.paylar.map(function (p, i) { return [i ? "" : dosemeAdres(d.no), i ? "" : f2(d.lx) + "×" + f2(d.ly), i ? "" : f2(d.m), i ? "" : d.tip, i ? "" : f2(d.g) + " / " + f2(d.q), kirisAdres(p.kiris_no), p.kenar, p.sekil, f2(p.tepe_g), f2(p.tepe_q), f2(p.q_eM_g), f2(p.q_eV_g), f1(p.toplam_G), f1(p.toplam_Q)]; });
    })));
    // Kombinasyonlar: önce aile özeti (aile = yönetmelik denklemi; deprem ailesi 32 doğrultu/işaret varyantı), sonra açılır tam liste
    const kombs = v.kombinasyonlar || [], nUyg = kombs.filter(function (k) { return k.uygulandi; }).length;
    const aileler = [], aileAd = {};
    kombs.forEach(function (k) {
      const a = (k.aile || k.ad) + "|" + (k.tur || "") + "|" + (k.uygulandi ? 1 : 0);
      if (!aileAd[a]) { aileAd[a] = { ad: k.aile || k.ad, tur: k.tur || "", kaynak: k.kaynak || "", uygulandi: k.uygulandi, neden: k.neden, not: k.not || "", l: [] }; aileler.push(aileAd[a]); }
      aileAd[a].l.push(k);
      if (k.not && !aileAd[a].not) aileAd[a].not = k.not;
    });
    const zarfK = {}; ((v.zarf && v.zarf.kombinasyonlar) || []).forEach(function (a) { zarfK[a] = 1; });
    h += "<h4>Kombinasyonlar (" + nUyg + " uygulandı / " + kombs.length + "; zarfa giren " + kombSayisi(v) + (driftSayisi(v) ? ", öteleme " + driftSayisi(v) : "") + ")</h4>" +
      tabloH(["Aile", "Adet", "Tür", "Kaynak", "Durum / not"], aileler.map(function (a) {
        const r = [a.ad, String(a.l.length), a.tur, a.kaynak, a.uygulandi ? "✓ " + (a.not || (a.tur === "drift" ? "göreli kat ötelemesi" : "zarfa girer")) : "— " + (a.neden || "uygulanmadı") + (a.not ? " (" + a.not + ")" : "")];
        r.ek = a.uygulandi ? "" : ' class="bn-pasif-satir"';
        return r;
      })) +
      '<details class="bn-ayrinti"><summary>Tüm kombinasyonlar (' + kombs.length + ")</summary>" + tabloH(["Ad", "Katsayılar", "Tür", "Zarf", "Durum"], kombs.map(function (k) {
        const r = [k.ad, Object.keys(k.katsayilar || {}).map(function (d) { return String(k.katsayilar[d]).replace(".", ",") + "·" + d; }).join(" + "), k.tur || "", zarfK[k.ad] ? "✓" : "—",
          k.uygulandi ? ((v.sonuclar && v.sonuclar[k.ad]) ? "✓ hazır" : "✓ (seçince yüklenir)") : "— " + (k.neden || "uygulanmadı")];
        r.ek = k.uygulandi ? "" : ' class="bn-pasif-satir"';
        return r;
      })) + "</details>";
    if (v.ruzgar && v.ruzgar.katlar) {
      h += "<h4>Rüzgâr kat kuvvetleri (TS 498:2021 md. 14; W = C·q·A, C = " + f2(v.ruzgar.C) + ")</h4>" + tabloH(["Kat", "z (m)", "q (kN/m²)", "Cephe A_x (m²)", "Cephe A_y (m²)", "F_x (kN)", "F_y (kN)"], v.ruzgar.katlar.slice().sort(function (a, b) { return b.kat - a.kat; }).map(function (k) {
        const q = (v.ruzgar.q_h || []).filter(function (x) { return x.kat === k.kat; })[0] || {};
        return [katAdV(v, k.kat), f2(k.z != null ? k.z : q.z), f2(k.q != null ? k.q : q.q), f2(k.cephe_x), f2(k.cephe_y), f1(k.F_x), f1(k.F_y)];
      }));
      if (v.ruzgar.toplam_x != null) h += '<p class="not">ΣW_x = ' + f1(v.ruzgar.toplam_x) + " kN · ΣW_y = " + f1(v.ruzgar.toplam_y) + " kN. Cephe alanı A = cephe genişliği × kat yükseklik payı (m²); F_x, X doğrultusunda esen rüzgârın kat kuvvetidir.</p>";
      if (v.ruzgar.kaynak) h += '<p class="not">' + kacis(v.ruzgar.kaynak) + "</p>";
    }
    if (v.kar) {
      const kr = v.kar;
      h += "<h4>Kar yükü (TS 498:2021 md. 11)</h4>" + tabloH(["Bölge", "Rakım (m)", "S_k (kN/m²)", "μ", "C_e · C_t", "s = μ·C_e·C_t·S_k (kN/m²)", "Çatı alanı (m²)", "ΣS (kN)"],
        [[String(kr.bolge), f1(kr.rakim), f2(kr.Sk), f2(kr.mu), (kr.Ce != null ? f2(kr.Ce) : "1,00") + " · " + (kr.Ct != null ? f2(kr.Ct) : "1,00"), f2(kr.s), f2(kr.cati_alani), f1(kr.S_toplam)]]);
      [kr.Sk_kaynak, kr.mu_kaynak].filter(Boolean).forEach(function (t) { h += '<p class="not">' + kacis(t) + "</p>"; });
      if (kr.kaynak && !kr.Sk_kaynak) h += '<p class="not">' + kacis(kr.kaynak) + "</p>";
      if (kr.dogrulandi === false) h += '<p class="bn-uyari-kutu">Kar değerleri doğrulanacak (dogrulandi: false).</p>';
    }
    h += "<h4>Ağ</h4>" + tabloH(["Eleman", "Tür", "Kaynak", "Kat", "L (m)", "Kesit", "Düğümler"], (v.ag.elemanlar || []).map(function (e) { return ["e" + e.no, e.tur, elemanAdi(e), e.kat == null ? "—" : String(e.kat), f2(e.L), e.kesit, e.dugumler.join(" → ")]; }));
    return h;
  }
  // genel model (surum 3) yük tabloları: çubuk yük dökümü (veri.yukler.cubuklar) ve panel yükleri / kenar payları (veri.yukler.paneller)
  function s3YukTablolari(v) {
    const yc = (v.yukler && v.yukler.cubuklar) || [], yp = (v.yukler && v.yukler.paneller) || [];
    const turu = {}; ((v.bina && v.bina.cubuklar) || []).forEach(function (c) { turu[c.no] = c.tur || "diger"; });
    const karVar = yc.some(function (y) { return y.S && y.S.toplam_kN; });
    const ac = function (n) { return n > 60 ? '<details class="bn-ayrinti"><summary>' + n + " satır (aç)</summary>" : ""; }, kapa = function (n) { return n > 60 ? "</details>" : ""; };
    let h = "<h4>Çubuk yük dökümü (kN toplam; q = Σ/L kN/m)</h4>" + ac(yc.length) + tabloH(["Çubuk", "Tür", "L (m)", "G öz", "G panel", "G duvar", "G ek", "ΣG (kN)", "q_G (kN/m)", "Q panel", "Q ek", "ΣQ (kN)"].concat(karVar ? ["ΣS (kN)"] : []),
      yc.map(function (y) {
        const G = y.G || {}, Q = y.Q || {}, S = y.S || {}, L = y.L || 1;
        return ["Ç" + y.no, cubukTurAdi(turu[y.no]), f2(y.L), f1(+G.oz || 0), f1(+G.panel || 0), f1(+G.duvar || 0), f1(+G.ek || 0), f1(+G.toplam_kN || 0), f2((+G.toplam_kN || 0) / L),
          f1(+Q.panel || 0), f1(+Q.ek || 0), f1(+Q.toplam_kN || 0)].concat(karVar ? [f1(+S.toplam_kN || 0)] : []);
      })) + kapa(yc.length);
    h += "<h4>Panel yükleri ve kenar payları</h4>" + ac(yp.length) + tabloH(["Panel", "Tür", "Alan (m²)", "Eğim (°)", "g / q / s (kN/m²)", "ΣG", "ΣQ", "ΣS", "Dağıtım", "Kenar payları (m² → çubuk)"], yp.map(function (p) {
      return ["P" + p.no, p.tur || "", f2(p.alan), f1(p.egim), f2(p.g) + " / " + f2(p.q) + " / " + f2(p.s), f1(p.G_toplam), f1(p.Q_toplam), f1(p.S_toplam), p.dagitim || "",
        (p.kenarlar || []).filter(function (k) { return k.sekil !== "yok"; }).map(function (k) { return f2(k.pay) + " → Ç" + (k.cubuklar || []).join("/Ç"); }).join("; ") || "—"];
    })) + kapa(yp.length);
    return h;
  }
  function cubukTurAdi(t) { const x = CUBUK_TURLERI.filter(function (c) { return c[0] === (t || "diger"); })[0]; return x ? x[1] : (t || "Çubuk"); }
  // ---------- Tasarım (Dilim 3, §11: veri.tasarim) ----------
  // D/C sınıfları: y < 0,7 ≤ s < 0,9 ≤ t ≤ 1,0 < k (renk körlüğü için kırmızıda desen + kalın kenar; tabloda simge)
  const DC_SINIF = [["y", "< 0,7", "<0.7"], ["s", "0,7–0,9", "0.7-0.9"], ["t", "0,9–1,0", "0.9-1.0"], ["k", "> 1,0", ">1.0"]];
  const OZET_ETIKET = {
    Md_mesnet: ["M_d mesnet (−M)", "kN·m"], Mr_mesnet: ["M_r mesnet", "kN·m"], As_ust_cm2: ["Üst donatı gerekli (mesnet)", "cm²"], As_ust_mevcut_cm2: ["Üst donatı (kesitte)", "cm²"], oneri_ust: ["Üst çubuk önerisi", ""],
    Md_aciklik: ["M_d açıklık (+M)", "kN·m"], Mr_aciklik: ["M_r açıklık", "kN·m"], As_alt_cm2: ["Alt donatı gerekli (açıklık)", "cm²"], As_alt_mevcut_cm2: ["Alt donatı (kesitte)", "cm²"], oneri_alt: ["Alt çubuk önerisi", ""],
    Vd: ["V_d", "kN"], etriye: ["Etriye", ""],
    rho: ["Boyuna donatı oranı ρ", "%"], As_toplam_cm2: ["A_s toplam", "cm²"], N_max_kN: ["N_d,maks (basınç +)", "kN"], N_min_kN: ["N_d,min", "kN"],
    N_sinir_TBDY_kN: ["N sınırı 0,40·f_ck·A_c (TBDY 7.3.1.2)", "kN"], N_sinir_TS500_kN: ["N sınırı 0,9·f_cd·A_c (TS 500)", "kN"], e_min_x_mm: ["e_min,x", "mm"], e_min_y_mm: ["e_min,y", "mm"],
    sinif: ["Kesit sınıfı (Tablo 5.1)", ""], profil: ["Profil", ""], Mn_kNm: ["M_n (karakteristik)", "kN·m"], Pn_kN: ["P_n (basınç)", "kN"], Vn_kN: ["V_n (kesme)", "kN"],
    Mc_kNm: ["M_c = M_n/Ω", "kN·m"], Pc_kN: ["P_c = P_n/Ω", "kN"], Vc_kN: ["V_c = V_n/Ω", "kN"], Lb_m: ["L_b (yanal tutulmamış boy)", "m"],
    d_m: ["d (faydalı yükseklik)", "m"], b: ["b", "m"], h: ["h", "m"],
    rho_varsayim: ["ρ varsayıldı (kesitte verilmedi)", ""], rho_gerekli: ["ρ gerekli (öneri)", "%"], As_gerekli_cm2: ["A_s gerekli", "cm²"], Ndm_kN: ["N_dm (TBDY 7.3.1.2)", "kN"],
    bX: ["b_X", "m"], bY: ["b_Y", "m"], yon: ["Kolon yönü", ""],
    L_m: ["L (eleman boyu)", "m"], K: ["K (burkulma katsayısı)", ""], yontem: ["Yöntem", ""],
    N_kN: ["N (belirleyen; basınç +)", "kN"], Mx_kNm: ["M_x (belirleyen)", "kN·m"], My_kNm: ["M_y (belirleyen)", "kN·m"], V_kN: ["V (belirleyen)", "kN"],
    // genel model (surum 3) çubuk özetleri: çapraz / çekme elemanı
    Tc_kN: ["T_c = T_n/Ω (çekme)", "kN"], narinlik_basinc: ["KL/i (basınç)", ""], narinlik_cekme: ["L/i (çekme)", ""], yalniz_cekme: ["Yalnız çekme", ""],
    tbdy_capraz: ["TBDY çapraz (süneklik, düzen)", ""], kontrol: ["Kontrol", ""],
  };
  function yokSayisi(t) { return (t.elemanlar || []).filter(function (e) { return e.dc == null; }).length; }
  function tasarimVar() { const v = V(); return !!(v && v.tasarim && Array.isArray(v.tasarim.elemanlar)); }
  function dcAktif() { return !!(SON && !sonEski && D.sekme === "tasarim" && D.dcGorunum && tasarimVar()); }
  function tasarimKaydi(tur, no) { const v = V(); return v && v.tasarim ? (v.tasarim.elemanlar || []).filter(function (e) { return e.tur === tur && e.no === no; })[0] || null : null; }
  // Tasarım kaydı ↔ sahne anahtarı. Genel model kayıtları {tur: kolon|kiris|capraz…, no: çubuk no, cubuk, kaynak?}; sahne çubuğu {tur: "cubuk", no}
  // olarak tanır. Genelleştirilmiş aks–kat elemanının kaydı kaynak {aks_kat, no} taşır; karma modelde (aks–kat kolon + genel çözüm)
  // sahnede aks–kat elemanı durur. Önce sahnede gerçekten var olan karşılık seçilir.
  function sahneAnahtari(e) {
    if (!e) return null;
    const k = e.kaynak && e.kaynak.aks_kat ? e.kaynak : null;
    if (e.cubuk != null && nesneBul("cubuk", +e.cubuk)) return { tur: "cubuk", no: +e.cubuk };
    if (k && nesneBul(k.aks_kat, +k.no)) return { tur: k.aks_kat, no: +k.no };
    if (e.cubuk != null && s3Var()) return { tur: "cubuk", no: +e.cubuk };
    if (k) return { tur: k.aks_kat, no: +k.no };
    return { tur: e.tur, no: e.no };
  }
  // sahne elemanından ({tur, no}) tasarım kaydı: çubuk → çubuk numarasıyla; kolon/kiriş → kaynağı eşleşen kayıt, yoksa tür/no
  function kayitSahneden(tur, no) {
    if (tur === "cubuk") return dcKaydiCubuk(+no);
    const v = V();
    if (!v || !v.tasarim) return null;
    return (v.tasarim.elemanlar || []).filter(function (e) { return e.kaynak && e.kaynak.aks_kat === tur && +e.kaynak.no === +no; })[0] || tasarimKaydi(tur, no);
  }
  // tasarım ayrıntısı isteği (bina_eleman_tasarim) anahtarı: "cubuk" alanı olan kayıt çubuk numarasıyla kesin çözülür (sözleşme C7)
  function tasarimIstekHedefi(e, s) { return e && e.cubuk != null ? { tur: "cubuk", no: +e.cubuk } : { tur: s.tur, no: s.no }; }
  function dcDagilimi(t) {
    if (t.dc_dagilimi) return t.dc_dagilimi;
    const d = { "<0.7": 0, "0.7-0.9": 0, "0.9-1.0": 0, ">1.0": 0 };
    (t.elemanlar || []).forEach(function (e) { const c = DC_SINIF.filter(function (x) { return x[0] === dcSinif(e.dc); })[0]; if (c) d[c[2]]++; });
    return d;
  }
  function dcMetin(dc) { return dc == null ? "—" : dc >= 99 ? "≥ 99 (kesit yetersiz)" : f2(dc); }
  function dcCip(dc) {
    const c = dcSinif(dc);
    return '<span class="bn-dc-cip bn-dc-' + c + '"' + (c === "yok" ? ' title="Tahkik edilemedi (hesaplanamadı)"' : "") + ">" + (c === "k" ? "✗ " : c === "t" ? "! " : "") + (c === "yok" ? "— yok" : dcMetin(dc)) + "</span>";
  }
  // tasarım kaydının tür adı: çubuk türleri (kolon, kiriş, çapraz, aşık, kren kirişi …) küçük harfle; sistem önekiyle
  function turAd(e) { return (e.sistem === "celik" ? "çelik " : "") + cubukTurAdi(e.tur).toLocaleLowerCase("tr"); }
  // belirleyen kontrolün talep / kapasitesi: yönetmelik sınır koşulu olmayan (kosul ≠ true) satırlardan, adı belirleyen etiketiyle
  // başlayan (büyük/küçük harf duyarsız) en büyük D/C'li kontrol; yoksa koşul dışı en büyük D/C
  function belirleyenKontrol(e) {
    const l = (e.kontroller || []).filter(function (k) { return !k.kosul; }), b = ((e.belirleyen && e.belirleyen.kontrol) || "").toLocaleLowerCase("tr");
    const uyan = l.filter(function (k) { const a = String(k.ad || "").toLocaleLowerCase("tr"); return b && (a.indexOf(b) === 0 || a.indexOf(": " + b) >= 0); });
    const ara = uyan.length ? uyan : l;
    return ara.reduce(function (m, k) { return !m || (k.dc || 0) > (m.dc || 0) ? k : m; }, null);
  }
  function tkDeger(x, birim) { return typeof x === "number" ? fmt(x, 3) + (birim ? " " + birim : "") : x == null ? "—" : String(x); }
  // Yatay yığılmış D/C dağılım çubuğu (HTML; genişlik ∝ eleman sayısı)
  function dcCubugu(t) {
    const d = dcDagilimi(t), top = DC_SINIF.reduce(function (s, c) { return s + (+d[c[2]] || 0); }, 0) || 1;
    return '<div class="bn-dc-cubuk" role="img" aria-label="D/C dağılımı: ' + DC_SINIF.map(function (c) { return c[1] + " " + (d[c[2]] || 0); }).join(", ") + '">' +
      DC_SINIF.map(function (c) { const n = +d[c[2]] || 0; return n ? '<span class="bn-dc-dilim bn-dc-' + c[0] + '" style="flex-grow:' + n + '" title="D/C ' + c[1] + ": " + n + ' eleman">' + n + "</span>" : ""; }).join("") + "</div>" +
      '<div class="bn-dc-lejant-satir">' + DC_SINIF.map(function (c) { return '<span><i class="bn-dc-kare bn-dc-' + c[0] + '"></i>D/C ' + c[1] + " · " + (+d[c[2]] || 0) + "</span>"; }).join("") +
      (yokSayisi(t) ? '<span><i class="bn-dc-kare bn-dc-yok"></i>hesaplanamadı · ' + yokSayisi(t) + "</span>" : "") + "<span>toplam " + (top + yokSayisi(t)) + "</span></div>";
  }
  // 3B sahne altı lejant (D/C görünümü açıkken)
  function dcLejantCiz() {
    const el = document.getElementById("bn-dc-lejant");
    if (!el) return;
    if (!dcAktif()) { el.hidden = true; el.innerHTML = ""; return; }
    const t = V().tasarim, d = dcDagilimi(t);
    el.hidden = false;
    el.innerHTML = "<b>D/C</b>" + DC_SINIF.map(function (c) { return '<span><i class="bn-dc-kare bn-dc-' + c[0] + '"></i>' + c[1] + " (" + (+d[c[2]] || 0) + ")</span>"; }).join("") +
      (yokSayisi(t) ? '<span><i class="bn-dc-kare bn-dc-yok"></i>yok (' + yokSayisi(t) + ")</span>" : "") +
      '<span class="bn-dc-not">en büyük ' + f2(t.en_buyuk_dc != null ? t.en_buyuk_dc : 0) + " · bütün katlar</span>";
  }
  function tasarimSekmesi() {
    const v = V(), t = v.tasarim;
    if (!t) return '<div class="bn-bilgi-kutu" id="bn-tasarim-yok"><b>Tasarım kontrolleri motor güncellemesiyle gelecek.</b><p class="not">Kiriş eğilme/kesme ve kolon N–M etkileşimi (TS 500, TBDY 2018 Bölüm 7), çelik eleman tahkikleri (ÇYTHYE 2018) motorun kesit tasarımı modülüyle (veri.tasarim) gelir; bu yanıtta yok. İç kuvvetler ve zarf “Diyagramlar” sekmesinde hazır.</p></div>';
    const yon = t.yontem || {};
    let h = '<details class="bn-yontem" open><summary>Yöntem ve varsayımlar</summary>' +
      '<div class="bn-yontem-ic"><p>' + Object.keys(yon).map(function (k) { return "<b>" + kacis(k === "celik" ? "Çelik" : k === "betonarme" ? "Betonarme" : k) + ":</b> " + kacis(yon[k]); }).join(" · ") + "</p>" +
      ((t.varsayimlar || []).length ? "<ul>" + t.varsayimlar.map(function (x) { return "<li>" + kacis(x) + "</li>"; }).join("") + "</ul>" : "") +
      '<p class="not">Öğretim / ön boyutlandırma amaçlıdır; kapasite tasarımı, ikinci mertebe ve süneklik koşullarının tamamı kapsam dışıdır.</p></div></details>';
    if ((t.uyarilar || []).length) h += '<div class="bn-uyari-kutu">' + t.uyarilar.map(function (u) { return "<div>⚠ " + kacis(adresTurkce(u)) + "</div>"; }).join("") + "</div>";
    h += "<h4>D/C dağılımı (" + (t.elemanlar || []).length + " eleman; en büyük " + f2(t.en_buyuk_dc) + (t.kombinasyon_sayisi ? "; " + t.kombinasyon_sayisi + " dayanım/deprem kombinasyonu" : "") + ")</h4>" + dcCubugu(t);
    const kritik = (t.kritik_elemanlar || []).slice(0, 10);
    if (kritik.length) h += '<div class="bn-kritik"><span class="not">Kritik:</span>' + kritik.map(function (k) {
      return '<button type="button" class="bn-cip bn-kritik-cip" data-dc-sec="' + kacis(k.tur + ":" + k.no) + '" title="' + kacis((k.kontrol || "") + (k.kombinasyon ? " · " + k.kombinasyon : "")) + '">' + kacis(kritikAdi(k)) + " " + dcCip(k.dc) + "</button>";
    }).join("") + "</div>";
    h += '<div class="bn-satir"><label class="bn-onay"><input type="checkbox" id="bn-dc-gorunum"' + (D.dcGorunum ? " checked" : "") + "> 3B’de D/C renkleri</label>" +
      '<select class="girdi bn-secici" id="bn-dc-filtre" aria-label="Tasarım tablosu süzgeci">' + secenekler([["", "Bütün elemanlar"], ["kiris", "Yalnız kirişler"], ["kolon", "Yalnız kolonlar"]].concat(digerTurler(t)).concat([["asim", "Yalnız D/C > 1"]]).concat(yokSayisi(t) ? [["yok", "Yalnız hesaplanamayanlar"]] : []), D.tasarimFiltre) + "</select></div>";
    h += '<div id="bn-tasarim-ayrinti" class="bn-tasarim-ayrinti" aria-live="polite">' + tasarimAyrintiHtml() + "</div>";
    h += "<h4>Elemanlar (D/C’ye göre sıralı; satıra dokun: 3B’de seçilir, ayrıntı açılır)</h4>" + tasarimTablosu(t);
    return h;
  }
  // genel modelde kolon/kiriş dışındaki çubuk türleri (çapraz, aşık, kren …) için süzgeç seçenekleri
  function digerTurler(t) {
    const g = {};
    (t.elemanlar || []).forEach(function (e) { if (e.tur && e.tur !== "kolon" && e.tur !== "kiris") g[e.tur] = 1; });
    return Object.keys(g).map(function (k) { return [k, "Yalnız " + cubukTurAdi(k).toLocaleLowerCase("tr")]; });
  }
  // tasarım kaydının adı: genel çözümde çubuk adı Türkçe türüyle ("Ç41 (çapraz)"; motor adresi ASCII "Ç41 (capraz)"), aks–kat'ta motor adresi
  function tasarimAdi(e) {
    if (e.cubuk != null) return elemanAdi(e);
    return e.adres || (e.tur === "kolon" ? kolonAdres(e.no) : kirisAdres(e.no));
  }
  // motor metnindeki ASCII çubuk adresleri ("Ç41 (capraz)") Türkçe tür adıyla ("Ç41 (çapraz)")
  function adresTurkce(metin) {
    return String(metin == null ? "" : metin).replace(/Ç(\d+) \(([a-z-]+)\)/g, function (m, no, t) {
      const x = CUBUK_TURLERI.filter(function (c) { return c[0] === t; })[0];
      return x ? "Ç" + no + " (" + x[1].toLocaleLowerCase("tr") + ")" : m;
    });
  }
  function kritikAdi(k) { const e = tasarimKaydi(k.tur, k.no); return e ? tasarimAdi(e) : (k.adres || (k.tur + " " + k.no)); }
  function tasarimTablosu(t) {
    const f = D.tasarimFiltre;
    const l = (t.elemanlar || []).filter(function (e) { return !f || (f === "asim" ? e.dc > 1 : f === "yok" ? e.dc == null : e.tur === f); }).slice()
      .sort(function (a, b) { return (b.dc == null ? -1 : b.dc) - (a.dc == null ? -1 : a.dc); });
    if (!l.length) return '<p class="not">Süzgece uyan eleman yok.</p>';
    const sec = D.tasarimSecim;
    return '<div class="se-tablo-kutu"><table class="se-sonuc-tablo bn-dc-tablo"><thead><tr>' + ["Eleman", "Tür", "Kesit", "Belirleyen kontrol", "Kombinasyon", "Talep", "Kapasite", "D/C", "Durum"].map(function (x) { return "<th>" + x + "</th>"; }).join("") + "</tr></thead><tbody>" +
      l.map(function (e) {
        const k = belirleyenKontrol(e) || {}, b = e.belirleyen || {};
        const aktif = sec && sec.tur === e.tur && sec.no === e.no;
        return '<tr class="bn-dc-satir bn-dc-satir-' + dcSinif(e.dc) + (aktif ? " aktif" : "") + '" data-dc-tur="' + e.tur + '" data-dc-no="' + e.no + '" tabindex="0" aria-selected="' + !!aktif + '">' +
          '<th scope="row">' + kacis(tasarimAdi(e)) + '<span class="bn-dc-mobil"> ' + dcCip(e.dc) + "</span></th><td class=\"bn-dc-kisa\">" + kacis(turAd(e)) + "</td><td class=\"bn-dc-kisa\">" + kacis(e.kesit || "") + "</td><td>" + kacis(b.kontrol || k.ad || (e.dc == null ? "hesaplanamadı" : "")) + "</td>" +
          '<td class="bn-komb-ad">' + kacis(b.kombinasyon || k.kombinasyon || "—") + '</td><td class="sayi">' + kacis(tkDeger(k.talep, k.birim)) + '</td><td class="sayi">' + kacis(tkDeger(k.kapasite, k.birim)) + "</td>" +
          '<td class="sayi">' + dcCip(e.dc) + "</td><td>" + kacis(e.durum || "") + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }
  // tasarım özeti değeri: sayı (birimli), evet/hayır, dizi (K → "K_güçlü x / K_zayıf y"; diğerleri " / " ile), nesne ("a: v, …")
  function ozetDegerMetni(k, val, birim) {
    const tek = function (x) { return typeof x === "boolean" ? (x ? "evet" : "hayır") : typeof x === "number" ? fmt(x, 4) : x == null ? "—" : typeof x === "object" ? JSON.stringify(x) : String(x); };
    if (typeof val === "boolean") return val ? "evet" : "hayır";
    if (/^rho/.test(k) && typeof val === "number") return "%" + fmt(val * 100, 3);
    if (typeof val === "number") return fmt(val, 4) + (birim ? " " + birim : "");
    if (Array.isArray(val)) {
      if (k === "K" && val.length === 2) return "K_güçlü " + tek(val[0]) + " / K_zayıf " + tek(val[1]);
      return val.map(tek).join(" / ") + (birim ? " " + birim : "");
    }
    if (val && typeof val === "object") return Object.keys(val).map(function (a) { return a + ": " + tek(val[a]); }).join(", ");
    return String(val);
  }
  function tasarimAyrintiHtml() {
    const s = D.tasarimSecim, e = s && tasarimKaydi(s.tur, s.no);
    if (!e) return '<p class="not bn-tasarim-ipucu">Bir elemana dokunun (3B sahnede ya da tablodaki satıra): özet, kontroller ve “Ayrıntılı hesap”.</p>';
    const oz = e.ozet || {}, b = e.belirleyen || {};
    const sira = Object.keys(OZET_ETIKET), ozAnahtar = Object.keys(oz).sort(function (a, b) { const i = sira.indexOf(a), j = sira.indexOf(b); return (i < 0 ? 999 : i) - (j < 0 ? 999 : j); });
    const ozSatir = ozAnahtar.filter(function (k) { return oz[k] != null && oz[k] !== ""; }).map(function (k) {
      const et = OZET_ETIKET[k] || [k, ""], val = oz[k];
      const deger = ozetDegerMetni(k, val, et[1]);
      return '<div class="bn-param"><span>' + kacis(et[0]) + "</span><b>" + kacis(deger) + "</b></div>";
    }).join("");
    // kosul: true → yönetmelik sınır koşulu (boyut, en az donatı …): D/C'ye katılmaz, soluk ve "koşul" etiketli
    const kont = (e.kontroller || []).map(function (k) {
      const sag = !(k.saglandi === false || (!k.kosul && k.dc > 1 + 1e-9));
      const r = [(k.ad || "") + (k.kosul ? " (koşul)" : ""), tkDeger(k.talep, k.birim), tkDeger(k.kapasite, k.birim), dcMetin(k.dc), sag ? "✓" : "✗", k.kombinasyon || "", k.kaynak || ""];
      r.ek = !sag ? ' class="bn-drift-asim"' : k.kosul ? ' class="bn-pasif-satir"' : "";
      return r;
    });
    const anahtar = e.tur + ":" + e.no, ayr = TASARIM_AYR[anahtar];
    return '<div class="bn-kart bn-dc-kart bn-dc-kenar-' + dcSinif(e.dc) + '"><div class="bn-dc-baslik"><b>' + kacis(tasarimAdi(e) || "") + "</b> · " + kacis(turAd(e)) + " · " + kacis(e.kesit || "") + (e.malzeme ? " · " + kacis(e.malzeme) : "") +
      (e.kat != null ? " · kat " + kacis(e.kat) : "") + " " + dcCip(e.dc) + ' <span class="se-rozet">' + kacis(e.durum || "") + "</span>" +
      '<button type="button" class="bn-firca-kapat bn-dc-kapat" id="bn-tasarim-kapat" aria-label="Ayrıntıyı kapat">✕</button></div>' +
      '<p class="not">Belirleyen: <b>' + kacis(b.kontrol || "—") + "</b>" + (b.kombinasyon ? " · " + kacis(b.kombinasyon) : "") + (e.fe_elemanlar && e.fe_elemanlar.length ? " · FE eleman " + e.fe_elemanlar.map(function (n) { return "e" + n; }).join(", ") : "") + "</p>" +
      (e.hata ? '<div class="hata-kutu" role="alert"><strong>Tahkik edilemedi</strong><div class="se-hata-metin">' + kacis(e.hata) + "</div></div>" : "") +
      ((e.uyarilar || []).length ? '<div class="bn-uyari-kutu">' + e.uyarilar.map(function (u) { return "<div>⚠ " + kacis(adresTurkce(u)) + "</div>"; }).join("") + "</div>" : "") +
      (ozSatir ? '<div class="bn-param-grid bn-dc-ozet">' + ozSatir + "</div>" : "") +
      (kont.length ? '<details class="bn-ayrinti"' + (kont.length <= 8 ? " open" : "") + "><summary>Kontroller (" + kont.length + ")</summary>" + tabloH(["Kontrol", "Talep", "Kapasite", "D/C", "", "Kombinasyon", "Kaynak"], kont, "bn-mini") + "</details>" : "") +
      '<div class="dugmeler"><button type="button" class="dugme kucuk" id="bn-tasarim-hesap"' + (ayr && ayr.then ? " disabled" : "") + ">" + (ayr && ayr.then ? "Hesaplanıyor…" : ayr ? "Ayrıntılı hesabı yenile" : "Ayrıntılı hesap") + "</button></div>" +
      '<div id="bn-tasarim-hesap-kap">' + (ayr && ayr.then ? '<p class="not bn-yukleniyor" role="status"><span class="bn-donen" aria-hidden="true"></span> Ayrıntılı hesap motorda hazırlanıyor' +
        (e.tur === "kolon" && e.sistem !== "celik" ? " (N–M eğrileri ve bütün kombinasyon noktaları; ~190 kB)" : "") + "…</p>" : ayr ? ayrintiliHesapHtml(ayr) : "") + "</div></div>";
  }
  function ayrintiliHesapHtml(y) {
    if (y.hata) return '<div class="hata-kutu" role="alert"><strong>Ayrıntılı hesap alınamadı</strong><div class="se-hata-metin">' + kacis(y.hata) + "</div></div>";
    const s = y.sonuc || {};
    let h = "";
    if (s.egri_x || s.egri_y) {
      h += "<h4>N–M etkileşim diyagramı</h4>" + '<div class="se-seg" role="group" aria-label="Eğilme ekseni">' + ["x", "y"].filter(function (k) { return s["egri_" + k]; }).map(function (k) {
        return '<button type="button" class="se-seg-d" data-nm-eksen="' + k + '" aria-pressed="' + (D.nmEksen === k) + '">M_' + k + " ekseni</button>";
      }).join("") + '</div><div class="se-sekil bn-nm" id="bn-nm"></div>' +
        '<p class="not" id="bn-nm-eksen-not"></p>' +
        '<p class="not">Eğri: kesitin taşıma gücü (N basınç +). Noktalar: her kombinasyonun kolon alt/üst ucundaki eş zamanlı (N, |M|) değerleri; kırmızı nokta D/C > 1. Kesikli ışın orijinden en elverişsiz noktaya, eğriyle kesiştiği yer kapasitedir: D/C = |OP| / |OC|.</p>';
    }
    if (Array.isArray(s.kuvvetler) && s.kuvvetler.length) {
      h += '<details class="bn-ayrinti"><summary>Kombinasyon kuvvetleri (' + s.kuvvetler.length + "; N basınç +)</summary>" + tabloH(["Kombinasyon", "N (kN)", "M_x (kN·m)", "M_y (kN·m)", "V (kN)"].concat(s.kuvvetler[0].dc != null ? ["D/C"] : []),
        s.kuvvetler.map(function (k) { return [k.ad || "", fmt(k.N, 4), fmt(k.Mx, 4), fmt(k.My, 4), fmt(k.V, 4)].concat(k.dc != null ? [dcMetin(k.dc)] : []); }), "bn-mini") + "</details>";
    }
    if ((s.uyarilar || []).length) h += '<div class="bn-uyari-kutu">' + s.uyarilar.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    h += '<div class="anlatim se-anlatim bn-tasarim-anlatim" id="bn-tasarim-anlatim"></div>';
    return h;
  }
  // tasarım ayrıntısını (ve gerekiyorsa N–M ile anlatımı) çiz
  function tasarimAyrintiCiz() {
    const kap = document.getElementById("bn-tasarim-ayrinti");
    if (!kap) return;
    kap.innerHTML = tasarimAyrintiHtml();
    const s = D.tasarimSecim, ayr = s && TASARIM_AYR[s.tur + ":" + s.no];
    if (!ayr || ayr.then || ayr.hata) return;
    nmCiz();
    const an = document.getElementById("bn-tasarim-anlatim");
    if (an && ayr.bloklar && ayr.bloklar.length) {
      A.semaOlaylariBagla(an);
      A.anlatimDersCiz({ ad: ayr.ad || "tasarim", bloklar: ayr.bloklar, zincir: false }, an);
    }
  }
  function nmCiz() {
    const kap = document.getElementById("bn-nm"), s = D.tasarimSecim, ayr = s && TASARIM_AYR[s.tur + ":" + s.no];
    if (!kap || !ayr || !ayr.sonuc) return;
    if (!ayr.sonuc["egri_" + D.nmEksen]) D.nmEksen = ayr.sonuc.egri_x ? "x" : "y";
    document.querySelectorAll("#bn-tasarim-ayrinti [data-nm-eksen]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.nmEksen === D.nmEksen)); });
    kap.innerHTML = nmSvg(ayr.sonuc, D.nmEksen, Math.max(260, Math.min(640, kap.clientWidth || 480)));
    const en = document.getElementById("bn-nm-eksen-not"), ee = ayr.sonuc.egri_eksen;
    if (en) en.textContent = ee && ee["egri_" + D.nmEksen] ? "M_" + D.nmEksen + ": " + ee["egri_" + D.nmEksen] + "." : "";
  }
  // egri: [{N, M}] (§11) ya da tasarim.kolon_etkilesim çıktısı {noktalar: [{N_kN, M_kNm}]}
  function egriNokta(e) {
    const l = Array.isArray(e) ? e : (e && e.noktalar) || [];
    return l.map(function (p) { return { N: +(p.N != null ? p.N : p.N_kN), M: Math.abs(+(p.M != null ? p.M : p.M_kNm)) }; }).filter(function (p) { return isFinite(p.N) && isFinite(p.M); }).sort(function (a, b) { return a.N - b.N; });
  }
  function nmSvg(son, eksen, W) {
    const egri = egriNokta(son["egri_" + eksen]);
    if (egri.length < 2) return '<p class="not">Etkileşim eğrisi verisi yok.</p>';
    const nk = (son.noktalar || []).map(function (p) {
      const M = Math.abs(+(eksen === "y" ? (p.My != null ? p.My : p.My_tasarim_kNm) : (p.Mx != null ? p.Mx : p.Mx_tasarim_kNm)) || 0), N = +(p.N != null ? p.N : p.Nd_kN) || 0;
      const dc = eksen === "y" ? (p.dc_y != null ? p.dc_y : p.dc) : (p.dc_x != null ? p.dc_x : p.dc);
      return { ad: p.ad || "", N: N, M: M, dc: +dc || 0 };
    });
    const H = Math.round(Math.min(420, Math.max(240, W * 0.78))), pl = 56, pr = 16, pu = 16, pa = 36;
    const Mmax = Math.max.apply(null, egri.map(function (p) { return p.M; }).concat(nk.map(function (p) { return p.M; }))) * 1.12 || 1;
    const Nlo = Math.min(0, Math.min.apply(null, egri.map(function (p) { return p.N; }).concat(nk.map(function (p) { return p.N; })))) * 1.06;
    const Nhi = Math.max.apply(null, egri.map(function (p) { return p.N; }).concat(nk.map(function (p) { return p.N; }))) * 1.06 || 1;
    const X = function (m) { return pl + m / Mmax * (W - pl - pr); }, Y = function (n) { return H - pa - (n - Nlo) / (Nhi - Nlo) * (H - pa - pu); };
    const adim = function (aralik) { const k = Math.pow(10, Math.floor(Math.log10(aralik / 5))); return [1, 2, 5, 10].map(function (c) { return c * k; }).filter(function (c) { return aralik / c <= 6; })[0] || k * 10; };
    let s = "";
    const aN = adim(Nhi - Nlo), aM = adim(Mmax);
    for (let n = Math.ceil(Nlo / aN) * aN; n <= Nhi + 1e-9; n += aN) s += '<path class="bn-spek-izgara" d="M' + pt(pl - 4, Y(n)) + " L" + pt(W - pr, Y(n)) + '"/>' + metinSvg(pl - 6, Y(n) + 4, fmt(n, 4), "bn-spek-t", "end");
    for (let m = 0; m <= Mmax + 1e-9; m += aM) s += '<path class="bn-spek-izgara" d="M' + pt(X(m), Y(Nlo)) + " L" + pt(X(m), pu) + '"/>' + metinSvg(X(m), H - pa + 15, fmt(m, 4), "bn-spek-t", "middle");
    s += '<path class="se-eksen" d="M' + pt(pl, Y(0)) + " L" + pt(W - pr, Y(0)) + " M" + pt(X(0), Y(Nlo)) + " L" + pt(X(0), pu) + '"/>';
    // N sınırları (TBDY 0,40 fck Ac; TS 500 0,9 fcd Ac)
    const oz = son.ozet || {};
    [[oz.N_sinir_TBDY_kN, "0,40·f_ck·A_c"], [oz.N_sinir_TS500_kN, "0,9·f_cd·A_c"]].forEach(function (c) {
      if (typeof c[0] === "number" && c[0] < Nhi) s += '<path class="bn-nm-sinir" d="M' + pt(X(0), Y(c[0])) + " L" + pt(W - pr, Y(c[0])) + '"/>' + metinSvg(W - pr - 2, Y(c[0]) - 4, c[1] + " = " + f1(c[0]), "bn-spek-t bn-nm-sinir-t", "end");
    });
    let d = "M" + pt(X(0), Y(egri[0].N));
    egri.forEach(function (p) { d += " L" + pt(X(p.M), Y(p.N)); });
    d += " L" + pt(X(0), Y(egri[egri.length - 1].N));
    s += '<path class="bn-nm-egri" d="' + d + ' Z"/>';
    // noktalar (D/C > 1 kırmızı); en elverişsiz nokta için orijinden ışın ve eğri kesişimi
    let en = null;
    nk.forEach(function (p) { if (!en || p.dc > en.dc) en = p; });
    nk.forEach(function (p) {
      s += '<circle class="bn-nm-n' + (p.dc > 1 + 1e-9 ? " bn-nm-asim" : "") + '" cx="' + r1(X(p.M)) + '" cy="' + r1(Y(p.N)) + '" r="3.4"><title>' + kacis(p.ad + ": N = " + f1(p.N) + " kN, M = " + f1(p.M) + " kN·m, D/C = " + f2(p.dc)) + "</title></circle>";
    });
    if (en && (en.M > 1e-9 || Math.abs(en.N) > 1e-9)) {
      let tK = null;
      for (let i = 0; i < egri.length - 1; i++) {
        const a = egri[i], b = egri[i + 1], dM = b.M - a.M, dN = b.N - a.N, den = en.M * dN - en.N * dM;
        if (Math.abs(den) < 1e-12) continue;
        const t = (a.M * dN - a.N * dM) / den, u = (a.M * en.N - a.N * en.M) / den;
        if (t > 0 && u >= -1e-9 && u <= 1 + 1e-9 && (tK == null || t < tK)) tK = t;
      }
      const uc = tK != null ? Math.max(tK, 1) : 1.15;
      s += '<path class="bn-nm-isin" d="M' + pt(X(0), Y(0)) + " L" + pt(X(en.M * uc), Y(en.N * uc)) + '"/>';
      if (tK != null) s += '<rect class="bn-nm-kap" x="' + r1(X(en.M * tK) - 4.5) + '" y="' + r1(Y(en.N * tK) - 4.5) + '" width="9" height="9" transform="rotate(45 ' + r1(X(en.M * tK)) + " " + r1(Y(en.N * tK)) + ')"><title>Kapasite C: N = ' + kacis(f1(en.N * tK)) + " kN, M = " + kacis(f1(en.M * tK)) + " kN·m</title></rect>";
      s += '<circle class="bn-nm-en' + (en.dc > 1 + 1e-9 ? " bn-nm-asim" : "") + '" cx="' + r1(X(en.M)) + '" cy="' + r1(Y(en.N)) + '" r="6"/>' +
        metinSvg(Math.min(W - pr - 4, X(en.M) + 9), Y(en.N) - 8, "P: D/C = " + f2(en.dc), "bn-spek-t bn-spek-vurgu", X(en.M) > W * 0.6 ? "end" : "start");
    }
    s += metinSvg((pl + W - pr) / 2, H - 4, "M_" + eksen + " (kN·m)", "bn-spek-t", "middle") + metinSvg(6, pu + 4, "N (kN)", "bn-spek-t", "start");
    return '<svg class="se-svg bn-nm-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="N–M' + eksen + ' etkileşim diyagramı"><title>N–M etkileşimi (M_' + eksen + "), " + nk.length + " kombinasyon noktası; en büyük D/C " + kacis(f2(en ? en.dc : 0)) + "</title>" + s + "</svg>";
  }
  // Eleman seçimi (sahne ya da tablo): ayrıntı paneli, tablo satırı vurgusu, 3B seçim
  function tasarimSec(tur, no, kaydir) {
    const e = tasarimKaydi(tur, no);
    D.tasarimSecim = e ? { tur: tur, no: no } : null;
    D.secim = e ? [sahneAnahtari(e)] : [];
    if (e && D.kat !== e.kat && B.katlar.some(function (k) { return k.no === e.kat; })) D.kat = e.kat;
    yenile();
    tasarimAyrintiCiz();
    document.querySelectorAll("#bn-sekme-icerik tr.bn-dc-satir").forEach(function (r) {
      const a = e && r.dataset.dcTur === tur && +r.dataset.dcNo === no;
      r.classList.toggle("aktif", !!a); r.setAttribute("aria-selected", String(!!a));
    });
    if (!e) { A.toast("Bu eleman için tasarım kaydı yok."); return; }
    if (kaydir) { const k = document.getElementById("bn-tasarim-ayrinti"); if (k) k.scrollIntoView({ block: "nearest", behavior: azHareket() ? "auto" : "smooth" }); }
  }
  // Ayrıntılı hesap: bina_eleman_tasarim {cozum_kimligi, tur, no, bina} → {ad, bloklar, sonuc (+ egri_x, egri_y, noktalar), hata}
  function ayrintiliHesap() {
    const s = D.tasarimSecim, v = V();
    if (!s || !v) return;
    const anahtar = s.tur + ":" + s.no, sonSON = SON, h = tasarimIstekHedefi(tasarimKaydi(s.tur, s.no), s);
    const p = A.motorIstegi({ islem: "bina_eleman_tasarim", girdi: { cozum_kimligi: v.cozum_kimligi || null, tur: h.tur, no: h.no, bina: SON.bina || kopya(B) } }).then(function (y) {
      if (SON !== sonSON) return;
      if (!y) y = { hata: "Boş yanıt." };
      if (y.hata && /Bilinmeyen işlem/.test(y.hata)) y = { hata: "Bu motor sürümü eleman tasarım ayrıntısını (bina_eleman_tasarim) henüz desteklemiyor. Özet ve kontroller yukarıda." };
      TASARIM_AYR[anahtar] = y;
    }, function (e) { if (SON === sonSON) TASARIM_AYR[anahtar] = { hata: (e && e.message) ? e.message : String(e) }; }).then(function () {
      const c = D.tasarimSecim;
      if (c && c.tur + ":" + c.no === anahtar && D.sekme === "tasarim") tasarimAyrintiCiz();
    });
    TASARIM_AYR[anahtar] = p;
    tasarimAyrintiCiz();
  }
  // ---------- Anlatım ----------
  // ---------- Temel sekmesi (veri.temel, tasarım §13): taban basıncı / oturma haritası, özet, zımbalama, donatı, uyarılar ----------
  // Tek renk tonlu sıralı ölçek (açık → koyu mavi; koyu temada ters: küçük değer zemine yakın koyu ton). Aşım ve çekme ayrıca desen + kenarla.
  const ISI_RAMPA = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"];
  function koyuTema() {
    const t = document.documentElement.dataset.tema;
    if (t === "koyu") return true;
    if (t === "acik") return false;
    return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  }
  function isiRengi(u) {
    const r = koyuTema() ? ISI_RAMPA.slice().reverse() : ISI_RAMPA;
    const x = Math.max(0, Math.min(1, isFinite(u) ? u : 0)) * (r.length - 1), i = Math.min(r.length - 2, Math.floor(x)), f = x - i;
    const h = function (s, k) { return parseInt(s.substr(1 + 2 * k, 2), 16); };
    return "rgb(" + [0, 1, 2].map(function (k) { return Math.round(h(r[i], k) + (h(r[i + 1], k) - h(r[i], k)) * f); }).join(",") + ")";
  }
  function temelDurumAdi(t) { return (t.belirleyen_servis || t.durum || "G+Q") + " (servis)"; }
  function farkliOturmaMetin(t) {
    if (t.farkli_oturma_metin) return t.farkli_oturma_metin;
    const fo = t.farkli_oturma, o = typeof fo === "number" ? fo : fo && fo.oran;
    if (o == null || !isFinite(o)) return "—";
    return o > 1e-12 ? "1/" + Math.round(1 / o).toLocaleString("tr-TR") : "—";
  }
  function temelTasarim(t, tur) { return (Array.isArray(t.tasarim) ? t.tasarim : []).filter(function (x) { return x.tur === tur; }); }
  // Tekil temeller: veri.akis.temeller içinde yalnız boyutlu (B, L) temel mesnetleri. Eski genel model çözümleri açık mesnetleri de
  // (aks null, B yok) buraya yazar; onlar mesnet tepkisi tablosuna gider (sözleşme C2).
  function tekilTemeller(v) { return ((v && v.akis && v.akis.temeller) || []).filter(function (t) { return t && t.B != null; }); }
  function dugumAdresV(v, no) { const d = ((v && v.ag && v.ag.dugumler) || []).filter(function (x) { return x.no === no; })[0]; return d && d.adres ? d.adres : "D" + no; }
  function temelEtiketi(t) { return "T-" + (Array.isArray(t.aks) ? adres(t.aks) : (t.adres || "D" + t.dugum)); }
  // açık mesnetler (veri.akis.mesnetler; eski çözümde temeller içindeki B'siz kayıtlar)
  function acikMesnetler(v) {
    const a = (v && v.akis) || {}, l = Array.isArray(a.mesnetler) ? a.mesnetler.slice() : [];
    (a.temeller || []).forEach(function (t) { if (t && t.B == null && !l.some(function (m) { return m.dugum === t.dugum; })) l.push(t); });
    return l;
  }
  // Tekil temel tablosu (veri.akis.temeller; servis G+Q) — Tablolar sekmesi ve Temel sekmesi (tekil / eski motor) ortak
  function tekilTemelTablosu(v) {
    return tabloH(["Temel", "B×L (m)", "N (kN)", "M_X", "M_Y", "σ_max", "σ_min", "e_X / e_Y", "D/C"], tekilTemeller(v).map(function (t) {
      return [temelEtiketi(t), f2(t.B) + "×" + f2(t.L), f1(t.N_servis), f1(t.MX), f1(t.MY), f1(t.sigma_max), f1(t.sigma_min), f2(t.e_X) + " / " + f2(t.e_Y) + (t.cekirdek_icinde ? "" : " (!)"), '<b class="' + (t.DC > 1 ? "bn-kotu" : "bn-iyi") + '">' + f2(t.DC) + "</b>"];
    }));
  }
  // Açık mesnet tipi okunur: motorun "ozel" tipi serbestliklerinden (veri.ag.mesnetler ux…rz) Mesnet aracı adıyla ya da tutulu /
  // serbest doğrultularla ("özel (tutulu: uz; serbest: ux, uy, rx, ry, rz)")
  const MESNET_TIP_AD = { ankastre: "ankastre", mafsal: "sabit mafsal", elastik: "elastik", yay: "yay" };
  const MESNET_KAYICI = [["kayıcı (X serbest)", [0, 1, 1, 0, 0, 0]], ["kayıcı (Y serbest)", [1, 0, 1, 0, 0, 0]], ["kayıcı (X, Y serbest)", [0, 0, 1, 0, 0, 0]]];
  function mesnetTipEtiketi(v, m) {
    if (!m) return "—";
    const tip = m.tip || "";
    if (tip !== "ozel") return MESNET_TIP_AD[tip] || tip || "—";
    const a = ((v && v.ag && v.ag.mesnetler) || []).filter(function (x) { return x.dugum === m.dugum; })[0] || m;
    const SD = ["ux", "uy", "uz", "rx", "ry", "rz"];
    if (!SD.some(function (k) { return typeof a[k] === "boolean"; })) return "özel";
    const b = SD.map(function (k) { return a[k] ? 1 : 0; });
    const hazir = MESNET_KAYICI.filter(function (h) { return h[1].join("") === b.join(""); })[0];
    if (hazir) return hazir[0];
    const tut = SD.filter(function (k, i) { return b[i]; }), ser = SD.filter(function (k, i) { return !b[i]; });
    return "özel (tutulu: " + (tut.join(", ") || "—") + "; serbest: " + (ser.join(", ") || "—") + ")";
  }
  function mesnetTepkiTablosu(v) {
    const l = acikMesnetler(v);
    if (!l.length) return "";
    return "<h4>Mesnet tepkileri (açık mesnetler; servis, kN · kN·m)</h4>" + tabloH(["Mesnet", "Tip", "N_G", "N_Q", "N_G + N_Q", "M_X", "M_Y"], l.map(function (m) {
      return [m.adres || dugumAdresV(v, m.dugum), mesnetTipEtiketi(v, m), f1(m.N_G), f1(m.N_Q), f1((+m.N_G || 0) + (+m.N_Q || 0)), f1(m.MX), f1(m.MY)];
    })) + '<p class="not">Açık mesnetler (Mesnet aracı) temel değildir: boyut ve taban basıncı tahkiki yapılmaz, yalnız tepkiler verilir.</p>';
  }
  function temelPrm(ad, deger, ek) { return '<div class="bn-param"><span>' + ad + "</span><b>" + deger + "</b>" + (ek ? '<span class="bn-kaynak">' + ek + "</span>" : "") + "</div>"; }
  // Tekil temel (ya da temel ayrıntısı döndürmeyen eski motor): özet + tekil temel tablosu; harita yok
  function tekilTemelSekmesi(v, t) {
    const tl = tekilTemeller(v), qem = t && t.q_em != null ? t.q_em : (v.bina.temeller && v.bina.temeller.zemin && v.bina.temeller.zemin.q_em);
    const sm = tl.length ? Math.max.apply(null, tl.map(function (x) { return +x.sigma_max; })) : (t ? t.p_maks : null);
    const sn = tl.length ? Math.min.apply(null, tl.map(function (x) { return +x.sigma_min; })) : (t ? t.p_min : null);
    const dc = tl.length ? Math.max.apply(null, tl.map(function (x) { return +x.DC; })) : (t ? t.DC_zemin : null);
    const tip = (t && t.tip) || (v.bina.temeller && v.bina.temeller.tip) || "tekil";
    let h = '<div class="bn-temel-ozet"><h4>' + kacis((TEMEL_TIP_AD[tip] || "Tekil") + " temel · G+Q (servis)") + "</h4>" +
      '<div class="bn-param-grid bn-temel-param">' + temelPrm("σ_maks (kN/m²)", sm != null ? f1(sm) : "—", qem != null ? "q_em = " + f1(qem) : "") +
      temelPrm("σ_min (kN/m²)", sn != null ? f1(sn) : "—", sn != null && sn < 0 ? "zeminde çekme" : "") +
      temelPrm("Zemin D/C (σ_maks / q_em)", dc != null ? dcCip(dc) : "—", "TS 500 emniyet, servis") + "</div></div>";
    h += "<h4>Tekil temeller (servis G+Q)</h4>" + (tl.length ? tekilTemelTablosu(v) : '<p class="not">Tekil temel kaydı yok.</p>');
    h += mesnetTepkiTablosu(v);
    const genel = v.model === "genel";
    h += '<p class="not">' + (tip === "tekil" ? "Tekil temelde her kolonun altında ayrı pabuç vardır; taban basıncı σ = N/(B·L) ± 6M/(B·L²). " +
        (genel ? TEMEL_S3_TEKIL + " Zemin basıncı ve oturma haritası mütemadi ve radye temelde çizilir (Bina / temel panelinden temel tipini değiştirin)."
          : "Zemin basıncı ve oturma haritası mütemadi ve radye temelde çizilir (Bina / temel panelinden temel tipini değiştirin).")
      : "Bu çözümde temel ızgarasının düğüm basınçları yok (motor temel ayrıntısı döndürmedi); yalnız tekil temel özeti gösteriliyor. Binayı yeniden çözün.") + "</p>";
    return h;
  }
  // Kontrol listesi tablosu (zemin emniyeti, TBDY 16.8 taşıma gücü, en küçük kalınlıklar)
  function temelKontrolTablosu(l) {
    return '<div class="se-tablo-kutu"><table class="se-sonuc-tablo bn-temel-kontrol"><thead><tr><th scope="col">Kontrol</th><th scope="col">Talep</th><th scope="col">Sınır</th><th scope="col">D/C</th><th scope="col">Kaynak</th></tr></thead><tbody>' +
      l.map(function (k) {
        const b = k.birim ? " " + kacis(k.birim) : "", kosul = k.kosul;
        return '<tr class="' + (k.saglandi === false ? "bn-drift-asim" : "") + '"><th scope="row">' + kacis(k.ad) + (k.kombinasyon ? ' <span class="bn-kaynak">' + kacis(k.kombinasyon) + "</span>" : "") + "</th>" +
          '<td class="sayi">' + (kosul ? "≥ " : "") + fmt(k.talep, 3) + b + '</td><td class="sayi">' + fmt(k.kapasite, 3) + b + "</td><td>" + dcCip(k.dc) + '</td><td class="bn-kaynak-h">' + kacis(k.kaynak || "") + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }
  function temelSekmesi() {
    const v = V(), t = v.temel || null;
    if (!temelVar()) return tekilTemelSekmesi(v, t);
    const dg = t.dugumler, m = t.model || {}, zb = v.bina.temeller && v.bina.temeller.zemin || {};
    const cekme = dg.filter(function (d) { return d.p_kNm2 < 0; });
    const qem = t.q_em != null ? t.q_em : zb.q_em, k0 = m.k0 != null ? m.k0 : t.k0 != null ? t.k0 : zb.k0;
    const zk = (t.zemin_kontrolleri || []).concat(t.kontroller || []);
    const tbdy = (t.zemin_kontrolleri || []).filter(function (k) { return /TBDY/.test(k.ad || ""); })[0];
    let h = '<div class="bn-temel-ozet"><h4>' + kacis((TEMEL_TIP_AD[t.tip] || t.tip || "Temel") + " temel · " + temelDurumAdi(t)) + "</h4>" +
      '<div class="bn-param-grid bn-temel-param">' +
      temelPrm("p_maks (kN/m²)", f1(t.p_maks), qem != null ? "q_em = " + f1(qem) : "") +
      temelPrm("p_min (kN/m²)", f1(t.p_min), t.p_min < 0 ? "zeminde çekme (ayrılma)" : "") +
      temelPrm("Zemin D/C (p_maks / q_em)", dcCip(t.DC_zemin), "TS 500 emniyet, servis") +
      (tbdy ? temelPrm("Taşıma gücü D/C (q_o / q_t)", dcCip(tbdy.dc), "q_o = " + f1(tbdy.talep) + " (" + kacis(tbdy.kombinasyon || "katsayılı") + ") · q_t = " + f1(tbdy.kapasite) + " kN/m²") : "") +
      temelPrm("Oturma maks (mm)", f1(t.oturma_maks_mm), t.oturma_min_mm != null ? "min " + f1(t.oturma_min_mm) + " mm" : "") +
      temelPrm("Farklı oturma (Δw / L)", kacis(farkliOturmaMetin(t)), t.farkli_oturma_yer ? "kolonlar " + kacis(t.farkli_oturma_yer) : "komşu kolonlar arası") +
      temelPrm("k₀ (kN/m³)", k0 != null ? Math.round(k0).toLocaleString("tr-TR") : "—", "Winkler yatak katsayısı") +
      (m.dugum_sayisi ? temelPrm("Model", m.dugum_sayisi + " düğüm · " + m.eleman_sayisi + " eleman", (m.taban_alani != null ? "taban " + f1(m.taban_alani) + " m²" : "") + (m.W_temel != null ? " · öz ağırlık " + f1(m.W_temel) + " kN" : "")) : "") +
      (t.en_buyuk_dc != null ? temelPrm("Temel D/C maks", dcCip(t.en_buyuk_dc), "zemin + kesit + zımbalama") : "") +
      "</div></div>";
    const uy = (t.uyarilar || []).slice();
    if (cekme.length && !uy.some(function (u) { return /çekme|ayrıl/i.test(u); })) uy.unshift(cekme.length + " düğümde taban basıncı negatif (p < 0): temel zeminden ayrılıyor. Winkler yayı çekme taşıyamaz; sonuç yaklaşıktır, temel boyutunu ya da kalınlığını artırın.");
    if (uy.length) h += '<div class="bn-uyari-kutu bn-temel-uyari">' + uy.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    else h += '<div class="bn-iyi-kutu">Zeminde çekme yok; taban basıncı her yerde basınç.</div>';
    if ((t.oneriler || []).length) h += '<div class="bn-uyari-kutu">' + t.oneriler.map(function (u) { return "<div>→ " + kacis(u) + "</div>"; }).join("") + "</div>";
    h += '<div class="bn-satir"><div class="se-seg" role="group" aria-label="Harita">' +
      '<button type="button" class="se-seg-d" data-temel-harita="p" aria-pressed="' + (D.temelHarita !== "w") + '">Taban basıncı (kN/m²)</button>' +
      '<button type="button" class="se-seg-d" data-temel-harita="w" aria-pressed="' + (D.temelHarita === "w") + '">Oturma (mm)</button></div></div>' +
      '<div class="se-sekil bn-temel-harita" id="bn-temel-harita"></div><p class="not" id="bn-temel-bilgi" aria-live="polite"></p>';
    if (zk.length) h += "<h4>Zemin ve boyut kontrolleri</h4>" + temelKontrolTablosu(zk);
    // temel kirişleri (mütemadi; kirişli radyede aks kirişleri)
    const tk = temelTasarim(t, "temel-kirisi");
    if (tk.length) {
      h += "<h4>Temel kirişleri (TS 500; katsayılı kombinasyonların zarfı)</h4>" + '<div class="se-tablo-kutu"><table class="se-sonuc-tablo bn-temel-donati"><thead><tr><th scope="col">Kiriş</th><th scope="col">b × h (m)</th><th scope="col">M_d alt / üst (kN·m)</th><th scope="col">As alt / üst (cm²)</th><th scope="col">Öneri alt / üst</th><th scope="col">V_d (kN) · etriye</th><th scope="col">D/C</th><th scope="col"><span class="bn-gizli-etiket">Diyagram</span></th></tr></thead><tbody>' +
        tk.map(function (d) {
          const ad = "TK-" + (d.hat != null ? d.hat : d.aks || ""), fil = (d.yon === "y" ? "x:" : "y:") + (d.hat != null ? d.hat : d.aks);
          return '<tr class="' + (d.dc > 1 ? "bn-drift-asim" : "") + '"><th scope="row">' + kacis(ad) + ' <span class="bn-kaynak">' + (d.yon === "y" ? "Y" : "X") + " doğr.</span></th>" +
            '<td class="sayi">' + f2(d.b) + " × " + f2(d.h) + '</td><td class="sayi">' + f1(d.Md_alt != null ? d.Md_alt : d.Md_mesnet) + " / " + f1(d.Md_ust != null ? d.Md_ust : d.Md_aciklik) + '</td><td class="sayi">' + f2(d.As_alt_cm2) + " / " + f2(d.As_ust_cm2) +
            "</td><td>" + kacis((d.oneri_alt || "—") + " / " + (d.oneri_ust || "—")) + '</td><td class="sayi">' + f1(d.Vd) + (d.etriye ? " · " + kacis(d.etriye) : "") + "</td><td>" + dcCip(d.dc) + (d.oneri ? '<div class="bn-kaynak">' + kacis(d.oneri) + "</div>" : "") +
            '</td><td><button type="button" class="dugme kucuk" data-temel-sekme-git="diyagram" data-temel-aks-filtre="' + kacis(fil) + '" aria-label="' + kacis(ad) + ' diyagramları">Diyagram</button></td></tr>';
        }).join("") + "</tbody></table></div>";
    }
    const tb = temelTasarim(t, "tabla");
    if (tb.length) {
      h += "<h4>Tabla konsolu (m başına; ters T)</h4>" + tabloH(["Tabla", "Konsol c (m)", "p_d (kN/m²)", "M (kN·m/m)", "V (kN/m)", "h (m)", "As (cm²/m)", "Öneri", "D/C"], tb.map(function (d) {
        return ["Tabla", f2(d.konsol_boyu), f1(d.p_d), f1(d.M_m), f1(d.V_m), f2(d.h), f2(d.As_cm2_m), d.oneri_donati || "—", dcCip(d.dc)];
      }));
    }
    const rs = temelTasarim(t, "radye-serit");
    if (rs.length) {
      h += "<h4>Radye donatısı (m başına; ρ_min = 0,002)</h4>" + tabloH(["Doğrultu", "h (m)", "m alt / üst (kN·m/m)", "As alt / üst (cm²/m)", "As_min (cm²/m)", "Öneri alt / üst", "D/C"], rs.map(function (d) {
        return [d.yon === "y" ? "Y doğrultusu" : "X doğrultusu", f2(d.h), f1(d.M_alt_m) + " / " + f1(d.M_ust_m), f2(d.As_alt_cm2_m) + " / " + f2(d.As_ust_cm2_m), f2(d.As_min_cm2_m), (d.oneri_alt || "—") + " / " + (d.oneri_ust || "—"), dcCip(d.dc)];
      }));
    }
    const zm = temelTasarim(t, "zimbalama");
    h += "<h4>Zımbalama (TS 500 md. 8.3)</h4>";
    if (zm.length) {
      h += '<div class="se-tablo-kutu"><table class="se-sonuc-tablo bn-temel-zimba"><thead><tr><th scope="col">Kolon</th><th scope="col">Konum</th><th scope="col">N_d (kN)</th><th scope="col">Zemin tepkisi F_a (kN)</th><th scope="col">V_pd (kN)</th><th scope="col">u_p (m)</th><th scope="col">d (m)</th><th scope="col">V_pr (kN)</th><th scope="col">D/C</th></tr></thead><tbody>' +
        zm.map(function (z) {
          const ad = z.adres || (Array.isArray(z.aks) ? "S-" + z.aks.join("") : z.kolon_no != null ? kolonAdres(z.kolon_no) : "—");
          return '<tr class="' + (z.dc > 1 ? "bn-drift-asim" : "") + '"><th scope="row">' + kacis(ad) + (z.kombinasyon ? ' <span class="bn-kaynak">' + kacis(z.kombinasyon) + "</span>" : "") + "</th><td>" + kacis(z.konum || "—") + '</td><td class="sayi">' + f1(z.N_d) + '</td><td class="sayi">' + f1(z.F_a) + '</td><td class="sayi">' + f1(z.V_pd) + '</td><td class="sayi">' + f2(z.u_p) + '</td><td class="sayi">' + f2(z.d) + '</td><td class="sayi">' + f1(z.V_pr) + "</td><td>" + dcCip(z.dc) + "</td></tr>";
        }).join("") + '</tbody></table></div><p class="not">V_pd = N_d − F_a (zımbalama çevresi içindeki zemin tepkisi); V_pr = γ·f_ctd·u_p·d, u_p kolon yüzünden d/2 uzaklıkta (kenar ve köşe kolonda açık çevre).</p>';
    } else h += '<p class="not">' + (t.tip === "surekli" ? "Mütemadi temelde kolon yükü temel kirişine aktarılır; zımbalama yerine kiriş kesmesi ve tabla kesmesi denetlenir (yukarıdaki tablolar)."
      : t.tip === "radye" && m.kiris ? "Kirişli radyede kolonlar temel kirişlerine oturur; zımbalama yerine kiriş kesmesi denetlenir." : "Zımbalama kaydı yok.") + "</p>";
    if ((v.ag.elemanlar || []).some(function (e) { return e.tur === "temel-kirisi"; }))
      h += '<p class="not">Temel kirişlerinin N, V, M diyagramları Diyagramlar sekmesinde (aks filtresiyle tek kiriş). <button type="button" class="dugme kucuk" data-temel-sekme-git="diyagram">Diyagramlara git</button></p>';
    const nt = (t.notlar || []).concat(t.varsayimlar || []);
    if (nt.length) h += '<details class="bn-ayrinti"><summary>Model notları ve varsayımlar (' + nt.length + ")</summary>" + nt.map(function (n) { return '<p class="not">' + kacis(n) + "</p>"; }).join("") + "</details>";
    return h;
  }
  // Düğüm hücreleri: dikdörtgen ızgarada (radye) her düğümün etki alanı komşu düğümlere olan uzaklıkların yarısıdır (düzgün olmayan ızgara da)
  function temelHucreleri(dg, sinirlar) {
    const yuv = function (x) { return Math.round(x * 1e4) / 1e4; }, satir = {}, sutun = {};
    dg.forEach(function (d) { (satir[yuv(d.Y)] = satir[yuv(d.Y)] || []).push(d.X); (sutun[yuv(d.X)] = sutun[yuv(d.X)] || []).push(d.Y); });
    Object.keys(satir).forEach(function (k) { satir[k].sort(function (a, b) { return a - b; }); });
    Object.keys(sutun).forEach(function (k) { sutun[k].sort(function (a, b) { return a - b; }); });
    const komsu = function (l, x, s0, s1) {
      const i = l.indexOf(x), a = i > 0 ? (l[i - 1] + x) / 2 : s0, b = i >= 0 && i < l.length - 1 ? (l[i + 1] + x) / 2 : s1;
      return [Math.max(s0, a), Math.min(s1, b)];
    };
    return dg.map(function (d) {
      const xr = komsu(satir[yuv(d.Y)], d.X, sinirlar.x0, sinirlar.x1), yr = komsu(sutun[yuv(d.X)], d.Y, sinirlar.y0, sinirlar.y1);
      return { d: d, x0: xr[0], x1: xr[1], y0: yr[0], y1: yr[1] };
    });
  }
  // Plan haritası: radyede düğüm etki hücreleri, mütemadide kiriş boyunca B genişlikte şeritler (her düğüm komşu eleman yarılarını boyar);
  // tek tonlu sıralı ölçek + lejant (0 … üst sınır; basınçta q_em çizgisi), en büyük değer işareti, akslar ve kolonlar
  function temelHaritaCiz() {
    const kap = document.getElementById("bn-temel-harita"), v = V();
    if (!kap || !v || !v.temel) return;
    document.querySelectorAll("#bn-sonuc [data-temel-harita]").forEach(function (b) { b.setAttribute("aria-pressed", String((b.dataset.temelHarita === "w") === (D.temelHarita === "w"))); });
    const t = v.temel, dg = (t.dugumler || []).filter(function (d) { return isFinite(d.X) && isFinite(d.Y); }), m = t.model || {}, wk = D.temelHarita === "w", ana = wk ? "w_mm" : "p_kNm2";
    if (!dg.length) { kap.innerHTML = ""; return; }
    const nd = {}; dg.forEach(function (d) { nd[d.no] = d; });
    const qem = t.q_em != null ? +t.q_em : null;
    const kirisEl = (t.elemanlar || []).filter(function (e) { return e.tur === "temel-kirisi" && e.dugumler && nd[e.dugumler[0]] && nd[e.dugumler[1]]; });
    const radye = t.tip === "radye" || !kirisEl.length;
    const Bs = +((m.kesit && m.kesit.B) || t.B || (v.bina.temeller && v.bina.temeller.surekli && v.bina.temeller.surekli.B) || 1);
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    dg.forEach(function (d) { x0 = Math.min(x0, d.X); x1 = Math.max(x1, d.X); y0 = Math.min(y0, d.Y); y1 = Math.max(y1, d.Y); });
    if (radye && m.plak && isFinite(m.plak.X0)) { x0 = Math.min(x0, m.plak.X0); x1 = Math.max(x1, m.plak.X1); y0 = Math.min(y0, m.plak.Y0); y1 = Math.max(y1, m.plak.Y1); }
    const pay = radye ? 0 : Bs / 2;
    x0 -= pay; x1 += pay; y0 -= pay; y1 += pay;
    const W = Math.max(280, Math.min(960, kap.clientWidth || 600)), pl = 34, pr = 34, pu = 26, lejH = 62;
    const sc = Math.min((W - pl - pr) / Math.max(0.5, x1 - x0), Math.min(520, Math.max(240, window.innerHeight * 0.5)) / Math.max(0.5, y1 - y0));
    const Hp = (y1 - y0) * sc, H = Math.round(pu + Hp + 24 + lejH);
    const ox = ((W - pl - pr) - (x1 - x0) * sc) / 2;
    const X = function (x) { return pl + (x - x0) * sc + ox; }, Y = function (y) { return pu + (y1 - y) * sc; };
    const degerler = dg.map(function (d) { return +d[ana]; }).filter(isFinite);
    const vmax = Math.max.apply(null, degerler), vmin = Math.min.apply(null, degerler);
    // renk ölçeği değer aralığında (küçük farklar da görünsün); negatif (çekme / kalkma) hücreler ayrıca taralı
    let alt = Math.max(0, vmin), ust = Math.max(vmax, 1e-9);
    if (ust - alt < 1e-6 * Math.max(1, ust)) alt = 0;
    const u = function (val) { return (val - alt) / (ust - alt); };
    const sinif = function (val) { return (val < 0) ? " bn-isi-cekme" : (!wk && qem != null && val > qem) ? " bn-isi-asim" : ""; };
    const baslik = function (d) { return "Düğüm " + d.no + " (X " + f2(d.X) + ", Y " + f2(d.Y) + " m): p = " + f1(d.p_kNm2) + " kN/m², oturma = " + f2(d.w_mm) + " mm"; };
    let s = "";
    if (radye) {
      temelHucreleri(dg, { x0: x0, x1: x1, y0: y0, y1: y1 }).forEach(function (c) {
        const val = +c.d[ana];
        s += '<rect class="bn-isi' + sinif(val) + '" x="' + r1(X(c.x0)) + '" y="' + r1(Y(c.y1)) + '" width="' + r1((c.x1 - c.x0) * sc + 0.6) + '" height="' + r1((c.y1 - c.y0) * sc + 0.6) + '" fill="' + isiRengi(u(Math.max(0, val))) + '" data-tdugum="' + c.d.no + '"><title>' + kacis(baslik(c.d)) + "</title></rect>";
      });
      s += '<rect class="bn-isi-cerceve" x="' + r1(X(x0)) + '" y="' + r1(Y(y1)) + '" width="' + r1((x1 - x0) * sc) + '" height="' + r1((y1 - y0) * sc) + '"/>';
      // kirişli radye: aks kirişleri çizgi
      kirisEl.forEach(function (e) { const p = nd[e.dugumler[0]], q = nd[e.dugumler[1]]; s += '<path class="bn-isi-kiris" d="M' + pt(X(p.X), Y(p.Y)) + " L" + pt(X(q.X), Y(q.Y)) + '"/>'; });
    } else {
      // her eleman iki yarıya: uç düğümün değeriyle boyanır (düğüm değerleri birebir; kesişimlerde aynı düğüm aynı renk)
      kirisEl.forEach(function (e) {
        const p = nd[e.dugumler[0]], q = nd[e.dugumler[1]], L = Math.hypot(q.X - p.X, q.Y - p.Y) || 1;
        const nx = -(q.Y - p.Y) / L * Bs / 2, ny = (q.X - p.X) / L * Bs / 2, mx = (p.X + q.X) / 2, my = (p.Y + q.Y) / 2;
        [[p, p.X, p.Y, mx, my], [q, mx, my, q.X, q.Y]].forEach(function (y) {
          const d = y[0], val = +d[ana], k = [[y[1] + nx, y[2] + ny], [y[3] + nx, y[4] + ny], [y[3] - nx, y[4] - ny], [y[1] - nx, y[2] - ny]];
          s += '<polygon class="bn-isi' + sinif(val) + '" points="' + k.map(function (c) { return pt(X(c[0]), Y(c[1])); }).join(" ") + '" fill="' + isiRengi(u(Math.max(0, val))) + '" data-tdugum="' + d.no + '" data-teleman="' + e.no + '"><title>' + kacis("TK-" + ((e.kaynak && e.kaynak.hat) || "") + " · " + baslik(d)) + "</title></polygon>";
        });
      });
      // kiriş dış çizgisi (B genişlikte şerit)
      kirisEl.forEach(function (e) {
        const p = nd[e.dugumler[0]], q = nd[e.dugumler[1]], L = Math.hypot(q.X - p.X, q.Y - p.Y) || 1, nx = -(q.Y - p.Y) / L * Bs / 2, ny = (q.X - p.X) / L * Bs / 2;
        s += '<path class="bn-isi-serit-kenar" d="M' + pt(X(p.X + nx), Y(p.Y + ny)) + " L" + pt(X(q.X + nx), Y(q.Y + ny)) + " M" + pt(X(p.X - nx), Y(p.Y - ny)) + " L" + pt(X(q.X - nx), Y(q.Y - ny)) + '"/>';
      });
    }
    // akslar ve kolonlar
    const bn = v.bina, akx = (bn.akslar && bn.akslar.x) || [], aky = (bn.akslar && bn.akslar.y) || [];
    akx.forEach(function (ak) { s += '<path class="bn-isi-aks" d="M' + pt(X(+ak.konum), Y(y1) - 6) + " L" + pt(X(+ak.konum), Y(y0) + 6) + '"/>' + metinSvg(X(+ak.konum), pu - 10, ak.ad, "bn-isi-aks-t", "middle"); });
    aky.forEach(function (ak) { s += '<path class="bn-isi-aks" d="M' + pt(X(x0) - 6, Y(+ak.konum)) + " L" + pt(X(x1) + 6, Y(+ak.konum)) + '"/>' + metinSvg(X(x0) - 12, Y(+ak.konum) + 4, ak.ad, "bn-isi-aks-t", "end"); });
    const konum = function (ad, l) { const a2 = l.filter(function (z) { return z.ad === ad; })[0]; return a2 ? +a2.konum : null; };
    (bn.kolonlar || []).filter(function (c) { return c.kat === 1; }).forEach(function (c) {
      const cx = konum(c.aks[0], akx), cy = konum(c.aks[1], aky), ks = kesitOzV(bn, c.kesit);
      if (cx == null || cy == null) return;
      const dx = c.yon === "y" ? ks[1] : ks[0], dy = c.yon === "y" ? ks[0] : ks[1];
      const bx = Math.max(5, dx * sc), by = Math.max(5, dy * sc);
      s += '<rect class="bn-isi-kolon" x="' + r1(X(cx) - bx / 2) + '" y="' + r1(Y(cy) - by / 2) + '" width="' + r1(bx) + '" height="' + r1(by) + '"/>';
    });
    // en büyük değer işareti
    const dm = dg.reduce(function (a, d) { return +d[ana] > +a[ana] ? d : a; }, dg[0]);
    s += '<circle class="bn-isi-maks" cx="' + r1(X(dm.X)) + '" cy="' + r1(Y(dm.Y)) + '" r="5"/>' + metinSvg(X(dm.X) + (X(dm.X) > W * 0.7 ? -8 : 8), Y(dm.Y) - 8, (wk ? "w_maks " + f2(dm.w_mm) + " mm" : "p_maks " + f1(dm.p_kNm2)), "bn-isi-etiket", X(dm.X) > W * 0.7 ? "end" : "start");
    // lejant (renk çubuğu 0 … üst; basınçta q_em çizgisi)
    const lx = pl, lw = Math.min(360, W - pl - pr - 50), ly = pu + Hp + 30, lh = 12;
    let grd = '<linearGradient id="bn-isi-grd" x1="0" x2="1" y1="0" y2="0">';
    for (let i = 0; i <= 12; i++) grd += '<stop offset="' + (i / 12).toFixed(3) + '" stop-color="' + isiRengi(i / 12) + '"/>';
    grd += "</linearGradient>";
    s += '<rect class="bn-isi-lejant" x="' + lx + '" y="' + ly + '" width="' + lw + '" height="' + lh + '" fill="url(#bn-isi-grd)" rx="3"/>';
    [0, 0.5, 1].forEach(function (f) { const d = alt + f * (ust - alt); s += '<path class="bn-isi-tik" d="M' + pt(lx + f * lw, ly + lh) + ' l0,4"/>' + metinSvg(lx + f * lw, ly + lh + 16, wk ? f2(d) : f1(d), "bn-isi-lt", f === 0 ? "start" : f === 1 ? "end" : "middle"); });
    s += metinSvg(lx + lw + 8, ly + lh - 1, wk ? "mm" : "kN/m²", "bn-isi-lt", "start");
    if (!wk && qem != null) {
      if (qem >= alt && qem <= ust) {
        const qx = lx + u(qem) * lw;
        s += '<path class="bn-isi-qem" d="M' + pt(qx, ly - 6) + " L" + pt(qx, ly + lh + 2) + '"/>' + metinSvg(qx, ly - 9, "q_em " + f1(qem), "bn-isi-lt bn-isi-qem-t", qx > lx + lw * 0.8 ? "end" : "middle");
      } else s += metinSvg(lx + lw + 8, ly + lh + 16, "q_em = " + f1(qem) + (qem > ust ? " (ölçeğin üstünde; p_maks / q_em = " + f2(vmax / qem) + ")" : ""), "bn-isi-lt bn-isi-qem-t", "start");
    }
    if (vmin < 0) s += metinSvg(lx, ly - 9, "taralı: " + (wk ? "kalkma (w < 0)" : "çekme (p < 0)"), "bn-isi-lt", "start");
    kap.innerHTML = '<svg class="se-svg bn-isi-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + kacis((wk ? "Oturma" : "Taban basıncı") + " haritası; en büyük " + (wk ? f2(vmax) + " mm" : f1(vmax) + " kN/m²") + ", en küçük " + (wk ? f2(vmin) + " mm" : f1(vmin) + " kN/m²")) + '">' +
      "<defs>" + grd + '<pattern id="bn-isi-desen" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)"><rect width="6" height="6" class="bn-isi-desen-z"/><line x1="0" y1="0" x2="0" y2="6" class="bn-isi-desen-c"/></pattern></defs>' + s + "</svg>";
    const bil = document.getElementById("bn-temel-bilgi");
    if (bil) bil.textContent = (wk ? "Oturma w (mm), " : "Taban basıncı p = k₀·w (kN/m²), ") + temelDurumAdi(t) + ". Hücreye dokun: değer. " +
      (radye ? "Her hücre bir ızgara düğümünün etki alanı." : "Kiriş şeridi B = " + f2(Bs) + " m genişlikte; her düğüm komşu eleman yarılarını boyar.") + (!wk && qem != null ? " Koyu kırmızı kenar: p > q_em." : "");
  }
  // bina kesit kütüphanesinden kolon kesit boyutu (b, h; m) — harita için yaklaşık
  function kesitOzV(bn, ad) {
    const k = (bn.kesitler || {})[ad] || {};
    if (k.tip === "profil") {
      const p = profilBul(k.profil), bp = p ? null : basitProfil(k.profil);
      if (p) return [p.b / 1000, p.h / 1000];
      if (bp) return [+bp.b, +bp.h];
    }
    const b = +k.b || +k.B || 0.4, h = +k.h || +k.H || b;
    return [b, h];
  }
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
    const m = kopya(v.fe_model);
    let parcali = 0;
    if (Array.isArray(m.yayili)) {
      // se.js yalnız q/qz okur: parçalı doğrusal kayıtlar (q1→q2, [x1, x2]) aynı elemanın düzgün yüküne toplamı koruyarak eklenir
      const L = {};
      (m.elemanlar || []).forEach(function (e) {
        const a = (m.dugumler || []).filter(function (d) { return d.no === e.dugumler[0]; })[0], b = (m.dugumler || []).filter(function (d) { return d.no === e.dugumler[1]; })[0];
        if (a && b) L[e.no] = Math.hypot((b.x || 0) - (a.x || 0), (b.y || 0) - (a.y || 0), (b.z || 0) - (a.z || 0)) || 1;
      });
      const top = {};
      m.yayili.forEach(function (y) {
        if (y.q1 != null || y.q2 != null) { parcali++; const q1 = +y.q1 || 0, q2 = +y.q2 || 0, x1 = +y.x1 || 0, x2 = y.x2 != null ? +y.x2 : (L[y.eleman] || 0); top[y.eleman] = (top[y.eleman] || 0) + (q1 + q2) / 2 * (x2 - x1); }
      });
      m.yayili = m.yayili.filter(function (y) { return y.q1 == null && y.q2 == null; });
      Object.keys(top).forEach(function (no) {
        const kayit = m.yayili.filter(function (y) { return String(y.eleman) === String(no); })[0];
        const ek = top[no] / (L[no] || 1);
        if (kayit) kayit.q = (+kayit.q || 0) + ek; else m.yayili.push({ eleman: +no, q: ek });
      });
      m.yayili.forEach(function (y) { if (typeof y.q === "number") y.q = Math.round(y.q * 1e6) / 1e6; });
    }
    try { A.seModelYukle(m); if (parcali) A.toast(parcali + " parçalı yük Sonlu eleman sayfası için toplamı koruyan eşdeğer düzgün yüke çevrildi."); }
    catch (e) { A.toast("Model aktarılamadı: " + (e && e.message ? e.message : e)); }
  }

  // ---------- Olaylar ----------
  // düzenleyicinin içine eklenen modül pencereleri (kaplama, eleman bilgisi, araç kutuları) kendi olaylarını işler: data-sekme vb. çakışmasın
  function disModul(el) { return !!(el && el.closest && el.closest(".bn-kaplama, .bilgi-pencere, .bilgi-menu, .arac-kok")); }
  function olaylariBagla() {
    kok.addEventListener("click", function (e) {
      const t = e.target.closest("button, [data-sankey]");
      if (!t || !kok.contains(t) || disModul(t)) return;
      const ds = t.dataset;
      if (ds.kat != null) { D.kat = +ds.kat; D.zAks = null; D.kirisBas = null; kamera.sifirla(); yenile(); olayYay("gorunum", gorunum()); return; }
      if (t.id === "bn-kat-ekle") {
        // menü sabit konumlu açılır: kaydırmalı kat şeridi (ve tam ekran şeridi) onu kırpmasın
        const m = document.getElementById("bn-kat-menu"), r = t.getBoundingClientRect();
        m.classList.toggle("gizli");
        m.style.top = Math.round(r.bottom + 4) + "px"; m.style.left = Math.round(Math.max(4, Math.min(r.left, window.innerWidth - 200))) + "px";
        return;
      }
      if (ds.katIslem) { document.getElementById("bn-kat-menu").classList.add("gizli"); if (ds.katIslem === "sil") katSil(ustKat()); else katEkle(ds.katIslem === "kopyala"); return; }
      if (ds.gorunum) {
        if (ds.gorunum === "sifirla") { kamera.sifirla(); ref.svg.setAttribute("viewBox", kamera.viewBox()); return; }
        gorunumGit(ds.gorunum); return;
      }
      if (ds.arac) { if (ds.arac === "kutuphane") { D.panelSekme = "kutuphane"; panelAc(); } else aracSec(ds.arac); yenile(); return; }
      if (t.id === "bn-proje-kaydet") { projeKaydet(false); return; }
      if (t.id === "bn-proje-ac") { projeAc(); return; }
      if (ds.cikti) { if (ds.cikti === "rapor") raporAc(); else if (ds.cikti === "tablolar") tablolarAc(); else if (ds.cikti === "isi") isiAc(); else if (ds.cikti === "ifc") ifcAc(); return; }
      if (t.id === "bn-geri") { geriAl(); return; }
      if (t.id === "bn-ileri") { ileriAl(); return; }
      if (t.id === "bn-sihirbaz") { sihirbazAc(); return; }
      if (t.id === "bn-sih-iptal") { ref.sihirbazDlg.close ? ref.sihirbazDlg.close() : ref.sihirbazDlg.removeAttribute("open"); return; }
      if (t.id === "bn-json") { jsonAc(); return; }
      if (t.id === "bn-json-uygula") { jsonUygula(); return; }
      if (t.id === "bn-json-kopyala") { if (navigator.clipboard) navigator.clipboard.writeText(ref.jsonMetin.value).then(function () { A.toast("Kopyalandı."); }, function () { A.toast("Kopyalanamadı."); }); return; }
      if (t.id === "bn-json-indir") { jsonIndir(); return; }
      if (t.id === "bn-json-kapat") { ref.jsonDlg.close ? ref.jsonDlg.close() : ref.jsonDlg.removeAttribute("open"); return; }
      if (t.id === "bn-doldur" || t.id === "bn-kat-kopyala") {
        if (s3Var()) { A.toast("Bu komut aks–kat modeli içindir; genel modelde Hızlı panel ve Doğrusal dizi araçlarını kullanın."); return; }
        if (t.id === "bn-doldur") dosemeleriDoldur(); else katKopyalaAlttan();
        return;
      }
      if (t.id === "bn-firca-kapat") { D.firca = null; yenile(); return; }
      if (t.id === "bn-formul-kapat") { ref.formul.classList.add("gizli"); D.formul = null; return; }
      if (ds.psek) { D.panelSekme = ds.psek; ustCubukCiz(); panelCiz(); return; }
      if (ds.temelTip) { temelTipSec(ds.temelTip); return; }
      if (ds.temelAks) { temelAksSec(ds.temelAks); return; }
      if (ds.temelHarita) { D.temelHarita = ds.temelHarita === "w" ? "w" : "p"; temelHaritaCiz(); return; }
      if (ds.temelSekmeGit) {
        D.sekme = ds.temelSekmeGit;
        if (D.sekme === "diyagram") D.aksFiltre = ds.temelAksFiltre || "";
        sekmeCiz();
        const s0 = document.getElementById("bn-sekme-icerik"); if (s0) s0.scrollIntoView({ block: "start", behavior: azHareket() ? "auto" : "smooth" });
        return;
      }
      if (t.id === "bn-tam") { tamEkranDegistir(); return; }
      if (t.id === "bn-arac-ac") { if (aracYon) aracKatmaniGoster(!!ref.aracKatman.hidden); else { D.aracKapali = !D.aracKapali; yerlesimUygula(); } return; }
      if (t.id === "bn-panel-ac") { D.panelKapali = !D.panelKapali; if (!D.panelKapali) ref.panel.open = true; yerlesimUygula(); return; }
      if (t.id === "bn-sonuc-yer") { sonucYerDegistir(); return; }
      if (t.id === "bn-ayni-tur") { ayniTurdenSec(); return; }
      if (ds.s3Komut) { const M = modul("MatrisArac"); if (M && M.komut(ds.s3Komut)) aracCalistir(ds.s3Komut); return; }
      if (ds.s3UretecSil) {
        const MO = modul("ModelOps");
        if (MO && window.confirm("Üreteç " + ds.s3UretecSil + " ve ürettiği bütün elemanlar silinsin mi?")) {
          try { const r = MO.uretecSil(B, +ds.s3UretecSil); D.secim = []; binaAyarla(r.model, { normalize: false, etiket: "Üreteç " + ds.s3UretecSil + " silindi." + (r.uyarilar.length ? " " + r.uyarilar.join(" ") : "") }); }
          catch (x) { A.toast(x.message); }
        }
        return;
      }
      if (t.id === "bn-secim-sil") { secimiSil(); return; }
      if (t.id === "bn-yuk-yolu") { if (D.secim.length) { D.akisHedef = D.secim[0]; D.sekme = "akis"; sonucuCiz(); sahneCiz(); ref.sahneKutu.scrollIntoView({ block: "nearest" }); } return; }
      if (ds.aksEkle) { aksEkle(ds.aksEkle); return; }
      if (ds.aksSil) { const p = ds.aksSil.split(":"); aksSil(p[0], +p[1]); return; }
      if (ds.katSil) { katSil(+ds.katSil); return; }
      if (ds.firca) { D.firca = D.firca === ds.firca ? null : ds.firca; aracSec("sec"); yenile(); return; }
      if (ds.kesitSil) { kesitSil(ds.kesitSil); return; }
      if (t.id === "bn-yk-ekle") { yeniKesitEkle(); return; }
      if (t.id === "bn-coz") { coz(); return; }
      if (ds.hatSekme && !t.disabled && SON) { D.sekme = ds.hatSekme; sekmeCiz(); ref.sonuc.scrollIntoView({ block: "start", behavior: azHareket() ? "auto" : "smooth" }); return; }
      if (ds.adim != null && !t.disabled) { adimaGit(+ds.adim); return; }
      if (ds.sekme) { D.sekme = ds.sekme; sekmeCiz(); return; }
      if (ds.akisDurum) { D.akisDurum = ds.akisDurum; sekmeCiz(); return; }
      if (t.id === "bn-oynat") { oynatToggle(); return; }
      if (ds.sankey != null) { D.sankeySecim = D.sankeySecim === ds.sankey ? null : ds.sankey; sankeyCiz(); return; }
      if (ds.dgm) { D.diyagram = ds.dgm; diyagramiCiz(); return; }
      if (ds.depYon) { D.depremYon = ds.depYon === "y" ? "y" : "x"; sekmeCiz(); return; }
      if (t.id === "bn-se-ac") { seAc(); return; }
      if (t.id === "bn-tasarim-hesap") { ayrintiliHesap(); return; }
      if (ds.dcSec) { const q = ds.dcSec.split(":"); tasarimSec(q[0], +q[1], true); return; }
      if (t.id === "bn-tasarim-kapat") { D.tasarimSecim = null; D.secim = []; yenile(); tasarimAyrintiCiz(); document.querySelectorAll("#bn-sekme-icerik tr.bn-dc-satir.aktif").forEach(function (r) { r.classList.remove("aktif"); r.setAttribute("aria-selected", "false"); }); return; }
      if (ds.nmEksen) { D.nmEksen = ds.nmEksen; nmCiz(); return; }
    });
    // tasarım tablosu: satıra dokun / Enter → eleman seçimi
    kok.addEventListener("click", function (e) {
      const r = e.target.closest ? e.target.closest("tr.bn-dc-satir") : null;
      if (r && kok.contains(r)) tasarimSec(r.dataset.dcTur, +r.dataset.dcNo, true);
    });
    kok.addEventListener("keydown", function (e) {
      const r = e.target.closest("tr.bn-dc-satir");
      if (r && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); tasarimSec(r.dataset.dcTur, +r.dataset.dcNo, true); return; }
      const t = e.target.closest("[data-sankey]");
      if (t && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); D.sankeySecim = D.sankeySecim === t.dataset.sankey ? null : t.dataset.sankey; sankeyCiz(); }
    });
    kok.addEventListener("change", function (e) {
      const el = e.target, ds = el.dataset;
      if (disModul(el)) return;
      if (el.id === "bn-sablon") { if (el.value) sablonYukle(el.value); return; }
      if (el.id === "bn-duzlem") { duzlemSec(ds.duzlemTur, el.value); return; }
      if (el.id === "bn-tum-katlar") { D.tumKatlar = el.checked; return; }
      if (ds.oz) { ozellikDegistir(ds.oz, el.value); return; }
      if (ds.oz3) { s3OzellikDegistir(ds.oz3, el); return; }
      if (ds.bina) { B[ds.bina] = el.value; degisti(); return; }
      if (ds.yd) { yukDurumuDegistir(ds.yd, ds.ydAlan, el); return; }
      if (ds.dep) { depremDegistir(ds.dep, el.value, el); return; }
      if (ds.analiz) { B.analiz[ds.analiz] = !!el.checked; degisti(); spektrumOnizle(); return; }
      if (ds.analizSec) { B.analiz[ds.analizSec] = el.value; degisti(); return; }
      if (ds.temel) { B.temeller[ds.temel] = el.value; degisti(); return; }
      if (ds.temelA) { temelAlanDegistir(ds.temelA, el); return; }
      if (ds.temelKiris) { const r = B.temeller.radye; if (r) { if (el.checked) r.kiris = Object.assign({}, TEMEL_VARS.kiris, D.sonRadyeKiris || {}); else { D.sonRadyeKiris = r.kiris; r.kiris = null; } degisti(); } return; }
      if (ds.temelV) { const n = sayiOku(el.value); if (n != null && n > 0) { B.temeller.varsayilan[ds.temelV] = n; degisti(); } return; }
      if (ds.zemin) { const n = sayiOku(el.value); if (n != null && n > 0) { B.temeller.zemin[ds.zemin] = n; degisti(); } return; }
      if (ds.aks) { aksDegistir(ds.aks, +ds.i, ds.a, el.value); return; }
      if (ds.katI != null) { katDegistir(+ds.katI, ds.a, el.value); return; }
      if (el.id === "bn-yk-tip") { document.getElementById("bn-yk-dik").style.display = el.value === "profil" ? "none" : ""; document.getElementById("bn-yk-prof").style.display = el.value === "profil" ? "" : "none"; return; }
      if (el.id === "bn-dep-ok") { D.depremOk = el.checked; sahneCiz(); return; }
      if (el.id === "bn-dc-gorunum") { D.dcGorunum = el.checked; sahneCiz(); return; }
      if (el.id === "bn-dc-filtre") { D.tasarimFiltre = el.value; sekmeCiz(); return; }
      if (el.id === "bn-def-durum" || el.id === "bn-tablo-durum" || el.id === "bn-dgm-durum") {
        // yanıtta olmayan kombinasyon / ince durum motordan tembel alınır (önbellek: veri.sonuclar / veri.durumlar); çizim işlevleri bekler
        const id = el.id, ad = el.value;
        if (id === "bn-dgm-durum") D.diyagramDurum = ad; else D.deformeDurum = ad;
        if (id === "bn-def-durum") deformeyiCiz(); else if (id === "bn-dgm-durum") diyagramiCiz(); else sekmeCiz();
        if (id !== "bn-tablo-durum") sahneCiz();
        return;
      }
      if (el.id === "bn-aks-filtre") { D.aksFiltre = el.value; diyagramiCiz(); return; }
      if (el.name === "sistem" && el.form === ref.sihirbazForm) { ref.sihirbazForm.querySelector(".bn-sih-dik").style.display = el.value === "celik" ? "none" : ""; ref.sihirbazForm.querySelector(".bn-sih-prof").style.display = el.value === "celik" ? "" : "none"; }
    });
    kok.addEventListener("input", function (e) {
      const el = e.target;
      if (disModul(el)) return;
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
    // temel haritasında hücreye dokun → değer
    kok.addEventListener("click", function (e) {
      const c = e.target.closest ? e.target.closest("[data-tdugum]") : null;
      if (!c || !kok.contains(c) || !V() || !V().temel) return;
      const d = (V().temel.dugumler || []).filter(function (x) { return x.no === +c.dataset.tdugum; })[0], bil = document.getElementById("bn-temel-bilgi");
      document.querySelectorAll("#bn-temel-harita .bn-isi-secili").forEach(function (x) { x.classList.remove("bn-isi-secili"); });
      c.classList.add("bn-isi-secili");
      if (d && bil) bil.textContent = "Düğüm " + d.no + " (X " + f2(d.X) + ", Y " + f2(d.Y) + " m): p = " + f1(d.p_kNm2) + " kN/m², oturma = " + f2(d.w_mm) + " mm" + (d.p_kNm2 < 0 ? " — çekme (ayrılma)" : "");
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
      if (document.querySelector("dialog[open]") || KAPLAMA.el) return;
      if (e.defaultPrevented) return;
      const k = e.key;
      // etkin kip (ölçüm; bina_cizim.js araçları) Esc / Enter / Geri tuşlarını önce alır
      const kip = aktifKip();
      if (kip && kip.tus && !(e.ctrlKey || e.metaKey || e.altKey)) { let al = false; try { al = !!kip.tus(e); } catch (x) { al = false; } if (al) { e.preventDefault(); return; } }
      if (k === "?" && !(e.ctrlKey || e.metaKey || e.altKey)) { e.preventDefault(); kisayolPenceresi(); return; }
      // Kısayollar tek kaynak: araç kutuları kuruluysa (MatrisArac) komut kısayollarını o işler (S, K, R, D, W, Del, F, Shift+F, 1–4, U, Ctrl+Z/Y/C/V, Ctrl+Enter);
      // burada yalnız kataloğun karşılamadıkları kalır (Ctrl+Shift+Z yinele, Backspace = Sil, Esc). Modül yoksa eski kısayollar.
      if (aracYon) {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (k === "z" || k === "Z")) { e.preventDefault(); ileriAl(); return; }
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        if (k === "Backspace") { if (D.secim.length) { e.preventDefault(); secimiSil(); } else { aracSec("sil"); yenile(); } return; }
      } else {
        if ((e.ctrlKey || e.metaKey) && (k === "z" || k === "Z")) { e.preventDefault(); if (e.shiftKey) ileriAl(); else geriAl(); return; }
        if ((e.ctrlKey || e.metaKey) && (k === "y" || k === "Y")) { e.preventDefault(); ileriAl(); return; }
        if ((e.ctrlKey || e.metaKey) && k === "Enter") { e.preventDefault(); coz(); return; }
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        const kisayol = { s: "sec", k: "kolon", r: "kiris", d: "doseme", w: "duvar" };
        const kl = k.toLowerCase();
        if (kisayol[kl]) { aracSec(kisayol[kl]); yenile(); return; }
        if (k === "Delete" || k === "Backspace") { if (D.secim.length) { e.preventDefault(); secimiSil(); } else { aracSec("sil"); yenile(); } return; }
        if (kl === "f") { e.preventDefault(); tamEkranDegistir(); return; }
      }
      if (k === "Escape") {
        if (D.tamEkran && !D.kirisBas && !D.secim.length && !D.firca && (!aktifKip() || D.arac === "sec")) { tamEkranKapat(); return; }
        if (aktifKip() && !D.kirisBas && !D.secim.length && !D.firca) { aracSec("sec"); yenile(); return; }     // kipten çık
        D.kirisBas = null; D.secim = []; D.firca = null; yenile();
      }
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
  function yukDurumuDegistir(durum, alan, el) {
    const yd = B.yuk_durumlari[durum];
    if (!yd) return;
    if (alan === "acik") { yd.acik = !!el.checked; if (durum === "G") yd.acik = true; }
    else if (alan === "bolge") yd.bolge = Math.min(9, Math.max(1, parseInt(el.value, 10) || 1));
    else { const n = sayiOku(el.value); if (n == null || n < 0) { A.toast("Sayı girin."); panelCiz(); return; } yd[alan] = n; }
    degisti();
  }
  function depremDegistir(alan, deger, el) {
    const dp = B.deprem;
    if (alan === "tasiyici") { const t = tasiyiciBul(deger); dp.tasiyici = deger; if (t) { dp.R = t.R; dp.D = t.D; } }
    else if (alan === "BKS") { dp.BKS = TBDY.I[+deger] ? +deger : 3; dp.I = TBDY.I[dp.BKS]; }
    else if (alan === "zemin_sinifi" || alan === "periyot" || alan === "diyafram" || alan === "dolgu" || alan === "DD") dp[alan] = deger;
    else {
      const n = sayiOku(deger);
      if (n == null || n < 0) { A.toast("Sayı girin (ondalık için virgül ya da nokta)."); panelCiz(); return; }
      if (alan === "dismerkezlik" && n > 0.3) { A.toast("Dışmerkezlik kat boyutunun oranıdır (TBDY: 0,05)."); panelCiz(); return; }
      dp[alan] = n;
    }
    void el;
    degisti();
    spektrumOnizle();
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
    const M = window.MatrisAks;
    if (M && s3Var()) {      // genel model: aksa bağlı çubuk/panel/düğümler de (MatrisAks.aksSil "elemanlarla")
      let r;
      try { r = M.aksSil(B, { yon: e, ad: a.ad }); } catch (x) { A.toast(x.message); return; }
      if (r.onayGerekli) {
        if (!window.confirm("Aks " + a.ad + "'ya bağlı " + r.bagli.ozet + " var; elemanlarla birlikte silinsin mi?")) return;
        try { r = M.aksSil(B, { yon: e, ad: a.ad, secenek: "elemanlarla" }); } catch (x) { A.toast(x.message); return; }
      }
      if (r.silindi === false) { if (r.uyarilar && r.uyarilar.length) A.toast(r.uyarilar.join(" ")); return; }
      // çizim aracındaki “Aks sil” ile aynı kapı (MatrisBinaCizim.aksSilEngelleri): motorun her zaman reddettiği yeni bozukluk kalırsa silinmez
      const BC = window.MatrisBinaCizim, engelFn = BC && (BC.aksSilEngelleri || (BC.SAF && BC.SAF.aksSilEngelleri));
      const engel = engelFn ? engelFn(B, r.model) : [];
      if (engel.length) {
        A.toast("Aks " + a.ad + " silinmedi (motor bu modeli çözmez): " + engel.slice(0, 3).map(function (u) { return u.mesaj; }).join(" ") +
          (engel.length > 3 ? " … (+" + (engel.length - 3) + ")" : "") + " — elemanları önce düzenleyin ya da çizimdeki “Aks sil” aracının “en yakın aksa taşı” seçeneğini kullanın.");
        return;
      }
      binaAyarla(r.model, { etiket: "Aks " + a.ad + " silindi" + (r.uyarilar && r.uyarilar.length ? ": " + r.uyarilar.join(" ") : ".") });
      return;
    }
    const bagli =B.kolonlar.filter(function (c) { return c.aks[e === "x" ? 0 : 1] === a.ad; }).length + B.kirisler.filter(function (k) { return k.bas[e === "x" ? 0 : 1] === a.ad || k.son[e === "x" ? 0 : 1] === a.ad; }).length;
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
      const M = window.MatrisAks;
      if (M && M.aksYenidenAdlandir) {      // bütün başvurular (aks–kat elemanları, çubuk/panel REF'leri, temeller, yükler)
        try { binaAyarla(M.aksYenidenAdlandir(B, { yon: e, eski: a.ad, yeni: yeni }).model, { normalize: false }); } catch (x) { A.toast(x.message); panelCiz(); }
        return;
      }
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
    else { const n = sayiOku(deger); if (n == null || (i > 0 && n <= B.katlar[i - 1].kot) || (i < B.katlar.length - 1 && n >= B.katlar[i + 1].kot)) { A.toast("Kot komşu katların arasında olmalı."); panelCiz(); return; } k.kot = n; zKatKot(k.no, n); }
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
    sablonYukle(m[1], { adres: true });
  }

  // =====================================================================================================================
  // ---------- Kablolama (Dilim 4f, 1. aşama): iç API (window.MatrisBina), araç kutuları, ölçüm, sağ tık, çıktılar, masaüstü ----------
  // Modüller isteğe bağlıdır (her biri yoksa ilgili özellik sessizce kapanır): MatrisArac (arac_kutusu.js), MatrisBilgi (eleman_bilgi.js),
  // MatrisOlcum (olcum.js), MatrisTablo (tablo_editoru.js), MatrisIsi (isi_haritasi.js), MatrisIFC (ifc_disari.js), MatrisDosya (masaustu_kopru.js).
  // =====================================================================================================================
  function modul(ad) { return window[ad] || null; }
  const SVG_NS = "http://www.w3.org/2000/svg";

  // ---- olaylar (bina_cizim.js ve modüller dinler): "model", "cozum", "secim", "gorunum", "kip", "ciz", "hazir"
  const DINLEYICI = {};
  function olayYay(ad, veri) { (DINLEYICI[ad] || []).slice().forEach(function (f) { try { f(veri); } catch (e) { setTimeout(function () { throw e; }, 0); } }); }
  function dinle(ad, f) {
    (DINLEYICI[ad] = DINLEYICI[ad] || []).push(f);
    return function () { DINLEYICI[ad] = (DINLEYICI[ad] || []).filter(function (g) { return g !== f; }); };
  }
  let sonSecimAnahtar = "[]";
  function secimDegistiMi() {
    const a = JSON.stringify(D.secim);
    if (a !== sonSecimAnahtar) { sonSecimAnahtar = a; olayYay("secim", secim()); }
  }

  // ---- tek geri al yığını: dışarıdan gelen bütün model değişiklikleri (tablo editörü, bina_cizim.js işlemleri, proje açma) buradan geçer
  // sec: {geriAl (true: önceki hâl geri al yığınına), etiket (bildirim), normalize (true: binaYukle denetimi), secim ([{tur,no}]), sessiz}
  function binaAyarla(yeni, sec) {
    sec = sec || {};
    if (!yeni || typeof yeni !== "object") throw new Error("binaAyarla: bina bir JSON nesnesi olmalı.");
    if (!ref.svg) throw new Error("Bina sayfası henüz başlamadı (MatrisBina.hazir() / \"matris-bina-hazir\" olayını bekleyin).");
    const b = sec.normalize === false ? kopya(yeni) : binaYukle(yeni);    // hatalıysa fırlatır; model değişmez
    const onceki = B ? anlikGoruntu() : "";
    B = b;
    const simdi = anlikGoruntu();
    if (simdi === onceki) { if (sec.secim) D.secim = sec.secim.slice(); yenile(); return false; }
    if (sec.geriAl !== false && (sonAnlik || onceki)) {
      gecmis.geri.push(sonAnlik || onceki);
      if (gecmis.geri.length > GECMIS_EN_FAZLA) gecmis.geri.shift();
      gecmis.ileri = [];
    }
    sonAnlik = simdi;
    D.secim = sec.secim ? sec.secim.slice() : D.secim.filter(function (s) { return ["kolon", "kiris", "doseme", "cubuk", "panel", "dugum", "mesnet"].indexOf(s.tur) < 0 || nesneBul(s.tur, s.no); });
    D.kirisBas = null;
    D.kat = Math.min(Math.max(0, D.kat), ustKat());
    if (SON) sonEski = true;
    taslakKaydet();
    modelDegisti(sec.etiket || "");
    yenile();
    if (sec.etiket && !sec.sessiz) A.toast(sec.etiket);
    return true;
  }
  // her model değişikliğinden sonra (degisti, geri/ileri, binaAyarla, binayiAyarla): masaüstü kirli bayrağı ve dinleyiciler
  function modelDegisti(etiket) {
    const F = modul("MatrisDosya");
    if (F) { try { F.degisti(true); } catch (e) { /* masaüstü köprüsü yoksa */ } }
    geoOnbellek.anahtar = null;
    olayYay("model", { etiket: etiket || "" });
    if (KAPLAMA.tur === "tablolar") tablolarTazeleGecikmeli();
  }
  function cozumKimligi() { return SON && !sonEski && SON.veri ? SON.veri.cozum_kimligi || null : null; }
  function veriGuncel() { return SON && !sonEski ? SON.veri : null; }
  function secim() { return D.secim.map(function (s) { return { tur: s.tur, no: s.no }; }); }
  function seciliAyarla(liste) {
    D.secim = (Array.isArray(liste) ? liste : liste ? [liste] : []).filter(function (s) { return s && s.tur && s.no != null; }).map(function (s) { return { tur: String(s.tur), no: s.no }; });
    D.kirisBas = null;
    if (B && ref.svg) yenile();
    return secim();
  }
  // Çözüm hazır mı? Değilse çöz (rapor, ısı haritası). Promise<bool>
  function cozumHazir() {
    if (SON && !sonEski) return Promise.resolve(true);
    // çözüm sürerken model değiştiyse (sonuç eski kaldı) bir kez daha çöz
    return coz().then(function (ok) { return ok || !(SON && sonEski) ? ok : coz(); });
  }

  // ---- görünüm (kamera + kat + süzgeçler). Aks görünümü MatrisAks biçiminde: {tur: "plan", z} | {tur: "cephe", x|y} | {tur: "3b"}
  function zAksiAdi(kat) {
    const M = modul("MatrisAks");
    if (M && M.katZAksi) { try { const z = M.katZAksi(B, kat); if (z && z.ad != null) return z.ad; } catch (e) { /* yoksay */ } }
    return katAd(kat);
  }
  function duzlemZ() { return D.zAks != null && zAksBul(D.zAks) ? String(D.zAks) : zAksiAdi(D.kat); }
  function aksGorunumu() {
    const g = kamera ? kamera.gorunum : "3b";
    if (g === "plan") return { tur: "plan", z: duzlemZ() };
    if (g === "on") return { tur: "cephe", y: cepheAks("y") };
    if (g === "yan") return { tur: "cephe", x: cepheAks("x") };
    return { tur: "3b", z: duzlemZ() };
  }
  function cepheAks(e) {
    const l = B.akslar[e] || [];
    return D.cephe[e] && l.some(function (a) { return a.ad === D.cephe[e]; }) ? D.cephe[e] : (l[0] || {}).ad || null;
  }
  // plan düzlemi etkin katın Z aksı mı (aks–kat araçları yalnız orada)
  function duzlemKatMi() {
    if (D.zAks == null) return true;
    const z = zAksBul(D.zAks);
    return !z || (z.kat != null && +z.kat === D.kat);
  }
  // aks–kat çizim kipi: aks–kat modeli (surum 3 içeriği yok) ve etkin kat düzlemi → kolon/kiriş/döşeme aks–kat elemanı olarak eklenir
  function aksKatModu() { return !!B && !s3Var() && !(+B.surum >= 3) && D.kat >= 1 && duzlemKatMi(); }
  // düzlem değiştir: plan/3B'de Z aksı, cephede X ya da Y aksı (PgUp / PgDn; kat dışı Z aksları — saçak, mahya — dahil)
  function duzlemSec(tur, ad) {
    if (tur === "z") {
      const z = zAksBul(ad);
      if (!z) return;
      D.zAks = String(z.ad);
      if (z.kat != null && B.katlar.some(function (k) { return k.no === +z.kat; })) { D.kat = +z.kat; D.zAks = null; }
    } else if (tur === "x" || tur === "y") D.cephe[tur] = String(ad);
    D.kirisBas = null;
    yenile(); olayYay("gorunum", gorunum());
  }
  function duzlemGec(adim) {
    const M = window.MatrisAks, g = aksGorunumu();
    if (!M || !M.gorunumKomsu) { katGec(adim); return; }
    let n;
    try { n = M.gorunumKomsu(B, g, adim); } catch (e) { katGec(adim); return; }
    if (g.tur === "cephe") { const e = g.x != null ? "x" : "y"; if (n[e] !== g[e]) duzlemSec(e, n[e]); }
    else if (n.z !== g.z) duzlemSec("z", n.z);
  }
  function duzlemKomsuVar(adim) {
    const M = window.MatrisAks, g = aksGorunumu();
    if (!M || !M.gorunumKomsu) return adim > 0 ? D.kat < ustKat() : D.kat > 0;
    try { const n = M.gorunumKomsu(B, g, adim); return g.tur === "cephe" ? n[g.x != null ? "x" : "y"] !== g[g.x != null ? "x" : "y"] : n.z !== g.z; } catch (e) { return false; }
  }
  function gorunum() {
    return { tur: kamera ? kamera.gorunum : "3b", kat: D.kat, zAks: D.zAks, tumKatlar: D.tumKatlar, aks: B ? aksGorunumu() : null, cephe: Object.assign({}, D.cephe),
      bakis: kamera ? { fi: kamera.bakis.fi, psi: kamera.bakis.psi } : null, gizli: Object.keys(D.gizli), yalit: D.yalit ? Object.keys(D.yalit) : null,
      katSuzgec: D.katSuzgec ? D.katSuzgec.slice() : null, telKafes: D.telKafes, etiketler: D.etiketler, izgara: D.izgara };
  }
  function gorunumGit(ad) {
    if (!kamera || !C.GORUNUMLER[ad]) return;
    kamera.git(ad, function (k, bitti) {
      D.hafif = !bitti; sahneYenile();
      if (bitti) { gorunumDugmeleri(); if (D.sekme === "deforme") deformeyiCiz(); if (D.sekme === "diyagram") diyagramiCiz(); olayYay("gorunum", gorunum()); aracYenile(); }
    });
    gorunumDugmeleri();
    aracYenile();
  }
  // g: "3b" | "plan" | "on" | "yan" | {tur: "3b"|"plan"|"on"|"yan"|"cephe", kat?, z?, x?, y?, gizli?, yalit?, katSuzgec?, telKafes?, etiketler?, izgara?, bakis?}
  function gorunumAyarla(g) {
    if (!B) return null;
    if (typeof g === "string") g = { tur: g };
    g = g || {};
    if (g.kat != null && B.katlar.some(function (k) { return k.no === +g.kat; })) { D.kat = +g.kat; D.zAks = null; }
    if (g.cephe && typeof g.cephe === "object") { if (g.cephe.x != null) D.cephe.x = String(g.cephe.x); if (g.cephe.y != null) D.cephe.y = String(g.cephe.y); }
    const zIstek = g.z != null ? g.z : (g.aks && g.aks.z != null ? g.aks.z : null);
    if (zIstek != null) {
      const M = modul("MatrisAks");
      let kat = null;
      if (M && M.zAksiKati) { try { kat = M.zAksiKati(B, zIstek); } catch (e) { kat = null; } }
      if (kat == null && !zAksBul(zIstek)) { const k = B.katlar.filter(function (x) { return x.ad === String(zIstek) || String(x.kot) === String(zIstek); })[0]; kat = k ? k.no : null; }
      if (kat != null && B.katlar.some(function (k) { return k.no === +kat; })) { D.kat = +kat; D.zAks = null; }
      else if (zAksBul(zIstek)) D.zAks = String(zAksBul(zIstek).ad);
    }
    if (g.x != null) D.cephe.x = String(g.x);
    if (g.y != null) D.cephe.y = String(g.y);
    if (g.gizli) { D.gizli = {}; g.gizli.forEach(function (a) { D.gizli[a] = true; }); }
    if (g.yalit !== undefined) { D.yalit = null; if (g.yalit) { D.yalit = {}; g.yalit.forEach(function (a) { D.yalit[a] = true; }); } }
    if (g.katSuzgec !== undefined) D.katSuzgec = Array.isArray(g.katSuzgec) && g.katSuzgec.length ? g.katSuzgec.map(Number) : null;
    ["telKafes", "etiketler", "izgara"].forEach(function (a) { if (g[a] != null) D[a] = !!g[a]; });
    let tur = g.tur === "cephe" ? (g.x != null ? "yan" : "on") : g.tur;
    if (tur === "serbest" && g.bakis && kamera) { kamera.bakis.fi = +g.bakis.fi || 0; kamera.bakis.psi = +g.bakis.psi || 0; kamera.gorunum = "serbest"; tur = null; }
    yenile();
    if (tur && C.GORUNUMLER[tur]) gorunumGit(tur);
    else olayYay("gorunum", gorunum());
    return gorunum();
  }
  function sigdir() { if (!kamera) return; kamera.sifirla(); ref.svg.setAttribute("viewBox", kamera.viewBox()); sahneYenile(); }

  // ---- görünüm süzgeçleri: gizle / yalıt / kat süzgeci (sahneCiz `gorunurMu` ile uygular)
  function nesneAnahtar(tur, no) { return (tur === "duvar" ? "kiris" : tur) + ":" + no; }
  function gorunurMu(tur, no, kat) {
    const a = nesneAnahtar(tur, no);
    if (D.yalit && !D.yalit[a]) return false;
    if (D.gizli[a]) return false;
    if (D.katSuzgec && kat != null && D.katSuzgec.indexOf(kat) < 0) return false;
    return true;
  }
  function suzgecVar() { return !!(D.yalit || Object.keys(D.gizli).length || D.katSuzgec); }
  function gizle(liste) { (liste || D.secim).forEach(function (s) { D.gizli[nesneAnahtar(s.tur, s.no)] = true; }); D.secim = []; yenile(); olayYay("gorunum", gorunum()); }
  function yalit(liste) {
    const l = liste || D.secim;
    if (!l.length) { A.toast("Yalıtmak için önce eleman seçin."); return; }
    D.yalit = {}; l.forEach(function (s) { D.yalit[nesneAnahtar(s.tur, s.no)] = true; });
    yenile(); olayYay("gorunum", gorunum());
    A.toast(l.length + " eleman yalıtıldı; “Hepsini göster” ile geri gelir.");
  }
  function hepsiniGoster() { D.gizli = {}; D.yalit = null; D.katSuzgec = null; yenile(); olayYay("gorunum", gorunum()); }
  function katSuzgeciAc() {
    const katlar = B.katlar.filter(function (k) { return k.no >= 1; });
    const k = kaplamaAc("suzgec", "Kat süzgeci", { kucuk: true });
    k.govde.innerHTML = '<p class="not">Yalnız işaretli katların elemanları çizilir (temeller her zaman görünür).</p><div class="bn-suzgec-liste">' + katlar.map(function (x) {
      return '<label class="bn-onay"><input type="checkbox" value="' + x.no + '"' + (!D.katSuzgec || D.katSuzgec.indexOf(x.no) >= 0 ? " checked" : "") + "> " + kacis(x.ad) + " (+" + f2(+x.kot) + " m)</label>";
    }).join("") + '</div><div class="dugmeler"><button type="button" class="dugme ana" data-suzgec="uygula">Uygula</button><button type="button" class="dugme" data-suzgec="hepsi">Hepsi</button><button type="button" class="dugme" data-suzgec="etkin">Yalnız etkin kat</button></div>';
    k.govde.addEventListener("click", function (e) {
      const t = e.target.closest("[data-suzgec]");
      if (!t) return;
      const kutular = Array.from(k.govde.querySelectorAll("input[type=checkbox]"));
      if (t.dataset.suzgec === "hepsi") kutular.forEach(function (c) { c.checked = true; });
      else if (t.dataset.suzgec === "etkin") kutular.forEach(function (c) { c.checked = +c.value === D.kat; });
      else {
        const l = kutular.filter(function (c) { return c.checked; }).map(function (c) { return +c.value; });
        D.katSuzgec = l.length && l.length < katlar.length ? l : null;
        kaplamaKapat(); yenile(); olayYay("gorunum", gorunum());
      }
    });
  }

  // ---- kip (etkin araç) kaydı: D.arac bir kipse sahne dokunuşları ona gider. bina_cizim.js çizim/aks araçları da buradan bağlanır.
  // k = {basla?(), bitir?(), dokun?(p, e, hedef), hareket?(p, e), surukleBasla?(p, e) → bool, surukle?(p, e), surukleBitir?(p, e), tus?(e) → bool, ipucu?: metin | fn}
  const KIPLER = {};
  function kipKaydet(id, k) { KIPLER[id] = k || {}; return function () { if (KIPLER[id] === k) delete KIPLER[id]; }; }
  // kip.eskiMi() true dönerse (ör. aks–kat modelinde kat düzleminde Kolon/Kiriş/Döşeme) sahnenin yerleşik aks–kat aracı çalışır
  function aktifKip() {
    const k = KIPLER[D.arac];
    if (!k) return null;
    if (k.eskiMi) { try { if (k.eskiMi()) return null; } catch (e) { /* yoksay */ } }
    return k;
  }
  function aracSec(id) {
    if (D.arac === id) return;
    const onceki = KIPLER[D.arac];
    if (onceki && onceki.bitir) { try { onceki.bitir(); } catch (e) { /* yoksay */ } }
    D.arac = id; D.kirisBas = null;
    const k = KIPLER[id];
    if (k && k.basla) { try { k.basla(); } catch (e) { /* yoksay */ } }
    olayYay("kip", id);
  }
  function kipIpucu() {
    const k = aktifKip();
    if (!k || !k.ipucu) return null;
    try { return typeof k.ipucu === "function" ? k.ipucu() : String(k.ipucu); } catch (e) { return null; }
  }
  function ipucuYaz() {
    const s = ref.sahneUst && ref.sahneUst.querySelector(".bn-ipucu");
    const m = kipIpucu();
    if (s && m != null) s.textContent = m;
  }

  // ---- sahne katmanları: her sahneCiz'den sonra (ölçüm; bina_cizim.js: aks balonları, yakalama işaretleri, önizleme)
  // ciz(baglam) → SVG metni; baglam = {P(X, Y, Z) → [x, y], P3([X, Y, Z]), T, bakis, s (1 ekran px = s viewBox birimi), W, H, gorunum, kat, bina}
  const KATMANLAR = [];
  let SAHNE_BAGLAM = null;
  function katmanKaydet(ad, ciz, sec) {
    const i = KATMANLAR.findIndex(function (k) { return k.ad === ad; });
    const k = Object.assign({ ad: ad, ciz: ciz, sira: 0, el: null }, sec || {});
    if (i >= 0) KATMANLAR.splice(i, 1, k); else KATMANLAR.push(k);
    KATMANLAR.sort(function (a, b) { return a.sira - b.sira; });
    if (B && ref.svg) sahneYenile();
    return function () { const j = KATMANLAR.indexOf(k); if (j >= 0) KATMANLAR.splice(j, 1); if (k.el) k.el.remove(); };
  }
  function katmanlariCiz() {
    if (!ref.svg || !SAHNE_BAGLAM) return;
    KATMANLAR.forEach(function (k) {
      const g = document.createElementNS(SVG_NS, "g");
      g.setAttribute("class", "bn-katman bn-katman-" + k.ad);
      g.setAttribute("data-katman", k.ad);
      try { g.innerHTML = k.ciz(SAHNE_BAGLAM) || ""; } catch (e) { g.innerHTML = ""; }
      // sira < 0: elemanların altında (aks ızgarası); değilse üstte (ölçü, yakalama, önizleme)
      const defs = k.sira < 0 ? ref.svg.querySelector("defs") : null;
      if (defs) ref.svg.insertBefore(g, defs.nextSibling); else ref.svg.appendChild(g);
      k.el = g;
      if (k.bagla) { try { k.bagla(g); } catch (e) { /* yoksay */ } }
    });
  }
  function katmanTazele(ad) {
    const k = KATMANLAR.filter(function (x) { return x.ad === ad; })[0];
    if (!k || !k.el || !k.el.isConnected || !SAHNE_BAGLAM) { sahneYenile(); return; }
    try { k.el.innerHTML = k.ciz(SAHNE_BAGLAM) || ""; } catch (e) { k.el.innerHTML = ""; }
  }
  function izdusum() { return SAHNE_BAGLAM; }
  function pxOlcek() { return (kamera && ref.svg && kamera.pxOlcek(ref.svg)) || 1; }
  // istemci noktası → viewBox; sahnedeki hedef (bina elemanı) → {tur, no} | null
  function hedefBul(olay) {
    if (!olay || !ref.svg) return null;
    const el = olay.target && olay.target.closest ? olay.target.closest("[data-tur][data-no]") : null;
    if (el && ref.svg.contains(el)) {
      const tur = el.getAttribute("data-tur") === "duvar" ? "kiris" : el.getAttribute("data-tur"), no = +el.getAttribute("data-no");
      if (["kolon", "kiris", "doseme", "temel", "cubuk", "panel", "dugum", "mesnet"].indexOf(tur) >= 0 && isFinite(no)) return { tur: tur, no: no };
      // yayılı temel: mütemadi temel kirişi, radye plağı, kirişli radyenin aks kirişi
      const alt = { "temel-kirisi": "surekli", radye: "radye", "radye-kirisi": "radye-kirisi" }[tur];
      if (alt && isFinite(no)) {
        const h = { tur: "temel", alt: alt, no: no };
        if (el.getAttribute("data-aks") != null) h.aks = el.getAttribute("data-aks");
        if (el.getAttribute("data-yon")) h.yon = el.getAttribute("data-yon");
        return h;
      }
    }
    if (olay.clientX == null || !kamera) return null;
    const p = kamera.svgNokta(ref.svg, olay.clientX, olay.clientY), h = C.vurus(hedefler, p[0], p[1]);
    if (!h) return null;
    if (h.kind === "nesne") return { tur: h.nesne, no: h.no };
    if (h.kind === "temel" && h.no != null) { const t = { tur: "temel", no: h.no }; ["alt", "aks", "yon"].forEach(function (a) { if (h[a] != null) t[a] = h[a]; }); return t; }
    if (h.kind === "kesisim") {
      const c = kolonBul(h.aks, D.kat);
      if (c) return { tur: "kolon", no: c.no };
      const ix = B.akslar.x.findIndex(function (a) { return a.ad === h.aks[0]; }), iy = B.akslar.y.findIndex(function (a) { return a.ad === h.aks[1]; });
      const no = 1000 * D.kat + 20 * ix + iy + 1, geo = olcumGeo(), v = veriGuncel();     // motorla aynı aks–kat düğüm numarası
      const var_ = (geo && geo.dugumler.some(function (d) { return d.no === no; })) || (v && v.ag && (v.ag.dugumler || []).some(function (d) { return d.no === no; }));
      return ix >= 0 && iy >= 0 && var_ ? { tur: "dugum", no: no } : null;
    }
    if (h.kind === "hucre") { const d = dosemeBul(h.kose[0], D.kat); return d ? { tur: "doseme", no: d.no } : null; }
    return null;
  }

  // ---- ölçüm (MatrisOlcum.Arac): sahnenin kendi jestleri dokunuş/hover verir; ölçüler "olcum" katmanında
  const OLCUM_KIP = { "olc-uzaklik": "uzaklik", "olc-aci": "aci", "olc-alan": "alan", "olc-boy": "boy", "olc-kot": "kot", "olc-koordinat": "koordinat" };
  let olcum = null, olcumMetin = "";
  const geoOnbellek = { anahtar: null, geo: null };
  function olcumGeo() {
    const O = modul("MatrisOlcum");
    if (!O || !B) return null;
    const a = sonAnlik || anlikGoruntu();
    if (geoOnbellek.anahtar !== a) {
      let g = null;
      try { g = O.geometri(B); } catch (e) { g = null; }
      geoOnbellek.anahtar = a; geoOnbellek.geo = g;
    }
    return geoOnbellek.geo;
  }
  const OLCUM_IPUCU = "Ölçüm: düğüme, aks kesişimine ya da çubuğa dokunun (yakalama işareti görünür). Esc yarım ölçümü siler, yarım ölçüm yoksa " +
    "ölçümden çıkar (sonuçlar kalır); “Ölçüleri temizle” hepsini siler.";
  function olcumEscNotu() {
    return olcum && olcum.olcer.bekleyen.length ? " · Esc: yarım ölçümü siler." : " · Esc: ölçümden çıkar (sonuçlar kalır); “Ölçüleri temizle” hepsini siler.";
  }
  function olcumKur() {
    const O = modul("MatrisOlcum");
    if (!O || !O.Arac || olcum) return;
    olcum = new O.Arac({
      geo: function () { return olcumGeo(); },
      cevir: function () { return SAHNE_BAGLAM ? SAHNE_BAGLAM.P3 : null; },
      kip: "uzaklik", tol: 14,
      escSonuclariKorur: true,      // Esc yalnız yarım ölçümü siler; yoksa sayfa Esc'i kipten çıkar (bitir), sonuçlar "Ölçüleri temizle"ye dek kalır
      ipucu: function (m) { olcumMetin = m || ""; ipucuYaz(); },
      degisti: function () { aracYenile(); },
    });
    katmanKaydet("olcum", function () { return olcum.svg(); }, { sira: 50, bagla: function (g) { g.setAttribute("class", "bn-katman olcum-kok"); olcum.sec.katman = g; } });
    Object.keys(OLCUM_KIP).forEach(function (id) {
      kipKaydet(id, {
        basla: function () { olcum.kipSec(OLCUM_KIP[id]); },
        // kipten çıkınca yalnız yarım ölçüm silinir; tamamlanan ölçüler "Ölçüleri temizle"ye kadar kalır (ölçü türleri birleştirilebilir)
        bitir: function () { olcum.yakalanan = null; olcum.olcer.bekleyen = []; olcum.ciz(); olcumMetin = ""; aracYenile(); },
        dokun: function (p) { olcum.sec.tol = 14 * pxOlcek(); olcum.dokun(p); },
        hareket: function (p) { olcum.sec.tol = 14 * pxOlcek(); olcum.hareket(p); },
        // Esc: yarım ölçüm varsa onu siler; yoksa işlenmez (escSonuclariKorur) → sayfa Esc'i kipten çıkar, tamamlanan ölçüler kalır
        tus: function (e) { return (e.key === "Escape" || e.key === "Enter" || e.key === "Backspace") && olcum.tus(e.key); },
        // adım iletisi (olcum.js: "Birinci noktayı seçin." …) Esc'in o anki etkisini de söyler
        ipucu: function () { return olcumMetin ? olcumMetin + olcumEscNotu() : OLCUM_IPUCU; },
      });
    });
  }

  // ---- kopyala / yapıştır (aks–kat: seçili kolon, kiriş ve döşemeler etkin kata — ya da “Tüm katlara uygula” ile bütün katlara — aynı akslarda)
  let PANO = null;
  function metinSecili() { try { const s = window.getSelection && window.getSelection(); return !!(s && String(s).trim()); } catch (e) { return false; } }
  function kopyalanabilir() { return D.secim.filter(function (s) { return nesneBul(s.tur, s.no); }); }
  function kopyala() {
    const l = kopyalanabilir();
    if (!l.length) return;
    PANO = { kolonlar: [], kirisler: [], dosemeler: [], s3: { cubuklar: [], paneller: [] }, catiKat: ustKat() };
    l.forEach(function (s) {
      const n = nesneBul(s.tur, s.no), liste = { kolon: "kolonlar", kiris: "kirisler", doseme: "dosemeler" }[s.tur];
      if (liste) PANO[liste].push(kopya(n));
      else if (s.tur === "cubuk") PANO.s3.cubuklar.push(+s.no);
      else if (s.tur === "panel") PANO.s3.paneller.push(+s.no);
    });
    const s3 = PANO.s3.cubuklar.length + PANO.s3.paneller.length;
    A.toast(l.length + " eleman panoya alındı. " + (s3 ? "Yapıştır (Ctrl+V): kaynak kesişime, sonra hedef kesişime dokunun (aks aralığı kadar ötelenir)." : "Başka bir kata geçip Yapıştır (Ctrl+V): aynı akslara kopyalanır."));
    aracYenile();
  }
  function yapistir() {
    if (!PANO) return;
    if (PANO.s3 && PANO.s3.cubuklar.length + PANO.s3.paneller.length && KIPLER.yapistir) {     // genel model: kesişimden kesişime öteleme kipi
      aracSec("yapistir"); yenile(); return;
    }
    const hedefKatlar = katlarHedef(), yeniSecim = [], cati = ustKat();
    let n = 0, atlanan = 0, parapet = 0;
    const aksVar = function (aks) { return aksX(aks[0]) != null && aksY(aks[1]) != null; };
    hedefKatlar.forEach(function (kat) {
      PANO.kolonlar.forEach(function (c) {
        if (!aksVar(c.aks) || kolonBul(c.aks, kat)) { atlanan++; return; }
        const y = Object.assign(kopya(c), { no: yeniNo(B.kolonlar), kat: kat }); B.kolonlar.push(y); yeniSecim.push({ tur: "kolon", no: y.no }); n++;
      });
      PANO.kirisler.forEach(function (k) {
        if (!aksVar(k.bas) || !aksVar(k.son) || kirisBul(k.bas, k.son, kat)) { atlanan++; return; }
        const y = Object.assign(kopya(k), { no: yeniNo(B.kirisler), kat: kat });
        // çatı kirişinin parapeti (duvar_h) ara kata taşınmaz: orada duvar kat yüksekliğindedir
        if (y.duvar_h != null && k.kat === PANO.catiKat && kat !== cati) { delete y.duvar_h; parapet++; }
        B.kirisler.push(y); yeniSecim.push({ tur: "kiris", no: y.no }); n++;
      });
      PANO.dosemeler.forEach(function (d) {
        if (!aksVar(d.kose[0]) || !aksVar(d.kose[1]) || dosemeBul(d.kose[0], kat)) { atlanan++; return; }
        const y = Object.assign(kopya(d), { no: yeniNo(B.dosemeler), kat: kat }); B.dosemeler.push(y); yeniSecim.push({ tur: "doseme", no: y.no }); n++;
      });
    });
    if (!n) { A.toast("Yapıştırılacak yer yok: hedef katta aynı akslarda zaten eleman var" + (atlanan ? " (" + atlanan + " atlandı)." : ".")); return; }
    const tur0 = yeniSecim[0].tur;
    D.secim = yeniSecim.filter(function (s) { return s.tur === tur0; });
    A.toast(n + " eleman yapıştırıldı" + (atlanan ? " (" + atlanan + " dolu yer atlandı)" : "") + "." +
      (parapet ? " " + parapet + " çatı kirişinin parapet yüksekliği (duvar_h) ara katta kullanılmadı; duvar kat yüksekliğinde." : ""));
    degisti();
  }
  function firca() {
    if (D.firca) { D.firca = null; yenile(); return; }
    const s = D.secim[0], n = s && nesneBul(s.tur, s.no);
    if (n && n.kesit && (s.tur === "kolon" || s.tur === "kiris")) {
      D.firca = n.kesit; aracSec("sec"); D.secim = []; yenile();
      A.toast("Fırça: " + n.kesit + " — dokunduğunuz kolon/kirişe atanır. Esc bırakır.");
    } else { D.panelSekme = "kutuphane"; panelAc(); yenile(); A.toast("Kütüphanede bir kesitin fırça düğmesine basın ya da önce bir kolon/kiriş seçin."); }
  }
  function panelGit(sekme) { D.panelSekme = sekme; yenile(); panelAc(); }
  function katGec(adim) {
    const l = B.katlar.map(function (k) { return k.no; }).sort(function (a, b) { return a - b; }), i = l.indexOf(D.kat), j = Math.max(0, Math.min(l.length - 1, i + adim));
    if (j === i) return;
    D.kat = l[j]; D.zAks = null; D.kirisBas = null; if (kamera) kamera.sifirla(); yenile(); olayYay("gorunum", gorunum());
  }
  function sonucSekmesiGit(sekme) {
    if (!SON) { A.toast("Önce modeli çözün (Çöz ▶)."); return; }
    D.sekme = sekme;
    if (ref.sonuc.querySelector(".bn-sekmeler")) sekmeCiz(); else sonucuCiz();
    cekmeceAc();
    if (!D.tamEkran) { const s0 = document.getElementById("bn-sekme-icerik"); if (s0) s0.scrollIntoView({ block: "nearest", behavior: azHareket() ? "auto" : "smooth" }); }
    aracYenile();
  }

  // ---- Model denetimi (aks–kat: dogrula(); surum 3 listeleri varsa ModelOps.denetle de)
  function modelDenetle() {
    const dg = dogrula();
    const ek = [];      // genel model (ModelOps.denetle) bulguları dogrula() uyarılarında
    const k = kaplamaAc("denetim", "Model denetimi", { kucuk: true });
    const satir = function (u, sinif) {
      const hedef = u.tur && u.no != null ? ' data-denetim-tur="' + kacis(u.tur) + '" data-denetim-no="' + u.no + '" data-denetim-kat="' + (u.kat != null ? u.kat : "") + '"' : "";
      return '<li class="' + sinif + '">' + (hedef ? '<button type="button" class="bn-bag"' + hedef + ">" + kacis(u.metin || u.mesaj) + "</button>" : kacis(u.metin || u.mesaj || u)) + "</li>";
    };
    const n = dg.hata.length + dg.uyari.length + ek.length;
    k.govde.innerHTML = (n ? "" : '<p class="bn-denetim-tamam">✓ Sorun bulunmadı: model çözüme hazır.</p>') +
      (dg.hata.length ? "<h3>Düzeltilmesi gerekenler (" + dg.hata.length + ")</h3><ul class=\"bn-denetim\">" + dg.hata.map(function (m) { return satir({ metin: m }, "hata"); }).join("") + "</ul>" : "") +
      (dg.uyari.length ? "<h3>Uyarılar (" + dg.uyari.length + ")</h3><ul class=\"bn-denetim\">" + dg.uyari.map(function (u) { return satir(u, "uyari"); }).join("") + "</ul>" : "") +
      (ek.length ? "<h3>Serbest model (" + ek.length + ")</h3><ul class=\"bn-denetim\">" + ek.map(function (u) { return satir(u, "uyari"); }).join("") + "</ul>" : "") +
      '<p class="not">Uyarıya dokunun: eleman seçilir ve katı açılır.</p>';
    k.govde.addEventListener("click", function (e) {
      const t = e.target.closest("[data-denetim-tur]");
      if (!t) return;
      if (t.dataset.denetimKat !== "") D.kat = +t.dataset.denetimKat;
      D.secim = [{ tur: t.dataset.denetimTur, no: +t.dataset.denetimNo }]; D.panelSekme = "nesne";
      kaplamaKapat(); yenile(); panelAc();
    });
  }

  // =====================================================================================================================
  // Kaplama: rapor önizleme, tablolar, ısı haritası, IFC ve küçük iletişim kutuları için tek tip modal pencere.
  // Düzenleyicinin içine eklenir (tam ekranda da görünür); Esc (modül içinde değilse) ya da ✕ kapatır; odak kapanınca geri döner.
  // =====================================================================================================================
  let KAPLAMA = { tur: null };
  function modalAcik() { return !!(KAPLAMA.el || kok.querySelector("dialog[open]")); }
  function kaplamaAc(tur, baslik, sec) {
    kaplamaKapat();
    sec = sec || {};
    const el = document.createElement("div"), id = "bn-kaplama-baslik-" + tur;
    el.className = "bn-kaplama" + (sec.kucuk ? " bn-kaplama-kucuk" : "") + (sec.genis ? " bn-kaplama-genis" : "");
    el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true"); el.setAttribute("aria-labelledby", id);
    el.dataset.kaplama = tur;
    el.innerHTML = '<div class="bn-kaplama-pencere"><div class="bn-kaplama-ust"><h2 id="' + id + '">' + kacis(baslik) + "</h2>" +
      '<div class="bn-kaplama-araclar"></div><button type="button" class="dugme kucuk bn-kaplama-kapat" data-kaplama-kapat aria-label="Kapat" title="Kapat (Esc)">✕</button></div>' +
      '<div class="bn-kaplama-govde" tabindex="-1"></div></div>';
    kok.appendChild(el);
    document.body.classList.add("bn-kaplama-acik");
    const k = { tur: tur, el: el, govde: el.querySelector(".bn-kaplama-govde"), araclar: el.querySelector(".bn-kaplama-araclar"), temizle: null,
      odak: document.activeElement && document.activeElement !== document.body ? document.activeElement : null };
    KAPLAMA = k;
    el.addEventListener("click", function (e) { if (e.target.closest("[data-kaplama-kapat]")) kaplamaKapat(); });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !e.defaultPrevented && !(e.target.closest && e.target.closest(".tablo-ed, .isi-kok"))) { e.preventDefault(); kaplamaKapat(); return; }
      if (e.key === "Tab") {      // odak kaplama içinde döner
        const l = Array.from(el.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea, iframe, [tabindex]:not([tabindex="-1"])')).filter(function (x) { return x.offsetParent !== null || x === document.activeElement; });
        if (!l.length) return;
        if (e.shiftKey && document.activeElement === l[0]) { e.preventDefault(); l[l.length - 1].focus(); }
        else if (!e.shiftKey && document.activeElement === l[l.length - 1]) { e.preventDefault(); l[0].focus(); }
      }
    });
    setTimeout(function () { if (KAPLAMA === k) { const o = el.querySelector(sec.odak || ".bn-kaplama-kapat"); if (o) o.focus({ preventScroll: true }); } }, 0);
    aracYenile();
    return k;
  }
  function kaplamaKapat() {
    const k = KAPLAMA;
    if (!k.el) return;
    KAPLAMA = { tur: null };
    if (k.temizle) { try { k.temizle(); } catch (e) { /* yoksay */ } }
    k.el.remove();
    document.body.classList.remove("bn-kaplama-acik");
    if (k.odak && k.odak.isConnected && k.odak.focus) { try { k.odak.focus({ preventScroll: true }); } catch (e) { /* yoksay */ } }
    aracYenile();
  }
  function bekleNotu(kap, m) { kap.innerHTML = '<p class="not bn-bekle" role="status"><span class="bn-donen" aria-hidden="true"></span> ' + kacis(m) + "</p>"; }
  function hataNotu(kap, m, baslik) { kap.innerHTML = ""; const d = document.createElement("div"); kap.appendChild(d); hataGoster(d, [m], baslik || ""); }
  function motorHatasi(y, varsayilan) { return y && y.hata ? y.hata : varsayilan || "Boş yanıt."; }
  function dosyaAdiTemiz(s) { return String(s || "bina").replace(/[^\wğüşöçıİĞÜŞÖÇ.-]+/g, "_").replace(/^_+|_+$/g, "") || "bina"; }
  function dosyaKaydet(ad, icerik, tur) {
    const F = modul("MatrisDosya");
    if (F) return F.kaydet(ad, icerik, tur);
    const blob = new Blob([icerik], { type: tur === "html" ? "text/html;charset=utf-8" : tur === "ifc" ? "application/x-step" : tur === "csv" ? "text/csv;charset=utf-8" : "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = ad;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
    return Promise.resolve({ ad: ad });
  }

  // ---- proje künyesi (rapor kapağı, IFC proje bilgisi): görüntüleyene özel, localStorage (try/catch)
  const KUNYE_ANAHTAR = "bina.rapor.kunye", RAPOR_TABLO_ANAHTAR = "bina.rapor.tablolar", RAPOR_AYAR_ANAHTAR = "bina.rapor.ayar";
  const KUNYE_ALANLARI = [["ad", "Proje adı"], ["yer", "Yer / adres"], ["il", "İl"], ["ilce", "İlçe"], ["ada", "Ada"], ["parsel", "Parsel"], ["malik", "Yapı sahibi"], ["hazirlayan", "Hazırlayan"], ["kontrol", "Kontrol eden"], ["tarih", "Tarih"]];
  function depoOku(a, v) { try { const s = localStorage.getItem(a); return s ? JSON.parse(s) : v; } catch (e) { return v; } }
  function depoYaz(a, v) { try { localStorage.setItem(a, JSON.stringify(v)); } catch (e) { /* özel pencere: yalnız bu oturum */ } }
  function kunye() {
    const k = depoOku(KUNYE_ANAHTAR, {}) || {}, o = {};
    KUNYE_ALANLARI.forEach(function (a) { if (k[a[0]] != null && String(k[a[0]]).trim()) o[a[0]] = String(k[a[0]]).trim(); });
    if (!o.ad && B && B.baslik) o.ad = B.baslik;
    return o;
  }
  let RAPOR_TABLOLAR = new Set(depoOku(RAPOR_TABLO_ANAHTAR, []) || []), RAPOR_FILTRE = {};
  function raporTablolariAyarla(s) { RAPOR_TABLOLAR = new Set(Array.from(s || [])); depoYaz(RAPOR_TABLO_ANAHTAR, Array.from(RAPOR_TABLOLAR)); }

  // =====================================================================================================================
  // 📄 Statik rapor: köprü "bina_rapor" {cozum_kimligi, bina, secenek: {proje, eleman_detay, tablolar, tablo_filtre}} → {html, dosya_adi}
  // Çözüm yoksa (ya da model değiştiyse) önce çözer. Önizleme iframe'de; Yazdır / PDF, HTML indir, yeni pencerede aç.
  // =====================================================================================================================
  let RAPOR = null;     // {anahtar, html, dosya_adi}
  let RAPOR_EK = [];    // eleman bilgi penceresinden "Rapora ekle" ile gelen tablolar (bu oturum; köprüde secenek.ek_tablolar)
  function denetciRaporaEkle(k) {
    const satirlar = String(k.tsv || "").split("\n").slice(1).filter(function (l) { return l.trim(); }).map(function (l) { return l.split("\t"); });
    const n = Math.max(2, Math.min(8, satirlar.reduce(function (m, r) { return Math.max(m, r.length); }, 0)));
    const ad = "eleman_" + k.tur + "_" + k.no + "_" + (k.sekme || "hepsi"), bas = ["Büyüklük", "Değer", "Birim"], sut = [];
    for (let i = 0; i < n; i++) sut.push({ ad: "s" + i, baslik: bas[i] || "Sütun " + (i + 1), tur: "metin" });
    const t = { ad: ad, baslik: (k.baslik || "Eleman") + (k.adres ? " (" + k.adres + ")" : "") + (k.sekmeAdi ? " — " + k.sekmeAdi : ""), grup: "Eleman", sutunlar: sut,
      satirlar: satirlar.map(function (r) { const d = {}; r.slice(0, n).forEach(function (v, i) { d["s" + i] = v; }); return { degerler: d }; }),
      aciklama: "Eleman bilgi penceresinden eklendi" + (k.durum ? " (durum: " + k.durum + ")" : "") + "." };
    RAPOR_EK = RAPOR_EK.filter(function (x) { return x.ad !== ad; }).concat([t]);
    A.toast("Rapora eklendi: " + t.baslik + ". Raporu açıp “Raporu oluştur” ile yenileyin.");
  }
  let TABLO_ED = null;  // açık tablo editörü (rapor seçimi canlı okunur)
  function raporSecenegi() {
    const ayar = depoOku(RAPOR_AYAR_ANAHTAR, {}) || {};
    const f = {};
    RAPOR_TABLOLAR.forEach(function (ad) { if (RAPOR_FILTRE[ad]) f[ad] = RAPOR_FILTRE[ad]; });
    let t = { tablolar: Array.from(RAPOR_TABLOLAR), tablo_filtre: f };
    if (TABLO_ED && TABLO_ED.raporSecenegi) { try { t = TABLO_ED.raporSecenegi(); } catch (e) { /* yoksay */ } }
    return { proje: kunye(), eleman_detay: ["kritik", "hepsi", "yok"].indexOf(ayar.eleman_detay) >= 0 ? ayar.eleman_detay : "kritik", tablolar: t.tablolar || [], tablo_filtre: t.tablo_filtre || {},
      ek_tablolar: RAPOR_EK.slice() };
  }
  function raporAc(sec) {
    sec = sec || {};
    const k = kaplamaAc("rapor", "Statik hesap raporu", { genis: true, odak: sec.kunye ? "[data-kunye=ad]" : null });
    const ayar = depoOku(RAPOR_AYAR_ANAHTAR, {}) || {}, ky = depoOku(KUNYE_ANAHTAR, {}) || {};
    k.araclar.innerHTML = '<button type="button" class="dugme kucuk ana" data-rapor="yazdir" disabled>Yazdır / PDF</button>' +
      '<button type="button" class="dugme kucuk" data-rapor="indir" disabled>HTML indir</button>' +
      '<button type="button" class="dugme kucuk" data-rapor="pencere" disabled>Yeni pencerede aç</button>';
    k.govde.innerHTML = '<div class="bn-rapor">' +
      '<details class="bn-rapor-form"' + (sec.kunye || window.innerWidth >= 900 ? " open" : "") + '><summary>Proje künyesi ve rapor içeriği</summary><form class="bn-rapor-alanlar" data-rapor-form>' +
      KUNYE_ALANLARI.map(function (a) {
        return '<label class="bn-alan"><span>' + kacis(a[1]) + '</span><input class="girdi" data-kunye="' + a[0] + '" value="' + kacis(ky[a[0]] != null ? ky[a[0]] : (a[0] === "ad" && B.baslik ? B.baslik : "")) + '"' +
          (a[0] === "tarih" ? ' placeholder="' + kacis(new Date().toLocaleDateString("tr-TR")) + '"' : "") + "></label>";
      }).join("") +
      '<label class="bn-alan"><span>Eleman ayrıntısı</span><select class="girdi" data-rapor-ayar="eleman_detay">' +
        secenekler([["kritik", "Kritik elemanlar (her türde en büyük D/C ve D/C > 1)"], ["hepsi", "Bütün elemanlar"], ["yok", "Yalnız özet tablolar"]], ayar.eleman_detay || "kritik") + "</select></label>" +
      '<p class="not bn-rapor-tablolar"></p>' +
      '<div class="dugmeler"><button type="button" class="dugme ana" data-rapor="olustur">Raporu oluştur</button><button type="button" class="dugme" data-rapor="tablolar">Tabloları seç…</button>' +
        (RAPOR_EK.length ? '<button type="button" class="dugme" data-rapor="ek-temizle">Eleman eklerini çıkar</button>' : "") + "</div>" +
      "</form></details>" +
      '<div class="bn-rapor-durum" aria-live="polite"></div>' +
      '<iframe class="bn-rapor-onizleme" title="Statik hesap raporu önizlemesi" sandbox="allow-same-origin" hidden></iframe></div>';
    // tablo kimlikleri son bina_tablolar yanıtındaki başlıklarla yazılır (bilinmeyen kimlik varsa başlıklar bir kez motordan istenir)
    const tabloNotu = function () {
      const s = raporSecenegi(), n = s.tablolar.length, el = k.govde.querySelector(".bn-rapor-tablolar");
      if (!el) return;
      el.textContent = (n ? "Rapora eklenecek tablolar (Ek C): " + n + " — " + s.tablolar.slice(0, 6).map(function (id) { return TABLO_BASLIK[id] || id; }).join(", ") + (n > 6 ? " …" : "") : "Rapora ek tablo seçilmedi (Tablolar penceresinde onay kutularıyla seçilir).") +
        (RAPOR_EK.length ? " Eleman bilgisinden eklenen: " + RAPOR_EK.length + "." : "");
    };
    // masaüstü içerik güvenliği ilkesi satır içi olay özniteliğini (onsubmit) çalıştırmaz: Enter formu göndermesin (sayfa yenilenmesin)
    const rf = k.govde.querySelector("[data-rapor-form]");
    if (rf) rf.addEventListener("submit", function (e) { e.preventDefault(); });
    tabloNotu();
    if (raporSecenegi().tablolar.some(function (id) { return !TABLO_BASLIK[id]; })) tabloBasliklariAl().then(function () { if (KAPLAMA === k) tabloNotu(); });
    k.govde.addEventListener("change", function (e) {
      const el = e.target;
      if (el.dataset.kunye) { const v = depoOku(KUNYE_ANAHTAR, {}) || {}; v[el.dataset.kunye] = el.value; depoYaz(KUNYE_ANAHTAR, v); }
      else if (el.dataset.raporAyar) { const v = depoOku(RAPOR_AYAR_ANAHTAR, {}) || {}; v[el.dataset.raporAyar] = el.value; depoYaz(RAPOR_AYAR_ANAHTAR, v); }
    });
    const tik = function (e) {
      const t = e.target.closest("[data-rapor]");
      if (!t || t.disabled) return;
      const a = t.dataset.rapor;
      if (a === "olustur") raporUret(k);
      else if (a === "tablolar") tablolarAc();
      else if (a === "ek-temizle") { RAPOR_EK = []; t.remove(); tabloNotu(); }
      else if (a === "yazdir" && RAPOR) raporYazdir();
      else if (a === "indir" && RAPOR) dosyaKaydet(RAPOR.dosya_adi, RAPOR.html, "html");
      else if (a === "pencere" && RAPOR) raporPencere();
    };
    k.el.addEventListener("click", tik);
    const anahtar = raporAnahtari();
    if (RAPOR && RAPOR.anahtar === anahtar) raporGoster(k); else raporUret(k);
    return k;
  }
  function raporAnahtari() { return (cozumKimligi() || "") + "|" + JSON.stringify(raporSecenegi()); }
  function raporDurum(k, html) { const d = k.govde.querySelector(".bn-rapor-durum"); if (d) d.innerHTML = html; }
  function raporUret(k) {
    if (!k || !k.el) return Promise.resolve(false);
    const dugmeler = k.el.querySelectorAll("[data-rapor]");
    dugmeler.forEach(function (b) { if (b.dataset.rapor !== "tablolar") b.disabled = true; });
    raporDurum(k, '<p class="not bn-bekle" role="status"><span class="bn-donen" aria-hidden="true"></span> ' + (SON && !sonEski ? "Rapor hazırlanıyor…" : "Rapor için önce model çözülüyor…") + "</p>");
    return cozumHazir().then(function (ok) {
      if (!ok || !SON || sonEski) throw new Error("Rapor için modelin çözülmesi gerekiyor; çözüm tamamlanmadı" + (sonCozumHatasi ? ": " + sonCozumHatasi : "."));
      if (KAPLAMA !== k) return null;
      raporDurum(k, '<p class="not bn-bekle" role="status"><span class="bn-donen" aria-hidden="true"></span> Rapor hazırlanıyor…</p>');
      const secenek = raporSecenegi();
      return A.motorIstegi({ islem: "bina_rapor", girdi: { cozum_kimligi: cozumKimligi(), bina: SON.bina || kopya(B), secenek: secenek } }).then(function (y) {
        if (!y || y.hata || !y.html) throw new Error(motorHatasi(y, "Rapor motorundan yanıt gelmedi."));
        RAPOR = { anahtar: raporAnahtari(), html: y.html, dosya_adi: y.dosya_adi || ("statik_rapor_" + dosyaAdiTemiz(B.baslik) + ".html") };
        if (KAPLAMA === k) raporGoster(k);
        return true;
      });
    }).catch(function (e) {
      if (KAPLAMA !== k) return false;
      raporDurum(k, "");
      const d = document.createElement("div"); k.govde.querySelector(".bn-rapor-durum").appendChild(d);
      hataGoster(d, [(e && e.message) || String(e)], "Rapor oluşturulamadı");
      k.el.querySelectorAll('[data-rapor="olustur"]').forEach(function (b) { b.disabled = false; });
      return false;
    });
  }
  function raporGoster(k) {
    const f = k.govde.querySelector(".bn-rapor-onizleme");
    f.hidden = false; f.srcdoc = RAPOR.html;
    k.el.querySelectorAll("[data-rapor]").forEach(function (b) { b.disabled = false; });
    raporDurum(k, '<p class="not">' + kacis(RAPOR.dosya_adi) + " · " + Math.round(RAPOR.html.length / 1024) + " kB · çözüm " + kacis(String(cozumKimligi() || "").slice(0, 10)) +
      ". Künyeyi ya da tablo seçimini değiştirdiyseniz “Raporu oluştur” ile yenileyin.</p>");
    olayYay("rapor", { dosya_adi: RAPOR.dosya_adi, bayt: RAPOR.html.length });
  }
  function raporYazdir() {
    const F = modul("MatrisDosya");
    if (F && F.pdfYazdir) return F.pdfYazdir(RAPOR.html, RAPOR.dosya_adi.replace(/\.html?$/i, ""));
    raporPencere(true);
    return Promise.resolve(null);
  }
  function raporPencere(yazdir) {
    const url = URL.createObjectURL(new Blob([RAPOR.html], { type: "text/html;charset=utf-8" }));
    const p = window.open(url, "_blank");
    if (!p) { A.toast("Açılır pencere engellendi; “HTML indir” ile kaydedip açabilirsiniz."); return; }
    if (yazdir) p.addEventListener("load", function () { try { p.print(); } catch (e) { /* yoksay */ } });
    setTimeout(function () { URL.revokeObjectURL(url); }, 60000);
  }

  // =====================================================================================================================
  // ⬇ IFC: MatrisIFC.uretAyrintili(bina, veri?, secenek) → {metin, uyarilar, sayac, dosya_adi} → MatrisDosya.kaydet(…, "ifc")
  // =====================================================================================================================
  function ifcAc() {
    const M = modul("MatrisIFC");
    if (!M) { A.toast("IFC modülü yüklenmedi."); return; }
    const v = veriGuncel();
    const k = kaplamaAc("ifc", "IFC dışa aktarımı", { kucuk: true, odak: "[data-ifc=indir]" });
    let ad = "bina.ifc";
    try { ad = M.dosyaAdi(B); } catch (e) { /* varsayılan */ }
    k.govde.innerHTML = '<p class="not">IFC4 (ISO 10303-21) yapı modeli: katlar, aks ızgaraları, kolon/kiriş/döşeme/temel katıları, malzeme ve kesitler; isteğe bağlı yapısal analiz modeli. BIM görüntüleyicilerinde açılır.</p>' +
      '<form class="bn-ifc">' +
      '<label class="bn-onay"><input type="checkbox" data-ifc-s="analiz" checked> Yapısal analiz modeli (düğümler, çubuklar, mesnetler, yük grupları)</label>' +
      '<label class="bn-onay"><input type="checkbox" data-ifc-s="yukler"' + (v ? " checked" : " disabled") + "> " + (v && v.model === "genel" ? "G, Q ve S yükleri" : "G ve Q yükleri") + (v ? "" : " (çözüm gerekir)") + "</label>" +
      '<label class="bn-onay"><input type="checkbox" data-ifc-s="sonuclar"' + (v ? " checked" : " disabled") + "> Tasarım sonuçları (D/C özellikleri)" + (v ? "" : " (çözüm gerekir)") + "</label>" +
      '<label class="bn-alan"><span>Aks ızgarası</span><select class="girdi" data-ifc-s="izgara">' + secenekler([["kat", "Her kat seviyesinde"], ["tek", "Yalnız en altta"], ["yok", "Yok"]], "kat") + "</select></label>" +
      '<label class="bn-alan"><span>Dosya adı</span><input class="girdi" data-ifc-s="dosya_adi" value="' + kacis(ad) + '"></label>' +
      (SON && sonEski ? '<p class="not">Model çözümden sonra değişti: yükler ve D/C eklenmez (yeniden çözün).</p>' : "") +
      '<div class="dugmeler"><button type="button" class="dugme ana" data-ifc="indir">IFC dosyasını kaydet</button><button type="button" class="dugme" data-kaplama-kapat>Vazgeç</button></div>' +
      '<div class="bn-ifc-sonuc" aria-live="polite"></div></form>';
    const indir = function () {
      const s = function (a) { return k.govde.querySelector('[data-ifc-s="' + a + '"]'); };
      const izg = s("izgara").value;
      const secenek = { analiz: s("analiz").checked, yukler: !!v && s("yukler").checked, sonuclar: !!v && s("sonuclar").checked, izgara: izg === "yok" ? false : izg,
        proje: kunye(), dosya_adi: (s("dosya_adi").value.trim() || ad).replace(/(\.ifc)?$/i, ".ifc") };
      ifcUret(secenek, k.govde.querySelector(".bn-ifc-sonuc"));
    };
    k.govde.addEventListener("click", function (e) { if (e.target.closest("[data-ifc=indir]")) indir(); });
    // Enter (dosya adı alanında) = "IFC dosyasını kaydet"; satır içi onsubmit masaüstü içerik güvenliği ilkesinde çalışmaz
    const f = k.govde.querySelector("form.bn-ifc");
    if (f) f.addEventListener("submit", function (e) { e.preventDefault(); indir(); });
  }
  // dışa aktarır; sonuc kutusu verilirse özet yazar. Dönüş: Promise<{dosya_adi, bayt, uyarilar, sayac} | null>
  function ifcUret(secenek, kutu) {
    const M = modul("MatrisIFC");
    if (!M) return Promise.resolve(null);
    const v = veriGuncel();
    let r;
    try { r = M.uretAyrintili(kopya(B), v, secenek || { analiz: true, yukler: !!v, sonuclar: !!v, proje: kunye() }); }
    catch (e) { if (kutu) hataNotu(kutu, (e && e.message) || String(e), "IFC üretilemedi"); else A.toast("IFC üretilemedi: " + ((e && e.message) || e)); return Promise.resolve(null); }
    const ozet = { dosya_adi: r.dosya_adi, bayt: r.metin.length, uyarilar: r.uyarilar || [], sayac: r.sayac || {} };
    return dosyaKaydet(r.dosya_adi, r.metin, "ifc").then(function (k) {
      if (kutu) {
        const sc = ozet.sayac, say = [["IFCBUILDINGSTOREY", "kat"], ["IFCCOLUMN", "kolon"], ["IFCBEAM", "kiriş"], ["IFCMEMBER", "diğer çubuk"], ["IFCSLAB", "döşeme"], ["IFCFOOTING", "temel"],
          ["IFCSTRUCTURALCURVEMEMBER", "analiz çubuğu"], ["IFCSTRUCTURALPOINTCONNECTION", "analiz düğümü"]].filter(function (a) { return sc[a[0]]; }).map(function (a) { return sc[a[0]] + " " + a[1]; });
        kutu.innerHTML = '<p class="bn-denetim-tamam">' + (k ? "✓ Kaydedildi: " + kacis(k.ad || r.dosya_adi) : "Kaydetme iptal edildi.") + " · " + Math.round(ozet.bayt / 1024) + " kB</p>" +
          (say.length ? '<p class="not">' + kacis(say.join(" · ")) + "</p>" : "") +
          (ozet.uyarilar.length ? '<ul class="bn-denetim">' + ozet.uyarilar.slice(0, 12).map(function (u) { return '<li class="uyari">' + kacis(u) + "</li>"; }).join("") + "</ul>" : "");
      }
      olayYay("ifc", ozet);
      return k ? ozet : null;
    }, function (e) { if (kutu) hataNotu(kutu, (e && e.message) || String(e), "IFC kaydedilemedi"); return null; });
  }

  // =====================================================================================================================
  // ▦ Tablolar: köprü "bina_tablolar" {cozum_kimligi, bina} → {tablolar, cozumlu}; MatrisTablo.ac(...) editörü; düzenle → binaAyarla (tek geri al
  // yığını) + çözüm eski + tablolar yeniden; rapor seçimi saklanır ve rapora iletilir.
  // =====================================================================================================================
  let tabloIstekSira = 0, tabloTazeleZ = 0;
  const TABLO_BASLIK = {};      // tablo kimliği → başlık (son bina_tablolar yanıtından; rapor notunda kimlik yerine)
  function tabloBasliklariYaz(y) { ((y && y.tablolar) || []).forEach(function (t) { if (t && t.ad) TABLO_BASLIK[t.ad] = t.baslik || t.ad; }); }
  function tabloBasliklariAl() {
    const kimlik = cozumKimligi();
    return Promise.resolve(A.motorIstegi({ islem: "bina_tablolar", girdi: kimlik ? { cozum_kimligi: kimlik } : { bina: kopya(B) } })).then(function (y) { tabloBasliklariYaz(y); }, function () { /* yoksay */ });
  }
  function tabloIste() {
    const sira = ++tabloIstekSira, kimlik = cozumKimligi();
    // güncel çözüm varsa yalnız kimlik gider (köprü bina verilince kimliği aks–kat okuyucusuyla yeniden hesaplar; genel modelde eşleşmez);
    // çözüm bellekten düşmüşse bina ile yeniden istenir
    const iste = function (g) { return A.motorIstegi({ islem: "bina_tablolar", girdi: g }); };
    return iste(kimlik ? { cozum_kimligi: kimlik } : { bina: kopya(B) }).then(function (y) {
      if (kimlik && y && y.hata && /bellekte yok/i.test(String(y.hata))) return iste({ bina: kopya(B) });
      return y;
    }).then(function (y) {
      if (sira !== tabloIstekSira) return null;      // daha yeni istek var
      if (!y || y.hata || !Array.isArray(y.tablolar)) throw new Error(motorHatasi(y, "Tablo yanıtı boş."));
      tabloBasliklariYaz(y);
      return y;
    });
  }
  // secenek.csvIceri: editör açılır açılmaz CSV içe aktarma başlar (masaüstü Dosya › İçe aktar › Tablolar (.csv)…; sözleşme C23)
  function tablolarAc(baslangic, secenek) {
    const M = modul("MatrisTablo");
    if (!M) { A.toast("Tablo editörü modülü yüklenmedi."); return; }
    const k = kaplamaAc("tablolar", "Tablolar ve metraj", { genis: true });
    k.araclar.innerHTML = '<button type="button" class="dugme kucuk" data-tablo-git="rapor">📄 Rapora geç</button>';
    k.araclar.addEventListener("click", function (e) { if (e.target.closest("[data-tablo-git]")) { const s = TABLO_ED ? TABLO_ED.raporSecimi() : RAPOR_TABLOLAR; raporTablolariAyarla(s); raporAc(); } });
    bekleNotu(k.govde, "Tablolar hazırlanıyor…");
    k.temizle = function () {
      if (TABLO_ED) { try { raporTablolariAyarla(TABLO_ED.raporSecimi()); RAPOR_FILTRE = TABLO_ED.raporSecenegi().tablo_filtre || {}; TABLO_ED.kapat(); } catch (e) { /* yoksay */ } }
      TABLO_ED = null;
    };
    tabloIste().then(function (y) {
      if (!y || KAPLAMA !== k) return;
      k.govde.innerHTML = "";
      TABLO_ED = M.ac(k.govde, {
        tablolar: y.tablolar, bina: kopya(B), cozumlu: !!y.cozumlu, raporSecimi: new Set(RAPOR_TABLOLAR), dosyaOnEki: B.baslik || "bina", baslangic: baslangic || undefined,
        csvIceri: secenek && secenek.csvIceri ? true : undefined,
        raporSecimiDegisti: function (s) { raporTablolariAyarla(s); },
        duzenle: function (yeni, degisiklikler, bilgi) {
          const geri = !!(bilgi && bilgi.geriAl);
          binaAyarla(yeni, { geriAl: true, etiket: geri ? "Tablo düzenlemesi geri alındı." : (degisiklikler.length + " tablo değişikliği modele uygulandı."), sessiz: true });
          tablolarTazeleGecikmeli(0);
          return true;
        },
      });
      olayYay("tablolar", { sayi: y.tablolar.length, cozumlu: !!y.cozumlu });
    }).catch(function (e) { if (KAPLAMA === k) hataNotu(k.govde, (e && e.message) || String(e), "Tablolar alınamadı"); });
  }
  // açık editörün tablolarını güncel modelden yeniden ister (model değişince; kısa gecikmeyle birleştirir)
  function tablolarTazeleGecikmeli(ms) {
    clearTimeout(tabloTazeleZ);
    tabloTazeleZ = setTimeout(function () {
      if (KAPLAMA.tur !== "tablolar" || !TABLO_ED) return;
      const ed = TABLO_ED;
      tabloIste().then(function (y) {
        if (!y || TABLO_ED !== ed) return;
        ed.guncelle({ tablolar: y.tablolar, bina: kopya(B), cozumlu: !!y.cozumlu, eski: !!(SON && sonEski && !y.cozumlu) });
      }).catch(function (e) { A.toast("Tablolar yenilenemedi: " + ((e && e.message) || e)); });
    }, ms == null ? 250 : ms);
  }

  // =====================================================================================================================
  // 🌡 Isı haritası: köprü "bina_alan" {cozum_kimligi, bina, durum, katsayilar?} → {alan}; MatrisIsi.ac(...). Çözüm yoksa önce çözer.
  // Durum: veri.durumlar + uygulanan kombinasyonlar + "zarf+" / "zarf-" (MatrisIsi alan.secenekler'den listeler).
  // =====================================================================================================================
  let ISI = null, isiDurum = null;
  function isiVarsayilanDurum(v) {
    if (isiDurum && ((v.durumlar && v.durumlar[isiDurum]) || (v.kombinasyonlar || []).some(function (k) { return k.ad === isiDurum && k.uygulandi; }) || /^zarf[+-]$/.test(isiDurum))) return isiDurum;
    const komb = (v.kombinasyonlar || []).filter(function (k) { return k.uygulandi && k.tur === "dayanim"; });
    const tercih = komb.filter(function (k) { return k.ad === "1.4G+1.6Q"; })[0] || komb[0];
    return tercih ? tercih.ad : (v.durumlar && v.durumlar.G ? "G" : Object.keys(v.durumlar || {})[0] || "G");
  }
  function alanIste(durum) {
    const v = SON.veri, g = { cozum_kimligi: cozumKimligi(), bina: SON.bina || kopya(B), durum: durum };
    if (durum === "G+Q" && !(v.durumlar && v.durumlar["G+Q"]) && !(v.kombinasyonlar || []).some(function (k) { return k.ad === "G+Q"; })) g.katsayilar = { G: 1, Q: 1 };
    return A.motorIstegi({ islem: "bina_alan", girdi: g }).then(function (y) {
      if (!y || y.hata || !y.alan) throw new Error(motorHatasi(y, "Isı haritası alanı gelmedi."));
      return y.alan;
    });
  }
  // ısı haritası FE kaydı → sahne anahtarı. Genel çözümde bina_no çubuk numarasıdır (FE türü kolon/kiriş/çapraz… olsa da);
  // panel/döşeme plak alanları kendi türleriyle gelir.
  function isiSahneAnahtari(k) {
    const v = V(), tur = k.tur;
    if (tur === "doseme" || tur === "panel") return { tur: tur, no: k.bina_no };
    if (v && v.model === "genel") return cubuktanSahne(+k.bina_no);
    return { tur: tur === "kolon" || tur === "kiris" ? tur : (tur || "cubuk"), no: k.bina_no };
  }
  // sahne seçimi → ısı haritasının başlangıç seçimi: genel çözümde çubuğun FE eleman numaraları (FE türü çubuk türüdür, "cubuk" değil)
  function isiSecimi(s) {
    const v = V();
    if (s && s.tur === "temel") return undefined;     // temel ısı haritasında radye/taban basıncı katmanıdır, eleman seçimi yok
    if (!s || !v || v.model !== "genel" || !v.ag) return s ? { tur: s.tur, no: s.no } : undefined;
    let cno = null;
    if (s.tur === "cubuk") cno = +s.no;
    else if (s.tur === "kolon" || s.tur === "kiris") { const r = kayitSahneden(s.tur, s.no); cno = r && r.cubuk != null ? +r.cubuk : null; }
    if (cno == null) return { tur: s.tur, no: s.no };
    const l = (v.ag.elemanlar || []).filter(function (e) { return e.cubuk === cno; }).map(function (e) { return e.no; });
    return l.length ? l : undefined;
  }
  function isiAc(hedef) {
    const M = modul("MatrisIsi");
    if (!M) { A.toast("Isı haritası modülü yüklenmedi."); return; }
    const k = kaplamaAc("isi", "Isı haritası", { genis: true });
    bekleNotu(k.govde, SON && !sonEski ? "Alanlar hesaplanıyor…" : "Isı haritası için önce model çözülüyor…");
    k.temizle = function () { if (ISI) { try { ISI.kapat(); } catch (e) { /* yoksay */ } } ISI = null; };
    cozumHazir().then(function (ok) {
      if (KAPLAMA !== k) return null;
      if (!ok || !SON || sonEski) throw new Error("Isı haritası için model çözülmeli; çözüm tamamlanmadı" + (sonCozumHatasi ? ": " + sonCozumHatasi : "."));
      const durum = isiVarsayilanDurum(SON.veri);
      bekleNotu(k.govde, "Alanlar hesaplanıyor (" + durum + ")…");
      return alanIste(durum).then(function (alan) {
        if (KAPLAMA !== k) return;
        isiDurum = durum;
        k.govde.innerHTML = "";
        const s = hedef || (D.secim[0] || null);
        ISI = M.ac(k.govde, {
          alan: alan, bina: SON.bina || B, secim: isiSecimi(s),
          olay: {
            elemanSec: function (no, kayit) {
              if (!kayit || kayit.bina_no == null) return;
              D.secim = [isiSahneAnahtari(kayit)];
              if (kayit.kat != null && B.katlar.some(function (x) { return x.no === kayit.kat; })) D.kat = kayit.kat;
              yenile();
            },
            kapat: function () { kaplamaKapat(); },
            durumSec: function (ad) {
              const g = ISI;
              alanIste(ad).then(function (a) { if (ISI === g) { isiDurum = ad; g.guncelle(a, SON.bina || B); } }, function (e) { A.toast(ad + ": " + ((e && e.message) || e)); });
            },
            tasarim: function (h) {
              if (!h || h.no == null) return;
              kaplamaKapat();
              D.sekme = "tasarim";
              if (ref.sonuc.querySelector(".bn-sekmeler")) sekmeCiz(); else sonucuCiz();
              cekmeceAc();
              // ısı haritası kaydı: FE elemanının türü ve bina_no'su (genel çözümde çubuk numarası; aks–kat çözümünde kolon/kiriş no)
              const r = !tasarimVar() ? null : V().model === "genel" ? dcKaydiCubuk(+h.no) : (h.tur === "kolon" || h.tur === "kiris") ? kayitSahneden(h.tur, +h.no) : null;
              if (r) tasarimSec(r.tur, r.no, true); else A.toast("Bu eleman için tasarım kaydı yok.");
            },
          },
        });
        // yayılı temelden (mütemadi / radye) açılınca zemin katmanı taban basıncıyla başlar (sağ tık "Isı haritasında incele")
        if (s && s.tur === "temel" && s.alt && alan.radye && ISI && typeof ISI.ayarla === "function") { try { ISI.ayarla({ radye: "p" }); } catch (e) { /* yoksay */ } }
        olayYay("isi", { durum: durum, eleman: (alan.elemanlar || []).length });
      });
    }).catch(function (e) { if (KAPLAMA === k) hataNotu(k.govde, (e && e.message) || String(e), "Isı haritası açılamadı"); });
  }

  // =====================================================================================================================
  // Proje dosyası (.matris = {tur: "matris-proje", surum, bina, gorunum, arac_yerlesimi}) — masaüstünde yerel dosya, web'de indirme/yükleme
  // =====================================================================================================================
  const PROJE_SURUM = 1;
  function projeNesnesi() {
    return { tur: "matris-proje", surum: PROJE_SURUM, uygulama: "Matris Öğren", kaydedildi: new Date().toISOString(), bina: kopya(B), gorunum: gorunum(),
      arac_yerlesimi: aracYon ? aracYon.yerlesim() : null };
  }
  function projeDosyaAdi() { return dosyaAdiTemiz(B && B.baslik ? B.baslik : "bina") + ".matris"; }
  function projeKaydet(farkli) {
    if (!B) return Promise.resolve(null);
    const metin = JSON.stringify(projeNesnesi(), null, 1), F = modul("MatrisDosya");
    if (!F) return dosyaKaydet(projeDosyaAdi(), metin, "matris");
    return F.kaydet(projeDosyaAdi(), metin, "matris", { farkli: !!farkli }).then(function (r) {
      if (r) { F.degisti(false); A.toast("Proje kaydedildi: " + (r.ad || projeDosyaAdi())); }
      return r;
    }, function (e) { A.toast("Proje kaydedilemedi: " + ((e && e.message) || e)); return null; });
  }
  // metin ya da nesne: .matris projesi ya da düz bina JSON'u (eski kayıtlar) kabul edilir
  function projeYukle(icerik, ad) {
    let p = icerik;
    if (typeof p === "string") {
      try { p = JSON.parse(p.charCodeAt(0) === 0xfeff ? p.slice(1) : p); } catch (e) { throw new Error((ad || "Dosya") + " JSON olarak okunamadı: " + e.message); }
    }
    if (!p || typeof p !== "object") throw new Error("Dosya bir proje ya da bina JSON'u değil.");
    let bina = p, gor = null, yer = null;
    if (p.tur === "matris-proje") {
      if (+p.surum > PROJE_SURUM) throw new Error("Bu proje daha yeni bir sürümle kaydedilmiş (" + p.surum + "); uygulamayı güncelleyin.");
      bina = p.bina; gor = p.gorunum || null; yer = p.arac_yerlesimi || null;
    }
    binayiAyarla(bina, "Açıldı: " + (ad || (bina && bina.baslik) || "proje"));
    if (gor) { try { gorunumAyarla(gor); } catch (e) { /* görünüm isteğe bağlı */ } }
    if (yer && aracYon) { try { aracYon.yerlesimYukle(aracGoc(yer)); } catch (e) { A.toast("Araç kutusu yerleşimi okunamadı: " + e.message); } }
    sablonSeciciAyarla("");
    return true;
  }
  function projeAc() {
    const F = modul("MatrisDosya");
    const yukle = function (r) {
      if (!r) return;
      try { projeYukle(r.icerik, r.ad); if (F) F.degisti(false); } catch (e) { A.toast(e.message); }
    };
    if (F) return F.ac(["matris", "json"]).then(yukle, function (e) { A.toast("Dosya açılamadı: " + ((e && e.message) || e)); });
    jsonAc();
    return Promise.resolve(null);
  }
  function projeYeni() {
    const F = modul("MatrisDosya");
    if (F && F.kirliMi && F.kirliMi() && !window.confirm("Kaydedilmemiş değişiklikler var. Yeni proje açılsın mı? (Geri al ile dönebilirsiniz.)")) return;
    binayiAyarla(YERLESIK_SABLON["betonarme-2kat-3x2"](), "Yeni proje (2 katlı betonarme şablon).");
    sablonSeciciAyarla("");
    if (F && F.yeni) F.yeni();
  }
  // Sahne görüntüsü (PNG; olmazsa SVG): hesaplanan stiller gömülür
  function sahneResmi() {
    const svg = ref.svg;
    if (!svg) return Promise.resolve(null);
    const kopyaSvg = svg.cloneNode(true), kaynaklar = svg.querySelectorAll("*"), hedefler_ = kopyaSvg.querySelectorAll("*");
    const OZ = ["fill", "fill-opacity", "stroke", "stroke-width", "stroke-opacity", "stroke-dasharray", "opacity", "font-size", "font-weight", "font-family", "paint-order", "text-anchor"];
    kaynaklar.forEach(function (el, i) {
      const cs = getComputedStyle(el), h = hedefler_[i];
      h.setAttribute("style", OZ.map(function (a) { return a + ":" + cs.getPropertyValue(a); }).join(";"));
    });
    const r = svg.getBoundingClientRect();
    kopyaSvg.setAttribute("xmlns", SVG_NS);
    kopyaSvg.setAttribute("width", Math.round(r.width)); kopyaSvg.setAttribute("height", Math.round(r.height));
    const arka = getComputedStyle(kok).getPropertyValue("--arka") || "#fff";
    const metin = new XMLSerializer().serializeToString(kopyaSvg).replace(/^<svg /, '<svg style="background:' + arka.trim() + '" ');
    const ad = dosyaAdiTemiz(B.baslik) + "_gorunum";
    return new Promise(function (coz_) {
      const img = new Image(), url = URL.createObjectURL(new Blob([metin], { type: "image/svg+xml" }));
      img.onload = function () {
        try {
          const cv = document.createElement("canvas"), o = 2;
          cv.width = Math.round(r.width * o); cv.height = Math.round(r.height * o);
          const cx = cv.getContext("2d"); cx.fillStyle = arka.trim() || "#fff"; cx.fillRect(0, 0, cv.width, cv.height); cx.drawImage(img, 0, 0, cv.width, cv.height);
          URL.revokeObjectURL(url);
          cv.toBlob(function (b) { coz_(b ? dosyaKaydet(ad + ".png", b, "png") : dosyaKaydet(ad + ".svg", metin, "svg")); }, "image/png");
        } catch (e) { URL.revokeObjectURL(url); coz_(dosyaKaydet(ad + ".svg", metin, "svg")); }
      };
      img.onerror = function () { URL.revokeObjectURL(url); coz_(dosyaKaydet(ad + ".svg", metin, "svg")); };
      img.src = url;
    });
  }

  // =====================================================================================================================
  // Yüzen araç kutuları (MatrisArac): komut kaydı, kısayollar (tek kaynak), bina_cizim.js için kancalar
  // =====================================================================================================================
  let aracYon = null;
  const ARAC_ANAHTAR = "bina.arac";
  const SONRAKI_ASAMA = " — Etkin değil: aks tabanlı çizim modülü (bina_cizim.js) yüklenmedi; uygulamayı yenileyin.";
  // aks tabanlı çizim / değiştirme komutları docs/bina_cizim.js'te bağlanır (MatrisBina.komutBagla); modül yoksa soluk ve ipucunda nedeni yazılı
  const SONRAKI = ["aks-ekle", "aks-sil", "aks-tasi", "aks-sistemi", "aks-gorunurluk", "cubuk-ciz", "hizli-cubuk", "hizli-capraz", "egik-cubuk", "makas", "besik-cerceve",
    "asik", "kren-yolu", "mesnet", "yuk-ata", "tasi", "dondur", "ayna", "dogrusal-dizi", "mafsal", "yalniz-cekme",
    "bol", "kesisimde-bol", "duzlemle-bol", "birlestir", "dugum-birlestir", "kesit-degistir", "aci"];
  const IKON_DUVAR = '<svg class="arac-ikon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
    '<path d="M3 20h18M3 9h18"/><path class="a n" d="M3 12.7h18M3 16.3h18M8 9v3.7M15 9v3.7M11.5 12.7v3.6M5 16.3V20M18 12.7v3.6M12 16.3V20"/><path class="t" d="M3 5h18"/></svg>';
  const IKON_IFC = '<svg class="arac-ikon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
    '<path d="M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15"/><path d="M12 3.5v11"/><path class="a" d="M7.8 10.3L12 14.5l4.2-4.2"/><path class="a n" d="M8 17.3h8"/></svg>';
  function katalogKaydi(id) { const M = modul("MatrisArac"); return M ? M.KATALOG.filter(function (x) { return x.id === id; })[0] || null : null; }
  // etkin(): model yoksa ya da iletişim kutusu/kaplama açıksa false (kısayollar da çalışmaz); calistir hataları bildirime
  function komutSar(id, v) {
    const t = Object.assign({}, typeof v === "function" ? { calistir: v } : v);
    const e = t.etkin, f = t.calistir, n = t.neden;
    t.etkin = function () { if (!B || modalAcik()) return false; try { return typeof e === "function" ? !!e() : e !== false; } catch (x) { return false; } };
    // devre dışı nedeni (sözleşme C8): sayfa durumu (model yok, pencere açık) önce, sonra komutun kendi nedeni (metin ya da işlev)
    t.neden = function () {
      if (!B) return "Bina sayfası hazırlanıyor.";
      if (modalAcik()) return "Önce açık pencereyi kapatın.";
      try { const m = typeof n === "function" ? n() : n; return m == null || m === "" ? null : String(m); } catch (x) { return null; }
    };
    if (typeof f === "function") t.calistir = function (olay, k) { try { return f(olay, k); } catch (x) { A.toast((x && x.message) || String(x)); return null; } };
    if (t.ipucu === undefined) { const kk = katalogKaydi(id); if (kk) t.ipucu = kk.ipucu; }
    return t;
  }
  // bina_cizim.js ve modüller: MatrisBina.komutBagla({id: fn | {calistir, etkin, secili, secenek, secenekSec, kisayol?, ipucu?}})
  function komutBagla(harita) {
    const M = modul("MatrisArac");
    if (!M) return false;
    const h = {};
    Object.keys(harita || {}).forEach(function (id) { h[id] = komutSar(id, harita[id]); });
    M.baglar(h);
    aracYenile();
    return true;
  }
  function aracYenile() { const M = modul("MatrisArac"); if (M && aracYon) { try { M.yenile(); } catch (e) { /* yoksay */ } } }
  // yüzen araç kutularını göster / gizle (☰, masaüstü "Araç kutuları"); sahne boşalan alana yeniden sığar
  function aracKatmaniGoster(g) {
    if (!ref.aracKatman) return;
    ref.aracKatman.hidden = !g;
    yerlesimUygula();
    if (B && kamera) sahneYenile();
  }
  // yüzen araç kutularının sahneden kapladığı paylar (SVG piksel = görünüm birimi; kamera sıfırdayken): {sol, ust, sag, alt}
  function aracPaylari() {
    const M = modul("MatrisArac"), sifir = { sol: 0, ust: 0, sag: 0, alt: 0 };
    if (!M || !aracYon || !M.kenarPaylari || !ref.aracKatman || ref.aracKatman.hidden || !ref.svg) return sifir;
    let p;
    try { p = M.kenarPaylari(); } catch (e) { return sifir; }
    const kr = ref.aracKatman.getBoundingClientRect(), sr = ref.svg.getBoundingClientRect();
    if (!kr.width || !sr.width) return sifir;
    // katman sahneye göre ötelenmiş olabilir (üst ipucu şeridi, tam ekran kenar boşlukları)
    return { sol: p.sol ? p.sol + Math.max(0, kr.left - sr.left) : 0, ust: p.ust ? p.ust + Math.max(0, kr.top - sr.top) : 0,
      sag: p.sag ? p.sag + Math.max(0, sr.right - kr.right) : 0, alt: p.alt ? p.alt + Math.max(0, sr.bottom - kr.bottom) : 0 };
  }
  function kipKomutu(arac, ek) { return Object.assign({ tur: "kip", secili: function () { return D.arac === arac; }, calistir: function () { aracSec(arac); yenile(); } }, ek || {}); }
  function sonucKomutu(sekme, kosul, kosulNeden) {
    return { secili: function () { return !!SON && D.sekme === sekme; }, etkin: function () { return !!SON && (!kosul || kosul()); }, calistir: function () { sonucSekmesiGit(sekme); },
      neden: function () { return !SON ? "Önce modeli çözün (Çöz ▶)." : kosul && !kosul() ? (kosulNeden || null) : null; } };
  }
  function aracKomutlari() {
    const h = {
      // Çizim (aks–kat modelinin araçları; bina_cizim.js aks tabanlı karşılıklarıyla yeniden bağlar)
      sec: kipKomutu("sec"),
      "hizli-kolon": kipKomutu("kolon", { ipucu: "Etkin katın aks kesişimine dokunun: kolon ekle/kaldır (alt ve üst kat kotu arasında)." }),
      "hizli-kiris": kipKomutu("kiris", { ipucu: "Etkin katta iki aks kesişimine art arda dokunun ya da birinden ötekine sürükleyin: kiriş. Arada kolon yoksa sürekli kiriş." }),
      "hizli-panel": kipKomutu("doseme", { ipucu: "Hücredeki + işaretine dokunun: dört aks kesişimi arasında döşeme." }),
      duvar: kipKomutu("duvar", { ad: "Duvar", ikon: IKON_DUVAR, grup_varsayilan: "cizim", kisayol: "W", ipucu: "Kirişe (genel modelde kiriş, bağ ya da diğer türdeki çubuğa) dokunun: duvar ekle/kaldır (duvar türü ve yüksekliği özellik panelinde)." }),
      // Aks (aks–kat modelinin mevcut karşılıkları)
      "aks-sihirbaz": { calistir: function () { sihirbazAc(); }, ipucu: "Aks aralıkları, kat sayısı ve yüksekliğiyle yeni aks–kat modeli kurar." },
      "aks-duzenle": { calistir: function () { panelGit("akslar"); }, ipucu: "Akslar ve katlar tablosu (özellik paneli): ad, konum, kot; elemanlar akslara bağlı taşınır." },
      "duzlem-yukari": { calistir: function () { duzlemGec(1); }, etkin: function () { return duzlemKomsuVar(1); }, neden: "Bu yönde başka düzlem yok." },
      "duzlem-asagi": { calistir: function () { duzlemGec(-1); }, etkin: function () { return duzlemKomsuVar(-1); }, neden: "Bu yönde başka düzlem yok." },
      // Düzenleme
      "geri-al": { calistir: function () { geriAl(); }, etkin: function () { return gecmis.geri.length > 0; }, neden: "Geri alınacak değişiklik yok." },
      yinele: { calistir: function () { ileriAl(); }, etkin: function () { return gecmis.ileri.length > 0; }, neden: "Yinelenecek (geri alınmış) değişiklik yok." },
      kopyala: { calistir: kopyala, etkin: function () { return kopyalanabilir().length > 0 && !metinSecili(); }, ipucu: "Seçili kolon, kiriş ve döşemeleri panoya alır.",
        neden: function () { return metinSecili() ? "Sayfada metin seçili: Ctrl+C metni kopyalar." : "Önce bir eleman seçin."; } },
      yapistir: { calistir: yapistir, etkin: function () { return !!PANO; }, ipucu: "Panodakileri etkin kata (“Tüm katlara uygula” işaretliyse bütün katlara) aynı akslarda yapıştırır; dolu yerler atlanır.",
        neden: "Pano boş: önce elemanları Kopyala ile alın." },
      sil: { calistir: function () { if (D.secim.length) secimiSil(); else { aracSec("sil"); yenile(); } }, ipucu: "Seçili elemanları siler; seçim yoksa Sil aracını açar (dokunulan eleman silinir)." },
      "ozellik-ata": { tur: "kip", calistir: firca, secili: function () { return !!D.firca; }, ipucu: "Kesit fırçası: seçili kolon/kirişin kesitini alır, dokunduğunuz elemanlara atar (Esc bırakır)." },
      // Ölçme
      "olc-temizle": { calistir: function () { if (olcum) olcum.temizle(true); }, etkin: function () { return !!olcum && (olcum.olcer.sonuclar.length > 0 || olcum.olcer.bekleyen.length > 0); },
        neden: "Silinecek ölçü yok." },
      // Görünüm
      "gor-3b": { tur: "kip", secili: function () { return kamera && kamera.gorunum === "3b"; }, calistir: function () { gorunumGit("3b"); } },
      "gor-plan": { tur: "kip", secili: function () { return kamera && kamera.gorunum === "plan"; }, calistir: function () { gorunumGit("plan"); }, ipucu: "Etkin kat düzleminde plan (kat çiplerinden ya da PgUp/PgDn ile değişir)." },
      "gor-on": { tur: "kip", secili: function () { return kamera && kamera.gorunum === "on"; }, calistir: function () { gorunumGit("on"); }, ipucu: "Önden (XZ) görünüş." },
      "gor-yan": { tur: "kip", secili: function () { return kamera && kamera.gorunum === "yan"; }, calistir: function () { gorunumGit("yan"); }, ipucu: "Yandan (YZ) görünüş." },
      "kat-suzgeci": { calistir: katSuzgeciAc, secili: function () { return !!D.katSuzgec; } },
      yalit: { calistir: function () { yalit(); }, etkin: function () { return D.secim.length > 0; }, neden: "Önce yalıtılacak elemanları seçin." },
      "hepsini-goster": { calistir: hepsiniGoster, etkin: suzgecVar, neden: "Gizlenen ya da yalıtılan eleman yok." },
      "tel-kafes": { secili: function () { return D.telKafes; }, calistir: function () { D.telKafes = !D.telKafes; sahneCiz(); olayYay("gorunum", gorunum()); } },
      etiketler: { secili: function () { return D.etiketler; }, calistir: function () { D.etiketler = !D.etiketler; sahneCiz(); olayYay("gorunum", gorunum()); } },
      izgara: { secili: function () { return D.izgara; }, calistir: function () { D.izgara = !D.izgara; sahneCiz(); olayYay("gorunum", gorunum()); } },
      // tek kaynak: F tam ekran (mevcut davranış korunur), Shift+F sığdır
      sigdir: { kisayol: "Shift+F", calistir: sigdir },
      "tam-ekran": { kisayol: "F", secili: function () { return D.tamEkran; }, calistir: tamEkranDegistir, ipucu: "Düzenleyiciyi tam ekran yapar; Esc ya da F ile çıkılır." },
      // Analiz
      coz: { calistir: function () { coz(); }, etkin: function () { return !D.cozuluyor; }, neden: "Çözüm sürüyor." },
      denetle: { calistir: modelDenetle },
      "yuk-durumlari": { calistir: function () { panelGit("yukler"); } },
      kombinasyonlar: { calistir: function () { panelGit("yukler"); }, ipucu: "Kombinasyon kümesi (TS 500 / ÇYTHYE + TBDY) Yükler sekmesinde; çözümden sonra her birleşim sonuç seçicilerinde." },
      "analiz-ayar": { calistir: function () { panelGit("deprem"); }, ipucu: "Çatlamış rijitlik, diyafram, periyot ve dışmerkezlik (Deprem sekmesi); çelik L_b (Bina sekmesi)." },
      kutuphane: { calistir: function () { panelGit("kutuphane"); }, secili: function () { return D.panelSekme === "kutuphane"; },
        ipucu: "Kütüphane (özellik paneli): malzemeler, bu binanın kesitleri, yeni kesit ve kesit fırçası, duvar türleri, hareketli yük sınıfları." },
      // Sonuç
      deforme: sonucKomutu("deforme"),
      diyagram: Object.assign(sonucKomutu("diyagram"), { secenek: function () { return D.diyagram; }, secenekSec: function (id) { D.diyagram = id; if (D.sekme === "diyagram" && SON) diyagramiCiz(); } }),
      "yuk-akisi": sonucKomutu("akis"),
      "tasarim-dc": sonucKomutu("tasarim", tasarimVar, "Bu çözümde tasarım kontrolü yok."),
      "isi-haritasi": { calistir: function () { isiAc(); }, etkin: function () { return !!modul("MatrisIsi"); }, secili: function () { return KAPLAMA.tur === "isi"; }, neden: "Isı haritası modülü yüklenmedi." },
      tablolar: { calistir: function () { tablolarAc(); }, etkin: function () { return !!modul("MatrisTablo"); }, neden: "Tablo editörü modülü yüklenmedi." },
      rapor: { calistir: function () { raporAc(); }, ipucu: "Statik hesap raporu (bütün parametreler, yönetmelik künyeleri, tablolar): önizleme, yazdır / PDF, HTML indir. Çözüm yoksa önce çözer." },
      ifc: { ad: "IFC dışa aktar", ikon: IKON_IFC, grup_varsayilan: "sonuc", tur: "eylem", calistir: function () { ifcAc(); }, etkin: function () { return !!modul("MatrisIFC"); }, neden: "IFC modülü yüklenmedi.",
        ipucu: "Modeli IFC4 (.ifc) olarak kaydeder: katlar, aks ızgaraları, elemanlar, malzeme ve kesitler, isteğe bağlı yapısal analiz modeli ve D/C." },
    };
    if (modul("MatrisOlcum")) Object.keys(OLCUM_KIP).forEach(function (id) { h[id] = kipKomutu(id); });
    SONRAKI.forEach(function (id) { const kk = katalogKaydi(id); h[id] = { calistir: function () {}, etkin: false, ipucu: (kk ? kk.ipucu : "") + SONRAKI_ASAMA, neden: "Aks tabanlı çizim modülü (bina_cizim.js) yüklenmedi; uygulamayı yenileyin." }; });
    return h;
  }
  // Bina sayfasının ilk yerleşimi (kayıtlı yerleşim yoksa): kutular kenar şeritlerinde (rıhtım), hepsi açık; dizi sırası önceliktir
  // (yer kalmayınca en düşük öncelikliler taşma çekmecesine gider ve yer açılınca kendiliğinden döner), sira şeritteki görünür sıra.
  // Katman genişliğinden bağımsız: küçük pencere ve tam ekran yalnız başka bir W × H'dir (MatrisArac.Duzen.rihtim).
  const ARAC_ONCELIK = ["k-cizim", "k-duzenleme", "k-gorunum", "k-analiz", "k-sonuc", "k-aks", "k-olcme", "k-degistirme", "k-uretec"];
  const ARAC_URETEC = ["makas", "besik-cerceve", "asik", "kren-yolu", "mesnet", "yuk-ata"];
  function binaVarsayilanYerlesim(M) {
    const grup = function (g, cikar) { return M.KATALOG.filter(function (k) { return k.grup === g && (!cikar || cikar.indexOf(k.id) < 0); }).map(function (k) { return k.id; }); };
    const kutu = function (id, ad, komutlar, ayar) {
      return Object.assign({ id: id, ad: ad, komutlar: komutlar, yon: "yatay", kucuk: true, saydamlik: 1, kilitli: false, gizli: false, katli: false, yer: "kenar", konum: null, kenar: "ust" }, ayar || {});
    };
    const cizim = grup("cizim", ARAC_URETEC), i = cizim.indexOf("hizli-panel");
    cizim.splice(i >= 0 ? i + 1 : cizim.length, 0, "duvar");
    return { surum: M.SURUM, ad: "bina", kutular: [
      kutu("k-cizim", "Çizim", cizim, { kenar: "sol", yon: "dikey", sira: 1 }),
      kutu("k-duzenleme", "Düzenleme", grup("duzenleme"), { kenar: "ust", sira: 1 }),
      kutu("k-gorunum", "Görünüm", grup("gorunum"), { kenar: "alt", sira: 1 }),
      kutu("k-analiz", "Analiz", grup("analiz"), { kenar: "alt", sira: 2 }),
      kutu("k-sonuc", "Sonuç", grup("sonuc").concat(["ifc"]), { kenar: "sag", yon: "dikey", sira: 1 }),
      kutu("k-aks", "Aks", grup("aks"), { kenar: "ust", sira: 2 }),
      kutu("k-olcme", "Ölçme", grup("olcme"), { kenar: "sag", yon: "dikey", sira: 2 }),
      kutu("k-degistirme", "Değiştirme", grup("degistirme"), { kenar: "sag", yon: "dikey", sira: 3 }),
      kutu("k-uretec", "Üreteç ve yük", ARAC_URETEC.slice(), { kenar: "sol", yon: "dikey", sira: 2 }),
    ] };
  }
  /**
   * Bina sayfasının sürüm 1 araç kutusu yerleşimi (surum < 2, ad "bina"): sürüm 1 varsayılanı Aks, Ölçme, Değiştirme ve Üreteç'i yer
   * kazanmak için katlı başlatıyordu (açılır); dar pencerede birleştirilmiş "Düzenleme ve aks" kutusu yeniden ikiye ayrılır; bilinen
   * kutular sürüm 2 öncelik sırasına dizilir (bilinmeyenler göreli sıralarıyla sonda). Genel sürüm geçişi (kenar şeritleri) sonra
   * MatrisArac'ta (Duzen.dogrula) yapılır. Girdi değişmez; uygulanmazsa girdinin kendisi döner.
   */
  function aracGoc(y) {
    if (!y || typeof y !== "object" || !Array.isArray(y.kutular) || !(+y.surum < 2) || y.ad !== "bina") return y;
    const M = modul("MatrisArac");
    const g = JSON.parse(JSON.stringify(y));
    g.kutular = g.kutular.filter(function (k) { return k && typeof k === "object"; });
    g.kutular.forEach(function (k) { if (["k-aks", "k-olcme", "k-degistirme", "k-uretec"].indexOf(k.id) >= 0) { k.katli = false; delete k.otoKatli; } });
    const aksG = M ? M.KATALOG.filter(function (k) { return k.grup === "aks"; }).map(function (k) { return k.id; }) : [];
    const dz = g.kutular.filter(function (k) { return k.id === "k-duzenleme"; })[0];
    if (dz && dz.ad === "Düzenleme ve aks" && Array.isArray(dz.komutlar) && aksG.length && aksG.every(function (c) { return dz.komutlar.indexOf(c) >= 0; }) &&
        !g.kutular.some(function (k) { return k.id === "k-aks"; })) {
      const aksK = Object.assign({}, dz, { id: "k-aks", ad: "Aks", komutlar: dz.komutlar.filter(function (c) { return aksG.indexOf(c) >= 0; }), kenar: "ust", katli: false, konum: null });
      dz.ad = "Düzenleme";
      dz.komutlar = dz.komutlar.filter(function (c) { return aksG.indexOf(c) < 0; });
      g.kutular.splice(g.kutular.indexOf(dz) + 1, 0, aksK);
    }
    const bilinen = g.kutular.filter(function (k) { return ARAC_ONCELIK.indexOf(k.id) >= 0; }).sort(function (a, b) { return ARAC_ONCELIK.indexOf(a.id) - ARAC_ONCELIK.indexOf(b.id); });
    g.kutular = bilinen.concat(g.kutular.filter(function (k) { return ARAC_ONCELIK.indexOf(k.id) < 0; }));
    return g;
  }
  function aracKur() {
    const M = modul("MatrisArac");
    if (!M || aracYon || !ref.aracKatman) return;
    M.katalogKaydet();
    komutBagla(aracKomutlari());
    let kayitli = null;
    try { kayitli = localStorage.getItem(ARAC_ANAHTAR); } catch (e) { kayitli = null; }
    // yerleşim değişince (kutu taşındı, katlandı, gizlendi) sahne kutuların bıraktığı alana yeniden sığar
    const sec = { anahtar: ARAC_ANAHTAR, kisayollar: true, olay: function (ad) { if (ad === "calistir") aracYenile(); else if ((ad === "yerlesim" || ad === "boyut") && B && kamera) sahneYenile(); },
      varsayilan: function () { return binaVarsayilanYerlesim(M); } };      // "Varsayılana dön" bina varsayılanına döner
    // araç kutuları eski sol araç çubuğunun (Seç, Kolon, Kiriş, Döşeme, Duvar, Sil, Kütüphane) bütün komutlarını taşır: çubuk gizlenir.
    // Sınıf varsayılan yerleşimden ve kurulumdan ÖNCE eklenir: genişlik ve ilk yerleşim kapsayıcının son boyuyla yapılır (sonradan
    // genişleyen katman alta çapalı kutuları üstteki kutuların üstüne itmesin)
    kok.classList.add("bn-arac-yonetimli");
    if (!kayitli) { sec.yerlesim = binaVarsayilanYerlesim(M); depoYaz("bina.arac.ek", { duvar: 1, ifc: 1 }); }
    else {
      // sürüm 1 yerleşimi: bina kutularına özgü geçiş (aracGoc), sonra MatrisArac genel geçişi; bozuk kayıt MatrisArac'ta varsayılana düşer
      try { const y0 = JSON.parse(kayitli), y1 = aracGoc(y0); if (y1 !== y0) sec.yerlesim = y1; } catch (e) { /* bozuk kayıt */ }
    }
    try { aracYon = M.kur(ref.aracKatman, sec); }
    catch (e) { aracYon = null; kok.classList.remove("bn-arac-yonetimli"); return; }
    yerlesimUygula();
    // devre dışı komut çalıştırılmak istenince nedeni bildirimle (araç kutusu düğmesi kendi balonunda gösterir)
    if (M.dinle) M.dinle(function (ad, v) {
      if (ad !== "reddedildi" || !v || v.kaynak === "dugme") return;
      A.toast("“" + (v.ad || v.id) + "” şu an kullanılamıyor" + (v.neden ? ": " + v.neden : "."));
    });
    // kataloğun dışındaki sayfa komutları (duvar, ifc) varsayılan kutulara bir kez eklenir (kullanıcı sonra çıkarırsa geri gelmez)
    const ek = depoOku("bina.arac.ek", {}) || {};
    [["duvar", "k-cizim", "hizli-panel"], ["ifc", "k-sonuc", "rapor"]].forEach(function (x) {
      if (ek[x[0]]) return;
      try {
        const y = aracYon.yerlesim(), var_ = y.kutular.some(function (k) { return k.komutlar.indexOf(x[0]) >= 0; }), kt = y.kutular.filter(function (k) { return k.id === x[1]; })[0];
        if (!var_ && kt) { const i = kt.komutlar.indexOf(x[2]); kt.komutlar.splice(i >= 0 ? i + 1 : kt.komutlar.length, 0, x[0]); aracYon.yerlesimYukle(y); }
        ek[x[0]] = 1;
      } catch (e) { /* yerleşim kilitli vb. */ }
    });
    depoYaz("bina.arac.ek", ek);
  }

  // =====================================================================================================================
  // Sağ tık / uzun basma: MatrisBilgi bağlam menüsü ve denetçi. Uzun basma tek kaynak: Cizim3B.jestler (MatrisBilgi'nin kendi uzun basması kapalı).
  // =====================================================================================================================
  let bilgiBag = null;
  const BAGLAM_KANCALARI = [];     // bina_cizim.js: fn(hedef, komutlar) → komutlar (bol, birlestir, mafsal, kesit-oner…)
  function baglamKomutlari(hedef) {
    const tur = hedef.tur, no = hedef.no, cubukMu = tur === "kolon" || tur === "kiris" || tur === "cubuk", yayili = tur === "temel" && !!hedef.alt;
    let k = {
      ozellikler: function () { if (!yayili) D.secim = [{ tur: tur, no: no }]; D.panelSekme = tur === "temel" ? "bina" : "nesne"; yenile(); panelAc(); },
      "isi-haritasi": { calistir: function () { isiAc(yayili ? { tur: tur, no: no, alt: hedef.alt } : { tur: tur, no: no }); }, etkin: !!modul("MatrisIsi") && tur !== "dugum" && (tur !== "temel" || !!hedef.alt),
        neden: !modul("MatrisIsi") ? "Isı haritası modülü yüklenmedi" : tur === "temel" ? "Tekil temelin taban basıncı Temel sekmesinde" : null },
      "yuk-akisi": { calistir: function () {
        if (!SON || sonEski) { A.toast("Yük akışı için önce modeli çözün."); return; }
        D.akisHedef = { tur: tur, no: no }; D.secim = [{ tur: tur, no: no }]; sonucSekmesiGit("akis"); sahneCiz();
      }, etkin: !!SON && !sonEski && ["doseme", "kiris", "kolon", "cubuk", "panel", "temel"].indexOf(tur) >= 0 && !yayili,
        neden: !SON || sonEski ? "Önce modeli çözün" : yayili ? "Mütemadi / radye temelin yük aktarımı Temel sekmesinde (taban basıncı haritası)" : "Bu eleman türü için yük akışı yok" },
      tasarim: { calistir: function () {
        if (tur === "temel") { sonucSekmesiGit("temel"); return; }
        sonucSekmesiGit("tasarim");
        const r = tasarimVar() ? kayitSahneden(tur, no) : null;
        if (r) tasarimSec(r.tur, r.no, true); else A.toast("Bu eleman için tasarım kaydı yok.");
      }, etkin: !!SON && !sonEski && (tur === "temel" || (tasarimVar() && !!kayitSahneden(tur, no))),
        ad: tur === "temel" ? "Temel sekmesinde göster" : undefined, neden: !SON || sonEski ? "Önce modeli çözün" : "Bu eleman için tasarım kaydı yok" },
      gizle: function () { gizle([{ tur: tur, no: no }]); },
      yalit: function () { yalit([{ tur: tur, no: no }]); },
    };
    if (["kolon", "kiris", "doseme", "cubuk", "panel", "dugum", "mesnet"].indexOf(tur) >= 0 && nesneBul(tur, no)) k.sil = function () { D.secim = [{ tur: tur, no: no }]; secimiSil(); };
    void cubukMu;
    BAGLAM_KANCALARI.forEach(function (f) { try { k = f(hedef, k) || k; } catch (e) { /* yoksay */ } });
    return k;
  }
  function baglamKancasi(f) { BAGLAM_KANCALARI.push(f); return function () { const i = BAGLAM_KANCALARI.indexOf(f); if (i >= 0) BAGLAM_KANCALARI.splice(i, 1); }; }
  function menuKatmani() { return D.tamEkran ? kok : document.body; }
  function bilgiSecenekleri() {
    return {
      bul: function (e) {
        if (e && e.type === "contextmenu" && (e.pointerType === "touch" || dokunmaSonu())) return null;   // dokunmatik: uzun basmayı Cizim3B işler
        return B ? hedefBul(e) : null;
      },
      bina: function () { return B; },
      veri: function () { return veriGuncel(); },
      komutlar: baglamKomutlari,
      secili: function () { return D.secim[0] ? { tur: D.secim[0].tur, no: D.secim[0].no } : null; },
      konum: function (h) {
        const el = ref.svg.querySelector('[data-tur="' + h.tur + '"][data-no="' + h.no + '"]');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
      },
      uzunBasma: false,
      denetci: function () { return denetciSecenekleri(); },
      get kapsayici() { return menuKatmani(); },
    };
  }
  // Denetçi seçenekleri: rapora ekle, çözüm eski mi, motor ayrıntısı (köprü bina_eleman_bilgi, sözleşme C5). Ayrıntı yalnız güncel
  // çözümde ve çubuk türü elemanlar için istenir; motor işlemi tanımıyorsa ("Bilinmeyen işlem") bir daha sorulmaz, sessizce yok sayılır.
  let MOTOR_BILGI = null;
  function denetciSecenekleri() {
    return { raporaEkle: denetciRaporaEkle, eski: !!(SON && sonEski), paketIste: motorAyrintisiIste };
  }
  function motorAyrintisiIste(h) {
    if (!h || !SON || sonEski || MOTOR_BILGI === false || ["cubuk", "kolon", "kiris"].indexOf(h.tur) < 0) return null;
    const kimlik = cozumKimligi();
    if (!kimlik) return null;
    return Promise.resolve(A.motorIstegi({ islem: "bina_eleman_bilgi", girdi: { cozum_kimligi: kimlik, tur: h.tur, no: h.no } })).then(function (y) {
      if (y && y.hata && /Bilinmeyen işlem/i.test(String(y.hata))) { MOTOR_BILGI = false; return null; }
      if (!y || y.hata) throw new Error(motorHatasi(y));
      MOTOR_BILGI = true;
      return cozumKimligi() === kimlik ? y.paket || null : null;
    });
  }
  let sonDokunma = 0;
  function dokunmaSonu() { return Date.now() - sonDokunma < 1500; }
  function bilgiKur() {
    const M = modul("MatrisBilgi");
    if (!M || bilgiBag || !ref.svg) return;
    ref.svg.addEventListener("pointerdown", function (e) { if (e.pointerType === "touch") sonDokunma = Date.now(); }, true);
    bilgiBag = M.bagla(ref.svg, bilgiSecenekleri());
    // açık denetçi pencereleri çözümle ve modelle birlikte tazelenir: yeni çözüm gelince güncel sonuçlar (motor ayrıntısı yeniden istenir),
    // model değişince son çözüm "eski" uyarısıyla (şablon / proje / yeni model yüklenince iğnelenmemiş pencereler binayiAyarla'da kapanır)
    const tazele = function () { try { M.tazele(B, SON ? SON.veri : null, { eski: !!(SON && sonEski) }); } catch (e) { /* yoksay */ } };
    dinle("cozum", tazele);
    dinle("model", tazele);
  }
  // Cizim3B uzun basma → bağlam menüsü (MatrisBilgi yoksa eski davranış: seç + özellik paneli)
  function uzunBasmaMenusu(p, e) {
    // önce dokunulan noktadaki öğe (sağ tıkla aynı yol: bütün katların elemanları, temeller); yoksa etkin katın vuruş hedefleri
    let hedef = null;
    if (e && e.clientX != null && document.elementFromPoint) {
      try { const el = document.elementFromPoint(e.clientX, e.clientY); if (el) hedef = hedefBul({ target: el, clientX: e.clientX, clientY: e.clientY }); } catch (x) { hedef = null; }
    }
    if (!hedef) {
      const h = C.vurus(hedefler, p[0], p[1]);
      if (h && h.kind === "nesne") hedef = { tur: h.nesne, no: h.no };
      else if (h && h.kind === "kesisim") { const c = kolonBul(h.aks, D.kat); if (c) hedef = { tur: "kolon", no: c.no }; }
      else if (h && h.kind === "hucre") { const d = dosemeBul(h.kose[0], D.kat); if (d) hedef = { tur: "doseme", no: d.no }; }
    }
    if (!hedef) return;
    const yayili = hedef.tur === "temel" && !!hedef.alt;
    const M = modul("MatrisBilgi");
    if (!M) { if (!yayili) D.secim = [{ tur: hedef.tur, no: hedef.no }]; D.panelSekme = hedef.tur === "temel" ? "bina" : "nesne"; yenile(); panelAc(); return; }
    if (!yayili) { D.secim = [{ tur: hedef.tur, no: hedef.no }]; yenile(); }
    M.menuAc({ x: e && e.clientX != null ? e.clientX : 0, y: e && e.clientY != null ? e.clientY : 0 },
      Object.assign({}, hedef, { bina: B, veri: veriGuncel(), komutlar: baglamKomutlari(hedef), kapsayici: menuKatmani(), donus: ref.svg,
        denetci: denetciSecenekleri() }));
    // parmak kalkınca tarayıcının ürettiği tek tıklama menü öğesini tetiklemesin
    const yut = function (ev) { ev.stopPropagation(); ev.preventDefault(); document.removeEventListener("click", yut, true); };
    document.addEventListener("click", yut, true);
    const kaldir = function () { setTimeout(function () { document.removeEventListener("click", yut, true); }, 450); document.removeEventListener("pointerup", kaldir, true); };
    document.addEventListener("pointerup", kaldir, true);
  }

  // =====================================================================================================================
  // Masaüstü: menü komutları (masaustu-komut) ve açılan dosyalar (masaustu-dosya-acildi). İşlenen olayda e.preventDefault().
  // =====================================================================================================================
  const BEKLEYEN_DOSYA = [];
  function binaSayfasiEtkin() { const s = document.getElementById("sayfa-bina"); return !!(s && s.classList.contains("aktif")); }
  function binaSayfasinaGec() { if (!binaSayfasiEtkin() && A.sayfaGoster) A.sayfaGoster("bina", true); }
  // masaüstü menüsü / panel düğmesi → araç kutusu komutu; devre dışıysa MatrisArac "reddedildi" yayar (nedenli bildirim aracKur'da)
  function aracCalistir(id) {
    const M = modul("MatrisArac"), k = M && M.komut(id);
    if (!k) return false;
    if (!M.bagliMi(k)) { A.toast("“" + k.ad + "” bu sayfada henüz bağlı değil."); return true; }
    M.calistir(id);
    return true;
  }
  // masaüstü komutu → işleyen; true dönerse olay işlendi
  const MASAUSTU_ARAC = {
    "eleman-kopyala": "kopyala", "eleman-yapistir": "yapistir", sil: "sil", tasi: "tasi", dondur: "dondur", ayna: "ayna", dizi: "dogrusal-dizi", "ozellik-ata": "ozellik-ata",
    mafsal: "mafsal", "yalniz-cekme": "yalniz-cekme", bol: "bol", "kesisimde-bol": "kesisimde-bol", birlestir: "birlestir", "dugum-birlestir": "dugum-birlestir",
    "gorunum-3b": "gor-3b", "gorunum-plan": "gor-plan", "gorunum-on": "gor-on", "gorunum-yan": "gor-yan", sigdir: "sigdir", "kat-suzgeci": "kat-suzgeci",
    yalit: "yalit", "tumunu-goster": "hepsini-goster", "tel-kafes": "tel-kafes", etiketler: "etiketler", izgara: "izgara",
    "secim-kipi": "sec", "cubuk-ciz": "cubuk-ciz", "hizli-cubuk": "hizli-cubuk", "kolon-ekle": "hizli-kolon", "kiris-ekle": "hizli-kiris", "capraz-ekle": "hizli-capraz",
    "doseme-ekle": "hizli-panel", "egik-cubuk": "egik-cubuk", "uretec-makas": "makas", "uretec-cerceve": "besik-cerceve", "uretec-asik": "asik", "uretec-kren": "kren-yolu",
    "mesnet-ata": "mesnet", "yuk-ata": "yuk-ata", "olc-uzaklik": "olc-uzaklik", "olc-aci": "olc-aci", "olc-alan": "olc-alan", "olc-kot": "olc-kot",
    "olc-koordinat": "olc-koordinat", "olc-temizle": "olc-temizle", "aks-hizli": "aks-sihirbaz", "aks-duzenle": "aks-duzenle", "aks-ekle": "aks-ekle", "aks-sil": "aks-sil",
    "aks-sistemi-ekle": "aks-sistemi", "aks-sistemleri": "aks-sistemi", "aks-sistemi-sec": "aks-gorunurluk", "aks-yukari": "duzlem-yukari", "aks-asagi": "duzlem-asagi",
    "yuk-akisi": "yuk-akisi", "sekil-degistirme": "deforme", "kesit-oner": "kesit-oner",
  };
  function masaustuKomut(d) {
    const k = d.komut, etkin = binaSayfasiEtkin();
    const sayfada = function (f) { binaSayfasinaGec(); if (!B) { A.toast("Bina sayfası hazırlanıyor; komutu yeniden deneyin."); return true; } f(); return true; };
    switch (k) {
      case "yeni": return sayfada(projeYeni);
      case "kaydet": case "farkli-kaydet": if (!B) return false; projeKaydet(k === "farkli-kaydet"); return true;
      case "ac": return sayfada(projeAc);
      case "json-iceri": return sayfada(projeAc);
      case "json-disari": if (!B) return false; dosyaKaydet(dosyaAdiTemiz(B.baslik) + ".json", JSON.stringify(B, null, 2), "json"); return true;
      case "ifc": return sayfada(ifcAc);
      case "csv": return sayfada(tablolarCsvKaydet);              // dışa aktar: bütün tablolar tek CSV (Türkçe yerel ayarlı hesap tabloları için ";" ayraç ve ondalık virgül)
      case "csv-iceri": return sayfada(function () { tablolarAc(undefined, { csvIceri: true }); });
      case "tablolar": return sayfada(function () { tablolarAc(); });
      case "yazdir":       // Bina sayfasında yazdır: statik rapor (uygulama arayüzü değil); başka sayfada yerleşik window.print
        if (!etkin || !B) return false;
        raporAc(); raporHazirOlunca(function () { raporPencere(true); });
        return true;
      case "kisayollar": if (!etkin || !B) return false; kisayolPenceresi(); return true;
      case "metraj": return sayfada(function () { tablolarAc("metraj_ozet"); });
      case "rapor": case "rapor-icerik": return sayfada(function () { raporAc(); });
      case "proje-bilgileri": return sayfada(function () { raporAc({ kunye: true }); });
      case "rapor-html": return sayfada(function () { raporAc(); raporHazirOlunca(function () { dosyaKaydet(RAPOR.dosya_adi, RAPOR.html, "html"); }); });
      case "rapor-pdf": return sayfada(function () { raporAc(); raporHazirOlunca(raporYazdir); });
      case "resim": return sayfada(sahneResmi);
      case "isi-haritasi": return sayfada(function () { isiAc(); });
      case "coz": return sayfada(function () { coz(); });
      case "tasarim-kontrol": case "betonarme": case "celik": return sayfada(function () { cozumHazir().then(function (ok) { if (ok) sonucSekmesiGit("tasarim"); }); });
      case "temel": return sayfada(function () { cozumHazir().then(function (ok) { if (ok) sonucSekmesiGit("temel"); }); });
      case "yuk-durumlari": case "kombinasyonlar": case "kar-ruzgar": return sayfada(function () { panelGit("yukler"); });
      case "deprem": return sayfada(function () { panelGit("deprem"); });
      case "kat-duzenle": return sayfada(function () { panelGit("akslar"); });
      case "sablon": return sayfada(function () { if (ref.sablon) ref.sablon.focus(); });
      case "sonuclari-temizle": return sayfada(function () { sonucuTemizle(); yenile(); });
      case "tam-ekran": return sayfada(tamEkranDegistir);
      case "secimi-birak": if (!etkin || !B) return false; D.secim = []; D.firca = null; D.kirisBas = null; yenile(); return true;
      case "geri-al": case "yinele": {
        const el = document.activeElement;
        if (!etkin || !B || (el && (el.isContentEditable || /^(INPUT|TEXTAREA)$/.test(el.tagName)))) return false;   // metin kutusunda yerleşik geri al
        if (k === "geri-al") geriAl(); else ileriAl();
        return true;
      }
      case "arac-kutulari": if (!ref.aracKatman) return false; aracKatmaniGoster(!!ref.aracKatman.hidden); return true;
      case "arac-ozellestir": if (!aracYon) return false; binaSayfasinaGec(); aracYon.ozellestir(true); return true;
      case "arac-varsayilan": if (!aracYon) return false; aracYon.varsayilanaDon(); return true;
      case "arac-disari": if (!aracYon) return false; aracYon.disaAktar(); return true;
      case "arac-iceri": if (!aracYon || !aracYon.iceAktar) return false; aracYon.iceAktar(); return true;
      case "yakalama": case "aks-yapisik": case "aks-balon": case "aks-olcu":      // aks araç seti: bina_cizim.js (MatrisBina.komutBagla ile)
        if (aracCalistir(k)) return true;
        A.toast("Bu komut aks tabanlı çizim modülüyle (bina_cizim.js) gelir; modül yüklenmedi, uygulamayı yenileyin."); return true;
      default:
        if (MASAUSTU_ARAC[k]) { if (!B) return false; binaSayfasinaGec(); return aracCalistir(MASAUSTU_ARAC[k]); }
        return false;
    }
  }
  // Bütün tabloları (bina_tablolar; Tablolar penceresiyle aynı istek) tek CSV dosyasına kaydeder
  function tablolarCsvKaydet() {
    // tablo_editoru.js CSV üreticisini iç yardımcılarında (MatrisTablo._ic) verir; doğrudan dışa açılırsa o kullanılır
    const M = modul("MatrisTablo"), csv = M && (typeof M.tumunuCsv === "function" ? M.tumunuCsv : M._ic && typeof M._ic.tumunuCsv === "function" ? M._ic.tumunuCsv : null);
    if (!csv) { A.toast("Tablo modülü yüklenmedi."); return Promise.resolve(null); }
    A.toast("Tablolar hazırlanıyor…");
    return tabloIste().then(function (y) {
      if (!y) return null;
      const metin = csv(y.tablolar, { ayirici: ";", ondalikVirgul: true });
      return dosyaKaydet(dosyaAdiTemiz(B.baslik) + "_tablolar.csv", metin, "csv").then(function (r) { if (r) A.toast(y.tablolar.length + " tablo CSV olarak kaydedildi."); return r; });
    }).catch(function (e) { A.toast("Tablolar alınamadı: " + ((e && e.message) || e)); return null; });
  }
  // Klavye kısayolları penceresi: araç kutusu komutlarının kısayolları (MatrisArac.kisayollar, tek kaynak) + sayfa tuşları; "?" ya da
  // masaüstü menüsü (kisayollar). Araç kutusu yoksa eski araç çubuğu kısayolları.
  // araç kutusu modülü (MatrisArac) yüklenmediyse sayfa tuşları (C22 içeriğiyle aynı)
  const SAYFA_TUSLARI_YEREL = [["Esc", "Kipten çık, seçimi ya da yarım çizimi / ölçümü bırak; tam ekrandan çık", "sayfa"],
    ["Shift+F10", "Seçili elemanın bağlam (sağ tık) menüsü", "sayfa"], ["Enter", "Bağlam menüsünde: Bilgi", "sayfa"], ["?", "Kısayol listesini aç", "sayfa"],
    ["PgUp", "Düzlem yukarı: bir üst Z aksı ya da sonraki cephe aksı (aks–kat çiziminde üst kat)", "aks"], ["PgDn", "Düzlem aşağı", "aks"],
    ["F", "Tam ekran (Esc ya da F ile çıkılır)", "gorunum"], ["Shift+F", "Modeli sığdır", "gorunum"], ["Ctrl+Shift+Z", "Yinele", "duzenleme"],
    ["Backspace", "Seçileni sil (seçim yoksa Sil aracı)", "duzenleme"]].map(function (x) { return { kisayol: x[0], ad: x[1], grup: x[2] }; });
  function kisayolPenceresi() {
    const M = modul("MatrisArac"), gruplar = [], grupAd = {};
    const ekle = function (grup, kisayol, ad) {
      if (!grupAd[grup]) { grupAd[grup] = []; gruplar.push(grup); }
      if (!grupAd[grup].some(function (x) { return x[0] === kisayol; })) grupAd[grup].push([kisayol, ad]);
    };
    const gAd = {}; ((M && M.GRUPLAR) || []).forEach(function (g) { gAd[g.id] = g.ad; });
    const var_ = {};
    if (M && aracYon) {
      M.kisayollar().forEach(function (k) { const kk = M.komut(k.id); var_[k.kisayol] = 1; ekle(gAd[kk && kk.grup] || "Diğer", k.kisayol, k.ad); });
    } else {
      [["S", "Seç"], ["K", "Kolon"], ["R", "Kiriş"], ["D", "Döşeme"], ["W", "Duvar"], ["Del", "Sil"], ["Ctrl+Z", "Geri al"], ["Ctrl+Y", "Yinele"], ["Ctrl+Enter", "Çöz"], ["F", "Tam ekran"]]
        .forEach(function (x) { var_[x[0]] = 1; ekle("Araç çubuğu", x[0], x[1]); });
    }
    // sayfa tuşları tek listeden (MatrisArac.SAYFA_TUSLARI, sözleşme C22; app.js Yardım tablosu ve masaüstü penceresiyle aynı satırlar):
    // başlık grubun adı ("sayfa" → "Sayfa"); kayıttan (komut kısayolu) zaten listelenen tuş atlanır
    const SAYFA = (M && M.SAYFA_TUSLARI) || SAYFA_TUSLARI_YEREL;
    const grupAdi = function (g) { return (M && M.grupAdi) ? M.grupAdi(g) : (gAd[g] || (g === "sayfa" ? "Sayfa" : g)); };
    SAYFA.forEach(function (x) { if (!var_[x.kisayol]) ekle(grupAdi(x.grup), x.kisayol, x.ad); });
    const k = kaplamaAc("kisayollar", "Klavye kısayolları", { kucuk: true });
    k.govde.innerHTML = '<p class="not">Yazı alanı ve iletişim kutusu açıkken kısayollar çalışmaz. Araç kutusu düğmesinin üstünde bekleyince de kısayolu görünür.</p>' +
      gruplar.map(function (g) {
        return "<h3>" + kacis(g) + '</h3><table class="se-sonuc-tablo bn-kisayol-tablo"><tbody>' + grupAd[g].map(function (x) {
          return '<tr><th scope="row"><kbd class="arac-kbd">' + kacis(x[0]) + "</kbd></th><td>" + kacis(x[1]) + "</td></tr>";
        }).join("") + "</tbody></table>";
      }).join("");
    return k;
  }
  // rapor üretimi bitince (ya da hazırsa hemen) fn
  function raporHazirOlunca(fn) {
    if (RAPOR && RAPOR.anahtar === raporAnahtari()) { fn(); return; }
    const kaldir = dinle("rapor", function () { kaldir(); fn(); });
    setTimeout(kaldir, 180000);
  }
  function masaustuDosya(d) {
    if (!d || typeof d.icerik !== "string") return false;
    if (!B) { BEKLEYEN_DOSYA.push(d); binaSayfasinaGec(); return true; }
    binaSayfasinaGec();
    try {
      projeYukle(d.icerik, d.ad);
      const F = modul("MatrisDosya"); if (F) F.degisti(!!d.kurtarma);
    } catch (e) { A.toast(e.message); }
    return true;
  }
  function masaustuBagla() {
    window.addEventListener("masaustu-komut", function (e) {
      const d = e.detail || {};
      let islendi = false;
      try { islendi = masaustuKomut(d); } catch (x) { A.toast((x && x.message) || String(x)); islendi = true; }
      if (islendi) e.preventDefault();
    });
    window.addEventListener("masaustu-dosya-acildi", function (e) { if (masaustuDosya(e.detail)) e.preventDefault(); });
    const F = modul("MatrisDosya");
    if (F && F.projeKaynagi) F.projeKaynagi(function () { return B ? { ad: projeDosyaAdi(), icerik: JSON.stringify(projeNesnesi(), null, 1) } : null; });
  }
  masaustuBagla();     // betik yüklenir yüklenmez (dosyalar sayfa "load"undan sonra gelir; bina henüz başlamadıysa kuyruğa alınır)
  function bekleyenDosyalariAc() {
    const F = modul("MatrisDosya");
    const d0 = F && F.bekleyenDosya ? F.bekleyenDosya() : null;
    if (d0) BEKLEYEN_DOSYA.push(d0);
    while (BEKLEYEN_DOSYA.length) masaustuDosya(BEKLEYEN_DOSYA.shift());
  }

  // =====================================================================================================================
  // window.MatrisBina — dar iç API (bina_cizim.js ve modüller için). Bina henüz başlamadıysa okuyucular null döner; hazir() / "hazir" olayı.
  // =====================================================================================================================
  let hazirMiB = false;
  window.MatrisBina = Object.freeze({
    surum: 2,
    hazir: function () { return hazirMiB; },
    bina: function () { return B; },                                  // canlı nesne: salt okunur kabul edin; değiştirmek için binaAyarla
    binaAyarla: function (yeni, sec) { return binaAyarla(yeni, sec); },
    veri: function () { return veriGuncel(); },                        // güncel çözüm verisi (model çözümden sonra değiştiyse null)
    cozumEski: function () { return !!(SON && sonEski); },
    cozumKimligi: cozumKimligi,
    coz: function () { return coz(); },                               // Promise<bool>
    yenile: function () { if (B) yenile(); },
    secim: secim,
    seciliAyarla: seciliAyarla,
    gorunum: function () { return B ? gorunum() : null; },
    gorunumAyarla: gorunumAyarla,
    sahne: function () { return ref.svg || null; },
    izdusum: izdusum,                                                  // {P, P3, T, bakis, s, W, H, gorunum, kat, bina, alan} (son çizim; alan: sığdırma dikdörtgeni, svg px)
    // bina_cizim.js kancaları
    kip: function () { return D.arac; },
    kipAyarla: function (id) { aracSec(id); if (B) yenile(); },
    kipKaydet: kipKaydet,
    katmanKaydet: katmanKaydet,
    katmanTazele: katmanTazele,
    komutBagla: komutBagla,
    baglamKancasi: baglamKancasi,
    hedefBul: hedefBul,
    dinle: dinle,
    kaplamaAc: function (tur, baslik, sec) { return kaplamaAc(tur, baslik, sec); },
    kaplamaKapat: kaplamaKapat,
    toast: function (m) { A.toast(m); },
    // çıktılar
    raporAc: raporAc, tablolarAc: tablolarAc, isiAc: isiAc, ifcAc: ifcAc, ifcUret: ifcUret,
    projeNesnesi: function () { return B ? projeNesnesi() : null; }, projeYukle: projeYukle, projeKaydet: projeKaydet,
    // §19 aks tabanlı modelleme (docs/bina_cizim.js kullanır)
    s3Var: function (b) { return s3Var(b); },                         // genel model mi (sözleşme C1; b verilmezse etkin bina)
    aksKatModu: function () { return aksKatModu(); },                 // aks–kat modeli ve etkin kat düzlemi: Kolon/Kiriş/Döşeme aks–kat elemanı ekler
    duzlem: function () { return B ? aksGorunumu() : null; },         // {tur: "plan"|"cephe"|"3b", z?, x?, y?} (MatrisAks görünümü)
    duzlemSec: function (tur, ad) { if (B) duzlemSec(tur, ad); },     // tur: "z" | "x" | "y"
    duzlemGec: function (adim) { if (B) duzlemGec(adim); },
    duzlemKomsuVar: function (adim) { return !!B && duzlemKomsuVar(adim); },
    zAkslari: function () { return B ? zAkslari() : []; },
    refKoordinat: function (ref) { return refP(ref); },              // REF → [X, Y, Z] | null (önbellekli)
    geometri: function () { return olcumGeo(); },                      // MatrisOlcum.geometri (önbellekli; yakalama)
    kesitBoyut: function (ad) { return B ? kesitBoyut(ad) : null; },
    kutuphane: function () { return KUT; },
    tumKatlar: function () { return !!D.tumKatlar; },
    pano: function () { return PANO ? kopya(PANO) : null; },
    ayar: function () { return { aksOlcu: D.aksOlcu, aksBalon: D.aksBalon, izgara: D.izgara, etiketler: D.etiketler, balonR: aksBalonR() }; },
    ayarla: function (o) { o = o || {}; ["aksOlcu", "aksBalon"].forEach(function (k) { if (o[k] != null) D[k] = !!o[k]; }); if (B) sahneYenile(); },
    ipucuYenile: function () { ipucuYaz(); },
    aracYenile: function () { aracYenile(); },
    sahneYenile: function () { if (B) sahneYenile(); },
    motorS3: function () { return motorS3Yokla(); },                  // Promise<bool>: köprüde genel model ve bina_kesit_oner var mı
    pxOlcek: function () { return pxOlcek(); },
    firca: function () { if (B) firca(); },                          // kesit fırçası (aks–kat; seçili kolon/kirişin kesiti)
  });

  // ---------- Başlatma ----------
  let basladi = false, sonGenislik = 0;
  // Bina sayfası etkin mi: gövdeye sınıf (geniş yerleşim: içerik pencere genişliğinin tamamını kullanır); sayfadan çıkınca tam ekran kapanır
  function sayfaIzle() {
    const sayfa = document.getElementById("sayfa-bina");
    if (!sayfa) return;
    const uygula = function () {
      const aktif = sayfa.classList.contains("aktif");
      document.body.classList.toggle("bn-sayfa", aktif);
      if (!aktif && D.tamEkran) tamEkranKapat();
      if (aktif && basladi) requestAnimationFrame(function () { boyutDegisti(false); });
    };
    uygula();
    if (typeof MutationObserver === "function") new MutationObserver(uygula).observe(sayfa, { attributes: true, attributeFilter: ["class"] });
  }
  function boyutIzle() {
    // SVG kutusu: genişlik (normal) ya da her iki boyut (tam ekran: çekmece, yön değişimi) değişince yeniden ölç
    let yon = window.innerWidth > window.innerHeight, bek = 0, sonPencere = [window.innerWidth, window.innerHeight];
    const yeniden = function (sigdir) {
      cancelAnimationFrame(bek);
      bek = requestAnimationFrame(function () {
        const y = window.innerWidth > window.innerHeight;
        boyutDegisti(sigdir || y !== yon);
        yon = y;
        if (D.tamEkran) { cekmeceUygula(); yuzenUygula(); }
        ayiracGuncelle();
      });
    };
    if (typeof ResizeObserver === "function") {
      let sonW = 0, sonH = 0;
      new ResizeObserver(function () {
        const w = ref.svgKutu.clientWidth, h = ref.svgKutu.clientHeight;
        if (!w) return;
        if (Math.abs(w - sonW) < 2 && (!D.tamEkran || Math.abs(h - sonH) < 2)) return;
        sonW = w; sonH = h;
        yeniden(false);
      }).observe(ref.svgKutu);
    }
    window.addEventListener("resize", function () {
      const p = [window.innerWidth, window.innerHeight];
      if (p[0] === sonPencere[0] && p[1] === sonPencere[1]) return;
      sonPencere = p;
      yeniden(false);
    });
    window.addEventListener("orientationchange", function () { yeniden(true); });
    document.addEventListener("fullscreenchange", tamEkranOlayi);
    document.addEventListener("webkitfullscreenchange", tamEkranOlayi);
  }
  function baslat() {
    iskeletKur();
    sablonListesi();
    yerlesimUygula();
    sahneBoyutla();
    jestleriKur();
    hoverKur();
    olaylariBagla();
    cekmeceJesti();
    ayiraclariKur();
    yuzenJesti();
    boyutIzle();
    const taslak = taslakOku();
    let yuklendi = false;
    if (taslak) { try { B = binaYukle(taslak); yuklendi = true; } catch (e) { yuklendi = false; } }
    if (!yuklendi) { B = YERLESIK_SABLON["betonarme-2kat-3x2"](); sablonSecili = "betonarme-2kat-3x2"; }
    zKatSenkron(B);
    sonAnlik = anlikGoruntu();
    D.kat = Math.min(Math.max(1, ustKat()), D.kat);
    olcumKur();
    aracKur();
    bilgiKur();
    yenile();
    kutuphaneyiAl();
    sablonlariAl();
    hashKontrol();
    hazirMiB = true;
    olayYay("hazir", window.MatrisBina);
    try { window.dispatchEvent(new CustomEvent("matris-bina-hazir", { detail: window.MatrisBina })); } catch (e) { /* eski tarayıcı */ }
    bekleyenDosyalariAc();
  }
  function acilis() {
    const ilk = function () { basladi = true; sonGenislik = kok.clientWidth; baslat(); sayfaIzle(); };
    if (typeof ResizeObserver !== "function") { ilk(); return; }
    let bekleyen = 0;
    new ResizeObserver(function () {
      const w = kok.clientWidth;
      if (!w) return;
      if (!basladi) { ilk(); return; }
      if (Math.abs(w - sonGenislik) < 24) return;
      sonGenislik = w;
      cancelAnimationFrame(bekleyen);
      bekleyen = requestAnimationFrame(function () { sahneBoyutla(); sahneCiz(); sonucBoyutlari(); if (D.panelSekme === "deprem") onizlemeCiz(); });
    }).observe(kok);
  }
  acilis();
})();
