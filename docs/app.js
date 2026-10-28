/* Matris Öğren — uygulama mantığı: form, Python motoruyla (motor.worker.js) iletişim, çizim, ayarlar, kurulum. */
"use strict";

(function () {
  const $ = function (id) { return document.getElementById(id); };
  const AYAR_ANAHTAR = "matris-ogren-ayarlar";
  const GIRDI_ANAHTAR = "matris-ogren-girdiler";
  const VARSAYILAN_AYAR = { ondalik: false, basamak: 4, kural: true, python: true, sema: true, en_fazla_eleman: 36, tema: "otomatik" };

  // ---------- İşlem tanımları ----------
  const MA = { ad: "A", tur: "matris", etiket: "A matrisi" };
  function secim(secenekler, varsayilan) {
    return { ad: "yontem", tur: "secim", etiket: "Yöntem", secenekler: secenekler, deger: varsayilan || "" };
  }
  const EAL = {
    E: { ad: "E", tur: "metin", etiket: "E (elastisite modülü)", deger: "E" },
    A: { ad: "A", tur: "metin", etiket: "A (kesit alanı)", deger: "A" },
    I: { ad: "I", tur: "metin", etiket: "I (atalet momenti)", deger: "I" },
    L: { ad: "L", tur: "metin", etiket: "L (eleman boyu)", deger: "L" },
  };
  const ISLEMLER = [
    { id: "topla", grup: "Temel işlemler", ad: "Toplama   A + B",
      alanlar: [MA, { ad: "B", tur: "matris", etiket: "B matrisi" }], ornek: { A: "1 2; 3 4", B: "5 6; 7 8" } },
    { id: "cikar", grup: "Temel işlemler", ad: "Çıkarma   A − B",
      alanlar: [MA, { ad: "B", tur: "matris", etiket: "B matrisi" }], ornek: { A: "5 6; 7 8", B: "1 2; 3 4" } },
    { id: "skaler", grup: "Temel işlemler", ad: "Skalerle çarpma   k·A",
      alanlar: [{ ad: "k", tur: "metin", etiket: "k (skaler)", deger: "2" }, MA], ornek: { k: "3", A: "1 2; 3 4" } },
    { id: "carp", grup: "Temel işlemler", ad: "Matris çarpımı   A·B·…",
      alanlar: [{ ad: "matrisler", tur: "liste", etiket: "Matrisler (çarpım sırasıyla)" }], ornek: { matrisler: ["1 2; 3 4", "5 6; 7 8"] } },
    { id: "transpoz", grup: "Temel işlemler", ad: "Transpoz   Aᵀ", alanlar: [MA], ornek: { A: "1 2 3; 4 5 6" } },
    { id: "iz", grup: "Temel işlemler", ad: "İz   tr(A)", alanlar: [MA], ornek: { A: "1 2; 3 4" } },
    { id: "determinant", grup: "Temel işlemler", ad: "Determinant   det(A)",
      alanlar: [MA, secim([["", "Otomatik"], ["kofaktor", "Kofaktör açılımı"], ["eliminasyon", "Satır eliminasyonu"]])],
      ornek: { A: "2 1 0; 1 3 1; 0 1 4" } },
    { id: "ters", grup: "Temel işlemler", ad: "Ters matris   A⁻¹",
      alanlar: [MA, secim([["", "Otomatik"], ["formul", "Ek (adjoint) matris formülü"], ["gauss", "Gauss-Jordan"]])],
      ornek: { A: "4 7; 2 6" } },
    { id: "rank", grup: "Temel işlemler", ad: "Rank", alanlar: [MA], ornek: { A: "1 2; 2 4" } },
    { id: "coz", grup: "Denklem ve özdeğer", ad: "Denklem sistemi   A·x = b",
      alanlar: [MA, { ad: "b", tur: "matris", etiket: "b (sağ taraf, sütun vektörü)" },
        secim([["gauss", "Gauss eliminasyonu"], ["cramer", "Cramer kuralı"], ["ters", "Ters matris"]], "gauss"),
        { ad: "bilinmeyen", tur: "metin", etiket: "Bilinmeyen adı", deger: "x" }],
      ornek: { A: "2 1; 1 3", b: "3; 5", yontem: "gauss", bilinmeyen: "x" } },
    { id: "ozdeger", grup: "Denklem ve özdeğer", ad: "Özdeğer ve özvektör",
      alanlar: [MA, { ad: "M", tur: "matris", etiket: "M kütle matrisi (isteğe bağlı: K·φ = λ·M·φ)", istege: true },
        { ad: "ozvektor", tur: "onay", etiket: "Özvektörleri de hesapla", deger: true }],
      ornek: { A: "2 1; 1 2", M: "", ozvektor: true } },
    { id: "cubuk_eleman", grup: "Sonlu elemanlar", ad: "Çubuk elemanı rijitlik matrisi",
      alanlar: [EAL.E, EAL.A, EAL.L], ornek: { E: "200000", A: "100", L: "1000" } },
    { id: "kiris_eleman", grup: "Sonlu elemanlar", ad: "Kiriş elemanı rijitlik matrisi",
      alanlar: [EAL.E, EAL.I, EAL.L], ornek: { E: "E", I: "I", L: "L" } },
    { id: "kafes_eleman", grup: "Sonlu elemanlar", ad: "Kafes (2B çubuk) elemanı",
      alanlar: [EAL.E, EAL.A, EAL.L, { ad: "aci", tur: "metin", etiket: "Açı θ (derece)", deger: "0" }],
      ornek: { E: "E", A: "A", L: "L", aci: "45" } },
    { id: "birlestir", grup: "Sonlu elemanlar", ad: "Global matris birleştirme",
      alanlar: [{ ad: "elemanlar", tur: "elemanlar", etiket: "Eleman matrisleri ve global serbestlik numaraları" },
        { ad: "n", tur: "metin", etiket: "Toplam serbestlik sayısı" }],
      ornek: { elemanlar: [{ k: "k -k; -k k", dof: "1 2" }, { k: "k -k; -k k", dof: "2 3" }], n: "3" } },
    { id: "sinir_kosulu", grup: "Sonlu elemanlar", ad: "Sınır koşulu uygula ve çöz",
      alanlar: [{ ad: "K", tur: "matris", etiket: "K (global rijitlik matrisi)" }, { ad: "F", tur: "matris", etiket: "F (yük vektörü)" },
        { ad: "sabit", tur: "metin", etiket: "Tutulu (mesnetli) serbestlik dereceleri, örn. 1 3" },
        { ad: "bilinmeyen", tur: "metin", etiket: "Bilinmeyen adı", deger: "u" }],
      ornek: { K: "2 -1 0; -1 2 -1; 0 -1 1", F: "0; 0; 10", sabit: "1", bilinmeyen: "u" } },
  ];
  function islemBul(id) { return ISLEMLER.find(function (i) { return i.id === id; }) || ISLEMLER[0]; }

  // ---------- Durum ----------
  const durum = { islem: "topla", girdiler: {}, hazir: false, sonYanit: null, sonIstek: null, kurOlayi: null };
  let ayar = Object.assign({}, VARSAYILAN_AYAR);
  try {
    const k = JSON.parse(localStorage.getItem(AYAR_ANAHTAR) || "null");
    if (k && typeof k === "object") ayar = Object.assign({}, VARSAYILAN_AYAR, k);
    const g = JSON.parse(localStorage.getItem(GIRDI_ANAHTAR) || "null");
    if (g && typeof g === "object") durum.girdiler = g;
  } catch (e) { /* özel pencere ya da engelli depolama */ }
  function ayariKaydet() { try { localStorage.setItem(AYAR_ANAHTAR, JSON.stringify(ayar)); } catch (e) { /* yoksay */ } }
  function girdileriKaydet() { try { localStorage.setItem(GIRDI_ANAHTAR, JSON.stringify(durum.girdiler)); } catch (e) { /* yoksay */ } }

  // ---------- Yardımcılar ----------
  function kacis(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function katexHtml(tex, blok) {
    if (!window.katex) return (blok ? '<pre class="kod">' : "<code>") + kacis(tex) + (blok ? "</pre>" : "</code>");
    try {
      // Etkileşim kitaplığı varsa onun KaTeX seçenekleri (ders makroları \ka \kutua … ve \htmlClass kx-* izni) kullanılır.
      const sec = (window.Etkilesim && typeof Etkilesim.katexSecenek === "function")
        ? Etkilesim.katexSecenek(!!blok)
        : { displayMode: !!blok, throwOnError: false, strict: "ignore", trust: false };
      return katex.renderToString(tex, sec);
    } catch (e) { return "<code>" + kacis(tex) + "</code>"; }
  }
  // Markdown + LaTeX: kod ve formüller önce ayrılır (yer tutucu), markdown işlenir, sonra geri konur.
  function mdRender(md, satir) {
    const yer = [];
    const sakla = function (html) { yer.push(html); return "" + (yer.length - 1) + ""; };
    let m = String(md || "");
    m = m.replace(/```[a-zA-Z0-9_-]*\r?\n([\s\S]*?)```/g, function (_, kod) {
      return sakla('<pre class="kod">' + kacis(kod.replace(/\n$/, "")) + "</pre>");
    });
    m = m.replace(/`([^`\n]+)`/g, function (_, kod) { return sakla("<code>" + kacis(kod) + "</code>"); });
    m = m.replace(/\$\$([\s\S]+?)\$\$/g, function (_, tex) { return sakla(katexHtml(tex.trim(), true)); });
    m = m.replace(/\$([^$\n]+?)\$/g, function (_, tex) { return sakla(katexHtml(tex, false)); });
    let html;
    if (window.marked && typeof marked.parse === "function") {
      try {
        html = satir ? marked.parseInline(m, { gfm: true, breaks: false, async: false })
                     : marked.parse(m, { gfm: true, breaks: false, async: false });
      } catch (e) { html = satir ? kacis(m) : "<p>" + kacis(m) + "</p>"; }
    } else if (satir) {
      html = kacis(m);
    } else {
      html = "<p>" + kacis(m).replace(/\n\n+/g, "</p><p>").replace(/\n/g, "<br>") + "</p>";
    }
    return html.replace(/(\d+)/g, function (_, i) { return yer[+i]; });
  }
  let toastZaman = null;
  function toast(metin, dugmeMetni, dugmeIslevi, kalici) {
    const t = $("toast"), d = $("toast-dugme");
    $("toast-metin").textContent = metin;
    if (dugmeMetni) { d.textContent = dugmeMetni; d.classList.remove("gizli"); d.onclick = dugmeIslevi; }
    else { d.classList.add("gizli"); d.onclick = null; }
    t.classList.remove("gizli");
    clearTimeout(toastZaman);
    if (!kalici) toastZaman = setTimeout(function () { t.classList.add("gizli"); }, 4500);
  }
  function durumYaz(metin, sinif) {
    const d = $("durum");
    d.textContent = metin;
    d.className = "durum" + (sinif ? " " + sinif : "");
  }
  function kopyala(metin) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(metin).then(function () { toast("Kopyalandı."); }, function () { toast("Kopyalanamadı."); });
    } else {
      toast("Bu tarayıcıda panoya kopyalama desteklenmiyor.");
    }
  }

  // ---------- Motor (Web Worker) ----------
  let motor = null, sayac = 0, motorSurum = null;
  const bekleyen = new Map();
  // Motor hazır olmadan gelen ders/etkileşim istekleri burada bekler; motor hata verirse hepsi Türkçe iletiyle reddedilir.
  const hazirBekleyen = [];
  const durumDinleyen = [];     // motor yükleme ilerleme metnini izleyenler: fn(metin)
  function hazirBekle() {
    return new Promise(function (resolve, reject) {
      if (durum.hazir) { resolve(); return; }
      if (durum.motorHata) { reject(new Error(durum.motorHata)); return; }
      hazirBekleyen.push({ resolve: resolve, reject: reject });
    });
  }
  function hazirGoster(h) {
    durum.hazir = h;
    $("hesapla").disabled = !h;
    if (h) {
      durum.motorHata = "";
      $("yukleme").classList.add("gizli");
      durumYaz("Hazır ✓", "hazir");
      hazirBekleyen.splice(0).forEach(function (b) { b.resolve(); });
    }
  }
  function motorHata(mesaj) {
    hazirGoster(false);
    durum.motorHata = "Hesap motoru kullanılamıyor: " + mesaj;
    hazirBekleyen.splice(0).forEach(function (b) { b.reject(new Error(durum.motorHata)); });
    $("yukleme").classList.remove("gizli");
    $("yukleme-metin").innerHTML = '<span class="hata-kutu" style="display:block">' + kacis(mesaj) + "</span>" +
      '<button type="button" class="dugme kucuk" id="motor-tekrar" style="margin-top:8px">Tekrar dene</button>';
    $("motor-tekrar").onclick = motoruBaslat;
    durumYaz("Motor hatası", "hata");
  }
  function motoruBaslat() {
    if (motor) { try { motor.terminate(); } catch (e) { /* yoksay */ } }
    bekleyen.forEach(function (b) { b.reject(new Error("Motor yeniden başlatıldı.")); });
    bekleyen.clear();
    hazirGoster(false);
    durum.motorHata = "";
    $("yukleme").classList.remove("gizli");
    $("yukleme-metin").textContent = "Başlatılıyor…";
    $("yukleme-cubuk").style.width = "2%";
    durumYaz("Motor yükleniyor…", "");
    if (!window.Worker) { motorHata("Bu tarayıcı Web Worker desteklemiyor."); return; }
    try { motor = new Worker("motor.worker.js", { type: "module" }); }
    catch (e) { motorHata("Motor başlatılamadı: " + e.message); return; }
    motor.onmessage = function (e) {
      const m = e.data || {};
      if (m.tur === "durum") {
        $("yukleme-metin").textContent = m.metin;
        $("yukleme-cubuk").style.width = (m.oran || 0) + "%";
        durumYaz(m.metin, "");
        durumDinleyen.slice().forEach(function (f) { f(m.metin); });
      } else if (m.tur === "hazir") {
        motorSurum = m.surum || {};
        $("yukleme-cubuk").style.width = "100%";
        hazirGoster(true);
        $("ayar-surum").textContent = "Motor " + (motorSurum.motor || "?") + " · sympy " + (motorSurum.sympy || "?") +
          " · Python " + (motorSurum.python || "?") + " · Pyodide " + (motorSurum.pyodide || "?");
        yardimiDoldur();
      } else if (m.tur === "hata") {
        motorHata(m.mesaj || "Bilinmeyen motor hatası.");
      } else if (m.tur === "yanit") {
        const b = bekleyen.get(m.id);
        if (b) { bekleyen.delete(m.id); b.resolve(m.yanit); }
      }
    };
    motor.onerror = function (e) { motorHata("Motor hatası: " + (e && e.message ? e.message : "bilinmeyen")); };
    motor.postMessage({ tur: "baslat" });
  }
  function iste(istek) {
    return new Promise(function (resolve, reject) {
      if (!motor) { reject(new Error("Motor yok.")); return; }
      const id = ++sayac;
      bekleyen.set(id, { resolve: resolve, reject: reject });
      motor.postMessage({ tur: "istek", id: id, istek: istek });
    });
  }
  // Etkileşim kitaplığının (Etkilesim.motorBagla) ve ders örneklerinin kullandığı istek işlevi: motor hazır olana dek bekler,
  // geçerli ayarları (sema dahil) isteğe ekler, yanıtı (ya da Türkçe bir hatayı) Promise olarak döndürür.
  function motorIstegi(istek) {
    return hazirBekle().then(function () {
      const g = Object.assign({}, istek || {});
      g.ayarlar = Object.assign({
        ondalik: !!ayar.ondalik, basamak: +ayar.basamak || 4, en_fazla_eleman: +ayar.en_fazla_eleman || 0, sema: !!ayar.sema,
      }, g.ayarlar || {});
      return iste(g);
    });
  }

  // ---------- Form ----------
  function alanHtml(alan, deger) {
    const etiket = '<label class="alan" for="alan-' + alan.ad + '">' + kacis(alan.etiket) +
      (alan.istege ? ' <small>(boş bırakılabilir)</small>' : "") + "</label>";
    if (alan.tur === "matris") {
      return etiket + '<textarea id="alan-' + alan.ad + '" class="girdi" rows="2" data-alan="' + alan.ad +
        '" placeholder="örn. 1 2; 3 4" spellcheck="false">' + kacis(deger == null ? "" : deger) + "</textarea>";
    }
    if (alan.tur === "metin") {
      return etiket + '<input id="alan-' + alan.ad + '" class="girdi" data-alan="' + alan.ad + '" value="' +
        kacis(deger == null ? (alan.deger == null ? "" : alan.deger) : deger) + '" spellcheck="false">';
    }
    if (alan.tur === "secim") {
      const sec = deger == null ? alan.deger : deger;
      return etiket + '<select id="alan-' + alan.ad + '" class="girdi" data-alan="' + alan.ad + '">' +
        alan.secenekler.map(function (s) {
          return '<option value="' + kacis(s[0]) + '"' + (s[0] === sec ? " selected" : "") + ">" + kacis(s[1]) + "</option>";
        }).join("") + "</select>";
    }
    if (alan.tur === "onay") {
      const isaretli = deger == null ? !!alan.deger : !!deger;
      return '<label class="alan" style="display:flex;gap:8px;align-items:center;font-weight:500"><input type="checkbox" data-alan="' +
        alan.ad + '"' + (isaretli ? " checked" : "") + "> " + kacis(alan.etiket) + "</label>";
    }
    if (alan.tur === "liste") {
      const l = Array.isArray(deger) && deger.length ? deger : ["", ""];
      return '<label class="alan">' + kacis(alan.etiket) + '</label><div data-liste="' + alan.ad + '">' +
        l.map(function (v, i) { return listeSatirHtml(i, v); }).join("") + "</div>" +
        '<div class="dugmeler" style="margin-top:6px"><button type="button" class="dugme kucuk" data-ekle="liste">＋ Matris ekle</button>' +
        '<button type="button" class="dugme kucuk" data-sil="liste">− Sonuncuyu kaldır</button></div>';
    }
    if (alan.tur === "elemanlar") {
      const l = Array.isArray(deger) && deger.length ? deger : [{ k: "", dof: "" }];
      return '<label class="alan">' + kacis(alan.etiket) + '</label><div data-elemanlar="' + alan.ad + '">' +
        l.map(function (v, i) { return elemanSatirHtml(i, v); }).join("") + "</div>" +
        '<div class="dugmeler" style="margin-top:6px"><button type="button" class="dugme kucuk" data-ekle="elemanlar">＋ Eleman ekle</button>' +
        '<button type="button" class="dugme kucuk" data-sil="elemanlar">− Sonuncuyu kaldır</button></div>';
    }
    return "";
  }
  function listeSatirHtml(i, v) {
    return '<div class="eleman-satiri"><div class="baslik">Matris ' + (i + 1) + "</div>" +
      '<textarea class="girdi" rows="2" data-liste-eleman placeholder="örn. 1 2; 3 4" spellcheck="false">' + kacis(v || "") + "</textarea></div>";
  }
  function elemanSatirHtml(i, v) {
    return '<div class="eleman-satiri"><div class="baslik">Eleman ' + (i + 1) + "</div>" +
      '<textarea class="girdi" rows="2" data-k placeholder="eleman matrisi, örn. k -k; -k k" spellcheck="false">' + kacis(v.k || "") + "</textarea>" +
      '<input class="girdi" data-dof style="margin-top:6px" placeholder="global serbestlik numaraları, örn. 1 2" value="' + kacis(v.dof || "") + '" spellcheck="false"></div>';
  }
  function formuKur() {
    const islem = islemBul(durum.islem);
    const g = durum.girdiler[islem.id] || {};
    $("form").innerHTML = islem.alanlar.map(function (a) { return alanHtml(a, g[a.ad]); }).join("");
    $("islem").value = islem.id;
  }
  function girdiOku() {
    const islem = islemBul(durum.islem), form = $("form"), g = {};
    islem.alanlar.forEach(function (a) {
      if (a.tur === "liste") {
        g[a.ad] = Array.prototype.map.call(form.querySelectorAll("[data-liste-eleman]"), function (t) { return t.value; });
      } else if (a.tur === "elemanlar") {
        g[a.ad] = Array.prototype.map.call(form.querySelectorAll("[data-elemanlar] .eleman-satiri"), function (s) {
          return { k: s.querySelector("[data-k]").value, dof: s.querySelector("[data-dof]").value };
        });
      } else {
        const el = form.querySelector('[data-alan="' + a.ad + '"]');
        if (!el) return;
        g[a.ad] = a.tur === "onay" ? el.checked : el.value;
      }
    });
    return g;
  }
  function girdiyiSakla() {
    durum.girdiler[durum.islem] = girdiOku();
    girdileriKaydet();
  }
  function islemSec(id) {
    durum.islem = id;
    formuKur();
  }
  function islemListesiniKur() {
    const sel = $("islem");
    let html = "", grup = null;
    ISLEMLER.forEach(function (i) {
      if (i.grup !== grup) { if (grup !== null) html += "</optgroup>"; html += '<optgroup label="' + kacis(i.grup) + '">'; grup = i.grup; }
      html += '<option value="' + i.id + '">' + kacis(i.ad) + "</option>";
    });
    sel.innerHTML = html + "</optgroup>";
    sel.addEventListener("change", function () { girdiyiSakla(); islemSec(sel.value); });
  }

  // ---------- Hesap ve çizim ----------
  function gorunum() {
    const r = document.querySelector('input[name="gorunum"]:checked');
    return r ? r.value : "hepsi";
  }
  // mod verilmezse hesap sayfasındaki "Görünüm" seçimi kullanılır; dersler her zaman "hepsi" ister (ayarlara uyar).
  function bloklariSec(bloklar, modVer) {
    const mod = modVer || gorunum();
    return bloklar.filter(function (b) {
      if (b.etiket === "python") return mod === "python" || (mod === "hepsi" && ayar.python);
      if (b.etiket === "kural") return mod !== "python" && ayar.kural;
      if (b.etiket === "sema" || b.tur === "sema") return mod !== "python" && ayar.sema !== false;
      return mod !== "python";
    });
  }
  let kopyaMetinleri = [];

  // ---------- Ok şemaları ----------
  // Motor "sema" bloğu gönderir: {baslik, kareler: [{baslik, svg}]} (bkz. web_kopru.py). Her blok, karelerini adım adım
  // gösteren bir karta dönüşür: sahnede SVG, altında açıklama; ◀ ▶ / Oynat / noktalar / "Tümünü göster".
  // Adım değişince SVG düğümü yeniden kurulur; böylece style.css'teki ok animasyonları baştan oynar.
  const SEMA_BEKLEME = 1300;   // bir karede bekleme süresi (ms)
  const SEMA_KADEME = 280;     // karedeki her ek ok kademesi (.g1 … .g7) için ek bekleme (ms)
  const SEMA_YASAK = "script,foreignObject,style,iframe,object,embed,link,meta,base,animate,set,animateMotion,animateTransform,use,image";
  const SEMA_IKON = {
    oynat: '<polygon points="7 4 19 12 7 20" fill="currentColor"/>',
    duraklat: '<rect x="6" y="5" width="4.2" height="14" rx="1.2" fill="currentColor"/><rect x="13.8" y="5" width="4.2" height="14" rx="1.2" fill="currentColor"/>',
    tekrar: '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
    onceki: '<polyline points="15 5 8 12 15 19"/>',
    sonraki: '<polyline points="9 5 16 12 9 19"/>',
    izgara: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
    tek: '<rect x="4" y="6" width="16" height="12" rx="2"/>'
  };
  // Kimliğin ilk harfi "ev sahibi"dir: "s" = hesap makinesi anlatımı, "d" = dersler (örnek çözümleri ve etkileşimlerin
  // motor çıktıları). Her ev sahibi kendi gözlemcilerine sahiptir; biri sıfırlanınca diğerinin kartları etkilenmez.
  let semaVeri = {};        // kimlik -> {baslik, w, kareler: [{baslik, svg, kademe}]}
  let semaDurum = {};       // kimlik -> {adim, tum, oynuyor, zaman, t0, elle, olcuW, kamera}
  let semaGozlemci = {};    // ev sahibi -> IntersectionObserver: kart ilk kez görününce kendiliğinden oynat
  let semaOlcer = {};       // ev sahibi -> ResizeObserver: açıklama kutusunun yüksekliğini sabitle
  let semaSayac = 0;        // kimlikler hiç sıfırlanmaz: aynı sayfada iki ev sahibinin kimliği çakışmaz
  function semaKimlik(onek) { semaSayac += 1; return onek + semaSayac; }

  function azHareket() {
    try { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }
    catch (e) { return false; }
  }
  function semaIkon(ad) {
    return '<svg class="sema-ikon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
      (SEMA_IKON[ad] || "") + "</svg>";
  }
  function semaDur(s) {
    if (!s) return;
    if (s.zaman) { clearTimeout(s.zaman); s.zaman = 0; }
    s.oynuyor = false;
  }
  // Her yeniden çizimde (ve hata/sonuç değişiminde) bütün zamanlayıcı, gözlemci ve durum sıfırlanır.
  // onek verilirse yalnız o ev sahibinin (s ya da d) durumu sıfırlanır.
  function semaSifirla(onek) {
    Object.keys(semaDurum).forEach(function (k) {
      if (onek && k.charAt(0) !== onek) return;
      semaDur(semaDurum[k]); semaKameraDur(semaDurum[k]);
      delete semaDurum[k]; delete semaVeri[k];
    });
    [semaGozlemci, semaOlcer].forEach(function (gruplar) {
      Object.keys(gruplar).forEach(function (o) {
        if (onek && o !== onek) return;
        gruplar[o].disconnect(); delete gruplar[o];
      });
    });
  }
  // Bir kutunun (örn. yeniden çizilecek bir etkileşim çıktısının) içindeki şema kartlarını durdurur ve unutur.
  function semaTemizleKok(kok) {
    if (!kok) return;
    Array.prototype.forEach.call(kok.querySelectorAll(".sema[data-sema-id]"), function (fig) {
      const k = fig.dataset.semaId, o = k.charAt(0), st = fig.querySelector(".sema-sahne");
      semaDur(semaDurum[k]); semaKameraDur(semaDurum[k]);
      delete semaDurum[k]; delete semaVeri[k];
      if (st) {
        if (semaGozlemci[o]) semaGozlemci[o].unobserve(st);
        if (semaOlcer[o]) semaOlcer[o].unobserve(st);
      }
    });
  }
  // Motorun SVG'sini güvenli ve tutarlı hâle getirir: tehlikeli öğe/öznitelikleri atar, kareleri ortak viewBox'a oturtur
  // (kareler arasında sahne boyu oynamasın), her karenin ok kademesini (en büyük gN) bulur.
  function semaHazirla(icerik) {
    const ham = icerik && Array.isArray(icerik.kareler) ? icerik.kareler : [];
    const kareler = [];
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    ham.forEach(function (k) {
      if (!k || typeof k.svg !== "string") return;
      const sablon = document.createElement("template");
      sablon.innerHTML = k.svg;
      const kok = sablon.content.querySelector("svg");
      if (!kok) return;
      kok.querySelectorAll(SEMA_YASAK).forEach(function (el) { el.remove(); });
      let kademe = 0;
      [kok].concat(Array.prototype.slice.call(kok.querySelectorAll("*"))).forEach(function (el) {
        Array.prototype.slice.call(el.attributes).forEach(function (a) {
          const ad = a.name.toLowerCase();
          if (ad.indexOf("on") === 0 || ((ad === "href" || ad === "xlink:href") && a.value.trim().charAt(0) !== "#")) el.removeAttribute(a.name);
        });
        const m = /(?:^|\s)g([0-7])(?:\s|$)/.exec(el.getAttribute("class") || "");
        if (m) kademe = Math.max(kademe, +m[1]);
      });
      let vb = (kok.getAttribute("viewBox") || "").trim().split(/[\s,]+/).map(Number);
      if (vb.length !== 4 || !vb.every(function (d) { return isFinite(d); })) {
        const w = parseFloat(kok.getAttribute("width")), h = parseFloat(kok.getAttribute("height"));
        vb = w > 0 && h > 0 ? [0, 0, w, h] : null;
      }
      if (vb && vb[2] > 0 && vb[3] > 0) {
        x0 = Math.min(x0, vb[0]); y0 = Math.min(y0, vb[1]);
        x1 = Math.max(x1, vb[0] + vb[2]); y1 = Math.max(y1, vb[1] + vb[3]);
      }
      kareler.push({ baslik: k.baslik == null ? "" : String(k.baslik), svg: "", kok: kok, kademe: kademe });
    });
    const tam = isFinite(x0) && x1 > x0 && y1 > y0;
    kareler.forEach(function (k) {
      if (tam) {
        k.kok.setAttribute("viewBox", [x0, y0, x1 - x0, y1 - y0].join(" "));
        k.kok.setAttribute("width", String(x1 - x0));
        k.kok.setAttribute("height", String(y1 - y0));
      }
      k.kok.setAttribute("focusable", "false");
      k.svg = k.kok.outerHTML;
      delete k.kok;
    });
    return { baslik: icerik && icerik.baslik ? String(icerik.baslik) : "", w: tam ? Math.round(x1 - x0) : 0, kareler: kareler };
  }
  // Bir sema bloğunun kart HTML'i. Tek kareli blokta kontrol yoktur (yalnız başlık, görsel, açıklama).
  function semaHtml(icerik, kimlik) {
    const v = semaHazirla(icerik);
    const n = v.kareler.length;
    if (!n) return "";
    semaVeri[kimlik] = v;
    semaDurum[kimlik] = { adim: 0, tum: false, oynuyor: false, zaman: 0, t0: Date.now(), elle: false, olcuW: 0, kamera: 0 };
    const k0 = v.kareler[0];
    const ad = v.baslik || "Ok şeması";
    const cok = n > 1;
    let h = '<figure class="sema" data-sema-id="' + kimlik + '"' + (cok ? ' tabindex="0"' : "") +
      ' aria-label="' + kacis("Ok şeması: " + ad + (cok ? ", " + n + " adım" : "")) + '">' +
      '<div class="sema-ust"><div class="sema-baslik"><span aria-hidden="true">🧭</span> ' + kacis(ad) + "</div>" +
      (cok ? '<span class="sema-sayac" aria-hidden="true">Adım 1 / ' + n + "</span>" : "") + "</div>" +
      '<div class="sema-govde">' +
      '<div class="sema-sahne"' + (v.w ? ' style="--sema-w:' + v.w + '"' : "") + ' aria-hidden="true" tabindex="-1">' + k0.svg + "</div>" +
      '<p class="sema-aciklama" aria-live="polite" aria-atomic="true">' +
      (cok ? '<span class="sema-oku">Adım 1 / ' + n + ": </span>" : "") +
      '<span class="sema-metin">' + kacis(k0.baslik) + "</span></p>";
    if (cok) {
      h += '<div class="sema-noktalar' + (n > 12 ? " cok" : "") + '" role="group" aria-label="Adım seç">';
      for (let i = 0; i < n; i++) {
        h += '<button type="button" class="sema-nokta' + (i === 0 ? " aktif" : "") + '" data-sema="git" data-adim="' + i +
          '" aria-label="Adım ' + (i + 1) + '"' + (i === 0 ? ' aria-current="step"' : "") + "></button>";
      }
      h += "</div>";
    }
    h += "</div>";
    if (cok) {
      h += '<div class="sema-izgara gizli" role="list" aria-label="Tüm adımlar"></div>' +
        '<div class="sema-kontrol">' +
        '<button type="button" class="dugme kucuk sema-adim" data-sema="onceki" aria-label="Önceki adım" aria-disabled="true">' + semaIkon("onceki") + "</button>" +
        (azHareket() ? "" : '<button type="button" class="dugme kucuk ana sema-oynat" data-sema="oynat" data-durum="oynat">' + semaIkon("oynat") + "<span>Oynat</span></button>") +
        '<button type="button" class="dugme kucuk sema-adim" data-sema="sonraki" aria-label="Sonraki adım">' + semaIkon("sonraki") + "</button>" +
        '<button type="button" class="dugme kucuk sema-izgara-dugme" data-sema="izgara" data-durum="adim">' + semaIkon("izgara") + "<span>Tümünü göster</span></button>" +
        "</div>";
    }
    return h + "</figure>";
  }
  function semaFigur(kimlik) {
    return document.querySelector('.sema[data-sema-id="' + kimlik + '"]');
  }
  // aria-disabled (disabled değil): odaktaki düğme pasifleşince klavye odağı kaybolmasın.
  function semaPasif(el, pasif) {
    if (!el) return;
    if (pasif) el.setAttribute("aria-disabled", "true"); else el.removeAttribute("aria-disabled");
  }
  // Yalnız kontrolleri günceller (SVG'ye dokunmaz): Duraklat/Oynat/Tekrar, ◀ ▶ pasifliği, canlı bölge kipi.
  function semaKumanda(fig, s, n) {
    const sonda = s.adim >= n - 1;
    semaPasif(fig.querySelector('[data-sema="onceki"]'), s.tum || s.adim <= 0);
    semaPasif(fig.querySelector('[data-sema="sonraki"]'), s.tum || sonda);
    const oynat = fig.querySelector('[data-sema="oynat"]');
    if (oynat) {
      semaPasif(oynat, s.tum);
      const d = s.oynuyor ? "duraklat" : (sonda ? "tekrar" : "oynat");
      if (oynat.getAttribute("data-durum") !== d) {
        oynat.setAttribute("data-durum", d);
        oynat.innerHTML = semaIkon(d) + "<span>" + (d === "duraklat" ? "Duraklat" : d === "tekrar" ? "Tekrar" : "Oynat") + "</span>";
      }
    }
    const izg = fig.querySelector('[data-sema="izgara"]');
    if (izg) {
      const d = s.tum ? "tum" : "adim";
      if (izg.getAttribute("data-durum") !== d) {
        izg.setAttribute("data-durum", d);
        izg.innerHTML = semaIkon(s.tum ? "tek" : "izgara") + "<span>" + (s.tum ? "Adım adım göster" : "Tümünü göster") + "</span>";
      }
    }
    const p = fig.querySelector(".sema-aciklama");
    if (p) p.setAttribute("aria-live", s.oynuyor ? "off" : "polite");   // oynarken ekran okuyucu her adımı okumasın
  }
  function semaYenile(kimlik) {
    const fig = semaFigur(kimlik), v = semaVeri[kimlik], s = semaDurum[kimlik];
    if (fig && v && s) semaKumanda(fig, s, v.kareler.length);
  }
  // Açıklama kutusunun yüksekliğini en uzun açıklamaya göre sabitler (adım değişince kart zıplamasın).
  // Ölçüm gizli bir kopyada yapılır; canlı bölgeye dokunulmaz.
  function semaSabitle(fig, v) {
    const s = semaDurum[fig.dataset.semaId];
    const p = fig.querySelector(".sema-aciklama");
    if (!s || !p) return;
    const w = p.offsetWidth;
    if (!w || w === s.olcuW) return;      // gizliyken (kart ya da ızgara kipi) ölçülemez; genişlik aynıysa yeniden ölçme
    const kopya = p.cloneNode(false);
    kopya.removeAttribute("aria-live");
    kopya.setAttribute("aria-hidden", "true");
    kopya.style.cssText = "position:absolute;visibility:hidden;pointer-events:none;min-height:0;width:" + w + "px";
    p.parentNode.appendChild(kopya);
    let en = 0;
    v.kareler.forEach(function (k) {
      kopya.textContent = k.baslik;
      en = Math.max(en, kopya.getBoundingClientRect().height);
    });
    p.parentNode.removeChild(kopya);
    p.style.minHeight = Math.ceil(en) + "px";
    s.olcuW = w;
  }
  // Kamera: dar ekranda sığmayan şema sahnesinde yana kayar. Her adımda önce karedeki ilk vurgulu bölgeye oturur
  // (A'nın satırı), oklar çizilirken sonuncusuna süzülür (C'nin hücresi). Kullanıcı kaydırırsa hemen bırakır.
  // Sahne sığıyorsa, azaltılmış hareket isteniyorsa ya da karede vurgu yoksa hiçbir şey yapmaz.
  function semaKameraDur(s) {
    if (s && s.kamera) { cancelAnimationFrame(s.kamera); s.kamera = 0; }
  }
  function semaKamera(s, sahne, kademe) {
    semaKameraDur(s);
    if (!s || !sahne || azHareket()) return;
    const en = sahne.clientWidth, tasma = sahne.scrollWidth - en;
    if (tasma < 8) return;
    const sr = sahne.getBoundingClientRect(), sol = sahne.scrollLeft;
    const gruplar = {};
    Array.prototype.forEach.call(sahne.querySelectorAll(".vurgu"), function (el) {
      const m = /(?:^|\s)g([0-7])(?:\s|$)/.exec(el.getAttribute("class") || "");
      const r = el.getBoundingClientRect();
      if (!m || !(r.width > 0)) return;
      const a = r.left - sr.left + sol, b = r.right - sr.left + sol, g = gruplar[m[1]];
      if (g) { g.a = Math.min(g.a, a); g.b = Math.max(g.b, b); } else gruplar[m[1]] = { a: a, b: b };
    });
    const anahtar = Object.keys(gruplar).sort();
    if (!anahtar.length) return;
    const kes = function (x) { return Math.max(0, Math.min(tasma, x)); };
    const orta = function (g) { return kes((g.a + g.b) / 2 - en / 2); };
    let sol0 = Infinity, sag0 = -Infinity;
    anahtar.forEach(function (k) { sol0 = Math.min(sol0, gruplar[k].a); sag0 = Math.max(sag0, gruplar[k].b); });
    if (sag0 - sol0 <= en - 32) { sahne.scrollLeft = kes((sol0 + sag0) / 2 - en / 2); return; }   // hepsi aynı anda görünür: ortala
    const bas = orta(gruplar[anahtar[0]]), bit = orta(gruplar[anahtar[anahtar.length - 1]]);
    sahne.scrollLeft = bas;
    if (Math.abs(bit - bas) < 16) return;
    const basla = performance.now() + 350, sure = Math.min(1600, 500 + (kademe || 0) * 200);
    const kare = function (t) {
      s.kamera = 0;
      if (!sahne.isConnected) return;
      const u = Math.min(1, Math.max(0, (t - basla) / sure));
      sahne.scrollLeft = bas + (bit - bas) * (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
      if (u < 1) s.kamera = requestAnimationFrame(kare);
    };
    s.kamera = requestAnimationFrame(kare);
  }
  // Parmakla, tekerlekle ya da fareyle sahneye dokunan kişi kamerayı bırakmış olur.
  function semaKameraBirak(e) {
    const st = e.target && e.target.closest ? e.target.closest(".sema-sahne") : null;
    const fig = st ? st.closest(".sema[data-sema-id]") : null;
    if (fig) semaKameraDur(semaDurum[fig.dataset.semaId]);
  }
  // Geçerli adımı (ya da "Tümünü göster" kipinde bütün adımları) çizer.
  function semaCiz(kimlik) {
    const fig = semaFigur(kimlik), v = semaVeri[kimlik], s = semaDurum[kimlik];
    if (!fig || !v || !s) return;
    const n = v.kareler.length;
    const govde = fig.querySelector(".sema-govde"), izgara = fig.querySelector(".sema-izgara");
    const sahne = fig.querySelector(".sema-sahne"), p = fig.querySelector(".sema-aciklama");
    const sayac = fig.querySelector(".sema-sayac");
    semaKumanda(fig, s, n);
    semaKameraDur(s);
    if (sayac) sayac.textContent = s.tum ? n + " adım" : "Adım " + (s.adim + 1) + " / " + n;
    if (s.tum) {
      sahne.innerHTML = "";                // aynı SVG'ler iki yerde durmasın
      govde.classList.add("gizli");
      izgara.innerHTML = v.kareler.map(function (k, i) {
        return '<div class="sema-hucre" role="listitem"><div aria-hidden="true">' + k.svg + "</div>" +
          '<div class="sema-hucre-baslik"><b aria-hidden="true">' + (i + 1) + '</b><span class="sema-oku">Adım ' + (i + 1) + ": </span>" + kacis(k.baslik) + "</div></div>";
      }).join("");
      izgara.classList.remove("gizli");
      return;
    }
    izgara.classList.add("gizli");
    izgara.innerHTML = "";
    govde.classList.remove("gizli");
    const k = v.kareler[s.adim];
    sahne.innerHTML = k.svg;               // düğümler yeniden kurulur: CSS animasyonu baştan başlar
    semaKamera(s, sahne, k.kademe);        // dar ekranda sığmayan şema: kamera vurgulu bölgeleri izler
    p.innerHTML = '<span class="sema-oku">Adım ' + (s.adim + 1) + " / " + n + ': </span><span class="sema-metin">' + kacis(k.baslik) + "</span>";
    fig.querySelectorAll(".sema-nokta").forEach(function (d, i) {
      d.classList.toggle("aktif", i === s.adim);
      d.classList.toggle("gecmis", i < s.adim);
      if (i === s.adim) d.setAttribute("aria-current", "step"); else d.removeAttribute("aria-current");
    });
  }
  // Otomatik oynatma: her kare SEMA_BEKLEME (+ ok kademesi kadar ek) süre kalır; son karede durur.
  function semaPlanla(kimlik) {
    const s = semaDurum[kimlik], v = semaVeri[kimlik];
    if (!s || !v || !s.oynuyor) return;
    const n = v.kareler.length;
    if (s.adim >= n - 1) { semaDur(s); semaYenile(kimlik); return; }
    s.zaman = setTimeout(function () {
      s.zaman = 0;
      if (semaDurum[kimlik] !== s || !s.oynuyor) return;     // yeniden çizim ya da duraklatma: eski zamanlayıcıyı yok say
      s.adim += 1;
      semaCiz(kimlik);
      semaPlanla(kimlik);
    }, SEMA_BEKLEME + v.kareler[s.adim].kademe * SEMA_KADEME);
  }
  function semaOynat(kimlik) {
    const s = semaDurum[kimlik], v = semaVeri[kimlik];
    if (!s || !v) return;
    s.elle = true;
    if (s.oynuyor) { semaDur(s); semaYenile(kimlik); return; }
    if (s.adim >= v.kareler.length - 1) s.adim = 0;          // sondaysa baştan oyna
    s.oynuyor = true;
    semaCiz(kimlik);
    semaPlanla(kimlik);
  }
  function semaGit(kimlik, i) {
    const s = semaDurum[kimlik], v = semaVeri[kimlik];
    if (!s || !v) return;
    s.elle = true;
    semaDur(s);
    s.tum = false;
    s.adim = Math.max(0, Math.min(v.kareler.length - 1, i));
    semaCiz(kimlik);
  }
  function semaIzgara(kimlik) {
    const s = semaDurum[kimlik];
    if (!s || !semaVeri[kimlik]) return;
    s.elle = true;
    semaDur(s);
    s.tum = !s.tum;
    semaCiz(kimlik);
  }
  // Kart ilk kez görününce (kullanıcı henüz dokunmadıysa) kendiliğinden oynar.
  function semaOtoBaslat(kimlik) {
    const s = semaDurum[kimlik], v = semaVeri[kimlik];
    if (!s || !v || s.elle || s.tum || s.oynuyor || azHareket()) return;
    s.oynuyor = true;
    if (Date.now() - s.t0 > 700) semaCiz(kimlik);            // ilk karenin animasyonu ekran dışındayken bitmişti: baştan oynat
    else {
      semaYenile(kimlik);
      const fig = semaFigur(kimlik);
      if (fig) semaKamera(s, fig.querySelector(".sema-sahne"), v.kareler[s.adim].kademe);
    }
    semaPlanla(kimlik);
  }
  // anlatim içindeki kartları devreye alır: açıklama yüksekliği ölçümü + görününce otomatik oynatma.
  // kok: kartların bulunduğu kutu; onek: ev sahibi ("s" hesap, "d" dersler). Gözlemciler ev sahibi başına tembel kurulur.
  function semaBaslat(kok, onek) {
    const figurler = Array.prototype.slice.call(kok.querySelectorAll(".sema[data-sema-id]")).filter(function (f) {
      const v = semaVeri[f.dataset.semaId];
      return v && v.kareler.length > 1;
    });
    if (!figurler.length) return;
    if (typeof ResizeObserver !== "undefined") {
      if (!semaOlcer[onek]) {
        semaOlcer[onek] = new ResizeObserver(function (girdiler) {
          girdiler.forEach(function (g) {
            const fig = g.target.closest(".sema[data-sema-id]");
            const v = fig ? semaVeri[fig.dataset.semaId] : null;
            if (v) semaSabitle(fig, v);
          });
        });
      }
      figurler.forEach(function (f) { semaOlcer[onek].observe(f.querySelector(".sema-sahne")); });
    }
    if (azHareket()) return;                                  // azaltılmış harekette otomatik oynatma yok
    if (typeof IntersectionObserver === "undefined") {
      figurler.forEach(function (f) {
        const kimlik = f.dataset.semaId, s = semaDurum[kimlik];
        s.zaman = setTimeout(function () { s.zaman = 0; semaOtoBaslat(kimlik); }, 300);
      });
      return;
    }
    if (!semaGozlemci[onek]) {
      semaGozlemci[onek] = new IntersectionObserver(function (girdiler, gozlemci) {
        girdiler.forEach(function (g) {
          if (!g.isIntersecting || g.intersectionRatio < 0.39) return;
          gozlemci.unobserve(g.target);
          const fig = g.target.closest(".sema[data-sema-id]");
          if (fig) semaOtoBaslat(fig.dataset.semaId);
        });
      }, { threshold: 0.4 });
    }
    figurler.forEach(function (f) { semaGozlemci[onek].observe(f.querySelector(".sema-sahne")); });
  }
  // Tıklama (data-sema düğmeleri), klavye (ok tuşları) ve odak olayları #anlatim üzerinde yetki devriyle işlenir.
  function semaTikla(dugme) {
    if (dugme.getAttribute("aria-disabled") === "true") return;
    const fig = dugme.closest(".sema[data-sema-id]");
    if (!fig) return;
    const kimlik = fig.dataset.semaId, s = semaDurum[kimlik];
    if (!s || !semaVeri[kimlik]) return;
    const eylem = dugme.dataset.sema;
    if (eylem === "onceki") semaGit(kimlik, s.adim - 1);
    else if (eylem === "sonraki") semaGit(kimlik, s.adim + 1);
    else if (eylem === "git") semaGit(kimlik, +dugme.dataset.adim || 0);
    else if (eylem === "oynat") semaOynat(kimlik);
    else if (eylem === "izgara") semaIzgara(kimlik);
  }
  function semaTus(e) {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    const fig = e.target.closest ? e.target.closest(".sema[data-sema-id]") : null;
    if (!fig) return;
    const kimlik = fig.dataset.semaId, s = semaDurum[kimlik], v = semaVeri[kimlik];
    if (!s || !v || v.kareler.length < 2 || s.tum) return;
    const st = e.target.closest(".sema-sahne");
    if (st && st.scrollWidth > st.clientWidth + 1) return;   // yana kayan sahnede oklar kaydırmaya kalsın
    e.preventDefault();
    const hedef = s.adim + (e.key === "ArrowRight" ? 1 : -1);
    if (hedef >= 0 && hedef < v.kareler.length) semaGit(kimlik, hedef);
  }
  // Klavyeyle karta odaklanan kişi için otomatik oynatma durur (fareyle tıklamada durmaz).
  function semaOdak(e) {
    const fig = e.target.closest ? e.target.closest(".sema[data-sema-id]") : null;
    if (!fig) return;
    const s = semaDurum[fig.dataset.semaId];
    if (!s || !s.oynuyor) return;
    let klavye = false;
    try { klavye = e.target.matches(":focus-visible"); } catch (x) { klavye = false; }
    if (!klavye) return;
    s.elle = true;
    semaDur(s);
    semaYenile(fig.dataset.semaId);
  }

  // Bir motor yanıtını (bloklar) hedef kutuya çizer. Hesap sayfası ("s") ve dersler/etkileşimler ("d") aynı çiziciyi kullanır.
  // Hesap sayfasında kopyalama metinleri kopyaMetinleri dizisinde, diğerlerinde düğmenin kendi özniteliğinde durur.
  function anlatimYaz(y, hedef, onek) {
    const ders = onek !== "s";
    const parcalar = bloklariSec(y.bloklar || [], ders ? "hepsi" : null).map(function (b) {
      if (b.tur === "kod") {
        const kopya = ders ? 'data-kopyala-metin="' + kacis(b.kod) + '"' : 'data-kopyala="' + (kopyaMetinleri.push(b.kod) - 1) + '"';
        return '<div class="kod-baslik">' + kacis(b.baslik || "🐍 Python ile") +
          ' <button type="button" class="dugme kucuk" ' + kopya + '>Kodu kopyala</button></div>' +
          '<pre class="kod">' + kacis(b.kod) + "</pre>" +
          (b.cikti ? '<div class="kod-baslik">Çıktı:</div><pre class="kod cikti">' + kacis(b.cikti) + "</pre>" : "");
      }
      if (b.tur === "math") return "<div>" + katexHtml(b.icerik, true) + "</div>";
      if (b.tur === "sema") return semaHtml(b.icerik, semaKimlik(onek));   // sözlük: asla mdRender'a gitmez
      return typeof b.icerik === "string" ? mdRender(b.icerik) : "";
    }).filter(Boolean);
    hedef.innerHTML = parcalar.join("\n") || '<p class="not">Bu görünümde gösterilecek bölüm yok.</p>';
    semaBaslat(hedef, onek);
  }
  function anlatimCiz() {
    semaSifirla("s");
    const y = durum.sonYanit;
    if (!y || y.hata) return;
    kopyaMetinleri = [];
    anlatimYaz(y, $("anlatim"), "s");
  }
  // Etkileşim kitaplığının motor yanıtı çizicisi (Etkilesim.motorBagla): aynı hedefe yeniden çizilirse eski şemalar unutulur.
  function anlatimDersCiz(y, hedef) {
    semaTemizleKok(hedef);
    anlatimYaz(y, hedef, "d");
  }
  function zincirCiz(y) {
    const z = $("zincir");
    if (!y.zincir) { z.innerHTML = ""; return; }
    const hedefler = ISLEMLER.filter(function (i) {
      return i.alanlar.some(function (a) { return a.tur === "matris" || a.tur === "liste" || a.tur === "elemanlar"; });
    });
    z.innerHTML = '<label class="not" style="flex:1 1 100%;margin:0">Bu sonucu başka bir işlemde kullan:</label>' +
      '<select id="zincir-hedef" class="girdi" style="flex:1 1 180px;min-height:40px">' +
      hedefler.map(function (i) {
        return '<option value="' + i.id + '"' + (i.id === durum.islem ? " selected" : "") + ">" + kacis(i.ad) + "</option>";
      }).join("") + "</select>" +
      '<button type="button" class="dugme kucuk" id="zincir-tasi">Sonucu taşı →</button>' +
      '<button type="button" class="dugme kucuk" id="sonuc-kopyala">Sonucu kopyala</button>';
    $("zincir-tasi").onclick = function () { sonucuTasi($("zincir-hedef").value, y.sonuc_metin); };
    $("sonuc-kopyala").onclick = function () { kopyala(y.sonuc_metin); };
  }
  function sonucuTasi(hedefId, metin) {
    girdiyiSakla();
    const hedef = islemBul(hedefId);
    const g = Object.assign({}, durum.girdiler[hedef.id] || {});
    const alan = hedef.alanlar.find(function (a) { return a.tur === "matris" || a.tur === "liste" || a.tur === "elemanlar"; });
    if (!alan) return;
    if (alan.tur === "matris") g[alan.ad] = metin;
    else if (alan.tur === "liste") {
      const l = Array.isArray(g[alan.ad]) ? g[alan.ad].slice() : [];
      l[0] = metin; if (l.length < 2) l.push("");
      g[alan.ad] = l;
    } else {
      const l = Array.isArray(g[alan.ad]) && g[alan.ad].length ? g[alan.ad].slice() : [{ k: "", dof: "" }];
      l[0] = Object.assign({}, l[0], { k: metin });
      g[alan.ad] = l;
    }
    durum.girdiler[hedef.id] = g;
    girdileriKaydet();
    islemSec(hedef.id);
    sayfaGoster("hesap");
    window.scrollTo({ top: 0, behavior: "smooth" });
    toast("Sonuç " + hedef.ad.trim() + " işlemine " + (alan.tur === "matris" ? alan.ad + " olarak" : "ilk matris olarak") + " kondu.");
  }
  function hataGoster(y) {
    semaSifirla("s");                    // kart gizlenirken şema zamanlayıcıları ve gözlemcileri de durur
    const h = $("hata-metin");
    if (y.hata_turu === "girdi") {
      h.innerHTML = "<b>Girdi hatası:</b> " + kacis(y.hata) +
        '<p class="not" style="margin-top:6px">Satırları <kbd>;</kbd> ile, elemanları boşlukla ayırın; her satırda eşit sayıda eleman olmalı.</p>';
    } else {
      h.innerHTML = "<b>Motor hatası:</b> " + kacis(y.hata) +
        (y.iz ? '<details class="katlanir" style="margin-top:6px"><summary>Ayrıntı</summary><pre class="kod" style="font-size:12px">' + kacis(y.iz) + "</pre></details>" : "");
    }
    $("hata-kart").classList.remove("gizli");
    $("sonuc-kart").classList.add("gizli");
    $("anlatim-kart").classList.add("gizli");
    $("bos-kart").classList.add("gizli");
  }
  function yanitGoster(y, ms) {
    if (!y || y.hata) { hataGoster(y || { hata: "Boş yanıt.", hata_turu: "ic" }); return; }
    durum.sonYanit = y;
    $("hata-kart").classList.add("gizli");
    $("bos-kart").classList.add("gizli");
    $("sonuc-sure").textContent = (ms / 1000).toFixed(1) + " s";
    const tex = (y.sonuc_etiket ? y.sonuc_etiket + " = " : "") + y.sonuc_latex;
    $("sonuc-latex").innerHTML = katexHtml(tex, true);
    zincirCiz(y);
    anlatimCiz();
    $("sonuc-kart").classList.remove("gizli");
    $("anlatim-kart").classList.remove("gizli");
    if (window.innerWidth < 900) $("sonuc-kart").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  async function hesapla() {
    if (!durum.hazir) { toast("Python motoru henüz hazır değil; yükleme bitince deneyin."); return; }
    girdiyiSakla();
    const islem = islemBul(durum.islem);
    const istek = {
      islem: islem.id, girdi: girdiOku(),
      ayarlar: { ondalik: !!ayar.ondalik, basamak: +ayar.basamak || 4, en_fazla_eleman: +ayar.en_fazla_eleman || 0, sema: !!ayar.sema },
    };
    durum.sonIstek = istek;
    $("hesapla").disabled = true;
    durumYaz("Hesaplanıyor…", "");
    const t0 = performance.now();
    const uzun = setTimeout(function () { toast("Hesap sürüyor… Büyük ya da sembolik matrislerde uzun sürebilir.", null, null, true); }, 15000);
    try {
      const y = await iste(istek);
      clearTimeout(uzun); $("toast").classList.add("gizli");
      yanitGoster(y, performance.now() - t0);
    } catch (e) {
      clearTimeout(uzun);
      hataGoster({ hata: e.message, hata_turu: "ic" });
    } finally {
      $("hesapla").disabled = !durum.hazir;
      if (durum.hazir) durumYaz("Hazır ✓", "hazir");
    }
  }
  async function yardimiDoldur() {
    try {
      const y = await iste({ islem: "yardim", girdi: {}, ayarlar: {} });
      if (y && !y.hata && y.bloklar && y.bloklar.length && typeof y.bloklar[0].icerik === "string") $("yardim-fonksiyonlar").innerHTML = mdRender(y.bloklar[0].icerik);
    } catch (e) { /* yardım isteğe bağlı */ }
  }

  // ---------- Yardım: Bina sayfasının klavye kısayolları ----------
  // Tek kaynak: araç kutusu kayıt defteri (MatrisArac.kisayollar(); bina.js ve bina_cizim.js bağlamaları dahil). Bina sayfası henüz
  // açılmadıysa kayıt boştur; o zaman katalogdaki kısayollar gösterilir. Sayfanın kendi tuşları (bina.js klavye işleyicisi) aynı
  // tuştaki kayıttan önce gelir: F / Shift+F bina.js'te tam ekran / sığdır olarak yeniden atanır.
  const SAYFA_TUSLARI = [
    { kisayol: "Esc", ad: "Kipten çık, seçimi ya da yarım çizimi / ölçümü bırak; tam ekrandan çık", grup: "sayfa" },
    { kisayol: "Shift+F10", ad: "Seçili elemanın bağlam (sağ tık) menüsü", grup: "sayfa" },
    { kisayol: "?", ad: "Kısayol listesini aç", grup: "sayfa" },
    { kisayol: "PgUp", ad: "Düzlem yukarı: bir üst Z aksı ya da sonraki cephe aksı (aks–kat çiziminde üst kat)", grup: "aks" },
    { kisayol: "PgDn", ad: "Düzlem aşağı", grup: "aks" },
    { kisayol: "F", ad: "Tam ekran (Esc ya da F ile çıkılır)", grup: "gorunum" },
    { kisayol: "Shift+F", ad: "Modeli sığdır", grup: "gorunum" },
    { kisayol: "Ctrl+Shift+Z", ad: "Yinele", grup: "duzenleme" },
    { kisayol: "Backspace", ad: "Seçileni sil (seçim yoksa Sil aracı)", grup: "duzenleme" },
  ];
  function kisayolSatirlari(M) {
    let liste = [];
    try { liste = M.kisayollar() || []; } catch (e) { liste = []; }
    let kaynak = "kayit";
    if (liste.length) {
      liste = liste.map(function (k) { const kk = M.komut ? M.komut(k.id) : null; return { kisayol: k.kisayol, ad: k.ad, grup: (kk && kk.grup) || "diger" }; });
    } else {
      kaynak = "katalog";
      liste = (M.KATALOG || []).filter(function (k) { return k.kisayol && M.kisayolMetni(k.kisayol); })
        .map(function (k) { return { kisayol: M.kisayolMetni(k.kisayol), ad: k.ad, grup: k.grup }; });
    }
    const sayfa = {};
    SAYFA_TUSLARI.forEach(function (t) { sayfa[t.kisayol] = 1; });
    const satirlar = liste.filter(function (k) { return !sayfa[k.kisayol]; }).concat(SAYFA_TUSLARI);
    const sira = {};
    (M.GRUPLAR || []).forEach(function (g, i) { sira[g.id] = i; });
    const siraAl = function (g) { return g === "sayfa" ? 1000 : (sira[g] != null ? sira[g] : 500); };
    satirlar.forEach(function (s, i) { s.i = i; });
    satirlar.sort(function (a, b) { return siraAl(a.grup) - siraAl(b.grup) || a.i - b.i; });
    return { satirlar: satirlar, kaynak: kaynak };
  }
  function kisayolTablosu() {
    const tablo = $("yardim-kisayollar");
    if (!tablo) return;
    const M = window.MatrisArac;
    if (!M || typeof M.kisayollar !== "function") {
      tablo.dataset.kaynak = "yok";
      tablo.innerHTML = '<tbody><tr><td class="not">Araç kutusu modülü yüklenmedi; kısayollar Bina sayfasında araç kutusu düğmelerinin ' +
        "ipucunda yazar (tam liste: KULLANIM.md, 3.10).</td></tr></tbody>";
      return;
    }
    const s = kisayolSatirlari(M);
    const grupAd = { sayfa: "Bina sayfası", diger: "Diğer" };
    (M.GRUPLAR || []).forEach(function (g) { grupAd[g.id] = g.ad; });
    tablo.dataset.kaynak = s.kaynak;
    tablo.innerHTML = '<thead><tr><th scope="col">Tuş</th><th scope="col">Komut</th><th scope="col">Araç grubu</th></tr></thead><tbody>' +
      s.satirlar.map(function (r) {
        return '<tr><td style="white-space:nowrap"><kbd>' + kacis(r.kisayol) + "</kbd></td><td>" + kacis(r.ad) + '</td><td style="white-space:nowrap">' +
          kacis(grupAd[r.grup] || r.grup) + "</td></tr>";
      }).join("") + "</tbody>" +
      (s.kaynak === "katalog" ? '<tfoot><tr><td colspan="3" class="not">Bina sayfası açılınca sayfanın kendi komutları (ör. W duvar) da listeye eklenir.</td></tr></tfoot>' : "");
  }

  // ---------- Dersler ----------
  // dersler.json iki biçimde olabilir. Yeni: [{no, id, baslik, bolum, bolum_adi, ozet, sure, md, parcalar[]}] (zengin dersler);
  // eski: [{no, baslik, md}] (defterden çıkarılan düz markdown). İkisi de aynı sayfada çizilir.
  // Yol: #dersler = liste, #ders/<id> = tek ders (eski biçimde id yerine no kullanılır).
  const DERS_SON_ANAHTAR = "matris-ogren-son-ders";
  const KUTU_BASLIK = {
    not: "Not", uyari: "Dikkat", ipucu: "İpucu", tanim: "Tanım", ozet: "Özet", hata: "Sık yapılan hata", muhendislik: "Mühendislikte",
  };
  let dersler = [];
  let dersSoz = null;            // dersleriYukle() sözü; yönlendirme ders listesi gelene dek bekler
  let dersPanelSay = 0;
  const dersDurum = { acik: null };

  function dersKimlik(d) { return String(d.id != null && d.id !== "" ? d.id : d.no); }
  function dersIndeks(id) {
    for (let i = 0; i < dersler.length; i++) if (dersKimlik(dersler[i]) === String(id)) return i;
    return -1;
  }
  function sonDersOku() { try { return localStorage.getItem(DERS_SON_ANAHTAR); } catch (e) { return null; } }
  function sonDersYaz(id) { try { localStorage.setItem(DERS_SON_ANAHTAR, String(id)); } catch (e) { /* yoksay */ } }
  function dersBaglanti(id) { return "#ders/" + encodeURIComponent(id); }

  async function dersleriYukle() {
    const kutu = $("dersler");
    try {
      const r = await fetch("dersler.json");
      if (!r.ok) throw new Error(r.status);
      const liste = await r.json();
      dersler = Array.isArray(liste) ? liste : [];
      dersListeCiz();
    } catch (e) { kutu.innerHTML = '<p class="not">Dersler yüklenemedi (' + kacis(e.message) + ").</p>"; }
  }
  // Liste: bölümlere göre gruplanmış kartlar (bölüm yoksa tek grup). Her kart bir bağlantıdır (#ders/<id>).
  function dersListeCiz() {
    const kutu = $("dersler");
    if (!dersler.length) { kutu.innerHTML = '<p class="not">Ders içeriği bulunamadı.</p>'; return; }
    const gruplar = [];
    dersler.forEach(function (d, i) {
      const ad = d.bolum_adi || "";
      let g = null;
      for (let k = 0; k < gruplar.length; k++) if (gruplar[k].ad === ad) { g = gruplar[k]; break; }
      if (!g) { g = { ad: ad, liste: [] }; gruplar.push(g); }
      g.liste.push({ d: d, i: i });
    });
    let h = "";
    const son = sonDersOku(), sonI = son == null ? -1 : dersIndeks(son);
    if (sonI >= 0) {
      h += '<a class="ders-devam" href="' + dersBaglanti(son) + '"><span>Kaldığın yerden devam et</span><b>' +
        mdRender(dersler[sonI].baslik, true) + "</b></a>";
    }
    gruplar.forEach(function (g) {
      h += '<section class="ders-grup">' + (g.ad ? '<h3 class="ders-grup-baslik">' + kacis(g.ad) + "</h3>" : "") + '<ul class="ders-liste">';
      g.liste.forEach(function (o) {
        const d = o.d;
        h += '<li><a class="ders-satir" href="' + dersBaglanti(dersKimlik(d)) + '">' +
          '<span class="ders-no" aria-hidden="true">' + (d.bolum ? kacis(d.no) : o.i + 1) + "</span>" +
          '<span class="ders-satir-metin"><b class="ders-satir-baslik">' + mdRender(d.baslik, true) + "</b>" +
          (d.ozet ? '<span class="ders-satir-ozet">' + mdRender(d.ozet, true) + "</span>" : "") + "</span>" +
          (d.sure ? '<span class="ders-sure">~' + kacis(d.sure) + " dk</span>" : "") + "</a></li>";
      });
      h += "</ul></section>";
    });
    kutu.innerHTML = h;
  }

  // Açık dersin etkileşimlerini, şema kartlarını ve DOM'unu bırakır (animasyon/zamanlayıcı sızmasın).
  function dersTemizle() {
    const kart = $("ders-kart");
    if (window.Etkilesim && typeof Etkilesim.temizle === "function") {
      Array.prototype.forEach.call(kart.querySelectorAll("[data-etkilesim]"), function (div) {
        try { Etkilesim.temizle(div); } catch (e) { /* yoksay */ }
      });
    }
    semaSifirla("d");
    kart.innerHTML = "";
  }
  function dersListeGoster() {
    dersTemizle();
    dersDurum.acik = null;
    $("ders-kart").classList.add("gizli");
    $("ders-liste-kart").classList.remove("gizli");
    dersListeCiz();     // "kaldığın yerden devam et" bağlantısı güncel kalsın
  }

  function dersParcaMd(icerik) {
    const el = document.createElement("div");
    el.className = "ders-md";
    el.innerHTML = mdRender(icerik);
    return el;
  }
  function dersSekilEl(svg, baslik) {
    const fig = document.createElement("figure");
    fig.className = "ders-sekil";
    // SVG'yi ders derleyicisi (ders_derle.py) denetler ve derler; güvenilir kaynak olduğundan olduğu gibi konur.
    fig.innerHTML = '<div class="ders-sekil-svg">' + svg + "</div>" + (baslik ? "<figcaption>" + mdRender(baslik, true) + "</figcaption>" : "");
    return fig;
  }
  function dersEtkilesimEl(p, alistirma, kurulacak) {
    const kap = document.createElement("section");
    kap.className = "ders-etkilesim" + (alistirma ? " ders-alistirma" : "");
    let ust = "";
    if (alistirma) ust += '<span class="ders-rozet">Alıştırma</span>';
    if (p.baslik) ust += '<h4 class="ders-etk-baslik">' + mdRender(p.baslik, true) + "</h4>";
    if (ust) kap.innerHTML = '<div class="ders-etk-ust">' + ust + "</div>";
    const alan = document.createElement("div");
    alan.className = "ders-etk-alan";
    alan.setAttribute("data-etkilesim", p.ad || "");
    kap.appendChild(alan);
    kurulacak.push({ alan: alan, ad: (alistirma ? "alistirma:" : "") + (p.ad || ""), param: p.param || {} });
    return kap;
  }
  // Etkileşimler DOM'a girdikten sonra kurulur (ölçü gerektirenler için). Bilinmeyen ad "yok": sakin bir "yakında" notu.
  function dersEtkilesimKur(k) {
    const yakinda = function () { k.alan.innerHTML = '<p class="ders-yakinda">Bu çizim yakında.</p>'; };
    if (!window.Etkilesim || typeof Etkilesim.kur !== "function") { yakinda(); return; }
    try {
      Etkilesim.kur(k.alan, k.ad, k.param);
      if (k.alan.dataset.durum === "yok") { Etkilesim.temizle(k.alan); yakinda(); }
    } catch (e) {
      k.alan.innerHTML = '<p class="ders-yakinda">Bu çizim şu an gösterilemiyor.</p>';
    }
  }

  // Örnek kartı: soru + (şekil) + İpucu / Cevabı göster / Adım adım çözüm. Çözüm motorda "ders_calistir" ile çalışır ve
  // hesap sayfasıyla aynı çizici (anlatimYaz: adımlar, formüller, ok şemaları) ile gösterilir.
  function dersOrnekEl(p) {
    const art = document.createElement("article");
    art.className = "ders-ornek";
    const n = ++dersPanelSay;
    const kod = String(p.kod || "").trim();
    let h = '<h4 class="ders-ornek-baslik"><span class="ders-rozet">Örnek ' + kacis(p.no != null ? p.no : "") + "</span>" +
      (p.baslik ? '<span class="ders-ayrac" aria-hidden="true"> · </span><span>' + mdRender(p.baslik, true) + "</span>" : "") + "</h4>";
    h += '<div class="ders-ornek-soru">' + mdRender(p.soru) + "</div>";
    const dugmeler = [];
    if (p.ipucu) dugmeler.push(["ipucu", "İpucu"]);
    if (p.cevap) dugmeler.push(["cevap", "Cevabı göster"]);
    if (kod) dugmeler.push(["cozum", "Adım adım çözüm"]);
    art.innerHTML = h;
    if (p.sekil) art.appendChild(dersSekilEl(p.sekil, ""));
    if (dugmeler.length) {
      const satir = document.createElement("div");
      satir.className = "ders-ornek-dugmeler";
      satir.innerHTML = dugmeler.map(function (d) {
        return '<button type="button" class="dugme kucuk" data-ac="' + d[0] + '" aria-expanded="false" aria-controls="dp' + n + "-" + d[0] + '">' + d[1] + "</button>";
      }).join("");
      art.appendChild(satir);
    }
    const panel = function (ad, sinif, etiket, govde) {
      const el = document.createElement("div");
      el.id = "dp" + n + "-" + ad;
      el.className = "ders-panel " + sinif + " gizli";
      el.setAttribute("data-panel", ad);
      el.innerHTML = '<b class="ders-panel-etiket">' + etiket + "</b>" + govde;
      art.appendChild(el);
      return el;
    };
    if (p.ipucu) panel("ipucu", "ders-ipucu", "İpucu", '<div class="ders-panel-icerik anlatim">' + mdRender(p.ipucu) + "</div>");
    if (p.cevap) panel("cevap", "ders-cevap", "Cevap", '<div class="ders-panel-icerik anlatim">' + mdRender(p.cevap) + "</div>");
    if (kod) panel("cozum", "ders-cozum", "Adım adım çözüm", '<div class="ders-panel-icerik anlatim ders-cozum-icerik"></div>');
    if (p.yorum && (p.cevap || kod)) panel("yorum", "ders-yorum", "Yorum", '<div class="ders-panel-icerik anlatim">' + mdRender(p.yorum) + "</div>");
    art.addEventListener("click", function (e) {
      const b = e.target.closest ? e.target.closest("button[data-ac]") : null;
      if (!b || !art.contains(b)) return;
      const ad = b.dataset.ac, pn = art.querySelector('[data-panel="' + ad + '"]');
      if (!pn) return;
      const acik = !pn.classList.toggle("gizli");
      b.setAttribute("aria-expanded", acik ? "true" : "false");
      b.classList.toggle("aktif", acik);
      if (ad === "cozum" && acik && !pn.dataset.yuklendi) {
        pn.dataset.yuklendi = "1";
        dersCozumYukle(pn.querySelector(".ders-cozum-icerik"), kod, pn);
      }
      const yorum = art.querySelector('[data-panel="yorum"]');
      if (yorum) {
        const c = art.querySelector('[data-panel="cevap"]'), z = art.querySelector('[data-panel="cozum"]');
        yorum.classList.toggle("gizli", !((c && !c.classList.contains("gizli")) || (z && !z.classList.contains("gizli"))));
      }
    });
    return art;
  }
  function dersCozumYukle(hedef, kod, panel) {
    let dinleyen = null;
    const birak = function () {
      const i = durumDinleyen.indexOf(dinleyen);
      if (i >= 0) durumDinleyen.splice(i, 1);
    };
    const yaz = function (metin) { hedef.innerHTML = '<p class="not ders-bekle" role="status">' + kacis(metin) + "</p>"; };
    if (!durum.hazir && !durum.motorHata) {
      // Motor hâlâ yükleniyor: ilerleme metni gösterilir, hazır olunca çözüm kendiliğinden gelir.
      yaz($("yukleme-metin").textContent || "Python motoru yükleniyor…");
      dinleyen = function (metin) { if (hedef.isConnected) yaz(metin); };
      durumDinleyen.push(dinleyen);
    } else {
      yaz("Çözüm hazırlanıyor…");
    }
    const hata = function (ileti) {
      birak();
      panel.dataset.yuklendi = "";       // kapatıp yeniden açınca bir kez daha denenir
      if (hedef.isConnected) hedef.innerHTML = '<p class="hata-kutu">Çözüm gösterilemedi: ' + kacis(ileti) + "</p>";
    };
    motorIstegi({ islem: "ders_calistir", girdi: { kod: kod } }).then(function (y) {
      if (!y || y.hata) { hata(y && y.hata ? y.hata : "Boş yanıt."); return; }
      birak();
      if (hedef.isConnected) anlatimDersCiz(y, hedef);
    }, function (e) { hata(e && e.message ? e.message : "bilinmeyen hata"); });
  }

  function dersParcaEl(p, kurulacak) {
    if (!p || typeof p !== "object") return null;
    if (p.tur === "kutu") {
      const cesit = KUTU_BASLIK[p.cesit] ? p.cesit : "not";
      const el = document.createElement("aside");
      el.className = "ders-kutu kutu-" + cesit;
      el.setAttribute("role", "note");
      el.innerHTML = '<div class="ders-kutu-baslik">' + mdRender(p.baslik || KUTU_BASLIK[cesit], true) + "</div>" +
        '<div class="ders-kutu-govde anlatim">' + mdRender(p.icerik) + "</div>";
      return el;
    }
    if (p.tur === "sekil") return typeof p.svg === "string" ? dersSekilEl(p.svg, p.baslik) : null;
    if (p.tur === "etkilesim") return dersEtkilesimEl(p, false, kurulacak);
    if (p.tur === "alistirma") return dersEtkilesimEl(p, true, kurulacak);
    if (p.tur === "ornek") return dersOrnekEl(p);
    return typeof p.icerik === "string" ? dersParcaMd(p.icerik) : null;     // "md" ve bilinmeyen türler
  }

  function dersAc(id) {
    const i = dersIndeks(id);
    if (i < 0) { toast("Ders bulunamadı."); dersListeGoster(); return; }
    dersTemizle();
    const d = dersler[i], kimlik = dersKimlik(d), kart = $("ders-kart");
    dersDurum.acik = kimlik;
    sonDersYaz(kimlik);
    let h = '<nav class="ders-yol" aria-label="Konum"><a class="ders-geri" href="#dersler">← Tüm dersler</a>' +
      (d.bolum_adi ? '<span class="ders-yol-bolum">' + kacis(d.bolum_adi) + "</span>" : "") + "</nav>" +
      '<header class="ders-ust"><p class="ders-no-etiket">Ders ' + (d.bolum ? kacis(d.no) : i + 1) + (d.sure ? " · ~" + kacis(d.sure) + " dk" : "") + "</p>" +
      '<h2 id="ders-baslik" tabindex="-1">' + mdRender(d.baslik, true) + "</h2>" +
      (d.ozet ? '<p class="ders-ozet">' + mdRender(d.ozet, true) + "</p>" : "") + "</header>" +
      '<div class="ders-govde" id="ders-govde"></div><nav class="ders-gezinti" aria-label="Ders gezintisi">';
    const bag = function (j, yon, etiket) {
      if (j < 0 || j >= dersler.length) return '<span class="ders-gez bos"></span>';
      return '<a class="ders-gez ' + yon + '" rel="' + yon + '" href="' + dersBaglanti(dersKimlik(dersler[j])) + '"><small>' + etiket + "</small><b>" +
        mdRender(dersler[j].baslik, true) + "</b></a>";
    };
    h += bag(i - 1, "prev", "← Önceki ders") + bag(i + 1, "next", "Sonraki ders →") + "</nav>";
    kart.innerHTML = h;
    const govde = $("ders-govde"), kurulacak = [];
    if (Array.isArray(d.parcalar) && d.parcalar.length) {
      d.parcalar.forEach(function (p) {
        const el = dersParcaEl(p, kurulacak);
        if (el) govde.appendChild(el);
      });
    } else {
      // Eski biçim: düz markdown. Başlık zaten üstte; gövdenin ilk başlık satırı atlanır.
      const el = dersParcaMd(String(d.md || "").replace(/^#+[^\n]*\n*/, ""));
      el.classList.add("anlatim");
      govde.appendChild(el);
    }
    $("ders-liste-kart").classList.add("gizli");
    kart.classList.remove("gizli");
    kurulacak.forEach(dersEtkilesimKur);
    window.scrollTo(0, 0);
    try { $("ders-baslik").focus({ preventScroll: true }); } catch (e) { /* yoksay */ }
  }

  // Adres çubuğu: #ders/<id> → ders, #dersler → liste, diğerleri → sayfa. Geri/ileri düğmeleri de buradan geçer.
  function hashYonlendir() {
    let h = (location.hash || "").replace(/^#/, "");
    try { h = decodeURIComponent(h); } catch (e) { /* bozuk kodlama: olduğu gibi */ }
    if (h.indexOf("ders/") === 0) {
      sayfaGoster("dersler", true);
      const id = h.slice(5);
      (dersSoz || Promise.resolve()).then(function () {
        if (dersDurum.acik !== id || $("ders-kart").classList.contains("gizli")) dersAc(id);
      });
    } else if (h === "dersler") {
      sayfaGoster("dersler", true);
      dersListeGoster();
    } else if (h.indexOf("bina/") === 0) {
      // #bina/sablon/<ad> (derslerdeki "Bina sayfasında aç"): sayfa görünür olur; bina.js henüz kurulmadıysa kurulurken
      // adresi okur (hashKontrol), kurulduysa kendi hashchange dinleyicisi şablonu yükler.
      sayfaGoster("bina", true);
    } else if (h && $("sayfa-" + h)) {
      sayfaGoster(h, true);
    }
  }

  // ---------- Sayfalar, ayarlar, kurulum ----------
  // adresDokunma: yönlendirici (hashYonlendir) çağırıyorsa adres çubuğuna dokunulmaz; sekme düğmeleri açık dersi adreste korur.
  function sayfaGoster(ad, adresDokunma) {
    document.querySelectorAll(".sayfa").forEach(function (s) { s.classList.toggle("aktif", s.id === "sayfa-" + ad); });
    document.querySelectorAll(".alt-nav button").forEach(function (b) { b.classList.toggle("aktif", b.dataset.sayfa === ad); });
    if (ad === "yardim") { try { kisayolTablosu(); } catch (e) { /* yardım tablosu isteğe bağlı */ } }
    if (adresDokunma) return;
    const hedef = ad === "dersler" && dersDurum.acik != null ? dersBaglanti(dersDurum.acik) : "#" + ad;
    try { history.replaceState(null, "", hedef); } catch (e) { /* yoksay */ }
  }
  function temayiUygula() {
    const kok = document.documentElement;
    if (ayar.tema === "acik" || ayar.tema === "koyu") { kok.dataset.tema = ayar.tema; kok.style.colorScheme = ayar.tema === "koyu" ? "dark" : "light"; }
    else { delete kok.dataset.tema; kok.style.colorScheme = "light dark"; }
  }
  function ayarlariForma() {
    $("ayar-ondalik").checked = !!ayar.ondalik;
    $("ayar-basamak").value = ayar.basamak;
    $("ayar-kural").checked = !!ayar.kural;
    $("ayar-python").checked = !!ayar.python;
    $("ayar-sema").checked = ayar.sema !== false;
    $("ayar-eleman").value = ayar.en_fazla_eleman;
    $("ayar-tema").value = ayar.tema;
  }
  // Not: pencere kapanırken bu işlev iki kez çalışır (Tamam düğmesi + close olayı); ikinci çalışmada hiçbir şey değişmez.
  function ayarlariOku() {
    const eski = JSON.stringify([ayar.ondalik, ayar.basamak, ayar.en_fazla_eleman]);
    const eskiGorunum = JSON.stringify([ayar.kural, ayar.python, ayar.sema]);
    ayar.ondalik = $("ayar-ondalik").checked;
    ayar.basamak = Math.max(1, Math.min(12, parseInt($("ayar-basamak").value, 10) || 4));
    ayar.kural = $("ayar-kural").checked;
    ayar.python = $("ayar-python").checked;
    ayar.sema = $("ayar-sema").checked;
    ayar.en_fazla_eleman = Math.max(0, Math.min(400, parseInt($("ayar-eleman").value, 10) || 0));
    ayar.tema = $("ayar-tema").value;
    ayariKaydet();
    temayiUygula();
    // Görünümü etkileyen ayar değişmediyse anlatım yeniden çizilmez: oynayan ok şeması baştan başlamasın.
    if (JSON.stringify([ayar.kural, ayar.python, ayar.sema]) !== eskiGorunum) anlatimCiz();
    if (!durum.sonYanit || !durum.hazir) return;
    const sayiDegisti = JSON.stringify([ayar.ondalik, ayar.basamak, ayar.en_fazla_eleman]) !== eski;
    // Şema kapalıyken hesaplanan sonuçta şema bloğu yoktur: şema açılınca aynı hesap şemalı olarak yenilenir.
    // (Son istek zaten şema istediyse yeniden hesaplanmaz; eski motor şema üretmese de döngü oluşmaz.)
    const semaIstenecek = ayar.sema && !(durum.sonIstek && durum.sonIstek.ayarlar && durum.sonIstek.ayarlar.sema);
    if (sayiDegisti || semaIstenecek) hesapla();
  }
  function servisCalisaniKur() {
    if (!("serviceWorker" in navigator)) return;
    let kontrolVardi = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.register("sw.js").catch(function () { /* yerel dosya ya da desteklenmiyor */ });
    navigator.serviceWorker.addEventListener("controllerchange", function () {
      if (kontrolVardi) toast("Uygulama güncellendi.", "Yenile", function () { location.reload(); }, true);
      kontrolVardi = true;
    });
  }
  async function onbellegiSil() {
    try {
      if (window.caches) {
        const adlar = await caches.keys();
        await Promise.all(adlar.filter(function (k) { return k.indexOf("matris-ogren-") === 0; }).map(function (k) { return caches.delete(k); }));
      }
      if (navigator.serviceWorker) {
        const kayitlar = await navigator.serviceWorker.getRegistrations();
        await Promise.all(kayitlar.map(function (r) { return r.unregister(); }));
      }
    } catch (e) { /* yoksay */ }
    location.reload();
  }
  function kurulumuHazirla() {
    window.addEventListener("beforeinstallprompt", function (e) {
      e.preventDefault();
      durum.kurOlayi = e;
      $("kur-dugme-kutu").classList.remove("gizli");
    });
    $("kur").addEventListener("click", async function () {
      if (!durum.kurOlayi) return;
      durum.kurOlayi.prompt();
      try { await durum.kurOlayi.userChoice; } catch (e) { /* yoksay */ }
      durum.kurOlayi = null;
      $("kur-dugme-kutu").classList.add("gizli");
    });
    window.addEventListener("appinstalled", function () { toast("Matris Öğren yüklendi. Artık uygulama listenizde."); });
  }

  // ---------- Başlat ----------
  // Çözüm anlatımının olay delegasyonu: ok şeması denetimleri ve kod kopyalama (hesap sayfası ve ders kartı için ortak).
  function semaOlaylariBagla(kok) {
    kok.addEventListener("click", function (e) {
      const sd = e.target.closest("button[data-sema]");
      if (sd) { semaTikla(sd); return; }
      const m = e.target.closest("[data-kopyala-metin]");
      if (m) { kopyala(m.getAttribute("data-kopyala-metin") || ""); return; }
      const b = e.target.closest("[data-kopyala]");
      if (b) kopyala(kopyaMetinleri[+b.dataset.kopyala] || "");
    });
    kok.addEventListener("keydown", semaTus);     // oklu şema: ← → ile adım adım
    kok.addEventListener("focusin", semaOdak);    // klavyeyle odaklanınca otomatik oynatma durur
    ["touchstart", "wheel", "pointerdown"].forEach(function (ad) {   // sahneyi kendisi kaydıran kişi için kamera durur
      kok.addEventListener(ad, semaKameraBirak, { passive: true });
    });
  }
  function baslat() {
    temayiUygula();
    islemListesiniKur();
    islemSec(durum.islem);

    $("form").addEventListener("input", girdiyiSakla);
    $("form").addEventListener("submit", function (e) { e.preventDefault(); hesapla(); });
    $("form").addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); hesapla(); }
    });
    $("form").addEventListener("click", function (e) {
      const ekle = e.target.closest("[data-ekle]"), sil = e.target.closest("[data-sil]");
      if (ekle) {
        e.preventDefault();
        const g = girdiOku();
        if (ekle.dataset.ekle === "liste") { const l = g.matrisler || []; l.push(""); g.matrisler = l; }
        else { const l = g.elemanlar || []; l.push({ k: "", dof: "" }); g.elemanlar = l; }
        durum.girdiler[durum.islem] = g; girdileriKaydet(); formuKur();
      } else if (sil) {
        e.preventDefault();
        const g = girdiOku();
        if (sil.dataset.sil === "liste") { if ((g.matrisler || []).length > 2) g.matrisler.pop(); }
        else if ((g.elemanlar || []).length > 1) g.elemanlar.pop();
        durum.girdiler[durum.islem] = g; girdileriKaydet(); formuKur();
      }
    });
    $("hesapla").addEventListener("click", hesapla);
    $("ornek").addEventListener("click", function () {
      const islem = islemBul(durum.islem);
      durum.girdiler[islem.id] = JSON.parse(JSON.stringify(islem.ornek));
      girdileriKaydet(); formuKur();
    });
    $("temizle").addEventListener("click", function () {
      delete durum.girdiler[durum.islem]; girdileriKaydet(); formuKur();
    });
    document.querySelectorAll('input[name="gorunum"]').forEach(function (r) { r.addEventListener("change", anlatimCiz); });
    semaOlaylariBagla($("anlatim"));   // hesap sayfasındaki çözüm
    semaOlaylariBagla($("ders-kart")); // ders sayfasındaki örnek çözümleri (aynı çizici, aynı denetimler)
    document.querySelectorAll(".alt-nav button").forEach(function (b) {
      b.addEventListener("click", function () { sayfaGoster(b.dataset.sayfa); });
    });

    const dlg = $("ayarlar");
    $("ayarlar-ac").addEventListener("click", function () { ayarlariForma(); if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", ""); });
    $("ayar-kapat").addEventListener("click", function () { ayarlariOku(); if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); });
    dlg.addEventListener("close", ayarlariOku);
    $("motor-yenile").addEventListener("click", function () { if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); motoruBaslat(); });
    $("onbellek-sil").addEventListener("click", onbellegiSil);

    fetch("surum.json").then(function (r) { return r.ok ? r.json() : null; }).then(function (s) {
      if (s && s.surum) $("surum-etiketi").textContent = "v" + String(s.surum).slice(0, 7);
    }).catch(function () { /* yoksay */ });

    kurulumuHazirla();
    servisCalisaniKur();
    // Etkileşim kitaplığı (varsa) hesap motoruna bağlanır: şekil içindeki "motordan hesapla" düğmeleri aynı çiziciyi kullanır.
    if (window.Etkilesim && typeof Etkilesim.motorBagla === "function") {
      try { Etkilesim.motorBagla(motorIstegi, anlatimDersCiz); } catch (e) { /* kitaplık bağlanamazsa ders yine açılır */ }
    }
    dersSoz = dersleriYukle();
    window.addEventListener("hashchange", hashYonlendir);
    // Bina sayfası kurulunca (kendi kısayol bağlamaları kayda girer) açık Yardım sayfasındaki kısayol tablosu tazelenir
    window.addEventListener("matris-bina-hazir", function () {
      const y = $("sayfa-yardim");
      if (y && y.classList.contains("aktif")) { try { kisayolTablosu(); } catch (e) { /* yoksay */ } }
    });
    hashYonlendir();
    motoruBaslat();
  }
  // Bina sayfası (bina.js) bir sonlu eleman modelini (örn. G durumu) Sonlu eleman sayfasına aktarıp açar.
  // se.js kendini window.MatrisSE.modelYukle ile kaydeder; sayfa yüklenmemişse Türkçe hata fırlatılır.
  function seModelYukle(model) {
    if (!window.MatrisSE || typeof window.MatrisSE.modelYukle !== "function") throw new Error("Sonlu eleman sayfası yüklenmedi.");
    window.MatrisSE.modelYukle(model);
    sayfaGoster("se");
    window.scrollTo({ top: 0, behavior: "smooth" });
    toast("Model Sonlu eleman sayfasına aktarıldı.");
  }
  // Ek sayfa betikleri (se.js: sonlu eleman sayfası, bina.js: bina sayfası) için ortak, küçük ve dondurulmuş yüzey:
  // motor isteği, anlatım çizici, yardımcılar, sayfa geçişi ve sonlu eleman sayfasına model aktarımı.
  window.MatrisApp = Object.freeze({
    motorIstegi: motorIstegi, anlatimDersCiz: anlatimDersCiz, semaOlaylariBagla: semaOlaylariBagla,
    kacis: kacis, katexHtml: katexHtml, toast: toast, sayfaGoster: sayfaGoster, seModelYukle: seModelYukle,
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", baslat); else baslat();
})();
