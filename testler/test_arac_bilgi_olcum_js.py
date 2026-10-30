# -*- coding: utf-8 -*-
"""Arayüz modülleri testleri pytest üzerinden: docs/olcum.js (MatrisOlcum), docs/arac_kutusu.js (MatrisArac),
docs/eleman_bilgi.js (MatrisBilgi).

- ``node --check`` ve ``node --test testler/js/<modül>.test.js`` (node'un yerleşik test koşucusu; bağımlılık yok).
- Eleman bilgisi, motorun gerçek çözümüyle (``yapi.bina_coz``) karşılaştırılır: JSON dosyaları burada üretilir ve
  ``MATRIS_BILGI_FIXTURE`` (aks–kat) ile ``MATRIS_BILGI_GENEL`` (genel, surum 3) üzerinden node testine verilir (uzunluk, kesit alanı, iç kuvvet ekstremumları, zarf, D/C, metraj,
  yük yolu, döşeme payı korunumu, temel ve mesnet tepkileri).
- Diller arası yapısal eşitlik: ölçüm geometrisindeki (``MatrisOlcum.geometri``) kolon/kiriş uç koordinatları motorun
  aks–kat ağıyla (``yapi._ag_olustur``) birebir aynı olmalı.
node yoksa testler atlanır.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
DOCS = PROJE / "docs"
JS = PROJE / "testler" / "js"
NODE = shutil.which("node")
MODULLER = ["olcum", "arac_kutusu", "eleman_bilgi"]

pytestmark = pytest.mark.skipif(NODE is None, reason="node kurulu değil")


def _node(*args, girdi=None, zaman=180, env=None):
    return subprocess.run([NODE, *args], input=girdi, capture_output=True, text=True, timeout=zaman, cwd=PROJE,
                          env={**os.environ, **(env or {})})


@pytest.mark.parametrize("modul", MODULLER)
def test_sozdizimi(modul):
    r = _node("--check", str(DOCS / f"{modul}.js"))
    assert r.returncode == 0, r.stderr


@pytest.fixture(scope="module")
def cozumler(tmp_path_factory):
    import yapi
    d = tmp_path_factory.mktemp("bilgi")
    yollar = []
    for ad in ("betonarme-2kat-3x2", "celik-1kat-depo", "betonarme-3kat-3x3"):
        bina = yapi.bina_sablon(ad)
        veri = yapi.bina_coz(bina, anlat=False).veri
        yol = d / f"{ad}.json"
        yol.write_text(json.dumps({"bina": bina, "veri": veri}, ensure_ascii=False), encoding="utf-8")
        yollar.append(str(yol))
    return yollar


@pytest.fixture(scope="module")
def genel_cozum(tmp_path_factory):
    """Genel (surum 3) model çözümü: çapraz çerçeve şablonu + B2 tabanında açık mafsal mesnet (eski motor bu mesneti
    veri.akis.temeller'e B'siz kayıt olarak yazar; eleman bilgisi onu tekil temel saymamalı)."""
    import yapi
    bina = yapi.bina_sablon("celik-cbf-3kat")
    bina["mesnetler"] = [{"dugum": {"aks": ["B", "2"], "z": "±0.00"}, "ux": True, "uy": True, "uz": True}]
    veri = yapi.bina_coz(bina, anlat=False).veri
    assert veri.get("model") == "genel"
    yol = tmp_path_factory.mktemp("bilgi_genel") / "celik-cbf-3kat.json"
    yol.write_text(json.dumps({"bina": bina, "veri": veri}, ensure_ascii=False), encoding="utf-8")
    return str(yol)


@pytest.mark.parametrize("modul", MODULLER)
def test_node_birim_testleri(modul, cozumler, genel_cozum):
    env = {"MATRIS_BILGI_FIXTURE": os.pathsep.join(cozumler), "MATRIS_BILGI_GENEL": genel_cozum} if modul == "eleman_bilgi" else None
    r = _node("--test", str(JS / f"{modul}.test.js"), zaman=300, env=env)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout
    if modul == "eleman_bilgi":
        assert "# skipped 0" in r.stdout, "gerçek çözüm karşılaştırması atlandı"


_BETIK = """
const O = require(process.argv[1]);
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const g = O.geometri(JSON.parse(veri), { aks: null });
  process.stdout.write(JSON.stringify({
    cubuklar: g.cubuklar.map(c => ({ tur: c.tur, no: c.no, A: c.A, B: c.B, i: c.i, j: c.j })),
    dugumler: g.dugumler.filter(n => n.no != null).map(n => ({ no: n.no, P: n.P, etiket: n.etiket })),
    kesisim: O.aksKesisimleri(JSON.parse(veri), { aks: null }).length,
  }));
});
"""


def _sablonlar():
    import yapi
    return [s["ad"] for s in yapi.bina_sablonlar() if int(yapi.BINA_SABLONLARI[s["ad"]].get("surum", 1)) < 3]   # aks–kat şablonları


@pytest.mark.parametrize("ad", _sablonlar())
def test_olcum_geometrisi_motor_agiyla_ayni(ad):
    import yapi
    bina = yapi.bina_sablon(ad)
    r = _node("-e", _BETIK, str(DOCS / "olcum.js"), girdi=json.dumps(bina))
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)
    B = yapi._bina_oku(bina)
    ag, _model = yapi._ag_olustur(B, None)
    kon = {dg["no"]: [dg["X"], dg["Y"], dg["Z"]] for dg in ag["dugumler"]}
    # kolonlar: alt → üst düğüm motorla aynı numara ve konum
    for e in ag["elemanlar"]:
        if e["tur"] != "kolon":
            continue
        c = next(c for c in js["cubuklar"] if c["tur"] == "kolon" and c["no"] == e["kaynak_no"])
        assert (c["i"], c["j"]) == (f"n{e['dugumler'][0]}", f"n{e['dugumler'][1]}")
        assert c["A"] == pytest.approx(kon[e["dugumler"][0]]) and c["B"] == pytest.approx(kon[e["dugumler"][1]])
    # kirişler: motor parçalara böler; JS çubuğu ilk parçanın başından son parçanın sonuna
    for k in B.kirisler:
        parca = sorted((e for e in ag["elemanlar"] if e["tur"] == "kiris" and e["kaynak_no"] == k["no"]), key=lambda e: e["parca"])
        c = next(c for c in js["cubuklar"] if c["tur"] == "kiris" and c["no"] == k["no"])
        assert c["A"] == pytest.approx(kon[parca[0]["dugumler"][0]]) and c["B"] == pytest.approx(kon[parca[-1]["dugumler"][1]])
    # numaralı düğümlerin konumu motorla aynı
    for n in js["dugumler"]:
        if n["no"] in kon:
            assert n["P"] == pytest.approx(kon[n["no"]])
    # aks kesişimleri: X × Y × kat sayısı
    assert js["kesisim"] == len(bina["akslar"]["x"]) * len(bina["akslar"]["y"]) * len(bina["katlar"])
