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
