/* Matris Öğren — uygulama mantığı: form, Python motoruyla (motor.worker.js) iletişim, çizim, ayarlar, kurulum. */
"use strict";

(function () {
  const $ = function (id) { return document.getElementById(id); };
  const AYAR_ANAHTAR = "matris-ogren-ayarlar";
  const GIRDI_ANAHTAR = "matris-ogren-girdiler";
  const VARSAYILAN_AYAR = { ondalik: false, basamak: 4, kural: true, python: true, en_fazla_eleman: 36, tema: "otomatik" };

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
        { ad: "sabit", tur: "metin", etiket: "Sabit (mesnetli) serbestlikler, örn. 1 3" },
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
      return katex.renderToString(tex, { displayMode: !!blok, throwOnError: false, strict: "ignore", trust: false });
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
  function hazirGoster(h) {
    durum.hazir = h;
    $("hesapla").disabled = !h;
    if (h) {
      $("yukleme").classList.add("gizli");
      durumYaz("Hazır ✓", "hazir");
    }
  }
  function motorHata(mesaj) {
    hazirGoster(false);
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
  function bloklariSec(bloklar) {
    const mod = gorunum();
    return bloklar.filter(function (b) {
      if (b.etiket === "python") return mod === "python" || (mod === "hepsi" && ayar.python);
      if (b.etiket === "kural") return mod !== "python" && ayar.kural;
      return mod !== "python";
    });
  }
  let kopyaMetinleri = [];
  function anlatimCiz() {
    const y = durum.sonYanit;
    if (!y || y.hata) return;
    kopyaMetinleri = [];
    const parcalar = bloklariSec(y.bloklar || []).map(function (b) {
      if (b.tur === "kod") {
        const i = kopyaMetinleri.push(b.kod) - 1;
        return '<div class="kod-baslik">' + kacis(b.baslik || "🐍 Python ile") +
          ' <button type="button" class="dugme kucuk" data-kopyala="' + i + '">Kodu kopyala</button></div>' +
          '<pre class="kod">' + kacis(b.kod) + "</pre>" +
          (b.cikti ? '<div class="kod-baslik">Çıktı:</div><pre class="kod cikti">' + kacis(b.cikti) + "</pre>" : "");
      }
      if (b.tur === "math") return "<div>" + katexHtml(b.icerik, true) + "</div>";
      return mdRender(b.icerik);
    });
    $("anlatim").innerHTML = parcalar.join("\n") || '<p class="not">Bu görünümde gösterilecek bölüm yok.</p>';
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
      ayarlar: { ondalik: !!ayar.ondalik, basamak: +ayar.basamak || 4, en_fazla_eleman: +ayar.en_fazla_eleman || 0 },
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
      if (y && !y.hata && y.bloklar && y.bloklar.length) $("yardim-fonksiyonlar").innerHTML = mdRender(y.bloklar[0].icerik);
    } catch (e) { /* yardım isteğe bağlı */ }
  }

  // ---------- Dersler ----------
  async function dersleriYukle() {
    const kutu = $("dersler");
    try {
      const r = await fetch("dersler.json");
      if (!r.ok) throw new Error(r.status);
      const liste = await r.json();
      kutu.innerHTML = "";
      if (!liste.length) { kutu.innerHTML = '<p class="not">Ders içeriği bulunamadı.</p>'; return; }
      liste.forEach(function (ders) {
        const det = document.createElement("details");
        det.className = "katlanir ders";
        // "anlatim" sınıfı: ders gövdesi de çözüm anlatımıyla aynı stili (formül/tablo yana kaydırma) alır.
        det.innerHTML = "<summary>" + mdRender(ders.baslik, true) + '</summary><div class="icerik anlatim"></div>';
        det.addEventListener("toggle", function () {
          if (det.open && !det.dataset.cizildi) {
            // Başlık zaten özette; gövdenin ilk başlık satırı atlanır.
            det.querySelector(".icerik").innerHTML = mdRender(String(ders.md || "").replace(/^#+[^\n]*\n*/, ""));
            det.dataset.cizildi = "1";
          }
        });
        kutu.appendChild(det);
      });
    } catch (e) { kutu.innerHTML = '<p class="not">Dersler yüklenemedi (' + kacis(e.message) + ").</p>"; }
  }

  // ---------- Sayfalar, ayarlar, kurulum ----------
  function sayfaGoster(ad) {
    document.querySelectorAll(".sayfa").forEach(function (s) { s.classList.toggle("aktif", s.id === "sayfa-" + ad); });
    document.querySelectorAll(".alt-nav button").forEach(function (b) { b.classList.toggle("aktif", b.dataset.sayfa === ad); });
    try { history.replaceState(null, "", "#" + ad); } catch (e) { /* yoksay */ }
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
    $("ayar-eleman").value = ayar.en_fazla_eleman;
    $("ayar-tema").value = ayar.tema;
  }
  function ayarlariOku() {
    const eski = JSON.stringify([ayar.ondalik, ayar.basamak, ayar.en_fazla_eleman]);
    ayar.ondalik = $("ayar-ondalik").checked;
    ayar.basamak = Math.max(1, Math.min(12, parseInt($("ayar-basamak").value, 10) || 4));
    ayar.kural = $("ayar-kural").checked;
    ayar.python = $("ayar-python").checked;
    ayar.en_fazla_eleman = Math.max(0, Math.min(400, parseInt($("ayar-eleman").value, 10) || 0));
    ayar.tema = $("ayar-tema").value;
    ayariKaydet();
    temayiUygula();
    anlatimCiz();
    if (JSON.stringify([ayar.ondalik, ayar.basamak, ayar.en_fazla_eleman]) !== eski && durum.sonYanit && durum.hazir) hesapla();
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
  function baslat() {
    temayiUygula();
    islemListesiniKur();
    const ilk = (location.hash || "").replace("#", "");
    if (ilk && $("sayfa-" + ilk)) sayfaGoster(ilk);
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
    $("anlatim").addEventListener("click", function (e) {
      const b = e.target.closest("[data-kopyala]");
      if (b) kopyala(kopyaMetinleri[+b.dataset.kopyala] || "");
    });
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
    dersleriYukle();
    motoruBaslat();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", baslat); else baslat();
})();
