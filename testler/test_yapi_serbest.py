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


@pytest.mark.parametrize("ad, cubuklar", [("celik-cbf-3kat", [55, 94]), ("betonarme-4kat-radye", None)])
def test_kesit_onerisi_kendi_tahkikinde_yeterli(ad, cubuklar):
    """Önerilen kesit, kaydın bütün kurallarıyla (aynı iç kuvvetler) D/C ≤ 1 vermeli. Eskiden: cbf döşemeli çaprazlı kirişe
    IPE 100 (tarama yalnız pozitif moment bölgesinin L_b = 0'ıyla; negatif bölgede D/C 1,80) ve radye kirişine 30x30 (öneri
    40 mm, tahkik pas + 20 = 50 mm donatı derinliğiyle: D/C 99) önerilirdi."""
    b = yapi.bina_sablon(ad)
    hedef = "hepsi" if cubuklar is None else [{"tur": "cubuk", "no": n} for n in cubuklar]
    o = YS.kesit_oner(b, hedef=hedef)
    for x in o["oneriler"]:
        if x.get("oneri"):
            assert x["dc_oneri"] is not None and x["dc_oneri"] <= 1.0 + 1e-9, (x["cubuk"], x["oneri"], x["dc_oneri"])
    if cubuklar:
        for x in o["oneriler"]:
            assert x["oneri"] != "IPE 100" and x["durum"].startswith("doğrulandı") and "IPE 100" in x["gerekce"][-1]


def _rc_30(boy=0.30):
    """betonarme-3kat-3x3 genel motorla (surum 3), bütün kolonlar boy × boy (ρ verilmez: 0,01)."""
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["surum"] = 3
    b["kesitler"]["S45x45"].update({"b": boy, "h": boy})
    return b


def test_kesit_onerisi_yalniz_donati_degisimi():
    """K1 'donatı': b × h yeterli ama gerekli ρ > mevcut ρ → uygula {ad 'B30x30-ρ%2.00', tanım = mevcut kart + donati_orani}
    (null değil). Eskiden degisim 'aynı', uygula None: 'Mevcut 300 × 300 mm: ρ = 0.02 ile yeterli' denip uygulanamazdı."""
    b = _rc_30()
    o = YS.kesit_oner(b, hedef=[{"tur": "cubuk", "no": 1}])
    x = o["oneriler"][0]
    assert x["kesit"] == "S45x45" and x["oneri"] == "30x30" and x["degisim"] == "donatı"
    assert x["dc_once"] > 1.0 and x["dc_oneri"] <= 1.0 and x["rho_once"] == pytest.approx(0.01)
    assert x["donati_orani"] >= 0.02 - 1e-9 and any("yalnız boyuna donatıda" in g for g in x["gerekce"])
    u = x["uygula"]
    assert u is not None and u["yeni"] and u["ad"] == f"B30x30-ρ%{x['donati_orani'] * 100:.2f}"
    eski = b["kesitler"]["S45x45"]
    assert u["tanim"] == dict(eski, donati_orani=x["donati_orani"])          # mevcut kart + donati_orani
    assert "mevcut iç kuvvetlerle tahmin" in o["aciklama"]
    # uygulanınca aynı kolon için yeniden öneri: ρ zaten yeterli → değişiklik yok (sonsuz döngü yok)
    b2 = copy.deepcopy(b)
    b2["kesitler"][u["ad"]] = u["tanim"]
    next(k for k in b2["kolonlar"] if k["no"] == 1)["kesit"] = u["ad"]
    x2 = YS.kesit_oner(b2, hedef=[{"tur": "cubuk", "no": 1}])["oneriler"][0]
    assert x2["kesit"] == u["ad"] and x2["rho_once"] == pytest.approx(x["donati_orani"])
    if x2["dc_once"] <= 1.0:
        assert x2["degisim"] in ("aynı", "küçült") and (x2["degisim"] != "aynı" or x2["uygula"] is None)
    # As verilmiş kart: donatı değişiminde As düşer (ρ yeni toplam donatıyı tanımlar)
    b3 = _rc_30()
    b3["kesitler"]["S45x45"]["As"] = 9.0                          # ρ = 0,01
    x3 = YS.kesit_oner(b3, hedef=[{"tur": "cubuk", "no": 1}])["oneriler"][0]
    assert x3["degisim"] == "donatı" and "As" not in x3["uygula"]["tanim"] and x3["uygula"]["tanim"]["donati_orani"] >= 0.02 - 1e-9


def test_kesit_onerisi_yinele_yakinsar_ve_rho_grubu():
    """K1 'Hepsini uygula' (yinele 3): ρ-only değişiklik de uygulanır, onarım turunda grup küçülmez, son çözüm D/C ≤ 1. Eskiden
    bütün kolonlar 'aynı' (uygula yok) kalır, kirişler küçülür ve D/C 1,65 → 1,85 olurdu."""
    o = YS.kesit_oner(_rc_30(), yinele=3)
    assert o["dc_once"] > 1.6 and o["dc_sonra"] <= 1.0
    assert not any("yakınsamadı" in u for u in o["uyarilar"])
    t0 = o["turlar"][0]
    kolon = next(d for d in t0["degisen"] if d["kesit"] == "S45x45")
    assert kolon["yeni"].startswith("B30x30-ρ%") and kolon["donati_orani"] >= 0.02 - 1e-9 and len(kolon["cubuklar"]) == 27
    for t in o["turlar"][1:]:                                     # onarım turları: yalnız büyüt / donatı, küçültme yok
        assert all(d["degisim"] in ("büyüt", "donatı") for d in t.get("degisen") or [])
    assert o["turlar"][-1]["asan"] == 0
    son = coz(o["bina"]).veri
    assert son["tasarim"]["en_buyuk_dc"] == pytest.approx(o["dc_sonra"], abs=1e-4)
    # öneriler (0. tur kirişleri küçültür) göreli kat ötelemesini yeni aşan katlar doğurursa yanıt bunu söyler: 'yakınsadı' (D/C ≤ 1)
    # ötelemeyi kapsamaz (eskiden uyarısızdı)
    asan = lambda v: {y: {k["kat"] for k in v["deprem"]["katlar"] if k.get(f"uygun_{y}") is False} for y in "xy"}  # noqa: E731
    a0, a1 = asan(coz(_rc_30()).veri), asan(son)
    yeni = {y: sorted(a1[y] - a0[y]) for y in "xy" if a1[y] - a0[y]}
    u = [x for x in o["uyarilar"] if "göreli kat ötelemesi" in x]
    assert yeni and len(u) == 1 and "(öneriden önce bu katlarda sağlanıyordu)" in u[0]
    assert all(f"{y.upper()} yönü kat {', '.join(map(str, k))}" in u[0] for y, k in yeni.items())


def test_oteleme_uyarisi():
    """_oteleme_uyarisi: yalnız YENİ aşan katlar; önce bilinmiyorsa son çözümde aşan bütün katlar; aşan yoksa None."""
    assert YS._oteleme_uyarisi({"x": [2], "y": []}, {"x": [2], "y": []}) is None
    assert YS._oteleme_uyarisi({"x": [], "y": []}, None) is None
    u = YS._oteleme_uyarisi({"x": [2], "y": []}, {"x": [1, 2, 3], "y": [3]})
    assert u.startswith("Önerilen kesitlerle göreli kat ötelemesi sınırı (TBDY 2018 md. 4.9.1) aşılıyor: X yönü kat 1, 3; Y yönü kat 3 "
                        "(öneriden önce bu katlarda sağlanıyordu).")
    u = YS._oteleme_uyarisi(None, {"x": [1], "y": []})
    assert "aşılıyor: X yönü kat 1. Öneriler yalnız eleman D/C'sine göre" in u and "sağlanıyordu" not in u
    assert YS._oteleme_asan(None) == {"x": [], "y": []}
    assert YS._oteleme_asan({"katlar": [{"kat": 1, "uygun_x": True, "uygun_y": False}, {"kat": 2, "uygun_x": False}]}) == {"x": [2], "y": [1]}


def test_kesit_onerisi_yakinsamazsa_uyari():
    """yinele turları yetmezse (son çözümde D/C > 1) yanıt açık bir uyarı taşır: '… 1 turda yakınsamadı: Ç12 (1,07), …'."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["surum"] = 3
    b["kesitler"]["S40x40"].update({"b": 0.25, "h": 0.25})
    o = YS.kesit_oner(b, yinele=1)
    assert o["dc_sonra"] > 1.0
    u = [x for x in o["uyarilar"] if "turda yakınsamadı" in x]
    assert len(u) == 1 and u[0].startswith("Kesit önerileri 1 turda yakınsamadı: ") and "D/C > 1" in u[0]
    asan = [k for k in coz(o["bina"]).veri["tasarim"]["elemanlar"] if k["dc"] > 1.0]
    # aks–kat kaynaklı çubuk kullanıcının gördüğü adla (kolon 7), öteki çubuklar Ç{no}
    ad = lambda k: f"kolon {k['kaynak']['no']} (" if (k.get("kaynak") or {}).get("aks_kat") == "kolon" else f"Ç{k['cubuk']} ("  # noqa: E731
    assert asan and all(ad(k) in u[0] for k in asan[:8]) and "(1,1" in u[0]
    el = [{"cubuk": 12, "dc": 1.0712, "kaynak": None}, {"cubuk": 3, "dc": 0.5}, {"cubuk": 9, "dc": 1.2, "kaynak": {"aks_kat": "kiris", "no": 4}}]
    assert YS._yakinsamadi_uyarisi(el, 2).startswith("Kesit önerileri 2 turda yakınsamadı: kiriş 4 (1,2), Ç12 (1,07) — ")
    # hiç tur uygulanamadıysa nedeni de yazılır ("0 turda" tek başına yanıltıcıydı)
    assert YS._yakinsamadi_uyarisi(el, 0).startswith("Kesit önerileri 0 turda yakınsamadı (uygulanabilir kesit değişikliği bulunamadı): kiriş 4")
    o3 = YS.kesit_oner(b, yinele=3)                                # üç turla yakınsar
    assert o3["dc_sonra"] <= 1.0 and not any("yakınsamadı" in x for x in o3["uyarilar"])


def test_kesit_onerisi_kolon_ndm_deprem_yokken_g_q():
    """Deprem birleşimi yokken kolon önerisinin TBDY 7.3.1.2 satırı, kaydın 'Ndm ≤ 0,40 fck Ac' satırıyla aynı N_dm'i (G + Q)
    kullanır; eskiden 'A_c ≥ N_dm/(0,40 f_ck) = 0·10³/(0,40·30) = 0 cm²' yazardı (motor-tuketici-new-5)."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["surum"] = 3
    r = coz(b)
    k1 = next(k for k in r.veri["tasarim"]["elemanlar"] if k["cubuk"] == 1)
    import tasarim
    kont = YS._ba_kontroller(tasarim, *_ba_girdisi(r.ic["tasarim"], r.ic["B"].cubuk_no[1])[:6], 152.0, cikti=(cik := {}))
    assert cik == {"Ndm": 152.0, "N040": pytest.approx(0.4 * 30 * 0.16 * 1000), "kombinasyon": "G+Q", "kaynak": "G+Q"}
    assert next(x for x in kont if x["ad"] == "TBDY: Ndm ≤ 0,40 fck Ac")["talep"] == 152.0
    Ndm = k1["ozet"]["Ndm_kN"]
    assert Ndm > 100 and k1["ozet"]["N_sinir_TBDY_kN"] == pytest.approx(0.4 * 30 * 0.16 * 1000)
    x = YS.kesit_oner(b, hedef=[{"tur": "cubuk", "no": 1}])["oneriler"][0]
    tbdy = next(g for g in x["gerekce"] if g.startswith("TBDY 2018 md. 7.3.1.2"))
    assert f"= {Ndm:.1f}·10³/(0,40·30)" in tbdy and "deprem birleşimi yok: N_dm ≈ G + Q" in tbdy and "= 0 cm²" not in tbdy
    # deprem varken satır deprem birleşimlerinden (değişmedi)
    b3 = yapi.bina_sablon("betonarme-3kat-3x3")
    b3["surum"] = 3
    x3 = YS.kesit_oner(b3, hedef=[{"tur": "cubuk", "no": 1}])["oneriler"][0]
    assert any("(N_dm = deprem birleşimlerindeki en büyük eksenel basınç)" in g for g in x3["gerekce"])


def test_oneri_uygula_onarim_turunda_kucultmez():
    """_oneri_uygula(kucultme=False): çelikte 'küçült' grubu atlanır; betonarme kolon grubunda b × h mevcut boyuttan küçülmez,
    ρ azalmaz (atlama yalnız b, h ve ρ aynıysa)."""
    bina = {"kesitler": {"P": {"tip": "profil", "profil": "IPE 300", "malzeme": "S275"},
                         "K": {"tip": "dikdortgen", "b": 0.4, "h": 0.4, "malzeme": "C30", "donati_orani": 0.02}},
            "cubuklar": [{"no": 1, "kesit": "P"}, {"no": 2, "kesit": "K"}, {"no": 3, "kesit": "K"}]}
    B = type("B", (), {"cubuklar": []})()
    celik = {"cubuk": 1, "kesit": "P", "tur": "kiris", "sistem": "celik", "oneri": "IPE 270", "malzeme": "S275", "degisim": "küçült",
             "agirlik_kg_m": 36.1}
    ba = [{"cubuk": n, "kesit": "K", "tur": "kolon", "sistem": "betonarme", "oneri": "30x30", "b": 0.3, "h": 0.3, "b_once": 0.4,
           "h_once": 0.4, "malzeme": "C30", "degisim": "küçült", "donati_orani": 0.015} for n in (2, 3)]
    yeni, degisen = YS._oneri_uygula(bina, [celik] + ba, B, kucultme=False)
    assert degisen == [] and yeni["cubuklar"] == bina["cubuklar"]
    yeni, degisen = YS._oneri_uygula(bina, [celik] + ba, B, kucultme=True)      # 0. tur: ekonomi (küçültme serbest)
    assert {d["kesit"]: d["yeni"] for d in degisen} == {"P": "IPE270", "K": "B30x30-ρ%1.50"}
    # aynı b × h, daha çok ρ isteyen üye: onarım turunda 'donatı' değişimi, mevcut kart + donati_orani
    ba2 = [dict(ba[0], b=0.4, h=0.4, oneri="40x40", degisim="aynı", donati_orani=0.025)]
    yeni, degisen = YS._oneri_uygula(bina, ba2, B, kucultme=False)
    assert degisen[0]["degisim"] == "donatı" and degisen[0]["yeni"] == "B40x40-ρ%2.50"
    assert yeni["kesitler"]["B40x40-ρ%2.50"] == dict(bina["kesitler"]["K"], donati_orani=0.025)


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


@pytest.mark.parametrize("ad", list(YS.SERBEST_SABLONLAR))
def test_akis_sankey_g_q_s(sablonlar, ad):
    """AKIS-QS: panel → çubuk bantları her düşey yük durumunda (G, Q, kar varsa S); bir çubuğa gelen bantların toplamı
    veri.yukler.cubuklar[].<durum>.panel ile, durum toplamı korunum 'paneller' (dağıtılan) ile aynı. Eskiden yalnız G vardı."""
    v = sablonlar[ad].veri
    sk = v["akis"]["sankey"]
    durumlar = {e["durum"] for e in sk}
    assert durumlar == {"G", "Q", "S"} if v["kar"] else {"G", "Q"}
    assert all(e["kaynak"].startswith("P") and e["hedef"].startswith("Ç") and e["kN"] > 0 for e in sk)
    yuk = {y["no"]: y for y in v["yukler"]["cubuklar"]}
    for d in durumlar:
        pay = {}
        for e in sk:
            if e["durum"] == d:
                pay[int(e["hedef"][1:])] = pay.get(int(e["hedef"][1:]), 0.0) + e["kN"]
        for no, kN in pay.items():
            assert kN == pytest.approx((yuk[no].get(d) or {}).get("panel", 0.0), rel=1e-4, abs=1e-3), (d, no)
        dagitilan = sum(p[f"{d}_toplam"] for p in v["yukler"]["paneller"] if p.get("dagitim") != "yok")
        assert sum(pay.values()) == pytest.approx(dagitilan, rel=1e-4) and dagitilan > 0
    if ad == "celik-cbf-3kat":
        assert sorted((e["kaynak"], e["durum"], round(e["kN"], 2)) for e in sk if e["hedef"] == "Ç97") == [
            ("P13", "G", 40.5), ("P13", "Q", 18.0), ("P13", "S", 5.4), ("P14", "G", 40.5), ("P14", "Q", 18.0), ("P14", "S", 5.4)]


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
    # tasarım: eleman başına D/C aks–kat motoruyla aynı (betonarme kolonda öz ağırlık çubuk boyunca yayılı → üst uçta N biraz farklı)
    tol = 0.05 if ad == "betonarme-2kat-3x2" else 0.20
    t1 = {(k["tur"], k["no"]): k for k in v1["tasarim"]["elemanlar"]}
    for k in v2["tasarim"]["elemanlar"]:
        k1 = t1[(k["kaynak"]["aks_kat"], k["kaynak"]["no"])]
        assert k["dc"] == pytest.approx(k1["dc"], rel=tol), (k["cubuk"], k["kaynak"], k1["dc"], k["dc"], k1["belirleyen"], k["belirleyen"])
        assert k["belirleyen"]["kombinasyon"] is not None, k
        bas = k["kontroller"][0]                       # D/C'yi belirleyen satır başta; sağlanan bir koşul satırı olamaz
        assert bas["dc"] == pytest.approx(k["dc"]) and not (bas.get("kosul") and bas["saglandi"]), (k["cubuk"], bas)


def test_betonarme_dc_kosul_satirlari():
    """surum 3'te betonarme kolon D/C'si yönetmelik koşul satırlarından (ρ ≥ 0,01, etriye aralığı, boyut) gelmez; aks–kat ile aynı."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    v1 = coz(b).veri
    b3 = copy.deepcopy(b)
    b3["surum"] = 3
    v3 = coz(b3).veri
    assert v3["model"] == "genel"
    t1 = {(k["tur"], k["no"]): k["dc"] for k in v1["tasarim"]["elemanlar"]}
    kolon1 = next(k for k in v3["tasarim"]["elemanlar"] if k["kaynak"] == {"aks_kat": "kolon", "no": 1})
    assert kolon1["dc"] == pytest.approx(t1[("kolon", 1)], rel=0.03) and kolon1["dc"] < 0.5          # eskiden 1,0 (ρ satırı)
    assert kolon1["belirleyen"] == {"kontrol": "N–M", "kombinasyon": "1.4G+1.6Q"}
    for k in v3["tasarim"]["elemanlar"]:
        etkin = [x for x in k["kontroller"] if not (x.get("kosul") and x["saglandi"])]      # sağlanan koşul D/C'ye girmez
        assert max(x["dc"] for x in etkin) == pytest.approx(k["dc"])
        rho = [x for x in k["kontroller"] if "ρ ≥ 0,01" in x["ad"] or "aralığı" in x["ad"]]
        assert all(x.get("kosul") for x in rho), rho
    # deprem: kolonlarda TBDY N_dm ≤ 0,40 f_ck A_c (dayanım) ve en küçük boyut ≥ 300 mm (koşul) satırları
    b3 = yapi.bina_sablon("betonarme-3kat-3x3")
    b3["surum"] = 3
    r = coz(b3)
    import tasarim
    kont = YS._ba_kontroller(tasarim, *_ba_girdisi(r.ic["tasarim"], r.ic["B"].cubuk_no[1]))
    ndm = [x for x in kont if x["ad"] == "TBDY: Ndm ≤ 0,40 fck Ac"]
    assert len(ndm) == 1 and not ndm[0]["kosul"] and ndm[0]["kombinasyon"]
    assert any("en küçük boyutu ≥ 300" in x["ad"] and x["kosul"] for x in kont)


def test_betonarme_kolon_donati_kurali_aks_kat_ile_ayni():
    """Kolon D/C'si iki motorda aynı donatıyla: kesitte donati_orani / As verilmişse o, yoksa ρ = 0,01 (gerekli ρ özette); eskiden
    genel motor ρ'yu 0,04'e kadar tarayıp yetersiz kolonu 'yeterli' gösterirdi (aks–kat: 'donatı artır')."""
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["kesitler"]["S30x30"] = {"tip": "dikdortgen", "b": 0.3, "h": 0.3, "malzeme": "C30", "donati": "B420C", "pas": 0.03}
    for k in b["kolonlar"]:
        k["kesit"] = "S30x30"
    for rho in (None, 0.03):
        x = copy.deepcopy(b)
        if rho:
            x["kesitler"]["S30x30"]["donati_orani"] = rho
        v1 = coz(copy.deepcopy(x)).veri
        x["surum"] = 3
        v3 = coz(x).veri
        t1 = {(k["tur"], k["no"]): k for k in v1["tasarim"]["elemanlar"]}
        kol = [(k, t1[(k["kaynak"]["aks_kat"], k["kaynak"]["no"])]) for k in v3["tasarim"]["elemanlar"] if k["tur"] == "kolon"]
        assert [k["durum"] for k, _ in kol] == [k1["durum"] for _, k1 in kol]
        assert [k["dc"] > 1.0 for k, _ in kol] == [k1["dc"] > 1.0 for _, k1 in kol]
        if rho is None:
            assert sum(k["durum"] == "donatı artır" for k, _ in kol) >= 20                # ρ = 0,01 yetmiyor
            assert all(k["ozet"]["rho_varsayim"] and k["ozet"]["rho"] == pytest.approx(0.01) for k, _ in kol)
            assert all(k["ozet"]["rho_gerekli"] >= 0.01 for k, _ in kol if k["ozet"]["rho_gerekli"] is not None)
        else:
            assert all(k["dc"] == pytest.approx(k1["dc"], rel=0.03) for k, k1 in kol)
            assert all(not k["ozet"]["rho_varsayim"] and k["ozet"]["rho"] == pytest.approx(rho) for k, _ in kol)


def _ba_girdisi(T, c):
    """_ba_kontroller girdileri (test): _cubuk_tasarla'nın betonarme dalını yeniden kurmadan T.sonuclar'dan."""
    import tasarim
    YS._cubuk_tasarla(tasarim, T, c)
    s = T.sonuclar[c["no"]]
    ks = T.B.kesitler[c["kesit"]]
    kuv = s["bilgi"]["kuvvetler"]
    ad_komb = {x["ad"]: x["ad"].rsplit(" (", 1)[0] for x in kuv}
    return s["r"], kuv, ad_komb, "kolon", ks, T.B.malzemeler[ks["malzeme"]], None


def test_belirleyen_satir_basta_ve_kisaltmada_korunur():
    r = coz(yapi.bina_sablon("celik-sanayi-4hol"))
    v = r.veri
    assert v["ozet"].get("tasarim_kisaltildi")                  # büyük model: yanıtta 3 satır
    for k in v["tasarim"]["elemanlar"]:
        assert len(k["kontroller"]) <= 3
        bas = k["kontroller"][0]
        assert bas["dc"] == pytest.approx(k["dc"]) and not (bas.get("kosul") and bas["saglandi"]), (k["cubuk"], bas)
    tam = r.ic["tas_tam"]                                       # rapor için kısaltılmamış satırlar
    assert any(len(k["kontroller"]) > 3 for k in tam["elemanlar"])
    assert [k["dc"] for k in tam["elemanlar"]] == [k["dc"] for k in v["tasarim"]["elemanlar"]]


# ---------------------------------------------------------------------------
# tek yönlendirme kuralı (C1), temel tipi, akış kayıtları, otomatik mesnetler, diyafram, panel ek yükü, balkon, anlatım
# ---------------------------------------------------------------------------
def test_yonlendirme_dogruluk_tablosu():
    """yapi._serbest_mi = yapi_serbest.serbest_mi (arayüz s3Var ile aynı tablo)."""
    def b(**ek):
        x = yapi.bina_sablon("betonarme-2kat-3x2")
        x.update(ek)
        return x
    tablo = [
        (b(), False),
        (b(mesnetler=[{"dugum": {"aks": ["B", "2"], "z": "+3.00"}, "ux": True, "uy": True, "uz": True}]), True),
        (b(dugumler=[{"no": 100001, "X": 0, "Y": 0, "Z": 3}]), True),
        (b(uretecler=[{"no": 1, "tur": "makas", "parametreler": {}}]), True),
        (b(ek_yukler=[{"tur": "dugum", "aks": ["B", "2"], "kat": 1, "durum": "G", "FZ": -10}]), False),
        (b(ek_yukler=[{"tur": "dugum", "dugum": {"aks": ["B", "2"], "z": "+3.00"}, "durum": "G", "FZ": -10}]), True),
        (b(ek_yukler=[{"tur": "cubuk", "cubuk": 1, "durum": "G", "q": -1}]), True),
        (b(surum=3), True),
        (yapi.bina_sablon("celik-cbf-3kat"), True),
        (b(cubuklar=[], mesnetler=[]), False),
        # K2 ek satırları (bina_cizim.js genelMi, bina.js s3Var/binaYukle ile aynı): tür büyük/küçük harf ve boşluk duyarsız;
        # surum: sayı ya da tamsayı/ondalık dizesi → tam kısmı, başka her şey → 1 (eskiden "3.0" aks–kat sayılırdı)
        (b(ek_yukler=[{"tur": "Cubuk", "cubuk": 1, "durum": "G", "q": -1}]), True),
        (b(ek_yukler=[{"tur": " panel", "panel": 1, "durum": "G", "p": -1}]), True),
        (b(ek_yukler=[{"tur": "PANEL", "panel": 1, "durum": "G", "p": -1}]), True),
        (b(ek_yukler=[{"tur": "\ufeffpanel\u3000", "panel": 1, "durum": "G", "p": -1}]), True),       # JS trim() kümesi
        (b(ek_yukler=[{"tur": "\x1cpanel", "panel": 1, "durum": "G", "p": -1}]), False),
        (b(surum="3.0"), True),
        (b(surum="3.5"), True),
        (b(surum=" 3 "), True),
        (b(surum="3a"), False),
        (b(surum="0x3"), False),
        (b(surum="1e1"), False),
        (b(surum=2.9), False),
        (b(surum=3.7), True),
        (b(surum=True), False),
        (b(surum=None), False),
    ]
    for bina, beklenen in tablo:
        assert yapi._serbest_mi(bina) is beklenen and YS.serbest_mi(bina) is beklenen, bina.get("ek_yukler") or bina.get("surum")
        assert yapi._serbest_mi(json.dumps(bina)) is beklenen
    assert [yapi._surum_sayi(x) for x in (float("inf"), float("nan"), "+3", "-3", "3.", "", [3], 0)] == [1, 1, 3, -3, 1, 1, 1, 0]
    # JS ile aynı uç durumlar (eskiden OverflowError): float'a sığmayan tamsayı (JSON'u JS Infinity okur → 1), çok uzun rakam dizisi
    # (JS Math.trunc(parseFloat) = ±Infinity); boşluk kümesi JS \s (\ufeff var, \x1c ve \x85 yok)
    assert [yapi._surum_sayi(x) for x in (10 ** 400, "1" * 400, "-" + "9" * 400, "\ufeff3", "\u00a03\u3000", "\x1c3", "\x853")] == [
        1, math.inf, -math.inf, 3, 3, 1, 1]
    assert yapi._serbest_mi({"surum": "1" * 400}) is True and yapi._serbest_mi({"surum": 10 ** 400}) is False
    # aks–kat modeline açık mesnet: genel motora gider ve mesnet hesaba girer (eskiden sessizce yok sayılırdı)
    x = b(mesnetler=[{"dugum": {"aks": ["B", "2"], "kat": 1}, "uz": True}])
    v = coz(x).veri
    assert v["model"] == "genel" and v["akis"]["mesnetler"] and v["akis"]["mesnetler"][0]["adres"].startswith("B2/")


@pytest.mark.parametrize("ad", list(YS.SERBEST_SABLONLAR))
def test_cozum_kimligi_cozmeden(ad):
    b = yapi.bina_sablon(ad)
    assert yapi.cozum_kimligi(b) == coz(b).veri["cozum_kimligi"] == yapi.cozum_kimligi(json.dumps(b))
    b2 = yapi.bina_sablon("betonarme-2kat-3x2")
    assert yapi.cozum_kimligi(b2) == coz(b2).veri["cozum_kimligi"]


def test_mutemadi_radye_genel_model_hatalari():
    """Mütemadi / radye genel modelde çözülür (eskiden 'henüz çözülmüyor'); kalan öğretici hatalar (C11)."""
    b = yapi.bina_sablon("celik-cbf-3kat")
    b["temeller"]["tip"] = "kazik"
    with pytest.raises(mo.MatrisHatasi, match="tanımsız"):
        coz(b)
    # ek aks sistemindeki taban (GLOBAL ızgaranın dışında): mütemadi temelde öğretici hata
    b = kutu_bina(0.0, deprem=False)
    b["aks_sistemleri"] = [{"ad": "R", "tur": "kartezyen", "orijin": [3, 3, 0], "aci": 30, "x": [{"ad": "P", "konum": 0}],
                            "y": [{"ad": "Q", "konum": 0}]}]
    b["cubuklar"] += [{"no": 20, "i": {"sistem": "R", "aks": ["P", "Q"], "z": "±0.00"}, "j": {"sistem": "R", "aks": ["P", "Q"], "z": "Çatı"},
                       "tur": "kolon", "kesit": "K"},
                      {"no": 21, "i": {"sistem": "R", "aks": ["P", "Q"], "z": "Çatı"}, "j": R("A", "1", "Çatı"), "tur": "kiris", "kesit": "B"}]
    b["temeller"] = {"tip": "surekli", "surekli": {"yon": "xy", "B": 1.0, "tasma": 0.5}}
    with pytest.raises(mo.MatrisHatasi, match="GLOBAL X/Y aks kesişiminde değil") as h:
        coz(copy.deepcopy(b))
    assert str(h.value).startswith("Mütemadi temel: taban düğümü") and "R:PQ/±0.00" in str(h.value)
    # açık mesnet temel ağının üzerinde (A1 temel kotunda)
    b["temeller"] = {"tip": "radye", "radye": {"h": 0.5, "tasma": 0.5}}
    b["mesnetler"] = [{"dugum": R("A", "1", "±0.00"), "ux": True, "uy": True, "uz": True}]
    with pytest.raises(mo.MatrisHatasi, match=r"açık mesnetli \('mesnetler'\) ve radye ağının üzerinde"):
        coz(copy.deepcopy(b))
    # aks–kat modeline (genel motor) üst katta açık mesnet: artık radyeyle çözülür
    b = yapi.bina_sablon("betonarme-4kat-radye")
    b["mesnetler"] = [{"dugum": {"aks": ["A", "1"], "kat": 1}, "uz": True}]
    v = coz(b).veri
    assert v["model"] == "genel" and v["temel"]["tip"] == "radye" and v["bina"]["temeller"]["tip"] == "radye"
    assert len(v["akis"]["mesnetler"]) == 1 and v["akis"]["temeller"] == []


def test_akis_temel_ve_acik_mesnet_kayitlari():
    b = yapi.bina_sablon("celik-cbf-3kat")
    v0 = coz(copy.deepcopy(b)).veri
    assert v0["akis"]["mesnetler"] == []
    assert v0["akis"]["temeller"] and all(t["B"] and t["L"] and t["h"] and t["N_temel"] > 0 and t["aks"] for t in v0["akis"]["temeller"])
    t = v0["akis"]["temeller"][0]
    assert t["N_temel"] == pytest.approx(yapi.GAMMA_BA * t["B"] * t["L"] * t["h"])
    assert t["N_servis"] == pytest.approx(t["N_G"] + t["N_Q"] + t["N_temel"])
    b["mesnetler"] = [{"dugum": {"aks": ["B", "2"], "z": "±0.00"}, "ux": True, "uy": True, "uz": True}]
    v = coz(b).veri
    assert len(v["akis"]["temeller"]) == len(v0["akis"]["temeller"]) - 1
    assert all(x.get("B") and x.get("L") and x.get("N_temel") for x in v["akis"]["temeller"])
    m = v["akis"]["mesnetler"]
    assert len(m) == 1 and set(m[0]) == {"dugum", "adres", "tip", "N_G", "N_Q", "MX", "MY"} and m[0]["adres"] == "B2/±0.00"
    assert m[0]["N_G"] > 0 and m[0]["tip"] == "mafsal"
    assert [x["dugum"] for x in v["bina"]["temeller"]["liste"]] == [x["dugum"] for x in v["akis"]["temeller"]]
    assert m[0]["dugum"] not in [x["dugum"] for x in v["bina"]["temeller"]["liste"]]


def test_ek_aks_sistemi_kolon_tabanlari_mesnetli():
    """30° dönük ek aks sisteminin kesişimlerindeki kolon tabanları temele oturur (C3); bölme düğümü oturmaz."""
    b = kutu_bina(0.0, deprem=False)
    b["aks_sistemleri"] = [{"ad": "KANAT", "tur": "kartezyen", "orijin": [12, 0, 0], "aci": 30,
                            "x": [{"ad": "P", "konum": 0}, {"ad": "R", "konum": 5}], "y": [{"ad": "1", "konum": 0}, {"ad": "2", "konum": 4}],
                            "z": None}]
    K = lambda a, z: {"sistem": "KANAT", "aks": a, "z": z}  # noqa: E731
    n = max(c["no"] for c in b["cubuklar"])
    for a in (["P", "1"], ["R", "1"], ["R", "2"], ["P", "2"]):
        n += 1
        b["cubuklar"].append({"no": n, "i": K(a, "±0.00"), "j": K(a, "Çatı"), "tur": "kolon", "kesit": "K"})
    for a, c_ in ((["P", "1"], ["R", "1"]), (["R", "1"], ["R", "2"]), (["R", "2"], ["P", "2"]), (["P", "2"], ["P", "1"])):
        n += 1
        b["cubuklar"].append({"no": n, "i": K(a, "Çatı"), "j": K(c_, "Çatı"), "tur": "kiris", "kesit": "B"})
    b["temeller"]["ozel"] = [{"sistem": "KANAT", "aks": ["R", "2"], "B": 2.5, "L": 2.5}, {"aks": ["A", "1"], "B": 2.2, "L": 2.2}]
    v = coz(b).veri                                              # eskiden: 'Yapı mekanizma'
    tem = v["akis"]["temeller"]
    assert len(tem) == 8
    kanat = [t for t in tem if t.get("sistem") == "KANAT"]
    assert len(kanat) == 4 and next(t for t in kanat if t["aks"] == ["R", "2"])["B"] == 2.5
    assert next(t for t in tem if t["aks"] == ["A", "1"] and not t.get("sistem"))["B"] == 2.2
    assert all(abs(p["kolon_taban"] - p["toplam"]) < 1e-6 * max(1.0, p["toplam"]) for p in v["akis"]["korunum"].values())
    # bölme düğümü taban kotunda olsa da otomatik mesnet almaz
    B = YS._oku(b)
    assert all(B.coz.dugum[n_]["tur"] == "aks" for n_, m in B.mesnetler.items() if m["kaynak"] == "temel")


def test_rijit_diyafram_seviyesinde_acik_mesnet():
    b = yapi.bina_sablon("celik-cbf-3kat")
    b["mesnetler"] = [{"dugum": {"aks": ["A", "1"], "z": "+3.50"}, "uy": True}]
    with pytest.raises(mo.MatrisHatasi, match=r"rijit diyaframlı \+3\.50 seviyesinde: yatay ux/uy ve dönme rz ayrıca mesnetlenemez") as h:
        coz(b)
    assert "analiz" in str(h.value) and "esnek" in str(h.value) and "efendi düğüm 9" not in str(h.value)
    # ipucu önce arayüz ayarını söyler (DIYAFRAM-IPUCU; eskiden yalnız JSON düzenlemesi önerilirdi)
    assert "Bina sayfası › Deprem sekmesi › Diyafram: «Esnek»" in str(h.value)
    b2 = copy.deepcopy(b)
    b2["deprem"]["diyafram"] = "esnek"                                                  # arayüzün yazdığı alan
    assert coz(b2).veri["ag"]["diyafram_seviye"]["1"]["mod"] == "esnek"
    b2 = copy.deepcopy(b)
    b2["analiz"]["diyafram"] = {"1": "rijit"}                                            # JSON'da kat bazında rijit: ayar geçmez
    with pytest.raises(mo.MatrisHatasi, match=r"analiz\.diyafram rijit verilmiş") as h:
        coz(b2)
    assert '"analiz": {"diyafram": {"1": "esnek"}}' in str(h.value) and "Deprem sekmesi" not in str(h.value)
    b["mesnetler"] = [{"dugum": {"aks": ["A", "1"], "z": "+3.50"}, "uz": True}]          # düşey mesnet verilebilir
    assert coz(b).veri["akis"]["mesnetler"][0]["adres"] == "A1/+3.50"
    b["mesnetler"] = [{"dugum": {"aks": ["A", "1"], "z": "+3.50"}, "ux": True}]
    b["analiz"]["diyafram"] = {"1": "esnek"}                                             # önerilen çıkış yolu
    assert coz(b).veri["ag"]["diyafram_seviye"]["1"]["mod"] == "esnek"


def test_panel_ek_yuku_durumu():
    b = kutu_bina(0.0, deprem=False)
    b["yuk_durumlari"]["S"] = {"acik": True, "bolge": 3, "rakim": 0}
    v0 = coz(copy.deepcopy(b)).veri["yukler"]["toplam"]
    A = 36.0
    for durum, ek, beklenen in (("S", {"p": 1.0}, {"S": A}), ("Q", {"p": 0.5}, {"Q": 0.5 * A}), ("G", {"p": 2.0}, {"G": 2.0 * A}),
                                ("S", {"g": 0.3, "q": 0.2}, {"S": 0.5 * A}),                 # eski biçim, durum S → ikisi de S
                                (None, {"g": 0.3, "q": 0.2}, {"G": 0.3 * A, "Q": 0.2 * A})):   # eski biçim, durumsuz → g G, q Q
        x = copy.deepcopy(b)
        y = {"tur": "panel", "panel": 1, **ek}
        if durum:
            y["durum"] = durum
        x["ek_yukler"] = [y]
        t = coz(x).veri["yukler"]["toplam"]
        for d in ("G", "Q", "S"):
            assert t[d] == pytest.approx(v0[d] + beklenen.get(d, 0.0), rel=1e-6), (durum, ek, d)


def test_balkon_ts498_genel_model():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["dosemeler"][0]["kullanim"] = "balkon"
    v1 = coz(b).veri
    b3 = copy.deepcopy(b)
    b3["surum"] = 3
    v3 = coz(b3).veri
    assert v1["yukler"]["toplam"]["Q"] == pytest.approx(274.0)
    assert v3["yukler"]["toplam"]["Q"] == pytest.approx(v1["yukler"]["toplam"]["Q"])
    p = next(p for p in v3["yukler"]["paneller"] if p["no"] == 1)
    assert p["q"] == pytest.approx(5.0 + 0.35 * (20.0 - 10.0)) and "Çizelge 6 satır 4" in p["q_kaynak"]


@pytest.mark.parametrize("ad", list(YS.SERBEST_SABLONLAR) + ["portal"])
def test_anlatim_adimlari_ardisik(ad):
    import re
    b = portal(H=10.0, capraz="yalniz", kiris_mafsal=True, taban="mafsal") if ad == "portal" else yapi.bina_sablon(ad)
    r = coz(b, anlat=True)
    nolar = [int(m.group(1)) for _, i, _ in r.anlatim.bloklar for m in [re.match(r"^#+\s*(\d+)\. Adım", str(i))] if m]
    assert nolar == list(range(1, len(nolar) + 1)) and len(nolar) >= 6, nolar
    metin = " ".join(str(i) for _, i, _ in r.anlatim.bloklar)
    if ad != "portal":                    # deprem adımının alt başlıkları da aynı numarayla (5.1, 5.2 …)
        n_dep = next(n for _, i, _ in r.anlatim.bloklar for m in [re.match(r"^#+\s*(\d+)\. Adım: TBDY", str(i))] if m for n in [int(m.group(1))])
        assert f"**{n_dep}.1 Girdiler" in metin and "**7.1 Girdiler" not in metin


def test_aks_kat_deprem_anlatimi_numarasi_degismez():
    r = coz(yapi.bina_sablon("betonarme-3kat-3x3"), anlat=True)
    metin = " ".join(str(i) for _, i, _ in r.anlatim.bloklar)
    assert "7. Adım: TBDY 2018" in metin and "**7.1 Girdiler" in metin and "**7.10 Düşey deprem" in metin


def test_basit_kesit_ust_duzey_lehcesi():
    """IFC/arayüz örneklerindeki {"tip": "boru", "D": 0.1143, "t": 0.004} (m) ve 2L {"h": 60, "ara": 10} (mm) kesitleri."""
    B = YS._oku(portal(H=0.0))
    kart = lambda k: YS._kesit_kart("X", dict(k, malzeme="S275"), B)  # noqa: E731
    a = kart({"tip": "boru", "D": 0.1143, "t": 0.004})
    assert a["profil"].startswith("BORU") and a["h"] == pytest.approx(0.1143)
    assert a["A"] == pytest.approx(kart({"tip": "boru", "boyutlar": {"D": 114.3, "t": 4.0}})["A"])
    assert a["A"] == pytest.approx(math.pi * (0.1143 ** 2 - (0.1143 - 0.008) ** 2) / 4, rel=1e-6)
    assert kart({"tip": "kutu", "h": 0.10, "b": 0.10, "t": 0.005})["aile"] == "KUTU"
    assert kart({"tip": "L", "h": 0.07, "b": 0.07, "t": 0.007})["aile"] == "L"
    assert kart({"tip": "U", "h": 0.16, "b": 0.065, "tw": 0.0075, "tf": 0.0105})["aile"] == "UPN"
    k2 = kart({"tip": "2L", "h": 60, "b": 60, "t": 6, "ara": 10})
    assert k2["aile"] == "2L" and k2["b"] == pytest.approx(0.06)
    # birim kesit başına dış boyuttan: mm verilen ince et kalınlığı (t = 4 mm) metre sanılmaz
    assert kart({"tip": "boru", "D": 114.3, "t": 4})["A"] == pytest.approx(a["A"])
    assert kart({"tip": "kutu", "h": 100, "b": 100, "t": 5})["A"] == pytest.approx(kart({"tip": "kutu", "h": 0.1, "b": 0.1, "t": 0.005})["A"])
    with pytest.raises(mo.MatrisHatasi, match="eşit kollu"):
        kart({"tip": "L", "h": 0.08, "b": 0.06, "t": 0.006})


_ORNEK_BETIK = 'const O=require(process.argv[1]);process.stdout.write(JSON.stringify(O[process.argv[2]]()));'


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
@pytest.mark.parametrize("ad", ["serbest", "aks"])
def test_ifc_orneklerinin_kesitleri_cozulur(ad):
    r = subprocess.run([NODE, "-e", _ORNEK_BETIK, str(PROJE / "testler" / "js" / "ifc_ornekler.js"), ad], capture_output=True, text=True,
                       timeout=60)
    assert r.returncode == 0, r.stderr
    b = json.loads(r.stdout)
    B = YS._oku(dict(b, temeller=dict(b.get("temeller") or {}, tip="tekil"), paneller=[], ek_yukler=[]))
    assert {ad_: k["tip"] for ad_, k in B.kesitler.items() if ad_ in ("BORU", "KUTU")} == {"BORU": "basit", "KUTU": "basit"}
    try:                                         # IFC örneği yapısal olarak tam olmayabilir; kesit hatası olmamalı
        coz(b)
    except mo.MatrisHatasi as h:
        assert "çözümlenemedi" not in str(h) and "Kesit" not in str(h), str(h)


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
