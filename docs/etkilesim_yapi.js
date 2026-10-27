/* Matris Öğren · yapı analizi etkileşimleri ve alıştırmaları (docs/etkilesim_yapi.js)
 *
 * Çekirdek (etkilesim.js) yüklendikten sonra çalışır; bağımlılığı yoktur, etkilesim_se.js'ye de bağlı değildir.
 * Renkler yalnız E.renk() / E.zemin() ile (var(--sema-*)) verilir: açık ve koyu tema otomatik.
 *
 * ETKİLEŞİMLER (BICIM.md 6.3)
 *   doseme-dagilimi  plan karesi, TS 500 md. 11.4.3 45° çizgileri, kenar kirişlerine üçgen / trapez / düzgün yük,
 *                    tepe p = w·l_k/2, paylar (kN), q_eM ve q_eV, korunum Σ = w·l_k·l_u
 *   kolon-birikimi   yük alanı (iç / kenar / köşe kolon) ve kolon şeridinde kat kat gelen G, Q okları, kümülatif N,
 *                    TS 498:2021 Çizelge 7 hareketli yük azaltması β
 *   deprem-spektrumu TBDY 2018 yatay elastik tasarım spektrumu S_ae(T) ve azaltılmış S_aR(T) = S_ae/R_a:
 *                    S_S, S_1, zemin sınıfı (Tablo 2.1/2.2 → F_S, F_1), R, I, D kaydırıcıları → S_DS, S_D1, T_A, T_B, T_p noktası
 *   kombinasyon-zarfi  G, Q, E moment diyagramları (istasyon değerleri), katsayı kaydırıcıları, kendi kombinasyonun, TS 500 (6.3) ve
 *                    TBDY (4.11)/(4.12) zarfı; en büyük / en küçük eğriler belirleyen ailenin renginde, kesit tablosu
 *   ruzgar-kat-kuvveti TS 498:2021 md. 14: q(z) Çizelge 4 basamakları, F_i = C·q(z_i)·B·h_pay, kat kesmesi, devrilme momenti
 *   kat-kuvvetleri   TBDY 2018 md. 4.7: T_pA, S_aR, V_tE ≥ 0,04·I·S_DS·W_t, ΔF_NE, ters üçgen F_iE (m_i·H_i), kat kesmesi V_i
 *
 * ALIŞTIRMALAR (BICIM.md 7): alistirma:doseme-esdeger, alistirma:kombinasyon, alistirma:deprem-vt
 *
 * Birimler: kN, m, kN/m, kN/m². Döşeme yükü w kN/m²; kısa kenar l_k, uzun kenar l_u, m = l_u / l_k.
 */
(function () {
  "use strict";
  var E = typeof window !== "undefined" ? window.Etkilesim : (typeof globalThis !== "undefined" ? globalThis.Etkilesim : undefined);
  if (!E) return;

  const el = E.el, svg = E.svg, sahne = E.sahne, ok = E.ok, yazi = E.yazi, renk = E.renk, zemin = E.zemin;
  const kaydirici = E.kaydirici, dugme = E.dugme, secici = E.secici, Kesir = E.Kesir, Mat = E.Mat;

  /* ================================================================== yardımcılar */

  const CSS = [
    ".ky-kap{display:grid;gap:10px;min-width:0;max-width:100%}",
    ".ky-kap>*{min-width:0}",
    ".ky-sahne{background:var(--kart,#fff);border:1px solid var(--cizgi,#d9e1ee);border-radius:12px;padding:8px;overflow:hidden}",
    ".ky-svg{display:block;margin:0 auto;max-width:100%;height:auto;overflow:visible}",
    ".ky-iki{display:flex;flex-wrap:wrap;gap:10px}",
    ".ky-iki>*{flex:1 1 280px;min-width:0}",
    ".ky-ayar{display:grid;grid-template-columns:minmax(0,1fr);gap:0 20px}",
    "@media (min-width:640px){.ky-ayar{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}",
    ".ky-ayar .kx-kaydirici{margin:6px 0}",
    ".ky-satir{display:flex;flex-wrap:wrap;gap:8px;align-items:center}",
    ".ky-formul{min-width:0;max-width:100%;overflow-x:auto;overflow-y:hidden;font-size:.95em}",
    ".ky-formul .kx-tex-blok{margin:2px 0;padding:2px 0}",
    ".ky-bilgi{margin:0;padding:8px 12px;border-radius:10px;background:var(--ana-acik,#e4ebfa);color:var(--metin,#15213a);font-size:.93em}",
    ".ky-not{margin:0;color:var(--soluk,#5b6b85);font-size:.88em}",
    ".kx-kok svg text.ky-halo{paint-order:stroke;stroke:var(--kart,#fff);stroke-width:3px;stroke-linejoin:round}",
    ".ky-tablo{border-collapse:collapse;width:100%;font-size:.88em;font-variant-numeric:tabular-nums}",
    ".ky-tablo th,.ky-tablo td{padding:3px 6px;border-bottom:1px solid var(--cizgi,#d9e1ee);text-align:left;vertical-align:top}",
    ".ky-tablo th{color:var(--soluk,#5b6b85);font-weight:600}",
    "@media (prefers-reduced-motion:reduce){.ky-kap *{transition:none!important}}"
  ].join("\n");

  function kur(kok) {
    E.stilEkle("etkilesim-yapi-stil", CSS);
    const k = el("div", { class: "ky-kap" });
    kok.appendChild(k);
    return k;
  }
  function kart() { return el("div", { class: "ky-sahne" }, Array.prototype.slice.call(arguments)); }
  function sv(gen, yuk, etiket) { const s = sahne(gen, yuk, etiket); s.classList.add("ky-svg"); return s; }
  function svBoyut(s, gen, yuk) {
    s.setAttribute("viewBox", "0 0 " + gen + " " + yuk);
    s.setAttribute("width", gen);
    s.setAttribute("height", yuk);
  }
  function formulKutu() { return el("div", { class: "ky-formul" }); }
  function texYaz(kutu, kaynak) { E.tex(kutu, kaynak, true); }
  function satir() { return el("div", { class: "ky-satir" }, Array.prototype.slice.call(arguments)); }
  function bos(d) { while (d.firstChild) d.removeChild(d.firstChild); }
  function r2(x) { return Math.round(x * 100) / 100; }
  function kenet(x, alt, ust) { return x < alt ? alt : x > ust ? ust : x; }
  function sayiP(x, vars, alt, ust) {
    let v = typeof x === "string" ? Number(x.replace(",", ".")) : Number(x);
    if (x === null || x === undefined || x === "" || !isFinite(v)) v = vars;
    return kenet(v, alt, ust);
  }
  const f = (x, b) => E.sayi(x, b || 4);
  const ft = x => E.sayiTex(x, 4);

  function cizgi(x1, y1, x2, y2, o) {
    o = o || {};
    return svg("line", {
      x1: r2(x1), y1: r2(y1), x2: r2(x2), y2: r2(y2), stroke: renk(o.renk || "metin"), "stroke-width": o.kal || 1.5,
      "stroke-dasharray": o.kesik ? (o.kesik === true ? "5 4" : o.kesik) : null, "stroke-linecap": "round", opacity: o.opak === undefined ? null : o.opak
    });
  }
  function yol(d, o) {
    o = o || {};
    return svg("path", {
      d, fill: o.dolgu ? zemin(o.dolgu) : "none", stroke: o.renk === null ? "none" : renk(o.renk || "metin"), "stroke-width": o.kal || 1.5,
      "stroke-dasharray": o.kesik ? "5 4" : null, "stroke-linecap": "round", "stroke-linejoin": "round", opacity: o.opak === undefined ? null : o.opak
    });
  }
  function dikdortgen(x, y, w, h, o) {
    o = o || {};
    return svg("rect", {
      x: r2(x), y: r2(y), width: r2(Math.max(0, w)), height: r2(Math.max(0, h)), rx: o.rx === undefined ? 0 : o.rx,
      fill: o.dolgu ? zemin(o.dolgu) : "none", stroke: o.renk ? renk(o.renk) : "none", "stroke-width": o.kal || 1.5,
      "stroke-dasharray": o.kesik ? "5 4" : null, opacity: o.opak === undefined ? null : o.opak
    });
  }
  function yaziH(x, y, metin, o) {
    o = Object.assign({}, o);
    o.sinif = ["ky-halo", o.sinif].filter(Boolean).join(" ");
    return yazi(x, y, metin, o);
  }
  function sl(etiket, min, max, adim, deger, birim, isl, bicim) {
    return kaydirici({ etiket, min, max, adim, deger, birim, bicim: bicim || (v => String(+(+v).toPrecision(4))), degisince: isl });
  }
  function nokta(p) { return p.map(q => r2(q[0]) + " " + r2(q[1])).join(" L"); }

  /* TS 500 md. 11.4.3 dağıtımı: bir panelin dört kenarına giden yükler (yapi._doseme_dagit ile aynı kurallar). */
  function dagit(lx, ly, w, dagitim) {
    const lk = Math.min(lx, ly), lu = Math.max(lx, ly), m = lu / lk;
    const tip = dagitim === "cift" || dagitim === "tek" ? dagitim : (m <= 2 + 1e-9 ? "cift" : "tek");
    const p = w * lk / 2;
    const kenar = (L) => {
      const kisa = Math.abs(L - lk) < 1e-9;
      let sekil;
      if (tip === "cift") sekil = (kisa || Math.abs(m - 1) < 1e-9) ? "ucgen" : "trapez";
      else sekil = kisa ? "yok" : "duzgun";
      let qM = 0, qV = 0, pay = 0;
      if (sekil === "ucgen") { qM = w * lk / 3; qV = w * lk / 4; pay = w * lk * lk / 4; }
      else if (sekil === "trapez") { qM = p * (1 - 1 / (3 * m * m)); qV = p * (1 - 1 / (2 * m)); pay = p * (lu - lk / 2); }
      else if (sekil === "duzgun") { qM = p; qV = p; pay = p * L; }
      return { L, kisa, sekil, qM, qV, pay };
    };
    return { lk, lu, m, tip, p, x: kenar(lx), y: kenar(ly), toplam: w * lx * ly };
  }

  const SEKIL_AD = { ucgen: "üçgen", trapez: "trapez", duzgun: "düzgün", yok: "yük yok" };
  const SEKIL_AILE = { ucgen: "a", trapez: "b", duzgun: "c", yok: "sil" };

  /* ================================================================== 1. doseme-dagilimi */

  E.kaydet("doseme-dagilimi", function (kok, p) {
    const kap = kur(kok);
    let lx = sayiP(p.lx, 5, 1, 16), ly = sayiP(p.ly, 4, 1, 16), w = sayiP(p.w, 5, 0.5, 30);
    let dagitim = p.dagitim === "cift" || p.dagitim === "tek" ? p.dagitim : "otomatik";
    const W = 420, H = 330, KUTU = 200, HP = 34, CX = 210, CY = 160;
    const sd = sv(W, H, "Döşeme planı: 45° çizgileri ve kenar kirişlerine giden üçgen, trapez ya da düzgün yükler");
    const dyn = svg("g");
    sd.appendChild(dyn);
    const formul = formulKutu();
    const bilgi = el("p", { class: "ky-bilgi" });
    let slx, sly, slw, sec;

    /* Kenar üstüne yük şekli: kenar (ax, ay) → (bx, by) doğrultusunda, dışa normal (nx, ny) yönünde HP yükseklikte. */
    function sekilCiz(ax, ay, bx, by, nx, ny, d, lkPx) {
      if (d.sekil === "yok") return;
      const L = Math.hypot(bx - ax, by - ay), ux = (bx - ax) / L, uy = (by - ay) / L;
      const pt = (t, h) => [ax + ux * t + nx * h, ay + uy * t + ny * h];
      let pts;
      if (d.sekil === "ucgen") pts = [[ax, ay], pt(L / 2, HP), [bx, by]];
      else if (d.sekil === "trapez") pts = [[ax, ay], pt(lkPx / 2, HP), pt(L - lkPx / 2, HP), [bx, by]];
      else pts = [[ax, ay], pt(0, HP), pt(L, HP), [bx, by]];
      const aile = SEKIL_AILE[d.sekil];
      dyn.appendChild(yol("M" + nokta(pts) + " Z", { dolgu: aile, renk: aile, kal: 1.6 }));
      const adet = Math.max(3, Math.round(L / 22));
      for (let i = 1; i < adet; i++) {
        const t = L * i / adet;
        let h = HP;
        if (d.sekil === "ucgen") h = HP * (t <= L / 2 ? t / (L / 2) : (L - t) / (L / 2));
        else if (d.sekil === "trapez") h = HP * Math.min(1, t / (lkPx / 2), (L - t) / (lkPx / 2));
        if (h < 4) continue;
        const a = pt(t, h), b = pt(t, 2);
        dyn.appendChild(ok(a[0], a[1], b[0], b[1], { renk: aile, kalinlik: 1.2, bas: 4 }));
      }
      const c = pt(L / 2, HP + 12);
      dyn.appendChild(yaziH(c[0], c[1], SEKIL_AD[d.sekil] + " · " + f(d.pay) + " kN", { renk: aile, boyut: 10.5, kalin: true }));
    }

    function ciz() {
      const d = dagit(lx, ly, w, dagitim);
      const olc = KUTU / Math.max(lx, ly);
      const pw = lx * olc, ph = ly * olc, x0 = CX - pw / 2, y0 = CY - ph / 2, x1 = x0 + pw, y1 = y0 + ph;
      const lkPx = d.lk * olc;
      bos(dyn);
      dyn.appendChild(dikdortgen(x0, y0, pw, ph, { dolgu: "cizgi", renk: "metin", kal: 2 }));
      // kirişler (kalın) ve köşe kolonları
      [[x0, y0, x1, y0], [x0, y1, x1, y1], [x0, y0, x0, y1], [x1, y0, x1, y1]].forEach(s => dyn.appendChild(cizgi(s[0], s[1], s[2], s[3], { renk: "metin", kal: 4 })));
      [[x0, y0], [x1, y0], [x0, y1], [x1, y1]].forEach(q => dyn.appendChild(dikdortgen(q[0] - 5, q[1] - 5, 10, 10, { dolgu: "metin", renk: "metin", kal: 1 })));
      if (d.tip === "cift") {
        const h = lkPx / 2;
        // köşelerden 45° çizgiler ve sırt çizgisi
        dyn.appendChild(cizgi(x0, y0, x0 + h, y0 + h, { renk: "a", kal: 1.6, kesik: true }));
        dyn.appendChild(cizgi(x1, y0, x1 - h, y0 + h, { renk: "a", kal: 1.6, kesik: true }));
        dyn.appendChild(cizgi(x0, y1, x0 + h, y1 - h, { renk: "a", kal: 1.6, kesik: true }));
        dyn.appendChild(cizgi(x1, y1, x1 - h, y1 - h, { renk: "a", kal: 1.6, kesik: true }));
        if (pw > ph + 1e-6) dyn.appendChild(cizgi(x0 + h, y0 + h, x1 - h, y0 + h, { renk: "a", kal: 1.6, kesik: true }));
        else if (ph > pw + 1e-6) dyn.appendChild(cizgi(x0 + h, y0 + h, x0 + h, y1 - h, { renk: "a", kal: 1.6, kesik: true }));
        dyn.appendChild(yaziH(x0 + 14, y0 + 14, "45°", { renk: "a", boyut: 10 }));
      } else {
        // tek doğrultulu: kısa doğrultuda şerit okları
        const yatay = lx < ly; // kısa kenar x ise yük x doğrultusunda taşınır
        const adet = 4;
        for (let i = 1; i <= adet; i++) {
          if (yatay) {
            const y = y0 + ph * i / (adet + 1);
            dyn.appendChild(ok(CX, y, x0 + 8, y, { renk: "c", kalinlik: 1.4, bas: 5, kesik: false }));
            dyn.appendChild(ok(CX, y, x1 - 8, y, { renk: "c", kalinlik: 1.4, bas: 5 }));
          } else {
            const x = x0 + pw * i / (adet + 1);
            dyn.appendChild(ok(x, CY, x, y0 + 8, { renk: "c", kalinlik: 1.4, bas: 5 }));
            dyn.appendChild(ok(x, CY, x, y1 - 8, { renk: "c", kalinlik: 1.4, bas: 5 }));
          }
        }
      }
      dyn.appendChild(yaziH(CX, CY, "w = " + f(w) + " kN/m²", { boyut: 12, kalin: true }));
      dyn.appendChild(yaziH(CX, CY + 16, "m = " + f(d.m, 3) + (d.tip === "cift" ? " ≤ 2: çift doğrultulu" : " > 2: tek doğrultulu"), { boyut: 10.5, renk: "soluk" }));
      // kenar yükleri: alt ve üst (x kirişleri), sol ve sağ (y kirişleri)
      sekilCiz(x0, y1, x1, y1, 0, 1, d.x, lkPx);
      sekilCiz(x0, y0, x1, y0, 0, -1, d.x, lkPx);
      sekilCiz(x0, y0, x0, y1, -1, 0, d.y, lkPx);
      sekilCiz(x1, y0, x1, y1, 1, 0, d.y, lkPx);
      // ölçüler
      dyn.appendChild(yaziH(CX, y0 - HP - 32, "l_x = " + f(lx) + " m" + (d.x.kisa ? " (kısa)" : " (uzun)"), { boyut: 11, renk: "soluk" }));
      dyn.appendChild(yaziH(x1 + 6, y1 + HP + 12, "l_y = " + f(ly) + " m" + (d.y.kisa ? " (kısa)" : " (uzun)"), { boyut: 11, renk: "soluk", hiza: "sol" }));
      if (d.tip === "cift" || d.tip === "tek") dyn.appendChild(yaziH(CX, y1 + HP + 30, "tepe p = w·l_k/2 = " + f(d.p) + " kN/m", { boyut: 11.5, renk: "metin", kalin: true }));

      /* formüller */
      const kisa = d.x.kisa ? d.x : d.y, uzun = d.x.kisa ? d.y : d.x;
      let tx = "\\begin{aligned}m&=\\tfrac{l_u}{l_k}=\\tfrac{" + ft(d.lu) + "}{" + ft(d.lk) + "}=" + ft(d.m) +
        (d.tip === "cift" ? "\\le 2\\ (\\text{çift doğrultulu})\\\\" : ">2\\ (\\text{tek doğrultulu})\\\\") +
        "\\kutua{p}&=\\tfrac{w\\,l_k}{2}=\\tfrac{" + ft(w) + "\\cdot" + ft(d.lk) + "}{2}=" + ft(d.p) + "\\ \\text{kN/m}\\\\";
      if (d.tip === "cift") {
        tx += "\\text{üçgen (kısa):}\\ & \\ka{q_{eM}=\\tfrac{w\\,l_k}{3}}=" + ft(kisa.qM) + ",\\quad \\kb{q_{eV}=\\tfrac{w\\,l_k}{4}}=" + ft(kisa.qV) + "\\\\" +
          "& \\text{pay } \\tfrac{w\\,l_k^2}{4}=" + ft(kisa.pay) + "\\ \\text{kN}\\\\";
        if (Math.abs(d.m - 1) < 1e-9) {
          tx += "\\text{kare panel:}\\ & \\text{dört kenar da üçgen; toplam } 4\\cdot" + ft(kisa.pay) + "=\\kutuc{" + ft(d.toplam) + "}=w\\,l_k\\,l_u\\ \\checkmark\\end{aligned}";
        } else {
          tx += "\\text{trapez (uzun):}\\ & \\ka{q_{eM}=\\tfrac{w\\,l_k}{2}\\big(1-\\tfrac{1}{3m^2}\\big)}=" + ft(uzun.qM) + "\\\\" +
            "& \\kb{q_{eV}=\\tfrac{w\\,l_k}{2}\\big(1-\\tfrac{1}{2m}\\big)}=" + ft(uzun.qV) + "\\\\" +
            "& \\text{pay } \\tfrac{w\\,l_k}{2}\\big(l_u-\\tfrac{l_k}{2}\\big)=" + ft(uzun.pay) + "\\ \\text{kN}\\\\" +
            "\\text{korunum:}\\ & 2\\cdot" + ft(kisa.pay) + "+2\\cdot" + ft(uzun.pay) + "=\\kutuc{" + ft(d.toplam) + "}=w\\,l_k\\,l_u\\ \\checkmark\\end{aligned}";
        }
      } else {
        tx += "\\text{düzgün (uzun):}\\ & \\kc{q=\\tfrac{w\\,l_k}{2}}=" + ft(uzun.qM) + "\\ \\text{kN/m}\\\\ & \\text{pay } q\\,l_u=" + ft(uzun.pay) + "\\ \\text{kN}\\\\" +
          "\\text{kısa kenar:}\\ & \\ksil{0}\\\\" +
          "\\text{korunum:}\\ & 2\\cdot" + ft(uzun.pay) + "=\\kutuc{" + ft(d.toplam) + "}=w\\,l_k\\,l_u\\ \\checkmark\\end{aligned}";
      }
      texYaz(formul, tx);
      bilgi.textContent = d.tip === "cift"
        ? "TS 500 md. 11.4.3: köşelerden 45° çizgiler kısa kenara üçgen, uzun kenara trapez düşürür. q_eM ve q_eV yalnız el hesabı kısayoludur; sonlu elemanda gerçek şekil parçalı yük olarak verilir."
        : "m > 2 (TS 500 md. 11.2.1): plak yalnız kısa doğrultuda taşır; yük uzun kenar kirişlerine düzgün w·l_k/2 olarak gider, kısa kenar kirişleri döşemeden pay almaz (öz ağırlık ve duvar yine vardır).";
    }

    slx = sl("$l_x$", 2, 12, 0.5, lx, "m", v => { lx = v; ciz(); });
    sly = sl("$l_y$", 2, 12, 0.5, ly, "m", v => { ly = v; ciz(); });
    slw = sl("$w$ (döşeme yükü)", 1, 15, 0.5, w, "kN/m²", v => { w = v; ciz(); });
    sec = secici([{ deger: "otomatik", etiket: "dağıtım: otomatik" }, { deger: "cift", etiket: "çift" }, { deger: "tek", etiket: "tek" }], dagitim, v => { dagitim = v; ciz(); });
    function ayarla(nlx, nly, nw, nd) {
      lx = nlx; ly = nly; w = nw; dagitim = nd;
      slx.ayarla(lx, true); sly.ayarla(ly, true); slw.ayarla(w, true); sec.ayarla(dagitim, true);
      ciz();
    }
    kap.appendChild(kart(sd));
    kap.appendChild(satir(
      dugme("D1 paneli (5×4, w = 5)", () => ayarla(5, 4, 5, "otomatik"), { baslik: "Ders örneği: m = 1.25, tepe 10 kN/m" }),
      dugme("Kare 4×4", () => ayarla(4, 4, 5, "otomatik"), { baslik: "m = 1: dört kenar da üçgen" }),
      dugme("Tek doğrultulu 8×3", () => ayarla(8, 3, 5.25, "otomatik"), { baslik: "m = 2.67 > 2: düzgün yük yalnız uzun kenarlara" }),
      sec.kok));
    kap.appendChild(el("div", { class: "ky-ayar" }, slx.kok, sly.kok, slw.kok));
    kap.appendChild(bilgi);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ky-not" }, "Mavi üçgen kısa kenar kirişine, turuncu trapez uzun kenar kirişine giden yüktür; yükseklik tepe değeri p'dir (her kenarda aynı). " +
      "Şekil üstündeki sayı o kirişe giden toplam kN'dur; dördünün toplamı panel yüküne eşittir."));
    ciz();
  }, {
    baslik: "Döşemeden kirişe: 45° kuralı",
    aciklama: "Panel kenarlarını ve yükü değiştir; 45° çizgileri, kirişlere giden üçgen/trapez yükler, q_eM, q_eV ve korunum canlı güncellenir.",
    varsayilan: { lx: 5, ly: 4, w: 5, dagitim: "otomatik" }
  });

  /* ================================================================== 2. kolon-birikimi */

  /* TS 498:2021 md. 16 Çizelge 7, (a) konut / büro / işhanı: taşınan tam kat sayısına göre β */
  const BETA_A = [1, 1, 1, 0.95, 0.88, 0.80, 0.71, 0.65, 0.60, 0.60, 0.60, 0.60];
  const betaOf = n => n <= BETA_A.length ? BETA_A[n - 1] : 0.60;
  const KONUM_KATSAYI = { ic: 1, kenar: 0.5, kose: 0.25 };
  const KONUM_AD = { ic: "iç kolon", kenar: "kenar kolonu", kose: "köşe kolonu" };

  E.kaydet("kolon-birikimi", function (kok, p) {
    const kap = kur(kok);
    let kat = Math.round(sayiP(p.kat, 4, 1, 8)), g = sayiP(p.g, 5, 0.5, 20), q = sayiP(p.q, 2, 0, 10);
    let lx = sayiP(p.lx, 5, 2, 12), ly = sayiP(p.ly, 4, 2, 12);
    let konum = KONUM_KATSAYI[p.konum] ? p.konum : "ic";
    let beta = p.beta === false || p.beta === "false" || p.beta === 0 ? false : true;
    const qEm = sayiP(p.q_em, 200, 50, 1000);
    const PW = 230, PH = 210;
    const sp = sv(PW, PH, "Plan: aks ızgarası ve kolonun yük alanı");
    const pdyn = svg("g");
    sp.appendChild(pdyn);
    const se = sv(260, 300, "Kolon şeridi: kat kat gelen yükler ve kümülatif eksenel kuvvet");
    const sdyn = svg("g");
    se.appendChild(sdyn);
    const formul = formulKutu();
    const bilgi = el("p", { class: "ky-bilgi" });
    let slKat, slG, slQ, slLx, slLy, secK, secB;

    function hesap() {
      const A = lx * ly * KONUM_KATSAYI[konum];
      const Gk = g * A, Qk = q * A;
      const katlar = []; // üstten alta: segment i (i = 1 en üst) n_i = i kat taşır
      for (let i = 1; i <= kat; i++) {
        const b = beta ? betaOf(i) : 1;
        katlar.push({ n: i, NG: i * Gk, NQ_ham: i * Qk, beta: b, NQ: b * i * Qk });
      }
      return { A, Gk, Qk, katlar, son: katlar[kat - 1] };
    }

    function planCiz(h) {
      bos(pdyn);
      const olc = Math.min(70 / lx, 60 / ly, 14), X0 = 30, Y0 = 26;
      const xs = [X0, X0 + lx * olc, X0 + 2 * lx * olc], ys = [Y0, Y0 + ly * olc, Y0 + 2 * ly * olc];
      // yük alanı
      let ax0, ay0, aw, ah;
      if (konum === "ic") { ax0 = xs[1] - lx * olc / 2; ay0 = ys[1] - ly * olc / 2; aw = lx * olc; ah = ly * olc; }
      else if (konum === "kenar") { ax0 = xs[1] - lx * olc / 2; ay0 = ys[0]; aw = lx * olc; ah = ly * olc / 2; }
      else { ax0 = xs[0]; ay0 = ys[0]; aw = lx * olc / 2; ah = ly * olc / 2; }
      pdyn.appendChild(dikdortgen(ax0, ay0, aw, ah, { dolgu: "c", renk: "c", kal: 1.6, kesik: true }));
      xs.forEach(x => pdyn.appendChild(cizgi(x, ys[0] - 10, x, ys[2] + 10, { renk: "soluk", kal: 1, kesik: "3 3" })));
      ys.forEach(y => pdyn.appendChild(cizgi(xs[0] - 10, y, xs[2] + 10, y, { renk: "soluk", kal: 1, kesik: "3 3" })));
      // kirişler
      ys.forEach(y => pdyn.appendChild(cizgi(xs[0], y, xs[2], y, { renk: "metin", kal: 2.2 })));
      xs.forEach(x => pdyn.appendChild(cizgi(x, ys[0], x, ys[2], { renk: "metin", kal: 2.2 })));
      // kolonlar
      const kx = konum === "kose" ? xs[0] : xs[1], ky = konum === "ic" ? ys[1] : ys[0];
      xs.forEach(x => ys.forEach(y => pdyn.appendChild(dikdortgen(x - 4, y - 4, 8, 8, { dolgu: "cizgi", renk: "metin", kal: 1 }))));
      pdyn.appendChild(dikdortgen(kx - 6, ky - 6, 12, 12, { dolgu: "c", renk: "c", kal: 2 }));
      pdyn.appendChild(yaziH(xs[1], ys[0] - 16, "l_x = " + f(lx) + " m", { boyut: 10.5, renk: "soluk" }));
      pdyn.appendChild(yaziH(xs[2] + 4, ys[1], "l_y = " + f(ly), { boyut: 10.5, renk: "soluk", hiza: "sol" }));
      pdyn.appendChild(yaziH(konum === "kose" ? ax0 + aw + 6 : ax0 + aw / 2, konum === "ic" ? ay0 + ah / 2 + 16 : ay0 + ah + 14, "A_trib = " + f(h.A) + " m²",
        { boyut: 11, renk: "c", kalin: true, hiza: konum === "kose" ? "sol" : "orta" }));
      pdyn.appendChild(yaziH(PW / 2, PH - 8, KONUM_AD[konum] + ": komşu açıklıkların yarısı", { boyut: 10.5, renk: "soluk" }));
      const ol = 2 * lx * olc + 2 * X0 + 40;
      svBoyut(sp, Math.max(PW, ol), Math.max(PH, 2 * ly * olc + Y0 + 34));
    }

    function seritCiz(h) {
      bos(sdyn);
      const X = 120, KY = 44, YT = 34, YZ = YT + kat * KY, GW = 24;
      const Nmax = h.son.NG + h.son.NQ || 1;
      // katlar ve segmentler
      for (let i = 0; i < kat; i++) {
        const s = h.katlar[i], yUst = YT + i * KY, yAlt = yUst + KY;
        const N = s.NG + s.NQ, gw = 10 + GW * N / Nmax;
        sdyn.appendChild(dikdortgen(X - gw / 2, yUst + 8, gw, KY - 8, { dolgu: "c", renk: "c", kal: 1.4 }));
        // kat döşemesi çizgisi
        sdyn.appendChild(cizgi(X - 46, yUst + 8, X + 46, yUst + 8, { renk: "metin", kal: 2.4 }));
        sdyn.appendChild(yaziH(X - 52, yUst + 8, "kat " + (kat - i), { boyut: 10, renk: "soluk", hiza: "sag" }));
        // gelen yükler: G mavi, Q turuncu
        sdyn.appendChild(ok(X - 14, yUst - 16, X - 14, yUst + 4, { renk: "a", kalinlik: 2, bas: 6 }));
        sdyn.appendChild(ok(X + 14, yUst - 16, X + 14, yUst + 4, { renk: "b", kalinlik: 2, bas: 6 }));
        sdyn.appendChild(yaziH(X - 20, yUst - 20, "G " + f(h.Gk, 3), { boyut: 9.5, renk: "a", hiza: "sag" }));
        sdyn.appendChild(yaziH(X + 20, yUst - 20, "Q " + f(h.Qk, 3), { boyut: 9.5, renk: "b", hiza: "sol" }));
        // kümülatif N
        sdyn.appendChild(yaziH(X + 50, yUst + KY / 2 + 6, "N = " + f(N, 4) + " kN", { boyut: 10.5, renk: "c", kalin: true, hiza: "sol" }));
        sdyn.appendChild(yaziH(X + 50, yUst + KY / 2 + 19, f(s.NG, 4) + " + " + (s.beta < 1 ? s.beta.toFixed(2) + "·" : "") + f(s.NQ_ham, 4), { boyut: 9, renk: "soluk", hiza: "sol" }));
      }
      // temel
      sdyn.appendChild(dikdortgen(X - 34, YZ + 8, 68, 12, { dolgu: "cizgi", renk: "metin", kal: 1.2 }));
      sdyn.appendChild(cizgi(X - 60, YZ + 20, X + 60, YZ + 20, { renk: "metin", kal: 1.4 }));
      for (let x = X - 56; x <= X + 56; x += 12) sdyn.appendChild(cizgi(x, YZ + 20, x - 6, YZ + 27, { renk: "soluk", kal: 1 }));
      sdyn.appendChild(ok(X, YZ - 6, X, YZ + 6, { renk: "c", kalinlik: 2.4, bas: 7 }));
      sdyn.appendChild(yaziH(X, YZ + 42, "N_taban = " + f(h.son.NG + h.son.NQ, 4) + " kN", { boyut: 11, renk: "c", kalin: true }));
      svBoyut(se, 260, YZ + 56);
    }

    function ciz() {
      const h = hesap();
      planCiz(h);
      seritCiz(h);
      const s = h.son, N = s.NG + s.NQ, Agerek = N / qEm;
      let tx = "\\begin{aligned}A_{\\text{trib}}&=" + (konum === "ic" ? "l_x\\,l_y" : konum === "kenar" ? "\\tfrac{l_x\\,l_y}{2}" : "\\tfrac{l_x\\,l_y}{4}") +
        "=" + ft(h.A) + "\\ \\text{m}^2\\\\ \\ka{G_{\\text{kat}}}&=g\\,A=" + ft(h.Gk) + ",\\quad \\kb{Q_{\\text{kat}}}=q\\,A=" + ft(h.Qk) + "\\ \\text{kN}\\\\" +
        "N_{\\text{taban}}&=n\\,G_{\\text{kat}}+\\beta(n)\\,n\\,Q_{\\text{kat}}\\\\&=" + kat + "\\cdot" + ft(h.Gk) + "+" + (s.beta < 1 ? s.beta.toFixed(2) + "\\cdot" : "") + kat + "\\cdot" + ft(h.Qk) +
        "=\\kutuc{" + ft(N) + "}\\ \\text{kN}" + (s.beta < 1 ? "\\\\&\\quad(\\beta=" + s.beta.toFixed(2) + ":\\ \\text{Çizelge 7, " + kat + " kat})" : "") + "\\\\" +
        "\\text{temel:}\\ & A\\ge\\tfrac{N}{q_{em}}=\\tfrac{" + ft(N) + "}{" + ft(qEm) + "}=" + ft(Agerek) + "\\ \\text{m}^2\\\\&\\Rightarrow\\ B=L\\ge" + ft(Math.sqrt(Agerek)) + "\\ \\text{m}\\end{aligned}";
      texYaz(formul, tx);
      bilgi.textContent = (beta && kat > 3)
        ? "Üçten çok kat taşıyan segmentlerde hareketli yük β ile azaltıldı (TS 498:2021 md. 16 Çizelge 7, konut/büro: 4 kat 0.95, 5 kat 0.88, 6 kat 0.80, 7 kat 0.71, 8 kat 0.65). Döşeme ve kirişte azaltma yoktur."
        : (beta ? "Üç kata kadar β = 1: azaltma başlamaz. Kat sayısını 4'e çıkar." : "β uygulanmıyor: hareketli yük tam toplanır (depo ve ağır atölyede zorunlu).");
    }

    slKat = sl("kat sayısı $n$", 1, 8, 1, kat, "", v => { kat = Math.round(v); ciz(); }, v => String(Math.round(v)));
    slG = sl("$g$ (sabit)", 2, 12, 0.5, g, "kN/m²", v => { g = v; ciz(); });
    slQ = sl("$q$ (hareketli)", 0, 7.5, 0.5, q, "kN/m²", v => { q = v; ciz(); });
    slLx = sl("$l_x$", 3, 9, 0.5, lx, "m", v => { lx = v; ciz(); });
    slLy = sl("$l_y$", 3, 9, 0.5, ly, "m", v => { ly = v; ciz(); });
    secK = secici([{ deger: "ic", etiket: "iç" }, { deger: "kenar", etiket: "kenar" }, { deger: "kose", etiket: "köşe" }], konum, v => { konum = v; ciz(); });
    secB = secici([{ deger: true, etiket: "β uygula" }, { deger: false, etiket: "β yok" }], beta, v => { beta = v; ciz(); });
    function ayarla(nk, ng, nq, nlx, nly, nkon) {
      kat = nk; g = ng; q = nq; lx = nlx; ly = nly; konum = nkon;
      slKat.ayarla(kat, true); slG.ayarla(g, true); slQ.ayarla(q, true); slLx.ayarla(lx, true); slLy.ayarla(ly, true); secK.ayarla(konum, true);
      ciz();
    }
    kap.appendChild(el("div", { class: "ky-iki" }, kart(sp), kart(se)));
    kap.appendChild(satir(
      dugme("Şablon B1 (2 kat, 5×4, iç)", () => ayarla(2, 5, 2, 5, 4, "ic"), { baslik: "Ders örneği 5: iç kolon B1'in yük alanı (kiriş payları hariç)" }),
      dugme("8 katlı konut", () => ayarla(8, 6, 2, 5, 5, "ic"), { baslik: "Azaltma β = 0.65" }),
      secK.kok, secB.kok));
    kap.appendChild(el("div", { class: "ky-ayar" }, slKat.kok, slG.kok, slQ.kok, slLx.kok, slLy.kok));
    kap.appendChild(bilgi);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ky-not" }, "Yük alanı yöntemi yalnız döşeme payını sayar; kiriş öz ağırlığı, duvar ve kolon öz ağırlığı gerçek hesapta eklenir (ders örneği 5). " +
      "Sonlu eleman eksenel kuvveti bundan birkaç yüzde sapar: iç kolon fazla, köşe kolon az yüklenir."));
    ciz();
  }, {
    baslik: "Kolonda yük birikimi ve yük alanı",
    aciklama: "Kat sayısı, kat yükleri, aks aralıkları ve kolon konumunu değiştir; yük alanı, kat kat gelen G ve Q, kümülatif N ve β azaltması canlı güncellenir.",
    varsayilan: { kat: 4, g: 5, q: 2, lx: 5, ly: 4, konum: "ic", beta: true }
  });

  /* ================================================================== 3. deprem-spektrumu */

  /* TBDY 2018 Tablo 2.1 (F_S) ve Tablo 2.2 (F_1), md. 2.3.3.1: ara değerler doğrusal enterpolasyon, uç sütunlar sabit
     (kaynak: scratchpad/tasarim/arastirma_tbdy2018.json; ZF için sahaya özel analiz gerekir, burada yok). */
  const TBDY_FS = { SS: [0.25, 0.5, 0.75, 1.0, 1.25, 1.5], ZA: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], ZB: [0.9, 0.9, 0.9, 0.9, 0.9, 0.9], ZC: [1.3, 1.3, 1.2, 1.2, 1.2, 1.2], ZD: [1.6, 1.4, 1.2, 1.1, 1.0, 1.0], ZE: [2.4, 1.7, 1.3, 1.1, 0.9, 0.8] };
  const TBDY_F1 = { S1: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], ZA: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], ZB: [0.8, 0.8, 0.8, 0.8, 0.8, 0.8], ZC: [1.5, 1.5, 1.5, 1.5, 1.5, 1.4], ZD: [2.4, 2.2, 2.0, 1.9, 1.8, 1.7], ZE: [4.2, 3.3, 2.8, 2.4, 2.2, 2.0] };
  const TBDY_TL = 6;
  function araDeger(xs, ys, x) {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
    for (let i = 0; i < xs.length - 1; i++) if (x >= xs[i] && x <= xs[i + 1]) return ys[i] + (x - xs[i]) / (xs[i + 1] - xs[i]) * (ys[i + 1] - ys[i]);
    return ys[ys.length - 1];
  }
  /* Spektrum parametreleri ve eğri değerleri (Denk. 2.1–2.3, 4.1, 4.8) */
  function spektrum(SS, S1, zemin, R, I, D) {
    const FS = araDeger(TBDY_FS.SS, TBDY_FS[zemin], SS), F1 = araDeger(TBDY_F1.S1, TBDY_F1[zemin], S1);
    const SDS = SS * FS, SD1 = S1 * F1, TA = 0.2 * SD1 / SDS, TB = SD1 / SDS;
    const sae = T => T <= TA ? (0.4 + 0.6 * T / TA) * SDS : T <= TB ? SDS : T <= TBDY_TL ? SD1 / T : SD1 * TBDY_TL / (T * T);
    const ra = T => T > TB ? R / I : D + (R / I - D) * T / TB;
    return { FS, F1, SDS, SD1, TA, TB, sae, ra };
  }

  E.kaydet("deprem-spektrumu", function (kok, p) {
    const kap = kur(kok);
    let SS = sayiP(p.SS, 1.0, 0.1, 2.5), S1 = sayiP(p.S1, 0.3, 0.02, 1.0), Tp = sayiP(p.Tp, 0.4, 0.05, 4), R = sayiP(p.R, 8, 1, 8), D = sayiP(p.D, 3, 1, 3);
    let zemin = TBDY_FS[p.zemin] ? p.zemin : "ZC", I = [1.0, 1.2, 1.5].indexOf(Number(p.I)) >= 0 ? Number(p.I) : 1.0;
    const W = 520, H = 320, PL = 52, PR = 16, PU = 22, PA = 40, TMAX = 3;
    const sd = sv(W, H, "TBDY 2018 yatay elastik tasarım spektrumu S_ae(T) ve azaltılmış spektrum S_aR(T)");
    const dyn = svg("g");
    sd.appendChild(dyn);
    const formul = formulKutu();
    const bilgi = el("p", { class: "ky-bilgi" });
    let sSS, sS1, sTp, sR, sD, secZ, secI;

    function ciz() {
      const s = spektrum(SS, S1, zemin, R, I, D);
      const Smax = Math.max(s.SDS, 0.2) * 1.12;
      const X = T => PL + T / TMAX * (W - PL - PR), Y = v => H - PA - v / Smax * (H - PA - PU);
      bos(dyn);
      // eksenler ve ızgara
      dyn.appendChild(cizgi(PL, Y(0), W - PR, Y(0), { renk: "metin", kal: 1.4 }));
      dyn.appendChild(cizgi(PL, Y(0), PL, PU, { renk: "metin", kal: 1.4 }));
      for (let T = 0; T <= TMAX + 1e-9; T += 0.5) { dyn.appendChild(cizgi(X(T), Y(0), X(T), Y(0) + 4, { renk: "soluk", kal: 1 })); dyn.appendChild(yaziH(X(T), Y(0) + 14, f(T, 2), { boyut: 10, renk: "soluk" })); }
      const adim = Smax > 1.5 ? 0.5 : Smax > 0.6 ? 0.25 : 0.1;
      for (let v = adim; v <= Smax + 1e-9; v += adim) { dyn.appendChild(cizgi(PL, Y(v), W - PR, Y(v), { renk: "kenar", kal: 1 })); dyn.appendChild(yaziH(PL - 6, Y(v), f(v, 3), { boyut: 10, renk: "soluk", hiza: "sag" })); }
      dyn.appendChild(yaziH(W / 2, H - 6, "T (s)", { boyut: 11, renk: "soluk" }));
      dyn.appendChild(yaziH(PL + 4, PU - 8, "S (g)", { boyut: 11, renk: "soluk", hiza: "sol" }));
      // eğriler
      const Ts = [];
      for (let T = 0; T <= TMAX + 1e-9; T += T < 0.6 ? 0.01 : 0.05) Ts.push(T);
      const sae = Ts.map(T => [X(T), Y(s.sae(T))]), sar = Ts.map(T => [X(T), Y(s.sae(T) / s.ra(T))]);
      dyn.appendChild(yol("M" + nokta(sae), { renk: "a", kal: 2.4 }));
      dyn.appendChild(yol("M" + nokta(sar), { renk: "b", kal: 2.4 }));
      // köşe periyotları
      [[s.TA, "T_A"], [s.TB, "T_B"]].forEach((k, i) => {
        dyn.appendChild(cizgi(X(k[0]), Y(0), X(k[0]), PU + 4, { renk: "soluk", kal: 1.2, kesik: true }));
        dyn.appendChild(yaziH(X(k[0]) + 3, PU + 12 + 13 * i, k[1] + " = " + f(k[0], 3) + " s", { boyut: 10, renk: "soluk", hiza: "sol" }));
      });
      // T_p noktası
      const sT = s.sae(Tp), rT = sT / s.ra(Tp);
      dyn.appendChild(cizgi(X(Tp), Y(0), X(Tp), Y(sT), { renk: "sil", kal: 1.2, kesik: true }));
      dyn.appendChild(svg("circle", { cx: r2(X(Tp)), cy: r2(Y(sT)), r: 5, fill: renk("a"), stroke: renk("kart"), "stroke-width": 1.5 }));
      dyn.appendChild(svg("circle", { cx: r2(X(Tp)), cy: r2(Y(rT)), r: 5, fill: renk("b"), stroke: renk("kart"), "stroke-width": 1.5 }));
      const sag = Tp > 2.1;
      dyn.appendChild(yaziH(X(Tp) + (sag ? -8 : 8), Y(sT) - 10, "S_ae(T_p) = " + f(sT, 3), { boyut: 11, renk: "a", kalin: true, hiza: sag ? "sag" : "sol" }));
      dyn.appendChild(yaziH(X(Tp) + (sag ? -10 : 10), Math.min(Y(rT) + 22, Y(0) - 8), "S_aR(T_p) = " + f(rT, 3), { boyut: 11, renk: "b", kalin: true, hiza: sag ? "sag" : "sol" }));
      // gösterge
      dyn.appendChild(cizgi(W - PR - 150, PU + 30, W - PR - 126, PU + 30, { renk: "a", kal: 2.4 }));
      dyn.appendChild(yaziH(W - PR - 120, PU + 30, "S_ae(T): elastik (Denk. 2.2)", { boyut: 10.5, hiza: "sol" }));
      dyn.appendChild(cizgi(W - PR - 150, PU + 46, W - PR - 126, PU + 46, { renk: "b", kal: 2.4 }));
      dyn.appendChild(yaziH(W - PR - 120, PU + 46, "S_aR(T) = S_ae / R_a(T) (Denk. 4.8)", { boyut: 10.5, hiza: "sol" }));
      // formüller
      const bolge = Tp <= s.TA ? "0 \\le T_p \\le T_A" : Tp <= s.TB ? "T_A \\le T_p \\le T_B" : Tp <= TBDY_TL ? "T_B \\le T_p \\le T_L" : "T_p \\ge T_L";
      const saeTex = Tp <= s.TA ? "\\big(0.4+0.6\\tfrac{T_p}{T_A}\\big)S_{DS}" : Tp <= s.TB ? "S_{DS}" : Tp <= TBDY_TL ? "\\tfrac{S_{D1}}{T_p}" : "\\tfrac{S_{D1}T_L}{T_p^2}";
      const raTex = Tp > s.TB ? "\\tfrac{R}{I}=\\tfrac{" + ft(R) + "}{" + ft(I) + "}" : "D+\\big(\\tfrac{R}{I}-D\\big)\\tfrac{T_p}{T_B}=" + ft(D) + "+\\big(" + ft(R / I) + "-" + ft(D) + "\\big)\\tfrac{" + ft(Tp) + "}{" + ft(s.TB) + "}";
      texYaz(formul, "\\begin{aligned}" +
        "\\kutua{S_{DS}}&=S_S\\,F_S=" + ft(SS) + "\\cdot" + ft(s.FS) + "=" + ft(s.SDS) + ",\\qquad \\kutua{S_{D1}}=S_1\\,F_1=" + ft(S1) + "\\cdot" + ft(s.F1) + "=" + ft(s.SD1) + "\\\\" +
        "T_A&=0.2\\,\\tfrac{S_{D1}}{S_{DS}}=" + ft(s.TA) + "\\ \\text{s},\\qquad T_B=\\tfrac{S_{D1}}{S_{DS}}=" + ft(s.TB) + "\\ \\text{s},\\qquad T_L=6\\ \\text{s}\\\\" +
        "\\ka{S_{ae}(T_p)}&=" + saeTex + "=" + ft(sT) + "\\ g\\quad(" + bolge + ")\\\\" +
        "R_a(T_p)&=" + raTex + "=" + ft(s.ra(Tp)) + "\\\\" +
        "\\kb{S_{aR}(T_p)}&=\\tfrac{S_{ae}(T_p)}{R_a(T_p)}=\\tfrac{" + ft(sT) + "}{" + ft(s.ra(Tp)) + "}=" + ft(rT) + "\\ g\\end{aligned}");
      bilgi.textContent = "F_S = " + f(s.FS, 3) + " (Tablo 2.1, " + zemin + ", S_S = " + f(SS, 3) + "), F_1 = " + f(s.F1, 3) + " (Tablo 2.2). " +
        (Tp > s.TB ? "T_p > T_B: azaltma katsayısı tam R/I; yapı yumuşadıkça S_aR 1/T ile düşer." : Tp >= s.TA ? "T_p platoda (T_A–T_B): S_ae = S_DS; R_a T_B'ye doğru D'den R/I'ya doğrusal büyür (Denk. 4.1b)." : "T_p < T_A: çok rijit yapı; S_ae 0,4·S_DS'den başlayıp yükselir, R_a ≈ D (dayanım fazlalığı).") +
        " Taban kesme katsayısı S_aR(T_p) (g) ile V_tE = m_t·S_aR·g (Denk. 4.19; alt sınır 0,04·I·S_DS).";
    }

    sSS = sl("$S_S$ (DD-2 harita)", 0.1, 2.5, 0.05, SS, "", v => { SS = v; ciz(); });
    sS1 = sl("$S_1$ (DD-2 harita)", 0.02, 1.0, 0.01, S1, "", v => { S1 = v; ciz(); });
    sTp = sl("$T_p$ hakim periyot", 0.05, 4, 0.05, Tp, "s", v => { Tp = v; ciz(); });
    sR = sl("$R$ (Tablo 4.1)", 1, 8, 0.5, R, "", v => { R = v; ciz(); });
    sD = sl("$D$ (Tablo 4.1)", 1, 3, 0.5, D, "", v => { D = v; ciz(); });
    secZ = secici(["ZA", "ZB", "ZC", "ZD", "ZE"].map(z => ({ deger: z, etiket: z })), zemin, v => { zemin = v; ciz(); });
    secI = secici([{ deger: 1.0, etiket: "I = 1,0 (BKS 3)" }, { deger: 1.2, etiket: "I = 1,2 (BKS 2)" }, { deger: 1.5, etiket: "I = 1,5 (BKS 1)" }], I, v => { I = v; ciz(); });
    function ayarla(o) {
      SS = o.SS; S1 = o.S1; zemin = o.zemin; R = o.R; I = o.I; D = o.D; Tp = o.Tp;
      sSS.ayarla(SS, true); sS1.ayarla(S1, true); sTp.ayarla(Tp, true); sR.ayarla(R, true); sD.ayarla(D, true); secZ.ayarla(zemin, true); secI.ayarla(I, true);
      ciz();
    }
    kap.appendChild(kart(sd));
    kap.appendChild(satir(
      dugme("Ders örneği (S_S 1,2; S_1 0,35; ZC)", () => ayarla({ SS: 1.2, S1: 0.35, zemin: "ZC", R: 8, I: 1.0, D: 3, Tp: 0.38 }), { baslik: "2 katlı betonarme çerçeve, T_pA = 0,1·6^0,75" }),
      dugme("Yumuşak zemin ZE", () => ayarla({ SS: 0.8, S1: 0.25, zemin: "ZE", R: 8, I: 1.0, D: 3, Tp: 0.8 }), { baslik: "F_1 büyür, T_B sağa kayar" }),
      dugme("Hastane, ZD, R = 4", () => ayarla({ SS: 1.0, S1: 0.3, zemin: "ZD", R: 4, I: 1.5, D: 2.5, Tp: 0.5 }), { baslik: "I = 1,5 ve sınırlı süneklik: S_aR üç kat büyür" }),
      secZ.kok, secI.kok));
    kap.appendChild(el("div", { class: "ky-ayar" }, sSS.kok, sS1.kok, sTp.kok, sR.kok, sD.kok));
    kap.appendChild(bilgi);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ky-not" }, "Mavi eğri elastik tasarım spektrumu S_ae(T) (TBDY 2018 Denk. 2.2; T_A, T_B Denk. 2.3), turuncu eğri azaltılmış tasarım spektrumu S_aR(T) = S_ae(T)/R_a(T) " +
      "(Denk. 4.8; R_a Denk. 4.1). Harita katsayıları S_S, S_1 AFAD Türkiye Deprem Tehlike Haritası'ndan (tdth.afad.gov.tr) koordinatla okunur; F_S, F_1 Tablo 2.1 ve 2.2'den zemin sınıfına göre enterpolasyonla alınır."));
    ciz();
  }, {
    baslik: "TBDY 2018 tasarım spektrumu",
    aciklama: "S_S, S_1, zemin sınıfı, R, I ve D'yi değiştir; S_DS, S_D1, T_A, T_B, S_ae(T) ve S_aR(T) eğrileri ile T_p noktası canlı güncellenir.",
    varsayilan: { SS: 1.0, S1: 0.3, zemin: "ZC", R: 8, I: 1.0, D: 3, Tp: 0.4 }
  });

  /* ================================================================== 4. kombinasyon-zarfi */

  /* Varsayılan diyagramlar: 3 katlı ders binasının (betonarme-3kat-3x3) K-A2→B2/k1 kirişi (eleman 30), yapi.bina_coz
     istasyon değerleri, kN·m; pozitif = alt lif çekme. E = EX+ durumu (TBDY eşdeğer deprem, +X, +%5 dışmerkezlik). */
  const KZ_G = [-32.24, -13.886, 2.297, 14.995, 22.896, 24.906, 20.807, 10.818, -3.969, -22.24, -42.682];
  const KZ_Q = [-10.399, -4.741, 0.417, 4.576, 7.234, 7.976, 6.717, 3.542, -1.133, -6.808, -12.983];
  const KZ_E = [67.016, 54.345, 41.675, 29.004, 16.334, 3.663, -9.007, -21.678, -34.349, -47.019, -59.69];
  const KZ_AILE_AD = { a: "1,4G + 1,6Q (TS 500 Denk. 6.3)", sil: "G + Q ± E + 0,3E_Z (TBDY Denk. 4.11)", c: "0,9G ± E − 0,3E_Z (TBDY Denk. 4.12)" };

  function diziP(v, vars) {
    let a = v;
    if (typeof a === "string") a = a.split(/[\s,;]+/).filter(Boolean).map(Number);
    if (!Array.isArray(a) || a.length < 2 || a.length > 101 || a.some(x => !isFinite(Number(x)))) return vars.slice();
    return a.map(Number);
  }
  /* Zarfa giren birleşimler: TBDY 4.4.4.1'de 0,3·E_d(Z) = 0,3·(2/3)·S_DS·G = 0,2·S_DS·G (Denk. 4.10), kar ve EY bu kirişte yok. */
  function kzKombinasyonlar(SDS) {
    const kz = 0.2 * SDS;
    const g1 = 1 + kz, g2 = 0.9 - kz;
    return [
      { ad: "1.4G+1.6Q", g: 1.4, q: 1.6, e: 0, aile: "a" },
      { ad: f(g1, 3) + "G+Q+E", g: g1, q: 1, e: 1, aile: "sil" },
      { ad: f(g1, 3) + "G+Q−E", g: g1, q: 1, e: -1, aile: "sil" },
      { ad: f(g2, 3) + "G+E", g: g2, q: 0, e: 1, aile: "c" },
      { ad: f(g2, 3) + "G−E", g: g2, q: 0, e: -1, aile: "c" }
    ];
  }
  function cizgiYol(pts) { return "M" + nokta(pts); }

  E.kaydet("kombinasyon-zarfi", function (kok, p) {
    const kap = kur(kok);
    let Gd = diziP(p.G, KZ_G), Qd = diziP(p.Q, KZ_Q), Ed = diziP(p.E, KZ_E);
    if (!(Gd.length === Qd.length && Qd.length === Ed.length)) { Gd = KZ_G.slice(); Qd = KZ_Q.slice(); Ed = KZ_E.slice(); }
    const n = Gd.length, L = sayiP(p.L, 5, 0.5, 30);
    let gG = sayiP(p.gG, 1.4, -1, 2), gQ = sayiP(p.gQ, 1.6, -1, 2), gE = sayiP(p.gE, 0, -1.5, 1.5);
    let SDS = sayiP(p.SDS, 1.2, 0, 2.5), xK = sayiP(p.x, L, 0, L);
    const ara = (d, x) => {
      const t = Math.min(n - 1, Math.max(0, x / L * (n - 1)));
      const i = Math.min(n - 2, Math.floor(t)), u = t - i;
      return d[i] + u * (d[i + 1] - d[i]);
    };
    const W = 440, PL = 44, PR = 14, NS = 100;
    const X = x => PL + x / L * (W - PL - PR);
    const s1 = sv(W, 190, "Yük durumlarının moment diyagramları: G, Q ve E");
    const d1 = svg("g"); s1.appendChild(d1);
    const s2 = sv(W, 274, "Kombinasyonlar, zarf ve belirleyen bölgeler");
    const d2 = svg("g"); s2.appendChild(d2);
    const tablo = el("div", { class: "ky-formul" });
    const formul = formulKutu();
    const bilgi = el("p", { class: "ky-bilgi" });
    let sG, sQ, sE, sS, sX;

    function eksen(d, y0, ust, alt, Y, Mmax, birimYaz) {
      d.appendChild(cizgi(PL, y0, W - PR, y0, { renk: "metin", kal: 1.6 }));
      d.appendChild(cizgi(PL, ust, PL, alt, { renk: "soluk", kal: 1 }));
      [Mmax, -Mmax].forEach(v => {
        d.appendChild(cizgi(PL - 3, Y(v), PL, Y(v), { renk: "soluk", kal: 1 }));
        d.appendChild(yaziH(PL - 5, Y(v), f(v, 3), { boyut: 9.5, renk: "soluk", hiza: "sag" }));
      });
      for (let i = 0; i <= 4; i++) {
        const x = L * i / 4;
        d.appendChild(yaziH(X(x), alt + 10, f(x, 3), { boyut: 9.5, renk: "soluk" }));
      }
      if (birimYaz) d.appendChild(yaziH(W - PR, alt + 10, "x (m)", { boyut: 9.5, renk: "soluk", hiza: "sag" }));
    }

    function ciz() {
      const komb = kzKombinasyonlar(SDS);
      const xs = [], vals = [];
      for (let j = 0; j <= NS; j++) {
        const x = L * j / NS;
        const g = ara(Gd, x), q = ara(Qd, x), e = ara(Ed, x);
        xs.push(x);
        vals.push({ g, q, e, k: komb.map(c => c.g * g + c.q * q + c.e * e), oz: gG * g + gQ * q + gE * e });
      }
      const mx = vals.map(v => { let b = 0; v.k.forEach((t, i) => { if (t > v.k[b]) b = i; }); return b; });
      const mn = vals.map(v => { let b = 0; v.k.forEach((t, i) => { if (t < v.k[b]) b = i; }); return b; });

      /* 1. panel: durumlar */
      bos(d1);
      const M1 = Math.max(1e-9, ...vals.map(v => Math.max(Math.abs(v.g), Math.abs(v.q), Math.abs(v.e))));
      const y01 = 92, Y1 = v => y01 + v / M1 * 70;
      eksen(d1, y01, 18, 166, Y1, M1, true);
      [["g", "a", "G"], ["q", "b", "Q"], ["e", "c", "E (EX+)"]].forEach(([a, aile, ad]) => {
        const pts = vals.map((v, j) => [X(xs[j]), Y1(v[a])]);
        d1.appendChild(yol(cizgiYol(pts), { renk: aile, kal: 2.2 }));
        const son = vals[NS][a];
        d1.appendChild(yaziH(X(L) - 4, Y1(son) + (son >= 0 ? 10 : -10), ad + " " + f(son, 4), { boyut: 10, renk: aile, kalin: true, hiza: "sag" }));
      });
      d1.appendChild(yaziH(PL + 4, 10, "yük durumları (load case), kN·m; pozitif aşağı (alt lif çekme)", { boyut: 10, renk: "soluk", hiza: "sol" }));

      /* 2. panel: kombinasyonlar ve zarf */
      bos(d2);
      const tum = vals.reduce((a, v) => a.concat(v.k, [v.oz]), []);
      const M2 = Math.max(1e-9, ...tum.map(Math.abs));
      const y02 = 128, Y2 = v => y02 + v / M2 * 98;
      // zarf bandı
      const ust = vals.map((v, j) => [X(xs[j]), Y2(v.k[mx[j]])]);
      const alt = vals.map((v, j) => [X(xs[j]), Y2(v.k[mn[j]])]).reverse();
      d2.appendChild(yol("M" + nokta(ust.concat(alt)) + " Z", { dolgu: "cizgi", renk: null }));
      eksen(d2, y02, 24, 232, Y2, M2, true);
      // belirleyen bölgeler: max ve min eğrileri, belirleyen ailenin renginde parça parça
      [mx, mn].forEach(ind => {
        let bas = 0;
        for (let j = 1; j <= NS + 1; j++) {
          if (j === NS + 1 || ind[j] !== ind[bas]) {
            const pts = [];
            for (let t = bas; t <= Math.min(j, NS); t++) pts.push([X(xs[t]), Y2(vals[t].k[ind[t]])]);
            const c = komb[ind[bas]];
            d2.appendChild(yol(cizgiYol(pts), { renk: c.aile, kal: 3.2, kesik: c.e < 0 }));
            bas = j;
          }
        }
      });
      // kendi kombinasyonun
      d2.appendChild(yol(cizgiYol(vals.map((v, j) => [X(xs[j]), Y2(v.oz)])), { renk: "metin", kal: 1.6 }));
      // kesit (prob) çizgisi
      const vx = { g: ara(Gd, xK), q: ara(Qd, xK), e: ara(Ed, xK) };
      const kx = komb.map(c => c.g * vx.g + c.q * vx.q + c.e * vx.e), oz = gG * vx.g + gQ * vx.q + gE * vx.e;
      let iMx = 0, iMn = 0;
      kx.forEach((t, i) => { if (t > kx[iMx]) iMx = i; if (t < kx[iMn]) iMn = i; });
      d2.appendChild(cizgi(X(xK), 24, X(xK), 232, { renk: "soluk", kal: 1, kesik: "3 3" }));
      d2.appendChild(svg("circle", { cx: r2(X(xK)), cy: r2(Y2(kx[iMx])), r: 4.5, fill: renk(komb[iMx].aile), stroke: renk("kart"), "stroke-width": 1.5 }));
      d2.appendChild(svg("circle", { cx: r2(X(xK)), cy: r2(Y2(kx[iMn])), r: 4.5, fill: renk(komb[iMn].aile), stroke: renk("kart"), "stroke-width": 1.5 }));
      d2.appendChild(svg("circle", { cx: r2(X(xK)), cy: r2(Y2(oz)), r: 4, fill: renk("kart"), stroke: renk("metin"), "stroke-width": 2 }));
      // gösterge
      [["a", false, "1,4G+1,6Q"], ["sil", false, "4.11 (+E)"], ["sil", true, "4.11 (−E)"], ["c", false, "4.12 (+E)"], ["c", true, "4.12 (−E)"]].forEach((g, i) => {
        const gx = PL - 30 + i * 80, gy = 10;
        d2.appendChild(cizgi(gx, gy, gx + 18, gy, { renk: g[0], kal: 3, kesik: g[1] ? "5 4" : false }));
        d2.appendChild(yaziH(gx + 21, gy, g[2], { boyut: 9.5, renk: g[0], hiza: "sol" }));
      });
      d2.appendChild(yaziH(PL, 264, "ince koyu çizgi: kendi kombinasyonun; boş daire: kesitteki değeri", { boyut: 9.5, renk: "soluk", hiza: "sol" }));

      /* tablo: iki uç ve orta */
      bos(tablo);
      const tb = el("table", { class: "ky-tablo" });
      tb.appendChild(el("tr", null, el("th", null, "Kesit"), el("th", null, "M_max, belirleyen"), el("th", null, "M_min, belirleyen")));
      [[0, "sol uç"], [L / 2, "orta"], [L, "sağ uç"]].forEach(([x, ad]) => {
        const g = ara(Gd, x), q = ara(Qd, x), e = ara(Ed, x);
        const k = komb.map(c => c.g * g + c.q * q + c.e * e);
        let a = 0, b = 0;
        k.forEach((t, i) => { if (t > k[a]) a = i; if (t < k[b]) b = i; });
        tb.appendChild(el("tr", null, el("td", null, ad, el("br"), "x = " + f(x, 3) + " m"),
          el("td", { style: "color:" + renk(komb[a].aile) }, el("b", null, f(k[a], 4)), el("br"), komb[a].ad),
          el("td", { style: "color:" + renk(komb[b].aile) }, el("b", null, f(k[b], 4)), el("br"), komb[b].ad)));
      });
      tablo.appendChild(tb);

      /* formül */
      const kz = 0.2 * SDS;
      texYaz(formul, "\\begin{aligned}" +
        "x&=" + ft(xK) + "\\ \\text{m}:\\quad \\ka{M_G}=" + ft(vx.g) + ",\\ \\kb{M_Q}=" + ft(vx.q) + ",\\ \\kc{M_E}=" + ft(vx.e) + "\\ \\text{kN·m}\\\\" +
        "M&=" + ft(gG) + "\\,\\ka{M_G}" + (gQ < 0 ? "" : "+") + ft(gQ) + "\\,\\kb{M_Q}" + (gE < 0 ? "" : "+") + ft(gE) + "\\,\\kc{M_E}=\\boldsymbol{" + ft(oz) + "}\\ \\text{kN·m}\\\\" +
        "0.3E_d^{(Z)}&=0.3\\cdot\\tfrac{2}{3}S_{DS}\\,G=" + ft(kz) + "\\,G\\quad(S_{DS}=" + ft(SDS) + ")\\\\" +
        "\\text{zarf:}\\ & M_{\\max}=" + ft(kx[iMx]) + "\\ (" + komb[iMx].ad.replace("−", "-") + "),\\quad M_{\\min}=" + ft(kx[iMn]) + "\\ (" + komb[iMn].ad.replace("−", "-") + ")" +
        "\\end{aligned}");
      const ucB = komb[mn[NS]].aile, ortaB = komb[mx[NS / 2]].aile;
      bilgi.textContent = "Kombinasyon yeniden çözüm değildir: her kesitte γ_G·M_G + γ_Q·M_Q + γ_E·M_E toplanır. Zarf her kesitte en büyük ve en küçük değeri ayrı ayrı seçer; " +
        "burada sağ uçta M_min'i " + KZ_AILE_AD[ucB] + ", ortada M_max'ı " + KZ_AILE_AD[ortaB] + " belirliyor. " +
        "Kirişte donatı her kesitte zarfa göre konur; kolonda ise aynı kombinasyondan gelen (N, M) çiftine bakılır.";
    }

    sG = sl("$\\gamma_G$", -1, 2, 0.05, gG, "", v => { gG = v; ciz(); });
    sQ = sl("$\\gamma_Q$", -1, 2, 0.05, gQ, "", v => { gQ = v; ciz(); });
    sE = sl("$\\gamma_E$", -1.5, 1.5, 0.05, gE, "", v => { gE = v; ciz(); });
    sS = sl("$S_{DS}$ (düşey deprem $E_Z$ için)", 0, 2, 0.05, SDS, "", v => { SDS = v; ciz(); });
    sX = sl("kesit $x$", 0, L, L / 50, xK, "m", v => { xK = v; ciz(); });
    function ayarla(g, q, e) {
      gG = g; gQ = q; gE = e;
      sG.ayarla(gG, true); sQ.ayarla(gQ, true); sE.ayarla(gE, true);
      ciz();
    }
    kap.appendChild(kart(s1));
    kap.appendChild(kart(s2));
    kap.appendChild(satir(
      dugme("1,4G + 1,6Q", () => ayarla(1.4, 1.6, 0), { baslik: "TS 500 Denk. (6.3)" }),
      dugme("G + Q + E (4.11)", () => ayarla(r2(1 + 0.2 * SDS), 1, 1), { baslik: "TBDY Denk. (4.11): G + Q + 0,2S + E_d(H) + 0,3E_d(Z)" }),
      dugme("0,9G − E (4.12)", () => ayarla(r2(0.9 - 0.2 * SDS), 0, -1), { baslik: "TBDY Denk. (4.12): 0,9G + H + E_d(H) − 0,3E_d(Z)" }),
      dugme("Servis G + Q", () => ayarla(1, 1, 0), { baslik: "TS 500 md. 6.2.6(f): kullanılabilirlik" })));
    kap.appendChild(el("div", { class: "ky-ayar" }, sG.kok, sQ.kok, sE.kok, sS.kok, sX.kok));
    kap.appendChild(bilgi);
    kap.appendChild(tablo);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ky-not" }, "Varsayılan diyagramlar 3 katlı ders binasının K-A2→B2/k1 kirişinin (eleman 30) motor çıktısıdır; E, +X yönündeki eşdeğer deprem durumudur (EX+). " +
      "Deprem birleşimlerinde E'nin işareti iki yönlü alınır; kesikli çizgiler −E'li birleşimlerdir. Bu kirişte kar ve EY momenti sıfıra yakın olduğundan zarfa yazılmadı."));
    ciz();
  }, {
    baslik: "Kombinasyon ve zarf",
    aciklama: "G, Q ve E moment diyagramlarını katsayılarla topla; zarfın en büyük ve en küçük eğrileri belirleyen kombinasyonun renginde çizilir.",
    varsayilan: { L: 5, gG: 1.4, gQ: 1.6, gE: 0, SDS: 1.2, x: 5 }
  });

  /* ================================================================== 5. ruzgar-kat-kuvveti */

  /* TS 498:2021 md. 14 Çizelge 4: zeminden yükseklik → emme basıncı q (kN/m²); md. 14.3 yüksekte ve sarp yamaçta q ≥ 1,1;
     Çizelge 5 (1.1.1): kapalı bina C = 1,2, kule tipi 1,6. Kat kuvveti F_i = C·q(z_i)·B·h_pay (yapi._ruzgar_durumlari ile aynı). */
  const RUZ_Q = [[8, 0.5, 28], [20, 0.8, 36], [100, 1.1, 42], [Infinity, 1.3, 46]];
  function ruzQ(z) {
    for (const s of RUZ_Q) if (z <= s[0] + 1e-9) return s[1];
    return 1.3;
  }

  E.kaydet("ruzgar-kat-kuvveti", function (kok, p) {
    const kap = kur(kok);
    let kat = Math.round(sayiP(p.kat, 3, 1, 30)), h = sayiP(p.h, 3.2, 2.5, 5), B = sayiP(p.B, 8, 2, 60);
    let C = Number(p.C) === 1.6 ? 1.6 : 1.2, sarp = p.sarp === true || p.sarp === "true";
    const W = 520, H = 360, YU = 30, YA = 320;
    const sd = sv(W, H, "Rüzgâr: q(z) basamakları, kat kuvvetleri ve kat kesmesi");
    const dyn = svg("g"); sd.appendChild(dyn);
    const formul = formulKutu();
    const bilgi = el("p", { class: "ky-bilgi" });
    let sK, sH, sB, secC, secS;

    function hesap() {
      const katlar = [];
      for (let i = 1; i <= kat; i++) {
        const z = i * h;
        let q = ruzQ(z);
        if (sarp) q = Math.max(q, 1.1);
        const hp = h / 2 + (i < kat ? h / 2 : 0);
        katlar.push({ i, z, q, hp, A: B * hp, F: C * q * B * hp });
      }
      let V = 0;
      for (let j = katlar.length - 1; j >= 0; j--) { V += katlar[j].F; katlar[j].V = V; }
      const Mo = katlar.reduce((s, k) => s + k.F * k.z, 0);
      return { katlar, Vt: V, Mo, Ht: kat * h };
    }

    function ciz() {
      const hs = hesap();
      bos(dyn);
      const zmax = hs.Ht;
      const Z = z => YA - z / zmax * (YA - YU);
      // q(z) profili (sol)
      const QX0 = 30, QX1 = 130, qmax = 1.4, QX = q => QX0 + q / qmax * (QX1 - QX0);
      dyn.appendChild(cizgi(QX0, YA, QX0, YU - 6, { renk: "soluk", kal: 1 }));
      dyn.appendChild(cizgi(QX0, YA, QX1 + 6, YA, { renk: "metin", kal: 1.4 }));
      const pr = [];
      let zAlt = 0;
      for (const s of RUZ_Q) {
        if (zAlt >= zmax) break;
        const zUst = Math.min(s[0], zmax);
        const q = sarp ? Math.max(s[1], 1.1) : s[1];
        pr.push([QX(q), Z(zAlt)], [QX(q), Z(zUst)]);
        if (zUst < zmax) dyn.appendChild(yaziH(QX0 - 4, Z(zUst), f(zUst, 3), { boyut: 9, renk: "soluk", hiza: "sag" }));
        dyn.appendChild(yaziH(QX(q) + 3, Z((zAlt + zUst) / 2), "q = " + f(q, 2), { boyut: 9.5, renk: "b", hiza: "sol" }));
        zAlt = zUst;
      }
      dyn.appendChild(yol("M" + QX0 + " " + YA + " L" + nokta(pr) + " L" + QX0 + " " + r2(Z(zmax)) + " Z", { dolgu: "b", renk: "b", kal: 1.6 }));
      dyn.appendChild(yaziH(QX0, YU - 14, "q(z) kN/m²", { boyut: 10, renk: "b", hiza: "sol" }));
      // bina cephesi (orta)
      const BX0 = 210, BX1 = 300;
      dyn.appendChild(dikdortgen(BX0, Z(hs.Ht), BX1 - BX0, YA - Z(hs.Ht), { dolgu: "cizgi", renk: "metin", kal: 1.6 }));
      dyn.appendChild(cizgi(BX0 - 30, YA, BX1 + 30, YA, { renk: "metin", kal: 1.6 }));
      const Fmax = Math.max(...hs.katlar.map(k => k.F)) || 1;
      const adim = Math.ceil(kat / 10);
      hs.katlar.forEach(k => {
        const y = Z(k.z);
        dyn.appendChild(cizgi(BX0, y, BX1, y, { renk: "metin", kal: 1 }));
        const uz = 14 + 50 * k.F / Fmax;
        dyn.appendChild(ok(BX0 - 4 - uz, y, BX0 - 3, y, { renk: "a", kalinlik: 2, bas: 6 }));
        if ((kat - k.i) % adim === 0) dyn.appendChild(yaziH(BX0 - 8 - uz, y, f(k.F, 4), { boyut: 9.5, renk: "a", hiza: "sag" }));
      });
      dyn.appendChild(yaziH((BX0 + BX1) / 2, YA + 12, "B = " + f(B, 3) + " m cephe", { boyut: 9.5, renk: "soluk" }));
      dyn.appendChild(yaziH(BX0 - 40, YU - 14, "F_i (kN)", { boyut: 10, renk: "a" }));
      // kat kesmesi (sağ)
      const VX0 = 340, VX1 = 500, VX = v => VX0 + v / (hs.Vt || 1) * (VX1 - VX0);
      dyn.appendChild(cizgi(VX0, YA, VX0, Z(hs.Ht) - 6, { renk: "soluk", kal: 1 }));
      const vp = [[VX0, Z(hs.Ht)]];
      for (let j = hs.katlar.length - 1; j >= 0; j--) {
        const k = hs.katlar[j], yU = Z(k.z), yA = Z(k.z - h);
        vp.push([VX(k.V), yU], [VX(k.V), yA]);
        if ((kat - k.i) % adim === 0) dyn.appendChild(yaziH(VX(k.V) + 3, (yU + yA) / 2, f(k.V, 4), { boyut: 9.5, renk: "c", hiza: "sol" }));
      }
      vp.push([VX0, YA]);
      dyn.appendChild(yol("M" + nokta(vp) + " Z", { dolgu: "c", renk: "c", kal: 1.6 }));
      dyn.appendChild(yaziH(VX0, YU - 14, "kat kesmesi V_i (kN)", { boyut: 10, renk: "c", hiza: "sol" }));

      const ust = hs.katlar[kat - 1], ilk = hs.katlar[0];
      texYaz(formul, "\\begin{aligned}" +
        "\\ka{F_i}&=C\\,q(z_i)\\,B\\,h_{\\text{pay}},\\qquad h_{\\text{pay}}=\\tfrac{h_i}{2}+\\tfrac{h_{i+1}}{2}\\\\" +
        "\\text{kat }1:\\ & " + ft(C) + "\\cdot" + ft(ilk.q) + "\\cdot" + ft(B) + "\\cdot" + ft(ilk.hp) + "=" + ft(ilk.F) + "\\ \\text{kN}\\quad(z=" + ft(ilk.z) + "\\ \\text{m})\\\\" +
        (kat > 1 ? "\\text{kat }" + kat + "\\ (\\text{tepe}):\\ & " + ft(C) + "\\cdot" + ft(ust.q) + "\\cdot" + ft(B) + "\\cdot" + ft(ust.hp) + "=" + ft(ust.F) + "\\ \\text{kN}\\quad(z=" + ft(ust.z) + "\\ \\text{m})\\\\" : "") +
        "\\kc{V_t}&=\\sum F_i=\\kutuc{" + ft(hs.Vt) + "}\\ \\text{kN},\\qquad M_o=\\sum F_i\\,z_i=" + ft(hs.Mo) + "\\ \\text{kN·m}" +
        "\\end{aligned}");
      bilgi.textContent = "TS 498:2021 md. 14: W = C·q·A. q, zeminden yüksekliğe göre Çizelge 4 basamaklarından (≤ 8 m: 0,5; 8–20 m: 0,8; 20–100 m: 1,1; > 100 m: 1,3 kN/m²; q = v²/1600) alınır; " +
        "C = 1,2 kapalı binada rüzgâra bakan yüzün basıncı (+0,8q) ile arka yüzün emmesinin (−0,4q) toplamıdır (Çizelge 5). " +
        (sarp ? "Sarp yamaç: q en az 1,1 kN/m² (md. 14.3). " : "") +
        "Bu araç ve motor kat payının tamamına kat düzeyindeki q'yu uygular.";
    }

    sK = sl("kat sayısı $N$", 1, 30, 1, kat, "", v => { kat = Math.round(v); ciz(); }, v => String(Math.round(v)));
    sH = sl("kat yüksekliği $h$", 2.5, 5, 0.1, h, "m", v => { h = v; ciz(); });
    sB = sl("cephe genişliği $B$", 2, 60, 1, B, "m", v => { B = v; ciz(); });
    secC = secici([{ deger: 1.2, etiket: "C = 1,2 (kapalı bina)" }, { deger: 1.6, etiket: "C = 1,6 (kule tipi)" }], C, v => { C = v; ciz(); });
    secS = secici([{ deger: false, etiket: "normal arazi" }, { deger: true, etiket: "sarp yamaç (q ≥ 1,1)" }], sarp, v => { sarp = v; ciz(); });
    function ayarla(nk, nh, nB, nC) {
      kat = nk; h = nh; B = nB; C = nC;
      sK.ayarla(kat, true); sH.ayarla(h, true); sB.ayarla(B, true); secC.ayarla(C, true);
      ciz();
    }
    kap.appendChild(kart(sd));
    kap.appendChild(satir(
      dugme("Ders binası (3 kat, B = 8 m)", () => ayarla(3, 3.2, 8, 1.2), { baslik: "W+X durumu: 15,36 + 15,36 + 12,288 = 43,008 kN" }),
      dugme("10 katlı konut", () => ayarla(10, 3, 20, 1.2), { baslik: "z > 20 m'de q = 1,1 kN/m²" }),
      dugme("Kule (30 kat, C = 1,6)", () => ayarla(30, 3.5, 12, 1.6), { baslik: "z > 100 m'de q = 1,3 kN/m²" }),
      secC.kok, secS.kok));
    kap.appendChild(el("div", { class: "ky-ayar" }, sK.kok, sH.kok, sB.kok));
    kap.appendChild(bilgi);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ky-not" }, "Rüzgâr dört yönde ayrı yük durumudur (W+X, W−X, W+Y, W−Y); X yönündeki rüzgâr Y doğrultusundaki cepheye çarpar, B o cephenin genişliğidir. " +
      "Kat kuvveti o kattaki cephe düğümlerine aks payıyla dağıtılır. Aynı ders binasında deprem taban kesmesi V_tE ≈ 321 kN, rüzgârınki 43 kN: alçak betonarme binada rüzgâr nadiren belirler."));
    ciz();
  }, {
    baslik: "Rüzgâr kat kuvvetleri (TS 498:2021 md. 14)",
    aciklama: "Kat sayısı, kat yüksekliği, cephe genişliği ve C katsayısını değiştir; q(z) basamakları, kat kuvvetleri ve kat kesmesi canlı güncellenir.",
    varsayilan: { kat: 3, h: 3.2, B: 8, C: 1.2, sarp: false }
  });

  /* ================================================================== 6. kat-kuvvetleri */

  /* TBDY 2018 md. 4.7: T_pA = C_t·H_N^(3/4) (Denk. 4.27, C_t = 0,1 betonarme çerçeve), S_ae (Denk. 2.2), R_a (4.1),
     V_tE = m_t·S_aR·g ≥ 0,04·m_t·I·S_DS·g (4.19), ΔF_NE = 0,0075·N·V_tE (4.22), F_iE = (V_tE − ΔF_NE)·m_iH_i/Σm_jH_j (4.23). */
  E.kaydet("kat-kuvvetleri", function (kok, p) {
    const kap = kur(kok);
    let N = Math.round(sayiP(p.N, 3, 1, 12)), w = sayiP(p.w, 1057, 100, 5000), wN = sayiP(p.wN, 998.5, 100, 5000), h = sayiP(p.h, 3.2, 2.5, 5);
    let SDS = sayiP(p.SDS, 1.2, 0.1, 2.5), SD1 = sayiP(p.SD1, 0.45, 0.02, 1.5), R = sayiP(p.R, 8, 1, 8), D = sayiP(p.D, 3, 1, 3);
    let I = [1.0, 1.2, 1.5].indexOf(Number(p.I)) >= 0 ? Number(p.I) : 1.0;
    let Tel = sayiP(p.Tp, 0, 0, 4), mod = Tel > 0 ? "elle" : "ampirik";
    const Ct = 0.1, W = 520, H = 372, YU = 54, YA = 330;
    const sd = sv(W, H, "Eşdeğer deprem yükü: ters üçgen kat kuvvetleri, tepe ek kuvveti ve kat kesmesi");
    const dyn = svg("g"); sd.appendChild(dyn);
    const formul = formulKutu();
    const bilgi = el("p", { class: "ky-bilgi" });
    let sN, sW, sWN, sH, sSDS, sSD1, sR, sT, secI, secM;

    function hesap() {
      const HN = N * h, TpA = Ct * Math.pow(HN, 0.75);
      const Tp = mod === "elle" && Tel > 0 ? Tel : TpA;
      const TA = 0.2 * SD1 / SDS, TB = SD1 / SDS, TL = 6;
      const Sae = Tp <= TA ? (0.4 + 0.6 * Tp / TA) * SDS : Tp <= TB ? SDS : Tp <= TL ? SD1 / Tp : SD1 * TL / (Tp * Tp);
      const Ra = Tp > TB ? R / I : D + (R / I - D) * Tp / TB;
      const SaR = Sae / Ra;
      const katlar = [];
      for (let i = 1; i <= N; i++) katlar.push({ i, H: i * h, w: i === N ? wN : w });
      const Wt = katlar.reduce((s, k) => s + k.w, 0);
      const Vh = Wt * SaR, Vmin = 0.04 * Wt * I * SDS, Vt = Math.max(Vh, Vmin);
      const dF = 0.0075 * N * Vt;
      const top = katlar.reduce((s, k) => s + k.w * k.H, 0);
      katlar.forEach(k => { k.F = (Vt - dF) * k.w * k.H / top; });
      let V = 0;
      for (let j = N - 1; j >= 0; j--) { V += katlar[j].F + (j === N - 1 ? dF : 0); katlar[j].V = V; }
      const Mo = katlar.reduce((s, k) => s + k.F * k.H, 0) + dF * HN;
      return { HN, TpA, Tp, TA, TB, Sae, Ra, SaR, katlar, Wt, mt: Wt / 9.81, Vh, Vmin, Vt, dF, top, Mo };
    }

    function ciz() {
      const s = hesap();
      bos(dyn);
      const Z = z => YA - z / s.HN * (YA - YU);
      const BX0 = 190, BX1 = 270;
      dyn.appendChild(dikdortgen(BX0, YU, BX1 - BX0, YA - YU, { dolgu: "cizgi", renk: "metin", kal: 1.6 }));
      dyn.appendChild(cizgi(BX0 - 150, YA, BX1 + 40, YA, { renk: "metin", kal: 1.6 }));
      for (let x = BX0 - 146; x <= BX1 + 36; x += 12) dyn.appendChild(cizgi(x, YA, x - 6, YA + 7, { renk: "soluk", kal: 1 }));
      const Fmax = Math.max(...s.katlar.map(k => k.F), s.dF) || 1, OL = 120;
      const adim = Math.ceil(N / 8);
      // ters üçgen zarfı (kesikli)
      dyn.appendChild(yol("M" + BX0 + " " + YA + " L" + r2(BX0 - OL * s.katlar[N - 1].F / Fmax) + " " + r2(Z(s.HN)), { renk: "a", kal: 1, kesik: true }));
      s.katlar.forEach(k => {
        const y = Z(k.H), uz = Math.max(6, OL * k.F / Fmax);
        dyn.appendChild(cizgi(BX0, y, BX1, y, { renk: "metin", kal: 1 }));
        dyn.appendChild(ok(BX0 - 3 - uz, y, BX0 - 3, y, { renk: "a", kalinlik: 2.2, bas: 6 }));
        if ((N - k.i) % adim === 0) dyn.appendChild(yaziH(BX0 - 7 - uz, y + (k.i === N ? 8 : 0), "F" + k.i + " = " + f(k.F, 4), { boyut: 9.5, renk: "a", hiza: "sag" }));
      });
      // ΔF_N tepe ek kuvveti
      const yN = Z(s.HN) - 14, uzN = Math.max(8, OL * s.dF / Fmax);
      dyn.appendChild(ok(BX0 - 3 - uzN, yN, BX0 - 3, Z(s.HN) - 2, { renk: "sil", kalinlik: 2.2, bas: 6 }));
      dyn.appendChild(yaziH(BX0 - 7 - uzN, yN - 4, "ΔF_N = " + f(s.dF, 4), { boyut: 9.5, renk: "sil", hiza: "sag" }));
      // kütle noktaları
      s.katlar.forEach(k => dyn.appendChild(svg("circle", { cx: (BX0 + BX1) / 2, cy: r2(Z(k.H)), r: 3 + 3 * k.w / Math.max(w, wN), fill: renk("metin"), opacity: 0.55 })));
      dyn.appendChild(yaziH((BX0 + BX1) / 2, YA + 18, "H_N = " + f(s.HN, 3) + " m", { boyut: 9.5, renk: "soluk" }));
      // kat kesmesi (sağ)
      const VX0 = 320, VX1 = 492, VX = v => VX0 + v / (s.Vt || 1) * (VX1 - VX0);
      const vp = [[VX0, Z(s.HN)]];
      for (let j = N - 1; j >= 0; j--) {
        const k = s.katlar[j], yU = Z(k.H), yA = Z(k.H - h);
        vp.push([VX(k.V), yU], [VX(k.V), yA]);
        if ((N - k.i) % adim === 0) dyn.appendChild(yaziH(Math.min(VX(k.V) + 3, VX1 - 2), (yU + yA) / 2, "V" + k.i + " = " + f(k.V, 4), { boyut: 9.5, renk: "c", hiza: VX(k.V) + 60 > W ? "sag" : "sol" }));
      }
      vp.push([VX0, YA]);
      dyn.appendChild(yol("M" + nokta(vp) + " Z", { dolgu: "c", renk: "c", kal: 1.6 }));
      dyn.appendChild(cizgi(VX0, YA, VX0, YU - 4, { renk: "soluk", kal: 1 }));
      dyn.appendChild(yaziH(VX0, 12, "kat kesmesi V_i (kN)", { boyut: 10, renk: "c", hiza: "sol" }));
      dyn.appendChild(yaziH(20, 12, "F_iE: ters üçgen (m_i·H_i ile)", { boyut: 10, renk: "a", hiza: "sol" }));

      const k1 = s.katlar[0], kN = s.katlar[N - 1];
      const bolge = s.Tp <= s.TA ? "(0.4+0.6\\tfrac{T_p}{T_A})S_{DS}" : s.Tp <= s.TB ? "S_{DS}" : "\\tfrac{S_{D1}}{T_p}";
      texYaz(formul, "\\begin{aligned}" +
        "T_{pA}&=C_t\\,H_N^{3/4}=0.1\\cdot" + ft(s.HN) + "^{0.75}=" + ft(s.TpA) + "\\ \\text{s}" + (mod === "elle" ? ",\\quad T_p=" + ft(s.Tp) + "\\ \\text{s (elle)}" : "") + "\\\\" +
        "S_{ae}(T_p)&=" + bolge + "=" + ft(s.Sae) + ",\\quad R_a=" + ft(s.Ra) + ",\\quad S_{aR}=" + ft(s.SaR) + "\\\\" +
        "\\kutua{V_{tE}}&=W_t\\,S_{aR}=" + ft(s.Wt) + "\\cdot" + ft(s.SaR) + "=" + ft(s.Vh) + (s.Vmin > s.Vh ? "\\ <\\ " : "\\ \\ge\\ ") + "0.04\\,I\\,S_{DS}W_t=" + ft(s.Vmin) +
        "\\ \\Rightarrow\\ \\boldsymbol{" + ft(s.Vt) + "}\\ \\text{kN}\\\\" +
        "\\ksil{\\Delta F_{NE}}&=0.0075\\,N\\,V_{tE}=0.0075\\cdot" + N + "\\cdot" + ft(s.Vt) + "=" + ft(s.dF) + "\\ \\text{kN}\\\\" +
        "\\ka{F_{1E}}&=(V_{tE}-\\Delta F_{NE})\\tfrac{w_1H_1}{\\sum w_jH_j}=" + ft(s.Vt - s.dF) + "\\cdot\\tfrac{" + ft(k1.w * k1.H) + "}{" + ft(s.top) + "}=" + ft(k1.F) + "\\ \\text{kN}\\\\" +
        (N > 1 ? "\\ka{F_{" + N + "E}}&=" + ft(s.Vt - s.dF) + "\\cdot\\tfrac{" + ft(kN.w * kN.H) + "}{" + ft(s.top) + "}=" + ft(kN.F) + "\\ \\text{kN}\\\\" : "") +
        "\\kc{V_1}&=\\sum F_{iE}+\\Delta F_{NE}=\\kutuc{" + ft(s.katlar[0].V) + "}=V_{tE}\\ \\checkmark,\\qquad M_o=" + ft(s.Mo) + "\\ \\text{kN·m}" +
        "\\end{aligned}");
      bilgi.textContent = "m_t = W_t/g = " + f(s.mt, 4) + " t. " +
        (s.Vmin > s.Vh ? "Alt sınır belirledi: 0,04·I·S_DS·W_t > W_t·S_aR (Denk. 4.19); uzun periyotlu ya da büyük R'li binada olur. " : "") +
        (s.Tp > s.TB ? "T_p > T_B: R_a = R/I, S_ae = S_D1/T_p (inen kol). " : s.Tp >= s.TA ? "T_p platoda: S_ae = S_DS, R_a = D + (R/I − D)·T_p/T_B (Denk. 4.1b). " : "T_p < T_A: çok rijit bina. ") +
        "Kat kuvveti m_i·H_i ile orantılıdır (birinci mod ters üçgen varsayımı); ΔF_N yüksek modların etkisini tepe kata ekler.";
    }

    sN = sl("kat sayısı $N$", 1, 12, 1, N, "", v => { N = Math.round(v); ciz(); }, v => String(Math.round(v)));
    sW = sl("kat ağırlığı $w_i=w_G+n\\,w_Q$", 100, 5000, 1, w, "kN", v => { w = v; ciz(); });
    sWN = sl("çatı katı $w_N$", 100, 5000, 1, wN, "kN", v => { wN = v; ciz(); });
    sH = sl("kat yüksekliği $h$", 2.5, 5, 0.1, h, "m", v => { h = v; ciz(); });
    sSDS = sl("$S_{DS}$", 0.1, 2.5, 0.01, SDS, "", v => { SDS = v; ciz(); });
    sSD1 = sl("$S_{D1}$", 0.02, 1.5, 0.01, SD1, "", v => { SD1 = v; ciz(); });
    sR = sl("$R$ (Tablo 4.1)", 1, 8, 0.5, R, "", v => { R = v; ciz(); });
    sT = sl("$T_p$ (elle)", 0.05, 4, 0.01, Tel > 0 ? Tel : 0.5, "s", v => { Tel = v; if (mod !== "elle") { mod = "elle"; secM.ayarla("elle", true); } ciz(); });
    secI = secici([{ deger: 1.0, etiket: "I = 1,0" }, { deger: 1.2, etiket: "I = 1,2" }, { deger: 1.5, etiket: "I = 1,5" }], I, v => { I = v; ciz(); });
    secM = secici([{ deger: "ampirik", etiket: "T_p = T_pA" }, { deger: "elle", etiket: "T_p elle" }], mod, v => { mod = v; if (v === "elle" && !(Tel > 0)) Tel = sT.deger(); ciz(); });
    function ayarla(o) {
      N = o.N; w = o.w; wN = o.wN; h = o.h; SDS = o.SDS; SD1 = o.SD1; R = o.R; D = o.D; I = o.I; mod = o.mod; if (o.Tp) Tel = o.Tp;
      sN.ayarla(N, true); sW.ayarla(w, true); sWN.ayarla(wN, true); sH.ayarla(h, true); sSDS.ayarla(SDS, true); sSD1.ayarla(SD1, true); sR.ayarla(R, true);
      if (o.Tp) sT.ayarla(o.Tp, true);
      secI.ayarla(I, true); secM.ayarla(mod, true);
      ciz();
    }
    kap.appendChild(kart(sd));
    kap.appendChild(satir(
      dugme("Ders binası (3 kat)", () => ayarla({ N: 3, w: 1057.005, wN: 998.505, h: 3.2, SDS: 1.2, SD1: 0.45, R: 8, D: 3, I: 1.0, mod: "ampirik" }), { baslik: "betonarme-3kat-3x3: V_tE = 321,02 kN (T_pA ile)" }),
      dugme("Rayleigh, çatlamış (T_p = 0,544)", () => ayarla({ N: 3, w: 1057.005, wN: 998.505, h: 3.2, SDS: 1.2, SD1: 0.45, R: 8, D: 3, I: 1.0, mod: "elle", Tp: 0.544 }), { baslik: "Tablo 4.2 rijitlikleriyle Rayleigh periyodu" }),
      dugme("8 katlı", () => ayarla({ N: 8, w: 2500, wN: 2200, h: 3, SDS: 1.0, SD1: 0.35, R: 8, D: 3, I: 1.0, mod: "ampirik" }), { baslik: "ΔF_N = 0,06·V_tE" }),
      secI.kok, secM.kok));
    kap.appendChild(el("div", { class: "ky-ayar" }, sN.kok, sW.kok, sWN.kok, sH.kok, sSDS.kok, sSD1.kok, sR.kok, sT.kok));
    kap.appendChild(bilgi);
    kap.appendChild(formul);
    kap.appendChild(el("p", { class: "ky-not" }, "D = " + f(D, 2) + " (Tablo 4.1, A11 için 3), C_t = 0,1 (betonarme çerçeve, Denk. 4.27). Kat ağırlıkları TBDY Tablo 4.3 ile w_i = w_G + n·w_Q (konut ve büroda n = 0,3; çatıda karın %30'u). " +
      "Kat kuvvetleri rijit diyaframda kütle merkezine, ±%5 dışmerkezlikle (M_ib = F_iE·0,05·B_i) etkir."));
    ciz();
  }, {
    baslik: "Eşdeğer deprem yükü: kat kuvvetleri",
    aciklama: "Kat sayısı, kat ağırlığı, kat yüksekliği ve spektrum değerlerini değiştir; V_tE, ΔF_N, ters üçgen F_iE ve kat kesmesi canlı güncellenir.",
    varsayilan: { N: 3, w: 1057, wN: 998.5, h: 3.2, SDS: 1.2, SD1: 0.45, R: 8, D: 3, I: 1.0 }
  });

  /* ================================================================== alıştırma: doseme-esdeger */

  const zorlukOku = p => kenet(Math.round(Number(p && p.zorluk) || 1), 1, 3);
  const K = x => Kesir.al(x);
  const Kt = x => K(x).tex();
  const PANELLER = [[4, 5], [4, 6], [3, 4], [5, 6], [4, 8], [3, 5], [5, 8], [4, 4], [6, 6], [3, 6], [5, 5], [6, 8]];
  const WLER = ["4", "5", "6", "7.5", "8", "4.5", "5.5"];

  E.kaydet("alistirma:doseme-esdeger", function (kok, p) {
    return E.alistirmaKur(kok, p, (rnd, pp) => {
      const z = zorlukOku(pp);
      let panel = rnd.sec(PANELLER);
      if (z === 3 && rnd.sayi() < 0.25) panel = rnd.sec([[3, 8], [3, 7], [4, 9]]);
      const lk = K(panel[0]), lu = K(panel[1]), w = K(rnd.sec(WLER));
      const m = lu.bol(lk), p0 = w.carp(lk).bol(2);
      const giris = "Dört kenarı kirişe oturan panel $l_k=" + Kt(lk) + "$ m, $l_u=" + Kt(lu) + "$ m; döşeme yükü $w=" + Kt(w) + "$ kN/m². ";
      const mAdim = { metin: "Döşeme tipini oranla belirle.", tex: "m=\\tfrac{l_u}{l_k}=\\tfrac{" + Kt(lu) + "}{" + Kt(lk) + "}=" + Kt(m) + (m.karsilastir(K(2)) <= 0 ? "\\le 2\\ \\Rightarrow\\ \\text{çift doğrultulu}" : ">2\\ \\Rightarrow\\ \\text{tek doğrultulu}") };
      const pAdim = { metin: "Tepe yükü: 45° üçgeninin yüksekliği $l_k/2$'dir.", tex: "\\kutua{p=\\tfrac{w\\,l_k}{2}}=\\tfrac{" + Kt(w) + "\\cdot" + Kt(lk) + "}{2}=" + Kt(p0) + "\\ \\text{kN/m}" };
      if (z === 1) {
        return {
          metin: giris + "Kirişlere giden üçgen ve trapez yükün **tepe değeri** $p$ kaç kN/m?",
          etiket: "p =", cevap: new Mat([[p0]]), tolerans: "tam",
          ipucu: ["Köşelerden 45° çizilince kısa kenara dik yükseklik $l_k/2$ olur.", "Tepe değeri $p=w\\,l_k/2$; kısa ve uzun kenarda aynıdır."],
          aciklama: "TS 500 md. 11.4.3: 45° çizgileri kısa kenara üçgen, uzun kenara trapez düşürür; ikisinin de tepesi $p=w\\,l_k/2$'dir.",
          adimlar: [mAdim, pAdim, { metin: "Kontrol: $2\\cdot\\tfrac{p\\,l_k}{2}+2\\cdot p\\,(l_u-\\tfrac{l_k}{2})=w\\,l_k\\,l_u$." }]
        };
      }
      if (z === 2) {
        const momentMi = rnd.sayi() < 0.5;
        const cevap = momentMi ? w.carp(lk).bol(3) : w.carp(lk).bol(4);
        return {
          metin: giris + "**Kısa kenar** kirişine giden üçgen yükün " + (momentMi ? "moment eşdeğeri $q_{eM}$" : "kesme (tepki) eşdeğeri $q_{eV}$") + " kaç kN/m?",
          etiket: (momentMi ? "q_eM" : "q_eV") + " =", cevap: new Mat([[cevap]]), tolerans: "tam",
          ipucu: ["Üçgen yükün tepesi $p=w\\,l_k/2$.", momentMi ? "Üçgen için $q_{eM}=\\tfrac{2}{3}p=w\\,l_k/3$." : "Üçgen için $q_{eV}=\\tfrac{1}{2}p=w\\,l_k/4$ (bileşke $p\\,l_k/2$, tepki $p\\,l_k/4$)."],
          aciklama: "Basit kirişte üçgen yükün en büyük momenti $p\\,l_k^2/12$, düzgün yükün $q\\,l_k^2/8$: eşitlersen $q_{eM}=2p/3$. Tepki için $q_{eV}=p/2$. TS 500 bu kısayolları vermez; sonlu elemanda gerçek şekil kullanılır.",
          adimlar: [mAdim, pAdim, momentMi
            ? { metin: "Moment eşdeğeri: $q_{eM}=\\tfrac{2}{3}p$.", tex: "\\kutua{q_{eM}=\\tfrac{w\\,l_k}{3}}=\\tfrac{" + Kt(w) + "\\cdot" + Kt(lk) + "}{3}=" + Kt(cevap) + "\\ \\text{kN/m}" }
            : { metin: "Kesme eşdeğeri: $q_{eV}=\\tfrac{1}{2}p$.", tex: "\\kutub{q_{eV}=\\tfrac{w\\,l_k}{4}}=\\tfrac{" + Kt(w) + "\\cdot" + Kt(lk) + "}{4}=" + Kt(cevap) + "\\ \\text{kN/m}" }]
        };
      }
      // zorluk 3: uzun kenar
      if (m.karsilastir(K(2)) > 0) {
        return {
          metin: giris + "Döşeme tipini belirle; **uzun kenar** kirişine giden yayılı yük kaç kN/m?",
          etiket: "q =", cevap: new Mat([[p0]]), tolerans: "tam",
          ipucu: ["$m=l_u/l_k$ 2'den büyükse plak tek doğrultuludur.", "Tek doğrultulu plakta yük uzun kenar kirişlerine düzgün $w\\,l_k/2$ olarak gider."],
          aciklama: "$m>2$: tek doğrultulu (TS 500 md. 11.2.1). Yük yalnız kısa doğrultuda taşınır; her uzun kenar kirişi $w\\,l_k/2$ düzgün yük alır, kısa kenar kirişleri döşemeden pay almaz.",
          adimlar: [mAdim, { metin: "Uzun kenar kirişine düzgün yük.", tex: "\\kutuc{q=\\tfrac{w\\,l_k}{2}}=" + Kt(p0) + "\\ \\text{kN/m},\\qquad \\text{korunum } 2\\,q\\,l_u=" + Kt(p0.carp(lu).carp(2)) + "=w\\,l_k\\,l_u\\ \\checkmark" }]
        };
      }
      const momentMi = rnd.sayi() < 0.6;
      const bir = K(1);
      const cevap = momentMi ? p0.carp(bir.cikar(bir.bol(m.carp(m).carp(3)))) : p0.carp(bir.cikar(bir.bol(m.carp(2))));
      return {
        metin: giris + "**Uzun kenar** kirişine giden trapez yükün " + (momentMi ? "moment eşdeğeri $q_{eM}$" : "kesme (tepki) eşdeğeri $q_{eV}$") + " kaç kN/m?",
        etiket: (momentMi ? "q_eM" : "q_eV") + " =", cevap: new Mat([[cevap]]), tolerans: "tam",
        ipucu: ["Önce $m=l_u/l_k$ ve tepe $p=w\\,l_k/2$.", momentMi ? "Trapez: $q_{eM}=p\\,(1-\\tfrac{1}{3m^2})$." : "Trapez: $q_{eV}=p\\,(1-\\tfrac{1}{2m})$."],
        aciklama: "Trapez yükün rampaları $l_k/2$, platosu $l_u-l_k$ uzunluğundadır. Basit kirişte moment eşitliğinden $q_{eM}=p(1-1/3m^2)$, tepki eşitliğinden $q_{eV}=p(1-1/2m)$ çıkar; $m=1$'de üçgen değerlerine, $m\\to\\infty$'da $p$'ye yaklaşır.",
        adimlar: [mAdim, pAdim, momentMi
          ? { metin: "Trapezin moment eşdeğeri.", tex: "\\kutua{q_{eM}=p\\Big(1-\\tfrac{1}{3m^2}\\Big)}=" + Kt(p0) + "\\Big(1-\\tfrac{1}{3\\cdot" + Kt(m.carp(m)) + "}\\Big)=" + Kt(cevap) + "\\ \\text{kN/m}" }
          : { metin: "Trapezin kesme eşdeğeri.", tex: "\\kutub{q_{eV}=p\\Big(1-\\tfrac{1}{2m}\\Big)}=" + Kt(p0) + "\\Big(1-\\tfrac{1}{2\\cdot" + Kt(m) + "}\\Big)=" + Kt(cevap) + "\\ \\text{kN/m}" }]
      };
    });
  }, { baslik: "Döşeme payı ve eşdeğer yük", aciklama: "Verilen l_k, l_u ve w ile tepe p, üçgen ya da trapez için q_eM / q_eV.", varsayilan: { zorluk: 2 } });

  /* ================================================================== alıştırma: kombinasyon */

  const Kd = x => E.sayiTex(K(x).sayi(), 6);          // ondalık TeX (cevap ondalık yazılır)
  const ondalik6 = x => E.sayi(x, 6);
  const isaretli = x => (K(x).isaret() < 0 ? "-" : "+") + Kd(K(x).mutlak());

  E.kaydet("alistirma:kombinasyon", function (kok, p) {
    return E.alistirmaKur(kok, p, (rnd, pp) => {
      const z = zorlukOku(pp);
      const isr = rnd.sayi() < 0.5 ? -1 : 1;
      const kesit = isr < 0 ? "bir kirişin mesnet kesitinde" : "bir kirişin açıklık kesitinde";
      const G = K(isr * rnd.tam(20, 90)), Q = K(isr * rnd.tam(5, 35));
      const durum = "$M_G=" + Kd(G) + "$, $M_Q=" + Kd(Q) + "$";
      if (z === 1) {
        const c = K("1.4").carp(G).topla(K("1.6").carp(Q));
        return {
          metin: "Yük durumlarının " + kesit + " verdiği momentler " + durum + " kN·m. TS 500 Denk. (6.3) birleşimi $1.4G+1.6Q$ için tasarım momenti $M_d$ kaç kN·m?",
          etiket: "M_d =", cevap: new Mat([[c]]), tolerans: "tam", bicim: ondalik6,
          ipucu: ["Kombinasyon yeniden çözüm değildir: her durumun sonucu katsayısıyla çarpılıp toplanır.", "$M_d=1.4\\,M_G+1.6\\,M_Q$; işaretleri koru."],
          aciklama: "Doğrusal çözümde süperpozisyon geçerlidir: $M(1.4G+1.6Q)=1.4\\,M(G)+1.6\\,M(Q)$. SAP2000'de \"Linear Add\" kombinasyonu da yalnız bu toplamı yapar.",
          adimlar: [{ metin: "Katsayılı toplam.", tex: "\\kutuc{M_d}=1.4\\cdot(" + Kd(G) + ")+1.6\\cdot(" + Kd(Q) + ")=" + Kd(K("1.4").carp(G)) + isaretli(K("1.6").carp(Q)) + "=\\kutuc{" + Kd(c) + "}\\ \\text{kN·m}" }]
        };
      }
      const SDS = K(rnd.sec(["0.6", "0.8", "1", "1.2", "1.5"]));
      const kz = K("0.2").carp(SDS);                          // 0,3·(2/3)·S_DS
      const Em = K(rnd.sifirsiz(-9, 9) * 10 + rnd.tam(-4, 4));
      if (z === 2) {
        const S = K(isr * rnd.tam(0, 12));
        const ilk = rnd.sayi() < 0.55;
        const cevap = ilk
          ? G.topla(Q).topla(K("0.2").carp(S)).topla(Em).topla(kz.carp(G))
          : K("0.9").carp(G).topla(Em).cikar(kz.carp(G));
        const gKat = ilk ? K(1).topla(kz) : K("0.9").cikar(kz);
        return {
          metin: "Yük durumlarının " + kesit + " verdiği momentler " + durum + ", $M_S=" + Kd(S) + "$ (kar) ve yatay deprem $E_d^{(H)}$ için $M_E=" + Kd(Em) +
            "$ kN·m; $S_{DS}=" + Kd(SDS) + "$. TBDY 2018 Denk. " + (ilk ? "(4.11) $G+Q+0.2S+E_d^{(H)}+0.3E_d^{(Z)}$" : "(4.12) $0.9G+H+E_d^{(H)}-0.3E_d^{(Z)}$ ($H=0$)") +
            " birleşiminin momenti kaç kN·m? Düşey deprem $E_d^{(Z)}=\\tfrac{2}{3}S_{DS}\\,G$ (Denk. 4.10).",
          etiket: "M =", cevap: new Mat([[cevap]]), tolerans: "tam", bicim: ondalik6,
          ipucu: ["$0.3E_d^{(Z)}=0.3\\cdot\\tfrac{2}{3}S_{DS}\\,G=0.2\\,S_{DS}\\,G$: düşey deprem $G$'nin katsayısını değiştirir.",
            ilk ? "$G$'nin toplam katsayısı $1+0.2\\,S_{DS}$; kar $0.2$ ile girer." : "$G$'nin toplam katsayısı $0.9-0.2\\,S_{DS}$; hareketli yük ve kar bu birleşimde yoktur."],
          aciklama: "TBDY md. 4.4.4.1: (4.11) düşey yükü büyüten, (4.12) azaltan deprem birleşimidir. $E_d^{(H)}$ iki yönlü ($\\pm$) alındığından her ikisi de işaret değiştirerek zarfa girer.",
          adimlar: [
            { metin: "Düşey deprem payı.", tex: "0.3E_d^{(Z)}=0.2\\,S_{DS}\\,G=0.2\\cdot" + Kd(SDS) + "\\cdot G=" + Kd(kz) + "\\,G" },
            ilk
              ? { metin: "Denk. (4.11) toplamı.", tex: "\\kutuc{M}=" + Kd(gKat) + "\\cdot(" + Kd(G) + ")" + isaretli(Q) + "+0.2\\cdot(" + Kd(S) + ")" + isaretli(Em) + "=\\kutuc{" + Kd(cevap) + "}\\ \\text{kN·m}" }
              : { metin: "Denk. (4.12) toplamı.", tex: "\\kutuc{M}=" + Kd(gKat) + "\\cdot(" + Kd(G) + ")" + isaretli(Em) + "=\\kutuc{" + Kd(cevap) + "}\\ \\text{kN·m}" }]
        };
      }
      // zorluk 3: zarf (en büyük ve en küçük)
      const ruzgar = rnd.sayi() < 0.5;
      let liste, giris;
      if (ruzgar) {
        const Wm = K(rnd.tam(10, 70));
        liste = [
          { ad: "1.4G+1.6Q", v: K("1.4").carp(G).topla(K("1.6").carp(Q)) },
          { ad: "G+1.3Q+1.3W", v: G.topla(K("1.3").carp(Q)).topla(K("1.3").carp(Wm)) },
          { ad: "G+1.3Q-1.3W", v: G.topla(K("1.3").carp(Q)).cikar(K("1.3").carp(Wm)) },
          { ad: "0.9G+1.3W", v: K("0.9").carp(G).topla(K("1.3").carp(Wm)) },
          { ad: "0.9G-1.3W", v: K("0.9").carp(G).cikar(K("1.3").carp(Wm)) }];
        giris = "Yük durumlarının " + kesit + " verdiği momentler " + durum + " ve rüzgâr için $M_W=\\pm" + Kd(Wm) + "$ kN·m (rüzgâr iki yönden eser). " +
          "TS 500 Denk. (6.3), (6.5) ve (6.6) birleşimlerinin zarfında en büyük ve en küçük moment nedir?";
      } else {
        const Ea = Em.mutlak();
        const g1 = K(1).topla(kz), g2 = K("0.9").cikar(kz);
        liste = [
          { ad: "1.4G+1.6Q", v: K("1.4").carp(G).topla(K("1.6").carp(Q)) },
          { ad: Kd(g1) + "G+Q+E", v: g1.carp(G).topla(Q).topla(Ea) },
          { ad: Kd(g1) + "G+Q-E", v: g1.carp(G).topla(Q).cikar(Ea) },
          { ad: Kd(g2) + "G+E", v: g2.carp(G).topla(Ea) },
          { ad: Kd(g2) + "G-E", v: g2.carp(G).cikar(Ea) }];
        giris = "Yük durumlarının " + kesit + " verdiği momentler " + durum + " ve yatay deprem için $M_E=\\pm" + Kd(Ea) + "$ kN·m; $S_{DS}=" + Kd(SDS) +
          "$, kar ve toprak itkisi yok. TS 500 Denk. (6.3) ile TBDY Denk. (4.11) ve (4.12) birleşimlerinin ($0.3E_d^{(Z)}=0.2S_{DS}G$ dahil) zarfında en büyük ve en küçük moment nedir?";
      }
      let iMx = 0, iMn = 0;
      liste.forEach((k, i) => { if (k.v.karsilastir(liste[iMx].v) > 0) iMx = i; if (k.v.karsilastir(liste[iMn].v) < 0) iMn = i; });
      return {
        metin: giris, alanlar: ["M_max =", "M_min ="], cevap: new Mat([[liste[iMx].v, liste[iMn].v]]), tolerans: "tam", bicim: ondalik6,
        ipucu: ["Her birleşimi ayrı hesapla; rüzgâr ya da deprem işareti hem + hem − alınır.", "Zarf, beş değerin en büyüğü ve en küçüğüdür; ikisi farklı birleşimlerden gelebilir."],
        aciklama: "Zarf her büyüklük için ayrı seçilir: en büyük " + liste[iMx].ad + ", en küçük " + liste[iMn].ad + " birleşiminden. Kolon gibi iki büyüklüğün (N, M) birlikte denetlendiği elemanda zarf değerleri aynı anda oluşmayabilir.",
        adimlar: liste.map((k, i) => ({ metin: (i === iMx ? "**en büyük** " : i === iMn ? "**en küçük** " : "") + "$" + k.ad.replace(/-/g, "-") + "$", tex: "M=" + Kd(k.v) + "\\ \\text{kN·m}" }))
      };
    });
  }, { baslik: "Kombinasyon ve zarf", aciklama: "Yük durumu momentlerinden TS 500 / TBDY birleşimi (1, 2) ya da zarfın en büyük ve en küçük değeri (3).", varsayilan: { zorluk: 2 } });

  /* ================================================================== alıştırma: deprem-vt */

  /* Tablo 4.1 satırları (R, D) ve Tablo 3.1 I değerleri araştırma dosyasından (TBDY 2018); g = 9,81 m/s². */
  const DVT_SIS = [{ kod: "A11", R: "8", D: "3" }, { kod: "A12", R: "7", D: "2.5" }, { kod: "A13", R: "6", D: "2.5" }, { kod: "A15", R: "7", D: "2.5" }, { kod: "C13", R: "5", D: "2" }];
  const DVT_SDS = ["0.6", "0.8", "1", "1.2", "1.5"], DVT_SD1 = ["0.25", "0.3", "0.4", "0.45", "0.6"], DVT_I = ["1", "1", "1.2", "1.5"];
  const DVT_MT = [180, 240, 320, 400, 520, 650, 800, 1000];

  function dvtHesap(o) {
    const TA = K("0.2").carp(o.SD1).bol(o.SDS), TB = o.SD1.bol(o.SDS);
    let Sae, bolge;
    if (o.Tp.karsilastir(TA) <= 0) { Sae = K("0.4").topla(K("0.6").carp(o.Tp).bol(TA)).carp(o.SDS); bolge = "T_p\\le T_A"; }
    else if (o.Tp.karsilastir(TB) <= 0) { Sae = o.SDS; bolge = "T_A\\le T_p\\le T_B"; }
    else { Sae = o.SD1.bol(o.Tp); bolge = "T_B<T_p\\le T_L"; }
    const RI = o.R.bol(o.I);
    const Ra = o.Tp.karsilastir(TB) > 0 ? RI : o.D.topla(RI.cikar(o.D).carp(o.Tp).bol(TB));
    const SaR = Sae.bol(Ra), g = K("9.81");
    const V = o.mt.carp(SaR).carp(g), Vmin = K("0.04").carp(o.mt).carp(o.I).carp(o.SDS).carp(g);
    const Vt = V.karsilastir(Vmin) >= 0 ? V : Vmin;
    return { TA, TB, Sae, bolge, RI, Ra, SaR, V, Vmin, Vt };
  }

  E.kaydet("alistirma:deprem-vt", function (kok, p) {
    return E.alistirmaKur(kok, p, (rnd, pp) => {
      const z = zorlukOku(pp);
      const sis = rnd.sec(DVT_SIS);
      const o = { SDS: K(rnd.sec(DVT_SDS)), SD1: K(rnd.sec(DVT_SD1)), R: K(sis.R), D: K(sis.D), I: K(rnd.sec(DVT_I)), mt: K(rnd.sec(DVT_MT)) };
      const TB = o.SD1.bol(o.SDS).sayi();
      let Tp;
      if (z === 1) {
        const aday = [0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.4, 1.6, 2].filter(t => t > TB + 0.02);
        if (!aday.length) return null;
        Tp = rnd.sec(aday);
      } else if (z === 2) {
        Tp = Math.round(TB * rnd.sec([0.45, 0.55, 0.65, 0.75, 0.85]) * 100) / 100;
        if (Tp <= 0.2 * TB + 0.005 || Tp >= TB) return null;
      } else {
        Tp = rnd.sec([0.25, 0.4, 0.5, 0.7, 1, 1.5, 2, 2.5, 3]);
      }
      o.Tp = K(String(Tp));
      const h = dvtHesap(o);
      const N = rnd.tam(2, 10);
      const dF = K("0.0075").carp(N).carp(h.Vt);
      const veri = "$S_{DS}=" + Kd(o.SDS) + "$, $S_{D1}=" + Kd(o.SD1) + "$, $T_p=" + Kd(o.Tp) + "$ s, " + sis.kod + " sistemi ($R=" + Kd(o.R) + "$, $D=" + Kd(o.D) +
        "$), $I=" + Kd(o.I) + "$, toplam kütle $m_t=" + Kd(o.mt) + "$ t ($g=9.81$ m/s²)";
      const adimlar = [
        { metin: "Köşe periyotları (Denk. 2.3).", tex: "T_A=0.2\\tfrac{S_{D1}}{S_{DS}}=" + Kd(h.TA) + ",\\qquad T_B=\\tfrac{S_{D1}}{S_{DS}}=" + Kd(h.TB) + "\\ \\text{s}" },
        { metin: "Elastik spektral ivme (Denk. 2.2), $" + h.bolge + "$.", tex: "S_{ae}(T_p)=" + Kd(h.Sae) },
        { metin: "Deprem yükü azaltma katsayısı (Denk. 4.1).", tex: "R_a=" + (o.Tp.karsilastir(h.TB) > 0 ? "\\tfrac{R}{I}=" : "D+\\big(\\tfrac{R}{I}-D\\big)\\tfrac{T_p}{T_B}=") + Kd(h.Ra) + ",\\qquad S_{aR}=\\tfrac{S_{ae}}{R_a}=" + Kd(h.SaR) },
        { metin: "Taban kesme kuvveti ve alt sınır (Denk. 4.19).", tex: "m_t\\,S_{aR}\\,g=" + Kd(h.V) + ",\\quad 0.04\\,m_t\\,I\\,S_{DS}\\,g=" + Kd(h.Vmin) + "\\ \\Rightarrow\\ \\kutuc{V_{tE}=" + Kd(h.Vt) + "}\\ \\text{kN}" }];
      const ipucu = ["Önce $T_B=S_{D1}/S_{DS}$: $T_p$ spektrumun hangi kolunda?", "$R_a=R/I$ yalnız $T_p>T_B$ iken; platoda $D$'den $R/I$'ya doğrusal artar.", "$V_{tE}=m_tS_{aR}g$ ama $0.04\\,m_t\\,I\\,S_{DS}\\,g$'den az olamaz."];
      if (z < 3) {
        return {
          metin: veri + ". TBDY 2018 eşdeğer deprem yükü yöntemiyle toplam deprem yükü (taban kesme kuvveti) $V_{tE}$ kaç kN?",
          etiket: "V_tE =", cevap: new Mat([[h.Vt]]), tolerans: "yaklasik", bicim: ondalik6, ipucu,
          aciklama: "$V_{tE}=m_t\\,S_{aR}(T_p)\\,g\\ge0.04\\,m_t\\,I\\,S_{DS}\\,g$ (Denk. 4.19); $S_{aR}=S_{ae}/R_a$ (Denk. 4.8).",
          adimlar
        };
      }
      return {
        metin: veri + ", kat sayısı $N=" + N + "$. Taban kesme kuvveti $V_{tE}$ ve tepe kata eklenen $\\Delta F_{NE}$ kaç kN?",
        alanlar: ["V_tE =", "ΔF_NE ="], cevap: new Mat([[h.Vt, dF]]), tolerans: "yaklasik", bicim: ondalik6, ipucu,
        aciklama: "$\\Delta F_{NE}=0.0075\\,N\\,V_{tE}$ (Denk. 4.22); kalan $V_{tE}-\\Delta F_{NE}$ katlara $m_iH_i$ ile dağıtılır (Denk. 4.23)." +
          (h.Vmin.karsilastir(h.V) > 0 ? " Bu soruda alt sınır belirledi." : ""),
        adimlar: adimlar.concat([{ metin: "Tepe ek kuvveti (Denk. 4.22).", tex: "\\Delta F_{NE}=0.0075\\cdot" + N + "\\cdot" + Kd(h.Vt) + "=\\kutuc{" + Kd(dF) + "}\\ \\text{kN}" }])
      };
    });
  }, { baslik: "Taban kesme kuvveti V_tE", aciklama: "S_DS, S_D1, T_p, R, D, I ve m_t ile V_tE (1: T_p > T_B, 2: platoda, 3: karışık ve ΔF_NE).", varsayilan: { zorluk: 2 } });
})();
