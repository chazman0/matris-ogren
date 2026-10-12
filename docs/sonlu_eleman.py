# -*- coding: utf-8 -*-
"""Sonlu eleman modülü (Matris Öğren): yay, çubuk, kafes, kiriş ve çerçeve modellerini adım adım çözer.

Kullanım::

    import sonlu_eleman as se
    r = se.se_coz(se.ornek_model("kafes-iki-cubuk"))   # sözlük ya da JSON metni
    r.deger          # u: global yer değiştirme vektörü (sympy Matrix; SD sırasıyla)
    r.veri           # yapılı sonuçlar (aşağıya bakın)
    r.anlatim        # adım adım anlatım (matris_ogren.Anlatim): md / math / sema / kod blokları
    r.python_kodu, r.python_ciktisi

Genel işlevler: ``se_coz(model, *, goster=None)``, ``ornek_model(ad)``, ``ornek_listesi()``,
``ORNEK_MODELLER`` (yalnız sabit değerlerden oluşan sözlük).

Model şeması (sayılar sayı ya da metin olabilir: "200e6", "1/3", "E", "P" ...; koordinatlar sayı olmalıdır)::

    {"tip": "yay" | "cubuk" | "kafes" | "kiris" | "cerceve",
     "baslik": "...", "birim": {"kuvvet": "kN", "uzunluk": "m"},
     "dugumler":  [{"no": 1, "x": 0, "y": 0}],
     "elemanlar": [{"no": 1, "dugumler": [1, 3], "E": "200e6", "A": "0.001", "I": "8e-6", "k": "1000"}],
     "mesnetler": [{"dugum": 1, "ux": true, "uy": true, "rz": false}],
     "yukler":    [{"dugum": 3, "Fx": 0, "Fy": -10, "M": 0}],
     "yayili":    [{"eleman": 1, "q": -12}]}

* Düğüm başına SD: yay/çubuk 1 (u), kafes 2 (u, v), kiriş 2 (v, θ), çerçeve 3 (u, v, θ).
  Global SD numarası, "dugumler" listesindeki sıraya göre verilir: i. sıradaki düğüm
  d·(i-1)+1 … d·i numaralarını alır (SD etiketi u₁, v₁, θ₁ ... düğüm "no" değerini kullanır).
* Gerekli özellikler: yay → k; çubuk, kafes → E, A; kiriş → E, I; çerçeve → E, A, I.
* Yay/çubuk modelinde yalnız x kullanılır (y yoksayılır); kirişte tüm düğümler aynı yatay doğruda olmalıdır.
* Mesnet bayrakları: yay/çubuk ux; kafes ux, uy; kiriş uy (çökme v), rz (dönme θ); çerçeve ux, uy, rz.
  Eksik bayrak = serbest. Yükler: yay/çubuk Fx; kafes Fx, Fy; kiriş Fy, M; çerçeve Fx, Fy, M.
* ``yayili``: eleman yerel y yönünde düzgün yayılı yük q (yerel y = eleman ekseninin 90° saat yönünün tersi;
  kiriş ve çerçeve için; + = yerel y yönü). Yatay, soldan sağa giden elemanda q < 0 aşağı doğrudur.
* Birimler kN ve m'dir (E: kN/m², A: m², I: m⁴). X sağa, Y yukarı, dönme ve moment saat yönünün tersi (+).

Hesap modu: toplam SD ≤ 12 ise "kesin" (sympy, kesirli/sembolik; E, A, P ... harf olabilir),
daha büyükse "sayisal" (numpy, ondalık; harfli girdi öğretici hata verir).

``Sonuc.veri`` sözlüğünün anahtarları (sayılar JSON'a uygun ``float``; sembolik çözümde sayı yerine ifade metni)::

    tip, baslik, birim {"kuvvet", "uzunluk"}, mod ("kesin" | "sayisal"), sd_sayisi, sd_etiketleri [str],
    dugumler  [{no, x, y, sd [global SD numaraları, 1'den], u [bu düğümün yer değiştirmeleri]}],
    elemanlar [{no, dugumler [i, j], L, c, s, uc_kuvvetleri [yerel uç kuvvetleri, SE işaretiyle],
                N (çekme +), durum ("çekme" | "basınç" | "sıfır" | "eğilme"),
                diyagram {x [yerel konum], N, V, M [aynı uzunlukta listeler]}}],
    tepkiler  [{dugum, Fx, Fy, M}],           # yalnız mesnetli düğümler (mesnedin yapıya uyguladığı kuvvet)
    u [n], F [n],                              # global yer değiştirme ve (eşdeğer düğüm yükleriyle) yük vektörü
    denge {Fx, Fy, M},                         # dış kuvvet + tepki toplamı kalıntıları (≈ 0)
    olcek (şekil değiştirmiş biçim çizim ölçeği ya da None), K (n ≤ 40 ise mesnetsiz K, iç içe liste).
"""
from __future__ import annotations

import contextlib
import copy
import html as _html
import io
import json
import math
import re
from types import SimpleNamespace

import sympy as sp

import matris_ogren as mo

try:  # numpy Pyodide ve Colab'da hazırdır; yoksa yalnız kesin mod çalışır
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

__version__ = "0.1.0"

MatrisHatasi = mo.MatrisHatasi
SD_ESIK = 12   # toplam SD bu sayıyı aşarsa hesap sayısal (numpy) yapılır


# ============================================================================
# Örnek modeller (yalnız sabit değerler: ast.literal_eval ile okunabilir)
# ============================================================================
ORNEK_MODELLER = {
    "yay-seri": {
        "tip": "yay",
        "baslik": "Seri bağlı iki yay",
        "aciklama": "Soldaki ucu sabit, seri bağlı iki yayın serbest ucuna 10 kN çekme uygulanır; her yayın uzaması P/k ile bulunur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 1, "y": 0},
            {"no": 3, "x": 2, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "k": "1000"},
            {"no": 2, "dugumler": [2, 3], "k": "2000"},
        ],
        "mesnetler": [{"dugum": 1, "ux": True}],
        "yukler": [{"dugum": 3, "Fx": 10}],
    },
    "cubuk-kademeli": {
        "tip": "cubuk",
        "baslik": "Kademeli kesitli eksenel çubuk",
        "aciklama": "Kesit alanı yarıya düşen iki parçalı çubuk, serbest ucundan 100 kN çekilir; her parçanın uzaması PL/EA ile bulunur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 1, "y": 0},
            {"no": 3, "x": 2, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.002"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.001"},
        ],
        "mesnetler": [{"dugum": 1, "ux": True}],
        "yukler": [{"dugum": 3, "Fx": 100}],
    },
    "kafes-iki-cubuk": {
        "tip": "kafes",
        "baslik": "İki çubuklu kafes (üçgen)",
        "aciklama": "6 m açıklıklı, 4 m yüksekliğindeki iki çubuklu kafesin tepe düğümüne 10 kN aşağı yük gelir; iki çubuk da basınç çalışır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 6, "y": 0},
            {"no": 3, "x": 3, "y": 4},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 3], "E": "200e6", "A": "0.001"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.001"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True},
            {"dugum": 2, "ux": True, "uy": True},
        ],
        "yukler": [{"dugum": 3, "Fy": -10}],
    },
    "kafes-uc-cubuk": {
        "tip": "kafes",
        "baslik": "Üç çubuklu hiperstatik kafes",
        "aciklama": "Tek serbest düğüme üç mafsallı çubuk bağlıdır; bir çubuk fazla olduğundan denge denklemleri yetmez, rijitlik yöntemi çözer.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
            {"no": 3, "x": 6, "y": 0},
            {"no": 4, "x": 3, "y": 4},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 4], "E": "200e6", "A": "0.001"},
            {"no": 2, "dugumler": [2, 4], "E": "200e6", "A": "0.002"},
            {"no": 3, "dugumler": [3, 4], "E": "200e6", "A": "0.001"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True},
            {"dugum": 2, "ux": True, "uy": True},
            {"dugum": 3, "ux": True, "uy": True},
        ],
        "yukler": [{"dugum": 4, "Fx": 10, "Fy": -20}],
    },
    "kafes-pratt-kopru": {
        "tip": "kafes",
        "baslik": "Pratt kafes köprü",
        "aciklama": "12 m açıklıklı Pratt kafes köprünün üç alt düğümüne 10 kN düşey yük gelir; üst başlık basınç, alt başlık çekme çalışır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
            {"no": 3, "x": 6, "y": 0},
            {"no": 4, "x": 9, "y": 0},
            {"no": 5, "x": 12, "y": 0},
            {"no": 6, "x": 3, "y": 3},
            {"no": 7, "x": 6, "y": 3},
            {"no": 8, "x": 9, "y": 3},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.002"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.002"},
            {"no": 3, "dugumler": [3, 4], "E": "200e6", "A": "0.002"},
            {"no": 4, "dugumler": [4, 5], "E": "200e6", "A": "0.002"},
            {"no": 5, "dugumler": [6, 7], "E": "200e6", "A": "0.002"},
            {"no": 6, "dugumler": [7, 8], "E": "200e6", "A": "0.002"},
            {"no": 7, "dugumler": [1, 6], "E": "200e6", "A": "0.002"},
            {"no": 8, "dugumler": [5, 8], "E": "200e6", "A": "0.002"},
            {"no": 9, "dugumler": [2, 6], "E": "200e6", "A": "0.002"},
            {"no": 10, "dugumler": [3, 7], "E": "200e6", "A": "0.002"},
            {"no": 11, "dugumler": [4, 8], "E": "200e6", "A": "0.002"},
            {"no": 12, "dugumler": [6, 3], "E": "200e6", "A": "0.002"},
            {"no": 13, "dugumler": [8, 3], "E": "200e6", "A": "0.002"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True},
            {"dugum": 5, "uy": True},
        ],
        "yukler": [
            {"dugum": 2, "Fy": -10},
            {"dugum": 3, "Fy": -10},
            {"dugum": 4, "Fy": -10},
        ],
    },
    "kiris-konsol": {
        "tip": "kiris",
        "baslik": "Ucundan yüklü konsol kiriş",
        "aciklama": "3 m boyundaki ankastre konsolun serbest ucuna 10 kN aşağı yük gelir; uç çökmesi PL³/3EI, uç dönmesi PL²/2EI ile bulunur.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "8e-6"},
        ],
        "mesnetler": [{"dugum": 1, "uy": True, "rz": True}],
        "yukler": [{"dugum": 2, "Fy": -10}],
    },
    "kiris-basit-yayili": {
        "tip": "kiris",
        "baslik": "Yayılı yüklü basit kiriş",
        "aciklama": "6 m açıklıklı basit kiriş iki elemana bölünmüş ve 12 kN/m düzgün yayılı yük taşır; orta çökme 5qL⁴/384EI'dir.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 3, "y": 0},
            {"no": 3, "x": 6, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "I": "2e-5"},
        ],
        "mesnetler": [
            {"dugum": 1, "uy": True},
            {"dugum": 3, "uy": True},
        ],
        "yayili": [
            {"eleman": 1, "q": -12},
            {"eleman": 2, "q": -12},
        ],
    },
    "kiris-ankastre-mafsalli": {
        "tip": "kiris",
        "baslik": "Bir ucu ankastre, bir ucu kayıcı kiriş",
        "aciklama": "4 m'lik tek elemanlı kiriş, sol ucu ankastre sağ ucu kayıcı mesnetli; 10 kN/m yayılı yükte hiperstatiktir (kayıcı tepkisi 3qL/8).",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 4, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"},
        ],
        "mesnetler": [
            {"dugum": 1, "uy": True, "rz": True},
            {"dugum": 2, "uy": True},
        ],
        "yayili": [{"eleman": 1, "q": -10}],
    },
    "cerceve-konsol-kolon": {
        "tip": "cerceve",
        "baslik": "Yatay yüklü konsol kolon",
        "aciklama": "3 m'lik ankastre kolonun üst ucuna 10 kN yatay yük gelir; çerçeve elemanı hem eksenel hem eğilme rijitliğini birlikte taşır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 0, "y": 3},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.01", "I": "8e-6"},
        ],
        "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "rz": True}],
        "yukler": [{"dugum": 2, "Fx": 10}],
    },
    "cerceve-portal": {
        "tip": "cerceve",
        "baslik": "Portal çerçeve",
        "aciklama": "Ankastre tabanlı 6 m açıklıklı, 4 m yüksekliğindeki portal çerçeve; kirişte 10 kN/m yayılı yük, sol üst köşede 20 kN yatay yük vardır.",
        "birim": {"kuvvet": "kN", "uzunluk": "m"},
        "dugumler": [
            {"no": 1, "x": 0, "y": 0},
            {"no": 2, "x": 0, "y": 4},
            {"no": 3, "x": 6, "y": 4},
            {"no": 4, "x": 6, "y": 0},
        ],
        "elemanlar": [
            {"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.01", "I": "1e-4"},
            {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.01", "I": "2e-4"},
            {"no": 3, "dugumler": [4, 3], "E": "200e6", "A": "0.01", "I": "1e-4"},
        ],
        "mesnetler": [
            {"dugum": 1, "ux": True, "uy": True, "rz": True},
            {"dugum": 4, "ux": True, "uy": True, "rz": True},
        ],
        "yukler": [{"dugum": 2, "Fx": 20}],
        "yayili": [{"eleman": 2, "q": -10}],
    },
}


def ornek_model(ad):
    """Örnek modelin bağımsız bir kopyasını (sözlük) döndürür."""
    if ad not in ORNEK_MODELLER:
        raise MatrisHatasi(f"Örnek model yok: {ad!r}. Seçenekler: {', '.join(ORNEK_MODELLER)}.")
    return copy.deepcopy(ORNEK_MODELLER[ad])


def ornek_listesi():
    """Örnek modellerin kısa listesi: [{ad, baslik, tip, aciklama}, ...]."""
    return [{"ad": ad, "baslik": m.get("baslik", ad), "tip": m["tip"], "aciklama": m.get("aciklama", "")}
            for ad, m in ORNEK_MODELLER.items()]


# ============================================================================
# Tür bilgileri
# ============================================================================
_TIPLER = ("yay", "cubuk", "kafes", "kiris", "cerceve")
_TIP_AD = {
    "yay": "yay sistemi (1 boyutlu)",
    "cubuk": "eksenel çubuk (1 boyutlu)",
    "kafes": "düzlem kafes",
    "kiris": "kiriş (Euler–Bernoulli)",
    "cerceve": "düzlem çerçeve",
}
_SD_SAYISI = {"yay": 1, "cubuk": 1, "kafes": 2, "kiris": 2, "cerceve": 3}
_SD_ADLARI = {"yay": ("u",), "cubuk": ("u",), "kafes": ("u", "v"), "kiris": ("v", "θ"), "cerceve": ("u", "v", "θ")}
_SD_LATEX = {"u": "u", "v": "v", "θ": r"\theta"}
_MESNET_ANAHTAR = {"yay": ("ux",), "cubuk": ("ux",), "kafes": ("ux", "uy"), "kiris": ("uy", "rz"),
                   "cerceve": ("ux", "uy", "rz")}
_BILESEN = {"yay": ("Fx",), "cubuk": ("Fx",), "kafes": ("Fx", "Fy"), "kiris": ("Fy", "M"),
            "cerceve": ("Fx", "Fy", "M")}
_OZELLIK = {"yay": ("k",), "cubuk": ("E", "A"), "kafes": ("E", "A"), "kiris": ("E", "I"),
            "cerceve": ("E", "A", "I")}
_OZELLIK_AD = {"E": "elastisite modülü", "A": "kesit alanı", "I": "atalet momenti", "k": "yay sabiti"}
_RIJIT_HAREKET = {"yay": 1, "cubuk": 1, "kafes": 3, "kiris": 2, "cerceve": 3}
_TR_SADE = str.maketrans("şçığöüŞÇİĞÖÜ", "scigouSCIGOU")

_ALT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_UST = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")


def _alt(n):
    return str(n).translate(_ALT)


def _ust(n):
    return str(n).translate(_UST)


# ============================================================================
# Sayı biçimleme
# ============================================================================
def _gercek(x):
    """Sayıysa float, sembolik/karmaşıksa None."""
    if isinstance(x, (bool, int, float)):
        return float(x)
    if np is not None and isinstance(x, np.generic):
        return float(x)
    try:
        x = sp.sympify(x)
        if x.free_symbols:
            return None
        return float(x)
    except (TypeError, ValueError, ArithmeticError):
        return None


def _ondalik_metin(v, basamak=None):
    """float → düz metin (anlamlı basamak sayısı kadar; çok büyük/küçükse 10'un kuvveti)."""
    if v == 0:
        return "0"
    b = int(basamak or mo.ayarlar.basamak)
    s = f"{v:.{b}g}"
    if "e" in s:
        m, e = s.split("e")
        return f"{m}×10{_ust(int(e))}"
    return s


def _metin(x, basamak=None):
    """Skaleri düz metne (md tablosu, SVG yazısı) çevirir; sembolik ifade olduğu gibi yazılır."""
    v = _gercek(x)
    if v is None:
        return str(sp.sympify(x)).replace("**", "^").replace("*", "·")
    return _ondalik_metin(v, basamak)


def _L_ondalik(v, basamak=None):
    if v == 0:
        return "0"
    b = int(basamak or mo.ayarlar.basamak)
    s = f"{v:.{b}g}"
    if "e" in s:
        m, e = s.split("e")
        return rf"{m}\times 10^{{{int(e)}}}"
    return s


def _L(x):
    """Skaler → LaTeX (kesin modda motorun kesir/ondalık ayarı; sayısal modda ondalık)."""
    if isinstance(x, float) or (np is not None and isinstance(x, np.floating)):
        return _L_ondalik(float(x))
    return mo.L(x)


def _Lp(x):
    s = _L(x)
    if s.startswith("-") or (isinstance(x, sp.Basic) and x.is_Add):
        return rf"\left({s}\right)"
    return s


def _sade(x):
    """Kesin moddaki ifadeleri sadeleştirir (sembolikse simplify, kök içeren sayıysa payda köksüz)."""
    if isinstance(x, sp.MatrixBase):
        return x.applyfunc(_sade)
    if not isinstance(x, sp.Basic):
        return x
    if x.free_symbols:
        return sp.simplify(x)
    if x.is_Rational:
        return x
    y = sp.radsimp(sp.expand(x))
    if y.is_Number:
        return y
    try:
        if abs(float(y)) < 1e-13 and sp.simplify(y) == 0:
            return sp.Integer(0)
    except (TypeError, ValueError):
        pass
    return y


def _veri_sayi(x):
    """JSON'a uygun değer: sayıysa float, sembolikse ifade metni."""
    v = _gercek(x)
    if v is not None:
        return v
    return str(sp.sympify(x))


def _isaret_negatif(x):
    """x negatif mi? (sembolik ifadede '-P' gibi eksi işareti çıkarılabiliyorsa negatif sayılır)."""
    v = _gercek(x)
    if v is not None:
        return v < 0
    try:
        return bool(sp.sympify(x).could_extract_minus_sign())
    except (AttributeError, TypeError):
        return False


# ============================================================================
# Model okuma ve doğrulama
# ============================================================================
def _tam(x, ad):
    if isinstance(x, bool):
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {x!r}).")
    try:
        f = float(x)
    except (TypeError, ValueError):
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {x!r}).") from None
    if not math.isfinite(f) or not f.is_integer():
        raise MatrisHatasi(f"{ad} tam sayı olmalı (girilen: {x!r}).")
    return int(f)


def _bayrak(v):
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "evet", "doğru", "dogru", "var", "x")
    return bool(v)


def _say(deger, ad, zorunlu=False):
    """Bir model değerini sympy skalerine çevirir (hata iletisi ad ile başlar)."""
    if deger is None or (isinstance(deger, str) and not deger.strip()):
        if zorunlu:
            raise MatrisHatasi(f"{ad} verilmedi.")
        return sp.Integer(0)
    try:
        return mo.skaler_oku(deger)
    except MatrisHatasi as e:
        raise MatrisHatasi(f"{ad}: {e}") from None
    except Exception:  # noqa: BLE001
        raise MatrisHatasi(f"{ad}: değer anlaşılamadı ({deger!r}). Sayı ya da E, A, P gibi bir ifade yazın.") from None


def _koord(deger, ad):
    v = _say(deger, ad)
    if v.free_symbols or v.is_real is False:
        raise MatrisHatasi(f"{ad} sayı olmalı (harf/sembol olamaz; girilen: {deger!r}). "
                           "Koordinatlar yapının geometrisidir; sayısal verilmelidir.")
    return v


def _sd_etiketleri(tip, dugumler):
    uni, tex = [], []
    for dg in dugumler:
        for a in _SD_ADLARI[tip]:
            uni.append(f"{a}{_alt(dg.no)}")
            tex.append(f"{_SD_LATEX[a]}_{{{dg.no}}}")
    return uni, tex


def _model_oku(model):
    """Sözlük ya da JSON metnini doğrulayıp hesaplanabilir bir model nesnesine (SimpleNamespace) çevirir."""
    if isinstance(model, str):
        try:
            model = json.loads(model)
        except ValueError as e:
            raise MatrisHatasi(f"Model JSON olarak okunamadı: {e}") from None
    if not isinstance(model, dict):
        raise MatrisHatasi('Model bir sözlük (ya da JSON metni) olmalı: {"tip": "kafes", "dugumler": [...], '
                           '"elemanlar": [...], "mesnetler": [...], "yukler": [...]}.')
    tip = str(model.get("tip", "")).strip().lower().translate(_TR_SADE)
    if tip not in _TIPLER:
        raise MatrisHatasi(f"Bilinmeyen model türü: {model.get('tip')!r}. Seçenekler: {', '.join(_TIPLER)} "
                           "(yay, eksenel çubuk, kafes, kiriş, çerçeve).")
    d = _SD_SAYISI[tip]
    birim = model.get("birim") if isinstance(model.get("birim"), dict) else {}
    kuvvet = str(birim.get("kuvvet", "kN"))
    uzunluk = str(birim.get("uzunluk", "m"))
    semb = False

    # --- düğümler ---
    dl = model.get("dugumler")
    if not isinstance(dl, list) or not dl:
        raise MatrisHatasi("Modelde düğüm yok: 'dugumler' listesi boş ya da eksik. "
                           "Örnek: [{\"no\": 1, \"x\": 0, \"y\": 0}, {\"no\": 2, \"x\": 3, \"y\": 0}].")
    dugumler, dn = [], {}
    for k, dg in enumerate(dl, start=1):
        if not isinstance(dg, dict):
            raise MatrisHatasi(f"{k}. düğüm bir sözlük olmalı: {{\"no\": 1, \"x\": 0, \"y\": 0}}.")
        no = _tam(dg.get("no", k), f"{k}. düğümün 'no' değeri")
        if no in dn:
            raise MatrisHatasi(f"Düğüm {no} iki kez tanımlandı; her düğüm numarası yalnız bir kez kullanılabilir.")
        x = _koord(dg.get("x", 0), f"Düğüm {no}: x koordinatı")
        y = sp.Integer(0) if tip in ("yay", "cubuk") else _koord(dg.get("y", 0), f"Düğüm {no}: y koordinatı")
        dn[no] = len(dugumler)
        dugumler.append(SimpleNamespace(no=no, x=x, y=y, i=len(dugumler)))
    if tip == "kiris":
        for dg in dugumler[1:]:
            if sp.simplify(dg.y - dugumler[0].y) != 0:
                raise MatrisHatasi(
                    f"Kiriş modelinde bütün düğümler aynı yatay doğru üzerinde olmalı (y aynı): düğüm {dg.no} "
                    f"y={dg.y}, düğüm {dugumler[0].no} y={dugumler[0].y}. Eğik ya da kırık eksenli taşıyıcılar "
                    "için 'cerceve' türünü kullanın.")

    # --- elemanlar ---
    el = model.get("elemanlar")
    if not isinstance(el, list) or not el:
        raise MatrisHatasi("Modelde eleman yok: 'elemanlar' listesi boş ya da eksik. Örnek: "
                           "[{\"no\": 1, \"dugumler\": [1, 2], \"E\": \"200e6\", \"A\": \"0.001\"}].")
    elemanlar, en = [], {}
    for k, e in enumerate(el, start=1):
        if not isinstance(e, dict):
            raise MatrisHatasi(f"{k}. eleman bir sözlük olmalı: {{\"no\": 1, \"dugumler\": [1, 2], ...}}.")
        no = _tam(e.get("no", k), f"{k}. elemanın 'no' değeri")
        if no in en:
            raise MatrisHatasi(f"Eleman {no} iki kez tanımlandı; her eleman numarası yalnız bir kez kullanılabilir.")
        dd = e.get("dugumler")
        if not isinstance(dd, (list, tuple)) or len(dd) != 2:
            raise MatrisHatasi(f"Eleman {no}: 'dugumler' iki düğüm numarası içermeli, örn. [1, 2].")
        a = _tam(dd[0], f"Eleman {no}: birinci düğüm numarası")
        b = _tam(dd[1], f"Eleman {no}: ikinci düğüm numarası")
        for dno in (a, b):
            if dno not in dn:
                raise MatrisHatasi(f"Eleman {no} tanımsız bir düğüme bağlı: düğüm {dno}. "
                                   f"Tanımlı düğümler: {sorted(dn)}.")
        ia, ib = dn[a], dn[b]
        dx = dugumler[ib].x - dugumler[ia].x
        dy = dugumler[ib].y - dugumler[ia].y
        sifir = (dx == 0) if tip in ("yay", "cubuk", "kiris") else (dx == 0 and dy == 0)
        if a == b or sifir:
            raise MatrisHatasi(f"Eleman {no}'nin boyu sıfır: düğüm {a} ve düğüm {b} aynı noktada. "
                               "Sıfır boylu elemanın rijitliği tanımsızdır (EA/L, EI/L³ ifadelerinde L = 0 olurdu); "
                               "düğüm koordinatlarını düzeltin.")
        if tip == "kiris" and dx < 0:
            raise MatrisHatasi(f"Eleman {no}: kiriş elemanları soldan sağa tanımlanmalıdır (ilk düğümün x'i küçük "
                               f"olmalı); düğüm sırasını [{b}, {a}] yapın. (Yerel y ekseni yukarıyı gösterir; "
                               "yayılı yük q aşağı için negatiftir.)")
        ozel = {}
        for p in _OZELLIK[tip]:
            v = _say(e.get(p), f"Eleman {no}: {p} ({_OZELLIK_AD[p]})", zorunlu=True)
            if v.free_symbols:
                semb = True
            elif v.is_real is False or v <= 0:
                raise MatrisHatasi(f"Eleman {no}: {p} ({_OZELLIK_AD[p]}) pozitif bir sayı olmalı (girilen: {e.get(p)!r}). "
                                   "Sıfır ya da negatif rijitlik yapıyı çözülemez yapar.")
            ozel[p] = v
        en[no] = len(elemanlar)
        elemanlar.append(SimpleNamespace(no=no, dno=(a, b), ia=ia, ib=ib, idx=len(elemanlar),
                                         E=ozel.get("E"), A=ozel.get("A"), I=ozel.get("I"), k=ozel.get("k")))

    kullanilan = {x for e in elemanlar for x in e.dno}
    for dg in dugumler:
        if dg.no not in kullanilan:
            raise MatrisHatasi(f"Düğüm {dg.no} hiçbir elemana bağlı değil: bu düğümün serbestlikleri için denklem "
                               "yazılamaz (K matrisinde sıfır satır/sütun oluşur). Düğümü bir elemana bağlayın "
                               "ya da modelden çıkarın.")

    # --- mesnetler ---
    mesnet = [[False] * d for _ in dugumler]
    for m in model.get("mesnetler") or []:
        if not isinstance(m, dict):
            raise MatrisHatasi('Her mesnet bir sözlük olmalı: {"dugum": 1, "ux": true, "uy": true}.')
        dno = _tam(m.get("dugum"), "Mesnetin 'dugum' değeri")
        if dno not in dn:
            raise MatrisHatasi(f"Mesnet tanımsız bir düğümde: düğüm {dno}. Tanımlı düğümler: {sorted(dn)}.")
        for k, anahtar in enumerate(_MESNET_ANAHTAR[tip]):
            deger = m.get(anahtar)
            if deger is None and tip in ("yay", "cubuk") and anahtar == "ux":
                deger = m.get("u")
            if _bayrak(deger):
                mesnet[dn[dno]][k] = True

    # --- yükler ---
    yuk = [[sp.Integer(0)] * d for _ in dugumler]
    for y in model.get("yukler") or []:
        if not isinstance(y, dict):
            raise MatrisHatasi('Her yük bir sözlük olmalı: {"dugum": 3, "Fy": -10}.')
        dno = _tam(y.get("dugum"), "Yükün 'dugum' değeri")
        if dno not in dn:
            raise MatrisHatasi(f"Yük tanımsız bir düğümde: düğüm {dno}. Tanımlı düğümler: {sorted(dn)}.")
        gecerli = _BILESEN[tip]
        for anahtar in ("Fx", "Fy", "M"):
            ham = y.get(anahtar)
            if ham is None and tip in ("yay", "cubuk") and anahtar == "Fx":
                ham = y.get("F")
            if anahtar not in gecerli:
                if ham is not None and _say(ham, f"Düğüm {dno}: {anahtar}") != 0:
                    raise MatrisHatasi(f"Düğüm {dno}: {anahtar} yükü bu model türünde ({_TIP_AD[tip]}) etkisizdir; "
                                       f"bu türde geçerli yükler: {', '.join(gecerli)}.")
                continue
            v = _say(ham, f"Düğüm {dno}: {anahtar} yükü")
            if v.free_symbols:
                semb = True
            yuk[dn[dno]][gecerli.index(anahtar)] += v

    # --- yayılı yükler ---
    q = [sp.Integer(0)] * len(elemanlar)
    for y in model.get("yayili") or []:
        if not isinstance(y, dict):
            raise MatrisHatasi('Her yayılı yük bir sözlük olmalı: {"eleman": 1, "q": -12}.')
        if tip not in ("kiris", "cerceve"):
            raise MatrisHatasi("Yayılı yük (yayili) yalnız kiriş ve çerçeve modelinde kullanılabilir; "
                               f"{_TIP_AD[tip]} yalnız düğüm yükü taşır.")
        eno = _tam(y.get("eleman"), "Yayılı yükün 'eleman' değeri")
        if eno not in en:
            raise MatrisHatasi(f"Yayılı yük tanımsız bir elemanda: eleman {eno}. Tanımlı elemanlar: {sorted(en)}.")
        v = _say(y.get("q"), f"Eleman {eno}: yayılı yük q")
        if v.free_symbols:
            semb = True
        q[en[eno]] += v

    M = SimpleNamespace(
        tip=tip, d=d, baslik=str(model.get("baslik") or f"{_TIP_AD[tip].capitalize()} modeli"),
        kuvvet=kuvvet, uzunluk=uzunluk, dugumler=dugumler, dn=dn, elemanlar=elemanlar, en=en,
        mesnet=mesnet, yuk=yuk, q=q, n=d * len(dugumler), sembolik=semb, uyarilar=[],
    )
    M.sd_et, M.sd_tex = _sd_etiketleri(tip, dugumler)

    # --- hesap modu ---
    if M.n > SD_ESIK:
        if semb:
            raise MatrisHatasi(
                f"Harfli (sembolik) girdi en çok {SD_ESIK} serbestlik derecesinde (SD) çözülür; bu model {M.n} SD içeriyor. "
                "Sembolik çözüm büyüdükçe ifadeler okunamaz hale gelir: E, A, P gibi harfleri sayıyla değiştirin "
                f"ya da modeli {SD_ESIK} SD'ye indirin.")
        M.mod = "sayisal"
        if np is None:
            raise MatrisHatasi(f"{M.n} SD için sayısal hesap gerekir ama numpy yüklü değil.")
    else:
        M.mod = "kesin"
    M.sayisal = M.mod == "sayisal"

    # --- birim uyarısı (E değeri MPa girilmiş olabilir) ---
    if kuvvet == "kN" and uzunluk == "m":
        for e in elemanlar:
            v = _gercek(e.E) if e.E is not None else None
            if v is not None and 1e3 <= v <= 1e6:
                s = f"{v:,.0f}".replace(",", " ")
                M.uyarilar.append(
                    f"E = {s} girildi: MPa mı? Birimler kN ve m ise E, kN/m² cinsinden yazılmalıdır "
                    f"(1 MPa = 1000 kN/m²): çelik için 2,0×10⁸ kN/m² (200 GPa), beton için yaklaşık 3×10⁷ kN/m². "
                    f"Eleman {e.no}'de E değeri bu beklentinin çok altında.")
                break

    if M.sayisal:
        _floata_cevir(M)
    return M


def _floata_cevir(M):
    for dg in M.dugumler:
        dg.x, dg.y = float(dg.x), float(dg.y)
    for e in M.elemanlar:
        for p in ("E", "A", "I", "k"):
            v = getattr(e, p)
            if v is not None:
                setattr(e, p, float(v))
    M.yuk = [[float(v) for v in satir] for satir in M.yuk]
    M.q = [float(v) for v in M.q]



# ============================================================================
# Hesap çekirdeği (kesin: sympy, sayısal: numpy)
# ============================================================================
def _mat(M, satirlar):
    return np.array(satirlar, dtype=float) if M.sayisal else sp.Matrix(satirlar)


def _vek(M, liste):
    return np.array(liste, dtype=float) if M.sayisal else sp.Matrix(liste)


def _sifir_mat(M, n):
    return np.zeros((n, n)) if M.sayisal else sp.zeros(n, n)


def _sifir_vek(M, n):
    return np.zeros(n) if M.sayisal else sp.zeros(n, 1)


def _liste(v):
    return [v[i] for i in range(len(v))]


def _al(M, v, idx):
    idx = list(idx)
    return v[idx] if M.sayisal else sp.Matrix([v[i] for i in idx])


def _k_kiris(E, I, L):
    a = E * I / L ** 3
    return [[12 * a, 6 * L * a, -12 * a, 6 * L * a],
            [6 * L * a, 4 * L * L * a, -6 * L * a, 2 * L * L * a],
            [-12 * a, -6 * L * a, 12 * a, -6 * L * a],
            [6 * L * a, 2 * L * L * a, -6 * L * a, 4 * L * L * a]]


def _k_cerceve(E, A, I, L):
    ea = E * A / L
    a = E * I / L ** 3
    return [[ea, 0, 0, -ea, 0, 0],
            [0, 12 * a, 6 * L * a, 0, -12 * a, 6 * L * a],
            [0, 6 * L * a, 4 * L * L * a, 0, -6 * L * a, 2 * L * L * a],
            [-ea, 0, 0, ea, 0, 0],
            [0, -12 * a, -6 * L * a, 0, 12 * a, -6 * L * a],
            [0, 6 * L * a, 2 * L * L * a, 0, -6 * L * a, 4 * L * L * a]]


def _T_cerceve(c, s):
    return [[c, s, 0, 0, 0, 0], [-s, c, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0],
            [0, 0, 0, c, s, 0], [0, 0, 0, -s, c, 0], [0, 0, 0, 0, 0, 1]]


def _sembol_degerleri(*nesneler):
    """Sembolleri (E, A, P ...) mekanizma denetimi için pozitif sayılara bağlar."""
    semb = set()
    for o in nesneler:
        if isinstance(o, (sp.Basic, sp.MatrixBase)):
            semb |= o.free_symbols
    return {s: sp.Rational(13 + 7 * i, 10) for i, s in enumerate(sorted(semb, key=lambda s: s.name))}


def _hazirla(M):
    """Eleman geometrisi, eleman matrisleri, birleştirilmiş K, yük vektörü F, mesnet listeleri."""
    tip, d, say = M.tip, M.d, M.sayisal
    bir, sifir = (1.0, 0.0) if say else (sp.Integer(1), sp.Integer(0))
    for e in M.elemanlar:
        a, b = M.dugumler[e.ia], M.dugumler[e.ib]
        dx, dy = b.x - a.x, b.y - a.y
        if tip in ("yay", "cubuk"):
            e.L = abs(dx)
            e.c, e.s = (bir if dx > 0 else -bir), sifir
        elif tip == "kiris":
            e.L, e.c, e.s = dx, bir, sifir
        elif say:
            e.L = math.hypot(dx, dy)
            e.c, e.s = dx / e.L, dy / e.L
        else:
            e.L = _sade(sp.sqrt(dx * dx + dy * dy))
            e.c, e.s = _sade(dx / e.L), _sade(dy / e.L)
        e.aci = math.degrees(math.atan2(float(dy), float(dx)))
        E, A, I, k, L, c, s = e.E, e.A, e.I, e.k, e.L, e.c, e.s
        if tip == "yay":
            kl = _mat(M, [[k, -k], [-k, k]])
        elif tip in ("cubuk", "kafes"):
            ea = E * A / L
            kl = _mat(M, [[ea, -ea], [-ea, ea]])
        elif tip == "kiris":
            kl = _mat(M, _k_kiris(E, I, L))
        else:
            kl = _mat(M, _k_cerceve(E, A, I, L))
        if tip == "kafes":
            e.T = _mat(M, [[c, s, 0, 0], [0, 0, c, s]])
        elif tip == "cerceve":
            e.T = _mat(M, _T_cerceve(c, s))
        else:
            e.T = None
        ke = kl if e.T is None else e.T.T @ kl @ e.T
        if not say:
            kl, ke = _sade(kl), _sade(ke)
        e.k_yerel, e.ke = kl, ke
        e.dofs = [d * e.ia + j for j in range(d)] + [d * e.ib + j for j in range(d)]
        q = M.q[e.idx]
        e.q = q
        e.feq_yerel = e.feq = None
        if tip in ("kiris", "cerceve") and q != 0:
            if tip == "kiris":
                fy = _vek(M, [q * L / 2, q * L ** 2 / 12, q * L / 2, -q * L ** 2 / 12])
                fg = fy
            else:
                fy = _vek(M, [0, q * L / 2, q * L ** 2 / 12, 0, q * L / 2, -q * L ** 2 / 12])
                fg = e.T.T @ fy
            if not say:
                fy, fg = _sade(fy), _sade(fg)
            e.feq_yerel, e.feq = fy, fg

    n = M.n
    K = _sifir_mat(M, n)
    for e in M.elemanlar:
        for a_, I_ in enumerate(e.dofs):
            for b_, J_ in enumerate(e.dofs):
                K[I_, J_] += e.ke[a_, b_]
    M.K = K if say else _sade(K)
    Fd = _sifir_vek(M, n)
    for i, satir in enumerate(M.yuk):
        for j, v in enumerate(satir):
            Fd[d * i + j] += v
    F = Fd.copy()
    for e in M.elemanlar:
        if e.feq is not None:
            for a_, I_ in enumerate(e.dofs):
                F[I_] += e.feq[a_]
    M.F_dugum, M.F = Fd, (F if say else _sade(F))
    M.sabit = [d * i + j for i, fl in enumerate(M.mesnet) for j, f in enumerate(fl) if f]
    ks = set(M.sabit)
    M.serbest = [i for i in range(n) if i not in ks]
    _mekanizma_kontrol(M)


def _mekanizma_kontrol(M):
    """İndirgenmiş K tekilse (mekanizma / yetersiz mesnet) öğretici hata verir."""
    if not M.serbest:
        return
    Ks = M.K[np.ix_(M.serbest, M.serbest)] if M.sayisal else M.K.extract(M.serbest, M.serbest)
    z = 0
    if np is not None:
        if not M.sayisal:
            Ks = np.array(Ks.subs(_sembol_degerleri(Ks)).evalf(20).tolist(), dtype=float)
        w = np.abs(np.linalg.eigvalsh(Ks))
        z = int((w <= 1e-11 * max(float(w.max()), 1e-300)).sum())
    else:  # pragma: no cover (numpy yoksa: kesin kip)
        z = Ks.shape[0] - Ks.subs(_sembol_degerleri(Ks)).rank()
    if z == 0:
        return
    gerek = _RIJIT_HAREKET[M.tip]
    ipucu = {
        "yay": "En az bir düğümün u serbestliğini tutun (ux: true).",
        "cubuk": "En az bir düğümün u serbestliğini tutun (ux: true).",
        "kafes": "Düzlem kafes için en az 3 bileşen tutulmalıdır: örneğin bir düğümde ux ve uy, başka bir düğümde uy "
                 "(üç mesnet çubuğu tek noktada kesişmemeli, hepsi paralel olmamalı). Ayrıca her düğümün çubuklarla "
                 "kararlı bağlandığını (üçgenleme) denetleyin.",
        "kiris": "Kiriş için en az 2 bileşen tutulmalıdır: bir ankastre (uy ve rz) ya da iki farklı noktada uy.",
        "cerceve": "Düzlem çerçeve için en az 3 bileşen tutulmalıdır: bir ankastre (ux, uy, rz) ya da bir sabit "
                   "(ux, uy) ile bir kayıcı (uy) mesnet gibi.",
    }[M.tip]
    raise MatrisHatasi(
        f"Mesnetler yetersiz ya da yapı mekanizma: yapı {z} bağımsız rijit cisim hareketi (ya da mekanizma "
        f"hareketi) yapabilir; indirgenmiş K matrisi tekildir ve çözüm tek değildir. Hiç mesnetsiz bir "
        f"{_TIP_AD[M.tip]} {gerek} rijit hareket yapabilir; mesnetler bunların hepsini engellemelidir. {ipucu}")


def _coz(M):
    """K_ss u_s = F_s sistemini çözer (kesin: sympy LU, sayısal: numpy), sonra tepkileri hesaplar."""
    if M.sayisal:
        u = np.zeros(M.n)
        if M.serbest:
            u[M.serbest] = np.linalg.solve(M.K[np.ix_(M.serbest, M.serbest)], M.F[M.serbest])
    else:
        u = sp.zeros(M.n, 1)
        if M.serbest:
            Ks = M.K.extract(M.serbest, M.serbest)
            Fs = sp.Matrix([M.F[i] for i in M.serbest])
            us = Ks.LUsolve(Fs)
            for a, i in enumerate(M.serbest):
                u[i] = _sade(us[a])
    M.u = u
    _tepki_hesapla(M)


def _tepki_hesapla(M):
    """R = K u − F: yalnız tutulu SD'lerde sıfırdan farklı olmalı (serbest SD'lerde sağlama)."""
    R = M.K @ M.u - M.F
    if M.sayisal:
        olcek = max(1.0, float(np.abs(M.F).max()))
        ks = set(M.sabit)
        for i in range(M.n):
            if i not in ks and abs(R[i]) <= 1e-9 * olcek:
                R[i] = 0.0
    else:
        R = _sade(R)
    M.R_tam = R


def _eleman_kuvvetleri(M):
    """Her eleman için u_e, yerel yer değiştirme d, uç kuvvetleri f = k d − f_eq ve eksenel kuvvet N."""
    tip = M.tip
    for e in M.elemanlar:
        ue = _al(M, M.u, e.dofs)
        e.ue = ue
        if tip in ("yay", "cubuk", "kafes"):
            e.dyerel = e.c * ue if e.T is None else e.T @ ue
            ea = e.k if tip == "yay" else e.E * e.A / e.L
            if tip == "kafes":
                N = ea * (-e.c * ue[0] - e.s * ue[1] + e.c * ue[2] + e.s * ue[3])
            else:
                N = ea * e.c * (ue[1] - ue[0])
            e.N = N if M.sayisal else _sade(N)
            e.ea = ea
            e.f = None
            e.sigma = None if tip == "yay" else (e.N / e.A if M.sayisal else _sade(e.N / e.A))
        else:
            dy = ue if e.T is None else e.T @ ue
            f = e.k_yerel @ dy
            if e.feq_yerel is not None:
                f = f - e.feq_yerel
            if not M.sayisal:
                dy, f = _sade(dy), _sade(f)
            e.dyerel, e.f = dy, f
            e.N = _sifir_degeri(M) if tip == "kiris" else -f[0]
            e.sigma = None


def _sifir_degeri(M):
    return 0.0 if M.sayisal else sp.Integer(0)


def _denge_hesapla(M):
    """Dış yükler (düğüm yükleri + yayılı yük bileşkeleri) ile mesnet tepkilerinin dengesi (ilk düğüme göre)."""
    tip, d = M.tip, M.d
    x0, y0 = M.dugumler[0].x, M.dugumler[0].y
    sx = sy = sm = _sifir_degeri(M)
    for i, dg in enumerate(M.dugumler):
        fx = fy = mz = _sifir_degeri(M)
        for j, ad in enumerate(_BILESEN[tip]):
            v = M.yuk[i][j] + (M.R_tam[d * i + j] if (d * i + j) in M.sabit else 0)
            if ad == "Fx":
                fx = v
            elif ad == "Fy":
                fy = v
            else:
                mz = v
        sx, sy = sx + fx, sy + fy
        sm = sm + mz + (dg.x - x0) * fy - (dg.y - y0) * fx
    for e in M.elemanlar:
        if e.q != 0:
            W = e.q * e.L
            fx, fy = -e.s * W, e.c * W
            a, b = M.dugumler[e.ia], M.dugumler[e.ib]
            xm, ym = (a.x + b.x) / 2, (a.y + b.y) / 2
            sx, sy = sx + fx, sy + fy
            sm = sm + (xm - x0) * fy - (ym - y0) * fx
    if not M.sayisal:
        sx, sy, sm = _sade(sx), _sade(sy), _sade(sm)
    M.denge = {"Fx": sx, "Fy": sy, "M": sm}
    uKu = (M.u @ (M.K @ M.u)) if M.sayisal else _sade((M.u.T * M.K * M.u)[0, 0])
    uF = (M.u @ M.F) if M.sayisal else _sade((M.u.T * M.F)[0, 0])
    M.enerji = {"uKu": uKu, "uF": uF}


# ============================================================================
# Şema çizimi: bağımsız SVG (var() renkleri style özniteliğinde; <marker> ve <script> yok)
# ============================================================================
_AILE = {  # aile -> (dolgu, çizgi); PWA'nın --sema-* değişkenleri yoksa yazılı renkler kullanılır
    "a": ("var(--sema-a-bg,rgba(59,130,246,.14))", "var(--sema-a,#3b82f6)"),     # mavi
    "b": ("var(--sema-b-bg,rgba(245,158,11,.16))", "var(--sema-b,#f59e0b)"),     # amber
    "c": ("var(--sema-c-bg,rgba(16,185,129,.16))", "var(--sema-c,#10b981)"),     # yeşil
    "sil": ("var(--sema-sil-bg,rgba(239,68,68,.10))", "var(--sema-sil,#ef4444)"),  # kırmızı
}
_NOTR = "var(--sema-cizgi,#94a3b8)"
_KART = "var(--kart,#fff)"
_YAZI_AILESI = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"


def _n(v):
    """Koordinatı en çok 1 ondalıkla yazar."""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _st(dolgu=None, cizgi=None):
    """var() içeren renkleri style özniteliğine koyar (sunum özniteliklerinde var() her tarayıcıda güvenilir değildir)."""
    parca = ([f"fill:{dolgu}"] if dolgu else []) + ([f"stroke:{cizgi}"] if cizgi else [])
    return f'style="{";".join(parca)}"' if parca else ""


def _sv(x, basamak=None):
    """SVG etiketi için sayı metni (gerçek eksi işareti)."""
    return _metin(x, basamak).replace("-", "−")


class _Cizim:
    """Tek bir şema karesi için küçük SVG çizici: dünya (x, y) -> ekran (piksel, y aşağı) dönüşümü ve temel parçalar.

    Her parça çizildiği yerin sınırını kaydeder; görünüm kutusu (viewBox) bu sınırlardan hesaplanır.
    Kademe sınıfları: elemanlar g0, mesnetler g1, yükler/oklar g2, yazılar g3, şekil değiştirmiş biçim g4."""

    def __init__(self, M, genislik=400.0, en_buyuk=110.0):
        self.M = M
        xs = [float(dg.x) for dg in M.dugumler]
        ys = [float(dg.y) for dg in M.dugumler]
        self.xmin, self.ymax = min(xs), max(ys)
        self.gx, self.gy = max(xs) - min(xs), max(ys) - min(ys)
        aday = [en_buyuk]
        if self.gx > 0:
            aday.append(genislik / self.gx)
        if self.gy > 0:
            aday.append(0.9 * genislik / self.gy)
        self.s = min(aday)
        self.arka, self.orta, self.on = [], [], []
        self._e = [math.inf, math.inf, -math.inf, -math.inf]
        pts = [self.P(dg.x, dg.y) for dg in M.dugumler]
        self.merkez = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    # --- koordinat ---------------------------------------------------------
    def P(self, x, y):
        return (float(x) - self.xmin) * self.s, (self.ymax - float(y)) * self.s

    def D(self, i):
        dg = self.M.dugumler[i]
        return self.P(dg.x, dg.y)

    def E(self, e):
        return self.D(e.ia), self.D(e.ib)

    def kapsa(self, x0, y0, x1=None, y1=None):
        if x1 is None:
            x1, y1 = x0, y0
        k = self._e
        k[0], k[1] = min(k[0], x0, x1), min(k[1], y0, y1)
        k[2], k[3] = max(k[2], x0, x1), max(k[3], y0, y1)

    # --- parçalar ----------------------------------------------------------
    @staticmethod
    def _boya(aile):
        if aile is None:
            return 'stroke="currentColor"'
        if aile == "n":
            return _st(None, _NOTR)
        return _st(None, _AILE[aile][1])

    def cizgi(self, a, b, aile=None, kalin=2.4, sinif="g0", kesik=None, opak=None, katman="orta"):
        oz = (f' stroke-dasharray="{kesik}"' if kesik else "") + (f' opacity="{opak}"' if opak is not None else "")
        sn = f' class="{sinif}"' if sinif else ""
        getattr(self, katman).append(
            f'<line{sn} x1="{_n(a[0])}" y1="{_n(a[1])}" x2="{_n(b[0])}" y2="{_n(b[1])}" {self._boya(aile)} '
            f'stroke-width="{kalin}" stroke-linecap="round"{oz}/>')
        self.kapsa(a[0], a[1], b[0], b[1])

    def yol(self, pts, aile=None, kalin=2.0, sinif="g4", animasyon=False, kesik=None, opak=None, katman="orta"):
        if len(pts) < 2:
            return
        d = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts)
        sn = f"ok {sinif}" if animasyon else sinif
        pl = ' pathLength="1"' if animasyon else ""
        oz = (f' stroke-dasharray="{kesik}"' if kesik else "") + (f' opacity="{opak}"' if opak is not None else "")
        getattr(self, katman).append(
            f'<path class="{sn}"{pl} d="{d}" fill="none" {self._boya(aile)} stroke-width="{kalin}" '
            f'stroke-linecap="round" stroke-linejoin="round"{oz}/>')
        for x, y in pts:
            self.kapsa(x, y)

    def poligon(self, pts, aile, sinif="g3", katman="arka"):
        if len(pts) < 3:
            return
        d = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts) + " Z"
        getattr(self, katman).append(f'<path class="{sinif}" d="{d}" {_st(_AILE[aile][0], None)} stroke="none"/>')
        for x, y in pts:
            self.kapsa(x, y)

    def daire(self, c, r, aile=None, kalin=1.6, sinif="g0", katman="on", dolgu=_KART):
        if aile is None:
            boya = f'{_st(dolgu, None)} stroke="currentColor"'
        else:
            boya = _st(dolgu, _AILE[aile][1])
        getattr(self, katman).append(
            f'<circle class="{sinif}" cx="{_n(c[0])}" cy="{_n(c[1])}" r="{r}" {boya} stroke-width="{kalin}"/>')
        self.kapsa(c[0] - r, c[1] - r, c[0] + r, c[1] + r)

    def dikdortgen(self, x, y, w, h, aile=None, sinif="g0", katman="orta", kalin=1.8):
        dolgu = _AILE[aile or "a"][0]
        getattr(self, katman).append(
            f'<rect class="{sinif}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="2" '
            f'{_st(dolgu, None)} stroke="currentColor" stroke-width="{kalin}"/>')
        self.kapsa(x, y, x + w, y + h)

    def yazi(self, x, y, metin, hiza="middle", boyut=None, aile=None, kalin=False, sinif="g3", opak=None, cizik=False):
        metin = str(metin)
        oz = f' class="{sinif}"' if sinif else ""
        oz += f' x="{_n(x)}" y="{_n(y)}" dy=".35em" text-anchor="{hiza}"'
        oz += ' fill="currentColor"' if aile is None else f" {_st(_AILE[aile][1], None)}"
        if boyut:
            oz += f' font-size="{boyut}"'
        if kalin:
            oz += ' font-weight="600"'
        if opak is not None:
            oz += f' opacity="{opak}"'
        self.on.append(f"<text{oz}>{_html.escape(metin, quote=False)}</text>")
        b = boyut or 13
        gen = len(metin) * b * 0.58
        x0 = x - gen / 2 if hiza == "middle" else (x if hiza == "start" else x - gen)
        self.kapsa(x0, y - b * 0.7, x0 + gen, y + b * 0.7)
        if cizik:
            self.cizgi((x0 - 1, y), (x0 + gen + 1, y), "sil", kalin=1.6, sinif=sinif, katman="on")

    def ok(self, a, b, aile, g=2, kalin=2.0, uc=7.0, katman="orta"):
        """a -> b ok: <path class="ok" pathLength="1"> gövde + <polyline class="ok-uc"> ok başı."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        uz = math.hypot(dx, dy)
        if uz < 1.0:
            return
        tx, ty = dx / uz, dy / uz
        bx, by = b[0] - tx * uc, b[1] - ty * uc
        k = uc * 0.55
        p1, p2 = (bx - ty * k, by + tx * k), (bx + ty * k, by - tx * k)
        cz = _st(None, _AILE[aile][1])
        lst = getattr(self, katman)
        lst.append(f'<path class="ok g{g}" pathLength="1" d="M{_n(a[0])} {_n(a[1])} L{_n(b[0])} {_n(b[1])}" '
                   f'fill="none" {cz} stroke-width="{kalin}" stroke-linecap="round"/>')
        lst.append(f'<polyline class="ok-uc g{g}" points="{_n(p1[0])},{_n(p1[1])} {_n(b[0])},{_n(b[1])} '
                   f'{_n(p2[0])},{_n(p2[1])}" fill="none" {cz} stroke-width="{kalin}" stroke-linecap="round" '
                   f'stroke-linejoin="round"/>')
        self.kapsa(a[0], a[1], b[0], b[1])

    def yay_ok(self, c, r, ccw, aile, g=2, kalin=2.0, bas=40.0, son=280.0, katman="orta"):
        """Moment/dönme oku: c merkezli yay (ccw: saat yönünün tersi); açılar derece, dünya yönünde."""
        f0, f1 = (bas, son) if ccw else (son, bas)
        pts = []
        for k in range(25):
            f = math.radians(f0 + (f1 - f0) * k / 24)
            pts.append((c[0] + r * math.cos(f), c[1] - r * math.sin(f)))
        sg = 1.0 if f1 > f0 else -1.0
        fa = math.radians(f1)
        tx, ty = -math.sin(fa) * sg, -math.cos(fa) * sg
        b = pts[-1]
        bx, by = b[0] - tx * 6.0, b[1] - ty * 6.0
        k = 3.6
        p1, p2 = (bx - ty * k, by + tx * k), (bx + ty * k, by - tx * k)
        cz = _st(None, _AILE[aile][1])
        d = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts)
        lst = getattr(self, katman)
        lst.append(f'<path class="ok g{g}" pathLength="1" d="{d}" fill="none" {cz} stroke-width="{kalin}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
        lst.append(f'<polyline class="ok-uc g{g}" points="{_n(p1[0])},{_n(p1[1])} {_n(b[0])},{_n(b[1])} '
                   f'{_n(p2[0])},{_n(p2[1])}" fill="none" {cz} stroke-width="{kalin}" stroke-linecap="round" '
                   f'stroke-linejoin="round"/>')
        self.kapsa(c[0] - r - 2, c[1] - r - 2, c[0] + r + 2, c[1] + r + 2)

    def mesnet(self, X, Y, tur, yon="alt", g=1):
        """Mesnet simgesi: sabit (üçgen), kayıcı (üçgen + ayrık çizgi), ankastre (taralı duvar). yon: gövdenin düğüme göre yeri."""
        def P(a, b):
            return {"alt": (X + a, Y + b), "ust": (X + a, Y - b), "sol": (X - b, Y + a), "sag": (X + b, Y + a)}[yon]

        def seg(p, q):
            return f"M{_n(p[0])} {_n(p[1])} L{_n(q[0])} {_n(q[1])}"

        ince = _st(None, _NOTR)
        parca = []
        if tur == "ankastre":
            d = seg(P(-16, 0), P(16, 0)) + "".join(" " + seg(P(t, 0), P(t - 6, 9)) for t in (-12, -6, 0, 6, 12))
            parca.append(f'<path d="{d}" fill="none" {ince} stroke-width="1.8" stroke-linecap="round"/>')
            self.kapsa(*P(-16, 0), *P(16, 0))
            self.kapsa(*P(-18, 10), *P(18, 10))
        else:
            h = 14 if tur == "sabit" else 12
            nok = " ".join(f"{_n(p[0])},{_n(p[1])}" for p in (P(0, 0), P(-9, h), P(9, h)))
            parca.append(f'<polygon points="{nok}" {_st(_KART, _NOTR)} stroke-width="1.8" stroke-linejoin="round"/>')
            z = h if tur == "sabit" else h + 4
            d = seg(P(-15, z), P(15, z)) + "".join(" " + seg(P(t, z), P(t - 5, z + 6)) for t in (-10, -3, 4, 11))
            parca.append(f'<path d="{d}" fill="none" {ince} stroke-width="1.8" stroke-linecap="round"/>')
            self.kapsa(*P(-16, 0), *P(16, z + 7))
        self.orta.append(f'<g class="g{g}">' + "".join(parca) + "</g>")

    @staticmethod
    def zigzag(a, b):
        """Yay simgesi için kırık çizgi noktaları."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        uz = math.hypot(dx, dy)
        if uz < 8:
            return [a, b]
        tx, ty = dx / uz, dy / uz
        nx, ny = -ty, tx
        kol = min(14.0, uz * 0.18)
        orta = uz - 2 * kol
        tepe = max(2, min(7, int(orta / 14)))
        pts = [a, (a[0] + tx * kol, a[1] + ty * kol)]
        for k in range(2 * tepe):
            t = kol + orta * (k + 0.5) / (2 * tepe)
            sg = 1 if k % 2 == 0 else -1
            pts.append((a[0] + tx * t + nx * 7.0 * sg, a[1] + ty * t + ny * 7.0 * sg))
        pts += [(a[0] + tx * (uz - kol), a[1] + ty * (uz - kol)), b]
        return pts

    def dugum_noktalari(self, aile=None, opak=None):
        for i in range(len(self.M.dugumler)):
            self.daire(self.D(i), 4.5, aile=aile, sinif="g0")

    def dugum_numaralari(self, mesafe=15.0):
        """Düğüm numaralarını yapının merkezinden dışarıya doğru yazar."""
        for i, dg in enumerate(self.M.dugumler):
            X, Y = self.D(i)
            vx, vy = X - self.merkez[0], Y - self.merkez[1] - 8.0
            uz = math.hypot(vx, vy) or 1.0
            self.yazi(X + vx / uz * mesafe, Y + vy / uz * mesafe, str(dg.no), boyut=12, kalin=True, opak=0.85)

    def eleman_daireleri(self, yukari=False):
        """Eleman numaralarını orta noktada küçük daire içinde yazar (yukari: elemanın üstüne kaydırma, piksel)."""
        kayma = 24.0 if yukari is True else float(yukari or 0)
        for e in self.M.elemanlar:
            a, b = self.E(e)
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - kayma
            self.daire((mx, my), 9, aile="b", kalin=1.5, sinif="g3")
            self.yazi(mx, my, str(e.no), boyut=11, kalin=True)

    # --- çıktı -------------------------------------------------------------
    def svg(self, baslik, pay=14.0):
        k = self._e
        if k[0] == math.inf:
            k = [0.0, 0.0, 10.0, 10.0]
        x0, y0 = k[0] - pay, k[1] - pay
        w, h = k[2] - k[0] + 2 * pay, k[3] - k[1] + 2 * pay
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_n(x0)} {_n(y0)} {_n(w)} {_n(h)}" '
            f'width="{_n(w)}" height="{_n(h)}" style="max-width:100%;height:auto" '
            f'font-family="{_YAZI_AILESI}" font-size="13" role="img" aria-label="{_html.escape(baslik, quote=True)}">'
            + "".join(self.arka + self.orta + self.on) + "</svg>")


# ============================================================================
# Anlatım yardımcıları: tablo, etiketli matris, diyagram verisi, ölçek
# ============================================================================
def _tablo(basliklar, satirlar):
    """md tablosu (hücrelerde '|' ve '$' bulunmamalı)."""
    def h(x):
        return str(x).replace("|", "/")
    ust = "| " + " | ".join(h(b) for b in basliklar) + " |"
    ara = "|" + "|".join("---" for _ in basliklar) + "|"
    return "\n".join([ust, ara] + ["| " + " | ".join(h(x) for x in s) + " |" for s in satirlar])


def _etiketli(A, satir_et, sut_et=None):
    """Kenarlarında SD etiketleri olan matris (KaTeX array; \\bordermatrix kullanılmaz)."""
    sut_et = satir_et if sut_et is None else sut_et
    r, c = len(satir_et), len(sut_et)
    ust = " & ".join([""] + [rf"\scriptstyle {t}" for t in sut_et])
    govde = [" & ".join([rf"\scriptstyle {satir_et[i]}"] + [_L(A[i, j]) for j in range(c)]) for i in range(r)]
    return (r"\left[\begin{array}{c|" + "c" * c + "}" + ust + r" \\ \hline " + r" \\ ".join(govde)
            + r"\end{array}\right]")


def _etiketli_vek(v, satir_et):
    govde = r" \\ ".join(rf"\scriptstyle {satir_et[i]} & {_L(v[i])}" for i in range(len(satir_et)))
    return r"\left[\begin{array}{c|c}" + govde + r"\end{array}\right]"


def _yerel_etiketler(M, e):
    a, b = e.dno
    t = M.tip
    if t in ("yay", "cubuk"):
        return [rf"u_{{{a}}}", rf"u_{{{b}}}"]
    if t == "kafes":
        return [rf"\bar u_{{{a}}}", rf"\bar u_{{{b}}}"]
    if t == "kiris":
        return [rf"v_{{{a}}}", rf"\theta_{{{a}}}", rf"v_{{{b}}}", rf"\theta_{{{b}}}"]
    return [rf"\bar u_{{{a}}}", rf"\bar v_{{{a}}}", rf"\theta_{{{a}}}",
            rf"\bar u_{{{b}}}", rf"\bar v_{{{b}}}", rf"\theta_{{{b}}}"]


def _genel_etiketler(M, e):
    return [M.sd_tex[i] for i in e.dofs]


def _buyukluk(v):
    """Mutlak değer (sembolik ifadede eksi işareti çıkarılabiliyorsa işareti atar)."""
    return -v if _isaret_negatif(v) else v


def _sv_isaretli(x, basamak=None):
    s = _sv(x, basamak)
    return s if s.startswith("−") or s == "0" else "+" + s


def _guzel_olcek(x):
    """x'ten küçük ya da eşit en yakın 1-2-5 dizisi sayısı (ölçek çarpanı için)."""
    p = 10.0 ** math.floor(math.log10(x))
    m = x / p
    for t in (5.0, 2.0, 1.0):
        if m >= t:
            return t * p
    return p


def _ol_metin(x):
    return f"{x:g}"


def _kisa(v):
    """Yazı etiketi için kısa sayı (en çok 3 anlamlı basamak)."""
    return _sv(v, 3)


# --- diyagram verisi ---------------------------------------------------------
def _diyagram_hazirla(M, adet=20):
    """Her eleman için boyunca x, N, V, M dizileri (yapı işaret kuralı) ve uç/ekstremum değerleri.

    N çekme +; V(x) = f1 + q·x; M(x) = −m1 + f1·x + q·x²/2 (alt lif çekme +, yani 'sagging' +)."""
    tip, say = M.tip, M.sayisal
    for e in M.elemanlar:
        L = e.L
        e.ekst = None
        if tip in ("kiris", "cerceve"):
            if tip == "kiris":
                f1, m1, f2, m2, N = e.f[0], e.f[1], e.f[2], e.f[3], _sifir_degeri(M)
            else:
                f1, m1, f2, m2, N = e.f[1], e.f[2], e.f[4], e.f[5], -e.f[0]
            q = e.q
            xs = [float(L) * i / adet for i in range(adet + 1)] if say else [L * sp.Rational(i, adet) for i in range(adet + 1)]
            xe = None
            if q != 0:
                aday = -f1 / q
                g, gL = _gercek(aday), _gercek(L)
                if g is not None and gL is not None and 1e-9 * gL < g < gL * (1 - 1e-9):
                    xe = float(aday) if say else aday
                    xs = sorted(xs + [xe], key=float)
            V = [f1 + q * x for x in xs]
            Mo = [-m1 + f1 * x + q * x * x / 2 for x in xs]
            if not say:
                V = [_sade(v) if _gercek(v) is not None else sp.expand(v) for v in V]
                Mo = [_sade(v) if _gercek(v) is not None else sp.expand(v) for v in Mo]
            e.dx, e.dV, e.dM, e.dN = xs, V, Mo, [N] * len(xs)
            if xe is not None:
                e.ekst = (xe, Mo[xs.index(xe)])
            e.m_uc, e.v_uc = (-m1, m2), (f1, -f2)
            kM, kV = Mo[-1] - m2, V[-1] + f2
            if not say and _gercek(kM) is None:
                kM = sp.simplify(kM)
            if not say and _gercek(kV) is None:
                kV = sp.simplify(kV)
            e.kontrol = (kM, kV)
        else:
            z = _sifir_degeri(M)
            e.dx, e.dN, e.dV, e.dM = [z, L], [e.N, e.N], [z, z], [z, z]
            e.m_uc = e.v_uc = (z, z)
            e.kontrol = (z, z)


def _durum(M, e, nmax):
    if M.tip in ("kiris", "cerceve"):
        return "eğilme"
    v = _gercek(e.N)
    if v is None:
        if e.N == 0:
            return "sıfır"
        return "basınç" if _isaret_negatif(e.N) else "çekme"
    if abs(v) <= 1e-9 * max(nmax, 1e-300) or v == 0:
        return "sıfır"
    return "çekme" if v > 0 else "basınç"


# --- şekil değiştirmiş biçim (sayısal) ----------------------------------------
def _deplasman_ornekleri(M, e, adet=12):
    """[(taban (X, Y), yer değiştirme (dX, dY))]: elemanın 0..L boyunca dünya koordinatlarında örnekleri."""
    tip = M.tip
    a, b = M.dugumler[e.ia], M.dugumler[e.ib]
    xa, ya, xb, yb = float(a.x), float(a.y), float(b.x), float(b.y)
    L, c, s = float(e.L), float(e.c), float(e.s)
    ue = [float(v) for v in e.ue]
    dy = [float(v) for v in e.dyerel]
    cikti = []
    for k in range(adet + 1):
        xi = k / adet
        X, Y = xa + xi * (xb - xa), ya + xi * (yb - ya)
        if tip in ("yay", "cubuk"):
            d = ((1 - xi) * ue[0] + xi * ue[1], 0.0)
        elif tip == "kafes":
            d = ((1 - xi) * ue[0] + xi * ue[2], (1 - xi) * ue[1] + xi * ue[3])
        else:
            if tip == "kiris":
                u1, v1, t1, u2, v2, t2 = 0.0, dy[0], dy[1], 0.0, dy[2], dy[3]
            else:
                u1, v1, t1, u2, v2, t2 = dy
            n1, n2 = 1 - 3 * xi ** 2 + 2 * xi ** 3, L * (xi - 2 * xi ** 2 + xi ** 3)
            n3, n4 = 3 * xi ** 2 - 2 * xi ** 3, L * (-xi ** 2 + xi ** 3)
            vl = n1 * v1 + n2 * t1 + n3 * v2 + n4 * t2
            ul = (1 - xi) * u1 + xi * u2
            d = (ul * c - vl * s, ul * s + vl * c)
        cikti.append(((X, Y), d))
    return cikti


def _olcek_bul(M):
    xs = [float(g.x) for g in M.dugumler]
    ys = [float(g.y) for g in M.dugumler]
    boyut = max(max(xs) - min(xs), max(ys) - min(ys))
    um = 0.0
    for e in M.elemanlar:
        for _, d in _deplasman_ornekleri(M, e):
            um = max(um, math.hypot(*d))
    if um <= 0 or boyut <= 0:
        return 1.0
    return _guzel_olcek(0.1 * boyut / um)


# ============================================================================
# Anlatım adımları: metin, tablo, matris (şemalar sonraki bölümde)
# ============================================================================
def _basla(anl, no, baslik, ne):
    anl.baslik(f"{no}. Adım: {baslik}", 3)
    anl.metin("**Ne yapıyoruz, neden?** " + ne)


def _birimler(M):
    k, u = M.kuvvet, M.uzunluk
    return {"F": k, "L": u, "E": f"{k}/{u}²", "A": f"{u}²", "I": f"{u}⁴", "k": f"{k}/{u}", "q": f"{k}/{u}",
            "M": f"{k}·{u}", "Fx": k, "Fy": k, "sigma": f"{k}/{u}²"}


def _mesnet_turu(M, i):
    """(anahtar, açıklama): anahtar ankastre / sabit / kayici / donme (mesnet yoksa None)."""
    fl, t = M.mesnet[i], M.tip
    if not any(fl):
        return None, ""
    if t in ("yay", "cubuk"):
        return "ankastre", "sabit uç (u = 0)"
    if t == "kafes":
        if all(fl):
            return "sabit", "sabit (mafsallı) mesnet"
        return "kayici", ("yatay hareketi tutan kayıcı mesnet" if fl[0] else "düşey hareketi tutan kayıcı mesnet")
    if t == "kiris":
        if all(fl):
            return "ankastre", "ankastre mesnet (çökme ve dönme tutulu)"
        if fl[0]:
            return "sabit", "mafsallı ya da kayıcı mesnet (çökme tutulu, dönme serbest)"
        return "donme", "dönmeyi tutan mesnet"
    if all(fl):
        return "ankastre", "ankastre mesnet"
    if fl[0] and fl[1]:
        return "sabit", "sabit (mafsallı) mesnet"
    if fl[0] or fl[1]:
        return "kayici", ("yatay hareketi tutan kayıcı mesnet" if fl[0] else "düşey hareketi tutan kayıcı mesnet")
    return "donme", "dönmeyi tutan mesnet"


def _hesap_modu_notu(M):
    if M.sayisal:
        return (f"**Hesap modu: sayısal.** Model {M.n} serbestlik derecesi (SD) içerdiği için (eşik: {SD_ESIK}) hesap "
                "numpy ile ondalık sayılarla yapılır; tam matrisler yazılmaz, özet tablolar ve şemalar gösterilir.")
    ek = " Harfli (sembolik) büyüklükler olduğu gibi taşınır." if M.sembolik else ""
    return (f"**Hesap modu: kesin.** Model {M.n} SD içerdiği için (eşik: {SD_ESIK}) hesap sympy ile kesirli sayılarla "
            "yapılır; yuvarlama hatası yoktur." + ek)


def _adim_model(M, anl):
    t, b = M.tip, _birimler(M)
    anl.baslik(M.baslik, 2)
    _basla(anl, 1, "Modeli tanıyalım: veri tabloları",
           "Matris yöntemi yapıyı yalnızca dört tabloyla tanır: düğümler, elemanlar, mesnetler ve yükler. Hesaba "
           "girmeden önce bu tabloları bir arada görüyoruz; girdide bir hata varsa en ucuz burada yakalanır.")
    anl.metin(f"**Model türü:** {_TIP_AD[t]}. Düğüm başına {M.d} serbestlik derecesi (SD): "
              f"{', '.join(_SD_ADLARI[t])}; toplam {M.n} SD. **Birimler:** kuvvet {M.kuvvet}, uzunluk {M.uzunluk}.")
    anl.metin(_hesap_modu_notu(M))
    for u in M.uyarilar:
        anl.uyari(u)

    if t in ("yay", "cubuk"):
        ust = ["Düğüm", f"x [{M.uzunluk}]"]
        sat = [[dg.no, _metin(dg.x)] for dg in M.dugumler]
    else:
        ust = ["Düğüm", f"x [{M.uzunluk}]", f"y [{M.uzunluk}]"]
        sat = [[dg.no, _metin(dg.x), _metin(dg.y)] for dg in M.dugumler]
    anl.metin("**Düğümler**\n\n" + _tablo(ust, sat))

    ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]"] + (["θ"] if t in ("kafes", "cerceve") else []) \
        + [f"{p} [{b[p]}]" for p in _OZELLIK[t]]
    sat = []
    for e in M.elemanlar:
        satir = [e.no, f"{e.dno[0]} → {e.dno[1]}", _metin(e.L)]
        if t in ("kafes", "cerceve"):
            satir.append(f"{e.aci + 0.0:.2f}°")
        satir += [_metin(getattr(e, p)) for p in _OZELLIK[t]]
        sat.append(satir)
    anl.metin("**Elemanlar**\n\n" + _tablo(ust, sat))

    sat = []
    for i, dg in enumerate(M.dugumler):
        if any(M.mesnet[i]):
            tutulu = ", ".join(M.sd_et[M.d * i + j] for j in range(M.d) if M.mesnet[i][j])
            sat.append([dg.no, tutulu + " = 0", _mesnet_turu(M, i)[1]])
    anl.metin("**Mesnetler** (tutulu serbestlikler)\n\n" + _tablo(["Düğüm", "Tutulu SD", "Mesnet türü"], sat))

    ad = _BILESEN[t]
    ust = ["Düğüm"] + [f"{a} [{b[a]}]" for a in ad]
    sat = [[dg.no] + [_metin(M.yuk[i][j]) for j in range(M.d)]
           for i, dg in enumerate(M.dugumler) if any(v != 0 for v in M.yuk[i])]
    if sat:
        anl.metin("**Düğüm yükleri**\n\n" + _tablo(ust, sat))
    else:
        anl.metin("**Düğüm yükleri:** yok.")
    qs = [[e.no, _metin(e.q)] for e in M.elemanlar if e.q != 0]
    if qs:
        anl.metin(f"**Yayılı yükler** (elemanın yerel y yönünde düzgün yayılı)\n\n"
                  + _tablo(["Eleman", f"q [{b['q']}]"], qs)
                  + "\n\nYatay ve soldan sağa giden bir elemanda yerel y yukarıyı gösterir; bu yüzden aşağı doğru yük "
                    "**negatif** q ile girilir.")
    anl.metin("*İşaret kuralı:* x sağa, y yukarı pozitiftir; kuvvetler eksen yönünde pozitif, moment ve dönme "
              "saat yönünün tersine pozitiftir.")


def _adim_sd(M, anl):
    d, t = M.d, M.tip
    _basla(anl, 3, "Serbestlik dereceleri (SD) ve numaralandırma",
           "Matrislerin satır ve sütunlarına birer numara vermemiz gerekir. Her düğümün her hareket olasılığına "
           "(SD) sırayla bir numara veriyoruz; bundan sonra bu numaralar hep K matrisinin satır ve sütun numarası olacak.")
    anl.metin(f"Numaralama kuralı: \"dugumler\" listesindeki sırayla, her düğüme art arda {d} numara verilir "
              f"({', '.join(_SD_ADLARI[t])} sırasıyla). Listede i. sıradaki düğüm {d}(i−1)+1 … {d}i numaralarını alır. "
              "Python 0'dan saydığı için kodda her numaradan 1 çıkarılır.")
    ust = ["Düğüm", "SD numaraları (1'den)", "Python indisleri (0'dan)", "Tutulu mu?"]
    sat = []
    for i, dg in enumerate(M.dugumler):
        nolar = ", ".join(f"{M.sd_et[d * i + j]} = {d * i + j + 1}" for j in range(d))
        py = ", ".join(str(d * i + j) for j in range(d))
        tut = ", ".join(M.sd_et[d * i + j] for j in range(d) if M.mesnet[i][j]) or "hayır"
        sat.append([dg.no, nolar, py, tut])
    anl.metin(_tablo(ust, sat))
    sabit = [i + 1 for i in M.sabit]
    serbest = [i + 1 for i in M.serbest]
    anl.metin(f"**Tutulu SD'ler** (yer değiştirmesi sıfır, {len(sabit)} adet): {sabit}. "
              f"**Serbest SD'ler** (bilinmeyen, {len(serbest)} adet): {serbest}.")
    if M.n <= 12:
        vek = ", ".join(M.sd_tex)
    else:
        vek = ", ".join(M.sd_tex[:d * 2]) + r", \ldots, " + ", ".join(M.sd_tex[-d:])
    anl.mat(rf"\mathbf{{u}} = \left[{vek}\right]^T \quad\Rightarrow\quad \mathbf{{K}}:\ {M.n}\times{M.n},\qquad "
            rf"\mathbf{{F}}:\ {M.n}\times 1")


# --- Adım 4: eleman matrisleri ---------------------------------------------
def _yerel_k_formul(M):
    """Yerel eleman matrisinin harfli (formül) biçimi (LaTeX)."""
    t = M.tip
    if t == "yay":
        return r"\mathbf{k} = k\begin{bmatrix}1&-1\\-1&1\end{bmatrix}"
    if t in ("cubuk", "kafes"):
        return r"\mathbf{k} = \dfrac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}"
    if t == "kiris":
        return (r"\mathbf{k} = \dfrac{EI}{L^3}\begin{bmatrix}12&6L&-12&6L\\6L&4L^2&-6L&2L^2\\"
                r"-12&-6L&12&-6L\\6L&2L^2&-6L&4L^2\end{bmatrix}")
    return (r"\mathbf{k} = \begin{bmatrix}"
            r"\frac{EA}{L}&0&0&-\frac{EA}{L}&0&0\\"
            r"0&\frac{12EI}{L^3}&\frac{6EI}{L^2}&0&-\frac{12EI}{L^3}&\frac{6EI}{L^2}\\"
            r"0&\frac{6EI}{L^2}&\frac{4EI}{L}&0&-\frac{6EI}{L^2}&\frac{2EI}{L}\\"
            r"-\frac{EA}{L}&0&0&\frac{EA}{L}&0&0\\"
            r"0&-\frac{12EI}{L^3}&-\frac{6EI}{L^2}&0&\frac{12EI}{L^3}&-\frac{6EI}{L^2}\\"
            r"0&\frac{6EI}{L^2}&\frac{2EI}{L}&0&-\frac{6EI}{L^2}&\frac{4EI}{L}"
            r"\end{bmatrix}")


def _geometri_latex(M, e):
    t = M.tip
    ga, gb = M.dugumler[e.ia], M.dugumler[e.ib]
    a, b = e.dno
    dx = rf"{_Lp(gb.x)} - {_Lp(ga.x)}"
    dy = rf"{_Lp(gb.y)} - {_Lp(ga.y)}"
    if t in ("yay", "cubuk"):
        return rf"L = \left|x_{{{b}}} - x_{{{a}}}\right| = \left|{dx}\right| = {_L(e.L)}"
    if t == "kiris":
        return rf"L = x_{{{b}}} - x_{{{a}}} = {dx} = {_L(e.L)}"
    aci = f"{e.aci:.2f}"
    return (rf"L = \sqrt{{({dx})^2 + ({dy})^2}} = {_L(e.L)},\quad "
            rf"c = \cos\theta = \dfrac{{{dx}}}{{L}} = {_L(e.c)},\quad "
            rf"s = \sin\theta = \dfrac{{{dy}}}{{L}} = {_L(e.s)},\quad \theta = {aci}^{{\circ}}")


def _katsayi_denklemleri(M, e):
    """Rijitlik katsayılarının sayısal açılımı (EA/L, EI/L³ ...)."""
    t, L = M.tip, e.L
    sade = (lambda v: v) if M.sayisal else _sade
    sat = []
    if t == "yay":
        sat.append(rf"k = {_L(e.k)}\ \text{{{M.kuvvet}/{M.uzunluk}}}")
    if t in ("cubuk", "kafes", "cerceve"):
        ea = sade(e.E * e.A / L)
        sat.append(rf"\dfrac{{EA}}{{L}} = \dfrac{{{_Lp(e.E)}\cdot {_Lp(e.A)}}}{{{_Lp(L)}}} = {_L(ea)}")
    if t in ("kiris", "cerceve"):
        ei = sade(e.E * e.I / L ** 3)
        sat.append(rf"\dfrac{{EI}}{{L^3}} = \dfrac{{{_Lp(e.E)}\cdot {_Lp(e.I)}}}{{({_Lp(L)})^3}} = {_L(ei)}")
    return sat


def _T_formul(M):
    if M.tip == "kafes":
        return r"\begin{bmatrix} c & s & 0 & 0 \\ 0 & 0 & c & s \end{bmatrix}"
    return (r"\begin{bmatrix} c&s&0&0&0&0 \\ -s&c&0&0&0&0 \\ 0&0&1&0&0&0 \\ "
            r"0&0&0&c&s&0 \\ 0&0&0&-s&c&0 \\ 0&0&0&0&0&1 \end{bmatrix}")


def _eleman_ayrinti(M, anl, e):
    """Tek elemanın geometrisi, yerel matrisi, T'si ve global eleman matrisi."""
    t, no = M.tip, e.no
    a, b = e.dno
    yer, gen = _yerel_etiketler(M, e), _genel_etiketler(M, e)
    anl.metin(f"**Eleman {no}** (düğüm {a} → düğüm {b})")
    anl.mat(_geometri_latex(M, e))
    for denk in _katsayi_denklemleri(M, e):
        anl.mat(denk)
    if e.T is None:
        anl.metin("Yerel eksen global eksenle çakışık olduğu için dönüşüm gerekmez; yerel matris doğrudan "
                  "global eleman matrisidir. Satır ve sütun başlıkları o satırın hangi SD'ye ait olduğunu gösterir:")
        anl.mat(rf"\mathbf{{k}}^{{({no})}} = {_etiketli(e.k_yerel, yer)}")
        return
    anl.metin("Elemanın **kendi ekseninde (yerel)** yazılmış rijitlik matrisi:")
    anl.mat(rf"\mathbf{{k}}^{{({no})}}_{{\text{{yerel}}}} = {_etiketli(e.k_yerel, yer)}")
    anl.metin("Yerel yer değiştirmelerle global yer değiştirmeler arasındaki **dönüşüm matrisi** "
              "$\\mathbf{T}$ (sütunlar global SD'lere, satırlar yerel SD'lere karşılık gelir):")
    anl.mat(rf"\mathbf{{T}}^{{({no})}} = {_T_formul(M)} = {_etiketli(e.T, yer, gen)}")
    anl.metin("Global eksendeki eleman matrisi $\\mathbf{k}_e = \\mathbf{T}^T\\,\\mathbf{k}\\,\\mathbf{T}$:")
    anl.mat(rf"\mathbf{{k}}^{{({no})}}_e = \mathbf{{T}}^T\,\mathbf{{k}}\,\mathbf{{T}} = {_etiketli(e.ke, gen)}")


def _eleman_tablosu(M):
    """Büyük modellerde eleman özeti (md tablosu)."""
    t, b = M.tip, _birimler(M)
    sade = (lambda v: v) if M.sayisal else _sade
    if t == "yay":
        ust = ["Eleman", "Düğümler", f"k [{b['k']}]"]
    elif t == "cubuk":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", f"EA/L [{b['k']}]"]
    elif t == "kafes":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", "c", "s", f"EA/L [{b['k']}]"]
    elif t == "kiris":
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", f"EI/L³ [{b['F']}/{M.uzunluk}]"]
    else:
        ust = ["Eleman", "Düğümler", f"L [{M.uzunluk}]", "c", "s", "EA/L", "12EI/L³", "6EI/L²", "4EI/L"]
    sat = []
    for e in M.elemanlar:
        L = e.L
        satir = [e.no, f"{e.dno[0]} → {e.dno[1]}"]
        if t == "yay":
            satir.append(_metin(e.k))
        elif t == "cubuk":
            satir += [_metin(L), _metin(sade(e.E * e.A / L))]
        elif t == "kafes":
            satir += [_metin(L), _metin(e.c), _metin(e.s), _metin(sade(e.E * e.A / L))]
        elif t == "kiris":
            satir += [_metin(L), _metin(sade(e.E * e.I / L ** 3))]
        else:
            ei3 = sade(e.E * e.I / L ** 3)
            satir += [_metin(L), _metin(e.c), _metin(e.s), _metin(sade(e.E * e.A / L)), _metin(12 * ei3),
                      _metin(6 * ei3 * L), _metin(4 * ei3 * L * L)]
        sat.append(satir)
    return _tablo(ust, sat)


_ELEMAN_ACILIS = {
    "yay": ("Yapıyı elemanlara (parçalara) ayırıp her elemanı tek başına tanımlıyoruz. Bir elemanın **rijitlik matrisi**, "
            "\"elemanın uçlarını şu kadar oynatırsam uçlarında hangi kuvvetler doğar?\" sorusunun cevabıdır. "
            "Yay için bu cevap Hooke yasasıdır: kuvvet = k × uzama."),
    "cubuk": ("Yapıyı elemanlara ayırıp her elemanın **rijitlik matrisini** yazıyoruz: elemanın uçlarını oynatırsak "
              "uçlarında hangi kuvvetler doğar? Eksenel çubukta bu cevap Hooke yasasının çubuktaki karşılığıdır: "
              "kuvvet = (EA/L) × uzama."),
    "kafes": ("Kafes çubuğu yalnız **kendi ekseni boyunca** kuvvet taşır; oysa düğüm yer değiştirmelerini ortak $x$–$y$ "
              "eksenlerinde ($u$, $v$) tanımlıyoruz. Bu yüzden önce çubuğu kendi ekseninde (yerel) tanımlar, sonra bir "
              "**dönüşüm matrisi** $\\mathbf{T}$ ile global eksenlere çeviririz: $\\mathbf{k}_e=\\mathbf{T}^T\\mathbf{k}\\,\\mathbf{T}$."),
    "kiris": ("Kiriş elemanının her ucunda iki serbestlik vardır: çökme $v$ ve dönme $\\theta$. Rijitlik matrisi, bu dört "
              "serbestlikten birine birim yer değiştirme verip diğerlerini tuttuğumuzda uçlarda doğan kuvvet ve "
              "momentlerdir (Euler–Bernoulli kirişi). Yatay kirişte yerel eksen global eksenle aynıdır; dönüşüm gerekmez."),
    "cerceve": ("Çerçeve elemanı hem eksenel kuvvet hem eğilme taşır. Yerel $6\\times6$ matris eksenel ($EA/L$) ve eğilme "
                "($EI/L^3$) parçalarının birleşimidir; elemanın kendi ekseninde yazılır. Eleman eğik olabildiği için "
                "dönüşüm matrisi $\\mathbf{T}$ ile global eksenlere çevrilir: $\\mathbf{k}_e=\\mathbf{T}^T\\mathbf{k}\\,\\mathbf{T}$."),
}


def _adim_elemanlar(M, anl):
    t = M.tip
    _basla(anl, 4, "Eleman rijitlik matrisleri", _ELEMAN_ACILIS[t])
    anl.kural("Rijitlik matrisinin **$j$. sütunu**, $j$. serbestliğe birim yer değiştirme verilip diğerleri tutulduğunda "
              "elemanın uçlarında doğan kuvvetlerdir. Matris simetriktir ve sütunları toplandığında (rijit ötelenme) "
              "sıfır çıkar: eleman rijit cisim gibi hareket ederse içinde kuvvet doğmaz.")
    anl.mat(_yerel_k_formul(M))
    if t in ("kafes", "cerceve"):
        if t == "kafes":
            anl.metin("$c=\\cos\\theta$ ve $s=\\sin\\theta$; $\\theta$, $x$ ekseninden çubuğa saat yönünün tersine ölçülen açıdır. "
                      "Çubuğun yerel yer değiştirmesi $\\bar u = c\\,u + s\\,v$ olur (düğüm hareketinin çubuk eksenindeki izdüşümü).")
            anl.mat(r"\mathbf{k}_e = \dfrac{EA}{L}\begin{bmatrix} c^2 & cs & -c^2 & -cs \\ cs & s^2 & -cs & -s^2 \\ "
                    r"-c^2 & -cs & c^2 & cs \\ -cs & -s^2 & cs & s^2 \end{bmatrix}")
        else:
            anl.metin("$c=\\cos\\theta$ ve $s=\\sin\\theta$; $\\theta$, $x$ ekseninden eleman eksenine saat yönünün tersine ölçülen "
                      "açıdır. Yerel yer değiştirmeler $\\bar u = c\\,u + s\\,v$, $\\bar v = -s\\,u + c\\,v$ ve $\\theta$ (dönme eksen "
                      "takımından bağımsızdır).")
    if M.sayisal:
        anl.metin(f"Model büyük olduğundan ({M.n} SD) yalnız **ilk eleman** ayrıntılı gösterilir; hepsinin özeti aşağıdaki "
                  "tablodadır. Diğer elemanlar aynı adımlarla hesaplanır.")
        _eleman_ayrinti(M, anl, M.elemanlar[0])
        anl.metin("**Tüm elemanların özeti**\n\n" + _eleman_tablosu(M))
    else:
        for e in M.elemanlar:
            _eleman_ayrinti(M, anl, e)


# --- Adım 5: birleştirme ----------------------------------------------------
def _motor_bloklari(sonuc, anl):
    """Motor işlevinin anlatım bloklarını bizim anlatıma ekler: ilk başlık ve 'kod' blokları atılır."""
    bl = list(sonuc.anlatim.bloklar)
    if bl and bl[0][0] == "md" and bl[0][1].lstrip().startswith("#"):
        bl = bl[1:]
    for b in bl:
        if b[0] != "kod":
            anl.bloklar.append(b)


def _simetrik_mi(M, A):
    if M.sayisal:
        return bool(np.allclose(A, A.T, rtol=1e-9, atol=1e-9 * max(1.0, float(np.abs(A).max()))))
    return all(sp.simplify(x) == 0 for x in (A - A.T))


def _adim_birlestirme(M, anl):
    t = M.tip
    _basla(anl, 5, "Birleştirme (assembly): global K matrisi",
           "Elemanlar düğümlerde birbirine bağlıdır: bir düğümün hareketi o düğüme bağlı **bütün** elemanları etkiler. "
           "Bunu hesaba katmak için her eleman matrisini, kendi SD'lerinin global numaralarına karşılık gelen satır ve "
           "sütunlara **toplayarak** yapının tek bir rijitlik matrisini ($\\mathbf{K}$) kuruyoruz.")
    sat = []
    for e in M.elemanlar:
        sat.append([e.no, ", ".join(M.sd_et[i] for i in e.dofs), [i + 1 for i in e.dofs], e.dofs])
    anl.metin("**Her elemanın SD'leri hangi global satır/sütunlara denk geliyor?**\n\n"
              + _tablo(["Eleman", "Yerel SD sırası", "Global SD numaraları (1'den)", "Python indisleri (0'dan)"], sat))
    if [e.no for e in M.elemanlar] != list(range(1, len(M.elemanlar) + 1)):
        eslesme = ", ".join(f"{k}. = eleman {e.no}" for k, e in enumerate(M.elemanlar, start=1))
        anl.uyari(f"Aşağıdaki birleştirme anlatımında elemanlar listedeki sıralarıyla numaralanır: {eslesme}.")
    if not M.sayisal:
        elemanlar = [(e.ke, [i + 1 for i in e.dofs]) for e in M.elemanlar]
        r = mo.birlestir(elemanlar, M.n, ad="K", goster="yok")
        _motor_bloklari(r, anl)
    else:
        esik = 1e-12 * max(float(np.abs(M.K).max()), 1e-300)
        dolu = np.abs(M.K) > esik
        nz = int(dolu.sum())
        ii, jj = np.nonzero(dolu)
        bant = int(np.abs(ii - jj).max()) if nz else 0
        anl.metin(f"$\\mathbf{{K}}$ matrisi {M.n}×{M.n} boyutundadır ve tam olarak yazılmayacak. Yalnız aynı elemanda "
                  f"buluşan SD çiftleri sıfırdan farklıdır: {nz} terim dolu, doluluk oranı %{100.0 * nz / M.n ** 2:.1f}, "
                  f"yarı bant genişliği {bant}. Aşağıdaki **doluluk haritası** hangi terime hangi elemanın katkı verdiğini gösterir.")
        anl.sema("Doluluk haritası", _sema_doluluk(M))
        m = min(6, M.n)
        anl.metin(f"Örnek olarak $\\mathbf{{K}}$ matrisinin sol üst {m}×{m} köşesi:")
        anl.mat(rf"\mathbf{{K}}_{{1\ldots {m}}} = {_etiketli(M.K[:m, :m], M.sd_tex[:m])}")
    sim = _simetrik_mi(M, M.K)
    anl.metin(("**Sağlama:** $\\mathbf{K}$ simetriktir ($K_{ij}=K_{ji}$) ✔; her eleman matrisi simetrik olduğundan toplamı da öyledir. "
               if sim else "**Uyarı:** $\\mathbf{K}$ simetrik çıkmadı; eleman matrislerini denetleyin. ")
              + f"Henüz mesnet uygulanmadığı için $\\mathbf{{K}}$ **tekildir**: yapı hiç tutulmadan {_RIJIT_HAREKET[t]} "
                "bağımsız rijit cisim hareketi yapabilir (enerji harcamadan). Mesnetler bu hareketleri engelleyecek.")


# --- Adım 6: yük vektörü ------------------------------------------------------
def _feq_formul(M):
    if M.tip == "kiris":
        return (r"\mathbf{f}_{eq} = \int_0^L \mathbf{N}^T q\,dx = "
                r"\begin{bmatrix} qL/2 \\ qL^2/12 \\ qL/2 \\ -qL^2/12 \end{bmatrix}")
    return (r"\mathbf{f}_{eq} = \int_0^L \mathbf{N}^T q\,dx = "
            r"\begin{bmatrix} 0 \\ qL/2 \\ qL^2/12 \\ 0 \\ qL/2 \\ -qL^2/12 \end{bmatrix}")


def _adim_yukler(M, anl):
    t, d = M.tip, M.d
    yayili = [e for e in M.elemanlar if e.feq is not None]
    ac = ("Denklem takımının sağ tarafı yüklerdir. Her serbestlik derecesine (SD) karşılık gelen yük, $\\mathbf{F}$ "
          "vektörünün o SD'nin satırına yazılır. Düğüme etkiyen yükler olduğu gibi yazılır")
    ac += (", elemanın içine yayılmış yükler ise önce düğümlere aktarılır." if yayili else ".")
    _basla(anl, 6, "Yük vektörü F", ac)
    if yayili:
        anl.kural("$\\mathbf{K}\\mathbf{u}=\\mathbf{F}$ denklemi yalnız **düğümlerde** yazılır; bu yüzden eleman boyunca yayılı yük, "
                  "elemanın uçlarına **eşdeğer düğüm yükleri** olarak aktarılır: $\\mathbf{f}_{eq}=\\int_0^L \\mathbf{N}^T q\\,dx$ "
                  "($\\mathbf{N}$: şekil fonksiyonları). Düzgün $q$ için her uca $qL/2$ kuvvet ve $\\pm qL^2/12$ moment gelir "
                  "(ankastre uç tepkilerinin ters işaretlisi). Bu yalnız bir hesap kolaylığıdır: eleman içindeki gerçek $V$ ve "
                  "$M$ diyagramı 8. adımda $\\mathbf{f}_{eq}$ çıkarılarak düzeltilir.")
        anl.mat(_feq_formul(M))
        for e in yayili:
            yer = _yerel_etiketler(M, e)
            anl.metin(f"**Eleman {e.no}**: $q={_L(e.q)}\\ \\text{{{M.kuvvet}/{M.uzunluk}}}$, $L={_L(e.L)}\\ \\text{{{M.uzunluk}}}$ "
                      "(yerel $y$ yönünde; aşağı yönlü yük negatiftir).")
            anl.mat(rf"\mathbf{{f}}_{{eq}}^{{({e.no})}} = {_etiketli_vek(e.feq_yerel, yer)}")
            if e.T is not None:
                gen = _genel_etiketler(M, e)
                anl.metin("Eleman eğik ya da dönüşüm gerektiriyorsa eşdeğer yük global eksenlere çevrilir ($\\mathbf{T}^T\\mathbf{f}_{eq}$):")
                anl.mat(rf"\mathbf{{T}}^T\mathbf{{f}}_{{eq}}^{{({e.no})}} = {_etiketli_vek(e.feq, gen)}")
    fark = M.F - M.F_dugum
    sat = []
    for i in range(M.n):
        if M.F[i] != 0 or M.F_dugum[i] != 0:
            sat.append([f"{M.sd_et[i]} (SD {i + 1})", _metin(M.F_dugum[i]), _metin(fark[i]), _metin(M.F[i])])
    if sat:
        anl.metin("**$\\mathbf{F}$ vektörünün sıfırdan farklı satırları**\n\n"
                  + _tablo(["SD", "Düğüm yükü", "Yayılı yükten eşdeğer", "F toplam"], sat))
    else:
        anl.metin("Hiçbir yük tanımlanmadığı için $\\mathbf{F}=\\mathbf{0}$ (çözüm sıfır yer değiştirme verir).")
    b = _birimler(M)
    birim = f"Kuvvetler {M.kuvvet}" + (f", momentler {b['M']}" if t in ("kiris", "cerceve") else "") + " cinsindendir."
    if M.n <= 12:
        anl.mat(rf"\mathbf{{F}} = {_etiketli_vek(M.F, M.sd_tex)}")
        anl.metin(birim)
    else:
        anl.metin(f"$\\mathbf{{F}}$ vektörü {M.n} satırlıdır; yukarıdaki tabloda yalnız dolu satırlar gösterildi (kalan satırlar 0). {birim}")


# ============================================================================
# Şemalar: yapı modeli, doluluk haritası, sonuçlar
# ============================================================================
_YON_VEK = {"alt": (0.0, 1.0), "ust": (0.0, -1.0), "sol": (-1.0, 0.0), "sag": (1.0, 0.0)}


def _birim_vek(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    uz = math.hypot(dx, dy) or 1.0
    return dx / uz, dy / uz


def _don(v, derece):
    f = math.radians(derece)
    return v[0] * math.cos(f) - v[1] * math.sin(f), v[0] * math.sin(f) + v[1] * math.cos(f)


def _komsu_yonler(c, M, i):
    """Düğüme bağlı elemanların ekran birim vektörleri (düğümden uzağa doğru)."""
    cikti = []
    for e in M.elemanlar:
        if e.ia == i:
            cikti.append(_birim_vek(c.D(i), c.D(e.ib)))
        elif e.ib == i:
            cikti.append(_birim_vek(c.D(i), c.D(e.ia)))
    return cikti


def _bos_yon(dolu, adet=16):
    """Dolu yönlerden en uzak yönü seçer (eşitlikte yukarıdan başlayarak ilk bulunan)."""
    en = None
    for k in range(adet):
        f = math.pi / 2 + 2 * math.pi * k / adet
        v = (math.cos(f), -math.sin(f))
        mn = math.pi
        for d in dolu:
            mn = min(mn, math.acos(max(-1.0, min(1.0, v[0] * d[0] + v[1] * d[1]))))
        if en is None or mn > en[0] + 1e-9:
            en = (mn, v)
    return en[1]


def _f(v):
    g = _gercek(v)
    return 0.0 if g is None else g


def _mesnet_yonu(c, M, i, kom, ilk_kayan):
    """(simge türü, gövde yönü): modeldeki tutulu serbestliklere göre mesnet simgesi seçer."""
    t = M.tip
    tur, _ = _mesnet_turu(M, i)
    mx = sum(v[0] for v in kom)
    my = sum(v[1] for v in kom)
    if t in ("yay", "cubuk"):
        if len(kom) >= 2:
            return "sabit", "alt"
        return "ankastre", ("sol" if mx > 0 else "sag")
    if tur in ("ankastre", "donme"):
        if abs(mx) >= abs(my):
            return "ankastre", ("sol" if mx > 0 else "sag")
        return "ankastre", ("ust" if my > 0 else "alt")
    if t == "kiris":
        return ("sabit" if i == ilk_kayan else "kayici"), "alt"
    fl = M.mesnet[i]
    if tur == "kayici" and fl[0] and not fl[1]:
        return "kayici", ("sol" if mx > 0 else "sag")
    return tur, ("ust" if my > 0.5 else "alt")


def _mesnetleri_ciz(c, M, dolu):
    ilk = None
    if M.tip == "kiris":
        aday = [i for i, fl in enumerate(M.mesnet) if fl[0] and not fl[1]]
        if aday:
            ilk = min(aday, key=lambda i: float(M.dugumler[i].x))
    for i in range(len(M.dugumler)):
        if _mesnet_turu(M, i)[0] is None:
            continue
        X, Y = c.D(i)
        tur, yon = _mesnet_yonu(c, M, i, _komsu_yonler(c, M, i), ilk)
        c.mesnet(X, Y, tur, yon, g=1)
        v = _YON_VEK[yon]
        aci = 45 if tur == "ankastre" else 30
        dolu[i] += [v, _don(v, aci), _don(v, -aci)]


def _kuvvet_oku(c, M, X, Y, ad, v, aile, fmax, dolu, onek="", kom=()):
    """Düğümde tek bileşenli kuvvet/moment oku. Ok ucu düğüme yönelir; yazı kuyruğun ardındadır."""
    g = _gercek(v)
    neg = (g < 0) if g is not None else _isaret_negatif(v)
    if ad == "M":
        c.yay_ok((X, Y), 17, not neg, aile, g=2)
        c.yazi(X + 22, Y - 22, f"{onek}{_kisa(_buyukluk(v))} {M.kuvvet}·{M.uzunluk}", hiza="start", boyut=12)
        dolu.append((0.7, -0.7))
        return
    sg = -1.0 if neg else 1.0
    wx, wy = (1.0, 0.0) if ad == "Fx" else (0.0, 1.0)
    d = (sg * wx, -sg * wy)
    uz = 30.0 + 22.0 * abs(g) / fmax if (g is not None and fmax > 0) else 44.0
    # kuyruk elemanın üstüne düşüyorsa ok düğümden dışarıya doğru çizilir (kuyruk düğümde)
    cekme = any(-d[0] * m[0] - d[1] * m[1] > 0.8 for m in kom)
    if cekme:
        kuyruk = (X + d[0] * 6.0, Y + d[1] * 6.0)
        tip = (X + d[0] * (6.0 + uz), Y + d[1] * (6.0 + uz))
        uc = tip
        yon = d
    else:
        tip = (X - d[0] * 6.0, Y - d[1] * 6.0)
        kuyruk = (X - d[0] * (6.0 + uz), Y - d[1] * (6.0 + uz))
        uc = kuyruk
        yon = (-d[0], -d[1])
    c.ok(kuyruk, tip, aile, g=2)
    metin = f"{onek}{_kisa(_buyukluk(v))} {M.kuvvet}"
    if abs(yon[0]) > 0.5:
        c.yazi(uc[0] + yon[0] * 6.0, uc[1], metin, hiza=("start" if yon[0] > 0 else "end"), boyut=12)
    else:
        c.yazi(uc[0], uc[1] + yon[1] * 12.0, metin, boyut=12)
    dolu.append(yon if not cekme else (d[0], d[1]))


def _fmax(M):
    degerler = [abs(_f(M.yuk[i][j])) for i in range(len(M.dugumler)) for j, ad in enumerate(_BILESEN[M.tip]) if ad != "M"]
    return max(degerler or [0.0])


def _yukleri_ciz(c, M, dolu):
    t = M.tip
    fmax = _fmax(M)
    for i in range(len(M.dugumler)):
        X, Y = c.D(i)
        for j, ad in enumerate(_BILESEN[t]):
            v = M.yuk[i][j]
            if v != 0:
                _kuvvet_oku(c, M, X, Y, ad, v, "b", fmax, dolu[i], kom=_komsu_yonler(c, M, i))
    for e in M.elemanlar:
        if e.q == 0:
            continue
        a, b = c.E(e)
        n = (-float(e.s), -float(e.c))
        neg = (_f(e.q) < 0) if _gercek(e.q) is not None else _isaret_negatif(e.q)
        d = (-n[0], -n[1]) if neg else n
        uzp = math.hypot(b[0] - a[0], b[1] - a[1])
        adet = max(3, int(round(uzp / 26.0)))
        kuy = []
        for k in range(adet):
            r = (k + 0.5) / adet
            p = (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r)
            kp = (p[0] - d[0] * 26.0, p[1] - d[1] * 26.0)
            c.ok(kp, (p[0] - d[0] * 3.0, p[1] - d[1] * 3.0), "b", g=2, kalin=1.8, uc=6.0)
            kuy.append(kp)
        c.cizgi(kuy[0], kuy[-1], "b", kalin=1.8, sinif="g2")
        orta = ((kuy[0][0] + kuy[-1][0]) / 2, (kuy[0][1] + kuy[-1][1]) / 2)
        c.yazi(orta[0] - d[0] * 13.0, orta[1] - d[1] * 13.0, f"q = {_kisa(_buyukluk(e.q))} {M.kuvvet}/{M.uzunluk}", boyut=12)
        dolu[e.ia].append((-d[0], -d[1]))
        dolu[e.ib].append((-d[0], -d[1]))


def _dugum_numaralari_yaz(c, M, dolu):
    for i, dg in enumerate(M.dugumler):
        X, Y = c.D(i)
        v = _bos_yon(dolu[i] + _komsu_yonler(c, M, i))
        c.yazi(X + v[0] * 15.0, Y + v[1] * 15.0, str(dg.no), boyut=12, kalin=True, opak=0.9)


def _birinci_boyut(M):
    return M.tip in ("yay", "cubuk")


def _cubuk_yuksekligi(M, e):
    amax = max((_f(x.A) for x in M.elemanlar), default=0.0)
    a = _gercek(e.A)
    return 24.0 if (a is None or amax <= 0) else 14.0 + 22.0 * a / amax


def _birinci_boyut_elemanlar(c, M):
    for e in M.elemanlar:
        a, b = c.E(e)
        if M.tip == "yay":
            c.yol(c.zigzag(a, b), None, kalin=2.0, sinif="g0")
        else:
            h = _cubuk_yuksekligi(M, e)
            c.dikdortgen(min(a[0], b[0]), a[1] - h / 2, abs(b[0] - a[0]), h, aile="a", sinif="g0")
    for e in M.elemanlar:
        a, b = c.E(e)
        mx = (a[0] + b[0]) / 2
        if M.tip == "yay":
            etiket = f"k = {_kisa(e.k)}"
        else:
            etiket = f"EA = {_kisa(e.E * e.A)}"
        c.yazi(mx, a[1] + (28.0 if M.tip == "yay" else _cubuk_yuksekligi(M, e) / 2 + 14.0), etiket, boyut=11, opak=0.85)


def _sema_yapi(M):
    """İki kare: (1) çizilmiş yapı, (2) serbestlik derecesi numaraları."""
    kareler = []
    # --- kare 1: yapı ---
    c = _Cizim(M)
    dolu = {i: [] for i in range(len(M.dugumler))}
    if _birinci_boyut(M):
        _birinci_boyut_elemanlar(c, M)
    else:
        for e in M.elemanlar:
            c.cizgi(*c.E(e), None, kalin=3.0, sinif="g0")
    _mesnetleri_ciz(c, M, dolu)
    _yukleri_ciz(c, M, dolu)
    c.dugum_noktalari()
    c.eleman_daireleri(yukari=(24 if M.tip == "yay" else 34) if _birinci_boyut(M) else False)
    _dugum_numaralari_yaz(c, M, dolu)
    sat = f"Düğüm numarası: yazı · eleman numarası: daire · birimler {M.kuvvet}, {M.uzunluk}"
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, sat, boyut=11, opak=0.8)
    kareler.append({"baslik": "Yapı: düğümler, elemanlar, mesnetler, yükler", "svg": c.svg("Yapı modeli")})
    # --- kare 2: SD numaraları ---
    c = _Cizim(M)
    for e in M.elemanlar:
        c.cizgi(*c.E(e), None, kalin=2.2, sinif="g0", opak=0.3)
    d, t = M.d, M.tip
    for i, dg in enumerate(M.dugumler):
        X, Y = c.D(i)
        for j, ad in enumerate(_SD_ADLARI[t]):
            k = d * i + j
            aile = "sil" if M.mesnet[i][j] else "a"
            if ad == "θ":
                c.yay_ok((X, Y), 22, True, aile, g=2, kalin=1.8, bas=110.0, son=340.0)
                ax, ay = X + 33.0 * math.cos(math.radians(225)), Y - 33.0 * math.sin(math.radians(225))
                c.yazi(ax, ay, str(k + 1), boyut=12, kalin=True, aile=aile)
            elif (t in ("yay", "cubuk", "kafes", "cerceve")) and ad == "u":
                c.ok((X + 12.0, Y), (X + 48.0, Y), aile, g=2, kalin=1.8)
                c.yazi(X + 58.0, Y, str(k + 1), boyut=12, kalin=True, aile=aile)
            else:
                c.ok((X, Y - 12.0), (X, Y - 48.0), aile, g=2, kalin=1.8)
                c.yazi(X, Y - 59.0, str(k + 1), boyut=12, kalin=True, aile=aile)
        c.daire((X, Y), 10, aile=None, sinif="g0")
        c.yazi(X, Y, str(dg.no), boyut=11, kalin=True)
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0,
           "ok yanındaki sayı = SD numarası · mavi: serbest, kırmızı: tutulu", boyut=11, opak=0.8)
    kareler.append({"baslik": "Serbestlik dereceleri (SD) numaraları", "svg": c.svg("Serbestlik dereceleri")})
    return kareler


# --- doluluk haritası (sayısal mod) -----------------------------------------
def _hucre_ciz(c, x, y, w, h, aile, sinif="g0", opak=0.85):
    c.orta.append(f'<rect class="{sinif}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" rx="1" '
                  f'style="fill:{_AILE[aile][1]};fill-opacity:{opak}"/>')
    c.kapsa(x, y, x + w, y + h)


def _matris_haritasi(M, idx, cnt, baslik, bant=(), vurgu=False):
    c = _Cizim(M)
    m = len(idx)
    nb = min(m, 60)
    blk = -(-m // nb)
    nb = -(-m // blk)
    cs = max(3.0, min(14.0, 300.0 / nb))
    x0, y0 = 34.0, 22.0
    gen = nb * cs
    c.cizgi((x0, y0), (x0 + gen, y0), "n", kalin=1.2, sinif="g0")
    c.cizgi((x0, y0 + gen), (x0 + gen, y0 + gen), "n", kalin=1.2, sinif="g0")
    c.cizgi((x0, y0), (x0, y0 + gen), "n", kalin=1.2, sinif="g0")
    c.cizgi((x0 + gen, y0), (x0 + gen, y0 + gen), "n", kalin=1.2, sinif="g0")
    for s in bant:
        p = s // blk
        c.arka.append(f'<rect class="g1" x="{_n(x0)}" y="{_n(y0 + p * cs)}" width="{_n(gen)}" height="{_n(cs)}" '
                      f'{_st(_AILE["sil"][0], None)}/>')
        c.arka.append(f'<rect class="g1" x="{_n(x0 + p * cs)}" y="{_n(y0)}" width="{_n(cs)}" height="{_n(gen)}" '
                      f'{_st(_AILE["sil"][0], None)}/>')
    for bi in range(nb):
        for bj in range(nb):
            alt = cnt[np.ix_(idx[bi * blk:(bi + 1) * blk], idx[bj * blk:(bj + 1) * blk])]
            mx = int(alt.max()) if alt.size else 0
            if mx > 0:
                _hucre_ciz(c, x0 + bj * cs, y0 + bi * cs, cs - 0.6, cs - 0.6, "a" if mx == 1 else "b")
    adim = max(1, nb // 10)
    for p in range(0, nb, adim):
        no = str(idx[p * blk] + 1)
        c.yazi(x0 + (p + 0.5) * cs, y0 - 9.0, no, boyut=10, opak=0.8)
        c.yazi(x0 - 6.0, y0 + (p + 0.5) * cs, no, hiza="end", boyut=10, opak=0.8)
    if vurgu:
        c.on.append(f'<rect class="vurgu" rx="6" x="{_n(x0 - 4)}" y="{_n(y0 - 4)}" width="{_n(gen + 8)}" '
                    f'height="{_n(gen + 8)}" fill="none" {_st(None, _AILE["c"][1])} stroke-width="2.5"/>')
        c.kapsa(x0 - 4, y0 - 4, x0 + gen + 4, y0 + gen + 4)
    sat1 = ("mavi: tek elemanın katkısı · sarı: birden çok eleman toplanır" if not vurgu
            else "yeşil çerçeve: çözülecek indirgenmiş matris")
    c.yazi(x0 + gen / 2, y0 + gen + 20.0, sat1, boyut=11, opak=0.8)
    if bant:
        c.yazi(x0 + gen / 2, y0 + gen + 36.0, "kırmızı bant: tutulu SD'nin satır ve sütunu", boyut=11, opak=0.8)
    if blk > 1:
        c.yazi(x0 + gen / 2, y0 + gen + (52.0 if bant else 36.0), f"her hücre {blk}×{blk} SD bloğu", boyut=11, opak=0.8)
    return {"baslik": baslik, "svg": c.svg("Doluluk haritası")}


def _sema_doluluk(M):
    n = M.n
    cnt = np.zeros((n, n), dtype=int)
    for e in M.elemanlar:
        for I in e.dofs:
            for J in e.dofs:
                cnt[I, J] += 1
    kareler = [_matris_haritasi(M, list(range(n)), cnt, "K matrisinin dolu terimleri", bant=M.sabit)]
    if M.serbest:
        kareler.append(_matris_haritasi(M, list(M.serbest), cnt, "Mesnet satır/sütunları atıldıktan sonra", vurgu=True))
    return kareler


# --- sonuç şemaları -----------------------------------------------------------
def _dugum_yer_degistirme(M, i):
    d, t, u = M.d, M.tip, M.u
    if t in ("yay", "cubuk"):
        return float(u[i]), 0.0
    if t == "kiris":
        return 0.0, float(u[d * i])
    return float(u[d * i]), float(u[d * i + 1])


def _gorunum_sonuc(M):
    """Sonuç karelerinin hepsi aynı ölçüde çizilsin diye ortak çizim nesnesi üretir."""
    return _Cizim(M)


def _sekil_kare(M, dolu):
    c = _Cizim(M)
    sc = _olcek_bul(M)
    _mesnetleri_ciz(c, M, dolu)
    if _birinci_boyut(M):
        kayma = 70.0
        for i in range(len(M.dugumler)):
            X, Y = c.D(i)
            dx, _ = _dugum_yer_degistirme(M, i)
            X2 = c.P(float(M.dugumler[i].x) + sc * dx, 0.0)[0]
            c.cizgi((X, Y), (X, Y + kayma - 6), "n", kalin=1.0, sinif="g0", kesik="3 3", opak=0.7)
            c.daire((X2, Y + kayma), 4.5, aile="a", sinif="g4")
            if abs(dx) > 0:
                c.yazi(X2, Y + kayma + 20.0, f"{M.sd_et[i]} = {_kisa(M.u[i])}", boyut=11)
        for e in M.elemanlar:
            a, b = c.E(e)
            c.cizgi(a, b, "n", kalin=1.6, sinif="g0", kesik="5 4", opak=0.8)
            pa = c.P(float(M.dugumler[e.ia].x) + sc * _dugum_yer_degistirme(M, e.ia)[0], 0.0)
            pb = c.P(float(M.dugumler[e.ib].x) + sc * _dugum_yer_degistirme(M, e.ib)[0], 0.0)
            c.yol([(pa[0], pa[1] + kayma), (pb[0], pb[1] + kayma)], "a", kalin=3.0, sinif="g4", animasyon=True)
    else:
        for e in M.elemanlar:
            c.cizgi(*c.E(e), "n", kalin=1.6, sinif="g0", kesik="5 4", opak=0.8)
        for e in M.elemanlar:
            pts = [c.P(X + sc * dX, Y + sc * dY) for (X, Y), (dX, dY) in _deplasman_ornekleri(M, e)]
            c.yol(pts, "a", kalin=2.8, sinif="g4", animasyon=True)
        for i, dg in enumerate(M.dugumler):
            dX, dY = _dugum_yer_degistirme(M, i)
            c.daire(c.P(float(dg.x) + sc * dX, float(dg.y) + sc * dY), 3.8, aile="a", sinif="g4")
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"kesikli: ilk durum · mavi: şekil değiştirmiş (×{_ol_metin(sc)} büyütülmüş)",
           boyut=11, opak=0.8)
    return {"baslik": "Şekil değiştirmiş biçim", "svg": c.svg("Şekil değiştirmiş biçim")}


def _normal_kare(M):
    """yay / çubuk / kafes: eleman eksenel kuvvetleri (çekme mavi, basınç kırmızı, kalınlık |N| ile orantılı)."""
    c = _Cizim(M)
    nmax = max((abs(_f(e.N)) for e in M.elemanlar), default=0.0)
    xs = [p for i in range(len(M.dugumler)) for p in [c.D(i)]]
    mx0 = sum(p[0] for p in xs) / len(xs)
    my0 = sum(p[1] for p in xs) / len(xs)
    for e in M.elemanlar:
        a, b = c.E(e)
        n = _f(e.N)
        if nmax <= 0 or abs(n) <= 1e-9 * nmax:
            aile, kalin = "n", 2.0
        else:
            aile, kalin = ("a" if n > 0 else "sil"), 2.5 + 5.0 * abs(n) / nmax
        c.yol([a, b], aile, kalin=kalin, sinif="g4", animasyon=True)
        t = _birim_vek(a, b)
        nv = (t[1], -t[0])
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if _birinci_boyut(M):
            nv = (0.0, -1.0)
        elif nv[0] * (mid[0] - mx0) + nv[1] * (mid[1] - my0) < 0:
            nv = (-nv[0], -nv[1])
        c.yazi(mid[0] + nv[0] * 14.0, mid[1] + nv[1] * 14.0, _kisa(e.N), boyut=12, kalin=True)
    c.dugum_noktalari()
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"N [{M.kuvvet}] · mavi: çekme (+) · kırmızı: basınç (−)", boyut=11, opak=0.8)
    return {"baslik": "Eksenel kuvvet N", "svg": c.svg("Eksenel kuvvet")}


def _kesit_kare(M, tur):
    """kiris / cerceve: N, V ya da M diyagramı (M, çekme tarafına çizilir)."""
    anahtar = {"N": "dN", "V": "dV", "M": "dM"}[tur]
    vmax = max((abs(_f(v)) for e in M.elemanlar for v in getattr(e, anahtar)), default=0.0)
    if vmax <= 1e-12:
        return None
    c = _Cizim(M)
    ol = 46.0 / vmax
    isaret = -1.0 if tur == "M" else 1.0
    yerlesen = []
    for e in M.elemanlar:
        a, b = c.E(e)
        Lp = math.hypot(b[0] - a[0], b[1] - a[1])
        t = _birim_vek(a, b)
        d = (isaret * -float(e.s), isaret * -float(e.c))
        L = _f(e.L)
        deger = [_f(v) for v in getattr(e, anahtar)]
        xs = [_f(x) for x in e.dx]
        taban = [(a[0] + t[0] * Lp * x / L, a[1] + t[1] * Lp * x / L) for x in xs]
        tepe = [(p[0] + d[0] * v * ol, p[1] + d[1] * v * ol) for p, v in zip(taban, deger)]
        parcalar, cur = [], [(taban[0], tepe[0], deger[0])]
        for k in range(1, len(xs)):
            v0, v1 = deger[k - 1], deger[k]
            if v0 * v1 < 0:
                r = v0 / (v0 - v1)
                z = (taban[k - 1][0] + (taban[k][0] - taban[k - 1][0]) * r, taban[k - 1][1] + (taban[k][1] - taban[k - 1][1]) * r)
                cur.append((z, z, 0.0))
                parcalar.append(cur)
                cur = [(z, z, 0.0)]
            cur.append((taban[k], tepe[k], v1))
        parcalar.append(cur)
        for pr in parcalar:
            isr = sum(p[2] for p in pr)
            aile = "a" if isr >= 0 else "sil"
            c.poligon([p[0] for p in pr] + [p[1] for p in reversed(pr)], aile, sinif="g3", katman="arka")
            c.yol([p[1] for p in pr], aile, kalin=2.2, sinif="g4", animasyon=True)
        c.cizgi(a, b, None, kalin=2.4, sinif="g0")
        for p, q in ((taban[0], tepe[0]), (taban[-1], tepe[-1])):
            c.cizgi(p, q, "n", kalin=1.0, sinif="g3")
        adaylar = [(0, deger[0]), (len(xs) - 1, deger[-1])]
        if tur == "M" and e.ekst is not None:
            xe, me = _f(e.ekst[0]), _f(e.ekst[1])
            adaylar.append((min(range(len(xs)), key=lambda k: abs(xs[k] - xe)), me))
        for k, v in adaylar:
            if abs(v) <= 1e-9 * vmax:
                continue
            sg = 1.0 if v > 0 else -1.0
            pos = (tepe[k][0] + d[0] * sg * 12.0, tepe[k][1] + d[1] * sg * 12.0)
            if any(math.hypot(pos[0] - q[0], pos[1] - q[1]) < 16.0 for q in yerlesen):
                continue
            yerlesen.append(pos)
            c.yazi(pos[0], pos[1], _kisa(v), boyut=12, kalin=True)
    c.dugum_noktalari()
    birim = f"{M.kuvvet}·{M.uzunluk}" if tur == "M" else M.kuvvet
    ek = " · çekme tarafına çizilir" if tur == "M" else ""
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, f"{tur} [{birim}] · mavi: + · kırmızı: −{ek}", boyut=11, opak=0.8)
    ad = {"N": "Eksenel kuvvet N diyagramı", "V": "Kesme kuvveti V diyagramı", "M": "Eğilme momenti M diyagramı"}[tur]
    return {"baslik": ad, "svg": c.svg(ad)}


def _tepki_kare(M, dolu):
    c = _Cizim(M)
    d, t = M.d, M.tip
    for e in M.elemanlar:
        c.cizgi(*c.E(e), None, kalin=2.6, sinif="g0", opak=0.55)
    _yukleri_ciz(c, M, dolu)
    olcek = max((abs(_f(M.R_tam[d * i + j])) for i, fl in enumerate(M.mesnet) for j, f in enumerate(fl)
                 if f and _BILESEN[t][j] != "M"), default=0.0)
    esik = 1e-9 * max(olcek, 1e-300)
    ad_r = {"Fx": "Rx", "Fy": "Ry", "M": "Mz"}
    for i, fl in enumerate(M.mesnet):
        X, Y = c.D(i)
        for j, f in enumerate(fl):
            if not f:
                continue
            v = M.R_tam[d * i + j]
            if abs(_f(v)) <= esik and _gercek(v) is not None:
                continue
            _kuvvet_oku(c, M, X, Y, _BILESEN[t][j], v, "c", olcek, dolu[i], onek=ad_r[_BILESEN[t][j]] + " = ",
                       kom=_komsu_yonler(c, M, i))
    c.dugum_noktalari()
    c.yazi((c._e[0] + c._e[2]) / 2, c._e[3] + 22.0, "yeşil: mesnet tepkileri · sarı: dış yükler", boyut=11, opak=0.8)
    return {"baslik": "Mesnet tepkileri", "svg": c.svg("Mesnet tepkileri")}


def _sema_sonuc(M):
    """Sonuç şemaları; harfli (sembolik) modellerde sayısal değer olmadığından boş liste döner."""
    if M.sembolik:
        return []
    t = M.tip
    dolu = {i: [] for i in range(len(M.dugumler))}
    kareler = [_sekil_kare(M, dolu)]
    if t in ("yay", "cubuk", "kafes"):
        kareler.append(_normal_kare(M))
    else:
        for tur in (("N", "V", "M") if t == "cerceve" else ("V", "M")):
            k = _kesit_kare(M, tur)
            if k is not None:
                kareler.append(k)
    dolu2 = {i: [] for i in range(len(M.dugumler))}
    kareler.append(_tepki_kare(M, dolu2))
    return kareler


def _adim_sema_model(M, anl):
    _basla(anl, 2, "Yapı modeli: şekil üzerinde",
           "Tablolar tam ama soyuttur. Aynı bilgiyi çizerek, modelin gerçekten kafamızdaki yapı olup olmadığını denetliyoruz: "
           "yanlış bağlanmış bir düğüm ya da ters yönlü bir yük şekilde hemen göze çarpar. İkinci karede her düğümün hangi "
           "serbestlik derecelerine (SD) hangi numarayı aldığını görüyoruz.")
    anl.metin("*Okuma kılavuzu:* düğüm numaraları yazıyla, eleman numaraları dairenin içinde gösterilir; sarı oklar yüklerdir, "
              "taralı simgeler mesnetlerdir. İkinci karede **mavi** oklar serbest, **kırmızı** olanlar tutulu (mesnetli) SD'leri gösterir.")
    anl.sema("Yapı modeli", _sema_yapi(M))


# ============================================================================
# Adım 7: sınır koşulları ve çözüm
# ============================================================================
def _hucre(M, x):
    """Tablo hücresi: sayı (ondalık); kesin modda kesirli bir sayıysa yanına p/q eklenir."""
    s = _metin(x)
    if not M.sayisal and not mo.ayarlar.ondalik:
        y = sp.sympify(x)
        if y.is_Rational and not y.is_Integer:
            s += f" ({y.p}/{y.q})"
    return s


def _sd_birimi(M, ad):
    return "rad" if ad == "θ" else M.uzunluk


def _kuvvet_olcegi(M):
    v = [abs(_gercek(x)) for x in list(M.F) + list(M.R_tam) if _gercek(x) is not None]
    return max([1.0] + v)


def _sifir_mi(M, x, olcek=1.0):
    v = _gercek(x)
    if v is None:
        return sp.simplify(x) == 0
    return abs(v) <= 1e-9 * max(olcek, 1e-300)


def _yer_degistirme_tablosu(M):
    t, d = M.tip, M.d
    ust = ["Düğüm"] + [f"{a} [{_sd_birimi(M, a)}]" for a in _SD_ADLARI[t]]
    sat = []
    for i, dg in enumerate(M.dugumler):
        sat.append([dg.no] + [_hucre(M, M.u[d * i + j]) for j in range(d)])
    kesik = ""
    if len(sat) > 30:
        sat = sat[:30]
        kesik = f"\n\n*(İlk 30 düğüm gösterildi; tümü `veri[\"dugumler\"]` içindedir.)*"
    return _tablo(ust, sat) + kesik


def _tepki_tablosu(M):
    t, d = M.tip, M.d
    ad_r = {"Fx": "Rx", "Fy": "Ry", "M": "Rm"}
    if t in ("yay", "cubuk"):
        ad_r = {"Fx": "R"}
    birim = {"Fx": M.kuvvet, "Fy": M.kuvvet, "M": f"{M.kuvvet}·{M.uzunluk}"}
    ust = ["Düğüm"] + [f"{ad_r[b]} [{birim[b]}]" for b in _BILESEN[t]]
    sat = []
    for i, dg in enumerate(M.dugumler):
        if any(M.mesnet[i]):
            sat.append([dg.no] + [(_hucre(M, M.R_tam[d * i + j]) if M.mesnet[i][j] else "—") for j in range(d)])
    return _tablo(ust, sat)


def _adim_cozum(M, anl):
    t, d = M.tip, M.d
    _basla(anl, 7, "Sınır koşulları ve çözüm",
           "Mesnetsiz yapının $\\mathbf{K}$ matrisi tekildir (yapı rijit cisim gibi kayabilir), bu yüzden "
           "$\\mathbf{K}\\mathbf{u}=\\mathbf{F}$ tek başına çözülemez. Mesnetler bazı SD'lerin yer değiştirmesini sıfıra "
           "bağlar; bu bilinen değerleri denklemden çıkarıp yalnız **bilinmeyen** (serbest) SD'ler için küçük bir sistem "
           "çözüyoruz. Sonra tutulu SD'lerdeki denge artığından **mesnet tepkilerini** buluyoruz.")
    sabit1 = [i + 1 for i in M.sabit]
    serbest1 = [i + 1 for i in M.serbest]
    if M.sabit:
        sat = [[i + 1, M.sd_et[i], M.dugumler[i // d].no] for i in M.sabit]
        anl.metin("**Tutulu SD'ler** (mesnet; yer değiştirme = 0)\n\n" + _tablo(["SD no", "SD", "Düğüm"], sat))
    anl.metin(f"Tutulu SD'ler: {sabit1}. Serbest (bilinmeyen) SD'ler: {serbest1 or 'yok'}. "
              f"İndirgenmiş sistemin boyutu {len(M.serbest)}×{len(M.serbest)}.")
    if not M.serbest:
        anl.metin("Bütün SD'ler tutulu olduğundan bilinmeyen yer değiştirme yoktur ($\\mathbf{u}=\\mathbf{0}$); mesnet tepkileri "
                  "yalnız yüklerin karşılığıdır: $\\mathbf{R}=-\\mathbf{F}$.")
    elif not M.sayisal:
        anl.metin("Aşağıda motorun Gauss yok etme anlatımı vardır: tutulu satır/sütunlar atılır, indirgenmiş sistem çözülür, "
                  "tepkiler $\\mathbf{R}=\\mathbf{K}\\mathbf{u}-\\mathbf{F}$ ile bulunur.")
        try:
            r = mo.sinir_kosulu(M.K, M.F, sabit=sabit1, goster="yok")
            _motor_bloklari(r, anl)
        except MatrisHatasi as e:  # pragma: no cover (mekanizma denetimi daha önce yapıldı)
            anl.uyari(f"Ayrıntılı çözüm anlatımı oluşturulamadı: {e}")
    else:
        m = len(M.serbest)
        Ks = M.K[np.ix_(M.serbest, M.serbest)]
        Fs = M.F[M.serbest]
        us = M.u[M.serbest]
        kosul = float(np.linalg.cond(Ks))
        art = float(np.abs(Ks @ us - Fs).max())
        anl.metin(f"Tutulu {len(M.sabit)} SD'nin satır ve sütunları $\\mathbf{{K}}$'dan atılır; kalan "
                  f"$\\mathbf{{K}}_s$ ({m}×{m}) simetrik ve pozitif tanımlıdır. Sistem "
                  f"$\\mathbf{{K}}_s\\mathbf{{u}}_s=\\mathbf{{F}}_s$ `numpy.linalg.solve` ile (LU ayrışımı) çözülür. "
                  f"Koşul sayısı ≈ {kosul:.3g}; sağlama $\\max|\\mathbf{{K}}_s\\mathbf{{u}}_s-\\mathbf{{F}}_s|$ = {art:.2g} "
                  f"(yuvarlama düzeyinde ✔).")
        anl.kural("Koşul sayısı, çözümün veri hatasına duyarlılığını gösterir: yaklaşık $10^{k}$ ise ondalık basamakların "
                  "$k$ tanesi kaybolur. Tek cins eleman ve makul mesnetle genelde küçüktür; çok farklı rijitlikler "
                  "(çok ince ile çok kalın eleman) bunu büyütür.")
    anl.metin("**Düğüm yer değiştirmeleri** ($\\mathbf{u}$)\n\n" + _yer_degistirme_tablosu(M))
    if M.sabit:
        ad_r = ("R" if t in ("yay", "cubuk") else "Rx, Ry, Rm")
        anl.metin(f"**Mesnet tepkileri** ($\\mathbf{{R}}=\\mathbf{{K}}\\mathbf{{u}}-\\mathbf{{F}}$; {ad_r}: mesnedin yapıya uyguladığı "
                  "kuvvet, global eksenin pozitif yönünde +). Tablo yalnız tutulu bileşenleri gösterir; serbest SD'lerde "
                  "$R_i=0$ çıkmalıdır (sağlama).\n\n" + _tepki_tablosu(M))
        if M.sayisal:
            kalan = max([abs(float(M.R_tam[i])) for i in M.serbest] + [0.0])
            anl.metin(f"Serbest SD'lerdeki tepkilerin en büyüğü {kalan:.2g} (≈ 0) ✔.")


# ============================================================================
# Adım 8: eleman kuvvetleri
# ============================================================================
def _en_buyuk_N(M):
    v = [abs(_gercek(e.N)) for e in M.elemanlar if _gercek(e.N) is not None]
    return max(v) if v else 0.0


def _eksenel_adim(M, anl):
    t = M.tip
    _basla(anl, 8, "Eleman kuvvetleri: eksenel kuvvet N" + ("" if t == "yay" else " ve gerilme σ"),
           "Yer değiştirmeleri bilmek yetmez; mühendis asıl olarak elemanın **ne kadar yüklendiğini** ister. Her elemanın iki "
           "ucundaki yer değiştirmeyi eleman eksenine çevirip uzamasını (δ) buluyor, rijitlikle çarparak kuvvete geçiyoruz.")
    if t == "yay":
        anl.kural("Yay kuvveti: $F=k\\,\\delta$, $\\delta=u_j-u_i$ (uzama). Çekme **+**, basınç **−**.")
    elif t == "cubuk":
        anl.kural("Eksenel kuvvet: $N=\\dfrac{EA}{L}\\,\\delta$, $\\delta=u_j-u_i$ (uzama); gerilme $\\sigma=N/A$. "
                  "Çekme **+**, basınç **−**.")
    else:
        anl.kural("Kafes elemanı yalnız eksenel kuvvet taşır. Eleman ekseni yönündeki uzama "
                  "$\\delta=-c\\,u_i-s\\,v_i+c\\,u_j+s\\,v_j$ ($c=\\cos\\alpha$, $s=\\sin\\alpha$); "
                  "$N=\\dfrac{EA}{L}\\,\\delta$, $\\sigma=N/A$. Çekme **+**, basınç **−**.")
    nmax = _en_buyuk_N(M)
    for e in M.elemanlar:
        e.durum = _durum(M, e, nmax)
        e.delta = e.dyerel[1] - e.dyerel[0]
        if not M.sayisal:
            e.delta = _sade(e.delta)
    if not M.sayisal and len(M.elemanlar) <= 12:
        for e in M.elemanlar:
            ea = "k" if t == "yay" else r"\frac{EA}{L}"
            deger = _Lp(e.ea)
            anl.mat(rf"\delta_{{{e.no}}} = {_L(e.delta)},\qquad N_{{{e.no}}} = {ea}\,\delta_{{{e.no}}} = "
                    rf"{deger}\cdot {_Lp(e.delta)} = {_L(e.N)}")
    ust = ["Eleman", f"L [{M.uzunluk}]", f"δ [{M.uzunluk}]", f"N [{M.kuvvet}]"]
    if t != "yay":
        ust.append(f"σ=N/A [{M.kuvvet}/{M.uzunluk}²]")
    ust.append("Durum")
    sat = []
    for e in M.elemanlar[:60]:
        s = [e.no, _metin(e.L), _hucre(M, e.delta), _hucre(M, e.N)]
        if t != "yay":
            s.append(_hucre(M, e.sigma))
        s.append(e.durum)
        sat.append(s)
    anl.metin("**Eleman kuvvetleri**\n\n" + _tablo(ust, sat))
    if len(M.elemanlar) > 60:
        anl.metin("*(İlk 60 eleman gösterildi; tümü `veri[\"elemanlar\"]` içindedir.)*")
    sifir = [e.no for e in M.elemanlar if e.durum == "sıfır"]
    if sifir and t == "kafes":
        anl.metin(f"**Sıfır çubuk(lar):** eleman {', '.join(str(x) for x in sifir)} bu yük altında kuvvet taşımıyor; "
                  "yük değişince taşıyabilir, bu yüzden kafesten çıkarılmaz.")
    cek = [e.no for e in M.elemanlar if e.durum == "çekme"]
    bas = [e.no for e in M.elemanlar if e.durum == "basınç"]
    anl.metin(f"Çekilen elemanlar: {cek or 'yok'}; basılan elemanlar: {bas or 'yok'}. Basınç çubukları burkulma "
              "açısından da kontrol edilmelidir (yalnız σ yetmez).")


def _egilme_etiketleri(M, e):
    a, b = e.dno
    if M.tip == "kiris":
        return [rf"f_{{y,{a}}}", rf"m_{{{a}}}", rf"f_{{y,{b}}}", rf"m_{{{b}}}"]
    return [rf"f_{{x,{a}}}", rf"f_{{y,{a}}}", rf"m_{{{a}}}", rf"f_{{x,{b}}}", rf"f_{{y,{b}}}", rf"m_{{{b}}}"]


def _egilme_adim(M, anl):
    t = M.tip
    _basla(anl, 8, "Eleman uç kuvvetleri ve iç kuvvet diyagramları",
           "Elemanın iki ucundaki yer değiştirmeleri ($\\mathbf{d}$) bildiğimize göre, uç kuvvetlerini rijitlik matrisinden "
           "buluyoruz. Bu kuvvetler 'sonlu eleman işaretiyle' çıkar; tasarımda kullandığımız kesme kuvveti $V$ ve eğilme "
           "momenti $M$ işaretine çevirip eleman boyunca diyagramını çiziyoruz.")
    anl.kural("Uç kuvvetleri: $\\mathbf{f}=\\mathbf{k}\\,\\mathbf{d}-\\mathbf{f}_{eq}$ ($\\mathbf{d}=\\mathbf{T}\\mathbf{u}_e$ eleman "
              "yerel eksenindeki yer değiştirme; yayılı yük varsa $\\mathbf{f}_{eq}$ çıkarılır, çünkü o yük 6. adımda düğümlere "
              "aktarılmıştı). Sonlu eleman işaretinden yapı işaretine geçiş (i: başlangıç, j: bitiş ucu):\n\n"
              "$V(0)=f_{y,i}$, $V(L)=-f_{y,j}$, $M(0)=-m_i$, $M(L)=m_j$, $N=-f_{x,i}$. "
              "Eleman içinde: $V(x)=f_{y,i}+q\\,x$, $M(x)=-m_i+f_{y,i}\\,x+q\\,x^2/2$ "
              "($M>0$: alt lif çekilir; $N>0$: çekme).")
    ayrinti = M.elemanlar if (not M.sayisal and len(M.elemanlar) <= 6) else M.elemanlar[:1]
    for e in ayrinti:
        yer = _egilme_etiketleri(M, e)
        anl.mat(rf"\mathbf{{f}}^{{({e.no})}} = \mathbf{{k}}\mathbf{{d}}" + (r" - \mathbf{f}_{eq}" if e.feq_yerel is not None else "")
                + rf" = {_etiketli_vek(e.f, yer)}")
    if len(ayrinti) < len(M.elemanlar):
        anl.metin(f"Yalnız ilk elemanın vektörü gösterildi; hepsinin uç kuvvetleri aşağıdaki tablodadır.")
    ust = ["Eleman", f"N [{M.kuvvet}]", f"V(0) [{M.kuvvet}]", f"M(0) [{M.kuvvet}·{M.uzunluk}]",
           f"V(L) [{M.kuvvet}]", f"M(L) [{M.kuvvet}·{M.uzunluk}]", "M ekstremum (x*)"]
    sat = []
    for e in M.elemanlar[:60]:
        ek = "—"
        if e.ekst is not None:
            ek = f"{_hucre(M, e.ekst[1])} (x = {_metin(e.ekst[0])})"
        sat.append([e.no, _hucre(M, e.N), _hucre(M, e.v_uc[0]), _hucre(M, e.m_uc[0]),
                    _hucre(M, e.v_uc[1]), _hucre(M, e.m_uc[1]), ek])
    anl.metin("**Uç iç kuvvetleri (yapı işaret kuralı)**\n\n" + _tablo(ust, sat))
    if len(M.elemanlar) > 60:
        anl.metin("*(İlk 60 eleman gösterildi; tümü `veri[\"elemanlar\"]` içindedir.)*")
    if any(e.ekst is not None for e in M.elemanlar):
        anl.metin("Yayılı yüklü elemanda $V(x)=0$ olduğu yerde $M$ ekstremumdur: $x^*=-f_{y,i}/q$. "
                  "Moment diyagramı bu noktada eğimini değiştirir (parabol tepesi).")
    olcek = _kuvvet_olcegi(M)
    kotu = [e.no for e in M.elemanlar
            if not (_sifir_mi(M, e.kontrol[0], olcek) and _sifir_mi(M, e.kontrol[1], olcek))]
    if kotu:
        anl.uyari(f"Eleman {kotu} için eleman içi diyagram uç değerlerle tutmadı; modeli denetleyin.")
    else:
        anl.metin("**Sağlama:** eleman boyunca $V(x)$ ve $M(x)$ ifadeleri j ucunda $M(L)=m_j$ ve $V(L)=-f_{y,j}$ "
                  "değerlerine ulaşıyor ✔ (uç kuvvetleri ile iç kuvvet diyagramları tutarlı).")


def _adim_eleman_kuvvetleri(M, anl):
    if M.tip in ("yay", "cubuk", "kafes"):
        _eksenel_adim(M, anl)
    else:
        _egilme_adim(M, anl)
        nmax = _en_buyuk_N(M)
        for e in M.elemanlar:
            e.durum = "eğilme"


# ============================================================================
# Adım 9: sonuç şemaları, Adım 10: denge ve enerji sağlaması
# ============================================================================
def _adim_sema_sonuc(M, anl):
    t = M.tip
    _basla(anl, 9, "Sonuçlar şekil üzerinde",
           "Sayılar doğrudur ama sezgi vermez. Yer değiştirmiş biçim, iç kuvvet diyagramları ve tepkiler birlikte "
           "bakıldığında 'bu sonuç makul mu?' sorusuna hızlıca cevap verir: yük aşağı ise yapı aşağı sarkmalı, mesnet "
           "tepkileri yükü dengelemeli, moment çekilen tarafa çizilmeli.")
    kareler = _sema_sonuc(M)
    if not kareler:
        anl.metin("Sonuçlar harfli (sembolik) olduğundan sayısal şekil çizilemez. Harfleri sayıyla değiştirip modeli yeniden "
                  "çözerseniz şekil değiştirmiş biçim ve diyagramlar çizilir.")
        return
    ek = {"yay": "Yer değiştirmiş biçim abartılı çizilir (ölçek karede yazılıdır); ikinci karede eleman kuvvetleri, sonda tepkiler.",
          "cubuk": "Yer değiştirmiş biçim abartılı çizilir (ölçek karede yazılıdır); ikinci karede eleman kuvvetleri, sonda tepkiler.",
          "kafes": "Eksenel kuvvet karesinde **mavi** çekme, **kırmızı** basınç çubuğudur; kalınlık |N| ile orantılıdır.",
          "kiris": "V ve M diyagramları eleman eksenine dik çizilir; moment çekilen lif tarafındadır.",
          "cerceve": "N, V ve M diyagramları eleman eksenine dik çizilir; moment çekilen lif tarafındadır."}[t]
    anl.metin("*Okuma kılavuzu:* ilk karede kesik çizgi yüksüz, düz çizgi yüklü (abartılı) biçimdir. " + ek)
    anl.sema("Sonuçlar", kareler)


_DENGE_ANAHTAR = {"yay": ("Fx",), "cubuk": ("Fx",), "kafes": ("Fx", "Fy", "M"), "kiris": ("Fy", "M"),
                  "cerceve": ("Fx", "Fy", "M")}


def _adim_denge(M, anl):
    t = M.tip
    _basla(anl, 10, "Sağlama: denge ve enerji",
           "Bir hesabın doğru olduğuna sonuç makul görünüyor diye değil, **bağımsız bir denetimle** inanırız. İki denetim "
           "yapıyoruz: (1) dış yükler ile mesnet tepkileri bütün yapıyı dengelemeli, (2) yükün yaptığı iş, yapıda "
           "depolanan şekil değiştirme enerjisine eşit olmalı.")
    dg0 = M.dugumler[0]
    nokta = f"düğüm {dg0.no}" + ("" if t in ("yay", "cubuk") else f" ({_metin(dg0.x)}, {_metin(dg0.y)})")
    olcek = _kuvvet_olcegi(M)
    ad = {"Fx": "ΣFx", "Fy": "ΣFy", "M": f"ΣM ({nokta})"}
    birim = {"Fx": M.kuvvet, "Fy": M.kuvvet, "M": f"{M.kuvvet}·{M.uzunluk}"}
    sat, hepsi = [], True
    for a in _DENGE_ANAHTAR[t]:
        v = M.denge[a]
        ok = _sifir_mi(M, v, olcek)
        hepsi = hepsi and ok
        sat.append([ad[a], f"{_metin(v)} {birim[a]}", "✔" if ok else "✘ (denge sağlanmıyor)"])
    anl.kural("Denge: dış yükler (düğüm yükleri ve yayılı yük bileşkeleri) ile mesnet tepkilerinin toplamı sıfır olmalıdır. "
              "Moment toplamı herhangi bir noktaya göre alınabilir; burada ilk düğüm seçildi.")
    anl.metin("**Denge toplamları** (yük + tepki)\n\n" + _tablo(["Toplam", "Değer", "Sonuç"], sat))
    if hepsi:
        anl.metin("Dış kuvvetler ile tepkiler dengededir ✔: çözüm fiziksel olarak tutarlı (çözüm tek başına doğruluğu "
                  "kanıtlamaz ama hatalı mesnet, yük işareti ve birleştirme hatalarını yakalar).")
    else:
        anl.uyari("Denge sağlanmadı: yük işaretlerini, mesnetleri ve eleman bağlantılarını denetleyin.")
    uKu, uF = M.enerji["uKu"], M.enerji["uF"]
    fark = uKu - uF
    ok_e = _sifir_mi(M, fark, max(1.0, abs(_gercek(uF) or 0.0)))
    birim_e = f"{M.kuvvet}·{M.uzunluk}"
    if M.sembolik:
        anl.mat(rf"U=\tfrac12\,\mathbf{{u}}^T\mathbf{{K}}\mathbf{{u}} = {_L(_sade(uKu / 2))},\qquad "
                rf"W=\tfrac12\,\mathbf{{u}}^T\mathbf{{F}} = {_L(_sade(uF / 2))}")
    else:
        anl.mat(rf"U=\tfrac12\,\mathbf{{u}}^T\mathbf{{K}}\mathbf{{u}} = {_L(uKu / 2)}\ \text{{{birim_e}}},\qquad "
                rf"W=\tfrac12\,\mathbf{{u}}^T\mathbf{{F}} = {_L(uF / 2)}\ \text{{{birim_e}}}")
    anl.metin("**Enerji sağlaması (Clapeyron):** doğrusal elastik yapıda dış yükün yaptığı iş "
              "$W=\\tfrac12\\mathbf{u}^T\\mathbf{F}$, yapıda depolanan şekil değiştirme enerjisi "
              "$U=\\tfrac12\\mathbf{u}^T\\mathbf{K}\\mathbf{u}$'ya eşittir; $\\mathbf{K}$ pozitif tanımlı olduğundan $U>0$ "
              + ("olmalıdır. " if not _sifir_mi(M, uF, 1.0) else "(yük yoksa ikisi de 0'dır). ")
              + ("Eşitlik sağlandı ✔." if ok_e else "Eşitlik sağlanmadı; hesabı denetleyin."))
    if M.sayisal:
        buyuk = float(np.abs(M.u).max())
        k = int(np.abs(M.u).argmax())
        ek = f"En büyük yer değiştirme: {M.sd_et[k]} = {_ondalik_metin(float(M.u[k]))} {_sd_birimi(M, _SD_ADLARI[t][k % M.d])}."
    else:
        ek = ""
    if M.n <= 12:
        ozet = rf"\mathbf{{u}} = {_etiketli_vek(M.u, M.sd_tex)}"
        anl.sonuc(ozet, f"Global yer değiştirme vektörü ({M.uzunluk}; dönmeler rad). {ek}".strip())
    else:
        anl.sonuc(r"\mathbf{u}\ \text{(" + str(M.n) + r" bileşen; tablolar yukarıda)}", ek or "Yer değiştirmeler yukarıdaki tabloda.")


# ============================================================================
# Adım 11: bağımsız Python betiği (gerçekten çalıştırılır)
# ============================================================================
def _py_sayi(M, x):
    """Üretilen betiğe yazılacak sayı metni (kesin modda tam kesirli)."""
    if M.sayisal:
        return repr(float(x))
    x = sp.sympify(x)
    if x.is_Integer:
        return str(int(x))
    if x.is_Rational:
        return f"sp.Rational({x.p}, {x.q})"
    if x.is_Float:
        return repr(float(x))
    s = sp.sstr(x).replace("sqrt(", "sp.sqrt(")
    return re.sub(r"(?<![\w.])(\d+)/(\d+)", r"sp.Rational(\1, \2)", s)


_PY_ELEMAN = {
    "yay": '''def eleman_matrisleri(e):
    i, j, kk = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    ci = 1 if dx > 0 else -1              # eleman ekseni yönü (+x ya da -x)
    kl = mat([[kk, -kk], [-kk, kk]])      # yerel yay matrisi
    Te = mat([[ci, 0], [0, ci]])          # dönüşüm (yalnız yön işareti)
    return kl, Te, [d*i, d*j], None
''',
    "cubuk": '''def eleman_matrisleri(e):
    i, j, Ek, Ak = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    Lb = abs(dx)                          # eleman boyu
    ci = 1 if dx > 0 else -1              # eleman ekseni yönü (+x ya da -x)
    ea = Ek*Ak/Lb
    kl = mat([[ea, -ea], [-ea, ea]])      # yerel matris EA/L [[1,-1],[-1,1]]
    Te = mat([[ci, 0], [0, ci]])
    return kl, Te, [d*i, d*j], None
''',
    "kafes": '''def eleman_matrisleri(e):
    i, j, Ek, Ak = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    dy = dugum_xy[j][1] - dugum_xy[i][1]
    Lb = kok(dx**2 + dy**2)               # eleman boyu
    ci, si = dx/Lb, dy/Lb                 # cos ve sin
    ea = Ek*Ak/Lb
    kl = mat([[ea, -ea], [-ea, ea]])      # yerel matris EA/L [[1,-1],[-1,1]]
    Te = mat([[ci, si, 0, 0], [0, 0, ci, si]])   # global -> eleman ekseni
    return kl, Te, [d*i, d*i + 1, d*j, d*j + 1], None
''',
    "kiris": '''def eleman_matrisleri(e):
    i, j, Ek, Ik, qq = e
    Lb = dugum_xy[j][0] - dugum_xy[i][0]  # eleman boyu
    a = Ek*Ik/Lb**3
    kl = mat([[12*a, 6*Lb*a, -12*a, 6*Lb*a],
              [6*Lb*a, 4*Lb**2*a, -6*Lb*a, 2*Lb**2*a],
              [-12*a, -6*Lb*a, 12*a, -6*Lb*a],
              [6*Lb*a, 2*Lb**2*a, -6*Lb*a, 4*Lb**2*a]])
    feq = None
    if qq != 0:                           # yayılı yükün eşdeğer düğüm yükleri
        feq = mat([qq*Lb/2, qq*Lb**2/12, qq*Lb/2, -qq*Lb**2/12])
    return kl, None, [d*i, d*i + 1, d*j, d*j + 1], feq
''',
    "cerceve": '''def eleman_matrisleri(e):
    i, j, Ek, Ak, Ik, qq = e
    dx = dugum_xy[j][0] - dugum_xy[i][0]
    dy = dugum_xy[j][1] - dugum_xy[i][1]
    Lb = kok(dx**2 + dy**2)               # eleman boyu
    ci, si = dx/Lb, dy/Lb                 # cos ve sin
    ea = Ek*Ak/Lb
    a = Ek*Ik/Lb**3
    kl = mat([[ea, 0, 0, -ea, 0, 0],
              [0, 12*a, 6*Lb*a, 0, -12*a, 6*Lb*a],
              [0, 6*Lb*a, 4*Lb**2*a, 0, -6*Lb*a, 2*Lb**2*a],
              [-ea, 0, 0, ea, 0, 0],
              [0, -12*a, -6*Lb*a, 0, 12*a, -6*Lb*a],
              [0, 6*Lb*a, 2*Lb**2*a, 0, -6*Lb*a, 4*Lb**2*a]])
    Te = mat([[ci, si, 0, 0, 0, 0], [-si, ci, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0],
              [0, 0, 0, ci, si, 0], [0, 0, 0, -si, ci, 0], [0, 0, 0, 0, 0, 1]])
    feq = None
    if qq != 0:                           # yayılı yükün eşdeğer düğüm yükleri (yerel eksende)
        feq = mat([0, qq*Lb/2, qq*Lb**2/12, 0, qq*Lb/2, -qq*Lb**2/12])
    return kl, Te, [d*i, d*i + 1, d*i + 2, d*j, d*j + 1, d*j + 2], feq
''',
}


def _py_eleman_satiri(M, e):
    t = M.tip
    deg = {"yay": [e.k], "cubuk": [e.E, e.A], "kafes": [e.E, e.A],
           "kiris": [e.E, e.I, e.q], "cerceve": [e.E, e.A, e.I, e.q]}[t]
    return "(" + ", ".join([str(e.ia), str(e.ib)] + [_py_sayi(M, v) for v in deg]) + "),"


def _py_betik(M):
    t, d, kesin = M.tip, M.d, not M.sayisal
    S = lambda x: _py_sayi(M, x)  # noqa: E731
    ad_e = {"yay": "(i, j, k)", "cubuk": "(i, j, E, A)", "kafes": "(i, j, E, A)",
            "kiris": "(i, j, E, I, q)", "cerceve": "(i, j, E, A, I, q)"}[t]
    s = [f"# {M.baslik}: {_TIP_AD[t]}, {M.n} SD, doğrudan rijitlik yöntemi (tek başına çalışır)"]
    if kesin:
        s += ["import sympy as sp", "mat = sp.Matrix", "kok = sp.sqrt", ""]
        semb = set()
        for e in M.elemanlar:
            for v in (e.E, e.A, e.I, e.k, e.q):
                if isinstance(v, sp.Basic):
                    semb |= v.free_symbols
        for satir in M.yuk:
            for v in satir:
                semb |= sp.sympify(v).free_symbols
        if semb:
            ad = sorted(x.name for x in semb)
            s += [f"{', '.join(ad)} = sp.symbols('{' '.join(ad)}')" if len(ad) > 1
                  else f"{ad[0]} = sp.symbols('{ad[0]}')", ""]

        s += ["def sifirlar(n, m=1):", "    return sp.zeros(n, m)", ""]
    else:
        s += ["import numpy as np", "np.set_printoptions(precision=6, suppress=True, linewidth=110)",
              "kok = np.sqrt", "", "def mat(a):", "    return np.array(a, dtype=float)", "",
              "def sifirlar(n, m=1):", "    return np.zeros(n) if m == 1 else np.zeros((n, m))", ""]
    s += [f"d = {d}                    # düğüm başına SD ({', '.join(_SD_ADLARI[t])})",
          "",
          "# --- model verisi ---",
          "dugum_xy = [" + ", ".join(f"({S(g.x)}, {S(g.y)})" for g in M.dugumler) + "]   # düğüm koordinatları",
          f"# elemanlar: {ad_e}; i, j = düğüm sırası (0'dan)",
          "elemanlar = ["] + ["    " + _py_eleman_satiri(M, e) for e in M.elemanlar] + ["]"]
    fd = [M.F_dugum[i] for i in range(M.n)]
    s += ["F_dugum = [" + ", ".join(S(v) for v in fd) + "]   # düğüm yükleri (SD sırasıyla)",
          f"sabit = {list(M.sabit)}   # tutulu SD'ler (0'dan)", "n = d*len(dugum_xy)"]
    if kesin:
        s += ["",
              "# sayıları sympy'a çevir: bölmeler kesirli kalır, yuvarlama olmaz",
              "dugum_xy = [tuple(sp.sympify(c) for c in p) for p in dugum_xy]",
              "elemanlar = [e[:2] + tuple(sp.sympify(v) for v in e[2:]) for e in elemanlar]",
              "F_dugum = [sp.sympify(v) for v in F_dugum]"]
    s += ["", "# --- eleman matrisleri ---"] + _PY_ELEMAN[t].rstrip("\n").split("\n")
    s += ["",
          "# --- birleştirme: K ve F ---",
          "K = sifirlar(n, n)",
          "F = sifirlar(n)",
          "for e in elemanlar:",
          "    kl, Te, dofs, feq = eleman_matrisleri(e)",
          "    ke = kl if Te is None else Te.T @ kl @ Te",
          "    for a, p in enumerate(dofs):",
          "        for b, r in enumerate(dofs):",
          "            K[p, r] += ke[a, b]",
          "    if feq is not None:",
          "        fg = feq if Te is None else Te.T @ feq",
          "        for a, p in enumerate(dofs):",
          "            F[p] += fg[a]",
          "for p, v in enumerate(F_dugum):",
          "    F[p] += v"]
    if kesin:
        s += ["K = K.applyfunc(sp.simplify)"]
    s += ["", "# --- sınır koşulları ve çözüm ---",
          "serbest = [p for p in range(n) if p not in sabit]",
          "u = sifirlar(n)"]
    if kesin:
        s += ["if serbest:",
              "    Ks = K.extract(serbest, serbest)",
              "    Fs = sp.Matrix([F[p] for p in serbest])",
              "    us = Ks.LUsolve(Fs)",
              "    for a, p in enumerate(serbest):",
              "        u[p] = sp.simplify(us[a])",
              "R = (K*u - F).applyfunc(sp.simplify)     # tepkiler R = K u - F"]
    else:
        s += ["if serbest:",
              "    u[serbest] = np.linalg.solve(K[np.ix_(serbest, serbest)], F[serbest])",
              "R = K @ u - F                            # tepkiler R = K u - F"]
    s += ["", "# --- sonuçlar ---",
          "print('u =', " + ("list(u))" if kesin else "u)"),
          "print('Mesnet tepkileri (tutulu SD, 1 tabanlı):')",
          "for p in sabit:",
          "    print(f'  R[{p + 1}] = {R[p]}')",
          "print('Eleman kuvvetleri:')",
          "for no, e in enumerate(elemanlar, start=1):",
          "    kl, Te, dofs, feq = eleman_matrisleri(e)",
          "    ue = mat([u[p] for p in dofs])",
          "    de = ue if Te is None else Te @ ue      # eleman eksenindeki yer değiştirme",
          "    f = kl @ de",
          "    if feq is not None:",
          "        f = f - feq                         # f = k d - f_eq"]
    if kesin:
        s += ["    f = f.applyfunc(sp.simplify)"]
    if t in ("yay", "cubuk", "kafes"):
        s += ["    N = f[1]                                # eksenel kuvvet (çekme +)",
              ("    print(f'  Eleman {no}: N = {N}')" if kesin else "    print(f'  Eleman {no}: N = {float(N):.6g}')")]
    else:
        s += [("    print(f'  Eleman {no}: f = {list(f)}')" if kesin
               else "    print(f'  Eleman {no}: f = {[round(float(x), 6) for x in f]}')")]
    return s


def _adim_python(M, anl):
    _basla(anl, 11, "Aynı hesap Python'da",
           "Elle yaptığımız bütün işlemleri (eleman matrisi, birleştirme, sınır koşulu, çözüm, tepkiler, eleman kuvvetleri) "
           "tek bir betikte topluyoruz. Betik kendi başına çalışır; çıktısı yukarıdaki sonuçlarla aynı olmalıdır. "
           + ("Kesin modda `sympy` (kesirli/harfli sonuç), sayısal modda `numpy` kullanılır."))
    kod, cikti = mo._python_bolumu(anl, _py_betik(M))
    return kod, cikti


# ============================================================================
# Yapılı sonuç verisi ve genel işlev
# ============================================================================
def _veri_olustur(M):
    """Sonuc.veri: JSON'a uygun, yapılı sonuçlar (sembolik çözümde sayı yerine ifade metni)."""
    t, d = M.tip, M.d
    V = _veri_sayi
    nmax = _en_buyuk_N(M)
    dugumler = []
    for i, dg in enumerate(M.dugumler):
        dugumler.append({"no": dg.no, "x": V(dg.x), "y": V(dg.y),
                         "sd": [d * i + j + 1 for j in range(d)],
                         "u": [V(M.u[d * i + j]) for j in range(d)]})
    elemanlar = []
    for e in M.elemanlar:
        uc = [V(-e.N), V(e.N)] if e.f is None else [V(x) for x in e.f]
        elemanlar.append({
            "no": e.no, "dugumler": list(e.dno), "L": V(e.L), "c": V(e.c), "s": V(e.s),
            "uc_kuvvetleri": uc, "N": V(e.N), "durum": _durum(M, e, nmax),
            "diyagram": {"x": [V(x) for x in e.dx], "N": [V(x) for x in e.dN],
                         "V": [V(x) for x in e.dV], "M": [V(x) for x in e.dM]}})
    tepkiler = []
    for i, dg in enumerate(M.dugumler):
        if not any(M.mesnet[i]):
            continue
        r = {"dugum": dg.no, "Fx": 0.0, "Fy": 0.0, "M": 0.0}
        for j, ad in enumerate(_BILESEN[t]):
            if M.mesnet[i][j]:
                r[ad] = V(M.R_tam[d * i + j])
        tepkiler.append(r)
    olcek = None
    if not M.sembolik:
        try:
            olcek = float(_olcek_bul(M))
        except (TypeError, ValueError, ArithmeticError):  # pragma: no cover
            olcek = None
    veri = {
        "tip": t, "baslik": M.baslik, "birim": {"kuvvet": M.kuvvet, "uzunluk": M.uzunluk},
        "mod": M.mod, "sd_sayisi": M.n, "sd_etiketleri": list(M.sd_et),
        "dugumler": dugumler, "elemanlar": elemanlar, "tepkiler": tepkiler,
        "u": [V(M.u[i]) for i in range(M.n)], "F": [V(M.F[i]) for i in range(M.n)],
        "denge": {k: V(v) for k, v in M.denge.items()},
        "olcek": olcek,
        "K": ([[V(M.K[i, j]) for j in range(M.n)] for i in range(M.n)] if M.n <= 40 else None),
    }
    return veri


def se_coz(model, *, goster=None):
    """Bir sonlu eleman modelini (sözlük ya da JSON metni) doğrudan rijitlik yöntemiyle çözer.

    Dönüş: ``Sonuc`` — ``.deger`` global yer değiştirme vektörü u (sympy Matrix), ``.veri`` yapılı sonuçlar,
    ``.anlatim`` adım adım anlatım, ``.python_kodu`` / ``.python_ciktisi`` çalıştırılmış bağımsız betik."""
    M = _model_oku(model)
    _hazirla(M)
    _coz(M)
    _eleman_kuvvetleri(M)
    _denge_hesapla(M)
    _diyagram_hazirla(M)
    anl = mo.Anlatim()
    _adim_model(M, anl)
    _adim_sema_model(M, anl)
    _adim_sd(M, anl)
    _adim_elemanlar(M, anl)
    _adim_birlestirme(M, anl)
    _adim_yukler(M, anl)
    _adim_cozum(M, anl)
    _adim_eleman_kuvvetleri(M, anl)
    _adim_sema_sonuc(M, anl)
    _adim_denge(M, anl)
    kod, cikti = _adim_python(M, anl)
    if M.sayisal:
        deger = sp.Matrix([float(v) for v in M.u])
    else:
        deger = sp.Matrix(M.u)
    sonuc = mo.Sonuc(deger, anl, "u", kod, cikti)
    sonuc.veri = _veri_olustur(M)
    mo.son_anlatim = anl
    anl.goster(goster)
    return sonuc
