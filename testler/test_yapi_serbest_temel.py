# -*- coding: utf-8 -*-
"""Genel modelde (yapi_serbest, surum 3) mütemadi ve radye temel (K-1, sözleşme C11): aks–kat motoruyla eşdeğerlik
(model_ops.genellestir), yerli surum 3 modelleri, ek aks sistemi, ters / dönük kolon, öğretici hatalar, yük akışı."""
from __future__ import annotations

import copy
import functools
import json
import shutil
import subprocess
from pathlib import Path

import pytest

import matris_ogren as mo
import yapi
import yapi_serbest as YS

PROJE = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
_BETIK = ('const M=require(process.argv[1]);let v="";process.stdin.on("data",d=>v+=d);'
          'process.stdin.on("end",()=>{process.stdout.write(JSON.stringify(M.genellestir(JSON.parse(v)).model))});')


def coz(b, anlat=False):
    return yapi.bina_coz(copy.deepcopy(b), goster="yok", anlat=anlat)


def R(x, y, z, sistem=None):
    r = {"aks": [x, y], "z": z}
    if sistem:
        r["sistem"] = sistem
    return r


def genellestir(b):
    """docs/model_ops.js genellestir (surum 3); temeller şablondaki gibi geri yazılır (arayüz kapısı eski sürümde çeviriyordu)."""
    r = subprocess.run([NODE, "-e", _BETIK, str(PROJE / "docs" / "model_ops.js")], input=json.dumps(b), capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, r.stderr
    g = json.loads(r.stdout)
    g["temeller"] = copy.deepcopy(b["temeller"])
    return g


@functools.lru_cache(maxsize=None)
def _cift(ad):
    b = yapi.bina_sablon(ad)
    g = genellestir(b)
    return b, g, coz(b).veri, coz(g).veri


def _yakin(a, b, rel=1e-5, abs_=1e-9):
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b)))


def _tasarim_anahtari(t):
    return (t["tur"], t.get("hat") or t.get("yon") or tuple(t.get("aks") or ()))


def donuk_radye():
    """6 × 6 m tek katlı betonarme çerçeve + 30° dönük ek aks sisteminde (orijin 3; 2,5) bir kolon; kirişsiz radye."""
    b = {"surum": 3, "baslik": "Dönük aks sistemli radye", "sistem": "betonarme",
         "akslar": {"x": [{"ad": "A", "konum": 0}, {"ad": "B", "konum": 6}], "y": [{"ad": "1", "konum": 0}, {"ad": "2", "konum": 6}],
                    "z": [{"ad": "T", "konum": 0, "kat": 0}, {"ad": "K1", "konum": 3.0, "kat": 1}]},
         "aks_sistemleri": [{"ad": "R", "tur": "kartezyen", "orijin": [3.0, 2.5, 0], "aci": 30, "x": [{"ad": "P", "konum": 0}],
                             "y": [{"ad": "Q", "konum": 0}]}],
         "malzemeler": {"C30": {"kutuphane": "C30/37"}, "B420C": {"kutuphane": "B420C"}},
         "kesitler": {"S40": {"tip": "dikdortgen", "b": 0.4, "h": 0.4, "malzeme": "C30"},
                      "K30x50": {"tip": "dikdortgen", "b": 0.3, "h": 0.5, "malzeme": "C30"}},
         "cubuklar": [], "ek_yukler": [],
         "temeller": {"tip": "radye", "zemin": {"q_em": 150, "k0": 15000}, "radye": {"h": 0.5, "tasma": 0.8, "ag": 0.5, "kiris": None}}}
    n = 0
    for a in (("A", "1"), ("B", "1"), ("A", "2"), ("B", "2")):
        n += 1
        b["cubuklar"].append({"no": n, "tur": "kolon", "i": R(*a, "T"), "j": R(*a, "K1"), "kesit": "S40"})
    n += 1
    b["cubuklar"].append({"no": n, "tur": "kolon", "i": R("P", "Q", "T", "R"), "j": R("P", "Q", "K1", "R"), "kesit": "S40"})
    for a, c in ((("A", "1"), ("B", "1")), (("B", "1"), ("B", "2")), (("B", "2"), ("A", "2")), (("A", "2"), ("A", "1"))):
        n += 1
        b["cubuklar"].append({"no": n, "tur": "kiris", "i": R(*a, "K1"), "j": R(*c, "K1"), "kesit": "K30x50"})
    for a in (("A", "1"), ("B", "1"), ("A", "2"), ("B", "2")):
        n += 1
        b["cubuklar"].append({"no": n, "tur": "kiris", "i": R("P", "Q", "K1", "R"), "j": R(*a, "K1"), "kesit": "K30x50"})
    for c in b["cubuklar"][5:]:
        b["ek_yukler"] += [{"tur": "cubuk", "cubuk": c["no"], "durum": "G", "q": -20}, {"tur": "cubuk", "cubuk": c["no"], "durum": "Q", "q": -8}]
    return b


def _cbf(tip):
    b = yapi.bina_sablon("celik-cbf-3kat")
    b["temeller"]["tip"] = tip
    if tip == "surekli":
        b["temeller"]["surekli"] = {"yon": "xy", "akslar": "tum", "B": 1.4, "h_tabla": 0.4, "b_govde": 0.5, "h_govde": 1.0, "tasma": 0.6,
                                    "ag": 0.5}
        b["temeller"]["zemin"] = {"q_em": 200, "k0": 20000}
    else:
        b["temeller"]["radye"] = {"h": 0.6, "tasma": 1.0, "ag": 1.0, "kiris": None}
        b["temeller"]["zemin"] = {"q_em": 150, "k0": 15000}
    return b


@functools.lru_cache(maxsize=None)
def _cbf_cozum(tip):
    return coz(_cbf(tip), anlat=True)


# ---------------------------------------------------------------------------
# aks–kat şablonları genellestir ile genel modele: veri.temel aks–kat motoruyla aynı
# ---------------------------------------------------------------------------
@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
@pytest.mark.parametrize("ad,tip", [("betonarme-3kat-surekli-temel", "surekli"), ("betonarme-4kat-radye", "radye")])
def test_genellestir_mutemadi_radye_esdegerligi(ad, tip):
    b, g, v1, v2 = _cift(ad)
    assert g["surum"] == 3 and g["temeller"]["tip"] == tip
    assert v2["model"] == "genel" and v2["temel"]["tip"] == tip and v2["bina"]["temeller"]["tip"] == tip
    T1, T2 = v1["temel"], v2["temel"]
    for k in ("p_maks", "p_min", "DC_zemin", "oturma_maks_mm", "oturma_min_mm", "q_o", "en_buyuk_dc", "farkli_oturma", "p_min_katsayili"):
        assert _yakin(T2[k], T1[k]), (k, T1[k], T2[k])
    for k in ("W_temel", "yay_toplami", "dugum_sayisi", "eleman_sayisi"):
        assert _yakin(T2["model"][k], T1["model"][k]), k
    beklenen = {"surekli": dict(p_maks=66.6443, DC_zemin=0.4443, q_o=103.902, en_buyuk_dc=0.57143, W=1088.99, n=135),
                "radye": dict(p_maks=60.5121, DC_zemin=0.50427, q_o=93.4471, en_buyuk_dc=0.71792, W=2940.0, n=195)}[tip]
    for k in ("p_maks", "DC_zemin", "q_o", "en_buyuk_dc"):
        assert T2[k] == pytest.approx(beklenen[k], rel=1e-5)
    assert T2["model"]["W_temel"] == pytest.approx(beklenen["W"], rel=1e-5)
    # temel düğümleri: numaralar aynı; basınç ve oturma konuma göre
    assert {d["no"] for d in T1["dugumler"]} == {d["no"] for d in T2["dugumler"]} and len(T2["dugumler"]) == beklenen["n"]
    n1 = {(round(d["X"], 3), round(d["Y"], 3)): d for d in T1["dugumler"]}
    for d in T2["dugumler"]:
        d1 = n1[(round(d["X"], 3), round(d["Y"], 3))]
        assert _yakin(d["p_kNm2"], d1["p_kNm2"], abs_=1e-6) and _yakin(d["w_mm"], d1["w_mm"], abs_=1e-6)
    # tasarım kayıtları (temel kirişi hat başına + tabla; radye şeritleri + zımbalama)
    t1 = {_tasarim_anahtari(t): t for t in T1["tasarim"]}
    t2 = {_tasarim_anahtari(t): t for t in T2["tasarim"]}
    assert set(t1) == set(t2)
    say = {}
    for k, t in t2.items():
        assert _yakin(t["dc"], t1[k]["dc"]), k
        say[t["tur"]] = say.get(t["tur"], 0) + 1
    assert say == ({"temel-kirisi": 6, "tabla": 1} if tip == "surekli" else {"radye-serit": 2, "zimbalama": 12})
    # tepkiler: temel düzlemi içindeki tutulu serbestliklerin (FX, FY, MZ) tepkileri düğüm başına aynı; yük toplamları
    for d in ("G", "Q", "EX+", "EY-"):
        r1 = {t["dugum"]: t for t in v1["durumlar"][d]["tepkiler"]}
        r2 = {t["dugum"]: t for t in v2["durumlar"][d]["tepkiler"]}
        assert set(r1) == set(r2) and len(r2) == beklenen["n"]
        for n, t in r2.items():
            for a in ("FX", "FY", "FZ", "MX", "MY", "MZ"):
                assert abs(t[a] - r1[n][a]) <= 1e-6 + 1e-4 * abs(r1[n][a]), (d, n, a, r1[n][a], t[a])
    for d in ("G", "Q"):
        assert abs(v2["yukler"]["toplam"][d] - v1["yukler"]["toplam"][d]) <= 1e-9
        oz = v2["durumlar"][d]["yay_ozet"]                    # C12: yazılmayan Winkler yaylarının toplamı
        assert oz["FZ"] + sum(t["FZ"] for t in v2["durumlar"][d]["tepkiler"]) == pytest.approx(v2["yukler"]["toplam"][d], rel=1e-5)
    assert v2["ozet"]["en_buyuk_temel_DC"] == pytest.approx(v1["ozet"]["en_buyuk_temel_DC"])
    # yük akışı ve korunum
    ya = T2["yuk_akisi"]
    assert ya["kolon_N"] == pytest.approx(T1["yuk_akisi"]["kolon_N"], rel=1e-7) and ya["kolon_N_kolonlar"] == pytest.approx(ya["kolon_N"])
    assert ya["dugum_yuku"] == 0.0 and abs(ya["fark"]) <= 1e-3
    kg = v2["akis"]["korunum"]["G"]
    assert kg["temel_oz"] == pytest.approx(T2["model"]["W_temel"], rel=1e-5) and abs(kg["ek"]) <= 1e-6
    assert v2["akis"]["temeller"] == [] and v2["ag"]["mesnetler"] == []
    # öz ağırlık yükleri (C11.3; iki motorda da)
    for T in (T1, T2):
        oz = T["oz_yuk"]
        L = {e["no"]: e["L"] for e in T["elemanlar"]}
        assert sum(e["q"] * L[e["no"]] for e in oz["elemanlar"]) + sum(d["P"] for d in oz["dugumler"]) == pytest.approx(oz["W"], rel=1e-5)
    # veri.ag: temel elemanları ve düğümleri
    tem_el = [e for e in v2["ag"]["elemanlar"] if e["tur"] in ("temel-kirisi", "radye-serit")]
    assert len(tem_el) == T2["model"]["eleman_sayisi"]
    assert all(e["cubuk"] is None and e["kesit"] == ("TK" if e["tur"] == "temel-kirisi" else "RS") and e["kaynak_no"] for e in tem_el)
    assert any(d["tur"] == "temel" for d in v2["ag"]["dugumler"])
    ince = {e["no"] for e in tem_el if e["tur"] == "radye-serit"}
    assert not ince & {z["no"] for z in v2["zarf"]["elemanlar"]}                # veri.zarf'ta radye şeridi yok
    assert v2["bina"]["temeller"][tip] and "kesit" not in v2["bina"]["temeller"][tip]


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
def test_ters_ve_dik_kolonlar_zimbalama():
    """Kolonun i ucu üstte (ters çizim) ya da yerel ekseni 90° dönük (aks–kat yon 'y'): taban kuvvetleri doğru uçtan, bX/bY
    kesitin bina eksenlerindeki izdüşümünden."""
    b = yapi.bina_sablon("betonarme-4kat-radye")
    b["kesitler"]["S40x60"] = {"tip": "dikdortgen", "b": 0.4, "h": 0.6, "malzeme": "C30", "donati": "B420C", "pas": 0.03}
    for k in b["kolonlar"]:
        k["kesit"] = "S40x60"
    assert {k["yon"] for k in b["kolonlar"]} == {"x", "y"}
    g = genellestir(b)
    assert {c.get("aci", 0) for c in g["cubuklar"] if c["tur"] == "kolon"} == {0, 90}
    v1, v2 = coz(b).veri, coz(g).veri
    z1 = {tuple(t["aks"]): t for t in v1["temel"]["tasarim"] if t["tur"] == "zimbalama"}
    z2 = {tuple(t["aks"]): t for t in v2["temel"]["tasarim"] if t["tur"] == "zimbalama"}
    assert set(z1) == set(z2) and len(z2) == 12
    for k in z1:
        assert abs(z2[k]["dc"] - z1[k]["dc"]) <= 1e-9 and z2[k]["u_p"] == pytest.approx(z1[k]["u_p"], abs=1e-9)
    ters = copy.deepcopy(g)
    for c in ters["cubuklar"]:
        if c["tur"] == "kolon":
            c["i"], c["j"] = c["j"], c["i"]
    v3 = coz(ters).veri
    z3 = {tuple(t["aks"]): t for t in v3["temel"]["tasarim"] if t["tur"] == "zimbalama"}
    for k in z2:
        assert z3[k]["dc"] == pytest.approx(z2[k]["dc"], abs=1e-9)
    assert v3["temel"]["yuk_akisi"]["kolon_N"] == pytest.approx(v2["temel"]["yuk_akisi"]["kolon_N"], abs=1e-6)
    assert v3["temel"]["p_maks"] == pytest.approx(v2["temel"]["p_maks"], abs=1e-9)


# ---------------------------------------------------------------------------
# yerli surum 3 modelleri
# ---------------------------------------------------------------------------
def test_cbf_mutemadi_xy_caprazli_yuk_akisi():
    r = _cbf_cozum("surekli")
    v = r.veri
    T = v["temel"]
    assert v["model"] == "genel" and T["tip"] == "surekli"
    say = {}
    for t in T["tasarim"]:
        say[t["tur"]] = say.get(t["tur"], 0) + 1
    assert say == {"temel-kirisi": 7, "tabla": 1}
    assert any("C30/37" in x for x in T["varsayimlar"]) and YS.TEMEL_MAFSAL_NOTU in T["varsayimlar"]
    ya = T["yuk_akisi"]                        # çaprazlar da tabana iner: kolon_N (bütün çubuklar) > yalnız kolonlar
    assert ya["kolon_N"] == pytest.approx(4508.32, abs=0.02) and ya["kolon_N_kolonlar"] == pytest.approx(4353.88, abs=0.02)
    assert abs(ya["fark"]) <= 1e-3 and ya["dugum_yuku"] == 0.0
    kg = v["akis"]["korunum"]["G"]
    assert kg["temel_oz"] == pytest.approx(T["model"]["W_temel"], rel=1e-5) and abs(kg["ek"]) <= 1e-6
    assert kg["kolon_taban"] == pytest.approx(kg["toplam"], rel=1e-9) and kg["temel"] == 0.0
    md = r.anlatim.markdown()
    assert "Temel ve zemin" in md and "Temel öz" in md and "Winkler yayı k_z = k0·A_etki" in md
    assert r.ic["temel"]["k0"] == 20000 and r.ic["alan"]["ag"]["temel"] is not None


def test_cbf_radye_zimbalama_ve_kombinasyon():
    r = _cbf_cozum("radye")
    T = r.veri["temel"]
    assert sum(1 for t in T["tasarim"] if t["tur"] == "zimbalama") == 12
    assert abs(T["yuk_akisi"]["fark"]) <= 1e-3
    k = yapi.kombinasyon_kisa(r.ic, "G+Q")
    assert k["temel"]["p_maks"] == pytest.approx(T["p_maks"], rel=1e-6)


@pytest.mark.parametrize("tip", ["surekli", "radye"])
def test_sanayi_otomatik_ag(tip):
    b = yapi.bina_sablon("celik-sanayi-4hol")
    b["temeller"]["tip"] = tip
    if tip == "surekli":
        b["temeller"]["surekli"] = {"yon": "y", "akslar": "tum", "B": 1.2, "h_tabla": 0.35, "b_govde": 0.5, "h_govde": 0.9, "tasma": 0.5,
                                    "ag": "otomatik"}
    else:
        b["temeller"]["radye"] = {"h": 0.5, "tasma": 0.5, "ag": "otomatik", "kiris": None}
    v = coz(b).veri
    T = v["temel"]
    assert T["tip"] == tip and T["tasarim"] and abs(T["yuk_akisi"]["fark"]) <= 1e-3
    assert any("büyütüldü" in n for n in T["notlar"])
    assert abs(v["akis"]["korunum"]["G"]["ek"]) <= 1e-6


# ---------------------------------------------------------------------------
# ek aks sistemi, açık mesnet, kopuk taban, bağ kirişi, numara çakışması
# ---------------------------------------------------------------------------
def test_donuk_sistem_kirissiz_radye_sanal_cizgiler():
    r = coz(donuk_radye(), anlat=True)
    T = r.veri["temel"]
    iz = T["model"]["izgara"]
    assert any(abs(x - 3.0) < 1e-6 for x in iz["x"]) and any(abs(y - 2.5) < 1e-6 for y in iz["y"])
    z = [t for t in T["tasarim"] if t["tur"] == "zimbalama"]
    assert len(z) == 5 and any(t["kolon_no"] == 5 for t in z)
    BT = r.ic["alan"]["ag"]["temel"].BT
    assert BT.sanal == 2 and BT.kolon_no[5]["adres"] == "Ç5 (R:PQ)"
    assert any("sanal çizgi" in n for n in T["notlar"]) and "sanal çizgi" in r.anlatim.markdown()


def test_donuk_sistem_mutemadi_ve_kirisli_radye_hatasi_ve_mesnetle_cozum():
    b = donuk_radye()
    b["temeller"] = {"tip": "surekli", "zemin": {"q_em": 150, "k0": 15000}, "surekli": {"yon": "xy", "B": 1.0, "tasma": 0.5}}
    with pytest.raises(mo.MatrisHatasi, match="GLOBAL X/Y aks kesişiminde değil") as h:
        coz(b)
    assert str(h.value).startswith("Mütemadi temel: taban düğümü") and "(R:PQ/T)" in str(h.value)
    k = donuk_radye()
    k["temeller"]["radye"]["kiris"] = {"b": 0.4, "h": 1.0}
    with pytest.raises(mo.MatrisHatasi, match=r"^Kirişli radye: taban düğümü .* GLOBAL X/Y aks kesişiminde değil"):
        coz(k)
    b["mesnetler"] = [{"dugum": R("P", "Q", "T", "R"), "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}]
    v = coz(b).veri
    assert v["temel"]["tip"] == "surekli" and len(v["akis"]["mesnetler"]) == 1
    kg = v["akis"]["korunum"]["G"]
    assert kg["kolon_taban"] == pytest.approx(kg["toplam"], rel=1e-9) and kg["temel"] > 0      # açık mesnet tepkisi + yaylar


def test_acik_mesnet_ag_uzerinde_hatasi():
    b = donuk_radye()
    b["mesnetler"] = [{"dugum": R("A", "1", "T"), "uz": True}]          # radye ızgarası bütün aks kesişimlerinden geçer
    with pytest.raises(mo.MatrisHatasi, match=r"Düğüm 1 \(A1/T\) açık mesnetli \('mesnetler'\) ve radye ağının üzerinde\. Açık mesnedi "
                                              r"kaldırın \(düğüm temele oturur\) ya da tekil temel seçin\."):
        coz(b)
    for tip, ad in (("radye", "radye"), ("surekli", "mütemadi temel")):
        # aks kesişimi dışındaki bir ağ noktası (A1–B1 arası, x = 3): bölme düğümüne kolon ve açık mesnet
        b = donuk_radye()
        b["cubuklar"] = [c for c in b["cubuklar"] if c["no"] not in (5, 10, 11, 12, 13)]
        b["ek_yukler"] = [y for y in b["ek_yukler"] if y["cubuk"] not in (5, 10, 11, 12, 13)]
        if tip == "surekli":
            b["temeller"] = {"tip": "surekli", "surekli": {"yon": "xy", "B": 1.0, "tasma": 0.5, "ag": 0.5}}
        b["dugumler"] = [{"no": 7000, "tur": "bolme", "cubuk_i": R("A", "1", "T"), "cubuk_j": R("B", "1", "T"), "oran": 0.5}]
        b["cubuklar"] += [{"no": 30, "tur": "kolon", "i": {"dugum": 7000}, "j": {"X": 3.0, "Y": 0.0, "Z": 3.0}, "kesit": "S40"},
                          {"no": 31, "tur": "kiris", "i": {"X": 3.0, "Y": 0.0, "Z": 3.0}, "j": R("A", "1", "K1"), "kesit": "K30x50"}]
        b["mesnetler"] = [{"dugum": {"dugum": 7000}, "uz": True}]
        with pytest.raises(mo.MatrisHatasi, match=rf"Düğüm 7000 \(D7000 \(bölme\)\) açık mesnetli \('mesnetler'\) ve {ad} ağının üzerinde"):
            coz(b)
    # mütemadi temelde ağın dışında kalan açık mesnet bağımsız nokta mesnedidir (A1 kolonsuz kalınca şerit A1'e uzanmaz)
    b = donuk_radye()
    b["temeller"] = {"tip": "surekli", "surekli": {"yon": "xy", "B": 1.0, "tasma": 0.5}}
    b["mesnetler"] = [{"dugum": R("A", "1", "T"), "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True},
                      {"dugum": R("P", "Q", "T", "R"), "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}]
    v = coz(b).veri
    assert [m["adres"] for m in v["akis"]["mesnetler"]] == ["A1/T", "R:PQ/T"]


def test_kopuk_taban_ve_kolonsuz_listelenen_aks():
    b = donuk_radye()
    b["cubuklar"] = [c for c in b["cubuklar"] if c["no"] not in (5, 10, 11, 12, 13)]
    b["ek_yukler"] = [y for y in b["ek_yukler"] if y["cubuk"] not in (5, 10, 11, 12, 13)]
    b["akslar"]["x"].append({"ad": "C", "konum": 9.0})
    b["cubuklar"].append({"no": 40, "tur": "capraz", "i": R("C", "1", "T"), "j": R("B", "1", "K1"), "kesit": "S40",
                          "serbest": {"i": ["My", "Mz"], "j": ["My", "Mz"]}})
    b["temeller"] = {"tip": "surekli", "surekli": {"yon": "x", "B": 1.0, "tasma": 0.5}}
    with pytest.raises(mo.MatrisHatasi) as h:
        coz(b)
    m = str(h.value)
    assert m.startswith("Mütemadi temel: taban düğümü") and "C1/T" in m and "temel ağına bağlanmadı (altında temel kirişi yok)" in m
    assert m.endswith("(düğüm kolon taşımıyor: temel kirişinin uçları kolonlara göre belirlenir)")
    b["temeller"]["surekli"]["yon"] = "xy"                          # C aksında kolon yok: listelenirse temel.py hatası
    b["temeller"]["surekli"]["akslar"] = ["1", "2", "A", "B", "C"]
    with pytest.raises(mo.MatrisHatasi, match=r"temeller\.surekli\.akslar: 'C' aksında zemin kat \(kat 1\) kolonu yok"):
        coz(b)


def test_bag_kirisi_uyarisi_ve_numara_cakismasi():
    b = donuk_radye()
    b["dugumler"] = [{"no": 50001, "tur": "bolme", "cubuk_i": R("A", "1", "K1"), "cubuk_j": R("B", "1", "K1"), "oran": 0.5}]
    b["cubuklar"] = [c for c in b["cubuklar"] if c["no"] != 6]
    b["ek_yukler"] = [y for y in b["ek_yukler"] if y["cubuk"] != 6]
    b["cubuklar"] += [{"no": 6, "tur": "kiris", "i": R("A", "1", "K1"), "j": {"dugum": 50001}, "kesit": "K30x50"},
                      {"no": 20, "tur": "kiris", "i": {"dugum": 50001}, "j": R("B", "1", "K1"), "kesit": "K30x50"},
                      {"no": 21, "tur": "kiris", "i": R("A", "2", "T"), "j": R("B", "2", "T"), "kesit": "K30x50"}]
    r = coz(b)
    v = r.veri
    info = r.ic["alan"]["ag"]["temel"]
    assert info.ilk_no == 50002 and 50001 not in info.dno
    assert sum(1 for d in v["ag"]["dugumler"] if d["no"] == 50001) == 1
    assert any(u.startswith("Ç21 temel seviyesinde: temel ağıyla paralel çalışır") for u in v["uyarilar"])
    assert abs(v["temel"]["yuk_akisi"]["fark"]) <= 1e-3
    # bağ kirişi temel düğümlerine yük indirir: kolon_N (bütün çubuklar) − yalnız kolonlar = bağ kirişinin G+Q payı
    assert v["temel"]["yuk_akisi"]["kolon_N"] > v["temel"]["yuk_akisi"]["kolon_N_kolonlar"]


def test_temel_dugumune_dugum_yuku():
    b = donuk_radye()
    b["ek_yukler"].append({"tur": "dugum", "dugum": R("A", "1", "T"), "durum": "G", "FZ": -50.0})
    v = coz(b).veri
    ya = v["temel"]["yuk_akisi"]
    assert ya["dugum_yuku"] == pytest.approx(50.0) and abs(ya["fark"]) <= 1e-3


def test_temel_gorunumu_cozumsuz():
    """tablolar çözümsüz modelde de kullanır (C11.4): eleman None, lam çubuk ekseni."""
    B = YS._oku(donuk_radye())
    BT = YS._temel_gorunum(B)
    assert BT.sanal == 2 and len(BT.kolonlar) == 5 and all(k["eleman"] is None and k["lam"] for k in BT.kolonlar)
    assert set(BT.taban_ixy) == set(B.temel_dugumleri) and not B.mesnetler
    assert BT.kolon_no[1]["bX"] == pytest.approx(0.4) and BT.kolon_key[(0, 0, 1)]["dugum"] == 1


def test_kesit_onerisi_gercek_temelle():
    b = _cbf("surekli")
    for yinele in (0, 1):
        o = YS.kesit_oner(copy.deepcopy(b), hedef=[{"tur": "cubuk", "no": 1}], yinele=yinele)
        assert o["oneriler"] and not any("tekil temel" in u for u in o["uyarilar"])
        if yinele:
            assert o["bina"]["temeller"]["tip"] == "surekli" and o["dc_sonra"] is not None
