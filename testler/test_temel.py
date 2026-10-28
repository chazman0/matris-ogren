# -*- coding: utf-8 -*-
"""temel.py: mütemadi (sürekli) temel ve radye — Winkler zemini, taban basıncı, oturma, zımbalama, donatı (§13).

Sınamalar: denge (Σ p·A = Σ N_kolon + W_temel), simetrik yükte simetrik basınç, rijit radye sınırında düzgün basınç,
sonsuz kiriş Winkler çözümüyle (Hetényi) karşılaştırma, zımbalama el hesabı (TS 500 md. 8.3.1), ters T kesit
özellikleri, öğretici hatalar, şablonlar ve köprü.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

import matris_ogren as mo
import sonlu_eleman as se
import tasarim as ts
import temel as tm
import yapi

PROJE = Path(__file__).resolve().parent.parent


def yakin(a, b, tol=1e-8):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def bina_temelli(sablon, tip, **ayar):
    b = yapi.bina_sablon(sablon)
    b["temeller"]["tip"] = tip
    if ayar:
        b["temeller"][tip] = dict(b["temeller"].get(tip) or {}, **ayar)
    return b


@pytest.fixture(scope="module")
def kucuk():
    """2 katlı 3×2 aks şablonu: mütemadi (xy) ve radye ile (anlatımlı)."""
    return {tip: yapi.bina_coz(bina_temelli("betonarme-2kat-3x2", tip), goster="yok") for tip in ("surekli", "radye")}


@pytest.fixture(scope="module")
def sablonlar():
    return {ad: yapi.bina_coz(yapi.bina_sablon(ad), goster="yok") for ad in ("betonarme-3kat-surekli-temel", "betonarme-4kat-radye")}


# ---------------------------------------------------------------------------
# saf yardımcılar
# ---------------------------------------------------------------------------
def test_tip_oku_ve_es_anlamlar():
    assert tm.tip_oku(None) == "tekil" and tm.tip_oku("Mütemadi") == "surekli" and tm.tip_oku("sürekli") == "surekli"
    assert tm.tip_oku("radye") == "radye"
    with pytest.raises(mo.MatrisHatasi, match="tanımsız"):
        tm.tip_oku("kazik")


def test_ters_t_kesit_el_hesabi():
    B, t, b, H = 1.2, 0.4, 0.5, 1.0
    k = tm.ters_t_kesit(B, t, b, H)
    A1, A2 = B * t, b * (H - t)
    yc = (A1 * t / 2 + A2 * (t + (H - t) / 2)) / (A1 + A2)
    I = B * t ** 3 / 12 + A1 * (yc - t / 2) ** 2 + b * (H - t) ** 3 / 12 + A2 * (t + (H - t) / 2 - yc) ** 2
    assert yakin(k["A"], A1 + A2) and yakin(k["y_c"], yc) and yakin(k["I_guclu"], I) and not k["dikdortgen"]
    assert yakin(k["I_zayif"], t * B ** 3 / 12 + (H - t) * b ** 3 / 12)
    d = tm.ters_t_kesit(1.0, 0.0, 1.0, 0.8)          # dikdörtgen özel hal
    assert d["dikdortgen"] and yakin(d["A"], 0.8) and yakin(d["I_guclu"], 0.8 ** 3 / 12)
    with pytest.raises(mo.MatrisHatasi, match="tabla genişliği"):
        tm.ters_t_kesit(0.5, 0.3, 0.6, 1.0)
    with pytest.raises(mo.MatrisHatasi, match="h_govde"):
        tm.ters_t_kesit(1.2, 1.2, 0.5, 1.0)


def test_zimbalama_el_hesabi_ic_kenar_kose():
    """TS 500 md. 8.3.1: V_pr = γ f_ctd u_p d; u_p kolon yüzünden d/2; V_pd = N_d − p_d·A (çevre içi zemin tepkisi)."""
    fctd = ts.beton_malzeme("C30/37")["fctd"]                 # MPa
    bx, by, d, N, p = 0.5, 0.6, 0.63, 1500.0, 120.0
    z = tm.zimbalama(N, bx, by, d, "C30/37", p_d=p)
    u = 2 * (bx + d) + 2 * (by + d)
    A = (bx + d) * (by + d)
    assert z["konum"] == "iç" and yakin(z["u_p"], u) and yakin(z["A_bolge"], A)
    assert yakin(z["V_pr"], fctd * 1000.0 * u * d) and yakin(z["V_pd"], N - p * A) and yakin(z["dc"], (N - p * A) / z["V_pr"])
    # kenar kolon: −X yüzü plak kenarında → o yan açık (Şekil 8.5), u = (by + d) + 2(bx + d/2)
    z = tm.zimbalama(N, bx, by, d, "C30/37", p_d=p, kenar={"-X": 0.0})
    assert z["konum"] == "kenar" and yakin(z["u_p"], (by + d) + 2 * (bx + d / 2))
    assert yakin(z["A_bolge"], (bx + d / 2) * (by + d))
    # köşe kolon: −X ve −Y açık, u = (bx + d/2) + (by + d/2)
    z = tm.zimbalama(N, bx, by, d, "C30/37", p_d=0.0, kenar={"-X": 0.0, "-Y": 0.0})
    assert z["konum"] == "köşe" and yakin(z["u_p"], (bx + d / 2) + (by + d / 2)) and yakin(z["V_pd"], N)
    # kenar yakınsa (a < d/2) kapalı çevre geçersiz; uzaksa iç kolon gibi (kapalı daha küçük çevre seçilir)
    z = tm.zimbalama(N, bx, by, d, "C30/37", kenar={"-X": 5.0})
    assert z["konum"] == "iç" and yakin(z["u_p"], u)
    # dışmerkezlik: γ = 1/(1 + 1,5(e_x + e_y)/√(b_x b_y)) (Denk. 8.24)
    z = tm.zimbalama(N, bx, by, d, "C30/37", ex=0.05, ey=0.02)
    g = 1.0 / (1.0 + 1.5 * 0.07 / math.sqrt(bx * by))
    assert yakin(z["gamma"], g) and yakin(z["V_pr"], g * fctd * 1000.0 * u * d)


def test_plak_egilme_en_kucuk_donati_ve_dikdortgen_blok():
    r = tm.plak_egilme(0.0, 0.6, "C30/37", "B420C")
    d = (0.6 - tm.PAS) * 1000.0
    assert yakin(r["As_gerekli_cm2"], 0.002 * 1000.0 * d / 100.0) and r["durum"] == "yeterli"   # ρ_min = 0,002 (TS 500)
    bm, dm = ts.beton_malzeme("C30/37"), ts.donati_malzeme("B420C")
    Md = 250.0
    r = tm.plak_egilme(Md, 0.6, "C30/37", "B420C")
    a = d - math.sqrt(d * d - 2 * Md * 1e6 / (0.85 * bm["fcd"] * 1000.0))
    As = 0.85 * bm["fcd"] * 1000.0 * a / dm["fyd"]
    assert yakin(r["As_hesap_cm2"], As / 100.0, 1e-9) and r["Mr_kNm"] >= Md and r["oneri"]["s_mm"] <= 200.0


# ---------------------------------------------------------------------------
# sonsuz kiriş Winkler çözümü (Hetényi) ↔ ayrık yaylı sonlu eleman
# ---------------------------------------------------------------------------
def test_sonsuz_kiris_hetenyi():
    """w(x) = Pβ/(2k)·e^(−βx)(cos βx + sin βx), M(0) = P/(4β), β = ⁴√(k/(4EI)), k = k0·b. Mütemadi temelle aynı ağ ve yay
    kuralı (k_z = k0·b·l_etki); a·β ≈ 0,06 ile fark binde birkaç."""
    k0, b, E, I, P, ag, L = 20000.0, 1.0, 30e6, 0.05, 100.0, 0.25, 60.0
    model, iP, pts = tm.kiris_winkler_modeli(L, ag, b, k0, E, I, P)
    r = se.coz_coklu(model, {"P": {"yukler": model["yukler"]}})["P"]
    k = k0 * b
    beta = (k / (4 * E * I)) ** 0.25
    w0 = P * beta / (2 * k)
    u = r["u"]
    w = lambda i: -u[6 * (i - 1) + 1]          # noqa: E731  (motor y yukarı; oturma aşağı +)
    assert abs(w(iP) - w0) / w0 < 5e-3
    for x in (1.0, 2.5, 5.0):
        i = iP + round(x / ag)
        wx = w0 * math.exp(-beta * x) * (math.cos(beta * x) + math.sin(beta * x))
        assert abs(w(i) - wx) < 5e-3 * w0, (x, w(i), wx)
    M0 = max(max(abs(m) for m in e["M"]) for e in r["elemanlar"])
    assert abs(M0 - P / (4 * beta)) / (P / (4 * beta)) < 1e-2
    # yay kuvvetleri toplamı = P (denge) ve p = k0·w
    assert yakin(sum(y["kuvvet"] for y in r["yaylar"]), P, 1e-9)


# ---------------------------------------------------------------------------
# bina ile birlikte çözüm: denge, simetri, rijit sınır
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tip", ["surekli", "radye"])
def test_denge_sigma_pA_esit_sigma_N(kucuk, tip):
    v = kucuk[tip].veri
    T = v["temel"]
    sA = sum(d["p_kNm2"] * d["A"] for d in T["dugumler"])
    toplam = v["yukler"]["toplam"]["G"] + v["yukler"]["toplam"]["Q"]          # temel öz ağırlığı G'de
    ya = T["yuk_akisi"]
    assert yakin(sA, toplam, 1e-4) and yakin(ya["zemin"], toplam, 1e-6)
    assert yakin(ya["kolon_N"] + ya["temel_W"], ya["zemin"], 1e-8) and abs(ya["fark"]) < 1e-6
    assert yakin(sum(k["N_servis"] for k in T["kolonlar"]), ya["kolon_N"], 1e-5)
    # korunum: Σ temel (tepki + yay) = toplam; kolon tabanı + temel öz ağırlığı = toplam
    for durum in ("G", "Q"):
        p = v["akis"]["korunum"][durum]
        assert yakin(p["yay"], p["toplam"], 1e-6) and abs(p["tepki"]) < 1e-6
        assert yakin(p["kolon_taban"] + p.get("temel_oz", 0.0), p["toplam"], 1e-6)
    assert yakin(T["model"]["W_temel"], v["akis"]["korunum"]["G"]["temel_oz"], 1e-9)
    # p = k0·w her düğümde
    k0 = v["bina"]["temeller"]["zemin"]["k0"]
    assert all(abs(d["p_kNm2"] - k0 * d["w_mm"] / 1000.0) < 1e-3 * max(1.0, d["p_kNm2"]) for d in T["dugumler"])
    assert yakin(T["model"]["yay_toplami"], k0 * T["model"]["taban_alani"], 1e-6)


def test_radye_oz_agirligi_ve_taban_alani(kucuk):
    T = kucuk["radye"].veri["temel"]
    pl = T["model"]["plak"]
    alan = (pl["X1"] - pl["X0"]) * (pl["Y1"] - pl["Y0"])
    assert yakin(pl["alan"], alan) and yakin(T["model"]["taban_alani"], alan) and yakin(sum(d["A"] for d in T["dugumler"]), alan, 1e-6)
    assert yakin(T["model"]["W_temel"], 25.0 * 0.8 * alan, 1e-6)       # γ_b·h·A (C30/37, h = 0,8 m varsayılan)


def test_surekli_kesisim_alani_bir_kez(kucuk):
    T = kucuk["surekli"].veri["temel"]
    m = T["model"]
    B = m["kesit"]["B"]
    uzunluk = sum(h["L"] for h in T["hatlar"])
    assert m["ortak_alan"] > 0 and yakin(m["taban_alani"], uzunluk * B - m["ortak_alan"], 1e-9)
    assert yakin(sum(d["A"] for d in T["dugumler"]), m["taban_alani"], 1e-6)


@pytest.mark.parametrize("tip", ["surekli", "radye"])
def test_simetrik_yukte_simetrik_basinc(tip):
    """Tek açıklıklı çerçeve (5 × 4 m, kare kolonlar, dört kenarda duvar) iki eksene göre simetriktir: p(X, Y) = p(5 − X, Y)
    = p(X, 4 − Y)."""
    v = yapi.bina_coz(bina_temelli("betonarme-tek-aciklik", tip), anlat=False).veri
    T = v["temel"]
    p = {(round(d["X"], 6), round(d["Y"], 6)): d["p_kNm2"] for d in T["dugumler"]}
    assert len(p) == len(T["dugumler"])
    olcek = max(abs(x) for x in p.values())
    for (X, Y), deger in p.items():
        for ayna in ((round(5.0 - X, 6), Y), (X, round(4.0 - Y, 6))):
            assert ayna in p and abs(p[ayna] - deger) < 1e-6 * olcek, (tip, X, Y, deger, p.get(ayna))
    assert T["p_maks"] > T["p_min"] > 0


def test_rijit_radye_duzgun_basinc():
    """Çok rijit plak (h = 4 m, yumuşak zemin): oturma her yerde aynı, basınç düzgün p = (ΣN + W)/A."""
    b = bina_temelli("betonarme-tek-aciklik", "radye", h=4.0, tasma=1.0, ag=0.5)
    b["temeller"]["zemin"]["k0"] = 2000
    v = yapi.bina_coz(b, anlat=False).veri
    T = v["temel"]
    ort = (v["yukler"]["toplam"]["G"] + v["yukler"]["toplam"]["Q"]) / T["model"]["taban_alani"]
    assert (T["p_maks"] - T["p_min"]) / ort < 2e-3
    assert abs(T["p_maks"] - ort) / ort < 2e-3
    # aynı binada ince radye kolon altlarında basıncı yoğunlaştırır
    b = bina_temelli("betonarme-tek-aciklik", "radye", h=0.3, tasma=1.0, ag=0.5)
    b["temeller"]["zemin"]["k0"] = 50000
    v2 = yapi.bina_coz(b, anlat=False).veri
    T2 = v2["temel"]
    ort2 = (v2["yukler"]["toplam"]["G"] + v2["yukler"]["toplam"]["Q"]) / T2["model"]["taban_alani"]
    assert (T2["p_maks"] - T2["p_min"]) / ort2 > 0.2


def test_surekli_kenar_basinci_ve_dönme_yayi():
    """yon = 'x': kolonların Y doğrultusundaki momenti tablayı yan yatırır; kenar basıncı k0·(w ± θ·B/2) ortalamadan büyük."""
    b = bina_temelli("betonarme-2kat-3x2", "surekli", yon="x")
    v = yapi.bina_coz(b, anlat=False).veri
    T = v["temel"]
    assert all("p_maks_kNm2" in d and d["p_maks_kNm2"] >= d["p_kNm2"] - 1e-9 >= d["p_min_kNm2"] - 2e-9 for d in T["dugumler"])
    assert T["p_maks"] >= max(d["p_kNm2"] for d in T["dugumler"])
    assert T["p_maks"] == pytest.approx(max(d["p_maks_kNm2"] for d in T["dugumler"]), rel=1e-4)
    assert all(h["yon"] == "x" for h in T["hatlar"]) and len(T["hatlar"]) == 2


# ---------------------------------------------------------------------------
# veri.temel şeması, tasarım ve anlatım
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tip", ["surekli", "radye"])
def test_veri_temel_semasi(kucuk, tip):
    r = kucuk[tip]
    v = r.veri
    T = v["temel"]
    json.dumps(T, allow_nan=False)
    for a in ("tip", "elemanlar", "dugumler", "p_maks", "p_min", "q_em", "DC_zemin", "oturma_maks_mm", "farkli_oturma", "tasarim",
              "uyarilar", "kolonlar", "yuk_akisi", "zemin_kontrolleri", "model", "en_buyuk_dc", "q_t", "q_o"):
        assert a in T, a
    assert T["tip"] == tip and T["q_em"] == v["bina"]["temeller"]["zemin"]["q_em"]
    assert all({"no", "X", "Y", "w_mm", "p_kNm2"} <= set(d) for d in T["dugumler"])
    assert yakin(T["DC_zemin"], T["p_maks"] / T["q_em"], 1e-4)
    assert T["oturma_maks_mm"] == pytest.approx(max(d["w_mm"] for d in T["dugumler"]), rel=1e-4)
    assert T["farkli_oturma"] >= 0 and T["farkli_oturma_metin"].startswith("1/")
    turler = {"surekli": {"temel-kirisi"}, "radye": {"radye-serit"}}[tip]
    assert {e["tur"] for e in T["elemanlar"]} == turler
    ag_el = {e["no"]: e for e in v["ag"]["elemanlar"]}
    assert all(ag_el[e["no"]]["tur"] == e["tur"] for e in T["elemanlar"])
    assert len(T["kolonlar"]) == sum(1 for c in v["bina"]["kolonlar"] if c["kat"] == 1)
    # zemin kontrolleri: TS 500 emniyet (servis) ve TBDY 16.8 (katsayılı) ayrı
    adlar = [k["ad"] for k in T["zemin_kontrolleri"]]
    assert any("TS 500" in a for a in adlar) and any("TBDY" in a for a in adlar)
    assert T["q_t"] == pytest.approx(T["q_k"] / 1.4, rel=1e-5)
    # tasarım kayıtları
    tt = {t["tur"] for t in T["tasarim"]}
    if tip == "surekli":
        assert {"temel-kirisi", "tabla"} <= tt
        for t in T["tasarim"]:
            if t["tur"] == "temel-kirisi":
                assert t["oneri_alt"] and t["oneri_ust"] and t["etriye"] and t["dc"] > 0
    else:
        assert {"radye-serit", "zimbalama"} <= tt
        z = [t for t in T["tasarim"] if t["tur"] == "zimbalama"]
        assert len(z) == len(T["kolonlar"]) and all(t["V_pr"] > 0 and t["u_p"] > 0 for t in z)
        assert {t["yon"] for t in T["tasarim"] if t["tur"] == "radye-serit"} == {"x", "y"}
    assert T["en_buyuk_dc"] == pytest.approx(max([t["dc"] for t in T["tasarim"]] + [k["dc"] for k in T["zemin_kontrolleri"]]), rel=1e-6)
    # anlatım: 13. adım Temel ve zemin (Winkler, yük akışı, TS 500 / TBDY maddeleri), Python 14
    md = "\n".join(str(b[1]) for b in r.anlatim.bloklar if b[0] == "md")
    for parca in ("13. Adım: Temel ve zemin", "14. Adım: Aynı hesap Python", "Winkler", "kolon → temel → zemin", "TS 500 md. 10.4.2",
                  "TBDY 2018 md. 16.8"):
        assert parca in md, parca
    if tip == "radye":
        assert "Zımbalama" in md and "TS 500 md. 8.3.1" in md
    assert "Σ yay kuvveti" in r.python_ciktisi and "[Hata" not in r.python_ciktisi


def test_radye_zimbalama_kolon_basina_el_hesabi(kucuk):
    """Kritik zımbalama kaydı: V_pd = N_d − p_d·A, V_pr = γ f_ctd u_p d (kayıttaki değerlerle yeniden)."""
    T = kucuk["radye"].veri["temel"]
    fctd = ts.beton_malzeme("C30/37")["fctd"]
    for z in (t for t in T["tasarim"] if t["tur"] == "zimbalama"):
        assert z["V_pd"] == pytest.approx(z["N_d"] - z["p_d"] * z["A_bolge"], rel=1e-4)
        assert z["V_pr"] == pytest.approx(z["gamma"] * fctd * 1000.0 * z["u_p"] * z["d"], rel=1e-4)
        assert z["d"] == pytest.approx(0.8 - tm.PAS)
        assert z["konum"] in ("iç", "kenar", "köşe")


def test_kombinasyon_temel_basinci(kucuk):
    r = kucuk["radye"]
    T = r.veri["temel"]
    g = yapi.kombinasyon_kisa(r.ic, "G")["temel"]
    q = yapi.kombinasyon_kisa(r.ic, "Q")["temel"]
    gq = yapi.kombinasyon_kisa(r.ic, "G+Q")["temel"]
    pg = {d["no"]: d["p_kNm2"] for d in g["dugumler"]}
    pq = {d["no"]: d["p_kNm2"] for d in q["dugumler"]}
    assert all(abs(d["p_kNm2"] - pg[d["no"]] - pq[d["no"]]) < 1e-3 for d in gq["dugumler"])        # doğrusallık
    assert gq["p_maks"] == pytest.approx(T["p_maks"], rel=1e-3)
    d14 = yapi.kombinasyon_kisa(r.ic, "1.4G+1.6Q")
    assert d14["temel"]["p_maks"] > gq["p_maks"]
    radye_el = {e["no"] for e in T["elemanlar"]}
    assert all(e.get("diyagram") is False and "M" not in e for e in d14["elemanlar"] if e["no"] in radye_el)


def test_yanit_kayitlari_ince(kucuk):
    """Radye şeritleri durumlarda diyagramsız; temel kirişleri 3 noktalı; temel yayları veri.durumlar'a yazılmaz."""
    for tip, r in kucuk.items():
        v = r.veri
        tur = {e["no"]: e["tur"] for e in v["ag"]["elemanlar"]}
        temel_dg = {d["no"] for d in v["temel"]["dugumler"]}
        for k in v["durumlar"].values():
            assert not any(y["dugum"] in temel_dg for y in k["yaylar"])
            for e in k["elemanlar"]:
                if tur[e["no"]] == "radye-serit":
                    assert e["diyagram"] is False and "uc_kuvvetleri" not in e
                elif tur[e["no"]] == "temel-kirisi" and k["diyagram"]:
                    assert len(e["x"]) == 3 and len(e["M"]) == 3
        assert all(e["no"] not in tur or tur[e["no"]] != "radye-serit" for e in v["zarf"]["elemanlar"])


def test_tekil_temel_ozeti_davranis_degismez():
    v = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"), anlat=False).veri
    T = v["temel"]
    assert T["tip"] == "tekil" and T["elemanlar"] == [] and T["DC_zemin"] == pytest.approx(max(t["DC"] for t in v["akis"]["temeller"]), rel=1e-4)
    assert all(e["tur"] in ("kolon", "kiris") for e in v["ag"]["elemanlar"])


# ---------------------------------------------------------------------------
# ağ aralığı, SD sınırı, öğretici hatalar
# ---------------------------------------------------------------------------
def test_ag_araligi_sd_sinirina_gore_buyutulur():
    b = bina_temelli("betonarme-3kat-3x3", "radye", ag=0.5)
    v = yapi.bina_coz(b, anlat=False).veri
    T = v["temel"]
    assert T["model"]["ag"] > 0.5 and any("büyütüldü" in u for u in T["uyarilar"])
    assert any("Temel: " in u and "büyütüldü" in u for u in v["ozet"]["uyarilar"])
    n_temel = len(T["dugumler"])
    serbest = 6 * sum(1 for d in v["ag"]["dugumler"] if not d["efendi"]) - 3 * n_temel
    assert serbest <= yapi.EN_FAZLA_SD
    # verilmezse (otomatik) not olarak düşülür
    b = yapi.bina_sablon("betonarme-3kat-3x3")
    b["temeller"]["tip"] = "radye"
    T = yapi.bina_coz(b, anlat=False).veri["temel"]
    assert T["model"]["ag"] > 0.5 and not any("büyütüldü" in u for u in T["uyarilar"]) and any("büyütüldü" in n for n in T["notlar"])


@pytest.mark.parametrize("degisim, desen", [
    ({"tip": "kazik"}, "tanımsız"),
    ({"tip": "surekli", "surekli": {"yon": "z"}}, "yon"),
    ({"tip": "surekli", "surekli": {"B": 0.4, "b_govde": 0.5}}, "gövde tabladan geniş"),
    ({"tip": "surekli", "surekli": {"h_tabla": 1.2, "h_govde": 1.0}}, "TOPLAM"),
    ({"tip": "surekli", "surekli": {"yon": "x", "akslar": ["1"]}}, "altında temel kirişi yok"),
    ({"tip": "surekli", "surekli": {"yon": "x", "akslar": ["A"]}}, "bilinmeyen aks"),
    ({"tip": "surekli", "surekli": {"B": 5.0}}, "tablalar üst üste"),
    ({"tip": "surekli", "surekli": {"ag": 0.01}}, "çok küçük"),
    ({"tip": "radye", "radye": {"kiris": {"b": 0.5, "h": 0.5}}}, "plak kalınlığından"),
    ({"tip": "radye", "radye": {"h": -1}}, "pozitif"),
    ({"tip": "radye", "radye": {"tasma": -0.5}}, "negatif"),
    ({"tip": "radye", "radye": {"yatay": "yay"}}, "kh_oran"),
])
def test_ogretici_hatalar(degisim, desen):
    b = yapi.bina_sablon("betonarme-2kat-3x2")
    b["temeller"].update(degisim)
    with pytest.raises(mo.MatrisHatasi, match=desen):
        yapi.bina_coz(b, anlat=False)


def test_yatay_yay_secenegi_ve_kirisli_radye():
    b = bina_temelli("betonarme-tek-aciklik", "radye", yatay="yay", kh_oran=0.3, kiris={"b": 0.4, "h": 1.0}, h=0.4)
    v = yapi.bina_coz(b, anlat=False).veri
    T = v["temel"]
    assert T["model"]["yatay"] == "yay" and T["model"]["kiris"] == {"b": 0.4, "h": 1.0}
    assert {"temel-kirisi", "radye-serit"} == {e["tur"] for e in T["elemanlar"]}
    assert any(t["tur"] == "temel-kirisi" for t in T["tasarim"]) and not any(t["tur"] == "zimbalama" for t in T["tasarim"])
    sA = sum(d["p_kNm2"] * d["A"] for d in T["dugumler"])
    assert yakin(sA, v["yukler"]["toplam"]["G"] + v["yukler"]["toplam"]["Q"], 1e-4)


# ---------------------------------------------------------------------------
# şablonlar ve köprü
# ---------------------------------------------------------------------------
def test_sablonlar_cozulur(sablonlar):
    s = sablonlar["betonarme-3kat-surekli-temel"].veri
    assert s["temel"]["tip"] == "surekli" and s["bina"]["temeller"]["surekli"]["yon"] == "xy"
    r = sablonlar["betonarme-4kat-radye"].veri
    assert r["temel"]["tip"] == "radye" and r["bina"]["temeller"]["radye"]["h"] == 0.7
    for v in (s, r):
        T = v["temel"]
        assert T["DC_zemin"] < 1.0 and T["en_buyuk_dc"] <= 1.0 and T["uyarilar"] == []
        assert all(t["durum"] == "yeterli" for t in T["tasarim"])
        assert v["deprem"] and any("E" in (k.get("q_o_kombinasyon") or "") for k in [T])        # TBDY 16.8: deprem birleşimi belirleyici
        assert len(json.dumps(v, ensure_ascii=False)) < 2_000_000
    aks_kat = [x["ad"] for x in yapi.bina_sablonlar() if int(yapi.BINA_SABLONLARI[x["ad"]].get("surum", 1)) < 3]
    assert aks_kat[-2:] == ["betonarme-3kat-surekli-temel", "betonarme-4kat-radye"]


def test_kopru_bina_coz_ve_kombinasyon():
    ozellik = importlib.util.spec_from_file_location("web_kopru_temel_testi", PROJE / "docs" / "web_kopru.py")
    kopru = importlib.util.module_from_spec(ozellik)
    ozellik.loader.exec_module(kopru)
    b = bina_temelli("betonarme-tek-aciklik", "surekli")
    y = json.loads(kopru.calistir(json.dumps({"islem": "bina_coz", "girdi": {"bina": b}})))
    assert y["hata"] is None and y["veri"]["temel"]["tip"] == "surekli"
    z = json.loads(kopru.calistir(json.dumps({"islem": "bina_kombinasyon",
                                               "girdi": {"cozum_kimligi": y["veri"]["cozum_kimligi"], "ad": "1.4G+1.6Q"}})))
    assert z["hata"] is None and z["sonuc"]["temel"]["p_maks"] > y["veri"]["temel"]["p_maks"]


def test_web_dosyalari_temel_modulunu_tasir():
    assert '"temel.py"' in (PROJE / "web_yap.py").read_text(encoding="utf-8")
    assert '"temel.py"' in (PROJE / "docs" / "motor.worker.js").read_text(encoding="utf-8")
    assert '"./temel.py"' in (PROJE / "docs" / "sw.js").read_text(encoding="utf-8")
