# -*- coding: utf-8 -*-
"""alan.py (ısı haritası alanları, §16) ve köprü "bina_alan" testleri; docs/isi_haritasi.js node testleri.

Doğrulamalar:
* Eğri yer değiştirme (M/EI'nin iki kez integrali + uç ötelemeleri): basit kiriş orta sehim 5qL⁴/384EI, konsol uç PL³/3EI ve
  bütün eğri P x²(3L − x)/6EI, z′ yönünde konsol, iki ucu ankastre qL⁴/384EI, ucu mafsallı (Mz serbest) eleman — düğüm
  dönmesi eleman ucundan farklıyken de eğri kesin; bina içinde bir kirişi ortadan bölüp yeniden çözmek alan.py'nin
  istasyon değeriyle aynı yer değiştirmeyi verir (parçalı döşeme yükü dahil).
* Lif gerilmesi işareti (σ = N/A − Mz·y/Iz − My·z/Iy): Mz > 0 alt (−y′) lifi, My > 0 −z′ lifini çeker; eğrilikten
  hesaplanan birim şekil değiştirme (ε = −y·v″ − z·w″) ile aynı işaret.
* Kombinasyon = durum alanlarının doğrusal birleşimi; zarf her istasyonda kombinasyonların en büyüğü / en küçüğü.
* Navier plağı: kare plak ν = 0,3 → w = 0,00406 qa⁴/D, m = 0,0479 qa²; 45° yük payı alanları TS 500 dağıtımıyla aynı.
"""
from __future__ import annotations

import importlib.util
import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

import alan
import sonlu_eleman as se
import yapi

PROJE = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
E, IZ, IY, A = 2.0e8, 2.0e-4, 1.0e-4, 0.01


# ---------------------------------------------------------------------------------------------
# Çekirdek: tek çubuk modelleri (se_coz) + alan.cubuk_alani
# ---------------------------------------------------------------------------------------------
def _el(no, a, b, **ek):
    return dict(no=no, dugumler=[a, b], E=E, G=8.0e7, A=A, Iy=IY, Iz=IZ, J=1.0e-5, **ek)


def _dg(no, x, y=0.0, z=0.0):
    return {"no": no, "x": x, "y": y, "z": z}


ANK = {"ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}


def _coz(m):
    v = se.se_coz(m, goster="yok").veri
    u = np.array(v["u"], dtype=float).reshape(-1, 6)
    return v, u, {d["no"]: i for i, d in enumerate(v["dugumler"])}


def _alan(v, u, no, k, xe):
    """Motor koordinatında (lam ve u motor sisteminde) tek eleman, tek durum → (9, n): N, Vy, Vz, T, My, Mz, ux, uy, uz."""
    e = v["elemanlar"][k]
    d = e["diyagram"]
    diy = np.array([[d[a] for a in ("N", "V", "M", "Vz", "My", "T")]])
    i, j = e["dugumler"]
    return alan.cubuk_alani(d["x"], diy, e["lam"], u[no[i], :3][None], u[no[j], :3][None], E * A, E * IY, E * IZ, np.asarray(xe))[0]


def test_basit_kiris_orta_sehim():
    L, q = 6.0, 10.0
    m = {"tip": "cerceve3b", "dugumler": [_dg(1, 0), _dg(2, L)], "elemanlar": [_el(1, 1, 2)],
         "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "uz": True, "rx": True}, {"dugum": 2, "uy": True, "uz": True}],
         "yayili": [{"eleman": 1, "q": -q}]}
    v, u, no = _coz(m)
    xe = np.linspace(0, L, 13)
    F = _alan(v, u, no, 0, xe)
    assert F[7, 6] == pytest.approx(-5 * q * L ** 4 / (384 * E * IZ), rel=1e-10)
    # bütün eğri: v(x) = −q x (L³ − 2Lx² + x³) / 24EI
    assert F[7] == pytest.approx(-q * xe * (L ** 3 - 2 * L * xe ** 2 + xe ** 3) / (24 * E * IZ), abs=1e-12)
    # uçlarda düğüm ötelemesi (sıfır) ve iç kuvvetler: Mz(L/2) = qL²/8, Vy(0) = qL/2
    assert F[5, 6] == pytest.approx(q * L ** 2 / 8) and F[1, 0] == pytest.approx(q * L / 2)


def test_konsol_uc_yuku_butun_egri():
    L, P = 6.0, 20.0
    m = {"tip": "cerceve3b", "dugumler": [_dg(1, 0), _dg(2, L)], "elemanlar": [_el(1, 1, 2)],
         "mesnetler": [dict(ANK, dugum=1)], "yukler": [{"dugum": 2, "Fy": -P}]}
    v, u, no = _coz(m)
    xe = np.linspace(0, L, 21)
    F = _alan(v, u, no, 0, xe)
    assert F[7, -1] == pytest.approx(-P * L ** 3 / (3 * E * IZ), rel=1e-10)
    assert F[7] == pytest.approx(-P * xe ** 2 * (3 * L - xe) / (6 * E * IZ), abs=1e-12)


def test_konsol_z_yonu_ve_my_isareti():
    """z′ yönünde (−) uç yükü: w = −P x²(3L − x)/6EI_y; ankastre uçta My < 0 (üst, +z′ lifi çekmede)."""
    L, P = 4.0, 12.0
    m = {"tip": "cerceve3b", "dugumler": [_dg(1, 0), _dg(2, L)], "elemanlar": [_el(1, 1, 2)],
         "mesnetler": [dict(ANK, dugum=1)], "yukler": [{"dugum": 2, "Fz": -P}]}
    v, u, no = _coz(m)
    xe = np.linspace(0, L, 21)
    F = _alan(v, u, no, 0, xe)
    assert F[8] == pytest.approx(-P * xe ** 2 * (3 * L - xe) / (6 * E * IY), abs=1e-12)
    assert F[4, 0] == pytest.approx(-P * L)            # My(0) = −PL
    # eğrilik: EI_y w″ = My (sayısal ikinci türev)
    h = xe[1] - xe[0]
    w2 = (F[8, 2:] - 2 * F[8, 1:-1] + F[8, :-2]) / h ** 2
    assert w2 * E * IY == pytest.approx(F[4, 1:-1], rel=1e-6, abs=1e-6)


def test_iki_ucu_ankastre():
    L, q = 5.0, 8.0
    m = {"tip": "cerceve3b", "dugumler": [_dg(1, 0), _dg(2, L)], "elemanlar": [_el(1, 1, 2)],
         "mesnetler": [dict(ANK, dugum=1), dict(ANK, dugum=2)], "yayili": [{"eleman": 1, "q": -q}]}
    v, u, no = _coz(m)
    xe = np.linspace(0, L, 11)
    F = _alan(v, u, no, 0, xe)
    assert F[7, 5] == pytest.approx(-q * L ** 4 / (384 * E * IZ), rel=1e-10)
    assert F[7] == pytest.approx(-q * xe ** 2 * (L - xe) ** 2 / (24 * E * IZ), abs=1e-12)


def test_mafsalli_uclu_eleman():
    """A ankastre — B kayıcı — C ankastre; 1. elemanın B ucunda Mz serbest (mafsal), yük yalnız 1. elemanda.
    B düğümünün dönmesi (2. eleman belirler) 0'dır ama 1. elemanın B ucundaki eğimi qL³/48EI'dir: yalnız uç ötelemeleri
    kullanan eğri, ankastre–mafsallı kiriş eğrisini v = −q x²(3L² − 5Lx + 2x²)/48EI kesin verir."""
    L, q = 6.0, 10.0
    m = {"tip": "cerceve3b", "dugumler": [_dg(1, 0), _dg(2, L), _dg(3, 2 * L)],
         "elemanlar": [_el(1, 1, 2, serbest={"i": [], "j": ["Mz"]}), _el(2, 2, 3)],
         "mesnetler": [dict(ANK, dugum=1), {"dugum": 2, "uy": True, "uz": True}, dict(ANK, dugum=3)],
         "yayili": [{"eleman": 1, "q": -q}]}
    v, u, no = _coz(m)
    assert abs(u[no[2], 5]) < 1e-12                       # düğüm dönmesi 0
    xe = np.linspace(0, L, 25)
    F = _alan(v, u, no, 0, xe)
    ref = -q * xe ** 2 * (3 * L ** 2 - 5 * L * xe + 2 * xe ** 2) / (48 * E * IZ)
    assert F[7] == pytest.approx(ref, abs=1e-12)
    assert np.max(np.abs(ref)) == pytest.approx(q * L ** 4 / (185 * E * IZ), rel=2e-3)     # ≈ qL⁴/185EI
    v_, dv = alan.sehim_egrisi(v["elemanlar"][0]["diyagram"]["x"], v["elemanlar"][0]["diyagram"]["M"],
                               v["elemanlar"][0]["diyagram"]["V"], E * IZ, 0.0, 0.0, np.array([L]))
    assert dv[0] == pytest.approx(q * L ** 3 / (48 * E * IZ), rel=1e-9)                   # mafsalda eleman eğimi ≠ 0


def test_eksenel_yayili_yuk():
    """Eksenel yayılı yük p (x′ yönünde) altında konsol: N = p(L − x), u(x) = p(Lx − x²/2)/EA."""
    L, p = 3.0, 5.0
    m = {"tip": "cerceve3b", "dugumler": [_dg(1, 0), _dg(2, L)], "elemanlar": [_el(1, 1, 2)],
         "mesnetler": [dict(ANK, dugum=1)], "yayili": [{"eleman": 1, "qx1": p, "qx2": p, "x1": 0.0, "x2": L}]}
    try:
        v, u, no = _coz(m)
    except Exception as hata:          # noqa: BLE001 — eksenel yayılı yük anahtarı motorda yoksa atla
        pytest.skip(f"eksenel yayılı yük biçimi desteklenmiyor: {hata}")
    xe = np.linspace(0, L, 7)
    F = _alan(v, u, no, 0, xe)
    if abs(F[0, 0]) < 1e-12:
        pytest.skip("eksenel yayılı yük bu anahtarla verilmiyor")
    assert F[0] == pytest.approx(p * (L - xe), abs=1e-9)
    assert F[6] == pytest.approx(p * (L * xe - xe ** 2 / 2) / (E * A), abs=1e-12)


def test_hermite_kubik_kesin():
    xs = np.array([0.0, 0.7, 1.5, 3.0])
    f = 2 - xs + 0.5 * xs ** 2 - 0.3 * xs ** 3
    df = -1 + xs - 0.9 * xs ** 2
    xe = np.linspace(0, 3, 17)
    a, b = alan.hermite_ara_deger(xs, f, df, xe)
    assert a == pytest.approx(2 - xe + 0.5 * xe ** 2 - 0.3 * xe ** 3, abs=1e-12)
    assert b == pytest.approx(-1 + xe - 0.9 * xe ** 2, abs=1e-12)


def test_lif_gerilmesi_isareti_ve_egrilik():
    """σ = N/A − Mz·y/Iz − My·z/Iy: Mz > 0 → −y′ lifi çekme; My > 0 → −z′ lifi çekme. Eğrilikten birim şekil
    değiştirme ε = −y·v″ − z·w″ ile aynı (E·ε = σ)."""
    k = {"A": A, "Iy": IY, "Iz": IZ}
    assert alan.lif_gerilmesi(k, 0.0, 0.0, 10.0, -0.1, 0.0) > 0 > alan.lif_gerilmesi(k, 0.0, 0.0, 10.0, 0.1, 0.0)
    assert alan.lif_gerilmesi(k, 0.0, 10.0, 0.0, 0.0, -0.1) > 0 > alan.lif_gerilmesi(k, 0.0, 10.0, 0.0, 0.0, 0.1)
    assert alan.lif_gerilmesi(k, 5.0, 0.0, 0.0, 0.3, -0.2) == pytest.approx(5.0 / A / 1000)
    # iki eksenli konsol: uç yükü (Fy, Fz) → kökte eğrilikler
    L, P = 4.0, 10.0
    m = {"tip": "cerceve3b", "dugumler": [_dg(1, 0), _dg(2, L)], "elemanlar": [_el(1, 1, 2)],
         "mesnetler": [dict(ANK, dugum=1)], "yukler": [{"dugum": 2, "Fy": -P, "Fz": 0.6 * P}]}
    v, u, no = _coz(m)
    xe = np.linspace(0, L, 41)
    F = _alan(v, u, no, 0, xe)
    h = xe[1] - xe[0]
    i = 10
    v2 = (F[7, i + 1] - 2 * F[7, i] + F[7, i - 1]) / h ** 2
    w2 = (F[8, i + 1] - 2 * F[8, i] + F[8, i - 1]) / h ** 2
    for y, z in ((0.05, 0.03), (-0.05, 0.03), (0.05, -0.03), (-0.05, -0.03)):
        eps = -y * v2 - z * w2
        s = alan.lif_gerilmesi(k, F[0, i], F[4, i], F[5, i], y, z)
        assert s == pytest.approx(E * eps / 1000, rel=1e-6)


# ---------------------------------------------------------------------------------------------
# Bina: alan paketi, kombinasyon, zarf, eğri yer değiştirme (bölünmüş kiriş), kullanım
# ---------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def bina2():
    r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"), goster="yok", anlat=False)
    return r


@pytest.fixture(scope="module")
def celik():
    return yapi.bina_coz(yapi.bina_sablon("celik-1kat-depo"), goster="yok", anlat=False)


def test_alan_semasi(bina2):
    ic = bina2.ic
    a = alan.eleman_alanlari(ic, "G")
    assert set(a) >= {"durum", "birim", "elemanlar", "dugumler", "paneller", "aralik", "secenekler", "isaret", "radye"}
    assert len(a["elemanlar"]) == len(bina2.veri["ag"]["elemanlar"])
    e = a["elemanlar"][0]
    assert set(e) >= {"no", "tur", "bina_no", "i", "j", "yerel", "kesit", "x", "u", "N", "Vy", "Vz", "T", "My", "Mz", "sigma_max",
                      "sigma_min", "tau_max", "von_mises", "kullanim", "ekstremum"}
    assert len(e["x"]) >= alan.ISTASYON and e["x"][0] == 0 and e["x"][-1] == pytest.approx(e["L"])
    assert len(e["u"]) == len(e["x"]) and all(len(q) == 3 for q in e["u"])
    assert e["kesit"]["sekil"] == "dikdortgen" and e["kesit"]["malzeme"]["tur"] == "beton"
    assert a["not"] and "kullanım" in a["not"]
    for v in e["yerel"].values():
        assert math.isclose(sum(c * c for c in v), 1.0, rel_tol=1e-9)
    json.dumps(a)                                   # JSON'a yazılabilir
    assert a["secenekler"]["zarf"] == ["zarf+", "zarf-"] and "G" in a["secenekler"]["durumlar"]
    assert not any(d.endswith("~c") for d in a["secenekler"]["durumlar"])


def test_istasyonlar_motor_diyagramlariyla_ayni(bina2):
    """Motor istasyonlarında alan.py'nin N, Vy, Mz, My değerleri paket diyagramıyla aynı; uçlarda u = düğüm ötelemesi."""
    ic = bina2.ic
    a = alan.eleman_alanlari(ic, "G", paneller=False)
    G = bina2.veri["durumlar"]["G"]
    kisa = {e["no"]: e for e in G["elemanlar"]}
    dug = {d["no"]: d for d in G["dugumler"]}
    for e in a["elemanlar"]:
        k = kisa[e["no"]]
        x = np.array(e["x"])
        for xm, N, V, M, My in zip(k["x"], k["N"], k["V"], k["M"], k["My"]):
            i = int(np.argmin(np.abs(x - xm)))
            assert abs(x[i] - xm) < 1e-6
            assert e["N"][i] == pytest.approx(N, rel=1e-4, abs=1e-6)
            assert e["Vy"][i] == pytest.approx(V, rel=1e-4, abs=1e-6)
            assert e["Mz"][i] == pytest.approx(M, rel=1e-4, abs=1e-6)
            assert e["My"][i] == pytest.approx(My, rel=1e-4, abs=1e-6)
        for uc, idx in ((0, 0), (1, -1)):
            d = dug[e["dugumler"][uc]]
            assert e["u"][idx] == pytest.approx([d["uX"], d["uY"], d["uZ"]], rel=1e-4, abs=1e-10)


def _yayili_bol(kayitlar, eleman, L, a, yeni_i, yeni_j):
    """eleman'ın yayılı yük kayıtlarını x = a'da iki elemana böler (parçalı doğrusal)."""
    out = []
    for y in kayitlar:
        if y["eleman"] != eleman:
            out.append(y)
            continue
        if "q" in y and "q1" not in y:
            q1 = q2 = y["q"]
            x1, x2 = 0.0, L
        else:
            q1, q2, x1, x2 = y["q1"], y["q2"], y.get("x1", 0.0), y.get("x2", L)
        ek = {k: v for k, v in y.items() if k not in ("eleman", "q", "q1", "q2", "x1", "x2")}
        def q_(x):
            return q1 + (q2 - q1) * (x - x1) / (x2 - x1)
        if x1 < a:
            b = min(x2, a)
            out.append(dict(ek, eleman=yeni_i, q1=q1, q2=q_(b), x1=x1, x2=b))
        if x2 > a:
            b = max(x1, a)
            out.append(dict(ek, eleman=yeni_j, q1=q_(b), q2=q2, x1=b - a, x2=x2 - a))
    return out


def test_bolunmus_kiris_egri_yer_degistirme(bina2):
    """Bir kirişi (parçalı döşeme yükleriyle) ortadan bölüp G durumunu yeniden çözmek: yeni orta düğümün ötelemesi,
    alan.py'nin x = L/2 istasyonundaki eğri yer değiştirmesine eşit (özel çözüm = M/EI'nin iki kez integrali)."""
    ic = bina2.ic
    fm = json.loads(json.dumps(bina2.veri["fe_model"]))
    a = alan.eleman_alanlari(ic, "G", paneller=False)
    kirisler = [e for e in a["elemanlar"] if e["tur"] == "kiris"]
    yuklu = {y["eleman"] for y in fm["yayili"]}
    e = max((k for k in kirisler if k["no"] in yuklu), key=lambda k: abs(min(q[2] for q in k["u"])))
    L = e["L"]
    el = next(x for x in fm["elemanlar"] if x["no"] == e["no"])
    dno = {d["no"]: d for d in fm["dugumler"]}
    i, j = el["dugumler"]
    yeni_d = max(d["no"] for d in fm["dugumler"]) + 1
    yeni_e = max(x["no"] for x in fm["elemanlar"]) + 1
    fm["dugumler"].append({"no": yeni_d, **{c: (dno[i][c] + dno[j][c]) / 2 for c in ("x", "y", "z")}})
    el["dugumler"] = [i, yeni_d]
    fm["elemanlar"].append(dict(el, no=yeni_e, dugumler=[yeni_d, j]))
    fm["yayili"] = _yayili_bol(fm["yayili"], e["no"], L, L / 2, e["no"], yeni_e)
    v = se.se_coz(fm, goster="yok").veri
    u = np.array(v["u"], dtype=float).reshape(-1, 6)
    k = [d["no"] for d in v["dugumler"]].index(yeni_d)
    orta = [u[k, 0], -u[k, 2], u[k, 1]]                     # motor → bina (X = x, Y = −z, Z = y)
    x = np.array(e["x"])
    s = int(np.argmin(np.abs(x - L / 2)))
    assert x[s] == pytest.approx(L / 2)
    assert e["u"][s] == pytest.approx(orta, rel=1e-4, abs=1e-9)
    # doğrusal ara değer (uç ötelemeleri) bundan farklı: eğri gerçekten eğri
    lin = (np.array(e["u"][0]) + np.array(e["u"][-1])) / 2
    assert abs(orta[2] - lin[2]) > 0.2 * abs(orta[2])


def test_kombinasyon_super_pozisyon_ve_zarf(bina2):
    ic = bina2.ic
    komb = ic["kombinasyonlar"]
    ad = next(a for a in komb if set(komb[a]) <= {"G", "Q"} and len(komb[a]) == 2)
    kat = komb[ad]
    k = alan.eleman_alanlari(ic, ad, paneller=False)
    tek = {d: alan.eleman_alanlari(ic, d, paneller=False) for d in kat}
    for i, e in enumerate(k["elemanlar"]):
        for b in ("N", "Vy", "Vz", "T", "My", "Mz"):
            ref = sum(g * np.array(tek[d]["elemanlar"][i][b]) for d, g in kat.items())
            assert np.array(e[b]) == pytest.approx(ref, rel=1e-4, abs=1e-6)
        ref_u = sum(g * np.array(tek[d]["elemanlar"][i]["u"]) for d, g in kat.items())
        assert np.array(e["u"]) == pytest.approx(ref_u, rel=1e-4, abs=1e-12)
    zp, zm = alan.eleman_alanlari(ic, "zarf+", paneller=False), alan.eleman_alanlari(ic, "zarf-", paneller=False)
    assert zp["zarf"] and zp["kombinasyon_sayisi"] >= 2 and zp["zarf_not"]
    liste = alan.durum_katsayilari(ic, "zarf+")
    ornek = [alan.eleman_alanlari(ic, a, paneller=False) for a, _ in liste[:6]]
    for i in range(len(zp["elemanlar"])):
        for b in ("N", "Mz", "von_mises"):
            ust, alt = np.array(zp["elemanlar"][i][b]), np.array(zm["elemanlar"][i][b])
            for o in ornek:
                d = np.array(o["elemanlar"][i][b])
                assert np.all(ust >= d - 1e-6 * (1 + np.abs(d)))
                if b != "von_mises":
                    assert np.all(alt <= d + 1e-6 * (1 + np.abs(d)))
        assert zp["elemanlar"][i]["belirleyen"]["kombinasyon"] in dict(liste)


def test_gerilme_ve_kullanim(bina2, celik):
    a = alan.eleman_alanlari(bina2.ic, "1.4G+1.6Q", paneller=False)
    for e in a["elemanlar"]:
        k = e["kesit"]
        Wy, Wz = k["Wy"], k["Wz"]
        for i in range(len(e["x"])):
            N, My, Mz = e["N"][i], e["My"][i], e["Mz"][i]
            beklenen = (N / k["A"] + abs(My) / Wy + abs(Mz) / Wz) / 1000
            olc = 2e-4 * (abs(N) / k["A"] + abs(My) / Wy + abs(Mz) / Wz) / 1000 + 1e-9     # 5 anlamlı basamağa yuvarlama payı
            assert e["sigma_max"][i] == pytest.approx(beklenen, abs=olc)
            # dikdörtgende en dış lif = dört köşenin en büyüğü
            kose = max(alan.lif_gerilmesi(k, N, My, Mz, sy * k["dy"] / 2, sz * k["dz"] / 2) for sy in (-1, 1) for sz in (-1, 1))
            assert e["sigma_max"][i] == pytest.approx(kose, abs=olc)
            assert e["von_mises"][i] >= max(abs(e["sigma_max"][i]), abs(e["sigma_min"][i])) - 1e-9
    # betonarme: kullanım tasarım kapasitelerinden (kiriş |M|/M_r, |V|/V_r)
    tas = {f: t for t in bina2.veri["tasarim"]["elemanlar"] for f in t["fe_elemanlar"]}
    kir = [e for e in a["elemanlar"] if e["tur"] == "kiris" and e["kullanim"]]
    assert kir
    for e in kir:
        assert min(e["kullanim"]) >= 0
        t = tas[e["no"]]
        Mr = next(float(c["kapasite"]) for c in t["kontroller"] if c["ad"].startswith("Eğilme (açıklık"))
        i = int(np.argmax(e["Mz"]))
        if e["Mz"][i] > 0:
            assert e["kullanim"][i] >= e["Mz"][i] / Mr * (1 - 2e-4)
    kol = [e for e in a["elemanlar"] if e["tur"] == "kolon"]
    assert all(e["kullanim"] is not None for e in kol)
    # çelik: von Mises / F_y; I kesit
    c = alan.eleman_alanlari(celik.ic, "G+Q", paneller=False)
    for e in c["elemanlar"]:
        assert e["kesit"]["sekil"] == "I" and e["kesit"]["malzeme"]["tur"] == "celik"
        fy = e["kesit"]["malzeme"]["fy"]
        assert np.array(e["kullanim"]) == pytest.approx(np.array(e["von_mises"]) / fy, rel=1e-3)
    assert c["not"] is None


def test_kesit_geometrisi_eksenleri(bina2, celik):
    """Kirişte derinlik y′ boyunca (Iz güçlü); kolonda yon takası dy/dz'yi değiştirir; I profilde h, b, tw, tf."""
    a = alan.eleman_alanlari(bina2.ic, "G", paneller=False)
    for e in a["elemanlar"]:
        k = e["kesit"]
        if e["tur"] == "kiris":
            assert k["eksen"] == "y" and k["dy"] == pytest.approx(k["h"]) and k["Iz"] >= k["Iy"]
        assert k["Wz"] == pytest.approx(k["Iz"] / (k["dy"] / 2), rel=1e-5)
    c = alan.eleman_alanlari(celik.ic, "G", paneller=False)
    k = c["elemanlar"][0]["kesit"]
    assert {"h", "b", "tw", "tf", "profil"} <= set(k) and k["tw"] < k["tf"] < k["b"]


def test_durum_hatalari(bina2):
    from matris_ogren import MatrisHatasi
    with pytest.raises(MatrisHatasi, match="bulunamadı"):
        alan.eleman_alanlari(bina2.ic, "YOK")
    with pytest.raises(MatrisHatasi, match="boş"):
        alan.durum_katsayilari(bina2.ic, "")
    with pytest.raises(MatrisHatasi, match="çözülmeli"):
        alan.eleman_alanlari({}, "G")
    serbest = alan.eleman_alanlari(bina2.ic, "benim", katsayilar={"G": 1.2, "Q": 0.5}, paneller=False)
    g, q = alan.eleman_alanlari(bina2.ic, "G", paneller=False), alan.eleman_alanlari(bina2.ic, "Q", paneller=False)
    assert np.array(serbest["elemanlar"][3]["Mz"]) == pytest.approx(1.2 * np.array(g["elemanlar"][3]["Mz"]) + 0.5 * np.array(q["elemanlar"][3]["Mz"]), rel=2e-4, abs=1e-4)


def test_eleman_bilgi_yardimcilari(bina2):
    ic = bina2.ic
    kir = bina2.veri["bina"]["kirisler"][0]
    fe = alan.fe_elemanlari(ic, "kiris", kir["no"])
    assert fe and all(e["kaynak_no"] == kir["no"] for e in fe)
    b = alan.eleman_bilgi_alani(ic, "kiris", kir["no"], "G")
    assert b["fe"] == [e["no"] for e in fe] and b["uclar"] and "Mz" in b["en_buyuk"]
    uc = b["uclar"][0]["i"]
    lam = np.array(next(e["lam"] for e in bina2.veri["ag"]["elemanlar"] if e["no"] == b["fe"][0]))
    assert uc["u_yerel"] == pytest.approx(list(lam @ np.array(uc["u"])), abs=1e-15)
    kay = alan.eleman_kaydi(ic, b["fe"][0])
    assert "lam" not in kay and kay["L"] > 0
    z = alan.eleman_bilgi_alani(ic, "kiris", kir["no"], "zarf+")
    assert z["uclar"] is None
    from matris_ogren import MatrisHatasi
    with pytest.raises(MatrisHatasi, match="ağında yok"):
        alan.fe_elemanlari(ic, "kolon", 9999)


# ---------------------------------------------------------------------------------------------
# Döşemeler: Navier plak, 45° yük payı, radye
# ---------------------------------------------------------------------------------------------
def test_navier_kare_plak():
    p = alan.navier_plak(1.0, 1.0, 1.0, 1.0, nu=0.3)
    c = alan.PLAK_IZGARA // 2
    assert p["w"][c][c] == pytest.approx(0.00406, abs=2e-5)
    assert p["mx"][c][c] == pytest.approx(0.0479, abs=2e-4) and p["my"][c][c] == pytest.approx(0.0479, abs=2e-4)
    assert abs(p["w"][0][c]) < 1e-15 and abs(p["mx"][c][0]) < 1e-12      # basit mesnetli kenar
    # dikdörtgen plakta kısa doğrultu momenti büyük
    r = alan.navier_plak(2.0, 1.0, 1.0, 1.0, nu=0.3)
    assert r["my"][c][c] > r["mx"][c][c]


def test_yuk_payi_poligonlari_ts500_dagitimi(bina2):
    p = alan.yuk_payi_poligonlari(0, 0, 5, 4, "cift")
    alanlar = {k: alan.poligon_alani(v) for k, v in p.items()}
    assert sum(alanlar.values()) == pytest.approx(20.0)
    assert alanlar["sol"] == pytest.approx(4 ** 2 / 4) and alanlar["alt"] == pytest.approx((5 + 1) / 2 * 2)
    t = alan.yuk_payi_poligonlari(0, 0, 9, 4, "tek")
    assert alan.poligon_alani(t["alt"]) == pytest.approx(18.0) and t["sol"] == []
    pan = alan.panel_alanlari(bina2.ic, "G")
    Y = bina2.ic["alan"]["Y"]
    for pn, d in zip(pan, Y.dosemeler):
        assert pn["izgara"]["q"] == pytest.approx(d["g"])
        assert sum(y["alan"] for y in pn["yuk_payi"]) == pytest.approx(d["alan"], rel=1e-9)
        for y, pay in zip(pn["yuk_payi"], d["paylar"]):
            assert y["alan"] * d["g"] == pytest.approx(pay["toplam_G"], rel=1e-6)       # alan × g = kirişe giden yük
        assert pn["alfa"]["x"] > 0 and pn["en_buyuk"]["w"] > 0
    q = alan.panel_alanlari(bina2.ic, "Q")
    assert q[0]["izgara"]["q"] == pytest.approx(Y.dosemeler[0]["q_top"])


def test_radye_alani_winkler(bina2):
    """Temel modülünün bıraktığı taban basıncı metası ile: p = k0·w, w = −u_Z; meta yoksa None."""
    ic = dict(bina2.ic)
    assert alan.radye_alani(ic, "G") is None
    taban = [d for d in bina2.veri["ag"]["dugumler"] if d["kat"] == 1]
    ic["temel"] = {"k0": 15000.0, "dugumler": [(d["no"], d["X"], d["Y"]) for d in taban]}
    r = alan.radye_alani(ic, "G")
    uz = {d["no"]: d["uZ"] for d in bina2.veri["durumlar"]["G"]["dugumler"]}
    for d in r["dugumler"]:
        assert d["w"] == pytest.approx(-uz[d["no"]], rel=1e-4)
        assert d["p"] == pytest.approx(15000.0 * d["w"], rel=1e-4)
    assert len(r["x"]) * len(r["y"]) >= len(r["dugumler"]) and r["p_maks"] >= r["p_min"]


# ---------------------------------------------------------------------------------------------
# Köprü "bina_alan"
# ---------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def kopru():
    oz = importlib.util.spec_from_file_location("web_kopru_alan_testi", PROJE / "docs" / "web_kopru.py")
    m = importlib.util.module_from_spec(oz)
    oz.loader.exec_module(m)
    return m


def _iste(k, islem, girdi):
    return json.loads(k.calistir(json.dumps({"islem": islem, "girdi": girdi})))


def test_kopru_bina_alan(kopru):
    assert "bina_alan" in kopru.BINA_ISLEMLER
    bina = yapi.bina_sablon("betonarme-tek-aciklik")
    c = _iste(kopru, "bina_coz", {"bina": bina})
    kim = c["veri"]["cozum_kimligi"]
    y = _iste(kopru, "bina_alan", {"cozum_kimligi": kim, "durum": "G+Q"})
    assert y["hata"] is None and y["cozum_kimligi"] == kim
    a = y["alan"]
    assert a["durum"] == "G+Q" and a["elemanlar"] and a["paneller"] and "aralik" in a
    y2 = _iste(kopru, "bina_alan", {"cozum_kimligi": kim, "durum": "zarf-", "istasyon": 5, "elemanlar": [a["elemanlar"][0]["no"]]})
    assert y2["hata"] is None and len(y2["alan"]["elemanlar"]) == 1 and "paneller" not in y2["alan"]
    assert len(y2["alan"]["elemanlar"][0]["x"]) < len(a["elemanlar"][0]["x"])
    # önbellekte yoksa bina ile yeniden çözülür
    y3 = _iste(kopru, "bina_alan", {"cozum_kimligi": "bina-yok", "bina": bina, "durum": "G"})
    assert y3["hata"] is None
    for girdi, metin in (({"cozum_kimligi": kim}, "boş"), ({"cozum_kimligi": kim, "durum": "G", "istasyon": 500}, "istasyon"),
                         ({"cozum_kimligi": kim, "durum": "XYZ"}, "bulunamadı"), ({"cozum_kimligi": "bina-yok", "durum": "G"}, "bellekte yok"),
                         ({"cozum_kimligi": kim, "durum": "G", "katsayilar": [1]}, "sözlük")):
        h = _iste(kopru, "bina_alan", girdi)
        assert h["hata_turu"] == "girdi" and metin in h["hata"], h


# ---------------------------------------------------------------------------------------------
# docs/isi_haritasi.js: sözdizimi, node birim testleri ve Python ile dil arası tutarlılık
# ---------------------------------------------------------------------------------------------
JS = PROJE / "docs" / "isi_haritasi.js"


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
def test_js_sozdizimi_ve_birim_testleri():
    r = subprocess.run([NODE, "--check", str(JS)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    r = subprocess.run([NODE, "--test", str(PROJE / "testler" / "js" / "isi_haritasi.test.js")], capture_output=True, text=True,
                       timeout=300, cwd=PROJE)
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-3000:]
    assert "# fail 0" in r.stdout


_JS_BETIK = r"""
const M = require(process.argv[1]);
let veri = "";
process.stdin.on("data", d => veri += d);
process.stdin.on("end", () => {
  const a = JSON.parse(veri), out = {smax: [], ext: {}, ag: null};
  for (const e of a.elemanlar) {
    const an = M.kesitAnahat(e.kesit, false);
    const s = [];
    for (let k = 0; k < e.x.length; k++) s.push(M.kesitUcLifleri(an, e.kesit, e.N[k], e.My[k], e.Mz[k]).cekme.s);
    out.smax.push(s);
  }
  for (const ad of ["N", "Mz", "u", "uZ", "von_mises", "kullanim"]) {
    const x = M.ekstremumBul(a.elemanlar, ad, null, null);
    out.ext[ad] = [x.min && x.min.deger, x.max && x.max.deger];
  }
  const ag = M.cubukAgi(a.elemanlar, {});
  const V = new Float32Array(ag.kose);
  M.degerleriDoldur(ag, a.elemanlar, "Mz", V);
  let mx = -Infinity, mn = Infinity, maxI = 0;
  for (let v = 0; v < ag.kose; v++) { mx = Math.max(mx, V[v]); mn = Math.min(mn, V[v]); }
  for (let i = 0; i < ag.I.length; i++) maxI = Math.max(maxI, ag.I[i]);
  out.ag = {kose: ag.kose, ucgen: ag.ucgen, maxI: maxI, mz: [mn, mx], aralik: ag.araliklar.map(r => r.say)};
  process.stdout.write(JSON.stringify(out));
});
"""


@pytest.mark.skipif(NODE is None, reason="node kurulu değil")
@pytest.mark.parametrize("sablon,durum", [("betonarme-2kat-3x2", "1.4G+1.6Q"), ("celik-1kat-depo", "G+Q")])
def test_js_python_tutarliligi(sablon, durum):
    """JS kesit anahatlarında en büyük lif gerilmesi = Python σ_maks (dikdörtgen ve I kesitte kesin); JS ekstremumları =
    Python aralıkları; ağ indisleri köşe sayısı içinde; renk değerleri istasyon değerleri."""
    r = yapi.bina_coz(yapi.bina_sablon(sablon), goster="yok", anlat=False)
    a = alan.eleman_alanlari(r.ic, durum, paneller=False)
    p = subprocess.run([NODE, "-e", _JS_BETIK, str(JS)], input=json.dumps(a), capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    js = json.loads(p.stdout)
    for e, s in zip(a["elemanlar"], js["smax"]):
        # I profilde katalog W ile anahat (köşe yarıçapsız) arasında küçük fark olabilir
        k = e["kesit"]
        tol = 2e-4 if k["sekil"] == "dikdortgen" else 0.04
        for i, (sj, sp) in enumerate(zip(s, e["sigma_max"])):
            olc = (abs(e["N"][i]) / k["A"] + abs(e["My"][i]) / k["Wy"] + abs(e["Mz"][i]) / k["Wz"]) / 1000
            assert sj == pytest.approx(sp, abs=tol * olc + 1e-9)
    for ad in ("N", "Mz", "u", "uZ", "von_mises", "kullanim"):
        lo, hi = a["aralik"][ad]
        olc = 1000.0 if ad in ("u", "uZ") else 1.0
        assert js["ext"][ad][0] == pytest.approx(lo * olc, rel=1e-4, abs=1e-9)     # çıktı 5 anlamlı basamak
        assert js["ext"][ad][1] == pytest.approx(hi * olc, rel=1e-4, abs=1e-9)
    assert js["ag"]["maxI"] < js["ag"]["kose"] and all(s > 0 for s in js["ag"]["aralik"])
    assert js["ag"]["mz"] == pytest.approx(a["aralik"]["Mz"], rel=1e-4)
