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


# ---------------------------------------------------------------------------
# K-20: panellerin aks–kat kaynağı (C17) — köprü testi test_kopru_bina'da
# K-26: adres metinlerinde Türkçe tür adları (C18)
# ---------------------------------------------------------------------------
def test_tur_adi_ve_adresler():
    assert YS.TUR_ADI == {"kolon": "kolon", "kiris": "kiriş", "capraz": "çapraz", "makas-ust": "makas üst başlık",
                          "makas-alt": "makas alt başlık", "makas-dikme": "makas dikmesi", "makas-diyagonal": "makas diyagonali",
                          "asik": "aşık", "kren": "kren kirişi", "bag": "bağ", "diger": "diğer"}
    assert set(YS.TUR_ADI) == set(YS._TURLER)
    v = _iki_motor("betonarme-2kat-3x2")[1]
    k = next(k for k in v["tasarim"]["elemanlar"] if k["tur"] == "kiris")
    assert k["adres"] == f"Ç{k['cubuk']} (kiriş)" and k["tur"] == "kiris"
    assert all("(kiris)" not in e["adres"] for e in v["ag"]["elemanlar"])
    assert any("(kiriş)" in e["adres"] for e in v["ag"]["elemanlar"])
    v = coz(yapi.bina_sablon("celik-cbf-3kat")).veri
    assert any(k["adres"].endswith("(çapraz)") for k in v["tasarim"]["elemanlar"])
    with pytest.raises(Exception, match=r"bir kiriş \(kolon değil\)"):
        YS._cubuk_bul(YS._oku(yapi.bina_sablon("celik-cbf-3kat")), "kolon",
                      next(c["no"] for c in yapi.bina_sablon("celik-cbf-3kat")["cubuklar"] if c["tur"] == "kiris"))


# ---------------------------------------------------------------------------
# K-30: genel betonarme kolon özeti (C21) — yön, bX/bY izdüşümü, alt uç N
# K-44: kat ağırlık tablosu aks–kat kuralıyla (kolon ağırlığı üst kata)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", ["betonarme-2kat-3x2", "betonarme-3kat-3x3"])
def test_kolon_ozeti_ve_kat_agirliklari_aks_kat_ile_ayni(ad):
    v1, v3 = _iki_motor(ad)
    for a, k in _eslesen(v1, v3, "kolon"):
        o1, o3 = a["ozet"], k["ozet"]
        assert o3["yon"] == o1["yon"] and o3["bX"] == pytest.approx(o1["bX"]) and o3["bY"] == pytest.approx(o1["bY"])
        assert o3["N_min_kN"] == pytest.approx(o1["N_min_kN"], rel=0.01) and o3["N_max_kN"] == pytest.approx(o1["N_max_kN"], rel=0.01)
    for k1, k3 in zip(v1["yukler"]["katlar"], v3["yukler"]["katlar"]):
        assert k1["kat"] == k3["kat"]
        for a in ("G", "Q", "S", "w"):
            assert k3[a] == pytest.approx(k1[a], abs=1e-6), (k1["kat"], a)
    assert v3["yukler"]["katlar"][0]["G"] == 0.0
    if v1.get("deprem"):
        assert v3["deprem"]["m_t"] == pytest.approx(v1["deprem"]["m_t"], rel=1e-12)
        for y in ("X", "Y"):
            assert v3["deprem"][y]["VtE"] == pytest.approx(v1["deprem"][y]["VtE"], rel=1e-12)


def test_dikdortgen_kolon_90_derece_bX_bY_takas():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["kesitler"]["S30x60"] = {"tip": "dikdortgen", "b": 0.3, "h": 0.6, "malzeme": "C30", "donati": "B420C", "pas": 0.03}
    for k in b["kolonlar"]:
        k["kesit"] = "S30x60"
    b["kolonlar"][0]["yon"], b["kolonlar"][1]["yon"] = "x", "y"
    b["surum"] = 3
    v = coz(b).veri
    oz = {k["kaynak"]["no"]: k["ozet"] for k in v["tasarim"]["elemanlar"] if k["tur"] == "kolon"}
    n1, n2 = b["kolonlar"][0]["no"], b["kolonlar"][1]["no"]
    assert (oz[n1]["yon"], oz[n1]["bX"], oz[n1]["bY"]) == ("x", pytest.approx(0.6), pytest.approx(0.3))
    assert (oz[n2]["yon"], oz[n2]["bX"], oz[n2]["bY"]) == ("y", pytest.approx(0.3), pytest.approx(0.6))
    # aks–kat kaynağı olmayan çubuk: yön yerel eksen açısından
    B = YS._oku(b)
    c = dict(next(c for c in B.cubuklar if c["tur"] == "kolon"), kaynak=None)
    assert [YS._kolon_yonu(B, dict(c, aci=a)) for a in (0, 90, 180, 270, 30)] == ["x", "y", "x", "y", "30°"]


# ---------------------------------------------------------------------------
# K-14: döşemeli çelik kirişte bölge etiketleri ve özet alanları (aks–kat ile aynı)
# ---------------------------------------------------------------------------
def test_celik_doseme_kirisi_bolge_etiketleri():
    v1, v3 = _iki_motor("celik-1kat-depo")
    say = 0
    for a, k in _eslesen(v1, v3, "kiris"):
        say += 1
        assert k["belirleyen"]["kontrol"] == a["belirleyen"]["kontrol"] and k["dc"] == pytest.approx(a["dc"], rel=1e-9)
        for alan in ("bolge", "Lb_neg_m", "Cb_neg", "Mc_neg_kNm"):
            assert k["ozet"].get(alan) == pytest.approx(a["ozet"].get(alan)), (k["cubuk"], alan)
        bolge = k["ozet"]["bolge"]
        assert k["belirleyen"]["kontrol"].endswith(f"({bolge} M)")
        assert all(f"{bolge} M" in x["ad"] for x in k["kontroller"][:2])
    assert say >= 6 and any(k["ozet"]["bolge"] == "negatif" for k in v3["tasarim"]["elemanlar"] if k["tur"] == "kiris")


# ---------------------------------------------------------------------------
# K-13: birden çok parçalı aks–kat kirişine tek öneri (C19)
# ---------------------------------------------------------------------------
def _uzun_kirisli():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["kirisler"][0]["son"] = ["C", "1"]                      # kiriş 1 A1 → C1 (B1 kolonunda iki parça)
    b["kirisler"] = [k for k in b["kirisler"] if k["no"] != 2]
    b["kesitler"]["K25x32"] = {"tip": "dikdortgen", "b": 0.25, "h": 0.32, "malzeme": "C30", "donati": "B420C", "pas": 0.03}
    b["kirisler"][0]["kesit"] = "K25x32"
    return b


def test_parcali_aks_kat_kirisine_tek_oneri():
    b = _uzun_kirisli()
    gor = coz(copy.deepcopy(b))
    ic = YS.genel_cozum(b)
    parca = [c["no"] for c in ic["B"].cubuklar if (c.get("kaynak") or {}).get("aks_kat") == "kiris" and c["kaynak"]["no"] == 1]
    assert len(parca) == 2
    o = YS.kesit_oner(ic=ic, hedef=[{"tur": "kiris", "no": 1}], gorunen=gor.ic)
    assert len(o["oneriler"]) == 1
    x = o["oneriler"][0]
    tablo = next(k["dc"] for k in gor.veri["tasarim"]["elemanlar"] if k["tur"] == "kiris" and k["no"] == 1)
    assert x["cubuk"] == parca[0] and x["cubuklar"] == parca and x["dc_once"] == pytest.approx(tablo)
    assert x["kaynak"]["aks_kat"] == "kiris" and x["kaynak"]["no"] == 1 and x["uygula"]["tanim"]["tip"] == "dikdortgen"
    T = ic["tasarim"]
    kart = dict(T.B.kesitler["K25x32"], b=x["b"], h=x["h"])
    tekrar = YS._uyeler_dc(tasarim_mod(), T, [T.B.cubuk_no[n] for n in parca], kart)
    assert all(d <= x["dc_oneri"] + 1e-9 for d in tekrar.values())          # dc_oneri ≥ her parçanın yeniden tahkiki
    h = YS.kesit_oner(ic=ic, hedef="hepsi", gorunen=gor.ic)                   # 'hepsi' de aks–kat elemanı başına bir öneri
    assert [y["cubuklar"] for y in h["oneriler"] if y.get("cubuklar")] == [parca]
    assert sum(1 for y in h["oneriler"] if y["cubuk"] in parca) == 1
    y = YS.kesit_oner(ic=ic, hedef=[{"tur": "kiris", "no": 1}], yinele=1, gorunen=gor.ic)
    yeni = next(k for k in y["bina"]["kirisler"] if k["no"] == 1)
    assert yeni["kesit"] == x["uygula"]["ad"]
    v2 = coz(copy.deepcopy(y["bina"])).veri
    assert next(k["dc"] for k in v2["tasarim"]["elemanlar"] if k["tur"] == "kiris" and k["no"] == 1) <= 1.0 + 1e-9


def tasarim_mod():
    import tasarim
    return tasarim
