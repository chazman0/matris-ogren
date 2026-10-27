/* Matris Öğren — masaüstü köprüsü ve dosya işlemleri (window.MatrisDosya).

   Aynı kod hem web sürümünde hem masaüstü sürümünde çalışır:
   - Masaüstünde (ön yükleme betiği window.masaustu yüzeyini açmışsa) kaydet/aç/PDF işlemleri yerel iletişim
     kutularıyla yapılır, menü komutları ve açılan proje dosyaları sayfaya olay olarak iletilir, servis çalışanı
     kaydedilmez (uygulama zaten yereldir).
   - Web sürümünde: kaydet → Blob indirme, aç → dosya seçici (input[type=file]), PDF → yeni pencerede yazdırma.

   API (hepsi Promise döndürür; kullanıcı vazgeçerse sonuç null):
     MatrisDosya.kaydet(ad, icerik, tur, secenek?)  → {ad, yol?} | null
         icerik: metin | Blob | ArrayBuffer | Uint8Array; tur: "ifc" | "csv" | ".csv" | "text/csv" | ... (yoksa addan);
         tur "matris" = proje dosyası: masaüstünde pencerenin dosyasına doğrudan yazılır (secenek.farkli → iletişim kutusu).
     MatrisDosya.ac(turler?, secenek?)               → {ad, icerik, yol?} | null   (turler: ["matris", "json"] varsayılan;
         secenek.ikili → icerik Uint8Array)
     MatrisDosya.pdfYazdir(html, ad)                 → {ad, yol?} | null
   Yardımcılar: masaustu (bool), degisti(kirli), yeni(), projeKaynagi(fn), klasordeGoster(yol), bekleyenDosya().
   Olaylar (window üzerinde, CustomEvent, iptal edilebilir — işleyen e.preventDefault() çağırır):
     "masaustu-komut"        detail: {komut, ...ek}       (menü ve kısayollar; ör. {komut: "sayfa", sayfa: "bina"})
     "masaustu-dosya-acildi" detail: {ad, icerik, yol?, kurtarma?}   (.matris/.json açıldı: menü, çift tıklama, sürükle-bırak) */
(function () {
  "use strict";

  const M = window.masaustu && typeof window.masaustu.kaydet === "function" ? window.masaustu : null;
  const MASAUSTU = !!M;

  const TURLER = {
    matris: { uzanti: "matris", mime: "application/json", ad: "Matris Öğren projesi" },
    json: { uzanti: "json", mime: "application/json", ad: "JSON verisi" },
    ifc: { uzanti: "ifc", mime: "application/x-step", ad: "IFC yapı modeli" },
    csv: { uzanti: "csv", mime: "text/csv", ad: "CSV tablosu" },
    tsv: { uzanti: "tsv", mime: "text/tab-separated-values", ad: "TSV tablosu" },
    html: { uzanti: "html", mime: "text/html", ad: "HTML belgesi" },
    pdf: { uzanti: "pdf", mime: "application/pdf", ad: "PDF belgesi" },
    txt: { uzanti: "txt", mime: "text/plain", ad: "Metin" },
    md: { uzanti: "md", mime: "text/markdown", ad: "Markdown metni" },
    svg: { uzanti: "svg", mime: "image/svg+xml", ad: "SVG çizimi" },
    png: { uzanti: "png", mime: "image/png", ad: "PNG resmi" },
    dxf: { uzanti: "dxf", mime: "application/dxf", ad: "DXF çizimi" },
  };

  function uzantisi(ad) {
    const m = /\.([A-Za-z0-9]{1,10})$/.exec(String(ad || ""));
    return m ? m[1].toLowerCase() : "";
  }

  // "ifc" | ".ifc" | "text/csv" | undefined (+ dosya adı) → {uzanti, mime, ad}
  function turCoz(tur, ad) {
    const t = String(tur || "").trim().toLowerCase();
    if (t) {
      const anahtar = t.replace(/^\./, "");
      if (TURLER[anahtar]) return TURLER[anahtar];
      const mime = t.split(";")[0];
      for (const k in TURLER) { if (TURLER[k].mime === mime) return TURLER[k]; }
      if (/^[a-z0-9]{1,10}$/.test(anahtar)) return { uzanti: anahtar, mime: "application/octet-stream", ad: anahtar.toUpperCase() + " dosyası" };
    }
    const u = uzantisi(ad);
    if (u && TURLER[u]) return TURLER[u];
    return { uzanti: u, mime: "application/octet-stream", ad: u ? u.toUpperCase() + " dosyası" : "Dosya" };
  }

  function adDuzelt(ad, t) {
    let a = String(ad || "").replace(/[\\/:*?"<>|\u0000-\u001f]+/g, "_").trim() || "dosya";
    if (t.uzanti && uzantisi(a) !== t.uzanti) a += "." + t.uzanti;
    return a;
  }

  function metinMi(t) { return /^text\/|json|xml|svg|x-step|dxf/.test(t.mime); }

  async function ikiliyeCevir(icerik) {
    if (icerik instanceof Blob) return new Uint8Array(await icerik.arrayBuffer());
    if (icerik instanceof ArrayBuffer) return new Uint8Array(icerik);
    if (ArrayBuffer.isView(icerik)) return new Uint8Array(icerik.buffer, icerik.byteOffset, icerik.byteLength);
    return null;
  }

  // ------------------------------------------------------------------ kaydet
  function webIndir(ad, icerik, t) {
    const tur = t.mime + (metinMi(t) && !/charset/.test(t.mime) ? ";charset=utf-8" : "");
    const blob = icerik instanceof Blob ? icerik : new Blob([icerik == null ? "" : icerik], { type: tur });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = ad;
    a.rel = "noopener";
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 4000);
    return { ad: ad };
  }

  async function kaydet(ad, icerik, tur, secenek) {
    const s = secenek || {};
    const t = turCoz(tur, ad);
    const dosyaAdi = adDuzelt(ad, t);
    if (!MASAUSTU) return webIndir(dosyaAdi, icerik, t);
    if (t.uzanti === "matris") {
      const metin = typeof icerik === "string" ? icerik : new TextDecoder().decode(await ikiliyeCevir(icerik) || new Uint8Array());
      const r = await M.projeKaydet({ ad: dosyaAdi, icerik: metin, farkli: !!s.farkli });
      if (r) kirli = false;
      return r || null;
    }
    const ikili = await ikiliyeCevir(icerik);
    return (await M.kaydet({
      ad: dosyaAdi, icerik: ikili || String(icerik == null ? "" : icerik), baslik: s.baslik || "",
      filtreler: t.uzanti ? [{ ad: t.ad, uzantilar: [t.uzanti] }] : [],
    })) || null;
  }

  // ------------------------------------------------------------------ aç
  function turListesi(turler) {
    let liste = turler;
    if (typeof liste === "string") liste = liste.split(",");
    if (!Array.isArray(liste) || !liste.length) liste = ["matris", "json"];
    return liste.map(function (x) { return turCoz(x, ""); }).filter(function (t) { return t.uzanti; });
  }

  function webAc(liste, ikili) {
    return new Promise(function (coz, reddet) {
      const girdi = document.createElement("input");
      girdi.type = "file";
      girdi.accept = liste.map(function (t) { return "." + t.uzanti; }).join(",");
      girdi.style.display = "none";
      let bitti = false;
      const son = function (deger, hata) {
        if (bitti) return;
        bitti = true;
        girdi.remove();
        if (hata) reddet(hata); else coz(deger);
      };
      girdi.addEventListener("change", function () {
        const dosya = girdi.files && girdi.files[0];
        if (!dosya) { son(null); return; }
        (ikili ? dosya.arrayBuffer().then(function (b) { return new Uint8Array(b); }) : dosya.text())
          .then(function (icerik) {
            if (!ikili && icerik.charCodeAt(0) === 0xfeff) icerik = icerik.slice(1);
            son({ ad: dosya.name, icerik: icerik });
          }, function (e) { son(null, e); });
      });
      girdi.addEventListener("cancel", function () { son(null); });
      document.body.appendChild(girdi);
      girdi.click();
    });
  }

  async function ac(turler, secenek) {
    const s = secenek || {};
    const liste = turListesi(turler);
    if (!MASAUSTU) return webAc(liste, !!s.ikili);
    if (!s.ikili && liste.some(function (t) { return t.uzanti === "matris"; })) return (await M.projeAc()) || null;
    return (await M.ac({
      ikili: !!s.ikili, baslik: s.baslik || "",
      filtreler: [{ ad: liste.map(function (t) { return t.ad; }).join(", "), uzantilar: liste.map(function (t) { return t.uzanti; }) }],
    })) || null;
  }

  // ------------------------------------------------------------------ PDF
  function webYazdir(html, ad) {
    const belge = String(html || "");
    const yazdirVeKapat = function (pen) {
      const bas = function () { try { pen.focus(); pen.print(); } catch (e) { /* yoksay */ } };
      if (pen.document.readyState === "complete") setTimeout(bas, 250);
      else pen.addEventListener("load", function () { setTimeout(bas, 250); });
    };
    const pen = window.open("", "_blank");
    if (pen && pen.document) {
      pen.document.open();
      pen.document.write(belge);
      pen.document.close();
      try { if (!pen.document.title) pen.document.title = ad || "Rapor"; } catch (e) { /* yoksay */ }
      yazdirVeKapat(pen);
      return { ad: ad || "rapor" };
    }
    // Açılır pencere engellendiyse: görünmez çerçevede yazdır.
    const cerceve = document.createElement("iframe");
    cerceve.setAttribute("aria-hidden", "true");
    cerceve.style.cssText = "position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden";
    cerceve.srcdoc = belge;
    cerceve.addEventListener("load", function () {
      setTimeout(function () {
        try { cerceve.contentWindow.focus(); cerceve.contentWindow.print(); } catch (e) { /* yoksay */ }
        setTimeout(function () { cerceve.remove(); }, 60000);
      }, 250);
    });
    document.body.appendChild(cerceve);
    return { ad: ad || "rapor" };
  }

  async function pdfYazdir(html, ad) {
    const dosyaAdi = String(ad || "rapor").replace(/\.(pdf|html?)$/i, "");
    if (!MASAUSTU) return webYazdir(html, dosyaAdi);
    const r = await M.pdfYazdir({ html: String(html || ""), ad: dosyaAdi + ".pdf" });
    if (r && r.yol) bildir("PDF kaydedildi: " + r.ad, "Klasörde göster", function () { M.klasordeGoster(r.yol); });
    return r || null;
  }

  // ------------------------------------------------------------------ durum, otomatik kayıt
  let kirli = false;
  let kaynak = null;
  let zamanlayici = null;
  const OTOMATIK_KAYIT_MS = 20000;

  function otomatikKaydet() {
    zamanlayici = null;
    if (!MASAUSTU || !kirli || typeof kaynak !== "function") return;
    try {
      const p = kaynak();
      if (p && typeof p.icerik === "string" && p.icerik) M.otomatikKayit(p.icerik, p.ad || "");
    } catch (e) { /* kaynak hata verirse bir sonraki değişiklikte yeniden denenir */ }
  }

  // degisti() ya da degisti(true): kaydedilmemiş değişiklik var; degisti(false): kaydedildi / temiz.
  function degisti(k) {
    kirli = k === undefined ? true : !!k;
    if (!MASAUSTU) return;
    M.degisti(kirli);
    if (kirli && kaynak && !zamanlayici) zamanlayici = setTimeout(otomatikKaydet, OTOMATIK_KAYIT_MS);
  }

  function yeni() {
    kirli = false;
    if (MASAUSTU) M.yeni();
  }

  // fn() → {ad, icerik} (projenin .matris metni): kaydedilmemiş değişiklik varken düzenli aralıklarla kurtarma kaydı alınır.
  function projeKaynagi(fn) { kaynak = typeof fn === "function" ? fn : null; }

  function bildir(metin, dugme, fn) {
    const A = window.MatrisApp;
    if (A && typeof A.toast === "function") A.toast(metin, dugme, fn);
  }

  // ------------------------------------------------------------------ olaylar
  let bekleyen = null;   // işlenmemiş son açılan dosya (sayfa betikleri sonradan alabilir)

  function yay(ad, detail) {
    const olay = new CustomEvent(ad, { detail: detail, cancelable: true });
    window.dispatchEvent(olay);
    return olay.defaultPrevented;
  }

  function duzenlenebilirOdak() {
    const el = document.activeElement;
    return !!el && (el.isContentEditable || /^(INPUT|TEXTAREA)$/.test(el.tagName));
  }

  // Sayfa betiklerinin işlemediği komutlar için yerleşik davranış.
  function yerlesikKomut(d) {
    const k = d.komut;
    if ((k === "geri-al" || k === "yinele") && duzenlenebilirOdak()) {
      document.execCommand(k === "geri-al" ? "undo" : "redo");
      return true;
    }
    if (k === "sayfa" && d.sayfa) {
      const dugme = document.querySelector('.alt-nav button[data-sayfa="' + String(d.sayfa).replace(/["\\]/g, "") + '"]');
      if (dugme) { dugme.click(); return true; }
      return false;
    }
    if (k === "ayarlar") { const a = document.getElementById("ayarlar-ac"); if (a) { a.click(); return true; } return false; }
    if (k === "yazdir") { window.print(); return true; }
    // Proje kaynağı bildirilmişse (projeKaynagi) kaydetme köprüde yapılır; sayfa olayı kendisi de işleyebilir.
    if ((k === "kaydet" || k === "farkli-kaydet") && typeof kaynak === "function") {
      let p = null;
      try { p = kaynak(); } catch (e) { p = null; }
      if (p && typeof p.icerik === "string") {
        kaydet(p.ad || "proje.matris", p.icerik, "matris", { farkli: k === "farkli-kaydet" });
        return true;
      }
    }
    return false;
  }

  function komutGeldi(d) {
    if (!d || typeof d.komut !== "string") return;
    if (yay("masaustu-komut", d)) return;
    yerlesikKomut(d);
  }

  function dosyaGeldi(d) {
    if (!d || typeof d.icerik !== "string") return;
    if (yay("masaustu-dosya-acildi", d)) { bekleyen = null; return; }
    bekleyen = d;
    if (d.kurtarma) bildir("Kurtarılan çalışma hazır: " + (d.ad || "proje"));
  }

  // İşlenmemiş son açılan dosyayı verir ve kuyruktan çıkarır (geç yüklenen sayfa betikleri için).
  function bekleyenDosya() { const d = bekleyen; bekleyen = null; return d; }

  if (MASAUSTU) {
    document.documentElement.classList.add("masaustu");
    // Masaüstünde servis çalışanı gerekmez (dosyalar yerelden gelir); app.js'in kaydı sessizce atlanır.
    try {
      if (navigator.serviceWorker && typeof navigator.serviceWorker.register === "function") {
        navigator.serviceWorker.register = function () { return Promise.reject(new Error("Masaüstü sürümünde servis çalışanı kullanılmaz.")); };
      }
    } catch (e) { /* yoksay */ }
    M.komutDinle(komutGeldi);
    M.dosyaDinle(dosyaGeldi);
    // Sayfanın bütün betikleri yüklendikten sonra ana sürece "hazır" denir: bekleyen dosyalar ve komutlar o zaman gelir.
    const hazir = function () { setTimeout(function () { M.hazir(); }, 0); };
    if (document.readyState === "complete") hazir(); else window.addEventListener("load", hazir, { once: true });
  }

  window.MatrisDosya = Object.freeze({
    masaustu: MASAUSTU,
    kaydet: kaydet,
    ac: ac,
    pdfYazdir: pdfYazdir,
    degisti: degisti,
    yeni: yeni,
    projeKaynagi: projeKaynagi,
    klasordeGoster: function (yol) { if (MASAUSTU && yol) M.klasordeGoster(yol); },
    bekleyenDosya: bekleyenDosya,
    kirliMi: function () { return kirli; },
    turCoz: turCoz,
  });
})();
