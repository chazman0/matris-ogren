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
 *
 * ALIŞTIRMALAR (BICIM.md 7): alistirma:doseme-esdeger
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
})();
