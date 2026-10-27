# -*- coding: utf-8 -*-
"""yapi_serbest.py: aks sistemi tabanlı genel bina modeli (surum 3) — REF çözümü, panel dağıtımı, korunum, mafsal, yalnız
çekme, kren, esnek diyafram, kesit önerisi, şablonlar, aks–kat modeliyle (model_ops.genellestir) eşdeğerlik, köprü."""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

import matris_ogren as mo
import yapi
import yapi_serbest as YS
import yapi_veri as yv

PROJE = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")


def yakin(a, b, tol=1e-6):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def R(x, y, z):
    return {"aks": [x, y], "z": z}


# ---------------------------------------------------------------------------
# küçük modeller
# ---------------------------------------------------------------------------
def portal(H=10.0, w=0.0, taban="mafsal", kiris="HEB 200", kolon="HEB 200", kiris_mafsal=False, capraz=None, kume="cythye_gkt"):
    """X–Z düzleminde tek açıklıklı portal (L = 6, h = 4); öz ağırlık yok (γ = 0); düzlem dışı ötelemeler üst düğümlerde tutulu."""
    b = {"tur": "bina", "surum": 3, "sistem": "celik", "baslik": "portal",
         "akslar": {"x": [{"ad": "A", "konum": 0.0}, {"ad": "B", "konum": 6.0}], "y": [{"ad": "1", "konum": 0.0}],
                    "z": [{"ad": "±0.00", "konum": 0.0, "kat": 0}, {"ad": "Üst", "konum": 4.0, "kat": 1}]},
         "malzemeler": {"S275": {"kutuphane": "S275", "gamma": 0.0}},
         "kesitler": {"KOLON": {"tip": "profil", "profil": kolon, "malzeme": "S275"},
                      "KIRIS": {"tip": "profil", "profil": kiris, "malzeme": "S275"},
                      "CAP": {"tip": "profil", "profil": "BORU 88.9x4", "malzeme": "S275"}},
         "cubuklar": [{"no": 1, "i": R("A", "1", "±0.00"), "j": R("A", "1", "Üst"), "tur": "kolon", "kesit": "KOLON"},
                      {"no": 2, "i": R("B", "1", "±0.00"), "j": R("B", "1", "Üst"), "tur": "kolon", "kesit": "KOLON"},
                      {"no": 3, "i": R("A", "1", "Üst"), "j": R("B", "1", "Üst"), "tur": "kiris", "kesit": "KIRIS"}],
         "mesnetler": [{"dugum": R("A", "1", "Üst"), "uy": True}, {"dugum": R("B", "1", "Üst"), "uy": True}],
         "temeller": {"mesnet": taban},
         "ek_yukler": [], "kombinasyon_kumesi": kume}
    if kiris_mafsal:
        b["cubuklar"][2]["serbest"] = {"i": ["My", "Mz"], "j": ["My", "Mz"]}
    if H:
        b["ek_yukler"].append({"tur": "dugum", "dugum": R("A", "1", "Üst"), "durum": "Q", "FX": H})
    if w:
        b["ek_yukler"].append({"tur": "cubuk", "cubuk": 3, "durum": "G", "yon": "Z", "q1": -w, "q2": -w})
    if capraz:
        mafsal = {"i": ["My", "Mz"], "j": ["My", "Mz"]}
        b["cubuklar"] += [{"no": 4, "i": R("A", "1", "±0.00"), "j": R("B", "1", "Üst"), "tur": "capraz", "kesit": "CAP", "serbest": mafsal,
                           "yalniz_cekme": capraz == "yalniz"},
                          {"no": 5, "i": R("B", "1", "±0.00"), "j": R("A", "1", "Üst"), "tur": "capraz", "kesit": "CAP", "serbest": mafsal,
                           "yalniz_cekme": capraz == "yalniz"}]
    return b


def kutu_bina(panel_kalinlik=0.0, deprem=True):
    """6 × 6 m, 4 m tek katlı çelik kutu: 4 kolon (ankastre), 4 kiriş, bir panel (kalınlık 0: sac → esnek diyafram)."""
    b = {"tur": "bina", "surum": 3, "sistem": "celik",
         "akslar": {"x": [{"ad": "A", "konum": 0.0}, {"ad": "B", "konum": 6.0}], "y": [{"ad": "1", "konum": 0.0}, {"ad": "2", "konum": 6.0}],
                    "z": [{"ad": "±0.00", "konum": 0.0, "kat": 0}, {"ad": "Çatı", "konum": 4.0, "kat": 1}]},
         "malzemeler": {"S275": {"kutuphane": "S275"}},
         "kesitler": {"K": {"tip": "profil", "profil": "HEB 200", "malzeme": "S275"}, "B": {"tip": "profil", "profil": "IPE 300", "malzeme": "S275"}},
         "cubuklar": [], "paneller": [{"no": 1, "kose": [R("A", "1", "Çatı"), R("B", "1", "Çatı"), R("B", "2", "Çatı"), R("A", "2", "Çatı")],
                                       "tur": "cati" if panel_kalinlik == 0 else "doseme", "kalinlik": panel_kalinlik, "g": 0.5, "q": 1.0,
                                       "dagitim": "iki"}],
         "temeller": {"mesnet": "ankastre"}, "kombinasyon_kumesi": "cythye_ydkt",
         "yuk_durumlari": {"E": {"acik": deprem}},
         "deprem": {"etkin": deprem, "SS": 1.0, "S1": 0.3, "zemin_sinifi": "ZC", "BKS": 3, "tasiyici": "celik-cerceve-yuksek"}}
    n = 0
    for x in "AB":
        for y in "12":
            n += 1
            b["cubuklar"].append({"no": n, "i": R(x, y, "±0.00"), "j": R(x, y, "Çatı"), "tur": "kolon", "kesit": "K"})
    for a, c in ((("A", "1"), ("B", "1")), (("A", "2"), ("B", "2")), (("A", "1"), ("A", "2")), (("B", "1"), ("B", "2"))):
        n += 1
        b["cubuklar"].append({"no": n, "i": R(*a, "Çatı"), "j": R(*c, "Çatı"), "tur": "kiris", "kesit": "B"})
    return b


def egik_cati(alfa=35.0):
    """4 × 6 m eğik çatı paneli (α), kar açık; kolonlar ankastre."""
    h_m = 3.0 + 4.0 * math.tan(math.radians(alfa))
    b = {"tur": "bina", "surum": 3, "sistem": "celik",
         "akslar": {"x": [{"ad": "A", "konum": 0.0}, {"ad": "B", "konum": 4.0}], "y": [{"ad": "1", "konum": 0.0}, {"ad": "2", "konum": 6.0}],
                    "z": [{"ad": "±0.00", "konum": 0.0, "kat": 0}, {"ad": "Saçak", "konum": 3.0, "kat": 1}, {"ad": "Mahya", "konum": h_m}]},
         "malzemeler": {"S275": {"kutuphane": "S275", "gamma": 0.0}},
         "kesitler": {"K": {"tip": "profil", "profil": "HEB 200", "malzeme": "S275"}},
         "cubuklar": [{"no": 1, "i": R("A", "1", "±0.00"), "j": R("A", "1", "Saçak"), "tur": "kolon", "kesit": "K"},
                      {"no": 2, "i": R("A", "2", "±0.00"), "j": R("A", "2", "Saçak"), "tur": "kolon", "kesit": "K"},
                      {"no": 3, "i": R("B", "1", "±0.00"), "j": R("B", "1", "Mahya"), "tur": "kolon", "kesit": "K"},
                      {"no": 4, "i": R("B", "2", "±0.00"), "j": R("B", "2", "Mahya"), "tur": "kolon", "kesit": "K"},
                      {"no": 5, "i": R("A", "1", "Saçak"), "j": R("A", "2", "Saçak"), "tur": "kiris", "kesit": "K"},
                      {"no": 6, "i": R("B", "1", "Mahya"), "j": R("B", "2", "Mahya"), "tur": "kiris", "kesit": "K"},
                      {"no": 7, "i": R("A", "1", "Saçak"), "j": R("B", "1", "Mahya"), "tur": "kiris", "kesit": "K"},
                      {"no": 8, "i": R("A", "2", "Saçak"), "j": R("B", "2", "Mahya"), "tur": "kiris", "kesit": "K"}],
         "paneller": [{"no": 1, "kose": [R("A", "1", "Saçak"), R("A", "2", "Saçak"), R("B", "2", "Mahya"), R("B", "1", "Mahya")],
                       "tur": "cati", "kalinlik": 0.0, "g": 0.5, "q": 1.0, "kar": True, "ruzgar": False, "dagitim": "iki"}],
         "temeller": {"mesnet": "ankastre"}, "kombinasyon_kumesi": "cythye_ydkt",
         "yuk_durumlari": {"S": {"acik": True, "bolge": 3, "rakim": 0}}}
    return b


def coz(b, anlat=False):
    return yapi.bina_coz(b, goster="yok", anlat=anlat)


# ---------------------------------------------------------------------------
# REF çözümü (§19.2), aks sistemleri, bölme/kesişim düğümleri, aksla birlikte taşınma
# ---------------------------------------------------------------------------
def test_ref_cozumu_ve_aks_sistemleri():
    b = portal(H=0.0)
    b["aks_sistemleri"] = [
        {"ad": "KANAT-B", "tur": "kartezyen", "orijin": [30, 0, 0], "aci": 30,
         "x": [{"ad": "A", "konum": 0}, {"ad": "B", "konum": 5}], "y": [{"ad": "1", "konum": 0}, {"ad": "2", "konum": 4}], "z": None},
        {"ad": "KUBBE", "tur": "silindirik", "orijin": [0, 20, 0], "aci": 0, "r": [{"ad": "R1", "konum": 5}],
         "teta": [{"ad": "T0", "konum": 0}, {"ad": "T90", "konum": 90}], "z": None}]
    b["dugumler"] = [{"no": 100001, "tur": "bolme", "cubuk_i": R("A", "1", "Üst"), "cubuk_j": R("B", "1", "Üst"), "oran": 0.25},
                     {"no": 100002, "tur": "kesisim", "a": [R("A", "1", "±0.00"), R("B", "1", "Üst")],
                      "b": [R("B", "1", "±0.00"), R("A", "1", "Üst")]},
                     {"no": 100003, "tur": "bolme", "cubuk_i": {"dugum": 100001}, "cubuk_j": R("B", "1", "Üst"), "oran": 0.5}]
    b["cubuklar"] += [
        {"no": 10, "i": {"sistem": "KANAT-B", "aks": ["A", "1"], "z": "±0.00"}, "j": {"sistem": "KANAT-B", "aks": ["B", "2"], "z": "±0.00"},
         "tur": "kiris", "kesit": "KIRIS"},
        {"no": 11, "i": {"sistem": "KUBBE", "aks": ["R1", "T0"], "z": "Üst"}, "j": {"sistem": "KUBBE", "aks": ["R1", "T90"], "z": "Üst"},
         "tur": "kiris", "kesit": "KIRIS"},
        {"no": 12, "i": {"aks": ["A", "1"], "kat": 1}, "j": {"dugum": 100001}, "tur": "diger", "kesit": "KIRIS"},
        {"no": 13, "i": {"dugum": 100002}, "j": {"dugum": 100003}, "tur": "diger", "kesit": "KIRIS"},
    ]
    B = YS._oku(b)
    D = B.coz.dugum
    k = B.cubuk_no[10]
    Pj = (D[k["j"]]["X"], D[k["j"]]["Y"], D[k["j"]]["Z"])
    assert Pj == pytest.approx((30 + 5 * math.cos(math.radians(30)) - 4 * math.sin(math.radians(30)),
                                5 * math.sin(math.radians(30)) + 4 * math.cos(math.radians(30)), 0.0))
    k = B.cubuk_no[11]
    assert (D[k["i"]]["X"], D[k["i"]]["Y"], D[k["i"]]["Z"]) == pytest.approx((5.0, 20.0, 4.0))
    assert (D[k["j"]]["X"], D[k["j"]]["Y"]) == pytest.approx((0.0, 25.0), abs=1e-9)
    assert (D[100001]["X"], D[100001]["Z"]) == pytest.approx((1.5, 4.0))
    assert (D[100002]["X"], D[100002]["Z"]) == pytest.approx((3.0, 2.0))       # X çaprazın kesişimi
    assert D[100003]["X"] == pytest.approx(3.75)                                  # bölmenin bölmesi (yinelemeli)
    # {aks, kat} ile {aks, z} aynı düğüm (aks–kat numarası korunur)
    assert B.cubuk_no[12]["i"] == B.cubuk_no[3]["i"] == 1001
    assert D[1001]["tur"] == "aks" and D[1001]["aks"] == ["A", "1"]


def test_ref_dongu_ve_tanimsiz_hatalari():
    b = portal(H=0.0)
    b["dugumler"] = [{"no": 100001, "tur": "bolme", "cubuk_i": {"dugum": 100002}, "cubuk_j": R("B", "1", "Üst"), "oran": 0.5},
                     {"no": 100002, "tur": "bolme", "cubuk_i": {"dugum": 100001}, "cubuk_j": R("A", "1", "Üst"), "oran": 0.5}]
    with pytest.raises(mo.MatrisHatasi, match="döngü"):
        YS._oku(b)
    b = portal(H=0.0)
    b["cubuklar"][2]["j"] = R("C", "1", "Üst")
    with pytest.raises(mo.MatrisHatasi, match="aksı yok"):
        YS._oku(b)
    b = portal(H=0.0)
    b["cubuklar"][2]["j"] = {"aks": ["B", "1"], "z": "Mahya"}
    with pytest.raises(mo.MatrisHatasi, match="Z aksı"):
        YS._oku(b)


def test_aks_tasininca_dugumler_birlikte_tasinir():
    b = yapi.bina_sablon("celik-cbf-3kat")
    B1 = YS._oku(b)
    orta = next(d for d in b["dugumler"] if d.get("tur") == "bolme")["no"]
    kes = next(d for d in b["dugumler"] if d.get("tur") == "kesisim")["no"]
    x_orta, y_kes = B1.coz.dugum[orta]["X"], B1.coz.dugum[kes]["Y"]
    b2 = copy.deepcopy(b)
    next(a for a in b2["akslar"]["x"] if a["ad"] == "C")["konum"] = 13.0     # C aksı 1 m sağa
    next(a for a in b2["akslar"]["y"] if a["ad"] == "2")["konum"] = 7.0      # 2 aksı 1 m ileri
    B2 = YS._oku(b2)
    assert B2.coz.dugum[orta]["X"] == pytest.approx(x_orta + 0.5)                # B–C ortası: bölme düğümü aksı izler
    assert B2.coz.dugum[kes]["Y"] == pytest.approx(y_kes + 0.5)                  # kesişim düğümü de
    c = next(c for c in B2.cubuklar if B2.coz.dugum[c["j"]].get("aks") == ["C", "1"])
    assert B2.coz.dugum[c["j"]]["X"] == pytest.approx(13.0)


# ---------------------------------------------------------------------------
# panel → çubuk dağıtımı
# ---------------------------------------------------------------------------
def _toplam(segs):
    return sum((u1 - u0) * (d0 + d1) / 2.0 for u0, u1, d0, d1 in segs)


def test_dikdortgen_iki_dogrultulu_45_derece():
    Q = [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)]          # lx = 4 (kısa), ly = 5
    uzun, kisa = YS._iki_kenar(Q, 0), YS._iki_kenar(Q, 1)
    # TS 500 45°: uzun kenar trapez (rampalar l_k/2 = 2, plato 2), kısa kenar üçgen (tepe 2)
    birim = yapi._sekil_parcalari("trapez", 4.0, 5.0)
    assert [(round(a, 9), round(b, 9), round(c, 9), round(d, 9)) for a, b, c, d in uzun] == \
        [(x1, x2, 2.0 * f1, 2.0 * f2) for x1, x2, f1, f2 in birim]
    assert _toplam(uzun) == pytest.approx(4.0 / 2.0 * (5.0 - 4.0 / 2.0)) and _toplam(kisa) == pytest.approx(4.0 ** 2 / 4.0)
    assert max(d for s in kisa for d in s[2:]) == pytest.approx(2.0)
    assert sum(_toplam(YS._iki_kenar(Q, e)) for e in range(4)) == pytest.approx(20.0)
    # kare: dört üçgen, her biri alanın dörtte biri
    K = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    assert all(_toplam(YS._iki_kenar(K, e)) == pytest.approx(4.0) for e in range(4))


def test_ucgen_ve_cokgen_panel_korunum():
    eskenar = [(0.0, 0.0), (6.0, 0.0), (3.0, 3.0 * math.sqrt(3.0))]
    A = 9.0 * math.sqrt(3.0)
    assert all(_toplam(YS._iki_kenar(eskenar, e)) == pytest.approx(A / 3.0) for e in range(3))
    dik = [(0.0, 0.0), (4.0, 0.0), (0.0, 3.0)]
    assert sum(_toplam(YS._iki_kenar(dik, e)) for e in range(3)) == pytest.approx(6.0)
    besgen = [(0.0, 0.0), (6.0, 0.0), (7.0, 3.0), (3.0, 5.0), (-1.0, 3.0)]
    assert sum(_toplam(YS._iki_kenar(besgen, e)) for e in range(5)) == pytest.approx(abs(YS._alan2(besgen)))
    ters = list(reversed(besgen))                                     # köşe yönü (saat yönü) sonucu değiştirmez
    assert sum(_toplam(YS._iki_kenar(ters, e)) for e in range(5)) == pytest.approx(abs(YS._alan2(besgen)))


def test_tek_dogrultulu_dagitim():
    Q = [(0.0, 0.0), (6.0, 0.0), (6.0, 2.0), (0.0, 2.0)]
    for e in (0, 2):
        s = YS._tek_kenar(Q, e, "tek-13")
        assert s[0][2] == pytest.approx(1.0) and s[0][3] == pytest.approx(1.0)      # q = p·l_k/2 düzgün
    assert YS._tek_kenar(Q, 1, "tek-13") == []
    T = [(0.0, 0.0), (4.0, 0.0), (4.0, 6.0), (0.0, 3.0)]                          # yamuk (kalkan duvar gibi)
    top = _toplam(YS._tek_kenar(T, 1, "tek-24")) + _toplam(YS._tek_kenar(T, 3, "tek-24"))
    assert top == pytest.approx(abs(YS._alan2(T)))


def test_egik_cati_izdusum_ve_kar():
    alfa = 35.0
    r = coz(egik_cati(alfa))
    v = r.veri
    p = v["yukler"]["paneller"][0]
    A_yuzey = 6.0 * 4.0 / math.cos(math.radians(alfa))
    A_yatay = 24.0
    mu = yv.kar_mu1(alfa)
    assert mu == pytest.approx(0.8 * (60 - alfa) / 30)
    assert p["G_toplam"] == pytest.approx(0.5 * A_yuzey) and p["Q_toplam"] == pytest.approx(1.0 * A_yatay)
    assert p["S_toplam"] == pytest.approx(mu * 0.75 * A_yatay)
    for d, beklenen in (("G", 0.5 * A_yuzey), ("Q", 1.0 * A_yatay), ("S", mu * 0.75 * A_yatay)):
        assert sum(t["FZ"] for t in v["durumlar"][d]["tepkiler"]) == pytest.approx(beklenen, rel=1e-6)
    assert v["ag"]["paneller"][0]["egim"] == pytest.approx(alfa)


# ---------------------------------------------------------------------------
# korunum, mafsal, el hesabı (portal)
# ---------------------------------------------------------------------------
def test_portal_el_hesabi_yatay_ve_dusey():
    H, w, L, h = 10.0, 5.0, 6.0, 4.0
    r = coz(portal(H=H, w=w, taban="mafsal"))
    v = r.veri
    tep = {t["dugum"]: t for t in v["durumlar"]["Q"]["tepkiler"] if t["dugum"] in (1, 21)}
    # antisimetrik yük: taban kesmeleri eşit (H/2), düşey tepkiler ±H·h/L (statik)
    # (kiriş eksenel kısalması simetrik bileşeni çok az bozar)
    assert tep[1]["FX"] == pytest.approx(-H / 2, rel=1e-3) and tep[21]["FX"] == pytest.approx(-H / 2, rel=1e-3)
    assert tep[1]["FX"] + tep[21]["FX"] == pytest.approx(-H, rel=1e-6)
    assert abs(tep[1]["FZ"]) == pytest.approx(H * h / L, rel=1e-6) and tep[1]["FZ"] == pytest.approx(-tep[21]["FZ"])
    # düşey düzgün yük: iki mafsallı çerçevenin yatay itkisi H = wL²/(4h(3 + 2k)), k = (I_kiriş/I_kolon)(h/L)
    k = h / L
    H_beklenen = w * L ** 2 / (4 * h * (3 + 2 * k))
    tg = {t["dugum"]: t for t in v["durumlar"]["G"]["tepkiler"] if t["dugum"] in (1, 21)}
    assert abs(tg[1]["FX"]) == pytest.approx(H_beklenen, rel=0.01) and tg[1]["FX"] == pytest.approx(-tg[21]["FX"])
    assert tg[1]["FZ"] == pytest.approx(w * L / 2, rel=1e-6)


def test_mafsalli_kiris_uc_momentleri_sifir():
    w, L = 8.0, 6.0
    r = coz(portal(H=0.0, w=w, taban="ankastre", kiris_mafsal=True))
    v = r.veri
    fe = v["ag"]["cubuklar"][2]["fe"][0]
    e = next(e for e in v["durumlar"]["G"]["elemanlar"] if e["no"] == fe)
    assert abs(e["M"][0]) < 1e-6 and abs(e["M"][-1]) < 1e-6
    assert max(e["M"]) == pytest.approx(w * L ** 2 / 8, rel=1e-6)                # basit kiriş qL²/8
    kol = next(e for e in v["durumlar"]["G"]["elemanlar"] if e["no"] == v["ag"]["cubuklar"][0]["fe"][0])
    assert max(abs(m) for m in kol["M"]) < 1e-6                                   # mafsal kolona moment aktarmaz


@pytest.mark.parametrize("model", ["portal", "kutu", "egik"])
def test_korunum_her_durum(model):
    b = {"portal": lambda: portal(H=10.0, w=5.0), "kutu": lambda: kutu_bina(0.0), "egik": lambda: egik_cati(20.0)}[model]()
    v = coz(b).veri
    for d, k in v["durumlar"].items():
        assert all(abs(x) < 1e-6 * max(1.0, v["yukler"]["toplam"]["G"]) for x in k["denge"].values()), (d, k["denge"])
    for d, p in v["akis"]["korunum"].items():
        assert yakin(p["kolon_taban"], p["toplam"], 1e-8), (d, p)


# ---------------------------------------------------------------------------
# yalnız çekme X çapraz: doğrudan (yinelemeli) çözüm
# ---------------------------------------------------------------------------
def test_x_capraz_yalniz_cekme():
    H, L, h = 20.0, 6.0, 4.0
    b = portal(H=H, taban="mafsal", kiris_mafsal=True, capraz="yalniz")
    r = coz(b)
    v = r.veri
    assert v["yalniz_cekme"]["var"] and "süperpozisyon" in v["yalniz_cekme"]["aciklama"]
    kayit = yapi.kombinasyon_kisa(r.ic, "G+Q")
    fe = {c["no"]: c["fe"][0] for c in v["ag"]["cubuklar"]}
    N = {c: -next(e for e in kayit["elemanlar"] if e["no"] == fe[c])["uc_kuvvetleri"][0] for c in (4, 5)}
    cos_a = L / math.hypot(L, h)
    # H, A üst düğümüne +X: B tabanından A üstüne giden çapraz (5) basınca düşer → devre dışı; 4 çekmede N = H / cos α
    assert N[4] == pytest.approx(H / cos_a, rel=1e-6) and abs(N[5]) < 1e-6
    assert fe[5] in v["yalniz_cekme"]["kombinasyonlar"]["G+Q"]["etkin_degil"]
    # süperpozisyon olsaydı (doğrusal, iki çapraz da etkin) her biri H/(2 cos α) taşırdı
    lin = yapi.kombinasyon_kisa(r.ic, "Q")
    N_lin = -next(e for e in lin["elemanlar"] if e["no"] == fe[4])["uc_kuvvetleri"][0]
    assert N_lin == pytest.approx(H / (2 * cos_a), rel=0.05)
    # tasarımda yalnız çekme çaprazı basınç tahkiki yapılmaz
    tas = {k["cubuk"]: k for k in v["tasarim"]["elemanlar"]}
    assert tas[5]["ozet"]["yalniz_cekme"] is True


# ---------------------------------------------------------------------------
# kren (K) alt durumları ve zarf
# ---------------------------------------------------------------------------
def kren_bina():
    return {"tur": "bina", "surum": 3, "sistem": "celik",
            "akslar": {"x": [{"ad": "A", "konum": 0.0}, {"ad": "B", "konum": 6.0}], "y": [{"ad": "1", "konum": 0.0}],
                       "z": [{"ad": "±0.00", "konum": 0.0, "kat": 0}, {"ad": "Ray", "konum": 6.0, "kat": 1}]},
            "malzemeler": {"S275": {"kutuphane": "S275", "gamma": 0.0}},
            "kesitler": {"KR": {"tip": "profil", "profil": "HEA 300", "malzeme": "S275"}},
            "cubuklar": [{"no": 1, "i": R("A", "1", "Ray"), "j": R("B", "1", "Ray"), "tur": "kren", "kesit": "KR"}],
            "mesnetler": [{"dugum": R("A", "1", "Ray"), "ux": True, "uy": True, "uz": True, "rx": True},
                          {"dugum": R("B", "1", "Ray"), "uy": True, "uz": True}],
            "kren": [{"no": 1, "yol": [1], "tekerlek": {"P_maks": 100.0, "P_min": 0.0, "H_yanal": 0.0, "H_fren": 0.0, "adet": 1, "aralik": 0.0},
                      "dinamik": 1.2, "konum_sayisi": 5}],
            "kombinasyon_kumesi": "cythye_ydkt"}


def test_kren_zarfi_ve_kombinasyonlari():
    r = coz(kren_bina())
    v = r.veri
    kr = v["kren"]
    assert len(kr["durumlar"]) == 10 and kr["durumlar"][0] == "K1.1a"
    z = kr["zarf"][0]
    assert z["M_max"] == pytest.approx(1.2 * 100.0 * 6.0 / 4.0, rel=0.005)        # tekerlek açıklık ortasında: P·φ·L/4
    assert z["V_max"] == pytest.approx(120.0, rel=0.01) or z["V_min"] == pytest.approx(-120.0, rel=0.01)
    k = next(k for k in v["kombinasyonlar"] if k.get("kren") == "K1.3a")
    assert k["katsayilar"]["K1.3a"] == pytest.approx(k["katsayilar"]["Q"]) and k["uygulandi"]
    kayit = yapi.kombinasyon_kisa(r.ic, "K1.3a")
    assert sum(t["FZ"] for t in kayit["tepkiler"]) == pytest.approx(120.0, rel=1e-6)
    assert not any(k.get("kren") for k in v["kombinasyonlar"] if k["tur"] == "deprem")


# ---------------------------------------------------------------------------
# esnek / rijit diyafram ve deprem
# ---------------------------------------------------------------------------
def test_esnek_ve_rijit_diyafram():
    ve = coz(kutu_bina(0.0)).veri                                   # sac çatı: esnek
    assert ve["ag"]["diyafram_seviye"]["1"]["mod"] == "esnek" and not any(d["efendi"] for d in ve["ag"]["dugumler"])
    VtE = ve["deprem"]["VtE"]
    assert sum(t["FX"] for t in ve["durumlar"]["EX+"]["tepkiler"]) == pytest.approx(-VtE, rel=1e-4)   # ince kayıt: 5 basamak
    vr = coz(kutu_bina(0.15)).veri                                  # betonarme döşeme paneli: rijit (efendi düğüm)
    assert vr["ag"]["diyafram_seviye"]["1"]["mod"] == "rijit" and any(d["efendi"] for d in vr["ag"]["dugumler"])
    assert vr["deprem"]["m_t"] > ve["deprem"]["m_t"]                 # 15 cm plak kütlesi
    b = kutu_bina(0.15)
    b["analiz"] = {"diyafram": {"1": "esnek"}}                      # kullanıcı seçimi önceliklidir
    assert coz(b).veri["ag"]["diyafram_seviye"]["1"]["mod"] == "esnek"


# ---------------------------------------------------------------------------
# öğretici hatalar
# ---------------------------------------------------------------------------
def test_ogretici_hatalar():
    b = kutu_bina(0.0, deprem=False)
    b["cubuklar"] = [c for c in b["cubuklar"] if c["no"] != 8]       # bir kenar kirişi yok
    with pytest.raises(mo.MatrisHatasi, match="kenarında"):
        coz(b)
    b = kutu_bina(0.0, deprem=False)
    b["ek_yukler"] = [{"tur": "dugum", "dugum": R("A", "2", "±0.00"), "durum": "Q", "FZ": -5}]
    b["cubuklar"] = [c for c in b["cubuklar"] if c["no"] != 2]       # A2 kolonu yok: tabanı yüzen düğüm
    b["paneller"] = []
    with pytest.raises(mo.MatrisHatasi, match="yüzen düğüm"):
        coz(b)
    b = portal(H=5.0, capraz="normal")                              # X kesişim düğümünde dört yarım çubuk mafsallı → düzlem dışı mekanizma
    b["dugumler"] = [{"no": 100001, "tur": "kesisim", "a": [R("A", "1", "±0.00"), R("B", "1", "Üst")],
                      "b": [R("B", "1", "±0.00"), R("A", "1", "Üst")]}]
    m = {"i": ["My", "Mz"], "j": ["My", "Mz"]}
    b["cubuklar"] = b["cubuklar"][:3] + [{"no": 4 + k, "i": u, "j": {"dugum": 100001}, "tur": "capraz", "kesit": "CAP", "serbest": m}
                                         for k, u in enumerate((R("A", "1", "±0.00"), R("B", "1", "Üst"), R("B", "1", "±0.00"),
                                                                 R("A", "1", "Üst")))]
    with pytest.raises(mo.MatrisHatasi, match="mekanizma"):
        coz(b)


def test_burulma_zinciri_donme_tutulur():
    """Mafsallı tabanlı kolon + iki ucu mafsallı kirişler: kolon burulması hiçbir yere bağlı değil (yalnız dönme modu) → tutulur, uyarı."""
    b = portal(H=5.0, taban="mafsal", kiris_mafsal=True, capraz="normal")
    v = coz(b).veri
    assert v["ag"]["donme_tutulan"] and any("dönme" in u for u in v["uyarilar"])


# ---------------------------------------------------------------------------
# kesit önerisi
# ---------------------------------------------------------------------------
def test_kesit_onerisi_dc_azaltir():
    b = portal(H=10.0, w=25.0, taban="ankastre", kiris="IPE 160")
    v = coz(b).veri
    assert v["tasarim"]["en_buyuk_dc"] > 1.0
    o = YS.kesit_oner(b, yinele=1)
    oneri = {x["cubuk"]: x for x in o["oneriler"]}
    assert oneri[3]["oneri"].startswith("IPE") and oneri[3]["dc_oneri"] <= 1.0 and oneri[3]["gerekce"]
    assert o["dc_sonra"] < o["dc_once"] and o["dc_sonra"] <= 1.0
    yeni = o["bina"]
    assert yeni["cubuklar"][2]["kesit"] != "KIRIS" and yeni["kesitler"][yeni["cubuklar"][2]["kesit"]]["profil"] == oneri[3]["oneri"]
    assert coz(yeni).veri["tasarim"]["en_buyuk_dc"] <= 1.0


# ---------------------------------------------------------------------------
# şablonlar
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def sablonlar():
    return {ad: coz(yapi.bina_sablon(ad)) for ad in YS.SERBEST_SABLONLAR}


def test_sablon_listesi():
    adlar = [s["ad"] for s in yapi.bina_sablonlar()]
    assert "celik-sanayi-4hol" in adlar and "celik-cbf-3kat" in adlar
    for ad in YS.SERBEST_SABLONLAR:
        b = yapi.bina_sablon(ad)
        assert b["surum"] == 3 and b["cubuklar"] and YS.serbest_mi(b)
        # bütün düğümler aks kesişimi ya da bölme/kesişim düğümü (serbest koordinat yok)
        for d in b.get("dugumler", []):
            assert d.get("tur") in ("bolme", "kesisim") and "X" not in d
        for c in b["cubuklar"]:
            for u in ("i", "j"):
                assert set(c[u]) <= {"aks", "z", "dugum", "sistem"}


@pytest.mark.parametrize("ad", list(YS.SERBEST_SABLONLAR))
def test_sablon_cozulur_makul(sablonlar, ad):
    r = sablonlar[ad]
    v = r.veri
    json.loads(json.dumps(v, ensure_ascii=False))
    assert v["surum"] == 3 and v["model"] == "genel"
    for anahtar in ("bina", "ag", "yukler", "durumlar", "kombinasyonlar", "zarf", "akis", "deprem", "ruzgar", "kar", "tasarim", "uyarilar"):
        assert anahtar in v
    for d, p in v["akis"]["korunum"].items():
        assert yakin(p["kolon_taban"], p["toplam"], 1e-7), (d, p)
    t = v["tasarim"]
    assert all(k["dc"] is not None for k in t["elemanlar"])
    assert t["en_buyuk_dc"] <= 1.0, t["kritik_elemanlar"][:3]
    assert all(s["uygun"] for s in v["deprem"]["katlar"])
    assert v["ruzgar"]["yontem"] == ("panel" if ad == "celik-sanayi-4hol" else "kat")


def test_sanayi_sablonu_ayrintilari(sablonlar):
    v = sablonlar["celik-sanayi-4hol"].veri
    turler = {c["tur"] for c in v["ag"]["cubuklar"]}
    assert {"kolon", "kiris", "asik", "capraz", "kren"} <= turler
    assert v["kren"] and v["kren"]["kopruler"][0]["kren"] == [1, 2]
    assert v["ag"]["diyafram_seviye"]["1"]["mod"] == "esnek"
    assert v["kar"]["paneller"] and all(p["mu"] == pytest.approx(0.8) for p in v["kar"]["paneller"])
    # vute: kesit kartı ve uyarı; çatı paneli sac (kalınlık 0) aşıklara tek doğrultulu
    assert v["kutuphane_ozeti"]["kesitler"]["VUTE"]["tip"] == "vute"
    cati = [p for p in v["ag"]["paneller"] if p["tur"] == "cati"]
    assert cati and all(p["kalinlik"] == 0 and p["dagitim"] == "tek-13" for p in cati)
    # rüzgâr: rüzgâra bakan duvar +0,8, eğimli çatı 1,2 sin α − 0,4
    wp = {p["panel"]: p for p in v["ruzgar"]["paneller"]}
    assert any(p["cp"]["W+X"] == pytest.approx(0.8) for p in wp.values())
    egim = math.degrees(math.atan2(1.75, 10.0))
    assert any(p["cp"]["W+X"] == pytest.approx(1.2 * math.sin(math.radians(egim)) - 0.4) for p in wp.values())


def test_cbf_sablonu_capraz_kosullari(sablonlar):
    v = sablonlar["celik-cbf-3kat"].veri
    cap = [k for k in v["tasarim"]["elemanlar"] if k["tur"] == "capraz"]
    assert cap and all(k["ozet"]["tbdy_capraz"]["suneklik"] == "SDY" for k in cap)
    assert {k["ozet"]["tbdy_capraz"]["duzen"] for k in cap} == {"ters_V", "X"}
    assert any("TBDY" in x["ad"] for k in cap for x in k["kontroller"])
    assert v["ag"]["diyafram_seviye"]["1"]["mod"] == "rijit"
    assert v["tasarim"]["Lb_K_varsayimlari"]


# ---------------------------------------------------------------------------
# aks–kat modeliyle eşdeğerlik (docs/model_ops.js genellestir → surum 3)
# ---------------------------------------------------------------------------
_BETIK = ('const M=require(process.argv[1]);let v="";process.stdin.on("data",d=>v+=d);'
          'process.stdin.on("end",()=>{process.stdout.write(JSON.stringify(M.genellestir(JSON.parse(v)).model))});')


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
@pytest.mark.parametrize("ad", ["betonarme-2kat-3x2", "betonarme-3kat-3x3", "celik-1kat-depo"])
def test_genellestir_esdegerligi(ad):
    b = yapi.bina_sablon(ad)
    for d in ("S", "W", "E"):
        b["yuk_durumlari"][d]["acik"] = True
    b["deprem"]["etkin"] = True
    r = subprocess.run([NODE, "-e", _BETIK, str(PROJE / "docs" / "model_ops.js")], input=json.dumps(b), capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    g = json.loads(r.stdout)
    assert g["surum"] == 3 and g["cubuklar"] and not g.get("kolonlar")
    v1, v2 = coz(b).veri, coz(g).veri
    assert v2["surum"] == 3 and v1["surum"] == 2
    for d in ("G", "Q", "S", "W+X", "W-Y", "EX+", "EY-"):
        t1 = {t["dugum"]: t for t in v1["durumlar"][d]["tepkiler"]}
        t2 = {t["dugum"]: t for t in v2["durumlar"][d]["tepkiler"]}
        assert set(t1) == set(t2)
        for n in t1:
            for a in ("FX", "FY", "FZ", "MX", "MY", "MZ"):
                assert t2[n][a] == pytest.approx(t1[n][a], rel=1e-7, abs=1e-6), (d, n, a)
    kol1 = {c["no"]: c for c in v1["akis"]["kolonlar"]}
    kol2 = {c["kaynak"]["no"]: c for c in v2["akis"]["kolonlar"]}
    assert set(kol1) == set(kol2)
    for n in kol1:
        assert kol2[n]["N_kum_G"] == pytest.approx(kol1[n]["N_kum_G"], rel=1e-8, abs=1e-8)
        assert kol2[n]["N_kum_Q"] == pytest.approx(kol1[n]["N_kum_Q"], rel=1e-8, abs=1e-8)
    for yon in ("X", "Y"):
        assert v2["deprem"][yon]["VtE"] == pytest.approx(v1["deprem"][yon]["VtE"], rel=1e-9)
        assert v2["deprem"][yon]["Tp"] == pytest.approx(v1["deprem"][yon]["Tp"], rel=1e-9)
    assert v2["deprem"]["m_t"] == pytest.approx(v1["deprem"]["m_t"], rel=1e-9)
    assert v2["yukler"]["toplam"] == pytest.approx(v1["yukler"]["toplam"])


def test_aks_kat_bina_genel_motorla_dogrudan():
    """surum 1 bina doğrudan yapi_serbest ile de çözülür (Python dönüştürücü, genellestir kuralı)."""
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    v1 = coz(b).veri
    v2 = YS.bina_coz(b, goster="yok", anlat=False).veri
    t1 = {t["dugum"]: t["FZ"] for t in v1["durumlar"]["G"]["tepkiler"]}
    t2 = {t["dugum"]: t["FZ"] for t in v2["durumlar"]["G"]["tepkiler"]}
    assert t2 == pytest.approx(t1)


# ---------------------------------------------------------------------------
# anlatım ve köprü
# ---------------------------------------------------------------------------
def test_anlatim_ve_program_adi_yok():
    r = coz(egik_cati(25.0), anlat=True)
    metin = " ".join(str(i) for _, i, _ in r.anlatim.bloklar)
    assert "açıortay" in metin and "TS 500" in metin


@pytest.fixture(scope="module")
def kopru():
    ozellik = importlib.util.spec_from_file_location("web_kopru_serbest_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def iste(kopru, islem, girdi):
    return json.loads(kopru.calistir(json.dumps({"islem": islem, "girdi": girdi})))


def test_kopru_genel_model(kopru):
    assert "bina_kesit_oner" in kopru.BINA_ISLEMLER
    b = portal(H=10.0, w=25.0, taban="ankastre", kiris="IPE 160")
    y = iste(kopru, "bina_coz", {"bina": b})
    assert y["hata"] is None and y["veri"]["surum"] == 3
    kim = y["veri"]["cozum_kimligi"]
    z = iste(kopru, "bina_eleman_tasarim", {"cozum_kimligi": kim, "tur": "cubuk", "no": 3})
    assert z["hata"] is None and z["sonuc"]["cubuk"] == 3 and z["bloklar"]
    z = iste(kopru, "bina_kesit_oner", {"cozum_kimligi": kim, "hedef": [{"tur": "cubuk", "no": 3}], "yinele": 0})
    assert z["hata"] is None and z["oneriler"][0]["oneri"] and z["bina"] is None
    z = iste(kopru, "bina_kesit_oner", {"bina": b, "hedef": "hepsi", "yinele": 2})
    assert z["hata"] is None and z["dc_sonra"] <= 1.0 and z["bina"]["surum"] == 3
    z = iste(kopru, "bina_kesit_oner", {"hedef": "hepsi"})
    assert z["hata"] and "kimliği" in z["hata"]
