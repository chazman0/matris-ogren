/* Matris Öğren — ısı haritaları (§16.4): hangi elemanın neresi ne kadar zorlanıyor, ne kadar yer değiştiriyor.
   Yapı görünümü (bütün çubuklar gerçek kesit katısı ya da ince tüp; istasyon değerlerinden renk) ve eleman görünümü
   (tek eleman büyük ölçekte; lif gerilmesi σ(x, y, z); kesit düzlemi + 2B kesit haritası + tarafsız eksen; boyunca
   N, V, M, T ve sehim grafikleri).

   API (tarayıcı):
     const g = MatrisIsi.ac(kapsayici, {alan, bina?, secim?, olay: {elemanSec(no, kayit), kapat(), durumSec?(ad), tasarim?(kayit)}})
       → {guncelle(alan), kapat(), goruntuAl(), sec(no), incele(no), durum(), kareSuresi(n)}
     alan  = köprü "bina_alan" yanıtının "alan" sözlüğü (alan.eleman_alanlari şeması, §16.1–16.2);
     bina  = bina JSON'u (kat ve aks adları süzgeçler için; yoksa koordinatlardan türetilir);
     secim = başlangıçta seçili FE eleman no'su / no listesi / {tur, no} (bina elemanı).
   Bağımlılıksız: WebGL (2 ya da 1) — tek köşe tamponu, renk değerleri ayrı tamponda (büyüklük değişince yalnız o güncellenir),
   renk kimliğiyle seçim (picking); WebGL yoksa SVG yedek. Saf yardımcılar DOM'suzdur ve Node'da module.exports ile
   testlenir (testler/js/isi_haritasi.test.js).

   İşaret kuralı (alan.py ile aynı; testle kilitli): σ(y, z) = N/A − Mz·y/Iz − My·z/Iy  (y, z yerel; çekme +; MPa).
   Mz > 0 alt (−y′) lifi, My > 0 −z′ lifini çeker. */
(function (kok) {
  "use strict";

  // =====================================================================================
  // 1. Biçim yardımcıları
  // =====================================================================================
  function fmt(v, n) {
    if (typeof v !== "number") return v == null ? "—" : String(v);
    if (!isFinite(v)) return "—";
    const a = Math.abs(v);
    if (a < 1e-12) return "0";
    let t;
    if (a >= 1e6 || a < 1e-3) t = v.toExponential(Math.max(1, (n || 4) - 1)).replace("e+", "e");
    else t = String(parseFloat(v.toPrecision(n || 4)));
    return t.replace(".", ",").replace("-", "−");
  }
  function kacis(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function sayiOku(s) {
    if (typeof s === "number") return isFinite(s) ? s : null;
    const t = String(s == null ? "" : s).trim().replace(/\s/g, "").replace(",", ".").replace("−", "-");
    if (!t) return null;
    const v = Number(t);
    return isFinite(v) ? v : null;
  }

  // =====================================================================================
  // 2. Büyüklükler (yapı görünümü seçicisi) ve istasyon değerleri
  // =====================================================================================
  const BUYUKLUKLER = [
    { ad: "u", etiket: "|u| toplam yer değiştirme", kisa: "|u|", birim: "mm", grup: "Yer değiştirme", iki: false },
    { ad: "uX", etiket: "u_X yer değiştirme", kisa: "u_X", birim: "mm", grup: "Yer değiştirme", iki: true },
    { ad: "uY", etiket: "u_Y yer değiştirme", kisa: "u_Y", birim: "mm", grup: "Yer değiştirme", iki: true },
    { ad: "uZ", etiket: "u_Z yer değiştirme (düşey)", kisa: "u_Z", birim: "mm", grup: "Yer değiştirme", iki: true },
    { ad: "N", etiket: "N eksenel kuvvet (çekme +)", kisa: "N", birim: "kN", grup: "İç kuvvet", iki: true },
    { ad: "Vy", etiket: "V_y′ kesme kuvveti", kisa: "V_y′", birim: "kN", grup: "İç kuvvet", iki: true },
    { ad: "Vz", etiket: "V_z′ kesme kuvveti", kisa: "V_z′", birim: "kN", grup: "İç kuvvet", iki: true },
    { ad: "T", etiket: "T burulma momenti", kisa: "T", birim: "kN·m", grup: "İç kuvvet", iki: true },
    { ad: "My", etiket: "M_y′ eğilme momenti", kisa: "M_y′", birim: "kN·m", grup: "İç kuvvet", iki: true },
    { ad: "Mz", etiket: "M_z′ eğilme momenti (güçlü eksen)", kisa: "M_z′", birim: "kN·m", grup: "İç kuvvet", iki: true },
    { ad: "sigma_max", etiket: "σ_maks en dış lif", kisa: "σ_maks", birim: "MPa", grup: "Gerilme", iki: true },
    { ad: "sigma_min", etiket: "σ_min en dış lif", kisa: "σ_min", birim: "MPa", grup: "Gerilme", iki: true },
    { ad: "sigma_lif", etiket: "σ_x lif gerilmesi (kesit üzerinde)", kisa: "σ_x", birim: "MPa", grup: "Gerilme", iki: true, lif: true },
    { ad: "von_mises", etiket: "von Mises eşdeğer gerilme", kisa: "σ_vM", birim: "MPa", grup: "Gerilme", iki: false },
    { ad: "tau_max", etiket: "τ_maks kayma gerilmesi", kisa: "τ_maks", birim: "MPa", grup: "Gerilme", iki: false },
    { ad: "kullanim", etiket: "Kullanım oranı (talep/kapasite)", kisa: "D/C", birim: "", grup: "Tasarım", iki: false },
  ];
  const BUYUKLUK = {};
  BUYUKLUKLER.forEach(function (b) { BUYUKLUK[b.ad] = b; });
  BUYUKLUK.vm_lif = { ad: "vm_lif", etiket: "von Mises (lif, τ_maks ile)", kisa: "σ_vM", birim: "MPa", iki: false, lif: true };
  const GECERSIZ = 3.0e38;
  const KOSE_BUTCESI = 450000;     // yapı görünümünde köşe sayısı üst sınırı (aşılırsa halkalar seyreltilir)

  /** Eleman kaydının k. istasyonundaki değeri (gösterim biriminde: yer değiştirme mm). Yoksa null. */
  function istasyonDegeri(el, ad, k) {
    if (ad === "u") {
      if (el.u_abs && el.u_abs[k] != null) return el.u_abs[k] * 1000;
      const u = el.u && el.u[k];
      return u ? Math.hypot(u[0], u[1], u[2]) * 1000 : null;
    }
    if (ad === "uX" || ad === "uY" || ad === "uZ") {
      const u = el.u && el.u[k];
      const v = u ? u["XYZ".indexOf(ad[1])] : null;
      return v == null ? null : v * 1000;
    }
    const d = el[ad];
    if (!d) return null;
    const v = d[k];
    return v == null || !isFinite(v) ? null : v;
  }

  /** Doğrusal elastik lif gerilmesi (MPa, çekme +): σ = N/A − Mz·y/Iz − My·z/Iy. */
  function lifGerilmesi(kesit, N, My, Mz, y, z) {
    const A = kesit.A || 1, Iy = kesit.Iy || 1, Iz = kesit.Iz || 1;
    return (N / A - Mz * y / Iz - My * z / Iy) / 1000;
  }
  /** Lif değeri: σ_x ya da von Mises √(σ² + 3τ_maks²) (τ istasyonun en büyük kayma gerilmesi; güvenli yanda). */
  function lifDegeri(el, k, y, z, vm) {
    const s = lifGerilmesi(el.kesit || {}, (el.N && el.N[k]) || 0, (el.My && el.My[k]) || 0, (el.Mz && el.Mz[k]) || 0, y, z);
    if (!vm) return s;
    const t = el.tau_max ? (el.tau_max[k] || 0) : 0;
    return Math.sqrt(s * s + 3 * t * t);
  }
  /** Tarafsız eksen σ(y, z) = 0: a·y + b·z = c (a = Mz/Iz, b = My/Iy, c = N/A). Eğilme yoksa null. */
  function tarafsizEksen(kesit, N, My, Mz) {
    const a = Mz / (kesit.Iz || 1), b = My / (kesit.Iy || 1), c = N / (kesit.A || 1);
    const olc = Math.max(Math.abs(c), 1e-9) * 1e-9;
    if (Math.abs(a) < olc && Math.abs(b) < olc) return null;
    if (Math.abs(a) < 1e-15 && Math.abs(b) < 1e-15) return null;
    return { a: a, b: b, c: c };
  }
  /** Doğru a·y + b·z = c'nin [y0, y1] × [z0, z1] kutusundaki parçası: [[y, z], [y, z]] ya da null. */
  function dogruKirp(d, y0, y1, z0, z1) {
    if (!d) return null;
    const p = [];
    function ekle(y, z) {
      if (y >= y0 - 1e-12 && y <= y1 + 1e-12 && z >= z0 - 1e-12 && z <= z1 + 1e-12) {
        for (let i = 0; i < p.length; i++) if (Math.abs(p[i][0] - y) + Math.abs(p[i][1] - z) < 1e-12) return;
        p.push([y, z]);
      }
    }
    if (Math.abs(d.b) > 1e-15) { ekle(y0, (d.c - d.a * y0) / d.b); ekle(y1, (d.c - d.a * y1) / d.b); }
    if (Math.abs(d.a) > 1e-15) { ekle((d.c - d.b * z0) / d.a, z0); ekle((d.c - d.b * z1) / d.a, z1); }
    return p.length >= 2 ? [p[0], p[1]] : null;
  }

  // =====================================================================================
  // 3. Renk ölçeği: kesikli 9 bant (mavi → camgöbeği → yeşil → sarı → kırmızı) / sürekli; iki yönlü (sıfır ortada)
  // =====================================================================================
  const PALET = {
    klasik: [[0, 0, 255], [0, 178, 255], [0, 255, 255], [0, 255, 178], [0, 255, 0], [178, 255, 0], [255, 255, 0], [255, 178, 0], [255, 0, 0]],
    iki: [[31, 86, 168], [52, 120, 205], [112, 160, 226], [174, 202, 238], [226, 226, 223], [242, 184, 176], [232, 131, 123], [216, 82, 78], [176, 44, 42]],
  };
  const BANT = 9;
  /** t ∈ [0, 1] → [r, g, b] (0–255). bantli: 9 eşit bant; değilse 9 durak arası doğrusal. */
  function renkAl(t, palet, bantli) {
    const p = PALET[palet] || PALET.klasik;
    if (!(t >= 0)) t = 0;
    if (t > 1) t = 1;
    if (bantli) return p[Math.min(BANT - 1, Math.floor(t * BANT))].slice();
    const s = t * (p.length - 1), i = Math.min(p.length - 2, Math.floor(s)), f = s - i;
    return [0, 1, 2].map(function (j) { return Math.round(p[i][j] + (p[i + 1][j] - p[i][j]) * f); });
  }
  function renkHex(c) { return "#" + c.map(function (v) { return (v < 16 ? "0" : "") + Math.max(0, Math.min(255, v | 0)).toString(16); }).join(""); }
  function degerRengi(v, lo, hi, palet, bantli) {
    if (v == null || !isFinite(v) || v >= GECERSIZ) return null;
    return renkAl(hi > lo ? (v - lo) / (hi - lo) : 0.5, palet, bantli);
  }
  /** Renk ölçeği aralığı: iki yönlüde ±max|v| (sıfır ortada); eşit uçlarda küçük açıklık. */
  function aralikBelirle(lo, hi, iki) {
    if (lo == null || hi == null || !isFinite(lo) || !isFinite(hi)) return [0, 1];
    if (iki) { const m = Math.max(Math.abs(lo), Math.abs(hi)) || 1; return [-m, m]; }
    if (hi - lo <= 1e-12 * Math.max(1, Math.abs(hi), Math.abs(lo))) {
      const d = Math.abs(hi) * 0.05 || 1;
      return [lo - d, hi + d];
    }
    return [lo, hi];
  }
  /** Lejant sınırları (yukarıdan aşağı: hi … lo), n bant → n + 1 değer. */
  function lejantSinirlari(lo, hi, n) {
    n = n || BANT;
    const out = [];
    for (let i = n; i >= 0; i--) out.push(lo + (hi - lo) * i / n);
    return out;
  }
  /** Renk dokusu verisi (RGBA Uint8): bantlıda 9 texel (NEAREST), süreklide 256 texel (LINEAR). */
  function dokuVerisi(palet, bantli) {
    const n = bantli ? BANT : 256, d = new Uint8Array(n * 4);
    for (let i = 0; i < n; i++) {
      const c = bantli ? (PALET[palet] || PALET.klasik)[i] : renkAl(i / (n - 1), palet, false);
      d[4 * i] = c[0]; d[4 * i + 1] = c[1]; d[4 * i + 2] = c[2]; d[4 * i + 3] = 255;
    }
    return d;
  }
  // Yük payı (döşemeden kirişe) bölgeleri için kategorik renkler (sabit sıra; komşu kirişler farklı)
  const KATEGORI = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"];

  // =====================================================================================
  // 4. Renk kimliği (picking)
  // =====================================================================================
  const PANEL_KIMLIK0 = 0x700000, RADYE_KIMLIK = 0x7f0000;
  function kimlikRenk(id) { return [id & 255, (id >> 8) & 255, (id >> 16) & 255]; }
  function renkKimlik(r, g, b) { return r + (g << 8) + (b << 16); }

  // =====================================================================================
  // 5. Kesit anahatları (yerel y′, z′ düzleminde, ağırlık merkezi başlangıçta) ve üçgenleme
  // =====================================================================================
  function isaretliAlan(p) {
    let s = 0;
    for (let i = 0; i < p.length; i++) { const a = p[i], b = p[(i + 1) % p.length]; s += a[0] * b[1] - b[0] * a[1]; }
    return s / 2;
  }
  function ccw(p) { return isaretliAlan(p) < 0 ? p.slice().reverse() : p; }
  function daire(r, n) {
    const out = [];
    for (let i = 0; i < n; i++) { const t = 2 * Math.PI * i / n; out.push([r * Math.cos(t), r * Math.sin(t)]); }
    return out;
  }
  function _pozitif(v, yedek) { return typeof v === "number" && isFinite(v) && v > 0 ? v : yedek; }

  /** Kesit kaydı (alan.py kesit_geometrisi) → {parcalar: [{dis: [[y, z]...] (CCW), ic: [[y, z]...]|null, puruzsuz}], dy, dz}.
      tup: true → yarıçapı tupR olan 6 kenarlı ince tüp. Bilinmeyen şekil → dy × dz dikdörtgen. */
  function kesitAnahat(k, tup, tupR) {
    k = k || {};
    if (tup) {
      const r = _pozitif(tupR, 0.05);
      return { parcalar: [{ dis: daire(r, 6), ic: null, puruzsuz: true }], dy: 2 * r, dz: 2 * r };
    }
    const sekil = k.sekil || "dikdortgen";
    const eksY = (k.eksen || "y") === "y";
    const dy = _pozitif(k.dy, _pozitif(k.h, 0.3)), dz = _pozitif(k.dz, _pozitif(k.b, 0.3));
    // (d: derinlik ekseni, g: genişlik ekseni) → (y, z)
    function yz(d, g) { return eksY ? [d, g] : [g, d]; }
    function cevir(liste) { return ccw(liste.map(function (q) { return yz(q[0], q[1]); })); }
    if (sekil === "I") {
      const h = _pozitif(k.h, dy), b = _pozitif(k.b, dz), tw = _pozitif(k.tw, h / 25), tf = _pozitif(k.tf, h / 16);
      const H = h / 2, Bb = b / 2, T = tw / 2;
      return {
        parcalar: [{ dis: cevir([[-H, -Bb], [-H, Bb], [-H + tf, Bb], [-H + tf, T], [H - tf, T], [H - tf, Bb], [H, Bb], [H, -Bb], [H - tf, -Bb], [H - tf, -T], [-H + tf, -T], [-H + tf, -Bb]]), ic: null, puruzsuz: false }],
        dy: dy, dz: dz,
      };
    }
    if (sekil === "kutu") {
      const h = _pozitif(k.h, dy), b = _pozitif(k.b, dz), t = Math.min(_pozitif(k.t, h / 20), Math.min(h, b) / 2.2);
      const dis = cevir([[-h / 2, -b / 2], [h / 2, -b / 2], [h / 2, b / 2], [-h / 2, b / 2]]);
      const ic = cevir([[-h / 2 + t, -b / 2 + t], [h / 2 - t, -b / 2 + t], [h / 2 - t, b / 2 - t], [-h / 2 + t, b / 2 - t]]);
      return { parcalar: [{ dis: dis, ic: ic, puruzsuz: false }], dy: dy, dz: dz };
    }
    if (sekil === "boru") {
      const D = _pozitif(k.D, Math.max(dy, dz)), t = Math.min(_pozitif(k.t, D / 20), D / 2.2);
      return { parcalar: [{ dis: daire(D / 2, 24), ic: daire(D / 2 - t, 24), puruzsuz: true }], dy: D, dz: D };
    }
    if (sekil === "L" || sekil === "2L") {
      const b = _pozitif(k.b, Math.max(dy, dz) / (sekil === "2L" ? 2 : 1)), t = Math.min(_pozitif(k.t, b / 10), b / 2.5);
      const c = (b * b + b * t - t * t) / (2 * (2 * b - t));       // ağırlık merkezinin dış köşeden uzaklığı
      if (sekil === "L") {
        const p = [[0, 0], [b, 0], [b, t], [t, t], [t, b], [0, b]].map(function (q) { return [q[0] - c, q[1] - c]; });
        return { parcalar: [{ dis: cevir(p), ic: null, puruzsuz: false }], dy: dy, dz: dz };
      }
      const s = _pozitif(k.s, 0.01) / 2;
      // sırt sırta iki korniyer: düşey kollar (d boyunca) ortada s aralıkla, yatay kollar dışa doğru, alt kenarda
      const sag = [[0, s], [0, s + b], [t, s + b], [t, s + t], [b, s + t], [b, s]].map(function (q) { return [q[0] - c, q[1]]; });
      const sol = sag.map(function (q) { return [q[0], -q[1]]; });
      return { parcalar: [{ dis: cevir(sag), ic: null, puruzsuz: false }, { dis: cevir(sol), ic: null, puruzsuz: false }], dy: dy, dz: dz };
    }
    if (sekil === "U") {
      const h = _pozitif(k.h, dy), b = _pozitif(k.b, dz), tw = _pozitif(k.tw, h / 25), tf = _pozitif(k.tf, h / 16);
      const A1 = 2 * b * tf, A2 = (h - 2 * tf) * tw;
      const gc = (A1 * b / 2 + A2 * tw / 2) / (A1 + A2);
      const p = [[-h / 2, 0], [-h / 2, b], [-h / 2 + tf, b], [-h / 2 + tf, tw], [h / 2 - tf, tw], [h / 2 - tf, b], [h / 2, b], [h / 2, 0]]
        .map(function (q) { return [q[0], q[1] - gc]; });
      return { parcalar: [{ dis: cevir(p), ic: null, puruzsuz: false }], dy: dy, dz: dz };
    }
    return { parcalar: [{ dis: ccw([[-dy / 2, -dz / 2], [dy / 2, -dz / 2], [dy / 2, dz / 2], [-dy / 2, dz / 2]]), ic: null, puruzsuz: false }], dy: dy, dz: dz };
  }

  /** Basit çokgen (CCW) kulak kırpma üçgenlemesi → [i, j, k, ...]. */
  function ucgenle(p) {
    const n = p.length, out = [];
    if (n < 3) return out;
    const idx = [];
    for (let i = 0; i < n; i++) idx.push(i);
    function cap(o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }
    function icinde(q, a, b, c) {
      const d1 = cap(a, b, q), d2 = cap(b, c, q), d3 = cap(c, a, q);
      return d1 >= -1e-15 && d2 >= -1e-15 && d3 >= -1e-15;
    }
    let guv = 0;
    while (idx.length > 3 && guv++ < 10000) {
      let kesildi = false;
      for (let i = 0; i < idx.length; i++) {
        const ia = idx[(i + idx.length - 1) % idx.length], ib = idx[i], ic = idx[(i + 1) % idx.length];
        const a = p[ia], b = p[ib], c = p[ic];
        if (cap(a, b, c) <= 1e-15) continue;            // içbükey köşe
        let bos = true;
        for (let j = 0; j < idx.length; j++) {
          const q = idx[j];
          if (q === ia || q === ib || q === ic) continue;
          if (icinde(p[q], a, b, c)) { bos = false; break; }
        }
        if (!bos) continue;
        out.push(ia, ib, ic);
        idx.splice(i, 1);
        kesildi = true;
        break;
      }
      if (!kesildi) break;                               // dejenere: kalanı yelpaze
    }
    for (let i = 1; i + 1 < idx.length; i++) out.push(idx[0], idx[i], idx[i + 1]);
    return out;
  }
  function cokgenIcinde(q, p) {
    let ic = false;
    for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
      const a = p[i], b = p[j];
      if ((a[1] > q[1]) !== (b[1] > q[1]) && q[0] < (b[0] - a[0]) * (q[1] - a[1]) / (b[1] - a[1]) + a[0]) ic = !ic;
    }
    return ic;
  }
  /** Kesitin en büyük çekme ve basınç lifi (anahat köşelerinde; doğrusal alan köşede uç değer alır). */
  function kesitUcLifleri(an, kesit, N, My, Mz) {
    let mx = null, mn = null;
    an.parcalar.forEach(function (pr) {
      pr.dis.forEach(function (q) {
        const s = lifGerilmesi(kesit, N, My, Mz, q[0], q[1]);
        if (!mx || s > mx.s) mx = { y: q[0], z: q[1], s: s };
        if (!mn || s < mn.s) mn = { y: q[0], z: q[1], s: s };
      });
    });
    return { cekme: mx, basinc: mn };
  }

  // =====================================================================================
  // 6. Ağ kurma: çubuklar (kesit ekstrüzyonu, istasyonlarda halka), döşeme plakları, radye
  // =====================================================================================
  function _anahatAnahtari(k, tup, tupR) {
    if (tup) return "tup:" + (tupR || 0).toFixed(5);
    k = k || {};
    return [k.sekil, k.eksen, k.dy, k.dz, k.h, k.b, k.tw, k.tf, k.t, k.D, k.s].join("|");
  }
  function _halkaNormalleri(pts, puruzsuz, ic) {
    const n = pts.length, ken = [];
    for (let p = 0; p < n; p++) {
      const a = pts[p], b = pts[(p + 1) % n];
      let ny = b[1] - a[1], nz = -(b[0] - a[0]);
      const l = Math.hypot(ny, nz) || 1;
      ny /= l; nz /= l;
      if (ic) { ny = -ny; nz = -nz; }
      ken.push([ny, nz]);
    }
    if (!puruzsuz) return ken;
    const kos = [];
    for (let p = 0; p < n; p++) {
      const a = ken[(p + n - 1) % n], b = ken[p];
      const y = a[0] + b[0], z = a[1] + b[1], l = Math.hypot(y, z) || 1;
      kos.push([y / l, z / l]);
    }
    return kos;
  }
  /** Bir anahatın istasyon başına köşe ve üçgen sayısı (bellek önceden ayrılır). */
  /** Kenarları m eşit parçaya bölünmüş halka (yan yüzlerde lif gerilmesi y·M(x) çarpımı üçgenlerde dişli görünmesin). */
  function halkaIncelt(pts, m) {
    if (!(m > 1)) return pts;
    const out = [];
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      for (let j = 0; j < m; j++) out.push([a[0] + (b[0] - a[0]) * j / m, a[1] + (b[1] - a[1]) * j / m]);
    }
    return out;
  }
  /** Yan yüz halkaları: puruzsuz olmayan parçalarda kenarlar bol parçaya bölünür; kapaklar özgün anahatla. */
  function yanHalkalari(an, bol) {
    return an.parcalar.map(function (pr) {
      const m = pr.puruzsuz ? 1 : bol;
      return { dis: halkaIncelt(pr.dis, m), ic: pr.ic ? halkaIncelt(pr.ic, m) : null, puruzsuz: pr.puruzsuz };
    });
  }
  function anahatSayilari(an) {
    let kose = 0, ucg = 0, kapakK = 0, kapakU = 0;
    (an.yan || an.parcalar).forEach(function (pr) {
      const halkalar = pr.ic ? [pr.dis, pr.ic] : [pr.dis];
      halkalar.forEach(function (h) { kose += pr.puruzsuz ? h.length : 2 * h.length; ucg += 2 * h.length; });
    });
    an.parcalar.forEach(function (pr) {
      if (pr.ic) { kapakK += 2 * pr.dis.length; kapakU += 2 * pr.dis.length; }
      else { kapakK += pr.dis.length; kapakU += pr.dis.length - 2; }
    });
    return { kose: kose, ucgen: ucg, kapakKose: kapakK, kapakUcgen: kapakU };
  }

  /** Çubuk ağları (tek tampon): elemanlar → {P, D (Float32 xyz), Nr (Int8 xyz0), K (Uint8 rgba kimlik), vEl (Uint32),
      vSt (Uint16), vYZ (Float32), I (Uint32), araliklar: [{bas, say}], anahatlar: [an], kose, ucgen}.
      secenek: {tup, tupR(el) → yarıçap, liste: [eleman sırası] (yalnız bunlar), kimlik0 (varsayılan 1),
      seyrek (≥ 1: her seyrek'inci istasyonda halka; uçlar her zaman — çok büyük modelde köşe sayısını azaltır),
      bol (≥ 1: yan yüz kenarlarını böl — eleman görünümünde lif gerilmesi bantları düzgün)}. */
  function istasyonSecimi(ns, seyrek) {
    const out = [];
    const a = Math.max(1, seyrek | 0);
    for (let k = 0; k < ns; k += a) out.push(k);
    if (out[out.length - 1] !== ns - 1) out.push(ns - 1);
    return out;
  }
  function cubukAgi(elemanlar, secenek) {
    secenek = secenek || {};
    const seyrek = Math.max(1, secenek.seyrek | 0 || 1), bol = Math.max(1, secenek.bol | 0 || 1);
    const liste = secenek.liste || elemanlar.map(function (_, i) { return i; });
    const onbellek = {};
    const an = [], say = [];
    let topK = 0, topI = 0;
    liste.forEach(function (ei) {
      const e = elemanlar[ei];
      const r = secenek.tup ? (secenek.tupR ? secenek.tupR(e) : 0.05) : 0;
      const ah = _anahatAnahtari(e.kesit, secenek.tup, r);
      if (!onbellek[ah]) {
        const a = kesitAnahat(e.kesit, secenek.tup, r);
        a.yan = yanHalkalari(a, bol);
        a.sayi = anahatSayilari(a);
        a.kapakUcgen = a.parcalar.map(function (pr) { return pr.ic ? null : ucgenle(pr.dis); });
        a.normal = a.yan.map(function (pr) {
          return { dis: _halkaNormalleri(pr.dis, pr.puruzsuz, false), ic: pr.ic ? _halkaNormalleri(pr.ic, pr.puruzsuz, true) : null };
        });
        onbellek[ah] = a;
      }
      const a = onbellek[ah];
      const ns = (e.x || []).length >= 2 ? istasyonSecimi(e.x.length, seyrek).length : 0;
      an.push(a);
      const k = ns >= 2 ? a.sayi.kose * ns + 2 * a.sayi.kapakKose : 0;
      const u = ns >= 2 ? 3 * (a.sayi.ucgen * (ns - 1) + 2 * a.sayi.kapakUcgen) : 0;
      say.push([k, u]);
      topK += k; topI += u;
    });
    const P = new Float32Array(3 * topK), D = new Float32Array(3 * topK), Nr = new Int8Array(4 * topK), K = new Uint8Array(4 * topK);
    const vEl = new Uint32Array(topK), vSt = new Uint16Array(topK), vYZ = new Float32Array(2 * topK), I = new Uint32Array(topI);
    const araliklar = new Array(elemanlar.length);
    let v = 0, ii = 0;
    const kimlik0 = secenek.kimlik0 == null ? 1 : secenek.kimlik0;
    liste.forEach(function (ei, li) {
      const e = elemanlar[ei], a = an[li], xs = e.x || [];
      const ibas = ii;
      if (xs.length < 2) { araliklar[ei] = { bas: ibas, say: 0 }; return; }
      const ist = istasyonSecimi(xs.length, seyrek), ns = ist.length;
      const ex = e.yerel.x, ey = e.yerel.y, ez = e.yerel.z, I0 = e.i, U = e.u || [];
      const kc = kimlikRenk(kimlik0 + ei);
      function koy(kk, y, z, n0, n1, n2) {
        const k = ist[kk], xk = xs[k];
        const o = 3 * v;
        P[o] = I0[0] + xk * ex[0] + y * ey[0] + z * ez[0];
        P[o + 1] = I0[1] + xk * ex[1] + y * ey[1] + z * ez[1];
        P[o + 2] = I0[2] + xk * ex[2] + y * ey[2] + z * ez[2];
        const u = U[k];
        if (u) { D[o] = u[0] || 0; D[o + 1] = u[1] || 0; D[o + 2] = u[2] || 0; }
        const q = 4 * v;
        Nr[q] = Math.round(127 * n0); Nr[q + 1] = Math.round(127 * n1); Nr[q + 2] = Math.round(127 * n2);
        K[q] = kc[0]; K[q + 1] = kc[1]; K[q + 2] = kc[2]; K[q + 3] = 255;
        vEl[v] = ei; vSt[v] = k; vYZ[2 * v] = y; vYZ[2 * v + 1] = z;
        return v++;
      }
      a.parcalar.forEach(function (pr, pi) {
        const yan = a.yan[pi];
        const halkalar = yan.ic ? [[yan.dis, a.normal[pi].dis], [yan.ic, a.normal[pi].ic]] : [[yan.dis, a.normal[pi].dis]];
        halkalar.forEach(function (hn) {
          const pts = hn[0], nor = hn[1], n = pts.length, taban = v;
          for (let k = 0; k < ns; k++) {
            for (let p = 0; p < n; p++) {
              const q0 = pts[p];
              if (pr.puruzsuz) {
                const nn = nor[p];
                koy(k, q0[0], q0[1], nn[0] * ey[0] + nn[1] * ez[0], nn[0] * ey[1] + nn[1] * ez[1], nn[0] * ey[2] + nn[1] * ez[2]);
              } else {
                const q1 = pts[(p + 1) % n], nn = nor[p];
                const n0 = nn[0] * ey[0] + nn[1] * ez[0], n1 = nn[0] * ey[1] + nn[1] * ez[1], n2 = nn[0] * ey[2] + nn[1] * ez[2];
                koy(k, q0[0], q0[1], n0, n1, n2);
                koy(k, q1[0], q1[1], n0, n1, n2);
              }
            }
          }
          const adim = pr.puruzsuz ? n : 2 * n;
          for (let k = 0; k + 1 < ns; k++) {
            for (let p = 0; p < n; p++) {
              let A, B;
              if (pr.puruzsuz) { A = taban + k * adim + p; B = taban + k * adim + (p + 1) % n; }
              else { A = taban + k * adim + 2 * p; B = A + 1; }
              const C = A + adim, Dd = B + adim;
              I[ii++] = A; I[ii++] = B; I[ii++] = Dd;
              I[ii++] = A; I[ii++] = Dd; I[ii++] = C;
            }
          }
        });
        // uç kapakları (x = 0 ve x = L)
        [0, ns - 1].forEach(function (k) {
          const sg = k === 0 ? -1 : 1;
          const n0 = sg * ex[0], n1 = sg * ex[1], n2 = sg * ex[2];
          const taban = v, n = pr.dis.length;
          pr.dis.forEach(function (q) { koy(k, q[0], q[1], n0, n1, n2); });
          if (pr.ic) {
            pr.ic.forEach(function (q) { koy(k, q[0], q[1], n0, n1, n2); });
            for (let p = 0; p < n; p++) {
              const A = taban + p, B = taban + (p + 1) % n, C = taban + n + p, Dd = taban + n + (p + 1) % n;
              I[ii++] = A; I[ii++] = B; I[ii++] = Dd; I[ii++] = A; I[ii++] = Dd; I[ii++] = C;
            }
          } else {
            const t = a.kapakUcgen[pi];
            for (let j = 0; j < t.length; j++) I[ii++] = taban + t[j];
          }
        });
      });
      araliklar[ei] = { bas: ibas, say: ii - ibas };
    });
    return { P: P, D: D, Nr: Nr, K: K, vEl: vEl, vSt: vSt, vYZ: vYZ, I: I, araliklar: araliklar, anahatlar: an, kose: topK, ucgen: topI / 3 };
  }

  /** Çubuk ağı köşe değerleri: büyüklük `ad` (istasyon ya da lif) → V (Float32, geçersiz = GECERSIZ). */
  function degerleriDoldur(ag, elemanlar, ad, V) {
    const b = BUYUKLUK[ad] || {};
    const n = ag.vEl.length;
    if (b.lif) {
      const vm = ad === "vm_lif";
      for (let v = 0; v < n; v++) {
        const e = elemanlar[ag.vEl[v]];
        const s = lifDegeri(e, ag.vSt[v], ag.vYZ[2 * v], ag.vYZ[2 * v + 1], vm);
        V[v] = isFinite(s) ? s : GECERSIZ;
      }
      return V;
    }
    const tab = istasyonTablosu(elemanlar, ad);
    for (let v = 0; v < n; v++) {
      const x = tab[ag.vEl[v]][ag.vSt[v]];
      V[v] = x == null || !isFinite(x) ? GECERSIZ : x;
    }
    return V;
  }
  /** Her eleman için istasyon değerleri dizisi (gösterim biriminde; yoksa null öğeler). */
  function istasyonTablosu(elemanlar, ad) {
    return elemanlar.map(function (e) {
      const ns = (e.x || []).length, a = new Array(ns);
      for (let k = 0; k < ns; k++) a[k] = istasyonDegeri(e, ad, k);
      return a;
    });
  }
  /** Görünür elemanlar üzerinde en küçük/en büyük: {min: {deger, el, k}, max: {...}} (lif büyüklüğünde anahat köşelerinde). */
  function ekstremumBul(elemanlar, ad, gorunur, anahatlar) {
    const b = BUYUKLUK[ad] || {};
    let mn = null, mx = null;
    for (let ei = 0; ei < elemanlar.length; ei++) {
      if (gorunur && !gorunur[ei]) continue;
      const e = elemanlar[ei], ns = (e.x || []).length;
      for (let k = 0; k < ns; k++) {
        if (b.lif) {
          const an = anahatlar && anahatlar[ei];
          if (!an) continue;
          for (let p = 0; p < an.parcalar.length; p++) {
            const pts = an.parcalar[p].dis;
            for (let q = 0; q < pts.length; q++) {
              const s = lifDegeri(e, k, pts[q][0], pts[q][1], ad === "vm_lif");
              if (!isFinite(s)) continue;
              if (!mx || s > mx.deger) mx = { deger: s, el: ei, k: k, y: pts[q][0], z: pts[q][1] };
              if (!mn || s < mn.deger) mn = { deger: s, el: ei, k: k, y: pts[q][0], z: pts[q][1] };
            }
          }
        } else {
          const s = istasyonDegeri(e, ad, k);
          if (s == null || !isFinite(s)) continue;
          if (!mx || s > mx.deger) mx = { deger: s, el: ei, k: k };
          if (!mn || s < mn.deger) mn = { deger: s, el: ei, k: k };
        }
      }
    }
    return { min: mn, max: mx };
  }

  /** Döşeme plağı ızgara ağı (nx × ny): köşe ötelemeleri çift doğrusal + plak sehimi (−w, aşağı). */
  function plakAgi(panel, koseU, kimlik) {
    const g = panel.izgara, nx = g.nx, ny = g.ny, z = panel.z;
    const n = nx * ny;
    const P = new Float32Array(3 * n), D = new Float32Array(3 * n), Nr = new Int8Array(4 * n), K = new Uint8Array(4 * n);
    const kc = kimlikRenk(kimlik);
    const x0 = g.x[0], x1 = g.x[nx - 1], y0 = g.y[0], y1 = g.y[ny - 1];
    const cu = koseU || [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const v = j * nx + i, o = 3 * v;
        P[o] = g.x[i]; P[o + 1] = g.y[j]; P[o + 2] = z;
        const s = x1 > x0 ? (g.x[i] - x0) / (x1 - x0) : 0, t = y1 > y0 ? (g.y[j] - y0) / (y1 - y0) : 0;
        for (let c = 0; c < 3; c++) {
          D[o + c] = (1 - s) * (1 - t) * cu[0][c] + s * (1 - t) * cu[1][c] + s * t * cu[2][c] + (1 - s) * t * cu[3][c];
        }
        const w = g.w && g.w[j] ? g.w[j][i] : 0;
        D[o + 2] -= w || 0;
        Nr[4 * v + 2] = 127;
        K[4 * v] = kc[0]; K[4 * v + 1] = kc[1]; K[4 * v + 2] = kc[2]; K[4 * v + 3] = 255;
      }
    }
    const I = new Uint32Array(6 * (nx - 1) * (ny - 1));
    let ii = 0;
    for (let j = 0; j + 1 < ny; j++) {
      for (let i = 0; i + 1 < nx; i++) {
        const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1;
        I[ii++] = a; I[ii++] = b; I[ii++] = d; I[ii++] = a; I[ii++] = d; I[ii++] = c;
      }
    }
    return { P: P, D: D, Nr: Nr, K: K, I: I, kose: n };
  }
  function plakDegeri(panel, ad, i, j) {
    const g = panel.izgara;
    if (ad === "w") return g.w && g.w[j] && g.w[j][i] != null ? g.w[j][i] * 1000 : null;
    const d = g[ad];
    return d && d[j] && d[j][i] != null ? d[j][i] : null;
  }
  /** Radye ızgarası: tanımlı dört köşeli hücreler; değer p (kN/m²) ya da w (mm). */
  function radyeAgi(radye, kimlik) {
    const nx = radye.x.length, ny = radye.y.length, n = nx * ny;
    const P = new Float32Array(3 * n), D = new Float32Array(3 * n), Nr = new Int8Array(4 * n), K = new Uint8Array(4 * n);
    const kc = kimlikRenk(kimlik);
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const v = j * nx + i, o = 3 * v;
        P[o] = radye.x[i]; P[o + 1] = radye.y[j]; P[o + 2] = radye.z || 0;
        const w = radye.w[j][i];
        D[o + 2] = w == null ? 0 : -w;
        Nr[4 * v + 2] = 127;
        K[4 * v] = kc[0]; K[4 * v + 1] = kc[1]; K[4 * v + 2] = kc[2]; K[4 * v + 3] = 255;
      }
    }
    const idx = [];
    for (let j = 0; j + 1 < ny; j++) {
      for (let i = 0; i + 1 < nx; i++) {
        const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1;
        if ([a, b, c, d].some(function (q) { return radye.w[Math.floor(q / nx)][q % nx] == null; })) continue;
        idx.push(a, b, d, a, d, c);
      }
    }
    return { P: P, D: D, Nr: Nr, K: K, I: new Uint32Array(idx), kose: n };
  }

  // =====================================================================================
  // 7. Kamera ve matrisler (sütun düzenli 4×4)
  // =====================================================================================
  function m4Carp(a, b) {
    const o = new Float32Array(16);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k];
      o[i * 4 + j] = s;
    }
    return o;
  }
  function v3Fark(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function v3Dis(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function v3Ic(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function v3Bir(a) { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }

  /** Kamera {hedef, uzak, yaw, pitch (radyan), fov, orto, R (sahne yarıçapı)} → {mvp, goz, sag, yukari, ileri, yariY, yariX}. */
  function kameraMatrisi(kam, en, boy) {
    const cp = Math.cos(kam.pitch), sp = Math.sin(kam.pitch), cy = Math.cos(kam.yaw), sy = Math.sin(kam.yaw);
    const d = [cp * cy, cp * sy, sp];
    const goz = [kam.hedef[0] + kam.uzak * d[0], kam.hedef[1] + kam.uzak * d[1], kam.hedef[2] + kam.uzak * d[2]];
    const ileri = [-d[0], -d[1], -d[2]];
    const sag = [-sy, cy, 0];
    const yukari = v3Dis(sag, ileri);
    const V = new Float32Array([sag[0], yukari[0], -ileri[0], 0, sag[1], yukari[1], -ileri[1], 0, sag[2], yukari[2], -ileri[2], 0,
      -v3Ic(sag, goz), -v3Ic(yukari, goz), v3Ic(ileri, goz), 1]);
    const R = kam.R || 10;
    const yak = Math.max(kam.uzak - 6 * R, kam.uzak * 0.002, 1e-3), uzak = kam.uzak + 6 * R;
    const asp = en / Math.max(1, boy);
    const yariY = kam.uzak * Math.tan(kam.fov / 2), yariX = yariY * asp;
    let Pm;
    if (kam.orto) {
      const n = kam.uzak - 6 * R;                         // dik izdüşümde yakın düzlem gözün arkasında olabilir
      Pm = new Float32Array([1 / yariX, 0, 0, 0, 0, 1 / yariY, 0, 0, 0, 0, -2 / (uzak - n), 0, 0, 0, -(uzak + n) / (uzak - n), 1]);
    } else {
      const f = 1 / Math.tan(kam.fov / 2);
      Pm = new Float32Array([f / asp, 0, 0, 0, 0, f, 0, 0, 0, 0, (uzak + yak) / (yak - uzak), -1, 0, 0, 2 * uzak * yak / (yak - uzak), 0]);
    }
    return { mvp: m4Carp(Pm, V), goz: goz, sag: sag, yukari: yukari, ileri: ileri, yariY: yariY, yariX: yariX };
  }
  /** Dünya noktası → ekran (piksel, sol üst başlangıç) ve derinlik; kameranın arkasındaysa null. */
  function izdusur(km, p, en, boy) {
    const m = km.mvp;
    const x = m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12];
    const y = m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13];
    const z = m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14];
    const w = m[3] * p[0] + m[7] * p[1] + m[11] * p[2] + m[15];
    if (w <= 1e-9) return null;
    return [(x / w * 0.5 + 0.5) * en, (1 - (y / w * 0.5 + 0.5)) * boy, z / w];
  }
  const STANDART = {
    "3b": { yaw: -55 * Math.PI / 180, pitch: 24 * Math.PI / 180, orto: false },
    plan: { yaw: -Math.PI / 2, pitch: Math.PI / 2 - 1e-4, orto: true },
    on: { yaw: -Math.PI / 2, pitch: 0, orto: true },
    yan: { yaw: 0, pitch: 0, orto: true },
  };
  /** Kutu (min, max) → hedef ve uzaklık (sığdır): kutunun 8 köşesi kamera sağ/yukarı eksenlerine izdüşürülür,
      en-boy oranı (kam.asp) hesaba katılır; perspektifte derinlik payı eklenir. */
  function sigdir(kam, kmin, kmax) {
    const c = [(kmin[0] + kmax[0]) / 2, (kmin[1] + kmax[1]) / 2, (kmin[2] + kmax[2]) / 2];
    const R = Math.max(1e-3, Math.hypot(kmax[0] - kmin[0], kmax[1] - kmin[1], kmax[2] - kmin[2]) / 2);
    kam.hedef = c;
    kam.R = R;
    const km = kameraMatrisi(Object.assign({}, kam, { uzak: 1, hedef: c }), 1, 1);
    let hx = 0, hy = 0, hz = 0;
    for (let i = 0; i < 8; i++) {
      const q = [i & 1 ? kmax[0] : kmin[0], i & 2 ? kmax[1] : kmin[1], i & 4 ? kmax[2] : kmin[2]];
      const d = v3Fark(q, c);
      hx = Math.max(hx, Math.abs(v3Ic(d, km.sag))); hy = Math.max(hy, Math.abs(v3Ic(d, km.yukari))); hz = Math.max(hz, Math.abs(v3Ic(d, km.ileri)));
    }
    const asp = kam.asp || 1.6;
    const yariY = Math.max(hy, hx / asp, R * 0.05) * 1.12;
    kam.uzak = yariY / Math.tan(kam.fov / 2) + (kam.orto ? 0 : hz);
    return kam;
  }
  function kutuHesapla(elemanlar, gorunur) {
    const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    elemanlar.forEach(function (e, i) {
      if (gorunur && !gorunur[i]) return;
      [e.i, e.j].forEach(function (p) { for (let c = 0; c < 3; c++) { mn[c] = Math.min(mn[c], p[c]); mx[c] = Math.max(mx[c], p[c]); } });
    });
    if (!isFinite(mn[0])) return [[0, 0, 0], [1, 1, 1]];
    return [mn, mx];
  }

  // =====================================================================================
  // 8. Süzgeçler: kat ve aks
  // =====================================================================================
  function katListesi(alan, bina) {
    const var_ = {};
    (alan.elemanlar || []).forEach(function (e) { if (e.kat != null) var_[e.kat] = true; });
    const adlar = {};
    ((bina && bina.katlar) || []).forEach(function (k) { adlar[k.no] = k.ad; });
    return Object.keys(var_).map(Number).sort(function (a, b) { return a - b; }).map(function (k) {
      return { no: k, ad: adlar[k] ? k + " — " + adlar[k] : "Kat " + k };
    });
  }
  function aksListesi(alan, bina) {
    const out = [];
    const ak = bina && bina.akslar;
    if (ak && (ak.x || ak.y)) {
      (ak.x || []).forEach(function (a) { if (typeof a.konum === "number") out.push({ yon: "x", ad: String(a.ad), konum: a.konum }); });
      (ak.y || []).forEach(function (a) { if (typeof a.konum === "number") out.push({ yon: "y", ad: String(a.ad), konum: a.konum }); });
      return out;
    }
    const xs = {}, ys = {};
    (alan.dugumler || []).forEach(function (d) { xs[d.X.toFixed(3)] = d.X; ys[d.Y.toFixed(3)] = d.Y; });
    Object.keys(xs).map(function (k) { return xs[k]; }).sort(function (a, b) { return a - b; })
      .forEach(function (x, i) { out.push({ yon: "x", ad: "X" + (i + 1) + " (" + fmt(x, 4) + " m)", konum: x }); });
    Object.keys(ys).map(function (k) { return ys[k]; }).sort(function (a, b) { return a - b; })
      .forEach(function (y, i) { out.push({ yon: "y", ad: "Y" + (i + 1) + " (" + fmt(y, 4) + " m)", konum: y }); });
    return out;
  }
  function aksUstunde(e, aks) {
    const c = aks.yon === "x" ? 0 : 1;
    return Math.abs(e.i[c] - aks.konum) < 1e-3 && Math.abs(e.j[c] - aks.konum) < 1e-3;
  }

  // =====================================================================================
  // 9. WebGL çizici
  // =====================================================================================
  const VS_ANA = "attribute vec3 aP; attribute vec3 aD; attribute vec3 aN; attribute float aV; attribute float aX;\n" +
    "uniform mat4 uM; uniform float uS; uniform vec3 uL;\n" +
    "varying float vV; varying float vI; varying float vX;\n" +
    "void main(){ gl_Position = uM * vec4(aP + uS * aD, 1.0);\n" +
    "  float l = length(aN);\n" +
    "  vI = l > 0.0 ? 0.42 + 0.58 * abs(dot(aN / l, uL)) : 1.0; vV = aV; vX = aX; }";
  const FS_ANA = "#ifdef GL_FRAGMENT_PRECISION_HIGH\nprecision highp float;\n#else\nprecision mediump float;\n#endif\n" +
    "varying float vV; varying float vI; varying float vX;\n" +
    "uniform sampler2D uT; uniform float uA; uniform float uB; uniform float uKes; uniform vec3 uG; uniform float uO;\n" +
    "void main(){ if (vX > uKes) discard; vec3 c;\n" +
    "  if (vV > 1.0e37) c = uG; else { float t = uB > uA ? clamp((vV - uA) / (uB - uA), 0.0, 1.0) : 0.5;\n" +
    "    c = texture2D(uT, vec2(t * 0.9990 + 0.0005, 0.5)).rgb; }\n" +
    "  gl_FragColor = vec4(c * vI, uO); }";
  const VS_SEC = "attribute vec3 aP; attribute vec3 aD; attribute vec4 aK; attribute float aX;\n" +
    "uniform mat4 uM; uniform float uS; varying vec4 vK; varying float vX;\n" +
    "void main(){ gl_Position = uM * vec4(aP + uS * aD, 1.0); vK = aK; vX = aX; }";
  const FS_SEC = "precision mediump float; varying vec4 vK; varying float vX; uniform float uKes;\n" +
    "void main(){ if (vX > uKes) discard; gl_FragColor = vec4(vK.rgb, 1.0); }";
  const VS_CIZ = "attribute vec3 aP; attribute vec3 aD; uniform mat4 uM; uniform float uS;\n" +
    "void main(){ gl_Position = uM * vec4(aP + uS * aD, 1.0); }";
  const FS_CIZ = "precision mediump float; uniform vec4 uR; void main(){ gl_FragColor = uR; }";

  function Cizici(tuval) {
    const ozel = { antialias: true, alpha: false, preserveDrawingBuffer: false, premultipliedAlpha: false };
    let gl = null, s2 = false;
    try { gl = tuval.getContext("webgl2", ozel); s2 = !!gl; } catch (e) { gl = null; }
    if (!gl) { try { gl = tuval.getContext("webgl", ozel) || tuval.getContext("experimental-webgl", ozel); } catch (e) { gl = null; } }
    if (!gl) throw new Error("WebGL yok");
    if (!s2 && !gl.getExtension("OES_element_index_uint")) throw new Error("WebGL: 32 bit indis yok");
    this.gl = gl;
    this.surum = s2 ? 2 : 1;
    function derle(vs, fs) {
      function sh(t, k) {
        const s = gl.createShader(t);
        gl.shaderSource(s, k);
        gl.compileShader(s);
        if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error("Gölgelendirici: " + gl.getShaderInfoLog(s));
        return s;
      }
      const p = gl.createProgram();
      gl.attachShader(p, sh(gl.VERTEX_SHADER, vs));
      gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs));
      gl.bindAttribLocation(p, 0, "aP");
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error("Program: " + gl.getProgramInfoLog(p));
      const kon = { p: p, a: {}, u: {} };
      ["aP", "aD", "aN", "aV", "aX", "aK"].forEach(function (a) { kon.a[a] = gl.getAttribLocation(p, a); });
      ["uM", "uS", "uL", "uT", "uA", "uB", "uKes", "uG", "uO", "uR"].forEach(function (u) { kon.u[u] = gl.getUniformLocation(p, u); });
      return kon;
    }
    this.ana = derle(VS_ANA, FS_ANA);
    this.sec = derle(VS_SEC, FS_SEC);
    this.ciz = derle(VS_CIZ, FS_CIZ);
    this.doku = gl.createTexture();
    this.secimFbo = null;
    this.paletAyarla("klasik", true);
  }
  Cizici.prototype.paletAyarla = function (palet, bantli) {
    const gl = this.gl;
    const anahtar = palet + (bantli ? "|b" : "|s");
    if (this._palet === anahtar) return;
    this._palet = anahtar;
    gl.bindTexture(gl.TEXTURE_2D, this.doku);
    const d = dokuVerisi(palet, bantli);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, d.length / 4, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, d);
    const f = bantli ? gl.NEAREST : gl.LINEAR;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, f);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  };
  /** Ağ → GPU nesnesi {bP, bD, bN, bK, bV, bX?, bI, sayI}. */
  Cizici.prototype.nesne = function (ag, xDizisi) {
    const gl = this.gl;
    function tampon(veri, tur) { const b = gl.createBuffer(); gl.bindBuffer(tur || gl.ARRAY_BUFFER, b); gl.bufferData(tur || gl.ARRAY_BUFFER, veri, gl.STATIC_DRAW); return b; }
    const n = {
      bP: tampon(ag.P), bD: tampon(ag.D), bN: tampon(ag.Nr), bK: tampon(ag.K),
      bV: gl.createBuffer(), bX: xDizisi ? tampon(xDizisi) : null, bI: tampon(ag.I, gl.ELEMENT_ARRAY_BUFFER), sayI: ag.I.length, kose: ag.kose,
    };
    gl.bindBuffer(gl.ARRAY_BUFFER, n.bV);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(ag.kose), gl.DYNAMIC_DRAW);
    return n;
  };
  Cizici.prototype.degerYukle = function (n, V) { const gl = this.gl; gl.bindBuffer(gl.ARRAY_BUFFER, n.bV); gl.bufferData(gl.ARRAY_BUFFER, V, gl.DYNAMIC_DRAW); };
  Cizici.prototype.indisYukle = function (n, I) { const gl = this.gl; gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, n.bI); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, I, gl.DYNAMIC_DRAW); n.sayI = I.length; };
  /** Renk ölçekli çizgiler (hafif kip: deforme eksen çizgileri, istasyon değerleriyle). */
  Cizici.prototype.degerliCizgi = function (n, o) {
    const gl = this.gl, pr = this.ana;
    if (!n || !n.say) return;
    gl.useProgram(pr.p);
    this._temizle();
    this._oznitelik(pr, "aP", n.bP, 3, gl.FLOAT);
    this._oznitelik(pr, "aD", n.bD, 3, gl.FLOAT);
    this._oznitelik(pr, "aV", n.bV, 1, gl.FLOAT);
    if (pr.a.aN >= 0) gl.vertexAttrib3f(pr.a.aN, 0, 0, 0);
    if (pr.a.aX >= 0) gl.vertexAttrib1f(pr.a.aX, 0);
    gl.uniformMatrix4fv(pr.u.uM, false, o.mvp);
    gl.uniform1f(pr.u.uS, o.olcek);
    gl.uniform3fv(pr.u.uL, [0, 0, 1]);
    gl.uniform1f(pr.u.uA, o.lo);
    gl.uniform1f(pr.u.uB, o.hi);
    gl.uniform1f(pr.u.uKes, 1e30);
    gl.uniform3fv(pr.u.uG, o.gri || [0.6, 0.6, 0.6]);
    gl.uniform1f(pr.u.uO, 1);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.doku);
    gl.uniform1i(pr.u.uT, 0);
    gl.drawArrays(gl.LINES, 0, n.say);
  };
  Cizici.prototype.cizgiNesnesi = function (P, D) {
    const gl = this.gl;
    const n = { bP: gl.createBuffer(), bD: gl.createBuffer(), say: P.length / 3 };
    gl.bindBuffer(gl.ARRAY_BUFFER, n.bP); gl.bufferData(gl.ARRAY_BUFFER, P, gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER, n.bD); gl.bufferData(gl.ARRAY_BUFFER, D, gl.DYNAMIC_DRAW);
    return n;
  };
  Cizici.prototype.sil = function (n) {
    if (!n) return;
    const gl = this.gl;
    ["bP", "bD", "bN", "bK", "bV", "bX", "bI"].forEach(function (k) { if (n[k]) gl.deleteBuffer(n[k]); });
  };
  Cizici.prototype._temizle = function () {
    const gl = this.gl;
    if (this._azami == null) this._azami = Math.min(16, gl.getParameter(gl.MAX_VERTEX_ATTRIBS));
    for (let i = 0; i < this._azami; i++) gl.disableVertexAttribArray(i);
  };
  Cizici.prototype._oznitelik = function (pr, ad, b, boyut, tur, normal) {
    const gl = this.gl, k = pr.a[ad];
    if (k == null || k < 0) return;
    if (!b) { gl.disableVertexAttribArray(k); if (ad === "aX") gl.vertexAttrib1f(k, 0); return; }
    gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.enableVertexAttribArray(k);
    gl.vertexAttribPointer(k, boyut, tur, !!normal, 0, 0);
  };
  Cizici.prototype.basla = function (en, boy, arka) {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, en, boy);
    gl.clearColor(arka[0], arka[1], arka[2], 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
  };
  /** Yüzey (renk ölçekli). o: {mvp, olcek, isik, lo, hi, kes, gri, opak}. */
  Cizici.prototype.yuzey = function (n, o) {
    const gl = this.gl, pr = this.ana;
    if (!n || !n.sayI) return;
    gl.useProgram(pr.p);
    this._temizle();
    this._oznitelik(pr, "aP", n.bP, 3, gl.FLOAT);
    this._oznitelik(pr, "aD", n.bD, 3, gl.FLOAT);
    this._oznitelik(pr, "aN", n.bN, 4, gl.BYTE, true);
    this._oznitelik(pr, "aV", n.bV, 1, gl.FLOAT);
    this._oznitelik(pr, "aX", n.bX, 1, gl.FLOAT);
    gl.uniformMatrix4fv(pr.u.uM, false, o.mvp);
    gl.uniform1f(pr.u.uS, o.olcek);
    gl.uniform3fv(pr.u.uL, o.isik);
    gl.uniform1f(pr.u.uA, o.lo);
    gl.uniform1f(pr.u.uB, o.hi);
    gl.uniform1f(pr.u.uKes, o.kes == null ? 1e30 : o.kes);
    gl.uniform3fv(pr.u.uG, o.gri || [0.6, 0.6, 0.6]);
    gl.uniform1f(pr.u.uO, o.opak == null ? 1 : o.opak);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.doku);
    gl.uniform1i(pr.u.uT, 0);
    if (o.ofset) { gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(1, 1); }
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, n.bI);
    gl.drawElements(gl.TRIANGLES, n.sayI, gl.UNSIGNED_INT, 0);
    gl.disable(gl.POLYGON_OFFSET_FILL);
    this._oznitelik(pr, "aN", null); this._oznitelik(pr, "aV", null);
  };
  /** Düz renkli çizgi / üçgen kümesi (hayalet, seçim çerçevesi, yük payı bölgeleri). */
  Cizici.prototype.duz = function (n, o, mod) {
    const gl = this.gl, pr = this.ciz;
    if (!n || !n.say) return;
    gl.useProgram(pr.p);
    this._temizle();
    this._oznitelik(pr, "aP", n.bP, 3, gl.FLOAT);
    this._oznitelik(pr, "aD", n.bD, 3, gl.FLOAT);
    gl.uniformMatrix4fv(pr.u.uM, false, o.mvp);
    gl.uniform1f(pr.u.uS, o.olcek);
    gl.uniform4fv(pr.u.uR, o.renk);
    if (o.renk[3] < 1) { gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false); }
    if (o.ustte) gl.disable(gl.DEPTH_TEST);
    gl.drawArrays(mod == null ? gl.LINES : mod, 0, n.say);
    gl.disable(gl.BLEND); gl.depthMask(true); gl.enable(gl.DEPTH_TEST);
  };
  /** Renk kimliği geçişi (ekran dışı çerçeve tamponu) ve tek piksel okuma. */
  Cizici.prototype.secimHazirla = function (en, boy) {
    const gl = this.gl;
    if (!this.secimFbo || this.secimFbo.en !== en || this.secimFbo.boy !== boy) {
      if (this.secimFbo) { gl.deleteFramebuffer(this.secimFbo.f); gl.deleteTexture(this.secimFbo.t); gl.deleteRenderbuffer(this.secimFbo.d); }
      const f = gl.createFramebuffer(), t = gl.createTexture(), d = gl.createRenderbuffer();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, en, boy, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.bindRenderbuffer(gl.RENDERBUFFER, d);
      gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT16, en, boy);
      gl.bindFramebuffer(gl.FRAMEBUFFER, f);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, d);
      this.secimFbo = { f: f, t: t, d: d, en: en, boy: boy };
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.secimFbo.f);
    gl.viewport(0, 0, en, boy);
    gl.clearColor(0, 0, 0, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
  };
  Cizici.prototype.secimCiz = function (n, o) {
    const gl = this.gl, pr = this.sec;
    if (!n || !n.sayI) return;
    gl.useProgram(pr.p);
    this._temizle();
    this._oznitelik(pr, "aP", n.bP, 3, gl.FLOAT);
    this._oznitelik(pr, "aD", n.bD, 3, gl.FLOAT);
    this._oznitelik(pr, "aK", n.bK, 4, gl.UNSIGNED_BYTE, true);
    this._oznitelik(pr, "aX", n.bX, 1, gl.FLOAT);
    gl.uniformMatrix4fv(pr.u.uM, false, o.mvp);
    gl.uniform1f(pr.u.uS, o.olcek);
    gl.uniform1f(pr.u.uKes, o.kes == null ? 1e30 : o.kes);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, n.bI);
    gl.drawElements(gl.TRIANGLES, n.sayI, gl.UNSIGNED_INT, 0);
    this._oznitelik(pr, "aK", null);
  };
  Cizici.prototype.pikselOku = function (x, y) {
    const gl = this.gl, p = new Uint8Array(4);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.secimFbo.f);
    gl.readPixels(x, this.secimFbo.boy - 1 - y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, p);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return renkKimlik(p[0], p[1], p[2]);
  };
  Cizici.prototype.birak = function () {
    try { const e = this.gl.getExtension("WEBGL_lose_context"); if (e) e.loseContext(); } catch (e) { /* yok */ }
  };

  // =====================================================================================
  // 10. Arayüz
  // =====================================================================================
  function azHareket() {
    try { return !!(kok.matchMedia && kok.matchMedia("(prefers-reduced-motion: reduce)").matches); } catch (e) { return false; }
  }
  function cssRenk(el, ad, yedek) {
    try {
      const v = getComputedStyle(el).getPropertyValue(ad).trim();
      return v || yedek;
    } catch (e) { return yedek; }
  }
  function rgbDizi(css) {
    const c = String(css || "").trim();
    let m = /^#([0-9a-f]{6})$/i.exec(c);
    if (m) return [parseInt(m[1].slice(0, 2), 16) / 255, parseInt(m[1].slice(2, 4), 16) / 255, parseInt(m[1].slice(4, 6), 16) / 255];
    m = /^#([0-9a-f]{3})$/i.exec(c);
    if (m) return [0, 1, 2].map(function (i) { return parseInt(m[1][i] + m[1][i], 16) / 255; });
    m = /rgba?\(([^)]+)\)/.exec(c);
    if (m) { const p = m[1].split(",").map(Number); return [p[0] / 255, p[1] / 255, p[2] / 255]; }
    return [0.95, 0.96, 0.98];
  }
  function elemanAdi(e) {
    const tur = { kolon: "Kolon", kiris: "Kiriş" }[e.tur] || (e.tur ? e.tur.charAt(0).toUpperCase() + e.tur.slice(1) : "Eleman");
    return "E" + e.no + " · " + tur + (e.adres ? " " + e.adres : (e.bina_no != null ? " " + e.bina_no : ""));
  }
  function birimMetni(b) { return b.birim ? " (" + b.birim + ")" : ""; }

  function ac(kapsayici, ayar) {
    if (!kapsayici) throw new Error("MatrisIsi.ac: kapsayıcı öğe gerekli.");
    ayar = ayar || {};
    const olay = ayar.olay || {};
    let alan = ayar.alan || { elemanlar: [] };
    let bina = ayar.bina || null;
    const D = {
      buyukluk: "u", palet: "klasik", bantli: true, elle: false, elleMin: null, elleMax: null,
      deforme: true, olcekCarpan: 1, gercek: false, hayalet: true, anim: false, animFaz: 0,
      tup: false, doseme: "kapali", radye: "kapali", kat: "", aks: "", gizli: {}, yalit: null, secili: {}, uzerinde: -1,
      perspektif: true,
    };
    const kam = { hedef: [0, 0, 0], uzak: 10, yaw: STANDART["3b"].yaw, pitch: STANDART["3b"].pitch, fov: 35 * Math.PI / 180, orto: false, R: 5 };
    const kokEl = document.createElement("div");
    kokEl.className = "isi-kok";
    kokEl.setAttribute("role", "region");
    kokEl.setAttribute("aria-label", "Isı haritası: sonuçların yapı üzerinde renkli gösterimi");
    kokEl.innerHTML = iskelet();
    kapsayici.appendChild(kokEl);
    function $(s) { return kokEl.querySelector(s); }
    const R = {
      buyukluk: $("[data-isi=buyukluk]"), durum: $("[data-isi=durum]"), durumKutu: $(".isi-durum-kutu"), durumAd: $(".isi-durum-ad"),
      sahne: $(".isi-sahne"), tuval: $(".isi-tuval"), svg: $(".isi-svg"), lejant: $(".isi-lejant"), plakLejant: $(".isi-plak-lejant"),
      mx: $(".isi-mx"), mn: $(".isi-mn"), sonda: $(".isi-sonda"), bilgi: $(".isi-bilgi"), canli: $(".isi-canli"), not: $(".isi-not"),
      olcekMod: $("[data-isi=olcek-mod]"), olcekMin: $("[data-isi=olcek-min]"), olcekMax: $("[data-isi=olcek-max]"),
      deforme: $("[data-isi=deforme]"), defOlcek: $("[data-isi=def-olcek]"), defCikti: $(".isi-def-cikti"), anim: $("[data-isi=anim]"),
      hayalet: $("[data-isi=hayalet]"), kat: $("[data-isi=kat]"), aks: $("[data-isi=aks]"), doseme: $("[data-isi=doseme]"),
      radye: $("[data-isi=radye]"), radyeKutu: $(".isi-radye-kutu"), ayar: $(".isi-ayar"), persp: $("[data-isi=persp]"),
      eleman: $(".isi-eleman"),
    };
    let cz = null, svgMod = false;
    try { cz = new Cizici(R.tuval); } catch (e) { cz = null; svgMod = true; }
    if (svgMod) { R.tuval.hidden = true; R.svg.removeAttribute("hidden");   /* SVGElement'in hidden özelliği yok: öznitelik */ R.not.textContent = "WebGL kullanılamıyor: basit (SVG) çizim gösteriliyor."; R.not.hidden = false; }
    // ---- durum ----
    let els = [], noIdx = {}, ag = null, gpu = null, V = null, gorunur = null, ekst = null, aralik = [0, 1], umax = 0, otoOlcek = 1;
    let plaklar = [], radyeN = null, payiN = [], hayaletN = null, eksenN = null, secimN = null, uzerindeN = null, panelKutu = [];
    let plakAralik = [0, 1], radyeAralik = [0, 1], modelBoyut = 10;
    let en = 1, boy = 1, dpr = 1, istek = 0, secimKirli = true, sonKare = 0, kapali = false;
    let EG = null;    // eleman görünümü
    const dinleyiciler = [];
    function dinle(h, t, f, o) { h.addEventListener(t, f, o); dinleyiciler.push([h, t, f, o]); }

    function iskelet() {
      const sec = BUYUKLUKLER.map(function (b) { return '<option value="' + b.ad + '">' + kacis(b.etiket + birimMetni(b)) + "</option>"; });
      const gruplar = {};
      BUYUKLUKLER.forEach(function (b, i) { (gruplar[b.grup] = gruplar[b.grup] || []).push(sec[i]); });
      const secenekler = Object.keys(gruplar).map(function (g) { return '<optgroup label="' + kacis(g) + '">' + gruplar[g].join("") + "</optgroup>"; }).join("");
      return '' +
        '<div class="isi-ust">' +
        '<label class="isi-etiket">Büyüklük <select class="girdi isi-sec" data-isi="buyukluk">' + secenekler + "</select></label>" +
        '<label class="isi-etiket isi-durum-kutu" hidden>Durum <select class="girdi isi-sec" data-isi="durum"></select></label>' +
        '<span class="isi-durum-ad" aria-live="polite"></span>' +
        '<span class="isi-bosluk"></span>' +
        '<button type="button" class="dugme kucuk" data-isi="incele" title="Seçili elemanı ayrıntılı incele (Enter / çift tıklama)">İncele</button>' +
        '<button type="button" class="dugme kucuk" data-isi="png" title="Görüntüyü PNG olarak indir">PNG</button>' +
        '<button type="button" class="dugme kucuk isi-kapat" data-isi="kapat" aria-label="Isı haritasını kapat">✕</button>' +
        "</div>" +
        '<details class="isi-ayar"><summary>Görünüm, ölçek ve süzgeçler</summary><div class="isi-ayar-govde">' +
        '<div class="isi-grup" role="group" aria-label="Renk ölçeği"><span class="isi-grup-ad">Renk</span>' +
        '<div class="isi-seg" data-seg="renk"><button type="button" data-v="bant" aria-pressed="true">9 bant</button><button type="button" data-v="surekli" aria-pressed="false">Sürekli</button>' +
        '<button type="button" data-v="iki" aria-pressed="false" title="Sıfır ortada, iki yönlü (mavi − / kırmızı +)">İki yönlü</button></div></div>' +
        '<div class="isi-grup" role="group" aria-label="Ölçek kilidi"><span class="isi-grup-ad">Ölçek</span>' +
        '<select class="girdi isi-kucuk" data-isi="olcek-mod"><option value="oto">Otomatik</option><option value="elle">Elle (kilitli)</option></select>' +
        '<input class="girdi isi-sayi" data-isi="olcek-min" inputmode="decimal" aria-label="Ölçek en küçük" placeholder="min" disabled>' +
        '<input class="girdi isi-sayi" data-isi="olcek-max" inputmode="decimal" aria-label="Ölçek en büyük" placeholder="maks" disabled></div>' +
        '<div class="isi-grup" role="group" aria-label="Deforme şekil"><label class="isi-onay"><input type="checkbox" data-isi="deforme" checked> Deforme</label>' +
        '<input type="range" class="isi-aralik" data-isi="def-olcek" min="0" max="100" value="50" aria-label="Deforme ölçeği"><output class="isi-def-cikti">×1</output>' +
        '<button type="button" class="dugme kucuk" data-isi="gercek" title="Yer değiştirmeleri gerçek boyutta çiz">Gerçek ölçek</button>' +
        '<button type="button" class="dugme kucuk" data-isi="anim" aria-pressed="false" title="0 → 1 → 0 canlandırma">▶ Canlandır</button>' +
        '<label class="isi-onay"><input type="checkbox" data-isi="hayalet" checked> Deforme olmamış hayalet</label></div>' +
        '<div class="isi-grup" role="group" aria-label="Görünüm"><span class="isi-grup-ad">Görünüm</span>' +
        '<div class="isi-seg" data-seg="gorunum"><button type="button" data-v="3b">3B</button><button type="button" data-v="plan">Plan</button><button type="button" data-v="on">Ön</button><button type="button" data-v="yan">Yan</button><button type="button" data-v="sigdir">Sığdır</button></div>' +
        '<label class="isi-onay"><input type="checkbox" data-isi="persp" checked> Perspektif</label></div>' +
        '<div class="isi-grup" role="group" aria-label="Süzgeçler"><span class="isi-grup-ad">Süzgeç</span>' +
        '<select class="girdi isi-kucuk" data-isi="kat" aria-label="Kat süzgeci"></select><select class="girdi isi-kucuk" data-isi="aks" aria-label="Aks süzgeci"></select>' +
        '<button type="button" class="dugme kucuk" data-isi="yalit" title="Yalnız seçili elemanları göster">Yalıt</button>' +
        '<button type="button" class="dugme kucuk" data-isi="gizle" title="Seçili elemanları gizle">Gizle</button>' +
        '<button type="button" class="dugme kucuk" data-isi="tumu">Tümünü göster</button></div>' +
        '<div class="isi-grup" role="group" aria-label="Çizim"><span class="isi-grup-ad">Çizim</span>' +
        '<div class="isi-seg" data-seg="cizim"><button type="button" data-v="kati" aria-pressed="true">Gerçek kesit</button><button type="button" data-v="tup" aria-pressed="false">İnce tüp</button></div>' +
        '<label class="isi-etiket">Döşeme <select class="girdi isi-kucuk" data-isi="doseme"><option value="kapali">Kapalı</option><option value="w">Plak sehimi w</option>' +
        '<option value="mx">Plak momenti m_x</option><option value="my">Plak momenti m_y</option><option value="payi">Yük payı (45°)</option></select></label>' +
        '<label class="isi-etiket isi-radye-kutu" hidden>Radye <select class="girdi isi-kucuk" data-isi="radye"><option value="kapali">Kapalı</option>' +
        '<option value="p">Taban basıncı p</option><option value="w">Oturma w</option></select></label></div>' +
        "</div></details>" +
        '<p class="isi-not not" hidden></p>' +
        '<div class="isi-sahne">' +
        '<canvas class="isi-tuval" tabindex="0" aria-label="Yapı ısı haritası. Ok tuşları: eleman gezintisi; Enter: incele; Esc: seçimi bırak; + / −: yakınlaştır; sürükle: döndür, sağ tuş ya da Shift: kaydır."></canvas>' +
        '<svg class="isi-svg" hidden tabindex="0" role="img" aria-label="Yapı ısı haritası (basit çizim)"></svg>' +
        '<div class="isi-lejant"></div><div class="isi-plak-lejant isi-lejant" hidden></div>' +
        '<div class="isi-isaret isi-mx" hidden>MX</div><div class="isi-isaret isi-mn" hidden>MN</div>' +
        '<div class="isi-sonda" role="status" hidden></div>' +
        "</div>" +
        '<div class="isi-alt"><span class="isi-bilgi"></span></div>' +
        '<div class="isi-canli isi-gizli-metin" aria-live="polite"></div>' +
        '<div class="isi-eleman" role="dialog" aria-modal="false" aria-label="Eleman incelemesi" tabindex="-1" hidden></div>';
    }

    // ---------------- veri hazırlığı ----------------
    function alanHazirla() {
      els = (alan.elemanlar || []).filter(function (e) { return e && e.i && e.j && e.yerel && e.x && e.x.length >= 2; });
      noIdx = {};
      els.forEach(function (e, i) { noIdx[e.no] = i; });
      umax = 0;
      els.forEach(function (e) { (e.u || []).forEach(function (u) { umax = Math.max(umax, Math.hypot(u[0], u[1], u[2])); }); });
      (alan.dugumler || []).forEach(function (d) { if (d.u) umax = Math.max(umax, Math.hypot(d.u[0], d.u[1], d.u[2])); });
      const kt = kutuHesapla(els, null);
      const boyut = Math.max(1e-3, Math.hypot(kt[1][0] - kt[0][0], kt[1][1] - kt[0][1], kt[1][2] - kt[0][2]));
      modelBoyut = boyut;
      otoOlcek = umax > 0 ? 0.06 * boyut / umax : 1;
      // durum seçici
      const s = alan.secenekler;
      if (olay.durumSec && s) {
        R.durumKutu.hidden = false;
        let h = "";
        if (s.durumlar && s.durumlar.length) h += '<optgroup label="Yük durumları">' + s.durumlar.map(function (a) { return '<option value="' + kacis(a) + '">' + kacis(a) + "</option>"; }).join("") + "</optgroup>";
        if (s.kombinasyonlar && s.kombinasyonlar.length) h += '<optgroup label="Kombinasyonlar">' + s.kombinasyonlar.map(function (k) { return '<option value="' + kacis(k.ad) + '">' + kacis(k.ad) + (k.tur ? " (" + kacis(k.tur) + ")" : "") + "</option>"; }).join("") + "</optgroup>";
        h += '<optgroup label="Zarf"><option value="zarf+">Zarf + (en büyük)</option><option value="zarf-">Zarf − (en küçük)</option></optgroup>';
        R.durum.innerHTML = h;
        R.durum.value = alan.durum;
      }
      R.durumAd.textContent = (R.durumKutu.hidden ? "Durum: " + (alan.durum || "—") : "") +
        (alan.zarf ? (R.durumKutu.hidden ? " · " : "") + (alan.kombinasyon_sayisi || "") + " kombinasyonun zarfı" : "");
      // süzgeç listeleri
      const kv = R.kat.value, av = R.aks.value;
      R.kat.innerHTML = '<option value="">Bütün katlar</option>' + katListesi(alan, bina).map(function (k) { return '<option value="' + k.no + '">' + kacis(k.ad) + "</option>"; }).join("");
      const akslar = aksListesi(alan, bina);
      R.aks.innerHTML = '<option value="">Bütün akslar</option>' + akslar.map(function (a, i) {
        return '<option value="' + i + '">' + kacis((a.yon === "x" ? "Aks " : "Aks ") + a.ad) + "</option>";
      }).join("");
      R.aks._akslar = akslar;
      if ([].some.call(R.kat.options, function (o) { return o.value === kv; })) R.kat.value = kv;
      if ([].some.call(R.aks.options, function (o) { return o.value === av; })) R.aks.value = av;
      R.radyeKutu.hidden = !alan.radye;
      const notlar = [];
      if (alan.not) notlar.push(alan.not);
      if (alan.zarf_not) notlar.push(alan.zarf_not);
      if (svgMod) notlar.unshift("WebGL kullanılamıyor: basit (SVG) çizim gösteriliyor.");
      R.not.textContent = notlar.join(" ");
      R.not.hidden = !notlar.length;
      // kullanım verisi yoksa seçici ipucu
      const kulVar = els.some(function (e) { return e.kullanim; });
      [].forEach.call(R.buyukluk.options, function (o) { if (o.value === "kullanim") o.disabled = !kulVar; });
      if (D.buyukluk === "kullanim" && !kulVar) D.buyukluk = "von_mises";
      R.buyukluk.value = D.buyukluk;
    }
    function tupYaricapi(e) {
      const boyut = modelBoyut || 10;
      const k = e.kesit || {};
      const s = 0.3 * Math.max(k.dy || 0.2, k.dz || 0.2);
      return Math.max(0.0025 * boyut, Math.min(s, 0.008 * boyut));
    }
    function agKur() {
      if (svgMod) { gorunurlukGuncelle(); return; }
      cz.sil(gpu);
      const bas = (kok.performance ? performance.now() : Date.now());
      // çok büyük modelde köşe bütçesi: önce halkalar seyreltilir (değerler istasyonlarda kesin kalır), gerekirse ince tüp
      let tup = D.tup, seyrek = 1;
      ag = cubukAgi(els, { tup: tup, tupR: tupYaricapi });
      if (ag.kose > KOSE_BUTCESI) {
        seyrek = Math.min(4, Math.ceil(ag.kose / KOSE_BUTCESI));
        ag = cubukAgi(els, { tup: tup, tupR: tupYaricapi, seyrek: seyrek });
        if (!tup && ag.kose > 3 * KOSE_BUTCESI) { tup = true; ag = cubukAgi(els, { tup: true, tupR: tupYaricapi, seyrek: seyrek }); }
        R.not.textContent = "Model büyük (" + els.length + " eleman): halkalar her " + seyrek + " istasyonda bir çizildi" + (tup && !D.tup ? ", ince tüpe geçildi" : "") +
          "; renkler istasyon değerleridir. Ayrıntı için eleman görünümünü kullanın.";
        R.not.hidden = false;
      }
      ag.seyrek = seyrek;
      gpu = cz.nesne(ag);
      V = new Float32Array(ag.kose);
      ag.surec = (kok.performance ? performance.now() : Date.now()) - bas;
      plakKur();
      gorunurlukGuncelle();
    }
    function koseOtelemesi(p) {
      let en_ = null, ed = 1e-3;
      (alan.dugumler || []).forEach(function (d) {
        const m = Math.abs(d.X - p[0]) + Math.abs(d.Y - p[1]) + Math.abs(d.Z - p[2]);
        if (m < ed) { ed = m; en_ = d; }
      });
      return en_ && en_.u ? en_.u : [0, 0, 0];
    }
    function plakKur() {
      plaklar.forEach(function (p) { cz.sil(p.n); });
      payiN.forEach(function (p) { cz.sil(p); });
      if (radyeN) cz.sil(radyeN.n);
      plaklar = []; payiN = []; radyeN = null; panelKutu = [];
      (alan.paneller || []).forEach(function (pn, pi) {
        if (!pn.izgara || !pn.izgara.x) return;
        const cu = pn.kose.map(koseOtelemesi);
        const a = plakAgi(pn, cu, PANEL_KIMLIK0 + pi);
        plaklar.push({ pn: pn, n: cz.nesne(a), ag: a, kosu: cu, pi: pi });
        panelKutu.push(pn);
      });
      // yük payı bölgeleri: kenar yönü ve sıra paritesiyle 4 renk (komşu kirişler farklı)
      const ys = {}, xs = {};
      (alan.paneller || []).forEach(function (pn) { ys[pn.kose[0][1].toFixed(3)] = 1; ys[pn.kose[2][1].toFixed(3)] = 1; xs[pn.kose[0][0].toFixed(3)] = 1; xs[pn.kose[2][0].toFixed(3)] = 1; });
      const ysS = Object.keys(ys).map(Number).sort(function (a, b) { return a - b; }), xsS = Object.keys(xs).map(Number).sort(function (a, b) { return a - b; });
      const kume = [[], [], [], []];
      (alan.paneller || []).forEach(function (pn) {
        if (!plakGorunur(pn)) return;
        const z = pn.z + 0.004;
        (pn.yuk_payi || []).forEach(function (yp) {
          if (!yp.poligon || yp.poligon.length < 3) return;
          let renk;
          if (yp.kenar === "alt" || yp.kenar === "ust") {
            const yv = yp.kenar === "alt" ? pn.kose[0][1] : pn.kose[2][1];
            renk = ysS.indexOf(Number(yv.toFixed(3))) % 2;
          } else {
            const xv = yp.kenar === "sol" ? pn.kose[0][0] : pn.kose[2][0];
            renk = 2 + xsS.indexOf(Number(xv.toFixed(3))) % 2;
          }
          const t = ucgenle(ccw(yp.poligon));
          const pol = ccw(yp.poligon);
          for (let i = 0; i < t.length; i++) kume[renk].push(pol[t[i]][0], pol[t[i]][1], z);
        });
      });
      payiN = kume.map(function (k) { const P = new Float32Array(k); return cz.cizgiNesnesi(P, new Float32Array(P.length)); });
      if (alan.radye && alan.radye.x && alan.radye.x.length > 1 && alan.radye.y.length > 1) {
        const a = radyeAgi(alan.radye, RADYE_KIMLIK);
        radyeN = { n: cz.nesne(a), ag: a };
      }
      plakDegerleri();
    }
    function plakDegerleri() {
      if (svgMod) return;
      let lo = Infinity, hi = -Infinity;
      if (D.doseme === "w" || D.doseme === "mx" || D.doseme === "my") {
        plaklar.forEach(function (p) {
          const g = p.pn.izgara, Vp = new Float32Array(g.nx * g.ny);
          for (let j = 0; j < g.ny; j++) for (let i = 0; i < g.nx; i++) {
            const v = plakDegeri(p.pn, D.doseme, i, j);
            Vp[j * g.nx + i] = v == null ? GECERSIZ : v;
            if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
          }
          cz.degerYukle(p.n, Vp);
        });
        plakAralik = aralikBelirle(lo, hi, false);
      }
      if (radyeN && D.radye !== "kapali") {
        const r = alan.radye, nx = r.x.length, Vr = new Float32Array(nx * r.y.length);
        let a = Infinity, b = -Infinity;
        for (let j = 0; j < r.y.length; j++) for (let i = 0; i < nx; i++) {
          let v = D.radye === "p" ? r.p[j][i] : r.w[j][i];
          if (v != null && D.radye === "w") v *= 1000;
          Vr[j * nx + i] = v == null ? GECERSIZ : v;
          if (v != null) { a = Math.min(a, v); b = Math.max(b, v); }
        }
        cz.degerYukle(radyeN.n, Vr);
        radyeAralik = aralikBelirle(a, b, false);
      }
    }
    function plakGorunur(pn) { return D.kat === "" || String(pn.kat) === String(D.kat); }
    function gorunurHesapla() {
      const g = new Uint8Array(els.length);
      const aks = R.aks._akslar && D.aks !== "" ? R.aks._akslar[+D.aks] : null;
      for (let i = 0; i < els.length; i++) {
        const e = els[i];
        let ok = true;
        if (D.kat !== "" && String(e.kat) !== String(D.kat)) ok = false;
        if (ok && aks && !aksUstunde(e, aks)) ok = false;
        if (ok && D.yalit && !D.yalit[i]) ok = false;
        if (ok && D.gizli[i]) ok = false;
        g[i] = ok ? 1 : 0;
      }
      return g;
    }
    function gorunurlukGuncelle() {
      gorunur = gorunurHesapla();
      if (!svgMod && ag) {
        let say = 0;
        for (let i = 0; i < els.length; i++) if (gorunur[i] && ag.araliklar[i]) say += ag.araliklar[i].say;
        const I = new Uint32Array(say);
        let o = 0;
        for (let i = 0; i < els.length; i++) {
          if (!gorunur[i] || !ag.araliklar[i]) continue;
          const a = ag.araliklar[i];
          I.set(ag.I.subarray(a.bas, a.bas + a.say), o);
          o += a.say;
        }
        cz.indisYukle(gpu, I);
        hayaletKur();
      }
      degerGuncelle();
    }
    function hayaletKur() {
      const P = [], Q = [], Dq = [];
      for (let i = 0; i < els.length; i++) {
        if (!gorunur[i]) continue;
        const e = els[i];
        P.push(e.i[0], e.i[1], e.i[2], e.j[0], e.j[1], e.j[2]);
        // hafif kip: deforme eksen çizgisi (istasyonlarda)
        for (let k = 0; k + 1 < e.x.length; k++) {
          for (let m = k; m <= k + 1; m++) {
            for (let c = 0; c < 3; c++) Q.push(e.i[c] + e.x[m] * e.yerel.x[c]);
            const u = (e.u && e.u[m]) || [0, 0, 0];
            Dq.push(u[0], u[1], u[2]);
          }
        }
      }
      if (hayaletN) cz.sil(hayaletN);
      if (eksenN) cz.sil(eksenN);
      hayaletN = cz.cizgiNesnesi(new Float32Array(P), new Float32Array(P.length));
      eksenN = cz.cizgiNesnesi(new Float32Array(Q), new Float32Array(Dq));
      eksenN.bV = cz.gl.createBuffer();
      eksenDegerleri();
      secimKur();
    }
    /** Seçili (ve üzerine gelinen) elemanların tel çerçevesi: anahat köşelerinden boyuna çizgiler + uç halkaları. */
    function cerceveCizgileri(liste) {
      const P = [], Dd = [];
      liste.forEach(function (ei) {
        const e = els[ei];
        if (!e || !ag) return;
        const an = ag.anahatlar[ei] || kesitAnahat(e.kesit, false);
        const ex = e.yerel.x, ey = e.yerel.y, ez = e.yerel.z, xs = e.x, U = e.u || [];
        function nokta(k, y, z) {
          y *= 1.04; z *= 1.04;
          P.push(e.i[0] + xs[k] * ex[0] + y * ey[0] + z * ez[0], e.i[1] + xs[k] * ex[1] + y * ey[1] + z * ez[1], e.i[2] + xs[k] * ex[2] + y * ey[2] + z * ez[2]);
          const u = U[k] || [0, 0, 0];
          Dd.push(u[0], u[1], u[2]);
        }
        an.parcalar.forEach(function (pr) {
          const pts = pr.dis, n = pts.length, adim = pr.puruzsuz ? Math.max(1, Math.floor(n / 4)) : 1;
          for (let p = 0; p < n; p += adim) {
            for (let k = 0; k + 1 < xs.length; k++) { nokta(k, pts[p][0], pts[p][1]); nokta(k + 1, pts[p][0], pts[p][1]); }
          }
          [0, xs.length - 1, Math.floor(xs.length / 2)].forEach(function (k) {
            for (let p = 0; p < n; p++) { nokta(k, pts[p][0], pts[p][1]); nokta(k, pts[(p + 1) % n][0], pts[(p + 1) % n][1]); }
          });
        });
      });
      return [new Float32Array(P), new Float32Array(Dd)];
    }
    function secimKur() {
      if (svgMod || !cz) return;
      if (secimN) cz.sil(secimN);
      if (uzerindeN) cz.sil(uzerindeN);
      const sec = Object.keys(D.secili).map(Number).filter(function (i) { return gorunur && gorunur[i]; });
      const a = cerceveCizgileri(sec);
      secimN = cz.cizgiNesnesi(a[0], a[1]);
      const b = cerceveCizgileri(D.uzerinde >= 0 && !D.secili[D.uzerinde] ? [D.uzerinde] : []);
      uzerindeN = cz.cizgiNesnesi(b[0], b[1]);
    }
    /** Hafif kip eksen çizgisi değerleri: istasyon büyüklüğü (lif büyüklüğünde en dış lif σ_maks / von Mises). */
    function eksenDegerleri() {
      if (svgMod || !eksenN || !eksenN.bV) return;
      const ad = D.buyukluk === "sigma_lif" ? "sigma_max" : (D.buyukluk === "vm_lif" ? "von_mises" : D.buyukluk);
      const V2 = new Float32Array(eksenN.say);
      let o = 0;
      for (let i = 0; i < els.length; i++) {
        if (!gorunur[i]) continue;
        const e = els[i];
        for (let k = 0; k + 1 < e.x.length; k++) {
          for (let m = k; m <= k + 1; m++) { const v = istasyonDegeri(e, ad, m); V2[o++] = v == null ? GECERSIZ : v; }
        }
      }
      cz.degerYukle(eksenN, V2);
    }
    function degerGuncelle() {
      const b = BUYUKLUK[D.buyukluk];
      ekst = ekstremumBul(els, D.buyukluk, gorunur, ag ? ag.anahatlar : els.map(function (e) { return kesitAnahat(e.kesit, false); }));
      const lo = ekst.min ? ekst.min.deger : null, hi = ekst.max ? ekst.max.deger : null;
      if (D.elle && D.elleMin != null && D.elleMax != null && D.elleMax > D.elleMin) aralik = [D.elleMin, D.elleMax];
      else aralik = aralikBelirle(lo, hi, D.palet === "iki" && b.iki);
      if (!D.elle) { R.olcekMin.value = fmt(aralik[0], 5); R.olcekMax.value = fmt(aralik[1], 5); }
      if (!svgMod && ag) { degerleriDoldur(ag, els, D.buyukluk, V); cz.degerYukle(gpu, V); eksenDegerleri(); }
      lejantCiz();
      bilgiYaz();
      iste();
      if (EG) EG.guncelle();
    }

    // ---------------- lejant ----------------
    function lejantHtml(baslik, alt, lo, hi, ek) {
      const sin = lejantSinirlari(lo, hi, BANT);
      let h = '<div class="isi-lej-baslik">' + kacis(baslik) + "</div>" + (alt ? '<div class="isi-lej-alt">' + kacis(alt) + "</div>" : "");
      if (D.bantli) {
        h += '<ol class="isi-lej-bantlar" aria-label="Renk bantları (yukarıdan aşağı)">';
        for (let i = 0; i < BANT; i++) {
          const t = (BANT - 1 - i + 0.5) / BANT;
          h += '<li><span class="isi-lej-renk" style="background:' + renkHex(renkAl(t, D.palet, true)) + '"></span><span class="isi-lej-deger">' + fmt(sin[i], 4) + "</span></li>";
        }
        h += '<li class="isi-lej-son"><span class="isi-lej-renk isi-lej-bos"></span><span class="isi-lej-deger">' + fmt(sin[BANT], 4) + "</span></li></ol>";
        h += '<div class="isi-lej-dar-uclar" aria-hidden="true"><span>' + fmt(lo, 4) + "</span><span>" + fmt(hi, 4) + "</span></div>";
      } else {
        const durak = [];
        for (let i = 0; i <= 10; i++) durak.push(renkHex(renkAl(1 - i / 10, D.palet, false)) + " " + (i * 10) + "%");
        h += '<div class="isi-lej-surekli"><span class="isi-lej-serit" style="--isi-g:' + durak.join(",") + '"></span><span class="isi-lej-uclar"><span>' +
          fmt(hi, 4) + "</span><span>" + fmt((lo + hi) / 2, 4) + "</span><span>" + fmt(lo, 4) + "</span></span></div>" +
          '<div class="isi-lej-dar-uclar" aria-hidden="true"><span>' + fmt(lo, 4) + "</span><span>" + fmt(hi, 4) + "</span></div>";
      }
      return h + (ek || "");
    }
    function ekstMetni(x, ad) {
      if (!x) return "";
      const e = els[x.el];
      return ad + " " + fmt(x.deger, 4) + " — E" + e.no + ", x = " + fmt(e.x[x.k], 3) + " m";
    }
    function lejantCiz() {
      const b = BUYUKLUK[D.buyukluk];
      const ek = '<div class="isi-lej-ek">' + (ekst.max ? '<div><b class="isi-lej-mx">MX</b> ' + kacis(ekstMetni(ekst.max, "")) + "</div>" : "") +
        (ekst.min ? '<div><b class="isi-lej-mn">MN</b> ' + kacis(ekstMetni(ekst.min, "")) + "</div>" : "") +
        (D.elle ? '<div class="isi-lej-kilit">Ölçek kilitli (elle)</div>' : "") + "</div>";
      R.lejant.innerHTML = lejantHtml(b.kisa + birimMetni(b), (alan.durum || "") + (alan.zarf ? " (zarf)" : ""), aralik[0], aralik[1], ek);
      R.lejant.setAttribute("aria-label", "Lejant: " + b.etiket + ", " + fmt(aralik[0], 4) + " ile " + fmt(aralik[1], 4) + " " + (b.birim || "") + " arası");
      // plak / radye lejantı
      let ph = "";
      if (D.doseme === "w" || D.doseme === "mx" || D.doseme === "my") {
        const ad = { w: "Plak sehimi w (mm)", mx: "Plak m_x (kN·m/m)", my: "Plak m_y (kN·m/m)" }[D.doseme];
        ph += lejantHtml(ad, "Navier, 4 kenar basit mesnet", plakAralik[0], plakAralik[1], "");
      } else if (D.doseme === "payi") {
        ph += '<div class="isi-lej-baslik">Yük payı (45°)</div><ul class="isi-lej-kat">' +
          ["X doğrultulu kiriş (1., 3., … Y aksı)", "X doğrultulu kiriş (2., 4., … Y aksı)", "Y doğrultulu kiriş (1., 3., … X aksı)", "Y doğrultulu kiriş (2., 4., … X aksı)"].map(function (t, i) {
            return '<li><span class="isi-lej-renk" style="background:' + KATEGORI[i] + '"></span>' + kacis(t) + "</li>";
          }).join("") + "</ul>";
      }
      if (radyeN && D.radye !== "kapali") ph += lejantHtml(D.radye === "p" ? "Taban basıncı p (kN/m²)" : "Oturma w (mm)", "Winkler, p = k0·w", radyeAralik[0], radyeAralik[1], "");
      R.plakLejant.innerHTML = ph;
      R.plakLejant.hidden = !ph;
    }
    function bilgiYaz() {
      let ng = 0;
      for (let i = 0; i < els.length; i++) if (gorunur && gorunur[i]) ng++;
      const b = BUYUKLUK[D.buyukluk];
      R.bilgi.textContent = ng + " / " + els.length + " eleman · " + b.kisa + ": " + fmt(ekst.min ? ekst.min.deger : null, 4) + " … " +
        fmt(ekst.max ? ekst.max.deger : null, 4) + (b.birim ? " " + b.birim : "") + " · ölçek " + defOlcekMetni() +
        (ag ? " · " + ag.kose.toLocaleString("tr-TR") + " köşe" : "") + (sonKare ? " · kare " + sonKare.toFixed(1) + " ms" : "");
    }

    // ---------------- deforme ölçeği ----------------
    function defCarpan() {
      if (!D.deforme) return 0;
      if (D.gercek) return 1;
      return otoOlcek * D.olcekCarpan;
    }
    function defOlcekMetni() { const s = defCarpan(); return s === 0 ? "kapalı" : "×" + fmt(s, 3); }
    function etkinOlcek() {
      const s = defCarpan();
      return D.anim ? s * (0.5 - 0.5 * Math.cos(D.animFaz)) : s;
    }

    // ---------------- boyut ve kamera ----------------
    function boyutla() {
      const r = R.sahne.getBoundingClientRect();
      kokEl.classList.toggle("isi-dar", kokEl.getBoundingClientRect().width < 600);
      kam.asp = r.width / Math.max(1, r.height);
      dpr = Math.min(2, kok.devicePixelRatio || 1);
      en = Math.max(1, Math.round(r.width * dpr));
      boy = Math.max(1, Math.round(r.height * dpr));
      if (R.tuval.width !== en || R.tuval.height !== boy) { R.tuval.width = en; R.tuval.height = boy; secimKirli = true; }
      iste();
    }
    function gorunumAyarla(ad, anim) {
      const kutu = kutuHesapla(els, gorunur);
      if (ad === "sigdir") { sigdir(kam, kutu[0], kutu[1]); secimKirli = true; iste(); return; }
      const s = STANDART[ad] || STANDART["3b"];
      if (ad === "3b") R.persp.checked = D.perspektif;
      // hedef kamera: yön ve izdüşüm önce, sığdırma o yönde
      const hk = Object.assign({}, kam, { yaw: s.yaw, pitch: s.pitch, orto: ad === "3b" ? !D.perspektif : true, hedef: kam.hedef.slice() });
      sigdir(hk, kutu[0], kutu[1]);
      if (!anim || azHareket()) { Object.assign(kam, hk); secimKirli = true; iste(); return; }
      const k0 = { yaw: kam.yaw, pitch: kam.pitch, uzak: kam.uzak, hedef: kam.hedef.slice() }, t0 = performance.now();
      let dy = hk.yaw - k0.yaw;
      while (dy > Math.PI) dy -= 2 * Math.PI;
      while (dy < -Math.PI) dy += 2 * Math.PI;
      kam.orto = hk.orto; kam.R = hk.R;
      function adim(t) {
        const f = Math.min(1, (t - t0) / 220), g = f * f * (3 - 2 * f);
        kam.yaw = k0.yaw + dy * g; kam.pitch = k0.pitch + (hk.pitch - k0.pitch) * g; kam.uzak = k0.uzak + (hk.uzak - k0.uzak) * g;
        for (let c = 0; c < 3; c++) kam.hedef[c] = k0.hedef[c] + (hk.hedef[c] - k0.hedef[c]) * g;
        secimKirli = true;
        ciz();
        if (f < 1 && !kapali) requestAnimationFrame(adim);
      }
      requestAnimationFrame(adim);
    }

    // ---------------- çizim ----------------
    let sonRaf = 0, yavasSay = 0, hafif = false;
    function iste() {
      if (istek || kapali) return;
      istek = requestAnimationFrame(function (t) {
        istek = 0;
        // etkileşim (sürükleme) sırasında kare aralığı uzunsa (yazılımsal çizici, zayıf GPU): hafif kip — katılar yerine
        // deforme eksen çizgileri; bırakınca tam çizim
        if (surukle && sonRaf) {
          yavasSay = t - sonRaf > 70 ? yavasSay + 1 : 0;
          if (yavasSay >= 2) hafif = true;
        }
        sonRaf = t;
        ciz();
      });
    }
    function hizliBitir() {
      sonRaf = 0; yavasSay = 0;
      if (hafif) { hafif = false; iste(); }
    }
    function arkaRenk() { return rgbDizi(cssRenk(kokEl, "--arka", "#f3f6fb")); }
    function ciz() {
      if (kapali) return;
      const t0 = performance.now();
      if (svgMod) { svgCiz(); isaretleriYerlestir(); return; }
      const km = kameraMatrisi(kam, en, boy);
      const s = etkinOlcek();
      const isik = v3Bir([-km.ileri[0] + 0.25 * km.yukari[0], -km.ileri[1] + 0.25 * km.yukari[1], -km.ileri[2] + 0.25 * km.yukari[2]]);
      cz.basla(en, boy, arkaRenk());
      cz.paletAyarla(D.palet, D.bantli);
      if (hafif) {
        const mt = rgbDizi(cssRenk(kokEl, "--metin", "#15213a"));
        cz.degerliCizgi(eksenN, { mvp: km.mvp, olcek: s, lo: aralik[0], hi: aralik[1] });
        if (D.hayalet && s > 0) cz.duz(hayaletN, { mvp: km.mvp, olcek: 0, renk: mt.concat([0.3]) });
        secimKirli = true;
        isaretleriYerlestir(km);
        sonKare = performance.now() - t0;
        return;
      }
      cz.yuzey(gpu, { mvp: km.mvp, olcek: s, isik: isik, lo: aralik[0], hi: aralik[1], ofset: true });
      if (D.doseme === "w" || D.doseme === "mx" || D.doseme === "my") {
        plaklar.forEach(function (p) { if (plakGorunur(p.pn)) cz.yuzey(p.n, { mvp: km.mvp, olcek: s, isik: isik, lo: plakAralik[0], hi: plakAralik[1], opak: 1 }); });
      } else if (D.doseme === "payi") {
        payiN.forEach(function (n, i) { cz.duz(n, { mvp: km.mvp, olcek: 0, renk: rgbDizi(KATEGORI[i]).concat([0.55]) }, cz.gl.TRIANGLES); });
      }
      if (radyeN && D.radye !== "kapali") cz.yuzey(radyeN.n, { mvp: km.mvp, olcek: s, isik: isik, lo: radyeAralik[0], hi: radyeAralik[1] });
      const metin = rgbDizi(cssRenk(kokEl, "--metin", "#15213a"));
      if (D.hayalet && s > 0) cz.duz(hayaletN, { mvp: km.mvp, olcek: 0, renk: metin.concat([0.35]) });
      cz.duz(uzerindeN, { mvp: km.mvp, olcek: s, renk: metin.concat([0.55]) });
      cz.duz(secimN, { mvp: km.mvp, olcek: s, renk: metin.concat([1]), ustte: false });
      secimKirli = true;
      isaretleriYerlestir(km);
      sonKare = performance.now() - t0;
      if (D.anim && !kapali) {
        D.animFaz += 0.06;
        iste();
      }
    }
    function noktaKonumu(ei, k, y, z, s) {
      const e = els[ei], u = (e.u && e.u[k]) || [0, 0, 0], x = e.x[k];
      y = y || 0; z = z || 0;
      return [0, 1, 2].map(function (c) { return e.i[c] + x * e.yerel.x[c] + y * e.yerel.y[c] + z * e.yerel.z[c] + s * u[c]; });
    }
    function isaretleriYerlestir(km) {
      km = km || kameraMatrisi(kam, en, boy);
      const s = etkinOlcek();
      [[R.mx, ekst && ekst.max], [R.mn, ekst && ekst.min]].forEach(function (c) {
        const el = c[0], x = c[1];
        if (!x || !gorunur || !gorunur[x.el]) { el.hidden = true; return; }
        const p = izdusur(km, noktaKonumu(x.el, x.k, x.y, x.z, s), en, boy);
        if (!p) { el.hidden = true; return; }
        el.hidden = false;
        el.style.transform = "translate(" + (p[0] / dpr).toFixed(1) + "px," + (p[1] / dpr).toFixed(1) + "px)";
      });
    }

    // ---------------- SVG yedek çizim ----------------
    function svgCiz() {
      const r = R.sahne.getBoundingClientRect();
      const w = Math.max(1, r.width), h = Math.max(1, r.height);
      en = w; boy = h; dpr = 1;
      const km = kameraMatrisi(kam, w, h), s = etkinOlcek();
      const parca = [];
      for (let ei = 0; ei < els.length; ei++) {
        if (!gorunur || !gorunur[ei]) continue;
        const e = els[ei], tab = [];
        for (let k = 0; k < e.x.length; k++) tab.push(BUYUKLUK[D.buyukluk].lif ? Math.max(lifUc(e, k, 1), -1e300) : istasyonDegeri(e, D.buyukluk, k));
        let onceki = izdusur(km, noktaKonumu(ei, 0, 0, 0, s), w, h);
        for (let k = 1; k < e.x.length; k++) {
          const p = izdusur(km, noktaKonumu(ei, k, 0, 0, s), w, h);
          if (p && onceki) {
            const v = tab[k] != null && tab[k - 1] != null ? (tab[k] + tab[k - 1]) / 2 : null;
            const c = degerRengi(v, aralik[0], aralik[1], D.palet, D.bantli);
            parca.push({ d: (p[2] + onceki[2]) / 2, h: '<line x1="' + onceki[0].toFixed(1) + '" y1="' + onceki[1].toFixed(1) + '" x2="' + p[0].toFixed(1) + '" y2="' + p[1].toFixed(1) +
              '" stroke="' + (c ? renkHex(c) : "#999") + '" data-el="' + ei + '"' + (D.secili[ei] ? ' class="isi-svg-secili"' : "") + "/>" });
          }
          onceki = p;
        }
      }
      parca.sort(function (a, b) { return b.d - a.d; });
      R.svg.setAttribute("viewBox", "0 0 " + w.toFixed(0) + " " + h.toFixed(0));
      R.svg.innerHTML = '<g class="isi-svg-cubuk">' + parca.map(function (p) { return p.h; }).join("") + "</g>";
    }
    function lifUc(e, k, isaret) {
      const an = kesitAnahat(e.kesit, false), u = kesitUcLifleri(an, e.kesit || {}, e.N[k] || 0, e.My[k] || 0, e.Mz[k] || 0);
      return isaret > 0 ? u.cekme.s : u.basinc.s;
    }

    // ---------------- seçim (picking) ve sonda ----------------
    function kimlikAl(sx, sy) {
      if (svgMod) {
        const el = document.elementFromPoint(sx, sy);
        const d = el && el.getAttribute && el.getAttribute("data-el");
        return d != null ? { tur: "el", ei: +d } : null;
      }
      const r = R.tuval.getBoundingClientRect();
      const x = Math.round((sx - r.left) * dpr), y = Math.round((sy - r.top) * dpr);
      if (x < 0 || y < 0 || x >= en || y >= boy) return null;
      if (secimKirli) {
        const km = kameraMatrisi(kam, en, boy), s = etkinOlcek();
        cz.secimHazirla(en, boy);
        cz.secimCiz(gpu, { mvp: km.mvp, olcek: s });
        if (D.doseme === "w" || D.doseme === "mx" || D.doseme === "my") plaklar.forEach(function (p) { if (plakGorunur(p.pn)) cz.secimCiz(p.n, { mvp: km.mvp, olcek: s }); });
        if (D.doseme === "payi") plaklar.forEach(function (p) { if (plakGorunur(p.pn)) cz.secimCiz(p.n, { mvp: km.mvp, olcek: 0 }); });
        if (radyeN && D.radye !== "kapali") cz.secimCiz(radyeN.n, { mvp: km.mvp, olcek: s });
        secimKirli = false;
      }
      const id = cz.pikselOku(x, y);
      if (id >= 1 && id <= els.length) return { tur: "el", ei: id - 1 };
      if (id >= PANEL_KIMLIK0 && id < PANEL_KIMLIK0 + plaklar.length) return { tur: "panel", pi: id - PANEL_KIMLIK0 };
      if (id === RADYE_KIMLIK) return { tur: "radye" };
      return null;
    }
    /** Ekran noktasına en yakın istasyon aralığı: x ve değer (doğrusal ara değer). */
    function elemanUzerindeX(ei, sx, sy) {
      const r = R.sahne.getBoundingClientRect();
      const px = (sx - r.left) * dpr, py = (sy - r.top) * dpr;
      const km = kameraMatrisi(kam, en, boy), s = etkinOlcek(), e = els[ei];
      let en_ = { d: Infinity, x: 0, k: 0, t: 0 };
      let onceki = izdusur(km, noktaKonumu(ei, 0, 0, 0, s), en, boy);
      for (let k = 1; k < e.x.length; k++) {
        const p = izdusur(km, noktaKonumu(ei, k, 0, 0, s), en, boy);
        if (p && onceki) {
          const ax = p[0] - onceki[0], ay = p[1] - onceki[1], l2 = ax * ax + ay * ay;
          const t = l2 > 0 ? Math.max(0, Math.min(1, ((px - onceki[0]) * ax + (py - onceki[1]) * ay) / l2)) : 0;
          const qx = onceki[0] + t * ax - px, qy = onceki[1] + t * ay - py, d = qx * qx + qy * qy;
          if (d < en_.d) en_ = { d: d, x: e.x[k - 1] + t * (e.x[k] - e.x[k - 1]), k: k - 1, t: t };
        }
        onceki = p;
      }
      return en_;
    }
    function sondaGoster(sx, sy) {
      const h = kimlikAl(sx, sy);
      const r = R.sahne.getBoundingClientRect();
      let metin = null;
      let yeniUzerinde = -1;
      if (h && h.tur === "el") {
        const e = els[h.ei], b = BUYUKLUK[D.buyukluk], q = elemanUzerindeX(h.ei, sx, sy);
        yeniUzerinde = h.ei;
        let v;
        if (b.lif) {
          const a = lifUc(e, q.k, 1), c = lifUc(e, Math.min(e.x.length - 1, q.k + 1), 1);
          const a2 = lifUc(e, q.k, -1), c2 = lifUc(e, Math.min(e.x.length - 1, q.k + 1), -1);
          v = "σ_çekme " + fmt(a + (c - a) * q.t, 4) + " / σ_basınç " + fmt(a2 + (c2 - a2) * q.t, 4) + " MPa";
        } else {
          const a = istasyonDegeri(e, D.buyukluk, q.k), c = istasyonDegeri(e, D.buyukluk, Math.min(e.x.length - 1, q.k + 1));
          v = b.kisa + " = " + (a == null || c == null ? "—" : fmt(a + (c - a) * q.t, 4) + (b.birim ? " " + b.birim : ""));
        }
        metin = "<b>" + kacis(elemanAdi(e)) + "</b><br>x = " + fmt(q.x, 3) + " / " + fmt(e.L, 3) + " m<br>" + kacis(v) +
          (e.kesit && e.kesit.ad ? "<br><span class='isi-soluk'>" + kacis(e.kesit.ad) + "</span>" : "");
      } else if (h && h.tur === "panel") {
        const pn = plaklar[h.pi].pn, nokta = zeminNoktasi(sx, sy, pn.z);
        let v = "";
        if (nokta && (D.doseme === "w" || D.doseme === "mx" || D.doseme === "my")) {
          const g = pn.izgara;
          const i = Math.max(0, Math.min(g.nx - 1, Math.round((nokta[0] - g.x[0]) / (g.x[g.nx - 1] - g.x[0]) * (g.nx - 1))));
          const j = Math.max(0, Math.min(g.ny - 1, Math.round((nokta[1] - g.y[0]) / (g.y[g.ny - 1] - g.y[0]) * (g.ny - 1))));
          const pv = plakDegeri(pn, D.doseme, i, j);
          v = { w: "w", mx: "m_x", my: "m_y" }[D.doseme] + " = " + fmt(pv, 4) + (D.doseme === "w" ? " mm" : " kN·m/m");
        } else if (nokta && D.doseme === "payi") {
          (pn.yuk_payi || []).forEach(function (yp) {
            if (yp.poligon && yp.poligon.length > 2 && cokgenIcinde(nokta, yp.poligon)) {
              v = "→ kiriş " + (yp.kiris != null ? yp.kiris : "?") + " (" + (yp.kenar || "") + ", " + (yp.sekil || "") + "), pay alanı " + fmt(yp.alan, 3) + " m²";
            }
          });
        }
        metin = "<b>Döşeme " + kacis(pn.adres || pn.no) + "</b><br>q = " + fmt(pn.izgara.q, 4) + " kN/m²" + (v ? "<br>" + kacis(v) : "") +
          (pn.alfa ? "<br><span class='isi-soluk'>α_x = " + fmt(pn.alfa.x, 3) + ", α_y = " + fmt(pn.alfa.y, 3) + " (basit mesnetli)</span>" : "");
      } else if (h && h.tur === "radye") {
        const rd = alan.radye, nokta = zeminNoktasi(sx, sy, rd.z || 0);
        let en_ = null, ed = Infinity;
        if (nokta) rd.dugumler.forEach(function (d) { const m = Math.hypot(d.X - nokta[0], d.Y - nokta[1]); if (m < ed) { ed = m; en_ = d; } });
        metin = "<b>Radye</b>" + (en_ ? "<br>düğüm " + en_.no + ": p = " + fmt(en_.p, 4) + " kN/m², w = " + fmt(en_.w * 1000, 4) + " mm" : "");
      }
      if (yeniUzerinde !== D.uzerinde) { D.uzerinde = yeniUzerinde; secimKur(); iste(); }
      if (!metin) { R.sonda.hidden = true; return; }
      R.sonda.innerHTML = metin;
      R.sonda.hidden = false;
      const x = sx - r.left + 14, y = sy - r.top + 14;
      R.sonda.style.left = Math.min(x, r.width - 200) + "px";
      R.sonda.style.top = Math.min(y, r.height - 80) + "px";
    }
    function zeminNoktasi(sx, sy, z) {
      const r = R.sahne.getBoundingClientRect();
      const km = kameraMatrisi(kam, en, boy);
      const nx = ((sx - r.left) / r.width) * 2 - 1, ny = 1 - ((sy - r.top) / r.height) * 2;
      let o, d;
      if (kam.orto) {
        o = [0, 1, 2].map(function (c) { return km.goz[c] + nx * km.yariX * km.sag[c] + ny * km.yariY * km.yukari[c]; });
        d = km.ileri;
      } else {
        o = km.goz;
        const t = Math.tan(kam.fov / 2), asp = r.width / Math.max(1, r.height);
        d = v3Bir([0, 1, 2].map(function (c) { return km.ileri[c] + nx * t * asp * km.sag[c] + ny * t * km.yukari[c]; }));
      }
      if (Math.abs(d[2]) < 1e-9) return null;
      const t = (z - o[2]) / d[2];
      return t > 0 ? [o[0] + t * d[0], o[1] + t * d[1]] : null;
    }
    function sec(ei, ek) {
      if (ei == null || ei < 0 || ei >= els.length) { D.secili = {}; }
      else if (ek) { if (D.secili[ei]) delete D.secili[ei]; else D.secili[ei] = true; }
      else { D.secili = {}; D.secili[ei] = true; }
      secimKur();
      iste();
      if (ei != null && ei >= 0 && els[ei]) {
        const e = els[ei];
        duyur(elemanAdi(e) + ". " + elemanOzeti(e));
        if (olay.elemanSec) {
          try { olay.elemanSec(e.no, { no: e.no, bina_no: e.bina_no, tur: e.tur, adres: e.adres, kat: e.kat }); } catch (er) { /* dış hata */ }
        }
      }
      if (svgMod) svgCiz();
    }
    function elemanOzeti(e) {
      const b = BUYUKLUK[D.buyukluk], x = e.ekstremum && e.ekstremum[D.buyukluk === "u" ? "u" : D.buyukluk];
      if (x) return b.etiket + ": en büyük |değer| " + fmt(D.buyukluk.charAt(0) === "u" ? x.deger * 1000 : x.deger, 4) + (b.birim ? " " + b.birim : "") + ", x = " + fmt(x.x, 3) + " m";
      return "";
    }
    function duyur(m) { R.canli.textContent = m; }
    function seciliIlk() { const k = Object.keys(D.secili); return k.length ? +k[0] : -1; }
    function sonrakiGorunur(ei, yon) {
      if (!els.length) return -1;
      let i = ei;
      for (let n = 0; n < els.length; n++) {
        i = (i + yon + els.length) % els.length;
        if (i < 0) i = 0;
        if (gorunur[i]) return i;
      }
      return -1;
    }

    // ---------------- etkileşim ----------------
    const isaretciler = new Map();
    let surukle = null, sonDokunma = 0, sonDokunmaEl = -1, sondaBekle = 0;
    const hedefYuzey = svgMod ? R.svg : R.tuval;
    dinle(hedefYuzey, "contextmenu", function (e) { e.preventDefault(); });
    dinle(hedefYuzey, "pointerdown", function (e) {
      hedefYuzey.focus({ preventScroll: true });
      try { hedefYuzey.setPointerCapture(e.pointerId); } catch (er) { /* yok */ }
      isaretciler.set(e.pointerId, { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, t0: performance.now() });
      surukle = { kaydir: e.button === 2 || e.button === 1 || e.shiftKey || e.ctrlKey, hareket: 0 };
      if (isaretciler.size === 2) {
        const p = Array.from(isaretciler.values());
        surukle.cimdik = { d: Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y), mx: (p[0].x + p[1].x) / 2, my: (p[0].y + p[1].y) / 2 };
      }
    });
    function kaydir(dx, dy) {
      const r = R.sahne.getBoundingClientRect();
      const km = kameraMatrisi(kam, en, boy);
      const olc = 2 * km.yariY / Math.max(1, r.height);
      for (let c = 0; c < 3; c++) kam.hedef[c] += (-dx * km.sag[c] + dy * km.yukari[c]) * olc;
    }
    function yakinlas(f, sx, sy) {
      const r = R.sahne.getBoundingClientRect();
      if (sx != null) {
        const km = kameraMatrisi(kam, en, boy);
        const nx = ((sx - r.left) / r.width) * 2 - 1, ny = 1 - ((sy - r.top) / r.height) * 2;
        for (let c = 0; c < 3; c++) kam.hedef[c] += (nx * km.yariX * km.sag[c] + ny * km.yariY * km.yukari[c]) * (1 - f);
      }
      kam.uzak = Math.max(kam.R * 0.02, Math.min(kam.R * 40, kam.uzak * f));
      secimKirli = true;
      iste();
    }
    dinle(hedefYuzey, "pointermove", function (e) {
      const p = isaretciler.get(e.pointerId);
      if (!p) {
        if (e.pointerType === "mouse" && !sondaBekle) {
          const sx = e.clientX, sy = e.clientY;
          sondaBekle = requestAnimationFrame(function () { sondaBekle = 0; if (!kapali) sondaGoster(sx, sy); });
        }
        return;
      }
      const dx = e.clientX - p.x, dy = e.clientY - p.y;
      p.x = e.clientX; p.y = e.clientY;
      surukle.hareket += Math.abs(dx) + Math.abs(dy);
      if (isaretciler.size >= 2 && surukle.cimdik) {
        const q = Array.from(isaretciler.values());
        const d = Math.hypot(q[0].x - q[1].x, q[0].y - q[1].y), mx = (q[0].x + q[1].x) / 2, my = (q[0].y + q[1].y) / 2;
        if (d > 0 && surukle.cimdik.d > 0) yakinlas(surukle.cimdik.d / d, mx, my);
        kaydir(mx - surukle.cimdik.mx, my - surukle.cimdik.my);
        surukle.cimdik = { d: d, mx: mx, my: my };
      } else if (surukle.kaydir) {
        kaydir(dx, dy);
      } else {
        kam.yaw -= dx * 0.008;
        kam.pitch = Math.max(-Math.PI / 2 + 1e-4, Math.min(Math.PI / 2 - 1e-4, kam.pitch + dy * 0.008));
      }
      R.sonda.hidden = true;
      secimKirli = true;
      iste();
    });
    function birak(e) {
      const p = isaretciler.get(e.pointerId);
      isaretciler.delete(e.pointerId);
      if (!p || !surukle) return;
      const tik = surukle.hareket < 6 && performance.now() - p.t0 < 600 && isaretciler.size === 0 && !surukle.cimdik;
      if (tik) {
        const h = kimlikAl(e.clientX, e.clientY);
        const simdi = performance.now();
        if (h && h.tur === "el") {
          if (simdi - sonDokunma < 380 && sonDokunmaEl === h.ei) { sec(h.ei, false); incele(h.ei); }
          else sec(h.ei, e.shiftKey || e.ctrlKey || e.metaKey);
          sonDokunma = simdi; sonDokunmaEl = h.ei;
          if (e.pointerType !== "mouse") sondaGoster(e.clientX, e.clientY);
        } else if (!e.shiftKey) { sec(null); R.sonda.hidden = true; }
      }
      if (isaretciler.size === 0) { surukle = null; hizliBitir(); }
    }
    dinle(hedefYuzey, "pointerup", birak);
    dinle(hedefYuzey, "pointercancel", birak);
    dinle(hedefYuzey, "pointerleave", function (e) { if (e.pointerType === "mouse" && !isaretciler.size) { R.sonda.hidden = true; if (D.uzerinde >= 0) { D.uzerinde = -1; secimKur(); iste(); } } });
    dinle(hedefYuzey, "wheel", function (e) {
      e.preventDefault();
      yakinlas(Math.exp(Math.max(-0.5, Math.min(0.5, e.deltaY * (e.deltaMode === 1 ? 0.05 : 0.0015)))), e.clientX, e.clientY);
    }, { passive: false });
    dinle(hedefYuzey, "keydown", function (e) {
      const k = e.key;
      if (k === "ArrowRight" || k === "ArrowDown" || k === "ArrowLeft" || k === "ArrowUp") {
        e.preventDefault();
        const yon = k === "ArrowRight" || k === "ArrowDown" ? 1 : -1;
        const s = sonrakiGorunur(seciliIlk() < 0 ? (yon > 0 ? -1 : 0) : seciliIlk(), yon);
        if (s >= 0) sec(s, false);
      } else if (k === "Enter") {
        e.preventDefault();
        if (seciliIlk() >= 0) incele(seciliIlk());
      } else if (k === "Escape") {
        if (EG && EG.acik()) EG.kapat(); else sec(null);
      } else if (k === "+" || k === "=") { yakinlas(0.85); }
      else if (k === "-" || k === "_") { yakinlas(1 / 0.85); }
      else if (k === "Home" || k === "f") { gorunumAyarla("sigdir"); }
    });
    // ---- denetimler ----
    dinle(R.buyukluk, "change", function () { D.buyukluk = R.buyukluk.value; degerGuncelle(); });
    dinle(R.durum, "change", function () { if (olay.durumSec) olay.durumSec(R.durum.value); });
    kokEl.querySelectorAll(".isi-seg").forEach(function (seg) {
      dinle(seg, "click", function (e) {
        const b = e.target.closest("button[data-v]");
        if (!b) return;
        const v = b.getAttribute("data-v"), tur = seg.getAttribute("data-seg");
        if (tur === "renk") {
          D.bantli = v !== "surekli"; D.palet = v === "iki" ? "iki" : "klasik";
          if (v === "surekli") D.palet = D.palet === "iki" ? "iki" : "klasik";
          seg.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
          degerGuncelle(); plakDegerleri(); lejantCiz();
        } else if (tur === "gorunum") {
          gorunumAyarla(v, true);
        } else if (tur === "cizim") {
          D.tup = v === "tup";
          seg.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
          agKur();
        }
      });
    });
    dinle(R.olcekMod, "change", function () {
      D.elle = R.olcekMod.value === "elle";
      R.olcekMin.disabled = R.olcekMax.disabled = !D.elle;
      if (D.elle) { D.elleMin = aralik[0]; D.elleMax = aralik[1]; }
      degerGuncelle();
    });
    function elleOku() {
      const a = sayiOku(R.olcekMin.value), b = sayiOku(R.olcekMax.value);
      if (a != null && b != null && b > a) { D.elleMin = a; D.elleMax = b; R.olcekMin.removeAttribute("aria-invalid"); R.olcekMax.removeAttribute("aria-invalid"); degerGuncelle(); }
      else { R.olcekMax.setAttribute("aria-invalid", "true"); }
    }
    dinle(R.olcekMin, "change", elleOku);
    dinle(R.olcekMax, "change", elleOku);
    function defKaydirici() {
      const v = +R.defOlcek.value;                   // 0…100 → 0, sonra 10^((v−50)/25) (×0,01 … ×100 otomatik)
      D.olcekCarpan = v <= 0 ? 0 : Math.pow(10, (v - 50) / 25);
      D.gercek = false;
      R.defCikti.textContent = defOlcekMetni();
      secimKirli = true;
      isaretleriYerlestir();
      bilgiYaz();
      iste();
    }
    dinle(R.defOlcek, "input", defKaydirici);
    dinle(R.deforme, "change", function () { D.deforme = R.deforme.checked; R.defCikti.textContent = defOlcekMetni(); secimKirli = true; bilgiYaz(); iste(); });
    dinle($("[data-isi=gercek]"), "click", function () { D.gercek = true; D.deforme = true; R.deforme.checked = true; R.defCikti.textContent = defOlcekMetni(); secimKirli = true; bilgiYaz(); iste(); });
    dinle(R.anim, "click", function () {
      if (azHareket()) { duyur("Hareket azaltma tercihi açık: canlandırma kapalı."); return; }
      D.anim = !D.anim;
      R.anim.setAttribute("aria-pressed", D.anim ? "true" : "false");
      R.anim.textContent = D.anim ? "❚❚ Durdur" : "▶ Canlandır";
      D.animFaz = 0;
      secimKirli = true;
      iste();
    });
    dinle(R.hayalet, "change", function () { D.hayalet = R.hayalet.checked; iste(); });
    dinle(R.persp, "change", function () { D.perspektif = R.persp.checked; kam.orto = !D.perspektif; secimKirli = true; iste(); });
    dinle(R.kat, "change", function () { D.kat = R.kat.value; if (!svgMod) plakKur(); gorunurlukGuncelle(); });
    dinle(R.aks, "change", function () { D.aks = R.aks.value; gorunurlukGuncelle(); });
    dinle($("[data-isi=yalit]"), "click", function () {
      const k = Object.keys(D.secili);
      if (!k.length) { duyur("Önce bir ya da daha çok eleman seçin (Shift ile çoklu seçim)."); return; }
      D.yalit = {}; k.forEach(function (i) { D.yalit[i] = true; });
      gorunurlukGuncelle(); gorunumAyarla("sigdir");
    });
    dinle($("[data-isi=gizle]"), "click", function () {
      Object.keys(D.secili).forEach(function (i) { D.gizli[i] = true; });
      D.secili = {};
      gorunurlukGuncelle();
    });
    dinle($("[data-isi=tumu]"), "click", function () {
      D.gizli = {}; D.yalit = null; D.kat = ""; D.aks = ""; R.kat.value = ""; R.aks.value = "";
      if (!svgMod) plakKur();
      gorunurlukGuncelle();
    });
    dinle(R.doseme, "change", function () { D.doseme = R.doseme.value; plakDegerleri(); lejantCiz(); secimKirli = true; iste(); });
    dinle(R.radye, "change", function () { D.radye = R.radye.value; plakDegerleri(); lejantCiz(); secimKirli = true; iste(); });
    dinle($("[data-isi=incele]"), "click", function () {
      const s = seciliIlk();
      if (s < 0) { duyur("İncelemek için bir eleman seçin (tıklayın ya da ok tuşlarıyla gezinin)."); return; }
      incele(s);
    });
    dinle($("[data-isi=png]"), "click", function () {
      const url = goruntuAl();
      if (!url) return;
      const a = document.createElement("a");
      a.href = url; a.download = "isi-haritasi-" + String(alan.durum || "durum").replace(/[^\w+-]/g, "_") + ".png";
      document.body.appendChild(a); a.click(); a.remove();
    });
    dinle($("[data-isi=kapat]"), "click", function () { kapat(); if (olay.kapat) olay.kapat(); });
    let ro = null;
    if (kok.ResizeObserver) { ro = new ResizeObserver(function () { boyutla(); if (EG) EG.boyutla(); }); ro.observe(R.sahne); }
    else dinle(kok, "resize", boyutla);

    // ---------------- görüntü al ----------------
    function goruntuAl() {
      if (EG && EG.acik()) return EG.goruntuAl();
      if (svgMod) {
        const s = new XMLSerializer().serializeToString(R.svg);
        return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s);
      }
      ciz();
      const tv = document.createElement("canvas");
      const lw = Math.round(170 * dpr);
      tv.width = en + lw; tv.height = boy;
      const c = tv.getContext("2d");
      const ar = arkaRenk();
      c.fillStyle = "rgb(" + ar.map(function (v) { return Math.round(v * 255); }).join(",") + ")";
      c.fillRect(0, 0, tv.width, tv.height);
      c.drawImage(R.tuval, lw, 0);
      lejantTuvale(c, 10 * dpr, 14 * dpr, dpr, BUYUKLUK[D.buyukluk], aralik, cssRenk(kokEl, "--metin", "#15213a"));
      return tv.toDataURL("image/png");
    }
    function lejantTuvale(c, x, y, o, b, ar, renk) {
      c.fillStyle = renk;
      c.font = (13 * o) + "px sans-serif";
      c.fillText(b.kisa + birimMetni(b), x, y + 10 * o);
      c.font = (11 * o) + "px sans-serif";
      c.fillText(String(alan.durum || ""), x, y + 26 * o);
      const sin = lejantSinirlari(ar[0], ar[1], BANT), h = 20 * o, y0 = y + 40 * o;
      for (let i = 0; i < BANT; i++) {
        c.fillStyle = renkHex(renkAl((BANT - 1 - i + 0.5) / BANT, D.palet, D.bantli));
        c.fillRect(x, y0 + i * h, 22 * o, h - 1);
      }
      c.fillStyle = renk;
      for (let i = 0; i <= BANT; i++) c.fillText(fmt(sin[i], 4), x + 28 * o, y0 + i * h + 4 * o);
      if (ekst && ekst.max) c.fillText("MX " + ekstMetni(ekst.max, ""), x, y0 + (BANT + 1) * h + 6 * o);
      if (ekst && ekst.min) c.fillText("MN " + ekstMetni(ekst.min, ""), x, y0 + (BANT + 1) * h + 22 * o);
    }

    // =====================================================================================
    // 11. Eleman görünümü
    // =====================================================================================
    function incele(ei) {
      if (ei == null || ei < 0 || !els[ei]) return;
      if (!EG) EG = ElemanGorunumu();
      EG.ac(ei);
    }
    function ElemanGorunumu() {
      const kab = R.eleman;
      kab.innerHTML = '' +
        '<div class="isi-el-ust">' +
        '<div class="isi-el-gez"><button type="button" class="dugme kucuk" data-e="onceki" aria-label="Önceki eleman">‹</button>' +
        '<div class="isi-el-baslik"></div>' +
        '<button type="button" class="dugme kucuk" data-e="sonraki" aria-label="Sonraki eleman">›</button></div>' +
        '<div class="isi-el-denetim">' +
        '<label class="isi-etiket">Yüzey <select class="girdi isi-kucuk" data-e="renk"><option value="sigma_lif">σ_x lif gerilmesi</option><option value="vm_lif">von Mises (lif)</option></select></label>' +
        '<label class="isi-onay" title="Elemanı kesit konumunda kes: bu konumdan sonrası gizlenir, kesit yüzü gerilmeyle boyanır"><input type="checkbox" data-e="kes"> Kesitte aç</label>' +
        '<button type="button" class="dugme kucuk" data-e="tasarim" hidden>Tasarım ayrıntısı</button>' +
        '<button type="button" class="dugme kucuk" data-e="kapat">Yapıya dön</button>' +
        "</div></div>" +
        '<p class="isi-el-not not" hidden></p>' +
        '<div class="isi-el-govde">' +
        '<div class="isi-el-3b"><canvas class="isi-el-tuval" tabindex="0" aria-label="Eleman katı görünümü: sürükle döndür, tekerlek yakınlaştır"></canvas>' +
        '<svg class="isi-el-svg" hidden></svg><div class="isi-lejant isi-el-lejant"></div></div>' +
        '<div class="isi-el-kesit"><div class="isi-el-kesit-ust"><b>Kesit</b> <span class="isi-el-kx"></span></div>' +
        '<canvas class="isi-kesit-tuval" role="img" aria-label="Kesit gerilme haritası"></canvas>' +
        '<label class="isi-etiket isi-x-etiket">Kesit konumu x <input type="range" class="isi-aralik" data-e="x" min="0" max="1000" value="500"></label>' +
        '<div class="isi-kesit-bilgi"></div></div>' +
        '<div class="isi-el-grafikler" aria-label="Eleman boyunca iç kuvvet ve sehim grafikleri"></div>' +
        '<div class="isi-el-tablolar"></div>' +
        "</div>";
      function q(s) { return kab.querySelector(s); }
      const E = {
        baslik: q(".isi-el-baslik"), renk: q("[data-e=renk]"), kes: q("[data-e=kes]"), x: q("[data-e=x]"), tuval: q(".isi-el-tuval"), svg: q(".isi-el-svg"),
        lejant: q(".isi-el-lejant"), kTuval: q(".isi-kesit-tuval"), kBilgi: q(".isi-kesit-bilgi"), kx: q(".isi-el-kx"), grafik: q(".isi-el-grafikler"),
        tablo: q(".isi-el-tablolar"), not: q(".isi-el-not"), tasarim: q("[data-e=tasarim]"), kutu3: q(".isi-el-3b"),
      };
      let ecz = null;
      try { ecz = new Cizici(E.tuval); } catch (er) { ecz = null; }
      if (!ecz) { E.tuval.hidden = true; E.svg.removeAttribute("hidden"); }
      const ek = { hedef: [0, 0, 0], uzak: 5, yaw: 0, pitch: 0.4, fov: 30 * Math.PI / 180, orto: false, R: 1 };
      let ei = -1, eag = null, en_ = null, ex = 0.5, eEn = 1, eBoy = 1, eDpr = 1, eIstek = 0, eAralik = [0, 1], an = null, kapakN = null, halkaN = null, eV = null;
      let surk = null;
      const ptr = new Map();
      function acik() { return !kab.hidden; }
      function e_() { return els[ei]; }
      function ac(i) {
        ei = i;
        kab.hidden = false;
        kokEl.classList.add("isi-el-acik");
        const e = e_();
        E.baslik.innerHTML = "<b>" + kacis(elemanAdi(e)) + "</b> <span class='isi-soluk'>" + kacis((e.kesit && e.kesit.ad) || "") + " · L = " + fmt(e.L, 4) + " m · " +
          kacis(alan.durum || "") + "</span>";
        const notlar = [];
        if (alan.zarf) notlar.push("Zarf: iç kuvvetler her istasyonda farklı kombinasyonlardan gelebilir; lif gerilmesi bu kuvvetlerle hesaplanır, eş zamanlı değildir.");
        if (e.kesit && e.kesit.not) notlar.push(e.kesit.not);
        if (alan.not && e.kesit && e.kesit.malzeme && e.kesit.malzeme.tur === "beton") notlar.push(alan.not);
        E.not.textContent = notlar.join(" ");
        E.not.hidden = !notlar.length;
        E.tasarim.hidden = !(olay.tasarim && e.tasarim);
        an = kesitAnahat(e.kesit, false);
        if (ecz) {
          if (en_) ecz.sil(en_);
          eag = cubukAgi(els, { liste: [ei], bol: 4 });
          const xa = new Float32Array(eag.kose);
          for (let v = 0; v < eag.kose; v++) xa[v] = e.x[eag.vSt[v]];
          en_ = ecz.nesne(eag, xa);
          eV = new Float32Array(eag.kose);
        }
        // kamera: elemana yandan ve hafif üstten bak
        const ey = e.yerel.y, ez = e.yerel.z, exv = e.yerel.x;
        const d = v3Bir([0.6 * ez[0] + 0.4 * ey[0] + 0.18 * exv[0], 0.6 * ez[1] + 0.4 * ey[1] + 0.18 * exv[1], 0.6 * ez[2] + 0.4 * ey[2] + 0.18 * exv[2]]);
        ek.pitch = Math.asin(Math.max(-0.999, Math.min(0.999, d[2])));
        ek.yaw = Math.atan2(d[1], d[0]);
        const s = etkinOlcek();
        const p0 = noktaKonumu(ei, 0, 0, 0, s), p1 = noktaKonumu(ei, e.x.length - 1, 0, 0, s);
        const r = Math.max(e.L / 2, (an.dy + an.dz));
        ek.R = r;
        const kmn = [0, 1, 2].map(function (c) { return Math.min(p0[c], p1[c]) - (an.dy + an.dz) / 2; });
        const kmx = [0, 1, 2].map(function (c) { return Math.max(p0[c], p1[c]) + (an.dy + an.dz) / 2; });
        const b3 = E.kutu3.getBoundingClientRect();
        ek.asp = b3.width / Math.max(1, b3.height) || 1.5;
        sigdir(ek, kmn, kmx);
        ex = e.L / 2;
        E.x.value = 500;
        boyutla();
        guncelle();
        kab.focus({ preventScroll: true });
        duyur("İnceleme: " + elemanAdi(e) + ". " + elemanOzeti(e));
      }
      function kapatEG() {
        kab.hidden = true;
        kokEl.classList.remove("isi-el-acik");
        R.tuval.focus({ preventScroll: true });
      }
      function boyutla() {
        if (!acik()) return;
        const r = E.kutu3.getBoundingClientRect();
        ek.asp = r.width / Math.max(1, r.height);
        eDpr = Math.min(2, kok.devicePixelRatio || 1);
        eEn = Math.max(1, Math.round(r.width * eDpr)); eBoy = Math.max(1, Math.round(r.height * eDpr));
        if (ecz && (E.tuval.width !== eEn || E.tuval.height !== eBoy)) { E.tuval.width = eEn; E.tuval.height = eBoy; }
        eIste();
        kesitCiz();
      }
      function guncelle() {
        if (!acik() || ei < 0) return;
        const e = e_();
        if (!e) { kapatEG(); return; }
        // yüzey değerleri
        const ad = E.renk.value, vm = ad === "vm_lif";
        let lo = Infinity, hi = -Infinity;
        for (let k = 0; k < e.x.length; k++) {
          an.parcalar.forEach(function (pr) {
            pr.dis.forEach(function (p) { const s = lifDegeri(e, k, p[0], p[1], vm); lo = Math.min(lo, s); hi = Math.max(hi, s); });
          });
        }
        eAralik = aralikBelirle(lo, hi, D.palet === "iki" && !vm);
        if (ecz) { degerleriDoldur(eag, els, ad, eV); ecz.degerYukle(en_, eV); }
        const b = BUYUKLUK[ad];
        E.lejant.innerHTML = lejantHtml(b.kisa + birimMetni(b), "lif gerilmesi, " + (alan.durum || ""), eAralik[0], eAralik[1], "");
        grafikCiz();
        tabloCiz();
        xAyarla(ex);
      }
      function xAyarla(x) {
        const e = e_();
        ex = Math.max(0, Math.min(e.L, x));
        E.x.value = Math.round(ex / (e.L || 1) * 1000);
        E.kx.textContent = "x = " + fmt(ex, 3) + " m (i ucundan bakış: z′ sağa, y′ yukarı)";
        kapakKur();
        kesitCiz();
        imlecCiz();
        eIste();
      }
      /** x'te istasyon ara değeri (doğrusal). */
      function xDeger(dizi, x) {
        const e = e_(), xs = e.x;
        if (!dizi) return null;
        let k = 0;
        while (k + 1 < xs.length - 1 && xs[k + 1] < x) k++;
        const t = xs[k + 1] > xs[k] ? Math.max(0, Math.min(1, (x - xs[k]) / (xs[k + 1] - xs[k]))) : 0;
        const a = dizi[k], b = dizi[k + 1];
        if (a == null || b == null) return null;
        return a + (b - a) * t;
      }
      function kuvvetX(x) {
        const e = e_();
        return { N: xDeger(e.N, x) || 0, Vy: xDeger(e.Vy, x) || 0, Vz: xDeger(e.Vz, x) || 0, T: xDeger(e.T, x) || 0, My: xDeger(e.My, x) || 0, Mz: xDeger(e.Mz, x) || 0,
          tau: xDeger(e.tau_max, x) || 0 };
      }
      function kapakKur() {
        if (!ecz) return;
        const e = e_(), kv = kuvvetX(ex), vm = E.renk.value === "vm_lif";
        const P = [], Dd = [], Nn = [], Vv = [], Ii = [];
        // x'teki yer değiştirme (ara değer)
        const u = [0, 1, 2].map(function (c) { return xDeger((e.u || []).map(function (q) { return q ? q[c] : 0; }), ex) || 0; });
        an.parcalar.forEach(function (pr) {
          const taban = P.length / 3;
          const ekle = function (p) {
            for (let c = 0; c < 3; c++) P.push(e.i[c] + ex * e.yerel.x[c] + p[0] * e.yerel.y[c] + p[1] * e.yerel.z[c]);
            Dd.push(u[0], u[1], u[2]);
            Nn.push(Math.round(127 * e.yerel.x[0]), Math.round(127 * e.yerel.x[1]), Math.round(127 * e.yerel.x[2]), 0);
            const s = lifGerilmesi(e.kesit, kv.N, kv.My, kv.Mz, p[0], p[1]);
            Vv.push(vm ? Math.sqrt(s * s + 3 * kv.tau * kv.tau) : s);
          };
          pr.dis.forEach(ekle);
          if (pr.ic) {
            pr.ic.forEach(ekle);
            const n = pr.dis.length;
            for (let p = 0; p < n; p++) { const A = taban + p, B = taban + (p + 1) % n, C = taban + n + p, Dq = taban + n + (p + 1) % n; Ii.push(A, B, Dq, A, Dq, C); }
          } else ucgenle(pr.dis).forEach(function (t) { Ii.push(taban + t); });
        });
        if (kapakN) ecz.sil(kapakN);
        const a = { P: new Float32Array(P), D: new Float32Array(Dd), Nr: new Int8Array(Nn), K: new Uint8Array(Nn.length), I: new Uint32Array(Ii), kose: P.length / 3 };
        kapakN = ecz.nesne(a);
        ecz.degerYukle(kapakN, new Float32Array(Vv));
        // kesit konumu halkası (kesit kapalıyken de görünür): anahat kenarları, biraz büyütülmüş
        const Lp = [], Ld = [];
        an.parcalar.forEach(function (pr) {
          const n = pr.dis.length;
          for (let p = 0; p < n; p++) {
            [pr.dis[p], pr.dis[(p + 1) % n]].forEach(function (q) {
              for (let c = 0; c < 3; c++) Lp.push(e.i[c] + ex * e.yerel.x[c] + 1.08 * q[0] * e.yerel.y[c] + 1.08 * q[1] * e.yerel.z[c]);
              Ld.push(u[0], u[1], u[2]);
            });
          }
        });
        if (halkaN) ecz.sil(halkaN);
        halkaN = ecz.cizgiNesnesi(new Float32Array(Lp), new Float32Array(Ld));
      }
      function eIste() {
        if (eIstek || kapali) return;
        eIstek = requestAnimationFrame(function () { eIstek = 0; eCiz(); });
      }
      function eCiz() {
        if (!acik()) return;
        if (!ecz) { eSvgCiz(); return; }
        const km = kameraMatrisi(ek, eEn, eBoy), s = etkinOlcek();
        const isik = v3Bir([-km.ileri[0] + 0.3 * km.yukari[0], -km.ileri[1] + 0.3 * km.yukari[1], -km.ileri[2] + 0.3 * km.yukari[2]]);
        ecz.basla(eEn, eBoy, arkaRenk());
        ecz.paletAyarla(D.palet, D.bantli);
        const kes = E.kes.checked ? ex : null;
        ecz.yuzey(en_, { mvp: km.mvp, olcek: s, isik: isik, lo: eAralik[0], hi: eAralik[1], kes: kes == null ? null : kes + 1e-9 });
        if (E.kes.checked) ecz.yuzey(kapakN, { mvp: km.mvp, olcek: s, isik: [km.ileri[0] * -1, km.ileri[1] * -1, km.ileri[2] * -1], lo: eAralik[0], hi: eAralik[1] });
        ecz.duz(halkaN, { mvp: km.mvp, olcek: s, renk: rgbDizi(cssRenk(kokEl, "--metin", "#15213a")).concat([1]) });
      }
      function eSvgCiz() {
        // WebGL yok: elemanın üst (+y′) ve alt (−y′) lif şeridi
        const e = e_(), w = 600, h = 140, xs = e.x, L = e.L || 1;
        let s = '<rect x="0" y="0" width="' + w + '" height="' + h + '" fill="none"/>';
        [[an.dy / 2, 20], [-an.dy / 2, 80]].forEach(function (lf) {
          for (let k = 0; k + 1 < xs.length; k++) {
            const v = (lifDegeri(e, k, lf[0], 0, false) + lifDegeri(e, k + 1, lf[0], 0, false)) / 2;
            const c = degerRengi(v, eAralik[0], eAralik[1], D.palet, D.bantli);
            s += '<rect x="' + (xs[k] / L * w).toFixed(1) + '" y="' + lf[1] + '" width="' + ((xs[k + 1] - xs[k]) / L * w + 0.5).toFixed(1) + '" height="40" fill="' + (c ? renkHex(c) : "#999") + '"/>';
          }
        });
        s += '<line x1="' + (ex / L * w).toFixed(1) + '" y1="10" x2="' + (ex / L * w).toFixed(1) + '" y2="130" stroke="currentColor" stroke-width="2"/>' +
          '<text x="4" y="14" font-size="12" fill="currentColor">+y′ lifi</text><text x="4" y="134" font-size="12" fill="currentColor">−y′ lifi</text>';
        E.svg.setAttribute("viewBox", "0 0 " + w + " " + h);
        E.svg.innerHTML = s;
      }
      function kesitCiz() {
        const e = e_(), c = E.kTuval;
        const r = c.getBoundingClientRect();
        const o = Math.min(2, kok.devicePixelRatio || 1);
        const W = Math.max(60, Math.round(r.width * o)), H = Math.max(60, Math.round(r.height * o));
        if (c.width !== W || c.height !== H) { c.width = W; c.height = H; }
        const g = c.getContext("2d");
        if (!g) return;
        g.clearRect(0, 0, W, H);
        const kv = kuvvetX(ex), vm = E.renk.value === "vm_lif";
        // kesit kutusu (y yukarı, z sağa)
        let y0 = Infinity, y1 = -Infinity, z0 = Infinity, z1 = -Infinity;
        an.parcalar.forEach(function (pr) { pr.dis.forEach(function (p) { y0 = Math.min(y0, p[0]); y1 = Math.max(y1, p[0]); z0 = Math.min(z0, p[1]); z1 = Math.max(z1, p[1]); }); });
        const pay = 34 * o, olc = Math.min((W - 2 * pay) / Math.max(1e-9, z1 - z0), (H - 2 * pay) / Math.max(1e-9, y1 - y0));
        const cx = W / 2 - (z0 + z1) / 2 * olc, cy = H / 2 + (y0 + y1) / 2 * olc;
        function ekr(y, z) { return [cx + z * olc, cy - y * olc]; }
        // gerilme alanı (piksel ızgarası) → yol ile kırp
        const im = g.createImageData(W, H), d = im.data;
        for (let py = 0; py < H; py++) {
          const y = (cy - py) / olc;
          for (let px = 0; px < W; px++) {
            const z = (px - cx) / olc;
            if (y < y0 - 1e-9 || y > y1 + 1e-9 || z < z0 - 1e-9 || z > z1 + 1e-9) continue;
            let s = lifGerilmesi(e.kesit, kv.N, kv.My, kv.Mz, y, z);
            if (vm) s = Math.sqrt(s * s + 3 * kv.tau * kv.tau);
            const cc = degerRengi(s, eAralik[0], eAralik[1], D.palet, D.bantli) || [150, 150, 150];
            const i = 4 * (py * W + px);
            d[i] = cc[0]; d[i + 1] = cc[1]; d[i + 2] = cc[2]; d[i + 3] = 255;
          }
        }
        const gecici = document.createElement("canvas");
        gecici.width = W; gecici.height = H;
        gecici.getContext("2d").putImageData(im, 0, 0);
        g.save();
        g.beginPath();
        an.parcalar.forEach(function (pr) {
          [pr.dis].concat(pr.ic ? [pr.ic] : []).forEach(function (h) {
            h.forEach(function (p, i) { const s = ekr(p[0], p[1]); if (i) g.lineTo(s[0], s[1]); else g.moveTo(s[0], s[1]); });
            g.closePath();
          });
        });
        g.clip("evenodd");
        g.drawImage(gecici, 0, 0);
        g.restore();
        const metin = cssRenk(kokEl, "--metin", "#15213a");
        g.strokeStyle = metin; g.lineWidth = 1.5 * o;
        g.beginPath();
        an.parcalar.forEach(function (pr) {
          [pr.dis].concat(pr.ic ? [pr.ic] : []).forEach(function (h) {
            h.forEach(function (p, i) { const s = ekr(p[0], p[1]); if (i) g.lineTo(s[0], s[1]); else g.moveTo(s[0], s[1]); });
            g.closePath();
          });
        });
        g.stroke();
        // tarafsız eksen
        const te = tarafsizEksen(e.kesit, kv.N, kv.My, kv.Mz);
        const dy = (y1 - y0) * 0.15, dz = (z1 - z0) * 0.15;
        const seg = dogruKirp(te, y0 - dy, y1 + dy, z0 - dz, z1 + dz);
        let teMetin = "Tarafsız eksen yok (saf eksenel ya da sıfır)";
        if (seg) {
          const a = ekr(seg[0][0], seg[0][1]), b = ekr(seg[1][0], seg[1][1]);
          g.save(); g.setLineDash([6 * o, 4 * o]); g.lineWidth = 2 * o; g.strokeStyle = metin;
          g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); g.restore();
          teMetin = "Tarafsız eksen (σ = 0): kesik çizgi";
        } else if (te) {
          teMetin = "Tarafsız eksen kesit dışında: bütün kesit " + (lifGerilmesi(e.kesit, kv.N, kv.My, kv.Mz, 0, 0) >= 0 ? "çekmede" : "basınçta");
        }
        // en büyük çekme / basınç lifleri
        const ul = kesitUcLifleri(an, e.kesit, kv.N, kv.My, kv.Mz);
        g.font = (11 * o) + "px sans-serif";
        [[ul.cekme, "maks ", "#b0302d"], [ul.basinc, "min ", "#1f56a8"]].forEach(function (u) {
          if (!u[0]) return;
          const p = ekr(u[0].y, u[0].z);
          g.fillStyle = "#fff"; g.strokeStyle = u[2]; g.lineWidth = 2.5 * o;
          g.beginPath(); g.arc(p[0], p[1], 5 * o, 0, 2 * Math.PI); g.fill(); g.stroke();
          g.fillStyle = metin;
          const t = u[1] + (u[0].s > 0 ? "+" : "") + fmt(u[0].s, 4);
          const tx = Math.max(2 * o, Math.min(W - g.measureText(t).width - 2 * o, p[0] + 8 * o));
          g.fillText(t, tx, Math.max(12 * o, Math.min(H - 4 * o, p[1] - 8 * o)));
        });
        // eksen okları
        g.strokeStyle = metin; g.fillStyle = metin; g.lineWidth = 1 * o;
        const ox = 14 * o, oy = H - 14 * o;
        g.beginPath(); g.moveTo(ox, oy); g.lineTo(ox + 22 * o, oy); g.moveTo(ox, oy); g.lineTo(ox, oy - 22 * o); g.stroke();
        g.fillText("z′", ox + 24 * o, oy + 4 * o); g.fillText("y′", ox - 4 * o, oy - 26 * o);
        E.kBilgi.innerHTML = "<div>N = " + fmt(kv.N, 4) + " kN · M_y′ = " + fmt(kv.My, 4) + " · M_z′ = " + fmt(kv.Mz, 4) + " kN·m</div>" +
          "<div>σ çekme (+) " + fmt(ul.cekme && ul.cekme.s, 4) + " MPa · σ basınç (−) " + fmt(ul.basinc && ul.basinc.s, 4) + " MPa</div>" +
          '<div class="isi-soluk">' + kacis(teMetin) + " · σ = N/A − M_z′·y/I_z − M_y′·z/I_y</div>";
      }
      // ---- boyunca grafikler ----
      const GRAF = [["N", "N", "kN"], ["Vy", "V_y′", "kN"], ["Vz", "V_z′", "kN"], ["T", "T", "kN·m"], ["My", "M_y′", "kN·m"], ["Mz", "M_z′", "kN·m"], ["v", "sehim y′", "mm"], ["w", "sehim z′", "mm"]];
      function sehimDizisi(e, c) {
        // kiriş ekseni (uçları birleştiren doğru) göre yerel sehim: u·y′ (ya da z′) − uç değerlerin doğrusal ara değeri
        const ax = c === "v" ? e.yerel.y : e.yerel.z, xs = e.x, L = e.L || xs[xs.length - 1] || 1;
        const d = (e.u || []).map(function (u) { return u ? (u[0] * ax[0] + u[1] * ax[1] + u[2] * ax[2]) * 1000 : 0; });
        const a = d[0] || 0, b = d[d.length - 1] || 0;
        return d.map(function (v, k) { return v - (a + (b - a) * xs[k] / L); });
      }
      function grafikVerisi(e, ad) { return ad === "v" || ad === "w" ? sehimDizisi(e, ad) : e[ad]; }
      function grafikCiz() {
        const e = e_(), xs = e.x, L = e.L || xs[xs.length - 1] || 1;
        const W = 320, H = 92, pl = 46, pr = 8, pt = 16, pb = 16;
        let h = "";
        GRAF.forEach(function (g) {
          const d = grafikVerisi(e, g[0]);
          if (!d) return;
          let lo = 0, hi = 0;
          d.forEach(function (v) { if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); } });
          if (hi - lo < 1e-12) { hi += 1; lo -= 1; }
          const sx = function (x) { return pl + x / L * (W - pl - pr); }, sy = function (v) { return pt + (hi - v) / (hi - lo) * (H - pt - pb); };
          let yol = "", alanYol = "M" + sx(0).toFixed(1) + "," + sy(0).toFixed(1);
          d.forEach(function (v, k) { if (v == null) return; const p = sx(xs[k]).toFixed(1) + "," + sy(v).toFixed(1); yol += (yol ? "L" : "M") + p; alanYol += "L" + p; });
          alanYol += "L" + sx(xs[xs.length - 1]).toFixed(1) + "," + sy(0).toFixed(1) + "Z";
          let imx = 0, imn = 0;
          d.forEach(function (v, k) { if (v > d[imx]) imx = k; if (v < d[imn]) imn = k; });
          h += '<figure class="isi-graf" data-g="' + g[0] + '"><figcaption>' + kacis(g[1]) + " <span class='isi-soluk'>(" + kacis(g[2]) + ")</span></figcaption>" +
            '<svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" role="img" aria-label="' + kacis(g[1] + " boyunca; en büyük " + fmt(d[imx], 4) + ", en küçük " + fmt(d[imn], 4) + " " + g[2]) + '">' +
            '<line class="isi-graf-sifir" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + sy(0).toFixed(1) + '" y2="' + sy(0).toFixed(1) + '"/>' +
            '<path class="isi-graf-alan" d="' + alanYol + '"/><path class="isi-graf-cizgi" d="' + yol + '"/>' +
            '<text class="isi-graf-etiket" x="' + (pl - 4) + '" y="' + (pt + 4) + '" text-anchor="end">' + kacis(fmt(hi, 3)) + "</text>" +
            '<text class="isi-graf-etiket" x="' + (pl - 4) + '" y="' + (H - pb + 2) + '" text-anchor="end">' + kacis(fmt(lo, 3)) + "</text>" +
            '<text class="isi-graf-etiket" x="' + pl + '" y="' + (H - 3) + '">0</text><text class="isi-graf-etiket" x="' + (W - pr) + '" y="' + (H - 3) + '" text-anchor="end">' + kacis(fmt(L, 3)) + " m</text>" +
            '<g class="isi-graf-imlec"><line x1="0" x2="0" y1="' + pt + '" y2="' + (H - pb) + '"/><circle r="3.5" cx="0" cy="0"/></g>' +
            '<text class="isi-graf-deger" x="' + (W - pr) + '" y="11" text-anchor="end"></text>' +
            '<rect class="isi-graf-hedef" x="' + pl + '" y="0" width="' + (W - pl - pr) + '" height="' + H + '"/>' +
            "</svg></figure>";
        });
        E.grafik.innerHTML = h;
        E.grafik._olcek = { W: W, pl: pl, pr: pr, pt: pt, pb: pb, H: H };
      }
      function imlecCiz() {
        const e = e_(), L = e.L || 1, o = E.grafik._olcek;
        if (!o) return;
        E.grafik.querySelectorAll(".isi-graf").forEach(function (f) {
          const ad = f.getAttribute("data-g"), d = grafikVerisi(e, ad);
          let lo = 0, hi = 0;
          d.forEach(function (v) { if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); } });
          if (hi - lo < 1e-12) { hi += 1; lo -= 1; }
          const v = xDeger(d, ex);
          const x = o.pl + ex / L * (o.W - o.pl - o.pr), y = o.pt + (hi - (v || 0)) / (hi - lo) * (o.H - o.pt - o.pb);
          const g = f.querySelector(".isi-graf-imlec");
          g.querySelector("line").setAttribute("x1", x.toFixed(1)); g.querySelector("line").setAttribute("x2", x.toFixed(1));
          g.querySelector("circle").setAttribute("cx", x.toFixed(1)); g.querySelector("circle").setAttribute("cy", y.toFixed(1));
          f.querySelector(".isi-graf-deger").textContent = "x = " + fmt(ex, 3) + " m: " + fmt(v, 4);
        });
      }
      function tabloCiz() {
        const e = e_(), son = e.x.length - 1;
        const ad = ["N", "Vy", "Vz", "T", "My", "Mz"], etk = ["N", "V_y′", "V_z′", "T", "M_y′", "M_z′"];
        let h = '<table class="isi-tablo"><caption>Uç kuvvetleri (diyagram işaretiyle; kN, kN·m)</caption><thead><tr><th>Uç</th>' +
          etk.map(function (t) { return "<th>" + kacis(t) + "</th>"; }).join("") + "</tr></thead><tbody>";
        [["i (x = 0)", 0], ["j (x = L)", son]].forEach(function (u) {
          h += "<tr><th>" + u[0] + "</th>" + ad.map(function (a) { return "<td>" + fmt(e[a] && e[a][u[1]], 4) + "</td>"; }).join("") + "</tr>";
        });
        h += "</tbody></table>";
        const x = e.ekstremum || {};
        const satir = [["u", "|u| (mm)", 1000], ["N", "N (kN)"], ["Vy", "V_y′ (kN)"], ["Vz", "V_z′ (kN)"], ["T", "T (kN·m)"], ["My", "M_y′ (kN·m)"], ["Mz", "M_z′ (kN·m)"],
          ["sigma_max", "σ_maks (MPa)"], ["sigma_min", "σ_min (MPa)"], ["von_mises", "von Mises (MPa)"], ["tau_max", "τ_maks (MPa)"], ["kullanim", "Kullanım (D/C)"]];
        h += '<table class="isi-tablo"><caption>Ekstremumlar</caption><thead><tr><th>Büyüklük</th><th>en büyük</th><th>x (m)</th><th>en küçük</th><th>x (m)</th></tr></thead><tbody>';
        satir.forEach(function (s) {
          const k = x[s[0]];
          if (!k) return;
          const c = s[2] || 1, mx = k.max || k, mn = k.min || k;
          h += "<tr><th>" + kacis(s[1]) + "</th><td>" + fmt(mx.deger * c, 4) + "</td><td>" + fmt(mx.x, 3) + "</td><td>" + fmt(mn.deger * c, 4) + "</td><td>" + fmt(mn.x, 3) + "</td></tr>";
        });
        h += "</tbody></table>";
        const kul = x.kullanim, tas = e.tasarim;
        h += '<div class="isi-el-tasarim">';
        if (kul) h += "<div><b>Kullanım oranı</b> en büyük " + fmt((kul.max || kul).deger, 3) + " (x = " + fmt((kul.max || kul).x, 3) + " m)" +
          ((e.kesit && e.kesit.malzeme && e.kesit.malzeme.tur === "celik") ? " — von Mises / F_y" : " — |M|/M_r ve |V|/V_r (tasarım kapasiteleri)") + "</div>";
        if (tas) h += "<div><b>Tasarım D/C</b> " + fmt(tas.dc, 3) + " · " + kacis(tas.durum || "") + (tas.belirleyen ? " · belirleyen: " + kacis(tas.belirleyen.kontrol || "") +
          (tas.belirleyen.kombinasyon ? " (" + kacis(tas.belirleyen.kombinasyon) + ")" : "") : "") + "</div>";
        if (e.belirleyen) h += "<div class='isi-soluk'>Zarfta belirleyen kombinasyon: " + kacis(e.belirleyen.kombinasyon) + "</div>";
        if (!kul && !tas) h += "<div class='isi-soluk'>Tasarım bilgisi yok (çözümde kesit tahkiki yapılmadı).</div>";
        h += "</div>";
        E.tablo.innerHTML = h;
      }
      function goruntuAlEG() {
        if (!ecz) return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(E.svg));
        eCiz();
        const tv = document.createElement("canvas");
        tv.width = eEn + E.kTuval.width; tv.height = Math.max(eBoy, E.kTuval.height);
        const c = tv.getContext("2d");
        const ar = arkaRenk();
        c.fillStyle = "rgb(" + ar.map(function (v) { return Math.round(v * 255); }).join(",") + ")";
        c.fillRect(0, 0, tv.width, tv.height);
        c.drawImage(E.tuval, 0, 0);
        c.drawImage(E.kTuval, eEn, 0);
        return tv.toDataURL("image/png");
      }
      // ---- etkileşim ----
      kab.addEventListener("click", function (ev) {
        const b = ev.target.closest("[data-e]");
        if (!b) return;
        const a = b.getAttribute("data-e");
        if (a === "kapat") kapatEG();
        else if (a === "onceki" || a === "sonraki") {
          const s = sonrakiGorunur(ei, a === "sonraki" ? 1 : -1);
          if (s >= 0) { sec(s, false); ac(s); }
        } else if (a === "tasarim" && olay.tasarim) {
          const e = e_();
          olay.tasarim({ tur: e.tur, no: e.bina_no, fe: e.no });
        }
      });
      E.renk.addEventListener("change", function () { guncelle(); });
      E.kes.addEventListener("change", function () {
        // kesit yüzü görünsün: göz +x′ tarafına (kalan parça x ≤ x_c, kesit yüzünün normali +x′)
        const e = e_(), a = E.kes.checked ? [0.62, 0.5, 0.35] : [0.18, 0.6, 0.4];
        const d = v3Bir([0, 1, 2].map(function (c) { return a[0] * e.yerel.x[c] + a[1] * e.yerel.z[c] + a[2] * e.yerel.y[c]; }));
        ek.pitch = Math.asin(Math.max(-0.999, Math.min(0.999, d[2])));
        ek.yaw = Math.atan2(d[1], d[0]);
        // görünen parçaya sığdır (kesitte: 0 … x_c)
        const sk = etkinOlcek(), r0 = (an.dy + an.dz) / 2;
        const p0 = noktaKonumu(ei, 0, 0, 0, sk), p1 = noktaKonumu(ei, e.x.length - 1, 0, 0, sk);
        const t = E.kes.checked ? Math.max(0.15, ex / (e.L || 1)) : 1;
        const pc = [0, 1, 2].map(function (c) { return p0[c] + (p1[c] - p0[c]) * t; });
        sigdir(ek, [0, 1, 2].map(function (c) { return Math.min(p0[c], pc[c]) - r0; }), [0, 1, 2].map(function (c) { return Math.max(p0[c], pc[c]) + r0; }));
        eIste();
      });
      E.x.addEventListener("input", function () { xAyarla(+E.x.value / 1000 * (e_().L || 1)); });
      E.grafik.addEventListener("pointermove", function (ev) {
        const r = ev.target.closest("svg");
        if (!r) return;
        const b = r.getBoundingClientRect(), o = E.grafik._olcek;
        const fx = (ev.clientX - b.left) / b.width * o.W;
        const x = (fx - o.pl) / (o.W - o.pl - o.pr) * (e_().L || 1);
        xAyarla(x);
      });
      E.tuval.addEventListener("pointerdown", function (ev) {
        try { E.tuval.setPointerCapture(ev.pointerId); } catch (er) { /* yok */ }
        ptr.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
        surk = { kaydir: ev.button === 2 || ev.shiftKey };
        if (ptr.size === 2) { const p = Array.from(ptr.values()); surk.d = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); }
      });
      E.tuval.addEventListener("pointermove", function (ev) {
        const p = ptr.get(ev.pointerId);
        if (!p || !surk) return;
        const dx = ev.clientX - p.x, dy = ev.clientY - p.y;
        p.x = ev.clientX; p.y = ev.clientY;
        if (ptr.size >= 2 && surk.d) {
          const q = Array.from(ptr.values()), d = Math.hypot(q[0].x - q[1].x, q[0].y - q[1].y);
          if (d > 0) ek.uzak = Math.max(ek.R * 0.05, Math.min(ek.R * 20, ek.uzak * surk.d / d));
          surk.d = d;
        } else if (surk.kaydir) {
          const km = kameraMatrisi(ek, eEn, eBoy), b = E.tuval.getBoundingClientRect(), olc = 2 * km.yariY / Math.max(1, b.height);
          for (let c = 0; c < 3; c++) ek.hedef[c] += (-dx * km.sag[c] + dy * km.yukari[c]) * olc;
        } else {
          ek.yaw -= dx * 0.01;
          ek.pitch = Math.max(-Math.PI / 2 + 1e-4, Math.min(Math.PI / 2 - 1e-4, ek.pitch + dy * 0.01));
        }
        eIste();
      });
      function eBirak(ev) { ptr.delete(ev.pointerId); if (!ptr.size) surk = null; }
      E.tuval.addEventListener("pointerup", eBirak);
      E.tuval.addEventListener("pointercancel", eBirak);
      E.tuval.addEventListener("contextmenu", function (ev) { ev.preventDefault(); });
      E.tuval.addEventListener("wheel", function (ev) {
        ev.preventDefault();
        ek.uzak = Math.max(ek.R * 0.05, Math.min(ek.R * 20, ek.uzak * Math.exp(Math.max(-0.5, Math.min(0.5, ev.deltaY * 0.0015)))));
        eIste();
      }, { passive: false });
      kab.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape") { ev.stopPropagation(); kapatEG(); }
        else if ((ev.key === "ArrowRight" || ev.key === "ArrowLeft") && ev.target === E.tuval) {
          ev.preventDefault();
          xAyarla(ex + (ev.key === "ArrowRight" ? 1 : -1) * (e_().L || 1) / 40);
        }
      });
      return {
        ac: ac, acik: acik, guncelle: function () { if (acik()) guncelle(); }, boyutla: boyutla, goruntuAl: goruntuAlEG,
        kapat: kapatEG, birak: function () { if (ecz) ecz.birak(); }, durum: function () { return { acik: acik(), el: ei >= 0 && els[ei] ? els[ei].no : null, x: ex }; },
        xAyarla: function (x) { xAyarla(x); },
      };
    }

    // ---------------- başlangıç ----------------
    function secimCoz(s) {
      if (s == null) return [];
      if (typeof s === "number") return noIdx[s] != null ? [noIdx[s]] : [];
      if (Array.isArray(s)) return s.map(function (n) { return noIdx[n]; }).filter(function (i) { return i != null; });
      if (typeof s === "object" && s.no != null) {
        if (s.tur === "fe") return noIdx[s.no] != null ? [noIdx[s.no]] : [];
        const out = [];
        els.forEach(function (e, i) { if (e.bina_no === s.no && (!s.tur || e.tur === s.tur)) out.push(i); });
        return out;
      }
      return [];
    }
    const genis = kapsayici.clientWidth || 800;
    let mobil = false;
    try { mobil = !!(kok.matchMedia && kok.matchMedia("(pointer: coarse)").matches) || genis < 600; } catch (e) { mobil = genis < 600; }
    if (mobil) {
      D.tup = true;
      kokEl.querySelectorAll('[data-seg=cizim] button').forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-v") === "tup" ? "true" : "false"); });
    }
    if (genis >= 900) R.ayar.open = true;
    alanHazirla();
    boyutla();
    agKur();
    gorunumAyarla("3b", false);
    R.defCikti.textContent = defOlcekMetni();
    secimCoz(ayar.secim).forEach(function (i) { D.secili[i] = true; });
    secimKur();
    ciz();

    function guncelleAPI(yeni, yeniBina) {
      if (!yeni) return;
      const eskiSecim = Object.keys(D.secili).map(function (i) { return els[i] && els[i].no; });
      const egNo = EG && EG.acik() ? EG.durum().el : null, egX = EG && EG.acik() ? EG.durum().x : null;
      if (egNo != null) EG.kapat();
      alan = yeni;
      if (yeniBina) bina = yeniBina;
      D.secili = {}; D.gizli = {}; D.yalit = null;
      alanHazirla();
      eskiSecim.forEach(function (no) { if (noIdx[no] != null) D.secili[noIdx[no]] = true; });
      agKur();
      if (egNo != null && noIdx[egNo] != null) { EG.ac(noIdx[egNo]); if (egX != null) EG.xAyarla(egX); }
      secimKirli = true;
      iste();
    }
    function kapat() {
      if (kapali) return;
      kapali = true;
      if (istek) cancelAnimationFrame(istek);
      dinleyiciler.forEach(function (d) { d[0].removeEventListener(d[1], d[2], d[3]); });
      if (ro) ro.disconnect();
      if (EG) EG.birak();
      if (cz) cz.birak();
      kokEl.remove();
    }
    return {
      guncelle: guncelleAPI,
      kapat: kapat,
      goruntuAl: goruntuAl,
      sec: function (no) { const i = noIdx[no]; sec(i == null ? null : i, false); },
      incele: function (no) { const i = noIdx[no]; if (i != null) { sec(i, false); incele(i); } },
      /** Eleman noktasının istemci (sayfa) koordinatı: {x, y} — testler ve dış araçlar için (deforme ölçeği dahil). */
      ekranKonumu: function (no, oran) {
        const i = noIdx[no];
        if (i == null) return null;
        const e = els[i], k = Math.round((oran == null ? 0.5 : oran) * (e.x.length - 1));
        const km = kameraMatrisi(kam, en, boy), p = izdusur(km, noktaKonumu(i, k, 0, 0, etkinOlcek()), en, boy);
        if (!p) return null;
        const r = R.sahne.getBoundingClientRect();
        return { x: r.left + p[0] / dpr, y: r.top + p[1] / dpr };
      },
      buyuklukSec: function (ad) { if (BUYUKLUK[ad]) { D.buyukluk = ad; R.buyukluk.value = ad; degerGuncelle(); } },
      gorunum: function (ad) { gorunumAyarla(ad, false); },
      ayarla: function (o) {
        o = o || {};
        if (o.doseme) { D.doseme = o.doseme; R.doseme.value = o.doseme; plakDegerleri(); }
        if (o.radye) { D.radye = o.radye; R.radye.value = o.radye; plakDegerleri(); }
        if (o.tup != null && o.tup !== D.tup) { D.tup = !!o.tup; agKur(); }
        if (o.palet) D.palet = o.palet;
        if (o.bantli != null) D.bantli = !!o.bantli;
        if (o.kat != null) { D.kat = String(o.kat); R.kat.value = D.kat; if (!svgMod) plakKur(); gorunurlukGuncelle(); }
        if (o.olcek != null) { D.olcekCarpan = o.olcek; D.gercek = false; }
        if (o.x != null && EG) EG.xAyarla(o.x);
        degerGuncelle();
        lejantCiz();
        secimKirli = true;
        iste();
      },
      durum: function () {
        return {
          webgl: !svgMod, surum: cz ? cz.surum : 0, eleman: els.length, kose: ag ? ag.kose : 0, ucgen: ag ? ag.ucgen : 0, kurulum_ms: ag ? ag.surec : 0,
          seyrek: ag ? ag.seyrek : 1,
          son_kare_ms: sonKare, buyukluk: D.buyukluk, aralik: aralik.slice(), secili: Object.keys(D.secili).map(function (i) { return els[i].no; }),
          ekstremum: ekst ? { min: ekst.min && { deger: ekst.min.deger, no: els[ekst.min.el].no, x: els[ekst.min.el].x[ekst.min.k] },
            max: ekst.max && { deger: ekst.max.deger, no: els[ekst.max.el].no, x: els[ekst.max.el].x[ekst.max.k] } } : null,
          eleman_gorunumu: EG ? EG.durum() : { acik: false }, tup: D.tup, olcek: defCarpan(),
        };
      },
      kareSuresi: function (n, hafifKip) {
        n = n || 20;
        hafif = !!hafifKip;
        if (svgMod) { const t0 = performance.now(); for (let i = 0; i < n; i++) svgCiz(); return (performance.now() - t0) / n; }
        const gl = cz.gl, px = new Uint8Array(4);
        // readPixels GPU'yu bekletir (finish bazı sürücülerde beklemez): kare süresi = çizim + eşitleme
        ciz(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
        const t0 = performance.now();
        for (let i = 0; i < n; i++) { kam.yaw += 0.01; ciz(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); }
        const ort = (performance.now() - t0) / n;
        hafif = false;
        iste();
        return ort;
      },
    };
  }

  const API = {
    ac: ac,
    // saf yardımcılar (testler ve başka modüller için)
    BUYUKLUKLER: BUYUKLUKLER, PALET: PALET, BANT: BANT, GECERSIZ: GECERSIZ,
    fmt: fmt, istasyonDegeri: istasyonDegeri, lifGerilmesi: lifGerilmesi, lifDegeri: lifDegeri, tarafsizEksen: tarafsizEksen, dogruKirp: dogruKirp,
    renkAl: renkAl, renkHex: renkHex, degerRengi: degerRengi, aralikBelirle: aralikBelirle, lejantSinirlari: lejantSinirlari, dokuVerisi: dokuVerisi,
    kimlikRenk: kimlikRenk, renkKimlik: renkKimlik, kesitAnahat: kesitAnahat, isaretliAlan: isaretliAlan, ucgenle: ucgenle, cokgenIcinde: cokgenIcinde,
    kesitUcLifleri: kesitUcLifleri, anahatSayilari: anahatSayilari, cubukAgi: cubukAgi, degerleriDoldur: degerleriDoldur, istasyonTablosu: istasyonTablosu,
    ekstremumBul: ekstremumBul, plakAgi: plakAgi, plakDegeri: plakDegeri, radyeAgi: radyeAgi, kameraMatrisi: kameraMatrisi, izdusur: izdusur, sigdir: sigdir,
    kutuHesapla: kutuHesapla, STANDART: STANDART, katListesi: katListesi, aksListesi: aksListesi, aksUstunde: aksUstunde,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.MatrisIsi = API;
})(typeof window !== "undefined" ? window : globalThis);
