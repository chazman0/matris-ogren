/* Matris Öğren · matris bölümünün etkileşimleri (docs/etkilesim_matris.js)
 *
 * Sekiz çizim (BICIM.md §6.1) ve dokuz alıştırma (§7). Hepsi docs/etkilesim.js çekirdeğinin (window.Etkilesim)
 * üstüne kurulur: dış kitaplık, ağ ya da eval yok. Renk anlamı derslerle aynıdır:
 *   mavi = satır / ilk girdi, turuncu = sütun / ikinci girdi, yeşil = sonuç, kırmızı = silinen / hata.
 * Alıştırmaların "Cevap" ve yerel "Adım adım çözüm" bölümleri motor olmadan da okla ve renkli kutuyla çizilir.
 */
(function (E) {
  "use strict";
  if (!E) return;

  const el = E.el, svg = E.svg, sahne = E.sahne, ok = E.ok, yazi = E.yazi, renk = E.renk, zemin = E.zemin;
  const Kesir = E.Kesir, Mat = E.Mat, matrisCiz = E.matrisCiz, metinDugum = E.metinDugum, texDugum = E.texDugum;
  const ALT_RAKAM = "₀₁₂₃₄₅₆₇₈₉";

  /* ------------------------------------------------------------------ küçük yardımcılar */

  function ind(n) { return String(n).split("").map(h => ALT_RAKAM[+h] || h).join(""); }
  function kisit(x, a, b) { return Math.max(a, Math.min(b, x)); }
  function bosalt(d) { while (d.firstChild) d.removeChild(d.firstChild); }
  function koy(d) {
    bosalt(d);
    const ekle = c => {
      if (!c) return;
      if (Array.isArray(c)) c.forEach(ekle);
      else d.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    };
    for (let k = 1; k < arguments.length; k++) ekle(arguments[k]);
    return d;
  }
  const T = x => Kesir.al(x).tex();
  const par = x => { const k = Kesir.al(x); return k.isaret() < 0 ? "(" + k.tex() + ")" : k.tex(); };
  const para = m => el("p", null, metinDugum(m));
  const blok = t => texDugum(t, true);
  const cip = (metin, aile) => el("span", { class: ["km-cip", aile] }, metin);
  const sozcuk = n => n + ". ";

  E.stilEkle("etkilesim-matris-stil", [
    ".km-kap{display:grid;gap:10px;min-width:0;max-width:100%}",
    ".km-kap [hidden],.km-cozum [hidden]{display:none!important}",
    ".km-sahne{text-align:center}",
    ".km-panel{background:var(--kart,#fff);border:1px solid var(--cizgi,#d9e1ee);border-radius:12px;padding:8px 12px;min-width:0;overflow-x:auto}",
    ".km-panel p{margin:4px 0}",
    ".km-panel .kx-tex-blok{margin:0;padding:2px 0}",
    ".km-giris{display:grid;gap:3px;min-width:0}",
    ".km-giris-ad{color:var(--soluk,#5b6b85);font-size:.9em}",
    ".km-girisler{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:8px 12px}",
    ".km-girdi{width:100%;min-width:0;min-height:40px;padding:6px 10px;border:1.5px solid var(--cizgi,#d9e1ee);border-radius:8px;" +
      "background:var(--kart,#fff);color:var(--metin,#15213a);font:inherit;font-size:16px;font-variant-numeric:tabular-nums}",
    ".km-girdi:focus{outline:none;border-color:var(--ana,#1e3a8a);box-shadow:0 0 0 3px var(--ana-acik,#e4ebfa)}",
    ".km-girdi.km-yanlis{border-color:var(--sema-sil,#dc2626)}",
    ".km-hata{color:var(--sema-sil,#dc2626);font-size:.88em}",
    ".km-hata:empty{display:none}",
    ".km-cip{display:inline-block;padding:0 .45em;border-radius:6px;font-weight:600;font-variant-numeric:tabular-nums}",
    ".km-cip.a{background:var(--sema-a-bg,rgba(37,99,235,.12));color:var(--sema-a,#2563eb)}",
    ".km-cip.b{background:var(--sema-b-bg,rgba(217,119,6,.14));color:var(--sema-b,#d97706)}",
    ".km-cip.c{background:var(--sema-c-bg,rgba(5,150,105,.13));color:var(--sema-c,#059669)}",
    ".km-cip.sil{background:var(--sema-sil-bg,rgba(220,38,38,.11));color:var(--sema-sil,#dc2626)}",
    ".km-tus{fill:transparent;stroke:none;cursor:pointer;pointer-events:all}",
    ".km-tus:focus{outline:none}",
    ".km-tus:focus-visible,.km-chip:focus-visible rect{stroke:var(--vurgu,#0e9f8f);stroke-width:2.5}",
    ".km-chip{cursor:pointer}",
    ".km-chip:focus{outline:none}",
    ".km-olcer{height:10px;border-radius:6px;background:var(--cizgi,#d9e1ee);overflow:hidden}",
    ".km-olcer>i{display:block;height:100%;width:0;background:var(--sema-b,#d97706);transition:width .1s}",
    ".km-olcer.yesil>i{background:var(--sema-c,#059669)}",
    ".km-cozum{display:grid;gap:8px;max-width:100%;min-width:0}",
    ".km-cozum p{margin:0}",
    ".km-cozum .kx-sahne{margin:0}",
    ".km-cozum .kx-tex-blok{padding:0}",
    ".km-tutamak-g{cursor:grab}",
    ".km-adim-no{color:var(--soluk,#5b6b85);font-size:.88em;font-variant-numeric:tabular-nums}",
    "@media (prefers-reduced-motion:reduce){.km-olcer>i{transition:none}}"
  ].join("\n"));

  /* ------------------------------------------------------------------ düzenlenebilir matris girdisi */

  function matrisGirisi(etiket, ilk, degisti, ayar) {
    ayar = ayar || {};
    const g = el("input", {
      type: "text", class: "km-girdi", spellcheck: "false", autocomplete: "off", autocapitalize: "off",
      enterkeyhint: "done", placeholder: "1 2; 3 4", "aria-label": String(etiket).replace(/\$/g, "")
    });
    const hata = el("span", { class: "km-hata", role: "status" });
    g.value = Mat.al(ilk).metin();
    g.addEventListener("input", () => {
      try {
        const M = Mat.oku(g.value);
        if (M.m > (ayar.enM || 6) || M.n > (ayar.enN || 8)) throw new RangeError("En çok " + (ayar.enM || 6) + " satır ve " + (ayar.enN || 8) + " sütun.");
        const h = ayar.kontrol ? ayar.kontrol(M) : null;
        if (h) throw new RangeError(h);
        hata.textContent = "";
        g.classList.remove("km-yanlis");
        degisti(M);
      } catch (h) {
        hata.textContent = (h && h.message) || "Okunamadı";
        g.classList.add("km-yanlis");
      }
    });
    return {
      kok: el("label", { class: "km-giris" }, el("span", { class: "km-giris-ad" }, metinDugum(etiket)), g, hata),
      girdi: g,
      ayarla(M) { g.value = Mat.al(M).metin(); hata.textContent = ""; g.classList.remove("km-yanlis"); }
    };
  }

  /* Adım düğmeleri: Geri, İleri, Baştan (+ isteğe bağlı Oynat). */
  function adimDugmeleri(ayar) {
    const dGeri = E.dugme("Geri", ayar.geri);
    const dIleri = E.dugme("İleri", ayar.ileri, { ana: true });
    const dBas = E.dugme("Baştan", ayar.bastan);
    const dOynat = ayar.oynat ? E.dugme("Oynat", ayar.oynat) : null;
    return {
      kok: el("div", { class: "kx-satir" }, dGeri, dIleri, dBas, dOynat),
      guncelle(s, N) { dGeri.disabled = s <= 0; dIleri.disabled = s >= N; dBas.disabled = s <= 0; },
      oynatYaz(calisiyor) { if (dOynat) dOynat.textContent = calisiyor ? "Durdur" : "Oynat"; }
    };
  }

  /* ------------------------------------------------------------------ SVG yardımcıları */

  /* Hücre merkezleri arasında, uçlardan kısaltılmış ok. */
  function okHucre(a, b, s) {
    s = s || {};
    const dx = b.cx - a.cx, dy = b.cy - a.cy, L = Math.hypot(dx, dy) || 1;
    const k1 = s.ilk === undefined ? 12 : s.ilk, k2 = s.son === undefined ? 14 : s.son;
    return ok(a.cx + dx / L * k1, a.cy + dy / L * k1, b.cx - dx / L * k2, b.cy - dy / L * k2, s);
  }

  /* Ortasında etiket, iki ucunda ok olan ölçü çizgisi. yatay: true → y = sabit, x a0..a1 arasında. */
  function ciftOk(yatay, sabit, a0, a1, etiket, aile) {
    const orta = (a0 + a1) / 2, yar = etiket.length * 3.4 + 7, g = svg("g", null);
    const o = { renk: aile, kalinlik: 1.6, bas: 6 };
    if (yatay) {
      g.appendChild(yazi(orta, sabit, etiket, { renk: aile, boyut: 12, kalin: true }));
      if (orta - a0 - yar > 10) { g.appendChild(ok(orta - yar, sabit, a0 + 1, sabit, o)); g.appendChild(ok(orta + yar, sabit, a1 - 1, sabit, o)); }
    } else {
      g.appendChild(svg("g", { transform: "rotate(-90 " + sabit + " " + orta + ")" }, yazi(sabit, orta, etiket, { renk: aile, boyut: 12, kalin: true })));
      if (orta - a0 - yar > 10) { g.appendChild(ok(sabit, orta - yar, sabit, a0 + 1, o)); g.appendChild(ok(sabit, orta + yar, sabit, a1 - 1, o)); }
    }
    return g;
  }

  /* Satır ve sütun numaralı, kenarlarında m ve n ölçüleri olan matris.
   * o: { ad, i, j, mod: hucre | satir | sutun, boyut, tus(i, j), enGenis } → { dugum, api, odak(i, j) } */
  function gostergeCiz(A, o) {
    o = Object.assign({ ad: "", i: -1, j: -1, mod: "hucre", boyut: true, tus: null, enGenis: 340 }, o || {});
    const ML = 42, MT = o.boyut ? 48 : 26;
    const c = kisit(Math.floor((o.enGenis - ML - 26) / A.n), 30, 52);
    const s = sahne(ML + A.n * c + 26, MT + A.m * c + 8, "Matris: " + A.m + " satır, " + A.n + " sütun");
    const M = matrisCiz(A, { x: ML, y: MT, hucre: c });
    s.appendChild(M.g);
    const sec = o.i >= 0 && o.j >= 0;
    if (sec) {
      if (o.mod !== "sutun") M.satirBoya(o.i, "a");
      if (o.mod !== "satir") M.sutunBoya(o.j, "b");
      M.boya(o.i, o.j, "c");
    }
    for (let j = 0; j < A.n; j++) {
      const on = sec && j === o.j && o.mod !== "satir";
      s.appendChild(yazi(M.hucre(0, j).cx, MT - 10, j + 1, { renk: on ? "b" : "soluk", kalin: on, boyut: 12 }));
    }
    for (let i = 0; i < A.m; i++) {
      const on = sec && i === o.i && o.mod !== "sutun";
      s.appendChild(yazi(ML - 8, M.hucre(i, 0).cy, i + 1, { renk: on ? "a" : "soluk", kalin: on, boyut: 12, hiza: "sag" }));
    }
    if (o.ad) s.appendChild(yazi(ML / 2 + 4, MT - 10, o.ad, { kalin: true, boyut: 15 }));
    if (o.boyut) {
      const h0 = M.hucre(0, 0), h1 = M.hucre(0, A.n - 1), v1 = M.hucre(A.m - 1, 0);
      s.appendChild(ciftOk(true, 12, h0.x, h1.x + c, "n = " + A.n + " sütun", "b"));
      s.appendChild(ciftOk(false, 11, h0.y, v1.y + c, "m = " + A.m + " satır", "a"));
    }
    if (o.tus) {
      const ilk = sec ? [o.i, o.j] : [0, 0];
      for (let i = 0; i < A.m; i++) {
        for (let j = 0; j < A.n; j++) {
          const h = M.hucre(i, j);
          s.appendChild(svg("rect", {
            class: "km-tus", x: h.x + 1.5, y: h.y + 1.5, width: c - 3, height: c - 3, rx: 6, role: "button",
            tabindex: i === ilk[0] && j === ilk[1] ? 0 : -1, dataset: { i: String(i), j: String(j) },
            "aria-label": (o.ad || "a").toLowerCase() + (i + 1) + (j + 1) + " = " + A.g(i, j) + ", " + (i + 1) + ". satır " + (j + 1) + ". sütun",
            onclick: () => o.tus(i, j),
            onkeydown: e => {
              const yon = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [-1, 0], ArrowDown: [1, 0] }[e.key];
              if (yon) {
                e.preventDefault();
                o.tus(kisit(i + yon[0], 0, A.m - 1), kisit(j + yon[1], 0, A.n - 1), true);
              } else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); o.tus(i, j); }
            }
          }));
        }
      }
    }
    return {
      dugum: s, api: M,
      odak(i, j) {
        const r = s.querySelector('[data-i="' + i + '"][data-j="' + j + '"]');
        if (r) r.focus({ preventScroll: true });
      }
    };
  }

  /* Yan yana matris denklemi: parcalar = [{ M, ad, boya, satir, sutun, kutu, bicim }, { yaz, gen, boyut, renk }].
   * ayar: { enGenis, hucre, ust, alt, oklar: [{ kimden: [parca, i, j], kime: [...], renk, egri }], sonra(svg, parcalar) } */
  function denklemSekli(parcalar, ayar) {
    ayar = Object.assign({ enGenis: 400, ust: 18, alt: 0, oklar: [], etiket: "Matris işlemi" }, ayar || {});
    const bosluk = 6, yazGen = 26;
    let kol = 0, nm = 0, ny = 0;
    parcalar.forEach(q => { if (q.M) { kol += q.M.n; nm++; } else ny++; });
    const c = ayar.hucre || kisit(Math.floor((ayar.enGenis - ny * (yazGen + bosluk) - nm * (16 + bosluk)) / Math.max(1, kol)), 24, 42);
    let H = 0;
    parcalar.forEach(q => { if (q.M) H = Math.max(H, q.M.m * c); });
    let x = 0;
    parcalar.forEach(q => {
      if (q.M) {
        q.cizim = matrisCiz(q.M, { x, y: ayar.ust + (H - q.M.m * c) / 2, hucre: c, bicim: q.bicim });
        q.x0 = x;
        x += q.cizim.genislik + bosluk;
      } else {
        const g = q.gen || yazGen;
        q.x0 = x;
        q.xm = x + g / 2;
        x += g + bosluk;
      }
    });
    const s = sahne(Math.max(40, x - bosluk), ayar.ust + H + ayar.alt, ayar.etiket);
    parcalar.forEach(q => {
      if (q.M) {
        const ap = q.cizim;
        (q.satir || []).forEach(a => ap.satirBoya(a[0], a[1]));
        (q.sutun || []).forEach(a => ap.sutunBoya(a[0], a[1]));
        (q.boya || []).forEach(a => ap.boya(a[0], a[1], a[2]));
        s.appendChild(ap.g);
        (q.kutu || []).forEach(a => ap.kutu(a[0], a[1], a[2], a[3], a[4], a[5]));
        if (q.ad) s.appendChild(yazi(q.x0 + ap.genislik / 2, 7, q.ad, { renk: "soluk", boyut: 12, kalin: true }));
      } else {
        s.appendChild(yazi(q.xm, ayar.ust + H / 2, q.yaz, { boyut: q.boyut || 20, kalin: true, renk: q.renk || "soluk" }));
      }
    });
    ayar.oklar.forEach(o => {
      const a = parcalar[o.kimden[0]].cizim.hucre(o.kimden[1], o.kimden[2]);
      const b = parcalar[o.kime[0]].cizim.hucre(o.kime[1], o.kime[2]);
      s.appendChild(okHucre(a, b, { renk: o.renk, egri: o.egri, kalinlik: o.kalinlik || 2, bas: 6, ilk: o.ilk, son: o.son }));
    });
    if (ayar.sonra) ayar.sonra(s, parcalar, c);
    return s;
  }

  const sahneKap = d => el("div", { class: "kx-sahne km-sahne" }, d);
  const cozumKutusu = (...c) => el("div", { class: "km-cozum" }, c);

  /* ------------------------------------------------------------------ Gauss–Jordan adımları (kesin kesir) */

  /* A (n×n) ve R (n×r) için [A | R] üzerinde adımları üretir.
   * durumlar[s] s. işlemden sonraki satırlar; islemler[s-1] o işlem: yer | bol | cikar | tekil. */
  function gaussAdimlari(A, R) {
    const n = A.m;
    const a = A.v.map((r, i) => r.concat(R.v[i]));
    const durumlar = [a.map(r => r.slice())], islemler = [];
    let tekil = false;
    const kaydet = op => { islemler.push(op); durumlar.push(a.map(r => r.slice())); };
    for (let k = 0; k < n; k++) {
      let p = k;
      while (p < n && a[p][k].sifirMi()) p++;
      if (p === n) { islemler.push({ tur: "tekil", k }); tekil = true; break; }
      if (p !== k) { const t = a[p]; a[p] = a[k]; a[k] = t; kaydet({ tur: "yer", k, i: p }); }
      const piv = a[k][k];
      if (!piv.esit(1)) { a[k] = a[k].map(x => x.bol(piv)); kaydet({ tur: "bol", k, c: piv }); }
      for (let i = 0; i < n; i++) {
        if (i === k || a[i][k].sifirMi()) continue;
        const c = a[i][k];
        a[i] = a[i].map((x, j) => x.cikar(c.carp(a[k][j])));
        kaydet({ tur: "cikar", k, i, c });
      }
    }
    return { durumlar, islemler, tekil, n };
  }

  function islemTex(op) {
    const R = x => "R_{" + (x + 1) + "}";
    if (op.tur === "yer") return R(op.k) + " \\leftrightarrow " + R(op.i);
    if (op.tur === "bol") {
      if (op.c.tamMi()) return R(op.k) + " \\leftarrow \\dfrac{" + R(op.k) + "}{" + op.c.tex() + "}";
      const t = op.c.ters();
      return R(op.k) + " \\leftarrow " + (t.isaret() < 0 ? "\\left(" + t.tex() + "\\right)" : t.tex()) + R(op.k);
    }
    if (op.tur === "cikar") {
      const mut = op.c.mutlak(), kat = mut.esit(1) ? "" : mut.tex();
      return R(op.i) + " \\leftarrow " + R(op.i) + (op.c.isaret() > 0 ? " - " : " + ") + kat + R(op.k);
    }
    return "";
  }

  function islemKisa(op) {
    const R = x => "R" + ind(x + 1);
    if (op.tur === "yer") return R(op.k) + " ↔ " + R(op.i);
    if (op.tur === "bol") return R(op.k) + " ← " + R(op.k) + " ÷ " + op.c.toString();
    if (op.tur === "cikar") return R(op.i) + " ← " + R(op.i) + (op.c.isaret() > 0 ? " − " : " + ") + (op.c.mutlak().esit(1) ? "" : op.c.mutlak().toString() + "·") + R(op.k);
    return "pivot yok";
  }

  function islemAciklama(op) {
    if (op.tur === "yer") return "Pivot yerindeki eleman sıfır; aşağıdaki sıfırdan farklı satırla yer değiştirdik.";
    if (op.tur === "bol") return "Pivotu 1 yapmak için pivot satırını pivota böldük.";
    if (op.tur === "cikar") return "Pivot satırının uygun katını " + (op.i + 1) + ". satırdan çıkardık; (" + (op.i + 1) + ", " + (op.k + 1) + ") hücresi sıfırlandı.";
    return "Bu sütunda pivot olacak sıfırdan farklı eleman kalmadı: matris tekil (det = 0).";
  }

  /* Genişletilmiş matrisin bir durumunu çizer. o: { islem (az önce yapılan), sonraki, bitti, tekil, enGenis } */
  function gaussCiz(durum, nA, o) {
    o = o || {};
    const m = durum.length, w = durum[0].length;
    const ML = 58, SAG = 44;
    const c = kisit(Math.floor(((o.enGenis || 340) - ML - 16 - SAG) / w), 36, 46);
    const s = sahne(ML + w * c + 16 + SAG, m * c + 10, "Genişletilmiş matris ve satır işlemi");
    const M = matrisCiz(new Mat(durum), { x: ML, y: 5, hucre: c });
    if (w >= 7) for (let i = 0; i < m; i++) for (let j = 0; j < w; j++) M.yaziDugumu(i, j).style.fontSize = "11px";
    s.appendChild(M.g);
    const op = o.islem, sn = o.sonraki;
    if (op && op.tur !== "tekil") {
      M.satirBoya(op.k, "a");
      if (op.tur === "cikar") { M.satirBoya(op.i, "b"); M.boya(op.i, op.k, "c"); }
      if (op.tur === "yer") M.satirBoya(op.i, "b");
      if (op.tur === "bol") M.boya(op.k, op.k, "c");
    }
    if (op && op.tur === "tekil") M.sutunBoya(op.k, "sil");
    if (sn && sn.tur === "cikar") M.boya(sn.i, sn.k, "sil");
    if (op && op.tur !== "tekil") M.kutu(op.k, op.k, op.k, op.k, "c", { kalinlik: 2.5 });
    if (o.bitti) M.kutu(0, nA, m - 1, w - 1, "c", { dolgu: true, kalinlik: 2.5 });
    const ayrac = ML + 8 + nA * c;
    s.appendChild(svg("line", { x1: ayrac, y1: 3, x2: ayrac, y2: m * c + 7, "stroke-width": 2, "stroke-dasharray": "4 3", style: { stroke: renk("cizgi") } }));
    for (let i = 0; i < m; i++) {
      const on = op && op.tur !== "tekil" ? (i === op.k ? "a" : ((op.tur === "cikar" || op.tur === "yer") && i === op.i ? "b" : "soluk")) : "soluk";
      s.appendChild(yazi(14, M.hucre(i, 0).cy, "R" + ind(i + 1), { renk: on, kalin: on !== "soluk", boyut: 12 }));
    }
    if (op && (op.tur === "cikar" || op.tur === "yer")) {
      const y1 = M.hucre(op.k, 0).cy, y2 = M.hucre(op.i, 0).cy, e = (y2 > y1 ? 1 : -1) * 0.3;
      s.appendChild(ok(42, y1, 42, y2, { renk: "b", egri: e, kalinlik: 2, bas: 6 }));
      if (op.tur === "yer") s.appendChild(ok(42, y2, 42, y1, { renk: "b", egri: -e, kalinlik: 2, bas: 6 }));
    }
    if (op && op.tur === "bol") {
      s.appendChild(yazi(ML + w * c + 22, M.hucre(op.k, 0).cy, "÷ " + op.c.toString(), { renk: "a", boyut: 12, kalin: true, hiza: "sol" }));
    }
    return { dugum: s, api: M };
  }

  /* ================================================================ 1. matris-gezgini */

  E.kaydet("matris-gezgini", function (kok, p) {
    let A = Mat.al(p.A), si = 0, sj = 0, mod = "hucre", sinav = null;
    const ad = String(p.ad || "A"), kucuk = ad.toLowerCase();
    const sekilKutu = el("div", { class: "kx-sahne km-sahne" });
    const bilgi = el("div", { class: "km-panel", "aria-live": "polite" });
    const geri = el("p", { class: "kx-geri", role: "status" });
    const dSinav = E.dugme("Beni sına", () => sinavBaslat());
    const dIptal = E.dugme("Sınavı bırak", () => { sinav = null; geri.className = "kx-geri"; koy(geri); dIptal.hidden = true; ciz(); });
    dIptal.hidden = true;
    const modSec = E.secici([{ deger: "hucre", etiket: "Hücre" }, { deger: "satir", etiket: "Satır" }, { deger: "sutun", etiket: "Sütun" }], "hucre", v => { mod = v; ciz(); });
    const giris = matrisGirisi("Kendi matrisini yaz (satırlar noktalı virgülle ayrılır)", A, M => {
      A = M; si = Math.min(si, A.m - 1); sj = Math.min(sj, A.n - 1); sinav = null; dIptal.hidden = true; koy(geri); ciz();
    }, { enM: 6, enN: 7 });

    function sec(i, j, klavye) {
      if (sinav && !klavye) {
        const dogru = i === sinav.i && j === sinav.j;
        geri.className = "kx-geri " + (dogru ? "dogru" : "yanlis");
        koy(geri, metinDugum(dogru
          ? "Doğru! $" + kucuk + "_{" + (i + 1) + (j + 1) + "}$ " + (i + 1) + ". satır ile " + (j + 1) + ". sütunun kesiştiği hücredir."
          : "O hücre $" + kucuk + "_{" + (i + 1) + (j + 1) + "}$. Aradığın $" + kucuk + "_{" + (sinav.i + 1) + (sinav.j + 1) + "}$: önce satır, sonra sütun."));
        si = i; sj = j;
        if (dogru) { sinav = null; dIptal.hidden = true; }
      } else { si = i; sj = j; }
      ciz();
    }

    function sinavBaslat() {
      const r = E.rastgele((Date.now() ^ (Math.random() * 4294967296)) >>> 0);
      sinav = { i: r.tam(0, A.m - 1), j: r.tam(0, A.n - 1) };
      dIptal.hidden = false;
      geri.className = "kx-geri";
      koy(geri, metinDugum("**Bul:** $" + kucuk + "_{" + (sinav.i + 1) + (sinav.j + 1) + "}$ hangi hücre? Dokun."));
      ciz();
    }

    function ciz() {
      const a = document.activeElement;
      const odakta = !!(a && kok.contains(a) && a.classList && a.classList.contains("km-tus"));
      const g = gostergeCiz(A, { ad, i: si, j: sj, mod: sinav ? "hucre" : mod, tus: sec, enGenis: 340 });
      if (sinav) { g.api.sifirla(); }
      koy(sekilKutu, g.dugum);
      if (odakta) g.odak(si, sj);
      const x = A.g(si, sj);
      const satirM = new Mat([A.satir(si)]), sutunM = new Mat(A.sutun(sj).map(v => [v]));
      koy(bilgi,
        el("p", null, metinDugum("Seçili hücre: "), cip(kucuk + ind(si + 1) + ind(sj + 1), "c"), metinDugum(" = **" + x.toString() + "**  →  "),
          cip((si + 1) + ". satır", "a"), metinDugum(" ve "), cip((sj + 1) + ". sütun", "b")),
        el("p", null, metinDugum("Boyut: "), cip(A.m + " satır", "a"), metinDugum(" × "), cip(A.n + " sütun", "b"),
          metinDugum(" = **" + A.m * A.n + " eleman**. Boyut hep satır × sütun sırasıyla söylenir.")),
        el("div", { style: { display: "flex", flexWrap: "wrap", gap: "6px 22px", alignItems: "center" } },
          el("div", null, el("div", { class: "km-giris-ad" }, "Satır " + (si + 1) + " (1×" + A.n + ")"), blok("\\mathbf{r}_{" + (si + 1) + "}=" + satirM.tex({ vurgu: () => "ka" }))),
          el("div", null, el("div", { class: "km-giris-ad" }, "Sütun " + (sj + 1) + " (" + A.m + "×1)"), blok("\\mathbf{c}_{" + (sj + 1) + "}=" + sutunM.tex({ vurgu: () => "kb" })))));
    }

    kok.appendChild(el("div", { class: "km-kap" }, el("div", { class: "kx-satir" }, metinDugum("Göster:"), modSec.kok, dSinav, dIptal), sekilKutu, geri, bilgi,
      el("details", null, el("summary", null, "Kendi matrisini dene"), giris.kok)));
    ciz();
    return { yok_et() { sinav = null; } };
  }, {
    baslik: "Matris gezgini",
    aciklama: "Bir hücreye dokun: satırı mavi, sütunu turuncu, kendisi yeşil yanar; $a_{ij}$ adı, boyutlar ve satır/sütun vektörü görünür.",
    varsayilan: { A: "2 0 7 1; 5 -3 4 8; 6 9 -2 0", ad: "A" }
  });

  /* ================================================================ 2. eleman-eleman */

  function boyutaUydur(M, m, n) {
    return new Mat(Array.from({ length: m }, (_, i) => Array.from({ length: n }, (_, j) => (i < M.m && j < M.n ? M.g(i, j) : Kesir.SIFIR))));
  }

  E.kaydet("eleman-eleman", function (kok, p) {
    let A = Mat.al(p.A), B = Mat.al(p.B), islem = p.islem === "cikar" || p.islem === "skaler" ? p.islem : "topla";
    let k = Kesir.al(p.k === undefined ? 2 : p.k), s = 0, oyn = null;
    if (islem !== "skaler" && (A.m !== B.m || A.n !== B.n)) B = boyutaUydur(B, A.m, A.n);
    const sekilKutu = el("div", { class: "kx-sahne km-sahne" });
    const formul = el("div", { class: "km-panel", "aria-live": "polite" });
    const kRange = E.kaydirici({ etiket: "Çarpan $k$", min: -5, max: 5, adim: 1, deger: Number(k.sayi()), degisince: v => { k = Kesir.al(v); dur(); ciz(); } });
    const adim = adimDugmeleri({
      geri: () => { dur(); s = Math.max(0, s - 1); ciz(); },
      ileri: () => { dur(); s = Math.min(A.m * A.n, s + 1); ciz(); },
      bastan: () => { dur(); s = 0; ciz(); },
      oynat: () => oynat()
    });
    const gA = matrisGirisi("$A$ matrisi", A, M => {
      A = M;
      if (islem !== "skaler" && (B.m !== M.m || B.n !== M.n)) { B = boyutaUydur(B, M.m, M.n); gB.ayarla(B); }
      dur(); s = 0; ciz();
    }, { enM: 5, enN: 5 });
    const gB = matrisGirisi("$B$ matrisi", B, M => {
      B = M;
      if (A.m !== M.m || A.n !== M.n) { A = boyutaUydur(A, M.m, M.n); gA.ayarla(A); }
      dur(); s = 0; ciz();
    }, { enM: 5, enN: 5 });
    const islemSec = E.secici([{ deger: "topla", etiket: "$A+B$" }, { deger: "cikar", etiket: "$A-B$" }, { deger: "skaler", etiket: "$kA$" }], islem, v => {
      islem = v;
      if (islem !== "skaler" && (A.m !== B.m || A.n !== B.n)) { B = boyutaUydur(B, A.m, A.n); gB.ayarla(B); }
      dur(); s = 0; ciz();
    });

    function dur() { if (oyn) { oyn.durdur(); oyn = null; } adim.oynatYaz(false); }

    function oynat() {
      if (oyn && oyn.calisiyor()) { dur(); return; }
      const N = A.m * A.n;
      if (E.hareketAzalt()) { s = N; ciz(); return; }
      if (s >= N) s = 0;
      let birikim = 0.9;
      oyn = E.animasyon(kok, (t, dt) => {
        birikim += dt;
        if (birikim < 0.9) return true;
        birikim = 0;
        if (s < N) { s++; ciz(); }
        if (s >= N) { adim.oynatYaz(false); return false; }
        return true;
      });
      adim.oynatYaz(true);
    }

    function sonuc() { return islem === "topla" ? A.topla(B) : islem === "cikar" ? A.cikar(B) : A.skaler(k); }

    function ciz() {
      const C = sonuc(), N = A.m * A.n, n = A.n, c = s - 1;
      const ci = c >= 0 ? Math.floor(c / n) : -1, cj = c >= 0 ? c % n : -1;
      const aB = [], bB = [], cB = [];
      for (let t = 0; t < s - 1; t++) {
        const i = Math.floor(t / n), j = t % n;
        aB.push([i, j, "cizgi"]); bB.push([i, j, "cizgi"]); cB.push([i, j, "c"]);
      }
      if (c >= 0) { aB.push([ci, cj, "a"]); bB.push([ci, cj, "b"]); cB.push([ci, cj, "c"]); }
      const op = islem === "topla" ? "+" : islem === "cikar" ? "−" : "";
      const parcalar = islem === "skaler"
        ? [{ yaz: k.toString(), gen: 34, boyut: 17, renk: "b" }, { M: A, ad: "A", boya: aB }, { yaz: "=" }, { M: C, ad: "C = kA", boya: cB, kutu: c >= 0 ? [[ci, cj, ci, cj, "c", { kalinlik: 2.5 }]] : [] }]
        : [{ M: A, ad: "A", boya: aB }, { yaz: op, renk: "ana" }, { M: B, ad: "B", boya: bB }, { yaz: "=" }, { M: C, ad: "C", boya: cB, kutu: c >= 0 ? [[ci, cj, ci, cj, "c", { kalinlik: 2.5 }]] : [] }];
      const iA = islem === "skaler" ? 1 : 0, iB = 2, iC = parcalar.length - 1;
      const oklar = [];
      if (c >= 0) {
        oklar.push({ kimden: [iA, ci, cj], kime: [iC, ci, cj], renk: "a", egri: islem === "skaler" ? -0.3 : -0.35 });
        if (islem !== "skaler") oklar.push({ kimden: [iB, ci, cj], kime: [iC, ci, cj], renk: "b", egri: -0.35 });
      }
      const sk = denklemSekli(parcalar, {
        enGenis: 350, oklar, etiket: "Karşılıklı hücreler sonuca akar",
        sonra(sv, ps, hu) {
          const Cc = ps[iC].cizim;
          for (let i = 0; i < A.m; i++) {
            for (let j = 0; j < n; j++) {
              if (i * n + j >= s) Cc.yaz(i, j, "?");
              const h = Cc.hucre(i, j);
              sv.appendChild(svg("rect", {
                class: "km-tus", x: h.x + 1.5, y: h.y + 1.5, width: hu - 3, height: hu - 3, rx: 6, role: "button", tabindex: 0,
                "aria-label": "Sonuç hücresi " + (i + 1) + "," + (j + 1) + ": buraya git",
                onclick: () => { dur(); s = i * n + j + 1; ciz(); },
                onkeydown: e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); dur(); s = i * n + j + 1; ciz(); } }
              }));
            }
          }
        }
      });
      koy(sekilKutu, sk);
      adim.guncelle(s, N);
      const kucukC = "c_{" + (c >= 0 ? (ci + 1) + "" + (cj + 1) : "ij") + "}";
      const isim = c >= 0 ? (ci + 1) + "" + (cj + 1) : "ij";
      let satirlar;
      if (c < 0) {
        satirlar = [el("p", null, metinDugum(islem === "skaler"
          ? "Her hücre ayrı ayrı $k$ ile çarpılır. **İleri**'ye bas ya da sonuç matrisinde bir kutuya dokun."
          : "Karşılıklı (aynı konumdaki) hücreler toplanır. **İleri**'ye bas ya da sonuç matrisinde bir kutuya dokun."))];
      } else {
        const a = A.g(ci, cj), b = B.g(ci, cj), r = C.g(ci, cj);
        const tx = islem === "topla"
          ? kucukC + "=\\ka{a_{" + isim + "}}+\\kb{b_{" + isim + "}}=\\ka{" + par(a) + "}+\\kb{" + par(b) + "}=\\kc{" + T(r) + "}"
          : islem === "cikar"
            ? kucukC + "=\\ka{a_{" + isim + "}}-\\kb{b_{" + isim + "}}=\\ka{" + par(a) + "}-\\kb{" + par(b) + "}=\\kc{" + T(r) + "}"
            : kucukC + "=\\kb{k}\\cdot\\ka{a_{" + isim + "}}=\\kb{" + par(k) + "}\\cdot\\ka{" + par(a) + "}=\\kc{" + T(r) + "}";
        satirlar = [el("p", null, cip("adım " + s + " / " + N, "c"), metinDugum(" " + (ci + 1) + ". satır, " + (cj + 1) + ". sütun")), blok(tx)];
      }
      if (s >= N) {
        satirlar.push(el("p", null, metinDugum(islem === "skaler"
          ? "**Bitti.** Boyut değişmedi: " + C.m + "×" + C.n + ". Sonuçtaki her hücre $k$ kat büyüdü."
          : "**Bitti.** İki matris de " + A.m + "×" + A.n + " idi; sonuç da " + C.m + "×" + C.n + ". Boyutlar farklı olsaydı bu işlem tanımsız olurdu.")));
      }
      koy(formul, satirlar);
      kRange.kok.hidden = islem !== "skaler";
      gB.kok.hidden = islem === "skaler";
    }

    kok.appendChild(el("div", { class: "km-kap" },
      el("div", { class: "kx-satir" }, metinDugum("İşlem:"), islemSec.kok), kRange.kok, sekilKutu, adim.kok, formul,
      el("details", null, el("summary", null, "Kendi matrislerini dene"), el("div", { class: "km-girisler" }, gA.kok, gB.kok))));
    ciz();
    return { yok_et() { dur(); } };
  }, {
    baslik: "Eleman eleman işlem",
    aciklama: "Toplama, çıkarma ve skalerle çarpmada karşılıklı hücreler oklarla sonuca akar; adım adım ya da oynat.",
    varsayilan: { A: "2 -1 3; 0 4 1", B: "1 5 -2; 3 -1 2", islem: "topla", k: 2 }
  });

  /* ================================================================ 3. carpim-gezgini */

  E.kaydet("carpim-gezgini", function (kok, p) {
    let A = Mat.al(p.A), B = Mat.al(p.B), si = 0, sj = 0, kt = null, oyn = null;
    const sekilKutu = el("div", { class: "kx-sahne km-sahne" });
    const boyutKutu = el("div", { class: "km-panel", "aria-live": "polite" });
    const formul = el("div", { class: "km-panel", "aria-live": "polite" });
    const adim = adimDugmeleri({
      geri: () => { dur(); kt = Math.max(0, (kt === null ? A.n : kt) - 1); ciz(); },
      ileri: () => { dur(); kt = Math.min(A.n, (kt === null ? A.n : kt) + 1); ciz(); },
      bastan: () => { dur(); kt = 0; ciz(); },
      oynat: () => oynat()
    });
    const gA = matrisGirisi("$A$ matrisi", A, M => { A = M; yenile(); }, { enM: 5, enN: 5 });
    const gB = matrisGirisi("$B$ matrisi", B, M => { B = M; yenile(); }, { enM: 5, enN: 5 });

    function yenile() { dur(); si = Math.min(si, A.m - 1); sj = Math.min(sj, Math.max(0, B.n - 1)); kt = null; ciz(); }
    function dur() { if (oyn) { oyn.durdur(); oyn = null; } adim.oynatYaz(false); }

    function oynat() {
      if (oyn && oyn.calisiyor()) { dur(); return; }
      if (A.n !== B.m) return;
      if (E.hareketAzalt()) { kt = A.n; ciz(); return; }
      if (kt === null || kt >= A.n) kt = 0;
      let birikim = 0.9;
      ciz();
      oyn = E.animasyon(kok, (t, dt) => {
        birikim += dt;
        if (birikim < 0.9) return true;
        birikim = 0;
        if (kt < A.n) { kt++; ciz(); }
        if (kt >= A.n) { adim.oynatYaz(false); return false; }
        return true;
      });
      adim.oynatYaz(true);
    }

    function secHucre(i, j) { dur(); si = i; sj = j; kt = null; ciz(); }

    function ciz() {
      const tanimli = A.n === B.m;
      const boyutlar = el("p", null,
        cip("A: " + A.m + "×" + A.n, "a"), metinDugum("  ·  "), cip("B: " + B.m + "×" + B.n, "b"), metinDugum("  →  "),
        tanimli
          ? [metinDugum("iç boyutlar "), cip(A.n + " = " + B.m + " ✓", "c"), metinDugum("  →  sonuç "), cip(A.m + "×" + B.n, "c")]
          : [metinDugum("iç boyutlar "), cip(A.n + " ≠ " + B.m, "sil"), metinDugum(" → **çarpım tanımsız**")]);
      koy(boyutKutu, boyutlar);
      if (!tanimli) {
        const c0 = kisit(Math.floor(300 / (A.n + B.n)), 26, 40);
        const MA = matrisCiz(A, { hucre: c0, x: 0, y: 0 }), MB = matrisCiz(B, { hucre: c0, x: MA.genislik + 40, y: 0 });
        const sv = sahne(MA.genislik + MB.genislik + 40, Math.max(MA.yukseklik, MB.yukseklik), "İç boyutlar uyuşmuyor");
        sv.append(MA.g, MB.g, yazi(MA.genislik + 20, Math.max(MA.yukseklik, MB.yukseklik) / 2, "×", { boyut: 20, kalin: true }));
        MA.sutunBoya(A.n - 1, "sil");
        for (let j = 0; j < B.n; j++) MB.boya(0, j, "sil");
        koy(sekilKutu, sv);
        koy(formul, el("p", null, metinDugum("$A$'nın sütun sayısı ($" + A.n + "$) ile $B$'nin satır sayısı ($" + B.m + "$) eşit değil. Satırın elemanlarıyla sütunun elemanları **bire bir eşleşemez**; bu yüzden $AB$ yoktur.")));
        adim.guncelle(0, 0);
        return;
      }
      const C = A.carp(B), K = A.n;
      if (kt === null) kt = K;
      const kk = kt - 1;
      const c = kisit(Math.floor(310 / (A.n + B.n)), 26, 44), bos = 12, ust = 22;
      const xB = A.n * c + 16 + bos;
      const yA = ust + B.m * c + bos;
      const MBc = matrisCiz(B, { hucre: c, x: xB, y: ust });
      const MAc = matrisCiz(A, { hucre: c, x: 0, y: yA });
      const MCc = matrisCiz(C, { hucre: c, x: xB, y: yA });
      const sv = sahne(xB + Math.max(MBc.genislik, MCc.genislik), yA + A.m * c, "Falk şeması: A sol altta, B sağ üstte, C sağ altta");
      MAc.satirBoya(si, "a"); MBc.sutunBoya(sj, "b");
      MCc.satirBoya(si, "a");
      for (let i = 0; i < C.m; i++) if (i !== si) MCc.boya(i, sj, "b");
      MCc.boya(si, sj, "c");
      if (kk >= 0) { MAc.boya(si, kk, "c"); MBc.boya(kk, sj, "c"); }
      sv.append(MBc.g, MAc.g, MCc.g);
      if (kk >= 0) {
        MAc.kutu(si, kk, si, kk, "c", { kalinlik: 2.5 });
        MBc.kutu(kk, sj, kk, sj, "c", { kalinlik: 2.5 });
      }
      MCc.kutu(si, sj, si, sj, "c", { kalinlik: 2.5, dolgu: kt >= K });
      sv.appendChild(yazi(xB + MBc.genislik / 2, 8, "B", { renk: "b", kalin: true, boyut: 13 }));
      sv.appendChild(yazi(MAc.genislik / 2, yA - 7, "A", { renk: "a", kalin: true, boyut: 13 }));
      sv.appendChild(yazi(xB + MCc.genislik / 2, yA - 7, "C = AB", { renk: "c", kalin: true, boyut: 13 }));
      sv.appendChild(yazi(MAc.genislik / 2, ust + B.m * c / 2, "satır ×", { renk: "soluk", boyut: 11 }));
      sv.appendChild(yazi(MAc.genislik / 2, ust + B.m * c / 2 + 14, "sütun", { renk: "soluk", boyut: 11 }));
      if (kk >= 0) {
        const hA = MAc.hucre(si, kk), hB = MBc.hucre(kk, sj), hC = MCc.hucre(si, sj);
        sv.appendChild(ok(hA.cx + 8, hA.cy + 14, hC.cx - 6, hA.cy + 14, { renk: "a", kalinlik: 2, bas: 6 }));
        sv.appendChild(ok(hB.cx + 14, hB.cy + 8, hB.cx + 14, hC.cy - 6, { renk: "b", kalinlik: 2, bas: 6 }));
      }
      for (let i = 0; i < C.m; i++) {
        for (let j = 0; j < C.n; j++) {
          const h = MCc.hucre(i, j);
          sv.appendChild(svg("rect", {
            class: "km-tus", x: h.x + 1.5, y: h.y + 1.5, width: c - 3, height: c - 3, rx: 6, role: "button", tabindex: 0,
            "aria-label": "c" + (i + 1) + (j + 1) + " = " + C.g(i, j) + ": bu hücreyi hesapla",
            onclick: () => secHucre(i, j),
            onkeydown: e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); secHucre(i, j); } }
          }));
        }
      }
      koy(sekilKutu, sv);
      // terim satırları
      const terim = t => "\\ka{" + par(A.g(si, t)) + "}\\!\\cdot\\!\\kb{" + par(B.g(t, sj)) + "}";
      const adlar = "c_{" + (si + 1) + (sj + 1) + "}";
      let sembol = [], sayisal = [], toplam = Kesir.SIFIR;
      for (let t = 0; t < K; t++) sembol.push("a_{" + (si + 1) + (t + 1) + "}b_{" + (t + 1) + (sj + 1) + "}");
      for (let t = 0; t < kt; t++) {
        const dj = terim(t);
        sayisal.push(t === kk && kt < K ? "\\kutuc{" + dj + "}" : dj);
        toplam = toplam.topla(A.g(si, t).carp(B.g(t, sj)));
      }
      const satirlar = [
        el("p", null, metinDugum("Seçili: "), cip("c" + ind(si + 1) + ind(sj + 1), "c"), metinDugum(" = A'nın "), cip((si + 1) + ". satırı", "a"),
          metinDugum(" · B'nin "), cip((sj + 1) + ". sütunu", "b")),
        blok(adlar + "=" + sembol.join("+")),
        blok(kt === 0 ? adlar + "=\\;?" : adlar + "=" + sayisal.join("+") + (kt < K ? "+\\cdots" : "") + "=" + (kt >= K ? "\\kutuc{\\kc{" + T(toplam) + "}}" : "\\kc{" + T(toplam) + "}\\;\\text{(şimdilik)}"))
      ];
      if (kt >= K) satirlar.push(el("p", null, metinDugum("Dokunduğun hücre **" + toplam.toString() + "**. Sonuçtaki başka bir yeşil kutuya dokunup aynı işlemi tekrarla.")));
      else satirlar.push(el("p", null, metinDugum("Terim " + kt + " / " + K + ": her adımda **A'dan bir sayı × B'den bir sayı** çarpılıp toplama eklenir.")));
      koy(formul, satirlar);
      adim.guncelle(kt, K);
    }

    kok.appendChild(el("div", { class: "km-kap" }, boyutKutu, sekilKutu, adim.kok, formul,
      el("details", null, el("summary", null, "Kendi matrislerini dene"), el("div", { class: "km-girisler" }, gA.kok, gB.kok))));
    ciz();
    return { yok_et() { dur(); } };
  }, {
    baslik: "Matris çarpımı gezgini",
    aciklama: "Sonuç hücresine dokun: A'nın satırı mavi, B'nin sütunu turuncu yanar; terim terim çarpılıp toplanır. İç boyutlar denetlenir.",
    varsayilan: { A: "1 2 3; 4 5 6", B: "7 8; 9 10; 11 12" }
  });

  /* ================================================================ 4. transpoz-aynasi */

  const SATIR_RENK = ["a", "b", "c"], SATIR_MAKRO = ["ka", "kb", "kc"];

  E.kaydet("transpoz-aynasi", function (kok, p) {
    let A = Mat.al(p.A), t = 0, sec = null, oyn = null, yon = 1;
    let jetonlar = [], ustKatman = null, bolgeA = null, bolgeT = null, N = 0, c = 40, yer = null;
    const sahneKutu = el("div", { class: "kx-sahne km-sahne" });
    const bilgi = el("div", { class: "km-panel", "aria-live": "polite" });
    const tPanel = el("div", { class: "km-panel" });
    const kay = E.kaydirici({
      etiket: "Ayna: soldan sağa", min: 0, max: 1, adim: 0.01, deger: 0,
      bicim: v => (v < 0.005 ? "A" : v > 0.995 ? "Aᵀ" : Math.round(v * 100) + "%"),
      degisince: v => { dur(); t = v; yerlestir(); }
    });
    const dCevir = E.dugme("Aynayı çevir", () => cevir(), { ana: true });
    const giris = matrisGirisi("Kendi matrisini yaz (satırlar noktalı virgülle ayrılır)", A, M => { A = M; sec = null; dur(); kur(); }, { enM: 5, enN: 5 });

    function dur() { if (oyn) { oyn.durdur(); oyn = null; } }

    function cevir() {
      if (oyn && oyn.calisiyor()) { dur(); return; }
      const hedef = t < 0.5 ? 1 : 0;
      if (E.hareketAzalt()) { t = hedef; kay.ayarla(t, true); yerlestir(); return; }
      oyn = E.animasyon(kok, (_, dt) => {
        t += (hedef ? 1 : -1) * dt / 1.6;
        if ((hedef && t >= 1) || (!hedef && t <= 0)) { t = hedef; kay.ayarla(t, true); yerlestir(); return false; }
        kay.ayarla(t, true); yerlestir();
        return true;
      });
    }

    function poz(i, j) { return { x: 8 + j * c, y: 18 + i * c }; }

    function yerlestir() {
      const e = t * t * (3 - 2 * t);
      jetonlar.forEach(j => {
        const a = poz(j.i, j.j), b = poz(j.j, j.i);
        const dx = b.x - a.x, dy = b.y - a.y, bump = Math.sin(Math.PI * e) * 0.22;
        j.g.setAttribute("transform", "translate(" + (a.x + dx * e + dy * bump).toFixed(1) + " " + (a.y + dy * e - dx * bump).toFixed(1) + ")");
      });
      if (bolgeA) bolgeA.style.opacity = String(1 - e);
      if (bolgeT) bolgeT.style.opacity = String(e);
      bilgiYaz();
    }

    function sec_(i, j) { sec = [i, j]; secimCiz(); bilgiYaz(); }

    function secimCiz() {
      bosalt(ustKatman);
      if (!sec) return;
      const [i, j] = sec;
      jetonlar.forEach(k => k.g.classList.toggle("km-sec", k.i === i && k.j === j));
      if (i === j) return;
      const a = poz(i, j), b = poz(j, i);
      ustKatman.appendChild(ok(a.x + c / 2, a.y + c / 2, b.x + c / 2, b.y + c / 2, { renk: "c", egri: 0.35, kalinlik: 2, bas: 7, kesik: true }));
    }

    function bilgiYaz() {
      const T_ = A.transpoz(), simetrik = A.kare() && A.esit(T_);
      const secili = sec ? A.g(sec[0], sec[1]) : null;
      const parcalar = [
        el("p", null, cip("A: " + A.m + "×" + A.n, "a"), metinDugum("  →  "), cip("Aᵀ: " + A.n + "×" + A.m, "b"),
          metinDugum(" Satır sayısı ile sütun sayısı **yer değiştirir**."))
      ];
      if (sec) {
        const [i, j] = sec;
        parcalar.push(el("p", null, metinDugum("Seçili: "), cip("a" + ind(i + 1) + ind(j + 1) + " = " + secili.toString(), "c"),
          metinDugum(i === j ? "  Ana köşegende olduğu için **yerinden oynamaz**." : "  Konum $(" + (i + 1) + "," + (j + 1) + ")\\to(" + (j + 1) + "," + (i + 1) + ")$: satır ve sütun numarası yer değiştirir.")));
      } else {
        parcalar.push(el("p", { class: "km-giris-ad" }, "Bir sayıya dokun: gideceği yer kesikli okla görünür."));
      }
      if (simetrik) parcalar.push(el("p", null, metinDugum("**Simetrik:** $A=A^T$. Ayna çizgisinin iki yanındaki sayılar eşit; kaydırınca hiçbir şey değişmez.")));
      koy(bilgi, parcalar);
    }

    function kur() {
      dur();
      N = Math.max(A.m, A.n);
      c = kisit(Math.floor(300 / N), 30, 50);
      const sv = sahne(N * c + 16, N * c + 28, "Transpoz aynası: sayılar ana köşegen etrafında yer değiştirir");
      bolgeA = svg("rect", { x: 8, y: 18, width: A.n * c, height: A.m * c, rx: 8, fill: "none", "stroke-width": 2, "stroke-dasharray": "6 4", style: { stroke: renk("a") } });
      bolgeT = svg("rect", { x: 8, y: 18, width: A.m * c, height: A.n * c, rx: 8, fill: "none", "stroke-width": 2, "stroke-dasharray": "6 4", style: { stroke: renk("b") } });
      sv.appendChild(bolgeA); sv.appendChild(bolgeT);
      sv.appendChild(svg("line", { x1: 4, y1: 14, x2: 12 + N * c, y2: 22 + N * c, "stroke-width": 2.5, style: { stroke: renk("vurgu") } }));
      sv.appendChild(yazi(8 + N * c - 4, 10, "ayna (ana köşegen)", { renk: "vurgu", boyut: 11, hiza: "sag", kalin: true }));
      ustKatman = svg("g", null);
      jetonlar = [];
      const kat = svg("g", null);
      for (let i = 0; i < A.m; i++) {
        for (let j = 0; j < A.n; j++) {
          const aile = SATIR_RENK[i % 3];
          const g = svg("g", {
            class: "km-chip", role: "button", tabindex: 0, "aria-label": "a" + (i + 1) + (j + 1) + " = " + A.g(i, j) + ": yerini göster",
            onclick: () => sec_(i, j),
            onkeydown: ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); sec_(i, j); } }
          },
          svg("rect", { x: 2, y: 2, width: c - 4, height: c - 4, rx: 7, "stroke-width": 1.8, style: { fill: zemin(aile), stroke: renk(aile) } }),
          yazi(c / 2, c / 2, A.g(i, j).toString(), { boyut: 14, kalin: true }));
          kat.appendChild(g);
          jetonlar.push({ g, i, j });
        }
      }
      sv.appendChild(kat); sv.appendChild(ustKatman);
      koy(sahneKutu, sv);
      const mtex = (M, f) => M.tex({ vurgu: f });
      koy(tPanel, blok("A=" + mtex(A, i => SATIR_MAKRO[i % 3]) + "\\;\\longrightarrow\\;A^{T}=" + mtex(A.transpoz(), (i, j) => SATIR_MAKRO[j % 3])),
        el("p", { class: "km-giris-ad" }, "Aynı renk = aynı sayılar: A'nın satırı Aᵀ'nin sütunu olur."));
      secimCiz(); yerlestir();
    }

    kok.appendChild(el("div", { class: "km-kap" }, sahneKutu, kay.kok, el("div", { class: "kx-satir" }, dCevir), bilgi, tPanel,
      el("details", null, el("summary", null, "Kendi matrisini dene"), giris.kok)));
    E.stilEkle("km-transpoz", ".km-chip.km-sec rect{stroke-width:3.2}");
    kur();
    return { yok_et() { dur(); } };
  }, {
    baslik: "Transpoz aynası",
    aciklama: "Ana köşegen bir ayna: sayılar $(i,j)$'den $(j,i)$'ye kayar. Kaydırıcıyla ara konumu gör; satırlar sütun olur.",
    varsayilan: { A: "1 2 3; 4 5 6" }
  });

  /* ================================================================ 5. kofaktor-acilim */

  E.kaydet("kofaktor-acilim", function (kok, p) {
    let A = Mat.al(p.A), cizgi = { tur: "satir", no: 0 }, s = 0, oyn = null;
    const sekilKutu = el("div", { class: "kx-sahne km-sahne" });
    const panel = el("div", { class: "km-panel", "aria-live": "polite" });
    const ipucu = el("p", { class: "km-giris-ad" });
    const sec = E.secici([
      { deger: "s0", etiket: "Satır 1" }, { deger: "s1", etiket: "Satır 2" }, { deger: "s2", etiket: "Satır 3" },
      { deger: "c0", etiket: "Sütun 1" }, { deger: "c1", etiket: "Sütun 2" }, { deger: "c2", etiket: "Sütun 3" }
    ], "s0", v => { cizgi = { tur: v[0] === "s" ? "satir" : "sutun", no: Number(v[1]) }; dur(); s = 0; ciz(); });
    const adim = adimDugmeleri({
      geri: () => { dur(); s = Math.max(0, s - 1); ciz(); },
      ileri: () => { dur(); s = Math.min(3, s + 1); ciz(); },
      bastan: () => { dur(); s = 0; ciz(); },
      oynat: () => oynat()
    });
    const giris = matrisGirisi("Kendi $3\\times3$ matrisini yaz", A, M => { A = M; dur(); s = 0; ciz(); }, {
      enM: 3, enN: 3, kontrol: M => (M.m === 3 && M.n === 3 ? null : "3×3 olmalı")
    });

    function dur() { if (oyn) { oyn.durdur(); oyn = null; } adim.oynatYaz(false); }

    function oynat() {
      if (oyn && oyn.calisiyor()) { dur(); return; }
      if (E.hareketAzalt()) { s = 3; ciz(); return; }
      if (s >= 3) s = 0;
      let bir = 1.2;
      oyn = E.animasyon(kok, (_, dt) => {
        bir += dt;
        if (bir < 1.2) return true;
        bir = 0;
        if (s < 3) { s++; ciz(); }
        if (s >= 3) { adim.oynatYaz(false); return false; }
        return true;
      });
      adim.oynatYaz(true);
    }

    const hucreSira = () => [0, 1, 2].map(k => (cizgi.tur === "satir" ? [cizgi.no, k] : [k, cizgi.no]));

    function ciz() {
      const sira = hucreSira(), aile = cizgi.tur === "satir" ? "a" : "b";
      const c = 42, MA = matrisCiz(A, { hucre: c, x: 0, y: 20 });
      const isaret = new Mat([[1, -1, 1], [-1, 1, -1], [1, -1, 1]]);
      const c2 = 26, xS = MA.genislik + 36;
      const MS = matrisCiz(isaret, { hucre: c2, x: xS, y: 20 + (3 * c - 3 * c2) / 2, bicim: x => (x.isaret() > 0 ? "+" : "−") });
      const sv = sahne(xS + MS.genislik + 4, 20 + 3 * c + 6, "Kofaktör açılımı");
      sira.forEach(([i, j]) => MA.boya(i, j, aile));
      const cur = s >= 1 ? sira[s - 1] : null;
      if (cur) {
        const [ci, cj] = cur;
        for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) if (i !== ci && j !== cj) MA.boya(i, j, "c");
        MS.boya(ci, cj, "c");
      }
      sv.append(MA.g, MS.g);
      sv.appendChild(yazi(MA.genislik / 2, 8, "A", { kalin: true, boyut: 14 }));
      sv.appendChild(yazi(xS + MS.genislik / 2, 8, "işaret satrancı", { renk: "soluk", boyut: 11 }));
      sv.appendChild(yazi(MA.genislik + 18, 20 + 1.5 * c, "→", { renk: "soluk", boyut: 18 }));
      if (cur) {
        const [ci, cj] = cur, h = MA.hucre(ci, cj), h0 = MA.hucre(0, 0), h2 = MA.hucre(2, 2);
        const kl = { "stroke-width": 3, "stroke-linecap": "round", style: { stroke: renk("sil") } };
        sv.appendChild(svg("line", Object.assign({ x1: h0.x + 2, y1: h.cy, x2: h2.x + c - 2, y2: h.cy }, kl)));
        sv.appendChild(svg("line", Object.assign({ x1: h.cx, y1: h0.y + 2, x2: h.cx, y2: h2.y + c - 2 }, kl)));
        MA.kutu(ci, cj, ci, cj, aile, { kalinlik: 3 });
        for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) if (i !== ci && j !== cj) MA.kutu(i, j, i, j, "c", { kalinlik: 1.8 });
      }
      koy(sekilKutu, sv);
      // sayısal panel
      const satirlar = [];
      const terimler = sira.map(([i, j]) => {
        const M = A.minor(i, j), d = M.det(), isr = (i + j) % 2 ? -1 : 1, a = A.g(i, j);
        const deger = a.carp(d).carp(isr);
        return { i, j, M, d, isr, a, deger };
      });
      let toplam = Kesir.SIFIR;
      const adlar = cizgi.tur === "satir" ? (cizgi.no + 1) + ". satırdan" : (cizgi.no + 1) + ". sütundan";
      satirlar.push(el("p", null, metinDugum("Açılım: **" + adlar + "**  "), cip("det A = Σ (−1)" + "ⁱ⁺ʲ · aᵢⱼ · Mᵢⱼ", "c")));
      for (let k = 0; k < s; k++) {
        const t = terimler[k];
        toplam = toplam.topla(t.deger);
        const mt = t.M.tex({ ortam: "vmatrix", vurgu: () => "kc" });
        const tx = "\\kb{" + (t.isr > 0 ? "+" : "-") + "}\\,\\ka{" + par(t.a) + "}\\cdot " + mt + "=" + T(t.deger);
        satirlar.push(blok(k === s - 1 ? "\\kutuc{" + tx + "}" : tx));
        if (k === s - 1) {
          satirlar.push(el("p", null, metinDugum(t.a.sifirMi()
            ? "Bu eleman $0$, terim kendiliğinden $0$. Minörü hesaplamaya bile gerek yok: **sıfırı çok olan satır/sütun** seç."
            : "İşaret: $(-1)^{" + (t.i + 1) + "+" + (t.j + 1) + "}=" + (t.isr > 0 ? "+1" : "-1") + "$. Kırmızı çizgi " + (t.i + 1) + ". satırı ve " + (t.j + 1) + ". sütunu siler; kalan $2\\times2$ **minör**: $M_{" + (t.i + 1) + (t.j + 1) + "}=" + T(t.d) + "$.")));
        }
      }
      if (s === 0) satirlar.push(el("p", null, metinDugum("**İleri**'ye bas: seçtiğin " + (cizgi.tur === "satir" ? "satırdaki" : "sütundaki") + " elemanlar sırayla ele alınır.")));
      if (s >= 3) {
        const parts = terimler.map(t => T(t.deger));
        satirlar.push(blok("\\det A=" + parts.map((x, k) => (k ? "+(" + x + ")" : x)).join("") + "=\\kutuc{\\kc{" + T(toplam) + "}}"));
        satirlar.push(el("p", null, metinDugum("Hangi satır ya da sütundan açarsan aç **aynı sonuç** çıkar: $\\det A=" + T(A.det()) + "$. Başka bir çizgi seçip dene.")));
      } else if (s > 0) {
        satirlar.push(el("p", null, cip("ara toplam = " + toplam.toString(), "c")));
      }
      koy(panel, satirlar);
      adim.guncelle(s, 3);
      // en çok sıfırlı çizgi
      let en = { n: -1, ad: "" };
      for (let k = 0; k < 3; k++) {
        const r = A.satir(k).filter(x => x.sifirMi()).length, q = A.sutun(k).filter(x => x.sifirMi()).length;
        if (r > en.n) en = { n: r, ad: (k + 1) + ". satır" };
        if (q > en.n) en = { n: q, ad: (k + 1) + ". sütun" };
      }
      ipucu.textContent = en.n > 0 ? "Kısa yol: en çok sıfır içeren çizgi " + en.ad + " (" + en.n + " sıfır). Sıfırlı terimler hiç hesaplanmaz." : "Bu matriste sıfır yok; her çizgi aynı işi çıkarır.";
    }

    kok.appendChild(el("div", { class: "km-kap" }, el("div", { class: "kx-satir" }, sec.kok), sekilKutu, adim.kok, panel, ipucu,
      el("details", null, el("summary", null, "Kendi matrisini dene"), giris.kok)));
    ciz();
    return { yok_et() { dur(); } };
  }, {
    baslik: "Kofaktör açılımı",
    aciklama: "Bir satır ya da sütun seç; her terimde satır ve sütun kırmızı çizilir, minör kutulanır, işaret satrancı gösterilir, toplam birikir.",
    varsayilan: { A: "2 0 1; 3 -1 4; 5 2 -2" }
  });

  /* ================================================================ 6. donusum-2b */

  let donSay = 0;
  const F_SEKLI = [[0.15, 0.1], [0.35, 0.1], [0.35, 0.45], [0.7, 0.45], [0.7, 0.6], [0.35, 0.6], [0.35, 0.8], [0.8, 0.8], [0.8, 0.95], [0.15, 0.95]];
  const f2 = v => String(Math.round(v * 100) / 100).replace("-0", "0");
  const aci = v => ((v % 360) + 360) % 360;

  /* Sürüklenebilir tutamak: büyük görünmez dokunma alanı + küçük görünür daire. */
  function tutamak(aile, etiket, yaz) {
    return svg("g", { class: "km-tutamak-g", role: "slider", "aria-label": etiket, "aria-valuetext": yaz || etiket, tabindex: 0 },
      svg("circle", { r: 18, fill: "transparent", stroke: "none", style: { pointerEvents: "all" } }),
      svg("circle", { r: 7, "stroke-width": 2.5, style: { fill: zemin(aile), stroke: renk(aile) } }));
  }

  E.kaydet("donusum-2b", function (kok, p) {
    const klipId = "km-don-" + (++donSay);
    let A = Mat.al(p.A);
    if (A.m !== 2 || A.n !== 2) A = new Mat([[1, 0], [0, 1]]);
    let P = [Kesir.al(2), Kesir.al(1)];
    const U = 36, O = 150, SINIR = 14; // SINIR: dörtte bir birim cinsinden (3,5 birim)
    const sx = x => O + x * U, sy = y => O - y * U;
    const kaldirlar = [];
    let oyn = null;
    const sv = sahne(300, 300, "Düzlemin dönüşümü: birim kare ve F harfi A matrisiyle dönüşür");
    sv.appendChild(svg("clipPath", { id: klipId }, svg("rect", { x: 0, y: 0, width: 300, height: 300 })));
    const cizgiS = { stroke: renk("cizgi") };

    // sabit ızgara ve eksenler
    const gSabit = svg("g", null);
    for (let k = -4; k <= 4; k++) {
      gSabit.appendChild(svg("line", { x1: sx(k), y1: 2, x2: sx(k), y2: 298, "stroke-width": k ? 0.8 : 1.6, style: { stroke: k ? renk("cizgi") : renk("soluk") } }));
      gSabit.appendChild(svg("line", { x1: 2, y1: sy(k), x2: 298, y2: sy(k), "stroke-width": k ? 0.8 : 1.6, style: { stroke: k ? renk("cizgi") : renk("soluk") } }));
    }
    sv.appendChild(gSabit);

    // dönüşmüş ızgara
    const gIz = svg("g", { "clip-path": "url(#" + klipId + ")" });
    const izler = [];
    for (let k = -6; k <= 6; k++) for (let f = 0; f < 2; f++) {
      const l = svg("line", { "stroke-width": 1, style: { stroke: renk("c"), opacity: 0.45 } });
      gIz.appendChild(l); izler.push({ l, k, f });
    }
    sv.appendChild(gIz);

    // birim kare ve F (özgün), dönüşmüş kare ve F
    sv.appendChild(svg("rect", { x: sx(0), y: sy(1), width: U, height: U, "stroke-width": 1.5, "stroke-dasharray": "5 4", fill: "none", style: { stroke: renk("soluk") } }));
    sv.appendChild(svg("polygon", { points: F_SEKLI.map(q => sx(q[0]) + "," + sy(q[1])).join(" "), "stroke-width": 1.2, style: { fill: zemin("cizgi"), stroke: renk("soluk") } }));
    const kareT = svg("polygon", { "stroke-width": 2, "stroke-linejoin": "round", style: { fill: zemin("c"), stroke: renk("c") } });
    const fT = svg("polygon", { "stroke-width": 1.5, "stroke-linejoin": "round", style: { fill: renk("c"), stroke: renk("c"), opacity: 0.8 } });
    const okG = svg("g", null);
    const etG = svg("g", null);
    sv.append(kareT, fT, okG, etG);

    const h1 = tutamak("a", "A'nın 1. sütununun ucu (e₁ nereye gidiyor)");
    const h2 = tutamak("b", "A'nın 2. sütununun ucu (e₂ nereye gidiyor)");
    const hp = tutamak("c", "Deneme noktası p");
    sv.append(h1, h2, hp);
    const sahneKutu = el("div", { class: "kx-sahne km-sahne" }, sv);
    const panel = el("div", { class: "km-panel", "aria-live": "polite" });
    const ayarRenk = (g, nokta) => g.setAttribute("transform", "translate(" + nokta[0].toFixed(1) + " " + nokta[1].toFixed(1) + ")");

    // m: { a, b, c, d } sayısal; çizimi günceller
    function cizim(m) {
      const c1 = [m.a, m.c], c2 = [m.b, m.d];
      izler.forEach(z => {
        const ana = z.f ? c2 : c1, yan = z.f ? c1 : c2;
        z.l.setAttribute("x1", sx(z.k * ana[0] - 8 * yan[0])); z.l.setAttribute("y1", sy(z.k * ana[1] - 8 * yan[1]));
        z.l.setAttribute("x2", sx(z.k * ana[0] + 8 * yan[0])); z.l.setAttribute("y2", sy(z.k * ana[1] + 8 * yan[1]));
      });
      const T_ = (x, y) => [sx(m.a * x + m.b * y), sy(m.c * x + m.d * y)];
      kareT.setAttribute("points", [T_(0, 0), T_(1, 0), T_(1, 1), T_(0, 1)].map(q => q[0].toFixed(1) + "," + q[1].toFixed(1)).join(" "));
      fT.setAttribute("points", F_SEKLI.map(q => T_(q[0], q[1])).map(q => q[0].toFixed(1) + "," + q[1].toFixed(1)).join(" "));
      ayarRenk(h1, [sx(m.a), sy(m.c)]); ayarRenk(h2, [sx(m.b), sy(m.d)]);
      const px = P[0].sayi(), py = P[1].sayi();
      ayarRenk(hp, [sx(px), sy(py)]);
      bosalt(okG); bosalt(etG);
      const uz = (x1, y1, x2, y2) => Math.hypot(x2 - x1, y2 - y1) > 6;
      // p = x·e1' + y·e2' : ucu uca eklenen iki ok
      const q1 = [sx(m.a * px), sy(m.c * px)], q2 = T_(px, py);
      if (uz(O, O, q1[0], q1[1])) okG.appendChild(ok(O, O, q1[0], q1[1], { renk: "a", kalinlik: 2, kesik: true, bas: 6 }));
      if (uz(q1[0], q1[1], q2[0], q2[1])) okG.appendChild(ok(q1[0], q1[1], q2[0], q2[1], { renk: "b", kalinlik: 2, kesik: true, bas: 6 }));
      if (uz(O, O, sx(m.a), sy(m.c))) okG.appendChild(ok(O, O, sx(m.a), sy(m.c) , { renk: "a", kalinlik: 3.2, bas: 9 }));
      if (uz(O, O, sx(m.b), sy(m.d))) okG.appendChild(ok(O, O, sx(m.b), sy(m.d), { renk: "b", kalinlik: 3.2, bas: 9 }));
      okG.appendChild(svg("circle", { cx: q2[0], cy: q2[1], r: 4.5, style: { fill: renk("c") } }));
      etG.appendChild(yazi(sx(m.a) + (m.a >= 0 ? 10 : -10), sy(m.c) - 12, "e₁′", { renk: "a", kalin: true, boyut: 13, hiza: m.a >= 0 ? "sol" : "sag" }));
      etG.appendChild(yazi(sx(m.b) + (m.b >= 0 ? 10 : -10), sy(m.d) - 12, "e₂′", { renk: "b", kalin: true, boyut: 13, hiza: m.b >= 0 ? "sol" : "sag" }));
      etG.appendChild(yazi(sx(px) + 10, sy(py) + 16, "p", { renk: "c", kalin: true, boyut: 13, hiza: "sol" }));
      etG.appendChild(yazi(q2[0] + 8, q2[1] - 9, "Ap", { renk: "c", kalin: true, boyut: 13, hiza: "sol" }));
    }

    const sayisal = () => ({ a: A.g(0, 0).sayi(), b: A.g(0, 1).sayi(), c: A.g(1, 0).sayi(), d: A.g(1, 1).sayi() });

    function bilgiYaz() {
      const a = A.g(0, 0), b = A.g(0, 1), c = A.g(1, 0), d = A.g(1, 1), x = P[0], y = P[1];
      const det = a.carp(d).cikar(b.carp(c));
      const sutunTex = (u, v, mk) => new Mat([[u], [v]]).tex({ vurgu: () => mk });
      const sonuc = new Mat([[a.carp(x).topla(b.carp(y))], [c.carp(x).topla(d.carp(y))]]);
      const durum = det.sifirMi()
        ? cip("det = 0", "sil") : cip("det = " + det.toString(), det.isaret() < 0 ? "b" : "c");
      const yorum = det.sifirMi()
        ? "Düzlem bir doğruya (ya da noktaya) çöktü: alan $0$. Bilgi kaybolduğu için $A$'nın **tersi yok**."
        : "Birim karenin alanı $1$ iken paralelkenarın alanı $|\\det A|=" + det.mutlak().tex() + "$." +
          (det.isaret() < 0 ? " Determinant negatif: şekil **ters yüzü döndü** (F harfi aynalandı)." : " Determinant pozitif: yön korundu.");
      koy(panel,
        blok("A=" + A.tex({ vurgu: (i, j) => (j ? "kb" : "ka") }) + "\\quad A\\mathbf{e}_1=" + sutunTex(a, c, "ka") + ",\\; A\\mathbf{e}_2=" + sutunTex(b, d, "kb")),
        el("p", null, durum, metinDugum("  " + yorum)),
        blok("A\\mathbf{p}=\\ka{" + par(x) + "}" + sutunTex(a, c, "ka") + "+\\kb{" + par(y) + "}" + sutunTex(b, d, "kb") + "=" + sonuc.tex({ vurgu: () => "kc" })),
        el("p", { class: "km-giris-ad" }, "Mavi ve turuncu uçları (e₁′, e₂′) ya da yeşil p noktasını sürükle. Klavyede ok tuşları da çalışır."));
    }

    function uygula(yeni, sessiz) {
      A = yeni;
      cizim(sayisal());
      bilgiYaz();
      if (!sessiz) giris.ayarla(A);
    }

    function dur() { if (oyn) { oyn.durdur(); oyn = null; } }

    function gec(hedef) {
      dur();
      const bas = sayisal(), son = { a: hedef.g(0, 0).sayi(), b: hedef.g(0, 1).sayi(), c: hedef.g(1, 0).sayi(), d: hedef.g(1, 1).sayi() };
      if (E.hareketAzalt()) { uygula(hedef); return; }
      let t = 0;
      oyn = E.animasyon(kok, (_, dt) => {
        t = Math.min(1, t + dt / 0.7);
        const e = t * t * (3 - 2 * t);
        cizim({ a: bas.a + (son.a - bas.a) * e, b: bas.b + (son.b - bas.b) * e, c: bas.c + (son.c - bas.c) * e, d: bas.d + (son.d - bas.d) * e });
        if (t >= 1) { uygula(hedef); return false; }
        return true;
      });
    }

    const dortte = x => new Kesir(Math.round(kisit(x, -SINIR / 4, SINIR / 4) * 4), 4);
    const dunya = pt => [(pt.x - O) / U, (O - pt.y) / U];
    function sutunTasi(j) {
      return pt => {
        dur();
        const [x, y] = dunya(pt), r = A.v.map(s => s.slice());
        r[0][j] = dortte(x); r[1][j] = dortte(y);
        uygula(new Mat(r));
      };
    }
    function sutunKlavye(j) {
      return (dx, dy) => {
        dur();
        const r = A.v.map(s => s.slice());
        r[0][j] = dortte(r[0][j].sayi() + dx * 0.25); r[1][j] = dortte(r[1][j].sayi() - dy * 0.25);
        uygula(new Mat(r));
      };
    }
    kaldirlar.push(E.surukle(h1, { svg: sv, tasi: sutunTasi(0), klavye: sutunKlavye(0) }));
    kaldirlar.push(E.surukle(h2, { svg: sv, tasi: sutunTasi(1), klavye: sutunKlavye(1) }));
    kaldirlar.push(E.surukle(hp, {
      svg: sv,
      tasi: pt => { const [x, y] = dunya(pt); P = [dortte(x), dortte(y)]; cizim(sayisal()); bilgiYaz(); },
      klavye: (dx, dy) => { P = [dortte(P[0].sayi() + dx * 0.25), dortte(P[1].sayi() - dy * 0.25)]; cizim(sayisal()); bilgiYaz(); }
    }));

    const giris = matrisGirisi("Matrisi elle yaz", A, M => { dur(); uygula(M, true); }, {
      enM: 2, enN: 2, kontrol: M => (M.m === 2 && M.n === 2 ? null : "2×2 olmalı")
    });
    const hazir = [
      ["Birim", "1 0; 0 1"], ["Döndür 90°", "0 -1; 1 0"], ["Ölçekle", "2 0; 0 1"],
      ["Kaydır", "1 1; 0 1"], ["Yansıt", "1 0; 0 -1"], ["Ez (tekil)", "1 2; 1/2 1"]
    ];
    const hazirSatir = el("div", { class: "kx-satir" }, hazir.map(h => E.dugme(h[0], () => gec(Mat.oku(h[1])))));

    kok.appendChild(el("div", { class: "km-kap" }, sahneKutu, hazirSatir, panel,
      el("details", null, el("summary", null, "Matrisi sayı yazarak değiştir"), giris.kok)));
    uygula(A, true);
    return { yok_et() { dur(); kaldirlar.forEach(k => k()); } };
  }, {
    baslik: "2B dönüşüm",
    aciklama: "$A$'nın sütunları $\\mathbf{e}_1$ ve $\\mathbf{e}_2$'nin gittiği yerdir. Uçları sürükle; birim kare ve F harfi nasıl bükülüyor, alan ve yön nasıl değişiyor gör.",
    varsayilan: { A: "2 1; 0 1" }
  });

  /* ================================================================ 7. gauss-adim */

  E.kaydet("gauss-adim", function (kok, p) {
    let mod = p.mod === "ters" ? "ters" : "coz";
    let A = Mat.al(p.A);
    if (!A.kare()) A = new Mat([[2, 1], [1, 3]]);
    let b = p.b !== undefined && p.b !== null && p.b !== "" ? Mat.al(p.b) : null;
    if (!b || b.m !== A.m || b.n !== 1) b = new Mat(A.v.map((_, i) => [i + 1]));
    let G = null, N = 0, s = 0, oyn = null, kay = null;
    const sekilKutu = el("div", { class: "kx-sahne km-sahne" });
    const panel = el("div", { class: "km-panel", "aria-live": "polite" });
    const kayKap = el("div");
    const adim = adimDugmeleri({
      geri: () => git(s - 1), ileri: () => git(s + 1), bastan: () => git(0), oynat: () => oynat()
    });
    const modSec = E.secici([{ deger: "coz", etiket: "Sistemi çöz" }, { deger: "ters", etiket: "Tersi bul" }], mod, v => { mod = v; dur(); s = 0; hesapla(); girisGoster(); });
    const girA = matrisGirisi("Katsayı matrisi $A$ (kare)", A, M => { A = M; if (b.m !== A.m) b = new Mat(A.v.map((_, i) => [i + 1])); girB.ayarla(b); dur(); s = 0; hesapla(); }, {
      enM: 4, enN: 4, kontrol: M => (M.m === M.n ? null : "Kare olmalı (satır = sütun)")
    });
    const girB = matrisGirisi("Sağ taraf $b$ (sütun)", b, M => { b = M; dur(); s = 0; hesapla(); }, {
      enM: 4, enN: 1, kontrol: M => (M.m === A.m && M.n === 1 ? null : "Tam " + A.m + " sayı yaz (sütun)")
    });
    function girisGoster() { girB.kok.hidden = mod === "ters"; }

    function dur() { if (oyn) { oyn.durdur(); oyn = null; } adim.oynatYaz(false); }

    function oynat() {
      if (oyn && oyn.calisiyor()) { dur(); return; }
      if (E.hareketAzalt()) { git(N); return; }
      if (s >= N) s = 0;
      let bek = 1.3;
      oyn = E.animasyon(kok, (_, dt) => {
        bek += dt;
        if (bek < 1.3) return true;
        bek = 0;
        if (s < N) git(s + 1, true);
        if (s >= N) { adim.oynatYaz(false); return false; }
        return true;
      });
      adim.oynatYaz(true);
    }

    function git(k, sessiz) {
      if (!sessiz) dur();
      s = kisit(k, 0, N);
      kay.ayarla(s, true);
      ciz();
    }

    function hesapla() {
      G = gaussAdimlari(A, mod === "ters" ? Mat.birim(A.m) : b);
      N = G.islemler.length;
      s = Math.min(s, N);
      kay = E.kaydirici({
        etiket: "Adım", min: 0, max: Math.max(1, N), adim: 1, deger: s,
        bicim: v => v + " / " + N, degisince: v => { dur(); s = Math.round(v); ciz(); }
      });
      koy(kayKap, kay.kok);
      ciz();
    }

    function ciz() {
      const durum = G.durumlar[Math.min(s, G.durumlar.length - 1)];
      const op = s > 0 ? G.islemler[s - 1] : null;
      const sn = s < N ? G.islemler[s] : null;
      const bitti = s === N && !G.tekil;
      const sc = gaussCiz(durum, A.n, { islem: op, sonraki: sn && sn.tur !== "tekil" ? sn : null, bitti, enGenis: 340 });
      koy(sekilKutu, sc.dugum);
      const parca = [];
      parca.push(el("p", null, cip("Adım " + s + " / " + N, "a"), metinDugum("  "),
        op ? cip(islemKisa(op), op.tur === "tekil" ? "sil" : "b") : cip("başlangıç: [A | " + (mod === "ters" ? "I" : "b") + "]", "a")));
      if (op) {
        if (op.tur !== "tekil") parca.push(blok(islemTex(op)));
        parca.push(para(islemAciklama(op)));
      } else {
        parca.push(para("**Amaç:** sol yarıyı birim matris $I$ yapmak. Her sütunda önce **pivot** seçilir (mavi satır, yeşil kutu), sonra o sütunun diğer elemanları sıfırlanır."));
      }
      if (sn && sn.tur !== "tekil") parca.push(el("p", { class: "km-giris-ad" }, "Sıradaki: " + islemKisa(sn) + (sn.tur === "cikar" ? " (kırmızı hücre sıfırlanacak)" : "")));
      if (G.tekil && s === N) {
        parca.push(el("p", { class: "kx-geri uyari" }, mod === "ters"
          ? "Pivot kalmadı: $A$ tekil, tersi yok."
          : "Pivot kalmadı: $\\det A=0$. Sistemin ya çözümü yoktur ya da sonsuz çözümü vardır."));
      } else if (bitti) {
        const sag = new Mat(durum.map(r => r.slice(A.n)));
        if (mod === "ters") {
          parca.push(blok("A^{-1}=" + sag.tex({ vurgu: () => "kutuc" })));
          parca.push(para("Sol yarı $I$ oldu; sağ yarıda **$A^{-1}$** kaldı. Kontrol: $A\\,A^{-1}=I$."));
        } else {
          parca.push(blok("\\mathbf{x}=" + sag.tex({ vurgu: () => "kutuc" })));
          parca.push(el("p", null, durum.map((r, i) => [cip("x" + ind(i + 1) + " = " + r[A.n].toString(), "c"), metinDugum(" ")]).reduce((a, q) => a.concat(q), [])));
        }
      }
      koy(panel, parca);
      adim.guncelle(s, N);
    }

    kok.appendChild(el("div", { class: "km-kap" }, modSec.kok, sekilKutu, kayKap, adim.kok, panel,
      el("details", null, el("summary", null, "Kendi sistemini dene"), el("div", { class: "km-girisler" }, girA.kok, girB.kok))));
    girisGoster();
    hesapla();
    return { yok_et() { dur(); } };
  }, {
    baslik: "Gauss–Jordan adım adım",
    aciklama: "Pivotu seç, bölerek 1 yap, altındaki ve üstündeki elemanları sıfırla. Sistemi çözer ya da $[A\\,|\\,I]$ üzerinden tersi bulur; kesirler tam gösterilir.",
    varsayilan: { A: "2 1 -1; -3 -1 2; -2 1 2", b: "8; -11; -3", mod: "coz" }
  });

  /* ================================================================ 8. ozvektor-2b */

  function tamKok(k) {
    if (k.isaret() < 0) return null;
    const ks = n => {
      if (n < 2n) return n;
      let x = BigInt(Math.floor(Math.sqrt(Number(n))));
      while (x * x > n) x--;
      while ((x + 1n) * (x + 1n) <= n) x++;
      return x;
    };
    const a = ks(k.pay), b = ks(k.payda);
    return a * a === k.pay && b * b === k.payda ? new Kesir(a, b) : null;
  }

  /* 2×2 özdeğerler: [{ l: sayı, tam: Kesir | null, aci: [derece, derece+180] }] */
  function ozler2(A) {
    const a = A.g(0, 0), b = A.g(0, 1), c = A.g(1, 0), d = A.g(1, 1);
    const iz = a.topla(d), det = a.carp(d).cikar(b.carp(c));
    const disc = iz.carp(iz).bol(4).cikar(det);
    if (disc.isaret() < 0) return { iz, det, disc, liste: [] };
    const kk = tamKok(disc), yar = iz.bol(2);
    const ls = kk
      ? (kk.sifirMi() ? [{ l: yar.sayi(), tam: yar }] : [{ l: yar.topla(kk).sayi(), tam: yar.topla(kk) }, { l: yar.cikar(kk).sayi(), tam: yar.cikar(kk) }])
      : [{ l: yar.sayi() + Math.sqrt(disc.sayi()), tam: null }, { l: yar.sayi() - Math.sqrt(disc.sayi()), tam: null }];
    const an = a.sayi(), bn = b.sayi(), cn = c.sayi(), dn = d.sayi();
    const liste = ls.map(o => {
      let v;
      if (Math.abs(bn) > 1e-12) v = [bn, o.l - an];
      else if (Math.abs(cn) > 1e-12) v = [o.l - dn, cn];
      else v = Math.abs(o.l - an) < 1e-12 ? [1, 0] : [0, 1];
      const g = aci(Math.atan2(v[1], v[0]) * 180 / Math.PI);
      return { l: o.l, tam: o.tam, aci: [g, aci(g + 180)] };
    });
    // iki özdeğer farklı ve köşegen değilse aynı yönler çakışmasın; köşegen + eşit → her yön özvektör
    return { iz, det, disc, liste, hepsi: bn === 0 && cn === 0 && an === dn };
  }

  E.kaydet("ozvektor-2b", function (kok, p) {
    let A = Mat.al(p.A);
    if (A.m !== 2 || A.n !== 2) A = new Mat([[2, 1], [1, 2]]);
    let th = 20, ozler = ozler2(A), goster = false, oyn = null, gidis = null;
    const O = 150;
    const kaldirlar = [];
    const sv = sahne(300, 300, "Birim vektör x döner; Ax çizilir. Aynı doğrultuya gelince özvektör bulunur");
    const sahneKutu = el("div", { class: "kx-sahne km-sahne" }, sv);
    const panel = el("div", { class: "km-panel", "aria-live": "polite" });
    const olcer = el("div", { class: "km-olcer", role: "img", "aria-label": "x ile Ax ne kadar paralel" }, el("i"));
    const gDin = svg("g", null);
    const hx = tutamak("a", "x vektörünün ucu: açıyı değiştir");
    const bilgiSatir = el("p", { class: "km-giris-ad" });

    const kay = E.kaydirici({
      etiket: "x vektörünün açısı", min: 0, max: 359, adim: 1, deger: th, birim: "°",
      degisince: v => { durGidis(); th = v; ciz(); }
    });
    const dOzdog = E.dugme("Özvektöre git", () => ozGit(), { ana: true });
    const dGoster = E.dugme("Özdoğruları göster", () => { goster = !goster; dGoster.textContent = goster ? "Özdoğruları gizle" : "Özdoğruları göster"; ciz(); });
    const dOynat = E.dugme("Oynat", () => oynat());
    const giris = matrisGirisi("Matrisi elle yaz ($2\\times2$)", A, M => { A = M; ozler = ozler2(A); durGidis(); ciz(); }, {
      enM: 2, enN: 2, kontrol: M => (M.m === 2 && M.n === 2 ? null : "2×2 olmalı")
    });

    function durGidis() {
      if (gidis) { gidis.durdur(); gidis = null; }
      if (oyn) { oyn.durdur(); oyn = null; dOynat.textContent = "Oynat"; }
    }

    function oynat() {
      if (oyn) { durGidis(); return; }
      if (E.hareketAzalt()) { ozGit(); return; }
      oyn = E.animasyon(kok, (_, dt) => {
        th = aci(th + dt * 24);
        kay.ayarla(Math.round(th) % 360, true);
        ciz();
        return true;
      });
      dOynat.textContent = "Durdur";
    }

    function ozGit() {
      durGidis();
      if (!ozler.liste.length) { bilgiSatir.textContent = "Bu matrisin gerçek özvektörü yok: her vektör dönüyor."; return; }
      const hedefler = [];
      ozler.liste.forEach(o => o.aci.forEach(g => hedefler.push(g)));
      // bulunduğun yerden en yakın değil, sıradaki özyön
      hedefler.sort((u, v) => aci(u - th - 0.5) - aci(v - th - 0.5));
      const hedef = hedefler[0];
      if (E.hareketAzalt()) { th = hedef; kay.ayarla(Math.round(th) % 360, true); ciz(); return; }
      const bas = th, fark = ((hedef - bas + 540) % 360) - 180;
      let t = 0;
      gidis = E.animasyon(kok, (_, dt) => {
        t = Math.min(1, t + dt / 1.2);
        th = aci(bas + fark * (t * t * (3 - 2 * t)));
        kay.ayarla(Math.round(th) % 360, true);
        ciz();
        if (t >= 1) { gidis = null; return false; }
        return true;
      });
    }

    const an = () => ({ a: A.g(0, 0).sayi(), b: A.g(0, 1).sayi(), c: A.g(1, 0).sayi(), d: A.g(1, 1).sayi() });

    function ciz() {
      const m = an(), nA = Math.sqrt(m.a * m.a + m.b * m.b + m.c * m.c + m.d * m.d);
      const u = kisit(125 / Math.max(nA, 1.6), 20, 70);
      const rad = th * Math.PI / 180, x = [Math.cos(rad), Math.sin(rad)];
      const Ax = [m.a * x[0] + m.b * x[1], m.c * x[0] + m.d * x[1]];
      const nAx = Math.hypot(Ax[0], Ax[1]);
      const cross = x[0] * Ax[1] - x[1] * Ax[0], dot = x[0] * Ax[0] + x[1] * Ax[1];
      const hizali = nAx < 1e-9 || Math.abs(cross) <= 0.03 * nAx;
      const P = (v, k) => [O + v[0] * (k === undefined ? u : k), O - v[1] * (k === undefined ? u : k)];
      bosalt(gDin);
      // eksenler
      gDin.appendChild(svg("line", { x1: 4, y1: O, x2: 296, y2: O, "stroke-width": 1.2, style: { stroke: renk("cizgi") } }));
      gDin.appendChild(svg("line", { x1: O, y1: 4, x2: O, y2: 296, "stroke-width": 1.2, style: { stroke: renk("cizgi") } }));
      // birim çember ve imgesi (elips)
      gDin.appendChild(svg("circle", { cx: O, cy: O, r: u, fill: "none", "stroke-width": 1.2, "stroke-dasharray": "4 4", style: { stroke: renk("soluk") } }));
      const nok = [];
      for (let k = 0; k <= 72; k++) {
        const r = k / 72 * 2 * Math.PI, c = Math.cos(r), s = Math.sin(r);
        const q = P([m.a * c + m.b * s, m.c * c + m.d * s]);
        nok.push(q[0].toFixed(1) + "," + q[1].toFixed(1));
      }
      gDin.appendChild(svg("polyline", { points: nok.join(" "), fill: "none", "stroke-width": 1.4, style: { stroke: renk("b"), opacity: 0.55 } }));
      // x'in doğrusu
      const d1 = P(x, 145), d2 = P(x, -145);
      gDin.appendChild(svg("line", { x1: d1[0], y1: d1[1], x2: d2[0], y2: d2[1], "stroke-width": 1.2, "stroke-dasharray": "6 5", style: { stroke: hizali ? renk("c") : renk("soluk") } }));
      if (goster) ozler.liste.forEach(o => {
        const e1 = P([Math.cos(o.aci[0] * Math.PI / 180), Math.sin(o.aci[0] * Math.PI / 180)], 148), e2 = P([Math.cos(o.aci[0] * Math.PI / 180), Math.sin(o.aci[0] * Math.PI / 180)], -148);
        gDin.appendChild(svg("line", { x1: e1[0], y1: e1[1], x2: e2[0], y2: e2[1], "stroke-width": 2.5, "stroke-dasharray": "2 6", "stroke-linecap": "round", style: { stroke: renk("c") } }));
      });
      // Ax ve x okları
      const tAx = P(Ax);
      if (nAx * u > 6) gDin.appendChild(ok(O, O, tAx[0], tAx[1], { renk: hizali ? "c" : "b", kalinlik: 3.4, bas: 10 }));
      const tx = P(x);
      gDin.appendChild(ok(O, O, tx[0], tx[1], { renk: hizali ? "c" : "a", kalinlik: 3.4, bas: 10 }));
      gDin.appendChild(yazi(tAx[0] + (Ax[0] >= 0 ? 9 : -9), tAx[1] - 10, "Ax", { renk: hizali ? "c" : "b", kalin: true, boyut: 14, hiza: Ax[0] >= 0 ? "sol" : "sag" }));
      gDin.appendChild(yazi(tx[0] + (x[0] >= 0 ? 9 : -9), tx[1] + 16, "x", { renk: hizali ? "c" : "a", kalin: true, boyut: 14, hiza: x[0] >= 0 ? "sol" : "sag" }));
      hx.setAttribute("transform", "translate(" + tx[0].toFixed(1) + " " + tx[1].toFixed(1) + ")");
      hx.setAttribute("aria-valuetext", Math.round(th) + " derece");
      // ölçer
      const paralel = nAx < 1e-9 ? 1 : 1 - Math.abs(cross) / nAx;
      olcer.firstChild.style.width = Math.round(paralel * 100) + "%";
      olcer.classList.toggle("yesil", hizali);
      // panel
      const parca = [];
      parca.push(el("p", null, cip("x = (" + f2(x[0]) + " ; " + f2(x[1]) + ")", "a"), metinDugum("  "), cip("Ax = (" + f2(Ax[0]) + " ; " + f2(Ax[1]) + ")", "b")));
      if (hizali) {
        const lam = nAx < 1e-9 ? 0 : dot;
        const eslesen = ozler.liste.find(o => Math.abs(o.l - lam) < 0.06);
        const lamMetin = eslesen && eslesen.tam ? eslesen.tam.toString() : f2(lam);
        parca.push(el("p", { class: "kx-geri dogru" }, "Özvektör bulundu: Ax, x ile aynı doğrultuda. Ax = λx, λ = " + lamMetin + (Math.abs(lam) < 1e-9 ? " (x sıfıra çöktü)" : (lam < 0 ? " (negatif: ters yöne)" : ""))));
      } else {
        parca.push(el("p", null, metinDugum("**Ax** hâlâ **x**'e paralel değil. Çubuk ne kadar dolarsa o kadar yaklaştın.")));
      }
      parca.push(el("p", { class: "km-giris-ad" }, "Paralellik:"), olcer);
      const iz = ozler.iz, det = ozler.det;
      let kar = "\\lambda^2-(" + iz.tex() + ")\\lambda+(" + det.tex() + ")=0";
      if (ozler.liste.length) {
        kar += ozler.liste.length === 2 && ozler.liste[0].tam
          ? "\\;\\Rightarrow\\;\\lambda_1=\\ka{" + ozler.liste[0].tam.tex() + "},\\;\\lambda_2=\\kb{" + ozler.liste[1].tam.tex() + "}"
          : "\\;\\Rightarrow\\;\\lambda\\approx " + ozler.liste.map(o => f2(o.l)).join(",\\;");
      } else kar += "\\;\\Rightarrow\\;\\text{gerçek kök yok (her vektör döner)}";
      parca.push(blok(kar));
      if (bilgiSatir.textContent) parca.push(bilgiSatir);
      koy(panel, parca);
    }

    kaldirlar.push(E.surukle(hx, {
      svg: sv,
      tasi: pt => {
        durGidis();
        th = aci(Math.atan2(O - pt.y, pt.x - O) * 180 / Math.PI);
        kay.ayarla(Math.round(th) % 360, true);
        bilgiSatir.textContent = "";
        ciz();
      },
      klavye: (dx) => { durGidis(); th = aci(th + dx * -1); kay.ayarla(Math.round(th) % 360, true); ciz(); }
    }));
    sv.append(gDin, hx);
    kok.appendChild(el("div", { class: "km-kap" }, sahneKutu, kay.kok, el("div", { class: "kx-satir" }, dOzdog, dOynat, dGoster), panel,
      el("details", null, el("summary", null, "Kendi matrisini dene"), giris.kok)));
    ciz();
    return { yok_et() { durGidis(); kaldirlar.forEach(k => k()); } };
  }, {
    baslik: "Özvektör avı",
    aciklama: "Birim vektör $\\mathbf{x}$'i döndür; $A\\mathbf{x}$ onunla aynı doğrultuya gelince $\\mathbf{x}$ bir özvektör, uzama oranı $\\lambda$ olur.",
    varsayilan: { A: "2 1; 1 2" }
  });

  /* ================================================================ ALIŞTIRMALAR: ortak parçalar */

  E.stilEkle("etkilesim-matris-alistirma", [
    ".km-hesap{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,175px),1fr));gap:2px 12px}",
    ".km-hesap>*{min-width:0;overflow-x:auto;padding:2px 0}",
    ".km-hesap .katex-display{margin:0}"
  ].join("\n"));

  const zor = p => kisit(Math.round(Number((p || {}).zorluk) || 1), 1, 3);
  const boyP = (p, vars) => { const b = Math.round(Number((p || {}).boyut)); return b >= 1 && b <= 4 ? b : vars; };
  /* Kütüphane adımları zaten numaralı liste olarak gösterir; metindeki "**1.**" önekini atarız. */
  const adimTemizle = a => {
    if (typeof a === "string") return a.replace(/^\*\*\d+\.\*\*\s*/, "").replace(/^\*\*\d+\.\s*/, "**");
    if (!a || typeof a.metin !== "string") return a;
    return Object.assign({}, a, { metin: adimTemizle(a.metin) });
  };
  const ak = uret => (kok, p) => E.alistirmaKur(kok, p, (rnd, pp) => {
    const s = uret(rnd, pp);
    if (s && Array.isArray(s.adimlar)) s.adimlar = s.adimlar.map(adimTemizle);
    return s;
  });
  const hesapKutusu = liste => el("div", { class: "km-hesap" }, liste.map(s => texDugum(s, false)));
  const cozum = (...c) => el("div", { class: "km-cozum" }, c);
  const sahneDiv = d => el("div", { class: "kx-sahne km-sahne" }, d);
  const kk = (a, b) => new Kesir(a, b === undefined ? 1 : b);

  /* Yalın matris resmi (isteğe bağlı adıyla). */
  function duzMatris(A, ad, hucre) {
    const c = hucre || 38, ML = ad ? 28 : 2;
    const M = matrisCiz(A, { x: ML, y: 4, hucre: c });
    const s = sahne(ML + M.genislik + 4, M.yukseklik + 8, "Matris " + (ad || ""));
    s.appendChild(M.g);
    if (ad) s.appendChild(yazi(ML - 4, 4 + M.yukseklik / 2, ad + " =", { kalin: true, boyut: 14, hiza: "sag" }));
    return s;
  }

  /* ikili işlem şekli: A (+|−) B = C ya da kA = C; i0,j0 hücresi vurgulu ve oklu. */
  function elemanSekli(A, B, C, isaret, k) {
    const i0 = Math.min(A.m - 1, 0), j0 = 0;
    const ilk = k !== undefined
      ? [{ yaz: k.toString(), gen: 14 + 8 * k.toString().length, renk: "b", boyut: 18 }, { M: A, ad: "A", boya: [[i0, j0, "a"]] }]
      : [{ M: A, ad: "A", boya: [[i0, j0, "a"]] }, { yaz: isaret, boyut: 22 }, { M: B, ad: "B", boya: [[i0, j0, "b"]] }];
    const parcalar = ilk.concat([{ yaz: "=", boyut: 22 }, { M: C, ad: "C", boya: [[i0, j0, "c"]] }]);
    const son = parcalar.length - 1, ai = k !== undefined ? 1 : 0, bi = 2;
    const oklar = [{ kimden: [ai, i0, j0], kime: [son, i0, j0], renk: "a", egri: -0.35 }];
    if (k === undefined) oklar.push({ kimden: [bi, i0, j0], kime: [son, i0, j0], renk: "b", egri: 0.35 });
    return denklemSekli(parcalar, { enGenis: 340, oklar, etiket: "İşlem şeması" });
  }

  /* Gauss–Jordan'ın tüm adımlarını {metin, tex, sekil} olarak verir. */
  function gaussAdimListesi(A, R, nA, enGenis) {
    const G = gaussAdimlari(A, R), liste = [];
    G.islemler.forEach((op, k) => {
      const durum = G.durumlar[Math.min(k + 1, G.durumlar.length - 1)];
      const sn = k + 1 < G.islemler.length ? G.islemler[k + 1] : null;
      const son = k === G.islemler.length - 1 && !G.tekil;
      liste.push({
        metin: "**" + islemKisa(op) + ":** " + islemAciklama(op),
        tex: op.tur === "tekil" ? "" : islemTex(op),
        sekil: gaussCiz(durum, nA, { islem: op, sonraki: sn && sn.tur !== "tekil" ? sn : null, bitti: son, enGenis: enGenis || 330 }).dugum
      });
    });
    return { G, liste };
  }

  /* ================================================================ 1. alistirma:boyut */

  E.kaydet("alistirma:boyut", ak(function (rnd, p) {
    const z = zor(p);
    const m = rnd.tam(2, z === 1 ? 3 : 4);
    let n = rnd.tam(2, z === 1 ? 4 : 5);
    if (n === m) n++;
    const A = Mat.rastgele(rnd, m, n, -5, 9);
    const i = rnd.tam(0, m - 1), j = rnd.tam(0, n - 1);
    const aij = "$a_{" + (i + 1) + (j + 1) + "}$";
    let alanlar = ["$m$ (satır sayısı)", "$n$ (sütun sayısı)"];
    let cevap = [m, n];
    let metin = "Aşağıdaki matrisin boyutu $m\\times n$ kaçtır? Önce **satırları** (yatay sıralar), sonra **sütunları** (dikey sıralar) say.";
    if (z >= 2) {
      alanlar.push(aij + " elemanı");
      cevap.push(A.g(i, j));
      metin = "Matrisin boyutunu ve " + aij + " elemanını yaz. $a_{" + (i + 1) + (j + 1) + "}$: " + (i + 1) + ". satır ile " + (j + 1) + ". sütunun kesiştiği sayı.";
    }
    if (z >= 3) {
      alanlar.push("Eleman sayısı", "$A^T$ kaç satırlı?");
      cevap.push(m * n, n);
      metin = "Boyutu, " + aij + " elemanını, toplam eleman sayısını ve $A^T$'nin satır sayısını bul.";
    }
    const gosterge = (mod, ii, jj) => gostergeCiz(A, { ad: "A", i: ii, j: jj, mod, boyut: true, enGenis: 330 }).dugum;
    return {
      metin,
      sekil: () => duzMatris(A, "A", 40),
      cevap: [cevap], alanlar,
      ipucu: [
        "Satır yataydır (soldan sağa), sütun dikeydir (yukarıdan aşağı).",
        "Boyut her zaman **satır × sütun** sırasıyla yazılır: ilk sayı satır sayısıdır."
      ],
      aciklama: cozum(
        sahneDiv(gosterge("hucre", i, j)),
        para("Mavi ok **satırları** sayar: $m=" + m + "$. Turuncu ok **sütunları** sayar: $n=" + n + "$. Boyut: $" + m + "\\times " + n + "$."),
        z >= 2 ? para("$a_{" + (i + 1) + (j + 1) + "}$: " + (i + 1) + ". satır (mavi şerit) ile " + (j + 1) + ". sütunun (turuncu şerit) kesiştiği hücre = **" + A.g(i, j).toString() + "**.") : null,
        z >= 3 ? para("Eleman sayısı $m\\cdot n=" + m + "\\cdot " + n + "=" + (m * n) + "$. Transpoz satırla sütunu değiştirir: $A^T$ boyutu $" + n + "\\times " + m + "$, yani " + n + " satır.") : null),
      adimlar: [
        { metin: "**1. Satırları say.** Yatay sıraların sayısı $m$'dir.", tex: "m=" + m, sekil: gosterge("satir", i, j) },
        { metin: "**2. Sütunları say.** Dikey sıraların sayısı $n$'dir.", tex: "n=" + n, sekil: gosterge("sutun", i, j) },
        { metin: "**3. Boyutu yaz:** önce satır, sonra sütun.", tex: "A\\in\\mathbb{R}^{" + m + "\\times " + n + "}" }
      ].concat(z >= 2 ? [{ metin: "**4. Elemanı oku.** " + (i + 1) + ". satırda " + (j + 1) + ". sütuna in.", tex: "a_{" + (i + 1) + (j + 1) + "}=" + A.g(i, j).tex(), sekil: gosterge("hucre", i, j) }] : [])
    };
  }), {
    baslik: "Alıştırma: matris boyutu",
    aciklama: "Satır ve sütun say, $m\\times n$ yaz; zorlaştıkça belirli bir elemanı ve eleman sayısını bul.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 2. alistirma:toplama */

  E.kaydet("alistirma:toplama", ak(function (rnd, p) {
    const z = zor(p), nb = boyP(p, 0);
    const m = nb || 2, n = nb || (z === 1 ? 2 : 3);
    const cikar = z === 1 ? false : (z === 2 ? rnd.sayi() < 0.4 : rnd.sayi() < 0.7);
    const alt = z === 1 ? -4 : -8, ust = z === 1 ? 6 : 9;
    const A = Mat.rastgele(rnd, m, n, alt, ust), B = Mat.rastgele(rnd, m, n, alt, ust);
    const C = cikar ? A.cikar(B) : A.topla(B);
    const is = cikar ? "−" : "+", op = cikar ? "cikar" : "topla";
    const hesap = [];
    for (let i = 0; i < m; i++) for (let j = 0; j < n; j++) {
      hesap.push("c_{" + (i + 1) + (j + 1) + "}=\\ka{" + T(A.g(i, j)) + "}" + (cikar ? "-" + "\\kb{" + par(B.g(i, j)) + "}" : "+\\kb{" + par(B.g(i, j)) + "}") + "=\\kc{" + T(C.g(i, j)) + "}");
    }
    const sekil = () => denklemSekli([{ M: A, ad: "A" }, { yaz: is, boyut: 22 }, { M: B, ad: "B" }], { enGenis: 340 });
    return {
      metin: cikar ? "$C=A-B$ matrisini bul. Aynı konumdaki sayılar birbirinden çıkarılır." : "$C=A+B$ matrisini bul. Aynı konumdaki sayılar birbiriyle toplanır.",
      sekil, cevap: C, etiket: "C",
      ipucu: ["Önce iki matrisin boyutu aynı mı bak: " + m + "×" + n + " ve " + m + "×" + n + ".", "$c_{ij}=a_{ij}" + (cikar ? "-" : "+") + "b_{ij}$: sol üstten başla, her hücre için bir işlem."],
      aciklama: cozum(
        sahneDiv(elemanSekli(A, B, C, is)),
        para("Mavi ve turuncu oklar aynı konumdaki iki sayıyı sonuç hücresine taşır. Boyutlar aynı olduğu için işlem tanımlı."),
        hesapKutusu(hesap)),
      adimlar: [
        { metin: "**1. Boyutları karşılaştır.** Toplama/çıkarma için ikisi de $" + m + "\\times " + n + "$ olmalı. Öyle.", sekil: sekil() },
        { metin: "**2. Hücre hücre uygula.** Her $c_{ij}$ için $a_{ij}$ ile $b_{ij}$ " + (cikar ? "çıkarılır" : "toplanır") + ".", sekil: elemanSekli(A, B, C, is) },
        { metin: "**3. Sonuç:**", tex: "C=" + C.tex() }
      ],
      motor: { islem: op, girdi: { A: A.metin(), B: B.metin() } }
    };
  }), {
    baslik: "Alıştırma: matris toplama",
    aciklama: "Aynı boyutlu iki matrisi hücre hücre topla ya da çıkar.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 3. alistirma:skaler */

  E.kaydet("alistirma:skaler", ak(function (rnd, p) {
    const z = zor(p), nb = boyP(p, 0);
    const m = nb || 2, n = nb || (z === 1 ? 2 : 3);
    let k;
    if (z === 1) k = kk(rnd.tam(2, 4));
    else if (z === 2) k = kk(-rnd.tam(1, 4));
    else k = rnd.sec([kk(1, 2), kk(3, 2), kk(-2, 3), kk(2, 3), kk(-1, 2)]);
    const A = Mat.rastgele(rnd, m, n, z === 1 ? -4 : -6, z === 1 ? 6 : 8);
    const C = A.skaler(k);
    const hesap = [];
    for (let i = 0; i < m; i++) for (let j = 0; j < n; j++) hesap.push("c_{" + (i + 1) + (j + 1) + "}=\\kb{" + par(k) + "}\\cdot\\ka{" + par(A.g(i, j)) + "}=\\kc{" + T(C.g(i, j)) + "}");
    const sekil = () => denklemSekli([{ yaz: k.toString(), gen: 14 + 8 * k.toString().length, renk: "b", boyut: 18 }, { M: A, ad: "A" }], { enGenis: 320 });
    return {
      metin: "$k=" + k.tex() + "$ için $kA$ matrisini bul. Skaler **her** hücreyi çarpar.",
      sekil, cevap: C, etiket: "kA",
      ipucu: ["$k$'yı sırayla her hücreyle çarp. Matris boyutu değişmez: " + m + "×" + n + ".", "Negatif sayıyla çarparken işaret değişir; kesirli $k$'da payda ile çalış."],
      aciklama: cozum(
        sahneDiv(elemanSekli(A, null, C, "", k)),
        para("Turuncu $k$ sayısı, her mavi hücreyle çarpılıp yeşil sonuç hücresine yazılır."),
        hesapKutusu(hesap)),
      adimlar: [
        { metin: "**1.** Skaler ($k=" + k.tex() + "$) matrisin **tüm** elemanlarına uygulanır.", sekil: sekil() },
        { metin: "**2.** İlk hücre: $" + par(k) + "\\cdot " + par(A.g(0, 0)) + "=" + T(C.g(0, 0)) + "$. Aynısını diğer hücrelere de yap.", sekil: elemanSekli(A, null, C, "", k) },
        { metin: "**3. Sonuç:**", tex: "kA=" + C.tex() }
      ],
      motor: { islem: "skaler", girdi: { k: k.toString(), A: A.metin() } }
    };
  }), {
    baslik: "Alıştırma: skaler çarpım",
    aciklama: "Bir sayıyla matrisin her hücresini çarp; negatif ve kesirli katsayılar zorlaştıkça gelir.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 4. alistirma:carpim */

  /* A·B şeması: i0 satırı mavi, j0 sütunu turuncu, kesişim yeşil. */
  function carpimSekli(A, B, C, i0, j0) {
    const K = A.n, orta = Math.floor((K - 1) / 2);
    return denklemSekli([
      { M: A, ad: "A", satir: [[i0, "a"]], kutu: [[i0, 0, i0, K - 1, "a", { kalinlik: 2.5 }]] },
      { yaz: "×", boyut: 20 },
      { M: B, ad: "B", sutun: [[j0, "b"]], kutu: [[0, j0, K - 1, j0, "b", { kalinlik: 2.5 }]] },
      { yaz: "=", boyut: 22 },
      { M: C, ad: "C", boya: [[i0, j0, "c"]], kutu: [[i0, j0, i0, j0, "c", { kalinlik: 2.5 }]] }
    ], {
      enGenis: 350,
      oklar: [
        { kimden: [0, i0, orta], kime: [4, i0, j0], renk: "a", egri: -0.4 },
        { kimden: [2, orta, j0], kime: [4, i0, j0], renk: "b", egri: 0.4 }
      ]
    });
  }

  E.kaydet("alistirma:carpim", ak(function (rnd, p) {
    const z = zor(p), nb = boyP(p, 0);
    let m, k, n;
    if (nb) { m = k = n = nb; }
    else if (z === 1) { m = 2; k = 2; n = 2; }
    else if (z === 2) { if (rnd.sayi() < 0.5) { m = 2; k = 3; n = 2; } else { m = 3; k = 2; n = 3; } }
    else { m = 3; k = 3; n = 3; }
    const lo = z === 1 ? -3 : -4, hi = z === 1 ? 5 : 6;
    const A = Mat.rastgele(rnd, m, k, lo, hi), B = Mat.rastgele(rnd, k, n, lo, hi);
    const C = A.carp(B);
    const i0 = rnd.tam(0, m - 1), j0 = rnd.tam(0, n - 1);
    const hesap = [];
    for (let i = 0; i < m; i++) for (let j = 0; j < n; j++) {
      const t = [];
      for (let q = 0; q < k; q++) t.push("\\ka{" + par(A.g(i, q)) + "}\\kb{\\cdot " + par(B.g(q, j)) + "}");
      hesap.push("c_{" + (i + 1) + (j + 1) + "}=" + t.join("+") + "=\\kc{" + T(C.g(i, j)) + "}");
    }
    const sekil = () => denklemSekli([{ M: A, ad: "A" }, { yaz: "×", boyut: 20 }, { M: B, ad: "B" }], { enGenis: 350 });
    return {
      metin: "$AB$ çarpımını hesapla. $c_{ij}$ = $A$'nın $i$. **satırı** ile $B$'nin $j$. **sütununun** karşılıklı çarpımlarının toplamı.",
      sekil, cevap: C, etiket: "AB",
      ipucu: [
        "İç boyutlar eşleşmeli: $(" + m + "\\times " + k + ")(" + k + "\\times " + n + ")$ → sonuç $" + m + "\\times " + n + "$.",
        "$c_{11}$ için $A$'nın 1. satırını $B$'nin 1. sütunuyla çarp ve topla: " + k + " çarpım, " + (k - 1) + " toplama.",
        "Kayıt: sağ taraftaki matrisi yukarıdan aşağı, soldakini soldan sağa oku."
      ],
      aciklama: cozum(
        el("p", null, cip("(" + m + "×" + k + ")·(" + k + "×" + n + ")", "a"), metinDugum(" iç boyutlar **" + k + " = " + k + "** olduğundan çarpım tanımlı; sonuç "), cip(m + "×" + n, "c"), metinDugum(".")),
        sahneDiv(carpimSekli(A, B, C, i0, j0)),
        para("Örnek: $c_{" + (i0 + 1) + (j0 + 1) + "}$ için " + (i0 + 1) + ". satır (mavi kutu) ve " + (j0 + 1) + ". sütun (turuncu kutu) çarpılıp toplanır; sonuç yeşil hücreye yazılır. Aynı kural her hücre için:"),
        hesapKutusu(hesap)),
      adimlar: [
        { metin: "**1. Boyut kontrolü.** İç boyutlar $" + k + "=" + k + "$; çarpım tanımlı, sonuç $" + m + "\\times " + n + "$.", sekil: sekil() },
        { metin: "**2. Bir hücre:** $c_{" + (i0 + 1) + (j0 + 1) + "}$ = " + (i0 + 1) + ". satır · " + (j0 + 1) + ". sütun.", tex: hesap[i0 * n + j0], sekil: carpimSekli(A, B, C, i0, j0) },
        { metin: "**3. Tüm hücreleri doldur:** her satır-sütun çifti için aynısını yap." },
        { metin: "**4. Sonuç:**", tex: "AB=" + C.tex() }
      ],
      motor: { islem: "carp", girdi: { matrisler: [A.metin(), B.metin()] } }
    };
  }), {
    baslik: "Alıştırma: matris çarpımı",
    aciklama: "Satır × sütun kuralıyla çarp; zorlaştıkça boyutlar büyür.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 5. alistirma:transpoz */

  /* A ve Aᵀ yan yana; her satır kendi renginde Aᵀ'nin sütununa dönüşür. */
  function transpozSekli(A, i0, j0) {
    const T_ = A.transpoz(), fam = ["a", "b", "c"];
    return denklemSekli([
      { M: A, ad: "A", satir: A.v.map((_, i) => [i, fam[i % 3]]) },
      { yaz: "→", boyut: 20 },
      { M: T_, ad: "Aᵀ", sutun: A.v.map((_, i) => [i, fam[i % 3]]) }
    ], { enGenis: 350, oklar: [{ kimden: [0, i0, j0], kime: [2, j0, i0], renk: "sil", egri: -0.35 }] });
  }

  E.kaydet("alistirma:transpoz", ak(function (rnd, p) {
    const z = zor(p), nb = boyP(p, 0);
    let m, n;
    if (nb) { m = nb; n = nb === 1 ? 1 : nb + (rnd.sayi() < 0.5 ? -1 : 0); }
    else if (z === 1) { m = 2; n = 3; } else if (z === 2) { m = rnd.sec([3, 4]); n = m === 3 ? 4 : 3; } else { m = 3; n = 3; }
    if (rnd.sayi() < 0.5 && z < 3 && !nb) { const t = m; m = n; n = t; }
    const A = Mat.rastgele(rnd, m, n, -5, 9);
    let B = null, S = A;
    if (z === 3) { B = Mat.rastgele(rnd, m, n, -5, 9); S = A.topla(B); }
    const R = S.transpoz();
    const i0 = rnd.tam(0, S.m - 1), j0 = rnd.tam(0, S.n - 1);
    const sekil = () => (B ? denklemSekli([{ M: A, ad: "A" }, { yaz: "+", boyut: 22 }, { M: B, ad: "B" }], { enGenis: 350 }) : duzMatris(A, "A", 40));
    return {
      metin: B ? "$(A+B)^T$ matrisini bul. Önce topla, sonra satırlarla sütunları değiştir." : "$A^T$ matrisini yaz: $A$'nın satırları $A^T$'nin sütunları olur.",
      sekil, cevap: R, etiket: B ? "(A+B)ᵀ" : "Aᵀ",
      ipucu: B
        ? ["Önce $S=A+B$ hesapla (hücre hücre).", "Sonra $S$'nin 1. satırını 1. sütun yap, 2. satırını 2. sütun yap, böyle devam et."]
        : ["$A$ " + A.m + "×" + A.n + " ise $A^T$ " + A.n + "×" + A.m + " olur.", "$A$'nın 1. satırını soldan sağa oku, $A^T$'nin 1. sütununa yukarıdan aşağı yaz."],
      aciklama: cozum(
        B ? sahneDiv(elemanSekli(A, B, S, "+")) : null,
        B ? para("Önce $S=A+B$ (yukarıdaki toplama), sonra $S^T$:") : null,
        sahneDiv(transpozSekli(S, i0, j0)),
        para("Her satır kendi rengindeki sütuna döner. Kırmızı ok bir örnek: $s_{" + (i0 + 1) + (j0 + 1) + "}$ sayısı $(" + (i0 + 1) + "," + (j0 + 1) + ")$'den $(" + (j0 + 1) + "," + (i0 + 1) + ")$'ye taşınır. Boyut $" + S.m + "\\times " + S.n + "$ iken $" + S.n + "\\times " + S.m + "$ olur.")),
      adimlar: (B ? [{ metin: "**1. Topla:** $S=A+B$.", tex: "S=" + S.tex(), sekil: elemanSekli(A, B, S, "+") }] : []).concat([
        { metin: "**" + (B ? 2 : 1) + ". Satırları sütuna çevir.** Aynı renkli şerit, yeni sütun olur.", sekil: transpozSekli(S, i0, j0) },
        { metin: "**" + (B ? 3 : 2) + ". Sonuç** ($" + S.n + "\\times " + S.m + "):", tex: (B ? "(A+B)^T=" : "A^T=") + R.tex() }
      ]),
      motor: B ? undefined : { islem: "transpoz", girdi: { A: A.metin() } }
    };
  }), {
    baslik: "Alıştırma: transpoz",
    aciklama: "Satırları sütun yap; zorlaştıkça $(A+B)^T$ gelir.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 6. alistirma:determinant */

  /* 3×3 Sarrus şeması. asama: 0 yalnız genişletilmiş matris, 1 + mavi köşegenler, 2 + turuncu köşegenler. */
  function sarrusSekli(A, asama) {
    const ext = new Mat(A.v.map(r => r.concat([r[0], r[1]])));
    const c = 34, ML = 6, MT = 8;
    const M = matrisCiz(ext, { x: ML, y: MT, hucre: c, parantez: false });
    for (let i = 0; i < 3; i++) for (let j = 3; j < 5; j++) M.boya(i, j, "cizgi");
    const s = sahne(ML + M.genislik + 6, MT + M.yukseklik + 8, "Sarrus kuralı: üç artı, üç eksi köşegen");
    s.appendChild(M.g);
    const bar = ML + 8 + 3 * c;
    s.appendChild(svg("line", { x1: bar, y1: MT - 2, x2: bar, y2: MT + 3 * c + 2, "stroke-width": 2, "stroke-dasharray": "4 3", style: { stroke: renk("soluk") } }));
    if (asama >= 1) for (let q = 0; q < 3; q++) s.appendChild(okHucre(M.hucre(0, q), M.hucre(2, q + 2), { renk: "a", kalinlik: 2.2, bas: 7, ilk: 8, son: 10 }));
    if (asama >= 2) for (let q = 0; q < 3; q++) s.appendChild(okHucre(M.hucre(2, q), M.hucre(0, q + 2), { renk: "b", kalinlik: 2.2, bas: 7, ilk: 8, son: 10 }));
    return s;
  }

  function det2Sekli(A) {
    const c = 44, M = matrisCiz(A, { x: 6, y: 6, hucre: c });
    const s = sahne(M.genislik + 12, M.yukseklik + 12, "2×2 determinant: iki köşegen");
    s.appendChild(M.g);
    s.appendChild(okHucre(M.hucre(0, 0), M.hucre(1, 1), { renk: "a", kalinlik: 2.6, bas: 8, ilk: 9, son: 11 }));
    s.appendChild(okHucre(M.hucre(0, 1), M.hucre(1, 0), { renk: "b", kalinlik: 2.6, bas: 8, ilk: 9, son: 11 }));
    return s;
  }

  E.kaydet("alistirma:determinant", ak(function (rnd, p) {
    const z = zor(p);
    const n = boyP(p, z === 1 ? 2 : 3);
    let A = null, d = null;
    for (let t = 0; t < 200; t++) {
      if (n === 4) {
        A = Mat.rastgele(rnd, 4, 4, -3, 4);
        const sat = rnd.tam(0, 3);
        for (let j = 0; j < 4; j++) if (j !== rnd.tam(0, 3) && rnd.sayi() < 0.7) A = A.harita((x, i, jj) => (i === sat && jj === j ? Kesir.SIFIR : x));
      } else {
        A = Mat.rastgele(rnd, n, n, z === 1 ? -5 : (z === 2 ? -3 : -5), z === 1 ? 7 : (z === 2 ? 5 : 6));
        if (n === 3 && z === 2) { const i = rnd.tam(0, 2), j = rnd.tam(0, 2); A = A.harita((x, a, b) => (a === i && b === j ? Kesir.SIFIR : x)); }
      }
      d = A.det();
      if (!d.sifirMi()) break;
    }
    const sekilSoru = () => duzMatris(A, "A", n === 4 ? 36 : 42);
    const a = i => j => A.g(i, j);
    let aciklama, adimlar;
    if (n === 1 || n === 2) {
      const [p11, p12, p21, p22] = [A.g(0, 0), A.g(0, 1), A.g(1, 0), A.g(1, 1)];
      const tx = "\\det A=\\ka{" + par(p11) + "\\cdot " + par(p22) + "}-\\kb{" + par(p12) + "\\cdot " + par(p21) + "}=\\ka{" + T(p11.carp(p22)) + "}-\\kb{" + par(p12.carp(p21)) + "}=\\kutuc{" + T(d) + "}";
      aciklama = cozum(sahneDiv(det2Sekli(A)),
        para("**Mavi köşegen** (sol üstten sağ alta) çarpımı artı, **turuncu köşegen** (sağ üstten sol alta) çarpımı eksi alınır."),
        blok(tx));
      adimlar = [
        { metin: "**1. Ana köşegeni çarp** (mavi): $a_{11}a_{22}$.", tex: "\\ka{" + par(p11) + "\\cdot " + par(p22) + "}=" + T(p11.carp(p22)), sekil: det2Sekli(A) },
        { metin: "**2. Ters köşegeni çarp** (turuncu): $a_{12}a_{21}$.", tex: "\\kb{" + par(p12) + "\\cdot " + par(p21) + "}=" + T(p12.carp(p21)) },
        { metin: "**3. Çıkar:** ana köşegen eksi ters köşegen.", tex: tx }
      ];
    } else if (n === 3) {
      const g = (i, j) => A.g(i, j);
      const art = [0, 1, 2].map(q => g(0, q).carp(g(1, (q + 1) % 3)).carp(g(2, (q + 2) % 3)));
      const eks = [0, 1, 2].map(q => g(2, q).carp(g(1, (q + 1) % 3)).carp(g(0, (q + 2) % 3)));
      const artTex = [0, 1, 2].map(q => par(g(0, q)) + "\\cdot " + par(g(1, (q + 1) % 3)) + "\\cdot " + par(g(2, (q + 2) % 3)));
      const eksTex = [0, 1, 2].map(q => par(g(2, q)) + "\\cdot " + par(g(1, (q + 1) % 3)) + "\\cdot " + par(g(0, (q + 2) % 3)));
      const sA = art.reduce((x, y) => x.topla(y), Kesir.SIFIR), sB = eks.reduce((x, y) => x.topla(y), Kesir.SIFIR);
      const t1 = "\\ka{" + artTex.join("+") + "}=\\ka{" + art.map(T).join("+(") .replace(/\+\(/g, "+(") + "}";
      const artDeger = art.map((x, q) => (q ? "+" : "") + par(x)).join("");
      const eksDeger = eks.map((x, q) => (q ? "+" : "") + par(x)).join("");
      aciklama = cozum(sahneDiv(sarrusSekli(A, 2)),
        para("İlk iki sütunu sağa tekrar yaz (sönük). **Mavi** üç köşegen ($\\searrow$) toplanır, **turuncu** üç köşegen ($\\nearrow$) çıkarılır."),
        blok("\\ka{" + artTex.join("+") + "}\\;=\\;\\ka{" + T(sA) + "}"),
        blok("\\kb{" + eksTex.join("+") + "}\\;=\\;\\kb{" + T(sB) + "}"),
        blok("\\det A=\\ka{" + T(sA) + "}-\\kb{" + par(sB) + "}=\\kutuc{" + T(d) + "}"));
      adimlar = [
        { metin: "**1. İlk iki sütunu sağa tekrar yaz.**", sekil: sarrusSekli(A, 0) },
        { metin: "**2. Mavi köşegenleri çarp ve topla** (sağa aşağı).", tex: "\\ka{" + artTex.join("+") + "}=\\ka{" + artDeger + "}=\\ka{" + T(sA) + "}", sekil: sarrusSekli(A, 1) },
        { metin: "**3. Turuncu köşegenleri çarp ve topla** (sağa yukarı).", tex: "\\kb{" + eksTex.join("+") + "}=\\kb{" + eksDeger + "}=\\kb{" + T(sB) + "}", sekil: sarrusSekli(A, 2) },
        { metin: "**4. Mavi toplamdan turuncu toplamı çıkar.**", tex: "\\det A=\\ka{" + T(sA) + "}-\\kb{" + par(sB) + "}=" + T(d) }
      ];
      void t1;
    } else {
      // 4×4: en çok sıfırı olan satırdan kofaktör açılımı
      let en = 0, say = -1;
      for (let i = 0; i < 4; i++) { const s = A.satir(i).filter(x => x.sifirMi()).length; if (s > say) { say = s; en = i; } }
      const terimler = [], tx = [];
      for (let j = 0; j < 4; j++) {
        const a = A.g(en, j);
        if (a.sifirMi()) continue;
        const kof = A.kofaktor(en, j);
        terimler.push(a.carp(kof));
        tx.push("\\ka{" + par(a) + "}\\cdot\\kb{" + par(kof) + "}");
      }
      const tablo = A.kare() ? A : A;
      aciklama = cozum(
        sahneDiv(gostergeCiz(tablo, { ad: "A", i: en, j: 0, mod: "satir", boyut: false, enGenis: 320 }).dugum),
        para("En çok sıfırı olan **" + (en + 1) + ". satırdan** açılım: sıfırlı terimler hiç hesaplanmaz. $\\kb{C_{ij}}$ = işaretli $3\\times3$ minör determinantı."),
        blok("\\det A=" + (tx.length ? tx.join("+") : "0") + "=\\kutuc{" + T(d) + "}"));
      adimlar = [
        { metin: "**1. Sıfırı çok olan satırı seç:** " + (en + 1) + ". satır.", sekil: gostergeCiz(tablo, { ad: "A", i: en, j: 0, mod: "satir", boyut: false, enGenis: 320 }).dugum },
        { metin: "**2. Sıfırdan farklı her eleman için** $a_{ij}\\cdot C_{ij}$ yaz ($C_{ij}=(-1)^{i+j}\\det M_{ij}$).", tex: tx.join("+") },
        { metin: "**3. Topla:**", tex: "\\det A=" + T(d) }
      ];
    }
    void a;
    return {
      metin: "Aşağıdaki matrisin determinantını hesapla.",
      sekil: sekilSoru, cevap: Mat.al(d), etiket: "det A",
      ipucu: n === 2 ? ["$\\det\\begin{bmatrix}a&b\\\\c&d\\end{bmatrix}=ad-bc$.", "Ana köşegen çarpımı eksi ters köşegen çarpımı."]
        : n === 3 ? ["Sarrus: ilk iki sütunu sağa tekrar yaz, 3 köşegeni topla, 3 köşegeni çıkar.", "Bir satır ya da sütunda sıfır varsa kofaktör açılımı da kısa sürer."]
          : ["Sıfırı en çok olan satır ya da sütundan kofaktör aç.", "Her terim: $a_{ij}\\cdot(-1)^{i+j}\\cdot$ ($3\\times3$ minör determinantı)."],
      aciklama, adimlar,
      motor: { islem: "determinant", girdi: { A: A.metin() } }
    };
  }), {
    baslik: "Alıştırma: determinant",
    aciklama: "$2\\times2$ köşegen kuralı, $3\\times3$ Sarrus ve kofaktör açılımıyla determinant hesapla.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 7. alistirma:ters */

  function ters2Sekli(A) {
    const c = 46, M = matrisCiz(A, { x: 6, y: 6, hucre: c });
    const s = sahne(M.genislik + 12, M.yukseklik + 12, "2×2 ters: köşegen yer değiştirir, diğerlerinin işareti döner");
    s.appendChild(M.g);
    M.boya(0, 0, "a"); M.boya(1, 1, "a"); M.boya(0, 1, "sil"); M.boya(1, 0, "sil");
    s.appendChild(okHucre(M.hucre(0, 0), M.hucre(1, 1), { renk: "a", egri: 0.3, kalinlik: 2.2, bas: 7, ilk: 9, son: 11 }));
    s.appendChild(okHucre(M.hucre(1, 1), M.hucre(0, 0), { renk: "a", egri: 0.3, kalinlik: 2.2, bas: 7, ilk: 9, son: 11 }));
    return s;
  }

  E.kaydet("alistirma:ters", ak(function (rnd, p) {
    const z = zor(p);
    const n = boyP(p, z === 1 ? 2 : 3);
    const mk = z === 1 ? 4 : (z === 2 ? 2 : 6);
    let A = null, d = null;
    for (let t = 0; t < 400; t++) {
      if (n === 1) A = Mat.rastgele(rnd, 1, 1, 2, 6);
      else if (n === 2) A = Mat.rastgele(rnd, 2, 2, -4, 5);
      else if (n === 3) A = Mat.rastgele(rnd, 3, 3, z === 2 ? -2 : -3, z === 2 ? 3 : 4);
      else A = Mat.rastgele(rnd, 4, 4, -1, 2);
      d = A.det();
      if (!d.sifirMi() && Number(d.mutlak().sayi()) <= (n === 4 ? 2 : mk)) break;
    }
    const Ti = A.ters();
    const dN = Number(d.sayi());
    let aciklama, adimlar;
    if (n === 2) {
      const [a1, b1, c1, d1] = [A.g(0, 0), A.g(0, 1), A.g(1, 0), A.g(1, 1)];
      const adj = "\\begin{bmatrix}\\ka{" + T(d1) + "}&\\ksil{" + T(b1.neg()) + "}\\\\ \\ksil{" + T(c1.neg()) + "}&\\ka{" + T(a1) + "}\\end{bmatrix}";
      aciklama = cozum(
        sahneDiv(ters2Sekli(A)),
        para("**Mavi** köşegen elemanlar yer değiştirir, **kırmızı** elemanların işareti değişir; sonra hepsi $\\det A$'ya bölünür."),
        blok("\\det A=" + T(a1) + "\\cdot " + par(d1) + "-" + par(b1) + "\\cdot " + par(c1) + "=\\kb{" + T(d) + "}\\ne 0"),
        blok("A^{-1}=\\dfrac{1}{\\kb{" + T(d) + "}}" + adj + "=\\kutuc{" + Ti.tex() + "}"),
        para("Kontrol için $AA^{-1}=I$ olmalı."));
      adimlar = [
        { metin: "**1. Determinantı hesapla.** Sıfırsa ters yoktur.", tex: "\\det A=\\kb{" + T(d) + "}", sekil: ters2Sekli(A) },
        { metin: "**2. Ek matrisi kur:** köşegeni değiştir, diğerlerinin işaretini çevir.", tex: "\\operatorname{adj}A=" + adj },
        { metin: "**3. $\\det A$'ya böl.**", tex: "A^{-1}=\\dfrac{1}{" + T(d) + "}" + adj + "=" + Ti.tex() }
      ];
    } else if (n === 1) {
      aciklama = cozum(para("$1\\times1$ matrisin tersi $1/a$'dır."), blok("A^{-1}=\\kutuc{" + Ti.tex() + "}"));
      adimlar = [{ metin: "**Tersini al:** $a^{-1}=1/a$.", tex: "A^{-1}=" + Ti.tex() }];
    } else {
      const { G, liste } = gaussAdimListesi(A, Mat.birim(n), n, 340);
      const ilk = { metin: "**Başla:** $A$'nın sağına birim matrisi yaz: $[A\\,|\\,I]$. Amaç sol yarıyı $I$ yapmak.", sekil: gaussCiz(G.durumlar[0], n, { enGenis: 340 }).dugum };
      const son = G.durumlar[G.durumlar.length - 1];
      aciklama = cozum(
        para("Gauss–Jordan: $[A\\,|\\,I]$ matrisine satır işlemleri uygulanır. Sol yarı $I$ olunca sağ yarı $A^{-1}$ olur."),
        sahneDiv(gaussCiz(son, n, { bitti: true, enGenis: 340 }).dugum),
        para("Bu çözümde " + G.islemler.length + " satır işlemi yapıldı ($\\det A=" + T(d) + "\\ne0$, ters var). Sağ yarı:"),
        blok("A^{-1}=\\kutuc{" + Ti.tex() + "}"),
        para("Her adımı görmek için **Adım adım çözüm** düğmesine bas."));
      adimlar = [ilk].concat(liste, [{ metin: "**Sonuç:** sol yarı $I$ oldu, sağ yarı tersi verir.", tex: "A^{-1}=" + Ti.tex() }]);
    }
    void dN;
    return {
      metin: n === 2 ? "$A^{-1}$ matrisini bul. $2\\times2$ için kısa yol: köşegeni değiştir, diğerlerinin işaretini çevir, $\\det A$'ya böl." : "$A^{-1}$ matrisini bul (ipucu: $[A\\,|\\,I]$ üzerinde Gauss–Jordan).",
      sekil: () => duzMatris(A, "A", n >= 4 ? 34 : 42), cevap: Ti, etiket: "A⁻¹",
      ipucu: n === 2
        ? ["Önce $\\det A=ad-bc$ hesapla; sıfır olmadığını gör.", "$A^{-1}=\\dfrac{1}{\\det A}\\begin{bmatrix}d&-b\\\\-c&a\\end{bmatrix}$"]
        : ["$[A\\,|\\,I]$ yaz. Her sütunda pivotu 1 yap, sütunun diğer elemanlarını sıfırla.", "Sol yarı $I$ olunca sağ yarı $A^{-1}$ olur. Kontrol: $AA^{-1}=I$."],
      aciklama, adimlar,
      motor: { islem: "ters", girdi: { A: A.metin() } }
    };
  }), {
    baslik: "Alıştırma: ters matris",
    aciklama: "$2\\times2$ için ek matris formülü, $3\\times3$ için Gauss–Jordan ile $A^{-1}$ bul.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 8. alistirma:coz */

  function denkTex(A, b) {
    const satirlar = A.v.map((r, i) => {
      let s = "";
      r.forEach((a, j) => {
        if (a.sifirMi()) return;
        const neg = a.isaret() < 0, mut = a.mutlak(), kat = mut.esit(1) ? "" : mut.tex();
        s += (s === "" ? (neg ? "-" : "") : (neg ? "-" : "+")) + kat + "x_{" + (j + 1) + "}";
      });
      return (s || "0") + "&=" + T(b.g(i, 0));
    });
    return "\\begin{aligned}" + satirlar.join("\\\\") + "\\end{aligned}";
  }

  E.kaydet("alistirma:coz", ak(function (rnd, p) {
    const z = zor(p);
    const n = boyP(p, z === 1 ? 2 : 3);
    let A = null, b = null, x = null;
    for (let t = 0; t < 400; t++) {
      const lo = z === 1 ? -3 : -3, hi = z === 1 ? 4 : 4;
      A = Mat.rastgele(rnd, n, n, lo, hi);
      const d = A.det();
      if (d.sifirMi() || Number(d.mutlak().sayi()) > (z === 3 ? 7 : (n === 2 ? 6 : 5))) continue;
      if (z === 3) { b = Mat.rastgele(rnd, n, 1, -6, 9); x = A.ters().carp(b); }
      else { x = Mat.rastgele(rnd, n, 1, -3, 4); b = A.carp(x); }
      break;
    }
    const G = gaussAdimlari(A, b);
    const alanlar = Array.from({ length: n }, (_, i) => "$x_{" + (i + 1) + "}$");
    const sistem = () => el("div", { class: "kx-tex-blok km-sahne" }, texDugum(denkTex(A, b), true));
    const sekilSoru = () => {
      const kap = el("div", null);
      kap.appendChild(texDugum(denkTex(A, b), true));
      return kap;
    };
    const sonSatir = x.v.map((r, i) => "x_{" + (i + 1) + "}=\\kc{" + T(r[0]) + "}").join(",\\;\\;");
    let kontrol = "";
    {
      const t = [];
      for (let j = 0; j < n; j++) if (!A.g(0, j).sifirMi()) t.push(par(A.g(0, j)) + "\\cdot " + par(x.g(j, 0)));
      kontrol = "1.\\text{ denklem: }" + t.join("+") + "=" + T(b.g(0, 0)) + "\\;\\checkmark";
    }
    const { liste } = gaussAdimListesi(A, b, n, 330);
    const aciklama = cozum(
      para("Genişletilmiş matris $[A\\,|\\,b]$ satır işlemleriyle $[I\\,|\\,x]$ biçimine getirilir; sağ sütun çözümü verir."),
      sahneDiv(gaussCiz(G.durumlar[G.durumlar.length - 1], n, { bitti: true, enGenis: 330 }).dugum),
      blok(sonSatir),
      para("Kontrol (çözümü ilk denkleme koy):"),
      blok(kontrol));
    void sistem;
    return {
      metin: "Aşağıdaki " + n + " bilinmeyenli doğrusal denklem sistemini çöz. Matris biçimi: $Ax=b$.",
      sekil: sekilSoru, cevap: x, alanlar,
      ipucu: ["$[A\\,|\\,b]$ genişletilmiş matrisini yaz: katsayılar solda, sağ taraf en sağ sütunda.", "Her sütunda pivotu 1 yap, o sütundaki diğer elemanları sıfırla (Gauss–Jordan).", "Bitince sağ sütundaki sayılar sırasıyla $x_1,x_2,\\dots$ olur." + (z === 3 ? " Sonuç kesirli çıkabilir." : "")],
      aciklama,
      adimlar: [{ metin: "**Başla:** katsayıları ve sağ tarafı tek matriste topla: $[A\\,|\\,b]$.", tex: "[A\\,|\\,b]", sekil: gaussCiz(G.durumlar[0], n, { enGenis: 330 }).dugum }]
        .concat(liste, [{ metin: "**Sonuç:** sol yarı $I$ oldu; sağ sütun çözümdür.", tex: sonSatir }]),
      motor: { islem: "coz", girdi: { A: A.metin(), b: b.metin() } }
    };
  }), {
    baslik: "Alıştırma: denklem sistemi",
    aciklama: "Gauss–Jordan ile $Ax=b$ sistemini çöz; zorlaştıkça kesirli çözümler gelir.",
    varsayilan: { zorluk: 1 }
  });

  /* ================================================================ 9. alistirma:ozdeger */

  function polyTex(c) {
    const n = c.length - 1;
    let s = "";
    c.forEach((v, i) => {
      if (v === 0) return;
      const d = n - i, neg = v < 0, m = Math.abs(v);
      let t = m === 1 && d > 0 ? "" : String(m);
      if (d > 0) t += "\\lambda" + (d > 1 ? "^{" + d + "}" : "");
      s += (s === "" ? (neg ? "-" : "") : (neg ? "-" : "+")) + t;
    });
    return s || "0";
  }

  function amlTex(A) {
    return "\\begin{bmatrix}" + A.v.map((r, i) => r.map((x, j) => (i === j ? "\\kb{" + T(x) + "-\\lambda}" : T(x))).join("&")).join("\\\\") + "\\end{bmatrix}";
  }

  E.kaydet("alistirma:ozdeger", ak(function (rnd, p) {
    const z = zor(p), nb = boyP(p, 0);
    const n = nb ? (nb >= 3 ? 3 : 2) : (z === 3 ? 3 : 2);
    const simetri = !nb && z === 1;
    let A = null, ozler = null, vek = null;
    for (let t = 0; t < 400; t++) {
      if (simetri) {
        const a = rnd.tam(-2, 4), b = rnd.tam(1, 3);
        A = Mat.al([[a, b], [b, a]]);
        ozler = [{ l: a - b, v: [1, -1] }, { l: a + b, v: [1, 1] }];
      } else if (n === 2) {
        let l1 = rnd.tam(-3, 5), l2 = rnd.tam(-3, 5);
        if (l1 === l2) continue;
        let s = rnd.sec([-2, -1, 1, 2]), tt = rnd.tam(-2, 2);
        const P = Mat.al([[1, s], [tt, 1 + s * tt]]);
        A = P.carp(Mat.al([[l1, 0], [0, l2]])).carp(P.ters());
        ozler = [{ l: l1, v: [1, tt] }, { l: l2, v: [s, 1 + s * tt] }];
        if (A.g(0, 1).sifirMi() && A.g(1, 0).sifirMi()) continue;
      } else {
        const ls = [rnd.tam(-2, 4), rnd.tam(-2, 4), rnd.tam(-2, 4)];
        if (ls[0] === ls[1] || ls[0] === ls[2] || ls[1] === ls[2]) continue;
        const L = Mat.al([[1, 0, 0], [rnd.tam(-1, 1), 1, 0], [rnd.tam(-1, 1), rnd.tam(-1, 1), 1]]);
        const U = Mat.al([[1, rnd.tam(-1, 1), rnd.tam(-1, 1)], [0, 1, rnd.tam(-1, 1)], [0, 0, 1]]);
        const P = L.carp(U);
        A = P.carp(Mat.al([[ls[0], 0, 0], [0, ls[1], 0], [0, 0, ls[2]]])).carp(P.ters());
        const buyuk = A.sayilar().some(x => Math.abs(Number(x)) > 14);
        if (buyuk) continue;
        ozler = ls.map((l, i) => ({ l, v: [P.g(0, i), P.g(1, i), P.g(2, i)].map(x => Number(x.sayi())) }));
      }
      break;
    }
    ozler.sort((u, w) => u.l - w.l);
    const lam = ozler.map(o => o.l);
    const tr = Number(A.iz().sayi()), dt = Number(A.det().sayi());
    let katsayi;
    if (n === 2) katsayi = [1, -tr, dt];
    else {
      const g = (i, j) => Number(A.g(i, j).sayi());
      const c2 = g(0, 0) * g(1, 1) - g(0, 1) * g(1, 0) + g(0, 0) * g(2, 2) - g(0, 2) * g(2, 0) + g(1, 1) * g(2, 2) - g(1, 2) * g(2, 1);
      katsayi = [1, -tr, c2, -dt];
    }
    // z2: en küçük özdeğerin özvektörü, v1 = 1 olacak biçimde
    const vSor = !simetri && n === 2 && z >= 2 && ozler[0].v[0] !== 0;
    let r = null;
    if (vSor) r = kk(ozler[0].v[1]).bol(kk(ozler[0].v[0]));
    const alanlar = lam.map((_, i) => "$\\lambda_{" + (i + 1) + "}$").concat(vSor ? ["$v_2$ ($v_1=1$ iken)"] : []);
    const cevap = lam.slice();
    if (vSor) cevap.push(r);
    const carpan = lam.map(l => "(\\lambda" + (l === 0 ? "" : (l > 0 ? "-" + l : "+" + (-l))) + ")").join("");
    const carpanKutu = lam.map(l => "\\kutuc{\\lambda_" + (lam.indexOf(l) + 1) + "=" + l + "}").join(",\\;");
    const metin = "Matrisin özdeğerlerini bul (küçükten büyüğe sırala, $\\lambda_1\\le\\lambda_2" + (n === 3 ? "\\le\\lambda_3" : "") + "$)." +
      (vSor ? " Ayrıca $\\lambda_1$'e ait özvektörün $v_1=1$ alınmış hâlinde $v_2$ değerini yaz." : "") +
      " Karakteristik denklem: $\\det(A-\\lambda I)=0$.";
    const sekil = () => duzMatris(A, "A", n === 3 ? 40 : 46);
    let vSekli = null, vTex = "";
    if (vSor) {
      const lv = ozler[0].l;
      const vv = Mat.al([[1], [r]]);
      vSekli = () => denklemSekli([
        { M: A, ad: "A" },
        { M: vv, ad: "v", sutun: [[0, "b"]] },
        { yaz: "=", boyut: 22 },
        { M: vv.skaler(kk(lv)), ad: "λ₁v", sutun: [[0, "c"]] }
      ], { enGenis: 330 });
      vTex = "(A-\\lambda_1I)v=0,\\; v_1=1\\;\\Rightarrow\\; v_2=\\kb{" + T(r) + "}";
    }
    const polinom = polyTex(katsayi);
    const aciklama = cozum(
      para("**1.** $A-\\lambda I$: köşegenden $\\lambda$ çıkarılır (turuncu), determinantı sıfıra eşitlenir."),
      blok("A-\\lambda I=" + amlTex(A)),
      blok("\\det(A-\\lambda I)=\\ka{" + polinom + "}=0"),
      blok(carpan + "=0\\;\\Rightarrow\\; " + carpanKutu),
      para("**Kontrol:** özdeğerlerin toplamı $= \\operatorname{iz}A$: $" + lam.join("+") + "=" + tr + "$; çarpımı $=\\det A$: $" + lam.map(par0).join("\\cdot ") + "=" + dt + "$."),
      vSekli ? para("**2.** $\\lambda_1=" + lam[0] + "$ için $v_1=1$ alınırsa $v_2=" + T(r) + "$. Bu vektör $Av=\\lambda_1v$ eşitliğini sağlar:") : null,
      vSekli ? sahneDiv(vSekli()) : null);
    function par0(x) { return x < 0 ? "(" + x + ")" : String(x); }
    const adimlar = [
      { metin: "**1. $A-\\lambda I$ matrisini yaz.** Köşegen elemanlardan $\\lambda$ çıkar.", tex: "A-\\lambda I=" + amlTex(A), sekil: sekil() },
      { metin: "**2. Determinantı aç** (" + (n === 2 ? "$2\\times2$: ana köşegen − ters köşegen" : "$3\\times3$: Sarrus") + "). Sonuç $\\lambda$'da " + (n === 2 ? "ikinci" : "üçüncü") + " derece polinomdur.", tex: "\\det(A-\\lambda I)=\\ka{" + polinom + "}" },
      { metin: "**3. Katsayıları kontrol et:** $\\lambda" + (n === 2 ? "" : "^2") + "$ katsayısı $-\\operatorname{iz}A=" + (-tr) + "$, sabit terim $" + (n === 2 ? "\\det A" : "-\\det A") + "$.", tex: "\\operatorname{iz}A=" + tr + ",\\;\\det A=" + dt },
      { metin: "**4. Polinomu çarpanlarına ayır, kökleri oku.**", tex: carpan + "=0\\Rightarrow " + carpanKutu }
    ];
    if (vSor) adimlar.push({ metin: "**5. Özvektör.** $\\lambda_1$ için $(A-\\lambda_1I)v=0$ çöz; $v_1=1$ al.", tex: vTex, sekil: vSekli() });
    return {
      metin, sekil, cevap: [cevap], alanlar,
      ipucu: [
        "$\\det(A-\\lambda I)=0$ yaz. $2\\times2$ için polinom: $\\lambda^2-(\\operatorname{iz}A)\\lambda+\\det A=0$.",
        "İz $=" + tr + "$ ve $\\det A=" + dt + "$ — köklerin toplamı iz, çarpımı determinant olmalı.",
        "Tamsayı kökleri $\\det A$'nın bölenleri arasında ara."
      ],
      aciklama, adimlar,
      motor: { islem: "ozdeger", girdi: { A: A.metin() } }
    };
  }), {
    baslik: "Alıştırma: özdeğer",
    aciklama: "Karakteristik denklemden özdeğerleri bul; zorlaştıkça özvektör ve $3\\times3$ matrisler gelir.",
    varsayilan: { zorluk: 1 }
  });

  /*__DEVAM__*/
})(window.Etkilesim);
