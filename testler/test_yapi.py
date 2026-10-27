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
    assert [s["ad"] for s in liste] == SABLONLAR and len(liste) == 7
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
    assert v["tur"] == "bina" and v["surum"] == 2          # Dilim 2: S/W/E durumları ince kayıt (diyagram: false)
    for anahtar in ("bina", "kutuphane_ozeti", "ag", "yukler", "durumlar", "kombinasyonlar", "sonuclar", "zarf", "akis", "ozet", "fe_model",
                    "deprem", "ruzgar", "kar", "kutle_merkezi", "cozum_kimligi"):
        assert anahtar in v
    assert {"G", "Q"} <= set(v["durumlar"])
    assert v["ozet"]["sd_sayisi"] == 6 * sum(1 for d in v["ag"]["dugumler"] if not d["efendi"])   # efendi düğümler sanal
    assert len(v["durumlar"]["G"]["u"]) == 6 * len(v["ag"]["dugumler"])
    assert r.deger.shape == (len(v["durumlar"]["G"]["u"]), 1)
    tur = {}
    for e in v["ag"]["elemanlar"]:          # temel-kirisi / radye-serit: mütemadi ve radye temel (temel.py)
        assert e["tur"] in ("kolon", "kiris", "temel-kirisi", "radye-serit") and len(e["lam"]) == 3 and "kaynak_no" in e and "parca" in e
        tur[e["no"]] = e["tur"]
    tam = [("G", v["durumlar"]["G"]), ("Q", v["durumlar"]["Q"])] + list(v["sonuclar"].items())
    for ad_, k in tam:
        assert set(k) == {"u", "diyagram", "dugumler", "tepkiler", "elemanlar", "denge", "yaylar"} and k["diyagram"] is True
        for e in k["elemanlar"]:
            if tur[e["no"]] == "radye-serit":      # radye şeridi: yalnız enb (taban basıncı ve şerit momentleri veri.temel'de)
                assert set(e) == {"no", "diyagram", "enb"} and e["diyagram"] is False
                continue
            n = len(e["x"])                       # temel kirişi parçası (a ≈ 0,5 m) 3 noktalı: uçlar + orta
            assert n >= (3 if tur[e["no"]] == "temel-kirisi" else 11) and all(len(e[a]) == n for a in ("N", "V", "M", "Vz", "My", "T"))
            assert len(e["uc_kuvvetleri"]) == 12 and set(e["enb"]) == {"N", "V", "M", "Vz", "My", "T"}
    for ad_, k in v["durumlar"].items():
        if ad_ not in ("G", "Q"):          # S, W, E: yalnız uç kuvvetleri + enb (tam dizi bina_kombinasyon ile tembel)
            assert k["diyagram"] is False and k["u"] is None
            assert all((set(e) == {"no", "diyagram"} if tur[e["no"]] == "radye-serit" else
                        set(e) == {"no", "uc_kuvvetleri", "enb"} and len(e["uc_kuvvetleri"]) == 12) for e in k["elemanlar"])
        assert all(abs(x) < 1e-6 for x in k["denge"].values()), (ad_, k["denge"])
    for ad_, k in v["sonuclar"].items():
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
    """veri JSON boyutu (UTF-8 metin, köprüdeki gibi ensure_ascii=False): varsayılan şablonlar ve S, W, E hepsi açık."""
    boy = lambda v: len(json.dumps(v, ensure_ascii=False))  # noqa: E731
    assert boy(cozumler["betonarme-2kat-3x2"].veri) < 300_000
    assert boy(cozumler["betonarme-3kat-3x3"].veri) < 800_000          # S, W, E açık şablon
    assert boy(cozumler["betonarme-4kat-4x3"].veri) < 1_000_000        # Dilim 3: veri.tasarim (116 eleman) dahil
    for ad, sinir in (("betonarme-2kat-3x2", 450_000), ("betonarme-4kat-4x3", 1_300_000)):
        b = yapi.bina_sablon(ad)
        for d in ("S", "W", "E"):
            b["yuk_durumlari"][d]["acik"] = True
        v = yapi.bina_coz(b, anlat=False).veri
        assert boy(v) < sinir, (ad, boy(v))
        assert len(v["durumlar"]) == 12 and v["deprem"] and v["ruzgar"] and v["kar"]


@pytest.mark.parametrize("ad", SABLONLAR)
def test_korunum_bes_sayi(cozumler, ad):
    v = cozumler[ad].veri
    for durum in ("G", "Q"):
        p = v["akis"]["korunum"][durum]
        assert yakin(p["toplam"], v["yukler"]["toplam"][durum], 1e-6)
        # mütemadi / radye: temel öz ağırlığı kat 0'da (kolonlardan geçmez; korunumda temel_oz)
        assert yakin(p["kolon_taban"] + p.get("temel_oz", 0.0), p["toplam"], 1e-6), (ad, durum, p)
        assert yakin(p["temel"], p["toplam"], 1e-6) and yakin(p["tepki"] + p["yay"], p["temel"], 1e-9)   # temel = tepki + yay
        if durum == "G":
            assert yakin(p["dosemeler"] + p["duvarlar"] + p["kiris_oz"] + p["kolon_oz"] + p["ek"] + p.get("temel_oz", 0.0), p["toplam"], 1e-9)
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
    temel_oz = cozumler[ad].veri["akis"]["korunum"]["G"].get("temel_oz", 0.0)     # mütemadi / radye öz ağırlığı kolonlardan geçmez
    assert yakin(trib + temel_oz, cozumler[ad].veri["yukler"]["toplam"]["G"], 1e-6)   # yük alanları toplamı = toplam yük


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
    G, Q, D = v["durumlar"]["G"], v["durumlar"]["Q"], v["sonuclar"]["1.4G+1.6Q"]
    S = yapi.kombinasyon_kisa(cozumler["betonarme-2kat-3x2"].ic, "G+Q")      # tembel tam kayıt (köprü bina_kombinasyon)
    assert D["u"] is None and S["u"] is None and len(G["u"]) == 108      # kombinasyonlarda u yazılmaz (boyut)
    for dg, dq, dd, ds in zip(G["dugumler"], Q["dugumler"], D["dugumler"], S["dugumler"]):
        for a in ("uX", "uY", "uZ", "rX", "rY", "rZ"):
            assert yakin(dd[a], 1.4 * dg[a] + 1.6 * dq[a], 1e-7) and yakin(ds[a], dg[a] + dq[a], 1e-7)
    for eg, eq in zip(G["elemanlar"], Q["elemanlar"]):
        assert eg["x"] == eq["x"]                                          # ortak istasyonlar
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
    assert set(v["sonuclar"]) == {"1.4G+1.6Q"} and v["ozet"]["kombinasyon_sayisi"] == 2 == v["zarf"]["kombinasyon_sayisi"]
    assert not komb["G+1.2Q+1.2T"]["uygulandi"] and "T" in komb["G+1.2Q+1.2T"]["neden"]      # 6.4: T yoksa satır yok
    for ad in ("1.4G+1.6Q+1.6S", "G+Q+S"):                                                     # kar kapalı: kar satırları yok
        assert not komb[ad]["uygulandi"] and "S (kar)" in komb[ad]["neden"]
    z = v["zarf"]["elemanlar"][0]
    e_d, e_s = D["elemanlar"][0], S["elemanlar"][0]
    assert yakin(z["M_max"], max(max(e_d["M"]), max(e_s["M"])), 1e-5) and yakin(z["M_min"], min(min(e_d["M"]), min(e_s["M"])), 1e-5)
    assert z["belirleyen"]["M_max"] in ("1.4G+1.6Q", "G+Q")


def test_celik_sablon_kombinasyonlari(cozumler):
    v = cozumler["celik-1kat-depo"].veri
    assert v["bina"]["kombinasyon_kumesi"] == "cythye_ydkt" and set(v["sonuclar"]) == {"1.4G"}
    komb = {k["ad"]: k for k in v["kombinasyonlar"]}
    assert komb["1.2G+1.6Q"]["uygulandi"] and komb["1.2G+1.6Q"]["aile"] == "1.2G+1.6Q+0.5(Qr|S|R)"   # 2b, S = 0
    assert not komb["1.2G+1.6(Qr|S|R)"]["uygulandi"]                                                    # 2a: S gerekli
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
        N += 25.0 * B_ * L_ * 0.6                                    # temel öz ağırlığı (h = 0.6 m)
        assert yakin(t["N_temel"], 25.0 * B_ * L_ * 0.6, 1e-8) and yakin(t["N_servis"], N, 1e-8)
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
    assert yakin(p["yay"], p["toplam"], 1e-6) and p["tepki"] == 0.0 and yakin(p["temel"], p["toplam"], 1e-6)
    assert yakin(p["kolon_taban"], p["toplam"], 1e-6)
    # temel N/M yay kuvvetlerinden: Σ N_G = toplam G; M'ler sıfır değil
    assert yakin(sum(t["N_G"] for t in v["akis"]["temeller"]), p["toplam"], 1e-6)
    assert all(t["N_G"] > 0 for t in v["akis"]["temeller"]) and any(abs(t["MX"]) > 1e-6 for t in v["akis"]["temeller"])
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
    assert yakin(zemin, v["yukler"]["toplam"]["G"], 1e-5)          # sankey bantları 6 anlamlı basamak
    for r in v["yukler"]["kirisler"]:
        assert yakin(r["G"]["toplam_kN"], r["G"]["doseme"] + r["G"]["duvar"] + r["G"]["oz"] + r["G"]["ek"], 1e-9)
        assert yakin(r["el_hesabi"]["R_G"], r["G"]["toplam_kN"] / 2, 1e-9)
    dis = next(r for r in v["yukler"]["kirisler"] if r["no"] == 1)
    assert dis["G"]["duvar"] > 0 and yakin(dis["kN_m"]["duvar"], 2.70 * (3.0 - 0.5), 1e-9)
    assert [k["kat"] for k in v["yukler"]["katlar"]] == [0, 1, 2] and v["yukler"]["katlar"][0]["G"] == 0.0
    assert yakin(sum(k["G"] for k in v["yukler"]["katlar"]), v["yukler"]["toplam"]["G"], 1e-9)


def test_gozden_gecirme_ornegi_duvarli_tek_panel():
    """Gözden geçirmede çöken örnek: 2×2 aks, 4 × 6 m tek panel, yalnız K1'de duvar, konut. G ve Q istasyonları ortak,
    kombinasyonlar kurulur, korunum sağlanır."""
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["akslar"]["x"][1]["konum"] = 4.0
    b["akslar"]["y"][1]["konum"] = 6.0
    for k in b["kirisler"]:
        k["duvar"] = "tugla19" if k["no"] == 1 else None
    v = yapi.bina_coz(b, anlat=False).veri
    for eg, eq, ed in zip(v["durumlar"]["G"]["elemanlar"], v["durumlar"]["Q"]["elemanlar"], v["sonuclar"]["1.4G+1.6Q"]["elemanlar"]):
        assert eg["x"] == eq["x"] == ed["x"]
    p = v["akis"]["korunum"]["G"]
    assert yakin(p["kolon_taban"], p["toplam"], 1e-6) and yakin(p["temel"], p["toplam"], 1e-6)


def test_kombinasyon_dogrudan_cozumle_ayni():
    """1.4G+1.6Q süperpozisyonu, aynı katsayılarla ölçeklenmiş yüklerin tek durumda doğrudan çözümüyle 1e-9 içinde aynı."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    r = yapi.bina_coz(b, anlat=False)
    v = r.veri
    fe = v["fe_model"]
    B = yapi._bina_oku(b)
    Y = yapi._yukleri_hazirla(B)
    ag, model = yapi._ag_olustur(B, Y)
    durumlar, _, _ = yapi._yuk_durumlari(B, Y, ag)
    birlesik = {"yukler": [], "yayili": []}
    for ad, g in (("G", 1.4), ("Q", 1.6)):
        for y in durumlar[ad]["yukler"]:
            birlesik["yukler"].append({a: (x * g if a != "dugum" else x) for a, x in y.items()})
        for y in durumlar[ad]["yayili"]:
            birlesik["yayili"].append({a: (x * g if a in ("q", "q1", "q2") else x) for a, x in y.items()})
    dogrudan = se.coz_coklu(model, {"D": birlesik}, diyagram_nokta=11)["D"]
    # yuvarlanmamış süperpozisyon (motor iç yolu) 1e-9 içinde doğrudan çözümle aynı
    kisa_m, _ = yapi._durumlari_coz(B, model, durumlar)
    kisa = {ad: yapi._kisa_bina(k, ag) for ad, k in kisa_m.items()}
    komb = yapi._kisa_birlesim(kisa, {"G": 1.4, "Q": 1.6})
    for ek, ed in zip(komb["elemanlar"], dogrudan["elemanlar"]):
        assert len(ek["x"]) == len(ed["x"]) and all(abs(a - c_) < 1e-12 for a, c_ in zip(ek["x"], ed["x"]))
        for a, b_ in zip(ek["uc_kuvvetleri"], ed["uc_kuvvetleri"]):
            assert yakin(a, b_, 1e-9)
        for b in ("V", "M", "My", "Vz", "N", "T"):
            for a, c_ in zip(ek[b], ed[b] if isinstance(ed[b], list) else [ed[b]] * len(ek[b])):
                assert abs(a - c_) <= 1e-9 * max(1.0, abs(c_)), (ek["no"], b)
    for i, (a, b_) in enumerate(zip(komb["u"], dogrudan["u"])):
        assert yakin(a, b_, 1e-9)
    # JSON çıktısı (6 anlamlı basamak) 1e-5 içinde aynı
    for ek, ed in zip(v["sonuclar"]["1.4G+1.6Q"]["elemanlar"], dogrudan["elemanlar"]):
        for a, c_ in zip(ek["M"], ed["M"]):
            assert abs(a - c_) <= 1e-5 * max(1.0, abs(c_))
    assert fe["tip"] == "cerceve3b"


def test_tek_dogrultu_kare_panel_korunum():
    """dagitim 'tek' + kare panel: X kirişleri taşıyan sayılır, yük kaybolmaz."""
    B = yapi._bina_oku(_panel_bina(5, 5, "tek"))
    Y = yapi._yukleri_hazirla(B)
    d = Y.dosemeler[0]
    assert d["tip"] == "tek" and "Kare panel" in d["not"]
    assert yakin(sum(p["toplam_G"] for p in d["paylar"]), d["g"] * 25.0, 1e-10)
    for p in d["paylar"]:
        if p["key"][1] == "x":
            assert p["sekil"] == "duzgun" and p["kenar"] == "uzun" and yakin(p["toplam_G"], d["g"] * 2.5 * 5.0)
        else:
            assert p["sekil"] == "yok" and p["kenar"] == "kisa"
    v = yapi.bina_coz(_panel_bina(5, 5, "tek"), anlat=False).veri
    assert yakin(v["akis"]["korunum"]["G"]["kolon_taban"], v["yukler"]["toplam"]["G"], 1e-6)


def test_balkon_10m2_ustu():
    """TS 498:2021 Çizelge 6 satır 4: balkon > 10 m² → q = 5,0 + 0,35·(A − 10)."""
    b = _panel_bina(5, 4)
    b["dosemeler"][0]["kullanim"] = "balkon"
    B = yapi._bina_oku(b)
    d = B.dosemeler[0]
    assert yakin(d["q"], 5.0 + 0.35 * 10.0) and "0,35" in d["q_kaynak"]
    b2 = _panel_bina(2.5, 4)
    b2["dosemeler"][0]["kullanim"] = "balkon"
    assert yapi._bina_oku(b2).dosemeler[0]["q"] == 5.0
    v = yapi.bina_coz(b, anlat=False).veri
    assert yakin(v["yukler"]["dosemeler"][0]["q"], 8.5) and yakin(v["yukler"]["toplam"]["Q"], 8.5 * 20.0, 1e-9)


def test_kolonsuz_ara_dugum_yuk_alani():
    """A–B–C akslı, yalnız A ve C'de kolon (B kolonsuz sürekli kiriş düğümü): kolonsuz düğüm payı taşıyan kirişin uç
    kolonlarına dağıtılır → Σ N_trib = toplam G; fark makul."""
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["kolonlar"] = [c for c in b["kolonlar"] if c["aks"][0] != "B"]
    v = yapi.bina_coz(b, anlat=False).veri
    kol = v["akis"]["kolonlar"]
    assert len(kol) == 8
    trib = sum(k["N_trib_G"] for k in kol if k["kat"] == 1)
    assert yakin(trib, v["yukler"]["toplam"]["G"], 1e-6) and v["akis"]["korunum"]["G"]["dagitilamayan"] == 0.0
    assert yakin(v["akis"]["korunum"]["G"]["yuk_alani"], v["yukler"]["toplam"]["G"], 1e-6)
    assert all(abs(k["fark_yuzde"]) < 40.0 for k in kol)
    # 5 m açıklık tarafındaki A kolonları, 4 m tarafındaki C kolonlarından çok taşır (basit kiriş oranı: 5/9 → A? hayır: B'ye yakın olan az)
    kA = next(k for k in kol if k["aks"] == ["A", "1"] and k["kat"] == 1)
    kC = next(k for k in kol if k["aks"] == ["C", "1"] and k["kat"] == 1)
    assert kA["N_trib_G"] > 0 and kC["N_trib_G"] > 0 and kC["N_trib_G"] > kA["N_trib_G"]   # B düğümü C'ye yakın (4 m < 5 m)


def test_kat0_dugum_yuku_korunum():
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["ek_yukler"] = [{"tur": "dugum", "aks": ["A", "1"], "kat": 0, "durum": "G", "FZ": -50}]
    v = yapi.bina_coz(b, anlat=False).veri
    p = v["akis"]["korunum"]["G"]
    assert v["yukler"]["katlar"][0]["kat"] == 0 and v["yukler"]["katlar"][0]["G"] == 50.0
    assert p["kat0"] == 50.0 and yakin(p["kolon_taban"] + p["kat0"], p["toplam"], 1e-6) and yakin(p["temel"], p["toplam"], 1e-6)
    assert yakin(p["yuk_alani"] + p["kat0"], p["toplam"], 1e-6)


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
    with pytest.raises(mo.MatrisHatasi, match="yuk_durumlari / deprem"):
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


# ===========================================================================
# Dilim 2: TBDY 2018 eşdeğer deprem yükü, rüzgâr, kar, rijit diyafram, kombinasyon kümeleri
# ===========================================================================
def hepsi_acik(ad, **deprem):
    b = yapi.bina_sablon(ad)
    for d in ("S", "W", "E"):
        b["yuk_durumlari"][d]["acik"] = True
    b["deprem"].update(deprem)
    return b


@pytest.fixture(scope="module")
def uc_kat():
    """3 katlı şablon (deprem, rüzgâr, kar açık; rijit diyafram) ve iç paket."""
    return yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"), anlat=False)


def tork(v, K):
    """Mesnet tepkilerinin düşey eksen (Z) etrafındaki momenti, orijine göre: Σ (X·F_Y − Y·F_X + M_Z)."""
    xy = {n["no"]: (n["X"], n["Y"]) for n in v["ag"]["dugumler"]}
    return sum(xy[t["dugum"]][0] * t["FY"] - xy[t["dugum"]][1] * t["FX"] + t["MZ"] for t in K["tepkiler"])


@pytest.mark.parametrize("zemin,SS,beklenen", [("ZD", 0.60, 1.4 + 0.4 * (1.2 - 1.4)), ("ZD", 0.20, 1.6), ("ZD", 1.70, 1.0),
                                               ("ZE", 0.875, 1.3 + 0.5 * (1.1 - 1.3)), ("ZC", 1.0, 1.2), ("ZA", 0.9, 0.8)])
def test_FS_ara_deger(zemin, SS, beklenen):
    assert yakin(yv.zemin_katsayisi(yv.TBDY_FS, zemin, SS), beklenen, 1e-12)


@pytest.mark.parametrize("zemin,S1,beklenen", [("ZD", 0.25, 2.1), ("ZC", 0.55, 1.45), ("ZE", 0.05, 4.2), ("ZE", 0.9, 2.0), ("ZB", 0.3, 0.8)])
def test_F1_ara_deger(zemin, S1, beklenen):
    assert yakin(yv.zemin_katsayisi(yv.TBDY_F1, zemin, S1), beklenen, 1e-12)


def test_tablo_degerleri_arastirma_ile_ayni():
    """Tablo 2.1, 2.2, 3.1, 4.1 (arayüz alt kümesi), Ct, Tablo 4.2 ve kombinasyon katsayıları kaynak listeleriyle birebir."""
    assert yv.TBDY_FS["ZC"] == [1.3, 1.3, 1.2, 1.2, 1.2, 1.2] and yv.TBDY_FS["ZE"] == [2.4, 1.7, 1.3, 1.1, 0.9, 0.8]
    assert yv.TBDY_F1["ZD"] == [2.4, 2.2, 2.0, 1.9, 1.8, 1.7] and yv.TBDY_F1["ZC"][-1] == 1.4
    assert [yv.TBDY_BKS_I[k]["I"] for k in (1, 2, 3)] == [1.5, 1.2, 1.0]
    tablo41 = {"betonarme-cerceve-yuksek": ("A11", 8, 3, 3), "betonarme-perde-bosluksuz": ("A13", 6, 2.5, 2),
               "betonarme-perde-cerceve": ("A15", 7, 2.5, 2), "betonarme-cerceve-sinirli": ("A31", 4, 2.5, 7),
               "betonarme-tek-katli-mafsalli": ("A16", 3, 2, None), "celik-cerceve-yuksek": ("C11", 8, 3, 3),
               "celik-dismerkez-capraz": ("C12", 8, 2.5, 2), "celik-merkezi-capraz": ("C13", 5, 2, 4),
               "celik-cerceve-sinirli": ("C31", 4, 2.5, 7), "celik-tek-katli-mafsalli": ("C16", 4, 2, None)}
    for ad, (kod, R, D, bys) in tablo41.items():
        t = yv.TBDY_TASIYICI[ad]
        assert (t["kod"], t["R"], t["D"], t["BYS_min"]) == (kod, R, D, bys), ad
    assert list(yv.TBDY_TASIYICI_ARAYUZ) == list(tablo41)
    assert yv.tasiyici_anahtar("celik-mcm-yuksek") == "celik-cerceve-yuksek" and yv.tasiyici_anahtar("yok") is None
    assert yv.TBDY_CT["betonarme-cerceve"] == 0.10 and yv.TBDY_CT["celik-cerceve"] == 0.08 and yv.TBDY_CT["diger"] == 0.07
    assert yv.TBDY_ETKIN_RIJITLIK["kolon"]["egilme"] == 0.70 and yv.TBDY_ETKIN_RIJITLIK["kiris"]["egilme"] == 0.35
    K = {k: {s["ad"]: s["katsayilar"] for s in v["liste"]} for k, v in yv.KOMBINASYONLAR.items()}
    ts = K["ts500"]   # TS 500 Denk. (6.3)–(6.6), (6.9), (6.10); TBDY (4.11), (4.12)
    assert ts["1.4G+1.6Q"] == {"G": 1.4, "Q": 1.6} and ts["G+1.2Q+1.2T"] == {"G": 1.0, "Q": 1.2, "T": 1.2}
    assert ts["G+1.3Q+1.3W"] == {"G": 1.0, "Q": 1.3, "W": 1.3} and ts["0.9G+1.3W"] == {"G": 0.9, "W": 1.3}
    assert ts["1.4G+1.6Q+1.6H"] == {"G": 1.4, "Q": 1.6, "H": 1.6} and ts["0.9G+1.6H"] == {"G": 0.9, "H": 1.6}
    assert ts["G+Q+0.2S+Ed(H)+0.3Ed(Z)"] == {"G": 1.0, "Q": 1.0, "S": 0.2, "EH": 1.0, "EZ": 0.3}
    assert ts["0.9G+H+Ed(H)-0.3Ed(Z)"] == {"G": 0.9, "H": 1.0, "EH": 1.0, "EZ": -0.3}
    # kar: TS 500 terim vermez; TS 498:2021 md. 3.1 hareketli yük (Q gibi), md. 12.1 kar + rüzgâr S/2 + W ya da S + W/2
    assert ts["1.4G+1.6Q+1.6S"] == {"G": 1.4, "Q": 1.6, "S": 1.6} and ts["G+Q+S"] == {"G": 1.0, "Q": 1.0, "S": 1.0}
    assert ts["G+1.3Q+1.3(S/2)+1.3W"] == {"G": 1.0, "Q": 1.3, "S": 0.65, "W": 1.3}
    assert ts["G+1.3Q+1.3S+1.3(W/2)"] == {"G": 1.0, "Q": 1.3, "S": 1.3, "W": 0.65}
    kar = {s["ad"]: s for s in yv.KOMBINASYONLAR["ts500"]["liste"] if "S" in s["katsayilar"] and "EH" not in s["katsayilar"]}
    assert all(s["gerekli"] == ["S"] for s in kar.values()) and len(kar) == 4
    assert "12.1(a)" in kar["G+1.3Q+1.3(S/2)+1.3W"]["kaynak"] and "12.1(b)" in kar["G+1.3Q+1.3S+1.3(W/2)"]["kaynak"]
    assert "md. 3.1" in kar["1.4G+1.6Q+1.6S"]["kaynak"] and "TS 498" in yv.KOMBINASYONLAR["ts500"]["kaynak"]
    yd = K["cythye_ydkt"]   # ÇYTHYE 5.3.1 (rüzgâr 1,6W) + TBDY 9.2.5.1 (4.11'de 1,2G)
    assert yd["1.4G"] == {"G": 1.4} and yd["1.2G+1.6(Qr|S|R)"] == {"G": 1.2, "S": 1.6}
    assert yd["1.2G+1.6Q+0.5(Qr|S|R)"] == {"G": 1.2, "Q": 1.6, "S": 0.5}
    assert yd["1.2G+1.6(Qr|S|R)+Q"] == {"G": 1.2, "S": 1.6, "Q": 1.0} and yd["1.2G+1.6(Qr|S|R)+0.8W"] == {"G": 1.2, "S": 1.6, "W": 0.8}
    assert yd["1.2G+Q+0.5(Qr|S|R)+1.6W"] == {"G": 1.2, "Q": 1.0, "S": 0.5, "W": 1.6} and yd["0.9G+1.6W"] == {"G": 0.9, "W": 1.6}
    assert yd["1.2G+Q+0.2S+Ed(H)+0.3Ed(Z)"] == {"G": 1.2, "Q": 1.0, "S": 0.2, "EH": 1.0, "EZ": 0.3}
    gk = K["cythye_gkt"]    # ÇYTHYE 5.3.2 + TBDY (9.1a–c)
    assert gk["G"] == {"G": 1.0} and gk["G+W"] == {"G": 1.0, "W": 1.0} and gk["0.6G+W"] == {"G": 0.6, "W": 1.0}
    assert gk["G+0.7E"]["EH"] == 0.7 and gk["G+0.75Q+0.75S+0.75(0.7E)"]["EH"] == 0.525 and gk["0.6G+0.7E"]["G"] == 0.6


def test_spektrum_dort_bolge_ve_koseler():
    sp_ = yapi._spektrum(1.0, 0.3, "ZC")
    SDS, SD1, TA, TB, TL = sp_["SDS"], sp_["SD1"], sp_["TA"], sp_["TB"], sp_["TL"]
    assert yakin(SDS, 1.2) and yakin(SD1, 0.45) and yakin(TA, 0.2 * 0.45 / 1.2) and yakin(TB, 0.375) and TL == 6.0
    Sae = sp_["Sae"]
    assert yakin(Sae(0.0), 0.4 * SDS) and yakin(Sae(TA), SDS) and yakin(Sae(TB), SDS)
    assert yakin(Sae(TA / 2), (0.4 + 0.3) * SDS) and yakin(Sae((TA + TB) / 2), SDS)
    assert yakin(Sae(1.0), SD1) and yakin(Sae(2.0), SD1 / 2) and yakin(Sae(TL), SD1 / TL) and yakin(Sae(8.0), SD1 * TL / 64)
    for T in (TA, TB, TL):          # süreklilik
        assert yakin(Sae(T - 1e-9), Sae(T + 1e-9), 1e-6)


def test_Ra_TB_de_surekli(uc_kat):
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    B = yapi._bina_oku(b)
    Y = yapi._yukleri_hazirla(B)
    dep = yapi._deprem_on(B, Y, yapi._kat_kutleleri(B, Y, n=B.deprem["n"], kar_payi=0.3))
    TB, R, I, D = dep["sp"]["TB"], dep["R"], dep["I"], dep["D"]
    assert yakin(dep["Ra"](0.0), D) and yakin(dep["Ra"](TB), R / I) and yakin(dep["Ra"](TB + 1e-9), R / I, 1e-8)
    assert yakin(dep["Ra"](TB / 2), D + (R / I - D) / 2)
    assert yakin(dep["SaR"](1.0), dep["sp"]["Sae"](1.0) / (R / I))


def test_taban_kesme_ve_kat_kuvvetleri(uc_kat):
    d = uc_kat.veri["deprem"]
    g = 9.81
    assert d["Tp_yontem"] == "ampirik" and yakin(d["Tp"], d["TpA"]) and yakin(d["TpA"], 0.1 * 9.6 ** 0.75)
    assert yakin(d["m_t"], d["W_t"] / g) and yakin(d["m_t"], sum(k["m_i"] for k in d["katlar"]))
    V = d["m_t"] * d["Sae_Tp"] / d["Ra"] * g
    assert yakin(d["SaR"], d["Sae_Tp"] / d["Ra"]) and yakin(d["VtE"], max(V, 0.04 * d["m_t"] * d["I"] * d["SDS"] * g))
    assert yakin(d["VtE_min"], 0.04 * d["m_t"] * d["I"] * d["SDS"] * g)
    assert yakin(d["dFN"], 0.0075 * 3 * d["VtE"])
    # Σ F_iE + ΔF_NE = V_tE; F_iE ∝ m_i·H_i (Denk. 4.23); V_i = Σ_{j≥i} F_j
    kat = d["katlar"]
    assert yakin(sum(k["F_x"] for k in kat), d["VtE"], 1e-9) and yakin(sum(k["F_y"] for k in kat), d["Y"]["VtE"], 1e-9)
    mh = sum(k["m_i"] * k["H"] for k in kat)
    for k in kat:
        F = (d["VtE"] - d["dFN"]) * k["m_i"] * k["H"] / mh + (d["dFN"] if k["kat"] == 3 else 0.0)
        assert yakin(k["F_x"], F, 1e-9)
        assert yakin(k["V_x"], sum(j["F_x"] for j in kat if j["kat"] >= k["kat"]), 1e-9)
    assert yakin(kat[0]["V_x"], d["VtE"]) and [k["H"] for k in kat] == [3.2, 6.4, 9.6]


def test_taban_kesme_alt_siniri():
    """Uzun periyotta (C_t büyük girildi) V_tE = 0,04·m_t·I·S_DS·g alt sınırı belirler (Denk. 4.19)."""
    v = yapi.bina_coz(hepsi_acik("betonarme-2kat-3x2", Ct=0.6, periyot="ampirik"), anlat=False).veri["deprem"]
    assert v["TpA"] > 1.7 and v["X"]["alt_sinir_etkin"]
    assert yakin(v["VtE"], 0.04 * v["m_t"] * v["I"] * v["SDS"] * 9.81, 1e-9) and v["VtE"] > v["X"]["VtE_hesap"]


def test_H_i_temel_kotundan_olculur():
    """Temel kotu 0 değilse H_i ve H_N temel üstünden ölçülür; kat kuvvetleri kotun kaymasından etkilenmez."""
    b = hepsi_acik("betonarme-2kat-3x2")
    d0 = yapi.bina_coz(b, anlat=False).veri["deprem"]
    for kt in b["katlar"]:
        kt["kot"] += 100.0
    d1 = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert yakin(d1["HN"], d0["HN"]) and [k["H"] for k in d1["katlar"]] == [3.0, 6.0]
    for k0, k1 in zip(d0["katlar"], d1["katlar"]):
        assert yakin(k0["F_x"], k1["F_x"], 1e-8)


def test_rayleigh_tek_serbestlik_kapali_form():
    """Tek katlı, dört kolonlu, kirişleri çok rijit bina; rijit diyafram (kütle efendi düğümde): T = 2π√(m/k), k = 4·12EI/h³;
    betonarmede deprem hesabı çatlamış kesitle (TBDY 4.5.8, kolon EI × 0,70)."""
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kesitler"]["K25x50"] = {"tip": "dikdortgen", "b": 1.0, "h": 2.0, "malzeme": "C30"}
    for k in b["kirisler"]:
        k["duvar"] = None
    b["yuk_durumlari"]["E"]["acik"] = True
    b["deprem"]["periyot"] = "rayleigh"
    r = yapi.bina_coz(b, anlat=False)
    d = r.veri["deprem"]
    assert r.veri["ag"]["diyafram"] == "rijit" and len(r.veri["ag"]["diyaframlar"]) == 1 and d["catlamis_rijitlik"]
    k = 4 * 12 * 32000e3 * 0.70 * (0.3 ** 4 / 12) / 3.0 ** 3
    T = 2 * math.pi * math.sqrt(d["m_t"] / k)
    assert abs(d["X"]["Tp_rayleigh"] / T - 1) < 0.01 and abs(d["Y"]["Tp_rayleigh"] / T - 1) < 0.01
    assert d["X"]["Tp_rayleigh"] >= T          # kiriş tam rijit değil: biraz daha esnek
    # Denk. (4.26) ile aynı: tek kat → T = 2π√(m·d/F)
    ray = d["X"]["rayleigh"][0]
    assert yakin(d["X"]["Tp_rayleigh"], 2 * math.pi * math.sqrt(ray["m"] * ray["d_f"] / ray["F_f"]), 1e-8)
    # T_p ≤ 1,4·T_pA (md. 4.7.3.2)
    assert d["Tp"] <= 1.4 * d["TpA"] * (1 + 1e-9) and yakin(d["Tp"], min(d["X"]["Tp_rayleigh"], 1.4 * d["TpA"]), 1e-9)
    assert any("1,4·T_pA" in u for u in d["uyarilar"])


def test_dismerkezlik_momenti_ve_isaret(uc_kat):
    """M_ib = F_iE·0,05·B_i; EX+ kuvveti +Y'ye kaydırır (M_Z = −F·e), EY+ +X'e (M_Z = +F·e): mesnet torku farkı ±2ΣF·e."""
    v, ic = uc_kat.veri, uc_kat.ic
    d = v["deprem"]
    for k in d["katlar"]:
        assert yakin(k["Mb_x"], k["F_x"] * 0.05 * 8.0, 1e-9) and yakin(k["Mb_y"], k["F_y"] * 0.05 * 10.0, 1e-9)
        assert k["B_dik_x"] == 8.0 and k["B_dik_y"] == 10.0
    ex = 2 * sum(k["Mb_x"] for k in d["katlar"])
    ey = 2 * sum(k["Mb_y"] for k in d["katlar"])
    assert yakin(tork(v, yapi.kombinasyon_kisa(ic, "EX+")) - tork(v, yapi.kombinasyon_kisa(ic, "EX-")), ex, 1e-7)
    assert yakin(tork(v, yapi.kombinasyon_kisa(ic, "EY+")) - tork(v, yapi.kombinasyon_kisa(ic, "EY-")), -ey, 1e-7)
    for ad, yon in (("EX+", "FX"), ("EY-", "FY")):
        K = yapi.kombinasyon_kisa(ic, ad)
        assert yakin(abs(sum(t[yon] for t in K["tepkiler"])), d["VtE"], 1e-8)


def test_dismerkezlik_esnek_diyafram_ayni_moment():
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["deprem"]["diyafram"] = "esnek"
    r = yapi.bina_coz(b, anlat=False)
    v = r.veri
    assert v["ag"]["diyafram"] == "esnek" and not v["ag"]["diyaframlar"]
    ex = 2 * sum(k["Mb_x"] for k in v["deprem"]["katlar"])
    assert yakin(tork(v, yapi.kombinasyon_kisa(r.ic, "EX+")) - tork(v, yapi.kombinasyon_kisa(r.ic, "EX-")), ex, 1e-7)


def test_simetrik_bina_eta_bir_ve_donme_sifir():
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["deprem"]["dismerkezlik"] = 0.0
    r = yapi.bina_coz(b, anlat=False)
    d = r.veri["deprem"]
    assert all(yakin(k["eta_bx"], 1.0, 1e-9) and yakin(k["eta_by"], 1.0, 1e-9) for k in d["katlar"])
    efendi = [n for n in yapi.kombinasyon_kisa(r.ic, "EX+")["dugumler"] if n["no"] >= 9000]
    assert len(efendi) == 3 and all(abs(n["rZ"]) < 1e-15 for n in efendi)
    # kütle merkezi plan ortasında
    assert all(yakin(k["X"], 5.0) and yakin(k["Y"], 4.0) for k in r.veri["kutle_merkezi"])
    # %5 dışmerkezlik η_bi'yi 1'in biraz üstüne çıkarır (A1 yok)
    d5 = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"), anlat=False).veri["deprem"]
    assert all(1.0 < k["eta_bx"] < 1.2 for k in d5["katlar"]) and d5["X"]["D_b"] == 1.0


def _a_aksi_rijit(kesit_a=0.9, kesit=0.3):
    """A aksı kolonları büyük (kesit_a), ötekiler küçük: rijitlik merkezi A aksına kayar → Y depreminde A1 burulma düzensizliği."""
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["kesitler"]["SA"] = {"tip": "dikdortgen", "b": kesit_a, "h": kesit_a, "malzeme": "C30"}
    b["kesitler"]["SK"] = {"tip": "dikdortgen", "b": kesit, "h": kesit, "malzeme": "C30"}
    for c in b["kolonlar"]:
        c["kesit"] = "SA" if c["aks"][0] == "A" else "SK"
    return b


def test_dbi_kat_bazinda_iki_dogrultuya():
    """TBDY md. 4.7.4: A1 düzensizliği olan i'inci katta ±%5 dışmerkezlik HER İKİ deprem doğrultusu için D_bi = (η_bi/1,2)²
    ile büyütülür — kat bazında (η_bi o katın iki doğrultudaki değerinin büyüğü). Düzensizlik Y depreminde çıksa da X depremi
    dışmerkezliği de büyür; katlar farklı D_bi alır."""
    r = yapi.bina_coz(_a_aksi_rijit(), anlat=False)
    v = r.veri
    d = v["deprem"]
    kat = d["katlar"]
    assert all(k["eta_by"] > 1.2 > k["eta_bx"] for k in kat)                       # düzensizlik yalnız Y depreminde
    for k in kat:
        eta = max(k["eta_bx"], k["eta_by"])
        assert yakin(k["D_b"], (eta / 1.2) ** 2, 1e-9) and yakin(d["D_b_kat"][str(k["kat"])], k["D_b"], 1e-9)
        assert yakin(k["e_x"], 0.05 * k["D_b"] * k["B_dik_x"], 1e-9) and yakin(k["e_y"], 0.05 * k["D_b"] * k["B_dik_y"], 1e-9)
    Db = [k["D_b"] for k in kat]
    assert Db[0] > Db[1] > Db[2] > 1.0                                                # kat kat farklı (tek değer değil)
    assert yakin(d["X"]["D_b"], max(Db)) and yakin(d["Y"]["D_b"], max(Db))
    # E durumlarındaki ek burulma: EX+ ile EX− tepki torklarının farkı = 2·Σ F_i·e_i (kat bazında D_bi ile), Y için de
    for yon, y in (("X", "x"), ("Y", "y")):
        fark = abs(tork(v, v["durumlar"][f"E{yon}+"]) - tork(v, v["durumlar"][f"E{yon}-"]))
        beklenen = 2 * sum(k[f"F_{y}"] * k[f"e_{y}"] for k in kat)
        assert yakin(fark, beklenen, 2e-3), (yon, fark, beklenen)
        tek = 2 * sum(k[f"F_{y}"] * 0.05 * max(Db) * k[f"B_dik_{y}"] for k in kat)   # eski hata: tek (en büyük) D_b
        assert abs(fark - tek) > 0.02 * tek
    assert any("md. 4.7.4" in u and "her iki" in u for u in d["uyarilar"]) and d["uygulanabilir"]


def test_eta_2_ustu_tablo44_diger_satiri():
    """η_bi > 2,0: Tablo 4.4'ün 'diğer tüm binalar' satırı (DTS 1–2: BYS ≥ 5, DTS 3–4: BYS ≥ 6) — yöntem otomatik
    reddedilmez; alçak binada (BYS büyük) yine uygulanabilir. η_bi işaretli ötelemelerle: A–B akslarında Y doğrultusunda
    perde gibi kolonlar, C'de narin kolonlar ve %30 dışmerkezlikle A kenarı ters yönde ötelenir, (Δ)ort küçülür, η_bi > 2."""
    b = _a_aksi_rijit(0.3, 0.3)
    b["kesitler"]["SA"]["h"] = 2.0
    for c in b["kolonlar"]:
        if c["aks"][0] in ("A", "B"):
            c["kesit"], c["yon"] = "SA", "y"
    b["analiz"]["catlamis_rijitlik"] = False
    b["deprem"]["dismerkezlik"] = 0.3
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    eta = max(max(k["eta_bx"], k["eta_by"]) for k in d["katlar"])
    assert eta > 2.0, eta
    u = d["uygulanabilirlik"]
    assert u["satir"] == "diger" and u["esik"] == u["esik_diger"] == (5 if d["DTS"][0] in "12" else 6)
    assert d["uygulanabilir"] == (d["BYS"] >= u["esik_diger"])
    assert d["BYS"] >= 6 and d["uygulanabilir"]                                       # H_N = 9,6 m: BYS büyük → izinli
    assert any("diğer tüm binalar" in x and "yine uygulanabilir" in x for x in d["uyarilar"])
    assert not any("uygulanamaz (Tablo 4.4)" in x for x in d["uyarilar"])
    assert all(k["D_b"] <= (2.0 / 1.2) ** 2 + 1e-9 for k in d["katlar"]) and max(k["D_b"] for k in d["katlar"]) > 2.7


def test_rijitlik_merkezi_paydalari():
    """X_RM = Σ(k_y·X)/Σk_y, Y_RM = Σ(k_x·Y)/Σk_x. 9 × 4 m plan (A = 0, B = 9; 1 = 0, 2 = 4), 30×60 kolonlar yön x:
    hepsi aynı → rijitlik merkezi plan ortası (4,5; 2); A aksı kolonları büyütülünce X_RM A'ya kayar."""
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["akslar"]["x"][1]["konum"] = 9.0
    b["kesitler"]["S"] = {"tip": "dikdortgen", "b": 0.3, "h": 0.6, "malzeme": "C30"}
    for c in b["kolonlar"]:
        c["kesit"], c["yon"] = "S", "x"
    rm = yapi._rijitlik_merkezi(yapi._bina_oku(b))[0]
    assert yakin(rm["X"], 4.5, 1e-12) and yakin(rm["Y"], 2.0, 1e-12)
    # yalnız A1 kolonu büyük (60×60): X_RM = Σ k_y X / Σ k_y, Y_RM = Σ k_x Y / Σ k_x (eski kod paydaları takas ediyordu)
    b["kesitler"]["B"] = {"tip": "dikdortgen", "b": 0.6, "h": 0.6, "malzeme": "C30"}
    b["kolonlar"][0]["kesit"] = "B"
    B = yapi._bina_oku(b)
    rm = yapi._rijitlik_merkezi(B)[0]
    ky = {(c["ix"], c["iy"]): c["Iy_m"] for c in B.kolonlar}
    kx = {(c["ix"], c["iy"]): c["Iz_m"] for c in B.kolonlar}
    X = sum(v * B.xk[ix] for (ix, iy), v in ky.items()) / sum(ky.values())
    Y = sum(v * B.yk[iy] for (ix, iy), v in kx.items()) / sum(kx.values())
    assert yakin(rm["X"], X, 1e-12) and yakin(rm["Y"], Y, 1e-12) and 0 < rm["X"] < 4.5 and 0 < rm["Y"] < 2.0
    assert 0 <= rm["X"] <= 9 and 0 <= rm["Y"] <= 4                                    # plan içinde (eski: Y = 8 > 4)


def test_diyafram_koleleri_omega_carpi_r(uc_kat):
    """Rijit diyaframlı katta köle yatay yer değiştirmeleri efendinin rijit cisim hareketi: u_s = u_m + ω × r."""
    v = uc_kat.veri
    K = yapi.kombinasyon_kisa(uc_kat.ic, "EX+")
    u = {n["no"]: n for n in K["dugumler"]}
    efendi = {n["kat"]: n for n in v["ag"]["dugumler"] if n["efendi"]}
    assert set(efendi) == {1, 2, 3} and all(e["no"] == 9000 + k for k, e in efendi.items())
    sayi = 0
    for n in v["ag"]["dugumler"]:
        if n["efendi"] or n["kat"] == 0:
            continue
        m = efendi[n["kat"]]
        um, us = u[m["no"]], u[n["no"]]
        assert abs(us["uX"] - (um["uX"] - um["rZ"] * (n["Y"] - m["Y"]))) < 1e-11
        assert abs(us["uY"] - (um["uY"] + um["rZ"] * (n["X"] - m["X"]))) < 1e-11
        assert abs(us["rZ"] - um["rZ"]) < 1e-12
        sayi += 1
    assert sayi == 27 and abs(u[9003]["rZ"]) > 1e-7       # dışmerkezlik katı döndürür
    dyf = v["ag"]["diyaframlar"]
    assert len(dyf) == 3 and all(len(x["dugumler"]) == 9 for x in dyf) and dyf[0]["ana"] == 9001


def test_goreli_kat_otelemesi_ve_theta():
    b = hepsi_acik("betonarme-3kat-3x3", SS_DD3=0.4, S1_DD3=0.12, dolgu="esnek", BKS=1)
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert d["I"] == 1.5 and d["DTS"] == "1a"
    sp2, sp3 = yapi._spektrum(1.0, 0.3, "ZC"), yapi._spektrum(0.4, 0.12, "ZC")
    lam = sp3["Sae"](d["Tp"]) / sp2["Sae"](d["Tp"])
    assert yakin(d["lambda"], lam) and 0 < lam < 1 and yakin(d["SDS_DD3"], sp3["SDS"])
    assert yakin(d["sinir_oran"], 0.016 * 1.0) and yakin(d["theta_sinir"], 0.12 * 3 / (0.5 * 8))
    w = {k["kat"]: k["w_i"] for k in d["katlar"]}
    for k in d["katlar"]:
        for y in ("x", "y"):
            assert yakin(k[f"delta_etkin_{y}"], d["R"] / d["I"] * k[f"delta_{y}"], 1e-9)            # δ = (R/I)·Δ
            assert yakin(k[f"oran_{y}"], d["lambda"] * k[f"delta_etkin_{y}"] / k["h"], 1e-9)          # λ·δ/h
            Vi = k[f"V_{y}"]
            assert yakin(k[f"theta_{y}"], k[f"delta_ort_{y}"] * sum(w[j] for j in w if j >= k["kat"]) / (Vi * k["h"]), 1e-9)
            assert k[f"delta_{y}"] > 0 and k[f"d_{y}"] > 0
        assert k["uygun"] == (k["oran_x"] <= k["sinir"] and k["oran_y"] <= k["sinir"])
    d2 = yapi.bina_coz(hepsi_acik("celik-1kat-depo"), anlat=False).veri["deprem"]
    assert yakin(d2["kappa"], 0.5) and yakin(d2["sinir_oran"], 0.008 * 0.5 * 1.5)        # tek katlı çelik MÇ: %50 artırım
    assert any("4.9.1.5" in u for u in d2["uyarilar"])


def test_drift_alt_sinirsiz_ve_14TpA_sinirsiz():
    """md. 4.9.1.1: drift hesabında V_tE alt sınırı uygulanmaz → Δ, alt sınırlı kuvvetten küçük ölçeklenir."""
    d = yapi.bina_coz(hepsi_acik("betonarme-2kat-3x2", Ct=0.6, periyot="ampirik"), anlat=False).veri["deprem"]
    oran = d["X"]["V_drift"] / d["VtE"]
    assert d["X"]["alt_sinir_etkin"] and yakin(d["X"]["olcek_drift"], oran) and oran < 1


def test_catlamis_rijitlik_periyodu_uzatir():
    b = hepsi_acik("betonarme-3kat-3x3", periyot="rayleigh")
    b["analiz"]["catlamis_rijitlik"] = False
    v1 = yapi.bina_coz(b, anlat=False).veri
    t1 = v1["deprem"]["X"]["Tp_rayleigh"]
    assert any("4.5.8.1'e aykırı" in u for u in v1["ozet"]["uyarilar"])          # açıkça kapatılırsa çözülür ama uyarılır
    b["analiz"]["catlamis_rijitlik"] = True
    v = yapi.bina_coz(b, anlat=False).veri
    t2 = v["deprem"]["X"]["Tp_rayleigh"]
    assert math.sqrt(1 / 0.7) - 1e-6 <= t2 / t1 <= math.sqrt(1 / 0.35) + 1e-6
    assert v["ag"]["rijitlik_carpani"] == {"kolon": 0.7, "kiris": 0.35} and v["deprem"]["catlamis_rijitlik"]
    assert not any("4.5.8.1'e aykırı" in u for u in v["ozet"]["uyarilar"])


def test_catlamis_rijitlik_varsayilani():
    """TBDY 4.5.8.1: betonarme + deprem → varsayılan çatlamış; deprem kapalı ya da çelik → brüt (anahtar verilmezse)."""
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["analiz"].pop("catlamis_rijitlik")
    assert yapi._bina_oku(b).analiz["catlamis_rijitlik"] is True
    b["yuk_durumlari"]["E"]["acik"] = False
    b["deprem"]["etkin"] = False
    assert yapi._bina_oku(b).analiz["catlamis_rijitlik"] is False
    c = yapi.bina_sablon("celik-1kat-depo")
    c["analiz"].pop("catlamis_rijitlik", None)
    c["yuk_durumlari"]["E"]["acik"] = True
    assert yapi._bina_oku(c).analiz["catlamis_rijitlik"] is False
    for ad in ("betonarme-tek-aciklik", "betonarme-2kat-3x2", "betonarme-3kat-3x3", "betonarme-4kat-4x3"):
        assert yapi.bina_sablon(ad)["analiz"]["catlamis_rijitlik"] is True


def test_catlamis_yalniz_deprem_birlesimlerinde():
    """TBDY 4.5.8.3: G durumu (deprem dışı birleşimler) çatlamış ayarından bağımsız (brüt K); E durumu değişir; deprem
    birleşimleri G'yi çatlamış kesitli kopyadan (G~c) alır, 1.4G+1.6Q brüt G'den."""
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    r1 = yapi.bina_coz(b, anlat=False)
    b0 = copy.deepcopy(b)
    b0["analiz"]["catlamis_rijitlik"] = False
    r0 = yapi.bina_coz(b0, anlat=False)
    G1, G0 = r1.veri["durumlar"]["G"], r0.veri["durumlar"]["G"]
    for e1, e0 in zip(G1["elemanlar"], G0["elemanlar"]):
        assert all(abs(a - c) <= 1e-9 * max(1.0, abs(c)) for a, c in zip(e1["uc_kuvvetleri"], e0["uc_kuvvetleri"]))
    E1, E0 = r1.veri["durumlar"]["EX+"], r0.veri["durumlar"]["EX+"]
    assert max(abs(d1["uX"]) for d1 in E1["dugumler"]) > 1.3 * max(abs(d0["uX"]) for d0 in E0["dugumler"])
    p = r1.ic["paket"]
    assert "G~c" in p.durum and "G~c" not in r1.veri["durumlar"] and "G~c" not in r0.ic["paket"].durum
    ad = "G+Q+0.2S+EX++0.3EY++0.3EZ"
    assert r1.ic["kombinasyonlar"][ad] == {"G~c": 1.0, "Q~c": 1.0, "S~c": 0.2, "EX+": 1.0, "EY+": 0.3, "EZ": 0.3}
    assert r1.ic["kombinasyonlar"]["1.4G+1.6Q"] == {"G": 1.4, "Q": 1.6}
    k = next(k for k in r1.veri["kombinasyonlar"] if k["ad"] == ad)
    assert k["katsayilar"] == {"G": 1.0, "Q": 1.0, "S": 0.2, "EX+": 1.0, "EY+": 0.3, "EZ": 0.3} and k["catlamis"]
    # G~c'nin toplam düşey tepkisi aynı (denge), iç kuvvetleri farklı (rijitlik dağılımı)
    Gc = yapi.kombinasyon_kisa(r1.ic, "G~c")
    assert yakin(sum(t["FZ"] for t in Gc["tepkiler"]), sum(t["FZ"] for t in G1["tepkiler"]), 1e-8)
    assert any(abs(a["uc_kuvvetleri"][5] - c["uc_kuvvetleri"][5]) > 1e-3 for a, c in zip(Gc["elemanlar"], G1["elemanlar"]))
    # çelikte çarpan uygulanmaz (yalnız beton elemanlar)
    c = yapi.bina_sablon("celik-1kat-depo")
    c["yuk_durumlari"]["E"]["acik"] = True
    c["analiz"]["catlamis_rijitlik"] = True
    vc = yapi.bina_coz(c, anlat=False).veri
    assert all(e["rijitlik_carpani"] == 1.0 for e in vc["ag"]["elemanlar"])


def test_ruzgar_el_hesabi(uc_kat):
    v = uc_kat.veri
    w = v["ruzgar"]
    assert w["C"] == 1.2 and [q["q"] for q in w["q_h"]] == [0.5, 0.5, 0.8] and [q["z"] for q in w["q_h"]] == [3.2, 6.4, 9.6]
    beklenen_x = [1.2 * 0.5 * 8 * 3.2, 1.2 * 0.5 * 8 * 3.2, 1.2 * 0.8 * 8 * 1.6]       # C·q(z)·B·(h_i/2 + h_(i+1)/2)
    beklenen_y = [1.2 * 0.5 * 10 * 3.2, 1.2 * 0.5 * 10 * 3.2, 1.2 * 0.8 * 10 * 1.6]
    for k, fx, fy in zip(w["katlar"], beklenen_x, beklenen_y):
        assert yakin(k["F_x"], fx) and yakin(k["F_y"], fy) and yakin(k["cephe_x"], fx / (1.2 * k["q"]))
    for ad, bil, toplam in (("W+X", "FX", -sum(beklenen_x)), ("W-Y", "FY", sum(beklenen_y))):
        K = yapi.kombinasyon_kisa(uc_kat.ic, ad)
        assert yakin(sum(t[bil] for t in K["tepkiler"]), toplam, 1e-8)
    assert "TS 498:2021 md. 14" in w["kaynak"]


@pytest.mark.parametrize("bolge,rakim,Sk", [(3, 0, 0.75), (7, 850, 1.25), (9, 1200, 1.60 * 1.10), (5, 1600, 1.30 * 1.15), (1, 200, 0.75)])
def test_kar_cizelge3(bolge, rakim, Sk):
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["yuk_durumlari"]["S"].update({"acik": True, "bolge": bolge, "rakim": rakim, "mu": 0.8})
    v = yapi.bina_coz(b, anlat=False).veri
    k = v["kar"]
    assert yakin(k["Sk"], Sk, 1e-12) and yakin(k["s"], 0.8 * Sk, 1e-12)
    assert yakin(k["cati_alani"], 9.0 * 4.0) and yakin(k["S_toplam"], k["s"] * 36.0, 1e-9)
    assert yakin(v["yukler"]["toplam"]["S"], k["S_toplam"], 1e-9) and "Çizelge 3" in k["kaynak"]
    assert yakin(sum(t["FZ"] for t in v["durumlar"]["S"]["tepkiler"]), k["S_toplam"], 1e-4)


def test_EZ_duşey_deprem(uc_kat):
    v = uc_kat.veri
    kz = 2.0 / 3.0 * v["deprem"]["SDS"]
    assert yakin(v["deprem"]["EZ_katsayi"], kz)
    K = yapi.kombinasyon_kisa(uc_kat.ic, "EZ")
    assert yakin(sum(t["FZ"] for t in K["tepkiler"]), kz * v["yukler"]["toplam"]["G"], 1e-8)
    G = yapi.kombinasyon_kisa(uc_kat.ic, "G~c")         # EZ yalnız deprem birleşimlerinde: çatlamış kesitli G'nin katı
    for eg, ez in zip(G["elemanlar"], K["elemanlar"]):
        for a, b_ in zip(eg["uc_kuvvetleri"], ez["uc_kuvvetleri"]):
            assert abs(b_ - kz * a) <= 1e-7 * max(1.0, abs(a))


def test_kombinasyon_adlari_ve_sayilari(uc_kat):
    v = uc_kat.veri
    K = {k["ad"]: k for k in v["kombinasyonlar"]}
    k = K["G+Q+0.2S+EX++0.3EY++0.3EZ"]
    assert k["uygulandi"] and k["tur"] == "deprem" and k["katsayilar"] == {"G": 1.0, "Q": 1.0, "S": 0.2, "EX+": 1.0, "EY+": 0.3, "EZ": 0.3}
    assert "4.11" in k["kaynak"]
    k = K["0.9G+EX-+0.3EY+-0.3EZ"]
    assert k["katsayilar"] == {"G": 0.9, "EX-": 1.0, "EY+": 0.3, "EZ": -0.3} and "4.12" in k["kaynak"] and "H = 0" in K["0.9G+EX++0.3EY++-0.3EZ".replace("++-", "+-")]["not"]
    assert K["G+1.3Q+1.3W+X"]["katsayilar"] == {"G": 1.0, "Q": 1.3, "W+X": 1.3} and "6.5" in K["G+1.3Q+1.3W+X"]["kaynak"]
    assert K["0.9G+1.3W-Y"]["katsayilar"] == {"G": 0.9, "W-Y": 1.3}
    assert K["G+Q+0.2S-0.3EX-+EY++0.3EZ"]["katsayilar"] == {"G": 1.0, "Q": 1.0, "S": 0.2, "EX-": -0.3, "EY+": 1.0, "EZ": 0.3}
    assert K["G+Q+EY-"]["tur"] == "drift"
    uyg = [k for k in v["kombinasyonlar"] if k["uygulandi"]]
    assert sum(1 for k in uyg if k["tur"] == "deprem") == 64 and sum(1 for k in uyg if k["tur"] == "drift") == 4
    # rüzgârlı: 6.5 ve 6.6 (4 + 4) + kar–rüzgâr TS 498 md. 12.1 (a) S/2 + W ve (b) S + W/2 (4 + 4)
    assert sum(1 for k in uyg if "W" in "".join(k["katsayilar"])) == 16
    assert K["G+1.3Q+0.65S+1.3W+X"]["katsayilar"] == {"G": 1.0, "Q": 1.3, "S": 0.65, "W+X": 1.3} and "12.1" in K["G+1.3Q+0.65S+1.3W+X"]["kaynak"]
    assert K["G+1.3Q+1.3S+0.65W-Y"]["katsayilar"] == {"G": 1.0, "Q": 1.3, "S": 1.3, "W-Y": 0.65}
    assert K["1.4G+1.6Q+1.6S"]["katsayilar"] == {"G": 1.4, "Q": 1.6, "S": 1.6} and "6.3" in K["1.4G+1.6Q+1.6S"]["kaynak"]
    assert K["G+Q+S"]["tur"] == "servis" and K["G+Q+S"]["uygulandi"]
    n = len([k for k in uyg if k["tur"] != "drift"])
    assert n == 84 == v["ozet"]["kombinasyon_sayisi"] == v["zarf"]["kombinasyon_sayisi"] == len(v["zarf"]["kombinasyonlar"])
    assert v["ozet"]["drift_kombinasyon_sayisi"] == 4 and not any(a.startswith("G+Q+E") for a in v["zarf"]["kombinasyonlar"])
    assert len({k["ad"] for k in v["kombinasyonlar"]}) == len(v["kombinasyonlar"])      # adlar tekil
    for k in uyg:                                                                         # katsayı anahtarları durum adları
        assert set(k["katsayilar"]) <= set(v["durumlar"]), k["ad"]
        assert yapi._komb_adi(k["katsayilar"]) == k["ad"]


def test_kar_kombinasyonlari_ts500_toplam_tepki(uc_kat):
    """Kar açık ts500 kümesi: 1,4G + 1,6Q + 1,6S ve TS 498 md. 12.1 kar–rüzgâr birleşimleri doğrusal toplam (Σ FZ tepki)."""
    v = uc_kat.veri
    T = {d: sum(t["FZ"] for t in v["durumlar"][d]["tepkiler"]) for d in ("G", "Q", "S")}
    for ad, (g, q, s) in (("1.4G+1.6Q+1.6S", (1.4, 1.6, 1.6)), ("G+1.3Q+0.65S+1.3W+X", (1.0, 1.3, 0.65)),
                          ("G+1.3Q+1.3S+0.65W+Y", (1.0, 1.3, 1.3)), ("G+Q+S", (1.0, 1.0, 1.0))):
        K = yapi.kombinasyon_kisa(uc_kat.ic, ad)
        assert yakin(sum(t["FZ"] for t in K["tepkiler"]), g * T["G"] + q * T["Q"] + s * T["S"], 1e-4), ad   # S ince kayıt (5 basamak)
    assert yakin(T["S"], v["yukler"]["toplam"]["S"], 1e-4) and T["S"] > 0


def test_duvar_parapet_ve_kiris_oz_net():
    """Şablon: çatı kirişinde kat yüksekliğinde duvar yok, 1 m parapet (duvar_h); ara kat dış kirişinde h_kat − h_kiriş.
    Kiriş öz ağırlığı varsayılan A_net = b·(h − t_döşeme) (döşeme içindeki kısım döşemede sayıldı); 'brut' seçeneği b·h.
    İki durumda da korunum (toplam = kolon tabanı = temel)."""
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    B = yapi._bina_oku(b)
    cati = [k for k in B.kirisler if k["kat"] == 3 and k["duvar"]]
    ara = [k for k in B.kirisler if k["kat"] == 1 and k["duvar"]]
    assert cati and all(k["h_duvar"] == 1.0 and k["h_duvar_kaynak"].startswith("duvar_h") for k in cati)
    assert ara and all(yakin(k["h_duvar"], 3.2 - 0.55) for k in ara)
    assert len(cati) == len(ara) == 8                                   # yalnız dış kirişler
    Y = yapi._yukleri_hazirla(B)
    w = B.duvarlar["tugla19"]["deger"]
    r_cati = next(r for r in Y.kirisler if r["no"] == cati[0]["no"])
    assert yakin(r_cati["kN_m"]["duvar"], w * 1.0)
    # öz ağırlık: net (t = 0,15) ve brüt
    k1 = B.kiris_no[1]
    assert yakin(k1["A_oz"], 0.25 * (0.55 - 0.15)) and k1["t_doseme"] == 0.15
    assert yakin(next(r for r in Y.kirisler if r["no"] == 1)["kN_m"]["oz"], 25.0 * 0.25 * 0.40)
    bb = copy.deepcopy(b)
    bb["analiz"]["kiris_oz"] = "brut"
    vb = yapi.bina_coz(bb, anlat=False).veri
    vn = yapi.bina_coz(b, anlat=False).veri
    n_par = sum(1 for k in B.kirisler)
    fark = vb["akis"]["korunum"]["G"]["kiris_oz"] - vn["akis"]["korunum"]["G"]["kiris_oz"]
    assert yakin(fark, sum(25.0 * k["b"] * 0.15 * k["L"] for k in B.kirisler), 1e-9) and n_par == 36
    for v in (vb, vn):
        p = v["akis"]["korunum"]["G"]
        assert yakin(p["toplam"], p["kolon_taban"], 1e-6) and yakin(p["toplam"], p["temel"], 1e-6)
        assert yakin(p["toplam"], v["yukler"]["toplam"]["G"], 1e-9)
    # çelik profilde katalog ağırlığı (döşeme payı düşülmez)
    c = yapi._bina_oku(yapi.bina_sablon("celik-1kat-depo"))
    yapi._yukleri_hazirla(c)
    assert all(k["A_oz"] == k["A"] and k["t_doseme"] == 0.0 for k in c.kirisler)
    # duvar_h hatası
    bh = copy.deepcopy(b)
    bh["kirisler"][0]["duvar_h"] = 25
    with pytest.raises(mo.MatrisHatasi, match="duvar_h"):
        yapi._bina_oku(bh)
    bh["kirisler"][0]["duvar_h"] = 1.2
    assert yapi._bina_oku(bh).kiris_no[bh["kirisler"][0]["no"]]["h_duvar"] == 1.2
    bh["analiz"]["kiris_oz"] = "yarim"
    with pytest.raises(mo.MatrisHatasi, match="kiris_oz"):
        yapi._bina_oku(bh)


def test_kombinasyon_dengeleri_ve_zarf_kapsar(uc_kat):
    v, paket = uc_kat.veri, uc_kat.ic["paket"]
    assert all(o["denge_enb"] < 1e-6 for o in v["kombinasyon_ozet"].values())
    zarf = {z["no"]: z for z in v["zarf"]["elemanlar"]}
    for k in v["kombinasyonlar"]:
        if not k["uygulandi"] or k["tur"] == "drift":
            continue
        K = paket.kisa(paket.birlesim(uc_kat.ic["kombinasyonlar"][k["ad"]]))     # hesapta kullanılan katsayılar (G~c …)
        for e in K["elemanlar"]:
            z = zarf[e["no"]]
            for a in ("N", "M", "V", "My", "Vz", "T"):
                ust, alt = z[a + "_max"], z[a + "_min"]
                assert max(e[a]) <= ust + 1e-5 * max(1.0, abs(ust)) and min(e[a]) >= alt - 1e-5 * max(1.0, abs(alt)), (k["ad"], e["no"], a)


def test_deprem_kombinasyonu_superpozisyon_dogrudan_cozum():
    """G+Q+0.2S+EX++0.3EY++0.3EZ: durumların katsayılı toplamı = aynı katsayılarla birleştirilmiş yüklerin tek çözümü."""
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    B = yapi._bina_oku(b)
    Y = yapi._yukleri_hazirla(B)
    kutle = yapi._kat_kutleleri(B, Y, n=B.deprem["n"], kar_payi=0.3)
    dep = yapi._deprem_on(B, Y, kutle)
    ag, model = yapi._ag_olustur(B, Y, kutle)
    B.ag = ag
    durumlar, _, _ = yapi._yuk_durumlari(B, Y, ag, dep)
    kisa_m, _ = yapi._durumlari_coz(B, model, durumlar, ag)
    paket = yapi._Paket({ad: yapi._kisa_bina(k, ag) for ad, k in kisa_m.items()})
    yapi._deprem_son(B, ag, dep, paket, durumlar)
    kat = {"G": 1.0, "Q": 1.0, "S": 0.2, "EX+": 1.0, "EY+": 0.3, "EZ": 0.3}
    birlesik = yapi._yuk_kayit_birlesim(durumlar, kat)
    dogrudan = se.coz_coklu(model, {"D": {"yukler": birlesik["yukler"], "yayili": birlesik["yayili"]}})["D"]
    komb = paket.kisa(paket.birlesim(kat))
    for ek, ed in zip(komb["elemanlar"], dogrudan["elemanlar"]):
        for a, c_ in zip(ek["uc_kuvvetleri"], ed["uc_kuvvetleri"]):
            assert abs(a - c_) <= 1e-8 * max(1.0, abs(c_))
    for a, c_ in zip(komb["u"], dogrudan["u"]):
        assert abs(a - c_) <= 1e-12 + 1e-8 * abs(c_)


def test_yuk_durumlari_ac_kapa_tum_sablonlar():
    """Her şablon: S, W, E hepsi açık, hepsi kapalı ve tek tek açık çözülür; JSON geçerli (NaN/inf yok), dengeler sıfır."""
    for ad in SABLONLAR:
        for acik in ((), ("S",), ("W",), ("E",), ("S", "W", "E")):
            b = yapi.bina_sablon(ad)
            for d in ("S", "W", "E"):
                b["yuk_durumlari"][d]["acik"] = d in acik
            b["deprem"]["etkin"] = "E" in acik
            v = yapi.bina_coz(b, anlat=False).veri
            json.loads(json.dumps(v, ensure_ascii=False), parse_constant=lambda c: pytest.fail(f"{ad} {acik}: {c}"))
            assert ("EX+" in v["durumlar"]) == ("E" in acik) and (v["deprem"] is not None) == ("E" in acik)
            assert ("W+X" in v["durumlar"]) == ("W" in acik) and (v["ruzgar"] is not None) == ("W" in acik)
            assert ("S" in v["durumlar"]) == ("S" in acik) and (v["kar"] is not None) == ("S" in acik)
            assert (len(v["ag"]["diyaframlar"]) > 0) == ("E" in acik)
            for k in v["durumlar"].values():
                assert all(abs(x) < 1e-6 for x in k["denge"].values())


def test_anlatim_deprem_bolumleri():
    r = yapi.bina_coz(hepsi_acik("betonarme-3kat-3x3", SS_DD3=0.4, S1_DD3=0.12), goster="yok")
    metin = "\n".join(str(i) for _, i, _ in r.anlatim.bloklar)
    for parca in ("load pattern", "Tablo 2.1", "Rayleigh", "T_pA", "V_tE", "M_b,x", "efendi", "η_bi", "θ_II", "Tablo 4.4",
                  "programları bir kombinasyonu yeniden", "G+Q+0.2S+EX++0.3EY++0.3EZ", "(2/3)·S_DS", "λ = S_ae"):
        assert parca in metin, parca
    semalar = [i for t, i, _ in r.anlatim.bloklar if t == "sema"]
    basliklar = " ".join(k["baslik"] for s in semalar for k in s["kareler"])
    assert "Tasarım spektrumu" in basliklar and "Kat deprem kuvvetleri" in basliklar
    assert "aynı plan" in basliklar                          # aynı planlı katlar tek şema
    # Python betiği deprem kat kuvvetlerini de hesaplar ve motorla aynı
    d = r.veri["deprem"]
    satir = next(s for s in r.python_ciktisi.splitlines() if s.startswith("Kat kuvvetleri F_iE"))
    degerler = [float(x) for x in satir.split(":")[1].split("(")[0].replace(" ", "").split(",")]
    assert all(abs(a - k["F_x"]) < 0.006 for a, k in zip(degerler, d["katlar"]))
    assert f"V_tE = max(" in r.python_ciktisi and "[Hata" not in r.python_ciktisi


def test_veri_deprem_sozlesmesi(uc_kat):
    """Arayüzün (docs/bina.js) okuduğu alan adları."""
    d = uc_kat.veri["deprem"]
    for a in ("FS", "F1", "SDS", "SD1", "TA", "TB", "TL", "DTS", "BYS", "I", "R", "D", "n", "HN", "TpA", "Tp", "Tp_yontem", "Sae_Tp", "Ra",
              "SaR", "VtE", "VtE_min", "dFN", "m_t", "W_t", "SDS_DD3", "SD1_DD3", "lambda", "kappa", "theta_sinir", "kaynaklar", "katlar",
              "spektrum", "uyarilar", "uygulanabilir"):
        assert a in d, a
    for a in ("SS", "SDS", "SD1", "TA", "DTS", "R", "TpA", "SaR", "VtE", "dFN", "oran", "theta"):
        assert isinstance(d["kaynaklar"][a], str) and ("TBDY" in d["kaynaklar"][a] or "AFAD" in d["kaynaklar"][a]), a
    for k in d["katlar"]:
        for a in ("kat", "H", "h", "w_i", "m_i", "F_x", "F_y", "V_x", "V_y", "d_x", "d_y", "delta_x", "delta_y", "oran_x", "oran_y",
                  "sinir", "eta_bx", "eta_by", "theta_x", "theta_y", "uygun"):
            assert a in k, a
        assert k["delta_x"] < 0.05 and k["oran_x"] < 0.05           # metre ve boyutsuz
    T = [p[0] for p in d["spektrum"]]
    assert T == sorted(T) and all(len(p) == 3 for p in d["spektrum"]) and d["Tp"] in T
    assert d["DTS"] == "1" and d["BYS"] == 7 and d["uygulanabilir"] is True        # H_N = 9,6 m: 7 < H_N ≤ 10,5 (Tablo 3.3)
    v = uc_kat.veri
    assert [k["kat"] for k in v["kutle_merkezi"]] == [1, 2, 3] and {"X", "Y"} <= set(v["kutle_merkezi"][0])
    assert {"C", "q_h", "katlar", "kaynak"} <= set(v["ruzgar"]) and {"kat", "z", "q"} == set(v["ruzgar"]["q_h"][0])
    assert {"kat", "cephe_x", "cephe_y", "F_x", "F_y"} <= set(v["ruzgar"]["katlar"][0])
    assert {"bolge", "rakim", "Sk", "mu", "s", "cati_alani", "S_toplam", "kaynak"} <= set(v["kar"])
    assert v["cozum_kimligi"] == uc_kat.ic["kimlik"]


def test_deprem_onizleme_cozumle_tutarli(uc_kat):
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["yuk_durumlari"]["E"]["acik"] = False             # önizleme deprem kapalıyken de çalışır
    on = yapi.deprem_onizleme(b)
    d = uc_kat.veri["deprem"]
    assert on["tahmin"] is True and "spektrum" in on
    for a in ("SDS", "SD1", "TpA", "Tp", "VtE", "dFN", "m_t", "W_t", "DTS", "BYS"):
        assert on[a] == d[a] or yakin(on[a], d[a], 1e-8), a
    for k0, k1 in zip(on["katlar"], d["katlar"]):
        assert yakin(k0["F_x"], k1["F_x"], 1e-8) and yakin(k0["V_x"], k1["V_x"], 1e-8) and yakin(k0["Mb_x"], k1["Mb_x"], 1e-8)
    with pytest.raises(mo.MatrisHatasi, match="deprem"):
        b2 = yapi.bina_sablon("betonarme-tek-aciklik")
        b2.pop("deprem")
        yapi.deprem_onizleme(b2)


def test_I_BKS_den_ve_tasiyici_takma_ad():
    b = hepsi_acik("betonarme-2kat-3x2", BKS=2)
    b["deprem"].pop("I", None)
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert d["I"] == 1.2
    b = hepsi_acik("betonarme-2kat-3x2", BKS=1, I=1.0)
    r = yapi.bina_coz(b, anlat=False)
    assert any("Tablo 3.1" in u for u in r.veri["ozet"]["uyarilar"])
    b = hepsi_acik("celik-1kat-depo", tasiyici="celik-mcm-yuksek")       # eski ad = C11
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert d["tasiyici"] == "celik-cerceve-yuksek" and d["tasiyici_kod"] == "C11" and d["R"] == 8
    b = hepsi_acik("betonarme-2kat-3x2", tasiyici="betonarme-perde-bosluksuz")
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert (d["R"], d["D"], d["Ct"]) == (6, 2.5, 0.07)


def test_deprem_ogretici_hatalar():
    for alan, deger, desen in (("zemin_sinifi", "ZX", "ZA, ZB, ZC"), ("zemin_sinifi", "ZF", "sahaya özel"), ("SS", 0, "pozitif"),
                               ("SS", -0.5, "pozitif"), ("S1", 0, "pozitif"), ("tasiyici", "yok-sistem", "Tablo 4.1"),
                               ("BKS", 4, "Tablo 3.1"), ("dolgu", "tas", "0,008κ"), ("periyot", "modal", "ampirik"), ("n", 1.5, "Tablo 4.3"),
                               ("SS", 5.0, "g cinsinden"), ("diyafram", "yarı", "rijit")):
        b = hepsi_acik("betonarme-tek-aciklik", **{alan: deger})
        with pytest.raises(mo.MatrisHatasi, match=desen):
            yapi.bina_coz(b, anlat=False)
    b = hepsi_acik("betonarme-tek-aciklik", SS_DD3=0.4)
    with pytest.raises(mo.MatrisHatasi, match="birlikte"):
        yapi.bina_coz(b, anlat=False)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["yuk_durumlari"]["E"]["acik"] = True
    b.pop("deprem")
    with pytest.raises(mo.MatrisHatasi, match="deprem' kartı yok"):
        yapi.bina_coz(b, anlat=False)
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["yuk_durumlari"]["S"].update({"acik": True, "bolge": 12})
    with pytest.raises(mo.MatrisHatasi, match="1…9"):
        yapi.bina_coz(b, anlat=False)


def test_kombinasyon_kisa_serbest_katsayilar(uc_kat):
    ic = uc_kat.ic
    a = yapi.kombinasyon_kisa(ic, "benim", {"G": 1.0, "EX+": 0.5})
    g, e = yapi.kombinasyon_kisa(ic, "G"), yapi.kombinasyon_kisa(ic, "EX+")
    for ea, eg, ee in zip(a["elemanlar"], g["elemanlar"], e["elemanlar"]):
        for x, y, z in zip(ea["M"], eg["M"], ee["M"]):
            assert abs(x - (y + 0.5 * z)) <= 1e-5 * max(1.0, abs(y), abs(z))      # diyagram dizileri 6 anlamlı basamak
    with pytest.raises(mo.MatrisHatasi, match="yük durumu bu çözümde yok"):
        yapi.kombinasyon_kisa(ic, "x", {"T": 1.0})
    with pytest.raises(mo.MatrisHatasi, match="bulunamadı"):
        yapi.kombinasyon_kisa(ic, "yok")
    with pytest.raises(mo.MatrisHatasi, match="Önce bina çözülmeli"):
        yapi.kombinasyon_kisa(None, "G")
    assert yapi._cozum_kimligi(yapi._bina_oku(yapi.bina_sablon("betonarme-3kat-3x3"))) == ic["kimlik"]


def test_buyuk_modelde_sonuclar_tembel():
    """4 katlı şablon S, W, E açık: yanıt bütçesi aşılacağından varsayılan tam kombinasyon da tembel (sonuclar boş)."""
    v = yapi.bina_coz(hepsi_acik("betonarme-4kat-4x3"), anlat=False).veri
    assert v["sonuclar"] == {} and v["ozet"]["sonuclar_tembel"] is True and v["gosterilecek"] == []
    b = hepsi_acik("betonarme-4kat-4x3")
    b["analiz"]["gosterilecek"] = ["1.4G+1.6Q"]                  # kullanıcı isterse yazılır
    assert set(yapi.bina_coz(b, anlat=False).veri["sonuclar"]) == {"1.4G+1.6Q"}


def test_kutuphane_tasiyici_sistemler():
    k = yapi.kutuphane()
    ts = k["tasiyici_sistemler"]
    assert [t["ad"] for t in ts] == list(yv.TBDY_TASIYICI_ARAYUZ)
    for t in ts:
        assert {"ad", "etiket", "R", "D", "BYS_izin", "kaynak"} <= set(t) and "Tablo 4.1" in t["kaynak"]
    a11 = ts[0]
    assert a11["etiket"].startswith("A11") and a11["BYS_izin"] == "≥ 3" and (a11["R"], a11["D"]) == (8, 3)
    assert next(t for t in ts if t["kod"] == "C16")["BYS_izin"] == "–"


def test_sayi_bicimi_tam_sayi_sifirlari_korunur():
    assert yapi._f(30, 0) == "30" and yapi._f(300, 0) == "300" and yapi._f(30.0) == "30" and yapi._f(2.50) == "2.5"
    assert yapi._f(0.0, 0) == "0" and yapi._f(-0.001) == "0" and yapi._f(1.234, 1) == "1.2" and yapi._f(-40, 0) == "-40"
    r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"), goster="yok")
    metin = "\n".join(str(i) for t, i, _ in r.anlatim.bloklar if t == "md")
    assert "40 × 40 cm" in metin and "25 × 50 cm" in metin and "40 × 40 |" in metin
