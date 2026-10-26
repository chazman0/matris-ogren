# -*- coding: utf-8 -*-
"""yapi.py / yapi_veri.py: kesit özellikleri, döşeme dağıtımı, eksen eşlemesi, korunum, kombinasyonlar, şablonlar, hatalar."""
from __future__ import annotations

import copy
import json
import math

import pytest

import matris_ogren as mo
import sonlu_eleman as se
import yapi
import yapi_veri as yv

SABLONLAR = list(yapi.BINA_SABLONLARI)


@pytest.fixture(scope="module")
def cozumler():
    """Her şablon bir kez çözülür (anlatımlı)."""
    return {ad: yapi.bina_coz(yapi.bina_sablon(ad), goster="yok") for ad in SABLONLAR}


def yakin(a, b, tol=1e-8):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# ---------------------------------------------------------------------------
# kütüphane (yapi_veri)
# ---------------------------------------------------------------------------
def test_kutuphane_degerleri():
    assert yv.BETONLAR["C30/37"]["Ec"] == 32000 and yv.BETONLAR["C30/37"]["fck"] == 30
    assert yv.BETONLAR["C25/30"]["fctk"] == 1.8
    assert yv.CELIKLER["S275"]["Fy"] == 275 and yv.CELIKLER["S275"]["E"] == 200000 and yv.CELIKLER["S275"]["G"] == 77200
    assert yv.TS498_HAREKETLI["konut"]["deger"] == 2.0 and yv.TS498_HAREKETLI["derslik"]["deger"] == 3.5
    assert yv.TS498_HAREKETLI["magaza"]["deger"] == 5.0 and yv.TS498_HAREKETLI["tribun-ayakta"]["deger"] == 7.5
    assert yv.TS498_BIRIM_AGIRLIK["betonarme"]["deger"] == 25.0 and yv.TS498_BIRIM_AGIRLIK["celik"]["deger"] == 78.5
    assert yakin(yv.DUVARLAR["tugla-delikli-19"]["deger"], 2.70, 1e-9)
    assert yakin(yv.DUVARLAR["gazbeton-25"]["deger"], 2.45, 1e-9)
    assert len(yv.PROFILLER) == 56 and yv.PROFILLER["IPE 300"]["Iy"] == 8356.0 and yv.PROFILLER["HEB 300"]["A"] == 149.1
    assert yv.azaltma_beta("a", 3) == 1.0 and yv.azaltma_beta("a", 7) == 0.71 and yv.azaltma_beta("a", 20) == 0.60
    assert yv.azaltma_beta("b", 5) == 0.94 and yv.azaltma_beta("yok", 9) == 1.0
    for kayit in yv.TS498_HAREKETLI.values():
        assert "kaynak" in kayit and "dogrulandi" in kayit
    ydkt = {s["ad"]: s for s in yv.KOMBINASYONLAR["cythye_ydkt"]["liste"]}
    assert ydkt["0.9G+1.6W"]["katsayilar"]["W"] == 1.6       # ÇYTHYE rüzgâr katsayısı 1,6 (1,3 değil)
    ts = {s["ad"]: s for s in yv.KOMBINASYONLAR["ts500"]["liste"]}
    assert ts["1.4G+1.6Q"]["katsayilar"] == {"G": 1.4, "Q": 1.6} and "6.3" in ts["1.4G+1.6Q"]["kaynak"]
    assert any(s["tur"] == "deprem" and "4.11" in s["kaynak"] for s in yv.KOMBINASYONLAR["ts500"]["liste"])


def test_dogrulanmamis_kayitlar_bilgi():
    """Liste bilgi amaçlıdır (hata değil): her öğe TABLO.anahtar biçiminde ve gerçekten dogrulandi False."""
    liste = yv.dogrulanmamis_kayitlar()
    assert isinstance(liste, list)
    for ad in liste:
        tablo, _, anahtar = ad.partition(".")
        assert hasattr(yv, tablo)
        if anahtar and not anahtar.startswith(("ts500", "cythye")):
            assert getattr(yv, tablo)[anahtar]["dogrulandi"] is False
    assert yapi.dogrulanmamis_kayitlar() == liste


# ---------------------------------------------------------------------------
# kesit özellikleri
# ---------------------------------------------------------------------------
def test_kesit_dikdortgen_kapali_form():
    mal = {"C30": yapi._malzeme("C30", {"kutuphane": "C30/37"})}
    k = yapi._kesit_ozellikleri("K25x50", {"tip": "dikdortgen", "b": 0.25, "h": 0.5, "malzeme": "C30"}, mal)
    b, h = 0.25, 0.5
    assert yakin(k["A"], b * h) and yakin(k["I_guclu"], b * h ** 3 / 12) and yakin(k["I_zayif"], h * b ** 3 / 12)
    beta = 1 / 3 - 0.21 * (b / h) * (1 - b ** 4 / (12 * h ** 4))
    assert yakin(k["J"], beta * b ** 3 * h) and yakin(k["Wpl"], b * h * h / 4) and yakin(k["Wel"], b * h * h / 6)
    assert yakin(k["E"], 32000e3) and yakin(k["G"], 0.4 * 32000e3) and k["gamma"] == 25.0
    k2 = yapi._kesit_ozellikleri("S50x30", {"tip": "dikdortgen", "b": 0.5, "h": 0.3, "malzeme": "C30"}, mal)
    assert yakin(k2["J"], k["J"] * (0.3 / 0.25) ** 3 * (0.5 / 0.5) * 0 + (1 / 3 - 0.21 * 0.6 * (1 - 0.6 ** 4 / 12)) * 0.3 ** 3 * 0.5)


def test_kesit_profil():
    mal = {"S275": yapi._malzeme("S275", {"kutuphane": "S275"})}
    k = yapi._kesit_ozellikleri("IPE300", {"tip": "profil", "profil": "ipe300", "malzeme": "S275"}, mal)
    assert k["profil"] == "IPE 300" and yakin(k["A"], 53.81e-4) and yakin(k["I_guclu"], 8356e-8) and yakin(k["I_zayif"], 603.8e-8)
    assert yakin(k["J"], 20.12e-8) and yakin(k["Wpl"], 628.4e-6) and yakin(k["h"], 0.3) and yakin(k["E"], 200000e3)
    with pytest.raises(mo.MatrisHatasi, match="profil"):
        yapi._kesit_ozellikleri("X", {"tip": "profil", "profil": "IPE 999", "malzeme": "S275"}, mal)


def test_kolon_yon_takasi():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kesitler"]["S30x50"] = {"tip": "dikdortgen", "b": 0.3, "h": 0.5, "malzeme": "C30"}
    for c in b["kolonlar"]:
        c["kesit"] = "S30x50"
    b["kolonlar"][0]["yon"] = "x"
    b["kolonlar"][1]["yon"] = "y"
    B = yapi._bina_oku(b)
    cx, cy = B.kolonlar[0], B.kolonlar[1]
    Ig, Iz = 0.3 * 0.5 ** 3 / 12, 0.5 * 0.3 ** 3 / 12
    assert yakin(cx["Iz_m"], Ig) and yakin(cx["Iy_m"], Iz) and cx["bX"] == 0.5 and cx["bY"] == 0.3
    assert yakin(cy["Iz_m"], Iz) and yakin(cy["Iy_m"], Ig) and cy["bX"] == 0.3 and cy["bY"] == 0.5
    v = yapi.bina_coz(b, anlat=False).veri["bina"]["kolonlar"]
    assert yakin(v[0]["Iz_m"], Ig, 1e-9) and yakin(v[1]["Iz_m"], Iz, 1e-9)


# ---------------------------------------------------------------------------
# döşeme dağıtımı
# ---------------------------------------------------------------------------
def _panel_bina(dx, dy, dagitim="otomatik", q=None):
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["akslar"]["x"][1]["konum"] = dx
    b["akslar"]["y"][1]["konum"] = dy
    b["dosemeler"][0]["dagitim"] = dagitim
    if q is not None:
        b["dosemeler"][0]["q"] = q
    return b


@pytest.mark.parametrize("dx,dy,dagitim,beklenen", [(5, 4, "otomatik", "cift"), (4, 4, "otomatik", "cift"), (8, 4, "otomatik", "cift"),
                                                     (8.1, 4, "otomatik", "tek"), (5, 4, "tek", "tek"), (12, 4, "cift", "cift")])
def test_doseme_dagitimi_korunum(dx, dy, dagitim, beklenen):
    B = yapi._bina_oku(_panel_bina(dx, dy, dagitim))
    Y = yapi._yukleri_hazirla(B)
    d = Y.dosemeler[0]
    assert d["tip"] == beklenen and yakin(d["m"], max(dx, dy) / min(dx, dy))
    topG = sum(p["toplam_G"] for p in d["paylar"])
    topQ = sum(p["toplam_Q"] for p in d["paylar"])
    assert yakin(topG, d["g"] * dx * dy, 1e-10) and yakin(topQ, d["q_top"] * dx * dy, 1e-10)
    lx, ly = min(dx, dy), max(dx, dy)
    for p in d["paylar"]:
        if beklenen == "cift":
            assert p["sekil"] == ("ucgen" if p["kenar"] == "kisa" or dx == dy else "trapez")
            assert yakin(p["tepe_g"], d["g"] * lx / 2)
            if p["sekil"] == "ucgen":
                assert yakin(p["q_eM_g"], d["g"] * lx / 3) and yakin(p["q_eV_g"], d["g"] * lx / 4)
            else:
                m = ly / lx
                assert yakin(p["q_eM_g"], d["g"] * lx / 2 * (1 - 1 / (3 * m * m))) and yakin(p["q_eV_g"], d["g"] * lx / 2 * (1 - 1 / (2 * m)))
            # parçalı yükün alanı = pay
            alan = sum((f1 + f2) / 2 * (x2 - x1) for x1, x2, f1, f2 in p["parcalar_birim"]) * p["tepe_g"]
            assert yakin(alan, p["toplam_G"], 1e-10)
        else:
            assert p["sekil"] == ("yok" if p["kenar"] == "kisa" else "duzgun")
            if p["sekil"] == "duzgun":
                assert yakin(p["q_eM_g"], d["g"] * lx / 2) and yakin(p["toplam_G"], d["g"] * lx / 2 * ly)


def test_doseme_yuk_degerleri():
    B = yapi._bina_oku(_panel_bina(5, 4))
    Y = yapi._yukleri_hazirla(B)
    d = Y.dosemeler[0]
    assert yakin(d["g_plak"], 25 * 0.12) and yakin(d["g"], 3.0 + 1.5) and d["q_top"] == 2.0 and "Çizelge 6" in d["q_kaynak"]
    B2 = yapi._bina_oku(_panel_bina(5, 4, q=3.5))
    assert yapi._yukleri_hazirla(B2).dosemeler[0]["q_top"] == 3.5


# ---------------------------------------------------------------------------
# eksen eşlemesi: düzlem çerçeve (cerceve) ile bina ağı aynı sonucu vermeli
# ---------------------------------------------------------------------------
def _portal_bina():
    """1 Y aksı, 2 X aksı, 2 kat: XZ düzleminde iki katlı düzlem çerçeve (döşeme yok; kirişlere ek yük)."""
    return {"tur": "bina", "baslik": "portal", "sistem": "betonarme",
            "akslar": {"x": [{"ad": "A", "konum": 0}, {"ad": "B", "konum": 6}], "y": [{"ad": "1", "konum": 0}]},
            "katlar": [{"no": 0, "kot": 0}, {"no": 1, "kot": 3.5}, {"no": 2, "kot": 6.5}],
            "malzemeler": {"C30": {"kutuphane": "C30/37"}},
            "kesitler": {"S": {"tip": "dikdortgen", "b": 0.3, "h": 0.5, "malzeme": "C30"},
                         "K": {"tip": "dikdortgen", "b": 0.25, "h": 0.6, "malzeme": "C30"}},
            "kolonlar": [{"no": 1, "aks": ["A", "1"], "kat": 1, "kesit": "S", "yon": "x"}, {"no": 2, "aks": ["B", "1"], "kat": 1, "kesit": "S", "yon": "x"},
                         {"no": 3, "aks": ["A", "1"], "kat": 2, "kesit": "S", "yon": "x"}, {"no": 4, "aks": ["B", "1"], "kat": 2, "kesit": "S", "yon": "x"}],
            "kirisler": [{"no": 1, "kat": 1, "bas": ["A", "1"], "son": ["B", "1"], "kesit": "K"},
                         {"no": 2, "kat": 2, "bas": ["A", "1"], "son": ["B", "1"], "kesit": "K"}],
            "dosemeler": [], "duvarlar": {},
            "ek_yukler": [{"tur": "kiris", "kiris": 1, "durum": "G", "q": 20.0}, {"tur": "kiris", "kiris": 2, "durum": "Q", "q": 8.0},
                          {"tur": "dugum", "aks": ["A", "1"], "kat": 2, "durum": "Q", "FX": 15.0}],
            "temeller": {"mesnet": "ankastre"}}


def test_eksen_eslemesi_cerceve_ile_ayni():
    bina = _portal_bina()
    r = yapi.bina_coz(bina, anlat=False)
    v = r.veri
    E = 32000e3
    A_s, I_s = 0.3 * 0.5, 0.3 * 0.5 ** 3 / 12
    A_k, I_k = 0.25 * 0.6, 0.25 * 0.6 ** 3 / 12
    W_s1, W_s2 = 25 * A_s * 3.5, 25 * A_s * 3.0
    oz_k = 25 * A_k
    cer = {"tip": "cerceve", "hesap": "sayisal",
           "dugumler": [{"no": 1, "x": 0, "y": 0}, {"no": 2, "x": 6, "y": 0}, {"no": 3, "x": 0, "y": 3.5}, {"no": 4, "x": 6, "y": 3.5},
                        {"no": 5, "x": 0, "y": 6.5}, {"no": 6, "x": 6, "y": 6.5}],
           "elemanlar": [{"no": 1, "dugumler": [1, 3], "E": E, "A": A_s, "I": I_s}, {"no": 2, "dugumler": [2, 4], "E": E, "A": A_s, "I": I_s},
                         {"no": 3, "dugumler": [3, 5], "E": E, "A": A_s, "I": I_s}, {"no": 4, "dugumler": [4, 6], "E": E, "A": A_s, "I": I_s},
                         {"no": 5, "dugumler": [3, 4], "E": E, "A": A_k, "I": I_k}, {"no": 6, "dugumler": [5, 6], "E": E, "A": A_k, "I": I_k}],
           "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "rz": True}, {"dugum": 2, "ux": True, "uy": True, "rz": True}]}
    durumlar = {"G": {"yukler": [{"dugum": 3, "Fy": -W_s1}, {"dugum": 4, "Fy": -W_s1}, {"dugum": 5, "Fy": -W_s2}, {"dugum": 6, "Fy": -W_s2}],
                      "yayili": [{"eleman": 5, "q": -(oz_k + 20.0)}, {"eleman": 6, "q": -oz_k}]},
                "Q": {"yukler": [{"dugum": 5, "Fx": 15.0}], "yayili": [{"eleman": 6, "q": -8.0}]}}
    ref = se.coz_coklu(cer, durumlar, diyagram_nokta=11)
    # bina ağı eleman sırası: kolonlar (kat 1: 1, 2; kat 2: 3, 4), sonra kirişler (kat 1, kat 2) → aynı sıra
    for durum in ("G", "Q"):
        for e_b, e_r in zip(v["durumlar"][durum]["elemanlar"], ref[durum]["elemanlar"]):
            fb, fr = e_b["uc_kuvvetleri"], e_r["uc_kuvvetleri"]
            for i3, i2 in ((0, 0), (1, 1), (5, 2), (6, 3), (7, 4), (11, 5)):
                assert yakin(fb[i3], fr[i2], 1e-8), (durum, e_b["no"], i3, fb[i3], fr[i2])
            for i3 in (2, 3, 4, 8, 9, 10):   # düzlem dışı bileşenler sıfır
                assert abs(fb[i3]) < 1e-8
            assert yakin(e_b["M"][0], e_r["M"][0], 1e-5) and yakin(e_b["M"][-1], e_r["M"][-1], 1e-5)   # diyagramlar 6 anlamlı basamak
            assert yakin(max(e_b["M"]), max(e_r["M"]), 1e-5) and yakin(min(e_b["M"]), min(e_r["M"]), 1e-5)
        # tepkiler: bina FZ = cerceve Fy, FX = Fx, MY = −Mz (bina Y = −z_m)
        tb = {t["dugum"]: t for t in v["durumlar"][durum]["tepkiler"]}
        for t in ref[durum]["tepkiler"]:
            no = 1 if t["dugum"] == 1 else 21
            assert yakin(tb[no]["FZ"], t["Fy"], 1e-8) and yakin(tb[no]["FX"], t["Fx"], 1e-8) and yakin(tb[no]["MY"], -t["Mz"], 1e-8)
            assert abs(tb[no]["FY"]) < 1e-8 and abs(tb[no]["MX"]) < 1e-8 and abs(tb[no]["MZ"]) < 1e-8
        # yer değiştirmeler: bina uX = u, uZ = v, rY = −θ
        db = {d["no"]: d for d in v["durumlar"][durum]["dugumler"]}
        u = ref[durum]["u"]
        for k, no in enumerate((1, 21, 1001, 1021, 2001, 2021)):
            assert yakin(db[no]["uX"], u[3 * k], 1e-8) and yakin(db[no]["uZ"], u[3 * k + 1], 1e-8) and yakin(db[no]["rY"], -u[3 * k + 2], 1e-8)
    # lam bina koordinatında: kolon x′ = +Z, kiriş x′ = +X ve y′ = +Z
    lam = {e["no"]: e["lam"] for e in v["ag"]["elemanlar"]}
    assert lam[1][0] == [0.0, 0.0, 1.0] and lam[1][1] == [-1.0, 0.0, 0.0] and lam[1][2] == [0.0, -1.0, 0.0]
    assert lam[5][0] == [1.0, 0.0, 0.0] and lam[5][1] == [0.0, 0.0, 1.0] and lam[5][2] == [0.0, -1.0, 0.0]


def test_y_yonu_kirisi_de_dusey_yuk_tasir():
    """Y doğrultusundaki kiriş (motor −z yönü): yerel y′ yine yukarı, M diyagramı X yönündeki eş kirişle aynı."""
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["akslar"]["y"][1]["konum"] = 5.0   # 5 × 5 kare panel: dört kiriş eş yüklü
    v = yapi.bina_coz(b, anlat=False).veri
    kir = [e for e in v["durumlar"]["G"]["elemanlar"] if e["no"] > 4]
    assert len(kir) == 4
    for e in kir[1:]:
        assert yakin(max(e["M"]), max(kir[0]["M"]), 1e-5) and yakin(min(e["M"]), min(kir[0]["M"]), 1e-5)
        assert yakin(e["uc_kuvvetleri"][1], kir[0]["uc_kuvvetleri"][1], 1e-6)
    kol = [e for e in v["durumlar"]["G"]["elemanlar"] if e["no"] <= 4]
    assert all(yakin(e["uc_kuvvetleri"][0], kol[0]["uc_kuvvetleri"][0], 1e-6) for e in kol)


# ---------------------------------------------------------------------------
# şablonlar: çözüm, simetri, korunum, tributary, temel, kombinasyon, JSON
# ---------------------------------------------------------------------------
def test_sablon_listesi():
    liste = yapi.bina_sablonlar()
    assert [s["ad"] for s in liste] == SABLONLAR and len(liste) == 5
    assert "betonarme-2kat-3x2" in SABLONLAR and "celik-1kat-depo" in SABLONLAR
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["kolonlar"] = []
    assert yapi.bina_sablon("betonarme-2kat-3x2")["kolonlar"]      # kopya
    with pytest.raises(mo.MatrisHatasi, match="şablonu yok"):
        yapi.bina_sablon("yok")


@pytest.mark.parametrize("ad", SABLONLAR)
def test_sablon_cozulur_ve_json(cozumler, ad):
    r = cozumler[ad]
    v = r.veri
    metin = json.dumps(v, ensure_ascii=False)
    json.loads(metin, parse_constant=lambda c: pytest.fail(f"geçersiz JSON sabiti: {c}"))
    assert v["tur"] == "bina" and v["surum"] == 1
    for anahtar in ("bina", "kutuphane_ozeti", "ag", "yukler", "durumlar", "kombinasyonlar", "sonuclar", "zarf", "akis", "ozet", "fe_model"):
        assert anahtar in v
    assert set(v["durumlar"]) == {"G", "Q"}
    assert v["ozet"]["sd_sayisi"] == 6 * len(v["ag"]["dugumler"]) == len(v["durumlar"]["G"]["u"])
    assert r.deger.shape == (v["ozet"]["sd_sayisi"], 1)
    for e in v["ag"]["elemanlar"]:
        assert e["tur"] in ("kolon", "kiris") and len(e["lam"]) == 3 and "kaynak_no" in e and "parca" in e
    for ad_, k in list(v["durumlar"].items()) + list(v["sonuclar"].items()):
        assert set(k) == {"u", "dugumler", "tepkiler", "elemanlar", "denge", "yaylar"}
        for e in k["elemanlar"]:
            n = len(e["x"])
            assert n >= 11 and all(len(e[a]) == n for a in ("N", "V", "M", "Vz", "My", "T")) and len(e["uc_kuvvetleri"]) == 12
            assert set(e["enb"]) == {"N", "V", "M", "Vz", "My", "T"}
        assert all(abs(x) < 1e-6 for x in k["denge"].values())
    assert all({"tur", "icerik", "etiket"} <= set(b) or b["tur"] in ("kod", "sema") for b in [
        {"tur": t, "icerik": i, "etiket": e} for t, i, e in r.anlatim.bloklar])
    assert sum(1 for t, _, _ in r.anlatim.bloklar if t == "sema") >= 3
    assert "Σ kolon taban N" in r.python_ciktisi and "[Hata" not in r.python_ciktisi
    # fe_model Sonlu eleman sayfasında çözülebilir (G durumu)
    fe = se.coz_coklu(v["fe_model"], {"G": {"yukler": v["fe_model"]["yukler"], "yayili": v["fe_model"]["yayili"]}})
    assert yakin(sum(t["Fy"] for t in fe["G"]["tepkiler"]) + sum(y["kuvvet"] for y in fe["G"]["yaylar"] if y["bilesen"] == "Fy"),
                 v["yukler"]["toplam"]["G"], 1e-6)


def test_yanit_boyutu(cozumler):
    assert len(json.dumps(cozumler["betonarme-2kat-3x2"].veri)) < 400_000
    assert len(json.dumps(cozumler["betonarme-3kat-3x3"].veri)) < 600_000


@pytest.mark.parametrize("ad", SABLONLAR)
def test_korunum_bes_sayi(cozumler, ad):
    v = cozumler[ad].veri
    for durum in ("G", "Q"):
        p = v["akis"]["korunum"][durum]
        assert yakin(p["toplam"], v["yukler"]["toplam"][durum], 1e-6)
        assert yakin(p["kolon_taban"], p["toplam"], 1e-6), (ad, durum, p)
        assert yakin(p["temel"] + p["yay"], p["toplam"], 1e-6)
        if durum == "G":
            assert yakin(p["dosemeler"] + p["duvarlar"] + p["kiris_oz"] + p["kolon_oz"] + p["ek"], p["toplam"], 1e-9)
    # python betiği aynı toplamı veriyor
    satir = next(s for s in cozumler[ad].python_ciktisi.splitlines() if s.startswith("Σ kolon taban N"))
    assert abs(float(satir.split("=")[1].split()[0]) - v["akis"]["korunum"]["G"]["kolon_taban"]) < 0.02


@pytest.mark.parametrize("ad", SABLONLAR)
def test_tributary_fe_farki_makul(cozumler, ad):
    for k in cozumler[ad].veri["akis"]["kolonlar"]:
        assert abs(k["fark_yuzde"]) < 40.0, k
        assert k["N_kum_G"] > 0 and k["N_trib_G"] > 0 and k["N_G"] > 0
    kol = cozumler[ad].veri["akis"]["kolonlar"]
    trib = sum(k["N_trib_G"] for k in kol if k["kat"] == 1)
    assert yakin(trib, cozumler[ad].veri["yukler"]["toplam"]["G"], 1e-6)   # yük alanları toplamı = toplam yük


def test_simetrik_bina_simetrik(cozumler):
    v = cozumler["betonarme-tek-aciklik"].veri
    N = [k["N_kum_G"] for k in v["akis"]["kolonlar"]]
    assert all(yakin(n, N[0], 1e-6) for n in N)
    v = cozumler["betonarme-2kat-3x2"].veri
    kol = {(k["aks"][0], k["aks"][1], k["kat"]): k for k in v["akis"]["kolonlar"]}
    for kat in (1, 2):
        assert yakin(kol[("A", "1", kat)]["N_kum_G"], kol[("A", "2", kat)]["N_kum_G"], 1e-6)
        assert yakin(kol[("C", "1", kat)]["N_kum_G"], kol[("C", "2", kat)]["N_kum_G"], 1e-6)
        assert kol[("B", "1", kat)]["N_kum_G"] > kol[("A", "1", kat)]["N_kum_G"] > kol[("C", "1", kat)]["N_kum_G"]   # 5 m açıklık > 4 m
    v = cozumler["betonarme-3kat-3x3"].veri
    kol = {(k["aks"][0], k["aks"][1], k["kat"]): k for k in v["akis"]["kolonlar"]}
    assert yakin(kol[("A", "1", 1)]["N_kum_G"], kol[("C", "3", 1)]["N_kum_G"], 1e-6)
    assert yakin(kol[("A", "2", 1)]["N_kum_G"], kol[("C", "2", 1)]["N_kum_G"], 1e-6)


def test_kombinasyon_superpozisyon(cozumler):
    v = cozumler["betonarme-2kat-3x2"].veri
    G, Q, D, S = v["durumlar"]["G"], v["durumlar"]["Q"], v["sonuclar"]["1.4G+1.6Q"], v["sonuclar"]["G+Q"]
    for i in range(len(G["u"])):
        assert yakin(D["u"][i], 1.4 * G["u"][i] + 1.6 * Q["u"][i], 1e-7)
        assert yakin(S["u"][i], G["u"][i] + Q["u"][i], 1e-7)
    for eg, eq, ed in zip(G["elemanlar"], Q["elemanlar"], D["elemanlar"]):
        for a in ("M", "V", "N"):
            for x, y, z in zip(eg[a], eq[a], ed[a]):
                assert yakin(z, 1.4 * x + 1.6 * y, 3e-5)
        for x, y, z in zip(eg["uc_kuvvetleri"], eq["uc_kuvvetleri"], ed["uc_kuvvetleri"]):
            assert yakin(z, 1.4 * x + 1.6 * y, 1e-7)
    for tg, tq, td in zip(G["tepkiler"], Q["tepkiler"], D["tepkiler"]):
        assert yakin(td["FZ"], 1.4 * tg["FZ"] + 1.6 * tq["FZ"], 1e-7)
    komb = {k["ad"]: k for k in v["kombinasyonlar"]}
    assert komb["1.4G+1.6Q"]["uygulandi"] and komb["G+Q"]["uygulandi"] and komb["G+Q"]["tur"] == "servis"
    assert not komb["0.9G+1.3W"]["uygulandi"] and "W" in komb["0.9G+1.3W"]["neden"]
    assert set(v["sonuclar"]) == {"1.4G+1.6Q", "G+Q"} and v["ozet"]["kombinasyon_sayisi"] == 2
    z = v["zarf"]["elemanlar"][0]
    e_d, e_s = D["elemanlar"][0], S["elemanlar"][0]
    assert yakin(z["M_max"], max(max(e_d["M"]), max(e_s["M"])), 1e-5) and yakin(z["M_min"], min(min(e_d["M"]), min(e_s["M"])), 1e-5)
    assert z["belirleyen"]["M_max"] in ("1.4G+1.6Q", "G+Q")


def test_celik_sablon_kombinasyonlari(cozumler):
    v = cozumler["celik-1kat-depo"].veri
    assert v["bina"]["kombinasyon_kumesi"] == "cythye_ydkt" and set(v["sonuclar"]) == {"1.4G", "G+Q"}
    assert v["bina"]["temeller"]["mesnet"] == "mafsal"
    assert all(m["tip"] == "mafsal" for m in v["ag"]["mesnetler"])
    assert yakin(v["kutuphane_ozeti"]["kesitler"]["IPE300"]["Iy"], 8356e-8, 1e-9)


def test_temel_sigma_formulu(cozumler):
    v = cozumler["betonarme-2kat-3x2"].veri
    G, Q = v["durumlar"]["G"], v["durumlar"]["Q"]
    tG = {t["dugum"]: t for t in G["tepkiler"]}
    tQ = {t["dugum"]: t for t in Q["tepkiler"]}
    for t in v["akis"]["temeller"]:
        N = tG[t["dugum"]]["FZ"] + tQ[t["dugum"]]["FZ"]
        MX = tG[t["dugum"]]["MX"] + tQ[t["dugum"]]["MX"]
        MY = tG[t["dugum"]]["MY"] + tQ[t["dugum"]]["MY"]
        B_, L_ = t["B"], t["L"]
        assert yakin(t["N_servis"], N, 1e-8)
        assert yakin(t["sigma_max"], N / (B_ * L_) + 6 * abs(MX) / (B_ * L_ ** 2) + 6 * abs(MY) / (L_ * B_ ** 2), 1e-7)
        assert yakin(t["sigma_min"], N / (B_ * L_) - 6 * abs(MX) / (B_ * L_ ** 2) - 6 * abs(MY) / (L_ * B_ ** 2), 1e-7)
        assert yakin(t["DC"], t["sigma_max"] / t["q_em"], 1e-7) and t["q_em"] == 200
        assert t["cekirdek_icinde"] == (t["e_X"] <= B_ / 6 + 1e-9 and t["e_Y"] <= L_ / 6 + 1e-9)
    ozel = {(t["aks"][0], t["aks"][1]): t for t in v["akis"]["temeller"]}
    assert ozel[("B", "1")]["B"] == 2.0 and ozel[("A", "1")]["B"] == 1.6
    assert v["ozet"]["en_buyuk_temel_DC"] == max(t["DC"] for t in v["akis"]["temeller"])


def test_elastik_temel():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["temeller"]["mesnet"] = "elastik"
    v = yapi.bina_coz(b, anlat=False).veri
    assert v["durumlar"]["G"]["yaylar"] and all(m["tip"] == "elastik" for m in v["ag"]["mesnetler"])
    p = v["akis"]["korunum"]["G"]
    assert yakin(p["yay"] + p["temel"], p["toplam"], 1e-6) and yakin(p["kolon_taban"], p["toplam"], 1e-6)
    fe = v["fe_model"]
    assert fe["yaylar"][0]["ky"] == 20000 * 1.6 * 1.6 and yakin(fe["yaylar"][0]["krx"], 20000 * 1.6 * 1.6 ** 3 / 12)
    assert all(d["uZ"] < 0 for d in v["durumlar"]["G"]["dugumler"])   # çökme aşağı


def test_sankey_ve_yuk_dokumu(cozumler):
    v = cozumler["betonarme-2kat-3x2"].veri
    s = v["akis"]["sankey"]
    kaynaklar = {x["kaynak"][0] for x in s}
    assert {"D", "K", "S", "T"} <= kaynaklar and any(x["hedef"] == "Zemin" for x in s)
    dG = sum(x["kN"] for x in s if x["kaynak"].startswith("D") and x["durum"] == "G")
    assert yakin(dG, v["akis"]["korunum"]["G"]["dosemeler"], 1e-6)
    zemin = sum(x["kN"] for x in s if x["hedef"] == "Zemin" and x["durum"] == "G")
    assert yakin(zemin, v["yukler"]["toplam"]["G"], 1e-6)
    for r in v["yukler"]["kirisler"]:
        assert yakin(r["G"]["toplam_kN"], r["G"]["doseme"] + r["G"]["duvar"] + r["G"]["oz"] + r["G"]["ek"], 1e-9)
        assert yakin(r["el_hesabi"]["R_G"], r["G"]["toplam_kN"] / 2, 1e-9)
    dis = next(r for r in v["yukler"]["kirisler"] if r["no"] == 1)
    assert dis["G"]["duvar"] > 0 and yakin(dis["kN_m"]["duvar"], 2.70 * (3.0 - 0.5), 1e-9)
    assert yakin(v["yukler"]["katlar"][0]["G"] + v["yukler"]["katlar"][1]["G"], v["yukler"]["toplam"]["G"], 1e-9)


def test_hareketli_yuk_ek_dugum_ve_doseme():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["ek_yukler"] = [{"tur": "dugum", "aks": ["B", "2"], "kat": 1, "durum": "Q", "FZ": -10},
                      {"tur": "doseme", "doseme": 1, "q": 1.0}, {"tur": "kiris", "kiris": 1, "durum": "G", "q": 2.0}]
    v = yapi.bina_coz(b, anlat=False).veri
    assert yakin(v["yukler"]["toplam"]["Q"], (2.0 + 1.0) * 20 + 10, 1e-9)
    assert yakin(v["akis"]["korunum"]["Q"]["kolon_taban"], v["yukler"]["toplam"]["Q"], 1e-6)
    assert yakin(next(r for r in v["yukler"]["kirisler"] if r["no"] == 1)["G"]["ek"], 2.0 * 5, 1e-9)


# ---------------------------------------------------------------------------
# öğretici hatalar
# ---------------------------------------------------------------------------
def test_hata_yuzen_doseme():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kirisler"] = [k for k in b["kirisler"] if k["no"] != 2]
    with pytest.raises(mo.MatrisHatasi, match="yüzen döşeme"):
        yapi.bina_coz(b)


def test_hata_kiris_uclari():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["kirisler"][0]["son"] = ["B", "2"]
    with pytest.raises(mo.MatrisHatasi, match="aynı aks çizgisi"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["kirisler"][0]["son"] = ["A", "1"]
    with pytest.raises(mo.MatrisHatasi, match="aynı aks kesişimi"):
        yapi.bina_coz(b)


def test_komsu_olmayan_kiris_bolunur():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    k1 = next(k for k in b["kirisler"] if k["kat"] == 1 and k["bas"] == ["A", "1"] and k["son"] == ["B", "1"])
    k2 = next(k for k in b["kirisler"] if k["kat"] == 1 and k["bas"] == ["B", "1"] and k["son"] == ["C", "1"])
    b["kirisler"].remove(k2)
    k1["son"] = ["C", "1"]
    v = yapi.bina_coz(b, anlat=False).veri
    kir = next(k for k in v["bina"]["kirisler"] if k["no"] == k1["no"])
    assert len(kir["parcalar"]) == 2 and yakin(kir["L"], 9.0)
    assert yakin(v["akis"]["korunum"]["G"]["kolon_taban"], v["yukler"]["toplam"]["G"], 1e-6)


def test_hata_bilinmeyen_kesit_ve_malzeme():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kolonlar"][0]["kesit"] = "YOK"
    with pytest.raises(mo.MatrisHatasi, match="kesit 'YOK'"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["malzemeler"]["C30"] = {"kutuphane": "C99"}
    with pytest.raises(mo.MatrisHatasi, match="kütüphanede"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["dosemeler"][0]["kullanim"] = "uzay-istasyonu"
    with pytest.raises(mo.MatrisHatasi, match="TS 498"):
        yapi.bina_coz(b)


def test_hata_sd_siniri():
    xs = [{"ad": chr(65 + i), "konum": 4.0 * i} for i in range(12)]
    ys = [{"ad": str(j + 1), "konum": 4.0 * j} for j in range(12)]
    b = {"tur": "bina", "akslar": {"x": xs, "y": ys}, "katlar": [{"no": k, "kot": 3.0 * k} for k in range(3)],
         "malzemeler": {"C30": {"kutuphane": "C30/37"}}, "kesitler": {"S": {"tip": "dikdortgen", "b": 0.4, "h": 0.4, "malzeme": "C30"}},
         "kolonlar": [{"no": 200 * k + 12 * i + j + 1, "aks": [xs[i]["ad"], ys[j]["ad"]], "kat": k, "kesit": "S"}
                      for k in (1, 2) for i in range(12) for j in range(12)]}
    with pytest.raises(mo.MatrisHatasi, match="küçült"):
        yapi.bina_coz(b)
    b["akslar"]["x"].append({"ad": "M", "konum": 48.0})
    with pytest.raises(mo.MatrisHatasi, match="en fazla 12"):
        yapi.bina_coz(b)


def test_hata_cesitli():
    with pytest.raises(mo.MatrisHatasi, match="JSON"):
        yapi.bina_coz("{bozuk")
    with pytest.raises(mo.MatrisHatasi, match="bina modeli değil"):
        yapi.bina_coz(se.ornek_model("kafes-iki-cubuk"))
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kolonlar"].append(dict(b["kolonlar"][0], no=99))
    with pytest.raises(mo.MatrisHatasi, match="ikinci kolon"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["dosemeler"][0]["kose"] = [["A", "1"], ["A", "2"]]
    with pytest.raises(mo.MatrisHatasi, match="tek hücre"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kirisler"][0]["duvar"] = "yok-duvar"
    with pytest.raises(mo.MatrisHatasi, match="duvar"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["ek_yukler"] = [{"tur": "kiris", "kiris": 1, "durum": "W", "q": 1}]
    with pytest.raises(mo.MatrisHatasi, match="Dilim 2"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kolonlar"][0]["kat"] = 5
    with pytest.raises(mo.MatrisHatasi, match="kat 5 yok"):
        yapi.bina_coz(b)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["katlar"] = b["katlar"][:1]
    with pytest.raises(mo.MatrisHatasi, match="Katlar eksik"):
        yapi.bina_coz(b)


# ---------------------------------------------------------------------------
# yük yolu ve kütüphane özeti
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("hedef", [{"tur": "doseme", "no": 1, "durum": "G"}, {"tur": "kiris", "no": 2, "durum": "Q"},
                                   {"tur": "kolon", "no": 7, "durum": "G+Q"}])
def test_yuk_yolu(cozumler, hedef):
    bina = yapi.bina_sablon("betonarme-2kat-3x2")
    y = yapi.yuk_yolu(bina, cozumler["betonarme-2kat-3x2"].veri, hedef)
    json.dumps(y)
    assert y["hedef"]["durum"] == hedef["durum"] and len(y["adimlar"]) >= 3
    for a in y["adimlar"]:
        assert a["baslik"] and a["bloklar"] and set(a["vurgu"]) == {"dosemeler", "kirisler", "kolonlar", "temeller"}
        assert all(b["tur"] in ("md", "math") and b["icerik"] for b in a["bloklar"])
    son = y["adimlar"][-1]
    assert "Denge" in son["baslik"] and son["vurgu"]["temeller"]
    if hedef["tur"] == "doseme":
        assert y["adimlar"][0]["vurgu"]["dosemeler"] == [1] and len(y["adimlar"][1]["vurgu"]["kirisler"]) == 4
    if hedef["tur"] == "kolon":
        assert 7 in y["adimlar"][0]["vurgu"]["kolonlar"]


def test_yuk_yolu_hatalari(cozumler):
    bina = yapi.bina_sablon("betonarme-2kat-3x2")
    v = cozumler["betonarme-2kat-3x2"].veri
    with pytest.raises(mo.MatrisHatasi, match="bina_coz"):
        yapi.yuk_yolu(bina, {}, {"tur": "doseme", "no": 1})
    with pytest.raises(mo.MatrisHatasi, match="Döşeme 99 yok"):
        yapi.yuk_yolu(bina, v, {"tur": "doseme", "no": 99})
    with pytest.raises(mo.MatrisHatasi, match="durum"):
        yapi.yuk_yolu(bina, v, {"tur": "doseme", "no": 1, "durum": "W"})


def test_kutuphane_ozeti():
    k = yapi.kutuphane()
    json.dumps(k, ensure_ascii=False)
    assert {"malzemeler", "kesit_katalogu", "kullanim_siniflari", "duvarlar", "kaplamalar", "kombinasyon_kumeleri", "sablonlar", "dogrulanmamis"} <= set(k)
    assert k["malzemeler"]["C30/37"]["E_MPa"] == 32000 and k["malzemeler"]["S275"]["Fy"] == 275
    assert len(k["kesit_katalogu"]["profiller"]["IPE"]) == 18 and len(k["kesit_katalogu"]["profiller"]["HEB"]) == 19
    assert k["kullanim_siniflari"]["konut"]["deger"] == 2.0
    assert k["dogrulanmamis"] == yv.dogrulanmamis_kayitlar()


def test_anlat_kapali_hizli():
    r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"), anlat=False)
    assert len(r.anlatim.bloklar) == 1 and r.python_kodu == "" and r.veri["ozet"]["eleman"] == 26


def test_ornek_modeller_bozulmadi():
    assert len(se.ORNEK_MODELLER) == 20
