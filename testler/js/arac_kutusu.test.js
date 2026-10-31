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
  assert.equal(y.surum, 2);
  assert.equal(A.SURUM, 2);
  assert.equal(y.kutular.length, A.GRUPLAR.length);
  const hepsi = [].concat.apply([], y.kutular.map(function (k) { return k.komutlar; }));
  assert.deepEqual(hepsi.slice().sort(), A.KATALOG.map(function (k) { return k.id; }).sort());
  y.kutular.forEach(function (k) {
    assert.equal(k.konum, null); assert.ok(["ust", "alt", "sol", "sag"].indexOf(k.kenar) >= 0);
    assert.equal(k.gizli, false); assert.equal(k.yer, "kenar"); assert.ok(k.sira >= 1);
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

test("kenar payları: yalnız üst kenara değen sütun (tam ekranda uzayan kapsayıcı) yan kenarın payıdır", function () {
  // 1280×720 tam ekran: Çizim sütunu yönetici düğmesinin yanında (x = 48), artık alta değmiyor; Görünüm + Analiz altta
  const W = 956, H = 475;
  const l = [{ x: 8, y: 433, w: 34, h: 34 }, { x: 48, y: 8, w: 70, h: 361 }, { x: 124, y: 8, w: 574, h: 42 }, { x: 124, y: 56, w: 153, h: 35 },
    { x: 124, y: 425, w: 563, h: 42 }, { x: 124, y: 377, w: 330, h: 42 }, { x: 878, y: 8, w: 70, h: 325 }];
  assert.deepEqual(D.kenarPaylari(l, W, H), { sol: 118, ust: 91, sag: 78, alt: 98 });
  // ortadaki sütun üst kenara değiyorsa yan payı daha büyükse üst pay kalır
  assert.deepEqual(D.kenarPaylari([{ x: 400, y: 8, w: 60, h: 150 }], 1000, 600), { sol: 0, ust: 158, sag: 0, alt: 0 });
  // yalnız sol kenara değen şerit: yakın olduğu üst/alt kenarın payı daha küçükse o
  assert.deepEqual(D.kenarPaylari([{ x: 8, y: 500, w: 500, h: 40 }], 1000, 600), { sol: 0, ust: 0, sag: 0, alt: 100 });
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

// ---- rıhtım (kenar şeridi) yerleşimi: tasarım §3 boy tablosu (1920'de ölçülen kutular, px) ve §4 başvuru katmanları
const BOY = {   // [yt genişlik, yb genişlik, yk genişlik, d1 [w, h], d2 [w, h]]; yt/yb yüksekliği 42, yk 30
  "k-cizim": [434, 398, 108, [70, 361], [78, 217]], "k-duzenleme": [574, 506, 140, [70, 469], [78, 253]],
  "k-aks": [424, 398, 98, [70, 361], [78, 217]], "k-gorunum": [563, 506, 129, [70, 469], [78, 253]],
  "k-analiz": [330, 290, 112, [70, 253], [78, 145]], "k-sonuc": [402, 362, 112, [70, 325], [78, 181]],
  "k-olcme": [367, 326, 113, [70, 289], [78, 181]], "k-degistirme": [393, 326, 139, [70, 289], [78, 181]],
  "k-uretec": [373, 290, 155, [70, 253], [78, 145]],
};
const VARS = [["k-cizim", "sol", 1], ["k-duzenleme", "ust", 1], ["k-gorunum", "alt", 1], ["k-analiz", "alt", 2], ["k-sonuc", "sag", 1],
  ["k-aks", "ust", 2], ["k-olcme", "sag", 2], ["k-degistirme", "sag", 3], ["k-uretec", "sol", 2]];
function olcu(id) {
  const b = BOY[id];
  return { yt: [b[0], 42], yb: [b[1], 42], yk: [b[2], 30], d1: b[3], d2: b[4], dk1: [b[3][0], 30], dk2: [b[4][0], 30] };
}
function liste(ek) {
  return VARS.map(function (v, i) { return Object.assign({ id: v[0], kenar: v[1], sira: v[2], oncelik: i, katli: false, olcu: olcu(v[0]) }, (ek || {})[v[0]] || {}); });
}
const SEC = { kose: [[34, 34]], tasma: [34, 34] };
function bicimler(r) { const o = {}; r.kutular.forEach(function (q, id) { o[id] = q.bicim; }); return o; }
function dikdortgenler(r) { const l = []; r.kutular.forEach(function (q) { l.push(q); }); return l.concat(r.kose, r.tasmaDugme ? [r.tasmaDugme] : []); }

test("rıhtım: başvuru katmanlarında taşanlar ve biçimler (tasarım §4)", function () {
  const BEKLENEN = [
    [1466, 701, [], function (r, b) {
      ["k-duzenleme", "k-aks", "k-gorunum", "k-analiz"].forEach(function (id) { assert.equal(b[id], "yt", id); });
      ["k-cizim", "k-uretec", "k-sonuc", "k-olcme", "k-degistirme"].forEach(function (id) { assert.equal(b[id], "d2", id); });
      assert.deepEqual(r.pay, { sol: 86, ust: 50, sag: 86, alt: 50 });
    }],
    [1116, 571, ["k-degistirme"]],
    [1146, 705, []],
    [1011, 389, ["k-olcme", "k-degistirme", "k-uretec"], function (r, b) { assert.equal(b["k-aks"], "yb"); }],
    [1041, 523, ["k-degistirme"]],
    [926, 341, ["k-olcme", "k-degistirme", "k-uretec"], function (r, b) {
      ["k-duzenleme", "k-aks", "k-gorunum", "k-analiz"].forEach(function (id) { assert.equal(b[id], "yb", id); });
    }],
    [670, 347, ["k-analiz", "k-aks", "k-olcme", "k-degistirme", "k-uretec"]],
    [1496, 835, [], function (r, b) {
      assert.equal(b["k-cizim"], "d1"); assert.equal(b["k-uretec"], "d1");
      ["k-sonuc", "k-olcme", "k-degistirme"].forEach(function (id) { assert.equal(b[id], "d2", id); });
    }],
    [956, 475, ["k-olcme", "k-degistirme", "k-uretec"], function (r, b) {
      assert.deepEqual([b["k-cizim"], b["k-sonuc"], b["k-duzenleme"], b["k-aks"], b["k-gorunum"], b["k-analiz"]], ["d1", "d1", "yb", "yt", "yt", "yb"]);
    }],
    [700, 523, ["k-analiz", "k-aks", "k-degistirme"]],
  ];
  BEKLENEN.forEach(function (c) {
    const r = D.rihtim(liste(), c[0], c[1], SEC);
    assert.deepEqual(r.tasma, c[2], c[0] + "×" + c[1]);
    assert.equal(!!r.tasmaDugme, c[2].length > 0, c[0] + "×" + c[1] + " taşma düğmesi");
    if (c[3]) c[3](r, bicimler(r));
    // yönetici düğmesi alt sol köşede (8, H − 42), taşma düğmesi yanında
    assert.deepEqual(r.kose[0], { x: 8, y: c[1] - 42, w: 34, h: 34 });
    if (r.tasmaDugme) assert.deepEqual(r.tasmaDugme, { x: 48, y: c[1] - 42, w: 34, h: 34 });
  });
  // 1466×701'de konumlar: üst bant soldan, alt bant köşe düğmesinden sonra, sağ sütun sağa yaslı
  const r = D.rihtim(liste(), 1466, 701, SEC);
  assert.deepEqual(["k-duzenleme", "k-aks", "k-gorunum", "k-analiz", "k-cizim", "k-uretec", "k-sonuc"].map(function (id) { const q = r.kutular.get(id); return [q.x, q.y]; }),
    [[8, 8], [588, 8], [48, 651], [617, 651], [8, 56], [8, 279], [1380, 56]]);
});

test("rıhtım: değişmezler (W 640..2000 × H 200..1100): çakışma yok, sınırlar içinde, iç dikdörtgen boş, belirlenimci, öncelik", function () {
  const b = 8, g = 6;
  let n = 0;
  for (let W = 640; W <= 2000; W += 37) {
    for (let H = 200; H <= 1100; H += 41) {
      // katlı kutular da (kullanıcı katladı) aynı kurallara uyar
      const ek = (W + H) % 3 === 0 ? { "k-sonuc": { katli: true }, "k-aks": { katli: true } } : null;
      const l = liste(ek), r = D.rihtim(l, W, H, SEC), R = dikdortgenler(r), ad = W + "×" + H;
      for (let i = 0; i < R.length; i++) {
        const a = R[i];
        assert.ok(a.x >= 0 && a.y >= 0 && a.x + a.w <= W && a.y + a.h <= H, ad + " sınır");
        for (let j = i + 1; j < R.length; j++) assert.ok(!D.cakisir(a, R[j], 0), ad + " çakışma " + i + "/" + j);
      }
      const ic = { x: r.pay.sol, y: r.pay.ust, w: W - r.pay.sol - r.pay.sag, h: H - r.pay.ust - r.pay.alt };
      assert.ok(ic.w > 0 && ic.h > 0, ad + " iç dikdörtgen");
      R.forEach(function (q) {
        const ox = Math.min(q.x + q.w, ic.x + ic.w) - Math.max(q.x, ic.x), oy = Math.min(q.y + q.h, ic.y + ic.h) - Math.max(q.y, ic.y);
        assert.ok(ox <= 0 || oy <= 0, ad + " kutu iç dikdörtgende");
      });
      assert.deepEqual(D.rihtim(liste(ek), W, H, SEC), r, ad + " belirlenimci");
      // her kutu ya bir şeritte ya çekmecede, ikisinde birden değil
      const yerli = new Set(r.kutular.keys());
      l.forEach(function (it) { assert.ok(yerli.has(it.id) !== (r.tasma.indexOf(it.id) >= 0), ad + " " + it.id); });
      // öncelik: şeritte taşan bir kutu varken o şeridin daha düşük öncelikli kendi kutusu yerleşmez (kutu tek başına sığmıyorsa hariç)
      const tU = r.pay.ust ? r.pay.ust - b : 0, tA = r.pay.alt ? r.pay.alt - b : 0;
      const L = { ust: W - 2 * b, alt: W - 2 * b - 40 - (r.tasmaDugme ? 40 : 0) }, sL = H - 2 * b - (tU ? tU + g : 0) - (tA ? tA + g : 0);
      r.tasma.forEach(function (id) {
        const it = l.find(function (x) { return x.id === id; });
        const bant = it.kenar === "ust" || it.kenar === "alt";
        const tekBasina = bant ? (it.katli ? it.olcu.yk[0] : it.olcu.yb[0]) > L[it.kenar] : it.olcu[it.katli ? "dk2" : "d2"][1] > sL;
        if (tekBasina) return;
        l.forEach(function (o_) {
          const q = r.kutular.get(o_.id);
          if (o_.kenar === it.kenar && o_.oncelik > it.oncelik && q && q.kenar === it.kenar && !q.yedek) assert.fail(ad + ": " + id + " taşarken " + o_.id + " şeritte");
        });
      });
      n++;
    }
  }
  assert.ok(n > 800);
});

test("rıhtım: iki geçiş — taşma varsa taşma düğmesi köşeye eklenip yeniden yerleşilir; en küçük sahne kuralları", function () {
  // taşma yoksa tek geçiş (taşma düğmesi yok), varsa ikinci geçiş köşe listesine düğmeyi ekleyen geçişin aynısı
  const r0 = D.rihtim(liste(), 1466, 701, SEC);
  assert.equal(r0.tasmaDugme, null);
  assert.deepEqual(r0, D.rihtim(liste(), 1466, 701, { kose: [[34, 34]] }));
  const r1 = D.rihtim(liste(), 926, 341, SEC), r2 = D.rihtim(liste(), 926, 341, { kose: [[34, 34], [34, 34]] });
  assert.deepEqual(r1.tasma, r2.tasma); assert.deepEqual(r1.pay, r2.pay);
  assert.deepEqual(r1.tasmaDugme, r2.kose[1]); assert.deepEqual(r1.kose, [r2.kose[0]]);
  r1.kutular.forEach(function (q, id) { assert.deepEqual(q, r2.kutular.get(id), id); });
  // tasmaZorla: taşan yokken de düğmeye yer açılır (yüzen kutu sahnede yer bulamadı)
  assert.deepEqual(D.rihtim(liste(), 1466, 701, Object.assign({ tasmaZorla: true }, SEC)).tasmaDugme, { x: 48, y: 701 - 42, w: 34, h: 34 });
  // yönetici yok (sec.kose []): alt bant köşeden başlar, alt pay yalnız kutulardan
  const ry = D.rihtim(liste(), 1466, 701, {});
  assert.equal(ry.kutular.get("k-gorunum").x, 8);
  // en küçük sahne yüksekliği: H = 220'de üst bant kalkar (kutuları başka şeride ya da çekmeceye), alt bant ve köşe kalır
  const rh = D.rihtim(liste(), 1466, 220, SEC);
  assert.equal(rh.pay.ust, 0);
  rh.kutular.forEach(function (q, id) { assert.notEqual(q.kenar, "ust", id); });
  assert.ok(rh.tasma.indexOf("k-duzenleme") >= 0);
  assert.ok(rh.pay.alt >= 42);
  assert.ok(220 - rh.pay.ust - rh.pay.alt - 2 * 6 >= D.SAHNE_MIN_H - 16);
  // en küçük sahne genişliği: dar ve yüksek katmanda sağ sütun kalkar
  const rw = D.rihtim(liste(), 300, 900, SEC);
  assert.ok(300 - (rw.pay.sol ? rw.pay.sol + 6 : 8) - (rw.pay.sag ? rw.pay.sag + 6 : 8) >= D.SAHNE_MIN_W);
  assert.equal(rw.pay.sag, 0);
  // geri düşme: sağ sütuna sığmayan kutu öteki şeride kalınlığı değişmeden girer (yedek), kendi kutularından sonra dizilir
  const rf = D.rihtim(liste(), 1600, 520, SEC), f = [];
  rf.kutular.forEach(function (q, id) { if (q.yedek) f.push([id, q.kenar]); });
  f.forEach(function (x) { const it = liste().find(function (o_) { return o_.id === x[0]; }); assert.notEqual(it.kenar, x[1]); });
});

test("rıhtım: katlı kutu bantta katlı başlık (yk), sütunda sütun genişliğinde çip (dk); kenar sırası (sira) görünür sırayı belirler", function () {
  const r = D.rihtim(liste({ "k-aks": { katli: true }, "k-sonuc": { katli: true } }), 1116, 571, SEC);
  assert.equal(r.kutular.get("k-aks").bicim, "yk");
  const q = r.kutular.get("k-sonuc");
  assert.equal(q.bicim, "dk2"); assert.equal(q.w, q.sutunW); assert.equal(q.h, 30); assert.equal(q.x, 1116 - 8 - q.sutunW);
  // katlanan Sonuç yer açar: Değiştirme artık sığar
  assert.deepEqual(r.tasma, []);
  // sira: alt bantta Analiz önce (sira 1), Görünüm sonra; öncelik değişmez
  const r2 = D.rihtim(liste({ "k-analiz": { sira: 0 } }), 1466, 701, SEC);
  assert.ok(r2.kutular.get("k-analiz").x < r2.kutular.get("k-gorunum").x);
});

test("kenaraAl / serbestBirak: şeridin en öncelikli kutusu, sira yeniden numaralanır; yüzen kutu çapasıyla", function () {
  const y0 = { surum: 2, ad: "t", kutular: VARS.map(function (v) { return { id: v[0], ad: v[0], komutlar: [], kenar: v[1], sira: v[2] }; }) };
  const y = D.dogrula(y0);
  const ids = function (yy) { return yy.kutular.map(function (k) { return k.id; }); };
  // Ölçme sağ şeridin önüne: dizide k-sonuc'un önüne; görünür sırası yerinde (2)
  const a = D.kenaraAl(y, "k-olcme", "sag");
  assert.deepEqual(ids(a).slice(0, 6), ["k-cizim", "k-duzenleme", "k-gorunum", "k-analiz", "k-olcme", "k-sonuc"]);
  assert.deepEqual(["k-sonuc", "k-olcme", "k-degistirme"].map(function (id) { return D.kutuBul(a, id).sira; }), [1, 2, 3]);
  assert.equal(JSON.stringify(D.dogrula(y0)), JSON.stringify(y), "girdi değişmez");
  // Analiz sol sütuna, Üreteç'in önüne (yuva): en öncelikli sol kutusu, sira 2; Görünüm alt bantta yeniden 1
  const b = D.kenaraAl(y, "k-analiz", "sol", { once: "k-uretec" });
  assert.equal(ids(b)[0], "k-analiz");
  const ka = D.kutuBul(b, "k-analiz");
  assert.deepEqual([ka.kenar, ka.yer, ka.sira, D.kutuBul(b, "k-cizim").sira, D.kutuBul(b, "k-uretec").sira], ["sol", "kenar", 2, 1, 3]);
  // yüzdür: konum ve yön; öncelik ve dönülecek kenar korunur; kenara alınınca konum silinir
  const c = D.serbestBirak(y, "k-analiz", { x: 300, y: 200, yx: "sol", yy: "ust" }, "dikey");
  const kc = D.kutuBul(c, "k-analiz");
  assert.deepEqual([kc.yer, kc.yon, kc.kenar, kc.konum], ["serbest", "dikey", "alt", { x: 300, y: 200, yx: "sol", yy: "ust" }]);
  assert.deepEqual(ids(c), ids(y));
  const geri = D.dogrula(JSON.stringify(c));
  assert.deepEqual(D.kutuBul(geri, "k-analiz").konum, kc.konum, "yüzen kutu JSON gidiş-dönüş");
  const dd = D.kenaraAl(c, "k-analiz", "ust", { once: null });
  const kd = D.kutuBul(dd, "k-analiz");
  assert.deepEqual([kd.yer, kd.kenar, kd.konum, kd.sira], ["kenar", "ust", null, 3]);
  assert.equal(ids(dd)[1], "k-analiz");
  assert.throws(function () { D.kenaraAl(y, "yok", "sol"); }, /bulunamadı/);
  assert.throws(function () { D.serbestBirak(y, "k-aks", null); }, /konum/);
  // kutuGuncelle: çapasız kutu yüzemez; kenara alınan kutunun çapası düşer
  assert.equal(D.kutuBul(D.kutuGuncelle(y, "k-aks", { yer: "serbest" }), "k-aks").yer, "kenar");
  assert.equal(D.kutuBul(D.kutuGuncelle(c, "k-analiz", { yer: "kenar" }), "k-analiz").konum, null);
  // yeni kutu: konumsuzsa şeridin sonuna (dizinin sonunda), konumluysa yüzer
  const e = D.kutuEkle(y, { kenar: "sag" }), ke = D.kutuBul(e.yerlesim, e.id);
  assert.deepEqual([ke.yer, ke.sira, ids(e.yerlesim).length - 1], ["kenar", 4, ids(e.yerlesim).indexOf(e.id)]);
  const e2 = D.kutuEkle(y, { konum: { x: 5, y: 5, yx: "sol", yy: "ust" } });
  assert.equal(D.kutuBul(e2.yerlesim, e2.id).yer, "serbest");
});

test("doğrula: sürüm 1 → 2 geçişi (otoKatli açılır, kenar çapadan, sıra çapalardan, konum düşer)", function () {
  const v1 = { surum: 1, ad: "bina", kutular: [
    { id: "k-cizim", ad: "Çizim", komutlar: ["sec"], yon: "dikey", kenar: "sol", konum: { x: 48, y: 8, yx: "sol", yy: "ust" } },
    { id: "k-duzenleme", ad: "Düzenleme", komutlar: ["sil"], kenar: "ust", konum: { x: 124, y: 8, yx: "sol", yy: "ust" } },
    { id: "k-aks", ad: "Aks", komutlar: ["aks-ekle"], kenar: "ust", katli: true, otoKatli: true, otoKonum: { x: 700, y: 8, yx: "sol", yy: "ust" },
      konum: { x: 20, y: 8, yx: "sag", yy: "ust" } },
    { id: "k-gorunum", ad: "Görünüm", komutlar: ["gor-3b"], kenar: "alt", konum: { x: 400, y: 8, yx: "sag", yy: "alt" } },
    { id: "k-analiz", ad: "Analiz", komutlar: ["coz"], kenar: "alt", konum: { x: 124, y: 8, yx: "sol", yy: "alt" } },
    { id: "k-sonuc", ad: "Sonuç", komutlar: ["rapor"], yon: "dikey", kenar: "sag", katli: true, konum: { x: 8, y: 8, yx: "sag", yy: "ust" } },
    { id: "k-olcme", ad: "Ölçme", komutlar: ["olc-aci"], yon: "dikey", kenar: "sag", konum: { x: 8, y: 120, yx: "sag", yy: "alt" } },
    { id: "k-yuzen", ad: "Benim", komutlar: ["sec"], yon: "dikey", kenar: "ust", konum: { x: 300, y: 300, yx: "sol", yy: "ust" } },
    { id: "k-sol-yatay", ad: "Yatay", komutlar: ["sec"], kenar: "alt", konum: { x: 8, y: 16, yx: "sol", yy: "ust" } },
  ] };
  const rapor = {};
  const y = D.dogrula(JSON.stringify(v1), rapor);
  assert.equal(rapor.goc, true);
  assert.equal(y.surum, 2);
  y.kutular.forEach(function (k) {
    assert.equal(k.yer, "kenar", k.id); assert.equal(k.konum, null, k.id);
    assert.ok(!("otoKatli" in k) && !("otoKonum" in k), k.id);
  });
  const k = function (id) { return D.kutuBul(y, id); };
  assert.equal(k("k-aks").katli, false, "otoKatli → açık");
  assert.equal(k("k-sonuc").katli, true, "kullanıcının katlaması korunur");
  // kenar: dikey kutu yan kenara değiyorsa (≤ 22 px) o kenar; Çizim yönetici düğmesinin yanına itilmişti (x = 48): eski kenarı (sol)
  assert.equal(k("k-cizim").kenar, "sol");
  assert.equal(k("k-sonuc").kenar, "sag");
  assert.equal(k("k-yuzen").kenar, "ust", "kenara değmeyen kutu eski kenarında");
  // yatay kutu üst/alt kenara değiyorsa o kenar: üst kenara değen (y = 16) "alt" tercihli kutu üst şeride geçer
  assert.equal(k("k-sol-yatay").kenar, "ust");
  // sıra: bantta soldan çapalılar soldan sağa, sonra sağdan çapalılar (sağ uzaklığı büyük olan önce); sütunda üstten, sonra alttan
  assert.deepEqual(["k-sol-yatay", "k-duzenleme", "k-yuzen", "k-aks"].map(function (id) { return k(id).sira; }), [1, 2, 3, 4]);
  assert.deepEqual(["k-analiz", "k-gorunum"].map(function (id) { return k(id).sira; }), [1, 2]);
  assert.deepEqual(["k-sonuc", "k-olcme"].map(function (id) { return k(id).sira; }), [1, 2]);
  // sürüm 2 gidiş-dönüş: geçiş yok
  const r2 = {};
  assert.deepEqual(D.dogrula(JSON.parse(JSON.stringify(y)), r2), y);
  assert.equal(r2.goc, undefined);
  assert.throws(function () { D.dogrula({ surum: 3, kutular: [] }); }, /daha yeni bir sürüm/);
});

test("sayfa tuşları (C22): donmuş liste, 10 satır sırasıyla, Enter dahil; grup adları", function () {
  const S = A.SAYFA_TUSLARI;
  assert.ok(Object.isFrozen(S) && S.every(function (x) { return Object.isFrozen(x); }));
  assert.deepEqual(S.map(function (x) { return x.kisayol; }), ["Esc", "Shift+F10", "Enter", "?", "PgUp", "PgDn", "F", "Shift+F", "Ctrl+Shift+Z", "Backspace"]);
  assert.deepEqual(S.map(function (x) { return x.grup; }), ["sayfa", "sayfa", "sayfa", "sayfa", "aks", "aks", "gorunum", "gorunum", "duzenleme", "duzenleme"]);
  assert.equal(S[2].ad, "Bağlam menüsünde: Bilgi");
  assert.equal(S[0].ad, "Kipten çık, seçimi ya da yarım çizimi / ölçümü bırak; tam ekrandan çık");
  S.forEach(function (x) { assert.deepEqual(Object.keys(x), ["kisayol", "ad", "grup"]); assert.ok(x.ad.length > 3); });
  assert.equal(A.grupAdi("sayfa"), "Sayfa"); assert.equal(A.grupAdi("gorunum"), "Görünüm"); assert.equal(A.grupAdi("aks"), "Aks");
  assert.throws(function () { "use strict"; S.push({}); });
});

test("en yakın boş yer (yüzen kutu geri düşmesi): engellerden ARALIK uzakta, sınırlar içinde; yer yoksa null", function () {
  const dolu = [{ x: 8, y: 8, w: 500, h: 42 }, { x: 8, y: 56, w: 70, h: 300 }];
  const p = D.yakinBos({ x: 20, y: 20, w: 100, h: 40 }, 800, 400, dolu);
  assert.ok(p && !dolu.some(function (d) { return D.cakisir({ x: p.x, y: p.y, w: 100, h: 40 }, d); }));
  assert.ok(p.x >= 8 && p.y >= 8 && p.x + 100 <= 792 && p.y + 40 <= 392);
  assert.ok(Math.hypot(p.x - 20, p.y - 20) < 120, JSON.stringify(p));
  assert.deepEqual(D.yakinBos({ x: 300, y: 200, w: 100, h: 40 }, 800, 400, dolu), { x: 300, y: 200 });
  assert.equal(D.yakinBos({ x: 0, y: 0, w: 100, h: 40 }, 800, 400, [{ x: 0, y: 0, w: 800, h: 400 }]), null);
});
