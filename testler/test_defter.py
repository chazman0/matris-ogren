# -*- coding: utf-8 -*-
"""Colab defteri (Matris_Ogren.ipynb) gömülü modüllerle eşleşik mi?

Defter ``defter_yap.py`` ile üretilir ve kurulum hücresine programın 10 modülünü (matris_ogren, sonlu_eleman, yapi_veri, yapi,
yapi_serbest, temel, tasarim, rapor, tablolar, alan) ``{ad: (_SHA256, _PAKET)}`` sözlüğü olarak zlib + base64 ile gömer. Bir modül
değişip defter yeniden üretilmezse Colab'daki öğrenci eski modülü çalıştırır; bu test bunu yakalar. Düzeltme:
``python3 defter_yap.py`` (sympy ve numpy yeter; nbformat gerekmez). Ayrıca: modül kümesi tam bu 10 modül, iki üretim bayt bayt aynı, defter nbformat
şemasına uygun (kuruluysa) ve "Bina modeli" bölümü şablon listesini üretim anındaki ``yapi.bina_sablonlar()`` ile taşır.
"""
from __future__ import annotations

import ast
import base64
import hashlib
import importlib.util
import json
import re
import zlib
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
DEFTER = KOK / "Matris_Ogren.ipynb"
YENIDEN = "python3 defter_yap.py ile defteri yeniden üretin."
MODULLER = ("matris_ogren", "sonlu_eleman", "yapi_veri", "yapi", "yapi_serbest", "temel", "tasarim", "rapor", "tablolar", "alan")


def _defter() -> dict:
    if not DEFTER.exists():
        pytest.skip("Matris_Ogren.ipynb yok")
    return json.loads(DEFTER.read_text(encoding="utf-8"))


def _kaynak(h) -> str:
    k = h.get("source", "")
    return "".join(k) if isinstance(k, list) else k


def _kurulum_hucresi() -> str:
    for h in _defter().get("cells", []):
        metin = _kaynak(h)
        if h.get("cell_type") == "code" and "_MODULLER = {" in metin:
            return metin
    pytest.fail("Defterde kurulum hücresi (_MODULLER sözlüğü) bulunamadı. " + YENIDEN)


def _gomulu() -> dict:
    """Kurulum hücresindeki _MODULLER sözlüğü → {ad: (sha, paket metni)} (hücre çalıştırılmadan, ast ile okunur)."""
    hucre = _kurulum_hucresi()
    for dugum in ast.parse(hucre).body:
        if isinstance(dugum, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_MODULLER" for t in dugum.targets):
            return ast.literal_eval(dugum.value)
    pytest.fail("_MODULLER ataması okunamadı. " + YENIDEN)


def _defter_yap():
    spec = importlib.util.spec_from_file_location("defter_yap_test", KOK / "defter_yap.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_modul_kumesi_tam_on_modul():
    gomulu = _gomulu()
    assert tuple(gomulu) == MODULLER, f"gömülü modüller {list(gomulu)}; beklenen {list(MODULLER)}. " + YENIDEN
    assert _defter_yap().MODULLER == MODULLER


@pytest.mark.parametrize("ad", MODULLER)
def test_gomulu_modul_dosyayla_ayni(ad):
    """Her gömülü modül: bildirilen özet dosyanın SHA-256'sı, paket açılınca dosyanın baytları."""
    sha, paket = _gomulu()[ad]
    dosya = (KOK / f"{ad}.py").read_bytes()
    gercek = hashlib.sha256(dosya).hexdigest()
    assert sha == gercek, f"Defterdeki {ad}.py eski (özet {sha[:12]}…, dosya {gercek[:12]}…). " + YENIDEN
    assert zlib.decompress(base64.b64decode(paket)) == dosya, f"gömülü {ad}.py paketi dosyayla aynı değil. " + YENIDEN


def test_surum_etiketi_matris_modulunden():
    surum = re.search(r'^__version__\s*=\s*"([^"]+)"', (KOK / "matris_ogren.py").read_text(encoding="utf-8"), re.M).group(1)
    assert f'_SURUM = "{surum}"' in _kurulum_hucresi(), YENIDEN


def test_kurulum_klasoru_ve_yol():
    """Modüller Colab'da /content/matris_modulleri'ye (başka yerde geçici klasöre) yazılır, klasör sys.path başına eklenir ve ikinci
    çalıştırmada modüller gömülü kopyadan yeniden yüklenir."""
    h = _kurulum_hucresi()
    assert 'Path("/content/matris_modulleri") if _colab else Path(tempfile.gettempdir()) / "matris_modulleri"' in h
    assert "sys.path.insert(0, str(_klasor))" in h and "sys.modules.pop(_ad, None)" in h
    assert "hashlib.sha256(_kaynak).hexdigest() != _sha" in h          # bozuk paket öğretici hatayla durur
    compile(h, "kurulum", "exec")


def test_iki_uretim_bayt_bayt_ayni_ve_dosyayla_ayni():
    """Defter yeniden üretilince aynı baytlar çıkar (sıra numaralı hücre kimlikleri, nbformat JSON biçimi) ve depodaki defter
    güncel modüllerden üretilmiş olanla aynıdır."""
    dy = _defter_yap()
    a, b = dy.defter_metni(dy.defter_olustur()), dy.defter_metni(dy.defter_olustur())
    assert a == b
    assert DEFTER.read_text(encoding="utf-8") == a, "Depodaki defter güncel üretimle aynı değil. " + YENIDEN
    nb = json.loads(a)
    assert [h["id"] for h in nb["cells"]] == [f"hucre-{i:02d}" for i in range(len(nb["cells"]))]
    assert nb["nbformat"] == 4 and nb["nbformat_minor"] == 5


def test_nbformat_ile_ayni_metin_ve_sema():
    nbformat = pytest.importorskip("nbformat")
    import io
    dy = _defter_yap()
    nb = dy.defter_olustur()
    dugum = nbformat.from_dict(nb)
    nbformat.validate(dugum)
    s = io.StringIO()
    nbformat.write(dugum, s)
    assert s.getvalue() == dy.defter_metni(nb)


def test_bina_modeli_bolumu():
    """'Bina modeli' bölümü: şablon açılır listesi yapi.bina_sablonlar() ile aynı; çöz → özet (ΣG, en büyük D/C, belirleyen);
    rapor iframe srcdoc ile; kesit önerisi yinele = 0. Form hücreleri derlenir."""
    import yapi
    hucre = _defter()["cells"]
    kodlar = [_kaynak(h) for h in hucre if h["cell_type"] == "code"]
    coz = next(k for k in kodlar if "11.1) Bina şablonunu çöz" in k)
    m = re.search(r'^sablon = "([^"]+)" #@param (\[.*\])$', coz, re.M)
    assert m and json.loads(m.group(2)) == [s["ad"] for s in yapi.bina_sablonlar()] and m.group(1) in json.loads(m.group(2))
    assert "yapi.bina_coz(bina" in coz and "Σ G (sabit yük)" in coz and "En büyük D/C" in coz and "Belirleyen" in coz
    rap = next(k for k in kodlar if "11.2) Statik hesap raporu" in k)
    assert "rapor.statik_rapor(bina, veri)" in rap and "<iframe srcdoc=" in rap and "_html.escape(belge, quote=True)" in rap
    oner = next(k for k in kodlar if "11.3) Kesit önerisi" in k)
    assert "yapi_serbest.kesit_oner(bina, ic=cozum.ic, hedef=\"hepsi\", yinele=0)" in oner
    for k in (coz, rap, oner):
        compile(k, "form", "exec")
    md = "".join(_kaynak(h) for h in hucre if h["cell_type"] == "markdown")
    assert "## 11) Bina modeli" in md and "## 12) Serbest çalışma alanı" in md


def test_bina_hucreleri_calisir(tmp_path, monkeypatch):
    """Bina formlarının gövdeleri (IPython olmadan, display yerine toplayıcı) gerçek modüllerle çalışır: özet, rapor dosyası ve
    öneri tablosu üretilir."""
    hucre = _defter()["cells"]
    kodlar = [_kaynak(h) for h in hucre if h["cell_type"] == "code"]
    gosterilen = []

    class _Gosterim(str):
        pass
    import sys
    import types
    disp = types.ModuleType("IPython.display")
    disp.Markdown = disp.Math = disp.HTML = _Gosterim
    disp.display = gosterilen.append
    paket = types.ModuleType("IPython")
    paket.display = disp
    monkeypatch.setitem(sys.modules, "IPython", paket)
    monkeypatch.setitem(sys.modules, "IPython.display", disp)
    monkeypatch.chdir(tmp_path)
    ns = {}
    for baslik, ek in (("11.1) Bina şablonunu çöz", {"betonarme-2kat-3x2": "betonarme-tek-aciklik"}), ("11.2) Statik hesap raporu", {}),
                       ("11.3) Kesit önerisi", {})):
        k = next(x for x in kodlar if baslik in x)
        for a, b in ek.items():
            k = k.replace(f'sablon = "{a}"', f'sablon = "{b}"')
        exec(compile(k, baslik, "exec"), ns)      # noqa: S102 — defter hücresi
    metin = "\n".join(str(x) for x in gosterilen)
    assert "❌" not in metin, metin[:2000]
    assert "| Σ G (sabit yük) | 208.35 kN |" in metin and "En büyük D/C" in metin and "Belirleyen" in metin
    assert (tmp_path / "statik_rapor.html").read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    assert "<iframe srcdoc=" in metin and "| Çubuk | Tür | Kesit | Öneri |" in metin and "(kiriş " in metin


def test_paket_satirlari_bekci_desenine_takilmaz():
    """Base64 rastgele harf dizisidir: bir paket satırı yanlışlıkla yasak ürün adı desenine (test_program_adi_yok) uymasın diye
    satır sonu eşleşmenin ortasına kaydırılır; birleştirilen satırlar paketin kendisidir."""
    dy = _defter_yap()
    assert dy._YASAK is not None and dy._ISTISNA is not None          # desen bekçi testinden okunur
    yasakli = "Ex" + "cel"
    paket = "A" * 70 + yasakli + "B" * 10 + "/c" + "si+" + "C" * 90
    satirlar = dy._bol(paket)
    assert "".join(satirlar) == paket and all(len(s) <= 76 for s in satirlar)
    assert not [s for s in satirlar if dy._satir_temiz(s)]
    assert dy._satir_temiz("xx" + yasakli + "yy") is not None
