/* Matris Öğren — aks sistemi (tasarım belgesi §19: aks sistemi tabanlı modelleme).
   Tarayıcıda window.MatrisAks, node'da module.exports (UMD). İki katman:

   1) SAF MANTIK (DOM yok, node testli). Bütün düzenleme işlevleri girdiyi DEĞİŞTİRMEZ; sonuç yeni bir bina ve rapordur:
        { model, uyarilar: [metin], ...işleme özgü alanlar }
      Geçersiz girdi (olmayan aks, anlaşılmayan REF, bozuk sözdizimi) AksHatasi fırlatır.
   2) ARAYÜZ BİLEŞENLERİ (DOM): sihirbaz (hızlı aks), duzenleyici (aks verisi tablosu), sahneKatmani (SVG metni),
      balonSurukle (işaretçi yardımcıları). bina.js çağırır; bu dosya bina.js'e bağımlı değildir.

   Koordinat: bina sistemi X sağa, Y derinlik, Z yukarı (§2). Birim m.
   Aks verisi (§19.1):
     akslar: {x: [{ad, konum, tur: "ana"|"ikincil", gorunur, balon: "bas"|"son"|"iki"|"yok"}], y: [...], z: [{ad, konum, kat?}]}
     aks_sistemleri: [{ad, tur: "kartezyen", orijin: [X, Y, Z], aci (Z etrafında, derece), x, y, z: null|[...]},
                      {ad, tur: "silindirik", orijin, aci, r: [...], teta: [... (derece)], z: null|[...]}]
     z: null → ek sistem GLOBAL Z akslarını kullanır (kotlar mutlak); kendi z listesi varsa kot = orijin Z + konum.
   Düğüm başvurusu (REF, §19.2):
     {"aks": ["B","3"], "z": "Saçak"} (GLOBAL) | {"sistem": "KANAT-B", "aks": ["C","2"], "z": "±0.00"} |
     {"aks": ["A","1"], "kat": k} (eski; kat k'nın Z aksı) | {"dugum": no} → dugumler kaydı:
       {no, X, Y, Z} (serbest; yalnız içe aktarma/geriye uyum) | {no, tur: "bolme", cubuk_i: REF, cubuk_j: REF, oran: t} |
       {no, tur: "kesisim", a: [REF, REF], b: [REF, REF]} (iki doğrunun en yakın noktası; çakışmıyorsa ortak dikmenin ortası).
     Kayıtsız {"dugum": no} (no < 100000) eski aks–kat numarasıdır: no = 1000·kat + 20·ix + iy + 1.
   Kat ↔ Z aksı: akslar.z[i].kat = n → kat n'nin kotu o aksın konumudur (tek kaynak akslar.z; `katlar` eşlenir).
   Görünüm: {tur: "plan", z: ad, sistem?} | {tur: "cephe", x: ad | y: ad (silindirikte r | teta), sistem?} | {tur: "3b", z?: ad}. */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.MatrisAks = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function () {
  "use strict";

  const TOL = 0.001;
  const D2R = Math.PI / 180;
  const GLOBAL = "GLOBAL";
  const YAKALAMA_ADIMI = 0.05;
  const EN_AZ_ARALIK = 0.3;      // motorun aks aralığı alt sınırı (yapi._bina_oku)
  const BALON_YERLERI = ["bas", "son", "iki", "yok"];
  const ILK_SERBEST_DUGUM = 100001;

  function AksHatasi(mesaj) {
    const e = new Error(mesaj);
    e.name = "AksHatasi";
    Object.setPrototypeOf(e, AksHatasi.prototype);
    return e;
  }
  AksHatasi.prototype = Object.create(Error.prototype);
  AksHatasi.prototype.constructor = AksHatasi;

  // ---------------------------------------------------------------- küçük yardımcılar
  function kopya(o) { return o === undefined ? undefined : JSON.parse(JSON.stringify(o)); }
  function r6(v) { const r = Math.round(v * 1e6) / 1e6; return r === 0 ? 0 : r; }
  function yuvarla(v, adim) { return r6(Math.round(v / adim) * adim); }
  function sayiOku(s) {
    if (typeof s === "number") return isFinite(s) ? s : null;
    let t = String(s == null ? "" : s).trim().replace(/−/g, "-").replace(/^±/, "");
    if (/^[+-]?\d+,\d+$/.test(t)) t = t.replace(",", ".");
    if (!/^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/.test(t)) return null;
    const n = parseFloat(t);
    return isFinite(n) ? n : null;
  }
  /** Türkçe gösterim: 2 ondalık, ondalık virgül, gerçek eksi işareti. */
  function fmt(v, b) {
    if (typeof v !== "number" || !isFinite(v)) return "—";
    b = b == null ? 2 : b;
    return (Math.round(v * Math.pow(10, b)) / Math.pow(10, b)).toFixed(b).replace(".", ",").replace("-", "−");
  }
  /** Kısa gösterim: gereksiz sıfırlar atılır (6 → "6", 7.5 → "7,5"). */
  function fmtKisa(v) {
    if (typeof v !== "number" || !isFinite(v)) return "—";
    return String(r6(Math.round(v * 1000) / 1000)).replace(".", ",").replace("-", "−");
  }
  /** Sözdizimi için makine biçimi (nokta ondalık). */
  function fmtMakine(v) { return String(r6(Math.round(v * 1e4) / 1e4)); }
  function kotAdi(z) {
    const v = Math.round(z * 100) / 100;
    if (Math.abs(v) < 0.005) return "±0.00";
    return (v > 0 ? "+" : "-") + Math.abs(v).toFixed(2);
  }
  function topla(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
  function cikar(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function olcek(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
  function ic(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function uzaklik(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); }

  // ---------------------------------------------------------------- aralık sözdizimi
  /** Tek terim: "n@a" (n adet a aralık; "n×a", "n*a", "nxa" de olur) ya da "a". */
  function terimOku(t) {
    const m = /^(\d+)\s*[@×xX*]\s*(.+)$/.exec(t);
    if (m) {
      const a = sayiOku(m[2]);
      if (a == null) return null;
      return { adet: +m[1], deger: a, carpanli: true };
    }
    const a = sayiOku(t);
    return a == null ? null : { adet: 1, deger: a, carpanli: false };
  }
  /** Virgülü ayırıcı mı ondalık mı olduğu bağlamdan çözülür: "7,5" ondalık; "6, 7" ve "3@6,2@7.5" ayırıcı. */
  function parcala(metin) {
    const ham = String(metin == null ? "" : metin).replace(/\u2212/g, "-").trim();
    const parcalar = [];
    let ayiriciVirgul = /;|,\s/.test(ham);
    ham.split(/;|,(?=\s)|\s+/).forEach(function (p) {
      p = p.replace(/^,+|,+$/g, "").trim();
      if (!p) return;
      if (p.indexOf(",") >= 0) {
        const ondalik = p.replace(/,/g, ".");
        if (terimOku(ondalik)) { parcalar.push(ondalik); return; }     // "7,5" → 7.5 ; "2@7,5" → 2@7.5
        ayiriciVirgul = true;                                           // "3@6,2@7.5" → iki terim
        const q = p.split(",").map(function (x) { return x.trim(); }).filter(Boolean);
        for (let i = 0; i < q.length; i++) {
          // "n@a,b" içinde virgülden sonra yalnız rakam varsa ondalıktır: "3@6,2@7,5" → 3@6, 2@7.5
          if (/@|×|\*/.test(q[i]) && i + 1 < q.length && /^\d+$/.test(q[i + 1]) && q[i].indexOf(".") < 0 && terimOku(q[i] + "." + q[i + 1])) { parcalar.push(q[i] + "." + q[i + 1]); i++; }
          else parcalar.push(q[i]);
        }
        return;
      }
      parcalar.push(p);
    });
    return { parcalar: parcalar, ayiriciVirgul: ayiriciVirgul };
  }
  /**
   * Aralık/konum sözdizimini ayrıştırır.
   *   "3@6, 2@7.5, 5" → aralıklar [6,6,6,7.5,7.5,5]; "0 6 12 19.5" → konumlar. Türkçe ondalık virgül: "7,5".
   * sec: {kip: "otomatik"|"aralik"|"konum", baslangic: 0}
   * Otomatik: "@" varsa ya da virgül/noktalı virgülle ayrılmışsa aralık; yalnız boşlukla ayrılmış ve kesin artan ise konum.
   * Dönüş: {tur, araliklar, konumlar, uyarilar}
   */
  function sozdizimiAyristir(metin, sec) {
    sec = sec || {};
    const bas = sec.baslangic == null ? 0 : +sec.baslangic;
    const p = parcala(metin);
    if (!p.parcalar.length) throw new AksHatasi("Aks dizisi boş. Örnek: \"3@6, 2@7.5\" (aralıklar) ya da \"0 6 12\" (konumlar).");
    const terimler = p.parcalar.map(function (t) {
      const r = terimOku(t);
      if (!r) throw new AksHatasi("\"" + t + "\" anlaşılamadı. Terimler \"adet@aralık\" (3@6) ya da sayı (7,5) olmalı.");
      if (r.carpanli && r.adet < 1) throw new AksHatasi("\"" + t + "\": adet en az 1 olmalı.");
      return r;
    });
    const carpanVar = terimler.some(function (t) { return t.carpanli; });
    let kip = sec.kip || "otomatik";
    if (kip === "otomatik") {
      if (carpanVar || p.ayiriciVirgul || terimler.length < 2) kip = "aralik";
      else {
        let artan = true;
        for (let i = 1; i < terimler.length; i++) if (!(terimler[i].deger > terimler[i - 1].deger)) artan = false;
        kip = artan ? "konum" : "aralik";
      }
    }
    const uyarilar = [];
    if (kip === "konum") {
      if (carpanVar) throw new AksHatasi("Konum dizisinde \"adet@aralık\" kullanılamaz; konumları boşlukla yazın: \"0 6 12\".");
      let k = terimler.map(function (t) { return r6(t.deger); }).sort(function (a, b) { return a - b; });
      const tekil = k.filter(function (v, i) { return i === 0 || Math.abs(v - k[i - 1]) > TOL; });
      if (tekil.length !== k.length) uyarilar.push("Aynı konum birden çok yazılmış; tekrarlar atıldı.");
      k = tekil;
      return { tur: "konum", konumlar: k, araliklar: konumdanAralik(k), uyarilar: uyarilar };
    }
    const araliklar = [];
    terimler.forEach(function (t) {
      if (!(t.deger > 0)) throw new AksHatasi("Aralıklar sıfırdan büyük olmalı (" + fmtKisa(t.deger) + " verildi).");
      for (let i = 0; i < t.adet; i++) araliklar.push(r6(t.deger));
    });
    if (araliklar.length > 200) throw new AksHatasi("En çok 200 aralık yazılabilir.");
    return { tur: "aralik", araliklar: araliklar, konumlar: araliktanKonum(araliklar, bas), uyarilar: uyarilar };
  }
  function konumdanAralik(konumlar) {
    const a = [];
    for (let i = 1; i < konumlar.length; i++) a.push(r6(konumlar[i] - konumlar[i - 1]));
    return a;
  }
  function araliktanKonum(araliklar, bas) {
    const k = [r6(bas || 0)];
    araliklar.forEach(function (a) { k.push(r6(k[k.length - 1] + a)); });
    return k;
  }
  /** Konumlardan kısa aralık sözdizimi: [0,6,12,18,25.5] → "3@6, 7.5" (başlangıç 0 değilse konum dizisi yazılır). */
  function sozdizimiYaz(konumlar, sec) {
    sec = sec || {};
    const k = (konumlar || []).slice().sort(function (a, b) { return a - b; });
    if (k.length < 2) return k.length ? fmtMakine(k[0]) : "";
    if (Math.abs(k[0] - (sec.baslangic || 0)) > TOL) return k.map(fmtMakine).join(" ");
    const a = konumdanAralik(k), gr = [];
    a.forEach(function (v) {
      const s = gr[gr.length - 1];
      if (s && Math.abs(s.v - v) < 1e-6) s.n++; else gr.push({ v: v, n: 1 });
    });
    return gr.map(function (g) { return g.n > 1 ? g.n + "@" + fmtMakine(g.v) : fmtMakine(g.v); }).join(", ");
  }

  // ---------------------------------------------------------------- ad üretme
  function harfAdi(i) {
    let s = "";
    i = Math.floor(i);
    do { s = String.fromCharCode(65 + (i % 26)) + s; i = Math.floor(i / 26) - 1; } while (i >= 0);
    return s;
  }
  function harfIndeks(ad) {
    if (!/^[A-Z]+$/.test(String(ad))) return -1;
    let n = 0;
    for (const c of String(ad)) n = n * 26 + (c.charCodeAt(0) - 64);
    return n - 1;
  }
  /** n ad üretir. ilk: "A" (harf), "1" (sayı), "R1"/"T1" gibi önekli sayı ya da boş (yöne göre otomatik). */
  function adlarUret(yon, n, ilk) {
    let tip, bas = 0, onek = "";
    const varsayilan = { x: "A", y: "1", r: "R1", teta: "T1" }[yon] || "1";
    const s = String(ilk == null || ilk === "" || ilk === "otomatik" ? varsayilan : ilk).trim().toUpperCase();
    let m;
    if (harfIndeks(s) >= 0) { tip = "harf"; bas = harfIndeks(s); }
    else if ((m = /^([A-Z]*)(\d+)$/.exec(s))) { tip = "sayi"; onek = m[1]; bas = +m[2]; }
    else throw new AksHatasi("İlk aks adı \"" + ilk + "\" anlaşılamadı; harf (A) ya da sayı (1) olmalı.");
    const l = [];
    for (let i = 0; i < n; i++) l.push(tip === "harf" ? harfAdi(bas + i) : onek + (bas + i));
    return l;
  }
  function benzersizAd(ad, mevcut) {
    const var_ = new Set((mevcut || []).map(String));
    let a = String(ad);
    while (var_.has(a)) a += "'";
    return a;
  }
  /** Listenin sonuna eklenecek aksın adı: harfliyse sonraki harf, sayılıysa sonraki sayı. */
  function sonrakiAd(liste, yon) {
    const adlar = (liste || []).map(function (a) { return String(a.ad); });
    let enH = -1, enS = null, onek = "";
    adlar.forEach(function (a) {
      const h = harfIndeks(a);
      if (h > enH) enH = h;
      const m = /^([A-Z]*)(\d+)$/i.exec(a);
      if (m && (enS == null || +m[2] > enS)) { enS = +m[2]; onek = m[1]; }
    });
    if (yon === "z") return null;
    if (enH >= 0 && (yon === "x" || enS == null)) return benzersizAd(harfAdi(enH + 1), adlar);
    if (enS != null) return benzersizAd(onek + (enS + 1), adlar);
    return adlarUret(yon, 1)[0];
  }

  // ---------------------------------------------------------------- sistemler
  function yonler(tur) { return tur === "silindirik" ? ["r", "teta", "z"] : ["x", "y", "z"]; }
  function aksNormal(a, i, yon) {
    const o = { ad: String(a.ad), konum: +a.konum, tur: a.tur === "ikincil" ? "ikincil" : "ana", gorunur: a.gorunur !== false,
      balon: BALON_YERLERI.indexOf(a.balon) >= 0 ? a.balon : (yon === "z" ? "bas" : "bas"), _i: i };
    if (a.kat != null && a.kat !== "") o.kat = +a.kat;
    return o;
  }
  function sirali(l, yon) {
    return (Array.isArray(l) ? l : []).map(function (a, i) { return aksNormal(a, i, yon); })
      .filter(function (a) { return isFinite(a.konum); })
      .sort(function (a, b) { return a.konum - b.konum || a._i - b._i; });
  }
  /** GLOBAL Z aksları: akslar.z; yoksa katlardan türetilir (geriye uyum). */
  function zHam(bina) {
    const ak = bina && bina.akslar;
    if (ak && Array.isArray(ak.z) && ak.z.length) return ak.z;
    return zTuret(bina && bina.katlar);
  }
  function zTuret(katlar) {
    const l = [], adlar = [];
    (Array.isArray(katlar) ? katlar : []).forEach(function (k, i) {
      const kot = +k.kot;
      if (!isFinite(kot)) return;
      const ad = benzersizAd(kotAdi(kot), adlar);
      adlar.push(ad);
      l.push({ ad: ad, konum: r6(kot), kat: k.no != null ? +k.no : i });
    });
    return l.sort(function (a, b) { return a.konum - b.konum; });
  }
  function globalSistem(bina) {
    const ak = (bina && bina.akslar) || {};
    return { ad: GLOBAL, tur: "kartezyen", orijin: [0, 0, 0], aci: 0, global: true, zOrtak: true,
      yonler: ["x", "y", "z"], l: { x: sirali(ak.x, "x"), y: sirali(ak.y, "y"), z: sirali(zHam(bina), "z") } };
  }
  function ekSistem(s, gz, sira) {
    const tur = s.tur === "silindirik" ? "silindirik" : "kartezyen";
    const yl = yonler(tur);
    const o = Array.isArray(s.orijin) ? s.orijin : [0, 0, 0];
    const zOrtak = !Array.isArray(s.z) || !s.z.length;
    const l = {};
    l[yl[0]] = sirali(s[yl[0]], yl[0]);
    l[yl[1]] = sirali(s[yl[1]], yl[1]);
    l.z = zOrtak ? gz : sirali(s.z, "z");
    return { ad: String(s.ad), tur: tur, orijin: [+o[0] || 0, +o[1] || 0, +o[2] || 0], aci: +s.aci || 0, global: false, zOrtak: zOrtak,
      gorunur: s.gorunur !== false, yonler: yl, l: l, sira: sira };
  }
  /** Normalleştirilmiş bütün sistemler (ilk GLOBAL). Her sistemde l[yon] konuma göre sıralı akslar. */
  function sistemler(bina) {
    const g = globalSistem(bina);
    const l = [g];
    (Array.isArray(bina && bina.aks_sistemleri) ? bina.aks_sistemleri : []).forEach(function (s, i) { if (s && s.ad != null) l.push(ekSistem(s, g.l.z, i + 1)); });
    return l;
  }
  function sistemBul(bina, ad, liste) {
    const l = liste || sistemler(bina);
    const a = ad == null || ad === "" ? GLOBAL : String(ad);
    const s = l.find(function (x) { return x.ad === a; });
    if (!s) throw new AksHatasi("\"" + a + "\" adlı aks sistemi yok.");
    return s;
  }
  function aksBul(S, yon, ad, zorunlu) {
    const l = S.l[yon];
    if (!l) throw new AksHatasi(S.ad + " sisteminde \"" + yon + "\" yönü yok (yönler: " + S.yonler.join(", ") + ").");
    const a = l.find(function (x) { return x.ad === String(ad); });
    if (!a && zorunlu !== false) throw new AksHatasi(yonAdi(yon) + " aksı \"" + ad + "\" " + (S.global ? "" : S.ad + " sisteminde ") + "tanımlı değil.");
    return a || null;
  }
  function yonAdi(yon) { return { x: "X", y: "Y", z: "Z", r: "R", teta: "θ" }[yon] || yon; }
  /** Sistem yerel (u, v, z-konum) → bina (X, Y, Z). Kartezyen: u, v eksenleri aci kadar döndürülmüş; silindirik: u = r, v = θ (derece). */
  function sistemNokta(S, u, v, zk) {
    const ox = S.orijin[0], oy = S.orijin[1];
    const Z = S.zOrtak ? zk : S.orijin[2] + zk;
    if (S.tur === "silindirik") {
      const t = (v + S.aci) * D2R;
      return [r6(ox + u * Math.cos(t)), r6(oy + u * Math.sin(t)), r6(Z)];
    }
    const c = Math.cos(S.aci * D2R), s = Math.sin(S.aci * D2R);
    return [r6(ox + u * c - v * s), r6(oy + u * s + v * c), r6(Z)];
  }
  /** Bina (X, Y, Z) → sistem yerel (u, v, z-konum). */
  function noktaSistem(S, X, Y, Z) {
    const dx = X - S.orijin[0], dy = Y - S.orijin[1];
    const zk = S.zOrtak ? Z : Z - S.orijin[2];
    if (S.tur === "silindirik") {
      let t = Math.atan2(dy, dx) / D2R - S.aci;
      t = ((t % 360) + 360) % 360;
      return [Math.hypot(dx, dy), t, zk];
    }
    const c = Math.cos(S.aci * D2R), s = Math.sin(S.aci * D2R);
    return [dx * c + dy * s, -dx * s + dy * c, zk];
  }

  // ---------------------------------------------------------------- kat ↔ Z aksı
  function katZAksi(bina, kat) {
    const z = sirali(zHam(bina), "z");
    return z.find(function (a) { return a.kat === +kat; }) || null;
  }
  function katKotu(bina, kat) {
    const a = katZAksi(bina, kat);
    if (a) return a.konum;
    const k = (bina && Array.isArray(bina.katlar) ? bina.katlar : []).find(function (x, i) { return (x.no != null ? +x.no : i) === +kat; });
    return k ? +k.kot : null;
  }
  function zAksiKati(bina, ad) {
    const a = sirali(zHam(bina), "z").find(function (x) { return x.ad === String(ad); });
    return a && a.kat != null ? a.kat : null;
  }
  function katAdiVarsayilan(no) { return +no === 0 ? "Temel" : no + ". kat"; }
  /** akslar.z ↔ katlar eşlemesi (tek kaynak akslar.z): kata bağlı Z aksının kotu kat kotudur; Z aksı olmayan kata aks eklenir. */
  function katlariSenkronla(bina) {
    const m = kopya(bina) || {};
    const uy = [];
    if (!m.akslar) m.akslar = { x: [], y: [] };
    if (!Array.isArray(m.akslar.z) || !m.akslar.z.length) m.akslar.z = zTuret(m.katlar);
    const katlar = Array.isArray(m.katlar) ? m.katlar : [];
    const zKat = new Map();
    m.akslar.z.forEach(function (a) { if (a.kat != null) zKat.set(+a.kat, a); });
    katlar.forEach(function (k, i) {
      const no = k.no != null ? +k.no : i;
      if (!zKat.has(no)) {
        const a = { ad: benzersizAd(kotAdi(+k.kot), m.akslar.z.map(function (x) { return x.ad; })), konum: r6(+k.kot), kat: no };
        m.akslar.z.push(a); zKat.set(no, a);
        uy.push("Kat " + no + " için Z aksı " + a.ad + " eklendi.");
      }
    });
    for (const [no, a] of zKat) {
      let k = katlar.find(function (x, i) { return (x.no != null ? +x.no : i) === no; });
      if (!k) { k = { no: no, ad: katAdiVarsayilan(no), kot: r6(+a.konum) }; katlar.push(k); uy.push("Z aksı " + a.ad + " için kat " + no + " eklendi."); }
      else if (Math.abs(+k.kot - +a.konum) > 1e-9) k.kot = r6(+a.konum);
    }
    m.katlar = katlar.sort(function (a, b) { return (+a.no) - (+b.no); });
    m.akslar.z.sort(function (a, b) { return +a.konum - +b.konum; });
    const kots = m.katlar.map(function (k) { return +k.kot; });
    for (let i = 1; i < kots.length; i++) if (!(kots[i] > kots[i - 1])) uy.push("Kat kotları artan sırada değil (kat " + m.katlar[i].no + "); kat Z akslarını denetleyin.");
    return { model: m, uyarilar: uy };
  }
  /** Eski model (surum 1/2) yükseltme: akslar.z katlardan eklenir; kolon/kiriş/döşeme aynen kalır. */
  function yukselt(bina) {
    if (!bina || typeof bina !== "object") throw new AksHatasi("Bina bir JSON nesnesi olmalı.");
    const once = +bina.surum || 1;
    const r = katlariSenkronla(bina);
    const m = r.model;
    const uy = [];
    if (!m.akslar.x) m.akslar.x = [];
    if (!m.akslar.y) m.akslar.y = [];
    if (once < 3) { m.surum = 3; uy.push("Model sürüm " + once + "'den 3'e yükseltildi; Z aksları katlardan türetildi (" + m.akslar.z.map(function (a) { return a.ad; }).join(", ") + ")."); }
    return { model: m, uyarilar: uy.concat(r.uyarilar) };
  }

  // ---------------------------------------------------------------- REF çözücü
  function aksRefMi(r) { return !!(r && typeof r === "object" && !Array.isArray(r) && Array.isArray(r.aks) && r.aks.length === 2); }
  function dugumHaritasi(bina) {
    const h = new Map();
    (bina && Array.isArray(bina.dugumler) ? bina.dugumler : []).forEach(function (d) { if (d && d.no != null) h.set(+d.no, d); });
    return h;
  }
  /** Çözücü bağlamı (tekrarlı çağrılar için: sistemler ve düğüm haritası bir kez kurulur). */
  function Cozucu(bina) {
    this.bina = bina || {};
    this.S = sistemler(this.bina);
    this.dh = dugumHaritasi(this.bina);
    this.onbellek = new Map();
  }
  Cozucu.prototype.sistem = function (ad) { return sistemBul(this.bina, ad, this.S); };
  Cozucu.prototype.aks = function (ref) {
    const S = this.sistem(ref.sistem);
    const a = aksBul(S, S.yonler[0], ref.aks[0]), b = aksBul(S, S.yonler[1], ref.aks[1]);
    let zk;
    if (ref.z != null) zk = aksBul(S, "z", ref.z).konum;
    else if (ref.kat != null) {
      const k = katKotu(this.bina, ref.kat);
      if (k == null) throw new AksHatasi("Kat " + ref.kat + " tanımlı değil (" + JSON.stringify(ref) + ").");
      zk = S.zOrtak ? k : k - S.orijin[2];
    } else if (ref.Z != null && isFinite(+ref.Z)) zk = S.zOrtak ? +ref.Z : +ref.Z - S.orijin[2];
    else throw new AksHatasi("Aks başvurusunda Z aksı eksik: " + JSON.stringify(ref) + " — {\"aks\": [..], \"z\": ad} olmalı.");
    return sistemNokta(S, a.konum, b.konum, zk);
  };
  Cozucu.prototype.dugum = function (no, yol) {
    no = +no;
    if (this.onbellek.has(no)) return this.onbellek.get(no);
    if (yol.has(no)) throw new AksHatasi("Döngüsel düğüm tanımı: " + Array.from(yol).concat([no]).join(" → ") + " (bölme/kesişim düğümü kendine dayanıyor).");
    yol.add(no);
    const d = this.dh.get(no);
    let P;
    if (d && d.tur === "bolme") {
      const Pi = this.coz(d.cubuk_i, yol), Pj = this.coz(d.cubuk_j, yol), t = +d.oran;
      if (!isFinite(t)) throw new AksHatasi("Bölme düğümü " + no + ": oran sayı olmalı.");
      P = [r6(Pi[0] + (Pj[0] - Pi[0]) * t), r6(Pi[1] + (Pj[1] - Pi[1]) * t), r6(Pi[2] + (Pj[2] - Pi[2]) * t)];
    } else if (d && d.tur === "kesisim") {
      if (!Array.isArray(d.a) || !Array.isArray(d.b) || d.a.length !== 2 || d.b.length !== 2) throw new AksHatasi("Kesişim düğümü " + no + ": a ve b ikişer REF olmalı.");
      P = dogruKesisimi(this.coz(d.a[0], yol), this.coz(d.a[1], yol), this.coz(d.b[0], yol), this.coz(d.b[1], yol));
      if (!P) throw new AksHatasi("Kesişim düğümü " + no + ": doğrular paralel; kesişim yok.");
    } else if (d && d.X != null) {
      P = [+d.X, +d.Y, +d.Z];
      if (!P.every(isFinite)) throw new AksHatasi("Düğüm " + no + " koordinatları sayı değil.");
    } else if (no > 0 && no < ILK_SERBEST_DUGUM) {
      P = this.aksKatNo(no);
    }
    if (!P) throw new AksHatasi("Düğüm " + no + " modelde yok.");
    yol.delete(no);
    this.onbellek.set(no, P);
    return P;
  };
  /** Eski aks–kat düğüm numarası (1000·kat + 20·ix + iy + 1) → koordinat. */
  Cozucu.prototype.aksKatNo = function (no) {
    const G = this.S[0];
    const kat = Math.floor(no / 1000), r = no - 1000 * kat - 1;
    const ix = Math.floor(r / 20), iy = r % 20;
    const kot = katKotu(this.bina, kat);
    if (r < 0 || ix >= G.l.x.length || iy >= G.l.y.length || kot == null) return null;
    return [G.l.x[ix].konum, G.l.y[iy].konum, kot];
  };
  Cozucu.prototype.coz = function (ref, yol) {
    yol = yol || new Set();
    if (typeof ref === "string" && /^\d+$/.test(ref.trim())) ref = +ref;
    if (typeof ref === "number") return this.dugum(ref, yol);
    if (Array.isArray(ref)) {
      if (ref.length !== 3 || !ref.every(function (v) { return isFinite(+v); })) throw new AksHatasi("Koordinat dizisi [X, Y, Z] olmalı: " + JSON.stringify(ref));
      return ref.map(Number);
    }
    if (ref && typeof ref === "object") {
      if (ref.dugum != null) return this.dugum(+ref.dugum, yol);
      if (aksRefMi(ref)) return this.aks(ref);
      if (ref.X != null && ref.Y != null && ref.Z != null) {
        const P = [+ref.X, +ref.Y, +ref.Z];
        if (P.every(isFinite)) return P;
      }
    }
    throw new AksHatasi("Düğüm başvurusu anlaşılamadı: " + JSON.stringify(ref) +
      ' — {"aks": ["A","1"], "z": ad}, {"sistem": ad, "aks": [..], "z": ad}, {"aks": [..], "kat": k} ya da {"dugum": no} olmalı.');
  };
  /** İki doğrunun (P1P2, Q1Q2) en yakın noktası (kesişiyorsa kesişim, değilse ortak dikmenin ortası); paralelse null. */
  function dogruKesisimi(P1, P2, Q1, Q2) {
    const d1 = cikar(P2, P1), d2 = cikar(Q2, Q1), r = cikar(P1, Q1);
    const a = ic(d1, d1), e = ic(d2, d2), b = ic(d1, d2), c = ic(d1, r), f = ic(d2, r);
    const den = a * e - b * b;
    if (a < 1e-18 || e < 1e-18 || Math.abs(den) <= 1e-12 * a * e) return null;
    const s = (b * f - c * e) / den, t = (a * f - b * c) / den;
    const A = topla(P1, olcek(d1, s)), B = topla(Q1, olcek(d2, t));
    return [r6((A[0] + B[0]) / 2), r6((A[1] + B[1]) / 2), r6((A[2] + B[2]) / 2)];
  }
  function refKoordinat(bina, ref) { return new Cozucu(bina).coz(ref); }
  function refKoordinatGuvenli(bina, ref) { try { return refKoordinat(bina, ref); } catch (e) { return null; } }
  /** Bir REF'i karşılaştırma anahtarına çevirir ({aks, kat} → kata bağlı Z aksının adı). */
  function refAnahtar(bina, ref) {
    if (typeof ref === "number" || (typeof ref === "string" && /^\d+$/.test(ref))) return "d|" + (+ref);
    if (!ref || typeof ref !== "object") return "?|" + JSON.stringify(ref);
    if (ref.dugum != null) return "d|" + (+ref.dugum);
    if (aksRefMi(ref)) {
      let z = ref.z;
      if (z == null && ref.kat != null) { const a = katZAksi(bina, ref.kat); z = a ? a.ad : "kat" + ref.kat; }
      return "a|" + (ref.sistem || GLOBAL) + "|" + ref.aks[0] + "|" + ref.aks[1] + "|" + z;
    }
    return "?|" + JSON.stringify(ref);
  }
  function aksRef(S, a, b, z) {
    const r = { aks: [String(a), String(b)], z: String(z) };
    if (S && !S.global) return Object.assign({ sistem: S.ad }, r);
    return r;
  }
  /** Koordinat → aynı konumdaki (tol içinde) aks kesişimi REF'i (önce GLOBAL, sonra ek sistemler); yoksa null. */
  function koordinattanRef(bina, P, sec) {
    sec = sec || {};
    const tol = sec.tol == null ? TOL : +sec.tol;
    const S = sec._S || sistemler(bina);
    let en = null, ed = tol;
    S.forEach(function (s) {
      if (s.gorunur === false && sec.gizli !== true) return;
      const L = noktaSistem(s, P[0], P[1], P[2]);
      const yu = s.yonler[0], yv = s.yonler[1];
      const yak = function (l, v, dairesel) {
        let b = null, bd = Infinity;
        l.forEach(function (a) {
          let d = Math.abs(a.konum - v);
          if (dairesel) { d = Math.abs(((a.konum - v) % 360 + 540) % 360 - 180); }
          if (d < bd) { bd = d; b = a; }
        });
        return b;
      };
      const a = yak(s.l[yu], L[0]), b = yak(s.l[yv], L[1], s.tur === "silindirik"), z = yak(s.l.z, L[2]);
      if (!a || !b || !z) return;
      const Q = sistemNokta(s, a.konum, b.konum, z.konum);
      const d = uzaklik(P, Q);
      if (d <= ed + 1e-12 && (en == null || d < ed - 1e-12)) { ed = d; en = aksRef(s, a.ad, b.ad, z.ad); }
    });
    return en;
  }

  // ---------------------------------------------------------------- görünüm geometrisi
  function gorunumCoz(bina, g, Sl) {
    g = g || { tur: "plan" };
    const S = Sl || sistemler(bina);
    const tur = g.tur === "cephe" || g.tur === "3b" ? g.tur : "plan";
    const ana = sistemBul(bina, g.sistem, S);
    const o = { tur: tur, ana: ana, S: S };
    if (tur === "plan") {
      const z = g.z != null ? aksBul(ana, "z", g.z) : ana.l.z[0];
      if (!z) throw new AksHatasi("Plan görünümü için Z aksı yok; önce Z aksları tanımlayın.");
      o.z = z;
    } else if (tur === "cephe") {
      const yu = ana.yonler[0], yv = ana.yonler[1];
      if (g[yu] != null) { o.sabitYon = yu; o.sabit = aksBul(ana, yu, g[yu]); o.gezYon = yv; }
      else if (g[yv] != null) { o.sabitYon = yv; o.sabit = aksBul(ana, yv, g[yv]); o.gezYon = yu; }
      else throw new AksHatasi("Cephe görünümü için " + yonAdi(yu) + " ya da " + yonAdi(yv) + " aksı seçilmeli.");
    } else {
      o.z = g.z != null ? aksBul(ana, "z", g.z) : ana.l.z[0] || null;
    }
    return o;
  }
  /** Plan görünümünde çizilecek sistemler: seçili sistem + aynı Z akslarını paylaşan görünür ek sistemler. */
  function planSistemleri(o, g) {
    if (o.ana.zOrtak && !(g && g.yalnizSistem)) return o.S.filter(function (s) { return s.zOrtak && (s.global || s.gorunur !== false); });
    return [o.ana];
  }
  /** Görünüm düzlemindeki bütün aks kesişimleri: [{ref, P, sistem, adlar: [u, v, z]}]. */
  function kesisimler(bina, g) {
    const o = gorunumCoz(bina, g), l = [];
    const ekle = function (s, a, b, z) { l.push({ ref: aksRef(s, a.ad, b.ad, z.ad), P: sistemNokta(s, a.konum, b.konum, z.konum), sistem: s.ad, adlar: [a.ad, b.ad, z.ad] }); };
    if (o.tur === "plan") {
      planSistemleri(o, g).forEach(function (s) {
        const z = s === o.ana ? o.z : aksBul(s, "z", o.z.ad, false);
        if (!z) return;
        s.l[s.yonler[0]].forEach(function (a) { s.l[s.yonler[1]].forEach(function (b) { ekle(s, a, b, z); }); });
      });
    } else if (o.tur === "cephe") {
      const s = o.ana, ilk = o.sabitYon === s.yonler[0];
      s.l[o.gezYon].forEach(function (c) { s.l.z.forEach(function (z) { if (ilk) ekle(s, o.sabit, c, z); else ekle(s, c, o.sabit, z); }); });
    } else {
      o.S.forEach(function (s) {
        if (!s.global && s.gorunur === false) return;
        s.l[s.yonler[0]].forEach(function (a) { s.l[s.yonler[1]].forEach(function (b) { s.l.z.forEach(function (z) { ekle(s, a, b, z); }); }); });
      });
    }
    return l;
  }
  /** Görünüm düzlemindeki aks parçaları (komşu iki kesişim arası; hızlı çubuk için): [{i, j, Pi, Pj, aks: {sistem, yon, ad}, yay?}]. */
  function aksParcalari(bina, g) {
    const o = gorunumCoz(bina, g), l = [];
    const parca = function (s, yon, ad, ra, rb, yay) {
      const Pi = new Cozucu(bina).coz(ra), Pj = new Cozucu(bina).coz(rb);
      if (uzaklik(Pi, Pj) < TOL) return;
      const p = { i: ra, j: rb, Pi: Pi, Pj: Pj, aks: { sistem: s.ad, yon: yon, ad: ad } };
      if (yay) p.yay = true;
      l.push(p);
    };
    const duzlem = function (s, yu, yv, z, sabit) {
      // yu yönündeki her aks boyunca (yv akslarının ardışık çiftleri) ve tersi
      const lu = s.l[yu], lv = s.l[yv];
      const ref = function (au, av) { return s.yonler[0] === yu ? aksRef(s, au.ad, av.ad, z.ad) : aksRef(s, av.ad, au.ad, z.ad); };
      void sabit;
      lu.forEach(function (au) { for (let k = 0; k + 1 < lv.length; k++) parca(s, yu, au.ad, ref(au, lv[k]), ref(au, lv[k + 1]), s.tur === "silindirik" && yu === "r"); });
      lv.forEach(function (av) { for (let k = 0; k + 1 < lu.length; k++) parca(s, yv, av.ad, ref(lu[k], av), ref(lu[k + 1], av), s.tur === "silindirik" && yv === "r"); });
      if (s.tur === "silindirik" && lv.length > 2 && yv === "teta") {
        // tam çember: son θ aksından ilkine kapanış yayı (toplam açı ≥ 360 − son aralık)
        const ilk = lv[0], son = lv[lv.length - 1];
        if (360 - (son.konum - ilk.konum) <= Math.max.apply(null, konumdanAralik(lv.map(function (a) { return a.konum; }))) + 1e-9) {
          lu.forEach(function (au) { if (au.konum > TOL) parca(s, yu, au.ad, ref(au, son), ref(au, ilk), true); });
        }
      }
    };
    if (o.tur === "plan") {
      planSistemleri(o, g).forEach(function (s) {
        const z = s === o.ana ? o.z : aksBul(s, "z", o.z.ad, false);
        if (z) duzlem(s, s.yonler[0], s.yonler[1], z);
      });
    } else if (o.tur === "cephe") {
      const s = o.ana, ilk = o.sabitYon === s.yonler[0];
      const ref = function (c, z) { return ilk ? aksRef(s, o.sabit.ad, c.ad, z.ad) : aksRef(s, c.ad, o.sabit.ad, z.ad); };
      s.l[o.gezYon].forEach(function (c) { for (let k = 0; k + 1 < s.l.z.length; k++) parca(s, "z-dusey", c.ad, ref(c, s.l.z[k]), ref(c, s.l.z[k + 1])); });
      s.l.z.forEach(function (z) { const lc = s.l[o.gezYon]; for (let k = 0; k + 1 < lc.length; k++) parca(s, "z", z.ad, ref(lc[k], z), ref(lc[k + 1], z), s.tur === "silindirik" && o.gezYon === "teta"); });
      l.forEach(function (p) { if (p.aks.yon === "z-dusey") p.aks.yon = o.gezYon; });
    } else {
      o.S.forEach(function (s) {
        if (!s.global && s.gorunur === false) return;
        s.l.z.forEach(function (z) { duzlem(s, s.yonler[0], s.yonler[1], z); });
      });
    }
    return l;
  }
  /** Görünüm düzlemindeki gözler (dört kesişim arası; hızlı panel/çapraz için): [{koseler: [REF×4], P: [[X,Y,Z]×4], adlar}]. */
  function gozler(bina, g) {
    const o = gorunumCoz(bina, g), l = [], cz = new Cozucu(bina);
    const goz = function (s, r4, adlar) { l.push({ koseler: r4, P: r4.map(function (r) { return cz.coz(r); }), sistem: s.ad, adlar: adlar }); };
    if (o.tur === "plan" || o.tur === "3b") {
      const sl = o.tur === "plan" ? planSistemleri(o, g) : [o.ana];
      sl.forEach(function (s) {
        const z = s === o.ana ? o.z : aksBul(s, "z", o.z.ad, false);
        if (!z) return;
        const lu = s.l[s.yonler[0]], lv = s.l[s.yonler[1]];
        for (let i = 0; i + 1 < lu.length; i++) for (let j = 0; j + 1 < lv.length; j++) {
          if (s.tur === "silindirik" && lu[i].konum < TOL) continue;   // merkezdeki üçgen gözler dışarıda
          goz(s, [aksRef(s, lu[i].ad, lv[j].ad, z.ad), aksRef(s, lu[i + 1].ad, lv[j].ad, z.ad), aksRef(s, lu[i + 1].ad, lv[j + 1].ad, z.ad), aksRef(s, lu[i].ad, lv[j + 1].ad, z.ad)],
            [lu[i].ad + "–" + lu[i + 1].ad, lv[j].ad + "–" + lv[j + 1].ad, z.ad]);
        }
      });
    } else {
      const s = o.ana, ilk = o.sabitYon === s.yonler[0], lc = s.l[o.gezYon], lz = s.l.z;
      const ref = function (c, z) { return ilk ? aksRef(s, o.sabit.ad, c.ad, z.ad) : aksRef(s, c.ad, o.sabit.ad, z.ad); };
      for (let i = 0; i + 1 < lc.length; i++) for (let k = 0; k + 1 < lz.length; k++) {
        goz(s, [ref(lc[i], lz[k]), ref(lc[i + 1], lz[k]), ref(lc[i + 1], lz[k + 1]), ref(lc[i], lz[k + 1])], [o.sabit.ad, lc[i].ad + "–" + lc[i + 1].ad, lz[k].ad + "–" + lz[k + 1].ad]);
      }
    }
    return l;
  }
  /** Görünüm düzlemine düşen bölme/kesişim düğümleri (yakalama için): [{ref: {dugum}, P}]. */
  function duzlemDugumleri(bina, g, tol) {
    const o = gorunumCoz(bina, g), cz = new Cozucu(bina), l = [];
    tol = tol == null ? 0.01 : tol;
    dugumHaritasi(bina).forEach(function (d, no) {
      if (d.tur !== "bolme" && d.tur !== "kesisim") return;
      let P;
      try { P = cz.coz({ dugum: no }); } catch (e) { return; }
      if (o.tur === "plan") { if (Math.abs(P[2] - sistemNokta(o.ana, 0, 0, o.z.konum)[2]) > tol) return; }
      else if (o.tur === "cephe") {
        const L = noktaSistem(o.ana, P[0], P[1], P[2]);
        const i = o.sabitYon === o.ana.yonler[0] ? 0 : 1;
        if (Math.abs(L[i] - o.sabit.konum) > (o.ana.tur === "silindirik" && i === 1 ? 0.01 : tol)) return;
      }
      l.push({ ref: { dugum: no }, P: P, tur: d.tur });
    });
    return l;
  }
  /**
   * Bir noktaya en yakın kesişim (görünüm düzleminde).
   * nokta: ekran [x, y] (sec.izdusum verildiyse; tolerans px) ya da bina [X, Y, Z] (tolerans m).
   * sec: {izdusum(X,Y,Z) → [x,y], tol (px: 14, m: 0.25), dugumler: true (bölme/kesişim düğümlerine de yakala)}
   * Dönüş: {ref, P, uzaklik, tur: "kesisim"|"bolme"|"kesisim-dugumu"} ya da null.
   */
  function enYakinKesisim(bina, g, nokta, sec) {
    sec = sec || {};
    const iz = typeof sec.izdusum === "function" ? sec.izdusum : null;
    const tol = sec.tol != null ? +sec.tol : (iz ? 14 : 0.25);
    const aday = kesisimler(bina, g).map(function (k) { return { ref: k.ref, P: k.P, tur: "kesisim" }; });
    if (sec.dugumler !== false) duzlemDugumleri(bina, g).forEach(function (d) { aday.push({ ref: d.ref, P: d.P, tur: d.tur === "bolme" ? "bolme" : "kesisim-dugumu" }); });
    let en = null, ed = tol;
    aday.forEach(function (a) {
      let d;
      if (iz) { const q = iz(a.P[0], a.P[1], a.P[2]); d = Math.hypot(q[0] - nokta[0], q[1] - nokta[1]); }
      else d = uzaklik(a.P, nokta);
      // eşit uzaklıkta düğüm kaydı değil aks kesişimi tercih edilir (aday sırası)
      if (d < ed - 1e-9 || (d <= ed && !en)) { ed = d; en = { ref: a.ref, P: a.P, uzaklik: d, tur: a.tur }; }
    });
    return en;
  }
  /** Ekran noktasına en yakın aks parçası (hızlı çubuk): {parca, uzaklik} ya da null. sec: {izdusum, tol: 10 px}. */
  function enYakinParca(bina, g, nokta, sec) {
    sec = sec || {};
    const iz = sec.izdusum, tol = sec.tol != null ? +sec.tol : 10;
    let en = null, ed = tol;
    aksParcalari(bina, g).forEach(function (p) {
      const a = iz(p.Pi[0], p.Pi[1], p.Pi[2]), b = iz(p.Pj[0], p.Pj[1], p.Pj[2]);
      const d = noktaParca(nokta, a, b);
      if (d.d <= ed && d.t > 0.05 && d.t < 0.95) { ed = d.d; en = { parca: p, uzaklik: d.d }; }
    });
    return en;
  }
  /** Ekran noktasını içeren göz (hızlı panel/çapraz): göz nesnesi ya da null. */
  function gozBul(bina, g, nokta, sec) {
    const iz = sec && sec.izdusum;
    const l = gozler(bina, g);
    for (let i = l.length - 1; i >= 0; i--) {
      const pts = l[i].P.map(function (P) { return iz ? iz(P[0], P[1], P[2]) : [P[0], P[1]]; });
      if (cokgenIcinde(pts, nokta[0], nokta[1])) return l[i];
    }
    return null;
  }
  function noktaParca(p, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
    let t = L2 > 0 ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2 : 0;
    t = Math.max(0, Math.min(1, t));
    return { d: Math.hypot(a[0] + dx * t - p[0], a[1] + dy * t - p[1]), t: t };
  }
  function cokgenIcinde(pts, x, y) {
    let i_ = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const xi = pts[i][0], yi = pts[i][1], xj = pts[j][0], yj = pts[j][1];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) i_ = !i_;
    }
    return i_;
  }
  /** PgUp/PgDn: görünüm düzlemini bir sonraki/önceki aksa taşır (plan: Z; cephe: sabit aks yönü). */
  function gorunumKomsu(bina, g, adim) {
    const o = gorunumCoz(bina, g);
    const n = Object.assign({}, g);
    if (o.tur === "plan" || o.tur === "3b") {
      const l = o.ana.l.z, i = l.indexOf(o.z);
      const j = Math.max(0, Math.min(l.length - 1, i + (adim || 1)));
      n.z = l[j].ad;
    } else {
      const l = o.ana.l[o.sabitYon], i = l.indexOf(o.sabit);
      const j = Math.max(0, Math.min(l.length - 1, i + (adim || 1)));
      n[o.sabitYon] = l[j].ad;
    }
    return n;
  }

  // ---------------------------------------------------------------- model gezgini (REF'ler)
  /** Modeldeki bütün REF konumlarını gezer; fn(ref, yer) yeni REF döndürür (ya da aynısını). Model yerinde değişir (kopyada kullanılır). */
  function refleriGez(m, fn) {
    (m.cubuklar || []).forEach(function (c, k) { if (!c) return; c.i = fn(c.i, { liste: "cubuklar", no: c.no, k: k, uc: "i" }); c.j = fn(c.j, { liste: "cubuklar", no: c.no, k: k, uc: "j" }); });
    (m.paneller || []).forEach(function (p, k) { if (p && Array.isArray(p.kose)) p.kose = p.kose.map(function (r, i) { return fn(r, { liste: "paneller", no: p.no, k: k, kose: i }); }); });
    (m.mesnetler || []).forEach(function (s, k) { if (s && s.dugum != null) s.dugum = fn(s.dugum, { liste: "mesnetler", k: k }); });
    (m.ek_yukler || []).forEach(function (y, k) { if (y && y.tur === "dugum" && y.dugum != null) y.dugum = fn(y.dugum, { liste: "ek_yukler", k: k }); });
    (m.dugumler || []).forEach(function (d, k) {
      if (!d) return;
      if (d.tur === "bolme") { d.cubuk_i = fn(d.cubuk_i, { liste: "dugumler", no: d.no, k: k }); d.cubuk_j = fn(d.cubuk_j, { liste: "dugumler", no: d.no, k: k }); }
      else if (d.tur === "kesisim") {
        if (Array.isArray(d.a)) d.a = d.a.map(function (r) { return fn(r, { liste: "dugumler", no: d.no, k: k }); });
        if (Array.isArray(d.b)) d.b = d.b.map(function (r) { return fn(r, { liste: "dugumler", no: d.no, k: k }); });
      }
    });
    (m.uretecler || []).forEach(function (u, k) {
      if (u && Array.isArray(u.goz)) u.goz = u.goz.map(function (r) { return fn(r, { liste: "uretecler", no: u.no, k: k }); });
    });
  }
  /** REF bu aksı kullanıyor mu? (sistem, yön, ad) — aks–kat ({aks, kat}) REF'leri de. */
  function refAksiKullanir(bina, ref, sistemAd, yon, ad, S) {
    if (!aksRefMi(ref)) return false;
    const rs = ref.sistem || GLOBAL;
    const Sr = S.find(function (s) { return s.ad === rs; });
    if (!Sr) return false;
    if (yon === "z") {
      // GLOBAL Z aksı: GLOBAL ve z-ortak sistemlerin REF'leri
      const hedef = sistemAd || GLOBAL;
      const ayniZ = rs === hedef || (hedef === GLOBAL && Sr.zOrtak);
      if (!ayniZ) return false;
      if (ref.z != null) return String(ref.z) === String(ad);
      if (ref.kat != null) { const a = katZAksi(bina, ref.kat); return !!a && a.ad === String(ad); }
      return false;
    }
    if (rs !== (sistemAd || GLOBAL)) return false;
    const i = Sr.yonler.indexOf(yon);
    return i >= 0 && i < 2 && String(ref.aks[i]) === String(ad);
  }
  function eslesenAksKat(m, yon, ad, kat) {
    // aks–kat elemanları (yalnız GLOBAL x/y; z için kat)
    const r = { kolonlar: [], kirisler: [], dosemeler: [], temeller: [], ek_yukler_aks: [] };
    const xy = function (a) { return Array.isArray(a) && (yon === "x" ? String(a[0]) === ad : yon === "y" ? String(a[1]) === ad : false); };
    if (yon === "x" || yon === "y") {
      (m.kolonlar || []).forEach(function (c) { if (xy(c.aks)) r.kolonlar.push(c.no); });
      (m.kirisler || []).forEach(function (k) { if (xy(k.bas) || xy(k.son)) r.kirisler.push(k.no); });
      (m.dosemeler || []).forEach(function (d) { if (Array.isArray(d.kose) && d.kose.some(xy)) r.dosemeler.push(d.no); });
      ((m.temeller && m.temeller.ozel) || []).forEach(function (t, i) { if (xy(t.aks)) r.temeller.push(i); });
      (m.ek_yukler || []).forEach(function (y, i) { if (y && y.tur === "dugum" && y.dugum == null && xy(y.aks)) r.ek_yukler_aks.push(i); });
    } else if (kat != null) {
      (m.kolonlar || []).forEach(function (c) { const k = c.kat == null ? 1 : +c.kat; if (k === kat || k - 1 === kat) r.kolonlar.push(c.no); });
      (m.kirisler || []).forEach(function (k) { if ((k.kat == null ? 1 : +k.kat) === kat) r.kirisler.push(k.no); });
      (m.dosemeler || []).forEach(function (d) { if ((d.kat == null ? 1 : +d.kat) === kat) r.dosemeler.push(d.no); });
      (m.ek_yukler || []).forEach(function (y, i) { if (y && y.tur === "dugum" && y.dugum == null && y.aks && (y.kat == null ? 1 : +y.kat) === kat) r.ek_yukler_aks.push(i); });
    }
    return r;
  }
  /**
   * Bir aksa bağlı elemanlar (silme uyarısı için). Bölme/kesişim düğümleri üzerinden dolaylı bağlılık da sayılır.
   * hedef: {sistem, yon, ad}. Dönüş: {cubuklar, paneller, mesnetler, ek_yukler, dugumler, kolonlar, kirisler, dosemeler, temeller, toplam, ozet}
   */
  function bagliElemanlar(bina, hedef) {
    const S = sistemler(bina);
    const sAd = hedef.sistem || GLOBAL, yon = hedef.yon, ad = String(hedef.ad);
    const Sh = sistemBul(bina, sAd, S);
    aksBul(Sh, yon, ad);
    // bağımlı düğümler (sabit nokta yinelemesi)
    const dh = dugumHaritasi(bina);
    const bagliDugum = new Set();
    const refBagli = function (r) {
      if (aksRefMi(r)) return refAksiKullanir(bina, r, sAd, yon, ad, S);
      const no = typeof r === "number" ? r : (r && r.dugum != null ? +r.dugum : null);
      return no != null && bagliDugum.has(no);
    };
    let degisti = true;
    while (degisti) {
      degisti = false;
      dh.forEach(function (d, no) {
        if (bagliDugum.has(no)) return;
        let refs = [];
        if (d.tur === "bolme") refs = [d.cubuk_i, d.cubuk_j];
        else if (d.tur === "kesisim") refs = [].concat(d.a || [], d.b || []);
        if (refs.some(refBagli)) { bagliDugum.add(no); degisti = true; }
      });
    }
    const r = { cubuklar: [], paneller: [], mesnetler: [], ek_yukler: [], dugumler: Array.from(bagliDugum).sort(function (a, b) { return a - b; }) };
    (bina.cubuklar || []).forEach(function (c) { if (c && (refBagli(c.i) || refBagli(c.j))) r.cubuklar.push(c.no); });
    (bina.paneller || []).forEach(function (p) { if (p && Array.isArray(p.kose) && p.kose.some(refBagli)) r.paneller.push(p.no); });
    (bina.mesnetler || []).forEach(function (s, i) { if (s && refBagli(s.dugum)) r.mesnetler.push(i); });
    const cset = new Set(r.cubuklar);
    (bina.ek_yukler || []).forEach(function (y, i) {
      if (!y) return;
      if ((y.tur === "dugum" && y.dugum != null && refBagli(y.dugum)) || (y.tur === "cubuk" && cset.has(+y.cubuk))) r.ek_yukler.push(i);
    });
    let kat = null;
    if (yon === "z" && sAd === GLOBAL) { const a = aksBul(Sh, "z", ad); kat = a.kat != null ? a.kat : null; }
    const ak = sAd === GLOBAL ? eslesenAksKat(bina, yon, ad, kat) : { kolonlar: [], kirisler: [], dosemeler: [], temeller: [], ek_yukler_aks: [] };
    r.kolonlar = ak.kolonlar; r.kirisler = ak.kirisler; r.dosemeler = ak.dosemeler; r.temeller = ak.temeller;
    ak.ek_yukler_aks.forEach(function (i) { if (r.ek_yukler.indexOf(i) < 0) r.ek_yukler.push(i); });
    const ks = new Set(r.kirisler), ds = new Set(r.dosemeler);
    (bina.ek_yukler || []).forEach(function (y, i) {
      if (!y || r.ek_yukler.indexOf(i) >= 0) return;
      if ((y.tur === "kiris" && ks.has(+y.kiris)) || (y.tur === "doseme" && ds.has(+y.doseme))) r.ek_yukler.push(i);
    });
    r.ek_yukler.sort(function (a, b) { return a - b; });
    r.kat = kat;
    r.toplam = r.cubuklar.length + r.paneller.length + r.mesnetler.length + r.ek_yukler.length + r.dugumler.length + r.kolonlar.length + r.kirisler.length + r.dosemeler.length + r.temeller.length;
    const parca = [];
    [["cubuklar", "çubuk"], ["paneller", "panel"], ["kolonlar", "kolon"], ["kirisler", "kiriş"], ["dosemeler", "döşeme"], ["mesnetler", "mesnet"],
      ["ek_yukler", "yük"], ["dugumler", "bölme/kesişim düğümü"], ["temeller", "özel temel"]].forEach(function (p) { if (r[p[0]].length) parca.push(r[p[0]].length + " " + p[1]); });
    r.ozet = parca.join(", ");
    return r;
  }

  // ---------------------------------------------------------------- aks düzenleme (saf)
  /** Değiştirilebilir ham aks listesi (model kopyası üzerinde). GLOBAL z yoksa katlardan kurulur. */
  function hamListe(m, sistemAd, yon) {
    const sAd = sistemAd || GLOBAL;
    if (sAd === GLOBAL) {
      if (!m.akslar) m.akslar = { x: [], y: [] };
      if (yon === "z" && (!Array.isArray(m.akslar.z) || !m.akslar.z.length)) m.akslar.z = zTuret(m.katlar);
      if (["x", "y", "z"].indexOf(yon) < 0) throw new AksHatasi("GLOBAL sistemde yön x, y ya da z olmalı.");
      if (!Array.isArray(m.akslar[yon])) m.akslar[yon] = [];
      return m.akslar[yon];
    }
    const s = (m.aks_sistemleri || []).find(function (x) { return x && String(x.ad) === String(sAd); });
    if (!s) throw new AksHatasi("\"" + sAd + "\" adlı aks sistemi yok.");
    if (yon === "z" && (!Array.isArray(s.z) || !s.z.length)) return hamListe(m, GLOBAL, "z");
    if (yonler(s.tur).indexOf(yon) < 0) throw new AksHatasi(sAd + " sisteminde \"" + yon + "\" yönü yok.");
    if (!Array.isArray(s[yon])) s[yon] = [];
    return s[yon];
  }
  function hamBul(liste, ad) {
    const a = liste.find(function (x) { return String(x.ad) === String(ad); });
    if (!a) throw new AksHatasi("\"" + ad + "\" adlı aks yok.");
    return a;
  }
  function zGlobalMi(m, sistemAd, yon) {
    if (yon !== "z") return false;
    if (!sistemAd || sistemAd === GLOBAL) return true;
    const s = (m.aks_sistemleri || []).find(function (x) { return x && String(x.ad) === String(sistemAd); });
    return !!s && (!Array.isArray(s.z) || !s.z.length);
  }
  function sonuc(m, uy, ek) {
    let r = { model: m, uyarilar: uy || [] };
    if (m.akslar && Array.isArray(m.akslar.z) && m.akslar.z.some(function (a) { return a.kat != null; })) {
      const s = katlariSenkronla(m);
      r.model = s.model;
      s.uyarilar.forEach(function (u) { if (r.uyarilar.indexOf(u) < 0) r.uyarilar.push(u); });
    }
    aralikDenetle(r.model).forEach(function (u) { if (r.uyarilar.indexOf(u) < 0) r.uyarilar.push(u); });
    return Object.assign(r, ek || {});
  }
  /** Motor sınırı: GLOBAL X/Y aksları arası ≥ 0.3 m; ayrıca aynı konumda iki aks. */
  function aralikDenetle(m) {
    const uy = [];
    const G = globalSistem(m);
    ["x", "y"].forEach(function (yon) {
      const l = G.l[yon];
      for (let i = 1; i < l.length; i++) {
        const d = l[i].konum - l[i - 1].konum;
        if (d < EN_AZ_ARALIK - 1e-9) uy.push(yonAdi(yon) + " aksları " + l[i - 1].ad + "–" + l[i].ad + " arası " + fmt(d) + " m; hesap motoru en az 0,30 m ister.");
      }
    });
    const z = G.l.z;
    for (let i = 1; i < z.length; i++) if (z[i].konum - z[i - 1].konum < TOL) uy.push("Z aksları " + z[i - 1].ad + " ve " + z[i].ad + " aynı kotta.");
    return uy;
  }
  /**
   * Serbest koordinatlı (eski) düğümleri aksla birlikte taşı (yapışık): aksın eski konumundaki düğümler yeni konuma.
   * Aks adıyla başvurulan elemanlar zaten adla bağlıdır; bu yalnız {X,Y,Z} kayıtları içindir.
   */
  function serbestleriTasi(m, Sonce, yon, eski, yeni, uy) {
    let n = 0;
    (m.dugumler || []).forEach(function (d) {
      if (!d || d.tur || d.X == null) return;
      const L = noktaSistem(Sonce, +d.X, +d.Y, +d.Z);
      const i = Sonce.yonler.indexOf(yon);
      if (i < 0 || Math.abs(L[i] - eski) > TOL) return;
      L[i] = yeni;
      const P = sistemNokta(Sonce, L[0], L[1], L[2]);
      d.X = P[0]; d.Y = P[1]; d.Z = P[2];
      n++;
    });
    if (n) uy.push(n + " serbest koordinatlı düğüm aksla birlikte taşındı.");
  }
  /**
   * Aksı yeni konuma taşır. Adla başvurulan bütün elemanlar aksa yapışıktır (model aynı kalır, geometri değişir).
   * p: {sistem, yon, ad, konum, kaydir: false (sonrakileri de aynı farkla kaydır), yapisik: true (serbest düğümleri de taşı)}
   */
  function aksTasi(bina, p) {
    const m = kopya(bina);
    const uy = [];
    const S0 = sistemBul(bina, p.sistem);
    const liste = hamListe(m, p.sistem, p.yon);
    const a = hamBul(liste, p.ad);
    const yeni = sayiOku(p.konum);
    if (yeni == null) throw new AksHatasi("Konum sayı olmalı.");
    const eski = +a.konum, fark = r6(yeni - eski);
    const tasinan = [a];
    if (p.kaydir) liste.forEach(function (b) { if (b !== a && +b.konum > eski + 1e-9) tasinan.push(b); });
    const sonra = sirali(liste, p.yon);
    const oncekiSira = sonra.map(function (x) { return x.ad; }).join("|");
    tasinan.forEach(function (b) {
      const k0 = +b.konum;
      b.konum = r6(k0 + fark);
      if (p.yapisik !== false) serbestleriTasi(m, S0, p.yon, k0, b.konum, uy);
    });
    const yeniSira = sirali(liste, p.yon).map(function (x) { return x.ad; }).join("|");
    if (oncekiSira !== yeniSira) uy.push(yonAdi(p.yon) + " akslarının sırası değişti; adlar yerinde kaldı (gerekirse \"Yeniden adlandır\").");
    return sonuc(m, uy, { tasinan: tasinan.map(function (b) { return String(b.ad); }) });
  }
  /** Aralığı (bir önceki aksa uzaklık) değiştirir: konum = önceki + aralık. kaydir: sonrakiler de kayar. */
  function aralikDegistir(bina, p) {
    const S = sistemBul(bina, p.sistem);
    const l = S.l[p.yon];
    if (!l) throw new AksHatasi("Yön tanımsız: " + p.yon);
    const i = l.findIndex(function (a) { return a.ad === String(p.ad); });
    if (i < 0) throw new AksHatasi("\"" + p.ad + "\" adlı aks yok.");
    if (i === 0) throw new AksHatasi("İlk aksın aralığı yoktur; konumunu değiştirin.");
    const ar = sayiOku(p.aralik);
    if (ar == null || !(ar > 0)) throw new AksHatasi("Aralık sıfırdan büyük bir sayı olmalı.");
    return aksTasi(bina, { sistem: p.sistem, yon: p.yon, ad: p.ad, konum: r6(l[i - 1].konum + ar), kaydir: !!p.kaydir, yapisik: p.yapisik });
  }
  /**
   * Aks ekler. p: {sistem, yon, konum | arasina: [ad1, ad2] (ortasına) | sona: aralik, ad?, tur, gorunur, balon, kat}
   * Ad verilmezse: sona eklenirse sonraki harf/sayı; araya eklenirse öncekinin adı + "'" (A'); Z'de kot adı.
   */
  function aksEkle(bina, p) {
    const m = kopya(bina);
    const S = sistemBul(bina, p.sistem);
    const l = S.l[p.yon];
    if (!l) throw new AksHatasi("Yön tanımsız: " + p.yon);
    const liste = hamListe(m, p.sistem, p.yon);
    let konum = p.konum != null ? sayiOku(p.konum) : null, onceki = null;
    if (konum == null && Array.isArray(p.arasina)) {
      const a = aksBul(S, p.yon, p.arasina[0]), b = aksBul(S, p.yon, p.arasina[1]);
      konum = r6((a.konum + b.konum) / 2);
      onceki = a.konum <= b.konum ? a : b;
    } else if (konum == null) {
      const son = l[l.length - 1];
      const ar = p.sona != null ? sayiOku(p.sona) : (l.length > 1 ? son.konum - l[l.length - 2].konum : (p.yon === "z" ? 3 : p.yon === "teta" ? 30 : 6));
      konum = son ? r6(son.konum + ar) : 0;
    }
    if (konum == null) throw new AksHatasi("Yeni aksın konumu belirlenemedi.");
    if (l.some(function (a) { return Math.abs(a.konum - konum) < TOL; })) throw new AksHatasi(fmt(konum) + " m konumunda zaten bir aks var.");
    const adlar = liste.map(function (a) { return String(a.ad); });
    let ad = p.ad != null && String(p.ad).trim() !== "" ? String(p.ad).trim() : null;
    if (ad && adlar.indexOf(ad) >= 0) throw new AksHatasi("\"" + ad + "\" adı bu yönde zaten var; aks adları benzersiz olmalı.");
    if (!ad) {
      if (p.yon === "z") ad = benzersizAd(kotAdi(konum), adlar);
      else {
        if (!onceki) { const ar = l.filter(function (a) { return a.konum < konum; }); onceki = ar.length < l.length ? ar[ar.length - 1] || null : null; }
        ad = onceki ? benzersizAd(onceki.ad + "'", adlar) : (konum < (l[0] ? l[0].konum : 0) ? benzersizAd(l[0].ad + "0", adlar) : sonrakiAd(liste, p.yon));
      }
    }
    const yeni = { ad: ad, konum: r6(konum) };
    if (p.yon !== "z") { yeni.tur = p.tur === "ikincil" ? "ikincil" : "ana"; yeni.gorunur = p.gorunur !== false; yeni.balon = BALON_YERLERI.indexOf(p.balon) >= 0 ? p.balon : "bas"; }
    else if (p.kat != null) yeni.kat = +p.kat;
    liste.push(yeni);
    liste.sort(function (a, b) { return +a.konum - +b.konum; });
    return sonuc(m, [], { eklenen: ad });
  }
  /** REF'lerde ve aks–kat elemanlarında aks adını eşleme tablosuyla değiştirir (sistem/yön kapsamında). */
  function adlariUygula(m, bina, sAd, yon, esle) {
    const S = sistemler(bina);
    const Sh = sistemBul(bina, sAd, S);
    const iz = Sh.yonler.indexOf(yon);
    refleriGez(m, function (r) {
      if (!aksRefMi(r)) return r;
      const rs = r.sistem || GLOBAL;
      if (yon === "z") {
        const Sr = S.find(function (s) { return s.ad === rs; });
        const kapsam = rs === sAd || (sAd === GLOBAL && Sr && Sr.zOrtak);
        if (kapsam && r.z != null && esle.has(String(r.z))) return Object.assign({}, r, { z: esle.get(String(r.z)) });
        return r;
      }
      if (rs !== sAd || iz < 0 || iz > 1 || !esle.has(String(r.aks[iz]))) return r;
      const a = r.aks.slice(); a[iz] = esle.get(String(a[iz]));
      return Object.assign({}, r, { aks: a });
    });
    if (sAd === GLOBAL && (yon === "x" || yon === "y")) {
      const k = yon === "x" ? 0 : 1;
      const ad2 = function (a) { if (Array.isArray(a) && esle.has(String(a[k]))) { a = a.slice(); a[k] = esle.get(String(a[k])); } return a; };
      (m.kolonlar || []).forEach(function (c) { c.aks = ad2(c.aks); });
      (m.kirisler || []).forEach(function (c) { c.bas = ad2(c.bas); c.son = ad2(c.son); });
      (m.dosemeler || []).forEach(function (d) { if (Array.isArray(d.kose)) d.kose = d.kose.map(ad2); });
      if (m.temeller && Array.isArray(m.temeller.ozel)) m.temeller.ozel.forEach(function (t) { t.aks = ad2(t.aks); });
      (m.ek_yukler || []).forEach(function (y) { if (y && y.aks) y.aks = ad2(y.aks); });
    }
  }
  /** Aksı yeniden adlandırır; bütün REF'ler (ve aks–kat elemanları) güncellenir. p: {sistem, yon, eski, yeni} */
  function aksYenidenAdlandir(bina, p) {
    const m = kopya(bina);
    const liste = hamListe(m, p.sistem, p.yon);
    const a = hamBul(liste, p.eski);
    const yeni = String(p.yeni == null ? "" : p.yeni).trim();
    if (!yeni) throw new AksHatasi("Yeni ad boş olamaz.");
    if (yeni === String(p.eski)) return sonuc(m, [], { esleme: {} });
    if (liste.some(function (b) { return b !== a && String(b.ad) === yeni; })) throw new AksHatasi("\"" + yeni + "\" adı bu yönde zaten var; aks adları benzersiz olmalı.");
    a.ad = yeni;
    const esle = new Map([[String(p.eski), yeni]]);
    adlariUygula(m, bina, p.sistem || GLOBAL, p.yon, esle);
    const es = {}; es[String(p.eski)] = yeni;
    return sonuc(m, [], { esleme: es });
  }
  /** Bütün aksları konum sırasına göre yeniden adlandırır (A, B, C… ya da 1, 2, 3…). p: {sistem, yon, ilk} */
  function yenidenHarfle(bina, p) {
    const m = kopya(bina);
    const S = sistemBul(bina, p.sistem);
    const l = S.l[p.yon];
    if (!l) throw new AksHatasi("Yön tanımsız: " + p.yon);
    const liste = hamListe(m, p.sistem, p.yon);
    let adlar;
    if (p.yon === "z") adlar = l.map(function (a) { return kotAdi(a.konum); });
    else adlar = adlarUret(p.yon, l.length, p.ilk);
    const esle = new Map();
    l.forEach(function (a, i) { if (a.ad !== adlar[i]) esle.set(a.ad, adlar[i]); });
    if (new Set(adlar).size !== adlar.length) throw new AksHatasi("Üretilen adlar benzersiz değil (aynı kotta iki Z aksı?).");
    liste.forEach(function (a) { if (esle.has(String(a.ad))) a.ad = esle.get(String(a.ad)); });
    adlariUygula(m, bina, p.sistem || GLOBAL, p.yon, esle);
    const es = {}; esle.forEach(function (v, k) { es[k] = v; });
    return sonuc(m, [], { esleme: es });
  }
  /** Ham listeyi konuma göre sıralar (başvurular adla olduğu için model geometrisi değişmez). */
  function aksSirala(bina, p) {
    const m = kopya(bina);
    hamListe(m, p.sistem, p.yon).sort(function (a, b) { return +a.konum - +b.konum; });
    return sonuc(m, []);
  }
  /** Aksı ofsetle çoğaltır: adet kopya, konum + k·ofset (özellikler kopyalanır, ad otomatik). */
  function aksCogalt(bina, p) {
    const S = sistemBul(bina, p.sistem);
    const a = aksBul(S, p.yon, p.ad);
    const ofs = sayiOku(p.ofset), n = p.adet == null ? 1 : Math.round(+p.adet);
    if (ofs == null || Math.abs(ofs) < TOL) throw new AksHatasi("Ofset sıfırdan farklı bir sayı olmalı.");
    if (!(n >= 1 && n <= 100)) throw new AksHatasi("Adet 1 ile 100 arasında olmalı.");
    let b = bina, eklenen = [], uy = [];
    for (let k = 1; k <= n; k++) {
      const r = aksEkle(b, { sistem: p.sistem, yon: p.yon, konum: r6(a.konum + k * ofs), tur: a.tur, gorunur: a.gorunur, balon: a.balon });
      b = r.model; eklenen.push(r.eklenen); uy = r.uyarilar;
    }
    return { model: b, uyarilar: uy, eklenen: eklenen };
  }
  /** Görsel özellikler: {tur, gorunur, balon} (ve Z'de kat). */
  function aksOzellik(bina, p) {
    const m = kopya(bina);
    const a = hamBul(hamListe(m, p.sistem, p.yon), p.ad);
    const o = p.ozellik || {};
    if (o.tur != null) a.tur = o.tur === "ikincil" ? "ikincil" : "ana";
    if (o.gorunur != null) a.gorunur = !!o.gorunur;
    if (o.balon != null) { if (BALON_YERLERI.indexOf(o.balon) < 0) throw new AksHatasi("Balon yeri: " + BALON_YERLERI.join(", ")); a.balon = o.balon; }
    if ("kat" in o && p.yon === "z") {
      if (o.kat == null || o.kat === "") delete a.kat;
      else {
        const k = +o.kat;
        if (hamListe(m, p.sistem, "z").some(function (b) { return b !== a && b.kat != null && +b.kat === k; })) throw new AksHatasi("Kat " + k + " başka bir Z aksına bağlı.");
        a.kat = k;
      }
    }
    return sonuc(m, []);
  }
  /** Bağlı elemanları siler (aksSil "elemanlarla"). */
  function elemanlariSil(m, b) {
    const set = function (l) { return new Set(l); };
    const cs = set(b.cubuklar), ps = set(b.paneller), ds = set(b.dugumler), ms = set(b.mesnetler), ys = set(b.ek_yukler);
    const ko = set(b.kolonlar), ki = set(b.kirisler), do_ = set(b.dosemeler), te = set(b.temeller);
    m.cubuklar = (m.cubuklar || []).filter(function (c) { return !cs.has(c.no); });
    m.paneller = (m.paneller || []).filter(function (p) { return !ps.has(p.no); });
    m.dugumler = (m.dugumler || []).filter(function (d) { return !ds.has(+d.no); });
    m.mesnetler = (m.mesnetler || []).filter(function (s, i) { return !ms.has(i); });
    m.ek_yukler = (m.ek_yukler || []).filter(function (y, i) { return !ys.has(i); });
    if (m.kolonlar) m.kolonlar = m.kolonlar.filter(function (c) { return !ko.has(c.no); });
    if (m.kirisler) m.kirisler = m.kirisler.filter(function (c) { return !ki.has(c.no); });
    if (m.dosemeler) m.dosemeler = m.dosemeler.filter(function (c) { return !do_.has(c.no); });
    if (m.temeller && Array.isArray(m.temeller.ozel)) m.temeller.ozel = m.temeller.ozel.filter(function (t, i) { return !te.has(i); });
    (m.kren || []).forEach(function (k) { if (k && Array.isArray(k.yol)) k.yol = k.yol.filter(function (x) { return !cs.has(+x); }); });
  }
  /** "En yakın aksa taşı" sonrası bozulan elemanları ayıklar (sıfır boylu çubuk, çakışan kolon, < 3 köşeli panel...). */
  function bozuklariAyikla(m, uy) {
    const anahtar = function (r) { return refAnahtar(m, r); };
    const silC = [];
    m.cubuklar = (m.cubuklar || []).filter(function (c) {
      if (anahtar(c.i) === anahtar(c.j)) { silC.push(c.no); return false; }
      return true;
    });
    if (silC.length) uy.push("Uçları aynı kesişime düşen " + silC.length + " çubuk silindi (" + silC.join(", ") + ").");
    const silP = [];
    m.paneller = (m.paneller || []).filter(function (p) {
      if (!Array.isArray(p.kose)) return true;
      const g = [], gor = new Set();
      p.kose.forEach(function (r) { const k = anahtar(r); if (!gor.has(k)) { gor.add(k); g.push(r); } });
      p.kose = g;
      if (g.length < 3) { silP.push(p.no); return false; }
      return true;
    });
    if (silP.length) uy.push("Köşeleri çakışan " + silP.length + " panel silindi (" + silP.join(", ") + ").");
    const silK = [];
    if (m.kirisler) m.kirisler = m.kirisler.filter(function (k) {
      if (Array.isArray(k.bas) && Array.isArray(k.son) && String(k.bas) === String(k.son)) { silK.push(k.no); return false; }
      return true;
    });
    if (silK.length) uy.push("Başı ve sonu aynı aksa düşen " + silK.length + " kiriş silindi.");
    if (m.kolonlar) {
      const gor = new Set(), sil = [];
      m.kolonlar = m.kolonlar.filter(function (c) { const k = String(c.aks) + "|" + c.kat; if (gor.has(k)) { sil.push(c.no); return false; } gor.add(k); return true; });
      if (sil.length) uy.push("Aynı kesişime düşen " + sil.length + " kolon silindi.");
    }
    if (m.dosemeler) {
      const sil = [];
      m.dosemeler = m.dosemeler.filter(function (d) {
        if (Array.isArray(d.kose) && d.kose.length === 2 && (String(d.kose[0][0]) === String(d.kose[1][0]) || String(d.kose[0][1]) === String(d.kose[1][1]))) { sil.push(d.no); return false; }
        return true;
      });
      if (sil.length) uy.push("Alanı sıfıra inen " + sil.length + " döşeme silindi.");
    }
  }
  /**
   * Aks siler. p: {sistem, yon, ad, secenek: undefined | "elemanlarla" | "tasi" | "iptal"}
   * Bağlı eleman varsa ve seçenek verilmediyse model değişmez: {onayGerekli: true, bagli, secenekler, komsu}.
   * "elemanlarla": bağlı çubuk/panel/mesnet/yük/kolon/kiriş/döşeme (dolaylı: bölme düğümleri) de silinir.
   * "tasi": başvurular en yakın komşu aksa aktarılır; bozulan elemanlar ayıklanıp raporlanır.
   */
  function aksSil(bina, p) {
    const S = sistemBul(bina, p.sistem);
    const a = aksBul(S, p.yon, p.ad);
    const l = S.l[p.yon];
    const b = bagliElemanlar(bina, { sistem: p.sistem, yon: p.yon, ad: p.ad });
    let komsu = null;
    l.forEach(function (x) { if (x !== a && (!komsu || Math.abs(x.konum - a.konum) < Math.abs(komsu.konum - a.konum))) komsu = x; });
    const temel = { hedef: { sistem: p.sistem || GLOBAL, yon: p.yon, ad: a.ad }, bagli: b, komsu: komsu ? komsu.ad : null, secenekler: ["elemanlarla", "tasi", "iptal"] };
    if (p.secenek === "iptal") return Object.assign({ model: kopya(bina), uyarilar: [], silindi: false }, temel);
    if (zGlobalMi(bina, p.sistem, p.yon) && a.kat != null && (b.kolonlar.length || b.kirisler.length || b.dosemeler.length)) {
      return Object.assign({ model: kopya(bina), uyarilar: ["Z aksı " + a.ad + " kat " + a.kat + "'e bağlı ve o katta eleman var; katı Katlar bölümünden silin."], silindi: false }, temel);
    }
    if (b.toplam > 0 && !p.secenek) {
      return Object.assign({ model: kopya(bina), uyarilar: [yonAdi(p.yon) + " aksı " + a.ad + "'ya bağlı " + b.ozet + " var."], silindi: false, onayGerekli: true }, temel);
    }
    const m = kopya(bina), uy = [];
    if (b.toplam > 0 && p.secenek === "elemanlarla") { elemanlariSil(m, b); uy.push(b.ozet + " silindi."); }
    else if (b.toplam > 0 && p.secenek === "tasi") {
      if (!komsu) throw new AksHatasi("Taşınacak komşu aks yok.");
      adlariUygula(m, bina, p.sistem || GLOBAL, p.yon, new Map([[a.ad, komsu.ad]]));
      uy.push(b.ozet + " " + komsu.ad + " aksına taşındı.");
      bozuklariAyikla(m, uy);
    } else if (b.toplam > 0) throw new AksHatasi("Silme seçeneği anlaşılamadı: " + p.secenek);
    const liste = hamListe(m, p.sistem, p.yon);
    liste.splice(liste.findIndex(function (x) { return String(x.ad) === a.ad; }), 1);
    if (zGlobalMi(bina, p.sistem, p.yon) && a.kat != null && Array.isArray(m.katlar)) {
      m.katlar = m.katlar.filter(function (k) { return +k.no !== a.kat; });
      uy.push("Kat " + a.kat + " (eleman yok) kaldırıldı.");
    }
    return sonuc(m, uy, Object.assign(temel, { silindi: true }));
  }

  // ---------------------------------------------------------------- ek aks sistemleri
  function sistemDenetle(s, mevcut) {
    if (!s || s.ad == null || String(s.ad).trim() === "") throw new AksHatasi("Aks sisteminin adı olmalı.");
    if (String(s.ad) === GLOBAL) throw new AksHatasi("\"GLOBAL\" adı ana sisteme ayrılmıştır.");
    if (mevcut.some(function (x) { return String(x.ad) === String(s.ad); })) throw new AksHatasi("\"" + s.ad + "\" adlı sistem zaten var.");
    if (s.tur && s.tur !== "kartezyen" && s.tur !== "silindirik") throw new AksHatasi("Sistem türü kartezyen ya da silindirik olmalı.");
  }
  /** Ek sistem ekler. Eksik listeler varsayılanla doldurulur (kartezyen 3×3 @6 m; silindirik R 5/10, θ 0–90 @30°). */
  function sistemEkle(bina, s) {
    const m = kopya(bina);
    if (!Array.isArray(m.aks_sistemleri)) m.aks_sistemleri = [];
    s = kopya(s || {});
    if (s.ad == null) s.ad = benzersizAd("S" + (m.aks_sistemleri.length + 1), m.aks_sistemleri.map(function (x) { return x.ad; }));
    sistemDenetle(s, m.aks_sistemleri);
    s.ad = String(s.ad);
    s.tur = s.tur === "silindirik" ? "silindirik" : "kartezyen";
    s.orijin = Array.isArray(s.orijin) ? s.orijin.map(function (v) { return +v || 0; }) : [0, 0, 0];
    s.aci = +s.aci || 0;
    if (s.tur === "kartezyen") {
      if (!Array.isArray(s.x)) s.x = adlarUret("x", 3).map(function (ad, i) { return { ad: ad, konum: 6 * i }; });
      if (!Array.isArray(s.y)) s.y = adlarUret("y", 3).map(function (ad, i) { return { ad: ad, konum: 6 * i }; });
    } else {
      if (!Array.isArray(s.r)) s.r = [{ ad: "R1", konum: 5 }, { ad: "R2", konum: 10 }];
      if (!Array.isArray(s.teta)) s.teta = adlarUret("teta", 4).map(function (ad, i) { return { ad: ad, konum: 30 * i }; });
    }
    if (s.z === undefined) s.z = null;
    m.aks_sistemleri.push(s);
    return sonuc(m, []);
  }
  /** Sistem özelliklerini değiştirir (ad değişirse REF'lerdeki "sistem" de güncellenir). degisim: {ad, orijin, aci, gorunur, z} */
  function sistemGuncelle(bina, ad, degisim) {
    const m = kopya(bina);
    const s = (m.aks_sistemleri || []).find(function (x) { return String(x.ad) === String(ad); });
    if (!s) throw new AksHatasi("\"" + ad + "\" adlı aks sistemi yok.");
    const d = degisim || {};
    if (d.ad != null && String(d.ad) !== String(ad)) {
      sistemDenetle({ ad: d.ad, tur: s.tur }, m.aks_sistemleri.filter(function (x) { return x !== s; }));
      s.ad = String(d.ad);
      refleriGez(m, function (r) { return aksRefMi(r) && r.sistem === String(ad) ? Object.assign({}, r, { sistem: s.ad }) : r; });
    }
    if (d.orijin != null) s.orijin = d.orijin.map(function (v) { const n = sayiOku(v); if (n == null) throw new AksHatasi("Orijin koordinatları sayı olmalı."); return n; });
    if (d.aci != null) { const n = sayiOku(d.aci); if (n == null) throw new AksHatasi("Açı sayı olmalı."); s.aci = n; }
    if (d.gorunur != null) s.gorunur = !!d.gorunur;
    if (d.z !== undefined) s.z = d.z;
    return sonuc(m, []);
  }
  /** Sistemi siler; bağlı REF varsa seçenek ister ("elemanlarla" | "iptal"). */
  function sistemSil(bina, ad, secenek) {
    const S = sistemler(bina);
    const Sh = sistemBul(bina, ad, S);
    if (Sh.global) throw new AksHatasi("GLOBAL sistem silinemez.");
    const toplam = { cubuklar: [], paneller: [], mesnetler: [], ek_yukler: [], dugumler: [], kolonlar: [], kirisler: [], dosemeler: [], temeller: [] };
    [Sh.yonler[0], Sh.yonler[1]].forEach(function (yon) {
      Sh.l[yon].forEach(function (a) {
        const b = bagliElemanlar(bina, { sistem: ad, yon: yon, ad: a.ad });
        Object.keys(toplam).forEach(function (k) { b[k].forEach(function (v) { if (toplam[k].indexOf(v) < 0) toplam[k].push(v); }); });
      });
    });
    const n = Object.keys(toplam).reduce(function (s, k) { return s + toplam[k].length; }, 0);
    toplam.toplam = n;
    if (secenek === "iptal" || (n > 0 && !secenek)) return { model: kopya(bina), uyarilar: n ? [ad + " sistemine bağlı " + n + " kayıt var."] : [], bagli: toplam, onayGerekli: n > 0 && !secenek, silindi: false };
    const m = kopya(bina);
    if (n > 0) elemanlariSil(m, toplam);
    m.aks_sistemleri = (m.aks_sistemleri || []).filter(function (x) { return String(x.ad) !== String(ad); });
    return sonuc(m, n ? [n + " bağlı kayıt silindi."] : [], { bagli: toplam, silindi: true });
  }

  // ---------------------------------------------------------------- hızlı aks sihirbazı (saf çıktı)
  function konumlarOku(g, yon) {
    if (g == null) return null;
    if (Array.isArray(g)) return g.map(Number).sort(function (a, b) { return a - b; });
    if (typeof g === "object") {
      if (g.dizi != null && String(g.dizi).trim() !== "") return sozdizimiAyristir(g.dizi, { baslangic: g.baslangic || 0 }).konumlar;
      const n = Math.round(+g.adet), a = sayiOku(g.aralik);
      if (!(n >= 1)) throw new AksHatasi(yonAdi(yon) + ": aks adedi en az 1 olmalı.");
      if (n > 1 && !(a > 0)) throw new AksHatasi(yonAdi(yon) + ": aralık sıfırdan büyük olmalı.");
      const k = [];
      for (let i = 0; i < n; i++) k.push(r6((+g.baslangic || 0) + i * (a || 0)));
      return k;
    }
    return sozdizimiAyristir(g).konumlar;
  }
  /**
   * Hızlı aks: p = {x, y: sözdizimi metni | {adet, aralik} | {dizi} | [konumlar], ilkX: "A", ilkY: "1",
   *                 z: kat yükseklikleri sözdizimi ("1@4.5, 3@3.2") | katlar: {adet, yukseklik}, taban: 0 (temel kotu),
   *                 ekZ: [{ad, konum}] (saçak, mahya, kren...), balon: "bas"}
   * Dönüş: akslar {x, y, z} (z[i].kat: 0 tabanda, 1..n kat döşemeleri).
   */
  function hizliAks(p) {
    p = p || {};
    const xs = konumlarOku(p.x == null ? "1@6" : p.x, "x"), ys = konumlarOku(p.y == null ? "1@6" : p.y, "y");
    const balon = BALON_YERLERI.indexOf(p.balon) >= 0 ? p.balon : "bas";
    const ax = adlarUret("x", xs.length, p.ilkX), ay = adlarUret("y", ys.length, p.ilkY);
    const ak = {
      x: xs.map(function (k, i) { return { ad: ax[i], konum: k, tur: "ana", gorunur: true, balon: balon }; }),
      y: ys.map(function (k, i) { return { ad: ay[i], konum: k, tur: "ana", gorunur: true, balon: balon }; }),
      z: [],
    };
    const taban = sayiOku(p.taban) || 0;
    let zk;
    if (p.katlar && typeof p.katlar === "object" && !Array.isArray(p.katlar)) zk = konumlarOku({ adet: (+p.katlar.adet || 0) + 1, aralik: p.katlar.yukseklik, baslangic: taban }, "z");
    else if (p.z != null && String(p.z).trim() !== "") {
      const r = typeof p.z === "string" ? sozdizimiAyristir(p.z, { baslangic: taban }) : null;
      zk = r ? r.konumlar : konumlarOku(p.z, "z");
    } else zk = [taban, r6(taban + 3)];
    const adlar = [];
    zk.forEach(function (k, i) { const ad = benzersizAd(kotAdi(k), adlar); adlar.push(ad); ak.z.push({ ad: ad, konum: r6(k), kat: i }); });
    (p.ekZ || []).forEach(function (e) {
      if (typeof e === "string") { const m = /^(.+?)\s*[=:]\s*(\S+)$/.exec(e); e = m ? { ad: m[1], konum: m[2] } : null; }
      if (!e) return;
      const k = sayiOku(e.konum);
      if (k == null) throw new AksHatasi("Ek Z aksı \"" + (e.ad || "?") + "\": kot sayı olmalı.");
      if (ak.z.some(function (a) { return Math.abs(a.konum - k) < TOL; })) throw new AksHatasi("Ek Z aksı \"" + (e.ad || "?") + "\" (" + fmt(k) + ") bir kat aksıyla aynı kotta.");
      const ad = benzersizAd(String(e.ad || kotAdi(k)).trim() || kotAdi(k), adlar);
      adlar.push(ad);
      ak.z.push({ ad: ad, konum: r6(k) });
    });
    ak.z.sort(function (a, b) { return a.konum - b.konum; });
    return ak;
  }
  /** Z akslarından katlar listesi (kat ad: Temel, 1. kat, ...). */
  function katlarTuret(akslar, eski) {
    const l = [];
    ((akslar && akslar.z) || []).forEach(function (a) {
      if (a.kat == null) return;
      const e = (eski || []).find(function (k) { return +k.no === +a.kat; });
      l.push({ no: +a.kat, ad: e && e.ad ? e.ad : katAdiVarsayilan(+a.kat), kot: r6(+a.konum) });
    });
    return l.sort(function (a, b) { return a.no - b.no; });
  }

  const SAF = {
    TOL: TOL, GLOBAL: GLOBAL, YAKALAMA_ADIMI: YAKALAMA_ADIMI, BALON_YERLERI: BALON_YERLERI, AksHatasi: AksHatasi,
    sayiOku: sayiOku, fmt: fmt, fmtKisa: fmtKisa, kotAdi: kotAdi, yuvarla: yuvarla,
    sozdizimiAyristir: sozdizimiAyristir, sozdizimiYaz: sozdizimiYaz, konumdanAralik: konumdanAralik, araliktanKonum: araliktanKonum,
    harfAdi: harfAdi, harfIndeks: harfIndeks, adlarUret: adlarUret, benzersizAd: benzersizAd, sonrakiAd: sonrakiAd,
    sistemler: sistemler, sistemBul: function (bina, ad) { return sistemBul(bina, ad); }, sistemNokta: sistemNokta, noktaSistem: noktaSistem, yonler: yonler, yonAdi: yonAdi,
    refKoordinat: refKoordinat, refKoordinatGuvenli: refKoordinatGuvenli, Cozucu: Cozucu, refAnahtar: refAnahtar, aksRefMi: aksRefMi,
    koordinattanRef: koordinattanRef, dogruKesisimi: dogruKesisimi,
    katZAksi: katZAksi, katKotu: katKotu, zAksiKati: zAksiKati, katlariSenkronla: katlariSenkronla, katlarTuret: katlarTuret, yukselt: yukselt,
    gorunumCoz: gorunumCoz, kesisimler: kesisimler, aksParcalari: aksParcalari, gozler: gozler, duzlemDugumleri: duzlemDugumleri,
    enYakinKesisim: enYakinKesisim, enYakinParca: enYakinParca, gozBul: gozBul, gorunumKomsu: gorunumKomsu,
    refleriGez: refleriGez, bagliElemanlar: bagliElemanlar,
    aksTasi: aksTasi, aralikDegistir: aralikDegistir, aksEkle: aksEkle, aksSil: aksSil, aksYenidenAdlandir: aksYenidenAdlandir,
    yenidenHarfle: yenidenHarfle, aksSirala: aksSirala, aksCogalt: aksCogalt, aksOzellik: aksOzellik, aralikDenetle: aralikDenetle,
    sistemEkle: sistemEkle, sistemGuncelle: sistemGuncelle, sistemSil: sistemSil,
    hizliAks: hizliAks,
  };

  // =================================================================================================================
  // ARAYÜZ (DOM). Saf mantığı kullanır; yalnız tarayıcıda çağrılır.
  // =================================================================================================================
  function kacis(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function r1(v) { return Math.round(v * 10) / 10; }
  function pt(p) { return r1(p[0]) + "," + r1(p[1]); }
  function birim2(dx, dy) { const L = Math.hypot(dx, dy); return L > 1e-9 ? [dx / L, dy / L] : null; }
  function yol(pts) { return "M" + pts.map(pt).join(" L"); }
  function veriAks(s, yon, ad) {
    return ' data-aks-sistem="' + kacis(s) + '" data-aks-yon="' + kacis(yon) + '" data-aks-ad="' + kacis(ad) + '"';
  }
  function kotEtiketi(a) {
    const kotlu = /^[±+-]\d+\.\d\d$/.test(a.ad) && Math.abs(sayiOku(a.ad.replace("±", "")) - a.konum) < 0.005;
    const kot = kotAdi(a.konum).replace(".", ",").replace("-", "\u2212");
    return kotlu ? kot : a.ad + "  " + kot;
  }

  /** Z etiketi genişliği (px, yaklaşık; 11 px yazı). */
  function zEtiketGenislik(a) { return Math.max(38, kotEtiketi(a).length * 6.3 + 14); }

  /**
   * Aks katmanı (SVG metni): aks çizgileri (ana: noktalı-kesikli; ikincil: kesikli ince), balonlar (daire içinde ad),
   * aralık ölçü zinciri (+ toplam), kesişim noktaları; cephede Z aksları kot etiketiyle (etiket sağda, kat yükseklikleri
   * ölçü zinciri solda); 3B'de seçili Z'de ızgara, diğer Z seviyeleri soluk çerçeve ve sağ arka köşede kot etiketleri.
   * izdusum(X, Y, Z) → [x, y] (SVG/viewBox koordinatı; Cizim3B ile: q = Cizim3B.izdusum(X,Y,Z,bakis); [T.x(q[0]), T.y(q[1])]).
   * sec: {balonR: 11, olcu: true (3B'de olcu3b), kesisim: true, secili: {sistem, yon, ad}, ekSistemler: true,
   *       onizleme: {sistem, yon, ad, konum} (sürükleme sırasında aksı geçici konumda çiz)}
   * Öğeler: .aks-cizgi (+ .aks-vurus: geniş görünmez vuruş çizgisi), .aks-balon / .aks-zbalon (data-aks-sistem, -yon, -ad),
   *         .aks-olcu, .aks-kesisim (data-aks-ref = REF JSON).
   */
  function sahneKatmani(bina, g, iz, sec) {
    sec = Object.assign({ balonR: 11, olcu: true, kesisim: true, secili: null, ekSistemler: true }, sec || {});
    g = g || { tur: "plan" };
    let b = bina;
    if (sec.onizleme) { try { b = aksTasi(bina, { sistem: sec.onizleme.sistem, yon: sec.onizleme.yon, ad: sec.onizleme.ad, konum: sec.onizleme.konum, yapisik: false }).model; } catch (e) { b = bina; } }
    let o;
    try { o = gorunumCoz(b, g); } catch (e) { return '<g class="aks-katman"></g>'; }
    const R = sec.balonR;
    const olcuAcik = o.tur === "3b" ? !!sec.olcu3b : sec.olcu !== false;
    const uzatV = olcuAcik ? R * 4.4 : R * 1.6;
    const secili = sec.secili || g.secili || null;
    const katman = { cizgi: [], olcu: [], kes: [], balon: [] };
    const zEtiketler = [];
    /** Z etiketleri (cephe): çizgi ucunda; birbirine yakın kotlarda (Saçak/Mahya) dikey yönde aralanır, kayanlara kılavuz çizgisi. */
    const zEtiketYerlestir = function () {
      const l = zEtiketler.map(function (e) {
        const w = zEtiketGenislik(e.a);
        return Object.assign(e, { w: w, C: [e.P[0] + e.d[0] * (w / 2 + 3), e.P[1] + e.d[1] * (w / 2 + 3)] });
      }).sort(function (p, q) { return p.C[1] - q.C[1]; });
      // 1B etiket yerleşimi: çakışan etiketler grup olur, grup doğal konumlarının ortasına ortalanır (yukarı ve aşağı eşit açılır)
      const ARA = 19;
      let gruplar = l.map(function (e) { return { e: [e], ort: e.C[1] }; });
      let degisti = true;
      while (degisti) {
        degisti = false;
        for (let i = 0; i + 1 < gruplar.length; i++) {
          const a = gruplar[i], b2 = gruplar[i + 1];
          const aAlt = a.ort + (a.e.length - 1) * ARA / 2, bUst = b2.ort - (b2.e.length - 1) * ARA / 2;
          if (bUst - aAlt < ARA - 1e-6) {
            const e = a.e.concat(b2.e);
            gruplar.splice(i, 2, { e: e, ort: e.reduce(function (t, x) { return t + x.C[1]; }, 0) / e.length });
            degisti = true; break;
          }
        }
      }
      gruplar.forEach(function (g_) {
        g_.e.forEach(function (e, i) {
          const y = g_.ort + (i - (g_.e.length - 1) / 2) * ARA;
          if (Math.abs(y - e.C[1]) > 0.5) {
            e.C = [e.C[0] + 8, y];
            katman.cizgi.push('<path class="aks-olcu-c" d="M' + pt(e.P) + " L" + pt([e.C[0] - e.w / 2, e.C[1]]) + '"/>');
          }
          katman.balon.push(zBalon(e.s, e.a, e.C, e.sec, e.v));
        });
      });
    };
    const seciliMi = function (s, yon, ad) { return !!secili && (secili.sistem || GLOBAL) === s.ad && secili.yon === yon && String(secili.ad) === String(ad); };
    const sinifS = function (s) { return s.global ? "aks-s0" : "aks-s" + (((s.sira - 1) % 3) + 1); };
    const ekr = function (P) { return iz(P[0], P[1], P[2]); };
    const zBalon = function (s, a, C, sec_, v) {
      const t = kotEtiketi(a), w = zEtiketGenislik(a), h = 17;
      return '<g class="aks-balon aks-zbalon ' + sinifS(s) + (sec_ ? " aks-secili" : "") + '"' + v + '><title>' + kacis(yonAdi("z") + " aksı " + a.ad + (a.kat != null ? " — kat " + a.kat : "")) + "</title>" +
        '<rect x="' + r1(C[0] - w / 2) + '" y="' + r1(C[1] - h / 2) + '" width="' + r1(w) + '" height="' + h + '" rx="4"/>' +
        '<text x="' + r1(C[0]) + '" y="' + r1(C[1]) + '" text-anchor="middle" dominant-baseline="central">' + kacis(t) + "</text></g>";
    };
    /**
     * Bir aks çizgisi: f(t) bina noktası, t: lo → hi (lo > hi olabilir; çizginin "baş"ı lo ucudur); dairesel → 5°'lik örnekleme.
     * k: {zEtiket, uzat (baş uzatması), sonUzat, halka: [θ] (tam çemberde balon halkanın üstünde)}
     */
    const cizgi = function (s, yon, a, f, lo, hi, dairesel, k) {
      k = k || {};
      const n = dairesel ? Math.max(2, Math.ceil(Math.abs(hi - lo) / 5) + 1) : 2;
      const pts = [];
      for (let i = 0; i < n; i++) pts.push(ekr(f(lo + (hi - lo) * i / (n - 1))));
      const d0 = birim2(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]), d1 = birim2(pts[n - 1][0] - pts[n - 2][0], pts[n - 1][1] - pts[n - 2][1]);
      if (!d0 || !d1) return null;              // ekranda nokta (bakış doğrultusunda): çizilmez
      const sec_ = seciliMi(s, yon, a.ad);
      const balon = k.zEtiket ? "son" : (k.halka ? "yok" : a.balon);
      const uz = k.uzat != null ? k.uzat : uzatV;
      const basU = k.halka ? 0 : k.zEtiket ? (olcuAcik ? R * 3.2 : R * 1.2) : (balon === "bas" || balon === "iki" ? uz : R * 1.2);
      const sonU = k.sonUzat != null ? k.sonUzat : (k.zEtiket ? R * 0.8 : (balon === "son" || balon === "iki" ? uz : R * 1.2));
      const A = [pts[0][0] + d0[0] * basU, pts[0][1] + d0[1] * basU], B = [pts[n - 1][0] + d1[0] * sonU, pts[n - 1][1] + d1[1] * sonU];
      const tum = [A].concat(pts, [B]);
      const sinif = "aks-cizgi" + (a.tur === "ikincil" ? " aks-ikincil" : "") + (sec_ ? " aks-secili" : "") + (k.zEtiket ? " aks-zcizgi" : "");
      const v = veriAks(s.ad, yon, a.ad);
      katman.cizgi.push('<g class="' + sinifS(s) + '"><path class="' + sinif + '" d="' + yol(tum) + '"/><path class="aks-vurus" d="' + yol(tum) + '"' + v + "/></g>");
      const daire = function (C) {
        const uzun = String(a.ad).length > 2;
        katman.balon.push('<g class="aks-balon ' + sinifS(s) + (sec_ ? " aks-secili" : "") + '"' + v + ' role="button" aria-label="' + kacis(yonAdi(yon) + " aksı " + a.ad + ", " + fmt(a.konum) + (yon === "teta" ? "°" : " m")) + '">' +
          '<circle cx="' + r1(C[0]) + '" cy="' + r1(C[1]) + '" r="' + r1(uzun ? R * 1.25 : R) + '"/><text x="' + r1(C[0]) + '" y="' + r1(C[1]) + '" text-anchor="middle" dominant-baseline="central"' + (uzun ? ' class="aks-balon-uzun"' : "") + ">" + kacis(a.ad) + "</text></g>");
      };
      const balonCiz = function (P, d) {
        if (k.zEtiket) { zEtiketler.push({ s: s, a: a, P: P, d: d, sec: sec_, v: v }); return; }
        const r = String(a.ad).length > 2 ? R * 1.25 : R;
        daire([P[0] + d[0] * r, P[1] + d[1] * r]);
      };
      if (!k.gizle) {
        if (k.halka) daire(ekr(f(k.halka)));
        if (balon === "bas" || balon === "iki") balonCiz(A, d0);
        if (balon === "son" || balon === "iki") balonCiz(B, d1);
      }
      return { bas: pts[0], son: pts[n - 1], d0: d0, d1: d1, a: a };
    };
    // Ölçü zinciri: aynı aileden paralel çizgilerin uç noktaları (ekran), dışa doğru d yönünde. taraf: "bas" | "son" | otomatik
    const olcuZinciri = function (cl, taraf) {
      cl = cl.filter(Boolean);
      if (!olcuAcik || cl.length < 2) return;
      const sonda = taraf ? taraf === "son" : cl.every(function (c) { return c.a.balon === "son"; });
      const P = cl.map(function (c) { return sonda ? c.son : c.bas; }), d = sonda ? cl[0].d1 : cl[0].d0;
      const zincir = function (ofs, ilkSon, metinler) {
        const C = P.map(function (p) { return [p[0] + d[0] * ofs, p[1] + d[1] * ofs]; });
        const sec2 = ilkSon ? [C[0], C[C.length - 1]] : C;
        let s = '<path class="aks-olcu-c" d="' + yol(sec2) + '"/>';
        sec2.forEach(function (c) { s += '<path class="aks-olcu-t" d="M' + pt([c[0] - (d[0] + d[1]) * 3.2, c[1] - (d[1] - d[0]) * 3.2]) + " L" + pt([c[0] + (d[0] + d[1]) * 3.2, c[1] + (d[1] - d[0]) * 3.2]) + '"/>'; });
        metinler.forEach(function (m) {
          const a = sec2[m.i], b2 = sec2[m.i + 1];
          const L = Math.hypot(b2[0] - a[0], b2[1] - a[1]);
          if (L < m.t.length * 6 + 4) return;
          let ang = Math.atan2(b2[1] - a[1], b2[0] - a[0]) / D2R;
          if (ang > 90.01) ang -= 180; else if (ang < -89.99) ang += 180;
          const M = [(a[0] + b2[0]) / 2 + d[0] * 7.5, (a[1] + b2[1]) / 2 + d[1] * 7.5];
          s += '<text class="aks-olcu-y" x="' + r1(M[0]) + '" y="' + r1(M[1]) + '" text-anchor="middle" dominant-baseline="central"' +
            (Math.abs(ang) > 0.5 ? ' transform="rotate(' + r1(ang) + " " + r1(M[0]) + " " + r1(M[1]) + ')"' : "") + ">" + kacis(m.t) + "</text>";
        });
        return s;
      };
      let s = zincir(R * 1.1, false, cl.slice(1).map(function (c, i) { return { i: i, t: fmt(c.a.konum - cl[i].a.konum) }; }));
      if (cl.length > 2) s += zincir(R * 2.6, true, [{ i: 0, t: fmt(cl[cl.length - 1].a.konum - cl[0].a.konum) }]);
      katman.olcu.push('<g class="aks-olcu">' + s + "</g>");
    };
    const gorunurL = function (s, yon) { return s.l[yon].filter(function (a) { return a.gorunur !== false; }); };
    const sinirlar = function (l) { return l.length ? [l[0].konum, l[l.length - 1].konum] : [0, 0]; };
    const kesisimCiz = function (s, Pl) {
      if (!sec.kesisim) return;
      Pl.forEach(function (q) {
        const p = ekr(q.P);
        katman.kes.push('<circle class="aks-kesisim ' + sinifS(s) + '" cx="' + r1(p[0]) + '" cy="' + r1(p[1]) + '" r="2.4" data-aks-ref="' + kacis(JSON.stringify(q.ref)) + '"/>');
      });
    };
    /** Sık akslarda balon seyreltme: ekranda bir öncekine 2R'den yakın balon çizilmez (seçili aks her zaman çizilir). */
    const seyrek = function (s, yon, l, nokta) {
      const g_ = new Set();
      let son = null;
      l.forEach(function (a, i) {
        const p = nokta(a);
        const uzak = !son || Math.hypot(p[0] - son[0], p[1] - son[1]) >= 2 * R + 3;
        const sonuncu = i === l.length - 1 && son && Math.hypot(p[0] - son[0], p[1] - son[1]) >= R;
        if (uzak || seciliMi(s, yon, a.ad) || sonuncu) { g_.add(a.ad); son = p; }
      });
      return function (a) { return !g_.has(a.ad); };
    };
    const planCiz = function (s, z, olculu) {
      const yu = s.yonler[0], yv = s.yonler[1], lu = gorunurL(s, yu), lv = gorunurL(s, yv);
      if (!lu.length && !lv.length) return;
      if (s.tur === "silindirik") {
        // halkalar (R) ve ışınlar (θ); tam çemberde R balonu halkanın üstünde ilk iki ışının ortasında
        const bv = sinirlar(lv), rmax = lu.length ? lu[lu.length - 1].konum : 0;
        let tam = false, ara = 30;
        if (lv.length > 2) { const ar = konumdanAralik(lv.map(function (a) { return a.konum; })); ara = ar[0]; tam = 360 - (bv[1] - bv[0]) <= Math.max.apply(null, ar) + 1e-9; }
        const gr = seyrek(s, yu, lu, function (a) { return ekr(sistemNokta(s, a.konum, tam ? bv[0] + ara / 2 : bv[0], z.konum)); });
        const gt = seyrek(s, yv, lv, function (b2) { return ekr(sistemNokta(s, rmax, b2.konum, z.konum)); });
        lu.forEach(function (a) {
          if (a.konum < TOL) return;
          cizgi(s, yu, a, function (t) { return sistemNokta(s, a.konum, t, z.konum); }, bv[0], tam ? bv[0] + 360 : bv[1], true,
            tam ? { halka: bv[0] + ara / 2, sonUzat: 0, uzat: 0, gizle: gr(a) } : { uzat: R * 1.6, gizle: gr(a) });
        });
        lv.forEach(function (b2) { cizgi(s, yv, b2, function (t) { return sistemNokta(s, t, b2.konum, z.konum); }, rmax, 0, false, { uzat: R * 1.6, sonUzat: 0, gizle: gt(b2) }); });
      } else {
        const bu = sinirlar(lu), bv = sinirlar(lv);
        const gu = seyrek(s, yu, lu, function (a) { return ekr(sistemNokta(s, a.konum, bv[0], z.konum)); });
        const gv = seyrek(s, yv, lv, function (b2) { return ekr(sistemNokta(s, bu[0], b2.konum, z.konum)); });
        const cu = lu.map(function (a) { return cizgi(s, yu, a, function (t) { return sistemNokta(s, a.konum, t, z.konum); }, bv[0], bv[1], false, { gizle: gu(a) }); });
        const cv = lv.map(function (b2) { return cizgi(s, yv, b2, function (t) { return sistemNokta(s, t, b2.konum, z.konum); }, bu[0], bu[1], false, { gizle: gv(b2) }); });
        if (olculu) { olcuZinciri(cu); olcuZinciri(cv); }
      }
      const ks = [];
      lu.forEach(function (a) { lv.forEach(function (b2) { ks.push({ ref: aksRef(s, a.ad, b2.ad, z.ad), P: sistemNokta(s, a.konum, b2.konum, z.konum) }); }); });
      kesisimCiz(s, ks);
    };
    if (o.tur === "plan") {
      const sl = sec.ekSistemler ? planSistemleri(o, g) : [o.ana];
      sl.forEach(function (s) {
        const z = s === o.ana ? o.z : aksBul(s, "z", o.z.ad, false);
        if (z) planCiz(s, z, s === o.ana || s.global);
      });
    } else if (o.tur === "cephe") {
      const s = o.ana, ilk = o.sabitYon === s.yonler[0], gy = o.gezYon;
      const lc = gorunurL(s, gy), lz = s.l.z;
      const sil = s.tur === "silindirik" && gy === "teta";
      const bc = sinirlar(lc), bz = sinirlar(lz);
      const nokta = function (c, zk) { return ilk ? sistemNokta(s, o.sabit.konum, c, zk) : sistemNokta(s, c, o.sabit.konum, zk); };
      const gc = seyrek(s, gy, lc, function (c) { return ekr(nokta(c.konum, bz[0])); });
      const cc = lc.map(function (c) { return cizgi(s, gy, c, function (t) { return nokta(c.konum, t); }, bz[0], bz[1], false, { gizle: gc(c) }); });
      const czl = lz.map(function (z) { return cizgi(s, "z", z, function (t) { return nokta(t, z.konum); }, bc[0], bc[1], sil, { zEtiket: true }); });
      if (!sil) olcuZinciri(cc);
      olcuZinciri(czl, "bas");
      zEtiketYerlestir();
      const ks = [];
      lc.forEach(function (c) { lz.forEach(function (z) { ks.push({ ref: ilk ? aksRef(s, o.sabit.ad, c.ad, z.ad) : aksRef(s, c.ad, o.sabit.ad, z.ad), P: nokta(c.konum, z.konum) }); }); });
      kesisimCiz(s, ks);
    } else {
      // 3B: seçili (ya da en alt) Z'de ızgara + balonlar; diğer Z seviyeleri soluk çerçeve; kot etiketleri sağ arka köşede
      const G = o.ana, z0 = o.z;
      o.S.forEach(function (s) {
        if (!s.global && (s.gorunur === false || !sec.ekSistemler)) return;
        const z = s.zOrtak && z0 ? aksBul(s, "z", z0.ad, false) : s.l.z[0];
        if (z) planCiz(s, z, s === G);
      });
      const lx = gorunurL(G, G.yonler[0]), ly = gorunurL(G, G.yonler[1]);
      if (lx.length && ly.length && G.tur === "kartezyen") {
        const x0 = lx[0].konum, x1 = lx[lx.length - 1].konum, y0 = ly[0].konum, y1 = ly[ly.length - 1].konum;
        const et = [];
        G.l.z.forEach(function (z) {
          const kos = [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]].map(function (q) { return ekr(sistemNokta(G, q[0], q[1], z.konum)); });
          if (!z0 || z.ad !== z0.ad) katman.cizgi.push('<path class="aks-seviye" d="' + yol(kos) + '"/>');
          // köşe: ekranda en sağdaki üst köşe
          let K = kos[0];
          kos.slice(0, 4).forEach(function (q) { if (q[0] > K[0] + 1e-6 || (Math.abs(q[0] - K[0]) < 1e-6 && q[1] < K[1])) K = q; });
          et.push({ z: z, K: K });
        });
        et.sort(function (p, q) { return q.K[1] - p.K[1]; });     // aşağıdan yukarı; çakışanlar yukarı itilir
        let son = Infinity;
        et.forEach(function (e) {
          const w = zEtiketGenislik(e.z);
          let y = e.K[1];
          if (y > son - 19) y = son - 19;
          son = y;
          const C = [e.K[0] + 16 + w / 2, y];
          katman.cizgi.push('<path class="aks-olcu-c" d="M' + pt(e.K) + " L" + pt([e.K[0] + 14, y]) + '"/>');
          katman.balon.push(zBalon(G, e.z, C, seciliMi(G, "z", e.z.ad) || (z0 && e.z.ad === z0.ad), veriAks(G.ad, "z", e.z.ad)));
        });
      }
    }
    return '<g class="aks-katman">' + katman.cizgi.join("") + katman.olcu.join("") + katman.kes.join("") + katman.balon.join("") + "</g>";
  }

  /**
   * Görünüm için önerilen kenar payları (px): balonlar, ölçü zinciri ve Z etiketleri kesilmesin. bina.js sığdırmada kullanır.
   * Dönüş: {sol, sag, ust, alt}
   */
  function kenarPaylari(bina, g, sec) {
    sec = Object.assign({ balonR: 11, olcu: true }, sec || {});
    const R = sec.balonR, olcu = sec.olcu !== false;
    const balonPay = (olcu ? R * 4.4 : R * 1.6) + 2 * R + 8, bos = R * 1.2 + 10;
    let o;
    try { o = gorunumCoz(bina, g); } catch (e) { return { sol: bos, sag: bos, ust: bos, alt: bos }; }
    const s = o.ana;
    const var_ = function (yon, yer) { return (s.l[yon] || []).some(function (a) { return a.gorunur !== false && (a.balon === yer || a.balon === "iki"); }); };
    if (o.tur === "cephe") {
      const zMax = s.l.z.reduce(function (m, a) { return Math.max(m, zEtiketGenislik(a)); }, 0);
      const gy = o.gezYon;
      return { sol: olcu ? R * 3.2 + 16 : bos, sag: R * 0.8 + zMax + 22, ust: var_(gy, "son") ? balonPay : bos + 12, alt: var_(gy, "bas") ? balonPay : bos };
    }
    if (s.tur === "silindirik") return { sol: R * 3.6 + 6, sag: R * 3.6 + 6, ust: R * 3.6 + 6, alt: R * 3.6 + 6 };
    const yu = s.yonler[0], yv = s.yonler[1];
    return { sol: var_(yv, "bas") ? balonPay : bos, sag: var_(yv, "son") ? balonPay : bos, alt: var_(yu, "bas") ? balonPay : bos, ust: var_(yu, "son") ? balonPay : bos };
  }

  /** Dik izdüşümlü plan/cephe görünümünü W×H kutuya sığdıran izdüşüm (önizleme ve sınama için). sec: {pad: sayı | {sol, sag, ust, alt}, enCok: 60 px/m} */
  function uygunIzdusum(bina, g, W, H, sec) {
    sec = sec || {};
    const o = gorunumCoz(bina, g);
    const pp = sec.pad == null ? kenarPaylari(bina, g, sec) : (typeof sec.pad === "number" ? { sol: sec.pad, sag: sec.pad, ust: sec.pad, alt: sec.pad } : sec.pad);
    const harita = function (P) {
      if (o.tur === "cephe") {
        const L = noktaSistem(o.ana, P[0], P[1], P[2]);
        if (o.ana.tur === "kartezyen") return [o.sabitYon === o.ana.yonler[0] ? L[1] : L[0], P[2]];
        return [o.sabitYon === "teta" ? L[0] : L[1] * D2R * o.sabit.konum, P[2]];
      }
      return [P[0], P[1]];
    };
    const pts = [];
    if (o.tur === "cephe") kesisimler(bina, g).forEach(function (k) { pts.push(harita(k.P)); });
    else {
      planSistemleri(o, g).forEach(function (s) {
        const z = s === o.ana ? o.z : aksBul(s, "z", o.z.ad, false);
        if (!z) return;
        if (s.tur === "silindirik") {
          const rm = s.l.r.length ? s.l.r[s.l.r.length - 1].konum : 0;
          for (let t = 0; t < 360; t += 15) pts.push(harita(sistemNokta(s, rm, t, z.konum)));
        } else s.l[s.yonler[0]].forEach(function (a) { s.l[s.yonler[1]].forEach(function (b) { pts.push(harita(sistemNokta(s, a.konum, b.konum, z.konum))); }); });
      });
    }
    if (!pts.length) pts.push([0, 0]);
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    pts.forEach(function (p) { x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]); });
    const dx = Math.max(x1 - x0, 1e-6), dy = Math.max(y1 - y0, 1e-6);
    const aw = Math.max(40, W - pp.sol - pp.sag), ah = Math.max(40, H - pp.ust - pp.alt);
    const s = Math.min(aw / dx, ah / dy, sec.enCok || 60);
    const ox = pp.sol + (aw - dx * s) / 2, oy = pp.ust + (ah - dy * s) / 2;
    const f = function (X, Y, Z) { const q = harita([X, Y, Z]); return [ox + (q[0] - x0) * s, oy + (y1 - q[1]) * s]; };
    f.olcek = s; f.kutu = [dx, dy]; f.pay = pp;
    return f;
  }

  // ---------------------------------------------------------------- balon sürükleme yardımcıları
  /** Ekranda sürüklenen balonun yeni konumu (m; θ'da derece), adim'a yuvarlanır. */
  function surukleKonum(bina, hedef, iz, P0, P, sec) {
    sec = sec || {};
    const S = sistemBul(bina, hedef.sistem);
    const a = aksBul(S, hedef.yon, hedef.ad);
    const yu = S.yonler[0], yv = S.yonler[1];
    const ilkK = function (y) { const l = S.l[y]; return l.length ? (S.tur === "silindirik" && y === "r" ? l[l.length - 1].konum : l[0].konum) : 0; };
    const nokta = function (k) {
      const u = hedef.yon === yu ? k : ilkK(yu), v = hedef.yon === yv ? k : ilkK(yv), z = hedef.yon === "z" ? k : (sec.zKonum != null ? sec.zKonum : ilkK("z"));
      return sistemNokta(S, u, v, z);
    };
    const adim = sec.adim || (hedef.yon === "teta" ? 0.5 : YAKALAMA_ADIMI);
    const h = 1;
    const w0 = iz.apply(null, nokta(a.konum)), w1 = iz.apply(null, nokta(a.konum + h));
    const d = [w1[0] - w0[0], w1[1] - w0[1]], L2 = d[0] * d[0] + d[1] * d[1];
    if (L2 < 1e-12) return a.konum;
    const del = ((P[0] - P0[0]) * d[0] + (P[1] - P0[1]) * d[1]) / L2 * h;
    const k0 = sec.konum0 != null ? sec.konum0 : a.konum;
    return yuvarla(k0 + del, adim);
  }
  /** Olay hedefinden aks balonu/çizgisi kimliği: {sistem, yon, ad} ya da null. */
  function aksHedefi(el) {
    const e = el && el.closest ? el.closest("[data-aks-yon]") : null;
    if (!e) return null;
    return { sistem: e.getAttribute("data-aks-sistem") || GLOBAL, yon: e.getAttribute("data-aks-yon"), ad: e.getAttribute("data-aks-ad"), balon: !!(e.classList && e.classList.contains("aks-balon")) };
  }
  /** Olay hedefinden kesişim REF'i ya da null. */
  function kesisimHedefi(el) {
    const e = el && el.closest ? el.closest("[data-aks-ref]") : null;
    if (!e) return null;
    try { return JSON.parse(e.getAttribute("data-aks-ref")); } catch (x) { return null; }
  }
  /**
   * Balon sürükleme: svg içindeki .aks-balon öğelerine işaretçiyle tutup aksı taşır (yakalama 0,05 m),
   * sürüklerken sayısal giriş kutusu gösterir; tıklama (ya da çift tık) kutuyu yazmaya açar.
   * sec: {bina: bina | () => bina, gorunum: g | () => g, izdusum: (X,Y,Z) => [x,y] (ya da izdusumAl: () => izdusum; kamera değişirse),
   *       nokta: (e) => [x, y] (izdüşümle aynı koordinat; Cizim3B: kamera.svgNokta(svg, e.clientX, e.clientY)),
   *       onizle: (hedef + {konum}) | null, degisti: (yeniBina, rapor), kaydir: false, adim: 0.05}
   * Dönüş: {kaldir()}
   */
  function balonSurukle(svg, sec) {
    const al = function (v) { return typeof v === "function" ? v() : v; };
    let s = null, kutu = null;
    const kap = svg.parentElement || svg;
    function kutuKapat() { if (kutu) { kutu.remove(); kutu = null; } }
    function kutuAc(hedef, x, y, deger, yazilabilir) {
      if (!kutu) {
        kutu = document.createElement("div");
        kutu.className = "aks-sayisal";
        kutu.innerHTML = '<label><span></span><input class="girdi" inputmode="decimal" autocomplete="off"></label>';
        kap.appendChild(kutu);
      }
      const r = kap.getBoundingClientRect();
      kutu.style.left = Math.max(4, Math.min(r.width - 150, x - r.left + 14)) + "px";
      kutu.style.top = Math.max(4, Math.min(r.height - 44, y - r.top - 40)) + "px";
      kutu.querySelector("span").textContent = yonAdi(hedef.yon) + " " + hedef.ad + (hedef.yon === "teta" ? " (°)" : " (m)");
      const inp = kutu.querySelector("input");
      inp.value = fmtKisa(deger).replace("\u2212", "-");
      inp.readOnly = !yazilabilir;
      if (yazilabilir) {
        inp.onkeydown = function (e) {
          if (e.key === "Enter") { e.preventDefault(); uygula(hedef, sayiOku(inp.value)); kutuKapat(); }
          else if (e.key === "Escape") { e.preventDefault(); kutuKapat(); if (sec.onizle) sec.onizle(null); }
        };
        inp.onblur = function () { setTimeout(kutuKapat, 0); };
        setTimeout(function () { inp.focus(); inp.select(); }, 0);
      }
    }
    function uygula(hedef, konum) {
      if (konum == null) return;
      try {
        const r = aksTasi(al(sec.bina), { sistem: hedef.sistem, yon: hedef.yon, ad: hedef.ad, konum: konum, kaydir: !!al(sec.kaydir) });
        if (sec.onizle) sec.onizle(null);
        if (sec.degisti) sec.degisti(r.model, r);
      } catch (e) { if (sec.hata) sec.hata(e); }
    }
    function down(e) {
      const h = aksHedefi(e.target);
      if (!h || !h.balon) return;
      if (e.button != null && e.button !== 0 && e.pointerType === "mouse") return;
      e.stopPropagation(); e.preventDefault();
      const b = al(sec.bina), S = sistemBul(b, h.sistem);
      const a = aksBul(S, h.yon, h.ad);
      s = { h: h, P0: sec.nokta(e), konum0: a.konum, konum: a.konum, id: e.pointerId, oynadi: false, x: e.clientX, y: e.clientY };
      try { svg.setPointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
    }
    function move(e) {
      if (!s || e.pointerId !== s.id) return;
      e.stopPropagation(); e.preventDefault();
      if (!s.oynadi && Math.hypot(e.clientX - s.x, e.clientY - s.y) < 4) return;
      s.oynadi = true;
      const g = al(sec.gorunum), o = gorunumCoz(al(sec.bina), g);
      const k = surukleKonum(al(sec.bina), s.h, (sec.izdusumAl ? sec.izdusumAl() : sec.izdusum), s.P0, sec.nokta(e), { adim: sec.adim, konum0: s.konum0, zKonum: o.z ? o.z.konum : null });
      if (k !== s.konum) { s.konum = k; if (sec.onizle) sec.onizle({ sistem: s.h.sistem, yon: s.h.yon, ad: s.h.ad, konum: k }); }
      kutuAc(s.h, e.clientX, e.clientY, k, false);
    }
    function up(e) {
      if (!s || e.pointerId !== s.id) return;
      e.stopPropagation();
      try { svg.releasePointerCapture(e.pointerId); } catch (x) { /* yoksay */ }
      const t = s; s = null;
      if (t.oynadi) { kutuKapat(); if (Math.abs(t.konum - t.konum0) > 1e-9) uygula(t.h, t.konum); else if (sec.onizle) sec.onizle(null); }
      else kutuAc(t.h, e.clientX, e.clientY, t.konum0, true);
    }
    function cancel() { if (s) { s = null; kutuKapat(); if (sec.onizle) sec.onizle(null); } }
    svg.addEventListener("pointerdown", down, true);
    svg.addEventListener("pointermove", move, true);
    svg.addEventListener("pointerup", up, true);
    svg.addEventListener("pointercancel", cancel, true);
    return {
      kaldir: function () {
        svg.removeEventListener("pointerdown", down, true); svg.removeEventListener("pointermove", move, true);
        svg.removeEventListener("pointerup", up, true); svg.removeEventListener("pointercancel", cancel, true);
        kutuKapat();
      },
      ac: function (hedef, x, y) { const a = aksBul(sistemBul(al(sec.bina), hedef.sistem), hedef.yon, hedef.ad); kutuAc(hedef, x, y, a.konum, true); },
    };
  }

  // ---------------------------------------------------------------- ortak DOM yardımcıları
  function el(etiket, ozellik, icerik) {
    const e = document.createElement(etiket);
    Object.keys(ozellik || {}).forEach(function (k) {
      if (k === "class") e.className = ozellik[k];
      else if (k === "text") e.textContent = ozellik[k];
      else if (k === "html") e.innerHTML = ozellik[k];
      else e.setAttribute(k, ozellik[k]);
    });
    (icerik || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  let kimlikSay = 0;
  function kimlik(on) { return on + "-" + (++kimlikSay); }
  function sekmeKlavye(liste, e, sec) {
    // sekme listesi: ←/→, Home/End (WAI-ARIA)
    const d = Array.from(liste.querySelectorAll('[role="tab"]'));
    const i = d.indexOf(document.activeElement);
    if (i < 0) return;
    let j = null;
    if (e.key === "ArrowRight") j = (i + 1) % d.length;
    else if (e.key === "ArrowLeft") j = (i - 1 + d.length) % d.length;
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = d.length - 1;
    if (j == null) return;
    e.preventDefault();
    sec(d[j].getAttribute("data-sekme"));
    const yeni = liste.querySelector('[data-sekme="' + d[j].getAttribute("data-sekme") + '"]');
    if (yeni) yeni.focus();
  }
  function onizlemeSvg(bina, g, W, H, sinif, etiket, sec) {
    let ic = "";
    try {
      // yükseklik içeriğe uyar (H üst sınır): genişliğe göre ölçek, sonra içerik yüksekliği + paylar
      const f0 = uygunIzdusum(bina, g, W, 100000, { balonR: 9.5 });
      H = Math.round(Math.max(150, Math.min(H, f0.kutu[1] * f0.olcek + f0.pay.ust + f0.pay.alt + 4)));
      ic = sahneKatmani(bina, g, uygunIzdusum(bina, g, W, H, { balonR: 9.5 }), Object.assign({ balonR: 9.5, kesisim: true }, sec || {}));
    } catch (e) { ic = ""; }
    return '<svg class="aks-mini ' + sinif + '" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + kacis(etiket) + '">' + ic + "</svg>";
  }

  // ---------------------------------------------------------------- hızlı aks sihirbazı
  const EK_Z_HAZIR = [["Saçak", 1.0], ["Mahya", 2.5], ["Kren", -1.5]];
  /**
   * Hızlı aks sihirbazı (yeni model). sec: {bina? (varsa değerler ondan), tamam(akslar, katlar), iptal?()}
   * Dönüş: {kaldir(), deger() → {akslar, katlar} | hata fırlatır}
   */
  function sihirbaz(kapsayici, sec) {
    sec = sec || {};
    const d = {
      sekme: "x",
      x: { kip: "esit", adet: "4", aralik: "6", dizi: "3@6, 7.5", ilk: "A" },
      y: { kip: "esit", adet: "3", aralik: "5", dizi: "2@5", ilk: "1" },
      z: { kip: "esit", adet: "3", yukseklik: "3.2", dizi: "1@4.5, 2@3.2", taban: "0", ek: [] },
    };
    if (sec.bina && sec.bina.akslar) {
      const G = sistemler(sec.bina)[0];
      ["x", "y"].forEach(function (y) {
        const l = G.l[y];
        if (!l.length) return;
        d[y].kip = "dizi"; d[y].dizi = sozdizimiYaz(l.map(function (a) { return a.konum; })); d[y].ilk = l[0].ad;
      });
      const kz = G.l.z.filter(function (a) { return a.kat != null; });
      if (kz.length) { d.z.kip = "dizi"; d.z.taban = fmtMakine(kz[0].konum); d.z.dizi = sozdizimiYaz(kz.map(function (a) { return a.konum; }), { baslangic: kz[0].konum }); }
      d.z.ek = G.l.z.filter(function (a) { return a.kat == null; }).map(function (a) { return { ad: a.ad, konum: fmtMakine(a.konum) }; });
    }
    const kok = el("div", { class: "aks-sihirbaz" });
    const no = kimlik("aks-sh");
    kapsayici.innerHTML = "";
    kapsayici.appendChild(kok);

    function parametre() {
      const p = { ilkX: d.x.ilk, ilkY: d.y.ilk, taban: d.z.taban };
      ["x", "y"].forEach(function (y) { p[y] = d[y].kip === "dizi" ? { dizi: d[y].dizi } : { adet: d[y].adet, aralik: d[y].aralik }; });
      if (d.z.kip === "dizi") p.z = d.z.dizi; else p.katlar = { adet: d.z.adet, yukseklik: d.z.yukseklik };
      p.ekZ = d.z.ek.filter(function (e) { return String(e.ad).trim() !== "" || String(e.konum).trim() !== ""; });
      return p;
    }
    function deger() {
      const ak = hizliAks(parametre());
      return { akslar: ak, katlar: katlarTuret(ak, sec.bina && sec.bina.katlar) };
    }
    function yonOzet(y) {
      try {
        const ak = hizliAks(Object.assign(parametre(), y === "z" ? {} : {}));
        const l = ak[y];
        if (y === "z") {
          const k = l.filter(function (a) { return a.kat != null; });
          return { tamam: true, metin: k.length - 1 + " kat, " + l.length + " Z aksı; en üst kot " + fmt(l[l.length - 1].konum) + " m" };
        }
        return { tamam: true, metin: l.length + " aks (" + l[0].ad + "–" + l[l.length - 1].ad + "), toplam " + fmt(l[l.length - 1].konum - l[0].konum) + " m" };
      } catch (e) { return { tamam: false, metin: e.message }; }
    }
    function alan(etiket, ad, deger_, ek) {
      return '<label class="aks-alan"><span>' + etiket + '</span><input class="girdi" data-alan="' + ad + '" value="' + kacis(deger_) + '"' + (ek || ' inputmode="decimal"') + ' autocomplete="off"></label>';
    }
    function panelHtml() {
      const y = d.sekme, v = d[y];
      let h = '<div class="se-seg aks-kip" role="group" aria-label="Giriş biçimi">' +
        '<button type="button" class="se-seg-d" data-kip="esit" aria-pressed="' + (v.kip === "esit") + '">' + (y === "z" ? "Kat adedi" : "Eşit aralık") + "</button>" +
        '<button type="button" class="se-seg-d" data-kip="dizi" aria-pressed="' + (v.kip === "dizi") + '">Aralık dizisi</button></div>';
      if (y === "z") {
        if (v.kip === "esit") h += '<div class="aks-iki">' + alan("Kat adedi", "adet", v.adet, ' inputmode="numeric"') + alan("Kat yüksekliği (m)", "yukseklik", v.yukseklik) + "</div>";
        else h += alan("Kat yükseklikleri", "dizi", v.dizi, ' inputmode="text" spellcheck="false" placeholder="1@4.5, 3@3.2"');
        h += '<div class="aks-iki">' + alan("Temel (taban) kotu (m)", "taban", v.taban) + "<span></span></div>";
        h += '<div class="aks-ekz"><div class="aks-ekz-bas"><b>Ek Z aksları</b><span class="not">Saçak, mahya, kren rayı… (kat değildir)</span></div>';
        v.ek.forEach(function (e, i) {
          h += '<div class="aks-ekz-satir"><input class="girdi" data-ek="' + i + '" data-a="ad" value="' + kacis(e.ad) + '" aria-label="Ek Z aksı adı" placeholder="Ad">' +
            '<input class="girdi" data-ek="' + i + '" data-a="konum" value="' + kacis(e.konum) + '" inputmode="decimal" aria-label="' + kacis((e.ad || "Ek Z aksı") + " kotu (m)") + '" placeholder="Kot (m)">' +
            '<button type="button" class="dugme kucuk aks-sil-d" data-ek-sil="' + i + '" aria-label="' + kacis((e.ad || "Ek Z aksı") + " kaldır") + '">×</button></div>';
        });
        h += '<div class="aks-cipler">' + EK_Z_HAZIR.map(function (e) { return '<button type="button" class="bn-cip bn-cip-ekle" data-ek-hazir="' + kacis(e[0]) + '">+ ' + kacis(e[0]) + "</button>"; }).join("") +
          '<button type="button" class="bn-cip bn-cip-ekle" data-ek-hazir="">+ Diğer</button></div></div>';
      } else {
        if (v.kip === "esit") h += '<div class="aks-iki">' + alan("Aks adedi", "adet", v.adet, ' inputmode="numeric"') + alan("Aralık (m)", "aralik", v.aralik) + "</div>";
        else h += alan("Aralıklar ya da konumlar", "dizi", v.dizi, ' inputmode="text" spellcheck="false" placeholder="3@6, 2@7.5, 5"');
        h += '<div class="aks-iki">' + alan("İlk aks adı", "ilk", v.ilk, ' inputmode="text" spellcheck="false" placeholder="' + (y === "x" ? "A" : "1") + '"') + "<span></span></div>";
      }
      if (v.kip === "dizi") h += '<p class="not aks-ipucu"><code>3@6, 2@7.5, 5</code> aralıklar · <code>0 6 12 19.5</code> konumlar · ondalık virgül de olur: <code>7,5</code></p>';
      h += '<p class="aks-durum" data-durum aria-live="polite"></p>';
      return h;
    }
    function ciz() {
      const sek = ["x", "y", "z"].map(function (y) {
        const ad = { x: "X aksları", y: "Y aksları", z: "Z · katlar" }[y];
        return '<button type="button" role="tab" class="aks-sekme" id="' + no + "-t-" + y + '" data-sekme="' + y + '" aria-selected="' + (d.sekme === y) + '" aria-controls="' + no + '-p" tabindex="' + (d.sekme === y ? 0 : -1) + '">' + ad + ' <span class="aks-sayac" data-sayac="' + y + '"></span></button>';
      }).join("");
      kok.innerHTML =
        '<div class="aks-sh-govde"><div class="aks-sh-form">' +
        '<div class="aks-sekmeler" role="tablist" aria-label="Aks yönü">' + sek + "</div>" +
        '<div class="aks-sh-panel" role="tabpanel" id="' + no + '-p" aria-labelledby="' + no + "-t-" + d.sekme + '">' + panelHtml() + "</div></div>" +
        '<div class="aks-sh-onizleme" aria-label="Önizleme"><div data-onizleme></div><p class="aks-ozet" data-ozet></p></div></div>' +
        '<div class="dugmeler aks-sh-dugmeler">' + (sec.iptal ? '<button type="button" class="dugme" data-iptal>İptal</button>' : "") +
        '<button type="button" class="dugme ana" data-tamam>' + (sec.dugmeMetni || "Aksları oluştur") + "</button></div>";
      onizle();
    }
    function onizle() {
      const dr = kok.querySelector("[data-durum]");
      const oz = yonOzet(d.sekme);
      if (dr) { dr.textContent = oz.metin; dr.className = "aks-durum" + (oz.tamam ? "" : " aks-hata"); }
      ["x", "y", "z"].forEach(function (y) {
        const s = kok.querySelector('[data-sayac="' + y + '"]');
        try { s.textContent = "(" + hizliAks(parametre())[y].length + ")"; } catch (e) { s.textContent = "(!)"; }
      });
      const kutu = kok.querySelector("[data-onizleme]"), ozet = kok.querySelector("[data-ozet]"), tm = kok.querySelector("[data-tamam]");
      let r;
      try { r = deger(); } catch (e) {
        kutu.innerHTML = '<div class="aks-mini-bos">' + kacis(e.message) + "</div>"; ozet.textContent = ""; tm.disabled = true; return;
      }
      tm.disabled = false;
      const b = { akslar: r.akslar, katlar: r.katlar };
      const y0 = r.akslar.y[0].ad;
      // önizleme 1:1 piksel (yazılar sahneyle aynı boyda): kutu genişliği ölçülür; geniş kutuda plan ve kesit yan yana
      const kw = kutu.clientWidth || 340, iki = kw >= 600;
      const W = Math.round(Math.max(240, iki ? (kw - 12) / 2 : Math.min(kw, 560)));
      kutu.classList.toggle("aks-iki-fig", iki);
      kutu.innerHTML = '<figure class="aks-fig">' + onizlemeSvg(b, { tur: "plan", z: r.akslar.z[0].ad }, W, Math.round(W * 0.74), "aks-mini-plan", "Plan önizlemesi") + "<figcaption>Plan</figcaption></figure>" +
        '<figure class="aks-fig">' + onizlemeSvg(b, { tur: "cephe", y: y0 }, W, Math.round(W * 0.74), "aks-mini-kesit", "Kesit önizlemesi") + "<figcaption>Kesit · " + kacis(y0) + " aksı</figcaption></figure>";
      const nk = r.katlar.length - 1;
      ozet.textContent = r.akslar.x.length + " X · " + r.akslar.y.length + " Y · " + r.akslar.z.length + " Z aksı · " + nk + " kat · plan " +
        fmt(r.akslar.x[r.akslar.x.length - 1].konum - r.akslar.x[0].konum) + " × " + fmt(r.akslar.y[r.akslar.y.length - 1].konum - r.akslar.y[0].konum) + " m";
    }
    function sekmeSec(y) { if (d.sekme !== y) { d.sekme = y; ciz(); } }
    kok.addEventListener("input", function (e) {
      const t = e.target;
      if (t.hasAttribute("data-alan")) d[d.sekme][t.getAttribute("data-alan")] = t.value;
      else if (t.hasAttribute("data-ek")) d.z.ek[+t.getAttribute("data-ek")][t.getAttribute("data-a")] = t.value;
      onizle();
    });
    kok.addEventListener("click", function (e) {
      const t = e.target.closest("button");
      if (!t) return;
      if (t.hasAttribute("data-sekme")) sekmeSec(t.getAttribute("data-sekme"));
      else if (t.hasAttribute("data-kip")) { d[d.sekme].kip = t.getAttribute("data-kip"); ciz(); const i = kok.querySelector(".aks-sh-panel input"); if (i) i.focus(); }
      else if (t.hasAttribute("data-ek-hazir")) {
        const ad = t.getAttribute("data-ek-hazir");
        let ust = 0;
        try { const ak = hizliAks(Object.assign(parametre(), { ekZ: [] })); ust = ak.z[ak.z.length - 1].konum; } catch (x) { /* yoksay */ }
        const h = EK_Z_HAZIR.find(function (q) { return q[0] === ad; });
        d.z.ek.push({ ad: ad ? benzersizAd(ad, d.z.ek.map(function (q) { return q.ad; })) : "", konum: h ? fmtMakine(r6(ust + h[1])) : "" });
        ciz();
        const i = kok.querySelectorAll(".aks-ekz-satir input");
        if (i.length) i[ad ? i.length - 1 : i.length - 2].focus();
      } else if (t.hasAttribute("data-ek-sil")) { d.z.ek.splice(+t.getAttribute("data-ek-sil"), 1); ciz(); }
      else if (t.hasAttribute("data-tamam")) { try { const r = deger(); if (sec.tamam) sec.tamam(r.akslar, r.katlar); } catch (x) { onizle(); } }
      else if (t.hasAttribute("data-iptal")) { if (sec.iptal) sec.iptal(); }
    });
    kok.addEventListener("keydown", function (e) {
      if (e.target.getAttribute && e.target.getAttribute("role") === "tab") sekmeKlavye(kok.querySelector('[role="tablist"]'), e, sekmeSec);
      else if (e.key === "Enter" && e.target.tagName === "INPUT") { e.preventDefault(); const tm = kok.querySelector("[data-tamam]"); if (!tm.disabled) tm.click(); }
    });
    ciz();
    return { kaldir: function () { kok.remove(); }, deger: deger, eleman: kok };
  }

  // ---------------------------------------------------------------- aks verisi düzenleyici (tablo)
  /**
   * Aks verisi tablosu (§19.3). sec: {bina, degisti(yeniBina, rapor), sekme?: "x"|"y"|"z"|"s:AD", secim?(hedef)}
   * Dönüş: {guncelle(bina), geriAl(), kaldir(), sec(sekme), eleman}
   */
  function duzenleyici(kapsayici, sec) {
    sec = sec || {};
    const d = { bina: sec.bina || { akslar: { x: [], y: [] } }, sekme: sec.sekme || "x", alt: null, secili: null, kaydir: false, yapisik: true,
      geri: [], ileri: [], onay: null, cogalt: false, mesaj: null, odak: null, yeniSistem: false };
    const kok = el("div", { class: "aks-duzenleyici" });
    const no = kimlik("aks-dz");
    kapsayici.innerHTML = "";
    kapsayici.appendChild(kok);

    function sistemAdi() { return d.sekme.indexOf("s:") === 0 ? d.sekme.slice(2) : GLOBAL; }
    function yon() {
      if (d.sekme.indexOf("s:") !== 0) return d.sekme;
      let S; try { S = sistemBul(d.bina, sistemAdi()); } catch (e) { return "x"; }
      const yl = S.zOrtak ? S.yonler.slice(0, 2) : S.yonler;
      if (!d.alt || yl.indexOf(d.alt) < 0) d.alt = yl[0];
      return d.alt;
    }
    function hedef(ad) { return { sistem: sistemAdi(), yon: yon(), ad: ad }; }
    function uygula(fn, sonra) {
      let r;
      try { r = fn(d.bina); } catch (e) { d.mesaj = { tur: "hata", metin: e.message }; ciz(); return null; }
      if (r.onayGerekli) { d.onay = r; d.mesaj = null; ciz(); const b = kok.querySelector(".aks-onay button"); if (b) b.focus(); return r; }
      if (r.silindi === false && r.uyarilar && r.uyarilar.length) { d.mesaj = { tur: "uyari", metin: r.uyarilar.join(" ") }; d.onay = null; ciz(); return r; }
      d.geri.push(d.bina); if (d.geri.length > 60) d.geri.shift(); d.ileri = [];
      d.bina = r.model; d.onay = null;
      d.mesaj = r.uyarilar && r.uyarilar.length ? { tur: "uyari", metin: r.uyarilar.join(" ") } : null;
      if (sonra) sonra(r);
      ciz();
      if (sec.degisti) sec.degisti(d.bina, r);
      return r;
    }
    function geriAl() {
      if (!d.geri.length) return;
      d.ileri.push(d.bina); d.bina = d.geri.pop(); d.onay = null; d.mesaj = { tur: "bilgi", metin: "Son değişiklik geri alındı." };
      ciz();
      if (sec.degisti) sec.degisti(d.bina, { model: d.bina, uyarilar: [], geriAlindi: true });
    }
    function yinele() {
      if (!d.ileri.length) return;
      d.geri.push(d.bina); d.bina = d.ileri.pop(); d.onay = null; d.mesaj = null;
      ciz();
      if (sec.degisti) sec.degisti(d.bina, { model: d.bina, uyarilar: [], yinelendi: true });
    }
    function sekmelerHtml() {
      let S;
      try { S = sistemler(d.bina); } catch (e) { S = [globalSistem({})]; }
      const G = S[0];
      const t = [["x", "X", G.l.x.length], ["y", "Y", G.l.y.length], ["z", "Z", G.l.z.length]].map(function (q) { return { id: q[0], ad: q[1] + " (" + q[2] + ")" }; });
      S.slice(1).forEach(function (s) { t.push({ id: "s:" + s.ad, ad: s.ad, ek: true, s: s }); });
      return t.map(function (q) {
        const ak = d.sekme === q.id;
        return '<button type="button" role="tab" class="aks-sekme' + (q.ek ? " aks-sekme-ek aks-s" + (((q.s.sira - 1) % 3) + 1) : "") + '" data-sekme="' + kacis(q.id) + '" id="' + no + "-t-" + kacis(q.id.replace(/[^\w-]/g, "_")) + '" aria-selected="' + ak + '" tabindex="' + (ak ? 0 : -1) + '" aria-controls="' + no + '-p">' + kacis(q.ad) + "</button>";
      }).join("") + '<button type="button" class="aks-sekme aks-sekme-arti" data-yeni-sistem aria-expanded="' + d.yeniSistem + '">+ Sistem</button>';
    }
    function sistemHtml() {
      if (d.yeniSistem) {
        return '<form class="aks-sistem-form aks-yeni-sistem" data-yeni-sistem-form><b>Yeni aks sistemi</b>' +
          '<label class="aks-alan"><span>Ad</span><input class="girdi" name="ad" value="' + kacis(benzersizAd("KANAT-" + harfAdi((d.bina.aks_sistemleri || []).length), (d.bina.aks_sistemleri || []).map(function (s) { return s.ad; }))) + '" required></label>' +
          '<label class="aks-alan"><span>Tür</span><select class="girdi" name="tur"><option value="kartezyen">Kartezyen (döndürülmüş/ötelenmiş)</option><option value="silindirik">Silindirik (R, θ)</option></select></label>' +
          '<label class="aks-alan"><span>Orijin X (m)</span><input class="girdi" name="ox" value="0" inputmode="decimal"></label>' +
          '<label class="aks-alan"><span>Orijin Y (m)</span><input class="girdi" name="oy" value="0" inputmode="decimal"></label>' +
          '<label class="aks-alan"><span>Açı (°)</span><input class="girdi" name="aci" value="0" inputmode="decimal"></label>' +
          '<div class="dugmeler"><button type="button" class="dugme kucuk" data-yeni-sistem-iptal>Vazgeç</button><button class="dugme kucuk ana">Sistemi ekle</button></div></form>';
      }
      if (d.sekme.indexOf("s:") !== 0) return "";
      let S; try { S = sistemBul(d.bina, sistemAdi()); } catch (e) { return ""; }
      const yl = S.zOrtak ? S.yonler.slice(0, 2) : S.yonler;
      return '<div class="aks-sistem-form" data-sistem-form>' +
        '<label class="aks-alan"><span>Ad</span><input class="girdi" data-sis="ad" value="' + kacis(S.ad) + '"></label>' +
        '<label class="aks-alan"><span>Tür</span><input class="girdi" value="' + (S.tur === "silindirik" ? "Silindirik" : "Kartezyen") + '" readonly tabindex="-1"></label>' +
        '<label class="aks-alan"><span>Orijin X (m)</span><input class="girdi" data-sis="ox" value="' + kacis(fmtKisa(S.orijin[0])) + '" inputmode="decimal"></label>' +
        '<label class="aks-alan"><span>Orijin Y (m)</span><input class="girdi" data-sis="oy" value="' + kacis(fmtKisa(S.orijin[1])) + '" inputmode="decimal"></label>' +
        '<label class="aks-alan"><span>Açı (°)</span><input class="girdi" data-sis="aci" value="' + kacis(fmtKisa(S.aci)) + '" inputmode="decimal"></label>' +
        '<label class="bn-onay aks-onay-kutu"><input type="checkbox" data-sis="gorunur"' + (S.gorunur !== false ? " checked" : "") + "> Görünür</label>" +
        '<button type="button" class="dugme kucuk aks-tehlike" data-sistem-sil>Sistemi sil</button></div>' +
        '<div class="se-seg aks-alt" role="group" aria-label="Yön">' + yl.map(function (y) { return '<button type="button" class="se-seg-d" data-alt="' + y + '" aria-pressed="' + (yon() === y) + '">' + yonAdi(y) + " (" + S.l[y].length + ")</button>"; }).join("") +
        (S.zOrtak ? '<span class="not">Z: GLOBAL Z aksları</span>' : "") + "</div>";
    }
    function tabloHtml() {
      let S, l, y = yon();
      try { S = sistemBul(d.bina, sistemAdi()); l = S.l[y]; } catch (e) { return '<p class="aks-hata">' + kacis(e.message) + "</p>"; }
      const z = y === "z", th = y === "teta";
      const birim = th ? "°" : "m";
      let h = '<div class="aks-tablo-kap"><table class="aks-tablo' + (z ? " aks-tablo-z" : "") + '" aria-label="' + kacis((S.global ? "" : S.ad + " ") + yonAdi(y) + " aks verisi") + '"><thead><tr>' +
        '<th scope="col">Ad</th><th scope="col">' + (z ? "Kot" : th ? "Açı" : "Konum") + " (" + birim + ')</th><th scope="col">Aralık (' + birim + ")</th>" +
        (z ? '<th scope="col">Kat</th>' : '<th scope="col">Tür</th><th scope="col">Görünür</th><th scope="col">Balon</th>') + "</tr></thead><tbody>";
      if (!l.length) h += '<tr><td colspan="' + (z ? 4 : 6) + '" class="not">Aks yok. “+ Sona ekle” ile başlayın.</td></tr>';
      l.forEach(function (a, i) {
        const ar = i ? a.konum - l[i - 1].konum : null;
        const kisa = ar != null && ar < EN_AZ_ARALIK - 1e-9 && !z && !th;
        const ad = kacis(a.ad);
        h += '<tr data-ad="' + ad + '" tabindex="-1" class="' + (d.secili === a.ad ? "secili" : "") + (kisa ? " aks-kisa" : "") + '"' + (d.secili === a.ad ? ' aria-selected="true"' : "") + ">" +
          '<th scope="row"><input class="aks-h" data-sut="ad" data-ad="' + ad + '" value="' + ad + '" data-ilk="' + ad + '" aria-label="Aks adı" spellcheck="false" autocomplete="off"></th>' +
          '<td><input class="aks-h sayi" data-sut="konum" data-ad="' + ad + '" value="' + kacis(fmtKisa(a.konum)) + '" data-ilk="' + kacis(fmtKisa(a.konum)) + '" inputmode="decimal" aria-label="' + ad + " " + (z ? "kotu" : "konumu") + '" autocomplete="off"></td>' +
          "<td>" + (i ? '<input class="aks-h sayi" data-sut="aralik" data-ad="' + ad + '" value="' + kacis(fmtKisa(ar)) + '" data-ilk="' + kacis(fmtKisa(ar)) + '" inputmode="decimal" aria-label="' + ad + ' aralığı" autocomplete="off"' + (kisa ? ' aria-invalid="true" title="Hesap motoru en az 0,30 m aralık ister"' : "") + ">" : '<span class="aks-bos" aria-label="İlk aks: aralık yok">—</span>') + "</td>";
        if (z) {
          h += '<td><input class="aks-h aks-kat" data-sut="kat" data-ad="' + ad + '" value="' + (a.kat != null ? kacis(a.kat) : "") + '" data-ilk="' + (a.kat != null ? kacis(a.kat) : "") + '" inputmode="numeric" placeholder="—" aria-label="' + ad + ' kat numarası (boş: kat değil)" autocomplete="off"' + (S.global ? "" : " disabled") + "></td>";
        } else {
          h += '<td><select class="aks-h" data-sut="tur" data-ad="' + ad + '" aria-label="' + ad + ' türü"><option value="ana"' + (a.tur === "ana" ? " selected" : "") + '>Ana</option><option value="ikincil"' + (a.tur === "ikincil" ? " selected" : "") + ">İkincil</option></select></td>" +
            '<td class="aks-orta"><input type="checkbox" class="aks-h" data-sut="gorunur" data-ad="' + ad + '"' + (a.gorunur !== false ? " checked" : "") + ' aria-label="' + ad + ' görünür"></td>' +
            '<td><select class="aks-h" data-sut="balon" data-ad="' + ad + '" aria-label="' + ad + ' balon yeri">' + [["bas", "Başta"], ["son", "Sonda"], ["iki", "İki uçta"], ["yok", "Yok"]].map(function (q) { return '<option value="' + q[0] + '"' + (a.balon === q[0] ? " selected" : "") + ">" + q[1] + "</option>"; }).join("") + "</select></td>";
        }
        h += "</tr>";
      });
      return h + "</tbody></table></div>";
    }
    function onayHtml() {
      const o = d.onay;
      if (!o) return "";
      if (o.sistemSil) {
        return '<div class="aks-onay" role="alertdialog" aria-labelledby="' + no + '-onay"><p id="' + no + '-onay"><b>' + kacis(o.ad) + "</b> sistemine bağlı " + kacis(o.bagli.toplam) + ' kayıt var.</p><div class="dugmeler">' +
          '<button type="button" class="dugme kucuk aks-tehlike" data-onay="sistem-elemanlarla">Elemanlarla birlikte sil</button><button type="button" class="dugme kucuk" data-onay="iptal">İptal</button></div></div>';
      }
      const b = o.bagli, h = o.hedef;
      return '<div class="aks-onay" role="alertdialog" aria-labelledby="' + no + '-onay" aria-describedby="' + no + '-onay-l"><p id="' + no + '-onay"><b>' + kacis(yonAdi(h.yon) + " aksı " + h.ad) + "</b> silinecek; bu aksa bağlı " + kacis(b.ozet) + " var.</p>" +
        '<ul id="' + no + '-onay-l" class="aks-bagli">' + [["cubuklar", "Çubuk"], ["paneller", "Panel"], ["kolonlar", "Kolon"], ["kirisler", "Kiriş"], ["dosemeler", "Döşeme"], ["dugumler", "Bölme/kesişim düğümü"]].filter(function (q) { return b[q[0]].length; })
          .map(function (q) { return "<li>" + q[1] + ": " + b[q[0]].slice(0, 12).join(", ") + (b[q[0]].length > 12 ? " …" : "") + "</li>"; }).join("") +
        (b.mesnetler.length ? "<li>Mesnet: " + b.mesnetler.length + "</li>" : "") + (b.ek_yukler.length ? "<li>Yük: " + b.ek_yukler.length + "</li>" : "") + "</ul>" +
        '<div class="dugmeler"><button type="button" class="dugme kucuk aks-tehlike" data-onay="elemanlarla">Elemanlarla birlikte sil</button>' +
        (o.komsu ? '<button type="button" class="dugme kucuk" data-onay="tasi">En yakın aksa taşı (' + kacis(o.komsu) + ")</button>" : "") +
        '<button type="button" class="dugme kucuk" data-onay="iptal">İptal</button></div></div>';
    }
    function ciz() {
      const odak = document.activeElement && kok.contains(document.activeElement) ? document.activeElement : null;
      const istek = d.odak || (odak && odak.getAttribute("data-sut") ? { ad: odak.getAttribute("data-ad"), sut: odak.getAttribute("data-sut") } : odak && odak.getAttribute("data-sekme") ? { sekme: odak.getAttribute("data-sekme") } : odak && odak.tagName === "TR" ? { satir: d.secili != null ? d.secili : odak.getAttribute("data-ad") } : null);
      d.odak = null;
      const y = yon(), secVar = d.secili != null;
      kok.innerHTML =
        '<div class="aks-sekmeler" role="tablist" aria-label="Aks sistemi ve yönü">' + sekmelerHtml() + "</div>" +
        '<div class="aks-dz-panel" role="tabpanel" id="' + no + '-p">' + sistemHtml() +
        '<div class="aks-arac-cubugu" role="toolbar" aria-label="Aks işlemleri">' +
        '<button type="button" class="dugme kucuk" data-is="sona">+ Sona ekle</button>' +
        '<button type="button" class="dugme kucuk" data-is="araya"' + (secVar ? "" : " disabled") + ' title="Seçili aksla sonraki aksın ortasına">+ Araya ekle</button>' +
        '<button type="button" class="dugme kucuk" data-is="cogalt"' + (secVar ? "" : " disabled") + ' aria-expanded="' + d.cogalt + '">Çoğalt…</button>' +
        '<button type="button" class="dugme kucuk" data-is="sil"' + (secVar ? "" : " disabled") + ">Sil</button>" +
        '<button type="button" class="dugme kucuk" data-is="sirala">Sırala</button>' +
        '<button type="button" class="dugme kucuk" data-is="harfle" title="' + (y === "z" ? "Kot adlarıyla" : "Konum sırasıyla A, B, C… / 1, 2, 3…") + '">Yeniden adlandır</button>' +
        '<button type="button" class="dugme kucuk" data-is="geri"' + (d.geri.length ? "" : " disabled") + ' aria-keyshortcuts="Control+Z">↶ Geri al</button>' +
        "</div>" +
        '<div class="aks-secenekler"><label class="bn-onay"><input type="checkbox" data-secenek="kaydir"' + (d.kaydir ? " checked" : "") + "> Aralık değişince sonrakileri kaydır</label>" +
        '<label class="bn-onay"><input type="checkbox" data-secenek="yapisik"' + (d.yapisik ? " checked" : "") + "> Elemanlar akslara yapışık</label></div>" +
        (d.cogalt && secVar ? '<form class="aks-cogalt" data-cogalt-form><span>' + kacis(yonAdi(y) + " " + d.secili) + " çoğalt:</span>" +
          '<label class="aks-alan"><span>Ofset (' + (y === "teta" ? "°" : "m") + ')</span><input class="girdi" name="ofset" value="' + (y === "teta" ? "30" : y === "z" ? "3" : "6") + '" inputmode="decimal"></label>' +
          '<label class="aks-alan"><span>Adet</span><input class="girdi" name="adet" value="1" inputmode="numeric"></label><button class="dugme kucuk ana">Çoğalt</button></form>' : "") +
        onayHtml() + tabloHtml() +
        '<p class="aks-mesaj' + (d.mesaj ? " aks-" + d.mesaj.tur : "") + '" aria-live="polite">' + (d.mesaj ? kacis(d.mesaj.metin) : "") + "</p>" +
        '<p class="not aks-klavye">↑/↓ satırlar arası · Enter kaydet ve alta geç · Esc vazgeç · Ctrl+Z geri al</p></div>';
      const lst = kok.querySelector('[role="tablist"]'), akt = lst && lst.querySelector('[aria-selected="true"]');
      if (akt && lst.scrollWidth > lst.clientWidth) {
        const fark = akt.getBoundingClientRect().right - lst.getBoundingClientRect().right;
        if (fark > 0) lst.scrollLeft = fark + 24;
      }
      if (istek) {
        let hedefEl = null;
        if (istek.satir != null) hedefEl = kok.querySelector('tbody tr[data-ad="' + CSSkacis(istek.satir) + '"]') || kok.querySelector("tbody tr");
        else if (istek.sekme) hedefEl = kok.querySelector('[data-sekme="' + CSSkacis(istek.sekme) + '"]');
        else if (istek.ad != null) hedefEl = kok.querySelector('[data-sut="' + istek.sut + '"][data-ad="' + CSSkacis(istek.ad) + '"]');
        if (hedefEl) { hedefEl.focus(); if (hedefEl.select && hedefEl.tagName === "INPUT" && hedefEl.type !== "checkbox") hedefEl.select(); }
      }
    }
    function CSSkacis(s) { return String(s).replace(/["\\]/g, "\\$&"); }
    function hucreKaydet(inp) {
      const sut = inp.getAttribute("data-sut"), ad = inp.getAttribute("data-ad");
      const h = hedef(ad);
      const v = inp.type === "checkbox" ? inp.checked : inp.value;
      if (inp.tagName === "INPUT" && inp.type !== "checkbox" && String(v) === inp.getAttribute("data-ilk")) return false;
      if (sut === "ad") { const ok = uygula(function (b) { return aksYenidenAdlandir(b, { sistem: h.sistem, yon: h.yon, eski: ad, yeni: v }); }); if (ok) { if (d.secili === ad) d.secili = String(v).trim(); } return !!ok; }
      if (sut === "konum") return !!uygula(function (b) { const k = sayiOku(v); if (k == null) throw new AksHatasi("Konum sayı olmalı (ör. 7,5)."); return aksTasi(b, { sistem: h.sistem, yon: h.yon, ad: ad, konum: k, yapisik: d.yapisik }); });
      if (sut === "aralik") return !!uygula(function (b) { return aralikDegistir(b, { sistem: h.sistem, yon: h.yon, ad: ad, aralik: v, kaydir: d.kaydir, yapisik: d.yapisik }); });
      if (sut === "kat") return !!uygula(function (b) { const t = String(v).trim(); if (t !== "" && !/^\d+$/.test(t)) throw new AksHatasi("Kat numarası 0, 1, 2… olmalı (boş: kat değil)."); return aksOzellik(b, { sistem: h.sistem, yon: h.yon, ad: ad, ozellik: { kat: t === "" ? null : +t } }); });
      const oz = {}; oz[sut] = v;
      return !!uygula(function (b) { return aksOzellik(b, { sistem: h.sistem, yon: h.yon, ad: ad, ozellik: oz }); });
    }
    function satirKomsu(ad, adim) {
      const s = Array.from(kok.querySelectorAll("tbody tr[data-ad]")).map(function (r) { return r.getAttribute("data-ad"); });
      const i = s.indexOf(ad);
      return i < 0 ? null : s[Math.max(0, Math.min(s.length - 1, i + adim))];
    }
    function isYap(is) {
      const y = yon(), sAd = sistemAdi(), ad = d.secili;
      if (is === "sona") uygula(function (b) { return aksEkle(b, { sistem: sAd, yon: y }); }, function (r) { d.secili = r.eklenen; d.odak = { ad: r.eklenen, sut: "konum" }; });
      else if (is === "araya" && ad != null) {
        const n = satirKomsu(ad, 1);
        if (n == null || n === ad) { d.mesaj = { tur: "uyari", metin: "Seçili aks sonuncu; araya eklemek için sonraki aks gerekir." }; ciz(); return; }
        uygula(function (b) { return aksEkle(b, { sistem: sAd, yon: y, arasina: [ad, n] }); }, function (r) { d.secili = r.eklenen; d.odak = { ad: r.eklenen, sut: "ad" }; });
      } else if (is === "cogalt") { d.cogalt = !d.cogalt; ciz(); const i = kok.querySelector("[data-cogalt-form] input"); if (i) i.focus(); }
      else if (is === "sil" && ad != null) {
        const sonraki = satirKomsu(ad, 1) !== ad ? satirKomsu(ad, 1) : satirKomsu(ad, -1);
        const r = uygula(function (b) { return aksSil(b, { sistem: sAd, yon: y, ad: ad }); });
        if (r && r.onayGerekli) d.onay.hedef = { sistem: sAd, yon: y, ad: ad };
        else if (r && r.silindi) { d.secili = sonraki !== ad ? sonraki : null; ciz(); }
        if (r && r.onayGerekli) ciz();
      } else if (is === "sirala") uygula(function (b) { return aksSirala(b, { sistem: sAd, yon: y }); }, function () { d.mesaj = { tur: "bilgi", metin: "Aks listesi konuma göre sıralandı." }; });
      else if (is === "harfle") uygula(function (b) { return yenidenHarfle(b, { sistem: sAd, yon: y }); }, function (r) { const n = Object.keys(r.esleme).length; d.secili = d.secili != null && r.esleme[d.secili] ? r.esleme[d.secili] : d.secili; d.mesaj = { tur: "bilgi", metin: n ? n + " aks yeniden adlandırıldı; bütün başvurular güncellendi." : "Adlar zaten sıralı." }; });
      else if (is === "geri") geriAl();
    }
    kok.addEventListener("click", function (e) {
      const t = e.target;
      const b = t.closest("button");
      const tr = t.closest("tbody tr[data-ad]");
      if (tr && !b && !t.closest("input, select")) tr.focus();
      if (tr && !b) { const ad = tr.getAttribute("data-ad"); if (d.secili !== ad) { d.secili = ad; tr.parentNode.querySelectorAll("tr").forEach(function (r) { r.classList.toggle("secili", r === tr); r.toggleAttribute("aria-selected", r === tr); }); kok.querySelectorAll('[data-is="araya"],[data-is="cogalt"],[data-is="sil"]').forEach(function (x) { x.disabled = false; }); if (sec.secim) sec.secim(hedef(ad)); } return; }
      if (!b) return;
      if (b.hasAttribute("data-sekme")) { const s = b.getAttribute("data-sekme"); if (s !== d.sekme) { d.sekme = s; d.secili = null; d.onay = null; d.cogalt = false; d.yeniSistem = false; d.mesaj = null; d.odak = { sekme: s }; ciz(); } }
      else if (b.hasAttribute("data-yeni-sistem")) { d.yeniSistem = !d.yeniSistem; ciz(); const i = kok.querySelector("[data-yeni-sistem-form] input"); if (i) i.focus(); }
      else if (b.hasAttribute("data-yeni-sistem-iptal")) { d.yeniSistem = false; ciz(); }
      else if (b.hasAttribute("data-alt")) { d.alt = b.getAttribute("data-alt"); d.secili = null; ciz(); }
      else if (b.hasAttribute("data-is")) isYap(b.getAttribute("data-is"));
      else if (b.hasAttribute("data-sistem-sil")) {
        const ad = sistemAdi();
        const r = sistemSil(d.bina, ad);
        if (r.onayGerekli) { d.onay = { sistemSil: true, ad: ad, bagli: r.bagli }; ciz(); }
        else uygula(function (bb) { return sistemSil(bb, ad); }, function () { d.sekme = "x"; });
      } else if (b.hasAttribute("data-onay")) {
        const o = d.onay, s = b.getAttribute("data-onay");
        if (s === "iptal" || !o) { d.onay = null; d.mesaj = { tur: "bilgi", metin: "Silme iptal edildi." }; ciz(); return; }
        if (s === "sistem-elemanlarla") { uygula(function (bb) { return sistemSil(bb, o.ad, "elemanlarla"); }, function () { d.sekme = "x"; }); return; }
        const h = o.hedef;
        const sonraki = satirKomsu(h.ad, 1) !== h.ad ? satirKomsu(h.ad, 1) : satirKomsu(h.ad, -1);
        uygula(function (bb) { return aksSil(bb, { sistem: h.sistem, yon: h.yon, ad: h.ad, secenek: s }); }, function () { d.secili = sonraki !== h.ad ? sonraki : null; });
      }
    });
    kok.addEventListener("change", function (e) {
      const t = e.target;
      if (t.hasAttribute("data-sut")) { if (!d._kaydediyor) hucreKaydet(t); }
      else if (t.hasAttribute("data-secenek")) d[t.getAttribute("data-secenek")] = t.checked;
      else if (t.hasAttribute("data-sis")) {
        const k = t.getAttribute("data-sis"), ad = sistemAdi();
        const dg = {};
        if (k === "ad") dg.ad = t.value.trim();
        else if (k === "gorunur") dg.gorunur = t.checked;
        else if (k === "aci") dg.aci = t.value;
        else { const S = sistemBul(d.bina, ad); dg.orijin = S.orijin.slice(); dg.orijin[k === "ox" ? 0 : 1] = t.value; }
        uygula(function (b) { return sistemGuncelle(b, ad, dg); }, function () { if (dg.ad) d.sekme = "s:" + dg.ad; });
      }
    });
    kok.addEventListener("submit", function (e) {
      e.preventDefault();
      const f = e.target;
      if (f.hasAttribute("data-cogalt-form")) {
        const h = hedef(d.secili);
        uygula(function (b) { return aksCogalt(b, { sistem: h.sistem, yon: h.yon, ad: h.ad, ofset: f.ofset.value, adet: f.adet.value }); }, function (r) { d.cogalt = false; d.mesaj = { tur: "bilgi", metin: r.eklenen.length + " aks eklendi: " + r.eklenen.join(", ") }; });
      } else if (f.hasAttribute("data-yeni-sistem-form")) {
        const s = { ad: f.ad.value.trim(), tur: f.tur.value, orijin: [sayiOku(f.ox.value) || 0, sayiOku(f.oy.value) || 0, 0], aci: sayiOku(f.aci.value) || 0, z: null };
        uygula(function (b) { return sistemEkle(b, s); }, function () { d.yeniSistem = false; d.sekme = "s:" + s.ad; d.alt = null; d.secili = null; });
      }
    });
    kok.addEventListener("keydown", function (e) {
      const t = e.target;
      if (t.getAttribute && t.getAttribute("role") === "tab") { sekmeKlavye(kok.querySelector('[role="tablist"]'), e, function (s) { d.sekme = s; d.secili = null; d.onay = null; d.mesaj = null; ciz(); }); return; }
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && (e.key === "z" || e.key === "Z")) {
        if (t.tagName === "INPUT" && t.type !== "checkbox" && t.value !== t.getAttribute("data-ilk")) return;   // girişin kendi geri alması
        e.preventDefault(); geriAl(); return;
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === "y" || e.key === "Y" || (e.shiftKey && (e.key === "z" || e.key === "Z")))) { e.preventDefault(); yinele(); return; }
      if (e.key === "Escape" && d.onay) { e.preventDefault(); d.onay = null; ciz(); return; }
      if (t.tagName === "TR" && t.hasAttribute("data-ad")) {
        // satır odağı: ↑/↓ satır seçer, Delete/Backspace siler, Enter ilk hücreye girer
        const ad = t.getAttribute("data-ad");
        if (e.key === "ArrowDown" || e.key === "ArrowUp") {
          e.preventDefault();
          const n = satirKomsu(ad, e.key === "ArrowDown" ? 1 : -1);
          const r = n != null ? kok.querySelector('tbody tr[data-ad="' + CSSkacis(n) + '"]') : null;
          if (r) { r.focus(); r.click(); }
        } else if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); d.secili = ad; isYap("sil"); }
        else if (e.key === "Enter") { e.preventDefault(); const i = t.querySelector('input[data-sut="konum"]'); if (i) { i.focus(); i.select(); } }
        return;
      }
      if (!t.hasAttribute || !t.hasAttribute("data-sut")) return;
      const ad = t.getAttribute("data-ad"), sut = t.getAttribute("data-sut"), metin = t.tagName === "INPUT" && t.type !== "checkbox";
      if (e.key === "Escape" && metin) { e.preventDefault(); t.value = t.getAttribute("data-ilk"); t.blur(); return; }
      const git = function (adim) {
        const n = satirKomsu(ad, adim);
        if (n == null) return;
        d.secili = n;
        if (metin && t.value !== t.getAttribute("data-ilk")) {
          d.odak = { ad: n, sut: sut };
          d._kaydediyor = true;
          const ok = hucreKaydet(t);
          d._kaydediyor = false;
          if (ok) return;
        }
        const h = kok.querySelector('[data-sut="' + sut + '"][data-ad="' + CSSkacis(n) + '"]');
        kok.querySelectorAll("tbody tr").forEach(function (r) { r.classList.toggle("secili", r.getAttribute("data-ad") === n); });
        if (h) { h.focus(); if (h.select && h.tagName === "INPUT" && h.type !== "checkbox") h.select(); }
      };
      if (e.key === "Enter" && metin) { e.preventDefault(); git(1); }
      else if ((e.key === "ArrowDown" || e.key === "ArrowUp") && t.tagName !== "SELECT") { e.preventDefault(); git(e.key === "ArrowDown" ? 1 : -1); }
    });
    kok.addEventListener("focusin", function (e) {
      const t = e.target;
      if (!t.hasAttribute || !t.hasAttribute("data-ad")) return;
      const ad = t.getAttribute("data-ad");
      if (d.secili === ad) return;
      d.secili = ad;
      kok.querySelectorAll("tbody tr").forEach(function (r) { r.classList.toggle("secili", r.getAttribute("data-ad") === ad); });
      kok.querySelectorAll('[data-is="araya"],[data-is="cogalt"],[data-is="sil"]').forEach(function (x) { x.disabled = false; });
      if (sec.secim) sec.secim(hedef(ad));
    });
    ciz();
    return {
      guncelle: function (b) { d.bina = b; d.onay = null; ciz(); },
      geriAl: geriAl, yinele: yinele,
      sec: function (s, ad) { d.sekme = s; if (ad != null) d.secili = String(ad); ciz(); },
      bina: function () { return d.bina; },
      kaldir: function () { kok.remove(); }, eleman: kok,
    };
  }

  const ARAYUZ = {
    sahneKatmani: sahneKatmani, uygunIzdusum: uygunIzdusum, kenarPaylari: kenarPaylari, surukleKonum: surukleKonum, aksHedefi: aksHedefi, kesisimHedefi: kesisimHedefi,
    balonSurukle: balonSurukle, sihirbaz: sihirbaz, duzenleyici: duzenleyici,
  };

  return Object.freeze(Object.assign({}, SAF, ARAYUZ));
});
