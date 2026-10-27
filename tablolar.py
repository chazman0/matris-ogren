# -*- coding: utf-8 -*-
"""Bina tabloları ve metraj (Matris Öğren): tabloları göster ve etkileşimli veri tabanı düzenleme.

Tek kaynak: arayüzdeki tablo editörü (``docs/tablo_editoru.js``) ve statik hesap raporu (``rapor.py``) aynı tabloları
kullanır. Kullanım::

    import yapi, tablolar
    bina = yapi.bina_sablon("betonarme-2kat-3x2")
    tablolar.bina_tablolari(bina)                   # çözümsüz: Model + Yükler (girdi) + Metraj (+ deprem önizlemesi)
    r = yapi.bina_coz(bina, anlat=False)
    tablolar.bina_tablolari(bina, r.veri)           # çözümlü: + Analiz, Deprem, Tasarım, Temel
    tablolar.degisiklikleri_uygula(bina, [{"yol": ["katlar", {"no": 2}, "kot"], "deger": 6.5}])   # düzenlemeyi binaya uygula

TABLO şeması (§15.1)::

    {"ad": "katlar", "baslik": "Katlar", "grup": "Model" | "Yükler" | "Analiz" | "Tasarım" | "Metraj" | "Deprem" | "Temel",
     "sutunlar": [{"ad", "baslik", "birim", "tur": "sayi" | "metin" | "secim" | "bool", "secenekler"?, "duzenlenebilir": bool,
                   "ondalik"?, "bos_olur"?, "vurgu"?: "dc"}],
     "satirlar": [{"degerler": {sutun_ad: değer}, "yol"?: {sutun_ad: JSON yolu}, "hucre"?: {sutun_ad: {"tur", "secenekler", ...}},
                   "ozet"?: true}],
     "toplam"?: {sutun_ad: değer}, "aciklama": "...", "kaynak": "..."}

- Sayılar ham float'tır (arayüz ``ondalik`` önerisiyle biçimler); boş değer ``None``.
- Bir hücre yalnız sütun ``duzenlenebilir`` ve satırın ``yol``unda o sütun varsa düzenlenir. ``yol`` bina JSON'u içindeki gerçek
  alana işaret eder: anahtar (metin), liste sırası (tam sayı) ya da liste elemanı seçici ``{"no": 3}`` / ``{"ad": "A"}`` /
  ``{"aks": ["B", "1"], "_olustur": true}`` (``_olustur``: eşleşen eleman yoksa seçici alanlarıyla yeni eleman eklenir).
  Ara sözlük/liste yoksa oluşturulur. ``secenekler`` elemanı değer ya da ``{"deger", "etiket"}`` olabilir.
- ``satir.hucre``: anahtar–değer (parametre) tablolarında satıra özgü hücre türü/seçenekleri.
- ``satir.ozet``: ara toplam / Σ satırı (arayüz kalın gösterir).
- ``sutun.vurgu == "dc"``: değer > 1 ise arayüz ve rapor kırmızı gösterir.

Metraj (eğitim amaçlı yaklaşık keşif; birim fiyat yoktur): betonarme kolon ``b·h·(H − t_döşeme)``, kiriş ``b·(h − t)·L_net``
(L_net: aks boyu − uçlardaki kolonların yarı genişlikleri), döşeme ``aks-aks alan·t``, tekil temel ``B·L·h``; kalıp alanları;
donatı tasarımdan (``veri.tasarim`` A_s + etriye) ya da açıkça "yaklaşık" etiketli kg/m³ oranlarından; çelik profil başına
uzunluk, katalog birim ağırlığı (``yapi_veri.PROFILLER.g``; yoksa A·7850), bağlantı payı (varsayılan %10, ``bina.metraj``
ile değiştirilebilir) ve boya yüzeyi (profil çevresi × L).
"""
from __future__ import annotations

import copy
import json
import math

import yapi_veri as yv

__version__ = "0.1.0"

GRUPLAR = ("Model", "Yükler", "Deprem", "Analiz", "Tasarım", "Temel", "Metraj")
CELIK_YOGUNLUK = 7850.0          # kg/m³ (çelik ve donatı; TS 498: 78,5 kN/m³)
BAGLANTI_PAYI = 0.10             # çelik bağlantı / levha / kaynak payı (oran), bina.metraj.baglanti_payi ile değişir
DONATI_ORANLARI = {              # kg/m³ — YAKLAŞIK öğretim değerleri (yönetmelik değeri değildir; tasarımdan A_s yoksa)
    "kolon": 160.0, "kiris": 130.0, "doseme": 80.0, "temel": 70.0, "diger": 100.0,
}
KOLON_ETRIYE = (8.0, 0.10)       # Φ (mm), aralık (m): kolon etriyesi varsayımı (tasarım vermezse; TBDY sarılma bölgesi mertebesi)
_DURUM_AD = {"G": "Sabit yük (öz ağırlık, kaplama, duvar)", "Q": "Hareketli yük (TS 498 Çizelge 6)", "S": "Kar (TS 498 md. 11)",
             "W": "Rüzgâr (TS 498 md. 14)", "E": "Deprem (TBDY 2018 eşdeğer deprem yükü)"}
_TUR_AD = {"kolon": "Kolon", "kiris": "Kiriş", "doseme": "Döşeme", "temel": "Temel", "panel": "Panel"}


# ============================================================================
# Yol (JSON yolu) — arayüzdeki MatrisTablo._ic.yolUygula ile aynı anlam
# ============================================================================
def _secici_mi(p):
    return isinstance(p, dict)


def _eslesir(eleman, secici):
    if not isinstance(eleman, dict):
        return False
    for a, v in secici.items():
        if a.startswith("_"):
            continue
        if a not in eleman or not _esit(eleman[a], v):
            return False
    return True


def _esit(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or (isinstance(a, bool) and isinstance(b, bool) and a == b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_esit(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_esit(a[k], b[k]) for k in a)
    return a == b


def _adim(kap, p, sonraki, olustur):
    """Bir yol adımı: kap[p] (gerekirse oluşturarak)."""
    if _secici_mi(p):
        if not isinstance(kap, list):
            raise KeyError(f"seçici {p!r} bir liste bekler")
        for e in kap:
            if _eslesir(e, p):
                return e
        if olustur and p.get("_olustur"):
            yeni = {a: copy.deepcopy(v) for a, v in p.items() if not a.startswith("_")}
            kap.append(yeni)
            return yeni
        raise KeyError(f"listede {p!r} ile eşleşen eleman yok")
    if isinstance(p, bool):
        raise KeyError("yol adımı bool olamaz")
    if isinstance(p, int):
        if not isinstance(kap, list) or not -len(kap) <= p < len(kap):
            raise KeyError(f"liste sırası {p} yok")
        return kap[p]
    if not isinstance(kap, dict):
        raise KeyError(f"{p!r} anahtarı bir sözlük bekler")
    if p not in kap or kap[p] is None:
        if not olustur:
            raise KeyError(f"{p!r} anahtarı yok")
        kap[p] = [] if (_secici_mi(sonraki) or isinstance(sonraki, int) and not isinstance(sonraki, bool)) else {}
    return kap[p]


def yol_al(bina, yol):
    """``yol``un gösterdiği değer (son anahtar sözlükte yoksa None — "varsayılan"); ara adımlar yoksa KeyError
    (seçici ``_olustur`` olsa bile oluşturmaz)."""
    kap = bina
    for i, p in enumerate(yol[:-1]):
        kap = _adim(kap, p, yol[i + 1], False)
    son = yol[-1]
    if isinstance(kap, dict) and isinstance(son, str):
        return kap.get(son)
    return _adim(kap, son, None, False)


def yol_ata(bina, yol, deger):
    """``bina`` içinde ``yol``a ``deger`` yazar (yerinde); ara sözlük/listeler ve ``_olustur`` seçicili elemanlar oluşturulur."""
    if not isinstance(yol, (list, tuple)) or not yol:
        raise KeyError("yol boş")
    kap = bina
    for i, p in enumerate(yol[:-1]):
        kap = _adim(kap, p, yol[i + 1], True)
    son = yol[-1]
    if _secici_mi(son):
        raise KeyError("yolun son adımı seçici olamaz (alan adı ya da sıra olmalı)")
    if isinstance(son, int) and not isinstance(son, bool):
        if not isinstance(kap, list) or not -len(kap) <= son < len(kap):
            raise KeyError(f"liste sırası {son} yok")
        kap[son] = deger
    else:
        if not isinstance(kap, dict):
            raise KeyError(f"{son!r} anahtarı bir sözlük bekler")
        kap[son] = deger
    return bina


def degisiklikleri_uygula(bina, degisiklikler):
    """Tablo düzenlemelerini binanın KOPYASINA uygular: degisiklikler = [{"yol": [...], "deger": v}, ...] → yeni bina."""
    yeni = copy.deepcopy(bina)
    for d in degisiklikler or []:
        yol_ata(yeni, list(d["yol"]), copy.deepcopy(d.get("deger")))
    return yeni


# ============================================================================
# yardımcılar
# ============================================================================
def _n(x):
    """Kayan nokta gürültüsünü at (2.6500000000000004 → 2.65); None/NaN → None."""
    if x is None or isinstance(x, bool):
        return x
    if isinstance(x, int):
        return x
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    if x == 0:
        return 0.0
    return float(f"{x:.10g}")


def _S(ad, baslik, birim="", tur="sayi", duzenlenebilir=False, ondalik=None, secenekler=None, **ek):
    s = {"ad": ad, "baslik": baslik, "birim": birim, "tur": tur, "duzenlenebilir": bool(duzenlenebilir)}
    if ondalik is not None:
        s["ondalik"] = ondalik
    if secenekler is not None:
        s["secenekler"] = secenekler
    s.update(ek)
    return s


def _R(degerler, yol=None, **ek):
    r = {"degerler": {a: (_n(v) if isinstance(v, float) else v) for a, v in degerler.items()}}
    yol = {a: y for a, y in (yol or {}).items() if y is not None}
    if yol:
        r["yol"] = yol
    r.update(ek)
    return r


def _T(ad, baslik, grup, sutunlar, satirlar, aciklama="", kaynak="", toplam=None):
    t = {"ad": ad, "baslik": baslik, "grup": grup, "sutunlar": sutunlar, "satirlar": satirlar, "aciklama": aciklama, "kaynak": kaynak}
    if toplam:
        t["toplam"] = {a: (_n(v) if isinstance(v, float) else v) for a, v in toplam.items()}
    return t


def _topla(satirlar, *adlar):
    t = {}
    for a in adlar:
        s = 0.0
        var = False
        for r in satirlar:
            if r.get("ozet"):
                continue
            v = r["degerler"].get(a)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                s += v
                var = True
        if var:
            t[a] = s
    return t


def _liste_yolu(ham, liste_ad, no, alan, ilk=1):
    """Ham bina listesinde no'lu elemanın alan yolu: eleman 'no' taşıyorsa {"no": n} seçici; taşımıyorsa (no = sıra + ilk)
    sıra numarası; bulunamazsa None (düzenlenemez)."""
    liste = ham.get(liste_ad) if isinstance(ham, dict) else None
    if not isinstance(liste, list):
        return None
    for e in liste:
        if isinstance(e, dict) and "no" in e and _esit(e.get("no"), no):
            return [liste_ad, {"no": e["no"]}, alan]
    i = no - ilk if isinstance(no, int) else None
    if i is not None and 0 <= i < len(liste) and isinstance(liste[i], dict) and "no" not in liste[i]:
        return [liste_ad, i, alan]
    return None


def _aks_yolu(ham, yon, ad, alan):
    akslar = (ham.get("akslar") or {}).get(yon) if isinstance(ham, dict) else None
    if not isinstance(akslar, list):
        return None
    for e in akslar:
        if isinstance(e, dict) and str(e.get("ad", "")).strip() == ad:
            return ["akslar", yon, {"ad": e["ad"]}, alan]
    return None


def _secim(liste):
    return [x for x in liste]


def _ref_metin(ref):
    if isinstance(ref, dict):
        if "dugum" in ref:
            return f"D{ref['dugum']}"
        if "aks" in ref:
            a = ref.get("aks") or ["?", "?"]
            return f"{a[0]}{a[1]}/k{ref.get('kat', '?')}"
        if "X" in ref:
            return f"({_n(ref.get('X'))}, {_n(ref.get('Y'))}, {_n(ref.get('Z'))})"
    return json.dumps(ref, ensure_ascii=False)


def _kesit_secenekleri(ham):
    return sorted(str(a) for a in (ham.get("kesitler") or {}))


# ============================================================================
# Bağlam: ham bina + (varsa) yapi okuması B / Y + (varsa) çözüm verisi
# ============================================================================
class _Baglam:
    def __init__(self, bina, veri):
        if isinstance(bina, str):
            bina = json.loads(bina)
        self.ham = bina if isinstance(bina, dict) else {}
        self.veri = veri if isinstance(veri, dict) else None
        self.B = self.Y = None
        self.okuma_hatasi = None
        try:
            import yapi
            self.yapi = yapi
        except Exception:  # pragma: no cover — yapi.py yoksa yalnız ham tablolar
            self.yapi = None
        if self.yapi is not None:
            try:
                self.B = self.yapi._bina_oku(copy.deepcopy(self.ham))
                self.Y = self.yapi._yukleri_hazirla(self.B)
            except Exception as e:  # noqa: BLE001 — geçersiz model: ham tablolar yine gösterilir
                self.B = self.Y = None
                self.okuma_hatasi = str(e)
        self.tasarim = {}
        if self.veri and isinstance(self.veri.get("tasarim"), dict):
            for e in self.veri["tasarim"].get("elemanlar") or []:
                self.tasarim[(e.get("tur"), e.get("no"))] = e
        self.metraj_ayar = self.ham.get("metraj") if isinstance(self.ham.get("metraj"), dict) else {}

    # --- düğüm koordinatı (aks–kat ve serbest düğümler) ---
    def ref_koordinat(self, ref):
        B = self.B
        if not isinstance(ref, dict):
            return None
        if all(a in ref for a in ("X", "Y", "Z")):
            try:
                return float(ref["X"]), float(ref["Y"]), float(ref["Z"])
            except (TypeError, ValueError):
                return None
        if "dugum" in ref:
            for d in self.ham.get("dugumler") or []:
                if isinstance(d, dict) and _esit(d.get("no"), ref["dugum"]):
                    return self.ref_koordinat(d)
            if self.veri:
                for d in (self.veri.get("ag") or {}).get("dugumler") or []:
                    if _esit(d.get("no"), ref["dugum"]):
                        return d["X"], d["Y"], d["Z"]
            return None
        if "aks" in ref and B is not None:
            a = ref.get("aks") or []
            try:
                ix, iy = B.ax[str(a[0])], B.ay[str(a[1])]
                return B.xk[ix], B.yk[iy], B.kat[int(ref.get("kat", 0))]["kot"]
            except (KeyError, IndexError, TypeError, ValueError):
                return None
        return None


def _baglanti_payi(c):
    v = c.metraj_ayar.get("baglanti_payi")
    try:
        v = float(v)
        if 0.0 <= v <= 1.0:
            return v
    except (TypeError, ValueError):
        pass
    return BAGLANTI_PAYI


def _donati_orani(c, tur):
    d = c.metraj_ayar.get("donati_orani") if isinstance(c.metraj_ayar.get("donati_orani"), dict) else {}
    try:
        v = float(d.get(tur))
        if v >= 0:
            return v
    except (TypeError, ValueError):
        pass
    return DONATI_ORANLARI.get(tur, DONATI_ORANLARI["diger"])


# ============================================================================
# MODEL
# ============================================================================
def _t_genel(c):
    ham, B = c.ham, c.B
    an = ham.get("analiz") if isinstance(ham.get("analiz"), dict) else {}
    sistem = B.sistem if B else ham.get("sistem", "betonarme")
    kume = B.kombinasyon_kumesi if B else ham.get("kombinasyon_kumesi") or ("ts500" if sistem == "betonarme" else "cythye_ydkt")
    satirlar = [
        _R({"parametre": "Başlık", "deger": ham.get("baslik") or "", "birim": "", "aciklama": "Rapor kapağında ve tablolarda"},
           {"deger": ["baslik"]}, hucre={"deger": {"tur": "metin"}}),
        _R({"parametre": "Taşıyıcı sistem", "deger": sistem, "birim": "", "aciklama": "betonarme | çelik"},
           {"deger": ["sistem"]}, hucre={"deger": {"tur": "secim", "secenekler": ["betonarme", "celik"]}}),
        _R({"parametre": "Kombinasyon kümesi", "deger": kume, "birim": "",
            "aciklama": "; ".join(f"{a}: {k['ad']}" for a, k in yv.KOMBINASYONLAR.items())},
           {"deger": ["kombinasyon_kumesi"]}, hucre={"deger": {"tur": "secim", "secenekler": list(yv.KOMBINASYONLAR)}}),
        _R({"parametre": "Çatlamış kesit rijitliği (TBDY 4.5.8)",
            "deger": (B.analiz["catlamis_rijitlik"] if B else an.get("catlamis_rijitlik")), "birim": "",
            "aciklama": "betonarme + deprem: zorunlu (Tablo 4.2)"},
           {"deger": ["analiz", "catlamis_rijitlik"]}, hucre={"deger": {"tur": "bool"}}),
        _R({"parametre": "Kiriş öz ağırlığı", "deger": (B.analiz["kiris_oz"] if B else an.get("kiris_oz", "net")), "birim": "",
            "aciklama": "net: b·(h − t), döşeme içindeki kısım döşemede sayılır; brut: b·h"},
           {"deger": ["analiz", "kiris_oz"]}, hucre={"deger": {"tur": "secim", "secenekler": ["net", "brut"]}}),
        _R({"parametre": "Çelik kiriş yanal tutulma L_b", "deger": (B.analiz["celik_Lb"] if B else an.get("celik_Lb", "otomatik")),
            "birim": "", "aciklama": "otomatik: döşemeli kirişte pozitif momentte L_b = 0; boy: L_b = açıklık"},
           {"deger": ["analiz", "celik_Lb"]}, hucre={"deger": {"tur": "secim", "secenekler": ["otomatik", "boy"]}}),
        _R({"parametre": "Diyagram nokta sayısı", "deger": (B.analiz["diyagram_nokta"] if B else an.get("diyagram_nokta", 11)),
            "birim": "", "aciklama": "eleman başına iç kuvvet istasyonu (3–41)"},
           {"deger": ["analiz", "diyagram_nokta"]}, hucre={"deger": {"tur": "sayi", "ondalik": 0}}),
    ]
    if c.okuma_hatasi:
        satirlar.append(_R({"parametre": "Model denetimi", "deger": "hata", "birim": "", "aciklama": c.okuma_hatasi},
                           hucre={"deger": {"tur": "metin"}}))
    return _T("genel", "Genel Parametreler", "Model",
              [_S("parametre", "Parametre", tur="metin"), _S("deger", "Değer", duzenlenebilir=True),
               _S("birim", "Birim", tur="metin"), _S("aciklama", "Açıklama", tur="metin")],
              satirlar, "Bina düzeyindeki seçimler: sistem, kombinasyon kümesi, analiz seçenekleri.",
              "TS 500 md. 6.2.6; ÇYTHYE 5.3; TBDY 2018 md. 4.4.4, 4.5.8")


def _t_katlar(c):
    ham, B = c.ham, c.B
    satirlar = []
    if B:
        for kt in B.katlar:
            satirlar.append(_R({"no": kt["no"], "ad": kt["ad"], "kot": kt["kot"], "h": kt["h"] if kt["no"] else None},
                               {"ad": _liste_yolu(ham, "katlar", kt["no"], "ad", ilk=0),
                                "kot": _liste_yolu(ham, "katlar", kt["no"], "kot", ilk=0)}))
    else:
        onceki = None
        for i, kt in enumerate(ham.get("katlar") or []):
            if not isinstance(kt, dict):
                continue
            no = kt.get("no", i)
            kot = kt.get("kot")
            h = (kot - onceki) if isinstance(kot, (int, float)) and isinstance(onceki, (int, float)) else None
            satirlar.append(_R({"no": no, "ad": kt.get("ad") or "", "kot": kot, "h": h},
                               {"ad": _liste_yolu(ham, "katlar", no, "ad", ilk=0), "kot": _liste_yolu(ham, "katlar", no, "kot", ilk=0)}))
            onceki = kot
    return _T("katlar", "Katlar", "Model",
              [_S("no", "Kat", tur="sayi", ondalik=0), _S("ad", "Ad", tur="metin", duzenlenebilir=True),
               _S("kot", "Kot", "m", duzenlenebilir=True, ondalik=2), _S("h", "Kat yüksekliği", "m", ondalik=2)],
              satirlar, "Kat 0 temel seviyesidir. Kat yüksekliği h = kot_k − kot_(k−1); yüksekliği değiştirmek için kotu düzenleyin "
                        "(üst katların kotları ayrı ayrı girilir).", "")


def _t_akslar(c):
    ham, B = c.ham, c.B
    satirlar = []
    if B:
        for yon in ("x", "y"):
            liste = B.akslar[yon]
            for i, a in enumerate(liste):
                aralik = liste[i + 1]["konum"] - a["konum"] if i + 1 < len(liste) else None
                satirlar.append(_R({"yon": yon.upper(), "ad": a["ad"], "konum": a["konum"], "aralik": aralik},
                                   {"konum": _aks_yolu(ham, yon, a["ad"], "konum")}))
    else:
        for yon in ("x", "y"):
            for a in ((ham.get("akslar") or {}).get(yon) or []):
                if isinstance(a, dict):
                    satirlar.append(_R({"yon": yon.upper(), "ad": str(a.get("ad", "")), "konum": a.get("konum"), "aralik": None},
                                       {"konum": _aks_yolu(ham, yon, str(a.get("ad", "")), "konum")}))
    return _T("akslar", "Akslar", "Model",
              [_S("yon", "Doğrultu", tur="metin"), _S("ad", "Aks", tur="metin"), _S("konum", "Konum", "m", duzenlenebilir=True, ondalik=2),
               _S("aralik", "Sonraki aksa aralık", "m", ondalik=2)],
              satirlar, "X doğrultusu harfli akslar (A, B, …), Y doğrultusu sayılı akslar (1, 2, …). Aks konumu değişince bütün "
                        "kolon, kiriş ve döşemeler yeni konuma taşınır.", "")


def _ag_dugumleri(c):
    """[(no, adres, X, Y, Z, kat, aks)] — çözümden ya da aks–kat modelinden (kullanılan kesişimler)."""
    if c.veri and (c.veri.get("ag") or {}).get("dugumler"):
        return [(d["no"], d.get("adres", ""), d["X"], d["Y"], d["Z"], d.get("kat"), d.get("aks")) for d in c.veri["ag"]["dugumler"]]
    B = c.B
    if not B:
        return []
    kume = set()
    for col in B.kolonlar:
        kume.add((col["kat"] - 1, col["ix"], col["iy"]))
        kume.add((col["kat"], col["ix"], col["iy"]))
    for k in B.kirisler:
        for i in range(k["i0"], k["i1"] + 1):
            kume.add((k["kat"], i, k["sabit"]) if k["yon"] == "x" else (k["kat"], k["sabit"], i))
    sonuc = []
    for kat, ix, iy in sorted(kume):
        no = c.yapi._dugum_no(kat, ix, iy)
        sonuc.append((no, f"{B.xad[ix]}{B.yad[iy]}/k{kat}", B.xk[ix], B.yk[iy], B.kat[kat]["kot"], kat, [B.xad[ix], B.yad[iy]]))
    return sonuc


def _t_dugumler(c):
    ham = c.ham
    satirlar = []
    serbest = {d.get("no"): (i, d) for i, d in enumerate(ham.get("dugumler") or []) if isinstance(d, dict)}
    gorulen = set()
    for no, adres, X, Y, Z, kat, aks in _ag_dugumleri(c):
        yol = {}
        if no in serbest:
            gorulen.add(no)
            yol = {a: _liste_yolu(ham, "dugumler", no, a) for a in ("X", "Y", "Z")}
        satirlar.append(_R({"no": no, "adres": adres, "X": X, "Y": Y, "Z": Z, "kat": kat,
                            "tur": "serbest" if no in serbest else "aks–kat"}, yol))
    for no, (i, d) in serbest.items():
        if no in gorulen:
            continue
        satirlar.append(_R({"no": no, "adres": str(d.get("ad") or f"D{no}"), "X": d.get("X"), "Y": d.get("Y"), "Z": d.get("Z"),
                            "kat": d.get("kat"), "tur": "serbest"},
                           {a: _liste_yolu(ham, "dugumler", no, a) for a in ("X", "Y", "Z")}))
    return _T("dugumler", "Düğüm Koordinatları", "Model",
              [_S("no", "Düğüm", ondalik=0), _S("adres", "Adres", tur="metin"), _S("X", "X", "m", duzenlenebilir=True, ondalik=3),
               _S("Y", "Y", "m", duzenlenebilir=True, ondalik=3), _S("Z", "Z", "m", duzenlenebilir=True, ondalik=3),
               _S("kat", "Kat", ondalik=0), _S("tur", "Tür", tur="metin")],
              satirlar, "Bina koordinatı: X sağa, Y plan derinliği, Z yukarı. Aks–kat düğümleri (no = 1000·kat + 20·i_x + i_y + 1) aks "
                        "konumlarından ve kat kotlarından gelir (Akslar / Katlar tablosundan düzenlenir); serbest düğümler (≥ 100000) "
                        "burada düzenlenir.", "")


def _uzunluk(p, q):
    if p is None or q is None:
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p, q)))


def _cubuk_kayitlari(c):
    """Bina çubukları (kolon, kiriş, serbest çubuk) tek listede: metraj ve Çubuklar tablosu için."""
    ham, B = c.ham, c.B
    kayit = []
    if B:
        for col in B.kolonlar:
            kayit.append({"tur": "kolon", "no": col["no"], "adres": col["adres"], "kat": col["kat"], "kesit": col["kesit"],
                          "i": f"{col['aks'][0]}{col['aks'][1]}/k{col['kat'] - 1}", "j": f"{col['aks'][0]}{col['aks'][1]}/k{col['kat']}",
                          "L": col["L"], "yon": col["yon"], "duvar": None, "aci": None, "serbest": "", "liste": "kolonlar", "ham": col})
        for k in B.kirisler:
            kayit.append({"tur": "kiris", "no": k["no"], "adres": k["adres"], "kat": k["kat"], "kesit": k["kesit"],
                          "i": f"{k['bas'][0]}{k['bas'][1]}/k{k['kat']}", "j": f"{k['son'][0]}{k['son'][1]}/k{k['kat']}",
                          "L": k["L"], "yon": k["yon"], "duvar": k["duvar"], "aci": None, "serbest": "", "liste": "kirisler", "ham": k})
    for i, cb in enumerate(ham.get("cubuklar") or []):
        if not isinstance(cb, dict):
            continue
        p, q = c.ref_koordinat(cb.get("i")), c.ref_koordinat(cb.get("j"))
        serb = cb.get("serbest") if isinstance(cb.get("serbest"), dict) else {}
        serb_m = "; ".join(f"{u}: {','.join(v)}" for u, v in serb.items() if v)
        kayit.append({"tur": str(cb.get("tur") or "diger"), "no": cb.get("no", i + 1), "adres": f"C{cb.get('no', i + 1)}",
                      "kat": cb.get("kat"), "kesit": str(cb.get("kesit") or ""), "i": _ref_metin(cb.get("i")), "j": _ref_metin(cb.get("j")),
                      "L": _uzunluk(p, q), "yon": None, "duvar": None, "aci": cb.get("aci", 0), "serbest": serb_m,
                      "yalniz_cekme": bool(cb.get("yalniz_cekme", False)), "liste": "cubuklar", "ham": cb})
    return kayit


def _malzeme_adi(c, kesit_ad):
    kes = (c.ham.get("kesitler") or {}).get(kesit_ad) or {}
    return str(kes.get("malzeme") or "")


def _t_cubuklar(c):
    ham = c.ham
    kesitler = _kesit_secenekleri(ham)
    duvarlar = [{"deger": None, "etiket": "(duvar yok)"}] + sorted(str(a) for a in (ham.get("duvarlar") or {}))
    satirlar = []
    for k in _cubuk_kayitlari(c):
        yol = {"kesit": _liste_yolu(ham, k["liste"], k["no"], "kesit")}
        if k["tur"] == "kolon":
            yol["yon"] = _liste_yolu(ham, "kolonlar", k["no"], "yon")
        if k["liste"] == "kirisler":
            yol["duvar"] = _liste_yolu(ham, "kirisler", k["no"], "duvar")
        if k["liste"] == "cubuklar":
            yol["aci"] = _liste_yolu(ham, "cubuklar", k["no"], "aci")
            yol["yalniz_cekme"] = _liste_yolu(ham, "cubuklar", k["no"], "yalniz_cekme")
        satirlar.append(_R({"tur": k["tur"], "no": k["no"], "adres": k["adres"], "kat": k["kat"], "i": k["i"], "j": k["j"],
                            "kesit": k["kesit"], "malzeme": _malzeme_adi(c, k["kesit"]), "yon": k["yon"], "duvar": k["duvar"],
                            "L": k["L"], "aci": k["aci"], "serbest": k["serbest"], "yalniz_cekme": k.get("yalniz_cekme")}, yol))
    return _T("cubuklar", "Çubuklar (Kolon, Kiriş, Çapraz…)", "Model",
              [_S("tur", "Tür", tur="metin"), _S("no", "No", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("i", "i ucu", tur="metin"), _S("j", "j ucu", tur="metin"),
               _S("kesit", "Kesit", tur="secim", duzenlenebilir=True, secenekler=kesitler), _S("malzeme", "Malzeme", tur="metin"),
               _S("yon", "Kolon yönü", tur="secim", duzenlenebilir=True, secenekler=["x", "y"]),
               _S("duvar", "Duvar", tur="secim", duzenlenebilir=True, secenekler=duvarlar, bos_olur=True),
               _S("L", "Uzunluk", "m", ondalik=3), _S("aci", "Yerel eksen açısı", "°", duzenlenebilir=True, ondalik=1),
               _S("serbest", "Uç serbestlikleri", tur="metin"), _S("yalniz_cekme", "Yalnız çekme", tur="bool", duzenlenebilir=True)],
              satirlar, "Kolon kat k: kot_(k−1) → kot_k; kiriş küçük akstan büyük aksa. Kolon yönü x: güçlü eksen (h) X doğrultusunda. "
                        "Kesit, yön ve duvar atamaları buradan değiştirilebilir.",
              "TS 500; ÇYTHYE 2018; bina modeli §2–§3")


def _t_kesitler(c):
    ham, B = c.ham, c.B
    malz = sorted(str(a) for a in (ham.get("malzemeler") or {}))
    profiller = list(yv.PROFILLER)
    satirlar = []
    for ad, kayit in (ham.get("kesitler") or {}).items():
        if not isinstance(kayit, dict):
            continue
        ks = (B.kesitler.get(str(ad)) if B else None) or {}
        tip = str(kayit.get("tip", "dikdortgen")).strip().lower()
        p = yv.PROFILLER.get(ks.get("profil") or "") or {}
        A = ks.get("A")
        Ig, Iz = ks.get("I_guclu"), ks.get("I_zayif")
        i_g = math.sqrt(Ig / A) if (A and Ig) else None
        i_z = math.sqrt(Iz / A) if (A and Iz) else None
        yol = {"malzeme": ["kesitler", ad, "malzeme"]}
        if tip == "dikdortgen":
            yol.update({"b": ["kesitler", ad, "b"], "h": ["kesitler", ad, "h"]})
        elif tip == "profil":
            yol["profil"] = ["kesitler", ad, "profil"]
        satirlar.append(_R({
            "ad": str(ad), "tip": tip, "profil": ks.get("profil") or kayit.get("profil"), "malzeme": str(kayit.get("malzeme", "")),
            "b": ks.get("b", kayit.get("b")), "h": ks.get("h", kayit.get("h")),
            "A": A * 1e4 if A else None, "Iy": Ig * 1e8 if Ig else None, "Iz": Iz * 1e8 if Iz else None,
            "J": ks.get("J") * 1e8 if ks.get("J") else None, "Wel": ks.get("Wel") * 1e6 if ks.get("Wel") else None,
            "Wpl": ks.get("Wpl") * 1e6 if ks.get("Wpl") else None, "iy": i_g * 100 if i_g else None, "iz": i_z * 100 if i_z else None,
            "g": p.get("g") if p else (A * c_gamma(c, kayit) / 9.81 * 1000 if A and c_gamma(c, kayit) else None)}, yol))
    return _T("kesitler", "Kesitler", "Model",
              [_S("ad", "Kesit", tur="metin"), _S("tip", "Tip", tur="metin"),
               _S("profil", "Profil", tur="secim", duzenlenebilir=True, secenekler=profiller),
               _S("malzeme", "Malzeme", tur="secim", duzenlenebilir=True, secenekler=malz),
               _S("b", "b", "m", duzenlenebilir=True, ondalik=3), _S("h", "h", "m", duzenlenebilir=True, ondalik=3),
               _S("A", "A", "cm²", ondalik=1), _S("Iy", "I (güçlü)", "cm⁴", ondalik=0), _S("Iz", "I (zayıf)", "cm⁴", ondalik=0),
               _S("J", "J", "cm⁴", ondalik=0), _S("Wel", "W_el", "cm³", ondalik=0), _S("Wpl", "W_pl", "cm³", ondalik=0),
               _S("iy", "i (güçlü)", "cm", ondalik=2), _S("iz", "i (zayıf)", "cm", ondalik=2), _S("g", "Birim ağırlık", "kg/m", ondalik=1)],
              satirlar, "Dikdörtgen: A = b·h, I = b·h³/12, J ≈ β·c³·a (β = 1/3 − 0,21(c/a)(1 − c⁴/12a⁴)), W_pl = b·h²/4. Profil: katalog "
                        "değerleri (I güçlü = I_y Avrupa kuralı). Boyut değişikliği o kesiti kullanan bütün elemanlara yansır.",
              "yapi_veri.PROFILLER (Avrupa profil kataloğu / EN 10365); TS 500")


def c_gamma(c, kayit):
    """Kesit malzemesinin birim hacim ağırlığı (kN/m³) ya da None."""
    mad = str(kayit.get("malzeme", ""))
    if c.B and mad in c.B.malzemeler:
        return c.B.malzemeler[mad]["gamma"]
    return None


def _t_malzemeler(c):
    ham, B = c.ham, c.B
    secenek = list(yv.BETONLAR) + list(yv.CELIKLER) + list(yv.DONATILAR)
    satirlar = []
    for ad, kayit in (ham.get("malzemeler") or {}).items():
        if not isinstance(kayit, dict):
            continue
        m = (B.malzemeler.get(str(ad)) if B else None) or {}
        tur = m.get("tur")
        if tur == "beton":
            kart = yv.BETONLAR.get(m["kutuphane"], {})
            dayanim, f_d = m.get("fck"), kart.get("fcd")
        elif tur == "celik":
            dayanim, f_d = m.get("Fy"), None
        elif tur == "donati":
            kart = yv.DONATILAR.get(m["kutuphane"], {})
            dayanim, f_d = m.get("fyk"), kart.get("fyd")
        else:
            dayanim = f_d = None
        satirlar.append(_R({"ad": str(ad), "kutuphane": m.get("kutuphane", kayit.get("kutuphane")), "tur": tur or "",
                            "dayanim": dayanim, "tasarim": f_d, "E": m.get("E_MPa"), "G": m.get("G_MPa"), "gamma": m.get("gamma"),
                            "kaynak": m.get("kaynak", "")},
                           {"kutuphane": ["malzemeler", ad, "kutuphane"]}))
    return _T("malzemeler", "Malzemeler", "Model",
              [_S("ad", "Malzeme", tur="metin"), _S("kutuphane", "Sınıf (kütüphane)", tur="secim", duzenlenebilir=True, secenekler=secenek),
               _S("tur", "Tür", tur="metin"), _S("dayanim", "f_ck / F_y / f_yk", "MPa", ondalik=0),
               _S("tasarim", "f_cd / f_yd", "MPa", ondalik=2), _S("E", "E", "MPa", ondalik=0), _S("G", "G", "MPa", ondalik=0),
               _S("gamma", "γ", "kN/m³", ondalik=1), _S("kaynak", "Kaynak", tur="metin")],
              satirlar, "Beton: f_cd = f_ck/1,5; donatı: f_yd = f_yk/1,15; çelik: F_y (t ≤ 16 mm).",
              "TS 500:2000 Çizelge 3.2; TS 708; ÇYTHYE 2018 Tablo 2.1A")


def _t_dosemeler(c):
    ham, B = c.ham, c.B
    kullanim = list(yv.TS498_HAREKETLI)
    satirlar = []
    kaynak_d = B.dosemeler if B else [d for d in (ham.get("dosemeler") or []) if isinstance(d, dict)]
    for i, d in enumerate(kaynak_d):
        no = d.get("no", i + 1)
        if B:
            deg = {"no": no, "adres": d["adres"], "kat": d["kat"], "lx": d["dx"], "ly": d["dy"], "h": d["h"], "kullanim": d["kullanim"],
                   "dagitim": d["dagitim"], "alan": d["dx"] * d["dy"]}
        else:
            deg = {"no": no, "adres": "", "kat": d.get("kat"), "lx": None, "ly": None, "h": d.get("h"), "kullanim": d.get("kullanim"),
                   "dagitim": d.get("dagitim", "otomatik"), "alan": None}
        satirlar.append(_R(deg, {a: _liste_yolu(ham, "dosemeler", no, a) for a in ("h", "kullanim", "dagitim")}))
    return _T("dosemeler", "Döşemeler", "Model",
              [_S("no", "No", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("lx", "Δx", "m", ondalik=2), _S("ly", "Δy", "m", ondalik=2), _S("h", "Kalınlık t", "m", duzenlenebilir=True, ondalik=3),
               _S("kullanim", "Kullanım sınıfı", tur="secim", duzenlenebilir=True, secenekler=kullanim),
               _S("dagitim", "Dağıtım", tur="secim", duzenlenebilir=True, secenekler=["otomatik", "cift", "tek"]),
               _S("alan", "Alan (aks-aks)", "m²", ondalik=2)],
              satirlar, "Tek hücrelik dikdörtgen paneller. Dağıtım otomatik: m = l_u/l_k ≤ 2 çift doğrultulu (45° kuralı), > 2 tek doğrultulu.",
              "TS 500 md. 11.4.3; TS 498:2021 Çizelge 6", toplam=_topla(satirlar, "alan"))


def _poligon_alani(noktalar):
    """3B düzlemsel çokgen alanı (Newell)."""
    if not noktalar or any(p is None for p in noktalar) or len(noktalar) < 3:
        return None, None
    nx = ny = nz = 0.0
    for i, p in enumerate(noktalar):
        q = noktalar[(i + 1) % len(noktalar)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    alan = 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
    return alan, 0.5 * abs(nz)      # yüzey alanı, yatay izdüşüm


def _t_paneller(c):
    ham = c.ham
    if not isinstance(ham.get("paneller"), list) or not ham["paneller"]:
        return None
    satirlar = []
    for i, p in enumerate(ham["paneller"]):
        if not isinstance(p, dict):
            continue
        no = p.get("no", i + 1)
        noktalar = [c.ref_koordinat(r) for r in (p.get("kose") or [])]
        alan, izd = _poligon_alani(noktalar)
        satirlar.append(_R({"no": no, "tur": p.get("tur", "doseme"), "kose": " – ".join(_ref_metin(r) for r in p.get("kose") or []),
                            "kalinlik": p.get("kalinlik", 0.0), "g": p.get("g", 0.0), "q": p.get("q"), "kullanim": p.get("kullanim"),
                            "kar": bool(p.get("kar", False)), "dagitim": p.get("dagitim", "iki"), "alan": alan, "izdusum": izd},
                           {a: _liste_yolu(ham, "paneller", no, a) for a in ("kalinlik", "g", "q", "kullanim", "kar", "dagitim")}))
    return _T("paneller", "Paneller (Döşeme / Çatı / Cephe)", "Model",
              [_S("no", "No", ondalik=0), _S("tur", "Tür", tur="metin"), _S("kose", "Köşeler", tur="metin"),
               _S("kalinlik", "Kalınlık", "m", duzenlenebilir=True, ondalik=3), _S("g", "Ek sabit g", "kN/m²", duzenlenebilir=True, ondalik=2),
               _S("q", "Hareketli q", "kN/m²", duzenlenebilir=True, ondalik=2, bos_olur=True),
               _S("kullanim", "Kullanım", tur="secim", duzenlenebilir=True, secenekler=list(yv.TS498_HAREKETLI), bos_olur=True),
               _S("kar", "Kar", tur="bool", duzenlenebilir=True),
               _S("dagitim", "Dağıtım", tur="secim", duzenlenebilir=True, secenekler=["iki", "tek-13", "tek-24", "yok"]),
               _S("alan", "Yüzey alanı", "m²", ondalik=2), _S("izdusum", "Yatay izdüşüm", "m²", ondalik=2)],
              satirlar, "Serbest model panelleri (surum 3). Kalınlık 0: taşıyıcı olmayan kaplama (sac).", "§12.2",
              toplam=_topla(satirlar, "alan", "izdusum"))


def _t_mesnetler(c):
    ham, B = c.ham, c.B
    satirlar = []
    if c.veri and (c.veri.get("ag") or {}).get("mesnetler"):
        adres = {d["no"]: d.get("adres", "") for d in c.veri["ag"].get("dugumler") or []}
        for m in c.veri["ag"]["mesnetler"]:
            satirlar.append(_R({"dugum": m["dugum"], "adres": adres.get(m["dugum"], ""), "tip": m.get("tip", ""),
                                "ux": None, "uy": None, "uz": None, "rx": None, "ry": None, "rz": None}))
    elif B:
        for col in B.kolonlar:
            if col["kat"] != 1:
                continue
            satirlar.append(_R({"dugum": c.yapi._dugum_no(0, col["ix"], col["iy"]), "adres": f"{col['aks'][0]}{col['aks'][1]}/k0",
                                "tip": B.temeller["mesnet"], "ux": None, "uy": None, "uz": None, "rx": None, "ry": None, "rz": None}))
    for t in satirlar:
        tip = t["degerler"]["tip"]
        tut = {"ankastre": (True,) * 6, "mafsal": (True, True, True, False, False, False)}.get(tip)
        if tut:
            t["degerler"].update(dict(zip(("ux", "uy", "uz", "rx", "ry", "rz"), tut)))
    for i, m in enumerate(ham.get("mesnetler") or []):
        if not isinstance(m, dict):
            continue
        satirlar.append(_R({"dugum": _ref_metin(m.get("dugum")), "adres": "serbest", "tip": "serbest",
                            **{a: bool(m.get(a, False)) for a in ("ux", "uy", "uz", "rx", "ry", "rz")}},
                           {a: ["mesnetler", i, a] for a in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    return _T("mesnetler", "Mesnetler", "Model",
              [_S("dugum", "Düğüm", tur="metin"), _S("adres", "Adres", tur="metin"), _S("tip", "Tip", tur="metin")]
              + [_S(a, a, tur="bool", duzenlenebilir=True) for a in ("ux", "uy", "uz", "rx", "ry", "rz")],
              satirlar, "Kolon tabanları temel mesnet tipine göre tutulur (ankastre: 6 SD; mafsal: ötelemeler; elastik: Winkler yayları "
                        "k_Z = k0·B·L, k_rX = k0·B·L³/12). Mesnet tipi Temel Parametreleri tablosundan değişir.",
              "TS 500; Winkler zemin modeli")


def _temel_listesi(c):
    """[{kolon_no, aks, B, L, h, ozel}] kolon tabanları için (çözümden ya da modelden)."""
    B = c.B
    if not B:
        return []
    ozel = B.temeller["ozel"]
    h = B.temeller["varsayilan"]["h"]
    sonuc = []
    for col in B.kolonlar:
        if col["kat"] != 1:
            continue
        o = ozel.get((col["ix"], col["iy"]))
        bb = o or B.temeller["varsayilan"]
        sonuc.append({"kolon_no": col["no"], "aks": list(col["aks"]), "B": bb["B"], "L": bb["L"], "h": h, "ozel": o is not None})
    return sonuc


def _t_temeller(c):
    satirlar = []
    for t in _temel_listesi(c):
        sec = {"aks": t["aks"], "_olustur": True}
        satirlar.append(_R({"kolon_no": t["kolon_no"], "aks": f"{t['aks'][0]}{t['aks'][1]}", "B": t["B"], "L": t["L"], "h": t["h"],
                            "alan": t["B"] * t["L"], "ozel": t["ozel"]},
                           {"B": ["temeller", "ozel", sec, "B"], "L": ["temeller", "ozel", sec, "L"]}))
    return _T("temeller", "Temeller (Tekil)", "Model",
              [_S("kolon_no", "Kolon", ondalik=0), _S("aks", "Aks", tur="metin"), _S("B", "B", "m", duzenlenebilir=True, ondalik=2),
               _S("L", "L", "m", duzenlenebilir=True, ondalik=2), _S("h", "h", "m", ondalik=2), _S("alan", "Taban alanı", "m²", ondalik=2),
               _S("ozel", "Özel boyut", tur="bool")],
              satirlar, "Her kolon tabanında tekil temel. Varsayılan boyut Temel Parametreleri tablosundadır; burada bir temelin B/L'si "
                        "değişince o aks için 'temeller.ozel' kaydı oluşturulur.", "TS 500 md. 15", toplam=_topla(satirlar, "alan"))


# ============================================================================
# YÜKLER
# ============================================================================
def _t_yuk_durumlari(c):
    ham, B, Y = c.ham, c.B, c.Y
    yd = ham.get("yuk_durumlari") if isinstance(ham.get("yuk_durumlari"), dict) else {}
    dep = ham.get("deprem") if isinstance(ham.get("deprem"), dict) else {}
    toplam = (c.veri or {}).get("yukler", {}).get("toplam") if c.veri else None
    toplam = toplam or (Y.toplam if Y else {})
    satirlar = []
    for ad in ("G", "Q", "S", "W", "E"):
        kayit = yd.get(ad) if isinstance(yd.get(ad), dict) else {}
        if ad in ("G", "Q"):
            acik = True
        elif ad == "S":
            acik = bool(B.kar) if B else bool(kayit.get("acik"))
        elif ad == "W":
            acik = bool(B.ruzgar) if B else bool(kayit.get("acik"))
        else:
            acik = bool(B.deprem) if B else bool(kayit.get("acik") or dep.get("etkin"))
        if c.veri:
            if ad == "W" and c.veri.get("ruzgar"):
                tpl = max(c.veri["ruzgar"].get("toplam_x") or 0.0, c.veri["ruzgar"].get("toplam_y") or 0.0)
            elif ad == "E" and c.veri.get("deprem"):
                tpl = c.veri["deprem"].get("VtE")
            else:
                tpl = toplam.get(ad)
        else:
            tpl = toplam.get(ad)
        satirlar.append(_R({"ad": ad, "aciklama": _DURUM_AD[ad], "acik": acik, "toplam": tpl,
                            "not": {"W": "yatay, en büyük doğrultu (kN)", "E": "taban kesme kuvveti V_tE (kN)"}.get(ad, "düşey toplam (kN)")},
                           {"acik": ["yuk_durumlari", ad, "acik"] if ad in ("S", "W", "E") else None}))
    return _T("yuk_durumlari", "Yük Durumları", "Yükler",
              [_S("ad", "Durum", tur="metin"), _S("aciklama", "Açıklama", tur="metin"), _S("acik", "Etkin", tur="bool", duzenlenebilir=True),
               _S("toplam", "Toplam", "kN", ondalik=2), _S("not", "Not", tur="metin")],
              satirlar, "Her durum ayrı çözülür (yük deseni); birleşimler katsayılarla toplanır. Deprem durumu deprem kartı "
                        "etkin olunca (E açık ya da deprem.etkin) EX±, EY± ve EZ alt durumlarına açılır.",
              "TS 498:2021; TBDY 2018 md. 4.4")


def _dos_yuk_kayitlari(c):
    if c.veri and (c.veri.get("yukler") or {}).get("dosemeler") is not None:
        return c.veri["yukler"]["dosemeler"]
    if not c.Y:
        return []
    return [{"no": d["no"], "kat": d["kat"], "lx": d["lx"], "ly": d["ly"], "m": d["m"], "tip": d["tip"], "g": d["g"], "q": d["q_top"],
             "g_plak": d["g_plak"], "g_ek": d["g_ek"] + d["ek_g"], "alan": d["alan"], "G_toplam": d["G_toplam"], "Q_toplam": d["Q_toplam"],
             "q_kaynak": d["q_kaynak"], "paylar": d["paylar"]} for d in c.Y.dosemeler]


def _t_doseme_yukleri(c):
    ham = c.ham
    adres = {d["no"]: d["adres"] for d in c.B.dosemeler} if c.B else {}
    satirlar = []
    for d in _dos_yuk_kayitlari(c):
        qe = {"kisa": [0.0, 0.0], "uzun": [0.0, 0.0]}
        for p in d.get("paylar") or []:
            k = p.get("kenar")
            if k in qe:
                qe[k][0] = max(qe[k][0], p.get("q_eM_g") or 0.0)
                qe[k][1] = max(qe[k][1], p.get("q_eM_q") or 0.0)
        no = d["no"]
        satirlar.append(_R({"no": no, "adres": adres.get(no, ""), "kat": d["kat"], "lk": d["lx"], "lu": d["ly"], "m": d["m"],
                            "tip": d["tip"], "g_plak": d["g_plak"], "g_ek": d["g_ek"], "g": d["g"], "q": d["q"], "alan": d["alan"],
                            "G_toplam": d["G_toplam"], "Q_toplam": d["Q_toplam"],
                            "qeM_g_kisa": qe["kisa"][0], "qeM_g_uzun": qe["uzun"][0], "qeM_q_kisa": qe["kisa"][1], "qeM_q_uzun": qe["uzun"][1],
                            "kaynak": d.get("q_kaynak", "")},
                           {"g_ek": _liste_yolu(ham, "dosemeler", no, "g_ek"), "q": _liste_yolu(ham, "dosemeler", no, "q")}))
    return _T("doseme_yukleri", "Döşeme Yükleri", "Yükler",
              [_S("no", "No", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("lk", "l_k (kısa)", "m", ondalik=2), _S("lu", "l_u (uzun)", "m", ondalik=2), _S("m", "m = l_u/l_k", ondalik=3),
               _S("tip", "Doğrultu", tur="metin"), _S("g_plak", "g_plak = γ·t", "kN/m²", ondalik=2),
               _S("g_ek", "g_ek (kaplama)", "kN/m²", duzenlenebilir=True, ondalik=2), _S("g", "g", "kN/m²", ondalik=2),
               _S("q", "q", "kN/m²", duzenlenebilir=True, ondalik=2, bos_olur=True), _S("alan", "Alan", "m²", ondalik=2),
               _S("G_toplam", "G toplam", "kN", ondalik=2), _S("Q_toplam", "Q toplam", "kN", ondalik=2),
               _S("qeM_g_kisa", "q_eM,g kısa kenar", "kN/m", ondalik=2), _S("qeM_g_uzun", "q_eM,g uzun kenar", "kN/m", ondalik=2),
               _S("qeM_q_kisa", "q_eM,q kısa kenar", "kN/m", ondalik=2), _S("qeM_q_uzun", "q_eM,q uzun kenar", "kN/m", ondalik=2),
               _S("kaynak", "q kaynağı", tur="metin")],
              satirlar, "g = 25·t + g_ek (+ ek alan yükü); q boş bırakılırsa kullanım sınıfından (TS 498 Çizelge 6). Eşdeğer düzgün yükler "
                        "(moment eşdeğeri) yalnız el hesabı içindir: üçgen p·l_k/3, trapez (p·l_k/2)(1 − 1/(3m²)); FE'ye gerçek üçgen/trapez "
                        "yük gider.", "TS 498:2021 Çizelge 6; TS 500 md. 11.4.3",
              toplam=_topla(satirlar, "alan", "G_toplam", "Q_toplam"))


def _kiris_yukleri(c):
    if c.veri and (c.veri.get("yukler") or {}).get("kirisler") is not None:
        return c.veri["yukler"]["kirisler"]
    return c.Y.kirisler if c.Y else []


def _t_duvar_yukleri(c):
    ham, B = c.ham, c.B
    if not B:
        return _T("duvar_yukleri", "Duvar Yükleri", "Yükler", [], [], "Model okunamadı: " + (c.okuma_hatasi or ""), "")
    duvarlar = [{"deger": None, "etiket": "(duvar yok)"}] + sorted(str(a) for a in (ham.get("duvarlar") or {}))
    satirlar = []
    for k in B.kirisler:
        w = B.duvarlar[k["duvar"]]["deger"] if k["duvar"] else 0.0
        hd = k["h_duvar"] if k["duvar"] else None
        gd = w * hd if k["duvar"] else 0.0
        satirlar.append(_R({"kiris": k["no"], "adres": k["adres"], "kat": k["kat"], "duvar": k["duvar"],
                            "w": w if k["duvar"] else None, "h_duvar": hd, "h_kaynak": k.get("h_duvar_kaynak", "") if k["duvar"] else "",
                            "g_d": gd, "L": k["L"], "toplam": gd * k["L"], "alan": (hd or 0.0) * k["L"]},
                           {"duvar": _liste_yolu(ham, "kirisler", k["no"], "duvar"), "h_duvar": _liste_yolu(ham, "kirisler", k["no"], "duvar_h")}))
    return _T("duvar_yukleri", "Duvar Yükleri", "Yükler",
              [_S("kiris", "Kiriş", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("duvar", "Duvar", tur="secim", duzenlenebilir=True, secenekler=duvarlar, bos_olur=True),
               _S("w", "Duvar ağırlığı", "kN/m²", ondalik=2),
               _S("h_duvar", "Duvar yüksekliği", "m", duzenlenebilir=True, ondalik=2, bos_olur=True),
               _S("h_kaynak", "Yükseklik kaynağı", tur="metin"), _S("g_d", "g_d = w·h", "kN/m", ondalik=2),
               _S("L", "Kiriş boyu", "m", ondalik=2), _S("toplam", "Toplam", "kN", ondalik=2), _S("alan", "Duvar alanı", "m²", ondalik=2)],
              satirlar, "Duvar yüksekliği boş: kat yüksekliği − kiriş yüksekliği; elle verilirse (ör. çatıda 1,0 m parapet) 'duvar_h'.",
              "TS 498:2021 md. 5 → TS ISO 9194; yapi_veri.DUVARLAR", toplam=_topla(satirlar, "toplam", "alan"))


def _t_kar_ruzgar(c):
    ham, B = c.ham, c.B
    S = ((ham.get("yuk_durumlari") or {}).get("S") or {}) if isinstance(ham.get("yuk_durumlari"), dict) else {}
    W = ((ham.get("yuk_durumlari") or {}).get("W") or {}) if isinstance(ham.get("yuk_durumlari"), dict) else {}
    kar = (c.veri or {}).get("kar") or (B.kar if B else None) or {}
    rz = B.ruzgar if B else None
    satirlar = [
        _R({"grup": "Kar", "parametre": "Kar yükü etkin", "deger": bool(B.kar) if B else bool(S.get("acik")), "birim": "", "kaynak": ""},
           {"deger": ["yuk_durumlari", "S", "acik"]}, hucre={"deger": {"tur": "bool"}}),
        _R({"grup": "Kar", "parametre": "Kar bölgesi", "deger": kar.get("bolge", S.get("bolge")), "birim": "", "kaynak": "TS 498:2021 Ek 1/2"},
           {"deger": ["yuk_durumlari", "S", "bolge"]}, hucre={"deger": {"tur": "secim", "secenekler": list(range(1, 10))}}),
        _R({"grup": "Kar", "parametre": "Rakım", "deger": kar.get("rakim", S.get("rakim", 0)), "birim": "m", "kaynak": ""},
           {"deger": ["yuk_durumlari", "S", "rakim"]}),
        _R({"grup": "Kar", "parametre": "S_k (zemin kar yükü)", "deger": kar.get("Sk", S.get("Sk")), "birim": "kN/m²",
            "kaynak": kar.get("Sk_kaynak", "TS 498:2021 Çizelge 3")}, {"deger": ["yuk_durumlari", "S", "Sk"]}, hucre={"deger": {"bos_olur": True}}),
        _R({"grup": "Kar", "parametre": "μ1 (şekil katsayısı)", "deger": kar.get("mu", S.get("mu", 0.8)), "birim": "",
            "kaynak": kar.get("mu_kaynak", "TS EN 1991-1-3 Tablo 5.2")}, {"deger": ["yuk_durumlari", "S", "mu"]}),
        _R({"grup": "Kar", "parametre": "C_e · C_t", "deger": (kar.get("Ce", 1.0) or 1.0) * (kar.get("Ct", 1.0) or 1.0), "birim": "", "kaynak": ""}),
        _R({"grup": "Kar", "parametre": "s = μ1·C_e·C_t·S_k (çatı)", "deger": kar.get("s"), "birim": "kN/m²", "kaynak": "TS EN 1991-1-3 Denk. 5.1"}),
        _R({"grup": "Kar", "parametre": "Çatı alanı / toplam S", "deger": kar.get("S_toplam"), "birim": "kN",
            "kaynak": f"çatı alanı {_n(kar.get('cati_alani'))} m²" if kar.get("cati_alani") is not None else ""}),
        _R({"grup": "Rüzgâr", "parametre": "Rüzgâr yükü etkin", "deger": bool(rz) if B else bool(W.get("acik")), "birim": "", "kaynak": ""},
           {"deger": ["yuk_durumlari", "W", "acik"]}, hucre={"deger": {"tur": "bool"}}),
        _R({"grup": "Rüzgâr", "parametre": "C (basınç + emme)", "deger": (rz or {}).get("C", W.get("C", yv.TS498_RUZGAR["C"])), "birim": "",
            "kaynak": (rz or {}).get("C_kaynak", "TS 498:2021 Çizelge 5")}, {"deger": ["yuk_durumlari", "W", "C"]}),
        _R({"grup": "Rüzgâr", "parametre": "Sarp yamaç (q ≥ 1,1)", "deger": bool((rz or {}).get("sarp", W.get("sarp", False))), "birim": "",
            "kaynak": "TS 498:2021 md. 14.3"}, {"deger": ["yuk_durumlari", "W", "sarp"]}, hucre={"deger": {"tur": "bool"}}),
    ]
    for kt in ((c.veri or {}).get("ruzgar") or {}).get("katlar") or []:
        satirlar.append(_R({"grup": "Rüzgâr", "parametre": f"Kat {kt['kat']}: q(z = {_n(kt['z'])} m), F_x / F_y",
                            "deger": kt.get("q"), "birim": "kN/m²",
                            "kaynak": f"F_x = {_n(kt.get('F_x'))} kN, F_y = {_n(kt.get('F_y'))} kN (cephe {_n(kt.get('cephe_x'))} / {_n(kt.get('cephe_y'))} m²)"}))
    return _T("kar_ruzgar", "Kar ve Rüzgâr Yükleri", "Yükler",
              [_S("grup", "Yük", tur="metin"), _S("parametre", "Parametre", tur="metin"), _S("deger", "Değer", duzenlenebilir=True, ondalik=3),
               _S("birim", "Birim", tur="metin"), _S("kaynak", "Kaynak / not", tur="metin")],
              satirlar, "Kar yalnız en üst kat (çatı) döşemelerine, yatay izdüşüme; rüzgâr kat seviyelerine cephe alanı × C·q(z).",
              "TS 498:2021 md. 11 ve 14; TS EN 1991-1-3")


def _t_ek_yukler(c):
    ham = c.ham
    satirlar = []
    for i, y in enumerate(ham.get("ek_yukler") or []):
        if not isinstance(y, dict):
            continue
        tur = str(y.get("tur", ""))
        if tur == "kiris":
            hedef = f"Kiriş {y.get('kiris')}"
            alanlar = ("q",)
        elif tur == "dugum":
            hedef = _ref_metin(y.get("dugum")) if "dugum" in y else f"{(y.get('aks') or ['?', '?'])[0]}{(y.get('aks') or ['?', '?'])[1]}/k{y.get('kat', 1)}"
            alanlar = ("FX", "FY", "FZ", "MX", "MY", "MZ")
        elif tur == "doseme":
            hedef = f"Döşeme {y.get('doseme')}"
            alanlar = ("g", "q")
        elif tur == "cubuk":
            hedef = f"Çubuk {y.get('cubuk')} ({y.get('yon', 'Z')})"
            alanlar = ("q1", "q2")
        else:
            hedef, alanlar = "?", ()
        deg = {"sira": i + 1, "tur": tur, "hedef": hedef, "durum": y.get("durum", "G" if tur != "doseme" else ""),
               **{a: y.get(a) for a in ("q", "g", "q1", "q2", "FX", "FY", "FZ", "MX", "MY", "MZ")}}
        yol = {a: ["ek_yukler", i, a] for a in alanlar}
        if tur != "doseme":
            yol["durum"] = ["ek_yukler", i, "durum"]
        satirlar.append(_R(deg, yol))
    sut = [_S("sira", "Sıra", ondalik=0), _S("tur", "Tür", tur="metin"), _S("hedef", "Hedef", tur="metin"),
           _S("durum", "Durum", tur="secim", duzenlenebilir=True, secenekler=["G", "Q", "S"])]
    for a, b, birim in (("q", "q (aşağı +)", "kN/m"), ("g", "g", "kN/m²"), ("q1", "q1", "kN/m"), ("q2", "q2", "kN/m"),
                        ("FX", "FX", "kN"), ("FY", "FY", "kN"), ("FZ", "FZ", "kN"), ("MX", "MX", "kN·m"), ("MY", "MY", "kN·m"),
                        ("MZ", "MZ", "kN·m")):
        sut.append(_S(a, b, birim, duzenlenebilir=True, ondalik=2, bos_olur=True))
    return _T("ek_yukler", "Ek Yükler", "Yükler", sut, satirlar,
              "Kirişe çizgisel (q, aşağı pozitif), düğüme tekil (bina koordinatında; FZ yukarı +), döşemeye alan yükü (g, q). "
              "Yeni ek yük modelde (özellik paneli / JSON) eklenir; burada değerleri düzenlenir.", "TS 498:2021")


def _t_eleman_yukleri(c):
    B = c.B
    adres = {k["no"]: k["adres"] for k in B.kirisler} if B else {}
    satirlar = []
    for r in _kiris_yukleri(c):
        kn = r.get("kN_m") or {}
        L = r.get("L") or 0.0
        for durum in ("G", "Q", "S"):
            d = r.get(durum) or {}
            if durum == "S" and not (d.get("toplam_kN") or 0.0):
                continue
            if durum == "G":
                oz, duvar, ek = kn.get("oz"), kn.get("duvar"), kn.get("ek_G")
                qeM, qeV = kn.get("q_eM_G"), kn.get("q_eV_G")
            elif durum == "Q":
                oz = duvar = None
                ek, qeM, qeV = kn.get("ek_Q"), kn.get("q_eM_Q"), kn.get("q_eV_Q")
            else:
                oz = duvar = None
                ek, qeM, qeV = None, None, (d.get("toplam_kN") or 0.0) / L if L else None
            satirlar.append(_R({"kiris": r["no"], "adres": adres.get(r["no"], ""), "kat": r.get("kat"), "durum": durum, "L": L,
                                "oz": oz, "duvar": duvar, "ek": ek, "doseme_kN": d.get("doseme"), "qeM": qeM, "qeV": qeV,
                                "toplam": d.get("toplam_kN")}))
    return _T("eleman_yukleri", "Eleman Yük Ataması (Kiriş Başına)", "Yükler",
              [_S("kiris", "Kiriş", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("durum", "Durum", tur="metin"), _S("L", "L", "m", ondalik=2), _S("oz", "Öz ağırlık", "kN/m", ondalik=2),
               _S("duvar", "Duvar", "kN/m", ondalik=2), _S("ek", "Ek çizgisel", "kN/m", ondalik=2),
               _S("doseme_kN", "Döşemeden (toplam)", "kN", ondalik=2), _S("qeM", "q_eM (moment eşd.)", "kN/m", ondalik=2),
               _S("qeV", "q_eV = toplam/L", "kN/m", ondalik=2), _S("toplam", "Toplam", "kN", ondalik=2)],
              satirlar, "Kiriş başına yük durumu dökümü. Döşeme payı FE'de gerçek üçgen/trapez (parçalı doğrusal) yük olarak verilir; "
                        "q_eM yalnız el hesabı karşılaştırması içindir.", "TS 498:2021; TS 500 md. 11.4.3",
              toplam=_topla(satirlar, "toplam"))


def _t_kat_agirliklari(c):
    yuk_kat = None
    if c.veri and (c.veri.get("yukler") or {}).get("katlar") is not None:
        yuk_kat = c.veri["yukler"]["katlar"]
    elif c.Y:
        yuk_kat = c.Y.katlar
    dep = _deprem_verisi(c)
    dk = {k["kat"]: k for k in (dep or {}).get("katlar") or []}
    satirlar = []
    for k in yuk_kat or []:
        d = dk.get(k["kat"], {})
        satirlar.append(_R({"kat": k["kat"], "kot": k["kot"], "h": k["h"], "G": k["G"], "Q": k["Q"], "S": k.get("S"), "w": k.get("w"),
                            "w_i": d.get("w_i"), "m_i": d.get("m_i")}))
    return _T("kat_agirliklari", "Kat Ağırlıkları", "Yükler",
              [_S("kat", "Kat", ondalik=0), _S("kot", "Kot", "m", ondalik=2), _S("h", "h", "m", ondalik=2),
               _S("G", "G", "kN", ondalik=2), _S("Q", "Q", "kN", ondalik=2), _S("S", "S", "kN", ondalik=2), _S("w", "G + Q", "kN", ondalik=2),
               _S("w_i", "Deprem ağırlığı w_i = G + nQ (+0,3S)", "kN", ondalik=2), _S("m_i", "Kütle m_i = w_i/g", "t", ondalik=3)],
              satirlar, "Kat seviyesine toplanan yükler (kat k: o seviyedeki döşeme, kiriş, duvar ve altındaki kolonların öz ağırlığı). "
                        "w_i deprem kütlesi TBDY Tablo 4.3 hareketli yük katılım katsayısı n ile.", "TS 498:2021; TBDY 2018 md. 4.5.9",
              toplam=_topla(satirlar, "G", "Q", "S", "w", "w_i", "m_i"))


def _kombinasyon_kayitlari(c):
    if c.veri and c.veri.get("kombinasyonlar") is not None:
        return c.veri["kombinasyonlar"]
    B = c.B
    if not B:
        return []
    mevcut = {"G", "Q"}
    if B.kar:
        mevcut.add("S")
    if B.ruzgar:
        mevcut |= {"W+X", "W-X", "W+Y", "W-Y"}
    if B.deprem:
        mevcut |= {"EX+", "EX-", "EY+", "EY-", "EZ"}
    try:
        return c.yapi._kombinasyon_listesi(B, mevcut)
    except Exception:  # noqa: BLE001
        return []


def _t_kombinasyonlar(c):
    kayitlar = _kombinasyon_kayitlari(c)
    durumlar = []
    for k in kayitlar:
        for d in k.get("katsayilar") or {}:
            if d not in durumlar:
                durumlar.append(d)
    sira = ["G", "Q", "S", "W+X", "W-X", "W+Y", "W-Y", "EX+", "EX-", "EY+", "EY-", "EZ", "T", "H", "W", "EH"]
    durumlar.sort(key=lambda d: sira.index(d) if d in sira else len(sira))
    satirlar = []
    for i, k in enumerate(kayitlar):
        kat = k.get("katsayilar") or {}
        satirlar.append(_R({"sira": i + 1, "ad": k.get("ad"), "aile": k.get("aile", ""), "tur": k.get("tur", ""),
                            "uygulandi": bool(k.get("uygulandi")), **{"k_" + d: kat.get(d) for d in durumlar},
                            "kaynak": k.get("kaynak", ""), "neden": k.get("neden") or k.get("not") or ""}))
    kume = c.B.kombinasyon_kumesi if c.B else c.ham.get("kombinasyon_kumesi", "")
    return _T("kombinasyonlar", "Yük Birleşimleri", "Yükler",
              [_S("sira", "Sıra", ondalik=0), _S("ad", "Birleşim", tur="metin"), _S("aile", "Satır (şablon)", tur="metin"),
               _S("tur", "Tür", tur="metin"), _S("uygulandi", "Uygulandı", tur="bool")]
              + [_S("k_" + d, d, ondalik=3) for d in durumlar]
              + [_S("kaynak", "Kaynak", tur="metin"), _S("neden", "Not / neden", tur="metin")],
              satirlar, f"Küme: {kume} — {yv.KOMBINASYONLAR.get(kume, {}).get('ad', '')}. Ed(H) TBDY 4.4.2 doğrultu birleştirmesiyle "
                        "(±EX ± 0,3EY, ±0,3EX ± EY, dışmerkezlik ±) varyantlara açılır. Küme Genel Parametreler tablosunda değişir.",
              yv.KOMBINASYONLAR.get(kume, {}).get("kaynak", ""))


# ============================================================================
# DEPREM
# ============================================================================
def _deprem_verisi(c):
    if c.veri is not None:
        return c.veri.get("deprem")
    if not c.B or not c.B.deprem or c.yapi is None:
        return None
    if "_dep_onizleme" not in c.__dict__:
        try:
            c._dep_onizleme = c.yapi.deprem_onizleme(copy.deepcopy(c.ham))
        except Exception:  # noqa: BLE001
            c._dep_onizleme = None
    return c._dep_onizleme


def _t_deprem_parametreleri(c):
    ham, B = c.ham, c.B
    dham = ham.get("deprem") if isinstance(ham.get("deprem"), dict) else {}
    dB = (B.deprem if B else None) or {}
    dep = _deprem_verisi(c) or {}

    def g(a, vars_=None):
        return dB.get(a, dham.get(a, vars_))

    tas = list(getattr(yv, "TBDY_TASIYICI_ARAYUZ", ()))
    if g("tasiyici") and g("tasiyici") not in tas:
        tas.append(g("tasiyici"))
    girdi = [
        ("etkin", "Deprem yükü etkin (deprem.etkin)", bool(B.deprem) if B else bool(dham.get("etkin")), "", {"tur": "bool"}, "TBDY 2018"),
        ("SS", "S_S (kısa periyot harita spektral ivme)", g("SS"), "g", None, "AFAD TDTH, DD-2"),
        ("S1", "S_1 (1 s harita spektral ivme)", g("S1"), "g", None, "AFAD TDTH, DD-2"),
        ("SS_DD3", "S_S (DD-3, λ için)", g("SS_DD3"), "g", {"bos_olur": True}, "AFAD TDTH, DD-3"),
        ("S1_DD3", "S_1 (DD-3, λ için)", g("S1_DD3"), "g", {"bos_olur": True}, "AFAD TDTH, DD-3"),
        ("zemin_sinifi", "Yerel zemin sınıfı", g("zemin_sinifi", "ZC"), "", {"tur": "secim", "secenekler": ["ZA", "ZB", "ZC", "ZD", "ZE"]},
         "TBDY Tablo 16.1"),
        ("BKS", "Bina kullanım sınıfı BKS", g("BKS", 3), "", {"tur": "secim", "secenekler": [1, 2, 3]}, "TBDY Tablo 3.1"),
        ("I", "Bina önem katsayısı I", g("I"), "", None, "TBDY Tablo 3.1"),
        ("tasiyici", "Taşıyıcı sistem (Tablo 4.1)", g("tasiyici"), "", {"tur": "secim", "secenekler": tas}, "TBDY Tablo 4.1"),
        ("R", "Taşıyıcı sistem davranış katsayısı R", g("R"), "", None, "TBDY Tablo 4.1"),
        ("D", "Dayanım fazlalığı katsayısı D", g("D"), "", None, "TBDY Tablo 4.1"),
        ("n", "Hareketli yük kütle katılım katsayısı n", g("n"), "", None, "TBDY Tablo 4.3"),
        ("Ct", "C_t (ampirik periyot)", g("Ct"), "", None, "TBDY md. 4.7.3.4"),
        ("periyot", "Periyot yöntemi", g("periyot", "otomatik"), "", {"tur": "secim", "secenekler": ["otomatik", "ampirik", "rayleigh"]},
         "TBDY md. 4.7.3"),
        ("diyafram", "Kat diyaframı", g("diyafram", "rijit"), "", {"tur": "secim", "secenekler": ["rijit", "esnek"]}, "TBDY md. 4.5.6"),
        ("dismerkezlik", "Ek dışmerkezlik oranı", g("dismerkezlik", 0.05), "", None, "TBDY md. 4.5.10"),
        ("dolgu", "Dolgu duvar bağlantısı", g("dolgu", "bitisik"), "", {"tur": "secim", "secenekler": ["bitisik", "esnek"]}, "TBDY md. 4.9.1.3"),
    ]
    satirlar = []
    for a, ad, deger, birim, hucre, kaynak in girdi:
        satirlar.append(_R({"tur": "girdi", "parametre": ad, "deger": deger, "birim": birim, "kaynak": kaynak}, {"deger": ["deprem", a]},
                           **({"hucre": {"deger": hucre}} if hucre else {})))
    hesap = [("FS", "F_S (kısa periyot zemin katsayısı)", "", "TBDY Tablo 2.1"), ("F1", "F_1 (1 s zemin katsayısı)", "", "TBDY Tablo 2.2"),
             ("SDS", "S_DS = S_S·F_S", "g", "TBDY Denk. 2.2"), ("SD1", "S_D1 = S_1·F_1", "g", "TBDY Denk. 2.2"),
             ("TA", "T_A = 0,2·S_D1/S_DS", "s", "TBDY md. 2.3.4"), ("TB", "T_B = S_D1/S_DS", "s", "TBDY md. 2.3.4"),
             ("TL", "T_L", "s", "TBDY md. 2.3.4"), ("DTS", "Deprem tasarım sınıfı DTS", "", "TBDY Tablo 3.2"),
             ("BYS", "Bina yükseklik sınıfı BYS", "", "TBDY Tablo 3.3"), ("HN", "H_N (bina yüksekliği)", "m", ""),
             ("TpA", "T_pA = C_t·H_N^(3/4) (ampirik)", "s", "TBDY Denk. 4.27"), ("Tp_rayleigh", "T_p Rayleigh", "s", "TBDY Denk. 4.26"),
             ("Tp", "Kullanılan T_p", "s", "TBDY md. 4.7.3"), ("Sae_Tp", "S_ae(T_p)", "g", "TBDY Denk. 2.3"),
             ("Ra", "R_a(T_p)", "", "TBDY Denk. 4.1"), ("SaR", "S_aR(T_p) = S_ae·I/R_a", "g", "TBDY Denk. 4.8"),
             ("W_t", "Toplam deprem ağırlığı W_t", "kN", "TBDY md. 4.5.9"), ("m_t", "Toplam kütle m_t", "t", ""),
             ("VtE", "Taban kesme kuvveti V_tE = m_t·S_aR·g", "kN", "TBDY Denk. 4.19"), ("VtE_min", "V_tE alt sınırı 0,04·m_t·I·S_DS·g", "kN", "TBDY Denk. 4.19"),
             ("dFN", "Tepe ek kuvveti ΔF_NE", "kN", "TBDY Denk. 4.20"), ("lambda", "λ (DD-3/DD-2 oranı)", "", "TBDY md. 4.9.1.3"),
             ("sinir_oran", "Göreli öteleme sınırı (κ·0,008/0,016)", "", "TBDY Denk. 4.34"), ("theta_sinir", "θ_II sınırı", "", "TBDY Denk. 4.38")]
    for a, ad, birim, kaynak in hesap:
        if a in dep:
            satirlar.append(_R({"tur": "hesap" + (" (önizleme)" if c.veri is None else ""), "parametre": ad, "deger": dep.get(a),
                                "birim": birim, "kaynak": kaynak},
                               **({"hucre": {"deger": {"tur": "metin"}}} if isinstance(dep.get(a), str) else {})))
    return _T("deprem_parametreleri", "Deprem Parametreleri (TBDY 2018)", "Deprem",
              [_S("tur", "Tür", tur="metin"), _S("parametre", "Parametre", tur="metin"), _S("deger", "Değer", duzenlenebilir=True, ondalik=4),
               _S("birim", "Birim", tur="metin"), _S("kaynak", "Kaynak", tur="metin")],
              satirlar, "Girdi satırları düzenlenebilir (deprem kartı); hesap satırları çözümden ya da çözümsüz önizlemeden (ampirik T_p).",
              "TBDY 2018 Bölüm 2, 3, 4")


def _t_kat_kuvvetleri(c):
    dep = _deprem_verisi(c)
    satirlar = []
    for k in (dep or {}).get("katlar") or []:
        satirlar.append(_R({"kat": k["kat"], "H": k.get("H"), "w_i": k.get("w_i"), "m_i": k.get("m_i"),
                            "F_x": k.get("F_x"), "F_y": k.get("F_y"), "V_x": k.get("V_x"), "V_y": k.get("V_y"),
                            "e_x": k.get("e_x"), "e_y": k.get("e_y")}))
    return _T("kat_kuvvetleri", "Eşdeğer Deprem Kat Kuvvetleri", "Deprem",
              [_S("kat", "Kat", ondalik=0), _S("H", "H_i", "m", ondalik=2), _S("w_i", "w_i", "kN", ondalik=2), _S("m_i", "m_i", "t", ondalik=3),
               _S("F_x", "F_iE (X)", "kN", ondalik=2), _S("F_y", "F_iE (Y)", "kN", ondalik=2), _S("V_x", "V_i (X)", "kN", ondalik=2),
               _S("V_y", "V_i (Y)", "kN", ondalik=2), _S("e_x", "Ek dışmerkezlik (X depremi)", "m", ondalik=3),
               _S("e_y", "Ek dışmerkezlik (Y depremi)", "m", ondalik=3)],
              satirlar, "F_iE = (V_tE − ΔF_NE)·m_i·H_i / Σ(m_j·H_j); tepe katına ΔF_NE eklenir; V_i kat kesme kuvveti.",
              "TBDY 2018 Denk. 4.20–4.21", toplam=_topla(satirlar, "w_i", "m_i", "F_x", "F_y"))


def _t_burulma(c):
    if c.veri is None:
        return None
    dep = c.veri.get("deprem")
    satirlar = []
    for k in (dep or {}).get("katlar") or []:
        ex, ey = k.get("eta_bx"), k.get("eta_by")
        en = max(v for v in (ex, ey, 0.0) if v is not None)
        satirlar.append(_R({"kat": k["kat"], "eta_bx": ex, "eta_by": ey, "durum": "A1 düzensizliği (η_bi > 1,2)" if en > 1.2 else "düzenli",
                            "dc": en / 2.0 if en else None}))
    return _T("burulma", "Burulma Düzensizliği η_bi", "Deprem",
              [_S("kat", "Kat", ondalik=0), _S("eta_bx", "η_bi (X depremi)", ondalik=3), _S("eta_by", "η_bi (Y depremi)", ondalik=3),
               _S("durum", "Durum", tur="metin"), _S("dc", "η_bi / 2,0", ondalik=3, vurgu="dc")],
              satirlar, "η_bi = (Δ_i)max / (Δ_i)ort (±%5 dışmerkezlikle); > 1,2 A1 burulma düzensizliği, > 2,0 eşdeğer deprem yükü "
                        "yöntemi uygulanamaz.", "TBDY 2018 Tablo 3.6 (A1), md. 4.6.2")


def _t_oteleme(c):
    if c.veri is None:
        return None
    dep = c.veri.get("deprem") or {}
    satirlar = []
    for k in dep.get("katlar") or []:
        sinir = k.get("sinir", dep.get("sinir_oran"))
        ox, oy = k.get("oran_x"), k.get("oran_y")
        en = max(v for v in (ox, oy, 0.0) if v is not None)
        satirlar.append(_R({"kat": k["kat"], "h": k.get("h"), "d_x": (k.get("d_x") or 0.0) * 1000, "d_y": (k.get("d_y") or 0.0) * 1000,
                            "delta_x": (k.get("delta_etkin_x") or 0.0) * 1000, "delta_y": (k.get("delta_etkin_y") or 0.0) * 1000,
                            "oran_x": ox, "oran_y": oy, "sinir": sinir, "dc": en / sinir if sinir else None,
                            "uygun": bool(k.get("uygun", True))}))
    return _T("oteleme", "Göreli Kat Ötelemeleri", "Deprem",
              [_S("kat", "Kat", ondalik=0), _S("h", "h_i", "m", ondalik=2), _S("d_x", "d_i (X)", "mm", ondalik=2),
               _S("d_y", "d_i (Y)", "mm", ondalik=2), _S("delta_x", "δ_i etkin (X)", "mm", ondalik=2), _S("delta_y", "δ_i etkin (Y)", "mm", ondalik=2),
               _S("oran_x", "λ·δ/h (X)", ondalik=5), _S("oran_y", "λ·δ/h (Y)", ondalik=5), _S("sinir", "Sınır κ·0,008", ondalik=4),
               _S("dc", "Oran / sınır", ondalik=3, vurgu="dc"), _S("uygun", "Sağlanıyor", tur="bool")],
              satirlar, "δ_i = (R/I)·Δ_i (etkin göreli öteleme); λ·δ_i,max/h_i ≤ κ·0,008 (dolgu bitişik) ya da κ·0,016 (esnek).",
              "TBDY 2018 Denk. 4.33–4.34")


def _t_theta(c):
    if c.veri is None:
        return None
    dep = c.veri.get("deprem") or {}
    sinir = dep.get("theta_sinir")
    satirlar = []
    for k in dep.get("katlar") or []:
        tx, ty = k.get("theta_x"), k.get("theta_y")
        en = max(v for v in (tx, ty, 0.0) if v is not None)
        satirlar.append(_R({"kat": k["kat"], "theta_x": tx, "theta_y": ty, "sinir": sinir, "dc": en / sinir if sinir else None}))
    return _T("theta", "İkinci Mertebe Göstergesi θ_II", "Deprem",
              [_S("kat", "Kat", ondalik=0), _S("theta_x", "θ_II (X)", ondalik=4), _S("theta_y", "θ_II (Y)", ondalik=4),
               _S("sinir", "Sınır θ_II,max", ondalik=3), _S("dc", "θ / sınır", ondalik=3, vurgu="dc")],
              satirlar, "θ_II,i = (Δ_i)ort·Σw_j / (V_i·h_i); sınırı aşılırsa ikinci mertebe etkileri hesaba katılır.",
              "TBDY 2018 Denk. 4.37–4.38")


def _t_spektrum(c):
    dep = _deprem_verisi(c)
    if not dep or not dep.get("spektrum"):
        return None
    satirlar = []
    for p in dep["spektrum"]:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            satirlar.append(_R({"T": p[0], "Sae": p[1], "SaR": p[2] if len(p) > 2 else None}))
    return _T("spektrum", "Tasarım Spektrumu", "Deprem",
              [_S("T", "T", "s", ondalik=3), _S("Sae", "S_ae(T)", "g", ondalik=4), _S("SaR", "S_aR(T)", "g", ondalik=4)],
              satirlar, "Yatay elastik tasarım spektrumu ve azaltılmış spektrum (I/R_a).", "TBDY 2018 Denk. 2.3, 4.8")


# ============================================================================
# ANALİZ
# ============================================================================
def _eleman_bilgi(c):
    return {e["no"]: e for e in ((c.veri or {}).get("ag") or {}).get("elemanlar") or []}


def _durum_sirasi(c):
    v = c.veri or {}
    adlar = list((v.get("durumlar") or {}).keys())
    for ad in v.get("sonuclar") or {}:
        if ad not in adlar:
            adlar.append(ad)
    return adlar


def _kisa(c, ad):
    v = c.veri or {}
    return (v.get("durumlar") or {}).get(ad) or (v.get("sonuclar") or {}).get(ad)


def _t_yer_degistirmeler(c):
    if c.veri is None:
        return None
    adres = {d["no"]: d.get("adres", "") for d in (c.veri.get("ag") or {}).get("dugumler") or []}
    satirlar = []
    for ad in _durum_sirasi(c):
        k = _kisa(c, ad) or {}
        for d in k.get("dugumler") or []:
            satirlar.append(_R({"durum": ad, "dugum": d["no"], "adres": adres.get(d["no"], ""),
                                "uX": d["uX"] * 1000, "uY": d["uY"] * 1000, "uZ": d["uZ"] * 1000, "rX": d["rX"], "rY": d["rY"], "rZ": d["rZ"]}))
    return _T("dugum_yer_degistirmeleri", "Düğüm Yer Değiştirmeleri", "Analiz",
              [_S("durum", "Durum / birleşim", tur="metin"), _S("dugum", "Düğüm", ondalik=0), _S("adres", "Adres", tur="metin"),
               _S("uX", "u_X", "mm", ondalik=3), _S("uY", "u_Y", "mm", ondalik=3), _S("uZ", "u_Z", "mm", ondalik=3),
               _S("rX", "θ_X", "rad", ondalik=6), _S("rY", "θ_Y", "rad", ondalik=6), _S("rZ", "θ_Z", "rad", ondalik=6)],
              satirlar, "Her yük durumu (G, Q, S, W±, EX±, EY±, EZ) ve yanıtta tam verilen birleşimler için bina koordinatında.",
              "Sonlu eleman çözümü (cerceve3b, 6 SD/düğüm)")


def _t_tepkiler(c):
    if c.veri is None:
        return None
    adres = {d["no"]: d.get("adres", "") for d in (c.veri.get("ag") or {}).get("dugumler") or []}
    satirlar = []
    for ad in _durum_sirasi(c):
        k = _kisa(c, ad) or {}
        tep = k.get("tepkiler") or []
        for t in tep:
            satirlar.append(_R({"durum": ad, "dugum": t["dugum"], "adres": adres.get(t["dugum"], ""),
                                **{a: t.get(a) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}}))
        if tep:
            satirlar.append(_R({"durum": ad, "dugum": None, "adres": "Σ (toplam)",
                                **{a: sum(t.get(a) or 0.0 for t in tep) for a in ("FX", "FY", "FZ", "MX", "MY", "MZ")}}, ozet=True))
    return _T("mesnet_tepkileri", "Mesnet Tepkileri", "Analiz",
              [_S("durum", "Durum / birleşim", tur="metin"), _S("dugum", "Düğüm", ondalik=0), _S("adres", "Adres", tur="metin"),
               _S("FX", "F_X", "kN", ondalik=2), _S("FY", "F_Y", "kN", ondalik=2), _S("FZ", "F_Z", "kN", ondalik=2),
               _S("MX", "M_X", "kN·m", ondalik=2), _S("MY", "M_Y", "kN·m", ondalik=2), _S("MZ", "M_Z", "kN·m", ondalik=2)],
              satirlar, "Bina koordinatında mesnet tepkileri; her durumun Σ satırı toplam yükü dengeler (korunum: ΣF_Z = durumun düşey yükü).",
              "Sonlu eleman çözümü")


def _t_zarf(c):
    if c.veri is None:
        return None
    bilgi = _eleman_bilgi(c)
    satirlar = []
    for z in (c.veri.get("zarf") or {}).get("elemanlar") or []:
        e = bilgi.get(z["no"], {})
        bel = z.get("belirleyen") or {}
        satirlar.append(_R({"no": z["no"], "tur": e.get("tur", ""), "adres": e.get("adres", ""), "kat": e.get("kat"),
                            **{a: z.get(a) for a in ("N_max", "N_min", "V_max", "V_min", "M_max", "M_min", "Vz_max", "Vz_min",
                                                     "My_max", "My_min", "T_max", "T_min")},
                            "bel_M_max": bel.get("M_max", ""), "bel_M_min": bel.get("M_min", ""), "bel_N_min": bel.get("N_min", "")}))
    sut = [_S("no", "FE eleman", ondalik=0), _S("tur", "Tür", tur="metin"), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0)]
    for a, b, birim in (("N", "N", "kN"), ("V", "V_y", "kN"), ("M", "M_z", "kN·m"), ("Vz", "V_z", "kN"), ("My", "M_y", "kN·m"), ("T", "T", "kN·m")):
        sut += [_S(a + "_max", b + " maks", birim, ondalik=2), _S(a + "_min", b + " min", birim, ondalik=2)]
    sut += [_S("bel_M_max", "Belirleyen (M maks)", tur="metin"), _S("bel_M_min", "Belirleyen (M min)", tur="metin"),
            _S("bel_N_min", "Belirleyen (N min)", tur="metin")]
    return _T("eleman_kuvvetleri_zarf", "Eleman İç Kuvvet Zarfı", "Analiz", sut, satirlar,
              f"Uygulanan {(c.veri.get('zarf') or {}).get('kombinasyon_sayisi', '')} dayanım/deprem birleşiminin zarfı (her istasyonda "
              "maks/min). Yerel eksen: x′ eleman ekseni, y′ kirişte yukarı; M = M_z güçlü eksen. N çekme +.", "Sonlu eleman çözümü")


def _t_kombinasyon_ozeti(c):
    if c.veri is None:
        return None
    satirlar = []
    for ad, o in (c.veri.get("kombinasyon_ozet") or {}).items():
        enb, u = o.get("enb") or {}, o.get("u_enb") or {}
        satirlar.append(_R({"ad": ad, **{a: enb.get(a) for a in ("N", "V", "M", "Vz", "My", "T")},
                            "uX": (u.get("X") or 0.0) * 1000, "uY": (u.get("Y") or 0.0) * 1000, "uZ": (u.get("Z") or 0.0) * 1000,
                            "FZ": o.get("FZ_tepki")}))
    return _T("kombinasyon_ozeti", "Birleşim Özeti (En Büyük Değerler)", "Analiz",
              [_S("ad", "Birleşim", tur="metin"), _S("N", "|N| maks", "kN", ondalik=2), _S("V", "|V_y| maks", "kN", ondalik=2),
               _S("M", "|M_z| maks", "kN·m", ondalik=2), _S("Vz", "|V_z| maks", "kN", ondalik=2), _S("My", "|M_y| maks", "kN·m", ondalik=2),
               _S("T", "|T| maks", "kN·m", ondalik=3), _S("uX", "|u_X| maks", "mm", ondalik=3), _S("uY", "|u_Y| maks", "mm", ondalik=3),
               _S("uZ", "|u_Z| maks", "mm", ondalik=3), _S("FZ", "ΣF_Z tepki", "kN", ondalik=2)],
              satirlar, "Her uygulanan birleşimin bütün elemanlardaki en büyük mutlak iç kuvvetleri ve yer değiştirmeleri.", "")


def _t_kolon_yukleri(c):
    if c.veri is None:
        return None
    satirlar = []
    for k in (c.veri.get("akis") or {}).get("kolonlar") or []:
        satirlar.append(_R({"no": k["no"], "adres": k.get("adres", ""), "kat": k.get("kat"), "N_G": k.get("N_G"), "N_Q": k.get("N_Q"),
                            "N_kum_G": k.get("N_kum_G"), "N_kum_Q": k.get("N_kum_Q"), "A_trib": k.get("A_trib"),
                            "N_trib_G": k.get("N_trib_G"), "N_trib_Q": k.get("N_trib_Q"), "fark": k.get("fark_yuzde")}))
    return _T("kolon_yukleri", "Kolon Eksenel Yükleri (Yük Akışı)", "Analiz",
              [_S("no", "Kolon", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("N_G", "N_G (kat payı)", "kN", ondalik=2), _S("N_Q", "N_Q (kat payı)", "kN", ondalik=2),
               _S("N_kum_G", "N_G kümülatif (FE)", "kN", ondalik=2), _S("N_kum_Q", "N_Q kümülatif (FE)", "kN", ondalik=2),
               _S("A_trib", "Yük alanı", "m²", ondalik=2), _S("N_trib_G", "N_G yük alanı", "kN", ondalik=2),
               _S("N_trib_Q", "N_Q yük alanı", "kN", ondalik=2), _S("fark", "FE − yük alanı", "%", ondalik=1)],
              satirlar, "FE eksenel kuvvetleri (süreklilik ve rijitlik dağılımıyla) yük alanı (tributary) el hesabıyla karşılaştırılır.",
              "TS 498:2021; FE çözümü")


def _t_korunum(c):
    if c.veri is None:
        return None
    kor = (c.veri.get("akis") or {}).get("korunum") or {}
    satirlar = []
    for d, p in kor.items():
        satirlar.append(_R({"durum": d, **{a: p.get(a) for a in ("dosemeler", "duvarlar", "kiris_oz", "kolon_oz", "ek", "toplam",
                                                                  "kolon_taban", "tepki", "temel")}}))
    return _T("korunum", "Yük Korunumu", "Analiz",
              [_S("durum", "Durum", tur="metin"), _S("dosemeler", "Döşemeler", "kN", ondalik=2), _S("duvarlar", "Duvarlar", "kN", ondalik=2),
               _S("kiris_oz", "Kiriş öz", "kN", ondalik=2), _S("kolon_oz", "Kolon öz", "kN", ondalik=2), _S("ek", "Ek yükler", "kN", ondalik=2),
               _S("toplam", "Toplam yük", "kN", ondalik=2), _S("kolon_taban", "Kolon tabanları ΣN", "kN", ondalik=2),
               _S("tepki", "Mesnet tepkileri ΣF_Z", "kN", ondalik=2), _S("temel", "Temeller", "kN", ondalik=2)],
              satirlar, "Döşeme → kiriş → kolon → temel → zemin: her aşamada toplam aynı kalmalıdır (denge sağlaması).", "")


# ============================================================================
# TASARIM
# ============================================================================
def _tasarim_satirlari(c, tur, sistem):
    sonuc = []
    for e in ((c.veri or {}).get("tasarim") or {}).get("elemanlar") or []:
        if e.get("tur") == tur and e.get("sistem") == sistem:
            sonuc.append(e)
    return sonuc


def _t_tasarim_kiris(c):
    if c.veri is None or not c.veri.get("tasarim"):
        return None
    satirlar = []
    for e in _tasarim_satirlari(c, "kiris", "betonarme"):
        o, b = e.get("ozet") or {}, e.get("belirleyen") or {}
        satirlar.append(_R({"no": e["no"], "adres": e.get("adres", ""), "kat": e.get("kat"), "kesit": e.get("kesit", ""),
                            "dc": e.get("dc"), "durum": e.get("durum", ""), "kontrol": b.get("kontrol", ""), "kombinasyon": b.get("kombinasyon", ""),
                            "Md_mesnet": o.get("Md_mesnet"), "Md_aciklik": o.get("Md_aciklik"), "Vd": o.get("Vd"),
                            "As_ust": o.get("As_ust_cm2"), "As_alt": o.get("As_alt_cm2"), "oneri_ust": o.get("oneri_ust", ""),
                            "oneri_alt": o.get("oneri_alt", ""), "etriye": o.get("etriye", "")}))
    if not satirlar:
        return None
    return _T("tasarim_betonarme_kiris", "Betonarme Kiriş Tahkikleri", "Tasarım",
              [_S("no", "Kiriş", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0), _S("kesit", "Kesit", tur="metin"),
               _S("dc", "D/C", ondalik=3, vurgu="dc"), _S("durum", "Durum", tur="metin"), _S("kontrol", "Belirleyen kontrol", tur="metin"),
               _S("kombinasyon", "Belirleyen birleşim", tur="metin"), _S("Md_mesnet", "M_d mesnet", "kN·m", ondalik=2),
               _S("Md_aciklik", "M_d açıklık", "kN·m", ondalik=2), _S("Vd", "V_d", "kN", ondalik=2),
               _S("As_ust", "A_s üst", "cm²", ondalik=2), _S("As_alt", "A_s alt", "cm²", ondalik=2),
               _S("oneri_ust", "Üst donatı önerisi", tur="metin"), _S("oneri_alt", "Alt donatı önerisi", tur="metin"),
               _S("etriye", "Etriye", tur="metin")],
              satirlar, "Eğilme (mesnet üst / açıklık alt), kesme; D/C > 1 kırmızı.", (c.veri["tasarim"].get("yontem") or {}).get("betonarme", ""))


def _t_tasarim_kolon(c):
    if c.veri is None or not c.veri.get("tasarim"):
        return None
    satirlar = []
    for e in _tasarim_satirlari(c, "kolon", "betonarme"):
        o, b = e.get("ozet") or {}, e.get("belirleyen") or {}
        satirlar.append(_R({"no": e["no"], "adres": e.get("adres", ""), "kat": e.get("kat"), "kesit": e.get("kesit", ""),
                            "dc": e.get("dc"), "durum": e.get("durum", ""), "kontrol": b.get("kontrol", ""), "kombinasyon": b.get("kombinasyon", ""),
                            "N_max": o.get("N_max_kN"), "Ndm": o.get("Ndm_kN"), "N_sinir": o.get("N_sinir_TBDY_kN"),
                            "rho": (o.get("rho") or 0.0) * 100 if o.get("rho") is not None else None, "As": o.get("As_toplam_cm2")}))
    if not satirlar:
        return None
    return _T("tasarim_betonarme_kolon", "Betonarme Kolon Tahkikleri", "Tasarım",
              [_S("no", "Kolon", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0), _S("kesit", "Kesit", tur="metin"),
               _S("dc", "D/C", ondalik=3, vurgu="dc"), _S("durum", "Durum", tur="metin"), _S("kontrol", "Belirleyen kontrol", tur="metin"),
               _S("kombinasyon", "Belirleyen birleşim", tur="metin"), _S("N_max", "N_d maks", "kN", ondalik=2),
               _S("Ndm", "N_dm", "kN", ondalik=2), _S("N_sinir", "0,40·f_ck·A_c", "kN", ondalik=2),
               _S("rho", "ρ", "%", ondalik=2), _S("As", "A_s toplam", "cm²", ondalik=2)],
              satirlar, "N–M etkileşimi (iki eksenli), N_dm ≤ 0,40 f_ck A_c (TBDY 7.3.1.2); D/C > 1 kırmızı.",
              (c.veri["tasarim"].get("yontem") or {}).get("betonarme", ""))


def _t_tasarim_celik(c):
    if c.veri is None or not c.veri.get("tasarim"):
        return None
    satirlar = []
    for e in ((c.veri.get("tasarim") or {}).get("elemanlar") or []):
        if e.get("sistem") != "celik":
            continue
        o, b = e.get("ozet") or {}, e.get("belirleyen") or {}
        satirlar.append(_R({"tur": e.get("tur", ""), "no": e["no"], "adres": e.get("adres", ""), "kat": e.get("kat"), "kesit": e.get("kesit", ""),
                            "dc": e.get("dc"), "durum": e.get("durum", ""), "sinif": o.get("sinif", ""), "kontrol": b.get("kontrol", ""),
                            "kombinasyon": b.get("kombinasyon", ""), "Mc": o.get("Mc_kNm"), "Pc": o.get("Pc_kN"), "Vc": o.get("Vc_kN"),
                            "Lb": o.get("Lb_m")}))
    if not satirlar:
        return None
    return _T("tasarim_celik", "Çelik Eleman Tahkikleri", "Tasarım",
              [_S("tur", "Tür", tur="metin"), _S("no", "No", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("kesit", "Profil", tur="metin"), _S("dc", "D/C", ondalik=3, vurgu="dc"), _S("durum", "Durum", tur="metin"),
               _S("sinif", "Kesit sınıfı", tur="metin"), _S("kontrol", "Belirleyen kontrol", tur="metin"),
               _S("kombinasyon", "Belirleyen birleşim", tur="metin"), _S("Mc", "M_c (tasarım eğilme)", "kN·m", ondalik=2),
               _S("Pc", "P_c (tasarım basınç)", "kN", ondalik=2), _S("Vc", "V_c (tasarım kesme)", "kN", ondalik=2),
               _S("Lb", "L_b", "m", ondalik=2)],
              satirlar, "Basınç, eğilme (yanal burulmalı burkulma), kesme ve bileşik etki (Denk. 11.1a/b).",
              (c.veri["tasarim"].get("yontem") or {}).get("celik", ""))


# ============================================================================
# TEMEL
# ============================================================================
def _t_temel_parametreleri(c):
    ham, B = c.ham, c.B
    t = ham.get("temeller") if isinstance(ham.get("temeller"), dict) else {}
    tB = B.temeller if B else {}
    var = tB.get("varsayilan") or t.get("varsayilan") or {}
    zem = tB.get("zemin") or t.get("zemin") or {}
    tip = str(t.get("tip") or tB.get("tip") or "tekil")
    satirlar = [
        _R({"parametre": "Temel tipi", "deger": tip, "birim": "", "aciklama": "tekil | surekli (mütemadi) | radye"},
           {"deger": ["temeller", "tip"]}, hucre={"deger": {"tur": "secim", "secenekler": ["tekil", "surekli", "radye"]}}),
        _R({"parametre": "Mesnet modeli (tekil)", "deger": tB.get("mesnet", t.get("mesnet", "ankastre")), "birim": "",
            "aciklama": "ankastre | mafsal | elastik (Winkler yayları)"},
           {"deger": ["temeller", "mesnet"]}, hucre={"deger": {"tur": "secim", "secenekler": ["ankastre", "mafsal", "elastik"]}}),
        _R({"parametre": "Zemin emniyet gerilmesi q_em", "deger": zem.get("q_em", 200.0), "birim": "kN/m²", "aciklama": "TS 500 servis kontrolü"},
           {"deger": ["temeller", "zemin", "q_em"]}),
        _R({"parametre": "Yatak katsayısı k0", "deger": zem.get("k0", 20000.0), "birim": "kN/m³", "aciklama": "Winkler zemin modeli"},
           {"deger": ["temeller", "zemin", "k0"]}),
        _R({"parametre": "Varsayılan tekil temel B", "deger": var.get("B", 1.5), "birim": "m", "aciklama": ""},
           {"deger": ["temeller", "varsayilan", "B"]}),
        _R({"parametre": "Varsayılan tekil temel L", "deger": var.get("L", 1.5), "birim": "m", "aciklama": ""},
           {"deger": ["temeller", "varsayilan", "L"]}),
        _R({"parametre": "Temel yüksekliği h", "deger": var.get("h", 0.6), "birim": "m", "aciklama": ""},
           {"deger": ["temeller", "varsayilan", "h"]}),
    ]
    for anahtar, alanlar in (("surekli", (("B", "Tabla genişliği B", "m"), ("h_tabla", "Tabla yüksekliği", "m"), ("b_govde", "Gövde genişliği", "m"),
                                          ("h_govde", "Gövde yüksekliği", "m"), ("tasma", "Uç taşma", "m"), ("ag", "Eleman bölme aralığı", "m"))),
                             ("radye", (("h", "Radye kalınlığı", "m"), ("tasma", "Aks dışına taşma", "m"), ("ag", "Izgara aralığı", "m")))):
        if tip == anahtar or isinstance(t.get(anahtar), dict):
            ks = t.get(anahtar) if isinstance(t.get(anahtar), dict) else {}
            for a, ad, birim in alanlar:
                satirlar.append(_R({"parametre": f"{'Mütemadi' if anahtar == 'surekli' else 'Radye'}: {ad}", "deger": ks.get(a), "birim": birim,
                                    "aciklama": "§13"}, {"deger": ["temeller", anahtar, a]}, hucre={"deger": {"bos_olur": True}}))
    return _T("temel_parametreleri", "Temel ve Zemin Parametreleri", "Temel",
              [_S("parametre", "Parametre", tur="metin"), _S("deger", "Değer", duzenlenebilir=True, ondalik=3),
               _S("birim", "Birim", tur="metin"), _S("aciklama", "Açıklama", tur="metin")],
              satirlar, "Temel tipi, zemin ve varsayılan boyutlar.", "TS 500 md. 15; TBDY 2018 Bölüm 16")


def _t_temel_basinclari(c):
    if c.veri is None:
        return None
    k0 = ((c.B.temeller["zemin"]["k0"]) if c.B else None)
    satirlar = []
    for t in (c.veri.get("akis") or {}).get("temeller") or []:
        aks = t.get("aks") or ["", ""]
        BL = (t.get("B") or 0.0) * (t.get("L") or 0.0)
        s_ort = (t.get("N_servis") or 0.0) / BL if BL else None
        satirlar.append(_R({"kolon_no": t.get("kolon_no"), "aks": f"{aks[0]}{aks[1]}", "B": t.get("B"), "L": t.get("L"),
                            "N_G": t.get("N_G"), "N_Q": t.get("N_Q"), "N_temel": t.get("N_temel"), "N_servis": t.get("N_servis"),
                            "MX": t.get("MX"), "MY": t.get("MY"), "sigma_max": t.get("sigma_max"), "sigma_min": t.get("sigma_min"),
                            "e_X": t.get("e_X"), "e_Y": t.get("e_Y"), "q_em": t.get("q_em"), "dc": t.get("DC"),
                            "cekirdek": bool(t.get("cekirdek_icinde")),
                            "oturma": (s_ort / k0 * 1000.0) if (s_ort is not None and k0) else None}))
    return _T("temel_basinclari", "Temel Taban Basınçları", "Temel",
              [_S("kolon_no", "Kolon", ondalik=0), _S("aks", "Aks", tur="metin"), _S("B", "B", "m", ondalik=2), _S("L", "L", "m", ondalik=2),
               _S("N_G", "N_G", "kN", ondalik=2), _S("N_Q", "N_Q", "kN", ondalik=2), _S("N_temel", "Temel öz ağırlığı", "kN", ondalik=2),
               _S("N_servis", "N servis", "kN", ondalik=2), _S("MX", "M_X", "kN·m", ondalik=2), _S("MY", "M_Y", "kN·m", ondalik=2),
               _S("sigma_max", "σ_maks", "kN/m²", ondalik=2), _S("sigma_min", "σ_min", "kN/m²", ondalik=2),
               _S("e_X", "e_X", "m", ondalik=3), _S("e_Y", "e_Y", "m", ondalik=3), _S("q_em", "q_em", "kN/m²", ondalik=1),
               _S("dc", "σ_maks / q_em", ondalik=3, vurgu="dc"), _S("cekirdek", "e ≤ B/6 (çekirdek)", tur="bool"),
               _S("oturma", "Oturma ≈ σ_ort/k0 (yaklaşık)", "mm", ondalik=2)],
              satirlar, "Servis yükü (G + Q + temel öz ağırlığı) ile σ = N/(BL) ± 6M_X/(BL²) ± 6M_Y/(LB²). Oturma Winkler k0 ile "
                        "yaklaşık (elastik zemin oturma hesabı değildir).", "TS 500 md. 15; Winkler modeli",
              toplam=_topla(satirlar, "N_servis"))


def _t_temel_dugumleri(c):
    tv = (c.veri or {}).get("temel") if c.veri else None
    if not isinstance(tv, dict) or not tv.get("dugumler"):
        return None
    satirlar = [_R({"no": d.get("no"), "X": d.get("X"), "Y": d.get("Y"), "w_mm": d.get("w_mm"), "p": d.get("p_kNm2"),
                    "dc": (d.get("p_kNm2") / tv["q_em"]) if (tv.get("q_em") and d.get("p_kNm2") is not None) else None})
                for d in tv["dugumler"]]
    return _T("temel_dugumleri", "Temel Düğümleri: Taban Basıncı ve Oturma", "Temel",
              [_S("no", "Düğüm", ondalik=0), _S("X", "X", "m", ondalik=2), _S("Y", "Y", "m", ondalik=2), _S("w_mm", "Oturma w", "mm", ondalik=2),
               _S("p", "Taban basıncı p", "kN/m²", ondalik=2), _S("dc", "p / q_em", ondalik=3, vurgu="dc")],
              satirlar, f"Temel tipi: {tv.get('tip', '')}; p_maks = {_n(tv.get('p_maks'))} kN/m², en büyük oturma {_n(tv.get('oturma_maks_mm'))} mm.",
              "Winkler zemin modeli; TS 500")


# ============================================================================
# METRAJ
# ============================================================================
def _sinif(c, kesit_ad):
    """Kesit malzemesinin kütüphane sınıfı (C30/37, S275 …)."""
    B = c.B
    mad = _malzeme_adi(c, kesit_ad)
    if B and mad in B.malzemeler:
        return B.malzemeler[mad]["kutuphane"], B.malzemeler[mad]["tur"]
    return mad, ""


def _profil_cevresi(p, ks):
    """Boya yüzeyi için çevre (m/m): I/H profil U = 2h + 4b − 2t_w − (8 − 2π)r (mm); yoksa kutu yaklaşımı 2(b + h)."""
    if p and all(a in p for a in ("h", "b", "tw")):
        r = p.get("r") or 0.0
        return (2 * p["h"] + 4 * p["b"] - 2 * p["tw"] - (8 - 2 * math.pi) * r) / 1000.0
    if ks.get("b") and ks.get("h"):
        return 2 * (ks["b"] + ks["h"])
    return None


def _etriye_ayristir(metin):
    """'Φ8/15' → (8.0, 0.15); okunamazsa None."""
    if not isinstance(metin, str):
        return None
    m = metin.replace("ø", "Φ").replace("φ", "Φ").replace("Ø", "Φ").replace(" ", "")
    if "Φ" not in m or "/" not in m:
        return None
    try:
        cap, ara = m.split("Φ", 1)[1].split("/", 1)
        ara = "".join(ch for ch in ara if ch.isdigit() or ch in ".,").replace(",", ".")
        return float(cap), float(ara) / 100.0
    except (ValueError, IndexError):
        return None


def _etriye_kg(cap_mm, aralik, a, b, L, pas=0.03):
    """Kapalı etriye: n = ⌈L/s⌉ + 1, boy = 2(a − 2c) + 2(b − 2c) + 2·10Φ (kanca); kg = n·boy·πΦ²/4·7850."""
    if not cap_mm or not aralik or L <= 0:
        return 0.0
    d = cap_mm / 1000.0
    boy = 2 * max(a - 2 * pas, 0.05) + 2 * max(b - 2 * pas, 0.05) + 20 * d
    n = math.ceil(L / aralik) + 1
    return n * boy * math.pi * d * d / 4.0 * CELIK_YOGUNLUK


def _metraj_hesap(c):
    """Eleman başına metraj kayıtları: (betonarme listesi, çelik listesi, diğer: duvar/panel)."""
    B, ham = c.B, c.ham
    beton, celik, diger = [], [], {"duvar": {}, "panel": 0.0, "doseme_alan": 0.0}
    if B is None:
        return beton, celik, diger

    def kolon_var(ix, iy, kat):
        return B.kolon_key.get((ix, iy, kat)) or B.kolon_key.get((ix, iy, kat + 1))

    # döşeme kalınlıkları: kolon üstü ve kiriş üstü
    t_kiris = {}
    for d in B.dosemeler:
        for key in d["kenarlar"].values():
            kp = B.kiris_parca.get(key)
            if kp:
                t_kiris[kp[0]["no"]] = max(t_kiris.get(kp[0]["no"], 0.0), d["h"])

    def t_kolon(col):
        t = 0.0
        for d in B.dosemeler:
            if d["kat"] == col["kat"] and d["ix0"] <= col["ix"] <= d["ix1"] and d["iy0"] <= col["iy"] <= d["iy1"]:
                t = max(t, d["h"])
        return t

    for col in B.kolonlar:
        ks = B.kesitler[col["kesit"]]
        sinif, mtur = _sinif(c, col["kesit"])
        if ks["tip"] == "profil":
            celik.append({"tur": "kolon", "no": col["no"], "adres": col["adres"], "kat": col["kat"], "profil": ks["profil"],
                          "sinif": sinif, "L": col["L"], "ks": ks})
            continue
        t = t_kolon(col)
        H = max(col["L"] - t, 0.0)
        V = col["bX"] * col["bY"] * H
        kalip = 2 * (col["bX"] + col["bY"]) * H
        tas = c.tasarim.get(("kolon", col["no"]))
        if tas and (tas.get("ozet") or {}).get("As_toplam_cm2") is not None:
            As = tas["ozet"]["As_toplam_cm2"] * 1e-4
            et = _etriye_ayristir((tas.get("ozet") or {}).get("etriye")) or KOLON_ETRIYE
            donati = As * col["L"] * CELIK_YOGUNLUK + _etriye_kg(et[0], et[1], col["bX"], col["bY"], col["L"], ks.get("pas") or 0.03)
            kaynak = f"tasarım A_s = {_n(tas['ozet']['As_toplam_cm2'])} cm² + etriye Φ{_n(et[0])}/{_n(et[1] * 100)}" + \
                     ("" if (tas.get("ozet") or {}).get("etriye") else " (varsayım)")
        else:
            oran = _donati_orani(c, "kolon")
            donati, kaynak = V * oran, f"yaklaşık {_n(oran)} kg/m³"
        beton.append({"tur": "kolon", "no": col["no"], "adres": col["adres"], "kat": col["kat"], "sinif": sinif,
                      "olcu": f"{_n(col['bX'] * 100)}×{_n(col['bY'] * 100)} cm", "uzunluk": H, "alan": None, "beton": V, "kalip": kalip,
                      "donati": donati, "donati_kaynak": kaynak, "t": t})
    for k in B.kirisler:
        ks = B.kesitler[k["kesit"]]
        sinif, mtur = _sinif(c, k["kesit"])
        # net boy: kolon yüzleri arası (aks boyu − uçlardaki/ara kolonların yarı genişlikleri)
        Lnet = 0.0
        for p in k["parcalar"]:
            i = p["i"]
            uclar = [(i, k["sabit"]), (i + 1, k["sabit"])] if k["yon"] == "x" else [(k["sabit"], i), (k["sabit"], i + 1)]
            kes = 0.0
            for ix, iy in uclar:
                col = kolon_var(ix, iy, k["kat"])
                if col:
                    kes += (col["bX"] if k["yon"] == "x" else col["bY"]) / 2.0
            Lnet += max(p["L"] - kes, 0.0)
        if ks["tip"] == "profil":
            celik.append({"tur": "kiris", "no": k["no"], "adres": k["adres"], "kat": k["kat"], "profil": ks["profil"], "sinif": sinif,
                          "L": k["L"], "ks": ks})
        else:
            t = t_kiris.get(k["no"], 0.0)
            hn = max(k["h"] - t, 0.0)
            V = k["b"] * hn * Lnet
            kalip = (k["b"] + 2 * hn) * Lnet
            tas = c.tasarim.get(("kiris", k["no"]))
            oz = (tas or {}).get("ozet") or {}
            if tas and oz.get("As_ust_cm2") is not None and oz.get("As_alt_cm2") is not None:
                As = (oz["As_ust_cm2"] + oz["As_alt_cm2"]) * 1e-4
                et = _etriye_ayristir(oz.get("etriye"))
                donati = As * k["L"] * CELIK_YOGUNLUK + (_etriye_kg(et[0], et[1], k["b"], k["h"], Lnet, ks.get("pas") or 0.03) if et else 0.0)
                kaynak = f"tasarım A_s üst + alt = {_n(oz['As_ust_cm2'] + oz['As_alt_cm2'])} cm²" + (f" + etriye {oz.get('etriye')}" if et else "")
            else:
                oran = _donati_orani(c, "kiris")
                donati, kaynak = V * oran, f"yaklaşık {_n(oran)} kg/m³"
            beton.append({"tur": "kiris", "no": k["no"], "adres": k["adres"], "kat": k["kat"], "sinif": sinif,
                          "olcu": f"{_n(k['b'] * 100)}×{_n(k['h'] * 100)} cm (t = {_n(t * 100)} cm)", "uzunluk": Lnet, "alan": None,
                          "beton": V, "kalip": kalip, "donati": donati, "donati_kaynak": kaynak, "t": t})
        if k["duvar"]:
            dv = B.duvarlar[k["duvar"]]
            anahtar = dv.get("kutuphane") or k["duvar"]
            diger["duvar"][anahtar] = diger["duvar"].get(anahtar, 0.0) + k["h_duvar"] * Lnet
    # döşeme betonu: kesitlerde döşeme malzemesi yok → betonarme sistemde kolon/kiriş betonu; çelik sistemde ilk beton malzemesi
    beton_sinif = None
    for ad, m in B.malzemeler.items():
        if m["tur"] == "beton":
            beton_sinif = m["kutuphane"]
            break
    for d in B.dosemeler:
        b_sol = b_sag = b_alt = b_ust = 0.0
        for kenar, key in d["kenarlar"].items():
            kp = B.kiris_parca.get(key)
            if kp:
                b = kp[0]["b"] if B.kesitler[kp[0]["kesit"]]["tip"] == "dikdortgen" else 0.0
                if kenar == "sol":
                    b_sol = b
                elif kenar == "sag":
                    b_sag = b
                elif kenar == "alt":
                    b_alt = b
                else:
                    b_ust = b
        alan = d["dx"] * d["dy"]
        diger["doseme_alan"] += alan
        kalip = max(d["dx"] - (b_sol + b_sag) / 2, 0.0) * max(d["dy"] - (b_alt + b_ust) / 2, 0.0)
        V = alan * d["h"]
        oran = _donati_orani(c, "doseme")
        beton.append({"tur": "doseme", "no": d["no"], "adres": d["adres"], "kat": d["kat"], "sinif": beton_sinif or "",
                      "olcu": f"{_n(d['dx'])}×{_n(d['dy'])} m, t = {_n(d['h'] * 100)} cm", "uzunluk": None, "alan": alan, "beton": V,
                      "kalip": kalip, "donati": V * oran, "donati_kaynak": f"yaklaşık {_n(oran)} kg/m³"})
    # tekil temeller
    if str(B.temeller.get("tip", "tekil")) == "tekil":
        for t in _temel_listesi(c):
            h = t["h"]
            V = t["B"] * t["L"] * h
            oran = _donati_orani(c, "temel")
            beton.append({"tur": "temel", "no": t["kolon_no"], "adres": f"T-{t['aks'][0]}{t['aks'][1]}", "kat": 0, "sinif": beton_sinif or "",
                          "olcu": f"{_n(t['B'])}×{_n(t['L'])}×{_n(h)} m", "uzunluk": None, "alan": t["B"] * t["L"], "beton": V,
                          "kalip": 2 * (t["B"] + t["L"]) * h, "donati": V * oran, "donati_kaynak": f"yaklaşık {_n(oran)} kg/m³"})
    # serbest çubuklar ve paneller (surum 3)
    for cb in _cubuk_kayitlari(c):
        if cb["liste"] != "cubuklar" or not cb["L"]:
            continue
        kayit = (ham.get("kesitler") or {}).get(cb["kesit"]) or {}
        ks = B.kesitler.get(cb["kesit"])
        if ks is None:
            continue
        sinif, _ = _sinif(c, cb["kesit"])
        if ks["tip"] == "profil":
            celik.append({"tur": cb["tur"], "no": cb["no"], "adres": cb["adres"], "kat": cb["kat"], "profil": ks["profil"], "sinif": sinif,
                          "L": cb["L"], "ks": ks})
        elif kayit:
            V = ks["A"] * cb["L"]
            oran = _donati_orani(c, "diger")
            beton.append({"tur": cb["tur"], "no": cb["no"], "adres": cb["adres"], "kat": cb["kat"], "sinif": sinif,
                          "olcu": f"{_n(ks['b'] * 100)}×{_n(ks['h'] * 100)} cm", "uzunluk": cb["L"], "alan": None, "beton": V,
                          "kalip": 2 * (ks["b"] + ks["h"]) * cb["L"], "donati": V * oran, "donati_kaynak": f"yaklaşık {_n(oran)} kg/m³"})
    for i, p in enumerate(ham.get("paneller") or []):
        if not isinstance(p, dict):
            continue
        alan, _ = _poligon_alani([c.ref_koordinat(r) for r in (p.get("kose") or [])])
        if alan is None:
            continue
        tk = p.get("kalinlik") or 0.0
        if tk > 0:
            V = alan * tk
            oran = _donati_orani(c, "doseme")
            beton.append({"tur": "panel", "no": p.get("no", i + 1), "adres": f"P{p.get('no', i + 1)}", "kat": p.get("kat"), "sinif": beton_sinif or "",
                          "olcu": f"t = {_n(tk * 100)} cm", "uzunluk": None, "alan": alan, "beton": V, "kalip": alan, "donati": V * oran,
                          "donati_kaynak": f"yaklaşık {_n(oran)} kg/m³"})
        else:
            diger["panel"] += alan
    for e in celik:
        ks = e["ks"]
        p = yv.PROFILLER.get(e["profil"] or "") or {}
        e["g"] = p.get("g") if p.get("g") else ks["A"] * CELIK_YOGUNLUK
        e["g_kaynak"] = "katalog" if p.get("g") else "A·7850"
        e["kutle"] = e["g"] * e["L"]
        e["cevre"] = _profil_cevresi(p, ks)
        e["boya"] = e["cevre"] * e["L"] if e["cevre"] else None
    return beton, celik, diger


def _t_metraj_betonarme(c, mh):
    beton = mh[0]
    satirlar = [_R({"tur": _TUR_AD.get(b["tur"], b["tur"]), "no": b["no"], "adres": b["adres"], "kat": b["kat"], "sinif": b["sinif"],
                    "olcu": b["olcu"], "uzunluk": b["uzunluk"], "alan": b["alan"], "beton": b["beton"], "kalip": b["kalip"],
                    "donati": b["donati"], "oran": b["donati"] / b["beton"] if b["beton"] else None, "donati_kaynak": b["donati_kaynak"]})
                for b in beton]
    return _T("metraj_betonarme", "Metraj: Betonarme Elemanlar", "Metraj",
              [_S("tur", "Tür", tur="metin"), _S("no", "No", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("sinif", "Beton sınıfı", tur="metin"), _S("olcu", "Ölçü", tur="metin"), _S("uzunluk", "Net boy", "m", ondalik=2),
               _S("alan", "Alan", "m²", ondalik=2), _S("beton", "Beton", "m³", ondalik=3), _S("kalip", "Kalıp", "m²", ondalik=2),
               _S("donati", "Donatı", "kg", ondalik=1), _S("oran", "Donatı oranı", "kg/m³", ondalik=0),
               _S("donati_kaynak", "Donatı kaynağı", tur="metin")],
              satirlar, "Eğitim amaçlı yaklaşık keşif. Kolon b·h·(H − t_döşeme); kiriş b·(h − t)·L_net (L_net = aks boyu − kolon yarı "
                        "genişlikleri); döşeme aks-aks alan·t; tekil temel B·L·h. Kalıp: kolon çevre·H, kiriş (b + 2(h − t))·L_net, döşeme "
                        "kiriş aralarındaki alt yüz, temel yan yüzler. Donatı: tasarım A_s (boyuna, aks boyunca; bindirme/kanca payı yok) + "
                        "etriye; tasarım yoksa 'yaklaşık' kg/m³ oranı (Metraj Varsayımları).", "Yaklaşık keşif — yönetmelik değeri değildir",
              toplam=_topla(satirlar, "beton", "kalip", "donati"))


def _t_metraj_celik(c, mh):
    celik = mh[1]
    satirlar = [_R({"tur": _TUR_AD.get(e["tur"], e["tur"]), "no": e["no"], "adres": e["adres"], "kat": e["kat"], "profil": e["profil"],
                    "sinif": e["sinif"], "L": e["L"], "g": e["g"], "g_kaynak": e["g_kaynak"], "kutle": e["kutle"], "cevre": e["cevre"],
                    "boya": e["boya"]}) for e in celik]
    return _T("metraj_celik", "Metraj: Çelik Elemanlar", "Metraj",
              [_S("tur", "Tür", tur="metin"), _S("no", "No", ondalik=0), _S("adres", "Adres", tur="metin"), _S("kat", "Kat", ondalik=0),
               _S("profil", "Profil", tur="metin"), _S("sinif", "Çelik sınıfı", tur="metin"), _S("L", "Uzunluk", "m", ondalik=3),
               _S("g", "Birim ağırlık", "kg/m", ondalik=1), _S("g_kaynak", "g kaynağı", tur="metin"), _S("kutle", "Kütle", "kg", ondalik=1),
               _S("cevre", "Boya çevresi", "m²/m", ondalik=3), _S("boya", "Boya yüzeyi", "m²", ondalik=2)],
              satirlar, "Uzunluk düğümden düğüme (eksen boyu); birim ağırlık profil kataloğundan (yoksa A·7850 kg/m³); boya çevresi "
                        "I/H profilde U = 2h + 4b − 2t_w − (8 − 2π)r. Bağlantı payı profil özetinde eklenir.",
              "yapi_veri.PROFILLER (Avrupa profil kataloğu / EN 10365)", toplam=_topla(satirlar, "L", "kutle", "boya"))


def _t_metraj_profil(c, mh):
    pay = _baglanti_payi(c)
    gr = {}
    for e in mh[1]:
        g = gr.setdefault((e["profil"], e["sinif"]), {"adet": 0, "L": 0.0, "g": e["g"], "kutle": 0.0, "boya": 0.0})
        g["adet"] += 1
        g["L"] += e["L"]
        g["kutle"] += e["kutle"]
        g["boya"] += e["boya"] or 0.0
    satirlar = []
    for (profil, sinif), g in sorted(gr.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
        kp = g["kutle"] * (1 + pay)
        satirlar.append(_R({"profil": profil, "sinif": sinif, "adet": g["adet"], "L": g["L"], "g": g["g"], "kutle": g["kutle"],
                            "pay": pay * 100, "kutle_payli": kp, "ton": kp / 1000.0, "boya": g["boya"]}))
    return _T("metraj_profil_ozeti", "Metraj: Çelik Profil Özeti", "Metraj",
              [_S("profil", "Profil", tur="metin"), _S("sinif", "Sınıf", tur="metin"), _S("adet", "Adet", ondalik=0),
               _S("L", "Toplam uzunluk", "m", ondalik=2), _S("g", "Birim ağırlık", "kg/m", ondalik=1), _S("kutle", "Net kütle", "kg", ondalik=1),
               _S("pay", "Bağlantı payı", "%", ondalik=1), _S("kutle_payli", "Kütle (paylı)", "kg", ondalik=1),
               _S("ton", "Kütle (paylı)", "t", ondalik=3), _S("boya", "Boya yüzeyi", "m²", ondalik=2)],
              satirlar, f"Bağlantı (levha, bulon, kaynak) payı %{_n(pay * 100)} — Metraj Varsayımları tablosundan değiştirilebilir.",
              "Yaklaşık keşif", toplam=_topla(satirlar, "adet", "L", "kutle", "kutle_payli", "ton", "boya"))


def _t_metraj_ozet(c, mh):
    beton, celik, diger = mh
    pay = _baglanti_payi(c)
    satirlar = []
    sinif_tur = {}
    for b in beton:
        sinif_tur.setdefault(b["sinif"] or "beton", {}).setdefault(b["tur"], 0.0)
        sinif_tur[b["sinif"] or "beton"][b["tur"]] += b["beton"]
    for sinif, turler in sinif_tur.items():
        for tur, v in turler.items():
            satirlar.append(_R({"kalem": f"Beton — {_TUR_AD.get(tur, tur).lower()}", "malzeme": sinif, "miktar": v, "birim": "m³", "aciklama": ""}))
        satirlar.append(_R({"kalem": "Beton (toplam)", "malzeme": sinif, "miktar": sum(turler.values()), "birim": "m³", "aciklama": ""}, ozet=True))
    if beton:
        satirlar.append(_R({"kalem": "Kalıp", "malzeme": "", "miktar": sum(b["kalip"] for b in beton), "birim": "m²",
                            "aciklama": "kolon, kiriş, döşeme alt yüzü, temel yanları"}))
        donati = sum(b["donati"] for b in beton)
        dad = ""
        if c.B:
            for m in c.B.malzemeler.values():
                if m["tur"] == "donati":
                    dad = m["kutuphane"]
                    break
        top_v = sum(b["beton"] for b in beton)
        yaklasik = sum(1 for b in beton if b["donati_kaynak"].startswith("yaklaşık"))
        satirlar.append(_R({"kalem": "Donatı çeliği", "malzeme": dad or "B420C", "miktar": donati / 1000.0, "birim": "t",
                            "aciklama": f"{_n(round(donati, 1))} kg; ortalama {_n(round(donati / top_v, 1)) if top_v else 0} kg/m³; "
                                        f"{yaklasik}/{len(beton)} eleman yaklaşık oranla"}))
    if celik:
        net = sum(e["kutle"] for e in celik)
        siniflar = sorted({e["sinif"] for e in celik})
        satirlar.append(_R({"kalem": "Yapısal çelik (profil)", "malzeme": ", ".join(siniflar), "miktar": net * (1 + pay) / 1000.0, "birim": "t",
                            "aciklama": f"net {_n(round(net, 1))} kg + bağlantı payı %{_n(pay * 100)}"}))
        satirlar.append(_R({"kalem": "Boya yüzeyi", "malzeme": "", "miktar": sum(e["boya"] or 0.0 for e in celik), "birim": "m²",
                            "aciklama": "profil çevresi × uzunluk"}))
    for anahtar, alan in diger["duvar"].items():
        satirlar.append(_R({"kalem": "Duvar (kirişler üstü)", "malzeme": anahtar, "miktar": alan, "birim": "m²",
                            "aciklama": "net kiriş boyu × duvar yüksekliği (boşluklar düşülmedi)"}))
    if diger["doseme_alan"]:
        satirlar.append(_R({"kalem": "Döşeme alanı (aks-aks)", "malzeme": "", "miktar": diger["doseme_alan"], "birim": "m²", "aciklama": ""}))
    if diger["panel"]:
        satirlar.append(_R({"kalem": "Panel / sac kaplama", "malzeme": "", "miktar": diger["panel"], "birim": "m²",
                            "aciklama": "kalınlığı 0 olan paneller"}))
    return _T("metraj_ozet", "Metraj Özeti", "Metraj",
              [_S("kalem", "Kalem", tur="metin"), _S("malzeme", "Malzeme / sınıf", tur="metin"), _S("miktar", "Miktar", ondalik=3),
               _S("birim", "Birim", tur="metin"), _S("aciklama", "Açıklama", tur="metin")],
              satirlar, "Malzeme → miktar. Eğitim amaçlı yaklaşık keşiftir; birim fiyat ve pozlar (Çevre ve Şehircilik Bakanlığı birim "
                        "fiyatları) kapsam dışıdır.", "Yaklaşık keşif — yönetmelik değeri değildir")


def _t_metraj_varsayimlari(c):
    pay = _baglanti_payi(c)
    satirlar = [
        _R({"parametre": "Çelik bağlantı payı", "deger": pay, "birim": "oran", "aciklama": "0,10 = %10 (levha, bulon, kaynak)"},
           {"deger": ["metraj", "baglanti_payi"]}),
    ]
    for tur, ad in (("kolon", "Kolon"), ("kiris", "Kiriş"), ("doseme", "Döşeme / panel"), ("temel", "Tekil temel"), ("diger", "Diğer betonarme")):
        satirlar.append(_R({"parametre": f"Yaklaşık donatı oranı — {ad}", "deger": _donati_orani(c, tur), "birim": "kg/m³",
                            "aciklama": "tasarım A_s yoksa kullanılır (yaklaşık öğretim değeri)"},
                           {"deger": ["metraj", "donati_orani", tur]}))
    satirlar += [
        _R({"parametre": "Çelik / donatı yoğunluğu", "deger": CELIK_YOGUNLUK, "birim": "kg/m³", "aciklama": "TS 498: 78,5 kN/m³"}),
        _R({"parametre": "Kolon etriyesi (tasarım vermezse)", "deger": f"Φ{_n(KOLON_ETRIYE[0])}/{_n(KOLON_ETRIYE[1] * 100)}", "birim": "",
            "aciklama": "varsayım"}, hucre={"deger": {"tur": "metin"}}),
    ]
    return _T("metraj_varsayimlari", "Metraj Varsayımları", "Metraj",
              [_S("parametre", "Parametre", tur="metin"), _S("deger", "Değer", duzenlenebilir=True, ondalik=3),
               _S("birim", "Birim", tur="metin"), _S("aciklama", "Açıklama", tur="metin")],
              satirlar, "Metraj parametreleri bina JSON'unda 'metraj' altında saklanır (analizi etkilemez).", "Yaklaşık keşif")


# ============================================================================
# Ana işlev
# ============================================================================
def bina_tablolari(bina, veri=None, *, kati=False):
    """Bina (sözlük ya da JSON metni) ve isteğe bağlı çözüm verisi (``yapi.bina_coz(...).veri``) → TABLO listesi (§15.1).

    veri yoksa Model + Yükler (girdi) + Metraj (+ deprem kartı etkinse çözümsüz deprem önizlemesi) tabloları; veri varsa
    Analiz, Deprem, Tasarım ve Temel tabloları da. ``kati=True``: bir tablo kurulamazsa hata yükseltilir (testler); varsayılan
    davranışta o tablo atlanır (rapor ve arayüz kırılmaz)."""
    c = _Baglam(bina, veri)
    tablolar = []

    def ekle(fn, *a):
        try:
            t = fn(c, *a)
        except Exception:  # noqa: BLE001
            if kati:
                raise
            return
        if t is not None:
            tablolar.append(t)

    for fn in (_t_genel, _t_katlar, _t_akslar, _t_dugumler, _t_cubuklar, _t_kesitler, _t_malzemeler, _t_dosemeler, _t_paneller,
               _t_mesnetler, _t_temeller,
               _t_yuk_durumlari, _t_doseme_yukleri, _t_duvar_yukleri, _t_kar_ruzgar, _t_ek_yukler, _t_eleman_yukleri, _t_kat_agirliklari,
               _t_kombinasyonlar):
        ekle(fn)
    if (c.B and c.B.deprem) or (c.veri and c.veri.get("deprem")) or isinstance(c.ham.get("deprem"), dict):
        ekle(_t_deprem_parametreleri)
        if _deprem_verisi(c):
            for fn in (_t_spektrum, _t_kat_kuvvetleri, _t_burulma, _t_oteleme, _t_theta):
                ekle(fn)
    if c.veri is not None:
        for fn in (_t_yer_degistirmeler, _t_tepkiler, _t_zarf, _t_kombinasyon_ozeti, _t_kolon_yukleri, _t_korunum,
                   _t_tasarim_kiris, _t_tasarim_kolon, _t_tasarim_celik):
            ekle(fn)
    ekle(_t_temel_parametreleri)
    if c.veri is not None:
        ekle(_t_temel_basinclari)
        ekle(_t_temel_dugumleri)
    try:
        mh = _metraj_hesap(c)
    except Exception:  # noqa: BLE001
        if kati:
            raise
        mh = None
    if mh is not None:
        for fn in (_t_metraj_ozet, _t_metraj_betonarme, _t_metraj_celik, _t_metraj_profil):
            if fn in (_t_metraj_celik, _t_metraj_profil) and not mh[1]:
                continue
            ekle(fn, mh)
    ekle(_t_metraj_varsayimlari)
    sira = {g: i for i, g in enumerate(GRUPLAR)}
    tablolar.sort(key=lambda t: sira.get(t["grup"], len(sira)))     # kararlı: grup içi sıra korunur
    return tablolar


def tablo(tablolar, ad):
    """Listeden ada göre tablo (yoksa None)."""
    return next((t for t in tablolar if t.get("ad") == ad), None)


def metraj_ozeti(bina, veri=None):
    """Rapor için kısayol: yalnız 'metraj_ozet' tablosu."""
    return tablo(bina_tablolari(bina, veri), "metraj_ozet")
