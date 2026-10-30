# -*- coding: utf-8 -*-
"""Tablo editörü CSV içe aktarma ve sayfa kısayolları: tarayıcı testi (sözleşmeler C22, C23, C24).

Sayfa gerçek tarayıcıda (başsız) açılır; motor Pyodide yerine CPython'da çalışır: ``testler/tarayici_sunucu.py`` alt süreci
``docs/`` klasörünü sunar ve ``/motor.worker.js`` yerine istekleri ``web_kopru.calistir``'a ileten ara worker verir. Yardımcılar
``testler/test_bina_tarayici.py``'den kopyalanmıştır (o modül içe aktarılmaz; sözleşme C24).

1. Tablolar penceresinde (betonarme-2kat-3x2) "CSV ▾ › Bu tablo" ile indirilen dosyada bir düzenlenebilir değer değiştirilir ve
   editörün kendi "İçe aktar (.csv)…" düğmesiyle (gizli input[type=file]) geri okunur: hücre sarı (bekleyen), model değişmez;
   Uygula modeli değiştirir, Ctrl+Z geri alır. Bölümlü "Bütün tablolar — tek CSV" dosyası başka tablodaki değişikliği o tabloya
   yazar, tanınmayan sütunu uyarır; Geri al bekleyenleri tek adımda kaldırır.
2. Masaüstü yolu (sahte window.masaustu): Dosya › İçe aktar › Tablolar (.csv)… komutu (``csv-iceri``) editörü açar ve hemen yerel
   "Aç" iletişim kutusundan (MatrisDosya.ac(["csv"])) dosyayı okur. bina.js'in C23 tarafı (tablolarAc(undefined, {csvIceri: true}),
   bina-sayfa paketi) gerekir.
3. Bina "?" kısayol penceresinin satırları (Sayfa ve araç grubu başlıkları) Yardım sayfasının kısayol tablosuyla aynı tuşlarda aynı
   (tuş, komut, grup) satırlarıdır; ikisinde de Enter var. MatrisArac.SAYFA_TUSLARI ve bina.js kisayolPenceresi (C22, bina-sayfa
   paketi) gerekir.
Herhangi bir sayfa hatası (pageerror) ya da konsol hatası testi düşürür (engellenen ağ / service worker iletileri hariç).

Playwright Python paketi ve bir Chromium yoksa atlanır (MATRIS_CHROMIUM, /opt/pw-browsers/chromium ya da
/opt/pw-browsers/chromium-*/chrome-linux*/chrome).
"""
from __future__ import annotations

import csv
import glob
import io
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent

try:
    from playwright.sync_api import sync_playwright
except ImportError:          # pragma: no cover - ortamda yoksa
    sync_playwright = None


def _tarayici_yolu():
    adaylar = [os.environ.get("MATRIS_CHROMIUM") or "", "/opt/pw-browsers/chromium"] + sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    return next((a for a in adaylar if a and os.path.isfile(a) and os.access(a, os.X_OK)), None)


TARAYICI = _tarayici_yolu()
pytestmark = pytest.mark.skipif(sync_playwright is None or TARAYICI is None, reason="playwright ya da Chromium yok")

# ağ erişimi olmayan ortamda beklenen konsol iletileri (yazı tipi / CDN istekleri, service worker kaydı)
YOKSAY = ("net::ERR", "Failed to load resource", "service worker", "Service Worker", "ServiceWorker")

SABLON = "betonarme-2kat-3x2"


@pytest.fixture(scope="module")
def sunucu():
    p = subprocess.Popen([sys.executable, "-I", str(PROJE / "testler" / "tarayici_sunucu.py"), str(PROJE), "0"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    satir = {}
    okuyucu = threading.Thread(target=lambda: satir.setdefault("v", p.stdout.readline()), daemon=True)
    okuyucu.start()
    okuyucu.join(60)
    try:
        if not satir.get("v", "").startswith("HAZIR "):
            p.kill()
            pytest.fail("test sunucusu başlamadı: " + (p.stderr.read() or "")[-2000:])
        yield satir["v"].split()[1]
    finally:
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()


@pytest.fixture(scope="module")
def tarayici():
    with sync_playwright() as pw:
        t = pw.chromium.launch(executable_path=TARAYICI)
        try:
            yield t
        finally:
            t.close()


def _sayfa_ac(tarayici, sunucu, en=1440, boy=900, on_betik=None, indirme=False):
    """Yeni bağlam (boş localStorage: varsayılan araç kutusu yerleşimi) ve Bina sayfası. on_betik: sayfa betiklerinden önce çalışan
    betik (ör. sahte masaüstü yüzeyi)."""
    ctx = tarayici.new_context(service_workers="block", viewport={"width": en, "height": boy}, accept_downloads=indirme)
    if on_betik:
        ctx.add_init_script(on_betik)
    pg = ctx.new_page()
    hatalar = []
    pg.on("pageerror", lambda e: hatalar.append("pageerror: " + str(e)))
    pg.on("console", lambda m: hatalar.append("console: " + m.text)
          if m.type == "error" and not any(y in m.text for y in YOKSAY) else None)
    pg.on("dialog", lambda d: d.accept())
    pg.set_default_timeout(120_000)
    pg.goto(sunucu + "index.html")
    pg.click("button[data-sayfa='bina']")
    pg.wait_for_function("window.MatrisBina && MatrisBina.hazir()")
    return ctx, pg, hatalar


def _sablon(pg, ad):
    # aynı şablon yeniden seçilse de change olayı oluşsun
    pg.evaluate("window.__oncekiBina = MatrisBina.bina(); document.querySelector('select#bn-sablon').value = ''")
    pg.select_option("select#bn-sablon", ad)
    pg.wait_for_function("MatrisBina.bina() && MatrisBina.bina() !== window.__oncekiBina && document.querySelector('select#bn-sablon').value === "
                         + json.dumps(ad))
    pg.wait_for_timeout(300)


def _coz(pg):
    return pg.evaluate("MatrisBina.coz()")


def _hatasiz(hatalar, adim):
    assert not hatalar, f"{adim}: " + " | ".join(hatalar)[:3000]


# ---------------------------------------------------------------------------------------------------------------- yardımcılar
def _csv_oku(metin: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(metin.lstrip("﻿"), newline=""), delimiter=";"))


def _csv_yaz(satirlar: list[list[str]]) -> bytes:
    cikti = io.StringIO(newline="")
    csv.writer(cikti, delimiter=";", lineterminator="\r\n").writerows(satirlar)
    return ("﻿" + cikti.getvalue()).encode("utf-8")


def _doseme_h(pg, no=1):
    return pg.evaluate(f"(MatrisBina.bina().dosemeler || []).find(d => d.no === {no}).h")


def _tablolar_ac(pg, ad):
    pg.evaluate(f"MatrisBina.tablolarAc({json.dumps(ad)})")
    pg.wait_for_selector(".bn-kaplama[data-kaplama='tablolar'] .tablo-ed .tablo-ed-tablo tbody tr[data-r]")
    pg.wait_for_function("document.querySelector('.tablo-ed .tablo-ed-oge.aktif') && document.querySelector('.tablo-ed .tablo-ed-oge.aktif').dataset.ad === "
                         + json.dumps(ad))


def _sari_hucreler(pg):
    return pg.evaluate("""() => Array.from(document.querySelectorAll('.tablo-ed td.tablo-ed-degisti')).map(td => ({
        metin: td.textContent, baslik: td.getAttribute('title') || '', sutun: +td.dataset.c,
        satir: td.closest('tr').querySelector('th.tablo-ed-no').textContent}))""")


def _mesaj(pg):
    return pg.evaluate("(document.querySelector('.tablo-ed .tablo-ed-mesaj') || {}).textContent || ''")


# ---------------------------------------------------------------------------------------------------------------- 1. tarayıcı yolu
def test_csv_ice_aktarma_editor_dugmesiyle(tarayici, sunucu, tmp_path):
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, indirme=True)
    try:
        _sablon(pg, SABLON)
        h0 = _doseme_h(pg)
        assert h0 == pytest.approx(0.14), h0
        _tablolar_ac(pg, "dosemeler")
        dugme = pg.locator(".tablo-ed .tablo-ed-csv-iceri")
        assert dugme.inner_text() == "İçe aktar (.csv)…"
        girdi = pg.evaluate("""() => { const g = document.querySelector('.tablo-ed input.tablo-ed-csv-dosya');
            return g && {tur: g.type, kabul: g.accept, gizli: g.hidden}; }""")
        assert girdi == {"tur": "file", "kabul": ".csv,text/csv", "gizli": True}
        # buton CSV ▾ menüsünün yanında
        assert pg.evaluate("document.querySelector('.tablo-ed .tablo-ed-menu').nextElementSibling.classList.contains('tablo-ed-csv-iceri')")

        # var olan dışa aktarma yolu: CSV ▾ › Bu tablo (görünen satırlar)
        pg.click(".tablo-ed .tablo-ed-csv-d")
        with pg.expect_download() as indirilen:
            pg.click(".tablo-ed [data-csv='bu']")
        metin = Path(indirilen.value.path()).read_text(encoding="utf-8")
        assert metin.startswith("﻿")
        satirlar = _csv_oku(metin)
        bas = satirlar[0]
        assert bas[0] == "No" and "Kalınlık t [m]" in bas, bas
        i_no, i_h = bas.index("No"), bas.index("Kalınlık t [m]")
        hedef = next(r for r in satirlar[1:] if r and r[i_no] == "1")
        assert hedef[i_h] == "0,14", hedef
        hedef[i_h] = "0,18"
        dosya = tmp_path / indirilen.value.suggested_filename
        dosya.write_bytes(_csv_yaz(satirlar))

        # editörün kendi düğmesi → dosya seçici → gizli girdi
        with pg.expect_file_chooser() as secici:
            dugme.click()
        assert secici.value.element.get_attribute("accept") == ".csv,text/csv"
        secici.value.set_files(str(dosya))
        pg.wait_for_function("document.querySelectorAll('.tablo-ed td.tablo-ed-degisti').length === 1")
        sari = _sari_hucreler(pg)
        assert sari[0]["satir"] == "1" and float(sari[0]["metin"].replace(",", ".")) == pytest.approx(0.18), sari
        assert "Önceki:" in sari[0]["baslik"], sari
        assert "CSV: 1 değişiklik bekliyor (Uygula), 0 uyarı" in _mesaj(pg), _mesaj(pg)
        assert "CSV: 1 değişiklik bekliyor (Uygula), 0 uyarı" in pg.text_content("#toast-metin")
        assert pg.inner_text(".tablo-ed .tablo-ed-uygula") == "Uygula (1)"
        assert _doseme_h(pg) == pytest.approx(0.14), "Uygula'dan önce model değişmez"

        # Uygula → model; Ctrl+Z (editörde) → önceki model
        pg.click(".tablo-ed .tablo-ed-uygula")
        pg.wait_for_function("Math.abs((MatrisBina.bina().dosemeler || []).find(d => d.no === 1).h - 0.18) < 1e-12")
        pg.wait_for_timeout(600)                     # tablolar güncel modelden yenilenir
        pg.focus(".tablo-ed .tablo-ed-izgara")
        pg.keyboard.press("Control+z")
        pg.wait_for_function("Math.abs((MatrisBina.bina().dosemeler || []).find(d => d.no === 1).h - 0.14) < 1e-12")
        pg.wait_for_timeout(600)

        # bölümlü tek dosya: başka tablodaki (katlar) değişiklik o tabloya yazılır; tanınmayan sütun uyarılır
        pg.click(".tablo-ed .tablo-ed-csv-d")
        with pg.expect_download() as indirilen:
            pg.click(".tablo-ed [data-csv='tek']")
        satirlar = _csv_oku(Path(indirilen.value.path()).read_text(encoding="utf-8"))
        bas_i = next(i for i, r in enumerate(satirlar) if r and r[0].startswith("Tablo: ") and len(r) > 2 and r[2] == "katlar")
        k_bas = satirlar[bas_i + 1]
        assert k_bas[:2] == ["Kat", "Ad"], k_bas
        k_bas.append("Renk")
        k1 = next(r for r in satirlar[bas_i + 2:] if r and r[0] == "1")
        k1[1] = "Birinci kat"
        k1.append("mavi")
        dosya2 = tmp_path / "bolumlu.csv"
        dosya2.write_bytes(_csv_yaz(satirlar))
        with pg.expect_file_chooser() as secici:
            dugme.click()
        secici.value.set_files(str(dosya2))
        pg.wait_for_function("document.querySelector('.tablo-ed .tablo-ed-oge.aktif').dataset.ad === 'katlar' && "
                             "document.querySelectorAll('.tablo-ed td.tablo-ed-degisti').length === 1")
        mesaj = _mesaj(pg)
        assert "CSV: 1 değişiklik bekliyor (Uygula), 1 uyarı" in mesaj and "sütun bulunamadı: Renk" in mesaj, mesaj
        assert _sari_hucreler(pg)[0]["metin"] == "Birinci kat"
        # Geri al: CSV'nin bütün bekleyenleri tek adımda kalkar; model hiç değişmedi
        pg.click(".tablo-ed .tablo-ed-geri")
        pg.wait_for_function("document.querySelectorAll('.tablo-ed td.tablo-ed-degisti').length === 0")
        assert pg.evaluate("MatrisBina.bina().katlar.find(k => k.no === 1).ad") != "Birinci kat"
        _hatasiz(hatalar, "CSV içe aktarma (tarayıcı)")
    finally:
        ctx.close()


# ---------------------------------------------------------------------------------------------------------------- 2. masaüstü yolu
SAHTE_MASAUSTU = """
window.__cagri = [];
window.__dinleyici = {};
const bos = () => Promise.resolve(null);
window.masaustu = Object.freeze({
  surum: "1.0.0", platform: "linux",
  kaydet: bos, projeKaydet: bos, projeAc: bos, pdfYazdir: bos,
  ac: (s) => { window.__cagri.push(["ac", s]); return Promise.resolve(window.__csvDosya || null); },
  klasordeGoster: () => {}, degisti: () => {}, yeni: () => {}, otomatikKayit: () => {}, hazir: () => {}, tamEkran: () => {},
  yeniPencere: () => {}, harici: () => {},
  kisayollar: (l) => { window.__cagri.push(["kisayollar", l]); },
  komutDinle: (fn) => { window.__dinleyici.komut = fn; return () => {}; },
  dosyaDinle: (fn) => { window.__dinleyici.dosya = fn; return () => {}; },
});
"""


def test_csv_iceri_masaustu_komutu(tarayici, sunucu):
    """Dosya › İçe aktar › Tablolar (.csv)… (komut csv-iceri): editör açılır, yerel Aç kutusundan okunan dosya hemen içe aktarılır.
    bina-sayfa paketinin C23 tarafını (tablolarAc(undefined, {csvIceri: true})) gerektirir."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, on_betik=SAHTE_MASAUSTU)
    try:
        assert pg.evaluate("MatrisDosya.masaustu") is True
        _sablon(pg, SABLON)
        # düzenlenmiş dosyanın baytları (ana sürecin "matris:ac" yanıtı gibi: {ad, yol, icerik: Uint8Array})
        pg.evaluate("""async () => {
          const y = await MatrisApp.motorIstegi({islem: "bina_tablolar", girdi: {bina: MatrisBina.bina()}});
          const t = y.tablolar.find(x => x.ad === "dosemeler");
          const I = MatrisTablo._ic, m = I.csvAyristir(I.csvUret(t, {}));
          const ih = m[0].indexOf("Kalınlık t [m]"), r = m.find(s => s[0] === "1");
          r[ih] = "0,2";
          const metin = "\\ufeff" + m.map(s => s.map(h => I.csvAlan(h, ";")).join(";")).join("\\r\\n") + "\\r\\n";
          window.__csvDosya = {ad: "Bina_dosemeler.csv", yol: "/k/Bina_dosemeler.csv", icerik: new TextEncoder().encode(metin)};
        }""")
        pg.evaluate("() => window.__dinleyici.komut({komut: 'csv-iceri'})")
        try:
            pg.wait_for_function("document.querySelectorAll('.tablo-ed td.tablo-ed-degisti').length === 1", timeout=30_000)
        except Exception:
            pytest.fail("csv-iceri komutu editörü açıp içe aktarmayı başlatmadı (bina.js C23: tablolarAc(undefined, {csvIceri: true})); "
                        "editör: " + str(pg.evaluate("!!document.querySelector('.tablo-ed')")) + ", mesaj: " + _mesaj(pg))
        ac = [c for c in pg.evaluate("window.__cagri") if c[0] == "ac"]
        assert ac == [["ac", {"ikili": True, "baslik": "Tabloları CSV dosyasından içe aktar",
                              "filtreler": [{"ad": "CSV tablosu", "uzantilar": ["csv"]}]}]], ac
        assert pg.evaluate("document.querySelector('.tablo-ed .tablo-ed-oge.aktif').dataset.ad") == "dosemeler"
        assert "Bina_dosemeler.csv — CSV: 1 değişiklik bekliyor (Uygula), 0 uyarı" in _mesaj(pg), _mesaj(pg)
        pg.click(".tablo-ed .tablo-ed-uygula")
        pg.wait_for_function("Math.abs((MatrisBina.bina().dosemeler || []).find(d => d.no === 1).h - 0.2) < 1e-12")
        # editörün düğmesi de masaüstünde yerel Aç kutusunu kullanır (gizli girdi açılmaz); vazgeçilirse değişiklik yok
        pg.wait_for_timeout(600)
        pg.evaluate("() => { window.__csvDosya = null; }")
        pg.click(".tablo-ed .tablo-ed-csv-iceri")
        pg.wait_for_function("window.__cagri.filter(c => c[0] === 'ac').length === 2")
        assert pg.evaluate("document.querySelectorAll('.tablo-ed td.tablo-ed-degisti').length") == 0
        _hatasiz(hatalar, "csv-iceri (masaüstü)")
    finally:
        ctx.close()


# ---------------------------------------------------------------------------------------------------------------- 3. kısayol satırları
def test_bina_kisayol_penceresi_yardim_tablosuyla_ayni(tarayici, sunucu):
    """Bina "?" penceresi ve Yardım kısayol tablosu aynı (tuş, komut, grup) satırlarını gösterir; ikisinde de Enter (C22).
    bina-sayfa paketinin MatrisArac.SAYFA_TUSLARI ve kisayolPenceresi tarafını gerektirir."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu)
    try:
        pg.wait_for_timeout(500)
        pg.evaluate("document.activeElement && document.activeElement.blur && document.activeElement.blur()")
        pg.keyboard.press("?")
        pg.wait_for_selector(".bn-kaplama[data-kaplama='kisayollar']")
        pencere = pg.evaluate("""() => {
          const k = document.querySelector(".bn-kaplama[data-kaplama='kisayollar'] .bn-kaplama-govde"), sonuc = [];
          let grup = null;
          k.querySelectorAll("h3, tr").forEach(el => {
            if (el.tagName === "H3") grup = el.textContent.trim();
            else sonuc.push([el.querySelector("kbd").textContent.trim(), el.querySelector("td").textContent.trim(), grup]);
          });
          return sonuc; }""")
        pg.keyboard.press("Escape")
        pg.wait_for_function("!document.querySelector(\".bn-kaplama[data-kaplama='kisayollar']\")")
        pg.click("button[data-sayfa='yardim']")
        pg.wait_for_function("document.getElementById('yardim-kisayollar').dataset.kaynak === 'kayit'")
        yardim = pg.evaluate("""() => Array.from(document.querySelectorAll('#yardim-kisayollar tbody tr')).map(tr =>
            Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim()))""")
        assert len(pencere) >= 30 and len(yardim) >= 30, (len(pencere), len(yardim))
        p_kume = {tuple(r) for r in pencere}
        y_kume = {tuple(r) for r in yardim}
        assert len(p_kume) == len(pencere) and len(y_kume) == len(yardim), "yinelenen satır"
        assert p_kume == y_kume, {"yalniz_pencerede": sorted(p_kume - y_kume)[:12], "yalniz_yardimda": sorted(y_kume - p_kume)[:12]}
        enter = [r for r in pencere if r[0] == "Enter"]
        assert enter == [["Enter", "Bağlam menüsünde: Bilgi", "Sayfa"]], enter
        assert any(r[0] == "?" and r[2] == "Sayfa" for r in yardim)
        _hatasiz(hatalar, "kısayol satırları")
    finally:
        ctx.close()
