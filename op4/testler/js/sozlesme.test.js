// op4 JS sözleşme sınamaları (S26, S27): op4_ops.js ve op4_cekirdek.js dışa aktarımları, kod tabloları, öznitelik
// kimlikleri, taslak dönüş biçimleri. Sahibi: sözleşme; B gövdeleri doldurdukça kendi sınamalarını ayrı dosyalara yazar.
// Çalıştırma: node --test op4/testler/js/*.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const OP4 = path.join(__dirname, "..", "..");
const Op4Ops = require(path.join(OP4, "js", "op4_ops.js"));
const Op4Cekirdek = require(path.join(OP4, "js", "op4_cekirdek.js"));
const oku = (g) => JSON.parse(fs.readFileSync(path.join(OP4, g), "utf8"));

test("op4_ops dışa aktarımları (sözleşme S26)", () => {
  for (const ad of ["bosModel", "katUyeligi", "kullanimYeri", "profilAdiNormal", "oznitelikCikar", "sahneCikar", "sonucEsle"])
    assert.equal(typeof Op4Ops[ad], "function", ad);
  assert.ok(Op4Ops.Op4Hatasi.prototype instanceof Error);
  for (const ad of Op4Ops.TASLAK) assert.equal(typeof Op4Ops[ad], "function", ad);
});

test("KODLAR op4/veri/sahne_kodlari.json ile birebir", () => {
  const j = oku("veri/sahne_kodlari.json");
  for (const [tablo, deger] of Object.entries(Op4Ops.KODLAR)) assert.deepEqual(deger, j[tablo], tablo);
  for (const tablo of Object.keys(j)) if (!["bicim", "aciklama"].includes(tablo)) assert.ok(tablo in Op4Ops.KODLAR, tablo);
});

test("OZNITELIK_IDLERI op4/veri/oznitelikler.json Faz 1 kimlikleriyle aynı", () => {
  const ids = oku("veri/oznitelikler.json").oznitelikler.filter((o) => o.faz === 1).map((o) => o.id);
  assert.deepEqual([...Op4Ops.OZNITELIK_IDLERI].sort(), [...ids].sort());
});

test("bosModel MIMARI §13.4 biçiminde ve her çağrıda yeni nesne", () => {
  const m = Op4Ops.bosModel();
  assert.equal(m.tur, "bina");
  assert.equal(m.surum, 3);
  assert.equal(m.baslik, "Adsız 1");
  assert.deepEqual(m.akslar.z, [{ ad: "±0.00", konum: 0, kat: 0 }]);
  assert.deepEqual(m.katlar, [{ no: 0, ad: "±0.00", kot: 0 }]);
  assert.deepEqual(Object.keys(m.malzemeler), ["C30", "B420C", "S275", "S355"]);
  for (const k of ["dugumler", "cubuklar", "paneller", "mesnetler", "ek_yukler", "uretecler"]) assert.deepEqual(m[k], [], k);
  assert.equal(m.deprem.etkin, false);
  assert.equal(m.temeller.tip, "tekil");
  assert.equal(Op4Ops.bosModel({ baslik: "Adsız 2" }).baslik, "Adsız 2");
  m.cubuklar.push(1);
  assert.deepEqual(Op4Ops.bosModel().cubuklar, []);
});

test("taslak dönüş biçimleri C++ köprüsünün beklediği alanları taşır", () => {
  const m = Op4Ops.bosModel();
  const k = Op4Ops.katUyeligi(m);
  for (const a of ["seviyeler", "dugum", "cubuk", "panel", "seviye"]) assert.ok(a in k, a);
  const u = Op4Ops.kullanimYeri(m);
  for (const a of ["cubuk", "panel", "dugum"]) assert.ok(a in u, a);
  const p = Op4Ops.profilAdiNormal("HE340A");
  for (const a of ["ad", "aile", "durum"]) assert.ok(a in p, a);
  assert.ok(["tamam", "kutuphanede_yok", "anlasilmadi"].includes(p.durum));
  const o = Op4Ops.oznitelikCikar(m);
  assert.ok(Array.isArray(o.satirlar) && Array.isArray(o.sutunlar));
  for (const s of o.sutunlar) assert.equal(s.degerler.length, o.satirlar.length, s.id);
  const s = Op4Ops.sahneCikar(m, 7);
  assert.equal(s.sahne_surumu, 7);
  assert.ok(s.dugumler.xyz instanceof Float64Array);
  assert.ok(s.cubuklar.i instanceof Uint32Array);
  assert.ok(s.cubuklar.serbestlik instanceof Uint16Array);
  assert.ok(s.paneller.kose_bas instanceof Uint32Array);
  assert.equal(s.cubuklar.y_yerel.length, 3 * s.cubuklar.no.length);
  assert.equal(s.dugumler.xyz.length, 3 * s.dugumler.no.length);
  const e = Op4Ops.sonucEsle(m, {});
  assert.ok(Array.isArray(e.elemanlar) && Array.isArray(e.uyarilar));
});

test("profil_adlari.json vektörleri biçimce geçerli (B doldurunca profilAdiNormal bunları geçmeli)", () => {
  const v = oku("testler/ortak/profil_adlari.json").vektorler;
  assert.ok(v.length >= 12);
  for (const x of v) {
    assert.ok(typeof x.girdi === "string");
    assert.ok(["tamam", "kutuphanede_yok", "anlasilmadi"].includes(x.durum));
    if (!Op4Ops.TASLAK.includes("profilAdiNormal")) {
      const r = Op4Ops.profilAdiNormal(x.girdi);
      assert.equal(r.ad, x.ad, x.girdi);
      assert.equal(r.durum, x.durum, x.girdi);
    }
  }
});

test("op4_cekirdek cephesi (sözleşme S27): yöntemler, beyaz liste, temel akış", () => {
  assert.equal(typeof Op4Cekirdek.olustur, "function");
  assert.deepEqual([...Op4Cekirdek.ISLEMLER], ["hizliAks", "aksSihirbazi", "baslikDegistir", "genellestir"]);
  const c = Op4Cekirdek.olustur({ Op4Ops });
  for (const ad of ["yeniBos", "yukle", "uygula", "geriAl", "yinele", "geriAlBilgisi", "islemler", "sahne", "oznitelikler",
    "sahneSurumu", "ozet", "denetle", "metin", "sonucEsle", "ifcDisari", "tabloUygula"])
    assert.equal(typeof c[ad], "function", ad);
  const y = c.yeniBos();
  assert.equal(y.basarili, true);
  assert.equal(y.ozet.baslik, "Adsız 1");
  assert.equal(y.ozet.bos, true);
  const metin = c.metin();
  assert.equal(JSON.parse(metin).tur, "bina");
  assert.equal(c.metin(), metin, "kanonik metin kararlı");
  const s0 = c.sahneSurumu();
  assert.equal(c.yukle(metin, "sinama").basarili, true);
  assert.ok(c.sahneSurumu() > s0);
  assert.equal(c.yukle("{bozuk", "sinama").basarili, false);
  assert.equal(c.yukle('{"tur":"matris"}', "sinama").basarili, false);
  const r = c.uygula("yokBoyleIslem", {});
  assert.equal(r.basarili, false);
  assert.match(r.hata, /Bilinmeyen işlem/);
  for (const a of ["islem", "basarili", "uyarilar", "eklenen", "silinen", "degisen", "sahne_surumu"]) assert.ok(a in r, a);
  const g = c.geriAlBilgisi();
  for (const a of ["geri_alinabilir", "yinelenebilir", "geri_al_adi", "yinele_adi", "adim", "yine_adim"]) assert.ok(a in g, a);
  for (const a of ["gecerli", "uyarilar", "eleman_uyarilari", "serbest_dugum"]) assert.ok(a in c.denetle(), a);
});

test("komutlar.json: B'nin komutları ve beyaz liste tutarlı", () => {
  const k = oku("veri/komutlar.json").komutlar;
  const b = k.filter((x) => x.sahip === "B").map((x) => x.id).sort();
  assert.deepEqual(b, ["duzenle.geri_al", "duzenle.yinele", "model.denetle"]);
});
