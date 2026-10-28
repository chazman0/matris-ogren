# -*- coding: utf-8 -*-
"""Bina sayfası tarayıcı testi: genel (surum 3) modelin sonuç ekranı, açık mesnet, yönlendirme ve C1 doğruluk tablosu.

Sayfa gerçek tarayıcıda (başsız) açılır; motor Pyodide yerine CPython'da çalışır: ``testler/tarayici_sunucu.py`` alt süreci
``docs/`` klasörünü sunar ve ``/motor.worker.js`` yerine istekleri ``web_kopru.calistir``'a ileten ara worker verir.

Adımlar:
1. celik-cbf-3kat ve celik-sanayi-4hol: çöz, bütün sonuç sekmelerini aç (yük akışı, tablolar, tasarım, temel…);
2. cbf'ye B2 tabanında açık mafsal mesnet (MatrisBinaCizim.mesnetAta), yeniden çöz, sekmeleri yeniden aç;
3. betonarme-2kat-3x2 + mesnetler kaydı: genel model olarak çözülür ya da açık bir yönlendirme / girdi hatası gösterilir;
4. aynı sayfada celik-cbf-3kat yeniden çözülür (önceki yönlendirme sonraki çözümleri zehirlemez);
5. MatrisBina.s3Var(model) C1 doğruluk tablosuyla aynı.
Herhangi bir sayfa hatası (pageerror) ya da konsol hatası testi düşürür (engellenen ağ / service worker iletileri hariç).

Playwright Python paketi ve bir Chromium yoksa atlanır (MATRIS_CHROMIUM, /opt/pw-browsers/chromium ya da
/opt/pw-browsers/chromium-*/chrome-linux*/chrome).
"""
from __future__ import annotations

import glob
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

# C1 doğruluk tablosu (motor paketiyle ortak; testler/test_bina_kablolama.py ile aynı); taban: betonarme-2kat-3x2
C1_TABLOSU = [
    ("taban", {}, False),
    ("mesnet", {"mesnetler": [{"dugum": {"aks": ["B", "2"], "z": "+3.00"}, "ux": True, "uy": True, "uz": True}]}, True),
    ("dugum", {"dugumler": [{"no": 100001, "X": 0, "Y": 0, "Z": 3}]}, True),
    ("uretec", {"uretecler": [{"no": 1, "tur": "makas", "parametreler": {}}]}, True),
    ("aks-kat dugum yuku", {"ek_yukler": [{"tur": "dugum", "aks": ["B", "2"], "kat": 1, "durum": "G", "FZ": -10}]}, False),
    ("ref dugum yuku", {"ek_yukler": [{"tur": "dugum", "dugum": {"aks": ["B", "2"], "z": "+3.00"}, "durum": "G", "FZ": -10}]}, True),
    ("cubuk yuku", {"ek_yukler": [{"tur": "cubuk", "cubuk": 1, "durum": "G", "q": -1}]}, True),
    ("surum 3", {"surum": 3}, True),
    ("bos listeler", {"cubuklar": [], "mesnetler": []}, False),
]


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
def sayfa(sunucu):
    with sync_playwright() as pw:
        tarayici = pw.chromium.launch(executable_path=TARAYICI)
        try:
            ctx = tarayici.new_context(service_workers="block", viewport={"width": 1440, "height": 900})
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
            yield pg, hatalar
        finally:
            tarayici.close()


def _sablon(pg, ad):
    # aynı şablon yeniden seçilse de change olayı oluşsun
    pg.evaluate("window.__oncekiBina = MatrisBina.bina(); document.querySelector('select#bn-sablon').value = ''")
    pg.select_option("select#bn-sablon", ad)
    pg.wait_for_function("MatrisBina.bina() && MatrisBina.bina() !== window.__oncekiBina && document.querySelector('select#bn-sablon').value === "
                         + json.dumps(ad))
    pg.wait_for_timeout(300)


def _coz(pg):
    return pg.evaluate("MatrisBina.coz()")


def _hata_metni(pg):
    return pg.evaluate("(document.getElementById('bn-hata') || {}).innerText || ''")


def _sekmeleri_gez(pg):
    sekmeler = pg.evaluate("Array.from(document.querySelectorAll('#bn-sonuc .bn-sekme')).map(b => b.dataset.sekme)")
    icerik = {}
    for s in sekmeler:
        pg.click(f"#bn-sonuc .bn-sekme[data-sekme='{s}']")
        pg.wait_for_timeout(150)
        icerik[s] = pg.evaluate("(document.getElementById('bn-sekme-icerik') || document.getElementById('bn-sonuc')).innerText")
    return icerik


def _hatasiz(hatalar, adim):
    assert not hatalar, f"{adim}: " + " | ".join(hatalar)[:3000]


@pytest.mark.parametrize("ad", ["celik-cbf-3kat", "celik-sanayi-4hol"])
def test_genel_model_sonuc_sekmeleri(sayfa, ad):
    pg, hatalar = sayfa
    _sablon(pg, ad)
    assert pg.evaluate("MatrisBina.s3Var()") is True
    assert _coz(pg) is True, _hata_metni(pg)
    assert pg.evaluate("MatrisBina.veri().model") == "genel"
    icerik = _sekmeleri_gez(pg)
    assert "temel" in icerik and "akis" in icerik and "tasarim" in icerik, list(icerik)
    # yük akışı: genel korunum zinciri (panel + çubuk öz + duvar + ek) ve sankey sütunları paneller → çubuklar
    pg.click("#bn-sonuc .bn-sekme[data-sekme='akis']")
    korunum = pg.evaluate("(document.querySelector('.bn-korunum') || {}).innerText || ''")
    assert "Panel + çubuk öz" in korunum and "✓ dört sayı eşit" in korunum, korunum
    assert not korunum.split("\n")[2].startswith("0,0 kN"), korunum
    basliklar = pg.evaluate("Array.from(document.querySelectorAll('.bn-sankey-bsl')).map(t => t.textContent)")
    assert any("Panel" in b for b in basliklar) and any("Çubuk" in b for b in basliklar), basliklar
    # tablolar: aks–kat döşeme / kiriş dökümleri yerine çubuk ve panel yükleri
    assert "Döşeme payları" not in icerik.get("tablolar", "")
    _hatasiz(hatalar, ad)


def test_acik_mesnet_cozulur_ve_temel_sekmesi_acilir(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "celik-cbf-3kat")
    sonuc = pg.evaluate("""(() => {
      const MC = window.MatrisBinaCizim;
      if (!MC || typeof MC.mesnetAta !== "function") return "mesnetAta yok";
      const b = JSON.parse(JSON.stringify(MatrisBina.bina()));
      const r = MC.mesnetAta(b, { aks: ["B", "2"], z: "±0.00" }, "mafsal");
      MatrisBina.binaAyarla((r && r.model) || r || b, { etiket: "mesnet" });
      return (MatrisBina.bina().mesnetler || []).length;
    })()""")
    assert sonuc == 1, sonuc
    assert _coz(pg) is True, _hata_metni(pg)
    icerik = _sekmeleri_gez(pg)
    assert "Mesnet tepkileri" in icerik["temel"], icerik["temel"][:800]
    assert "undefined" not in icerik["temel"] and "NaN" not in icerik["temel"]
    _hatasiz(hatalar, "açık mesnet")


def test_aks_kat_modelde_mesnet_ve_zehirlenme_yok(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("""(() => {
      const b = JSON.parse(JSON.stringify(MatrisBina.bina()));
      b.mesnetler = [{ dugum: { aks: ["B", "2"], z: "+3.00" }, ux: true, uy: true, uz: true }];
      MatrisBina.binaAyarla(b, {});
    })()""")
    assert pg.evaluate("MatrisBina.s3Var()") is True
    if _coz(pg):
        assert pg.evaluate("MatrisBina.veri().model") == "genel"     # motor modeli genel model olarak çözdü
        _sekmeleri_gez(pg)
    else:
        assert _hata_metni(pg).strip(), "çözüm başarısız ama hata gösterilmedi"
    # aynı sayfada genel model yine çözülür (önceki yönlendirme hatası motoru "genel model yok" diye işaretlemez)
    _sablon(pg, "celik-cbf-3kat")
    assert _coz(pg) is True, _hata_metni(pg)
    assert pg.evaluate("MatrisBina.veri().model") == "genel"
    _hatasiz(hatalar, "yönlendirme")


def test_s3var_c1_dogruluk_tablosu(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    sonuc = pg.evaluate("""(tablo) => {
      const taban = JSON.parse(JSON.stringify(MatrisBina.bina()));
      return tablo.map(([ad, ek]) => [ad, MatrisBina.s3Var(Object.assign(JSON.parse(JSON.stringify(taban)), ek))]);
    }""", [[ad, ek] for ad, ek, _b in C1_TABLOSU])
    assert dict(sonuc) == {ad: b for ad, _e, b in C1_TABLOSU}
    assert pg.evaluate("MatrisBina.s3Var()") is False      # yüklü taban model
    _hatasiz(hatalar, "C1")


def test_masaustu_csv_disa_aktarim(sayfa):
    """Masaüstü "Dışa aktar › CSV" (masaustu-komut csv): bütün tablolar tek CSV dosyasına (";" ayraç, ondalık virgül) kaydedilir."""
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    with pg.expect_download(timeout=120_000) as indirme:
        islendi = pg.evaluate("""(() => {
          const e = new CustomEvent("masaustu-komut", { detail: { komut: "csv" }, cancelable: true });
          window.dispatchEvent(e);
          return e.defaultPrevented;
        })()""")
    assert islendi is True
    d = indirme.value
    assert d.suggested_filename.endswith("_tablolar.csv"), d.suggested_filename
    metin = Path(d.path()).read_text(encoding="utf-8-sig")
    assert metin.count("Tablo: ") > 5 and ";" in metin, metin[:300]
    _hatasiz(hatalar, "csv")
