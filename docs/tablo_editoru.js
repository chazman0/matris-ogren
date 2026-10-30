/* Matris Öğren — tablo editörü (tasarım belgesi §15.3): bina tablolarını (tablolar.py → köprü "bina_tablolar") gösterir,
   düzenler, CSV'ye aktarır ve statik hesap raporuna seçtirir. Bağımlılıksız; tarayıcıda window.MatrisTablo, node'da
   module.exports (yalnız saf mantık `_ic` node testlidir).

   Kullanım:
     const ed = MatrisTablo.ac(kapsayici, {
       tablolar,                         // [TABLO] (§15.1 şeması)
       bina,                             // düzenlemelerin uygulanacağı bina JSON'u (sözlük)
       duzenle(yeniBina, degisiklikler, bilgi),   // "Uygula": değişiklikler binaya uygulanmış KOPYA + [{yol, deger, bag?}]
                                         //  (bilgi.geriAl = true: uygulanmış son düzenlemenin geri alınması). Promise dönebilir.
       raporSecimi: Set,                 // rapora eklenecek tablo adları
       raporSecimiDegisti(set),          // seçim her değişince (yeni Set)
       baslangic?, cozumlu?, dosyaOnEki?, kapat?() // ilk tablo; sonuçlar (Analiz/Tasarım…) var mı; CSV dosya adı öneki; ✕ düğmesi
     });
     ed.guncelle({tablolar?, bina?, raporSecimi?, cozumlu?})   // yeni tablolar (ör. yeniden çözümden sonra)
     ed.raporSecimi()      → Set (kopya)
     ed.raporSecenegi()    → {tablolar: [ad...], tablo_filtre: {ad: {satirlar: [indeks...]}}}  (köprü "bina_rapor" secenek'i)
     ed.sec(ad)            // tabloyu aç
     ed.kapat()            // DOM'u ve dinleyicileri kaldırır

   Düzenleme: yalnız sütunu `duzenlenebilir` ve satırında `yol` olan hücreler. Değişen hücre sarı; "Uygula" bütün bekleyen
   değişiklikleri binanın kopyasına uygular (`_ic.degisiklikleriUygula`: tablolar.degisiklikleri_uygula ile aynı anlam) ve
   `duzenle`yi çağırır; "Geri al" önce bekleyenleri, sonra uygulanmış düzenlemeleri (bina anlık görüntüsü) geri alır.
   Hesap tablosu programlarından sekmeyle ayrılmış (TSV) yapıştırma etkin hücreden itibaren yazar; CSV UTF-8 BOM'lu, `;`
   ayırıcılı ve isteğe bağlı ondalık virgüllüdür (Türkçe hesap tablosu programları için). */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika(kok);
  if (typeof module === "object" && module && module.exports) module.exports = api;
  if (kok && typeof kok === "object") kok.MatrisTablo = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function (kok) {
  "use strict";

  const GRUPLAR = ["Model", "Yükler", "Deprem", "Analiz", "Tasarım", "Temel", "Metraj"];
  const SONUC_GRUPLARI = ["Analiz", "Tasarım"];         // model değişince geçersiz olan gruplar (Deprem/Temel hesap satırları da)

  // ======================================================================
  // Saf mantık (DOM'suz)
  // ======================================================================
  function kopya(o) {
    if (o === undefined) return undefined;
    return JSON.parse(JSON.stringify(o));
  }
  function nesneMi(o) { return o !== null && typeof o === "object" && !Array.isArray(o); }
  function tamSayiMi(p) { return typeof p === "number" && Number.isInteger(p); }

  /** tablolar._esit ile aynı: bool katı, sayılar sayısal, dizi/sözlük öğe öğe. */
  function esit(a, b) {
    if (typeof a === "boolean" || typeof b === "boolean") return a === b;
    if (typeof a === "number" && typeof b === "number") return a === b;
    if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every(function (x, i) { return esit(x, b[i]); });
    if (nesneMi(a) && nesneMi(b)) {
      const ka = Object.keys(a), kb = Object.keys(b);
      return ka.length === kb.length && ka.every(function (k) { return Object.prototype.hasOwnProperty.call(b, k) && esit(a[k], b[k]); });
    }
    if (a === undefined) a = null;
    if (b === undefined) b = null;
    return a === b;
  }
  function eslesir(e, sec) {
    if (!nesneMi(e)) return false;
    return Object.keys(sec).every(function (k) {
      if (k.charAt(0) === "_") return true;
      return Object.prototype.hasOwnProperty.call(e, k) && esit(e[k], sec[k]);
    });
  }

  function yolHatasi(m) { const e = new Error(m); e.name = "YolHatasi"; return e; }

  /** Bir yol adımı: kap[p] (gerekirse oluşturarak) — tablolar._adim ile aynı. */
  function adim(kap, p, sonraki, olustur) {
    if (nesneMi(p)) {
      if (!Array.isArray(kap)) throw yolHatasi("seçici " + JSON.stringify(p) + " bir liste bekler");
      for (const e of kap) if (eslesir(e, p)) return e;
      if (olustur && p._olustur) {
        const yeni = {};
        Object.keys(p).forEach(function (k) { if (k.charAt(0) !== "_") yeni[k] = kopya(p[k]); });
        kap.push(yeni);
        return yeni;
      }
      throw yolHatasi("listede " + JSON.stringify(p) + " ile eşleşen eleman yok");
    }
    if (typeof p === "boolean") throw yolHatasi("yol adımı bool olamaz");
    if (tamSayiMi(p)) {
      if (!Array.isArray(kap) || p < -kap.length || p >= kap.length) throw yolHatasi("liste sırası " + p + " yok");
      return kap[p < 0 ? kap.length + p : p];
    }
    if (!nesneMi(kap)) throw yolHatasi(JSON.stringify(p) + " anahtarı bir sözlük bekler");
    if (!Object.prototype.hasOwnProperty.call(kap, p) || kap[p] === null || kap[p] === undefined) {
      if (!olustur) throw yolHatasi(JSON.stringify(p) + " anahtarı yok");
      kap[p] = (nesneMi(sonraki) || tamSayiMi(sonraki)) ? [] : {};
    }
    return kap[p];
  }
  function cokluYol(yol) { return Array.isArray(yol) && yol.length > 0 && Array.isArray(yol[0]); }

  /** Yolun gösterdiği değer (son anahtar yoksa null); ara adım yoksa hata. Yolların listesinde ilk yol. */
  function yolAl(bina, yol) {
    if (cokluYol(yol)) yol = yol[0];
    let kap = bina;
    for (let i = 0; i < yol.length - 1; i++) kap = adim(kap, yol[i], yol[i + 1], false);
    const son = yol[yol.length - 1];
    if (nesneMi(kap) && typeof son === "string") return Object.prototype.hasOwnProperty.call(kap, son) && kap[son] !== undefined ? kap[son] : null;
    return adim(kap, son, null, false);
  }
  /** Yerinde yazar; ara sözlük/listeler ve `_olustur` seçicili elemanlar oluşturulur. Yolların listesinde hepsine. */
  function yolAta(bina, yol, deger) {
    if (cokluYol(yol)) { yol.forEach(function (y) { yolAta(bina, y, kopya(deger)); }); return bina; }
    if (!Array.isArray(yol) || !yol.length) throw yolHatasi("yol boş");
    let kap = bina;
    for (let i = 0; i < yol.length - 1; i++) kap = adim(kap, yol[i], yol[i + 1], true);
    const son = yol[yol.length - 1];
    if (nesneMi(son)) throw yolHatasi("yolun son adımı seçici olamaz (alan adı ya da sıra olmalı)");
    if (tamSayiMi(son)) {
      if (!Array.isArray(kap) || son < -kap.length || son >= kap.length) throw yolHatasi("liste sırası " + son + " yok");
      kap[son < 0 ? kap.length + son : son] = deger;
    } else {
      if (!nesneMi(kap)) throw yolHatasi(JSON.stringify(son) + " anahtarı bir sözlük bekler");
      kap[son] = deger;
    }
    return bina;
  }

  const AKS_SIRA = { x: 0, y: 1, r: 0, teta: 1 };
  function sistemAdi(s) { return s === undefined || s === null || s === "" || s === "GLOBAL" ? null : String(s); }
  function adMetni(x) { return String(x === undefined || x === null ? "" : x).trim(); }
  function basitMi(x) { return x === null || typeof x !== "object"; }

  function aksListesi(bina, yon, sistem) {
    sistem = sistemAdi(sistem);
    let liste;
    if (sistem === null) liste = nesneMi(bina.akslar) ? bina.akslar[yon] : undefined;
    else {
      const s = (Array.isArray(bina.aks_sistemleri) ? bina.aks_sistemleri : []).find(function (s) { return nesneMi(s) && String(s.ad) === sistem; });
      if (!s) throw yolHatasi("aks sistemi " + JSON.stringify(sistem) + " yok");
      liste = s[yon];
    }
    if (!Array.isArray(liste)) throw yolHatasi(yon + " aks listesi yok" + (sistem ? " (" + sistem + ")" : ""));
    return liste;
  }

  /** tablolar.aks_yeniden_adlandir ile aynı: aksı (yerinde) yeniden adlandırır, bağlı başvuruları günceller. */
  function aksYenidenAdlandir(bina, yon, eski, yeni, sistem) {
    yon = String(yon).toLowerCase();
    eski = adMetni(eski);
    yeni = adMetni(yeni);
    if (!yeni) throw new Error("Aks adı boş olamaz.");
    const liste = aksListesi(bina, yon, sistem);
    let hedef = null;
    for (const a of liste) {
      if (!nesneMi(a)) continue;
      const ad = adMetni(a.ad);
      if (ad === yeni && yeni !== eski) throw new Error(yon.toUpperCase() + " aksı '" + yeni + "' zaten var; aks adları benzersiz olmalı.");
      if (ad === eski && !hedef) hedef = a;
    }
    if (!hedef) throw yolHatasi(yon.toUpperCase() + " aksı '" + eski + "' yok");
    if (yeni === eski) return bina;
    hedef.ad = yeni;
    sistem = sistemAdi(sistem);
    const zOrtak = new Set((Array.isArray(bina.aks_sistemleri) ? bina.aks_sistemleri : [])
      .filter(function (s) { return nesneMi(s) && !(Array.isArray(s.z) && s.z.length); }).map(function (s) { return String(s.ad); }));
    const i = AKS_SIRA[yon];
    function uyar(rs) {
      if (yon === "z" && sistem === null) return rs === null || zOrtak.has(rs);
      return rs === sistem;
    }
    function yurut(o, kokMu) {
      if (Array.isArray(o)) { o.forEach(function (v) { yurut(v, false); }); return; }
      if (!nesneMi(o)) return;
      const rs = sistemAdi(o.sistem);
      if (yon === "z") {
        if (Object.prototype.hasOwnProperty.call(o, "aks") && typeof o.z === "string" && o.z.trim() === eski && uyar(rs)) o.z = yeni;
      } else if (i !== undefined) {
        const a = o.aks;
        if (Array.isArray(a) && a.length > i && basitMi(a[i]) && adMetni(a[i]) === eski && uyar(rs)) a[i] = yeni;
        if (sistem === null && rs === null && (yon === "x" || yon === "y")) {
          ["bas", "son"].forEach(function (k) {
            const b = o[k];
            if (Array.isArray(b) && b.length === 2 && basitMi(b[i]) && adMetni(b[i]) === eski) b[i] = yeni;
          });
          if (Array.isArray(o.kose)) {
            o.kose.forEach(function (kk) {
              if (Array.isArray(kk) && kk.length === 2 && basitMi(kk[i]) && adMetni(kk[i]) === eski) kk[i] = yeni;
            });
          }
        }
      }
      Object.keys(o).forEach(function (k) {
        if (kokMu && (k === "akslar" || k === "aks_sistemleri")) return;
        yurut(o[k], false);
      });
    }
    yurut(bina, true);
    return bina;
  }

  /** tablolar.aks_sistemi_yeniden_adlandir ile aynı. */
  function aksSistemiYenidenAdlandir(bina, eski, yeni) {
    eski = adMetni(eski);
    yeni = adMetni(yeni);
    if (!yeni || yeni === "GLOBAL") throw new Error("Aks sistemi adı boş ya da 'GLOBAL' olamaz.");
    const sistemler = (Array.isArray(bina.aks_sistemleri) ? bina.aks_sistemleri : []).filter(nesneMi);
    const hedef = sistemler.find(function (s) { return adMetni(s.ad) === eski; });
    if (!hedef) throw yolHatasi("aks sistemi '" + eski + "' yok");
    if (yeni === eski) return bina;
    if (sistemler.some(function (s) { return adMetni(s.ad) === yeni; })) throw new Error("Aks sistemi '" + yeni + "' zaten var.");
    hedef.ad = yeni;
    function yurut(o, kokMu) {
      if (Array.isArray(o)) { o.forEach(function (v) { yurut(v, false); }); return; }
      if (!nesneMi(o)) return;
      if (typeof o.sistem === "string" && o.sistem.trim() === eski) o.sistem = yeni;
      Object.keys(o).forEach(function (k) { if (!(kokMu && k === "aks_sistemleri")) yurut(o[k], false); });
    }
    yurut(bina, true);
    return bina;
  }

  function bagSirasi(d) {
    const bag = d && d.bag;
    if (!nesneMi(bag)) return 0;
    return bag.islem === "sistem_ad" ? 2 : 1;
  }
  /** Tek değişikliği yerinde uygular: {yol, deger, bag?}. */
  function degisiklikUygula(bina, d) {
    const bag = d.bag;
    if (nesneMi(bag) && bag.islem === "aks_ad") return aksYenidenAdlandir(bina, bag.yon, yolAl(bina, d.yol), d.deger, bag.sistem);
    if (nesneMi(bag) && bag.islem === "sistem_ad") return aksSistemiYenidenAdlandir(bina, yolAl(bina, d.yol), d.deger);
    return yolAta(bina, d.yol, kopya(d.deger === undefined ? null : d.deger));
  }
  /** Değişiklikleri binanın KOPYASINA uygular (önce düz yazımlar, sonra aks adları, en son sistem adları; kararlı). */
  function degisiklikleriUygula(bina, degisiklikler) {
    const yeni = kopya(bina);
    const sirali = (degisiklikler || []).map(function (d, i) { return [bagSirasi(d), i, d]; })
      .sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    sirali.forEach(function (x) { degisiklikUygula(yeni, x[2]); });
    return yeni;
  }

  // ---------------------------------------------------------------- metin ↔ değer
  const TR_KATLA = { "ı": "i", "İ": "i", "ş": "s", "ğ": "g", "ç": "c", "ö": "o", "ü": "u", "â": "a", "î": "i", "û": "u" };
  /** Karşılaştırma için: Türkçe küçük harf + ASCII'ye katlama ("Kapalı" → "kapali"). */
  function katla(m) {
    return String(m === undefined || m === null ? "" : m).toLocaleLowerCase("tr").replace(/[ışğçöüâîûİ]/g, function (c) { return TR_KATLA[c] || c; }).trim();
  }

  /** Sayı okuma: "1,5" "1.5" "1.234,5" "1,234.5" "1 234,5" "−2" "1e-3" "%10" → sayı; okunamazsa NaN. */
  function sayiOku(m) {
    if (typeof m === "number") return isFinite(m) ? m : NaN;
    let s = String(m === undefined || m === null ? "" : m).replace(/[\s  ']/g, "").replace(/−/g, "-").replace(/%/g, "");
    if (!s) return NaN;
    const nokta = (s.match(/\./g) || []).length, virgul = (s.match(/,/g) || []).length;
    if (nokta && virgul) {
      if (s.lastIndexOf(",") > s.lastIndexOf(".")) s = s.replace(/\./g, "").replace(",", ".");
      else s = s.replace(/,/g, "");
    } else if (virgul) {
      s = virgul > 1 ? s.replace(/,/g, "") : s.replace(",", ".");
    } else if (nokta > 1) {
      s = s.replace(/\./g, "");
    }
    if (!/^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(s)) return NaN;
    return parseFloat(s);
  }

  const DOGRU = ["1", "true", "evet", "e", "dogru", "var", "acik", "✓", "✔", "x", "yes", "y", "on", "+"];
  const YANLIS = ["0", "false", "hayir", "h", "yanlis", "yok", "kapali", "–", "-", "✗", "✘", "no", "n", "off"];

  /** Hücre türü: sütun tanımı + satıra özgü `hucre` üstüne yazımı. */
  function hucreTuru(satir, sutun) {
    const t = Object.assign({}, sutun || {});
    const h = satir && satir.hucre && sutun ? satir.hucre[sutun.ad] : null;
    if (h) Object.assign(t, h);
    if (!t.tur) t.tur = "sayi";
    return t;
  }
  function duzenlenebilir(satir, sutun) {
    return !!(sutun && sutun.duzenlenebilir && satir && satir.yol && satir.yol[sutun.ad]);
  }
  function secenekDeger(o) { return nesneMi(o) && Object.prototype.hasOwnProperty.call(o, "deger") ? o.deger : o; }
  function secenekEtiket(o) {
    if (nesneMi(o) && Object.prototype.hasOwnProperty.call(o, "deger")) return String(o.etiket !== undefined ? o.etiket : o.deger);
    return o === null || o === undefined ? "" : String(o);
  }

  /** Metni hücre türüne göre değere çevirir → {deger} | {hata}. */
  function degerCevir(metin, tur) {
    tur = tur || { tur: "sayi" };
    if (typeof metin !== "string") {
      if (metin === null || metin === undefined) metin = "";
      else if (typeof metin === "boolean" && tur.tur === "bool") return { deger: metin };
      else metin = String(metin);
    }
    const ham = metin.trim();
    if (tur.tur === "bool") {
      const k = katla(ham);
      if (DOGRU.indexOf(k) >= 0) return { deger: true };
      if (YANLIS.indexOf(k) >= 0 || k === "") return { deger: false };
      return { hata: "evet/hayır (1/0, doğru/yanlış) bekleniyor: " + JSON.stringify(ham) };
    }
    if (tur.tur === "secim") {
      const sec = tur.secenekler || [];
      if (ham === "") {
        const bos = sec.find(function (o) { const d = secenekDeger(o); return d === null || d === ""; });
        if (bos !== undefined) return { deger: secenekDeger(bos) };
        if (tur.bos_olur) return { deger: null };
        return { hata: "boş bırakılamaz; seçenekler: " + sec.map(secenekEtiket).join(", ") };
      }
      const k = katla(ham);
      for (const o of sec) {
        const d = secenekDeger(o);
        if (d !== null && d !== undefined && katla(d) === k) return { deger: d };
      }
      for (const o of sec) if (katla(secenekEtiket(o)) === k) return { deger: secenekDeger(o) };
      const n = sayiOku(ham);
      if (!isNaN(n)) for (const o of sec) if (secenekDeger(o) === n) return { deger: n };
      return { hata: JSON.stringify(ham) + " seçeneklerde yok: " + sec.map(secenekEtiket).join(", ") };
    }
    if (tur.tur === "metin") {
      if (ham === "" && tur.bos_olur) return { deger: null };
      return { deger: ham };
    }
    // sayı
    if (ham === "") {
      if (tur.bos_olur) return { deger: null };
      return { hata: "sayı bekleniyor (boş bırakılamaz)" };
    }
    let v = sayiOku(ham);
    if (isNaN(v)) return { hata: "sayı okunamadı: " + JSON.stringify(ham) };
    if (/%/.test(ham) && tur.birim !== "%") v = v / 100;      // "%10" → 0.10 (oran); birimi % olan sütunda 10
    if (tur.ondalik === 0 && !Number.isInteger(v)) return { hata: "tam sayı bekleniyor: " + JSON.stringify(ham) };
    return { deger: v };
  }

  /** Görüntü metni — tablolar.hucre_metni ile aynı kural. */
  function bicimle(deger, tur, ondalikVirgul) {
    tur = tur || {};
    if (deger === null || deger === undefined) return "";
    if (typeof deger === "boolean") return deger ? "✓" : "–";
    for (const o of tur.secenekler || []) if (nesneMi(o) && esit(o.deger, deger)) return String(o.etiket !== undefined ? o.etiket : deger);
    if (typeof deger === "number") {
      if (!isFinite(deger)) return "";
      const od = tur.ondalik;
      let m;
      if (od === undefined || od === null) {
        if (Number.isInteger(deger)) m = String(deger);
        else if (Math.abs(deger) >= 1e-4) {
          m = deger.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
          if (m === "-0" || m === "") m = "0";
        } else m = deger.toExponential(3).replace(/e([+-])(\d)$/, "e$10$2");
      } else {
        m = deger.toFixed(Math.max(0, Math.min(10, od | 0)));
        if (parseFloat(m) === 0) m = m.replace(/^-/, "");
      }
      return ondalikVirgul ? m.replace(".", ",") : m;
    }
    return String(deger);
  }

  // ---------------------------------------------------------------- sıralama ve süzme
  function karsilastir(a, b) {
    const ab = a === null || a === undefined || a === "", bb = b === null || b === undefined || b === "";
    if (ab || bb) return ab === bb ? 0 : (ab ? 1 : -1);
    if (typeof a === "number" && typeof b === "number") return a - b;
    if (typeof a === "boolean" && typeof b === "boolean") return (a ? 1 : 0) - (b ? 1 : 0);
    return String(a).localeCompare(String(b), "tr", { numeric: true, sensitivity: "base" });
  }
  /** Satır sırası (asıl indeksler) → sıralı yeni dizi. Boşlar her iki yönde de sonda; özet (Σ) satırları en sonda; kararlı. */
  function sirala(satirlar, idx, sutunAd, yon) {
    if (!sutunAd || !yon) return idx.slice();
    const k = yon === "azalan" ? -1 : 1;
    const normal = idx.filter(function (i) { return !satirlar[i].ozet; });
    const ozet = idx.filter(function (i) { return satirlar[i].ozet; });
    normal.sort(function (i, j) {
      const a = satirlar[i].degerler[sutunAd], b = satirlar[j].degerler[sutunAd];
      const ab = a === null || a === undefined || a === "", bb = b === null || b === undefined || b === "";
      if (ab || bb) return ab === bb ? i - j : (ab ? 1 : -1);
      return k * karsilastir(a, b) || i - j;
    });
    return normal.concat(ozet);
  }

  /** Süzgeç ifadesi: "metin" (içerir) | "=metin" (tam) | ">1" ">=0,5" "<3" "<=2" "<>0" | "1..5" (aralık) | "boş" | "dolu" |
   *  "!ifade" (değil) | "a|b" (ya da). Büyük/küçük harf ve Türkçe harf duyarsız. */
  function suzgecEslesir(deger, tur, ifade) {
    const alt = String(ifade).split("|").map(function (s) { return s.trim(); }).filter(function (s) { return s !== ""; });
    if (!alt.length) return true;
    return alt.some(function (s) { return tekSuzgec(deger, tur, s); });
  }
  function tekSuzgec(deger, tur, s) {
    if (s.charAt(0) === "!" && s.length > 1) return !tekSuzgec(deger, tur, s.slice(1).trim());
    const bos = deger === null || deger === undefined || deger === "";
    const k = katla(s);
    if (k === "bos") return bos;
    if (k === "dolu") return !bos;
    const sayisal = typeof deger === "number";
    let m = /^(<=|>=|<>|!=|<|>|=)\s*(.+)$/.exec(s);
    if (m) {
      const op = m[1], sag = m[2].trim();
      const n = sayiOku(sag);
      if (sayisal && !isNaN(n)) {
        return op === "<" ? deger < n : op === ">" ? deger > n : op === "<=" ? deger <= n : op === ">=" ? deger >= n
          : op === "=" ? Math.abs(deger - n) <= 1e-9 * Math.max(1, Math.abs(n)) : Math.abs(deger - n) > 1e-9 * Math.max(1, Math.abs(n));
      }
      if (op === "=" || op === "<>" || op === "!=") {
        const es = katla(bicimle(deger, tur)) === katla(sag) || katla(deger) === katla(sag);
        return op === "=" ? es : !es;
      }
      return false;
    }
    m = /^(.+?)\s*\.\.\s*(.+)$/.exec(s);
    if (m && sayisal) {
      const a = sayiOku(m[1]), b = sayiOku(m[2]);
      if (!isNaN(a) && !isNaN(b)) return deger >= Math.min(a, b) && deger <= Math.max(a, b);
    }
    if (bos) return false;
    if (typeof deger === "boolean") {
      if (DOGRU.indexOf(k) >= 0) return deger === true;
      if (YANLIS.indexOf(k) >= 0) return deger === false;
    }
    const gor = katla(bicimle(deger, tur));
    return gor.indexOf(k) >= 0 || katla(deger).indexOf(k) >= 0;
  }
  /** Süzgeçleri ({sutun_ad: ifade}) geçen satırların asıl indeksleri (özet/Σ satırları da aynı süzgeçten geçer). */
  function suz(tablo, suzgecler) {
    const etkin = Object.keys(suzgecler || {}).filter(function (a) { return String(suzgecler[a] || "").trim() !== ""; });
    const sonuc = [];
    const sutun = {};
    (tablo.sutunlar || []).forEach(function (s) { sutun[s.ad] = s; });
    (tablo.satirlar || []).forEach(function (r, i) {
      for (const a of etkin) if (!suzgecEslesir(r.degerler[a], hucreTuru(r, sutun[a] || { ad: a }), suzgecler[a])) return;
      sonuc.push(i);
    });
    return sonuc;
  }
  /** Görünen satırların toplamı (tablo.toplam'daki sütunlar için; özet satırları hariç). */
  function toplamHesapla(tablo, idx) {
    const t = {};
    Object.keys(tablo.toplam || {}).forEach(function (a) {
      let s = 0, var_ = false;
      idx.forEach(function (i) {
        const r = tablo.satirlar[i];
        const v = r.degerler[a];
        if (!r.ozet && typeof v === "number" && isFinite(v)) { s += v; var_ = true; }
      });
      if (var_) t[a] = s;
    });
    return t;
  }
  function dcAsimi(deger, tur) {
    return !!(tur && tur.vurgu === "dc" && typeof deger === "number" && deger > 1 + 1e-12);
  }

  // ---------------------------------------------------------------- CSV ve TSV
  function csvAlan(m, ayirici) {
    m = String(m === undefined || m === null ? "" : m);
    if (m.indexOf(ayirici) >= 0 || /["\r\n\t]/.test(m) || /^\s|\s$/.test(m)) return '"' + m.replace(/"/g, '""') + '"';
    return m;
  }
  /** Ham değerin dışa aktarım metni (tam duyarlık; ondalık virgül seçeneği; bool evet/hayır; seçimde etiket). */
  function disaDeger(deger, tur, ondalikVirgul) {
    if (deger === null || deger === undefined) return "";
    if (typeof deger === "boolean") return deger ? "evet" : "hayır";
    for (const o of (tur && tur.secenekler) || []) if (nesneMi(o) && esit(o.deger, deger)) return String(o.etiket !== undefined ? o.etiket : deger);
    if (typeof deger === "number") {
      if (!isFinite(deger)) return "";
      let m = String(Number(deger.toPrecision(12)));
      m = m.replace(/e/i, "E");
      return ondalikVirgul ? m.replace(".", ",") : m;
    }
    return String(deger);
  }
  function baslikMetni(s) { return s.birim ? s.baslik + " [" + s.birim + "]" : s.baslik; }
  /** Tek tablo CSV'si (BOM yok; satır sonu CRLF). sec: {ayirici, ondalikVirgul, idx?, toplam?: true} */
  function csvSatirlari(tablo, sec) {
    sec = sec || {};
    const ay = sec.ayirici || ";", ov = sec.ondalikVirgul !== false;
    const sutunlar = tablo.sutunlar || [];
    const idx = sec.idx || tablo.satirlar.map(function (_, i) { return i; });
    const satirlar = [sutunlar.map(function (s) { return csvAlan(baslikMetni(s), ay); }).join(ay)];
    idx.forEach(function (i) {
      const r = tablo.satirlar[i];
      satirlar.push(sutunlar.map(function (s) { return csvAlan(disaDeger(r.degerler[s.ad], hucreTuru(r, s), ov), ay); }).join(ay));
    });
    const top = sec.toplam === false ? null : (sec.idx ? toplamHesapla(tablo, idx) : tablo.toplam);
    if (top && Object.keys(top).length) {
      satirlar.push(sutunlar.map(function (s, j) {
        if (Object.prototype.hasOwnProperty.call(top, s.ad)) return csvAlan(disaDeger(top[s.ad], s, ov), ay);
        return j === 0 ? csvAlan("Toplam", ay) : "";
      }).join(ay));
    }
    return satirlar;
  }
  const BOM = "﻿";
  function csvUret(tablo, sec) { return BOM + csvSatirlari(tablo, sec).join("\r\n") + "\r\n"; }
  /** Tek CSV'de bölümlü bütün tablolar: her bölüm "Tablo: başlık;grup" satırı + başlık + satırlar + boş satır. */
  function tumunuCsv(tablolar, sec) {
    sec = sec || {};
    const ay = sec.ayirici || ";";
    const parca = [];
    (tablolar || []).forEach(function (t) {
      parca.push([csvAlan("Tablo: " + t.baslik, ay), csvAlan(t.grup || "", ay), csvAlan(t.ad, ay)].join(ay));
      Array.prototype.push.apply(parca, csvSatirlari(t, { ayirici: ay, ondalikVirgul: sec.ondalikVirgul }));
      parca.push("");
    });
    return BOM + parca.join("\r\n") + "\r\n";
  }
  /** Sekmeyle ayrılmış metin (hesap tablosu programlarından kopyalanan hücreler) → satır × sütun dizisi. Tırnaklı alanlar
   *  (içinde sekme/satır sonu olabilir) desteklenir; sondaki tek satır sonu atılır. */
  function tsvAyristir(metin) {
    const s = String(metin === undefined || metin === null ? "" : metin).replace(/\r\n?/g, "\n").replace(/^﻿/, "");
    const sonuc = [];
    let satir = [], alan = "", i = 0, tirnak = false, alanBasi = true;
    while (i < s.length) {
      const c = s.charAt(i);
      if (tirnak) {
        if (c === '"') {
          if (s.charAt(i + 1) === '"') { alan += '"'; i += 2; continue; }
          tirnak = false; i++; continue;
        }
        alan += c; i++; continue;
      }
      if (c === '"' && alanBasi) { tirnak = true; alanBasi = false; i++; continue; }
      if (c === "\t") { satir.push(alan); alan = ""; alanBasi = true; i++; continue; }
      if (c === "\n") { satir.push(alan); sonuc.push(satir); satir = []; alan = ""; alanBasi = true; i++; continue; }
      alan += c; alanBasi = false; i++;
    }
    if (alan !== "" || satir.length || !alanBasi) { satir.push(alan); sonuc.push(satir); }
    return sonuc;
  }
  /** Seçili hücreler → TSV (sekme/satır sonu içeren alan tırnaklı). */
  function tsvUret(matris) {
    return matris.map(function (r) {
      return r.map(function (m) { m = String(m === undefined || m === null ? "" : m); return /["\t\n\r]/.test(m) ? '"' + m.replace(/"/g, '""') + '"' : m; }).join("\t");
    }).join("\r\n");
  }

  /** Yapıştırma planı: matris (tsvAyristir) görünür satır/sütun düzeninde (r0, c0)'dan itibaren yazılır. 1×1 matris ve
   *  `aralik` ({r0, c0, r1, c1}) verilirse aralığın tamamı doldurulur. → {degisiklikler: [{satir, sutun, yol, deger, bag?,
   *  ilk}], hatalar: [metin], atlanan: n} — `satir` asıl satır indeksi. */
  function yapistirmaPlani(tablo, gorunurSatir, gorunurSutun, r0, c0, matris, aralik) {
    const plan = { degisiklikler: [], hatalar: [], atlanan: 0 };
    if (!matris || !matris.length) return plan;
    let hedefler = [];
    if (matris.length === 1 && matris[0].length === 1 && aralik && (aralik.r1 > aralik.r0 || aralik.c1 > aralik.c0)) {
      for (let r = aralik.r0; r <= aralik.r1; r++) for (let c = aralik.c0; c <= aralik.c1; c++) hedefler.push([r, c, matris[0][0]]);
    } else {
      matris.forEach(function (satir, i) { satir.forEach(function (m, j) { hedefler.push([r0 + i, c0 + j, m]); }); });
    }
    hedefler.forEach(function (h) {
      const ri = gorunurSatir[h[0]], s = gorunurSutun[h[1]];
      if (ri === undefined || !s) { plan.atlanan++; return; }
      const satir = tablo.satirlar[ri];
      if (!duzenlenebilir(satir, s)) { plan.atlanan++; return; }
      const tur = hucreTuru(satir, s);
      const c = degerCevir(h[2], tur);
      if (c.hata) { plan.hatalar.push("Satır " + (ri + 1) + ", " + s.baslik + ": " + c.hata); return; }
      const d = { satir: ri, sutun: s.ad, yol: satir.yol[s.ad], deger: c.deger, ilk: satir.degerler[s.ad] };
      if (satir.bag && satir.bag[s.ad]) d.bag = satir.bag[s.ad];
      plan.degisiklikler.push(d);
    });
    return plan;
  }

  /** Bekleyen (uygulanmamış) düzenlemeler: yol anahtarına göre (aynı alanı gösteren bütün hücreler aynı değeri gösterir),
   *  geri al yığını (her ekleme bir adım). */
  function Duzenleme() {
    this.bekleyen = new Map();
    this.yigin = [];
  }
  Duzenleme.anahtar = function (yol) { return JSON.stringify(yol); };
  Duzenleme.prototype.ekle = function (liste) {
    const adim_ = [];
    const self = this;
    (liste || []).forEach(function (d) {
      const k = Duzenleme.anahtar(d.yol);
      const onceki = self.bekleyen.get(k);
      const ilk = onceki ? onceki.ilk : d.ilk;
      adim_.push({ k: k, onceki: onceki });
      if (esit(d.deger, ilk)) self.bekleyen.delete(k);
      else self.bekleyen.set(k, { yol: d.yol, deger: d.deger, bag: d.bag, ilk: ilk, tablo: d.tablo, satir: d.satir, sutun: d.sutun });
    });
    if (adim_.length) this.yigin.push(adim_);
    return adim_.length;
  };
  Duzenleme.prototype.geriAl = function () {
    const adim_ = this.yigin.pop();
    if (!adim_) return false;
    for (let i = adim_.length - 1; i >= 0; i--) {
      const a = adim_[i];
      if (a.onceki) this.bekleyen.set(a.k, a.onceki); else this.bekleyen.delete(a.k);
    }
    return true;
  };
  Duzenleme.prototype.deger = function (yol) {
    const e = this.bekleyen.get(Duzenleme.anahtar(yol));
    return e;
  };
  Duzenleme.prototype.sayi = function () { return this.bekleyen.size; };
  Duzenleme.prototype.degisiklikler = function () {
    return Array.from(this.bekleyen.values()).map(function (e) {
      const d = { yol: e.yol, deger: e.deger };
      if (e.bag) d.bag = e.bag;
      return d;
    });
  };
  Duzenleme.prototype.tablolar = function () {
    const s = new Set();
    this.bekleyen.forEach(function (e) { if (e.tablo) s.add(e.tablo); });
    return s;
  };
  Duzenleme.prototype.temizle = function () { this.bekleyen.clear(); this.yigin = []; };

  /** Yolun okunur yazımı: katlar › [no = 2] › kot. */
  function yolMetni(yol) {
    if (cokluYol(yol)) return yol.map(yolMetni).join("  +  ");
    return (yol || []).map(function (p) {
      if (nesneMi(p)) return "[" + Object.keys(p).filter(function (k) { return k.charAt(0) !== "_"; }).map(function (k) { return k + " = " + JSON.stringify(p[k]); }).join(", ") + "]";
      if (tamSayiMi(p)) return "[" + p + "]";
      return String(p);
    }).join(" › ");
  }
  /** Tablo listesi grup sırasıyla: [[grup, [tablo...]]]. */
  function gruplu(tablolar) {
    const g = new Map();
    GRUPLAR.forEach(function (x) { g.set(x, []); });
    (tablolar || []).forEach(function (t) { const k = t.grup || "Diğer"; if (!g.has(k)) g.set(k, []); g.get(k).push(t); });
    return Array.from(g.entries()).filter(function (x) { return x[1].length; });
  }
  /** Sütun genişliği önerisi (px): başlık, birim ve ilk satırların görüntü uzunluğundan. */
  function sutunGenisligi(tablo, s, ornek) {
    let n = Math.max(String(s.baslik || "").length * 0.92, (s.birim ? String(s.birim).length + 2 : 0));
    const satirlar = tablo.satirlar || [];
    const adim_ = Math.max(1, Math.floor(satirlar.length / (ornek || 200)));
    for (let i = 0; i < satirlar.length; i += adim_) {
      const r = satirlar[i];
      const m = bicimle(r.degerler[s.ad], hucreTuru(r, s));
      if (m.length > n) n = m.length;
    }
    const tur = s.tur || "sayi";
    return Math.round(Math.max(tur === "bool" ? 52 : 64, Math.min(tur === "metin" ? 340 : 200, n * 7.4 + 22)));
  }

  const _ic = {
    GRUPLAR: GRUPLAR, esit: esit, kopya: kopya, yolAl: yolAl, yolAta: yolAta, cokluYol: cokluYol,
    aksYenidenAdlandir: aksYenidenAdlandir, aksSistemiYenidenAdlandir: aksSistemiYenidenAdlandir,
    degisiklikUygula: degisiklikUygula, degisiklikleriUygula: degisiklikleriUygula,
    katla: katla, sayiOku: sayiOku, degerCevir: degerCevir, bicimle: bicimle, hucreTuru: hucreTuru, duzenlenebilir: duzenlenebilir,
    sirala: sirala, suzgecEslesir: suzgecEslesir, suz: suz, toplamHesapla: toplamHesapla, dcAsimi: dcAsimi,
    csvAlan: csvAlan, disaDeger: disaDeger, csvUret: csvUret, tumunuCsv: tumunuCsv, tsvAyristir: tsvAyristir, tsvUret: tsvUret,
    yapistirmaPlani: yapistirmaPlani, Duzenleme: Duzenleme, yolMetni: yolMetni, gruplu: gruplu, sutunGenisligi: sutunGenisligi,
    secenekDeger: secenekDeger, secenekEtiket: secenekEtiket,
  };

  // ======================================================================
  // Arayüz (DOM)
  // ======================================================================
  function kacis(m) {
    return String(m === undefined || m === null ? "" : m).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function depoAl(a, v) { try { const x = kok.localStorage.getItem("matris-tablo-" + a); return x === null ? v : JSON.parse(x); } catch (e) { return v; } }
  function depoYaz(a, v) { try { kok.localStorage.setItem("matris-tablo-" + a, JSON.stringify(v)); } catch (e) { /* yok say */ } }
  function dosyaAdi(m) { return String(m || "tablo").replace(/[\\/:*?"<>|\s]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 80) || "tablo"; }
  function indir(ad, metin) {
    const blob = new Blob([metin], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = ad; a.rel = "noopener";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  let acikSayisi = 0;
  function ac(kapsayici, secenek) {
    if (!kapsayici || !kapsayici.appendChild) throw new Error("MatrisTablo.ac: kapsayıcı öğe gerekli.");
    const sec = Object.assign({}, secenek || {});
    const D = {
      tablolar: Array.isArray(sec.tablolar) ? sec.tablolar : [],
      bina: sec.bina || null,
      rapor: new Set(sec.raporSecimi ? Array.from(sec.raporSecimi) : []),
      cozumlu: sec.cozumlu !== undefined ? !!sec.cozumlu : (sec.tablolar || []).some(function (t) { return SONUC_GRUPLARI.indexOf(t.grup) >= 0; }),
      eski: false,                          // uygulanan düzenlemeden sonra sonuç tabloları eski
      ad: null, tablo: null,
      durum: new Map(),                     // tablo adı → {sira: {sutun, yon}, suzgec: {}, secili: Set, kaydir}
      gorunur: [],                          // görünür satırların asıl indeksleri (süz + sırala)
      duz: new Duzenleme(),
      gecmis: [],                           // uygulanmış düzenlemeler: önceki bina anlık görüntüleri
      aktif: { r: 0, c: 0 }, capa: null,    // etkin hücre ve aralık çapası (görünür koordinat)
      satirH: 30, pencere: [0, 0], editor: null,
      csv: Object.assign({ ayirici: ";", ondalikVirgul: true }, depoAl("csv", {})),
      raporSuz: !!depoAl("rapor-suz", false),
      kapali: new Set(depoAl("kapali-gruplar", [])),
      liste: "",
    };
    const salt = typeof sec.duzenle !== "function";
    const kimlik = "tablo-ed-" + (++acikSayisi);

    const kok_ = document.createElement("div");
    kok_.className = "tablo-ed" + (salt ? " tablo-ed-salt" : "");
    kok_.innerHTML =
      '<div class="tablo-ed-ust">' +
      '  <div class="tablo-ed-mobil"><label class="tablo-ed-gizli" for="' + kimlik + '-liste">Tablo</label><select class="girdi tablo-ed-mliste" id="' + kimlik + '-liste"></select>' +
      '    <label class="tablo-ed-onay tablo-ed-mrapor"><input type="checkbox"> Rapora ekle</label></div>' +
      '  <div class="tablo-ed-baslik"><h3></h3><span class="tablo-ed-sayac"></span></div>' +
      '  <div class="tablo-ed-araclar">' +
      (salt ? "" :
        '    <button type="button" class="dugme kucuk ana tablo-ed-uygula" disabled title="Bekleyen değişiklikleri modele uygula">Uygula</button>' +
        '    <button type="button" class="dugme kucuk tablo-ed-geri" disabled title="Geri al (Ctrl+Z)">↶ Geri al</button>' +
        '    <button type="button" class="dugme kucuk tablo-ed-yapistir" title="Hesap tablosu programından kopyalanan hücreleri etkin hücreden itibaren yapıştır (Ctrl+V)">Yapıştır…</button>') +
      '    <button type="button" class="dugme kucuk tablo-ed-temizle" title="Sıralama ve süzgeçleri kaldır">Süzgeçleri temizle</button>' +
      '    <div class="tablo-ed-menu"><button type="button" class="dugme kucuk tablo-ed-csv-d" aria-haspopup="true" aria-expanded="false">CSV ▾</button>' +
      '      <div class="tablo-ed-menu-liste" hidden>' +
      '        <button type="button" data-csv="bu">Bu tablo (görünen satırlar)</button>' +
      '        <button type="button" data-csv="rapor">Rapora seçilenler — tek CSV</button>' +
      '        <button type="button" data-csv="tek">Bütün tablolar — tek CSV (bölümlü)</button>' +
      '        <button type="button" data-csv="ayri">Bütün tablolar — ayrı dosyalar</button>' +
      '        <button type="button" data-csv="kopyala">Görünen tabloyu panoya kopyala (sekmeli)</button>' +
      '        <label class="tablo-ed-onay"><input type="checkbox" data-ayar="ondalikVirgul"> Ondalık virgül (3,14)</label>' +
      '        <label class="tablo-ed-onay"><input type="checkbox" data-ayar="virgulAyirici"> Ayırıcı virgül (yoksa ;)</label>' +
      "      </div></div>" +
      (sec.kapat ? '    <button type="button" class="dugme kucuk tablo-ed-kapat" aria-label="Tablo editörünü kapat">✕</button>' : "") +
      "  </div>" +
      "</div>" +
      '<div class="tablo-ed-uyari" hidden></div>' +
      '<div class="tablo-ed-govde">' +
      '  <nav class="tablo-ed-liste" aria-label="Tablolar">' +
      '    <input type="search" class="girdi tablo-ed-ara" placeholder="Tablo ara…" aria-label="Tablo ara">' +
      '    <div class="tablo-ed-gruplar"></div>' +
      '    <div class="tablo-ed-rapor-alt"><span class="tablo-ed-rapor-say"></span>' +
      '      <button type="button" class="dugme kucuk tablo-ed-rapor-hepsi">Tümü</button><button type="button" class="dugme kucuk tablo-ed-rapor-hic">Hiçbiri</button></div>' +
      "  </nav>" +
      '  <section class="tablo-ed-sag">' +
      '    <p class="tablo-ed-aciklama"></p>' +
      '    <div class="tablo-ed-izgara" tabindex="0" role="region" aria-label="Tablo ızgarası (ok tuşları, Enter düzenle, Ctrl+C/V)"><table class="tablo-ed-tablo"><colgroup></colgroup><thead></thead><tbody></tbody><tfoot></tfoot></table></div>' +
      '    <div class="tablo-ed-durum" aria-live="polite"><span class="tablo-ed-hucre-bilgi"></span><span class="tablo-ed-mesaj"></span></div>' +
      '    <label class="tablo-ed-onay tablo-ed-rapor-suz"><input type="checkbox"> Raporda yalnız görünen (süzülen ya da seçili) satırlar</label>' +
      "  </section>" +
      "</div>" +
      '<div class="tablo-ed-yapistir-kutu" hidden role="dialog" aria-label="Yapıştır">' +
      '  <p>Hesap tablosu programından kopyaladığınız hücreleri (sekmeyle ayrılmış) buraya yapıştırın; etkin hücreden itibaren sağa ve aşağı yazılır. Salt okunur hücreler atlanır.</p>' +
      '  <textarea class="girdi" rows="6" spellcheck="false"></textarea>' +
      '  <div class="dugmeler"><button type="button" class="dugme kucuk ana" data-yap="tamam">Yapıştır</button><button type="button" class="dugme kucuk" data-yap="iptal">Vazgeç</button></div>' +
      "</div>";
    kapsayici.appendChild(kok_);

    const $ = function (s) { return kok_.querySelector(s); };
    const E = {
      baslik: $(".tablo-ed-baslik h3"), sayac: $(".tablo-ed-sayac"), uygula: $(".tablo-ed-uygula"), geri: $(".tablo-ed-geri"),
      yapistir: $(".tablo-ed-yapistir"), temizle: $(".tablo-ed-temizle"), csvD: $(".tablo-ed-csv-d"), csvMenu: $(".tablo-ed-menu-liste"),
      uyari: $(".tablo-ed-uyari"), gruplar: $(".tablo-ed-gruplar"), ara: $(".tablo-ed-ara"), raporSay: $(".tablo-ed-rapor-say"),
      aciklama: $(".tablo-ed-aciklama"), izgara: $(".tablo-ed-izgara"), tablo: $(".tablo-ed-tablo"), colgroup: $("colgroup"),
      thead: $("thead"), tbody: $("tbody"), tfoot: $("tfoot"), bilgi: $(".tablo-ed-hucre-bilgi"), mesaj: $(".tablo-ed-mesaj"),
      mliste: $(".tablo-ed-mliste"), mrapor: $(".tablo-ed-mrapor input"), raporSuz: $(".tablo-ed-rapor-suz input"),
      yapKutu: $(".tablo-ed-yapistir-kutu"), yapMetin: $(".tablo-ed-yapistir-kutu textarea"),
    };
    E.raporSuz.checked = D.raporSuz;
    $('[data-ayar="ondalikVirgul"]').checked = !!D.csv.ondalikVirgul;
    $('[data-ayar="virgulAyirici"]').checked = D.csv.ayirici === ",";

    let mesajZaman = null;
    function mesaj(m, tur) {
      E.mesaj.textContent = m || "";
      E.mesaj.className = "tablo-ed-mesaj" + (tur ? " tablo-ed-mesaj-" + tur : "");
      clearTimeout(mesajZaman);
      if (m && tur !== "hata") mesajZaman = setTimeout(function () { E.mesaj.textContent = ""; }, 6000);
    }
    function tdurum(ad) {
      if (!D.durum.has(ad)) D.durum.set(ad, { sira: { sutun: null, yon: null }, suzgec: {}, secili: new Set(), kaydir: 0 });
      return D.durum.get(ad);
    }
    function raporBildir() {
      if (typeof sec.raporSecimiDegisti === "function") {
        try { sec.raporSecimiDegisti(new Set(D.rapor)); } catch (e) { mesaj("Rapor seçimi bildirilemedi: " + e.message, "hata"); }
      }
      raporSayYaz();
    }
    function raporSayYaz() {
      const n = D.tablolar.filter(function (t) { return D.rapor.has(t.ad); }).length;
      E.raporSay.textContent = n ? "Rapora: " + n + " tablo" : "Rapora tablo seçilmedi";
      E.mrapor.checked = !!(D.ad && D.rapor.has(D.ad));
    }

    // ------------------------------------------------------------ liste
    function listeCiz() {
      const ara = katla(D.liste);
      const bekleyen = D.duz.tablolar();
      let h = "";
      gruplu(D.tablolar).forEach(function (g) {
        const ad = g[0];
        const liste = g[1].filter(function (t) { return !ara || katla(t.baslik).indexOf(ara) >= 0 || katla(t.ad).indexOf(ara) >= 0; });
        if (!liste.length) return;
        const hepsi = liste.every(function (t) { return D.rapor.has(t.ad); }), biri = liste.some(function (t) { return D.rapor.has(t.ad); });
        const eskiG = D.eski && (SONUC_GRUPLARI.indexOf(ad) >= 0);
        h += '<details class="tablo-ed-grup"' + (D.kapali.has(ad) && !ara ? "" : " open") + ' data-grup="' + kacis(ad) + '"><summary>' +
          '<input type="checkbox" class="tablo-ed-grup-rapor" title="Bu gruptaki bütün tabloları rapora ekle" aria-label="' + kacis(ad) + ' grubunu rapora ekle"' +
          (hepsi ? " checked" : "") + (biri && !hepsi ? ' data-yarim="1"' : "") + "> <span>" + kacis(ad) + "</span> <small>" + liste.length + "</small>" +
          (eskiG ? ' <span class="tablo-ed-eski-rozet" title="Model değişti: yeniden çözülene kadar eski">eski</span>' : "") + "</summary><ul>";
        liste.forEach(function (t) {
          h += '<li class="tablo-ed-oge' + (t.ad === D.ad ? " aktif" : "") + '" data-ad="' + kacis(t.ad) + '">' +
            '<input type="checkbox" class="tablo-ed-oge-rapor" title="Rapora ekle" aria-label="' + kacis(t.baslik) + ' rapora ekle"' + (D.rapor.has(t.ad) ? " checked" : "") + ">" +
            '<button type="button" class="tablo-ed-oge-d"' + (t.ad === D.ad ? ' aria-current="true"' : "") + ">" + kacis(t.baslik) +
            (bekleyen.has(t.ad) ? ' <span class="tablo-ed-nokta" title="Uygulanmamış değişiklik var">●</span>' : "") +
            ' <small>' + (t.satirlar || []).length + "</small></button></li>";
        });
        h += "</ul></details>";
      });
      E.gruplar.innerHTML = h || '<p class="not">Tablo yok.</p>';
      E.gruplar.querySelectorAll('[data-yarim="1"]').forEach(function (k) { k.indeterminate = true; });
      // telefon listesi
      let m = "";
      gruplu(D.tablolar).forEach(function (g) {
        m += '<optgroup label="' + kacis(g[0]) + '">' + g[1].map(function (t) {
          return '<option value="' + kacis(t.ad) + '"' + (t.ad === D.ad ? " selected" : "") + ">" + kacis(t.baslik) + " (" + (t.satirlar || []).length + ")</option>";
        }).join("") + "</optgroup>";
      });
      E.mliste.innerHTML = m;
      raporSayYaz();
    }

    // ------------------------------------------------------------ tablo seçimi ve başlık
    function sutunlar() { return D.tablo ? D.tablo.sutunlar || [] : []; }
    function yenidenHesapla() {
      const t = D.tablo;
      if (!t) { D.gorunur = []; return; }
      const d = tdurum(t.ad);
      D.gorunur = sirala(t.satirlar, suz(t, d.suzgec), d.sira.sutun, d.sira.yon);
    }
    let olcer = null;
    /** Sütun genişliği (px): yazı tipiyle ölçülür (başlık kalın, değerler örneklenir); ölçülemezse karakter sayısından. */
    function genislik(t, s) {
      if (!olcer) {
        try { olcer = document.createElement("canvas").getContext("2d"); } catch (e) { olcer = false; }
      }
      if (!olcer) return sutunGenisligi(t, s);
      if (!D._aile) {     // tuval yazı tipi sözdizimi "-apple-system" gibi adları kabul etmez: ayıkla, olmazsa sans-serif
        const aile = (getComputedStyle(E.tablo).fontFamily || "").split(",").map(function (x) { return x.trim(); })
          .filter(function (x) { return x && x.charAt(0) !== "-" && x !== "BlinkMacSystemFont"; }).join(", ") || "sans-serif";
        olcer.font = "13.5px " + aile;
        D._aile = /13\.5px/.test(olcer.font) ? aile : "sans-serif";
      }
      const aile = D._aile;
      olcer.font = "700 12.5px " + aile;
      let w = olcer.measureText(String(s.baslik || "")).width + (s.duzenlenebilir && !salt ? 16 : 0) + 30;
      olcer.font = "500 11.5px " + aile;
      w = Math.max(w, olcer.measureText(String(s.birim || "")).width + 26);
      olcer.font = "13.5px " + aile;
      const satirlar = t.satirlar || [];
      const adim_ = Math.max(1, Math.floor(satirlar.length / 300));
      let dc = false, enUzun = 0;
      for (let i = 0; i < satirlar.length; i += adim_) {
        const r = satirlar[i], tur = hucreTuru(r, s), v = r.degerler[s.ad];
        const m = bicimle(v, tur);
        if (m) enUzun = Math.max(enUzun, olcer.measureText(m).width * (typeof v === "number" ? 1.06 : 1.02));
        if (dcAsimi(v, tur)) dc = true;
      }
      w = Math.max(w, enUzun + 22 + (dc ? 14 : 0));
      const tur = s.tur || "sayi";
      return Math.round(Math.max(tur === "bool" ? 48 : 56, Math.min(tur === "metin" ? 360 : 240, w)));
    }
    function basCiz() {
      const t = D.tablo, d = tdurum(t.ad);
      const ss = sutunlar();
      let col = '<col class="tablo-ed-no-col" style="width:52px">';
      let gen = 52;
      ss.forEach(function (s) { const w = s._gen || (s._gen = genislik(t, s)); gen += w; col += '<col style="width:' + w + 'px">'; });
      E.colgroup.innerHTML = col;
      E.tablo.style.width = gen + "px";
      let h1 = '<tr class="tablo-ed-bas"><th class="tablo-ed-no" scope="col" title="Satır no (tablodaki asıl sıra)">#</th>';
      ss.forEach(function (s, j) {
        const ok = d.sira.sutun === s.ad ? (d.sira.yon === "azalan" ? "▼" : "▲") : "";
        const duz = !salt && s.duzenlenebilir;
        h1 += '<th scope="col" aria-colindex="' + (j + 2) + '"' + (ok ? ' aria-sort="' + (d.sira.yon === "azalan" ? "descending" : "ascending") + '"' : "") +
          ' class="' + (s.tur === "sayi" || !s.tur ? "tablo-ed-sayi" : "") + (duz ? " tablo-ed-bas-duz" : "") + '">' +
          '<button type="button" class="tablo-ed-sirala" data-c="' + j + '" title="Sırala: ' + kacis(baslikMetni(s)) + (duz ? " (düzenlenebilir)" : "") + '">' +
          '<span class="tablo-ed-sb">' + kacis(s.baslik) + (duz ? ' <span class="tablo-ed-kalem" aria-hidden="true">✎</span>' : "") + "</span>" +
          (s.birim ? '<span class="tablo-ed-birim">' + kacis(s.birim) + "</span>" : '<span class="tablo-ed-birim">&nbsp;</span>') +
          '<span class="tablo-ed-ok" aria-hidden="true">' + ok + "</span></button></th>";
      });
      h1 += "</tr>";
      let h2 = '<tr class="tablo-ed-suz-satir"><th class="tablo-ed-no" scope="col"><span class="tablo-ed-gizli">Süzgeç</span>⌕</th>';
      ss.forEach(function (s, j) {
        const v = d.suzgec[s.ad] || "";
        h2 += '<th scope="col"><input type="text" class="tablo-ed-suz' + (v ? " dolu" : "") + '" data-c="' + j + '" value="' + kacis(v) +
          '" placeholder="süz" aria-label="' + kacis(s.baslik) + ' süzgeci" title="metin (içerir), >1, <=0,5, 1..5, =A, !x, boş, dolu, a|b" spellcheck="false" autocomplete="off"></th>';
      });
      h2 += "</tr>";
      E.thead.innerHTML = h1 + h2;
      E.tablo.setAttribute("aria-colcount", String(ss.length + 1));
    }
    function sec_(ad, koru) {
      const t = D.tablolar.find(function (x) { return x.ad === ad; }) || D.tablolar[0] || null;
      editorKapat(true, true);          // açık düzenleyicideki değer kaybolmasın
      if (D.tablo) tdurum(D.tablo.ad).kaydir = E.izgara.scrollTop;
      D.tablo = t;
      D.ad = t ? t.ad : null;
      if (D.ad) depoYaz("son", D.ad);
      if (!t) {
        E.baslik.textContent = "Tablo yok";
        E.aciklama.textContent = "";
        E.thead.innerHTML = E.tbody.innerHTML = E.tfoot.innerHTML = E.colgroup.innerHTML = "";
        E.sayac.textContent = "";
        listeCiz();
        return;
      }
      E.baslik.textContent = t.baslik;
      const eskiT = D.eski && SONUC_GRUPLARI.indexOf(t.grup) >= 0;
      E.aciklama.innerHTML = (eskiT ? '<span class="tablo-ed-eski-rozet">eski</span> ' : "") + kacis(t.aciklama || "") +
        (t.kaynak ? ' <span class="tablo-ed-kaynak">Kaynak: ' + kacis(t.kaynak) + "</span>" : "");
      yenidenHesapla();
      basCiz();
      D.satirH = satirYuksekligi();
      if (!koru) { D.aktif = { r: 0, c: 0 }; D.capa = null; }
      D.pencere = [-1, -1];
      E.izgara.scrollTop = koru ? E.izgara.scrollTop : tdurum(t.ad).kaydir || 0;
      if (!koru) E.izgara.scrollLeft = 0;
      govdeCiz(true);
      toplamCiz();
      yukseklikAyarla();
      govdeCiz(true);
      sayacYaz();
      listeCiz();
      bilgiYaz();
    }
    function sayacYaz() {
      const t = D.tablo;
      if (!t) return;
      const n = t.satirlar.length, g = D.gorunur.length;
      const sel = tdurum(t.ad).secili.size;
      E.sayac.textContent = (g === n ? n + " satır" : g + " / " + n + " satır") + (sel ? " · " + sel + " seçili" : "");
      if (E.uygula) {
        const k = D.duz.sayi();
        E.uygula.disabled = k === 0;
        E.uygula.textContent = k ? "Uygula (" + k + ")" : "Uygula";
        E.geri.disabled = !(D.duz.yigin.length || D.gecmis.length);
      }
    }

    // ------------------------------------------------------------ gövde (sanal kaydırma)
    function satirYuksekligi() {
      const v = parseFloat(getComputedStyle(kok_).getPropertyValue("--tablo-ed-satir"));
      return v > 10 ? v : 30;
    }
    function aralikNorm() {
      const a = D.aktif, c = D.capa || a;
      return { r0: Math.min(a.r, c.r), r1: Math.max(a.r, c.r), c0: Math.min(a.c, c.c), c1: Math.max(a.c, c.c) };
    }
    function hucreHtml(t, ri, r, s, j, vr) {
      const tur = hucreTuru(r, s);
      const duz = !salt && duzenlenebilir(r, s);
      const bek = duz ? D.duz.deger(r.yol[s.ad]) : null;
      const deger = bek ? bek.deger : r.degerler[s.ad];
      const m = bicimle(deger, tur);
      let k = "";
      if (tur.tur === "sayi") k += " tablo-ed-sayi";
      else if (tur.tur === "bool") k += " tablo-ed-bool";
      if (duz) k += " tablo-ed-duz";
      if (bek) k += " tablo-ed-degisti";
      if (dcAsimi(deger, tur)) k += " tablo-ed-dc";
      const a = D.aralik;
      if (vr >= a.r0 && vr <= a.r1 && j >= a.c0 && j <= a.c1 && (a.r1 > a.r0 || a.c1 > a.c0)) k += " tablo-ed-secili";
      if (vr === D.aktif.r && j === D.aktif.c) k += " tablo-ed-aktif";
      const baslik = bek ? ' title="Önceki: ' + kacis(bicimle(bek.ilk, tur)) + ' → yeni: ' + kacis(m) + '"' : (m.length > 18 ? ' title="' + kacis(m) + '"' : "");
      return '<td class="' + k.trim() + '" data-c="' + j + '"' + baslik + (duz && tur.tur === "bool" ? ' aria-checked="' + (deger ? "true" : "false") + '"' : "") + ">" + kacis(m) + "</td>";
    }
    function govdeCiz(zorla) {
      const t = D.tablo;
      if (!t) return;
      const H = D.satirH, n = D.gorunur.length;
      const ust = E.izgara.scrollTop, yuk = E.izgara.clientHeight || 400;
      const ilk = Math.max(0, Math.floor(ust / H) - 8), son = Math.min(n, Math.ceil((ust + yuk) / H) + 8);
      if (!zorla && ilk === D.pencere[0] && son === D.pencere[1]) return;
      D.pencere = [ilk, son];
      D.aralik = aralikNorm();
      const ss = sutunlar(), secili = tdurum(t.ad).secili;
      const kolon = ss.length + 1;
      let h = ilk > 0 ? '<tr class="tablo-ed-bosluk" aria-hidden="true"><td colspan="' + kolon + '" style="height:' + (ilk * H) + 'px"></td></tr>' : "";
      for (let vr = ilk; vr < son; vr++) {
        const ri = D.gorunur[vr], r = t.satirlar[ri];
        h += '<tr data-r="' + vr + '" aria-rowindex="' + (vr + 3) + '" class="' + (r.ozet ? "tablo-ed-ozet" : "") + (secili.has(ri) ? " tablo-ed-satir-secili" : "") +
          (vr % 2 ? " tablo-ed-cift" : "") + '"><th class="tablo-ed-no" scope="row" data-satir="' + vr + '">' + (r.ozet ? "Σ" : ri + 1) + "</th>";
        for (let j = 0; j < ss.length; j++) h += hucreHtml(t, ri, r, ss[j], j, vr);
        h += "</tr>";
      }
      if (son < n) h += '<tr class="tablo-ed-bosluk" aria-hidden="true"><td colspan="' + kolon + '" style="height:' + ((n - son) * H) + 'px"></td></tr>';
      if (!n) h = '<tr><td colspan="' + kolon + '" class="tablo-ed-bos">' + (t.satirlar.length ? "Süzgeçlere uyan satır yok." : "Bu tabloda satır yok.") + "</td></tr>";
      E.tbody.innerHTML = h;
      E.tablo.setAttribute("aria-rowcount", String(n + 2));
      if (D.editor) editorYerlestir();
    }
    function toplamCiz() {
      const t = D.tablo;
      if (!t || !t.toplam || !Object.keys(t.toplam).length || !D.gorunur.length) { E.tfoot.innerHTML = ""; return; }
      const sz = tdurum(t.ad).suzgec;
      const tumu = !Object.keys(sz).some(function (a) { return String(sz[a] || "").trim(); });
      const top = tumu ? t.toplam : toplamHesapla(t, D.gorunur);
      let h = '<tr class="tablo-ed-toplam"><th class="tablo-ed-no" scope="row" title="' + (tumu ? "Toplam" : "Görünen (süzülen) satırların toplamı") + '">Σ</th>';
      let etiket = false;      // etiket, toplamı olmayan ilk geniş metin sütununa (yoksa yalnız Σ)
      sutunlar().forEach(function (s) {
        if (Object.prototype.hasOwnProperty.call(top, s.ad)) h += '<td class="tablo-ed-sayi">' + kacis(bicimle(top[s.ad], s)) + "</td>";
        else if (!etiket && s.tur === "metin" && (s._gen || 0) >= 76) { etiket = true; h += "<td>" + (tumu ? "Toplam" : "Σ süzülen") + "</td>"; }
        else h += "<td></td>";
      });
      E.tfoot.innerHTML = h + "</tr>";
    }
    /** Az satırlı tabloda ızgara içerik kadar kısalır (CSS yüksekliği üst sınırdır). */
    function yukseklikAyarla() {
      E.izgara.style.height = "";
      const enFazla = E.izgara.clientHeight;
      const icerik = (E.thead.offsetHeight || 0) + Math.max(1, D.gorunur.length) * D.satirH + (E.tfoot.offsetHeight || 0) + 18;
      if (icerik < enFazla) E.izgara.style.height = Math.max(icerik, 150) + "px";
    }
    function tazele() { yenidenHesapla(); D.pencere = [-1, -1]; govdeCiz(true); toplamCiz(); yukseklikAyarla(); sayacYaz(); bilgiYaz(); }

    // ------------------------------------------------------------ etkin hücre
    function hucreBul(vr, c) {
      const tr = E.tbody.querySelector('tr[data-r="' + vr + '"]');
      return tr ? tr.querySelector('td[data-c="' + c + '"]') : null;
    }
    function etkinSatir() { return D.tablo ? D.tablo.satirlar[D.gorunur[D.aktif.r]] : null; }
    function bilgiYaz() {
      const t = D.tablo, r = etkinSatir(), s = sutunlar()[D.aktif.c];
      if (!t || !r || !s) { E.bilgi.textContent = ""; return; }
      const duz = !salt && duzenlenebilir(r, s);
      const a = aralikNorm();
      const boyut = (a.r1 - a.r0 + 1) + " × " + (a.c1 - a.c0 + 1);
      E.bilgi.innerHTML = "<b>" + kacis(r.ozet ? "Σ" : "Satır " + (D.gorunur[D.aktif.r] + 1)) + " · " + kacis(baslikMetni(s)) + "</b>" +
        (boyut !== "1 × 1" ? " · seçim " + boyut : "") +
        (duz ? ' · <span class="tablo-ed-yol" title="Bina JSON yolu">✎ ' + kacis(yolMetni(r.yol[s.ad])) + "</span>" : (salt ? "" : " · salt okunur"));
    }
    function gorunurYap() {
      const H = D.satirH, iz = E.izgara;
      const ustBas = E.thead.offsetHeight || 0, altTop = E.tfoot.offsetHeight || 0;
      const y = D.aktif.r * H;
      if (y < iz.scrollTop) iz.scrollTop = y;
      else if (y + H > iz.scrollTop + iz.clientHeight - ustBas - altTop) iz.scrollTop = y + H - iz.clientHeight + ustBas + altTop;
      govdeCiz(false);
      const td = hucreBul(D.aktif.r, D.aktif.c);
      if (td) {
        const noG = 52, sol = td.offsetLeft, sag = sol + td.offsetWidth;
        if (sol - noG < iz.scrollLeft) iz.scrollLeft = Math.max(0, sol - noG);
        else if (sag > iz.scrollLeft + iz.clientWidth) iz.scrollLeft = sag - iz.clientWidth;
      }
    }
    /** Etkin hücre ve aralık sınıflarını çizilmiş hücrelerde günceller (DOM yeniden kurulmaz: tıklama/çift tıklama korunur). */
    function secimBoya() {
      const a = D.aralik = aralikNorm();
      const coklu = a.r1 > a.r0 || a.c1 > a.c0;
      const secili = D.tablo ? tdurum(D.tablo.ad).secili : new Set();
      E.tbody.querySelectorAll("tr[data-r]").forEach(function (tr) {
        const vr = +tr.dataset.r;
        tr.classList.toggle("tablo-ed-satir-secili", secili.has(D.gorunur[vr]));
        const icinde = vr >= a.r0 && vr <= a.r1;
        for (let k = 1; k < tr.children.length; k++) {
          const td = tr.children[k], j = k - 1;
          td.classList.toggle("tablo-ed-secili", coklu && icinde && j >= a.c0 && j <= a.c1);
          td.classList.toggle("tablo-ed-aktif", vr === D.aktif.r && j === D.aktif.c);
        }
      });
    }
    function etkinYap(r, c, genislet) {
      const n = D.gorunur.length, m = sutunlar().length;
      if (!n || !m) return;
      r = Math.max(0, Math.min(n - 1, r));
      c = Math.max(0, Math.min(m - 1, c));
      if (genislet) { if (!D.capa) D.capa = { r: D.aktif.r, c: D.aktif.c }; }
      else D.capa = null;
      D.aktif = { r: r, c: c };
      gorunurYap();
      secimBoya();
      bilgiYaz();
    }

    // ------------------------------------------------------------ düzenleme
    function degisiklikEkle(liste) {
      const n = D.duz.ekle(liste.map(function (d) { return Object.assign({ tablo: D.ad }, d); }));
      govdeCiz(true);
      sayacYaz();
      listeCiz();
      return n;
    }
    function hucreYaz(vr, c, metinYaDaDeger, hamDeger) {
      const t = D.tablo, ri = D.gorunur[vr], r = t.satirlar[ri], s = sutunlar()[c];
      if (!duzenlenebilir(r, s)) return false;
      const tur = hucreTuru(r, s);
      let deger;
      if (hamDeger) deger = metinYaDaDeger;
      else {
        const cv = degerCevir(metinYaDaDeger, tur);
        if (cv.hata) { mesaj(s.baslik + ": " + cv.hata, "hata"); return false; }
        deger = cv.deger;
      }
      const d = { satir: ri, sutun: s.ad, yol: r.yol[s.ad], deger: deger, ilk: r.degerler[s.ad] };
      if (r.bag && r.bag[s.ad]) d.bag = r.bag[s.ad];
      degisiklikEkle([d]);
      mesaj("");
      return true;
    }
    function editorAc(ilkMetin) {
      if (salt) return;
      const r = etkinSatir(), s = sutunlar()[D.aktif.c];
      if (!r || !s) return;
      if (!duzenlenebilir(r, s)) { mesaj("Bu hücre salt okunur (hesaplanan değer ya da modelde karşılığı yok).", "bilgi"); return; }
      const tur = hucreTuru(r, s);
      const bek = D.duz.deger(r.yol[s.ad]);
      const deger = bek ? bek.deger : r.degerler[s.ad];
      if (tur.tur === "bool") { hucreYaz(D.aktif.r, D.aktif.c, !deger, true); return; }
      editorKapat(false);
      let el;
      if (tur.tur === "secim") {
        el = document.createElement("select");
        let h = "";
        const sec_ = tur.secenekler || [];
        const bosVar = sec_.some(function (o) { const d = secenekDeger(o); return d === null || d === ""; });
        if (tur.bos_olur && !bosVar) h += '<option value="-1">(boş)</option>';
        let secili = -1;
        sec_.forEach(function (o, i) { if (esit(secenekDeger(o), deger)) secili = i; h += '<option value="' + i + '">' + kacis(secenekEtiket(o) || "(boş)") + "</option>"; });
        if (secili < 0 && deger !== null && deger !== undefined && deger !== "") { h = '<option value="-2" selected>' + kacis(String(deger)) + " (listede yok)</option>" + h; }
        el.innerHTML = h;
        if (secili >= 0) el.value = String(secili);
        else if (deger === null || deger === undefined) el.value = "-1";
        el.addEventListener("change", function () { editorKapat(true); });
      } else {
        el = document.createElement("input");
        el.type = "text";
        el.spellcheck = false;
        el.autocomplete = "off";
        if (tur.tur === "sayi") el.inputMode = "decimal";
        el.value = ilkMetin !== undefined ? ilkMetin : (typeof deger === "number" ? String(deger) : (deger === null || deger === undefined ? "" : String(deger)));
      }
      el.className = "tablo-ed-editor";
      el.setAttribute("aria-label", s.baslik + " düzenle");
      D.editor = { el: el, vr: D.aktif.r, c: D.aktif.c, tur: tur };
      E.izgara.appendChild(el);
      editorYerlestir();
      el.addEventListener("keydown", editorTus);
      el.addEventListener("blur", function () { setTimeout(function () { if (D.editor && D.editor.el === el) editorKapat(true, true); }, 0); });
      el.focus();
      if (el.select && ilkMetin === undefined) el.select();
      else if (el.setSelectionRange) el.setSelectionRange(el.value.length, el.value.length);
    }
    function editorYerlestir() {
      const ed = D.editor;
      if (!ed) return;
      const td = hucreBul(ed.vr, ed.c);
      if (!td) { ed.el.style.visibility = "hidden"; return; }
      ed.el.style.visibility = "";
      const ir = E.izgara.getBoundingClientRect(), tr = td.getBoundingClientRect();
      ed.el.style.top = (tr.top - ir.top + E.izgara.scrollTop) + "px";
      ed.el.style.left = (tr.left - ir.left + E.izgara.scrollLeft) + "px";
      ed.el.style.width = Math.max(tr.width, ed.tur.tur === "secim" ? 140 : 80) + "px";
      ed.el.style.height = tr.height + "px";
    }
    function editorKapat(kaydet, bulanik) {
      const ed = D.editor;
      if (!ed) return true;
      let tamam = true;
      if (kaydet) {
        if (ed.tur.tur === "secim") {
          const i = +ed.el.value;
          if (i !== -2) {
            const sec_ = ed.tur.secenekler || [];
            const deger = i === -1 ? null : secenekDeger(sec_[i]);
            tamam = hucreYaz(ed.vr, ed.c, deger, true);
          }
        } else {
          tamam = hucreYaz(ed.vr, ed.c, ed.el.value, false);
          if (!tamam && !bulanik) { ed.el.classList.add("hata"); ed.el.focus(); return false; }
        }
      }
      D.editor = null;
      ed.el.remove();
      if (!bulanik) E.izgara.focus({ preventScroll: true });
      govdeCiz(true);
      return tamam;
    }
    function editorTus(e) {
      const ed = D.editor;
      if (!ed) return;
      if (e.key === "Escape") { e.preventDefault(); editorKapat(false); return; }
      if (e.key === "Enter") {
        e.preventDefault();
        if (editorKapat(true)) etkinYap(D.aktif.r + (e.shiftKey ? -1 : 1), D.aktif.c, false);
        return;
      }
      if (e.key === "Tab") {
        e.preventDefault();
        if (editorKapat(true)) etkinYap(D.aktif.r, D.aktif.c + (e.shiftKey ? -1 : 1), false);
      }
    }
    function secimiTemizle() {
      if (salt) return;
      const a = aralikNorm(), liste = [];
      let atla = 0;
      for (let vr = a.r0; vr <= a.r1; vr++) {
        for (let c = a.c0; c <= a.c1; c++) {
          const r = D.tablo.satirlar[D.gorunur[vr]], s = sutunlar()[c];
          if (!r || !duzenlenebilir(r, s)) continue;
          const tur = hucreTuru(r, s);
          let deger;
          if (tur.tur === "metin") deger = tur.bos_olur ? null : "";
          else if (tur.bos_olur) deger = null;
          else if (tur.tur === "secim" && (tur.secenekler || []).some(function (o) { return secenekDeger(o) === null; })) deger = null;
          else { atla++; continue; }
          const d = { satir: D.gorunur[vr], sutun: s.ad, yol: r.yol[s.ad], deger: deger, ilk: r.degerler[s.ad] };
          if (r.bag && r.bag[s.ad]) d.bag = r.bag[s.ad];
          liste.push(d);
        }
      }
      if (liste.length) degisiklikEkle(liste);
      if (atla) mesaj(atla + " hücre boş bırakılamaz (zorunlu değer).", "bilgi");
    }
    function yapistirMetin(metin) {
      if (salt || !D.tablo) return;
      const matris = tsvAyristir(metin);
      if (!matris.length) { mesaj("Yapıştırılacak hücre yok.", "bilgi"); return; }
      const a = aralikNorm();
      const plan = yapistirmaPlani(D.tablo, D.gorunur, sutunlar(), a.r0, a.c0, matris, a);
      if (plan.degisiklikler.length) degisiklikEkle(plan.degisiklikler);
      const parca = [plan.degisiklikler.length + " hücre yazıldı"];
      if (plan.atlanan) parca.push(plan.atlanan + " hücre atlandı (salt okunur ya da tablo dışında)");
      if (plan.hatalar.length) parca.push(plan.hatalar.length + " hata: " + plan.hatalar.slice(0, 3).join("; ") + (plan.hatalar.length > 3 ? "…" : ""));
      mesaj(parca.join(" · ") + ".", plan.hatalar.length ? "hata" : "tamam");
      if (matris.length > 1 || (matris[0] && matris[0].length > 1)) {
        D.capa = { r: a.r0, c: a.c0 };
        D.aktif = { r: Math.min(D.gorunur.length - 1, a.r0 + matris.length - 1), c: Math.min(sutunlar().length - 1, a.c0 + Math.max.apply(null, matris.map(function (x) { return x.length; })) - 1) };
        secimBoya();
        bilgiYaz();
      }
    }
    function secimTsv() {
      const a = aralikNorm(), t = D.tablo, ss = sutunlar(), m = [];
      for (let vr = a.r0; vr <= a.r1; vr++) {
        const r = t.satirlar[D.gorunur[vr]];
        if (!r) continue;
        const sat = [];
        for (let c = a.c0; c <= a.c1; c++) {
          const s = ss[c], tur = hucreTuru(r, s);
          const bek = !salt && duzenlenebilir(r, s) ? D.duz.deger(r.yol[s.ad]) : null;
          sat.push(disaDeger(bek ? bek.deger : r.degerler[s.ad], tur, !!D.csv.ondalikVirgul));
        }
        m.push(sat);
      }
      return tsvUret(m);
    }
    function uygula() {
      if (D.editor) editorKapat(true, true);
      if (salt || !D.duz.sayi()) return;
      const degisiklikler = D.duz.degisiklikler();
      let yeni;
      try {
        yeni = degisiklikleriUygula(D.bina || {}, degisiklikler);
      } catch (e) {
        mesaj("Değişiklikler uygulanamadı: " + (e && e.message ? e.message : e), "hata");
        return;
      }
      const onceki = kopya(D.bina || {});
      let sonuc;
      try {
        sonuc = sec.duzenle(yeni, kopya(degisiklikler), { geriAl: false });
      } catch (e) {
        mesaj("Model değişikliği reddedildi: " + (e && e.message ? e.message : e), "hata");
        return;
      }
      const yama = new Map();
      D.duz.bekleyen.forEach(function (e, k) { yama.set(k, e.deger); });
      const bitir = function () {
        D.gecmis.push(onceki);
        if (D.gecmis.length > 20) D.gecmis.shift();
        D.bina = yeni;
        const n = degisiklikler.length;
        // tablolar yenilenene kadar uygulanan değerler aynı alanı gösteren bütün hücrelerde görünsün (iyimser yama)
        D.tablolar.forEach(function (t) {
          (t.satirlar || []).forEach(function (r) {
            if (!r.yol) return;
            Object.keys(r.yol).forEach(function (a) { const k = Duzenleme.anahtar(r.yol[a]); if (yama.has(k)) r.degerler[a] = kopya(yama.get(k)); });
          });
        });
        // yeniden adlandırılan aks/sistemin {"ad": eski} seçicilerini yeni adla değiştir (tablolar yenilenmeden yapılan düzenlemeler için)
        degisiklikler.forEach(function (d) { if (d.bag) yolAdiniGuncelle(d.yol, d.deger); });
        D.duz.temizle();
        if (D.cozumlu) { D.eski = true; uyariYaz(); }
        tazele();
        listeCiz();
        mesaj(n + " değişiklik modele uygulandı." + (D.cozumlu ? " Sonuçlar için modeli yeniden çözün." : ""), "tamam");
      };
      if (sonuc && typeof sonuc.then === "function") {
        E.uygula.disabled = true;
        sonuc.then(bitir, function (e) { sayacYaz(); mesaj("Model değişikliği reddedildi: " + (e && e.message ? e.message : e), "hata"); });
      } else bitir();
    }
    function yolAdiniGuncelle(yol, yeni) {
      const onEk = yol.slice(0, -2), sec_ = yol[yol.length - 2];
      if (!nesneMi(sec_) || sec_.ad === undefined) return;
      const duzelt = function (y) {
        if (!Array.isArray(y) || y.length <= onEk.length || !onEk.every(function (p, i) { return esit(p, y[i]); })) return y;
        const p = y[onEk.length];
        if (!nesneMi(p) || !esit(p.ad, sec_.ad)) return y;
        const z = y.slice();
        z[onEk.length] = Object.assign({}, p, { ad: yeni });
        return z;
      };
      D.tablolar.forEach(function (t) {
        (t.satirlar || []).forEach(function (r) {
          if (!r.yol) return;
          Object.keys(r.yol).forEach(function (a) { r.yol[a] = cokluYol(r.yol[a]) ? r.yol[a].map(duzelt) : duzelt(r.yol[a]); });
        });
      });
    }
    function geriAl() {
      if (salt) return;
      if (D.editor) { editorKapat(false); return; }
      if (D.duz.geriAl()) { govdeCiz(true); sayacYaz(); listeCiz(); mesaj("Son düzenleme geri alındı.", "bilgi"); return; }
      const onceki = D.gecmis.pop();
      if (!onceki) return;
      let sonuc;
      try { sonuc = sec.duzenle(kopya(onceki), [], { geriAl: true }); } catch (e) { D.gecmis.push(onceki); mesaj("Geri alınamadı: " + e.message, "hata"); return; }
      const bitir = function () { D.bina = onceki; if (D.cozumlu) { D.eski = true; uyariYaz(); } tazele(); mesaj("Uygulanmış son düzenleme geri alındı (model önceki hâline döndü).", "bilgi"); };
      if (sonuc && typeof sonuc.then === "function") sonuc.then(bitir, function (e) { D.gecmis.push(onceki); mesaj("Geri alınamadı: " + (e && e.message), "hata"); });
      else bitir();
    }
    function uyariYaz() {
      if (D.eski) {
        E.uyari.hidden = false;
        E.uyari.innerHTML = "Model değişti: <b>Analiz, Tasarım</b> ve deprem/temel hesap satırları yeniden çözülene kadar eski sonuçları gösterir. Model, yük ve metraj tabloları güncel modelden yenilenir.";
      } else { E.uyari.hidden = true; E.uyari.innerHTML = ""; }
    }

    // ------------------------------------------------------------ CSV / pano
    function csvSec() { return { ayirici: D.csv.ayirici, ondalikVirgul: !!D.csv.ondalikVirgul }; }
    function onEk() { return sec.dosyaOnEki ? dosyaAdi(sec.dosyaOnEki) + "_" : ""; }
    function csvIslem(tur) {
      const t = D.tablo;
      if (tur === "bu" && t) indir(onEk() + dosyaAdi(t.ad) + ".csv", csvUret(t, Object.assign(csvSec(), { idx: D.gorunur.length === t.satirlar.length ? null : D.gorunur })));
      else if (tur === "rapor") {
        const liste = D.tablolar.filter(function (x) { return D.rapor.has(x.ad); });
        if (!liste.length) { mesaj("Rapora seçilmiş tablo yok (soldaki onay kutuları).", "bilgi"); return; }
        indir(onEk() + "rapor_tablolari.csv", tumunuCsv(liste, csvSec()));
      } else if (tur === "tek") indir(onEk() + "tablolar.csv", tumunuCsv(D.tablolar, csvSec()));
      else if (tur === "ayri") {
        D.tablolar.forEach(function (x, i) { setTimeout(function () { indir(onEk() + dosyaAdi(x.ad) + ".csv", csvUret(x, csvSec())); }, i * 250); });
        mesaj(D.tablolar.length + " CSV dosyası indiriliyor (tarayıcı çoklu indirme izni isteyebilir).", "bilgi");
      } else if (tur === "kopyala" && t) {
        const ss = sutunlar();
        const m = [ss.map(baslikMetni)].concat(D.gorunur.map(function (i) {
          const r = t.satirlar[i];
          return ss.map(function (s) { return disaDeger(r.degerler[s.ad], hucreTuru(r, s), !!D.csv.ondalikVirgul); });
        }));
        const metin = tsvUret(m);
        const yaz = kok.navigator && kok.navigator.clipboard && kok.navigator.clipboard.writeText;
        if (yaz) kok.navigator.clipboard.writeText(metin).then(function () { mesaj(D.gorunur.length + " satır panoya kopyalandı.", "tamam"); }, function () { mesaj("Pano izni yok; CSV indirin.", "hata"); });
        else mesaj("Pano kullanılamıyor; CSV indirin.", "hata");
      }
    }

    // ------------------------------------------------------------ olaylar
    const dinleyiciler = [];
    function dinle(el, ad, fn, op) { el.addEventListener(ad, fn, op); dinleyiciler.push([el, ad, fn, op]); }

    dinle(E.gruplar, "click", function (e) {
      const k = e.target.closest(".tablo-ed-oge-rapor");
      if (k) {
        const ad = k.closest(".tablo-ed-oge").dataset.ad;
        if (k.checked) D.rapor.add(ad); else D.rapor.delete(ad);
        raporBildir();
        listeCiz();
        return;
      }
      const g = e.target.closest(".tablo-ed-grup-rapor");
      if (g) {
        e.preventDefault();
        const det = g.closest(".tablo-ed-grup");
        const adlar = Array.from(det.querySelectorAll(".tablo-ed-oge")).map(function (li) { return li.dataset.ad; });
        const hepsi = adlar.every(function (a) { return D.rapor.has(a); });
        adlar.forEach(function (a) { if (hepsi) D.rapor.delete(a); else D.rapor.add(a); });
        raporBildir();
        listeCiz();
        return;
      }
      const b = e.target.closest(".tablo-ed-oge-d");
      if (b) sec_(b.closest(".tablo-ed-oge").dataset.ad);
    });
    dinle(E.gruplar, "toggle", function (e) {
      const det = e.target;
      if (!det.classList || !det.classList.contains("tablo-ed-grup") || D.liste) return;
      if (det.open) D.kapali.delete(det.dataset.grup); else D.kapali.add(det.dataset.grup);
      depoYaz("kapali-gruplar", Array.from(D.kapali));
    }, true);
    dinle(E.ara, "input", function () { D.liste = E.ara.value; listeCiz(); });
    dinle($(".tablo-ed-rapor-hepsi"), "click", function () { D.tablolar.forEach(function (t) { D.rapor.add(t.ad); }); raporBildir(); listeCiz(); });
    dinle($(".tablo-ed-rapor-hic"), "click", function () { D.rapor.clear(); raporBildir(); listeCiz(); });
    dinle(E.mliste, "change", function () { sec_(E.mliste.value); });
    dinle(E.mrapor, "change", function () { if (!D.ad) return; if (E.mrapor.checked) D.rapor.add(D.ad); else D.rapor.delete(D.ad); raporBildir(); listeCiz(); });
    dinle(E.raporSuz, "change", function () { D.raporSuz = E.raporSuz.checked; depoYaz("rapor-suz", D.raporSuz); });
    if (E.uygula) {
      dinle(E.uygula, "click", uygula);
      dinle(E.geri, "click", geriAl);
      dinle(E.yapistir, "click", function () {
        E.yapKutu.hidden = false;
        E.yapMetin.value = "";
        E.yapMetin.focus();
      });
    }
    dinle(E.yapKutu, "click", function (e) {
      const b = e.target.closest("[data-yap]");
      if (!b) return;
      E.yapKutu.hidden = true;
      if (b.dataset.yap === "tamam") yapistirMetin(E.yapMetin.value);
      E.izgara.focus({ preventScroll: true });
    });
    dinle(E.yapKutu, "keydown", function (e) { if (e.key === "Escape") { E.yapKutu.hidden = true; E.izgara.focus({ preventScroll: true }); } });
    dinle(E.temizle, "click", function () {
      if (!D.tablo) return;
      const d = tdurum(D.tablo.ad);
      d.suzgec = {}; d.sira = { sutun: null, yon: null }; d.secili.clear();
      basCiz(); tazele();
    });
    dinle(E.csvD, "click", function () {
      const acik = E.csvMenu.hidden;
      E.csvMenu.hidden = !acik;
      E.csvD.setAttribute("aria-expanded", acik ? "true" : "false");
    });
    dinle(E.csvMenu, "click", function (e) {
      const b = e.target.closest("[data-csv]");
      if (b) { E.csvMenu.hidden = true; E.csvD.setAttribute("aria-expanded", "false"); csvIslem(b.dataset.csv); }
    });
    dinle(E.csvMenu, "change", function (e) {
      const k = e.target.closest("[data-ayar]");
      if (!k) return;
      if (k.dataset.ayar === "ondalikVirgul") D.csv.ondalikVirgul = k.checked;
      else D.csv.ayirici = k.checked ? "," : ";";
      if (D.csv.ayirici === "," && D.csv.ondalikVirgul) mesaj("Uyarı: virgül hem ayırıcı hem ondalık; sayılar tırnak içinde yazılır.", "bilgi");
      depoYaz("csv", D.csv);
    });
    const disTik = function (e) { if (!e.target.closest(".tablo-ed-menu")) { E.csvMenu.hidden = true; E.csvD.setAttribute("aria-expanded", "false"); } };
    dinle(document, "click", disTik);
    if (sec.kapat) dinle($(".tablo-ed-kapat"), "click", function () { sec.kapat(); });

    // başlık: sıralama ve süzgeç
    dinle(E.thead, "click", function (e) {
      const b = e.target.closest(".tablo-ed-sirala");
      if (!b || !D.tablo) return;
      const s = sutunlar()[+b.dataset.c], d = tdurum(D.tablo.ad);
      if (d.sira.sutun !== s.ad) d.sira = { sutun: s.ad, yon: "artan" };
      else if (d.sira.yon === "artan") d.sira.yon = "azalan";
      else d.sira = { sutun: null, yon: null };
      editorKapat(false);
      basCiz(); tazele();
    });
    let suzZaman = null;
    dinle(E.thead, "input", function (e) {
      const k = e.target.closest(".tablo-ed-suz");
      if (!k || !D.tablo) return;
      const s = sutunlar()[+k.dataset.c], d = tdurum(D.tablo.ad);
      if (k.value.trim()) d.suzgec[s.ad] = k.value; else delete d.suzgec[s.ad];
      k.classList.toggle("dolu", !!k.value.trim());
      clearTimeout(suzZaman);
      suzZaman = setTimeout(function () { D.aktif = { r: 0, c: D.aktif.c }; D.capa = null; E.izgara.scrollTop = 0; tazele(); }, 140);
    });
    dinle(E.thead, "keydown", function (e) {
      const k = e.target.closest(".tablo-ed-suz");
      if (k && (e.key === "Enter" || e.key === "ArrowDown")) { e.preventDefault(); E.izgara.focus({ preventScroll: true }); etkinYap(0, +k.dataset.c, false); }
      if (k && e.key === "Escape") { k.value = ""; k.dispatchEvent(new Event("input", { bubbles: true })); }
    });

    // gövde: fare/dokunma
    let surukle = false;
    dinle(E.izgara, "scroll", function () {
      if (D._kaydirIstek) return;
      D._kaydirIstek = true;
      (kok.requestAnimationFrame || setTimeout)(function () { D._kaydirIstek = false; govdeCiz(false); });
    }, { passive: true });
    dinle(E.tbody, "pointerdown", function (e) {
      if (e.button !== 0 && e.pointerType === "mouse") return;
      const no = e.target.closest("th[data-satir]");
      if (no && D.tablo) {
        const vr = +no.dataset.satir, ri = D.gorunur[vr], secili = tdurum(D.tablo.ad).secili;
        if (e.shiftKey && D._sonSatir !== undefined) {
          const a = Math.min(D._sonSatir, vr), b = Math.max(D._sonSatir, vr);
          for (let i = a; i <= b; i++) secili.add(D.gorunur[i]);
        } else if (e.ctrlKey || e.metaKey || e.pointerType !== "mouse") {
          if (secili.has(ri)) secili.delete(ri); else secili.add(ri);
        } else {
          const tek = secili.size === 1 && secili.has(ri);
          secili.clear();
          if (!tek) secili.add(ri);
        }
        D._sonSatir = vr;
        D.capa = { r: vr, c: 0 }; D.aktif = { r: vr, c: sutunlar().length - 1 };
        secimBoya(); sayacYaz(); bilgiYaz();
        return;
      }
      const td = e.target.closest("td[data-c]");
      if (!td) return;
      const tr = td.closest("tr[data-r]");
      if (!tr) return;
      const vr = +tr.dataset.r, c = +td.dataset.c;
      if (D.editor) editorKapat(true, true);
      const ayni = D.aktif.r === vr && D.aktif.c === c && !D.capa;
      const simdi = Date.now();
      const cift = ayni && D._sonTik && simdi - D._sonTik < 450;
      D._sonTik = simdi;
      etkinYap(vr, c, e.shiftKey);
      if (e.pointerType === "mouse" && !e.shiftKey) surukle = true;
      E.izgara.focus({ preventScroll: true });
      // etkin hücreye ikinci tıklama: evet/hayır hücresi değişir; çift tıklama (fare) ya da ikinci dokunuş (dokunmatik) düzenler
      if (salt || !ayni) return;
      const r = etkinSatir(), s = sutunlar()[c];
      if (!r || !s || !duzenlenebilir(r, s)) return;
      if (hucreTuru(r, s).tur === "bool" || cift || e.pointerType !== "mouse") { e.preventDefault(); D._sonTik = 0; editorAc(); }
    });
    dinle(E.tbody, "pointermove", function (e) {
      if (!surukle) return;
      const td = e.target.closest("td[data-c]"), tr = td && td.closest("tr[data-r]");
      if (!tr) return;
      const vr = +tr.dataset.r, c = +td.dataset.c;
      if (vr !== D.aktif.r || c !== D.aktif.c) {
        if (!D.capa) D.capa = { r: D.aktif.r, c: D.aktif.c };
        D.aktif = { r: vr, c: c };
        secimBoya(); bilgiYaz();
      }
    });
    dinle(document, "pointerup", function () { surukle = false; });

    // klavye
    dinle(E.izgara, "keydown", function (e) {
      if (D.editor || e.target !== E.izgara) return;
      const n = D.gorunur.length, m = sutunlar().length;
      if (!n || !m) return;
      const a = D.aktif, sayfa = Math.max(1, Math.floor((E.izgara.clientHeight - 90) / D.satirH));
      const ctrl = e.ctrlKey || e.metaKey;
      let r = a.r, c = a.c, islem = true;
      switch (e.key) {
        case "ArrowUp": r = ctrl ? 0 : r - 1; break;
        case "ArrowDown": r = ctrl ? n - 1 : r + 1; break;
        case "ArrowLeft": c = ctrl ? 0 : c - 1; break;
        case "ArrowRight": c = ctrl ? m - 1 : c + 1; break;
        case "Home": c = 0; if (ctrl) r = 0; break;
        case "End": c = m - 1; if (ctrl) r = n - 1; break;
        case "PageUp": r -= sayfa; break;
        case "PageDown": r += sayfa; break;
        case "Tab": c += e.shiftKey ? -1 : 1; if (c >= m) { c = 0; r++; } if (c < 0) { c = m - 1; r--; } break;
        default: islem = false;
      }
      if (islem) {
        if (e.key === "Tab" && ((c === a.c && r === a.r) || r < 0 || r >= n)) return;     // tablonun sonunda odak dışarı çıkabilir
        e.preventDefault();
        etkinYap(r, c, e.shiftKey && e.key !== "Tab");
        return;
      }
      if (ctrl && e.key === "Enter") { e.preventDefault(); uygula(); return; }
      if (e.key === "Enter" || e.key === "F2") { e.preventDefault(); editorAc(); return; }
      if (e.key === " ") {
        const rr = etkinSatir(), s = sutunlar()[a.c];
        if (rr && s && hucreTuru(rr, s).tur === "bool") { e.preventDefault(); editorAc(); }
        return;
      }
      if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); secimiTemizle(); return; }
      if (e.key === "Escape") { D.capa = null; secimBoya(); bilgiYaz(); return; }
      if (ctrl && (e.key === "z" || e.key === "Z")) { e.preventDefault(); geriAl(); return; }
      if (ctrl && (e.key === "a" || e.key === "A")) { e.preventDefault(); D.capa = { r: 0, c: 0 }; D.aktif = { r: n - 1, c: m - 1 }; secimBoya(); bilgiYaz(); return; }
      if (!ctrl && !e.altKey && e.key.length === 1 && !salt) {
        const rr = etkinSatir(), s = sutunlar()[a.c];
        if (rr && s && duzenlenebilir(rr, s)) {
          const tur = hucreTuru(rr, s);
          e.preventDefault();
          if (tur.tur === "secim" || tur.tur === "bool") editorAc(); else editorAc(e.key);
        }
      }
    });
    const girdiMi = function (el) { return !!(el && el.closest && el.closest("input, select, textarea")); };
    dinle(E.izgara, "copy", function (e) {
      if (D.editor || girdiMi(e.target) || !D.tablo || !D.gorunur.length) return;
      e.preventDefault();
      e.clipboardData.setData("text/plain", secimTsv());
      const a = aralikNorm();
      mesaj((a.r1 - a.r0 + 1) * (a.c1 - a.c0 + 1) + " hücre kopyalandı.", "bilgi");
    });
    dinle(E.izgara, "paste", function (e) {
      if (D.editor || salt || girdiMi(e.target)) return;
      const metin = (e.clipboardData || kok.clipboardData).getData("text");
      e.preventDefault();
      yapistirMetin(metin);
    });
    dinle(E.izgara, "focus", function () { bilgiYaz(); });
    const boyut = function () { D.satirH = satirYuksekligi(); D.pencere = [-1, -1]; govdeCiz(true); };
    dinle(kok, "resize", boyut);

    // ------------------------------------------------------------ başlat
    const ilk = sec.baslangic || depoAl("son", null);
    uyariYaz();
    sec_(D.tablolar.some(function (t) { return t.ad === ilk; }) ? ilk : (D.tablolar[0] || {}).ad);

    return {
      kapat: function () {
        editorKapat(false, true);
        dinleyiciler.forEach(function (d) { d[0].removeEventListener(d[1], d[2], d[3]); });
        kok_.remove();
      },
      guncelle: function (y) {
        y = y || {};
        if (Array.isArray(y.tablolar)) {
          const oncekiCozumlu = D.cozumlu;
          D.tablolar = y.tablolar;
          D.duz.temizle();
          D.durum.forEach(function (d) { d.secili.clear(); });
          D.cozumlu = y.cozumlu !== undefined ? !!y.cozumlu : y.tablolar.some(function (t) { return SONUC_GRUPLARI.indexOf(t.grup) >= 0; });
          D.eski = !!y.eski;
          if (oncekiCozumlu && !D.cozumlu) setTimeout(function () { mesaj("Tablolar güncel modelden yenilendi; Analiz ve Tasarım tabloları için modeli yeniden çözün.", "bilgi"); }, 0);
        }
        if (y.bina !== undefined) D.bina = y.bina;
        if (y.raporSecimi) D.rapor = new Set(Array.from(y.raporSecimi));
        uyariYaz();
        sec_(D.ad, true);
      },
      raporSecimi: function () { return new Set(D.rapor); },
      raporSecenegi: function () {
        const adlar = D.tablolar.filter(function (t) { return D.rapor.has(t.ad); }).map(function (t) { return t.ad; });
        const filtre = {};
        if (D.raporSuz) {
          adlar.forEach(function (ad) {
            const d = D.durum.get(ad), t = D.tablolar.find(function (x) { return x.ad === ad; });
            if (!d || !t) return;
            if (d.secili.size) filtre[ad] = { satirlar: Array.from(d.secili).sort(function (a, b) { return a - b; }) };
            else if (Object.keys(d.suzgec).some(function (a) { return d.suzgec[a]; })) filtre[ad] = { satirlar: suz(t, d.suzgec) };
          });
        }
        return { tablolar: adlar, tablo_filtre: filtre };
      },
      sec: function (ad) { sec_(ad); },
      durum: function () { return { ad: D.ad, bekleyen: D.duz.sayi(), gorunur: D.gorunur.length, eski: D.eski, gecmis: D.gecmis.length }; },
    };
  }

  return { ac: ac, _ic: _ic, surum: "1.0.0" };
});
