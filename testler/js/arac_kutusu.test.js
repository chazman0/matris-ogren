/* docs/arac_kutusu.js birim testleri (saf kısım: katalog, ikonlar, komut kaydı, yerleşim işlemleri, yapışma, kısayollar, arama).
   Çalıştırma: node --test testler/js/arac_kutusu.test.js */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const A = require(path.join(__dirname, "..", "..", "docs", "arac_kutusu.js"));
const M = require(path.join(__dirname, "..", "..", "docs", "model_ops.js"));
const D = A.Duzen;

const GEREKEN = {
  aks: ["aks-sihirbaz", "aks-duzenle", "aks-ekle", "aks-sil", "aks-tasi", "aks-sistemi", "aks-gorunurluk", "duzlem-yukari", "duzlem-asagi"],
  cizim: ["sec", "cubuk-ciz", "hizli-cubuk", "hizli-kolon", "hizli-kiris", "hizli-capraz", "hizli-panel", "egik-cubuk", "makas", "besik-cerceve", "asik", "kren-yolu", "mesnet", "yuk-ata"],
  duzenleme: ["geri-al", "yinele", "kopyala", "yapistir", "sil", "tasi", "dondur", "ayna", "dogrusal-dizi", "ozellik-ata", "mafsal", "yalniz-cekme"],
  degistirme: ["bol", "kesisimde-bol", "duzlemle-bol", "birlestir", "dugum-birlestir", "kesit-degistir", "aci"],
  olcme: ["olc-uzaklik", "olc-aci", "olc-alan", "olc-boy", "olc-kot", "olc-koordinat", "olc-temizle"],
  gorunum: ["gor-3b", "gor-plan", "gor-on", "gor-yan", "kat-suzgeci", "yalit", "hepsini-goster", "tel-kafes", "etiketler", "izgara", "sigdir", "tam-ekran"],
  analiz: ["coz", "denetle", "yuk-durumlari", "kombinasyonlar", "analiz-ayar", "kutuphane"],
  sonuc: ["deforme", "diyagram", "yuk-akisi", "isi-haritasi", "tasarim-dc", "tablolar", "rapor"],
};

test("katalog: kimlikler benzersiz, gruplar tanımlı, gerekli bütün komutlar var", function () {
  const idler = A.KATALOG.map(function (k) { return k.id; });
  assert.equal(new Set(idler).size, idler.length);
  const gruplar = new Set(A.GRUPLAR.map(function (g) { return g.id; }));
  A.KATALOG.forEach(function (k) {
    assert.ok(gruplar.has(k.grup), k.id);
    assert.ok(k.ad && k.ipucu, k.id);
    assert.ok(["kip", "anahtar", "eylem"].indexOf(k.tur) >= 0, k.id);
  });
  Object.keys(GEREKEN).forEach(function (g) {
    const l = A.KATALOG.filter(function (k) { return k.grup === g; }).map(function (k) { return k.id; });
    assert.deepEqual(l, GEREKEN[g], g);
  });
});

test("§19: serbest düğüm / serbest çizim komutu yok", function () {
  A.KATALOG.forEach(function (k) {
    assert.ok(!/dugum-ekle|dugum-tasi|serbest|nokta-ekle/.test(k.id), k.id);
    assert.ok(!/serbest (düğüm|çizim)|koordinatla düğüm/i.test(k.ad + " " + k.ipucu), k.id);
  });
  const cz = A.KATALOG.find(function (k) { return k.id === "cubuk-ciz"; });
  assert.match(cz.ipucu, /[Kk]esişim/);
});

test("hızlı çapraz tip seçicisi model işlemlerinin çapraz tipleriyle aynı", function () {
  assert.deepEqual(A.CAPRAZ_SECENEKLERI.map(function (s) { return s.id; }), Array.from(M.CAPRAZ_TIPLERI));
  const k = A.KATALOG.find(function (x) { return x.id === "hizli-capraz"; });
  assert.equal(k.secenekler, A.CAPRAZ_SECENEKLERI);
  assert.deepEqual(A.KATALOG.find(function (x) { return x.id === "diyagram"; }).secenekler.map(function (s) { return s.id; }), ["N", "V", "M", "Vz", "My", "T"]);
});

test("ikonlar: her komutun ve seçeneğin 24×24 özgün SVG ikonu var; yalnız güvenli öğeler", function () {
  const adlar = A.KATALOG.map(function (k) { return k.ikon; }).concat(A.CAPRAZ_SECENEKLERI.map(function (s) { return s.ikon; }), ["yonetici", "menu", "ozellestir", "diger"]);
  adlar.forEach(function (ad) {
    const ic = A.IKON[ad];
    assert.ok(typeof ic === "string" && ic.length > 20, ad);
    assert.ok(!/<(script|image|use|foreignObject|text)\b|on\w+=|href/i.test(ic), ad);
    const etiketler = ic.match(/<(\w+)/g).map(function (t) { return t.slice(1); });
    etiketler.forEach(function (t) { assert.ok(["path", "circle", "rect"].indexOf(t) >= 0, ad + ": " + t); });
    (ic.match(/-?\d*\.?\d+/g) || []).map(Number).forEach(function (v) { assert.ok(v >= -24 && v <= 24, ad + ": " + v); });   // mutlak ve göreli koordinatlar
    (ic.match(/\b(?:cx|cy|x|y)="(-?[\d.]+)"/g) || []).forEach(function (a) { const v = +a.split('"')[1]; assert.ok(v >= 0 && v <= 24, ad + ": " + a); });
  });
  // her ikon ayırt edilebilir (aynı çizim iki komutta yok)
  const ciz = A.KATALOG.map(function (k) { return A.IKON[k.ikon]; });
  assert.equal(new Set(ciz).size, ciz.length);
  const s = A.ikonSvg("sec");
  assert.match(s, /^<svg class="arac-ikon" viewBox="0 0 24 24"/);
  assert.match(s, /aria-hidden="true"/);
  assert.match(A.ikonSvg("yok-boyle-ikon"), /<svg/);
  assert.match(A.ikonSvg("🧱"), /arac-ikon-metin/);
  assert.equal(A.ikonSvg('<svg viewBox="0 0 24 24"></svg>'), '<svg viewBox="0 0 24 24"></svg>');
  assert.equal(A.ikonSvg("<img onerror=x>").indexOf("<img"), -1);
});

test("kısayollar: ayrıştırma, eşleşme (klavye düzeninden bağımsız), katalogda çakışma yok", function () {
  assert.deepEqual(A.kisayolCoz("Ctrl+Shift+z"), { ctrl: true, shift: true, alt: false, tus: "Z" });
  assert.deepEqual(A.kisayolCoz("PgUp"), { ctrl: false, shift: false, alt: false, tus: "PageUp" });
  assert.equal(A.kisayolCoz("Ctrl+"), null);
  assert.equal(A.kisayolCoz(""), null);
  const ol = function (key, o) { return Object.assign({ key: key, code: "", ctrlKey: false, metaKey: false, shiftKey: false, altKey: false }, o || {}); };
  assert.ok(A.kisayolEslesir(A.kisayolCoz("K"), ol("k", { code: "KeyK" })));
  assert.ok(!A.kisayolEslesir(A.kisayolCoz("K"), ol("K", { code: "KeyK", shiftKey: true })));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("Shift+L"), ol("L", { code: "KeyL", shiftKey: true })));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("Ctrl+Z"), ol("z", { code: "KeyZ", ctrlKey: true })));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("Ctrl+Z"), ol("z", { code: "KeyZ", metaKey: true })));
  assert.ok(!A.kisayolEslesir(A.kisayolCoz("Z"), ol("z", { code: "KeyZ", ctrlKey: true })));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("Del"), ol("Delete")));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("PgDn"), ol("PageDown")));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("Ctrl+Enter"), ol("Enter", { ctrlKey: true })));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("X"), ol("x", { code: "KeyX" })));
  assert.ok(A.kisayolEslesir(A.kisayolCoz("I"), ol("ı", { code: "KeyI" })));   // Türkçe klavye
  assert.ok(A.kisayolEslesir(A.kisayolCoz("1"), ol("1", { code: "Digit1" })));
  assert.equal(A.kisayolMetni("pgdn"), "PgDn");
  assert.equal(A.kisayolMetni("ctrl+shift+z"), "Ctrl+Shift+Z");
  const tum = A.KATALOG.filter(function (k) { return k.kisayol; }).map(function (k) { return A.kisayolMetni(k.kisayol); });
  assert.equal(new Set(tum).size, tum.length, "katalogda aynı kısayol iki komutta");
});

test("arama: Türkçe harf ve büyük/küçük harf duyarsız, ad başlangıcı önce", function () {
  assert.equal(A.normal("İÇ KUVVET ŞĞÜÖ"), "ic kuvvet sguo");
  assert.equal(A.ara(A.KATALOG, "ÇUBUK")[0].id, "cubuk-ciz");
  assert.equal(A.ara(A.KATALOG, "kolon")[0].id, "hizli-kolon");
  assert.ok(A.ara(A.KATALOG, "pgup").some(function (k) { return k.id === "duzlem-yukari"; }));    // kısayolda
  assert.ok(A.ara(A.KATALOG, "olcme").length >= 7);   // grup adında
  assert.equal(A.ara(A.KATALOG, "").length, A.KATALOG.length);
  assert.equal(A.ara(A.KATALOG, "zzzz").length, 0);
});

test("varsayılan yerleşim: her grup bir kutu, katalogdaki her komut tam bir kez", function () {
  const y = D.varsayilan();
  assert.equal(y.surum, 1);
  assert.equal(y.kutular.length, A.GRUPLAR.length);
  const hepsi = [].concat.apply([], y.kutular.map(function (k) { return k.komutlar; }));
  assert.deepEqual(hepsi.slice().sort(), A.KATALOG.map(function (k) { return k.id; }).sort());
  y.kutular.forEach(function (k) {
    assert.equal(k.konum, null); assert.ok(["ust", "alt", "sol", "sag"].indexOf(k.kenar) >= 0);
    assert.equal(k.gizli, false);
  });
  assert.equal(D.kutuBul(y, "k-cizim").yon, "dikey");
});

test("hazır yerleşimler: Çizim, Düzenleme, Değiştirme, Ölçme, Görünüm, Analiz, Sonuç + Varsayılan; hiçbir komut kaybolmaz", function () {
  assert.deepEqual(D.HAZIR_ADLARI.map(function (h) { return h.ad; }), ["Çizim", "Düzenleme", "Değiştirme", "Ölçme", "Görünüm", "Analiz", "Sonuç", "Varsayılan"]);
  D.HAZIR_ADLARI.forEach(function (h) {
    const y = D.hazir(h.id);
    const hepsi = new Set([].concat.apply([], y.kutular.map(function (k) { return k.komutlar; })));
    A.KATALOG.forEach(function (k) { assert.ok(hepsi.has(k.id), h.id + ": " + k.id); });
    assert.ok(y.kutular.some(function (k) { return !k.gizli; }), h.id);
    assert.deepEqual(D.dogrula(JSON.stringify(y)), y, h.id + " JSON gidiş-dönüş");
  });
  const o = D.hazir("olcme");
  const g = o.kutular.filter(function (k) { return !k.gizli; }).map(function (k) { return k.id; });
  assert.ok(g.indexOf("k-olcme") >= 0 && g.indexOf("k-cizim") < 0);
  assert.equal(D.kutuBul(o, "k-olcme").kucuk, false);
  assert.deepEqual(D.hazir("yok"), D.varsayilan());
});

test("doğrula: öğretici hatalar, düzeltmeler (yinelenen kimlik, komut, saydamlık sınırı)", function () {
  assert.throws(function () { D.dogrula("{bozuk"); }, /JSON olarak okunamadı/);
  assert.throws(function () { D.dogrula([]); }, /JSON nesnesi/);
  assert.throws(function () { D.dogrula({ kutular: 3 }); }, /"kutular" listesi yok/);
  assert.throws(function () { D.dogrula({ kutular: [{ ad: "x" }] }); }, /"komutlar" listesi yok/);
  assert.throws(function () { D.dogrula({ surum: 9, kutular: [] }); }, /daha yeni bir sürüm/);
  const y = D.dogrula({ kutular: [
    { id: "a", ad: "  Benim  ", komutlar: ["sec", "sec", 5, "bilinmeyen-komut"], saydamlik: 0.05, yon: "garip", konum: { x: -4, y: 12.6, yx: "sag", yy: "x" } },
    { id: "a", komutlar: [], kilitli: 1 },
  ] });
  assert.equal(y.kutular[0].ad, "Benim");
  assert.deepEqual(y.kutular[0].komutlar, ["sec", "bilinmeyen-komut"]);
  assert.equal(y.kutular[0].saydamlik, 0.3);
  assert.equal(y.kutular[0].yon, "yatay");
  assert.deepEqual(y.kutular[0].konum, { x: 0, y: 13, yx: "sag", yy: "ust" });
  assert.notEqual(y.kutular[1].id, "a");
  assert.equal(y.kutular[1].ad, "Kutu 2");
  assert.equal(y.kutular[1].kilitli, true);
});

test("düğme taşı / kopyala / çıkar: sıra, aynı kutuda yeniden sıralama, kilit, girdi değişmez", function () {
  const y0 = D.varsayilan();
  const anlik = JSON.stringify(y0);
  const y1 = D.dugmeTasi(y0, { komut: "olc-uzaklik", kaynak: "k-olcme", hedef: "k-cizim", sira: 3 });
  assert.equal(JSON.stringify(y0), anlik, "girdi değişmemeli");
  assert.equal(D.kutuBul(y1, "k-cizim").komutlar[3], "olc-uzaklik");
  assert.ok(D.kutuBul(y1, "k-olcme").komutlar.indexOf("olc-uzaklik") < 0);
  assert.deepEqual(D.komutKutulari(y1, "olc-uzaklik"), ["k-cizim"]);
  // aynı kutuda: 0. düğmeyi 3. sıranın önüne
  const once = D.kutuBul(y1, "k-aks").komutlar.slice();
  const y2 = D.dugmeTasi(y1, { komut: once[0], kaynak: "k-aks", hedef: "k-aks", sira: 3 });
  assert.deepEqual(D.kutuBul(y2, "k-aks").komutlar, [once[1], once[2], once[0]].concat(once.slice(3)));
  // kopya: kaynak korunur, hedefte yinelenmez
  const y3 = D.dugmeTasi(y2, { komut: "sec", kaynak: "k-cizim", hedef: "k-olcme", sira: 0, kopya: true });
  assert.deepEqual(D.komutKutulari(y3, "sec").sort(), ["k-cizim", "k-olcme"]);
  const y3b = D.dugmeTasi(y3, { komut: "sec", kaynak: null, hedef: "k-olcme" });
  assert.equal(D.kutuBul(y3b, "k-olcme").komutlar.filter(function (c) { return c === "sec"; }).length, 1);
  // kilit
  const k = D.kutuGuncelle(y3, "k-olcme", { kilitli: true });
  assert.throws(function () { D.dugmeTasi(k, { komut: "bol", kaynak: "k-degistirme", hedef: "k-olcme" }); }, /kilitli/);
  assert.throws(function () { D.dugmeTasi(k, { komut: "olc-aci", kaynak: "k-olcme", hedef: "k-cizim" }); }, /kilitli/);
  const kk = D.dugmeTasi(k, { komut: "olc-aci", kaynak: "k-olcme", hedef: "k-cizim", kopya: true });
  assert.ok(D.kutuBul(kk, "k-olcme").komutlar.indexOf("olc-aci") >= 0);
  assert.throws(function () { D.dugmeCikar(k, "k-olcme", "olc-aci"); }, /kilitli/);
  assert.throws(function () { D.dugmeTasi(y0, { komut: "sec", kaynak: "k-cizim", hedef: "yok" }); }, /bulunamadı/);
  const c = D.dugmeCikar(y0, "k-cizim", "sec");
  assert.ok(D.kutuBul(c, "k-cizim").komutlar.indexOf("sec") < 0);
});

test("kutu ekle / sil / adlandır / birleştir / boş alana bırakarak yeni kutu", function () {
  const y0 = D.varsayilan();
  const r1 = D.kutuEkle(y0, { komutlar: ["sec"] });
  assert.equal(D.kutuBul(r1.yerlesim, r1.id).ad, "Kutu 1");
  const r2 = D.kutuEkle(r1.yerlesim, {});
  assert.equal(D.kutuBul(r2.yerlesim, r2.id).ad, "Kutu 2");
  assert.notEqual(r1.id, r2.id);
  const r3 = D.kutuEkleTasi(y0, { konum: { x: 10, y: 20, yx: "sol", yy: "ust" }, yon: "dikey" }, "olc-alan", "k-olcme", false);
  const yk = D.kutuBul(r3.yerlesim, r3.id);
  assert.deepEqual(yk.komutlar, ["olc-alan"]); assert.equal(yk.yon, "dikey"); assert.deepEqual(yk.konum, { x: 10, y: 20, yx: "sol", yy: "ust" });
  assert.ok(D.kutuBul(r3.yerlesim, "k-olcme").komutlar.indexOf("olc-alan") < 0);
  const r4 = D.kutuEkleTasi(y0, {}, "olc-alan", "k-olcme", true);
  assert.ok(D.kutuBul(r4.yerlesim, "k-olcme").komutlar.indexOf("olc-alan") >= 0);
  const ad = D.kutuGuncelle(r1.yerlesim, r1.id, { ad: "  Sık kullanılanlar ", saydamlik: 2, bilinmeyen: 1 });
  assert.equal(D.kutuBul(ad, r1.id).ad, "Sık kullanılanlar");
  assert.equal(D.kutuBul(ad, r1.id).saydamlik, 1);
  assert.equal(D.kutuBul(ad, r1.id).bilinmeyen, undefined);
  assert.throws(function () { D.kutuGuncelle(ad, r1.id, { ad: "   " }); }, /boş olamaz/);
  const b = D.kutulariBirlestir(ad, r1.id, "k-cizim");
  assert.equal(D.kutuBul(b, "k-cizim"), null);
  const bk = D.kutuBul(b, r1.id).komutlar;
  assert.equal(bk[0], "sec"); assert.equal(bk.filter(function (c) { return c === "sec"; }).length, 1);
  assert.ok(bk.indexOf("hizli-kolon") >= 0);
  assert.throws(function () { D.kutulariBirlestir(b, r1.id, r1.id); }, /kendisiyle/);
  assert.throws(function () { D.kutulariBirlestir(D.kutuGuncelle(b, "k-aks", { kilitli: true }), r1.id, "k-aks"); }, /Kilitli/);
  const s = D.kutuSil(b, r1.id);
  assert.equal(D.kutuBul(s, r1.id), null);
  assert.throws(function () { D.kutuSil(s, r1.id); }, /bulunamadı/);
});

test("yapışma: kenarlara ve komşu kutuya; eşik dışında serbest; örtüşme önlenir", function () {
  const W = 1000, H = 600;
  assert.deepEqual(D.yapistir({ x: 15, y: 300, w: 40, h: 200 }, W, H, []), { x: 8, y: 300, kenarX: "sol", kenarY: null });
  assert.deepEqual(D.yapistir({ x: 945, y: 395, w: 40, h: 200 }, W, H, []), { x: 952, y: 392, kenarX: "sag", kenarY: "alt" });
  assert.deepEqual(D.yapistir({ x: 300, y: 300, w: 40, h: 40 }, W, H, []), { x: 300, y: 300, kenarX: null, kenarY: null });
  assert.deepEqual(D.yapistir({ x: -50, y: 900, w: 40, h: 40 }, W, H, [], 0), { x: 0, y: 560, kenarX: null, kenarY: null });
  // komşu kutunun sağına (6 px aralık) ve üst kenarına hizalanır
  const k = { x: 100, y: 100, w: 200, h: 40 };
  const r = D.yapistir({ x: 311, y: 108, w: 120, h: 40 }, W, H, [k]);
  assert.equal(r.x, 306); assert.equal(r.y, 100);
  // tam üstüne bırakılan kutu en yakın boş yere kayar
  const o = D.yapistir({ x: 120, y: 100, w: 60, h: 40 }, W, H, [k]);
  assert.ok(!D.cakisir({ x: o.x, y: o.y, w: 60, h: 40 }, k, 0));
});

test("çapa: kenara göre konum; kapsayıcı büyüyünce sağ/alt kenara bağlı kutu kenarda kalır", function () {
  const c = D.capa(940, 500, 50, 80, 1000, 600);
  assert.deepEqual(c, { x: 10, y: 20, yx: "sag", yy: "alt" });
  assert.deepEqual(D.mutlak(c, 50, 80, 1000, 600), { x: 940, y: 500 });
  assert.deepEqual(D.mutlak(c, 50, 80, 1400, 900), { x: 1340, y: 800 });
  assert.deepEqual(D.mutlak(D.capa(20, 30, 50, 80, 1000, 600), 50, 80, 300, 200), { x: 20, y: 30 });
  assert.deepEqual(D.mutlak({ x: 900, y: 0, yx: "sol", yy: "ust" }, 50, 80, 300, 200), { x: 250, y: 0 });   // sığdırılır
});

test("otomatik yerleşim: çakışmasız, sınırlar içinde, tercih edilen kenarda", function () {
  const W = 1100, H = 650;
  const liste = [
    { id: "ust1", w: 400, h: 42, kenar: "ust" }, { id: "ust2", w: 560, h: 42, kenar: "ust" }, { id: "ust3", w: 300, h: 42, kenar: "ust" },
    { id: "alt", w: 540, h: 42, kenar: "alt" }, { id: "sol", w: 46, h: 440, kenar: "sol" }, { id: "sag1", w: 46, h: 290, kenar: "sag" },
    { id: "sag2", w: 46, h: 290, kenar: "sag" },
  ];
  const sabit = [{ x: 8, y: H - 42, w: 34, h: 34 }];
  const r = D.otomatikYerlestir(liste, W, H, sabit);
  const dik = liste.map(function (l) { const q = r.get(l.id); return { id: l.id, x: q.x, y: q.y, w: l.w, h: l.h }; });
  dik.forEach(function (a, i) {
    assert.ok(a.x >= 0 && a.y >= 0 && a.x + a.w <= W && a.y + a.h <= H, a.id);
    assert.ok(!D.cakisir(a, sabit[0], 0), a.id + " yönetici düğmesi");
    dik.slice(i + 1).forEach(function (b) { assert.ok(!D.cakisir(a, b, 0), a.id + " × " + b.id); });
  });
  assert.deepEqual(r.get("ust1"), { x: 8, y: 8 });
  assert.equal(r.get("ust3").y > 8, true);          // üst sıra dolu → ikinci sıra
  assert.equal(r.get("alt").y, H - 42 - 8);
  assert.equal(r.get("sol").x, 8);
  assert.equal(r.get("sag1").x, W - 46 - 8);
  assert.ok(r.get("sol").y >= 8 + 42);              // üst kutuların altından başlar
});

test("komut kaydı: katalogla birleşir, bağlı değilse etkin değil, çalıştır, seçenek, olay", function () {
  A.katalogKaydet();
  assert.equal(A.bagliMi(A.komut("hizli-kolon")), false);
  assert.equal(A.etkinMi(A.komut("hizli-kolon")), false);
  assert.equal(A.calistir("hizli-kolon"), false);
  let n = 0, kip = null, son = null;
  const birak = A.dinle(function (ad, v) { if (ad === "calistir") son = v.id; });
  A.baglar({ "hizli-kolon": function () { n++; }, sec: { calistir: function () { kip = "sec"; }, secili: function () { return kip === "sec"; } } });
  const k = A.komut("hizli-kolon");
  assert.equal(k.ad, "Hızlı kolon"); assert.equal(k.kisayol, "K"); assert.equal(k.ikon, "hizli-kolon");
  assert.equal(A.calistir("hizli-kolon"), true); assert.equal(n, 1); assert.equal(son, "hizli-kolon");
  assert.equal(A.seciliMi(A.komut("sec")), false);
  A.calistir("sec");
  assert.equal(A.seciliMi(A.komut("sec")), true);
  A.komutKaydet({ id: "hizli-kolon", etkin: function () { return false; } });
  assert.equal(A.calistir("hizli-kolon"), false); assert.equal(n, 1);
  // seçenekli komut
  let secilen = null;
  A.komutKaydet({ id: "hizli-capraz", calistir: function () {}, secenekSec: function (id) { secilen = id; } });
  assert.equal(A.secenekDegeri(A.komut("hizli-capraz")), "X");
  // yeni (katalog dışı) komut
  const y = A.komutKaydet({ id: "ozel-araç", ad: "Benim aracım", grup_varsayilan: "cizim", ikon: "🧱", calistir: function () {} });
  assert.equal(y.grup, "cizim"); assert.equal(y.tur, "eylem");
  assert.throws(function () { A.komutKaydet({ ad: "kimliksiz" }); }, /id/);
  assert.ok(A.kisayollar().some(function (x) { return x.id === "duzlem-yukari" && x.kisayol === "PgUp"; }));
  birak();
  void secilen;
});

test("DOM'suz ortamda kur() açık hata verir; vekil işlevler kurulumdan önce uyarır", function () {
  assert.throws(function () { A.kur(null); }, /tarayıcıda/);
  assert.throws(function () { A.yerlesim(); }, /kur/);
});

test("kullanılamayan komutun nedeni (C8): komut kaydı saklar, nedenMetni çözer, çalıştır 'reddedildi' olayıyla bildirir", function () {
  A.katalogKaydet();
  assert.equal(A.nedenMetni(null), null);
  A.komutKaydet({ id: "tablolar", calistir: undefined });
  assert.equal(A.nedenMetni(A.komut("tablolar")), "Bu sayfada henüz bağlı değil.");
  let durum = false;
  const k = A.komutKaydet({ id: "tablolar", calistir: function () { durum = "calisti"; }, etkin: function () { return false; },
    neden: function () { return "Önce modeli çözün (Çöz ▶)."; } });
  assert.equal(typeof k.neden, "function");
  assert.equal(A.nedenMetni(k), "Önce modeli çözün (Çöz ▶).");
  const olaylar = [];
  const birak = A.dinle(function (ad, v) { if (ad === "reddedildi") olaylar.push(v); });
  assert.equal(A.calistir("tablolar"), false);
  assert.equal(durum, false);
  assert.deepEqual(olaylar, [{ id: "tablolar", neden: "Önce modeli çözün (Çöz ▶).", ad: "Tablolar" }]);
  // metin neden, boş neden ve hata atan neden işlevi
  A.komutKaydet({ id: "tablolar", neden: "Silinecek ölçü yok." });
  assert.equal(A.nedenMetni(A.komut("tablolar")), "Silinecek ölçü yok.");
  A.komutKaydet({ id: "tablolar", neden: "" });
  assert.equal(A.nedenMetni(A.komut("tablolar")), null);
  A.komutKaydet({ id: "tablolar", neden: function () { throw new Error("x"); } });
  assert.equal(A.nedenMetni(A.komut("tablolar")), null);
  // etkin komut olay yaymaz, çalışır
  A.komutKaydet({ id: "tablolar", etkin: true });
  assert.equal(A.calistir("tablolar"), true); assert.equal(durum, "calisti"); assert.equal(olaylar.length, 1);
  birak();
});

test("kenar payları: kenara yaslı kutular (ve bitişik ikinci sıra) payı belirler, ortada yüzen kutu sayılmaz", function () {
  const W = 1000, H = 600;
  assert.deepEqual(D.kenarPaylari([], W, H), { sol: 0, ust: 0, sag: 0, alt: 0 });
  const kutular = [
    { x: 8, y: 8, w: 300, h: 40 },        // sol üst köşe: sol ve üst kenara değer → payı küçük olan (üst, 48)
    { x: 100, y: 52, w: 200, h: 40 },     // üst kutunun altında bitişik → üst, 92
    { x: 8, y: 100, w: 46, h: 400 },      // sol, 54
    { x: 946, y: 100, w: 46, h: 300 },    // sağ, 54
    { x: 300, y: 552, w: 400, h: 40 },    // alt, 48
    { x: 400, y: 250, w: 100, h: 100 },   // ortada yüzen
    { x: 0, y: 0, w: 0, h: 0 }, null,     // gizli / boş
  ];
  assert.deepEqual(D.kenarPaylari(kutular, W, H), { sol: 54, ust: 92, sag: 54, alt: 48 });
  assert.equal(typeof A.kenarPaylari, "function");
  assert.deepEqual(A.kenarPaylari(), { sol: 0, ust: 0, sag: 0, alt: 0 });   // yönetici kurulmadan
});

test("kenar payları: boydan boya dikey sütun yan kenarın payıdır (yüksekliği alt/üst pay sayılmaz)", function () {
  const W = 900, H = 340;
  // sol kenarda yönetici düğmesi; Çizim kutusu onun yanına itilmiş (x = 48), bütün yüksekliği kaplar
  const l = [{ x: 8, y: 300, w: 32, h: 32 }, { x: 48, y: 8, w: 70, h: 326 }, { x: 124, y: 290, w: 500, h: 42 }];
  assert.deepEqual(D.kenarPaylari(l, W, H), { sol: 118, ust: 0, sag: 0, alt: 50 });
  // boydan boya yatay şerit: üst kenara yakınsa üst pay
  assert.deepEqual(D.kenarPaylari([{ x: 8, y: 60, w: 884, h: 40 }], W, H), { sol: 0, ust: 100, sag: 0, alt: 0 });
});

test("otomatik yerleşim (kw/kh): kutu kenar şeridinde aranır, yer yoksa katlanmış başlığıyla yerleşir", function () {
  const W = 800, H = 400;
  const uc = ["a", "b", "c"].map(function (id) { return { id: id, w: 700, h: 42, kenar: "ust", kw: 120, kh: 30 }; });
  const r = D.otomatikYerlestir(uc, W, H, []);
  assert.deepEqual(r.get("a"), { x: 8, y: 8 });
  assert.equal(r.get("b").katla, undefined);
  assert.ok(r.get("b").y <= 8 + 2 * 42 + 6, "b şeritte");
  assert.equal(r.get("c").katla, true);
  const dik = [{ x: r.get("a").x, y: r.get("a").y, w: 700, h: 42 }, { x: r.get("b").x, y: r.get("b").y, w: 700, h: 42 }, { x: r.get("c").x, y: r.get("c").y, w: 120, h: 30 }];
  dik.forEach(function (a, i) {
    assert.ok(a.x >= 0 && a.y >= 0 && a.x + a.w <= W && a.y + a.h <= H);
    dik.slice(i + 1).forEach(function (b) { assert.ok(!D.cakisir(a, b, 0)); });
  });
  // kw/kh verilmezse eski davranış: sahnenin içine doğru ilerler, katlanmaz
  const eski = D.otomatikYerlestir(uc.map(function (u) { return { id: u.id, w: u.w, h: u.h, kenar: u.kenar }; }), W, H, []);
  assert.equal(eski.get("c").katla, undefined);
  assert.ok(eski.get("c").y > r.get("b").y);
});

test("otomatik yerleşim (serbest): az önce açılan kutu şeritte yer yoksa açık boyuyla sahnede boş yer arar; hiç yoksa katlanır", function () {
  const W = 800, H = 400;
  const sabit = [{ x: 8, y: 8, w: 700, h: 42 }, { x: 8, y: 56, w: 700, h: 42 }];   // üst şerit dolu
  const it = { id: "x", w: 600, h: 42, kenar: "ust", kw: 120, kh: 30 };
  // şerit sınırlı arama: üst şeritte (iki kutu kalınlığı) 600 px yer yok → katlanır
  assert.equal(D.otomatikYerlestir([it], W, H, sabit).get("x").katla, true);
  // serbest: açık boyuyla sahnenin içinde (şeridin altında) yer bulunur, katlanmaz, sabitlerle çakışmaz
  const q = D.otomatikYerlestir([Object.assign({ serbest: true }, it)], W, H, sabit).get("x");
  assert.equal(q.katla, undefined);
  assert.ok(q.y > 56 + 42, "şeridin altında: " + q.y);
  sabit.forEach(function (s) { assert.ok(!D.cakisir({ x: q.x, y: q.y, w: 600, h: 42 }, s, 0)); });
  // hiç yer yoksa serbest kutu da katlanmış başlığıyla yerleşir
  const dolu = [{ x: 0, y: 0, w: W, h: 330 }, { x: 0, y: 336, w: 300, h: 64 }];   // yalnız sağ altta başlık kadar yer
  const r = D.otomatikYerlestir([Object.assign({ serbest: true }, it)], W, H, dolu).get("x");
  assert.equal(r.katla, true);
  assert.ok(!D.cakisir({ x: r.x, y: r.y, w: 120, h: 30 }, dolu[0], 0));
});

test("katlı kutu: varsayılan açık, kutuGuncelle ve doğrula 'katli' alanını korur", function () {
  const y0 = D.varsayilan();
  const id = y0.kutular[0].id;
  assert.equal(y0.kutular[0].katli, false);
  const y1 = D.kutuGuncelle(y0, id, { katli: 1 });
  assert.equal(D.kutuBul(y1, id).katli, true);
  assert.equal(D.kutuBul(y0, id).katli, false);                    // girdi değişmez
  const y2 = D.dogrula(JSON.parse(JSON.stringify(y1)));
  assert.equal(D.kutuBul(y2, id).katli, true);
  assert.equal(D.kutuBul(D.dogrula({ kutular: [{ id: "x", komutlar: ["sec"] }] }), "x").katli, false);
  assert.equal(D.kutuBul(D.kutuGuncelle(y1, id, { katli: false }), id).katli, false);
});
