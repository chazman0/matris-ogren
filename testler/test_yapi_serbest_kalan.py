# -*- coding: utf-8 -*-
"""yapi_serbest.py kalan işler: Bresler satırının D/C'ye girmesi (K-2) ve genel motorun diğer kalan maddeleri."""
from __future__ import annotations

import copy
import functools
import json
import math

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


# ---------------------------------------------------------------------------
# K-10: yaylı mesnet (C13)
# ---------------------------------------------------------------------------
def _R(x, y, z):
    return {"aks": [x, y], "z": z}


def _yayli_konsol(P=10.0, **mesnet):
    m = {"dugum": _R("A", "1", "Üst"), "ux": True, "uy": True, "rx": True, "ry": True, "rz": True, "kz": 5000.0}
    m.update(mesnet)
    return {"tur": "bina", "surum": 3, "sistem": "celik",
            "akslar": {"x": [{"ad": "A", "konum": 0.0}, {"ad": "B", "konum": 4.0}], "y": [{"ad": "1", "konum": 0.0}],
                       "z": [{"ad": "±0.00", "konum": 0.0, "kat": 0}, {"ad": "Üst", "konum": 3.0, "kat": 1}]},
            "malzemeler": {"S275": {"kutuphane": "S275", "gamma": 0.0}},
            "kesitler": {"K": {"tip": "profil", "profil": "HEB 200", "malzeme": "S275"}},
            "cubuklar": [{"no": 1, "i": _R("A", "1", "Üst"), "j": _R("B", "1", "Üst"), "tur": "kiris", "kesit": "K"}],
            "mesnetler": [{k: v for k, v in m.items() if v is not None}],
            "ek_yukler": [{"tur": "dugum", "dugum": _R("B", "1", "Üst"), "durum": "G", "FZ": -P}], "kombinasyon_kumesi": "cythye_gkt"}


def test_yayli_mesnet_konsol_el_hesabi():
    r = coz(_yayli_konsol())
    v = r.veri
    B = r.ic["B"]
    EI = B.malzemeler["S275"]["E"] * B.kesitler["K"]["I_guclu"]
    uc = next(d["no"] for d in v["ag"]["dugumler"] if abs(d["X"] - 4.0) < 1e-9)
    uz = next(d["uZ"] for d in v["durumlar"]["G"]["dugumler"] if d["no"] == uc)
    assert uz == pytest.approx(-(10.0 / 5000.0 + 10.0 * 4.0 ** 3 / (3.0 * EI)), rel=1e-6)    # δ = P/k_z + P·L³/(3EI)
    m = v["akis"]["mesnetler"]
    assert len(m) == 1 and m[0]["tip"] == "yay" and m[0]["yay"] == {"kz": 5000.0} and m[0]["N_G"] == pytest.approx(10.0)
    assert v["ag"]["mesnetler"][0]["yay"] == {"kz": 5000.0}
    y = v["durumlar"]["G"]["yaylar"]
    assert len(y) == 1 and y[0]["tur"] == "yay-mesnet" and y[0]["bilesen"] == "Fy" and y[0]["kuvvet"] == pytest.approx(10.0)
    kg = v["akis"]["korunum"]["G"]
    assert kg["toplam"] == pytest.approx(10.0) and kg["yay"] == pytest.approx(10.0) and kg["kolon_taban"] == pytest.approx(kg["toplam"])
    assert all(x.get("tur") == "yay-mesnet" for k in v["sonuclar"].values() for x in k["yaylar"])


def test_yayli_mesnet_eksen_eslemesi():
    """Bina eksenlerindeki yaylar motor eksenlerine: kx → kx, ky → kz, kz → ky, krx → krx, kry → krz, krz → kry."""
    b = _yayli_konsol(ux=None, uy=None, rz=None, kx=1e5, ky=2e5, krz=3e5)
    b["mesnetler"][0].pop("kz")
    b["mesnetler"][0]["uz"] = True
    b["ek_yukler"] += [{"tur": "dugum", "dugum": _R("B", "1", "Üst"), "durum": "G", "FX": 20.0, "FY": 30.0}]
    r = coz(b)
    v = r.veri
    y = {x["bilesen"]: x for x in v["durumlar"]["G"]["yaylar"]}
    assert set(y) == {"Fx", "Fz", "My"} and {x["tur"] for x in y.values()} == {"yay-mesnet"}
    assert y["Fx"]["k"] == pytest.approx(1e5) and y["Fz"]["k"] == pytest.approx(2e5) and y["My"]["k"] == pytest.approx(3e5)
    assert y["Fx"]["kuvvet"] == pytest.approx(-20.0, rel=1e-6)                 # yatay yük yalnız yayla dengelenir
    assert -y["Fz"]["kuvvet"] == pytest.approx(-30.0, rel=1e-6)                # bina FY = −motor Fz
    assert v["akis"]["mesnetler"][0]["yay"] == {"kx": 1e5, "ky": 2e5, "krz": 3e5}


@pytest.mark.parametrize("ek,desen", [({"uz": True}, r"mesnetler\[1\]: uz hem tutulu hem yaylı verilemez \(kz\)\."),
                                      ({"kz": 0}, r"mesnetler\[1\]: kz pozitif bir sayı olmalı \(kN/m ya da kN·m/rad\)\."),
                                      ({"kz": -5}, r"kz pozitif bir sayı"), ({"kz": "abc"}, r"kz pozitif bir sayı"),
                                      ({"krx": True}, r"rx hem tutulu hem yaylı|krx pozitif bir sayı")])
def test_yayli_mesnet_hatalari(ek, desen):
    with pytest.raises(Exception, match=desen):
        coz(_yayli_konsol(**ek))


# ---------------------------------------------------------------------------
# K-15: rijit diyaframlı seviyede mesnet (C14)
# ---------------------------------------------------------------------------
def test_rijit_diyafram_mesnedi_ceza_yayi():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["deprem"]["etkin"] = True
    b["yuk_durumlari"]["E"]["acik"] = True
    b["surum"] = 3
    b["mesnetler"] = [{"dugum": {"aks": ["C", "2"], "kat": 1}, "ux": True}]
    r = coz(copy.deepcopy(b))
    v = r.veri
    assert v["ag"]["diyafram_seviye"]["1"]["mod"] == "rijit"
    m = v["akis"]["mesnetler"]
    assert len(m) == 1 and m[0]["tip"] == "ozel"
    assert any("rijit diyaframlı 1. kat seviyesinde: ux/uy/rz mesnedi diyafram bağıyla (ceza rijitliği) uygulandı" in u
               for u in v["uyarilar"])
    p = r.ic["paket"]
    d = p.durum["EX+"]
    iy = [i for i, mm in enumerate(p.yay_meta) if mm.get("tur") == "diyafram-mesnet"]
    assert [p.yay_meta[i]["bilesen"] for i in iy] == ["Fx"]
    FX = float(d["tep"][:, 0].sum()) + float(sum(d["yay"][i] for i in iy))
    assert FX == pytest.approx(-v["deprem"]["X"]["VtE"], rel=1e-6)            # Σ tepki FX + Σ ceza yayı = −Σ uygulanan FX
    n = m[0]["dugum"]
    ux = {x["no"]: x["uX"] for x in v["durumlar"]["EX+"]["dugumler"]}
    assert abs(ux[n]) <= 1e-6 * max(abs(x) for x in ux.values())
    b["analiz"] = dict(b.get("analiz") or {}, diyafram={"1": "esnek"})
    v2 = coz(b).veri
    assert v2["ag"]["diyafram_seviye"]["1"]["mod"] == "esnek"
    assert not any(y.get("tur") == "diyafram-mesnet" for y in v2["durumlar"]["G"]["yaylar"])


# ---------------------------------------------------------------------------
# K-41: akış şeması çubuk → çubuk / mesnet kenarları (C15)
# ---------------------------------------------------------------------------
def _akis_ham(r):
    """Yuvarlatılmamış akış (iç işlev): paketten G/Q/S KISA'ları."""
    p = r.ic["paket"]
    kisa = {d: p.kisa(p.durum[d]) for d in ("G", "Q", "S") if d in p.durum}
    return YS._akis(r.ic["B"], r.ic["alan"]["Y"], r.ic["alan"]["ag"], kisa), kisa


@functools.lru_cache(maxsize=None)
def _akis_modeli(ad):
    b = yapi.bina_sablon(ad)
    if ad != "celik-cbf-3kat":
        b["surum"] = 3
    return coz(b)


@pytest.mark.parametrize("ad", ["celik-cbf-3kat", "betonarme-2kat-3x2", "betonarme-4kat-radye"])
def test_akis_dugum_kurali_korunum(ad):
    r = _akis_modeli(ad)
    akis, kisa = _akis_ham(r)
    for d, k in kisa.items():
        for n, (gir, cik) in YS._dugum_akimlari(r.ic["B"], r.ic["alan"]["Y"], r.ic["alan"]["ag"], k, d).items():
            a, b = sum(x for _, x in gir), sum(x for _, x in cik)
            assert a == pytest.approx(b, rel=1e-6, abs=1e-6), (d, n, gir, cik)          # düğümde Σ giren = Σ çıkan
    turler = {e["tur"] for e in akis["sankey"]}
    assert {"panel-cubuk", "cubuk-cubuk", "cubuk-mesnet"} <= turler
    assert all(e["kN"] >= 1e-9 for e in akis["sankey"]) and "sankey_kesildi" not in akis
    T = r.veri.get("temel") or {}
    if T.get("tip") in ("surekli", "radye"):          # temel ağı düğümünde tek çıkan M: Σ (G + Q) = yuk_akisi.kolon_N
        M = sum(e["kN"] for e in akis["sankey"] if e["hedef"].startswith("M") and e["durum"] in ("G", "Q"))
        assert M == pytest.approx(T["yuk_akisi"]["kolon_N"], rel=1e-6)
    else:                                             # Σ mesnede giren = Σ düşey tepki + yay kuvveti
        for d, k in kisa.items():
            M = sum(e["kN"] for e in akis["sankey"] if e["hedef"].startswith("M") and e["durum"] == d)
            R = sum(t["FZ"] for t in k["tepkiler"]) + sum(y["kuvvet"] for y in k["yaylar"] if y.get("bilesen") == "Fy")
            assert M == pytest.approx(R, rel=1e-6), d
    # yanıt: veri.akis.sankey aynı kenarlar (kN 6 anlamlı basamak), tur alanıyla
    assert len(r.veri["akis"]["sankey"]) == len(akis["sankey"]) and all("tur" in e for e in r.veri["akis"]["sankey"])


def test_akis_kolon_oz_agirligi_ve_kirislerden_gelen():
    """Açıklık yükü olmayan kolon: Σ çıkan − Σ giren = kendi G öz ağırlığı; kirişin aktardığı kolona gider."""
    r = _akis_modeli("betonarme-2kat-3x2")
    akis, _ = _akis_ham(r)
    B, YK = r.ic["B"], r.ic["alan"]["Y"]
    say = 0
    for c in B.cubuklar:
        if c["tur"] != "kolon":
            continue
        k = f"Ç{c['no']}"
        gir = sum(e["kN"] for e in akis["sankey"] if e["durum"] == "G" and e["hedef"] == k)
        cik = sum(e["kN"] for e in akis["sankey"] if e["durum"] == "G" and e["kaynak"] == k)
        oz = YK.cubuk_ozet[c["no"]]["G"]["toplam_kN"]
        assert cik - gir == pytest.approx(oz, abs=1e-6), (c["no"], gir, cik, oz)
        say += 1
    assert say > 0
    kiris = next(c for c in B.cubuklar if c["tur"] == "kiris")
    assert any(e["kaynak"] == f"Ç{kiris['no']}" and e["tur"] == "cubuk-cubuk" for e in akis["sankey"])


def test_akis_sankey_siniri():
    v = coz(yapi.bina_sablon("celik-sanayi-4hol")).veri
    sk = v["akis"]["sankey"]
    kes = v["akis"].get("sankey_kesildi") or {}
    for d in {e["durum"] for e in sk}:
        assert sum(1 for e in sk if e["durum"] == d and e["tur"] == "panel-cubuk") <= 600
        assert sum(1 for e in sk if e["durum"] == d and e["tur"] != "panel-cubuk") <= 600
    assert kes and all(n > 0 for n in kes.values())


def test_akis_dugum_yuku_kenarlari():
    v = coz(_yayli_konsol()).veri                     # uç düğüm yükü 10 kN → konsol → yaylı mesnet
    sk = [e for e in v["akis"]["sankey"] if e["durum"] == "G"]
    uc = next(d["no"] for d in v["ag"]["dugumler"] if abs(d["X"] - 4.0) < 1e-9)
    mes = v["akis"]["mesnetler"][0]["dugum"]
    assert sorted((e["kaynak"], e["hedef"], e["tur"]) for e in sk) == sorted([(f"D{uc}", "Ç1", "dugum-cubuk"),
                                                                              ("Ç1", f"M{mes}", "cubuk-mesnet")])
    assert all(e["kN"] == pytest.approx(10.0) for e in sk)


# ---------------------------------------------------------------------------
# K-37: rüzgâr, deprem ve kren eylemleri (C16)
# ---------------------------------------------------------------------------
def _eylem_toplami(e):
    F = [0.0] * 6
    for c in e["cubuklar"]:
        for y in c["yayili"]:
            for a in range(3):
                F[a] += (y["q1"] + y["q2"]) / 2.0 * (y["x2"] - y["x1"]) * y["vek"][a]
        for t in c["tekil"]:
            for a in range(3):
                F[a] += t["P"] * t["vek"][a]
    for d in e["dugumler"]:
        for a in range(6):
            F[a] += d["F"][a]
    return F


def test_eylemler_genel_sanayi_panel_ruzgari_deprem_kren():
    b = yapi.bina_sablon("celik-sanayi-4hol")
    r = coz(b)
    v = r.veri
    e = v["yukler"]["eylemler"]
    assert "eylemler_not" not in v["yukler"]
    for ad in ("W+X", "W-X", "W+Y", "W-Y"):                     # panel rüzgârı: çubuk yükleri, toplam = veri.ruzgar.toplam
        F = _eylem_toplami(e[ad])
        assert e[ad]["cubuklar"] and F[:3] == pytest.approx(v["ruzgar"]["toplam"][ad], abs=1e-3)
    for ad, i in (("EX+", 0), ("EX-", 0), ("EY+", 1), ("EY-", 1)):     # ± dışmerkezlik işaretidir; kuvvet V_tE yönünde
        F = _eylem_toplami(e[ad])
        assert F[i] == pytest.approx(v["deprem"]["X" if i == 0 else "Y"]["VtE"], rel=1e-5) and abs(F[1 - i]) < 1e-6
        assert not e[ad]["cubuklar"] and abs(F[2]) < 1e-9
    assert e["EZ"] == {"cubuklar": [], "dugumler": [], "G_carpani": pytest.approx(2.0 / 3.0 * v["deprem"]["SDS"])}
    B = r.ic["B"]
    kren = [k for k in e if k.startswith("K")]
    assert kren and set(kren) == {d for k in v["kren"]["kopruler"] for d in k["durumlar"]}
    for ad in kren:
        ki = int(ad[1:].split(".")[0])
        k0 = B.kopruler[ki - 1]
        t, phi = k0[0]["tekerlek"], k0[0]["dinamik"]
        F = _eylem_toplami(e[ad])
        assert F[2] == pytest.approx(-phi * t["adet"] * (t["P_maks"] + (t["P_min"] if len(k0) > 1 else 0.0)), rel=1e-6)
        yatay = math.hypot(len(k0) * t["adet"] * t["H_yanal"], t["adet"] * t["H_fren"])
        assert math.hypot(F[0], F[1]) == pytest.approx(yatay, rel=1e-6)
        assert all(c["tekil"] and not c["yayili"] for c in e[ad]["cubuklar"])
        for c in e[ad]["cubuklar"]:
            L = B.cubuk_no[c["no"]]["L"]
            assert all(0.0 <= x["x"] <= L + 1e-9 for x in c["tekil"])


@pytest.mark.parametrize("surum", [1, 3])
def test_eylemler_dugum_yukleri_3x3(surum):
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["yuk_durumlari"]["W"]["acik"] = True
    if surum == 3:
        b["surum"] = 3
    v = coz(b).veri
    e = v["yukler"]["eylemler"]
    assert set(e) == {"W+X", "W-X", "W+Y", "W-Y", "EX+", "EX-", "EY+", "EY-", "EZ"}
    dug = {d["no"] for d in v["ag"]["dugumler"]}
    for ad, x in e.items():
        assert x["cubuklar"] == [] and all(d["dugum"] in dug for d in x["dugumler"])
    rz = v["ruzgar"]
    assert _eylem_toplami(e["W+X"])[0] == pytest.approx(rz["toplam_x"], rel=1e-6)
    assert _eylem_toplami(e["W-Y"])[1] == pytest.approx(-rz["toplam_y"], rel=1e-6)
    assert _eylem_toplami(e["EX+"])[0] == pytest.approx(v["deprem"]["X"]["VtE"], rel=1e-5)
    assert _eylem_toplami(e["EY+"])[1] == pytest.approx(v["deprem"]["Y"]["VtE"], rel=1e-5)
    assert any(abs(d["F"][5]) > 0 for d in e["EX+"]["dugumler"])          # dışmerkezlik: efendi düğümde burulma momenti
    assert any(d["dugum"] in {n["no"] for n in v["ag"]["dugumler"] if n["efendi"]} for d in e["EX+"]["dugumler"])


def test_eylemler_boyut_korumasi():
    v = {"yukler": {"eylemler": {"W+X": {"cubuklar": [], "dugumler": [{"dugum": 1, "F": [1.0] * 6}] * 50}}}}
    YS._eylemleri_sinirla(v, 100, 1000)
    assert "eylemler" in v["yukler"]                                   # sınır içinde: dokunulmaz
    L = len(json.dumps(v["yukler"]["eylemler"], ensure_ascii=False))
    YS._eylemleri_sinirla(v, 900 + L, 1000)                            # yanıtı tek başına sınırın üstüne taşıyor: atılır
    assert "eylemler" not in v["yukler"] and v["yukler"]["eylemler_not"] == YS.EYLEMLER_NOTU
    v = {"yukler": {"eylemler": {"EZ": {"cubuklar": [], "dugumler": [], "G_carpani": 0.8}}}}
    YS._eylemleri_sinirla(v, 5000, 1000)                               # zaten büyük yanıtta küçük eylem kümesi korunur
    assert "eylemler" in v["yukler"]


# ---------------------------------------------------------------------------
# K-31: kesit önerisinin hafif ara çözümü (bina_coz(hafif=True)) tam çözümle aynı tasarım D/C'lerini verir
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", ["betonarme-2kat-3x2", "celik-cbf-3kat"])
def test_hafif_cozum_ayni_tasarim(ad):
    b = yapi.bina_sablon(ad)
    b["surum"] = 3
    tam = YS.bina_coz(copy.deepcopy(b), anlat=False)
    haf = YS.bina_coz(copy.deepcopy(b), anlat=False, hafif=True)
    assert set(haf.veri) == {"tasarim"} and haf.ic["hafif"] is True
    assert json.dumps(haf.veri["tasarim"]["elemanlar"], sort_keys=True) == json.dumps(tam.ic["tas_tam"]["elemanlar"] if "tas_tam" in tam.ic
                                                                                    else tam.veri["tasarim"]["elemanlar"], sort_keys=True)
    assert haf.ic["kimlik"] == tam.ic["kimlik"] and haf.ic["oteleme_asan"] == tam.ic["oteleme_asan"]
    assert haf.ic["kombinasyonlar"] == tam.ic["kombinasyonlar"]
