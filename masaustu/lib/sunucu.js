/* Matris Öğren masaüstü — uygulama dosyalarının sunulması (app://matris/... ve yerel önizleme sunucusu için ortak, saf Node).
   - URL yolu → uygulama/ altındaki dosya (dizin dışına çıkış engellenir),
   - doğru içerik türü (WASM akışlı derleme application/wasm ister; ES modülleri text/javascript),
   - HTML belgelerine İçerik Güvenliği Politikası (CSP): yalnız uygulamanın kendi dosyaları; satır içi betikler
     yalnız SHA-256 özetiyle (galeri.html gibi sayfalardaki küçük betikler), dış kaynak yok. */
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const ICERIK_TURU = {
  ".html": "text/html; charset=utf-8",
  ".htm": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webmanifest": "application/manifest+json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".wasm": "application/wasm",
  ".zip": "application/zip",
  ".whl": "application/zip",
  ".tar": "application/x-tar",
  ".py": "text/x-python; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".ttf": "font/ttf",
  ".pdf": "application/pdf",
};

function icerikTuru(dosya) {
  return ICERIK_TURU[path.extname(dosya).toLowerCase()] || "application/octet-stream";
}

// URL yolunu (ör. "/pyodide/pyodide.mjs") kök dizin içindeki mutlak dosya yoluna çevirir; geçersizse null.
function yolCozumle(kok, urlYolu) {
  let yol;
  try { yol = decodeURIComponent(String(urlYolu || "/").split("?")[0].split("#")[0]); } catch (e) { return null; }
  if (yol.indexOf("\0") >= 0) return null;
  yol = yol.replace(/\\/g, "/");
  if (yol === "" || yol.endsWith("/")) yol += "index.html";
  const kokMutlak = path.resolve(kok);
  const hedef = path.resolve(kokMutlak, "." + path.posix.normalize("/" + yol));
  if (hedef !== kokMutlak && !hedef.startsWith(kokMutlak + path.sep)) return null;
  return hedef;
}

// Satır içi <script> (src'siz) içeriklerinin CSP özetleri
function satirIciBetikOzetleri(html) {
  const ozetler = [];
  const desen = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = desen.exec(html)) !== null) {
    if (/\bsrc\s*=/i.test(m[1])) continue;
    if (/type\s*=\s*["']?(application\/(ld\+)?json|text\/template)/i.test(m[1])) continue;
    ozetler.push("'sha256-" + crypto.createHash("sha256").update(m[2], "utf8").digest("base64") + "'");
  }
  return ozetler;
}

function cspUret(html) {
  const betik = ["'self'", "'wasm-unsafe-eval'"].concat(satirIciBetikOzetleri(html || ""));
  return [
    "default-src 'self'",
    "script-src " + betik.join(" "),
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self' data: blob:",
    "worker-src 'self' blob:",
    "frame-src 'self' blob: data: about:",
    "media-src 'self' blob: data:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}

// {durum, basliklar, govde(Buffer)} — Electron protocol.handle ve http önizleme sunucusu aynı yanıtı üretir.
async function yanitUret(kok, urlMetni) {
  let url;
  try { url = new URL(urlMetni); } catch (e) { return hataYaniti(400, "Geçersiz adres"); }
  const dosya = yolCozumle(kok, url.pathname);
  if (!dosya) return hataYaniti(403, "Erişim reddedildi");
  let govde;
  try {
    const bilgi = await fs.promises.stat(dosya);
    if (!bilgi.isFile()) return hataYaniti(404, "Bulunamadı");
    govde = await fs.promises.readFile(dosya);
  } catch (e) {
    return hataYaniti(404, "Bulunamadı: " + url.pathname);
  }
  const tur = icerikTuru(dosya);
  const basliklar = {
    "Content-Type": tur,
    "Content-Length": String(govde.length),
    "Cache-Control": "no-cache",
    "X-Content-Type-Options": "nosniff",
  };
  if (tur.indexOf("text/html") === 0) {
    basliklar["Content-Security-Policy"] = cspUret(govde.toString("utf8"));
    basliklar["Referrer-Policy"] = "no-referrer";
  }
  return { durum: 200, basliklar: basliklar, govde: govde };
}

function hataYaniti(durum, metin) {
  const govde = Buffer.from(metin, "utf8");
  return { durum: durum, basliklar: { "Content-Type": "text/plain; charset=utf-8", "Content-Length": String(govde.length) }, govde: govde };
}

module.exports = { icerikTuru: icerikTuru, yolCozumle: yolCozumle, cspUret: cspUret, satirIciBetikOzetleri: satirIciBetikOzetleri, yanitUret: yanitUret };
