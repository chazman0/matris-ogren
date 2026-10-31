// op4/js/op4_cekirdek.js cephe sınamaları (B, F1 iş 1.3; MIMARI §9.3, §9.4, kabul B4). Çalıştırma: node --test op4/testler/js/*.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const OP4 = path.join(__dirname, "..", "..");
const DOCS = path.join(OP4, "..", "docs");
const Op4Ops = require(path.join(OP4, "js", "op4_ops.js"));
const Op4Cekirdek = require(path.join(OP4, "js", "op4_cekirdek.js"));
const IFC = require(path.join(DOCS, "ifc_disari.js"));
const SABLON = path.join(OP4, "testler", "derlem", "sablonlar");
const metinOku = (ad) => fs.readFileSync(path.join(SABLON, ad + ".json"), "utf8");
const yeni = (ayar) => Op4Cekirdek.olustur({ Op4Ops }, Object.assign({ saat: () => Date.UTC(2026, 0, 2, 3, 4, 5) }, ayar || {}));

test("TASLAK boş, beyaz liste Faz 1, C++ islem:: adlarıyla aynı (B4)", () => {
  assert.deepEqual([...Op4Cekirdek.TASLAK], []);
  assert.deepEqual([...Op4Cekirdek.ISLEMLER], ["hizliAks", "aksSihirbazi", "baslikDegistir", "genellestir"]);
  const h = fs.readFileSync(path.join(OP4, "kaynak", "cekirdek", "model_cekirdegi.h"), "utf8");
  const c = [...h.matchAll(/inline constexpr const char\* \w+ = "(\w+)";/g)].map((m) => m[1]);
  assert.deepEqual(c, [...Op4Cekirdek.ISLEMLER]);
  const c2 = yeni();
  assert.deepEqual(c2.islemler(), [...Op4Cekirdek.ISLEMLER]);
});

test("hizliAks: boş modelde aks ızgarası; rapor, sahne sürümü, geri al / yinele", () => {
  const c = yeni();
  c.yeniBos({ baslik: "Adsız 1" });
  const s0 = c.sahneSurumu();
  const r = c.uygula("hizliAks", { x: [6, 6], y: [5], z: [3.5, 3] });
  assert.equal(r.basarili, true, r.hata);
  assert.equal(r.icerik_degisti, true);
  assert.equal(r.sahne_surumu, s0 + 1);
  assert.deepEqual(r.eklenen.map((k) => k.tur), ["aks", "aks", "aks", "aks", "aks"]);
  const m = JSON.parse(c.metin());
  assert.deepEqual(m.akslar.x.map((a) => [a.ad, a.konum]), [["A", 0], ["B", 6], ["C", 12]]);
  assert.deepEqual(m.akslar.y.map((a) => [a.ad, a.konum]), [["1", 0], ["2", 5]]);
  assert.deepEqual(m.akslar.z.map((a) => [a.konum, a.kat]), [[0, 0], [3.5, 1], [6.5, 2]]);
  assert.deepEqual(m.katlar.map((k) => [k.no, k.kot]), [[0, 0], [1, 3.5], [2, 6.5]]);
  const s = c.sahne();
  assert.equal(s.akslar.length, 5);
  assert.equal(s.seviyeler.length, 3);
  assert.equal(s.sahne_surumu, c.sahneSurumu());
  const g = c.geriAlBilgisi();
  assert.deepEqual([g.geri_alinabilir, g.geri_al_adi, g.adim, g.yinelenebilir], [true, "Hızlı aks", 1, false]);
  const u = c.geriAl();
  assert.equal(u.basarili, true);
  assert.deepEqual(u.silinen.length, 5);
  assert.equal(JSON.parse(c.metin()).akslar.x.length, 0);
  assert.deepEqual([c.geriAlBilgisi().yinele_adi, c.geriAlBilgisi().yine_adim], ["Hızlı aks", 1]);
  const y = c.yinele();
  assert.equal(y.eklenen.length, 5);
  assert.equal(JSON.parse(c.metin()).akslar.x.length, 3);
  assert.equal(c.geriAl().basarili, true);
  assert.equal(c.geriAl().basarili, false);           // yığın boş
  assert.match(c.geriAl().hata, /Geri alınacak işlem yok/);
});

test("hizliAks: aks–kat şablonunda akslar taşınınca elemanlar değişen raporlanır; sözdizimi biçimi de kabul edilir", () => {
  const c = yeni();
  assert.equal(c.yukle(metinOku("betonarme-tek-aciklik"), "sablon:betonarme-tek-aciklik").basarili, true);
  const r = c.uygula("hizliAks", { x: [6], y: [4], z: [3] });   // A–B aralığı 5 → 6 m
  assert.equal(r.basarili, true, r.hata);
  const turler = new Set(r.degisen.map((k) => k.tur));
  assert.ok(turler.has("cubuk") && turler.has("dugum") && turler.has("aks"));
  assert.equal(JSON.parse(c.metin()).akslar.x[1].konum, 6);
  const r2 = c.uygula("hizliAks", { x: "2@6", y: "1@4", z: "1@3" });
  assert.equal(r2.basarili, true, r2.hata);
  assert.equal(JSON.parse(c.metin()).akslar.x.length, 3);
  assert.match(c.uygula("hizliAks", {}).hata, /x, y .* ve z .* gerekli/);
  const h = c.uygula("hizliAks", { x: [6, -1], y: [4], z: [3] });
  assert.equal(h.basarili, false);
  assert.match(h.hata, /x\[1\] sıfırdan büyük/);
});

test("aksSihirbazi ve baslikDegistir: içerik değişikliği, değişmeyen başlık adım üretmez", () => {
  const c = yeni();
  c.yeniBos();
  const a = { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 8 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 6 }], z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "+4.00", konum: 4, kat: 1 }] };
  const r = c.uygula("aksSihirbazi", { akslar: a });
  assert.equal(r.basarili, true, r.hata);
  assert.equal(JSON.parse(c.metin()).katlar.length, 2);
  const b = c.uygula("baslikDegistir", { baslik: "Depo binası" });
  assert.equal(b.basarili, true);
  assert.equal(b.icerik_degisti, true);
  assert.deepEqual([b.eklenen, b.silinen, b.degisen], [[], [], []]);
  assert.equal(c.sahne().baslik, "Depo binası");
  assert.equal(c.ozet().baslik, "Depo binası");
  const adim = c.geriAlBilgisi().adim;
  const ayni = c.uygula("baslikDegistir", { baslik: "Depo binası" });
  assert.equal(ayni.basarili, true);
  assert.equal(ayni.icerik_degisti, false);
  assert.equal(c.geriAlBilgisi().adim, adim);
  assert.equal(c.uygula("baslikDegistir", { baslik: "  " }).basarili, false);
  assert.equal(c.uygula("aksSihirbazi", {}).basarili, false);
});

test("C1 genel modele geçiş: onaysız gecis_onayi (model değişmez), onaylı dönüşüm; radye temel korunur (docs C11)", () => {
  const c = yeni();
  c.yukle(metinOku("betonarme-4kat-radye"), "sablon:betonarme-4kat-radye");
  const once = c.metin(), sahneOnce = c.sahne();
  const r = c.uygula("genellestir", {});
  assert.equal(r.basarili, true);
  assert.ok(r.gecis_onayi && /genel \(surum 3\)/.test(r.gecis_onayi.metin));
  assert.match(r.gecis_onayi.metin, /^Genel modele dönüştür — /);
  assert.doesNotMatch(r.gecis_onayi.metin, /tekil/);           // C11: genel model motoru radye temeli çözer
  assert.equal(r.icerik_degisti, false);
  assert.equal(c.metin(), once);
  assert.equal(c.geriAlBilgisi().adim, 0);
  const o = c.uygula("genellestir", { onay: true });
  assert.equal(o.basarili, true, o.hata);
  assert.equal(o.gecis_onayi, undefined);
  assert.equal(o.icerik_degisti, true);
  assert.ok(o.uyarilar.some((u) => /genelleştirildi/.test(u)));
  const m = JSON.parse(c.metin());
  assert.equal(m.surum, 3);
  assert.deepEqual([m.kolonlar.length, m.kirisler.length, m.dosemeler.length], [0, 0, 0]);
  assert.equal(m.temeller.tip, "radye");
  // genel görünüm kimlikleri ve sahne dönüşümde korunur: eleman farkı yok, yalnız içerik değişti
  assert.deepEqual([o.eklenen, o.silinen, o.degisen], [[], [], []]);
  assert.equal(c.sahne().cubuklar.no.length, sahneOnce.cubuklar.no.length);
  assert.deepEqual(Array.from(c.sahne().dugumler.xyz), Array.from(sahneOnce.dugumler.xyz));
  assert.equal(c.sahne().temeller.length, sahneOnce.temeller.length);
  assert.ok(c.sahne().temeller.every((t) => t.tur === Op4Ops.KODLAR.temel_turu.radye));
  // genel modelde yeniden çağrı: kapı kapalı, değişiklik yok
  const z = c.uygula("genellestir", {});
  assert.equal(z.gecis_onayi, undefined);
  assert.equal(z.icerik_degisti, false);
  assert.match(z.uyarilar[0], /zaten genel/);
  assert.equal(c.geriAl().basarili, true);
  assert.equal(c.metin(), once);
});

test("geri al sınırları: adım sayısı ve bellek (en az bir adım kalır); yeni işlem yineleme yığınını siler", () => {
  const c = yeni({ geriAlAdim: 3 });
  c.yeniBos();
  for (let i = 1; i <= 5; i++) assert.equal(c.uygula("baslikDegistir", { baslik: "B" + i }).basarili, true);
  assert.equal(c.geriAlBilgisi().adim, 3);
  c.geriAl();
  assert.equal(c.geriAlBilgisi().yine_adim, 1);
  c.uygula("baslikDegistir", { baslik: "Yeni" });
  assert.equal(c.geriAlBilgisi().yine_adim, 0);
  const k = yeni({ geriAlMb: 0.02 });   // ≈ 20 KB: büyük model anlığı tek başına sınırı aşar
  k.yukle(metinOku("celik-sanayi-4hol"), "sablon");
  for (let i = 1; i <= 4; i++) k.uygula("baslikDegistir", { baslik: "S" + i });
  assert.equal(k.geriAlBilgisi().adim, 1);
  assert.equal(yeni().yukle(metinOku("celik-sanayi-4hol"), "s").basarili, true);
});

test("kanonik metin: aynı model → aynı bayt; yükle ↔ metin gidiş-dönüşü; yükleme hataları", () => {
  for (const ad of ["betonarme-3kat-3x3", "celik-cbf-3kat"]) {
    const c = yeni();
    const y = c.yukle(metinOku(ad), "sablon:" + ad);
    assert.equal(y.basarili, true);
    const m1 = c.metin();
    assert.equal(c.metin(), m1);
    const d = yeni();
    d.yukle(m1, "kurtarma");
    assert.equal(d.metin(), m1);
    assert.equal(m1, JSON.stringify(JSON.parse(metinOku(ad))));
  }
  const c = yeni();
  const y1 = c.yukle(metinOku("betonarme-tek-aciklik"), "s");
  assert.equal(y1.surum, 1);
  assert.ok(y1.uyarilar.some((u) => /genel görünümle gösteriliyor/.test(u)));
  assert.equal(c.yukle(JSON.stringify({ ad: "x", bina: JSON.parse(metinOku("celik-1kat-depo")) }), "bina_sablon").basarili, true);
  assert.equal(c.ozet().baslik, JSON.parse(metinOku("celik-1kat-depo")).baslik);
  const once = c.metin();
  assert.equal(c.yukle("{bozuk", "dosya:x").basarili, false);
  assert.equal(c.yukle("[1,2]", "dosya:x").basarili, false);
  const h = c.yukle(JSON.stringify({ tur: "bina", surum: 3, aks_sistemleri: [{ ad: "S", tur: "kartezyen", x: [{ ad: "1", konum: "yok" }] }] }), "dosya:y");
  assert.equal(typeof h.basarili, "boolean");
  if (!h.basarili) assert.equal(c.metin(), once);
});

test("sahne ve öznitelikler aynı model için önbellekte; değişince yenilenir; kodlu biçim", () => {
  const c = yeni();
  c.yukle(metinOku("celik-cbf-3kat"), "s");
  const s = c.sahne(), t = c.oznitelikler(), k = c.oznitelikKodlu();
  assert.equal(c.sahne(), s);
  assert.equal(c.oznitelikler(), t);
  assert.equal(c.oznitelikKodlu(), k);
  assert.equal(k.satir_no.length, t.satirlar.length);
  c.uygula("baslikDegistir", { baslik: "X" });
  assert.notEqual(c.sahne(), s);
  assert.equal(c.sahne().baslik, "X");
});

test("denetle: ModelOps.denetle genel görünümde, eleman uyarıları kimlikli, serbest düğüm sayısı", () => {
  const c = yeni();
  c.yeniBos();
  const m = Op4Ops.bosModel();
  m.dugumler = [{ no: 100001, X: 0, Y: 0, Z: 0 }, { no: 100002, X: 0, Y: 0, Z: 3 }, { no: 100003, X: 5, Y: 0, Z: 3 }];
  m.cubuklar = [{ no: 1, i: { dugum: 100001 }, j: { dugum: 100002 } }, { no: 2, i: { dugum: 100002 }, j: { dugum: 100002 } }];
  c.yukle(JSON.stringify(m), "s");
  const d = c.denetle();
  assert.equal(d.gecerli, false);
  assert.equal(d.serbest_dugum, 3);
  assert.ok(d.uyarilar.some((u) => /sıfır boylu/.test(u)));
  assert.ok(d.eleman_uyarilari.some((e) => e.kimlik.tur === "cubuk" && e.kimlik.no === 2));
  assert.ok(d.eleman_uyarilari.some((e) => e.kimlik.tur === "dugum" && e.kimlik.no === 100003));
  c.yukle(metinOku("celik-1kat-depo"), "s");
  const d2 = c.denetle();
  assert.equal(d2.serbest_dugum, 0);
  assert.equal(typeof d2.gecerli, "boolean");
});

test("sonucEsle cephesi; geçersiz veri", () => {
  const c = yeni();
  c.yukle(metinOku("celik-1kat-depo"), "s");
  const v = JSON.parse(fs.readFileSync(path.join(OP4, "testler", "derlem", "sonuclar", "celik-1kat-depo.json"), "utf8"));
  const r = c.sonucEsle(v);
  assert.equal(r.basarili, true);
  assert.equal(r.elemanlar.length, 13);
  assert.equal(c.sonucEsle(null).basarili, false);
});

test("ifcDisari: zaman sabitken aynı model → aynı bayt; uygulama kimliği op4 / Opus Fortis; çekirdek saati", () => {
  const c = yeni();
  c.yukle(metinOku("celik-1kat-depo"), "s");
  const sec = { uygulama: { ad: "op4", surum: "0.1.0", firma: "Opus Fortis" }, zaman: "2026-10-30T12:00:00" };
  const a = c.ifcDisari(sec, null), b = c.ifcDisari(sec, null);
  assert.equal(a.basarili, true, a.hata);
  assert.equal(a.metin, b.metin);
  assert.match(a.metin, /^ISO-10303-21;/);
  assert.match(a.metin, /FILE_NAME\('[^']*','2026-10-30T12:00:00',\(''\),\(''\),'op4 0\.1\.0','op4',''\);/);
  assert.match(a.metin, /IFCAPPLICATION\(#\d+,'0\.1\.0','op4','op4'\);/);
  assert.match(a.metin, /IFCORGANIZATION\(\$,'Opus Fortis',\$,\$,\$\);/);
  assert.ok(a.metin.indexOf(IFC.stepMetin("Matris Öğren")) < 0, "eski uygulama adı kalmadı");
  assert.ok(a.dosya_adi.endsWith(".ifc"));
  const v = JSON.parse(fs.readFileSync(path.join(OP4, "testler", "derlem", "sonuclar", "celik-1kat-depo.json"), "utf8"));
  const d = c.ifcDisari(Object.assign({ dc: true }, sec), v);
  assert.equal(d.basarili, true, d.hata);
  // zaman verilmezse çekirdek saati (sınamada deterministik)
  const z = c.ifcDisari({}, null);
  assert.match(z.metin, /'2026-01-02T03:04:05'/);
  assert.match(z.metin, new RegExp(IFC.stepMetin("Matris Öğren").replace(/\\/g, "\\\\")));   // uygulama verilmezse docs/ davranışı
});

test("tabloUygula: kesit tablosu değişikliği tek adım; o kesiti kullanan çubuklar değişen", () => {
  const c = yeni();
  c.yukle(metinOku("celik-cbf-3kat"), "s");
  const r = c.tabloUygula([{ yol: ["kesitler", "KOLON", "profil"], deger: "HEB 300" }]);
  assert.equal(r.basarili, true, r.hata);
  assert.equal(r.icerik_degisti, true);
  const kolonlar = JSON.parse(c.metin()).cubuklar.filter((x) => x.kesit === "KOLON").map((x) => x.no);
  assert.deepEqual(r.degisen.filter((k) => k.tur === "cubuk").map((k) => k.no), kolonlar);
  assert.equal(c.geriAlBilgisi().geri_al_adi, "Tablo düzenleme");
  assert.equal(c.tabloUygula("x").basarili, false);
  assert.equal(c.tabloUygula([{ yol: ["kesitler", "KOLON", "profil"], deger: "HEB 300" }]).icerik_degisti, false);
});

test("hata kuralı: bilinmeyen işlem ve girdi hatası rapor; başka istisna fırlatılır", () => {
  const c = yeni();
  c.yeniBos();
  const r = c.uygula("yokBoyleIslem", {});
  assert.equal(r.basarili, false);
  assert.match(r.hata, /Bilinmeyen işlem/);
  const BC = require(path.join(DOCS, "bina_cizim.js"));
  const bozuk = Object.assign({}, BC, { aksSihirbazUygula: () => { throw new TypeError("iç bozukluk"); } });
  const k = Op4Cekirdek.olustur({ Op4Ops, MatrisBinaCizim: bozuk });
  k.yeniBos();
  assert.throws(() => k.uygula("hizliAks", { x: [6], y: [6], z: [3] }), /iç bozukluk/);
  assert.equal(k.geriAlBilgisi().adim, 0);
});
