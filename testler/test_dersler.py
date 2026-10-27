# -*- coding: utf-8 -*-
"""Ders kaynakları (dersler/*.md) için testler.

- Biçim: ders_derle.derle() hatasız geçer; her ders BICIM.md §8.1 alt sınırlarını sağlar.
- Örnekler: her kodlu örnek motorda çalışır, Sonuc döndürür ve 'kontrol' ifadesi doğru çıkar.
- Katalog: BICIM.md §6–§7'deki her etkileşim ve alıştırma, ilgili docs/etkilesim_*.js dosyasında kayıtlıdır.
- Derleyicinin kendisi: geçici klasördeki yapay derslerle (dersler henüz yazılmamışken de anlamlı).

Çalıştırma (proje klasöründen):
  uv run --python 3.13 --with sympy --with numpy --with pytest python -m pytest testler/test_dersler.py -q
"""
from __future__ import annotations

import ast
import importlib
import json
import re
import time
from pathlib import Path

import pytest
import sympy as sp

import ders_derle as dd
import matris_ogren as mo

DOCS = Path(dd.KOK) / "docs"


def _dersler() -> list[dict]:
    try:
        return dd.derle()
    except dd.DersHatasi:
        return []  # biçim hatası test_bicim_hatasiz içinde dosya:satır ayrıntısıyla raporlanır


DERSLER = _dersler()
KODLU_ORNEKLER = [
    pytest.param(d, p, id=f"{d['id']}-ornek{p['no']}")
    for d in DERSLER for p in d["parcalar"] if p["tur"] == "ornek" and p["kod"]
]


def _se_modulu():
    try:
        return importlib.import_module("sonlu_eleman")
    except ImportError:
        return None


def _yapi_modulu():
    try:
        return importlib.import_module("yapi")
    except ImportError:
        return None


def _tasarim_modulu():
    try:
        return importlib.import_module("tasarim")
    except ImportError:
        return None


def calistir(kod: str, ad_alani: dict):
    """Örnek kodunu çalıştırır ve son satırdaki ifadenin değerini döndürür (BICIM.md §5)."""
    agac = ast.parse(kod)
    son = agac.body.pop()
    exec(compile(agac, "<ornek>", "exec"), ad_alani)
    return eval(compile(ast.Expression(son.value), "<ornek>", "eval"), ad_alani)


def _ad_alani(kod: str) -> dict:
    ad_alani = {"mo": mo, "sp": sp}
    se = _se_modulu()
    if se is not None:
        ad_alani["se"] = se
    elif re.search(r"\bse\.", kod):
        pytest.skip("sonlu_eleman.py henüz yok")
    yapi = _yapi_modulu()
    if yapi is not None:
        ad_alani["yapi"] = yapi
    elif re.search(r"\byapi\.", kod):
        pytest.skip("yapi.py henüz yok")
    tasarim = _tasarim_modulu()
    if tasarim is not None:
        ad_alani["tasarim"] = tasarim
    elif re.search(r"\btasarim\.", kod):
        pytest.skip("tasarim.py henüz yok")
    return ad_alani


# ---------------------------------------------------------------- gerçek dersler

def test_bicim_hatasiz():
    dersler = dd.derle()  # hata varsa DersHatasi iletisi dosya:satır ayrıntısıyla görünür
    if not dersler:
        pytest.skip("dersler/ klasöründe henüz ders yok")


@pytest.mark.parametrize("ders", DERSLER, ids=lambda d: d["id"])
def test_pedagoji_alt_sinirlari(ders):
    assert dd.kalite(ders) == []


@pytest.mark.parametrize("ders,ornek", KODLU_ORNEKLER)
def test_ornek_kodu_calisir_ve_kontrolu_gecer(ders, ornek):
    ad_alani = _ad_alani(ornek["kod"])
    bas = time.perf_counter()
    r = calistir(ornek["kod"], ad_alani)
    sure = time.perf_counter() - bas
    ogeler = list(r) if isinstance(r, (list, tuple)) else [r]
    assert ogeler and all(hasattr(x, "anlatim") for x in ogeler), "son ifade Sonuc ya da Sonuc listesi olmalı"
    ad_alani["r"] = r
    assert eval(ornek["kontrol"], ad_alani), f"kontrol tutmadı: {ornek['kontrol']}"
    assert sure < 10, f"örnek {sure:.1f} s sürdü; tarayıcıda 2 s altı hedefleniyor"


@pytest.mark.parametrize("ders", DERSLER, ids=lambda d: d["id"])
def test_md_yedeginde_ozel_soz_dizimi_kalmaz(ders):
    assert not re.search(r"\\(?:kutusil|kutua|kutub|kutuc|ksil|ka|kb|kc)\s*\{", ders["md"])
    assert not re.search(r"^:::", ders["md"], re.M)


KATALOG = [(ad, ad) for ad in dd.ETKILESIMLER] + [(ad, "alistirma:" + ad) for ad in dd.ALISTIRMALAR]


@pytest.mark.parametrize("ad,anahtar", KATALOG, ids=[k for _, k in KATALOG])
def test_katalog_js_de_kayitli(ad, anahtar):
    js = DOCS / dd.etkilesim_dosyasi(ad)
    if not js.exists():
        pytest.skip(f"{js.name} henüz yok")
    metin = js.read_text(encoding="utf-8")
    assert re.search(r"kaydet\(\s*[\"']" + re.escape(anahtar) + r"[\"']", metin), \
        f"{js.name} içinde kaydet(\"{anahtar}\", …) yok"


def test_se_grubu_katalogda():
    katalog = set(dd.ETKILESIMLER) | set(dd.ALISTIRMALAR)
    assert dd.SE_GRUBU <= katalog and dd.YAPI_GRUBU <= katalog
    assert not (dd.SE_GRUBU & dd.YAPI_GRUBU)


# ---------------------------------------------------------------- derleyicinin kendisi (yapay ders)

ON_BILGI = "---\nbaslik: Deneme dersi\nbolum: {bolum}\nozet: Kısa özet.\nsure: 15\n---\n"

TAM_GOVDE = r'''## Neden?

Metin $a+b$ ve blok:

$$
\ka{1} + \kb{2} = \kc{3}
$$

::: tanim Matris
Sayıların dikdörtgen tablosu.
:::

::: etkilesim carpim-gezgini
{"A": "1 2; 3 4", "baslik": "Özel başlık"}
:::

::: alistirma carpim
{"zorluk": 2}
:::

::: ornek Toplama
$A+B$ nedir?
--- ipucu
Eleman eleman topla.
--- cevap
$$
\kutuc{2}
$$
--- kod
B = "1 0; 0 1"
mo.topla("1 2; 3 4", B)
--- kontrol
r.deger == sp.Matrix([[2, 2], [3, 5]])
--- yorum
Sıra önemli değil.
:::

::: sekil Basit şekil
<svg viewBox="0 0 10 10"><path class="ok" pathLength="1" d="M0 0L10 10" stroke="var(--sema-a,#3b82f6)"/></svg>
:::

```text
::: bu bir yönerge değil
```
'''


def _yaz(klasor: Path, govde: str, ad: str = "01-deneme.md", bolum: str = "matris") -> Path:
    yol = klasor / ad
    yol.write_text(ON_BILGI.format(bolum=bolum) + govde, encoding="utf-8")
    return yol


def test_derleyici_butun_parca_turlerini_ayristirir(tmp_path):
    _yaz(tmp_path, TAM_GOVDE)
    (ders,) = dd.derle(tmp_path)
    assert [p["tur"] for p in ders["parcalar"]] == ["md", "kutu", "etkilesim", "alistirma", "ornek", "sekil", "md"]
    kutu, etk, alis, ornek, sekil, son = ders["parcalar"][1:]
    assert (kutu["cesit"], kutu["baslik"]) == ("tanim", "Matris")
    assert etk == {"tur": "etkilesim", "ad": "carpim-gezgini", "baslik": "Özel başlık", "param": {"A": "1 2; 3 4"}}
    assert (alis["baslik"], alis["param"]) == ("Matris çarpımı", {"zorluk": 2})
    assert ornek["no"] == 1 and ornek["soru"] == "$A+B$ nedir?" and ornek["sekil"] == ""
    assert ornek["kod"].splitlines()[-1] == 'mo.topla("1 2; 3 4", B)'
    assert sekil["svg"].startswith("<svg") and sekil["baslik"] == "Basit şekil"
    assert "::: bu bir yönerge değil" in son["icerik"]
    assert r"\textcolor{#2563eb}{1}" in ders["md"] and r"\boxed{2}" in ders["md"]
    assert "Örnek 1.1: Toplama" in ders["md"]


def test_calistirici_yapay_ornekle(tmp_path):
    _yaz(tmp_path, TAM_GOVDE)
    ornek = next(p for p in dd.derle(tmp_path)[0]["parcalar"] if p["tur"] == "ornek")
    ad_alani = _ad_alani(ornek["kod"])
    ad_alani["r"] = calistir(ornek["kod"], ad_alani)
    assert hasattr(ad_alani["r"], "anlatim")
    assert eval(ornek["kontrol"], ad_alani)


def test_json_kontrol_icermez(tmp_path):
    _yaz(tmp_path, TAM_GOVDE)
    hedef = tmp_path / "dersler.json"
    dd.json_yaz(dd.derle(tmp_path), hedef)
    veri = json.loads(hedef.read_text(encoding="utf-8"))
    ornek = next(p for p in veri[0]["parcalar"] if p["tur"] == "ornek")
    assert "kontrol" not in ornek and ornek["kod"]
    assert veri[0]["md"] and veri[0]["bolum_adi"] == "Matris"


def test_kalite_eksikleri_sayar(tmp_path):
    _yaz(tmp_path, TAM_GOVDE)
    eksikler = dd.kalite(dd.derle(tmp_path)[0])
    assert any("ornek 1 < 6" in e for e in eksikler)
    assert any("'::: hata' kutusu yok" in e for e in eksikler)


HATALI = [
    ("ic-ice", "::: not\nA\n::: ipucu\nB\n:::\n:::\n", "iç içe"),
    ("kapanmamis", "::: not\nA\n", "kapanmamış"),
    ("sahipsiz-kapanis", "Metin\n:::\n", "açılmamış"),
    ("bilinmeyen-etkilesim", "::: etkilesim yok-boyle\n:::\n", "bilinmeyen etkilesim"),
    ("bilinmeyen-yonerge", "::: kutucuk\nA\n:::\n", "bilinmeyen yönerge"),
    ("bozuk-json", "::: etkilesim carpim-gezgini\n{A: 1}\n:::\n", "JSON"),
    ("kontrolsuz-kod", '::: ornek X\nSoru?\n--- cevap\n$1$\n--- kod\nmo.iz("1 0; 0 1")\n:::\n', "kontrol"),
    ("cevapsiz", "::: ornek X\nSoru?\n--- ipucu\nİp\n:::\n", "cevap"),
    ("import", '::: ornek X\nSoru?\n--- cevap\n$1$\n--- kod\nimport os\nmo.iz("1")\n--- kontrol\nTrue\n:::\n', "import"),
    ("son-satir-atama", '::: ornek X\nSoru?\n--- cevap\n$1$\n--- kod\nr = mo.iz("1")\n--- kontrol\nTrue\n:::\n',
     "son satırı"),
    ("betikli-svg", '::: sekil\n<svg viewBox="0 0 1 1"><script>alert(1)</script></svg>\n:::\n', "yasak"),
    ("dis-baglanti", '::: sekil\n<svg viewBox="0 0 1 1"><use href="http://x/y.svg#a"/></svg>\n:::\n', "dış bağlantı"),
    ("viewbox-yok", '::: sekil\n<svg><path d="M0 0"/></svg>\n:::\n', "viewBox"),
    ("tek-dolar", "Metin $a+b ve devamı\n", "'$'"),
    ("acik-blok", "$$\na+b\n", "'$$'"),
    ("h1", "# Büyük başlık\n", "'# başlık'"),
]


@pytest.mark.parametrize("govde,beklenen", [pytest.param(g, b, id=i) for i, g, b in HATALI])
def test_derleyici_hatayi_yakalar(tmp_path, govde, beklenen):
    _yaz(tmp_path, govde)
    with pytest.raises(dd.DersHatasi, match=re.escape(beklenen)):
        dd.derle(tmp_path)


@pytest.mark.parametrize("ad,bolum", [("11-deneme.md", "matris"), ("21-deneme.md", "se"), ("05-deneme.md", "yapi")])
def test_numara_bolum_uyumu(tmp_path, ad, bolum):
    _yaz(tmp_path, "Metin\n", ad=ad, bolum=bolum)
    with pytest.raises(dd.DersHatasi, match="uyuşmuyor"):
        dd.derle(tmp_path)


def test_yapi_bolumu_kabul(tmp_path):
    _yaz(tmp_path, "Metin\n", ad="21-deneme.md", bolum="yapi")
    (ders,) = dd.derle(tmp_path)
    assert ders["bolum_adi"] == "Yapı analizi"


def test_ayni_numara_iki_kez(tmp_path):
    _yaz(tmp_path, "Metin\n", ad="01-bir.md")
    _yaz(tmp_path, "Metin\n", ad="01-iki.md")
    with pytest.raises(dd.DersHatasi, match="çakışıyor"):
        dd.derle(tmp_path)


def test_bicim_ve_alt_cizgili_dosyalar_atlanir(tmp_path):
    (tmp_path / "BICIM.md").write_text("# serbest", encoding="utf-8")
    (tmp_path / "_taslak.md").write_text("# serbest", encoding="utf-8")
    assert dd.derle(tmp_path) == []
