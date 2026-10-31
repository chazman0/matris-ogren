# -*- coding: utf-8 -*-
"""docs/ifc_disari.js (MatrisIFC, IFC4 STEP dışa aktarım; tasarım belgesi §14.2) testleri pytest üzerinden.

- ``node --check`` ve ``node --test testler/js/ifc_disari.test.js`` (yerleşik test koşucusu).
- Bina şablonlarından (``yapi.bina_sablon``; aks–kat ve surum 3 genel model) Node ile IFC üretilir: çözümsüz ve ``yapi.bina_coz``
  verisiyle (yük grupları, birleşimler, yükler, D/C). Ayrıca ``testler/js/ifc_ornekler.js`` örnekleri (surum 3, §13 temeller,
  §19 aks sistemleri, motorun kesit dili).
- Genel model: motorun basit kesit adları (``MatrisIFC.basitProfil``; A, Iy, Iz, J ``tasarim.kesit_ozellik`` ile aynı), vute
  (``IfcExtrudedAreaSolidTapered`` + ``Pset_MatrisVute``), kesit uyarılarının tekilliği; G, Q, S yükleri STEP'ten bağımsız olarak
  toplanıp çözümün ``yukler.toplam`` ve çubuk toplamlarıyla karşılaştırılır.
- Örnekler motorla çözülür (K-11); rüzgâr/deprem/kren eylemleri (K-37, C16 ``veri.yukler.eylemler``: W = rüzgâr toplamı, EX/EY =
  V_tE, K = tekerlek yükleri, EZ = G_carpani × G; rijit diyafram merkezi ve bağları) ve mütemadi/radye temel öz ağırlığı (K-39, C11
  ``veri.temel.oz_yuk``: IFC G toplamı = ``veri.yukler.toplam.G``). Bu çıktıları üretmeyen motorda ilgili testler atlanır
  (``_motor_c16``, ``_motor_c11``, ``_motor_genel_temel``) ve IFC'nin "eski çözüm" notlarına izin verilir (``_uyarisiz``).
- Her dosyada STEP sözdizimi (her varlık satırı ``#n=IFC...(...);``) ve bütün ``#n`` başvurularının tanımlı olması denetlenir.
- ``ifcopenshell`` kuruluysa: dosya açılır; kat/eleman sayıları, kat kotları, profil türleri, malzeme ve kat içerme ilişkileri,
  aks ızgaraları; ``ifcopenshell.validate`` (EXPRESS kuralları dahil) hatasız; ``ifcopenshell.geom`` ile eleman sınır kutuları
  (kolon kat arası, kiriş üstü kat kotunda, döşeme üstü kat kotunda, temel üstü temel kotunda).
node yoksa testler atlanır; ifcopenshell yoksa yalnız onu gerektirenler atlanır.
"""
from __future__ import annotations

import json
import math
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
    return [s["ad"] for s in yapi.bina_sablonlar()]


def _genel_mi(ad):
    import yapi
    return int(yapi.BINA_SABLONLARI[ad].get("surum", 1)) >= 3       # surum 3 genel model (dugumler/cubuklar/paneller)


def _aks_kat_sablonlari():
    return [ad for ad in _sablonlar() if not _genel_mi(ad)]


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


ORNEK_ADLARI = ["temel", "serbest", "radye", "surekli", "aks", "genel", "genel_kesit"]


# Motor paketinin (paralel geliştirme) çıktıları: C16 veri.yukler.eylemler, C11 veri.temel.oz_yuk ve genel modelde mütemadi/radye.
# Bunları gerektiren testler motor yokken atlanır (birleştirmeden sonra koşar); motor varken "eski çözüm" notuna izin verilmez.
def _motor_c16():
    import yapi
    return hasattr(yapi, "EYLEMLER_NOTU")


def _motor_c11():
    import temel
    return hasattr(temel, "oz_yuk")


def _motor_genel_temel():
    import yapi_serbest
    return hasattr(yapi_serbest, "_temel_gorunum")


EYLEM_NOTU = "IFC yükleri: rüzgâr, deprem ve kren etkileri yük durumu/birleşim olarak vardır, eylem olarak yazılmadı ("
TEMEL_OZ_NOTU = "IFC yükleri: çözümde temel öz ağırlığı yükleri yok (veri.temel.oz_yuk; eski çözüm): "


def _uyarisiz(r, veri):
    """IFC uyarısız. Yalnız bu kurulumun motorunda olmayan çıktılar için (C16 eylemler, C11 oz_yuk) eski çözüm notları kalabilir."""
    kalan = list(r["uyarilar"])
    if veri is not None:
        if "eylemler" not in (veri.get("yukler") or {}) and not _motor_c16():
            kalan = [u for u in kalan if not u.startswith(EYLEM_NOTU)]
        if not (veri.get("temel") or {}).get("oz_yuk") and not _motor_c11():
            kalan = [u for u in kalan if not u.startswith(TEMEL_OZ_NOTU)]
    assert kalan == []


def _diyafram_beklenen(veri):
    """Eylem taşıyan rijit diyafram efendi düğümleri → (ayrı merkez bağlantısı sayısı, rijit bağ üyesi sayısı, ortak merkezli efendi
    sayısı). Efendi bir kat düğümüyle çakışıyorsa (1 mm) ayrı bağlantı yazılmaz: merkez o kat düğümüdür, bağlar ondan öteki kat
    düğümlerine."""
    ag = veri["ag"]
    dug = {d["no"]: d for d in ag["dugumler"]}
    eyl = (veri.get("yukler") or {}).get("eylemler") or {}
    efendi = {n["dugum"] for e in eyl.values() for n in e.get("dugumler", []) if dug.get(n["dugum"], {}).get("efendi")}
    merkez = bag = ortak = 0
    for d in ag.get("diyaframlar", []):
        if d["ana"] in efendi:
            m = dug[d["ana"]]
            uz = [math.dist((dug[n]["X"], dug[n]["Y"], dug[n]["Z"]), (m["X"], m["Y"], m["Z"])) for n in d["dugumler"]]
            if any(x < 1e-3 for x in uz):
                ortak += 1
                bag += len(uz) - 1
            else:
                merkez += 1
                bag += len(uz)
    return merkez, bag, ortak


@lru_cache(maxsize=None)
def _ornek_json(ad):
    r = _node("-e", "process.stdout.write(JSON.stringify(require(process.argv[1])[process.argv[2]]()))", str(ORNEKLER), ad)
    assert r.returncode == 0, r.stderr
    return r.stdout


def _ornek_bina(ad):
    """Örnek model (her çağrıda yeni kopya: testler modeli değiştirebilir)."""
    return json.loads(_ornek_json(ad))


def _genel_beklenen(bina):
    """Genel model (surum 3): fiziksel eleman sayıları. Tekil temel: en alt Z aksındaki kolon çubuğu tabanı başına bir."""
    en_alt = min(bina["akslar"]["z"], key=lambda z: z["konum"])["ad"]
    tabanlar = {tuple(r["aks"]) for c in bina["cubuklar"] if c["tur"] == "kolon" for r in (c["i"], c["j"])
                if isinstance(r, dict) and r.get("z") == en_alt and "aks" in r and not r.get("sistem")}
    return {"cubuk": len(bina["cubuklar"]), "panel": len(bina["paneller"]),
            "temel": len(tabanlar) if bina["temeller"].get("tip", "tekil") == "tekil" else None}


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


# STEP varlıkları ayrıştırılmış alanlarla: #n → (TİP, [alan]); alan: ("R", n) başvuru, ("S", metin), ("E", enum), ("T", tip, değer),
# float, None ($ / *), liste. Yük denetimleri bununla ifcopenshell olmadan yapılır.
_BELIRTEC = re.compile(r"#\d+|\$|\*|\.[A-Z0-9_]+\.|[-+0-9.Ee]+")


def _alanlar(govde):
    def deger(i):
        c = govde[i]
        if c == "'":
            j, m = i + 1, ""
            while True:
                if govde[j] == "'" and govde[j + 1:j + 2] == "'":
                    m, j = m + "'", j + 2
                elif govde[j] == "'":
                    return ("S", m), j + 1
                else:
                    m, j = m + govde[j], j + 1
        if c == "(":
            liste, j = [], i + 1
            if govde[j] == ")":
                return liste, j + 1
            while True:
                v, j = deger(j)
                liste.append(v)
                if govde[j] == ")":
                    return liste, j + 1
                j += 1
        m = re.match(r"[A-Z0-9_]+\(", govde[i:])
        if m:
            v, j = deger(i + len(m.group(0)) - 1)
            return ("T", m.group(0)[:-1], v[0] if v else None), j
        t = _BELIRTEC.match(govde, i).group(0)
        if t.startswith("#"):
            v = ("R", int(t[1:]))
        elif t in ("$", "*"):
            v = None
        elif t.startswith("."):
            v = ("E", t.strip("."))
        else:
            v = float(t)
        return v, i + len(t)
    return deger(0)[0]


def _varliklar(metin):
    V = {}
    for s in metin.split("\n"):
        m = _SATIR.match(s)
        if m:
            V[int(m.group(1))] = (m.group(2), _alanlar("(" + m.group(3) + ")"))
    return V


def _r(x):
    return x[1] if isinstance(x, tuple) and x[0] == "R" else None


def _uye_uclari(V, uye):
    """IfcStructuralCurveMember → (başlangıç, bitiş) noktaları (Reference/Edge topolojisinden)."""
    sek = V[_r(V[uye][1][6])]
    kenar = V[_r(V[_r(sek[1][2][0])][1][3][0])]
    nokta = lambda tepe: V[_r(V[_r(tepe)][1][0])][1][0]
    return nokta(kenar[1][0]), nokta(kenar[1][1])


def _yuk_toplamlari(metin):
    """Her yük durumunun eylemlerinin düşey bileşkesi (kN, aşağı +) ve eylem başına (durum, üye, kN) listesi.
    IfcStructuralLinearAction: değer × üye boyu; IfcStructuralCurveAction (POLYGONAL): yamuk integrali; IfcStructuralPointAction: FZ.
    Konumlar artan ve üye boyu içinde olmalı; her eylem bir yük durumuna atanmış ve bir yapı öğesine bağlı olmalı."""
    V = _varliklar(metin)
    uye = {_r(a[5]): _r(a[4]) for t, a in V.values() if t == "IFCRELCONNECTSSTRUCTURALACTIVITY"}
    durum = {}
    for t, a in V.values():
        if t == "IFCRELASSIGNSTOGROUP" and V[_r(a[6])][0] == "IFCSTRUCTURALLOADCASE":
            for o in a[4]:
                assert _r(o) not in durum, f"eylem #{_r(o)} iki yük durumunda"
                durum[_r(o)] = V[_r(a[6])][1][2][1]
    toplam, eylemler = Counter(), []
    for n, (t, a) in V.items():
        if t not in ("IFCSTRUCTURALLINEARACTION", "IFCSTRUCTURALCURVEACTION", "IFCSTRUCTURALPOINTACTION"):
            continue
        assert n in durum, f"#{n} yük durumuna atanmamış"
        assert n in uye, f"#{n} yapı öğesine bağlı değil"
        yk = V[_r(a[7])][1]
        if t == "IFCSTRUCTURALPOINTACTION":
            v = -(yk[3] or 0.0)
        else:
            L = math.dist(*_uye_uclari(V, uye[n]))
            if t == "IFCSTRUCTURALLINEARACTION":
                v = -(yk[3] or 0.0) * L
            else:
                f = [-(V[_r(r)][1][3] or 0.0) for r in yk[1]]
                x = [p[0] for p in yk[2]]
                assert all(b > a_ for a_, b in zip(x, x[1:])), f"#{n} konumlar artan değil: {x}"
                assert x[0] >= -1e-9 and x[-1] <= L + 1e-6, f"#{n} konum üye dışında: {x[0]}..{x[-1]} (L = {L})"
                v = sum((x[i + 1] - x[i]) * (f[i] + f[i + 1]) / 2 for i in range(len(x) - 1))
        toplam[durum[n]] += v
        eylemler.append((durum[n], uye[n], v, t))
    return toplam, eylemler, V


def _yuk_vektorleri(metin):
    """Her yük durumunun eylem bileşkesi, bina (global) eksenlerinde: {durum: [FX, FY, FZ, MX, MY, MZ]} (kN, kN·m; moment yalnız
    nokta eylemlerinin kendi momentleri — konum momenti eklenmez). Yayılı eylemler × üye boyu / yamuk integrali (_yuk_toplamlari gibi)."""
    V = _varliklar(metin)
    uye = {_r(a[5]): _r(a[4]) for t, a in V.values() if t == "IFCRELCONNECTSSTRUCTURALACTIVITY"}
    durum = {}
    for t, a in V.values():
        if t == "IFCRELASSIGNSTOGROUP" and V[_r(a[6])][0] == "IFCSTRUCTURALLOADCASE":
            for o in a[4]:
                durum[_r(o)] = V[_r(a[6])][1][2][1]
    toplam = {}
    for n, (t, a) in V.items():
        if t not in ("IFCSTRUCTURALLINEARACTION", "IFCSTRUCTURALCURVEACTION", "IFCSTRUCTURALPOINTACTION"):
            continue
        yk = V[_r(a[7])][1]
        v = [0.0] * 6
        if t == "IFCSTRUCTURALPOINTACTION":
            v = [yk[i] or 0.0 for i in range(1, 7)]
        elif t == "IFCSTRUCTURALLINEARACTION":
            L = math.dist(*_uye_uclari(V, uye[n]))
            v[:3] = [(yk[i] or 0.0) * L for i in (1, 2, 3)]
        else:
            x = [p[0] for p in yk[2]]
            f = [[V[_r(r)][1][i] or 0.0 for r in yk[1]] for i in (1, 2, 3)]
            v[:3] = [sum((x[i + 1] - x[i]) * (fi[i] + fi[i + 1]) / 2 for i in range(len(x) - 1)) for fi in f]
        top = toplam.setdefault(durum[n], [0.0] * 6)
        for i in range(6):
            top[i] += v[i]
    return toplam


def _eylem_toplami(e):
    """veri.yukler.eylemler[durum] kaydının bileşkesi [FX, FY, FZ, MX, MY, MZ] (bina eksenleri; q·vek, P·vek, F)."""
    t = [0.0] * 6
    for n in e.get("dugumler", []):
        for i in range(6):
            t[i] += n["F"][i]
    for c in e.get("cubuklar", []):
        for y in c.get("yayili", []):
            for i in range(3):
                t[i] += (y["q1"] + y["q2"]) / 2 * (y["x2"] - y["x1"]) * y["vek"][i]
        for y in c.get("tekil", []):
            for i in range(3):
                t[i] += y["P"] * y["vek"][i]
    return t


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
    _uyarisiz(r, veri)
    assert tip == Counter(r["sayac"])
    genel = _genel_mi(ad)
    nx, ny = len(bina["akslar"]["x"]), len(bina["akslar"]["y"])
    nz = len(bina["akslar"]["z"]) if genel else len(bina["katlar"])      # ızgara seviyeleri: Z aksları (yoksa katlar)
    assert tip["IFCBUILDINGSTOREY"] == len(bina["katlar"])
    if genel:
        # surum 3: her çubuk bir IfcColumn/IfcBeam/IfcMember, her panel bir IfcSlab/IfcCovering/IfcPlate; tekil temel kolon tabanlarında
        gb = _genel_beklenen(bina)
        assert tip["IFCCOLUMN"] + tip["IFCBEAM"] + tip["IFCMEMBER"] == gb["cubuk"]
        assert tip["IFCSLAB"] + tip["IFCCOVERING"] + tip["IFCPLATE"] == gb["panel"]
        if gb["temel"] is not None:
            assert tip["IFCFOOTING"] == gb["temel"]
        tb = {"dc": 0, "ag": False}
    else:
        assert tip["IFCCOLUMN"] == len(bina["kolonlar"])
        assert tip["IFCBEAM"] == len(bina["kirisler"])
        tb = _temel_beklenen(bina, veri)
        assert tip["IFCSLAB"] == len(bina["dosemeler"]) + tb["baseslab"]
        assert tip["IFCFOOTING"] == tb["pad"] + tb["strip"] + tb["beam"]
        assert len(re.findall(r"IFCFOOTING\([^\n]*\.PAD_FOOTING\.\);", r["metin"])) == tb["pad"]
        assert len(re.findall(r"IFCFOOTING\([^\n]*\.STRIP_FOOTING\.\);", r["metin"])) == tb["strip"]
        assert len(re.findall(r"IFCFOOTING\([^\n]*\.FOOTING_BEAM\.\);", r["metin"])) == tb["beam"]
        assert len(re.findall(r"IFCSLAB\([^\n]*\.BASESLAB\.\);", r["metin"])) == tb["baseslab"]
    if not bina.get("aks_sistemleri"):
        assert tip["IFCGRID"] == nz              # her Z (kat) seviyesinde aks ızgarası
        assert tip["IFCGRIDAXIS"] == nz * (nx + ny)
    assert tip["IFCSTRUCTURALANALYSISMODEL"] == 1
    assert tip["IFCAPPLICATION"] == 1
    if veri is None:
        assert tip["IFCSTRUCTURALCURVEMEMBER"] == (len(bina["cubuklar"]) if genel else len(bina["kolonlar"]) + len(bina["kirisler"]))
        if not genel:
            assert tip["IFCSTRUCTURALPOINTCONNECTION"] == nx * ny * len(bina["katlar"])
        assert tip["IFCSTRUCTURALLOADCASE"] >= 2
    else:
        ag = veri["ag"]
        efendi = {d["no"] for d in ag["dugumler"] if d.get("efendi")}
        merkez, bag, _ortak = _diyafram_beklenen(veri)      # eylem taşıyan diyafram merkezleri ve rijit bağları (K-37)
        assert tip["IFCSTRUCTURALCURVEMEMBER"] == sum(1 for e in ag["elemanlar"] if not set(e["dugumler"]) & efendi) + bag
        assert tip["IFCSTRUCTURALPOINTCONNECTION"] == len(ag["dugumler"]) - len(efendi) + merkez
        uyg = [k for k in veri["kombinasyonlar"] if k["uygulandi"] and k["tur"] != "drift"]
        durumlar = set(veri["durumlar"]) | {"G", "Q"} | {d for k in uyg for d in k["katsayilar"]} | set(veri["yukler"].get("eylemler") or {})
        assert tip["IFCSTRUCTURALLOADCASE"] == len(durumlar)
        assert tip["IFCSTRUCTURALLOADGROUP"] == len(uyg)
        assert tip["IFCRELASSIGNSTOGROUPBYFACTOR"] == sum(len(k["katsayilar"]) for k in uyg)
        assert tip["IFCSTRUCTURALLINEARACTION"] + tip["IFCSTRUCTURALCURVEACTION"] > 0
        dc = [e for e in veri.get("tasarim", {}).get("elemanlar", []) if e.get("dc") is not None]
        # bina elemanları + temel hattı / radye D/C'si (veri.temel.tasarim)
        assert len(re.findall(r"IFCPROPERTYSINGLEVALUE\('DC',\$,IFCRATIOMEASURE\(", r["metin"])) == len(dc) + tb["dc"]
        if genel:
            # analiz üyeleri (FE parçaları) motor çubuk no'suyla fiziksel elemana bağlı; yükler çözümün G, Q, S toplamlarına eşit
            assert tip["IFCRELASSIGNSTOPRODUCT"] == len(bina["cubuklar"])
            toplam, _e, _v = _yuk_toplamlari(r["metin"])
            for d, deger in veri["yukler"]["toplam"].items():
                assert toplam[d] == pytest.approx(deger, rel=1e-6, abs=1e-6), d
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
# Genel model (surum 3): motorun kesit dili, vute, G/Q/S yükleri (ifcopenshell gerekmez)
# ---------------------------------------------------------------------------
BASIT_ADLAR = ["BORU 168.3x6.3", "BORU 114.3x4", "KUTU 150x8", "KUTU 200x100x6", "L 100x10", "2L 70x7 s=10", "UPN 200",
               "upn 80", "Kutu 40×40×3", "2L 100x100x10", "BORU 48,3x3,2", "UPN 200.4", "UPN 219.5", "L 100x100x10"]
# motorun reddettiği adlar (tasarim._ad_coz MatrisHatasi): basitProfil null döner (K-8)
BASIT_RED = ["L 100x80x8", "2L 100x80x8", "2L 100x80x8 s=10", "UPN 221.5", "UPN 210"]


def test_basit_profil_tasarim_ile_ayni():
    """MatrisIFC.basitProfil (C9): motorun ad dilbilgisi; A, Iy, Iz (Iy yatay y ekseni etrafında) ve J tasarim.kesit_ozellik ile
    aynı (cm birimli katalog değerleri → m), ad motorun yazdığı biçimde."""
    import tasarim
    r = _node("-e", "const M = require(process.argv[1]); process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(M.basitProfil)))",
              str(MODUL), json.dumps(BASIT_ADLAR))
    assert r.returncode == 0, r.stderr
    for ad, js in zip(BASIT_ADLAR, json.loads(r.stdout)):
        p = tasarim.kesit_ozellik(ad)
        assert js["ad"] == p["ad"], ad
        assert js["tur"] == p["tip"], ad
        assert js["A"] == pytest.approx(p["A"] * 1e-4, rel=0.02), ad
        assert js["Iy"] == pytest.approx(p["Iy"] * 1e-8, rel=0.02), ad
        assert js["Iz"] == pytest.approx(p["Iz"] * 1e-8, rel=0.02), ad
        assert js["J"] == pytest.approx(p["It"] * 1e-8, rel=0.02), ad


def test_basit_profil_motorun_reddettigi_adlar():
    """K-8: motorun kabul etmediği basit kesit adları (farklı kollu korniyer, tablo dışı UPN) basitProfil'de de null."""
    import tasarim
    from yapi import MatrisHatasi
    r = _node("-e", "const M = require(process.argv[1]); process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(M.basitProfil)))",
              str(MODUL), json.dumps(BASIT_RED))
    assert r.returncode == 0, r.stderr
    for ad, js in zip(BASIT_RED, json.loads(r.stdout)):
        with pytest.raises(MatrisHatasi):
            tasarim.kesit_ozellik(ad)
        assert js is None, ad


def test_genel_model_cbf_kesit_ve_yukler():
    """celik-cbf-3kat (yapi.bina_coz verisi JSON'dan geçmiş): BORU çaprazları IfcCircleHollowProfileDef (dikdörtgen değil, 'tabloda
    yok' uyarısı yok); döşeme panellerinin üçgen payları IfcStructuralCurveAction; D/C her çubukta."""
    bina, veri, r = _sablon_ifc("celik-cbf-3kat", True)
    tip = _step_denetle(r["metin"])
    assert not [u for u in r["uyarilar"] if "tabloda yok" in u]
    assert tip["IFCCIRCLEHOLLOWPROFILEDEF"] > 0
    assert tip["IFCSTRUCTURALCURVEACTION"] > 0
    assert not re.search(r"IFCRECTANGLEPROFILEDEF\(\.AREA\.,'BORU", r["metin"])
    assert re.search(r"IFCCIRCLEHOLLOWPROFILEDEF\(\.AREA\.,'BORU 168\.3x6\.3',\$,0\.08415,0\.0063\)", r["metin"])
    assert len(re.findall(r"IFCPROPERTYSINGLEVALUE\('DC',", r["metin"])) == len(bina["cubuklar"])


def test_genel_model_sanayi_vute():
    """celik-sanayi-4hol: VUTE kesiti 0,30 × 0,30 dikdörtgen değil; temel profil (IPE 400) + derin uç profili (h + 0,40 m) ile
    IfcExtrudedAreaSolidTapered, Pset_MatrisVute; uyarılar tekrarsız (boş)."""
    bina, _veri, r = _sablon_ifc("celik-sanayi-4hol", False)
    tip = _step_denetle(r["metin"])
    assert not re.search(r"IFCRECTANGLEPROFILEDEF\(\.AREA\.,'VUTE'", r["metin"])
    vute = [c for c in bina["cubuklar"] if bina["kesitler"][c["kesit"]]["tip"] == "vute"]
    assert vute
    assert tip["IFCEXTRUDEDAREASOLIDTAPERED"] == len(vute)
    assert re.search(r"IFCISHAPEPROFILEDEF\(\.AREA\.,'IPE 400 \(vute derin u\\X2\\00E7\\X0\\, h = 0\.8 m\)',#\d+,0\.18,0\.8,", r["metin"])
    assert len(re.findall(r"IFCPROPERTYSET\('[^']{22}',#\d+,'Pset_MatrisVute'", r["metin"])) == len(vute)
    assert len(r["uyarilar"]) == len(set(r["uyarilar"]))
    assert r["uyarilar"] == []


def _cubuk_yukleri(metin, veri):
    """STEP eylemlerinden çubuk × durum düşey toplamları (analiz üyesi adındaki [E<no>] → veri.ag.elemanlar[].cubuk)."""
    toplam, eylemler, V = _yuk_toplamlari(metin)
    cubuk = {e["no"]: e["cubuk"] for e in veri["ag"]["elemanlar"]}
    sonuc = Counter()
    for durum, uye, v, _t in eylemler:
        if V[uye][0] == "IFCSTRUCTURALCURVEMEMBER":
            sonuc[(cubuk[int(re.search(r"\[E(\d+)\]", V[uye][1][2][1]).group(1))], durum)] += v
    return toplam, sonuc


def _cubuk_yuklerini_karsilastir(metin, veri):
    toplam, cub = _cubuk_yukleri(metin, veri)
    for d, deger in veri["yukler"]["toplam"].items():
        assert toplam[d] == pytest.approx(deger, rel=1e-6, abs=1e-6), d
    for c in veri["yukler"]["cubuklar"]:
        for d in ("G", "Q", "S"):
            beklenen = c.get(d, {}).get("toplam_kN", 0.0)
            assert cub[(c["no"], d)] == pytest.approx(beklenen, rel=1e-6, abs=1e-6), (c["no"], d)


def test_genel_model_cubuk_yukleri():
    """Her çubuğun G, Q, S yük toplamı (öz ağırlık + duvar + panel payı + ek) çözümün veri.yukler.cubuklar değerine eşit."""
    for ad in ("celik-cbf-3kat", "celik-sanayi-4hol"):
        _bina, veri, r = _sablon_ifc(ad, True)
        _cubuk_yuklerini_karsilastir(r["metin"], veri)


@lru_cache(maxsize=None)
def _genel_kesit_cozumlu():
    import yapi
    bina = _ornek_bina("genel_kesit")
    veri = json.loads(json.dumps(yapi.bina_coz(bina, anlat=False).veri))
    return bina, veri, _uret(bina, veri)


def test_ornek_genel_kesit_motorla_cozulur():
    """Motorun kesit dilindeki örnek (basit kesit adları, boyutlar, iki uçta vute, iki çubuklu panel kenarı zinciri, dağıtımı "yok"
    olan cephe paneli, kısmi/tekil/düğüm ek yükleri) motorla çözülür; IFC uyarısız; yükler çözümle aynı."""
    bina, veri, r = _genel_kesit_cozumlu()
    tip = _step_denetle(r["metin"])
    assert r["uyarilar"] == []
    for t in ("IFCCIRCLEHOLLOWPROFILEDEF", "IFCRECTANGLEHOLLOWPROFILEDEF", "IFCLSHAPEPROFILEDEF", "IFCUSHAPEPROFILEDEF",
              "IFCCOMPOSITEPROFILEDEF", "IFCEXTRUDEDAREASOLIDTAPERED", "IFCSTRUCTURALCURVEACTION", "IFCSTRUCTURALPOINTACTION"):
        assert tip[t] >= 1, t
    assert tip["IFCEXTRUDEDAREASOLIDTAPERED"] == 4
    # {tip: "kutu", boyutlar: {H: 200, B: 100, t: 6}} → 0,1 × 0,2, et 6 mm, sıcak köşe yarıçapları r_i = t, r_o = 1,5t
    assert re.search(r"IFCRECTANGLEHOLLOWPROFILEDEF\(\.AREA\.,'KUTU 200x100x6',\$,0\.1,0\.2,0\.006,0\.006,0\.009\)", r["metin"])
    assert re.search(r"IFCUSHAPEPROFILEDEF\(\.AREA\.,'UPN 200',\$,0\.2,0\.075,0\.0085,0\.0115,0\.0115,0\.00575,0\.0798", r["metin"])
    assert re.search(r"IFCCOMPOSITEPROFILEDEF\(\.AREA\.,'2L 70x7 s=10',\(#\d+,#\d+\),'2L'\)", r["metin"])
    # çubuk üzerindeki tekil ek yük: üyeye bağlı nokta eylemi, konumu Reference/Vertex topolojisiyle
    assert re.search(r"IFCSTRUCTURALPOINTACTION\('[^']{22}',#\d+,'G / E\d+ @[0-9.]+',[^\n]*,#\d+,#\d+,#\d+,\.GLOBAL_COORDS\.,\$\);", r["metin"])
    _cubuk_yuklerini_karsilastir(r["metin"], veri)
    # dağıtımı "yok" olan cephe panelinin G'si köşe düğümlerine: dört tekil düğüm yükü toplamı = panel G toplamı
    panel = next(p for p in veri["yukler"]["paneller"] if p["dagitim"] == "yok")
    kose = re.findall(r"IFCSTRUCTURALLOADSINGLEFORCE\('G / N\d+',0\.,0\.,(-[0-9.]+),", r["metin"])
    assert sum(-float(x) for x in kose) == pytest.approx(panel["G_toplam"], rel=1e-9)


def _vute_basit_bina():
    """K-7: genel kesit örneğinde aşıklar UPN 200 temelli, saçak aşığı KUTU 200x100x6 temelli, çaprazlar BORU 114.3x4 temelli vute."""
    bina = _ornek_bina("genel_kesit")
    k = bina["kesitler"]
    k.update({"V_UPN": {"tip": "vute", "temel": "ASIK", "ek_yukseklik": 0.1, "boy": 2.0},
              "V_KUTU": {"tip": "vute", "temel": "SACAK", "ek_yukseklik": 0.1, "derin_uc": "j"},
              "V_BORU": {"tip": "vute", "temel": "CAPRAZ", "ek_yukseklik": 0.05}})
    for c in bina["cubuklar"]:
        c["kesit"] = {"ASIK": "V_UPN", "SACAK": "V_KUTU", "CAPRAZ": "V_BORU"}.get(c["kesit"], c["kesit"])
    return bina


@lru_cache(maxsize=None)
def _vute_basit_cozumlu():
    import yapi
    bina = _vute_basit_bina()
    veri = json.loads(json.dumps(yapi.bina_coz(bina, anlat=False).veri))
    return bina, veri, _uret(bina, veri)


def test_vute_basit_temel_kesit():
    """K-7: KUTU ve U temelli vute IfcExtrudedAreaSolidTapered (derin uç aynı türde, h + ek); BORU temelli vute düz katı + Pset ve tek
    uyarı. Motor bu kesitleri çözer (yapi_serbest._derin_kesit); yükler çözümle aynı."""
    bina, veri, r = _vute_basit_cozumlu()
    tip = _step_denetle(r["metin"])
    n = Counter(c["kesit"] for c in bina["cubuklar"])
    assert tip["IFCEXTRUDEDAREASOLIDTAPERED"] == 4 + n["V_UPN"] + n["V_KUTU"]
    assert re.search(r"IFCUSHAPEPROFILEDEF\(\.AREA\.,'UPN 200 \(vute derin u\\X2\\00E7\\X0\\, h = 0\.3 m\)',#\d+,0\.3,0\.075,", r["metin"])
    assert re.search(r"IFCRECTANGLEHOLLOWPROFILEDEF\(\.AREA\.,'KUTU 200x100x6 \(vute derin u\\X2\\00E7\\X0\\, h = 0\.3 m\)',#\d+,0\.1,0\.3,"
                     r"0\.006,0\.006,0\.009\)", r["metin"])
    assert len(re.findall(r"IFCPROPERTYSET\('[^']{22}',#\d+,'Pset_MatrisVute'", r["metin"])) == 4 + sum(n[a] for a in ("V_UPN", "V_KUTU", "V_BORU"))
    assert r["uyarilar"] == ["vute temel kesiti CAPRAZ: konik katı yazılmadı (bu kesit için konik profil yok); temel kesitli düz katı ve "
                             f"Pset_MatrisVute yazıldı ({n['V_BORU']} eleman)."]
    _cubuk_yuklerini_karsilastir(r["metin"], veri)


def test_vute_basit_temel_ifcopenshell(tmp_path):
    """K-7: KUTU/U temelli konik katılar EXPRESS kurallarıyla geçerli (IfcTaperedSweptAreaProfiles: aynı profil türü); konik katı derin
    uçta h + ek, ince uçta temel profil yüksekliğinde (üst yüz hizalı)."""
    _ifc()
    np = pytest.importorskip("numpy")
    import ifcopenshell.geom
    _bina, veri, r = _vute_basit_cozumlu()
    f = _ac(r["metin"], tmp_path, "vute_basit")
    assert _dogrula(f, True) == []
    dug = {d["no"]: np.array([d["X"], d["Y"], d["Z"]]) for d in veri["ag"]["dugumler"]}
    cub = {c["no"]: c for c in veri["ag"]["cubuklar"]}
    for e in f.by_type("IfcMember"):
        if e.ObjectType not in ("V_UPN", "V_KUTU"):
            continue
        v = np.array(ifcopenshell.geom.create_shape(_ayarlar(), e).geometry.verts, dtype=float).reshape(-1, 3)
        c = cub[int(e.Tag[1:])]
        P0, P1 = dug[c["i"]], dug[c["j"]]
        L = np.linalg.norm(P1 - P0)
        t = (P1 - P0) / L
        s_, z = (v - P0) @ t, v[:, 2] - P0[2]
        h = 0.2 + 0.1
        derin, ince = (0.0, L) if e.ObjectType == "V_UPN" else (L, 0.0)
        for x, hh in ((derin, h), (ince, 0.2)):
            zz = z[np.abs(s_ - x) < 1e-4]
            assert zz.max() - zz.min() == pytest.approx(hh, abs=1e-4), (e.ObjectType, x)
            assert zz.max() == pytest.approx(0.1, abs=1e-4)          # üst yüz temel profille hizalı (+h/2)


# ---------------------------------------------------------------------------
# Örnekler motorla çözülür (K-11); rüzgâr/deprem/kren eylemleri (K-37); temel öz ağırlığı (K-39)
# ---------------------------------------------------------------------------
def _yayili_temelli_genel(bina):
    return int(bina.get("surum", 1)) >= 3 and (bina.get("temeller") or {}).get("tip", "tekil") in ("surekli", "radye")


@lru_cache(maxsize=None)
def _ornek_cozumlu(ad):
    import yapi
    bina = _ornek_bina(ad)
    veri = json.loads(json.dumps(yapi.bina_coz(bina, anlat=False).veri))
    return bina, veri, _uret(bina, veri)


@pytest.mark.parametrize("ad", ORNEK_ADLARI)
def test_ornekler_cozulur(ad):
    """K-11: her örnek yapi.bina_coz ile hatasız çözülür; çözüm verisiyle IFC uyarısız, yük eylemleri var ve G/Q/S toplamları
    çözümle aynı. 'serbest' (surum 3, mütemadi temel) motor paketiyle (C11 genel modelde temel) çözülür."""
    if _yayili_temelli_genel(_ornek_bina(ad)) and not _motor_genel_temel():
        pytest.skip("genel modelde mütemadi/radye temel motor paketi (C11) ile gelir")
    bina, veri, r = _ornek_cozumlu(ad)
    tip = _step_denetle(r["metin"])
    _uyarisiz(r, veri)
    assert tip["IFCSTRUCTURALLINEARACTION"] + tip["IFCSTRUCTURALCURVEACTION"] > 0
    vek = _yuk_vektorleri(r["metin"])
    temelli = (veri.get("temel") or {}).get("tip") in ("surekli", "radye")
    for d in ("G", "Q", "S"):
        if d == "G" and temelli and not _motor_c11():
            continue                                   # temel öz ağırlığı motorla (oz_yuk) gelir
        assert -vek.get(d, [0.0] * 6)[2] == pytest.approx(veri["yukler"]["toplam"].get(d, 0.0), abs=0.1), d


@pytest.mark.parametrize("ad", ["celik-sanayi-4hol", "betonarme-3kat-3x3", "celik-cbf-3kat"])
def test_eylem_toplamlari(ad):
    """K-37 (C16): her rüzgâr / deprem / kren durumunun IFC eylem bileşkesi veri.yukler.eylemler ile aynı (kuvvet ve moment); W =
    veri.ruzgar.toplam (panel yöntemi) ya da ±toplam_x / ±toplam_y; EX±/EY± ΣF = V_tE; K = tekerlek yükleri (düşey); EZ = G_carpani × G."""
    if not _motor_c16():
        pytest.skip("veri.yukler.eylemler motor paketi (C16) ile gelir")
    bina, veri, r = _sablon_ifc(ad, True)
    _step_denetle(r["metin"])
    assert r["uyarilar"] == []
    eyl = veri["yukler"]["eylemler"]
    assert {d for d in veri["durumlar"] if d[0] in "WE"} <= set(eyl)
    vek = _yuk_vektorleri(r["metin"])
    ruz = veri.get("ruzgar") or {}
    for d, e in eyl.items():
        t = vek[d]
        if e.get("G_carpani"):
            assert t[:3] == pytest.approx([e["G_carpani"] * x for x in vek["G"][:3]], abs=1e-6), d
            continue
        assert t == pytest.approx(_eylem_toplami(e), abs=1e-6), d
        if d[0] == "W":
            if ruz.get("toplam"):
                assert t[:3] == pytest.approx(ruz["toplam"][d], abs=1e-6), d
            else:
                i = 0 if d[-1] == "X" else 1
                assert t[i] == pytest.approx((1 if d[1] == "+" else -1) * ruz["toplam_" + d[-1].lower()], abs=1e-6), d
        elif d[:2] in ("EX", "EY"):
            i = 0 if d[1] == "X" else 1
            assert abs(t[i]) == pytest.approx(veri["deprem"][d[1]]["VtE"], rel=1e-9), d
            assert t[1 - i] == pytest.approx(0.0, abs=1e-9)
        elif d[0] == "K":
            k = next(k for k in veri["kren"]["kopruler"] if d in k["durumlar"])
            tk = k["tekerlek"]
            assert -t[2] == pytest.approx((tk["P_maks"] + tk["P_min"]) * tk["adet"] * k["dinamik"], rel=1e-9), d
    if ad == "celik-sanayi-4hol":
        assert any(d[0] == "K" for d in eyl)
    # her yapısal düğüm ayrı konumda: efendi bir kat düğümüyle çakışırsa (betonarme-3kat-3x3: kütle merkezi orta kolonda) merkez o kat
    # düğümüdür; aynı yerde ikinci bağlantı (düğüm birleştiren okuyucuda uz, rx, ry koşuluyla kolonu mesnetlerdi) yazılmaz
    V = _varliklar(r["metin"])
    konum = Counter()
    for t, a in V.values():
        if t == "IFCSTRUCTURALPOINTCONNECTION":
            tepe = V[_r(V[_r(V[_r(a[6])][1][2][0])][1][3][0])]
            konum[tuple(round(x, 3) for x in V[_r(tepe[1][0])][1][0])] += 1
    assert max(konum.values()) == 1
    merkez, bag, ortak = _diyafram_beklenen(veri)
    adlar = Counter(V[_r(a[4])][0] for t, a in V.values() if t == "IFCRELCONNECTSSTRUCTURALACTIVITY"
                    and V[_r(a[5])][0] == "IFCSTRUCTURALPOINTACTION" and "Diyafram merkezinde" in (V[_r(a[5])][1][3] or ("S", ""))[1])
    assert set(adlar) <= {"IFCSTRUCTURALPOINTCONNECTION"} and (sum(adlar.values()) > 0) == (merkez + ortak > 0)
    if ad == "betonarme-3kat-3x3":
        assert (merkez, ortak) == (0, 3)


@lru_cache(maxsize=None)
def _genel_temel_ifc(ad):
    """Aks–kat şablonunun model_ops.genellestir ile genel modeli (mütemadi/radye temel korunur), motorla çözümü ve IFC'si."""
    import yapi
    b = _node("-e", "const MO = require(process.argv[1]); process.stdout.write(JSON.stringify(MO.genellestir(JSON.parse(process.argv[2])).model))",
              str(PROJE / "docs" / "model_ops.js"), json.dumps(yapi.bina_sablon(ad)))
    assert b.returncode == 0, b.stderr
    bina = json.loads(b.stdout)
    veri = json.loads(json.dumps(yapi.bina_coz(bina, anlat=False).veri))
    return bina, veri, _uret(bina, veri)


_TEMEL_SABLONLARI = ["betonarme-3kat-surekli-temel", "betonarme-4kat-radye"]


@pytest.mark.parametrize("ad", _aks_kat_sablonlari() + [f"genel:{a}" for a in _TEMEL_SABLONLARI])
def test_temel_oz_agirligi_toplami(ad):
    """K-39 (C11 oz_yuk): IFC G toplamı = veri.yukler.toplam.G (temel öz ağırlığı dahil; 0,1 kN içinde), Q ve S (aks–kat karı çatı
    katı döşeme paylarından, veri.kar) aynı; mütemadi/radye temel elemanlarında ve temel düğümlerinde G eylemleri var (Σq·L + ΣP = W)."""
    genel = ad.startswith("genel:")
    kok = ad.split(":", 1)[-1]
    import yapi
    tip_ = yapi.BINA_SABLONLARI[kok].get("temeller", {}).get("tip", "tekil")
    if genel and not _motor_genel_temel():
        pytest.skip("genel modelde mütemadi/radye temel motor paketi (C11) ile gelir")
    if tip_ != "tekil" and not _motor_c11():
        pytest.skip("veri.temel.oz_yuk motor paketi (C11) ile gelir")
    _bina, veri, r = _genel_temel_ifc(kok) if genel else _sablon_ifc(kok, True)
    _step_denetle(r["metin"])
    _uyarisiz(r, veri)
    vek = _yuk_vektorleri(r["metin"])
    assert -vek["G"][2] == pytest.approx(veri["yukler"]["toplam"]["G"], abs=0.1)
    assert -vek["Q"][2] == pytest.approx(veri["yukler"]["toplam"]["Q"], abs=1e-6)
    assert -vek.get("S", [0.0] * 6)[2] == pytest.approx(veri["yukler"]["toplam"].get("S", 0.0), abs=1e-6)
    if tip_ != "tekil":
        oz = veri["temel"]["oz_yuk"]
        assert sum(x["P"] for x in oz["dugumler"]) + sum(
            x["q"] * next(e["L"] for e in veri["ag"]["elemanlar"] if e["no"] == x["no"]) for x in oz["elemanlar"]) == pytest.approx(oz["W"], abs=0.01)
        _t, eylemler, V = _yuk_toplamlari(r["metin"])
        tur = {e["no"]: e["tur"] for e in veri["ag"]["elemanlar"]}
        no = lambda u: int(re.search(r"\[E(\d+)\]", V[u][1][2][1]).group(1))      # noqa: E731 — analiz üyesi adındaki FE no
        temel_uye = {no(u) for d, u, _v, _t2 in eylemler if d == "G" and V[u][0] == "IFCSTRUCTURALCURVEMEMBER"
                     and tur.get(no(u)) in ("temel-kirisi", "radye-serit")}
        assert temel_uye == {x["no"] for x in oz["elemanlar"] if x["q"]}


def test_genel_temel_ifcopenshell(tmp_path):
    """Genelleştirilmiş mütemadi temelli model (motorla çözülmüş): EXPRESS kurallarıyla geçerli; diyafram merkezleri ve bağları dahil."""
    _ifc()
    if not _motor_genel_temel():
        pytest.skip("genel modelde mütemadi/radye temel motor paketi (C11) ile gelir")
    _bina, veri, r = _genel_temel_ifc("betonarme-3kat-surekli-temel")
    f = _ac(r["metin"], tmp_path, "genel_surekli")
    assert _dogrula(f, True) == []
    merkez, bag, _ortak = _diyafram_beklenen(veri)
    assert len([n for n in f.by_type("IfcStructuralPointConnection") if n.Name.endswith("diyafram merkezi")]) == merkez
    assert len([u for u in f.by_type("IfcStructuralCurveMember") if "diyafram ba" in u.Name]) == bag


def test_genel_model_kesit_uyarisi_tekil():
    """Tabloda olmayan profil: uyarı kesit adı başına bir kez, kullanım sayısıyla (çubuk başına değil)."""
    bina = _ornek_bina("genel_kesit")
    bina["kesitler"]["CAPRAZ"] = {"tip": "profil", "profil": "XYZ 120", "malzeme": "S275"}
    r = _uret(bina)
    _step_denetle(r["metin"])
    n = sum(1 for c in bina["cubuklar"] if c["kesit"] == "CAPRAZ")
    assert r["uyarilar"] == [f"Profil 'XYZ 120' tabloda yok; b × h dikdörtgen katı ile gösterildi ({n} eleman)."]


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
                  ("betonarme-4kat-radye", True), ("celik-cbf-3kat", True), ("celik-sanayi-4hol", True)}
KURALLI_ORNEK = {"serbest", "radye", "aks", "genel_kesit"}
# motorun basit kesit adı öneki → IFC profil sınıfı
_BASIT_IFC = {"BORU": "IfcCircleHollowProfileDef", "KUTU": "IfcRectangleHollowProfileDef", "L": "IfcLShapeProfileDef",
              "2L": "IfcCompositeProfileDef", "UPN": "IfcUShapeProfileDef"}


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
    genel = _genel_mi(ad)
    cubuk_siniflari = list(f.by_type("IfcColumn")) + list(f.by_type("IfcBeam")) + (list(f.by_type("IfcMember")) if genel else [])
    if genel:
        gb = _genel_beklenen(bina)
        assert len(cubuk_siniflari) == gb["cubuk"]
        assert len(f.by_type("IfcFooting")) == gb["temel"]
        tb = {"ag": False}
    else:
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
    # profiller: betonarmede dikdörtgen, çelikte I (tablodaki ad ve ölçüler); genel modelde motorun basit kesit adları ve vute
    kesitler = bina["kesitler"]
    for e in cubuk_siniflari:
        p = _profil(e)
        k = kesitler[e.ObjectType]
        if k["tip"] == "vute":
            k = kesitler[k["temel"]]
        if k["tip"] == "profil" and k["profil"].split()[0] in ("IPE", "HEA", "HEB"):
            assert p.is_a("IfcIShapeProfileDef") and p.ProfileName == k["profil"]
        elif k["tip"] == "profil":
            assert p.is_a(_BASIT_IFC[k["profil"].split()[0].upper()]) and p.ProfileName == k["profil"], (e.ObjectType, p)
        else:
            assert p.is_a("IfcRectangleProfileDef")
            assert (p.XDim, p.YDim) == pytest.approx((k["b"], k["h"]))
    # aks ızgaraları: U = X aksları, V = Y aksları
    izgaralar = f.by_type("IfcGrid")
    assert len(izgaralar) == (len(bina["akslar"]["z"]) if genel else len(bina["katlar"]))
    for g in izgaralar:
        assert [a.AxisTag for a in g.UAxes] == [a["ad"] for a in bina["akslar"]["x"]]
        assert [a.AxisTag for a in g.VAxes] == [a["ad"] for a in bina["akslar"]["y"]]
    # yapısal analiz modeli
    model = f.by_type("IfcStructuralAnalysisModel")
    assert len(model) == 1
    uyeler = [o for rel in model[0].IsGroupedBy for o in rel.RelatedObjects]
    assert sum(1 for o in uyeler if o.is_a("IfcStructuralCurveMember")) == len(f.by_type("IfcStructuralCurveMember"))
    # mesnetli düğümler (diyafram merkezinin uz, rx, ry koşulu mesnet değil: motorda efendi düğümün yalnız ux, uy, rz serbestliği var)
    mesnetli = [n for n in f.by_type("IfcStructuralPointConnection") if n.AppliedCondition and not n.Name.endswith("diyafram merkezi")]
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
    elif genel:
        assert mesnetli
    else:
        assert len(mesnetli) == len(bina["akslar"]["x"]) * len(bina["akslar"]["y"])
    if veri is not None:
        dc = {(e["tur"], e["no"]): e["dc"] for e in veri.get("tasarim", {}).get("elemanlar", []) if e.get("dc") is not None}
        if genel:      # surum 3: motor kaydı çubuk no'suyla ("cubuk" alanı)
            dc = {e["cubuk"]: e["dc"] for e in veri["tasarim"]["elemanlar"] if e.get("dc") is not None}
        bulunan = 0
        for e in cubuk_siniflari:
            ps = _pset(e, "Pset_MatrisOgren")
            anahtar = ps["No"] if genel else (ps["Tur"], ps["No"])
            if anahtar in dc:
                assert ps["DC"] == pytest.approx(dc[anahtar])
                bulunan += 1
        assert bulunan == len(dc)
        birlesimler = [g for g in f.by_type("IfcStructuralLoadGroup") if g.PredefinedType == "LOAD_COMBINATION"]
        for g in birlesimler:
            assert all(rel.is_a("IfcRelAssignsToGroupByFactor") for rel in g.IsGroupedBy)


@pytest.mark.parametrize("ad", _aks_kat_sablonlari())
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
    # aşıklar: ikisi mertek ortasında (bölme düğümleri), ikisi mahyada (M aksı, Mahya Z aksı)
    asik = sorted(((mn[0] + mx[0]) / 2, (mn[2] + mx[2]) / 2) for mn, mx in (_kutu(e) for e in f.by_type("IfcMember") if e.PredefinedType == "PURLIN"))
    assert [x for p in asik for x in p] == pytest.approx([2.5, 6.75, 2.5, 6.75, 5.0, 7.5, 5.0, 7.5], abs=TOL)
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


def test_genel_kesit_ifcopenshell(tmp_path):
    """Motorla çözülmüş genel kesit örneği: EXPRESS kurallarıyla geçerli; vute derin uçta h + 0,30 m (üst yüz mertekle hizalı, alta
    büyür), ince uçta temel profil; 2L kesiti iki korniyer sırt sırta (aralık 10 mm, yatay kollar altta)."""
    _ifc()
    np = pytest.importorskip("numpy")
    import ifcopenshell.geom
    bina, veri, r = _genel_kesit_cozumlu()
    f = _ac(r["metin"], tmp_path, "genel_kesit")
    assert _dogrula(f, True) == []
    dug = {d["no"]: np.array([d["X"], d["Y"], d["Z"]]) for d in veri["ag"]["dugumler"]}
    cub = {c["no"]: c for c in veri["ag"]["cubuklar"]}

    def kesit_kutusu(e):
        """Çubuk uçlarındaki kesitlerin derinlik (yukarı) doğrultusundaki aralığı: [(alt, üst) i ucunda, j ucunda]."""
        v = np.array(ifcopenshell.geom.create_shape(_ayarlar(), e).geometry.verts, dtype=float).reshape(-1, 3)
        c = cub[int(e.Tag[1:])]
        P0, P1 = dug[c["i"]], dug[c["j"]]
        t = (P1 - P0) / np.linalg.norm(P1 - P0)
        d = np.array([0.0, 0.0, 1.0]) - t * t[2]
        d /= np.linalg.norm(d)
        s_, h = (v - P0) @ t, (v - P0) @ d
        return [(h[np.abs(s_ - x) < 1e-4].min(), h[np.abs(s_ - x) < 1e-4].max()) for x in (0.0, np.linalg.norm(P1 - P0))]

    vute = [e for e in f.by_type("IfcBeam") if e.ObjectType == "VUTE"]
    assert len(vute) == 4
    for e in vute:
        (a0, u0), (a1, u1) = kesit_kutusu(e)
        assert (a0, u0) == pytest.approx((-0.45, 0.15), abs=1e-4)          # derin uç (i): IPE 300 + 0,30 m, üst yüz +h/2
        assert (a1, u1) == pytest.approx((-0.15, 0.15), abs=1e-4)
        ps = _pset(e, "Pset_MatrisVute")
        assert ps["TemelProfil"] == "IPE 300" and ps["EkYukseklik"] == pytest.approx(0.3) and ps["DerinUc"] == "i"
        assert e.Representation.Representations[0].RepresentationType == "AdvancedSweptSolid"
    iki_l = next(e for e in f.by_type("IfcMember") if e.ObjectType == "GERGI2")
    prof = _profil(iki_l)
    assert prof.is_a("IfcCompositeProfileDef") and len(prof.Profiles) == 2
    v = np.array(ifcopenshell.geom.create_shape(_ayarlar(), iki_l).geometry.verts, dtype=float).reshape(-1, 3)
    c = cub[int(iki_l.Tag[1:])]
    P0, P1 = dug[c["i"]], dug[c["j"]]
    uc = v[np.abs((v - P0) @ ((P1 - P0) / np.linalg.norm(P1 - P0))) < 1e-6]
    yan, dus = (uc - P0)[:, 1] * 1000, (uc - P0)[:, 2] * 1000       # gergi X doğrultusunda: kesit düzlemi Y–Z (mm)
    assert (yan.min(), yan.max()) == pytest.approx((-75.0, 75.0), abs=1e-3)     # 2b + s = 150
    assert np.abs(yan).min() == pytest.approx(5.0, abs=1e-3)                     # sırtlar arası s = 10
    assert dus.max() - dus.min() == pytest.approx(70.0, abs=1e-3)               # düşey kollar 70
    kol = np.abs(yan) > 5 + 7 + 9 + 1e-3                                        # sırt + t + kök yarıçapı ötesi: yatay kollar
    assert kol.any() and (yan[kol] > 0).any() and (yan[kol] < 0).any()
    assert dus[kol].max() - dus.min() <= 7.0 + 1e-3                             # ikisi de altta (t = 7)
