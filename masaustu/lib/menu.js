/* Matris Öğren masaüstü — yerel menü çubuğu şablonu (saf veri; ana süreç Menu.buildFromTemplate ile kurar).
   Bu dosya elektronsuz da yüklenebilir: testler şablonu doğrudan inceler.

   Menü öğelerinin çoğu sayfaya bir KOMUT gönderir: ana süreç ctx.komut(ad, ek) çağırır, köprü (docs/masaustu_kopru.js)
   bunu pencerede `masaustu-komut` olayı olarak yayınlar. Yalnız pencereye/uygulamaya ait işler (yeni pencere, son dosyalar,
   yakınlaştırma, tam ekran, hakkında) ana süreçte yapılır. */
"use strict";

// Sayfa tarafında kendi klavye işleyicisi olan kısayollar (bina.js: Ctrl+Z/Y, Esc, Delete) menüde gösterilir ama menüye
// kaydedilmez (registerAccelerator: false); böylece tuş bir kez işlenir ve metin kutularındaki doğal geri alma bozulmaz.
const SAYFA_TUSU = { registerAccelerator: false };

function menuSablonu(ctx) {
  const mac = ctx.platform === "darwin";
  const ad = ctx.uygulamaAdi || "Matris Öğren";
  const komut = function (etiket, kmt, hizlandirici, ek, secenek) {
    const oge = Object.assign({ label: etiket, id: "komut:" + kmt + (ek && ek.sayfa ? ":" + ek.sayfa : ""),
      click: function () { ctx.komut(kmt, ek || null); } }, secenek || {});
    if (hizlandirici) oge.accelerator = hizlandirici;
    return oge;
  };
  const ayrac = { type: "separator" };
  const yerel = ctx.yerel || {};
  const son = (ctx.sonDosyalar || []).slice(0, 10);
  const sonMenu = son.length
    ? son.map(function (yol, i) {
      return { label: (i < 9 ? "&" + (i + 1) + "  " : "    ") + yol.replace(/&/g, "&&"), click: function () { yerel.sonDosyaAc(yol); } };
    }).concat([ayrac, { label: "Listeyi temizle", click: function () { yerel.sonDosyalariTemizle(); } }])
    : [{ label: "(boş)", enabled: false }];

  const dosya = {
    label: "&Dosya",
    submenu: [
      komut("Yeni proje", "yeni", "CmdOrCtrl+N"),
      { label: "Yeni pencere", accelerator: "CmdOrCtrl+Shift+N", click: function () { yerel.yeniPencere(); } },
      ayrac,
      komut("Aç…", "ac", "CmdOrCtrl+O"),
      { label: "Son dosyalar", id: "son-dosyalar", submenu: sonMenu },
      ayrac,
      komut("Kaydet", "kaydet", "CmdOrCtrl+S"),
      komut("Farklı kaydet…", "farkli-kaydet", "CmdOrCtrl+Shift+S"),
      ayrac,
      { label: "Dışa aktar", submenu: [
        komut("IFC yapı modeli (.ifc)…", "ifc", "CmdOrCtrl+E"),
        komut("Tablolar (.csv)…", "csv"),
        komut("Bina verisi (.json)…", "json-disari"),
        komut("Statik rapor (.html)…", "rapor-html"),
      ] },
      komut("Raporu PDF olarak kaydet…", "rapor-pdf", "CmdOrCtrl+P"),
      ayrac,
      { label: "Kurtarma klasörünü göster", click: function () { yerel.kurtarmaKlasoru(); } },
      ayrac,
      { label: "Pencereyi kapat", role: "close", accelerator: "CmdOrCtrl+W" },
    ].concat(mac ? [] : [{ label: "Çıkış", role: "quit", accelerator: "Ctrl+Q" }]),
  };

  const duzen = {
    label: "D&üzen",
    submenu: [
      komut("Geri al", "geri-al", "CmdOrCtrl+Z", null, SAYFA_TUSU),
      komut("Yinele", "yinele", mac ? "Shift+Cmd+Z" : "Ctrl+Y", null, SAYFA_TUSU),
      ayrac,
      { label: "Kes", role: "cut" },
      { label: "Kopyala", role: "copy" },
      { label: "Yapıştır", role: "paste" },
      { label: "Tümünü seç", role: "selectAll" },
      ayrac,
      komut("Seçileni sil", "sil", "Delete", null, SAYFA_TUSU),
      komut("Seçimi bırak", "secimi-birak", "Esc", null, SAYFA_TUSU),
      ayrac,
      komut("Ayarlar…", "ayarlar", "CmdOrCtrl+,"),
    ],
  };

  const gorunum = {
    label: "&Görünüm",
    submenu: [
      komut("Hesapla", "sayfa", "CmdOrCtrl+1", { sayfa: "hesap" }),
      komut("Dersler", "sayfa", "CmdOrCtrl+2", { sayfa: "dersler" }),
      komut("Sonlu eleman", "sayfa", "CmdOrCtrl+3", { sayfa: "se" }),
      komut("Bina", "sayfa", "CmdOrCtrl+4", { sayfa: "bina" }),
      ayrac,
      komut("3B görünüm", "gorunum-3b"),
      komut("Plan (üstten)", "gorunum-plan"),
      komut("Önden", "gorunum-on"),
      komut("Yandan", "gorunum-yan"),
      komut("Modeli sığdır", "sigdir", "CmdOrCtrl+Shift+F"),
      komut("Araç kutuları", "arac-kutulari", "CmdOrCtrl+Shift+T"),
      ayrac,
      { label: "Yakınlaştır", role: "zoomIn", accelerator: "CmdOrCtrl+=" },
      { label: "Uzaklaştır", role: "zoomOut", accelerator: "CmdOrCtrl+-" },
      { label: "Gerçek boyut", role: "resetZoom", accelerator: "CmdOrCtrl+0" },
      ayrac,
      { label: "Tam ekran", id: "tam-ekran", accelerator: mac ? "Ctrl+Cmd+F" : "F11", click: function () { yerel.tamEkran(); } },
      ayrac,
      { label: "Yeniden yükle", role: "forceReload", accelerator: "CmdOrCtrl+Shift+R" },
      { label: "Geliştirici araçları", role: "toggleDevTools", accelerator: mac ? "Alt+Cmd+I" : "Ctrl+Shift+I" },
    ],
  };

  const cizim = {
    label: "&Çizim",
    submenu: [
      komut("Seç", "secim-kipi"),
      ayrac,
      komut("Düğüm ekle", "dugum-ekle"),
      komut("Çubuk çiz", "cubuk-ciz"),
      komut("Kolon ekle", "kolon-ekle"),
      komut("Kiriş ekle", "kiris-ekle"),
      komut("Döşeme / panel ekle", "doseme-ekle"),
      ayrac,
      komut("Aksları düzenle…", "aks-duzenle"),
      komut("Katları düzenle…", "kat-duzenle"),
      komut("Şablondan bina…", "sablon"),
      ayrac,
      komut("Izgarayı göster/gizle", "izgara"),
      komut("Yakalamayı aç/kapat", "yakalama"),
    ],
  };

  const analiz = {
    label: "&Analiz",
    submenu: [
      komut("Çöz", "coz", "F5"),
      ayrac,
      komut("Yük durumları…", "yuk-durumlari"),
      komut("Yük birleşimleri…", "kombinasyonlar"),
      komut("Deprem parametreleri…", "deprem"),
      ayrac,
      komut("Tablolar", "tablolar", "CmdOrCtrl+T"),
      komut("Isı haritası", "isi-haritasi"),
      ayrac,
      komut("Sonuçları temizle", "sonuclari-temizle"),
    ],
  };

  const tasarim = {
    label: "&Tasarım",
    submenu: [
      komut("Tüm kontroller", "tasarim-kontrol", "F6"),
      ayrac,
      komut("Betonarme kesitler", "betonarme"),
      komut("Çelik elemanlar", "celik"),
      komut("Temeller", "temel"),
    ],
  };

  const rapor = {
    label: "&Rapor",
    submenu: [
      komut("Statik hesap raporu", "rapor", "F9"),
      komut("Proje bilgileri…", "proje-bilgileri"),
      ayrac,
      komut("PDF olarak kaydet…", "rapor-pdf"),
      komut("HTML olarak kaydet…", "rapor-html"),
      komut("Yazdır…", "yazdir"),
      ayrac,
      komut("IFC dışa aktar…", "ifc"),
      komut("Tabloları CSV kaydet…", "csv"),
    ],
  };

  const yardim = {
    label: "&Yardım",
    role: "help",
    submenu: [
      komut("Dersler", "sayfa", "F1", { sayfa: "dersler" }),
      komut("Kullanım kılavuzu", "sayfa", null, { sayfa: "yardim" }),
      { label: "Klavye kısayolları", click: function () { yerel.kisayollar(); } },
      ayrac,
      { label: "Web sürümünü aç", click: function () { yerel.harici("https://chazman0.github.io/matris-ogren/"); } },
      { label: "Kaynak kodu", click: function () { yerel.harici("https://github.com/chazman0/matris-ogren"); } },
      ayrac,
      { label: ad + " hakkında", click: function () { yerel.hakkinda(); } },
    ],
  };

  const sablon = [dosya, duzen, gorunum, cizim, analiz, tasarim, rapor, yardim];
  if (mac) {
    sablon.unshift({
      label: ad,
      submenu: [
        { label: ad + " hakkında", click: function () { yerel.hakkinda(); } },
        ayrac,
        komut("Ayarlar…", "ayarlar"),
        ayrac,
        { label: ad + " gizle", role: "hide" },
        { label: "Diğerlerini gizle", role: "hideOthers" },
        { label: "Tümünü göster", role: "unhide" },
        ayrac,
        { label: ad + " uygulamasından çık", role: "quit", accelerator: "Cmd+Q" },
      ],
    });
    sablon.push({ label: "Pencere", role: "windowMenu", submenu: [
      { label: "Simge durumuna küçült", role: "minimize" },
      { label: "Yakınlaştır", role: "zoom" },
      ayrac,
      { label: "Tümünü öne getir", role: "front" },
    ] });
  }
  return sablon;
}

// Şablondaki komutların düz listesi (belgeler ve testler için): [{komut, etiket, menu, kisayol, ek}]
function komutListesi(platform) {
  const liste = [];
  const gez = function (ogeler, menu) {
    ogeler.forEach(function (o) {
      if (o.submenu) gez(o.submenu, menu || o.label.replace(/&/g, ""));
      else if (o.id && o.id.indexOf("komut:") === 0) {
        const p = o.id.split(":");
        liste.push({ komut: p[1], etiket: o.label, menu: menu, kisayol: o.accelerator || "", ek: p[2] ? { sayfa: p[2] } : null });
      }
    });
  };
  gez(menuSablonu({ platform: platform || "linux", komut: function () {}, yerel: {} }), "");
  return liste;
}

// Klavye kısayolları tablosu (Yardım > Klavye kısayolları penceresi)
function kisayolMetni(platform) {
  const mac = platform === "darwin";
  const goster = function (h) { return h.replace("CmdOrCtrl", mac ? "⌘" : "Ctrl").replace("Cmd", "⌘").replace("Shift", mac ? "⇧" : "Shift"); };
  const gorulen = new Set();
  const satirlar = [];
  komutListesi(platform).forEach(function (k) {
    if (!k.kisayol || gorulen.has(k.kisayol)) return;
    gorulen.add(k.kisayol);
    satirlar.push(goster(k.kisayol) + "\t" + k.etiket + (k.menu ? "  (" + k.menu + ")" : ""));
  });
  satirlar.push(goster(mac ? "Ctrl+Cmd+F" : "F11") + "\tTam ekran");
  satirlar.push(goster("CmdOrCtrl+Shift+N") + "\tYeni pencere");
  return satirlar.join("\n");
}

module.exports = { menuSablonu: menuSablonu, komutListesi: komutListesi, kisayolMetni: kisayolMetni };
