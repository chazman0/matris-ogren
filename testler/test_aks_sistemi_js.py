# -*- coding: utf-8 -*-
"""docs/aks_sistemi.js (aks sistemi, tasarım belgesi §19) testleri pytest üzerinden.

- ``node --check`` ve ``node --test testler/js/aks_sistemi.test.js`` (node'un yerleşik test koşucusu; bağımlılık yok).
- Diller arası: her bina şablonu ``yukselt`` ile aks sistemine (akslar.z) yükseltilince, kat Z akslarındaki aks REF'lerinin
  koordinatları motorun aks–kat ağıyla (``yapi._ag_olustur``) birebir aynı olmalı; ``model_ops.genellestir`` yükseltilmiş
  modelde de aynı uç düğümlerini vermeli.
- Kablolama: index.html'de model_ops.js'ten sonra, cizim3b.js'ten önce yüklenir; servis çalışanı kabuğunda ve stil
  dosyasında yer alır.
node yoksa node gerektiren testler atlanır.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
MODUL = PROJE / "docs" / "aks_sistemi.js"
JS_TEST = PROJE / "testler" / "js" / "aks_sistemi.test.js"
NODE = shutil.which("node")

node_gerekli = pytest.mark.skipif(NODE is None, reason="node kurulu değil")


def _node(*args, girdi=None, zaman=120):
    return subprocess.run([NODE, *args], input=girdi, capture_output=True, text=True, timeout=zaman, cwd=PROJE)


@node_gerekli
def test_sozdizimi():
    r = _node("--check", str(MODUL))
    assert r.returncode == 0, r.stderr


@node_gerekli
def test_node_birim_testleri():
    r = _node("--test", str(JS_TEST), zaman=300)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout


_BETIK = """
const path = require("path");
const A = require(process.argv[1]);
const M = require(path.join(path.dirname(process.argv[1]), "model_ops.js"));
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const bina = JSON.parse(veri);
  const y = A.yukselt(bina);
  const m = y.model;
  const kon = [];
  for (const z of m.akslar.z) for (const x of m.akslar.x) for (const yy of m.akslar.y)
    kon.push({kat: z.kat, aks: [x.ad, yy.ad], P: A.refKoordinat(m, {aks: [x.ad, yy.ad], z: z.ad})});
  const g0 = M.genellestir(bina).model, g1 = M.genellestir(m).model;
  const uc = g => g.cubuklar.map(c => [c.tur, M.dugumNo(g, c.i), M.dugumNo(g, c.j)]);
  process.stdout.write(JSON.stringify({z: m.akslar.z, katlar: m.katlar, surum: m.surum, kon,
    uc0: uc(g0), uc1: uc(g1), ref1: g1.cubuklar.slice(0, 3).map(c => [c.i, c.j]),
    kolonlar: m.kolonlar, kolonlar0: bina.kolonlar}));
});
"""


def _sablonlar():
    import yapi
    return [s["ad"] for s in yapi.bina_sablonlar()]


@node_gerekli
@pytest.mark.parametrize("ad", _sablonlar())
def test_yukseltilmis_aks_refleri_motor_agiyla_ayni(ad):
    import yapi
    bina = yapi.bina_sablon(ad)
    r = _node("-e", _BETIK, str(MODUL), girdi=json.dumps(bina))
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)
    assert js["surum"] == 3
    # Z aksları katlardan: her kat bir Z aksı, kot ve sıra aynı
    assert [(z["kat"], z["konum"]) for z in js["z"]] == [(k["no"], pytest.approx(k["kot"])) for k in bina["katlar"]]
    assert js["katlar"] == bina["katlar"]
    assert js["kolonlar"] == js["kolonlar0"]
    # kat Z aksındaki aks REF'i = motorun aks–kat düğümü
    B = yapi._bina_oku(bina)
    ag, _model = yapi._ag_olustur(B, None)
    motor = {(dg["kat"], tuple(dg["aks"])): (dg["X"], dg["Y"], dg["Z"]) for dg in ag["dugumler"] if dg.get("aks") and not dg.get("efendi")}
    js_kon = {(k["kat"], tuple(k["aks"])): k["P"] for k in js["kon"]}
    assert motor, "motor ağında aks düğümü yok"
    for anahtar, P in motor.items():
        assert js_kon[anahtar] == pytest.approx(list(P)), anahtar
    # genelleştirme yükseltilmiş modelde aynı düğümleri verir; REF'ler Z aksı adıyla yazılır
    assert js["uc1"] == js["uc0"]
    for i, j in js["ref1"]:
        for ref in (i, j):
            assert "z" in ref and "kat" not in ref, ref


def test_index_ve_servis_calisani_kablolamasi():
    html = (PROJE / "docs" / "index.html").read_text(encoding="utf-8")
    sira = [m.group(1) for m in re.finditer(r'<script src="([^"]+)"', html)]
    assert "aks_sistemi.js" in sira
    assert sira.index("model_ops.js") < sira.index("aks_sistemi.js") < sira.index("cizim3b.js") < sira.index("bina.js")
    sw = (PROJE / "docs" / "sw.js").read_text(encoding="utf-8")
    assert '"./aks_sistemi.js"' in sw
    css = (PROJE / "docs" / "style.css").read_text(encoding="utf-8")
    for sinif in (".aks-katman", ".aks-balon", ".aks-cizgi", ".aks-olcu-c", ".aks-sihirbaz", ".aks-tablo", ".aks-onay", ".aks-sayisal"):
        assert sinif in css, sinif


def test_modul_dom_disi_yuklenir_ve_api_tam():
    """Saf mantık node'da DOM'suz yüklenir; bina.js'in kullanacağı API adları dışa açık."""
    if NODE is None:
        pytest.skip("node kurulu değil")
    betik = ("const A = require(process.argv[1]); process.stdout.write(JSON.stringify(Object.keys(A).filter(k => typeof A[k] === 'function').sort()));")
    r = _node("-e", betik, str(MODUL))
    assert r.returncode == 0, r.stderr
    adlar = set(json.loads(r.stdout))
    gerekli = {"sozdizimiAyristir", "sozdizimiYaz", "adlarUret", "hizliAks", "katlarTuret", "yukselt", "katlariSenkronla",
               "refKoordinat", "koordinattanRef", "kesisimler", "aksParcalari", "gozler", "enYakinKesisim", "enYakinParca", "gozBul",
               "gorunumKomsu", "aksTasi", "aralikDegistir", "aksEkle", "aksSil", "aksYenidenAdlandir", "yenidenHarfle", "aksCogalt",
               "aksOzellik", "aksSirala", "bagliElemanlar", "sistemEkle", "sistemGuncelle", "sistemSil",
               "sahneKatmani", "kenarPaylari", "uygunIzdusum", "surukleKonum", "balonSurukle", "aksHedefi", "kesisimHedefi",
               "sihirbaz", "duzenleyici"}
    assert gerekli <= adlar, gerekli - adlar
