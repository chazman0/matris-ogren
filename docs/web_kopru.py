# -*- coding: utf-8 -*-
"""Pyodide köprüsü: tarayıcıdan gelen JSON isteğini matris_ogren'e iletir, yanıtı JSON olarak döndürür.

İstek (JSON metni):
  {"islem": "topla", "girdi": {"A": "1 2; 3 4", "B": "5 6; 7 8"},
   "ayarlar": {"ondalik": false, "basamak": 4, "en_fazla_eleman": 36}}

Yanıt (JSON metni):
  {"ad": "C",
   "bloklar": [{"tur": "md" | "math", "icerik": "...", "etiket": "adim" | "kural" | "sonuc"},
               {"tur": "kod", "baslik": "🐍 Python ile", "kod": "...", "cikti": "...", "etiket": "python"}],
   "sonuc_etiket": "\\mathbf{C}", "sonuc_latex": "\\begin{bmatrix}...", "sonuc_metin": "6 8; 10 12",
   "zincir": true, "hata": null}
Hata durumunda: {"hata": "...", "hata_turu": "girdi" | "ic", "iz": "..."}
"""
from __future__ import annotations

import json
import sys
import traceback

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


def _bloklar(anl) -> list[dict]:
    cikti = []
    for tur, icerik, etiket in anl.bloklar:
        if tur == "kod":
            baslik, kod, ck = icerik
            cikti.append({"tur": "kod", "baslik": baslik, "kod": kod, "cikti": ck, "etiket": etiket})
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
            raise mo.MatrisHatasi("Sabit serbestlikler tam sayı olmalı (örnek: 1 4).") from None
        if not sabit:
            raise mo.MatrisHatasi("En az bir sabit serbestlik girin (örnek: 1).")
        kw = {}
        if not _bos(g.get("bilinmeyen")):
            kw["bilinmeyen"] = str(g["bilinmeyen"]).strip()
        return mo.sinir_kosulu(K, F, sabit, **kw)
    raise mo.MatrisHatasi(f"Bilinmeyen işlem: {islem!r}")


def calistir(istek_json: str) -> str:
    try:
        istek = json.loads(istek_json)
        ayar = istek.get("ayarlar") or {}
        mo.ayarla(
            goster="yok",
            ondalik=bool(ayar.get("ondalik", False)),
            basamak=max(1, min(12, int(ayar.get("basamak", 4) or 4))),
            en_fazla_eleman=max(0, int(ayar.get("en_fazla_eleman", 36) or 36)),
        )
        islem = str(istek.get("islem", ""))
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
