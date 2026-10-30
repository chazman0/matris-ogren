/* docs/eleman_bilgi.js birim testleri (saf model: sekmeler, türetilen değerler, süperpozisyon, sehim, metraj, yük yolu, menü, TSV).
   Çalıştırma: node --test testler/js/eleman_bilgi.test.js
   MATRIS_BILGI_FIXTURE ortam değişkeni (yol listesi, ":" ayraçlı) verilirse gerçek çözümlü binalarla (yapi.bina_coz) karşılaştırma da yapılır
   — pytest sarmalayıcısı (testler/test_arac_bilgi_olcum_js.py) bu dosyaları üretir. */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const B = require(path.join(__dirname, "..", "..", "docs", "eleman_bilgi.js"));

function yakin(a, b, tol, m) { assert.ok(Math.abs(a - b) <= (tol == null ? 1e-9 : tol), (m || "") + ` beklenen ${b}, bulunan ${a}`); }
function sekme(m, id) { return m.sekmeler.find(function (s) { return s.id === id; }); }
function metin(m, id) { return B.tsv(m, id); }

/** Elle kurulmuş küçük çözüm: A–B (0, 5) × 1, katlar 0/3; kolon 1–2 (S30x30), kiriş 1 (K25x50, w_G = 10, w_Q = 4 kN/m basit kiriş momenti). */
function mini() {
  const L = 5, xs = [], MG = [], MQ = [], VG = [], VQ = [];
  for (let i = 0; i <= 10; i++) { const x = i * L / 10; xs.push(x); MG.push(10 * x * (L - x) / 2); MQ.push(4 * x * (L - x) / 2); VG.push(10 * (L / 2 - x)); VQ.push(4 * (L / 2 - x)); }
  const sifir = xs.map(function () { return 0; });
  const kiris = function (M, V, w) { return { no: 3, x: xs.slice(), N: sifir.slice(), V: V, M: M, Vz: sifir.slice(), My: sifir.slice(), T: sifir.slice(),
    uc_kuvvetleri: [0, w * L / 2, 0, 0, 0, 0, 0, w * L / 2, 0, 0, 0, 0] }; };
  const kolon = function (no, Nv) { return { no: no, x: [0, 1.5, 3], N: [Nv, Nv, Nv], V: [0, 0, 0], M: [0, 0, 0], Vz: [0, 0, 0], My: [0, 0, 0], T: [0, 0, 0], uc_kuvvetleri: [Nv, 0, 0, 0, 0, 0, -Nv, 0, 0, 0, 0, 0] }; };
  const durum = function (w) {
    return {
      elemanlar: [kolon(1, -w * L / 2), kolon(2, -w * L / 2), kiris(w === 10 ? MG : MQ, w === 10 ? VG : VQ, w)],
      dugumler: [{ no: 1, uX: 0, uY: 0, uZ: 0, rX: 0, rY: 0, rZ: 0 }, { no: 1001, uX: 0.001 * w, uY: 0, uZ: -0.0001 * w, rX: 0, rY: 0.0002 * w, rZ: 0 }],
      tepkiler: [{ dugum: 1, FX: 0, FY: 0, FZ: w * L / 2, MX: 0, MY: 0, MZ: 0 }, { dugum: 21, FX: 0, FY: 0, FZ: w * L / 2, MX: 0, MY: 0, MZ: 0 }],
    };
  };
  const bina = {
    tur: "bina", surum: 1,
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 5 }], y: [{ ad: "1", konum: 0 }, { ad: "2", konum: 4 }] },
    katlar: [{ no: 0, ad: "Temel", kot: 0 }, { no: 1, ad: "1. kat", kot: 3 }],
    malzemeler: { C30: { kutuphane: "C30/37" }, B420C: { kutuphane: "B420C" } },
    kesitler: { S30x30: { tip: "dikdortgen", b: 0.3, h: 0.3, malzeme: "C30", donati: "B420C", pas: 0.03 },
      K25x50: { tip: "dikdortgen", b: 0.25, h: 0.5, malzeme: "C30", donati: "B420C", pas: 0.03 } },
    kolonlar: [{ no: 1, aks: ["A", "1"], kat: 1, kesit: "S30x30", yon: "x" }, { no: 2, aks: ["B", "1"], kat: 1, kesit: "S30x30", yon: "y" }],
    kirisler: [{ no: 1, kat: 1, bas: ["A", "1"], son: ["B", "1"], kesit: "K25x50" }],
    dosemeler: [{ no: 1, kat: 1, kose: [["A", "1"], ["B", "2"]], h: 0.14, kullanim: "konut" }],
    ek_yukler: [{ tur: "kiris", kiris: 1, durum: "G", q: 2 }, { tur: "dugum", aks: ["A", "1"], kat: 1, durum: "Q", FZ: -10 }],
    temeller: { tip: "tekil", mesnet: "ankastre", zemin: { q_em: 200, k0: 20000 }, varsayilan: { B: 1.5, L: 1.5, h: 0.5 } },
  };
  const veri = {
    tur: "bina", gosterilecek: ["1.4G+1.6Q"],
    bina: { kolonlar: [{ no: 1, aks: ["A", "1"], kat: 1, kesit: "S30x30", yon: "x", bX: 0.3, bY: 0.3, L: 3, A: 0.09, malzeme: "C30", adres: "S-A1/k1" },
      { no: 2, aks: ["B", "1"], kat: 1, kesit: "S30x30", yon: "y", bX: 0.3, bY: 0.3, L: 3, A: 0.09, malzeme: "C30", adres: "S-B1/k1" }],
      kirisler: [{ no: 1, kat: 1, bas: ["A", "1"], son: ["B", "1"], kesit: "K25x50", b: 0.25, h: 0.5, L: 5, A: 0.125, malzeme: "C30", adres: "K-A1→B1/k1" }],
      dosemeler: [{ no: 1, kat: 1, kose: [["A", "1"], ["B", "2"]], h: 0.14, adres: "D-A1/B2/k1" }],
      temeller: { tip: "tekil", mesnet: "ankastre", zemin: { q_em: 200, k0: 20000 }, varsayilan: { B: 1.5, L: 1.5, h: 0.5 }, liste: [{ kolon_no: 1, aks: ["A", "1"], B: 1.5, L: 1.5 }] } },
    kutuphane_ozeti: { malzemeler: { C30: { E_kNm2: 32e6, G_kNm2: 12.8e6, gamma: 25, tur: "beton", kutuphane: "C30/37", fck: 30 }, B420C: { E_kNm2: 2e8, gamma: 78.5, tur: "donati", kutuphane: "B420C", fyk: 420 } },
      kesitler: { K25x50: { tip: "dikdortgen", b: 0.25, h: 0.5, A: 0.125, Iy: 0.25 * 0.125 / 12, Iz: 0.5 * 0.015625 / 12, J: 0.001788126628, Wpl: 0.015625, malzeme: "C30" } } },
    ag: {
      dugumler: [{ no: 1, X: 0, Y: 0, Z: 0, adres: "A1/k0", kat: 0, aks: ["A", "1"] }, { no: 21, X: 5, Y: 0, Z: 0, adres: "B1/k0", kat: 0, aks: ["B", "1"] },
        { no: 1001, X: 0, Y: 0, Z: 3, adres: "A1/k1", kat: 1, aks: ["A", "1"] }, { no: 1021, X: 5, Y: 0, Z: 3, adres: "B1/k1", kat: 1, aks: ["B", "1"] }],
      elemanlar: [{ no: 1, dugumler: [1, 1001], tur: "kolon", kaynak_no: 1, parca: 1, kat: 1, L: 3, kesit: "S30x30", adres: "S-A1/k1" },
        { no: 2, dugumler: [21, 1021], tur: "kolon", kaynak_no: 2, parca: 1, kat: 1, L: 3, kesit: "S30x30", adres: "S-B1/k1" },
        { no: 3, dugumler: [1001, 1021], tur: "kiris", kaynak_no: 1, parca: 1, kat: 1, L: 5, kesit: "K25x50", lam: [[1, 0, 0], [0, 0, 1], [0, -1, 0]], adres: "K-A1→B1/k1 (A1→B1)" }],
      mesnetler: [{ dugum: 1, tip: "ankastre" }, { dugum: 21, tip: "ankastre" }],
    },
    durumlar: { G: durum(10), Q: durum(4) },
    kombinasyonlar: [{ ad: "1.4G+1.6Q", katsayilar: { G: 1.4, Q: 1.6 }, tur: "dayanim", uygulandi: true }, { ad: "G+Q", katsayilar: { G: 1, Q: 1 }, tur: "servis", uygulandi: true },
      { ad: "G+Q+E", katsayilar: { G: 1, Q: 1, E: 1 }, uygulandi: false }],
    sonuclar: {},
    zarf: { elemanlar: [{ no: 3, N_max: 0, N_min: 0, V_max: 41, V_min: -41, M_max: 51.25, M_min: 0, Vz_max: 0, Vz_min: 0, My_max: 0, My_min: 0, T_max: 0, T_min: 0,
      belirleyen: { M_max: "1.4G+1.6Q", M_min: "G+Q" } }] },
    yukler: { kirisler: [{ no: 1, kat: 1, L: 5, G: { doseme: 30, duvar: 0, oz: 15.625, ek: 10, toplam_kN: 55.625 }, Q: { doseme: 20, ek: 0, toplam_kN: 20 } }],
      kolonlar: [{ no: 1, oz_kN: 6.75 }],
      dosemeler: [{ no: 1, kat: 1, lx: 4, ly: 5, m: 1.25, tip: "cift", g: 5, q: 2, g_plak: 3.5, g_ek: 1.5, alan: 20, G_toplam: 100, Q_toplam: 40,
        paylar: [{ kiris_no: 1, kenar_ad: "alt", kenar: "uzun", sekil: "trapez", tepe_g: 10, tepe_q: 4, toplam_G: 30, toplam_Q: 12 },
          { kiris_no: 9, kenar_ad: "ust", kenar: "uzun", sekil: "trapez", tepe_g: 10, tepe_q: 4, toplam_G: 70, toplam_Q: 28 }] }] },
    akis: { sankey: [{ kaynak: "D1", hedef: "K1", durum: "G", kN: 30 }, { kaynak: "D1", hedef: "K1", durum: "Q", kN: 12 },
      { kaynak: "K1", hedef: "S1/k1", durum: "G", kN: 27.8125 }, { kaynak: "K1", hedef: "S2/k1", durum: "G", kN: 27.8125 }, { kaynak: "S1/k1", hedef: "T-A1", durum: "G", kN: 34.56 }],
      temeller: [{ kolon_no: 1, aks: ["A", "1"], B: 1.5, L: 1.5, h: 0.5, N_G: 34.56, N_Q: 10, N_temel: 28.125, N_servis: 72.685, MX: 1, MY: -2, sigma_max: 35, sigma_min: 29.6,
        e_X: 0.01, e_Y: 0.02, q_em: 200, DC: 0.175, cekirdek_icinde: true }] },
    tasarim: { yontem: { betonarme: "TS 500:2000" }, elemanlar: [{ no: 1, tur: "kiris", sistem: "betonarme", dc: 0.52, durum: "yeterli", belirleyen: { kontrol: "eğilme", kombinasyon: "1.4G+1.6Q" },
      kontroller: [{ ad: "Eğilme Md ≤ Mr", talep: 50, kapasite: 96, birim: "kN·m", dc: 0.52, saglandi: true, kombinasyon: "1.4G+1.6Q", kaynak: "TS 500 md. 7.1" },
        { ad: "Kesme", talep: 41, kapasite: 30, birim: "kN", dc: 1.37, saglandi: false, kombinasyon: "1.4G+1.6Q", kaynak: "TS 500 md. 8.1" }],
      ozet: { As_ust_cm2: 3, As_alt_cm2: 2, oneri_ust: "2Φ14", etriye: "Φ8/20", karmasik: { a: 1 } } }] },
  };
  return { bina: bina, veri: veri };
}

test("kiriş: sekmeler, aks adresi, geometri, kesit (dikdörtgen formülü), malzeme", function () {
  const d = mini();
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  assert.equal(m.baslik, "Kiriş 1");
  assert.equal(m.adres, "K-A1→B1/k1");
  assert.deepEqual(m.sekmeler.map(function (s) { return s.id; }), ["geometri", "kesit", "baglanti", "yukler", "ic", "yer", "tasarim", "metraj", "yol"]);
  yakin(m.ham.L, 5);
  const g = metin(m, "geometri");
  assert.match(g, /Aks adresi\tA-1 \/ 1\. kat → B-1 \/ 1\. kat/);
  assert.match(g, /x′ \(eleman ekseni\)\t\(1,000; 0,000; 0,000\)/);
  assert.match(g, /i ucunda\tKolon 1/);
  const k = metin(m, "kesit");
  assert.match(k, /Alan A\t1250\tcm²/);
  assert.match(k, /Burulma sabiti J\t178813\tcm⁴/);
  assert.match(k, /f_ck\t30\tMPa/);
  assert.match(k, /Paspayı\t30\tmm/);
  assert.match(m.alt, /K25x50 · L 5,00 m · D\/C 0,52/);
});

test("iç kuvvetler: kombinasyon süperpozisyonla (1.4G + 1.6Q), uç kuvvetleri, ekstremumlar ve yerleri", function () {
  const d = mini();
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  assert.equal(m.durum, "1.4G+1.6Q");
  assert.deepEqual(m.durumlar.map(function (x) { return x.ad; }), ["G", "Q", "1.4G+1.6Q", "G+Q", "Zarf"]);
  const w = 1.4 * 10 + 1.6 * 4;
  yakin(m.ham.ext.M.max, w * 25 / 8, 1e-9); yakin(m.ham.ext.M.xmax, 2.5);
  yakin(m.ham.ext.V.max, w * 2.5, 1e-9); yakin(m.ham.ext.V.xmin, 5);
  const ic = sekme(m, "ic");
  assert.ok(ic.bolumler.some(function (b) { return b.svg && /bilgi-diyagram/.test(b.svg); }));
  assert.match(metin(m, "ic"), /süperpozisyon/);
  assert.match(metin(m, "ic"), /Vy \(kN\)\t51,00\t51,00/);
  const q = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri, { durum: "Q" });
  yakin(q.ham.ext.M.max, 4 * 25 / 8, 1e-9);
  const z = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri, { durum: "Zarf" });
  yakin(z.ham.zarf.M.max, 51.25); assert.equal(z.ham.zarf.M.bmax, "1.4G+1.6Q");
  assert.match(metin(z, "ic"), /Zarf diyagramları/);
  const yok = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri, { durum: "olmayan" });
  assert.equal(yok.durum, "1.4G+1.6Q");
});

test("yer değiştirme: uç düğümleri, açıklık içi bağıl sehim = 5wL⁴/384EI (%1)", function () {
  const d = mini();
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri, { durum: "G" });
  const EI = 32e6 * 0.25 * 0.125 / 12;
  yakin(Math.abs(m.ham.sehim.guclu), 5 * 10 * 625 / (384 * EI), 0.01 * 5 * 10 * 625 / (384 * EI));
  yakin(m.ham.sehim.x, 2.5);
  const t = metin(m, "yer");
  assert.match(t, /i \(1001\)\t10,000\t0,000\t-1,000/);
  assert.match(t, /L\/δ\t\d+/);
  // doğrudan: düzgün yayılı basit kiriş
  const xs = [], Ms = [];
  for (let i = 0; i <= 20; i++) { const x = i * 0.3; xs.push(x); Ms.push(x * (6 - x) / 2); }
  yakin(B.bagilSehim(xs, Ms, 1).delta, -5 * 1296 / 384, 0.003 * 5 * 1296 / 384);
  assert.equal(B.bagilSehim([0], [0], 1), null);
  assert.equal(B.bagilSehim(xs, Ms, 0), null);
});

test("tasarım, metraj ve yük yolu", function () {
  const d = mini();
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  yakin(m.ham.dc, 0.52);
  const t = sekme(m, "tasarim");
  const kon = t.bolumler.find(function (b) { return b.kontroller; }).kontroller;
  assert.equal(kon.length, 2); assert.equal(kon[1].saglandi, false);
  assert.match(metin(m, "tasarim"), /Kesme\t41,00\t30,00\tkN\t1,370\thayır/);
  assert.match(metin(m, "tasarim"), /Üst donatı önerisi\t2Φ14/);
  assert.ok(metin(m, "tasarim").indexOf("karmasik") < 0);
  const me = m.ham.metraj;
  yakin(me.beton_m3, 0.625); yakin(me.kalip_m2, 6.25); yakin(me.boyuna_kg, 5e-4 * 5 * 7850);
  const etriye = 26 * (2 * ((0.25 - 0.06) + (0.5 - 0.06)) + 0.16) * Math.PI * 0.008 * 0.008 / 4 * 7850;
  yakin(me.etriye_kg, etriye, 1e-9);
  assert.deepEqual(m.ham.yol, { gelenG: 30, gelenQ: 12, gidenG: 55.625, gidenQ: 0 });
  assert.match(metin(m, "yol"), /← gelen\tDöşeme 1\t30,00\t12,00/);
  assert.match(metin(m, "yol"), /→ giden\tKolon 1 \(kat 1\)\t27,81/);
  assert.match(metin(m, "yukler"), /Döşemeden\t30,00\t20,00/);
  assert.match(metin(m, "yukler"), /D1\talt \(uzun\)\ttrapez\t10,00\t4,00\t30,00\t12,00/);
  assert.match(metin(m, "yukler"), /Tanımlı ek yükler/);
});

test("kolon, düğüm, mesnet, döşeme, temel modelleri", function () {
  const d = mini();
  const k = B.bilgi({ tur: "kolon", no: 2 }, d.bina, d.veri);
  assert.match(metin(k, "geometri"), /Yerel eksen açısı \(aci\)\t90,0/);   // yon "y"
  assert.match(metin(k, "baglanti"), /i ucunda mesnet\tankastre/);
  assert.match(metin(k, "kesit"), /Boyutlar bX × bY\t30 × 30\tcm/);
  const t = B.bilgi({ tur: "temel", no: 1 }, d.bina, d.veri);
  assert.equal(t.baslik, "Temel A1");
  yakin(t.ham.dc, 0.175); yakin(t.ham.metraj.beton_m3, 1.125);
  assert.match(metin(t, "yol"), /← gelen\tKolon 1 \(kat 1\)\t34,56/);
  const ms = B.bilgi({ tur: "mesnet", no: 1 }, d.bina, d.veri);
  assert.equal(ms.sekmeler[1].id, "tepki");
  yakin(ms.ham.tepki["1.4G+1.6Q"].FZ, 1.4 * 25 + 1.6 * 10, 1e-9);
  const dg = B.bilgi({ tur: "dugum", no: 1001 }, d.bina, d.veri);
  assert.equal(dg.baslik, "Düğüm 1001");
  assert.equal(dg.adres, "A-1 / 1. kat");
  assert.match(metin(dg, "yukler"), /Q\t0,00\t0,00\t−10,00|Q\t0,00\t0,00\t-10,00/);
  assert.match(metin(dg, "yer"), /G\t10,000\t0,000\t-1,000/);
  const ds = B.bilgi({ tur: "doseme", no: 1 }, d.bina, d.veri);
  yakin(ds.ham.alan, 20); yakin(ds.ham.metraj.beton_m3, 2.8);
  yakin(ds.ham.paylarG, 100);   // paylar toplamı = G_toplam (korunum)
  assert.match(metin(ds, "geometri"), /Köşe aksları\tA1 – B2 \/ kat 1/);
  assert.throws(function () { B.bilgi({ tur: "kiris", no: 99 }, d.bina, d.veri); }, /modelde yok/);
  assert.throws(function () { B.bilgi({ tur: "garip", no: 1 }, d.bina, d.veri); }, /bilinmeyen tür/);
});

test("çözüm yoksa: geometri ve kesit bina JSON'dan, analiz sekmeleri \"Önce çözün\"", function () {
  const d = mini();
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, null);
  assert.equal(m.cozumVar, false);
  ["ic", "yer", "tasarim", "yol"].forEach(function (id) { assert.match(metin(m, id), /Önce çözün/, id); });
  assert.match(metin(m, "kesit"), /b, h ile formülden/);
  assert.match(metin(m, "kesit"), /E\t31801\tMPa/);   // 3250√30 + 14000
  yakin(m.ham.L, 5);
  const eski = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri, { eski: true });
  assert.match(eski.uyari, /son hâline ait değil/);
});

test("§19 aks sistemi: çapraz ve bölme düğümünün aks adresi (çözümsüz)", function () {
  const bina = {
    tur: "bina", surum: 3,
    akslar: { x: [{ ad: "A", konum: 0 }, { ad: "B", konum: 6 }, { ad: "C", konum: 12 }], y: [{ ad: "1", konum: 0 }],
      z: [{ ad: "±0.00", konum: 0, kat: 0 }, { ad: "Saçak", konum: 6, kat: 1 }, { ad: "Mahya", konum: 7.5 }] },
    kesitler: { IPE300: { tip: "profil", profil: "IPE 300", malzeme: "S275" } }, malzemeler: { S275: { kutuphane: "S275" } },
    dugumler: [{ no: 100001, tur: "bolme", cubuk_i: { aks: ["A", "1"], z: "Saçak" }, cubuk_j: { aks: ["C", "1"], z: "Saçak" }, oran: 0.5 }],
    cubuklar: [{ no: 12, i: { aks: ["A", "1"], z: "Saçak" }, j: { aks: ["C", "1"], z: "Saçak" }, tur: "kiris", kesit: "IPE300" },
      { no: 5, i: { aks: ["A", "1"], kat: 0 }, j: { aks: ["B", "1"], z: "Saçak" }, tur: "capraz", kesit: "IPE300", serbest: { i: ["My", "Mz"], j: ["My", "Mz"] }, yalniz_cekme: true },
      { no: 6, i: { dugum: 100001 }, j: { aks: ["B", "1"], z: "Mahya" }, tur: "makas-dikme", kesit: "IPE300" }],
  };
  const m = B.bilgi({ tur: "cubuk", no: 5 }, bina, null);
  assert.equal(m.baslik, "Çapraz 5");
  assert.equal(m.adres, "A-1 / ±0.00 → B-1 / Saçak");
  yakin(m.ham.L, Math.sqrt(72), 1e-9); yakin(m.ham.egim, 45, 1e-9);
  assert.match(metin(m, "baglanti"), /i ucu\tMy, Mz serbest/);
  assert.match(metin(m, "baglanti"), /Yalnız çekme\tevet/);
  assert.match(metin(m, "kesit"), /F_y\t275\tMPa/);
  const d = B.bilgi({ tur: "dugum", no: 100001 }, bina, null);
  assert.equal(d.adres, "bölme: çubuk 12, t=0,5");
  assert.match(metin(d, "geometri"), /Bölme oranı t\t0,500/);
  assert.match(metin(d, "geometri"), /Makas dikmesi 6/);
  const k6 = B.bilgi({ tur: "cubuk", no: 6 }, bina, null);
  assert.equal(k6.adres, "bölme: çubuk 12, t=0,5 → B-1 / Mahya");
});

test("menü öğeleri: türe uygun, bağlanmayanlar soluk, ayraçlar düzgün", function () {
  const l = B.menuOgeleri("kolon", { bol: function () {}, sil: { calistir: function () {}, etkin: false }, ozellikler: { calistir: function () {}, etkin: function () { return true; } } });
  const ad = function (id) { return l.find(function (o) { return o.id === id; }); };
  assert.equal(ad("bilgi").etkin, true);
  assert.equal(ad("bol").etkin, true);
  assert.equal(ad("ozellikler").etkin, true);
  assert.equal(ad("birlestir").etkin, false);
  assert.equal(ad("sil").etkin, false); assert.equal(ad("sil").tehlike, true);
  const d = B.menuOgeleri("dugum", {});
  assert.equal(d.some(function (o) { return o.id === "bol" || o.id === "tasarim"; }), false);
  [l, d, B.menuOgeleri("temel", {})].forEach(function (x) {
    assert.ok(!x[0].ayrac && !x[x.length - 1].ayrac);
    x.forEach(function (o, i) { if (o.ayrac) assert.ok(!x[i + 1].ayrac); });
  });
  assert.deepEqual(B.menuOgeleri("kiris").filter(function (o) { return !o.ayrac; }).map(function (o) { return o.ad; }),
    ["Bilgi", "Özellikler…", "Böl…", "Birleştir", "Mafsal…", "Kesit öner ve uygula", "Isı haritasında incele", "Yük akışını göster", "Tasarım ayrıntısı", "Gizle", "Yalıt", "Sil"]);
});

test("köprü paketi: 'Motor ayrıntısı' sekmeye eklenir, yeni sekme açılır, yer tutucu kalkar", function () {
  const d = mini();
  const paket = { sekmeler: { yol: [{ baslik: "Adım 1", satirlar: [["Döşeme 1", "30", "kN"]] }], ozel: [{ not: "ek" }] }, sekme_adlari: { ozel: "Özel" }, uyarilar: ["Yaklaşık."] };
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, null, { paket: paket });
  const yol = sekme(m, "yol");
  assert.equal(yol.bolumler.some(function (b) { return b.cozum; }), false);
  assert.equal(yol.bolumler[0].baslik, "Motor ayrıntısı — Adım 1");
  assert.equal(sekme(m, "ozel").ad, "Özel");
  assert.match(m.uyari, /Yaklaşık/);
  assert.equal(m.paket, true);
});

test("TSV ve SVG: tanımsız/NaN yok, kaçışlı, sekmeli", function () {
  const d = mini();
  ["kiris", "kolon", "doseme", "temel", "dugum", "mesnet"].forEach(function (tur) {
    const m = B.bilgi({ tur: tur, no: tur === "dugum" || tur === "mesnet" ? 1 : 1 }, d.bina, d.veri);
    const t = B.tsv(m);
    assert.ok(!/undefined|NaN|\[object/.test(t), tur);
    assert.equal(t.split("\n")[0].split("\t")[0], m.baslik);
    m.sekmeler.forEach(function (s) { s.bolumler.forEach(function (b) { assert.ok(!/undefined|NaN/.test(B.bolumHtml(b)), tur + "/" + s.id); }); });
  });
  const s = B.diyagramSvg([0, 1, 2], [0, 5, -3], "M");
  assert.match(s, /role="img"/); assert.match(s, /bilgi-dM/); assert.match(s, />5,0</); assert.match(s, />−3,0</);
  assert.match(B.bolumHtml({ baslik: "<x>", satirlar: [["a", "<b>", "m"]] }), /&lt;x&gt;.*&lt;b&gt;/);
  assert.equal(B.bicim(-0.004, 2), "0,00"); assert.equal(B.bicim(-2.25, 1), "−2,3");
});

test("bileşenler: dikdörtgen kesit (J), malzeme adından, süperpozisyon önbelleği, durum listesi", function () {
  const k = B.dikdortgenOzellik(0.25, 0.5);
  yakin(k.J, 0.001788126628, 1e-12); yakin(k.Iguclu, 0.25 * 0.125 / 12); yakin(k.Wpl, 0.25 * 0.25 / 4);
  const ml = B.malzemeOzellik({ kut: {}, bina: { malzemeler: { x: { kutuphane: "C25/30" } } } }, "x");
  yakin(ml.E, 3250 * 5 + 14000); assert.equal(ml.fck, 25);
  const d = mini();
  const a = B.kisa(d.veri, "G+Q"), b = B.kisa(d.veri, "G+Q");
  assert.equal(a, b);
  assert.equal(B.kisa(d.veri, "G+Q+E"), null);
  assert.equal(Object.keys(d.veri).indexOf("_sup"), -1);   // önbellek JSON'a sızmaz
  assert.deepEqual(B.durumListesi(null), []);
});

// ---- gerçek çözümlü binalar (pytest sarmalayıcısı üretir)
const FIXTURE = (process.env.MATRIS_BILGI_FIXTURE || "").split(path.delimiter).filter(Boolean);
test("gerçek çözüm: bütün elemanlar için bilgi motor verisiyle tutarlı", { skip: FIXTURE.length ? false : "MATRIS_BILGI_FIXTURE yok" }, function () {
  FIXTURE.forEach(function (dosya) {
    const d = JSON.parse(fs.readFileSync(dosya, "utf8"));
    const v = d.veri;
    const kom = v.gosterilecek[0];
    (v.bina.kolonlar.map(function (k) { return ["kolon", k]; })).concat(v.bina.kirisler.map(function (k) { return ["kiris", k]; })).forEach(function (q) {
      const tur = q[0], k = q[1];
      const m = B.bilgi({ tur: tur, no: k.no }, d.bina, v);
      const ad = path.basename(dosya) + " " + tur + " " + k.no;
      yakin(m.ham.L, k.L, 1e-6, ad + " L");
      yakin(m.ham.A, v.kutuphane_ozeti.kesitler[k.kesit].A, 1e-12, ad + " A");
      assert.equal(m.durum, kom, ad);
      const fe = v.ag.elemanlar.filter(function (e) { return e.tur === tur && e.kaynak_no === k.no; });
      const K = v.sonuclar[kom];
      ["N", "V", "M"].forEach(function (b) {
        let mx = -Infinity, mn = Infinity;
        fe.forEach(function (e) { const r = K.elemanlar.find(function (x) { return x.no === e.no; }); r[b].forEach(function (y) { mx = Math.max(mx, y); mn = Math.min(mn, y); }); });
        yakin(m.ham.ext[b].max, mx, 1e-9, ad + " " + b + " max"); yakin(m.ham.ext[b].min, mn, 1e-9, ad + " " + b + " min");
      });
      const z = B.bilgi({ tur: tur, no: k.no }, d.bina, v, { durum: "Zarf" }).ham.zarf;
      const ze = v.zarf.elemanlar.filter(function (e) { return fe.some(function (f) { return f.no === e.no; }); });
      yakin(z.M.max, Math.max.apply(null, ze.map(function (e) { return e.M_max; })), 1e-9, ad + " zarf");
      const t = (v.tasarim.elemanlar || []).find(function (e) { return e.tur === tur && e.no === k.no; });
      if (t) yakin(m.ham.dc, t.dc, 1e-12, ad + " D/C");
      if (m.ham.metraj && m.ham.metraj.beton_m3 != null) yakin(m.ham.metraj.beton_m3, k.A * k.L, 1e-9, ad + " beton");
      if (m.ham.metraj && m.ham.metraj.celik_kg != null) yakin(m.ham.metraj.celik_kg, k.A * k.L * 7850, 1e-9, ad + " çelik");
      if (m.ham.yol) {
        const id = tur === "kiris" ? "K" + k.no : "S" + k.no + "/k" + k.kat;
        const giden = v.akis.sankey.filter(function (s) { return s.kaynak === id && s.durum === "G"; }).reduce(function (a, s) { return a + s.kN; }, 0);
        yakin(m.ham.yol.gidenG, giden, 1e-9, ad + " yük yolu");
      }
      assert.ok(!/undefined|NaN/.test(B.tsv(m)), ad + " TSV");
    });
    (v.yukler.dosemeler || []).forEach(function (y) {
      const m = B.bilgi({ tur: "doseme", no: y.no }, d.bina, v);
      yakin(m.ham.paylarG, y.G_toplam, 1e-6, "döşeme " + y.no + " korunum");
    });
    (v.akis.temeller || []).forEach(function (t) {
      const m = B.bilgi({ tur: "temel", no: t.kolon_no }, d.bina, v);
      yakin(m.ham.dc, t.DC, 1e-12); yakin(m.ham.N_servis, t.N_servis, 1e-12);
    });
    v.ag.mesnetler.forEach(function (s) {
      const m = B.bilgi({ tur: "mesnet", no: s.dugum }, d.bina, v);
      const T = (v.sonuclar[kom].tepkiler || []).find(function (x) { return x.dugum === s.dugum; });
      if (T) yakin(m.ham.tepki[kom].FZ, T.FZ, 1e-9);
    });
  });
});

test("karma model: aks–kat kiriş, tasarım kaydına ve FE parçalarına kaynak {aks_kat, no} → çubuk numarasıyla bağlanır", function () {
  const d = mini();
  // genelleştirilmiş model çözümü: FE elemanı çubuk 12'yi taşır, tasarım kaydı no = çubuk no, kaynak aks–kat kiriş 1
  const fe = d.veri.ag.elemanlar[2];
  fe.cubuk = 12; fe.kaynak_no = 12;
  const t = d.veri.tasarim.elemanlar[0];
  t.no = 12; t.cubuk = 12; t.kaynak = { aks_kat: "kiris", no: 1 };
  // aynı numaralı başka bir aks–kat kaydı (tür + no eşleşmesi) kaynaktan sonra gelmeli
  d.veri.tasarim.elemanlar.push({ no: 1, tur: "kiris", sistem: "betonarme", dc: 0.99, durum: "yeterli", kontroller: [] });
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  yakin(m.ham.dc, 0.52);
  yakin(m.ham.ext.M.max, 1.4 * 31.25 + 1.6 * 12.5, 1e-9);      // FE parçası bulundu (çubuk 12)
  assert.match(metin(m, "tasarim"), /Talep\/kapasite D\/C\t0,520/);
});

test("karma model, genel çözüm: aks–kat kiriş ve kolonun yükleri ve yük yolu çözümdeki çubuk numarasıyla okunur", function () {
  const d = mini();
  const v = d.veri;
  v.model = "genel";
  const t = v.tasarim.elemanlar[0];
  t.no = 12; t.cubuk = 12; t.kaynak = { aks_kat: "kiris", no: 1 };
  v.yukler.kirisler = [];
  v.yukler.cubuklar = [{ no: 12, L: 5, G: { oz: 15.6, panel: 30, duvar: 0, ek: 10, toplam_kN: 55.6 }, Q: { panel: 12, toplam_kN: 12 } }];
  v.akis.sankey = [{ kaynak: "P1", hedef: "Ç12", durum: "G", kN: 30 }];
  // akış kolon kaydı: no = çubuk numarası (7), kaynak aks–kat kolon 2 (tasarım kaydı yok)
  v.akis.kolonlar = [{ no: 7, kat: 1, adres: "B1/+3.00", N_G: 40, N_Q: 9, N_kum_G: 40, N_kum_Q: 9, kaynak: { aks_kat: "kolon", no: 2 } }];
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, v);
  yakin(m.ham.yuk.G, 55.6, 1e-12);
  yakin(m.ham.panelPay, 30, 1e-12);
  assert.match(metin(m, "yukler"), /Panelden\t30,00\t12,00/);
  assert.match(metin(m, "yol"), /Panel 1/);
  const k = B.bilgi({ tur: "kolon", no: 2 }, d.bina, v);
  yakin(k.ham.N_kum.G, 40, 1e-12);
  assert.match(metin(k, "yukler"), /Birikimli N \(G \/ Q\)\t40,00 \/ 9,00/);
  // aks–kat çözümünde (model genel değil) eski yol: yukler.kirisler
  delete v.model;
  const ak = metin(B.bilgi({ tur: "kiris", no: 1 }, d.bina, v), "yukler");
  assert.match(ak, /Döşemeden aktarılan paylar/);
  assert.ok(ak.indexOf("Çubuğa gelen") < 0);
});

function genelYol(sankey) {
  const d = mini();
  const v = d.veri;
  v.model = "genel";
  const t = v.tasarim.elemanlar[0];
  t.no = 12; t.cubuk = 12; t.kaynak = { aks_kat: "kiris", no: 1 };
  v.yukler.kirisler = [];
  v.yukler.cubuklar = [{ no: 12, L: 5, G: { oz: 15.6, panel: 30, duvar: 0, ek: 10, toplam_kN: 55.6 }, Q: { panel: 12, toplam_kN: 12 }, S: { panel: 3, toplam_kN: 3 } }];
  v.akis.sankey = sankey;
  v.akis.kolonlar = [{ no: 7, kat: 1, adres: "B1/+3.00", N_G: 40, N_Q: 9, N_kum_G: 40, N_kum_Q: 9, kaynak: { aks_kat: "kolon", no: 2 } }];
  return d;
}

test("yük yolu (genel): kenarlar durumlarına göre okunur; Q/S bantları varsa sütun olur, yoksa 'veri yok' notu; çubukta paneller kümesi", function () {
  // eski motor: genel modelde yalnız G bantları (tur yok = panel-cubuk)
  let d = genelYol([{ kaynak: "P1", hedef: "Ç12", durum: "G", kN: 30 }, { kaynak: "P2", hedef: "Ç12", durum: "G", kN: 10.5 }]);
  let m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  let yol = sekme(m, "yol");
  assert.equal(yol.bolumler[0].baslik, "Akış şeması (G, kN)");
  let tb = yol.bolumler.find(function (b) { return b.tablo; });
  assert.equal(tb.baslik, "Panellerden aktarılan paylar (kN)");
  assert.deepEqual(tb.tablo.basliklar, ["Panel", "G"]);
  assert.ok(!yol.bolumler.some(function (b) { return b.baslik === "Aktardığı (kN)"; }), "giden kenarı yok: Aktardığı kümesi yazılmaz");
  assert.match(metin(m, "yol"), /Σ\t40,50/);
  assert.match(metin(m, "yol"), /yalnız G bantları var; Q ve S payları Yükler sekmesinde/);
  // K-41: "çubuktan sonraki aktarımı göstermez" notu kaldırıldı (motor C15 kenarlarını veriyor)
  assert.doesNotMatch(metin(m, "yol"), /göstermez/);
  // yeni motor: Q ve S bantları da var (G + Q + S)
  d = genelYol([{ kaynak: "P1", hedef: "Ç12", durum: "G", kN: 30, tur: "panel-cubuk" }, { kaynak: "P1", hedef: "Ç12", durum: "Q", kN: 12, tur: "panel-cubuk" }, { kaynak: "P1", hedef: "Ç12", durum: "S", kN: 3, tur: "panel-cubuk" },
    { kaynak: "P2", hedef: "Ç12", durum: "G", kN: 10, tur: "panel-cubuk" }, { kaynak: "P2", hedef: "Ç12", durum: "Q", kN: 4, tur: "panel-cubuk" }]);
  m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  yol = sekme(m, "yol");
  assert.equal(yol.bolumler[0].baslik, "Akış şeması (G + Q + S, kN)");
  tb = yol.bolumler.find(function (b) { return b.tablo; }).tablo;
  assert.deepEqual(tb.basliklar, ["Panel", "G", "Q", "S"]);
  assert.match(metin(m, "yol"), /Panel 1\t30,00\t12,00\t3,00/);
  assert.match(metin(m, "yol"), /Σ\t40,00\t16,00\t3,00/);
  assert.deepEqual(m.ham.yol, { gelenG: 40, gelenQ: 16, gidenG: 0, gidenQ: 0, gelenS: 3, gidenS: 0, kumeler: { panel: 40, cubuk: 0, aktardigi: 0 } });
  assert.ok(metin(m, "yol").indexOf("yalnız G bantları") < 0);
  // kolon: hiç kenar yok, yalnız panel bantları olan eski çözüm → açıklayıcı not
  const k = B.bilgi({ tur: "kolon", no: 2 }, d.bina, d.veri);
  const ky = sekme(k, "yol");
  assert.ok(ky, "kolonun yük yolu sekmesi");
  assert.match(metin(k, "yol"), /panel → çubuk paylarını gösterir; bu çubuğa panelden yük gelmiyor/);
  // panel yalnız kaynak: "Σ gelen 0" satırı yazılmaz, panel notu verilir; aks–kat döşemesi değişmez
  d.bina.paneller = [{ no: 1, dugumler: [], kalinlik: 0.12 }];
  const pn = B.bilgi({ tur: "panel", no: 1 }, d.bina, d.veri);
  const pt = sekme(pn, "yol").bolumler.find(function (b) { return b.tablo; }).tablo;
  assert.ok(!pt.satirlar.some(function (r) { return r[0] === "Σ gelen"; }), "panelde Σ gelen 0 yazılmaz");
  assert.match(metin(pn, "yol"), /Σ giden\t\t30,00\t12,00\t3,00/);
  assert.match(metin(pn, "yol"), /Panel yükü \(alan × yük yoğunluğu\) çubuklarına dağıtılır/);
  assert.doesNotMatch(metin(m, "yol"), /Panel yükü \(alan/);       // çubukta yok
});

test("K-41 yük yolu (C15): paneller, çubuklardan ve düğüm yüklerinden gelen, aktardığı (Ç… ve Mesnet / temel); Yükler sekmesinde yalnız panel payları", function () {
  const d = genelYol([
    { kaynak: "P1", hedef: "Ç12", durum: "G", kN: 30, tur: "panel-cubuk" }, { kaynak: "P1", hedef: "Ç12", durum: "Q", kN: 12, tur: "panel-cubuk" },
    { kaynak: "Ç20", hedef: "Ç12", durum: "G", kN: 8, tur: "cubuk-cubuk" }, { kaynak: "D1021", hedef: "Ç12", durum: "G", kN: 5, tur: "dugum-cubuk" },
    { kaynak: "Ç12", hedef: "Ç7", durum: "G", kN: 40, tur: "cubuk-cubuk" }, { kaynak: "Ç12", hedef: "Ç7", durum: "Q", kN: 6, tur: "cubuk-cubuk" },
    { kaynak: "Ç12", hedef: "M1", durum: "G", kN: 18.6, tur: "cubuk-mesnet" }, { kaynak: "Ç12", hedef: "M1", durum: "Q", kN: 6, tur: "cubuk-mesnet" },
    { kaynak: "Ç7", hedef: "M21", durum: "G", kN: 40, tur: "cubuk-mesnet" }]);
  d.veri.tasarim.elemanlar.push({ no: 7, cubuk: 7, tur: "kolon", kaynak: { aks_kat: "kolon", no: 2 }, dc: 0.3, kontroller: [] });
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  const yol = sekme(m, "yol");
  const tablo = function (bas) { const b = yol.bolumler.find(function (x) { return x.baslik === bas; }); return b ? b.tablo : null; };
  assert.deepEqual(tablo("Panellerden aktarılan paylar (kN)").satirlar, [["Panel 1", "30,00", "12,00"], ["Σ", "30,00", "12,00"]]);
  assert.deepEqual(tablo("Çubuklardan ve düğüm yüklerinden gelen (kN)").satirlar, [["Çubuk 20", "8,00", "0,00"], ["Düğüm yükü B1/k1", "5,00", "0,00"], ["Σ", "13,00", "0,00"]]);
  assert.deepEqual(tablo("Aktardığı (kN)").satirlar, [["Çubuk 7 (kolon 2)", "40,00", "6,00"], ["Mesnet / temel A1/k0", "18,60", "6,00"], ["Σ", "58,60", "12,00"]]);
  assert.deepEqual(tablo("Aktardığı (kN)").basliklar, ["Hedef", "G", "Q"]);
  assert.deepEqual(m.ham.yol.kumeler, { panel: 30, cubuk: 13, aktardigi: 58.6 });
  yakin(m.ham.yol.gelenG, 43); yakin(m.ham.yol.gidenG, 58.6);
  assert.doesNotMatch(metin(m, "yol"), /göstermez/);
  // Yükler sekmesinde "Panellerden aktarılan paylar" yalnız panel-cubuk kenarları
  yakin(m.ham.panelPay, 30, 1e-12);
  assert.match(metin(m, "yukler"), /Panellerden aktarılan paylar \(kN\)\nPanel\tG\tQ\tS\nP1\t30,00\t12,00\t0,00\n/);
  assert.doesNotMatch(metin(m, "yukler"), /Ç20|D1021/);
  // kolon (çubuk 7): yalnız çubuktan gelen ve mesnede aktardığı; panel kümesi yok
  const k = B.bilgi({ tur: "kolon", no: 2 }, d.bina, d.veri);
  const kt = metin(k, "yol");
  assert.match(kt, /Çubuklardan ve düğüm yüklerinden gelen \(kN\)\nKaynak\tG\tQ\nÇubuk 12 \(kiriş 1\)\t40,00\t6,00/);
  assert.match(kt, /Aktardığı \(kN\)\nHedef\tG\tQ\nMesnet \/ temel B1\/k0\t40,00/);
  assert.doesNotMatch(kt, /Panellerden/);
  // yük taşımayan çubuk (yeni motor): kenarsız çubuğa yeni not
  const c3 = genelYol([{ kaynak: "Ç12", hedef: "M1", durum: "G", kN: 1, tur: "cubuk-mesnet" }]);
  c3.veri.akis.kolonlar = [];
  const k3 = B.bilgi({ tur: "kolon", no: 2 }, c3.bina, c3.veri);
  assert.match(metin(k3, "yol"), /Akış şemasında bu çubuğa gelen ya da bu çubuktan giden yük yok/);
});

test("K-20 (C17) karma model, genel çözüm: aks–kat döşemesi kaynaklı panel kaydından yük ve kenar payları; kenar çubukları aks–kat kirişiyle adlanır", function () {
  const d = genelYol([{ kaynak: "P4", hedef: "Ç12", durum: "G", kN: 30, tur: "panel-cubuk" }, { kaynak: "P4", hedef: "Ç13", durum: "G", kN: 20, tur: "panel-cubuk" }]);
  d.veri.yukler.dosemeler = [];
  d.veri.tasarim.elemanlar.push({ no: 13, cubuk: 13, tur: "kiris", kaynak: { aks_kat: "kiris", no: 9, parca: 1 }, dc: 0.4, kontroller: [] });
  d.veri.yukler.paneller = [{ no: 4, tur: "doseme", alan: 20, egim: 0, dagitim: "iki", g: 5, q: 2, s: 0, G_toplam: 100, Q_toplam: 40, S_toplam: 0, q_kaynak: "TS 498",
    kaynak: { aks_kat: "doseme", no: 1 }, kenarlar: [{ kenar: 1, cubuklar: [12], pay: 6, sekil: "trapez" }, { kenar: 2, cubuklar: [13, 14], pay: 4, sekil: "ucgen" }, { kenar: 3, cubuklar: [], pay: 0, sekil: "yok" }] }];
  const m = B.bilgi({ tur: "doseme", no: 1 }, d.bina, d.veri);
  const t = metin(m, "yukler");
  assert.doesNotMatch(t, /Önce çözün/, "eski: 'Önce çözün: Kirişlere aktarılan paylar'");
  assert.match(t, /Panel yükleri \(çözüm\)/);
  assert.match(t, /Toplam G \/ Q \/ S\t100,00 \/ 40,00 \/ 0,00/);
  assert.match(t, /Taşıyıcı kenarlara paylar\nKenar\tÇubuk\(lar\)\tŞekil\tPay alanı \(m²\)\n1\tkiriş 1 \(Ç12\)\ttrapez\t6,00\n2\tkiriş 9 \(Ç13\), Ç14\tüçgen\t4,00/);
  yakin(m.ham.yuk.G, 100);
  // yük yolu: döşemenin paneli (P4) üzerinden
  assert.match(metin(m, "yol"), /→ giden\tÇubuk 12 \(kiriş 1\)\t30,00/);
  // kaynak eşleşmezse (başka döşeme) eski davranış
  const m2 = B.bilgi({ tur: "doseme", no: 1 }, d.bina, Object.assign({}, d.veri, { yukler: Object.assign({}, d.veri.yukler, { paneller: [] }) }));
  assert.match(metin(m2, "yukler"), /Önce çözün: Kirişlere aktarılan paylar/);
});

test("K-1 (C11.7) mütemadi temel kirişi, genel çözüm: 'Oturan kolonlar' çubuk numarasıyla", function () {
  const d = mini();
  d.bina.temeller = { tip: "surekli", mesnet: "ankastre", zemin: { q_em: 200, k0: 20000 }, surekli: { B: 1.2, h_tabla: 0.3, b_govde: 0.4, h_govde: 0.8, tasma: 0.5 } };
  d.veri.bina.temeller = d.bina.temeller;
  d.veri.temel = { tip: "surekli", belirleyen_servis: "G+Q", dugumler: [{ no: 1, X: 0, Y: 0, w_mm: 2, p_kNm2: 40 }],
    hatlar: [{ ad: "1", yon: "x", L: 6, bas: -0.5, son: 5.5, dugumler: [1], kolonlar: [7, 9] }],
    kolonlar: [{ kolon_no: 7, adres: "Ç7 (A1)", N_servis: 120 }, { kolon_no: 9, adres: "Ç9 (B1)", N_servis: 95 }], tasarim: [], model: { k0: 20000 } };
  const h = { tur: "temel", alt: "surekli", no: 1, aks: "1", yon: "x" };
  d.veri.model = "genel";
  const g = metin(B.bilgi(h, d.bina, d.veri), "geometri");
  assert.match(g, /Oturan kolonlar \(2\)\nÇubuk 7\tÇ7 \(A1\) · N = 120,0 kN\t?\nÇubuk 9\tÇ9 \(B1\)/);
  delete d.veri.model;
  assert.match(metin(B.bilgi(h, d.bina, d.veri), "geometri"), /\nKolon 7\t/, "aks–kat çözümünde kolon numarası");
});

test("K-10 (C13) yaylı mesnet denetçisi: tip 'yaylı mesnet', rijitlikler 'k_z = 10 000 kN/m', yay kuvvetleri (bina eksenleri, kombinasyon süperpozisyonu)", function () {
  const d = mini();
  d.veri.ag.mesnetler = [{ dugum: 1, tip: "yay", kaynak: "mesnetler", ux: true, uy: true, uz: false, rx: false, ry: false, rz: false, yay: { kz: 10000, kry: 2500.5 } }, { dugum: 21, tip: "ankastre" }];
  // motor ekseni yay kayıtları: Fy → FZ, Mz → −MY (C12)
  d.veri.durumlar.G.yaylar = [{ dugum: 1, sd: 1, bilesen: "Fy", k: 10000, kuvvet: 25, tur: "yay-mesnet" }, { dugum: 1, sd: 5, bilesen: "Mz", k: 2500.5, kuvvet: 2, tur: "yay-mesnet" }, { dugum: 1, sd: 6, bilesen: "Fx", k: 5, kuvvet: 99 }];
  d.veri.durumlar.Q.yaylar = [{ dugum: 1, sd: 1, bilesen: "Fy", k: 10000, kuvvet: 10, tur: "yay-mesnet" }, { dugum: 1, sd: 5, bilesen: "Mz", k: 2500.5, kuvvet: 1, tur: "yay-mesnet" }, { dugum: 1, sd: 6, bilesen: "Fx", k: 5, kuvvet: 1 }];
  const m = B.bilgi({ tur: "mesnet", no: 1 }, d.bina, d.veri);
  assert.equal(m.turAdi, "Mesnet");
  const bg = metin(m, "baglanti");
  assert.match(bg, /Mesnet\tyaylı mesnet/);
  assert.match(bg, /Yay rijitliği\tk_z = 10 000 kN\/m/);
  assert.match(bg, /Yay rijitliği\tk_ry = 2 500,5 kN·m\/rad/);
  assert.match(bg, /Tutulu yönler\tux, uy/);
  assert.ok(m.ozet.some(function (o) { return o.ad === "Yay" && o.deger === "k_z = 10 000 kN/m · k_ry = 2 500,5 kN·m/rad"; }));
  assert.deepEqual(m.ham.yay, { kz: 10000, kry: 2500.5 });
  const tp = metin(m, "tepki");
  assert.match(tp, /Yaylı mesnet\nYay rijitliği\tk_z = 10 000 kN\/m/);
  assert.match(tp, /Yay kuvvetleri \(bina koordinatı\)/);
  assert.deepEqual(m.ham.yayKuvveti.G, { FX: 0, FY: 0, FZ: 25, MX: 0, MY: -2, MZ: 0 }, "temel yayı (tur yok) sayılmaz");
  // kombinasyon: 1.4G + 1.6Q süperpozisyonu
  yakin(m.ham.yayKuvveti["1.4G+1.6Q"].FZ, 1.4 * 25 + 1.6 * 10, 1e-12);
  assert.equal(m.sekmeler[1].id, "tepki", "mesnette tepki sekmesi Geometri'den sonra");
  // çubuk denetçisinde uç mesnedi de "yaylı mesnet"
  assert.match(metin(B.bilgi({ tur: "kolon", no: 1 }, d.bina, d.veri), "baglanti"), /i ucunda mesnet\tyaylı mesnet/);
  assert.ok(!/NaN|undefined/.test(B.tsv(m)));
});

test("K-15 (C14) rijit diyafram düğümündeki mesnet: ux/uy/rz kuvveti ceza yayında (tur 'diyafram-mesnet') — 'Diyafram bağı kuvvetleri' tablosu ve notu", function () {
  const d = mini();
  d.veri.ag.mesnetler = [{ dugum: 1, tip: "ankastre", kaynak: "mesnetler", ux: true, uy: true, uz: true, rx: true, ry: true, rz: true }];
  // motor ekseni: Fz → −FY, My → MZ (C12); tepkilerde FY / MZ sıfır (yatay kuvvet ceza yayında)
  d.veri.durumlar.G.yaylar = [{ dugum: 1, sd: 3, bilesen: "Fz", k: 6e11, kuvvet: 16.5, tur: "diyafram-mesnet" }, { dugum: 1, sd: 5, bilesen: "My", k: 1.5e10, kuvvet: 49.5, tur: "diyafram-mesnet" }];
  d.veri.durumlar.Q.yaylar = [{ dugum: 1, sd: 3, bilesen: "Fz", k: 6e11, kuvvet: 7, tur: "diyafram-mesnet" }, { dugum: 1, sd: 5, bilesen: "My", k: 1.5e10, kuvvet: 20, tur: "diyafram-mesnet" }];
  const m = B.bilgi({ tur: "mesnet", no: 1 }, d.bina, d.veri);
  const tp = metin(m, "tepki");
  assert.match(tp, /Diyafram bağı kuvvetleri \(bina koordinatı\)\nDurum\tFX \(kN\)/);
  assert.match(tp, /\nG\t0,00\t[-−]16,50\t0,00\t0,00\t0,00\t49,50/);
  assert.match(tp, /diyafram bağıyla \(ceza rijitliği\) uygulandı/);
  assert.ok(!/Yay kuvvetleri/.test(tp), "diyafram yayı yaylı mesnet değildir");
  assert.deepEqual(m.ham.diyaframKuvveti.G, { FX: 0, FY: -16.5, FZ: 0, MX: 0, MY: 0, MZ: 49.5 });
  yakin(m.ham.diyaframKuvveti["1.4G+1.6Q"].MZ, 1.4 * 49.5 + 1.6 * 20, 1e-9);
  assert.ok(!m.ham.yayKuvveti);
  assert.ok(!/NaN|undefined/.test(B.tsv(m)));
});

test("tasarım kontrolleri: kapasiteye göre sayısal gürültü olan talep (3·10⁻¹⁷) 0 yazılır", function () {
  const d = mini();
  d.veri.tasarim.elemanlar[0].kontroller.push({ ad: "Zayıf eksen eğilmesi", talep: 3e-17, kapasite: 38.04, birim: "kN·m", dc: 0, saglandi: true });
  d.veri.tasarim.elemanlar[0].ozet.My_kNm = -2.5e-17;
  const m = B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri);
  const t = metin(m, "tasarim");
  assert.match(t, /Zayıf eksen eğilmesi\t0\t38,04\tkN·m/);
  assert.ok(t.indexOf("10^") < 0, t);
  // gerçek küçük değerler (ör. 0,004) bilimsel gösterimde kalır
  d.veri.tasarim.elemanlar[0].kontroller.push({ ad: "Küçük", talep: 0.004, kapasite: 1, birim: "", dc: 0.004, saglandi: true });
  assert.match(metin(B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri), "tasarim"), /Küçük\t4,00·10\^[−-]3\t1,000/);
});

test("tasarım özeti: dizi değerleri ' / ' ile birleşir, iç içe nesneler satıra yazılmaz", function () {
  const d = mini();
  d.veri.tasarim.elemanlar[0].ozet = { K: [0.65, 1], yalniz_cekme: true, Tc_kN: 412.5, ayrinti: { a: 1 } };
  const s = metin(B.bilgi({ tur: "kiris", no: 1 }, d.bina, d.veri), "tasarim");
  assert.match(s, /K \(güçlü \/ zayıf\)\t0,650 \/ 1,000|K \(güçlü \/ zayıf\)\t0,65 \/ 1/);
  assert.match(s, /Yalnız çekme\tevet/);
  assert.match(s, /T_c = T_n\/Ω \(çekme\)\t412,5/);
  assert.ok(s.indexOf("ayrinti") < 0 && s.indexOf("[object") < 0);
});

test("tekil temel: veri.akis.temeller'deki B'siz kayıt (açık mesnet) temel sayılmaz", function () {
  const d = mini();
  d.veri.akis.temeller.push({ dugum: 21, kolon_no: 2, aks: null, tip: "mafsal", N_G: 30, N_Q: 10, MX: 0, MY: 0 });
  const t2 = B.bilgi({ tur: "temel", no: 2 }, d.bina, d.veri);
  assert.equal(t2.ham.dc, undefined);
  assert.equal(sekme(t2, "tasarim"), undefined);   // taban basıncı / D/C yalnız B × L'si olan tekil temelde
  assert.ok(!/NaN|undefined/.test(B.tsv(t2)));
  assert.equal(t2.adres, "T-B1");              // aks, kolondan (B'siz kaydın aks: null değerinden değil)
  yakin(B.bilgi({ tur: "temel", no: 1 }, d.bina, d.veri).ham.dc, 0.175);
});

test("mütemadi temel kirişi ve radye: veri.temel hatlarından geometri, zemin basıncı, tasarım ve metraj", function () {
  const d = mini();
  d.bina.temeller = { tip: "surekli", mesnet: "elastik", zemin: { q_em: 200, k0: 20000 },
    surekli: { B: 1.2, h_tabla: 0.3, b_govde: 0.4, h_govde: 0.8, tasma: 0.5 } };
  d.veri.bina.temeller = d.bina.temeller;
  d.veri.temel = { tip: "surekli", belirleyen_servis: "G+Q",
    dugumler: [{ no: 1, X: -0.5, Y: 0, w_mm: 2.5, p_kNm2: 50 }, { no: 2, X: 2.5, Y: 0, w_mm: 4, p_kNm2: 80 }, { no: 3, X: 5.5, Y: 0, w_mm: 3, p_kNm2: 60 }],
    hatlar: [{ ad: "1", yon: "x", L: 6, bas: -0.5, son: 5.5, dugumler: [1, 2, 3], kolonlar: [1, 2] }],
    kolonlar: [{ kolon_no: 1, adres: "A1", N_servis: 120 }],
    tasarim: [{ tur: "temel-kirisi", hat: "1", yon: "x", b: 0.4, h: 0.8, Md_alt: 100, Md_ust: 50, As_alt_cm2: 5, As_ust_cm2: 3, oneri_alt: "4Φ14", oneri_ust: "3Φ12",
      Vd: 80, etriye: "Φ8/15", dc: 0.6, durum: "yeterli", kontroller: [{ ad: "Eğilme", talep: 100, kapasite: 180, birim: "kN·m", dc: 0.556, saglandi: true }] }],
    model: { k0: 20000 } };
  const m = B.bilgi({ tur: "temel", alt: "surekli", no: 1, aks: "1", yon: "x" }, d.bina, d.veri);
  assert.equal(m.baslik, "Mütemadi temel kirişi 1");
  assert.deepEqual(m.sekmeler.map(function (s) { return s.id; }), ["geometri", "zemin", "tasarim", "metraj"]);
  yakin(m.ham.p_maks, 80); yakin(m.ham.dc, 0.6);
  yakin(m.ham.metraj.beton_m3, (1.2 * 0.3 + 0.4 * 0.5) * 6, 1e-12);
  assert.match(metin(m, "geometri"), /Kolon 1\tA1 · N = 120,0 kN/);
  assert.match(metin(m, "zemin"), /Zemin D\/C \(p_maks \/ q_em\)\t0,400/);
  assert.ok(!/NaN|undefined/.test(B.tsv(m)));
  // çözümsüz: geometri bina tanımından, zemin basıncı "Önce çözün"
  const c = B.bilgi({ tur: "temel", alt: "surekli", no: 1, aks: "1", yon: "x" }, d.bina, null);
  assert.match(metin(c, "zemin"), /Önce çözün/);
  assert.match(metin(c, "geometri"), /Tabla B × h_tabla\t1,20 × 0,30/);
  // radye
  d.bina.temeller = { tip: "radye", mesnet: "elastik", zemin: { q_em: 200, k0: 20000 }, radye: { h: 0.6, tasma: 0.5, ag: 1 } };
  d.veri.bina.temeller = d.bina.temeller;
  d.veri.temel = { tip: "radye", p_maks: 90, p_min: 20, DC_zemin: 0.45, oturma_maks_mm: 4.5, oturma_min_mm: 1, farkli_oturma_metin: "1/2000", en_buyuk_dc: 0.7,
    model: { k0: 20000, plak: { X0: -0.5, X1: 5.5, Y0: -0.5, Y1: 4.5, h: 0.6, alan: 30 } },
    tasarim: [{ tur: "radye-serit", yon: "x", M_alt_m: 40, M_ust_m: 20, As_alt_cm2_m: 6, As_ust_cm2_m: 4, oneri_alt: "Φ12/18", oneri_ust: "Φ10/18", dc: 0.7 }],
    zemin_kontrolleri: [{ ad: "Zemin basıncı", talep: 90, kapasite: 200, birim: "kN/m²", dc: 0.45, saglandi: true }] };
  const r = B.bilgi({ tur: "temel", alt: "radye", no: 1 }, d.bina, d.veri);
  assert.equal(r.baslik, "Radye temel");
  yakin(r.ham.dc, 0.7); yakin(r.ham.p_maks, 90); yakin(r.ham.metraj.beton_m3, 18, 1e-12);
  assert.match(metin(r, "tasarim"), /X\t40,0 \/ 20,0\t6,00 \/ 4,00\tΦ12\/18 \/ Φ10\/18\t0,70/);
  assert.ok(!/NaN|undefined/.test(B.tsv(r)));
});

test("menü: yük akışı çubuk ve temel için, ısı haritası temel için; devre dışı öğe nedenini taşır", function () {
  const ids = function (tur) { return B.menuOgeleri(tur, {}).map(function (o) { return o.id; }); };
  assert.ok(ids("cubuk").indexOf("yuk-akisi") >= 0);
  assert.ok(ids("temel").indexOf("isi-haritasi") >= 0);
  const l = B.menuOgeleri("kolon", { tasarim: { calistir: function () {}, etkin: false, neden: "Bu çözümde tasarım kaydı yok." },
    "yuk-akisi": { calistir: function () {}, etkin: function () { return false; }, neden: function () { return "Önce modeli çözün."; } } });
  const o = function (id) { return l.find(function (x) { return x.id === id; }); };
  assert.equal(o("tasarim").etkin, false); assert.equal(o("tasarim").neden, "Bu çözümde tasarım kaydı yok.");
  assert.equal(o("yuk-akisi").neden, "Önce modeli çözün.");
  assert.equal(o("bilgi").neden, "");
});

const GENEL = process.env.MATRIS_BILGI_GENEL || "";
test("genel (surum 3) çözüm: çubuk, panel ve temel bilgisi motor kayıtlarıyla tutarlı", { skip: GENEL ? false : "MATRIS_BILGI_GENEL yok" }, function () {
  const d = JSON.parse(fs.readFileSync(GENEL, "utf8"));
  const v = d.veri;
  assert.equal(v.model, "genel");
  let n = 0;
  (v.tasarim.elemanlar || []).forEach(function (t) {
    if (t.cubuk == null) return;
    const m = B.bilgi({ tur: "cubuk", no: t.cubuk }, d.bina, v, { durum: "G" });
    const ad = "çubuk " + t.cubuk + " (" + t.tur + ")";
    assert.equal(m.durum, "G", ad);
    yakin(m.ham.dc, t.dc, 1e-12, ad + " D/C");
    // FE parçaları çubuk numarasıyla (ag.elemanlar[].cubuk)
    const fe = v.ag.elemanlar.filter(function (e) { return e.cubuk === t.cubuk; });
    assert.ok(fe.length > 0, ad + " FE");
    let mx = -Infinity;
    fe.forEach(function (e) { const r = v.durumlar.G.elemanlar.find(function (x) { return x.no === e.no; }); r.N.forEach(function (y) { mx = Math.max(mx, y); }); });
    yakin(m.ham.ext.N.max, mx, 1e-9, ad + " N max");
    // yükler veri.yukler.cubuklar'dan; panel payları sankey'den (P → Ç)
    const y = v.yukler.cubuklar.find(function (x) { return x.no === t.cubuk; });
    if (y) yakin(m.ham.yuk.G, y.G.toplam_kN, 1e-9, ad + " G");
    // panel payı yalnız panel → çubuk kenarları (C15 tur panel-cubuk ya da tursuz eski kayıt); motor çubuk → çubuk kenarı da verir
    const panelMi = function (e) { return !e.tur || e.tur === "panel-cubuk"; };
    const pay = v.akis.sankey.filter(function (e) { return e.hedef === "Ç" + t.cubuk && e.durum === "G" && panelMi(e); }).reduce(function (a, e) { return a + e.kN; }, 0);
    if (pay > 0) yakin(m.ham.panelPay, pay, 1e-9, ad + " panel payı");
    // yük yolu kümeleri (C15): panel / çubuk-düğüm gelen ve aktardığı toplamları kenarlarla aynı
    if (m.ham.yol && m.ham.yol.kumeler) {
      const gel = v.akis.sankey.filter(function (e) { return e.hedef === "Ç" + t.cubuk && e.durum === "G"; });
      yakin(m.ham.yol.kumeler.panel, gel.filter(panelMi).reduce(function (a, e) { return a + e.kN; }, 0), 1e-9, ad + " panel kümesi");
      yakin(m.ham.yol.kumeler.cubuk, gel.filter(function (e) { return !panelMi(e); }).reduce(function (a, e) { return a + e.kN; }, 0), 1e-9, ad + " çubuk kümesi");
      yakin(m.ham.yol.kumeler.aktardigi, v.akis.sankey.filter(function (e) { return e.kaynak === "Ç" + t.cubuk && e.durum === "G"; }).reduce(function (a, e) { return a + e.kN; }, 0), 1e-9, ad + " aktardığı");
    }
    assert.ok(!/undefined|NaN/.test(B.tsv(m)), ad + " TSV");
    n++;
  });
  assert.ok(n > 50, "tasarım kaydı olan çubuk sayısı " + n);
  (v.yukler.paneller || []).forEach(function (p) {
    const m = B.bilgi({ tur: "panel", no: p.no }, d.bina, v);
    yakin(m.ham.yuk.G, p.G_toplam, 1e-9, "panel " + p.no);
    assert.ok(!/undefined|NaN/.test(B.tsv(m)), "panel " + p.no + " TSV");
  });
  // C2: akis.temeller yalnız temel kayıtlarını (B, L, h, N_temel) taşır; açık mesnetler akis.mesnetler'dedir
  const tl = v.akis.temeller || [];
  assert.ok(tl.length > 0 && tl.every(function (t) { return t.B != null && t.N_temel != null; }), "akis.temeller yalnız temel kayıtları");
  const ms = v.akis.mesnetler || [];
  assert.ok(Array.isArray(v.akis.mesnetler), "akis.mesnetler listesi");
  ms.forEach(function (s) { assert.ok(s.dugum != null && "N_G" in s && "N_Q" in s, "mesnet kaydı " + JSON.stringify(s)); });
  tl.forEach(function (t) {
    const m = B.bilgi({ tur: "temel", no: t.kolon_no }, d.bina, v);
    yakin(m.ham.dc, t.DC, 1e-12); yakin(m.ham.N_servis, t.N_servis, 1e-12);
  });
});
