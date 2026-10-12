# -*- coding: utf-8 -*-
"""sonlu_eleman modülü testleri (pytest).

Kapsam: örnek model kataloğu, el hesabı/kapalı form kıyas çözümleri (kesin eşitlik), bağımsız numpy
referans çözücüsüyle karşılaştırma, K simetrisi ve rijit cisim sıfır özdeğerleri, denge ve enerji,
eleman uç kuvvetleri ve iç kuvvet diyagramları, sembolik çözümler, sayısal mod (SD > 12), öğretici
hata iletileri, anlatım/şema sözleşmesi, üretilen Python betiğinin sonuçla tutarlılığı, JSON uyumu.

Çalıştırma (proje klasöründen):
  uv run --python 3.13 --with sympy --with numpy --with pytest python -m pytest testler/test_se.py -q
"""
from __future__ import annotations

import ast
import contextlib
import copy
import io
import json
import re
import time
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

import matris_ogren as mo
import sonlu_eleman as se

ADLAR = list(se.ORNEK_MODELLER)
R = sp.Rational

_onbellek: dict = {}


def coz(ad):
    """Örnek modeli bir kez çözer (testler arasında paylaşılır; sonuç salt okunur kullanılır)."""
    if ad not in _onbellek:
        _onbellek[ad] = se.se_coz(se.ornek_model(ad))
    return _onbellek[ad]


# ---------------------------------------------------------------------------
# Bağımsız referans çözücü (numpy, yoğun matrisler; sonlu_eleman'dan hiçbir şey kullanmaz)
# ---------------------------------------------------------------------------
_D = {"yay": 1, "cubuk": 1, "kafes": 2, "kiris": 2, "cerceve": 3}
_YUK = {"yay": {"Fx": 0}, "cubuk": {"Fx": 0}, "kafes": {"Fx": 0, "Fy": 1},
        "kiris": {"Fy": 0, "M": 1}, "cerceve": {"Fx": 0, "Fy": 1, "M": 2}}
_MESNET = {"yay": ["ux"], "cubuk": ["ux"], "kafes": ["ux", "uy"], "kiris": ["uy", "rz"],
           "cerceve": ["ux", "uy", "rz"]}


def _cerceve_k(EA, EI, L):
    a, b = EA / L, EI / L ** 3
    return np.array([
        [a, 0, 0, -a, 0, 0],
        [0, 12 * b, 6 * b * L, 0, -12 * b, 6 * b * L],
        [0, 6 * b * L, 4 * b * L ** 2, 0, -6 * b * L, 2 * b * L ** 2],
        [-a, 0, 0, a, 0, 0],
        [0, -12 * b, -6 * b * L, 0, 12 * b, -6 * b * L],
        [0, 6 * b * L, 2 * b * L ** 2, 0, -6 * b * L, 4 * b * L ** 2]])


def _kiris_k(EI, L):
    b = EI / L ** 3
    return np.array([
        [12 * b, 6 * b * L, -12 * b, 6 * b * L],
        [6 * b * L, 4 * b * L ** 2, -6 * b * L, 2 * b * L ** 2],
        [-12 * b, -6 * b * L, 12 * b, -6 * b * L],
        [6 * b * L, 2 * b * L ** 2, -6 * b * L, 4 * b * L ** 2]])


def referans(m):
    """Modeli bağımsız olarak çözer. Dönüş: u, R (= K u - F), eleman listesi [(f_yerel, N)]."""
    tip = m["tip"]
    d = _D[tip]
    sira = {dg["no"]: i for i, dg in enumerate(m["dugumler"])}
    xy = np.array([[float(dg.get("x", 0)), 0.0 if tip in ("yay", "cubuk") else float(dg.get("y", 0))]
                   for dg in m["dugumler"]])
    n = d * len(sira)
    K = np.zeros((n, n))
    F = np.zeros(n)
    qlar = {y["eleman"]: float(y["q"]) for y in m.get("yayili", [])}
    eleman_verisi = []
    for e in m["elemanlar"]:
        a, b = (sira[v] for v in e["dugumler"])
        dx, dy = xy[b] - xy[a]
        L = float(np.hypot(dx, dy))
        c, s = dx / L, dy / L
        q = qlar.get(e["no"], 0.0)
        EA = float(e["E"]) * float(e["A"]) if "A" in e and "E" in e else 0.0
        if tip == "yay":
            kl, T, feq = float(e["k"]) * np.array([[1.0, -1.0], [-1.0, 1.0]]), np.eye(2), np.zeros(2)
        elif tip == "cubuk":
            kl, T, feq = EA / L * np.array([[1.0, -1.0], [-1.0, 1.0]]), np.eye(2), np.zeros(2)
        elif tip == "kafes":
            v = np.array([-c, -s, c, s])
            kl, T, feq = EA / L * np.outer(v, v), np.eye(4), np.zeros(4)
        elif tip == "kiris":
            EI = float(e["E"]) * float(e["I"])
            kl, T = _kiris_k(EI, L), np.eye(4)
            feq = np.array([q * L / 2, q * L ** 2 / 12, q * L / 2, -q * L ** 2 / 12])
        else:
            EI = float(e["E"]) * float(e["I"])
            kl = _cerceve_k(EA, EI, L)
            t3 = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
            T = np.block([[t3, np.zeros((3, 3))], [np.zeros((3, 3)), t3]])
            feq = np.array([0, q * L / 2, q * L ** 2 / 12, 0, q * L / 2, -q * L ** 2 / 12])
        dofs = [d * a + j for j in range(d)] + [d * b + j for j in range(d)]
        ke = T.T @ kl @ T
        K[np.ix_(dofs, dofs)] += ke
        F[dofs] += T.T @ feq
        eleman_verisi.append((kl, T, dofs, feq, c, s, EA, L))
    for y in m.get("yukler", []):
        i = sira[y["dugum"]]
        for ad, j in _YUK[tip].items():
            F[d * i + j] += float(y.get(ad, 0) or 0)
    tutulu = []
    for ms in m.get("mesnetler", []):
        i = sira[ms["dugum"]]
        for j, ad in enumerate(_MESNET[tip]):
            if ms.get(ad):
                tutulu.append(d * i + j)
    serbest = [i for i in range(n) if i not in tutulu]
    u = np.zeros(n)
    u[serbest] = np.linalg.solve(K[np.ix_(serbest, serbest)], F[serbest])
    Rt = K @ u - F
    uc = []
    for kl, T, dofs, feq, c, s, EA, L in eleman_verisi:
        f = kl @ (T @ u[dofs]) - feq
        if tip == "kafes":
            N = EA / L * (c * (u[dofs[2]] - u[dofs[0]]) + s * (u[dofs[3]] - u[dofs[1]]))
        elif tip in ("yay", "cubuk"):
            N = float(f[1])
        elif tip == "cerceve":
            N = -float(f[0])
        else:
            N = 0.0
        uc.append((f, N))
    return u, Rt, uc, K, F


def yakin(a, b, rtol=1e-8, atol=1e-10):
    return np.allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float), rtol=rtol, atol=atol)


def anlatim_metni(r):
    """Anlatımın md ve math bloklarını (kod ve şema hariç) birleştirir."""
    parcalar = []
    for b in r.anlatim.bloklar:
        if b[0] in ("md", "math"):
            parcalar.append(str(b[1]))
    return "\n".join(parcalar)


def kuvvet_bilesenleri(veri):
    """Yük vektörü F'nin x ve y bileşenleri toplamı (kirişte x yoktur)."""
    tip, F = veri["tip"], veri["F"]
    d = _D[tip]
    fx = fy = 0.0
    for i in range(len(veri["dugumler"])):
        if tip in ("yay", "cubuk", "kafes", "cerceve"):
            fx += F[d * i]
        if tip in ("kafes", "cerceve"):
            fy += F[d * i + 1]
        if tip == "kiris":
            fy += F[d * i]
    return fx, fy


# ---------------------------------------------------------------------------
# Katalog
# ---------------------------------------------------------------------------
def test_ornek_katalogu():
    assert ADLAR == ["yay-seri", "cubuk-kademeli", "kafes-iki-cubuk", "kafes-uc-cubuk", "kafes-pratt-kopru",
                     "kiris-konsol", "kiris-basit-yayili", "kiris-ankastre-mafsalli",
                     "cerceve-konsol-kolon", "cerceve-portal"]
    liste = se.ornek_listesi()
    assert [x["ad"] for x in liste] == ADLAR
    for x in liste:
        assert set(x) == {"ad", "baslik", "tip", "aciklama"}
        assert x["baslik"] and x["aciklama"]
        assert x["tip"] in _D
    # her türden en az bir örnek vardır
    assert {x["tip"] for x in liste} == set(_D)


def test_ornek_model_kopya_verir():
    m = se.ornek_model("kiris-konsol")
    m["elemanlar"][0]["E"] = "1"
    m["dugumler"].clear()
    assert se.ORNEK_MODELLER["kiris-konsol"]["elemanlar"][0]["E"] == "200e6"
    assert len(se.ORNEK_MODELLER["kiris-konsol"]["dugumler"]) == 2


def test_ornek_model_bilinmeyen_ad():
    with pytest.raises(mo.MatrisHatasi, match="Örnek model yok"):
        se.ornek_model("yok-boyle-bir-sey")


def test_ornek_modeller_literal_eval_ile_okunur():
    kaynak = Path(se.__file__).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    dugum = next(n for n in agac.body
                 if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "ORNEK_MODELLER" for t in n.targets))
    assert ast.literal_eval(dugum.value) == se.ORNEK_MODELLER


def test_ornek_modeller_json_uyumlu():
    assert json.loads(json.dumps(se.ORNEK_MODELLER)) == se.ORNEK_MODELLER


def test_cozum_girdiyi_degistirmez():
    for ad in ADLAR:
        m = se.ornek_model(ad)
        kopya = copy.deepcopy(m)
        se.se_coz(m)
        assert m == kopya, ad


# ---------------------------------------------------------------------------
# Kıyas (benchmark) çözümleri: kesin eşitlik
# ---------------------------------------------------------------------------
KESIN_U = {
    # F = k u: u2 = 10/1000, u3 = u2 + 10/2000
    "yay-seri": [0, R(1, 100), R(3, 200)],
    # u2 = PL/EA1, u3 = u2 + PL/EA2
    "cubuk-kademeli": [0, R(1, 4000), R(3, 4000)],
    # simetri: u3 = 0; v3 = -P/(2 sin a) * L/(EA) / sin a  -> -125 P / (32 EA) = -1/5120
    "kafes-iki-cubuk": [0, 0, 0, 0, 0, R(-1, 5120)],
    # v = -PL^3/3EI, theta = -PL^2/2EI (EI = 1600)
    "kiris-konsol": [0, 0, R(-9, 160), R(-9, 320)],
    # orta çökme 5qL^4/384EI = 0,050625; uç dönmesi qL^3/24EI = 0,027
    "kiris-basit-yayili": [0, R(-27, 1000), R(-81, 1600), 0, 0, R(27, 1000)],
    # theta(L) = qL^3/48EI = 1/300
    "kiris-ankastre-mafsalli": [0, 0, 0, R(1, 300)],
    # u = PL^3/3EI, theta = -PL^2/2EI
    "cerceve-konsol-kolon": [0, 0, 0, R(9, 160), 0, R(-9, 320)],
}


@pytest.mark.parametrize("ad", list(KESIN_U))
def test_kesin_yer_degistirme(ad):
    r = coz(ad)
    assert r.veri["mod"] == "kesin"
    beklenen = sp.Matrix([sp.nsimplify(v) for v in KESIN_U[ad]])
    assert r.deger == beklenen, (ad, list(r.deger))
    assert yakin(r.veri["u"], [float(v) for v in beklenen], rtol=1e-12, atol=1e-15)


def test_kesin_tepkiler():
    t = {x["dugum"]: x for x in coz("yay-seri").veri["tepkiler"]}
    assert t[1]["Fx"] == pytest.approx(-10)
    t = {x["dugum"]: x for x in coz("cubuk-kademeli").veri["tepkiler"]}
    assert t[1]["Fx"] == pytest.approx(-100)
    # iki çubuklu kafes: düşey tepkiler P/2, yatay tepkiler P/(2 tan a) = 3,75 (içe doğru)
    t = {x["dugum"]: x for x in coz("kafes-iki-cubuk").veri["tepkiler"]}
    assert (t[1]["Fx"], t[1]["Fy"]) == pytest.approx((3.75, 5.0))
    assert (t[2]["Fx"], t[2]["Fy"]) == pytest.approx((-3.75, 5.0))
    # konsol: tepki P ve ankastre momenti PL
    t = coz("kiris-konsol").veri["tepkiler"]
    assert len(t) == 1 and (t[0]["Fy"], t[0]["M"]) == pytest.approx((10.0, 30.0))
    # basit kiriş: qL/2 = 36
    t = {x["dugum"]: x for x in coz("kiris-basit-yayili").veri["tepkiler"]}
    assert (t[1]["Fy"], t[3]["Fy"]) == pytest.approx((36.0, 36.0))
    # bir ucu ankastre, bir ucu kayıcı: kayıcı 3qL/8 = 15, ankastre 5qL/8 = 25, M = qL^2/8 = 20
    t = {x["dugum"]: x for x in coz("kiris-ankastre-mafsalli").veri["tepkiler"]}
    assert t[2]["Fy"] == pytest.approx(15.0)
    assert (t[1]["Fy"], t[1]["M"]) == pytest.approx((25.0, 20.0))
    # konsol kolon: yatay tepki -P, taban momenti PL
    t = coz("cerceve-konsol-kolon").veri["tepkiler"]
    assert (t[0]["Fx"], t[0]["M"]) == pytest.approx((-10.0, 30.0))


def test_kafes_eleman_kuvvetleri_ve_durum():
    v = coz("kafes-iki-cubuk").veri
    assert [e["N"] for e in v["elemanlar"]] == pytest.approx([-6.25, -6.25])
    assert [e["durum"] for e in v["elemanlar"]] == ["basınç", "basınç"]
    assert v["elemanlar"][0]["L"] == pytest.approx(5.0)
    assert (v["elemanlar"][0]["c"], v["elemanlar"][0]["s"]) == pytest.approx((0.6, 0.8))
    # Pratt köprü: alt başlık çekme, üst başlık basınç, simetri
    v = coz("kafes-pratt-kopru").veri
    N = {e["no"]: e["N"] for e in v["elemanlar"]}
    d = {e["no"]: e["durum"] for e in v["elemanlar"]}
    for no in (1, 2, 3, 4):
        assert N[no] > 0 and d[no] == "çekme"
    for no in (5, 6):
        assert N[no] < 0 and d[no] == "basınç"
    assert N[1] == pytest.approx(N[4]) and N[5] == pytest.approx(N[6])
    # sol uç tepkisi 3P/2 = 15
    t = {x["dugum"]: x for x in v["tepkiler"]}
    assert t[1]["Fy"] == pytest.approx(15.0) and t[5]["Fy"] == pytest.approx(15.0)


def test_kiris_diyagramlari_kapali_form():
    v = coz("kiris-basit-yayili").veri
    e1, e2 = v["elemanlar"]
    for e in (e1, e2):
        dg = e["diyagram"]
        assert len(dg["x"]) == len(dg["N"]) == len(dg["V"]) == len(dg["M"]) >= 3
        assert dg["x"][0] == pytest.approx(0.0) and dg["x"][-1] == pytest.approx(e["L"])
    # sol eleman: V(0) = qL/2 = 36, V(3) = 0; M(0) = 0, M(3) = qL^2/8 = 54 (alt lif çekili, +)
    d1 = e1["diyagram"]
    assert d1["V"][0] == pytest.approx(36.0) and d1["V"][-1] == pytest.approx(0.0, abs=1e-9)
    assert d1["M"][0] == pytest.approx(0.0, abs=1e-9) and d1["M"][-1] == pytest.approx(54.0)
    # sağ eleman: M(3) = 54, V(L) = -36
    d2 = e2["diyagram"]
    assert d2["M"][0] == pytest.approx(54.0) and d2["M"][-1] == pytest.approx(0.0, abs=1e-9)
    assert d2["V"][-1] == pytest.approx(-36.0)
    # parabolik moment: orta nokta, M(x) = 36 x - 6 x^2 formülüne uyar
    for x, mm, vv in zip(d1["x"], d1["M"], d1["V"]):
        assert mm == pytest.approx(36 * x - 6 * x * x, abs=1e-9)
        assert vv == pytest.approx(36 - 12 * x, abs=1e-9)


def test_konsol_kiris_diyagrami():
    dg = coz("kiris-konsol").veri["elemanlar"][0]["diyagram"]
    # V = P = 10 sabit; M(x) = -(P (L - x)) : ankastrede hogging -30, uçta 0
    assert dg["V"] == pytest.approx([10.0] * len(dg["x"]))
    assert dg["M"][0] == pytest.approx(-30.0) and dg["M"][-1] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Bağımsız referans çözücü ile karşılaştırma (bütün örnekler)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", ADLAR)
def test_bagimsiz_referans_u_ve_tepkiler(ad):
    r = coz(ad)
    m = se.ornek_model(ad)
    u, Rt, uc, K, F = referans(m)
    v = r.veri
    assert yakin(v["u"], u, rtol=1e-8, atol=1e-12), ad
    assert yakin(v["F"], F, rtol=1e-9, atol=1e-9), ad
    assert yakin([float(x) for x in r.deger], u, rtol=1e-8, atol=1e-12)
    d = _D[m["tip"]]
    sira = {dg["no"]: i for i, dg in enumerate(m["dugumler"])}
    for t in v["tepkiler"]:
        i = sira[t["dugum"]]
        for j, ad_bilesen in enumerate(list(_YUK[m["tip"]])):
            idx = d * i + _YUK[m["tip"]][ad_bilesen]
            ms = next(x for x in m["mesnetler"] if x["dugum"] == t["dugum"])
            bayrak = _MESNET[m["tip"]][_YUK[m["tip"]][ad_bilesen]]
            if ms.get(bayrak):
                assert t[ad_bilesen] == pytest.approx(Rt[idx], rel=1e-8, abs=1e-8), (ad, t["dugum"], ad_bilesen)
    # yük bileşeni olmayan eksen sıfır yazılır
    for t in v["tepkiler"]:
        assert set(t) == {"dugum", "Fx", "Fy", "M"}


@pytest.mark.parametrize("ad", ADLAR)
def test_bagimsiz_referans_eleman_kuvvetleri(ad):
    r = coz(ad)
    m = se.ornek_model(ad)
    u, Rt, uc, K, F = referans(m)
    for e, (f, N) in zip(r.veri["elemanlar"], uc):
        if m["tip"] in ("kiris", "cerceve"):
            assert yakin(e["uc_kuvvetleri"], f, rtol=1e-7, atol=1e-7), (ad, e["no"])
        if m["tip"] != "kiris":
            assert e["N"] == pytest.approx(N, rel=1e-7, abs=1e-8), (ad, e["no"])


@pytest.mark.parametrize("ad", ADLAR)
def test_K_referansla_ayni_ve_simetrik(ad):
    r = coz(ad)
    K = np.array(r.veri["K"], dtype=float)
    _, _, _, Kref, _ = referans(se.ornek_model(ad))
    assert K.shape == Kref.shape == (r.veri["sd_sayisi"],) * 2
    assert np.allclose(K, Kref, rtol=1e-9, atol=1e-6)
    assert np.allclose(K, K.T, rtol=1e-12, atol=1e-9)


# mesnetsiz K'nın sıfır özdeğer sayısı (rijit cisim + varsa mekanizma hareketleri)
SIFIR_OZDEGER = {
    "yay-seri": 1, "cubuk-kademeli": 1,
    "kafes-iki-cubuk": 4, "kafes-uc-cubuk": 5, "kafes-pratt-kopru": 3,   # düzlem: 3 rijit hareket (+ mekanizmalar)
    "kiris-konsol": 2, "kiris-basit-yayili": 2, "kiris-ankastre-mafsalli": 2,   # çökme + dönme
    "cerceve-konsol-kolon": 3, "cerceve-portal": 3,
}


@pytest.mark.parametrize("ad", ADLAR)
def test_rijit_cisim_ozdegerleri(ad):
    K = np.array(coz(ad).veri["K"], dtype=float)
    w = np.linalg.eigvalsh((K + K.T) / 2)
    esik = 1e-9 * np.max(np.abs(w))
    assert int(np.sum(np.abs(w) < esik)) == SIFIR_OZDEGER[ad], (ad, w[:6])
    assert w.min() > -esik   # yarı pozitif tanımlı


@pytest.mark.parametrize("ad", ADLAR)
def test_denge_ve_enerji(ad):
    v = coz(ad).veri
    assert set(v["denge"]) == {"Fx", "Fy", "M"}
    for k, deger in v["denge"].items():
        assert abs(deger) < 1e-7, (ad, k, deger)
    # tepkiler + yükler: bağımsız toplam
    fx, fy = kuvvet_bilesenleri(v)
    assert sum(t["Fx"] for t in v["tepkiler"]) + fx == pytest.approx(0.0, abs=1e-7)
    assert sum(t["Fy"] for t in v["tepkiler"]) + fy == pytest.approx(0.0, abs=1e-7)
    # Clapeyron: U = 1/2 u^T K u = W = 1/2 u^T F > 0
    u, F, K = np.array(v["u"]), np.array(v["F"]), np.array(v["K"])
    U, W = 0.5 * u @ K @ u, 0.5 * u @ F
    assert W > 0
    assert U == pytest.approx(W, rel=1e-8)


def test_enerji_metinde_kesin_esit():
    metin = anlatim_metni(coz("kiris-basit-yayili"))
    assert "Clapeyron" in metin
    assert r"\frac{4617}{4000}" in metin    # U = W = 4617/4000 kN·m (kesin kesir)


# ---------------------------------------------------------------------------
# Sayısal mod ve sembolik çözümler
# ---------------------------------------------------------------------------
def test_sayisal_mod_esigi():
    assert se.SD_ESIK == 12
    v = coz("kafes-pratt-kopru").veri
    assert v["mod"] == "sayisal" and v["sd_sayisi"] == 16 > se.SD_ESIK
    assert all(isinstance(x, float) for x in v["u"])
    assert coz("cerceve-portal").veri["mod"] == "kesin"       # 12 SD: eşik dahil kesin
    assert coz("cerceve-portal").veri["sd_sayisi"] == se.SD_ESIK
    r = coz("kafes-pratt-kopru")
    assert isinstance(r.deger, sp.MatrixBase) and r.deger.shape == (16, 1)


def test_sembolik_sd_esigi_asilinca_ogretici_hata():
    m = se.ornek_model("kafes-pratt-kopru")
    m["elemanlar"][0]["E"] = "E"
    with pytest.raises(mo.MatrisHatasi) as h:
        se.se_coz(m)
    assert "en çok 12" in str(h.value) and "SD" in str(h.value)


def _sembol_degerleri(ifade, deger):
    return float(ifade.subs({s: deger[s.name] for s in ifade.free_symbols}))


def test_sembolik_iki_cubuklu_kafes():
    m = se.ornek_model("kafes-iki-cubuk")
    for e in m["elemanlar"]:
        e["E"], e["A"] = "E", "A"
    m["yukler"] = [{"dugum": 3, "Fy": "-P"}]
    r = se.se_coz(m)
    assert r.veri["mod"] == "kesin"
    v3 = r.deger[5]
    assert {s.name for s in v3.free_symbols} == {"E", "A", "P"}
    deger = {"E": 2.0e8, "A": 1.0e-3, "P": 10.0}
    assert _sembol_degerleri(v3, deger) == pytest.approx(-625 / (16 * 2.0e8 * 1.0e-3))
    # yapısal biçim: -125 P / (32 E A)
    sd = {s.name: s for s in v3.free_symbols}
    assert sp.simplify(v3 + R(125, 32) * sd["P"] / (sd["E"] * sd["A"])) == 0
    # .veri JSON'a uygun: harfli çözümde sayı yerine ifade metni
    json.dumps(r.veri)
    assert any(isinstance(x, str) for x in r.veri["u"])
    # üretilen betik de aynı ifadeyi verir
    ns: dict = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(r.python_kodu, "<kod>", "exec"), ns)
    for a, b in zip(ns["u"], r.deger):
        assert sp.simplify(a - b) == 0


def test_sembolik_konsol_kiris():
    m = se.ornek_model("kiris-konsol")           # L = 3
    m["elemanlar"][0]["E"], m["elemanlar"][0]["I"] = "E", "I"
    m["yukler"] = [{"dugum": 2, "Fy": "-P"}]
    r = se.se_coz(m)
    v, th = r.deger[2], r.deger[3]
    sd = {s.name: s for s in v.free_symbols}
    assert set(sd) == {"E", "I", "P"}
    assert sp.simplify(v + 9 * sd["P"] / (sd["E"] * sd["I"])) == 0          # -PL^3/3EI = -9P/EI
    assert sp.simplify(th + R(9, 2) * sd["P"] / (sd["E"] * sd["I"])) == 0   # -PL^2/2EI
    json.dumps(r.veri)


# ---------------------------------------------------------------------------
# JSON girişi / çıkışı
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", ADLAR)
def test_veri_json_uyumlu_ve_semali(ad):
    v = coz(ad).veri
    yeniden = json.loads(json.dumps(v))
    assert yeniden == v
    assert {"tip", "baslik", "birim", "mod", "sd_sayisi", "sd_etiketleri", "dugumler", "elemanlar",
            "tepkiler", "u", "F", "denge", "olcek", "K"} <= set(v)
    assert v["birim"] == {"kuvvet": "kN", "uzunluk": "m"}
    n = v["sd_sayisi"]
    assert n == _D[v["tip"]] * len(v["dugumler"]) == len(v["u"]) == len(v["F"]) == len(v["sd_etiketleri"])
    assert len(v["K"]) == n and all(len(s) == n for s in v["K"])
    for i, dg in enumerate(v["dugumler"]):
        assert set(dg) == {"no", "x", "y", "sd", "u"}
        assert dg["sd"] == [_D[v["tip"]] * i + j + 1 for j in range(_D[v["tip"]])]
        assert dg["u"] == [v["u"][k - 1] for k in dg["sd"]]
    for e in v["elemanlar"]:
        assert {"no", "dugumler", "L", "c", "s", "uc_kuvvetleri", "N", "durum", "diyagram"} <= set(e)
        assert e["durum"] in ("çekme", "basınç", "sıfır", "eğilme")
        assert set(e["diyagram"]) == {"x", "N", "V", "M"}
    assert v["olcek"] is None or v["olcek"] > 0


@pytest.mark.parametrize("ad", ["yay-seri", "kafes-iki-cubuk", "kiris-basit-yayili", "cerceve-portal"])
def test_json_metni_girdi_olarak_kabul_edilir(ad):
    a = se.se_coz(json.dumps(se.ornek_model(ad), ensure_ascii=False))
    assert a.deger == coz(ad).deger
    assert a.veri["u"] == coz(ad).veri["u"]


def test_goster_yok_ve_son_anlatim():
    r = se.se_coz(se.ornek_model("yay-seri"), goster="yok")
    assert mo.son_anlatim is r.anlatim


# ---------------------------------------------------------------------------
# Anlatım, şema sözleşmesi, Python betiği
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", ADLAR)
def test_anlatim_adimlari_ve_markdown(ad):
    r = coz(ad)
    metin = anlatim_metni(r)
    for i in range(1, 12):
        assert f"{i}. Adım" in metin, (ad, i)
    md = r.markdown()
    assert isinstance(md, str) and len(md) > 2000
    assert "Traceback" not in md and "[Hata" not in md
    assert md.count("```python") >= 1


@pytest.mark.parametrize("ad", ADLAR)
def test_sema_sozlesmesi(ad):
    r = coz(ad)
    semalar = [b for b in r.anlatim.bloklar if b[0] == "sema"]
    benim = [b for b in semalar if b[1]["baslik"] in ("Yapı modeli", "Sonuçlar")]
    basliklar = [b[1]["baslik"] for b in benim]
    assert basliklar.count("Yapı modeli") == 1 and basliklar.count("Sonuçlar") == 1
    # yapı şeması sonuçlardan önce gelir
    sira = [b[1]["baslik"] for b in r.anlatim.bloklar if b[0] == "sema"]
    assert sira.index("Yapı modeli") < sira.index("Sonuçlar")
    for b in benim + [b for b in semalar if b[1]["baslik"] == "Doluluk haritası"]:
        veri = b[1]
        assert not re.search(r"\d", veri["baslik"]), veri["baslik"]
        assert len(veri["kareler"]) >= 2
        for kare in veri["kareler"]:
            assert kare["baslik"].strip()
            svg = kare["svg"]
            assert svg.lstrip().startswith("<svg"), kare["baslik"]
            assert "<marker" not in svg and "<script" not in svg
            assert 'fill="var(' not in svg and 'stroke="var(' not in svg
            assert "javascript:" not in svg.lower() and " onload=" not in svg
            assert svg.count("<svg") == 1 and svg.rstrip().endswith("</svg>")


def test_sonuc_semasi_kareleri():
    kareler = {k["baslik"] for b in coz("cerceve-portal").anlatim.bloklar if b[0] == "sema"
               and b[1]["baslik"] == "Sonuçlar" for k in b[1]["kareler"]}
    assert {"Şekil değiştirmiş biçim", "Eksenel kuvvet N diyagramı", "Kesme kuvveti V diyagramı",
            "Eğilme momenti M diyagramı", "Mesnet tepkileri"} <= kareler
    kareler = {k["baslik"] for b in coz("kafes-iki-cubuk").anlatim.bloklar if b[0] == "sema"
               and b[1]["baslik"] == "Sonuçlar" for k in b[1]["kareler"]}
    assert "Şekil değiştirmiş biçim" in kareler and "Mesnet tepkileri" in kareler
    assert not any("Kesme" in k or "Eğilme" in k for k in kareler)    # kafeste V/M diyagramı yok


@pytest.mark.parametrize("ad", ADLAR)
def test_python_betigi_calisir_ve_sonucla_tutarlidir(ad):
    r = coz(ad)
    assert r.python_kodu.strip() and r.python_ciktisi.strip()
    assert "Traceback" not in r.python_ciktisi and "[Hata" not in r.python_ciktisi
    ns: dict = {"__name__": "betik"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(r.python_kodu, "<betik>", "exec"), ns)
    u_betik = [float(sp.N(x)) for x in ns["u"]]
    assert yakin(u_betik, r.veri["u"], rtol=1e-9, atol=1e-12), ad
    # kod bloğu anlatımda da vardır
    kodlar = [b for b in r.anlatim.bloklar if b[0] == "kod"]
    assert len(kodlar) == 1
    baslik, kod, cikti = kodlar[0][1]
    assert kod.strip() == r.python_kodu.strip() and cikti.strip() == r.python_ciktisi.strip()


def test_ondalik_ayari_sonucu_degistirmez():
    kesin = coz("kiris-konsol")
    mo.ayarla(ondalik=True)
    r = se.se_coz(se.ornek_model("kiris-konsol"))
    assert yakin(r.veri["u"], kesin.veri["u"], rtol=1e-12, atol=1e-15)
    assert r.markdown()


@pytest.mark.parametrize("ad", ADLAR)
def test_hiz(ad):
    t0 = time.perf_counter()
    se.se_coz(se.ornek_model(ad))
    assert time.perf_counter() - t0 < 10.0


# ---------------------------------------------------------------------------
# Öğretici hata iletileri
# ---------------------------------------------------------------------------
HATALAR = [
    ("sifir-boy", "kafes-iki-cubuk", lambda m: m["dugumler"][2].update(x=0, y=0), "boyu sıfır"),
    ("kopuk-dugum", "yay-seri", lambda m: m["dugumler"].append({"no": 4, "x": 3, "y": 0}),
     "hiçbir elemana bağlı değil"),
    ("mesnetsiz", "kiris-konsol", lambda m: m.update(mesnetler=[]), "Mesnetler yetersiz"),
    ("mesnet-yetersiz-kafes", "kafes-iki-cubuk",
     lambda m: m.update(mesnetler=[{"dugum": 1, "ux": True, "uy": True}]), "mekanizma"),
    ("bilinmeyen-tip", "yay-seri", lambda m: m.update(tip="plak"), "Bilinmeyen model türü"),
    ("cift-dugum", "yay-seri", lambda m: m["dugumler"][1].update(no=1), "iki kez tanımlandı"),
    ("cift-eleman", "yay-seri", lambda m: m["elemanlar"][1].update(no=1), "iki kez tanımlandı"),
    ("tanimsiz-dugume-eleman", "yay-seri", lambda m: m["elemanlar"][0].update(dugumler=[1, 9]),
     "tanımsız bir düğüme bağlı"),
    ("negatif-E", "cubuk-kademeli", lambda m: m["elemanlar"][0].update(E="-5"), "pozitif bir sayı"),
    ("sifir-A", "cubuk-kademeli", lambda m: m["elemanlar"][0].update(A=0), "pozitif bir sayı"),
    ("eksik-E", "cubuk-kademeli", lambda m: m["elemanlar"][0].pop("E"), "verilmedi"),
    ("kiris-farkli-y", "kiris-konsol", lambda m: m["dugumler"][1].update(y=1), "aynı yatay"),
    ("kiris-sagdan-sola", "kiris-konsol", lambda m: m["elemanlar"][0].update(dugumler=[2, 1]), "soldan sağa"),
    ("kafeste-yayili", "kafes-iki-cubuk", lambda m: m.update(yayili=[{"eleman": 1, "q": -1}]),
     "yalnız kiriş ve çerçeve"),
    ("harfli-koordinat", "kafes-iki-cubuk", lambda m: m["dugumler"][1].update(x="a"), "sayı olmalı"),
    ("bos-dugum", "yay-seri", lambda m: m.update(dugumler=[]), "Modelde düğüm yok"),
    ("bos-eleman", "yay-seri", lambda m: m.update(elemanlar=[]), "Modelde eleman yok"),
    ("yay-Fy", "yay-seri", lambda m: m["yukler"][0].update(Fy=5), "etkisizdir"),
    ("kafes-M", "kafes-iki-cubuk", lambda m: m["yukler"][0].update(M=5), "etkisizdir"),
    ("yuk-tanimsiz-dugum", "kafes-iki-cubuk", lambda m: m["yukler"][0].update(dugum=99), "tanımsız bir düğümde"),
    ("mesnet-tanimsiz-dugum", "kafes-iki-cubuk", lambda m: m["mesnetler"][0].update(dugum=99),
     "tanımsız bir düğümde"),
    ("yayili-tanimsiz-eleman", "kiris-basit-yayili", lambda m: m["yayili"][0].update(eleman=9),
     "tanımsız bir elemanda"),
    ("kesirli-dugum-no", "yay-seri", lambda m: m["dugumler"][0].update(no=1.5), "tam sayı olmalı"),
    ("tek-dugumlu-eleman", "yay-seri", lambda m: m["elemanlar"][0].update(dugumler=[1]), "iki düğüm numarası"),
    ("sembolik-sd-asimi", "kafes-pratt-kopru", lambda m: m["elemanlar"][0].update(E="E"), "en çok 12"),
]


@pytest.mark.parametrize("ad,on,degistir,anahtar", [pytest.param(a, b, c, d, id=a) for a, b, c, d in HATALAR])
def test_ogretici_hatalar(ad, on, degistir, anahtar):
    m = se.ornek_model(on)
    degistir(m)
    with pytest.raises(mo.MatrisHatasi) as h:
        se.se_coz(m)
    assert anahtar in str(h.value), str(h.value)


def test_hata_json_ve_tur():
    with pytest.raises(mo.MatrisHatasi, match="JSON"):
        se.se_coz("{bozuk json")
    with pytest.raises(mo.MatrisHatasi, match="sözlük"):
        se.se_coz([1, 2, 3])
