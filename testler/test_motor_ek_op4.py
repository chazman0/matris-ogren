"""İlk sürüm motor ekleri (op4 Yönetmelik sihirbazı §12 kararları): sahaya özel spektrum (TBDY 2018 md. 2.4), hareketli yük
azaltması (TS 498:2021 md. 16 Çizelge 7) ve karma yapı (malzemeye göre kombinasyon kümesi, TBDY md. 4.3.4.2 doğrultu
sistemleri, yükseklik boyunca bölge sistemleri). Sayılar el hesabıyla (yorum satırları) denetlenir; anahtarlar verilmeyen
modellerin sonuçları değişmez (bütün şablonlar için ayrıca derlem testleri koşar)."""
from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest

import yapi
import yapi_serbest
import yapi_veri as yv
from matris_ogren import MatrisHatasi

PROJE = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# yardımcılar
# ---------------------------------------------------------------------------
def _tek_aciklik(nkat, q=2.0, kullanim="konut", azaltma=False):
    """5 × 5 m tek açıklıklı, nkat katlı betonarme çerçeve: her katta tek döşeme (konut q = 2 kN/m²), 4 kolon, 4 kiriş."""
    akslar = {"x": [{"ad": "A", "konum": 0.0}, {"ad": "B", "konum": 5.0}], "y": [{"ad": "1", "konum": 0.0}, {"ad": "2", "konum": 5.0}]}
    katlar = [{"no": 0, "ad": "Temel", "kot": 0.0}] + [{"no": k, "kot": 3.0 * k} for k in range(1, nkat + 1)]
    kolonlar, kirisler, dosemeler = [], [], []
    for k in range(1, nkat + 1):
        for ax in ("A", "B"):
            for ay in ("1", "2"):
                kolonlar.append({"no": len(kolonlar) + 1, "aks": [ax, ay], "kat": k, "kesit": "S50x50"})
        for bas, son in ((["A", "1"], ["B", "1"]), (["A", "2"], ["B", "2"]), (["A", "1"], ["A", "2"]), (["B", "1"], ["B", "2"])):
            kirisler.append({"no": len(kirisler) + 1, "kat": k, "bas": bas, "son": son, "kesit": "K30x60"})
        dosemeler.append({"no": k, "kat": k, "kose": [["A", "1"], ["B", "2"]], "h": 0.14, "kullanim": kullanim, "q": q, "g_ek": 1.5})
    return {"tur": "bina", "surum": 1, "baslik": f"{nkat} katlı tek açıklık", "sistem": "betonarme", "akslar": akslar, "katlar": katlar,
            "malzemeler": {"C30": {"kutuphane": "C30/37"}},
            "kesitler": {"S50x50": {"tip": "dikdortgen", "b": 0.5, "h": 0.5, "malzeme": "C30"},
                         "K30x60": {"tip": "dikdortgen", "b": 0.3, "h": 0.6, "malzeme": "C30"}},
            "kolonlar": kolonlar, "kirisler": kirisler, "dosemeler": dosemeler,
            "yuk_durumlari": {"G": {"acik": True}, "Q": {"acik": True, "azaltma": azaltma}}}


def _kolon_kaydi(veri, no):
    return next(k for k in veri["tasarim"]["elemanlar"] if k["tur"] == "kolon" and k["no"] == no)


def _karma_bina():
    """4 katlı betonarme şablon, 4. kat (çatı katı) çelik: HEB 300 kolonlar, IPE 360 kirişler; deprem açık."""
    b = yapi.bina_sablon("betonarme-4kat-4x3")
    b["malzemeler"]["S275"] = {"kutuphane": "S275"}
    b["kesitler"]["HEB300"] = {"tip": "profil", "profil": "HEB 300", "malzeme": "S275"}
    b["kesitler"]["IPE360"] = {"tip": "profil", "profil": "IPE 360", "malzeme": "S275"}
    for c in b["kolonlar"]:
        if c["kat"] == 4:
            c["kesit"] = "HEB300"
    for k in b["kirisler"]:
        if k["kat"] == 4:
            k["kesit"] = "IPE360"
    b["yuk_durumlari"]["E"] = {"acik": True}
    b["deprem"]["etkin"] = True
    return b


@pytest.fixture(scope="module")
def kopru():
    ozellik = importlib.util.spec_from_file_location("web_kopru_motor_ek_testi", PROJE / "docs" / "web_kopru.py")
    modul = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(modul)
    return modul


def iste(kopru, islem, girdi=None):
    return json.loads(kopru.calistir(json.dumps({"islem": islem, "girdi": girdi or {}})))


# ===========================================================================
# 1. Sahaya özel spektrum (TBDY 2018 md. 2.4)
# ===========================================================================
def test_tablo_ara_degeri_ve_tablo_disi():
    f = yapi._tablo_fonk([(0.0, 0.4), (0.2, 1.0), (1.0, 0.5)])
    assert f(0.0) == pytest.approx(0.4)
    assert f(0.1) == pytest.approx(0.7)            # 0,4 + (0,1/0,2)·(1,0 − 0,4) = 0,7
    assert f(0.6) == pytest.approx(0.75)           # 1,0 + (0,4/0,8)·(0,5 − 1,0) = 0,75
    assert f(1.0) == pytest.approx(0.5)
    assert f(2.0) == pytest.approx(0.25)           # tablo dışı: 0,5·1,0/2,0 (sabit hız kolu, motor kuralı)


def test_standart_kopyasi_asgariyi_saglar():
    # ZC, S_S = 1,0, S_1 = 0,3: F_S = 1,2, F_1 = 1,5 → S_DS = 1,2, S_D1 = 0,45, T_A = 0,075, T_B = 0,375 s.
    # Köşe noktalarında standarda eşit tablo: 1/T kolu dışbükey olduğundan kirişler eğrinin üstünde → oran ≥ 1.
    nok = [(0.0, 0.48), (0.075, 1.2), (0.375, 1.2), (1.0, 0.45), (2.0, 0.225), (6.0, 0.075)]
    sp = yapi._spektrum_ozel(nok, 1.0, 0.3, "ZC")
    a = sp["asgari"]
    assert a["saglandi"] and a["araliklar"] == [] and a["en_kucuk_oran"] == pytest.approx(1.0, abs=1e-9)
    assert sp["FS"] == pytest.approx(1.2) and sp["F1"] == pytest.approx(1.5)
    assert sp["SDS"] == pytest.approx(1.2)
    # S_D1 = max_{1 ≤ T ≤ 6} T·S_ae: seyrek tabloda kiriş 1/T eğrisinin üstünde kalır (güvenli taraf). [2; 6] aralığında
    # S_ae = 0,225 − 0,0375(T − 2) → T·S_ae = T(0,3 − 0,0375T), en büyüğü T = 4 s'de 4·0,15 = 0,60 ([1; 2]'de en çok 0,506).
    assert sp["SD1"] == pytest.approx(0.60)


def test_yuzde_doksan_tabani_uygulanir():
    # Standardın 0,8 katı tablo → md. 2.4.1.2 sağlanmaz; tasarımda 0,90·standart kullanılır.
    std = yapi._spektrum(1.0, 0.3, "ZC")
    Ts = [0.0, 0.075, 0.375, 1.0, 2.0, 4.0]
    sp = yapi._spektrum_ozel([(T, 0.8 * std["Sae"](T)) for T in Ts], 1.0, 0.3, "ZC")
    assert not sp["asgari"]["saglandi"]
    assert sp["asgari"]["en_kucuk_oran"] == pytest.approx(0.8, abs=0.02)
    assert sp["Sae"](0.2) == pytest.approx(1.08)        # max(0,96, 0,9·1,2 = 1,08)
    assert sp["ham"](0.2) == pytest.approx(0.96)        # 0,8·1,2
    assert sp["SDS"] == pytest.approx(1.08)             # türetilen S_DS = tasarım spektrumunun tepesi = 0,9·1,2


def test_SDS_SD1_turetme_el_hesabi():
    # Tablo: [0; 0,4], [0,2; 1,0], [0,8; 1,0], [1,0; 0,7], [3,0; 0,2] — ZC, S_S = 1,0, S_1 = 0,3 tabanı.
    # Plato: tablo 1,0 < 0,9·1,2 = 1,08 → S_DS = 1,08 (taban). 1 ≤ T ≤ 3: S_ae = 0,7 − 0,25(T − 1), T·S_ae = T(0,95 − 0,25T);
    # türev 0,95 − 0,5T = 0 → T = 1,9 s → S_D1 = 1,9·0,475 = 0,9025 (0,01 s ızgarasında tam). T_B = 0,9025/1,08 = 0,8356 s.
    sp = yapi._spektrum_ozel([(0.0, 0.4), (0.2, 1.0), (0.8, 1.0), (1.0, 0.7), (3.0, 0.2)], 1.0, 0.3, "ZC")
    assert sp["SDS"] == pytest.approx(1.08)
    assert sp["SD1"] == pytest.approx(0.9025)
    assert sp["TB"] == pytest.approx(0.9025 / 1.08)
    assert sp["TA"] == pytest.approx(0.2 * 0.9025 / 1.08)
    # raporda verilen S_DS / S_D1 öncelikli (yine %90 tabanı)
    sp2 = yapi._spektrum_ozel([(0.0, 0.4), (0.2, 1.0), (0.8, 1.0), (1.0, 0.7), (3.0, 0.2)], 1.0, 0.3, "ZC", SDS_g=1.25, SD1_g=0.30)
    assert sp2["SDS"] == pytest.approx(1.25) and sp2["SD1"] == pytest.approx(0.405)   # 0,30 < 0,9·0,45 → 0,405
    assert sp2["notlar"]


def test_tablo_dogrulama_hatalari():
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    for noktalar, desen in (([[0.1, 0.5], [1.0, 0.4]], "T = 0"), ([[0, 0.5], [0.5, 0.4]], "T = 1 s"),
                            ([[0, 0.5], [0.4, 0.8], [0.3, 0.6], [1.0, 0.4]], "artan"), ([[0, 9.0], [1.0, 0.4]], "g cinsinden"),
                            ([[0, 0.5]], "en az iki")):
        b2 = copy.deepcopy(b)
        b2["deprem"]["ozel_spektrum"] = {"noktalar": noktalar, "kaynak": "deneme"}
        with pytest.raises(MatrisHatasi, match=desen):
            yapi.bina_coz(b2, anlat=False)


def test_ZF_ozel_spektrumla_cozulur():
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["deprem"]["zemin_sinifi"] = "ZF"
    with pytest.raises(MatrisHatasi, match="sahaya özel"):
        yapi.bina_coz(b, anlat=False)
    b["deprem"]["ozel_spektrum"] = {"noktalar": [[0, 0.6], [0.15, 1.5], [0.8, 1.5], [1.0, 1.2], [4.0, 0.3]],
                                    "kaynak": "Sahaya özel zemin davranış analizi (deneme)", "SDS": 1.5, "SD1": 1.2}
    r = yapi.bina_coz(b, anlat=True)
    d = r.veri["deprem"]
    assert d["zemin_sinifi"] == "ZF" and d["FS"] is None and d["F1"] is None
    assert d["SDS"] == pytest.approx(1.5) and d["SD1"] == pytest.approx(1.2)
    assert d["TB"] == pytest.approx(0.8)                       # 1,2/1,5
    oz = d["ozel_spektrum"]
    assert oz["taban_zemin"] == "ZE" and oz["SDS_kaynak"].startswith("kullanıcı")
    assert any("ZF" in u and "ZE" in u for u in d["uyarilar"])      # motor kuralı uyarısı (doğrulanmadı)
    assert any("λ = 1" in u for u in d["uyarilar"])               # ZF'de DD-3 tablosu yok
    assert d["lambda"] == 1.0
    assert "sahaya özel" in r.python_kodu and r.veri["ozet"]["en_buyuk_dc"] > 0


def test_ozel_spektrum_taban_kesmeyi_belirler():
    # Standardın yarısı kadar tablo: her T'de 0,9·standart taban yönetir → V_tE = 0,9·V_tE(standart) (ampirik T_p aynı).
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    std = yapi._spektrum(1.0, 0.3, "ZC")
    Ts = sorted({round(0.05 * i, 4) for i in range(0, 81)} | {std["TA"], std["TB"]})
    b2 = copy.deepcopy(b)
    b2["deprem"]["ozel_spektrum"] = {"noktalar": [[T, 0.5 * std["Sae"](T)] for T in Ts], "kaynak": "deneme"}
    r0, r2 = yapi.bina_coz(b, anlat=False), yapi.bina_coz(b2, anlat=False)
    assert r2.veri["deprem"]["Tp"] == pytest.approx(r0.veri["deprem"]["Tp"])
    assert r2.veri["deprem"]["VtE"] == pytest.approx(0.9 * r0.veri["deprem"]["VtE"], rel=1e-9)
    assert not r2.veri["deprem"]["ozel_spektrum"]["asgari"]["saglandi"]


def test_anahtarsiz_model_ozel_alan_yok():
    r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"), anlat=False)
    assert "ozel_spektrum" not in r.veri["deprem"] and "karma" not in r.veri["deprem"]
    assert "hareketli_azaltma" not in r.veri and "kombinasyon_kumeleri" not in r.veri["tasarim"]


# ===========================================================================
# 2. Hareketli yük azaltması (TS 498:2021 md. 16 Çizelge 7)
# ===========================================================================
@pytest.mark.parametrize("nkat, beta", [(1, 1.0), (3, 1.0), (6, 0.80), (10, 0.60)])
def test_azaltma_katsayisi_kat_sayisina_gore(nkat, beta):
    # Çizelge 7 (a: konut): üç kata kadar azaltma yok; 6 kat β = (3 + 0,8 + 0,6 + 0,4)/6 = 0,80; 10 katta %40 sınırı → 0,60.
    assert yv.azaltma_beta("a", nkat) == pytest.approx(beta)
    r = yapi.bina_coz(_tek_aciklik(nkat, azaltma=True), anlat=False)
    az = r.veri["hareketli_azaltma"]
    zemin = [e for e in az["elemanlar"] if e["kat"] == 1]
    assert len(zemin) == 4 and all(e["n"] == nkat and e["beta"] == pytest.approx(beta) for e in zemin)
    tepe = [e for e in az["elemanlar"] if e["kat"] == nkat]
    assert all(e["n"] == 1 and e["beta"] == 1.0 for e in tepe)
    assert az["temel"]["beta"] == pytest.approx(beta)


def test_azaltma_kolon_kuvveti_el_hesabi():
    # 10 kat, 5 × 5 m döşeme, q = 2 kN/m²: kat başına Q = 50 kN, simetri → her kolona 12,5 kN/kat; zemin kat kolonunda
    # N_Q = 10·12,5 = 125 kN. 1,4G + 1,6Q'da fark = 1,6·(1 − 0,60)·125 = 80 kN.
    r0 = yapi.bina_coz(_tek_aciklik(10), anlat=False)
    r1 = yapi.bina_coz(_tek_aciklik(10, azaltma=True), anlat=False)
    k0, k1 = _kolon_kaydi(r0.veri, 1), _kolon_kaydi(r1.veri, 1)
    assert k1["ozet"]["beta_Q"] == pytest.approx(0.6)
    NQ = next(k for k in r0.veri["akis"]["kolonlar"] if k["no"] == 1)["N_kum_Q"]
    assert NQ == pytest.approx(125.0, rel=1e-6)
    assert k0["ozet"]["N_max_kN"] - k1["ozet"]["N_max_kN"] == pytest.approx(1.6 * 0.4 * 125.0, rel=1e-4)
    # tekil temel: N_servis = N_G + β·N_Q + temel öz ağırlığı
    t0 = next(t for t in r0.veri["akis"]["temeller"] if t["kolon_no"] == 1)
    t1 = next(t for t in r1.veri["akis"]["temeller"] if t["kolon_no"] == 1)
    assert t1["beta_Q"] == pytest.approx(0.6) and "beta_Q" not in t0
    assert t0["N_servis"] - t1["N_servis"] == pytest.approx(0.4 * t0["N_Q"], rel=1e-9)
    # kirişlerde azaltma yok
    kir0 = {k["no"]: k["dc"] for k in r0.veri["tasarim"]["elemanlar"] if k["tur"] == "kiris"}
    kir1 = {k["no"]: k["dc"] for k in r1.veri["tasarim"]["elemanlar"] if k["tur"] == "kiris"}
    assert kir0 == kir1


def test_azaltma_gruplari_ve_farkli_kat_yukleri():
    # b grubu (mağaza) 6 kat: β = 0,90; depo: azaltma yok (β = 1).
    assert yv.azaltma_beta_katlar("b", [5.0] * 6)[0] == pytest.approx(0.90)
    assert yv.azaltma_beta_katlar("yok", [5.0] * 10)[0] == 1.0
    # Farklı kat yükleri (Çizelge 7 eşit yük içindir): en ağır kattan başlayan kat payları 1, 1, 1, 0,8, 0,6, 0,4:
    # yükler [3,5; 2; 2; 2; 2; 2] → (3,5 + 2 + 2 + 1,6 + 1,2 + 0,8)/13,5 = 11,1/13,5 = 0,8222 > β(6) = 0,80 (güvenli taraf).
    beta, ayr = yv.azaltma_beta_katlar("a", [2.0, 2.0, 3.5, 2.0, 2.0, 2.0])
    assert beta == pytest.approx(11.1 / 13.5) and ayr["beta_tablo"] == pytest.approx(0.8) and not ayr["esit"]


def test_azaltma_deprem_birlesiminde_uygulanmaz():
    b = yapi.bina_sablon("betonarme-4kat-4x3")
    b["yuk_durumlari"]["E"] = {"acik": True}
    b["deprem"]["etkin"] = True
    b2 = copy.deepcopy(b)
    b2["yuk_durumlari"]["Q"] = {"acik": True, "azaltma": True}
    r0, r2 = yapi.bina_coz(b, anlat=False), yapi.bina_coz(b2, anlat=False)
    T0, T2 = r0.ic["tasarim"], r2.ic["tasarim"]
    fe = next(c for c in r2.ic["alan"]["B"].kolonlar if c["kat"] == 1)["eleman"]
    assert T2.beta_q[fe] == pytest.approx(0.95)                      # 4 kat: β = 0,95
    b0, bl = yapi._blok(T0, fe), yapi._blok(T2, fe)
    for i, k in enumerate(T2.kombs):
        if k["tur"] == "deprem":
            assert (abs(bl[i] - b0[i]) < 1e-9).all()
    i = T2.adlar.index("1.4G+1.6Q")
    assert not (abs(bl[i] - b0[i]) < 1e-9).all()
    assert any("azaltma" in u.lower() for u in r2.veri["ozet"]["uyarilar"])


def test_azaltma_genel_modelde():
    a = yapi.bina_sablon("betonarme-4kat-4x3")
    a["surum"] = 3
    a["yuk_durumlari"]["Q"] = {"acik": True, "azaltma": True}
    r = yapi.bina_coz(a, anlat=False)
    az = r.veri["hareketli_azaltma"]
    assert sorted({(e["kat"], e["n"], e["beta"]) for e in az["elemanlar"]}) == [(1, 4, 0.95), (2, 3, 1.0), (3, 2, 1.0), (4, 1, 1.0)]
    assert {k["ozet"].get("beta_Q") for k in r.veri["tasarim"]["elemanlar"] if k["tur"] == "kolon"} == {0.95, 1.0}


# ===========================================================================
# 3. Karma yapı
# ===========================================================================
def test_malzemeye_gore_kombinasyon_kumesi():
    """Betonarme (4 kat) + çelik çatı katı: çelik elemanlar ÇYTHYE YDKT, betonarme TS 500 birleşimleriyle; aynı yük
    durumlarından. Çelik eleman kaydı tüm binanın cythye_ydkt ile çözümündekine, betonarme kaydı ts500 çözümündekine eşittir."""
    b = _karma_bina()
    bk = copy.deepcopy(b)
    bk["kombinasyon_kumeleri"] = {"betonarme": "ts500", "celik": "cythye_ydkt"}
    bc = copy.deepcopy(b)
    bc["kombinasyon_kumesi"] = "cythye_ydkt"
    rk, rb, rc = (yapi.bina_coz(x, anlat=False) for x in (bk, b, bc))
    kay = lambda r: {(k["tur"], k["no"]): k for k in r.veri["tasarim"]["elemanlar"]}   # noqa: E731
    K, Bb, C = kay(rk), kay(rb), kay(rc)
    celik = [a for a, k in K.items() if k["sistem"] == "celik"]
    beton = [a for a, k in K.items() if k["sistem"] == "betonarme"]
    assert celik and beton
    for a in celik:
        assert K[a]["dc"] == C[a]["dc"] and K[a]["belirleyen"] == C[a]["belirleyen"]
        assert not K[a]["belirleyen"]["kombinasyon"].startswith("G+Q+E")        # deprem satırında 1,2G (TBDY 9.2.5.1)
    for a in beton:
        assert K[a]["dc"] == Bb[a]["dc"] and K[a]["belirleyen"] == Bb[a]["belirleyen"]
    kk = rk.veri["tasarim"]["kombinasyon_kumeleri"]
    assert kk["betonarme"]["kume"] == "ts500" and kk["celik"]["kume"] == "cythye_ydkt"
    assert rk.veri["kombinasyon_kumeleri"] == {"betonarme": "ts500", "celik": "cythye_ydkt"}
    # tek eleman ayrıntısı da aynı kümeyle (köprü bina_eleman_tasarim yolu)
    tur, no = celik[0]
    assert yapi.eleman_tasarim(rk.ic, tur, no).veri["dc"] == K[celik[0]]["dc"]
    # çelik elemanı belirleyen ÇYTHYE birleşimi tembel kombinasyonla da kurulur (köprü bina_kombinasyon)
    ad = K[celik[0]]["belirleyen"]["kombinasyon"]
    assert ad not in {k["ad"] for k in rk.veri["kombinasyonlar"]} and yapi.kombinasyon_kisa(rk.ic, ad)["elemanlar"]


def test_kume_haritasi_hatalari():
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    for kk, desen in (({"ahsap": "ts500"}, "betonarme' ya da 'celik"), ({"celik": "yok"}, "tanımsız"), ("ts500", "sözlük")):
        b2 = copy.deepcopy(b)
        b2["kombinasyon_kumeleri"] = kk
        with pytest.raises(MatrisHatasi, match=desen):
            yapi.bina_coz(b2, anlat=False)
    b2 = copy.deepcopy(b)
    b2["kombinasyon_kumeleri"] = {"celik": "ts500"}
    r = yapi.bina_coz(b2, anlat=False)
    assert any("kombinasyon_kumeleri.celik = ts500" in u for u in r.veri["ozet"]["uyarilar"])


def test_dogrultuya_gore_R_D():
    # X: A11 (R = 8, D = 3), Y: A13 (R = 6, D = 2,5); ampirik T_p iki yönde aynı ve > T_B → R_a = R/I:
    # V_tE,Y / V_tE,X = 8/6 (alt sınır etkin değil). θ_II sınırı Y: 0,12·2,5/(0,5·6) = 0,10.
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["deprem"]["tasiyici_x"] = "betonarme-cerceve-yuksek"
    b["deprem"]["tasiyici_y"] = "betonarme-perde-bosluksuz"
    d = yapi.bina_coz(b, anlat=True).veri["deprem"]
    assert d["X"]["Tp"] == pytest.approx(d["Y"]["Tp"]) and d["X"]["Tp"] > d["TB"]
    assert d["X"]["Ra"] == pytest.approx(8.0) and d["Y"]["Ra"] == pytest.approx(6.0)
    assert d["Y"]["VtE"] / d["X"]["VtE"] == pytest.approx(8.0 / 6.0, rel=1e-9)
    assert d["Y"]["theta_sinir"] == pytest.approx(0.10) and d["X"]["theta_sinir"] == pytest.approx(0.12 * 3 / (0.5 * 8))
    assert d["karma"]["X"]["kod"] == "A11" and d["karma"]["Y"]["kod"] == "A13"
    assert d["Ct"] == pytest.approx(0.07)                                  # en küçük C_t (motor kuralı, güvenli taraf)
    assert any("4.3.4.2" in u for u in d["uyarilar"])
    # süneklik düzeyleri farklı (A11 yüksek, A31 sınırlı) → 4.3.4.2 uyarısı
    b["deprem"]["tasiyici_y"] = "betonarme-cerceve-sinirli"
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert any("süneklik düzeyleri farklı" in u for u in d["uyarilar"])


def test_bolge_sistemi_en_kucuk_R():
    # Ana A11 (R = 8, D = 3) + 3. katta C13 (R = 5, D = 2) → iki doğrultuda R = 5, D = 2 (en küçük R'li satır).
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["deprem"]["tasiyici_bolgeleri"] = [{"katlar": [3, 3], "tasiyici": "celik-merkezi-capraz", "ad": "çatı katı"}]
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert (d["R"], d["D"]) == (5.0, 2.0) and d["karma"]["Y"]["kod"] == "C13"
    assert d["karma"]["BYS_min"] == 4                                      # elverişsiz: C13 BYS ≥ 4 (A11: ≥ 3)
    assert d["kappa"] == 0.5 and d["Ch"] == 1.0                           # betonarme + çelik: κ en küçük, C_h en büyük
    assert d["sinir_oran"] == pytest.approx(0.004)
    assert any("en küçük R" in u for u in d["uyarilar"])
    # eşit R'de küçük D: C13 (5; 2) ve A22 (5; 2,5) → D = 2
    b["deprem"]["tasiyici_bolgeleri"] = [{"katlar": [2, 2], "tasiyici": "betonarme-karma-perde"},
                                        {"katlar": [3, 3], "tasiyici": "celik-merkezi-capraz"}]
    assert yv.TBDY_TASIYICI["betonarme-karma-perde"]["R"] == 5 and yv.TBDY_TASIYICI["betonarme-karma-perde"]["D"] == 2.5
    d = yapi.bina_coz(b, anlat=False).veri["deprem"]
    assert (d["R"], d["D"]) == (5.0, 2.0)


def test_bolge_hatalari_ve_genel_model_grubu():
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    for bol, desen in (([{"katlar": [2, 5], "tasiyici": "celik-cerceve-yuksek"}], "1…3"),
                       ([{"grup": "KOLON", "tasiyici": "celik-cerceve-yuksek"}], "yalnız genel modelde"),
                       ([{"katlar": [1, 1]}], "'tasiyici'"), ([{"tasiyici": "celik-cerceve-yuksek"}], "'katlar'"),
                       ([{"katlar": [1, 1], "tasiyici": "yok-boyle"}], "Tablo 4.1")):
        b2 = copy.deepcopy(b)
        b2["deprem"]["tasiyici_bolgeleri"] = bol
        with pytest.raises(MatrisHatasi, match=desen):
            yapi.bina_coz(b2, anlat=False)
    g = yapi.bina_sablon("celik-cbf-3kat")
    g["deprem"]["tasiyici_bolgeleri"] = [{"grup": "KIRIS", "tasiyici": "celik-cerceve-sinirli"}]
    d = yapi.bina_coz(g, anlat=False).veri["deprem"]
    assert d["karma"]["bolgeler"][0]["grup"] == "KIRIS" and d["R"] == 4.0          # C31 R = 4 < C13 R = 5
    g["deprem"]["tasiyici_bolgeleri"] = [{"grup": "YOK", "tasiyici": "celik-cerceve-sinirli"}]
    with pytest.raises(MatrisHatasi, match="hiçbir çubukta yok"):
        yapi.bina_coz(g, anlat=False)


def test_genel_model_malzemeye_gore_kume():
    g = yapi.bina_sablon("celik-cbf-3kat")
    g2 = copy.deepcopy(g)
    g2["kombinasyon_kumeleri"] = {"celik": "cythye_gkt"}
    r1, r2 = yapi.bina_coz(g, anlat=False), yapi.bina_coz(g2, anlat=False)
    assert r2.veri["tasarim"]["kombinasyon_kumeleri"]["celik"]["kume"] == "cythye_gkt"
    assert "GKT" in r2.veri["tasarim"]["yontem"]["celik"] and "YDKT" in r1.veri["tasarim"]["yontem"]["celik"]
    g3 = copy.deepcopy(g)
    g3["kombinasyon_kumesi"] = "cythye_gkt"
    r3 = yapi.bina_coz(g3, anlat=False)
    d2 = {k["no"]: k["dc"] for k in r2.veri["tasarim"]["elemanlar"]}
    d3 = {k["no"]: k["dc"] for k in r3.veri["tasarim"]["elemanlar"]}
    assert d2 == d3


def test_kutuphane_ve_dogrulanmamis():
    k = yapi.kutuphane()
    dep = k["deprem"]
    assert dep["TL"] == 6.0 and tuple(dep["DTS"]["satirlar"][0]) == (0.75, "1")
    assert dep["BYS"]["satirlar"][5][3] == 91.0                       # Tablo 3.3 DTS 4 sütunu: BYS 3 ≤ 91 m
    assert dep["ozel_spektrum"]["asgari_oran"] == 0.90 and "2.4.1.2" in dep["ozel_spektrum"]["kaynak"]
    assert "4.3.4.2" in dep["karma"]["kaynak"]
    liste = yv.dogrulanmamis_kayitlar()
    for ad in ("EK_KURALLAR.ozel_spektrum.SDS_SD1", "EK_KURALLAR.karma.yukseklik", "EK_KURALLAR.azaltma.deprem"):
        assert ad in liste and k["ek_kurallar"][ad.split(".", 1)[1]]["dogrulandi"] is False


# ===========================================================================
# 4. Köprü: bina_spektrum
# ===========================================================================
def test_kopru_bina_spektrum_standart(kopru):
    # Sihirbaz örneği (sihirbaz.md §4.4): S_S = 1,2, S_1 = 0,35, ZD → F_S = 1,02 (1,0–1,25 arası 1,1 → 1,0: 1,1 − 0,2·0,4),
    # F_1 = 1,95 (0,3–0,4 arası 2,0 → 1,9), S_DS = 1,224, S_D1 = 0,6825, T_A = 0,1115, T_B = 0,5576 s, DTS 1;
    # H_N = 12 m → BYS 6 (10,5 < 12 ≤ 17,5); T_pA = 0,10·12^0,75 = 0,6447 s; λ = S_ae,DD3/S_ae,DD2 (T_pA) = 0,446.
    assert "bina_spektrum" in kopru.BINA_ISLEMLER
    y = iste(kopru, "bina_spektrum", {"SS": 1.2, "S1": 0.35, "SS_DD3": 0.45, "S1_DD3": 0.13, "zemin_sinifi": "ZD", "BKS": 3, "HN": 12})
    assert y["hata"] is None
    assert y["FS"] == pytest.approx(1.02) and y["F1"] == pytest.approx(1.95)
    assert y["SDS"] == pytest.approx(1.224) and y["SD1"] == pytest.approx(0.6825)
    assert y["TA"] == pytest.approx(0.2 * 0.6825 / 1.224) and y["TB"] == pytest.approx(0.6825 / 1.224) and y["TL"] == 6.0
    assert y["DTS"] == "1" and y["BYS"] == 6 and y["TpA"] == pytest.approx(0.1 * 12 ** 0.75)
    assert y["R"] == 8 and y["Ra"] == pytest.approx(8.0) and y["lambda"] == pytest.approx(0.4457, abs=1e-4)
    e = y["egriler"]
    assert len(e["T"]) == len(e["DD2"]) == len(e["SaR"]) == len(e["DD3"]) == len(y["spektrum"])
    assert e["T"][0] == 0.0 and e["T"][-1] == pytest.approx(6.0) and e["ozel"] is None and e["standart"] is None
    i = e["T"].index(pytest.approx(1.0))
    assert e["DD2"][i] == pytest.approx(0.6825) and e["SaR"][i] == pytest.approx(0.6825 / 8)
    # bina_coz ile aynı spektrum: yapi._spektrum
    sp = yapi._spektrum(1.2, 0.35, "ZD")
    assert all(v == pytest.approx(sp["Sae"](T), rel=1e-9) for T, v in zip(e["T"], e["DD2"]))


def test_kopru_bina_spektrum_ozel_ve_hatalar(kopru):
    girdi = {"deprem": {"SS": 1.2, "S1": 0.35, "zemin_sinifi": "ZF", "BKS": 3,
                        "ozel_spektrum": {"noktalar": [[0, 0.6], [0.15, 1.5], [0.8, 1.5], [1.0, 1.2], [4.0, 0.3]], "kaynak": "rapor"}},
             "HN": 9.0, "T_maks": 3.0, "adim": 0.05}
    y = iste(kopru, "bina_spektrum", girdi)
    assert y["hata"] is None and y["FS"] is None and y["SDS"] == pytest.approx(1.5)
    assert y["ozel_spektrum"]["asgari"]["saglandi"] in (True, False) and y["ozel_spektrum"]["taban_zemin"] == "ZE"
    assert y["egriler"]["ozel"] is not None and y["egriler"]["standart"] is not None and y["egriler"]["T"][-1] == pytest.approx(3.0)
    assert any("ZF" in u for u in y["uyarilar"])
    # doğrultuya göre sistem: S_aR iki eğri
    y2 = iste(kopru, "bina_spektrum", {"SS": 1.0, "S1": 0.3, "zemin_sinifi": "ZC", "HN": 9.6, "tasiyici_x": "betonarme-cerceve-yuksek",
                                        "tasiyici_y": "betonarme-perde-bosluksuz"})
    assert y2["hata"] is None and y2["egriler"]["SaR_Y"] is not None and y2["karma"]["Y"]["kod"] == "A13"
    # hatalar: motorla aynı iletiler, girdi türü
    h = iste(kopru, "bina_spektrum", {"SS": 1.2, "S1": 0.35, "zemin_sinifi": "ZF"})
    assert h["hata_turu"] == "girdi" and "sahaya özel" in h["hata"]
    h = iste(kopru, "bina_spektrum", {"S1": 0.35, "zemin_sinifi": "ZC"})
    assert h["hata_turu"] == "girdi" and "deprem.SS" in h["hata"]
    # bina girdisi: kart ve aks–kat H_N
    y3 = iste(kopru, "bina_spektrum", {"bina": yapi.bina_sablon("betonarme-3kat-3x3")})
    assert y3["hata"] is None and y3["HN"] == pytest.approx(9.6) and y3["SDS"] == pytest.approx(1.2)


def test_kopru_kutuphane_dts_bys(kopru):
    y = iste(kopru, "bina_kutuphane")
    assert y["hata"] is None and y["deprem"]["TL"] == 6.0 and "satirlar" in y["deprem"]["BYS"] and "satirlar" in y["deprem"]["DTS"]


def test_rapor_ve_tablolar_ekleri():
    import rapor
    import tablolar
    b = _karma_bina()
    b["yuk_durumlari"]["Q"] = {"acik": True, "azaltma": True}
    b["kombinasyon_kumeleri"] = {"betonarme": "ts500", "celik": "cythye_ydkt"}
    b["deprem"]["tasiyici_bolgeleri"] = [{"katlar": [4, 4], "tasiyici": "celik-cerceve-yuksek"}]
    b["deprem"]["ozel_spektrum"] = {"noktalar": [[0, 0.4], [0.1, 1.0], [0.6, 1.0], [1.0, 0.5], [2.0, 0.2], [4.0, 0.08]], "kaynak": "deneme"}
    r = yapi.bina_coz(b, anlat=True)
    h = rapor.statik_rapor(b, r.veri)
    for metin in ("6.9 Hareketli yük azaltması", "Sahaya özel spektrum (TBDY md. 2.4)", "Karma taşıyıcı sistem", "Karma yapı — eleman"):
        assert metin in h
    t = tablolar.bina_tablolari(b, r.veri, kati=True)
    az = tablolar.tablo(t, "hareketli_azaltma")
    assert az and az["satirlar"][0]["degerler"]["beta"] == pytest.approx(0.95)
    assert tablolar.tablo(t, "ozel_spektrum") and tablolar.tablo(t, "karma_sistem")
    kol = tablolar.tablo(t, "tasarim_betonarme_kolon")
    assert any(s["ad"] == "beta_Q" for s in kol["sutunlar"])
    # anahtarsız modelde yeni tablolar yok
    t0 = tablolar.bina_tablolari(yapi.bina_sablon("betonarme-3kat-3x3"), yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"), anlat=False).veri)
    assert not {"hareketli_azaltma", "ozel_spektrum", "karma_sistem"} & {x["ad"] for x in t0}
    assert math.isfinite(r.veri["ozet"]["en_buyuk_dc"])
    assert yapi_serbest is not None
