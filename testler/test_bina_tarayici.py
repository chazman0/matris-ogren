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
6. araç kutuları (rıhtım yerleşimi; kabul A1–A18): 1920×1080 … 1024×768 pencere ve tam ekranda çakışmasız, her düğme vurulur, yönetici
   köşede, bütün kutulara (taşma çekmecesiyle) ulaşılır, model kutuların altında kalmaz, sığdırma ve taşma eşikleri; geçmişsiz yerleşim,
   kullanıcı katlaması, "Kenara sabitle" / kenara sürükleme, yüzen kutu, sürüm 1 yerleşim geçişi, aks balonları, mobil şerit;
7. surum 1 şablonları: tarayıcıda yüklenen model şablonun bütün eleman alanlarını (çatı parapeti duvar_h) taşır; çözümün ΣG'si ve D/C
   haritası köprünün (web_kopru bina_coz) ham şablon çözümüyle aynı;
8. "+Kat → Üsttekini kopyala", "Alt katı kopyala" ve yapıştır çatı parapetini (duvar_h) ara kata taşımaz; ΣG köprüyle aynı;
9. ölçümde Esc tamamlanan ölçüleri silmez; başka kattaki kirişe Yük ata o kirişin yük penceresini açar, Seç kat iletisi verir;
10. genel model sonuçları: vute kesit kartı, Türkçe çubuk türü adları, "kat null" / "null" yok, özel mesnet tipi, Q/S yük akışı;
11. duvar etiketi (değer bir kez), #bina/sablon/<ad> adresi, dolu çatıya "Alt katı kopyala" (parapet korunur), "?" sayfa tuşları (C22),
    masaüstü CSV içe aktarma kancası (C23), yaylı mesnet simgesi (C13), genel modelde mütemadi / radye temel (C11) ve yük akışı
    sütunları (C15; motorla bütünleştirmeden sonra; sözleşme örneğiyle motordan bağımsız da).
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
    # yük akışı: genel korunum zinciri (panel + çubuk öz + duvar + ek) ve sankey sütunları paneller → yatay çubuklar (→ düşey / eğik
    # çubuklar → mesnetler: motor çubuk → çubuk / mesnet kenarlarını verdiğinde; sözleşme C15)
    pg.click("#bn-sonuc .bn-sekme[data-sekme='akis']")
    korunum = pg.evaluate("(document.querySelector('.bn-korunum') || {}).innerText || ''")
    assert "Panel + çubuk öz" in korunum and "✓ dört sayı eşit" in korunum, korunum
    assert not korunum.split("\n")[2].startswith("0,0 kN"), korunum
    basliklar = pg.evaluate("Array.from(document.querySelectorAll('.bn-sankey-bsl')).map(t => t.textContent)")
    assert basliklar[:2] == ["Paneller", "Yatay çubuklar"], basliklar
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


# ---- araç kutuları: rıhtım (kenar şeridi) yerleşimi ve taşma çekmecesi (K-16, K-17, K-18; kabul A1–A18)

# Yerleşim denetimi (kabul A1–A4, A6–A9): görünür kutular, yönetici ve taşma düğmeleri; düğme vuruşu; model kesişimleri ve sığdırma
DUZEN_JS = r"""() => {
  const kok = document.querySelector('.arac-kok'), kr = kok.getBoundingClientRect(), svg = document.getElementById('bn-svg'), sr = svg.getBoundingClientRect();
  const gorunur = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const hata = [];
  const kutular = Array.from(document.querySelectorAll('.arac-kok > .arac-kutu')).filter(gorunur);
  const ogeler = kutular.map(k => [k.dataset.kutu, k.getBoundingClientRect()]);
  const yb = document.querySelector('.arac-kok > .arac-yonetici-ac'), td = document.querySelector('.arac-kok > .arac-tasma-ac');
  if (gorunur(yb)) ogeler.push(['yönetici', yb.getBoundingClientRect()]);
  if (gorunur(td)) ogeler.push(['taşma', td.getBoundingClientRect()]);
  // A1: kesişim alanı 0; aynı şeritteki kutular arası ≥ 6 px (±1)
  for (let i = 0; i < ogeler.length; i++) for (let j = i + 1; j < ogeler.length; j++) {
    const a = ogeler[i][1], b = ogeler[j][1];
    const w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (w > 0 && h > 0) hata.push('A1 ' + ogeler[i][0] + ' × ' + ogeler[j][0] + ' ' + w.toFixed(1) + '×' + h.toFixed(1));
  }
  const rihtim = kutular.filter(k => k.dataset.rihtim);
  for (let i = 0; i < rihtim.length; i++) for (let j = i + 1; j < rihtim.length; j++) {
    const p = rihtim[i], q = rihtim[j];
    if (p.dataset.rihtim !== q.dataset.rihtim) continue;
    const a = p.getBoundingClientRect(), b = q.getBoundingClientRect(), bant = p.dataset.rihtim === 'ust' || p.dataset.rihtim === 'alt';
    const ara = bant ? Math.max(b.left - a.right, a.left - b.right) : Math.max(b.top - a.bottom, a.top - b.bottom);
    if (ara < 5) hata.push('A1 aralık ' + p.dataset.kutu + '/' + q.dataset.kutu + ' ' + ara.toFixed(1));
  }
  // A2: katmanın içinde (±0,5 px)
  ogeler.forEach(([id, r]) => { if (r.left < kr.left - 0.5 || r.top < kr.top - 0.5 || r.right > kr.right + 0.5 || r.bottom > kr.bottom + 0.5) hata.push('A2 ' + id); });
  // A3: açık her kutunun her düğmesi beş noktada kendisini döndürür; düğme listesi kaydırmalı değil
  const vurus = (kutu, b, liste) => {
    const r = b.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) { liste.push(kutu + ':' + b.dataset.komut + ' boyutsuz'); return; }
    for (const [fx, fy] of [[.5, .5], [.15, .15], [.85, .15], [.15, .85], [.85, .85]]) {
      const t = document.elementFromPoint(r.left + r.width * fx, r.top + r.height * fy);
      if (!t || !b.contains(t)) { liste.push(kutu + ':' + b.dataset.komut + ' < ' + (t ? (t.closest('[data-kutu]') || {}).dataset?.kutu || t.className || t.tagName : 'yok')); return; }
    }
  };
  const vurulmaz = [];
  kutular.forEach(k => {
    if (k.classList.contains('arac-katli')) return;
    k.querySelectorAll('.arac-dugme').forEach(b => vurus(k.dataset.kutu, b, vurulmaz));
    const d = k.querySelector('.arac-dugmeler');
    if (d && d.scrollHeight > d.clientHeight + 1) hata.push('A3 kaydırmalı ' + k.dataset.kutu);
  });
  vurulmaz.forEach(v => hata.push('A3 ' + v));
  // A4: yönetici düğmesi (8, H − 42, 34, 34)
  let yonetici = null;
  if (gorunur(yb)) {
    const r = yb.getBoundingClientRect();
    yonetici = [r.left - kr.left, r.top - kr.top, r.width, r.height];
    const b = [8, kr.height - 42, 34, 34];
    if (yonetici.some((v, i) => Math.abs(v - b[i]) > 0.5)) hata.push('A4 yönetici ' + JSON.stringify(yonetici));
  }
  // A6: her kattaki (ve kot 0) aks kesişimi kutuların altında değil, svg içinde
  const bina = MatrisBina.bina(), iz = MatrisBina.izdusum(), pts = [];
  const kotlar = [0].concat(bina.katlar.map(k => +k.kot));
  for (const z of kotlar) for (const ax of bina.akslar.x) for (const ay of bina.akslar.y) {
    const p = iz.P(+ax.konum, +ay.konum, z), pt = svg.createSVGPoint(); pt.x = p[0]; pt.y = p[1];
    const r = pt.matrixTransform(svg.getScreenCTM()); pts.push([r.x, r.y]);
    const t = document.elementFromPoint(r.x, r.y), kk = t && t.closest && t.closest('.arac-kutu, .arac-yonetici-ac, .arac-tasma-ac, .arac-serit');
    if (kk) hata.push('A6 ' + ax.ad + ay.ad + '@' + z + ' < ' + (kk.dataset.kutu || kk.className.split(' ')[0]));
    if (r.x < sr.left || r.x > sr.right || r.y < sr.top || r.y > sr.bottom) hata.push('A6 sahne dışı ' + ax.ad + ay.ad + '@' + z);
  }
  // A7: sığdırma oranı; A8: modelin çizim yüksekliği
  const a = iz.alan, ax0 = sr.left + a.x, ay0 = sr.top + a.y;
  const ix = Math.max(0, Math.min(ax0 + a.w, kr.right) - Math.max(ax0, kr.left)), iy = Math.max(0, Math.min(ay0 + a.h, kr.bottom) - Math.max(ay0, kr.top));
  const ys = pts.map(p => p[1]);
  return { hata, tasan: MatrisArac.tasanlar(), katman: [kr.width, kr.height], oran: ix * iy / (kr.width * kr.height), modelH: Math.max(...ys) - Math.min(...ys),
    rihtim: Object.fromEntries(rihtim.map(k => [k.dataset.kutu, [k.dataset.rihtim, k.classList.contains('arac-katli')]])),
    katli: Array.from(document.querySelectorAll('.arac-kutu.arac-katli')).map(k => k.dataset.kutu),
    tasmaSayi: td ? +(td.querySelector('.arac-tasma-sayi') || {}).textContent : 0, yonetici };
}"""
# kutuların yerleşimi (A10 karşılaştırması): konum, boy, biçim sınıfları; taşanlar
YERLESIM_JS = r"""() => {
  const S = ['arac-yatay', 'arac-dikey', 'arac-basliksiz', 'arac-katli', 'arac-sutun2', 'arac-sutun-cip', 'arac-rihtimda', 'arac-serbest', 'arac-tasmada'];
  const k = document.querySelector('.arac-kok');
  return { katman: [k.clientWidth, k.clientHeight], tasan: MatrisArac.tasanlar(),
    kutular: Object.fromEntries(Array.from(document.querySelectorAll('.arac-kutu')).map(d => [d.dataset.kutu,
      [d.offsetLeft, d.offsetTop, d.offsetWidth, d.offsetHeight, S.filter(c => d.classList.contains(c)).join(' '), d.dataset.rihtim || '']])) };
}"""
# taşma çekmecesinin kutuları ve düğmeleri (A5): vuruş, görünüm alanı içinde
CEKMECE_JS = r"""() => {
  const p = document.querySelector('.arac-kok > .arac-tasma');
  if (!p) return null;
  const out = { kutular: [], hata: [] };
  p.querySelectorAll('.arac-kutu').forEach(k => {
    out.kutular.push(k.dataset.kutu);
    k.querySelectorAll('.arac-dugme').forEach(b => {
      const r = b.getBoundingClientRect();
      if (r.left < 0 || r.top < 0 || r.right > innerWidth || r.bottom > innerHeight) { out.hata.push('görünüm dışı ' + b.dataset.komut); return; }
      for (const [fx, fy] of [[.5, .5], [.15, .15], [.85, .15], [.15, .85], [.85, .85]]) {
        const t = document.elementFromPoint(r.left + r.width * fx, r.top + r.height * fy);
        if (!t || !b.contains(t)) { out.hata.push(k.dataset.kutu + ':' + b.dataset.komut); return; }
      }
    });
  });
  return out;
}"""
KUTULAR = ["k-cizim", "k-duzenleme", "k-gorunum", "k-analiz", "k-sonuc", "k-aks", "k-olcme", "k-degistirme", "k-uretec"]
# kabul eşikleri: (en, boy) → [pencere, tam ekran] için (sığdırma oranı A7, model yüksekliği A8, en çok taşan A9)
ESIK = {(1920, 1080): [(0.68, 440, 0), (0.71, 550, 0)], (1500, 950): [(0.60, 340, 1), (0.64, 445, 0)], (1366, 768): [(0.48, 200, 3), (0.57, 305, 1)],
        (1280, 720): [(0.42, 155, 3), (0.54, 265, 3)], (1024, 768): [(0.37, 160, 5), (0.50, 305, 3)]}


def _yerlesim_sayfasi(tarayici, sunucu, en, boy, tam=False, sablon=True):
    """Boş profil, betonarme-2kat-3x2, 3B; tam ekran isteğe bağlı; fare kutuların dışında; bildirim balonları gizli (vuruş testini örtmesin)."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, en, boy)
    if sablon:
        _sablon(pg, "betonarme-2kat-3x2")
    if tam:
        pg.click("#bn-tam")
        pg.wait_for_function("document.body.classList.contains('bn-tam-ekran')")
    _yerlesim_bekle(pg)
    return ctx, pg, hatalar


def _yerlesim_bekle(pg):
    pg.mouse.move(1, 1)
    pg.wait_for_timeout(600)
    pg.evaluate("document.querySelectorAll('.toast').forEach(t => t.style.visibility = 'hidden')")


def _duzen_denetle(pg, ad):
    d = pg.evaluate(DUZEN_JS)
    assert d["hata"] == [], f"{ad}: " + " | ".join(d["hata"][:20])
    return d


def _cekmece_denetle(pg, ad):
    """A5: kenardaki ∪ çekmecedeki = 9 kutu (yinelenmeden); çekmece açılır, düğmeleri vurulur, Esc kapatır ve odak düğmeye döner."""
    d = pg.evaluate(DUZEN_JS)
    yerli = [k for k in d["rihtim"]]
    assert sorted(yerli + d["tasan"]) == sorted(KUTULAR) and len(set(yerli) & set(d["tasan"])) == 0, (ad, yerli, d["tasan"])
    assert d["tasmaSayi"] == len(d["tasan"]), (ad, d["tasmaSayi"], d["tasan"])
    if not d["tasan"]:
        assert pg.query_selector(".arac-tasma-ac") is None, ad
        return d
    pg.click(".arac-tasma-ac")
    pg.wait_for_timeout(250)
    c = pg.evaluate(CEKMECE_JS)
    assert c is not None and c["kutular"] == d["tasan"], (ad, c)
    assert c["hata"] == [], (ad, c["hata"])
    assert pg.evaluate("document.querySelector('.arac-tasma-ac').getAttribute('aria-expanded')") == "true"
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(200)
    assert pg.query_selector(".arac-tasma") is None, ad
    assert pg.evaluate("document.activeElement && document.activeElement.classList.contains('arac-tasma-ac')"), ad
    pg.mouse.move(1, 1)
    _duzen_denetle(pg, ad + " çekmece kapandıktan sonra")
    return d


@pytest.mark.parametrize("tam", [False, True], ids=["pencere", "tam"])
@pytest.mark.parametrize("en,boy", list(ESIK))
def test_arac_kutulari_rihtim_yerlesimi(tarayici, sunucu, en, boy, tam):
    """A1–A9, A11: varsayılan yerleşim çakışmasız, katmanın içinde, her düğme vurulur, yönetici düğmesi köşede, bütün kutulara ulaşılır
    (çekmece), model kutuların altında kalmaz; sığdırma oranı, model boyu ve taşan sayısı eşiklerin içinde; tam ekranda şeritler kenarlarda."""
    ctx, pg, hatalar = _yerlesim_sayfasi(tarayici, sunucu, en, boy, tam)
    ad = f"{en}×{boy} {'tam' if tam else 'pencere'}"
    try:
        d = _duzen_denetle(pg, ad)
        oran, model_h, en_cok = ESIK[(en, boy)][1 if tam else 0]
        assert d["oran"] >= oran, (ad, "A7", round(d["oran"], 3))
        assert d["modelH"] >= model_h, (ad, "A8", round(d["modelH"]))
        assert len(d["tasan"]) <= en_cok, (ad, "A9", d["tasan"])
        # A9: Çizim, Düzenleme, Görünüm ve Sonuç her boyda kenarda ve açık; Analiz 1280×720 ve üstünde; boş profilde katlı kutu yok
        acik = {k for k, (_kn, katli) in d["rihtim"].items() if not katli}
        assert {"k-cizim", "k-duzenleme", "k-gorunum", "k-sonuc"} <= acik, (ad, d["rihtim"])
        if en >= 1280:
            assert "k-analiz" in acik, (ad, d["rihtim"])
        assert d["katli"] == [], (ad, d["katli"])
        if tam and en in (1920, 1500):
            # A11: alt bant kutuları katmanın altına, sağ sütun sağ kenara yaslı; Görünüm ile Analiz arası ≥ 6 px
            k = pg.evaluate(YERLESIM_JS)
            W, H = k["katman"]
            for kid, (x, y, w, h, _s, kn) in k["kutular"].items():
                if kn == "alt":
                    assert abs(y - (H - 8 - h)) <= 1, (ad, kid, y, h, H)
                if kn == "sag":
                    assert abs(x - (W - 8 - w)) <= 1, (ad, kid, x, w, W)
            g, a = k["kutular"]["k-gorunum"], k["kutular"]["k-analiz"]
            assert a[0] - (g[0] + g[2]) >= 5, (ad, g, a)
        _cekmece_denetle(pg, ad)
        _hatasiz(hatalar, ad)
    finally:
        ctx.close()


@pytest.mark.parametrize("dizi", [
    [(1920, 1080), (1024, 768)], [(1920, 1080), (1024, 768), (1920, 1080)], [(1500, 950), (1280, 720), (1500, 950)],
    [(1280, 720, "tam"), (1280, 720)], [(1500, 950, "tam"), (1500, 950)],
], ids=["1920-1024", "1920-1024-1920", "1500-1280-1500", "1280-tam-pencere", "1500-tam-pencere"])
def test_arac_yerlesimi_gecmissiz(tarayici, sunucu, dizi):
    """A10: boyut ve tam ekran değişikliklerinden sonra yerleşim, son boyutta yeni açılan sayfanınkiyle aynı (geçmiş yok)."""
    en, boy = dizi[0][:2]
    ctx, pg, hatalar = _yerlesim_sayfasi(tarayici, sunucu, en, boy)
    try:
        tam = False
        for adim in dizi:
            if len(adim) > 2:
                pg.click("#bn-tam"); tam = True
            elif tam:
                pg.click("#bn-tam"); tam = False
            pg.set_viewport_size({"width": adim[0], "height": adim[1]})
            _yerlesim_bekle(pg)
        once = pg.evaluate(YERLESIM_JS)
        _duzen_denetle(pg, str(dizi))
        _hatasiz(hatalar, str(dizi))
    finally:
        ctx.close()
    ctx, pg, hatalar = _yerlesim_sayfasi(tarayici, sunucu, dizi[-1][0], dizi[-1][1])
    try:
        taze = pg.evaluate(YERLESIM_JS)
    finally:
        ctx.close()
    assert once["katman"] == taze["katman"], (once["katman"], taze["katman"])
    assert once["tasan"] == taze["tasan"]
    assert once["kutular"] == taze["kutular"], {k: (once["kutular"].get(k), v) for k, v in taze["kutular"].items() if once["kutular"].get(k) != v}


def test_kullanici_katlamasi_kalir(tarayici, sunucu):
    """A12: kullanıcının katladığı kutular boyut değişince katlı kalır, ötekiler açık; kayıt sürüm 2, otoKatli/otoKonum yok."""
    ctx, pg, hatalar = _yerlesim_sayfasi(tarayici, sunucu, 1500, 950)
    try:
        for kid in ("k-aks", "k-sonuc"):
            pg.click(f".arac-kutu[data-kutu='{kid}'] .arac-kutu-katla")
            pg.wait_for_timeout(250)
        for en, boy in ((1280, 720), (1500, 950)):
            pg.set_viewport_size({"width": en, "height": boy})
            _yerlesim_bekle(pg)
            d = _duzen_denetle(pg, f"katlı {en}×{boy}")
            assert sorted(d["katli"]) == ["k-aks", "k-sonuc"], d["katli"]
        kayit = json.loads(pg.evaluate("localStorage.getItem('bina.arac')"))
        assert kayit["surum"] == 2
        assert all("otoKatli" not in k and "otoKonum" not in k for k in kayit["kutular"])
        assert sorted(k["id"] for k in kayit["kutular"] if k.get("katli")) == ["k-aks", "k-sonuc"]
        # sütundaki katlı kutu çip biçiminde (sütun genişliğinde), banttaki katlı başlık
        assert pg.evaluate("document.querySelector(\".arac-kutu[data-kutu='k-sonuc']\").classList.contains('arac-sutun-cip')")
        # katlı kutu açılınca şeridinin en öncelikli kutusu olur ve yerinde açılır
        pg.click(".arac-kutu[data-kutu='k-sonuc'] .arac-kutu-katla")
        pg.wait_for_timeout(300)
        assert pg.evaluate("document.querySelector(\".arac-kutu[data-kutu='k-sonuc']\").dataset.rihtim") == "sag"
        assert "k-sonuc" not in pg.evaluate("MatrisArac.tasanlar()")
        _hatasiz(hatalar, "katlı kutular")
    finally:
        ctx.close()


def test_kenara_sabitle_ve_surukleyerek_kenara_birak(tarayici, sunucu):
    """A13: 1280×720 penceresinde çekmeceden "Kenara sabitle" (ya da sağ kenara sürükleme) Ölçme'yi sağ sütuna açık yerleştirir; yerini
    alan kutunun çekmeceye düştüğü söylenir; sayfa yeniden yüklenince aynı yerleşim."""
    ctx, pg, hatalar = _yerlesim_sayfasi(tarayici, sunucu, 1280, 720)
    try:
        assert "k-olcme" in pg.evaluate("MatrisArac.tasanlar()")
        pg.click(".arac-tasma-ac")
        pg.wait_for_timeout(200)
        pg.click(".arac-tasma .arac-kutu[data-kutu='k-olcme'] .arac-kutu-menu-ac")
        pg.wait_for_timeout(150)
        ogeler = pg.evaluate("Array.from(document.querySelectorAll('.arac-menu .arac-menu-ad')).map(x => x.textContent)")
        assert "Kenara sabitle" in ogeler and "Sahnede yüzdür" in ogeler and "Kenar" in ogeler, ogeler
        pg.click(".arac-menu .arac-menu-oge:has-text('Kenara sabitle')")
        pg.wait_for_timeout(300)
        bildirim = pg.evaluate("document.querySelector('.arac-bildirim').textContent")
        tasan = pg.evaluate("MatrisArac.tasanlar()")
        assert "k-olcme" not in tasan and "k-sonuc" in tasan, tasan
        assert bildirim == "“Sonuç” sığmadı; ⋯ düğmesinden açılır.", bildirim
        assert pg.query_selector(".arac-tasma") is not None, "çekmece içinde çalışılırken açık kalır"
        pg.mouse.click(2, 2)          # dışarıya basınca çekmece kapanır
        pg.wait_for_timeout(200)
        assert pg.query_selector(".arac-tasma") is None
        _yerlesim_bekle(pg)
        d = _duzen_denetle(pg, "kenara sabitle")
        assert d["rihtim"]["k-olcme"] == ["sag", False]
        once = pg.evaluate(YERLESIM_JS)
        pg.reload()
        pg.click("button[data-sayfa='bina']")
        pg.wait_for_function("window.MatrisBina && MatrisBina.hazir()")
        _yerlesim_bekle(pg)
        sonra = pg.evaluate(YERLESIM_JS)
        assert sonra["tasan"] == once["tasan"] and sonra["kutular"]["k-olcme"] == once["kutular"]["k-olcme"]
        # sürükleyerek: çekmecedeki Sonuç'u tutamağından sağ kenara bırak → sağ sütunda açık, en öncelikli
        pg.click(".arac-tasma-ac")
        pg.wait_for_timeout(200)
        tut = pg.locator(".arac-tasma .arac-kutu[data-kutu='k-sonuc'] .arac-tutamak-izi").bounding_box()
        kr = pg.locator(".arac-kok").bounding_box()
        pg.mouse.move(tut["x"] + 4, tut["y"] + 7)
        pg.mouse.down()
        for i in range(1, 11):
            pg.mouse.move(tut["x"] + 4 + (kr["x"] + kr["width"] - 20 - tut["x"]) * i / 10, tut["y"] + 7 + (kr["y"] + 120 - tut["y"]) * i / 10)
            pg.wait_for_timeout(30)
        assert pg.evaluate("!!document.querySelector('.arac-rihtim-isaret')"), "bırakma işareti yok"
        pg.mouse.up()
        pg.wait_for_timeout(300)
        pg.mouse.click(2, 2)
        _yerlesim_bekle(pg)
        d = _duzen_denetle(pg, "sürükleyerek kenara")
        assert d["rihtim"].get("k-sonuc") == ["sag", False], d["rihtim"]
        assert "k-olcme" in d["tasan"], d["tasan"]
        _hatasiz(hatalar, "kenara sabitle")
    finally:
        ctx.close()


def test_yuzen_kutu_capasina_doner(tarayici, sunucu):
    """A14: sahnenin ortasına sürüklenen Analiz yüzer (yer "serbest", çapa); 1500→1024→1500 sonrası aynı yerde (±1 px); 1024'te kenardaki
    kutulara binmez."""
    ctx, pg, hatalar = _yerlesim_sayfasi(tarayici, sunucu, 1500, 950)
    try:
        tut = pg.locator(".arac-kutu[data-kutu='k-analiz'] .arac-tutamak-izi").bounding_box()
        sr = pg.locator("#bn-svg").bounding_box()
        hx, hy = sr["x"] + sr["width"] * 0.55, sr["y"] + sr["height"] * 0.45
        pg.mouse.move(tut["x"] + 4, tut["y"] + 7)
        pg.mouse.down()
        for i in range(1, 11):
            pg.mouse.move(tut["x"] + 4 + (hx - tut["x"]) * i / 10, tut["y"] + 7 + (hy - tut["y"]) * i / 10)
            pg.wait_for_timeout(30)
        pg.mouse.up()
        _yerlesim_bekle(pg)
        kayit = json.loads(pg.evaluate("localStorage.getItem('bina.arac')"))
        k = [x for x in kayit["kutular"] if x["id"] == "k-analiz"][0]
        assert k["yer"] == "serbest" and k["konum"], k
        konum = pg.evaluate("(() => { const d = document.querySelector(\".arac-kutu[data-kutu='k-analiz']\"); return [d.offsetLeft, d.offsetTop, d.classList.contains('arac-serbest')]; })()")
        assert konum[2], konum
        pg.set_viewport_size({"width": 1024, "height": 768})
        _yerlesim_bekle(pg)
        d = pg.evaluate(DUZEN_JS)
        assert not [h for h in d["hata"] if h.startswith(("A1", "A2"))], d["hata"]
        pg.set_viewport_size({"width": 1500, "height": 950})
        _yerlesim_bekle(pg)
        geri = pg.evaluate("(() => { const d = document.querySelector(\".arac-kutu[data-kutu='k-analiz']\"); return [d.offsetLeft, d.offsetTop]; })()")
        assert abs(geri[0] - konum[0]) <= 1 and abs(geri[1] - konum[1]) <= 1, (konum, geri)
        # yüzen kutunun menüsü: Yatay/Dikey yap ve "Kenara yerleştir"; kenara yerleşince şeridin en öncelikli kutusu
        pg.click(".arac-kutu[data-kutu='k-analiz'] .arac-kutu-menu-ac")
        pg.wait_for_timeout(150)
        ogeler = pg.evaluate("Array.from(document.querySelectorAll('.arac-menu .arac-menu-ad')).map(x => x.textContent)")
        assert "Kenara yerleştir" in ogeler and ("Dikey yap" in ogeler or "Yatay yap" in ogeler) and "Kenar" not in ogeler, ogeler
        pg.click(".arac-menu .arac-menu-oge:has-text('Kenara yerleştir')")
        pg.wait_for_timeout(300)
        assert pg.evaluate("document.querySelector(\".arac-kutu[data-kutu='k-analiz']\").dataset.rihtim") in ("ust", "alt", "sol", "sag")
        _hatasiz(hatalar, "yüzen kutu")
    finally:
        ctx.close()


# Taban 366e1c4'ün sürüm 1 yerleşimleri (boş profil): 1280×720 (Aks, Ölçme, Değiştirme, Üreteç katlı; Sonuç sığmadığı için kendiliğinden
# katlanmış: otoKatli) ve 1500×950 (birleşik "Düzenleme ve aks" kutusu). Komut listeleri sayfada katalogdan kurulur.
V1_KUTULAR = {
    "1280x720": [("k-cizim", "Çizim", "dikey", False, None, (48, 8, "sol", "ust"), "sol"), ("k-duzenleme", "Düzenleme", "yatay", False, None, (124, 8, "sol", "ust"), "ust"),
                 ("k-aks", "Aks", "yatay", True, None, (124, 8, "sag", "ust"), "ust"), ("k-gorunum", "Görünüm", "yatay", False, None, (124, 8, "sol", "alt"), "alt"),
                 ("k-analiz", "Analiz", "yatay", False, None, (124, 56, "sol", "alt"), "alt"), ("k-sonuc", "Sonuç", "dikey", True, True, (8, 8, "sag", "ust"), "sag"),
                 ("k-olcme", "Ölçme", "dikey", True, None, (84, 88, "sag", "ust"), "sag"), ("k-degistirme", "Değiştirme", "dikey", True, None, (84, 44, "sag", "ust"), "sag"),
                 ("k-uretec", "Üreteç ve yük", "dikey", True, None, (124, 56, "sol", "ust"), "sol")],
    "1500x950": [("k-cizim", "Çizim", "dikey", False, None, (8, 8, "sol", "ust"), "sol"), ("k-duzenleme", "Düzenleme ve aks", "yatay", False, None, (84, 8, "sol", "ust"), "ust"),
                 ("k-gorunum", "Görünüm", "yatay", False, None, (48, 8, "sol", "alt"), "alt"), ("k-analiz", "Analiz", "yatay", False, None, (166, 8, "sag", "alt"), "alt"),
                 ("k-sonuc", "Sonuç", "dikey", False, None, (8, 8, "sag", "ust"), "sag"), ("k-olcme", "Ölçme", "dikey", True, None, (8, 152, "sag", "alt"), "sag"),
                 ("k-degistirme", "Değiştirme", "dikey", True, None, (8, 196, "sag", "alt"), "sag"), ("k-uretec", "Üreteç ve yük", "dikey", True, None, (8, 160, "sol", "alt"), "sol")],
}
V1_KOMUT_JS = r"""(kutular) => {
  const g = (grup, cikar) => MatrisArac.KATALOG.filter(k => k.grup === grup && !(cikar || []).includes(k.id)).map(k => k.id);
  const URETEC = ['makas', 'besik-cerceve', 'asik', 'kren-yolu', 'mesnet', 'yuk-ata'], cizim = g('cizim', URETEC);
  cizim.splice(cizim.indexOf('hizli-panel') + 1, 0, 'duvar');
  const K = { 'k-cizim': cizim, 'k-duzenleme': g('duzenleme'), 'k-aks': g('aks'), 'k-gorunum': g('gorunum'), 'k-analiz': g('analiz'), 'k-sonuc': g('sonuc').concat(['ifc']),
    'k-olcme': g('olcme'), 'k-degistirme': g('degistirme'), 'k-uretec': URETEC };
  return { surum: 1, ad: 'bina', kutular: kutular.map(([id, ad, yon, katli, oto, c, kenar]) => Object.assign({ id, ad, yon, kucuk: true, saydamlik: 1, kilitli: false, gizli: false, katli,
    komutlar: ad === 'Düzenleme ve aks' ? K['k-duzenleme'].concat(K['k-aks']) : K[id], konum: { x: c[0], y: c[1], yx: c[2], yy: c[3] }, kenar },
    oto ? { otoKatli: true, otoKonum: { x: 8, y: 8, yx: 'sag', yy: 'ust' } } : {})) };
}"""


@pytest.mark.parametrize("kaynak", ["localStorage", "proje"])
@pytest.mark.parametrize("ornek", list(V1_KUTULAR))
def test_surum1_yerlesimi_kenar_seritlerine_gecer(tarayici, sunucu, ornek, kaynak):
    """A15: tabanın sürüm 1 yerleşimi (otoKatli, katlı Aks/Ölçme/Değiştirme/Üreteç; birleşik "Düzenleme ve aks") localStorage'dan ve
    .matris projesinden yüklenince sürüm 2 olur: Aks ayrı kutu, otoKatli yok, bütün kutular kenarda; 1280×720 sayılarına (A9) uyar."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, 1280, 720)
    try:
        v1 = pg.evaluate(V1_KOMUT_JS, [list(x) for x in V1_KUTULAR[ornek]])
        if kaynak == "localStorage":
            pg.evaluate("(y) => { localStorage.setItem('bina.arac', JSON.stringify(y)); localStorage.setItem('bina.arac.ek', JSON.stringify({ duvar: 1, ifc: 1 })); }", v1)
            pg.reload()
            pg.click("button[data-sayfa='bina']")
            pg.wait_for_function("window.MatrisBina && MatrisBina.hazir()")
        else:
            proje = {"tur": "matris-proje", "surum": 1, "bina": pg.evaluate("MatrisBina.bina()"), "arac_yerlesimi": v1}
            islendi = pg.evaluate("""(icerik) => { const e = new CustomEvent('masaustu-dosya-acildi', { detail: { icerik, ad: 'eski.matris' }, cancelable: true });
              window.dispatchEvent(e); return e.defaultPrevented; }""", json.dumps(proje))
            assert islendi
        _yerlesim_bekle(pg)
        assert pg.evaluate("document.querySelector('.arac-bildirim').textContent") == \
            "Araç kutuları kenar yerleşimine geçirildi; bir kutuyu sahneye sürükleyerek yüzdürebilirsiniz."
        y = pg.evaluate("MatrisArac.yerlesim()")
        assert y["surum"] == 2
        assert sorted(k["id"] for k in y["kutular"]) == sorted(KUTULAR)
        assert all(k["yer"] == "kenar" and k["konum"] is None and "otoKatli" not in k and not k["katli"] for k in y["kutular"]), y["kutular"]
        assert [k["id"] for k in y["kutular"]] == KUTULAR, "sürüm 2 öncelik sırası"
        assert next(k for k in y["kutular"] if k["id"] == "k-duzenleme")["ad"] == "Düzenleme"
        kayit = json.loads(pg.evaluate("localStorage.getItem('bina.arac')"))
        assert kayit["surum"] == 2 and all("otoKatli" not in k for k in kayit["kutular"])
        d = _duzen_denetle(pg, f"geçiş {ornek} {kaynak}")
        assert len(d["tasan"]) <= 3, d["tasan"]
        acik = {k for k, (_kn, katli) in d["rihtim"].items() if not katli}
        assert {"k-cizim", "k-duzenleme", "k-gorunum", "k-sonuc", "k-analiz"} <= acik, d["rihtim"]
        _hatasiz(hatalar, f"geçiş {ornek} {kaynak}")
    finally:
        ctx.close()


BALON_JS = r"""() => {
  const out = [], kr = document.querySelector('.arac-kok').getBoundingClientRect();
  document.querySelectorAll('#bn-svg .aks-balon').forEach(g => {
    const r = g.getBoundingClientRect();
    if (r.width < 2) return;
    const x = r.left + r.width / 2, y = r.top + r.height / 2;
    if (x < kr.left || y < kr.top || x > kr.right || y > kr.bottom) return;      // katmanın dışı (araç kutusu olamaz)
    const t = document.elementFromPoint(x, y), kk = t && t.closest && t.closest('.arac-kutu, .arac-yonetici-ac, .arac-tasma-ac');
    if (kk) out.push((g.textContent || '').trim().slice(0, 8) + ' < ' + (kk.dataset.kutu || kk.className.split(' ')[0]));
  });
  return out;
}"""


@pytest.mark.parametrize("en,boy", [(1280, 720), (1024, 768)])
def test_aks_balonlari_kutularin_altinda_kalmaz(tarayici, sunucu, en, boy):
    """A16: celik-sanayi-4hol, betonarme-4kat-4x3 ve celik-cbf-3kat 3B, plan ve önden görünüşte aks balonları ve kot etiketleri
    (.aks-balon / .aks-zbalon) kutuların altında değil (3B'de R-8 kenar payı)."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, en, boy)
    try:
        for ad in ("celik-sanayi-4hol", "betonarme-4kat-4x3", "celik-cbf-3kat"):
            _sablon(pg, ad)
            for g in ("gor-3b", "gor-plan", "gor-on"):
                pg.evaluate(f"MatrisArac.calistir('{g}')")
                _yerlesim_bekle(pg)
                assert pg.evaluate("document.querySelectorAll('#bn-svg .aks-balon').length") > 0, (ad, g)
                assert pg.evaluate(BALON_JS) == [], (ad, g, en, boy)
            pg.evaluate("MatrisArac.calistir('gor-3b')")
        _hatasiz(hatalar, f"balonlar {en}×{boy}")
    finally:
        ctx.close()


@pytest.mark.parametrize("tam", [False, True], ids=["pencere", "tam"])
def test_mobil_serit(tarayici, sunucu, tam):
    """A18: 390×844 (katman < 640 px): alt şerit, taşma düğmesi yok; model şeridin altında kalmaz; her kutunun çipi var ve çip grubunu
    görünür kaydırır; sığdırma oranı ve model boyu (A7, A8)."""
    ctx, pg, hatalar = _yerlesim_sayfasi(tarayici, sunucu, 390, 844, tam)
    try:
        assert pg.query_selector(".arac-serit") is not None
        assert pg.query_selector(".arac-tasma-ac") is None and pg.query_selector(".arac-yonetici-ac") is None
        d = pg.evaluate(DUZEN_JS)
        assert d["hata"] == [], d["hata"]
        assert d["oran"] >= (0.58 if tam else 0.45), d["oran"]
        assert d["modelH"] >= (195 if tam else 175), d["modelH"]
        cipler = pg.evaluate("Array.from(document.querySelectorAll('.arac-serit-cip')).map(c => c.dataset.git)")
        assert sorted(cipler) == sorted(KUTULAR), cipler
        for kid in cipler:
            pg.click(f".arac-serit-cip[data-git='{kid}']")
            pg.wait_for_timeout(450)
            gorunur = pg.evaluate("""(k) => { const g = document.querySelector(`.arac-serit-grup[data-kutu='${k}']`), v = g.parentNode.getBoundingClientRect(), r = g.getBoundingClientRect();
              return r.left >= v.left - 1 && r.left < v.right - 20; }""", kid)
            assert gorunur, kid
        _hatasiz(hatalar, "mobil şerit")
    finally:
        ctx.close()


# modelin aks kesişimlerinden (her kat kotunda) bir araç kutusunun altında kalanlar
KESISIM_ORTULU_JS = """() => {
  const b = MatrisBina.bina(), iz = MatrisBina.izdusum(), svg = document.getElementById('bn-svg'), out = [];
  for (const k of b.katlar) for (const ax of b.akslar.x) for (const ay of b.akslar.y) {
    const p = iz.P(+ax.konum, +ay.konum, +k.kot), pt = svg.createSVGPoint(); pt.x = p[0]; pt.y = p[1];
    const r = pt.matrixTransform(svg.getScreenCTM()), t = document.elementFromPoint(r.x, r.y), kk = t && t.closest && t.closest('.arac-kutu, .arac-yonetici-ac, .arac-tasma-ac');
    if (kk) out.push(ax.ad + ay.ad + '@' + k.kot + ':' + (kk.dataset.kutu || kk.className));
  }
  return out;
}"""


@pytest.mark.parametrize("en,boy", [(1500, 950), (1280, 720)])
def test_tam_ekranda_model_kutularin_altinda_kalmaz(tarayici, sunucu, en, boy):
    """Tam ekranda (4 katlı model) kutular kenar şeritlerinde: model kesişimleri kutuların altında değil; sığdırma dikdörtgeni
    (izdusum().alan) kenar paylarının içinde ve katmanın en az %50'si; çıkınca pencere yerleşimine döner."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu, en, boy)
    try:
        _sablon(pg, "betonarme-4kat-4x3")
        once = pg.evaluate(YERLESIM_JS)
        pg.click("#bn-tam")
        pg.wait_for_timeout(900)
        assert pg.evaluate("document.body.classList.contains('bn-tam-ekran')")
        _yerlesim_bekle(pg)
        assert pg.evaluate(KESISIM_ORTULU_JS) == [], f"tam ekran {en}×{boy}"
        d = _duzen_denetle(pg, f"tam ekran {en}×{boy}")
        pay = pg.evaluate("MatrisArac.kenarPaylari()")
        alan, katman = pg.evaluate("MatrisBina.izdusum().alan"), d["katman"]
        kr, sr = pg.locator(".arac-kok").bounding_box(), pg.locator("#bn-svg").bounding_box()
        # sığdırma dikdörtgeni katman koordinatında kenar paylarının içinde
        x0, y0 = sr["x"] + alan["x"] - kr["x"], sr["y"] + alan["y"] - kr["y"]
        assert x0 >= pay["sol"] - 1 and y0 >= pay["ust"] - 1, (alan, pay)
        assert x0 + alan["w"] <= katman[0] - pay["sag"] + 1 and y0 + alan["h"] <= katman[1] - pay["alt"] + 1, (alan, pay, katman)
        assert d["oran"] >= 0.5, d["oran"]
        pg.click("#bn-tam")
        pg.wait_for_timeout(400)
        _yerlesim_bekle(pg)
        assert pg.evaluate(YERLESIM_JS) == once, "tam ekrandan çıkınca pencere yerleşimi"
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


# ---- bina sayfası kalan işleri: duvar etiketi (K-21), şablon adresi (K-40), çatıya kat kopyası (K-43), sayfa tuşları (K-4),
# CSV içe aktarma kancası (K-3), yaylı mesnet simgesi (K-10), genel modelde temel (K-1), yük akışı sütunları (K-41)

def test_duvar_secenekleri_degeri_bir_kez_yazar(sayfa):
    """K-21: motorun duvar adı birim ağırlığı taşır; kiriş paneli, genel çubuk paneli, sihirbaz ve Kütüphane kartlarında değer bir kez."""
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("MatrisBina.gorunumAyarla({ kat: 1 }); MatrisBina.seciliAyarla([{ tur: 'kiris', no: MatrisBina.bina().kirisler.filter(k => k.kat === 1)[0].no }])")
    pg.wait_for_timeout(200)
    secenekler = pg.evaluate("Array.from(document.querySelectorAll('#bn-panel-icerik select[data-oz=duvar] option')).map(o => o.textContent)")
    assert len(secenekler) >= 2, secenekler
    pg.evaluate("document.getElementById('bn-sihirbaz').click()")          # bina sihirbazı (yeni bina)
    pg.wait_for_timeout(200)
    sihirbaz = pg.evaluate("Array.from(document.querySelectorAll('#bn-sihirbaz-form select[name=duvarTip] option')).map(o => o.textContent)")
    assert len(sihirbaz) >= 2, sihirbaz
    secenekler += sihirbaz
    pg.evaluate("document.getElementById('bn-sihirbaz-dlg').close()")
    assert pg.evaluate("MatrisBina.kaplamaKapat(), MatrisBina.seciliAyarla([]), MatrisArac.calistir('kutuphane')")
    pg.wait_for_timeout(200)
    kartlar = pg.evaluate("Array.from(document.querySelectorAll('#bn-panel-icerik .bn-kart')).map(k => k.textContent).filter(t => t.includes('kN/m²'))")
    assert kartlar
    _sablon(pg, "celik-cbf-3kat")
    pg.click("[data-psek='nesne']")
    pg.evaluate("MatrisBina.seciliAyarla([{ tur: 'cubuk', no: MatrisBina.bina().cubuklar.filter(c => c.tur === 'kiris')[0].no }])")
    pg.wait_for_timeout(200)
    genel = pg.evaluate("Array.from(document.querySelectorAll('#bn-panel-icerik select[data-oz3=duvar] option')).map(o => o.textContent)")
    assert len(genel) >= 2, genel
    for metin in [x for x in secenekler + genel if x != "Duvar yok" and "Başka duvar" not in x] + kartlar:
        assert metin.count("kN/m²") == 1, metin
    _hatasiz(hatalar, "duvar etiketi")


def _soguk_ac(tarayici, sunucu, adres):
    ctx = tarayici.new_context(service_workers="block", viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    hatalar = []
    pg.on("pageerror", lambda e: hatalar.append("pageerror: " + str(e)))
    pg.on("console", lambda m: hatalar.append("console: " + m.text) if m.type == "error" and not any(y in m.text for y in YOKSAY) else None)
    pg.set_default_timeout(120_000)
    pg.goto(sunucu + "index.html" + adres)
    pg.wait_for_function("window.MatrisBina && MatrisBina.hazir()")
    return ctx, pg, hatalar


def test_sablon_adres_baglantisi(tarayici, sunucu):
    """K-40: soğuk açılışta #bina/sablon/<ad> şablonu yükler ve seçicide gösterir; bilinmeyen adda yüklü varsayılan model ve seçici kalır,
    şablon adları söylenir, adres #bina olur."""
    ctx, pg, hatalar = _soguk_ac(tarayici, sunucu, "#bina/sablon/celik-cbf-3kat")
    try:
        pg.wait_for_function("MatrisBina.bina().surum >= 3 && document.querySelector('select#bn-sablon').value === 'celik-cbf-3kat'")
        assert "çapraz" in pg.evaluate("MatrisBina.bina().baslik")
        _hatasiz(hatalar, "şablon adresi")
    finally:
        ctx.close()
    ctx, pg, hatalar = _soguk_ac(tarayici, sunucu, "#bina/sablon/yok-boyle-sablon")
    try:
        pg.wait_for_function("document.getElementById('toast-metin').textContent.indexOf('Şablon bulunamadı') === 0")
        toast = pg.evaluate("document.getElementById('toast-metin').textContent")
        assert toast.startswith("Şablon bulunamadı: yok-boyle-sablon. Şablonlar: ") and "celik-cbf-3kat" in toast and "betonarme-2kat-3x2" in toast, toast
        assert pg.evaluate("location.hash") == "#bina"
        pg.wait_for_function("document.querySelector('select#bn-sablon').value === 'betonarme-2kat-3x2'")
        assert pg.evaluate("MatrisBina.bina().baslik").startswith("2 katlı betonarme")
        _hatasiz(hatalar, "bilinmeyen şablon adresi")
    finally:
        ctx.close()


def test_alt_kati_cati_katina_kopyalamak_parapeti_korur(sayfa, kopru):
    """K-43: dolu çatıya "Alt katı kopyala" önce sorar; çatı kirişlerinin duvarı (parapet duvar_h 1,0 m) aks açıklığına göre korunur;
    ΣG köprüyle aynı."""
    pg, hatalar = sayfa
    ham = yapi.bina_sablon("betonarme-2kat-3x2")
    parapet = _parapetler(ham, 2)
    _sablon(pg, "betonarme-2kat-3x2")
    sorular = []
    pg.on("dialog", lambda d: sorular.append(d.message))
    pg.evaluate("MatrisBina.gorunumAyarla({ kat: 2 })")
    pg.evaluate("document.getElementById('bn-kat-kopyala').click()")
    pg.wait_for_timeout(250)
    assert "Çatı katı alttaki katın kopyasıyla değişecek. Devam edilsin mi?" in sorular, sorular
    b = pg.evaluate("MatrisBina.bina()")
    assert _parapetler(b, 2) == parapet
    n = sum(1 for k in b["kirisler"] if k["kat"] == 2 and k.get("duvar_h") is not None)
    assert pg.evaluate("document.getElementById('toast-metin').textContent") == f"Çatı parapetleri korundu ({n} kiriş)."
    assert _coz(pg) is True, _hata_metni(pg)
    assert pg.evaluate("MatrisBina.veri().yukler.toplam.G") == pytest.approx(_kopru_coz(kopru, b)["yukler"]["toplam"]["G"], rel=1e-9)
    _hatasiz(hatalar, "çatıya kat kopyası")


def test_kisayol_penceresi_sayfa_tuslari(sayfa):
    """K-4 (C22): "?" penceresinin sayfa satırları MatrisArac.SAYFA_TUSLARI'ndan (kayıtta olan tuş atlanır), başlık grubun adı; Enter var."""
    pg, hatalar = sayfa
    pg.evaluate("MatrisBina.kaplamaKapat(); MatrisBina.seciliAyarla([]); document.activeElement && document.activeElement.blur()")
    pg.keyboard.press("?")
    pg.wait_for_selector(".bn-kaplama[data-kaplama='kisayollar']")
    satirlar = pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll(".bn-kaplama[data-kaplama='kisayollar'] h3").forEach(h => {
        h.nextElementSibling.querySelectorAll('tr').forEach(r => out.push([h.textContent, r.querySelector('kbd').textContent, r.querySelector('td').textContent]));
      });
      return out;
    }""")
    beklenen = pg.evaluate("""() => {
      const kayit = new Set(MatrisArac.kisayollar().map(k => k.kisayol));
      return MatrisArac.SAYFA_TUSLARI.filter(x => !kayit.has(x.kisayol)).map(x => [MatrisArac.grupAdi(x.grup), x.kisayol, x.ad]);
    }""")
    assert beklenen and all(b in satirlar for b in beklenen), (beklenen, satirlar)
    assert ["Sayfa", "Enter", "Bağlam menüsünde: Bilgi"] in satirlar
    assert sum(1 for s in satirlar if s[1] == "F") == 1          # F kayıttan (Tam ekran); sayfa satırı yinelenmez
    pg.evaluate("MatrisBina.kaplamaKapat()")
    _hatasiz(hatalar, "kısayol penceresi")


def test_masaustu_csv_iceri_aktarma_kancasi(sayfa):
    """K-3 (C23): masaüstü "csv-iceri" komutu tablo editörünü csvIceri: true ile açar; "tablolar" olduğu gibi (csvIceri yok)."""
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("""(() => { const ac = MatrisTablo.ac; window.__tabloSec = [];
      MatrisTablo.ac = function (k, s) { window.__tabloSec.push(!!(s && s.csvIceri)); return ac.apply(this, arguments); }; })()""")
    for komut in ("csv-iceri", "tablolar"):
        islendi = pg.evaluate("""(k) => { const e = new CustomEvent('masaustu-komut', { detail: { komut: k }, cancelable: true });
          window.dispatchEvent(e); return e.defaultPrevented; }""", komut)
        assert islendi, komut
        pg.wait_for_function("window.__tabloSec.length >= " + ("1" if komut == "csv-iceri" else "2"))
        pg.evaluate("MatrisBina.kaplamaKapat()")
    assert pg.evaluate("window.__tabloSec") == [True, False]
    _hatasiz(hatalar, "CSV kancası")


def test_yayli_mesnet_yay_simgesiyle_cizilir(sayfa):
    """K-10 (C13): yay rijitliği (kx … krz) verilen açık mesnet sahnede yay simgesiyle; ipucu rijitlikleri listeler."""
    pg, hatalar = sayfa
    _sablon(pg, "celik-cbf-3kat")
    pg.evaluate("""(() => { const b = JSON.parse(JSON.stringify(MatrisBina.bina()));
      b.mesnetler = [{ dugum: { aks: ['B', '2'], z: '±0.00' }, ux: true, uy: true, kz: 10000, kry: 2500.5 }, { dugum: { aks: ['C', '2'], z: '±0.00' }, ux: true, uy: true, uz: true }];
      MatrisBina.binaAyarla(b, {}); })()""")
    pg.wait_for_timeout(300)
    yay = pg.evaluate("""() => Array.from(document.querySelectorAll('#bn-svg g.b3-mesnet[data-tur=mesnet]')).map(g => [g.dataset.no, g.dataset.yay || '',
      (g.querySelector('title') || {}).textContent || '', !!g.querySelector('.b3-yay-c')])""")
    assert ["1", "1", "Yaylı mesnet 1: k_z = 10.000 kN/m, k_ry = 2.500,5 kN·m/rad", True] in yay, yay
    assert any(x[0] == "2" and x[1] == "" and not x[3] for x in yay), yay
    _hatasiz(hatalar, "yaylı mesnet")


@pytest.mark.parametrize("ad,tip", [("betonarme-3kat-surekli-temel", "surekli"), ("betonarme-4kat-radye", "radye")])
def test_genel_modelde_mutemadi_ve_radye_temel(sayfa, ad, tip):
    """K-1 (C11): genelleştirilen mütemadi / radye temelli model temel tipini korur, çözülür; Temel sekmesi basınç haritası; sahnede
    şerit / plak (motor geometrisi); şerit bilgisi D/C; ısı haritasında radye katmanı; IFC'de STRIP_FOOTING / BASESLAB.
    (motor, çizim ve IFC paketleriyle bütünleştirmeden sonra geçer)"""
    pg, hatalar = sayfa
    _sablon(pg, ad)
    tip_ = pg.evaluate("""() => { const r = MatrisBinaCizim.genellestirHazirla(JSON.parse(JSON.stringify(MatrisBina.bina())));
      MatrisBina.binaAyarla(r.model, { etiket: 'genel' }); return MatrisBina.bina().temeller.tip; }""")
    assert tip_ == tip and pg.evaluate("MatrisBina.s3Var()")
    assert _coz(pg) is True, _hata_metni(pg)
    assert "çözülmüyor" not in _hata_metni(pg)
    v = pg.evaluate("(() => { const v = MatrisBina.veri(); return { model: v.model, tip: v.temel && v.temel.tip, hat: ((v.temel && v.temel.hatlar) || []).length }; })()")
    assert v["model"] == "genel" and v["tip"] == tip, v
    icerik = _sekmeleri_gez(pg)
    pg.click("#bn-sonuc .bn-sekme[data-sekme='temel']")
    pg.wait_for_timeout(200)
    assert pg.evaluate("!!document.querySelector('#bn-temel-harita svg')")
    assert "genel modelde çözülmez" not in icerik["temel"] and "çözülmez" not in icerik["temel"]
    pg.evaluate("MatrisArac.calistir('gor-3b')")
    pg.wait_for_timeout(300)
    if tip == "surekli":
        assert pg.evaluate("document.querySelectorAll('#bn-svg [data-tur=temel-kirisi]').length") > 0
        hd = pg.evaluate("(() => { const e = document.querySelector('#bn-svg [data-tur=temel-kirisi]'); return { tur: 'temel', alt: 'surekli', no: +e.dataset.no, aks: e.dataset.aks, yon: e.dataset.yon }; })()")
        bilgi = pg.evaluate("(h) => MatrisBilgi.tsv(MatrisBilgi.bilgi(h, MatrisBina.bina(), MatrisBina.veri()))", hd)
        assert "D/C" in bilgi, bilgi[:600]
        assert pg.evaluate("(MatrisIFC.uretAyrintili(MatrisBina.bina(), MatrisBina.veri()).metin.match(/\\.STRIP_FOOTING\\./g) || []).length") == v["hat"] == 6
    else:
        assert pg.evaluate("document.querySelectorAll('#bn-svg [data-tur=radye]').length") > 0
        pg.evaluate("MatrisBina.isiAc()")
        pg.wait_for_selector(".isi-radye-kutu")
        pg.wait_for_function("!document.querySelector('.isi-radye-kutu').hidden")
        pg.evaluate("MatrisBina.kaplamaKapat()")
        assert pg.evaluate("(MatrisIFC.uretAyrintili(MatrisBina.bina(), MatrisBina.veri()).metin.match(/\\.BASESLAB\\./g) || []).length") == 1
    _hatasiz(hatalar, f"genel {tip}")


def test_genel_yuk_akisi_sutunlari(sayfa):
    """K-41 (C15): genel model akış şeması paneller → yatay çubuklar → düşey / eğik çubuklar → mesnetler; mesnet düğümleri (M…); çubuk
    adları Türkçe tür adıyla; bant ipucu kN ve durum. (motorun çubuk → çubuk / mesnet kenarlarıyla bütünleştirmeden sonra geçer)"""
    pg, hatalar = sayfa
    _sablon(pg, "celik-cbf-3kat")
    assert _coz(pg) is True, _hata_metni(pg)
    pg.click("#bn-sonuc .bn-sekme[data-sekme='akis']")
    pg.wait_for_timeout(200)
    basliklar = pg.evaluate("Array.from(document.querySelectorAll('.bn-sankey-bsl')).map(t => t.textContent)")
    assert basliklar == ["Paneller", "Yatay çubuklar", "Düşey ve eğik çubuklar", "Mesnetler"], basliklar
    sutun = pg.evaluate("new Set(Array.from(document.querySelectorAll('#bn-sankey .bn-sankey-dugum rect')).map(r => r.getAttribute('x'))).size")
    assert sutun >= 4, sutun
    assert pg.evaluate("document.querySelectorAll('#bn-sankey [data-sankey^=M]').length") > 0
    assert pg.evaluate("Array.from(document.querySelectorAll('#bn-sankey [data-sankey^=Ç] title')).some(t => / \\((kiriş|kolon|çapraz)\\) /.test(t.textContent))")
    ipucu = pg.evaluate("(document.querySelector('#bn-sankey path.bn-sankey-bant title') || {}).textContent || ''")
    assert " kN (" in ipucu, ipucu
    _hatasiz(hatalar, "yük akışı sütunları")


def test_genel_yuk_akisi_sutunlari_sozlesme_ornegi(sayfa):
    """K-41 (C15), motordan bağımsız: çözüme sözleşme biçiminde çubuk → çubuk, çubuk → mesnet ve düğüm yükü kenarları eklenince şema
    dört grup sütununa dizilir (kolon zinciri alt sütunlarda), mesnet ve düğüm yükü düğümleri adresle, bant ipucu kN ve durumla,
    sankey_kesildi notu gösterilir; tursuz eski kenar panel payıdır."""
    pg, hatalar = sayfa
    _sablon(pg, "celik-cbf-3kat")
    assert _coz(pg) is True, _hata_metni(pg)
    pg.evaluate("""(() => {
      const v = MatrisBina.veri(), nd = {}, ag = v.ag;
      ag.dugumler.forEach(d => { nd[d.no] = d; });
      const kolon = ag.cubuklar.filter(c => c.tur === 'kolon'), kiris = ag.cubuklar.filter(c => c.tur === 'kiris');
      const alt = c => (nd[c.i].Z <= nd[c.j].Z ? c.i : c.j), ust = c => (nd[c.i].Z <= nd[c.j].Z ? c.j : c.i);
      const ek = [];
      kolon.forEach(c => {
        if (nd[alt(c)].Z < 1e-6) ek.push({ kaynak: 'Ç' + c.no, hedef: 'M' + alt(c), durum: 'G', kN: 30, tur: 'cubuk-mesnet' });
        const ustteki = kolon.find(k => alt(k) === ust(c));
        if (ustteki) ek.push({ kaynak: 'Ç' + ustteki.no, hedef: 'Ç' + c.no, durum: 'G', kN: 12, tur: 'cubuk-cubuk' });
      });
      kiris.forEach(k => { const c = kolon.find(x => ust(x) === k.i || ust(x) === k.j); if (c) ek.push({ kaynak: 'Ç' + k.no, hedef: 'Ç' + c.no, durum: 'G', kN: 6, tur: 'cubuk-cubuk' }); });
      const k0 = kolon.find(c => nd[alt(c)].Z < 1e-6);
      ek.push({ kaynak: 'D' + ust(k0), hedef: 'Ç' + k0.no, durum: 'G', kN: 4, tur: 'dugum-cubuk' });
      v.akis.sankey = v.akis.sankey.concat(ek);
      v.akis.sankey_kesildi = { G: 3 };
    })()""")
    pg.click("#bn-sonuc .bn-sekme[data-sekme='akis']")
    pg.wait_for_timeout(250)
    basliklar = pg.evaluate("Array.from(document.querySelectorAll('.bn-sankey-bsl')).map(t => t.textContent)")
    assert basliklar == ["Paneller ve düğüm yükleri", "Yatay çubuklar", "Düşey ve eğik çubuklar", "Mesnetler"], basliklar
    # kolon zinciri (üst kat kolonu → alt kat kolonu) düşey çubuk grubunda birden çok sütun: en az 6 sütun
    sutun = pg.evaluate("new Set(Array.from(document.querySelectorAll('#bn-sankey .bn-sankey-dugum rect')).map(r => r.getAttribute('x'))).size")
    assert sutun >= 6, sutun
    m = pg.evaluate("Array.from(document.querySelectorAll('#bn-sankey [data-sankey^=M] title')).map(t => t.textContent)")
    assert m and all(t.startswith("M ") and "/±0.00" in t for t in m), m[:3]
    d = pg.evaluate("Array.from(document.querySelectorAll('#bn-sankey [data-sankey^=D] title')).map(t => t.textContent)")
    assert d and d[0].startswith("D "), d
    adlar = pg.evaluate("Array.from(document.querySelectorAll('#bn-sankey [data-sankey^=Ç] title')).map(t => t.textContent)")
    assert any(" (kolon) " in t for t in adlar) and any(" (kiriş) " in t for t in adlar), adlar[:5]
    ipucu = pg.evaluate("Array.from(document.querySelectorAll('#bn-sankey path.bn-sankey-bant title')).map(t => t.textContent)")
    assert any(t.endswith(" kN (G)") and "→ M " in t for t in ipucu), ipucu[:3]
    notlar = pg.evaluate("Array.from(document.querySelectorAll('#bn-sankey .not')).map(n => n.textContent)")
    assert "Akış şemasında en büyük kenarlar gösterildi (3 kenar atlandı)." in notlar, notlar
    _hatasiz(hatalar, "yük akışı sözleşme örneği")


@pytest.mark.parametrize("ad,tip", [("betonarme-3kat-surekli-temel", "surekli"), ("betonarme-4kat-radye", "radye")])
def test_genel_modelde_temel_arayuzu(sayfa, ad, tip):
    """K-1 (C11.5, C11.7), motordan bağımsız: temel tipi korunarak genelleştirilen modelde Temel paneli mütemadi / radyeyi açık tutar
    ve genel model notunu gösterir; sayfa denetimi çözümü engellemez; sahnede GLOBAL akslar boyunca temel kirişleri / radye plağı ve
    Winkler yayları çizilir, tekil temel mesnet simgesi (C3) çizilmez."""
    pg, hatalar = sayfa
    _sablon(pg, ad)
    pg.evaluate("""() => { const b0 = JSON.parse(JSON.stringify(MatrisBina.bina())), r = MatrisBinaCizim.genellestirHazirla(b0);
      r.model.temeller = b0.temeller; MatrisBina.binaAyarla(r.model, { etiket: 'genel' }); }""")
    assert pg.evaluate("MatrisBina.s3Var()") and pg.evaluate("MatrisBina.bina().temeller.tip") == tip
    pg.click("[data-psek='bina']")
    pg.wait_for_timeout(200)
    assert pg.evaluate("document.querySelectorAll('[data-temel-tip]:disabled').length") == 0
    notu = pg.evaluate("(document.querySelector('.bn-temel-s3-not') || {}).textContent || ''")
    assert notu.startswith("Genel modelde temel kirişleri GLOBAL X/Y aks çizgileri boyunca"), notu
    pg.evaluate("MatrisArac.calistir('gor-3b'); MatrisBina.gorunumAyarla({ kat: 0 })")
    pg.wait_for_timeout(300)
    if tip == "surekli":
        akslar = pg.evaluate("Array.from(new Set(Array.from(document.querySelectorAll('#bn-svg [data-tur=temel-kirisi]')).map(e => e.dataset.aks)))")
        b = pg.evaluate("MatrisBina.bina()")
        assert akslar and set(akslar) <= {a["ad"] for a in b["akslar"]["x"] + b["akslar"]["y"]}, akslar
    else:
        assert pg.evaluate("document.querySelectorAll('#bn-svg [data-tur=radye]').length") > 0
    assert pg.evaluate("document.querySelectorAll('#bn-svg g.b3-mesnet.b3-winkler').length") > 0
    assert pg.evaluate("document.querySelectorAll('#bn-svg [data-s3-taban]').length") == 0
    _coz(pg)
    assert "Temel panelinde Tekil seçin" not in _hata_metni(pg)
    _hatasiz(hatalar, f"genel temel arayüzü {tip}")
