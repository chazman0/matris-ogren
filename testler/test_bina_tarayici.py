# -*- coding: utf-8 -*-
"""Bina sayfası tarayıcı testi: genel (surum 3) modelin sonuç ekranı, açık mesnet, yönlendirme ve C1 doğruluk tablosu.

Sayfa gerçek tarayıcıda (başsız) açılır; motor Pyodide yerine CPython'da çalışır: ``testler/tarayici_sunucu.py`` alt süreci
``docs/`` klasörünü sunar ve ``/motor.worker.js`` yerine istekleri ``web_kopru.calistir``'a ileten ara worker verir.

Adımlar:
1. celik-cbf-3kat ve celik-sanayi-4hol: çöz, bütün sonuç sekmelerini aç (yük akışı, tablolar, tasarım, temel…);
2. cbf'ye B2 tabanında açık mafsal mesnet (MatrisBinaCizim.mesnetAta), yeniden çöz, sekmeleri yeniden aç;
3. betonarme-2kat-3x2 + mesnetler kaydı: genel model olarak çözülür ya da açık bir yönlendirme / girdi hatası gösterilir;
4. aynı sayfada celik-cbf-3kat yeniden çözülür (önceki yönlendirme sonraki çözümleri zehirlemez);
5. MatrisBina.s3Var(model) C1 / K2 doğruluk tablosuyla aynı; binaYukle surum'u tam kısmıyla alır (2.9 → 2);
6. araç kutuları 1500×950, 1366×768 ve 1280×720'de varsayılan yerleşimde ve her katlı kutu açılınca birbirine binmez;
7. surum 1 şablonları: tarayıcıda yüklenen model şablonun bütün eleman alanlarını (çatı parapeti duvar_h) taşır; çözümün ΣG'si ve D/C
   haritası köprünün (web_kopru bina_coz) ham şablon çözümüyle aynı;
8. "+Kat → Üsttekini kopyala", "Alt katı kopyala" ve yapıştır çatı parapetini (duvar_h) ara kata taşımaz; ΣG köprüyle aynı;
9. ölçümde Esc tamamlanan ölçüleri silmez; başka kattaki kirişe Yük ata o kirişin yük penceresini açar, Seç kat iletisi verir;
10. genel model sonuçları: vute kesit kartı, Türkçe çubuk türü adları, "kat null" / "null" yok, özel mesnet tipi, Q/S yük akışı.
Herhangi bir sayfa hatası (pageerror) ya da konsol hatası testi düşürür (engellenen ağ / service worker iletileri hariç).

Playwright Python paketi ve bir Chromium yoksa atlanır (MATRIS_CHROMIUM, /opt/pw-browsers/chromium ya da
/opt/pw-browsers/chromium-*/chrome-linux*/chrome).
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import yapi

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
    # K2 ek satırları (motor yapi._serbest_mi ve bina_cizim.js genelMi ile ortak)
    ("tur Cubuk", {"ek_yukler": [{"tur": "Cubuk", "cubuk": 1, "durum": "G", "q": -1}]}, True),
    ("tur ' panel'", {"ek_yukler": [{"tur": " panel", "panel": 1, "durum": "G", "q": -1}]}, True),
    ("tur PANEL", {"ek_yukler": [{"tur": "PANEL", "panel": 1, "durum": "G", "q": -1}]}, True),
    ("surum '3.0'", {"surum": "3.0"}, True),
    ("surum '3.5'", {"surum": "3.5"}, True),
    ("surum '3a'", {"surum": "3a"}, False),
    ("surum '0x3'", {"surum": "0x3"}, False),
    ("surum '1e1'", {"surum": "1e1"}, False),
    ("surum 2.9", {"surum": 2.9}, False),
]
# surum 1 (aks–kat) şablonları
SURUM1_SABLONLAR = [ad for ad in (s["ad"] if isinstance(s, dict) else s for s in yapi.bina_sablonlar())
                    if int(yapi.bina_sablon(ad).get("surum", 1)) < 3]


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


def _sayfa_ac(tarayici, sunucu, en=1440, boy=900):
    """Yeni bağlam (boş localStorage: varsayılan araç kutusu yerleşimi) ve Bina sayfası."""
    ctx = tarayici.new_context(service_workers="block", viewport={"width": en, "height": boy})
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


@pytest.fixture(scope="module")
def sayfa(tarayici, sunucu):
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu)
    try:
        yield pg, hatalar
    finally:
        ctx.close()


@pytest.fixture(scope="module")
def kopru():
    """Köprü (docs/web_kopru.py) bu süreçte: tarayıcı sonuçları aynı JSON'un CPython çözümüyle karşılaştırılır."""
    ozellik = importlib.util.spec_from_file_location("web_kopru_tarayici_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def _kopru_coz(kopru, bina):
    y = json.loads(kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": bina}})))
    assert not y.get("hata"), y.get("hata")
    return y["veri"]


def _dc_haritasi(veri):
    return {f"{e['tur']}{e['no']}": e.get("dc") for e in (veri.get("tasarim") or {}).get("elemanlar", [])}


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
    # K2: binaYukle (binaAyarla normalleştirir) surum'u tam kısmıyla alır; dize yalnız tamsayı / ondalık biçimindeyse sayılır
    surumlar = pg.evaluate("""(liste) => {
      const taban = JSON.parse(JSON.stringify(MatrisBina.bina()));
      const out = liste.map((s) => { MatrisBina.binaAyarla(Object.assign(JSON.parse(JSON.stringify(taban)), { surum: s }), { geriAl: false });
        return [MatrisBina.bina().surum, MatrisBina.s3Var()]; });
      MatrisBina.binaAyarla(taban, { geriAl: false });
      return out;
    }""", [2.9, "3.0", "3.5", "3a", "1e1", 1, True, "9" * 400, "-" + "9" * 400])
    # çok uzun rakam dizisi: JS'de ±Infinity (motor _surum_sayi da öyle) → +: genel (surum 3; JSON'a null yazılmaz), −: aks–kat
    assert surumlar == [[2, False], [3, True], [3, True], [1, False], [1, False], [1, False], [1, False], [3, True], [1, False]]
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


# ---- araç kutuları (NEW-2): varsayılan yerleşimde ve her katlı kutu açılınca kutular birbirine binmez

KUTU_KESISIM_JS = """() => {
  const l = Array.from(document.querySelectorAll('.arac-kutu')).filter(k => k.offsetParent).map(k => [k.dataset.kutu, k.getBoundingClientRect()]);
  const out = [];
  for (let i = 0; i < l.length; i++) for (let j = i + 1; j < l.length; j++) {
    const a = l[i][1], b = l[j][1];
    const w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (w > 0 && h > 0) out.push(l[i][0] + ' x ' + l[j][0] + ' ' + Math.round(w) + 'x' + Math.round(h));
  }
  return out;
}"""
KUTU_ACIK_JS = "Array.from(document.querySelectorAll('.arac-kutu')).filter(k => k.offsetParent && !k.classList.contains('arac-katli')).map(k => k.dataset.kutu)"
# görünür bir kutunun düğmesi başka bir kutunun altında mı (düğme ortasında elementFromPoint)
KUTU_ORTULU_JS = """() => {
  const out = [];
  document.querySelectorAll('.arac-kutu').forEach(k => {
    if (!k.offsetParent || k.classList.contains('arac-katli')) return;
    k.querySelectorAll('.arac-dugme').forEach(b => {
      const r = b.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      const t = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
      const kk = t && t.closest && t.closest('.arac-kutu');
      if (kk && kk !== k) out.push(k.dataset.kutu + ':' + b.dataset.komut + ' < ' + kk.dataset.kutu);
    });
  });
  return out;
}"""


@pytest.mark.parametrize("en,boy", [(1500, 950), (1366, 768), (1280, 720)])
def test_arac_kutulari_birbirine_binmez(tarayici, sunucu, en, boy):
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, en, boy)
    try:
        _sablon(pg, "betonarme-2kat-3x2")
        assert pg.evaluate(KUTU_KESISIM_JS) == [], "varsayılan yerleşim"
        assert pg.evaluate(KUTU_ORTULU_JS) == [], "varsayılan yerleşim"
        katli = pg.evaluate("Array.from(document.querySelectorAll('.arac-kutu.arac-katli')).filter(k => k.offsetParent).map(k => k.dataset.kutu)")
        assert katli, "varsayılan yerleşimde katlı kutu yok"
        acilan = []
        for kid in katli:
            pg.evaluate("(k) => document.querySelector(`.arac-kutu[data-kutu='${k}'] .arac-kutu-katla`).click()", kid)
            pg.wait_for_timeout(250)
            assert pg.evaluate(KUTU_KESISIM_JS) == [], f"{kid} açılınca"
            assert pg.evaluate(KUTU_ORTULU_JS) == [], f"{kid} açılınca"
            if pg.evaluate("(k) => document.querySelector(`.arac-kutu[data-kutu='${k}']`).classList.contains('arac-katli')", kid):
                # yer yoksa kutu katlı kalır ve kullanıcıya söylenir
                bildirim = pg.evaluate("(document.querySelector('.arac-bildirim') || {}).textContent || ''")
                assert "katlı bırakıldı" in bildirim, (kid, bildirim)
            else:
                acilan.append(kid)
                pg.evaluate("(k) => document.querySelector(`.arac-kutu[data-kutu='${k}'] .arac-kutu-katla`).click()", kid)
                pg.wait_for_timeout(200)
                assert pg.evaluate(KUTU_KESISIM_JS) == [], f"{kid} yeniden katlanınca"
        if en >= 1366:
            assert acilan == katli, f"{en}×{boy}: açılamayan kutu: {sorted(set(katli) - set(acilan))}"
        # pencere daralıp genişleyince (yan panel, geliştirici araçları …) yer kalmadığı için kendiliğinden katlanan kutular (ör. Sonuç)
        # yer açılınca yeniden açılır: açık kutular baştakiyle aynı, kutular yine birbirine binmez
        acik0 = sorted(pg.evaluate(KUTU_ACIK_JS))
        for dw, dh in ((250, 150), (0, 200)):
            pg.set_viewport_size({"width": en - dw, "height": boy - dh})
            pg.wait_for_timeout(400)
            pg.set_viewport_size({"width": en, "height": boy})
            pg.wait_for_timeout(400)
            assert sorted(pg.evaluate(KUTU_ACIK_JS)) == acik0, f"{en}×{boy} → −{dw}×{dh} → geri"
            assert pg.evaluate(KUTU_KESISIM_JS) == [], f"{en}×{boy} → −{dw}×{dh} → geri"
            assert pg.evaluate(KUTU_ORTULU_JS) == [], f"{en}×{boy} → −{dw}×{dh} → geri"
        _hatasiz(hatalar, f"araç kutuları {en}×{boy}")
    finally:
        ctx.close()


# modelin aks kesişimlerinden (her kat kotunda) bir araç kutusunun altında kalanlar
KESISIM_ORTULU_JS = """() => {
  const b = MatrisBina.bina(), iz = MatrisBina.izdusum(), svg = document.getElementById('bn-svg'), out = [];
  for (const k of b.katlar) for (const ax of b.akslar.x) for (const ay of b.akslar.y) {
    const p = iz.P(+ax.konum, +ay.konum, +k.kot), pt = svg.createSVGPoint(); pt.x = p[0]; pt.y = p[1];
    const r = pt.matrixTransform(svg.getScreenCTM()), t = document.elementFromPoint(r.x, r.y), kk = t && t.closest && t.closest('.arac-kutu');
    if (kk) out.push(ax.ad + ay.ad + '@' + k.kot + ':' + kk.dataset.kutu);
  }
  return out;
}"""


@pytest.mark.parametrize("en,boy", [(1500, 950), (1280, 720)])
def test_tam_ekranda_model_kutularin_altinda_kalmaz(tarayici, sunucu, en, boy):
    """Tam ekranda kapsayıcı uzayınca yönetici düğmesinin yanındaki Çizim sütunu alta değmez; Sığdır'ın kenar payları onu yine sol pay
    saymalı (üst pay sayılırsa model ince bir şeride, Analiz kutusunun altına sıkışıyordu)."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, en, boy)
    try:
        _sablon(pg, "betonarme-4kat-4x3")
        pg.click("#bn-tam")
        pg.wait_for_timeout(900)
        assert pg.evaluate("document.body.classList.contains('bn-tam-ekran')")
        assert pg.evaluate(KUTU_KESISIM_JS) == [], f"tam ekran {en}×{boy}"
        assert pg.evaluate(KESISIM_ORTULU_JS) == [], f"tam ekran {en}×{boy}"
        pay = pg.evaluate("MatrisArac.kenarPaylari()")
        katman = pg.evaluate("[document.querySelector('.arac-kok').clientWidth, document.querySelector('.arac-kok').clientHeight]")
        assert katman[1] - pay["ust"] - pay["alt"] > 0.4 * katman[1], (pay, katman)
        pg.click("#bn-tam")
        pg.wait_for_timeout(400)
        _hatasiz(hatalar, f"tam ekran {en}×{boy}")
    finally:
        ctx.close()


# ---- surum 1 şablonları (NEW-9): tarayıcı modeli şablon alanlarını korur; çözüm köprüyle aynı

@pytest.mark.parametrize("ad", SURUM1_SABLONLAR)
def test_surum1_sablon_alanlari_ve_cozumu_kopruyle_ayni(sayfa, kopru, ad):
    pg, hatalar = sayfa
    ham = yapi.bina_sablon(ad)
    _sablon(pg, ad)
    b = pg.evaluate("MatrisBina.bina()")
    assert b["surum"] == 1
    for liste in ("kolonlar", "kirisler", "dosemeler"):
        tarayici_l = {e["no"]: e for e in b[liste]}
        for e in ham.get(liste, []):
            t = tarayici_l.get(e["no"])
            assert t is not None, f"{liste} {e['no']} yok"
            eksik = sorted(k for k in e if k not in t)
            assert not eksik, f"{ad} {liste} {e['no']}: eksik alan {eksik}"
            if "duvar_h" in e:
                assert t["duvar_h"] == e["duvar_h"], f"{ad} kiriş {e['no']} parapeti"
    assert _coz(pg) is True, _hata_metni(pg)
    veri = pg.evaluate("MatrisBina.veri()")
    ref = _kopru_coz(kopru, ham)
    assert veri["yukler"]["toplam"]["G"] == pytest.approx(ref["yukler"]["toplam"]["G"], rel=1e-9, abs=1e-9)
    dc, dc_ref = _dc_haritasi(veri), _dc_haritasi(ref)
    assert dc.keys() == dc_ref.keys() and dc
    for k, v in dc_ref.items():
        assert dc[k] == pytest.approx(v, rel=1e-9, abs=1e-12) if v is not None else dc[k] is None, k
    _hatasiz(hatalar, ad)


# ---- kat kopyası ve yapıştır (NEW-1): çatı parapeti (duvar_h) ara kata taşınmaz

def _parapetler(b, kat):
    return sorted((k.get("duvar_h") is None, float(k.get("duvar_h") or 0)) for k in b["kirisler"] if k["kat"] == kat)


def test_kat_kopyasi_parapeti_ara_kata_tasimaz(sayfa, kopru):
    pg, hatalar = sayfa
    ham = yapi.bina_sablon("betonarme-2kat-3x2")
    parapet = _parapetler(ham, 2)
    assert (False, 1.0) in parapet
    # +Kat → Üsttekini kopyala: eski çatı (kat 2) ara kat olur, parapet yeni çatıya (kat 3) taşınır
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("document.querySelector(\"[data-kat-islem='kopyala']\").click()")
    pg.wait_for_timeout(200)
    b = pg.evaluate("MatrisBina.bina()")
    assert [k["no"] for k in b["kirisler"] if k["kat"] == 2 and "duvar_h" in k] == []
    assert _parapetler(b, 3) == parapet
    assert "parapet" in pg.evaluate("document.getElementById('toast-metin').textContent")
    assert _coz(pg) is True, _hata_metni(pg)
    G = pg.evaluate("MatrisBina.veri().yukler.toplam.G")
    assert G == pytest.approx(_kopru_coz(kopru, b)["yukler"]["toplam"]["G"], rel=1e-9)
    assert G == pytest.approx(1379.7, abs=0.05)
    # en üst kat silinince (+Kat'ın tersi) alttaki kat yeniden "Çatı" olur ve parapetleri geri gelir: şablonla aynı model ve ΣG
    pg.evaluate("document.querySelector(\"[data-kat-islem='sil']\").click()")
    pg.wait_for_timeout(200)
    b = pg.evaluate("MatrisBina.bina()")
    assert [k["ad"] for k in b["katlar"]] == [k["ad"] for k in ham["katlar"]]
    assert _parapetler(b, 2) == parapet
    assert "geri verildi" in pg.evaluate("document.getElementById('toast-metin').textContent")
    assert _coz(pg) is True, _hata_metni(pg)
    assert pg.evaluate("MatrisBina.veri().yukler.toplam.G") == pytest.approx(_kopru_coz(kopru, ham)["yukler"]["toplam"]["G"], rel=1e-9)
    # Boş kat + "Alt katı kopyala" (kat 3 etkin): kat 2 fiilen çatıydı, parapeti kat 3'e geçer. Boş kat eklenince eski çatıdaki
    # parapetler (üst kat boşken doğru) kalır ve kullanıcıya söylenir
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("document.querySelector(\"[data-kat-islem='bos']\").click()")
    pg.wait_for_timeout(150)
    assert pg.evaluate("MatrisBina.gorunum().kat") == 3
    assert _parapetler(pg.evaluate("MatrisBina.bina()"), 2) == parapet
    assert "çatı parapeti (duvar_h) duruyor" in pg.evaluate("document.getElementById('toast-metin').textContent")
    pg.evaluate("document.getElementById('bn-kat-kopyala').click()")
    pg.wait_for_timeout(150)
    b = pg.evaluate("MatrisBina.bina()")
    assert [k["no"] for k in b["kirisler"] if k["kat"] == 2 and "duvar_h" in k] == []
    assert _parapetler(b, 3) == parapet
    # çatı kirişi kopyalanıp 1. kata yapıştırılınca parapet taşınmaz (kat 1'in A1–B1 kirişi önce silinir)
    _sablon(pg, "betonarme-2kat-3x2")
    sonuc = pg.evaluate("""(() => {
      const b = JSON.parse(JSON.stringify(MatrisBina.bina()));
      const k1 = b.kirisler.filter(k => k.kat === 1 && k.bas.join('') === 'A1' && k.son.join('') === 'B1')[0];
      const k8 = b.kirisler.filter(k => k.kat === 2 && k.bas.join('') === 'A1' && k.son.join('') === 'B1')[0];
      b.kirisler = b.kirisler.filter(k => k !== k1);
      MatrisBina.binaAyarla(b, {});
      MatrisBina.gorunumAyarla({ kat: 2 });
      MatrisBina.seciliAyarla([{ tur: 'kiris', no: k8.no }]);
      MatrisArac.calistir('kopyala');
      MatrisBina.gorunumAyarla({ kat: 1 });
      MatrisArac.calistir('yapistir');
      const y = MatrisBina.bina().kirisler.filter(k => k.kat === 1 && k.bas.join('') === 'A1' && k.son.join('') === 'B1')[0];
      return { k8: k8.duvar_h, yeni: y ? ('duvar_h' in y ? y.duvar_h : null) : 'yok', duvar: y ? y.duvar : null };
    })()""")
    assert sonuc["k8"] == 1 and sonuc["yeni"] is None and sonuc["duvar"], sonuc
    _hatasiz(hatalar, "kat kopyası")


# ---- ölçüm Esc'i (NEW-3) ve başka kattaki eleman (NEW-6)

EKRAN_JS = """([X, Y, Z]) => {
  const b = MatrisBina.izdusum(), p = b.P(X, Y, Z), svg = document.getElementById('bn-svg');
  const pt = svg.createSVGPoint(); pt.x = p[0]; pt.y = p[1];
  const r = pt.matrixTransform(svg.getScreenCTM());
  return { x: r.x, y: r.y };
}"""


def _tikla(pg, P):
    pg.evaluate("document.getElementById('bn-svg').scrollIntoView({ block: 'center' })")
    e = pg.evaluate(EKRAN_JS, list(P))
    pg.mouse.move(e["x"], e["y"])
    pg.wait_for_timeout(80)
    pg.mouse.click(e["x"], e["y"])
    pg.wait_for_timeout(250)


def _olcum_metni(pg):
    return pg.evaluate("(document.querySelector('#bn-svg .olcum-kok') || {}).textContent || ''")


def test_olcumde_esc_tamamlanan_olculeri_silmez(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("MatrisBina.gorunumAyarla({ kat: 1 }); MatrisArac.calistir('olc-uzaklik')")
    ipucu = "(document.querySelector('.bn-ipucu') || {}).textContent || ''"
    _tikla(pg, (0, 0, 3))
    assert "Esc: yarım ölçümü siler" in pg.evaluate(ipucu)          # ipucu Esc'in o anki etkisini söyler
    _tikla(pg, (5, 0, 3))
    assert "L = 5,000" in _olcum_metni(pg)
    assert "Esc: ölçümden çıkar (sonuçlar kalır)" in pg.evaluate(ipucu)
    pg.keyboard.press("Escape")             # yarım ölçüm yok: kipten çıkılır, sonuç kalır
    pg.wait_for_timeout(150)
    assert pg.evaluate("MatrisBina.kip()") == "sec"
    assert "L = 5,000" in _olcum_metni(pg)
    pg.evaluate("MatrisArac.calistir('olc-uzaklik')")
    _tikla(pg, (0, 0, 3))                   # yarım ölçüm
    pg.keyboard.press("Escape")             # yalnız yarım ölçüm silinir, kipte kalınır
    pg.wait_for_timeout(150)
    assert pg.evaluate("MatrisBina.kip()") == "olc-uzaklik"
    assert "L = 5,000" in _olcum_metni(pg)
    pg.evaluate("MatrisArac.calistir('olc-temizle')")      # "Ölçüleri temizle" hepsini siler
    pg.wait_for_timeout(150)
    assert "L = 5,000" not in _olcum_metni(pg)
    pg.keyboard.press("Escape")
    _hatasiz(hatalar, "ölçüm Esc")


def test_baska_kattaki_kirise_yuk_ata_ve_kat_iletisi(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("MatrisBina.gorunumAyarla({ kat: 1 }); MatrisArac.calistir('yuk-ata')")
    assert pg.evaluate("MatrisBina.kip()") == "yuk-ata"
    _tikla(pg, (2.5, 0, 6))                 # çatı (kat 2) kirişi A1–B1, etkin kat 1
    baslik = pg.evaluate("(document.querySelector('.bn-kaplama h2') || {}).textContent || ''")
    no = pg.evaluate("MatrisBina.bina().kirisler.filter(k => k.kat === 2 && k.bas.join('') === 'A1' && k.son.join('') === 'B1')[0].no")
    assert baslik == f"Yük: Kiriş {no}", baslik
    assert "Çatı" in pg.evaluate("document.getElementById('toast-metin').textContent")
    # başka kattaki düğüme (çatı A1) dokunuş: kip önce düğüm yakalar → düğüm yükü penceresi; "kirişe uygulanıyor" iletisi verilmez
    pg.evaluate("MatrisBina.kaplamaKapat(); document.getElementById('toast-metin').textContent = ''")
    _tikla(pg, (0, 0, 6))
    baslik = pg.evaluate("(document.querySelector('.bn-kaplama h2') || {}).textContent || ''")
    assert baslik.startswith("Yük: Düğüm A-1"), baslik
    assert "uygulanıyor" not in pg.evaluate("document.getElementById('toast-metin').textContent")
    pg.evaluate("MatrisBina.kaplamaKapat(); MatrisBina.kipAyarla('sec'); MatrisBina.seciliAyarla([])")
    # Seç etkin kata uygulanır: başka kattaki kirişe dokununca hangi katın etkinleştirileceği söylenir
    _tikla(pg, (2.5, 0, 6))
    ileti = pg.evaluate("document.getElementById('toast-metin').textContent")
    assert f"Kiriş {no}" in ileti and "Çatı" in ileti and "etkinleştirin" in ileti, ileti
    assert pg.evaluate("MatrisBina.secim()") == []
    _hatasiz(hatalar, "başka kat")


# ---- genel model sonuç ayrıntıları (VUTE-PANEL, KOZMETIK, AKIS-QS)

def test_vute_kesit_karti_ve_secenegi(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "celik-sanayi-4hol")
    vute = pg.evaluate("(() => { const b = MatrisBina.bina(); const ad = Object.keys(b.kesitler).filter(k => b.kesitler[k].tip === 'vute')[0];"
                       " const c = (b.cubuklar || []).filter(c => c.kesit === ad)[0]; return [ad, c && c.no]; })()")
    assert vute[0] and vute[1], vute
    pg.evaluate("(no) => MatrisBina.seciliAyarla([{ tur: 'cubuk', no: no }])", vute[1])
    pg.wait_for_timeout(200)
    panel = pg.evaluate("document.getElementById('bn-panel-icerik').innerText")
    assert "undefined" not in panel and "30×50 cm" not in panel, panel[:600]
    assert "+ vute" in panel, panel[:600]
    secenek = pg.evaluate("(ad) => Array.from(document.querySelectorAll('#bn-panel-icerik select[data-oz3=kesit] option')).filter(o => o.value === ad).map(o => o.textContent)", vute[0])
    assert secenek and "+ vute" in secenek[0], secenek
    _hatasiz(hatalar, "vute")


def test_genel_sonuc_adlari_kat_ve_mesnet_tipi(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "celik-cbf-3kat")
    pg.evaluate("""(() => {
      const b = JSON.parse(JSON.stringify(MatrisBina.bina()));
      const r = MatrisBinaCizim.mesnetAta(b, { aks: ["B", "2"], z: "±0.00" }, "kayici-xy");
      MatrisBina.binaAyarla((r && r.model) || r || b, { etiket: "mesnet" });
    })()""")
    assert _coz(pg) is True, _hata_metni(pg)
    icerik = _sekmeleri_gez(pg)
    # Tasarım: çubuk türleri Türkçe (motor adresi "Ç41 (capraz)" değil "Ç41 (çapraz)")
    assert "(capraz)" not in icerik["tasarim"] and "(kiris)" not in icerik["tasarim"], icerik["tasarim"][:800]
    assert "(çapraz)" in icerik["tasarim"]
    # Temel: kayıcı mesnet tipi okunur
    assert "kayıcı (X, Y serbest)" in icerik["temel"] and "ozel" not in icerik["temel"], icerik["temel"][:800]
    # sanayi: tasarım ayrıntısında "kat null", Ağ tablosunda "null" yok
    _sablon(pg, "celik-sanayi-4hol")
    assert _coz(pg) is True, _hata_metni(pg)
    icerik = _sekmeleri_gez(pg)
    assert "null" not in icerik.get("tablolar", ""), "Tablolar'da null"
    pg.click("#bn-sonuc .bn-sekme[data-sekme='tasarim']")
    pg.evaluate("document.querySelector('#bn-sonuc .bn-dc-satir').click()")
    pg.wait_for_timeout(200)
    baslik = pg.evaluate("(document.querySelector('.bn-dc-baslik') || {}).innerText || ''")
    assert baslik and "null" not in baslik and "(kiris)" not in baslik, baslik
    _hatasiz(hatalar, "genel sonuç adları")


def test_genel_yuk_akisi_durumlari(sayfa):
    """Q / S akışı: motor bu durumlar için bant verdiyse şema çizilir, vermediyse boş kutu yerine açıklayıcı not; G+Q yalnız G ve Q."""
    pg, hatalar = sayfa
    _sablon(pg, "celik-cbf-3kat")
    assert _coz(pg) is True, _hata_metni(pg)
    pg.click("#bn-sonuc .bn-sekme[data-sekme='akis']")
    durumlar = pg.evaluate("Array.from(new Set((MatrisBina.veri().akis.sankey || []).filter(e => e.kN > 1e-6).map(e => e.durum)))")
    assert "G" in durumlar
    for d in ("G", "Q", "G+Q", "S"):
        if not pg.evaluate(f"!!document.querySelector(\"[data-akis-durum='{d}']\")"):
            continue
        pg.click(f"[data-akis-durum='{d}']")
        pg.wait_for_timeout(200)
        bant = pg.evaluate("document.querySelectorAll('#bn-sankey path.bn-sankey-bant').length")
        notu = pg.evaluate("Array.from(document.querySelectorAll('#bn-sankey .not')).map(n => n.textContent).join(' ')")
        istenen = d.split("+")
        if any(x in durumlar for x in istenen):
            assert bant > 0, (d, notu)
        else:
            assert bant == 0 and "akış bandı üretmedi" in notu, (d, notu)
        if any(x not in durumlar for x in istenen) and bant:
            assert "için akış verisi yok" in notu, (d, notu)
    # denetçi Yük yolu: başlık ve sütunlar yalnız var olan durumlar; giden kenarı yoksa "Σ giden 0" yazılmaz
    yol = pg.evaluate("MatrisBilgi.tsv(MatrisBilgi.bilgi({ tur: 'cubuk', no: 97 }, MatrisBina.bina(), MatrisBina.veri()), 'yol')")
    assert "Σ giden" not in yol, yol
    if "Q" in durumlar:
        assert "Akış şeması (G + Q" in yol, yol
    else:
        assert "Akış şeması (G, kN)" in yol and "Q ve S payları Yükler sekmesinde" in yol, yol
    _hatasiz(hatalar, "yük akışı")
