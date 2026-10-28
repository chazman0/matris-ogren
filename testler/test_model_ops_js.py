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
  const no = ref => M.dugumNo(m, ref);
  // düğüm konumları başvurulardan (aks–kat düğümleri için kayıt yazılmaz; konum akslardan çözülür)
  const gez = ref => { kon[no(ref)] = M.dugumKonumu(m, ref); };
  for (const c of m.cubuklar) { gez(c.i); gez(c.j); }
  for (const p of m.paneller) p.kose.forEach(gez);
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
    return [s["ad"] for s in yapi.bina_sablonlar() if int(yapi.BINA_SABLONLARI[s["ad"]].get("surum", 1)) < 3]   # aks–kat şablonları


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
    # (mütemadi / radye temel elemanları motorun ekidir — temel.py; JS üst yapı modeli bunları taşımaz)
    py = Counter((e["tur"], e["dugumler"][0], e["dugumler"][1]) for e in ag["elemanlar"] if e["tur"] in ("kolon", "kiris"))
    jsc = Counter((c["tur"], c["i"], c["j"]) for c in js["cubuklar"])
    assert jsc == py
    # düğüm konumları
    for dg in ag["dugumler"]:
        if dg.get("efendi") or (dg.get("temel") and dg["key"] is None):     # temel ara düğümleri (50001…) yalnız motorda
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


# Koparak taşıma (ui-akskat-2, ui-s3-3): genelleştirilmiş her aks–kat şablonunda kiriş ve kolonların taşı / döndür / ayna
# (kopyasız) sonucu ya ret (model aynı) ya da sıfır boylu / çakışan çubuk ve bozuk panel içermeyen, öteki elemanları yerinde model.
_TASI_BETIGI = """
const M = require(process.argv[1]);
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const g = M.genellestir(JSON.parse(veri)).model;
  const ENGEL = ["sifir-boy", "cakisan-cubuk", "panel-geometri"];
  const engel = m => M.denetle(m).uyarilar.filter(u => ENGEL.includes(u.kod)).map(u => u.mesaj);
  const once = engel(g);
  const kon = (m, no) => { const c = m.cubuklar.find(x => x.no === no); return [M.dugumKonumu(m, c.i), M.dugumKonumu(m, c.j)]; };
  const sonuc = { once, red: 0, gecerli: 0, hatalar: [] };
  const secilen = [g.cubuklar.find(c => c.tur === "kiris"), g.cubuklar.find(c => c.tur === "kolon")];
  for (const c of secilen) {
    const [P, Q] = kon(g, c.no);
    const ops = [
      ["tasi x", m => M.tasi(m, { cubuklar: [c.no] }, Q[0] - P[0] || 3, 0, 0)],
      ["tasi y", m => M.tasi(m, { cubuklar: [c.no] }, 0, 4, 0)],
      ["tasi z", m => M.tasi(m, { cubuklar: [c.no] }, 0, 0, 3)],
      ["dondur", m => M.dondur(m, { cubuklar: [c.no] }, { nokta: P, yon: [0, 0, 1] }, 90)],
      ["dondur180", m => M.dondur(m, { cubuklar: [c.no] }, { nokta: P, yon: [0, 0, 1] }, 180)],
      ["ayna", m => M.ayna(m, { cubuklar: [c.no] }, { X: P[0] + 2 }, { kopya: false })],
    ];
    for (const [ad, f] of ops) {
      const r = f(g);
      if (r.reddedildi) { sonuc.red++; if (JSON.stringify(r.model) !== JSON.stringify(g)) sonuc.hatalar.push(ad + ": ret modeli değiştirdi"); continue; }
      sonuc.gecerli++;
      const yeni = engel(r.model).filter(e => !once.includes(e));
      if (yeni.length) sonuc.hatalar.push(c.tur + " " + ad + ": " + yeni.join(" "));
      for (const d of g.cubuklar) {
        if (d.no === c.no) continue;
        const a = kon(g, d.no), b = kon(r.model, d.no);
        if (Math.hypot(a[0][0] - b[0][0], a[0][1] - b[0][1], a[0][2] - b[0][2]) + Math.hypot(a[1][0] - b[1][0], a[1][1] - b[1][1], a[1][2] - b[1][2]) > 1e-9) {
          sonuc.hatalar.push(c.tur + " " + ad + ": seçilmeyen çubuk " + d.no + " yer değiştirdi"); break;
        }
      }
      if (ad === "dondur180") {
        const t = r.model.cubuklar.find(x => x.no === c.no);
        if (JSON.stringify(t.i) !== JSON.stringify(c.i)) sonuc.hatalar.push(c.tur + " dondur180: dönme merkezindeki uç değişti");
      }
    }
  }
  process.stdout.write(JSON.stringify(sonuc));
});
"""


@pytest.mark.parametrize("ad", _sablonlar())
def test_koparak_tasima_sablonlarda(ad):
    import yapi
    r = _node("-e", _TASI_BETIGI, str(MODUL), girdi=json.dumps(yapi.bina_sablon(ad)))
    assert r.returncode == 0, r.stderr
    s = json.loads(r.stdout)
    assert s["hatalar"] == [], s["hatalar"]
    assert s["red"] + s["gecerli"] == 12
    assert s["red"] >= 1, "bir aks aralığı ötede kiriş/kolon var: en az bir taşıma reddedilmeli"
