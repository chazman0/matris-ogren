# -*- coding: utf-8 -*-
"""yapi.py Dilim 3: kesit tahkikleri (veri["tasarim"], 12. adım, eleman_tasarim) — moment işareti, el hesabı, kolon eksen
eşlemesi (yon takası), eş zamanlı kolon noktaları, çelik şablon, bütün şablonlar, tasarim.py yokken çözüm."""
from __future__ import annotations

import copy
import json
import math
import sys

import pytest

import matris_ogren as mo
import sonlu_eleman as se
import tasarim
import yapi

SABLONLAR = list(yapi.BINA_SABLONLARI)


@pytest.fixture(scope="module")
def cozumler():
    return {ad: yapi.bina_coz(yapi.bina_sablon(ad), goster="yok") for ad in SABLONLAR}


def yakin(a, b, tol=1e-6):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def kayit(veri, tur, no):
    return next(e for e in veri["tasarim"]["elemanlar"] if e["tur"] == tur and e["no"] == no)


def fe_eleman(veri, tur, no, parca=1):
    return next(e for e in veri["ag"]["elemanlar"] if e["tur"] == tur and e["kaynak_no"] == no and e["parca"] == parca)


def diyagram(kisa, no):
    return next(e for e in kisa["elemanlar"] if e["no"] == no)


# ---------------------------------------------------------------------------
# moment işareti: motor M "alt lif çekme +" (kirişte y′ yukarı)
# ---------------------------------------------------------------------------
def test_basit_kiris_aciklik_momenti_pozitif():
    """Uzay çerçeve motorunda iki ucu mafsallı (burulma tutulu) basit kiriş, düzgün aşağı yük: açıklık M = +qL²/8."""
    L, q = 6.0, 10.0
    model = {"tip": "cerceve3b", "hesap": "sayisal",
             "dugumler": [{"no": 1, "x": 0.0, "y": 0.0, "z": 0.0}, {"no": 2, "x": L, "y": 0.0, "z": 0.0}],
             "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": 3e7, "G": 1.2e7, "A": 0.125, "Iy": 6.5e-4, "Iz": 2.6e-3, "J": 1.6e-3}],
             "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "uz": True, "rx": True},
                           {"dugum": 2, "uy": True, "uz": True, "rx": True}],
             "yukler": [], "yayili": []}
    r = se.coz_coklu(model, {"G": {"yukler": [], "yayili": [{"eleman": 1, "q": -q}]}}, diyagram_nokta=11)["G"]
    e = r["elemanlar"][0]
    d = e.get("diyagram", e)
    orta = d["M"][len(d["M"]) // 2]
    assert yakin(d["x"][len(d["x"]) // 2], L / 2)
    assert orta > 0 and yakin(orta, q * L * L / 8, 1e-9)        # pozitif = alt lif çekme (sarkma)
    assert abs(d["M"][0]) < 1e-9 and abs(d["M"][-1]) < 1e-9


def test_bina_kirisi_isaret_kurali(cozumler):
    """Bina kirişinde (kolonlara ankastre) 1.4G+1.6Q: açıklık M > 0 (alt donatı), uçlar M < 0 (üst donatı); tasarım kaydı
    bu işaretle mesnet ve açıklık momentlerini ayırır."""
    v = cozumler["betonarme-tek-aciklik"].veri
    for k in v["bina"]["kirisler"]:
        e = fe_eleman(v, "kiris", k["no"])
        M = diyagram(v["sonuclar"]["1.4G+1.6Q"], e["no"])["M"]
        assert M[len(M) // 2] > 0 and M[0] < 0 and M[-1] < 0
        oz = kayit(v, "kiris", k["no"])["ozet"]
        assert yakin(oz["Md_aciklik"], max(M), 1e-4) and yakin(oz["Md_mesnet"], max(-M[0], -M[-1]), 1e-4)


# ---------------------------------------------------------------------------
# kiriş: el hesabı
# ---------------------------------------------------------------------------
def test_kiris_donati_el_hesabi(cozumler):
    v = cozumler["betonarme-tek-aciklik"].veri
    k = kayit(v, "kiris", 1)
    e = fe_eleman(v, "kiris", 1)
    d = diyagram(v["sonuclar"]["1.4G+1.6Q"], e["no"])      # tek dayanım kombinasyonu (S, W, E kapalı)
    assert v["tasarim"]["kombinasyon_sayisi"] == 1
    Md_a, Md_m, Vd = max(d["M"]), max(-d["M"][0], -d["M"][-1]), max(abs(x) for x in d["V"])
    b, h, dp = 0.25, 0.50, 0.03 + 0.02                       # K25x50, pas 30 mm + 20 mm → d′ = 50 mm
    for Md, As_kayit, oneri in ((Md_a, k["ozet"]["As_alt_cm2"], k["ozet"]["oneri_alt"]),
                                (Md_m, k["ozet"]["As_ust_cm2"], k["ozet"]["oneri_ust"])):
        r = tasarim.kiris_egilme(Md, b, h, dp, "C30/37", "B420C")
        assert yakin(r["As_gerekli_cm2"], As_kayit, 1e-4) and r["oneri"]["metin"] == oneri
        # kapalı form: a = d − √(d² − 2M/(0,85 fcd b)), As = max(0,85 fcd b a / fyd, ρmin b d)
        bm, dm = tasarim.beton_malzeme("C30/37"), tasarim.donati_malzeme("B420C")
        dd, bb, M = (h - dp) * 1000, b * 1000, Md * 1e6
        a = dd - math.sqrt(dd * dd - 2 * M / (0.85 * bm["fcd"] * bb))
        As = max(0.85 * bm["fcd"] * bb * a / dm["fyd"], 0.8 * bm["fctd"] / dm["fyd"] * bb * dd) / 100.0
        assert yakin(As, As_kayit, 1e-4)
    ks = tasarim.kiris_kesme(Vd, b, h, dp, "C30/37", "B420C")
    assert yakin(k["ozet"]["Vd"], Vd, 1e-4)
    assert k["ozet"]["etriye"] == f"Φ{ks['oneri']['cap']}/{ks['oneri']['s_mm'] / 10:.0f}"
    # kontrol satırları: dayanım satırları önce, belirleyen kombinasyon adlı
    ad = [x["ad"] for x in k["kontroller"]]
    assert ad[:4] == ["Eğilme (mesnet, üst) Md ≤ Mr", "Eğilme (açıklık, alt) Md ≤ Mr", "Kesme Vd ≤ Vc + Vw",
                      "Kesme üst sınırı Vd ≤ 0,22 fcd bw d"]
    assert k["kontroller"][0]["kombinasyon"] == "1.4G+1.6Q" and len(k["kontroller"]) <= 8
    assert k["belirleyen"]["kombinasyon"] == "1.4G+1.6Q" and k["dc"] == max(x["dc"] for x in k["kontroller"] if not x.get("kosul"))


def test_kiris_kosul_ihlali_belirler():
    """Sınırdaki koşul (TBDY bw = 250 mm) D/C'yi 1'e çekmez; sağlanmayan koşul (bw = 200 mm) belirler ve kesit büyüt der."""
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    v = yapi.bina_coz(b, anlat=False, goster="yok").veri
    assert all(e["dc"] < 1.0 for e in v["tasarim"]["elemanlar"])
    b["kesitler"]["K25x50"]["b"] = 0.20
    v = yapi.bina_coz(b, anlat=False, goster="yok").veri
    k = kayit(v, "kiris", 1)
    assert k["dc"] > 1.0 and k["belirleyen"]["kontrol"] == "boyut" and k["durum"] == "kesit büyüt"
    assert any(x.get("kosul") and not x["saglandi"] for x in k["kontroller"])


# ---------------------------------------------------------------------------
# kolon: eksen eşlemesi (yon takası) — X yönünde yatay yük yalnız X yönü boyutuyla eğilme yaratır
# ---------------------------------------------------------------------------
def _dikdortgen_kolonlu(yon, FX=0.0):
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kesitler"]["S30x60"] = {"tip": "dikdortgen", "b": 0.30, "h": 0.60, "malzeme": "C30", "donati": "B420C", "pas": 0.03}
    for c in b["kolonlar"]:
        c["kesit"], c["yon"] = "S30x60", yon
    if FX:
        for aks in (["A", "1"], ["A", "2"], ["B", "1"], ["B", "2"]):
            b["ek_yukler"].append({"tur": "dugum", "aks": aks, "kat": 1, "durum": "Q", "FX": FX})
    return yapi.bina_coz(b, anlat=False, goster="yok")


def test_kolon_eksen_eslemesi_X_yuku():
    r0, r1 = _dikdortgen_kolonlu("x"), _dikdortgen_kolonlu("x", FX=60.0)
    k0 = yapi.eleman_tasarim(r0.ic, "kolon", 1, goster="yok").veri
    k1 = yapi.eleman_tasarim(r1.ic, "kolon", 1, goster="yok").veri
    assert k1["ozet"]["bX"] == 0.60 and k1["ozet"]["bY"] == 0.30          # yon "x": güçlü boyut X doğrultusunda
    for p0, p1 in zip(k0["noktalar"], k1["noktalar"]):
        assert p0["ad"] == p1["ad"]
        assert abs(p1["Mx"] - p0["Mx"]) < 1e-3                          # X yükü bina X ekseni etrafında moment yaratmaz
        assert abs(p1["My"] - p0["My"]) > 50.0                           # yalnız Y ekseni etrafında (X yönü boyutu bX)
        assert abs(p1["N"] - p0["N"]) < 0.2 * abs(p0["N"]) + 50.0
    # kontrol bu eşlemeyle yapılmış: kolon_kontrol(b = bX, h = bY) ile aynı D/C; takas (b = bY, h = bX) farklı ve daha büyük
    nk = k1["noktalar"]
    arg = ([p["N"] for p in nk], [p["Mx"] for p in nk], [p["My"] for p in nk])
    As = 0.01 * 0.30 * 0.60 * 1e4
    dogru = tasarim.kolon_kontrol(*arg, 0.60, 0.30, As, 0.05, "C30/37", "B420C", tbdy=False)
    takas = tasarim.kolon_kontrol(*arg, 0.30, 0.60, As, 0.05, "C30/37", "B420C", tbdy=False)
    en_dogru = max(p["dc"] for p in dogru["noktalar"])
    assert yakin(max(p["dc"] for p in nk), en_dogru, 1e-4)
    assert max(p["dc"] for p in takas["noktalar"]) > 1.3 * en_dogru
    # yon "y" (güçlü boyut Y'de): aynı X yükü zayıf boyutla karşılanır → D/C artar
    r2 = _dikdortgen_kolonlu("y", FX=60.0)
    k2 = yapi.eleman_tasarim(r2.ic, "kolon", 1, goster="yok").veri
    assert k2["ozet"]["bX"] == 0.30 and k2["ozet"]["bY"] == 0.60
    assert max(p["dc"] for p in k2["noktalar"]) > 1.3 * en_dogru
    # eğri adları: egri_x bina X ekseni etrafında (derinlik bY), egri_y Y ekseni etrafında (derinlik bX)
    Mx_kap = max(p["M"] for p in k1["egri_x"])
    My_kap = max(p["M"] for p in k1["egri_y"])
    assert My_kap > 1.5 * Mx_kap                                       # bX = 0,60 > bY = 0,30


def test_kolon_noktalari_es_zamanli(cozumler):
    """Kolon noktaları zarf değil: her noktanın N, Mx, My'si aynı kombinasyonun aynı ucundan (kombinasyon_kisa ile denetlenir)."""
    r = cozumler["betonarme-3kat-3x3"]
    v = r.veri
    k = yapi.eleman_tasarim(r.ic, "kolon", 5, goster="yok").veri
    e = fe_eleman(v, "kolon", 5)
    lam = e["lam"]
    adlar = list(dict.fromkeys(p["kombinasyon"] for p in k["noktalar"]))
    assert len(k["noktalar"]) == 2 * len(adlar) == 2 * v["tasarim"]["kombinasyon_sayisi"]
    for ad in adlar[:: max(1, len(adlar) // 6)]:
        d = diyagram(yapi.kombinasyon_kisa(r.ic, ad), e["no"])
        for uc, s in (("alt", 0), ("üst", -1)):
            p = next(p for p in k["noktalar"] if p["kombinasyon"] == ad and p["uc"] == uc)
            assert yakin(p["N"], -d["N"][s], 1e-4)
            assert yakin(p["Mx"], d["My"][s] * lam[1][0] + d["M"][s] * lam[2][0], 1e-4)
            assert yakin(p["My"], d["My"][s] * lam[1][1] + d["M"][s] * lam[2][1], 1e-4)
    # eş zamanlılık zarfla aynı şey değil: en büyük N ile en büyük |Mx| farklı kombinasyonlardan gelir
    pN = max(k["noktalar"], key=lambda p: p["N"])
    pM = max(k["noktalar"], key=lambda p: abs(p["Mx"]))
    assert pN["kombinasyon"] != pM["kombinasyon"]
    assert abs(pN["Mx"]) < abs(pM["Mx"])
    # belirleyen satırın kombinasyonu nokta listesinde var
    assert kayit(v, "kolon", 5)["belirleyen"]["kombinasyon"] in adlar


def test_kolon_rho_varsayimi_ve_tarama():
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["kesitler"]["S45x45"].update(b=0.30, h=0.30)
    r = yapi.bina_coz(b, anlat=False, goster="yok")
    kol = [e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kolon"]
    assert all(e["ozet"]["rho"] == 0.01 and e["ozet"]["rho_varsayim"] for e in kol)
    asan = [e for e in kol if e["dc"] > 1.0]
    assert asan and all(e["durum"] in ("donatı artır", "kesit büyüt") for e in asan)
    e = max(asan, key=lambda e: e["dc"])
    rg = e["ozet"]["rho_gerekli"]
    assert rg is not None and 0.01 < rg <= 0.04
    nk = yapi.eleman_tasarim(r.ic, "kolon", e["no"], goster="yok").veri["noktalar"]
    arg = ([p["N"] for p in nk], [p["Mx"] for p in nk], [p["My"] for p in nk], 0.30, 0.30)
    dc = lambda rho: max(p["dc"] for p in tasarim.kolon_kontrol(*arg, rho * 900, 0.05, "C30/37", "B420C", tbdy=False)["noktalar"])  # noqa: E731
    assert dc(rg) <= 1.0 + 1e-9 and dc(rg - 0.0025) > 1.0
    # kesitte verilen donatı oranı kullanılır (varsayım değil)
    b["kesitler"]["S45x45"]["donati_orani"] = 0.03
    v = yapi.bina_coz(b, anlat=False, goster="yok").veri
    k = kayit(v, "kolon", e["no"])
    assert k["ozet"]["rho"] == 0.03 and not k["ozet"]["rho_varsayim"] and k["dc"] < e["dc"]
    assert not any("ρ = %1" in u for u in v["tasarim"]["varsayimlar"])


# ---------------------------------------------------------------------------
# çelik
# ---------------------------------------------------------------------------
def test_celik_sablon(cozumler):
    v = cozumler["celik-1kat-depo"].veri
    t = v["tasarim"]
    assert t["yontem"]["celik"].startswith("ÇYTHYE 2018") and "YDKT" in t["yontem"]["celik"]
    assert len(t["elemanlar"]) == len(v["bina"]["kirisler"]) + len(v["bina"]["kolonlar"])
    adlar = {k["ad"] for k in v["kombinasyonlar"] if k["uygulandi"]}
    for e in t["elemanlar"]:
        assert e["sistem"] == "celik" and 0 < e["dc"] < 5, e
        assert e["belirleyen"]["kombinasyon"] in adlar | {None}
        assert any(x["ad"].startswith("Bileşik etki") for x in e["kontroller"])
        assert {"sinif", "Mn_kNm", "Pn_kN", "Vn_kN"} <= set(e["ozet"])
        if e["tur"] == "kiris":
            assert e["ozet"]["Lb_m"] == 0.0                        # döşemeli kiriş: üst başlık tutulu
        else:
            assert e["ozet"]["Lb_m"] == 5.0 and e["ozet"]["K"] == 1.0
    assert any("üst başlık" in s for s in t["varsayimlar"])
    # L_b = açıklık seçeneği: yanal burulmalı burkulma devreye girer, eğilme kapasitesi düşer, kiriş D/C artar
    b = yapi.bina_sablon("celik-1kat-depo")
    b["analiz"]["celik_Lb"] = "boy"
    v2 = yapi.bina_coz(b, anlat=False, goster="yok").veri
    for e in v2["tasarim"]["elemanlar"]:
        if e["tur"] == "kiris":
            e1 = kayit(v, "kiris", e["no"])
            assert e["ozet"]["Lb_m"] > 0 and e["ozet"]["Mc_kNm"] < e1["ozet"]["Mc_kNm"] and e["dc"] > e1["dc"]
    # kolon güçlü eksen yon'a göre: HEB 240, yon x → güçlü eksen momenti motor M (bina Y ekseni etrafında)
    r = cozumler["celik-1kat-depo"]
    _ = r


def test_celik_kiris_negatif_moment_alt_baslik(cozumler):
    """Döşeme yalnız üst başlığı tutar: pozitif moment L_b = 0; mesnette (negatif moment) alt başlık basınçta → L_b = açıklık,
    C_b moment diyagramından (ÇYTHYE Denk. 9.1). İki bölge ayrı denetlenir, büyük D/C belirler. IPE 300, B mesnedi."""
    r = cozumler["celik-1kat-depo"]
    v = r.veri
    k = next(k for k in v["bina"]["kirisler"] if k["kesit"] == "IPE300" and k["bas"] == ["A", "1"])
    e = kayit(v, "kiris", k["no"])
    o = e["ozet"]
    assert o["Lb_m"] == 0.0 and yakin(o["Lb_neg_m"], 6.0) and o["bolge"] in ("pozitif", "negatif")
    assert 1.0 < o["Cb_neg"] < 3.0 and o["dc_negatif"] is not None and yakin(e["dc"], max(o["dc_pozitif"], o["dc_negatif"]), 1e-4)
    assert any("negatif M" in x["ad"] for x in e["kontroller"]) and any("pozitif M" in x["ad"] for x in e["kontroller"])
    # C_b el hesabı: belirleyen kombinasyonun negatif momentli parça diyagramı, çeyrek noktalar
    ad = "1.2G+1.6Q"
    d = diyagram(yapi.kombinasyon_kisa(r.ic, ad), k["parcalar"][0]["eleman"])
    xs, M = d["x"], d["M"]
    L = xs[-1]
    MA, MB, MC = (abs(float(np_interp(f * L, xs, M))) for f in (0.25, 0.5, 0.75))
    Cb = tasarim.cb_katsayisi(max(abs(m) for m in M), MA, MB, MC)
    assert min(M) < 0 and 1.5 < Cb < 3.0
    assert o["Cb_neg"] <= Cb * (1 + 1e-4)                               # en küçük C_b (güvenli taraf; 5 anlamlı basamak)
    # el hesabı: C_b = 1 ile L_b = 6 m'de kapasite çok düşer (eski L_b = 0 kabulü negatif bölgede güvensizdi)
    Mneg = -min(M)
    ust = tasarim.celik_egilme("IPE 300", 275.0, Lb=0.0)["Mc_kNm"]
    alt1 = tasarim.celik_egilme("IPE 300", 275.0, Lb=6.0, Cb=1.0)["Mc_kNm"]
    altC = tasarim.celik_egilme("IPE 300", 275.0, Lb=6.0, Cb=o["Cb_neg"])["Mc_kNm"]
    assert alt1 < 0.6 * ust and Mneg / alt1 > 1.0 and altC <= ust + 1e-9
    assert yakin(o["Mc_neg_kNm"], altC, 1e-4)
    assert e["dc"] <= 1.0 and v["tasarim"]["en_buyuk_dc"] <= 1.0                         # şablon yönetmeliği sağlar
    # 'boy' seçeneği: her yerde L_b = L, C_b = 1, tek denetim
    b = yapi.bina_sablon("celik-1kat-depo")
    b["analiz"]["celik_Lb"] = "boy"
    e2 = kayit(yapi.bina_coz(b, anlat=False, goster="yok").veri, "kiris", k["no"])
    assert e2["ozet"]["Lb_m"] == 6.0 and "Cb_neg" not in e2["ozet"] and e2["dc"] > e["dc"]
    # anlatım: iki bölge başlığı
    md = yapi.eleman_tasarim(r.ic, "kiris", k["no"], goster="yok").anlatim.markdown()
    assert "pozitif moment" in md and "negatif moment" in md and "alt başlık" in md


def np_interp(x, xs, ys):
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])
    return ys[-1]


def test_celik_kolon_guclu_eksen(cozumler):
    v = cozumler["celik-1kat-depo"].veri
    r = cozumler["celik-1kat-depo"]
    for c in v["bina"]["kolonlar"]:
        kk = yapi.eleman_tasarim(r.ic, "kolon", c["no"], goster="yok").veri
        d = diyagram(yapi.kombinasyon_kisa(r.ic, kk["kuvvetler"][0]["ad"]), c["eleman"])
        guclu, zayif = ("M", "My") if c["yon"] == "x" else ("My", "M")
        assert yakin(kk["kuvvetler"][0]["Mx"], max(abs(x) for x in d[guclu]), 1e-4)
        assert yakin(kk["kuvvetler"][0]["My"], max(abs(x) for x in d[zayif]), 1e-4)


# ---------------------------------------------------------------------------
# bütün şablonlar: şema, JSON, boyut, anlatım
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", SABLONLAR)
def test_butun_sablonlar_tasarim(cozumler, ad):
    r = cozumler[ad]
    v = r.veri
    t = v["tasarim"]
    json.dumps(t, allow_nan=False)
    assert {"yontem", "varsayimlar", "elemanlar", "en_buyuk_dc", "kritik", "dc_dagilimi", "uyarilar"} <= set(t)
    assert len(t["elemanlar"]) == len(v["bina"]["kirisler"]) + len(v["bina"]["kolonlar"])
    assert sum(t["dc_dagilimi"].values()) == len(t["elemanlar"]) and set(t["dc_dagilimi"]) == {"<0.7", "0.7-0.9", "0.9-1.0", ">1.0"}
    assert v["ozet"]["en_buyuk_dc"] == t["en_buyuk_dc"] == max(e["dc"] for e in t["elemanlar"])
    assert len(t["kritik"]) == min(5, len(t["elemanlar"])) and t["kritik_elemanlar"][0]["dc"] == t["en_buyuk_dc"]
    fe = {e["no"]: e for e in v["ag"]["elemanlar"]}
    for e in t["elemanlar"]:
        assert {"no", "tur", "kat", "adres", "kesit", "malzeme", "sistem", "fe_elemanlar", "dc", "durum", "belirleyen", "kontroller", "ozet"} <= set(e)
        assert e["durum"] in ("yeterli", "donatı artır", "kesit büyüt")
        assert 1 <= len(e["kontroller"]) <= 8
        assert all(fe[n]["tur"] == e["tur"] and fe[n]["kaynak_no"] == e["no"] for n in e["fe_elemanlar"])
        for x in e["kontroller"]:
            assert {"ad", "talep", "kapasite", "dc", "birim", "kaynak", "saglandi", "kombinasyon"} <= set(x)
        assert e["dc"] > 0
    assert len(json.dumps(t, ensure_ascii=False)) < 2_000 * len(t["elemanlar"]) + 5_000     # eleman başına ölçülü
    assert "egri_x" not in json.dumps(t)                                                     # eğri yalnız köprü ayrıntısında
    md = "\n".join(b[1] for b in r.anlatim.bloklar if b[0] == "md")
    assert "12. Adım: Kesit tahkikleri" in md and "13. Adım: Aynı hesap Python'da" in md
    assert "En kritik 10 eleman" in md and "D/C dağılımı" in md and "elemana dokununca" in md


def test_deprem_uyarisi(cozumler):
    t = cozumler["betonarme-3kat-3x3"].veri["tasarim"]
    assert any("kapasite tasarımı" in u for u in t["uyarilar"])
    assert t["kombinasyon_sayisi"] > 60                                                       # deprem birleşimleri dahil
    assert not any("kapasite tasarımı" in u for u in cozumler["betonarme-2kat-3x2"].veri["tasarim"]["uyarilar"])


def test_eleman_tasarim_anlatim_ve_hatalar(cozumler):
    r = cozumler["betonarme-2kat-3x2"]
    s = yapi.eleman_tasarim(r.ic, "kiris", 1, goster="yok")
    assert isinstance(s, mo.Sonuc) and s.veri["no"] == 1 and s.veri["tur"] == "kiris"
    turler = {b[0] for b in s.anlatim.bloklar}
    assert "sema" in turler and "math" in turler                                              # kesit şeması anlatımda
    assert yakin(s.veri["dc"], kayit(r.veri, "kiris", 1)["dc"], 1e-9)
    s = yapi.eleman_tasarim(r.ic, "kolon", 3, goster="yok")
    assert {"egri_x", "egri_y", "noktalar"} <= set(s.veri) and s.veri["egri_x"][0].keys() == {"N", "M"}
    assert set(s.veri["noktalar"][0]) >= {"ad", "N", "Mx", "My", "dc"}
    for tur, no, parca in (("kiriş", 1, "tanımsız"), ("kolon", 999, "yok"), ("kolon", "x", "tam sayı")):
        with pytest.raises(mo.MatrisHatasi, match=parca):
            yapi.eleman_tasarim(r.ic, tur, no)
    with pytest.raises(mo.MatrisHatasi, match="Önce bina"):
        yapi.eleman_tasarim({}, "kolon", 1)


# ---------------------------------------------------------------------------
# tasarim.py yokken
# ---------------------------------------------------------------------------
def test_tasarim_modulu_yokken(monkeypatch):
    monkeypatch.setitem(sys.modules, "tasarim", None)
    assert yapi._tasarim_modulu() is None
    r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"), goster="yok")
    assert "tasarim" not in r.veri and "en_buyuk_dc" not in r.veri["ozet"]
    md = "\n".join(b[1] for b in r.anlatim.bloklar if b[0] == "md")
    assert "Kesit tahkikleri" not in md and "13. Adım" in md and "11. Adım" in md
    assert r.veri["akis"]["kolonlar"] and r.ic["tasarim"] is None
    with pytest.raises(mo.MatrisHatasi, match="tasarim.py"):
        yapi.eleman_tasarim(r.ic, "kolon", 1)


def test_hatali_kesit_cozumu_durdurmaz():
    """tasarim.py'nin öğretici hatası (burada paspayı > h/2) çözümü durdurmaz: eleman kaydı "hesaplanamadı" olur, uyarı yazılır."""
    b = yapi.bina_sablon("betonarme-tek-aciklik")
    b["kesitler"]["K25x50"]["pas"] = 0.24                     # d′ = 0,26 m > h/2: kiris_egilme öğretici hata verir
    v = yapi.bina_coz(b, anlat=False, goster="yok").veri
    k = kayit(v, "kiris", 1)
    assert k["dc"] is None and k["durum"] == "hesaplanamadı" and "Paspayı" in k["hata"]
    assert any("tahkik yapılamadı" in u for u in v["tasarim"]["uyarilar"])
    assert v["tasarim"]["en_buyuk_dc"] == max(e["dc"] for e in v["tasarim"]["elemanlar"] if e["dc"] is not None)
    with pytest.raises(mo.MatrisHatasi):
        yapi.bina_coz(dict(copy.deepcopy(b), analiz={"celik_Lb": "kisa"}), anlat=False)
