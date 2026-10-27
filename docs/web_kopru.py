# -*- coding: utf-8 -*-
"""Pyodide köprüsü: tarayıcıdan gelen JSON isteğini matris_ogren'e iletir, yanıtı JSON olarak döndürür.

İstek (JSON metni):
  {"islem": "topla", "girdi": {"A": "1 2; 3 4", "B": "5 6; 7 8"},
   "ayarlar": {"ondalik": false, "basamak": 4, "en_fazla_eleman": 36, "sema": true}}
  "sema" (varsayılan true): adım adım oklu şema bloklarını da üret. Kapalıysa motor SVG hiç çizmez.

Yanıt (JSON metni):
  {"ad": "C",
   "bloklar": [{"tur": "md" | "math", "icerik": "...", "etiket": "adim" | "kural" | "sonuc"},
               {"tur": "kod", "baslik": "🐍 Python ile", "kod": "...", "cikti": "...", "etiket": "python"},
               {"tur": "sema", "icerik": {"baslik": "...", "kareler": [{"baslik": "...", "svg": "<svg ...>"}, ...]},
                "etiket": "sema"}],
   "sonuc_etiket": "\\mathbf{C}", "sonuc_latex": "\\begin{bmatrix}...", "sonuc_metin": "6 8; 10 12",
   "zincir": true, "hata": null}
  "sema" bloğunun "icerik" değeri metin değil sözlüktür (her kare = bir adım: başlık + eksiksiz, durağan SVG);
  tarayıcı bunu markdown'a değil, adım adım oynatıcıya (app.js) verir.
Hata durumunda: {"hata": "...", "hata_turu": "girdi" | "ic", "iz": "..."}

Sonlu eleman işlemleri (sonlu_eleman.py):
  "se_coz":      girdi {"model": {...} | "JSON metni"} → yukarıdaki yanıt biçimi + "veri" (Sonuc.veri: düğümler, elemanlar,
                 diyagramlar, tepkiler, yaylar, çökmeler, denge, boyut ...); "zincir" her zaman false. Model türleri:
                 yay, cubuk, kafes, kiris, cerceve, kafes3b, cerceve3b; isteğe bağlı yaylar, cokmeler ve eleman zemin'i.
  "se_ornekler": → {"ornekler": [{ad, baslik, tip, aciklama}], "hata": null}
  "se_ornek":    girdi {"ad": "kafes-iki-cubuk"} → {"ad", "model": {...}, "hata": null}

Bina işlemleri (yapi.py + yapi_veri.py):
  "bina_coz":       girdi {"bina": {...} | "JSON metni"} → {"ad": "bina", "bloklar", "veri" (yapi.bina_coz şeması: bina, ag,
                    yukler, durumlar, kombinasyonlar, sonuclar, zarf, akis, ozet, fe_model, deprem, ruzgar, kar, kutle_merkezi,
                    cozum_kimligi), "sonuc_metin", "zincir": false, "hata"}; çözümün iç paketi tembel kombinasyonlar için
                    önbelleğe alınır
  "bina_kutuphane": → {"malzemeler", "kesit_katalogu", "kullanim_siniflari", "duvarlar", "kaplamalar", "kombinasyon_kumeleri",
                    "sablonlar", "dogrulanmamis", ..., "hata": null}
  "bina_sablonlar": → {"sablonlar": [{ad, baslik, sistem, aciklama, kat, aks}], "hata": null}
  "bina_sablon":    girdi {"ad": "betonarme-2kat-3x2"} → {"ad", "bina": {...}, "hata": null}
  "bina_yuk_yolu":  girdi {"bina", "veri", "hedef": {"tur": "doseme"|"kiris"|"kolon", "no", "durum"}} → {"adimlar": [...], "hata": null}
  "bina_deprem":    girdi {"bina"} → {"deprem": (veri.deprem şeması, çözümsüz önizleme: spektrum, V_tE, F_i, V_i; "tahmin": true),
                    "hata": null}
  "bina_kombinasyon": girdi {"cozum_kimligi", "ad", "katsayilar"?, "bina"?} → {"ad", "cozum_kimligi", "sonuc": KISA (tam diziler),
                    "hata": null}. Son çözümler (en çok BINA_ONBELLEK_EN_FAZLA) bellekte tutulur; kimlik önbellekte yoksa ve
                    "bina" verilmişse bina anlatımsız yeniden çözülür, yoksa öğretici hata.
  "bina_eleman_tasarim": girdi {"cozum_kimligi", "tur": "kiris"|"kolon", "no" (bina eleman no'su), "bina"?} → {"ad", "bloklar"
                    (tasarim.py anlatımı: kesit şeması, formüller, N–M eğrisi), "sonuc": veri.tasarim.elemanlar[] kaydı (§11) +
                    kolonda "egri_x", "egri_y" [{N, M}] ve "noktalar" [{ad, kombinasyon, uc, N, Mx, My, dc}], çelikte "kuvvetler",
                    "uyarilar"; "cozum_kimligi", "hata": null}. Önbellek bina_kombinasyon ile aynı (tasarim.py yoksa öğretici hata).
                    Genel (surum 3) modelde "tur": "cubuk" (ya da çubuk türü) ve "no" çubuk numarasıdır; aks–kat kökenli çubuk
                    için "kolon"/"kiris" ve aks–kat no'su da kabul edilir.
  "bina_kesit_oner": girdi {"cozum_kimligi" | "bina", "hedef": "hepsi" | [{"tur", "no"}], "yinele": 0..3} → {"oneriler":
                    [{cubuk, tur, kesit, oneri (profil adı ya da "bxh" cm), gerekce [metin], dc_once, dc_oneri, dc_sonra, degisim}],
                    "turlar": [{tur, dc_maks, oneri_sayisi, degisen}], "dc_once", "dc_sonra", "bina" (yinele > 0: öneriler
                    uygulanmış bina JSON'u; aynı (kesit, tür) grubuna grubun en ağır önerisi), "cozum_kimligi", "aciklama",
                    "hata": null}. yinele > 0: öneri uygulanıp yeniden çözülür (rijitlik değişince kuvvetler değişir), en çok 3 tur.

Genel model (bina "surum": 3, yapi_serbest.py): bina_coz veri'sine ek alanlar — ag.cubuklar, ag.paneller (kenarlar, taşıyan
kenarlar), ag.dugumler[].tur ("aks" | "bolme" | "kesisim" | "ic" | "efendi"), ag.donme_tutulan, ag.diyafram_seviye,
yukler.paneller / yukler.cubuklar, bina.seviyeler (kat, kot, diyafram), kren (kopruler, durumlar, zarf), yalniz_cekme
(var, kombinasyonlar: etkin_degil, yineleme), uyarilar; tasarim.elemanlar[] her çubuk için (tur: kolon, kiris, capraz,
makas-*, asik, kren, bag, diger; cubuk, grup, L, varsayimlar).
"""
from __future__ import annotations

import ast
import importlib
import json
import sys
import traceback
from collections import OrderedDict

import sympy as sp

import matris_ogren as mo

mo.ayarla(goster="yok")

ISLEMLER = {
    "topla", "cikar", "skaler", "carp", "transpoz", "iz", "rank", "determinant", "ters", "coz", "ozdeger",
    "cubuk_eleman", "kiris_eleman", "kafes_eleman", "birlestir", "sinir_kosulu", "yardim",
}


def surum_json() -> str:
    return json.dumps({
        "motor": getattr(mo, "__version__", "?"),
        "sympy": sp.__version__,
        "python": sys.version.split()[0],
    })


# ---------------------------------------------------------------------------
# yardımcılar
# ---------------------------------------------------------------------------
def _sayi_listesi(v) -> list[int]:
    """'1 4' / '1,4' / [1, 4] → [1, 4]"""
    if isinstance(v, (list, tuple)):
        return [int(x) for x in v]
    return [int(p) for p in str(v).replace(",", " ").replace(";", " ").split()]


def _sayi(v):
    """Açı gibi sayısal alanlar: '45' → 45, '22.5' → 22.5"""
    s = str(v).strip()
    try:
        return int(s)
    except ValueError:
        return float(sp.sympify(s))


def _metin(d) -> str:
    """Sonucu yeniden girdi olarak kullanılabilecek 'a b; c d' metnine çevirir."""
    if isinstance(d, sp.MatrixBase):
        return "; ".join(" ".join(str(d[i, j]) for j in range(d.cols)) for i in range(d.rows))
    if isinstance(d, tuple) and d and isinstance(d[0], (list, tuple)):  # ozdeger: (degerler, ozvektorler)
        return " ".join(str(x) for x in d[0])
    return str(d)


def _zincir(d) -> bool:
    return isinstance(d, (sp.MatrixBase, sp.Expr))


def _latex(islem: str, r) -> str:
    d = r.deger
    if islem == "ozdeger":
        ozd = d[0] if isinstance(d, tuple) else d
        return r",\quad ".join(rf"\lambda_{{{i + 1}}} = {mo.L(x)}" for i, x in enumerate(ozd))
    try:
        return r.latex()
    except Exception:
        return sp.latex(d)


def _etiket(islem: str, ad) -> str:
    if islem == "ozdeger" or not ad:
        return ""
    ozel = {
        "det": r"\det(\mathbf{A})",
        "tr": r"\operatorname{tr}(\mathbf{A})",
        "rank": r"\operatorname{rank}(\mathbf{A})",
        "A^T": r"\mathbf{A}^{T}",
        "A^{-1}": r"\mathbf{A}^{-1}",
    }
    if ad in ozel:
        return ozel[ad]
    return rf"\mathbf{{{ad}}}"


def _sema(icerik) -> dict:
    """Ok şeması bloğunu JSON'a güvenli biçime getirir: {"baslik": str, "kareler": [{"baslik": str, "svg": str}]}.

    Motor her kareyi eksiksiz, durağan bir SVG olarak üretir (metinleri kaçışlıdır); burada yalnız tür/boşluk
    denetimi yapılır. SVG'siz kareler atılır."""
    if not isinstance(icerik, dict):
        return {"baslik": "", "kareler": []}
    kareler = []
    for k in icerik.get("kareler") or []:
        if isinstance(k, dict) and str(k.get("svg", "")).strip():
            kareler.append({"baslik": str(k.get("baslik", "")), "svg": str(k["svg"])})
    return {"baslik": str(icerik.get("baslik", "")), "kareler": kareler}


def _bloklar(anl) -> list[dict]:
    cikti = []
    for tur, icerik, etiket in anl.bloklar:
        if tur == "kod":
            baslik, kod, ck = icerik
            cikti.append({"tur": "kod", "baslik": baslik, "kod": kod, "cikti": ck, "etiket": etiket})
        elif tur == "sema":
            sema = _sema(icerik)
            if sema["kareler"]:
                cikti.append({"tur": "sema", "icerik": sema, "etiket": etiket})
        else:
            cikti.append({"tur": tur, "icerik": icerik, "etiket": etiket})
    return cikti


def _liste(g: dict, anahtar: str) -> list:
    v = g.get(anahtar)
    return list(v) if isinstance(v, (list, tuple)) else []


def _bos(v) -> bool:
    return v is None or not str(v).strip()


# ---------------------------------------------------------------------------
# işlem dağıtıcı
# ---------------------------------------------------------------------------
def _calistir(islem: str, g: dict):
    A, B = g.get("A", ""), g.get("B", "")
    if islem in ("topla", "cikar", "skaler", "transpoz", "iz", "rank", "determinant", "ters", "coz", "ozdeger") and _bos(A):
        raise mo.MatrisHatasi("A matrisini girin (örnek: 1 2; 3 4).")

    if islem in ("topla", "cikar"):
        if _bos(B):
            raise mo.MatrisHatasi("B matrisini girin.")
        return getattr(mo, islem)(A, B)
    if islem == "skaler":
        return mo.skaler(g.get("k") if not _bos(g.get("k")) else "1", A)
    if islem == "carp":
        m = [x for x in _liste(g, "matrisler") if not _bos(x)]
        if len(m) < 2:
            raise mo.MatrisHatasi("Çarpım için en az iki matris girin.")
        return mo.carp(*m)
    if islem in ("transpoz", "iz", "rank"):
        return getattr(mo, islem)(A)
    if islem == "determinant":
        kw = {"yontem": g["yontem"]} if not _bos(g.get("yontem")) else {}
        return mo.determinant(A, **kw)
    if islem == "ters":
        kw = {"yontem": g["yontem"]} if not _bos(g.get("yontem")) else {}
        return mo.ters(A, **kw)
    if islem == "coz":
        b = g.get("b", "")
        if _bos(b):
            raise mo.MatrisHatasi("b vektörünü girin (örnek: 3; 5).")
        kw = {}
        if not _bos(g.get("yontem")):
            kw["yontem"] = g["yontem"]
        if not _bos(g.get("bilinmeyen")):
            kw["bilinmeyen"] = str(g["bilinmeyen"]).strip()
        return mo.coz(A, b, **kw)
    if islem == "ozdeger":
        M = g.get("M")
        return mo.ozdeger(A, None if _bos(M) else M, ozvektor=bool(g.get("ozvektor", True)))
    if islem == "cubuk_eleman":
        return mo.cubuk_eleman(g.get("E") or "E", g.get("A") or "A", g.get("L") or "L")
    if islem == "kiris_eleman":
        return mo.kiris_eleman(g.get("E") or "E", g.get("I") or "I", g.get("L") or "L")
    if islem == "kafes_eleman":
        aci = g.get("aci")
        return mo.kafes_eleman(g.get("E") or "E", g.get("A") or "A", g.get("L") or "L",
                               aci_derece=0 if _bos(aci) else _sayi(aci))
    if islem == "birlestir":
        elemanlar = []
        for i, e in enumerate(_liste(g, "elemanlar"), start=1):
            k, dof = (e.get("k"), e.get("dof")) if isinstance(e, dict) else (e[0], e[1])
            if _bos(k):
                continue
            try:
                dof_l = _sayi_listesi(dof)
            except ValueError:
                raise mo.MatrisHatasi(f"Eleman {i}: serbestlik numaraları tam sayı olmalı (örnek: 1 2).") from None
            if not dof_l:
                raise mo.MatrisHatasi(f"Eleman {i}: global serbestlik numaralarını girin (örnek: 1 2).")
            elemanlar.append((k, dof_l))
        if not elemanlar:
            raise mo.MatrisHatasi("En az bir eleman matrisi girin.")
        n = g.get("n")
        if _bos(n):
            raise mo.MatrisHatasi("Toplam serbestlik sayısını girin.")
        try:
            n_int = int(str(n).strip())
        except ValueError:
            raise mo.MatrisHatasi("Toplam serbestlik sayısı tam sayı olmalı.") from None
        return mo.birlestir(elemanlar, n_int)
    if islem == "sinir_kosulu":
        K, F = g.get("K", ""), g.get("F", "")
        if _bos(K) or _bos(F):
            raise mo.MatrisHatasi("K matrisini ve F vektörünü girin.")
        try:
            sabit = _sayi_listesi(g.get("sabit", ""))
        except ValueError:
            raise mo.MatrisHatasi("Tutulu (sabit) serbestlik dereceleri (SD) tam sayı olmalı (örnek: 1 4).") from None
        # Boş bırakılırsa motor mesnetsiz durumu kendisi değerlendirir (K tekilse öğretici hata verir).
        kw = {}
        if not _bos(g.get("bilinmeyen")):
            kw["bilinmeyen"] = str(g["bilinmeyen"]).strip()
        return mo.sinir_kosulu(K, F, sabit, **kw)
    raise mo.MatrisHatasi(f"Bilinmeyen işlem: {islem!r}")


# ---------------------------------------------------------------------------
# ders örneği çalıştırma ("ders_calistir")
# ---------------------------------------------------------------------------
KOD_EN_FAZLA = 6000


def _se_modulu():
    """sonlu_eleman.py varsa (tembel) içe aktarır; yoksa None. Eski kurulumlarda dosya bulunmayabilir."""
    try:
        return importlib.import_module("sonlu_eleman")
    except ImportError:
        return None


def _yapi_modulu():
    """yapi.py (bina analizi) varsa (tembel) içe aktarır; yoksa None. sonlu_eleman.py'ye bağımlıdır."""
    try:
        return importlib.import_module("yapi")
    except ImportError:
        return None


def _tasarim_modulu():
    """tasarim.py (TS 500 / ÇYTHYE kesit tahkikleri) varsa (tembel) içe aktarır; yoksa None."""
    try:
        return importlib.import_module("tasarim")
    except ImportError:
        return None


def _sonuc_mu(x) -> bool:
    return isinstance(x, mo.Sonuc) or (hasattr(x, "anlatim") and hasattr(x, "deger") and hasattr(x.anlatim, "bloklar"))


def _kod_calistir(kod: str):
    """Ders örneği kodunu çalıştırır; son satırdaki ifadenin değerini döndürür (testler/test_dersler.calistir ile aynı):
    son deyim ayrılır, kalanı exec edilir, son ifade eval edilir. Ad alanı: mo, sp ve varsa se, yapi, tasarim."""
    agac = ast.parse(kod)
    if not agac.body:
        raise mo.MatrisHatasi("Örnek kodu boş.")
    son = agac.body.pop()
    if not isinstance(son, ast.Expr):
        raise mo.MatrisHatasi("Örnek kodunun son satırı bir değer (ifade) olmalı.")
    ad_alani = {"mo": mo, "sp": sp}
    se = _se_modulu()
    if se is not None:
        ad_alani["se"] = se
    yapi = _yapi_modulu()
    if yapi is not None:
        ad_alani["yapi"] = yapi
    tasarim = _tasarim_modulu()
    if tasarim is not None:
        ad_alani["tasarim"] = tasarim
    exec(compile(agac, "<ornek>", "exec"), ad_alani)
    return eval(compile(ast.Expression(son.value), "<ornek>", "eval"), ad_alani)


def _ders_yaniti(deger) -> dict:
    """Örnek kodunun değerini normal işlem yanıtı biçimine çevirir (uygulama aynı çiziciyi kullanır)."""
    if isinstance(deger, (list, tuple)) and deger and all(_sonuc_mu(x) for x in deger):
        bloklar = []
        for i, r in enumerate(deger, start=1):
            bloklar.append({"tur": "md", "icerik": f"#### {i}. adım" + (f": {r.ad}" if r.ad else ""), "etiket": "adim"})
            bloklar += _bloklar(r.anlatim)
        son = deger[-1]
        return {
            "ad": son.ad, "bloklar": bloklar,
            "sonuc_etiket": _etiket("ders", son.ad), "sonuc_latex": _latex("ders", son),
            "sonuc_metin": _metin(son.deger), "zincir": _zincir(son.deger), "hata": None,
        }
    if _sonuc_mu(deger):
        return {
            "ad": deger.ad, "bloklar": _bloklar(deger.anlatim),
            "sonuc_etiket": _etiket("ders", deger.ad), "sonuc_latex": _latex("ders", deger),
            "sonuc_metin": _metin(deger.deger), "zincir": _zincir(deger.deger), "hata": None,
        }
    if deger is None:
        raise mo.MatrisHatasi("Örnek kodu bir değer döndürmedi.")
    if isinstance(deger, str):
        return {"ad": "", "bloklar": [{"tur": "md", "icerik": deger, "etiket": "sonuc"}],
                "sonuc_etiket": "", "sonuc_latex": "", "sonuc_metin": deger, "zincir": False, "hata": None}
    if isinstance(deger, (bool, int, float, complex)):
        deger = sp.sympify(deger)
    tex = sp.latex(deger)
    return {"ad": "", "bloklar": [{"tur": "math", "icerik": tex, "etiket": "sonuc"}],
            "sonuc_etiket": "", "sonuc_latex": tex, "sonuc_metin": _metin(deger), "zincir": _zincir(deger), "hata": None}


def _ders_calistir(girdi: dict) -> dict:
    kod = girdi.get("kod")
    if not isinstance(kod, str) or not kod.strip():
        raise mo.MatrisHatasi("Örnek kodu boş.")
    if len(kod) > KOD_EN_FAZLA:
        raise mo.MatrisHatasi(f"Örnek kodu çok uzun ({len(kod)} karakter; en fazla {KOD_EN_FAZLA}).")
    try:
        deger = _kod_calistir(kod)
    except mo.MatrisHatasi:
        raise
    except Exception as e:  # noqa: BLE001 — sözdizimi, ad ve çalışma hataları öğrenciye okunur biçimde gider
        # Ders kodunun kendi hatası (sözdizimi, NameError…) "girdi" hatası gibi, izsiz bildirilir.
        raise mo.MatrisHatasi(f"Örnek kodu çalışmadı: {type(e).__name__}: {e}") from e
    return _ders_yaniti(deger)


# ---------------------------------------------------------------------------
# sonlu eleman ("se_coz", "se_ornekler", "se_ornek")
# ---------------------------------------------------------------------------
SE_ISLEMLER = {"se_coz", "se_ornekler", "se_ornek"}
SE_MODEL_EN_FAZLA = 200_000   # model JSON metni için üst sınır (karakter)


def _se_zorunlu():
    se = _se_modulu()
    if se is None:
        raise mo.MatrisHatasi("Sonlu eleman modülü (sonlu_eleman.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    return se


def _sonlu_sayilar(v):
    """JSON'a uygun olmayan sayıları (nan, ±inf) None yapar; tarayıcıdaki JSON.parse bunları okuyamaz."""
    if isinstance(v, float):
        return v if v == v and v not in (float("inf"), float("-inf")) else None
    if isinstance(v, dict):
        return {k: _sonlu_sayilar(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_sonlu_sayilar(x) for x in v]
    return v


def _se_coz_yaniti(girdi: dict) -> dict:
    """{"model": {...} ya da JSON metni} → matris işlemleriyle aynı yanıt biçimi + "veri" (yapılı sonuçlar)."""
    se = _se_zorunlu()
    model = girdi.get("model")
    if model is None or (isinstance(model, str) and not model.strip()):
        raise mo.MatrisHatasi("Model boş: düğüm, eleman, mesnet ve yük tanımlayın ya da bir örnek seçin.")
    if isinstance(model, str) and len(model) > SE_MODEL_EN_FAZLA:
        raise mo.MatrisHatasi(f"Model metni çok uzun ({len(model)} karakter; en fazla {SE_MODEL_EN_FAZLA}).")
    r = se.se_coz(model)
    return {
        "ad": r.ad, "bloklar": _bloklar(r.anlatim),
        "sonuc_etiket": _etiket("se_coz", r.ad), "sonuc_latex": _latex("se_coz", r),
        "sonuc_metin": _metin(r.deger), "zincir": False, "hata": None,
        "veri": _sonlu_sayilar(r.veri),
    }


def _se_islem(islem: str, girdi: dict) -> dict:
    if islem == "se_coz":
        return _se_coz_yaniti(girdi)
    se = _se_zorunlu()
    if islem == "se_ornekler":
        return {"ornekler": se.ornek_listesi(), "hata": None}
    ad = str(girdi.get("ad", "")).strip()
    return {"ad": ad, "model": se.ornek_model(ad), "hata": None}


# ---------------------------------------------------------------------------
# bina analizi ("bina_coz", "bina_kutuphane", "bina_sablonlar", "bina_sablon", "bina_yuk_yolu", "bina_deprem",
# "bina_kombinasyon", "bina_eleman_tasarim")
# ---------------------------------------------------------------------------
BINA_ISLEMLER = {"bina_coz", "bina_sablonlar", "bina_sablon", "bina_kutuphane", "bina_yuk_yolu", "bina_deprem", "bina_kombinasyon",
                 "bina_eleman_tasarim", "bina_kesit_oner"}
BINA_EN_FAZLA = 300_000   # bina JSON metni için üst sınır (karakter)
BINA_ONBELLEK_EN_FAZLA = 3   # tembel kombinasyonlar ve eleman tahkik ayrıntısı için bellekte tutulan son çözüm sayısı
_BINA_ONBELLEK: "OrderedDict[str, dict]" = OrderedDict()


def _onbellege_koy(ic: dict) -> None:
    kimlik = ic.get("kimlik")
    if not kimlik:
        return
    _BINA_ONBELLEK.pop(kimlik, None)
    _BINA_ONBELLEK[kimlik] = ic
    while len(_BINA_ONBELLEK) > BINA_ONBELLEK_EN_FAZLA:
        _BINA_ONBELLEK.popitem(last=False)


def _yapi_zorunlu():
    yapi = _yapi_modulu()
    if yapi is None:
        raise mo.MatrisHatasi("Bina modülü (yapi.py / yapi_veri.py) yüklenemedi; uygulamayı yenileyin ya da önbelleği silin.")
    return yapi


def _bina_girdisi(girdi: dict):
    bina = girdi.get("bina")
    if bina is None or (isinstance(bina, str) and not bina.strip()):
        raise mo.MatrisHatasi("Bina modeli boş: akslar, katlar, kolon/kiriş/döşeme tanımlayın ya da bir şablon seçin.")
    if isinstance(bina, str) and len(bina) > BINA_EN_FAZLA:
        raise mo.MatrisHatasi(f"Bina metni çok uzun ({len(bina)} karakter; en fazla {BINA_EN_FAZLA}).")
    return bina


def _bina_coz_yaniti(girdi: dict) -> dict:
    yapi = _yapi_zorunlu()
    r = yapi.bina_coz(_bina_girdisi(girdi), goster="yok")
    _onbellege_koy(getattr(r, "ic", None) or {})
    veri = _sonlu_sayilar(r.veri)   # ozet.uyarilar: yalnız bu modelde kullanılan doğrulanmamış kayıtlar (motor yazar)
    return {
        "ad": "bina", "bloklar": _bloklar(r.anlatim),
        "sonuc_etiket": r"\mathbf{u}_G", "sonuc_latex": "",
        "sonuc_metin": f"{veri['ozet']['sd_sayisi']} SD, {veri['ozet']['kombinasyon_sayisi']} kombinasyon; "
                       f"G = {veri['ozet']['toplam_G']} kN, Q = {veri['ozet']['toplam_Q']} kN",
        "zincir": False, "hata": None, "veri": veri,
    }


def _bina_kombinasyon_yaniti(girdi: dict) -> dict:
    """Tek kombinasyonun tam KISA'sı: önce önbellekteki çözüm (cozum_kimligi), yoksa girdi.bina anlatımsız yeniden çözülür."""
    yapi = _yapi_zorunlu()
    ad = str(girdi.get("ad") or "").strip()
    if not ad:
        raise mo.MatrisHatasi("Kombinasyon adı (ad) boş; örn. \"1.4G+1.6Q\" ya da \"G+Q+0.2S+EX++0.3EY++0.3EZ\".")
    katsayilar = girdi.get("katsayilar")
    if katsayilar is not None and not isinstance(katsayilar, dict):
        raise mo.MatrisHatasi("katsayilar bir sözlük olmalı: {\"G\": 1.4, \"Q\": 1.6}.")
    ic = _bina_ic(yapi, girdi)
    sonuc = yapi.kombinasyon_kisa(ic, ad, katsayilar)
    return {"ad": ad, "cozum_kimligi": ic.get("kimlik"), "sonuc": _sonlu_sayilar(sonuc), "hata": None}


def _bina_ic(yapi, girdi: dict) -> dict:
    """Önbellekteki çözüm paketi (cozum_kimligi); yoksa girdi.bina anlatımsız yeniden çözülür ve önbelleğe konur."""
    kimlik = girdi.get("cozum_kimligi")
    ic = _BINA_ONBELLEK.get(str(kimlik)) if kimlik else None
    if ic is not None:
        _BINA_ONBELLEK.move_to_end(str(kimlik))
    elif girdi.get("bina") is not None:
        r = yapi.bina_coz(_bina_girdisi(girdi), goster="yok", anlat=False)
        ic = r.ic
        _onbellege_koy(ic)
    else:
        raise mo.MatrisHatasi("Bu çözüm bellekte yok (sayfa yenilendi ya da son " + str(BINA_ONBELLEK_EN_FAZLA)
                              + " çözümün dışında kaldı). Binayı yeniden çözün; kombinasyonlar ve kesit tahkikleri, çözümde hesaplanan "
                              "G, Q, S, W ve E durumlarının katsayılı toplamından kurulur (yeniden çözüm gerekmez, ama durumların "
                              "bellekte olması gerekir).")
    return ic


def _bina_eleman_tasarim_yaniti(girdi: dict) -> dict:
    """Tek bina elemanının anlatımlı kesit tahkiki (tasarim.py): önbellekteki çözümden, yoksa girdi.bina yeniden çözülür."""
    yapi = _yapi_zorunlu()
    if not hasattr(yapi, "eleman_tasarim"):
        raise mo.MatrisHatasi("Bu kurulumdaki bina modülü kesit tahkiki içermiyor; uygulamayı yenileyin.")
    tur = str(girdi.get("tur") or "").strip().lower()
    if girdi.get("no") is None:
        raise mo.MatrisHatasi("Eleman numarası (no) verilmedi: bina kirişinin ya da kolonunun no'su.")
    ic = _bina_ic(yapi, girdi)
    if tur not in ("kiris", "kolon") and not ic.get("serbest"):
        raise mo.MatrisHatasi("Eleman türü (tur) 'kiris' ya da 'kolon' olmalı.")
    r = yapi.eleman_tasarim(ic, tur, girdi.get("no"), goster="yok")
    return {"ad": r.ad, "bloklar": _bloklar(r.anlatim), "sonuc": _sonlu_sayilar(r.veri), "cozum_kimligi": ic.get("kimlik"),
            "hata": None}


def _bina_kesit_oner_yaniti(girdi: dict) -> dict:
    """Kesit önerisi (genel model motoru; aks–kat bina da genel modele çevrilerek çözülür): öneri, gerekçe, D/C önce/sonra."""
    _yapi_zorunlu()
    try:
        serbest = importlib.import_module("yapi_serbest")
    except ImportError:
        raise mo.MatrisHatasi("Kesit önerisi için yapi_serbest.py gerekir; uygulamayı yenileyin.") from None
    kimlik = girdi.get("cozum_kimligi")
    ic = _BINA_ONBELLEK.get(str(kimlik)) if kimlik else None
    bina = girdi.get("bina")
    if ic is None and bina is None:
        raise mo.MatrisHatasi("Kesit önerisi için çözüm kimliği (önbellekte) ya da bina gerekir; binayı yeniden çözün.")
    if bina is not None:
        bina = _bina_girdisi(girdi)
    hedef = girdi.get("hedef", "hepsi")
    if hedef not in (None, "hepsi") and not isinstance(hedef, list):
        raise mo.MatrisHatasi('hedef "hepsi" ya da [{"tur": "cubuk", "no": 3}] listesi olmalı.')
    r = serbest.kesit_oner(bina, ic=ic if (ic is not None and ic.get("serbest")) else None, hedef=hedef or "hepsi",
                           yinele=girdi.get("yinele", 0))
    return dict(_sonlu_sayilar(r), hata=None)


def _bina_islem(islem: str, girdi: dict) -> dict:
    if islem == "bina_kesit_oner":
        return _bina_kesit_oner_yaniti(girdi)
    if islem == "bina_coz":
        return _bina_coz_yaniti(girdi)
    if islem == "bina_kombinasyon":
        return _bina_kombinasyon_yaniti(girdi)
    if islem == "bina_eleman_tasarim":
        return _bina_eleman_tasarim_yaniti(girdi)
    yapi = _yapi_zorunlu()
    if islem == "bina_deprem":
        return {"deprem": _sonlu_sayilar(yapi.deprem_onizleme(_bina_girdisi(girdi))), "hata": None}
    if islem == "bina_kutuphane":
        return dict(_sonlu_sayilar(yapi.kutuphane()), hata=None)
    if islem == "bina_sablonlar":
        return {"sablonlar": yapi.bina_sablonlar(), "hata": None}
    if islem == "bina_sablon":
        ad = str(girdi.get("ad", "")).strip()
        return {"ad": ad, "bina": yapi.bina_sablon(ad), "hata": None}
    veri = girdi.get("veri")
    if not isinstance(veri, dict):
        raise mo.MatrisHatasi("Yük yolu için önce binayı çözün; 'veri' alanı bina_coz yanıtının 'veri' sözlüğü olmalı.")
    yol = yapi.yuk_yolu(_bina_girdisi(girdi), veri, girdi.get("hedef") or {})
    return dict(_sonlu_sayilar(yol), hata=None)


def calistir(istek_json: str) -> str:
    try:
        istek = json.loads(istek_json)
        ayar = istek.get("ayarlar") or {}
        motor_ayari = dict(
            goster="yok",
            ondalik=bool(ayar.get("ondalik", False)),
            basamak=max(1, min(12, int(ayar.get("basamak", 4) or 4))),
            en_fazla_eleman=max(0, int(ayar.get("en_fazla_eleman", 36) or 36)),
        )
        # Ok şemaları (adım adım SVG). Eski bir motor kopyası "sema" ayarını tanımıyorsa hata verme, atla.
        if hasattr(mo.ayarlar, "sema"):
            motor_ayari["sema"] = bool(ayar.get("sema", True))
        mo.ayarla(**motor_ayari)
        islem = str(istek.get("islem", ""))
        if islem == "ders_calistir":
            return json.dumps(_ders_calistir(istek.get("girdi") or {}), ensure_ascii=False)
        if islem in SE_ISLEMLER:
            return json.dumps(_se_islem(islem, istek.get("girdi") or {}), ensure_ascii=False)
        if islem in BINA_ISLEMLER:
            return json.dumps(_bina_islem(islem, istek.get("girdi") or {}), ensure_ascii=False)
        if islem not in ISLEMLER:
            raise mo.MatrisHatasi(f"Bilinmeyen işlem: {islem!r}")
        if islem == "yardim":
            return json.dumps({
                "ad": "yardim",
                "bloklar": [{"tur": "md", "icerik": mo.YARDIM_METNI, "etiket": "adim"}],
                "sonuc_etiket": "", "sonuc_latex": "", "sonuc_metin": "", "zincir": False, "hata": None,
            }, ensure_ascii=False)
        g = istek.get("girdi") or {}
        r = _calistir(islem, g)
        return json.dumps({
            "ad": r.ad,
            "bloklar": _bloklar(r.anlatim),
            "sonuc_etiket": _etiket(islem, r.ad),
            "sonuc_latex": _latex(islem, r),
            "sonuc_metin": _metin(r.deger),
            "zincir": _zincir(r.deger),
            "hata": None,
        }, ensure_ascii=False)
    except mo.MatrisHatasi as e:
        return json.dumps({"hata": str(e), "hata_turu": "girdi"}, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001 — tarayıcıya her hatayı okunur biçimde geri ver
        return json.dumps({
            "hata": f"{type(e).__name__}: {e}",
            "hata_turu": "ic",
            "iz": traceback.format_exc()[-1500:],
        }, ensure_ascii=False)
