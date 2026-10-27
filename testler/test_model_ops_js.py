# -*- coding: utf-8 -*-
"""docs/model_ops.js (saf JS model işlemleri) testleri pytest üzerinden.

- ``node --check`` ve ``node --test testler/js/model_ops.test.js`` (node'un yerleşik test koşucusu; bağımlılık yok).
- Diller arası yapısal eşitlik: her bina şablonu için JS ``genellestir`` sonucundaki çubuk uç düğümleri ve konumları,
  motorun aks–kat ağıyla (``yapi._ag_olustur``) birebir aynı olmalı (düğüm no = 1000·kat + 20·ix + iy + 1).
node yoksa testler atlanır.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
MODUL = PROJE / "docs" / "model_ops.js"
JS_TEST = PROJE / "testler" / "js" / "model_ops.test.js"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node kurulu değil")


def _node(*args, girdi=None, zaman=120):
    return subprocess.run([NODE, *args], input=girdi, capture_output=True, text=True, timeout=zaman, cwd=PROJE)


def test_sozdizimi():
    r = _node("--check", str(MODUL))
    assert r.returncode == 0, r.stderr


def test_node_birim_testleri():
    r = _node("--test", str(JS_TEST), zaman=300)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout


_BETIK = """
const M = require(process.argv[1]);
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const r = M.genellestir(JSON.parse(veri));
  const m = r.model;
  const kon = {};
  for (const d of m.dugumler) kon[d.no] = [d.X, d.Y, d.Z];
  const no = ref => M.dugumNo(m, ref);
  const out = {
    cubuklar: m.cubuklar.map(c => ({tur: c.tur, i: no(c.i), j: no(c.j), kesit: c.kesit, aci: c.aci, kaynak: c.kaynak})),
    paneller: m.paneller.map(p => ({no: p.no, kose: p.kose.map(no), dagitim: p.dagitim})),
    dugumler: kon, denetle: M.denetle(m).uyarilar, uyarilar: r.uyarilar,
  };
  process.stdout.write(JSON.stringify(out));
});
"""


def _sablonlar():
    import yapi
    return [s["ad"] for s in yapi.bina_sablonlar()]


@pytest.mark.parametrize("ad", _sablonlar())
def test_genellestir_motor_agiyla_ayni(ad):
    import yapi
    bina = yapi.bina_sablon(ad)
    r = _node("-e", _BETIK, str(MODUL), girdi=json.dumps(bina))
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)
    B = yapi._bina_oku(bina)
    ag, _model = yapi._ag_olustur(B, None)
    # eleman uç düğümleri (yön dahil: kolon alt→üst, kiriş küçük akstan büyüğe)
    py = Counter((e["tur"], e["dugumler"][0], e["dugumler"][1]) for e in ag["elemanlar"])
    jsc = Counter((c["tur"], c["i"], c["j"]) for c in js["cubuklar"])
    assert jsc == py
    # düğüm konumları
    for dg in ag["dugumler"]:
        if dg.get("efendi"):
            continue
        assert js["dugumler"][str(dg["no"])] == pytest.approx([dg["X"], dg["Y"], dg["Z"]])
    # kolon yönü ↔ aci; kesit ve kaynak eşlemesi
    kolon = {c["no"]: c for c in B.kolonlar}
    for c in js["cubuklar"]:
        if c["tur"] == "kolon":
            assert c["aci"] == (90 if kolon[c["kaynak"]["no"]]["yon"] == "y" else 0)
            assert c["kesit"] == kolon[c["kaynak"]["no"]]["kesit"]
    # döşeme → panel (dört köşe, aynı sayıda), kat/aks köşeleri motorun düğümleri
    assert len(js["paneller"]) == len(B.dosemeler)
    tum = {dg["no"] for dg in ag["dugumler"]}
    for p in js["paneller"]:
        assert len(p["kose"]) == 4 and set(p["kose"]) <= tum
        assert p["dagitim"] in ("iki", "tek-13", "tek-24")
    assert js["denetle"] == []
