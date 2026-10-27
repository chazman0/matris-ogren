/* Matris Öğren masaüstü — ana sürecin saf yardımcıları (masaüstü çatısı olmadan test edilebilir):
   dosya okuma/yazma (atomik), ayar deposu, son dosyalar, komut satırı dosyaları, pencere sınırları, otomatik kayıt/kurtarma. */
"use strict";

const fs = require("fs");
const path = require("path");

const PROJE_UZANTILARI = [".matris", ".json"];
const EN_BUYUK_PROJE = 64 * 1024 * 1024;   // 64 MB: bundan büyük "proje" dosyası açılmaz (yanlış dosya koruması)

function projeDosyasiMi(yol) {
  return typeof yol === "string" && PROJE_UZANTILARI.indexOf(path.extname(yol).toLowerCase()) >= 0;
}

// Önce geçici dosyaya yazılır, sonra yeniden adlandırılır: yazarken çökme olursa eski dosya bozulmaz.
function atomikYaz(yol, icerik) {
  fs.mkdirSync(path.dirname(yol), { recursive: true });
  const gecici = yol + "." + process.pid + "." + Date.now() + ".tmp";
  const veri = typeof icerik === "string" ? Buffer.from(icerik, "utf8") : Buffer.from(icerik);
  fs.writeFileSync(gecici, veri);
  try {
    fs.renameSync(gecici, yol);
  } catch (e) {
    // Windows'ta hedef başka süreçte açıksa rename başarısız olabilir: doğrudan yaz.
    try { fs.writeFileSync(yol, veri); } finally { try { fs.unlinkSync(gecici); } catch (e2) { /* yoksay */ } }
  }
  return veri.length;
}

// Proje dosyasını metin olarak okur (UTF-8, BOM atılır). Uzantı ve boyut denetlenir.
function projeOku(yol) {
  if (!projeDosyasiMi(yol)) throw new Error("Yalnız .matris ve .json proje dosyaları açılabilir: " + path.basename(String(yol)));
  const bilgi = fs.statSync(yol);
  if (!bilgi.isFile()) throw new Error("Dosya değil: " + yol);
  if (bilgi.size > EN_BUYUK_PROJE) throw new Error("Dosya çok büyük (" + Math.round(bilgi.size / 1048576) + " MB).");
  let metin = fs.readFileSync(yol, "utf8");
  if (metin.charCodeAt(0) === 0xfeff) metin = metin.slice(1);
  return { ad: path.basename(yol), yol: yol, icerik: metin };
}

// Basit JSON ayar deposu (userData/<ad>.json); bozuk dosya varsayılana döner.
function depo(dosya, varsayilan) {
  let veri;
  try { veri = Object.assign({}, varsayilan, JSON.parse(fs.readFileSync(dosya, "utf8"))); }
  catch (e) { veri = Object.assign({}, varsayilan); }
  let zamanlayici = null;
  const kaydetSimdi = function () {
    if (zamanlayici) { clearTimeout(zamanlayici); zamanlayici = null; }
    try { atomikYaz(dosya, JSON.stringify(veri, null, 1)); } catch (e) { /* ayar yazılamazsa uygulama yine çalışır */ }
  };
  return {
    al: function (anahtar) { return veri[anahtar]; },
    koy: function (anahtar, deger) {
      veri[anahtar] = deger;
      if (!zamanlayici) zamanlayici = setTimeout(kaydetSimdi, 400);
    },
    kaydetSimdi: kaydetSimdi,
    hepsi: function () { return veri; },
  };
}

function yolAnahtari(yol) {
  const n = path.resolve(yol);
  return process.platform === "win32" || process.platform === "darwin" ? n.toLowerCase() : n;
}

// Son dosyalar listesine ekler (en yeni başta, tekrarsız, en çok `enFazla`).
function sonDosyaEkle(liste, yol, enFazla) {
  const anahtar = yolAnahtari(yol);
  const yeni = [path.resolve(yol)].concat((liste || []).filter(function (y) { return yolAnahtari(y) !== anahtar; }));
  return yeni.slice(0, enFazla || 10);
}

// Komut satırındaki proje dosyaları (dosya ilişkilendirmesi, "Birlikte aç", ikinci örnek). Seçenekler (--x) ve çalışma zamanının
// kendi bağımsız değişkenleri atlanır; göreli yollar `cwd`'ye göre çözülür; var olmayanlar atılır.
function dosyaArgumanlari(argv, cwd) {
  const sonuc = [];
  (argv || []).forEach(function (a) {
    if (typeof a !== "string" || a.indexOf("-") === 0) return;
    if (!projeDosyasiMi(a)) return;
    const yol = path.resolve(cwd || process.cwd(), a);
    try { if (fs.statSync(yol).isFile()) sonuc.push(yol); } catch (e) { /* yok */ }
  });
  return sonuc;
}

// Kayıtlı pencere sınırı ekranlardan birinin içinde değilse (ekran söküldü vb.) kullanılmaz.
// ekranlar: [{x, y, width, height}] (çalışma alanları)
function pencereSiniri(kayitli, ekranlar, varsayilan) {
  const v = Object.assign({ width: 1400, height: 900 }, varsayilan || {});
  if (!kayitli || !(kayitli.width > 200) || !(kayitli.height > 150)) return v;
  const s = { x: Math.round(kayitli.x), y: Math.round(kayitli.y), width: Math.round(kayitli.width), height: Math.round(kayitli.height) };
  const gorunur = (ekranlar || []).some(function (e) {
    const ox = Math.min(s.x + s.width, e.x + e.width) - Math.max(s.x, e.x);
    const oy = Math.min(s.y + s.height, e.y + e.height) - Math.max(s.y, e.y);
    return ox >= 120 && oy >= 80;
  });
  if (!gorunur || !Number.isFinite(s.x) || !Number.isFinite(s.y)) return { width: Math.min(s.width, 4000), height: Math.min(s.height, 3000) };
  return s;
}

// ---- Otomatik kayıt ve kurtarma: userData/kurtarma/<oturum>-<pencere>.json = {surum, zaman, ad, yol, icerik}
function kurtarma(klasor) {
  const dosyaAdi = function (oturum, pencere) { return path.join(klasor, String(oturum) + "-" + String(pencere) + ".json"); };
  return {
    klasor: klasor,
    yaz: function (oturum, pencere, kayit) {
      return atomikYaz(dosyaAdi(oturum, pencere), JSON.stringify({
        surum: 1, zaman: new Date().toISOString(), ad: kayit.ad || null, yol: kayit.yol || null, icerik: String(kayit.icerik || ""),
      }));
    },
    sil: function (oturum, pencere) { try { fs.unlinkSync(dosyaAdi(oturum, pencere)); } catch (e) { /* yok */ } },
    oku: function (oturum, pencere) {
      try { return JSON.parse(fs.readFileSync(dosyaAdi(oturum, pencere), "utf8")); } catch (e) { return null; }
    },
    // Bu oturuma ait olmayan (önceki, beklenmedik biçimde kapanmış oturumlardan kalan) kayıtlar, en yeni önce.
    artiklar: function (oturum) {
      let adlar = [];
      try { adlar = fs.readdirSync(klasor); } catch (e) { return []; }
      const kayitlar = [];
      adlar.forEach(function (ad) {
        if (!/\.json$/.test(ad) || ad.indexOf(String(oturum) + "-") === 0) return;
        const yol = path.join(klasor, ad);
        try {
          const k = JSON.parse(fs.readFileSync(yol, "utf8"));
          if (k && typeof k.icerik === "string" && k.icerik) kayitlar.push(Object.assign({ dosya: yol }, k));
          else fs.unlinkSync(yol);
        } catch (e) { try { fs.unlinkSync(yol); } catch (e2) { /* yoksay */ } }
      });
      kayitlar.sort(function (a, b) { return String(b.zaman).localeCompare(String(a.zaman)); });
      return kayitlar;
    },
    at: function (kayit) { try { fs.unlinkSync(kayit.dosya); } catch (e) { /* yok */ } },
  };
}

// Kaydet iletişim kutusu süzgeçleri: sayfadan gelen [{ad, uzantilar}] temizlenir (yalnız harf/rakam uzantılar).
function suzgecler(liste) {
  const sonuc = [];
  (Array.isArray(liste) ? liste : []).slice(0, 12).forEach(function (s) {
    if (!s || typeof s !== "object") return;
    const uz = (Array.isArray(s.uzantilar) ? s.uzantilar : []).map(function (u) { return String(u).replace(/^\./, ""); })
      .filter(function (u) { return u === "*" || /^[A-Za-z0-9]{1,10}$/.test(u); });
    if (uz.length) sonuc.push({ name: String(s.ad || uz.join(", ")).slice(0, 80), extensions: uz });
  });
  if (!sonuc.some(function (s) { return s.extensions.indexOf("*") >= 0; })) sonuc.push({ name: "Tüm dosyalar", extensions: ["*"] });
  return sonuc;
}

// Dosya adı temizliği (iletişim kutusunun önerdiği ad)
function guvenliAd(ad, yedek) {
  const temiz = String(ad || "").replace(/[\\/:*?"<>|\u0000-\u001f]+/g, "_").replace(/^\.+/, "").trim().slice(0, 150);
  return temiz || yedek || "adsiz";
}

// Rapor HTML'inde <title> yoksa eklenir (PDF belge başlığı olur; yoksa iç adres görünürdü).
function htmlBasligiEkle(html, baslik) {
  const metin = String(html || "");
  if (/<title[\s>]/i.test(metin)) return metin;
  const t = "<title>" + String(baslik || "Rapor").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }) + "</title>";
  if (/<head[^>]*>/i.test(metin)) return metin.replace(/<head[^>]*>/i, function (m) { return m + t; });
  if (/<html[^>]*>/i.test(metin)) return metin.replace(/<html[^>]*>/i, function (m) { return m + "<head><meta charset=\"utf-8\">" + t + "</head>"; });
  return "<!DOCTYPE html><html><head><meta charset=\"utf-8\">" + t + "</head><body>" + metin + "</body></html>";
}

// PDF bilgi sözlüğündeki üretici girdileri (/Creator, /Producer: tarayıcı motorunun adı) aynı uzunlukta boşlukla silinir;
// bayt konumları değişmediğinden çapraz başvuru tablosu geçerli kalır. Bilgi sözlüğü bulunamazsa veri olduğu gibi döner.
function pdfUreticiBilgisiniSil(veri) {
  const buf = Buffer.isBuffer(veri) ? veri : Buffer.from(veri);
  const metin = buf.toString("latin1");
  const iz = /\/Info\s+(\d+)\s+0\s+R/g;
  let m, no = null;
  while ((m = iz.exec(metin)) !== null) no = m[1];
  if (no === null) return buf;
  const bas = new RegExp("(^|[\\r\\n\\s])" + no + "\\s+0\\s+obj").exec(metin);
  if (!bas) return buf;
  const son = metin.indexOf("endobj", bas.index);
  if (son < 0) return buf;
  const sozluk = metin.slice(bas.index, son);
  const temiz = sozluk.replace(/\/(Creator|Producer)\s*(\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]*>)/g, function (x) { return " ".repeat(x.length); });
  if (temiz === sozluk) return buf;
  return Buffer.from(metin.slice(0, bas.index) + temiz + metin.slice(son), "latin1");
}

module.exports = {
  htmlBasligiEkle: htmlBasligiEkle, pdfUreticiBilgisiniSil: pdfUreticiBilgisiniSil,
  PROJE_UZANTILARI: PROJE_UZANTILARI, projeDosyasiMi: projeDosyasiMi, atomikYaz: atomikYaz, projeOku: projeOku, depo: depo,
  sonDosyaEkle: sonDosyaEkle, dosyaArgumanlari: dosyaArgumanlari, pencereSiniri: pencereSiniri, kurtarma: kurtarma,
  suzgecler: suzgecler, guvenliAd: guvenliAd,
};
