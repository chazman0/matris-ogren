# -*- coding: utf-8 -*-
"""tasarim.py testleri: TS 500 betonarme kiriş/kolon ve ÇYTHYE 2018 çelik tahkikleri (ders kitabı el hesaplarıyla).

El hesapları testin içinde bağımsız yazılmıştır (modülün yardımcıları kullanılmaz). Birimler: N, mm, MPa.
"""
from __future__ import annotations

import importlib
import json
import math
import sys
import types

import pytest

import matris_ogren as mo

# ----------------------------------------------------------------------------
# yapi_veri.py (kütüphane) paralel dalda geliştiriliyor; bu dalda yoksa testlerin kullandığı kayıtlarla (yapi_veri.py
# değerlerinin birebir kopyası) küçük bir yedek modül kurulur. Kütüphane varsa doğrudan o kullanılır.
# ----------------------------------------------------------------------------
try:
    import yapi_veri  # noqa: F401
    GERCEK_KUTUPHANE = True
except ImportError:  # pragma: no cover - yalnız kütüphanesiz dalda
    GERCEK_KUTUPHANE = False
    _yv = types.ModuleType("yapi_veri")
    _yv.BETONLAR = {}
    for _ad, _fck, _fctk, _Ec, _k1 in (("C20/25", 20, 1.6, 28000, 0.85), ("C25/30", 25, 1.8, 30000, 0.85),
                                       ("C30/37", 30, 1.9, 32000, 0.82), ("C35/45", 35, 2.1, 33000, 0.79),
                                       ("C40/50", 40, 2.2, 34000, 0.76), ("C45/55", 45, 2.3, 36000, 0.73),
                                       ("C50/60", 50, 2.5, 37000, 0.70)):
        _yv.BETONLAR[_ad] = {"tur": "beton", "fck": _fck, "fctk": _fctk, "Ec": _Ec, "k1": _k1, "dogrulandi": True}
    _yv.DONATILAR = {"B420C": {"tur": "donati", "fyk": 420, "Es": 200000},
                     "B500C": {"tur": "donati", "fyk": 500, "Es": 200000}}
    _yv.CELIKLER = {ad: {"tur": "celik", "Fy": fy, "Fu": fu, "Fy_40_80": fy2, "Fu_40_80": fu2, "E": 200000, "G": 77200}
                    for ad, fy, fu, fy2, fu2 in (("S235", 235, 360, 215, 360), ("S275", 275, 430, 255, 410),
                                                 ("S355", 355, 510, 335, 470))}
    _A = ("h", "b", "tw", "tf", "r", "A", "g", "Iy", "Wely", "Wply", "iy", "Iz", "Welz", "Wplz", "iz", "It", "Iw", "Avz")
    _yv.PROFILLER = {
        "IPE 200": dict(zip(_A, (200.0, 100.0, 5.6, 8.5, 12.0, 28.48, 22.4, 1943.0, 194.3, 220.6, 8.26, 142.4, 28.47,
                                 44.61, 2.24, 6.98, 12.99, 14.0))),
        "IPE 300": dict(zip(_A, (300.0, 150.0, 7.1, 10.7, 15.0, 53.81, 42.2, 8356.0, 557.1, 628.4, 12.46, 603.8, 80.5,
                                 125.2, 3.35, 20.12, 125.9, 25.68))),
        "HEA 300": dict(zip(_A, (290.0, 300.0, 8.5, 14.0, 27.0, 112.5, 88.0, 18260.0, 1260.0, 1383.0, 12.74, 6310.0,
                                 420.6, 641.2, 7.49, 85.17, 1200.0, 37.28))),
        "HEB 200": dict(zip(_A, (200.0, 200.0, 9.0, 15.0, 18.0, 78.08, 61.3, 5696.0, 569.6, 642.5, 8.54, 2003.0, 200.3,
                                 305.8, 5.07, 59.28, 171.1, 24.83))),
    }
    sys.modules["yapi_veri"] = _yv

import tasarim as ta  # noqa: E402

if ta.yv is None:  # tasarim, yedek modülden önce içe aktarılmışsa
    ta = importlib.reload(ta)

E = 200000.0
ES = 200000.0


def yakin(a, b, oran=1e-3, mutlak=1e-9):
    return abs(a - b) <= max(oran * abs(b), mutlak)


def json_temiz(x):
    json.dumps(x, allow_nan=False)
    return True


# ============================================================================
# Malzeme
# ============================================================================
def test_beton_malzeme_c30():
    b = ta.beton_malzeme("C30")
    assert b["sinif"] == "C30/37"
    assert yakin(b["fcd"], 20.0) and yakin(b["fctd"], 1.9 / 1.5) and b["k1"] == 0.82 and b["eps_cu"] == 0.003
    assert ta.beton_malzeme("c30/37") == b


@pytest.mark.parametrize("sinif,k1", [("C20", 0.85), ("C25", 0.85), ("C30", 0.82), ("C35", 0.79), ("C40", 0.76),
                                      ("C45", 0.73), ("C50", 0.70)])
def test_k1_cizelge_7_1(sinif, k1):
    assert ta.beton_malzeme(sinif)["k1"] == pytest.approx(k1)


def test_donati_malzeme():
    d = ta.donati_malzeme("B420C")
    assert yakin(d["fyd"], 420 / 1.15) and d["Es"] == 200000 and yakin(d["eps_yd"], 420 / 1.15 / 2e5)


def test_beton_sozlukle():
    b = ta.beton_malzeme({"fck": 30, "k1": 0.82})
    assert yakin(b["fctk"], 0.35 * math.sqrt(30)) and yakin(b["Ec"], 3250 * math.sqrt(30) + 14000)


# ============================================================================
# Kiriş eğilme (TS 500)
# ============================================================================
def el_as_tek(Md_kNm, b, d, fcd, fyd):
    M = Md_kNm * 1e6
    a = d - math.sqrt(d * d - 2 * M / (0.85 * fcd * b))
    return 0.85 * fcd * b * a / fyd, a


def test_tek_donatili_kiris_el_hesabi():
    """C30, B420C, 300×500, d = 460, Md = 150 kN·m → As ≈ 965 mm² (el hesabı ±%0,5)."""
    r = ta.kiris_egilme(150, 0.30, 0.50, 0.04, "C30", "B420C")
    As_el, a_el = el_as_tek(150, 300, 460, 20.0, 420 / 1.15)
    assert r["d_mm"] == 460.0 and r["tek_donatili"] is True
    assert abs(r["As_gerekli_cm2"] * 100 - As_el) <= 0.005 * As_el
    assert As_el == pytest.approx(965.4, abs=0.5)
    assert r["a_mm"] == pytest.approx(a_el, rel=1e-6)
    # ders kitabı ρ formülü (araştırma: ρ = 0,85fcd/fyd (1 − √(1 − 2Md/(0,85 fcd b d²))))
    rho = 0.85 * 20 / (420 / 1.15) * (1 - math.sqrt(1 - 2 * 150e6 / (0.85 * 20 * 300 * 460 ** 2)))
    assert r["rho_gerekli"] == pytest.approx(rho, rel=1e-6)
    assert r["oneri"]["As_cm2"] >= r["As_gerekli_cm2"] and r["oneri"]["sigar"]
    assert r["Mr_kNm"] >= 150 and r["durum"] == "yeterli" and r["dc"] <= 1.0
    assert json_temiz(r)


@pytest.mark.parametrize("sinif,rho_b", [("C20", 0.0164), ("C25", 0.0205), ("C30", 0.02373), ("C40", 0.02932)])
def test_rho_b_kapali_form(sinif, rho_b):
    """ρb = 0,85 k1 (fcd/fyd)·600/(600 + fyd) (araştırma çizelgesi değerleri)."""
    r = ta.kiris_egilme(50, 0.30, 0.50, 0.04, sinif, "B420C")
    b = ta.beton_malzeme(sinif)
    fyd = 420 / 1.15
    assert r["rho_b"] == pytest.approx(0.85 * b["k1"] * b["fcd"] / fyd * 600 / (600 + fyd), rel=1e-9)
    assert r["rho_b"] == pytest.approx(rho_b, rel=3e-3)


def test_rho_min_ve_rho_max():
    r30 = ta.kiris_egilme(50, 0.30, 0.50, 0.04, "C30")
    assert r30["rho_min"] == pytest.approx(0.8 * (1.9 / 1.5) / (420 / 1.15), rel=1e-9)
    assert r30["rho_min"] == pytest.approx(0.00277, abs=1e-5)
    assert r30["rho_max"] == 0.02                         # 0,85ρb = 0,02017 > 0,02
    r25 = ta.kiris_egilme(50, 0.30, 0.50, 0.04, "C25")
    assert r25["rho_max"] == pytest.approx(0.01742, rel=2e-3)   # 0,85ρb belirleyici
    # küçük momentte en az donatı belirleyici
    r = ta.kiris_egilme(10, 0.30, 0.50, 0.04, "C30")
    assert r["As_gerekli_cm2"] * 100 == pytest.approx(r30["rho_min"] * 300 * 460, rel=1e-9)


def test_mr_ters_problem_tutarli():
    """Gerekli As mevcut kabul edilirse Mr = Md (D/C = 1)."""
    for Md in (60, 150, 230):
        r = ta.kiris_egilme(Md, 0.30, 0.50, 0.04, "C30")
        t = ta.kiris_egilme(Md, 0.30, 0.50, 0.04, "C30", As_mevcut=r["As_gerekli_cm2"])
        if r["As_gerekli_cm2"] * 100 > r["rho_min"] * 300 * 460 * 1.001:
            assert t["Mr_kNm"] == pytest.approx(Md, rel=1e-4)
            assert t["dc"] == pytest.approx(1.0, abs=1e-3) or t["dc"] <= 1.0
        assert t["eps_s_r"] >= 420 / 1.15 / ES  # çelik akıyor


def test_cift_donati_esigi():
    """C25'te 0,85ρb < 0,02: Md, M_lim'i aşınca basınç donatısı gerekir."""
    b, d, fcd, fyd = 300.0, 460.0, 25 / 1.5, 420 / 1.15
    rho_b = 0.85 * 0.85 * fcd / fyd * 600 / (600 + fyd)
    As_lim = 0.85 * rho_b * b * d
    a_lim = As_lim * fyd / (0.85 * fcd * b)
    M_lim = As_lim * fyd * (d - a_lim / 2) / 1e6
    alt = ta.kiris_egilme(0.99 * M_lim, 0.30, 0.50, 0.04, "C25")
    ust = ta.kiris_egilme(1.05 * M_lim, 0.30, 0.50, 0.04, "C25")
    assert alt["tek_donatili"] and alt["As_ust_gerekli_cm2"] == 0
    assert not ust["tek_donatili"] and ust["As_ust_gerekli_cm2"] > 0
    # çift donatılı tasarımın kendi donatısıyla taşıma gücü ≈ Md
    t = ta.kiris_egilme(1.05 * M_lim, 0.30, 0.50, 0.04, "C25", As_mevcut=ust["As_gerekli_cm2"],
                        As_ust=ust["As_ust_gerekli_cm2"])
    assert t["Mr_kNm"] == pytest.approx(1.05 * M_lim, rel=0.02)
    # el hesabı As′ (basınç donatısı akıyorsa)
    c = a_lim / 0.85
    es2 = 0.003 * (c - 40) / c
    s2 = min(ES * es2, fyd)
    As2 = (1.05 - 1.0) * M_lim * 1e6 / (s2 * (d - 40))
    assert ust["As_ust_gerekli_cm2"] * 100 == pytest.approx(As2, rel=1e-6)


def test_kiris_durumlari():
    assert ta.kiris_egilme(900, 0.30, 0.50, 0.04, "C30")["durum"] == "kesit büyüt"
    r = ta.kiris_egilme(150, 0.30, 0.50, 0.04, "C30", As_mevcut=6.0)
    assert r["durum"] == "donatı artır" and r["dc"] > 1
    assert ta.kiris_egilme(150, 0.30, 0.50, 0.04, "C30", As_mevcut=12.0)["durum"] == "yeterli"
    # TBDY bw ≥ 250 mm
    r = ta.kiris_egilme(30, 0.20, 0.40, 0.04, "C30")
    assert r["durum"] == "kesit büyüt"
    assert ta.kiris_egilme(30, 0.20, 0.40, 0.04, "C30", tbdy=False)["durum"] == "yeterli"


# ============================================================================
# Kiriş kesme (TS 500 md. 8.1)
# ============================================================================
def test_kesme_el_hesabi():
    fctd, fcd, fywd, b, d = 1.9 / 1.5, 20.0, 420 / 1.15, 300.0, 460.0
    r = ta.kiris_kesme(200, 0.30, 0.50, 0.04, "C30", "B420C")
    Vcr = 0.65 * fctd * b * d
    assert r["V_cr_kN"] == pytest.approx(Vcr / 1e3, rel=1e-9) and r["V_cr_kN"] == pytest.approx(113.62, abs=0.01)
    assert r["V_c_kN"] == pytest.approx(0.8 * Vcr / 1e3, rel=1e-9)
    assert r["V_max_kN"] == pytest.approx(0.22 * fcd * b * d / 1e3, rel=1e-9)
    assert r["Asw_s_gerekli"] == pytest.approx((200e3 - 0.8 * Vcr) / (fywd * d), rel=1e-9)
    assert r["Asw_s_min"] == pytest.approx(0.3 * fctd * b / fywd, rel=1e-9)
    o = r["oneri"]
    assert o["s_mm"] <= d / 2 and o["Asw_s"] >= r["Asw_s_tasarim"] - 1e-12
    assert r["V_r_kN"] >= 200 and r["durum"] == "yeterli"
    assert json_temiz(r)


def test_kesme_min_etriye_ve_ust_sinir():
    r = ta.kiris_kesme(80, 0.30, 0.50, 0.04, "C30")
    assert not r["hesap_gerekli"] and r["Asw_s_tasarim"] == pytest.approx(r["Asw_s_min"])
    r = ta.kiris_kesme(700, 0.30, 0.50, 0.04, "C30")
    assert r["durum"] == "kesit büyüt"
    # Vd > 3Vcr → s ≤ d/4
    r = ta.kiris_kesme(400, 0.30, 0.50, 0.04, "C30")
    assert r["s_max_mm"] == pytest.approx(115.0) and r["oneri"]["s_mm"] <= 115.0
    # sarılma bölgesi
    r = ta.kiris_kesme(150, 0.30, 0.50, 0.04, "C30", sarilma=True, boyuna_cap=14)
    assert r["s_max_mm"] == pytest.approx(min(115.0, 112.0, 150.0))


def test_kesme_eksenel_basinc():
    r0 = ta.kiris_kesme(150, 0.30, 0.50, 0.04, "C30")
    r1 = ta.kiris_kesme(150, 0.30, 0.50, 0.04, "C30", Nd=300)
    assert r1["V_cr_kN"] == pytest.approx(r0["V_cr_kN"] * (1 + 0.07 * 300e3 / (300 * 500)), rel=1e-9)
    r2 = ta.kiris_kesme(150, 0.30, 0.50, 0.04, "C30", Nd=-300)   # 2 MPa çekme → γ = −0,3
    assert r2["V_cr_kN"] == pytest.approx(r0["V_cr_kN"] * (1 - 0.3 * 300e3 / (300 * 500)), rel=1e-9)


# ============================================================================
# Kolon N–M etkileşimi
# ============================================================================
KOLON = dict(b=0.40, h=0.50, As_toplam=24.0, paspayi=0.05, beton="C30", donati="B420C")


def test_kolon_uc_noktalari():
    fcd, fyd = 20.0, 420 / 1.15
    for yer in ("dort_yuz", "iki_yuz"):
        e = ta.kolon_etkilesim(**KOLON, yerlesim=yer)
        Ac, As = 400 * 500, 2400.0
        assert e["N0_kN"] == pytest.approx((0.85 * fcd * (Ac - As) + As * fyd) / 1e3, rel=1e-9)
        assert e["Nt_kN"] == pytest.approx(-As * fyd / 1e3, rel=1e-9)
        P = e["noktalar"]
        assert P[0]["N_kN"] == e["Nt_kN"] and P[-1]["N_kN"] == e["N0_kN"]
        assert P[0]["M_kNm"] == 0 and P[-1]["M_kNm"] == 0
        assert e["N_max_TS500_kN"] == pytest.approx(0.9 * fcd * Ac / 1e3)
        assert e["N_max_TBDY_kN"] == pytest.approx(0.40 * 30 * Ac / 1e3)
        assert json_temiz(e)


def test_kolon_dengeli_nokta_el_hesabi():
    """İki yüz donatılı: dengeli noktada εs = εyd; Nb, Mb kapalı formla."""
    e = ta.kolon_etkilesim(**KOLON, yerlesim="iki_yuz")
    fcd, fyd, k1 = 20.0, 420 / 1.15, 0.82
    h, b, dp, As1 = 500.0, 400.0, 50.0, 1200.0
    d = h - dp
    eyd = fyd / ES
    cb = 0.003 * d / (0.003 + eyd)
    a = k1 * cb
    es2 = 0.003 * (cb - dp) / cb
    s2 = min(ES * es2, fyd)
    cap = math.sqrt(4 * (As1 / 2) / math.pi)        # iki çubuk/yüz
    oran = min(max((a - (dp - cap / 2)) / cap, 0), 1)
    Cc = 0.85 * fcd * b * a
    Cs = As1 * s2 - oran * 0.85 * fcd * As1
    T = As1 * fyd
    Nb = Cc + Cs - T
    Mb = Cc * (h / 2 - a / 2) + Cs * (h / 2 - dp) + T * (d - h / 2)
    dg = e["dengeli"]
    assert dg["eps_s"] == pytest.approx(eyd, rel=1e-9)
    assert dg["c_mm"] == pytest.approx(cb, rel=1e-9)
    assert dg["N_kN"] == pytest.approx(Nb / 1e3, rel=1e-6)
    assert dg["M_kNm"] == pytest.approx(Mb / 1e6, rel=1e-6)


def test_kolon_egri_monoton_ve_disbukey():
    for yer in ("dort_yuz", "iki_yuz"):
        for eksen in ("x", "y"):
            e = ta.kolon_etkilesim(**KOLON, yerlesim=yer, eksen=eksen)
            P = e["noktalar"]
            N = [p["N_kN"] for p in P]
            assert all(b > a for a, b in zip(N, N[1:])), "N, c ile tekdüze artmalı"
            dg = e["dengeli"]
            for p in P:   # eğri, (Nt,0)–dengeli–(N0,0) kirişlerinin üstünde kalır (kabaca dışbükeylik)
                if p["N_kN"] <= dg["N_kN"]:
                    alt = dg["M_kNm"] * (p["N_kN"] - e["Nt_kN"]) / (dg["N_kN"] - e["Nt_kN"])
                else:
                    alt = dg["M_kNm"] * (e["N0_kN"] - p["N_kN"]) / (e["N0_kN"] - dg["N_kN"])
                assert p["M_kNm"] >= alt - 1e-6
            assert max(p["M_kNm"] for p in P) >= dg["M_kNm"] - 1e-9


def _M_N0(e):
    P = e["noktalar"]
    for a, b in zip(P, P[1:]):
        if a["N_kN"] <= 0 <= b["N_kN"]:
            return a["M_kNm"] + (b["M_kNm"] - a["M_kNm"]) * (0 - a["N_kN"]) / (b["N_kN"] - a["N_kN"])
    raise AssertionError


def test_kolon_saf_egilme_kiris_ile_uyumlu():
    e = ta.kolon_etkilesim(**KOLON, yerlesim="iki_yuz", n=120)
    M0 = _M_N0(e)
    cift = ta.kiris_egilme(100, 0.40, 0.50, 0.05, "C30", As_mevcut=12.0, As_ust=12.0)
    tek = ta.kiris_egilme(100, 0.40, 0.50, 0.05, "C30", As_mevcut=12.0)
    assert M0 == pytest.approx(cift["Mr_kNm"], rel=0.01)
    assert M0 == pytest.approx(tek["Mr_kNm"], rel=0.03)
    # el hesabı tek donatılı: As fyd (d − a/2)
    a = 1200 * (420 / 1.15) / (0.85 * 20 * 400)
    assert M0 == pytest.approx(1200 * 420 / 1.15 * (450 - a / 2) / 1e6, rel=0.03)


def test_radyal_dc_egri_uzerinde_bir():
    e = ta.kolon_etkilesim(**KOLON, yerlesim="dort_yuz")
    dg = e["dengeli"]
    k = ta.kolon_kontrol(dg["N_kN"], dg["M_kNm"], 0.0, **KOLON, tbdy=False)
    assert k["noktalar"][0]["dc_x"] == pytest.approx(1.0, abs=1e-6)
    k = ta.kolon_kontrol(0.5 * dg["N_kN"], 0.5 * dg["M_kNm"], 0.0, **KOLON)
    assert k["noktalar"][0]["dc_x"] == pytest.approx(0.5, abs=1e-6)
    # eğrinin başka bir köşesi (çekme bölgesi)
    p = e["noktalar"][5]
    k = ta.kolon_kontrol(p["N_kN"], p["M_kNm"], 0.0, **KOLON)
    assert k["noktalar"][0]["dc_x"] == pytest.approx(1.0, abs=1e-6)
    assert json_temiz(k)


def test_kolon_e_min_ve_eksenel_sinirlar():
    k = ta.kolon_kontrol(2000, 0.0, 0.0, **KOLON)
    p = k["noktalar"][0]
    assert p["e_min_x_mm"] == pytest.approx(15 + 0.03 * 500) and p["e_min_y_mm"] == pytest.approx(15 + 0.03 * 400)
    assert p["Mx_tasarim_kNm"] == pytest.approx(2000 * 0.030) and p["My_tasarim_kNm"] == pytest.approx(2000 * 0.027)
    k = ta.kolon_kontrol(3700, 10.0, 0.0, **KOLON)    # > 0,9 fcd Ac = 3600 kN
    assert k["durum"] == "kesit büyüt"
    # varsayılan tbdy=False (bağımsız API: TS 500): 0,40 fck Ac sınırı deprem dışı birleşime uygulanmaz
    k = ta.kolon_kontrol(2500, 10.0, 0.0, **KOLON)    # > 0,40 fck Ac = 2400 kN (TBDY) ama < 0,9 fcd Ac
    assert all(x["saglandi"] for x in k["kontroller"] if "Nd" in x["ad"]) and not any("TBDY" in x["ad"] for x in k["kontroller"])
    assert k["tbdy"] is False
    k = ta.kolon_kontrol(2500, 10.0, 0.0, **KOLON, tbdy=True)    # deprem listesi yok: her nokta deprem sayılır (uyarılı)
    assert any(not x["saglandi"] and "TBDY" in x["ad"] for x in k["kontroller"]) and any("deprem" in u for u in k["uyarilar"])
    # kombinasyon türü: yalnız deprem birleşimi noktasına (2.) uygulanır
    k = ta.kolon_kontrol([2500, 2500], [10.0, 10.0], [0.0, 0.0], **KOLON, tbdy=True, deprem=[False, True], adlar=["1.4G+1.6Q", "G+Q+E"])
    p1, p2 = k["noktalar"]
    assert not any("Ndm" in x["ad"] for x in p1["kontroller"]) and any("Ndm" in x["ad"] and not x["saglandi"] for x in p2["kontroller"])
    assert not any("deprem listesi" in u for u in k["uyarilar"])
    with pytest.raises(mo.MatrisHatasi, match="deprem"):
        ta.kolon_kontrol([2500, 2500], [10.0, 10.0], 0.0, **KOLON, tbdy=True, deprem=[True])


def test_kolon_donati_orani():
    k = ta.kolon_kontrol(800, 100, 0, **dict(KOLON, As_toplam=90.0))   # ρ = 0,045
    assert k["durum"] == "kesit büyüt"
    k = ta.kolon_kontrol(800, 100, 0, **dict(KOLON, As_toplam=16.0))   # ρ = 0,008
    assert any(not x["saglandi"] and "0,01" in x["ad"] for x in k["kontroller"])


def test_kolon_iki_eksen_bresler():
    kk = dict(KOLON, b=0.50, h=0.50)
    k = ta.kolon_kontrol([1500, 100], [120, 60], [120, 60], **kk)
    p = k["noktalar"][0]
    assert p["iki_eksen_yontemi"] == "Bresler ters yük"
    Nr = 1.0 / (1.0 / p["N_rx_kN"] + 1.0 / p["N_ry_kN"] - 1.0 / k["N0_kN"])
    assert p["N_r_kN"] == pytest.approx(Nr) and p["dc_iki_eksen"] == pytest.approx(1500 / Nr)
    assert p["N_rx_kN"] == pytest.approx(p["N_ry_kN"], rel=1e-9)     # kare kesit, simetrik
    q = k["noktalar"][1]
    assert q["iki_eksen_yontemi"] == "doğrusal moment toplamı" and q["dc_iki_eksen"] > 0
    assert k["dc"] >= max(p["dc"], q["dc"]) - 1e-12


# ============================================================================
# Çelik (ÇYTHYE 2018)
# ============================================================================
def test_celik_malzeme_bantlari():
    m = ta.celik_malzeme("S275")
    assert (m["Fy"], m["Fu"], m["E"], m["G"]) == (275, 430, 200000, 77200)
    m = ta.celik_malzeme("S275", t_mm=50)
    assert (m["Fy"], m["Fu"]) == (255, 410)
    with pytest.raises(mo.MatrisHatasi):
        ta.celik_malzeme("S275", t_mm=90)


def test_kesit_sinifi_ipe300_s275():
    s = ta.kesit_sinifi("IPE 300", 275)
    k = math.sqrt(E / 275)
    assert s["egilme"] == "kompakt" and s["basinc"] == "narin olmayan"
    assert s["baslik"]["oran"] == pytest.approx(150 / (2 * 10.7))
    assert s["govde"]["oran"] == pytest.approx((300 - 2 * 10.7 - 2 * 15) / 7.1)
    assert s["baslik"]["lambda_p"] == pytest.approx(0.38 * k) and s["baslik"]["lambda_p"] == pytest.approx(10.25, abs=0.01)
    assert s["govde"]["lambda_p"] == pytest.approx(101.4, abs=0.05) and s["govde"]["lambda_r"] == pytest.approx(153.7, abs=0.05)
    assert s["baslik"]["basinc_lambda_r"] == pytest.approx(0.56 * k) and s["govde"]["basinc_lambda_r"] == pytest.approx(1.49 * k)


@pytest.mark.parametrize("ad,profil,parca", [("BORU 168.3x6.3", "BORU 168.3x6.3", 1), ("KUTU 150x8", "KUTU 150x150x8", 2),
                                             ("L 100x10", "L 100x100x10", 1), ("2L 70x7 s=10", "2L 70x70x7 s=10", 1),
                                             ("UPN 200", "UPN 200", 2)])
def test_kesit_sinifi_basit_kesitler(ad, profil, parca):
    """C20: tabloda olmayan basit kesit adı (_ad_coz) Tablo 5.1A/B basit kesit kurallarıyla sınıflanır (eskiden 'tabloda yok')."""
    s = ta.kesit_sinifi(ad, 275)
    assert s["tur"] == "kesit_sinifi" and s["profil"] == profil and len(s["parcalar"]) == parca
    assert s["basinc"] in ("narin olmayan", "narin") and s["kaynak"].startswith("ÇYTHYE 2018 Tablo 5.1")
    assert s["egilme"] in (("kompakt", "kompakt olmayan", "narin") if not ad.startswith("2L") else (None,))
    c = ta.celik_cubuk_kontrol(ad, "S275", 2, kuvvetler={"N": 10})["sinif"]        # çubuk tahkikiyle aynı sınıf
    assert c["basinc"] == s["basinc"] and c["egilme"] == s["egilme"]
    assert ta.kesit_sinifi(ad, "S275")["Fy"] == pytest.approx(275.0)
    with pytest.raises(mo.MatrisHatasi, match="tabloda yok"):
        ta.kesit_sinifi("XYZ 100", 275)
    assert ta.kesit_sinifi("BORU 406.4x5", 355)["basinc"] == "narin"         # D/t = 81 > 0,11·E/Fy = 62


def test_kesit_sinifi_kompakt_olmayan_baslik():
    s = ta.kesit_sinifi("HEA 300", 355)     # 300/(2·14) = 10,71 > 0,38√(E/355) = 9,02
    assert s["baslik"]["egilme"] == "kompakt olmayan" and s["egilme"] == "kompakt olmayan"
    r = ta.celik_egilme("HEA 300", 355, 0.5)
    Mp = 355 * 1383e3
    lf, lp, lr = 300 / 28, 0.38 * math.sqrt(E / 355), math.sqrt(E / 355)
    assert r["Mn_FLB_kNm"] == pytest.approx((Mp - (Mp - 0.7 * 355 * 1260e3) * (lf - lp) / (lr - lp)) / 1e6, rel=1e-9)
    assert r["Mn_kNm"] == pytest.approx(min(r["Mn_FLB_kNm"], r["Mn_YBB_kNm"]))


def test_ipe300_mp_lp_lr():
    r = ta.celik_egilme("IPE 300", 275, 1.0)
    assert r["Mp_kNm"] == pytest.approx(275 * 628.4e3 / 1e6) and r["Mp_kNm"] == pytest.approx(172.81, abs=0.01)
    assert r["Lp_m"] * 1000 == pytest.approx(1.76 * 33.5 * math.sqrt(E / 275), rel=1e-9)
    # Lr el hesabı (c = 1, ho = d − tf, i_ts² = √(Iz Cw)/Wel)
    ho = 300 - 10.7
    its = math.sqrt(math.sqrt(603.8e4 * 125.9e9) / 557.1e3)
    jc = 20.12e4 / (557.1e3 * ho)
    Lr = 1.95 * its * E / (0.7 * 275) * math.sqrt(jc + math.sqrt(jc ** 2 + 6.76 * (0.7 * 275 / E) ** 2))
    assert r["Lr_m"] * 1000 == pytest.approx(Lr, rel=1e-9)
    assert r["bolge"].startswith("akma") and r["Mn_kNm"] == pytest.approx(r["Mp_kNm"])
    assert r["Mc_kNm"] == pytest.approx(0.9 * r["Mp_kNm"])
    g = ta.celik_egilme("IPE 300", 275, 1.0, yontem="GKT")
    assert g["Mc_kNm"] == pytest.approx(r["Mp_kNm"] / 1.67)
    assert json_temiz(r)


def test_ybb_bolge_surekliligi():
    r = ta.celik_egilme("IPE 300", 275, 1.0)
    Lp, Lr = r["Lp_m"], r["Lr_m"]
    e = 1e-7
    a, b = ta.celik_egilme("IPE 300", 275, Lp - e)["Mn_kNm"], ta.celik_egilme("IPE 300", 275, Lp + e)["Mn_kNm"]
    assert a == pytest.approx(b, rel=1e-6)
    a, b = ta.celik_egilme("IPE 300", 275, Lr - e)["Mn_kNm"], ta.celik_egilme("IPE 300", 275, Lr + e)["Mn_kNm"]
    assert a == pytest.approx(b, rel=2e-3)        # Denk. 9.6b'deki 6,76 yuvarlaması kadar
    assert a == pytest.approx(0.7 * 275 * 557.1e3 / 1e6, rel=2e-3)
    # Lb arttıkça Mn azalır
    Ms = [ta.celik_egilme("IPE 300", 275, L)["Mn_kNm"] for L in (1, 2, 3, 4, 5, 6, 8, 10)]
    assert all(b <= a + 1e-9 for a, b in zip(Ms, Ms[1:]))
    # Cb büyütür ama Mp'yi aşamaz
    assert ta.celik_egilme("IPE 300", 275, 4.0, Cb=1.3)["Mn_kNm"] <= 172.81 + 1e-9
    el = ta.celik_egilme("IPE 300", 275, 8.0)
    assert el["Fcr_MPa"] is not None and el["Mn_kNm"] == pytest.approx(el["Fcr_MPa"] * 557.1e3 / 1e6)


def test_cb_katsayisi():
    assert ta.cb_katsayisi(1, 1, 1, 1) == pytest.approx(1.0)
    assert ta.cb_katsayisi(1, 0.75, 1, 0.75) == pytest.approx(12.5 / 11.0)   # düzgün yayılı basit kiriş
    with pytest.raises(mo.MatrisHatasi):
        ta.cb_katsayisi(1, 2, 1, 1)


def test_zayif_eksen():
    r = ta.celik_egilme("IPE 300", 275, 1.0)
    assert r["Mny_kNm"] == pytest.approx(min(275 * 125.2e3, 1.6 * 275 * 80.5e3) / 1e6)


def _el_pn(A, i, KL, Fy):
    lam = KL / i
    Fe = math.pi ** 2 * E / lam ** 2
    Fcr = 0.658 ** (Fy / Fe) * Fy if lam <= 4.71 * math.sqrt(E / Fy) else 0.877 * Fe
    return Fcr * A / 1e3


@pytest.mark.parametrize("KL", [2.0, 3.0, 5.0, 8.0])
def test_heb200_pn_el_hesabi(KL):
    r = ta.celik_basinc("HEB 200", 275, KL, KL)
    assert r["Pn_kN"] == pytest.approx(_el_pn(7808, 50.7, KL * 1000, 275), rel=1e-9)
    assert r["Pc_kN"] == pytest.approx(0.9 * r["Pn_kN"])
    assert r["KLr"] == pytest.approx(KL * 1000 / 50.7)


def test_fcr_gecis_surekliligi():
    i = 50.7
    KL = 4.71 * math.sqrt(E / 275) * i / 1000
    a = ta.celik_basinc("HEB 200", 275, 1.0, KL * (1 - 1e-9))["Fcr_MPa"]
    b = ta.celik_basinc("HEB 200", 275, 1.0, KL * (1 + 1e-9))["Fcr_MPa"]
    assert a == pytest.approx(b, rel=5e-3)        # 0,658^2,25 = 0,390 ≈ 0,877/2,25 = 0,390
    assert ta.celik_basinc("HEB 200", 275, 1.0, KL * 1.01)["bolge"].startswith("elastik (")


@pytest.mark.parametrize("ad", ["IPE 200", "IPE 300"])
def test_kesme_ipe_cv1(ad):
    r = ta.celik_kesme(ad, 275)
    p = ta.yv.PROFILLER[ad]
    assert r["Cv1"] == 1.0 and r["phi_v"] == 1.0 and r["Omega_v"] == 1.5
    assert r["Vn_kN"] == pytest.approx(0.6 * 275 * p["h"] * p["tw"] / 1e3)
    assert r["Vc_kN"] == pytest.approx(r["Vn_kN"])


@pytest.mark.skipif(not GERCEK_KUTUPHANE, reason="tüm profil kataloğu (yapi_veri.py) gerekli")
def test_tum_profiller_siniflanir_ve_ipe_kesme_cv1():
    import yapi_veri as yv
    assert len(yv.PROFILLER) == 56
    for ad in yv.PROFILLER:
        for Fy in (235, 275, 355):
            s = ta.kesit_sinifi(ad, Fy)
            assert s["govde"]["egilme"] == "kompakt"
        if ad.startswith("IPE"):
            assert ta.celik_kesme(ad, 355)["Cv1"] == 1.0
        assert json_temiz(ta.celik_eleman_kontrol(ad, "S275", 4.0, kuvvetler={"N": 100, "Mx": 10}))


def test_celik_cekme():
    r = ta.celik_cekme("IPE 300", 275, 430, An=45.0, U=0.9, L=6.0)
    assert r["Tc_akma_kN"] == pytest.approx(0.9 * 275 * 5381 / 1e3)
    assert r["Tc_kirilma_kN"] == pytest.approx(0.75 * 430 * 0.9 * 4500 / 1e3)
    assert r["Tc_kN"] == pytest.approx(min(r["Tc_akma_kN"], r["Tc_kirilma_kN"]))
    assert r["kontroller"][-1]["talep"] == pytest.approx(6000 / 33.5)


def test_etkilesim_iki_dal_surekli():
    """Sınır eğrisi Pr/Pc = 0,2'de süreklidir: 11.1a ve 11.1b, M oranı 0,9'da D/C = 1 verir."""
    e = 1e-9
    a = ta.celik_etkilesim(0.2 + e, 0.9, 0, 1, 1, 1)
    b = ta.celik_etkilesim(0.2 - e, 0.9, 0, 1, 1, 1)
    assert a["dal"] == "11.1a" and b["dal"] == "11.1b"
    assert a["dc"] == pytest.approx(1.0, abs=1e-6) and b["dc"] == pytest.approx(1.0, abs=1e-6)
    assert ta.celik_etkilesim(0.5, 0.2, 0.1, 1, 1, 1)["dc"] == pytest.approx(0.5 + 8 / 9 * 0.3)
    assert ta.celik_etkilesim(0.1, 0.2, 0.1, 1, 1, 1)["dc"] == pytest.approx(0.05 + 0.3)


def test_celik_eleman_kontrol_tutarli():
    r = ta.celik_eleman_kontrol("HEB 200", "S275", 3.5, K=1.0,
                                kuvvetler=[{"ad": "B", "N": 500, "Mx": 40, "My": 5, "V": 50},
                                           {"ad": "Ç", "N": -200, "Mx": 30}])
    b, c = r["kombinasyonlar"]
    bas = ta.celik_basinc("HEB 200", 275, 3.5, 3.5)
    eg = ta.celik_egilme("HEB 200", 275, 3.5)
    et = ta.celik_etkilesim(500, 40, 5, bas["Pc_kN"], eg["Mc_kNm"], eg["Mcy_kNm"])
    assert b["dc_etkilesim"] == pytest.approx(et["dc"]) and b["dal"] == et["dal"]
    assert c["tur"] == "çekme" and c["Pc_kN"] == pytest.approx(r["cekme"]["Tc_kN"])
    assert r["dc"] == pytest.approx(max(b["dc"], c["dc"], *[k["dc"] for k in r["kontroller"]]))
    assert r["malzeme"]["Fy"] == 275 and r["durum"] == "yeterli"
    assert json_temiz(r)


# ============================================================================
# Anlatım
# ============================================================================
def test_anlatimli_sonuc_ve_icerik():
    s = ta.kiris_egilme_anlatimli(150, 0.30, 0.50, 0.04, "C30", "B420C", goster="yok")
    assert isinstance(s, mo.Sonuc) and s.veri == ta.kiris_egilme(150, 0.30, 0.50, 0.04, "C30", "B420C")
    md = s.anlatim.markdown()
    assert "Ne yapıyoruz, neden?" in md and "Denk. 7.3" in md and "10^{6}" in md
    assert any(b[0] == "sema" and "<svg" in b[1]["kareler"][0]["svg"] for b in s.anlatim.bloklar)
    assert mo.son_anlatim is s.anlatim

    s = ta.kolon_kontrol_anlatimli([1500, 800], [150, 250], [0, 60], **KOLON, goster="yok")
    assert "6.3.10" in s.anlatim.markdown() and "Bresler" in s.anlatim.markdown()
    svgs = [k["svg"] for b in s.anlatim.bloklar if b[0] == "sema" for k in b[1]["kareler"]]
    assert len(svgs) == 2 and all(x.startswith("<svg") for x in svgs)

    for s in (ta.kiris_kesme_anlatimli(200, 0.30, 0.50, 0.04, goster="yok"),
              ta.kolon_etkilesim_anlatimli(**KOLON, goster="yok"),
              ta.kesit_sinifi_anlatimli("IPE 300", 275, goster="yok"),
              ta.celik_egilme_anlatimli("IPE 300", 275, 6.0, M_talep=80, goster="yok"),
              ta.celik_basinc_anlatimli("HEB 200", 275, 3, 3, P_talep=900, goster="yok"),
              ta.celik_kesme_anlatimli("IPE 300", 275, V_talep=100, goster="yok"),
              ta.celik_cekme_anlatimli("IPE 300", 275, 430, goster="yok"),
              ta.celik_eleman_kontrol_anlatimli("IPE 300", "S275", 5, kuvvetler={"N": 100, "Mx": 80}, goster="yok")):
        md = s.anlatim.markdown()
        assert "Ne yapıyoruz, neden?" in md and len(md) > 300
        assert json_temiz(s.veri)


def test_anlatimsiz_ve_anlatimli_ayni_sonuc():
    a = ta.celik_eleman_kontrol("IPE 300", "S275", 5, kuvvetler={"N": 100, "Mx": 80})
    b = ta.celik_eleman_kontrol_anlatimli("IPE 300", "S275", 5, kuvvetler={"N": 100, "Mx": 80}, goster="yok").veri
    assert a == b


# ============================================================================
# Öğretici hatalar
# ============================================================================
@pytest.mark.parametrize("cagri", [
    lambda: ta.kiris_egilme(100, -0.30, 0.50, 0.04),
    lambda: ta.kiris_egilme(100, 0.30, 0, 0.04),
    lambda: ta.kiris_egilme(100, 0.30, 0.50, 0.25),          # paspayı ≥ h/2
    lambda: ta.kiris_egilme(100, 30, 50, 0.04),              # cm girilmiş
    lambda: ta.kiris_egilme(100, 0.30, 0.50, 0.04, beton="C99"),
    lambda: ta.kiris_egilme(100, 0.30, 0.50, 0.04, donati="S999"),
    lambda: ta.kiris_kesme(100, 0.30, 0.50, 0.30),
    lambda: ta.kolon_etkilesim(0.4, 0.5, 24, 0.20),          # paspayı ≥ b/2
    lambda: ta.kolon_etkilesim(0.4, 0.5, -24, 0.05),
    lambda: ta.kolon_etkilesim(0.4, 0.5, 24, 0.05, yerlesim="uc_yuz"),
    lambda: ta.kolon_etkilesim(0.4, 0.5, 24, 0.05, n_cubuk=7),
    lambda: ta.kolon_etkilesim(0.4, 0.5, 24, 0.05, eksen="z"),
    lambda: ta.kolon_kontrol([1, 2], [1, 2, 3], 0, **KOLON),
    lambda: ta.kesit_sinifi("IPE 301", 275),
    lambda: ta.celik_egilme("HEX 200", 275, 3),
    lambda: ta.celik_egilme("IPE 300", 275, -3),
    lambda: ta.celik_basinc("HEB 200", 275, 0, 3),
    lambda: ta.celik_malzeme("S999"),
    lambda: ta.celik_egilme("IPE 300", 275, 3, yontem="LRFD"),
    lambda: ta.celik_eleman_kontrol("IPE 300", "S275", 3, kuvvetler=[1, 2]),
    lambda: ta.celik_cekme("IPE 300", 275, 430, An=80.0),     # An > Ag
])
def test_ogretici_hatalar(cagri):
    with pytest.raises(mo.MatrisHatasi):
        cagri()


def test_profil_adi_esnek():
    assert ta.kesit_sinifi("ipe300", 275)["profil"] == "IPE 300"
    assert ta.celik_egilme("IPE 300", "S275", 2.0)["Fy"] == 275


# ============================================================================
# Basit kesitler: kapalı form özellikler (ders kitabı / katalog değerleri)
# ============================================================================
def oran_yakin(a, b, oran):
    return abs(a - b) <= oran * abs(b)


def test_kavis_kapali_form_sayisal():
    """Köşe dolgusu (kare − çeyrek daire): a, c, I_kenar, I_xy kapalı formları sayısal integralle."""
    import numpy as np
    r, n = 1.0, 2000
    x = (np.arange(n) + 0.5) / n
    X, Y = np.meshgrid(x, x)
    m = (X - 1) ** 2 + (Y - 1) ** 2 >= 1
    dA = 1.0 / n ** 2
    A = m.sum() * dA
    p = ta._kavis(0, 0, 1, 1, r)
    assert p["A"] == pytest.approx(A, rel=1e-4)
    assert p["cx"] == pytest.approx((X * m).sum() * dA / A, rel=1e-4)
    assert p["Iy0"] + p["A"] * p["cz"] ** 2 == pytest.approx((Y ** 2 * m).sum() * dA, rel=1e-3)
    assert p["Iyz0"] + p["A"] * p["cx"] * p["cz"] == pytest.approx((X * Y * m).sum() * dA, rel=1e-3)


def test_kutu_keskin_kose_arastirma_formulleri():
    """r = 0: araştırmadaki RHS formülleri birebir (b = 100, h = 200, t = 6)."""
    k = ta.kesit_ozellik("kutu", {"H": 200, "B": 100, "t": 6, "r_o": 0, "r_i": 0})
    b, h, t = 100.0, 200.0, 6.0
    assert k["A"] * 100 == pytest.approx(b * h - (b - 2 * t) * (h - 2 * t))
    assert k["Iy"] * 1e4 == pytest.approx((b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12)
    assert k["Iz"] * 1e4 == pytest.approx((h * b ** 3 - (h - 2 * t) * (b - 2 * t) ** 3) / 12)
    assert k["Wply"] * 1e3 == pytest.approx((b * h ** 2 - (b - 2 * t) * (h - 2 * t) ** 2) / 4, rel=1e-6)
    assert k["Wplz"] * 1e3 == pytest.approx((h * b ** 2 - (h - 2 * t) * (b - 2 * t) ** 2) / 4, rel=1e-6)
    bredt = 2 * t * (b - t) ** 2 * (h - t) ** 2 / ((b - t) + (h - t))
    assert oran_yakin(k["It"] * 1e4, bredt, 0.01)          # + t³p/3 terimi kadar fark
    assert json_temiz(k)


def test_kutu_sicak_katalog():
    """SHS 100×100×5 (EN 10210-2, r_o = 1,5t, r_i = t): A = 18,7 cm², I = 279 cm⁴, W_el = 55,9, W_pl = 66,4 cm³."""
    k = ta.kesit_ozellik("KUTU 100x5")
    assert k["ad"] == "KUTU 100x100x5" and k["r_o"] == 7.5 and k["r_i"] == 5.0
    for ad, deger in (("A", 18.7), ("Iy", 279.0), ("Iz", 279.0), ("Wely", 55.9), ("Wply", 66.4), ("iy", 3.86)):
        assert oran_yakin(k[ad], deger, 0.02), (ad, k[ad], deger)
    s = ta.kesit_ozellik("kutu", {"H": 100, "B": 100, "t": 5, "imalat": "soguk"})
    assert s["t_tasarim"] == pytest.approx(4.65) and s["A"] < k["A"]          # ÇYTHYE 5.4.2: 0,93t


def test_boru_kesin():
    """CHS 168,3 × 6,3: A = 32,1 cm², I = 1053 cm⁴, W_el = 125, W_pl = 165 cm³, i = 5,73 cm, J = 2I."""
    k = ta.kesit_ozellik("BORU 168.3x6.3")
    D, t = 168.3, 6.3
    d = D - 2 * t
    assert k["A"] * 100 == pytest.approx(math.pi / 4 * (D ** 2 - d ** 2))
    assert k["Iy"] * 1e4 == pytest.approx(math.pi / 64 * (D ** 4 - d ** 4))
    assert k["Wply"] * 1e3 == pytest.approx((D ** 3 - d ** 3) / 6)
    assert k["It"] == pytest.approx(2 * k["Iy"])
    for ad, deger in (("A", 32.1), ("Iy", 1053.0), ("Wely", 125.0), ("Wply", 165.0), ("iy", 5.73)):
        assert oran_yakin(k[ad], deger, 0.02), (ad, k[ad], deger)


def test_korniyer_katalog():
    """L 100×100×10 (EN 10056-1): A = 19,15 cm², Iy = 176,7 cm⁴, iy = 3,04, e = 2,82, Wel = 24,62, Iu = 280,7, i_v = 1,95."""
    k = ta.kesit_ozellik("L 100x10")
    assert k["ad"] == "L 100x100x10" and k["r1"] == 12
    for ad, deger in (("A", 19.15), ("Iy", 176.7), ("Iz", 176.7), ("iy", 3.04), ("e", 2.82), ("Wely", 24.62),
                      ("Iu", 280.7), ("iv", 1.95), ("iu", 3.83)):
        assert oran_yakin(k[ad], deger, 0.02), (ad, k[ad], deger)
    assert k["Iu"] + k["Iv"] == pytest.approx(k["Iy"] + k["Iz"])      # asal eksen dönüşümünde iz korunur
    assert k["i_min"] == pytest.approx(k["iv"])
    # keskin köşe: A = t(2b − t)
    s = ta.kesit_ozellik("L", {"b": 100, "t": 10, "r1": 0, "r2": 0})
    assert s["A"] * 100 == pytest.approx(10 * 190) and s["e"] * 10 == pytest.approx(54500 / 1900)


def test_cift_korniyer_paralel_eksen():
    """2L 100×10, s = 10 mm: Iz = 2[I_L + A_L(e + s/2)²] (ders kitabı değerleriyle ±%2), iy = tek korniyerin iy'si."""
    k = ta.kesit_ozellik("2L 100x10 s=10")
    Iz_el = 2 * (176.7 + 19.15 * (2.82 + 0.5) ** 2)
    assert oran_yakin(k["Iz"], Iz_el, 0.02)
    assert oran_yakin(k["iz"], math.sqrt(Iz_el / 38.3), 0.02) and oran_yakin(k["iz"], 4.50, 0.02)
    assert oran_yakin(k["A"], 2 * 19.15, 0.01) and oran_yakin(k["iy"], 3.04, 0.02)
    tek = ta.kesit_ozellik("L 100x10")
    assert k["Iy"] == pytest.approx(2 * tek["Iy"]) and k["i_i"] == pytest.approx(tek["iv"])
    assert 0 < k["H_ftb"] < 1 and json_temiz(k)


def test_upn_katalog():
    """UPN 200 (konik başlık modellenir): A = 32,2 cm², Iy = 1910, Iz = 148 cm⁴, e = 2,01 cm (±%3)."""
    k = ta.kesit_ozellik("UPN 200")
    for ad, deger in (("A", 32.2), ("Iy", 1910.0), ("Iz", 148.0), ("e_ag", 2.01), ("iz", 2.14)):
        assert oran_yakin(k[ad], deger, 0.03), (ad, k[ad], deger)


def test_standart_listeler_ve_adlar():
    for aile, adlar in ta.STANDART_KESITLER.items():
        assert len(adlar) >= 10
        for ad in adlar:
            k = ta.kesit_ozellik(ad)
            assert k["ad"] == ad and k["A"] > 0 and k["i_min"] > 0 and json_temiz(k)


# ============================================================================
# Çapraz / kafes çubuğu (ÇYTHYE Bölüm 7–8)
# ============================================================================
def _fcr(Fy, Fe):
    return 0.658 ** (Fy / Fe) * Fy if Fy / Fe <= 2.25 else 0.877 * Fe


def test_capraz_kutu_cekme_basinc_el_hesabi():
    """KUTU 100×5, S275, L = 4 m: Pc = 0,9 Fcr A (eğilmeli), Tc = min(0,9 Fy A, 0,75 Fu U An)."""
    k = ta.kesit_ozellik("KUTU 100x5")
    A, i = k["A"] * 100, k["iy"] * 10
    r = ta.celik_cubuk_kontrol("KUTU 100x5", "S275", 4.0, kuvvetler=[{"ad": "B", "N": 200}, {"ad": "Ç", "N": -300}],
                               An=15.0, U=0.9)
    lam = 4000 / i
    Fe = math.pi ** 2 * E / lam ** 2
    Pc = 0.9 * _fcr(275, Fe) * A / 1e3
    assert r["basinc"]["Pc_kN"] == pytest.approx(Pc, rel=1e-9) and Pc == pytest.approx(248.0, abs=0.5)
    Tc = min(0.9 * 275 * A, 0.75 * 430 * 0.9 * 1500) / 1e3
    assert r["cekme"]["Tc_kN"] == pytest.approx(Tc) and r["cekme"]["belirleyici"] == "kırılma"
    b, c = r["kombinasyonlar"]
    assert b["dc"] == pytest.approx(200 / Pc) and c["dc"] == pytest.approx(300 / Tc)
    assert r["dc"] == pytest.approx(max(200 / Pc, 300 / Tc, lam / 200, 4000 / i / 300))
    assert r["sinif"]["basinc"] == "narin olmayan" and json_temiz(r)
    g = ta.celik_cubuk_kontrol("KUTU 100x5", "S275", 4.0, kuvvetler={"N": 200}, yontem="GKT")
    assert g["basinc"]["Pc_kN"] == pytest.approx(_fcr(275, Fe) * A / 1e3 / 1.67)


def test_capraz_I_profil_celik_basinc_ile_ayni():
    r = ta.celik_cubuk_kontrol("HEB 200", "S275", 3.5, kuvvetler={"N": 500})
    b = ta.celik_basinc("HEB 200", 275, 3.5, 3.5)
    assert r["basinc"]["Pc_kN"] == pytest.approx(b["Pc_kN"]) and r["tip"] == "I"


def test_korniyer_basinc_bicimleri():
    """L 80×8: genel → v ekseni eğilmeli; düzlem kafes → Lc/i = 72 + 0,75 L/i_a (L/i_a ≤ 80) ya da 32 + 1,25 L/i_a."""
    k = ta.kesit_ozellik("L 80x8")
    r = ta.celik_cubuk_kontrol("L 80x8", "S275", 2.0, kuvvetler={"N": 50})
    Fe_v = math.pi ** 2 * E / (2000 / (k["iv"] * 10)) ** 2
    assert r["basinc"]["Fe_MPa"] <= Fe_v + 1e-9 and "v (zayıf asal)" in r["basinc"]["belirleyen"]
    assert r["basinc"]["Pc_kN"] == pytest.approx(0.9 * _fcr(275, r["basinc"]["Fe_MPa"]) * k["A"] * 100 / 1e3)
    assert any("8.3" in u for u in r["uyarilar"])
    for L in (1.5, 3.0):
        d = ta.celik_cubuk_kontrol("L 80x8", "S275", L, kuvvetler={"N": 50}, korniyer="duzlem")
        La = L * 1000 / (k["iy"] * 10)
        lam = 72 + 0.75 * La if La <= 80 else 32 + 1.25 * La
        assert d["basinc"]["etkin_narinlik"] == pytest.approx(lam)
        assert d["basinc"]["Fe_MPa"] == pytest.approx(math.pi ** 2 * E / lam ** 2)
    u = ta.celik_cubuk_kontrol("L 80x8", "S275", 3.0, kuvvetler={"N": 50}, korniyer="uzay")
    La = 3000 / (k["iy"] * 10)
    assert u["basinc"]["etkin_narinlik"] == pytest.approx(60 + 0.8 * La if La <= 75 else 45 + La)


def test_cift_korniyer_egilmeli_burulmali_el_hesabi():
    """2L 70×7: Denk. 8.6 (simetri ekseni + burulma; C_w ihmal, Denk. 8.14) ve yapma etkin narinlik (8.21)."""
    k = ta.kesit_ozellik("2L 70x7 s=10")
    L, a = 2500.0, 0.9
    r = ta.celik_cubuk_kontrol("2L 70x7 s=10", "S275", L / 1000, kuvvetler={"N": 100}, a_bag=a)
    A, iz, ii = k["A"] * 100, k["iz"] * 10, k["i_i"] * 10
    lz0 = L / iz
    ai = a * 1000 / ii
    lzm = math.sqrt(lz0 ** 2 + (0.5 * ai) ** 2) if ai > 40 else lz0
    Fez = math.pi ** 2 * E / lzm ** 2
    Fet = 77200 * k["It"] * 1e4 / (A * (k["io"] * 10) ** 2)
    H = k["H_ftb"]
    Fe_ftb = (Fez + Fet) / (2 * H) * (1 - math.sqrt(1 - 4 * Fez * Fet * H / (Fez + Fet) ** 2))
    Fe_y = math.pi ** 2 * E / (L / (k["iy"] * 10)) ** 2
    assert r["basinc"]["Fe_MPa"] == pytest.approx(min(Fe_ftb, Fe_y), rel=1e-9)
    assert Fe_ftb < Fez                                   # burulma etkisi kapasiteyi düşürür
    assert r["basinc"]["KLr_zm"] == pytest.approx(lzm)


def test_upn_egilmeli_burulmali():
    k = ta.kesit_ozellik("UPN 160")
    r = ta.celik_cubuk_kontrol("UPN 160", "S275", 2.0, K=(1.0, 0.5), kuvvetler={"N": 100})
    Fey = math.pi ** 2 * E / (2000 / (k["iy"] * 10)) ** 2
    ftb = [m for m in r["basinc"]["modlar"] if "burulmalı" in m["ad"]][0]
    assert ftb["Fe"] < Fey and r["basinc"]["Fe_MPa"] == pytest.approx(min(m["Fe"] for m in r["basinc"]["modlar"]))


def test_yalniz_cekme_capraz():
    r = ta.celik_cubuk_kontrol("BORU 76.1x3.2", "S275", 6.0, kuvvetler=[{"ad": "+X", "N": 80}, {"ad": "-X", "N": -60}],
                               yalniz_cekme=True)
    assert r["basinc"] is None and r["narinlik"]["basinc"] is None
    b, c = r["kombinasyonlar"]
    assert b["dc"] == 0.0 and "devre dışı" in b["not"]
    assert c["dc"] == pytest.approx(60 / r["cekme"]["Tc_kN"])
    assert not any("KL/i ≤ 200" in k["ad"] for k in r["kontroller"])
    assert any("L/i ≤ 300" in k["ad"] for k in r["kontroller"]) and any("Yalnız çekme" in u for u in r["uyarilar"])
    assert json_temiz(r)
    # aynı çubuk basınçta çalışsaydı narinlik 200'ü aşardı
    n = ta.celik_cubuk_kontrol("BORU 76.1x3.2", "S275", 6.0, kuvvetler=[{"N": 80}])
    assert n["durum"] == "kesit büyüt"


def test_narinlik_kosulu_asimi():
    k = ta.kesit_ozellik("L 50x5")
    r = ta.celik_cubuk_kontrol("L 50x5", "S275", 3.0, kuvvetler={"N": 5})
    oran = 3000 / (k["iv"] * 10)
    nk = [x for x in r["kontroller"] if x["ad"].startswith("Narinlik KL/i")][0]
    assert nk["talep"] == pytest.approx(oran) and oran > 200 and not nk["saglandi"]
    assert r["durum"] == "kesit büyüt" and "8.1.1" in nk["kaynak"]
    # çekme: L/i ≤ 300; kullanıcı sınırı
    c = ta.celik_cubuk_kontrol("L 50x5", "S275", 3.0, kuvvetler={"N": -5}, narinlik={"cekme": 250})
    ck = [x for x in c["kontroller"] if x["ad"].startswith("Narinlik L/i")][0]
    assert ck["kapasite"] == 250 and ck["talep"] == pytest.approx(oran) and not ck["saglandi"]
    assert not any(x["ad"].startswith("Narinlik KL/i") for x in c["kontroller"])


def test_tbdy_capraz_kosullari():
    r = ta.celik_cubuk_kontrol("BORU 114.3x4", "S275", 4.0, kuvvetler=[{"N": 100}, {"N": -100}],
                               tbdy_capraz={"suneklik": "SDS", "duzen": "ters_V"})
    sinir = [x for x in r["kontroller"] if "4,0√(E/Fy)" in x["ad"]][0]
    assert sinir["kapasite"] == pytest.approx(4.0 * math.sqrt(E / 275)) and "9.7.3.1" in sinir["kaynak"]
    t93 = [x for x in r["kontroller"] if "Tablo 9.3" in x["ad"]][0]
    assert t93["kapasite"] == pytest.approx(0.044 * E / 275)
    y = ta.celik_cubuk_kontrol("BORU 114.3x4", "S275", 4.0, kuvvetler=[{"N": -100}], yalniz_cekme=True,
                               tbdy_capraz={"suneklik": "SDY", "duzen": "X"})
    assert any("9.6.4.3" in x["ad"] and not x["saglandi"] for x in y["kontroller"]) and y["durum"] == "kesit büyüt"
    kd = ta.celik_cubuk_kontrol("BORU 114.3x4", "S275", 4.0, kuvvetler=[{"N": 10}],
                                tbdy_capraz={"suneklik": "SDS", "duzen": "K"})
    assert any("K düzeni" in x["ad"] and not x["saglandi"] for x in kd["kontroller"])


def test_basit_kesit_siniflari():
    q = math.sqrt(E / 275)
    s = ta.celik_cubuk_kontrol("KUTU 300x300x10", "S275", 3, kuvvetler={"N": 10})["sinif"]
    assert s["parcalar"][0]["oran"] == pytest.approx((300 - 30) / 10) and s["parcalar"][0]["lambda_r_basinc"] == \
        pytest.approx(1.40 * q) and s["basinc"] == "narin olmayan"
    ince = ta.celik_cubuk_kontrol({"tip": "kutu", "H": 300, "B": 300, "t": 5}, "S275", 3, kuvvetler={"N": 10})
    assert ince["sinif"]["basinc"] == "narin" and any("8.5" in u for u in ince["uyarilar"])
    s = ta.celik_cubuk_kontrol("L 100x10", "S275", 2, kuvvetler={"N": 10})["sinif"]
    assert s["parcalar"][0]["lambda_r_basinc"] == pytest.approx(0.45 * q) and s["parcalar"][0]["durum_basinc"] == "Durum 3"
    s = ta.celik_cubuk_kontrol("BORU 406.4x10", "S355", 2, kuvvetler={"N": 10})["sinif"]
    assert s["parcalar"][0]["lambda_r_basinc"] == pytest.approx(0.11 * E / 355)
    s = ta.celik_cubuk_kontrol("2L 100x10 s=0", "S275", 2, kuvvetler={"N": 10})["sinif"]
    assert s["parcalar"][0]["durum_basinc"] == "Durum 1"


# ============================================================================
# İki eksenli eğilme (aşık, kren kirişi)
# ============================================================================
def test_asik_iki_eksenli_etkilesim_el_hesabi():
    """IPE 200 aşık, eğim 15°, L = 5 m, üst başlık tutulu (Lb = 0): D/C = Mx/Mcx + My/Mcy (Denk. 11.1b, Pr = 0);
    Mcx = 0,9 Fy Wpl,y (Denk. 9.2), Mcy = 0,9 min(Fy Wpl,z; 1,6 Fy Wel,z) (Denk. 9.39)."""
    q, a, L = 4.0, math.radians(15), 5.0
    Mx, My = q * math.cos(a) * L ** 2 / 8, q * math.sin(a) * L ** 2 / 8
    r = ta.celik_eleman_kontrol("IPE 200", "S275", L, Lb=0.0, kuvvetler={"ad": "G+S", "Mx": Mx, "My": My})
    Mcx = 0.9 * 275 * 220.6e3 / 1e6
    Mcy = 0.9 * min(275 * 44.61e3, 1.6 * 275 * 28.47e3) / 1e6
    c = r["kombinasyonlar"][0]
    assert c["dal"] == "11.1b" and c["dc_etkilesim"] == pytest.approx(Mx / Mcx + My / Mcy, rel=1e-9)
    assert not any("Narinlik" in k["ad"] for k in r["kontroller"])      # eksenel kuvvet yok → narinlik koşulu yok
    # küçük eksenel basınç (Pr/Pc < 0,2): Pr/(2Pc) eklenir
    r2 = ta.celik_eleman_kontrol("IPE 200", "S275", L, Lb=0.0, kuvvetler={"N": 4, "Mx": Mx, "My": My})
    c2 = r2["kombinasyonlar"][0]
    assert c2["dal"] == "11.1b" and 4 / r2["basinc"]["Pc_kN"] < 0.2
    assert c2["dc_etkilesim"] == pytest.approx(4 / (2 * r2["basinc"]["Pc_kN"]) + Mx / Mcx + My / Mcy, rel=1e-9)
    assert any("Narinlik KL/i" in k["ad"] for k in r2["kontroller"])
    # Pr/Pc ≥ 0,2: 11.1a
    r3 = ta.celik_eleman_kontrol("IPE 200", "S275", L, Lb=0.0, kuvvetler={"N": 30, "Mx": Mx, "My": My})
    Pc = r3["basinc"]["Pc_kN"]
    assert r3["kombinasyonlar"][0]["dal"] == "11.1a"
    assert r3["kombinasyonlar"][0]["dc_etkilesim"] == pytest.approx(30 / Pc + 8 / 9 * (Mx / Mcx + My / Mcy))


def test_kren_ust_baslik_yaklasimi():
    k = {"Mx": 120, "My": 8}
    a = ta.celik_eleman_kontrol("HEA 300", "S275", 6, Lb=6, kuvvetler=k)
    b = ta.celik_eleman_kontrol("HEA 300", "S275", 6, Lb=6, kuvvetler=k, kren=True)
    assert b["Mcy_kullanilan_kNm"] == pytest.approx(a["egilme"]["Mcy_kNm"] / 2)
    ox = 120 / a["egilme"]["Mc_kNm"]
    assert b["kombinasyonlar"][0]["dc_etkilesim"] == pytest.approx(ox + 8 / (a["egilme"]["Mcy_kNm"] / 2))
    assert b["kombinasyonlar"][0]["dc"] > a["kombinasyonlar"][0]["dc"]
    assert any("Kren" in u for u in b["uyarilar"]) and json_temiz(b)


# ============================================================================
# Kesit önerisi
# ============================================================================
@pytest.mark.skipif(not GERCEK_KUTUPHANE, reason="tüm profil kataloğu (yapi_veri.py) gerekli")
def test_celik_oner_ipe_kiris_monoton():
    """Lb = 0, Mx = 220 kN·m: IPE 300 (Mc = 155,5) ve IPE 330 (Mc = 199,1) yetmez → IPE 360 (Mc = 252,2)."""
    kuv = [{"ad": "K1", "Mx": 220, "V": 150}]
    par = {"L": 6.0, "Lb": 0.0}
    r = ta.celik_kesit_oner("IPE", "S275", par, kuv, baslangic="IPE 300")
    assert r["oneri"] == "IPE 360" and r["durum"] == "bulundu" and r["degisim"] == "büyüt"
    assert r["mevcut"]["ad"] == "IPE 300" and r["mevcut"]["dc"] == pytest.approx(220 / (0.9 * 275 * 628.4e3 / 1e6))
    assert r["dc"] == pytest.approx(220 / (0.9 * 275 * 1019e3 / 1e6))
    g = {ad: p["g"] for ad, p in ta.yv.PROFILLER.items()}
    # bağımsız monotonluk: önerilenden hafif bütün IPE'ler D/C > 1
    for ad in (a for a in g if a.startswith("IPE ") and g[a] < g["IPE 360"]):
        assert ta.celik_eleman_kontrol(ad, "S275", 6.0, Lb=0.0, kuvvetler=kuv)["dc"] > 1.0, ad
    assert [d["ad"] for d in r["denenenler"]][-1] == "IPE 360" and all(not d["yeterli"] for d in r["denenenler"][:-1])
    w = [d["agirlik_kg_m"] for d in r["denenenler"]]
    assert w == sorted(w) and r["agirlik_kg_m"] == g["IPE 360"]
    assert {a["aile"] for a in r["alternatifler"]} == {"HEA", "HEB"} and all(a["oneri"] for a in r["alternatifler"])
    assert r["aile_degistir"] is None                     # HEA/HEB, IPE 360'tan ağır
    assert "IPE 330" in " ".join(r["gerekce"]) and json_temiz(r)
    # aile adı yerine profil adı
    assert ta.celik_kesit_oner("IPE 300", "S275", par, kuv)["oneri"] == "IPE 360"


@pytest.mark.skipif(not GERCEK_KUTUPHANE, reason="tüm profil kataloğu (yapi_veri.py) gerekli")
def test_celik_oner_aile_degistir():
    """Mx = 1500 kN·m: IPE 600 bile yetmez (Mc = 869 kN·m) → HEB/HEA önerilir."""
    r = ta.celik_kesit_oner("IPE", "S275", {"L": 6.0, "Lb": 0.0}, [{"Mx": 1500}])
    assert r["oneri"] is None and r["durum"] == "ailede yeterli profil yok"
    assert r["aile_degistir"] is not None and r["aile_degistir"]["aile"] in ("HEA", "HEB")
    ad = r["aile_degistir"]["oneri"]
    assert ta.celik_eleman_kontrol(ad, "S275", 6.0, Lb=0.0, kuvvetler=[{"Mx": 1500}])["dc"] <= 1.0


def test_celik_oner_eksenel_aileler():
    kuv = [{"ad": "B", "N": 300}, {"ad": "Ç", "N": -250}]
    r = ta.celik_kesit_oner("BORU", "S275", {"L": 5.0}, kuv)
    assert r["kontrol"] == "cubuk" and r["oneri"] is not None
    liste = ta.STANDART_KESITLER["BORU"]
    g = {ad: ta.kesit_ozellik(ad)["g"] for ad in liste}
    for ad in (a for a in liste if g[a] < g[r["oneri"]]):
        assert ta.celik_cubuk_kontrol(ad, "S275", 5.0, kuvvetler=kuv)["dc"] > 1.0, ad
    assert {a["aile"] for a in r["alternatifler"]} == {"KUTU", "L", "2L", "UPN"}
    assert json_temiz(r)
    # 2L ailesi yalnız çekme parametresiyle
    y = ta.celik_kesit_oner("2L", "S275", {"L": 5.0, "yalniz_cekme": True, "An_oran": 0.85, "U": 0.85},
                            [{"N": -250}, {"N": 50}], aile_degistir=False)
    assert y["oneri"] is not None and y["alternatifler"] == []


# ============================================================================
# Betonarme: eğik eleman ve kesit önerisi
# ============================================================================
def test_betonarme_egik_eleman_yol_secimi():
    kuv = [{"ad": "K1", "N": 50, "Mx": 120, "V": 90}, {"ad": "K2", "N": 600, "Mx": -150, "V": 120}]
    r = ta.betonarme_eleman_kontrol(0.30, 0.50, 0.04, "C30", "B420C", kuv, tur="egik")
    assert r["esik_kN"] == pytest.approx(0.1 * 30 * 300 * 500 / 1e3)          # 450 kN
    k1, k2 = r["kombinasyonlar"]
    assert k1["yol"] == "eğilme" and k2["yol"] == "N–M"
    eg = ta.kiris_egilme(120, 0.30, 0.50, 0.04, "C30", "B420C")
    assert r["egilme_alt"]["As_gerekli_cm2"] == pytest.approx(eg["As_gerekli_cm2"])
    assert r["kolon"] is not None and r["kolon"]["noktalar"][0]["Nd_kN"] == 600
    assert r["As_kaynak"].startswith("ρ taraması") and json_temiz(r)
    # aynı kuvvetler kiriş diye verilirse eksenel koşul aşılır
    k = ta.betonarme_eleman_kontrol(0.30, 0.50, 0.04, "C30", "B420C", kuv, tur="kiris")
    assert k["durum"] == "kesit büyüt" and any("kolon gibi" in u for u in k["uyarilar"])
    # kolon: kolon_kontrol ile aynı N–M sonucu
    c = ta.betonarme_eleman_kontrol(0.40, 0.50, 0.05, "C30", "B420C", [{"N": 1500, "Mx": 150, "My": 30, "V": 80}],
                                    tur="kolon", As_toplam=24)
    kk = ta.kolon_kontrol(1500, 150, 30, 0.40, 0.50, 24, 0.05)
    assert c["kombinasyonlar"][0]["dc"] >= kk["noktalar"][0]["dc"] - 1e-12 and c["kesme"] is not None


def test_betonarme_kolon_oner_el_hesabi():
    """C30: N_dm = 2000 kN → A_c ≥ 2000·10³/(0,40·30) = 166 667 mm²; N_d = 2400 kN → 2400·10³/(0,9·20) = 133 333 mm².
    5 cm adımlı, en küçük boyut ≥ 300 mm, en/boy ≤ 3 → en küçük alan 350 × 500 = 175 000 mm²."""
    kuv = [{"ad": "G+Q", "N": 2400, "Mx": 60, "My": 30, "deprem": False},
           {"ad": "G+Q+E", "N": 2000, "Mx": 90, "My": 40, "deprem": True}]
    r = ta.betonarme_kesit_oner("kolon", kuv, {"beton": "C30", "donati": "B420C"})
    assert r["A_c_TBDY_cm2"] == pytest.approx(2000e3 / 12 / 100) and r["A_c_TS500_cm2"] == pytest.approx(2400e3 / 18 / 100)
    assert r["A_c_gerekli_cm2"] == pytest.approx(1666.667, abs=1e-3)
    o = r["oneri"]
    assert sorted((o["b_mm"], o["h_mm"])) == [350, 500] and o["A_c_cm2"] == 1750
    assert 0.01 <= o["rho"] <= 0.04
    kk = ta.kolon_kontrol([2400, 2000], [60, 90], [30, 40], o["b"], o["h"], o["As_cm2"], 0.05, tbdy=True,
                          deprem=[False, True])
    assert kk["dc"] <= 1.0 + 1e-9
    assert any("7.3.1.2" in g for g in r["gerekce"]) and json_temiz(r)


def test_betonarme_kolon_oner_ndm_dis_degeri():
    """K-42: N_dm dışarıdan (Ndm, Ndm_kaynak): sözde kuvvet eklemeden TBDY 7.3.1.2 boyutlandırması ve gerekçe ifadesi."""
    kuv = [{"ad": "G+Q", "N": 1400, "Mx": 60, "My": 30, "deprem": False},
           {"ad": "G+Q+E", "N": 1500, "Mx": 90, "My": 40, "deprem": True}]
    r0 = ta.betonarme_kesit_oner("kolon", kuv)
    assert r0["N_dm_kN"] == pytest.approx(1500.0)
    r = ta.betonarme_kesit_oner("kolon", kuv, Ndm=2000.0, Ndm_kaynak="deprem")          # ön elemede düşen deprem birleşimi
    assert r["N_dm_kN"] == pytest.approx(2000.0) and r["A_c_TBDY_cm2"] == pytest.approx(2000e3 / 12 / 100)
    assert r["N_d_kN"] == pytest.approx(2000.0)                                          # N_d en az N_dm
    assert any("(N_dm = deprem birleşimlerindeki en büyük eksenel basınç)" in g for g in r["gerekce"])
    r = ta.betonarme_kesit_oner("kolon", kuv, Ndm=1000.0)                                 # küçükse kuvvetlerdeki büyük olan
    assert r["N_dm_kN"] == pytest.approx(1500.0)
    kuv_d = [dict(k, deprem=False) for k in kuv]
    r = ta.betonarme_kesit_oner("kolon", kuv_d, Ndm=1100.0, Ndm_kaynak="G+Q")             # deprem birleşimi yok: G + Q
    assert r["N_dm_kN"] == pytest.approx(1100.0) and r["A_c_TBDY_cm2"] == pytest.approx(1100e3 / 12 / 100)
    assert any("(deprem birleşimi yok: N_dm ≈ G + Q, tasarım kaydının 'Ndm ≤ 0,40 fck Ac' satırıyla aynı)" in g for g in r["gerekce"])
    r = ta.betonarme_kesit_oner("kolon", kuv_d, Ndm=1500.0, Ndm_kaynak="bütün")
    assert any("(deprem birleşimi yok: bütün birleşimlerin en büyük eksenel basıncı)" in g for g in r["gerekce"])
    assert not any("deprem' işareti yok" in u for u in r["uyarilar"]) and json_temiz(r)


def test_betonarme_kolon_oner_nm_belirleyici():
    kuv = [{"ad": "E", "N": 900, "Mx": 420, "My": 0, "deprem": True}]
    r = ta.betonarme_kesit_oner("kolon", kuv, kisitlar={"deneme_siniri": 200})
    o = r["oneri"]
    assert o is not None and o["A_c_cm2"] >= r["A_c_gerekli_cm2"]
    alanlar = [d["A_c_cm2"] for d in r["denenenler"]]
    assert alanlar == sorted(alanlar) and len(alanlar) > 1
    assert all(not d["yeterli"] for d in r["denenenler"][:-1]) and r["denenenler"][-1]["yeterli"]


def test_betonarme_kiris_h_oner_el_hesabi():
    """C30/B420C, b = 300, paspayı 40: M_d = 180 kN·m. h = 350 (d = 310): ρ = 0,0226 > ρ_max = 0,02 ✗; h = 400 ✓."""
    kuv = [{"ad": "mesnet", "Mx": -180, "V": 160}, {"ad": "açıklık", "Mx": 120, "V": 100}]
    r = ta.betonarme_kesit_oner("kiris", kuv, mevcut_b=0.30)
    fcd, fyd = 20.0, 420 / 1.15

    def rho(d):
        R = 0.85 * fcd * 300
        a = d - math.sqrt(d * d - 2 * 180e6 / R)
        return R * a / fyd / (300 * d)

    assert rho(310) > 0.02 > rho(360)
    assert r["oneri"]["b_mm"] == 300 and r["oneri"]["h_mm"] == 400 and r["oneri"]["h"] == pytest.approx(0.40)
    son = r["denenenler"][-1]
    assert son["rho_gerekli"] == pytest.approx(rho(360)) and son["V_max_kN"] == pytest.approx(0.22 * 20 * 300 * 360 / 1e3)
    assert r["rho_max"] == pytest.approx(min(0.85 * ta._rho_b(ta.beton_malzeme("C30"), ta.donati_malzeme("B420C")), 0.02))
    assert r["oneri"]["As_gerekli_cm2"] == pytest.approx(ta.kiris_egilme(180, 0.3, 0.4, 0.04)["As_gerekli_cm2"])
    # döşeme kalınlığı TBDY h ≥ 3 t_f
    r2 = ta.betonarme_kesit_oner("kiris", kuv, mevcut_b=0.30, kisitlar={"doseme_kalinligi": 0.15})
    assert r2["oneri"]["h_mm"] == 450 and r2["h_min_mm"] == 450
    # dar kiriş: h ≤ 3,5 b → b büyütülür
    r3 = ta.betonarme_kesit_oner("kiris", [{"Mx": 1300, "V": 300}], kisitlar={"b": 0.25})
    assert r3["oneri"]["h_mm"] <= 3.5 * r3["oneri"]["b_mm"] + 1e-9 and r3["oneri"]["b_mm"] > 250
    assert json_temiz(r) and json_temiz(r3)


def test_yeni_anlatimli_sarmalayicilar():
    for s in (ta.celik_cubuk_kontrol_anlatimli("2L 70x7", "S275", 3, kuvvetler=[{"N": 100}, {"N": -80}], goster="yok"),
              ta.celik_cubuk_kontrol_anlatimli("BORU 114.3x4", "S275", 3, kuvvetler=[{"N": 100}], goster="yok"),
              ta.betonarme_kesit_oner_anlatimli("kiris", [{"Mx": 180, "V": 160}], goster="yok"),
              ta.betonarme_kesit_oner_anlatimli("kolon", [{"N": 2000, "Mx": 100}], goster="yok"),
              ta.betonarme_eleman_kontrol_anlatimli(0.3, 0.5, 0.04, kuvvetler=[{"N": 50, "Mx": 120, "V": 90}],
                                                    tur="egik", goster="yok")):
        md = s.anlatim.markdown()
        assert "Ne yapıyoruz, neden?" in md and len(md) > 800 and json_temiz(s.veri)
    s = ta.celik_cubuk_kontrol_anlatimli("KUTU 100x5", "S275", 3, kuvvetler=[{"N": 100}], goster="yok")
    assert any(b[0] == "sema" and "<svg" in b[1]["kareler"][0]["svg"] for b in s.anlatim.bloklar)
    assert s.veri == ta.celik_cubuk_kontrol("KUTU 100x5", "S275", 3, kuvvetler=[{"N": 100}])


@pytest.mark.skipif(not GERCEK_KUTUPHANE, reason="tüm profil kataloğu (yapi_veri.py) gerekli")
def test_celik_oner_anlatimli_deneme_tablosu():
    s = ta.celik_kesit_oner_anlatimli("IPE", "S275", {"L": 6.0, "Lb": 0.0}, [{"Mx": 220}], goster="yok")
    md = s.anlatim.markdown()
    assert "Deneme tablosu" in md and "IPE 330" in md and "IPE 360" in md and s.veri["oneri"] == "IPE 360"


@pytest.mark.parametrize("cagri", [
    lambda: ta.kesit_ozellik("KUTU 100"),
    lambda: ta.kesit_ozellik("L 100x80x10"),                 # eşit olmayan kollar
    lambda: ta.kesit_ozellik("UPN 190"),
    lambda: ta.kesit_ozellik("kutu", {"H": 100, "B": 100, "t": 60}),
    lambda: ta.kesit_ozellik("altigen", {"a": 1}),
    lambda: ta.celik_cubuk_kontrol("L 80x8", "S275", 3, korniyer="egik"),
    lambda: ta.celik_cubuk_kontrol("L 80x8", "S275", 3, U=1.2),
    lambda: ta.celik_cubuk_kontrol("L 80x8", "S275", 3, narinlik={"burkulma": 100}),
    lambda: ta.celik_cubuk_kontrol("BORU 114.3x4", "S275", 3, tbdy_capraz={"suneklik": "SDX"}),
    lambda: ta.celik_kesit_oner("IPX", "S275", {}, [{"N": 10}]),
    lambda: ta.celik_kesit_oner("IPE", "S275", {"An": 10}, [{"N": 10}]),
    lambda: ta.celik_kesit_oner("IPE", "S275", {}, None),
    lambda: ta.celik_kesit_oner("BORU", "S275", {"kontrol": "eleman"}, [{"N": 10}]),
    lambda: ta.betonarme_eleman_kontrol(0.3, 0.5, kuvvetler=[{"Mx": 10}], tur="perde"),
    lambda: ta.betonarme_kesit_oner("doseme", [{"Mx": 10}]),
    lambda: ta.betonarme_kesit_oner("kiris", [{"Mx": 10}], kisitlar={"genislik": 0.3}),
])
def test_yeni_ogretici_hatalar(cagri):
    with pytest.raises(mo.MatrisHatasi):
        cagri()


@pytest.mark.parametrize("ad", ["UPN 200", "KUTU 100x5", "L 80x8", "2L 70x7 s=12", "BORU 114.3x4"])
def test_kesit_ozellik_sozlugu_cubuga_verilebilir(ad):
    k = ta.kesit_ozellik(ad)
    a = ta.celik_cubuk_kontrol(k, "S275", 3, kuvvetler={"N": 50})
    b = ta.celik_cubuk_kontrol(ad, "S275", 3, kuvvetler={"N": 50})
    assert a["profil"] == b["profil"] and a["basinc"]["Pc_kN"] == pytest.approx(b["basinc"]["Pc_kN"])
    assert a["ozellik"]["A"] == pytest.approx(k["A"])
