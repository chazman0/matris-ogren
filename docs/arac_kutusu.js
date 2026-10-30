/* Matris Öğren — yüzen araç kutuları (window.MatrisArac; node'da module.exports). Tasarım belgesi §17.1 ve §19.
   Bağımsız modül: sayfa (bina.js) komutlarını kaydeder, bu modül onları kullanıcının dilediği gibi grupladığı yüzen kutularda gösterir.

   Komut kaydı:
     MatrisArac.komutKaydet({ id, ad, ikon (ikon adı | SVG metni | emoji), grup_varsayilan, kisayol?, ipucu, tur? ("kip" | "anahtar" | "eylem"),
                              etkin(): bool, secili(): bool, calistir(olay?), secenekler?: [{id, ad, ikon}], secenek(): id, secenekSec(id) })
     Kimliği varsayılan katalogdaki bir komutla aynıysa ad/ikon/kısayol/ipucu katalogdan gelir; yalnız davranış (calistir/etkin/secili) verilir.
     MatrisArac.baglar({ "hizli-kolon": fn | {calistir, etkin, secili, ...}, ... }) çoklu kayıt kısayoludur.
   Kutular: MatrisArac.kur(kapsayici, {anahtar?, yonetici?, kisayollar?, mobilGenislik?, olay?(ad, veri)}) → yönetici.
     Sürüklenebilir (tutamaktan), kenara/köşeye ve komşu kutulara yapışan, yatay/dikey, küçültülebilir (yalnız ikon) / genişletilebilir (ikon + ad),
     saydamlık ayarlı, kilitlenebilir kutular; düğmeyi kutudan kutuya sürükle-bırak (Ctrl/Alt ile kopya), boş alana bırakınca yeni kutu;
     yeniden adlandır, sil, birleştir, gizle; "Özelleştir" kipi (ara, ekle/çıkar); hazır yerleşimler ve "Varsayılana dön";
     yerleşim localStorage'da (try/catch) ve JSON olarak dışa/içe aktarılır: yerlesim() / yerlesimYukle(json).
     Dar kapsayıcıda (< 640 px) kutular alt çekmecede yatay kaydırmalı şeride döner.
     Erişilebilirlik: role="toolbar", ok tuşlarıyla gezinti (Home/End), aria-pressed (kip/anahtar), aria-disabled, menülerde role="menu".
   Saf kısım (DOM'suz, node testli): katalog, ikonlar, yerleşim işlemleri (Duzen), yapışma/çapa/otomatik yerleşim, kısayol ayrıştırma, arama.

   §19 kararı: çizim yalnız aks kesişimleri (ve bölme/kesişim noktaları) arasındadır; katalogda serbest düğüm/serbest çizim komutu YOKTUR. */
(function (kok, fabrika) {
  "use strict";
  const api = fabrika();
  if (typeof module === "object" && module && module.exports) module.exports = api;
  else if (kok) kok.MatrisArac = api;
})(typeof window !== "undefined" ? window : (typeof self !== "undefined" ? self : this), function () {
  "use strict";

  // yerleşim sürümü 2: kutular kenar şeritlerine (rıhtım) yerleşir ya da kullanıcı taşıdıysa sahnede yüzer (yer: "serbest").
  // Sürüm 1 yerleşimleri (çapalı konum, otoKatli) dogrula'da kenar şeritlerine geçirilir.
  const SURUM = 2;
  const ANAHTAR = "matris.arac.yerlesim";
  const BOSLUK = 8;          // kapsayıcı kenarı ile kutu arası (px)
  const ARALIK = 6;          // kutular arası (px)
  const YAPISMA = 14;        // yapışma eşiği (px)
  const MOBIL = 640;         // bu genişliğin altında alt şerit
  const KENARLAR = ["ust", "alt", "sol", "sag"];
  const BANTLAR = ["ust", "alt"], SUTUNLAR = ["sol", "sag"];
  const SAHNE_MIN_H = 120, SAHNE_MIN_W = 200;     // rıhtımlar sahneden en az bu kadarını bırakır (px)
  const KOSE_DUGME = 34;     // yönetici ve taşma düğmesi (px)

  // ================================================================= İKONLAR (özgün, 24×24, çizgi tabanlı; iki ton: metin + vurgu)
  // Sınıflar: a = vurgu çizgisi, f = dolu (metin rengi), fa = dolu vurgu, y = açık vurgu dolgu, k = kesikli, t = kalın, n = ince.
  function p(d, c) { return '<path d="' + d + '"' + (c ? ' class="' + c + '"' : "") + "/>"; }
  function o(x, y, r, c) { return '<circle cx="' + x + '" cy="' + y + '" r="' + r + '"' + (c ? ' class="' + c + '"' : "") + "/>"; }
  function r(x, y, w, h, c, rx) { return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '"' + (rx ? ' rx="' + rx + '"' : "") + (c ? ' class="' + c + '"' : "") + "/>"; }
  function dg(x, y, c) { return r(x - 1.7, y - 1.7, 3.4, 3.4, c || "f", 0.6); }
  const SIMSEK = function (x, y) { return p("M" + (x + 1) + " " + y + "l-2.6 3.8h3.4l-2.6 3.8", "n"); };
  const CERCEVE = p("M4 3v18M20 3v18M3 4h18", "n");
  const IKON = {
    // ---- aks
    "aks-sihirbaz": p("M6 8v13M12 8v13", "k") + o(6, 4.6, 2.3) + o(12, 4.6, 2.3) + p("M3 13h13M3 18.5h13", "k") + p("M19 3v6M16 6h6", "a"),
    "aks-duzenle": r(3, 4, 14, 16, "", 1.5) + p("M3 9h14M3 14h14M8 4v16", "n") + p("M13.6 21.4l.7-3.2 6.1-6.1 2.5 2.5-6.1 6.1z", "a"),
    "aks-ekle": o(8, 4.6, 2.5) + p("M8 7.5V21", "k") + p("M17 12v8M13 16h8", "a"),
    "aks-sil": o(8, 4.6, 2.5) + p("M8 7.5V21", "k") + p("M14 13l6 6M20 13l-6 6", "a"),
    "aks-tasi": o(12, 4.6, 2.5) + p("M12 7.5V21", "k") + p("M4.5 14h15M7 11.5L4.5 14 7 16.5M17 11.5l2.5 2.5-2.5 2.5", "a"),
    "aks-sistemi": p("M3 20.5h11M3 20.5V10", "n k") + p("M9 16.5l8-4.6M9 16.5L4.6 8.9", "a") + p("M15 10.6l2 1.3-.6 2.2M4.2 11.2l.4-2.3 2.3-.2", "a n") + p("M19 2.5v6M16 5.5h6", "a"),
    "aks-gorunurluk": p("M3 13s3.4-6 9-6 9 6 9 6-3.4 6-9 6-9-6-9-6z") + o(12, 13, 2.5, "a") + p("M12 2v3", "n") + o(12, 2.2, 0.1),
    "duzlem-yukari": p("M3 15.5l4.5-3h13.5l-4.5 3z") + p("M3 21l4.5-3h13.5l-4.5 3z", "n k") + p("M12 10.5V3M9.2 5.8L12 3l2.8 2.8", "a"),
    "duzlem-asagi": p("M3 7.5l4.5-3h13.5l-4.5 3z", "n k") + p("M3 13l4.5-3h13.5l-4.5 3z") + p("M12 15.5V22M9.2 19.2L12 22l2.8-2.8", "a"),
    // ---- çizim (yalnız aks kesişimleri arası)
    "sec": p("M5.5 3.5l12.8 8-5.8 1.5 3.3 6.1-2.6 1.4-3.3-6.1-4.4 4.2z"),
    "cubuk-ciz": p("M4 3v18M12 3v18M20 3v18", "k n") + p("M4 17l8-9 8 5", "t a") + dg(4, 17) + dg(12, 8) + dg(20, 13),
    "hizli-cubuk": p("M2 16h20", "k n") + p("M6 16h12", "t a") + dg(6, 16) + dg(18, 16) + SIMSEK(12, 3),
    "hizli-kolon": p("M3 5h18M3 20h18", "k n") + p("M9 5v15", "t a") + dg(9, 5) + dg(9, 20) + SIMSEK(17, 8),
    "hizli-kiris": p("M4 4v17M20 4v17", "k n") + p("M4 14h16", "t a") + dg(4, 14) + dg(20, 14) + SIMSEK(12, 3),
    "hizli-capraz": CERCEVE + p("M4 4l16 16M20 4L4 20", "a"),
    "hizli-panel": p("M3 17.5l5-9.5h13l-5 9.5z", "y a") + dg(3, 17.5) + dg(8, 8) + dg(21, 8) + dg(16, 17.5),
    "egik-cubuk": p("M2 19.5h9M13 5.5h9", "k n") + p("M5 19.5L18 5.5", "t a") + dg(5, 19.5) + dg(18, 5.5),
    "makas": p("M2.5 18h19M2.5 18L12 7.5 21.5 18") + p("M7.2 18v-5.2M12 18V7.5M16.8 18v-5.2M7.2 12.8L12 18l4.8-5.2", "n a"),
    "besik-cerceve": p("M4.5 21V10.5L12 4.5l7.5 6V21", "t") + p("M2 21h20", "n") + p("M4.5 13.5l3.2-2.6M19.5 13.5l-3.2-2.6", "a"),
    "asik": p("M3 20L21 8.5", "t") + dg(6.6, 15.4, "fa") + dg(12, 12, "fa") + dg(17.4, 8.6, "fa") + p("M3 20h18", "n k"),
    "kren-yolu": p("M5 3v18", "t") + p("M5 13.5h7l-7 3.5", "n") + p("M6.5 7h9M11 7v6.5M6.5 13.5h9") + p("M17 10.2h4.5M19.6 8.2l2 2-2 2", "a"),
    "mesnet": o(12, 5, 1.8, "fa") + p("M12 6.8l-5.5 8h11z") + p("M4 17.5h16") + p("M6.5 17.5L4.5 20.5M10.5 17.5l-2 3M14.5 17.5l-2 3M18.5 17.5l-2 3", "n"),
    "yuk-ata": p("M3 19h18", "t") + p("M3 5h18", "n a") + p("M6 5v10.5M12 5v10.5M18 5v10.5", "a") + p("M4.4 13.9L6 15.5l1.6-1.6M10.4 13.9l1.6 1.6 1.6-1.6M16.4 13.9l1.6 1.6 1.6-1.6", "a"),
    // ---- çapraz tipleri (model işlemleri caprazUret ile aynı kimlikler)
    "cap-X": CERCEVE + p("M4 4l16 16M20 4L4 20", "a"),
    "cap-tek-/": CERCEVE + p("M4 20L20 4", "a"),
    "cap-tek-\\": CERCEVE + p("M4 4l16 16", "a"),
    "cap-V": CERCEVE + p("M4 4l8 16 8-16", "a"),
    "cap-ters-V": CERCEVE + p("M4 20l8-16 8 16", "a"),
    "cap-K": CERCEVE + p("M20 4L4 12l16 8", "a"),
    "cap-dismerkez-tek": CERCEVE + p("M4 20L14 4", "a") + dg(14, 4, "fa"),
    "cap-dismerkez-ters-V": CERCEVE + p("M4 20l6-16M20 20l-6-16", "a") + p("M10 4h4", "t a"),
    "cap-diz": CERCEVE + p("M4 10l6-6M20 10l-6-6", "a"),
    // ---- düzenleme
    "geri-al": p("M9 15L4 10l5-5") + p("M4 10h10.5a5.5 5.5 0 0 1 0 11H11", "a"),
    "yinele": p("M15 15l5-5-5-5") + p("M20 10H9.5a5.5 5.5 0 0 0 0 11H13", "a"),
    "kopyala": r(8.5, 8.5, 12, 12, "", 2) + p("M16 8.5V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16h3", "n a"),
    "yapistir": r(5, 5, 14, 16, "", 2) + r(9, 3, 6, 4, "a", 1) + p("M9 12h6M9 16h4", "n"),
    "sil": p("M4 7h16M9.5 7V4.5h5V7") + p("M6.2 7l.9 13.5h9.8l.9-13.5") + p("M10.2 11v6M13.8 11v6", "n a"),
    "tasi": p("M12 3v18M3 12h18") + p("M9 6l3-3 3 3M9 18l3 3 3-3M6 9l-3 3 3 3M18 9l3 3-3 3", "a"),
    "dondur": p("M8 16L16 8", "t") + p("M4.6 10.5A8 8 0 0 1 13.5 3.9", "a") + p("M11 2.6l2.6 1.3-1.2 2.6", "a") + p("M19.4 13.5a8 8 0 0 1-8.9 6.6", "a") + p("M13 21.4l-2.6-1.3 1.2-2.6", "a"),
    "ayna": p("M12 2.5v19", "k a") + p("M9 7L3 17h6z") + p("M15 7l6 10h-6z", "y a"),
    "dogrusal-dizi": r(3, 8, 5, 5, "", 1) + r(10, 8, 5, 5, "n", 1) + r(17, 8, 5, 5, "n k", 1) + p("M3 18h17.5M18 15.8l2.5 2.2-2.5 2.2", "a"),
    "ozellik-ata": r(4, 3, 13, 5.5, "", 1.5) + p("M17 5.8h3v5.2h-8.5V14") + r(10, 14, 3, 7, "fa", 1),
    "mafsal": p("M7.5 12h9", "t") + o(5, 12, 2.5, "a") + o(19, 12, 2.5, "a") + p("M3 18h18", "n k"),
    "yalniz-cekme": p("M7 12h10", "t") + p("M2 12h3.2M4 9.6L1.6 12 4 14.4M22 12h-3.2M20 9.6l2.4 2.4-2.4 2.4", "a") + p("M9.5 7.5l5 9M14.5 7.5l-5 9", "n k"),
    // ---- değiştirme
    "bol": p("M3 6.5h18", "t") + p("M12 9v4M10.2 11.4l1.8 1.8 1.8-1.8", "a n") + p("M3 18h5M10.5 18h3M16 18h5", "t") + dg(9.2, 18, "fa") + dg(14.8, 18, "fa"),
    "kesisimde-bol": p("M4 4l16 16M20 4L4 20") + o(12, 12, 2.6, "fa") + dg(4, 4) + dg(20, 20) + dg(20, 4) + dg(4, 20),
    "duzlemle-bol": p("M9 3l6 3.2V21L9 17.8z", "y a") + p("M2 13h7.6M14.4 13H22", "t") + p("M9.6 13h4.8", "k n"),
    "birlestir": p("M3 6.5h5M10.5 6.5h3M16 6.5h5", "t") + dg(9.2, 6.5) + dg(14.8, 6.5) + p("M12 9v4M10.2 11.4l1.8 1.8 1.8-1.8", "a n") + p("M3 18h18", "t a"),
    "dugum-birlestir": o(5, 6.5, 2.3) + o(5, 17.5, 2.3) + p("M7.5 7.8l5.8 3M7.5 16.2l5.8-3", "a") + r(14.5, 9.5, 5, 5, "fa", 1),
    "kesit-degistir": p("M3.5 4h9M3.5 19h9M8 4v15") + p("M15 7.5h6M19 5.5l2 2-2 2M21 16.5h-6M17 14.5l-2 2 2 2", "a"),
    "aci": p("M5 9.2l4.7-5.4M13.8 20.4l4.7-5.4") + p("M7.4 6.5l8.8 11.2") + p("M17 3.8a8.5 8.5 0 0 1 3.6 6.9", "a") + p("M22 8.6l-1.4 2.2-2.2-1.3", "a"),
    // ---- ölçme
    "olc-uzaklik": p("M4 6v13M20 6v13", "n") + p("M4 15h16", "a") + p("M2.6 16.4l2.8-2.8M18.6 16.4l2.8-2.8", "a") + dg(4, 6) + dg(20, 6),
    "olc-aci": p("M4 19h16M4 19L15 6") + p("M10.5 19A6.5 6.5 0 0 0 8.2 14", "a") + dg(4, 19),
    "olc-alan": p("M4 18L7 5l13 4-3 10z", "y a") + p("M7.5 15.5l5-7M11 17l4.8-6.6", "n a"),
    "olc-boy": p("M4 8h16", "t") + dg(4, 8) + dg(20, 8) + p("M4 12v7M20 12v7", "n") + p("M4 16.5h16", "a") + p("M2.6 17.9l2.8-2.8M18.6 17.9l2.8-2.8", "a"),
    "olc-kot": p("M3 6h11M3 19h11", "n k") + p("M8 6L5.6 2.5h4.8zM8 19l-2.4-3.5h4.8z") + p("M18 6v13", "a") + p("M16 6h4M16 19h4", "a"),
    "olc-koordinat": o(12, 12, 5) + p("M12 2v5M12 17v5M2 12h5M17 12h5") + o(12, 12, 1.4, "fa"),
    "olc-temizle": p("M3 7h12", "a") + p("M3 5v4M15 5v4", "n") + p("M10 20.5l8-8 3.2 3.2-5 4.8z") + p("M9 20.5h12", "n"),
    // ---- görünüm
    "gor-3b": p("M12 3l8 4.5v9L12 21l-8-4.5v-9z") + p("M4 7.5l8 4.5 8-4.5M12 12v9", "n a"),
    "gor-plan": r(4, 4, 16, 16, "", 1.5) + p("M4 10h16M4 15h16M10 4v16M15 4v16", "n k") + dg(10, 10, "fa") + dg(15, 15, "fa"),
    "gor-on": p("M4 20V5h16v15M12 5v15M4 12.5h16") + p("M2 20h20", "n") + p("M12 22.6v-1.2", "a"),
    "gor-yan": p("M9 20V5h9v15M9 12.5h9") + p("M6 20h15", "n") + p("M2 12.5h4M4.4 10.5l2 2-2 2", "a"),
    "kat-suzgeci": p("M3 8l9-4 9 4-9 4z") + p("M3 12.5l9 4 2.5-1.1", "n") + p("M15 14.5h7l-2.7 3.4V22l-1.6-.8v-3.3z", "a"),
    "yalit": r(9, 9, 6, 6, "y a", 1) + r(3, 3, 4, 4, "n k") + r(17, 3, 4, 4, "n k") + r(3, 17, 4, 4, "n k") + r(17, 17, 4, 4, "n k"),
    "hepsini-goster": p("M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z") + o(12, 12, 3, "a"),
    "tel-kafes": r(4, 8, 11, 11) + p("M9 4h11v11", "a k") + p("M4 8l5-4M15 8l5-4M15 19l5-4M4 19l5-4", "n"),
    "etiketler": p("M3 12.5V4h8.5l9.5 9.5-8.5 8.5z") + o(7.6, 8.1, 1.6, "fa"),
    "izgara": p("M3 8h18M3 16h18M8 3v18M16 3v18", "k") + o(8, 8, 1.6, "fa") + o(16, 16, 1.6, "fa"),
    "sigdir": p("M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5") + r(9, 9, 6, 6, "y a", 1),
    "tam-ekran": p("M4 10V4h6M14 4h6v6M20 14v6h-6M10 20H4v-6") + p("M4.5 4.5L9 9M19.5 4.5L15 9M19.5 19.5L15 15M4.5 19.5L9 15", "a n"),
    // ---- analiz
    "coz": o(12, 12, 9) + p("M10 7.8l6 4.2-6 4.2z", "fa"),
    "denetle": p("M9 6h12M9 12h12M9 18h12", "n") + p("M3 6l1.6 1.6L7.4 4.8M3 12l1.6 1.6 2.8-2.8", "a") + p("M3.4 16.6l3 3M6.4 16.6l-3 3"),
    "yuk-durumlari": p("M3 20h18", "t") + p("M6 3.5v12M12 7.5v8M18 10.5v5", "a") + p("M4.4 13.9L6 15.5l1.6-1.6M10.4 13.9l1.6 1.6 1.6-1.6M16.4 13.9l1.6 1.6 1.6-1.6", "a"),
    "kombinasyonlar": p("M18 4H6l6.5 8L6 20h12") + p("M18 4v2.6M18 20v-2.6", "n") + p("M8.5 12h4", "a t"),
    "analiz-ayar": p("M4 6h16M4 12h16M4 18h16", "n") + o(9, 6, 2.1, "fa") + o(15, 12, 2.1, "fa") + o(7, 18, 2.1, "fa"),
    "kutuphane": r(3.5, 4, 4.5, 16, "", 1) + r(9.5, 4, 4.5, 16, "", 1) + p("M5.7 8v2M11.7 8v2", "n") + p("M15.6 5.6l4.3-1.1 3 15.4-4.3 1.1z", "y a"),
    // ---- sonuç
    "deforme": p("M3 7h18", "n k") + p("M3 7C9 16 15 16 21 7", "a") + p("M3 7l-1.6 3h3.2zM21 7l-1.6 3h3.2z", "n"),
    "diyagram": p("M3 8h18", "t") + p("M3 8Q12 23 21 8", "y a") + p("M7.5 8v4.6M12 8v7M16.5 8v4.6", "n a"),
    "yuk-akisi": p("M3 5h18", "t") + p("M7 11h10", "t") + p("M10.5 17h3", "t") + p("M12 6.6v3M10.6 8.2L12 9.6l1.4-1.4M12 12.6v3M10.6 14.2l1.4 1.4 1.4-1.4", "a") + p("M6 21h12", "n"),
    "isi-haritasi": r(3, 4, 18, 16, "", 2) + '<rect x="3.8" y="4.8" width="5.4" height="14.4" class="fa" opacity=".25"/><rect x="9.3" y="4.8" width="5.4" height="14.4" class="fa" opacity=".55"/><rect x="14.8" y="4.8" width="5.4" height="14.4" class="fa" opacity=".9"/>',
    "tasarim-dc": p("M4 17a8 8 0 0 1 16 0") + p("M12 17l4.2-6", "a") + o(12, 17, 1.6, "f") + p("M4 20.5h16", "n") + p("M6.3 11.3l1 1M12 9v1.4M17.7 11.3l-1 1", "n"),
    "tablolar": r(3, 4, 18, 16, "", 1.5) + p("M3 9h18M3 14h18M9 4v16M15 4v16", "n"),
    "rapor": p("M6 3h9l4 4v14H6z") + p("M15 3v4h4", "n") + p("M9 11h7M9 14h7M9 17h4", "n a"),
    // ---- yönetim
    "yonetici": r(3, 3, 7.5, 7.5, "", 1.5) + r(13.5, 3, 7.5, 7.5, "", 1.5) + r(3, 13.5, 7.5, 7.5, "", 1.5) + r(13.5, 13.5, 7.5, 7.5, "y a", 1.5),
    "menu": o(6, 12, 1.5, "f") + o(12, 12, 1.5, "f") + o(18, 12, 1.5, "f"),
    "ozellestir": r(3, 3, 7.5, 7.5, "", 1.5) + r(13.5, 13.5, 7.5, 7.5, "", 1.5) + p("M14 7h6M17 4v6", "a") + p("M4.5 17.2h4.5", "a"),
    "diger": r(5, 5, 14, 14, "", 3) + p("M9 12h6M12 9v6", "a"),
  };
  /** İkon SVG metni: ikon adı (IKON), hazır SVG metni ya da emoji/metin. */
  function ikonSvg(ad, sinif) {
    const s = sinif ? " " + sinif : "";
    if (typeof ad === "string" && /^\s*<svg[\s>]/i.test(ad)) return ad;
    const ic = IKON[ad];
    if (ic == null) {
      if (typeof ad === "string" && ad && !IKON.hasOwnProperty(ad) && ad.length <= 3) {
        return '<span class="arac-ikon arac-ikon-metin' + s + '" aria-hidden="true">' + kacis(ad) + "</span>";
      }
      return ikonSvg("diger", sinif);
    }
    return '<svg class="arac-ikon' + s + '" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7"' +
      ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + ic + "</svg>";
  }

  // ================================================================= KATALOG
  const GRUPLAR = Object.freeze([
    { id: "aks", ad: "Aks" }, { id: "cizim", ad: "Çizim" }, { id: "duzenleme", ad: "Düzenleme" }, { id: "degistirme", ad: "Değiştirme" },
    { id: "olcme", ad: "Ölçme" }, { id: "gorunum", ad: "Görünüm" }, { id: "analiz", ad: "Analiz" }, { id: "sonuc", ad: "Sonuç" },
  ]);
  /**
   * Sayfa tuşları (sözleşme C22): komut kaydında olmayan, sayfanın kendisinin işlediği tuşlar. Bina "?" kısayol penceresi, Yardım
   * kısayol tablosu (app.js) ve masaüstü "Klavye kısayolları" bu tek listeden yapılır. grup: GRUPLAR kimliği ya da "sayfa".
   */
  const SAYFA_TUSLARI = Object.freeze([
    ["Esc", "Kipten çık, seçimi ya da yarım çizimi / ölçümü bırak; tam ekrandan çık", "sayfa"],
    ["Shift+F10", "Seçili elemanın bağlam (sağ tık) menüsü", "sayfa"],
    ["Enter", "Bağlam menüsünde: Bilgi", "sayfa"],
    ["?", "Kısayol listesini aç", "sayfa"],
    ["PgUp", "Düzlem yukarı: bir üst Z aksı ya da sonraki cephe aksı (aks–kat çiziminde üst kat)", "aks"],
    ["PgDn", "Düzlem aşağı", "aks"],
    ["F", "Tam ekran (Esc ya da F ile çıkılır)", "gorunum"],
    ["Shift+F", "Modeli sığdır", "gorunum"],
    ["Ctrl+Shift+Z", "Yinele", "duzenleme"],
    ["Backspace", "Seçileni sil (seçim yoksa Sil aracı)", "duzenleme"],
  ].map(function (s) { return Object.freeze({ kisayol: s[0], ad: s[1], grup: s[2] }); }));
  /** Hızlı çapraz tip seçicisi — kimlikler model işlemleri `CAPRAZ_TIPLERI` ile aynı. */
  const CAPRAZ_SECENEKLERI = Object.freeze([
    { id: "X", ad: "X çapraz" }, { id: "tek-/", ad: "Tek çapraz /" }, { id: "tek-\\", ad: "Tek çapraz \\" }, { id: "V", ad: "V çapraz" },
    { id: "ters-V", ad: "Ters V (chevron)" }, { id: "K", ad: "K çapraz" }, { id: "dismerkez-tek", ad: "Dışmerkez tek" },
    { id: "dismerkez-ters-V", ad: "Dışmerkez ters V (bağ kirişli)" }, { id: "diz", ad: "Diz çaprazı" },
  ].map(function (s) { return Object.freeze(Object.assign({ ikon: "cap-" + s.id }, s)); }));
  const DIYAGRAM_SECENEKLERI = Object.freeze([
    { id: "N", ad: "Normal kuvvet N" }, { id: "V", ad: "Kesme V" }, { id: "M", ad: "Eğilme momenti M" },
    { id: "Vz", ad: "Kesme Vz" }, { id: "My", ad: "Eğilme momenti My" }, { id: "T", ad: "Burulma T" },
  ].map(function (s) { return Object.freeze(Object.assign({ ikon: "diyagram" }, s)); }));

  // [id, ad, grup, tür, kısayol, ipucu, seçenekler?]
  const K = [
    // Aks
    ["aks-sihirbaz", "Hızlı aks sihirbazı", "aks", "eylem", "Shift+G", "X/Y/Z akslarını adet ve aralıkla (\"3@6, 2@7.5\") ya da konum listesiyle kurar; kat yükseklikleri ve saçak/mahya/kren gibi ek Z aksları."],
    ["aks-duzenle", "Aks verisi düzenle", "aks", "eylem", "G", "Her yön ayrı sekmede ad, konum, aralık, tür, görünürlük ve balon tablosu; elemanlar akslara yapışık taşınır."],
    ["aks-ekle", "Aks ekle", "aks", "kip", "", "Seçilen yöne yeni aks ekler; iki aksın arasına tıklarsanız tam ortasına yerleşir."],
    ["aks-sil", "Aks sil", "aks", "kip", "", "Aksı siler; bağlı eleman varsa \"elemanlarla birlikte sil\", \"en yakın aksa taşı\" ya da \"iptal\" sorulur."],
    ["aks-tasi", "Aks taşı", "aks", "kip", "", "Aks balonunu sürükleyin (0,05 m adım) ya da sayı girin; aksa yapışık düğümler ve elemanlar birlikte taşınır."],
    ["aks-sistemi", "Aks sistemi ekle", "aks", "eylem", "", "Döndürülmüş/ötelenmiş kartezyen ya da silindirik ek aks sistemi tanımlar."],
    ["aks-gorunurluk", "Aks görünürlüğü", "aks", "eylem", "", "Hangi aksların ve aks sistemlerinin sahnede görüneceğini, balonların yerini seçer."],
    ["duzlem-yukari", "Düzlem yukarı", "aks", "eylem", "PgUp", "Planda bir üst Z aksına, cephede bir sonraki aksa geçer."],
    ["duzlem-asagi", "Düzlem aşağı", "aks", "eylem", "PgDn", "Planda bir alt Z aksına, cephede bir önceki aksa geçer."],
    // Çizim — yalnız aks kesişimleri arasında
    ["sec", "Seç", "cizim", "kip", "S", "Elemana dokunun; Shift ile çoklu seçim. Sağ tık ya da uzun basma eleman bilgisini açar."],
    ["cubuk-ciz", "Çubuk çiz", "cizim", "kip", "L", "Kesişimden kesişime çubuk; art arda dokunuşlar zincir oluşturur, Esc bitirir."],
    ["hizli-cubuk", "Hızlı çubuk", "cizim", "kip", "Shift+L", "Bir aks parçasına dokunun: iki komşu kesişim arasına çubuk. Sürükleyerek birden çok parça."],
    ["hizli-kolon", "Hızlı kolon", "cizim", "kip", "K", "Planda kesişime dokunun: alt ve üst Z aksları arasına kolon (çoklu kat için sürükleyin)."],
    ["hizli-kiris", "Hızlı kiriş", "cizim", "kip", "R", "Etkin Z aksında iki komşu kesişim arasına kiriş; aks parçasına dokunun ya da sürükleyin."],
    ["hizli-capraz", "Hızlı çapraz", "cizim", "kip", "X", "Cephede bir göze dokunun; tipi sağ tık, uzun basma ya da Alt+↓ ile seçin.", CAPRAZ_SECENEKLERI],
    ["hizli-panel", "Hızlı panel", "cizim", "kip", "D", "Göze dokunun: dört kesişim arasında döşeme, çatı ya da cephe paneli."],
    ["egik-cubuk", "Eğik çubuk", "cizim", "kip", "E", "Farklı Z akslarındaki iki kesişim arası (mertek, makas üst başlığı)."],
    ["makas", "Makas üreteci", "cizim", "eylem", "", "Pratt, Howe, Warren, K, Fink… gerekli mahya/saçak akslarını kendisi ekler."],
    ["besik-cerceve", "Beşik çerçeve", "cizim", "eylem", "", "Açıklık, saçak ve mahya kotuyla çerçeve; vute boyu ve yüksekliği."],
    ["asik", "Aşık", "cizim", "eylem", "", "Mertek ya da panel üzerinde aralıklı aşıklar; aşık noktaları bölme düğümü olur."],
    ["kren-yolu", "Kren yolu", "cizim", "eylem", "", "Kolon konsolu ve kren kirişi, kren tanımıyla."],
    ["mesnet", "Mesnet", "cizim", "kip", "Shift+M", "Düğüme mesnet atar (ankastre, mafsal, kayıcı) ya da kaldırır."],
    ["yuk-ata", "Yük ata", "cizim", "kip", "Y", "Çubuğa yayılı/tekil, düğüme kuvvet, panele alan yükü; yük durumu seçilir."],
    // Düzenleme
    ["geri-al", "Geri al", "duzenleme", "eylem", "Ctrl+Z", "Son değişikliği geri alır."],
    ["yinele", "Yinele", "duzenleme", "eylem", "Ctrl+Y", "Geri alınanı yeniden uygular."],
    ["kopyala", "Kopyala", "duzenleme", "eylem", "Ctrl+C", "Seçili elemanları panoya alır."],
    ["yapistir", "Yapıştır", "duzenleme", "eylem", "Ctrl+V", "Panodakileri bir aks kesişiminden ötekine öteleyerek yapıştırır."],
    ["sil", "Sil", "duzenleme", "eylem", "Del", "Seçili elemanları siler."],
    ["tasi", "Taşı", "duzenleme", "kip", "M", "Seçimi bir kesişimden ötekine taşır (aks aralığı kadar)."],
    ["dondur", "Döndür", "duzenleme", "kip", "Shift+R", "Seçimi bir kesişim çevresinde döndürür."],
    ["ayna", "Ayna", "duzenleme", "kip", "", "Seçimi bir aks düzlemine göre yansıtır."],
    ["dogrusal-dizi", "Doğrusal dizi", "duzenleme", "eylem", "", "Seçimi aks aralıklarıyla n kez çoğaltır."],
    ["ozellik-ata", "Özellik ata", "duzenleme", "kip", "", "Kesit/malzeme fırçası: seçili özelliği dokunduğunuz elemanlara uygular."],
    ["mafsal", "Mafsal / serbestlik", "duzenleme", "eylem", "", "Uç serbestlikleri (My, Mz, T…) atar."],
    ["yalniz-cekme", "Yalnız çekme", "duzenleme", "anahtar", "", "Seçili çaprazları basınçta devre dışı bırakır (doğrusal olmayan çözüm)."],
    // Değiştirme
    ["bol", "Böl", "degistirme", "eylem", "B", "Çubuğu n eşit parçaya, verilen uzunluk/oranda ya da bir noktada böler (bölme düğümü)."],
    ["kesisimde-bol", "Kesişimlerde böl", "degistirme", "eylem", "", "Seçili çubukları birbirleriyle kesiştikleri yerlerde böler."],
    ["duzlemle-bol", "Düzlemle böl", "degistirme", "eylem", "", "Seçili çubukları bir aks düzlemiyle kesiştikleri yerde böler."],
    ["birlestir", "Birleştir", "degistirme", "eylem", "J", "Uç uca, eş doğrusal ve aynı özellikli çubuk zincirini tek çubuk yapar."],
    ["dugum-birlestir", "Düğümleri birleştir", "degistirme", "eylem", "Shift+J", "Tolerans içindeki çakışık düğümleri tek düğümde toplar."],
    ["kesit-degistir", "Kesit değiştir", "degistirme", "eylem", "", "Seçili çubukların kesitini değiştirir."],
    ["aci", "Yerel eksen açısı", "degistirme", "eylem", "", "Kesiti çubuk ekseni çevresinde döndürür (aci, derece)."],
    // Ölçme
    ["olc-uzaklik", "Uzaklık", "olcme", "kip", "U", "İki nokta arası uzaklık, ΔX/ΔY/ΔZ ve eğim."],
    ["olc-aci", "Açı", "olcme", "kip", "", "Üç nokta: birinci kol, köşe, ikinci kol."],
    ["olc-alan", "Alan", "olcme", "kip", "", "Çokgen alanı ve çevresi; ilk noktaya dokunun ya da Enter."],
    ["olc-boy", "Eleman boyu", "olcme", "kip", "", "Çubuğa tek dokunuşla boy, eğim ve doğrultu."],
    ["olc-kot", "Kot farkı", "olcme", "kip", "", "İki nokta arası düşey fark."],
    ["olc-koordinat", "Koordinat sorgula", "olcme", "kip", "", "Noktanın X, Y, Z koordinatı ve aks adresi."],
    ["olc-temizle", "Ölçüleri temizle", "olcme", "eylem", "", "Sahnedeki bütün ölçü çizgilerini siler (Esc yalnız yarım ölçümü siler; tamamlanan ölçüler kalır)."],
    // Görünüm
    ["gor-3b", "3B", "gorunum", "kip", "1", "Aksonometrik görünüş."],
    ["gor-plan", "Plan", "gorunum", "kip", "2", "Etkin Z aksında plan."],
    ["gor-on", "Ön (cephe)", "gorunum", "kip", "3", "Etkin Y aksında cephe."],
    ["gor-yan", "Yan (kesit)", "gorunum", "kip", "4", "Etkin X aksında kesit."],
    ["kat-suzgeci", "Kat süzgeci", "gorunum", "eylem", "", "Yalnız seçilen katları ya da Z aralığını gösterir."],
    ["yalit", "Yalıt", "gorunum", "eylem", "", "Yalnız seçili elemanları gösterir."],
    ["hepsini-goster", "Hepsini göster", "gorunum", "eylem", "", "Gizlenen ve yalıtılan her şeyi geri getirir."],
    ["tel-kafes", "Tel kafes", "gorunum", "anahtar", "", "Kesit prizmaları yerine eksen çizgileri."],
    ["etiketler", "Etiketler", "gorunum", "anahtar", "", "Eleman ve düğüm numaraları, kesit adları."],
    ["izgara", "Aks ızgarası", "gorunum", "anahtar", "", "Aks çizgileri, kesişim noktaları, balonlar ve aralık ölçü zinciri."],
    ["sigdir", "Sığdır", "gorunum", "eylem", "F", "Bütün modeli ekrana sığdırır."],
    ["tam-ekran", "Tam ekran", "gorunum", "anahtar", "Shift+F", "Sahneyi tam ekran yapar."],
    // Analiz
    ["coz", "Çöz", "analiz", "eylem", "Ctrl+Enter", "Modeli çözer: yükler, durumlar, kombinasyonlar, zarf ve tasarım."],
    ["denetle", "Modeli denetle", "analiz", "eylem", "", "Yüzen eleman, kenarı taşınmayan panel, mekanizma gibi sorunları listeler."],
    ["yuk-durumlari", "Yük durumları", "analiz", "eylem", "", "G, Q, S, W, E, kren durumları."],
    ["kombinasyonlar", "Kombinasyonlar", "analiz", "eylem", "", "TS 500 / ÇYTHYE / TBDY kombinasyon kümeleri."],
    ["analiz-ayar", "Analiz ayarları", "analiz", "eylem", "", "Çatlamış rijitlik, diyafram, diyagram nokta sayısı."],
    ["kutuphane", "Kütüphane", "analiz", "eylem", "", "Malzemeler, kesitler (yeni kesit, kesit fırçası), duvar türleri ve hareketli yük sınıfları."],
    // Sonuç
    ["deforme", "Deforme şekil", "sonuc", "anahtar", "", "Seçili durum ya da kombinasyonda şekil değiştirme (ölçekli)."],
    ["diyagram", "İç kuvvet diyagramı", "sonuc", "anahtar", "", "N, V, M, Vz, My, T diyagramları; büyüklüğü sağ tık ya da Alt+↓ ile seçin.", DIYAGRAM_SECENEKLERI],
    ["yuk-akisi", "Yük akışı", "sonuc", "anahtar", "", "Döşeme → kiriş → kolon → temel → zemin akışı."],
    ["isi-haritasi", "Isı haritası", "sonuc", "anahtar", "", "Gerilme, iç kuvvet ve D/C renk haritası."],
    ["tasarim-dc", "Tasarım (D/C)", "sonuc", "anahtar", "", "Kesit tahkikleri ve talep/kapasite renkleri."],
    ["tablolar", "Tablolar", "sonuc", "eylem", "", "Tepkiler, iç kuvvetler, metraj tabloları."],
    ["rapor", "Rapor", "sonuc", "eylem", "", "Statik hesap raporu."],
  ];
  const KATALOG = Object.freeze(K.map(function (k) {
    const t = { id: k[0], ad: k[1], grup: k[2], tur: k[3], kisayol: k[4] || "", ipucu: k[5], ikon: k[0] };
    if (k[6]) t.secenekler = k[6];
    return Object.freeze(t);
  }));
  const KATALOG_HARITA = new Map(KATALOG.map(function (k) { return [k.id, k]; }));

  // ================================================================= yardımcılar
  function kacis(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function kopya(o) { return JSON.parse(JSON.stringify(o)); }
  /** Türkçe büyük/küçük harf ve aksan duyarsız arama anahtarı. */
  function normal(s) {
    return String(s == null ? "" : s).replace(/İ/g, "i").replace(/I/g, "ı").toLowerCase()
      .replace(/[çğıöşü]/g, function (c) { return { "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u" }[c]; })
      .replace(/[âîû]/g, function (c) { return { "â": "a", "î": "i", "û": "u" }[c]; });
  }
  /** Komut ara: ad, ipucu, kimlik ve grup adında (sıra: ad başlangıcı > ad içi > diğer). */
  function ara(liste, sorgu) {
    const q = normal(sorgu).trim();
    if (!q) return liste.slice();
    const gadi = new Map(GRUPLAR.map(function (g) { return [g.id, g.ad]; }));
    const puanli = [];
    liste.forEach(function (k, i) {
      const ad = normal(k.ad), dig = normal([k.ipucu, k.id, gadi.get(k.grup) || k.grup, k.kisayol].join(" "));
      let pu = -1;
      if (ad.indexOf(q) === 0) pu = 0;
      else if (ad.split(/\s+/).some(function (w) { return w.indexOf(q) === 0; })) pu = 1;
      else if (ad.indexOf(q) >= 0) pu = 2;
      else if (dig.indexOf(q) >= 0) pu = 3;
      if (pu >= 0) puanli.push([pu, i, k]);
    });
    return puanli.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; }).map(function (x) { return x[2]; });
  }

  // ---- kısayollar
  const TUS_ADI = { del: "Delete", delete: "Delete", sil: "Delete", pgup: "PageUp", pageup: "PageUp", pgdn: "PageDown", pagedown: "PageDown",
    enter: "Enter", esc: "Escape", escape: "Escape", space: " ", bosluk: " ", tab: "Tab", home: "Home", end: "End", ins: "Insert", insert: "Insert",
    up: "ArrowUp", down: "ArrowDown", left: "ArrowLeft", right: "ArrowRight" };
  /** "Ctrl+Shift+Z" → {ctrl, shift, alt, tus: "Z"}; geçersizse null. */
  function kisayolCoz(m) {
    if (!m || typeof m !== "string") return null;
    const parcalar = m.split("+").map(function (s) { return s.trim(); }).filter(Boolean);
    if (!parcalar.length) return null;
    const k = { ctrl: false, shift: false, alt: false, tus: "" };
    if (/^(ctrl|cmd|meta|shift|alt)$/i.test(parcalar[parcalar.length - 1])) return null;   // "Ctrl+" gibi yarım kısayol
    for (let i = 0; i < parcalar.length; i++) {
      const s = parcalar[i], n = s.toLowerCase();
      if (i < parcalar.length - 1 && (n === "ctrl" || n === "cmd" || n === "meta")) k.ctrl = true;
      else if (i < parcalar.length - 1 && n === "shift") k.shift = true;
      else if (i < parcalar.length - 1 && n === "alt") k.alt = true;
      else if (i === parcalar.length - 1) k.tus = TUS_ADI[n] || (s.length === 1 ? s.toUpperCase() : s);
      else return null;
    }
    return k.tus ? k : null;
  }
  /** Klavye olayı kısayola uyuyor mu? (harflerde e.code da denenir: klavye düzeninden bağımsız). */
  function kisayolEslesir(k, e) {
    if (!k || !e) return false;
    if (!!(e.ctrlKey || e.metaKey) !== k.ctrl || !!e.altKey !== k.alt) return false;
    let tus = e.key || "";
    if (tus.length === 1) tus = tus.toLocaleUpperCase("tr") === "İ" ? "I" : tus.toUpperCase();
    const harf = k.tus.length === 1 && /[A-Z0-9]/.test(k.tus);
    const kod = e.code ? (e.code.indexOf("Key") === 0 ? e.code.slice(3) : e.code.indexOf("Digit") === 0 ? e.code.slice(5) : "") : "";
    const tusUyar = tus === k.tus || (harf && kod === k.tus);
    if (!tusUyar) return false;
    // Shift: harf/rakam/özel tuşlarda birebir; noktalama işaretlerinde (Shift ile üretilen) yok sayılır
    if (harf || k.tus.length > 1) return !!e.shiftKey === k.shift;
    return true;
  }
  function kisayolMetni(m) {
    const k = kisayolCoz(m);
    if (!k) return "";
    const ad = { Delete: "Del", PageUp: "PgUp", PageDown: "PgDn", Escape: "Esc", " ": "Boşluk", ArrowUp: "↑", ArrowDown: "↓", ArrowLeft: "←", ArrowRight: "→" }[k.tus] || k.tus;
    return (k.ctrl ? "Ctrl+" : "") + (k.alt ? "Alt+" : "") + (k.shift ? "Shift+" : "") + ad;
  }

  // ================================================================= YERLEŞİM (saf)
  function kutuKimligi(y, taban) {
    const var_ = new Set((y.kutular || []).map(function (k) { return k.id; }));
    let t = "k-" + (taban || "kutu").replace(/[^a-z0-9-]/gi, "").toLowerCase(), id = t, n = 2;
    while (var_.has(id)) id = t + "-" + n++;
    return id;
  }
  function grupKomutlari(grup) { return KATALOG.filter(function (k) { return k.grup === grup; }).map(function (k) { return k.id; }); }
  /** Grubun görünen adı (GRUPLAR; sayfa tuşlarının "sayfa" grubu → "Sayfa"). */
  function grupAdi(grup) { const g = GRUPLAR.find(function (x) { return x.id === grup; }); return g ? g.ad : grup === "sayfa" ? "Sayfa" : grup; }
  function yeniKutuNesnesi(id, ad, komutlar, ayar) {
    return Object.assign({ id: id, ad: ad, komutlar: komutlar.slice(), yon: "yatay", kucuk: true, saydamlik: 1, kilitli: false, gizli: false, katli: false,
      yer: "kenar", kenar: "ust", sira: null, konum: null }, ayar || {});
  }
  /** Kenar şeritlerindeki sıra (1..n): şeridin kutuları sira'sı olmayanlar sona (dizi sırasıyla) eklenerek numaralanır. */
  function siraNumarala(y, yalnizEksik) {
    KENARLAR.forEach(function (kn) {
      const l = y.kutular.map(function (k, i) { return { k: k, i: i }; }).filter(function (x) { return x.k.kenar === kn; });
      l.sort(function (a, b) {
        const sa = isFinite(a.k.sira) && a.k.sira != null ? +a.k.sira : Infinity, sb = isFinite(b.k.sira) && b.k.sira != null ? +b.k.sira : Infinity;
        return (sa - sb) || (a.i - b.i);
      });
      if (yalnizEksik) {
        let m = 0;
        l.forEach(function (x) { if (x.k.sira != null && isFinite(x.k.sira)) m = Math.max(m, +x.k.sira); });
        l.forEach(function (x) { if (x.k.sira == null || !isFinite(x.k.sira)) x.k.sira = ++m; });
      } else l.forEach(function (x, n) { x.k.sira = n + 1; });
    });
    return y;
  }
  /** Varsayılan yerleşim: her grup bir kutu, kenar şeritlerinde (dizi sırası = öncelik; sığmayan sondan taşma çekmecesine gider). */
  const VARSAYILAN_DUZEN = {
    aks: { kenar: "ust", yon: "yatay" }, duzenleme: { kenar: "ust", yon: "yatay" }, cizim: { kenar: "sol", yon: "dikey" },
    degistirme: { kenar: "sag", yon: "dikey" }, olcme: { kenar: "sag", yon: "dikey" },
    gorunum: { kenar: "alt", yon: "yatay" }, analiz: { kenar: "alt", yon: "yatay" }, sonuc: { kenar: "alt", yon: "yatay" },
  };
  const YERLESIM_SIRASI = ["aks", "duzenleme", "gorunum", "analiz", "sonuc", "cizim", "degistirme", "olcme"];
  function varsayilan() {
    const y = { surum: SURUM, ad: "varsayilan", kutular: [] };
    YERLESIM_SIRASI.forEach(function (g) { y.kutular.push(yeniKutuNesnesi("k-" + g, grupAdi(g), grupKomutlari(g), VARSAYILAN_DUZEN[g])); });
    return siraNumarala(y);
  }
  /** Hazır yerleşimler: bir işe odaklanır; diğer kutular gizli kalır (yönetici menüsünden açılır). */
  const HAZIR = {
    cizim: { ad: "Çizim", kutular: { aks: { kenar: "ust", yon: "yatay" }, cizim: { kenar: "sol", yon: "dikey", kucuk: false },
      gorunum: { kenar: "sag", yon: "dikey" }, duzenleme: { kenar: "alt", yon: "yatay" } } },
    duzenleme: { ad: "Düzenleme", hizli: ["sec", "olc-uzaklik"], kutular: { duzenleme: { kenar: "sol", yon: "dikey", kucuk: false },
      degistirme: { kenar: "ust", yon: "yatay" }, gorunum: { kenar: "sag", yon: "dikey" } } },
    degistirme: { ad: "Değiştirme", hizli: ["sec", "geri-al", "yinele", "sil"], kutular: { degistirme: { kenar: "sol", yon: "dikey", kucuk: false },
      duzenleme: { kenar: "alt", yon: "yatay" }, gorunum: { kenar: "sag", yon: "dikey" } } },
    olcme: { ad: "Ölçme", hizli: ["sec", "sigdir"], kutular: { olcme: { kenar: "sag", yon: "dikey", kucuk: false },
      gorunum: { kenar: "ust", yon: "yatay" }, aks: { kenar: "alt", yon: "yatay" } } },
    gorunum: { ad: "Görünüm", hizli: ["sec"], kutular: { gorunum: { kenar: "sol", yon: "dikey", kucuk: false }, aks: { kenar: "ust", yon: "yatay" } } },
    analiz: { ad: "Analiz", hizli: ["sec", "olc-uzaklik"], kutular: { analiz: { kenar: "sol", yon: "dikey", kucuk: false },
      sonuc: { kenar: "sag", yon: "dikey" }, gorunum: { kenar: "ust", yon: "yatay" } } },
    sonuc: { ad: "Sonuç", hizli: ["sec", "olc-uzaklik", "olc-koordinat"], kutular: { sonuc: { kenar: "sol", yon: "dikey", kucuk: false },
      gorunum: { kenar: "ust", yon: "yatay" }, analiz: { kenar: "sag", yon: "dikey" } } },
  };
  const HAZIR_ADLARI = Object.freeze(Object.keys(HAZIR).map(function (k) { return { id: k, ad: HAZIR[k].ad }; }).concat([{ id: "varsayilan", ad: "Varsayılan" }]));
  function hazir(ad) {
    if (ad === "varsayilan" || !HAZIR[ad]) return varsayilan();
    const h = HAZIR[ad], y = { surum: SURUM, ad: ad, kutular: [] };
    if (h.hizli) y.kutular.push(yeniKutuNesnesi("k-hizli", "Hızlı", h.hizli, { kenar: "ust", yon: "yatay" }));
    Object.keys(h.kutular).forEach(function (g) { y.kutular.push(yeniKutuNesnesi("k-" + g, grupAdi(g), grupKomutlari(g), h.kutular[g])); });
    GRUPLAR.forEach(function (g) {
      if (!h.kutular[g.id]) y.kutular.push(yeniKutuNesnesi("k-" + g.id, g.ad, grupKomutlari(g.id), Object.assign({}, VARSAYILAN_DUZEN[g.id], { gizli: true })));
    });
    return siraNumarala(y);
  }

  class YerlesimHatasi extends Error { constructor(m) { super(m); this.name = "YerlesimHatasi"; } }
  function konumOku(c) {
    if (!c || typeof c !== "object" || !isFinite(+c.x) || !isFinite(+c.y) || c.x === null || c.y === null) return null;
    return { x: Math.max(0, Math.round(+c.x)), y: Math.max(0, Math.round(+c.y)), yx: c.yx === "sag" ? "sag" : "sol", yy: c.yy === "alt" ? "alt" : "ust" };
  }
  // sürüm 1 → 2 geçişinde çapa kenara bu kadar yakınsa (px) kutu o kenarın şeridine geçer
  const GOC_ESIK = BOSLUK + YAPISMA;
  /**
   * Dışarıdan gelen (JSON/localStorage) yerleşimi denetler ve düzeltir. Yapısal hata → YerlesimHatasi (Türkçe, çözüm önerir).
   * Bilinmeyen komut kimlikleri korunur (sonradan kaydedilebilir; kayıtlı değilken çizilmez). Kutu içi yinelenen komutlar atılır.
   * Sürüm 1 yerleşimi (çapalı konumlar, otoKatli) sürüm 2'ye geçirilir: kutular kenar şeritlerine (rıhtım) yerleşir; kenar çapası
   * kenara değiyorsa ondan (dikey kutu sol/sağ, yatay kutu üst/alt), değmiyorsa eski tercih edilen kenar; şeritteki sıra çapalardan;
   * kendiliğinden katlanmış kutu (otoKatli) açılır. rapor (isteğe bağlı nesne) verilirse geçişte rapor.goc = true olur.
   */
  function dogrula(girdi, rapor) {
    let y = girdi;
    if (typeof y === "string") {
      try { y = JSON.parse(y); } catch (e) { throw new YerlesimHatasi("Yerleşim dosyası JSON olarak okunamadı (" + e.message + ")."); }
    }
    if (!y || typeof y !== "object" || Array.isArray(y)) throw new YerlesimHatasi("Yerleşim bir JSON nesnesi olmalı: {\"surum\": " + SURUM + ", \"kutular\": [...]}.");
    if (y.surum != null && +y.surum > SURUM) throw new YerlesimHatasi("Bu yerleşim daha yeni bir sürümle (" + y.surum + ") kaydedilmiş; uygulamayı güncelleyin.");
    if (!Array.isArray(y.kutular)) throw new YerlesimHatasi("Yerleşimde \"kutular\" listesi yok.");
    if (y.kutular.length > 60) throw new YerlesimHatasi("Yerleşimde çok fazla kutu var (" + y.kutular.length + " > 60).");
    // sürümü yazılmamış (elle yazılmış) yerleşim güncel sürüm sayılır
    const eski = y.surum != null && isFinite(+y.surum) && +y.surum < 2;
    const out = { surum: SURUM, ad: typeof y.ad === "string" ? y.ad.slice(0, 40) : "ozel", kutular: [] };
    const idler = new Set(), capalar = [];
    y.kutular.forEach(function (k, i) {
      if (!k || typeof k !== "object") throw new YerlesimHatasi((i + 1) + ". kutu bir nesne değil.");
      if (!Array.isArray(k.komutlar)) throw new YerlesimHatasi((i + 1) + ". kutuda \"komutlar\" listesi yok.");
      let id = typeof k.id === "string" && /^[\w-]{1,40}$/.test(k.id) ? k.id : "";
      if (!id || idler.has(id)) id = kutuKimligi(out, k.ad ? normal(k.ad) : "kutu");
      idler.add(id);
      const komutlar = [];
      k.komutlar.forEach(function (c) { if (typeof c === "string" && c && c.length <= 60 && komutlar.indexOf(c) < 0) komutlar.push(c); });
      const kk = yeniKutuNesnesi(id, (typeof k.ad === "string" && k.ad.trim() ? k.ad.trim() : "Kutu " + (i + 1)).slice(0, 40), komutlar, {
        yon: k.yon === "dikey" ? "dikey" : "yatay", kucuk: k.kucuk !== false, kilitli: !!k.kilitli, gizli: !!k.gizli, katli: !!k.katli,
        saydamlik: isFinite(+k.saydamlik) ? Math.max(0.3, Math.min(1, +k.saydamlik)) : 1,
        kenar: KENARLAR.indexOf(k.kenar) >= 0 ? k.kenar : "ust",
      });
      const c = konumOku(k.konum);
      if (eski) {
        // sürüm 1: yer kalmadığı için kendiliğinden katlanan kutu (otoKatli) kullanıcının katlaması değildir: açılır
        if (k.otoKatli === true) kk.katli = false;
        if (c) {
          if (kk.yon === "dikey" ? c.x <= GOC_ESIK : c.y <= GOC_ESIK) kk.kenar = kk.yon === "dikey" ? c.yx : c.yy;
        }
        capalar.push(c);
      } else {
        // yüzen kutu (kullanıcı sahneye taşıdı) çapasıyla; kenar şeridindeki kutunun konumu yoktur. yer yazılmamışsa çapa yüzen kutu demektir
        kk.yer = (k.yer === "serbest" || (k.yer == null && c)) && c ? "serbest" : "kenar";
        kk.konum = kk.yer === "serbest" ? c : null;
        kk.sira = k.sira != null && isFinite(+k.sira) && k.sira !== "" ? +k.sira : null;
      }
      out.kutular.push(kk);
    });
    if (eski) {
      // şeritteki sıra çapalardan: bantlarda soldan çapalı kutular soldan sağa, sonra sağdan çapalılar; sütunlarda üstten, sonra alttan
      KENARLAR.forEach(function (kn) {
        const bant = BANTLAR.indexOf(kn) >= 0;
        const l = out.kutular.map(function (k, i) { return { k: k, i: i, c: capalar[i] }; }).filter(function (x) { return x.k.kenar === kn; });
        const grup = function (x) { return !x.c ? 2 : (bant ? x.c.yx === "sol" : x.c.yy === "ust") ? 0 : 1; };
        const ofset = function (x) { return x.c ? (bant ? x.c.x : x.c.y) : 0; };
        l.sort(function (a, b) {
          const ga = grup(a), gb = grup(b);
          if (ga !== gb) return ga - gb;
          if (ga === 0) return (ofset(a) - ofset(b)) || (a.i - b.i);
          if (ga === 1) return (ofset(b) - ofset(a)) || (a.i - b.i);
          return a.i - b.i;
        });
        l.forEach(function (x, n) { x.k.sira = n + 1; });
      });
      if (rapor && typeof rapor === "object") rapor.goc = true;
    } else siraNumarala(out, true);
    return out;
  }
  function kutuBul(y, id) { return y.kutular.find(function (k) { return k.id === id; }) || null; }
  function kutuGerek(y, id) { const k = kutuBul(y, id); if (!k) throw new YerlesimHatasi("Kutu bulunamadı: " + id); return k; }
  /** Komutun bulunduğu kutular. */
  function komutKutulari(y, komut) { return y.kutular.filter(function (k) { return k.komutlar.indexOf(komut) >= 0; }).map(function (k) { return k.id; }); }
  /**
   * Düğme taşı/kopyala. a: {komut, kaynak (kutu id | null: katalogdan ekle), hedef (kutu id), sira (hedefte konum; yoksa sona), kopya}.
   * Aynı kutuda yeniden sıralama da budur. Kilitli kutudan çıkarılamaz, kilitli kutuya eklenemez.
   */
  function dugmeTasi(y0, a) {
    const y = kopya(y0), h = kutuGerek(y, a.hedef);
    if (h.kilitli) throw new YerlesimHatasi("“" + h.ad + "” kutusu kilitli; önce kilidi açın.");
    const kay = a.kaynak ? kutuGerek(y, a.kaynak) : null;
    if (kay && kay.kilitli && !a.kopya) throw new YerlesimHatasi("“" + kay.ad + "” kutusu kilitli; düğme çıkarılamaz (Ctrl ile kopyalayabilirsiniz).");
    let sira = a.sira == null ? h.komutlar.length : Math.max(0, Math.min(+a.sira, h.komutlar.length));
    if (kay && !a.kopya) {
      const i = kay.komutlar.indexOf(a.komut);
      if (i >= 0) { kay.komutlar.splice(i, 1); if (kay === h && i < sira) sira--; }
    }
    const j = h.komutlar.indexOf(a.komut);
    if (j >= 0) { h.komutlar.splice(j, 1); if (j < sira) sira--; }
    h.komutlar.splice(sira, 0, a.komut);
    return y;
  }
  function dugmeCikar(y0, kutuId, komut) {
    const y = kopya(y0), k = kutuGerek(y, kutuId);
    if (k.kilitli) throw new YerlesimHatasi("“" + k.ad + "” kutusu kilitli.");
    k.komutlar = k.komutlar.filter(function (c) { return c !== komut; });
    return y;
  }
  /**
   * Yeni kutu: a = {ad?, komutlar?, konum?, yon?, kenar?}. Dönüş {yerlesim, id}. Konumu verilen kutu (boş alana bırakılan düğme) o
   * çapada yüzer; konumsuz kutu tercih edilen kenarın şeridinin sonuna eklenir (dizinin sonunda: en düşük öncelik).
   */
  function kutuEkle(y0, a) {
    a = a || {};
    const y = kopya(y0);
    let n = 1;
    const adlar = new Set(y.kutular.map(function (k) { return k.ad; }));
    while (adlar.has("Kutu " + n)) n++;
    const ad = (a.ad && String(a.ad).trim()) ? String(a.ad).trim().slice(0, 40) : "Kutu " + n;
    const id = kutuKimligi(y, normal(ad));
    const konum = konumOku(a.konum), kenar = KENARLAR.indexOf(a.kenar) >= 0 ? a.kenar : "ust";
    const sira = y.kutular.reduce(function (m, k) { return k.kenar === kenar && isFinite(k.sira) && k.sira != null ? Math.max(m, +k.sira) : m; }, 0) + 1;
    y.kutular.push(yeniKutuNesnesi(id, ad, a.komutlar || [], { yon: a.yon === "dikey" ? "dikey" : "yatay", konum: konum, yer: konum ? "serbest" : "kenar",
      kenar: kenar, sira: sira, kucuk: a.kucuk !== false }));
    return { yerlesim: y, id: id };
  }
  /** Düğmeyi yeni bir kutuya al (boş alana bırakma): kaynak verilirse (kopya değilse) önce oradan çıkarılır. Dönüş {yerlesim, id}. */
  function kutuEkleTasi(y0, a, komut, kaynak, kopyaMi) {
    const y = kaynak && !kopyaMi ? dugmeCikar(y0, kaynak, komut) : y0;
    return kutuEkle(y, Object.assign({}, a, { komutlar: [komut] }));
  }
  function kutuSil(y0, id) {
    const y = kopya(y0);
    const i = y.kutular.findIndex(function (k) { return k.id === id; });
    if (i < 0) throw new YerlesimHatasi("Kutu bulunamadı: " + id);
    y.kutular.splice(i, 1);
    return y;
  }
  const GUNCELLENEBILIR = ["ad", "yon", "kucuk", "saydamlik", "kilitli", "gizli", "katli", "konum", "kenar", "yer", "sira"];
  function kutuGuncelle(y0, id, alanlar) {
    const y = kopya(y0), k = kutuGerek(y, id);
    Object.keys(alanlar || {}).forEach(function (a) {
      if (GUNCELLENEBILIR.indexOf(a) < 0) return;
      let v = alanlar[a];
      if (a === "ad") { v = String(v || "").trim().slice(0, 40); if (!v) throw new YerlesimHatasi("Kutu adı boş olamaz."); }
      if (a === "yon") v = v === "dikey" ? "dikey" : "yatay";
      if (a === "saydamlik") v = Math.max(0.3, Math.min(1, +v || 1));
      if (a === "kucuk" || a === "kilitli" || a === "gizli" || a === "katli") v = !!v;
      if (a === "kenar" && KENARLAR.indexOf(v) < 0) return;
      if (a === "yer") v = v === "serbest" ? "serbest" : "kenar";
      if (a === "konum") v = konumOku(v);
      if (a === "sira") v = v != null && isFinite(+v) ? +v : null;
      k[a] = v;
    });
    if (k.yer === "serbest" && !k.konum) k.yer = "kenar";       // çapasız kutu yüzemez
    if (k.yer === "kenar") k.konum = null;
    return y;
  }
  /**
   * Kutuyu bir kenar şeridine al ve o şeridin en öncelikli kutusu yap (kullanıcının eylemi kazanır): dizide aynı kenardaki ilk kutunun
   * önüne taşınır, şeritteki sıra (sira) yeniden numaralanır. sec: {once: kutu id (görünür sırada onun önüne) | null (sona)}; sec
   * verilmezse kutu aynı şeritteyse yerinde kalır, başka şeritten geliyorsa sona eklenir.
   */
  function kenaraAl(y0, id, kenar, sec) {
    const y = kopya(y0), i = y.kutular.findIndex(function (k) { return k.id === id; });
    if (i < 0) throw new YerlesimHatasi("Kutu bulunamadı: " + id);
    const k = y.kutular[i], kn = KENARLAR.indexOf(kenar) >= 0 ? kenar : (KENARLAR.indexOf(k.kenar) >= 0 ? k.kenar : "ust");
    const ayniSerit = k.yer !== "serbest" && k.kenar === kn;
    const yerli = y.kutular.map(function (x, n) { return { k: x, i: n }; }).filter(function (x) { return x.k.kenar === kn && x.k.yer !== "serbest"; });
    yerli.sort(function (a, b) {
      const sa = a.k.sira != null && isFinite(a.k.sira) ? +a.k.sira : Infinity, sb = b.k.sira != null && isFinite(b.k.sira) ? +b.k.sira : Infinity;
      return (sa - sb) || (a.i - b.i);
    });
    const sirali = yerli.map(function (x) { return x.k; });
    let yeri = ayniSerit ? sirali.indexOf(k) : sirali.length;
    const digerleri = sirali.filter(function (x) { return x !== k; });
    if (sec && sec.once !== undefined) {
      const j = sec.once == null ? -1 : digerleri.findIndex(function (x) { return x.id === sec.once; });
      yeri = j < 0 ? digerleri.length : j;
    }
    digerleri.splice(Math.max(0, Math.min(yeri, digerleri.length)), 0, k);
    digerleri.forEach(function (x, n) { x.sira = n + 1; });
    k.yer = "kenar"; k.kenar = kn; k.konum = null;
    y.kutular.splice(i, 1);
    const j = y.kutular.findIndex(function (x) { return x.kenar === kn && x.yer !== "serbest"; });
    y.kutular.splice(j < 0 ? Math.min(i, y.kutular.length) : j, 0, k);
    return y;
  }
  /** Kutuyu sahnede yüzdür: yer "serbest", çapa konum ({x, y, yx, yy}); yon verilirse yönü. Önceliği ve dönülecek kenarı korunur. */
  function serbestBirak(y0, id, konum, yon) {
    const y = kopya(y0), k = kutuGerek(y, id), c = konumOku(konum);
    if (!c) throw new YerlesimHatasi("Yüzen kutu için konum gerekli.");
    k.yer = "serbest"; k.konum = c;
    if (yon) k.yon = yon === "dikey" ? "dikey" : "yatay";
    return y;
  }
  /** Kaynak kutunun düğmeleri hedefin sonuna eklenir (yinelenenler atlanır), kaynak silinir. */
  function kutulariBirlestir(y0, hedefId, kaynakId) {
    if (hedefId === kaynakId) throw new YerlesimHatasi("Bir kutu kendisiyle birleştirilemez.");
    const y = kopya(y0), h = kutuGerek(y, hedefId), k = kutuGerek(y, kaynakId);
    if (h.kilitli || k.kilitli) throw new YerlesimHatasi("Kilitli kutular birleştirilemez; önce kilidi açın.");
    k.komutlar.forEach(function (c) { if (h.komutlar.indexOf(c) < 0) h.komutlar.push(c); });
    y.kutular = y.kutular.filter(function (x) { return x.id !== kaynakId; });
    return y;
  }

  // ---- geometri: yapışma, çapa, otomatik yerleşim (px; kapsayıcı koordinatı)
  /** Dikdörtgeni kapsayıcı kenarlarına ve komşu kutulara yapıştırır. r = {x, y, w, h}; digerleri = [{x, y, w, h}]. Dönüş {x, y, kenarX?, kenarY?}. */
  function yapistir(rc, W, H, digerleri, esik, bosluk) {
    esik = esik == null ? YAPISMA : esik; bosluk = bosluk == null ? BOSLUK : bosluk;
    const xs = [[bosluk, "sol"], [W - rc.w - bosluk, "sag"]], ys = [[bosluk, "ust"], [H - rc.h - bosluk, "alt"]];
    (digerleri || []).forEach(function (d) {
      const dikeyYakin = rc.y < d.y + d.h + esik && rc.y + rc.h > d.y - esik;
      const yatayYakin = rc.x < d.x + d.w + esik && rc.x + rc.w > d.x - esik;
      if (dikeyYakin) { xs.push([d.x + d.w + ARALIK, null]); xs.push([d.x - rc.w - ARALIK, null]); }
      if (yatayYakin) { xs.push([d.x, null]); xs.push([d.x + d.w - rc.w, null]); }
      if (yatayYakin) { ys.push([d.y + d.h + ARALIK, null]); ys.push([d.y - rc.h - ARALIK, null]); }
      if (dikeyYakin) { ys.push([d.y, null]); ys.push([d.y + d.h - rc.h, null]); }
    });
    function sec(aday, v) {
      let en = null;
      aday.forEach(function (a) { const d = Math.abs(a[0] - v); if (d <= esik && (!en || d < en[2])) en = [a[0], a[1], d]; });
      return en;
    }
    const ex = sec(xs, rc.x), ey = sec(ys, rc.y);
    let x = Math.max(0, Math.min(ex ? ex[0] : rc.x, Math.max(0, W - rc.w))), y = Math.max(0, Math.min(ey ? ey[0] : rc.y, Math.max(0, H - rc.h)));
    // bırakılan yer başka bir kutuyu örtüyorsa en yakın boş komşu konuma kaydır (yer yoksa kullanıcının seçtiği yer kalır)
    const ortu = function (q) { return (digerleri || []).some(function (d) { return cakisir(q, d, 0); }); };
    if (ortu({ x: x, y: y, w: rc.w, h: rc.h })) {
      let en = null;
      (digerleri || []).forEach(function (d) {
        [[d.x - rc.w - ARALIK, y], [d.x + d.w + ARALIK, y], [x, d.y - rc.h - ARALIK], [x, d.y + d.h + ARALIK]].forEach(function (c) {
          const q = { x: Math.round(c[0]), y: Math.round(c[1]), w: rc.w, h: rc.h };
          if (q.x < 0 || q.y < 0 || q.x + q.w > W || q.y + q.h > H || ortu(q)) return;
          const u = Math.hypot(q.x - x, q.y - y);
          if (!en || u < en.u) en = { x: q.x, y: q.y, u: u };
        });
      });
      if (en) { x = en.x; y = en.y; }
    }
    return { x: Math.round(x), y: Math.round(y), kenarX: ex ? ex[1] : null, kenarY: ey ? ey[1] : null };
  }
  /** Mutlak konumdan en yakın kenarlara göre çapa (pencere boyutu değişince kutu kenarına bağlı kalır). */
  function capa(x, y, w, h, W, H) {
    const yx = x + w / 2 <= W / 2 ? "sol" : "sag", yy = y + h / 2 <= H / 2 ? "ust" : "alt";
    return { x: Math.max(0, Math.round(yx === "sol" ? x : W - x - w)), y: Math.max(0, Math.round(yy === "ust" ? y : H - y - h)), yx: yx, yy: yy };
  }
  /** Çapadan mutlak konum (kapsayıcıya sığdırılmış). */
  function mutlak(k, w, h, W, H) {
    let x = k.yx === "sag" ? W - k.x - w : k.x, y = k.yy === "alt" ? H - k.y - h : k.y;
    x = Math.max(0, Math.min(x, W - w)); y = Math.max(0, Math.min(y, H - h));
    return { x: Math.round(Math.max(0, x)), y: Math.round(Math.max(0, y)) };
  }
  /** Kutunun katla düğmesi (▸ / ▾) kutunun katli durumuna göre. */
  function katlaDugmesi(d, kt) {
    const kb = d && d.querySelector(".arac-kutu-katla");
    if (!kb) return;
    kb.textContent = kt.katli ? "▸" : "▾";
    kb.setAttribute("aria-expanded", String(!kt.katli));
    kb.setAttribute("aria-label", kt.ad + (kt.katli ? " kutusunu aç" : " kutusunu katla"));
    kb.title = kt.katli ? "Aç" : "Katla (yalnız başlık)";
  }
  function cakisir(a, b, ara_) {
    const g = ara_ == null ? ARALIK : ara_;
    return a.x < b.x + b.w + g && a.x + a.w + g > b.x && a.y < b.y + b.h + g && a.y + a.h + g > b.y;
  }
  /**
   * Kutuları tercih ettikleri kenardan (ust/alt/sol/sag) başlayarak çakışmadan yerleştirir (yüzen kutu: "Sahnede yüzdür").
   * liste: [{id, w, h, kenar}] (sırayla); sabitler: zaten yerleşik dikdörtgenler. Dönüş: Map(id → {x, y}). Yer yoksa basamaklı.
   */
  function otomatikYerlestir(liste, W, H, sabitler, bosluk) {
    const b = bosluk == null ? BOSLUK : bosluk, adim = 4;
    const dolu = (sabitler || []).slice(), out = new Map();
    const ara_ = function (w, h, kenar) {
      const xMax = Math.max(b, W - w - b), yMax = Math.max(b, H - h - b);
      const bos = function (x, y) { const q = { x: x, y: y, w: w, h: h }; return !dolu.some(function (d) { return cakisir(q, d); }); };
      if (kenar === "ust" || kenar === "alt") {
        for (let i = 0; i <= (yMax - b) / adim; i++) {
          const y = kenar === "ust" ? b + i * adim : yMax - i * adim;
          for (let x = b; x <= xMax; x += adim) if (bos(x, y)) return { x: x, y: y };
        }
      } else {
        for (let i = 0; i <= (xMax - b) / adim; i++) {
          const x = kenar === "sol" ? b + i * adim : xMax - i * adim;
          for (let y = b; y <= yMax; y += adim) if (bos(x, y)) return { x: x, y: y };
        }
      }
      return null;
    };
    liste.forEach(function (it, n) {
      const w = Math.min(it.w, Math.max(1, W - 2 * b)), h = Math.min(it.h, Math.max(1, H - 2 * b));
      let bulunan = ara_(w, h, it.kenar || "ust");
      if (!bulunan) {   // yer yoksa basamaklı
        const xMax = Math.max(b, W - w - b), yMax = Math.max(b, H - h - b);
        bulunan = { x: Math.min(xMax, b + 24 * (n % 6)), y: Math.min(yMax, b + 24 * (n % 6)), bos: false };
      }
      dolu.push({ x: bulunan.x, y: bulunan.y, w: w, h: h });
      out.set(it.id, bulunan);
    });
    return out;
  }
  /**
   * rc = {x, y, w, h} konumuna en yakın boş yer (dolu dikdörtgenlerin hiçbirine ARALIK'tan yakın değil, kapsayıcının içinde kenardan
   * bosluk kadar içeride): {x, y} | null. Adaylar engellerin kenarları ve kaba bir ızgaradır (saf; yüzen kutunun çakışma geri düşmesi).
   */
  function yakinBos(rc, W, H, dolu, bosluk) {
    const b = bosluk == null ? BOSLUK : bosluk, w = rc.w, h = rc.h;
    const xMax = W - w - b, yMax = H - h - b;
    if (xMax < b - 1e-9 || yMax < b - 1e-9) return null;
    const l = dolu || [];
    const bos = function (x, y) { const q = { x: x, y: y, w: w, h: h }; return !l.some(function (d) { return cakisir(q, d); }); };
    const xs = [rc.x, b, xMax], ys = [rc.y, b, yMax];
    l.forEach(function (d) { xs.push(d.x - w - ARALIK, d.x + d.w + ARALIK, d.x, d.x + d.w - w); ys.push(d.y - h - ARALIK, d.y + d.h + ARALIK, d.y, d.y + d.h - h); });
    for (let x = b; x <= xMax; x += 16) xs.push(x);
    for (let y = b; y <= yMax; y += 16) ys.push(y);
    const kx = Array.from(new Set(xs.map(function (v) { return Math.round(Math.max(b, Math.min(xMax, v))); })));
    const ky = Array.from(new Set(ys.map(function (v) { return Math.round(Math.max(b, Math.min(yMax, v))); })));
    let en = null;
    kx.forEach(function (x) {
      ky.forEach(function (y) {
        const u = Math.hypot(x - rc.x, y - rc.y);
        if (en && u >= en.u) return;
        if (bos(x, y)) en = { x: x, y: y, u: u };
      });
    });
    return en ? { x: en.x, y: en.y } : null;
  }

  // ---- rıhtım (kenar şeridi) yerleşimi: saf işlev; yerleşim yalnız (katman W × H, kutu listesi) ile belirlenir, geçmişi yoktur
  const sutunBicimi = function (it, d) { return (it.katli ? "dk" : "d") + d; };
  // bant (üst/alt şerit): hepsi başlıklı (katlı: katlı başlık); sığmazsa en düşük öncelikliden başa doğru başlıklar gizlenir, yine
  // sığmazsa en düşük öncelikliler çıkar; sonra öncelik sırasıyla başlıklar sığdıkça geri verilir. Tek başına sığmayan kutu baştan çıkar.
  function bantSigdir(kutular, L, g) {
    const f = new Map(), red = [];
    let ic = [];
    kutular.forEach(function (it) {
      const b = it.katli ? "yk" : "yt", en = it.katli ? it.olcu.yk[0] : Math.min(it.olcu.yt[0], it.olcu.yb[0]);
      if (en > L) { red.push(it); return; }
      f.set(it.id, b); ic.push(it);
    });
    const boy = function () { return ic.reduce(function (s, it) { return s + it.olcu[f.get(it.id)][0]; }, 0) + g * Math.max(0, ic.length - 1); };
    for (let i = ic.length - 1; i >= 0 && boy() > L; i--) if (f.get(ic[i].id) === "yt") f.set(ic[i].id, "yb");
    while (ic.length && boy() > L) { const r_ = ic.pop(); f.delete(r_.id); red.push(r_); }
    ic.forEach(function (it) { if (f.get(it.id) === "yb") { f.set(it.id, "yt"); if (boy() > L) f.set(it.id, "yb"); } });
    return { kabul: ic, bicim: f, red: red };
  }
  // sütun (sol/sağ): hepsi tek düğme sütunu (d1) sığıyorsa o; değilse en düşük öncelikliler iki sütunlu biçim (d2) sığana dek çıkar,
  // kalanlar d1'e sığıyorsa d1. Bir sütunda tek biçim.
  function sutunSigdir(kutular, L, g) {
    const red = [];
    let ic = kutular.filter(function (it) { if (it.olcu[sutunBicimi(it, 2)][1] > L) { red.push(it); return false; } return true; });
    const boy = function (l, d) { return l.reduce(function (s, it) { return s + it.olcu[sutunBicimi(it, d)][1]; }, 0) + g * Math.max(0, l.length - 1); };
    let d = 1;
    if (boy(ic, 1) > L) {
      while (ic.length && boy(ic, 2) > L) red.push(ic.pop());
      d = boy(ic, 1) <= L ? 1 : 2;
    }
    const f = new Map();
    ic.forEach(function (it) { f.set(it.id, sutunBicimi(it, d)); });
    return { kabul: ic, bicim: f, red: red, d: d };
  }
  function rihtimGecis(liste, W, H, b, g, kose) {
    const grup = { ust: [], alt: [], sol: [], sag: [] };
    liste.forEach(function (it) { (grup[it.kenar] || grup.ust).push(it); });
    KENARLAR.forEach(function (k) { grup[k].sort(function (p_, q) { return p_.oncelik - q.oncelik; }); });
    const kenarOf = function (it) { return grup[it.kenar] ? it.kenar : "ust"; };
    const kabul = { ust: [], alt: [], sol: [], sag: [] }, bicim = new Map(), yedek = new Set(), tasma = [];
    let red = [];
    const koseW = kose.reduce(function (s, k) { return s + k[0] + g; }, 0), koseH = kose.reduce(function (m, k) { return Math.max(m, k[1]); }, 0);
    const bantL = { ust: W - 2 * b, alt: W - 2 * b - koseW };
    BANTLAR.forEach(function (k) {
      const r_ = bantSigdir(grup[k], bantL[k], g);
      kabul[k] = r_.kabul; r_.bicim.forEach(function (v, id) { bicim.set(id, v); }); red = red.concat(r_.red);
    });
    const kal = function (k) {
      let m = k === "alt" ? koseH : 0;
      kabul[k].forEach(function (it) { m = Math.max(m, it.olcu[bicim.get(it.id)][1]); });
      return m;
    };
    const sahneH = function () { const u = kal("ust"), a = kal("alt"); return H - 2 * b - (u ? u + g : 0) - (a ? a + g : 0); };
    // en küçük sahne yüksekliği: kalmazsa önce üst bandın, sonra alt bandın bütün kutuları çıkar (köşe düğmeleri kalır)
    BANTLAR.forEach(function (k) {
      if (sahneH() < SAHNE_MIN_H && kabul[k].length) { red = red.concat(kabul[k]); kabul[k].forEach(function (it) { bicim.delete(it.id); }); kabul[k] = []; }
    });
    const tU = kal("ust"), tA = kal("alt");
    const y0 = b + (tU ? tU + g : 0), y1 = H - b - (tA ? tA + g : 0), sL = y1 - y0;
    const sd = {}, sw = {};
    SUTUNLAR.forEach(function (k) {
      const r_ = sutunSigdir(grup[k], sL, g);
      kabul[k] = r_.kabul; sd[k] = r_.d; r_.bicim.forEach(function (v, id) { bicim.set(id, v); }); red = red.concat(r_.red);
      sw[k] = r_.kabul.reduce(function (m, it) { return Math.max(m, it.olcu[bicim.get(it.id)][0]); }, 0);
    });
    // en küçük sahne genişliği: kalmazsa önce sağ, sonra sol sütunun bütün kutuları çıkar
    const sahneW = function () { return W - 2 * b - (sw.sol ? sw.sol + g : 0) - (sw.sag ? sw.sag + g : 0); };
    ["sag", "sol"].forEach(function (k) {
      if (sahneW() >= SAHNE_MIN_W || !kabul[k].length) return;
      red = red.concat(kabul[k]); kabul[k].forEach(function (it) { bicim.delete(it.id); }); kabul[k] = []; sw[k] = 0;
    });
    // geri düşme: çıkan kutu öteki (boş olmayan) şeritlere, şeridin kalınlığı / genişliği değişmeden sığıyorsa girer
    const bantBoy = function (k, ek, ekB) {
      return kabul[k].reduce(function (s, it) { return s + it.olcu[bicim.get(it.id)][0]; }, 0) + ek.olcu[ekB][0] + g * kabul[k].length;
    };
    const sutunBoy = function (k, ek, ekB) {
      return kabul[k].reduce(function (s, it) { return s + it.olcu[bicim.get(it.id)][1]; }, 0) + ek.olcu[ekB][1] + g * kabul[k].length;
    };
    red.sort(function (p_, q) { return p_.oncelik - q.oncelik; }).forEach(function (it) {
      const kn = kenarOf(it), bantMi = BANTLAR.indexOf(kn) >= 0;
      const adaylar = bantMi ? [kn === "alt" ? "ust" : "alt", "sol", "sag"] : [kn === "sol" ? "sag" : "sol", "alt", "ust"];
      for (let i = 0; i < adaylar.length; i++) {
        const k = adaylar[i];
        if (!kabul[k].length) continue;
        if (BANTLAR.indexOf(k) >= 0) {
          const t = kal(k), bic = it.katli ? ["yk"] : ["yt", "yb"];
          const uy = bic.find(function (x) { return it.olcu[x][1] <= t && bantBoy(k, it, x) <= bantL[k]; });
          if (uy) { kabul[k].push(it); bicim.set(it.id, uy); yedek.add(it.id); return; }
        } else {
          const x = sutunBicimi(it, sd[k]);
          if (it.olcu[x][0] <= sw[k] && sutunBoy(k, it, x) <= sL) { kabul[k].push(it); bicim.set(it.id, x); yedek.add(it.id); return; }
        }
      }
      tasma.push(it.id);
    });
    // konumlar: şeritte önce kendi kutuları (sira, eşitse öncelik), sonra geri düşenler (öncelik)
    const out = new Map(), koseR = [];
    const sirala = function (l) {
      return l.slice().sort(function (p_, q) {
        const yp = yedek.has(p_.id), yq = yedek.has(q.id);
        if (yp !== yq) return yp ? 1 : -1;
        return (yp ? 0 : (p_.sira - q.sira)) || (p_.oncelik - q.oncelik);
      });
    };
    let x = b;
    kose.forEach(function (k) { koseR.push({ x: x, y: H - b - k[1], w: k[0], h: k[1] }); x += k[0] + g; });
    BANTLAR.forEach(function (k) {
      let xx = k === "alt" ? b + koseW : b;
      sirala(kabul[k]).forEach(function (it) {
        const s = it.olcu[bicim.get(it.id)];
        out.set(it.id, { x: xx, y: k === "ust" ? b : H - b - s[1], w: s[0], h: s[1], bicim: bicim.get(it.id), kenar: k, yedek: yedek.has(it.id) });
        xx += s[0] + g;
      });
    });
    SUTUNLAR.forEach(function (k) {
      let yy = y0;
      sirala(kabul[k]).forEach(function (it) {
        const bc = bicim.get(it.id), s = it.olcu[bc], cip = bc.charAt(1) === "k", w = cip ? sw[k] : s[0];
        out.set(it.id, { x: k === "sol" ? b : W - b - w, y: yy, w: w, h: s[1], bicim: bc, kenar: k, sutunW: sw[k], yedek: yedek.has(it.id) });
        yy += s[1] + g;
      });
    });
    return { kutular: out, tasma: tasma, kose: koseR, tasmaDugme: null,
      pay: { sol: sw.sol ? b + sw.sol : 0, sag: sw.sag ? b + sw.sag : 0, ust: tU ? b + tU : 0, alt: tA ? b + tA : 0 } };
  }
  /**
   * Rıhtım yerleşimi (saf). liste: [{id, kenar, sira, oncelik, katli, olcu: {yt, yb, yk, d1, d2, dk1, dk2: [w, h]}}] — yalnız kenardaki,
   * gizli olmayan kutular; oncelik = dizideki sıra (küçük = önemli). W × H: araç katmanı (px).
   * sec: {bosluk (8), aralik (6), kose: [[w, h]] (sol alt köşedeki düğmeler: yönetici), tasma: [w, h] (taşma düğmesi), tasmaZorla}.
   * Dönüş: {kutular: Map(id → {x, y, w, h, bicim, kenar, sutunW?, yedek}), tasma: [id] (sığmayanlar, öncelik sırasıyla),
   * kose: [{x, y, w, h}], tasmaDugme: {x, y, w, h} | null, pay: {sol, ust, sag, alt}}. Taşan kutu varsa ikinci geçiş taşma düğmesini
   * köşeye ekleyerek yapılır (belirlenimci). Şeritler sahneden tam pay kadar yer alır: kenar payları sığdırılan modeli kutulardan korur.
   */
  function rihtim(liste, W, H, sec) {
    sec = sec || {};
    const b = sec.bosluk == null ? BOSLUK : sec.bosluk, g = sec.aralik == null ? ARALIK : sec.aralik, kose = (sec.kose || []).slice();
    const r_ = rihtimGecis(liste || [], W, H, b, g, kose);
    if ((!r_.tasma.length && !sec.tasmaZorla) || !sec.tasma) return r_;
    const r2 = rihtimGecis(liste || [], W, H, b, g, kose.concat([sec.tasma]));
    r2.tasmaDugme = r2.kose.pop();
    return r2;
  }

  /**
   * Kenara yaslı görünür kutuların sahneden kapladığı paylar (px): {sol, ust, sag, alt}. kutular: [{x, y, w, h}] (kapsayıcı koordinatı).
   * Bir kutu değdiği (ya da kenara yaslı bir kutuya bitişik) kenarlardan payı en küçük olana sayılır; ortada yüzen kutu sayılmaz.
   */
  function kenarPaylariHesapla(kutular, W, H, esik) {
    const e = esik == null ? BOSLUK + YAPISMA : esik, pay = { sol: 0, ust: 0, sag: 0, alt: 0 };
    const l = (kutular || []).filter(function (k) { return k && k.w > 0 && k.h > 0; }).map(function (k) {
      return { k: k, p: { sol: k.x + k.w, ust: k.y + k.h, sag: W - k.x, alt: H - k.y }, kenar: null };
    });
    const ata = function (q, adaylar) {
      let en = null;
      adaylar.forEach(function (a) { if (!en || q.p[a] < q.p[en]) en = a; });
      q.kenar = en;
    };
    l.forEach(function (q) {
      const k = q.k, d = [];
      if (k.x <= e) d.push("sol");
      if (k.y <= e) d.push("ust");
      if (W - (k.x + k.w) <= e) d.push("sag");
      if (H - (k.y + k.h) <= e) d.push("alt");
      // boydan boya dikey sütun (üst ve alt kenara değer, yan kenara değmez; ör. sol kenarda yönetici düğmesinin yanına itilmiş Çizim
      // kutusu) yakın olduğu yan kenarın payıdır; boydan boya yatay şerit için tersi (yoksa bütün yüksekliği / genişliği pay sayılırdı)
      if (d.indexOf("ust") >= 0 && d.indexOf("alt") >= 0 && d.indexOf("sol") < 0 && d.indexOf("sag") < 0) d.push(q.p.sol <= q.p.sag ? "sol" : "sag");
      if (d.indexOf("sol") >= 0 && d.indexOf("sag") >= 0 && d.indexOf("ust") < 0 && d.indexOf("alt") < 0) d.push(q.p.ust <= q.p.alt ? "ust" : "alt");
      // sütun biçimli kutu (boyu eninin iki katından çok) yalnız üst ya da alt kenara değiyorsa yakın yan kenarın payı da adaydır: tam
      // ekranda kapsayıcı uzayınca yönetici düğmesinin yanındaki Çizim sütunu alta değmez olur, bütün boyu üst pay sayılırsa Sığdır
      // modeli ince bir şeride (öteki kutuların altına) sıkıştırır. Şerit biçimli kutu yalnız bir yan kenara değiyorsa tersi.
      if (d.length && k.h > 2 * k.w && d.indexOf("sol") < 0 && d.indexOf("sag") < 0) d.push(q.p.sol <= q.p.sag ? "sol" : "sag");
      if (d.length && k.w > 2 * k.h && d.indexOf("ust") < 0 && d.indexOf("alt") < 0) d.push(q.p.ust <= q.p.alt ? "ust" : "alt");
      if (d.length) ata(q, d);
    });
    // kenara yaslı kutuya bitişik (ikinci sıra / sütun) kutular aynı kenara
    for (let tur = 0, degisti = true; degisti && tur < 8; tur++) {
      degisti = false;
      l.forEach(function (q) {
        if (q.kenar) return;
        const k = q.k, ad = [];
        l.forEach(function (r_) {
          if (!r_.kenar || r_ === q) return;
          const m = r_.k, g = ARALIK + 6;
          const yatayOrt = k.x < m.x + m.w && k.x + k.w > m.x, dikeyOrt = k.y < m.y + m.h && k.y + k.h > m.y;
          if (r_.kenar === "ust" && yatayOrt && Math.abs(k.y - (m.y + m.h)) <= g) ad.push("ust");
          if (r_.kenar === "alt" && yatayOrt && Math.abs(m.y - (k.y + k.h)) <= g) ad.push("alt");
          if (r_.kenar === "sol" && dikeyOrt && Math.abs(k.x - (m.x + m.w)) <= g) ad.push("sol");
          if (r_.kenar === "sag" && dikeyOrt && Math.abs(m.x - (k.x + k.w)) <= g) ad.push("sag");
        });
        if (ad.length) { ata(q, ad); degisti = true; }
      });
    }
    l.forEach(function (q) { if (q.kenar) pay[q.kenar] = Math.max(pay[q.kenar], q.p[q.kenar]); });
    return pay;
  }

  const Duzen = Object.freeze({
    varsayilan: varsayilan, hazir: hazir, HAZIR_ADLARI: HAZIR_ADLARI, dogrula: dogrula, kutuBul: kutuBul, komutKutulari: komutKutulari,
    dugmeTasi: dugmeTasi, dugmeCikar: dugmeCikar, kutuEkle: kutuEkle, kutuEkleTasi: kutuEkleTasi, kutuSil: kutuSil, kutuGuncelle: kutuGuncelle,
    kutulariBirlestir: kutulariBirlestir, yapistir: yapistir, capa: capa, mutlak: mutlak, cakisir: cakisir, otomatikYerlestir: otomatikYerlestir,
    kenarPaylari: kenarPaylariHesapla, rihtim: rihtim, kenaraAl: kenaraAl, serbestBirak: serbestBirak, yakinBos: yakinBos, siraNumarala: siraNumarala,
    SAHNE_MIN_H: SAHNE_MIN_H, SAHNE_MIN_W: SAHNE_MIN_W,
  });

  // ================================================================= KOMUT KAYDI (modül düzeyi; bütün kutu yöneticileri paylaşır)
  const kayit = new Map();
  const dinleyiciler = new Set();
  const yoneticiler = new Set();
  function yay(ad, veri) {
    dinleyiciler.forEach(function (f) { try { f(ad, veri); } catch (e) { /* dinleyici hatası kutuları bozmasın */ } });
  }
  /**
   * Komut kaydı (yeniden kayıt alanları birleştirir). Dönüş: kayıtlı komut.
   *  t = {id, ad?, ikon?, grup_varsayilan?, kisayol?, ipucu?, tur?, etkin?, secili?, calistir?, secenekler?, secenek?, secenekSec?}
   */
  function komutKaydet(t) {
    if (!t || typeof t.id !== "string" || !t.id) throw new Error("komutKaydet: \"id\" gerekli.");
    const ana = KATALOG_HARITA.get(t.id) || {};
    const eski = kayit.get(t.id) || {};
    const k = Object.assign({}, ana, eski);
    k.id = t.id;      // kataloğun dışındaki sayfa komutları (ör. "ifc", "duvar") için de
    ["ad", "ikon", "kisayol", "ipucu", "tur", "etkin", "secili", "calistir", "secenekler", "secenek", "secenekSec", "neden"].forEach(function (a) {
      if (t[a] !== undefined) k[a] = t[a];
    });
    if (t.grup_varsayilan !== undefined) k.grup = t.grup_varsayilan;
    if (!k.ad) k.ad = t.id;
    if (!k.ikon) k.ikon = "diger";
    if (!k.tur) k.tur = "eylem";
    if (!k.grup) k.grup = "diger";
    if (k.secenekler && k._secenek == null) k._secenek = k.secenekler[0] && k.secenekler[0].id;
    k._kisayol = kisayolCoz(k.kisayol);
    kayit.set(t.id, k);
    yoneticiler.forEach(function (y) { y._kayitDegisti(); });
    return k;
  }
  /** Çoklu bağlama: {id: fn | {calistir, etkin, secili, ...}}. Katalogdaki her komutu da bağlantısız hâliyle kaydeder. */
  function baglar(harita) {
    katalogKaydet();
    Object.keys(harita || {}).forEach(function (id) {
      const v = harita[id];
      komutKaydet(Object.assign({ id: id }, typeof v === "function" ? { calistir: v } : v));
    });
  }
  /** Varsayılan kataloğun bütün komutlarını (bağlı değilse soluk görünür) kaydeder. */
  function katalogKaydet() { KATALOG.forEach(function (k) { if (!kayit.has(k.id)) kayit.set(k.id, Object.assign({}, k, { _kisayol: kisayolCoz(k.kisayol), _secenek: k.secenekler ? k.secenekler[0].id : null })); }); }
  function komut(id) { return kayit.get(id) || null; }
  function komutlar() { return Array.from(kayit.values()); }
  function bagliMi(k) { return !!(k && typeof k.calistir === "function"); }
  function etkinMi(k) {
    if (!bagliMi(k)) return false;
    if (typeof k.etkin === "function") { try { return !!k.etkin(); } catch (e) { return false; } }
    return k.etkin !== false;
  }
  /** Komut kullanılamıyorsa nedeni (komutun neden alanı: metin ya da işlev → metin | null; sözleşme C8); yoksa null. */
  function nedenMetni(k) {
    if (!k) return null;
    if (!bagliMi(k)) return "Bu sayfada henüz bağlı değil.";
    if (k.neden == null) return null;
    let v = null;
    try { v = typeof k.neden === "function" ? k.neden() : k.neden; } catch (e) { v = null; }
    return v == null || v === "" ? null : String(v);
  }
  function seciliMi(k) {
    if (!k || typeof k.secili !== "function") return false;
    try { return !!k.secili(); } catch (e) { return false; }
  }
  function secenekDegeri(k) {
    if (!k || !k.secenekler) return null;
    if (typeof k.secenek === "function") { try { const v = k.secenek(); if (v != null) return v; } catch (e) { /* yoksay */ } }
    return k._secenek != null ? k._secenek : k.secenekler[0].id;
  }
  function secenekAyarla(k, id) {
    k._secenek = id;
    if (typeof k.secenekSec === "function") k.secenekSec(id);
  }
  /** Komutu çalıştır. Etkin değilse çalıştırmaz, false döner ve "reddedildi" olayını ({id, neden}) yayar (sayfa bildirimi gösterir). */
  function calistir(id, olay) {
    const k = komut(id);
    if (!etkinMi(k)) { yay("reddedildi", { id: id, neden: nedenMetni(k), ad: k ? k.ad : id }); return false; }
    try { k.calistir(olay || null, k); } finally {
      yay("calistir", { id: id });
      yoneticiler.forEach(function (y) { y.yenile(); });
    }
    return true;
  }
  /** Kısayol tablosu: [{id, kisayol}] (çakışma denetimi ve yardım için). */
  function kisayollar() {
    return komutlar().filter(function (k) { return k._kisayol; }).map(function (k) { return { id: k.id, ad: k.ad, kisayol: kisayolMetni(k.kisayol) }; });
  }

  // ================================================================= DOM (yalnız tarayıcıda çalışır)
  function el(etiket, sinif, ozellik) {
    const e = document.createElement(etiket);
    if (sinif) e.className = sinif;
    if (ozellik) Object.keys(ozellik).forEach(function (a) { if (ozellik[a] != null) e.setAttribute(a, ozellik[a]); });
    return e;
  }
  function yazmaAlani(t) {
    if (!t || !t.tagName) return false;
    const a = t.tagName;
    return a === "INPUT" || a === "TEXTAREA" || a === "SELECT" || t.isContentEditable;
  }
  function hareketAz() { try { return window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return false; } }
  /** Menü, iletişim kutusu ve sürükleme hayaleti: tam ekrandaki öğenin içine (Fullscreen API'de yalnız o öğenin alt ağacı görünür), yoksa gövdeye. */
  function ustKatman() { return document.fullscreenElement || document.webkitFullscreenElement || document.body; }

  /** Dokunmatik uzun basmadan sonra parmak kalkınca tarayıcının ürettiği tek tıklamayı (450 ms içinde) yutar. */
  function belgeTikYut() {
    const yut = function (ev) { ev.stopPropagation(); ev.preventDefault(); document.removeEventListener("click", yut, true); };
    document.addEventListener("click", yut, true);
    setTimeout(function () { document.removeEventListener("click", yut, true); }, 450);
  }

  // ---- ortak açılır menü (role="menu"; alt menü içerikle yer değiştirir)
  let acikMenu = null;
  function menuKapat(odakGeri) {
    if (!acikMenu) return;
    const m = acikMenu;
    acikMenu = null;
    document.removeEventListener("pointerdown", m.disari, true);
    if (m.el.parentNode) m.el.parentNode.removeChild(m.el);
    if (odakGeri !== false && m.donus && m.donus.focus) { try { m.donus.focus({ preventScroll: true }); } catch (e) { /* yoksay */ } }
    if (m.kapaninca) m.kapaninca();
  }
  /**
   * ogeler: [{ad, ikon?, kisayol?, calistir?, soluk?, isaret? (true/false: onay kutusu), radyo?, alt? (öğeler), ayrac?, baslik?}]
   * konum: {x, y} (istemci px) ya da öğe (yanına açılır). sec: {donus (odak), etiket, kapaninca, sinif}
   */
  function menuAc(ogeler, konum, sec) {
    menuKapat(false);
    sec = sec || {};
    const m = el("div", "arac-menu" + (sec.sinif ? " " + sec.sinif : ""), { role: "menu", "aria-label": sec.etiket || "Menü", tabindex: "-1" });
    const yigin = [];
    function doldur(liste, geri) {
      m.innerHTML = "";
      if (geri) {
        const g = el("button", "arac-menu-oge arac-menu-geri", { type: "button", role: "menuitem" });
        g.innerHTML = '<span class="arac-menu-ok" aria-hidden="true">‹</span><span>' + kacis(geri) + "</span>";
        g.addEventListener("click", function () { const u = yigin.pop(); doldur(u.liste, u.geri); });
        m.appendChild(g);
      }
      liste.forEach(function (o_) {
        if (o_.ayrac) { m.appendChild(el("div", "arac-menu-ayrac", { role: "separator" })); return; }
        if (o_.baslik) { const b = el("div", "arac-menu-baslik"); b.textContent = o_.baslik; m.appendChild(b); return; }
        const rol = o_.radyo ? "menuitemradio" : (o_.isaret != null ? "menuitemcheckbox" : "menuitem");
        const b = el("button", "arac-menu-oge" + (o_.soluk ? " soluk" : ""), { type: "button", role: rol });
        if (o_.isaret != null || o_.radyo) b.setAttribute("aria-checked", o_.isaret ? "true" : "false");
        if (o_.soluk) b.setAttribute("aria-disabled", "true");
        if (o_.alt) b.setAttribute("aria-haspopup", "menu");
        b.innerHTML = (o_.ikon ? ikonSvg(o_.ikon, "arac-menu-ikon") : '<span class="arac-menu-ikon arac-menu-isaret" aria-hidden="true">' + (o_.isaret ? "✓" : "") + "</span>") +
          '<span class="arac-menu-ad">' + kacis(o_.ad) + "</span>" + (o_.kisayol ? '<kbd class="arac-kbd">' + kacis(o_.kisayol) + "</kbd>" : "") +
          (o_.alt ? '<span class="arac-menu-ok" aria-hidden="true">›</span>' : "") + (o_.ipucu ? "" : "");
        if (o_.ipucu) b.title = o_.ipucu;
        b.addEventListener("click", function (e) {
          if (o_.soluk) return;
          if (o_.alt) { yigin.push({ liste: liste, geri: geri }); doldur(o_.alt, o_.ad); return; }
          menuKapat(o_.odakGeri !== false);
          if (o_.calistir) o_.calistir(e);
        });
        m.appendChild(b);
      });
      const ilk = m.querySelector(".arac-menu-oge:not(.soluk)") || m.querySelector(".arac-menu-oge");
      if (ilk) setTimeout(function () { try { ilk.focus({ preventScroll: true }); } catch (e) { /* yoksay */ } }, 0);
      konumla();
    }
    function konumla() {
      const vw = window.innerWidth, vh = window.innerHeight;
      m.style.left = "0px"; m.style.top = "0px";
      const r_ = m.getBoundingClientRect();
      let x, y;
      if (konum && konum.getBoundingClientRect) {
        const a = konum.getBoundingClientRect();
        if (sec.yan) { x = a.right + 4; y = a.top; if (x + r_.width > vw - 4) x = a.left - r_.width - 4; }
        else { x = a.left; y = a.bottom + 4; if (y + r_.height > vh - 4) y = a.top - r_.height - 4; }
      } else { x = konum ? konum.x : 8; y = konum ? konum.y : 8; }
      x = Math.max(4, Math.min(x, vw - r_.width - 4)); y = Math.max(4, Math.min(y, vh - r_.height - 4));
      m.style.left = Math.round(x) + "px"; m.style.top = Math.round(y) + "px";
    }
    m.addEventListener("keydown", function (e) {
      const ogeler_ = Array.from(m.querySelectorAll(".arac-menu-oge"));
      const i = ogeler_.indexOf(document.activeElement);
      const git = function (j) { const n = ogeler_.length; if (!n) return; const t = ogeler_[(j + n) % n]; t.focus(); };
      if (e.key === "ArrowDown") { git(i + 1); e.preventDefault(); }
      else if (e.key === "ArrowUp") { git(i - 1); e.preventDefault(); }
      else if (e.key === "Home") { git(0); e.preventDefault(); }
      else if (e.key === "End") { git(ogeler_.length - 1); e.preventDefault(); }
      else if (e.key === "Escape") { menuKapat(); e.preventDefault(); e.stopPropagation(); }
      else if (e.key === "ArrowLeft" && yigin.length) { const u = yigin.pop(); doldur(u.liste, u.geri); e.preventDefault(); }
      else if (e.key === "ArrowRight" && document.activeElement && document.activeElement.getAttribute("aria-haspopup")) { document.activeElement.click(); e.preventDefault(); }
      else if (e.key === "Tab") { menuKapat(); }
    });
    ustKatman().appendChild(m);
    const kayit_ = { el: m, donus: sec.donus || null, kapaninca: sec.kapaninca || null,
      disari: function (e) { if (!m.contains(e.target)) menuKapat(false); } };
    acikMenu = kayit_;
    document.addEventListener("pointerdown", kayit_.disari, true);
    doldur(ogeler, null);
    return m;
  }

  // ---- küçük iletişim kutusu (ad değiştir, saydamlık, içe aktar)
  function diyalogAc(baslik, govde, dugmeler, konum, donus) {
    menuKapat(false);
    const d = el("div", "arac-diyalog", { role: "dialog", "aria-label": baslik, "aria-modal": "false" });
    d.innerHTML = '<div class="arac-diyalog-baslik">' + kacis(baslik) + '</div><div class="arac-diyalog-govde"></div><div class="arac-diyalog-dugmeler"></div>';
    const g = d.querySelector(".arac-diyalog-govde"), b = d.querySelector(".arac-diyalog-dugmeler");
    if (typeof govde === "string") g.innerHTML = govde; else if (govde) g.appendChild(govde);
    function kapat() {
      document.removeEventListener("pointerdown", disari, true);
      if (d.parentNode) d.parentNode.removeChild(d);
      if (donus && donus.focus) { try { donus.focus({ preventScroll: true }); } catch (e) { /* yoksay */ } }
    }
    (dugmeler || []).forEach(function (x) {
      const bt = el("button", "arac-diyalog-dugme" + (x.ana ? " ana" : ""), { type: "button" });
      bt.textContent = x.ad;
      bt.addEventListener("click", function () { if (x.calistir && x.calistir(d) === false) return; kapat(); });
      b.appendChild(bt);
    });
    d.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { kapat(); e.preventDefault(); e.stopPropagation(); }
      else if (e.key === "Enter" && e.target.tagName === "INPUT" && e.target.type !== "range") {
        const ana = d.querySelector(".arac-diyalog-dugme.ana"); if (ana) { ana.click(); e.preventDefault(); }
      }
    });
    function disari(e) { if (!d.contains(e.target)) kapat(); }
    ustKatman().appendChild(d);
    const vw = window.innerWidth, vh = window.innerHeight, r_ = d.getBoundingClientRect();
    let x = konum ? konum.x : (vw - r_.width) / 2, y = konum ? konum.y : (vh - r_.height) / 3;
    d.style.left = Math.round(Math.max(4, Math.min(x, vw - r_.width - 4))) + "px";
    d.style.top = Math.round(Math.max(4, Math.min(y, vh - r_.height - 4))) + "px";
    setTimeout(function () { document.addEventListener("pointerdown", disari, true); const i = d.querySelector("input, button"); if (i) i.focus(); }, 0);
    return { el: d, kapat: kapat };
  }

  /**
   * Araç kutusu yöneticisi: bir kapsayıcının üstünde yüzen kutular.
   *  sec: { anahtar (localStorage), yonetici (true: köşede yönetici düğmesi), kisayollar (true), mobilGenislik (640),
   *         olay(ad, veri) ("calistir" | "yerlesim" | "ozellestir"), yerlesim (başlangıç; yoksa kayıtlı ya da varsayılan) }
   */
  const GOC_ILETISI = "Araç kutuları kenar yerleşimine geçirildi; bir kutuyu sahneye sürükleyerek yüzdürebilirsiniz.";
  function Yonetici(kap, sec) {
    this.kap = kap;
    this.sec = sec || {};
    this.anahtar = this.sec.anahtar || ANAHTAR;
    this.ozellestirKipi = false;
    this.mobil = false;
    this.seritKatli = false;
    this.secilenKutu = null;
    this._tikYut = false;     // sürükleme / uzun basma sonrası gelen tek tıklamayı yut
    katalogKaydet();
    let y = null;
    const rapor = {};
    if (this.sec.yerlesim) { try { y = dogrula(this.sec.yerlesim, rapor); } catch (e) { y = null; } }
    if (!y) y = this._oku(rapor);
    this.y = y || varsayilan();
    this._tasmaAcik = false;
    this._tasan = [];
    if (getComputedStyle(kap).position === "static") kap.style.position = "relative";
    this.kok = el("div", "arac-kok");
    this.kok.setAttribute("data-arac", "");
    kap.appendChild(this.kok);
    this.ipucuEl = el("div", "arac-ipucu", { role: "tooltip", id: "arac-ipucu-" + Math.random().toString(36).slice(2, 8) });
    this.ipucuEl.hidden = true;
    this.bildirimEl = el("div", "arac-bildirim", { role: "status", "aria-live": "polite" });
    this._olaylar();
    this.ciz();
    const self = this;
    // sürüm 1 yerleşimi kenar şeritlerine geçirildi: bir kez kaydedilir ve söylenir
    if (rapor.goc && y) { this._kaydet(); this.bildir(GOC_ILETISI); }
    if (typeof ResizeObserver === "function") {
      this._ro = new ResizeObserver(function () { self._boyutDegisti(); });
      this._ro.observe(kap);
    } else window.addEventListener("resize", this._pencereBoyut = function () { self._boyutDegisti(); });
    // yazı tipleri sonradan yüklenince kutular genişleyebilir: ölçüler (biçim başına önbellek) silinir, son boylarıyla yeniden yerleşir
    const sonra = function () { if (self.kok.isConnected && !self.mobil) { self._olcuSil(); self._konumla(); } };
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(sonra);
    try { if (document.fonts && document.fonts.ready) document.fonts.ready.then(sonra, function () { /* yoksay */ }); } catch (e) { /* yoksay */ }
    yoneticiler.add(this);
  }
  const Y = Yonetici.prototype;
  Y._oku = function (rapor) {
    try {
      const m = window.localStorage.getItem(this.anahtar);
      return m ? dogrula(m, rapor) : null;
    } catch (e) { return null; }
  };
  Y._kaydet = function () {
    try { window.localStorage.setItem(this.anahtar, JSON.stringify(this.y)); } catch (e) { /* özel pencere / kota: yerleşim yalnız bu oturumda */ }
    this._olay("yerlesim", { yerlesim: this.yerlesim() });
  };
  Y._olay = function (ad, veri) { if (this.sec.olay) { try { this.sec.olay(ad, veri); } catch (e) { /* yoksay */ } } yay(ad, veri); };
  Y._kayitDegisti = function () {
    if (this._kayitZ) return;
    const self = this;
    this._kayitZ = setTimeout(function () { self._kayitZ = 0; self.ciz(); }, 0);
  };
  Y.bildir = function (metin) {
    const b = this.bildirimEl;
    b.textContent = metin;
    b.classList.add("gorunur");
    clearTimeout(this._bildirimZ);
    this._bildirimZ = setTimeout(function () { b.classList.remove("gorunur"); }, 2600);
  };
  Y.yerlesim = function () { return kopya(this.y); };
  Y.yerlesimYukle = function (girdi) {
    const rapor = {};
    const y = dogrula(girdi, rapor);   // hata fırlatır (çağıran gösterir)
    this.y = y;
    this._kaydet();
    this.ciz();
    if (rapor.goc) this.bildir(GOC_ILETISI);
    return this.yerlesim();
  };
  Y._uygula = function (yeni, mesaj) {
    this.y = yeni;
    this._kaydet();
    this.ciz();
    if (mesaj) this.bildir(mesaj);
  };
  Y._dene = function (f, mesaj) {
    try { this._uygula(f(), mesaj); return true; } catch (e) { this.bildir(e.message || String(e)); return false; }
  };
  Y.hazirYerlesim = function (ad) {
    const y = hazir(ad);
    this._uygula(y, "Yerleşim: " + ((HAZIR[ad] && HAZIR[ad].ad) || "Varsayılan"));
  };
  Y.varsayilanaDon = function () { this.hazirYerlesim("varsayilan"); };

  // ---- çizim
  Y.ciz = function () {
    const odak = this._odakAl();
    const W = this.kap.clientWidth;
    this.mobil = W > 0 && W < (this.sec.mobilGenislik || MOBIL);
    this._tasmaBelgeBirak();
    this.kok.innerHTML = "";
    this.kok.classList.toggle("arac-mobil", this.mobil);
    this.kok.classList.toggle("arac-ozellestir-kipi", this.ozellestirKipi);
    // sekme sırası: yönetici düğmesi, taşma düğmesi (_konumla ekler), sonra kutular
    if (this.sec.yonetici !== false && !this.mobil) {
      const yb = el("button", "arac-yonetici-ac", { type: "button", "aria-label": "Araç kutuları menüsü", "aria-haspopup": "menu", title: "Araç kutuları: yeni kutu, özelleştir, hazır yerleşimler" });
      yb.innerHTML = ikonSvg("yonetici");
      this.kok.appendChild(yb);
    }
    if (this.mobil) { this._seritCiz(); this._tasmaAcik = false; this._tasan = []; this._rihtim = null; } else this._kutulariCiz();
    if (this.ozellestirKipi) this._ozellestirCiz();
    this.kok.appendChild(this.ipucuEl);
    this.kok.appendChild(this.bildirimEl);
    if (!this.mobil) this._konumla();
    this.yenile();
    this._odakVer(odak);
  };
  // yeniden çizimde (kutular yeni öğeler) odaktaki denetim geri odaklanır: kutu + komut / katla / menü düğmesi, yönetici, taşma düğmesi
  Y._odakAl = function () {
    const a = typeof document !== "undefined" ? document.activeElement : null;
    if (!a || !this.kok.contains(a)) return null;
    const kd = a.closest && a.closest("[data-kutu]");
    if (a.classList.contains("arac-tasma-ac")) return { sec: ".arac-tasma-ac" };
    if (a.classList.contains("arac-yonetici-ac")) return { sec: ".arac-yonetici-ac" };
    if (!kd) return null;
    const k = kd.getAttribute("data-kutu"), q = '[data-kutu="' + k + '"] ';
    if (a.classList.contains("arac-dugme")) return { sec: q + '.arac-dugme[data-komut="' + a.getAttribute("data-komut") + '"]', yedek: q + ".arac-kutu-katla" };
    if (a.classList.contains("arac-kutu-katla")) return { sec: q + ".arac-kutu-katla" };
    if (a.classList.contains("arac-kutu-menu-ac")) return { sec: q + ".arac-kutu-menu-ac" };
    return null;
  };
  Y._odakVer = function (o) {
    if (!o) return;
    let t = null;
    try { t = this.kok.querySelector(o.sec) || (o.yedek ? this.kok.querySelector(o.yedek) : null); } catch (e) { t = null; }
    if (!t || !t.offsetParent) return;
    const tb = t.closest("[role=toolbar]");
    if (tb && t.tabIndex < 0) { tb.querySelectorAll(".arac-dugme, .arac-kutu-katla, .arac-kutu-menu-ac").forEach(function (x) { x.tabIndex = x === t ? 0 : -1; }); tb._son = t; }
    try { t.focus({ preventScroll: true }); } catch (e) { /* yoksay */ }
  };
  Y._dugmeHtml = function (k) {
    const sec_ = k.secenekler ? secenekDegeri(k) : null;
    const sO = sec_ != null ? k.secenekler.find(function (s) { return s.id === sec_; }) : null;
    const ikon = sO && sO.ikon ? sO.ikon : k.ikon;
    const ks = kisayolMetni(k.kisayol);
    const pres = k.tur === "kip" || k.tur === "anahtar";
    return '<button type="button" class="arac-dugme" data-komut="' + kacis(k.id) + '" tabindex="-1" aria-label="' + kacis(k.ad + (sO ? ": " + sO.ad : "")) + '"' +
      (pres ? ' aria-pressed="false"' : "") + (k.secenekler ? ' aria-haspopup="menu"' : "") + (ks ? ' aria-keyshortcuts="' + kacis(ks) + '"' : "") + ">" +
      ikonSvg(ikon) + '<span class="arac-ad">' + kacis(k.ad) + "</span>" + (k.secenekler ? '<span class="arac-secenek-isaret" aria-hidden="true"></span>' : "") +
      (this.ozellestirKipi ? '<span class="arac-cikar" aria-hidden="true" title="Kutudan çıkar">×</span>' : "") + "</button>";
  };
  Y._kutulariCiz = function () {
    const self = this;
    this.y.kutular.forEach(function (kt) {
      if (kt.gizli) return;
      const d = el("div", "arac-kutu arac-" + kt.yon + (kt.kucuk ? " arac-kucuk" : " arac-genis") + (kt.kilitli ? " arac-kilitli" : "") + (kt.katli ? " arac-katli" : ""), {
        role: "toolbar", "aria-label": kt.ad + " araçları", "aria-orientation": kt.yon === "dikey" ? "vertical" : "horizontal", "data-kutu": kt.id,
      });
      d.style.setProperty("--arac-saydam", String(kt.saydamlik));
      const ks = kt.komutlar.map(komut).filter(Boolean);
      d.innerHTML = '<div class="arac-tutamak" title="' + kacis(kt.ad) + (kt.kilitli ? " (kilitli)" : " — sürükleyerek taşıyın") + '">' +
        '<span class="arac-tutamak-izi" aria-hidden="true"></span><span class="arac-kutu-ad">' + kacis(kt.ad) + "</span>" +
        (kt.kilitli ? '<span class="arac-kilit" aria-hidden="true" title="Kilitli">' + KILIT_SVG + "</span>" : "") +
        '<button type="button" class="arac-kutu-katla" tabindex="-1" aria-expanded="' + !kt.katli + '" aria-label="' + kacis(kt.ad) + (kt.katli ? " kutusunu aç" : " kutusunu katla") + '" title="' + (kt.katli ? "Aç" : "Katla (yalnız başlık)") + '">' +
          (kt.katli ? "▸" : "▾") + "</button>" +
        '<button type="button" class="arac-kutu-menu-ac" tabindex="-1" aria-haspopup="menu" aria-label="' + kacis(kt.ad) + ' kutusu seçenekleri">' + ikonSvg("menu") + "</button></div>" +
        '<div class="arac-dugmeler">' + ks.map(function (k) { return self._dugmeHtml(k); }).join("") +
        (ks.length ? "" : '<span class="arac-bos">Düğmeleri buraya sürükleyin</span>') + "</div>";
      self.kok.appendChild(d);
      self._gezintiHazirla(d);
    });
  };
  const KILIT_SVG = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>';
  /** Roving tabindex: kutudaki ilk etkin düğme (ya da son odaklanan) sekme durağıdır. */
  Y._gezintiHazirla = function (kapsam) {
    const ogeler = Array.from(kapsam.querySelectorAll(kapsam.classList.contains("arac-katli") ? ".arac-kutu-katla, .arac-kutu-menu-ac" : ".arac-dugme, .arac-kutu-katla, .arac-kutu-menu-ac"));
    if (!ogeler.length) return;
    const onceki = kapsam._son && ogeler.indexOf(kapsam._son) >= 0 ? kapsam._son : (ogeler.find(function (b) { return b.classList.contains("arac-dugme"); }) || ogeler[0]);
    ogeler.forEach(function (b) { b.tabIndex = b === onceki ? 0 : -1; });
  };
  Y._seritCiz = function () {
    const self = this;
    const s = el("div", "arac-serit" + (this.seritKatli ? " katli" : ""), { role: "region", "aria-label": "Araç kutuları" });
    const gorunur = this.y.kutular.filter(function (k) { return !k.gizli && k.komutlar.some(function (c) { return kayit.has(c); }); });
    let ust = '<div class="arac-serit-ust"><div class="arac-serit-cipler" role="tablist" aria-label="Kutular">';
    gorunur.forEach(function (k, i) { ust += '<button type="button" class="arac-serit-cip' + (i === 0 ? " aktif" : "") + '" role="tab" data-git="' + kacis(k.id) + '">' + kacis(k.ad) + "</button>"; });
    ust += '</div><button type="button" class="arac-serit-yonetici" aria-label="Araç kutuları menüsü" aria-haspopup="menu">' + ikonSvg("yonetici") + "</button>" +
      '<button type="button" class="arac-serit-katla" aria-expanded="' + (!this.seritKatli) + '" aria-label="' + (this.seritKatli ? "Araçları aç" : "Araçları kapat") + '">' +
      (this.seritKatli ? "▴" : "▾") + "</button></div>";
    let govde = '<div class="arac-serit-govde">';
    gorunur.forEach(function (kt) {
      const ks = kt.komutlar.map(komut).filter(Boolean);
      govde += '<div class="arac-serit-grup" role="toolbar" aria-label="' + kacis(kt.ad) + ' araçları" data-kutu="' + kacis(kt.id) + '">' +
        '<span class="arac-serit-ad" aria-hidden="true">' + kacis(kt.ad) + "</span>" + ks.map(function (k) { return self._dugmeHtml(k); }).join("") + "</div>";
    });
    govde += "</div>";
    s.innerHTML = ust + govde;
    this.kok.appendChild(s);
    s.querySelectorAll(".arac-serit-grup").forEach(function (g) { self._gezintiHazirla(g); });
  };
  Y._ozellestirCiz = function () {
    const self = this;
    const p_ = el("div", "arac-ozellestir", { role: "dialog", "aria-label": "Araç kutularını özelleştir" });
    const kutuSecenek = this.y.kutular.map(function (k) {
      return '<option value="' + kacis(k.id) + '"' + (k.id === self.secilenKutu ? " selected" : "") + ">" + kacis(k.ad) + (k.gizli ? " (gizli)" : "") + "</option>";
    }).join("");
    p_.innerHTML = '<div class="arac-oz-ust"><b>Özelleştir</b><button type="button" class="arac-oz-bitti">Bitti</button></div>' +
      '<p class="arac-oz-yardim">Düğmeleri kutular arasında sürükleyin; boş alana bırakınca yeni kutu oluşur. Ctrl ya da Alt ile bırakmak kopyalar. Düğmedeki × kutudan çıkarır.</p>' +
      '<input type="search" class="arac-oz-ara" placeholder="Komut ara…" aria-label="Komut ara" autocomplete="off">' +
      '<label class="arac-oz-hedef"><span>Eklenecek kutu</span><select class="arac-oz-kutu">' + kutuSecenek + '<option value="__yeni">+ Yeni kutu</option></select></label>' +
      '<div class="arac-oz-liste" role="list"></div>' +
      '<div class="arac-oz-alt"><button type="button" class="arac-oz-yeni">Yeni kutu</button><button type="button" class="arac-oz-varsayilan">Varsayılana dön</button></div>';
    this.kok.appendChild(p_);
    if (!this.secilenKutu || !kutuBul(this.y, this.secilenKutu)) {
      const ilk = this.y.kutular.find(function (k) { return !k.gizli && !k.kilitli; });
      this.secilenKutu = ilk ? ilk.id : null;
      const s_ = p_.querySelector(".arac-oz-kutu"); if (s_ && this.secilenKutu) s_.value = this.secilenKutu;
    }
    this._ozListe(p_, this._ozSorgu || "");
    const a_ = p_.querySelector(".arac-oz-ara");
    a_.value = this._ozSorgu || "";
  };
  Y._ozListe = function (p_, sorgu) {
    const self = this;
    const liste = ara(komutlar(), sorgu);
    const gruplar = new Map();
    liste.forEach(function (k) { if (!gruplar.has(k.grup)) gruplar.set(k.grup, []); gruplar.get(k.grup).push(k); });
    let h = "";
    const sira = GRUPLAR.map(function (g) { return g.id; }).concat(Array.from(gruplar.keys()).filter(function (g) { return !GRUPLAR.some(function (x) { return x.id === g; }); }));
    sira.forEach(function (g) {
      const l = gruplar.get(g);
      if (!l) return;
      h += '<div class="arac-oz-grup" role="presentation">' + kacis(grupAdi(g)) + "</div>";
      l.forEach(function (k) {
        const kutular = komutKutulari(self.y, k.id).map(function (id) { const b = kutuBul(self.y, id); return b ? b.ad : id; });
        h += '<div class="arac-oz-oge' + (bagliMi(k) ? "" : " bagsiz") + '" role="listitem" data-komut="' + kacis(k.id) + '">' + ikonSvg(k.ikon) +
          '<span class="arac-oz-ad">' + kacis(k.ad) + (k.kisayol ? ' <kbd class="arac-kbd">' + kacis(kisayolMetni(k.kisayol)) + "</kbd>" : "") +
          '<small>' + (kutular.length ? kacis(kutular.join(", ")) : "hiçbir kutuda değil") + (bagliMi(k) ? "" : " · bu sayfada bağlı değil") + "</small></span>" +
          '<button type="button" class="arac-oz-ekle" aria-label="' + kacis(k.ad) + ' komutunu seçili kutuya ekle" title="Seçili kutuya ekle">+</button></div>';
      });
    });
    p_.querySelector(".arac-oz-liste").innerHTML = h || '<p class="arac-oz-yardim">Eşleşen komut yok.</p>';
  };
  // ---- rıhtım yerleşimi (DOM): biçim sınıfları, ölçüm önbelleği, kenar şeritleri, yüzen kutular, taşma çekmecesi
  // yt: yatay başlıklı, yb: yatay başlıksız, yk: yatay katlı başlık, d1: tek düğme sütunu, d2: iki düğme sütunu, dk1/dk2: sütunda katlı
  // çip (sütun genişliğinde), dk: yüzen dikey katlı kutu
  const BICIM_SINIF = { yt: "arac-yatay", yb: "arac-yatay arac-basliksiz", yk: "arac-yatay arac-katli", d1: "arac-dikey", d2: "arac-dikey arac-sutun2",
    dk1: "arac-dikey arac-katli arac-sutun-cip", dk2: "arac-dikey arac-katli arac-sutun-cip", dk: "arac-dikey arac-katli" };
  const BICIM_TUM = ["arac-yatay", "arac-dikey", "arac-basliksiz", "arac-katli", "arac-sutun2", "arac-sutun-cip"];
  const YER_SINIF = ["arac-rihtimda", "arac-serbest", "arac-tasmada", "arac-tasma-kutu"];
  function bicimUygula(d, b, sutunW) {
    BICIM_TUM.forEach(function (c) { d.classList.remove(c); });
    BICIM_SINIF[b].split(" ").forEach(function (c) { d.classList.add(c); });
    d.style.width = (b === "dk1" || b === "dk2") && sutunW ? sutunW + "px" : "";
    d.setAttribute("aria-orientation", b.charAt(0) === "d" ? "vertical" : "horizontal");
    d._bicim = b;
  }
  // yer sınıfı (kenarda / yüzen / çekmecede gizli / çekmece içinde); kenardaki kutu data-rihtim="<kenar>" taşır
  function yerSinifi(d, s, kenar) {
    YER_SINIF.forEach(function (c) { d.classList.toggle(c, c === s); });
    if (kenar) d.setAttribute("data-rihtim", kenar); else d.removeAttribute("data-rihtim");
  }
  // öğenin kenar uzunluğu (px, yukarı yuvarlanmış: yan yana dizilen kutular kesirli genişlikte bile örtüşmez)
  function boyu(d) { const r_ = d.getBoundingClientRect(); return [Math.ceil(r_.width - 0.02), Math.ceil(r_.height - 0.02)]; }
  /** Kutunun bütün biçimlerdeki boyu (ölçü sınıfı en büyük boy ve kaydırma sınırlarını kaldırır): {yt, yb, yk, d1, d2, dk1, dk2: [w, h]}. */
  Y._olcBicim = function (d) {
    const ust = d.parentNode, sonraki = d.nextSibling, disarida = ust !== this.kok;
    if (disarida) this.kok.appendChild(d);
    const sinif = d.className, st = d.getAttribute("style"), b0 = d._bicim, o = {};
    d.style.left = "0px"; d.style.top = "0px";
    ["yt", "yb", "yk", "d1", "d2"].forEach(function (b) {
      bicimUygula(d, b);
      YER_SINIF.forEach(function (c) { d.classList.remove(c); });
      d.classList.add("arac-olcum");
      o[b] = boyu(d);
    });
    // sütunda katlı çip: sütun genişliğinde (d1 / d2 genişliği), yüksekliği ölçülür (yatay katlı başlıkla aynı olacak biçimde CSS)
    ["dk1", "dk2"].forEach(function (b) {
      const w = o[b === "dk1" ? "d1" : "d2"][0];
      bicimUygula(d, b, w);
      o[b] = [w, boyu(d)[1]];
    });
    d.className = sinif;
    if (st == null) d.removeAttribute("style"); else d.setAttribute("style", st);
    d._bicim = b0;
    if (disarida && ust) ust.insertBefore(d, sonraki);
    return o;
  };
  Y._olcu = function (d) { return d._olcu || (d._olcu = this._olcBicim(d)); };
  Y._olcuSil = function () { this.kok.querySelectorAll(".arac-kutu").forEach(function (d) { d._olcu = null; }); };
  // çekmecedeki kutuyu katmana geri al (DOM sırası: kutular dizi sırasıyla; sekme sırası korunur)
  Y._kokeAl = function (d) {
    if (!d || d.parentNode === this.kok) return;
    const id = d.getAttribute("data-kutu"), i = this.y.kutular.findIndex(function (k) { return k.id === id; });
    let once = null;
    for (let j = i + 1; j < this.y.kutular.length && !once; j++) {
      const x = this.kok.querySelector(':scope > .arac-kutu[data-kutu="' + this.y.kutular[j].id + '"]');
      if (x) once = x;
    }
    if (!once) once = this.kok.querySelector(":scope > .arac-ozellestir") || (this.ipucuEl.parentNode === this.kok ? this.ipucuEl : null);
    this.kok.insertBefore(d, once);
  };
  /**
   * Yerleşim (geçmişsiz): kenardaki kutular rıhtım yerleşimiyle (Duzen.rihtim) şeritlere, yüzen kutular çapalarından (bir kutuya
   * biniyorsa en yakın boş yere; çapa değişmez), sığmayanlar taşma çekmecesine. Tam ekran yalnız başka bir W × H'dir. Kalıcı alan
   * yazılmaz (yalnız kullanıcı eylemleri kaydeder); her yerleşimde "boyut" olayı (sayfa sahneyi yeniden sığdırır).
   */
  Y._konumla = function () {
    const W = this.kap.clientWidth, H = this.kap.clientHeight;
    if (!W || !H || this.mobil) return;
    const self = this, yb = this.kok.querySelector(":scope > .arac-yonetici-ac");
    const els = new Map();
    this.kok.querySelectorAll(".arac-kutu").forEach(function (d) { els.set(d.getAttribute("data-kutu"), d); });
    const liste = [], serbest = [];
    this.y.kutular.forEach(function (kt, i) {
      const d = els.get(kt.id);
      if (!d) return;
      if (kt.yer === "serbest" && kt.konum) { serbest.push(kt); return; }
      liste.push({ id: kt.id, kenar: kt.kenar || "ust", sira: kt.sira != null && isFinite(kt.sira) ? +kt.sira : 1e6 + i, oncelik: i, katli: !!kt.katli, olcu: self._olcu(d) });
    });
    const tsec = { kose: yb ? [[KOSE_DUGME, KOSE_DUGME]] : [], tasma: [KOSE_DUGME, KOSE_DUGME] };
    let r = rihtim(liste, W, H, tsec);
    let yuzen = this._serbestYerlestir(serbest, els, r, W, H);
    if (yuzen.tasan.length && !r.tasmaDugme) {      // yüzen kutu sahnede yer bulamadı: çekmece düğmesi için köşeye yer aç
      r = rihtim(liste, W, H, Object.assign({ tasmaZorla: true }, tsec));
      yuzen = this._serbestYerlestir(serbest, els, r, W, H);
    }
    r.kutular.forEach(function (q, id) {
      const d = els.get(id);
      self._kokeAl(d);
      bicimUygula(d, q.bicim, q.sutunW);
      yerSinifi(d, "arac-rihtimda", q.kenar);
      d._gosterimKatli = false;
      d.style.left = q.x + "px"; d.style.top = q.y + "px";
    });
    if (yb && r.kose[0]) { yb.style.left = r.kose[0].x + "px"; yb.style.top = r.kose[0].y + "px"; yb.style.bottom = "auto"; }
    const sira = new Map(this.y.kutular.map(function (k, i) { return [k.id, i]; }));
    const tasan = r.tasma.concat(yuzen.tasan).sort(function (a, b) { return sira.get(a) - sira.get(b); });
    this._rihtim = r;
    this._tasan = tasan;
    this._tasmaGuncelle(els, W, H);
    this._olay("boyut", {});
  };
  // yüzen kutular (öncelik sırasıyla): çapadan mutlak konum; kenar şeridindeki bir kutuya, köşe düğmelerine ya da önceki yüzen kutuya
  // biniyorsa en yakın boş yer, o da yoksa katlı başlığıyla boş yer, o da yoksa çekmece (yalnız gösterim; çapa ve katli değişmez)
  Y._serbestYerlestir = function (serbest, els, r, W, H) {
    const self = this, dolu = [], yer = [], tasan = [];
    r.kutular.forEach(function (q) { dolu.push(q); });
    r.kose.forEach(function (q) { dolu.push(q); });
    if (r.tasmaDugme) dolu.push(r.tasmaDugme);
    const binerMi = function (q) { return dolu.some(function (o) { return cakisir(q, o, 0); }); };
    serbest.forEach(function (kt) {
      const d = els.get(kt.id);
      self._kokeAl(d);
      yerSinifi(d, "arac-serbest");
      const dikey = kt.yon === "dikey";
      bicimUygula(d, dikey ? (kt.katli ? "dk" : "d1") : (kt.katli ? "yk" : "yt"));
      d._gosterimKatli = false;
      // boy sol üst köşede ölçülür (eski konumdaki dar kalan alanda satır kırılmasın); mutlak() kutuyu katmana sığdırır
      d.style.left = "0px"; d.style.top = "0px";
      let s = boyu(d), m = mutlak(kt.konum, s[0], s[1], W, H), q = { x: m.x, y: m.y, w: s[0], h: s[1] };
      if (binerMi(q)) {
        const p_ = yakinBos(q, W, H, dolu);
        if (p_) q = { x: p_.x, y: p_.y, w: s[0], h: s[1] };
        else if (!kt.katli) {
          bicimUygula(d, dikey ? "dk" : "yk");
          d.style.left = "0px"; d.style.top = "0px";
          s = boyu(d); m = mutlak(kt.konum, s[0], s[1], W, H);
          const q2 = { x: m.x, y: m.y, w: s[0], h: s[1] }, p2 = binerMi(q2) ? yakinBos(q2, W, H, dolu) : q2;
          q = p2 ? { x: p2.x, y: p2.y, w: s[0], h: s[1] } : null;
          if (q) d._gosterimKatli = true;
        } else q = null;
      }
      katlaDugmesi(d, { katli: kt.katli || !!d._gosterimKatli, ad: kt.ad });
      self._gezintiHazirla(d);
      if (!q) { tasan.push(kt.id); return; }
      d.style.left = q.x + "px"; d.style.top = q.y + "px";
      dolu.push(q); yer.push(kt.id);
    });
    return { yer: yer, tasan: tasan };
  };
  // ---- taşma çekmecesi: köşede "⋯ n" düğmesi; açılınca sığmayan kutular öncelik sırasıyla yatay araç çubukları olarak listelenir
  Y._tasmaGuncelle = function (els, W, H) {
    const self = this, tasan = this._tasan, r = this._rihtim;
    let td = this.kok.querySelector(":scope > .arac-tasma-ac"), pn = this.kok.querySelector(":scope > .arac-tasma");
    if (!els) { els = new Map(); this.kok.querySelectorAll(".arac-kutu").forEach(function (d) { els.set(d.getAttribute("data-kutu"), d); }); }
    if (!tasan.length || !r || !r.tasmaDugme) {
      const odakta = !!(td && (document.activeElement === td || (pn && pn.contains(document.activeElement))));
      if (pn) { pn.querySelectorAll(".arac-kutu").forEach(function (d) { self._kokeAl(d); }); pn.parentNode.removeChild(pn); }
      if (td) {
        td.parentNode.removeChild(td);
        const yb = this.kok.querySelector(":scope > .arac-yonetici-ac");
        if (odakta && yb) { try { yb.focus({ preventScroll: true }); } catch (e) { /* yoksay */ } }
      }
      this._tasmaAcik = false;
      this._tasmaBelgeBirak();
      return;
    }
    if (!td) {
      td = el("button", "arac-tasma-ac", { type: "button", "aria-haspopup": "dialog" });
      const yb = this.kok.querySelector(":scope > .arac-yonetici-ac");
      this.kok.insertBefore(td, yb ? yb.nextSibling : this.kok.firstChild);
    }
    const b = r.tasmaDugme, adlar = tasan.map(function (id) { const k = kutuBul(self.y, id); return k ? k.ad : id; });
    td.style.left = b.x + "px"; td.style.top = b.y + "px";
    td.setAttribute("aria-label", "Sığmayan araç kutuları (" + tasan.length + ")");
    td.title = "Sığmayan araç kutuları: " + adlar.join(", ");
    td.setAttribute("aria-expanded", String(!!this._tasmaAcik));
    if (this._tasmaAcik) {
      if (!pn) {
        pn = el("div", "arac-tasma", { role: "dialog", "aria-label": "Sığmayan araç kutuları" });
        this.kok.insertBefore(pn, td.nextSibling);
      }
      pn.style.left = b.x + "px"; pn.style.bottom = (H - b.y + ARALIK) + "px";
      pn.style.maxWidth = Math.max(120, W - b.x - BOSLUK) + "px"; pn.style.maxHeight = Math.max(60, b.y - ARALIK - BOSLUK) + "px";
      let onceki = null;
      tasan.forEach(function (id) {
        const d = els.get(id), kt = kutuBul(self.y, id);
        if (!d || !kt) return;
        bicimUygula(d, kt.katli ? "yk" : "yt");
        yerSinifi(d, "arac-tasma-kutu");
        d._gosterimKatli = false;
        katlaDugmesi(d, kt);
        d.style.left = ""; d.style.top = "";
        const yeri = onceki ? onceki.nextSibling : pn.firstChild;
        if (d !== yeri) pn.insertBefore(d, yeri);
        onceki = d;
      });
      this._tasmaBelgeDinle();
    } else {
      // gizli taşan kutu çekmecedeki biçiminde (yatay; katlıysa katlı başlık) bekler: biçimi yerleşim geçmişine bağlı kalmaz
      tasan.forEach(function (id) {
        const d = els.get(id), kt = kutuBul(self.y, id);
        if (!d || !kt) return;
        self._kokeAl(d);
        yerSinifi(d, "arac-tasmada");
        bicimUygula(d, kt.katli ? "yk" : "yt");
        d._gosterimKatli = false;
        katlaDugmesi(d, kt);
        d.style.left = ""; d.style.top = "";
      });
      if (pn) { pn.querySelectorAll(".arac-kutu").forEach(function (d) { self._kokeAl(d); }); pn.parentNode.removeChild(pn); }
      this._tasmaBelgeBirak();
    }
    this._tasmaDugmeIcerik(td);
  };
  // taşan kutudaki bir komut basılıysa (etkin kip) düğme onun ikonunu gösterir: etkin araç görünür kalır
  Y._tasmaDugmeIcerik = function (td) {
    const self = this;
    let secili = null;
    (this._tasan || []).forEach(function (id) {
      if (secili) return;
      const d = self.kok.querySelector('.arac-kutu[data-kutu="' + id + '"]'), b = d && d.querySelector('.arac-dugme[aria-pressed="true"]');
      if (b) secili = b;
    });
    const ik = secili && secili.querySelector(".arac-ikon");
    const html = (ik ? ik.outerHTML : '<span class="arac-tasma-nokta" aria-hidden="true">⋯</span>') + '<span class="arac-tasma-sayi" aria-hidden="true">' + (this._tasan || []).length + "</span>";
    if (td._html !== html) { td.innerHTML = html; td._html = html; }
    td.classList.toggle("secili", !!secili);
  };
  /** Çekmeceyi aç / kapat (odak: açılınca ilk düğmeye, kapanınca isteğe bağlı taşma düğmesine). */
  Y._tasmaAc = function (acik, odakGeri) {
    if (this.mobil) return;
    this._tasmaAcik = !!acik && this._tasan.length > 0;
    this._tasmaGuncelle(null, this.kap.clientWidth, this.kap.clientHeight);
    const td = this.kok.querySelector(":scope > .arac-tasma-ac"), pn = this.kok.querySelector(":scope > .arac-tasma");
    try {
      if (this._tasmaAcik && pn) {
        const ilk = pn.querySelector('[tabindex="0"]') || pn.querySelector(".arac-dugme, .arac-kutu-katla");
        if (ilk) ilk.focus({ preventScroll: true });
      } else if (odakGeri && td) td.focus({ preventScroll: true });
    } catch (e) { /* yoksay */ }
  };
  // açık çekmecenin dışına basınca kapanır (olay engellenmez: sahne tıklaması geçer); menü ve iletişim kutusu dışarı sayılmaz
  Y._tasmaBelgeDinle = function () {
    if (this._tasmaDisari || typeof document === "undefined") return;
    const self = this;
    this._tasmaDisari = function (e) {
      const t = e.target;
      if (!t || !t.closest) return;
      if (t.closest(".arac-tasma, .arac-tasma-ac, .arac-menu, .arac-diyalog")) return;
      self._tasmaAc(false, false);
    };
    document.addEventListener("pointerdown", this._tasmaDisari, true);
  };
  Y._tasmaBelgeBirak = function () {
    if (!this._tasmaDisari) return;
    document.removeEventListener("pointerdown", this._tasmaDisari, true);
    this._tasmaDisari = null;
  };
  /** Sığmayan (çekmecedeki) kutuların kimlikleri, öncelik sırasıyla. */
  Y.tasanlar = function () { return (this._tasan || []).slice(); };
  /**
   * Kenar payları (px): {sol, ust, sag, alt} — rıhtım şeritlerinin kalınlıkları (köşe düğmeleri alt şerittedir); yüzen kutular sayılmaz.
   * Mobil şeritte alt.
   */
  Y.kenarPaylari = function () {
    const W = this.kap.clientWidth, H = this.kap.clientHeight, sifir = { sol: 0, ust: 0, sag: 0, alt: 0 };
    if (!W || !H || !this.kok.isConnected) return sifir;
    if (this.mobil) {
      const s_ = this.kok.querySelector(".arac-serit");
      if (!s_) return sifir;
      const kr = this.kap.getBoundingClientRect(), sr = s_.getBoundingClientRect();
      return { sol: 0, ust: 0, sag: 0, alt: Math.max(0, Math.round(kr.bottom - sr.top)) };
    }
    if (this._rihtim) return Object.assign({}, this._rihtim.pay);
    return sifir;
  };
  Y._boyutDegisti = function () {
    const W = this.kap.clientWidth;
    const mobil = W > 0 && W < (this.sec.mobilGenislik || MOBIL);
    if (mobil !== this.mobil) { this.ciz(); if (this.mobil) this._olay("boyut", {}); return; }
    if (!this.mobil) this._konumla();      // "boyut" olayını _konumla yayar
    else this._olay("boyut", {});
  };
  // kenar şeridi işlemi (kenara al, aç, göster): sonrasında başka bir kutu çekmeceye düştüyse söylenir
  Y._kenarIslem = function (f, id) {
    const once = new Set(this._tasan || []);
    if (!this._dene(f)) return false;
    const yeni = (this._tasan || []).filter(function (x) { return !once.has(x) && x !== id; });
    const self = this;
    if (yeni.length) this.bildir(yeni.map(function (x) { const k = kutuBul(self.y, x); return "“" + (k ? k.ad : x) + "”"; }).join(", ") + " sığmadı; ⋯ düğmesinden açılır.");
    return true;
  };
  /** Katlı kutuyu aç: kenardaysa şeridinin en öncelikli kutusu olur (yerinde açılır; başka kutu sığmazsa çekmeceye düşer). */
  Y._kutuAc = function (id) {
    const self = this, kt = kutuBul(this.y, id);
    if (!kt) return;
    this._kenarIslem(function () { const y = kutuGuncelle(self.y, id, { katli: false }); return kt.yer === "serbest" ? y : kenaraAl(y, id, kt.kenar); }, id);
  };
  /** Kenardaki (ya da çekmecedeki) kutuyu sahnede yüzdür: kenarından başlayarak boş yere yerleşir, çapası yazılır. */
  Y._yuzdur = function (id) {
    const self = this, kt = kutuBul(this.y, id), d = this.kok.querySelector('.arac-kutu[data-kutu="' + id + '"]');
    if (!kt || !d || this.mobil) return;
    const W = this.kap.clientWidth, H = this.kap.clientHeight, r = this._rihtim, q0 = r && r.kutular.get(id);
    const yon = q0 ? (q0.bicim.charAt(0) === "d" ? "dikey" : "yatay") : (BANTLAR.indexOf(kt.kenar) >= 0 ? "yatay" : "dikey");
    const o = this._olcu(d), b = yon === "dikey" ? (kt.katli ? "dk1" : "d1") : (kt.katli ? "yk" : "yt");
    const dolu = [];
    if (r) { r.kutular.forEach(function (q, k) { if (k !== id) dolu.push(q); }); r.kose.forEach(function (q) { dolu.push(q); }); if (r.tasmaDugme) dolu.push(r.tasmaDugme); }
    this.kok.querySelectorAll(":scope > .arac-kutu.arac-serbest").forEach(function (x) { if (x !== d) dolu.push({ x: x.offsetLeft, y: x.offsetTop, w: x.offsetWidth, h: x.offsetHeight }); });
    const p_ = otomatikYerlestir([{ id: id, w: o[b][0], h: o[b][1], kenar: kt.kenar }], W, H, dolu).get(id);
    this._dene(function () { return serbestBirak(self.y, id, capa(p_.x, p_.y, o[b][0], o[b][1], W, H), yon); },
      "“" + kt.ad + "” sahnede yüzüyor; kenara geri almak için kutu menüsünden “Kenara yerleştir”.");
  };
  /** etkin/secili durumlarını tazeler (sayfa durum değiştirince çağırır). */
  Y.yenile = function () {
    this.kok.querySelectorAll(".arac-dugme").forEach(function (b) {
      const k = komut(b.getAttribute("data-komut"));
      if (!k) return;
      const bagli = bagliMi(k), etkin = etkinMi(k);
      b.classList.toggle("bagsiz", !bagli);
      if (etkin) b.removeAttribute("aria-disabled"); else b.setAttribute("aria-disabled", "true");
      if (b.hasAttribute("aria-pressed")) {
        const s = seciliMi(k);
        b.setAttribute("aria-pressed", s ? "true" : "false");
        b.classList.toggle("secili", s);
      }
      if (k.secenekler) {
        const v = secenekDegeri(k), sO = k.secenekler.find(function (s) { return s.id === v; });
        if (sO && b.getAttribute("data-secenek") !== v) {
          b.setAttribute("data-secenek", v);
          const eski = b.querySelector(".arac-ikon");
          if (eski) eski.outerHTML = ikonSvg(sO.ikon || k.ikon);
          b.setAttribute("aria-label", k.ad + ": " + sO.ad);
        }
      }
    });
    const td = this.kok.querySelector(":scope > .arac-tasma-ac");
    if (td) this._tasmaDugmeIcerik(td);
  };

  // ---- ipucu
  Y._ipucuGoster = function (b) {
    const k = komut(b.getAttribute("data-komut"));
    if (!k) return;
    const sec_ = k.secenekler ? k.secenekler.find(function (s) { return s.id === secenekDegeri(k); }) : null;
    const ks = kisayolMetni(k.kisayol);
    this.ipucuEl.innerHTML = "<b>" + kacis(k.ad) + "</b>" + (sec_ ? " · " + kacis(sec_.ad) : "") + (ks ? ' <kbd class="arac-kbd">' + kacis(ks) + "</kbd>" : "") +
      (k.ipucu ? "<span>" + kacis(k.ipucu) + "</span>" : "") + (bagliMi(k) ? (etkinMi(k) ? "" : '<span class="arac-ipucu-not arac-ipucu-neden">Şu an kullanılamıyor' + (nedenMetni(k) ? ": " + kacis(nedenMetni(k)) : ".") + "</span>")
        : '<span class="arac-ipucu-not">Bu sayfada henüz bağlı değil.</span>');
    this.ipucuEl.hidden = false;
    const kr = this.kok.getBoundingClientRect(), br = b.getBoundingClientRect(), ir = this.ipucuEl.getBoundingClientRect();
    const kutu = b.closest(".arac-kutu");
    let x, y;
    if (kutu && kutu.classList.contains("arac-dikey")) {
      x = br.right + 8 - kr.left; y = br.top - kr.top;
      if (br.right + 8 + ir.width > kr.right) x = br.left - 8 - ir.width - kr.left;
    } else {
      x = br.left - kr.left; y = br.bottom + 8 - kr.top;
      if (br.bottom + 8 + ir.height > kr.bottom) y = br.top - 8 - ir.height - kr.top;
    }
    x = Math.max(4, Math.min(x, kr.width - ir.width - 4)); y = Math.max(4, Math.min(y, kr.height - ir.height - 4));
    this.ipucuEl.style.left = Math.round(x) + "px"; this.ipucuEl.style.top = Math.round(y) + "px";
    b.setAttribute("aria-describedby", this.ipucuEl.id);
  };
  Y._ipucuGizle = function () {
    clearTimeout(this._ipucuZ);
    this.ipucuEl.hidden = true;
    const b = this.kok.querySelector("[aria-describedby='" + this.ipucuEl.id + "']");
    if (b) b.removeAttribute("aria-describedby");
  };

  // ---- olaylar
  Y._olaylar = function () {
    const self = this, kok_ = this.kok;
    kok_.addEventListener("click", function (e) { self._tik(e); });
    kok_.addEventListener("contextmenu", function (e) {
      const b = e.target.closest(".arac-dugme");
      const t = e.target.closest(".arac-tutamak");
      if (b) { e.preventDefault(); self._dugmeMenusu(b, { x: e.clientX, y: e.clientY }); }
      else if (t) { e.preventDefault(); self._kutuMenusu(t.closest(".arac-kutu").getAttribute("data-kutu"), { x: e.clientX, y: e.clientY }); }
    });
    kok_.addEventListener("pointerdown", function (e) { self._asagi(e); });
    kok_.addEventListener("keydown", function (e) { self._tus(e); });
    kok_.addEventListener("focusin", function (e) {
      const b = e.target.closest && e.target.closest(".arac-dugme");
      const t = e.target.closest && e.target.closest("[role=toolbar]");
      if (t && b) t._son = b;
      if (b && b.matches(":focus-visible")) self._ipucuGoster(b);
    });
    kok_.addEventListener("focusout", function () { self._ipucuGizle(); });
    kok_.addEventListener("pointerover", function (e) {
      if (e.pointerType !== "mouse") return;
      const b = e.target.closest(".arac-dugme");
      if (!b || self._surukle) return;
      clearTimeout(self._ipucuZ);
      self._ipucuZ = setTimeout(function () { self._ipucuGoster(b); }, 380);
    });
    kok_.addEventListener("pointerout", function (e) {
      const b = e.target.closest(".arac-dugme");
      if (b && !b.contains(e.relatedTarget)) self._ipucuGizle();
    });
    kok_.addEventListener("input", function (e) {
      if (e.target.classList.contains("arac-oz-ara")) {
        self._ozSorgu = e.target.value;
        self._ozListe(self.kok.querySelector(".arac-ozellestir"), e.target.value);
      }
    });
    kok_.addEventListener("change", function (e) {
      if (e.target.classList.contains("arac-oz-kutu")) {
        if (e.target.value === "__yeni") { self._yeniKutu([]); }
        else self.secilenKutu = e.target.value;
      }
    });
    if (this.sec.kisayollar !== false) {
      this._kisayolDinle = function (e) { self._kisayol(e); };
      document.addEventListener("keydown", this._kisayolDinle);
    }
  };
  Y._kisayol = function (e) {
    if (e.defaultPrevented || yazmaAlani(e.target) || acikMenu) return;
    if (e.target && e.target.closest && e.target.closest(".arac-diyalog, .bilgi-pencere, .bilgi-menu")) return;
    if (!this.kap.isConnected || (this.kap.offsetParent === null && getComputedStyle(this.kap).position !== "fixed")) return;   // gizli sayfa
    for (const k of kayit.values()) {
      if (k._kisayol && kisayolEslesir(k._kisayol, e)) {
        if (!etkinMi(k)) return;
        e.preventDefault();
        calistir(k.id, e);
        return;
      }
    }
  };
  Y._tik = function (e) {
    const self = this;
    if (this._tikYut) { this._tikYut = false; e.preventDefault(); e.stopPropagation(); return; }
    const t = e.target;
    if (t.closest(".arac-cikar")) {
      const b = t.closest(".arac-dugme"), kd = b.closest("[data-kutu]");
      if (kd) this._dene(function () { return dugmeCikar(self.y, kd.getAttribute("data-kutu"), b.getAttribute("data-komut")); }, "Düğme kutudan çıkarıldı.");
      return;
    }
    const b = t.closest(".arac-dugme");
    if (b) {
      this._ipucuGizle();
      if (this.ozellestirKipi) { this.bildir("Özelleştir kipinde düğmeler çalışmaz; sürükleyin ya da × ile çıkarın."); return; }
      const k = komut(b.getAttribute("data-komut"));
      if (!bagliMi(k)) { this.bildir("“" + (k ? k.ad : "") + "” bu sayfada henüz bağlı değil."); return; }
      if (!etkinMi(k)) {
        const n = nedenMetni(k);
        this.bildir("“" + k.ad + "” şu an kullanılamıyor" + (n ? ": " + n : "."));
        yay("reddedildi", { id: k.id, neden: n, ad: k.ad, kaynak: "dugme" });   // düğmede bildirim kutunun kendi balonunda
        return;
      }
      calistir(k.id, e);
      return;
    }
    const kt_ = t.closest(".arac-kutu-katla");
    if (kt_) {
      const kd = kt_.closest(".arac-kutu"), id = kd && kd.getAttribute("data-kutu"), kt = id && kutuBul(this.y, id);
      if (kt) {
        // yüzen kutu sahnede açık boyuyla yer bulamadığı için katlı gösteriliyor (kullanıcı katlamadı)
        if (kd._gosterimKatli) { this.bildir("“" + kt.ad + "” için sahnede yer yok; kutu menüsünden “Kenara yerleştir” ile kenara alın."); return; }
        // açılan kutu şeridinin en öncelikli kutusu olur: yerinde açılır (başka kutu sığmazsa çekmeceye düşer); katlamak yalnız katlar
        if (kt.katli) this._kutuAc(id);
        else this._dene(function () { return kutuGuncelle(self.y, id, { katli: true }); });
      }
      return;
    }
    if (t.closest(".arac-kutu-menu-ac")) { const kd = t.closest(".arac-kutu"); this._kutuMenusu(kd.getAttribute("data-kutu"), t.closest(".arac-kutu-menu-ac")); return; }
    if (t.closest(".arac-tasma-ac")) { this._tasmaAc(!this._tasmaAcik, true); return; }
    if (t.closest(".arac-yonetici-ac, .arac-serit-yonetici")) { this.yoneticiMenusu(t.closest("button")); return; }
    if (t.closest(".arac-serit-katla")) { this.seritKatli = !this.seritKatli; this.ciz(); return; }
    const cip = t.closest(".arac-serit-cip");
    if (cip) {
      const g = this.kok.querySelector('.arac-serit-grup[data-kutu="' + cip.getAttribute("data-git") + '"]');
      this.kok.querySelectorAll(".arac-serit-cip").forEach(function (c) { c.classList.toggle("aktif", c === cip); });
      const gv = g && g.parentNode;   // yalnız şeridi kaydır (sayfayı kaydırmadan)
      if (gv) { try { gv.scrollTo({ left: Math.max(0, g.offsetLeft - gv.offsetLeft - 6), behavior: hareketAz() ? "auto" : "smooth" }); } catch (x) { gv.scrollLeft = g.offsetLeft - gv.offsetLeft - 6; } }
      return;
    }
    if (t.closest(".arac-oz-bitti")) { this.ozellestir(false); return; }
    if (t.closest(".arac-oz-yeni")) { this._yeniKutu([]); return; }
    if (t.closest(".arac-oz-varsayilan")) { this.varsayilanaDon(); return; }
    const ek = t.closest(".arac-oz-ekle");
    if (ek) {
      const id = ek.closest(".arac-oz-oge").getAttribute("data-komut");
      if (!this.secilenKutu || !kutuBul(this.y, this.secilenKutu)) { this._yeniKutu([id]); return; }
      const kt = kutuBul(this.y, this.secilenKutu);
      this._dene(function () { return dugmeTasi(self.y, { komut: id, kaynak: null, hedef: kt.id }); }, "“" + komut(id).ad + "” → " + kt.ad);
    }
  };
  Y._yeniKutu = function (komutlar_, konum) {
    const r_ = kutuEkle(this.y, { komutlar: komutlar_, konum: konum || null, kenar: "ust" });
    this.secilenKutu = r_.id;
    this._uygula(r_.yerlesim, "Yeni kutu: " + kutuBul(r_.yerlesim, r_.id).ad);
    return r_.id;
  };
  Y._tus = function (e) {
    // açık çekmece: Esc kapatır, odak taşma düğmesine döner
    if (e.key === "Escape" && this._tasmaAcik && e.target.closest && e.target.closest(".arac-tasma, .arac-tasma-ac")) {
      this._tasmaAc(false, true); e.preventDefault(); e.stopPropagation(); return;
    }
    const b = e.target.closest && e.target.closest(".arac-dugme, .arac-kutu-katla, .arac-kutu-menu-ac");
    const tb = e.target.closest && e.target.closest("[role=toolbar]");
    if (!b || !tb) return;
    if ((e.key === "ArrowDown" && e.altKey) || e.key === "ContextMenu" || (e.key === "F10" && e.shiftKey)) {
      if (b.classList.contains("arac-dugme")) { this._dugmeMenusu(b, b); e.preventDefault(); }
      else {      // başlıkta (katlı sütun çipi dahil): kutu menüsü
        const kd = b.closest(".arac-kutu");
        if (kd) { this._kutuMenusu(kd.getAttribute("data-kutu"), b); e.preventDefault(); }
      }
      return;
    }
    const ogeler = Array.from(tb.querySelectorAll(tb.classList.contains("arac-katli") ? ".arac-kutu-katla, .arac-kutu-menu-ac" : ".arac-dugme, .arac-kutu-katla, .arac-kutu-menu-ac"));
    const i = ogeler.indexOf(b);
    let j = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") j = i + 1;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") j = i - 1;
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = ogeler.length - 1;
    if (j == null) return;
    j = (j + ogeler.length) % ogeler.length;
    ogeler.forEach(function (x, n) { x.tabIndex = n === j ? 0 : -1; });
    ogeler[j].focus();
    e.preventDefault();
  };

  // ---- sürükleme (kutu taşıma, düğme taşıma)
  Y._asagi = function (e) {
    this._tikYut = false;
    if (e.button !== 0 && e.pointerType === "mouse") return;
    const self = this;
    const tut = e.target.closest(".arac-tutamak");
    if (tut && !e.target.closest(".arac-kutu-menu-ac, .arac-kutu-katla")) { this._kutuSurukle(e, tut.closest(".arac-kutu")); return; }
    const b = e.target.closest(".arac-dugme, .arac-oz-oge");
    if (!b || e.target.closest(".arac-cikar, .arac-oz-ekle")) return;
    const serit = !!b.closest(".arac-serit");
    const dokunma = e.pointerType !== "mouse";
    const bas = { x: e.clientX, y: e.clientY, id: e.pointerId, el: b, t: performance.now() };
    let uzunZ = 0, uzunOldu = false;
    if (dokunma && b.classList.contains("arac-dugme")) {
      uzunZ = setTimeout(function () {
        uzunZ = 0; uzunOldu = true;
        if (!self._surukle) { self._tikYut = true; self._dugmeMenusu(b, { x: bas.x, y: bas.y }); }
      }, 550);
    }
    const esik = dokunma ? 10 : 6;
    const hareket = function (ev) {
      if (ev.pointerId !== bas.id) return;
      const d = Math.hypot(ev.clientX - bas.x, ev.clientY - bas.y);
      if (!self._surukle) {
        if (d < esik || uzunOldu) return;
        if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
        if (serit && !self.ozellestirKipi) { bitir(); return; }   // şeritte kaydırma
        const kd = b.closest("[data-kutu]");
        const kaynak = b.classList.contains("arac-oz-oge") ? null : (kd ? kd.getAttribute("data-kutu") : null);
        const kt = kaynak ? kutuBul(self.y, kaynak) : null;
        if (kt && kt.kilitli && !(ev.ctrlKey || ev.altKey)) { self.bildir("“" + kt.ad + "” kilitli: düğme çıkarılamaz (Ctrl ile kopyalayın)."); bitir(); return; }
        self._dugmeSurukleBasla(b, kaynak, ev);
      }
      if (self._surukle) { self._dugmeSurukleHareket(ev); ev.preventDefault(); }
    };
    const yukari = function (ev) {
      if (ev.pointerId !== bas.id) return;
      if (self._surukle) { self._dugmeBirak(ev); self._tikYut = true; }
      else if (uzunOldu) belgeTikYut();   // uzun basmayla açılan menünün öğesine sahte tıklama gitmesin
      bitir();
    };
    const iptal = function (ev) { if (ev.pointerId !== bas.id) return; if (self._surukle) self._dugmeSurukleBitir(); bitir(); };
    function bitir() {
      if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
      document.removeEventListener("pointermove", hareket, true);
      document.removeEventListener("pointerup", yukari, true);
      document.removeEventListener("pointercancel", iptal, true);
    }
    document.addEventListener("pointermove", hareket, true);
    document.addEventListener("pointerup", yukari, true);
    document.addEventListener("pointercancel", iptal, true);
  };
  /**
   * Kutuyu tutamağından sürükle. İşaretçi bir kenara YAPISMA + 50 px yaklaşınca o kenarın şeridine bırakma hedefi (yerleştirme işareti
   * şeritteki kutuların arasında); orada bırakılan kutu kenara (o yuvaya) yerleşir ve şeridin en öncelikli kutusu olur. Başka yerde
   * bırakılan kutu sahnede yüzer (çapa; yapışma). Çekmecedeki kutu da sürüklenebilir. Dokunmada uzun basma kutu menüsünü açar.
   */
  Y._kutuSurukle = function (e, d) {
    const self = this, id = d.getAttribute("data-kutu"), kt = kutuBul(this.y, id);
    if (!kt) return;
    const dokunma = !!e.pointerType && e.pointerType !== "mouse", pid = e.pointerId, bx = e.clientX, by = e.clientY;
    const W = this.kap.clientWidth, H = this.kap.clientHeight, cekmecede = !!d.closest(".arac-tasma");
    let basladi = false, son = null, hedef = null, x0 = 0, y0 = 0, w = 0, h = 0, digerleri = [], uzunZ = 0, kr = null;
    if (dokunma) {
      uzunZ = setTimeout(function () { uzunZ = 0; if (!basladi) { bitir(); belgeTikYut(); self._kutuMenusu(id, { x: bx, y: by }); } }, 550);
    }
    e.preventDefault();
    const basla = function () {
      basladi = true;
      if (kt.kilitli) { self.bildir("“" + kt.ad + "” kilitli; taşımak için kutu menüsünden kilidi açın."); return false; }
      kr = self.kok.getBoundingClientRect();
      const dr = d.getBoundingClientRect();
      x0 = Math.round(dr.left - kr.left); y0 = Math.round(dr.top - kr.top); w = Math.ceil(dr.width); h = Math.ceil(dr.height);
      if (cekmecede) { self.kok.appendChild(d); yerSinifi(d, "arac-serbest"); d.style.left = x0 + "px"; d.style.top = y0 + "px"; }
      digerleri = Array.from(self.kok.querySelectorAll(":scope > .arac-kutu")).filter(function (x) { return x !== d && x.offsetParent; })
        .map(function (x) { return { x: x.offsetLeft, y: x.offsetTop, w: x.offsetWidth, h: x.offsetHeight }; });
      d.classList.add("arac-tasiniyor");
      self._ipucuGizle();
      return true;
    };
    const hareket = function (ev) {
      if (ev.pointerId !== pid) return;
      if (!basladi) {
        if (Math.hypot(ev.clientX - bx, ev.clientY - by) < (dokunma ? 10 : 5)) return;
        if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
        if (!basla()) { bitir(); return; }
      }
      ev.preventDefault();
      son = yapistir({ x: x0 + ev.clientX - bx, y: y0 + ev.clientY - by, w: w, h: h }, W, H, ev.shiftKey ? [] : digerleri);
      d.style.left = son.x + "px"; d.style.top = son.y + "px";
      hedef = self._rihtimHedefi(ev.clientX - kr.left, ev.clientY - kr.top, id, W, H);
      self._rihtimIsareti(hedef);
      d.classList.toggle("arac-yapisti", !hedef && !!(son.kenarX || son.kenarY));
      d.classList.toggle("arac-rihtima", !!hedef);
    };
    const yukari = function (ev) {
      if (ev.pointerId !== pid) return;
      const tasindi = basladi && !kt.kilitli && !!son;
      bitir();
      if (!tasindi) { if (basladi && cekmecede) self._konumla(); return; }
      if (hedef) {
        const k = hedef.kenar, once = hedef.once;
        self._kenarIslem(function () { return kenaraAl(self.y, id, k, { once: once }); }, id);
      } else {
        const yon = d.classList.contains("arac-dikey") ? "dikey" : "yatay";
        self._dene(function () { return serbestBirak(self.y, id, capa(son.x, son.y, w, h, W, H), yon); });
      }
    };
    const iptal = function (ev) { if (ev.pointerId !== pid) return; bitir(); if (basladi) self._konumla(); };
    function bitir() {
      if (uzunZ) { clearTimeout(uzunZ); uzunZ = 0; }
      document.removeEventListener("pointermove", hareket, true);
      document.removeEventListener("pointerup", yukari, true);
      document.removeEventListener("pointercancel", iptal, true);
      d.classList.remove("arac-tasiniyor", "arac-yapisti", "arac-rihtima");
      self._rihtimIsareti(null);
    }
    document.addEventListener("pointermove", hareket, true);
    document.addEventListener("pointerup", yukari, true);
    document.addEventListener("pointercancel", iptal, true);
  };
  /**
   * Sürüklenen kutu için bırakma hedefi: işaretçi (katman px) bir kenara YAPISMA + 50 px'ten yakınsa en yakın kenarın şeridi ve o
   * şeritte işaretçiye en yakın yuva: {kenar, once (yuvadan sonraki kutunun kimliği | null: sona), isaret: {x, y, w, h}} | null.
   */
  Y._rihtimHedefi = function (px, py, id, W, H) {
    const E = YAPISMA + 50, uz = { sol: px, sag: W - px, ust: py, alt: H - py };
    let kn = null;
    KENARLAR.forEach(function (k) { if (uz[k] <= E && (!kn || uz[k] < uz[kn])) kn = k; });
    if (!kn) return null;
    const r = this._rihtim, bant = BANTLAR.indexOf(kn) >= 0, l = [];
    if (r) r.kutular.forEach(function (q, kid) { if (q.kenar === kn && kid !== id && !q.yedek) l.push({ id: kid, q: q }); });
    l.sort(function (a, b) { return bant ? a.q.x - b.q.x : a.q.y - b.q.y; });
    let i = l.findIndex(function (o_) { return bant ? px < o_.q.x + o_.q.w / 2 : py < o_.q.y + o_.q.h / 2; });
    if (i < 0) i = l.length;
    const sonu = function (q) { return bant ? q.x + q.w + ARALIK / 2 : q.y + q.h + ARALIK / 2; };
    const basi = function (q) { return bant ? q.x - ARALIK / 2 : q.y - ARALIK / 2; };
    let isaret;
    if (bant) {
      const t = r ? Math.max(30, (kn === "ust" ? r.pay.ust : r.pay.alt) - BOSLUK) : 42;
      const bas0 = kn === "alt" && r && r.kose.length ? r.kose.reduce(function (m, k) { return Math.max(m, k.x + k.w); }, 0) + (r.tasmaDugme ? r.tasmaDugme.w + ARALIK : 0) + ARALIK / 2 : BOSLUK;
      const x = i < l.length ? basi(l[i].q) : (l.length ? sonu(l[l.length - 1].q) : bas0);
      isaret = { x: Math.round(x - 1.5), y: kn === "ust" ? BOSLUK : H - BOSLUK - t, w: 3, h: Math.round(t) };
    } else {
      const sw = r ? Math.max(30, (kn === "sol" ? r.pay.sol : r.pay.sag) - BOSLUK) : 40;
      const y0 = r ? BOSLUK + (r.pay.ust ? r.pay.ust - BOSLUK + ARALIK : 0) : BOSLUK;
      const y = i < l.length ? basi(l[i].q) : (l.length ? sonu(l[l.length - 1].q) : y0);
      isaret = { x: kn === "sol" ? BOSLUK : W - BOSLUK - sw, y: Math.round(y - 1.5), w: Math.round(sw), h: 3 };
    }
    return { kenar: kn, once: i < l.length ? l[i].id : null, isaret: isaret };
  };
  Y._rihtimIsareti = function (hd) {
    let m = this.kok.querySelector(":scope > .arac-rihtim-isaret");
    if (!hd) { if (m) m.parentNode.removeChild(m); return; }
    if (!m) { m = el("div", "arac-rihtim-isaret", { "aria-hidden": "true" }); this.kok.appendChild(m); }
    m.className = "arac-rihtim-isaret " + (BANTLAR.indexOf(hd.kenar) >= 0 ? "dikey" : "yatay");
    m.style.left = hd.isaret.x + "px"; m.style.top = hd.isaret.y + "px"; m.style.width = hd.isaret.w + "px"; m.style.height = hd.isaret.h + "px";
  };
  Y._dugmeSurukleBasla = function (b, kaynak, ev) {
    this._ipucuGizle();
    menuKapat(false);
    const id = b.getAttribute("data-komut"), k = komut(id);
    const hayalet = el("div", "arac-hayalet");
    hayalet.innerHTML = ikonSvg(k ? k.ikon : "diger") + '<span>' + kacis(k ? k.ad : id) + "</span>";
    ustKatman().appendChild(hayalet);
    const imi = el("div", "arac-yer-imi");
    const yeni = el("div", "arac-yeni-kutu-onizleme");
    yeni.textContent = "Yeni kutu";
    this.kok.appendChild(yeni);
    yeni.hidden = true;
    b.classList.add("arac-suruklenen");
    this.kok.classList.add("arac-surukleniyor");
    this._surukle = { id: id, kaynak: kaynak, el: b, hayalet: hayalet, imi: imi, yeni: yeni, hedef: null, sira: null };
    this._dugmeSurukleHareket(ev);
  };
  Y._dugmeSurukleHareket = function (ev) {
    const s = this._surukle;
    s.hayalet.style.left = (ev.clientX + 12) + "px"; s.hayalet.style.top = (ev.clientY + 10) + "px";
    s.kopya = !!(ev.ctrlKey || ev.altKey);
    s.hayalet.classList.toggle("kopya", s.kopya);
    const alt = document.elementFromPoint(ev.clientX, ev.clientY);
    const kutu = alt && alt.closest ? alt.closest(".arac-kutu, .arac-serit-grup") : null;
    const ozp = alt && alt.closest ? alt.closest(".arac-ozellestir") : null;
    const kr = this.kap.getBoundingClientRect();
    const icinde = ev.clientX >= kr.left && ev.clientX <= kr.right && ev.clientY >= kr.top && ev.clientY <= kr.bottom;
    if (s.imi.parentNode) s.imi.parentNode.removeChild(s.imi);
    this.kok.querySelectorAll(".arac-hedef").forEach(function (x) { x.classList.remove("arac-hedef", "arac-red"); });
    s.yeni.hidden = true;
    s.hedef = null; s.sira = null; s.cikar = false; s.yeniKonum = null;
    if (kutu) {
      const kt = kutuBul(this.y, kutu.getAttribute("data-kutu"));
      kutu.classList.add("arac-hedef");
      if (kt && kt.kilitli) { kutu.classList.add("arac-red"); return; }
      const dikey = kutu.classList.contains("arac-dikey");
      const dugmeler = Array.from(kutu.querySelectorAll(".arac-dugme")).filter(function (x) { return x !== s.el || s.kopya; });
      let sira = dugmeler.length;
      for (let i = 0; i < dugmeler.length; i++) {
        const r_ = dugmeler[i].getBoundingClientRect();
        if (dikey ? ev.clientY < r_.top + r_.height / 2 : ev.clientX < r_.left + r_.width / 2) { sira = i; break; }
      }
      const kap_ = kutu.querySelector(".arac-dugmeler") || kutu;
      s.imi.className = "arac-yer-imi " + (dikey ? "dikey" : "yatay");
      if (sira < dugmeler.length) kap_.insertBefore(s.imi, dugmeler[sira]); else kap_.appendChild(s.imi);
      // sıra: hedef kutunun komut listesindeki indeks (kayıtsız komutlar da listede durur)
      const hedefKomut = sira < dugmeler.length ? dugmeler[sira].getAttribute("data-komut") : null;
      s.hedef = kt.id;
      s.sira = hedefKomut ? kt.komutlar.indexOf(hedefKomut) : kt.komutlar.length;
    } else if (ozp && s.kaynak) {
      s.cikar = true;
      ozp.classList.add("arac-hedef");
    } else if (icinde && !this.mobil) {
      s.yeni.hidden = false;
      const x = ev.clientX - kr.left - 20, y = ev.clientY - kr.top - 20;
      s.yeni.style.left = Math.round(x) + "px"; s.yeni.style.top = Math.round(y) + "px";
      s.yeniKonum = { x: Math.max(0, x), y: Math.max(0, y) };
    }
  };
  Y._dugmeSurukleBitir = function () {
    const s = this._surukle;
    if (!s) return;
    if (s.hayalet.parentNode) s.hayalet.parentNode.removeChild(s.hayalet);
    if (s.imi.parentNode) s.imi.parentNode.removeChild(s.imi);
    if (s.yeni.parentNode) s.yeni.parentNode.removeChild(s.yeni);
    s.el.classList.remove("arac-suruklenen");
    this.kok.classList.remove("arac-surukleniyor");
    this.kok.querySelectorAll(".arac-hedef").forEach(function (x) { x.classList.remove("arac-hedef", "arac-red"); });
    this._surukle = null;
  };
  Y._dugmeBirak = function (ev) {
    const self = this;
    this._dugmeSurukleHareket(ev);
    const s = this._surukle;
    this._dugmeSurukleBitir();
    const ad = (komut(s.id) || { ad: s.id }).ad;
    if (s.hedef) {
      if (s.hedef === s.kaynak && !s.kopya) {
        this._dene(function () { return dugmeTasi(self.y, { komut: s.id, kaynak: s.kaynak, hedef: s.hedef, sira: s.sira }); });
      } else {
        const h = kutuBul(this.y, s.hedef);
        this._dene(function () { return dugmeTasi(self.y, { komut: s.id, kaynak: s.kaynak, hedef: s.hedef, sira: s.sira, kopya: s.kopya }); },
          "“" + ad + "” " + (s.kopya ? "kopyalandı" : "taşındı") + " → " + (h ? h.ad : ""));
      }
    } else if (s.cikar) {
      this._dene(function () { return dugmeCikar(self.y, s.kaynak, s.id); }, "“" + ad + "” kutudan çıkarıldı.");
    } else if (s.yeniKonum) {
      const W = this.kap.clientWidth, H = this.kap.clientHeight;
      const k = capa(s.yeniKonum.x, s.yeniKonum.y, 48, 70, W, H);
      try {
        const r_ = kutuEkleTasi(this.y, { konum: k, yon: "dikey" }, s.id, s.kaynak, s.kopya);
        this.secilenKutu = r_.id;
        this._uygula(r_.yerlesim, "Yeni kutu oluşturuldu: " + kutuBul(r_.yerlesim, r_.id).ad + " (adını kutu menüsünden değiştirebilirsiniz)");
      } catch (e) { this.bildir(e.message); }
    }
  };

  // ---- menüler
  Y._dugmeMenusu = function (b, konum) {
    const self = this, id = b.getAttribute("data-komut"), k = komut(id);
    if (!k) return;
    const kd = b.closest("[data-kutu]"), kutuId = kd ? kd.getAttribute("data-kutu") : null, kt = kutuId ? kutuBul(this.y, kutuId) : null;
    const ogeler = [];
    if (k.secenekler) {
      const v = secenekDegeri(k);
      ogeler.push({ baslik: k.ad + " — tip" });
      k.secenekler.forEach(function (s) {
        ogeler.push({ ad: s.ad, ikon: s.ikon, radyo: true, isaret: s.id === v, calistir: function () {
          secenekAyarla(k, s.id);
          self.yenile();
          if (etkinMi(k)) calistir(k.id);
        } });
      });
      ogeler.push({ ayrac: true });
    }
    if (bagliMi(k)) ogeler.push({ ad: "Çalıştır", ikon: k.ikon, kisayol: kisayolMetni(k.kisayol), soluk: !etkinMi(k), calistir: function () { calistir(k.id); } });
    if (kt) {
      ogeler.push({ ad: "Kutudan çıkar", soluk: kt.kilitli, calistir: function () { self._dene(function () { return dugmeCikar(self.y, kt.id, id); }, "“" + k.ad + "” çıkarıldı."); } });
      ogeler.push({ ad: "Yeni kutuya al", soluk: kt.kilitli, calistir: function () {
        try {
          const r_ = kutuEkleTasi(self.y, { kenar: "ust" }, id, kt.id, false);
          self.secilenKutu = r_.id;
          self._uygula(r_.yerlesim, "Yeni kutu: " + kutuBul(r_.yerlesim, r_.id).ad);
        } catch (e) { self.bildir(e.message); }
      } });
      const digerleri = this.y.kutular.filter(function (x) { return x.id !== kt.id && !x.kilitli; });
      if (digerleri.length) {
        ogeler.push({ ad: "Başka kutuya taşı", alt: digerleri.map(function (x) {
          return { ad: x.ad + (x.gizli ? " (gizli)" : ""), calistir: function () { self._dene(function () { return dugmeTasi(self.y, { komut: id, kaynak: kt.id, hedef: x.id }); }, "“" + k.ad + "” → " + x.ad); } };
        }) });
      }
    }
    ogeler.push({ ad: "Özelleştir…", ikon: "ozellestir", calistir: function () { self.ozellestir(true); } });
    menuAc(ogeler, konum, { donus: b, etiket: k.ad + " seçenekleri", yan: !!(konum && konum.getBoundingClientRect && b.closest(".arac-dikey")) });
  };
  /**
   * Kutu menüsü. Kenardaki kutu: "Kenar" alt menüsü (Üst / Alt / Sol / Sağ: o şeridin en öncelikli kutusu) ve "Sahnede yüzdür";
   * çekmecedeki kutu ayrıca "Kenara sabitle" (şeridinin en öncelikli kutusu; başka bir kutu çekmeceye düşebilir). Yüzen kutu:
   * "Yatay yap / Dikey yap" ve "Kenara yerleştir" (çapasına en yakın kenarın şeridine, en öne).
   */
  Y._kutuMenusu = function (id, konum) {
    const self = this, kt = kutuBul(this.y, id);
    if (!kt) return;
    const d = this.kok.querySelector('.arac-kutu[data-kutu="' + id + '"]');
    const donus = d ? (d.classList.contains("arac-sutun-cip") ? d.querySelector(".arac-kutu-katla") : d.querySelector(".arac-kutu-menu-ac")) : null;
    const g = function (alan) {
      return function () { const a = {}; a[alan.ad] = alan.v; self._dene(function () { return kutuGuncelle(self.y, id, a); }); };
    };
    const kenarIslem = function (kn) { return function () { self._kenarIslem(function () { return kenaraAl(self.y, id, kn); }, id); }; };
    const serbest = kt.yer === "serbest", tasmada = (this._tasan || []).indexOf(id) >= 0;
    const digerleri = this.y.kutular.filter(function (x) { return x.id !== id; });
    const ogeler = [{ baslik: kt.ad }, { ad: "Yeniden adlandır…", calistir: function () { self.adlandir(id); } }];
    if (serbest) {
      const c = kt.konum || { x: 0, y: 0, yx: "sol", yy: "ust" };
      ogeler.push({ ad: kt.yon === "dikey" ? "Yatay yap" : "Dikey yap", calistir: g({ ad: "yon", v: kt.yon === "dikey" ? "yatay" : "dikey" }) });
      ogeler.push({ ad: "Kenara yerleştir", calistir: kenarIslem(c.x <= c.y ? c.yx : c.yy) });
    } else {
      if (tasmada) ogeler.push({ ad: "Kenara sabitle", calistir: kenarIslem(kt.kenar) });
      ogeler.push({ ad: "Kenar", alt: [["ust", "Üst"], ["alt", "Alt"], ["sol", "Sol"], ["sag", "Sağ"]].map(function (x) {
        return { ad: x[1], radyo: true, isaret: kt.kenar === x[0], calistir: kenarIslem(x[0]) };
      }) });
      if (!this.mobil) ogeler.push({ ad: "Sahnede yüzdür", calistir: function () { self._yuzdur(id); } });
    }
    ogeler.push(
      { ad: kt.kucuk ? "Genişlet (ikon + ad)" : "Küçült (yalnız ikon)", calistir: g({ ad: "kucuk", v: !kt.kucuk }) },
      { ad: kt.katli ? "Aç (düğmeleri göster)" : "Katla (yalnız başlık)", calistir: kt.katli ? function () { self._kutuAc(id); } : g({ ad: "katli", v: true }) },
      { ad: "Saydamlık…", calistir: function () { self.saydamlik(id); } },
      { ad: "Kilitli", isaret: kt.kilitli, calistir: g({ ad: "kilitli", v: !kt.kilitli }) },
      { ad: "Birleştir", soluk: !digerleri.length || kt.kilitli, alt: digerleri.map(function (x) {
        return { ad: x.ad + " kutusunu buraya al", soluk: x.kilitli, calistir: function () { self._dene(function () { return kutulariBirlestir(self.y, id, x.id); }, x.ad + " → " + kt.ad + " birleştirildi."); } };
      }) },
      { ad: "Gizle", calistir: g({ ad: "gizli", v: true }) },
      { ayrac: true },
      { ad: "Kutuyu sil", soluk: kt.kilitli, calistir: function () { self._dene(function () { return kutuSil(self.y, id); }, "“" + kt.ad + "” silindi (komutlar Özelleştir listesinde durur)."); } });
    menuAc(ogeler, konum, { donus: donus, etiket: kt.ad + " kutusu" });
  };
  /** Yönetici menüsü (köşedeki düğme ya da sayfanın kendi menüsünden çağrılır). */
  Y.yoneticiMenusu = function (konum) {
    const self = this;
    const gizli = this.y.kutular.filter(function (k) { return k.gizli; });
    const hepsiKucuk = this.y.kutular.every(function (k) { return k.kucuk; });
    menuAc([
      { baslik: "Araç kutuları" },
      { ad: "Yeni kutu", ikon: "yonetici", calistir: function () { self._yeniKutu([]); self.ozellestir(true); } },
      { ad: this.ozellestirKipi ? "Özelleştirmeyi bitir" : "Özelleştir…", ikon: "ozellestir", calistir: function () { self.ozellestir(!self.ozellestirKipi); } },
      { ad: "Hazır yerleşim", alt: HAZIR_ADLARI.map(function (h) { return { ad: h.id === "varsayilan" ? "Varsayılana dön" : h.ad, calistir: function () { self.hazirYerlesim(h.id); } }; }) },
      // gösterilen kutu şeridinin en öncelikli kutusu olur (yer yoksa başka bir kutu çekmeceye düşer ve söylenir)
      { ad: "Gizli kutular", soluk: !gizli.length, alt: gizli.map(function (k) { return { ad: k.ad + " kutusunu göster", calistir: function () {
        self._kenarIslem(function () { const y = kutuGuncelle(self.y, k.id, { gizli: false }); return k.yer === "serbest" ? y : kenaraAl(y, k.id, k.kenar); }, k.id);
      } }; }) },
      { ad: hepsiKucuk ? "Hepsini genişlet (ikon + ad)" : "Hepsini küçült (yalnız ikon)", calistir: function () {
        const y = kopya(self.y); y.kutular.forEach(function (k) { k.kucuk = !hepsiKucuk; }); self._uygula(y);
      } },
      { ayrac: true },
      { ad: "Yerleşimi dışa aktar (JSON)", calistir: function () { self.disaAktar(); } },
      { ad: "Yerleşimi içe aktar…", calistir: function () { self.iceAktar(); } },
    ], konum, { donus: konum && konum.focus ? konum : null, etiket: "Araç kutuları menüsü" });
  };
  Y.adlandir = function (id) {
    const self = this, kt = kutuBul(this.y, id);
    if (!kt) return;
    const d = this.kok.querySelector('.arac-kutu[data-kutu="' + id + '"]');
    const r_ = d ? d.getBoundingClientRect() : null;
    diyalogAc("Kutuyu yeniden adlandır", '<input type="text" class="arac-diyalog-girdi" maxlength="40" aria-label="Kutu adı" value="' + kacis(kt.ad) + '">', [
      { ad: "İptal" },
      { ad: "Tamam", ana: true, calistir: function (dl) {
        const v = dl.querySelector("input").value;
        return self._dene(function () { return kutuGuncelle(self.y, id, { ad: v }); }, "Kutu adı: " + v.trim());
      } },
    ], r_ ? { x: r_.left, y: r_.bottom + 6 } : null, d ? d.querySelector(".arac-kutu-menu-ac") : null);
  };
  Y.saydamlik = function (id) {
    const self = this, kt = kutuBul(this.y, id);
    if (!kt) return;
    const d = this.kok.querySelector('.arac-kutu[data-kutu="' + id + '"]');
    const r_ = d ? d.getBoundingClientRect() : null;
    const dl = diyalogAc("Saydamlık: " + kt.ad, '<input type="range" min="30" max="100" step="5" value="' + Math.round(kt.saydamlik * 100) + '" aria-label="Opaklık yüzdesi"><output>' + Math.round(kt.saydamlik * 100) + " %</output>", [
      { ad: "Tamam", ana: true },
    ], r_ ? { x: r_.left, y: r_.bottom + 6 } : null, d ? d.querySelector(".arac-kutu-menu-ac") : null);
    const inp = dl.el.querySelector("input"), out = dl.el.querySelector("output");
    inp.addEventListener("input", function () {
      out.textContent = inp.value + " %";
      self.y = kutuGuncelle(self.y, id, { saydamlik: +inp.value / 100 });
      if (d) d.style.setProperty("--arac-saydam", String(+inp.value / 100));
      self._kaydet();
    });
  };
  Y.disaAktar = function () {
    const metin = JSON.stringify(this.y, null, 2);
    try {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([metin], { type: "application/json" }));
      a.download = "arac-yerlesimi.json";
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
      this.bildir("Yerleşim dışa aktarıldı (arac-yerlesimi.json).");
    } catch (e) { this.bildir("Dışa aktarılamadı: " + e.message); }
    return metin;
  };
  Y.iceAktar = function () {
    const self = this;
    const g = document.createElement("input");
    g.type = "file"; g.accept = "application/json,.json";
    g.addEventListener("change", function () {
      const f = g.files && g.files[0];
      if (!f) return;
      f.text().then(function (m) {
        try { self.yerlesimYukle(m); self.bildir("Yerleşim içe aktarıldı."); }
        catch (e) { diyalogAc("Yerleşim içe aktarılamadı", '<p class="arac-diyalog-hata">' + kacis(e.message) + "</p>", [{ ad: "Tamam", ana: true }]); }
      });
    });
    g.click();
  };
  Y.ozellestir = function (acik) {
    this.ozellestirKipi = acik == null ? !this.ozellestirKipi : !!acik;
    menuKapat(false);
    this.ciz();
    this._olay("ozellestir", { acik: this.ozellestirKipi });
    if (this.ozellestirKipi) { const a_ = this.kok.querySelector(".arac-oz-ara"); if (a_) a_.focus(); }
  };
  Y.kaldir = function () {
    this._tasmaBelgeBirak();
    if (this._ro) this._ro.disconnect();
    if (this._pencereBoyut) window.removeEventListener("resize", this._pencereBoyut);
    if (this._kisayolDinle) document.removeEventListener("keydown", this._kisayolDinle);
    if (this.kok.parentNode) this.kok.parentNode.removeChild(this.kok);
    yoneticiler.delete(this);
    if (son === this) son = null;
  };

  // ================================================================= dışa açık yüz
  let son = null;
  function kur(kap, sec) {
    if (typeof document === "undefined") throw new Error("MatrisArac.kur yalnız tarayıcıda çalışır.");
    if (!kap) throw new Error("MatrisArac.kur: kapsayıcı öğe gerekli.");
    son = new Yonetici(kap, sec);
    return son;
  }
  function vekil(ad) {
    return function () {
      if (!son) throw new Error("Önce MatrisArac.kur(kapsayici) çağrılmalı.");
      return son[ad].apply(son, arguments);
    };
  }
  function yenile() { yoneticiler.forEach(function (y) { y.yenile(); }); }
  /** Son kurulan yöneticinin kenar payları (px); yönetici yoksa sıfır. */
  function kenarPaylari() { return son ? son.kenarPaylari() : { sol: 0, ust: 0, sag: 0, alt: 0 }; }
  function dinle(f) { dinleyiciler.add(f); return function () { dinleyiciler.delete(f); }; }

  return Object.freeze({
    SURUM: SURUM, GRUPLAR: GRUPLAR, KATALOG: KATALOG, CAPRAZ_SECENEKLERI: CAPRAZ_SECENEKLERI, DIYAGRAM_SECENEKLERI: DIYAGRAM_SECENEKLERI,
    SAYFA_TUSLARI: SAYFA_TUSLARI, grupAdi: grupAdi,
    IKON: IKON, ikonSvg: ikonSvg,
    komutKaydet: komutKaydet, baglar: baglar, katalogKaydet: katalogKaydet, komut: komut, komutlar: komutlar, calistir: calistir,
    etkinMi: etkinMi, seciliMi: seciliMi, bagliMi: bagliMi, secenekDegeri: secenekDegeri, kisayollar: kisayollar, nedenMetni: nedenMetni, kenarPaylari: kenarPaylari,
    kisayolCoz: kisayolCoz, kisayolEslesir: kisayolEslesir, kisayolMetni: kisayolMetni, ara: ara, normal: normal,
    Duzen: Duzen, YerlesimHatasi: YerlesimHatasi,
    kur: kur, yenile: yenile, dinle: dinle,
    yerlesim: vekil("yerlesim"), yerlesimYukle: vekil("yerlesimYukle"), hazirYerlesim: vekil("hazirYerlesim"), varsayilanaDon: vekil("varsayilanaDon"),
    ozellestir: vekil("ozellestir"), yoneticiMenusu: vekil("yoneticiMenusu"), disaAktar: vekil("disaAktar"), tasanlar: vekil("tasanlar"),
  });
});
