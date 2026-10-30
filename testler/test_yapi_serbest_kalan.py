# -*- coding: utf-8 -*-
"""yapi_serbest.py kalan işler: Bresler satırının D/C'ye girmesi (K-2) ve genel motorun diğer kalan maddeleri."""
from __future__ import annotations

import copy
import functools

import pytest

import yapi
import yapi_serbest as YS


def coz(b, anlat=False):
    return yapi.bina_coz(b, goster="yok", anlat=anlat)


def _kolon30(b):
    b["kesitler"]["B30x30"] = {"tip": "dikdortgen", "b": 0.3, "h": 0.3, "malzeme": "C30", "donati": "B420C", "pas": 0.03}
    for k in b["kolonlar"]:
        k["kesit"] = "B30x30"
    return b


@functools.lru_cache(maxsize=None)
def _iki_motor(ad, kolon30=False):
    """(aks–kat veri, genel veri) — aynı aks–kat şablonu iki motorla (genel: surum 3, Python dönüştürücü)."""
    b = yapi.bina_sablon(ad)
    if kolon30:
        _kolon30(b)
    v1 = coz(copy.deepcopy(b)).veri
    b["surum"] = 3
    v3 = coz(b).veri
    assert v1.get("model") != "genel" and v3["model"] == "genel"
    return v1, v3


def _eslesen(v1, v3, tur=None):
    s1 = {(k["tur"], k["no"]): k for k in v1["tasarim"]["elemanlar"]}
    for k in v3["tasarim"]["elemanlar"]:
        if tur and k["tur"] != tur:
            continue
        kay = k.get("kaynak") or {}
        a = s1.get((kay.get("aks_kat"), kay.get("no")))
        if a is not None and a["dc"] is not None and k["dc"] is not None:
            yield a, k


# ---------------------------------------------------------------------------
# K-2: iki eksenli eğilme (Bresler) satırı genel motorda da D/C'ye girer
# ---------------------------------------------------------------------------
def test_kontrol_kuyrugu_onekleri():
    adlar = sorted(["1.4G+1.6Q", "G+Q+EX+", "G+Q"], key=len, reverse=True)
    k = YS._kontrol_kuyrugu
    assert k("N–M: 1.4G+1.6Q: İki eksenli eğilme (Bresler: 1/Nr = 1/Nrx + 1/Nry − 1/N0)", adlar) == \
        "İki eksenli eğilme (Bresler: 1/Nr = 1/Nrx + 1/Nry − 1/N0)"
    assert k("N–M: G+Q+EX+: TBDY: Ndm ≤ 0,40 fck Ac", adlar) == "TBDY: Ndm ≤ 0,40 fck Ac"     # en uzun kombinasyon adı
    assert k("N–M: Boyuna donatı ρ ≥ 0,01", adlar) == "Boyuna donatı ρ ≥ 0,01"
    assert k("Kesme (G+Q): Kesme dayanımı Vd ≤ Vc + Vw", adlar) == "Kesme dayanımı Vd ≤ Vc + Vw"
    assert k("Kesme (bilinmeyen): Kesme üst sınırı Vd ≤ 0,22 fcd bw d", adlar) == "Kesme üst sınırı Vd ≤ 0,22 fcd bw d"
    assert k("Açıklık (alt donatı): TBDY: bw ≥ 250 mm", adlar) == "TBDY: bw ≥ 250 mm"
    assert k("Eğilme elemanı koşulu |N_d| ≤ 0,1 f_ck A_c", adlar) == "Eğilme elemanı koşulu |N_d| ≤ 0,1 f_ck A_c"


def test_bresler_satiri_dc_ye_girer_3x3_kolon30():
    v1, v3 = _iki_motor("betonarme-3kat-3x3", True)
    a, k = next((a, k) for a, k in _eslesen(v1, v3, "kolon") if k["kaynak"]["no"] == 5)
    assert a["belirleyen"]["kontrol"] == "N–M"
    assert k["dc"] == pytest.approx(a["dc"], rel=0.03), (a["dc"], k["dc"])
    bres = [x for x in k["kontroller"] if "Bresler" in x["ad"]]
    assert bres and all(not x.get("kosul") for x in bres)                # dayanım satırı (sağlanan koşul değil)
    assert any(x["dc"] == pytest.approx(k["dc"]) for x in bres)           # D/C'yi Bresler satırı belirler
    assert k["belirleyen"]["kontrol"] == "N–M"


@pytest.mark.parametrize("ad,kolon30", [("betonarme-tek-aciklik", False), ("betonarme-2kat-3x2", False),
                                        ("betonarme-3kat-3x3", False), ("celik-1kat-depo", False),
                                        ("betonarme-4kat-4x3", False), ("betonarme-2kat-3x2", True),
                                        ("betonarme-3kat-3x3", True), ("betonarme-4kat-4x3", True)])
def test_dc_paritesi_aks_kat_ile(ad, kolon30):
    v1, v3 = _iki_motor(ad, kolon30)
    farklar = [(abs(k["dc"] - a["dc"]) / max(a["dc"], 1e-9), k["cubuk"], a["dc"], k["dc"]) for a, k in _eslesen(v1, v3)]
    assert farklar
    en = max(farklar)
    assert en[0] <= 0.03, en


@pytest.mark.parametrize("ad", ["betonarme-2kat-3x2", "betonarme-3kat-3x3", "betonarme-4kat-4x3"])
def test_rho_gerekli_aks_kat_ile(ad):
    for kolon30 in (False, True):
        v1, v3 = _iki_motor(ad, kolon30)
        for a, k in _eslesen(v1, v3, "kolon"):
            r1, r3 = a["ozet"].get("rho_gerekli"), k["ozet"].get("rho_gerekli")
            if r1 is None or r3 is None:
                assert r1 == r3, (k["cubuk"], r1, r3)
            else:
                assert abs(r3 - r1) <= 0.0025 + 1e-12, (k["cubuk"], r1, r3)
