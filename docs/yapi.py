# -*- coding: utf-8 -*-
"""Bina analizi ve yük akışı modülü (Matris Öğren): döşeme → kiriş → kolon → temel → zemin.

Kullanım::

    import yapi
    r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))   # sözlük ya da JSON metni
    r.deger      # G durumu yer değiştirme vektörü (motor SD sırası, sympy Matrix)
    r.veri       # yapılı sonuçlar (aşağıdaki şema; bina koordinatında)
    r.anlatim    # 13 adımlı anlatım (md / math / sema / kod blokları; 12. adım kesit tahkikleri)
    yapi.yuk_yolu(bina, r.veri, {"tur": "doseme", "no": 1, "durum": "G"})   # tek nesneden zemine yük zinciri
    yapi.kombinasyon_kisa(r.ic, "G+Q+0.2S+EX++0.3EY++0.3EZ")              # tek kombinasyonun tam kaydı (tembel)
    yapi.deprem_onizleme(bina)                                             # TBDY spektrum, V_tE, F_i (çözümsüz)
    r.veri["tasarim"]                                                      # kesit tahkikleri (tasarim.py varsa; §11)
    yapi.eleman_tasarim(r.ic, "kolon", 1)                                  # tek elemanın anlatımlı tahkiki, N–M eğrileri

Bina veri modeli (``tur: "bina"``, ``surum: 1``; birimler kN, m, kN/m², kN/m³; MPa yalnız malzeme kartında)::

    {"baslik", "sistem": "betonarme" | "celik",
     "akslar": {"x": [{"ad": "A", "konum": 0}, ...], "y": [{"ad": "1", "konum": 0}, ...]},
     "katlar": [{"no": 0, "ad": "Temel", "kot": 0.0}, {"no": 1, "kot": 3.0}, ...],
     "malzemeler": {"C30": {"kutuphane": "C30/37"}, "S275": {"kutuphane": "S275"}},
     "kesitler": {"S40x40": {"tip": "dikdortgen", "b": 0.4, "h": 0.4, "malzeme": "C30"},
                  "IPE300": {"tip": "profil", "profil": "IPE 300", "malzeme": "S275"}},
     "kolonlar": [{"no": 1, "aks": ["A", "1"], "kat": 1, "kesit": "S40x40", "yon": "x"}],
     "kirisler": [{"no": 1, "kat": 1, "bas": ["A", "1"], "son": ["B", "1"], "kesit": "K25x50", "duvar": "tugla19", "duvar_h": null}],
     "dosemeler": [{"no": 1, "kat": 1, "kose": [["A", "1"], ["B", "2"]], "h": 0.14, "kullanim": "konut",
                    "g_ek": 1.5, "q": null, "dagitim": "otomatik"}],
     "duvarlar": {"tugla19": {"kutuphane": "tugla-delikli-19"}},
     "ek_yukler": [{"tur": "kiris", "kiris": 1, "durum": "G", "q": 2.0},
                   {"tur": "dugum", "aks": ["B", "2"], "kat": 2, "durum": "Q", "FZ": -10},
                   {"tur": "doseme", "doseme": 1, "g": 0.5}],
     "temeller": {"tip": "tekil", "varsayilan": {"B": 1.6, "L": 1.6, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000},
                  "mesnet": "ankastre" | "mafsal" | "elastik", "ozel": [{"aks": ["B", "1"], "B": 2.0, "L": 2.0}]},
     "yuk_durumlari": {"G": {"acik": true}, "Q": {"acik": true}, "S": {"acik": false, "bolge": 3, "rakim": 0, "mu": 0.8},
                       "W": {"acik": false, "C": 1.2}, "E": {"acik": false}},
     "deprem": {"SS": 1.0, "S1": 0.3, "SS_DD3": 0.4, "S1_DD3": 0.12, "zemin_sinifi": "ZC", "BKS": 3, "I": 1.0,
                "tasiyici": "betonarme-cerceve-yuksek", "R": 8, "D": 3, "n": 0.3, "Ct": 0.1, "periyot": "ampirik" | "rayleigh",
                "diyafram": "rijit" | "esnek", "dismerkezlik": 0.05, "dolgu": "bitisik" | "esnek"},
     "kombinasyon_kumesi": "ts500" | "cythye_ydkt" | "cythye_gkt",
     "analiz": {"catlamis_rijitlik": null (betonarme + deprem: true, TBDY 4.5.8.1), "kiris_oz": "net" | "brut", "celik_Lb": "otomatik" | "boy",
                "diyagram_nokta": 11, "gosterilecek": null}}

Koordinatlar: **bina** sistemi X sağa (harfli akslar), Y plan derinliği (sayılı akslar), Z yukarı (kot). Motor
(``cerceve3b``) Y yukarı çalışır; dönüşüm tek yerdedir: ``_motor_koordinat`` / ``_bina_vek``.
Çıktı şeması ``bina_coz`` belgesinde ve KULLANIM.md 3.9'da anlatılır.
"""
from __future__ import annotations

import copy
import importlib
import json
import math
from types import SimpleNamespace

import sympy as sp

import matris_ogren as mo
import sonlu_eleman as se
import yapi_veri as yv

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

__version__ = "0.1.0"
MatrisHatasi = mo.MatrisHatasi

EN_FAZLA_AKS = 12
EN_FAZLA_KAT = 12
EN_FAZLA_SD = 1500
DIYAGRAM_NOKTA = 11
YANIT_BUTCESI = 1_050_000   # veri JSON'u (karakter) bu bütçeyi aşacaksa varsayılan tam kombinasyon da tembel bırakılır
GAMMA_BA = yv.TS498_BIRIM_AGIRLIK["betonarme"]["deger"]   # 25 kN/m³
_YON_AD = {"x": "X (güçlü eksen X doğrultusunda çalışır)", "y": "Y (güçlü eksen Y doğrultusunda çalışır)"}
_KENAR_AD = {"alt": "güney (küçük Y)", "ust": "kuzey (büyük Y)", "sol": "batı (küçük X)", "sag": "doğu (büyük X)"}


# ============================================================================
# Koordinat dönüşümü (TEK yer): bina (X sağa, Y derinlik, Z yukarı) ↔ motor cerceve3b (x_m, y_m yukarı, z_m)
# ============================================================================
def _motor_koordinat(X, Y, Z):
    """Bina → motor: x_m = X, y_m = Z, z_m = −Y (sağ el korunur). Vektörler için de aynı kural."""
    return float(X), float(Z), -float(Y)


def _bina_vek(v):
    """Motor vektörü (vx, vy, vz)_m → bina (X, Y, Z) = (vx, −vz, vy). Kuvvet, moment, yer değiştirme, dönme için."""
    return float(v[0]), -float(v[2]), float(v[1])


def _motor_vek(v):
    """Bina vektörü (X, Y, Z) → motor (x_m, y_m, z_m) = (X, Z, −Y)."""
    return float(v[0]), float(v[2]), -float(v[1])


def _bina_6(v):
    """Altı bileşen (öteleme + dönme) motor → bina."""
    a, b = _bina_vek(v[:3]), _bina_vek(v[3:6])
    return [a[0], a[1], a[2], b[0], b[1], b[2]]


# ============================================================================
# Küçük yardımcılar
# ============================================================================
def _r(x):
    """JSON'a yazılacak sayı: 10 anlamlı basamak (yanıt boyutu; bağıl hata < 1e-9)."""
    x = float(x)
    if x == 0.0 or x != x:
        return 0.0
    return float(f"{x:.10g}")


def _r6(x):
    """Diyagram dizileri için 6 anlamlı basamak (yanıt boyutu; uç kuvvetleri ve u 10 basamak kalır)."""
    x = float(x)
    if x == 0.0 or x != x:
        return 0.0
    return float(f"{x:.6g}")


def _r5(x):
    """Yalnız uç kuvvetli (ince) durumlar ve görüntü tabloları için 5 anlamlı basamak (yanıt boyutu; bağıl hata ≤ 5e-6)."""
    x = float(x)
    if x == 0.0 or x != x:
        return 0.0
    return float(f"{x:.5g}")


def _f(x, b=2):
    """Anlatım tablosu sayısı: en çok b ondalık, sondaki sıfırlar atılır."""
    s = f"{float(x):.{b}f}"
    if "." in s:                      # yalnız ondalık kısımdaki sondaki sıfırlar atılır (30 → "30", 2.50 → "2.5")
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _tablo(basliklar, satirlar):
    return se._tablo(basliklar, satirlar)


def _sayi(v, ad, pozitif=False, sifir_olur=True):
    if isinstance(v, bool) or v is None or (isinstance(v, str) and not v.strip()):
        raise MatrisHatasi(f"{ad} verilmedi (sayı bekleniyor).")
    try:
        x = float(sp.sympify(v)) if isinstance(v, str) else float(v)
    except (TypeError, ValueError, AttributeError):
        raise MatrisHatasi(f"{ad} sayı olmalı (girilen: {v!r}).") from None
    if x != x or x in (float("inf"), float("-inf")):
        raise MatrisHatasi(f"{ad} sonlu bir sayı olmalı (girilen: {v!r}).")
    if pozitif and (x < 0 or (x == 0 and not sifir_olur)):
        raise MatrisHatasi(f"{ad} pozitif olmalı (girilen: {v!r}).")
    return x


def _tam(v, ad):
    try:
        x = int(v)
    except (TypeError, ValueError):
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {v!r}).") from None
    if isinstance(v, float) and v != x:
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {v!r}).")
    return x


def _aks_cifti(v, ad, B):
    """[ax, ay] → (ix, iy) aks sıraları."""
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise MatrisHatasi(f"{ad}: aks adresi iki öğeli olmalı, örn. [\"B\", \"2\"] (girilen: {v!r}).")
    ax, ay = str(v[0]).strip(), str(v[1]).strip()
    if ax not in B.ax:
        raise MatrisHatasi(f"{ad}: {ax!r} diye bir X aksı yok. Tanımlı X aksları: {', '.join(B.ax)}.")
    if ay not in B.ay:
        raise MatrisHatasi(f"{ad}: {ay!r} diye bir Y aksı yok. Tanımlı Y aksları: {', '.join(B.ay)}.")
    return B.ax[ax], B.ay[ay]


# ============================================================================
# Malzeme ve kesit kartları
# ============================================================================
def _malzeme(ad, kayit):
    """Kütüphane kaydını (C30/37, S275, B420C) kN/m² birimli kartta çözümler; alanlar elle de verilebilir."""
    if not isinstance(kayit, dict):
        raise MatrisHatasi(f"Malzeme {ad!r} bir sözlük olmalı: {{\"kutuphane\": \"C30/37\"}}.")
    anahtar = str(kayit.get("kutuphane") or ad).strip()
    kart = None
    for tablo in (yv.BETONLAR, yv.CELIKLER, yv.DONATILAR):
        if anahtar in tablo:
            kart = tablo[anahtar]
            break
    if kart is None:
        secenek = ", ".join(list(yv.BETONLAR) + list(yv.CELIKLER) + list(yv.DONATILAR))
        raise MatrisHatasi(f"Malzeme {ad!r}: kütüphanede {anahtar!r} yok. Seçenekler: {secenek}.")
    m = {"ad": ad, "kutuphane": anahtar, "tur": kart["tur"], "kaynak": kart["kaynak"], "dogrulandi": kart["dogrulandi"]}
    if kart["tur"] == "beton":
        m["E_MPa"] = float(kayit.get("E", kart["Ec"]))
        m["G_MPa"] = kart["G_oran"] * m["E_MPa"]
        m["fck"] = kart["fck"]
        m["fctk"] = kart["fctk"]
        m["gamma"] = float(kayit.get("gamma", kart["gamma"]))
        m["nu"] = kart["nu"]
    elif kart["tur"] == "celik":
        m["E_MPa"] = float(kayit.get("E", kart["E"]))
        m["G_MPa"] = float(kayit.get("G", kart["G"]))
        m["Fy"] = kart["Fy"]
        m["Fu"] = kart["Fu"]
        m["gamma"] = float(kayit.get("gamma", kart["gamma"]))
        m["nu"] = kart["nu"]
    else:
        m["E_MPa"] = float(kart["Es"])
        m["G_MPa"] = m["E_MPa"] / 2.6
        m["fyk"] = kart["fyk"]
        m["gamma"] = 78.5
    m["E"] = m["E_MPa"] * 1000.0      # kN/m²
    m["G"] = m["G_MPa"] * 1000.0
    return m


def _kesit_ozellikleri(ad, kayit, malzemeler):
    """Kesit kartı: dikdörtgen (b, h) → A, I_guclu = b·h³/12, I_zayif = h·b³/12, J ≈ β·c³·a, Wpl = b·h²/4, Wel = b·h²/6;
    profil → katalog değerleri (cm → m). I_guclu, h'nin (yüksekliğin) derinlik olduğu eğilmedir."""
    if not isinstance(kayit, dict):
        raise MatrisHatasi(f"Kesit {ad!r} bir sözlük olmalı: {{\"tip\": \"dikdortgen\", \"b\": 0.25, \"h\": 0.5, \"malzeme\": \"C30\"}}.")
    tip = str(kayit.get("tip", "dikdortgen")).strip().lower()
    mad = str(kayit.get("malzeme", "")).strip()
    if mad not in malzemeler:
        raise MatrisHatasi(f"Kesit {ad!r}: malzeme {mad!r} 'malzemeler' sözlüğünde yok. Tanımlı: {', '.join(malzemeler) or '(yok)'}.")
    m = malzemeler[mad]
    k = {"ad": ad, "tip": tip, "malzeme": mad, "E": m["E"], "G": m["G"], "gamma": m["gamma"]}
    if tip == "dikdortgen":
        b = _sayi(kayit.get("b"), f"Kesit {ad!r}: b (genişlik, m)", pozitif=True, sifir_olur=False)
        h = _sayi(kayit.get("h"), f"Kesit {ad!r}: h (yükseklik, m)", pozitif=True, sifir_olur=False)
        if b > 5 or h > 5:
            raise MatrisHatasi(f"Kesit {ad!r}: b = {b}, h = {h} m çok büyük; kesit boyutları metre girilir (25 cm → 0.25).")
        a, c = max(b, h), min(b, h)
        beta = 1.0 / 3.0 - 0.21 * (c / a) * (1.0 - c ** 4 / (12.0 * a ** 4))
        k.update({"b": b, "h": h, "A": b * h, "I_guclu": b * h ** 3 / 12.0, "I_zayif": h * b ** 3 / 12.0,
                  "J": beta * c ** 3 * a, "beta": beta, "Wpl": b * h ** 2 / 4.0, "Wel": b * h ** 2 / 6.0,
                  "profil": None, "donati": kayit.get("donati"), "pas": kayit.get("pas", 0.03), "dogrulandi": True})
    elif tip == "profil":
        pad = str(kayit.get("profil", "")).strip()
        pad_n = pad.upper().replace("  ", " ")
        if pad_n and " " not in pad_n:
            for on in ("IPE", "HEA", "HEB"):
                if pad_n.startswith(on):
                    pad_n = on + " " + pad_n[len(on):]
        if pad_n not in yv.PROFILLER:
            raise MatrisHatasi(f"Kesit {ad!r}: profil {pad!r} tabloda yok. IPE 80…600, HEA 100…600, HEB 100…600 "
                               "yazılabilir (örn. \"IPE 300\").")
        p = yv.PROFILLER[pad_n]
        k.update({"b": p["b"] / 1000.0, "h": p["h"] / 1000.0, "A": p["A"] * 1e-4, "I_guclu": p["Iy"] * 1e-8,
                  "I_zayif": p["Iz"] * 1e-8, "J": p["It"] * 1e-8, "Wpl": p["Wply"] * 1e-6, "Wel": p["Wely"] * 1e-6,
                  "profil": pad_n, "g_kg": p["g"], "dogrulandi": p["dogrulandi"]})
    else:
        raise MatrisHatasi(f"Kesit {ad!r}: tip {tip!r} tanımsız; 'dikdortgen' ya da 'profil' olmalı.")
    return k


def _eleman_atalet(kesit, tur, yon="x"):
    """Motor Iy_m / Iz_m eşlemesi (§2). Kiriş: Iz_m = I_guclu (h düşey). Kolon: yon 'x' → Iz_m = I_guclu
    (bina Y ekseni etrafında eğilme = X yönünde ötelenme), yon 'y' → Iy_m = I_guclu."""
    if tur == "kiris" or yon == "x":
        return kesit["I_zayif"], kesit["I_guclu"]
    return kesit["I_guclu"], kesit["I_zayif"]


# ============================================================================
# Bina modelini okuma ve doğrulama
# ============================================================================
def _bina_oku(bina):
    if isinstance(bina, str):
        try:
            bina = json.loads(bina)
        except ValueError as e:
            raise MatrisHatasi(f"Bina JSON olarak okunamadı: {e}") from None
    if not isinstance(bina, dict):
        raise MatrisHatasi('Bina bir sözlük (ya da JSON metni) olmalı: {"tur": "bina", "akslar": {...}, "katlar": [...], ...}.')
    if bina.get("tur") not in (None, "bina") or ("tip" in bina and "akslar" not in bina):
        raise MatrisHatasi(f"Bu bir bina modeli değil (tur = {bina.get('tur', bina.get('tip'))!r}). "
                           "Sonlu eleman modelleri (kafes, çerçeve…) için se_coz kullanın.")
    B = SimpleNamespace(ham=bina, uyarilar=[])
    B.baslik = str(bina.get("baslik") or "Bina modeli")
    B.aciklama = str(bina.get("aciklama") or "")
    B.sistem = str(bina.get("sistem") or "betonarme").strip().lower()
    if B.sistem not in ("betonarme", "celik"):
        raise MatrisHatasi(f"sistem {B.sistem!r} tanımsız; 'betonarme' ya da 'celik' olmalı.")
    birim = bina.get("birim") if isinstance(bina.get("birim"), dict) else {}
    B.birim = {"kuvvet": str(birim.get("kuvvet", "kN")), "uzunluk": str(birim.get("uzunluk", "m"))}
    if B.birim != {"kuvvet": "kN", "uzunluk": "m"}:
        raise MatrisHatasi("Bina modülü kN ve m ile çalışır (TS 498 yükleri kN/m² ile girilir); birim alanını kN, m yapın.")

    # --- akslar ---
    akslar = bina.get("akslar")
    if not isinstance(akslar, dict) or not isinstance(akslar.get("x"), list) or not isinstance(akslar.get("y"), list):
        raise MatrisHatasi('Akslar eksik: "akslar": {"x": [{"ad": "A", "konum": 0}, ...], "y": [{"ad": "1", "konum": 0}, ...]}.')
    B.akslar = {}
    for yon in ("x", "y"):
        liste = []
        for k, a in enumerate(akslar[yon], start=1):
            if not isinstance(a, dict):
                raise MatrisHatasi(f"{yon} aksı {k}: sözlük olmalı ({{\"ad\": \"A\", \"konum\": 0}}).")
            ad = str(a.get("ad", "")).strip()
            if not ad:
                raise MatrisHatasi(f"{yon} aksı {k}: 'ad' boş.")
            liste.append({"ad": ad, "konum": _sayi(a.get("konum"), f"{yon} aksı {ad!r}: konum")})
        if not liste:
            raise MatrisHatasi(f"{yon} yönünde en az bir aks olmalı.")
        if len(liste) > EN_FAZLA_AKS:
            raise MatrisHatasi(f"{yon} yönünde {len(liste)} aks var; en fazla {EN_FAZLA_AKS} (modeli küçültün).")
        liste.sort(key=lambda a: a["konum"])
        adlar = [a["ad"] for a in liste]
        if len(set(adlar)) != len(adlar):
            raise MatrisHatasi(f"{yon} aks adları tekrarlı: {adlar}. Her aks adı bir kez kullanılmalı.")
        for a, b in zip(liste, liste[1:]):
            if b["konum"] - a["konum"] < 0.3:
                raise MatrisHatasi(f"{yon} aksları {a['ad']} ve {b['ad']} arası {b['konum'] - a['konum']:.2f} m; "
                                   "akslar en az 0,3 m aralıklı ve farklı konumda olmalı.")
        B.akslar[yon] = liste
    B.ax = {a["ad"]: i for i, a in enumerate(B.akslar["x"])}
    B.ay = {a["ad"]: i for i, a in enumerate(B.akslar["y"])}
    B.xk = [a["konum"] for a in B.akslar["x"]]
    B.yk = [a["konum"] for a in B.akslar["y"]]
    B.xad = [a["ad"] for a in B.akslar["x"]]
    B.yad = [a["ad"] for a in B.akslar["y"]]

    # --- katlar ---
    katlar = bina.get("katlar")
    if not isinstance(katlar, list) or len(katlar) < 2:
        raise MatrisHatasi('Katlar eksik: "katlar": [{"no": 0, "ad": "Temel", "kot": 0}, {"no": 1, "kot": 3}, ...] '
                           "(temel seviyesi kat 0 ve en az bir kat).")
    B.katlar = []
    for k, kt in enumerate(katlar):
        if not isinstance(kt, dict):
            raise MatrisHatasi(f"Kat {k}: sözlük olmalı ({{\"no\": 1, \"kot\": 3.0}}).")
        no = _tam(kt.get("no", k), f"Kat {k}: no")
        B.katlar.append({"no": no, "ad": str(kt.get("ad") or (f"{no}. kat" if no else "Temel")),
                         "kot": _sayi(kt.get("kot"), f"Kat {no}: kot (m)")})
    B.katlar.sort(key=lambda kt: kt["no"])
    if [kt["no"] for kt in B.katlar] != list(range(len(B.katlar))):
        raise MatrisHatasi(f"Kat numaraları 0'dan başlayıp ardışık olmalı (temel = 0): {[kt['no'] for kt in B.katlar]}.")
    if len(B.katlar) - 1 > EN_FAZLA_KAT:
        raise MatrisHatasi(f"{len(B.katlar) - 1} kat var; en fazla {EN_FAZLA_KAT} (modeli küçültün).")
    for a, b in zip(B.katlar, B.katlar[1:]):
        b["h"] = b["kot"] - a["kot"]
        if b["h"] < 2.0:
            raise MatrisHatasi(f"Kat {b['no']} yüksekliği {b['h']:.2f} m; kotlar artan olmalı ve kat yüksekliği en az 2 m.")
    B.katlar[0]["h"] = 0.0
    B.kat = {kt["no"]: kt for kt in B.katlar}
    B.nk = len(B.katlar) - 1

    # --- malzemeler, kesitler, duvarlar ---
    mal = bina.get("malzemeler")
    if not isinstance(mal, dict) or not mal:
        raise MatrisHatasi('Malzeme yok: "malzemeler": {"C30": {"kutuphane": "C30/37"}} gibi en az bir malzeme tanımlayın.')
    B.malzemeler = {str(ad): _malzeme(str(ad), kayit) for ad, kayit in mal.items()}
    kes = bina.get("kesitler")
    if not isinstance(kes, dict) or not kes:
        raise MatrisHatasi('Kesit yok: "kesitler": {"K25x50": {"tip": "dikdortgen", "b": 0.25, "h": 0.5, "malzeme": "C30"}}.')
    B.kesitler = {str(ad): _kesit_ozellikleri(str(ad), kayit, B.malzemeler) for ad, kayit in kes.items()}
    B.duvarlar = {}
    for ad, kayit in (bina.get("duvarlar") or {}).items():
        if not isinstance(kayit, dict):
            raise MatrisHatasi(f"Duvar {ad!r} bir sözlük olmalı: {{\"kutuphane\": \"tugla-delikli-19\"}}.")
        if "kutuphane" in kayit:
            anahtar = str(kayit["kutuphane"]).strip()
            if anahtar not in yv.DUVARLAR:
                raise MatrisHatasi(f"Duvar {ad!r}: kütüphanede {anahtar!r} yok. Seçenekler: {', '.join(yv.DUVARLAR)}.")
            d = yv.DUVARLAR[anahtar]
            B.duvarlar[str(ad)] = {"ad": str(ad), "kutuphane": anahtar, "deger": d["deger"], "aciklama": d["ad"],
                                   "kaynak": d["kaynak"], "dogrulandi": d["dogrulandi"]}
        else:
            B.duvarlar[str(ad)] = {"ad": str(ad), "kutuphane": None, "aciklama": str(kayit.get("ad", ad)),
                                   "deger": _sayi(kayit.get("kN_m2"), f"Duvar {ad!r}: kN_m2 (duvar alanı ağırlığı)", pozitif=True),
                                   "kaynak": "kullanıcı değeri", "dogrulandi": True}

    # --- kolonlar ---
    B.kolonlar, B.kolon_key = [], {}
    for k, c in enumerate(bina.get("kolonlar") or [], start=1):
        if not isinstance(c, dict):
            raise MatrisHatasi(f"{k}. kolon sözlük olmalı.")
        no = _tam(c.get("no", k), f"{k}. kolon: no")
        ix, iy = _aks_cifti(c.get("aks"), f"Kolon {no}", B)
        kat = _tam(c.get("kat", 1), f"Kolon {no}: kat")
        if not 1 <= kat <= B.nk:
            raise MatrisHatasi(f"Kolon {no}: kat {kat} yok; kolon katı 1…{B.nk} arasında olmalı (kat k kolonu kot_{{k-1}} ile kot_k arasındadır).")
        kad = str(c.get("kesit", "")).strip()
        if kad not in B.kesitler:
            raise MatrisHatasi(f"Kolon {no}: kesit {kad!r} 'kesitler' sözlüğünde yok. Tanımlı: {', '.join(B.kesitler)}.")
        yon = str(c.get("yon", "x")).strip().lower()
        if yon not in ("x", "y"):
            raise MatrisHatasi(f"Kolon {no}: yon {yon!r} tanımsız; 'x' ya da 'y' (güçlü eksenin çalıştığı doğrultu).")
        if (ix, iy, kat) in B.kolon_key:
            raise MatrisHatasi(f"Kolon {no}: {B.xad[ix]}{B.yad[iy]} aksında kat {kat} için ikinci kolon (kolon {B.kolon_key[(ix, iy, kat)]['no']}).")
        ks = B.kesitler[kad]
        Iy_m, Iz_m = _eleman_atalet(ks, "kolon", yon)
        bX, bY = (ks["h"], ks["b"]) if yon == "x" else (ks["b"], ks["h"])
        kol = {"no": no, "aks": [B.xad[ix], B.yad[iy]], "ix": ix, "iy": iy, "kat": kat, "kesit": kad, "yon": yon,
               "bX": bX, "bY": bY, "L": B.kat[kat]["h"], "kot_alt": B.kat[kat - 1]["kot"], "kot_ust": B.kat[kat]["kot"],
               "A": ks["A"], "Iy_m": Iy_m, "Iz_m": Iz_m, "J": ks["J"], "E": ks["E"], "G": ks["G"], "gamma": ks["gamma"],
               "malzeme": ks["malzeme"], "adres": f"S-{B.xad[ix]}{B.yad[iy]}/k{kat}"}
        B.kolonlar.append(kol)
        B.kolon_key[(ix, iy, kat)] = kol
    if not B.kolonlar:
        raise MatrisHatasi("Bina modelinde kolon yok; en az bir kolon tanımlayın (kolon tabanları mesnet olur).")

    # --- kirişler ---
    B.kirisler, B.kiris_parca = [], {}
    for k, kr in enumerate(bina.get("kirisler") or [], start=1):
        if not isinstance(kr, dict):
            raise MatrisHatasi(f"{k}. kiriş sözlük olmalı.")
        no = _tam(kr.get("no", k), f"{k}. kiriş: no")
        kat = _tam(kr.get("kat", 1), f"Kiriş {no}: kat")
        if not 1 <= kat <= B.nk:
            raise MatrisHatasi(f"Kiriş {no}: kat {kat} yok; kiriş katı 1…{B.nk} (o katın döşeme seviyesi).")
        bx, by = _aks_cifti(kr.get("bas"), f"Kiriş {no}: bas", B)
        sx, sy = _aks_cifti(kr.get("son"), f"Kiriş {no}: son", B)
        if bx == sx and by == sy:
            raise MatrisHatasi(f"Kiriş {no}: başlangıç ve bitiş aynı aks kesişimi ({B.xad[bx]}{B.yad[by]}).")
        if bx != sx and by != sy:
            raise MatrisHatasi(f"Kiriş {no}: uçları ({B.xad[bx]}{B.yad[by]} → {B.xad[sx]}{B.yad[sy]}) aynı aks çizgisi üzerinde değil; "
                               "kiriş ya aynı sayılı aks boyunca (X yönü) ya da aynı harfli aks boyunca (Y yönü) gider.")
        kad = str(kr.get("kesit", "")).strip()
        if kad not in B.kesitler:
            raise MatrisHatasi(f"Kiriş {no}: kesit {kad!r} 'kesitler' sözlüğünde yok. Tanımlı: {', '.join(B.kesitler)}.")
        duvar = kr.get("duvar")
        if duvar not in (None, ""):
            duvar = str(duvar).strip()
            if duvar not in B.duvarlar:
                raise MatrisHatasi(f"Kiriş {no}: duvar {duvar!r} 'duvarlar' sözlüğünde yok. Tanımlı: {', '.join(B.duvarlar) or '(yok)'}.")
        else:
            duvar = None
        ks = B.kesitler[kad]
        if by == sy:
            yon, sabit, i0, i1 = "x", by, min(bx, sx), max(bx, sx)
            konum = B.xk
        else:
            yon, sabit, i0, i1 = "y", bx, min(by, sy), max(by, sy)
            konum = B.yk
        Iy_m, Iz_m = _eleman_atalet(ks, "kiris")
        if yon == "x":
            bas_ad, son_ad = f"{B.xad[i0]}{B.yad[sabit]}", f"{B.xad[i1]}{B.yad[sabit]}"
        else:
            bas_ad, son_ad = f"{B.xad[sabit]}{B.yad[i0]}", f"{B.xad[sabit]}{B.yad[i1]}"
        parcalar = []
        for i in range(i0, i1):
            key = (kat, yon, sabit, i)
            if key in B.kiris_parca:
                raise MatrisHatasi(f"Kiriş {no}: kat {kat}'de aynı aks parçası kiriş {B.kiris_parca[key][0]['no']} ile çakışıyor; "
                                   "bir aks parçasında tek kiriş olabilir.")
            parcalar.append({"parca": len(parcalar) + 1, "i": i, "key": key, "L": konum[i + 1] - konum[i]})
        kir = {"no": no, "kat": kat, "bas": [B.xad[bx], B.yad[by]] if yon == "x" and bx <= sx or yon == "y" and by <= sy
               else [B.xad[sx], B.yad[sy]], "yon": yon, "sabit": sabit, "i0": i0, "i1": i1, "kesit": kad, "duvar": duvar,
               "L": konum[i1] - konum[i0], "b": ks["b"], "h": ks["h"], "A": ks["A"], "Iy_m": Iy_m, "Iz_m": Iz_m, "J": ks["J"],
               "E": ks["E"], "G": ks["G"], "gamma": ks["gamma"], "malzeme": ks["malzeme"], "parcalar": parcalar,
               "adres": f"K-{bas_ad}→{son_ad}/k{kat}"}
        kir["son"] = [B.xad[i1], B.yad[sabit]] if yon == "x" else [B.xad[sabit], B.yad[i1]]
        kir["bas"] = [B.xad[i0], B.yad[sabit]] if yon == "x" else [B.xad[sabit], B.yad[i0]]
        # duvar yüksekliği: varsayılan kirişin ALTINDAKİ kat yüksekliği − kiriş yüksekliği (eşit katlı binada kirişin
        # üstünde duran duvarın net yüksekliğiyle aynıdır); duvar_h ile açıkça verilebilir (ör. çatıda 1,0 m parapet)
        if kr.get("duvar_h") not in (None, ""):
            h_duvar = _sayi(kr.get("duvar_h"), f"Kiriş {no}: duvar_h (duvar yüksekliği, m)", pozitif=True, sifir_olur=False)
            if h_duvar > 10.0:
                raise MatrisHatasi(f"Kiriş {no}: duvar_h = {h_duvar} m çok büyük; duvar yüksekliği metre girilir (parapet 1,0).")
            kir["h_duvar_kaynak"] = "duvar_h (kullanıcı)"
        else:
            h_duvar = B.kat[kat]["h"] - ks["h"]
            kir["h_duvar_kaynak"] = "kat yüksekliği − kiriş yüksekliği"
        if duvar and h_duvar <= 0:
            raise MatrisHatasi(f"Kiriş {no}: duvar yüksekliği = kat yüksekliği − kiriş yüksekliği = {h_duvar:.2f} m ≤ 0; "
                               "kat yüksekliğini ya da kiriş kesitini düzeltin.")
        kir["h_duvar"] = h_duvar if duvar else 0.0
        B.kirisler.append(kir)
        for p in parcalar:
            B.kiris_parca[p["key"]] = (kir, p)

    # --- döşemeler ---
    B.dosemeler = []
    for k, d in enumerate(bina.get("dosemeler") or [], start=1):
        if not isinstance(d, dict):
            raise MatrisHatasi(f"{k}. döşeme sözlük olmalı.")
        no = _tam(d.get("no", k), f"{k}. döşeme: no")
        kat = _tam(d.get("kat", 1), f"Döşeme {no}: kat")
        if not 1 <= kat <= B.nk:
            raise MatrisHatasi(f"Döşeme {no}: kat {kat} yok; döşeme katı 1…{B.nk}.")
        kose = d.get("kose")
        if not isinstance(kose, (list, tuple)) or len(kose) != 2:
            raise MatrisHatasi(f"Döşeme {no}: kose = [[\"A\", \"1\"], [\"B\", \"2\"]] biçiminde iki köşe olmalı.")
        ix0, iy0 = _aks_cifti(kose[0], f"Döşeme {no}: kose[0]", B)
        ix1, iy1 = _aks_cifti(kose[1], f"Döşeme {no}: kose[1]", B)
        ix0, ix1, iy0, iy1 = min(ix0, ix1), max(ix0, ix1), min(iy0, iy1), max(iy0, iy1)
        if ix1 - ix0 != 1 or iy1 - iy0 != 1:
            raise MatrisHatasi(f"Döşeme {no}: köşeler ({B.xad[ix0]}{B.yad[iy0]} – {B.xad[ix1]}{B.yad[iy1]}) tek hücre tanımlamıyor; "
                               "döşeme komşu iki X aksı ile komşu iki Y aksı arasındaki tek dikdörtgen paneldir. "
                               "Büyük alan için her hücreye ayrı döşeme girin.")
        h = _sayi(d.get("h", 0.12), f"Döşeme {no}: h (kalınlık, m)", pozitif=True, sifir_olur=False)
        if h > 1.0:
            raise MatrisHatasi(f"Döşeme {no}: h = {h} m; kalınlık metre girilir (14 cm → 0.14).")
        kullanim = str(d.get("kullanim") or "konut").strip().lower()
        if kullanim not in yv.TS498_HAREKETLI and d.get("q") is None:
            raise MatrisHatasi(f"Döşeme {no}: kullanım sınıfı {kullanim!r} TS 498 çizelgesinde yok. Seçenekler: "
                               f"{', '.join(yv.TS498_HAREKETLI)}; ya da q değerini doğrudan verin.")
        kenarlar = {"alt": (kat, "x", iy0, ix0), "ust": (kat, "x", iy1, ix0), "sol": (kat, "y", ix0, iy0), "sag": (kat, "y", ix1, iy0)}
        eksik = [f"{_KENAR_AD[ad]} kenarı ({_kenar_adres(B, key)})" for ad, key in kenarlar.items() if key not in B.kiris_parca]
        if eksik:
            raise MatrisHatasi(f"Döşeme {no} (kat {kat}, {B.xad[ix0]}{B.yad[iy0]}–{B.xad[ix1]}{B.yad[iy1]}) 'yüzen döşeme': "
                               f"{'; '.join(eksik)} üzerinde kiriş yok. Döşeme yükü ancak dört kenarındaki kirişlere aktarılabilir; "
                               "eksik kirişleri ekleyin.")
        g_ek = d.get("g_ek", d.get("kaplama", 0.0))
        if isinstance(g_ek, str) and g_ek.strip() in yv.KAPLAMALAR:
            kap = yv.KAPLAMALAR[g_ek.strip()]
            g_ek_deger, g_ek_kaynak, g_ek_dogru = kap["deger"], f"{kap['ad']} ({kap['kaynak']})", kap["dogrulandi"]
        else:
            g_ek_deger = _sayi(g_ek if g_ek not in (None, "") else 0.0, f"Döşeme {no}: g_ek (kaplama + sıva, kN/m²)", pozitif=True)
            g_ek_kaynak, g_ek_dogru = "kullanıcı değeri (kaplama + sıva)", True
        if d.get("q") is None:
            qk = yv.TS498_HAREKETLI[kullanim]
            q, q_kaynak, q_dogru = qk["deger"], qk["kaynak"], qk["dogrulandi"]
            alan_p = (B.xk[ix1] - B.xk[ix0]) * (B.yk[iy1] - B.yk[iy0])
            if kullanim == "balkon" and alan_p > 10.0:      # TS 498:2021 Çizelge 6 satır 4: > 10 m² balkon
                q = 5.0 + 0.35 * (alan_p - 10.0)
                q_kaynak = f"TS 498:2021 md. 15.1 Çizelge 6 satır 4: balkon > 10 m² → 5,0 + 0,35·(A − 10) = 5,0 + 0,35·({alan_p:.2f} − 10)"
        else:
            q, q_kaynak, q_dogru = _sayi(d.get("q"), f"Döşeme {no}: q (kN/m²)", pozitif=True), "kullanıcı değeri", True
        dagitim = str(d.get("dagitim") or "otomatik").strip().lower()
        if dagitim not in ("otomatik", "cift", "tek"):
            raise MatrisHatasi(f"Döşeme {no}: dagitim {dagitim!r}; 'otomatik', 'cift' ya da 'tek' olmalı.")
        B.dosemeler.append({"no": no, "kat": kat, "kose": [[B.xad[ix0], B.yad[iy0]], [B.xad[ix1], B.yad[iy1]]],
                            "ix0": ix0, "iy0": iy0, "ix1": ix1, "iy1": iy1, "h": h, "kullanim": kullanim,
                            "g_ek": g_ek_deger, "g_ek_kaynak": g_ek_kaynak, "g_ek_dogrulandi": g_ek_dogru,
                            "q": q, "q_kaynak": q_kaynak, "q_dogrulandi": q_dogru, "dagitim": dagitim, "kenarlar": kenarlar,
                            "dx": B.xk[ix1] - B.xk[ix0], "dy": B.yk[iy1] - B.yk[iy0], "ek_g": 0.0, "ek_q": 0.0,
                            "adres": f"D-{B.xad[ix0]}{B.yad[iy0]}/{B.xad[ix1]}{B.yad[iy1]}/k{kat}"})
    nolar = [d["no"] for d in B.dosemeler]
    if len(set(nolar)) != len(nolar):
        raise MatrisHatasi(f"Döşeme numaraları tekrarlı: {nolar}.")
    for liste, ad in ((B.kolonlar, "Kolon"), (B.kirisler, "Kiriş")):
        nolar = [x["no"] for x in liste]
        if len(set(nolar)) != len(nolar):
            raise MatrisHatasi(f"{ad} numaraları tekrarlı: {nolar}.")
    B.kolon_no = {c["no"]: c for c in B.kolonlar}
    B.kiris_no = {k["no"]: k for k in B.kirisler}
    B.doseme_no = {d["no"]: d for d in B.dosemeler}
    for kat in range(1, B.nk + 1):
        if any(k["kat"] == kat for k in B.kirisler) and not any(c["kat"] == kat for c in B.kolonlar):
            raise MatrisHatasi(f"Kat {kat}'de kiriş var ama bu katı taşıyan kolon yok (kat {kat} kolonu kot_{kat - 1}–kot_{kat} "
                               "arasındadır); kirişler havada kalır. Kolon ekleyin.")

    # --- ek yükler ---
    B.ek_yukler = []
    B.ek_kar_var = False
    for k, y in enumerate(bina.get("ek_yukler") or [], start=1):
        if not isinstance(y, dict):
            raise MatrisHatasi(f"{k}. ek yük sözlük olmalı.")
        tur = str(y.get("tur", "")).strip().lower()
        durum = str(y.get("durum", "G")).strip().upper()
        if durum not in ("G", "Q", "S"):
            raise MatrisHatasi(f"{k}. ek yük: durum {durum!r}; 'G', 'Q' ya da 'S' (kar) olmalı; rüzgâr ve deprem yükleri "
                               "yuk_durumlari / deprem kartından üretilir.")
        if tur == "kiris":
            kno = _tam(y.get("kiris"), f"{k}. ek yük: kiris")
            if kno not in B.kiris_no:
                raise MatrisHatasi(f"{k}. ek yük: kiriş {kno} yok. Tanımlı kirişler: {sorted(B.kiris_no)}.")
            B.ek_yukler.append({"tur": "kiris", "kiris": kno, "durum": durum, "q": _sayi(y.get("q"), f"{k}. ek yük: q (kN/m, aşağı +)")})
            if durum == "S":
                B.ek_kar_var = True
        elif tur == "dugum":
            ix, iy = _aks_cifti(y.get("aks"), f"{k}. ek yük", B)
            kat = _tam(y.get("kat", 1), f"{k}. ek yük: kat")
            if not 0 <= kat <= B.nk:
                raise MatrisHatasi(f"{k}. ek yük: kat {kat} yok.")
            bil = {a: _sayi(y.get(a, 0.0), f"{k}. ek yük: {a}") for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}
            B.ek_yukler.append({"tur": "dugum", "aks": [B.xad[ix], B.yad[iy]], "ix": ix, "iy": iy, "kat": kat, "durum": durum, **bil})
            if durum == "S":
                B.ek_kar_var = True
        elif tur == "doseme":
            dno = _tam(y.get("doseme"), f"{k}. ek yük: doseme")
            if dno not in B.doseme_no:
                raise MatrisHatasi(f"{k}. ek yük: döşeme {dno} yok. Tanımlı döşemeler: {sorted(B.doseme_no)}.")
            g = _sayi(y.get("g", 0.0), f"{k}. ek yük: g (kN/m²)")
            q = _sayi(y.get("q", 0.0), f"{k}. ek yük: q (kN/m²)")
            B.doseme_no[dno]["ek_g"] += g
            B.doseme_no[dno]["ek_q"] += q
            B.ek_yukler.append({"tur": "doseme", "doseme": dno, "durum": "G" if g else "Q", "g": g, "q": q})
        else:
            raise MatrisHatasi(f"{k}. ek yük: tur {tur!r}; 'kiris', 'dugum' ya da 'doseme' olmalı.")

    # --- temeller ---
    t = bina.get("temeller") if isinstance(bina.get("temeller"), dict) else {}
    var = t.get("varsayilan") if isinstance(t.get("varsayilan"), dict) else {}
    zem = t.get("zemin") if isinstance(t.get("zemin"), dict) else {}
    mesnet = str(t.get("mesnet") or "ankastre").strip().lower()
    if mesnet not in ("ankastre", "mafsal", "elastik"):
        raise MatrisHatasi(f"temeller.mesnet {mesnet!r}; 'ankastre', 'mafsal' ya da 'elastik' olmalı.")
    B.temeller = {"tip": str(t.get("tip") or "tekil"),
                  "varsayilan": {"B": _sayi(var.get("B", 1.5), "temeller.varsayilan.B", pozitif=True, sifir_olur=False),
                                 "L": _sayi(var.get("L", 1.5), "temeller.varsayilan.L", pozitif=True, sifir_olur=False),
                                 "h": _sayi(var.get("h", 0.6), "temeller.varsayilan.h", pozitif=True)},
                  "zemin": {"q_em": _sayi(zem.get("q_em", 200.0), "temeller.zemin.q_em (kN/m²)", pozitif=True, sifir_olur=False),
                            "k0": _sayi(zem.get("k0", 20000.0), "temeller.zemin.k0 (kN/m³)", pozitif=True, sifir_olur=False)},
                  "mesnet": mesnet, "ozel": {}}
    for k, o in enumerate(t.get("ozel") or [], start=1):
        if not isinstance(o, dict):
            raise MatrisHatasi(f"temeller.ozel[{k}] sözlük olmalı.")
        ix, iy = _aks_cifti(o.get("aks"), f"temeller.ozel[{k}]", B)
        B.temeller["ozel"][(ix, iy)] = {"B": _sayi(o.get("B", B.temeller["varsayilan"]["B"]), f"temeller.ozel[{k}].B", pozitif=True, sifir_olur=False),
                                        "L": _sayi(o.get("L", B.temeller["varsayilan"]["L"]), f"temeller.ozel[{k}].L", pozitif=True, sifir_olur=False)}
    B.kombinasyon_kumesi = str(bina.get("kombinasyon_kumesi") or ("ts500" if B.sistem == "betonarme" else "cythye_ydkt")).strip().lower()
    if B.kombinasyon_kumesi not in yv.KOMBINASYONLAR:
        raise MatrisHatasi(f"kombinasyon_kumesi {B.kombinasyon_kumesi!r} tanımsız; seçenekler: {', '.join(yv.KOMBINASYONLAR)}.")
    an = bina.get("analiz") if isinstance(bina.get("analiz"), dict) else {}
    nokta = _tam(an.get("diyagram_nokta", DIYAGRAM_NOKTA), "analiz.diyagram_nokta")
    gost = an.get("gosterilecek", bina.get("gosterilecek"))
    if gost is not None and not isinstance(gost, (list, tuple)):
        raise MatrisHatasi("analiz.gosterilecek bir kombinasyon adı listesi olmalı, örn. [\"1.4G+1.6Q\", \"G+Q\"].")
    lb = str(an.get("celik_Lb", "otomatik")).strip().lower()
    if lb not in ("otomatik", "boy"):
        raise MatrisHatasi(f"analiz.celik_Lb {lb!r} tanımsız; 'otomatik' (döşemeli kiriş: pozitif momentte üst başlık tutulu, L_b = 0; "
                           "negatif momentte L_b = açıklık, C_b diyagramdan) ya da 'boy' "
                           "(L_b = kiriş açıklığı) olmalı.")
    koz = str(an.get("kiris_oz", "net")).strip().lower()
    if koz not in ("net", "brut"):
        raise MatrisHatasi(f"analiz.kiris_oz {koz!r} tanımsız; 'net' (betonarme kirişte A = b·(h − t_döşeme): döşeme içindeki kısım "
                           "döşeme ağırlığında sayılır) ya da 'brut' (A = b·h) olmalı.")
    cr = an.get("catlamis_rijitlik")
    B.analiz = {"catlamis_rijitlik": None if cr is None else bool(cr), "diyagram_nokta": max(3, min(41, nokta)),
                "gosterilecek": [str(x) for x in gost] if gost is not None else None, "celik_Lb": lb, "kiris_oz": koz}
    # --- yük durumları (S, W, E) ve deprem kartı ---
    _yuk_durumlarini_oku(B, bina)
    # --- çatlamış (etkin) kesit rijitliği: TBDY 4.5.8.1 betonarmede deprem hesabında zorunlu; varsayılan buna göre ---
    zorunlu = B.sistem == "betonarme" and B.deprem is not None
    if cr is None:
        B.analiz["catlamis_rijitlik"] = zorunlu
    elif zorunlu and not B.analiz["catlamis_rijitlik"]:
        B.uyarilar.append("analiz.catlamis_rijitlik = false: TBDY 4.5.8.1'e aykırı — betonarme binanın deprem hesabında Tablo 4.2 etkin "
                          "(çatlamış) kesit rijitlikleri zorunludur; bu çözüm brüt kesitle yapıldı (periyot kısa, öteleme küçük çıkar).")
    return B


def _yuk_durumlarini_oku(B, bina):
    """yuk_durumlari.S / W / E ve deprem kartını okur; B.kar, B.ruzgar, B.deprem (sözlük ya da None) doldurur."""
    yd = bina.get("yuk_durumlari") if isinstance(bina.get("yuk_durumlari"), dict) else {}
    S = yd.get("S") if isinstance(yd.get("S"), dict) else {}
    W = yd.get("W") if isinstance(yd.get("W"), dict) else {}
    E = yd.get("E") if isinstance(yd.get("E"), dict) else {}
    dep = bina.get("deprem") if isinstance(bina.get("deprem"), dict) else {}
    B.deprem_ham = copy.deepcopy(dep) if dep else None
    # kar (TS 498:2021 md. 11; TS EN 1991-1-3 μ1)
    B.kar = None
    if S.get("acik") or B.ek_kar_var:
        bolge = S.get("bolge")
        aciklama_b = ""
        if bolge in (None, "") and S.get("il"):
            bolge = yv.kar_bolgesi(S["il"], S.get("ilce"))
            if bolge is None:
                raise MatrisHatasi(f"yuk_durumlari.S: il/ilçe {S.get('il')!r}/{S.get('ilce')!r} Ek 1 listesinde bulunamadı; "
                                   "kar bölgesini (1–9) doğrudan girin.")
            aciklama_b = f" (Ek 1: {S['il']}{'/' + str(S['ilce']) if S.get('ilce') else ''} → bölge {bolge}; OCR aktarımı, doğrulanmadı)"
        if bolge in (None, ""):
            bolge = 3
            aciklama_b = " (bölge verilmedi; varsayılan 3)"
        bolge = _tam(bolge, "yuk_durumlari.S.bolge")
        if not 1 <= bolge <= 9:
            raise MatrisHatasi(f"yuk_durumlari.S.bolge = {bolge}; TS 498:2021 kar bölgesi 1…9 olmalı (Ek 1 / Ek 2).")
        rakim = _sayi(S.get("rakim", 0.0), "yuk_durumlari.S.rakim (m)", pozitif=True)
        if S.get("Sk") is not None:
            Sk, Sk_kaynak = _sayi(S["Sk"], "yuk_durumlari.S.Sk (kN/m²)", pozitif=True), "kullanıcı değeri"
        else:
            Sk, Sk_kaynak = yv.kar_Sk(bolge, rakim)
            Sk_kaynak = "TS 498:2021 Çizelge 3: " + Sk_kaynak + aciklama_b
        if S.get("alpha") is not None:
            alpha = _sayi(S["alpha"], "yuk_durumlari.S.alpha (çatı eğimi, derece)", pozitif=True)
            mu, mu_kaynak = yv.kar_mu1(alpha), f"TS EN 1991-1-3 Tablo 5.2 μ1(α = {_f(alpha)}°)"
        else:
            alpha = 0.0
            mu = _sayi(S.get("mu", 0.8), "yuk_durumlari.S.mu", pozitif=True)
            mu_kaynak = "TS EN 1991-1-3 Tablo 5.2 μ1 = 0,8 (düz çatı, α ≤ 30°)" if abs(mu - 0.8) < 1e-9 else "kullanıcı değeri"
        Ce = _sayi(S.get("Ce", 1.0), "yuk_durumlari.S.Ce", pozitif=True)
        Ct = _sayi(S.get("Ct", 1.0), "yuk_durumlari.S.Ct", pozitif=True)
        B.kar = {"acik": True, "bolge": bolge, "rakim": rakim, "Sk": Sk, "Sk_kaynak": Sk_kaynak, "mu": mu, "mu_kaynak": mu_kaynak,
                 "alpha": alpha, "Ce": Ce, "Ct": Ct, "s": mu * Ce * Ct * Sk, "kat": B.nk,
                 "kaynak": "TS 498:2021 md. 11 (S_k, Çizelge 3) ve TS EN 1991-1-3 Denk. (5.1): s = μ1·C_e·C_t·S_k",
                 "dogrulandi": S.get("Sk") is not None or (yv.TS498_KAR["dogrulandi"] and not aciklama_b.startswith(" (Ek 1"))}
    # rüzgâr (TS 498:2021 md. 14)
    B.ruzgar = None
    if W.get("acik"):
        C = _sayi(W.get("C", yv.TS498_RUZGAR["C"]), "yuk_durumlari.W.C", pozitif=True)
        sarp = bool(W.get("sarp", False))
        B.ruzgar = {"acik": True, "C": C, "sarp": sarp,
                    "q_kaynak": "TS 498:2021 md. 14.3 Çizelge 4 (q = v²/1600)" + ("; sarp yamaç: q ≥ 1,1" if sarp else ""),
                    "C_kaynak": "TS 498:2021 Çizelge 5 (1.1.1): C = 0,8 (basınç) + 0,4 (emme) = 1,2" if abs(C - 1.2) < 1e-9 else "kullanıcı değeri"}
    # deprem (TBDY 2018)
    B.deprem = None
    etkin = bool(E.get("acik")) or bool(dep.get("etkin"))
    if etkin:
        if not dep:
            raise MatrisHatasi("Deprem yükü açık ama 'deprem' kartı yok: {\"SS\": 1.0, \"S1\": 0.3, \"zemin_sinifi\": \"ZC\", ...} girin "
                               "(S_S, S_1 AFAD TDTH'den, tdth.afad.gov.tr).")
        SS = _sayi(dep.get("SS"), "deprem.SS (kısa periyot harita spektral ivme katsayısı)", pozitif=True, sifir_olur=False)
        S1 = _sayi(dep.get("S1"), "deprem.S1 (1,0 s harita spektral ivme katsayısı)", pozitif=True, sifir_olur=False)
        if SS > 3.0 or S1 > 1.5:
            raise MatrisHatasi(f"deprem.SS = {SS}, S1 = {S1}: değerler g cinsinden boyutsuzdur (Türkiye'de S_S ≤ ~2,0, S_1 ≤ ~0,6).")
        zemin = str(dep.get("zemin_sinifi") or dep.get("zemin") or "ZC").strip().upper()
        if zemin == "ZF":
            raise MatrisHatasi("Zemin sınıfı ZF: sahaya özel zemin davranış analizi gerekir (TBDY 16.5); Tablo 2.1/2.2'de değer yoktur.")
        if zemin not in ("ZA", "ZB", "ZC", "ZD", "ZE"):
            raise MatrisHatasi(f"deprem.zemin_sinifi {zemin!r}; ZA, ZB, ZC, ZD ya da ZE olmalı (TBDY Tablo 16.1).")
        DD = str(dep.get("DD") or "DD-2").strip().upper()
        if DD != "DD-2":
            B.uyarilar.append(f"deprem.DD = {DD}: dayanıma göre tasarımda DD-2 esastır (TBDY 4.4.1); girilen S_S/S_1 DD-2 kabul edildi.")
        BKS = _tam(dep.get("BKS", 3), "deprem.BKS")
        if BKS not in (1, 2, 3):
            raise MatrisHatasi(f"deprem.BKS = {BKS}; bina kullanım sınıfı 1, 2 ya da 3 olmalı (TBDY Tablo 3.1).")
        I_tablo = yv.TBDY_BKS_I[BKS]["I"]
        I = _sayi(dep.get("I", I_tablo), "deprem.I", pozitif=True, sifir_olur=False)
        if abs(I - I_tablo) > 1e-9:
            B.uyarilar.append(f"deprem.I = {I} girildi; Tablo 3.1'e göre BKS = {BKS} için I = {I_tablo}.")
        varsayilan_tasiyici = "betonarme-cerceve-yuksek" if B.sistem == "betonarme" else "celik-cerceve-yuksek"
        tasiyici_girdi = str(dep.get("tasiyici") or varsayilan_tasiyici).strip().lower()
        tasiyici = yv.tasiyici_anahtar(tasiyici_girdi)
        if tasiyici is None:
            raise MatrisHatasi(f"deprem.tasiyici {tasiyici_girdi!r} Tablo 4.1 listesinde yok. Sık kullanılanlar: "
                               f"{', '.join(yv.TBDY_TASIYICI_ARAYUZ)} (tam liste: bina_kutuphane → deprem.tasiyici).")
        ts = yv.TBDY_TASIYICI[tasiyici]
        if ts["grup"] not in (B.sistem, "onuretimli" if B.sistem == "betonarme" else B.sistem):
            B.uyarilar.append(f"deprem.tasiyici {ts['kod']} ({ts['grup']}) bina sistemiyle ({B.sistem}) uyuşmuyor; R ve D yine Tablo 4.1'den alındı.")
        R = _sayi(dep.get("R", ts["R"]), "deprem.R", pozitif=True, sifir_olur=False)
        D = _sayi(dep.get("D", ts["D"]), "deprem.D", pozitif=True, sifir_olur=False)
        if abs(R - ts["R"]) > 1e-9 or abs(D - ts["D"]) > 1e-9:
            B.uyarilar.append(f"deprem.R/D = {R}/{D} girildi; Tablo 4.1 {ts['kod']} için R = {ts['R']}, D = {ts['D']}.")
        # n: kullanım sınıfından öneri (en büyük n; döşeme yoksa 0,3)
        n_oneri = max([yv.TBDY_KUTLE_KATILIM_KULLANIM["n"].get(d["kullanim"], 0.3) for d in B.dosemeler] + [0.3])
        n = _sayi(dep.get("n", n_oneri), "deprem.n (hareketli yük kütle katılım katsayısı)", pozitif=True)
        if n > 1.0:
            raise MatrisHatasi(f"deprem.n = {n}; Tablo 4.3'te n ≤ 1,0 (konut 0,3; okul/mağaza 0,6; depo 0,8).")
        if B.sistem == "betonarme" and "cerceve" in tasiyici and "perde" not in tasiyici:
            Ct_varsayilan = yv.TBDY_CT["betonarme-cerceve"]
        elif B.sistem == "celik":
            Ct_varsayilan = yv.TBDY_CT["celik-cerceve"]
        else:
            Ct_varsayilan = yv.TBDY_CT["diger"]
        Ct = _sayi(dep.get("Ct", Ct_varsayilan), "deprem.Ct", pozitif=True, sifir_olur=False)
        periyot = str(dep.get("periyot") or "otomatik").strip().lower()
        if periyot not in ("ampirik", "rayleigh", "otomatik"):
            raise MatrisHatasi(f"deprem.periyot {periyot!r}; 'ampirik', 'rayleigh' ya da 'otomatik' olmalı.")
        diyafram = str(dep.get("diyafram") or "rijit").strip().lower()
        if diyafram not in ("rijit", "esnek"):
            raise MatrisHatasi(f"deprem.diyafram {diyafram!r}; 'rijit' ya da 'esnek' olmalı.")
        e = _sayi(dep.get("dismerkezlik", 0.05), "deprem.dismerkezlik", pozitif=True)
        dolgu = str(dep.get("dolgu") or "bitisik").strip().lower()
        if dolgu not in ("bitisik", "esnek"):
            raise MatrisHatasi(f"deprem.dolgu {dolgu!r}; 'bitisik' (gevrek dolgu çerçeveye bitişik, 0,008κ) ya da 'esnek' (0,016κ) olmalı.")
        SS3 = dep.get("SS_DD3")
        S13 = dep.get("S1_DD3")
        if (SS3 is None) != (S13 is None):
            raise MatrisHatasi("deprem.SS_DD3 ve S1_DD3 birlikte verilmeli (λ için DD-3 spektrumu).")
        B.deprem = {"etkin": True, "SS": SS, "S1": S1, "zemin_sinifi": zemin, "DD": DD, "BKS": BKS, "I": I, "tasiyici": tasiyici,
                    "tasiyici_kod": ts["kod"], "tasiyici_tanim": ts["tanim"], "BYS_min": ts["BYS_min"], "R": R, "D": D, "n": n,
                    "n_oneri": n_oneri, "Ct": Ct, "periyot": periyot, "diyafram": diyafram, "dismerkezlik": e, "dolgu": dolgu,
                    "SS_DD3": _sayi(SS3, "deprem.SS_DD3", pozitif=True) if SS3 is not None else None,
                    "S1_DD3": _sayi(S13, "deprem.S1_DD3", pozitif=True) if S13 is not None else None}



def _kenar_adres(B, key):
    kat, yon, sabit, i = key
    if yon == "x":
        return f"{B.xad[i]}{B.yad[sabit]}→{B.xad[i + 1]}{B.yad[sabit]}"
    return f"{B.xad[sabit]}{B.yad[i]}→{B.xad[sabit]}{B.yad[i + 1]}"


# ============================================================================
# Yükler (TS 498:2021) ve döşemeden kirişe dağıtım (TS 500 md. 11.4.3, 45° kuralı)
# ============================================================================
def _esdeger(sekil, w, lx, ly):
    """Eşdeğer düzgün yayılı yükler (yalnız el hesabı/anlatım; TS 500 bunları vermez, basit kiriş eşdeğerliğinden türetilir):
    üçgen q_eM = w·lx/3, q_eV = w·lx/4; trapez q_eM = (w·lx/2)(1 − 1/(3m²)), q_eV = (w·lx/2)(1 − 1/(2m)); düzgün w·lx/2."""
    p = w * lx / 2.0
    if sekil == "ucgen":
        return w * lx / 3.0, w * lx / 4.0
    if sekil == "trapez":
        m = ly / lx
        return p * (1.0 - 1.0 / (3.0 * m * m)), p * (1.0 - 1.0 / (2.0 * m))
    if sekil == "duzgun":
        return p, p
    return 0.0, 0.0


def _sekil_parcalari(sekil, lx, Le):
    """Birim tepe için parçalı doğrusal yük: [(x1, x2, f1, f2)] (f: tepe değerinin katı)."""
    if sekil == "ucgen":
        return [(0.0, lx / 2.0, 0.0, 1.0), (lx / 2.0, lx, 1.0, 0.0)]
    if sekil == "trapez":
        return [(0.0, lx / 2.0, 0.0, 1.0), (lx / 2.0, Le - lx / 2.0, 1.0, 1.0), (Le - lx / 2.0, Le, 1.0, 0.0)]
    if sekil == "duzgun":
        return [(0.0, Le, 1.0, 1.0)]
    return []


def _doseme_dagit(B, d):
    """Bir panelin dört kenar kirişine giden yükler. m = l_u/l_k ≤ 2 (ya da dagitim 'cift'): kısa kenara üçgen (tepe w·l_k/2),
    uzun kenara trapez (plato w·l_k/2, rampalar l_k/2); m > 2 ('tek'): uzun kenarlara düzgün w·l_k/2, kısa kenarlara 0.
    Korunum: Σ(kirişlere giden) = w·l_k·l_u (kesin)."""
    dx, dy = d["dx"], d["dy"]
    lx, ly = min(dx, dy), max(dx, dy)
    m = ly / lx
    if d["dagitim"] == "otomatik":
        tip = "cift" if m <= 2.0 + 1e-9 else "tek"
    else:
        tip = d["dagitim"]
    g, q, sk = d["g"], d["q_top"], d["s"]
    paylar = []
    kare = abs(dx - dy) < 1e-9
    d["not"] = ""
    if tip == "tek" and kare:
        d["not"] = "Kare panelde tek doğrultulu dağıtım: X doğrultusundaki kirişler taşıyan (uzun kenar) sayıldı, Y kirişlerine yük verilmedi."
    for ad, key in d["kenarlar"].items():
        Le = dx if key[1] == "x" else dy
        kisa = (key[1] == "y") if (tip == "tek" and kare) else abs(Le - lx) < 1e-9
        if tip == "cift":
            sekil = "ucgen" if (kisa or abs(m - 1.0) < 1e-9) else "trapez"
        else:
            sekil = "yok" if kisa else "duzgun"
        kenar = "kisa" if kisa else "uzun"
        kir, parca = B.kiris_parca[key]
        qMg, qVg = _esdeger(sekil, g, lx, ly)
        qMq, qVq = _esdeger(sekil, q, lx, ly)
        qMs, qVs = _esdeger(sekil, sk, lx, ly)
        birim = _sekil_parcalari(sekil, lx, Le)
        toplam_birim = {"ucgen": lx * lx / 4.0, "trapez": lx / 2.0 * (ly - lx / 2.0), "duzgun": lx / 2.0 * Le, "yok": 0.0}[sekil]
        paylar.append({"kenar_ad": ad, "kenar_aciklama": _KENAR_AD[ad], "key": key, "kiris_no": kir["no"], "parca": parca["parca"],
                       "kenar": kenar, "sekil": sekil, "L": Le, "tepe_g": g * lx / 2.0 if sekil != "yok" else 0.0,
                       "tepe_q": q * lx / 2.0 if sekil != "yok" else 0.0, "q_eM_g": qMg, "q_eV_g": qVg, "q_eM_q": qMq, "q_eV_q": qVq,
                       "tepe_s": sk * lx / 2.0 if sekil != "yok" else 0.0, "q_eM_s": qMs, "q_eV_s": qVs,
                       "toplam_G": g * toplam_birim, "toplam_Q": q * toplam_birim, "toplam_S": sk * toplam_birim, "parcalar_birim": birim})
    return lx, ly, m, tip, paylar


def _yukleri_hazirla(B):
    """Döşeme g/q, duvar, kiriş ve kolon öz ağırlıkları; döşeme payları; kiriş dökümü; eleman/düğüm yük havuzu (bina koordinatı,
    aşağı pozitif kN/m, tekil yükler bina bileşenleriyle)."""
    Y = SimpleNamespace(dosemeler=[], kirisler=[], kolonlar=[], katlar=[], toplam={"G": 0.0, "Q": 0.0, "S": 0.0},
                        parca_yuk={}, dugum_yuk={}, kiris_yuk={}, kar_var=B.kar is not None)
    s_cati = B.kar["s"] if B.kar else 0.0
    for d in B.dosemeler:
        d["g_plak"] = GAMMA_BA * d["h"]
        d["g"] = d["g_plak"] + d["g_ek"] + d["ek_g"]
        d["q_top"] = d["q"] + d["ek_q"]
        d["s"] = s_cati if (B.kar and d["kat"] == B.nk) else 0.0     # kar yalnız en üst kat döşemelerinde (çatı)
        d["alan"] = d["dx"] * d["dy"]
        lx, ly, m, tip, paylar = _doseme_dagit(B, d)
        d.update({"lx": lx, "ly": ly, "m": m, "tip": tip, "paylar": paylar, "G_toplam": d["g"] * d["alan"], "Q_toplam": d["q_top"] * d["alan"],
                  "S_toplam": d["s"] * d["alan"]})
        Y.dosemeler.append(d)
        for p in paylar:
            hav = Y.parca_yuk.setdefault(p["key"], {durum: {"duzgun": 0.0, "parcalar": [], "eV": 0.0, "eM": 0.0, "doseme_kN": 0.0}
                                                      for durum in ("G", "Q", "S")} | {"paylar": []})
            hav["paylar"].append((d["no"], p))
            for durum, tepe, eM, eV, top in (("G", p["tepe_g"], p["q_eM_g"], p["q_eV_g"], p["toplam_G"]),
                                              ("Q", p["tepe_q"], p["q_eM_q"], p["q_eV_q"], p["toplam_Q"]),
                                              ("S", p["tepe_s"], p["q_eM_s"], p["q_eV_s"], p["toplam_S"])):
                if tepe:
                    hav[durum]["parcalar"] += [(x1, x2, f1 * tepe, f2 * tepe) for x1, x2, f1, f2 in p["parcalar_birim"]]
                hav[durum]["eM"] += eM
                hav[durum]["eV"] += eV
                hav[durum]["doseme_kN"] += top
    # kiriş dökümü
    ek_kiris = {}
    for y in B.ek_yukler:
        if y["tur"] == "kiris":
            ek_kiris.setdefault(y["kiris"], {"G": 0.0, "Q": 0.0, "S": 0.0})[y["durum"]] += y["q"]
    bos = {"duzgun": 0.0, "parcalar": [], "eV": 0.0, "eM": 0.0, "doseme_kN": 0.0}
    t_dos = {}                                     # kirişe oturan döşemelerin en kalını (öz ağırlıkta çift sayımı önlemek için)
    for d in Y.dosemeler:
        for p in d["paylar"]:
            t_dos[p["kiris_no"]] = max(t_dos.get(p["kiris_no"], 0.0), d["h"])
    for k in B.kirisler:
        ks = B.kesitler[k["kesit"]]
        t = t_dos.get(k["no"], 0.0)
        if B.analiz["kiris_oz"] == "net" and ks["tip"] == "dikdortgen" and 0.0 < t < k["h"]:
            k["A_oz"], k["t_doseme"] = k["b"] * (k["h"] - t), t          # kirişin döşeme içindeki kısmı döşeme ağırlığında
        else:
            k["A_oz"], k["t_doseme"] = k["A"], 0.0
        oz = k["gamma"] * k["A_oz"]
        duvar = B.duvarlar[k["duvar"]]["deger"] * k["h_duvar"] if k["duvar"] else 0.0
        ek = ek_kiris.get(k["no"], {"G": 0.0, "Q": 0.0, "S": 0.0})
        ekG, ekQ, ekS = ek["G"], ek["Q"], ek["S"]
        dos = {"G": 0.0, "Q": 0.0, "S": 0.0}
        eMd = {"G": 0.0, "Q": 0.0, "S": 0.0}
        for p in k["parcalar"]:
            hav = Y.parca_yuk.get(p["key"]) or {"G": bos, "Q": bos, "S": bos}
            for durum in ("G", "Q", "S"):
                dos[durum] += hav[durum]["doseme_kN"]
                eMd[durum] += hav[durum]["eM"] * p["L"]
            Y.kiris_yuk[p["key"]] = {"G": {"duzgun": oz + duvar + ekG, "parcalar": hav["G"]["parcalar"], "eV": hav["G"]["eV"], "eM": hav["G"]["eM"]},
                                     "Q": {"duzgun": ekQ, "parcalar": hav["Q"]["parcalar"], "eV": hav["Q"]["eV"], "eM": hav["Q"]["eM"]},
                                     "S": {"duzgun": ekS, "parcalar": hav["S"]["parcalar"], "eV": hav["S"]["eV"], "eM": hav["S"]["eM"]}}
        L = k["L"]
        G_top = dos["G"] + (duvar + oz + ekG) * L
        Q_top = dos["Q"] + ekQ * L
        S_top = dos["S"] + ekS * L
        qM_G = oz + duvar + ekG + eMd["G"] / L
        qM_Q = ekQ + eMd["Q"] / L
        Y.kirisler.append({"no": k["no"], "kat": k["kat"], "adres": k["adres"], "L": L,
                           "G": {"doseme": dos["G"], "duvar": duvar * L, "oz": oz * L, "ek": ekG * L, "toplam_kN": G_top},
                           "Q": {"doseme": dos["Q"], "ek": ekQ * L, "toplam_kN": Q_top},
                           "S": {"doseme": dos["S"], "ek": ekS * L, "toplam_kN": S_top},
                           "kN_m": {"oz": oz, "duvar": duvar, "ek_G": ekG, "ek_Q": ekQ, "q_eM_G": qM_G, "q_eM_Q": qM_Q,
                                    "q_eV_G": G_top / L, "q_eV_Q": Q_top / L},
                           "el_hesabi": {"R_G": G_top / 2.0, "R_Q": Q_top / 2.0, "M_G": qM_G * L * L / 8.0, "M_Q": qM_Q * L * L / 8.0}})
    # kolon öz ağırlığı → üst düğüme tekil (G)
    bos6 = lambda: {"G": [0.0] * 6, "Q": [0.0] * 6, "S": [0.0] * 6}  # noqa: E731
    for c in B.kolonlar:
        W = c["gamma"] * c["A"] * c["L"]
        Y.kolonlar.append({"no": c["no"], "kat": c["kat"], "adres": c["adres"], "oz_kN": W})
        hav = Y.dugum_yuk.setdefault((c["ix"], c["iy"], c["kat"]), bos6())
        hav["G"][2] -= W
    for y in B.ek_yukler:
        if y["tur"] == "dugum":
            hav = Y.dugum_yuk.setdefault((y["ix"], y["iy"], y["kat"]), bos6())
            for i, a in enumerate(("FX", "FY", "FZ", "MX", "MY", "MZ")):
                hav[y["durum"]][i] += y[a]
    # kat toplamları (kat 0 = temel seviyesine doğrudan verilen düğüm yükleri; kolonlardan geçmez)
    for kt in B.katlar:
        k = kt["no"]
        G = sum(d["G_toplam"] for d in Y.dosemeler if d["kat"] == k)
        G += sum(r["G"]["duvar"] + r["G"]["oz"] + r["G"]["ek"] for r in Y.kirisler if r["kat"] == k)
        G += sum(c["oz_kN"] for c in Y.kolonlar if c["kat"] == k)
        G += sum(-h["G"][2] for key, h in Y.dugum_yuk.items() if key[2] == k) - sum(c["oz_kN"] for c in Y.kolonlar if c["kat"] == k)
        Q = sum(d["Q_toplam"] for d in Y.dosemeler if d["kat"] == k)
        Q += sum(r["Q"]["ek"] for r in Y.kirisler if r["kat"] == k)
        Q += sum(-h["Q"][2] for key, h in Y.dugum_yuk.items() if key[2] == k)
        Sk = sum(d["S_toplam"] for d in Y.dosemeler if d["kat"] == k)
        Sk += sum(r["S"]["ek"] for r in Y.kirisler if r["kat"] == k)
        Sk += sum(-h["S"][2] for key, h in Y.dugum_yuk.items() if key[2] == k)
        Y.katlar.append({"kat": k, "ad": kt["ad"], "kot": kt["kot"], "h": kt["h"], "G": G, "Q": Q, "S": Sk, "w": G + Q})
    Y.toplam = {"G": sum(k["G"] for k in Y.katlar), "Q": sum(k["Q"] for k in Y.katlar), "S": sum(k["S"] for k in Y.katlar)}
    Y.kat0 = {d: sum(-h[d][2] for key, h in Y.dugum_yuk.items() if key[2] == 0) for d in ("G", "Q", "S")}
    Y.korunum_parcalari = {
        "G": {"dosemeler": sum(d["G_toplam"] for d in Y.dosemeler),
              "duvarlar": sum(r["G"]["duvar"] for r in Y.kirisler),
              "kiris_oz": sum(r["G"]["oz"] for r in Y.kirisler),
              "kolon_oz": sum(c["oz_kN"] for c in Y.kolonlar),
              "ek": sum(r["G"]["ek"] for r in Y.kirisler) + sum(-h["G"][2] for h in Y.dugum_yuk.values()) - sum(c["oz_kN"] for c in Y.kolonlar)},
        "Q": {"dosemeler": sum(d["Q_toplam"] for d in Y.dosemeler), "duvarlar": 0.0, "kiris_oz": 0.0, "kolon_oz": 0.0,
              "ek": sum(r["Q"]["ek"] for r in Y.kirisler) + sum(-h["Q"][2] for h in Y.dugum_yuk.values())},
        "S": {"dosemeler": sum(d["S_toplam"] for d in Y.dosemeler), "duvarlar": 0.0, "kiris_oz": 0.0, "kolon_oz": 0.0,
              "ek": sum(r["S"]["ek"] for r in Y.kirisler) + sum(-h["S"][2] for h in Y.dugum_yuk.values())}}
    for durum in ("G", "Q", "S"):
        Y.korunum_parcalari[durum]["toplam"] = sum(Y.korunum_parcalari[durum].values())
    return Y


# ============================================================================
# Ağ (cerceve3b modeli): düğüm = aks kesişimi × kat; kolon alt→üst, kiriş küçük→büyük aks; parçalar ayrı eleman
# ============================================================================
def _dugum_no(kat, ix, iy):
    """Okunur düğüm numarası: 1000·kat + 20·(X aks sırası) + (Y aks sırası) + 1."""
    return 1000 * kat + 20 * ix + iy + 1


def _diyafram_destegi():
    """sonlu_eleman rijit diyafram API'sini (model["diyaframlar"], efendi düğüm 9000+kat) tanıyor mu? Paralel geliştirilen
    motor için özellik sezimi: modül niteliği, işlev adı ya da coz_coklu/_model_oku belgesinde 'diyafram' geçmesi."""
    if getattr(se, "DIYAFRAM_DESTEGI", None):
        return True
    if any("diyafram" in ad.lower() for ad in dir(se)):
        return True
    for f in (getattr(se, "coz_coklu", None), getattr(se, "_model_oku", None)):
        if f is not None and "diyafram" in (f.__doc__ or "").lower():
            return True
    try:
        import inspect
        return "diyafram" in inspect.getsource(se._model_oku).lower()
    except Exception:  # noqa: BLE001
        return False


def _ag_olustur(B, Y, kutle=None):
    """ag (bina koordinatı, UI için) ve motor modeli (cerceve3b, Y yukarı). Mesnetler temel düğümlerinde.
    ``kutle`` (kat kütle merkezleri) verilir ve rijit diyafram isteniyorsa (deprem.diyafram = 'rijit') motor destekliyorsa
    her kata efendi düğüm (9000 + kat, kat kütle merkezinde) ve köle listesi eklenir. Dönen ``model`` brüt kesitlidir;
    çatlamış rijitlik (analiz.catlamis_rijitlik ve deprem açık, TBDY Tablo 4.2: kolon 0,70, kiriş 0,35; yalnız beton) ayrı bir
    kopyada ``ag["model_c"]`` (deprem birleşimlerinin hesabı, md. 4.5.8.3)."""
    dugum_key = {}
    dugumler = []

    def dugum(ix, iy, kat):
        key = (ix, iy, kat)
        if key not in dugum_key:
            no = _dugum_no(kat, ix, iy)
            dugum_key[key] = no
            dugumler.append({"no": no, "X": B.xk[ix], "Y": B.yk[iy], "Z": B.kat[kat]["kot"],
                             "adres": f"{B.xad[ix]}{B.yad[iy]}/k{kat}", "kat": kat, "aks": [B.xad[ix], B.yad[iy]], "key": key, "efendi": False})
        return dugum_key[key]

    # çatlamış (etkin) kesit rijitliği (TBDY 4.5.8, Tablo 4.2): yalnız deprem etkili birleşimlerin hesabında (4.5.8.3) →
    # brüt model (G, Q, S, W: deprem dışı birleşimler) + çatlamış kopya (deprem birim durumları ve deprem birleşimlerine giren
    # G, Q, S). Çarpan yalnız beton malzemeli elemanlara uygulanır.
    catlamis = bool(B.analiz["catlamis_rijitlik"]) and B.deprem is not None
    ck = yv.TBDY_ETKIN_RIJITLIK["kolon"]["egilme"] if catlamis else 1.0
    cb = yv.TBDY_ETKIN_RIJITLIK["kiris"]["egilme"] if catlamis else 1.0

    def carpan(x, f):
        return f if B.malzemeler[x["malzeme"]]["tur"] == "beton" else 1.0

    elemanlar, model_el = [], []
    eno = 0
    for c in sorted(B.kolonlar, key=lambda c: (c["kat"], c["no"])):
        eno += 1
        i, j = dugum(c["ix"], c["iy"], c["kat"] - 1), dugum(c["ix"], c["iy"], c["kat"])
        c["eleman"] = eno
        elemanlar.append({"no": eno, "dugumler": [i, j], "tur": "kolon", "kaynak_no": c["no"], "parca": 1, "kat": c["kat"],
                          "L": c["L"], "kesit": c["kesit"], "kaynak": {"tur": "kolon", "no": c["no"], "parca": 1},
                          "key": (c["ix"], c["iy"], c["kat"]), "adres": c["adres"], "rijitlik_carpani": carpan(c, ck)})
        model_el.append({"no": eno, "dugumler": [i, j], "E": c["E"], "G": c["G"], "A": c["A"], "Iy": c["Iy_m"], "Iz": c["Iz_m"],
                         "J": c["J"], "kaynak": {"tur": "kolon", "no": c["no"], "parca": 1}})
    for k in sorted(B.kirisler, key=lambda k: (k["kat"], k["no"])):
        for p in k["parcalar"]:
            eno += 1
            kat, yon, sabit, i0 = p["key"]
            if yon == "x":
                a, b = dugum(i0, sabit, kat), dugum(i0 + 1, sabit, kat)
            else:
                a, b = dugum(sabit, i0, kat), dugum(sabit, i0 + 1, kat)
            p["eleman"] = eno
            elemanlar.append({"no": eno, "dugumler": [a, b], "tur": "kiris", "kaynak_no": k["no"], "parca": p["parca"], "kat": kat,
                              "L": p["L"], "kesit": k["kesit"], "kaynak": {"tur": "kiris", "no": k["no"], "parca": p["parca"]},
                              "key": p["key"], "adres": f"{k['adres']} ({_kenar_adres(B, p['key'])})", "rijitlik_carpani": carpan(k, cb)})
            model_el.append({"no": eno, "dugumler": [a, b], "E": k["E"], "G": k["G"], "A": k["A"], "Iy": k["Iy_m"], "Iz": k["Iz_m"],
                             "J": k["J"], "kaynak": {"tur": "kiris", "no": k["no"], "parca": p["parca"]}})
    n_kole = len(dugumler)
    # rijit diyafram: efendi düğümler (kat kütle merkezi), köleler = o katın bütün düğümleri
    diyaframlar, efendi = [], {}
    istek = bool(B.deprem) and B.deprem["diyafram"] == "rijit" and kutle is not None
    destek = _diyafram_destegi() if istek else False
    if istek and destek:
        for kk in kutle:
            kat = kk["kat"]
            koleler = [dg["no"] for dg in dugumler if dg["kat"] == kat]
            if len(koleler) < 2:
                continue
            no = 9000 + kat
            x, y, z = _motor_koordinat(kk["X"], kk["Y"], kk["kot"])
            diyaframlar.append({"dugumler": koleler, "ana": {"no": no, "x": x, "y": y, "z": z}, "ad": f"Kat {kat}"})
            efendi[kat] = no
            dugumler.append({"no": no, "X": kk["X"], "Y": kk["Y"], "Z": kk["kot"], "adres": f"KM/k{kat}", "kat": kat, "aks": None,
                             "key": None, "efendi": True})
    n = 6 * n_kole
    if n > EN_FAZLA_SD:
        raise MatrisHatasi(f"Bina ağı {n_kole} düğüm × 6 = {n} serbestlik derecesi; tarayıcıda çözüm için en fazla {EN_FAZLA_SD}. "
                           "Modeli küçültün: aks ya da kat sayısını azaltın, katları birleştirin.")
    # yerel eksen matrisleri (motor kuralı) → bina koordinatına
    model_dg = []
    for dg in dugumler:
        x, y, z = _motor_koordinat(dg["X"], dg["Y"], dg["Z"])
        dg["m"] = (x, y, z)
        if not dg["efendi"]:
            model_dg.append({"no": dg["no"], "x": x, "y": y, "z": z})
    dno = {dg["no"]: dg for dg in dugumler}
    for e in elemanlar:
        a, b = dno[e["dugumler"][0]]["m"], dno[e["dugumler"][1]]["m"]
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L = math.sqrt(dx * dx + dy * dy + dz * dz)
        lam = se._lam3b(dx / L, dy / L, dz / L, True)
        e["lam"] = [list(_bina_vek(satir)) for satir in lam]
    # mesnetler ve yaylar
    mesnetler, model_mes, yaylar = [], [], []
    tip = B.temeller["mesnet"]
    k0 = B.temeller["zemin"]["k0"]
    for dg in dugumler:
        if dg["kat"] != 0 or dg["efendi"]:
            continue
        ix, iy = dg["key"][0], dg["key"][1]
        tem = B.temeller["ozel"].get((ix, iy), B.temeller["varsayilan"])
        mesnetler.append({"dugum": dg["no"], "tip": tip, "aks": dg["aks"], "B": tem["B"], "L": tem["L"]})
        if tip == "ankastre":
            model_mes.append({"dugum": dg["no"], "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True})
        elif tip == "mafsal":
            model_mes.append({"dugum": dg["no"], "ux": True, "uy": True, "uz": True})
        else:
            # elastik: düşey yay kZ = k0·B·L (motor ky), dönme yayları krX = k0·B·L³/12 (motor krx), krY = k0·L·B³/12 (motor krz);
            # yatay ötelemeler ve düşey eksen etrafında dönme tutulu (bkz. §3)
            Bt, Lt = tem["B"], tem["L"]
            model_mes.append({"dugum": dg["no"], "ux": True, "uz": True, "ry": True})
            yaylar.append({"dugum": dg["no"], "ky": k0 * Bt * Lt, "krx": k0 * Bt * Lt ** 3 / 12.0, "krz": k0 * Lt * Bt ** 3 / 12.0})
    model = {"tip": "cerceve3b", "hesap": "sayisal", "baslik": B.baslik + " — bina ağı (G durumu)",
             "birim": dict(B.birim), "dugumler": model_dg, "elemanlar": model_el, "mesnetler": model_mes,
             "yukler": [], "yayili": []}
    if yaylar:
        model["yaylar"] = yaylar
    if diyaframlar:
        model["diyaframlar"] = diyaframlar
    model_c = None
    if catlamis:
        model_c = dict(model, baslik=B.baslik + " — bina ağı (çatlamış kesit, deprem birleşimleri)",
                       elemanlar=[dict(me, Iy=me["Iy"] * e["rijitlik_carpani"], Iz=me["Iz"] * e["rijitlik_carpani"])
                                  for me, e in zip(model_el, elemanlar)])
    ag = {"dugumler": dugumler, "elemanlar": elemanlar, "mesnetler": mesnetler, "sd_sayisi": n, "mod": "sayisal",
          "dugum_key": dugum_key, "dno": dno, "efendi": efendi, "diyaframlar": diyaframlar, "n_kole": n_kole,
          "diyafram_istek": istek, "diyafram_destek": destek, "rijitlik_carpani": {"kolon": ck, "kiris": cb},
          "model_c": model_c}
    return ag, model


def _diyaframsiz(ag, model):
    """Rijit diyafram yolu başarısız olduysa (motor desteklemiyor): efendi düğümler ve diyafram listesi atılır."""
    ag["dugumler"] = [dg for dg in ag["dugumler"] if not dg["efendi"]]
    ag["dno"] = {dg["no"]: dg for dg in ag["dugumler"]}
    ag["efendi"], ag["diyaframlar"], ag["diyafram_destek"] = {}, [], False
    model.pop("diyaframlar", None)
    if ag.get("model_c") is not None:
        ag["model_c"].pop("diyaframlar", None)


# ============================================================================
# Kat kütleleri (TBDY Denk. 4.16: w = w_G + n·w_Q [+ 0,3·S çatıda]), kütle merkezi, yaklaşık rijitlik merkezi
# ============================================================================
def _kat_kutleleri(B, Y, n=0.3, kar_payi=0.3):
    """Her kat (1…N) için düğüm ağırlıkları ve toplamlar. Düğüm payı: komşu panellerin çeyreği (g + n·q + 0,3·s),
    komşu kiriş parçalarının yarısı (öz + duvar + ek_G + n·ek_Q + 0,3·ek_S), kolon öz ağırlığının yarıları (kat k kolonunun
    üst yarısı kat k'ye, alt yarısı kat k−1'e), kata verilen ek düğüm yükleri. Dönüş [{kat, kot, H (temel üstünden
    yükseklik H_i), h, w, m, X, Y, BX, BY, dugum_w: {(ix, iy): w_j}, G, Q, S}]."""
    g = 9.81
    sonuc = []
    for kt in B.katlar:
        kat = kt["no"]
        if kat == 0:
            continue
        w = {}

        def ekle(ix, iy, v):
            w[(ix, iy)] = w.get((ix, iy), 0.0) + v

        for d in Y.dosemeler:
            if d["kat"] != kat:
                continue
            pay = (d["g"] + n * d["q_top"] + kar_payi * d["s"]) * d["alan"] / 4.0
            for ix in (d["ix0"], d["ix1"]):
                for iy in (d["iy0"], d["iy1"]):
                    ekle(ix, iy, pay)
        for key, hav in Y.kiris_yuk.items():
            k_, yon, sabit, i = key
            if k_ != kat:
                continue
            L = (B.xk[i + 1] - B.xk[i]) if yon == "x" else (B.yk[i + 1] - B.yk[i])
            q = hav["G"]["duzgun"] + n * hav["Q"]["duzgun"] + kar_payi * hav["S"]["duzgun"]
            uclar = [(i, sabit), (i + 1, sabit)] if yon == "x" else [(sabit, i), (sabit, i + 1)]
            for ix, iy in uclar:
                ekle(ix, iy, q * L / 2.0)
        for c in B.kolonlar:
            W = c["gamma"] * c["A"] * c["L"]
            if c["kat"] == kat:
                ekle(c["ix"], c["iy"], W / 2.0)
            elif c["kat"] == kat + 1:
                ekle(c["ix"], c["iy"], W / 2.0)
        for (ix, iy, k_), hav in Y.dugum_yuk.items():
            if k_ != kat:
                continue
            kolon_oz = sum(c["gamma"] * c["A"] * c["L"] for c in B.kolonlar if c["kat"] == kat and (c["ix"], c["iy"]) == (ix, iy))
            ekle(ix, iy, (-hav["G"][2] - kolon_oz) + n * (-hav["Q"][2]) + kar_payi * (-hav["S"][2]))
        W = sum(w.values())
        if W > 1e-9:
            X = sum(v * B.xk[ix] for (ix, iy), v in w.items()) / W
            Yc = sum(v * B.yk[iy] for (ix, iy), v in w.items()) / W
        else:
            X, Yc = (B.xk[0] + B.xk[-1]) / 2.0, (B.yk[0] + B.yk[-1]) / 2.0
        xs = [B.xk[ix] for (ix, iy) in w] or B.xk
        ys = [B.yk[iy] for (ix, iy) in w] or B.yk
        kk = next(x for x in Y.katlar if x["kat"] == kat)
        sonuc.append({"kat": kat, "kot": kt["kot"], "H": kt["kot"] - B.katlar[0]["kot"], "h": kt["h"], "w": W, "m": W / g, "X": X, "Y": Yc,
                      "BX": max(xs) - min(xs), "BY": max(ys) - min(ys), "dugum_w": w, "G": kk["G"], "Q": kk["Q"], "S": kk["S"]})
    return sonuc


def _rijitlik_merkezi(B):
    """Yaklaşık kat rijitlik merkezi: kolon kesme rijitlikleri k = 12EI/L³ ile ağırlıklı ortalama (kiriş etkisi yok).
    X_RM = Σ(k_y·X)/Σk_y (Y yönündeki rijitlikler X boyunca nasıl dağılmış), Y_RM = Σ(k_x·Y)/Σk_x."""
    out = []
    for kat in range(1, B.nk + 1):
        kx = ky = sx = sy = 0.0
        for c in B.kolonlar:
            if c["kat"] != kat:
                continue
            k_x = 12.0 * c["E"] * c["Iz_m"] / c["L"] ** 3     # X yönünde ötelenmeye direnç (bina Y ekseni etrafında eğilme)
            k_y = 12.0 * c["E"] * c["Iy_m"] / c["L"] ** 3
            kx += k_x
            ky += k_y
            sy += k_x * B.yk[c["iy"]]
            sx += k_y * B.xk[c["ix"]]
        out.append({"kat": kat, "X": sx / ky if ky else 0.0, "Y": sy / kx if kx else 0.0})
    return out


# ============================================================================
# TBDY 2018 eşdeğer deprem yükü: spektrum, sınıflar, periyot, taban kesme, kat kuvvetleri
# ============================================================================
def _spektrum(SS, S1, zemin):
    """S_DS, S_D1, T_A, T_B, T_L ve S_ae(T) kapanışı (Denk. 2.1–2.3; Tablo 2.1/2.2 ara değerli)."""
    FS = yv.zemin_katsayisi(yv.TBDY_FS, zemin, SS)
    F1 = yv.zemin_katsayisi(yv.TBDY_F1, zemin, S1)
    SDS, SD1 = SS * FS, S1 * F1
    TA, TB, TL = 0.2 * SD1 / SDS, SD1 / SDS, yv.TBDY_SPEKTRUM["TL"]

    def Sae(T):
        T = float(T)
        if T <= TA:
            return (0.4 + 0.6 * T / TA) * SDS
        if T <= TB:
            return SDS
        if T <= TL:
            return SD1 / T
        return SD1 * TL / T ** 2
    return {"FS": FS, "F1": F1, "SDS": SDS, "SD1": SD1, "TA": TA, "TB": TB, "TL": TL, "Sae": Sae}


def _dts(SDS, BKS):
    for esik, ad in yv.TBDY_DTS["satirlar"]:
        if SDS >= esik:
            return ad + ("a" if BKS == 1 else "")
    return "4a" if BKS == 1 else "4"  # pragma: no cover


def _bys(HN, DTS):
    kolon = 1 if DTS[0] in "12" else (2 if DTS[0] == "3" else 3)
    for satir in yv.TBDY_BYS["satirlar"]:
        sinir = satir[kolon]
        if sinir is None or HN <= sinir + 1e-9:
            return satir[0]
    return 1  # pragma: no cover


def _deprem_on(B, Y, kutle):
    """Çözümden bağımsız deprem büyüklükleri: spektrum, I, DTS, BYS, R_a, T_pA, kat ağırlıkları, m_t, uygulanabilirlik."""
    d = B.deprem
    sp_ = _spektrum(d["SS"], d["S1"], d["zemin_sinifi"])
    I, R, D = d["I"], d["R"], d["D"]
    SDS, TB = sp_["SDS"], sp_["TB"]
    DTS = _dts(SDS, d["BKS"])
    HN = B.katlar[-1]["kot"] - B.katlar[0]["kot"]
    BYS = _bys(HN, DTS)
    TpA = d["Ct"] * HN ** 0.75
    uyarilar = []

    def Ra(T):
        return R / I if T > TB else D + (R / I - D) * T / TB

    def SaR(T):
        return sp_["Sae"](T) / Ra(T)

    if d["BYS_min"] is not None and BYS < d["BYS_min"]:
        uyarilar.append(f"Tablo 4.1 {d['tasiyici_kod']}: izin verilen BYS ≥ {d['BYS_min']}, binanın BYS = {BYS} (H_N = {HN:.1f} m); "
                        "bu taşıyıcı sistem bu yükseklikte kullanılamaz.")
    if DTS.endswith("a") and yv.TBDY_TASIYICI[d["tasiyici"]]["suneklik"] == "sinirli":
        uyarilar.append(f"DTS = {DTS} binalarda süneklik düzeyi sınırlı sistem kullanılamaz (md. 4.3.4.1).")
    if d["tasiyici_kod"] in ("A31", "B31", "C31") and DTS not in ("3", "4"):
        uyarilar.append(f"{d['tasiyici_kod']} yalnız DTS = 3 ve 4 binalarda (md. 4.3.4.3); DTS = {DTS}.")
    # Tablo 4.4: düzenli bina varsayımı (η_bi çözümden sonra denetlenir)
    sutun = "dts12" if DTS[0] in "12" else "dts34"
    esik = yv.TBDY_UYGULANABILIRLIK["duzenli"][sutun]
    uygulanabilir = BYS >= esik
    uyg_bilgi = {"DTS": DTS, "BYS": BYS, "esik_duzenli": esik, "esik_diger": yv.TBDY_UYGULANABILIRLIK["diger"][sutun],
                 "kosul_duzenli": yv.TBDY_UYGULANABILIRLIK["duzenli"]["kosul"], "kaynak": yv.TBDY_UYGULANABILIRLIK["kaynak"],
                 "not": "B2 (yumuşak kat) düzensizliği bu modülde denetlenmez; η_bi çözümden sonra denetlenir (≤ 2,0)."}
    if not uygulanabilir:
        uyarilar.append(f"Eşdeğer deprem yükü yöntemi Tablo 4.4'e göre bu bina için uygulanamaz (DTS = {DTS}, BYS = {BYS} < {esik}); "
                        "mod birleştirme yöntemi gerekir. Sonuçlar yalnız öğretim amaçlıdır.")
    ampirik_yeter = (DTS[0] in "34") or (DTS[0] in "12" and BYS >= 6)
    yontem = d["periyot"]
    if yontem == "otomatik":
        yontem = "ampirik" if ampirik_yeter else "rayleigh"
    mt = sum(k["m"] for k in kutle)
    wt = sum(k["w"] for k in kutle)
    lam = 1.0
    sp3 = None
    if d["SS_DD3"] is not None:
        sp3 = _spektrum(d["SS_DD3"], d["S1_DD3"], d["zemin_sinifi"])
    else:
        uyarilar.append("DD-3 spektrumu (deprem.SS_DD3, S1_DD3) verilmedi; göreli kat ötelemesi denetiminde λ = 1 alındı "
                        "(md. 4.9.1.4 λ = S_ae(T_p; DD-3)/S_ae(T_p; DD-2) genellikle < 1, denetim güvenli taraftadır).")
    return {"sp": sp_, "sp3": sp3, "I": I, "R": R, "D": D, "DTS": DTS, "BYS": BYS, "HN": HN, "TpA": TpA, "Ra": Ra, "SaR": SaR,
            "mt": mt, "wt": wt, "N": len(kutle), "uyarilar": uyarilar, "uygulanabilir": uygulanabilir, "ampirik_yeter": ampirik_yeter,
            "Tp_yontem": yontem, "lam": lam, "kutle": kutle, "g": 9.81, "uygulanabilirlik": uyg_bilgi,
            "kappa": yv.TBDY_DEPREM_KURALLAR["kappa"][B.sistem], "Ch": yv.TBDY_DEPREM_KURALLAR["Ch"][B.sistem],
            "sinir_oran": (0.008 if d["dolgu"] == "bitisik" else 0.016) * yv.TBDY_DEPREM_KURALLAR["kappa"][B.sistem]}


def _taban_kesme(dep, Tp, alt_sinir=True):
    """V_tE (Denk. 4.19), ΔF_NE (4.22), F_iE (4.23) → (V_hesap, V_min, V_tE, ΔF_NE, [F_iE]); H_i temel üstünden ölçülür.
    alt_sinir=False: drift için (md. 4.9.1.1, 0,04·m_t·I·S_DS·g alt sınırı uygulanmaz)."""
    g, mt, I = dep["g"], dep["mt"], dep["I"]
    SDS = dep["sp"]["SDS"]
    V = mt * dep["SaR"](Tp) * g
    Vmin = 0.04 * mt * I * SDS * g
    V_kullanilan = max(V, Vmin) if alt_sinir else V
    dFN = 0.0075 * dep["N"] * V_kullanilan
    toplam = sum(k["m"] * k["H"] for k in dep["kutle"])
    F = [(V_kullanilan - dFN) * k["m"] * k["H"] / toplam for k in dep["kutle"]]
    return V, Vmin, V_kullanilan, dFN, F


def _spektrum_noktalari(dep, Tp):
    """[[T, S_ae, S_aR], ...] (0 … 4 s; köşe periyotları ve T_p dahil)."""
    sp_ = dep["sp"]
    Ts = sorted(set([i * 0.05 for i in range(0, 61)] + [i * 0.25 for i in range(13, 17)] + [sp_["TA"], sp_["TB"], Tp]))
    return [[_r(T), _r(sp_["Sae"](T)), _r(dep["SaR"](T))] for T in Ts if T <= 4.0 + 1e-9]


# ============================================================================
# Yük durumları (G, Q, S, W, E): motor kayıtları — parçalı (hedef yol) ve eşdeğer düzgün (yedek yol)
# ============================================================================
def _dusey_durum(B, Y, ag, durum):
    """G, Q ya da S için {"yukler", "yayili", "yayili_esdeger"} (motor koordinatı)."""
    yayili, esdeger = [], []
    for e in ag["elemanlar"]:
        if e["tur"] != "kiris":
            continue
        hav = Y.kiris_yuk.get(e["key"])
        if not hav:
            continue
        h = hav[durum]
        if h["duzgun"]:
            yayili.append({"eleman": e["no"], "q": -h["duzgun"]})
        for x1, x2, f1, f2 in h["parcalar"]:
            if f1 or f2:
                yayili.append({"eleman": e["no"], "q1": -f1, "q2": -f2, "x1": x1, "x2": x2})
        top = h["duzgun"] + h["eV"]
        if top:
            esdeger.append({"eleman": e["no"], "q": -top})
    yukler = []
    for key, hav in Y.dugum_yuk.items():
        if key not in ag["dugum_key"]:
            raise MatrisHatasi(f"Ek düğüm yükü {B.xad[key[0]]}{B.yad[key[1]]}/k{key[2]} hiçbir elemana bağlı olmayan bir noktada; "
                               "yük ancak kolon ya da kiriş düğümüne verilebilir.")
        v = hav[durum]
        if any(v):
            F = _motor_vek(v[:3])
            M = _motor_vek(v[3:])
            yukler.append({"dugum": ag["dugum_key"][key], "Fx": F[0], "Fy": F[1], "Fz": F[2], "Mx": M[0], "My": M[1], "Mz": M[2]})
    return {"yukler": yukler, "yayili": yayili, "yayili_esdeger": esdeger}


def _dugum_yuku_ekle(liste, dugum, FX=0.0, FY=0.0, FZ=0.0, MZ=0.0):
    """Bina bileşenli düğüm yükünü motor kaydına çevirip listeye ekler (aynı düğümde toplar)."""
    F = _motor_vek((FX, FY, FZ))
    M = _motor_vek((0.0, 0.0, MZ))
    for y in liste:
        if y["dugum"] == dugum:
            y["Fx"] += F[0]
            y["Fy"] += F[1]
            y["Fz"] += F[2]
            y["Mx"] += M[0]
            y["My"] += M[1]
            y["Mz"] += M[2]
            return
    liste.append({"dugum": dugum, "Fx": F[0], "Fy": F[1], "Fz": F[2], "Mx": M[0], "My": M[1], "Mz": M[2]})


def _ruzgar_durumlari(B, ag):
    """TS 498:2021 md. 14: kat kuvveti F_i = C·q(z_i)·A_cephe, A_cephe = B_cephe·(h_i/2 + h_(i+1)/2) (kat yükseklik payı);
    q(z) Çizelge 4 basamağı, z = kat seviyesinin temel üstünden yüksekliği. Kuvvet rüzgâr yüzündeki kat düğümlerine
    cephe payıyla (düğümün iki komşu aks aralığının yarısı) verilir. Dönüş (durumlar, ruzgar_veri)."""
    C = B.ruzgar["C"]
    z0 = B.katlar[0]["kot"]
    katlar = []
    durumlar = {ad: {"yukler": [], "yayili": [], "yayili_esdeger": []} for ad in ("W+X", "W-X", "W+Y", "W-Y")}
    for kt in B.katlar:
        kat = kt["no"]
        if kat == 0:
            continue
        dgs = [dg for dg in ag["dugumler"] if dg["kat"] == kat and not dg["efendi"]]
        if not dgs:
            continue
        z = kt["kot"] - z0
        q = yv.ruzgar_q(z)
        if B.ruzgar["sarp"]:
            q = max(q, 1.1)
        ust = B.kat[kat + 1]["h"] if kat + 1 in B.kat else 0.0
        h_pay = kt["h"] / 2.0 + ust / 2.0
        xs, ys = [dg["X"] for dg in dgs], [dg["Y"] for dg in dgs]
        BX, BY = max(xs) - min(xs), max(ys) - min(ys)
        kayit = {"kat": kat, "z": z, "kot": kt["kot"], "q": q, "h_pay": h_pay, "genislik_x": BY, "genislik_y": BX,
                 "cephe_x": BY * h_pay, "cephe_y": BX * h_pay, "F_x": C * q * BY * h_pay, "F_y": C * q * BX * h_pay}
        katlar.append(kayit)
        for ad, yuz, F, kenar_konum in (("W+X", "X", kayit["F_x"], min(xs)), ("W-X", "X", -kayit["F_x"], max(xs)),
                                        ("W+Y", "Y", kayit["F_y"], min(ys)), ("W-Y", "Y", -kayit["F_y"], max(ys))):
            yuz_d = [dg for dg in dgs if abs(dg[yuz] - kenar_konum) < 1e-9]
            diger = "Y" if yuz == "X" else "X"
            yuz_d.sort(key=lambda dg: dg[diger])
            konum = [dg[diger] for dg in yuz_d]
            genis = (max(konum) - min(konum)) if len(konum) > 1 else 0.0
            for j, dg in enumerate(yuz_d):
                if genis <= 1e-9:
                    pay = 1.0 / len(yuz_d)
                else:
                    alt = konum[j] if j == 0 else (konum[j] + konum[j - 1]) / 2.0
                    ust_ = konum[j] if j == len(konum) - 1 else (konum[j] + konum[j + 1]) / 2.0
                    pay = (ust_ - alt) / genis
                if yuz == "X":
                    _dugum_yuku_ekle(durumlar[ad]["yukler"], dg["no"], FX=F * pay)
                else:
                    _dugum_yuku_ekle(durumlar[ad]["yukler"], dg["no"], FY=F * pay)
    q_h = [{"kat": k["kat"], "z": k["z"], "q": k["q"]} for k in katlar]
    kaynak = (f"TS 498:2021 md. 14: W = C·q(z)·A; q Çizelge 4 (z ≤ 8 m 0,5; 8–20 m 0,8; 20–100 m 1,1; > 100 m 1,3 kN/m²), "
              f"C = {_f(C, 2)} ({B.ruzgar['C_kaynak']}); A = cephe genişliği × kat yükseklik payı")
    return durumlar, {"C": C, "C_kaynak": B.ruzgar["C_kaynak"], "q_kaynak": B.ruzgar["q_kaynak"], "kaynak": kaynak, "q_h": q_h,
                      "katlar": katlar, "toplam_x": sum(k["F_x"] for k in katlar), "toplam_y": sum(k["F_y"] for k in katlar)}


def _deprem_birim_durumlari(B, ag, dep):
    """Deprem için birim yük durumları (her yön d ∈ {X, Y}): R{d} kat kuvvetleri s_i = m_i·H_i/Σm_j·H_j (Σ = 1 kN),
    N{d} tepe kata 1 kN, T{d}{i} kat i'nin birim dışmerkezlik burulması: yalnız kat i'de M_Z = ∓s_i·B_i (e = 1·B_i, B_i deprem
    doğrultusuna dik kat boyutu; rijit diyaframda efendi düğüme moment, esnekte kütle payıyla kuvvet çifti), TN{d} tepe kat için
    aynısı (1 kN). Burulma kat kat ayrıdır, çünkü md. 4.7.4'teki D_bi kat bazındadır. E durumları süperpozisyondur (e_oran = 0,05):
    E{d}0 = (V − ΔF)·R + ΔF·N;  E{d}± = E{d}0 ± e_oran·[Σ_i D_bi·(V − ΔF)·T_i + D_bN·ΔF·TN]  ⇒  M_ib = F_iE·0,05·D_bi·B_i (Denk. 4.17)."""
    kutle = dep["kutle"]
    toplam = sum(k["m"] * k["H"] for k in kutle)
    sekil = {k["kat"]: k["m"] * k["H"] / toplam for k in kutle}
    tepe = kutle[-1]["kat"]
    efendi = ag["efendi"]
    bos = lambda: {"yukler": [], "yayili": [], "yayili_esdeger": []}  # noqa: E731
    durumlar = {}
    for yon in ("X", "Y"):
        R, N, TN = bos(), bos(), bos()
        for kk in kutle:
            kat = kk["kat"]
            s = sekil[kat]
            Bdik = kk["BY"] if yon == "X" else kk["BX"]
            T = durumlar.setdefault(f"T{yon}{kat}", bos())          # kat bazında birim burulma (D_bi kat kat, md. 4.7.4)
            kat_d = [dg for dg in ag["dugumler"] if dg["kat"] == kat and not dg["efendi"]]
            # kuvvet dağılımı: efendiye tek kuvvet; esnekte kütle payı
            if kat in efendi:
                hedefler = [(efendi[kat], 1.0)]
            else:
                W = sum(kk["dugum_w"].get(dg["key"][:2], 0.0) for dg in kat_d)
                hedefler = [(dg["no"], kk["dugum_w"].get(dg["key"][:2], 0.0) / W) for dg in kat_d] if W > 1e-12 else \
                    [(dg["no"], 1.0 / len(kat_d)) for dg in kat_d]
            for no, pay in hedefler:
                kw = {"FX": s * pay} if yon == "X" else {"FY": s * pay}
                _dugum_yuku_ekle(R["yukler"], no, **kw)
                if kat == tepe:
                    kw1 = {"FX": pay} if yon == "X" else {"FY": pay}
                    _dugum_yuku_ekle(N["yukler"], no, **kw1)
            # burulma (e = B_i): X yönü kuvvet +Y'ye kaydırılınca M_Z = −F·e; Y yönü kuvvet +X'e kaydırılınca M_Z = +F·e
            isaret = -1.0 if yon == "X" else 1.0
            if kat in efendi:
                _dugum_yuku_ekle(T["yukler"], efendi[kat], MZ=isaret * s * Bdik)
                if kat == tepe:
                    _dugum_yuku_ekle(TN["yukler"], efendi[kat], MZ=isaret * Bdik)
            else:
                # esnek diyafram: aynı momenti veren kuvvet dağılımı (net kuvvet 0): f_j = M·w_j·(c_j − c_m)/Σ w·(c − c_m)²
                koord = "Y" if yon == "X" else "X"
                merkez = kk["Y"] if yon == "X" else kk["X"]
                I = sum(kk["dugum_w"].get(dg["key"][:2], 0.0) * (dg[koord] - merkez) ** 2 for dg in kat_d)
                if I > 1e-12:
                    for dg in kat_d:
                        pay = kk["dugum_w"].get(dg["key"][:2], 0.0) * (dg[koord] - merkez) / I * Bdik
                        kw = {"FX": s * pay} if yon == "X" else {"FY": s * pay}
                        _dugum_yuku_ekle(T["yukler"], dg["no"], **kw)
                        if kat == tepe:
                            kw1 = {"FX": pay} if yon == "X" else {"FY": pay}
                            _dugum_yuku_ekle(TN["yukler"], dg["no"], **kw1)
        durumlar["R" + yon], durumlar["N" + yon], durumlar["TN" + yon] = R, N, TN
    return durumlar, sekil


def _yuk_durumlari(B, Y, ag, dep=None):
    """{durum: {"yukler": [...], "yayili": [...], "yayili_esdeger": [...]}} motor koordinatında. yayili: düzgün {"eleman", "q"}
    ve parçalı {"eleman", "q1", "q2", "x1", "x2"} (yerel y′, aşağı negatif). Durumlar: G, Q, [S], [W+X, W-X, W+Y, W-Y],
    deprem açıkken birim durumlar RX, NX, TX, TNX, RY, … (EX±, EY±, EZ çözümden sonra süperpozisyonla kurulur)."""
    durumlar = {"G": _dusey_durum(B, Y, ag, "G"), "Q": _dusey_durum(B, Y, ag, "Q")}
    ruzgar = None
    if B.kar:
        durumlar["S"] = _dusey_durum(B, Y, ag, "S")
    if B.ruzgar:
        wd, ruzgar = _ruzgar_durumlari(B, ag)
        durumlar.update(wd)
    sekil = None
    if dep is not None:
        ed, sekil = _deprem_birim_durumlari(B, ag, dep)
        durumlar.update(ed)
    return durumlar, ruzgar, sekil


# ============================================================================
# Çözüm: se.coz_coklu (K bir kez, bütün sağ taraflar) → motor KISA → bina koordinatında KISA
# ============================================================================
_DIYAGRAM = ("N", "V", "M", "Vz", "My", "T")
_BIRIM_DURUMLAR = ("RX", "NX", "TNX", "RY", "NY", "TNY")     # + kat burulmaları TX1, TX2, …, TY1, … (_birim_mi)
_CATLAMIS_EK = "~c"       # deprem birleşimlerine giren düşey durumların çatlamış kesitli çözümü: G~c, Q~c, S~c (TBDY 4.5.8.3)


def _birim_mi(ad):
    """Deprem birim durumu mu (çıktıya girmez): RX, NX, TNX, RY, NY, TNY ve kat burulmaları T{X|Y}{kat}."""
    return ad in _BIRIM_DURUMLAR or (len(ad) > 2 and ad[0] == "T" and ad[1] in "XY" and ad[2:].isdigit())


def _durumlari_coz(B, model, durumlar, ag=None):
    """{durum: KISA_motor}. Hedef yol: coz_coklu + parçalı yük. coz_coklu bulunmayan eski motor kopyasında her durum
    se_coz ile ve eşdeğer düzgün yükle (q_eV; toplam yük korunur) çözülür. Rijit diyafram isteği motor tarafından
    reddedilirse (API yok) diyaframsız yeniden çözülür ve uyarı eklenir."""
    nokta = B.analiz["diyagram_nokta"]
    if hasattr(se, "coz_coklu"):
        girdi = {ad: {"yukler": d["yukler"], "yayili": d["yayili"]} for ad, d in durumlar.items()}
        try:
            ham = se.coz_coklu(model, girdi, diyagram_nokta=nokta)
        except MatrisHatasi:
            if ag is None or not model.get("diyaframlar"):
                raise
            _diyaframsiz(ag, model)
            B.uyarilar.append("Rijit diyafram motor tarafından kabul edilmedi; bütün durumlar esnek diyaframla (kat düğümlerine "
                              "dağıtılmış kuvvet) çözüldü.")
            ham = se.coz_coklu(model, girdi, diyagram_nokta=nokta)
        yol = "coz_coklu"
    else:  # pragma: no cover — eski motor
        ham, yol = {}, "se_coz"
        for ad, d in durumlar.items():
            m = dict(model, yukler=d["yukler"], yayili=d["yayili_esdeger"])
            ham[ad] = se.se_coz(m, goster="yok").veri
    if ag is not None and ag["efendi"]:
        n_u = len(next(iter(ham.values()))["u"])
        if n_u == 6 * ag["n_kole"]:
            # motor efendi düğümleri u'ya yazmıyor: efendileri ag'den düşür (kat yer değiştirmeleri kölelerden okunur)
            _diyaframsiz(ag, model)
            ag["diyafram_destek"] = True
            ag["diyafram_not"] = "efendi düğümler motor çıktısında yok; kat ötelemeleri köle düğümlerden okundu"
        elif n_u != 6 * len(ag["dugumler"]):
            raise MatrisHatasi(f"coz_coklu {n_u} serbestlik derecesi döndürdü; bina ağı {6 * len(ag['dugumler'])} bekliyor "
                               "(diyafram API uyumsuzluğu).")
    sonuc = {}
    for ad, k in ham.items():
        elemanlar = []
        for e in k["elemanlar"]:
            diy = e.get("diyagram", e)
            kayit = {"no": e["no"], "uc_kuvvetleri": [float(x) for x in e["uc_kuvvetleri"]], "x": [float(x) for x in diy["x"]]}
            for ad_ in _DIYAGRAM:
                v = diy.get(ad_)
                if v is None:
                    kayit[ad_] = [0.0] * len(kayit["x"])
                elif isinstance(v, (int, float)):      # N sabit: skaler verilir, istasyon sayısına yayılır
                    kayit[ad_] = [float(v)] * len(kayit["x"])
                else:
                    kayit[ad_] = [float(x) for x in v]
            elemanlar.append(kayit)
        sonuc[ad] = {"u": [float(x) for x in k["u"]],
                     "tepkiler": [{a: float(t.get(a, 0.0)) for a in ("Fx", "Fy", "Fz", "Mx", "My", "Mz")} | {"dugum": t["dugum"]} for t in k["tepkiler"]],
                     "elemanlar": elemanlar,
                     "denge": {a: float(k["denge"].get(a, 0.0)) for a in ("Fx", "Fy", "Fz", "Mx", "My", "Mz")},
                     "yaylar": [dict(y) for y in k.get("yaylar") or []]}
    return sonuc, yol


def _enb(kayit):
    return {a: max(kayit[a], key=abs) if kayit[a] else 0.0 for a in _DIYAGRAM}


def _kisa_bina(kisa_m, ag):
    """Motor KISA → bina koordinatında KISA (şemadaki biçim): dugumler/tepkiler/denge dönüştürülür, eleman yerel değerleri aynı."""
    u = kisa_m["u"]
    dugumler = []
    for i, dg in enumerate(ag["dugumler"]):
        v = _bina_6(u[6 * i:6 * i + 6])
        dugumler.append({"no": dg["no"], "uX": v[0], "uY": v[1], "uZ": v[2], "rX": v[3], "rY": v[4], "rZ": v[5]})
    tepkiler = []
    for t in kisa_m["tepkiler"]:
        F = _bina_vek((t["Fx"], t["Fy"], t["Fz"]))
        Mm = _bina_vek((t["Mx"], t["My"], t["Mz"]))
        tepkiler.append({"dugum": t["dugum"], "FX": F[0], "FY": F[1], "FZ": F[2], "MX": Mm[0], "MY": Mm[1], "MZ": Mm[2]})
    d = kisa_m["denge"]
    F = _bina_vek((d["Fx"], d["Fy"], d["Fz"]))
    Mm = _bina_vek((d["Mx"], d["My"], d["Mz"]))
    elemanlar = []
    for e in kisa_m["elemanlar"]:
        k = {a: list(e[a]) for a in ("x",) + _DIYAGRAM}
        k["no"], k["uc_kuvvetleri"] = e["no"], list(e["uc_kuvvetleri"])
        k["enb"] = _enb(k)
        elemanlar.append(k)
    return {"u": list(u), "dugumler": dugumler, "tepkiler": tepkiler, "elemanlar": elemanlar,
            "denge": {"FX": F[0], "FY": F[1], "FZ": F[2], "MX": Mm[0], "MY": Mm[1], "MZ": Mm[2]},
            "yaylar": [dict(y) for y in kisa_m["yaylar"]]}


# ============================================================================
# Yük durumu paketi (numpy dizileri): süperpozisyon, kombinasyonlar ve zarf yeniden çözümsüz
# ============================================================================
class _Paket:
    """Bina koordinatlı KISA'ları düz numpy dizilerine çevirir: u (n), dug (nd×6), tep (nt×6), uc (ne×12),
    diy (Σ 6·ns_e, eleman blokları), denge (6), yay (ny). Kombinasyon = Σ γ·dizi; KISA'ya geri çevrilir."""

    def __init__(self, kisalar):
        ilk = next(iter(kisalar.values()))
        self.dugum_no = [d["no"] for d in ilk["dugumler"]]
        self.tepki_dugum = [t["dugum"] for t in ilk["tepkiler"]]
        self.yay_meta = [{a: y.get(a) for a in ("dugum", "sd", "bilesen", "k")} for y in ilk["yaylar"]]
        self.el_no = [e["no"] for e in ilk["elemanlar"]]
        self.el_x = [list(e["x"]) for e in ilk["elemanlar"]]
        self.ns = [len(x) for x in self.el_x]
        self.ofs = []
        o = 0
        for n in self.ns:
            self.ofs.append(o)
            o += 6 * n
        self.L = o
        self.durum = {}
        for ad, k in kisalar.items():
            self.ekle(ad, k)

    def ekle(self, ad, k):
        for e0, e1 in zip(self.el_x, k["elemanlar"]):
            if len(e0) != len(e1["x"]) or any(abs(a - b) > 1e-9 for a, b in zip(e0, e1["x"])):
                raise MatrisHatasi(f"Kombinasyon kurulamadı: eleman {e1['no']} için {ad} durumunun diyagram istasyonları ötekilerden "
                                   "farklı; coz_coklu bütün durumları ortak istasyonlarda vermelidir.")
        diy = np.zeros(self.L)
        for j, e in enumerate(k["elemanlar"]):
            blok = np.array([e[a] for a in _DIYAGRAM], dtype=float).reshape(-1)
            diy[self.ofs[j]:self.ofs[j] + 6 * self.ns[j]] = blok
        self.durum[ad] = {
            "u": np.array(k["u"], dtype=float),
            "dug": np.array([[d[a] for a in ("uX", "uY", "uZ", "rX", "rY", "rZ")] for d in k["dugumler"]], dtype=float).reshape(-1, 6),
            "tep": np.array([[t[a] for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")] for t in k["tepkiler"]], dtype=float).reshape(-1, 6),
            "uc": np.array([e["uc_kuvvetleri"] for e in k["elemanlar"]], dtype=float).reshape(-1, 12),
            "diy": diy,
            "denge": np.array([k["denge"][a] for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")], dtype=float),
            "yay": np.array([y["kuvvet"] for y in k["yaylar"]], dtype=float),
        }

    def birlesim(self, katsayilar):
        """Σ γ_ad · durum_ad (yalnız mevcut durumlar)."""
        adlar = [ad for ad in katsayilar if ad in self.durum]
        if not adlar:
            raise MatrisHatasi(f"Kombinasyon için hiçbir yük durumu yok: {list(katsayilar)}.")
        out = {}
        for anahtar in ("u", "dug", "tep", "uc", "diy", "denge", "yay"):
            out[anahtar] = sum(float(katsayilar[ad]) * self.durum[ad][anahtar] for ad in adlar)
        return out

    def kisa(self, arr):
        """Dizi kümesi → bina koordinatında KISA sözlüğü (enb dahil)."""
        elemanlar = []
        for j, no in enumerate(self.el_no):
            blok = arr["diy"][self.ofs[j]:self.ofs[j] + 6 * self.ns[j]].reshape(6, self.ns[j])
            k = {"no": no, "x": list(self.el_x[j]), "uc_kuvvetleri": [float(v) for v in arr["uc"][j]]}
            for a, satir in zip(_DIYAGRAM, blok):
                k[a] = [float(v) for v in satir]
            k["enb"] = _enb(k)
            elemanlar.append(k)
        return {"u": [float(v) for v in arr["u"]],
                "dugumler": [{"no": no, **{a: float(v) for a, v in zip(("uX", "uY", "uZ", "rX", "rY", "rZ"), arr["dug"][i])}}
                             for i, no in enumerate(self.dugum_no)],
                "tepkiler": [{"dugum": no, **{a: float(v) for a, v in zip(("FX", "FY", "FZ", "MX", "MY", "MZ"), arr["tep"][i])}}
                             for i, no in enumerate(self.tepki_dugum)],
                "elemanlar": elemanlar,
                "denge": {a: float(v) for a, v in zip(("FX", "FY", "FZ", "MX", "MY", "MZ"), arr["denge"])},
                "yaylar": [dict(m, kuvvet=float(arr["yay"][i])) for i, m in enumerate(self.yay_meta)]}

    def ozet(self, arr):
        """Kombinasyon özeti: en büyük mutlak diyagram değerleri (eleman bağımsız), en büyük düğüm ötelemeleri, Σ tepki FZ."""
        enb = {}
        for a_i, a in enumerate(_DIYAGRAM):
            en = 0.0
            for j in range(len(self.el_no)):
                blok = arr["diy"][self.ofs[j] + a_i * self.ns[j]:self.ofs[j] + (a_i + 1) * self.ns[j]]
                if blok.size:
                    en = max(en, float(np.max(np.abs(blok))))
            enb[a] = en
        dug = arr["dug"]
        return {"enb": enb, "u_enb": {"X": float(np.max(np.abs(dug[:, 0]))) if dug.size else 0.0,
                                      "Y": float(np.max(np.abs(dug[:, 1]))) if dug.size else 0.0,
                                      "Z": float(np.max(np.abs(dug[:, 2]))) if dug.size else 0.0},
                "FZ_tepki": float(np.sum(arr["tep"][:, 2])) if arr["tep"].size else 0.0,
                "denge_enb": float(np.max(np.abs(arr["denge"])))}


def _kisa_birlesim(kisalar, katsayilar):
    """u_komb = Σ γ_i u_i; iç kuvvetler, tepkiler, denge aynı katsayılarla (yeniden çözüm yok)."""
    p = _Paket({ad: kisalar[ad] for ad in katsayilar if ad in kisalar})
    return p.kisa(p.birlesim(katsayilar))


# ============================================================================
# Kombinasyon listesi (küme şablonlarının W / Ed(H) / Ed(Z) yön-dışmerkezlik çoğaltımı) ve zarf
# ============================================================================
_W_YONLER = ("W+X", "W-X", "W+Y", "W-Y")
_E_TEKLI = ("EX+", "EX-", "EY+", "EY-")


def _isaretli(k):
    return ("+" if k >= 0 else "-") + ("" if abs(abs(k) - 1.0) < 1e-9 else _f(abs(k), 4))


def _komb_adi(katsayilar):
    """Kombinasyon adı katsayılardan, sabit durum sırasıyla: G, Q, S, W±X/W±Y, EX±, EY±, EZ. Katsayı 1 yazılmaz, eksi işaret
    terimin önüne gelir: {"G": 1, "Q": 1, "S": 0.2, "EX+": 1, "EY+": 0.3, "EZ": 0.3} → "G+Q+0.2S+EX++0.3EY++0.3EZ";
    {"G": 0.9, "EX-": 1, "EY+": 0.3, "EZ": -0.3} → "0.9G+EX-+0.3EY+-0.3EZ"; {"G": 1, "Q": 1.3, "W+X": 1.3} → "G+1.3Q+1.3W+X"."""
    def sira(d):
        for i, on in enumerate(("G", "Q", "S", "W", "EX", "EY", "EZ")):
            if d == on or d.startswith(on):
                return (i, d)
        return (9, d)
    parcalar = []
    for d in sorted((d for d, v in katsayilar.items() if abs(v) > 1e-12), key=sira):
        t = _isaretli(katsayilar[d]) + d
        parcalar.append(t[1:] if not parcalar and t.startswith("+") else t)
    return "".join(parcalar) or "0"


def _eh_varyantlari():
    """TBDY Denk. (4.9): ±E_d(X) ± 0,3·E_d(Y) ve ±0,3·E_d(X) ± E_d(Y); E_d(X) ∈ {EX+, EX-}, E_d(Y) ∈ {EY+, EY-}
    (dışmerkezlik ±) → 2 × 2 × 2 × 2 × 2 = 32 varyant. Her öğe (etiket, {durum: katsayı})."""
    out = []
    for px, py in ((1.0, 0.3), (0.3, 1.0)):
        for sx in (1.0, -1.0):
            for sy in (1.0, -1.0):
                for ex in ("+", "-"):
                    for ey in ("+", "-"):
                        kx, ky = sx * px, sy * py
                        out.append((f"{_isaretli(kx)}EX{ex}{_isaretli(ky)}EY{ey}", {f"EX{ex}": kx, f"EY{ey}": ky}))
    return out


def _kombinasyon_listesi(B, mevcut):
    """Kümedeki her şablon satırı eldeki durumlarla açılır: W → 4 yön (W+X, W-X, W+Y, W-Y), EH → Denk. (4.9)'un 32 varyantı
    (drift satırında 4 tekli EX±/EY±), EZ → (2/3)·S_DS·G durumu. Satırın ``gerekli`` durumu (6.4'te T, 6.9/6.10'da H, kar
    satırlarında S) yoksa satır uygulanmaz; ikincil terimler (4.11'de 0,2S, 4.12'de H) yoksa sıfır alınır. Ad katsayılardan
    kurulur (``_komb_adi``). Dönüş [{ad, aile, katsayilar, tur, kaynak, not, uygulandi, neden, yon}]."""
    kume = yv.KOMBINASYONLAR[B.kombinasyon_kumesi]
    liste, adlar = [], set()

    def var_mi(d):
        if d == "W":
            return "W+X" in mevcut
        if d in ("EH", "EZ"):
            return "EX+" in mevcut
        return d in mevcut

    for satir in kume["liste"]:
        kat = dict(satir["katsayilar"])
        temel = {"aile": satir["ad"], "tur": satir["tur"], "kaynak": satir["kaynak"], "not": satir.get("not", "")}
        eksik = [d for d in kat if (d in ("G", "Q", "W", "EH", "EZ") or d in satir.get("gerekli", ())) and not var_mi(d)]
        if eksik:
            neden = ", ".join(f"{d} ({yv.YUK_DURUMU_ADLARI.get(d, d)})" for d in eksik) + " durumu yok"
            ad = satir["ad"] if satir["ad"] not in adlar else f"{satir['ad']} [{satir['kaynak']}]"
            adlar.add(ad)
            liste.append({"ad": ad, **temel, "katsayilar": kat, "uygulandi": False, "neden": neden, "yon": None})
            continue
        sifir = [d for d in kat if d in ("T", "H", "S") and not var_mi(d)]
        if sifir:   # sıcaklık/oturma ve toprak itkisi bu modülde üretilmez, kar kapalıysa S = 0: ikincil terim düşer
            ek = ", ".join(sifir) + (" = 0 (kar yükü kapalı)" if sifir == ["S"] else " = 0 (bu modülde üretilmez / kapalı)")
            temel = dict(temel, **{"not": (temel["not"] + "; " if temel["not"] else "") + ek})
        varyantlar = [({k: v for k, v in kat.items() if k not in ("W", "EH", "EZ") and k not in sifir}, {})]
        if "W" in kat:
            varyantlar = [({**ks, w: kat["W"]}, {**yon, "W": w}) for ks, yon in varyantlar for w in _W_YONLER]
        if "EH" in kat:
            yeni = []
            for ks, yon in varyantlar:
                if satir["tur"] == "drift":
                    yeni += [({**ks, e: kat["EH"]}, {**yon, "EH": e}) for e in _E_TEKLI]
                else:
                    for eh_ad, eh_k in _eh_varyantlari():
                        ks2 = dict(ks)
                        for d, v in eh_k.items():
                            ks2[d] = ks2.get(d, 0.0) + v * kat["EH"]
                        yeni.append((ks2, {**yon, "EH": eh_ad}))
            varyantlar = yeni
        if "EZ" in kat:
            varyantlar = [({**ks, "EZ": ks.get("EZ", 0.0) + kat["EZ"]}, yon) for ks, yon in varyantlar]
        for ks, yon in varyantlar:
            ks = {d: float(v) for d, v in ks.items()}
            ad = _komb_adi(ks)
            ozdes = next((k for k in liste if k["uygulandi"] and k["katsayilar"] == ks), None)
            if ozdes is not None or ad in adlar:
                ad2 = f"{ad} [{satir['kaynak']}]"
                adlar.add(ad2)
                liste.append({"ad": ad2, **temel, "katsayilar": ks, "uygulandi": False, "yon": yon or None,
                              "neden": f"{ozdes['ad'] if ozdes else ad} ile özdeş" + (f" ({', '.join(sifir)} = 0)" if sifir else "")})
                continue
            adlar.add(ad)
            liste.append({"ad": ad, **temel, "katsayilar": ks, "uygulandi": True, "neden": None, "yon": yon or None})
    return liste


def _cozum_katsayilari(k, paket):
    """Kombinasyonun hesapta kullanılan katsayıları: deprem (ve öteleme) birleşimlerinde G, Q, S yerine çatlamış kesitli
    kopyaları G~c, Q~c, S~c (TBDY 4.5.8.3; çatlamış çözüm varsa). Ad ve görünen katsayılar değişmez."""
    if k["tur"] not in ("deprem", "drift"):
        return dict(k["katsayilar"])
    return {(d + _CATLAMIS_EK if d + _CATLAMIS_EK in paket.durum else d): v for d, v in k["katsayilar"].items()}


def _zarf_paket(paket, kombinasyonlar):
    """Uygulanan dayanım/deprem/servis kombinasyonları üzerinde her eleman, her diyagram için max/min ve belirleyen ad.
    Γ (nc × ndurum) @ D (ndurum × L) tek matris çarpımı; eleman bloklarında istasyon ekseni boyunca uç değer."""
    uyg = [k for k in kombinasyonlar if k["uygulandi"] and k["tur"] != "drift"]
    if not uyg:
        return {"elemanlar": [], "kombinasyonlar": []}
    adlar_d = list(paket.durum)
    G = np.zeros((len(uyg), len(adlar_d)))
    for i, k in enumerate(uyg):
        for d, g in k.get("cozum", k["katsayilar"]).items():
            if d in paket.durum:
                G[i, adlar_d.index(d)] = g
    D = np.array([paket.durum[d]["diy"] for d in adlar_d])
    C = G @ D
    elemanlar = []
    for j, no in enumerate(paket.el_no):
        blok = C[:, paket.ofs[j]:paket.ofs[j] + 6 * paket.ns[j]].reshape(len(uyg), 6, paket.ns[j])
        mx, mn = blok.max(axis=2), blok.min(axis=2)        # (nc, 6)
        imx, imn = mx.argmax(axis=0), mn.argmin(axis=0)
        k, bel = {"no": no}, {}
        for a_i, a in enumerate(_DIYAGRAM):
            k[a + "_max"], k[a + "_min"] = float(mx[imx[a_i], a_i]), float(mn[imn[a_i], a_i])
            bel[a + "_max"], bel[a + "_min"] = uyg[imx[a_i]]["ad"], uyg[imn[a_i]]["ad"]
        k["belirleyen"] = bel
        elemanlar.append(k)
    return {"elemanlar": elemanlar, "kombinasyonlar": [k["ad"] for k in uyg]}


def _zarf(sonuclar):
    """Verilen KISA sözlüğü üzerinde (geriye uyumlu) zarf: her eleman, her istasyon için max/min ve belirleyen kombinasyon."""
    adlar = list(sonuclar)
    if not adlar:
        return {"elemanlar": [], "kombinasyonlar": []}
    p = _Paket(sonuclar)
    return _zarf_paket(p, [{"ad": ad, "katsayilar": {ad: 1.0}, "uygulandi": True, "tur": "dayanim"} for ad in adlar])


# ============================================================================
# Yük akışı: kiriş → kolon → temel; yük alanı (tributary) el hesabı; korunum; sankey
# ============================================================================
def _kolon_N(kisa, eleman_no):
    """Kolon elemanının eksenel kuvveti, basınç pozitif (FE: N = −f[0], çekme +)."""
    e = next(x for x in kisa["elemanlar"] if x["no"] == eleman_no)
    return e["uc_kuvvetleri"][0]


def _dugum_payi(B, Y, ix, iy, kat):
    """Bir aks kesişiminin kat payı (yük alanı yöntemi): komşu panellerin çeyreği × (g, q) + komşu kiriş parçalarının
    yarısı (öz + duvar + ek) + düğüm yükü (kolon öz ağırlığı dahil). Dönüş (G, Q, A_trib)."""
    G = Q = A = 0.0
    for d in Y.dosemeler:
        if d["kat"] == kat and ix in (d["ix0"], d["ix1"]) and iy in (d["iy0"], d["iy1"]):
            a = d["alan"] / 4.0
            A += a
            G += d["g"] * a
            Q += d["q_top"] * a
    for key, hav in Y.kiris_yuk.items():
        k_, yon, sabit, i = key
        if k_ != kat:
            continue
        uclar = [(i, sabit), (i + 1, sabit)] if yon == "x" else [(sabit, i), (sabit, i + 1)]
        if (ix, iy) in uclar:
            L = (B.xk[i + 1] - B.xk[i]) if yon == "x" else (B.yk[i + 1] - B.yk[i])
            G += hav["G"]["duzgun"] * L / 2.0
            Q += hav["Q"]["duzgun"] * L / 2.0
    hav = Y.dugum_yuk.get((ix, iy, kat))
    if hav:
        G += -hav["G"][2]
        Q += -hav["Q"][2]
    return G, Q, A


def _tasiyan_kolonlar(B, kat, ix, iy):
    """Kolonsuz bir düğümü taşıyan iki kolon: kiriş çizgisi boyunca iki yönde ilk kolonlu düğüm aranır (kiriş parçaları
    kesintisiz olmalı); önce X, sonra Y doğrultusu denenir. Dönüş [((ix, iy), uzaklık), ...] ya da []."""
    for yon in ("x", "y"):
        bulunan = []
        n = len(B.xk) if yon == "x" else len(B.yk)
        konum = B.xk if yon == "x" else B.yk
        i0 = ix if yon == "x" else iy
        sabit = iy if yon == "x" else ix
        for adim in (-1, 1):
            i = i0
            while True:
                parca = (kat, yon, sabit, i - 1 if adim < 0 else i)
                if parca not in B.kiris_parca:
                    break
                i += adim
                if not 0 <= i < n:
                    break
                dugum = (i, sabit) if yon == "x" else (sabit, i)
                if (dugum[0], dugum[1], kat) in B.kolon_key:
                    bulunan.append((dugum, abs(konum[i] - konum[i0])))
                    break
        if len(bulunan) == 2:
            return bulunan
    return []


def _yuk_alani(B, Y):
    """Yük alanı (tributary) el hesabı, kat kat yukarıdan aşağıya: her düğümün kat payı; kolonsuz düğümün payı
    (ve üstündeki kolondan inen yük) onu taşıyan kirişin iki ucundaki kolonlara basit kiriş tepkisi oranıyla
    (uzaklıkla ters orantılı) dağıtılır. Dönüş ({kolon_no: {"G", "Q", "A", "pay_G", "pay_Q"}}, dagitilamayan)."""
    sonuc = {}
    kum = {}                       # (ix, iy, kat) → üstten inen (G, Q) (kolonlu düğümde kolon kümülatifi)
    dagitilamayan = {"G": 0.0, "Q": 0.0}
    for kat in range(B.nk, 0, -1):
        dugumler = {(ix, iy) for d in Y.dosemeler if d["kat"] == kat for ix in (d["ix0"], d["ix1"]) for iy in (d["iy0"], d["iy1"])}
        for key in Y.kiris_yuk:
            k_, yon, sabit, i = key
            if k_ == kat:
                dugumler |= {(i, sabit), (i + 1, sabit)} if yon == "x" else {(sabit, i), (sabit, i + 1)}
        dugumler |= {(c["ix"], c["iy"]) for c in B.kolonlar if c["kat"] == kat}
        dugumler |= {(ix, iy) for (ix, iy, k_) in Y.dugum_yuk if k_ == kat}
        paylar = {}
        for ix, iy in dugumler:
            g, q, a = _dugum_payi(B, Y, ix, iy, kat)
            inen = kum.pop((ix, iy, kat), (0.0, 0.0))
            paylar[(ix, iy)] = [g + inen[0], q + inen[1], a]
        # kolonsuz düğümler → taşıyan kolonlara
        for (ix, iy), (g, q, a) in list(paylar.items()):
            if (ix, iy, kat) in B.kolon_key:
                continue
            tas = _tasiyan_kolonlar(B, kat, ix, iy)
            if not tas:
                dagitilamayan["G"] += g
                dagitilamayan["Q"] += q
                continue
            (d1, u1), (d2, u2) = tas
            for d_, oran in ((d1, u2 / (u1 + u2)), (d2, u1 / (u1 + u2))):
                paylar[d_][0] += g * oran
                paylar[d_][1] += q * oran
        for c in B.kolonlar:
            if c["kat"] != kat:
                continue
            g, q, a = paylar.get((c["ix"], c["iy"]), (0.0, 0.0, 0.0))
            sonuc[c["no"]] = {"G": g, "Q": q, "A": a}
            kum[(c["ix"], c["iy"], kat - 1)] = (g, q)
    return sonuc, dagitilamayan


def _mesnet_kuvvetleri(kisa):
    """Her temel düğümü için destek kuvvetleri (bina koordinatı): tepkiler + yay kuvvetleri (elastik temel).
    Yay: motor ky → FZ, krx → MX, krz → MY = −M_z,m (eksen eşlemesi). Dönüş {dugum: {"FZ", "MX", "MY"}}."""
    top = {}
    for t in kisa["tepkiler"]:
        top[t["dugum"]] = {"FZ": t["FZ"], "MX": t["MX"], "MY": t["MY"]}
    for y in kisa["yaylar"]:
        h = top.setdefault(y["dugum"], {"FZ": 0.0, "MX": 0.0, "MY": 0.0})
        if y.get("bilesen") == "Fy":
            h["FZ"] += y["kuvvet"]
        elif y.get("bilesen") == "Mx":
            h["MX"] += y["kuvvet"]
        elif y.get("bilesen") == "Mz":
            h["MY"] += -y["kuvvet"]
    return top


def _akis(B, Y, ag, durumlar_kisa):
    """Kolon tabloları (FE ve yük alanı), temel taban basıncı, korunum (beş sayı) ve sankey bantları."""
    G, Q = durumlar_kisa["G"], durumlar_kisa["Q"]
    kolon_key = {(c["ix"], c["iy"], c["kat"]): c for c in B.kolonlar}
    trib, dagitilamayan = _yuk_alani(B, Y)
    kolonlar = []
    for c in sorted(B.kolonlar, key=lambda c: (c["ix"], c["iy"], -c["kat"])):
        NkG, NkQ = _kolon_N(G, c["eleman"]), _kolon_N(Q, c["eleman"])
        ust = kolon_key.get((c["ix"], c["iy"], c["kat"] + 1))
        NuG = _kolon_N(G, ust["eleman"]) if ust else 0.0
        NuQ = _kolon_N(Q, ust["eleman"]) if ust else 0.0
        t = trib[c["no"]]
        tG, tQ, tA = t["G"], t["Q"], t["A"]
        fark = (NkG + NkQ - tG - tQ) / (tG + tQ) * 100.0 if (tG + tQ) > 1e-9 else 0.0
        kolonlar.append({"no": c["no"], "kat": c["kat"], "aks": c["aks"], "adres": c["adres"], "eleman": c["eleman"],
                         "N_G": NkG - NuG, "N_Q": NkQ - NuQ, "N_kum_G": NkG, "N_kum_Q": NkQ,
                         "N_trib_G": tG, "N_trib_Q": tQ, "A_trib": tA, "fark_yuzde": fark})
    # temeller: destek kuvvetleri = tepkiler + yay kuvvetleri; temel öz ağırlığı γ_b·B·L·h servis N'e eklenir
    temeller = []
    q_em = B.temeller["zemin"]["q_em"]
    h_t = B.temeller["varsayilan"]["h"]
    desG, desQ = _mesnet_kuvvetleri(G), _mesnet_kuvvetleri(Q)
    for m in ag["mesnetler"]:
        c = kolon_key.get((B.ax[m["aks"][0]], B.ay[m["aks"][1]], 1))
        tg, tq = desG.get(m["dugum"]), desQ.get(m["dugum"])
        if c is None or tg is None or tq is None:
            continue
        Bt, Lt = m["B"], m["L"]
        NG, NQ = tg["FZ"], tq["FZ"]
        Nt = GAMMA_BA * Bt * Lt * h_t
        N = NG + NQ + Nt
        MX, MY = tg["MX"] + tq["MX"], tg["MY"] + tq["MY"]
        A = Bt * Lt
        sig_m = 6.0 * abs(MX) / (Bt * Lt * Lt) + 6.0 * abs(MY) / (Lt * Bt * Bt)
        s_max, s_min = N / A + sig_m, N / A - sig_m
        eX, eY = (abs(MY) / N, abs(MX) / N) if N > 1e-9 else (0.0, 0.0)
        temeller.append({"kolon_no": c["no"], "aks": c["aks"], "dugum": m["dugum"], "B": Bt, "L": Lt, "h": h_t,
                         "N_G": NG, "N_Q": NQ, "N_temel": Nt, "N_servis": N,
                         "MX": MX, "MY": MY, "sigma_max": s_max, "sigma_min": s_min, "e_X": eX, "e_Y": eY, "q_em": q_em,
                         "DC": s_max / q_em if q_em else 0.0, "cekirdek_icinde": eX <= Bt / 6.0 + 1e-9 and eY <= Lt / 6.0 + 1e-9})
    # korunum
    korunum = {}
    for durum, kisa in (("G", G), ("Q", Q)):
        p = dict(Y.korunum_parcalari[durum])
        p["kolon_taban"] = sum(k["N_kum_" + durum] for k in kolonlar if k["kat"] == 1)
        p["kat0"] = Y.kat0[durum]                                   # temel seviyesine doğrudan verilen düğüm yükü
        p["tepki"] = sum(t["FZ"] for t in kisa["tepkiler"])
        # elastik temelde düşey yük yaylara gider: F_yay = −k·u (yayın yapıya uyguladığı, yukarı +); motor Fy = bina FZ
        p["yay"] = sum(y["kuvvet"] for y in kisa["yaylar"] if y.get("bilesen") == "Fy")
        p["temel"] = p["tepki"] + p["yay"]
        p["yuk_alani"] = sum(trib[k["no"]][durum] for k in kolonlar if k["kat"] == 1) + dagitilamayan[durum]
        p["dagitilamayan"] = dagitilamayan[durum]
        korunum[durum] = p
    # sankey
    sankey = []
    el_no = {e["no"]: e for e in ag["elemanlar"]}
    for d in Y.dosemeler:
        for p in d["paylar"]:
            for durum, kN in (("G", p["toplam_G"]), ("Q", p["toplam_Q"])):
                if kN > 1e-9:
                    sankey.append({"kaynak": f"D{d['no']}", "hedef": f"K{p['kiris_no']}", "durum": durum, "kN": kN})
    for durum, kisa in (("G", G), ("Q", Q)):
        # kiriş uç kesmeleri → düğüm → kolon (ya da taşıyan kiriş)
        dugum_gelen = {}
        for e in kisa["elemanlar"]:
            ae = el_no[e["no"]]
            if ae["tur"] != "kiris":
                continue
            for uc, idx in ((0, 1), (1, 7)):
                dno = ae["dugumler"][uc]
                dugum_gelen.setdefault(dno, []).append((ae["kaynak_no"], e["uc_kuvvetleri"][idx]))
        for dno, liste in dugum_gelen.items():
            dg = ag["dno"][dno]
            ix, iy, kat = dg["key"]
            c = kolon_key.get((ix, iy, kat))
            hedef = f"S{c['no']}/k{kat}" if c else None
            net = {}
            for kno, v in liste:
                net[kno] = net.get(kno, 0.0) + v
            alan = [k for k, v in net.items() if v < -1e-9]
            for kno, v in net.items():
                if v > 1e-9:
                    h = hedef or (f"K{alan[0]}" if len(alan) == 1 else f"N-{dg['adres']}")
                    sankey.append({"kaynak": f"K{kno}", "hedef": h, "durum": durum, "kN": v})
        for k in kolonlar:
            N = k["N_kum_" + durum]
            if N <= 1e-9:
                continue
            alt = kolon_key.get((B.ax[k["aks"][0]], B.ay[k["aks"][1]], k["kat"] - 1))
            if k["kat"] == 1:
                hedef = f"T-{k['aks'][0]}{k['aks'][1]}"
            elif alt:
                hedef = f"S{alt['no']}/k{k['kat'] - 1}"
            else:
                hedef = f"N-{k['aks'][0]}{k['aks'][1]}/k{k['kat'] - 1}"
            sankey.append({"kaynak": f"S{k['no']}/k{k['kat']}", "hedef": hedef, "durum": durum, "kN": N})
        for t in temeller:
            sankey.append({"kaynak": f"T-{t['aks'][0]}{t['aks'][1]}", "hedef": "Zemin", "durum": durum, "kN": t["N_" + durum]})
    return {"kolonlar": kolonlar, "temeller": temeller, "korunum": korunum, "sankey": sankey}


# ============================================================================
# Şemalar (mevcut _Cizim ile; düzlem çizici için sahte model: px, py)
# ============================================================================
def _cizici(noktalar, genislik=420.0):
    M = SimpleNamespace(dugumler=[SimpleNamespace(px=float(x), py=float(y)) for x, y in noktalar], uc=False, elemanlar=[])
    return se._Cizim(M, genislik=genislik)


def _sema_plan(B, Y, kat):
    """Kat planı: akslar, kolonlar, kirişler, döşemeler, 45° çizgiler ve kiriş üstünde üçgen/trapez/düzgün yük şekilleri (G)."""
    c = _cizici([(B.xk[0], B.yk[0]), (B.xk[-1], B.yk[-1])])
    pay = 0.06 * max(B.xk[-1] - B.xk[0], B.yk[-1] - B.yk[0], 1.0)
    for i, x in enumerate(B.xk):
        c.cizgi(c.P(x, B.yk[0] - pay), c.P(x, B.yk[-1] + pay), "n", kalin=0.8, kesik="4 4", opak=0.7)
        c.yazi(*c.P(x, B.yk[-1] + 1.6 * pay), B.xad[i], boyut=12, kalin=True)
    for j, y in enumerate(B.yk):
        c.cizgi(c.P(B.xk[0] - pay, y), c.P(B.xk[-1] + pay, y), "n", kalin=0.8, kesik="4 4", opak=0.7)
        c.yazi(*c.P(B.xk[0] - 1.6 * pay, y), B.yad[j], boyut=12, kalin=True)
    tepe_max = max([p["tepe_g"] for d in Y.dosemeler if d["kat"] == kat for p in d["paylar"]] + [1e-9])
    hmax = 0.22 * min([min(d["dx"], d["dy"]) for d in Y.dosemeler if d["kat"] == kat] + [1.0])
    for d in Y.dosemeler:
        if d["kat"] != kat:
            continue
        x0, y0, x1, y1 = B.xk[d["ix0"]], B.yk[d["iy0"]], B.xk[d["ix1"]], B.yk[d["iy1"]]
        c.poligon([c.P(x0, y0), c.P(x1, y0), c.P(x1, y1), c.P(x0, y1)], "c")
        lx = d["lx"]
        if d["tip"] == "cift":
            if d["dx"] <= d["dy"]:   # kısa kenar x: üçgen alt/üst, trapez sol/sağ; 45° çizgiler köşelerden
                mid = lx / 2.0
                c.yol([c.P(x0, y0), c.P(x0 + mid, y0 + mid), c.P(x0 + mid, y1 - mid), c.P(x0, y1)], "a", kalin=1.0, kesik="3 3")
                c.yol([c.P(x1, y0), c.P(x1 - mid, y0 + mid), c.P(x1 - mid, y1 - mid), c.P(x1, y1)], "a", kalin=1.0, kesik="3 3")
                c.cizgi(c.P(x0 + mid, y0 + mid), c.P(x1 - mid, y0 + mid), "a", kalin=1.0, kesik="3 3")
                c.cizgi(c.P(x0 + mid, y1 - mid), c.P(x1 - mid, y1 - mid), "a", kalin=1.0, kesik="3 3")
            else:
                mid = lx / 2.0
                c.yol([c.P(x0, y0), c.P(x0 + mid, y0 + mid), c.P(x1 - mid, y0 + mid), c.P(x1, y0)], "a", kalin=1.0, kesik="3 3")
                c.yol([c.P(x0, y1), c.P(x0 + mid, y1 - mid), c.P(x1 - mid, y1 - mid), c.P(x1, y1)], "a", kalin=1.0, kesik="3 3")
                c.cizgi(c.P(x0 + mid, y0 + mid), c.P(x0 + mid, y1 - mid), "a", kalin=1.0, kesik="3 3")
                c.cizgi(c.P(x1 - mid, y0 + mid), c.P(x1 - mid, y1 - mid), "a", kalin=1.0, kesik="3 3")
        else:
            for t in (0.35, 0.5, 0.65):
                if d["dx"] <= d["dy"]:
                    c.ok(c.P(x0 + t * d["dx"], (y0 + y1) / 2), c.P(x0 + t * d["dx"], y0 + 0.1 * d["dy"]), "a", kalin=1.0, uc=5.0)
                    c.ok(c.P(x0 + t * d["dx"], (y0 + y1) / 2), c.P(x0 + t * d["dx"], y1 - 0.1 * d["dy"]), "a", kalin=1.0, uc=5.0)
                else:
                    c.ok(c.P((x0 + x1) / 2, y0 + t * d["dy"]), c.P(x0 + 0.1 * d["dx"], y0 + t * d["dy"]), "a", kalin=1.0, uc=5.0)
                    c.ok(c.P((x0 + x1) / 2, y0 + t * d["dy"]), c.P(x1 - 0.1 * d["dx"], y0 + t * d["dy"]), "a", kalin=1.0, uc=5.0)
        c.yazi(*c.P((x0 + x1) / 2, (y0 + y1) / 2), f"D{d['no']}  m = {_f(d['m'], 2)}  ({'çift' if d['tip'] == 'cift' else 'tek'})", boyut=11, kalin=True)
        for p in d["paylar"]:
            if p["sekil"] == "yok":
                continue
            h = hmax * p["tepe_g"] / tepe_max
            pts = []
            for x1_, x2_, f1, f2 in p["parcalar_birim"]:
                for s, fct in ((x1_, f1), (x2_, f2)):
                    if p["kenar_ad"] == "alt":
                        pts.append(c.P(x0 + s, y0 + fct * h))
                    elif p["kenar_ad"] == "ust":
                        pts.append(c.P(x0 + s, y1 - fct * h))
                    elif p["kenar_ad"] == "sol":
                        pts.append(c.P(x0 + fct * h, y0 + s))
                    else:
                        pts.append(c.P(x1 - fct * h, y0 + s))
            c.poligon(pts, "b", katman="orta")
            c.yol(pts, "b", kalin=1.2, sinif="g2")
            if p["kenar_ad"] == "alt":
                et = c.P((x0 + x1) / 2, y0 + h + 0.25 * pay)
            elif p["kenar_ad"] == "ust":
                et = c.P((x0 + x1) / 2, y1 - h - 0.25 * pay)
            elif p["kenar_ad"] == "sol":
                et = c.P(x0 + h + 0.9 * pay, (y0 + y1) / 2)
            else:
                et = c.P(x1 - h - 0.9 * pay, (y0 + y1) / 2)
            c.yazi(et[0], et[1], f"{_f(p['tepe_g'], 1)} kN/m", boyut=10, aile="b")
    for k in B.kirisler:
        if k["kat"] != kat:
            continue
        if k["yon"] == "x":
            a, b = c.P(B.xk[k["i0"]], B.yk[k["sabit"]]), c.P(B.xk[k["i1"]], B.yk[k["sabit"]])
        else:
            a, b = c.P(B.xk[k["sabit"]], B.yk[k["i0"]]), c.P(B.xk[k["sabit"]], B.yk[k["i1"]])
        c.cizgi(a, b, None, kalin=3.0 if not k["duvar"] else 5.0, opak=1.0 if not k["duvar"] else 0.6)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        c.daire((mx, my), 8, aile="b", kalin=1.2, sinif="g3")
        c.yazi(mx, my, f"K{k['no']}", boyut=9, kalin=True)
    for col in B.kolonlar:
        if col["kat"] != kat:
            continue
        X, Yy = c.P(B.xk[col["ix"]], B.yk[col["iy"]])
        w, h = max(6.0, col["bX"] * c.s), max(6.0, col["bY"] * c.s)
        c.dikdortgen(X - w / 2, Yy - h / 2, w, h, aile="a", katman="on")
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 20.0, f"Kat {kat} planı · döşeme payları (G, tepe değeri kN/m) · kesikli: 45° dağılım çizgileri",
           boyut=11, opak=0.8)
    return {"baslik": f"Kat {kat}: döşemeden kirişe yük dağılımı (TS 500 md. 11.4.3)", "svg": c.svg(f"Kat {kat} planı")}


def _sema_ag(B, ag):
    """3B ağ: motor koordinatlarının aksonometrik izdüşümü; kolonlar mavi, kirişler amber, mesnet simgeleri."""
    pts = [se._izdusum(*dg["m"]) for dg in ag["dugumler"]]
    c = _cizici(pts, genislik=440.0)
    idx = {dg["no"]: i for i, dg in enumerate(ag["dugumler"])}
    for e in ag["elemanlar"]:
        a, b = c.D(idx[e["dugumler"][0]]), c.D(idx[e["dugumler"][1]])
        c.cizgi(a, b, "a" if e["tur"] == "kolon" else "b", kalin=2.4 if e["tur"] == "kolon" else 2.0)
    for m in ag["mesnetler"]:
        X, Yy = c.D(idx[m["dugum"]])
        c.mesnet(X, Yy, "ankastre" if m["tip"] == "ankastre" else "sabit", "alt")
    az = len(ag["dugumler"]) <= 40
    for i, dg in enumerate(ag["dugumler"]):
        X, Yy = c.D(i)
        c.daire((X, Yy), 3.0, aile=None, sinif="g0")
        if az:
            c.yazi(X + 9, Yy - 9, str(dg["no"]), boyut=9, opak=0.85, hiza="start")
    k = c._e
    ox, oy = k[0] - 24.0, k[3] + 24.0
    for ad, v in (("X", (1.0, 0.0, 0.0)), ("Y", (0.0, 0.0, -1.0)), ("Z", (0.0, 1.0, 0.0))):
        w = c.yon3(v)
        c.ok((ox, oy), (ox + w[0] * 26.0, oy + w[1] * 26.0), "n", g=0, kalin=1.4, uc=5.0)
        c.yazi(ox + w[0] * 36.0, oy + w[1] * 36.0, ad, boyut=11, opak=0.8)
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"{len(ag['dugumler'])} düğüm · {len(ag['elemanlar'])} eleman · {ag['sd_sayisi']} SD · "
           "mavi: kolon, amber: kiriş", boyut=11, opak=0.8)
    return {"baslik": "Bina ağı (cerceve3b): düğümler, elemanlar, mesnetler", "svg": c.svg("Bina ağı")}


def _sema_kolon_seridi(B, akis):
    """Kolon şeridi: her kolon dizisi için kat kat kümülatif N (G+Q) çubukları."""
    diziler = {}
    for k in akis["kolonlar"]:
        diziler.setdefault(tuple(k["aks"]), []).append(k)
    adlar = sorted(diziler, key=lambda a: (B.ax[a[0]], B.ay[a[1]]))
    nk = B.nk
    gen_x, gen_y = 90.0, 48.0
    c = _cizici([(0, 0), (gen_x * max(len(adlar), 1), gen_y * (nk + 1))], genislik=max(320.0, 70.0 * len(adlar)))
    Nmax = max([k["N_kum_G"] + k["N_kum_Q"] for k in akis["kolonlar"]] + [1e-9])
    for j, kt in enumerate(B.katlar):
        y = gen_y * j
        c.cizgi(c.P(-10, y), c.P(gen_x * len(adlar), y), "n", kalin=0.8, kesik="3 3", opak=0.6)
        c.yazi(*c.P(-22, y + gen_y * 0.5 if j < nk else y), f"k{kt['no']}" if j else "T", boyut=10, opak=0.8)
    for i, ad in enumerate(adlar):
        x = gen_x * (i + 0.5)
        c.yazi(*c.P(x, gen_y * (nk + 1) + 8), f"S {ad[0]}{ad[1]}", boyut=11, kalin=True)
        for k in diziler[ad]:
            N = k["N_kum_G"] + k["N_kum_Q"]
            w = max(4.0, 0.7 * gen_x * N / Nmax)
            y0, y1 = gen_y * (k["kat"] - 1), gen_y * k["kat"]
            X0, Y0 = c.P(x - w / 2, y1)
            X1, Y1 = c.P(x + w / 2, y0)
            c.dikdortgen(X0, Y0, X1 - X0, Y1 - Y0, aile="a")
            c.yazi(*c.P(x, (y0 + y1) / 2), f"{_f(N, 0)}", boyut=10, kalin=True)
        t = next((t for t in akis["temeller"] if tuple(t["aks"]) == ad), None)
        if t:
            X, Yy = c.P(x, -14)
            c.yazi(X, Yy, f"σ={_f(t['sigma_max'], 0)}", boyut=9, aile="c")
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 20.0, "Çubuk genişliği ∝ kümülatif N (G+Q, kN) · altta temel taban basıncı σ_max (kN/m²)",
           boyut=11, opak=0.8)
    return {"baslik": "Kolon şeridi: kat kat biriken eksenel kuvvet", "svg": c.svg("Kolon şeridi")}


# ============================================================================
# Anlatım adımları 1–11
# ============================================================================
def _adim_1(B, anl):
    anl.baslik(B.baslik, 2)
    if B.aciklama:
        anl.metin(B.aciklama)
    se._basla(anl, 1, "Bina tabloları: akslar, katlar, elemanlar, kütüphane kartları",
              "Bir binayı ticari yapı analiz programları da önce tablolarla tanır: aks ızgarası, kat kotları, kolon/kiriş/döşeme "
              "listeleri ve malzeme–kesit kartları. Adresleri (S-B1/k1 = B1 aksındaki 1. kat kolonu) baştan öğrenirsek yük "
              "akışını izlerken kaybolmayız.")
    anl.metin("**Akslar** (X sağa, harfli; Y plan derinliği, sayılı; Z yukarı):\n\n"
              + _tablo(["Yön", "Akslar (ad = konum m)"],
                       [["X", ", ".join(f"{a['ad']} = {_f(a['konum'])}" for a in B.akslar["x"])],
                        ["Y", ", ".join(f"{a['ad']} = {_f(a['konum'])}" for a in B.akslar["y"])]]))
    anl.metin("**Katlar** (kat k kolonu kot_{k−1} ile kot_k arasındadır):\n\n"
              + _tablo(["No", "Ad", "Kot (m)", "Kat yüksekliği (m)"], [[kt["no"], kt["ad"], _f(kt["kot"]), _f(kt["h"]) if kt["no"] else "–"] for kt in B.katlar]))
    anl.metin("**Malzemeler** (MPa; motor kN/m² kullanır: E_kN/m² = 1000·E_MPa):\n\n"
              + _tablo(["Ad", "Kütüphane", "E (MPa)", "G (MPa)", "Dayanım", "γ (kN/m³)", "Kaynak"],
                       [[m["ad"], m["kutuphane"], _f(m["E_MPa"], 0), _f(m["G_MPa"], 0),
                         f"fck = {m['fck']}" if m["tur"] == "beton" else (f"Fy = {m['Fy']}" if m["tur"] == "celik" else f"fyk = {m['fyk']}"),
                         _f(m["gamma"], 1), m["kaynak"].split(";")[0]] for m in B.malzemeler.values()]))
    satir = []
    for k in B.kesitler.values():
        if k["tip"] == "dikdortgen":
            boyut = f"{_f(k['b'] * 100, 0)} × {_f(k['h'] * 100, 0)} cm"
        else:
            boyut = k["profil"]
        satir.append([k["ad"], boyut, k["malzeme"], f"{k['A']:.4g}", f"{k['I_guclu']:.4g}", f"{k['I_zayif']:.4g}", f"{k['J']:.4g}", f"{k['Wpl']:.4g}"])
    anl.metin("**Kesitler** (m, m², m⁴, m³; I_güçlü: h'nin derinlik olduğu eğilme):\n\n"
              + _tablo(["Ad", "Boyut / profil", "Malzeme", "A", "I_güçlü", "I_zayıf", "J", "W_pl"], satir))
    anl.mat(r"A = b\,h,\quad I_{güçlü} = \frac{b\,h^{3}}{12},\quad I_{zayıf} = \frac{h\,b^{3}}{12},\quad "
            r"J \approx \beta\,c^{3}a,\ \ \beta = \tfrac{1}{3} - 0{,}21\tfrac{c}{a}\left(1 - \tfrac{c^{4}}{12a^{4}}\right)\ (c \le a),\quad "
            r"W_{pl} = \frac{b\,h^{2}}{4}")
    anl.metin("Profil kesitlerde değerler katalogdan gelir (I_y güçlü eksen, Avrupa kuralı; cm → m çevrilir).")
    anl.metin("**Kolonlar** (yön: güçlü eksenin çalıştığı doğrultu; bX, bY kesitin X ve Y yönündeki boyutları):\n\n"
              + _tablo(["Adres", "No", "Kat", "Kesit", "Yön", "bX × bY (cm)", "L (m)"],
                       [[c["adres"], c["no"], c["kat"], c["kesit"], c["yon"].upper(), f"{_f(c['bX'] * 100, 0)} × {_f(c['bY'] * 100, 0)}", _f(c["L"])]
                        for c in B.kolonlar]))
    anl.metin("**Kirişler:**\n\n" + _tablo(["Adres", "No", "Kat", "Kesit", "L (m)", "Parça", "Duvar"],
                                           [[k["adres"], k["no"], k["kat"], k["kesit"], _f(k["L"]), len(k["parcalar"]),
                                             f"{k['duvar']} ({_f(B.duvarlar[k['duvar']]['deger'])} kN/m², h = {_f(k['h_duvar'])} m)" if k["duvar"] else "–"]
                                            for k in B.kirisler]))
    if B.dosemeler:
        anl.metin("**Döşemeler:**\n\n" + _tablo(["Adres", "No", "Kat", "h (cm)", "Kullanım", "Dağıtım"],
                                                [[d["adres"], d["no"], d["kat"], _f(d["h"] * 100, 0), d["kullanim"], d["dagitim"]] for d in B.dosemeler]))
    anl.metin(f"Temeller: {B.temeller['tip']}, varsayılan B × L = {_f(B.temeller['varsayilan']['B'])} × {_f(B.temeller['varsayilan']['L'])} m, "
              f"zemin emniyet gerilmesi q_em = {_f(B.temeller['zemin']['q_em'])} kN/m², mesnet modeli **{B.temeller['mesnet']}**.")
    if B.deprem:
        anl.metin(f"Deprem kartı: S_S = {_f(B.deprem['SS'], 3)}, S_1 = {_f(B.deprem['S1'], 3)}, zemin {B.deprem['zemin_sinifi']}, "
                  f"taşıyıcı sistem {B.deprem['tasiyici_kod']} (R = {_f(B.deprem['R'])}, D = {_f(B.deprem['D'])}); eşdeğer deprem yükü 7. adımda.")
    if B.analiz["catlamis_rijitlik"] and B.deprem:
        anl.metin("**Çatlamış (etkin) kesit rijitliği** (TBDY md. 4.5.8, Tablo 4.2): betonarme kolon EI × 0,70, kiriş EI × 0,35. "
                  "4.5.8.1 betonarmede dayanıma göre tasarımda bunu zorunlu kılar; 4.5.8.3 ise yalnız **deprem etkili birleşimlerde ve "
                  "bu birleşimlere giren yükler altında** uygulanmasını ister. Bu yüzden iki rijitlik matrisi kurulur: **brüt K** ile "
                  "G, Q, S, W (1,4G + 1,6Q gibi deprem dışı birleşimler, servis ve yük akışı), **çatlamış K** ile deprem birim durumları "
                  "ve deprem birleşimlerine giren düşey yüklerin kopyaları G~c, Q~c, S~c. Her K içinde süperpozisyon yine doğrusaldır.")
    elif B.analiz["catlamis_rijitlik"]:
        anl.metin("Çatlamış kesit rijitliği seçili, ancak deprem kapalı: Tablo 4.2 yalnız deprem birleşimlerinde uygulandığından "
                  "(TBDY 4.5.8.3) bütün durumlar brüt kesitle çözüldü.")
    elif B.sistem == "betonarme" and B.deprem:
        anl.uyari("Çatlamış kesit rijitliği kapalı (analiz.catlamis_rijitlik = false): TBDY 4.5.8.1'e aykırı; deprem hesabı brüt "
                  "kesitle yapıldı, periyot kısa ve ötelemeler küçük (güvensiz taraf) çıkar.")


def _adim_2(B, Y, anl):
    se._basla(anl, 2, "Yükler (TS 498:2021)",
              "Yük akışı, yükün doğduğu yerde başlar: döşeme alan yükleri (sabit g ve hareketli q), duvarların çizgisel yükü, "
              "kirişlerin ve kolonların öz ağırlığı. TS 498:2021 karakteristik değerleri verir; tasarım değeri kombinasyonla "
              "(1,4G + 1,6Q) sonra oluşur.")
    anl.mat(r"g = \gamma_{ba}\,h_{plak} + g_{ek},\qquad q = q_{TS\,498}\ (\text{Çizelge 6}),\qquad "
            r"g_{duvar} = w_{duvar}\,h_{duvar},\ \ h_{duvar} = h_{kat,\,alt} - h_{kiriş},\qquad g_{öz} = \gamma\,A_{öz}")
    if Y.dosemeler:
        anl.metin("**Döşeme yükleri** (kN/m²):\n\n"
                  + _tablo(["Döşeme", "h (cm)", "Plak γ·h", "g_ek", "g toplam", "q", "Alan (m²)", "G (kN)", "Q (kN)", "q kaynağı"],
                           [[f"D{d['no']}", _f(d["h"] * 100, 0), _f(d["g_plak"]), _f(d["g_ek"] + d["ek_g"]), _f(d["g"]), _f(d["q_top"]),
                             _f(d["alan"]), _f(d["G_toplam"]), _f(d["Q_toplam"]), d["q_kaynak"].split("(")[0]] for d in Y.dosemeler]))
    duvarli = [k for k in B.kirisler if k["duvar"]]
    if duvarli:
        anl.metin("**Duvar yükleri** (kiriş üstünde çizgisel). Kural: duvar oturduğu kirişe yük verir ve yüksekliği **kirişin ALTINDAKİ "
                  "kat yüksekliği − kiriş yüksekliği** alınır (kat yükseklikleri eşitse kirişin üstündeki duvarın net yüksekliğiyle aynıdır). "
                  "Zemin kat duvarları temele/zemine oturur, çerçeveye girmez; çatı kirişine kat yüksekliğinde duvar konmaz, yalnız "
                  "parapet (`duvar_h`, ör. 1,0 m) verilir:\n\n"
                  + _tablo(["Kiriş", "Kat", "Duvar", "w (kN/m²)", "h_duvar (m)", "Yükseklik kuralı", "g_d (kN/m)"],
                           [[f"K{k['no']}", k["kat"], B.duvarlar[k["duvar"]]["aciklama"], _f(B.duvarlar[k["duvar"]]["deger"]), _f(k["h_duvar"]),
                             k["h_duvar_kaynak"], _f(B.duvarlar[k["duvar"]]["deger"] * k["h_duvar"])] for k in duvarli]))
    net = B.analiz["kiris_oz"] == "net"
    anl.metin(("**Öz ağırlıklar** — betonarme kirişte **A_net = b·(h − t_döşeme)**: kirişin döşeme içindeki kısmı döşeme "
               "ağırlığında (γ·h_plak) zaten sayıldı, iki kez sayılmasın diye çıkarıldı (brüt kesite `analiz.kiris_oz = \"brut\"` ile "
               "dönülür; t = kirişe oturan döşemelerin en kalını). Çelik profilde katalog ağırlığı (γ·A):" if net else
               "**Öz ağırlıklar** (brüt kesit, `analiz.kiris_oz = \"brut\"`: kirişin döşeme içindeki kısmı döşemede de sayıldığı için "
               "≈ %5 çift sayım vardır; varsayılan `net` A = b·(h − t) kullanır):") + "\n\n"
              + _tablo(["Eleman", "A_öz (m²)", "γ·A (kN/m)", "Toplam (kN)"],
                       [[f"K{r['no']}", f"{B.kiris_no[r['no']]['A_oz']:.4g}"
                         + (f" = {_f(B.kiris_no[r['no']]['b'], 2)}·({_f(B.kiris_no[r['no']]['h'], 2)} − {_f(B.kiris_no[r['no']]['t_doseme'], 2)})"
                            if B.kiris_no[r["no"]]["t_doseme"] else ""), _f(r["kN_m"]["oz"]), _f(r["G"]["oz"])] for r in Y.kirisler]
                       + [[f"S{c['no']}/k{c['kat']}", f"{B.kolon_no[c['no']]['A']:.4g}", _f(c["oz_kN"] / B.kolon_no[c["no"]]["L"]), _f(c["oz_kN"])]
                          for c in Y.kolonlar]))
    anl.metin("Kolon öz ağırlığı, kolonun üst düğümüne tekil yük olarak verilir (kolon boyunca yayılı olsaydı eksenel kuvvet "
              "alt uca doğru doğrusal artardı; tekil yükte alt kesit aynı toplamı taşır).")
    anl.metin("**Kat toplamları:**\n\n" + _tablo(["Kat", "Kot", "G (kN)", "Q (kN)", "S (kN)", "G + Q"],
                                                  [[k["kat"], _f(k["kot"]), _f(k["G"]), _f(k["Q"]), _f(k["S"]), _f(k["w"])] for k in Y.katlar]
                                                  + [["Toplam", "", _f(Y.toplam["G"]), _f(Y.toplam["Q"]), _f(Y.toplam["S"]), _f(Y.toplam["G"] + Y.toplam["Q"])]]))


def _adim_3(B, Y, anl):
    se._basla(anl, 3, "Döşemeden kirişe: TS 500 md. 11.4.3, 45° kuralı",
              "Döşeme yükü dört kenar kirişine, köşelerden 45° çizilen doğruların ayırdığı alanlara göre gider: kısa kenar "
              "kirişine üçgen, uzun kenar kirişine trapez yük. m = l_u/l_k ≤ 2 ise döşeme çift doğrultulu çalışır; m > 2 ise "
              "tek doğrultulu sayılır ve yük yalnız uzun kenarlara düzgün gider.")
    anl.mat(r"p_{max} = \frac{w\,l_k}{2}\ \text{(kN/m)},\qquad \text{üçgen: } q_{eM} = \frac{w\,l_k}{3},\ q_{eV} = \frac{w\,l_k}{4};\qquad "
            r"\text{trapez: } q_{eM} = \frac{w\,l_k}{2}\Bigl(1 - \frac{1}{3m^{2}}\Bigr),\ q_{eV} = \frac{w\,l_k}{2}\Bigl(1 - \frac{1}{2m}\Bigr)")
    anl.uyari("Eşdeğer düzgün yükler q_eM (açıklık momenti için) ve q_eV (mesnet tepkisi için) TS 500'de yoktur; basit kiriş "
              "eşdeğerliğinden türetilmiş el hesabı araçlarıdır. Sonlu eleman çözümüne **gerçek şekil** (parçalı doğrusal üçgen/trapez) gider.")
    for d in Y.dosemeler:
        sat = [[p["kenar_aciklama"], f"K{p['kiris_no']}", p["kenar"], p["sekil"], _f(p["tepe_g"]), _f(p["q_eM_g"]), _f(p["q_eV_g"]),
                _f(p["toplam_G"]), _f(p["tepe_q"]), _f(p["toplam_Q"])] for p in d["paylar"]]
        topG, topQ = sum(p["toplam_G"] for p in d["paylar"]), sum(p["toplam_Q"] for p in d["paylar"])
        anl.metin(f"**D{d['no']}** (kat {d['kat']}): l_k = {_f(d['lx'])} m, l_u = {_f(d['ly'])} m, m = {_f(d['m'], 3)} → "
                  f"**{'çift' if d['tip'] == 'cift' else 'tek'} doğrultulu**; g = {_f(d['g'])}, q = {_f(d['q_top'])} kN/m²"
                  + (f" ({d['q_kaynak']})" if "balkon" in d["q_kaynak"] else "") + (f". {d['not']}" if d.get("not") else ".") + "\n\n"
                  + _tablo(["Kenar", "Kiriş", "Kenar türü", "Şekil", "G tepe (kN/m)", "q_eM,G", "q_eV,G", "G payı (kN)", "Q tepe", "Q payı (kN)"], sat)
                  + f"\n\nKorunum: Σ paylar = {_f(topG)} kN = g·l_k·l_u = {_f(d['g'])}·{_f(d['lx'])}·{_f(d['ly'])} = {_f(d['G_toplam'])} kN ✓ "
                  f"(Q: {_f(topQ)} = {_f(d['Q_toplam'])} ✓).")
    # aynı planlı katlar (aynı paneller, aynı g/q/s ve dağıtım) tek şemayla gösterilir (yanıt boyutu)
    gruplar = {}
    for k in sorted({d["kat"] for d in Y.dosemeler}):
        imza = tuple(sorted((d["ix0"], d["iy0"], round(d["g"], 6), round(d["q_top"], 6), round(d["s"], 6), d["tip"])
                            for d in Y.dosemeler if d["kat"] == k))
        gruplar.setdefault(imza, []).append(k)
    if gruplar:
        semalar = []
        for katlar in gruplar.values():
            sm = _sema_plan(B, Y, katlar[0])
            if len(katlar) > 1:
                sm = dict(sm, baslik=f"{sm['baslik']} (aynı plan: kat {', '.join(str(k) for k in katlar)})")
            semalar.append(sm)
        anl.sema("Kat planları ve döşeme yük şekilleri", semalar)


def _adim_4(B, Y, anl):
    se._basla(anl, 4, "Kiriş yük dökümü ve el hesabı",
              "Her kirişin üstünde ne var? Döşeme payları (üçgen/trapez), duvar, öz ağırlık ve varsa ek yük. Basit kiriş "
              "kabulüyle uç tepkileri ve açıklık momentini elle hesaplıyoruz; 7. adımda sonlu eleman sonucuyla karşılaştıracağız. "
              "Fark, kirişin sürekliliğinden ve kolon rijitliğinden gelir.")
    anl.mat(r"R = \frac{G_{toplam}}{2}\ (\text{simetrik yük}),\qquad M_{açıklık} \approx \frac{q_{eM}\,L^{2}}{8},\quad "
            r"q_{eM} = g_{öz} + g_{duvar} + g_{ek} + \sum q_{eM,döşeme}")
    anl.metin(_tablo(["Kiriş", "L (m)", "Döşeme G (kN)", "Duvar (kN)", "Öz (kN)", "Ek G (kN)", "G toplam (kN)", "Q toplam (kN)",
                      "R_G (kN)", "q_eM,G (kN/m)", "M_G (kN·m)", "R_Q", "M_Q"],
                     [[f"K{r['no']}", _f(r["L"]), _f(r["G"]["doseme"]), _f(r["G"]["duvar"]), _f(r["G"]["oz"]), _f(r["G"]["ek"]),
                       _f(r["G"]["toplam_kN"]), _f(r["Q"]["toplam_kN"]), _f(r["el_hesabi"]["R_G"]), _f(r["kN_m"]["q_eM_G"]),
                       _f(r["el_hesabi"]["M_G"]), _f(r["el_hesabi"]["R_Q"]), _f(r["el_hesabi"]["M_Q"])] for r in Y.kirisler]))


def _adim_5(B, ag, anl):
    se._basla(anl, 5, "Ağ: bina → uzay çerçeve (cerceve3b) modeli",
              "Şimdi binayı motorun anladığı dile çeviriyoruz: her aks kesişimi × kat bir düğüm, her kolon ve her kiriş parçası "
              "bir uzay çerçeve elemanı. Motor Y'yi yukarı aldığı için koordinatları bir kez eşliyoruz; sonuçları okurken geri çeviriyoruz.")
    anl.mat(r"x_m = X,\quad y_m = Z,\quad z_m = -Y\qquad\Longleftrightarrow\qquad X = x_m,\quad Y = -z_m,\quad Z = y_m")
    anl.metin("Vektörler aynı kuralla döner: (F_X, F_Y, F_Z) = (F_{x,m}, −F_{z,m}, F_{y,m}). Eleman yerel eksenleri motorun Kassimali "
              "kuralıyla gelir (y′ düşey düzlemde yukarı; düşey elemanda z′ = Z_m = −Y_bina, y′ = −X_bina). Bu yüzden:")
    anl.metin("- **Kiriş:** I_z,m = I_güçlü (h düşey), I_y,m = I_zayıf; düşey yük yerel y′ yönündedir (aşağı negatif).\n"
              "- **Kolon:** yön X ise I_z,m = b_Y·b_X³/12 = I_güçlü (bina Y ekseni etrafında eğilme = X yönünde ötelenme), "
              "yön Y ise tersine takas edilir.")
    anl.metin(f"Düğüm numarası = 1000·kat + 20·(X aks sırası) + (Y aks sırası) + 1; **{len(ag['dugumler'])} düğüm**, "
              f"**{len(ag['elemanlar'])} eleman** ({sum(1 for e in ag['elemanlar'] if e['tur'] == 'kolon')} kolon, "
              f"{sum(1 for e in ag['elemanlar'] if e['tur'] == 'kiris')} kiriş parçası), **{ag['sd_sayisi']} SD** (düğüm başına 6).")
    anl.metin(_tablo(["Düğüm", "Adres", "X", "Y", "Z"], [[dg["no"], dg["adres"], _f(dg["X"]), _f(dg["Y"]), _f(dg["Z"])] for dg in ag["dugumler"][:60]])
              + ("\n\n… (ilk 60 düğüm)" if len(ag["dugumler"]) > 60 else ""))
    anl.metin(_tablo(["Eleman", "Tür", "Kaynak", "Düğümler", "L (m)", "Kesit"],
                     [[e["no"], e["tur"], f"{'S' if e['tur'] == 'kolon' else 'K'}{e['kaynak_no']}" + (f" p{e['parca']}" if e["tur"] == "kiris" else ""),
                       f"{e['dugumler'][0]} → {e['dugumler'][1]}", _f(e["L"]), e["kesit"]] for e in ag["elemanlar"][:80]])
              + ("\n\n… (ilk 80 eleman)" if len(ag["elemanlar"]) > 80 else ""))
    anl.metin(f"Mesnetler: {len(ag['mesnetler'])} temel düğümü, hepsi **{ag['mesnetler'][0]['tip'] if ag['mesnetler'] else '–'}**. "
              "Komşu olmayan akslar arasındaki kiriş ara kesişimlerde bölünür; kolonsuz ara düğüm sürekli kirişi verir "
              "(matris yöntemi bunu kendiliğinden doğru çözer).")
    anl.sema("Bina ağı", [_sema_ag(B, ag)])


def _adim_8(B, ag, durumlar_kisa, Y, yol, anl):
    se._basla(anl, 8, "Çözüm: K u = F, bütün sağ taraflar birlikte",
              "Rijitlik matrisi bir kez kurulur, mesnet satır/sütunları atılır, G, Q, S, W ve deprem birim durumlarının sağ tarafları "
              "birlikte çözülür (u = K_ff⁻¹ F; rijit diyaframda indirgenmiş sistem). Sonra her eleman için uç kuvvetleri f = k d − f_eq "
              "ve diyagramlar; sağlama olarak denge toplamları. EX±, EY± ve EZ birim durumların süperpozisyonudur.")
    anl.metin(f"Hesap modu: **sayısal** (numpy), {ag['sd_sayisi']} SD; çözüm yolu `{yol}`. Diyagram istasyonu: "
              f"{B.analiz['diyagram_nokta']} nokta (parça sınırları ve V = 0 noktaları eklenir)."
              + (" Çatlamış kesit rijitliği açık olduğundan iki K çarpanlarına ayrılır (brüt ve Tablo 4.2 çatlamış; TBDY 4.5.8.3): "
                 "aşağıdaki G, Q, S, W brüt K'nin sonuçlarıdır; deprem birleşimleri çatlamış K'deki G~c, Q~c, S~c ve E ile kurulur."
                 if ag.get("model_c") is not None else ""))
    sat = []
    for ad, k in durumlar_kisa.items():
        if _birim_mi(ad) or ad.endswith(_CATLAMIS_EK):
            continue
        uz = max((abs(dg["uZ"]) for dg in k["dugumler"]), default=0.0)
        ux = max((math.hypot(dg["uX"], dg["uY"]) for dg in k["dugumler"]), default=0.0)
        yay = sum(y["kuvvet"] for y in k["yaylar"] if y.get("bilesen") == "Fy")
        sat.append([ad, _f(sum(t["FZ"] for t in k["tepkiler"])), _f(yay), _f(Y.toplam.get(ad, 0.0)) if ad in Y.toplam else "–",
                    f"{k['denge']['FZ']:.1e}", f"{uz * 1000:.2f}", f"{ux * 1000:.2f}"])
    anl.metin(_tablo(["Durum", "Σ tepki FZ (kN)", "Σ yay kuvveti (kN)", "Toplam yük (kN)", "Denge kalıntısı ΣFZ", "max u_Z (mm)", "max yatay (mm)"], sat))
    anl.metin("Σ tepki + Σ yay = toplam yük: dış yükler mesnetlerde (elastik temelde yaylarda) karşılanmıştır (denge). "
              "Kiriş uç kesmelerini 8. adımda kolonlara taşıyacağız.")
    el_no = {e["no"]: e for e in ag["elemanlar"]}
    sat = []
    for r in Y.kirisler[:40]:
        k = B.kiris_no[r["no"]]
        p0, p1 = k["parcalar"][0], k["parcalar"][-1]
        eG0 = next(e for e in durumlar_kisa["G"]["elemanlar"] if e["no"] == p0["eleman"])
        eG1 = next(e for e in durumlar_kisa["G"]["elemanlar"] if e["no"] == p1["eleman"])
        Mmax = max(max(next(e for e in durumlar_kisa["G"]["elemanlar"] if e["no"] == p["eleman"])["M"]) for p in k["parcalar"])
        sat.append([f"K{r['no']}", _f(r["el_hesabi"]["R_G"]), _f(eG0["uc_kuvvetleri"][1]), _f(eG1["uc_kuvvetleri"][7]),
                    _f(r["el_hesabi"]["M_G"]), _f(Mmax), _f(min(eG0["M"][0], eG1["M"][-1]))])
    anl.metin("**El hesabı ↔ sonlu eleman (G):**\n\n"
              + _tablo(["Kiriş", "R el (kN)", "FE sol uç V (kN)", "FE sağ uç V (kN)", "M el = q_eM L²/8", "FE max açıklık M", "FE uç M (min)"], sat))
    anl.metin("Açıklık momenti el hesabından küçük, uçlarda negatif moment var: kiriş kolona ankastre bağlı sürekli bir çubuktur; "
              "basit kiriş kabulü güvenli tarafta açıklık momentini büyütür, uç momentini ise sıfır sayar.")
    _ = el_no


def _adim_9(B, akis, anl):
    se._basla(anl, 9, "Kirişten kolona, kolondan temele: birikim ve yük alanı karşılaştırması",
              "Kiriş uç kesmeleri kolon düğümüne iner; kolonun eksenel kuvveti üst kattan gelenle birikir. Aynı sayıyı "
              "'yük alanı' (tributary) yöntemiyle de buluyoruz: her kolon, komşu açıklıkların yarısını taşır. İki sonuç "
              "arasındaki fark, sürekliliğin ve rijitlik dağılımının etkisidir.")
    anl.mat(r"N_{kat} = N_{k} - N_{k+1}\ (\text{FE}),\qquad N_{trib} = \sum_{üst\ katlar}\Bigl[(g+q)A_{trib} + \sum \tfrac{L}{2}(g_{öz}+g_{duvar}) + G_{kolon}\Bigr]")
    anl.metin("**Kolonlar** (N basınç pozitif, kN; fark = (FE − yük alanı)/yük alanı):\n\n"
              + _tablo(["Kolon", "Kat", "N_G kat", "N_Q kat", "N_G küm.", "N_Q küm.", "A_trib (m²)", "N_trib,G", "N_trib,Q", "Fark %"],
                       [[f"S{k['no']}", k["kat"], _f(k["N_G"]), _f(k["N_Q"]), _f(k["N_kum_G"]), _f(k["N_kum_Q"]), _f(k["A_trib"]),
                         _f(k["N_trib_G"]), _f(k["N_trib_Q"]), _f(k["fark_yuzde"], 1)] for k in akis["kolonlar"]]))
    anl.metin("Köşe ve kenar kolonlarda FE değeri yük alanından genellikle **küçük**, iç kolonlarda **büyük** çıkar: sürekli "
              "kiriş ilk iç mesnede daha çok yük bırakır (basit kirişteki qL/2 yerine ≈ 1,25·qL/2); yük alanı yöntemi bu "
              "süreklilik etkisini göremez. Kolonsuz ara düğümlere inen paylar, taşıyan kirişin uçlarındaki kolonlara "
              "basit kiriş tepkisi oranıyla dağıtılmıştır.")
    anl.mat(r"\sigma_{max,min} = \frac{N}{B\,L} \pm \frac{6M_X}{B\,L^{2}} \pm \frac{6M_Y}{L\,B^{2}},\qquad e_X = \frac{M_Y}{N} \le \frac{B}{6},\ e_Y = \frac{M_X}{N} \le \frac{L}{6}")
    anl.metin(f"**Temeller** (servis: N = N_G + N_Q + G_temel; G_temel = γ_b·B·L·h, h = {_f(B.temeller['varsayilan']['h'])} m, temel üstü "
              "dolgu ihmal; B X yönünde, L Y yönünde; elastik temelde N ve M yay kuvvetlerinden okunur):\n\n"
              + _tablo(["Temel", "B × L (m)", "N_G", "N_Q", "G_temel", "N", "M_X", "M_Y", "σ_max", "σ_min", "e_X/B", "e_Y/L", "q_em", "D/C"],
                       [[f"T-{t['aks'][0]}{t['aks'][1]}", f"{_f(t['B'])} × {_f(t['L'])}", _f(t["N_G"]), _f(t["N_Q"]), _f(t["N_temel"]), _f(t["N_servis"]),
                         _f(t["MX"]), _f(t["MY"]), _f(t["sigma_max"]), _f(t["sigma_min"]), _f(t["e_X"] / t["B"], 3), _f(t["e_Y"] / t["L"], 3),
                         _f(t["q_em"]), _f(t["DC"], 2)] for t in akis["temeller"]]))
    kotu = [t for t in akis["temeller"] if t["DC"] > 1.0]
    if kotu:
        anl.uyari("Taban basıncı q_em'i aşan temeller: " + ", ".join(f"T-{t['aks'][0]}{t['aks'][1]} (D/C = {t['DC']:.2f})" for t in kotu)
                  + ". Temel boyutunu büyütün (B·L) ya da zemin değerini gözden geçirin.")
    anl.sema("Kolon şeridi", [_sema_kolon_seridi(B, akis)])


# ============================================================================
# Adım 13: bağımsız numpy betiği (ağ kurma + G çözümü + kolon taban toplamları; sonlu_eleman içe aktarmaz)
# ============================================================================
_PY_GOVDE = '''
GAUSS = ((-0.7745966692414834, 5/9), (0.0, 8/9), (0.7745966692414834, 5/9))   # 3 noktalı Gauss-Legendre (4. derece kesin)

def feq_parcali(L, parcalar):
    """Parçalı doğrusal q(x) için eşdeğer düğüm yükleri: f = ∫ Nᵀ q dx (Hermite kübik şekil fonksiyonları, yerel y')."""
    f = np.zeros(12)
    for q1, q2, x1, x2 in parcalar:
        for xi, w in GAUSS:
            x = (x1 + x2)/2 + (x2 - x1)/2*xi
            q = q1 + (q2 - q1)*(x - x1)/(x2 - x1)
            s = x/L
            N1, N2 = 1 - 3*s**2 + 2*s**3, L*(s - 2*s**2 + s**3)
            N3, N4 = 3*s**2 - 2*s**3, L*(-s**2 + s**3)
            dx = w*(x2 - x1)/2
            f[1] += dx*q*N1; f[5] += dx*q*N2; f[7] += dx*q*N3; f[11] += dx*q*N4
    return f

def eleman_matrisleri(e, parcalar):
    i, j, Ek, Gk, Ak, Iy, Iz, Jk = e
    dx = dugum_xyz[j][0] - dugum_xyz[i][0]
    dy = dugum_xyz[j][1] - dugum_xyz[i][1]
    dz = dugum_xyz[j][2] - dugum_xyz[i][2]
    Lb = np.sqrt(dx**2 + dy**2 + dz**2)
    cx, cy, cz = dx/Lb, dy/Lb, dz/Lb
    ea, gj = Ek*Ak/Lb, Gk*Jk/Lb
    by, bz = Ek*Iy/Lb**3, Ek*Iz/Lb**3
    kl = np.zeros((12, 12))
    def koy(a, b, v):
        kl[a, b] = v; kl[b, a] = v
    koy(0, 0, ea); koy(0, 6, -ea); koy(6, 6, ea)
    koy(3, 3, gj); koy(3, 9, -gj); koy(9, 9, gj)
    koy(1, 1, 12*bz); koy(1, 5, 6*Lb*bz); koy(1, 7, -12*bz); koy(1, 11, 6*Lb*bz)
    koy(5, 5, 4*Lb**2*bz); koy(5, 7, -6*Lb*bz); koy(5, 11, 2*Lb**2*bz)
    koy(7, 7, 12*bz); koy(7, 11, -6*Lb*bz); koy(11, 11, 4*Lb**2*bz)
    koy(2, 2, 12*by); koy(2, 4, -6*Lb*by); koy(2, 8, -12*by); koy(2, 10, -6*Lb*by)
    koy(4, 4, 4*Lb**2*by); koy(4, 8, 6*Lb*by); koy(4, 10, 2*Lb**2*by)
    koy(8, 8, 12*by); koy(8, 10, 6*Lb*by); koy(10, 10, 4*Lb**2*by)
    D = np.sqrt(cx**2 + cz**2)
    if D < 1e-12:                         # düşey eleman (kolon): z' = Z_m
        lam = [[0, cy, 0], [-cy, 0, 0], [0, 0, 1]]
    else:
        lam = [[cx, cy, cz], [-cx*cy/D, D, -cy*cz/D], [-cz/D, 0, cx/D]]
    Te = np.zeros((12, 12))
    for b in range(4):
        for a in range(3):
            for c in range(3):
                Te[3*b + a, 3*b + c] = lam[a][c]
    feq = feq_parcali(Lb, parcalar) if parcalar else None
    return kl, Te, [6*i + a for a in range(6)] + [6*j + a for a in range(6)], feq

K = np.zeros((n, n)); F = np.zeros(n)
for k, e in enumerate(elemanlar):
    kl, Te, dofs, feq = eleman_matrisleri(e, yayili.get(k, []))
    ke = Te.T @ kl @ Te
    for a, p in enumerate(dofs):
        for b, r in enumerate(dofs):
            K[p, r] += ke[a, b]
    if feq is not None:
        fg = Te.T @ feq
        for a, p in enumerate(dofs):
            F[p] += fg[a]
for p, v in F_dugum:
    F[p] += v
for p, kk in yaylar:
    K[p, p] += kk
serbest = [p for p in range(n) if p not in set(sabit)]
u = np.zeros(n)
u[serbest] = np.linalg.solve(K[np.ix_(serbest, serbest)], F[serbest])
R = K @ u - F
print(f"Toplam düşey yük (G) = {toplam_G:.2f} kN   (eşdeğer düğüm yükleri ΣF_y = {F[1::6].sum():.2f})")
print(f"Σ mesnet tepkisi F_y = {sum(R[p] for p in sabit if p % 6 == 1):.2f} kN")
print(f"max |u_y| = {abs(u[1::6]).max()*1000:.3f} mm")
print("Kolon taban eksenel kuvvetleri (basınç +):")
toplam = 0.0
for k in taban_kolonlar:
    kl, Te, dofs, feq = eleman_matrisleri(elemanlar[k], [])
    f = kl @ (Te @ u[dofs])
    N = f[0]
    toplam += N
    print(f"  {kolon_ad[k]}: N = {N:.2f} kN")
print(f"Σ kolon taban N = {toplam:.2f} kN")
'''


def _py_betik(B, ag, model, durum, Y):
    S = lambda x: repr(float(x))  # noqa: E731
    idx = {dg["no"]: i for i, dg in enumerate(model["dugumler"])}
    s = [f"# {B.baslik}: bina ağı (cerceve3b), {ag['sd_sayisi']} SD, G durumu, doğrudan rijitlik yöntemi (tek başına çalışır)",
         "import numpy as np", "np.set_printoptions(precision=4, suppress=True, linewidth=110)", "",
         "# --- düğümler: motor koordinatı (x_m, y_m, z_m) = (X, Z, -Y) bina ---",
         "dugum_xyz = [" + ", ".join(f"({S(x)}, {S(y)}, {S(z)})" for d in model["dugumler"] for x, y, z in [(d["x"], d["y"], d["z"])]) + "]",
         "n = 6*len(dugum_xyz)",
         "# elemanlar: (i, j, E, G, A, Iy, Iz, J)  i, j = düğüm sırası (0'dan); kolonlar alt→üst, kirişler küçük→büyük aks",
         "elemanlar = ["]
    for e in model["elemanlar"]:
        s.append(f"    ({idx[e['dugumler'][0]]}, {idx[e['dugumler'][1]]}, {S(e['E'])}, {S(e['G'])}, {S(e['A'])}, {S(e['Iy'])}, {S(e['Iz'])}, {S(e['J'])}),")
    s.append("]")
    s.append("# yayılı yükler (yerel y', aşağı negatif): eleman sırası -> [(q1, q2, x1, x2), ...]; düzgün yük q1 = q2")
    yay = {}
    eno_idx = {e["no"]: k for k, e in enumerate(model["elemanlar"])}
    el_L = {e["no"]: e["L"] for e in ag["elemanlar"]}
    for y in durum["yayili"]:
        k = eno_idx[y["eleman"]]
        if "q1" in y:
            yay.setdefault(k, []).append((y["q1"], y["q2"], y["x1"], y["x2"]))
        else:
            yay.setdefault(k, []).append((y["q"], y["q"], 0.0, el_L[y["eleman"]]))
    s.append("yayili = {")
    for k in sorted(yay):
        s.append(f"    {k}: [" + ", ".join(f"({S(a)}, {S(b)}, {S(c)}, {S(d)})" for a, b, c, d in yay[k]) + "],")
    s.append("}")
    fd = []
    for y in durum["yukler"]:
        i = idx[y["dugum"]]
        for j, a in enumerate(("Fx", "Fy", "Fz", "Mx", "My", "Mz")):
            if y.get(a):
                fd.append(f"({6 * i + j}, {S(y[a])})")
    s.append("F_dugum = [" + ", ".join(fd) + "]   # (SD, değer): kolon öz ağırlıkları ve ek düğüm yükleri")
    sabit = []
    for m in model["mesnetler"]:
        i = idx[m["dugum"]]
        for j, a in enumerate(("ux", "uy", "uz", "rx", "ry", "rz")):
            if m.get(a):
                sabit.append(6 * i + j)
    s.append(f"sabit = {sabit}   # tutulu SD'ler (temel düğümleri)")
    yaylar = []
    for y in model.get("yaylar") or []:
        i = idx[y["dugum"]]
        for j, a in enumerate(("kx", "ky", "kz", "krx", "kry", "krz")):
            if y.get(a):
                yaylar.append(f"({6 * i + j}, {S(y[a])})")
    s.append("yaylar = [" + ", ".join(yaylar) + "]   # elastik mesnet: (SD, k)")
    taban = [eno_idx[c["eleman"]] for c in B.kolonlar if c["kat"] == 1]
    s.append(f"taban_kolonlar = {taban}")
    s.append("kolon_ad = {" + ", ".join(f"{eno_idx[c['eleman']]}: {c['adres']!r}" for c in B.kolonlar if c["kat"] == 1) + "}")
    s.append(f"toplam_G = {S(Y.toplam['G'])}")
    s += _PY_GOVDE.rstrip("\n").split("\n")
    return s


def _py_deprem(deprem):
    """Betiğe eklenen bağımsız TBDY 2018 eşdeğer deprem yükü hesabı (spektrum → T_pA → V_tE → F_iE, X yönü)."""
    S = lambda x: repr(float(x))  # noqa: E731
    z = deprem["zemin_sinifi"]
    k = deprem["katlar"]
    s = ["", "# --- TBDY 2018 eşdeğer deprem yükü (X yönü): Tablo 2.1/2.2 → spektrum (Denk. 2.2) → V_tE (4.19) → F_iE (4.22–4.23) ---",
         "def ara_deger(x, xs, ys):   # md. 2.3.3.1: doğrusal ara değer, uçlarda sabit",
         "    if x <= xs[0]: return ys[0]",
         "    if x >= xs[-1]: return ys[-1]",
         "    for i in range(len(xs) - 1):",
         "        if xs[i] <= x <= xs[i + 1]: return ys[i] + (x - xs[i])/(xs[i + 1] - xs[i])*(ys[i + 1] - ys[i])",
         f"SS, S1 = {S(deprem['SS'])}, {S(deprem['S1'])}   # AFAD TDTH, DD-2; zemin {z}",
         f"FS = ara_deger(SS, {yv.TBDY_FS['SS']}, {yv.TBDY_FS[z]})   # Tablo 2.1",
         f"F1 = ara_deger(S1, {yv.TBDY_F1['S1']}, {yv.TBDY_F1[z]})   # Tablo 2.2",
         "SDS, SD1 = SS*FS, S1*F1",
         "TA, TB, TL = 0.2*SD1/SDS, SD1/SDS, 6.0",
         "def Sae(T):",
         "    if T <= TA: return (0.4 + 0.6*T/TA)*SDS",
         "    if T <= TB: return SDS",
         "    if T <= TL: return SD1/T",
         "    return SD1*TL/T**2",
         f"R, D, I = {S(deprem['R'])}, {S(deprem['D'])}, {S(deprem['I'])}   # Tablo 4.1, 3.1",
         "def Ra(T): return R/I if T > TB else D + (R/I - D)*T/TB   # Denk. (4.1)",
         f"HN, Ct = {S(deprem['HN'])}, {S(deprem['Ct'])}",
         "TpA = Ct*HN**0.75   # Denk. (4.27)"]
    if deprem["Tp_yontem"] == "ampirik":
        s.append("Tp = TpA   # md. 4.7.3.3")
    else:
        s.append(f"Tp = {S(deprem['Tp'])}   # Rayleigh (Denk. 4.26), motorun ağ çözümünden; ≤ 1,4·T_pA")
    s += [f"w = {[_r(x['w_i']) for x in k]}   # kat ağırlıkları w_i = w_G + n·w_Q (kN), Denk. (4.16)",
          f"H = {[_r(x['H']) for x in k]}   # temel üstünden kat yükseklikleri (m)",
          "g = 9.81",
          "m = [wi/g for wi in w]; mt = sum(m)",
          "V = mt*Sae(Tp)/Ra(Tp)*g",
          "Vmin = 0.04*mt*I*SDS*g",
          "VtE = max(V, Vmin)",
          "dFN = 0.0075*len(m)*VtE",
          "F = [(VtE - dFN)*mi*Hi/sum(mj*Hj for mj, Hj in zip(m, H)) for mi, Hi in zip(m, H)]",
          "F[-1] += dFN",
          'print(f"F_S = {FS:.4f}, F_1 = {F1:.4f}, S_DS = {SDS:.4f}, S_D1 = {SD1:.4f}, T_A = {TA:.4f} s, T_B = {TB:.4f} s")',
          'print(f"T_pA = {TpA:.4f} s, T_p = {Tp:.4f} s, S_ae = {Sae(Tp):.4f}, R_a = {Ra(Tp):.3f}, S_aR = {Sae(Tp)/Ra(Tp):.4f}")',
          'print(f"m_t = {mt:.3f} t, V_tE = max({V:.2f}, {Vmin:.2f}) = {VtE:.2f} kN, ΔF_NE = {dFN:.2f} kN")',
          'print("Kat kuvvetleri F_iE (kN):", ", ".join(f"{Fi:.2f}" for Fi in F), f"  (Σ = {sum(F):.2f})")']
    return s


def _adim_13(B, ag, model, durumlar, Y, anl, deprem=None):
    se._basla(anl, 13, "Aynı hesap Python'da",
              "Ağ kurma, parçalı yayılı yükün Gauss integrasyonuyla eşdeğer düğüm yüklerine çevrilmesi, birleştirme, çözüm ve "
              "kolon taban kuvvetleri tek bir numpy betiğinde"
              + ("; ardından TBDY 2018 eşdeğer deprem kat kuvvetleri (spektrum → V_tE → F_iE)" if deprem else "")
              + ". Betik sonlu_eleman modülünü içe aktarmaz; çıktısı 8., 11. (ve 7.) adımdaki sonuçlarla aynı olmalıdır "
              "(rijit diyafram ve yatay yüklerin çözümü betiğe alınmaz).")
    satirlar = _py_betik(B, ag, model, durumlar["G"], Y)
    if deprem:
        satirlar += _py_deprem(deprem)
    return mo._python_bolumu(anl, satirlar)


# ============================================================================
# Çıktı verisi (şema §4) ve ana işlev
# ============================================================================
def _kisa_veri(k, u_dahil=True, diyagram=True):
    """KISA → JSON. Kombinasyonlarda ``u`` yazılmaz (None; boyut), ``dugumler`` deforme şekil için kalır. ``diyagram=False``:
    eleman dizileri (x, N, V, M, …) yazılmaz, yalnız uç kuvvetleri ve enb (S, W, E durumları; tam dizi bina_kombinasyon ile)."""
    if not diyagram:     # ince kayıt: u yok, 5 anlamlı basamak; tam diziler bina_kombinasyon ile tembel alınır
        return {"u": None, "diyagram": False,
                "dugumler": [{"no": d["no"], **{a: float(f"{d[a]:.4g}") for a in ("uX", "uY", "uZ", "rX", "rY", "rZ")}} for d in k["dugumler"]],
                "tepkiler": [{"dugum": t["dugum"], **{a: _r5(t[a]) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}} for t in k["tepkiler"]],
                "elemanlar": [{"no": e["no"], "uc_kuvvetleri": [_r5(x) for x in e["uc_kuvvetleri"]],
                               "enb": {a: _r5(v) for a, v in e["enb"].items()}} for e in k["elemanlar"]],
                "denge": {a: _r(v) for a, v in k["denge"].items()},
                "yaylar": [{"dugum": y["dugum"], "sd": y.get("sd"), "bilesen": y.get("bilesen"), "k": _r(y["k"]), "kuvvet": _r5(y["kuvvet"])} for y in k["yaylar"]]}
    return {"u": [_r(x) for x in k["u"]] if u_dahil else None, "diyagram": True,
            "dugumler": [{"no": d["no"], **{a: _r(d[a]) for a in ("uX", "uY", "uZ", "rX", "rY", "rZ")}} for d in k["dugumler"]],
            "tepkiler": [{"dugum": t["dugum"], **{a: _r(t[a]) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}} for t in k["tepkiler"]],
            "elemanlar": [{"no": e["no"], "uc_kuvvetleri": [_r(x) for x in e["uc_kuvvetleri"]], "x": [_r(x) for x in e["x"]],
                           **{a: [_r6(x) for x in e[a]] for a in _DIYAGRAM},
                           "enb": {a: _r(v) for a, v in e["enb"].items()}} for e in k["elemanlar"]],
            "denge": {a: _r(v) for a, v in k["denge"].items()},
            "yaylar": [{"dugum": y["dugum"], "sd": y.get("sd"), "bilesen": y.get("bilesen"), "k": _r(y["k"]), "kuvvet": _r(y["kuvvet"])} for y in k["yaylar"]]}


def _kombinasyon_veri(kombinasyonlar):
    """veri.kombinasyonlar: [{ad, aile, katsayilar, tur, kaynak, uygulandi, neden, not[, catlamis]}]; ``catlamis: true``: deprem
    birleşimi G, Q, S'yi çatlamış kesitli kopyalardan (G~c, Q~c, S~c) alır; ``not`` ailenin yalnız ilk satırında
    (yanıt boyutu; aynı ailenin 32 deprem varyantı aynı notu taşır), ``yon`` yazılmaz (ad katsayılardan okunur)."""
    out, gorulen = [], set()
    for k in kombinasyonlar:
        r = {a: k[a] for a in ("ad", "aile", "katsayilar", "tur", "kaynak", "uygulandi", "neden")}
        r["not"] = k.get("not", "") if k["aile"] not in gorulen else ""
        if k.get("cozum") and k["cozum"] != k["katsayilar"]:
            r["catlamis"] = True          # G, Q, S çatlamış kesitli çözümden (G~c, Q~c, S~c; TBDY 4.5.8.3)
        gorulen.add(k["aile"])
        out.append(r)
    return out


def _veri_olustur(B, Y, ag, model, durumlar, durumlar_kisa, kombinasyonlar, sonuclar, zarf, akis, yol, *, deprem=None, ruzgar=None,
                  kutle=None, ozetler=None, gosterilecek=None, kimlik=None):
    bina = {
        "baslik": B.baslik, "sistem": B.sistem,
        "akslar": {"x": [dict(a) for a in B.akslar["x"]], "y": [dict(a) for a in B.akslar["y"]]},
        "katlar": [{"no": k["no"], "ad": k["ad"], "kot": k["kot"], "h": k["h"]} for k in B.katlar],
        "kolonlar": [{"no": c["no"], "aks": c["aks"], "kat": c["kat"], "kesit": c["kesit"], "yon": c["yon"], "bX": c["bX"], "bY": c["bY"],
                      "L": c["L"], "A": _r(c["A"]), "Iy_m": _r(c["Iy_m"]), "Iz_m": _r(c["Iz_m"]), "J": _r(c["J"]), "malzeme": c["malzeme"],
                      "eleman": c["eleman"], "adres": c["adres"], "oz_kN": _r(c["gamma"] * c["A"] * c["L"])} for c in B.kolonlar],
        "kirisler": [{"no": k["no"], "kat": k["kat"], "bas": k["bas"], "son": k["son"], "yon": k["yon"], "kesit": k["kesit"], "duvar": k["duvar"],
                      "b": k["b"], "h": k["h"], "L": k["L"], "A": _r(k["A"]), "Iy_m": _r(k["Iy_m"]), "Iz_m": _r(k["Iz_m"]), "J": _r(k["J"]),
                      "malzeme": k["malzeme"], "h_duvar": k["h_duvar"], "adres": k["adres"],
                      "parcalar": [{"parca": p["parca"], "eleman": p["eleman"], "L": p["L"]} for p in k["parcalar"]]} for k in B.kirisler],
        "dosemeler": [{"no": d["no"], "kat": d["kat"], "kose": d["kose"], "h": d["h"], "kullanim": d["kullanim"], "g_ek": d["g_ek"],
                       "q": d["q"], "dagitim": d["dagitim"], "adres": d["adres"]} for d in B.dosemeler],
        "duvarlar": {ad: {"kutuphane": d["kutuphane"], "deger": d["deger"], "aciklama": d["aciklama"], "dogrulandi": d["dogrulandi"]}
                     for ad, d in B.duvarlar.items()},
        "temeller": {"tip": B.temeller["tip"], "mesnet": B.temeller["mesnet"], "zemin": dict(B.temeller["zemin"]),
                     "varsayilan": dict(B.temeller["varsayilan"]),
                     "liste": [{"kolon_no": t["kolon_no"], "aks": t["aks"], "B": t["B"], "L": t["L"]} for t in akis["temeller"]]},
        "deprem": copy.deepcopy(B.deprem), "kar": copy.deepcopy(B.kar), "ruzgar": copy.deepcopy(B.ruzgar),
        "kombinasyon_kumesi": B.kombinasyon_kumesi, "analiz": dict(B.analiz),
    }
    kutuphane_ozeti = {
        "malzemeler": {ad: {"E_kNm2": m["E"], "G_kNm2": m["G"], "gamma": m["gamma"], "tur": m["tur"], "kutuphane": m["kutuphane"],
                            **({"fck": m["fck"]} if m["tur"] == "beton" else {}), **({"Fy": m["Fy"]} if m["tur"] == "celik" else {}),
                            **({"fyk": m["fyk"]} if m["tur"] == "donati" else {})} for ad, m in B.malzemeler.items()},
        "kesitler": {ad: {"tip": k["tip"], "b": k["b"], "h": k["h"], "profil": k["profil"], "A": _r(k["A"]), "Iy": _r(k["I_guclu"]),
                          "Iz": _r(k["I_zayif"]), "J": _r(k["J"]), "Wpl": _r(k["Wpl"]), "malzeme": k["malzeme"]} for ad, k in B.kesitler.items()},
    }
    ag_veri = {"dugumler": [{"no": d["no"], "X": d["X"], "Y": d["Y"], "Z": d["Z"], "adres": d["adres"], "kat": d["kat"], "aks": d["aks"],
                             "efendi": d["efendi"]} for d in ag["dugumler"]],
               "elemanlar": [{"no": e["no"], "dugumler": e["dugumler"], "tur": e["tur"], "kaynak_no": e["kaynak_no"], "parca": e["parca"],
                              "kat": e["kat"], "L": _r(e["L"]), "kesit": e["kesit"], "lam": [[_r6(x) for x in s] for s in e["lam"]],
                              "adres": e["adres"], "rijitlik_carpani": e["rijitlik_carpani"]} for e in ag["elemanlar"]],
               "mesnetler": [{"dugum": m["dugum"], "tip": m["tip"]} for m in ag["mesnetler"]],
               "diyaframlar": [{"ad": d["ad"], "ana": d["ana"]["no"], "dugumler": list(d["dugumler"]), "X": _r(d["ana"]["x"]),
                                "Y": _r(-d["ana"]["z"]), "Z": _r(d["ana"]["y"])} for d in ag["diyaframlar"]],
               "diyafram": "rijit" if ag["efendi"] else "esnek", "rijitlik_carpani": dict(ag["rijitlik_carpani"]),
               "sd_sayisi": ag["sd_sayisi"], "mod": "sayisal", "cozum_yolu": yol}
    yukler = {
        "dosemeler": [{"no": d["no"], "kat": d["kat"], "lx": d["lx"], "ly": d["ly"], "m": _r(d["m"]), "tip": d["tip"], "g": _r(d["g"]),
                       "q": _r(d["q_top"]), "g_plak": _r(d["g_plak"]), "g_ek": _r(d["g_ek"] + d["ek_g"]), "alan": _r(d["alan"]),
                       "G_toplam": _r(d["G_toplam"]), "Q_toplam": _r(d["Q_toplam"]), "q_kaynak": d["q_kaynak"], "q_dogrulandi": d["q_dogrulandi"],
                       "paylar": [{"kiris_no": p["kiris_no"], "parca": p["parca"], "eleman": B.kiris_no[p["kiris_no"]]["parcalar"][p["parca"] - 1]["eleman"],
                                   "kenar_ad": p["kenar_ad"], "kenar": p["kenar"], "sekil": p["sekil"], "L": _r(p["L"]),
                                   "tepe_g": _r(p["tepe_g"]), "tepe_q": _r(p["tepe_q"]), "q_eM_g": _r(p["q_eM_g"]), "q_eV_g": _r(p["q_eV_g"]),
                                   "q_eM_q": _r(p["q_eM_q"]), "q_eV_q": _r(p["q_eV_q"]), "toplam_G": _r(p["toplam_G"]), "toplam_Q": _r(p["toplam_Q"]),
                                   "parcalar_birim": [[_r(v) for v in t] for t in p["parcalar_birim"]]} for p in d["paylar"]]}
                      for d in Y.dosemeler],
        "kirisler": [{"no": r["no"], "kat": r["kat"], "L": r["L"], "G": {a: _r(v) for a, v in r["G"].items()}, "Q": {a: _r(v) for a, v in r["Q"].items()},
                      "S": {a: _r(v) for a, v in r["S"].items()},
                      "kN_m": {a: _r(v) for a, v in r["kN_m"].items()}, "el_hesabi": {a: _r(v) for a, v in r["el_hesabi"].items()}} for r in Y.kirisler],
        "kolonlar": [{"no": c["no"], "kat": c["kat"], "oz_kN": _r(c["oz_kN"])} for c in Y.kolonlar],
        "katlar": [{"kat": k["kat"], "kot": k["kot"], "h": k["h"], "G": _r(k["G"]), "Q": _r(k["Q"]), "S": _r(k["S"]), "w": _r(k["w"])} for k in Y.katlar],
        "toplam": {"G": _r(Y.toplam["G"]), "Q": _r(Y.toplam["Q"]), "S": _r(Y.toplam["S"])},
    }
    akis_veri = {
        "kolonlar": [{a: (_r(v) if isinstance(v, float) else v) for a, v in k.items()} for k in akis["kolonlar"]],
        "temeller": [{a: (_r(v) if isinstance(v, float) else v) for a, v in t.items()} for t in akis["temeller"]],
        "korunum": {d: {a: _r(v) for a, v in p.items()} for d, p in akis["korunum"].items()},
        "sankey": [dict(s, kN=_r6(s["kN"])) for s in akis["sankey"]],
    }
    uyarilar = list(B.uyarilar)
    kullanilan = set()
    for d in B.dosemeler:
        if not d["q_dogrulandi"]:
            kullanilan.add(f"TS498_HAREKETLI.{d['kullanim']} (döşeme D{d['no']})")
        if not d["g_ek_dogrulandi"]:
            kullanilan.add(f"KAPLAMALAR (döşeme D{d['no']}): {d['g_ek_kaynak']}")
    for ad, dv in B.duvarlar.items():
        if not dv["dogrulandi"]:
            kullanilan.add(f"DUVARLAR.{dv['kutuphane']} ({ad})")
    for k in sorted(kullanilan):
        uyarilar.append(f"Doğrulanmamış kütüphane değeri kullanıldı: {k}")
    en_dc = max((t["DC"] for t in akis["temeller"]), default=0.0)
    if en_dc > 1.0:
        uyarilar.append(f"En büyük temel taban basıncı oranı D/C = {en_dc:.2f} > 1.")
    if deprem:
        for u in deprem["uyarilar"]:
            if u not in uyarilar:
                uyarilar.append(u)
    if B.kar and not B.kar["dogrulandi"]:
        uyarilar.append("Kar bölgesi Ek 1 il/ilçe listesinden (OCR aktarımı, doğrulanmamış) alındı; bölgeyi haritadan doğrulayın.")
    fe_model = _sonlu(dict(model, yukler=durumlar["G"]["yukler"], yayili=durumlar["G"]["yayili"]))
    gosterilecek = gosterilecek or list(sonuclar)
    uygulanan = [k for k in kombinasyonlar if k["uygulandi"] and k["tur"] != "drift"]
    kar_veri = None
    if B.kar:
        cati = [d for d in Y.dosemeler if d["kat"] == B.nk]
        kar_veri = _sonlu({"bolge": B.kar["bolge"], "rakim": B.kar["rakim"], "Sk": B.kar["Sk"], "mu": B.kar["mu"], "s": B.kar["s"],
                           "Ce": B.kar["Ce"], "Ct": B.kar["Ct"], "alpha": B.kar["alpha"], "cati_alani": sum(d["alan"] for d in cati),
                           "S_toplam": Y.toplam["S"], "kat": B.nk, "Sk_kaynak": B.kar["Sk_kaynak"], "mu_kaynak": B.kar["mu_kaynak"],
                           "kaynak": B.kar["kaynak"] + "; " + B.kar["Sk_kaynak"] + "; μ1: " + B.kar["mu_kaynak"],
                           "dogrulandi": B.kar["dogrulandi"]})
    kmb_ozet = {ad: {"enb": {a: _r5(v) for a, v in o["enb"].items()}, "u_enb": {a: _r5(v) for a, v in o["u_enb"].items()},
                     "FZ_tepki": _r6(o["FZ_tepki"]), "denge_enb": float(f"{o['denge_enb']:.2g}")} for ad, o in (ozetler or {}).items()}
    tam = {"G", "Q"} | set(gosterilecek)
    veri = {
        "tur": "bina", "surum": 2, "baslik": B.baslik, "sistem": B.sistem, "birim": dict(B.birim), "cozum_kimligi": kimlik,
        "bina": bina, "kutuphane_ozeti": kutuphane_ozeti, "ag": ag_veri, "yukler": yukler,
        "durumlar": {ad: _kisa_veri(k, diyagram=ad in tam) for ad, k in durumlar_kisa.items()},
        "kombinasyonlar": _kombinasyon_veri(kombinasyonlar),
        "kombinasyon_ozet": kmb_ozet,
        "gosterilecek": list(gosterilecek),
        "sonuclar": {ad: _kisa_veri(k, u_dahil=False) for ad, k in sonuclar.items()},
        "zarf": {"kombinasyonlar": zarf["kombinasyonlar"], "kombinasyon_sayisi": len(zarf["kombinasyonlar"]),
                 "elemanlar": [{a: (_r6(v) if isinstance(v, float) else v) for a, v in z.items()} for z in zarf["elemanlar"]]},
        "akis": akis_veri,
        "deprem": _sonlu(deprem) if deprem else None,
        "ruzgar": _sonlu(ruzgar) if ruzgar else None,
        "kar": kar_veri,
        "kutle_merkezi": [{"kat": k["kat"], "X": _r(k["X"]), "Y": _r(k["Y"]), "w": _r(k["w"]), "m": _r(k["m"]), "BX": _r(k["BX"]), "BY": _r(k["BY"])}
                          for k in (kutle or [])],
        "rijitlik_merkezi": [{"kat": k["kat"], "X": _r(k["X"]), "Y": _r(k["Y"])} for k in _rijitlik_merkezi(B)],
        "ozet": {"sd_sayisi": ag["sd_sayisi"], "dugum": len(ag["dugumler"]), "eleman": len(ag["elemanlar"]),
                 "durum_sayisi": len(durumlar_kisa), "kombinasyon_sayisi": len(uygulanan), "gosterilen_sayisi": len(sonuclar),
                 "drift_kombinasyon_sayisi": sum(1 for k in kombinasyonlar if k["uygulandi"] and k["tur"] == "drift"),
                 "toplam_G": _r(Y.toplam["G"]), "toplam_Q": _r(Y.toplam["Q"]), "toplam_S": _r(Y.toplam["S"]),
                 "en_buyuk_temel_DC": _r(en_dc), "uyarilar": uyarilar,
                 "deprem_etkin": bool(deprem), "ruzgar_etkin": bool(ruzgar), "kar_etkin": bool(B.kar),
                 "diyafram": "rijit" if ag["efendi"] else "esnek", "catlamis_rijitlik": B.analiz["catlamis_rijitlik"]},
        "fe_model": fe_model,
    }
    return veri


# ============================================================================
# Deprem: çözümden sonra — Rayleigh periyodu, V_tE, F_iE, dışmerkezlik (E durumları süperpozisyonla), η_bi, drift, θ_II
# ============================================================================
def _yuk_kayit_birlesim(durumlar, katsayilar):
    """Birim durum yük kayıtlarının doğrusal birleşimi ({"yukler", "yayili", "yayili_esdeger"}; düğüm yükleri toplanır)."""
    yukler, yayili, esdeger = [], [], []
    for ad, g in katsayilar.items():
        d = durumlar.get(ad)
        if d is None or abs(g) < 1e-15:
            continue
        for y in d["yukler"]:
            _dugum_yuku_ekle(yukler, y["dugum"], 0.0, 0.0, 0.0, 0.0)
            hedef = next(h for h in yukler if h["dugum"] == y["dugum"])
            for a in ("Fx", "Fy", "Fz", "Mx", "My", "Mz"):
                hedef[a] += g * y.get(a, 0.0)
        for y in d["yayili"]:
            yayili.append({a: (v * g if a in ("q", "q1", "q2") else v) for a, v in y.items()})
        for y in d.get("yayili_esdeger", []):
            esdeger.append({a: (v * g if a == "q" else v) for a, v in y.items()})
    return {"yukler": yukler, "yayili": yayili, "yayili_esdeger": esdeger}


def _kat_d(ag, paket, arr, yon, kutle):
    """Kat yer değiştirmeleri d_i (yön X ya da Y): rijit diyaframda efendi düğüm, yoksa kütle ağırlıklı ortalama."""
    j = 0 if yon == "X" else 1
    idx = {no: i for i, no in enumerate(paket.dugum_no)}
    out = {}
    for kk in kutle:
        kat = kk["kat"]
        if kat in ag["efendi"] and ag["efendi"][kat] in idx:
            out[kat] = float(arr["dug"][idx[ag["efendi"][kat]], j])
            continue
        W = top = 0.0
        for dg in ag["dugumler"]:
            if dg["kat"] != kat or dg["efendi"] or dg["no"] not in idx:
                continue
            w = kk["dugum_w"].get(dg["key"][:2], 0.0)
            if w <= 0:
                w = 1e-9
            W += w
            top += w * float(arr["dug"][idx[dg["no"]], j])
        out[kat] = top / W if W > 0 else 0.0
    return out


def _delta_katlar(B, ag, paket, arr, yon):
    """Her kat için kolon hatlarındaki göreli kat ötelemeleri Δ = u_i − u_{i−1} (aynı aks kesişimi, art arda iki kat):
    {kat: {"max", "min", "ort", "dugum_max"}} (mutlak değerlerle; drift ve θ_II için) ve "eta" = η_bi (işaretli değerlerle)."""
    j = 0 if yon == "X" else 1
    idx = {no: i for i, no in enumerate(paket.dugum_no)}
    out = {}
    for kat in range(1, B.nk + 1):
        degerler = []
        for dg in ag["dugumler"]:
            if dg["kat"] != kat or dg["efendi"]:
                continue
            alt = ag["dugum_key"].get((dg["key"][0], dg["key"][1], kat - 1))
            if alt is None or alt not in idx or dg["no"] not in idx:
                continue
            degerler.append((float(arr["dug"][idx[dg["no"]], j]) - float(arr["dug"][idx[alt], j]), dg["no"]))
        if not degerler:
            out[kat] = {"max": 0.0, "min": 0.0, "ort": 0.0, "dugum_max": None, "eta": 1.0}
            continue
        mutlak = [(abs(x), no) for x, no in degerler]
        mx, mn = max(mutlak), min(mutlak)
        # η_bi işaretli ötelemelerle (deprem doğrultusunda baskın işaret +): bir kenar ters yönde ötelenirse (Δ)min < 0,
        # (Δ)ort = ½[(Δ)max + (Δ)min] küçülür ve η_bi > 2 olabilir (Tablo 3.6)
        isaret = 1.0 if max(degerler)[0] >= -min(degerler)[0] else -1.0
        s_max, s_min = max(isaret * x for x, _ in degerler), min(isaret * x for x, _ in degerler)
        s_ort = (s_max + s_min) / 2.0
        eta = s_max / s_ort if s_ort > 1e-15 else (1.0 if s_max <= 1e-15 else 99.0)
        out[kat] = {"max": mx[0], "min": mn[0], "ort": (mx[0] + mn[0]) / 2.0, "dugum_max": mx[1], "eta": eta}
    return out


def _deprem_kaynaklari(d):
    """veri.deprem.kaynaklar: alan adı → yönetmelik maddesi (UI parametre kartlarının altına yazar)."""
    K = {a: (v if not isinstance(v, str) or v.startswith("TBDY") else "TBDY 2018 — " + v) for a, v in yv.TBDY_DEPREM_KURALLAR.items()}
    afad = "AFAD Türkiye Deprem Tehlike Haritası (tdth.afad.gov.tr); TBDY 2018 md. 2.3.2.1, DD-2"
    ts = yv.TBDY_TASIYICI[d["tasiyici"]]
    rd = f"{ts['kaynak']}: {ts['kod']} — {ts['tanim']}"
    drift = K["drift"]
    return {
        "SS": afad, "S1": afad, "zemin_sinifi": yv.ZEMIN_SINIFLARI["kaynak"],
        "FS": yv.TBDY_FS["kaynak"], "F1": yv.TBDY_F1["kaynak"],
        "SDS": "TBDY 2018 Denk. (2.1): S_DS = S_S·F_S (F_S Tablo 2.1)", "SD1": "TBDY 2018 Denk. (2.1): S_D1 = S_1·F_1 (F_1 Tablo 2.2)",
        "TA": "TBDY 2018 Denk. (2.3): T_A = 0,2·S_D1/S_DS, T_B = S_D1/S_DS; md. 2.3.4.1: T_L = 6 s",
        "TB": "TBDY 2018 Denk. (2.3): T_B = S_D1/S_DS", "TL": "TBDY 2018 md. 2.3.4.1: T_L = 6 s",
        "Sae_Tp": "TBDY 2018 Denk. (2.2) yatay elastik tasarım spektrumu", "spektrum": yv.TBDY_SPEKTRUM["kaynak"],
        "DTS": yv.TBDY_DTS["kaynak"], "BYS": yv.TBDY_BYS["kaynak"], "HN": "TBDY 2018 md. 3.3.1.3: H_N bina tabanından ölçülür",
        "I": yv.TBDY_BKS_I["kaynak"], "BKS": yv.TBDY_BKS_I["kaynak"], "R": rd, "D": rd,
        "n": "TBDY 2018 Tablo 4.3 (md. 4.5.9.2), Denk. (4.16): m_i = (w_G + n·w_Q)/g; çatıda kar yükünün %30'u",
        "m_t": "TBDY 2018 Denk. (4.16): m_i = (w_G + n·w_Q)/g, m_t = Σ m_i", "W_t": "TBDY 2018 Denk. (4.16): w_i = w_G + n·w_Q",
        "Ct": yv.TBDY_CT["kaynak"], "TpA": "TBDY 2018 Denk. (4.27): T_pA = C_t·H_N^(3/4); " + yv.TBDY_CT["kaynak"],
        "Tp": K["Tp"] + "; md. 4.7.3.3: DTS = 3, 4 ve (DTS = 1, 2 ve BYS ≥ 6) binalarda T_p ≅ T_pA alınabilir",
        "Ra": K["Ra"], "SaR": K["SaR"], "VtE": K["VtE"], "VtE_min": K["VtE"], "dFN": K["dFN"], "F": K["FiE"],
        "e": K["dismerkezlik"], "Mb": K["dismerkezlik"], "eta_b": K["eta_b"], "D_b": K["eta_b"],
        "delta": drift, "oran": drift, "sinir": drift, "lambda": K["lambda"],
        "kappa": "TBDY 2018 md. 4.9.1.3: κ = 1 (betonarme), 0,5 (çelik)",
        "theta": K["theta"], "theta_sinir": K["theta"], "EZ": K["EdZ"], "EdH": K["EdH"],
        "uygulanabilir": yv.TBDY_UYGULANABILIRLIK["kaynak"], "catlamis_rijitlik": yv.TBDY_ETKIN_RIJITLIK["kaynak"],
        "Mo": "TBDY 2018 Denk. (4.25): M_o = Σ F_iE·H_i", "drift_notu": K["drift_notu"],
    }


def _kat_kuvvet_tablosu(kutle, Fx, dFNx, Fy, dFNy):
    """Kat tablosu satırları: F_i (tepe kata ΔF_NE eklenmiş) ve kat kesmesi V_i = Σ_{j≥i} F_j (iki yön)."""
    tepe = kutle[-1]["kat"]
    sat = []
    for k, fx, fy in zip(kutle, Fx, Fy):
        sat.append({"kat": k["kat"], "H": k["H"], "kot": k["kot"], "h": k["h"], "w_i": k["w"], "m_i": k["m"],
                    "G": k["G"], "Q": k["Q"], "S": k["S"], "X": k["X"], "Y": k["Y"], "BX": k["BX"], "BY": k["BY"],
                    "F_x": fx + (dFNx if k["kat"] == tepe else 0.0), "F_y": fy + (dFNy if k["kat"] == tepe else 0.0)})
    for yon in ("x", "y"):
        kum = 0.0
        for s in reversed(sat):
            kum += s["F_" + yon]
            s["V_" + yon] = kum
    return sat


def _deprem_son(B, ag, dep, paket, durumlar):
    """Birim durumlardan E durumlarını kurar (paket.durum'a EX+, EX-, EY+, EY-, EZ eklenir; durumlar'a yük kayıtları),
    T_p (Rayleigh / ampirik), V_tE, F_iE, η_bi ve D_bi, göreli kat ötelemesi ve θ_II tablolarını hesaplar."""
    d = B.deprem
    kutle = dep["kutle"]
    g = dep["g"]
    sp_ = dep["sp"]
    uyarilar = list(dep["uyarilar"])
    toplam = sum(k["m"] * k["H"] for k in kutle)
    sekil = {k["kat"]: k["m"] * k["H"] / toplam for k in kutle}
    tepe = kutle[-1]["kat"]
    yonler = {}
    e_oran = d["dismerkezlik"]
    kat_nolar = [k["kat"] for k in kutle]

    def eta_hesap(Ep, Em, yon):
        dp_, dm_ = _delta_katlar(B, ag, paket, Ep, yon), _delta_katlar(B, ag, paket, Em, yon)
        out = {}
        for kat in range(1, B.nk + 1):
            out[kat] = max(dp_[kat]["eta"], dm_[kat]["eta"])
        return out

    # 1) her doğrultu: T_p, V_tE, F_iE; D_bi = 1 ile (yalnız ±%5) η_bi
    for yon in ("X", "Y"):
        R, N, TN = paket.durum["R" + yon], paket.durum["N" + yon], paket.durum["TN" + yon]
        Tk = {kat: paket.durum[f"T{yon}{kat}"] for kat in kat_nolar if f"T{yon}{kat}" in paket.durum}
        # Rayleigh (Denk. 4.26): kurgusal yük F_fi = s_i (Σ = 1 kN) → d_fi (kütle merkezinde / efendi düğümde)
        dR = _kat_d(ag, paket, R, yon, kutle)
        pay = sum(k["m"] * dR[k["kat"]] ** 2 for k in kutle)
        payda = sum(sekil[k["kat"]] * dR[k["kat"]] for k in kutle)
        Tp_ray = 2.0 * math.pi * math.sqrt(pay / payda) if payda > 1e-15 else dep["TpA"]
        Tp_ray_sinirli = min(Tp_ray, 1.4 * dep["TpA"])
        yontem = dep["Tp_yontem"]
        Tp = dep["TpA"] if yontem == "ampirik" else Tp_ray_sinirli
        if yontem != "ampirik" and Tp_ray > 1.4 * dep["TpA"]:
            uyarilar.append(f"{yon} yönü: Rayleigh periyodu {Tp_ray:.3f} s > 1,4·T_pA = {1.4 * dep['TpA']:.3f} s; md. 4.7.3.2 üst sınırı uygulandı.")
        V, Vmin, Vk, dFN, F = _taban_kesme(dep, Tp)
        alt_sinir_etkin = Vmin > V + 1e-12
        # drift için (md. 4.9.1.1): 1,4·T_pA sınırı ve Denk. 4.19 alt sınırı olmadan
        Tp_d = dep["TpA"] if yontem == "ampirik" else Tp_ray
        Vd = dep["mt"] * dep["SaR"](Tp_d) * g
        olcek = Vd / Vk if Vk > 1e-12 else 1.0
        # dışmerkezlik: e_i = ±0,05·D_bi·B_i (deprem doğrultusuna dik kat boyutu); birim burulma durumu B_i'yi zaten içerir
        Bdik = {k["kat"]: (k["BY"] if yon == "X" else k["BX"]) for k in kutle}
        E0 = {a: (Vk - dFN) * R[a] + dFN * N[a] for a in R}

        def burulma(Db, Tk=Tk, TN=TN, Vk=Vk, dFN=dFN, E0=E0):
            """Σ_i D_bi·(V − ΔF)·T_i + D_bN·ΔF·TN (kat bazında büyütülmüş birim burulmaların toplamı)."""
            out = {a: dFN * Db.get(tepe, 1.0) * TN[a] for a in E0}
            for kat, T in Tk.items():
                for a in out:
                    out[a] = out[a] + (Vk - dFN) * Db.get(kat, 1.0) * T[a]
            return out

        Tb1 = burulma({})
        eta = eta_hesap({a: E0[a] + e_oran * Tb1[a] for a in E0}, {a: E0[a] - e_oran * Tb1[a] for a in E0}, yon)
        lam = dep["sp3"]["Sae"](Tp) / sp_["Sae"](Tp) if dep["sp3"] is not None else 1.0
        sinir = dep["sinir_oran"]
        if B.sistem == "celik" and B.nk == 1 and d["tasiyici_kod"] in ("C11", "C31"):   # md. 4.9.1.5
            sinir *= 1.5
            not_ = (f"Tek katlı çelik moment çerçeve: göreli kat ötelemesi sınırı md. 4.9.1.5'in izin verdiği en çok %50 "
                    f"artırımla {_f(sinir, 4)} alındı.")
            if not_ not in uyarilar:
                uyarilar.append(not_)
        yonler[yon] = {"Tp": Tp, "Tp_rayleigh": Tp_ray, "Tp_rayleigh_sinirli": Tp_ray_sinirli, "Tp_yontem": yontem,
                       "Sae_Tp": sp_["Sae"](Tp), "Ra": dep["Ra"](Tp), "SaR": dep["SaR"](Tp), "VtE": Vk, "VtE_hesap": V, "VtE_min": Vmin,
                       "alt_sinir_etkin": alt_sinir_etkin, "dFN": dFN, "F": list(F), "e_oran": e_oran, "B_dik": Bdik,
                       "eta": eta, "eta_max": max(eta.values()) if eta else 1.0, "lambda": lam, "sinir": sinir, "olcek_drift": olcek,
                       "Tp_drift": Tp_d, "V_drift": Vd, "E0": E0, "burulma": burulma, "dE": _kat_d(ag, paket, E0, yon, kutle),
                       "rayleigh": [{"kat": k["kat"], "m": k["m"], "F_f": sekil[k["kat"]], "d_f": dR[k["kat"]]} for k in kutle],
                       "Mo": sum(Fi * k["H"] for Fi, k in zip(F, kutle)) + dFN * kutle[-1]["H"]}
    # 2) D_bi kat bazında (md. 4.7.4, Denk. 4.29): A1 düzensizliği olan i'inci katta ±%5 dışmerkezlik HER İKİ deprem doğrultusu
    #    için D_bi = (η_bi/1,2)² ile büyütülür; η_bi o katın iki doğrultudaki değerlerinin büyüğü (η_bi ilk hesaptan, yinelenmez)
    Db = {}
    for kat in range(1, B.nk + 1):
        eta_k = max(yonler["X"]["eta"].get(kat, 1.0), yonler["Y"]["eta"].get(kat, 1.0))
        Db[kat] = min((eta_k / 1.2) ** 2, (2.0 / 1.2) ** 2) if (eta_k > 1.2 + 1e-12 and e_oran > 0) else 1.0
    buyuk = {kat: v for kat, v in Db.items() if v > 1.0}
    if buyuk:
        uyarilar.append("A1 burulma düzensizliği (η_bi > 1,2) olan kat(lar)da ±%" + _f(100 * e_oran, 1) + " ek dışmerkezlik her iki "
                        "deprem doğrultusu için D_bi = (η_bi/1,2)² ile büyütüldü (md. 4.7.4, Denk. 4.29; η_bi = iki doğrultunun büyüğü, "
                        "ilk hesaptan): " + ", ".join(f"kat {kat}: D_bi = {v:.3f}" for kat, v in buyuk.items()) + ".")
    # 3) E± = E0 ± e·Σ D_bi·burulma_i
    for yon in ("X", "Y"):
        v = yonler[yon]
        Vk, dFN, E0 = v["VtE"], v["dFN"], v.pop("E0")
        Tb = v.pop("burulma")(Db)
        Ep = {a: E0[a] + e_oran * Tb[a] for a in E0}
        Em = {a: E0[a] - e_oran * Tb[a] for a in E0}
        paket.durum[f"E{yon}+"], paket.durum[f"E{yon}-"] = Ep, Em
        for isaret, ad in ((1.0, f"E{yon}+"), (-1.0, f"E{yon}-")):
            kat_ = {"R" + yon: Vk - dFN, "N" + yon: dFN, "TN" + yon: isaret * e_oran * Db.get(tepe, 1.0) * dFN}
            kat_.update({f"T{yon}{kat}": isaret * e_oran * Db.get(kat, 1.0) * (Vk - dFN) for kat in kat_nolar})
            durumlar[ad] = _yuk_kayit_birlesim(durumlar, kat_)
        v.update({"Ep": Ep, "Em": Em, "D_b": max(Db.values()) if Db else 1.0, "D_b_kat": dict(Db)})
    X, Yy = yonler["X"], yonler["Y"]
    katlar = _kat_kuvvet_tablosu(kutle, X["F"], X["dFN"], Yy["F"], Yy["dFN"])
    theta_sinir = 0.12 * dep["D"] / (dep["Ch"] * dep["R"])
    w_ust = {k["kat"]: sum(kj["w"] for kj in kutle if kj["kat"] >= k["kat"]) for k in kutle}
    for yon, v in (("X", X), ("Y", Yy)):
        y = yon.lower()
        theta_max = 0.0
        dp_, dm_ = _delta_katlar(B, ag, paket, v["Ep"], yon), _delta_katlar(B, ag, paket, v["Em"], yon)
        for s in katlar:
            kat = s["kat"]
            dp, dm = dp_[kat], dm_[kat]
            D_max = max(dp["max"], dm["max"]) * v["olcek_drift"]       # Δ_i,max (drift spektrumu, alt sınırsız)
            D_ort = max(dp["ort"], dm["ort"])                         # θ_II için (Δ_i)ort, V_i ile aynı yükleme
            delta = dep["R"] / dep["I"] * D_max
            oran = v["lambda"] * delta / s["h"]
            Vi = s["V_" + y]
            theta = D_ort * w_ust[kat] / (Vi * s["h"]) if Vi > 1e-12 else 0.0
            theta_max = max(theta_max, theta)
            e_i = v["e_oran"] * v["D_b_kat"].get(kat, 1.0) * v["B_dik"][kat]
            s.update({f"d_{y}": v["dE"][kat], f"delta_{y}": D_max, f"delta_ort_{y}": D_ort, f"delta_etkin_{y}": delta,
                      f"oran_{y}": oran, f"eta_b{y}": v["eta"][kat], f"theta_{y}": theta, f"uygun_{y}": oran <= v["sinir"] + 1e-12,
                      f"e_{y}": e_i, f"Mb_{y}": s["F_" + y] * e_i, f"B_dik_{y}": v["B_dik"][kat], "D_b": v["D_b_kat"].get(kat, 1.0),
                      f"dugum_{y}": dp["dugum_max"] if dp["max"] >= dm["max"] else dm["dugum_max"]})
        v["theta_max"] = theta_max
        v["theta_sinir"] = theta_sinir
        if theta_max > theta_sinir:
            beta = max(1.0, 0.88 + dep["Ch"] * dep["R"] / dep["D"] * theta_max)
            uyarilar.append(f"{yon} yönü: θ_II,max = {theta_max:.4f} > 0,12·D/(C_h·R) = {theta_sinir:.4f}; ikinci mertebe etkileri "
                            f"önemli, iç kuvvetler β_II = {beta:.3f} ile büyütülmeli (Denk. 4.37; bu çözümde uygulanmadı).")
        kotu = [s["kat"] for s in katlar if not s[f"uygun_{y}"]]
        if kotu:
            uyarilar.append(f"{yon} yönü: göreli kat ötelemesi sınırı ({_f(v['sinir'], 4)}) aşıldı — kat(lar) {kotu}; rijitlik artırılıp "
                            "hesap yinelenmeli (md. 4.9.1.6).")
    for s in katlar:
        s["sinir"] = X["sinir"]
        s["uygun"] = bool(s["uygun_x"] and s["uygun_y"])
    # düşey deprem: E_d(Z) ≈ (2/3)·S_DS·G (Denk. 4.10)
    kz = 2.0 / 3.0 * sp_["SDS"]
    Gd = paket.durum.get("G" + _CATLAMIS_EK, paket.durum["G"])     # EZ yalnız deprem birleşimlerinde: çatlamış çözüm varsa G~c
    paket.durum["EZ"] = {a: kz * Gd[a] for a in Gd}
    durumlar["EZ"] = _yuk_kayit_birlesim(durumlar, {"G": kz})
    # Tablo 4.4: her katta η_bi ≤ 2,0 (ve B2 yok) → 1. satır; η_bi > 2,0 → "diğer tüm binalar" satırı (daha sıkı BYS eşiği)
    eta_tum = max(X["eta_max"], Yy["eta_max"])
    uyg = dict(dep["uygulanabilirlik"])
    if eta_tum <= 2.0 + 1e-12:
        uygulanabilir = dep["uygulanabilir"]
        uyg.update({"satir": "duzenli", "esik": uyg["esik_duzenli"]})
    else:
        uygulanabilir = dep["BYS"] >= uyg["esik_diger"]
        uyg.update({"satir": "diger", "esik": uyg["esik_diger"]})
        uyarilar.append(f"η_bi,max = {eta_tum:.2f} > 2,0: bina Tablo 4.4'ün 'diğer tüm binalar' satırına düşer (DTS = {dep['DTS']} için "
                        f"BYS ≥ {uyg['esik_diger']}); BYS = {dep['BYS']} → eşdeğer deprem yükü yöntemi "
                        + ("yine uygulanabilir. D_bi, md. 4.7.4'ün 1,2 < η_bi ≤ 2,0 koşulu dışında kaldığı için (2,0/1,2)² ile sınırlı tutuldu."
                           if uygulanabilir else "uygulanamaz; mod birleştirme yöntemi gerekir (md. 4.6.2.1). Sonuçlar yalnız öğretim amaçlıdır."))
    yon_ozet = {}
    for yon, v in (("X", X), ("Y", Yy)):
        yon_ozet[yon] = {a: v[a] for a in ("Tp", "Tp_rayleigh", "Tp_rayleigh_sinirli", "Tp_yontem", "Sae_Tp", "Ra", "SaR", "VtE",
                                           "VtE_hesap", "VtE_min", "alt_sinir_etkin", "dFN", "e_oran", "D_b", "eta_max", "lambda",
                                           "sinir", "olcek_drift", "Tp_drift", "V_drift", "theta_max", "theta_sinir", "Mo", "rayleigh")}
    sp3 = dep["sp3"]
    return {"FS": sp_["FS"], "F1": sp_["F1"], "SDS": sp_["SDS"], "SD1": sp_["SD1"], "TA": sp_["TA"], "TB": sp_["TB"], "TL": sp_["TL"],
            "DTS": dep["DTS"], "BYS": dep["BYS"], "I": dep["I"], "R": dep["R"], "D": dep["D"], "n": d["n"], "n_oneri": d["n_oneri"],
            "HN": dep["HN"], "Ct": d["Ct"], "TpA": dep["TpA"], "Tp": X["Tp"], "Tp_yontem": X["Tp_yontem"], "Tp_rayleigh": X["Tp_rayleigh"],
            "Sae_Tp": X["Sae_Tp"], "Ra": X["Ra"], "SaR": X["SaR"], "VtE": X["VtE"], "VtE_min": X["VtE_min"], "dFN": X["dFN"],
            "m_t": dep["mt"], "W_t": dep["wt"], "N": dep["N"], "EZ_katsayi": kz, "kappa": dep["kappa"], "Ch": dep["Ch"],
            "lambda": X["lambda"], "theta_sinir": theta_sinir, "sinir_oran": X["sinir"], "dolgu": d["dolgu"], "e_oran": d["dismerkezlik"],
            "SDS_DD3": sp3["SDS"] if sp3 else None, "SD1_DD3": sp3["SD1"] if sp3 else None,
            "diyafram": "rijit" if ag["efendi"] else "esnek", "diyafram_istek": d["diyafram"], "catlamis_rijitlik": B.analiz["catlamis_rijitlik"],
            "zemin_sinifi": d["zemin_sinifi"], "SS": d["SS"], "S1": d["S1"], "BKS": d["BKS"], "tasiyici": d["tasiyici"],
            "tasiyici_kod": d["tasiyici_kod"], "tasiyici_tanim": d["tasiyici_tanim"], "SS_DD3": d["SS_DD3"], "S1_DD3": d["S1_DD3"],
            "X": yon_ozet["X"], "Y": yon_ozet["Y"], "katlar": katlar, "spektrum": _spektrum_noktalari(dep, X["Tp"]),
            "uyarilar": uyarilar, "uygulanabilir": uygulanabilir, "uygulanabilirlik": uyg, "ampirik_yeter": dep["ampirik_yeter"],
            "D_b_kat": {str(k): v for k, v in X["D_b_kat"].items()}, "kaynaklar": _deprem_kaynaklari(d), "tahmin": False}


def _deprem_ozet(B, Y, dep, Tp=None):
    """Çözümsüz önizleme (köprü bina_deprem): spektrum, sınıflar, T_pA, V_tE, F_iE ve V_i (ampirik periyotla; iki yönde aynı).
    Şekli veri.deprem ile aynıdır; çözüm gerektiren alanlar (d, δ, η_bi, θ_II) yoktur, ``tahmin: True``."""
    Tp = dep["TpA"] if Tp is None else Tp
    V, Vmin, Vk, dFN, F = _taban_kesme(dep, Tp)
    sp_ = dep["sp"]
    sp3 = dep["sp3"]
    d = B.deprem
    lam = sp3["Sae"](Tp) / sp_["Sae"](Tp) if sp3 is not None else 1.0
    katlar = _kat_kuvvet_tablosu(dep["kutle"], F, dFN, F, dFN)
    for s in katlar:
        s["sinir"] = dep["sinir_oran"]
        for y in ("x", "y"):
            B_dik = s["BY"] if y == "x" else s["BX"]
            s[f"e_{y}"] = d["dismerkezlik"] * B_dik
            s[f"Mb_{y}"] = s["F_" + y] * s[f"e_{y}"]
    return {"FS": sp_["FS"], "F1": sp_["F1"], "SDS": sp_["SDS"], "SD1": sp_["SD1"], "TA": sp_["TA"], "TB": sp_["TB"], "TL": sp_["TL"],
            "DTS": dep["DTS"], "BYS": dep["BYS"], "I": dep["I"], "R": dep["R"], "D": dep["D"], "n": d["n"], "n_oneri": d["n_oneri"],
            "HN": dep["HN"], "Ct": d["Ct"], "TpA": dep["TpA"], "Tp": Tp, "Tp_yontem": "ampirik (önizleme)", "Sae_Tp": sp_["Sae"](Tp),
            "Ra": dep["Ra"](Tp), "SaR": dep["SaR"](Tp), "VtE": Vk, "VtE_hesap": V, "VtE_min": Vmin, "dFN": dFN,
            "m_t": dep["mt"], "W_t": dep["wt"], "N": dep["N"], "EZ_katsayi": 2.0 / 3.0 * sp_["SDS"], "kappa": dep["kappa"], "Ch": dep["Ch"],
            "lambda": lam, "theta_sinir": 0.12 * dep["D"] / (dep["Ch"] * dep["R"]), "sinir_oran": dep["sinir_oran"],
            "SDS_DD3": sp3["SDS"] if sp3 else None, "SD1_DD3": sp3["SD1"] if sp3 else None, "dolgu": d["dolgu"], "e_oran": d["dismerkezlik"],
            "zemin_sinifi": d["zemin_sinifi"], "SS": d["SS"], "S1": d["S1"], "BKS": d["BKS"], "tasiyici": d["tasiyici"],
            "tasiyici_kod": d["tasiyici_kod"], "tasiyici_tanim": d["tasiyici_tanim"], "SS_DD3": d["SS_DD3"], "S1_DD3": d["S1_DD3"],
            "katlar": katlar, "spektrum": _spektrum_noktalari(dep, Tp), "uyarilar": list(dep["uyarilar"]),
            "uygulanabilir": dep["uygulanabilir"], "uygulanabilirlik": dep["uygulanabilirlik"], "ampirik_yeter": dep["ampirik_yeter"],
            "kaynaklar": _deprem_kaynaklari(d), "tahmin": True}


def deprem_onizleme(bina):
    """Köprü ``bina_deprem``: çözüm yapmadan spektrum, sınıflar, kat ağırlıkları, V_tE, F_iE ve V_i (ampirik T_pA ile).
    Deprem yük durumu kapalı olsa da deprem kartı varsa hesaplanır (arayüz girdileri canlı önizler)."""
    if isinstance(bina, str):
        try:
            bina = json.loads(bina)
        except ValueError as e:
            raise MatrisHatasi(f"Bina JSON olarak okunamadı: {e}") from None
    if not isinstance(bina, dict):
        raise MatrisHatasi("Bina bir sözlük (ya da JSON metni) olmalı.")
    if not isinstance(bina.get("deprem"), dict) or not bina["deprem"]:
        raise MatrisHatasi("Deprem önizlemesi için 'deprem' kartı gerekli: {\"SS\": 1.0, \"S1\": 0.3, \"zemin_sinifi\": \"ZC\", ...}.")
    bina = dict(bina, deprem=dict(bina["deprem"], etkin=True))
    B = _bina_oku(bina)
    Y = _yukleri_hazirla(B)
    kutle = _kat_kutleleri(B, Y, n=B.deprem["n"], kar_payi=yv.TBDY_KUTLE_KATILIM_KULLANIM["kar"] if B.kar else 0.0)
    if not kutle or sum(k["m"] * k["H"] for k in kutle) <= 0:
        raise MatrisHatasi("Deprem önizlemesi için katlarda kütle yok: döşeme, kiriş ya da kolon ekleyin.")
    dep = _deprem_on(B, Y, kutle)
    veri = _deprem_ozet(B, Y, dep)
    veri["uyarilar"] = list(dict.fromkeys(list(B.uyarilar) + veri["uyarilar"]))
    return _sonlu(veri)


def _sonlu(v):
    """JSON'a yazılacak iç içe yapıda float'ları yuvarlar, sayı olmayanları bırakır."""
    if isinstance(v, dict):
        return {k: _sonlu(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_sonlu(x) for x in v]
    if isinstance(v, bool) or v is None or isinstance(v, (str, int)):
        return v
    if isinstance(v, float):
        return _r(v)
    try:
        return _r(float(v))
    except (TypeError, ValueError):
        return v


# ============================================================================
# Şemalar: spektrum ve kat kuvvetleri (deprem)
# ============================================================================
def _sema_spektrum(deprem):
    """S_ae(T) ve S_aR(T) eğrileri; T_A, T_B, T_p işaretli."""
    pts = deprem["spektrum"]
    Tmax, Smax = max(p[0] for p in pts), max(p[1] for p in pts)
    sx, sy = 300.0 / max(Tmax, 1e-9), 150.0 / max(Smax, 1e-9)
    c = _cizici([(0, 0), (300.0, 150.0)], genislik=360.0)
    c.cizgi(c.P(0, 0), c.P(300, 0), "n", kalin=1.0)
    c.cizgi(c.P(0, 0), c.P(0, 150), "n", kalin=1.0)
    c.yol([c.P(p[0] * sx, p[1] * sy) for p in pts], "a", kalin=2.0)
    c.yol([c.P(p[0] * sx, p[2] * sy) for p in pts], "b", kalin=2.0)
    for T, ad in ((deprem["TA"], "T_A"), (deprem["TB"], "T_B"), (deprem["Tp"], "T_p")):
        X, Y0 = c.P(T * sx, 0)
        c.cizgi((X, Y0), c.P(T * sx, 150), "n", kalin=0.8, kesik="3 3", opak=0.6)
        c.yazi(X, Y0 + 14, f"{ad} = {_f(T, 2)} s", boyut=10)
    c.yazi(*c.P(300, 150), f"S_ae(T_p) = {_f(deprem['Sae_Tp'], 3)} g (mavi)", boyut=10, hiza="end")
    c.yazi(*c.P(300, 135), f"S_aR(T_p) = {_f(deprem['SaR'], 3)} g (amber), R_a = {_f(deprem['Ra'], 2)}", boyut=10, hiza="end")
    c.yazi(*c.P(0, 160), f"S_DS = {_f(deprem['SDS'], 3)}, S_D1 = {_f(deprem['SD1'], 3)}", boyut=10, hiza="start")
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 20.0, "Yatay elastik tasarım spektrumu (Denk. 2.2) ve azaltılmış spektrum (Denk. 4.8) · T (s) → S_a (g)",
           boyut=11, opak=0.8)
    return {"baslik": "Tasarım spektrumu (TBDY 2018 Denk. 2.2 / 4.8)", "svg": c.svg("Spektrum")}


def _sema_kat_kuvvetleri(deprem):
    """Kat deprem kuvvetleri F_iE (X yönü) çubukları ve kat kesmeleri V_i."""
    katlar = deprem["katlar"]
    Fmax = max([abs(k.get("F_x", 0.0)) for k in katlar] + [1e-9])
    gen_y = 40.0
    c = _cizici([(0, 0), (260.0, gen_y * (len(katlar) + 1))], genislik=320.0)
    c.cizgi(c.P(100, 0), c.P(100, gen_y * (len(katlar) + 0.5)), "n", kalin=1.6)
    for k in katlar:
        y = gen_y * k["kat"]
        w = 140.0 * abs(k.get("F_x", 0.0)) / Fmax
        X0, Y0 = c.P(100, y + 8)
        c.dikdortgen(X0, Y0, w, 16.0, aile="a", katman="orta")
        c.ok(c.P(100 - 24, y), c.P(100 - 4, y), "b", g=0, kalin=1.6, uc=6.0)
        c.yazi(*c.P(100 + w + 6, y), f"F{k['kat']} = {_f(k.get('F_x', 0.0), 1)} kN · V{k['kat']} = {_f(k.get('V_x', 0.0), 1)} kN", boyut=10, hiza="start")
        c.yazi(*c.P(70, y), f"k{k['kat']} (H = {_f(k['H'])} m)", boyut=10, hiza="end")
        c.cizgi(c.P(90, y), c.P(110, y), "n", kalin=0.8, kesik="2 2")
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 20.0, f"V_tE = {_f(deprem['VtE'], 1)} kN (X yönü) · ΔF_N = {_f(deprem['dFN'], 1)} kN tepe kata · F_i ∝ m_i·H_i",
           boyut=11, opak=0.8)
    return {"baslik": "Kat deprem kuvvetleri F_iE ve kat kesmeleri (Denk. 4.19–4.23)", "svg": c.svg("Kat kuvvetleri")}


# ============================================================================
# Anlatım: yük durumları (6), deprem (7), kombinasyonlar (10), denge (11)
# ============================================================================
def _ara_deger_metni(tablo, zemin, deger, ad, girdi_ad):
    """Tablo 2.1 / 2.2 okuması: hangi sütunlar, doğrusal ara değer (md. 2.3.3.1)."""
    x = tablo["SS"] if "SS" in tablo else tablo["S1"]
    y = tablo[zemin]
    v = float(deger)
    if v <= x[0] + 1e-12:
        return f"{girdi_ad} = {_f(v, 3)} ≤ {_f(x[0])} → ilk sütun, {ad} = {_f(y[0], 3)}"
    if v >= x[-1] - 1e-12:
        return f"{girdi_ad} = {_f(v, 3)} ≥ {_f(x[-1])} → son sütun, {ad} = {_f(y[-1], 3)}"
    for i in range(len(x) - 1):
        if abs(v - x[i]) < 1e-12:
            return f"{girdi_ad} = {_f(v, 3)} sütunu: {ad} = {_f(y[i], 3)}"
        if x[i] < v < x[i + 1]:
            t = (v - x[i]) / (x[i + 1] - x[i])
            return (f"{girdi_ad} = {_f(v, 3)}, {_f(x[i])} ile {_f(x[i + 1])} sütunları arasında doğrusal ara değer: "
                    f"{ad} = {_f(y[i], 3)} + ({_f(v, 3)} − {_f(x[i])})/({_f(x[i + 1])} − {_f(x[i])})·({_f(y[i + 1], 3)} − {_f(y[i], 3)}) "
                    f"= {_f(y[i] + t * (y[i + 1] - y[i]), 4)}")
    return f"{ad} = {_f(y[-1], 3)}"  # pragma: no cover


def _adim_6(B, durumlar, Y, ruzgar, anl):
    se._basla(anl, 6, "Yük durumları: G, Q, S, W ve E ayrı ayrı",
              "Yaygın yapı analiz programlarındaki 'load pattern' (yük deseni) gibi her yük türünü ayrı bir sağ taraf "
              "vektörü olarak kuruyoruz. Neden ayrı? Çünkü "
              "kombinasyon katsayıları farklıdır (1,4G + 1,6Q; 0,9G + 1,3W; G + Q + 0,2S + E_d(H) + 0,3E_d(Z)) ve doğrusal "
              "sistemde sonuçlar sonradan toplanabilir; bir kez kurulan K ile bütün sağ taraflar tek çözümde biter.")
    anl.metin("Yapı analiz programlarının dilinde: **load pattern** = yükün kendisi (G, Q, S, W+X …), "
              "**load case** = bir pattern'in çözümü "
              "(burada doğrusal statik, tek K), **load combination** = case sonuçlarının katsayılı toplamı (10. adım). "
              "Programların TBDY 2018'e göre kendiliğinden ürettiği eşdeğer deprem yüklerini 7. adımda elle kuruyoruz.")
    sat = []
    el_L = {e["no"]: e["L"] for e in B.ag["elemanlar"]}
    for ad, d in durumlar.items():
        if _birim_mi(ad):
            continue
        parcali = sum(1 for y in d["yayili"] if "q1" in y)
        duzgun = len(d["yayili"]) - parcali
        topq = -sum((y.get("q") or 0.0) * el_L[y["eleman"]] for y in d["yayili"] if "q" in y)
        topp = -sum((y["q1"] + y["q2"]) / 2.0 * (y["x2"] - y["x1"]) for y in d["yayili"] if "q1" in y)
        topF = -sum(y.get("Fy", 0.0) for y in d["yukler"])
        topX = sum(y.get("Fx", 0.0) for y in d["yukler"])
        topY = -sum(y.get("Fz", 0.0) for y in d["yukler"])
        topM = sum(y.get("My", 0.0) for y in d["yukler"])
        if ad in yv.YUK_DURUMU_ADLARI:
            anlam = yv.YUK_DURUMU_ADLARI[ad]
        elif ad.startswith("W"):
            anlam = f"rüzgâr, {ad[1:]} doğrultusu"
        elif ad == "EZ":
            anlam = "düşey deprem (2/3)·S_DS·G"
        else:
            anlam = f"deprem {ad[1]} yönü, dışmerkezlik {ad[2:]}%5"
        sat.append([ad, anlam, duzgun, parcali, len(d["yukler"]), _f(topq + topp + topF), _f(topX), _f(topY), _f(topM)])
    anl.metin(_tablo(["Durum", "Anlam", "Düzgün yayılı", "Parçalı (üçgen/trapez)", "Düğüm yükü", "Σ düşey (kN)", "Σ F_X (kN)",
                      "Σ F_Y (kN)", "Σ M_Z düğüm (kN·m)"], sat))
    anl.metin("Parçalı kayıt biçimi: `{\"eleman\": no, \"q1\": q(x1), \"q2\": q(x2), \"x1\": 0, \"x2\": L}` (yerel y′, aşağı negatif); "
              "aynı elemana gelen kayıtlar üst üste toplanır.")
    if B.kar:
        k = B.kar
        anl.metin(f"**Kar (S)** — TS 498:2021 md. 11: bölge {k['bolge']}, rakım {_f(k['rakim'], 0)} m → S_k = **{_f(k['Sk'], 2)} kN/m²** "
                  f"({k['Sk_kaynak']}); çatı şekil katsayısı μ1 = {_f(k['mu'], 2)} ({k['mu_kaynak']}), C_e = {_f(k['Ce'])}, C_t = {_f(k['Ct'])}.")
        anl.mat(rf"s = \mu_1 C_e C_t S_k = {_f(k['mu'], 2)}\cdot{_f(k['Ce'])}\cdot{_f(k['Ct'])}\cdot{_f(k['Sk'], 2)} = {_f(k['s'], 3)}\ \text{{kN/m}}^2"
                rf"\quad\Rightarrow\quad \Sigma S = {_f(Y.toplam['S'])}\ \text{{kN (yalnız kat {B.nk} döşemeleri)}}")
        anl.metin("Kar, çatı döşemesinden kirişlere G ve Q ile aynı 45° kuralıyla gider (aynı üçgen/trapez şekiller, tepe s·l_k/2).")
        anl.uyari("TS 498:2021 çatı şekli için TS EN 1991-1-3'e yönlendirir; μ1 Eurocode Tablo 5.2'dendir (standart metni doğrudan "
                  "görülmedi, ikincil kaynaklar tutarlı).")
        anl.metin("Kar, TS 498:2021 md. 3.1'e göre bir **hareketli yük**tür; kar ile rüzgârın birlikte etkisi için md. 12.1 iki durum "
                  "verir: S/2 + W ya da S + W/2 (eğimi 45°'ye kadar çatılarda, en elverişsizi). 10. adımdaki kombinasyonlar bunu kullanır.")
    if ruzgar:
        anl.metin(f"**Rüzgâr (W±X, W±Y)** — TS 498:2021 md. 14: hız basıncı q(z) Çizelge 4 basamakları (0–8 m 0,5; 8–20 m 0,8; 20–100 m 1,1; "
                  f"> 100 m 1,3 kN/m²; z temel üstünden kat seviyesi), kapalı binada rüzgâra dik yüzeyde basınç + emme toplam katsayısı "
                  f"C = {_f(ruzgar['C'])} ({ruzgar['C_kaynak']}). Kat kuvveti:")
        anl.mat(r"W_i = C\,q(z_i)\,A_i,\qquad A_i = B_{cephe}\left(\frac{h_i}{2} + \frac{h_{i+1}}{2}\right)")
        anl.metin(_tablo(["Kat", "z (m)", "q (kN/m²)", "Kat payı (m)", "B_cephe X-rüzgârı (m)", "A_x (m²)", "F_x (kN)",
                          "B_cephe Y-rüzgârı (m)", "A_y (m²)", "F_y (kN)"],
                         [[k["kat"], _f(k["z"]), _f(k["q"]), _f(k["h_pay"]), _f(k["genislik_x"]), _f(k["cephe_x"]), _f(k["F_x"]),
                           _f(k["genislik_y"]), _f(k["cephe_y"]), _f(k["F_y"])] for k in ruzgar["katlar"]]
                         + [["Σ", "", "", "", "", "", _f(ruzgar["toplam_x"]), "", "", _f(ruzgar["toplam_y"])]]))
        anl.metin("Kat kuvveti rüzgârın çarptığı cephedeki kat düğümlerine, düğümün iki komşu aks aralığının yarısı oranında dağıtılır "
                  "(W+X: batı cephesinden +X yönünde; W−X: doğu cephesinden −X yönünde).")
    if B.deprem:
        anl.metin("**Deprem (EX±, EY±, EZ)**: eşdeğer deprem yükü kat kuvvetleri 7. adımda türetilir. Motor önce birim durumları "
                  "çözer (kat kuvveti şekli s_i = m_iH_i/Σm_jH_j, tepe kat 1 kN, birim burulma); EX± ve EY± bunların katsayılı "
                  "toplamıdır: EX+ / EX−: X yönü kat kuvvetleri, kütle merkezinden dik kat boyutunun ±%5'i kadar kaydırılmış "
                  "(ek burulma momenti). EZ: düşey deprem, G durumunun (2/3)·S_DS katı (Denk. 4.10).")


def _adim_7(B, deprem, anl):
    se._basla(anl, 7, "TBDY 2018 eşdeğer deprem yükü",
              "Deprem, binayı kütlesiyle orantılı yatay kuvvetlerle iter. Yönetmelik bunu bir tasarım spektrumundan (zemin ve "
              "harita katsayıları), taşıyıcı sistem davranış katsayısı R ile azaltarak ve kat kütlelerine yükseklikle orantılı "
              "dağıtarak hesaplar. Sonra dışmerkezlik, burulma düzensizliği, göreli kat ötelemesi ve ikinci mertebe denetlenir.")
    if not deprem:
        anl.metin("Bu modelde deprem yükü kapalı (`yuk_durumlari.E.acik` ya da `deprem.etkin` = true ile açılır; S_S, S_1 AFAD "
                  "Türkiye Deprem Tehlike Haritası'ndan girilir).")
        return
    d = deprem
    X, Yy = d["X"], d["Y"]
    # 1. spektrum
    anl.metin(f"**7.1 Girdiler.** S_S = {_f(d['SS'], 3)}, S_1 = {_f(d['S1'], 3)} (DD-2, %10/50 yıl, AFAD TDTH), zemin **{d['zemin_sinifi']}** "
              f"(Tablo 16.1), BKS = {d['BKS']} → I = {_f(d['I'], 2)} (Tablo 3.1), taşıyıcı sistem **{d['tasiyici_kod']}** "
              f"({d['tasiyici_tanim']}) → R = {_f(d['R'])}, D = {_f(d['D'])} (Tablo 4.1), n = {_f(d['n'], 2)} (Tablo 4.3), "
              f"C_t = {_f(d['Ct'], 3)} (Denk. 4.27).")
    anl.metin("**7.2 Yerel zemin katsayıları** (Tablo 2.1 / 2.2):\n\n"
              f"- {_ara_deger_metni(yv.TBDY_FS, d['zemin_sinifi'], d['SS'], 'F_S', 'S_S')}\n"
              f"- {_ara_deger_metni(yv.TBDY_F1, d['zemin_sinifi'], d['S1'], 'F_1', 'S_1')}")
    anl.mat(r"S_{DS} = S_S F_S,\quad S_{D1} = S_1 F_1,\quad T_A = 0{,}2\frac{S_{D1}}{S_{DS}},\quad T_B = \frac{S_{D1}}{S_{DS}},\quad T_L = 6\ \text{s}")
    anl.metin(f"S_DS = {_f(d['SS'], 3)}·{_f(d['FS'], 3)} = **{_f(d['SDS'], 4)}**, S_D1 = {_f(d['S1'], 3)}·{_f(d['F1'], 3)} = **{_f(d['SD1'], 4)}**; "
              f"T_A = {_f(d['TA'], 4)} s, T_B = {_f(d['TB'], 4)} s, T_L = {_f(d['TL'], 1)} s.")
    anl.mat(r"S_{ae}(T)=\begin{cases}\left(0{,}4+0{,}6\frac{T}{T_A}\right)S_{DS} & T\le T_A\\ S_{DS} & T_A\le T\le T_B\\ "
            r"\frac{S_{D1}}{T} & T_B\le T\le T_L\\ \frac{S_{D1}T_L}{T^2} & T\ge T_L\end{cases},\qquad "
            r"R_a(T)=\begin{cases}\frac{R}{I} & T>T_B\\ D+\left(\frac{R}{I}-D\right)\frac{T}{T_B} & T\le T_B\end{cases},\qquad S_{aR}=\frac{S_{ae}}{R_a}")
    Ra = lambda T: d["R"] / d["I"] if T > d["TB"] else d["D"] + (d["R"] / d["I"] - d["D"]) * T / d["TB"]  # noqa: E731
    kose = [("T = 0", 0.0), ("T = T_A", d["TA"]), ("T = T_B", d["TB"]), ("T = 1 s", 1.0), ("T = T_p", d["Tp"])]
    sat = []
    for ad, T in kose:
        sae = (0.4 + 0.6 * T / d["TA"]) * d["SDS"] if T <= d["TA"] else (d["SDS"] if T <= d["TB"] else (d["SD1"] / T if T <= d["TL"] else d["SD1"] * d["TL"] / T ** 2))
        sat.append([ad, _f(T, 4), _f(sae, 4), _f(Ra(T), 3), _f(sae / Ra(T), 4)])
    anl.metin("Spektrumun köşe değerleri (S_ae(T_A) = S_ae(T_B) = S_DS; T = 1 s'de S_ae = S_D1 (T_B ≤ 1 s ise); R_a T_B'de süreklidir):\n\n"
              + _tablo(["Nokta", "T (s)", "S_ae (g)", "R_a", "S_aR (g)"], sat))
    # 2. sınıflar ve uygulanabilirlik
    u = d.get("uygulanabilirlik") or {}
    anl.metin(f"**7.3 Sınıflar.** S_DS = {_f(d['SDS'], 3)} → DTS = **{d['DTS']}** (Tablo 3.2); H_N = {_f(d['HN'])} m → BYS = **{d['BYS']}** (Tablo 3.3). "
              f"Tablo 4.4: {u.get('kosul_duzenli', 'düzenli bina')} için BYS ≥ {u.get('esik_duzenli', '–')}, diğer binalar için "
              f"BYS ≥ {u.get('esik_diger', '–')}; bu binada η_bi,max = {_f(max(X['eta_max'], Yy['eta_max']), 3)} → "
              + ("1. satır (η_bi ≤ 2,0)" if u.get("satir", "duzenli") == "duzenli" else "'diğer tüm binalar' satırı (η_bi > 2,0)")
              + " → eşdeğer deprem yükü yöntemi "
              + ("**uygulanabilir**." if d["uygulanabilir"] else "**uygulanamaz** (mod birleştirme gerekir; sonuçlar yalnız öğretim içindir).")
              + " B2 (yumuşak kat) düzensizliği bu modülde denetlenmez.")
    # 3. kütleler
    anl.metin("**7.4 Kat ağırlıkları ve kütleleri** (Denk. 4.16: w_i = w_G + n·w_Q" + (" + 0,3·S (çatı)" if B.kar else "")
              + "; kolon öz ağırlığı üst ve alt kata yarı yarıya; H_i temel üstünden):\n\n"
              + _tablo(["Kat", "H_i (m)", "w_i (kN)", "m_i = w_i/g (t)", "m_i·H_i", "Kütle merkezi (X, Y)"],
                       [[k["kat"], _f(k["H"]), _f(k["w_i"]), _f(k["m_i"], 3), _f(k["m_i"] * k["H"], 2), f"({_f(k['X'])}, {_f(k['Y'])})"] for k in d["katlar"]]
                       + [["Σ", "", _f(d["W_t"]), _f(d["m_t"], 3), _f(sum(k["m_i"] * k["H"] for k in d["katlar"]), 2), ""]]))
    # 4. periyot
    anl.metin("**7.5 Hakim periyot — iki yol.** (a) Ampirik (Denk. 4.27) ve (b) Rayleigh (Denk. 4.26): kat kütle merkezlerine "
              "kurgusal F_fi ∝ m_i·H_i kuvvetleri (Σ = 1 kN) uygulanıp kat yer değiştirmeleri d_fi bu ağdan çözülür.")
    anl.mat(rf"T_{{pA}} = C_t H_N^{{3/4}} = {_f(d['Ct'], 3)}\cdot{_f(d['HN'])}^{{0{{,}}75}} = {_f(d['TpA'], 4)}\ \text{{s}},\qquad "
            r"T_p = 2\pi\sqrt{\frac{\sum m_i d_{fi}^2}{\sum F_{fi} d_{fi}}}\ \le 1{,}4\,T_{pA}")
    for yon, v in (("X", X), ("Y", Yy)):
        ray = v["rayleigh"]
        pay, payda = sum(r["m"] * r["d_f"] ** 2 for r in ray), sum(r["F_f"] * r["d_f"] for r in ray)
        anl.metin(f"Rayleigh, {yon} yönü:\n\n" + _tablo(["Kat", "m_i (t)", "F_fi (kN)", "d_fi (mm)", "m_i·d_fi² (t·m²)", "F_fi·d_fi (kN·m)"],
                                                        [[r["kat"], _f(r["m"], 3), _f(r["F_f"], 4), f"{r['d_f'] * 1000:.6f}", f"{r['m'] * r['d_f'] ** 2:.4e}",
                                                          f"{r['F_f'] * r['d_f']:.4e}"] for r in ray]
                                                        + [["Σ", "", "1", "", f"{pay:.4e}", f"{payda:.4e}"]])
                  + f"\n\nT_p,{yon} = 2π·√({pay:.4e}/{payda:.4e}) = **{_f(v['Tp_rayleigh'], 4)} s** (1,4·T_pA = {_f(1.4 * d['TpA'], 4)} s).")
    anl.metin(f"Kullanılan yöntem: **{d['Tp_yontem']}**"
              + (" (md. 4.7.3.3: bu binada T_p ≅ T_pA alınabilir; Rayleigh yalnız karşılaştırma)" if d["Tp_yontem"] == "ampirik" else " (≤ 1,4·T_pA ile sınırlı)")
              + f" → T_p,X = {_f(X['Tp'], 4)} s, T_p,Y = {_f(Yy['Tp'], 4)} s."
              + (" Rayleigh çözümü çatlamış kesitli K ile yapıldı (Tablo 4.2, md. 4.5.8): EI küçüldüğü için periyot brüt kesite göre "
                 "uzar (yaklaşık √(1/0,35…1/0,70) kat), ötelemeler büyür."
                 if d["catlamis_rijitlik"] else " Brüt kesit kullanıldı: betonarmede TBDY 4.5.8.1'e aykırı (periyot kısa, öteleme küçük çıkar)."
                 if B.sistem == "betonarme" else ""))
    # 5. taban kesme ve kat kuvvetleri
    anl.mat(r"V_{tE} = m_t\,S_{aR}(T_p)\,g \ \ge\ 0{,}04\,m_t\,I\,S_{DS}\,g,\qquad \Delta F_{NE} = 0{,}0075\,N\,V_{tE},\qquad "
            r"F_{iE} = (V_{tE}-\Delta F_{NE})\frac{m_i H_i}{\sum m_j H_j}")
    sat = []
    for yon, v in (("X", X), ("Y", Yy)):
        sat.append([yon, _f(v["Tp"], 4), _f(v["Sae_Tp"], 4), _f(v["Ra"], 3), _f(v["SaR"], 4), _f(v["VtE_hesap"]), _f(v["VtE_min"]),
                    _f(v["VtE"]) + (" (alt sınır)" if v["alt_sinir_etkin"] else ""), _f(v["dFN"]), _f(v["Mo"], 1)])
    anl.metin("**7.6 Taban kesme kuvveti** (g = 9,81 m/s²):\n\n"
              + _tablo(["Yön", "T_p (s)", "S_ae(T_p)", "R_a", "S_aR", "m_t·S_aR·g", "0,04·m_t·I·S_DS·g", "V_tE (kN)", "ΔF_NE (kN)", "M_o (kN·m)"], sat))
    toplam_mh = sum(k["m_i"] * k["H"] for k in d["katlar"])
    anl.metin("**7.7 Kat kuvvetleri F_iE ve kat kesmeleri V_i** (tepe kata ΔF_NE eklenmiş; V_i = Σ_{j≥i} F_j):\n\n"
              + _tablo(["Kat", "H_i (m)", "m_i·H_i/Σ", "F_x (kN)", "V_x (kN)", "F_y (kN)", "V_y (kN)"],
                       [[k["kat"], _f(k["H"]), _f(k["m_i"] * k["H"] / toplam_mh, 4), _f(k["F_x"]), _f(k["V_x"]), _f(k["F_y"]), _f(k["V_y"])] for k in d["katlar"]]
                       + [["Σ", "", "1", _f(sum(k["F_x"] for k in d["katlar"])), "", _f(sum(k["F_y"] for k in d["katlar"])), ""]])
              + f"\n\nSağlama: Σ F_iE + ΔF_NE = {_f(sum(k['F_x'] for k in d['katlar']))} kN = V_tE,X = {_f(X['VtE'])} kN ✓")
    # 6. dışmerkezlik, diyafram
    anl.metin(f"**7.8 Ek dışmerkezlik ve rijit diyafram** (md. 4.5.10.2, Denk. 4.17): kat kuvveti kütle merkezinden deprem doğrultusuna dik "
              f"kat boyutunun ±%{_f(100 * d['e_oran'], 1)}'i (A1 düzensizliği olan katta × D_bi) kadar kaydırılır; kütle merkezinde ek "
              "burulma momenti M_ib = F_iE·e_i. "
              "İşaret: EX+ kuvveti +Y'ye kaydırır → M_Z = −F·e; EY+ kuvveti +X'e kaydırır → M_Z = +F·e (Z yukarı, sağ el).\n\n"
              + _tablo(["Kat", "B_⊥,x (m)", "e_x (m)", "M_b,x = F_x·e_x (kN·m)", "B_⊥,y (m)", "e_y (m)", "M_b,y (kN·m)"],
                       [[k["kat"], _f(k["B_dik_x"]), _f(k["e_x"], 3), _f(k["Mb_x"]), _f(k["B_dik_y"]), _f(k["e_y"], 3), _f(k["Mb_y"])] for k in d["katlar"]]))
    if d["diyafram"] == "rijit":
        anl.metin("Diyafram **rijit**: her katta kütle merkezinde bir efendi düğüm (9000 + kat) vardır; köle düğümlerin düzlem içi "
                  "serbestlikleri ona bağlanır (efendi–köle / MPC). Kat kuvveti ve burulma momenti efendi düğüme uygulanır, kütle de "
                  "orada toplanmış sayılır. Köle yer değiştirmesi efendinin rijit cisim hareketidir (ω × r):")
        anl.mat(r"u_{X,s} = u_{X,m} - \theta_Z\,(Y_s - Y_m),\qquad u_{Y,s} = u_{Y,m} + \theta_Z\,(X_s - X_m),\qquad \theta_{Z,s} = \theta_{Z,m}")
    else:
        anl.metin("Diyafram **esnek**: kat kuvveti kat düğümlerine düğüm kütlesi payıyla, burulma momenti aynı momenti veren (net "
                  "kuvveti sıfır) bir kuvvet çiftiyle dağıtılır.")
    anl.mat(r"\eta_{bi} = \frac{(\Delta_i)_{max}}{(\Delta_i)_{ort}},\quad (\Delta_i)_{ort} = \tfrac{1}{2}[(\Delta_i)_{max}+(\Delta_i)_{min}];\qquad "
            r"\eta_{bi} > 1{,}2 \Rightarrow D_{bi} = \left(\frac{\eta_{bi}}{1{,}2}\right)^2")
    dbk = {int(k): v for k, v in (d.get("D_b_kat") or {}).items()}
    anl.metin(f"Burulma düzensizliği katsayısı η_bi,max: X yönü {_f(X['eta_max'], 3)}, Y yönü {_f(Yy['eta_max'], 3)}. Simetrik binada "
              "dışmerkezlik olmasa η_bi = 1 olurdu; ±%5 kaydırma tek başına η_bi'yi biraz büyütür. **md. 4.7.4**: A1 düzensizliği "
              "(1,2 < η_bi ≤ 2,0) olan **her katta ayrı ayrı**, o katın ±%5 dışmerkezliği **her iki deprem doğrultusu için** "
              "D_bi = (η_bi/1,2)² ile büyütülür (η_bi = o katta iki doğrultunun büyüğü; ilk hesaptan, yinelenmez). Bunun için birim "
              "burulma durumu kat kat ayrı çözülür (T_X1, T_X2, …).\n\n"
              + _tablo(["Kat", "η_bx", "η_by", "max η_bi", "D_bi", "e_x = 0,05·D_bi·B_⊥ (m)", "e_y (m)"],
                       [[k["kat"], _f(k["eta_bx"], 3), _f(k["eta_by"], 3), _f(max(k["eta_bx"], k["eta_by"]), 3),
                         _f(dbk.get(k["kat"], k.get("D_b", 1.0)), 3), _f(k["e_x"], 3), _f(k["e_y"], 3)] for k in d["katlar"]]))
    # 7. drift ve θ_II
    anl.mat(r"\Delta_i = u_i - u_{i-1},\qquad \delta_i = \frac{R}{I}\Delta_i,\qquad \lambda\frac{\delta_{i,max}}{h_i} \le "
            + (r"0{,}008\,\kappa" if d["dolgu"] == "bitisik" else r"0{,}016\,\kappa") + rf",\quad \kappa = {_f(d['kappa'], 1)},\ \lambda = {_f(d['lambda'], 3)}"
            r";\qquad \theta_{II,i} = \frac{(\Delta_i)_{ort}\sum_{k\ge i} w_k}{V_i h_i} \le 0{,}12\frac{D}{C_h R}")
    lam_metin = (f"λ = S_ae(T_p; DD-3)/S_ae(T_p; DD-2) = {_f(d['lambda'], 4)} (DD-3: S_DS = {_f(d['SDS_DD3'], 4)}, S_D1 = {_f(d['SD1_DD3'], 4)})"
                 if d.get("SDS_DD3") is not None else "λ = 1 (DD-3 spektrumu verilmedi; güvenli taraf)")
    anl.metin(f"{lam_metin}; sınır {_f(d['sinir_oran'], 4)} ({'gevrek dolgu çerçeveye bitişik' if d['dolgu'] == 'bitisik' else 'esnek derzli dolgu'}); "
              f"θ_II sınırı 0,12·D/(C_h·R) = {_f(d['theta_sinir'], 4)} (C_h = {_f(d['Ch'], 1)}).")
    sat = []
    for k in d["katlar"]:
        sat.append([k["kat"], _f(k["h"]), f"{k['delta_x'] * 1000:.2f}", f"{k['delta_etkin_x'] * 1000:.1f}", _f(k["oran_x"], 5), _f(k["eta_bx"], 3), _f(k["theta_x"], 4),
                    f"{k['delta_y'] * 1000:.2f}", f"{k['delta_etkin_y'] * 1000:.1f}", _f(k["oran_y"], 5), _f(k["eta_by"], 3), _f(k["theta_y"], 4),
                    _f(k["sinir"], 4), "✓" if k["uygun"] else "✗"])
    anl.metin("**7.9 Göreli kat ötelemesi, burulma ve ikinci mertebe** (Δ: azaltılmış yüklerle en büyük kolon hattı ötelemesi; δ = (R/I)·Δ; "
              "drift için md. 4.9.1.1 gereği 1,4·T_pA sınırı ve V_tE alt sınırı kaldırılmıştır):\n\n"
              + _tablo(["Kat", "h (m)", "Δ_x (mm)", "δ_x (mm)", "λδ_x/h", "η_bx", "θ_x", "Δ_y (mm)", "δ_y (mm)", "λδ_y/h", "η_by", "θ_y", "Sınır", "Uygun"], sat))
    anl.metin(f"**7.10 Düşey deprem** (Denk. 4.10): E_d(Z) ≈ (2/3)·S_DS·G = {_f(d['EZ_katsayi'], 4)}·G — EZ durumu G'nin bu katıdır "
              "(4.11'de +0,3, 4.12'de −0,3 katsayıyla girer).")
    for u_ in d["uyarilar"]:
        anl.uyari(u_)
    anl.sema("Spektrum ve kat kuvvetleri", [_sema_spektrum(d), _sema_kat_kuvvetleri(d)])


def _adim_10(B, kombinasyonlar, zarf, ag, ozet, anl):
    se._basla(anl, 10, "Kombinasyonlar ve zarf",
              "Doğrusal sistemde u_komb = Σγ_i u_i; iç kuvvetler de aynı katsayılarla toplanır. Yapı analiz programları bir kombinasyonu yeniden "
              "çözmez, case sonuçlarını toplar; biz de öyle yapıyoruz. Rüzgâr dört yöne, deprem Denk. (4.9)'un iki doğrultu "
              "birleştirmesine (%100 + %30) ve ± dışmerkezliğe göre çoğaltılır. Zarf, her kesitte kombinasyonların en büyüğü/en küçüğüdür.")
    anl.mat(r"\mathbf{u}_{komb} = \sum_i \gamma_i\,\mathbf{u}_i,\qquad \mathbf{f}_{komb} = \sum_i \gamma_i\,\mathbf{f}_i,\qquad "
            r"E_d^{(H)} = \pm E_d^{(X)} \pm 0{,}3E_d^{(Y)}\ \ \text{ya da}\ \ \pm 0{,}3E_d^{(X)} \pm E_d^{(Y)}")
    anl.metin("Ad kuralı: katsayılar sırasıyla yazılır, 1 yazılmaz, eksi terimin önüne gelir. Örnek: `G+Q+0.2S+EX++0.3EY++0.3EZ` = "
              "G + Q + 0,2·S + 1·(EX+) + 0,3·(EY+) + 0,3·EZ; `0.9G+EX-+0.3EY+-0.3EZ`; rüzgâr `G+1.3Q+1.3W+X` = G + 1,3Q + 1,3·(W+X).")
    aileler = {}
    for k in kombinasyonlar:
        a = aileler.setdefault(k["aile"], {"tur": k["tur"], "kaynak": k["kaynak"], "n": 0, "uygulandi": False, "neden": k.get("neden"), "ornek": None})
        if k["uygulandi"]:
            a["n"] += 1
            a["uygulandi"] = True
            a["ornek"] = a["ornek"] or k["ad"]
    anl.metin(f"Küme: **{yv.KOMBINASYONLAR[B.kombinasyon_kumesi]['ad']}**\n\n"
              + _tablo(["Kombinasyon (aile)", "Tür", "Kaynak", "Varyant", "Örnek ad", "Durum"],
                       [[ad, a["tur"], a["kaynak"], a["n"], f"`{a['ornek']}`" if a["ornek"] else "–",
                         "uygulandı ✓" if a["uygulandi"] else f"uygulanmadı: {a['neden']}"] for ad, a in aileler.items()]))
    if B.kombinasyon_kumesi == "ts500" and B.kar:
        anl.metin("**Kar (S) TS 500 birleşimlerinde:** TS 500 md. 6.2.6 kar terimini ayrı vermez; karakteristik yükler için atfettiği "
                  "TS 498:2021 kar yükünü hareketli yük sayar (md. 3.1) ve kar ile rüzgârın birlikteliğini md. 12'de düzenler. Bu "
                  "yüzden kar Q gibi katsayılandırılır: düşey birleşimde **1,4G + 1,6Q + 1,6S** (Denk. 6.3), rüzgârlı birleşimde md. 12.1'in "
                  "iki durumu **G + 1,3Q + 1,3(S/2) + 1,3W** ve **G + 1,3Q + 1,3S + 1,3(W/2)** (Denk. 6.5), servis **G + Q + S**; "
                  "0,9G + 1,3W ve karsız satırlar da kalır (kar her zaman bulunmayabilir). Deprem birleşiminde S, TBDY (4.11)'in 0,2S'siyle girer.")
    n_uyg = sum(1 for k in kombinasyonlar if k["uygulandi"] and k["tur"] != "drift")
    n_dr = sum(1 for k in kombinasyonlar if k["uygulandi"] and k["tur"] == "drift")
    anl.metin(f"Toplam **{n_uyg} dayanım/servis kombinasyonu** süperpozisyonla kuruldu"
              + (f" (ayrıca {n_dr} öteleme denetim birleşimi; zarfa girmez)" if n_dr else "")
              + f". Yanıtta yalnız seçilenlerin tam sonucu ({', '.join(ozet['gosterilecek'])}) yazılır; ötekiler zarfta ve özet "
              "tablosunda yaşar, istenen tek kombinasyonun tam dizileri `bina_kombinasyon` ile sonradan alınır.")
    sayac = {}
    for z in zarf["elemanlar"]:
        for ad in z["belirleyen"].values():
            sayac[ad] = sayac.get(ad, 0) + 1
    en = sorted(sayac.items(), key=lambda x: -x[1])[:8]
    anl.metin("**Zarfı en çok belirleyen kombinasyonlar** (eleman × büyüklük sayısı):\n\n" + _tablo(["Kombinasyon", "Belirlediği uç değer sayısı"], [[a, n] for a, n in en]))
    el = {e["no"]: e for e in ag["elemanlar"]}
    sat = []
    for z in zarf["elemanlar"][:60]:
        e = el[z["no"]]
        sat.append([z["no"], f"{'S' if e['tur'] == 'kolon' else 'K'}{e['kaynak_no']}", _f(z["N_min"]), _f(z["V_max"]), _f(z["V_min"]),
                    _f(z["M_max"]), _f(z["M_min"]), z["belirleyen"]["M_max"]])
    anl.metin("**Zarf** (N çekme +; M alt lif çekme +; kN, kN·m):\n\n"
              + _tablo(["Eleman", "Kaynak", "N_min", "V_max", "V_min", "M_max", "M_min", "M_max'ı belirleyen"], sat)
              + ("\n\n… (ilk 60 eleman)" if len(zarf["elemanlar"]) > 60 else ""))


def _adim_11(B, Y, akis, kombinasyonlar, ozetler, anl):
    se._basla(anl, 11, "Denge ve korunum: beş sayı, her kombinasyon",
              "Yük akışının sağlaması: döşeme + duvar + öz ağırlık toplamı = kirişlere giren = kolon tabanlarındaki ΣN = temel "
              "tepkileri = zemine giden. Beş sayı eşitse hiçbir yük yolda kaybolmamıştır. Her kombinasyonda ΣF ve ΣM kalıntısı "
              "sıfıra yakın olmalıdır.")
    sat = []
    for durum in ("G", "Q"):
        p = akis["korunum"][durum]
        sat.append([durum, _f(p["dosemeler"]), _f(p["duvarlar"]), _f(p["kiris_oz"]), _f(p["kolon_oz"]), _f(p["ek"]), _f(p["toplam"]),
                    _f(p["yuk_alani"]), _f(p["kolon_taban"]), _f(p["kat0"]), _f(p["temel"])])
    anl.metin(_tablo(["Durum", "Döşemeler", "Duvarlar", "Kiriş öz", "Kolon öz", "Ek", "**Toplam**", "Σ yük alanı", "**Σ kolon taban N**",
                      "Kat 0 düğüm yükü", "**Σ temel (tepki + yay)**"], sat))
    anl.metin("Toplam = Σ yük alanı = Σ kolon taban N + kat 0 düğüm yükü = Σ temel: temel seviyesine doğrudan verilen düğüm yükleri "
              "kolonlardan geçmeden mesnete iner; elastik temelde tepki yerine yay kuvveti okunur.")
    if any(abs(akis["korunum"][d]["dagitilamayan"]) > 1e-6 for d in ("G", "Q")):
        anl.uyari("Yük alanı el hesabında bazı kolonsuz düğüm payları hiçbir kolona ulaştırılamadı (kiriş zinciri kolona varmıyor); "
                  "FE çözümü yine de doğrudur, el hesabı toplamı eksik kalır.")
    aile = {}
    for k in kombinasyonlar:
        if not k["uygulandi"]:
            continue
        o = ozetler[k["ad"]]
        a = aile.setdefault(k["aile"], {"n": 0, "kalinti": 0.0, "FZ": [], "M": 0.0})
        a["n"] += 1
        a["kalinti"] = max(a["kalinti"], o["denge_enb"])
        a["FZ"].append(o["FZ_tepki"])
        a["M"] = max(a["M"], o["enb"]["M"])
    anl.metin("**Kombinasyon dengeleri** (aile başına: varyant sayısı, en büyük kalıntı |ΣF|,|ΣM|, Σ FZ tepki aralığı, en büyük |M|):\n\n"
              + _tablo(["Kombinasyon (aile)", "Varyant", "En büyük kalıntı", "Σ FZ tepki (kN) min … max", "max |M| (kN·m)"],
                       [[ad, a["n"], f"{a['kalinti']:.1e}", f"{_f(min(a['FZ']))} … {_f(max(a['FZ']))}", _f(a["M"])] for ad, a in aile.items()]))


# ============================================================================
# Adım 12: kesit tahkikleri (Dilim 3) — TS 500 / TBDY 2018 betonarme kiriş ve kolon, ÇYTHYE 2018 çelik eleman.
# Hesaplar tasarim.py'dedir; burada bina kuvvetleri (kombinasyon başına, eş zamanlı) elemanlara dağıtılır. tasarim.py
# yoksa (eski kurulum) bu bölüm atlanır ve veri["tasarim"] yazılmaz.
# ============================================================================
_PAS_EK = 0.02           # paspayı + etriye (Φ8) + boyuna çubuk yarıçapı ≈ paspayı + 20 mm: donatı ağırlık merkezi
_RHO_VARSAYILAN = 0.01   # TS 500 md. 7.4.1 / TBDY 2018 md. 7.3.2 en az kolon boyuna donatısı
_RHO_TARAMA = tuple(round(0.01 + 0.0025 * i, 4) for i in range(13))   # 0,01 → 0,04 (gerekli ρ önerisi)
_KONTROL_EN_FAZLA = 8
_TASARIM_TURLERI = ("dayanim", "deprem")
_DURUM_SIRA = {"yeterli": 0, "donatı artır": 1, "kesit büyüt": 2, "yetersiz": 2}
_DC_ARALIKLARI = (("<0.7", 0.7), ("0.7-0.9", 0.9), ("0.9-1.0", 1.0 + 1e-9), (">1.0", math.inf))
_I_N, _I_V, _I_M, _I_VZ, _I_MY = 0, 1, 2, 3, 4      # _DIYAGRAM sırası


def _tasarim_modulu():
    """tasarim.py (kesit hesapları) varsa (tembel) içe aktarır; yoksa None: bina çözümü tasarımsız sürer."""
    try:
        return importlib.import_module("tasarim")
    except ImportError:
        return None


def _tasarim_baglam(B, Y, ag, paket, kombinasyonlar):
    """Dayanım (TS 500 / ÇYTHYE) ve deprem (TBDY 4.4.4) kombinasyonlarının bütün diyagramları tek matris çarpımıyla:
    C (nk × L) = Γ (nk × ndurum) @ D (ndurum × L). Köprü ayrıntısı için önbellekte (ic["tasarim"]) saklanır."""
    kombs = [k for k in kombinasyonlar if k["uygulandi"] and k["tur"] in _TASARIM_TURLERI]
    adlar_d = list(paket.durum)
    G = np.zeros((len(kombs), len(adlar_d)))
    for i, k in enumerate(kombs):
        for d, g in k.get("cozum", k["katsayilar"]).items():
            if d in paket.durum:
                G[i, adlar_d.index(d)] = g
    D = np.array([paket.durum[d]["diy"] for d in adlar_d])
    GQ = np.zeros(paket.L)
    for d in ("G", "Q"):
        if d in paket.durum:
            GQ = GQ + paket.durum[d]["diy"]
    dosemeli = {p["kiris_no"] for d in Y.dosemeler for p in d["paylar"]}
    return SimpleNamespace(B=B, ag=ag, paket=paket, kombs=kombs, adlar=[k["ad"] for k in kombs],
                           deprem=[k["tur"] == "deprem" for k in kombs], C=G @ D, GQ=GQ, dosemeli=dosemeli,
                           el={e["no"]: e for e in ag["elemanlar"]}, idx={no: j for j, no in enumerate(paket.el_no)},
                           dno=ag["dno"], sonuclar={})


def _blok(T, eleman_no, dizi=None):
    """Eleman diyagram bloğu: (nk, 6, ns) = kombinasyon × (N, V, M, Vz, My, T) × istasyon (dizi verilirse (6, ns))."""
    p, j = T.paket, T.idx[eleman_no]
    if dizi is not None:
        return dizi[p.ofs[j]:p.ofs[j] + 6 * p.ns[j]].reshape(6, p.ns[j])
    return T.C[:, p.ofs[j]:p.ofs[j] + 6 * p.ns[j]].reshape(len(T.kombs), 6, p.ns[j])


def _kesit_bilgi(T, kesit_ad):
    """Tasarım için kesit kartı: betonarme (b, h, beton, donatı, paspayı, donatı ağırlık merkezi) ya da çelik profil."""
    B = T.B
    ks = B.kesitler[kesit_ad]
    m = B.malzemeler[ks["malzeme"]]
    if ks["tip"] == "profil":
        if m["tur"] != "celik":
            raise MatrisHatasi(f"Kesit {kesit_ad!r}: profil kesitin malzemesi çelik olmalı (S235, S275, S355).")
        return {"sistem": "celik", "profil": ks["profil"], "celik": m["kutuphane"], "malzeme_ad": ks["malzeme"]}
    if m["tur"] != "beton":
        raise MatrisHatasi(f"Kesit {kesit_ad!r}: dikdörtgen kesit beton malzemeli olmalı (dikdörtgen çelik kesit tahkiki yok).")
    ham = (B.ham.get("kesitler") or {}).get(kesit_ad) or {}
    don = ks.get("donati")
    if don and str(don) in B.malzemeler and B.malzemeler[str(don)]["tur"] == "donati":
        donati, donati_varsayim = B.malzemeler[str(don)]["kutuphane"], False
    elif don and str(don) in yv.DONATILAR:
        donati, donati_varsayim = str(don), False
    else:
        donati, donati_varsayim = "B420C", True
    pas = _sayi(ks.get("pas") if ks.get("pas") is not None else 0.03, f"Kesit {kesit_ad!r}: pas (paspayı, m)", pozitif=True, sifir_olur=False)
    return {"sistem": "betonarme", "b": ks["b"], "h": ks["h"], "beton": m["kutuphane"], "donati": donati,
            "donati_varsayim": donati_varsayim, "pas": pas, "d_ust": pas + _PAS_EK, "malzeme_ad": ks["malzeme"], "ham": ham}


_KAYNAK_KISA = {   # yanıt boyutu: uzun kaynak metinlerinin kısa biçimi (tam metin elemanın ayrıntı anlatımında)
    "Öğretici yaklaşım (Bresler": "Öğretici yaklaşım (Bresler ters yük / doğrusal moment toplamı); TS 500 iki eksenli etkileşim formülü vermez",
}


def _kontrol_kaydi(x, kombinasyon=None, ad=None, etiket=None, kosul=False):
    """tasarim.py kontrol satırı → §11 satırı (sayılar 5 anlamlı basamak). ``kosul``: yönetmelik alt/üst sınır koşulu (en az
    donatı, boyut, aralık, narinlik…) — elemanın D/C'sini yalnız sağlanmadığında belirler (sınırda D/C = 1 bilgi taşımaz).
    _etiket / _kosul belirleyen için, yanıttan silinir."""
    kaynak = x["kaynak"]
    for on, kisa in _KAYNAK_KISA.items():
        if kaynak.startswith(on):
            kaynak = kisa
    return {"ad": ad or x["ad"], "talep": _r5(x["talep"]), "kapasite": _r5(x["kapasite"]), "dc": _r5(min(float(x["dc"]), 99.0)),
            "birim": x.get("birim", ""), "kaynak": kaynak, "saglandi": bool(x["saglandi"]), "kombinasyon": kombinasyon,
            "kosul": bool(kosul), "_etiket": etiket or (ad or x["ad"])}


def _yeni_kontrol(ad, talep, kapasite, kaynak, birim, kombinasyon=None, etiket=None, kosul=False):
    dc = 99.0 if kapasite <= 0 else min(max(talep / kapasite, 0.0), 99.0)
    return _kontrol_kaydi({"ad": ad, "talep": talep, "kapasite": kapasite, "dc": dc, "birim": birim, "kaynak": kaynak,
                           "saglandi": dc <= 1.0 + 1e-9}, kombinasyon, etiket=etiket, kosul=kosul)


def _kiris_kuvvetleri(T, kir):
    """Bina kirişinin FE parçaları, dayanım/deprem kombinasyonları: mesnet (parça uçlarında en büyük −M, üst donatı), açıklık
    (en büyük +M, alt donatı), en büyük |V|; her biri [değer, kombinasyon, yer]. M işareti motor kuralı: alt lif çekme +."""
    mes, acik, kes = [0.0, None, None], [0.0, None, None], [0.0, None, None]
    for p in kir["parcalar"]:
        b = _blok(T, p["eleman"])
        e = T.el[p["eleman"]]
        xs = T.paket.el_x[T.idx[p["eleman"]]]
        M, V = b[:, _I_M, :], b[:, _I_V, :]
        for s, dg in ((0, e["dugumler"][0]), (-1, e["dugumler"][1])):
            i = int(np.argmin(M[:, s]))
            if -M[i, s] > mes[0]:
                mes = [float(-M[i, s]), T.adlar[i], f"{T.dno[dg]['adres']} ucu"]
        i, s = np.unravel_index(int(np.argmax(M)), M.shape)
        if M[i, s] > acik[0]:
            acik = [float(M[i, s]), T.adlar[i], f"{_kenar_adres(T.B, p['key'])}, x = {_f(xs[s])} m"]
        i, s = np.unravel_index(int(np.argmax(np.abs(V))), V.shape)
        if abs(V[i, s]) > kes[0]:
            kes = [float(abs(V[i, s])), T.adlar[i], f"{_kenar_adres(T.B, p['key'])}, x = {_f(xs[s])} m"]
    return {"mesnet": mes, "aciklik": acik, "kesme": kes}


def _kolon_noktalari(T, e):
    """Kolon FE elemanının her kombinasyonda alt (x = 0) ve üst (x = L) ucundaki EŞ ZAMANLI iç kuvvetleri (zarf değil):
    N basınç + (motor N çekme + olduğundan −N), Mx / My bina X / Y eksenleri etrafında. Yerel eksenler (lam: bina
    koordinatında x′, y′, z′ satırları) kullanılır: motor M (z′ etrafında) ve My (y′ etrafında) bina eksenlerine izdüşürülür;
    yon takası (§2) böylece kendiliğinden işlenir (kolonda y′ = −X, z′ = −Y; yalnız büyüklükler kullanılır)."""
    b = _blok(T, e["no"])
    lam = e["lam"]
    out = []
    for i, ad in enumerate(T.adlar):
        for uc, s in (("alt", 0), ("üst", -1)):
            Mz, My = float(b[i, _I_M, s]), float(b[i, _I_MY, s])
            out.append({"ad": f"{ad} ({uc})", "kombinasyon": ad, "uc": uc, "N": -float(b[i, _I_N, s]),
                        "Mx": My * lam[1][0] + Mz * lam[2][0], "My": My * lam[1][1] + Mz * lam[2][1],
                        "deprem": T.deprem[i]})
    return out


def _kayit_kur(tur, kayit, kb, fe, kontroller, durum, ozet):
    """§11 eleman kaydı. D/C = dayanım satırlarının (ve sağlanmayan koşul satırlarının) en büyüğü; satırlar önce dayanım,
    sonra koşullar (sağlanmayanlar önce, D/C azalan; sağlanan koşullardan yalnız en büyük D/C’li olanı — yanıt boyutu), en çok _KONTROL_EN_FAZLA.
    ``kosul`` alanı yalnız koşul satırlarında yazılır (true)."""
    etkin = [x for x in kontroller if not x["kosul"] or not x["saglandi"]] or kontroller
    en = max(etkin, key=lambda x: x["dc"])
    dc = en["dc"]
    kosul = sorted((x for x in kontroller if x["kosul"]), key=lambda x: (x["saglandi"], -x["dc"]))
    kota = 1 + sum(1 for x in kosul if not x["saglandi"])
    kontroller = [x for x in kontroller if not x["kosul"]] + kosul[:kota]
    if dc > 1.0 + 1e-9 and durum == "yeterli":
        durum = "donatı artır" if kb["sistem"] == "betonarme" else "kesit büyüt"
    return {"no": kayit["no"], "tur": tur, "kat": kayit["kat"], "adres": kayit["adres"], "kesit": kayit["kesit"],
            "malzeme": kb["malzeme_ad"], "sistem": kb["sistem"], "fe_elemanlar": fe, "dc": dc, "durum": durum,
            "belirleyen": {"kontrol": en["_etiket"], "kombinasyon": en["kombinasyon"]},
            "kontroller": [{a: v for a, v in x.items() if a[0] != "_" and (a != "kosul" or v)} for x in kontroller[:_KONTROL_EN_FAZLA]],
            "ozet": {a: (_r5(v) if isinstance(v, float) else v) for a, v in ozet.items()}}


def _kiris_ba(ts, T, kir, kb, anl=None):
    kv = _kiris_kuvvetleri(T, kir)
    mes, acik, kes = kv["mesnet"], kv["aciklik"], kv["kesme"]
    arg = (kb["b"], kb["h"], kb["d_ust"], kb["beton"], kb["donati"])
    if anl is not None:
        anl.baslik(f"Mesnet kesiti (üst donatı): M_d = {_f(mes[0])} kN·m — {mes[1] or '–'}, {mes[2] or '–'}", 2)
    em = ts.kiris_egilme(mes[0], *arg, anl=anl)
    if anl is not None:
        anl.baslik(f"Açıklık kesiti (alt donatı): M_d = {_f(acik[0])} kN·m — {acik[1] or '–'}, {acik[2] or '–'}", 2)
    ea = ts.kiris_egilme(acik[0], *arg, anl=anl)
    if anl is not None:
        anl.baslik(f"Kesme: V_d = {_f(kes[0])} kN — {kes[1] or '–'}, {kes[2] or '–'}", 2)
    kk = ts.kiris_kesme(kes[0], kb["b"], kb["h"], kb["d_ust"], kb["beton"], kb["donati"], anl=anl)
    ana = [_kontrol_kaydi(em["kontroller"][0], mes[1], "Eğilme (mesnet, üst) Md ≤ Mr", "eğilme (mesnet, üst)"),
           _kontrol_kaydi(ea["kontroller"][0], acik[1], "Eğilme (açıklık, alt) Md ≤ Mr", "eğilme (açıklık, alt)"),
           _kontrol_kaydi(kk["kontroller"][1], kes[1], "Kesme Vd ≤ Vc + Vw", "kesme"),
           _kontrol_kaydi(kk["kontroller"][0], kes[1], "Kesme üst sınırı Vd ≤ 0,22 fcd bw d", "kesme (üst sınır)")]
    diger, gorulen = [], set()
    for on, r, komb, bas in (("mesnet: ", em, mes[1], 1), ("açıklık: ", ea, acik[1], 1), ("kesme: ", kk, kes[1], 2)):
        for x in r["kontroller"][bas:]:
            if x["birim"] == "mm" and "aralığı" not in x["ad"]:      # boyut koşulları iki eğilme kesitinde aynı
                if x["ad"] in gorulen:
                    continue
                gorulen.add(x["ad"])
                diger.append(_kontrol_kaydi(x, None, etiket="boyut", kosul=True))
            else:
                diger.append(_kontrol_kaydi(x, komb, on + x["ad"], kosul=True))
    diger.sort(key=lambda x: (x["saglandi"], -x["dc"]))
    kontroller = ana + diger[:_KONTROL_EN_FAZLA - len(ana)]
    durum = max((em["durum"], ea["durum"], kk["durum"]), key=lambda d: _DURUM_SIRA.get(d, 2))
    o = kk["oneri"]
    ozet = {"As_ust_cm2": em["As_gerekli_cm2"], "As_alt_cm2": ea["As_gerekli_cm2"],
            "oneri_ust": em["oneri"]["metin"] if em.get("oneri") else None, "oneri_alt": ea["oneri"]["metin"] if ea.get("oneri") else None,
            "etriye": f"Φ{o['cap']}/{o['s_mm'] / 10:.0f}" if o else None, "Md_mesnet": mes[0], "Md_aciklik": acik[0], "Vd": kes[0],
            "d_m": kb["h"] - kb["d_ust"], "b": kb["b"], "h": kb["h"]}
    T.sonuclar[("kiris", kir["no"])] = {"egilme_mesnet": em, "egilme_aciklik": ea, "kesme": kk, "kuvvet": kv, "kb": kb}
    uyar = [u for r in (em, ea, kk) for u in r["uyarilar"]]
    return _kayit_kur("kiris", kir, kb, [p["eleman"] for p in kir["parcalar"]], kontroller, durum, ozet), uyar, {}


def _kolon_ba(ts, T, kol, kb, anl=None):
    e = T.el[kol["eleman"]]
    nok = _kolon_noktalari(T, e)
    bX, bY = kol["bX"], kol["bY"]
    Ac = bX * bY
    ham = kb["ham"]
    rho_ver = None
    if ham.get("As") is not None:
        rho_ver = _sayi(ham["As"], f"Kesit {kol['kesit']!r}: As (toplam boyuna donatı, cm²)", pozitif=True, sifir_olur=False) / (Ac * 1e4)
    elif ham.get("donati_orani") is not None:
        rho_ver = _sayi(ham["donati_orani"], f"Kesit {kol['kesit']!r}: donati_orani (ρ = As/Ac)", pozitif=True, sifir_olur=False)
        if rho_ver >= 0.2:
            raise MatrisHatasi(f"Kesit {kol['kesit']!r}: donati_orani = {rho_ver} çok büyük; oran girilir (%1 → 0.01).")
    rho = rho_ver if rho_ver is not None else _RHO_VARSAYILAN

    def kontrol(r, sec=None, anl_=None):
        p_ = nok if sec is None else [nok[i] for i in sec]
        return ts.kolon_kontrol([p["N"] for p in p_], [p["Mx"] for p in p_], [p["My"] for p in p_], bX, bY, r * Ac * 1e4,
                                kb["d_ust"], kb["beton"], kb["donati"], adlar=[p["ad"] for p in p_], tbdy=False, anl=anl_)

    def nokta_dc(r):
        return max(p["dc"] for p in r["noktalar"])

    if anl is not None:
        anl.baslik(f"Kolon kesiti {_f(bX * 100, 1)} × {_f(bY * 100, 1)} cm (X × Y), ρ = {rho:.4f}"
                   + (" (varsayım)" if rho_ver is None else ""), 2)
    r0 = kontrol(rho, anl_=anl)
    sirali = sorted(range(len(nok)), key=lambda i: -r0["noktalar"][i]["dc"])[:10]
    rho_ger = None
    for rr in _RHO_TARAMA:
        if abs(rr - rho) < 1e-12:
            d = nokta_dc(r0)
        else:
            d = nokta_dc(kontrol(rr, sirali))
            if d <= 1.0 + 1e-9 and len(sirali) < len(nok):
                d = nokta_dc(kontrol(rr))
        if d <= 1.0 + 1e-9:
            rho_ger = rr
            break
    i_en = max(range(len(nok)), key=lambda i: r0["noktalar"][i]["dc"])
    en, pn = r0["noktalar"][i_en], nok[i_en]
    kontroller = []
    for x in en["kontroller"]:
        et = "N–M" if ("etkileşim" in x["ad"] or "İki eksenli" in x["ad"]) else ("eksenel (0,9 fcd Ac)" if "0,9" in x["ad"] else x["ad"])
        kontroller.append(_kontrol_kaydi(x, pn["kombinasyon"], f"{x['ad']} — {pn['uc']} uç", et))
    genel = r0["kontroller"][len(en["kontroller"]):]
    for x in genel:
        if "ρ" in x["ad"]:
            kontroller.append(_kontrol_kaydi(x, None, etiket="donatı oranı", kosul=True))
    bm = ts.beton_malzeme(kb["beton"])
    N040 = 0.40 * bm["fck"] * Ac * 1000.0
    N09 = 0.9 * bm["fcd"] * Ac * 1000.0
    dep = [p for p in nok if p["deprem"]]
    if dep:
        pdm = max(dep, key=lambda p: p["N"])
        Ndm, kdm = pdm["N"], pdm["kombinasyon"]
    else:
        gq = _blok(T, e["no"], T.GQ)
        Ndm, kdm = float(max(-gq[_I_N, 0], -gq[_I_N, -1])), "G+Q"
    kontroller.append(_yeni_kontrol("TBDY: kolon en küçük boyutu ≥ 300 mm", 300.0, min(bX, bY) * 1000.0, ts.K_TS500["kolon_boyut_tbdy"],
                                    "mm", etiket="boyut", kosul=True))
    kontroller.append(_yeni_kontrol("TBDY: Ndm ≤ 0,40 fck Ac", max(Ndm, 0.0), N040,
                                    ts.K_TS500["N040"] + ("" if dep else "; deprem durumu yok: Ndm ≈ G + Q (E = 0)"), "kN", kdm,
                                    "TBDY Ndm ≤ 0,40 fck Ac"))
    boyut_eksenel = any(not x["saglandi"] for x in kontroller if x["_etiket"] in ("boyut", "eksenel (0,9 fcd Ac)", "TBDY Ndm ≤ 0,40 fck Ac"))
    dc = max(x["dc"] for x in kontroller)
    if boyut_eksenel or (dc > 1.0 + 1e-9 and rho_ger is None):
        durum = "kesit büyüt"
    elif dc > 1.0 + 1e-9:
        durum = "donatı artır"
    else:
        durum = "yeterli"
    ozet = {"rho": rho, "rho_varsayim": rho_ver is None, "rho_gerekli": rho_ger, "As_toplam_cm2": rho * Ac * 1e4,
            "As_gerekli_cm2": rho_ger * Ac * 1e4 if rho_ger is not None else None,
            "N_max_kN": max(p["N"] for p in nok), "N_min_kN": min(p["N"] for p in nok), "N_sinir_TBDY_kN": N040, "N_sinir_TS500_kN": N09,
            "Ndm_kN": Ndm, "bX": bX, "bY": bY, "yon": kol["yon"]}
    T.sonuclar[("kolon", kol["no"])] = {"kontrol": r0, "noktalar": nok, "kb": kb, "en": i_en, "Ndm": (Ndm, kdm), "rho": rho}
    uyar = list(r0["uyarilar"])
    ek = {"egri_x": [{"N": _r5(p["N_kN"]), "M": _r5(p["M_kNm"])} for p in r0["egri_x"]["noktalar"]],
          "egri_y": [{"N": _r5(p["N_kN"]), "M": _r5(p["M_kNm"])} for p in r0["egri_y"]["noktalar"]],
          "noktalar": [{"ad": p["ad"], "kombinasyon": p["kombinasyon"], "uc": p["uc"], "N": _r5(p["N"]), "Mx": _r5(p["Mx"]),
                        "My": _r5(p["My"]), "dc": _r5(q["dc"])} for p, q in zip(nok, r0["noktalar"])],
          "egri_eksen": {"egri_x": "bina X ekseni etrafında eğilme (derinlik bY, Y yönü boyutu)",
                         "egri_y": "bina Y ekseni etrafında eğilme (derinlik bX, X yönü boyutu)"}}
    return _kayit_kur("kolon", kol, kb, [kol["eleman"]], kontroller, durum, ozet), uyar, ek


def _celik_etiket(ad, dal):
    if ad.startswith("Bileşik"):
        return f"etkileşim {dal}" if dal else "etkileşim"
    for on, et in (("Kesme", "kesme"), ("Eksenel", "eksenel"), ("Güçlü", "eğilme (güçlü eksen)"), ("Zayıf", "eğilme (zayıf eksen)"),
                   ("Narinlik", "narinlik")):
        if ad.startswith(on):
            return et
    return ad


def _dc_dayanim(r):
    """Çelik tahkikinde kombinasyonların en büyük dayanım D/C'si (narinlik gibi koşul satırları hariç)."""
    return max((c["dc"] for c in r["kombinasyonlar"]), default=0.0)


def _celik(ts, T, tur, kayit, kb, anl=None):
    """ÇYTHYE çelik eleman: kombinasyon başına (N basınç +, güçlü eksen Mx, zayıf eksen My, güçlü eksen V) — her biri o
    kombinasyonda eleman boyunca en büyük mutlak değer (aynı kombinasyon: eş zamanlı yük durumu)."""
    if tur == "kiris":
        fe = [p["eleman"] for p in kayit["parcalar"]]
        L = max(p["L"] for p in kayit["parcalar"])
        tutulu = T.B.analiz["celik_Lb"] == "otomatik" and kayit["no"] in T.dosemeli
        Lb = 0.0 if tutulu else L
        ig, iz, iv = _I_M, _I_MY, _I_V
    else:
        fe = [kayit["eleman"]]
        L = Lb = kayit["L"]
        tutulu = False
        ig, iz, iv = (_I_M, _I_MY, _I_V) if kayit["yon"] == "x" else (_I_MY, _I_M, _I_VZ)   # §2: yon takası
    bl = [_blok(T, no) for no in fe]
    kuvvetler = []
    for i, ad in enumerate(T.adlar):
        Nv = np.concatenate([-b[i, _I_N, :] for b in bl])
        kuvvetler.append({"ad": ad, "N": float(Nv[int(np.argmax(np.abs(Nv)))]),
                          "Mx": float(max(np.max(np.abs(b[i, ig, :])) for b in bl)),
                          "My": float(max(np.max(np.abs(b[i, iz, :])) for b in bl)),
                          "V": float(max(np.max(np.abs(b[i, iv, :])) for b in bl))})
    yontem = "GKT" if T.B.kombinasyon_kumesi == "cythye_gkt" else "YDKT"

    def kontrol(Lb_, Cb_, kuv, baslik):
        if anl is not None:
            anl.baslik(baslik, 2)
        return ts.celik_eleman_kontrol(kb["profil"], kb["celik"], L=L, Lb=Lb_, K=1.0, kuvvetler=kuv, yontem=yontem, Cb=Cb_, anl=anl)

    def satirlar(r, on=""):
        en_ = max(r["kombinasyonlar"], key=lambda c: c["dc"]) if r["kombinasyonlar"] else None
        out = []
        for x in r["kontroller"]:
            komb, ad = None, x["ad"]
            if en_ and ad.startswith(en_["ad"] + ": "):
                komb, ad = en_["ad"], ad[len(en_["ad"]) + 2:]
            et = _celik_etiket(ad, en_["dal"] if en_ else None)
            narin = ad.startswith("Narinlik")
            out.append(_kontrol_kaydi(x, komb, ad if narin or not on else f"{ad} — {on}", et if narin or not on else f"{et} ({on.split(',')[0]})",
                                      kosul=narin))
        return out, en_

    neg = None
    if tutulu:
        # Döşeme yalnız ÜST başlığı tutar: pozitif momentte (açıklık, üst başlık basınçta) L_b = 0; negatif momentte (mesnet,
        # alt başlık basınçta) alt başlık serbest → L_b = parça açıklığı, C_b moment diyagramından (ÇYTHYE Denk. 9.1)
        kuv_p, kuv_n, cb_aday, Mn_max = [], [], [], 0.0
        for i, k in enumerate(kuvvetler):
            Mp = max(float(np.max(b[i, ig, :])) for b in bl)
            Mn = max(float(np.max(-b[i, ig, :])) for b in bl)
            kuv_p.append(dict(k, Mx=max(Mp, 0.0)))
            kuv_n.append(dict(k, Mx=max(Mn, 0.0)))
            j = max(range(len(bl)), key=lambda j_: float(np.max(-bl[j_][i, ig, :])))
            xs = np.array(T.paket.el_x[T.idx[fe[j]]])
            Mj = bl[j][i, ig, :]
            Lp = xs[-1] - xs[0]
            M_ceyrek = [abs(float(np.interp(xs[0] + f * Lp, xs, Mj))) for f in (0.25, 0.5, 0.75)]
            Mm = float(np.max(np.abs(Mj)))
            if Mn > 1e-9 and Mm > 1e-12:
                cb_aday.append((Mn, ts.cb_katsayisi(Mm, *M_ceyrek), Lp))
            Mn_max = max(Mn_max, Mn)
        if Mn_max > 1e-6:
            etkin = [c for c in cb_aday if c[0] >= 0.1 * Mn_max]           # önemli negatif momentli kombinasyonlar
            Cb_n = min(c[1] for c in etkin)                                   # güvenli taraf: en küçük C_b
            Lb_n = max(c[2] for c in etkin)
            neg = {"Lb": Lb_n, "Cb": Cb_n}
        r_p = kontrol(0.0, 1.0, kuv_p, f"{kb['profil']} {kb['celik']} — pozitif moment (açıklık): üst başlık basınçta, döşeme "
                                       f"yanal tutar → L_b = 0, L = {_f(L)} m, K = 1")
        r_n = None
        if neg:
            r_n = kontrol(neg["Lb"], neg["Cb"], kuv_n, f"{kb['profil']} {kb['celik']} — negatif moment (mesnet): alt başlık basınçta, "
                                                       f"tutulmamış → L_b = {_f(neg['Lb'])} m, C_b = {_f(neg['Cb'], 3)} (diyagramdan)")
        sp_, en_p = satirlar(r_p, "pozitif M, L_b = 0")
        if r_n is not None:
            sn_, en_n = satirlar(r_n, f"negatif M, L_b = {_f(neg['Lb'])} m, C_b = {_f(neg['Cb'], 2)}")
        def en_buyuk(sat):          # öteki bölgenin özeti: en büyük D/C'li dayanım satırı
            return [max((x for x in sat if not x["kosul"]), key=lambda x: x["dc"])]

        if r_n is not None and _dc_dayanim(r_n) > _dc_dayanim(r_p):
            r, en, bolge = r_n, en_n, "negatif"
            kontroller = sn_ + en_buyuk(sp_)
        else:
            r, en, bolge = r_p, en_p, "pozitif"
            kontroller = sp_ + (en_buyuk(sn_) if r_n is not None else [])
    else:
        r = kontrol(Lb, 1.0, kuvvetler, f"{kb['profil']} {kb['celik']}: L = {_f(L)} m, L_b = {_f(Lb)} m, K = 1, C_b = 1")
        kontroller, en = satirlar(r)
        r_p = r_n = None
        bolge = None
    eg, bs, ks = r["egilme"], r["basinc"], r["kesme"]
    eg_p = r_p["egilme"] if r_p is not None else eg
    sinif = r["sinif"]
    ozet = {"sinif": f"eğilme: {sinif.get('egilme', '?')}; basınç: {sinif.get('basinc', '?')}" if isinstance(sinif, dict) else str(sinif),
            "Mn_kNm": eg_p["Mn_kNm"], "Mc_kNm": eg_p["Mc_kNm"], "Pn_kN": bs["Pn_kN"], "Pc_kN": bs["Pc_kN"], "Vn_kN": ks["Vn_kN"],
            "Vc_kN": ks["Vc_kN"], "L_m": L, "Lb_m": Lb, "K": 1.0, "yontem": r["yontem"],
            "N_kN": en["N"] if en else 0.0, "Mx_kNm": en["Mx"] if en else 0.0, "My_kNm": en["My"] if en else 0.0,
            "V_kN": en["V"] if en else 0.0}
    if tutulu:
        ozet.update({"bolge": bolge, "Lb_neg_m": neg["Lb"] if neg else None, "Cb_neg": neg["Cb"] if neg else None,
                     "Mc_neg_kNm": r_n["egilme"]["Mc_kNm"] if r_n is not None else None,
                     "dc_pozitif": _dc_dayanim(r_p), "dc_negatif": _dc_dayanim(r_n) if r_n is not None else None})
    T.sonuclar[(tur, kayit["no"])] = {"celik": r, "kb": kb, "en": en, "Lb_tutulu": tutulu, "celik_poz": r_p, "celik_neg": r_n,
                                      "bolge": bolge}
    uyar = list(r["uyarilar"])
    durum = "yeterli" if max(x["dc"] for x in kontroller if not x["kosul"] or not x["saglandi"]) <= 1.0 + 1e-9 else "kesit büyüt"
    ek = {"kuvvetler": [{a: (_r5(v) if isinstance(v, float) else v) for a, v in k.items()} for k in kuvvetler]}
    return _kayit_kur(tur, kayit, kb, fe, kontroller, durum, ozet), uyar, ek


def _eleman_tasarla(ts, T, tur, kayit, anl=None):
    """Bir bina elemanının (kiriş: bütün FE parçaları; kolon) tahkiki → (§11 kaydı, uyarılar, köprü ayrıntısı ekleri)."""
    kb = _kesit_bilgi(T, kayit["kesit"])
    if kb["sistem"] == "celik":
        return _celik(ts, T, tur, kayit, kb, anl)
    if tur == "kiris":
        return _kiris_ba(ts, T, kayit, kb, anl)
    return _kolon_ba(ts, T, kayit, kb, anl)


def _tasarim_varsayimlari(T, kayitlar):
    B = T.B
    v = []
    ba = [k for k in kayitlar if k["sistem"] == "betonarme"]
    if ba:
        paslar = sorted({_f(T.sonuclar[(k["tur"], k["no"])]["kb"]["pas"] * 1000, 0) for k in ba if (k["tur"], k["no"]) in T.sonuclar})
        v.append(f"Paspayı {'/'.join(paslar) or '30'} mm (kesit kartındaki pas; verilmezse 30 mm); donatı ağırlık merkezi = paspayı "
                 "+ 20 mm (etriye Φ8 + boyuna çubuk yarıçapı) → 30 mm paspayında d′ = 50 mm (kiriş ve kolon).")
        v.append("Kiriş momentleri kolon ekseninde (mesnet yüzüne indirgenmedi), kesme en büyük |V| (yüzden d uzaklığa indirgenmedi): "
                 "güvenli tarafta. Kirişte eksenel kuvvet, zayıf eksen eğilmesi ve burulma ihmal edildi (kesmede Nd = 0).")
        if any(k["tur"] == "kolon" and k["ozet"].get("rho_varsayim") for k in ba):
            v.append("Kolon boyuna donatısı kesitte (donati_orani ya da As, cm²) verilmediyse ρ = %1 (TS 500 md. 7.4.1 / TBDY 2018 "
                     "md. 7.3.2 en az değeri) varsayıldı; dört yüze dağıtılmış 8 çubuk. 'Gerekli ρ' 0,01 → 0,04 aralığında 0,0025 adımla "
                     "taranır (ilk D/C ≤ 1; öneri).")
        if any(k["tur"] == "kolon" for k in ba):
            v.append("Kolon: her dayanım/deprem kombinasyonunun alt ve üst ucundaki eş zamanlı (N, Mx, My) noktaları (zarf değil); en "
                     "küçük dışmerkezlik TS 500 md. 6.3.10; narinlik (ikinci mertebe) moment büyütmesi yapılmadı; iki eksenli eğilme "
                     "öğretici yaklaşımla (Bresler / doğrusal toplam). TBDY Ndm = deprem birleşimlerindeki en büyük N (deprem yoksa G + Q).")
        if any(T.sonuclar.get((k["tur"], k["no"]), {}).get("kb", {}).get("donati_varsayim") for k in ba):
            v.append("Kesitte donatı sınıfı verilmediyse B420C alındı.")
    if any(k["sistem"] == "celik" for k in kayitlar):
        if B.analiz["celik_Lb"] == "otomatik":
            v.append("Çelik: K = 1, kolonda L = kat yüksekliği. Döşemeli kirişte döşeme yalnız ÜST başlığı yanal tutar: pozitif "
                     "moment (açıklık, üst başlık basınçta) L_b = 0 ile; negatif moment (mesnet, ALT başlık basınçta) L_b = parça "
                     "açıklığı ve C_b moment diyagramından (ÇYTHYE Denk. 9.1, çeyrek noktalar; önemli negatif momentli kombinasyonların "
                     "en küçüğü) ile ayrı denetlenir, büyük D/C belirler (analiz.celik_Lb = 'boy': her yerde L_b = L, C_b = 1). "
                     "Döşemesiz kirişte L_b = açıklık, C_b = 1. İkinci mertebe etkiler (B1/B2) yok; kesme güçlü eksende; kombinasyon "
                     "başına N, My, V eleman boyunca en büyük mutlak değerler.")
        else:
            v.append("Çelik: K = 1, kolonda L = kat yüksekliği; kirişte L_b = açıklık (analiz.celik_Lb = 'boy': döşemenin yanal "
                     "tutması hesaba katılmadı), C_b = 1; ikinci mertebe etkiler (B1/B2) yok; kesme güçlü eksende; kombinasyon başına "
                     "N, Mx, My, V eleman boyunca en büyük mutlak değerler.")
    v.append(f"Tahkik kombinasyonları: dayanım ve deprem birleşimleri ({len(T.kombs)} adet); servis (G+Q) ve öteleme denetim birleşimleri "
             "tahkike girmez.")
    return v


def _tasarim(ts, T):
    """§11 veri["tasarim"]: bütün bina kirişleri ve kolonları; D/C dağılımı, kritik elemanlar, varsayımlar, uyarılar."""
    B = T.B
    kayitlar, uyarilar = [], {}
    if T.kombs:
        for tur, liste in (("kiris", sorted(B.kirisler, key=lambda k: k["no"])), ("kolon", sorted(B.kolonlar, key=lambda c: c["no"]))):
            for k in liste:
                try:
                    kayit, uy, _ = _eleman_tasarla(ts, T, tur, k)
                except MatrisHatasi as h:
                    kayit = {"no": k["no"], "tur": tur, "kat": k["kat"], "adres": k["adres"], "kesit": k["kesit"],
                             "malzeme": B.kesitler[k["kesit"]]["malzeme"],
                             "sistem": "celik" if B.kesitler[k["kesit"]]["tip"] == "profil" else "betonarme",
                             "fe_elemanlar": [p["eleman"] for p in k["parcalar"]] if tur == "kiris" else [k["eleman"]],
                             "dc": None, "durum": "hesaplanamadı", "belirleyen": None, "kontroller": [], "ozet": {}, "hata": str(h)}
                    uy = [f"tahkik yapılamadı — {h}"]
                kayitlar.append(kayit)
                for u in uy:
                    uyarilar.setdefault(u, []).append(k["adres"])
    gecerli = [k for k in kayitlar if k["dc"] is not None]
    sirali = sorted(gecerli, key=lambda k: -k["dc"])
    dag = {ad: 0 for ad, _ in _DC_ARALIKLARI}
    for k in gecerli:
        dag[next(ad for ad, ust in _DC_ARALIKLARI if k["dc"] < ust)] += 1
    genel = []
    if any(T.deprem):
        genel.append("Deprem kombinasyonları (TBDY 2018 md. 4.4.4) tahkike girdi; TBDY kapasite tasarımı (güçlü kolon–zayıf kiriş, "
                     "kapasite kesmesi / kesme güvenliği, kolon–kiriş birleşim bölgesi, sünek detaylar) bu araçta yok: sonuçlar ön "
                     "boyutlandırmadır.")
    if not T.kombs:
        genel.append("Uygulanan dayanım kombinasyonu yok (G ve Q durumları gerekir); kesit tahkikleri yapılamadı.")
    tekil = [f"{u} ({', '.join(a[:3])}{f' … +{len(a) - 3} eleman' if len(a) > 3 else ''})" for u, a in uyarilar.items()]
    if len(tekil) > 12:
        tekil = tekil[:12] + [f"… ve {len(tekil) - 12} uyarı daha (her elemanın ayrıntısında)."]
    return {
        "yontem": {"betonarme": "TS 500:2000 (+TBDY 2018 Bölüm 7 boyut ve eksenel kuvvet sınırları)",
                   "celik": f"ÇYTHYE 2018 {'GKT' if B.kombinasyon_kumesi == 'cythye_gkt' else 'YDKT'}"},
        "varsayimlar": _tasarim_varsayimlari(T, gecerli),
        "kombinasyon_sayisi": len(T.adlar),
        "elemanlar": kayitlar,
        "en_buyuk_dc": sirali[0]["dc"] if sirali else 0.0,
        "kritik": [k["no"] for k in sirali[:5]],
        "kritik_elemanlar": [{"tur": k["tur"], "no": k["no"], "adres": k["adres"], "dc": k["dc"], "kontrol": k["belirleyen"]["kontrol"],
                              "kombinasyon": k["belirleyen"]["kombinasyon"]} for k in sirali[:10]],
        "dc_dagilimi": dag,
        "uyarilar": genel + tekil,
    }


def _adim_12(T, tas, anl):
    se._basla(anl, 12, "Kesit tahkikleri: TS 500 / TBDY 2018 betonarme, ÇYTHYE 2018 çelik",
              "Analiz bize her kesitteki iç kuvvetleri verdi; şimdi kesitin bunları taşıyıp taşımadığını soruyoruz. Her dayanım ve "
              "deprem kombinasyonu için talep (Md, Vd, Nd…) kesitin tasarım dayanımıyla karşılaştırılır: D/C = talep / kapasite ≤ 1. "
              "Betonarme kirişte donatı tasarlanır (mesnette üst, açıklıkta alt, kesmede etriye), kolonda kombinasyon noktaları N–M "
              "etkileşim eğrisiyle, çelik elemanda ÇYTHYE bileşik etki denklemleriyle denetlenir.")
    anl.metin(f"**Yöntem:** betonarme {tas['yontem']['betonarme']}; çelik {tas['yontem']['celik']}. "
              f"{tas['kombinasyon_sayisi']} kombinasyon, {len(tas['elemanlar'])} bina elemanı.")
    anl.metin("**Varsayımlar:**\n\n" + "\n".join(f"- {v}" for v in tas["varsayimlar"]))
    dag = tas["dc_dagilimi"]
    anl.metin("**D/C dağılımı** (eleman sayısı):\n\n" + _tablo(["D/C < 0,7", "0,7 – 0,9", "0,9 – 1,0", "> 1,0", "En büyük D/C"],
                                                             [[dag["<0.7"], dag["0.7-0.9"], dag["0.9-1.0"], dag[">1.0"], _f(tas["en_buyuk_dc"], 3)]]))
    gecerli = sorted((k for k in tas["elemanlar"] if k["dc"] is not None), key=lambda k: -k["dc"])
    sat = []
    for k in gecerli[:10]:
        bel = next((x for x in k["kontroller"] if x["dc"] == k["dc"]), k["kontroller"][0] if k["kontroller"] else None)
        kalin = "**" if k["dc"] > 1 else ""
        sat.append([k["adres"], k["kesit"], k["belirleyen"]["kontrol"],
                    f"`{k['belirleyen']['kombinasyon']}`" if k["belirleyen"]["kombinasyon"] else "–",
                    f"{_f(bel['talep'], 4)} {bel['birim']}" if bel else "–", f"{_f(bel['kapasite'], 4)} {bel['birim']}" if bel else "–",
                    kalin + _f(k["dc"], 3) + kalin, k["durum"]])
    if sat:
        anl.metin("**En kritik 10 eleman:**\n\n" + _tablo(["Eleman", "Kesit", "Kontrol", "Kombinasyon", "Talep", "Kapasite", "D/C", "Durum"], sat))
    kiris = next((k for k in gecerli if k["tur"] == "kiris"), None)
    kolon = next((k for k in gecerli if k["tur"] == "kolon"), None)
    if kiris is not None:
        _kisa_hesap(T, kiris, anl)
    if kolon is not None:
        _kisa_hesap(T, kolon, anl)
    for u in tas["uyarilar"][:6]:
        anl.uyari(u)
    anl.metin("Her elemanın ayrıntılı hesabı (malzeme, kesit şeması, formüller, N–M eğrisi ve kombinasyon noktaları) **Bina sayfasında "
              "elemana dokununca** açılır (köprü `bina_eleman_tasarim`).")


def _kisa_hesap(T, k, anl):
    s = T.sonuclar.get((k["tur"], k["no"]))
    if not s:
        return
    if k["sistem"] == "celik":
        r, en = s["celik"], s["en"]
        anl.metin(f"**Kritik {'kiriş' if k['tur'] == 'kiris' else 'kolon'} {k['adres']}** ({r['profil']}, {r['malzeme']['sinif']}, "
                  f"{r['yontem']}), belirleyen `{en['ad'] if en else '–'}`: P_c = {_f(r['basinc']['Pc_kN'], 1)} kN, "
                  f"M_cx = {_f(r['egilme']['Mc_kNm'], 1)} kN·m, M_cy = {_f(r['egilme']['Mcy_kNm'], 1)} kN·m, V_c = {_f(r['kesme']['Vc_kN'], 1)} kN "
                  f"(L_b = {_f(r['Lb_m'])} m).")
        if en:
            et = en["etkilesim"]
            Mc, Mcy = _f(r["egilme"]["Mc_kNm"], 1), _f(r["egilme"]["Mcy_kNm"], 1)
            if et["dal"] == "11.1a":
                anl.mat(rf"\frac{{P_r}}{{P_c}} + \frac{{8}}{{9}}\left(\frac{{M_{{rx}}}}{{M_{{cx}}}} + \frac{{M_{{ry}}}}{{M_{{cy}}}}\right) = "
                        rf"\frac{{{_f(abs(en['N']), 1)}}}{{{_f(en['Pc_kN'], 1)}}} + \frac{{8}}{{9}}\left(\frac{{{_f(en['Mx'], 1)}}}{{{Mc}}}"
                        rf" + \frac{{{_f(en['My'], 1)}}}{{{Mcy}}}\right) = {_f(et['dc'], 3)}\ (11.1a)")
            else:
                anl.mat(rf"\frac{{P_r}}{{2P_c}} + \frac{{M_{{rx}}}}{{M_{{cx}}}} + \frac{{M_{{ry}}}}{{M_{{cy}}}} = "
                        rf"\frac{{{_f(abs(en['N']), 1)}}}{{2\cdot{_f(en['Pc_kN'], 1)}}} + \frac{{{_f(en['Mx'], 1)}}}{{{Mc}}}"
                        rf" + \frac{{{_f(en['My'], 1)}}}{{{Mcy}}} = {_f(et['dc'], 3)}\ (11.1b)")
        return
    if k["tur"] == "kiris":
        em, ea, kk, kv = s["egilme_mesnet"], s["egilme_aciklik"], s["kesme"], s["kuvvet"]
        anl.metin(f"**Kritik kiriş {k['adres']}** ({k['kesit']}: b = {_f(em['b_mm'], 0)} mm, h = {_f(em['h_mm'], 0)} mm, "
                  f"d = {_f(em['d_mm'], 0)} mm; f_cd = {_f(em['fcd'], 2)}, f_yd = {_f(em['fyd'], 2)} MPa):")
        for ad, r, kvv in (("Mesnet (üst)", em, kv["mesnet"]), ("Açıklık (alt)", ea, kv["aciklik"])):
            if r["tek_donatili"] and r["As_gerekli_cm2"] is not None:
                anl.mat(rf"\text{{{ad}: }} M_d = {_f(kvv[0], 1)}\ \text{{kN·m}},\quad "
                        rf"a = d - \sqrt{{d^2 - \frac{{2M_d}}{{0{{,}}85 f_{{cd}} b}}}} = {_f(r['a_mm'], 1)}\ \text{{mm}},\quad "
                        rf"A_s = \max\left(\frac{{0{{,}}85 f_{{cd}} b a}}{{f_{{yd}}}},\ \rho_{{min}} b d\right) = {_f(r['As_gerekli_cm2'], 2)}\ \text{{cm}}^2"
                        rf"\ \Rightarrow\ \text{{{r['oneri']['metin'] if r.get('oneri') else '–'}}}")
            else:
                anl.metin(f"{ad}: M_d = {_f(kvv[0], 1)} kN·m — {'çift donatılı' if r['As_gerekli_cm2'] is not None else 'kesit yetersiz'} "
                          f"({r['durum']}); ayrıntı elemanda.")
            if kvv[1]:
                anl.metin(f"{ad}: belirleyen `{kvv[1]}`, {kvv[2]}.")
        anl.mat(rf"\text{{Kesme: }} V_d = {_f(kv['kesme'][0], 1)}\ \text{{kN}},\quad V_{{cr}} = 0{{,}}65 f_{{ctd}} b_w d = {_f(kk['V_cr_kN'], 1)},\quad "
                rf"V_c = 0{{,}}8V_{{cr}} = {_f(kk['V_c_kN'], 1)},\quad V_{{max}} = 0{{,}}22 f_{{cd}} b_w d = {_f(kk['V_max_kN'], 1)}\ \text{{kN}}"
                rf"\ \Rightarrow\ \text{{{kk['oneri']['metin']}}}")
        return
    r, nok, i = s["kontrol"], s["noktalar"], s["en"]
    p, q = nok[i], r["noktalar"][i]
    anl.metin(f"**Kritik kolon {k['adres']}** ({k['kesit']}: bX × bY = {_f(r['b_mm'], 0)} × {_f(r['h_mm'], 0)} mm, ρ = {s['rho']:.4f}"
              f"{' (varsayım)' if k['ozet'].get('rho_varsayim') else ''}, A_s = {_f(r['As_cm2'], 2)} cm²); belirleyen nokta "
              f"`{p['kombinasyon']}`, {p['uc']} uç (N, Mx, My aynı kombinasyondan):")
    anl.mat(rf"N_d = {_f(p['N'], 1)}\ \text{{kN}},\ M_{{dx}} = {_f(abs(p['Mx']), 1)},\ M_{{dy}} = {_f(abs(p['My']), 1)}\ \text{{kN·m}};\quad "
            rf"e_{{min}} = 15 + 0{{,}}03h \Rightarrow M_x = {_f(q['Mx_tasarim_kNm'], 1)},\ M_y = {_f(q['My_tasarim_kNm'], 1)}\ \text{{kN·m}};\quad "
            rf"\text{{D/C}}_x = {_f(q['dc_x'], 3)},\ \text{{D/C}}_y = {_f(q['dc_y'], 3)}"
            + (rf",\ \text{{D/C}}_{{2\,eksen}} = {_f(q['dc_iki_eksen'], 3)}" if q.get("dc_iki_eksen") is not None else ""))
    rg = k["ozet"].get("rho_gerekli")
    anl.metin(f"Mx bina X ekseni etrafındadır: basınç ve çekme yüzleri ±Y'de, derinlik Y yönü boyutu bY = {_f(r['h_mm'], 0)} mm; "
              f"My için derinlik bX = {_f(r['b_mm'], 0)} mm (kolon yön takası, §2). Gerekli ρ: "
              f"{_f(rg, 4) if rg is not None else '0,04 ile de sağlanmıyor → kesit büyüt'}. "
              f"TBDY: N_dm = {_f(s['Ndm'][0], 1)} kN (`{s['Ndm'][1]}`) ≤ 0,40 f_ck A_c = {_f(k['ozet']['N_sinir_TBDY_kN'], 1)} kN.")


def eleman_tasarim(ic, tur, no, goster=None):
    """Köprü ``bina_eleman_tasarim``: ``bina_coz(...).ic`` paketinden tek bina elemanının (tur = "kiris" | "kolon", bina no'su)
    anlatımlı tahkiki. Dönüş ``mo.Sonuc``: ``.veri`` = §11 eleman kaydı + kolonda ``egri_x``, ``egri_y`` [{N, M}] ve ``noktalar``
    [{ad, kombinasyon, uc, N, Mx, My, dc}], çelikte ``kuvvetler`` (kombinasyon başına N, Mx, My, V), ``uyarilar``; ``.anlatim``
    tasarim.py anlatımı (kesit şeması, formüller, N–M eğrisi)."""
    if not isinstance(ic, dict) or "paket" not in ic:
        raise MatrisHatasi("Önce bina çözülmeli (önbellekte çözüm yok ya da süresi doldu); binayı yeniden çözün.")
    T = ic.get("tasarim")
    ts = _tasarim_modulu()
    if T is None or ts is None:
        raise MatrisHatasi("Kesit tahkik modülü (tasarim.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    tur = str(tur or "").strip().lower()
    if tur not in ("kiris", "kolon"):
        raise MatrisHatasi(f"tur {tur!r} tanımsız; 'kiris' ya da 'kolon' olmalı.")
    no = _tam(no, "eleman no")
    liste = T.B.kirisler if tur == "kiris" else T.B.kolonlar
    kayit = next((k for k in liste if k["no"] == no), None)
    if kayit is None:
        raise MatrisHatasi(f"{'Kiriş' if tur == 'kiris' else 'Kolon'} {no} bu binada yok. Mevcut: "
                           f"{', '.join(str(k['no']) for k in liste[:20])}{'…' if len(liste) > 20 else ''}.")
    if not T.kombs:
        raise MatrisHatasi("Uygulanan dayanım kombinasyonu yok (G ve Q durumları gerekir); kesit tahkiki yapılamaz.")
    anl = mo.Anlatim()
    anl.baslik(f"{kayit['adres']} — {kayit['kesit']}: kesit tahkiki", 2)
    anl.metin(f"Tahkik kombinasyonları ({len(T.adlar)}): " + ", ".join(f"`{a}`" for a in T.adlar[:12])
              + (" …" if len(T.adlar) > 12 else "") + ". Kuvvetler aynı kombinasyondan alınır (eş zamanlı); varsayımlar bina "
              "anlatımının 12. adımında.")
    k, uy, ek = _eleman_tasarla(ts, T, tur, kayit, anl)
    if tur == "kolon" and k["sistem"] == "betonarme":
        s = T.sonuclar[("kolon", no)]
        rg = k["ozet"]["rho_gerekli"]
        anl.metin("Gerekli ρ taraması (0,01 → 0,04, adım 0,0025; ilk D/C ≤ 1): **"
                  + (f"ρ = {rg:.4f}" if rg is not None else "0,04 ile de sağlanmıyor — kesit büyütülmeli")
                  + f"**. TBDY N_dm = {_f(s['Ndm'][0], 1)} kN (`{s['Ndm'][1]}`) ≤ 0,40 f_ck A_c = {_f(k['ozet']['N_sinir_TBDY_kN'], 1)} kN.")
    anl.sonuc(rf"\text{{D/C}}_{{max}} = {_f(k['dc'], 3)}", f"Durum: **{k['durum']}** — belirleyen: {k['belirleyen']['kontrol']}"
              + (f" (`{k['belirleyen']['kombinasyon']}`)" if k["belirleyen"]["kombinasyon"] else ""))
    mo.son_anlatim = anl
    anl.goster(goster)
    s = mo.Sonuc(k["dc"], anl, f"{tur} {no}")
    s.veri = dict(k, **ek, uyarilar=uy)
    return s


# ============================================================================
# Ana işlev ve köprü yardımcıları
# ============================================================================
def _gosterilecek_sec(B, kombinasyonlar, zarf):
    """Tam KISA'sı yazılacak kombinasyonlar: kullanıcı listesi (analiz.gosterilecek) ya da yalnız ilk dayanım satırı (1.4G+1.6Q,
    1.4G …). G+Q servis birleşimi G ve Q durumlarının toplamıdır (arayüz doğrudan toplar); öteki kombinasyonlar (rüzgâr, deprem)
    zarf ve özet tablosunda yaşar, tam dizileri bina_kombinasyon ile tembel alınır (yanıt boyutu)."""
    uyg = [k for k in kombinasyonlar if k["uygulandi"]]
    adlar = {k["ad"] for k in uyg}
    if B.analiz["gosterilecek"] is not None:
        sec = [a for a in B.analiz["gosterilecek"] if a in adlar]
        eksik = [a for a in B.analiz["gosterilecek"] if a not in adlar]
        if eksik:
            B.uyarilar.append("analiz.gosterilecek listesinde uygulanmayan/bilinmeyen kombinasyon: " + ", ".join(eksik))
        return sec
    sec = []
    ilk = next((k["ad"] for k in uyg if k["tur"] == "dayanim"), None)
    if ilk:
        sec.append(ilk)
    return sec


def _cozum_kimligi(B):
    """Çözüm kimliği: bina girdisinin (normalize JSON) SHA-1 özeti; aynı bina aynı kimliği verir (köprü önbelleği anahtarı)."""
    import hashlib
    metin = json.dumps(B.ham, sort_keys=True, ensure_ascii=False, default=str)
    return "bina-" + hashlib.sha1(metin.encode("utf-8")).hexdigest()[:16]


def bina_coz(bina, *, goster=None, anlat=True):
    """Bina modelini (sözlük ya da JSON metni) çözer: yükler (TS 498) → döşeme dağıtımı (TS 500 45°) → cerceve3b ağı →
    G, Q, S, W, E (TBDY 2018 eşdeğer deprem yükü) çözümü (coz_coklu, tek K) → kombinasyon kümesi (TS 500 + TBDY 4.4.4 ya da
    ÇYTHYE YDKT/GKT + TBDY 9.2.5) ve zarf → yük akışı tabloları, korunum, sankey.

    Dönüş ``mo.Sonuc``: ``.deger`` G durumu u vektörü (motor SD sırası), ``.veri`` §4 şeması (bina koordinatında),
    ``.anlatim`` 13 adım (12. adım kesit tahkikleri, ``tasarim.py`` varsa; ``anlat=False`` ise yalnız başlık), ``.python_kodu`` / ``.python_ciktisi`` bağımsız numpy betiği,
    ``.ic`` tembel kombinasyon üretimi için paket (``kombinasyon_kisa``)."""
    B = _bina_oku(bina)
    Y = _yukleri_hazirla(B)
    kutle = dep = None
    if B.deprem:
        kutle = _kat_kutleleri(B, Y, n=B.deprem["n"], kar_payi=yv.TBDY_KUTLE_KATILIM_KULLANIM["kar"] if B.kar else 0.0)
        dep = _deprem_on(B, Y, kutle)
    ag, model = _ag_olustur(B, Y, kutle)
    B.ag = ag
    durumlar, ruzgar, _ = _yuk_durumlari(B, Y, ag, dep)
    if ag.get("model_c") is None:
        kisa_m, yol = _durumlari_coz(B, model, durumlar, ag)
    else:
        # TBDY 4.5.8.3: etkin (çatlamış) rijitlik yalnız deprem birleşimlerinde ve onlara giren yükler altında → iki K:
        # brüt K ile G, Q, S, W (deprem dışı birleşimler, servis, yük akışı); çatlamış K ile deprem birim durumları ve
        # deprem birleşimlerine giren düşey durumların kopyaları G~c, Q~c, S~c. Süperpozisyon her K içinde doğrusaldır.
        brut = {ad: d for ad, d in durumlar.items() if not _birim_mi(ad)}
        catl = {ad: d for ad, d in durumlar.items() if _birim_mi(ad)}
        catl.update({ad + _CATLAMIS_EK: durumlar[ad] for ad in ("G", "Q", "S") if ad in durumlar})
        kisa_m, yol = _durumlari_coz(B, model, brut, ag)
        kisa_c, _ = _durumlari_coz(B, ag["model_c"], catl, ag)
        kisa_m.update(kisa_c)
        yol += " ×2 (brüt K: G, Q, S, W; çatlamış K: deprem durumları ve G~c, Q~c, S~c)"
    durumlar_kisa = {ad: _kisa_bina(k, ag) for ad, k in kisa_m.items()}
    paket = _Paket(durumlar_kisa)
    deprem = _deprem_son(B, ag, dep, paket, durumlar) if dep else None
    for ad in list(paket.durum):          # birim durumlar çıktıya girmez; çatlamış kopyalar yalnız pakette (kombinasyon için)
        if _birim_mi(ad):
            durumlar.pop(ad, None)
            durumlar_kisa.pop(ad, None)
            paket.durum.pop(ad, None)
        elif ad.endswith(_CATLAMIS_EK):
            durumlar_kisa.pop(ad, None)
    for ad in ("EX+", "EX-", "EY+", "EY-", "EZ"):
        if ad in paket.durum:
            durumlar_kisa[ad] = paket.kisa(paket.durum[ad])
    kombinasyonlar = _kombinasyon_listesi(B, set(paket.durum))
    for k in kombinasyonlar:
        k["cozum"] = _cozum_katsayilari(k, paket)
    zarf = _zarf_paket(paket, kombinasyonlar)
    ozetler = {k["ad"]: paket.ozet(paket.birlesim(k["cozum"])) for k in kombinasyonlar if k["uygulandi"]}
    gosterilecek = _gosterilecek_sec(B, kombinasyonlar, zarf)
    komb_kat = {k["ad"]: k["cozum"] for k in kombinasyonlar if k["uygulandi"]}
    sonuclar = {ad: paket.kisa(paket.birlesim(komb_kat[ad])) for ad in gosterilecek}
    akis = _akis(B, Y, ag, durumlar_kisa)
    kimlik = _cozum_kimligi(B)
    veri = _veri_olustur(B, Y, ag, model, durumlar, durumlar_kisa, kombinasyonlar, sonuclar, zarf, akis, yol,
                         deprem=deprem, ruzgar=ruzgar, kutle=kutle, ozetler=ozetler, gosterilecek=gosterilecek, kimlik=kimlik)
    ts = _tasarim_modulu()
    T = tas = None
    if ts is not None:      # Dilim 3: kesit tahkikleri (tasarim.py yoksa alan yazılmaz)
        T = _tasarim_baglam(B, Y, ag, paket, kombinasyonlar)
        tas = _tasarim(ts, T)
        veri["tasarim"] = tas
        veri["ozet"]["en_buyuk_dc"] = tas["en_buyuk_dc"]
    if B.analiz["gosterilecek"] is None and veri["sonuclar"] and len(json.dumps(veri, ensure_ascii=False)) > YANIT_BUTCESI:
        # büyük model: varsayılan tam kombinasyon da yanıta yazılmaz (arayüz bina_kombinasyon ile tembel alır ya da G, Q'dan toplar)
        veri["sonuclar"], veri["gosterilecek"] = {}, []
        veri["ozet"]["gosterilen_sayisi"] = 0
        veri["ozet"]["sonuclar_tembel"] = True
        gosterilecek = []
    ozet = {"gosterilecek": gosterilecek}
    anl = mo.Anlatim()
    kod = cikti = ""
    if anlat:
        _adim_1(B, anl)
        _adim_2(B, Y, anl)
        _adim_3(B, Y, anl)
        _adim_4(B, Y, anl)
        _adim_5(B, ag, anl)
        _adim_6(B, durumlar, Y, ruzgar, anl)
        _adim_7(B, deprem, anl)
        _adim_8(B, ag, durumlar_kisa, Y, yol, anl)
        _adim_9(B, akis, anl)
        _adim_10(B, kombinasyonlar, zarf, ag, ozet, anl)
        _adim_11(B, Y, akis, kombinasyonlar, ozetler, anl)
        if tas is not None:
            _adim_12(T, tas, anl)
        kod, cikti = _adim_13(B, ag, model, durumlar, Y, anl, deprem)
    else:
        anl.baslik(B.baslik, 2)
    sonuc = mo.Sonuc(sp.Matrix(kisa_m["G"]["u"]), anl, "u_G", kod, cikti)
    sonuc.veri = veri
    sonuc.ic = {"kimlik": kimlik, "paket": paket, "kombinasyonlar": komb_kat, "durumlar": set(paket.durum), "tasarim": T,
                # alan.py (ısı haritaları, eleman bilgisi): normalize bina, ağ, motor modeli, yükler, tasarım sonucu, kombinasyon türleri
                "alan": {"B": B, "ag": ag, "model": model, "Y": Y, "tasarim": tas,
                         "komb_tur": {k["ad"]: k["tur"] for k in kombinasyonlar if k["uygulandi"]}}}
    mo.son_anlatim = anl
    anl.goster(goster)
    return sonuc


def kombinasyon_kisa(ic, ad, katsayilar=None):
    """Köprü ``bina_kombinasyon``: ``bina_coz(...).ic`` paketinden tek kombinasyonun (ya da tek yük durumunun) tam KISA'sı
    (diyagram dizileri dahil). ``ad`` uygulanan kombinasyonlarda ya da yük durumlarında yoksa ``katsayilar`` ({durum: γ})
    ile serbest bir birleşim kurulur (yalnız mevcut durumlar)."""
    if not isinstance(ic, dict) or "paket" not in ic:
        raise MatrisHatasi("Önce bina çözülmeli (önbellekte çözüm yok ya da süresi doldu); binayı yeniden çözün.")
    ad = str(ad)
    paket = ic["paket"]
    if ad in ic["kombinasyonlar"]:
        kat = ic["kombinasyonlar"][ad]
    elif ad in paket.durum:
        kat = {ad: 1.0}
    elif isinstance(katsayilar, dict) and katsayilar:
        kat = {}
        for d, g in katsayilar.items():
            if str(d) not in paket.durum:
                raise MatrisHatasi(f"Kombinasyon {ad!r}: {d!r} yük durumu bu çözümde yok. Mevcut durumlar: {', '.join(paket.durum)}.")
            kat[str(d)] = _sayi(g, f"Kombinasyon {ad!r}: {d} katsayısı")
    else:
        raise MatrisHatasi(f"Kombinasyon ya da yük durumu bulunamadı: {ad!r}. Uygulananlardan bazıları: "
                           f"{', '.join(list(ic['kombinasyonlar'])[:8])}…; ya da katsayilar = {{durum: γ}} verin.")
    return _kisa_veri(paket.kisa(paket.birlesim(kat)), u_dahil=False)


# ============================================================================
# Yük yolunu izle: tek nesneden zemine zincir
# ============================================================================
def _durum_deger(veri, durum, al):
    """durum 'G' | 'Q' | 'G+Q' için al(durum_adı) değerlerinin toplamı."""
    if durum == "G+Q":
        return al("G") + al("Q")
    return al(durum)


def yuk_yolu(bina, veri, hedef):
    """Bir döşeme, kiriş ya da kolondan zemine yük zinciri. hedef = {"tur": "doseme"|"kiris"|"kolon", "no": …, "durum": "G"|"Q"|"G+Q"}.
    Dönüş {"adimlar": [{"baslik", "bloklar": [{"tur": "md"|"math", "icerik"}], "vurgu": {"dosemeler", "kirisler", "kolonlar", "temeller"}}]}.
    ``veri`` = ``bina_coz(bina).veri`` (yeniden çözüm yapılmaz)."""
    if not isinstance(veri, dict) or veri.get("tur") != "bina":
        raise MatrisHatasi("yuk_yolu için önce bina_coz çalıştırılmalı; 'veri' bina çözümünün çıktısı olmalı.")
    if not isinstance(hedef, dict):
        raise MatrisHatasi('hedef bir sözlük olmalı: {"tur": "doseme", "no": 1, "durum": "G"}.')
    tur = str(hedef.get("tur", "")).strip().lower()
    durum = str(hedef.get("durum", "G")).strip().upper().replace(" ", "")
    if durum not in ("G", "Q", "G+Q"):
        raise MatrisHatasi(f"durum {durum!r}; 'G', 'Q' ya da 'G+Q' olmalı.")
    no = _tam(hedef.get("no"), "hedef.no")
    B = _bina_oku(bina)
    Y = _yukleri_hazirla(B)
    yk = veri["yukler"]
    adimlar = []
    vurgu = {"dosemeler": [], "kirisler": [], "kolonlar": [], "temeller": []}

    def adim(baslik, bloklar, **v):
        for k in vurgu:
            vurgu[k] = sorted(set(vurgu[k]) | set(v.get(k, [])))
        adimlar.append({"baslik": baslik, "bloklar": bloklar, "vurgu": {k: list(x) for k, x in vurgu.items()}})

    D = lambda a: _durum_deger(veri, durum, a)  # noqa: E731
    kiris_nolar, kolon_adresleri = [], []
    if tur == "doseme":
        d = next((x for x in yk["dosemeler"] if x["no"] == no), None)
        if d is None:
            raise MatrisHatasi(f"Döşeme {no} yok. Tanımlı: {[x['no'] for x in yk['dosemeler']]}.")
        bd = B.doseme_no[no]
        w = D(lambda a: d["g"] if a == "G" else d["q"])
        top = D(lambda a: d["G_toplam"] if a == "G" else d["Q_toplam"])
        vurgu["dosemeler"].append(no)
        adim(f"1. Döşeme D{no}: alan yükü ({durum})",
             [{"tur": "md", "icerik": f"Plak h = {_f(bd['h'] * 100, 0)} cm, kullanım **{bd['kullanim']}**; g = γ·h + g_ek = {_f(d['g_plak'])} + {_f(d['g_ek'])} = "
                                      f"**{_f(d['g'])} kN/m²**, q = **{_f(d['q'])} kN/m²** ({d['q_kaynak']}). Alan {_f(d['alan'])} m²."},
              {"tur": "math", "icerik": rf"W_{{{durum}}} = w\,l_k\,l_u = {_f(w)} \cdot {_f(d['lx'])} \cdot {_f(d['ly'])} = {_f(top)}\ \text{{kN}}"}])
        sat = []
        for p in d["paylar"]:
            pay = D(lambda a, p=p: p["toplam_G"] if a == "G" else p["toplam_Q"])
            tepe = D(lambda a, p=p: p["tepe_g"] if a == "G" else p["tepe_q"])
            sat.append([_KENAR_AD[p["kenar_ad"]], f"K{p['kiris_no']}", p["sekil"], _f(tepe), _f(pay)])
            kiris_nolar.append(p["kiris_no"])
        adim(f"2. Döşemeden kirişlere: 45° kuralı (m = {_f(d['m'], 2)}, {'çift' if d['tip'] == 'cift' else 'tek'} doğrultulu)",
             [{"tur": "math", "icerik": rf"p_{{max}} = \frac{{w\,l_k}}{{2}} = \frac{{{_f(w)} \cdot {_f(d['lx'])}}}{{2}} = {_f(w * d['lx'] / 2)}\ \text{{kN/m}}"},
              {"tur": "md", "icerik": _tablo(["Kenar", "Kiriş", "Şekil", "Tepe (kN/m)", "Pay (kN)"], sat)
                                      + f"\n\nΣ paylar = {_f(sum(float(s[-1]) for s in sat))} kN = W ✓ (korunum)."}], kirisler=kiris_nolar)
    elif tur == "kiris":
        if no not in B.kiris_no:
            raise MatrisHatasi(f"Kiriş {no} yok. Tanımlı: {sorted(B.kiris_no)}.")
        kiris_nolar = [no]
    elif tur == "kolon":
        if no not in B.kolon_no:
            raise MatrisHatasi(f"Kolon {no} yok. Tanımlı: {sorted(B.kolon_no)}.")
    else:
        raise MatrisHatasi(f"hedef.tur {tur!r}; 'doseme', 'kiris' ya da 'kolon' olmalı.")

    kolon_key = {(c["ix"], c["iy"], c["kat"]): c for c in B.kolonlar}
    akis_kol = {k["no"]: k for k in veri["akis"]["kolonlar"]}
    if kiris_nolar:
        kiris_nolar = sorted(set(kiris_nolar))
        vurgu["kirisler"] += kiris_nolar
        bloklar = []
        for kno in kiris_nolar:
            r = next(x for x in yk["kirisler"] if x["no"] == kno)
            k = B.kiris_no[kno]
            top = D(lambda a, r=r: r[a]["toplam_kN"])
            R_el = top / 2.0
            parcalar = next(x for x in veri["bina"]["kirisler"] if x["no"] == kno)["parcalar"]
            e0, e1 = parcalar[0]["eleman"], parcalar[-1]["eleman"]
            V0 = D(lambda a, e0=e0: next(e for e in veri["durumlar"][a]["elemanlar"] if e["no"] == e0)["uc_kuvvetleri"][1])
            V1 = D(lambda a, e1=e1: next(e for e in veri["durumlar"][a]["elemanlar"] if e["no"] == e1)["uc_kuvvetleri"][7])
            dokum = (f"döşeme {_f(D(lambda a, r=r: r[a]['doseme']))} + duvar {_f(r['G']['duvar'] if durum != 'Q' else 0)} + öz "
                     f"{_f(r['G']['oz'] if durum != 'Q' else 0)} + ek {_f(D(lambda a, r=r: r[a]['ek']))}")
            uclar = []
            for uc, V in ((k["bas"], V0), (k["son"], V1)):
                ix, iy = B.ax[uc[0]], B.ay[uc[1]]
                c = kolon_key.get((ix, iy, k["kat"]))
                if c:
                    uclar.append(f"{uc[0]}{uc[1]} → S{c['no']}/k{k['kat']}: **{_f(V)} kN**")
                    kolon_adresleri.append((ix, iy, k["kat"]))
                else:
                    uclar.append(f"{uc[0]}{uc[1]} (kolonsuz düğüm, komşu kirişe) **{_f(V)} kN**")
            bloklar.append({"tur": "md", "icerik": f"**K{kno}** ({k['adres']}, L = {_f(k['L'])} m): toplam {durum} = {dokum} = **{_f(top)} kN**. "
                                                     f"El hesabı R = W/2 = {_f(R_el)} kN; FE uç kesmeleri: " + "; ".join(uclar) + "."})
        bloklar.append({"tur": "math", "icerik": r"R_{el} = \frac{W}{2},\qquad V_{FE} = f_{uç} = (\mathbf{k}\,\mathbf{d} - \mathbf{f}_{eq})_{y'}"})
        bloklar.append({"tur": "md", "icerik": "FE uç kesmeleri, kirişin sürekliliği ve kolon rijitliği nedeniyle basit kiriş tepkisinden sapar; "
                                                 "iki ucun toplamı yine W'dir."})
        adim(f"{len(adimlar) + 1}. Kirişlerden kolonlara", bloklar, kirisler=kiris_nolar)
    if tur == "kolon":
        c = B.kolon_no[no]
        kolon_adresleri = [(c["ix"], c["iy"], c["kat"])]
    diziler = sorted({(ix, iy) for ix, iy, _ in kolon_adresleri})
    kol_nolar, temel_nolar = [], []
    bloklar = []
    for ix, iy in diziler:
        satirlar = []
        for kat in range(B.nk, 0, -1):
            c = kolon_key.get((ix, iy, kat))
            if c is None:
                continue
            a = akis_kol[c["no"]]
            kol_nolar.append(c["no"])
            Nk = D(lambda d_, a=a: a["N_" + d_])
            Nkum = D(lambda d_, a=a: a["N_kum_" + d_])
            Ntr = D(lambda d_, a=a: a["N_trib_" + d_])
            satirlar.append([f"S{c['no']}", kat, _f(Nk), _f(Nkum), _f(Ntr), _f((Nkum - Ntr) / Ntr * 100 if Ntr > 1e-9 else 0.0, 1)])
            if kat == 1:
                temel_nolar.append(c["no"])
        bloklar.append({"tur": "md", "icerik": f"**Kolon dizisi {B.xad[ix]}{B.yad[iy]}** ({durum}, basınç +):\n\n"
                                                 + _tablo(["Kolon", "Kat", "N kat payı", "N kümülatif (FE)", "N yük alanı", "Fark %"], satirlar)})
    if bloklar:
        bloklar.insert(0, {"tur": "math", "icerik": r"N_{k} = N_{k+1} + \sum V_{kiriş\ uçları} + G_{kolon}"})
        adim(f"{len(adimlar) + 1}. Kolonlarda birikim: kat kat aşağı", bloklar, kolonlar=kol_nolar)
    tem = [t for t in veri["akis"]["temeller"] if t["kolon_no"] in temel_nolar]
    if tem:
        sat = []
        for t in tem:
            N = D(lambda d_, t=t: t["N_" + d_])
            sat.append([f"T-{t['aks'][0]}{t['aks'][1]}", f"{_f(t['B'])} × {_f(t['L'])}", _f(N), _f(t["N_temel"]), _f(t["N_servis"]),
                        _f(t["sigma_max"]), _f(t["q_em"]), _f(t["DC"], 2)])
        adim(f"{len(adimlar) + 1}. Temel ve zemin",
             [{"tur": "math", "icerik": r"\sigma = \frac{N}{B\,L} \pm \frac{6M_X}{B\,L^{2}} \pm \frac{6M_Y}{L\,B^{2}} \le q_{em},\qquad N = N_G + N_Q + \gamma_b B L h"},
              {"tur": "md", "icerik": _tablo(["Temel", "B × L (m)", f"N ({durum})", "G_temel", "N servis", "σ_max (servis)", "q_em", "D/C"], sat)}],
             temeller=temel_nolar)
    kor = veri["akis"]["korunum"]
    topl = D(lambda d_: kor[d_]["toplam"])
    taban = D(lambda d_: kor[d_]["kolon_taban"])
    temel = D(lambda d_: kor[d_]["temel"])
    adim(f"{len(adimlar) + 1}. Denge: hiçbir yük kaybolmadı",
         [{"tur": "math", "icerik": rf"\sum W_{{{durum}}} = {_f(topl)}\ \text{{kN}} \quad\Rightarrow\quad \sum N_{{taban}} = {_f(taban)},\quad \sum R_{{temel}} = {_f(temel)}\ \text{{kN}}"},
          {"tur": "md", "icerik": "Bina toplam düşey yükü, kolon tabanlarındaki eksenel kuvvetlerin ve temel tepkilerinin toplamına eşittir (korunum)."}])
    return {"adimlar": adimlar, "hedef": {"tur": tur, "no": no, "durum": durum}}


# ============================================================================
# Kütüphane özeti (köprü için) ve şablonlar
# ============================================================================
def kutuphane():
    """Arayüz için kütüphane özeti: malzemeler, kesit kataloğu, kullanım sınıfları, duvar/kaplama takımları, kombinasyonlar, şablonlar."""
    mal = {}
    for tablo in (yv.BETONLAR, yv.CELIKLER, yv.DONATILAR):
        for ad, k in tablo.items():
            m = _malzeme(ad, {"kutuphane": ad})
            mal[ad] = {"tur": m["tur"], "E_MPa": m["E_MPa"], "G_MPa": m["G_MPa"], "gamma": m["gamma"], "kaynak": k["kaynak"],
                       "dogrulandi": k["dogrulandi"], **{a: k[a] for a in ("fck", "fctk", "Fy", "Fu", "fyk") if a in k}}
    dik = [{"ad": f"S{b}x{h}", "b": b / 100, "h": h / 100, "kullanim": "kolon"} for b, h in ((30, 30), (30, 50), (40, 40), (40, 60), (50, 50), (60, 60))]
    dik += [{"ad": f"K{b}x{h}", "b": b / 100, "h": h / 100, "kullanim": "kiris"} for b, h in ((25, 50), (25, 60), (30, 60), (30, 70), (40, 80))]
    profiller = {on: [ad for ad in yv.PROFILLER if ad.startswith(on)] for on in ("IPE", "HEA", "HEB")}
    return {
        "malzemeler": mal,
        "kesit_katalogu": {"dikdortgen_onerileri": dik, "profiller": profiller, "profil_ozellikleri": yv.kopya(yv.PROFILLER),
                           "profil_birimler": dict(yv.PROFIL_BIRIMLER)},
        "kullanim_siniflari": yv.kopya(yv.TS498_HAREKETLI),
        "duvarlar": yv.kopya(yv.DUVARLAR),
        "kaplamalar": yv.kopya(yv.KAPLAMALAR),
        "birim_agirliklar": yv.kopya(yv.TS498_BIRIM_AGIRLIK),
        "azaltma": yv.kopya(yv.TS498_AZALTMA),
        "kombinasyon_kumeleri": {k: {"ad": v["ad"], "kaynak": v["kaynak"], "liste": [{"ad": s["ad"], "tur": s["tur"], "kaynak": s["kaynak"],
                                                                                        "katsayilar": s["katsayilar"]} for s in v["liste"]]}
                                 for k, v in yv.KOMBINASYONLAR.items()},
        "sablonlar": bina_sablonlar(),
        "deprem": {"zemin_siniflari": yv.kopya(yv.ZEMIN_SINIFLARI), "FS": yv.kopya(yv.TBDY_FS), "F1": yv.kopya(yv.TBDY_F1),
                   "BKS": {str(k): v for k, v in yv.TBDY_BKS_I.items()}, "tasiyici": yv.kopya(yv.TBDY_TASIYICI),
                   "Ct": yv.kopya(yv.TBDY_CT), "n": yv.kopya(yv.TBDY_KUTLE_KATILIM_KULLANIM), "etkin_rijitlik": yv.kopya(yv.TBDY_ETKIN_RIJITLIK),
                   "kurallar": yv.kopya(yv.TBDY_DEPREM_KURALLAR), "uygulanabilirlik": yv.kopya(yv.TBDY_UYGULANABILIRLIK)},
        "kar": {"cizelge3": yv.kopya(yv.TS498_KAR), "mu": yv.kopya(yv.EN1991_KAR_SEKIL), "iller": sorted(yv.TS498_KAR_BOLGE_IL),
                "il_bolge": {il: yv.kar_bolgesi(il) for il in yv.TS498_KAR_BOLGE_IL}, "il_kaynak": yv.kopya(yv.TS498_KAR_BOLGE_KAYNAK)},
        "ruzgar": yv.kopya(yv.TS498_RUZGAR),
        "tasiyici_sistemler": tasiyici_sistemler(),
        "dogrulanmamis": yv.dogrulanmamis_kayitlar(),
        "sinirlar": {"aks": EN_FAZLA_AKS, "kat": EN_FAZLA_KAT, "sd": EN_FAZLA_SD},
    }


def tasiyici_sistemler(hepsi=False):
    """Arayüz listesi (TBDY 2018 Tablo 4.1): [{ad, etiket, kod, R, D, BYS_izin, BYS_min, sistem, kaynak, dogrulandi}].
    ``hepsi=True``: tablonun bütün satırları (varsayılan: yv.TBDY_TASIYICI_ARAYUZ alt kümesi, arayüz sırasıyla)."""
    adlar = list(yv.TBDY_TASIYICI) if hepsi else list(yv.TBDY_TASIYICI_ARAYUZ)
    out = []
    for ad in adlar:
        t = yv.TBDY_TASIYICI[ad]
        bys = "–" if t["BYS_min"] is None else (f"= {t['BYS_min']}" if t["BYS_min"] == 8 else f"≥ {t['BYS_min']}")
        out.append({"ad": ad, "etiket": f"{t['kod']} — {t['tanim']}", "kod": t["kod"], "R": t["R"], "D": t["D"], "BYS_izin": bys,
                    "BYS_min": t["BYS_min"], "sistem": t["grup"], "suneklik": t["suneklik"], "kaynak": t["kaynak"],
                    "dogrulandi": t["dogrulandi"]})
    return out


def _duvar_ata(kiris, dis, cati, duvar, parapet):
    """Şablon duvarı: dış kirişte; ara katta kat yüksekliğinde (kural: alttaki kat yüksekliği − kiriş yüksekliği), çatıda
    yalnız parapet (duvar_h = parapet m; parapet None/0 ise çatıda duvar yok)."""
    if not (dis and duvar):
        kiris["duvar"] = None
    elif cati:
        kiris["duvar"] = duvar if parapet else None
        if parapet:
            kiris["duvar_h"] = parapet
    else:
        kiris["duvar"] = duvar


def _izgara_bina(ad, baslik, aciklama, sistem, x_konum, y_konum, kat_h, nkat, kolon, kiris_x, kiris_y, doseme, duvar_dis,
                 malzemeler, kesitler, duvarlar, kullanim="konut", g_ek=1.5, temel=None, kombinasyon=None, kiris_dis=None,
                 deprem=False, kar=False, ruzgar=False, parapet=1.0, deprem_karti=None):
    xs = [chr(ord("A") + i) for i in range(len(x_konum))]
    ys = [str(j + 1) for j in range(len(y_konum))]
    b = {"tur": "bina", "surum": 1, "baslik": baslik, "aciklama": aciklama, "sistem": sistem,
         "birim": {"kuvvet": "kN", "uzunluk": "m"},
         "akslar": {"x": [{"ad": a, "konum": k} for a, k in zip(xs, x_konum)], "y": [{"ad": a, "konum": k} for a, k in zip(ys, y_konum)]},
         "katlar": [{"no": 0, "ad": "Temel", "kot": 0.0}] + [{"no": k, "ad": ("Çatı" if k == nkat else f"{k}. kat"), "kot": kat_h * k} for k in range(1, nkat + 1)],
         "malzemeler": malzemeler, "kesitler": kesitler, "kolonlar": [], "kirisler": [], "dosemeler": [], "duvarlar": duvarlar,
         "ek_yukler": [],
         "temeller": temel or {"tip": "tekil", "varsayilan": {"B": 1.6, "L": 1.6, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000}, "mesnet": "ankastre", "ozel": []},
         "yuk_durumlari": {"G": {"acik": True}, "Q": {"acik": True}, "S": {"acik": False, "bolge": 3, "rakim": 0, "mu": 0.8},
                           "W": {"acik": False, "C": 1.2}, "E": {"acik": False}},
         "deprem": {"etkin": False, "SS": 1.0, "S1": 0.3, "zemin_sinifi": "ZC", "DD": "DD-2", "BKS": 3,
                    "tasiyici": "betonarme-cerceve-yuksek" if sistem == "betonarme" else "celik-cerceve-yuksek",
                    "periyot": "otomatik", "diyafram": "rijit", "dismerkezlik": 0.05, "dolgu": "bitisik"},
         "kombinasyon_kumesi": kombinasyon or ("ts500" if sistem == "betonarme" else "cythye_ydkt"),
         "analiz": {"catlamis_rijitlik": sistem == "betonarme", "diyagram_nokta": 11}}
    cn = kn = dn = 0
    nx, ny = len(xs), len(ys)
    for k in range(1, nkat + 1):
        for i in range(nx):
            for j in range(ny):
                cn += 1
                b["kolonlar"].append({"no": cn, "aks": [xs[i], ys[j]], "kat": k, "kesit": kolon, "yon": "x" if (i + j) % 2 == 0 else "y"})
        # duvar: ara katların dış kirişlerinde kat yüksekliğinde (h_kat − h_kiriş); çatı kirişinde yalnız parapet (duvar_h)
        cati = k == nkat
        for j in range(ny):
            for i in range(nx - 1):
                kn += 1
                dis = j in (0, ny - 1)
                b["kirisler"].append({"no": kn, "kat": k, "bas": [xs[i], ys[j]], "son": [xs[i + 1], ys[j]],
                                      "kesit": kiris_dis if (dis and kiris_dis) else kiris_x})
                _duvar_ata(b["kirisler"][-1], dis, cati, duvar_dis, parapet)
        for i in range(nx):
            for j in range(ny - 1):
                kn += 1
                dis = i in (0, nx - 1)
                b["kirisler"].append({"no": kn, "kat": k, "bas": [xs[i], ys[j]], "son": [xs[i], ys[j + 1]],
                                      "kesit": kiris_dis if (dis and kiris_dis) else kiris_y})
                _duvar_ata(b["kirisler"][-1], dis, cati, duvar_dis, parapet)
        for i in range(nx - 1):
            for j in range(ny - 1):
                dn += 1
                b["dosemeler"].append({"no": dn, "kat": k, "kose": [[xs[i], ys[j]], [xs[i + 1], ys[j + 1]]], "h": doseme,
                                       "kullanim": "cati-gezilen" if (k == nkat and sistem == "betonarme" and nkat > 1) else kullanim,
                                       "g_ek": g_ek, "q": None, "dagitim": "otomatik"})
    if deprem_karti:
        b["deprem"].update(deprem_karti)
    if deprem:
        b["deprem"]["etkin"] = True
        b["yuk_durumlari"]["E"]["acik"] = True
    if kar:
        b["yuk_durumlari"]["S"]["acik"] = True
    if ruzgar:
        b["yuk_durumlari"]["W"]["acik"] = True
    b["sablon"] = ad
    return b


_BA_MAL = {"C30": {"kutuphane": "C30/37"}, "B420C": {"kutuphane": "B420C"}}
_BA_DUVAR = {"tugla19": {"kutuphane": "tugla-delikli-19"}}
BINA_SABLONLARI = {
    "betonarme-tek-aciklik": _izgara_bina(
        "betonarme-tek-aciklik", "Tek açıklıklı betonarme çerçeve (1×1 aks, 1 kat)",
        "5 × 4 m planlı, 3 m yüksekliğinde dört kolonlu tek katlı betonarme çerçeve; 12 cm döşeme, konut yükü. "
        "Yük akışının en küçük örneği: bir döşeme, dört kiriş, dört kolon, dört temel. Tek katta zemin kat duvarları temele oturur; çatı kirişlerinde yalnız 1 m parapet.",
        "betonarme", [0.0, 5.0], [0.0, 4.0], 3.0, 1, "S30x30", "K25x50", "K25x50", 0.12, "tugla19",
        _BA_MAL, {"S30x30": {"tip": "dikdortgen", "b": 0.30, "h": 0.30, "malzeme": "C30", "donati": "B420C", "pas": 0.03},
                  "K25x50": {"tip": "dikdortgen", "b": 0.25, "h": 0.50, "malzeme": "C30", "donati": "B420C", "pas": 0.03}}, _BA_DUVAR),
    "betonarme-2kat-3x2": _izgara_bina(
        "betonarme-2kat-3x2", "2 katlı betonarme konut (3×2 aks)",
        "Akslar A–B–C (0, 5, 9 m) ve 1–2 (0, 4 m); iki kat (3 m); 40×40 kolonlar, 25×50 kirişler, 14 cm döşeme; dış kirişlerde "
        "19 cm delikli tuğla duvar (çatıda 1 m parapet). Varsayılan örnek: çift doğrultulu (m = 1,25) ve 4×5 panellerle üçgen/trapez dağılım.",
        "betonarme", [0.0, 5.0, 9.0], [0.0, 4.0], 3.0, 2, "S40x40", "K25x50", "K25x50", 0.14, "tugla19",
        _BA_MAL, {"S40x40": {"tip": "dikdortgen", "b": 0.40, "h": 0.40, "malzeme": "C30", "donati": "B420C", "pas": 0.03},
                  "K25x50": {"tip": "dikdortgen", "b": 0.25, "h": 0.50, "malzeme": "C30", "donati": "B420C", "pas": 0.03}}, _BA_DUVAR,
        temel={"tip": "tekil", "varsayilan": {"B": 1.6, "L": 1.6, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000}, "mesnet": "ankastre",
               "ozel": [{"aks": ["B", "1"], "B": 2.0, "L": 2.0}, {"aks": ["B", "2"], "B": 2.0, "L": 2.0}]}),
    "betonarme-3kat-3x3": _izgara_bina(
        "betonarme-3kat-3x3", "3 katlı betonarme büro (3×3 aks)",
        "5 + 5 m ve 4 + 4 m aks aralıkları, üç kat (3,2 m); 45×45 kolonlar, 25×55 kirişler, 15 cm döşeme, ofis yükü (2 kN/m²); "
        "iç kolonların yük alanı dört panelin çeyreğidir. Deprem (TBDY 2018: S_S = 1,0, S_1 = 0,3, DD-3 S_S = 0,4, S_1 = 0,12, ZC, "
        "BKS 3, A11; çatlamış kesit rijitliği Tablo 4.2), kar (bölge 3) ve rüzgâr açık; tam TS 500 + TS 498 + TBDY 4.4.4 kombinasyon "
        "kümesi. Dış kirişlerde tuğla duvar, çatıda 1 m parapet. Yönetmeliği sağlar: D/C ≤ 1, λδ/h ≤ 0,008.",
        "betonarme", [0.0, 5.0, 10.0], [0.0, 4.0, 8.0], 3.2, 3, "S45x45", "K25x55", "K25x55", 0.15, "tugla19",
        _BA_MAL, {"S45x45": {"tip": "dikdortgen", "b": 0.45, "h": 0.45, "malzeme": "C30", "donati": "B420C", "pas": 0.03},
                  "K25x55": {"tip": "dikdortgen", "b": 0.25, "h": 0.55, "malzeme": "C30", "donati": "B420C", "pas": 0.03}}, _BA_DUVAR,
        kullanim="ofis", temel={"tip": "tekil", "varsayilan": {"B": 1.8, "L": 1.8, "h": 0.7}, "zemin": {"q_em": 250, "k0": 25000},
                                "mesnet": "ankastre", "ozel": [{"aks": ["B", "2"], "B": 2.4, "L": 2.4}]},
        deprem=True, kar=True, ruzgar=True, deprem_karti={"SS_DD3": 0.4, "S1_DD3": 0.12}),
    "celik-1kat-depo": _izgara_bina(
        "celik-1kat-depo", "Tek katlı çelik depo / atölye (2×1 aks, IPE/HEB)",
        "6 + 6 m × 6 m planlı, 5 m yüksekliğinde çelik çerçeve: HEB 240 kolonlar, IPE 400 ana kirişler (Y), IPE 300 kirişler (X), "
        "12 cm betonarme döşeme, hafif atölye yükü (5 kN/m²); kombinasyonlar ÇYTHYE YDKT (deprem/rüzgâr/kar açılırsa TBDY 9.2.5 satırlarıyla).",
        "celik", [0.0, 6.0, 12.0], [0.0, 6.0], 5.0, 1, "HEB240", "IPE300", "IPE400", 0.12, None,
        {"S275": {"kutuphane": "S275"}, "C30": {"kutuphane": "C30/37"}},
        {"HEB240": {"tip": "profil", "profil": "HEB 240", "malzeme": "S275"}, "IPE300": {"tip": "profil", "profil": "IPE 300", "malzeme": "S275"},
         "IPE400": {"tip": "profil", "profil": "IPE 400", "malzeme": "S275"}}, {},
        kullanim="atolye-hafif", g_ek=1.0,
        temel={"tip": "tekil", "varsayilan": {"B": 1.5, "L": 1.5, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000}, "mesnet": "mafsal", "ozel": []}),
    "betonarme-4kat-4x3": _izgara_bina(
        "betonarme-4kat-4x3", "4 katlı betonarme konut (4×3 aks)",
        "Akslar A–D (4 m aralık) ve 1–3 (5 m aralık), dört kat (3 m); 50×50 kolonlar, 30×60 kirişler, 15 cm döşeme; dış kirişlerde duvar, çatıda 1 m parapet. "
        "60 düğüm, 360 SD: tarayıcıda hâlâ hızlı çözülen büyükçe bir örnek.",
        "betonarme", [0.0, 4.0, 8.0, 12.0], [0.0, 5.0, 10.0], 3.0, 4, "S50x50", "K30x60", "K30x60", 0.15, "tugla19",
        _BA_MAL, {"S50x50": {"tip": "dikdortgen", "b": 0.50, "h": 0.50, "malzeme": "C30", "donati": "B420C", "pas": 0.03},
                  "K30x60": {"tip": "dikdortgen", "b": 0.30, "h": 0.60, "malzeme": "C30", "donati": "B420C", "pas": 0.03}}, _BA_DUVAR,
        temel={"tip": "tekil", "varsayilan": {"B": 2.0, "L": 2.0, "h": 0.8}, "zemin": {"q_em": 250, "k0": 25000}, "mesnet": "ankastre",
               "ozel": [{"aks": ["B", "2"], "B": 2.8, "L": 2.8}, {"aks": ["C", "2"], "B": 2.8, "L": 2.8}]}),
}


def bina_sablonlar():
    """Şablon listesi: [{ad, baslik, sistem, aciklama, kat, aks}]."""
    return [{"ad": ad, "baslik": b["baslik"], "sistem": b["sistem"], "aciklama": b["aciklama"],
             "kat": len(b["katlar"]) - 1, "aks": f"{len(b['akslar']['x'])}×{len(b['akslar']['y'])}"} for ad, b in BINA_SABLONLARI.items()]


def bina_sablon(ad):
    """Şablonun bağımsız kopyası."""
    if ad not in BINA_SABLONLARI:
        raise MatrisHatasi(f"Bina şablonu yok: {ad!r}. Seçenekler: {', '.join(BINA_SABLONLARI)}.")
    return copy.deepcopy(BINA_SABLONLARI[ad])


def dogrulanmamis_kayitlar():
    """yapi_veri.dogrulanmamis_kayitlar() kısayolu."""
    return yv.dogrulanmamis_kayitlar()
