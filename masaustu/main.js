/* Matris Öğren masaüstü — ana süreç.

   - Uygulama dosyaları (hazirla.js'in ../docs'tan kurduğu uygulama/ klasörü) app://matris/ adresinden sunulur
     (standart + güvenli şema: modül worker, WebAssembly akışlı derleme ve fetch çalışır; ağ gerekmez).
   - Türkçe yerel menü (lib/menu.js), kısayollar, çoklu pencere, son dosyalar, pencere durumu,
     otomatik kayıt ve çökme sonrası kurtarma, tek örnek + komut satırı/dosya ilişkilendirmesi (.matris),
     sürükle-bırak, yerel kaydet/aç iletişim kutuları, rapordan PDF (printToPDF).
   - Güvenlik: contextIsolation + sandbox, nodeIntegration kapalı; sayfa yalnız preload.js'in dar `window.masaustu`
     yüzeyini görür. Uygulama dışına gezinme engellenir; http(s) bağlantıları varsayılan tarayıcıda açılır. */
"use strict";

const { app, BrowserWindow, Menu, protocol, dialog, ipcMain, shell, screen, session, nativeTheme, nativeImage } = require("electron");
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const sunucu = require("./lib/sunucu");
const Y = require("./lib/yardimci");
const { menuSablonu, kisayolMetni, kisayolListesiTemizle } = require("./lib/menu");

const UYGULAMA_ADI = "Matris Öğren";
const UYGULAMA_KIMLIGI = "com.matrisogren.app";
const SEMA = "app";
const KOK_HOST = "matris";
const KOK_URL = SEMA + "://" + KOK_HOST + "/";
const UYGULAMA_KOK = path.join(__dirname, "uygulama");
const SIMGE = path.join(UYGULAMA_KOK, "icons", "icon-512.png");
const EN_BUYUK_KAYIT = 256 * 1024 * 1024;
const PROJE_FILTRELERI = [{ name: "Matris Öğren projesi", extensions: ["matris"] }, { name: "JSON", extensions: ["json"] }];

app.setName(UYGULAMA_ADI);
// Ayarlar, kurtarma kayıtları ve tarayıcı verisi kendi klasöründe (ör. %APPDATA%\Matris Öğren, ~/.config/Matris Öğren).
// Varsayılan yol her sürümde uygulama adını içermediğinden açıkça verilir; hazır olmadan önce yapılmalıdır.
(function () {
  const klasor = path.join(app.getPath("appData"), UYGULAMA_ADI);
  app.setPath("userData", klasor);
  app.setPath("sessionData", klasor);
})();
if (process.platform === "win32") app.setAppUserModelId(UYGULAMA_KIMLIGI);
// Tarayıcı kimliğinde masaüstü çatısının ve uygulamanın belirteçleri görünmesin (yalnız standart tarayıcı kimliği kalır).
app.userAgentFallback = String(app.userAgentFallback || "")
  .replace(/\(KHTML, like Gecko\)\s+.*?\s*(?=Chrome\/)/, "(KHTML, like Gecko) ").replace(/\s+Electron\/\S+/gi, "");

protocol.registerSchemesAsPrivileged([{
  scheme: SEMA,
  privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true, codeCache: true },
}]);

// ------------------------------------------------------------------ durum
const oturum = Date.now().toString(36) + "-" + process.pid;
const pencereler = new Map();          // webContents.id → durum
const bekleyenAcilislar = [];          // hazır olmadan gelen dosya açma istekleri (macOS open-file, ilk argümanlar)
const kaydedilenYollar = new Set();    // klasordeGoster yalnız bunlara izin verir
const yazdirmaBelgeleri = new Map();   // app://matris/__yazdir/<anahtar>.html → HTML (PDF için)
let pencereSayac = 0;
let ayarlar = null;
let kurtarmaDeposu = null;
let uygulamaBilgisi = {};
let hazirMi = false;
let cikisIstendi = false;               // before-quit ile başlar; kaydedilmemiş pencere sorusu sırasında askıya alınır

function durumBul(pencere) {
  if (!pencere || pencere.isDestroyed()) return null;
  return pencereler.get(pencere.webContents.id) || null;
}

function odakDurumu() {
  const p = BrowserWindow.getFocusedWindow();
  const d = durumBul(p);
  if (d) return d;
  const hepsi = Array.from(pencereler.values());
  return hepsi.length ? hepsi[hepsi.length - 1] : null;
}

function yolAnahtari(yol) {
  const n = path.resolve(yol);
  return process.platform === "win32" || process.platform === "darwin" ? n.toLowerCase() : n;
}

function sonKlasor() {
  const k = ayarlar && ayarlar.al("sonKlasor");
  try { if (k && fs.statSync(k).isDirectory()) return k; } catch (e) { /* yok */ }
  return app.getPath("documents");
}

function klasoruHatirla(yol) {
  if (ayarlar && yol) ayarlar.koy("sonKlasor", path.dirname(yol));
}

function uzantiEkle(yol, filtreler) {
  if (!yol || path.extname(yol)) return yol;
  const ilk = (filtreler || []).find(function (f) { return f.extensions && f.extensions[0] && f.extensions[0] !== "*"; });
  return ilk ? yol + "." + ilk.extensions[0] : yol;
}

// ------------------------------------------------------------------ uygulama dosyalarının sunulması
function protokolKur() {
  protocol.handle(SEMA, async function (istek) {
    let url;
    try { url = new URL(istek.url); } catch (e) { return new Response("Geçersiz adres", { status: 400 }); }
    if (url.host !== KOK_HOST) return new Response("Bulunamadı", { status: 404 });
    const yazdir = /^\/__yazdir\/([0-9a-f]{32})\.html$/.exec(url.pathname);
    if (yazdir) {
      const html = yazdirmaBelgeleri.get(yazdir[1]);
      if (html == null) return new Response("Bulunamadı", { status: 404 });
      return new Response(html, { status: 200, headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline' " + KOK_URL + "; img-src data: blob: " + KOK_URL +
          "; font-src data: " + KOK_URL + "; script-src 'none'",
      } });
    }
    const y = await sunucu.yanitUret(UYGULAMA_KOK, istek.url);
    return new Response(y.govde, { status: y.durum, headers: y.basliklar });
  });
}

function oturumGuvenligi() {
  const ses = session.defaultSession;
  const izinli = new Set(["clipboard-sanitized-write", "clipboard-read", "fullscreen"]);
  ses.setPermissionRequestHandler(function (_wc, izin, cevap) { cevap(izinli.has(izin)); });
  ses.setPermissionCheckHandler(function (_wc, izin) { return izinli.has(izin); });
  // Sayfanın kendi indirmeleri (<a download>): yerel "Kaydet" iletişim kutusu son kullanılan klasörde açılır.
  ses.on("will-download", function (_olay, oge) {
    oge.setSaveDialogOptions({ title: "Kaydet", defaultPath: path.join(sonKlasor(), Y.guvenliAd(oge.getFilename(), "dosya")) });
    oge.once("done", function (_e, sonuc) {
      if (sonuc === "completed" && oge.getSavePath()) { kaydedilenYollar.add(oge.getSavePath()); klasoruHatirla(oge.getSavePath()); }
    });
  });
}

function icAdresMi(url) {
  return typeof url === "string" && (url.indexOf(KOK_URL) === 0 || url.indexOf("blob:" + KOK_URL) === 0 || url === "about:blank");
}

function hariciAc(url) {
  if (/^(https?:|mailto:)/i.test(String(url || ""))) shell.openExternal(String(url)).catch(function () { /* yoksay */ });
}

// Her web içeriği için: gömülü webview yok, uygulama dışına gezinme yok, http(s) varsayılan tarayıcıda.
app.on("web-contents-created", function (_olay, wc) {
  wc.on("will-attach-webview", function (e) { e.preventDefault(); });
  wc.on("will-navigate", function (e, url) {
    if (icAdresMi(url)) return;
    e.preventDefault();
    hariciAc(url);
  });
  wc.setWindowOpenHandler(function (ayrinti) {
    const url = ayrinti.url;
    if (/^(https?:|mailto:)/i.test(url)) { hariciAc(url); return { action: "deny" }; }
    if (icAdresMi(url)) {
      // Rapor önizlemesi ya da web yedeğindeki yazdırma penceresi: preload'suz, yalıtılmış, menüsüz pencere.
      return { action: "allow", overrideBrowserWindowOptions: {
        title: UYGULAMA_ADI, autoHideMenuBar: true, icon: simge(),
        webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false },
      } };
    }
    return { action: "deny" };
  });
  wc.on("did-create-window", function (yeni) {
    yeni.removeMenu();
    yeni.on("page-title-updated", function (e, baslik) { if (!baslik || baslik === "about:blank") e.preventDefault(); });
  });
});

let simgeOnbellek = null;
function simge() {
  if (!simgeOnbellek) { try { simgeOnbellek = nativeImage.createFromPath(SIMGE); } catch (e) { simgeOnbellek = undefined; } }
  return simgeOnbellek && !simgeOnbellek.isEmpty() ? simgeOnbellek : undefined;
}

// ------------------------------------------------------------------ pencereler
function baslikGuncelle(d) {
  if (!d || d.pencere.isDestroyed()) return;
  const ad = d.yol ? path.basename(d.yol) : (d.ad || (d.kirli ? "Adsız proje" : ""));
  d.pencere.setTitle((d.kirli ? "• " : "") + (ad ? ad + " — " : "") + UYGULAMA_ADI);
  if (process.platform === "darwin") {
    d.pencere.setRepresentedFilename(d.yol || "");
    d.pencere.setDocumentEdited(!!d.kirli);
  }
}

function pencereDurumunuKaydet(pencere) {
  if (!ayarlar || pencere.isDestroyed()) return;
  const b = pencere.isMaximized() || pencere.isFullScreen() ? pencere.getNormalBounds() : pencere.getBounds();
  ayarlar.koy("pencere", { x: b.x, y: b.y, width: b.width, height: b.height, buyuk: pencere.isMaximized(), tamEkran: pencere.isFullScreen() });
}

function pencereAc() {
  const kayitli = ayarlar.al("pencere");
  const ekranlar = screen.getAllDisplays().map(function (e) { return e.workArea; });
  let sinir = Y.pencereSiniri(kayitli, ekranlar, { width: 1440, height: 920 });
  const onceki = BrowserWindow.getFocusedWindow() || Array.from(pencereler.values()).map(function (d) { return d.pencere; }).pop();
  if (onceki && !onceki.isDestroyed()) {
    const b = onceki.getBounds();
    sinir = Y.pencereSiniri({ x: b.x + 28, y: b.y + 28, width: b.width, height: b.height }, ekranlar, sinir);
  }
  const ilk = pencereler.size === 0;
  const pencere = new BrowserWindow(Object.assign({}, sinir, {
    minWidth: 760, minHeight: 520, show: false, title: UYGULAMA_ADI, icon: simge(),
    backgroundColor: nativeTheme.shouldUseDarkColors ? "#0f172a" : "#f3f6fb",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true, sandbox: true, nodeIntegration: false, nodeIntegrationInWorker: false, webSecurity: true,
      spellcheck: false, additionalArguments: ["--matris-surum=" + app.getVersion()],
    },
  }));
  const d = {
    no: ++pencereSayac, pencere: pencere, wcId: pencere.webContents.id, yol: null, ad: null, kirli: false, hazir: false, kuyruk: [],
    kapatOnay: false, kapatBekliyor: false, kurtarmaBekliyor: false, kurtarmaSil: false, cikisIcin: false, soruAcik: false,
    kisayollar: null,                   // Bina sayfasının son gönderdiği kısayol listesi (matris:kisayollar); pencereyle birlikte silinir
  };
  pencereler.set(d.wcId, d);

  pencere.once("ready-to-show", function () {
    if (ilk && kayitli && kayitli.buyuk) pencere.maximize();
    pencere.show();
    if (ilk && kayitli && kayitli.tamEkran) pencere.setFullScreen(true);
  });
  pencere.on("page-title-updated", function (e) { e.preventDefault(); });
  ["resize", "move", "maximize", "unmaximize", "enter-full-screen", "leave-full-screen"].forEach(function (olay) {
    pencere.on(olay, function () { pencereDurumunuKaydet(pencere); });
  });
  pencere.on("close", function (e) { kapatmaIstegi(e, d); });
  // Windows oturumu kapanırken soru sorulmaz; otomatik kayıt bir sonraki açılışta kurtarılmak üzere kalır.
  pencere.on("session-end", function () { d.kapatOnay = true; });
  pencere.on("closed", function () {
    pencereler.delete(d.wcId);
    if (!d.kirli || d.kurtarmaSil) kurtarmaDeposu.sil(oturum, d.no);
    // Çıkış sırasında soru sorulan pencere kapandıysa çıkış kalan pencerelerle sürer.
    if (d.cikisIcin) setImmediate(function () { app.quit(); });
  });

  const wc = pencere.webContents;
  wc.on("did-start-navigation", function (ayrinti) {
    if (!ayrinti || !ayrinti.isMainFrame || ayrinti.isSameDocument) return;
    if (d.hazir && d.kirli) d.kurtarmaBekliyor = true;   // yeniden yükleme: son otomatik kayıt geri verilir
    d.hazir = false;
    d.kisayollar = null;                // yeni belge: Bina sayfası hazır olunca listeyi yeniden gönderir
  });
  wc.on("render-process-gone", function (_e, ayrinti) {
    if (!ayrinti || ayrinti.reason === "clean-exit" || pencere.isDestroyed()) return;
    d.hazir = false;
    d.kurtarmaBekliyor = true;
    dialog.showMessageBox(pencere, {
      type: "error", title: UYGULAMA_ADI, buttons: ["Yeniden yükle", "Pencereyi kapat"], defaultId: 0, cancelId: 1, noLink: true,
      message: "Pencere içeriği beklenmedik biçimde kapandı.",
      detail: "Son otomatik kayıt yeniden yüklemeden sonra geri getirilir. (Neden: " + ayrinti.reason + ")",
    }).then(function (r) {
      if (pencere.isDestroyed()) return;
      if (r.response === 0) wc.reload(); else { d.kapatOnay = true; pencere.close(); }   // kayıt bir sonraki açılışta kurtarılabilir
    });
  });

  baslikGuncelle(d);
  pencere.loadURL(KOK_URL + "index.html");
  return d;
}

function kapatmaIstegi(e, d) {
  if (d.kapatOnay || !d.kirli) return;
  e.preventDefault();               // (çıkış sürüyorsa çıkış da durur; yanıta göre yeniden başlatılır)
  if (d.soruAcik) return;
  d.soruAcik = true;
  const kayitliCikis = cikisIstendi;
  cikisIstendi = false;
  const ad = d.yol ? path.basename(d.yol) : (d.ad || "Adsız proje");
  dialog.showMessageBox(d.pencere, {
    type: "warning", title: UYGULAMA_ADI, buttons: ["Kaydet", "Kaydetme", "Vazgeç"], defaultId: 0, cancelId: 2, noLink: true,
    message: "“" + ad + "” içindeki değişiklikler kaydedilsin mi?",
    detail: "Kaydetmezseniz son değişiklikler kaybolur.",
  }).then(function (r) {
    d.soruAcik = false;
    if (d.pencere.isDestroyed()) return;
    if (r.response === 0) {
      d.kapatBekliyor = true;
      d.cikisIcin = kayitliCikis;
      komutGonder(d, "kaydet", { kapatmak: true });
    } else if (r.response === 1) {
      d.kapatOnay = true;
      d.kurtarmaSil = true;
      d.cikisIcin = kayitliCikis;
      d.pencere.close();
    }
  });
}

function komutGonder(d, ad, ek) {
  if (!d || d.pencere.isDestroyed()) return;
  if (!d.hazir) return;
  d.pencere.webContents.send("matris:komut", Object.assign({ komut: ad }, ek || {}));
}

function dosyaGonder(d, veri) {
  if (!d || d.pencere.isDestroyed()) return;
  if (d.hazir) d.pencere.webContents.send("matris:dosya-acildi", veri);
  else d.kuyruk.push(veri);
}

function hazirOldu(d) {
  d.hazir = true;
  if (d.kurtarmaBekliyor) {
    d.kurtarmaBekliyor = false;
    const k = kurtarmaDeposu.oku(oturum, d.no);
    if (k && k.icerik) d.kuyruk.unshift({ ad: k.ad || (d.yol ? path.basename(d.yol) : "Kurtarılan proje"), yol: d.yol || k.yol || null, icerik: k.icerik, kurtarma: true });
  }
  d.kuyruk.splice(0).forEach(function (v) { d.pencere.webContents.send("matris:dosya-acildi", v); });
  baslikGuncelle(d);
}

// ------------------------------------------------------------------ dosyalar
function sonDosyaKaydet(yol) {
  ayarlar.koy("sonDosyalar", Y.sonDosyaEkle(ayarlar.al("sonDosyalar"), yol, 10));
  klasoruHatirla(yol);
  try { app.addRecentDocument(yol); } catch (e) { /* desteklenmiyor */ }
  menuKur();
}

// Bir proje dosyasını açar: dosya zaten bir pencerede açıksa o pencere öne gelir; hedef pencere kaydedilmemiş
// değişiklik içeriyorsa (ya da hedef yoksa) yeni pencere açılır.
function dosyaAc(yol, hedef) {
  if (!hazirMi) { bekleyenAcilislar.push(yol); return; }
  let veri;
  try { veri = Y.projeOku(yol); }
  catch (e) {
    dialog.showMessageBox(hedef && !hedef.pencere.isDestroyed() ? hedef.pencere : undefined, {
      type: "error", title: UYGULAMA_ADI, message: "Dosya açılamadı", detail: String(e && e.message ? e.message : e), buttons: ["Tamam"], noLink: true,
    });
    const liste = (ayarlar.al("sonDosyalar") || []).filter(function (y) { return yolAnahtari(y) !== yolAnahtari(yol); });
    ayarlar.koy("sonDosyalar", liste);
    menuKur();
    return;
  }
  const anahtar = yolAnahtari(veri.yol);
  const acik = Array.from(pencereler.values()).find(function (d) { return d.yol && yolAnahtari(d.yol) === anahtar; });
  if (acik) {
    if (acik.pencere.isMinimized()) acik.pencere.restore();
    acik.pencere.focus();
    return;
  }
  let d = hedef && !hedef.pencere.isDestroyed() && !hedef.kirli ? hedef : null;
  if (!d) d = pencereAc();
  d.yol = veri.yol;
  d.kirli = false;
  sonDosyaKaydet(veri.yol);
  baslikGuncelle(d);
  dosyaGonder(d, { ad: veri.ad, yol: veri.yol, icerik: veri.icerik });
  d.pencere.focus();
}

async function acIletisimi(d) {
  const r = await dialog.showOpenDialog(d && !d.pencere.isDestroyed() ? d.pencere : undefined, {
    title: "Proje aç", defaultPath: sonKlasor(), properties: ["openFile", "multiSelections"],
    filters: [{ name: "Proje dosyaları", extensions: ["matris", "json"] }].concat(PROJE_FILTRELERI, [{ name: "Tüm dosyalar", extensions: ["*"] }]),
  });
  if (r.canceled || !r.filePaths.length) return;
  r.filePaths.forEach(function (yol, i) { dosyaAc(yol, i === 0 ? d : null); });
}

async function dosyayaYaz(yol, icerik) {
  const veri = typeof icerik === "string" ? icerik : Buffer.from(icerik.buffer, icerik.byteOffset, icerik.byteLength);
  if (veri.length > EN_BUYUK_KAYIT) throw new Error("Dosya çok büyük.");
  Y.atomikYaz(yol, veri);
  kaydedilenYollar.add(yol);
  klasoruHatirla(yol);
}

function hataGoster(d, baslik, e) {
  dialog.showMessageBox(d && !d.pencere.isDestroyed() ? d.pencere : undefined, {
    type: "error", title: UYGULAMA_ADI, message: baslik, detail: String(e && e.message ? e.message : e), buttons: ["Tamam"], noLink: true,
  });
}

// ------------------------------------------------------------------ PDF
async function pdfUret(html, baslik) {
  const anahtar = crypto.randomBytes(16).toString("hex");
  yazdirmaBelgeleri.set(anahtar, Y.htmlBasligiEkle(html, baslik));
  const gizli = new BrowserWindow({
    show: false, width: 1100, height: 1500,
    webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false, javascript: false, spellcheck: false },
  });
  try {
    await gizli.loadURL(KOK_URL + "__yazdir/" + anahtar + ".html");
    const pdf = await gizli.webContents.printToPDF({
      pageSize: "A4", printBackground: true, preferCSSPageSize: true, generateTaggedPDF: true, generateDocumentOutline: true,
    });
    return Y.pdfUreticiBilgisiniSil(pdf);
  } finally {
    yazdirmaBelgeleri.delete(anahtar);
    if (!gizli.isDestroyed()) gizli.destroy();
  }
}

// ------------------------------------------------------------------ IPC (yalnız kendi pencerelerimizden ve uygulama adresinden)
function gonderen(olay) {
  const d = pencereler.get(olay.sender.id);
  if (!d) return null;
  const cerceve = olay.senderFrame;
  if (!cerceve || String(cerceve.url || "").indexOf(KOK_URL) !== 0) return null;
  return d;
}

function ipcKur() {
  ipcMain.handle("matris:kaydet", async function (olay, s) {
    const d = gonderen(olay);
    if (!d || !s) return null;
    const filtreler = Y.suzgecler((s.filtreler || []).map(function (f) { return { ad: f.ad, uzantilar: f.uzantilar }; }));
    const r = await dialog.showSaveDialog(d.pencere, {
      title: s.baslik || "Dışa aktar", defaultPath: path.join(sonKlasor(), Y.guvenliAd(s.ad, "dosya")), filters: filtreler,
      properties: ["createDirectory", "showOverwriteConfirmation"],
    });
    if (r.canceled || !r.filePath) return null;
    const yol = uzantiEkle(r.filePath, filtreler);
    try { await dosyayaYaz(yol, s.icerik); } catch (e) { hataGoster(d, "Dosya kaydedilemedi", e); return null; }
    return { ad: path.basename(yol), yol: yol };
  });

  ipcMain.handle("matris:ac", async function (olay, s) {
    const d = gonderen(olay);
    if (!d) return null;
    const r = await dialog.showOpenDialog(d.pencere, {
      title: (s && s.baslik) || "Dosya aç", defaultPath: sonKlasor(), properties: ["openFile"],
      filters: Y.suzgecler(((s && s.filtreler) || []).map(function (f) { return { ad: f.ad, uzantilar: f.uzantilar }; })),
    });
    if (r.canceled || !r.filePaths.length) return null;
    const yol = r.filePaths[0];
    try {
      const bilgi = fs.statSync(yol);
      if (bilgi.size > EN_BUYUK_KAYIT) throw new Error("Dosya çok büyük (" + Math.round(bilgi.size / 1048576) + " MB).");
      klasoruHatirla(yol);
      if (s && s.ikili) return { ad: path.basename(yol), yol: yol, icerik: new Uint8Array(fs.readFileSync(yol)) };
      let metin = fs.readFileSync(yol, "utf8");
      if (metin.charCodeAt(0) === 0xfeff) metin = metin.slice(1);
      return { ad: path.basename(yol), yol: yol, icerik: metin };
    } catch (e) { hataGoster(d, "Dosya açılamadı", e); return null; }
  });

  ipcMain.handle("matris:proje-kaydet", async function (olay, s) {
    const d = gonderen(olay);
    if (!d || !s) return null;
    let yol = !s.farkli && d.yol ? d.yol : null;
    if (!yol) {
      const onerilen = Y.guvenliAd(String(s.ad || "").replace(/\.(matris|json)$/i, ""), "proje") + ".matris";
      const r = await dialog.showSaveDialog(d.pencere, {
        title: s.farkli ? "Farklı kaydet" : "Projeyi kaydet",
        defaultPath: d.yol ? path.join(path.dirname(d.yol), path.basename(d.yol)) : path.join(sonKlasor(), onerilen),
        filters: PROJE_FILTRELERI, properties: ["createDirectory", "showOverwriteConfirmation"],
      });
      if (r.canceled || !r.filePath) { d.kapatBekliyor = false; d.cikisIcin = false; return null; }
      yol = uzantiEkle(r.filePath, PROJE_FILTRELERI);
    }
    try { await dosyayaYaz(yol, String(s.icerik == null ? "" : s.icerik)); }
    catch (e) { d.kapatBekliyor = false; d.cikisIcin = false; hataGoster(d, "Proje kaydedilemedi", e); return null; }
    d.yol = yol;
    d.kirli = false;
    kurtarmaDeposu.sil(oturum, d.no);
    sonDosyaKaydet(yol);
    baslikGuncelle(d);
    if (d.kapatBekliyor) {
      d.kapatBekliyor = false;
      d.kapatOnay = true;
      setImmediate(function () { if (!d.pencere.isDestroyed()) d.pencere.close(); });
    }
    return { ad: path.basename(yol), yol: yol };
  });

  ipcMain.handle("matris:proje-ac", async function (olay) {
    const d = gonderen(olay);
    if (!d) return null;
    const r = await dialog.showOpenDialog(d.pencere, {
      title: "Proje aç", defaultPath: sonKlasor(), properties: ["openFile"],
      filters: [{ name: "Proje dosyaları", extensions: ["matris", "json"] }].concat(PROJE_FILTRELERI),
    });
    if (r.canceled || !r.filePaths.length) return null;
    try {
      const veri = Y.projeOku(r.filePaths[0]);
      d.yol = veri.yol;
      d.kirli = false;
      sonDosyaKaydet(veri.yol);
      baslikGuncelle(d);
      return veri;
    } catch (e) { hataGoster(d, "Proje açılamadı", e); return null; }
  });

  ipcMain.handle("matris:pdf", async function (olay, s) {
    const d = gonderen(olay);
    if (!d || !s || !s.html) return null;
    const filtre = [{ name: "PDF belgesi", extensions: ["pdf"] }];
    const r = await dialog.showSaveDialog(d.pencere, {
      title: "PDF olarak kaydet", defaultPath: path.join(sonKlasor(), Y.guvenliAd(String(s.ad || "rapor").replace(/\.pdf$/i, ""), "rapor") + ".pdf"),
      filters: filtre, properties: ["createDirectory", "showOverwriteConfirmation"],
    });
    if (r.canceled || !r.filePath) return null;
    const yol = uzantiEkle(r.filePath, filtre);
    try {
      const pdf = await pdfUret(String(s.html), path.basename(yol, ".pdf"));
      await dosyayaYaz(yol, pdf);
    } catch (e) { hataGoster(d, "PDF oluşturulamadı", e); return null; }
    return { ad: path.basename(yol), yol: yol };
  });

  ipcMain.on("matris:klasorde-goster", function (olay, yol) {
    if (gonderen(olay) && kaydedilenYollar.has(yol)) shell.showItemInFolder(yol);
  });
  ipcMain.on("matris:kirli", function (olay, kirli) {
    const d = gonderen(olay);
    if (!d) return;
    d.kirli = !!kirli;
    if (!d.kirli) kurtarmaDeposu.sil(oturum, d.no);
    baslikGuncelle(d);
  });
  ipcMain.on("matris:yeni", function (olay) {
    const d = gonderen(olay);
    if (!d) return;
    d.yol = null;
    d.ad = null;
    d.kirli = false;
    kurtarmaDeposu.sil(oturum, d.no);
    baslikGuncelle(d);
  });
  ipcMain.on("matris:otomatik-kayit", function (olay, s) {
    const d = gonderen(olay);
    if (!d || !s || typeof s.icerik !== "string" || !s.icerik || s.icerik.length > 64 * 1024 * 1024) return;
    if (s.ad && !d.yol && d.ad !== s.ad) { d.ad = String(s.ad).slice(0, 150); baslikGuncelle(d); }
    try { kurtarmaDeposu.yaz(oturum, d.no, { ad: s.ad || (d.yol ? path.basename(d.yol) : null), yol: d.yol, icerik: s.icerik }); }
    catch (e) { /* disk dolu vb.: sessiz geç */ }
  });
  ipcMain.on("matris:hazir", function (olay) { const d = gonderen(olay); if (d) hazirOldu(d); });
  // Bina sayfasının kısayol listesi (araç kutusu komut kaydı + sayfa tuşları; Yardım › Klavye kısayolları penceresi için)
  ipcMain.on("matris:kisayollar", function (olay, liste) {
    const d = gonderen(olay);
    if (!d) return;
    const temiz = kisayolListesiTemizle(liste);
    d.kisayollar = temiz.length ? temiz : null;
  });
  ipcMain.on("matris:tam-ekran", function (olay) { const d = gonderen(olay); if (d) d.pencere.setFullScreen(!d.pencere.isFullScreen()); });
  ipcMain.on("matris:yeni-pencere", function (olay) { if (gonderen(olay)) pencereAc(); });
  ipcMain.on("matris:harici", function (olay, url) { if (gonderen(olay)) hariciAc(url); });
  ipcMain.on("matris:birakilan", function (olay, yollar) {
    const d = gonderen(olay);
    if (!d || !Array.isArray(yollar)) return;
    yollar.slice(0, 16).filter(function (y) { return typeof y === "string" && Y.projeDosyasiMi(y); })
      .forEach(function (y, i) { dosyaAc(y, i === 0 ? d : null); });
  });
}

// ------------------------------------------------------------------ menü
function menuKur() {
  const sablon = menuSablonu({
    platform: process.platform,
    uygulamaAdi: UYGULAMA_ADI,
    sonDosyalar: (ayarlar && ayarlar.al("sonDosyalar")) || [],
    komut: function (ad, ek, pencere) {
      let d = durumBul(pencere) || odakDurumu();
      if (!d) { if (ad !== "yeni") return; d = pencereAc(); return; }
      komutGonder(d, ad, ek);
    },
    yerel: {
      ac: function (pencere) { acIletisimi(durumBul(pencere) || odakDurumu()); },
      yeniPencere: function () { pencereAc(); },
      sonDosyaAc: function (yol, pencere) { dosyaAc(yol, durumBul(pencere) || odakDurumu()); },
      sonDosyalariTemizle: function () {
        ayarlar.koy("sonDosyalar", []);
        try { app.clearRecentDocuments(); } catch (e) { /* yoksay */ }
        menuKur();
      },
      kurtarmaKlasoru: function () {
        fs.mkdirSync(kurtarmaDeposu.klasor, { recursive: true });
        shell.openPath(kurtarmaDeposu.klasor);
      },
      tamEkran: function (pencere) {
        const p = pencere || BrowserWindow.getFocusedWindow();
        if (p && !p.isDestroyed()) p.setFullScreen(!p.isFullScreen());
      },
      // menü kısayolları + (Bina sayfası hazırsa) o pencerenin gönderdiği sayfa kısayolları; liste yoksa yönlendiren eski metin
      kisayollar: function (pencere) {
        const d = durumBul(pencere) || odakDurumu();
        dialog.showMessageBox(pencere || undefined, {
          type: "info", title: "Klavye kısayolları", message: "Klavye kısayolları",
          detail: kisayolMetni(process.platform, d ? d.kisayollar : null), buttons: ["Tamam"], noLink: true,
        });
      },
      harici: hariciAc,
      hakkinda: function (pencere) { hakkinda(pencere); },
    },
  });
  Menu.setApplicationMenu(Menu.buildFromTemplate(sablon));
}

function hakkinda(pencere) {
  const b = uygulamaBilgisi || {};
  const satirlar = ["Sürüm " + app.getVersion() + (b.icerik_surumu ? " (içerik " + b.icerik_surumu + ")" : "")];
  if (b.pyodide && b.pyodide.surum) {
    satirlar.push("Hesap motoru: Python + sympy + numpy (Pyodide " + b.pyodide.surum + "), bu bilgisayarda çevrimdışı çalışır.");
  }
  satirlar.push("", "Matris işlemleri, sonlu elemanlar ve yapı analizi için öğretici program: dersler, adım adım çözümler,",
    "aks tabanlı 3B bina modeli, TS 498 / TS 500 / ÇYTHYE / TBDY 2018 tabanlı hesap hattı, statik rapor ve IFC dışa aktarımı.",
    "", "Hesaplar eğitim amaçlıdır; mühendislik kararlarında yetkili bir mühendisin denetimi gerekir.");
  dialog.showMessageBox(pencere || undefined, {
    type: "info", title: UYGULAMA_ADI + " hakkında", message: UYGULAMA_ADI, detail: satirlar.join("\n"), icon: simge(),
    buttons: ["Tamam"], noLink: true,
  });
}

// ------------------------------------------------------------------ kurtarma
async function kurtarmaSor() {
  const artiklar = kurtarmaDeposu.artiklar(oturum).slice(0, 12);
  if (!artiklar.length) return;
  const liste = artiklar.map(function (k) {
    return "• " + (k.ad || (k.yol ? path.basename(k.yol) : "Adsız proje")) + "  (" + String(k.zaman || "").replace("T", " ").slice(0, 16) + ")";
  }).join("\n");
  const r = await dialog.showMessageBox({
    type: "warning", title: UYGULAMA_ADI, buttons: ["Kurtar", "Sil", "Sonra karar ver"], defaultId: 0, cancelId: 2, noLink: true,
    message: "Önceki oturum beklenmedik biçimde kapanmış.",
    detail: "Kaydedilmemiş " + artiklar.length + " çalışma bulundu:\n" + liste + "\n\nKurtarılan çalışmalar ayrı pencerelerde açılır; kaydetmeyi unutmayın.",
  });
  if (r.response === 1) { artiklar.forEach(function (k) { kurtarmaDeposu.at(k); }); return; }
  if (r.response !== 0) return;
  artiklar.forEach(function (k) {
    const d = pencereAc();
    d.yol = k.yol && fs.existsSync(k.yol) ? k.yol : null;
    d.ad = k.ad || null;
    d.kirli = true;
    try { kurtarmaDeposu.yaz(oturum, d.no, k); kurtarmaDeposu.at(k); } catch (e) { /* eski kayıt kalır */ }
    baslikGuncelle(d);
    dosyaGonder(d, { ad: k.ad || (d.yol ? path.basename(d.yol) : "Kurtarılan proje"), yol: d.yol, icerik: k.icerik, kurtarma: true });
  });
}

// ------------------------------------------------------------------ başlangıç
function uygulamaVarMi() {
  if (fs.existsSync(path.join(UYGULAMA_KOK, "index.html"))) return true;
  dialog.showErrorBox(UYGULAMA_ADI, "Uygulama dosyaları bulunamadı:\n" + UYGULAMA_KOK + "\n\nGeliştirme ortamında önce `npm run hazirla` çalıştırın.");
  return false;
}

function baslat() {
  process.on("uncaughtException", function (e) {
    console.error(e);
    try { dialog.showErrorBox(UYGULAMA_ADI + " — beklenmeyen hata", String(e && e.stack ? e.stack : e)); } catch (e2) { /* yoksay */ }
  });

  app.on("second-instance", function (_olay, argv, cwd) {
    const dosyalar = Y.dosyaArgumanlari(argv.slice(1), cwd);
    if (dosyalar.length) { dosyalar.forEach(function (y) { dosyaAc(y, null); }); return; }
    const d = odakDurumu();
    if (!d) { if (hazirMi) pencereAc(); return; }
    if (d.pencere.isMinimized()) d.pencere.restore();
    d.pencere.focus();
  });

  app.on("open-file", function (olay, yol) {      // macOS: Finder'dan aç / simgeye bırak
    olay.preventDefault();
    if (hazirMi) dosyaAc(yol, null); else bekleyenAcilislar.push(yol);
  });

  app.on("before-quit", function () {
    cikisIstendi = true;
    if (ayarlar) ayarlar.kaydetSimdi();
  });
  app.on("window-all-closed", function () {
    if (process.platform !== "darwin") app.quit();
  });
  app.on("activate", function () {
    if (hazirMi && pencereler.size === 0) pencereAc();
  });

  app.whenReady().then(function () {
    const veri = app.getPath("userData");
    ayarlar = Y.depo(path.join(veri, "ayarlar.json"), { sonDosyalar: [], pencere: null, sonKlasor: null });
    kurtarmaDeposu = Y.kurtarma(path.join(veri, "kurtarma"));
    try { uygulamaBilgisi = JSON.parse(fs.readFileSync(path.join(UYGULAMA_KOK, "masaustu.json"), "utf8")); } catch (e) { uygulamaBilgisi = {}; }
    if (process.platform === "darwin") {
      app.setAboutPanelOptions({ applicationName: UYGULAMA_ADI, applicationVersion: app.getVersion(), version: "", credits: "", copyright: UYGULAMA_ADI });
    }
    oturumGuvenligi();
    protokolKur();
    ipcKur();
    menuKur();
    if (!uygulamaVarMi()) { app.quit(); return; }
    hazirMi = true;
    const dosyalar = Y.dosyaArgumanlari(process.argv.slice(1), process.cwd()).concat(bekleyenAcilislar.splice(0));
    if (dosyalar.length) dosyalar.forEach(function (y) { dosyaAc(y, null); });
    else pencereAc();
    kurtarmaSor();
  });
}

if (!app.requestSingleInstanceLock()) app.quit();
else baslat();
