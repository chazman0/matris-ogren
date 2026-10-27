# -*- coding: utf-8 -*-
"""Bina analizi ve yük akışı modülü (Matris Öğren): döşeme → kiriş → kolon → temel → zemin.

Kullanım::

    import yapi
    r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))   # sözlük ya da JSON metni
    r.deger      # G durumu yer değiştirme vektörü (motor SD sırası, sympy Matrix)
    r.veri       # yapılı sonuçlar (aşağıdaki şema; bina koordinatında)
    r.anlatim    # 11 adımlı anlatım (md / math / sema / kod blokları)
    yapi.yuk_yolu(bina, r.veri, {"tur": "doseme", "no": 1, "durum": "G"})   # tek nesneden zemine yük zinciri

Bina veri modeli (``tur: "bina"``, ``surum: 1``; birimler kN, m, kN/m², kN/m³; MPa yalnız malzeme kartında)::

    {"baslik", "sistem": "betonarme" | "celik",
     "akslar": {"x": [{"ad": "A", "konum": 0}, ...], "y": [{"ad": "1", "konum": 0}, ...]},
     "katlar": [{"no": 0, "ad": "Temel", "kot": 0.0}, {"no": 1, "kot": 3.0}, ...],
     "malzemeler": {"C30": {"kutuphane": "C30/37"}, "S275": {"kutuphane": "S275"}},
     "kesitler": {"S40x40": {"tip": "dikdortgen", "b": 0.4, "h": 0.4, "malzeme": "C30"},
                  "IPE300": {"tip": "profil", "profil": "IPE 300", "malzeme": "S275"}},
     "kolonlar": [{"no": 1, "aks": ["A", "1"], "kat": 1, "kesit": "S40x40", "yon": "x"}],
     "kirisler": [{"no": 1, "kat": 1, "bas": ["A", "1"], "son": ["B", "1"], "kesit": "K25x50", "duvar": "tugla19"}],
     "dosemeler": [{"no": 1, "kat": 1, "kose": [["A", "1"], ["B", "2"]], "h": 0.14, "kullanim": "konut",
                    "g_ek": 1.5, "q": null, "dagitim": "otomatik"}],
     "duvarlar": {"tugla19": {"kutuphane": "tugla-delikli-19"}},
     "ek_yukler": [{"tur": "kiris", "kiris": 1, "durum": "G", "q": 2.0},
                   {"tur": "dugum", "aks": ["B", "2"], "kat": 2, "durum": "Q", "FZ": -10},
                   {"tur": "doseme", "doseme": 1, "g": 0.5}],
     "temeller": {"tip": "tekil", "varsayilan": {"B": 1.6, "L": 1.6, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000},
                  "mesnet": "ankastre" | "mafsal" | "elastik", "ozel": [{"aks": ["B", "1"], "B": 2.0, "L": 2.0}]},
     "kombinasyon_kumesi": "ts500" | "cythye_ydkt" | "cythye_gkt",
     "analiz": {"diyagram_nokta": 11}}

Koordinatlar: **bina** sistemi X sağa (harfli akslar), Y plan derinliği (sayılı akslar), Z yukarı (kot). Motor
(``cerceve3b``) Y yukarı çalışır; dönüşüm tek yerdedir: ``_motor_koordinat`` / ``_bina_vek``.
Çıktı şeması ``bina_coz`` belgesinde ve KULLANIM.md 3.9'da anlatılır.
"""
from __future__ import annotations

import copy
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


def _f(x, b=2):
    """Anlatım tablosu sayısı: en çok b ondalık, sondaki sıfırlar atılır."""
    s = f"{float(x):.{b}f}".rstrip("0").rstrip(".")
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
        h_duvar = B.kat[kat]["h"] - ks["h"]
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
    for k, y in enumerate(bina.get("ek_yukler") or [], start=1):
        if not isinstance(y, dict):
            raise MatrisHatasi(f"{k}. ek yük sözlük olmalı.")
        tur = str(y.get("tur", "")).strip().lower()
        durum = str(y.get("durum", "G")).strip().upper()
        if durum not in ("G", "Q"):
            raise MatrisHatasi(f"{k}. ek yük: durum {durum!r}; Dilim 1'de yalnız 'G' ve 'Q' çözülür (S, W, E Dilim 2).")
        if tur == "kiris":
            kno = _tam(y.get("kiris"), f"{k}. ek yük: kiris")
            if kno not in B.kiris_no:
                raise MatrisHatasi(f"{k}. ek yük: kiriş {kno} yok. Tanımlı kirişler: {sorted(B.kiris_no)}.")
            B.ek_yukler.append({"tur": "kiris", "kiris": kno, "durum": durum, "q": _sayi(y.get("q"), f"{k}. ek yük: q (kN/m, aşağı +)")})
        elif tur == "dugum":
            ix, iy = _aks_cifti(y.get("aks"), f"{k}. ek yük", B)
            kat = _tam(y.get("kat", 1), f"{k}. ek yük: kat")
            if not 0 <= kat <= B.nk:
                raise MatrisHatasi(f"{k}. ek yük: kat {kat} yok.")
            bil = {a: _sayi(y.get(a, 0.0), f"{k}. ek yük: {a}") for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}
            B.ek_yukler.append({"tur": "dugum", "aks": [B.xad[ix], B.yad[iy]], "ix": ix, "iy": iy, "kat": kat, "durum": durum, **bil})
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
    # --- deprem (okunur, saklanır; Dilim 1'de hesapta kullanılmaz) ---
    B.deprem = bina.get("deprem") if isinstance(bina.get("deprem"), dict) else None
    B.kombinasyon_kumesi = str(bina.get("kombinasyon_kumesi") or ("ts500" if B.sistem == "betonarme" else "cythye_ydkt")).strip().lower()
    if B.kombinasyon_kumesi not in yv.KOMBINASYONLAR:
        raise MatrisHatasi(f"kombinasyon_kumesi {B.kombinasyon_kumesi!r} tanımsız; seçenekler: {', '.join(yv.KOMBINASYONLAR)}.")
    an = bina.get("analiz") if isinstance(bina.get("analiz"), dict) else {}
    nokta = _tam(an.get("diyagram_nokta", DIYAGRAM_NOKTA), "analiz.diyagram_nokta")
    B.analiz = {"catlamis_rijitlik": bool(an.get("catlamis_rijitlik", False)), "diyagram_nokta": max(3, min(41, nokta))}
    if B.analiz["catlamis_rijitlik"]:
        B.uyarilar.append("analiz.catlamis_rijitlik Dilim 2'de uygulanır; bu çözümde brüt kesit rijitliği kullanıldı.")
    return B


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
    g, q = d["g"], d["q_top"]
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
        birim = _sekil_parcalari(sekil, lx, Le)
        toplam_birim = {"ucgen": lx * lx / 4.0, "trapez": lx / 2.0 * (ly - lx / 2.0), "duzgun": lx / 2.0 * Le, "yok": 0.0}[sekil]
        paylar.append({"kenar_ad": ad, "kenar_aciklama": _KENAR_AD[ad], "key": key, "kiris_no": kir["no"], "parca": parca["parca"],
                       "kenar": kenar, "sekil": sekil, "L": Le, "tepe_g": g * lx / 2.0 if sekil != "yok" else 0.0,
                       "tepe_q": q * lx / 2.0 if sekil != "yok" else 0.0, "q_eM_g": qMg, "q_eV_g": qVg, "q_eM_q": qMq, "q_eV_q": qVq,
                       "toplam_G": g * toplam_birim, "toplam_Q": q * toplam_birim, "parcalar_birim": birim})
    return lx, ly, m, tip, paylar


def _yukleri_hazirla(B):
    """Döşeme g/q, duvar, kiriş ve kolon öz ağırlıkları; döşeme payları; kiriş dökümü; eleman/düğüm yük havuzu (bina koordinatı,
    aşağı pozitif kN/m, tekil yükler bina bileşenleriyle)."""
    Y = SimpleNamespace(dosemeler=[], kirisler=[], kolonlar=[], katlar=[], toplam={"G": 0.0, "Q": 0.0},
                        parca_yuk={}, dugum_yuk={}, kiris_yuk={})
    for d in B.dosemeler:
        d["g_plak"] = GAMMA_BA * d["h"]
        d["g"] = d["g_plak"] + d["g_ek"] + d["ek_g"]
        d["q_top"] = d["q"] + d["ek_q"]
        d["alan"] = d["dx"] * d["dy"]
        lx, ly, m, tip, paylar = _doseme_dagit(B, d)
        d.update({"lx": lx, "ly": ly, "m": m, "tip": tip, "paylar": paylar, "G_toplam": d["g"] * d["alan"], "Q_toplam": d["q_top"] * d["alan"]})
        Y.dosemeler.append(d)
        for p in paylar:
            hav = Y.parca_yuk.setdefault(p["key"], {"G": {"duzgun": 0.0, "parcalar": [], "eV": 0.0, "eM": 0.0, "doseme_kN": 0.0},
                                                      "Q": {"duzgun": 0.0, "parcalar": [], "eV": 0.0, "eM": 0.0, "doseme_kN": 0.0},
                                                      "paylar": []})
            hav["paylar"].append((d["no"], p))
            for durum, tepe, eM, eV, top in (("G", p["tepe_g"], p["q_eM_g"], p["q_eV_g"], p["toplam_G"]),
                                              ("Q", p["tepe_q"], p["q_eM_q"], p["q_eV_q"], p["toplam_Q"])):
                hav[durum]["parcalar"] += [(x1, x2, f1 * tepe, f2 * tepe) for x1, x2, f1, f2 in p["parcalar_birim"]]
                hav[durum]["eM"] += eM
                hav[durum]["eV"] += eV
                hav[durum]["doseme_kN"] += top
    # kiriş dökümü
    ek_kiris = {}
    for y in B.ek_yukler:
        if y["tur"] == "kiris":
            ek_kiris.setdefault(y["kiris"], {"G": 0.0, "Q": 0.0})[y["durum"]] += y["q"]
    for k in B.kirisler:
        oz = k["gamma"] * k["A"]
        duvar = B.duvarlar[k["duvar"]]["deger"] * k["h_duvar"] if k["duvar"] else 0.0
        ekG, ekQ = ek_kiris.get(k["no"], {"G": 0.0, "Q": 0.0}).values()
        dosG = dosQ = eMG = eMQ = 0.0
        for p in k["parcalar"]:
            hav = Y.parca_yuk.get(p["key"])
            if hav:
                dosG += hav["G"]["doseme_kN"]
                dosQ += hav["Q"]["doseme_kN"]
                eMG += hav["G"]["eM"] * p["L"]
                eMQ += hav["Q"]["eM"] * p["L"]
            Y.kiris_yuk[p["key"]] = {"G": {"duzgun": oz + duvar + ekG, "parcalar": hav["G"]["parcalar"] if hav else [],
                                           "eV": hav["G"]["eV"] if hav else 0.0, "eM": hav["G"]["eM"] if hav else 0.0},
                                     "Q": {"duzgun": ekQ, "parcalar": hav["Q"]["parcalar"] if hav else [],
                                           "eV": hav["Q"]["eV"] if hav else 0.0, "eM": hav["Q"]["eM"] if hav else 0.0}}
        L = k["L"]
        G_top = dosG + (duvar + oz + ekG) * L
        Q_top = dosQ + ekQ * L
        qM_G = oz + duvar + ekG + eMG / L
        qM_Q = ekQ + eMQ / L
        Y.kirisler.append({"no": k["no"], "kat": k["kat"], "adres": k["adres"], "L": L,
                           "G": {"doseme": dosG, "duvar": duvar * L, "oz": oz * L, "ek": ekG * L, "toplam_kN": G_top},
                           "Q": {"doseme": dosQ, "ek": ekQ * L, "toplam_kN": Q_top},
                           "kN_m": {"oz": oz, "duvar": duvar, "ek_G": ekG, "ek_Q": ekQ, "q_eM_G": qM_G, "q_eM_Q": qM_Q,
                                    "q_eV_G": G_top / L, "q_eV_Q": Q_top / L},
                           "el_hesabi": {"R_G": G_top / 2.0, "R_Q": Q_top / 2.0, "M_G": qM_G * L * L / 8.0, "M_Q": qM_Q * L * L / 8.0}})
    # kolon öz ağırlığı → üst düğüme tekil (G)
    for c in B.kolonlar:
        W = c["gamma"] * c["A"] * c["L"]
        Y.kolonlar.append({"no": c["no"], "kat": c["kat"], "adres": c["adres"], "oz_kN": W})
        hav = Y.dugum_yuk.setdefault((c["ix"], c["iy"], c["kat"]), {"G": [0.0] * 6, "Q": [0.0] * 6})
        hav["G"][2] -= W
    for y in B.ek_yukler:
        if y["tur"] == "dugum":
            hav = Y.dugum_yuk.setdefault((y["ix"], y["iy"], y["kat"]), {"G": [0.0] * 6, "Q": [0.0] * 6})
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
        Y.katlar.append({"kat": k, "ad": kt["ad"], "kot": kt["kot"], "h": kt["h"], "G": G, "Q": Q, "w": G + Q})
    Y.toplam = {"G": sum(k["G"] for k in Y.katlar), "Q": sum(k["Q"] for k in Y.katlar)}
    Y.kat0 = {"G": sum(-h["G"][2] for key, h in Y.dugum_yuk.items() if key[2] == 0),
              "Q": sum(-h["Q"][2] for key, h in Y.dugum_yuk.items() if key[2] == 0)}
    Y.korunum_parcalari = {
        "G": {"dosemeler": sum(d["G_toplam"] for d in Y.dosemeler),
              "duvarlar": sum(r["G"]["duvar"] for r in Y.kirisler),
              "kiris_oz": sum(r["G"]["oz"] for r in Y.kirisler),
              "kolon_oz": sum(c["oz_kN"] for c in Y.kolonlar),
              "ek": sum(r["G"]["ek"] for r in Y.kirisler) + sum(-h["G"][2] for h in Y.dugum_yuk.values()) - sum(c["oz_kN"] for c in Y.kolonlar)},
        "Q": {"dosemeler": sum(d["Q_toplam"] for d in Y.dosemeler), "duvarlar": 0.0, "kiris_oz": 0.0, "kolon_oz": 0.0,
              "ek": sum(r["Q"]["ek"] for r in Y.kirisler) + sum(-h["Q"][2] for h in Y.dugum_yuk.values())}}
    for durum in ("G", "Q"):
        Y.korunum_parcalari[durum]["toplam"] = sum(Y.korunum_parcalari[durum].values())
    return Y


# ============================================================================
# Ağ (cerceve3b modeli): düğüm = aks kesişimi × kat; kolon alt→üst, kiriş küçük→büyük aks; parçalar ayrı eleman
# ============================================================================
def _dugum_no(kat, ix, iy):
    """Okunur düğüm numarası: 1000·kat + 20·(X aks sırası) + (Y aks sırası) + 1."""
    return 1000 * kat + 20 * ix + iy + 1


def _ag_olustur(B, Y):
    """ag (bina koordinatı, UI için) ve motor modeli (cerceve3b, Y yukarı). Mesnetler temel düğümlerinde."""
    dugum_key = {}
    dugumler = []

    def dugum(ix, iy, kat):
        key = (ix, iy, kat)
        if key not in dugum_key:
            no = _dugum_no(kat, ix, iy)
            dugum_key[key] = no
            dugumler.append({"no": no, "X": B.xk[ix], "Y": B.yk[iy], "Z": B.kat[kat]["kot"],
                             "adres": f"{B.xad[ix]}{B.yad[iy]}/k{kat}", "kat": kat, "aks": [B.xad[ix], B.yad[iy]], "key": key})
        return dugum_key[key]

    elemanlar, model_el = [], []
    eno = 0
    for c in sorted(B.kolonlar, key=lambda c: (c["kat"], c["no"])):
        eno += 1
        i, j = dugum(c["ix"], c["iy"], c["kat"] - 1), dugum(c["ix"], c["iy"], c["kat"])
        c["eleman"] = eno
        elemanlar.append({"no": eno, "dugumler": [i, j], "tur": "kolon", "kaynak_no": c["no"], "parca": 1, "kat": c["kat"],
                          "L": c["L"], "kesit": c["kesit"], "kaynak": {"tur": "kolon", "no": c["no"], "parca": 1},
                          "key": (c["ix"], c["iy"], c["kat"]), "adres": c["adres"]})
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
                              "key": p["key"], "adres": f"{k['adres']} ({_kenar_adres(B, p['key'])})"})
            model_el.append({"no": eno, "dugumler": [a, b], "E": k["E"], "G": k["G"], "A": k["A"], "Iy": k["Iy_m"], "Iz": k["Iz_m"],
                             "J": k["J"], "kaynak": {"tur": "kiris", "no": k["no"], "parca": p["parca"]}})
    n = 6 * len(dugumler)
    if n > EN_FAZLA_SD:
        raise MatrisHatasi(f"Bina ağı {len(dugumler)} düğüm × 6 = {n} serbestlik derecesi; tarayıcıda çözüm için en fazla {EN_FAZLA_SD}. "
                           "Modeli küçültün: aks ya da kat sayısını azaltın, katları birleştirin.")
    # yerel eksen matrisleri (motor kuralı) → bina koordinatına
    model_dg = []
    for dg in dugumler:
        x, y, z = _motor_koordinat(dg["X"], dg["Y"], dg["Z"])
        dg["m"] = (x, y, z)
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
        if dg["kat"] != 0:
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
    ag = {"dugumler": dugumler, "elemanlar": elemanlar, "mesnetler": mesnetler, "sd_sayisi": n, "mod": "sayisal",
          "dugum_key": dugum_key, "dno": dno}
    return ag, model


# ============================================================================
# Yük durumları (G, Q): motor kayıtları — parçalı (hedef yol) ve eşdeğer düzgün (yedek yol)
# ============================================================================
def _yuk_durumlari(B, Y, ag):
    """{durum: {"yukler": [...], "yayili": [...]}} motor koordinatında. yayili: düzgün {"eleman", "q"} ve parçalı
    {"eleman", "q1", "q2", "x1", "x2"} (yerel y′, aşağı negatif). Ayrıca her durum için "yayili_esdeger" (q_eV ile düzgün)."""
    durumlar = {}
    for durum in ("G", "Q"):
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
        durumlar[durum] = {"yukler": yukler, "yayili": yayili, "yayili_esdeger": esdeger}
    return durumlar


# ============================================================================
# Çözüm: se.coz_coklu (K bir kez, iki sağ taraf) → motor KISA → bina koordinatında KISA
# ============================================================================
_DIYAGRAM = ("N", "V", "M", "Vz", "My", "T")


def _durumlari_coz(B, model, durumlar):
    """{durum: KISA_motor}. Hedef yol: coz_coklu + parçalı yük. coz_coklu bulunmayan eski motor kopyasında her durum
    se_coz ile ve eşdeğer düzgün yükle (q_eV; toplam yük korunur) çözülür."""
    nokta = B.analiz["diyagram_nokta"]
    if hasattr(se, "coz_coklu"):
        girdi = {ad: {"yukler": d["yukler"], "yayili": d["yayili"]} for ad, d in durumlar.items()}
        ham = se.coz_coklu(model, girdi, diyagram_nokta=nokta)
        yol = "coz_coklu"
    else:  # pragma: no cover — eski motor
        ham, yol = {}, "se_coz"
        for ad, d in durumlar.items():
            m = dict(model, yukler=d["yukler"], yayili=d["yayili_esdeger"])
            ham[ad] = se.se_coz(m, goster="yok").veri
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
# Kombinasyonlar (doğrusal süperpozisyon) ve zarf
# ============================================================================
def _kisa_birlesim(kisalar, katsayilar):
    """u_komb = Σ γ_i u_i; iç kuvvetler, tepkiler, denge aynı katsayılarla (yeniden çözüm yok)."""
    adlar = [ad for ad in katsayilar if ad in kisalar]
    ilk = kisalar[adlar[0]]
    for ad in adlar[1:]:
        for e0, e1 in zip(ilk["elemanlar"], kisalar[ad]["elemanlar"]):
            if len(e0["x"]) != len(e1["x"]) or any(abs(a - b) > 1e-9 for a, b in zip(e0["x"], e1["x"])):
                raise MatrisHatasi(f"Kombinasyon kurulamadı: eleman {e0['no']} için {adlar[0]} ve {ad} durumlarının diyagram "
                                   "istasyonları farklı; coz_coklu bütün durumları ortak istasyonlarda vermelidir.")

    def top(al):
        return sum(katsayilar[ad] * al(kisalar[ad]) for ad in adlar)

    n = len(ilk["u"])
    u = [top(lambda k, i=i: k["u"][i]) for i in range(n)]
    dugumler = [{"no": dg["no"], **{a: top(lambda k, j=j, a=a: k["dugumler"][j][a]) for a in ("uX", "uY", "uZ", "rX", "rY", "rZ")}}
                for j, dg in enumerate(ilk["dugumler"])]
    tepkiler = [{"dugum": t["dugum"], **{a: top(lambda k, j=j, a=a: k["tepkiler"][j][a]) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}}
                for j, t in enumerate(ilk["tepkiler"])]
    elemanlar = []
    for j, e in enumerate(ilk["elemanlar"]):
        k = {"no": e["no"], "x": list(e["x"]),
             "uc_kuvvetleri": [top(lambda kk, j=j, i=i: kk["elemanlar"][j]["uc_kuvvetleri"][i]) for i in range(12)]}
        for a in _DIYAGRAM:
            k[a] = [top(lambda kk, j=j, a=a, i=i: kk["elemanlar"][j][a][i]) for i in range(len(e["x"]))]
        k["enb"] = _enb(k)
        elemanlar.append(k)
    denge = {a: top(lambda k, a=a: k["denge"][a]) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}
    yaylar = [dict(y, kuvvet=top(lambda k, j=j: k["yaylar"][j]["kuvvet"])) for j, y in enumerate(ilk["yaylar"])]
    return {"u": u, "dugumler": dugumler, "tepkiler": tepkiler, "elemanlar": elemanlar, "denge": denge, "yaylar": yaylar}


def _kombinasyonlar(B, durumlar_kisa):
    """Kümedeki her satır: eldeki durumlarla (G, Q) uygulanabiliyorsa süperpozisyon; değilse uygulandi: false + neden."""
    kume = yv.KOMBINASYONLAR[B.kombinasyon_kumesi]
    liste, sonuclar = [], {}
    for satir in kume["liste"]:
        eksik = [d for d in satir["katsayilar"] if d not in durumlar_kisa]
        kayit = {"ad": satir["ad"], "katsayilar": dict(satir["katsayilar"]), "tur": satir["tur"], "kaynak": satir["kaynak"],
                 "not": satir.get("not", ""), "uygulandi": not eksik}
        if eksik:
            kayit["neden"] = ", ".join(f"{d} ({yv.YUK_DURUMU_ADLARI.get(d, d)})" for d in eksik) + " durumu yok (Dilim 2)"
        else:
            sonuclar[satir["ad"]] = _kisa_birlesim(durumlar_kisa, satir["katsayilar"])
        liste.append(kayit)
    return liste, sonuclar


def _zarf(sonuclar):
    """Uygulanan kombinasyonların her eleman, her istasyon için max/min'i ve belirleyen kombinasyon."""
    adlar = list(sonuclar)
    if not adlar:
        return {"elemanlar": [], "kombinasyonlar": []}
    elemanlar = []
    for j, e in enumerate(sonuclar[adlar[0]]["elemanlar"]):
        k, bel = {"no": e["no"]}, {}
        for a in _DIYAGRAM:
            enb, enk = (-math.inf, None), (math.inf, None)
            for ad in adlar:
                dizi = sonuclar[ad]["elemanlar"][j][a]
                mx, mn = max(dizi), min(dizi)
                if mx > enb[0]:
                    enb = (mx, ad)
                if mn < enk[0]:
                    enk = (mn, ad)
            k[a + "_max"], k[a + "_min"] = enb[0], enk[0]
            bel[a + "_max"], bel[a + "_min"] = enb[1], enk[1]
        k["belirleyen"] = bel
        elemanlar.append(k)
    return {"elemanlar": elemanlar, "kombinasyonlar": adlar}


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
              "Bir binayı SAP2000 gibi bir program da önce tablolarla tanır: aks ızgarası, kat kotları, kolon/kiriş/döşeme "
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
        anl.metin("Deprem parametreleri okundu ve saklandı; eşdeğer deprem yükü Dilim 2'de hesaplanır.")


def _adim_2(B, Y, anl):
    se._basla(anl, 2, "Yükler (TS 498:2021)",
              "Yük akışı, yükün doğduğu yerde başlar: döşeme alan yükleri (sabit g ve hareketli q), duvarların çizgisel yükü, "
              "kirişlerin ve kolonların öz ağırlığı. TS 498:2021 karakteristik değerleri verir; tasarım değeri kombinasyonla "
              "(1,4G + 1,6Q) sonra oluşur.")
    anl.mat(r"g = \gamma_{ba}\,h_{plak} + g_{ek},\qquad q = q_{TS\,498}\ (\text{Çizelge 6}),\qquad "
            r"g_{duvar} = w_{duvar}\,(h_{kat} - h_{kiriş}),\qquad g_{öz} = \gamma\,A")
    if Y.dosemeler:
        anl.metin("**Döşeme yükleri** (kN/m²):\n\n"
                  + _tablo(["Döşeme", "h (cm)", "Plak γ·h", "g_ek", "g toplam", "q", "Alan (m²)", "G (kN)", "Q (kN)", "q kaynağı"],
                           [[f"D{d['no']}", _f(d["h"] * 100, 0), _f(d["g_plak"]), _f(d["g_ek"] + d["ek_g"]), _f(d["g"]), _f(d["q_top"]),
                             _f(d["alan"]), _f(d["G_toplam"]), _f(d["Q_toplam"]), d["q_kaynak"].split("(")[0]] for d in Y.dosemeler]))
    duvarli = [k for k in B.kirisler if k["duvar"]]
    if duvarli:
        anl.metin("**Duvar yükleri** (kiriş üstünde çizgisel):\n\n"
                  + _tablo(["Kiriş", "Duvar", "w (kN/m²)", "h_net (m)", "g_d (kN/m)"],
                           [[f"K{k['no']}", B.duvarlar[k["duvar"]]["aciklama"], _f(B.duvarlar[k["duvar"]]["deger"]), _f(k["h_duvar"]),
                             _f(B.duvarlar[k["duvar"]]["deger"] * k["h_duvar"])] for k in duvarli]))
    anl.metin("**Öz ağırlıklar** (brüt kesit; döşeme kalınlığı kadar üst kısmı döşemede saymak isterseniz A_net = b·(h − t) kullanılır, "
              "burada varsayılan brüttür):\n\n"
              + _tablo(["Eleman", "γ·A (kN/m)", "Toplam (kN)"],
                       [[f"K{r['no']}", _f(r["kN_m"]["oz"]), _f(r["G"]["oz"])] for r in Y.kirisler]
                       + [[f"S{c['no']}/k{c['kat']}", _f(c["oz_kN"] / B.kolon_no[c["no"]]["L"]), _f(c["oz_kN"])] for c in Y.kolonlar]))
    anl.metin("Kolon öz ağırlığı, kolonun üst düğümüne tekil yük olarak verilir (kolon boyunca yayılı olsaydı eksenel kuvvet "
              "alt uca doğru doğrusal artardı; tekil yükte alt kesit aynı toplamı taşır).")
    anl.metin("**Kat toplamları:**\n\n" + _tablo(["Kat", "Kot", "G (kN)", "Q (kN)", "G + Q"],
                                                  [[k["kat"], _f(k["kot"]), _f(k["G"]), _f(k["Q"]), _f(k["w"])] for k in Y.katlar]
                                                  + [["Toplam", "", _f(Y.toplam["G"]), _f(Y.toplam["Q"]), _f(Y.toplam["G"] + Y.toplam["Q"])]]))


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
    katlar = sorted({d["kat"] for d in Y.dosemeler})
    if katlar:
        anl.sema("Kat planları ve döşeme yük şekilleri", [_sema_plan(B, Y, k) for k in katlar])


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


def _adim_6(B, durumlar, anl):
    se._basla(anl, 6, "Yük durumları: G ve Q ayrı ayrı",
              "SAP2000'deki 'load pattern' gibi sabit (G) ve hareketli (Q) yükleri ayrı sağ taraf vektörleri olarak kuruyoruz. "
              "Neden ayrı? Çünkü kombinasyon katsayıları farklıdır (1,4G + 1,6Q) ve doğrusal sistemde sonuçlar sonradan toplanabilir; "
              "bir kez kurulan K ile iki sağ taraf tek çözümde biter.")
    sat = []
    for ad, d in durumlar.items():
        parcali = sum(1 for y in d["yayili"] if "q1" in y)
        duzgun = len(d["yayili"]) - parcali
        topq = -sum((y.get("q") or 0.0) * next(e["L"] for e in B.ag["elemanlar"] if e["no"] == y["eleman"]) for y in d["yayili"] if "q" in y)
        topp = -sum((y["q1"] + y["q2"]) / 2.0 * (y["x2"] - y["x1"]) for y in d["yayili"] if "q1" in y)
        topF = -sum(y.get("Fy", 0.0) for y in d["yukler"])
        sat.append([ad, yv.YUK_DURUMU_ADLARI[ad], duzgun, parcali, len(d["yukler"]), _f(topq + topp + topF)])
    anl.metin(_tablo(["Durum", "Anlam", "Düzgün yayılı kayıt", "Parçalı (üçgen/trapez) kayıt", "Düğüm yükü", "Toplam düşey (kN)"], sat))
    anl.metin("Parçalı kayıt biçimi: `{\"eleman\": no, \"q1\": q(x1), \"q2\": q(x2), \"x1\": 0, \"x2\": L}` (yerel y′, aşağı negatif); "
              "aynı elemana gelen kayıtlar üst üste toplanır.")


def _adim_7(B, ag, durumlar_kisa, Y, yol, anl):
    se._basla(anl, 7, "Çözüm: K u = F, iki sağ taraf",
              "Rijitlik matrisi bir kez kurulur, mesnet satır/sütunları atılır, G ve Q sağ tarafları birlikte çözülür "
              "(u = K_ff⁻¹ F). Sonra her eleman için uç kuvvetleri f = k d − f_eq ve diyagramlar; sağlama olarak denge toplamları.")
    anl.metin(f"Hesap modu: **sayısal** (numpy), {ag['sd_sayisi']} SD; çözüm yolu `{yol}`. Diyagram istasyonu: "
              f"{B.analiz['diyagram_nokta']} nokta (parça sınırları ve V = 0 noktaları eklenir).")
    sat = []
    for ad, k in durumlar_kisa.items():
        uz = max((abs(dg["uZ"]) for dg in k["dugumler"]), default=0.0)
        ux = max((math.hypot(dg["uX"], dg["uY"]) for dg in k["dugumler"]), default=0.0)
        yay = sum(y["kuvvet"] for y in k["yaylar"] if y.get("bilesen") == "Fy")
        sat.append([ad, _f(sum(t["FZ"] for t in k["tepkiler"])), _f(yay), _f(Y.toplam[ad]), f"{k['denge']['FZ']:.1e}", f"{uz * 1000:.2f}", f"{ux * 1000:.2f}"])
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


def _adim_8(B, akis, anl):
    se._basla(anl, 8, "Kirişten kolona, kolondan temele: birikim ve yük alanı karşılaştırması",
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


def _adim_9(B, kombinasyonlar, sonuclar, zarf, ag, anl):
    se._basla(anl, 9, "Kombinasyonlar ve zarf",
              "Doğrusal sistemde u_komb = Σγ_i u_i; iç kuvvetler de aynı katsayılarla toplanır, yeniden çözüm yapılmaz "
              "(SAP2000 de 'combo'ları böyle toplar). Dilim 1'de yalnız düşey yükler var: dayanım için 1,4G + 1,6Q, "
              "kullanılabilirlik için G + Q. Zarf, her kesitte uygulanan kombinasyonların en büyüğü/en küçüğüdür.")
    anl.mat(r"\mathbf{u}_{komb} = \sum_i \gamma_i\,\mathbf{u}_i,\qquad \mathbf{f}_{komb} = \sum_i \gamma_i\,\mathbf{f}_i")
    anl.metin(f"Küme: **{yv.KOMBINASYONLAR[B.kombinasyon_kumesi]['ad']}**\n\n"
              + _tablo(["Kombinasyon", "Tür", "Kaynak", "Durum"],
                       [[k["ad"], k["tur"], k["kaynak"], "uygulandı ✓" if k["uygulandi"] else f"uygulanmadı: {k['neden']}"] for k in kombinasyonlar]))
    el = {e["no"]: e for e in ag["elemanlar"]}
    sat = []
    for z in zarf["elemanlar"][:60]:
        e = el[z["no"]]
        sat.append([z["no"], f"{'S' if e['tur'] == 'kolon' else 'K'}{e['kaynak_no']}", _f(z["N_min"]), _f(z["V_max"]), _f(z["V_min"]),
                    _f(z["M_max"]), _f(z["M_min"]), z["belirleyen"]["M_max"]])
    anl.metin("**Zarf** (N çekme +; M alt lif çekme +; kN, kN·m):\n\n"
              + _tablo(["Eleman", "Kaynak", "N_min", "V_max", "V_min", "M_max", "M_min", "M_max'ı belirleyen"], sat)
              + ("\n\n… (ilk 60 eleman)" if len(zarf["elemanlar"]) > 60 else ""))


def _adim_10(B, Y, akis, sonuclar, anl):
    se._basla(anl, 10, "Denge ve korunum: beş sayı",
              "Yük akışının sağlaması: döşeme + duvar + öz ağırlık toplamı = kirişlere giren = kolon tabanlarındaki ΣN = temel "
              "tepkileri = zemine giden. Beş sayı eşitse hiçbir yük yolda kaybolmamıştır.")
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
    sat = []
    for ad, k in sonuclar.items():
        d = k["denge"]
        sat.append([ad, _f(sum(t["FZ"] for t in k["tepkiler"])), f"{d['FX']:.1e}", f"{d['FY']:.1e}", f"{d['FZ']:.1e}", f"{d['MX']:.1e}", f"{d['MY']:.1e}", f"{d['MZ']:.1e}"])
    anl.metin("**Kombinasyon dengeleri** (kalıntılar ≈ 0):\n\n" + _tablo(["Kombinasyon", "Σ FZ tepki (kN)", "ΣFX", "ΣFY", "ΣFZ", "ΣMX", "ΣMY", "ΣMZ"], sat))


# ============================================================================
# Adım 11: bağımsız numpy betiği (ağ kurma + G çözümü + kolon taban toplamları; sonlu_eleman içe aktarmaz)
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
    idx = {dg["no"]: i for i, dg in enumerate(ag["dugumler"])}
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


def _adim_11(B, ag, model, durumlar, Y, anl):
    se._basla(anl, 11, "Aynı hesap Python'da",
              "Ağ kurma, parçalı yayılı yükün Gauss integrasyonuyla eşdeğer düğüm yüklerine çevrilmesi, birleştirme, çözüm ve "
              "kolon taban kuvvetleri tek bir numpy betiğinde. Betik sonlu_eleman modülünü içe aktarmaz; çıktısı 7. ve 10. "
              "adımdaki G sonuçlarıyla aynı olmalıdır.")
    return mo._python_bolumu(anl, _py_betik(B, ag, model, durumlar["G"], Y))


# ============================================================================
# Çıktı verisi (şema §4) ve ana işlev
# ============================================================================
def _kisa_veri(k, u_dahil=True):
    """KISA → JSON. Kombinasyonlarda ``u`` yazılmaz (None; boyut), ``dugumler`` deforme şekil için kalır."""
    return {"u": [_r(x) for x in k["u"]] if u_dahil else None,
            "dugumler": [{"no": d["no"], **{a: _r(d[a]) for a in ("uX", "uY", "uZ", "rX", "rY", "rZ")}} for d in k["dugumler"]],
            "tepkiler": [{"dugum": t["dugum"], **{a: _r(t[a]) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}} for t in k["tepkiler"]],
            "elemanlar": [{"no": e["no"], "uc_kuvvetleri": [_r(x) for x in e["uc_kuvvetleri"]], "x": [_r(x) for x in e["x"]],
                           **{a: [_r6(x) for x in e[a]] for a in _DIYAGRAM},
                           "enb": {a: _r(v) for a, v in e["enb"].items()}} for e in k["elemanlar"]],
            "denge": {a: _r(v) for a, v in k["denge"].items()},
            "yaylar": [{"dugum": y["dugum"], "sd": y.get("sd"), "bilesen": y.get("bilesen"), "k": _r(y["k"]), "kuvvet": _r(y["kuvvet"])} for y in k["yaylar"]]}


def _veri_olustur(B, Y, ag, model, durumlar, durumlar_kisa, kombinasyonlar, sonuclar, zarf, akis, yol):
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
        "deprem": copy.deepcopy(B.deprem), "kombinasyon_kumesi": B.kombinasyon_kumesi, "analiz": dict(B.analiz),
    }
    kutuphane_ozeti = {
        "malzemeler": {ad: {"E_kNm2": m["E"], "G_kNm2": m["G"], "gamma": m["gamma"], "tur": m["tur"], "kutuphane": m["kutuphane"],
                            **({"fck": m["fck"]} if m["tur"] == "beton" else {}), **({"Fy": m["Fy"]} if m["tur"] == "celik" else {}),
                            **({"fyk": m["fyk"]} if m["tur"] == "donati" else {})} for ad, m in B.malzemeler.items()},
        "kesitler": {ad: {"tip": k["tip"], "b": k["b"], "h": k["h"], "profil": k["profil"], "A": _r(k["A"]), "Iy": _r(k["I_guclu"]),
                          "Iz": _r(k["I_zayif"]), "J": _r(k["J"]), "Wpl": _r(k["Wpl"]), "malzeme": k["malzeme"]} for ad, k in B.kesitler.items()},
    }
    ag_veri = {"dugumler": [{"no": d["no"], "X": d["X"], "Y": d["Y"], "Z": d["Z"], "adres": d["adres"], "kat": d["kat"], "aks": d["aks"]}
                            for d in ag["dugumler"]],
               "elemanlar": [{"no": e["no"], "dugumler": e["dugumler"], "tur": e["tur"], "kaynak_no": e["kaynak_no"], "parca": e["parca"],
                              "kat": e["kat"], "L": _r(e["L"]), "kesit": e["kesit"], "lam": [[_r(x) for x in s] for s in e["lam"]],
                              "adres": e["adres"]} for e in ag["elemanlar"]],
               "mesnetler": [{"dugum": m["dugum"], "tip": m["tip"]} for m in ag["mesnetler"]],
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
                      "kN_m": {a: _r(v) for a, v in r["kN_m"].items()}, "el_hesabi": {a: _r(v) for a, v in r["el_hesabi"].items()}} for r in Y.kirisler],
        "kolonlar": [{"no": c["no"], "kat": c["kat"], "oz_kN": _r(c["oz_kN"])} for c in Y.kolonlar],
        "katlar": [{"kat": k["kat"], "kot": k["kot"], "h": k["h"], "G": _r(k["G"]), "Q": _r(k["Q"]), "w": _r(k["w"])} for k in Y.katlar],
        "toplam": {"G": _r(Y.toplam["G"]), "Q": _r(Y.toplam["Q"])},
    }
    akis_veri = {
        "kolonlar": [{a: (_r(v) if isinstance(v, float) else v) for a, v in k.items()} for k in akis["kolonlar"]],
        "temeller": [{a: (_r(v) if isinstance(v, float) else v) for a, v in t.items()} for t in akis["temeller"]],
        "korunum": {d: {a: _r(v) for a, v in p.items()} for d, p in akis["korunum"].items()},
        "sankey": [dict(s, kN=_r(s["kN"])) for s in akis["sankey"]],
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
    fe_model = copy.deepcopy(model)
    fe_model["yukler"] = copy.deepcopy(durumlar["G"]["yukler"])
    fe_model["yayili"] = copy.deepcopy(durumlar["G"]["yayili"])
    veri = {
        "tur": "bina", "surum": 1, "baslik": B.baslik, "sistem": B.sistem, "birim": dict(B.birim),
        "bina": bina, "kutuphane_ozeti": kutuphane_ozeti, "ag": ag_veri, "yukler": yukler,
        "durumlar": {ad: _kisa_veri(k) for ad, k in durumlar_kisa.items()},
        "kombinasyonlar": kombinasyonlar,
        "sonuclar": {ad: _kisa_veri(k, u_dahil=False) for ad, k in sonuclar.items()},
        "zarf": {"kombinasyonlar": zarf["kombinasyonlar"],
                 "elemanlar": [{a: (_r6(v) if isinstance(v, float) else v) for a, v in z.items()} for z in zarf["elemanlar"]]},
        "akis": akis_veri,
        "ozet": {"sd_sayisi": ag["sd_sayisi"], "dugum": len(ag["dugumler"]), "eleman": len(ag["elemanlar"]),
                 "durum_sayisi": len(durumlar_kisa), "kombinasyon_sayisi": len(sonuclar), "toplam_G": _r(Y.toplam["G"]),
                 "toplam_Q": _r(Y.toplam["Q"]), "en_buyuk_temel_DC": _r(en_dc), "uyarilar": uyarilar},
        "fe_model": fe_model,
    }
    return veri


def bina_coz(bina, *, goster=None, anlat=True):
    """Bina modelini (sözlük ya da JSON metni) çözer: yükler (TS 498) → döşeme dağıtımı (TS 500 45°) → cerceve3b ağı →
    G ve Q çözümü (coz_coklu) → kombinasyonlar ve zarf → yük akışı tabloları, korunum, sankey.

    Dönüş ``mo.Sonuc``: ``.deger`` G durumu u vektörü (motor SD sırası), ``.veri`` §4 şeması (bina koordinatında),
    ``.anlatim`` 11 adım (``anlat=False`` ise yalnız başlık), ``.python_kodu`` / ``.python_ciktisi`` bağımsız numpy betiği."""
    B = _bina_oku(bina)
    Y = _yukleri_hazirla(B)
    ag, model = _ag_olustur(B, Y)
    B.ag = ag
    durumlar = _yuk_durumlari(B, Y, ag)
    kisa_m, yol = _durumlari_coz(B, model, durumlar)
    durumlar_kisa = {ad: _kisa_bina(k, ag) for ad, k in kisa_m.items()}
    kombinasyonlar, sonuclar = _kombinasyonlar(B, durumlar_kisa)
    zarf = _zarf(sonuclar)
    akis = _akis(B, Y, ag, durumlar_kisa)
    anl = mo.Anlatim()
    kod = cikti = ""
    if anlat:
        _adim_1(B, anl)
        _adim_2(B, Y, anl)
        _adim_3(B, Y, anl)
        _adim_4(B, Y, anl)
        _adim_5(B, ag, anl)
        _adim_6(B, durumlar, anl)
        _adim_7(B, ag, durumlar_kisa, Y, yol, anl)
        _adim_8(B, akis, anl)
        _adim_9(B, kombinasyonlar, sonuclar, zarf, ag, anl)
        _adim_10(B, Y, akis, sonuclar, anl)
        kod, cikti = _adim_11(B, ag, model, durumlar, Y, anl)
    else:
        anl.baslik(B.baslik, 2)
    sonuc = mo.Sonuc(sp.Matrix(kisa_m["G"]["u"]), anl, "u_G", kod, cikti)
    sonuc.veri = _veri_olustur(B, Y, ag, model, durumlar, durumlar_kisa, kombinasyonlar, sonuclar, zarf, akis, yol)
    mo.son_anlatim = anl
    anl.goster(goster)
    return sonuc


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
        "dogrulanmamis": yv.dogrulanmamis_kayitlar(),
        "sinirlar": {"aks": EN_FAZLA_AKS, "kat": EN_FAZLA_KAT, "sd": EN_FAZLA_SD},
    }


def _izgara_bina(ad, baslik, aciklama, sistem, x_konum, y_konum, kat_h, nkat, kolon, kiris_x, kiris_y, doseme, duvar_dis,
                 malzemeler, kesitler, duvarlar, kullanim="konut", g_ek=1.5, temel=None, kombinasyon=None, kiris_dis=None):
    xs = [chr(ord("A") + i) for i in range(len(x_konum))]
    ys = [str(j + 1) for j in range(len(y_konum))]
    b = {"tur": "bina", "surum": 1, "baslik": baslik, "aciklama": aciklama, "sistem": sistem,
         "birim": {"kuvvet": "kN", "uzunluk": "m"},
         "akslar": {"x": [{"ad": a, "konum": k} for a, k in zip(xs, x_konum)], "y": [{"ad": a, "konum": k} for a, k in zip(ys, y_konum)]},
         "katlar": [{"no": 0, "ad": "Temel", "kot": 0.0}] + [{"no": k, "ad": ("Çatı" if k == nkat else f"{k}. kat"), "kot": kat_h * k} for k in range(1, nkat + 1)],
         "malzemeler": malzemeler, "kesitler": kesitler, "kolonlar": [], "kirisler": [], "dosemeler": [], "duvarlar": duvarlar,
         "ek_yukler": [],
         "temeller": temel or {"tip": "tekil", "varsayilan": {"B": 1.6, "L": 1.6, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000}, "mesnet": "ankastre", "ozel": []},
         "yuk_durumlari": {"G": {"acik": True}, "Q": {"acik": True}, "S": {"acik": False}, "W": {"acik": False}, "E": {"acik": False}},
         "kombinasyon_kumesi": kombinasyon or ("ts500" if sistem == "betonarme" else "cythye_ydkt"),
         "analiz": {"catlamis_rijitlik": False, "diyagram_nokta": 11}}
    cn = kn = dn = 0
    nx, ny = len(xs), len(ys)
    for k in range(1, nkat + 1):
        for i in range(nx):
            for j in range(ny):
                cn += 1
                b["kolonlar"].append({"no": cn, "aks": [xs[i], ys[j]], "kat": k, "kesit": kolon, "yon": "x" if (i + j) % 2 == 0 else "y"})
        for j in range(ny):
            for i in range(nx - 1):
                kn += 1
                dis = j in (0, ny - 1)
                b["kirisler"].append({"no": kn, "kat": k, "bas": [xs[i], ys[j]], "son": [xs[i + 1], ys[j]],
                                      "kesit": kiris_dis if (dis and kiris_dis) else kiris_x, "duvar": duvar_dis if dis else None})
        for i in range(nx):
            for j in range(ny - 1):
                kn += 1
                dis = i in (0, nx - 1)
                b["kirisler"].append({"no": kn, "kat": k, "bas": [xs[i], ys[j]], "son": [xs[i], ys[j + 1]],
                                      "kesit": kiris_dis if (dis and kiris_dis) else kiris_y, "duvar": duvar_dis if dis else None})
        for i in range(nx - 1):
            for j in range(ny - 1):
                dn += 1
                b["dosemeler"].append({"no": dn, "kat": k, "kose": [[xs[i], ys[j]], [xs[i + 1], ys[j + 1]]], "h": doseme,
                                       "kullanim": "cati-gezilen" if (k == nkat and sistem == "betonarme" and nkat > 1) else kullanim,
                                       "g_ek": g_ek, "q": None, "dagitim": "otomatik"})
    b["sablon"] = ad
    return b


_BA_MAL = {"C30": {"kutuphane": "C30/37"}, "B420C": {"kutuphane": "B420C"}}
_BA_DUVAR = {"tugla19": {"kutuphane": "tugla-delikli-19"}}
BINA_SABLONLARI = {
    "betonarme-tek-aciklik": _izgara_bina(
        "betonarme-tek-aciklik", "Tek açıklıklı betonarme çerçeve (1×1 aks, 1 kat)",
        "5 × 4 m planlı, 3 m yüksekliğinde dört kolonlu tek katlı betonarme çerçeve; 12 cm döşeme, konut yükü. "
        "Yük akışının en küçük örneği: bir döşeme, dört kiriş, dört kolon, dört temel.",
        "betonarme", [0.0, 5.0], [0.0, 4.0], 3.0, 1, "S30x30", "K25x50", "K25x50", 0.12, "tugla19",
        _BA_MAL, {"S30x30": {"tip": "dikdortgen", "b": 0.30, "h": 0.30, "malzeme": "C30", "donati": "B420C", "pas": 0.03},
                  "K25x50": {"tip": "dikdortgen", "b": 0.25, "h": 0.50, "malzeme": "C30", "donati": "B420C", "pas": 0.03}}, _BA_DUVAR),
    "betonarme-2kat-3x2": _izgara_bina(
        "betonarme-2kat-3x2", "2 katlı betonarme konut (3×2 aks)",
        "Akslar A–B–C (0, 5, 9 m) ve 1–2 (0, 4 m); iki kat (3 m); 40×40 kolonlar, 25×50 kirişler, 14 cm döşeme; dış kirişlerde "
        "19 cm delikli tuğla duvar. Varsayılan örnek: çift doğrultulu (m = 1,25) ve 4×5 panellerle üçgen/trapez dağılım.",
        "betonarme", [0.0, 5.0, 9.0], [0.0, 4.0], 3.0, 2, "S40x40", "K25x50", "K25x50", 0.14, "tugla19",
        _BA_MAL, {"S40x40": {"tip": "dikdortgen", "b": 0.40, "h": 0.40, "malzeme": "C30", "donati": "B420C", "pas": 0.03},
                  "K25x50": {"tip": "dikdortgen", "b": 0.25, "h": 0.50, "malzeme": "C30", "donati": "B420C", "pas": 0.03}}, _BA_DUVAR,
        temel={"tip": "tekil", "varsayilan": {"B": 1.6, "L": 1.6, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000}, "mesnet": "ankastre",
               "ozel": [{"aks": ["B", "1"], "B": 2.0, "L": 2.0}, {"aks": ["B", "2"], "B": 2.0, "L": 2.0}]}),
    "betonarme-3kat-3x3": _izgara_bina(
        "betonarme-3kat-3x3", "3 katlı betonarme büro (3×3 aks)",
        "5 + 5 m ve 4 + 4 m aks aralıkları, üç kat (3,2 m); 45×45 kolonlar, 25×55 kirişler, 15 cm döşeme, ofis yükü (2 kN/m²); "
        "iç kolonların yük alanı dört panelin çeyreğidir.",
        "betonarme", [0.0, 5.0, 10.0], [0.0, 4.0, 8.0], 3.2, 3, "S45x45", "K25x55", "K25x55", 0.15, "tugla19",
        _BA_MAL, {"S45x45": {"tip": "dikdortgen", "b": 0.45, "h": 0.45, "malzeme": "C30", "donati": "B420C", "pas": 0.03},
                  "K25x55": {"tip": "dikdortgen", "b": 0.25, "h": 0.55, "malzeme": "C30", "donati": "B420C", "pas": 0.03}}, _BA_DUVAR,
        kullanim="ofis", temel={"tip": "tekil", "varsayilan": {"B": 1.8, "L": 1.8, "h": 0.7}, "zemin": {"q_em": 250, "k0": 25000},
                                "mesnet": "ankastre", "ozel": [{"aks": ["B", "2"], "B": 2.4, "L": 2.4}]}),
    "celik-1kat-depo": _izgara_bina(
        "celik-1kat-depo", "Tek katlı çelik depo / atölye (2×1 aks, IPE/HEB)",
        "6 + 6 m × 6 m planlı, 5 m yüksekliğinde çelik çerçeve: HEB 240 kolonlar, IPE 400 ana kirişler (Y), IPE 300 kirişler (X), "
        "12 cm betonarme döşeme, hafif atölye yükü (5 kN/m²); kombinasyonlar ÇYTHYE YDKT (Dilim 1: 1,4G ve G+Q).",
        "celik", [0.0, 6.0, 12.0], [0.0, 6.0], 5.0, 1, "HEB240", "IPE300", "IPE400", 0.12, None,
        {"S275": {"kutuphane": "S275"}, "C30": {"kutuphane": "C30/37"}},
        {"HEB240": {"tip": "profil", "profil": "HEB 240", "malzeme": "S275"}, "IPE300": {"tip": "profil", "profil": "IPE 300", "malzeme": "S275"},
         "IPE400": {"tip": "profil", "profil": "IPE 400", "malzeme": "S275"}}, {},
        kullanim="atolye-hafif", g_ek=1.0,
        temel={"tip": "tekil", "varsayilan": {"B": 1.5, "L": 1.5, "h": 0.6}, "zemin": {"q_em": 200, "k0": 20000}, "mesnet": "mafsal", "ozel": []}),
    "betonarme-4kat-4x3": _izgara_bina(
        "betonarme-4kat-4x3", "4 katlı betonarme konut (4×3 aks)",
        "Akslar A–D (4 m aralık) ve 1–3 (5 m aralık), dört kat (3 m); 50×50 kolonlar, 30×60 kirişler, 15 cm döşeme; dış duvarlı. "
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
