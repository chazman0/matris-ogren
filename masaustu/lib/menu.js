/* Matris Öğren masaüstü — yerel menü çubuğu şablonu (saf veri; ana süreç Menu.buildFromTemplate ile kurar).
   Bu dosya masaüstü çatısı olmadan da yüklenebilir: testler şablonu doğrudan inceler.

   Menü öğelerinin çoğu sayfaya bir KOMUT gönderir: ana süreç ctx.komut(ad, ek, pencere) çağırır, köprü
   (docs/masaustu_kopru.js) bunu pencerede `masaustu-komut` olayı olarak yayınlar. Yalnız pencereye/uygulamaya ait işler
   (aç, yeni pencere, son dosyalar, yakınlaştırma, tam ekran, hakkında) ana süreçte yapılır. */
"use strict";

// Sayfanın kendi klavye işleyicisi olan tuşlar (bina sayfası: Ctrl+Z/Y, Delete, Esc, PgUp/PgDn) menüde gösterilir ama
// sisteme kaydedilmez (registerAccelerator: false): tuş sayfaya ulaşır, metin kutularındaki doğal davranış bozulmaz.
const SAYFA_TUSU = { registerAccelerator: false };

function menuSablonu(ctx) {
  const mac = ctx.platform === "darwin";
  const ad = ctx.uygulamaAdi || "Matris Öğren";
  const yerel = ctx.yerel || {};
  const yerelIs = function (isAdi) {
    return function (_oge, pencere) { if (typeof yerel[isAdi] === "function") yerel[isAdi](pencere); };
  };
  const komut = function (etiket, kmt, hizlandirici, ek, secenek) {
    const oge = Object.assign({
      label: etiket,
      id: "komut:" + kmt + (ek && ek.sayfa ? ":" + ek.sayfa : ""),
      click: function (_oge, pencere) { ctx.komut(kmt, ek || null, pencere); },
    }, secenek || {});
    if (hizlandirici) oge.accelerator = hizlandirici;
    return oge;
  };
  const ayrac = { type: "separator" };
  const son = (ctx.sonDosyalar || []).slice(0, 10);
  const sonMenu = son.length
    ? son.map(function (yol, i) {
      return {
        label: (i < 9 ? "&" + (i + 1) + "  " : "    ") + String(yol).replace(/&/g, "&&"),
        click: function (_oge, pencere) { if (yerel.sonDosyaAc) yerel.sonDosyaAc(yol, pencere); },
      };
    }).concat([ayrac, { label: "Listeyi temizle", click: yerelIs("sonDosyalariTemizle") }])
    : [{ label: "(boş)", enabled: false }];

  const dosya = {
    label: "&Dosya",
    submenu: [
      komut("Yeni proje", "yeni", "CmdOrCtrl+N"),
      { label: "Yeni pencere", accelerator: "CmdOrCtrl+Shift+N", click: yerelIs("yeniPencere") },
      ayrac,
      { label: "Aç…", id: "ac", accelerator: "CmdOrCtrl+O", click: yerelIs("ac") },
      { label: "Son dosyalar", id: "son-dosyalar", submenu: sonMenu },
      ayrac,
      komut("Kaydet", "kaydet", "CmdOrCtrl+S"),
      komut("Farklı kaydet…", "farkli-kaydet", "CmdOrCtrl+Shift+S"),
      ayrac,
      // Tablolar (.csv): tablo editörü açılır ve CSV dosyası seçtirilir; değişen hücreler bekleyen değişiklik olur (Uygula ile modele).
      { label: "İçe aktar", submenu: [
        komut("Bina verisi (.json)…", "json-iceri"),
        komut("Tablolar (.csv)…", "csv-iceri"),
      ] },
      { label: "Dışa aktar", submenu: [
        komut("IFC yapı modeli (.ifc)…", "ifc", "CmdOrCtrl+E"),
        komut("Tablolar (.csv)…", "csv"),
        komut("Bina verisi (.json)…", "json-disari"),
        komut("Statik rapor (.html)…", "rapor-html"),
        komut("Görünüm resmi (.png)…", "resim"),
      ] },
      komut("Raporu PDF olarak kaydet…", "rapor-pdf", "CmdOrCtrl+P"),
      ayrac,
      { label: "Kurtarma klasörünü göster", click: yerelIs("kurtarmaKlasoru") },
      ayrac,
      { label: "Pencereyi kapat", role: "close", accelerator: "CmdOrCtrl+W" },
    ].concat(mac ? [] : [{ label: "Çıkış", role: "quit", accelerator: "Ctrl+Q" }]),
  };

  const duzen = {
    label: "D&üzen",
    submenu: [
      // macOS'ta tuş önce sayfaya gider; sayfa işlemezse (ör. metin kutusu) menü komutu çalışır ve köprü metni geri alır.
      komut("Geri al", "geri-al", "CmdOrCtrl+Z", null, mac ? null : SAYFA_TUSU),
      komut("Yinele", "yinele", mac ? "Shift+Cmd+Z" : "Ctrl+Y", null, mac ? null : SAYFA_TUSU),
      ayrac,
      { label: "Kes", role: "cut" },
      { label: "Kopyala", role: "copy" },
      { label: "Yapıştır", role: "paste" },
      { label: "Tümünü seç", role: "selectAll" },
      ayrac,
      komut("Elemanları kopyala", "eleman-kopyala"),
      komut("Elemanları yapıştır", "eleman-yapistir"),
      komut("Seçileni sil", "sil", "Delete", null, SAYFA_TUSU),
      komut("Seçimi bırak", "secimi-birak", "Esc", null, SAYFA_TUSU),
      ayrac,
      komut("Taşı…", "tasi"),
      komut("Döndür…", "dondur"),
      komut("Ayna…", "ayna"),
      komut("Doğrusal dizi…", "dizi"),
      ayrac,
      komut("Özellik ata…", "ozellik-ata"),
      komut("Uç serbestlikleri (mafsal)…", "mafsal"),
      komut("Yalnız çekme", "yalniz-cekme"),
      ayrac,
      komut("Böl…", "bol"),
      komut("Kesişimlerde böl", "kesisimde-bol"),
      komut("Birleştir", "birlestir"),
      komut("Düğümleri birleştir", "dugum-birlestir"),
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
      komut("Plan (seçili Z aksında)", "gorunum-plan"),
      komut("Önden (seçili Y aksında)", "gorunum-on"),
      komut("Yandan (seçili X aksında)", "gorunum-yan"),
      komut("Modeli sığdır", "sigdir", "CmdOrCtrl+Shift+F"),
      ayrac,
      komut("Kat süzgeci…", "kat-suzgeci"),
      komut("Seçileni yalıt", "yalit"),
      komut("Tümünü göster", "tumunu-goster"),
      komut("Tel kafes / katı", "tel-kafes"),
      komut("Etiketler", "etiketler"),
      ayrac,
      { label: "Araç kutuları", submenu: [
        komut("Araç kutularını göster / gizle", "arac-kutulari", "CmdOrCtrl+Shift+T"),
        komut("Özelleştir…", "arac-ozellestir"),
        komut("Varsayılan yerleşime dön", "arac-varsayilan"),
        ayrac,
        komut("Yerleşimi dışa aktar…", "arac-disari"),
        komut("Yerleşimi içe aktar…", "arac-iceri"),
      ] },
      ayrac,
      { label: "Yakınlaştır", role: "zoomIn", accelerator: "CmdOrCtrl+=" },
      { label: "Uzaklaştır", role: "zoomOut", accelerator: "CmdOrCtrl+-" },
      { label: "Gerçek boyut", role: "resetZoom", accelerator: "CmdOrCtrl+0" },
      // Görünmez eşdeğerler: "=" tuşu olmayan klavyeler (Türkçe Q/F) ve sayısal tuş takımı için
      { label: "Yakınlaştır (+)", role: "zoomIn", accelerator: "CmdOrCtrl+Plus", visible: false },
      { label: "Yakınlaştır (sayısal +)", role: "zoomIn", accelerator: "CmdOrCtrl+numadd", visible: false },
      { label: "Uzaklaştır (sayısal −)", role: "zoomOut", accelerator: "CmdOrCtrl+numsub", visible: false },
      { label: "Gerçek boyut (sayısal 0)", role: "resetZoom", accelerator: "CmdOrCtrl+num0", visible: false },
      ayrac,
      { label: "Tam ekran", id: "tam-ekran", accelerator: mac ? "Ctrl+Cmd+F" : "F11", click: yerelIs("tamEkran") },
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
      komut("Çubuk çiz (iki kesişim)", "cubuk-ciz"),
      komut("Hızlı çubuk (aks parçası)", "hizli-cubuk"),
      komut("Hızlı kolon", "kolon-ekle"),
      komut("Hızlı kiriş", "kiris-ekle"),
      komut("Hızlı çapraz…", "capraz-ekle"),
      komut("Hızlı panel / döşeme", "doseme-ekle"),
      komut("Eğik çubuk", "egik-cubuk"),
      ayrac,
      { label: "Üreteçler", submenu: [
        komut("Makas…", "uretec-makas"),
        komut("Beşik çerçeve…", "uretec-cerceve"),
        komut("Aşıklar…", "uretec-asik"),
        komut("Kren yolu…", "uretec-kren"),
      ] },
      komut("Şablondan bina…", "sablon"),
      ayrac,
      komut("Mesnet ata…", "mesnet-ata"),
      komut("Yük ata…", "yuk-ata"),
      ayrac,
      { label: "Ölç", submenu: [
        komut("Uzaklık", "olc-uzaklik"),
        komut("Açı", "olc-aci"),
        komut("Alan", "olc-alan"),
        komut("Kot farkı", "olc-kot"),
        komut("Koordinat sorgula", "olc-koordinat"),
        ayrac,
        komut("Ölçüleri temizle", "olc-temizle"),
      ] },
      ayrac,
      komut("Kesişimlere yakalama", "yakalama"),
    ],
  };

  const aks = {
    label: "&Aks",
    submenu: [
      komut("Hızlı aks (yeni model)…", "aks-hizli"),
      komut("Aks verisini düzenle…", "aks-duzenle", "CmdOrCtrl+G"),
      komut("Katları düzenle…", "kat-duzenle"),
      ayrac,
      komut("Aks ekle…", "aks-ekle"),
      komut("Aks sil…", "aks-sil"),
      komut("Elemanlar akslara yapışık", "aks-yapisik"),
      ayrac,
      komut("Ek aks sistemi ekle…", "aks-sistemi-ekle"),
      komut("Aks sistemlerini düzenle…", "aks-sistemleri"),
      komut("Görünür aks sistemi…", "aks-sistemi-sec"),
      ayrac,
      komut("Bir üst aks", "aks-yukari", "PageUp", null, SAYFA_TUSU),
      komut("Bir alt aks", "aks-asagi", "PageDown", null, SAYFA_TUSU),
      ayrac,
      komut("Aks ızgarasını göster / gizle", "izgara"),
      komut("Aks balonları", "aks-balon"),
      komut("Ölçü zinciri", "aks-olcu"),
    ],
  };

  const analiz = {
    label: "A&naliz",
    submenu: [
      komut("Çöz", "coz", "F5"),
      ayrac,
      komut("Yük durumları…", "yuk-durumlari"),
      komut("Yük birleşimleri…", "kombinasyonlar"),
      komut("Deprem parametreleri…", "deprem"),
      komut("Kar ve rüzgâr…", "kar-ruzgar"),
      ayrac,
      komut("Tablolar (düzenle, yapıştır)…", "tablolar", "CmdOrCtrl+T"),
      komut("Isı haritası", "isi-haritasi", "CmdOrCtrl+Shift+H"),
      komut("Yük akışı", "yuk-akisi"),
      komut("Şekil değiştirmiş biçim", "sekil-degistirme"),
      ayrac,
      komut("Sonuçları temizle", "sonuclari-temizle"),
    ],
  };

  const tasarim = {
    label: "&Tasarım",
    submenu: [
      komut("Tüm kontroller", "tasarim-kontrol", "F6"),
      ayrac,
      komut("Betonarme kiriş ve kolonlar", "betonarme"),
      komut("Çelik elemanlar", "celik"),
      komut("Temeller", "temel"),
      ayrac,
      komut("Kesit öner ve uygula", "kesit-oner"),
      komut("Metraj", "metraj"),
    ],
  };

  const rapor = {
    label: "&Rapor",
    submenu: [
      komut("Statik hesap raporu", "rapor", "F9"),
      komut("Proje bilgileri…", "proje-bilgileri"),
      komut("Rapor içeriği…", "rapor-icerik"),
      ayrac,
      komut("PDF olarak kaydet…", "rapor-pdf"),
      komut("HTML olarak kaydet…", "rapor-html"),
      komut("Yazdır…", "yazdir", "CmdOrCtrl+Shift+P"),
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
      { label: "Klavye kısayolları", click: yerelIs("kisayollar") },
      ayrac,
      { label: "Web sürümünü aç", click: function () { if (yerel.harici) yerel.harici("https://chazman0.github.io/matris-ogren/"); } },
      { label: "Kaynak kodu", click: function () { if (yerel.harici) yerel.harici("https://github.com/chazman0/matris-ogren"); } },
      ayrac,
      { label: ad + " hakkında", click: yerelIs("hakkinda") },
    ],
  };

  const sablon = [dosya, duzen, gorunum, cizim, aks, analiz, tasarim, rapor, yardim];
  if (mac) {
    sablon.unshift({
      label: ad,
      submenu: [
        { label: ad + " hakkında", click: yerelIs("hakkinda") },
        ayrac,
        komut("Ayarlar…", "ayarlar"),
        ayrac,
        { label: ad + " uygulamasını gizle", role: "hide" },
        { label: "Diğerlerini gizle", role: "hideOthers" },
        { label: "Tümünü göster", role: "unhide" },
        ayrac,
        { label: ad + " uygulamasından çık", role: "quit", accelerator: "Cmd+Q" },
      ],
    });
    sablon.push({ label: "Pencere", role: "windowMenu", submenu: [
      { label: "Simge durumuna küçült", role: "minimize" },
      { label: "Büyüt", role: "zoom" },
      ayrac,
      { label: "Tümünü öne getir", role: "front" },
    ] });
  }
  return sablon;
}

// Şablondaki sayfa komutlarının düz listesi (belgeler ve testler için): [{komut, etiket, menu, kisayol, ek, sayfaTusu}]
function komutListesi(platform) {
  const liste = [];
  const gez = function (ogeler, menu) {
    ogeler.forEach(function (o) {
      if (o.submenu) gez(o.submenu, menu || String(o.label).replace(/&/g, ""));
      else if (o.id && o.id.indexOf("komut:") === 0) {
        const p = o.id.split(":");
        liste.push({ komut: p[1], etiket: o.label, menu: menu, kisayol: o.accelerator || "", ek: p[2] ? { sayfa: p[2] } : null,
          sayfaTusu: o.registerAccelerator === false });
      }
    });
  };
  gez(menuSablonu({ platform: platform || "linux", komut: function () {}, yerel: {} }), "");
  return liste;
}

function kisayolGoster(h, mac) {
  const ad = { CmdOrCtrl: mac ? "⌘" : "Ctrl", Cmd: "⌘", Ctrl: mac ? "⌃" : "Ctrl", Shift: mac ? "⇧" : "Shift", Alt: mac ? "⌥" : "Alt",
    PageUp: "PgUp", PageDown: "PgDn" };
  return String(h).split("+").map(function (p) { return ad[p] || p; }).join(mac ? "" : "+");
}

// Sayfadan gelen kısayol listesinin sınırları (sözleşme C22): en çok 400 satır, her alan en çok 120 karakterlik metin.
const KISAYOL_SATIR_SINIRI = 400;
const KISAYOL_METIN_SINIRI = 120;

// Sayfanın gönderdiği kısayol listesi ([{tus, ad, grup}]) → temiz liste. Dizi değilse boş liste; tus ve ad dolu metin, grup metin
// olmalı ve hiçbiri 120 karakteri aşmamalı, yoksa satır atılır; denetim karakterleri boşluk olur; en çok 400 satır.
// preload.js aynı kuralı kendi içinde uygular (yalıtılmış ön yükleme betiği yerel modül yükleyemez); ana süreç yine de temizler.
function kisayolListesiTemizle(liste) {
  const sonuc = [];
  if (!Array.isArray(liste)) return sonuc;
  const n = Math.min(liste.length, KISAYOL_SATIR_SINIRI * 10);
  for (let i = 0; i < n && sonuc.length < KISAYOL_SATIR_SINIRI; i++) {
    const s = liste[i];
    if (!s || typeof s !== "object") continue;
    const alan = [s.tus, s.ad, s.grup];
    if (!alan.every(function (x) { return typeof x === "string" && x.length <= KISAYOL_METIN_SINIRI; })) continue;
    const temiz = alan.map(function (x) { return x.replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]+/g, " ").trim(); });
    if (!temiz[0] || !temiz[1]) continue;
    sonuc.push({ tus: temiz[0], ad: temiz[1], grup: temiz[2] });
  }
  return sonuc;
}

// Klavye kısayolları penceresinin (Yardım › Klavye kısayolları) metni.
// - sayfaListesi yoksa (Bina sayfası bu pencerede henüz hazır olmadıysa): menü kısayolları ve Bina sayfasının araç kısayollarının
//   nerede olduğunu söyleyen son satır.
// - sayfaListesi ([{tus, ad, grup}], masaustu_kopru.js'in gönderdiği, araç kutusu komut kaydı + sayfa tuşları) varsa: "Menü" bölümü
//   (aynı menü satırları) ve her grup için "Bina sayfası — <grup>" bölümü, satırlar "<tus>  <ad>"; gruplar listedeki ilk görünme
//   sırasıyla.
function kisayolMetni(platform, sayfaListesi) {
  const mac = platform === "darwin";
  const gorulen = new Set();
  const satirlar = [];
  const ekle = function (h, etiket) {
    if (!h || gorulen.has(h)) return;
    gorulen.add(h);
    satirlar.push(kisayolGoster(h, mac) + "  —  " + etiket);
  };
  ekle("CmdOrCtrl+O", "Aç (Dosya)");
  ekle("CmdOrCtrl+Shift+N", "Yeni pencere (Dosya)");
  komutListesi(platform).forEach(function (k) { ekle(k.kisayol, k.etiket + (k.menu ? " (" + k.menu + ")" : "")); });
  ekle(mac ? "Ctrl+Cmd+F" : "F11", "Tam ekran (Görünüm)");
  ekle("CmdOrCtrl+=", "Yakınlaştır (Görünüm)");
  ekle("CmdOrCtrl+-", "Uzaklaştır (Görünüm)");
  ekle("CmdOrCtrl+0", "Gerçek boyut (Görünüm)");
  const liste = kisayolListesiTemizle(sayfaListesi);
  if (!liste.length) {
    satirlar.push("", "Bina sayfasındaki araç kısayolları (S seç, L çubuk çiz, K kolon, Ctrl+Enter çöz…): Yardım › Kullanım kılavuzu " +
      "sayfasındaki Klavye kısayolları kartı ya da Bina sayfasında ? tuşu.");
    return satirlar.join("\n");
  }
  const gruplar = [], grupSatir = {};
  liste.forEach(function (s) {
    const g = s.grup || "Diğer";
    if (!grupSatir[g]) { grupSatir[g] = []; gruplar.push(g); }
    grupSatir[g].push(s.tus + "  " + s.ad);
  });
  const metin = ["Menü"].concat(satirlar);
  gruplar.forEach(function (g) { metin.push("", "Bina sayfası — " + g); Array.prototype.push.apply(metin, grupSatir[g]); });
  return metin.join("\n");
}

module.exports = {
  menuSablonu: menuSablonu, komutListesi: komutListesi, kisayolMetni: kisayolMetni, kisayolListesiTemizle: kisayolListesiTemizle,
  SAYFA_TUSU: SAYFA_TUSU, KISAYOL_SATIR_SINIRI: KISAYOL_SATIR_SINIRI, KISAYOL_METIN_SINIRI: KISAYOL_METIN_SINIRI,
};
