# -*- coding: utf-8 -*-
"""docs/ifc_disari.js (MatrisIFC, IFC4 STEP dışa aktarım; tasarım belgesi §14.2) testleri pytest üzerinden.

- ``node --check`` ve ``node --test testler/js/ifc_disari.test.js`` (yerleşik test koşucusu).
- Bina şablonlarından (``yapi.bina_sablon``) Node ile IFC üretilir: çözümsüz ve ``yapi.bina_coz`` verisiyle (yük grupları,
  birleşimler, D/C). Ayrıca ``testler/js/ifc_ornekler.js`` örnekleri (surum 3, §13 temeller, §19 aks sistemleri).
- Her dosyada STEP sözdizimi (her varlık satırı ``#n=IFC...(...);``) ve bütün ``#n`` başvurularının tanımlı olması denetlenir.
- ``ifcopenshell`` kuruluysa: dosya açılır; kat/eleman sayıları, kat kotları, profil türleri, malzeme ve kat içerme ilişkileri,
  aks ızgaraları; ``ifcopenshell.validate`` (EXPRESS kuralları dahil) hatasız; ``ifcopenshell.geom`` ile eleman sınır kutuları
  (kolon kat arası, kiriş üstü kat kotunda, döşeme üstü kat kotunda, temel üstü temel kotunda).
node yoksa testler atlanır; ifcopenshell yoksa yalnız onu gerektirenler atlanır.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest

PROJE = Path(__file__).resolve().parent.parent
MODUL = PROJE / "docs" / "ifc_disari.js"
ORNEKLER = PROJE / "testler" / "js" / "ifc_ornekler.js"
JS_TEST = PROJE / "testler" / "js" / "ifc_disari.test.js"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node kurulu değil")

ZAMAN = "2026-01-01T00:00:00"
TOL = 1e-3


def _node(*args, girdi=None, zaman=120):
    return subprocess.run([NODE, *args], input=girdi, capture_output=True, text=True, timeout=zaman, cwd=PROJE)


# stdin: {"bina" | "ornek", "veri", "secenek"} → stdout: {"metin", "uyarilar", "sayac", "bina"}
_BETIK = """
const M = require(process.argv[1]);
const O = require(process.argv[2]);
let girdi = "";
process.stdin.on("data", d => girdi += d);
process.stdin.on("end", () => {
  const g = JSON.parse(girdi);
  const bina = g.ornek ? O[g.ornek]() : g.bina;
  const r = M.uretAyrintili(bina, g.veri || null, g.secenek || {});
  process.stdout.write(JSON.stringify({metin: r.metin, uyarilar: r.uyarilar, sayac: r.sayac, bina: bina}));
});
"""


def _uret(bina=None, veri=None, secenek=None, ornek=None):
    girdi = {"bina": bina, "veri": veri, "secenek": dict({"zaman": ZAMAN}, **(secenek or {})), "ornek": ornek}
    r = _node("-e", _BETIK, str(MODUL), str(ORNEKLER), girdi=json.dumps(girdi, ensure_ascii=False))
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout)


def _sablonlar():
    import yapi
    return [s["ad"] for s in yapi.bina_sablonlar() if int(yapi.BINA_SABLONLARI[s["ad"]].get("surum", 1)) < 3]   # aks–kat şablonları


@lru_cache(maxsize=None)
def _sablon_ifc(ad, veri_ile):
    import yapi
    bina = yapi.bina_sablon(ad)
    veri = yapi.bina_coz(bina, anlat=False).veri if veri_ile else None
    if veri is not None:
        veri = json.loads(json.dumps(veri))     # köprüdeki gibi JSON'dan geçmiş veri
    return bina, veri, _uret(bina, veri)


@lru_cache(maxsize=None)
def _ornek_ifc(ad):
    return _uret(ornek=ad)


ORNEK_ADLARI = ["temel", "serbest", "radye", "surekli", "aks", "genel"]


def _temel_beklenen(bina, veri):
    """Temel tipine göre beklenen fiziksel temel elemanları (§3 tekil, §13 mütemadi / radye; temel.py kurallarıyla).

    Dönüş: {tip, pad, strip, beam, baseslab, ag (veri.temel ağı var mı)}. Mütemadide hat sayısı: veri.temel.hatlar ya da
    seçili aks çizgilerinden zemin kat kolonu olanlar; kirişli radyede her aks çizgisinde bir temel kirişi."""
    t = bina["temeller"]
    tip = t.get("tip", "tekil")
    vt = (veri or {}).get("temel") or {}
    ag = tip in ("surekli", "radye") and bool(vt.get("dugumler"))
    kat1 = {tuple(c["aks"]) for c in bina["kolonlar"] if c.get("kat", 1) == 1}
    b = {"tip": tip, "pad": 0, "strip": 0, "beam": 0, "baseslab": 0, "ag": ag, "dc": 0}
    if ag:      # D/C taşıyan fiziksel temeller: tasarım kaydı olan hatlar; radye plağında en büyük D/C
        tas = [x for x in vt.get("tasarim", []) if x.get("dc") is not None]
        hat = {str(x.get("hat")) for x in tas if x.get("tur") == "temel-kirisi"}
        b["dc"] = sum(1 for h in vt["hatlar"] if str(h["ad"]) in hat and (tip == "surekli" or h.get("kirisli")))
        b["dc"] += 1 if tip == "radye" and tas else 0
    if tip == "tekil":
        b["pad"] = len(kat1)
    elif tip == "surekli":
        s = t["surekli"]
        if ag:
            b["strip"] = len(vt["hatlar"])
        else:
            liste = None if s.get("akslar", "tum") == "tum" else [str(a) for a in s["akslar"]]
            for yon, akslar, i in (("x", bina["akslar"]["y"], 1), ("y", bina["akslar"]["x"], 0)):
                if yon in s.get("yon", "xy"):
                    b["strip"] += sum(1 for a in akslar if (liste is None or a["ad"] in liste) and any(k[i] == a["ad"] for k in kat1))
    else:
        b["baseslab"] = 1
        kir = (vt.get("model") or {}).get("kiris") if ag else t["radye"].get("kiris")
        if kir:
            b["beam"] = sum(1 for h in vt["hatlar"] if h.get("kirisli")) if ag else len(bina["akslar"]["x"]) + len(bina["akslar"]["y"])
    return b


# ---------------------------------------------------------------------------
# STEP sözdizimi (ifcopenshell gerekmez)
# ---------------------------------------------------------------------------
_SATIR = re.compile(r"^#(\d+)=([A-Z0-9]+)\((.*)\);$")
_METIN = re.compile(r"'(?:[^']|'')*'")


def _step_denetle(metin):
    satirlar = [s for s in metin.split("\n") if s]
    assert satirlar[:2] == ["ISO-10303-21;", "HEADER;"]
    assert "FILE_SCHEMA(('IFC4'));" in satirlar
    veri = satirlar.index("DATA;")
    assert satirlar[veri - 1] == "ENDSEC;"
    assert satirlar[-2:] == ["ENDSEC;", "END-ISO-10303-21;"]
    tanimli, refler, tipler = set(), [], Counter()
    for s in satirlar[veri + 1:-2]:
        m = _SATIR.match(s)
        assert m, f"varlık satırı biçimi: {s[:120]}"
        assert m.group(1) not in tanimli, f"tekrarlı varlık #{m.group(1)}"
        assert all(0x20 <= ord(c) <= 0x7E for c in s), f"ASCII dışı karakter: {s[:120]}"
        tanimli.add(m.group(1))
        tipler[m.group(2)] += 1
        govde = _METIN.sub("''", m.group(3))
        derinlik = 0
        for c in govde:
            derinlik += (c == "(") - (c == ")")
            assert derinlik >= 0, s[:120]
        assert derinlik == 0, s[:120]
        refler += re.findall(r"#(\d+)", govde)
    eksik = sorted({r for r in refler if r not in tanimli}, key=int)
    assert not eksik, f"tanımsız başvurular: {eksik[:20]}"
    return tipler


def test_sozdizimi():
    r = _node("--check", str(MODUL))
    assert r.returncode == 0, r.stderr


def test_node_birim_testleri():
    r = _node("--test", str(JS_TEST), zaman=300)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout


@pytest.mark.parametrize("veri_ile", [False, True], ids=["cozumsuz", "veri"])
@pytest.mark.parametrize("ad", _sablonlar())
def test_sablon_step_ve_sayilar(ad, veri_ile):
    bina, veri, r = _sablon_ifc(ad, veri_ile)
    tip = _step_denetle(r["metin"])
    assert r["uyarilar"] == []
    assert tip == Counter(r["sayac"])
    nx, ny = len(bina["akslar"]["x"]), len(bina["akslar"]["y"])
    assert tip["IFCBUILDINGSTOREY"] == len(bina["katlar"])
    assert tip["IFCCOLUMN"] == len(bina["kolonlar"])
    assert tip["IFCBEAM"] == len(bina["kirisler"])
    tb = _temel_beklenen(bina, veri)
    assert tip["IFCSLAB"] == len(bina["dosemeler"]) + tb["baseslab"]
    assert tip["IFCFOOTING"] == tb["pad"] + tb["strip"] + tb["beam"]
    assert len(re.findall(r"IFCFOOTING\([^\n]*\.PAD_FOOTING\.\);", r["metin"])) == tb["pad"]
    assert len(re.findall(r"IFCFOOTING\([^\n]*\.STRIP_FOOTING\.\);", r["metin"])) == tb["strip"]
    assert len(re.findall(r"IFCFOOTING\([^\n]*\.FOOTING_BEAM\.\);", r["metin"])) == tb["beam"]
    assert len(re.findall(r"IFCSLAB\([^\n]*\.BASESLAB\.\);", r["metin"])) == tb["baseslab"]
    assert tip["IFCGRID"] == len(bina["katlar"])              # her Z (kat) seviyesinde aks ızgarası
    assert tip["IFCGRIDAXIS"] == len(bina["katlar"]) * (nx + ny)
    assert tip["IFCSTRUCTURALANALYSISMODEL"] == 1
    assert tip["IFCAPPLICATION"] == 1
    if veri is None:
        assert tip["IFCSTRUCTURALCURVEMEMBER"] == len(bina["kolonlar"]) + len(bina["kirisler"])
        assert tip["IFCSTRUCTURALPOINTCONNECTION"] == nx * ny * len(bina["katlar"])
        assert tip["IFCSTRUCTURALLOADCASE"] >= 2
    else:
        ag = veri["ag"]
        efendi = {d["no"] for d in ag["dugumler"] if d.get("efendi")}
        assert tip["IFCSTRUCTURALCURVEMEMBER"] == sum(1 for e in ag["elemanlar"] if not set(e["dugumler"]) & efendi)
        assert tip["IFCSTRUCTURALPOINTCONNECTION"] == len(ag["dugumler"]) - len(efendi)
        uyg = [k for k in veri["kombinasyonlar"] if k["uygulandi"] and k["tur"] != "drift"]
        durumlar = set(veri["durumlar"]) | {"G", "Q"} | {d for k in uyg for d in k["katsayilar"]}
        assert tip["IFCSTRUCTURALLOADCASE"] == len(durumlar)
        assert tip["IFCSTRUCTURALLOADGROUP"] == len(uyg)
        assert tip["IFCRELASSIGNSTOGROUPBYFACTOR"] == sum(len(k["katsayilar"]) for k in uyg)
        assert tip["IFCSTRUCTURALLINEARACTION"] + tip["IFCSTRUCTURALCURVEACTION"] > 0
        dc = [e for e in veri.get("tasarim", {}).get("elemanlar", []) if e.get("dc") is not None]
        # bina elemanları + temel hattı / radye D/C'si (veri.temel.tasarim)
        assert len(re.findall(r"IFCPROPERTYSINGLEVALUE\('DC',\$,IFCRATIOMEASURE\(", r["metin"])) == len(dc) + tb["dc"]
        if tb["ag"]:
            # temel ağı: temel kirişi / radye şeridi analitik üyeleri ve her temel düğümünde Winkler yayı
            vt = veri["temel"]
            assert tip["IFCSTRUCTURALCURVEMEMBER"] >= len(vt["elemanlar"])
            assert len(re.findall(r"IFCBOUNDARYNODECONDITION\('Zemin yay", r["metin"])) >= 1
            assert "IFCMODULUSOFSUBGRADEREACTIONMEASURE(" in r["metin"]
    profil = "IFCISHAPEPROFILEDEF" if bina["sistem"] == "celik" else "IFCRECTANGLEPROFILEDEF"
    assert tip[profil] >= 1


@pytest.mark.parametrize("ad", ORNEK_ADLARI)
def test_ornek_step(ad):
    r = _ornek_ifc(ad)
    tip = _step_denetle(r["metin"])
    assert r["uyarilar"] == []
    assert tip == Counter(r["sayac"])


def test_belirlenimci():
    a = _uret(ornek="aks")["metin"]
    b = _uret(ornek="aks")["metin"]
    assert a == b


def test_program_adi_yalniz_matris_ogren():
    metin = _ornek_ifc("temel")["metin"]
    ad = "Matris \\X2\\00D6011F\\X0\\ren"
    uyg = [s for s in metin.split("\n") if "=IFCAPPLICATION(" in s]
    assert len(uyg) == 1 and uyg[0].endswith(f",'{ad}','{ad}');")
    satir = next(s for s in metin.split("\n") if s.startswith("FILE_NAME("))
    assert satir.endswith(f",'{ad}','');")


# ---------------------------------------------------------------------------
# ifcopenshell ile: açma, sayılar, ilişkiler, doğrulama, geometri
# ---------------------------------------------------------------------------
def _ifc():
    return pytest.importorskip("ifcopenshell")


def _ac(metin, tmp_path, ad="model"):
    ifcopenshell = _ifc()
    yol = tmp_path / f"{ad}.ifc"
    yol.write_text(metin, encoding="ascii")
    return ifcopenshell.open(str(yol))


# EXPRESS kuralları (WHERE/global kurallar) denetimi dosya başına ~2,5 s sabit maliyetli (kural modülü her çağrıda derlenir);
# şema denetimi (tür, sayı, zorunlu alan, ters ilişki) her dosyada, kural denetimi bütün varlık türlerini kapsayan temsilci
# dosyalarda yapılır.
KURALLI_SABLON = {("betonarme-3kat-3x3", True), ("celik-1kat-depo", True), ("betonarme-3kat-surekli-temel", True),
                  ("betonarme-4kat-radye", True)}
KURALLI_ORNEK = {"serbest", "radye", "aks"}


def _dogrula(f, kurallar=False):
    _ifc()
    import ifcopenshell.validate
    kayit = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(f, kayit, express_rules=kurallar)
    return [f"{s.get('message')} | {s.get('instance')}"[:400] for s in kayit.statements]


@lru_cache(maxsize=None)
def _ayarlar():
    import ifcopenshell.geom
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    return s


def _kutu(e):
    import ifcopenshell.geom
    import numpy as np
    sekil = ifcopenshell.geom.create_shape(_ayarlar(), e)
    v = np.array(sekil.geometry.verts, dtype=float).reshape(-1, 3)
    return v.min(axis=0), v.max(axis=0)


def _kat(e):
    rel = e.ContainedInStructure
    return rel[0].RelatingStructure if rel else None


def _profil(e):
    for rel in e.HasAssociations:
        if rel.is_a("IfcRelAssociatesMaterial"):
            m = rel.RelatingMaterial
            if m.is_a("IfcMaterialProfileSetUsage"):
                return m.ForProfileSet.MaterialProfiles[0].Profile
    return None


def _pset(e, ad):
    for rel in e.IsDefinedBy:
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.Name == ad:
            return {p.Name: p.NominalValue.wrappedValue for p in rel.RelatingPropertyDefinition.HasProperties}
    return None


@pytest.mark.parametrize("veri_ile", [False, True], ids=["cozumsuz", "veri"])
@pytest.mark.parametrize("ad", _sablonlar())
def test_sablon_ifcopenshell(ad, veri_ile, tmp_path):
    _ifc()
    bina, veri, r = _sablon_ifc(ad, veri_ile)
    f = _ac(r["metin"], tmp_path, ad)
    assert f.schema == "IFC4"
    assert _dogrula(f, (ad, veri_ile) in KURALLI_SABLON) == []
    assert len(f.by_type("IfcProject")) == 1
    katlar = sorted(f.by_type("IfcBuildingStorey"), key=lambda k: k.Elevation)
    assert [round(k.Elevation, 6) for k in katlar] == [round(k["kot"], 6) for k in bina["katlar"]]
    assert [k.Name for k in katlar] == [k["ad"] for k in bina["katlar"]]
    assert len(f.by_type("IfcColumn")) == len(bina["kolonlar"])
    assert len(f.by_type("IfcBeam")) == len(bina["kirisler"])
    tb = _temel_beklenen(bina, veri)
    assert len(f.by_type("IfcSlab")) == len(bina["dosemeler"]) + tb["baseslab"]
    assert Counter(e.PredefinedType for e in f.by_type("IfcFooting")) == Counter(
        {k: v for k, v in (("PAD_FOOTING", tb["pad"]), ("STRIP_FOOTING", tb["strip"]), ("FOOTING_BEAM", tb["beam"])) if v})
    # her fiziksel eleman bir kata bağlı, katı geometrisi ve malzemesi var
    for e in f.by_type("IfcBuildingElement"):
        assert _kat(e) is not None, e
        assert e.Representation.Representations[0].Items[0].is_a("IfcExtrudedAreaSolid")
        assert any(rel.is_a("IfcRelAssociatesMaterial") for rel in e.HasAssociations), e
    # profiller: betonarmede dikdörtgen, çelikte I (tablodaki ad ve ölçüler)
    kesitler = bina["kesitler"]
    for e in f.by_type("IfcColumn") + f.by_type("IfcBeam"):
        p = _profil(e)
        k = kesitler[e.ObjectType]
        if k["tip"] == "profil":
            assert p.is_a("IfcIShapeProfileDef") and p.ProfileName == k["profil"]
        else:
            assert p.is_a("IfcRectangleProfileDef")
            assert (p.XDim, p.YDim) == pytest.approx((k["b"], k["h"]))
    # aks ızgaraları: U = X aksları, V = Y aksları
    izgaralar = f.by_type("IfcGrid")
    assert len(izgaralar) == len(bina["katlar"])
    for g in izgaralar:
        assert [a.AxisTag for a in g.UAxes] == [a["ad"] for a in bina["akslar"]["x"]]
        assert [a.AxisTag for a in g.VAxes] == [a["ad"] for a in bina["akslar"]["y"]]
    # yapısal analiz modeli
    model = f.by_type("IfcStructuralAnalysisModel")
    assert len(model) == 1
    uyeler = [o for rel in model[0].IsGroupedBy for o in rel.RelatedObjects]
    assert sum(1 for o in uyeler if o.is_a("IfcStructuralCurveMember")) == len(f.by_type("IfcStructuralCurveMember"))
    mesnetli = [n for n in f.by_type("IfcStructuralPointConnection") if n.AppliedCondition]
    if tb["ag"]:
        # temel.py ağı: her temel düğümünde Winkler yayı k_z = k0·A (A: etki alanı); kolon tabanı sabit mesnet değil
        vt = veri["temel"]
        md = vt["model"]
        assert len(mesnetli) == len(vt["dugumler"])
        alan = {d["no"]: d["A"] for d in vt["dugumler"]}
        ag_ad = {d["adres"]: d["no"] for d in veri["ag"]["dugumler"]}
        for n in mesnetli:
            k = n.AppliedCondition
            kz = k.TranslationalStiffnessZ
            assert kz.is_a("IfcLinearStiffnessMeasure")
            assert kz.wrappedValue == pytest.approx(md["k0"] * alan[ag_ad[n.Name]], rel=1e-9)
            if md.get("yatay", "tutulu") == "tutulu":
                assert k.TranslationalStiffnessX.wrappedValue is True and k.RotationalStiffnessZ.wrappedValue is True
        # temel kirişi / radye şeridi analitik üyeleri: veri.temel.elemanlar kadar, temel kotunda, profil ve malzemesiyle
        temel_uye = [u for u in f.by_type("IfcStructuralCurveMember") if re.match(r"(TK|RŞ)-", u.Name)]
        assert len(temel_uye) == len(vt["elemanlar"])
        for u in temel_uye[:20]:
            assert _profil(u) is not None
        # fiziksel temel ↔ analitik üyeler
        fiz = {rel.RelatingProduct for rel in f.by_type("IfcRelAssignsToProduct")}
        assert all(e in fiz for e in f.by_type("IfcFooting")) and (tb["tip"] != "radye" or
                                                                   any(s_.PredefinedType == "BASESLAB" for s_ in fiz if s_.is_a("IfcSlab")))
        ps = _pset(f.by_type("IfcFooting")[0] if tb["tip"] == "surekli" else
                   next(s_ for s_ in f.by_type("IfcSlab") if s_.PredefinedType == "BASESLAB"), "Pset_MatrisOgren")
        assert ps["k0"] == pytest.approx(md["k0"]) and ps["DC_zemin"] == pytest.approx(vt["DC_zemin"])
    else:
        assert len(mesnetli) == len(bina["akslar"]["x"]) * len(bina["akslar"]["y"])
    if veri is not None:
        dc = {(e["tur"], e["no"]): e["dc"] for e in veri.get("tasarim", {}).get("elemanlar", []) if e.get("dc") is not None}
        bulunan = 0
        for e in f.by_type("IfcColumn") + f.by_type("IfcBeam"):
            ps = _pset(e, "Pset_MatrisOgren")
            anahtar = (ps["Tur"], ps["No"])
            if anahtar in dc:
                assert ps["DC"] == pytest.approx(dc[anahtar])
                bulunan += 1
        assert bulunan == len(dc)
        birlesimler = [g for g in f.by_type("IfcStructuralLoadGroup") if g.PredefinedType == "LOAD_COMBINATION"]
        for g in birlesimler:
            assert all(rel.is_a("IfcRelAssignsToGroupByFactor") for rel in g.IsGroupedBy)


@pytest.mark.parametrize("ad", _sablonlar())
def test_sablon_geometri(ad, tmp_path):
    _ifc()
    pytest.importorskip("numpy")
    bina, _veri, r = _sablon_ifc(ad, False)
    f = _ac(r["metin"], tmp_path, ad)
    kot = {k["no"]: k["kot"] for k in bina["katlar"]}
    ax = {a["ad"]: a["konum"] for a in bina["akslar"]["x"]}
    ay = {a["ad"]: a["konum"] for a in bina["akslar"]["y"]}
    kolonlar = {c["no"]: c for c in bina["kolonlar"]}
    for e in f.by_type("IfcColumn"):
        c = kolonlar[int(e.Tag[1:])]
        mn, mx = _kutu(e)
        assert (mn[2], mx[2]) == pytest.approx((kot[c["kat"] - 1], kot[c["kat"]]), abs=TOL)
        merkez = (mn + mx) / 2
        assert (merkez[0], merkez[1]) == pytest.approx((ax[c["aks"][0]], ay[c["aks"][1]]), abs=TOL)
    kirisler = {k["no"]: k for k in bina["kirisler"]}
    for e in f.by_type("IfcBeam"):
        k = kirisler[int(e.Tag[1:])]
        mn, mx = _kutu(e)
        h = _profil(e)
        h = h.OverallDepth if h.is_a("IfcIShapeProfileDef") else h.YDim
        assert (mn[2], mx[2]) == pytest.approx((kot[k["kat"]] - h, kot[k["kat"]]), abs=TOL)   # üstü kat kotunda
        xs = sorted([ax[k["bas"][0]], ax[k["son"][0]]])
        ys = sorted([ay[k["bas"][1]], ay[k["son"][1]]])
        if xs[0] != xs[1]:
            assert (mn[0], mx[0]) == pytest.approx(tuple(xs), abs=TOL)
        else:
            assert (mn[1], mx[1]) == pytest.approx(tuple(ys), abs=TOL)
    dosemeler = {d["no"]: d for d in bina["dosemeler"]}
    for e in f.by_type("IfcSlab"):
        if e.PredefinedType == "BASESLAB":
            continue
        d = dosemeler[int(e.Tag[1:])]
        mn, mx = _kutu(e)
        assert (mn[2], mx[2]) == pytest.approx((kot[d["kat"]] - d["h"], kot[d["kat"]]), abs=TOL)
        assert (mn[0], mx[0]) == pytest.approx(tuple(sorted(ax[q[0]] for q in d["kose"])), abs=TOL)
    tem = bina["temeller"]
    tb = _temel_beklenen(bina, None)
    xs, ys = sorted(ax.values()), sorted(ay.values())
    for e in f.by_type("IfcFooting"):
        mn, mx = _kutu(e)
        assert mx[2] == pytest.approx(kot[0], abs=TOL)                 # üstü temel kotunda
        if e.PredefinedType == "PAD_FOOTING":
            assert mx[2] - mn[2] == pytest.approx(tem["varsayilan"]["h"], abs=TOL)
        elif e.PredefinedType == "STRIP_FOOTING":
            s_ = tem["surekli"]
            assert mx[2] - mn[2] == pytest.approx(s_["h_govde"], abs=TOL)          # toplam yükseklik (tabla dahil)
            en = min(mx[0] - mn[0], mx[1] - mn[1])
            boy = max(mx[0] - mn[0], mx[1] - mn[1])
            assert en == pytest.approx(s_["B"], abs=TOL)                            # tabla genişliği
            tas = s_.get("tasma", 0.5)
            assert boy in (pytest.approx(xs[-1] - xs[0] + 2 * tas, abs=TOL), pytest.approx(ys[-1] - ys[0] + 2 * tas, abs=TOL))
        else:
            assert mx[2] - mn[2] == pytest.approx(tem["radye"]["kiris"]["h"], abs=TOL)
    if tb["tip"] == "radye":
        r_ = tem["radye"]
        taban = [e for e in f.by_type("IfcSlab") if e.PredefinedType == "BASESLAB"]
        assert len(taban) == 1
        mn, mx = _kutu(taban[0])
        assert (mn[2], mx[2]) == pytest.approx((kot[0] - r_["h"], kot[0]), abs=TOL)
        tas = r_.get("tasma", 1.0)
        assert (mn[0], mx[0], mn[1], mx[1]) == pytest.approx((xs[0] - tas, xs[-1] + tas, ys[0] - tas, ys[-1] + tas), abs=TOL)


@pytest.mark.parametrize("ad", ORNEK_ADLARI)
def test_ornek_ifcopenshell(ad, tmp_path):
    _ifc()
    r = _ornek_ifc(ad)
    f = _ac(r["metin"], tmp_path, ad)
    assert _dogrula(f, ad in KURALLI_ORNEK) == []
    for e in f.by_type("IfcBuildingElement"):
        assert _kat(e) is not None, e


def test_ornek_profil_turleri(tmp_path):
    _ifc()
    f = _ac(_ornek_ifc("serbest")["metin"], tmp_path, "serbest")
    turler = Counter(p.is_a() for p in f.by_type("IfcProfileDef"))
    for t in ("IfcRectangleProfileDef", "IfcIShapeProfileDef", "IfcRectangleHollowProfileDef", "IfcCircleHollowProfileDef",
              "IfcLShapeProfileDef", "IfcUShapeProfileDef", "IfcArbitraryClosedProfileDef"):
        assert turler[t] >= 1, t
    assert {m.PredefinedType for m in f.by_type("IfcMember")} >= {"CHORD", "PURLIN", "BRACE", "POST"}
    assert {c.PredefinedType for c in f.by_type("IfcCovering")} == {"ROOFING", "CLADDING"}
    assert {s.PredefinedType for s in f.by_type("IfcFooting")} == {"STRIP_FOOTING"}
    r = _ac(_ornek_ifc("radye")["metin"], tmp_path, "radye")
    assert {s.PredefinedType for s in r.by_type("IfcSlab")} >= {"BASESLAB"}
    assert {s.PredefinedType for s in r.by_type("IfcFooting")} == {"FOOTING_BEAM"}


def test_ornek_aks_sistemi_geometri(tmp_path):
    """§19: döndürülmüş kartezyen (KANAT-B, 30°) ve silindirik (KUBBE) sistem kolonları doğru yerde; kat kotu Z aksından."""
    _ifc()
    np = pytest.importorskip("numpy")
    r = _ornek_ifc("aks")
    f = _ac(r["metin"], tmp_path, "aks")
    katlar = sorted(f.by_type("IfcBuildingStorey"), key=lambda k: k.Elevation)
    assert [k.Elevation for k in katlar] == pytest.approx([0.0, 6.0])
    izg = f.by_type("IfcGrid")
    assert len(izg) == 8
    assert {g.PredefinedType for g in izg} == {"RECTANGULAR", "RADIAL"}
    kubbe = [g for g in izg if "KUBBE" in g.Name]
    assert len(kubbe) == 2 and all(a.AxisCurve.is_a("IfcCircle") for g in kubbe for a in g.UAxes)
    merkezler = []
    for e in f.by_type("IfcColumn"):
        mn, mx = _kutu(e)
        merkezler.append(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2], mx[2]))
    c, s = np.cos(np.radians(30)), np.sin(np.radians(30))
    beklenen = [(25.0, 0.0, 0.0, 6.0), (25 + 6 * c, 6 * s, 0.0, 6.0), (25 + 6 * c - 5 * s, 6 * s + 5 * c, 0.0, 6.0), (25 - 5 * s, 5 * c, 0.0, 6.0)]
    beklenen += [(5 + 3 * np.cos(np.radians(t)), 18 + 3 * np.sin(np.radians(t)), 0.0, 2.5) for t in (0, 120, 240)]
    for b in beklenen:
        assert any(np.allclose(m, b, atol=TOL) for m in merkezler), b
    # mahya kirişi (eğik): üst noktası mahya Z aksının üstünde değil; aşıklar mertek ortasında
    for e in f.by_type("IfcMember"):
        if e.PredefinedType == "PURLIN":
            mn, mx = _kutu(e)
            assert (mn[0] + mx[0]) / 2 == pytest.approx(2.5, abs=TOL)
            assert (mn[2] + mx[2]) / 2 == pytest.approx(6.75, abs=TOL)
    # Z aksları özellik kümesi
    ps = _pset(f.by_type("IfcBuilding")[0], "Pset_MatrisOgren_ZAkslari")
    assert ps == pytest.approx({"±0.00": 0.0, "Saçak": 6.0, "Mahya": 7.5})


def test_profil_tablosu_yapi_veri_ile_ayni():
    """JS'teki IPE/HEA/HEB ölçüleri (h, b, tw, tf, r; mm) yapi_veri.PROFILLER ile birebir aynı."""
    import yapi_veri as yv
    r = _node("-e", "process.stdout.write(JSON.stringify(require(process.argv[1]).PROFILLER))", str(MODUL))
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)
    assert set(js) == set(yv.PROFILLER)
    for ad, p in yv.PROFILLER.items():
        assert js[ad] == pytest.approx([p["h"], p["b"], p["tw"], p["tf"], p["r"]]), ad
