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
        if (x.duvar && k.no < ustKat()) G += duvarW(x.duvar) * Math.max(0, katH(k.no + 1) - o.h) * L;
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
    aracKapali: false, panelKapali: false, tamEkran: false, gercekTam: false, cekmeceH: 0, cekmeceKapali: true, temelHarita: "p", temelSecim: null,
  };
  (function () { try { const y = JSON.parse(localStorage.getItem(YERLESIM_ANAHTAR) || "{}") || {}; D.aracKapali = !!y.arac; D.panelKapali = !!y.panel; D.cekmeceH = +y.cekmece || 0; } catch (e) { /* depolama yok */ } })();
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
      return { tip: "profil", ad: ad, profil: k.profil, b: p.b / 1000, h: p.h / 1000, A: p.A / 1e4, Iy: p.Iz / 1e8, Iz: p.Iy / 1e8, J: (p.It || 10) / 1e8, g: p.g / 100, malzeme: k.malzeme, celik: true };
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
    return b;
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
    if (!kamera) kamera = new C.Kamera(w, h); else kamera.boyut(w, h);
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
    const arac = dar ? (ref.arac.offsetHeight || 48) + 10 : 0;
    // sayfa başından sahneye kadar olan pay (başlık satırı dahil): açılışta bütün düzenleyici kaydırmadan görünsün
    const ustPay = Math.max(ust + serit, ref.svgKutu.getBoundingClientRect().top + (window.scrollY || 0));
    const kalan = Math.floor(vh - nav - ustPay - alt - arac - 14);
    if (vh < 520) return Math.max(220, Math.floor(vh - nav - alt - 16));          // yatay telefon: sahne görünüme sığsın (üst çubuk kayar)
    if (dar) return Math.round(Math.max(280, Math.min(kalan, w * 1.35)));
    return Math.max(380, kalan);
  }
  // ---------- Yerleşim: daraltılabilir araç çubuğu / özellik paneli, tam ekran, sonuç çekmecesi ----------
  function yerlesimKaydet() {
    try { localStorage.setItem(YERLESIM_ANAHTAR, JSON.stringify({ arac: D.aracKapali, panel: D.panelKapali, cekmece: D.cekmeceH })); } catch (e) { /* depolama yok */ }
  }
  function yerlesimUygula() {
    kok.classList.toggle("bn-arac-kapali", D.aracKapali);
    kok.classList.toggle("bn-panel-kapali", D.panelKapali);
    if (ref.aracAc) { ref.aracAc.setAttribute("aria-pressed", String(!D.aracKapali)); ref.aracAc.title = D.aracKapali ? "Araç çubuğunu aç" : "Araç çubuğunu daralt"; ref.aracAc.setAttribute("aria-label", ref.aracAc.title); }
    if (ref.panelAc) { ref.panelAc.setAttribute("aria-pressed", String(!D.panelKapali)); ref.panelAc.title = D.panelKapali ? "Özellik panelini aç" : "Özellik panelini daralt"; ref.panelAc.setAttribute("aria-label", ref.panelAc.title); }
    if (ref.tam) { ref.tam.setAttribute("aria-pressed", String(D.tamEkran)); ref.tam.textContent = D.tamEkran ? "✕" : "⛶"; ref.tam.title = D.tamEkran ? "Tam ekrandan çık (Esc, F)" : "Tam ekran (F)"; ref.tam.setAttribute("aria-label", D.tamEkran ? "Tam ekrandan çık" : "Tam ekran"); }
    yerlesimKaydet();
    boyutDegisti(false);
  }
  // Boyut değişince sahneyi yeniden ölç ve çiz; sigdir: kamerayı sıfırla (bina yeniden sığdırılır; yön değişimi, tam ekrana giriş/çıkış)
  function boyutDegisti(sigdir) {
    if (!B || !kamera) return;
    const d = sahneBoyutla();
    if (sigdir) kamera.sifirla();
    if (d || sigdir) sahneYenile();
  }
  function tamEkranOgesi() { return document.fullscreenElement || document.webkitFullscreenElement || null; }
  function tamEkranDegistir() { if (D.tamEkran) tamEkranKapat(); else tamEkranAc(); }
  // Tam ekran: Fullscreen API (webkit önekli dahil) + her durumda "sahte tam ekran" düzeni (sabit konumlu, görünümü kaplayan kip;
  // üst başlık ve alt gezinti gizli). API yoksa (iPhone Safari) ya da reddedilirse yalnız sahte kip kalır.
  function tamEkranAc() {
    if (D.tamEkran) return;
    D.tamEkran = true; D.gercekTam = false;
    kok.classList.add("bn-tam"); document.body.classList.add("bn-tam-ekran");
    const el = document.documentElement, f = el.requestFullscreen || el.webkitRequestFullscreen;
    kok.dataset.tamKip = f ? "api" : "sahte";
    if (f) {
      try {
        const p = f.call(el, { navigationUI: "hide" });
        if (p && typeof p.then === "function") p.then(function () { D.gercekTam = !!tamEkranOgesi(); }, function () { D.gercekTam = false; kok.dataset.tamKip = "sahte"; });
        else D.gercekTam = !!tamEkranOgesi();
      } catch (e) { D.gercekTam = false; kok.dataset.tamKip = "sahte"; }
    }
    cekmeceUygula();
    yerlesimUygula();
    requestAnimationFrame(function () { boyutDegisti(true); });
  }
  function tamEkranKapat() {
    if (!D.tamEkran) return;
    D.tamEkran = false;
    const gercek = tamEkranOgesi();
    D.gercekTam = false;
    if (gercek) { const f = document.exitFullscreen || document.webkitExitFullscreen; try { const p = f && f.call(document); if (p && p.catch) p.catch(function () {}); } catch (e) { /* yoksay */ } }
    kok.classList.remove("bn-tam"); document.body.classList.remove("bn-tam-ekran");
    delete kok.dataset.tamKip;
    ref.cekmece.style.height = "";
    ref.cekmece.classList.remove("kapali");
    yerlesimUygula();
    boyutDegisti(true);
    sonucBoyutlari();
  }
  function tamEkranOlayi() {
    if (tamEkranOgesi()) { D.gercekTam = true; return; }
    if (D.gercekTam) { D.gercekTam = false; tamEkranKapat(); }   // tarayıcının kendi Esc'i ya da sistem hareketiyle çıkış
  }
  // Çekmece (tam ekran): hesap hattı + sonuç sekmeleri; tutamak sürüklenerek yükseklik, dokunarak aç/kapat
  function cekmeceMin() { return Math.round((ref.cekmeceTutamak.offsetHeight || 22) + (kok.querySelector(".bn-hat-kutu").offsetHeight || 48) + 12); }
  function cekmeceUygula() {
    if (!D.tamEkran) return;
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
      if (!D.tamEkran) return;
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
      if (!D.tamEkran) return;
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
  // Aks çizgisi boyunca kat 1 kolonlarının uç konumları (yon "x": y aksı üzerinde X'ler; "y": x aksı üzerinde Y'ler)
  function aksKolonUclari(yon, ad) {
    const l = B.kolonlar.filter(function (c) { return c.kat === 1 && c.aks[yon === "x" ? 1 : 0] === ad; })
      .map(function (c) { return yon === "x" ? aksX(c.aks[0]) : aksY(c.aks[1]); }).filter(function (v) { return v != null; });
    return l.length >= 2 ? [Math.min.apply(null, l), Math.max.apply(null, l)] : null;
  }
  // Mütemadi temel kirişleri: yon "x" → X doğrultusunda, y akslarında (1, 2, …); "y" → Y doğrultusunda, x akslarında (A, B, …); uç kolondan "tasma" kadar konsol
  function temelKirisleri(tasmali) {
    const t = B.temeller, s = t.surekli || TEMEL_VARS.surekli, l = [];
    const ekle = function (yon, a) {
      if (!temelSecili(a.ad)) return;
      const u = aksKolonUclari(yon, a.ad);
      if (!u) return;
      const ts = tasmali === false ? 0 : +s.tasma || 0;
      l.push({ yon: yon, aks: a.ad, konum: +a.konum, bas: u[0] - ts, son: u[1] + ts });
    };
    if (s.yon !== "y") B.akslar.y.forEach(function (a) { ekle("x", a); });
    if (s.yon !== "x") B.akslar.x.forEach(function (a) { ekle("y", a); });
    return l;
  }
  function radyeSinir() {
    const r = B.temeller.radye || TEMEL_VARS.radye, ts = +r.tasma || 0;
    const xs = B.akslar.x.map(function (a) { return +a.konum; }), ys = B.akslar.y.map(function (a) { return +a.konum; });
    if (!xs.length || !ys.length) return null;
    return { x0: Math.min.apply(null, xs) - ts, x1: Math.max.apply(null, xs) + ts, y0: Math.min.apply(null, ys) - ts, y1: Math.max.apply(null, ys) + ts };
  }
  // Temelleri sahneye ekler (tekil / mütemadi ters T / radye plak + kirişli radye kirişleri); temel planında ölçü etiketleri
  function temelleriCiz(sahne, T, b, P, s, kat, hafif, plan) {
    const t = B.temeller, z0 = katKot(0) || 0, hay = kat !== 0 ? " b3-hayalet" : "", tip = t.tip;
    const kol1 = B.kolonlar.filter(function (c) { return c.kat === 1 && aksX(c.aks[0]) != null && aksY(c.aks[1]) != null; });
    const etiket = function (X, Y, Z, metin) { const p = P(X, Y, Z); sahne.ekle(1e9, C.metin(p[0], p[1] + 4, metin, "b3-temel-t", "middle"), 2); };
    const serit = function (yon, konum, a, bb, gen, zAlt, zUst, sinif, ek) {
      const p1 = yon === "x" ? [a, konum] : [konum, a], p2 = yon === "x" ? [bb, konum] : [konum, bb], zm = (zAlt + zUst) / 2;
      C.prizma(sahne, T, b, [p1[0], p1[1], zm], [p2[0], p2[1], zm], yon === "x" ? [0, gen / 2, 0] : [gen / 2, 0, 0], [0, 0, (zUst - zAlt) / 2], sinif, ek, 1);
      if (kat === 0) hedefler.push({ tur: "dogru", a: P(p1[0], p1[1], zUst), b: P(p2[0], p2[1], zUst), r: 12 * s, kind: "temel" });
    };
    if (tip === "surekli") {
      const sk = t.surekli || TEMEL_VARS.surekli, zt = z0 - sk.h_govde, hg = Math.max(0, sk.h_govde - sk.h_tabla);
      temelKirisleri().forEach(function (k) {
        const ek = ' data-tur="temel-kirisi" data-aks="' + kacis(k.aks) + '" data-yon="' + k.yon + '"';
        if (sk.h_tabla > 0) serit(k.yon, k.konum, k.bas, k.son, sk.B, zt, zt + sk.h_tabla, "b3-temel b3-temel-tabla" + hay, ek);
        if (hg > 0) serit(k.yon, k.konum, k.bas, k.son, sk.b_govde, zt + sk.h_tabla, z0, "b3-temel b3-temel-govde" + hay, ek);
        if (plan && !hafif) etiket(k.yon === "x" ? (k.bas + k.son) / 2 : k.konum, k.yon === "x" ? k.konum : (k.bas + k.son) / 2, z0, "TK-" + k.aks + " · B " + f2(sk.B));
      });
    } else if (tip === "radye") {
      const r = t.radye || TEMEL_VARS.radye, e = radyeSinir();
      if (e) {
        const hk = r.kiris ? +r.kiris.h : 0, zb = z0 - Math.max(r.h, hk), zp = zb + r.h;
        C.prizma(sahne, T, b, [(e.x0 + e.x1) / 2, (e.y0 + e.y1) / 2, zb], [(e.x0 + e.x1) / 2, (e.y0 + e.y1) / 2, zp], [(e.x1 - e.x0) / 2, 0, 0], [0, (e.y1 - e.y0) / 2, 0], "b3-temel b3-radye" + hay, ' data-tur="radye"', 1);
        if (kat === 0) hedefler.push({ tur: "cokgen", pts: [P(e.x0, e.y0, zp), P(e.x1, e.y0, zp), P(e.x1, e.y1, zp), P(e.x0, e.y1, zp)], kind: "temel" });
        if (r.kiris) {
          B.akslar.y.forEach(function (a) { const u = aksKolonUclari("x", a.ad); if (u) serit("x", +a.konum, u[0], u[1], +r.kiris.b, zp, z0, "b3-temel b3-radye-kiris" + hay, ' data-tur="radye-kirisi" data-aks="' + kacis(a.ad) + '"'); });
          B.akslar.x.forEach(function (a) { const u = aksKolonUclari("y", a.ad); if (u) serit("y", +a.konum, u[0], u[1], +r.kiris.b, zp, z0, "b3-temel b3-radye-kiris" + hay, ' data-tur="radye-kirisi" data-aks="' + kacis(a.ad) + '"'); });
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
        if (kat === 0) hedefler.push({ tur: "daire", x: P(X, Y, z0)[0], y: P(X, Y, z0)[1], r: 18 * s, kind: "temel" });
        if (!hafif && !plan) C.mesnet(sahne, T, b, [X, Y, z0 - th], t.mesnet, ' class="b3-mesnet' + hay + '"');
        if (plan && !hafif) etiket(X, Y - Lt / 2 - 0.3, z0, f2(Bt) + "×" + f2(Lt));
      });
      return;
    }
    // Winkler zemini (mütemadi / radye): kolon altlarında yay simgesi
    if (!hafif && !plan) { const zb = z0 - temelDerinlik(); kol1.forEach(function (c) { C.mesnet(sahne, T, b, [aksX(c.aks[0]), aksY(c.aks[1]), zb], "elastik", ' class="b3-mesnet b3-winkler' + hay + '"'); }); }
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
    const T = C.donusum(pts, W, H, { pl: 40, pu: 44, pa: 40 });
    const P = function (X, Y, Z) { const q = C.izdusum(X, Y, Z, b); return [T.x(q[0]), T.y(q[1])]; };
    const sahne = new C.Sahne();
    const s = kamera.pxOlcek(svg) || 1;     // 1 ekran px = s viewBox birimi
    const rHedef = (jest && jest.kaba({ pointerType: "touch" }) ? 26 : 22) * s;
    hedefler = [];
    const hafif = D.hafif, kat = D.kat, kot = katKot(kat), celik = B.sistem === "celik";
    const uyarilar = sonUyarilar || [];
    const uyariVar = function (tur, no) { return uyarilar.some(function (u) { return u.tur === tur && u.no === no; }); };
    // D/C görünümü (Tasarım sekmesi): kolon/kiriş D/C rengiyle, bütün katlar tam renk ve dokunulabilir; döşeme/duvar soluk
    const dcG = dcAktif(), dcSn = function (tur, no) { const e = tasarimKaydi(tur, no); return " b3-dc b3-dc-" + (e ? dcSinif(e.dc) : "yok"); };

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
    // temeller (kat 1 kolonlarının altında; tip §13) ve mesnetler. Temel planı: Temel katı + Plan görünümü (üst katların kiriş/döşemesi çizilmez)
    const temelPlani = kat === 0 && kamera.gorunum === "plan";
    temelleriCiz(sahne, T, b, P, s, kat, hafif, temelPlani);
    // kolonlar
    B.kolonlar.forEach(function (c) {
      if (temelPlani && c.kat !== 1) return;
      const X = aksX(c.aks[0]), Y = aksY(c.aks[1]), z1 = katKot(c.kat), z0 = katKot(c.kat - 1);
      const ko = kesitOz(c.kesit);
      if (X == null || Y == null || z1 == null || z0 == null) return;
      const bX = ko ? (c.yon === "y" ? ko.b : ko.h) : 0.4, bY = ko ? (c.yon === "y" ? ko.h : ko.b) : 0.4;
      const sinif = "b3-kolon " + (dcG ? dcSn("kolon", c.no) : (ko && ko.celik ? "b3-celik" : "b3-beton") + (c.kat !== kat ? " b3-hayalet" : "")) + (secildiMi("kolon", c.no) ? " b3-secili" : "") + (uyariVar("kolon", c.no) ? " b3-uyarili" : "");
      const ekr = C.prizma(sahne, T, b, [X, Y, z0], [X, Y, z1], [bX / 2, 0, 0], [0, bY / 2, 0], sinif, ' data-tur="kolon" data-no="' + c.no + '"', 1);
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
      const X1 = aksX(k.bas[0]), Y1 = aksY(k.bas[1]), X2 = aksX(k.son[0]), Y2 = aksY(k.son[1]), Z = katKot(k.kat);
      const ko = kesitOz(k.kesit);
      if (X1 == null || Y1 == null || X2 == null || Y2 == null || Z == null) return;
      const bb = ko ? ko.b : 0.25, hh = ko ? ko.h : 0.5, yatayX = Y1 === Y2;
      const e1 = yatayX ? [0, bb / 2, 0] : [bb / 2, 0, 0];
      const sinif = "b3-kiris " + (dcG ? dcSn("kiris", k.no) : (ko && ko.celik ? "b3-celik" : "b3-beton") + (k.kat !== kat ? " b3-hayalet" : "")) + (secildiMi("kiris", k.no) ? " b3-secili" : "") + (uyariVar("kiris", k.no) ? " b3-uyarili" : "");
      C.prizma(sahne, T, b, [X1, Y1, Z - hh / 2], [X2, Y2, Z - hh / 2], e1, [0, 0, hh / 2], sinif, ' data-tur="kiris" data-no="' + k.no + '"', 1);
      if (k.duvar && !hafif) {
        const ust = katKot(k.kat + 1) != null ? katKot(k.kat + 1) - hh : Z + 1.0;
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
      const X1 = aksX(d.kose[0][0]), Y1 = aksY(d.kose[0][1]), X2 = aksX(d.kose[1][0]), Y2 = aksY(d.kose[1][1]), Z = katKot(d.kat);
      if (X1 == null || Y1 == null || X2 == null || Y2 == null || Z == null) return;
      const kose = [[X1, Y1, Z], [X2, Y1, Z], [X2, Y2, Z], [X1, Y2, Z]];
      const sinif = "b3-doseme" + (d.kat !== kat || dcG ? " b3-hayalet" : "") + (secildiMi("doseme", d.no) ? " b3-secili" : "") + (uyariVar("doseme", d.no) ? " b3-uyarili" : "");
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
    // (D/C görünümünde Seç aracıyla kesişim/hücre hedefleri konmaz: dokunuş doğrudan kolon/kirişe gider, bütün katlarda)
    if (kat >= 1 && kot != null && !hafif && !(dcG && D.arac === "sec")) {
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
    const eksen = eksenTakimi(vb, b);
    svg.setAttribute("viewBox", kamera.viewBox());
    svg.innerHTML = '<defs><pattern id="b3-tarama" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" class="b3-tarama-c"/></pattern>' +
      '<pattern id="b3-dc-desen" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)"><rect width="7" height="7" class="b3-dc-desen-z"/><line x1="0" y1="0" x2="0" y2="7" class="b3-dc-desen-c"/></pattern></defs>' +
      sahne.html() + eksen + '<path id="bn-gecici" class="b3-gecici" d=""/>';
    dcLejantCiz();
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
    if (SON && !sonEski && D.sekme === "tasarim" && tasarimVar() && (tur === "kolon" || tur === "kiris")) { tasarimSec(tur, no, false); return; }
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
        '<div class="bn-sahne-kutu" id="bn-sahne-kutu"><div class="bn-svg-kutu" id="bn-svg-kutu"><svg id="bn-svg" class="bn-svg" role="img" aria-label="3B bina sahnesi" preserveAspectRatio="xMidYMid meet"></svg>' +
          '<div class="bn-sahne-ust" id="bn-sahne-ust"></div>' +
          '<div class="bn-sahne-dugmeler" role="toolbar" aria-label="Yerleşim">' +
            '<button type="button" class="bn-sd bn-sd-arac" id="bn-arac-ac" aria-pressed="false" title="Araç çubuğunu daralt / aç">☰</button>' +
            '<button type="button" class="bn-sd bn-sd-panel" id="bn-panel-ac" aria-pressed="false" title="Özellik panelini daralt / aç">▤</button>' +
            '<button type="button" class="bn-sd bn-sd-tam" id="bn-tam" aria-pressed="false" title="Tam ekran (F)" aria-label="Tam ekran">⛶</button></div>' +
          '<div class="bn-sahne-alt" id="bn-sahne-alt"><label class="bn-onay"><input type="checkbox" id="bn-tum-katlar"> Tüm katlara uygula</label>' +
            '<button type="button" class="dugme kucuk" id="bn-doldur">Döşemeleri doldur</button><button type="button" class="dugme kucuk" id="bn-kat-kopyala">Alt katı kopyala</button></div>' +
          "</div>" +
          '<div class="bn-dc-lejant" id="bn-dc-lejant" hidden></div>' +
          '<div id="bn-formul" class="bn-formul gizli"></div>' +
        "</div>" +
        '<details class="bn-panel" id="bn-panel" open><summary>Özellikler</summary><div class="bn-panel-sekmeler" id="bn-panel-sekmeler"></div><div class="bn-panel-icerik" id="bn-panel-icerik"></div></details>' +
      "</div>" +
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
    ["sablon", "sihirbaz", "json", "geri", "ileri", "katlar", "gorunum", "arac", "sahne-kutu", "svg-kutu", "sahne-alt", "tam", "arac-ac", "panel-ac", "cekmece", "cekmece-tutamak", "svg", "sahne-ust", "tum-katlar", "doldur", "kat-kopyala", "formul", "panel", "panel-sekmeler", "panel-icerik",
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
    ref.sahneUst.innerHTML = '<span class="bn-ipucu">' + kacis(D.kat === 0 ? TEMEL_TIP_AD[B.temeller.tip] + " temel. Plan görünümü temel planını gösterir; temele dokun: Bina / temel ayarları." : ipucu[D.arac] || "") + "</span>" + (D.firca ? '<span class="bn-firca">Fırça: ' + kacis(D.firca) + ' <button type="button" class="bn-firca-kapat" id="bn-firca-kapat" aria-label="Fırçayı bırak">✕</button></span>' : "");
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
    return alanH("Başlık", '<input class="girdi" data-bina="baslik" value="' + kacis(B.baslik || "") + '">') +
      alanH("Sistem", '<select class="girdi" data-bina="sistem">' + secenekler([["betonarme", "Betonarme (TS 500)"], ["celik", "Çelik (ÇYTHYE)"]], B.sistem) + "</select>") +
      '<h3 class="bn-pbaslik">Temel ve zemin</h3>' + temelAlanlari() +
      '<h3 class="bn-pbaslik">Kesit tahkiki</h3>' +
      alanH("Çelik kiriş yanal burulmalı burkulma boyu L_b (ÇYTHYE 9.2)", '<select class="girdi" data-analiz-sec="celik_Lb">' + secenekler([["otomatik", "Otomatik — döşemeli kirişte üst başlık tutulu (L_b = 0)"], ["boy", "Eleman boyu (L_b = L; tutulma yok)"]], (B.analiz && B.analiz.celik_Lb) || "otomatik") + "</select>") +
      (B.sistem === "celik" ? "" : '<p class="not">Yalnız çelik elemanlarda kullanılır; betonarme tahkik TS 500 ile yapılır.</p>') +
      '<p class="not">Yük durumları ve kombinasyon kümesi “Yükler” sekmesinde, TBDY 2018 deprem girdileri “Deprem” sekmesinde. Uygulama öğretim ve ön boyutlandırma içindir, tasarım aracı değildir.</p>';
  }
  // Temel tipi seçici + tipe göre alanlar (tasarım §13). data-temel-a="<alt nesne>.<alan>" sayısal alanlar; m cinsinden.
  function sayiAlan(etiket, yol, deger, ipucu) {
    return alanH(etiket, '<input class="girdi" inputmode="decimal" data-temel-a="' + yol + '" value="' + kacis(deger != null ? deger : "") + '"' + (ipucu ? ' title="' + kacis(ipucu) + '"' : "") + ">");
  }
  function temelAlanlari() {
    const t = B.temeller, z = t.zemin || {}, v = t.varsayilan || {};
    let h = '<div class="se-seg bn-temel-tip" role="radiogroup" aria-label="Temel tipi">' + ["tekil", "surekli", "radye"].map(function (k) {
      return '<button type="button" class="se-seg-d" role="radio" data-temel-tip="' + k + '" aria-checked="' + (t.tip === k) + '" aria-pressed="' + (t.tip === k) + '">' + TEMEL_TIP_AD[k] + "</button>";
    }).join("") + "</div>";
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
    binayiAyarla(yeni, "Bina üretildi: " + p.x.length + "×" + p.y.length + " aks, " + p.katSayisi + " kat, " + TEMEL_TIP_AD[yeni.temeller.tip].toLocaleLowerCase("tr") + " temel.");
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
    k.duvarlar = sozlukListe(y.duvarlar, function (ad, x) { return { ad: ad, etiket: x.ad || ad, w: x.deger, kaynak: x.kaynak, dogrulandi: x.dogrulandi }; }) || k.duvarlar;
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
    return A.motorIstegi({ islem: "bina_sablonlar", girdi: {} }).then(function (y) {
      if (y && !y.hata && Array.isArray(y.sablonlar) && y.sablonlar.length) { sablonlar = y.sablonlar; sablonListesi(); }
    }, function () { /* yerleşik */ });
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
  function coz() {
    if (D.cozuluyor) return;
    const dg = dogrula();
    hataGoster(ref.hata, dg.hata, dg.hata.length > 1 ? "Modelde düzeltilecek yerler var:" : "");
    if (dg.hata.length) { ref.hata.scrollIntoView({ block: "nearest", behavior: "smooth" }); return; }
    if (dg.uyari.length && !window.confirm(dg.uyari.length + " uyarı var (ör. " + dg.uyari[0].metin + "). Yine de çözülsün mü?")) return;
    D.cozuluyor = true; ilerlemeBaslat(); hatCiz();
    const cozulen = kopya(B);
    A.motorIstegi({ islem: "bina_coz", girdi: { bina: cozulen } }).then(function (y) {
      if (!y || y.hata) { cekmeceAc(); SON = null; hataGoster(ref.hata, [y && y.hata ? y.hata : "Boş yanıt."], y && y.hata_turu === "ic" ? "Motor hatası" : "Bina çözülemedi"); sonucuTemizle(); return; }
      if (!y.veri || !y.veri.ag || !y.veri.durumlar) { hataGoster(ref.hata, ["Motor yanıtında “veri.ag” ya da “veri.durumlar” yok (şema §4)."], "Beklenmeyen yanıt"); return; }
      hataGoster(ref.hata, []);
      SON = { y: y, veri: y.veri, bina: cozulen }; sonEski = false; D.akisHedef = null; D.sankeySecim = null; D.sekme = "akis"; D.tasarimSecim = null;
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
      const t = (v.akis.temeller || []).filter(function (x) { return x.kolon_no === cno; })[0];
      if (!t) return;
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
      const t = v.akis.temeller.filter(function (x) { return x.kolon_no === +p[1]; })[0];
      if (!t) return;
      baslik = "Temel T-" + adres(t.aks) + " — taban basıncı (servis G+Q)";
      tex = "\\sigma_{max,min} = \\frac{N}{BL} \\pm \\frac{6M_X}{BL^2} \\pm \\frac{6M_Y}{LB^2} = \\frac{" + f1(t.N_servis).replace(",", "{,}") + "}{" + f2(t.B).replace(",", "{,}") + "\\cdot" + f2(t.L).replace(",", "{,}") + "} \\pm \\ldots = " + f1(t.sigma_max).replace(",", "{,}") + "\\ /\\ " + f1(t.sigma_min).replace(",", "{,}") + "\\ \\text{kN/m}^2";
      tex += "\\\\ e_X = " + f2(t.e_X).replace(",", "{,}") + "\\ \\text{m},\\ e_Y = " + f2(t.e_Y).replace(",", "{,}") + "\\ \\text{m}" + (t.cekirdek_icinde ? "\\ (\\le B/6: \\text{çekirdek içinde})" : "\\ (\\text{çekirdek dışında!})") + ",\\quad D/C = \\frac{\\sigma_{max}}{q_{em}} = " + f2(t.DC).replace(",", "{,}");
      not = "q_em = " + f1(t.q_em) + " kN/m². Temel ebatları: B = " + f2(t.B) + " m, L = " + f2(t.L) + " m."; adim = "akis";
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
    const cokKiris = (v.bina.kirisler || []).length >= 40;
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
    const basliklar = ["Döşemeler", "Kirişler"]; for (let k = ust; k >= 1; k--) basliklar.push("Kolon k" + k); basliklar.push("Temeller", "Zemin");
    if (cokKiris) svg += metinSvg(W / 2, H - 6, "Kiriş ve döşeme etiketleri için bir düğüme dokunun.", "bn-sankey-not", "middle");
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
    const bagli = {};
    if (secim) kenarlar.forEach(function (e) { if (e.kaynak === secim) bagli[e.hedef] = 1; if (e.hedef === secim) bagli[e.kaynak] = 1; });
    Object.keys(dugum).forEach(function (id) {
      const n = dugum[id];
      const ad = id.charAt(0) === "S" ? "S" + id.slice(1).replace(/\/k\d+/, "") : id.indexOf("T-") === 0 ? id.slice(2) : id.indexOf("N-") === 0 ? id.slice(2).replace(/\/k\d+/, "") : id;
      // 40+ kirişli binada döşeme/kiriş etiketleri yalnız seçili düğüm ve komşuları için gösterilir
      const etiketGoster = !(cokKiris && (id.charAt(0) === "D" || id.charAt(0) === "K")) || secim === id || bagli[id];
      svg += '<g class="bn-sankey-dugum' + (secim === id ? " aktif" : "") + '" data-sankey="' + kacis(id) + '" tabindex="0" role="button" aria-label="' + kacis(id + " " + f1(n.akis) + " kN") + '"><rect x="' + r1(n.x) + '" y="' + r1(n.y) + '" width="' + gw + '" height="' + r1(n.h) + '" rx="2"><title>' + kacis(ad + " " + f1(n.akis) + " kN") + "</title></rect>" +
        (etiketGoster ? metinSvg(n.s === 0 ? n.x - 4 : n.x + gw + 4, n.y + n.h / 2 + 3.5, ad + " " + f1(n.akis), "bn-sankey-t", n.s === 0 ? "end" : "start") : "") + "</g>";
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
    if (D.sekme === "temel" && !temelVar()) D.sekme = "akis";
    let h = '<div class="bn-eski se-eski' + (sonEski ? "" : " gizli") + '">Model değişti: aşağıdaki sonuçlar önceki modele aittir. Yeniden çözmek için “Çöz” düğmesine basın.</div>';
    h += '<div class="se-ozet"><span class="se-rozet">' + (o.sd_sayisi != null ? o.sd_sayisi : v.ag.sd_sayisi) + " SD</span><span class=\"se-rozet\">" + (o.eleman != null ? o.eleman : v.ag.elemanlar.length) + " eleman</span>" +
      '<span class="se-rozet">ΣG = ' + f1(o.toplam_G != null ? o.toplam_G : v.yukler.toplam.G) + " kN</span><span class=\"se-rozet\">ΣQ = " + f1(o.toplam_Q != null ? o.toplam_Q : v.yukler.toplam.Q) + " kN</span>" +
      '<span class="se-rozet">' + Object.keys(v.durumlar || {}).length + " durum · " + ((v.kombinasyonlar || []).filter(function (k) { return k.uygulandi && k.tur !== "drift"; }).length || Object.keys(v.sonuclar || {}).length) + " kombinasyon</span>" +
      (depremVar() ? '<span class="se-rozet">V_tE = ' + f1(v.deprem.VtE) + " kN</span>" : "") +
      (o.en_buyuk_temel_DC != null ? '<span class="se-rozet">Temel D/C maks ' + f2(o.en_buyuk_temel_DC) + "</span>" : "") +
      (v.tasarim ? '<span class="se-rozet bn-dc-rozet bn-dc-' + dcSinif(v.tasarim.en_buyuk_dc) + '">Eleman D/C maks ' + f2(v.tasarim.en_buyuk_dc) + "</span>" : "") + "</div>";
    if (o.uyarilar && o.uyarilar.length) h += '<div class="bn-uyari-kutu">' + o.uyarilar.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    h += '<div class="bn-sekmeler" role="tablist">' + SEKMELER.filter(function (s) { return (s[0] !== "deprem" || depremVar()) && (s[0] !== "temel" || temelVar()); }).map(function (s) { return '<button type="button" role="tab" class="bn-sekme' + (D.sekme === s[0] ? " aktif" : "") + '" data-sekme="' + s[0] + '" aria-selected="' + (D.sekme === s[0]) + '">' + s[1] + "</button>"; }).join("") + "</div>";
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
      '<div class="dugmeler"><button type="button" class="dugme kucuk" id="bn-oynat">▶ Oynat</button><span class="not">3B sahnede bir döşeme, kiriş ya da kolona dokun: yük yolu vurgulanır; ok ve etiketlere dokununca formül kartı açılır.</span></div></div>' +
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
  // Aks filtresi. Temel kirişi elemanının ara düğümleri aks kesişiminde değildir: eleman kendi "aks" alanını taşır (yoksa düğüm aksları).
  function elemanFiltre(e) {
    if (e.tur === "radye-serit") return false;              // radye ızgara şeritleri diyagramda çizilmez (Temel sekmesinde)
    if (!D.aksFiltre) return true;
    const p = D.aksFiltre.split(":"), i = p[0] === "x" ? 0 : 1;
    if (e.tur === "temel-kirisi" && e.aks != null) return String(e.aks) === p[1] && (!e.yon || e.yon === (i === 0 ? "y" : "x"));
    const a = agDugum(e.dugumler[0]), b = agDugum(e.dugumler[1]);
    return !!(a && b && a.aks && b.aks && a.aks[i] === p[1] && b.aks[i] === p[1]);
  }
  function elemanAdi(e) {
    if (e.tur === "kolon") return kolonAdres(e.kaynak_no);
    if (e.tur === "temel-kirisi") return e.adres || ("TK-" + (e.aks != null ? e.aks : e.kaynak_no));
    if (e.tur === "radye-serit") return e.adres || ("RŞ" + e.no);
    return kirisAdres(e.kaynak_no);
  }
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
        if (vs.length && Math.abs(vs[im]) > 1e-6) { const sg = def.isaret * vs[im] >= 0 ? 1 : -1; s += metinSvg(ust[im][0] + n[0] * sg * 10, ust[im][1] + n[1] * sg * 10 + 4, fmt(vs[im], 3), "se-etiket", "middle"); }
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
      '<p class="not">N = ' + fmt(enb.N, 3) + " kN · V_maks = " + fmt(enb.V, 3) + " kN · M_maks = " + fmt(enb.M, 3) + " kN·m · Vz = " + fmt(enb.Vz, 3) + " · My = " + fmt(enb.My, 3) + " · T = " + fmt(enb.T, 3) + "</p>" + zarfH + "</div>";
  }
  // ---------- Tablolar ----------
  function tablolarSekmesi() {
    const v = V();
    let h = '<div class="bn-satir">' + durumSecici("bn-tablo-durum", D.deformeDurum, false) + "</div>";
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
    h += "<h4>Kiriş yük dökümü (kN toplam; q = Σ/L kN/m)</h4>" + tabloH(["Kiriş", "L (m)", "G döşeme", "G duvar", "G öz", "G ek", "ΣG (kN)", "q_G (kN/m)", "Q döşeme", "Q ek", "ΣQ (kN)", "q_Q (kN/m)", "R_G≈qL/2", "M_G≈qL²/8"], (v.yukler.kirisler || []).map(function (k) {
      return [kirisAdres(k.no), f2(k.L), f1(k.G.doseme), f1(k.G.duvar), f1(k.G.oz), f1(k.G.ek), f1(k.G.toplam_kN), f2(kirisKNm(k, "G").toplam), f1(k.Q.doseme), f1(k.Q.ek), f1(k.Q.toplam_kN), f2(kirisKNm(k, "Q").toplam), f1(k.el_hesabi.R_G), f1(k.el_hesabi.M_G)];
    }));
    h += "<h4>Döşeme payları (TS 500 11.4.3)</h4>" + tabloH(["Döşeme", "lx×ly", "m", "Tip", "g / q", "Kiriş", "Kenar", "Şekil", "Tepe G", "Tepe Q", "q_eM G", "q_eV G", "Toplam G", "Toplam Q"], [].concat.apply([], (v.yukler.dosemeler || []).map(function (d) {
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
    h += "<h4>Ağ</h4>" + tabloH(["Eleman", "Tür", "Kaynak", "Kat", "L (m)", "Kesit", "Düğümler"], (v.ag.elemanlar || []).map(function (e) { return ["e" + e.no, e.tur, elemanAdi(e), String(e.kat), f2(e.L), e.kesit, e.dugumler.join(" → ")]; }));
    return h;
  }
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
  };
  function yokSayisi(t) { return (t.elemanlar || []).filter(function (e) { return e.dc == null; }).length; }
  function tasarimVar() { const v = V(); return !!(v && v.tasarim && Array.isArray(v.tasarim.elemanlar)); }
  function dcAktif() { return !!(SON && !sonEski && D.sekme === "tasarim" && D.dcGorunum && tasarimVar()); }
  function tasarimKaydi(tur, no) { const v = V(); return v && v.tasarim ? (v.tasarim.elemanlar || []).filter(function (e) { return e.tur === tur && e.no === no; })[0] || null : null; }
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
  function turAd(e) { return (e.sistem === "celik" ? "çelik " : "") + (e.tur === "kolon" ? "kolon" : "kiriş"); }
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
    if ((t.uyarilar || []).length) h += '<div class="bn-uyari-kutu">' + t.uyarilar.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    h += "<h4>D/C dağılımı (" + (t.elemanlar || []).length + " eleman; en büyük " + f2(t.en_buyuk_dc) + (t.kombinasyon_sayisi ? "; " + t.kombinasyon_sayisi + " dayanım/deprem kombinasyonu" : "") + ")</h4>" + dcCubugu(t);
    const kritik = (t.kritik_elemanlar || []).slice(0, 10);
    if (kritik.length) h += '<div class="bn-kritik"><span class="not">Kritik:</span>' + kritik.map(function (k) {
      return '<button type="button" class="bn-cip bn-kritik-cip" data-dc-sec="' + kacis(k.tur + ":" + k.no) + '" title="' + kacis((k.kontrol || "") + (k.kombinasyon ? " · " + k.kombinasyon : "")) + '">' + kacis(k.adres || (k.tur + " " + k.no)) + " " + dcCip(k.dc) + "</button>";
    }).join("") + "</div>";
    h += '<div class="bn-satir"><label class="bn-onay"><input type="checkbox" id="bn-dc-gorunum"' + (D.dcGorunum ? " checked" : "") + "> 3B’de D/C renkleri</label>" +
      '<select class="girdi bn-secici" id="bn-dc-filtre" aria-label="Tasarım tablosu süzgeci">' + secenekler([["", "Bütün elemanlar"], ["kiris", "Yalnız kirişler"], ["kolon", "Yalnız kolonlar"], ["asim", "Yalnız D/C > 1"]].concat(yokSayisi(t) ? [["yok", "Yalnız hesaplanamayanlar"]] : []), D.tasarimFiltre) + "</select></div>";
    h += '<div id="bn-tasarim-ayrinti" class="bn-tasarim-ayrinti" aria-live="polite">' + tasarimAyrintiHtml() + "</div>";
    h += "<h4>Elemanlar (D/C’ye göre sıralı; satıra dokun: 3B’de seçilir, ayrıntı açılır)</h4>" + tasarimTablosu(t);
    return h;
  }
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
          '<th scope="row">' + kacis(e.adres || (e.tur === "kolon" ? kolonAdres(e.no) : kirisAdres(e.no))) + '<span class="bn-dc-mobil"> ' + dcCip(e.dc) + "</span></th><td class=\"bn-dc-kisa\">" + kacis(turAd(e)) + "</td><td class=\"bn-dc-kisa\">" + kacis(e.kesit || "") + "</td><td>" + kacis(b.kontrol || k.ad || (e.dc == null ? "hesaplanamadı" : "")) + "</td>" +
          '<td class="bn-komb-ad">' + kacis(b.kombinasyon || k.kombinasyon || "—") + '</td><td class="sayi">' + kacis(tkDeger(k.talep, k.birim)) + '</td><td class="sayi">' + kacis(tkDeger(k.kapasite, k.birim)) + "</td>" +
          '<td class="sayi">' + dcCip(e.dc) + "</td><td>" + kacis(e.durum || "") + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }
  function tasarimAyrintiHtml() {
    const s = D.tasarimSecim, e = s && tasarimKaydi(s.tur, s.no);
    if (!e) return '<p class="not bn-tasarim-ipucu">Bir elemana dokunun (3B sahnede ya da tablodaki satıra): özet, kontroller ve “Ayrıntılı hesap”.</p>';
    const oz = e.ozet || {}, b = e.belirleyen || {};
    const sira = Object.keys(OZET_ETIKET), ozAnahtar = Object.keys(oz).sort(function (a, b) { const i = sira.indexOf(a), j = sira.indexOf(b); return (i < 0 ? 999 : i) - (j < 0 ? 999 : j); });
    const ozSatir = ozAnahtar.filter(function (k) { return oz[k] != null && oz[k] !== ""; }).map(function (k) {
      const et = OZET_ETIKET[k] || [k, ""], val = oz[k];
      const deger = typeof val === "boolean" ? (val ? "evet" : "hayır") : /^rho/.test(k) && typeof val === "number" ? "%" + fmt(val * 100, 3) : typeof val === "number" ? fmt(val, 4) + (et[1] ? " " + et[1] : "") : String(val);
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
    return '<div class="bn-kart bn-dc-kart bn-dc-kenar-' + dcSinif(e.dc) + '"><div class="bn-dc-baslik"><b>' + kacis(e.adres || "") + "</b> · " + kacis(turAd(e)) + " · " + kacis(e.kesit || "") + (e.malzeme ? " · " + kacis(e.malzeme) : "") +
      " · kat " + kacis(e.kat) + " " + dcCip(e.dc) + ' <span class="se-rozet">' + kacis(e.durum || "") + "</span>" +
      '<button type="button" class="bn-firca-kapat bn-dc-kapat" id="bn-tasarim-kapat" aria-label="Ayrıntıyı kapat">✕</button></div>' +
      '<p class="not">Belirleyen: <b>' + kacis(b.kontrol || "—") + "</b>" + (b.kombinasyon ? " · " + kacis(b.kombinasyon) : "") + (e.fe_elemanlar && e.fe_elemanlar.length ? " · FE eleman " + e.fe_elemanlar.map(function (n) { return "e" + n; }).join(", ") : "") + "</p>" +
      (e.hata ? '<div class="hata-kutu" role="alert"><strong>Tahkik edilemedi</strong><div class="se-hata-metin">' + kacis(e.hata) + "</div></div>" : "") +
      ((e.uyarilar || []).length ? '<div class="bn-uyari-kutu">' + e.uyarilar.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>" : "") +
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
    D.secim = e ? [{ tur: tur, no: no }] : [];
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
    const anahtar = s.tur + ":" + s.no, sonSON = SON;
    const p = A.motorIstegi({ islem: "bina_eleman_tasarim", girdi: { cozum_kimligi: v.cozum_kimligi || null, tur: s.tur, no: s.no, bina: SON.bina || kopya(B) } }).then(function (y) {
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
  function temelDurumAdi(t) { return t.durum || "G+Q (servis)"; }
  function farkliOturmaMetin(fo) {
    const o = typeof fo === "number" ? fo : fo && fo.oran;
    if (o == null || !isFinite(o)) return "—";
    return o > 0 ? "1/" + Math.round(1 / o).toLocaleString("tr-TR") : "0";
  }
  function temelZimbalama(t) { return Array.isArray(t.zimbalama) ? t.zimbalama : (Array.isArray(t.tasarim) ? t.tasarim.filter(function (x) { return x.tur === "zimbalama"; }) : []); }
  function temelDonati(t) { return Array.isArray(t.donati) ? t.donati : (Array.isArray(t.tasarim) ? t.tasarim.filter(function (x) { return x.tur !== "zimbalama"; }) : []); }
  function temelSekmesi() {
    const v = V(), t = v.temel, dg = t.dugumler || [];
    const cekme = dg.filter(function (d) { return d.p_kNm2 < 0; });
    const qem = t.q_em != null ? t.q_em : (v.bina.temeller && v.bina.temeller.zemin && v.bina.temeller.zemin.q_em);
    const fo = t.farkli_oturma;
    const prm = function (ad, deger, ek) { return '<div class="bn-param"><span>' + ad + "</span><b>" + deger + "</b>" + (ek ? '<span class="bn-kaynak">' + ek + "</span>" : "") + "</div>"; };
    let h = '<div class="bn-temel-ozet"><h4>' + kacis((TEMEL_TIP_AD[t.tip] || t.tip || "Temel") + " temel") + " · " + kacis(temelDurumAdi(t)) + "</h4>" +
      '<div class="bn-param-grid bn-temel-param">' +
      prm("p_maks (kN/m²)", f1(t.p_maks), "q_em = " + f1(qem)) +
      prm("p_min (kN/m²)", f1(t.p_min), t.p_min < 0 ? "zeminde çekme" : "") +
      prm("Zemin D/C (p_maks / q_em)", dcCip(t.DC_zemin), "TS 500 emniyet, servis") +
      prm("Oturma maks (mm)", f1(t.oturma_maks_mm), t.oturma_min_mm != null ? "min " + f1(t.oturma_min_mm) + " mm" : "") +
      prm("Farklı oturma", farkliOturmaMetin(fo), fo && typeof fo === "object" && fo.fark_mm != null ? "Δ = " + f1(fo.fark_mm) + " mm / " + f2(fo.aciklik_m) + " m" : "") +
      prm("k₀ (kN/m³)", t.k0 != null ? Math.round(t.k0).toLocaleString("tr-TR") : "—", "Winkler") +
      (t.tasima_gucu ? prm("Taşıma gücü D/C", dcCip(t.tasima_gucu.dc), "q_t = " + f1(t.tasima_gucu.q_t) + " kN/m² (" + kacis(t.tasima_gucu.kombinasyon || "katsayılı") + ")") : "") +
      "</div></div>";
    const uy = (t.uyarilar || []).slice();
    if (cekme.length && !uy.some(function (u) { return /çekme|ayrıl/i.test(u); })) uy.unshift(cekme.length + " düğümde taban basıncı negatif (p < 0): temel zeminden ayrılıyor. Winkler yayı çekme taşıyamaz; sonuç yaklaşıktır, temel boyutunu ya da kalınlığını artırın.");
    if (uy.length) h += '<div class="bn-uyari-kutu bn-temel-uyari">' + uy.map(function (u) { return "<div>⚠ " + kacis(u) + "</div>"; }).join("") + "</div>";
    else h += '<div class="bn-iyi-kutu">Zeminde çekme yok; taban basıncı her yerde basınç.</div>';
    h += '<div class="bn-satir"><div class="se-seg" role="group" aria-label="Harita">' +
      '<button type="button" class="se-seg-d" data-temel-harita="p" aria-pressed="' + (D.temelHarita !== "w") + '">Taban basıncı (kN/m²)</button>' +
      '<button type="button" class="se-seg-d" data-temel-harita="w" aria-pressed="' + (D.temelHarita === "w") + '">Oturma (mm)</button></div></div>' +
      '<div class="se-sekil bn-temel-harita" id="bn-temel-harita"></div><p class="not" id="bn-temel-bilgi" aria-live="polite"></p>';
    const zb = temelZimbalama(t);
    h += "<h4>Zımbalama (TS 500 md. 8.3)</h4>";
    if (zb.length) {
      h += '<div class="se-tablo-kutu"><table class="se-sonuc-tablo bn-temel-zimba"><thead><tr><th scope="col">Kolon</th><th scope="col">N_d (kN)</th><th scope="col">V_pd (kN)</th><th scope="col">V_pr (kN)</th><th scope="col">u_p (m)</th><th scope="col">d (m)</th><th scope="col">D/C</th></tr></thead><tbody>' +
        zb.map(function (z) {
          const ad = z.adres || (Array.isArray(z.aks) ? "S-" + z.aks.join("") : z.kolon != null ? kolonAdres(z.kolon) : "—");
          return '<tr class="' + (z.dc > 1 ? "bn-drift-asim" : "") + '"><th scope="row">' + kacis(ad) + '</th><td class="sayi">' + f1(z.N_d) + '</td><td class="sayi">' + f1(z.V_pd) + '</td><td class="sayi">' + f1(z.V_pr) + '</td><td class="sayi">' + f2(z.u_p) + '</td><td class="sayi">' + f2(z.d) + "</td><td>" + dcCip(z.dc) + "</td></tr>";
        }).join("") + "</tbody></table></div><p class=\"not\">V_pd = N_d − zemin tepkisi (zımbalama çevresi içinde); V_pr = γ·f_ctd·u_p·d, u_p kolon yüzünden d/2 uzaklıkta.</p>";
    } else h += '<p class="not">' + (t.tip === "surekli" ? "Mütemadi temelde kolon yükü temel kirişine aktarılır; zımbalama yerine kiriş kesmesi ve tabla kesmesi denetlenir (donatı tablosu)." : "Zımbalama kaydı yok.") + "</p>";
    const dn = temelDonati(t);
    if (dn.length) {
      const kir = dn.filter(function (d) { return d.tur !== "radye"; }), rad = dn.filter(function (d) { return d.tur === "radye"; });
      if (kir.length) {
        h += "<h4>Temel kirişi donatısı (TS 500)</h4>" + '<div class="se-tablo-kutu"><table class="se-sonuc-tablo bn-temel-donati"><thead><tr><th scope="col">Kiriş</th><th scope="col">M_d mesnet / açıklık (kN·m)</th><th scope="col">As üst (cm²)</th><th scope="col">As alt (cm²)</th><th scope="col">Öneri üst / alt</th><th scope="col">V_d (kN) · etriye</th><th scope="col">Tabla As (cm²/m)</th></tr></thead><tbody>' +
          kir.map(function (d) {
            return '<tr><th scope="row">' + kacis(d.ad || ("TK-" + (d.aks || ""))) + '</th><td class="sayi">' + f1(d.Md_mesnet) + " / " + f1(d.Md_aciklik) + '</td><td class="sayi">' + f2(d.As_ust_cm2) + '</td><td class="sayi">' + f2(d.As_alt_cm2) + "</td><td>" + kacis((d.oneri_ust || "—") + " / " + (d.oneri_alt || "—")) + '</td><td class="sayi">' + f1(d.Vd) + (d.etriye ? " · " + kacis(d.etriye) : "") + '</td><td class="sayi">' + (d.tabla ? f2(d.tabla.As_cm2_m) + (d.tabla.oneri ? " (" + kacis(d.tabla.oneri) + ")" : "") : "—") + "</td></tr>";
          }).join("") + "</tbody></table></div>";
      }
      if (rad.length) {
        h += "<h4>Radye donatısı (m başına; ρ_min = 0,002)</h4>" + '<div class="se-tablo-kutu"><table class="se-sonuc-tablo bn-temel-donati"><thead><tr><th scope="col">Doğrultu</th><th scope="col">m maks / min (kN·m/m)</th><th scope="col">As alt (cm²/m)</th><th scope="col">As üst (cm²/m)</th><th scope="col">As min (cm²/m)</th><th scope="col">Öneri alt / üst</th></tr></thead><tbody>' +
          rad.map(function (d) {
            return '<tr><th scope="row">' + kacis(d.yon === "y" ? "Y doğrultusu" : "X doğrultusu") + '</th><td class="sayi">' + f1(d.m_maks) + " / " + f1(d.m_min) + '</td><td class="sayi">' + f2(d.As_alt_cm2_m) + '</td><td class="sayi">' + f2(d.As_ust_cm2_m) + '</td><td class="sayi">' + f2(d.As_min_cm2_m) + "</td><td>" + kacis((d.oneri_alt || "—") + " / " + (d.oneri_ust || "—")) + "</td></tr>";
          }).join("") + "</tbody></table></div>";
      }
    }
    if ((v.ag.elemanlar || []).some(function (e) { return e.tur === "temel-kirisi"; }))
      h += '<p class="not">Temel kirişlerinin N, V, M diyagramları Diyagramlar sekmesinde (aks filtresiyle tek kiriş). <button type="button" class="dugme kucuk" data-temel-sekme-git="diyagram">Diyagramlara git</button></p>';
    return h;
  }
  // Plan haritası: radyede düğüm etki hücreleri, mütemadide kiriş boyunca B genişlikte şeritler; lejant + q_em çizgisi
  function temelHaritaCiz() {
    const kap = document.getElementById("bn-temel-harita"), v = V();
    if (!kap || !v || !v.temel) return;
    document.querySelectorAll("#bn-sonuc [data-temel-harita]").forEach(function (b) { b.setAttribute("aria-pressed", String((b.dataset.temelHarita === "w") === (D.temelHarita === "w"))); });
    const t = v.temel, dg = t.dugumler || [], wk = D.temelHarita === "w", ana = wk ? "w_mm" : "p_kNm2";
    if (!dg.length) { kap.innerHTML = ""; return; }
    const nd = {}; dg.forEach(function (d) { nd[d.no] = d; });
    const qem = t.q_em != null ? +t.q_em : null;
    const serit = (t.elemanlar || []).filter(function (e) { return e.tur === "temel-kirisi" && e.dugumler && nd[e.dugumler[0]] && nd[e.dugumler[1]]; });
    const radye = t.tip === "radye" || !serit.length;
    let a = +t.ag || 0;
    if (!(a > 0)) { const xs = dg.map(function (d) { return d.X; }).sort(function (p, q) { return p - q; }); a = 0.5; for (let i = 1; i < xs.length; i++) if (xs[i] - xs[i - 1] > 1e-6) { a = xs[i] - xs[i - 1]; break; } }
    const Bs = +(t.B || (t.parametreler && t.parametreler.B) || (v.bina.temeller && v.bina.temeller.surekli && v.bina.temeller.surekli.B) || 1);
    const pay = radye ? 0 : Bs / 2;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    dg.forEach(function (d) { x0 = Math.min(x0, d.X); x1 = Math.max(x1, d.X); y0 = Math.min(y0, d.Y); y1 = Math.max(y1, d.Y); });
    x0 -= pay; x1 += pay; y0 -= pay; y1 += pay;
    const W = Math.max(280, Math.min(1100, kap.clientWidth || 600)), pl = 34, pr = 34, pu = 26, lejH = 58;
    const sc = Math.min((W - pl - pr) / Math.max(0.5, x1 - x0), 520 / Math.max(0.5, y1 - y0));
    const Hp = (y1 - y0) * sc, H = Math.round(pu + Hp + 24 + lejH);
    const X = function (x) { return pl + (x - x0) * sc + ((W - pl - pr) - (x1 - x0) * sc) / 2; }, Y = function (y) { return pu + (y1 - y) * sc; };
    const degerler = dg.map(function (d) { return +d[ana]; }).filter(isFinite);
    const vmax = Math.max.apply(null, degerler), vmin = Math.min.apply(null, degerler);
    const ust = wk ? Math.max(vmax, 1e-9) : Math.max(vmax, qem || 0, 1e-9);
    const u = function (val) { return val / ust; };
    const sinif = function (val) { return (!wk && val < 0) ? " bn-isi-cekme" : (!wk && qem != null && val > qem) ? " bn-isi-asim" : ""; };
    const baslik = function (d) { return "Düğüm " + d.no + " (X " + f2(d.X) + ", Y " + f2(d.Y) + " m): p = " + f1(d.p_kNm2) + " kN/m², oturma = " + f2(d.w_mm) + " mm"; };
    let s = "", hucre = "";
    if (radye) {
      dg.forEach(function (d) {
        const val = +d[ana], cx0 = Math.max(x0, d.X - a / 2), cx1 = Math.min(x1, d.X + a / 2), cy0 = Math.max(y0, d.Y - a / 2), cy1 = Math.min(y1, d.Y + a / 2);
        hucre += '<rect class="bn-isi' + sinif(val) + '" x="' + r1(X(cx0)) + '" y="' + r1(Y(cy1)) + '" width="' + r1((cx1 - cx0) * sc + 0.6) + '" height="' + r1((cy1 - cy0) * sc + 0.6) + '" fill="' + isiRengi(u(Math.max(0, val))) + '" data-tdugum="' + d.no + '"><title>' + kacis(baslik(d)) + "</title></rect>";
      });
      s += hucre + '<rect class="bn-isi-cerceve" x="' + r1(X(x0)) + '" y="' + r1(Y(y1)) + '" width="' + r1((x1 - x0) * sc) + '" height="' + r1((y1 - y0) * sc) + '"/>';
    } else {
      serit.forEach(function (e) {
        const p = nd[e.dugumler[0]], q = nd[e.dugumler[1]], b = +(e.B || Bs), L = Math.hypot(q.X - p.X, q.Y - p.Y) || 1;
        const nx = -(q.Y - p.Y) / L * b / 2, ny = (q.X - p.X) / L * b / 2, val = (+p[ana] + +q[ana]) / 2;
        const k = [[p.X + nx, p.Y + ny], [q.X + nx, q.Y + ny], [q.X - nx, q.Y - ny], [p.X - nx, p.Y - ny]];
        hucre += '<polygon class="bn-isi' + sinif(val) + '" points="' + k.map(function (c) { return pt(X(c[0]), Y(c[1])); }).join(" ") + '" fill="' + isiRengi(u(Math.max(0, val))) + '" data-tdugum="' + p.no + '" data-teleman="' + e.no + '"><title>' + kacis(elemanAdi(e) + " · " + baslik(p)) + "</title></polygon>";
      });
      s += hucre;
    }
    // akslar ve kolonlar
    const bn = v.bina, akx = (bn.akslar && bn.akslar.x) || [], aky = (bn.akslar && bn.akslar.y) || [];
    akx.forEach(function (ak) { s += '<path class="bn-isi-aks" d="M' + pt(X(+ak.konum), Y(y1) - 6) + " L" + pt(X(+ak.konum), Y(y0) + 6) + '"/>' + metinSvg(X(+ak.konum), pu - 10, ak.ad, "bn-isi-aks-t", "middle"); });
    aky.forEach(function (ak) { s += '<path class="bn-isi-aks" d="M' + pt(X(x0) - 6, Y(+ak.konum)) + " L" + pt(X(x1) + 6, Y(+ak.konum)) + '"/>' + metinSvg(X(x0) - 12, Y(+ak.konum) + 4, ak.ad, "bn-isi-aks-t", "end"); });
    const konum = function (ad, l) { const a2 = l.filter(function (z) { return z.ad === ad; })[0]; return a2 ? +a2.konum : null; };
    (bn.kolonlar || []).filter(function (c) { return c.kat === 1; }).forEach(function (c) {
      const cx = konum(c.aks[0], akx), cy = konum(c.aks[1], aky);
      if (cx == null || cy == null) return;
      const bx = Math.max(5, (c.bX || 0.4) * sc), by = Math.max(5, (c.bY || 0.4) * sc);
      s += '<rect class="bn-isi-kolon" x="' + r1(X(cx) - bx / 2) + '" y="' + r1(Y(cy) - by / 2) + '" width="' + r1(bx) + '" height="' + r1(by) + '"/>';
    });
    // en büyük değer işareti
    const dm = dg.reduce(function (m, d) { return +d[ana] > +m[ana] ? d : m; }, dg[0]);
    s += '<circle class="bn-isi-maks" cx="' + r1(X(dm.X)) + '" cy="' + r1(Y(dm.Y)) + '" r="5"/>' + metinSvg(X(dm.X) + 8, Y(dm.Y) - 8, (wk ? "w_maks " + f1(dm.w_mm) + " mm" : "p_maks " + f1(dm.p_kNm2)), "bn-isi-etiket", X(dm.X) > W * 0.7 ? "end" : "start");
    // lejant (renk çubuğu, 0 … üst; basınçta q_em çizgisi)
    const lx = pl, lw = Math.min(360, W - pl - pr), ly = pu + Hp + 30, lh = 12;
    let grd = '<linearGradient id="bn-isi-grd" x1="0" x2="1" y1="0" y2="0">';
    for (let i = 0; i <= 12; i++) grd += '<stop offset="' + (i / 12).toFixed(3) + '" stop-color="' + isiRengi(i / 12) + '"/>';
    grd += "</linearGradient>";
    s += '<rect class="bn-isi-lejant" x="' + lx + '" y="' + ly + '" width="' + lw + '" height="' + lh + '" fill="url(#bn-isi-grd)" rx="3"/>';
    [0, 0.5, 1].forEach(function (f) { s += '<path class="bn-isi-tik" d="M' + pt(lx + f * lw, ly + lh) + " l0,4\"/>" + metinSvg(lx + f * lw, ly + lh + 16, wk ? f2(f * ust) : f1(f * ust), "bn-isi-lt", f === 0 ? "start" : f === 1 ? "end" : "middle"); });
    s += metinSvg(lx + lw + 8, ly + lh - 1, wk ? "mm" : "kN/m²", "bn-isi-lt", "start");
    if (!wk && qem != null && qem <= ust * 1.0001) {
      const qx = lx + (qem / ust) * lw;
      s += '<path class="bn-isi-qem" d="M' + pt(qx, ly - 6) + " L" + pt(qx, ly + lh + 2) + '"/>' + metinSvg(qx, ly - 9, "q_em " + f1(qem), "bn-isi-lt bn-isi-qem-t", qx > lx + lw * 0.8 ? "end" : "middle");
    }
    if (!wk && vmin < 0) s += metinSvg(lx, ly - 9, "taralı: çekme (p < 0)", "bn-isi-lt", "start");
    kap.innerHTML = '<svg class="se-svg bn-isi-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + kacis((wk ? "Oturma" : "Taban basıncı") + " haritası; en büyük " + (wk ? f1(vmax) + " mm" : f1(vmax) + " kN/m²")) + '">' +
      '<defs>' + grd + '<pattern id="bn-isi-desen" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)"><rect width="6" height="6" class="bn-isi-desen-z"/><line x1="0" y1="0" x2="0" y2="6" class="bn-isi-desen-c"/></pattern></defs>' + s + "</svg>";
    const bil = document.getElementById("bn-temel-bilgi");
    if (bil) bil.textContent = (wk ? "Oturma w (mm), " : "Taban basıncı p = k₀·w (kN/m²), ") + temelDurumAdi(t) + ". Hücreye dokun: değer. " + (radye ? "Her hücre bir ızgara düğümünün etki alanı (" + f2(a) + " m)." : "Şerit rengi, eleman uçlarındaki değerlerin ortalaması (B = " + f2(Bs) + " m).") + (!wk && qem != null ? " Koyu kırmızı kenar: p > q_em." : "");
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
  function olaylariBagla() {
    kok.addEventListener("click", function (e) {
      const t = e.target.closest("button, [data-sankey]");
      if (!t || !kok.contains(t)) return;
      const ds = t.dataset;
      if (ds.kat != null) { D.kat = +ds.kat; D.kirisBas = null; kamera.sifirla(); yenile(); return; }
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
      if (ds.temelTip) { temelTipSec(ds.temelTip); return; }
      if (ds.temelAks) { temelAksSec(ds.temelAks); return; }
      if (ds.temelHarita) { D.temelHarita = ds.temelHarita === "w" ? "w" : "p"; temelHaritaCiz(); return; }
      if (ds.temelSekmeGit) { D.sekme = ds.temelSekmeGit; if (D.sekme === "diyagram") D.aksFiltre = ds.temelAksFiltre || ""; sekmeCiz(); return; }
      if (t.id === "bn-tam") { tamEkranDegistir(); return; }
      if (t.id === "bn-arac-ac") { D.aracKapali = !D.aracKapali; yerlesimUygula(); return; }
      if (t.id === "bn-panel-ac") { D.panelKapali = !D.panelKapali; yerlesimUygula(); return; }
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
      if (el.id === "bn-sablon") { if (el.value) sablonYukle(el.value); return; }
      if (el.id === "bn-tum-katlar") { D.tumKatlar = el.checked; return; }
      if (ds.oz) { ozellikDegistir(ds.oz, el.value); return; }
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
      if (kl === "f") { e.preventDefault(); tamEkranDegistir(); return; }
      if (k === "Escape") {
        if (D.tamEkran && !D.kirisBas && !D.secim.length && !D.firca) { tamEkranKapat(); return; }
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
        if (D.tamEkran) cekmeceUygula();
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
    olaylariBagla();
    cekmeceJesti();
    boyutIzle();
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
