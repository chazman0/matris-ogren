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
from collections import defaultdict
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
_D = {"yay": 1, "cubuk": 1, "kafes": 2, "kiris": 2, "cerceve": 3, "kafes3b": 3, "cerceve3b": 6}
_YUK = {"yay": {"Fx": 0}, "cubuk": {"Fx": 0}, "kafes": {"Fx": 0, "Fy": 1},
        "kiris": {"Fy": 0, "M": 1}, "cerceve": {"Fx": 0, "Fy": 1, "M": 2},
        "kafes3b": {"Fx": 0, "Fy": 1, "Fz": 2},
        "cerceve3b": {"Fx": 0, "Fy": 1, "Fz": 2, "Mx": 3, "My": 4, "Mz": 5}}
_MESNET = {"yay": ["ux"], "cubuk": ["ux"], "kafes": ["ux", "uy"], "kiris": ["uy", "rz"],
           "cerceve": ["ux", "uy", "rz"], "kafes3b": ["ux", "uy", "uz"],
           "cerceve3b": ["ux", "uy", "uz", "rx", "ry", "rz"]}
_YAY = {"yay": ["kx"], "cubuk": ["kx"], "kafes": ["kx", "ky"], "kiris": ["ky", "kr"],
        "cerceve": ["kx", "ky", "kr"], "kafes3b": ["kx", "ky", "kz"],
        "cerceve3b": ["kx", "ky", "kz", "krx", "kry", "krz"]}
UC_BOYUT = ("kafes3b", "cerceve3b")


def _hermite_N(x, L):
    """Hermite şekil fonksiyonları [N1, N2, N3, N4] (v1, θ1, v2, θ2)."""
    xi = x / L
    return np.array([1 - 3 * xi ** 2 + 2 * xi ** 3, L * (xi - 2 * xi ** 2 + xi ** 3),
                     3 * xi ** 2 - 2 * xi ** 3, L * (-xi ** 2 + xi ** 3)])


def _gauss_integral(f, L, n=6):
    """∫₀ᴸ f(x) dx, Gauss–Legendre (f dizi döndürebilir)."""
    p, w = np.polynomial.legendre.leggauss(n)
    top = 0
    for pi, wi in zip(p, w):
        top = top + wi * f((pi + 1) * L / 2)
    return top * L / 2


def _winkler_k(ks, L):
    """Winkler zemin matrisi: ∫ k_s Nᵀ N dx sayısal integrasyonla (çözücüden bağımsız)."""
    return _gauss_integral(lambda x: ks * np.outer(_hermite_N(x, L), _hermite_N(x, L)), L)


def _feq_sayisal(q, L):
    """Düzgün q için ∫ Nᵀ q dx (v, θ sırası)."""
    return _gauss_integral(lambda x: q * _hermite_N(x, L), L)


def _lam3b(cx, cy, cz):
    """Yerel eksenler vektörel çarpımla: z' = x' × Y, y' = z' × x'; düşeyde z' = Z."""
    xp = np.array([cx, cy, cz])
    zp = np.cross(xp, [0.0, 1.0, 0.0])
    if np.linalg.norm(zp) < 1e-9:
        zp = np.array([0.0, 0.0, 1.0])
    else:
        zp = zp / np.linalg.norm(zp)
    yp = np.cross(zp, xp)
    return np.vstack([xp, yp, zp])


def _cerceve3b_k(EA, GJ, EIy, EIz, L):
    """12×12 uzay çerçeve matrisi, 2×2 ve 4×4 bloklardan kurulur (θ_y için işaret çevirme matrisiyle)."""
    k = np.zeros((12, 12))
    eks = np.array([[1.0, -1.0], [-1.0, 1.0]])
    k[np.ix_([0, 6], [0, 6])] += EA / L * eks
    k[np.ix_([3, 9], [3, 9])] += GJ / L * eks
    kz = _kiris_k(EIz, L)
    k[np.ix_([1, 5, 7, 11], [1, 5, 7, 11])] += kz
    S = np.diag([1.0, -1.0, 1.0, -1.0])      # θ_y = −w'
    k[np.ix_([2, 4, 8, 10], [2, 4, 8, 10])] += S @ _kiris_k(EIy, L) @ S
    return k


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
    """Modeli bağımsız olarak çözer (2B, 3B, yaylar, Winkler zemin, mesnet çökmesi).
    Dönüş: u, R (= K u - F), eleman listesi [(f_yerel, N)], K, F."""
    tip = m["tip"]
    d = _D[tip]
    sira = {dg["no"]: i for i, dg in enumerate(m["dugumler"])}
    xyz = np.array([[float(dg.get("x", 0)), 0.0 if tip in ("yay", "cubuk") else float(dg.get("y", 0)),
                     float(dg.get("z", 0)) if tip in UC_BOYUT else 0.0] for dg in m["dugumler"]])
    n = d * len(sira)
    K = np.zeros((n, n))
    F = np.zeros(n)
    qlar, qzlar = defaultdict(float), defaultdict(float)
    for y in m.get("yayili", []):          # aynı elemana birden çok yayılı yük verilmişse toplanır
        qlar[y["eleman"]] += float(y.get("q", 0) or 0)
        qzlar[y["eleman"]] += float(y.get("qz", 0) or 0)
    eleman_verisi = []
    for e in m["elemanlar"]:
        a, b = (sira[v] for v in e["dugumler"])
        dx, dy, dz = xyz[b] - xyz[a]
        L = float(np.sqrt(dx * dx + dy * dy + dz * dz))
        c, s = dx / L, dy / L
        q = qlar.get(e["no"], 0.0)
        ks = float(e.get("zemin") or 0)
        EA = float(e["E"]) * float(e["A"]) if "A" in e and "E" in e else 0.0
        if tip == "yay":
            kl, T, feq = float(e["k"]) * np.array([[1.0, -1.0], [-1.0, 1.0]]), np.eye(2), np.zeros(2)
        elif tip == "cubuk":
            kl, T, feq = EA / L * np.array([[1.0, -1.0], [-1.0, 1.0]]), np.eye(2), np.zeros(2)
        elif tip == "kafes":
            v = np.array([-c, -s, c, s])
            kl, T, feq = EA / L * np.outer(v, v), np.eye(4), np.zeros(4)
        elif tip == "kafes3b":
            cx, cy, cz = dx / L, dy / L, dz / L
            v = np.array([-cx, -cy, -cz, cx, cy, cz])
            kl, T, feq = EA / L * np.outer(v, v), np.eye(6), np.zeros(6)
        elif tip == "kiris":
            EI = float(e["E"]) * float(e["I"])
            kl, T = _kiris_k(EI, L), np.eye(4)
            feq = _feq_sayisal(q, L)
            if ks:
                kl = kl + _winkler_k(ks, L)
        elif tip == "cerceve":
            EI = float(e["E"]) * float(e["I"])
            kl = _cerceve_k(EA, EI, L)
            if ks:
                kl[np.ix_([1, 2, 4, 5], [1, 2, 4, 5])] += _winkler_k(ks, L)
            t3 = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
            T = np.block([[t3, np.zeros((3, 3))], [np.zeros((3, 3)), t3]])
            fq = _feq_sayisal(q, L)
            feq = np.array([0, fq[0], fq[1], 0, fq[2], fq[3]])
        else:
            E = float(e["E"])
            kl = _cerceve3b_k(EA, float(e["G"]) * float(e["J"]), E * float(e["Iy"]), E * float(e["Iz"]), L)
            lam = _lam3b(dx / L, dy / L, dz / L)
            T = np.kron(np.eye(4), lam)
            fq, fz = _feq_sayisal(q, L), _feq_sayisal(qzlar.get(e["no"], 0.0), L)
            feq = np.array([0, fq[0], fz[0], 0, -fz[1], fq[1], 0, fq[2], fz[2], 0, -fz[3], fq[3]])
        dofs = [d * a + j for j in range(d)] + [d * b + j for j in range(d)]
        ke = T.T @ kl @ T
        K[np.ix_(dofs, dofs)] += ke
        F[dofs] += T.T @ feq
        eleman_verisi.append((kl, T, dofs, feq, c, s, EA, L))
    for y in m.get("yukler", []):
        i = sira[y["dugum"]]
        for ad, j in _YUK[tip].items():
            F[d * i + j] += float(y.get(ad, 0) or 0)
    for y in m.get("yaylar", []):
        i = sira[y["dugum"]]
        for j, ad in enumerate(_YAY[tip]):
            K[d * i + j, d * i + j] += float(y.get(ad, 0) or 0)
    tutulu = []
    for ms in m.get("mesnetler", []):
        i = sira[ms["dugum"]]
        for j, ad in enumerate(_MESNET[tip]):
            if ms.get(ad):
                tutulu.append(d * i + j)
    u = np.zeros(n)
    for c_ in m.get("cokmeler", []):
        i = sira[c_["dugum"]]
        for j, ad in enumerate(_MESNET[tip]):
            if c_.get(ad) is not None:
                tutulu.append(d * i + j)
                u[d * i + j] = float(c_[ad])
    tutulu = sorted(set(tutulu))
    serbest = [i for i in range(n) if i not in tutulu]
    sag = F[serbest] - K[np.ix_(serbest, tutulu)] @ u[tutulu]
    u[serbest] = np.linalg.solve(K[np.ix_(serbest, serbest)], sag)
    Rt = K @ u - F
    uc = []
    for kl, T, dofs, feq, c, s, EA, L in eleman_verisi:
        f = kl @ (T @ u[dofs]) - feq
        if tip in ("kafes", "kafes3b"):
            # çubuk ekseni yönündeki birim vektör: global uç kuvvetinin (j ucu) eksene izdüşümü = N
            yon = np.array([c, s]) if tip == "kafes" else (xyz[dofs[d] // d] - xyz[dofs[0] // d]) / L
            N = float(f[d:] @ yon)
        elif tip in ("yay", "cubuk"):
            N = float(f[1])
        elif tip in ("cerceve", "cerceve3b"):
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
                     "kiris-konsol", "kiris-basit-yayili", "kiris-ankastre-mafsalli", "kiris-elastik-zemin",
                     "cerceve-konsol-kolon", "cerceve-portal", "cerceve-iki-katli", "cerceve-elastik-mesnet",
                     "cerceve-mesnet-cokmesi", "cerceve-temel-kirisi",
                     "kafes3b-tripod", "kafes3b-kule",
                     "cerceve3b-konsol-L", "cerceve3b-izgara", "cerceve3b-portal"]
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
            ms = next((x for x in m["mesnetler"] if x["dugum"] == t["dugum"]), {})
            bayrak = _MESNET[m["tip"]][_YUK[m["tip"]][ad_bilesen]]
            if ms.get(bayrak):
                assert t[ad_bilesen] == pytest.approx(Rt[idx], rel=1e-8, abs=1e-8), (ad, t["dugum"], ad_bilesen)
    # yük bileşeni olmayan eksen sıfır yazılır
    for t in v["tepkiler"]:
        if m["tip"] in UC_BOYUT:
            assert set(t) == {"dugum", "Fx", "Fy", "Fz", "Mx", "My", "Mz"}
        else:
            assert set(t) == {"dugum", "Fx", "Fy", "M"}
    # yay kuvvetleri −k·u
    for y in v["yaylar"]:
        i = sira[y["dugum"]]
        j = _YUK[m["tip"]][y["bilesen"]]
        assert y["kuvvet"] == pytest.approx(-y["k"] * u[d * i + j], rel=1e-9, abs=1e-9)


@pytest.mark.parametrize("ad", ADLAR)
def test_bagimsiz_referans_eleman_kuvvetleri(ad):
    r = coz(ad)
    m = se.ornek_model(ad)
    u, Rt, uc, K, F = referans(m)
    for e, (f, N) in zip(r.veri["elemanlar"], uc):
        if m["tip"] in ("kiris", "cerceve", "cerceve3b"):
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
    "kiris-elastik-zemin": 0,            # zemin her serbestliği tutar
    "cerceve-konsol-kolon": 3, "cerceve-portal": 3, "cerceve-iki-katli": 3, "cerceve-mesnet-cokmesi": 3,
    "cerceve-elastik-mesnet": 0,         # yaylar üç rijit hareketi de tutar
    "cerceve-temel-kirisi": 1,           # zemin yalnız düşeyi tutar: yatay öteleme kalır
    "kafes3b-tripod": 9,                 # 6 rijit + 3 (taban düğümleri birbirine bağlı değil)
    "kafes3b-kule": 11,                  # 24 SD − 13 çubuk
    "cerceve3b-konsol-L": 6, "cerceve3b-izgara": 6, "cerceve3b-portal": 6,   # uzay: 6 rijit hareket
}


@pytest.mark.parametrize("ad", ADLAR)
def test_rijit_cisim_ozdegerleri(ad):
    K = np.array(coz(ad).veri["K"], dtype=float)
    w = np.linalg.eigvalsh((K + K.T) / 2)
    esik = 1e-9 * np.max(np.abs(w))
    assert int(np.sum(np.abs(w) < esik)) == SIFIR_OZDEGER[ad], (ad, w[:12])
    assert w.min() > -esik   # yarı pozitif tanımlı


def tepki_vektoru(v):
    """veri → tüm SD'ler üzerinde tepki vektörü (tutulu SD'lerde değer, kalanı 0)."""
    tip, d = v["tip"], _D[v["tip"]]
    sira = {dg["no"]: i for i, dg in enumerate(v["dugumler"])}
    R = np.zeros(v["sd_sayisi"])
    for t in v["tepkiler"]:
        for ad, j in _YUK[tip].items():
            R[d * sira[t["dugum"]] + j] += t[ad]
    return R


def yay_zemin_vektoru(v):
    """Yay kuvvetleri ve zemin kuvvetlerinin SD vektörü."""
    tip, d = v["tip"], _D[v["tip"]]
    sira = {dg["no"]: i for i, dg in enumerate(v["dugumler"])}
    Y = np.zeros(v["sd_sayisi"])
    for y in v["yaylar"]:
        Y[d * sira[y["dugum"]] + _YUK[tip][y["bilesen"]]] += y["kuvvet"]
    for e in v["elemanlar"]:
        if e.get("zemin_kuvvetleri"):
            a, b = (sira[k] for k in e["dugumler"])
            dofs = [d * a + j for j in range(d)] + [d * b + j for j in range(d)]
            Y[dofs] += np.array(e["zemin_kuvvetleri"])
    return Y


@pytest.mark.parametrize("ad", ADLAR)
def test_denge_ve_enerji(ad):
    v = coz(ad).veri
    uc = v["tip"] in UC_BOYUT
    assert set(v["denge"]) == ({"Fx", "Fy", "Fz", "Mx", "My", "Mz"} if uc else {"Fx", "Fy", "M"})
    for k, deger in v["denge"].items():
        assert abs(deger) < 1e-7, (ad, k, deger)
    # tepkiler + yükler + yay/zemin kuvvetleri: bağımsız toplam (kuvvet bileşenleri)
    d = _D[v["tip"]]
    F, R, Y = np.array(v["F"]), tepki_vektoru(v), yay_zemin_vektoru(v)
    for ad_b, j in _YUK[v["tip"]].items():
        if ad_b.startswith("M"):
            continue
        top = sum((F + R + Y)[d * i + j] for i in range(len(v["dugumler"])))
        assert top == pytest.approx(0.0, abs=1e-7), (ad, ad_b)
    # Clapeyron: U = 1/2 u^T K u = W = 1/2 u^T (F + R) > 0 (R yalnız mesnet çökmesinde iş yapar)
    u, K = np.array(v["u"]), np.array(v["K"])
    U, W = 0.5 * u @ K @ u, 0.5 * u @ (F + R)
    assert W > 0
    assert U == pytest.approx(W, rel=1e-8)
    if not v["cokmeler"]:
        assert W == pytest.approx(0.5 * u @ F, rel=1e-8)


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
    assert {"tip", "baslik", "birim", "mod", "sd_sayisi", "sd_etiketleri", "boyut", "dugumler", "elemanlar",
            "tepkiler", "yaylar", "cokmeler", "u", "F", "denge", "olcek", "K"} <= set(v)
    assert v["birim"] == {"kuvvet": "kN", "uzunluk": "m"}
    assert v["boyut"] == (3 if v["tip"] in UC_BOYUT else 2)
    n = v["sd_sayisi"]
    assert n == _D[v["tip"]] * len(v["dugumler"]) == len(v["u"]) == len(v["F"]) == len(v["sd_etiketleri"])
    assert len(v["K"]) == n and all(len(s) == n for s in v["K"])
    for i, dg in enumerate(v["dugumler"]):
        assert set(dg) == {"no", "x", "y", "z", "sd", "u"}
        assert dg["sd"] == [_D[v["tip"]] * i + j + 1 for j in range(_D[v["tip"]])]
        assert dg["u"] == [v["u"][k - 1] for k in dg["sd"]]
    for e in v["elemanlar"]:
        assert {"no", "dugumler", "L", "c", "s", "uc_kuvvetleri", "N", "durum", "diyagram", "zemin"} <= set(e)
        assert e["durum"] in ("çekme", "basınç", "sıfır", "eğilme")
        if v["tip"] == "cerceve3b":
            assert set(e["diyagram"]) == {"x", "N", "V", "M", "Vz", "My", "T"}
            assert len(e["lam"]) == 3 and all(len(s) == 3 for s in e["lam"])
            lam = np.array(e["lam"])
            assert np.allclose(lam @ lam.T, np.eye(3), atol=1e-9)        # dik birim eksen takımı
            assert np.allclose(np.cross(lam[0], lam[1]), lam[2], atol=1e-9)   # sağ el: z' = x' × y'
            assert lam[1][1] >= -1e-12                                   # y' yukarı bakar
        else:
            assert set(e["diyagram"]) == {"x", "N", "V", "M"}
        if v["tip"] in UC_BOYUT:
            assert np.linalg.norm(e["yon"]) == pytest.approx(1.0)
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
    kareler = {k["baslik"] for b in coz("cerceve3b-konsol-L").anlatim.bloklar if b[0] == "sema"
               and b[1]["baslik"] == "Sonuçlar" for k in b[1]["kareler"]}
    assert {"Kesme kuvveti V diyagramı", "Eğilme momenti M diyagramı", "Burulma momenti T diyagramı",
            "Mesnet tepkileri"} <= kareler
    assert not any("Vz" in k or "My" in k for k in kareler)        # bu yükte x'z' düzleminde eğilme yok
    kareler = {k["baslik"] for b in coz("cerceve3b-portal").anlatim.bloklar if b[0] == "sema"
               and b[1]["baslik"] == "Sonuçlar" for k in b[1]["kareler"]}
    assert {"Eksenel kuvvet N diyagramı", "Kesme kuvveti V diyagramı", "Eğilme momenti M diyagramı",
            "Kesme kuvveti Vz diyagramı", "Eğilme momenti My diyagramı", "Burulma momenti T diyagramı"} <= kareler
    kareler = {k["baslik"] for b in coz("kiris-elastik-zemin").anlatim.bloklar if b[0] == "sema"
               and b[1]["baslik"] == "Sonuçlar" for k in b[1]["kareler"]}
    assert "Zemin basıncı diyagramı" in kareler


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
    ("zemin-kafeste", "kafes-iki-cubuk", lambda m: m["elemanlar"][0].update(zemin=100), "yalnız kiriş ve düzlem çerçeve"),
    ("zemin-negatif", "kiris-konsol", lambda m: m["elemanlar"][0].update(zemin=-5), "negatif olamaz"),
    ("qz-duzlemde", "kiris-basit-yayili", lambda m: m["yayili"][0].update(qz=5), "yalnız uzay çerçevede"),
    ("yay-negatif", "cerceve-portal", lambda m: m.update(yaylar=[{"dugum": 1, "ky": -5}]), "negatif olamaz"),
    ("yay-yanlis-anahtar", "kiris-konsol", lambda m: m.update(yaylar=[{"dugum": 1, "kx": 5}]), "tanımlı değil"),
    ("yay-tanimsiz-dugum", "cerceve-portal", lambda m: m.update(yaylar=[{"dugum": 9, "ky": 5}]), "tanımsız bir düğümde"),
    ("cokme-tanimsiz-dugum", "cerceve-portal", lambda m: m.update(cokmeler=[{"dugum": 9, "uy": -0.01}]),
     "tanımsız bir düğümde"),
    ("cokme-yanlis-anahtar", "cerceve-portal", lambda m: m.update(cokmeler=[{"dugum": 1, "uz": -0.01}]), "tanımlı değil"),
    ("3b-mesnet-yetersiz", "kafes3b-tripod", lambda m: m.update(mesnetler=m["mesnetler"][:2]), "mekanizma"),
    ("3b-eksik-J", "cerceve3b-konsol-L", lambda m: m["elemanlar"][0].pop("J"), "verilmedi"),
    ("3b-sifir-boy", "kafes3b-tripod", lambda m: m["dugumler"][3].update(x=4, y=0, z=0), "boyu sıfır"),
    ("3b-Mz-kafeste", "kafes3b-tripod", lambda m: m["yukler"][0].update(Mz=5), "etkisizdir"),
    ("3b-sembolik-sd-asimi", "cerceve3b-konsol-L", lambda m: m["elemanlar"][0].update(E="E"), "en çok 12"),
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


# ---------------------------------------------------------------------------
# 3 boyutlu yapılar: kapalı form ve tutarlılık
# ---------------------------------------------------------------------------
def test_kafes3b_tripod_kesin_cubuk_kuvvetleri():
    """Tepe düğümünün dengesinden: N1 = −225/8, N2 = −25/4, N3 = −125/8 (hepsi basınç)."""
    r = coz("kafes3b-tripod")
    v = r.veri
    assert v["mod"] == "kesin" and v["boyut"] == 3 and v["sd_sayisi"] == 12
    assert [e["N"] for e in v["elemanlar"]] == pytest.approx([-28.125, -6.25, -15.625])
    assert [e["durum"] for e in v["elemanlar"]] == ["basınç"] * 3
    assert all(e["L"] == pytest.approx(5.0) for e in v["elemanlar"])
    assert v["elemanlar"][0]["yon"] == pytest.approx([-0.8, 0.6, 0.0])
    # tepkiler yükü dengeler
    assert sum(t["Fx"] for t in v["tepkiler"]) == pytest.approx(-10.0)
    assert sum(t["Fy"] for t in v["tepkiler"]) == pytest.approx(30.0)
    assert sum(t["Fz"] for t in v["tepkiler"]) == pytest.approx(-5.0)
    # kesin kesirler
    N = [sp.nsimplify(x) for x in (R(-225, 8), R(-25, 4), R(-125, 8))]
    metin = anlatim_metni(r)
    assert r"\frac{225}{8}" in metin and r"\frac{125}{8}" in metin
    assert float(N[0]) == v["elemanlar"][0]["N"]


def test_cerceve3b_konsol_L_kapali_form():
    """δ = P L₂³/3EI + P L₁³/3EI + P L₂² L₁/GJ = 0.0013333 + 0.0045 + 0.0075 = 0.0133333 m (aşağı)."""
    v = coz("cerceve3b-konsol-L").veri
    P, L1, L2, EI, GJ = 10.0, 3.0, 2.0, 200e6 * 1e-4, 80e6 * 2e-4
    beklenen = -(P * L2 ** 3 / (3 * EI) + P * L1 ** 3 / (3 * EI) + P * L2 ** 2 * L1 / GJ)
    uc = {d["no"]: d for d in v["dugumler"]}[3]
    assert uc["u"][1] == pytest.approx(beklenen, rel=1e-9)
    # birinci kolda burulma T = P·L₂ = 20 kN·m sabittir; ikinci kolda burulma yok
    d1, d2 = v["elemanlar"][0]["diyagram"], v["elemanlar"][1]["diyagram"]
    assert all(abs(abs(t) - 20.0) < 1e-6 for t in d1["T"])
    assert all(abs(t) < 1e-6 for t in d2["T"])
    # ankastre tepkileri: Ry = P, Mz = P·L₁ = 30, Mx (burulma) = ∓P·L₂ = 20
    t = v["tepkiler"][0]
    assert t["Fy"] == pytest.approx(10.0) and abs(t["Mz"]) == pytest.approx(30.0) and abs(t["Mx"]) == pytest.approx(20.0)


def test_cerceve3b_duzlemde_2b_cerceveyle_ozdes():
    """z = 0 düzlemindeki uzay çerçeve, aynı 2B portal çerçeveyle aynı u, N, V, M'yi verir (yerel eksen kuralı tutarlı)."""
    m2 = se.ornek_model("cerceve-portal")
    m3 = {"tip": "cerceve3b", "baslik": "3B portal",
          "dugumler": [dict(dg, z=0) for dg in m2["dugumler"]],
          "elemanlar": [{"no": e["no"], "dugumler": e["dugumler"], "E": e["E"], "G": "80e6", "A": e["A"],
                         "Iy": "5e-4", "Iz": e["I"], "J": "7e-4"} for e in m2["elemanlar"]],
          "mesnetler": [{"dugum": ms["dugum"], "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}
                        for ms in m2["mesnetler"]],
          "yukler": m2["yukler"], "yayili": m2["yayili"]}
    r2, r3 = coz("cerceve-portal"), se.se_coz(m3)
    u2 = np.array(r2.veri["u"]).reshape(-1, 3)
    u3 = np.array(r3.veri["u"]).reshape(-1, 6)
    assert np.allclose(u2, u3[:, [0, 1, 5]], rtol=1e-9, atol=1e-14)
    assert np.allclose(u3[:, [2, 3, 4]], 0.0, atol=1e-14)          # düzlem dışı hareket yok
    for e2, e3 in zip(r2.veri["elemanlar"], r3.veri["elemanlar"]):
        assert e3["N"] == pytest.approx(e2["N"], rel=1e-9)
        for k in ("V", "M"):
            assert yakin(e3["diyagram"][k], e2["diyagram"][k], rtol=1e-9, atol=1e-9)
        assert yakin(e3["diyagram"]["Vz"], 0.0, atol=1e-9) and yakin(e3["diyagram"]["My"], 0.0, atol=1e-9)
    for t2, t3 in zip(r2.veri["tepkiler"], r3.veri["tepkiler"]):
        assert (t3["Fx"], t3["Fy"], t3["Mz"]) == pytest.approx((t2["Fx"], t2["Fy"], t2["M"]))


def test_cerceve3b_dusey_eleman_yerel_eksen():
    """Düşey kolon: Kassimali kuralı z' = Z, y' = −X (yukarı giden kolon); aşağı tanımlı kolonda y' = +X."""
    m = se.ornek_model("cerceve3b-konsol-L")
    m["dugumler"] = [{"no": 1, "x": 0, "y": 0, "z": 0}, {"no": 2, "x": 0, "y": 3, "z": 0}, {"no": 3, "x": 0, "y": 0, "z": 2}]
    m["elemanlar"][1]["dugumler"] = [2, 3]
    v = se.se_coz(m).veri
    lam = np.array(v["elemanlar"][0]["lam"])
    assert np.allclose(lam, [[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    m["elemanlar"][0]["dugumler"] = [2, 1]
    m["elemanlar"][1]["dugumler"] = [1, 3]
    m["mesnetler"][0]["dugum"] = 2
    v = se.se_coz(m).veri
    lam = np.array(v["elemanlar"][0]["lam"])
    assert np.allclose(lam, [[0, -1, 0], [1, 0, 0], [0, 0, 1]])


def test_cerceve3b_izgara_simetri_ve_tepkiler():
    v = coz("cerceve3b-izgara").veri
    dg = {d["no"]: d for d in v["dugumler"]}
    # simetrik yük: dört köşe tepkisi eşit, toplam = 120 kN
    assert [t["Fy"] for t in v["tepkiler"]] == pytest.approx([30.0] * 4)
    # orta düğüm en çok çöker; kenar ortaları birbirine eşit
    assert dg[5]["u"][1] < dg[2]["u"][1] < 0
    assert dg[2]["u"][1] == pytest.approx(dg[4]["u"][1]) == pytest.approx(dg[6]["u"][1]) == pytest.approx(dg[8]["u"][1])
    # ızgara: düzlem içi serbestlikler (u, w, θy) sıfır
    for d in v["dugumler"]:
        assert abs(d["u"][0]) < 1e-12 and abs(d["u"][2]) < 1e-12 and abs(d["u"][4]) < 1e-12


def test_cerceve3b_portal_denge_ve_simetri():
    v = coz("cerceve3b-portal").veri
    # yatay yük 30 kN: Rx toplamı −30; düşey yük 2 kiriş × 10 kN/m × 5 m = 100 kN; z yükü 10 kN
    assert sum(t["Fx"] for t in v["tepkiler"]) == pytest.approx(-30.0)
    assert sum(t["Fy"] for t in v["tepkiler"]) == pytest.approx(100.0)
    assert sum(t["Fz"] for t in v["tepkiler"]) == pytest.approx(10.0)
    # z yükü olmadan yapı z yönünde simetriktir: düğüm 5 ile 8, 6 ile 7 aynı u ve v
    m = se.ornek_model("cerceve3b-portal")
    m["yukler"] = [y for y in m["yukler"] if "Fz" not in y]
    dg = {d["no"]: d for d in se.se_coz(m).veri["dugumler"]}
    assert dg[5]["u"][:2] == pytest.approx(dg[8]["u"][:2]) and dg[6]["u"][:2] == pytest.approx(dg[7]["u"][:2])
    # z yükü, x doğrultusundaki kirişleri yatay düzlemde eğer: Vz ve My sıfırdan farklı
    e5 = {e["no"]: e for e in v["elemanlar"]}[5]["diyagram"]
    assert max(abs(x) for x in e5["My"]) > 1e-6 and max(abs(x) for x in e5["Vz"]) > 1e-6


def test_kafes3b_kule_cekme_basinc():
    v = coz("kafes3b-kule").veri
    N = {e["no"]: e["N"] for e in v["elemanlar"]}
    # rüzgâr +x yönünde: rüzgâr tarafındaki ayaklar (1, 4) daha az, arka ayaklar (2, 3) daha çok basınç taşır
    assert all(N[i] < 0 for i in (1, 2, 3, 4))
    assert N[1] + N[4] > N[2] + N[3]
    assert N[1] + N[2] + N[3] + N[4] < -80 * 0.9      # düşey yükün çoğunu ayaklar taşır (eğik ayak: |N| > Fy)
    assert sum(t["Fy"] for t in v["tepkiler"]) == pytest.approx(80.0)
    assert sum(t["Fx"] for t in v["tepkiler"]) == pytest.approx(-20.0)


# ---------------------------------------------------------------------------
# Temel sistemleri: elastik mesnet, Winkler zemin, mesnet çökmesi
# ---------------------------------------------------------------------------
def test_mesnet_cokmesi_kapali_form():
    """Bir ucu ankastre, diğer ucu kayıcı kiriş; kayıcı Δ kadar çökerse R_B = 3EIΔ/L³, M_A = 3EIΔ/L² (yük yok)."""
    m = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 4}],
         "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"}],     # EI = 4000
         "mesnetler": [{"dugum": 1, "uy": True, "rz": True}, {"dugum": 2, "uy": True}],
         "cokmeler": [{"dugum": 2, "uy": "-0.01"}], "yukler": []}
    r = se.se_coz(m)
    v = r.veri
    assert v["mod"] == "kesin"
    assert r.deger[2] == R(-1, 100) and r.deger[1] == 0          # u_s olduğu gibi; ankastre dönmesi 0
    t = {x["dugum"]: x for x in v["tepkiler"]}
    assert t[2]["Fy"] == pytest.approx(-1.875)         # 3·4000·0.01/64: kayıcı kirişi aşağı çeker
    assert t[1]["Fy"] == pytest.approx(1.875) and t[1]["M"] == pytest.approx(7.5)   # 3EIΔ/L² = 7.5
    assert v["cokmeler"] == [{"dugum": 2, "sd": "v₂", "deger": -0.01}]
    # kayıcıdaki dönme: θ_B = −3Δ/(2L) = −0.00375 (saat yönünde)
    assert r.deger[3] == R(-3, 800)
    metin = anlatim_metni(r)
    assert "\\mathbf{K}_{fs}" in metin and "Mesnet çökmesi" in metin
    # enerji: W = ½ uᵀ(F + R) = ½ · 0.01 · 1.875
    u, K = np.array(v["u"]), np.array(v["K"])
    assert 0.5 * u @ K @ u == pytest.approx(0.5 * 0.01 * 1.875)


def test_cokme_ile_yuk_superpozisyonu():
    """Çökme + yük çözümü, yalnız yük ve yalnız çökme çözümlerinin toplamıdır (doğrusal sistem)."""
    hepsi = coz("cerceve-mesnet-cokmesi").veri
    m_y = se.ornek_model("cerceve-mesnet-cokmesi")
    m_y["cokmeler"] = []
    m_c = se.ornek_model("cerceve-mesnet-cokmesi")
    m_c["yayili"] = []
    uy, uc_ = se.se_coz(m_y).veri["u"], se.se_coz(m_c).veri["u"]
    assert yakin(hepsi["u"], np.array(uy) + np.array(uc_), rtol=1e-9, atol=1e-15)
    # yalnız çökme: çökme tarafı daha az düşey tepki alır; toplam düşey tepki 0
    tc = {t["dugum"]: t for t in se.se_coz(m_c).veri["tepkiler"]}
    assert tc[1]["Fy"] + tc[4]["Fy"] == pytest.approx(0.0, abs=1e-9)
    assert tc[4]["Fy"] < 0 < tc[1]["Fy"]


def test_elastik_mesnet_kapali_form():
    """İki ucu düşey yaya oturan kiriş, ortadan P: v_orta = PL³/48EI + P/(2k); her yay P/2 taşır."""
    m = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 2}, {"no": 3, "x": 4}],
         "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"},
                       {"no": 2, "dugumler": [2, 3], "E": "200e6", "I": "2e-5"}],
         "mesnetler": [], "yaylar": [{"dugum": 1, "ky": 1000}, {"dugum": 3, "ky": 1000}],
         "yukler": [{"dugum": 2, "Fy": -10}]}
    r = se.se_coz(m)
    v = r.veri
    assert v["mod"] == "kesin" and v["tepkiler"] == []
    assert r.deger[2] == R(-1, 120)                   # −(1/300 + 1/200)
    assert r.deger[0] == r.deger[4] == R(-1, 200)     # yay çökmesi P/(2k)
    assert [y["kuvvet"] for y in v["yaylar"]] == pytest.approx([5.0, 5.0])
    assert [y["sd"] for y in v["yaylar"]] == ["v₁", "v₃"]
    # K köşegeninde yay var: K[0,0] = 12EI/L³ + k = 6000 + 1000
    assert v["K"][0][0] == pytest.approx(7000.0)
    metin = anlatim_metni(r)
    assert "köşegen" in metin and "Yay (elastik mesnet) kuvvetleri" in metin


def test_elastik_mesnet_cerceve_rijit_sinir():
    """Çok rijit yaylar ankastre mesnete, çok yumuşak dönme yayı mafsallı mesnede yaklaşır."""
    m = se.ornek_model("cerceve-elastik-mesnet")
    for y in m["yaylar"]:
        y.update(kx="1e12", ky="1e12", kr="1e12")
    u_rijit = np.array(se.se_coz(m).veri["u"])
    u_ank = np.array(coz("cerceve-portal").veri["u"])
    assert np.allclose(u_rijit, u_ank, rtol=1e-6, atol=1e-9)
    m2 = se.ornek_model("cerceve-portal")
    m2["mesnetler"] = [{"dugum": 1, "ux": True, "uy": True}, {"dugum": 4, "ux": True, "uy": True}]
    u_mafsal = np.array(se.se_coz(m2).veri["u"])
    m3 = se.ornek_model("cerceve-portal")
    m3["yaylar"] = [{"dugum": 1, "kr": "1e-6"}, {"dugum": 4, "kr": "1e-6"}]
    m3["mesnetler"] = [{"dugum": 1, "ux": True, "uy": True}, {"dugum": 4, "ux": True, "uy": True}]
    u_yumusak = np.array(se.se_coz(m3).veri["u"])
    assert np.allclose(u_yumusak, u_mafsal, rtol=1e-6, atol=1e-9)
    # elastik mesnet örneği: taban momenti dönme yayının kuvvetine eşittir (M = −kr·θ)
    v = coz("cerceve-elastik-mesnet").veri
    yay = {(y["dugum"], y["bilesen"]): y for y in v["yaylar"]}
    assert v["elemanlar"][0]["diyagram"]["M"][0] == pytest.approx(-yay[(1, "M")]["kuvvet"], rel=1e-9)
    assert v["tepkiler"] == []


def test_winkler_uzun_kiris_hetenyi():
    """Sonsuz uzun Winkler kirişinde tekil P: w_maks = Pβ/2k, M_maks = P/4β (β = (k/4EI)^¼)."""
    EI, k, P, L, ne = 4000.0, 1000.0, 10.0, 40.0, 80
    beta = (k / (4 * EI)) ** 0.25
    assert beta * L == pytest.approx(20.0)
    m = {"tip": "kiris", "dugumler": [{"no": i + 1, "x": L * i / ne} for i in range(ne + 1)],
         "elemanlar": [{"no": i + 1, "dugumler": [i + 1, i + 2], "E": "200e6", "I": "2e-5", "zemin": k} for i in range(ne)],
         "mesnetler": [], "yukler": [{"dugum": ne // 2 + 1, "Fy": -P}]}
    r = se.se_coz(m)
    v = r.veri
    assert v["mod"] == "sayisal" and v["tepkiler"] == []
    w = v["dugumler"][ne // 2]["u"][0]
    assert w == pytest.approx(-P * beta / (2 * k), rel=5e-3)
    Mmaks = max(abs(x) for e in v["elemanlar"] for x in e["diyagram"]["M"])
    assert Mmaks == pytest.approx(P / (4 * beta), rel=5e-3)
    # zemin kuvvetleri yükü taşır
    top = sum(x for e in v["elemanlar"] for x in (e["zemin_kuvvetleri"][0], e["zemin_kuvvetleri"][2]))
    assert top == pytest.approx(P, rel=1e-9)
    # uzaktaki çökme sönümlenir
    assert abs(v["dugumler"][0]["u"][0]) < 1e-3 * abs(w)


def test_winkler_kiris_kesit_diyagrami_tutarli():
    """Zeminli kirişte M(x) 5. dereceden polinom; uçlarda uç momentlerine ulaşır ve V'nin türevidir."""
    v = coz("kiris-elastik-zemin").veri
    e = v["elemanlar"][3]
    d = e["diyagram"]
    uc = e["uc_kuvvetleri"]
    assert d["M"][0] == pytest.approx(-uc[1], abs=1e-9) and d["M"][-1] == pytest.approx(uc[3], abs=1e-9)
    assert d["V"][0] == pytest.approx(uc[0], abs=1e-9) and d["V"][-1] == pytest.approx(-uc[2], abs=1e-9)
    # dM/dx ≈ V (merkezi fark)
    x, Mo, V = np.array(d["x"]), np.array(d["M"]), np.array(d["V"])
    turev = (Mo[2:] - Mo[:-2]) / (x[2:] - x[:-2])
    assert np.allclose(turev, V[1:-1], rtol=2e-2, atol=1e-6)
    # ortadaki çökme en büyük, kiriş simetrik
    dg = v["dugumler"]
    assert dg[4]["u"][0] < 0 and dg[0]["u"][0] == pytest.approx(dg[8]["u"][0])
    assert "Zemin tepkisi" in anlatim_metni(coz("kiris-elastik-zemin"))


def test_temel_kirisli_cerceve_zemin_dengesi():
    """Kolon–kiriş–temel sistemi: düşey yükü yalnız zemin taşır; yatay yükü düğüm 2'deki mesnet alır."""
    v = coz("cerceve-temel-kirisi").veri
    assert v["tepkiler"] == [{"dugum": 2, "Fx": pytest.approx(-15.0), "Fy": 0.0, "M": 0.0}]
    top = sum(x for e in v["elemanlar"] if e["zemin_kuvvetleri"] for x in (e["zemin_kuvvetleri"][1], e["zemin_kuvvetleri"][4]))
    assert top == pytest.approx(30.0 * 6.0, rel=1e-9)       # q·L = 180 kN
    # temel kirişi aşağı çöker, kolon altları en çok
    dg = {d["no"]: d for d in v["dugumler"]}
    assert dg[2]["u"][1] < 0 and dg[4]["u"][1] < 0
    assert all(e["zemin"] == 30000.0 for e in v["elemanlar"][:4]) and all(e["zemin"] is None for e in v["elemanlar"][4:])


def test_iki_katli_cerceve_denge():
    v = coz("cerceve-iki-katli").veri
    assert v["mod"] == "sayisal" and v["sd_sayisi"] == 18
    assert sum(t["Fx"] for t in v["tepkiler"]) == pytest.approx(-50.0)
    assert sum(t["Fy"] for t in v["tepkiler"]) == pytest.approx(200.0)        # 25·5 + 15·5
    dg = {d["no"]: d for d in v["dugumler"]}
    assert dg[3]["u"][0] > dg[2]["u"][0] > 0      # üst kat daha çok ötelenir


def test_tip_takma_adlari():
    m = se.ornek_model("kafes3b-tripod")
    for ad in ("KAFES-3B", "kafes_3b", "kafes3d", "Kafes3B"):
        m["tip"] = ad
        assert se.se_coz(m).veri["tip"] == "kafes3b"
    m = se.ornek_model("cerceve-portal")
    m["yukler"] = [{"dugum": 2, "Fx": 20, "Mz": 5}]       # düzlemde Mz, M ile aynı
    m["yayili"] = []
    assert se.se_coz(m).veri["F"][5] == 5.0


# ---------------------------------------------------------------------------
# Kapsam: qz, Mx/My, 3B yaylar ve çökmeler, ters yönlü elemanlar, eğik elemanda zemin
# ---------------------------------------------------------------------------
def _oz3b():
    return {"E": "200e6", "G": "80e6", "A": "0.01", "Iy": "1e-4", "Iz": "2e-4", "J": "3e-4"}


def _referansla_karsilastir(m, rtol=1e-8):
    """Motor çözümünü bağımsız referansla karşılaştırır: u, F, tepkiler, eleman uç kuvvetleri."""
    r = se.se_coz(m)
    v = r.veri
    u, Rt, uc, K, F = referans(m)
    assert yakin(v["u"], u, rtol=rtol, atol=1e-12)
    assert yakin(v["F"], F, rtol=1e-9, atol=1e-9)
    assert yakin(v["K"], K, rtol=1e-9, atol=1e-9)
    d = _D[m["tip"]]
    sira = {dg["no"]: i for i, dg in enumerate(m["dugumler"])}
    for t in v["tepkiler"]:
        i = sira[t["dugum"]]
        for ad, j in _YUK[m["tip"]].items():
            ms = next((x for x in m.get("mesnetler", []) if x["dugum"] == t["dugum"]), {})
            ck = next((x for x in m.get("cokmeler", []) if x["dugum"] == t["dugum"]), {})
            bayrak = _MESNET[m["tip"]][j]
            if ms.get(bayrak) or ck.get(bayrak) is not None:
                assert t[ad] == pytest.approx(Rt[d * i + j], rel=1e-7, abs=1e-7), (t["dugum"], ad)
    for e, (f, N) in zip(v["elemanlar"], uc):
        if m["tip"] in ("kiris", "cerceve", "cerceve3b"):
            assert yakin(e["uc_kuvvetleri"], f, rtol=1e-7, atol=1e-7), e["no"]
        if m["tip"] != "kiris":
            assert e["N"] == pytest.approx(N, rel=1e-7, abs=1e-8), e["no"]
    return r


def test_cerceve3b_qz_ve_Mx_My_referansla():
    """Yerel z′ yönünde yayılı yük (qz) ve Mx, My düğüm momentleri: motor ile bağımsız referans aynı sonucu verir."""
    m = {"tip": "cerceve3b", "dugumler": [{"no": 1, "x": 0, "y": 0, "z": 0}, {"no": 2, "x": 4, "y": 0, "z": 0},
                                          {"no": 3, "x": 4, "y": 0, "z": 3}],
         "elemanlar": [dict(no=1, dugumler=[1, 2], **_oz3b()), dict(no=2, dugumler=[2, 3], **_oz3b())],
         "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}],
         "yukler": [{"dugum": 3, "Fz": -5, "Mx": 2, "My": -3}],
         "yayili": [{"eleman": 1, "q": -4, "qz": 6}, {"eleman": 2, "qz": -2}]}
    r = _referansla_karsilastir(m)
    v = r.veri
    # qz'nin eşdeğer düğüm yükü: eleman 1 (x boyunca, z′ = Z): her uca qz·L/2 = 12 kN z yönünde;
    # eleman 2 (Z boyunca, y′ = Y, z′ = Z × Y = −X): qz = −2 → her uca 3 kN +x yönünde
    assert v["F"][2] == pytest.approx(12.0) and v["F"][8] == pytest.approx(12.0)
    assert v["F"][6] == pytest.approx(3.0) and v["F"][12] == pytest.approx(3.0)
    # düğüm momentleri F'de yerindedir; My'ye eleman 2'nin qz ankastrelik momenti de eklenir (qz·L²/12 = −1.5)
    assert v["F"][15] == pytest.approx(2.0) and v["F"][16] == pytest.approx(-3.0 - 1.5)
    # ankastre tepkisi dengeyi kapatır: ΣFz = 0, ΣFx = 0
    t = {x["dugum"]: x for x in v["tepkiler"]}
    assert t[1]["Fz"] == pytest.approx(-(-5 + 6 * 4)) and t[1]["Fx"] == pytest.approx(-6.0)
    assert "qz" in anlatim_metni(r) or "q_z" in anlatim_metni(r)


def test_cerceve3b_yaylar_ve_cokme_referansla():
    """Uzayda altı bileşenli yaylar ve uz / rx çökmesi: referansla aynı; yay kuvvetleri −k·u."""
    m = {"tip": "cerceve3b", "dugumler": [{"no": 1, "x": 0, "y": 0, "z": 0}, {"no": 2, "x": 0, "y": 3, "z": 0},
                                          {"no": 3, "x": 4, "y": 3, "z": 0}, {"no": 4, "x": 4, "y": 0, "z": 0}],
         "elemanlar": [dict(no=1, dugumler=[1, 2], **_oz3b()), dict(no=2, dugumler=[2, 3], **_oz3b()),
                       dict(no=3, dugumler=[3, 4], **_oz3b())],
         "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}],
         "yaylar": [{"dugum": 4, "kx": 5000, "ky": 8000, "kz": 3000, "krx": 400, "kry": 500, "krz": 600}],
         "cokmeler": [{"dugum": 4, "uz": "-0.02", "rx": "0.001"}],
         "yukler": [{"dugum": 3, "Fz": -10, "Fx": 4}]}
    r = _referansla_karsilastir(m)
    v = r.veri
    assert v["mod"] == "sayisal"
    assert {(c["dugum"], c["deger"]) for c in v["cokmeler"]} == {(4, -0.02), (4, 0.001)}
    assert v["u"][20] == pytest.approx(-0.02) and v["u"][21] == pytest.approx(0.001)
    yay = {(y["dugum"], y["bilesen"]): y for y in v["yaylar"]}
    assert set(yay) == {(4, "Fx"), (4, "Fy"), (4, "Fz"), (4, "Mx"), (4, "My"), (4, "Mz")}
    assert yay[(4, "Fx")]["kuvvet"] == pytest.approx(-5000 * v["u"][18])
    assert yay[(4, "Mz")]["kuvvet"] == pytest.approx(-600 * v["u"][23])
    # tutulan (çöken) bileşenlerde yay kuvveti çökme ile hesaplanır
    assert yay[(4, "Fz")]["kuvvet"] == pytest.approx(3000 * 0.02)


@pytest.mark.parametrize("ad", ["cerceve3b-konsol-L", "cerceve3b-izgara", "kafes3b-kule", "cerceve-iki-katli"])
def test_ters_yonlu_elemanlar_sonucu_degistirmez(ad):
    """Elemanların i–j sırası tersine çevrilince (−x, −y, −z yönünde elemanlar) u ve tepkiler değişmez;
    N aynı kalır; kiriş/çerçevede uç kuvvetleri yer değiştirir."""
    r0 = coz(ad)
    m = se.ornek_model(ad)
    xyz = {dg["no"]: (float(dg.get("x", 0)), float(dg.get("y", 0)), float(dg.get("z", 0))) for dg in m["dugumler"]}
    dusey = {}
    for e in m["elemanlar"]:
        a, b = xyz[e["dugumler"][0]], xyz[e["dugumler"][1]]
        dusey[e["no"]] = abs(a[0] - b[0]) < 1e-12 and abs(a[2] - b[2]) < 1e-12
        e["dugumler"] = list(reversed(e["dugumler"]))
    # yayılı yük yerel eksende verilir: eleman tersinince düzlemde y′ ters döner (q işaret değiştirir);
    # uzayda y′ düşey düzlemde yukarı kalır, z′ ters döner (qz işaret değiştirir); düşey uzay elemanında tersi
    for y in m.get("yayili", []):
        if m["tip"] == "cerceve3b":
            if dusey[y["eleman"]]:
                y["q"] = -float(y.get("q", 0) or 0)
            else:
                y["qz"] = -float(y.get("qz", 0) or 0)
        else:
            y["q"] = -float(y.get("q", 0) or 0)
    r1 = se.se_coz(m)
    assert yakin(r1.veri["u"], r0.veri["u"], rtol=1e-8, atol=1e-13)
    t0 = {x["dugum"]: x for x in r0.veri["tepkiler"]}
    for t in r1.veri["tepkiler"]:
        for k, val in t.items():
            if k != "dugum":
                assert val == pytest.approx(t0[t["dugum"]][k], rel=1e-7, abs=1e-7), (t["dugum"], k)
    d = _D[m["tip"]]
    for e0, e1 in zip(r0.veri["elemanlar"], r1.veri["elemanlar"]):
        assert e1["N"] == pytest.approx(e0["N"], rel=1e-7, abs=1e-7)
        if m["tip"] in ("cerceve", "cerceve3b"):
            f0, f1 = np.array(e0["uc_kuvvetleri"]), np.array(e1["uc_kuvvetleri"])
            if m["tip"] == "cerceve3b":
                # ters eleman: x′ ve z′ işaret değiştirir, y′ aynı (düşey düzlemde yukarı) -> yerel bileşenler
                # (fx, fy, fz, mx, my, mz)_j' = (−fx, fy, −fz, −mx, my, −mz)_i ve tersi; düşey elemanda z′ = Z
                # sabit kalır, y′ ters döner
                isaret = np.array(([-1, -1, 1, -1, -1, 1] if dusey[e0["no"]] else [-1, 1, -1, -1, 1, -1]) * 2)
                assert yakin(f1, isaret * np.concatenate([f0[d:], f0[:d]]), rtol=1e-7, atol=1e-7), e0["no"]
            else:
                # düzlemde: x′ ters, y′ ters, z′ (dönme) aynı
                isaret = np.array([-1, -1, 1] * 2)
                assert yakin(f1, isaret * np.concatenate([f0[d:], f0[:d]]), rtol=1e-7, atol=1e-7), e0["no"]


def test_egik_cerceve_elemaninda_zemin_referansla():
    """Eğik bir çerçeve elemanına Winkler zemini: yatak matrisi yerel y′ bileşenlerine eklenir (referansla aynı)."""
    m = {"tip": "cerceve", "dugumler": [{"no": 1, "x": 0, "y": 0}, {"no": 2, "x": 4, "y": 3}, {"no": 3, "x": 8, "y": 3}],
         "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "3e7", "A": "0.2", "I": "6e-3", "zemin": "20000"},
                       {"no": 2, "dugumler": [2, 3], "E": "3e7", "A": "0.2", "I": "6e-3", "zemin": "20000"}],
         "mesnetler": [{"dugum": 1, "ux": True, "uy": True}],
         "yukler": [{"dugum": 3, "Fy": -50}], "yayili": [{"eleman": 1, "q": -10}]}
    r = _referansla_karsilastir(m)
    v = r.veri
    u = np.array(v["u"])
    # zemin uç kuvvetleri (yerelde −K_w·d_y′, globale çevrilmiş) referansla aynı; toplamı + mesnet tepkisi = dış yük
    toplam = np.zeros(3)
    for e in v["elemanlar"]:
        me = next(x for x in m["elemanlar"] if x["no"] == e["no"])
        a, b = (next(i for i, dg in enumerate(m["dugumler"]) if dg["no"] == n) for n in me["dugumler"])
        dx, dy = (m["dugumler"][b][k] - m["dugumler"][a][k] for k in ("x", "y"))
        L = np.hypot(dx, dy); c, s_ = dx / L, dy / L
        t3 = np.array([[c, s_, 0.0], [-s_, c, 0.0], [0.0, 0.0, 1.0]])
        T = np.block([[t3, np.zeros((3, 3))], [np.zeros((3, 3)), t3]])
        dofs = [3 * a, 3 * a + 1, 3 * a + 2, 3 * b, 3 * b + 1, 3 * b + 2]
        dy_ = T @ u[dofs]
        fz = np.zeros(6)
        fz[[1, 2, 4, 5]] = -_winkler_k(float(me["zemin"]), L) @ dy_[[1, 2, 4, 5]]
        fg = T.T @ fz                                   # dışa verilen zemin kuvvetleri global eksendedir
        assert yakin(e["zemin_kuvvetleri"], fg, rtol=1e-7, atol=1e-7), e["no"]
        toplam += fg[:3] + fg[3:]
    # q eleman eksenine diktir (y′ = (−0.6, 0.8)); q = −10 üzerinden toplam 50 kN: (+30, −40) global bileşen
    t = v["tepkiler"][0]
    assert t["Fy"] + toplam[1] == pytest.approx(50 + 40, rel=1e-7)
    assert t["Fx"] + toplam[0] == pytest.approx(-30, rel=1e-7)
    assert abs(v["denge"]["Fy"]) < 1e-6 and abs(v["denge"]["M"]) < 1e-6


def test_ayni_elemana_iki_yayili_yuk_toplanir():
    m = se.ornek_model("kiris-basit-yayili")
    q = m["yayili"][0]["q"]
    m["yayili"] = [{"eleman": 1, "q": q}, {"eleman": 1, "q": "-5"}]
    r = se.se_coz(m)
    m2 = se.ornek_model("kiris-basit-yayili")
    m2["yayili"] = [{"eleman": 1, "q": str(float(q) - 5)}]
    assert yakin(r.veri["F"], se.se_coz(m2).veri["F"], rtol=1e-12, atol=1e-12)
    u, Rt, uc, K, F = referans(m)
    assert yakin(r.veri["u"], u, rtol=1e-9, atol=1e-14)


# ---------------------------------------------------------------------------
# Düzeltilen hataların gerileme (regresyon) testleri
# ---------------------------------------------------------------------------
def test_cokme_tum_serbestlikler_tutulu():
    """Her iki ucu ankastre kiriş, bir uç Δ çöker: serbest SD yok; V = 12EIΔ/L³, M = 6EIΔ/L²."""
    m = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 4}],
         "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"}],      # EI = 4000
         "mesnetler": [{"dugum": 1, "uy": True, "rz": True}, {"dugum": 2, "uy": True, "rz": True}],
         "cokmeler": [{"dugum": 2, "uy": "-0.01"}], "yukler": []}
    r = se.se_coz(m)
    v = r.veri
    assert list(r.deger) == [0, 0, R(-1, 100), 0] and v["sd_sayisi"] == 4
    t = {x["dugum"]: x for x in v["tepkiler"]}
    assert t[1]["Fy"] == pytest.approx(12 * 4000 * 0.01 / 64) and t[2]["Fy"] == pytest.approx(-7.5)
    assert t[1]["M"] == pytest.approx(6 * 4000 * 0.01 / 16) and t[2]["M"] == pytest.approx(15.0)
    assert r.python_kodu.strip() and "Traceback" not in r.python_ciktisi
    assert "Mesnet çökmesi" in anlatim_metni(r)


def test_sayisal_modda_cokme_kalinti_denetimi_gecer():
    """SD > eşik (sayısal mod) ve mesnet çökmesi: K_fs·u_s terimi kalıntı denetiminde hesaba katılır."""
    m = se.ornek_model("cerceve-iki-katli")
    m["cokmeler"] = [{"dugum": 4, "uy": "-0.02", "rz": "0.002"}]
    r = _referansla_karsilastir(m)
    assert r.veri["mod"] == "sayisal" and r.veri["sd_sayisi"] > se.SD_ESIK
    assert r.veri["u"][10] == pytest.approx(-0.02) and r.veri["u"][11] == pytest.approx(0.002)


def test_cok_rijit_yay_mekanizma_sayilmaz():
    """Çok rijit yaylar (k ≫ EA/L) K'nın ölçeğini şişirir; gerçek modlar sıfır sanılmamalı."""
    m = se.ornek_model("kafes-iki-cubuk")
    m["mesnetler"] = []
    m["yaylar"] = [{"dugum": d, "kx": "1e13", "ky": "1e13"} for d in (1, 2)]
    r = se.se_coz(m)
    assert r.veri["tepkiler"] == [] and len(r.veri["yaylar"]) == 4
    # yaylar çok rijit: sonuç ankastre (mesnetli) çözüme yaklaşır
    r0 = coz("kafes-iki-cubuk")
    assert yakin(r.veri["u"], r0.veri["u"], rtol=1e-5, atol=1e-9)
    # gerçek bir mekanizma rijit yaylara rağmen yakalanır: yalnız bir düğüm tutulu
    m["yaylar"] = [{"dugum": 1, "kx": "1e13", "ky": "1e13"}]
    with pytest.raises(mo.MatrisHatasi, match="mekanizma"):
        se.se_coz(m)


def test_betikte_d_sembolu_catismaz():
    """Kullanıcı 'd' adlı bir sembol kullanırsa üretilen betikteki SD değişkeniyle çakışmamalı."""
    m = se.ornek_model("kafes-iki-cubuk")
    m["elemanlar"][0]["A"] = "d"
    m["yukler"] = [{"dugum": 2, "Fy": "-P"}]
    r = se.se_coz(m)
    assert r.veri["mod"] == "kesin"
    ns: dict = {"__name__": "betik"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(r.python_kodu, "<betik>", "exec"), ns)
    assert len(ns["u"]) == r.veri["sd_sayisi"]
    for x, y in zip(ns["u"], r.deger):
        assert sp.simplify(sp.sympify(x) - y) == 0


@pytest.mark.parametrize("ad,degistir", [
    ("cerceve3b-egik-sembolik", lambda m: m["elemanlar"][0].update(E="E", G="G")),
    ("kiris-zemin-sembolik", None),
    ("kafes-yay-sembolik", None),
])
def test_sembolik_zor_modeller_hizli(ad, degistir):
    """Köklü/sembolik ifadeler LUsolve+simplify ile takılırdı; linsolve+cancel ile saniyeler içinde biter."""
    if ad == "cerceve3b-egik-sembolik":
        m = {"tip": "cerceve3b", "dugumler": [{"no": 1, "x": 0, "y": 0, "z": 0}, {"no": 2, "x": 3, "y": 2, "z": 1}],
             "elemanlar": [dict(no=1, dugumler=[1, 2], **_oz3b())],
             "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}],
             "yukler": [{"dugum": 2, "Fy": "-P", "Mx": "M0"}]}
        degistir(m)
    elif ad == "kiris-zemin-sembolik":
        m = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 2}, {"no": 3, "x": 4}],
             "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "E", "I": "I", "zemin": "k"},
                           {"no": 2, "dugumler": [2, 3], "E": "E", "I": "I", "zemin": "k"}],
             "mesnetler": [], "yukler": [{"dugum": 2, "Fy": "-P"}]}
    else:
        m = se.ornek_model("kafes-uc-cubuk")
        for e in m["elemanlar"]:
            e.update(E="E", A="A")
        m["mesnetler"] = m["mesnetler"][:2]      # düğüm 3'ün mesnedi yerine yaylar
        m["yaylar"] = [{"dugum": 3, "kx": "k", "ky": "k"}]
    t0 = time.perf_counter()
    r = se.se_coz(m)
    assert time.perf_counter() - t0 < 8.0, ad
    assert r.veri["mod"] == "kesin" and r.python_ciktisi and "Traceback" not in r.python_ciktisi
    # sembolik çözüm sayısal değerle tutarlı: sembolleri sayıya koyup referansla karşılaştır
    degerler = {"E": 2e8, "G": 8e7, "I": 1e-4, "L": 2.0, "k": 5000.0, "P": 10.0, "M0": 3.0, "A": 0.01}
    semboller = {a: sp.Symbol(a) for a in degerler}        # "E" ve "I" sympy sabitleri (e, i) değil, harf olmalı
    say = lambda s: sp.sympify(str(s), locals=semboller).subs({semboller[a]: b for a, b in degerler.items()})
    m_say = copy.deepcopy(m)
    for dg in m_say["dugumler"]:
        for k in ("x", "y", "z"):
            if k in dg:
                dg[k] = float(say(dg[k]))
    for e in m_say["elemanlar"]:
        for k in ("E", "G", "A", "I", "Iy", "Iz", "J", "zemin"):
            if k in e:
                e[k] = float(say(e[k]))
    for y in m_say["yukler"]:
        for k, v in list(y.items()):
            if k != "dugum":
                y[k] = float(say(v))
    for y in m_say.get("yaylar", []):
        for k, v in list(y.items()):
            if k != "dugum":
                y[k] = float(say(v))
    u_ref = referans(m_say)[0]
    u_semb = [float(sp.N(say(x), 30)) for x in r.deger]
    assert yakin(u_semb, u_ref, rtol=1e-7, atol=1e-12), ad


def test_z_uyarisi_duzlem_modelde():
    m = se.ornek_model("kafes-iki-cubuk")
    m["dugumler"][1]["z"] = 2
    r = se.se_coz(m)
    metin = anlatim_metni(r)
    assert "z yoksayıldı" in metin and "kafes3b" in metin
    assert yakin(r.veri["u"], coz("kafes-iki-cubuk").veri["u"], rtol=1e-12, atol=1e-15)


def test_cokme_u_takma_adi_cubukta():
    m = se.ornek_model("cubuk-kademeli")
    m["cokmeler"] = [{"dugum": m["dugumler"][0]["no"], "u": "0.001"}]
    r = se.se_coz(m)
    assert r.veri["cokmeler"][0]["deger"] == 0.001
    m["cokmeler"] = [{"dugum": m["dugumler"][0]["no"], "ux": "0.001"}]
    assert yakin(se.se_coz(m).veri["u"], r.veri["u"], rtol=1e-12, atol=1e-15)


def test_kr_krz_takma_adlari():
    """Düzlemde 'krz', uzayda 'kr' da kabul edilir (M/Mz gibi)."""
    m = se.ornek_model("cerceve-elastik-mesnet")
    for y in m["yaylar"]:
        if "kr" in y:
            y["krz"] = y.pop("kr")
    assert yakin(se.se_coz(m).veri["u"], coz("cerceve-elastik-mesnet").veri["u"], rtol=1e-12, atol=1e-15)
    m3 = se.ornek_model("cerceve3b-konsol-L")
    m3["mesnetler"][0]["rz"] = False
    m3["yaylar"] = [{"dugum": 1, "kr": 5000}]
    r3 = se.se_coz(m3)
    assert r3.veri["yaylar"][0]["bilesen"] == "Mz" and r3.veri["yaylar"][0]["k"] == 5000
    m3["yaylar"] = [{"dugum": 1, "krz": 5000}]
    assert yakin(se.se_coz(m3).veri["u"], r3.veri["u"], rtol=1e-12, atol=1e-15)
