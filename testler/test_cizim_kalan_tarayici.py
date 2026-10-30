# -*- coding: utf-8 -*-
"""Çizim araçları kalan işler — tarayıcı testi (paket cizim; sözleşme C24: fikstürler testler/test_bina_tarayici.py'den
KOPYALANMIŞTIR, o modül içe aktarılmaz).

Sayfa gerçek tarayıcıda (başsız) açılır; motor Pyodide yerine CPython'da çalışır: ``testler/tarayici_sunucu.py`` alt süreci
``docs/`` klasörünü sunar ve ``/motor.worker.js`` yerine istekleri ``web_kopru.calistir``'a ileten ara worker verir.

Adımlar:
1. K-1 / K-23: mütemadi temelli aks–kat şablonunda Böl → genel model kapısının onay metni "Böl — Model genel …" (temel yan cümlesi
   yok); temeller.tip "surekli" kalır.
2. K-10 (C13): celik-cbf-3kat B2/±0.00'a Mesnet aracı "Yaylı (elastik)": "Yaylı mesnet" penceresi (altı alan, yalnız k_z = 10000
   dolu; ≤ 0 alanlar reddedilir); kayıt {dugum, kz}; çözüm sonrası mesnet denetçisi "yaylı mesnet" ve "k_z = 10 000 kN/m".
3. K-15 (C14): celik-cbf-3kat C2/+3.50'ye ankastre: "Rijit diyaframlı kat" penceresi dört seçenek (klavyeyle odaklanan düğmeler);
   Vazgeç modeli değiştirmez; "Yalnız düşey mesnet", "Bu katın diyaframını esnek yap" ve "Olduğu gibi uygula" ile kurulan modeller
   çözülür; "Olduğu gibi uygula"da mesnet denetçisi "Diyafram bağı kuvvetleri" tablosunu gösterir. Aks–kat (depremli)
   betonarme-3kat-3x3'te soru genel model kapısından önce sorulur, "Yalnız düşey mesnet" modeli genelleştirir ve çözülür.
4. K-20 (C17): betonarme-2kat-3x2 + B2/Temel açık mesnet (karma model, genel çözüm): döşeme 1 denetçisi "Panel yükleri (çözüm)".
5. K-32 / K-31 (C19): betonarme-2kat-3x2 kolon 1 kesit önerisinde "Kesit grubuna uygula (12 çubuk)": tek geri al adımı, yeniden
   çözüm, "Grubun gerçek D/C maks"; Hepsini uygula öncesi "Hesaplanıyor: en çok 4 çözüm, yaklaşık …" ve sonrası "Süre: …".
6. K-22: Makas üreteci penceresinde "Düzlem dışı tutma" seçeneği.

Motor paketinin motor tarafını gerektiren adımlar (birleştirmeden sonra geçer): 2 (yaylı mesnet okunur, ag.mesnetler tip "yay"),
3'ün "Olduğu gibi uygula"sı (rijit diyafram düğümünde ux/uy/rz ceza yayı), 4 (panel kaynağı), 5'in "Süre"si (sure_ms).
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


# ---------------------------------------------------------------------------------------------------------------------------
# testler/test_bina_tarayici.py'den kopya fikstürler (C24)
def _tarayici_yolu():
    adaylar = [os.environ.get("MATRIS_CHROMIUM") or "", "/opt/pw-browsers/chromium"] + sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    return next((a for a in adaylar if a and os.path.isfile(a) and os.access(a, os.X_OK)), None)


TARAYICI = _tarayici_yolu()
pytestmark = pytest.mark.skipif(sync_playwright is None or TARAYICI is None, reason="playwright ya da Chromium yok")

# ağ erişimi olmayan ortamda beklenen konsol iletileri (yazı tipi / CDN istekleri, service worker kaydı)
YOKSAY = ("net::ERR", "Failed to load resource", "service worker", "Service Worker", "ServiceWorker")


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
    """Yeni bağlam (boş localStorage: varsayılan araç kutusu yerleşimi) ve Bina sayfası. Onay pencereleri (window.confirm) kabul
    edilir ve iletileri sayfa nesnesinin __onaylar listesine yazılır."""
    ctx = tarayici.new_context(service_workers="block", viewport={"width": en, "height": boy})
    pg = ctx.new_page()
    hatalar, onaylar = [], []
    pg.on("pageerror", lambda e: hatalar.append("pageerror: " + str(e)))
    pg.on("console", lambda m: hatalar.append("console: " + m.text)
          if m.type == "error" and not any(y in m.text for y in YOKSAY) else None)

    def _onay(d):
        onaylar.append(d.message)
        d.accept()
    pg.on("dialog", _onay)
    pg.set_default_timeout(120_000)
    pg.goto(sunucu + "index.html")
    pg.click("button[data-sayfa='bina']")
    pg.wait_for_function("window.MatrisBina && MatrisBina.hazir() && window.MatrisBinaCizim")
    pg.evaluate("""() => { window.__toast = []; const el = document.getElementById('toast-metin');
      new MutationObserver(() => window.__toast.push(el.textContent)).observe(el, { childList: true, characterData: true, subtree: true }); }""")
    pg.__onaylar = onaylar
    return ctx, pg, hatalar


@pytest.fixture(scope="module")
def sayfa(tarayici, sunucu):
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu)
    try:
        yield pg, hatalar
    finally:
        ctx.close()


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


def _hatasiz(hatalar, adim):
    assert not hatalar, f"{adim}: " + " | ".join(hatalar)[:3000]


# ---------------------------------------------------------------------------------------------------------------------------
# yardımcılar
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


def _toast_bekle(pg, parca, zaman=180_000):
    pg.wait_for_function("(p) => (window.__toast || []).some(t => t.indexOf(p) >= 0)", arg=parca, timeout=zaman)
    return [t for t in pg.evaluate("window.__toast") if parca in t]


def _mesnet_araci(pg, secenek, duzlem_z, ref):
    """Mesnet aracını seçenekle açar, plan görünümünde (duzlem_z) REF'in kesişimine dokunur."""
    pg.evaluate("MatrisBina.duzlemSec('z', " + json.dumps(duzlem_z) + ")")
    pg.wait_for_timeout(300)
    pg.evaluate("MatrisArac.komut('mesnet').secenekSec(" + json.dumps(secenek) + ")")
    pg.wait_for_timeout(150)
    assert pg.evaluate("MatrisBina.kip()") == "mesnet"
    P = pg.evaluate("(r) => MatrisBina.refKoordinat(r)", ref)
    assert P, ref
    _tikla(pg, P)


def _kaplama(pg):
    return pg.evaluate("(() => { const k = document.querySelector('.bn-kaplama'); return k ? { tur: k.dataset.kaplama, baslik: k.querySelector('h2').textContent, "
                       "metin: k.querySelector('.bn-kaplama-govde').innerText } : null; })()")


def _mesnet_kaydi(pg, ref):
    return pg.evaluate("(r) => { const A = MatrisAks, b = MatrisBina.bina(), k = A.refAnahtar(b, r);"
                       " return (b.mesnetler || []).find(s => A.refAnahtar(b, s.dugum) === k) || null; }", ref)


def _denetci_metni(pg, hedef):
    """Eleman bilgi denetçisini (MatrisBilgi.denetci, sayfadaki DOM penceresi) güncel çözümle açar; görünen metin."""
    return pg.evaluate("""(h) => { const p = MatrisBilgi.denetci(document.body, Object.assign({}, h, { bina: MatrisBina.bina(), veri: MatrisBina.veri() }));
      return { metin: p.el.innerText, tsv: MatrisBilgi.tsv(MatrisBilgi.bilgi(h, MatrisBina.bina(), MatrisBina.veri())) }; }""", hedef)


# ---------------------------------------------------------------------------------------------------------------------------
def test_k1_k23_kapi_metni_ve_temel_korunur(sayfa):
    """Mütemadi temelli aks–kat şablonu: Böl → onay metni işlem adıyla ("Böl — ") ve temel yan cümlesi olmadan; temel aynen."""
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-3kat-surekli-temel")
    pg.__onaylar.clear()
    pg.evaluate("MatrisBina.seciliAyarla([{ tur: 'kiris', no: 1 }]); MatrisArac.calistir('bol')")
    pg.wait_for_selector(".bn-kaplama[data-kaplama='bol']")
    pg.click(".bn-kaplama[data-kaplama='bol'] [data-tamam]")
    pg.wait_for_function("MatrisBina.bina().surum === 3")
    assert pg.__onaylar, "genel model kapısı sorulmadı"
    m = pg.__onaylar[-1]
    assert m.startswith("Böl — Model genel (surum 3) modele çevrilecek: "), m
    assert "temel" not in m and "tekil" not in m, m
    assert pg.evaluate("MatrisBina.bina().temeller.tip") == "surekli"
    _hatasiz(hatalar, "K-1 kapı")


def test_k10_yayli_mesnet_on_ayari_ve_denetci(sayfa):
    """K-10 (C13). Denetçi adımı motor paketinin yaylı mesnet desteğini gerektirir."""
    pg, hatalar = sayfa
    _sablon(pg, "celik-cbf-3kat")
    ref = {"aks": ["B", "2"], "z": "±0.00"}
    _mesnet_araci(pg, "yay", "±0.00", ref)
    k = _kaplama(pg)
    assert k and k["tur"] == "mesnet-yay" and k["baslik"] == "Yaylı mesnet", k
    alanlar = pg.evaluate("Array.from(document.querySelectorAll('.bn-kaplama .bn-alan')).map(a => [a.querySelector('span').textContent, a.querySelector('input').value])")
    assert alanlar == [["k_x (kN/m)", ""], ["k_y (kN/m)", ""], ["k_z (kN/m)", "10000"], ["k_rx (kN·m/rad)", ""], ["k_ry (kN·m/rad)", ""], ["k_rz (kN·m/rad)", ""]], alanlar
    assert pg.evaluate("document.activeElement && document.activeElement.dataset.a") == "kz", "k_z alanı odakta"
    # pozitif alan yoksa reddedilir, pencere açık kalır
    pg.fill(".bn-kaplama input[data-a='kz']", "0")
    pg.click(".bn-kaplama [data-tamam]")
    _toast_bekle(pg, "en az bir yay rijitliği", 10_000)
    assert _kaplama(pg) is not None
    pg.fill(".bn-kaplama input[data-a='kz']", "10000")
    pg.click(".bn-kaplama [data-tamam]")
    pg.wait_for_function("!document.querySelector('.bn-kaplama')")
    s = _mesnet_kaydi(pg, ref)
    assert s is not None and {a: s[a] for a in s if a != "dugum"} == {"kz": 10000}, s
    assert _coz(pg), _hata_metni(pg)
    v = pg.evaluate("(() => { const m = (MatrisBina.veri().ag.mesnetler || []).find(s => s.tip === 'yay'); return m || null; })()")
    assert v is not None, "motor yaylı mesnedi okumadı (C13)"
    d = _denetci_metni(pg, {"tur": "mesnet", "no": v["dugum"]})
    assert "yaylı mesnet" in d["metin"] and "k_z = 10 000 kN/m" in d["metin"], d["metin"][:1500]
    assert "k_z = 10 000 kN/m" in d["tsv"]
    _hatasiz(hatalar, "K-10 yaylı mesnet")


@pytest.mark.parametrize("secim", ["vazgec", "dusey", "esnek", "aynen"])
def test_k15_rijit_diyafram_sorusu(tarayici, sunucu, secim):
    """K-15 (C14): cbf C2/+3.50'ye ankastre → "Rijit diyaframlı kat" dört seçenek; seçilen model çözülür. "aynen" motor paketinin
    rijit diyafram düğümünde mesnet (ceza yayı) desteğini gerektirir."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu)
    try:
        _sablon(pg, "celik-cbf-3kat")
        ref = {"aks": ["C", "2"], "z": "+3.50"}
        once = pg.evaluate("JSON.stringify(MatrisBina.bina())")
        _mesnet_araci(pg, "ankastre", "+3.50", ref)
        k = _kaplama(pg)
        assert k and k["tur"] == "mesnet-diyafram" and k["baslik"] == "Rijit diyaframlı kat", k
        assert "rijit diyaframlı" in k["metin"] and "Yatay (ux, uy) ve rz mesnedi bu noktada bütün katın yatay hareketini tutar (diyafram bağı)." in k["metin"], k["metin"]
        dugmeler = pg.evaluate("Array.from(document.querySelectorAll('.bn-kaplama [data-diyafram]')).map(b => [b.dataset.diyafram, b.textContent, b.tagName])")
        assert [d[1] for d in dugmeler] == ["Olduğu gibi uygula", "Yalnız düşey mesnet (uz, rx, ry)", "Bu katın diyaframını esnek yap", "Vazgeç"]
        assert all(d[2] == "BUTTON" for d in dugmeler)
        assert pg.evaluate("document.activeElement && document.activeElement.dataset.diyafram") == "dusey", "klavye odağı güvenli seçenekte"
        if secim == "vazgec":
            pg.keyboard.press("Tab"); pg.keyboard.press("Tab")
            assert pg.evaluate("document.activeElement.dataset.diyafram") == "vazgec"
            pg.keyboard.press("Enter")
            pg.wait_for_function("!document.querySelector('.bn-kaplama')")
            assert pg.evaluate("JSON.stringify(MatrisBina.bina())") == once, "Vazgeç modeli değiştirmez"
            _hatasiz(hatalar, "K-15 vazgeç")
            return
        pg.click(f".bn-kaplama [data-diyafram='{secim}']")
        pg.wait_for_function("!document.querySelector('.bn-kaplama')")
        s = _mesnet_kaydi(pg, ref)
        assert s is not None
        if secim == "dusey":
            assert [s[a] for a in ("ux", "uy", "uz", "rx", "ry", "rz")] == [False, False, True, True, True, False]
        else:
            assert all(s[a] for a in ("ux", "uy", "uz", "rx", "ry", "rz"))
        if secim == "esnek":
            assert pg.evaluate("MatrisBina.bina().analiz.diyafram") == {"1": "esnek"}
        assert _coz(pg), _hata_metni(pg)
        assert not _hata_metni(pg).strip(), _hata_metni(pg)
        if secim == "aynen":
            # ux/uy/rz kuvveti ceza yayında (C12 tur 'diyafram-mesnet'): mesnet denetçisi ayrı tabloda gösterir
            n = pg.evaluate("(() => { const m = (MatrisBina.veri().ag.mesnetler || []).find(s => s.kaynak === 'mesnetler'); return m ? m.dugum : null; })()")
            assert n is not None
            d = _denetci_metni(pg, {"tur": "mesnet", "no": n})
            assert "Diyafram bağı kuvvetleri (bina koordinatı)" in d["tsv"], d["tsv"][:2000]
        _hatasiz(hatalar, "K-15 " + secim)
    finally:
        ctx.close()


def test_k15_aks_kat_modelinde_once_diyafram_sorusu_sonra_kapi(tarayici, sunucu):
    """K-15: aks–kat (surum 1, depremli) betonarme-3kat-3x3 C2/+3.20'ye ankastre — soru genelleştirilmiş kopyada sorulur (aks–kat
    döşemeleri panel olur), sonra genel model kapısı; "Yalnız düşey mesnet" modeli genelleştirir, mesnet uz/rx/ry, model çözülür."""
    ctx, pg, hatalar = _sayfa_ac(tarayici, sunucu)
    try:
        _sablon(pg, "betonarme-3kat-3x3")
        assert pg.evaluate("MatrisBina.bina().surum || 1") == 1
        z = pg.evaluate("MatrisBina.bina().akslar.z.map(a => a.ad)")[1]
        ref = {"aks": ["C", "2"], "z": z}
        pg.__onaylar.clear()
        _mesnet_araci(pg, "ankastre", z, ref)
        k = _kaplama(pg)
        assert k and k["tur"] == "mesnet-diyafram", k
        assert not pg.__onaylar, "kapı diyafram sorusundan önce sorulmamalı"
        pg.click(".bn-kaplama [data-diyafram='dusey']")
        pg.wait_for_function("MatrisBina.bina().surum === 3")
        assert pg.__onaylar and pg.__onaylar[-1].startswith("Mesnet — Model genel (surum 3) modele çevrilecek: "), pg.__onaylar
        s = _mesnet_kaydi(pg, ref)
        assert s is not None and [s[a] for a in ("ux", "uy", "uz", "rx", "ry", "rz")] == [False, False, True, True, True, False], s
        assert _coz(pg), _hata_metni(pg)
        _hatasiz(hatalar, "K-15 aks–kat")
    finally:
        ctx.close()


def test_k20_karma_doseme_denetcisi(sayfa):
    """K-20 (C17): karma model (aks–kat + açık mesnet), genel çözüm — döşeme 1 'Panel yükleri (çözüm)'. Motor paketinin panel
    kaynağını gerektirir."""
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    pg.evaluate("""() => { const b = JSON.parse(JSON.stringify(MatrisBina.bina()));
      const z0 = MatrisAks.sistemler(b)[0].l.z.slice().sort((p, q) => p.konum - q.konum)[0].ad;     // en alt Z aksı (tarayıcıda "±0.00")
      b.mesnetler = [{ dugum: { aks: ['B', '2'], z: z0 }, ux: true, uy: true, uz: true }];
      MatrisBina.binaAyarla(b, { etiket: 'test: B2 mesnedi' }); }""")
    assert _coz(pg), _hata_metni(pg)
    assert pg.evaluate("MatrisBina.veri().model") == "genel"
    d = _denetci_metni(pg, {"tur": "doseme", "no": 1})
    assert "Önce çözün" not in d["metin"] and "Panel yükleri (çözüm)" in d["tsv"] and "Taşıyıcı kenarlara paylar" in d["tsv"], d["tsv"][:2000]
    assert "kiriş " in d["tsv"]
    _hatasiz(hatalar, "K-20 döşeme")


def test_k32_k31_kesit_grubu_ve_hepsini_uygula_suresi(sayfa):
    """K-32: kolon 1 önerisinde "Kesit grubuna uygula (12 çubuk)" → tek geri al adımı, yeniden çözüm, "Grubun gerçek D/C maks";
    K-31: Hepsini uygula öncesi süre notu, sonrası "Süre:" (motor paketinin sure_ms'ini gerektirir)."""
    pg, hatalar = sayfa
    _sablon(pg, "betonarme-2kat-3x2")
    assert _coz(pg), _hata_metni(pg)
    once = pg.evaluate("JSON.stringify(MatrisBina.bina())")
    pg.evaluate("MatrisBina.seciliAyarla([{ tur: 'kolon', no: 1 }]); MatrisArac.calistir('kesit-oner')")
    pg.wait_for_selector(".bn-kaplama[data-kaplama='kesit-oner'] [data-oneri-grup]", timeout=180_000)
    d = pg.text_content(".bn-kaplama [data-oneri-grup]")
    uyeler = pg.evaluate("(() => { const b = MatrisBina.bina(), k1 = b.kolonlar.find(k => k.no === 1); return b.kolonlar.filter(k => k.kesit === k1.kesit && String(k.grup || '') === String(k1.grup || '')).map(k => k.no); })()")
    n = len(uyeler)
    assert d == f"Kesit grubuna uygula ({n} çubuk)", d
    pg.evaluate("window.__toast = []")
    pg.click(".bn-kaplama [data-oneri-grup]")
    t = _toast_bekle(pg, "Grubun gerçek D/C maks: ")
    assert t, pg.evaluate("window.__toast")
    b = pg.evaluate("MatrisBina.bina()")
    kesitler = {k["kesit"] for k in b["kolonlar"] if k["no"] in uyeler}
    assert len(kesitler) == 1, kesitler          # grubun bütün üyeleri tek zarf kesitinde
    assert pg.evaluate("JSON.stringify(MatrisBina.bina())") != once
    # tek geri al adımı modeli geri getirir
    pg.evaluate("MatrisArac.calistir('geri-al')")
    pg.wait_for_timeout(300)
    assert pg.evaluate("JSON.stringify(MatrisBina.bina())") == once
    # Hepsini uygula: önce süre notu, sonra "Süre:"
    assert _coz(pg), _hata_metni(pg)
    pg.evaluate("MatrisBina.seciliAyarla([]); MatrisArac.calistir('kesit-oner')")
    pg.wait_for_selector(".bn-kaplama[data-kaplama='kesit-oner'] [data-oneri-hepsi]", timeout=180_000)
    pg.evaluate("window.__toast = []")
    pg.click(".bn-kaplama [data-oneri-hepsi]")
    not_ = pg.text_content(".bn-kaplama .bc-oneri-sure")
    assert "Hesaplanıyor: en çok 4 çözüm, yaklaşık " in not_, not_
    _toast_bekle(pg, "Kesit önerileri uygulandı", 300_000)
    pg.wait_for_function("(window.__toast || []).some(t => /Süre: [0-9]/.test(t))", timeout=120_000)
    _hatasiz(hatalar, "K-32 / K-31")


def test_k22_makas_penceresi_yanal_tutma(sayfa):
    pg, hatalar = sayfa
    _sablon(pg, "celik-sanayi-4hol")
    pg.evaluate("MatrisArac.calistir('makas')")
    pg.wait_for_selector(".bn-kaplama[data-kaplama='makas'] select[data-a='yanal']")
    sec = pg.evaluate("Array.from(document.querySelectorAll(\".bn-kaplama select[data-a='yanal'] option\")).map(o => [o.value, o.textContent, o.selected])")
    assert [s[0] for s in sec] == ["uc-dikme", "yok"] and sec[0][2], sec
    assert "Üst başlığın düzlem dışı burkulma boyu, aşık ya da düzlem dışı bağ yoksa bütün açıklıktır." in pg.text_content(".bn-kaplama")
    pg.evaluate("MatrisBina.kaplamaKapat()")
    _hatasiz(hatalar, "K-22 makas penceresi")
