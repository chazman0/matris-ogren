# -*- coding: utf-8 -*-
"""
matris_ogren — Sonlu Elemanlar dersi için adım adım matris hesaplayıcı
=====================================================================

Her işlem üç şey gösterir:
  1) 📘 Kural / tanım   : kısa ders notu
  2) ✏️  Adım adım hesap : el ile nasıl yapılır (LaTeX ile)
  3) 🐍 Python ile       : aynı işin numpy / sympy kodu ve GERÇEK çıktısı

Girdi biçimleri (hepsi aynı matrisi verir):
  "1 2; 3 4"            satırlar ';' (veya satır sonu) ile, elemanlar boşluk ya da virgülle
  "[[1,2],[3,4]]"       Python listesi yazımı
  [[1, 2], [3, 4]]      Python listesi
  numpy dizisi, sympy Matrix, ya da bu modülün döndürdüğü Sonuc nesnesi

Elemanlar: tam sayı (3), ondalık (2.5 → kesin 5/2 olarak saklanır), kesir (1/3),
sembolik ifade (E*A/L, 2*E*I/L^3, sqrt(2)/2, sin(30*pi/180)).
Sembolik ifadelerde boşluk kullanmayın ("E*A/L") ya da elemanları virgülle ayırın.

Kullanım:
  import matris_ogren as mo
  mo.carp("1 2; 3 4", "5 6; 7 8")        # çarpım, adım adım
  mo.coz("2 1; 1 3", "3; 5")             # A x = b çözümü (Gauss eliminasyonu)
  mo.determinant("2 1 0; 1 3 1; 0 1 4")
  mo.ters("4 7; 2 6")
  mo.transpoz("1 2 3; 4 5 6")
  mo.yardim()                            # tüm fonksiyonların listesi

Tüm fonksiyonlar bir `Sonuc` nesnesi döndürür: `.deger` (sympy sonucu), `.anlatim`
(adımlar), `.python_kodu`, `.python_ciktisi`. Sonuc nesnesi doğrudan başka bir
fonksiyona girdi olarak verilebilir:  C = mo.carp(A, B); mo.transpoz(C)
"""
from __future__ import annotations

import ast
import contextlib
import functools
import html as _html
import io
import keyword
import math
import re
from dataclasses import dataclass, field
from typing import Any, Sequence

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    parse_expr,
    rationalize,
    standard_transformations,
)

try:  # numpy Colab'da hazır gelir; yoksa yalnız sympy kodu gösterilir
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:  # IPython yoksa (düz terminal) metin olarak yazdırılır
    from IPython import get_ipython  # type: ignore
    from IPython.display import HTML, Markdown, Math, display  # type: ignore
except ImportError:  # pragma: no cover
    get_ipython = None
    HTML = Markdown = Math = display = None


def _ipython_kabugu_var_mi() -> bool:
    """Gerçek bir IPython kabuğunda (Jupyter / Colab / ipython) mıyız?

    IPython kurulu olsa bile düz terminalde ``display()`` zengin çıktıyı değil
    ``<IPython.core.display.Markdown object>`` yazısını basar; bu yüzden yalnız
    çalışan bir kabuk varsa zengin gösterim kullanılır."""
    if get_ipython is None or display is None:
        return False
    try:
        return get_ipython() is not None
    except Exception:  # noqa: BLE001  # pragma: no cover
        return False


_IPYTHON = _ipython_kabugu_var_mi()

__all__ = [
    "ayarlar", "ayarla", "yardim", "matris", "Sonuc", "MatrisHatasi",
    "topla", "cikar", "skaler", "carp", "transpoz", "determinant", "ters",
    "rank", "coz", "ozdeger", "iz", "birim", "sifir",
    "cubuk_eleman", "kiris_eleman", "kafes_eleman", "birlestir", "sinir_kosulu",
    "son_anlatim_al",
]
# Not: `son_anlatim` modül değişkeni (mo.son_anlatim) durur; ancak `from matris_ogren import *`
# onu o anki değerinin bir KOPYASI olarak (None) alırdı. Güncel değer için `son_anlatim_al()`.

__version__ = "1.3.0"


# ============================================================================
# Ayarlar
# ============================================================================
@dataclass
class Ayarlar:
    """Gösterim ayarları (hesap her zaman kesin/sembolik yapılır)."""

    ondalik: bool = False       # True → sonuçlar ondalık gösterilir (örn. 0.3333)
    basamak: int = 4            # ondalık gösterimde anlamlı basamak sayısı
    en_fazla_eleman: int = 36   # eleman eleman anlatımda gösterilecek en fazla eleman (6×6)
    python: bool = True         # 🐍 Python kodu ve çıktısı gösterilsin mi
    kural: bool = True          # 📘 Kural kutusu gösterilsin mi
    sema: bool = True           # 🧭 ok şemaları (oklu adım görselleri) gösterilsin mi
    goster: str = "hepsi"       # varsayılan gösterim: hepsi | adimlar | python | sonuc | yok


ayarlar = Ayarlar()


def ayarla(**kw) -> Ayarlar:
    """Ayarları değiştir: mo.ayarla(ondalik=True, basamak=3)

    Geçerli anahtarlar: ondalik, basamak, en_fazla_eleman, python, kural,
    sema (🧭 oklu adım şemaları: mo.ayarla(sema=False) ile kapanır), goster."""
    for k, v in kw.items():
        if not hasattr(ayarlar, k):
            raise MatrisHatasi(f"Bilinmeyen ayar: {k!r}. Geçerli: {list(vars(ayarlar))}")
        setattr(ayarlar, k, v)
    return ayarlar


class MatrisHatasi(ValueError):
    """Kullanıcı girdisi ya da boyut uyuşmazlığı hatası (Türkçe açıklamalı)."""


class _TutarsizSistem(MatrisHatasi):
    """Denklem sistemi tutarsız (çözümü yok); sinir_kosulu bunu 'mesnet yetersiz' diye yorumlar."""


# ============================================================================
# Girdi ayrıştırma
# ============================================================================
# Eleman düzeyinde köşeli parantez yoktur (dış [ ] _metin_ayristir'da soyulur); ';' satır
# ayırıcısıdır, eleman içinde bulunamaz.
_IZINLI = re.compile(r"^[0-9A-Za-z_+\-*/^().,\s]*$")
_SAYI = re.compile(r"^[+-]?\d+(\.\d+)?$|^[+-]?\d+/\d+$|^[+-]?\.\d+$")
_NITELIK = re.compile(r"[A-Za-z_)]\s*\.\s*[A-Za-z_]")          # a.b  /  (x).b  (2.5 ya da .5 değil)
_E_GOSTERIM = re.compile(r"(?<![A-Za-z_])\d+(?:\.\d*)?[eE]([+-]?\d+)")  # 1e-3, 2.1E5
_EN_BUYUK_US = 64        # a^n içinde |n| üst sınırı (hesabın sonsuza uzamasını önler)
_EN_BUYUK_E_USSU = 99    # 1e99'a kadar yazılabilir

# parse_expr için KÜÇÜK bir ad alanı. Dikkat: sympy'nin varsayılan ad alanında
# E = Euler sayısı, I = sanal birim, N = sayısal değerlendirme fonksiyonudur;
# sonlu elemanlarda E (elastisite modülü), I (atalet momenti), N (şekil fonksiyonu)
# sembol olmalıdır. Bu yüzden ad alanını kendimiz kuruyoruz.
# Not: parse_expr eval tabanlıdır; aşağıdaki süzgeç (_ifade_denetle) TAM güvenli bir kum havuzu
# değildir. Amaç, yanlışlıkla yazılan ya da hesabı sonsuza uzatan girdileri anlaşılır bir
# hatayla durdurmaktır (tehdit modeli: kullanıcı kendi defterinde kendi girdisini yazar).
_AD_ALANI: dict[str, Any] = {
    "Symbol": sp.Symbol, "Integer": sp.Integer, "Float": sp.Float, "Rational": sp.Rational,
    "sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "exp": sp.exp,
    "log": sp.log, "ln": sp.log, "pi": sp.pi, "abs": sp.Abs, "Abs": sp.Abs,
}
_DONUSUMLER = standard_transformations + (convert_xor, rationalize)
_TANIMSIZ = (sp.zoo, sp.nan, sp.oo, -sp.oo)


def _tanimli_mi(ifade, kaynak: str):
    """Sıfıra bölme/sonsuz sızmasını (zoo, nan, ∞) hesabın içine girmeden yakala."""
    if ifade.has(*_TANIMSIZ):
        raise MatrisHatasi(
            f"Eleman tanımsız ya da sonsuz: {kaynak} (sıfıra bölme olabilir). Elemanlar sonlu olmalı."
        )
    return ifade


def _skaler_dogrula(ifade, kaynak: str) -> sp.Expr:
    """Okunan tek elemanın sayı/ifade ve sonlu olduğunu doğrula ("1,5" gibi demetleri reddeder)."""
    if not isinstance(ifade, sp.Expr):
        raise MatrisHatasi(f"Eleman bir sayı ya da ifade olmalı: {kaynak}")
    return _tanimli_mi(ifade, kaynak)


def _ifade_denetle(tok: str) -> None:
    """parse_expr'e (eval tabanlı) girmeden önce kaba süzgeç: nitelik/alt çizgili ad, aşırı büyük üs."""
    if "__" in tok or _NITELIK.search(tok):
        raise MatrisHatasi(
            f"Eleman yazımı desteklenmiyor: {tok!r} (nokta yalnız ondalık için kullanılır; ad.nitelik biçimi ve __ad__ yok)."
        )
    for m in _E_GOSTERIM.finditer(tok):
        if abs(int(m.group(1))) > _EN_BUYUK_E_USSU:
            raise MatrisHatasi(f"Üs çok büyük: {tok!r} (10'un kuvveti ±{_EN_BUYUK_E_USSU}'u aşamaz).")
    try:
        agac = ast.parse(tok.replace("^", "**"), mode="eval")
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return  # sözdizimi hatasını parse_expr kendi (Türkçeleştirilmiş) mesajıyla bildirir
    for dugum in ast.walk(agac):
        if not (isinstance(dugum, ast.BinOp) and isinstance(dugum.op, ast.Pow)):
            continue
        for alt in ast.walk(dugum.right):
            if isinstance(alt, ast.BinOp) and isinstance(alt.op, ast.Pow):
                raise MatrisHatasi(f"Üs içinde üs desteklenmiyor: {tok!r}. Önce ara sonucu ayrı hesaplayın.")
            if (
                isinstance(alt, ast.Constant)
                and isinstance(alt.value, (int, float))
                and not isinstance(alt.value, bool)
                and abs(alt.value) > _EN_BUYUK_US
            ):
                raise MatrisHatasi(f"Üs çok büyük: {tok!r} (üs en fazla {_EN_BUYUK_US} olabilir).")


def _skaler_ayristir(tok: str) -> sp.Expr:
    tok = tok.strip()
    if not tok:
        raise MatrisHatasi("Boş eleman.")
    if not _IZINLI.match(tok):
        raise MatrisHatasi(f"Geçersiz karakter içeren eleman: {tok!r}")
    if _SAYI.match(tok):
        try:
            return sp.Rational(tok)  # "2.5" → 5/2 (kesin), "1/3" → 1/3
        except (ZeroDivisionError, ValueError, TypeError):
            raise MatrisHatasi(f"Geçersiz sayı: {tok!r} (paydada sıfır olamaz).") from None
    _ifade_denetle(tok)
    try:
        expr = parse_expr(tok, global_dict=dict(_AD_ALANI), transformations=_DONUSUMLER)
    except NameError:
        raise MatrisHatasi(
            f"Desteklenmeyen işlev: {tok!r}. Kullanılabilenler: sqrt, sin, cos, tan, exp, log, ln, abs "
            "(sabit: pi). Dereceyi radyana çevirmek için: sin(30*pi/180)."
        ) from None
    except Exception as e:  # noqa: BLE001
        raise MatrisHatasi(f"Eleman anlaşılamadı: {tok!r} ({e})") from e
    return _skaler_dogrula(sp.sympify(expr), repr(tok))


def skaler_oku(x) -> sp.Expr:
    """Tek bir sayı/ifade oku (string, int, float, sympy)."""
    if isinstance(x, str):
        return _skaler_ayristir(x)
    if isinstance(x, bool):
        return sp.Integer(int(x))
    if isinstance(x, float):
        if not math.isfinite(x):
            raise MatrisHatasi(f"Eleman sonlu bir sayı olmalı: {x!r} (nan/inf kabul edilmez).")
        return sp.Rational(repr(x))
    if isinstance(x, int):
        return sp.Integer(x)
    if np is not None and isinstance(x, np.generic):
        return skaler_oku(x.item())
    return _skaler_dogrula(sp.sympify(x), repr(x))


def _metin_ayristir(s: str) -> list[list[sp.Expr]]:
    s = s.strip()
    if not s:
        raise MatrisHatasi("Boş matris girdisi.")
    if s.startswith("["):
        ic = s.strip()
        ic = re.sub(r"^\[\s*\[?", "", ic)
        ic = re.sub(r"\]?\s*\]$", "", ic)
        ic = re.sub(r"\]\s*,\s*\[", ";", ic)
        s = ic
    satirlar = [r for r in re.split(r"[;\n]", s) if r.strip()]
    veri = []
    for r in satirlar:
        r = r.strip()
        parcalar = [t for t in r.split(",")] if "," in r else re.split(r"\s+", r)
        parcalar = [t.strip() for t in parcalar if t.strip()]
        veri.append([_skaler_ayristir(t) for t in parcalar])
    genislikler = {len(r) for r in veri}
    if len(genislikler) != 1:
        raise MatrisHatasi(
            f"Satırların eleman sayıları farklı: {[len(r) for r in veri]}. Her satırda aynı sayıda eleman olmalı."
        )
    return veri


def matris(girdi, ad: str | None = None) -> sp.Matrix:
    """Her türlü girdiyi sympy Matrix'e çevir. Vektör (düz liste) → sütun vektörü."""
    if isinstance(girdi, Sonuc):
        girdi = girdi.deger
    if isinstance(girdi, sp.MatrixBase):
        M = _tanimli_mi(sp.Matrix(girdi), "sympy matrisinin bir elemanı")
    elif isinstance(girdi, str):
        M = sp.Matrix(_metin_ayristir(girdi))
    elif np is not None and isinstance(girdi, np.ndarray):
        if girdi.ndim == 1:
            M = sp.Matrix([[skaler_oku(v)] for v in girdi.tolist()])
        else:
            M = sp.Matrix([[skaler_oku(v) for v in row] for row in girdi.tolist()])
    elif isinstance(girdi, (list, tuple)):
        if len(girdi) == 0:
            raise MatrisHatasi("Boş liste.")
        if all(not isinstance(r, (list, tuple)) for r in girdi):
            M = sp.Matrix([[skaler_oku(v)] for v in girdi])  # düz liste → sütun vektörü
        else:
            M = sp.Matrix([[skaler_oku(v) for v in r] for r in girdi])
    elif isinstance(girdi, (int, float, sp.Expr)):
        M = sp.Matrix([[skaler_oku(girdi)]])
    else:
        raise MatrisHatasi(f"Matris olarak anlaşılamayan girdi: {type(girdi).__name__}")
    if M.rows == 0 or M.cols == 0:
        raise MatrisHatasi("Boş matris.")
    return M


# ============================================================================
# LaTeX biçimlendirme
# ============================================================================
def _ondalik_latex(x: sp.Expr) -> str:
    f = float(x)
    if f == 0:
        return "0"
    s = f"{f:.{ayarlar.basamak}g}"
    if "e" in s:
        m, e = s.split("e")
        return rf"{m}\times 10^{{{int(e)}}}"
    return s


def L(x) -> str:
    """Skaler → LaTeX (ayarlara göre kesir ya da ondalık)."""
    x = sp.sympify(x)
    if ayarlar.ondalik and x.is_number and x.is_real:
        return _ondalik_latex(x)
    return sp.latex(x)


def Lp(x) -> str:
    """Skaler → gerekirse parantezli LaTeX (çarpım içinde kullanmak için)."""
    s = L(x)
    x = sp.sympify(x)
    if s.startswith("-") or x.is_Add:
        return rf"\left({s}\right)"
    return s


def LM(M: sp.MatrixBase, cizgi: int | None = None) -> str:
    """Matris → LaTeX bmatrix. cizgi=k verilirse k. sütundan sonra dikey çizgi ([A|b])."""
    M = sp.Matrix(M)
    satirlar = [" & ".join(L(M[i, j]) for j in range(M.cols)) for i in range(M.rows)]
    govde = r" \\ ".join(satirlar)
    if cizgi is None:
        return rf"\begin{{bmatrix}} {govde} \end{{bmatrix}}"
    kolon = "c" * cizgi + "|" + "c" * (M.cols - cizgi)
    return rf"\left[\begin{{array}}{{{kolon}}} {govde} \end{{array}}\right]"


def B(ad: str) -> str:
    """Matris adı → kalın LaTeX (``K_s`` → K kalın, s alt indis)."""
    kok, alt_cizgi, alt = ad.partition("_")
    if alt_cizgi and kok and alt:
        return rf"\mathbf{{{kok}}}_{{{alt}}}"
    return rf"\mathbf{{{ad}}}"


def _boyut(M: sp.MatrixBase) -> str:
    return rf"{M.rows}\times{M.cols}"


@functools.lru_cache(maxsize=8192)
def _sifir_sayi(x) -> bool:
    """Sembolsüz ama rasyonel olmayan bir sayı (sqrt(5)/2 - 1, CRootOf...) tam sıfır mı?

    sympy otomatik sadeleştirmediği için yapısal ``x == 0`` yanlış "sıfır değil" der
    (ör. (1+sqrt(2))**2 - 3 - 2*sqrt(2)); sıfırı pivot sanmak 1/0 → nan üretir.
    Önce hızlı sayısal eleme, sonra kesin sadeleştirme, o da karar veremezse
    yüksek duyarlıklı sayısal karar kullanılır."""
    try:
        buyukluk = float(abs(x.evalf(30)))
    except (TypeError, ValueError, ArithmeticError):  # nan, karmaşık kalıntı vb.
        buyukluk = None
    if buyukluk is not None and buyukluk == buyukluk and buyukluk > 1e-20:
        return False
    try:
        s = sp.simplify(x)
    except Exception:  # noqa: BLE001
        s = x
    if s == 0 or s.is_zero is True:
        return True
    try:
        return bool(abs(x.evalf(120)) < sp.Float("1e-80"))
    except (TypeError, ValueError, ArithmeticError):
        return False


def _sifir(x) -> bool:
    """x tam olarak sıfır mı? Rasyonel için kesin; irrasyonel sayı ve sembolik ifade için sadeleştirerek."""
    x = sp.sympify(x)
    if x.is_Number:
        return x == 0
    if x.is_number:
        return _sifir_sayi(x)
    s = sp.simplify(x)
    return s == 0 or s.is_zero is True


@functools.lru_cache(maxsize=8192)
def _sade_sayi(x):
    """Sembolsüz irrasyonel sayıyı kanonik biçime yaklaştır: payda kök içermesin, gerçek sıfır 0 olsun."""
    if x.is_Number or x.has(sp.CRootOf):
        return x
    try:
        y = sp.radsimp(sp.expand(x))
    except Exception:  # noqa: BLE001
        return x
    if y.is_Number:
        return y
    if _sifir_sayi(y):
        return sp.S.Zero
    return y


def _sade(M):
    """Sonuçları sadeleştir. Rasyonel matrislerde hızlı geçer; sembolik ifadelere simplify,
    sembolsüz irrasyonel sayılara (kök içeren) radsimp uygulanır."""
    if isinstance(M, sp.MatrixBase):
        if M.free_symbols:
            return M.applyfunc(sp.simplify)
        if all(e.is_Rational for e in M):
            return M
        return M.applyfunc(_sade_sayi)
    M = sp.sympify(M)
    if M.free_symbols:
        return sp.simplify(M)
    return M if M.is_Rational else _sade_sayi(M)


def _esit(X, Y) -> bool:
    X, Y = sp.sympify(X), sp.sympify(Y)
    if isinstance(X, sp.MatrixBase) or isinstance(Y, sp.MatrixBase):
        if not (isinstance(X, sp.MatrixBase) and isinstance(Y, sp.MatrixBase)):
            return False
        if X.shape != Y.shape:
            return False
        return all(
            X[i, j] == Y[i, j] or _sifir(X[i, j] - Y[i, j])
            for i in range(X.rows)
            for j in range(X.cols)
        )
    return X == Y or _sifir(X - Y)


# ============================================================================
# 🧭 Ok şemaları: matris üstünde işlem sırasını gösteren adım adım SVG kareleri
# ============================================================================
_SEMA_ALT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_SEMA_UST = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")
_SEMA_AILE = {  # aile → (dolgu, çizgi); PWA'nın --sema-* değişkenleri yoksa yazılı renkler kullanılır
    "a": ("var(--sema-a-bg,rgba(59,130,246,.14))", "var(--sema-a,#3b82f6)"),     # kaynak satır (mavi)
    "b": ("var(--sema-b-bg,rgba(245,158,11,.16))", "var(--sema-b,#f59e0b)"),     # sütun / ikinci işlenen (amber)
    "c": ("var(--sema-c-bg,rgba(16,185,129,.16))", "var(--sema-c,#10b981)"),     # sonuç (yeşil)
    "sil": ("var(--sema-sil-bg,rgba(239,68,68,.10))", "var(--sema-sil,#ef4444)"),  # üstü çizilen (kırmızı)
}
_SEMA_CIZGI = "var(--sema-cizgi,#94a3b8)"
_SEMA_EN_SATIR, _SEMA_EN_SUTUN, _SEMA_EN_KARE = 6, 12, 40  # panel başına satır/sütun, blok başına kare üst sınırı


def _alt(n) -> str:
    """Sayıyı alt indis rakamlarına çevirir ('12' → '₁₂')."""
    return str(n).translate(_SEMA_ALT)


def _ust(n) -> str:
    """Sayıyı üst indis rakamlarına çevirir ('2' → '²')."""
    return str(n).translate(_SEMA_UST)


def _ind(i: int, j: int | None = None) -> str:
    """1 tabanlı alt indis: (1, 2) → '₁₂'; indis 10 ve üzeriyse virgülle: (10, 2) → '₁₀,₂'."""
    if j is None:
        return _alt(i)
    return _alt(f"{i}{j}") if i < 10 and j < 10 else f"{_alt(i)},{_alt(j)}"


def _sema_metin(x) -> str:
    """Skaleri şema hücresinde görünecek düz metne çevirir (ondalık ayarına uyar; ** → ^, * → ·, eksi gerçek eksi)."""
    if x is None:
        return ""
    x = sp.sympify(x)
    if ayarlar.ondalik and x.is_number and x.is_real:
        f = float(x)
        s = "0" if f == 0 else f"{f:.{ayarlar.basamak}g}"
    else:
        s = str(x).replace("**", "^").replace("*", "·")
    return s.replace("-", "−")


def _sk(x, par: bool = False) -> str:
    """Skaleri alt yazı (caption) metnine çevirir: gerçek eksi işareti; par=True ise negatif/toplam parantezli."""
    x = sp.sympify(x)
    s = _sema_metin(x).replace("-", "−")
    return f"({s})" if par and (s.startswith("−") or x.is_Add or "/" in s) else s


def _n(v: float) -> str:
    """Koordinatı en çok 1 ondalıkla yazar."""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _stil(dolgu: str | None = None, cizgi: str | None = None) -> str:
    """var() içeren renkleri style özniteliğine koyar (sunum özniteliklerinde var() her tarayıcıda, özellikle iOS Safari'de, güvenilmez)."""
    parca = ([f"fill:{dolgu}"] if dolgu else []) + ([f"stroke:{cizgi}"] if cizgi else [])
    return f'style="{";".join(parca)}"' if parca else ""


def _sema_sigar(*matrisler, kare: int = 0) -> bool:
    """Şema çizilsin mi? Ayar açıksa, her matris en çok 6 satır × 12 sütunsa ve kare sayısı sınırı aşmıyorsa."""
    return bool(ayarlar.sema) and kare <= _SEMA_EN_KARE and all(
        M.rows <= _SEMA_EN_SATIR and M.cols <= _SEMA_EN_SUTUN for M in matrisler
    )


class _Sema:
    """Tek bir şema karesini (SVG) kuran küçük, bağımsız çizici (yalnız saf Python).

    Paneller (matrisler) soldan sağa dizilir; vurgu, ok, rozet, bölme ve etiket çağrıları panel numarası
    ve hücre adresiyle verilir; yerleşim ``svg()`` içinde hesaplanır, böylece paneller ortalanır.
    Adres: ``(panel, satır, sütun, yön)`` (+ isteğe bağlı ``dx, dy`` kaydırması). Yön: c ortası, l|r|t|b hücre
    kenarı; L|R panelin soldaki/sağdaki dışı (satır hizasında), T|B üst/alt dışı (sütun hizasında).
    Aile: a mavi (kaynak), b amber (ikinci işlenen), c yeşil (sonuç), sil kırmızı (üstü çizilen).
    Sonuç, CSS olmadan da eksiksiz görünen statik bir SVG'dir; animasyon yalnız uygulama stilinden gelir."""

    SH = 30  # satır yüksekliği (px)

    def __init__(self):
        self._ogeler: list[tuple] = []  # soldan sağa: ("panel", no) | ("isaret", glif)
        self._pan: list[dict] = []
        self._vur: list[dict] = []
        self._bol: list[dict] = []
        self._cizik: list[dict] = []
        self._okl: list[dict] = []
        self._roz: list[dict] = []
        self._etk: list[dict] = []

    # --- ekleme çağrıları -------------------------------------------------
    def panel(self, M, cizgi=None, ust=None, sol=None, parantez=True) -> int:
        """Matris paneli ekler ve panel numarasını döndürür (None hücre = soluk nokta, str olduğu gibi yazılır).

        parantez: True köşeli ayraç, "|" determinant çubukları, False ayraçsız; ust/sol: sütun/satır başlıkları."""
        if isinstance(M, sp.MatrixBase):
            satirlar = [[M[i, j] for j in range(M.cols)] for i in range(M.rows)]
        else:
            satirlar = [list(r) if isinstance(r, (list, tuple)) else [r] for r in M]
        bos = [[x is None for x in r] for r in satirlar]
        hucre = [["" if x is None else (x if isinstance(x, str) else _sema_metin(x)) for x in r] for r in satirlar]
        self._pan.append({
            "h": hucre, "bos": bos, "n": len(hucre), "m": len(hucre[0]) if hucre else 0, "cizgi": cizgi,
            "ust": [str(t) for t in ust] if ust else None, "sol": [str(t) for t in sol] if sol else None,
            "par": parantez, "sil_s": set(), "sil_c": set(), "atla_h": set(),
        })
        self._ogeler.append(("panel", len(self._pan) - 1))
        return len(self._pan) - 1

    def isaret(self, glif: str) -> None:
        """İki panel arasına soluk bir işlem simgesi koyar (×  +  −  =  →)."""
        self._ogeler.append(("isaret", str(glif)))

    def vurgu(self, p, i, j, aile="a", g=0, i2=None, j2=None, kontur=False, ic=0) -> None:
        """Bir hücreyi (ya da (i,j)–(i2,j2) hücre bloğunu) aile renginde kutuyla vurgular; kontur=True yalnız çerçeve."""
        self._vur.append({"p": p, "i": i, "j": j, "i2": i if i2 is None else i2, "j2": j if j2 is None else j2,
                          "aile": aile, "g": g, "kontur": kontur, "ic": ic})

    def satir(self, p, i, aile="a", g=0) -> None:
        """Panelin i. satırının tamamını vurgular."""
        self._vur.append({"p": p, "i": i, "j": 0, "i2": i, "j2": None, "aile": aile, "g": g, "kontur": False, "ic": 0})

    def sutun(self, p, j, aile="b", g=0) -> None:
        """Panelin j. sütununun tamamını vurgular."""
        self._vur.append({"p": p, "i": 0, "j": j, "i2": None, "j2": j, "aile": aile, "g": g, "kontur": False, "ic": 0})

    def sil(self, p, satir=None, sutun=None, g=0, atla=None) -> None:
        """Bir satırı ve/veya sütunu kırmızı vurgu + çizgiyle üstü çizilmiş (silinmiş) gösterir; atla=(i, j) o hücrede çizgi kesilir."""
        P = self._pan[p]
        if atla is not None:
            P["atla_h"].add(tuple(atla))  # bu hücrenin yazısı soluklaşmaz
        if satir is not None:
            P["sil_s"].add(satir)
            self.satir(p, satir, "sil", g)
            self._cizik.append({"p": p, "i": satir, "j": None, "g": g, "atla": atla})
        if sutun is not None:
            P["sil_c"].add(sutun)
            self.sutun(p, sutun, "sil", g)
            self._cizik.append({"p": p, "i": None, "j": sutun, "g": g, "atla": atla})

    def ok(self, a, b, bend=0.0, g=0, aile=None) -> None:
        """a adresinden b adresine ok çizer (ikinci derece Bézier); bend: kirişten sapma px (+ = gidiş yönünün solu)."""
        self._okl.append({"a": a, "b": b, "bend": float(bend), "g": g, "aile": aile})

    def ok_satir(self, p, i, g=0, aile="a") -> None:
        """Vurgulu i. satırın içinde soldan sağa giden alt çizgi oku (okuma sırası)."""
        m = self._pan[p]["m"]
        self.ok((p, i, 0, "l", 5, 10), (p, i, m - 1, "r", -3, 10), 0.0, g, aile)

    def ok_sutun(self, p, j, g=0, aile="b") -> None:
        """Vurgulu j. sütunun sağ kenarında yukarıdan aşağıya inen ok (okuma sırası)."""
        n = self._pan[p]["n"]
        self.ok((p, 0, j, "r", -3, -10), (p, n - 1, j, "r", -3, 10), 0.0, g, aile)

    def rozet(self, p, i, j, metin, yer="ru", g=0, aile="a") -> None:
        """Hücre köşesine sıra numarası / çarpan rozeti koyar; yer: ru lu rb lb c (hücre), L R (panel kenarı)."""
        self._roz.append({"p": p, "i": i, "j": j, "metin": str(metin), "yer": yer, "g": g, "aile": aile})

    def bolme(self, p, satirlar=(), sutunlar=(), etiketler=None, aileler=None, g=0) -> None:
        """Paneli blok bloklara böler: verilen satır/sütun indisinden SONRA kesik çizgi; blok başına etiket ve aile
        (soldan sağa, yukarıdan aşağıya sırayla) verilirse bloklar renkli kutu ve silik büyük adla işaretlenir."""
        self._bol.append({"p": p, "satirlar": list(satirlar), "sutunlar": list(sutunlar),
                          "etiketler": list(etiketler or []), "aileler": list(aileler or []), "g": g})

    def etiket(self, metin, p=None, yer="ust", x=None, y=None, g=0, aile=None, boyut=13, kalin=False,
               dx=0.0, dy=0.0, adres=None, hiza=None) -> None:
        """Serbest yazı koyar: p verilirse panele göre (yer: ust alt sol sag), adres=(panel, i, j, yön[, dx, dy]) verilirse
        o noktaya (hiza: start|middle|end), yoksa (x, y) konumunda; 'K_ff' yazısı alt indis olur."""
        self._etk.append({"metin": str(metin), "p": p, "yer": yer, "x": x, "y": y, "g": g, "aile": aile,
                          "boyut": boyut, "kalin": kalin, "dx": dx, "dy": dy, "adres": adres, "hiza": hiza})

    # --- yerleşim ---------------------------------------------------------
    def _duzen(self):
        yer = []
        for P in self._pan:
            cw = []
            for j in range(P["m"]):
                w = max((len(P["h"][i][j]) for i in range(P["n"])), default=0) * 7.2 + 16
                if P["ust"] and j < len(P["ust"]):
                    w = max(w, len(P["ust"][j]) * 6.6 + 12)
                cw.append(min(96.0, max(36.0, w)))
            solw = (max((len(t) for t in P["sol"]), default=0) * 6.6 + 8) if P["sol"] else 0.0
            yer.append({"cw": cw, "W": sum(cw), "H": P["n"] * self.SH, "solw": solw,
                        "usth": 20.0 if P["ust"] else 0.0})
        x, onceki, isaretler = 0.0, False, []
        for o in self._ogeler:
            if o[0] == "panel":
                d = yer[o[1]]
                if onceki:
                    x += 14
                d["X"] = x + ((d["solw"] + 16) if d["solw"] else 10)
                x = d["X"] + d["W"] + 10
                onceki = True
            else:
                gw = max(34.0, len(o[1]) * 9.0 + 18)
                isaretler.append((o[1], x + gw / 2))
                x += gw
                onceki = False
        orta = max((d["H"] / 2 + d["usth"] for d in yer), default=0.0)
        for d in yer:
            d["Y"] = orta - d["H"] / 2
        return yer, isaretler, orta

    def _nokta(self, yer, a):
        p, i, j, yon = a[0], a[1], a[2], a[3]
        dx, dy = (a[4], a[5]) if len(a) >= 6 else (0.0, 0.0)
        d = yer[p]
        if j is not None:
            xl = d["X"] + sum(d["cw"][:j])
            xr = xl + d["cw"][j]
        else:
            xl, xr = d["X"], d["X"] + d["W"]
        if i is not None:
            yt = d["Y"] + i * self.SH
            yb = yt + self.SH
        else:
            yt, yb = d["Y"], d["Y"] + d["H"]
        xc, yc = (xl + xr) / 2, (yt + yb) / 2
        tablo = {
            "c": (xc, yc), "l": (xl + 2, yc), "r": (xr - 2, yc), "t": (xc, yt + 2), "b": (xc, yb - 2),
            "L": (d["X"] - 14, yc), "R": (d["X"] + d["W"] + 14, yc),
            "T": (xc, d["Y"] - d["usth"] - 8), "B": (xc, d["Y"] + d["H"] + 8),
        }
        x, y = tablo[yon]
        return x + dx, y + dy

    def _kutu(self, yer, p, i, j, i2, j2):
        """(i,j)–(i2,j2) hücrelerinin birleşik dikdörtgeni: (x, y, genişlik, yükseklik); None = sonuna kadar."""
        d, P = yer[p], self._pan[p]
        i2 = P["n"] - 1 if i2 is None else i2
        j2 = P["m"] - 1 if j2 is None else j2
        x = d["X"] + sum(d["cw"][:j])
        return x, d["Y"] + i * self.SH, sum(d["cw"][j:j2 + 1]), (i2 - i + 1) * self.SH

    # --- çizim parçaları ---------------------------------------------------
    @staticmethod
    def _kutu_svg(x, y, w, h, aile, g, kontur=False, ic=0) -> str:
        dolgu, cizgi = _SEMA_AILE[aile]
        boya = f'fill="none" {_stil(None, cizgi)}' if kontur else _stil(dolgu, cizgi)
        return (f'<rect class="vurgu g{g}" rx="6" x="{_n(x + 2 + ic)}" y="{_n(y + 2 + ic)}" '
                f'width="{_n(max(w - 4 - 2 * ic, 2))}" height="{_n(max(h - 4 - 2 * ic, 2))}" '
                f'{boya} stroke-width="1.5"/>')

    @staticmethod
    def _yazi(x, y, metin, anchor="middle", boyut=None, kalin=False, opak=None, genislik=None,
              sinif=None, alt=False, renk="currentColor") -> str:
        oz = ""
        if sinif:
            oz += f' class="{sinif}"'
        oz += f' x="{_n(x)}" y="{_n(y)}" dy=".35em" text-anchor="{anchor}"'
        oz += ' fill="currentColor"' if renk == "currentColor" else f' style="fill:{renk}"'
        if boyut:
            oz += f' font-size="{boyut}"'
        if kalin:
            oz += ' font-weight="600"'
        if opak is not None:
            oz += f' opacity="{opak}"'
        if genislik:
            oz += f' textLength="{_n(genislik)}" lengthAdjust="spacingAndGlyphs"'
        govde = _html.escape(metin, quote=False)
        if alt and "_" in metin:
            on, _, sonra = metin.partition("_")
            alt_kisim, son = sonra, ""
            for k, ch in enumerate(sonra):  # alt indis: ilk harf/rakam dışı karakterde biter
                if not (ch.isalnum()):
                    alt_kisim, son = sonra[:k], sonra[k:]
                    break
            govde = _html.escape(on, quote=False) + f'<tspan dy="3" font-size="9.5">{_html.escape(alt_kisim, quote=False)}</tspan>'
            if son:
                govde += f'<tspan dy="-3">{_html.escape(son, quote=False)}</tspan>'
        return f"<text{oz}>{govde}</text>"

    def _ok_svg(self, yer, o, kapsa):
        x0, y0 = self._nokta(yer, o["a"])
        x1, y1 = self._nokta(yer, o["b"])
        dx, dy = x1 - x0, y1 - y0
        uz = math.hypot(dx, dy)
        if uz < 1e-6:
            return ""
        nx, ny = dy / uz, -dx / uz
        cx, cy = (x0 + x1) / 2 + nx * o["bend"], (y0 + y1) / 2 + ny * o["bend"]
        tx, ty = x1 - cx, y1 - cy
        tu = math.hypot(tx, ty) or 1.0
        tx, ty = tx / tu, ty / tu  # bitiş teğeti (uç − kontrol noktası)
        bx, by = x1 - tx * 7.0, y1 - ty * 7.0
        p1, p2 = (bx - ty * 4.0, by + tx * 4.0), (bx + ty * 4.0, by - tx * 4.0)
        boya = _stil(None, _SEMA_AILE[o["aile"]][1]) if o["aile"] else 'stroke="currentColor"'
        opak = "" if o["aile"] else ' opacity=".7"'
        g = o["g"]
        xm, ym = (x0 + 2 * cx + x1) / 4, (y0 + 2 * cy + y1) / 4  # eğrinin t=½ noktası (görünüm kutusuna dahil)
        kapsa(x0, y0, x1, y1)
        kapsa(xm, ym, xm, ym)
        return (
            f'<path class="ok g{g}" pathLength="1" d="M{_n(x0)} {_n(y0)} Q{_n(cx)} {_n(cy)} {_n(x1)} {_n(y1)}" '
            f'fill="none" {boya} stroke-width="1.8" stroke-linecap="round"{opak}/>'
            f'<polyline class="ok-uc g{g}" points="{_n(p1[0])},{_n(p1[1])} {_n(x1)},{_n(y1)} {_n(p2[0])},{_n(p2[1])}" '
            f'fill="none" {boya} stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"{opak}/>'
        )

    def _rozet_svg(self, yer, o, kapsa):
        d = yer[o["p"]]
        w = 16.0 if len(o["metin"]) <= 1 else len(o["metin"]) * 6.6 + 10
        i, j, yon = o["i"], o["j"], o["yer"]
        if yon in ("L", "R"):
            yc = d["Y"] + (i + 0.5) * self.SH
            cx = d["X"] - 12 - w / 2 if yon == "L" else d["X"] + d["W"] + 12 + w / 2
            cy = yc
        else:
            xl = d["X"] + sum(d["cw"][:j])
            xr = xl + d["cw"][j]
            yt = d["Y"] + i * self.SH
            yb = yt + self.SH
            cx = {"ru": xr - 3, "rb": xr - 3, "lu": xl + 3, "lb": xl + 3}.get(yon, (xl + xr) / 2)
            cy = {"ru": yt + 3, "lu": yt + 3, "rb": yb - 3, "lb": yb - 3}.get(yon, (yt + yb) / 2)
        dolgu, cizgi = _SEMA_AILE[o["aile"]]
        kapsa(cx - w / 2, cy - 8, cx + w / 2, cy + 8)
        sekil = (f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="8"' if w <= 16.5 else
                 f'<rect rx="8" x="{_n(cx - w / 2)}" y="{_n(cy - 8)}" width="{_n(w)}" height="16"')
        return (f'<g class="rozet g{o["g"]}">{sekil} {_stil(dolgu, cizgi)} stroke-width="1.4"/>'
                + self._yazi(cx, cy, o["metin"], boyut=11, kalin=True) + "</g>")

    # --- çıktı ------------------------------------------------------------
    def svg(self, baslik=None) -> str:
        """Kareyi CSS gerektirmeyen, bağımsız bir <svg> dizgesi olarak döndürür (baslik erişilebilirlik adıdır)."""
        yer, isaretler, orta = self._duzen()
        sinir = [math.inf, math.inf, -math.inf, -math.inf]

        def kapsa(x0, y0, x1, y1):
            sinir[0], sinir[1] = min(sinir[0], x0, x1), min(sinir[1], y0, y1)
            sinir[2], sinir[3] = max(sinir[2], x0, x1), max(sinir[3], y0, y1)

        arka, yazi, cizgi, oklar, rozet = [], [], [], [], []
        SH = self.SH
        for p, P in enumerate(self._pan):  # paneller: hücre yazıları, köşeli ayraç, bölme çubuğu, başlıklar
            d = yer[p]
            X, Y, W, H = d["X"], d["Y"], d["W"], d["H"]
            kapsa(X - 10 - (d["solw"] + 6 if d["solw"] else 0), Y - d["usth"], X + W + 10, Y + H)
            for i in range(P["n"]):
                xl = X
                for j in range(P["m"]):
                    xc, yc = xl + d["cw"][j] / 2, Y + (i + 0.5) * SH
                    soluk = ".4" if ((i in P["sil_s"] or j in P["sil_c"]) and (i, j) not in P["atla_h"]) else None
                    if P["bos"][i][j]:
                        yazi.append(self._yazi(xc, yc, "·", opak=".3"))
                    elif P["h"][i][j]:
                        t = P["h"][i][j]
                        gen = d["cw"][j] - 10 if len(t) * 7.2 > d["cw"][j] - 8 else None
                        yazi.append(self._yazi(xc, yc, t, opak=soluk, genislik=gen))
                    xl += d["cw"][j]
            if P["ust"]:
                xl = X
                for j in range(P["m"]):
                    if j < len(P["ust"]) and P["ust"][j]:
                        yazi.append(self._yazi(xl + d["cw"][j] / 2, Y - 10, P["ust"][j], boyut=11, opak=".6"))
                    xl += d["cw"][j]
            if P["sol"]:
                for i in range(P["n"]):
                    if i < len(P["sol"]) and P["sol"][i]:
                        yazi.append(self._yazi(X - 14, Y + (i + 0.5) * SH, P["sol"][i], anchor="end", boyut=11, opak=".6"))
            if P["par"] == "|":  # determinant: dikey çubuklar
                sol, sag = X - 4, X + W + 4
                cizgi.append(f'<path d="M{_n(sol)} {_n(Y + 2)} V{_n(Y + H - 2)} M{_n(sag)} {_n(Y + 2)} V{_n(Y + H - 2)}" '
                             f'fill="none" {_stil(None, _SEMA_CIZGI)} stroke-width="1.6" stroke-linecap="round"/>')
            elif P["par"]:
                sol, sag = X - 4, X + W + 4
                cizgi.append(f'<path d="M{_n(sol + 5)} {_n(Y + 2)} H{_n(sol)} V{_n(Y + H - 2)} H{_n(sol + 5)} '
                             f'M{_n(sag - 5)} {_n(Y + 2)} H{_n(sag)} V{_n(Y + H - 2)} H{_n(sag - 5)}" '
                             f'fill="none" {_stil(None, _SEMA_CIZGI)} stroke-width="1.6" stroke-linecap="round" '
                             f'stroke-linejoin="round"/>')
            if P["cizgi"]:
                bx = X + sum(d["cw"][:P["cizgi"]])
                cizgi.append(f'<line x1="{_n(bx)}" y1="{_n(Y + 2)}" x2="{_n(bx)}" y2="{_n(Y + H - 2)}" '
                             f'{_stil(None, _SEMA_CIZGI)} stroke-width="1.2"/>')
        for glif, ox in isaretler:
            if glif.strip():  # boşluktan oluşan simge çizilmez; yalnız boşluk (ok koridoru) bırakır
                yazi.append(self._yazi(ox, orta, glif, boyut=16, opak=".55"))
            kapsa(ox - 9, orta - 9, ox + 9, orta + 9)
        for o in self._vur:  # vurgu kutuları (yazının arkasında)
            x, y, w, h = self._kutu(yer, o["p"], o["i"], o["j"], o["i2"], o["j2"])
            arka.append(self._kutu_svg(x, y, w, h, o["aile"], o["g"], o["kontur"], o["ic"]))
        for o in self._bol:  # blok bölmeleri: kutular + silik adlar + kesik ayraçlar
            d, P = yer[o["p"]], self._pan[o["p"]]
            n, m = P["n"], P["m"]
            satirlar = sorted({r for r in o["satirlar"] if 0 <= r < n - 1})
            sutunlar = sorted({c for c in o["sutunlar"] if 0 <= c < m - 1})
            r0, r1 = [0] + [r + 1 for r in satirlar], satirlar + [n - 1]
            c0, c1 = [0] + [c + 1 for c in sutunlar], sutunlar + [m - 1]
            k = 0
            for bi in range(len(r0)):
                for bj in range(len(c0)):
                    ad = o["etiketler"][k] if k < len(o["etiketler"]) else None
                    aile = o["aileler"][k] if k < len(o["aileler"]) else None
                    x, y, w, h = self._kutu(yer, o["p"], r0[bi], c0[bj], r1[bi], c1[bj])
                    if aile:
                        arka.append(self._kutu_svg(x, y, w, h, aile, o["g"]))
                    if ad:
                        gorunen = max(len(ad.replace("_", "")), 1)
                        boy = max(9.0, min(18.0, h * 0.5, w / (0.62 * gorunen)))
                        renk = _SEMA_AILE[aile][1] if aile else _SEMA_CIZGI
                        arka.append(self._yazi(x + w / 2, y + h / 2, ad, boyut=_n(boy), kalin=True, opak=".22",
                                               sinif=f"bolme-ad g{o['g']}", alt=True, renk=renk))
                    k += 1
            for r in satirlar:
                yy = d["Y"] + (r + 1) * SH
                arka.append(f'<line class="bolme g{o["g"]}" x1="{_n(d["X"] - 8)}" y1="{_n(yy)}" '
                            f'x2="{_n(d["X"] + d["W"] + 8)}" y2="{_n(yy)}" {_stil(None, _SEMA_CIZGI)} '
                            f'stroke-width="1.4" stroke-dasharray="4 3"/>')
            for c in sutunlar:
                xx = d["X"] + sum(d["cw"][:c + 1])
                arka.append(f'<line class="bolme g{o["g"]}" x1="{_n(xx)}" y1="{_n(d["Y"] - 6)}" '
                            f'x2="{_n(xx)}" y2="{_n(d["Y"] + d["H"] + 6)}" {_stil(None, _SEMA_CIZGI)} '
                            f'stroke-width="1.4" stroke-dasharray="4 3"/>')
            kapsa(d["X"] - 10, d["Y"] - 6, d["X"] + d["W"] + 10, d["Y"] + d["H"] + 6)
        for o in self._cizik:  # üstü çizili satır/sütun çizgileri (atla: o hücrede kesilir)
            d = yer[o["p"]]
            atla = o.get("atla")
            if o["i"] is not None:
                yy = d["Y"] + (o["i"] + 0.5) * SH
                parca = [(d["X"] + 4, d["X"] + d["W"] - 4)]
                if atla is not None and atla[0] == o["i"]:
                    xa = d["X"] + sum(d["cw"][:atla[1]])
                    parca = [(d["X"] + 4, xa + 2), (xa + d["cw"][atla[1]] - 2, d["X"] + d["W"] - 4)]
                cizgiler = [(a, yy, b, yy) for a, b in parca if b > a]
            else:
                xx = d["X"] + sum(d["cw"][:o["j"]]) + d["cw"][o["j"]] / 2
                parca = [(d["Y"] + 4, d["Y"] + d["H"] - 4)]
                if atla is not None and atla[1] == o["j"]:
                    ya = d["Y"] + atla[0] * SH
                    parca = [(d["Y"] + 4, ya + 2), (ya + SH - 2, d["Y"] + d["H"] - 4)]
                cizgiler = [(xx, a, xx, b) for a, b in parca if b > a]
            for x1, y1, x2, y2 in cizgiler:
                cizgi.append(f'<line class="sil-cizgi g{o["g"]}" x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" '
                             f'{_stil(None, _SEMA_AILE["sil"][1])} stroke-width="1.8" stroke-linecap="round"/>')
        for o in self._etk:  # serbest etiketler
            if o["adres"] is not None:
                x, y = self._nokta(yer, o["adres"])
                an = o["hiza"] or "middle"
            elif o["p"] is not None:
                d = yer[o["p"]]
                gx, gy = d["X"] + d["W"] / 2, d["Y"] + d["H"] / 2
                x, y, an = {
                    "ust": (gx, d["Y"] - d["usth"] - 14, "middle"),
                    "alt": (gx, d["Y"] + d["H"] + 16, "middle"),
                    "sol": (d["X"] - 14 - d["solw"], gy, "end"),
                }.get(o["yer"], (d["X"] + d["W"] + 14, gy, "start"))
            else:
                x, y, an = o["x"] or 0.0, o["y"] or 0.0, "middle"
            x, y = x + o["dx"], y + o["dy"]
            gen = len(o["metin"]) * 7.2 * o["boyut"] / 13
            kapsa(x - (gen if an == "end" else gen / 2 if an == "middle" else 0), y - 9,
                  x + (gen if an == "start" else gen / 2 if an == "middle" else 0), y + 9)
            renk = _SEMA_AILE[o["aile"]][1] if o["aile"] else "currentColor"
            yazi.append(self._yazi(x, y, o["metin"], anchor=an, boyut=None if o["boyut"] == 13 else o["boyut"],
                                   kalin=o["kalin"], sinif=f"etiket g{o['g']}", alt=True, renk=renk))
        for o in self._okl:
            oklar.append(self._ok_svg(yer, o, kapsa))
        for o in self._roz:
            rozet.append(self._rozet_svg(yer, o, kapsa))
        if sinir[0] == math.inf:
            sinir = [0.0, 0.0, 10.0, 10.0]
        pay = 10.0
        x0, y0 = sinir[0] - pay, sinir[1] - pay
        w, h = sinir[2] - sinir[0] + 2 * pay, sinir[3] - sinir[1] + 2 * pay
        ad = f' role="img" aria-label="{_html.escape(baslik, quote=True)}"' if baslik else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_n(x0)} {_n(y0)} {_n(w)} {_n(h)}" '
            f'width="{_n(w)}" height="{_n(h)}" style="max-width:100%;height:auto" '
            f'font-family="system-ui,-apple-system,\'Segoe UI\',Roboto,sans-serif" font-size="13"{ad}>'
            + "".join(arka + yazi + cizgi + oklar + rozet) + "</svg>"
        )


def _sema_html(icerik: dict) -> str:
    """Şema bloğunu bağımsız HTML'e çevirir (Colab/Jupyter): kare kare ızgara; 6'dan çok kare varsa kalanı <details> içinde."""
    kareler, ust = icerik["kareler"], icerik["baslik"]
    n = len(kareler)
    yazi = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"

    def sekil(k: int, kare: dict) -> str:
        return (
            '<figure style="margin:0;padding:10px 12px;border:1px solid rgba(128,128,128,.3);'
            'border-radius:12px;max-width:100%;box-sizing:border-box">'
            f'<div style="font:600 11px {yazi};opacity:.6;margin-bottom:4px">Adım {k}/{n}</div>'
            f'{kare["svg"]}'
            f'<figcaption style="font:13px/1.4 {yazi};margin-top:6px">{_html.escape(kare["baslik"])}</figcaption>'
            "</figure>"
        )

    def izgara(basla: int, bitir: int) -> str:
        return ('<div style="display:flex;flex-wrap:wrap;gap:12px">'
                + "".join(sekil(k + 1, kareler[k]) for k in range(basla, bitir)) + "</div>")

    cikti = (f'<div style="margin:.6em 0"><div style="font:600 14px {yazi};margin-bottom:8px">🧭 '
             f'{_html.escape(ust)}</div>' + izgara(0, min(n, 6)))
    if n > 6:
        cikti += (f'<details style="margin-top:10px"><summary style="cursor:pointer;font:13px {yazi}">'
                  f'Kalan {n - 6} adım</summary><div style="margin-top:10px">{izgara(6, n)}</div></details>')
    return cikti + "</div>"


def _sema_not(baslik: str) -> str:
    """Düz metin/Markdown çıktısında şema yerine görünen tek satırlık not (rakam içermez)."""
    return f"*🧭 Ok şeması: {baslik} (adım adım görsel; Colab ve uygulamada çizilir)*"


# --- Şema kareleri: işlem başına bir kare listesi üreten kurucular ---------------------------------------
def _sema_kare(s: _Sema, baslik: str) -> dict:
    """Çizilen kareyi alt yazısıyla tek bir kare sözlüğüne çevirir (alt yazı SVG'nin erişilebilirlik adı da olur)."""
    return {"baslik": baslik, "svg": s.svg(baslik)}


def _sema_sat(i: int, n: int) -> int:
    """Satır hizalı okların şerit kayması: orta çizginin üstündeki satırlarda -10, altında ve ortada +10 (işlem simgesine değmez)."""
    return -10 if 2 * i + 1 < n else 10


def _sema_dizi(parcalar, ayrac: str = " + ", en_cok: int = 4) -> str:
    """Parçaları ayraçla birleştirir; en_cok'tan fazlaysa ortası '…' olur (a₁₁·b₁₁ + a₁₂·b₂₁ + … + a₁ₙ·bₙ₁)."""
    parcalar = list(parcalar)
    if len(parcalar) > en_cok:
        parcalar = parcalar[:2] + ["…"] + parcalar[-1:]
    return ayrac.join(parcalar)


def _sema_toplam(degerler) -> str:
    """Terimleri işaretli toplam olarak yazar: ['2', '−6', '3'] → '2 − 6 + 3'."""
    s = ""
    for k, t in enumerate(degerler):
        if k == 0:
            s = t
        elif t.startswith("−"):
            s += " − " + t[1:]
        else:
            s += " + " + t
    return s


def _sema_eleman(ad: str, i: int, j: int) -> str:
    """Alt yazıdaki eleman simgesi (0 tabanlı i, j): tek harfli ad küçülür ('A', 0, 1 → 'a₁₂'), diğer adlar olduğu gibi kalır."""
    return f"{ad.lower() if len(ad) == 1 and ad.isalpha() else ad}{_ind(i + 1, j + 1)}"


def _sema_dolan(C, i: int, j: int) -> list[list]:
    """Sonuç matrisinin (i, j) hücresine kadar dolmuş hâli; sonrası None (soluk nokta)."""
    return [[C[r, k] if (r, k) <= (i, j) else None for k in range(C.cols)] for r in range(C.rows)]


def _sema_carp(MA, MB, C, a: str, b: str, c: str) -> list[dict]:
    """Matris çarpımı: sonuç elemanı başına bir kare; A'nın satırı ile B'nin sütunu sırayla eşlenir, C kademeli dolar."""
    n, kareler = MA.cols, []
    for i in range(MA.rows):
        for j in range(MB.cols):
            s = _Sema()
            pa = s.panel(MA)
            s.isaret("×")
            pb = s.panel(MB)
            s.isaret("=")
            pc = s.panel(_sema_dolan(C, i, j))
            for p, ad in ((pa, a), (pb, b), (pc, c)):
                s.etiket(ad, p, "ust")
            s.satir(pa, i, "a", 0)
            s.sutun(pb, j, "b", 0)
            if n > 1:
                s.ok_satir(pa, i, 1, "a")
                s.ok_sutun(pb, j, 1, "b")
                for k in range(n):
                    s.rozet(pa, i, k, k + 1, "ru", 2, "a")
                    s.rozet(pb, k, j, k + 1, "lu", 2, "b")
            if C.cols > 1:
                s.vurgu(pc, i, 0, "a", 2, i, C.cols - 1, True)
            if C.rows > 1:
                s.vurgu(pc, 0, j, "b", 2, C.rows - 1, j, True)
            s.vurgu(pc, i, j, "c", 3)
            s.rozet(pc, i, j, "Σ", "lu", 3, "c")
            terim = [f"{_sema_eleman(a, i, k)}·{_sema_eleman(b, k, j)}" for k in range(n)]
            sayi = [f"{_sk(MA[i, k], True)}·{_sk(MB[k, j], True)}" for k in range(n)]
            kareler.append(_sema_kare(
                s, f"{_sema_eleman(c, i, j)} = {_sema_dizi(terim)} = {_sema_dizi(sayi)} = {_sk(C[i, j])}"))
    return kareler


def _sema_topla(MA, MB, C, a: str, b: str, c: str, isaret: str) -> list[dict]:
    """Toplama/çıkarma: konum başına bir kare; aynı konumdaki a, b, c hücreleri aynı satır hizasında bir zincirle bağlanır."""
    gl, kareler = ("+" if isaret == "+" else "−"), []
    for i in range(MA.rows):
        for j in range(MA.cols):
            s = _Sema()
            pa = s.panel(MA)
            s.isaret(gl)
            pb = s.panel(MB)
            s.isaret("=")
            pc = s.panel(_sema_dolan(C, i, j))
            for p, ad in ((pa, a), (pb, b), (pc, c)):
                s.etiket(ad, p, "ust")
            dy = _sema_sat(i, MA.rows)
            s.vurgu(pa, i, j, "a", 0)
            s.ok((pa, i, j, "r", 0, dy), (pb, i, j, "l", 0, dy), 0.0, 1, "a")
            s.vurgu(pb, i, j, "b", 1)
            s.ok((pb, i, j, "r", 0, dy), (pc, i, j, "l", 0, dy), 0.0, 2, "b")
            s.vurgu(pc, i, j, "c", 3)
            kareler.append(_sema_kare(
                s, f"{_sema_eleman(c, i, j)} = {_sema_eleman(a, i, j)} {gl} {_sema_eleman(b, i, j)} = "
                   f"{_sk(MA[i, j])} {gl} {_sk(MB[i, j], True)} = {_sk(C[i, j])}"))
    return kareler


def _sema_skaler(kk, MA, C, a: str, c: str) -> list[dict]:
    """Skalerle çarpma: eleman başına bir kare; k her elemanla çarpılıp aynı konuma yazılır."""
    kareler = []
    for i in range(MA.rows):
        for j in range(MA.cols):
            s = _Sema()
            pk = s.panel([[kk]], parantez=False)
            s.isaret("×")
            pa = s.panel(MA)
            s.isaret("=")
            pc = s.panel(_sema_dolan(C, i, j))
            for p, ad in ((pk, "k"), (pa, a), (pc, c)):
                s.etiket(ad, p, "ust")
            dy = _sema_sat(i, MA.rows)
            s.vurgu(pk, 0, 0, "b", 0)
            s.vurgu(pa, i, j, "a", 1)
            s.ok((pa, i, j, "r", 0, dy), (pc, i, j, "l", 0, dy), 0.0, 2, "a")
            s.vurgu(pc, i, j, "c", 3)
            kareler.append(_sema_kare(
                s, f"{_sema_eleman(c, i, j)} = k·{_sema_eleman(a, i, j)} = {_sk(kk, True)}·{_sk(MA[i, j], True)} "
                   f"= {_sk(C[i, j])}"))
    return kareler


def _sema_transpoz(MA, T, a: str) -> list[dict]:
    """Transpoz: satır başına bir kare; A'nın i. satırı soldan sağa okunur, Aᵀ'nin i. sütununa yukarıdan aşağıya yazılır."""
    kareler = []
    for i in range(MA.rows):
        s = _Sema()
        pa = s.panel(MA)
        s.isaret("→")
        pt = s.panel([[T[r, k] if k <= i else None for k in range(T.cols)] for r in range(T.rows)])
        s.etiket(a, pa, "ust")
        s.etiket(f"{a}ᵀ", pt, "ust")
        s.satir(pa, i, "a", 0)
        if MA.cols > 1:
            s.ok_satir(pa, i, 1, "a")
        s.sutun(pt, i, "c", 2)
        if T.rows > 1:
            s.ok_sutun(pt, i, 3, "c")
        kareler.append(_sema_kare(
            s, f"{i + 1}. satır, {i + 1}. sütun olur: " + ", ".join(_sk(MA[i, j]) for j in range(MA.cols))))
    return kareler


def _sema_iz(MA, a: str) -> list[dict]:
    """İz: köşegen eleman başına bir kare; köşegen oklarla izlenir, ara toplam sağdaki kutuda büyür."""
    kareler, kismi = [], sp.Integer(0)
    for k in range(MA.rows):
        kismi = _sade(kismi + MA[k, k])
        s = _Sema()
        pa = s.panel(MA)
        s.isaret("→")
        pr = s.panel([[kismi]], parantez=False)
        s.etiket(a, pa, "ust")
        s.etiket("iz", pr, "ust")
        for r in range(k + 1):
            s.vurgu(pa, r, r, "a", 0 if r < k else 2)
            if r:
                s.ok((pa, r - 1, r - 1, "r", -5, 7), (pa, r, r, "l", 5, -7), 0.0, 0 if r < k else 1, "a")
        s.vurgu(pr, 0, 0, "c" if k == MA.rows - 1 else "a", 3)
        simge = [_sema_eleman(a, r, r) for r in range(k + 1)]
        deger = [_sk(MA[r, r]) for r in range(k + 1)]
        baslik = (f"{simge[0]} = {deger[0]}" if k == 0 else
                  f"{'iz' if k == MA.rows - 1 else 'ara toplam'} = {_sema_dizi(simge)} = {_sema_toplam(deger)}"
                  f" = {_sk(kismi)}")
        kareler.append(_sema_kare(s, baslik))
    return kareler


def _sema_det2(M) -> list[dict]:
    """2×2 determinant: üç kare (ana köşegen çarpımı, ters köşegen çarpımı, fark)."""
    d1, d2 = _sade(M[0, 0] * M[1, 1]), _sade(M[0, 1] * M[1, 0])
    d = _sade(d1 - d2)
    kareler = []
    for adim in range(3):
        s = _Sema()
        pa = s.panel(M, parantez="|")
        s.isaret("=")
        pr = s.panel([[(_sk(d1), f"{_sk(d1)} − {_sk(d2, True)}", _sk(d))[adim]]], parantez=False)
        s.vurgu(pa, 0, 0, "a", 0)
        s.vurgu(pa, 1, 1, "a", 0)
        s.ok((pa, 0, 0, "r", -5, 7), (pa, 1, 1, "l", 5, -7), 0.0, 1 if adim == 0 else 0, "a")
        if adim >= 1:
            s.vurgu(pa, 0, 1, "b", 1)
            s.vurgu(pa, 1, 0, "b", 1)
            s.ok((pa, 0, 1, "l", 5, 7), (pa, 1, 0, "r", -5, -7), 0.0, 2, "b")
        s.vurgu(pr, 0, 0, ("a", "b", "c")[adim], 3)
        baslik = (
            f"Ana köşegen: {_sema_eleman('a', 0, 0)}·{_sema_eleman('a', 1, 1)} = "
            f"{_sk(M[0, 0], True)}·{_sk(M[1, 1], True)} = {_sk(d1)}",
            f"Ters köşegen: {_sema_eleman('a', 0, 1)}·{_sema_eleman('a', 1, 0)} = "
            f"{_sk(M[0, 1], True)}·{_sk(M[1, 0], True)} = {_sk(d2)}",
            f"Fark: {_sk(d1)} − {_sk(d2, True)} = {_sk(d)}",
        )[adim]
        kareler.append(_sema_kare(s, baslik))
    return kareler


def _sema_det_kofaktor(M) -> list[dict]:
    """Kofaktör açılımı (ilk satır): terim başına bir kare (satır ve sütun silinir, kalan minör alınır) + toplam karesi."""
    n, kareler, ara, terimler = M.rows, [], sp.Integer(0), []
    for j in range(n):
        minor = M.minor_submatrix(0, j)
        dm = _sade(minor.det())
        isr = 1 if j % 2 == 0 else -1
        terim = _sade(isr * M[0, j] * dm)
        ara = _sade(ara + terim)
        terimler.append(terim)
        s = _Sema()
        pa = s.panel(M, parantez="|")
        s.sil(pa, satir=0, sutun=j, g=0, atla=(0, j))
        s.vurgu(pa, 0, j, "a", 1)
        s.isaret("→")
        pm = s.panel(minor, parantez="|")
        s.etiket(f"M{_ind(1, j + 1)}", pm, "ust")
        s.vurgu(pm, 0, 0, "c", 2, n - 2, n - 2, True)
        s.isaret("⇒")
        pr = s.panel([[ara]], parantez=False)
        s.etiket("toplam", pr, "ust")
        s.vurgu(pr, 0, 0, "a", 3)
        isaret = "+" if isr > 0 else "−"
        kareler.append(_sema_kare(
            s, f"{isaret} {_sema_eleman('a', 0, j)}·M{_ind(1, j + 1)} = {isaret} {_sk(M[0, j], True)}·{_sk(dm, True)}"
               f" = {_sk(terim)}"))
    s = _Sema()
    pa = s.panel(M, parantez="|")
    s.satir(pa, 0, "a", 0)
    s.isaret("=")
    pr = s.panel([[ara]], parantez=False)
    s.vurgu(pr, 0, 0, "c", 2)
    kareler.append(_sema_kare(s, f"det = {_sema_toplam([_sk(t) for t in terimler])} = {_sk(ara)}"))
    return kareler


def _sema_genislik(*matrisler) -> float:
    """Panelin yaklaşık genişliği (px): _Sema'nın sütun genişliği kuralıyla (satır etiketi ve boşluklar hariç)."""
    en = 0.0
    for M in matrisler:
        w = 0.0
        for j in range(M.cols):
            mx = max(len(_sema_metin(M[i, j])) for i in range(M.rows))
            w += min(96.0, max(36.0, mx * 7.2 + 16))
        en = max(en, w)
    return en


def _sema_terim(f, rj: str) -> str:
    """R_i ← R_i − f·R_j işleminin işaretli terimi: f=3 → '−3·R₁', f=−1 → '+R₁', f=1/2 → '−(1/2)·R₁'."""
    f = sp.sympify(f)
    neg = bool(f.could_extract_minus_sign())
    m = _sade(-f if neg else f)
    govde = rj if _esit(m, 1) else f"{_sk(m, True)}·{rj}"
    return ("+" if neg else "−") + govde


def _sema_islem_yazi(k: dict) -> str:
    """Satır işleminin kısa yazılışı: 'R₁ ↔ R₂', 'R₁ ← (1/2)·R₁', 'R₂ ← R₂ − 3·R₁'."""
    ri = f"R{_alt(k['i'] + 1)}"
    if k["tur"] == "degis":
        return f"{ri} ↔ R{_alt(k['j'] + 1)}"
    if k["tur"] == "olcek":
        f = sp.sympify(k["f"])
        return f"{ri} ← −{ri}" if _esit(f, -1) else f"{ri} ← {_sk(f, True)}·{ri}"
    t = _sema_terim(k["f"], f"R{_alt(k['j'] + 1)}")
    return f"{ri} ← {ri} {t[0]} {t[1:]}"


def _sema_eliminasyon(kayit: list[dict], cizgi) -> list[dict]:
    """Satır işlemleri: işlem başına bir kare. Sol kenarda yaylar hangi satırın hangisine etki ettiğini gösterir;
    sığarsa 'önce → sonra' çifti, sığmazsa yalnız 'önce' matrisi çizilir."""
    n = kayit[0]["once"].rows
    en = max(_sema_genislik(k["once"], k["sonra"]) for k in kayit)
    cift = 2 * en + 170 <= 560
    sol = [f"R{_alt(r + 1)}" for r in range(n)]
    kx = -(max(len(t) for t in sol) * 6.6 + 8 + 6)  # satır etiketlerinin solunda yay hattı
    sonek = {"degis": "pivot için satırlar yer değiştirir", "olcek": "pivot 1 yapılır"}
    kareler = []
    for k in kayit:
        i, j, c, tur = k["i"], k["j"], k["c"], k["tur"]
        s = _Sema()
        pb = s.panel(k["once"], cizgi=cizgi, sol=sol)
        if cift:
            s.isaret("→")
            pa = s.panel(k["sonra"], cizgi=cizgi)
            s.etiket("önce", pb, "ust")
            s.etiket("sonra", pa, "ust")
        else:
            pa = pb
        if tur == "degis":
            s.satir(pb, i, "a", 0)
            s.satir(pb, j, "b", 0)
            s.vurgu(pb, i, c, "a", 1, kontur=True, ic=2)
            s.vurgu(pb, j, c, "b", 1, kontur=True, ic=2)
            bend = min(56, 16 + 10 * abs(i - j))
            s.ok((pb, i, None, "L", kx, 0), (pb, j, None, "L", kx, 0), -bend, 1, "a")
            s.ok((pb, j, None, "L", kx, 0), (pb, i, None, "L", kx, 0), bend, 1, "a")
            if cift:
                s.satir(pa, i, "b", 2)
                s.satir(pa, j, "a", 2)
        elif tur == "olcek":
            s.satir(pb, i, "a", 0)
            if k["once"].cols > 1:
                s.ok_satir(pb, i, 1, "a")
            s.vurgu(pb, i, c, "b", 1, kontur=True, ic=2)
            s.satir(pa, i, "c", 2)
            s.rozet(pa, i, 0, "×" + _sk(k["f"], True), "R", 2, "c")
        else:
            s.satir(pb, j, "a", 0)
            s.satir(pb, i, "b", 0)
            s.vurgu(pb, j, c, "a", 1, kontur=True, ic=2)
            s.vurgu(pb, i, c, "b", 1, kontur=True, ic=2)
            bend = min(56, 16 + 10 * abs(i - j))
            s.ok((pb, j, None, "L", kx, 0), (pb, i, None, "L", kx, 0), -bend if j < i else bend, 1, "a")
            s.etiket(_sema_terim(k["f"], f"R{_alt(j + 1)}"), aile="a", g=1, boyut=12, hiza="end",
                     adres=(pb, (i + j) / 2, None, "L", kx - bend / 2 - 5, 0))
            s.satir(pa, i, "c", 2)
            s.vurgu(pa, i, c, "c", 2, kontur=True, ic=2)
        son = sonek.get(tur) or f"{c + 1}. sütun sıfırlanır"
        kareler.append(_sema_kare(s, f"{_sema_islem_yazi(k)} — {son}"))
    return kareler


def _sema_geri_koyma(U, n: int, adimlar: list[dict], ad: str, etk) -> list[dict]:
    """Geri yerine koyma: bilinmeyen başına bir kare; son satırdan başlanır, bilinen x'ler katsayılarıyla düşülür."""
    isim = [f"{ad}{_alt(etk(j))}" for j in range(n)]
    solw = max(len(t) for t in isim) * 6.6 + 8
    B = U.extract(list(range(n)), list(range(n + 1)))
    kareler = []
    for a in adimlar:
        i, Xv = a["i"], a["X"]
        s = _Sema()
        pu = s.panel(B, cizgi=n, ust=isim + ["b"])
        s.isaret("     ")
        px = s.panel([[Xv[j, 0] if j >= i else None] for j in range(n)], sol=isim)
        s.satir(pu, i, "a", 0)
        for _, _, j in a["bil"]:
            s.vurgu(pu, i, j, "b", 1, kontur=True, ic=2)
            s.vurgu(px, j, 0, "b", 1)
        s.vurgu(pu, i, i, "c", 1, kontur=True, ic=2)
        s.vurgu(px, i, 0, "c", 2)
        s.ok((pu, i, None, "R"), (px, i, 0, "L", -(solw + 6), 0), 0.0, 2, "c")
        terim = "".join(f" − {_sk(u, True)}·{_sk(xv, True)}" for u, xv, _ in a["bil"])
        pay = _sk(a["sag"]) + terim
        pivot = _sk(a["piv"], True)
        if _esit(a["piv"], 1):
            ifade = pay
        else:
            ifade = f"({pay})/{pivot}" if terim else f"{pay}/{pivot}"
        yazi = f"{isim[i]} = {ifade}" + (f" = {_sk(a['deger'])}" if ifade != _sk(a["deger"]) else "")
        kareler.append(_sema_kare(s, yazi))
    return kareler


def _sema_birlestir(adimlar: list[dict], n: int, ad: str) -> list[dict]:
    """Global birleştirme: eleman başına bir kare. k⁽ᵉ⁾ satırları global satırlara yayılır; K içinde her elemanın
    katkısı kendi renginde kutu olur, ortak (üst üste gelen) hücrelerde '+' rozeti görünür."""
    solw = len(str(n)) * 6.6 + 8

    def kad(e: int) -> str:
        return "k" + _ust(f"({e + 1})")

    kaps = []
    for a in adimlar:  # her elemanın K'da dolu kıldığı hücreler
        kaps.append({(I - 1, J - 1) for ai, I in enumerate(a["dof"]) for bi, J in enumerate(a["dof"])
                     if not _sifir(a["k"][ai, bi])})
    kareler = []
    for e, a in enumerate(adimlar):
        k, dof, aile = a["k"], a["dof"], "abc"[e % 3]
        s = _Sema()
        pk = s.panel(k, ust=[str(g) for g in dof], sol=[str(g) for g in dof])
        s.isaret(" " * 8)
        pK = s.panel(a["K"], ust=[str(r + 1) for r in range(n)], sol=[str(r + 1) for r in range(n)])
        s.etiket(kad(e), pk, "ust", aile=aile, kalin=True)
        s.etiket(ad, pK, "ust")
        s.vurgu(pk, 0, 0, aile, 0, len(dof) - 1, len(dof) - 1)
        for ai, I in enumerate(dof):
            s.ok((pk, ai, None, "R"), (pK, I - 1, None, "L", -(solw + 5), 0), 0.0, 1, aile)
        for e2 in range(e + 1):  # K'daki katkı kutuları: önceki elemanlar çerçeve, şimdiki dolgu; üst üste gelenler içe girer
            for (r, c) in sorted(kaps[e2]):
                kat = sum(1 for e3 in range(e2) if (r, c) in kaps[e3])
                s.vurgu(pK, r, c, "abc"[e2 % 3], 2 if e2 == e else 0, kontur=e2 < e, ic=3 * min(kat, 2))
        ortak = sorted(c for c in kaps[e] if any(c in kaps[e3] for e3 in range(e)))
        for (r, c) in ortak:
            s.rozet(pK, r, c, "+", "ru", 3, aile)
        liste = list(range(max(0, e - 5), e + 1))  # alt gösterge (en çok altı eleman)
        for sira, e2 in enumerate(liste):
            s.etiket(kad(e2), aile="abc"[e2 % 3], kalin=e2 == e, boyut=12, g=3,
                     adres=(pK, n - 1, None, "B", (sira - (len(liste) - 1) / 2) * 40, 8))
        onceki = adimlar[e - 1]["K"] if e else sp.zeros(n, n)
        parca = []
        for (r, c) in ortak[:2]:
            yeni = a["K"][r, c]
            parca.append(f"{ad}{_ind(r + 1, c + 1)} = {_sk(onceki[r, c])} + {_sk(_sade(yeni - onceki[r, c]), True)}"
                         f" = {_sk(yeni)}")
        yazi = f"{kad(e)}: serbestlik {', '.join(map(str, dof))} → {ad} matrisine eklenir"
        if parca:
            yazi += "; ortak " + "; ".join(parca) + (" …" if len(ortak) > 2 else "")
        kareler.append(_sema_kare(s, yazi))
    return kareler


def _sema_mesnet_bolum(MK, MF, serbest: list[int], sabit: list[int], kad: str, fad: str, bil: str) -> list[dict]:
    """Mesnet bölümleme: (gerekirse) serbest | mesnet sıralaması, dört bloğa bölünmüş K u = F ve indirgenmiş sistem.
    Burada f = serbest, s = mesnet (tutulu); motorun metnindeki 'K_s' ise indirgenmiş serbest sistemin adıdır."""
    n, nf, ns = MK.rows, len(serbest), len(sabit)
    kc, fc, bu = kad.replace("_", ""), fad.replace("_", ""), bil.replace("_", "")
    sira = serbest + sabit
    ad_f = lambda i: f"{bu}{_alt(i)}"  # noqa: E731
    kareler = []
    if sira != list(range(1, n + 1)):  # mesnet SD'ler sonda değilse önce yeniden sırala
        s = _Sema()
        p1 = s.panel([[ad_f(i)] for i in range(1, n + 1)])
        s.isaret(" " * 8)
        p2 = s.panel([[ad_f(i)] for i in sira])
        s.etiket("özgün", p1, "ust")
        s.etiket("yeni sıra", p2, "ust")
        for i in range(1, n + 1):
            aile = "c" if i in serbest else "sil"
            r = sira.index(i)
            s.satir(p1, i - 1, aile, 0)
            s.satir(p2, r, aile, 1)
            s.ok((p1, i - 1, None, "R"), (p2, r, None, "L"), 0.0, 1, aile)
        s.bolme(p2, [nf - 1], (), (), (), 2)
        s.etiket("serbest", aile="c", g=2, hiza="start", adres=(p2, (nf - 1) / 2, None, "R", 6, 0))
        s.etiket("mesnet", aile="sil", g=2, hiza="start", adres=(p2, nf + (ns - 1) / 2, None, "R", 6, 0))
        kareler.append(_sema_kare(
            s, "Sıralama: serbest " + ",".join(_alt(i) for i in serbest) + " | mesnet " + ",".join(_alt(i) for i in sabit)))
    ix = [i - 1 for i in sira]
    Kp, Fp = MK.extract(ix, ix), MF.extract(ix, [0])
    s = _Sema()  # bölümlenmiş sistem
    pK = s.panel(Kp)
    s.isaret("×")
    pu = s.panel([[ad_f(i)] if i in serbest else ["0"] for i in sira])
    s.isaret("=")
    pF = s.panel(Fp)
    s.etiket(kc, pK, "ust")
    s.etiket(bu, pu, "ust")
    s.etiket(fc, pF, "ust")
    s.bolme(pK, [nf - 1], [nf - 1], [f"{kc}_ff", f"{kc}_fs", f"{kc}_sf", f"{kc}_ss"], ["c", "b", "b", "sil"], 0)
    s.bolme(pu, [nf - 1], (), [f"{bu}_f", f"{bu}_s"], ["c", "sil"], 1)
    s.bolme(pF, [nf - 1], (), [f"{fc}_f", f"{fc}_s"], ["c", "sil"], 2)
    kareler.append(_sema_kare(
        s, f"Bölümleme (f = serbest, s = mesnet): {kc}_ff·{bu}_f + {kc}_fs·{bu}_s = {fc}_f ve {bu}_s = 0"))
    s = _Sema()  # indirgenmiş sistem
    pK = s.panel(Kp.extract(list(range(nf)), list(range(nf))))
    s.isaret("×")
    pu = s.panel([[ad_f(i)] for i in serbest])
    s.isaret("=")
    pF = s.panel(Fp.extract(list(range(nf)), [0]))
    s.etiket(f"{kc}_ff", pK, "ust", aile="c", kalin=True)
    s.etiket(f"{bu}_f", pu, "ust", aile="c", kalin=True)
    s.etiket(f"{fc}_f", pF, "ust", aile="c", kalin=True)
    for p, m in ((pK, nf), (pu, 1), (pF, 1)):
        s.vurgu(p, 0, 0, "c", 0, nf - 1, m - 1)
    kareler.append(_sema_kare(s, f"İndirgenmiş sistem: {kc}_ff·{bu}_f = {fc}_f (mesnet satır ve sütunları atıldı)"))
    return kareler


def _sema_mesnet_tepki(MK, u, MF, R, sabit: list[int], kad: str, fad: str, bil: str, rad: str) -> list[dict]:
    """Mesnet tepkileri: K × u − F = R tek karede; tutulu satırlar amber, serbest satırlarda sonuç 0 olur."""
    n = MK.rows
    s = _Sema()
    pK = s.panel(MK)
    s.isaret("×")
    pu = s.panel(u)
    s.isaret("−")
    pF = s.panel(MF)
    s.isaret("=")
    pR = s.panel(R)
    for p, ad in ((pK, kad), (pu, bil), (pF, fad), (pR, rad)):
        s.etiket(ad, p, "ust")
    for i in range(1, n + 1):
        mesnet = i in sabit
        if mesnet:
            s.satir(pK, i - 1, "b", 0)
        s.vurgu(pu, i - 1, 0, "sil" if mesnet else "c", 1)
        s.vurgu(pR, i - 1, 0, "b" if mesnet else "c", 2)
        if mesnet:
            s.etiket("tepki", aile="b", g=2, hiza="start", adres=(pR, i - 1, None, "R", 4, 0))
    kareler = [_sema_kare(
        s, f"{rad} = {kad}·{bil} − {fad}: tutulu SD'lerde ({', '.join(map(str, sabit))}) tepki, serbest SD'lerde 0")]
    return kareler


# ============================================================================
# Anlatım (adımların toplandığı yer) ve gösterim
# ============================================================================
@dataclass
class Anlatim:
    bloklar: list[tuple] = field(default_factory=list)

    # --- blok ekleme ---
    def baslik(self, metin: str, seviye: int = 3):
        self.bloklar.append(("md", "#" * seviye + " " + metin, "adim"))

    def metin(self, md: str):
        self.bloklar.append(("md", md, "adim"))

    def kural(self, md: str):
        self.bloklar.append(("md", "> 📘 **Kural:** " + md.replace("\n", "\n> "), "kural"))

    def uyari(self, md: str):
        self.bloklar.append(("md", "> ⚠️ " + md, "adim"))

    def mat(self, latex: str):
        self.bloklar.append(("math", latex, "adim"))

    def adim(self, md: str, latex: str | None = None):
        self.metin(md)
        if latex:
            self.mat(latex)

    def sonuc(self, latex: str, md: str = ""):
        self.bloklar.append(("md", "> ✅ **Sonuç** " + md, "sonuc"))
        self.bloklar.append(("math", latex, "sonuc"))

    def kod(self, kod: str, cikti: str, baslik: str = "🐍 Python ile"):
        self.bloklar.append(("kod", (baslik, kod, cikti), "python"))

    def sema(self, baslik: str, kareler: list[dict], konum: int | None = None):
        """🧭 Ok şeması bloğu ekler. kareler = [{"baslik": alt yazı, "svg": <svg ...>}, ...] (en çok 40 kare).

        Ayar kapalıysa ya da kare yoksa hiçbir şey eklemez. konum verilirse blok o sıraya sokulur;
        0. blok başlık olarak kaldığı için konum en az 1 olur."""
        if not ayarlar.sema or not kareler:
            return
        blok = ("sema", {"baslik": str(baslik),
                         "kareler": [{"baslik": str(k["baslik"]), "svg": str(k["svg"])}
                                     for k in list(kareler)[:_SEMA_EN_KARE]]}, "sema")
        if konum is None:
            self.bloklar.append(blok)
        else:
            self.bloklar.insert(max(1, int(konum)), blok)

    # --- dışa verme ---
    def markdown(self) -> str:
        parcalar = []
        for tur, icerik, _ in self.bloklar:
            if tur == "md":
                parcalar.append(icerik)
            elif tur == "math":
                parcalar.append("$$" + icerik + "$$")
            elif tur == "sema":
                parcalar.append(_sema_not(icerik["baslik"]))
            elif tur == "kod":
                baslik, kod, cikti = icerik
                parcalar.append(f"**{baslik}**\n\n```python\n{kod}\n```\nÇıktı:\n```text\n{cikti}\n```")
        return "\n\n".join(parcalar)

    def __str__(self) -> str:
        return self.markdown()

    def goster(self, mod: str | bool | None = None):
        mod = ayarlar.goster if mod is None or mod is True else mod
        if mod in (False, "yok", None):
            return
        secim = {
            "hepsi": {"kural", "adim", "sonuc", "python", "sema"},
            "adimlar": {"kural", "adim", "sonuc", "sema"},
            "python": {"python", "sonuc"},
            "sonuc": {"sonuc"},
        }.get(mod)
        if secim is None:
            raise MatrisHatasi(f"goster={mod!r} geçersiz. Seçenekler: hepsi, adimlar, python, sonuc, yok")
        if not ayarlar.python:
            secim = secim - {"python"}
        if not ayarlar.kural:
            secim = secim - {"kural"}
        if not ayarlar.sema:
            secim = secim - {"sema"}
        bloklar = [b for b in self.bloklar if b[2] in secim]
        if _IPYTHON:
            for tur, icerik, _ in bloklar:
                if tur == "md":
                    display(Markdown(icerik))
                elif tur == "math":
                    display(Math(icerik))
                elif tur == "sema":
                    if HTML is not None:
                        display(HTML(_sema_html(icerik)))
                    else:  # pragma: no cover
                        display(Markdown(_sema_not(icerik["baslik"])))
                else:
                    baslik, kod, cikti = icerik
                    display(Markdown(f"**{baslik}**"))
                    display(Markdown(f"```python\n{kod}\n```"))
                    display(Markdown(f"Çıktı:\n```text\n{cikti}\n```"))
        else:
            gecici = Anlatim(bloklar)
            print(gecici.markdown())


son_anlatim: Anlatim | None = None  # en son işlemin anlatımı (testler ve dışa verme için)


def son_anlatim_al() -> Anlatim | None:
    """En son işlemin anlatımını döndürür (`from matris_ogren import *` sonrası da günceldir)."""
    return son_anlatim


class Sonuc:
    """Bir işlemin sonucu: .deger (sympy), .anlatim, .python_kodu, .python_ciktisi, .ad"""

    def __init__(self, deger, anlatim: Anlatim, ad: str | None = None,
                 python_kodu: str = "", python_ciktisi: str = ""):
        self.deger = deger
        self.anlatim = anlatim
        self.ad = ad
        self.python_kodu = python_kodu
        self.python_ciktisi = python_ciktisi

    # IPython bu metodu bulunca kendi gösterimini yapmaz; anlatım zaten gösterildi.
    def _ipython_display_(self):
        return None

    def __repr__(self):
        d = self.deger
        if isinstance(d, sp.MatrixBase):
            return f"<Sonuc {self.ad or ''} {d.rows}x{d.cols}: {d.tolist()}>"
        return f"<Sonuc {self.ad or ''}: {d}>"

    def latex(self) -> str:
        return LM(self.deger) if isinstance(self.deger, sp.MatrixBase) else L(self.deger)

    def markdown(self) -> str:
        return self.anlatim.markdown()

    @property
    def M(self):
        return self.deger

    def __getattr__(self, isim):  # .T, .shape, .det() ... doğrudan sympy nesnesine gider
        if isim.startswith("__") or isim in ("deger", "anlatim", "ad", "python_kodu", "python_ciktisi"):
            raise AttributeError(isim)
        return getattr(self.deger, isim)

    def __getitem__(self, k):
        return self.deger[k]


def _bitir(deger, anl: Anlatim, ad: str | None, goster, kod: str = "", cikti: str = "") -> Sonuc:
    global son_anlatim
    son_anlatim = anl
    anl.goster(goster)
    return Sonuc(deger, anl, ad, kod, cikti)


# ============================================================================
# Python kodu üretimi ve çalıştırma
# ============================================================================
def _py_sayi(x: sp.Expr) -> str:
    x = sp.sympify(x)
    if x.is_Integer:
        return str(int(x))
    if x.is_Rational:
        return f"{x.p}/{x.q}"
    if x.is_number:
        return repr(float(x))
    return sp.pycode(x)


def _np_kodu(ad: str, M: sp.MatrixBase) -> str:
    satirlar = ", ".join("[" + ", ".join(_py_sayi(M[i, j]) for j in range(M.cols)) + "]" for i in range(M.rows))
    return f"{ad} = np.array([{satirlar}], dtype=float)"


def _sp_kodu(ad: str, M: sp.MatrixBase) -> str:
    satirlar = ", ".join("[" + ", ".join(_sp_eleman(M[i, j]) for j in range(M.cols)) + "]" for i in range(M.rows))
    return f"{ad} = sp.Matrix([{satirlar}])"


def _sp_eleman(x: sp.Expr) -> str:
    x = sp.sympify(x)
    if x.is_Integer:
        return str(int(x))
    if x.is_Rational:
        return f"sp.Rational({x.p}, {x.q})"
    return sp.pycode(x).replace("math.", "sp.")


def _sembolik_mi(*Ms) -> bool:
    for M in Ms:
        M = sp.sympify(M)
        if M.free_symbols:
            return True
    return False


def _semboller(*Ms) -> list[sp.Symbol]:
    s = set()
    for M in Ms:
        s |= sp.sympify(M).free_symbols
    return sorted(s, key=lambda t: t.name)


def _kod_baslangic(sembolik: bool, *Ms) -> list[str]:
    if sembolik:
        semb = _semboller(*Ms)
        satirlar = ["import sympy as sp"]
        if semb:
            adlar = " ".join(s.name for s in semb)
            sol = ", ".join(s.name for s in semb)
            satirlar.append(f"{sol} = sp.symbols('{adlar}')")
        return satirlar
    return ["import numpy as np", "np.set_printoptions(precision=4, suppress=True)"]


def _kodu_calistir(kod: str) -> str:
    """Üretilen Python kodunu temiz bir ad alanında çalıştırıp stdout'u döndür.

    Kod ``np.set_printoptions(...)`` çağırır; bu genel (global) bir ayardır. Kullanıcının kendi
    numpy gösterim ayarı bozulmasın diye çalıştırma, ayarları geri yükleyen bir bağlamda yapılır."""
    tampon = io.StringIO()
    alan: dict[str, Any] = {"__name__": "__matris_ogren_kod__"}
    ayar_koru = np.printoptions() if np is not None else contextlib.nullcontext()
    try:
        with ayar_koru, contextlib.redirect_stdout(tampon):
            exec(compile(kod, "<python_kodu>", "exec"), alan)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        tampon.write(f"\n[Hata: {type(e).__name__}: {e}]")
    return tampon.getvalue().rstrip("\n")


def _python_bolumu(anl: Anlatim, satirlar: list[str]) -> tuple[str, str]:
    kod = "\n".join(satirlar)
    cikti = _kodu_calistir(kod)
    anl.kod(kod, cikti if cikti else "(çıktı yok)")
    return kod, cikti


# ============================================================================
# Yardımcılar
# ============================================================================
_HARFLER = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_AYRILMIS_ADLAR = frozenset({"np", "sp", "math"})  # üretilen kodda modül adı olarak kullanılır


def _ad_gecerli_mi(ad) -> bool:
    """ad, üretilen Python kodunda değişken adı olarak kullanılabilir mi?"""
    return (
        isinstance(ad, str) and ad.isidentifier() and not keyword.iskeyword(ad)
        and ad not in _AYRILMIS_ADLAR
    )


def _ad_dogrula(ad, ne: str = "Ad") -> str:
    if not _ad_gecerli_mi(ad):
        raise MatrisHatasi(
            f"{ne} geçerli bir Python adı olmalı (harf, rakam ve _ ; rakamla başlamaz; "
            f"np, sp ve Python anahtar sözcükleri olamaz): {ad!r}"
        )
    return ad


def _serbest_ad(taban: str, yasak) -> str:
    """taban yasaklı değilse aynen; değilse taban_m, taban_m2, ... (kod adı çakışmasını önler)."""
    ad, i = taban, 1
    while ad in yasak:
        ad = f"{taban}_m" if i == 1 else f"{taban}_m{i}"
        i += 1
    return ad


class _KodAdlari:
    """Üretilen Python kodundaki değişken adlarını dağıtır.

    Matris/yardımcı değişken adları kullanıcı sembolleriyle (E, A, L, I, k, P, ...), ``np``/``sp``
    ile ve birbirleriyle çakışmaz; çakışma yoksa istenen ad aynen verilir. (Çakışma olunca matris
    değişkeni ``A_m`` gibi bir ad alır; yoksa ``A = sp.Matrix(...)`` satırı ``A`` sembolünü ezer ve
    sonraki satırlar sessizce yanlış hesaplanırdı.)"""

    def __init__(self, *Ms, ekstra=()):
        self.yasak: set[str] = set(_AYRILMIS_ADLAR) | {s.name for s in _semboller(*Ms)} | set(ekstra)

    def al(self, tercih: str) -> str:
        ad = _serbest_ad(tercih, self.yasak)
        self.yasak.add(ad)
        return ad


def _harf_sec(aday: str, kullanilan) -> str:
    """aday kullanılmıyorsa aday; değilse _HARFLER'de ondan sonraki ilk boş harf (sonra baştan)."""
    if aday not in kullanilan:
        return aday
    bas = _HARFLER.find(aday)
    sira = (_HARFLER[bas + 1:] + _HARFLER[:bas]) if bas >= 0 else _HARFLER
    for h in sira:
        if h not in kullanilan:
            return h
    i = 2
    while f"{aday}{i}" in kullanilan:
        i += 1
    return f"{aday}{i}"


def _sonuc_adi(girdi_adlari, tercih: str = "C") -> str:
    """Sonuç matrisine girdilerden farklı bir ad ver (C varsa D, ...)."""
    return _harf_sec(tercih, set(girdi_adlari))


def _adlar(n: int, adlar: Sequence[str] | None, varsayilan: str | None = None) -> list[str]:
    if adlar:
        adlar = list(adlar)
        if len(adlar) < n:
            raise MatrisHatasi(f"{n} matris için {len(adlar)} ad verildi.")
        adlar = adlar[:n]
        for ad in adlar:
            _ad_dogrula(ad, "Matris adı")
        if len(set(adlar)) < len(adlar):
            raise MatrisHatasi(f"Matris adları birbirinden farklı olmalı: {adlar}")
        return adlar
    if varsayilan:
        return [varsayilan]
    return [_HARFLER[i] for i in range(n)]


def _girdi_adlari(girdiler) -> list[str]:
    """Sonuc nesnelerinin adını korur, diğerlerine harf verir; adlar benzersiz ve geçerlidir
    (topla(carp, carp) gibi aynı adı taşıyan girdilerde ikinci girdi başka bir harf alır)."""
    adlar: list[str | None] = [None] * len(girdiler)
    kullanilan: set[str] = set()
    for i, g in enumerate(girdiler):
        ad = g.ad if isinstance(g, Sonuc) else None
        if ad and _ad_gecerli_mi(ad) and ad not in kullanilan:
            adlar[i] = ad
            kullanilan.add(ad)
    for i in range(len(girdiler)):
        if adlar[i] is None:
            aday = _HARFLER[i] if i < len(_HARFLER) else f"M{i + 1}"
            adlar[i] = _harf_sec(aday, kullanilan)
            kullanilan.add(adlar[i])
    return adlar  # type: ignore[return-value]


def _girdileri_al(girdiler, adlar):
    """Girdileri matrise çevirir; (matrisler, benzersiz geçerli adlar) döndürür."""
    Ms = [matris(g) for g in girdiler]
    if adlar is None:
        return Ms, _girdi_adlari(girdiler)
    return Ms, _adlar(len(Ms), adlar)


def _tutarlilik(bulunan, beklenen, islem: str) -> None:
    """İç tutarlılık denetimi. ``assert`` yerine: ``python -O`` ile kalkmaz, kullanıcıya ham
    AssertionError yerine açıklamalı MatrisHatasi gider."""
    if not _esit(bulunan, beklenen):
        raise MatrisHatasi(f"İç tutarlılık hatası ({islem}); girdiyi sadeleştirip yeniden deneyin.")


def _eleman_listesi_sinirli(n_eleman: int) -> bool:
    return n_eleman <= ayarlar.en_fazla_eleman


def _girdileri_goster(anl: Anlatim, Ms, adlar):
    parcalar = [rf"{B(a)} = {LM(M)}" for a, M in zip(adlar, Ms)]
    anl.mat(r",\qquad ".join(parcalar))


# ============================================================================
# Temel işlemler
# ============================================================================
def birim(n: int) -> sp.Matrix:
    """n×n birim matris I."""
    return sp.eye(n)


def sifir(m: int, n: int | None = None) -> sp.Matrix:
    """m×n sıfır matris."""
    return sp.zeros(m, n if n is not None else m)


def topla(A, B_, *, adlar=None, goster=None) -> Sonuc:
    """A + B: aynı boyuttaki matrislerin eleman eleman toplamı."""
    return _topla_cikar(A, B_, "+", adlar, goster)


def cikar(A, B_, *, adlar=None, goster=None) -> Sonuc:
    """A − B: aynı boyuttaki matrislerin eleman eleman farkı."""
    return _topla_cikar(A, B_, "-", adlar, goster)


def _topla_cikar(A, B_, isaret, adlar, goster) -> Sonuc:
    (MA, MB), (a, b) = _girdileri_al([A, B_], adlar)
    c = _sonuc_adi([a, b])
    anl = Anlatim()
    ad_islem = "Toplama" if isaret == "+" else "Çıkarma"
    anl.baslik(f"{ad_islem}: ${B(a)} {isaret} {B(b)}$")
    anl.kural(
        "İki matris **ancak boyutları aynıysa** toplanır/çıkarılır. İşlem *eleman eleman* yapılır: "
        rf"$c_{{ij}} = a_{{ij}} {isaret} b_{{ij}}$ (aynı konumdaki elemanlar {'toplanır' if isaret == '+' else 'çıkarılır'})."
    )
    _girdileri_goster(anl, [MA, MB], [a, b])
    if MA.shape != MB.shape:
        anl.uyari(rf"Boyutlar farklı: ${B(a)}$ ${_boyut(MA)}$, ${B(b)}$ ${_boyut(MB)}$ → bu işlem **tanımsızdır**.")
        anl.goster(goster)
        raise MatrisHatasi(f"Boyutlar farklı ({MA.rows}x{MA.cols} ve {MB.rows}x{MB.cols}); toplama/çıkarma tanımsız.")
    anl.metin(f"Boyut kontrolü: ikisi de ${_boyut(MA)}$ ✔")
    C = (MA + MB) if isaret == "+" else (MA - MB)
    C = _sade(C)
    if _eleman_listesi_sinirli(MA.rows * MA.cols) and _sema_sigar(MA, MB, kare=MA.rows * MA.cols):
        anl.sema("Aynı konumdaki elemanlar", _sema_topla(MA, MB, C, a, b, c, isaret))
    if _eleman_listesi_sinirli(MA.rows * MA.cols):
        anl.metin("Her eleman ayrı ayrı:")
        satirlar = []
        for i in range(MA.rows):
            for j in range(MA.cols):
                satirlar.append(
                    rf"c_{{{i+1}{j+1}}} &= a_{{{i+1}{j+1}}} {isaret} b_{{{i+1}{j+1}}} = "
                    rf"{L(MA[i, j])} {isaret} {Lp(MB[i, j])} = {L(C[i, j])}"
                )
        anl.mat(r"\begin{aligned}" + r" \\ ".join(satirlar) + r"\end{aligned}")
    else:
        anl.metin(f"Matris büyük ({MA.rows}×{MA.cols}); her eleman için aynı kural uygulanır, örneğin:")
        anl.mat(rf"c_{{11}} = {L(MA[0, 0])} {isaret} {Lp(MB[0, 0])} = {L(C[0, 0])}")
    anl.sonuc(rf"{B(c)} = {B(a)} {isaret} {B(b)} = {LM(C)}")
    # Python
    semb = _sembolik_mi(MA, MB)
    kod = _kod_baslangic(semb, MA, MB)
    yaz = _sp_kodu if semb else _np_kodu
    kn = _KodAdlari(MA, MB)
    ka, kb = kn.al(a), kn.al(b)
    kc = kn.al(c)
    kod += [yaz(ka, MA), yaz(kb, MB), f"{kc} = {ka} {isaret} {kb}", f"print({kc})"]
    k, ck = _python_bolumu(anl, kod)
    # iç tutarlılık
    beklenen = MA + MB if isaret == "+" else MA - MB
    _tutarlilik(C, beklenen, "topla/cikar")
    return _bitir(C, anl, c, goster, k, ck)


def skaler(k, A, *, adlar=None, goster=None) -> Sonuc:
    """k·A: matrisin bir sayı (skaler) ile çarpımı — her eleman k ile çarpılır."""
    (MA,), (a,) = _girdileri_al([A], adlar)
    kk = skaler_oku(k)
    c = _sonuc_adi([a])
    anl = Anlatim()
    anl.baslik(f"Skalerle çarpma: ${L(kk)}\\,{B(a)}$")
    anl.kural(r"Bir matris bir sayı (skaler) ile çarpılırken **her eleman** o sayı ile çarpılır: $(k\mathbf{A})_{ij} = k\,a_{ij}$.")
    if L(kk) == "k":   # k = k gibi totolojik satır yazma
        anl.mat(rf"{B(a)} = {LM(MA)}")
    else:
        anl.mat(rf"k = {L(kk)},\qquad {B(a)} = {LM(MA)}")
    C = _sade(kk * MA)
    if _eleman_listesi_sinirli(MA.rows * MA.cols) and _sema_sigar(MA, kare=MA.rows * MA.cols):
        anl.sema("Her eleman k ile çarpılır", _sema_skaler(kk, MA, C, a, c))
    if _eleman_listesi_sinirli(MA.rows * MA.cols):
        satirlar = [
            rf"c_{{{i+1}{j+1}}} &= {Lp(kk)}\cdot {Lp(MA[i, j])} = {L(C[i, j])}"
            for i in range(MA.rows) for j in range(MA.cols)
        ]
        anl.mat(r"\begin{aligned}" + r" \\ ".join(satirlar) + r"\end{aligned}")
    anl.sonuc(rf"{L(kk)}\,{B(a)} = {LM(C)}")
    semb = _sembolik_mi(MA, kk)
    kod = _kod_baslangic(semb, MA, kk)
    kn = _KodAdlari(MA, kk)
    ka, kkat = kn.al(a), kn.al("kat")
    kc = kn.al(c)
    kod += [(_sp_kodu if semb else _np_kodu)(ka, MA), f"{kkat} = {_sp_eleman(kk) if semb else _py_sayi(kk)}",
            f"{kc} = {kkat} * {ka}", f"print({kc})"]
    kd, ck = _python_bolumu(anl, kod)
    _tutarlilik(C, kk * MA, "skaler")
    return _bitir(C, anl, c, goster, kd, ck)


def carp(*girdiler, adlar=None, goster=None) -> Sonuc:
    """A·B (ya da A·B·C·…): matris çarpımı, her eleman için satır×sütun toplamı gösterilir."""
    if len(girdiler) < 2:
        raise MatrisHatasi("Çarpma için en az iki matris verin: carp(A, B) ya da carp(A, B, C).")
    Ms, adlar_ = _girdileri_al(list(girdiler), adlar)
    anl = Anlatim()
    anl.baslik("Matris çarpımı: $" + "".join(B(a) for a in adlar_) + "$")
    anl.kural(
        r"$\mathbf{A}$ ($m\times n$) ile $\mathbf{B}$ ($n\times p$) çarpılabilmesi için "
        r"**A'nın sütun sayısı = B'nin satır sayısı** olmalıdır; sonuç $m\times p$ olur. "
        r"Sonucun $i$. satır $j$. sütun elemanı, **A'nın $i$. satırı ile B'nin $j$. sütununun** karşılıklı "
        r"çarpımlarının toplamıdır: $c_{ij} = \sum_{l=1}^{n} a_{il}\,b_{lj}$ ($l$ toplam indisidir). "
        r"Genelde $\mathbf{AB} \neq \mathbf{BA}$ (sıra önemlidir)."
    )
    _girdileri_goster(anl, Ms, adlar_)
    if len(Ms) > 2:
        anl.metin("Birden çok matris soldan sağa ikişer ikişer çarpılır: "
                  + "$" + "".join(B(a) for a in adlar_) + " = " + _zincir_gosterimi(adlar_) + "$")
    sol, sol_ad = Ms[0], adlar_[0]
    kullanilan = set(adlar_)
    kod_satirlari = []
    for idx in range(1, len(Ms)):
        sag, sag_ad = Ms[idx], adlar_[idx]
        if len(Ms) == 2:
            sonuc_ad = _sonuc_adi(adlar_)
        else:
            sonuc_ad = _serbest_ad("".join(adlar_[: idx + 1]), kullanilan)
        kullanilan.add(sonuc_ad)
        sol = _ikili_carp(anl, sol, sag, sol_ad, sag_ad, sonuc_ad, goster)
        kod_satirlari.append((sol_ad, sag_ad, sonuc_ad))
        sol_ad = sonuc_ad
    C = sol
    anl.sonuc(rf"{B(sol_ad)} = " + "".join(B(a) for a in adlar_) + f" = {LM(C)}")
    semb = _sembolik_mi(*Ms)
    kod = _kod_baslangic(semb, *Ms)
    yaz = _sp_kodu if semb else _np_kodu
    kn = _KodAdlari(*Ms)
    kodad = {a: kn.al(a) for a in adlar_}
    kod += [yaz(kodad[a], M) for a, M in zip(adlar_, Ms)]
    op = "*" if semb else "@"
    for (x, y, z) in kod_satirlari:
        kodad[z] = kn.al(z)
        kod.append(f"{kodad[z]} = {kodad[x]} {op} {kodad[y]}")
    kod.append(f"print({kodad[sol_ad]})")
    if not semb:
        kod.append("# Not: numpy'da @ matris çarpımıdır; * eleman eleman çarpar (farklı şey!).")
    kd, ck = _python_bolumu(anl, kod)
    beklenen = Ms[0]
    for M in Ms[1:]:
        beklenen = beklenen * M
    _tutarlilik(C, beklenen, "carp")
    return _bitir(C, anl, sol_ad, goster, kd, ck)


def _zincir_gosterimi(adlar_) -> str:
    """Soldan sağa gruplama: (AB)C, ((AB)C)D, ... (LaTeX)."""
    s = B(adlar_[0])
    for idx, a in enumerate(adlar_[1:], start=1):
        s = f"{s}{B(a)}" if idx == 1 else f"({s}){B(a)}"
    return s


def _eleman_simgesi(ad: str, i: int, j: int) -> str:
    """ad adlı matrisin (i, j) elemanının LaTeX simgesi (i, j sıfırdan başlar).

    Tek harfli ad küçük harfle yazılır (A → a_{11}); diğer adlar (AB gibi) (\\mathbf{AB})_{11} olur.
    Böylece ara çarpım ile girdi matrisi aynı a_{ij} simgesini paylaşmaz."""
    if len(ad) == 1 and ad.isalpha():
        return rf"{ad.lower()}_{{{i + 1}{j + 1}}}"
    return rf"({B(ad)})_{{{i + 1}{j + 1}}}"


def _ikili_carp(anl: Anlatim, MA, MB, a, b, c, goster=None, sema: bool = True) -> sp.Matrix:
    if MA.cols != MB.rows:
        anl.uyari(
            rf"${B(a)}$ ${_boyut(MA)}$, ${B(b)}$ ${_boyut(MB)}$: {MA.cols} ≠ {MB.rows} → "
            r"**çarpım tanımsız** (soldakinin sütun sayısı sağdakinin satır sayısına eşit değil)."
        )
        anl.goster(goster)
        raise MatrisHatasi(
            f"{a} ({MA.rows}x{MA.cols}) · {b} ({MB.rows}x{MB.cols}) tanımsız: "
            f"{a} matrisinin sütun sayısı ({MA.cols}) ile {b} matrisinin satır sayısı ({MB.rows}) eşit olmalı."
        )
    anl.metin(
        rf"**{c} = {a}·{b}** — Boyut kontrolü: ${_boyut(MA)}$ · ${_boyut(MB)}$ → iç boyutlar eşit "
        rf"({MA.cols} = {MB.rows}) ✔, sonuç ${MA.rows}\times{MB.cols}$ olur."
    )
    C = sp.zeros(MA.rows, MB.cols)
    n = MA.cols
    satirlar = []
    goster_hepsi = _eleman_listesi_sinirli(MA.rows * MB.cols)
    konum = len(anl.bloklar)  # ok şeması, eleman eleman anlatımdan önce görünsün
    for i in range(MA.rows):
        for j in range(MB.cols):
            terimler = [MA[i, k] * MB[k, j] for k in range(n)]
            deger = _sade(sum(terimler, sp.Integer(0)))
            C[i, j] = deger
            if goster_hepsi:
                sembolik = " + ".join(_eleman_simgesi(a, i, k) + _eleman_simgesi(b, k, j) for k in range(n))
                sayisal = " + ".join(rf"{Lp(MA[i, k])}\cdot {Lp(MB[k, j])}" for k in range(n))
                parca = rf"{_eleman_simgesi(c, i, j)} &= {sembolik} = {sayisal}"
                if n > 1:
                    carpimlar = " + ".join(Lp(_sade(t)) for t in terimler)
                    if carpimlar != L(deger):
                        parca += rf" = {carpimlar}"
                parca += rf" = {L(deger)}"
                satirlar.append(parca)
    if sema and goster_hepsi and _sema_sigar(MA, MB, C, kare=MA.rows * MB.cols):
        anl.sema("Çarpım sırası: satır × sütun", _sema_carp(MA, MB, C, a, b, c), konum)
    if goster_hepsi:
        anl.metin(f"Her eleman için **{a} matrisinin satırı × {b} matrisinin sütunu** (karşılıklı elemanlar çarpılıp toplanır):")
        anl.mat(r"\begin{aligned}" + r" \\ ".join(satirlar) + r"\end{aligned}")
    else:
        anl.metin(f"Sonuç {MA.rows}×{MB.cols} = {MA.rows*MB.cols} elemanlı; örnek olarak ilk eleman:")
        sayisal = " + ".join(rf"{Lp(MA[0, k])}\cdot {Lp(MB[k, 0])}" for k in range(n))
        anl.mat(rf"{_eleman_simgesi(c, 0, 0)} = {sayisal} = {L(C[0, 0])}")
    anl.mat(rf"{B(c)} = {B(a)}{B(b)} = {LM(C)}")
    return C


def transpoz(A, *, adlar=None, goster=None) -> Sonuc:
    """Aᵀ: satırlar sütun, sütunlar satır olur."""
    (MA,), (a,) = _girdileri_al([A], adlar)
    anl = Anlatim()
    anl.baslik(rf"Transpoz: ${B(a)}^T$")
    anl.kural(
        r"Transpoz alınırken **satırlar sütun, sütunlar satır olur**: $(\mathbf{A}^T)_{ij} = a_{ji}$. "
        r"$m\times n$ matrisin transpozu $n\times m$ olur. Özellikler: $(\mathbf{A}^T)^T=\mathbf{A}$, "
        r"$(\mathbf{AB})^T = \mathbf{B}^T\mathbf{A}^T$. $\mathbf{A}^T=\mathbf{A}$ ise matris **simetrik**tir "
        r"(rijitlik matrisleri simetriktir)."
    )
    anl.mat(rf"{B(a)} = {LM(MA)}\quad ({_boyut(MA)})")
    T = MA.T
    if _sema_sigar(MA, T, kare=MA.rows):
        anl.sema("Satırlar sütun olur", _sema_transpoz(MA, T, a))
    satirlar = []
    satir_ayrac = r" \\ "
    for i in range(MA.rows):
        elemanlar = [L(MA[i, j]) for j in range(MA.cols)]
        yatay = " & ".join(elemanlar)
        dikey = satir_ayrac.join(elemanlar)
        satirlar.append(
            rf"\text{{{i+1}. satır }} \begin{{bmatrix}} {yatay} \end{{bmatrix}}"
            rf" &\;\longrightarrow\; \text{{{i+1}. sütun }} \begin{{bmatrix}} {dikey} \end{{bmatrix}}"
        )
    anl.metin("Her satır, aynı sıradaki sütun olur:")
    anl.mat(r"\begin{aligned}" + r" \\[4pt] ".join(satirlar) + r"\end{aligned}")
    if MA.rows > 1 and MA.cols > 1:
        anl.metin("Örneğin köşegen dışındaki elemanlar yer değiştirir:")
        anl.mat(rf"({B(a)}^T)_{{12}} = {_eleman_simgesi(a, 1, 0)} = {L(MA[1, 0])},\qquad "
                rf"({B(a)}^T)_{{21}} = {_eleman_simgesi(a, 0, 1)} = {L(MA[0, 1])}")
    anl.sonuc(rf"{B(a)}^T = {LM(T)}\quad ({_boyut(T)})")
    if MA.is_square:
        if _esit(MA, T):
            anl.metin(rf"${B(a)}^T = {B(a)}$ olduğundan ${B(a)}$ **simetrik** bir matristir.")
        else:
            anl.metin(rf"${B(a)}^T \neq {B(a)}$: matris simetrik değil.")
    semb = _sembolik_mi(MA)
    kn = _KodAdlari(MA)
    ka, kt = kn.al(a), kn.al("T")
    kod = _kod_baslangic(semb, MA) + [(_sp_kodu if semb else _np_kodu)(ka, MA), f"{kt} = {ka}.T", f"print({kt})"]
    if not semb:
        kod.append(f"print('simetrik mi?', np.array_equal({ka}, {ka}.T))" if MA.is_square else f"print('boyut:', {kt}.shape)")
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(T, anl, f"{a}^T", goster, kd, ck)


def iz(A, *, adlar=None, goster=None) -> Sonuc:
    """tr(A): köşegen elemanların toplamı."""
    (MA,), (a,) = _girdileri_al([A], adlar)
    _kare_kontrol(MA, a)
    anl = Anlatim()
    anl.baslik(rf"İz: $\operatorname{{tr}}({B(a)})$")
    anl.kural(r"Kare matrisin **izi**, ana köşegen elemanlarının toplamıdır: $\operatorname{tr}(\mathbf{A}) = \sum_i a_{ii}$. "
              r"İz, özdeğerlerin toplamına eşittir.")
    anl.mat(rf"{B(a)} = {LM(MA)}")
    t = _sade(MA.trace())
    if _sema_sigar(MA, kare=MA.rows):
        anl.sema("Köşegen elemanlar toplanır", _sema_iz(MA, a))
    anl.mat(rf"\operatorname{{tr}}({B(a)}) = " + " + ".join(Lp(MA[i, i]) for i in range(MA.rows)) + f" = {L(t)}")
    anl.sonuc(rf"\operatorname{{tr}}({B(a)}) = {L(t)}")
    semb = _sembolik_mi(MA)
    ka = _KodAdlari(MA).al(a)
    kod = _kod_baslangic(semb, MA) + [(_sp_kodu if semb else _np_kodu)(ka, MA),
                                      f"print({ka}.trace())" if semb else f"print(np.trace({ka}))"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(t, anl, "tr", goster, kd, ck)


def _kare_kontrol(M, ad):
    if not M.is_square:
        raise MatrisHatasi(f"{ad} kare değil ({M.rows}x{M.cols}); bu işlem yalnız kare matrisler için tanımlıdır.")


# ============================================================================
# Satır işlemleri (Gauss eliminasyonu) — det, rank, ters ve çözüm bunu kullanır
# ============================================================================
def _op_latex(tur: str, i: int, j: int | None = None, k=None) -> str:
    if tur == "degis":
        return rf"R_{{{i+1}}} \leftrightarrow R_{{{j+1}}}"
    if tur == "olcek":
        if sp.sympify(k) == -1:
            return rf"R_{{{i+1}}} \leftarrow -R_{{{i+1}}}"
        return rf"R_{{{i+1}}} \leftarrow {Lp(k)}\,R_{{{i+1}}}"
    # ekle: R_i ← R_i − f R_j
    k = sp.sympify(k)
    if k.is_number and k.is_negative:
        if k == -1:     # katsayı 1 yazılmaz: R_i ← R_i + R_j
            return rf"R_{{{i+1}}} \leftarrow R_{{{i+1}}} + R_{{{j+1}}}"
        return rf"R_{{{i+1}}} \leftarrow R_{{{i+1}}} + {L(-k)}\,R_{{{j+1}}}"
    if k == 1:
        return rf"R_{{{i+1}}} \leftarrow R_{{{i+1}}} - R_{{{j+1}}}"
    return rf"R_{{{i+1}}} \leftarrow R_{{{i+1}}} - {Lp(k)}\,R_{{{j+1}}}"


def _eliminasyon(M: sp.Matrix, n_katsayi: int, anl: Anlatim, *, rref: bool = False,
                 cizgi: int | None = None, anlat: bool = True, pivot_bir: bool | None = None):
    """
    M üzerinde satır işlemleri (ilk n_katsayi sütun pivot için kullanılır).
    rref=False → üst basamaklı (echelon) biçim; rref=True → indirgenmiş (Gauss–Jordan).
    Döndürür: (M, pivot_sutunlari, degis_sayisi)
    """
    M = sp.Matrix(M)
    m = M.rows
    pivotlar: list[int] = []
    r = 0
    degis = 0
    if pivot_bir is None:
        pivot_bir = rref
    sema_ac = bool(anlat and _sema_sigar(M))
    kayit: list[dict] = []
    konum = len(anl.bloklar)
    for c in range(n_katsayi):
        if r >= m:
            break
        p = None
        for i in range(r, m):
            if not _sifir(M[i, c]):
                p = i
                break
        if p is None:
            if anlat:
                anl.metin(f"Sütun {c+1}: satır {r+1} ve altındaki elemanların hepsi 0 → bu sütunda pivot yok, sonraki sütuna geçilir.")
            continue
        if p != r:
            once = M.copy() if sema_ac else None
            M.row_swap(p, r)
            degis += 1
            if sema_ac:
                kayit.append({"tur": "degis", "i": r, "j": p, "f": None, "c": c, "once": once, "sonra": M.copy()})
            if anlat:
                anl.metin(f"Sütun {c+1}: pivot konumu ($R_{{{r+1}}}$) 0, bu yüzden satır değiştirilir:")
                anl.mat(_op_latex("degis", r, p) + r"\quad\Rightarrow\quad " + LM(M, cizgi))
        pivot = M[r, c]
        if pivot_bir and not _esit(pivot, 1):
            f = _sade(1 / pivot)
            once = M.copy() if sema_ac else None
            M.row_op(r, lambda v, j, f=f: _sade(v * f))
            if sema_ac:
                kayit.append({"tur": "olcek", "i": r, "j": r, "f": f, "c": c, "once": once, "sonra": M.copy()})
            if anlat:
                anl.metin(f"Sütun {c+1}: pivotu 1 yapmak için satır {r+1}, ${L(pivot)}$ ile bölünür:")
                anl.mat(_op_latex("olcek", r, k=f) + r"\quad\Rightarrow\quad " + LM(M, cizgi))
        hedef = [i for i in range(m) if i != r] if rref else list(range(r + 1, m))
        for i in hedef:
            if _sifir(M[i, c]):
                continue
            f = _sade(M[i, c] / M[r, c])
            satir_r = [M[r, j] for j in range(M.cols)]
            once = M.copy() if sema_ac else None
            M.row_op(i, lambda v, j, f=f, sr=satir_r: _sade(v - f * sr[j]))
            if sema_ac:
                kayit.append({"tur": "ekle", "i": i, "j": r, "f": f, "c": c, "once": once, "sonra": M.copy()})
            if anlat:
                anl.metin(
                    f"Sütun {c+1}: {i+1}. satırın {c+1}. elemanını sıfırlamak için "
                    rf"çarpan $m_{{{i+1}{c+1}}} = a_{{{i+1}{c+1}}}/a_{{{r+1}{c+1}}} = {L(f)}$ "
                    "(sıfırlanacak eleman ÷ pivot) ile:"
                )
                anl.mat(_op_latex("ekle", i, r, f) + r"\quad\Rightarrow\quad " + LM(M, cizgi))
        pivotlar.append(c)
        r += 1
    if sema_ac and 0 < len(kayit) <= _SEMA_EN_KARE:
        anl.sema("Gauss–Jordan: satır işlemleri" if rref else "Gauss eliminasyonu: satır işlemleri",
                 _sema_eliminasyon(kayit, cizgi), max(1, konum))
    return M, pivotlar, degis


# ============================================================================
# Determinant
# ============================================================================
def determinant(A, *, adlar=None, goster=None, yontem: str | None = None) -> Sonuc:
    """det(A). 2×2 ve 3×3 için kofaktör (ve Sarrus), 4×4 ve üstü için satır indirgeme.
    yontem = "kofaktor" | "eliminasyon" ile zorlanabilir."""
    (MA,), (a,) = _girdileri_al([A], adlar)
    _kare_kontrol(MA, a)
    n = MA.rows
    anl = Anlatim()
    anl.baslik(rf"Determinant: $\det({B(a)})$")
    anl.kural(
        r"Determinant yalnız **kare** matrisler için tanımlı bir sayıdır. $\det\mathbf{A} = 0$ ise matris **tekil**dir "
        r"(tersi yoktur, $\mathbf{A}\mathbf{x}=\mathbf{b}$ tek çözümlü değildir). Sonlu elemanlarda mesnetlenmemiş bir "
        r"rijitlik matrisinin determinantı 0'dır (rijit cisim hareketi). "
        r"$2\times2$: $\det = a_{11}a_{22}-a_{12}a_{21}$. $3\times3$ ve üstü: kofaktör açılımı ya da satır indirgeme."
    )
    anl.mat(rf"{B(a)} = {LM(MA)}")
    if yontem is None:
        yontem = "kofaktor" if n <= 3 else "eliminasyon"
    if yontem == "kofaktor":
        d = _det_kofaktor(MA, anl, B(a))
    elif yontem == "eliminasyon":
        d = _det_eliminasyon(MA, anl, B(a))
    else:
        raise MatrisHatasi("yontem 'kofaktor' ya da 'eliminasyon' olmalı.")
    d = _sade(d)
    anl.sonuc(rf"\det({B(a)}) = {L(d)}")
    if _sifir(d):
        anl.metin(rf"$\det = 0$ → ${B(a)}$ **tekil** (singular): tersi yok; satırları/sütunları doğrusal bağımlı.")
    else:
        anl.metin(rf"$\det \neq 0$ → ${B(a)}$ **düzenli** (non-singular): tersi vardır, $\mathbf{{A}}\mathbf{{x}}=\mathbf{{b}}$ tek çözümlüdür.")
    semb = _sembolik_mi(MA)
    kn = _KodAdlari(MA)
    ka = kn.al(a)
    kod = _kod_baslangic(semb, MA) + [(_sp_kodu if semb else _np_kodu)(ka, MA)]
    if semb:
        kod += [f"print(sp.simplify({ka}.det()))"]
    else:
        kdet = kn.al("d")
        kod += [f"{kdet} = np.linalg.det({ka})", f"print(round({kdet}, 6) + 0.0)",
                "# numpy kayan noktalı hesaplar; 2.0000000000000004 gibi sonuçlar yuvarlama hatasıdır."]
    kd, ck = _python_bolumu(anl, kod)
    _tutarlilik(d, MA.det(), "determinant")
    return _bitir(d, anl, "det", goster, kd, ck)


def _det2_latex(M, i1, i2, j1, j2):
    """2×2 minörün açık hesabı: a·d − b·c"""
    a, b, c, d = M[i1, j1], M[i1, j2], M[i2, j1], M[i2, j2]
    deger = _sade(a * d - b * c)
    return rf"{Lp(a)}\cdot {Lp(d)} - {Lp(b)}\cdot {Lp(c)} = {L(deger)}", deger


def _det_kofaktor(M: sp.Matrix, anl: Anlatim, etiket: str, sema: bool = True):
    """etiket: det(...) içinde görünecek hazır LaTeX (örn. \\mathbf{A} ya da \\mathbf{K} - \\lambda\\mathbf{M})."""
    n = M.rows
    if n == 1:
        anl.metin("1×1 matrisin determinantı tek elemanın kendisidir.")
        return M[0, 0]
    if sema and _sema_sigar(M, kare=n + 1):
        if n == 2:
            anl.sema("Çapraz çarpımların farkı", _sema_det2(M))
        else:
            anl.sema("Kofaktör açılımı: ilk satır", _sema_det_kofaktor(M))
    if n == 2:
        anl.metin("2×2 için **çapraz çarpımların farkı**: ana köşegen çarpımı eksi diğer köşegen çarpımı.")
        ifade, d = _det2_latex(M, 0, 1, 0, 1)
        anl.mat(rf"\det({etiket}) = a_{{11}}a_{{22}} - a_{{12}}a_{{21}} = {ifade}")
        return d
    if n == 3:
        anl.metin("3×3 için **1. satıra göre kofaktör açılımı**: her eleman, kendi satır ve sütunu silinince kalan 2×2 "
                  "determinant (minör) ile çarpılır; işaretler $+,-,+$ sırasıyla gider "
                  "(formüldeki $a_{ij}$, determinantı alınan matrisin elemanlarıdır).")
        anl.mat(rf"\det({etiket}) = a_{{11}}" r"\begin{vmatrix} a_{22} & a_{23}\\ a_{32} & a_{33}\end{vmatrix}"
                r" - a_{12}\begin{vmatrix} a_{21} & a_{23}\\ a_{31} & a_{33}\end{vmatrix}"
                r" + a_{13}\begin{vmatrix} a_{21} & a_{22}\\ a_{31} & a_{32}\end{vmatrix}")
        m1, d1 = _det2_latex(M, 1, 2, 1, 2)
        m2, d2 = _det2_latex(M, 1, 2, 0, 2)
        m3, d3 = _det2_latex(M, 1, 2, 0, 1)
        anl.metin("Minörler:")
        anl.mat(r"\begin{aligned}"
                rf"M_{{11}} &= \begin{{vmatrix}} {L(M[1,1])} & {L(M[1,2])}\\ {L(M[2,1])} & {L(M[2,2])}\end{{vmatrix}} = {m1} \\ "
                rf"M_{{12}} &= \begin{{vmatrix}} {L(M[1,0])} & {L(M[1,2])}\\ {L(M[2,0])} & {L(M[2,2])}\end{{vmatrix}} = {m2} \\ "
                rf"M_{{13}} &= \begin{{vmatrix}} {L(M[1,0])} & {L(M[1,1])}\\ {L(M[2,0])} & {L(M[2,1])}\end{{vmatrix}} = {m3}"
                r"\end{aligned}")
        d = _sade(M[0, 0] * d1 - M[0, 1] * d2 + M[0, 2] * d3)
        anl.metin("Açılım:")
        anl.mat(rf"\det({etiket}) = {Lp(M[0,0])}\cdot {Lp(d1)} - {Lp(M[0,1])}\cdot {Lp(d2)} + {Lp(M[0,2])}\cdot {Lp(d3)} = {L(d)}")
        # Sarrus kontrolü
        s1 = [M[0, 0] * M[1, 1] * M[2, 2], M[0, 1] * M[1, 2] * M[2, 0], M[0, 2] * M[1, 0] * M[2, 1]]
        s2 = [M[0, 2] * M[1, 1] * M[2, 0], M[0, 0] * M[1, 2] * M[2, 1], M[0, 1] * M[1, 0] * M[2, 2]]
        anl.metin("**Sağlama (Sarrus kuralı):** ilk iki sütun sağa kopyalanır; sağa inen köşegen çarpımları toplanır, "
                  "sola inenler çıkarılır:")
        anl.mat(r"\det = (" + " + ".join(Lp(_sade(t)) for t in s1) + ") - (" + " + ".join(Lp(_sade(t)) for t in s2) + rf") = {L(d)}")
        return d
    # n ≥ 4: ilk satıra göre açılım, minörler özyinelemeli (anlatım kısaltılmış)
    anl.metin(f"{n}×{n} için 1. satıra göre kofaktör açılımı (her minör {n-1}×{n-1} determinanttır; "
              "minörler ayrıca hesaplanıp yerine yazılmıştır):")
    terimler = []
    d = sp.Integer(0)
    for j in range(n):
        minor = M.minor_submatrix(0, j)
        dm = _sade(minor.det())
        isaret = (-1) ** j
        d += isaret * M[0, j] * dm
        terimler.append(rf"{'+' if isaret > 0 else '-'}{Lp(M[0, j])}\cdot {Lp(dm)}")
    d = _sade(d)
    ifade = " ".join(terimler).lstrip("+")
    anl.mat(rf"\det({etiket}) = {ifade} = {L(d)}")
    return d


def _det_eliminasyon(M: sp.Matrix, anl: Anlatim, etiket: str):
    anl.metin("**Satır indirgeme yöntemi:** $R_i \\leftarrow R_i - f\\,R_j$ işlemi determinantı değiştirmez; "
              "iki satırın yer değiştirmesi işareti çevirir. Üst üçgen biçime gelince determinant, "
              "köşegen elemanlarının çarpımıdır.")
    U, pivotlar, degis = _eliminasyon(M, M.cols, anl, rref=False, pivot_bir=False)
    kose = [U[i, i] for i in range(M.rows)]
    d = _sade(sp.Integer(-1) ** degis * sp.prod(kose))
    anl.metin(f"Satır değiştirme sayısı: {degis} → işaret $(-1)^{{{degis}}} = {(-1)**degis}$. Köşegen çarpımı:")
    anl.mat(rf"\det({etiket}) = (-1)^{{{degis}}}\cdot " + r"\cdot ".join(Lp(k) for k in kose) + f" = {L(d)}")
    return d


# ============================================================================
# Ters
# ============================================================================
def ters(A, *, adlar=None, goster=None, yontem: str | None = None) -> Sonuc:
    """A⁻¹. 2×2 için formül, diğerleri için Gauss–Jordan ([A | I] → [I | A⁻¹]).
    yontem = "formul" | "gauss" ile zorlanabilir."""
    (MA,), (a,) = _girdileri_al([A], adlar)
    _kare_kontrol(MA, a)
    n = MA.rows
    anl = Anlatim()
    anl.baslik(rf"Ters matris: ${B(a)}^{{-1}}$")
    anl.kural(
        r"$\mathbf{A}^{-1}$, $\mathbf{A}\mathbf{A}^{-1} = \mathbf{A}^{-1}\mathbf{A} = \mathbf{I}$ koşulunu sağlayan matristir; "
        r"yalnız **kare ve $\det\neq0$** olan matrislerin tersi vardır. "
        r"$2\times2$: $\mathbf{A}^{-1} = \frac{1}{\det\mathbf{A}}\begin{bmatrix} d & -b\\ -c & a\end{bmatrix}$. "
        r"Genel yöntem (Gauss–Jordan): $[\,\mathbf{A}\mid\mathbf{I}\,]$ matrisine satır işlemleri uygulanarak sol taraf "
        r"$\mathbf{I}$ yapılır; sağ tarafta $\mathbf{A}^{-1}$ kalır. Çözümde $\mathbf{x}=\mathbf{A}^{-1}\mathbf{b}$ kullanılabilir "
        r"ama büyük sistemlerde ters almak yerine eliminasyon tercih edilir."
    )
    anl.mat(rf"{B(a)} = {LM(MA)}")
    d = _sade(MA.det())
    anl.metin(f"Önce determinant: $\\det({B(a)}) = {L(d)}$" + (" → **tekil, tersi yok.**" if _sifir(d) else " ≠ 0 ✔ tersi vardır."))
    if _sifir(d):
        anl.goster(goster)
        raise MatrisHatasi(f"{a} tekil (det = 0); tersi yoktur.")
    if yontem is None:
        yontem = "formul" if n == 2 else "gauss"
    if yontem == "formul":
        if n != 2:
            raise MatrisHatasi("'formul' yöntemi yalnız 2×2 için; yontem='gauss' kullanın.")
        p, q, r_, s = MA[0, 0], MA[0, 1], MA[1, 0], MA[1, 1]
        adj = sp.Matrix([[s, -q], [-r_, p]])
        Ainv = _sade(adj / d)
        anl.metin("2×2 formülü: köşegen elemanlar yer değiştirir, diğer ikisinin işareti değişir, determinanta bölünür.")
        anl.mat(rf"{B(a)}^{{-1}} = \frac{{1}}{{{L(d)}}}{LM(adj)} = {LM(Ainv)}")
    elif yontem == "gauss":
        anl.metin(rf"Genişletilmiş matris $[\,{B(a)}\mid\mathbf{{I}}\,]$ kurulur:")
        G = MA.row_join(sp.eye(n))
        anl.mat(LM(G, cizgi=n))
        anl.metin("Sol blok birim matris olana kadar satır işlemleri (pivotlar 1 yapılır, pivot sütununun diğer elemanları sıfırlanır):")
        R, pivotlar, _ = _eliminasyon(G, n, anl, rref=True, cizgi=n)
        Ainv = _sade(R[:, n:])
        anl.metin("Sol blok $\\mathbf{I}$ oldu; sağ blok tersi verir:")
        anl.mat(rf"[\,\mathbf{{I}}\mid{B(a)}^{{-1}}\,] = {LM(R, cizgi=n)}")
    else:
        raise MatrisHatasi("yontem 'formul' ya da 'gauss' olmalı.")
    anl.sonuc(rf"{B(a)}^{{-1}} = {LM(Ainv)}")
    sag = _sade(MA * Ainv)
    anl.metin(rf"**Sağlama:** ${B(a)}{B(a)}^{{-1}} = {LM(sag)} = \mathbf{{I}}$ ✔")
    semb = _sembolik_mi(MA)
    kn = _KodAdlari(MA)
    ka, kinv = kn.al(a), kn.al("Ainv")
    kod = _kod_baslangic(semb, MA) + [(_sp_kodu if semb else _np_kodu)(ka, MA)]
    kod += [f"{kinv} = sp.simplify({ka}.inv())", f"sp.pprint({kinv})"] if semb else \
           [f"{kinv} = np.linalg.inv({ka})", f"print({kinv})", f"print('saglama {ka} @ {kinv} =')",
            f"print(np.round({ka} @ {kinv}, 6) + 0.0)"]
    kd, ck = _python_bolumu(anl, kod)
    _tutarlilik(Ainv, MA.inv(), "ters")
    return _bitir(Ainv, anl, f"{a}^{{-1}}", goster, kd, ck)


# ============================================================================
# Rank
# ============================================================================
def rank(A, *, adlar=None, goster=None) -> Sonuc:
    """rank(A): doğrusal bağımsız satır (= sütun) sayısı; basamaklı biçimdeki sıfır olmayan satır sayısı."""
    (MA,), (a,) = _girdileri_al([A], adlar)
    anl = Anlatim()
    anl.baslik(rf"Rank: $\operatorname{{rank}}({B(a)})$")
    anl.kural(
        r"Rank, matristeki **doğrusal bağımsız satır sayısı**dır (doğrusal bağımsız sütun sayısına da eşittir; "
        r"satır ve sütun sayısının küçüğünü aşamaz). Satır işlemleriyle basamaklı biçime getirilince "
        r"**sıfır olmayan satırların sayısı** rankı verir. $n\times n$ matris için "
        r"rank $= n$ ise matris düzenlidir (tersi vardır); rank $< n$ ise tekildir."
    )
    anl.mat(rf"{B(a)} = {LM(MA)}")
    R, pivotlar, _ = _eliminasyon(MA, MA.cols, anl, rref=False, pivot_bir=False)
    rk = len(pivotlar)
    anl.metin(f"Basamaklı biçimde sıfır olmayan satır sayısı = pivot sayısı = **{rk}**.")
    anl.sonuc(rf"\operatorname{{rank}}({B(a)}) = {rk}")
    if MA.is_square:
        if rk == MA.rows:
            anl.metin("Rank = n → düzenli (tam ranklı).")
        else:
            anl.metin(f"Rank < n ({rk} < {MA.rows}) → tekil; {MA.rows - rk} satır diğerlerine bağımlı.")
    semb = _sembolik_mi(MA)
    ka = _KodAdlari(MA).al(a)
    kod = _kod_baslangic(semb, MA) + [(_sp_kodu if semb else _np_kodu)(ka, MA),
                                      f"print({ka}.rank())" if semb else f"print(np.linalg.matrix_rank({ka}))"]
    kd, ck = _python_bolumu(anl, kod)
    _tutarlilik(sp.Integer(rk), sp.Integer(MA.rank()), "rank")
    return _bitir(sp.Integer(rk), anl, "rank", goster, kd, ck)


# ============================================================================
# Doğrusal denklem sistemi çözümü
# ============================================================================
def _isaret_ayir(c):
    """Katsayıyı (negatif_mi, mutlak_değer) olarak ayır.

    Toplam olan katsayı ``(a + b)`` bölünmez; pozitif sayılır ve ``Lp`` onu parantezler."""
    c = sp.sympify(c)
    if c.is_Add:
        return False, c
    if c.is_number and c.is_real:
        return bool(c < 0), (-c if c < 0 else c)
    if c.could_extract_minus_sign():
        return True, -c
    return False, c


def _lineer_latex(terimler, *, ilk: str | None = None, carpi: str = "") -> str:
    """Σ katsayı·simge toplamını okunur LaTeX'e çevirir.

    Katsayı 1 yazılmaz (``1x_2`` değil ``x_2``); negatif terim ``+ (-3)x`` yerine `` - 3x`` olarak
    eklenir; sıfır katsayılı terim atlanır. ``ilk``: başa konacak hazır terim (ör. sağ taraf)."""
    cikti = ilk or ""
    for k, simge in terimler:
        if _sifir(k):
            continue
        neg, mut = _isaret_ayir(k)
        bir = mut == 1 or (mut.is_number and _esit(mut, 1))
        # sembolik katsayı + simge bitişik yazılırsa "ku_1" tek değişken gibi okunur → ince boşluk
        ayrac = carpi if (carpi or mut.is_number) else r"\,"
        govde = simge if bir else f"{Lp(mut)}{ayrac}{simge}"
        if cikti:
            cikti += (" - " if neg else " + ") + govde
        else:
            cikti = ("-" if neg else "") + govde
    return cikti or "0"


def _zincir_esit(parcalar) -> str:
    """Eşitlik zincirini kur; art arda aynı olan parçaları tek yaz (``= 4/5 = 4/5`` olmasın)."""
    temiz: list[str] = []
    for p in parcalar:
        if not temiz or temiz[-1] != p:
            temiz.append(p)
    return " = ".join(temiz)


def _kesir_latex(pay: str, payda) -> str:
    """payda 1 ise yalnız pay; değilse \\frac{pay}{payda}."""
    if _esit(payda, 1):
        return pay
    return rf"\frac{{{pay}}}{{{L(payda)}}}"


def _bilinmeyen_onek(x: str, n: int, *Ms) -> str:
    """Sonsuz çözümde bilinmeyen sembollerinin (x1, x2, ...) adı matristeki sembollerle çakışmasın."""
    isimler = {s.name for s in _semboller(*Ms)}
    onek = x
    while any(f"{onek}{j}" in isimler for j in range(1, n + 1)):
        onek += "_"
    return onek


def _coz_anlat(anl: Anlatim, MA, Mb, a: str, bad: str, x: str, yontem: str, *,
               goster=None, indisler=None, vektor_etiketi: str | None = None, ara: bool = False):
    """A x = b çözümünün anlatımını ``anl``'ye ekler (başlık, kural ve girdi gösterimi çağıranındır).

    Döndürür: ``(X, genel)``. Tek çözümde X sütun vektörüdür, genel None; sonsuz çözümde X None,
    genel ``sp.linsolve`` kümesidir. Çözüm yoksa MatrisHatasi (önce ``anl.goster(goster)`` ile
    o ana kadarki anlatım gösterilir).
    ``indisler``: bilinmeyenlerin alt indisleri (indirgenmiş sistemde global serbestlik numaraları).
    ``ara``: True ise çözüm "Sonuç" kutusu yerine ara adım olarak yazılır (çağıran asıl sonucu kendisi verir)."""
    n_bil = MA.cols
    kare = MA.is_square
    xl = x.replace("_", r"\_")
    etk = (lambda j: indisler[j]) if indisler is not None else (lambda j: j + 1)
    vek = vektor_etiketi or rf"\mathbf{{{xl}}}"

    def sim(j: int) -> str:
        return rf"{xl}_{{{etk(j)}}}"

    # Denklemleri açık yaz (katsayı 1 yazılmaz, negatif terim " - " ile eklenir)
    denk = []
    for i in range(MA.rows):
        sol = _lineer_latex([(MA[i, j], sim(j)) for j in range(n_bil)])
        denk.append(rf"{sol} &= {L(Mb[i, 0])}")
    anl.metin("Açık yazılışı (her satır bir denklem):")
    anl.mat(r"\begin{aligned}" + r" \\ ".join(denk) + r"\end{aligned}")

    if yontem == "gauss":
        anl.metin(rf"**İleri eliminasyon** — genişletilmiş matris $[\,{B(a)}\mid{B(bad)}\,]$:")
        G = MA.row_join(Mb)
        anl.mat(LM(G, cizgi=n_bil))
        U, pivotlar, _ = _eliminasyon(G, n_bil, anl, rref=False, cizgi=n_bil, pivot_bir=False)
        rk = len(pivotlar)
        # tutarsızlık kontrolü
        tutarsiz = any(all(_sifir(U[i, j]) for j in range(n_bil)) and not _sifir(U[i, n_bil]) for i in range(U.rows))
        if tutarsiz:
            anl.uyari("Bir satır $[\\,0\\;0\\cdots0\\mid c\\,]$ ($c\\neq0$) biçimine geldi: $0 = c$ çelişkisi → sistemin **çözümü yok** (tutarsız).")
            anl.goster(goster)
            raise _TutarsizSistem("Sistem tutarsız: çözüm yok (bir satır 0 = c, c ≠ 0 biçimine geldi; denklemler birbiriyle çelişiyor).")
        if rk < n_bil:
            anl.uyari(
                f"Pivot sayısı ({rk}) bilinmeyen sayısından ({n_bil}) az → **sonsuz çözüm** var; {n_bil - rk} bilinmeyen serbest. "
                "Sonlu elemanlarda bu durum genellikle **sınır koşulları (mesnetler) uygulanmadığı** için ortaya çıkar: "
                "rijitlik matrisi tekildir, yapı rijit cisim gibi hareket edebilir."
            )
            onek = _bilinmeyen_onek(x, n_bil, MA, Mb)
            semboller = sp.symbols(f"{onek}1:{n_bil + 1}")
            genel = sp.linsolve((MA, Mb), *semboller)
            if genel == sp.S.EmptySet:
                anl.goster(goster)
                raise _TutarsizSistem("Sistem tutarsız: çözüm yok.")
            sol = list(genel)[0]
            serbest = [s for s in semboller if any(e.has(s) for e in sol)]
            havuz = {s.name for s in _semboller(MA, Mb)}
            tonek = next((h for h in ("t", "s", "r", "q", "w")
                          if h not in havuz and not any(f"{h}_{k}" in havuz for k in range(1, len(serbest) + 1))), "tau")
            tsym = [sp.Symbol(tonek if len(serbest) == 1 else f"{tonek}_{k + 1}") for k in range(len(serbest))]
            vec = sp.Matrix(list(sol)).subs(dict(zip(serbest, tsym)))
            anl.metin(
                "Serbest bilinmeyen: "
                + ", ".join(f"${sim(semboller.index(s))}$ → ${sp.latex(t)}$" for s, t in zip(serbest, tsym))
                + " (herhangi bir gerçel sayı olabilir). Genel çözüm:"
            )
            anl.mat(rf"{vek} = {LM(vec)},\qquad " + ", ".join(sp.latex(t) for t in tsym) + r" \in \mathbb{R}")
            return None, genel
        gk = len(anl.bloklar)
        anl.metin("**Geri yerine koyma** — üst üçgen sistemden, son denklemden başlayarak:")
        X = sp.zeros(n_bil, 1)
        satirlar = []
        geri: list[dict] = []
        for i in range(n_bil - 1, -1, -1):
            sag = U[i, n_bil]
            piv = U[i, i]
            bilinenler = [(U[i, j], X[j, 0], j) for j in range(i + 1, n_bil) if not _sifir(U[i, j])]
            deger = _sade((sag - sum((u * xv for u, xv, _ in bilinenler), sp.Integer(0))) / piv)
            X[i, 0] = deger
            geri.append({"i": i, "X": X.copy(), "bil": bilinenler, "sag": sag, "piv": piv, "deger": deger})
            ilk = None if (bilinenler and _sifir(sag)) else L(sag)
            pay_s = _lineer_latex([(-u, sim(j)) for u, _, j in bilinenler], ilk=ilk)
            parcalar = [_kesir_latex(pay_s, piv)]
            if bilinenler:
                pay_n = _lineer_latex([(-u, Lp(xv)) for u, xv, _ in bilinenler], ilk=ilk, carpi=r"\cdot ")
                parcalar.append(_kesir_latex(pay_n, piv))
            parcalar.append(L(deger))
            satirlar.append(rf"{sim(i)} &= " + _zincir_esit(parcalar))
        anl.mat(r"\begin{aligned}" + r" \\ ".join(satirlar) + r"\end{aligned}")
        if _sema_sigar(U, kare=len(geri)):
            anl.sema("Geri yerine koyma: sondan başa", _sema_geri_koyma(U, n_bil, geri, x.replace("_", ""), etk),
                     max(1, gk))
    elif yontem == "cramer":
        if not kare or MA.rows > 3:
            raise MatrisHatasi("Cramer yöntemi burada yalnız 1×1–3×3 kare sistemler için gösterilir.")
        d = _sade(MA.det())
        anl.metin(rf"**Cramer kuralı:** ${xl}_i = \det(\mathbf{{A}}_i)/\det(\mathbf{{A}})$; $\mathbf{{A}}_i$ matrisi, "
                  r"$\mathbf{A}$ matrisinde $i$. sütun yerine $\mathbf{b}$ vektörü konarak elde edilir.")
        anl.mat(rf"\det({B(a)}) = {L(d)}")
        if _sifir(d):
            anl.uyari("$\\det = 0$ → Cramer uygulanamaz (tek çözüm yok).")
            anl.goster(goster)
            raise MatrisHatasi("det = 0: Cramer uygulanamaz.")
        X = sp.zeros(n_bil, 1)
        satirlar = []
        for i in range(n_bil):
            Ai = MA.copy()
            Ai[:, i] = Mb
            di = _sade(Ai.det())
            X[i, 0] = _sade(di / d)
            satirlar.append(
                rf"{sim(i)} &= " + _zincir_esit([
                    rf"\frac{{\det {LM(Ai)}}}{{{L(d)}}}",
                    _kesir_latex(L(di), d),
                    L(X[i, 0]),
                ])
            )
        anl.mat(r"\begin{aligned}" + r" \\[6pt] ".join(satirlar) + r"\end{aligned}")
    elif yontem == "ters":
        if not kare:
            raise MatrisHatasi("Ters yöntemi yalnız kare sistemler için.")
        d = _sade(MA.det())
        if _sifir(d):
            anl.uyari("$\\det = 0$ → ters yok, bu yöntem uygulanamaz.")
            anl.goster(goster)
            raise MatrisHatasi("det = 0: ters yöntemi uygulanamaz.")
        Ainv = _sade(MA.inv())
        anl.metin(rf"**Ters matris yöntemi:** ${vek} = {B(a)}^{{-1}}{B(bad)}$ (tersin adımları için `ters()` fonksiyonuna bakın).")
        anl.mat(rf"{B(a)}^{{-1}} = {LM(Ainv)}")
        X = _sade(Ainv * Mb)
        anl.mat(rf"{vek} = {LM(Ainv)}{LM(Mb)} = {LM(X)}")
    else:
        raise MatrisHatasi("yontem: 'gauss', 'cramer' ya da 'ters'.")

    if indisler is not None:    # indirgenmiş sistem: vektörün hangi global SD'lere karşılık geldiğini göster
        acilim = r"\begin{bmatrix} " + r" \\ ".join(sim(j) for j in range(n_bil)) + r" \end{bmatrix}"
        cozum = rf"{vek} = {acilim} = {LM(X)}"
    else:
        cozum = rf"{vek} = {LM(X)}"
    if ara:
        anl.metin("İndirgenmiş sistemin çözümü:")
        anl.mat(cozum)
    else:
        anl.sonuc(cozum)
    sag = _sade(MA * X)
    anl.metin(rf"**Sağlama:** ${B(a)}{vek} = {LM(sag)} = {B(bad)}$ ✔")
    _tutarlilik(sag, Mb, "coz")
    return X, None


def coz(A, b, *, adlar=None, goster=None, yontem: str = "gauss", bilinmeyen: str = "x") -> Sonuc:
    """A x = b sistemini çöz. yontem = "gauss" (eliminasyon + geri yerine koyma), "cramer" (n ≤ 3), "ters" (x = A⁻¹ b).
    Sonlu elemanlarda: K u = F → coz(K, F, bilinmeyen="u")."""
    MA, Mb = matris(A), matris(b)
    x = _ad_dogrula(bilinmeyen, "Bilinmeyen adı")
    if adlar is None:
        a = A.ad if isinstance(A, Sonuc) and _ad_gecerli_mi(A.ad) else "A"
        bad = b.ad if isinstance(b, Sonuc) and _ad_gecerli_mi(b.ad) else "b"
        if a == x:
            a = _harf_sec(a, {x, bad})
        if bad in (a, x):
            bad = _harf_sec(bad, {a, x, bad})
    else:
        a, bad = _adlar(2, adlar)
    if Mb.rows == 1 and Mb.cols == MA.rows and MA.rows > 1:
        Mb = Mb.T  # satır olarak yazılmış sağ taraf → sütun vektörü
    if Mb.cols != 1:
        raise MatrisHatasi("Sağ taraf b bir sütun vektörü olmalı (örn. \"3; 5\").")
    if Mb.rows != MA.rows:
        raise MatrisHatasi(f"{a} {MA.rows} satırlı ama {bad} {Mb.rows} elemanlı; satır sayıları eşit olmalı.")
    if yontem not in ("gauss", "cramer", "ters"):
        raise MatrisHatasi("yontem: 'gauss', 'cramer' ya da 'ters'.")
    n_bil = MA.cols
    xl = x.replace("_", r"\_")
    anl = Anlatim()
    anl.baslik(rf"Denklem sistemi: ${B(a)}\,\mathbf{{{xl}}} = {B(bad)}$")
    anl.kural(
        rf"$\mathbf{{A}}\mathbf{{{xl}}}=\mathbf{{b}}$, $n$ bilinmeyenli $m$ denklemin matris yazımıdır: katsayılar $\mathbf{{A}}$ matrisinde, "
        rf"bilinmeyenler $\mathbf{{{xl}}}$ vektöründe, sağ taraf $\mathbf{{b}}$ vektöründe toplanır. **Gauss eliminasyonu:** genişletilmiş matris "
        r"$[\,\mathbf{A}\mid\mathbf{b}\,]$ satır işlemleriyle üst üçgen yapılır (ileri eliminasyon), sonra son denklemden "
        r"başlayarak bilinmeyenler bulunur (geri yerine koyma). Kare sistemde $\det\mathbf{A}\neq0$ ise tek çözüm vardır. "
        r"Sonlu elemanlarda bu sistem $\mathbf{K}\mathbf{u}=\mathbf{F}$ biçimindedir (rijitlik × yer değiştirme = yük)."
    )
    anl.mat(rf"{B(a)} = {LM(MA)},\qquad {B(bad)} = {LM(Mb)}")
    X, genel = _coz_anlat(anl, MA, Mb, a, bad, x, yontem, goster=goster)

    # Üretilen Python kodu (adlar kullanıcı sembolleriyle çakışmaz)
    kn = _KodAdlari(MA, Mb)
    ka, kb, kx = kn.al(a), kn.al(bad), kn.al(x)
    if genel is not None:   # sonsuz çözüm: sympy'nin linsolve'u
        onek = _bilinmeyen_onek(x, n_bil, MA, Mb)
        kod = _kod_baslangic(True, MA, Mb) + [
            _sp_kodu(ka, MA), _sp_kodu(kb, Mb),
            f"{kx} = sp.symbols('{onek}1:{n_bil + 1}')",
            f"print(sp.linsolve(({ka}, {kb}), *{kx}))",
        ]
        kd, ck = _python_bolumu(anl, kod)
        return _bitir(genel, anl, x, goster, kd, ck)
    semb = _sembolik_mi(MA, Mb)
    kare = MA.is_square
    kod = _kod_baslangic(semb, MA, Mb)
    if semb:
        kod += [_sp_kodu(ka, MA), _sp_kodu(kb, Mb)]
        if yontem == "cramer":
            kd_, kAi, ki = kn.al("d"), kn.al("Ai"), kn.al("i")
            kod += [f"{kd_} = {ka}.det()", f"{kx} = sp.zeros({n_bil}, 1)", f"for {ki} in range({n_bil}):",
                    f"    {kAi} = {ka}.copy()", f"    {kAi}[:, {ki}] = {kb}   # {ki}. sütunu b ile değiştir",
                    f"    {kx}[{ki}, 0] = sp.simplify({kAi}.det() / {kd_})"]
        elif yontem == "ters":
            kinv = kn.al("Ainv")
            kod += [f"{kinv} = {ka}.inv()", f"{kx} = sp.simplify({kinv} * {kb})"]
        elif kare:
            kod += [f"{kx} = sp.simplify({ka}.LUsolve({kb}))"]
        else:
            kod += [f"{kx} = sp.simplify({ka}.gauss_jordan_solve({kb})[0])"]
        kod += [f"sp.pprint({kx})"]
    else:
        kod += [_np_kodu(ka, MA), _np_kodu(kb, Mb)]
        if yontem == "cramer":
            kd_, kAi, ki = kn.al("d"), kn.al("Ai"), kn.al("i")
            kod += [f"{kd_} = np.linalg.det({ka})", f"{kx} = np.zeros_like({kb})", f"for {ki} in range({n_bil}):",
                    f"    {kAi} = {ka}.copy()", f"    {kAi}[:, [{ki}]] = {kb}   # {ki}. sütunu b ile değiştir",
                    f"    {kx}[{ki}, 0] = np.linalg.det({kAi}) / {kd_}"]
        elif yontem == "ters":
            kinv = kn.al("Ainv")
            kod += [f"{kinv} = np.linalg.inv({ka})", f"{kx} = {kinv} @ {kb}"]
        elif kare:
            kod += [f"{kx} = np.linalg.solve({ka}, {kb})"]
        else:
            kod += [f"{kx} = np.linalg.lstsq({ka}, {kb}, rcond=None)[0]   # kare değil: tutarlı sistemde tam çözüm"]
        kod += [f"print({kx})", f"# Sağlama: {ka} @ {kx} ile {kb} aynı olmalı", f"print(np.allclose({ka} @ {kx}, {kb}))"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(X, anl, x, goster, kd, ck)


# ============================================================================
# Özdeğer / özvektör
# ============================================================================
def ozdeger(A, M=None, *, adlar=None, goster=None, ozvektor: bool = True) -> Sonuc:
    """A v = λ v (ya da M verilirse K φ = λ M φ, λ = ω²). n ≤ 3 için karakteristik polinom adım adım;
    daha büyük matrislerde sayısal (numpy) hesaplanır."""
    if M is None:
        (MA,), (a,) = _girdileri_al([A], adlar)
        MM, mad = None, None
    else:
        (MA, MM), (a, mad) = _girdileri_al([A, M], adlar if adlar else ["K", "M"])
    _kare_kontrol(MA, a)
    n = MA.rows
    lam = sp.Symbol("lambda")
    anl = Anlatim()
    anl.baslik(rf"Özdeğer problemi: ${B(a)}\mathbf{{v}} = \lambda{(B(mad) if MM is not None else '')}\mathbf{{v}}$")
    anl.kural(
        r"$\mathbf{A}\mathbf{v}=\lambda\mathbf{v}$ eşitliğini sağlayan $\lambda$ sayıları **özdeğer**, $\mathbf{v}\neq\mathbf{0}$ vektörleri "
        r"**özvektör**dür. $(\mathbf{A}-\lambda\mathbf{I})\mathbf{v}=\mathbf{0}$ sıfırdan farklı çözüm için "
        r"$\det(\mathbf{A}-\lambda\mathbf{I})=0$ olmalıdır (**karakteristik denklem**). "
        r"Sonlu elemanlarda serbest titreşim: $\mathbf{K}\boldsymbol{\phi}=\omega^2\mathbf{M}\boldsymbol{\phi}$, "
        r"$\det(\mathbf{K}-\omega^2\mathbf{M})=0$ → doğal frekanslar $\omega_i$, mod şekilleri $\boldsymbol{\phi}_i$."
    )
    anl.mat(rf"{B(a)} = {LM(MA)}" + (rf",\qquad {B(mad)} = {LM(MM)}" if MM is not None else ""))
    I_or_M = MM if MM is not None else sp.eye(n)
    Bm = _sade(MA - lam * I_or_M)
    sag_ad = B(mad) if MM is not None else r"\mathbf{I}"
    anl.metin(rf"${B(a)} - \lambda{sag_ad}$ matrisi:")
    anl.mat(LM(Bm))
    sayisal_yol = n > 3 or _sembolik_mi(MA) or (MM is not None and _sembolik_mi(MM))
    if not sayisal_yol:
        anl.metin("Karakteristik polinom (determinant, 1. satıra göre açılım):")
        p = _det_kofaktor(Bm, anl, f"{a}-\\lambda I", sema=False)
        p = sp.expand(p)
        pf = sp.factor(p)
        anl.mat(rf"p(\lambda) = {sp.latex(p)}" + (rf" = {sp.latex(pf)}" if pf != p else ""))
        kokler = sp.roots(sp.Poly(p, lam))
        if sum(kokler.values()) < n:
            kokler = {r: 1 for r in sp.Poly(p, lam).nroots()}
            anl.metin("Kökler kapalı biçimde sade çıkmadı; sayısal kökler:")
        ozd = []
        for r, kat in sorted(kokler.items(), key=lambda t: (sp.re(t[0]), sp.im(t[0]))):
            ozd.extend([r] * kat)
        anl.metin("$p(\\lambda)=0$ denkleminin kökleri özdeğerlerdir:")
        anl.mat(r",\quad ".join(
            rf"\lambda_{{{i+1}}} = {L(r)}" + (rf" \approx {_ondalik_latex(sp.N(r))}" if not sp.sympify(r).is_Rational and sp.sympify(r).is_real else "")
            for i, r in enumerate(ozd)))
        vekt = []
        if ozvektor:
            anl.metin("**Özvektörler:** her $\\lambda_i$ için $(\\mathbf{A}-\\lambda_i\\mathbf{I})\\mathbf{v}=\\mathbf{0}$ sisteminin sıfırdan farklı çözümü (sıfır uzayı):")
            gorulen = set()
            for i, r in enumerate(ozd):
                if r in gorulen:
                    continue
                gorulen.add(r)
                Br = _sade(MA - r * I_or_M)
                R, pivotlar, _ = _eliminasyon(Br, n, anl, rref=True, anlat=False)
                ns = Br.nullspace()
                vs = []
                for v in ns:
                    v = _sade(v)
                    payda = sp.lcm([sp.sympify(t).q for t in v if sp.sympify(t).is_Rational] or [1])
                    vs.append(_sade(v * payda))
                vekt.append((r, vs))
                anl.mat(rf"\lambda = {L(r)}:\quad {LM(Br)} \xrightarrow{{\text{{satır indirgeme}}}} {LM(R)}"
                        rf"\quad\Rightarrow\quad " + r",\ ".join(rf"\mathbf{{v}} = {LM(v)}" for v in vs))
        anl.sonuc(r",\quad ".join(rf"\lambda_{{{i+1}}} = {L(r)}" for i, r in enumerate(ozd)))
        if MM is not None:
            anl.metin("$\\lambda = \\omega^2$ olduğundan doğal frekanslar: "
                      + ", ".join(rf"$\omega_{{{i+1}}} = \sqrt{{{L(r)}}} \approx {_ondalik_latex(sp.sqrt(sp.N(r)))}$"
                                  for i, r in enumerate(ozd) if sp.sympify(r).is_real and sp.sympify(r) >= 0))
        deger = (ozd, vekt)
    else:
        anl.metin("Bu boyutta/sembolik durumda karakteristik polinomun kökleri elle uzun olur; sonuç sayısal/sembolik "
                  "kütüphane ile hesaplanır (yöntem aynıdır: $\\det(\\mathbf{A}-\\lambda\\mathbf{I})=0$).")
        Bm2 = MM.inv() * MA if MM is not None else MA
        ev = Bm2.eigenvals()
        ozd = []
        for r, kat in ev.items():
            ozd.extend([_sade(r)] * kat)
        anl.sonuc(r",\quad ".join(rf"\lambda_{{{i+1}}} = {L(r)}" for i, r in enumerate(ozd)))
        deger = (ozd, [])
    semb = _sembolik_mi(MA) or (MM is not None and _sembolik_mi(MM))
    kod = _kod_baslangic(semb, MA, *([MM] if MM is not None else []))
    if semb:
        kod += [_sp_kodu(a, MA)] + ([_sp_kodu(mad, MM)] if MM is not None else [])
        kod += [f"print(({mad}.inv()*{a}).eigenvals())" if MM is not None else f"print({a}.eigenvals())"]
    else:
        kod += [_np_kodu(a, MA)] + ([_np_kodu(mad, MM)] if MM is not None else [])
        if MM is not None:
            kod += [f"lam, phi = np.linalg.eig(np.linalg.solve({mad}, {a}))", "print('ozdegerler (omega^2):', lam)",
                    "print('frekanslar omega:', np.sqrt(np.abs(lam)))", "print('mod sekilleri (sutunlar):')", "print(phi)"]
        else:
            kod += [f"lam, v = np.linalg.eig({a})", "print('ozdegerler:', lam)", "print('ozvektorler (sutunlar):')", "print(v)"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(deger, anl, "lambda", goster, kd, ck)


# ============================================================================
# Sonlu elemanlar yardımcıları
# ============================================================================
def cubuk_eleman(E="E", A="A", L_="L", *, goster=None, ad: str = "k") -> Sonuc:
    """Çubuk (bar/truss, eksenel) elemanı rijitlik matrisi: k = (EA/L) [[1, -1], [-1, 1]]."""
    Ev, Av, Lv = skaler_oku(E), skaler_oku(A), skaler_oku(L_)
    anl = Anlatim()
    anl.baslik("Çubuk (eksenel) elemanı rijitlik matrisi")
    anl.kural(
        r"İki düğümlü çubuk elemanda düğüm kuvvetleri ile düğüm yer değiştirmeleri arasındaki bağ "
        r"$\mathbf{f} = \mathbf{k}\,\mathbf{u}$'dur. Eksenel rijitlik bir yay gibi $EA/L$'dir: "
        r"$\mathbf{k} = \dfrac{EA}{L}\begin{bmatrix} 1 & -1\\ -1 & 1\end{bmatrix}$. "
        r"1. satır: $f_1 = \frac{EA}{L}(u_1 - u_2)$; 2. satır: $f_2 = \frac{EA}{L}(u_2 - u_1)$. "
        r"Matris simetriktir ve tekildir ($\det=0$, mesnetsiz eleman rijit ötelenebilir)."
    )
    kat = _sade(Ev * Av / Lv)
    k = _sade(kat * sp.Matrix([[1, -1], [-1, 1]]))
    anl.mat(rf"E = {L(Ev)},\quad A = {L(Av)},\quad L = {L(Lv)}\quad\Rightarrow\quad \frac{{EA}}{{L}} = {L(kat)}")
    anl.sonuc(rf"{B(ad)} = {L(kat)}\begin{{bmatrix}} 1 & -1\\ -1 & 1\end{{bmatrix}} = {LM(k)}")
    semb = _sembolik_mi(k)
    kod = _kod_baslangic(semb, k)
    if semb:
        kod += [f"E_, A_, L_ = {_sp_eleman(Ev)}, {_sp_eleman(Av)}, {_sp_eleman(Lv)}",
                "k = (E_*A_/L_) * sp.Matrix([[1, -1], [-1, 1]])", "sp.pprint(sp.simplify(k))"]
    else:
        kod += [f"E, A, L = {_py_sayi(Ev)}, {_py_sayi(Av)}, {_py_sayi(Lv)}", "k = (E*A/L) * np.array([[1, -1], [-1, 1]])", "print(k)"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(k, anl, ad, goster, kd, ck)


def kiris_eleman(E="E", I="I", L_="L", *, goster=None, ad: str = "k") -> Sonuc:
    """Kiriş (Euler–Bernoulli) elemanı 4×4 rijitlik matrisi (v1, θ1, v2, θ2)."""
    Ev, Iv, Lv = skaler_oku(E), skaler_oku(I), skaler_oku(L_)
    anl = Anlatim()
    anl.baslik("Kiriş elemanı rijitlik matrisi (Euler–Bernoulli)")
    anl.kural(
        r"Serbestlikler: $[v_1, \theta_1, v_2, \theta_2]$ (çökme ve dönme). "
        r"$\mathbf{k} = \dfrac{EI}{L^3}\begin{bmatrix} 12 & 6L & -12 & 6L\\ 6L & 4L^2 & -6L & 2L^2\\ -12 & -6L & 12 & -6L\\ 6L & 2L^2 & -6L & 4L^2\end{bmatrix}$. "
        r"Simetriktir; her sütun, ilgili serbestliğe birim yer değiştirme verildiğinde oluşan uç kuvvetleridir."
    )
    kat = _sade(Ev * Iv / Lv**3)
    T = sp.Matrix([[12, 6 * Lv, -12, 6 * Lv], [6 * Lv, 4 * Lv**2, -6 * Lv, 2 * Lv**2],
                   [-12, -6 * Lv, 12, -6 * Lv], [6 * Lv, 2 * Lv**2, -6 * Lv, 4 * Lv**2]])
    k = _sade(kat * T)
    anl.mat(rf"E = {L(Ev)},\quad I = {L(Iv)},\quad L = {L(Lv)}\quad\Rightarrow\quad \frac{{EI}}{{L^3}} = {L(kat)}")
    anl.sonuc(rf"{B(ad)} = {L(kat)}{LM(T)} = {LM(k)}")
    semb = _sembolik_mi(k)
    kod = _kod_baslangic(semb, k)
    if semb:
        kod += [f"E_, I_, L_ = {_sp_eleman(Ev)}, {_sp_eleman(Iv)}, {_sp_eleman(Lv)}",
                "k = (E_*I_/L_**3) * sp.Matrix([[12, 6*L_, -12, 6*L_], [6*L_, 4*L_**2, -6*L_, 2*L_**2], [-12, -6*L_, 12, -6*L_], [6*L_, 2*L_**2, -6*L_, 4*L_**2]])",
                "sp.pprint(sp.simplify(k))"]
    else:
        kod += [f"E, I, L = {_py_sayi(Ev)}, {_py_sayi(Iv)}, {_py_sayi(Lv)}",
                "k = (E*I/L**3) * np.array([[12, 6*L, -12, 6*L], [6*L, 4*L**2, -6*L, 2*L**2], [-12, -6*L, 12, -6*L], [6*L, 2*L**2, -6*L, 4*L**2]])",
                "print(k)"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(k, anl, ad, goster, kd, ck)


def kafes_eleman(E="E", A="A", L_="L", aci_derece=0, *, goster=None, ad: str = "k") -> Sonuc:
    """Düzlem kafes elemanı: global 4×4 rijitlik k = Tᵀ k_yerel T (dönüşüm adım adım)."""
    Ev, Av, Lv = skaler_oku(E), skaler_oku(A), skaler_oku(L_)
    th = skaler_oku(aci_derece)
    anl = Anlatim()
    anl.baslik(f"Düzlem kafes elemanı: açı θ = {L(th)}°, global rijitlik $\\mathbf{{k}} = \\mathbf{{T}}^T\\mathbf{{k}}'\\mathbf{{T}}$")
    anl.kural(
        r"Yerel eksende eleman yalnız eksenel çalışır: $\mathbf{k}' = \frac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$. "
        r"Global serbestlikler $[u_1, v_1, u_2, v_2]$; yerel eksenel yer değiştirmeler $\mathbf{u}' = \mathbf{T}\mathbf{u}$, "
        r"$\mathbf{T} = \begin{bmatrix} c & s & 0 & 0\\ 0 & 0 & c & s\end{bmatrix}$, $c=\cos\theta$, $s=\sin\theta$. "
        r"Enerji eşitliğinden $\mathbf{k} = \mathbf{T}^T\mathbf{k}'\mathbf{T}$ (4×4) elde edilir."
    )
    c = _sade(sp.cos(th * sp.pi / 180))
    s = _sade(sp.sin(th * sp.pi / 180))
    kat = _sade(Ev * Av / Lv)
    kloc = _sade(kat * sp.Matrix([[1, -1], [-1, 1]]))
    T = sp.Matrix([[c, s, 0, 0], [0, 0, c, s]])
    anl.mat(rf"c = \cos{L(th)}^\circ = {L(c)},\quad s = \sin{L(th)}^\circ = {L(s)},\quad \frac{{EA}}{{L}} = {L(kat)}")
    anl.mat(rf"\mathbf{{k}}' = {LM(kloc)},\qquad \mathbf{{T}} = {LM(T)},\qquad \mathbf{{T}}^T = {LM(T.T)}")
    anl.metin("Önce $\\mathbf{T}^T\\mathbf{k}'$ (4×2 · 2×2), sonra sonuç ile $\\mathbf{T}$ (4×2 · 2×4) çarpılır:")
    ara = _ikili_carp(anl, T.T, kloc, "T^T", "k'", "T^Tk'", sema=False)
    k = _ikili_carp(anl, ara, T, "T^Tk'", "T", "k", sema=False)
    k = _sade(k)
    anl.metin("Kapalı biçim (kontrol): $\\mathbf{k} = \\frac{EA}{L}\\begin{bmatrix} c^2 & cs & -c^2 & -cs\\\\ cs & s^2 & -cs & -s^2\\\\ -c^2 & -cs & c^2 & cs\\\\ -cs & -s^2 & cs & s^2\\end{bmatrix}$")
    anl.sonuc(rf"{B(ad)} = {LM(k)}")
    semb = _sembolik_mi(k)
    kod = _kod_baslangic(semb, k)
    if semb:
        kod += [f"E_, A_, L_ = {_sp_eleman(Ev)}, {_sp_eleman(Av)}, {_sp_eleman(Lv)}",
                f"theta = sp.rad({_sp_eleman(th)})", "c, s = sp.cos(theta), sp.sin(theta)",
                "k_yerel = (E_*A_/L_) * sp.Matrix([[1, -1], [-1, 1]])",
                "T = sp.Matrix([[c, s, 0, 0], [0, 0, c, s]])", "k = sp.simplify(T.T * k_yerel * T)", "sp.pprint(k)"]
    else:
        kod += [f"E, A, L, theta = {_py_sayi(Ev)}, {_py_sayi(Av)}, {_py_sayi(Lv)}, np.radians({_py_sayi(th)})",
                "c, s = np.cos(theta), np.sin(theta)", "k_yerel = (E*A/L) * np.array([[1, -1], [-1, 1]])",
                "T = np.array([[c, s, 0, 0], [0, 0, c, s]])", "k = T.T @ k_yerel @ T", "print(k)"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(k, anl, ad, goster, kd, ck)


def birlestir(elemanlar, n_serbestlik: int, *, goster=None, ad: str = "K") -> Sonuc:
    """Global rijitlik matrisi birleştirme (assembly).
    elemanlar = [(k1, [1, 2]), (k2, [2, 3]), ...]  → her eleman matrisi ve global serbestlik numaraları (1'den başlar)."""
    K = sp.zeros(n_serbestlik, n_serbestlik)
    anl = Anlatim()
    anl.baslik(f"Global rijitlik matrisi birleştirme ({n_serbestlik} serbestlik)")
    anl.kural(
        r"Her elemanın rijitlik matrisindeki $k^{(e)}_{ab}$ elemanı, o elemanın yerel $a$ ve $b$ serbestliklerinin "
        r"**global numaralarına** karşılık gelen $K_{IJ}$ konumuna **eklenir** (üst üste gelenler toplanır). "
        r"Ortak düğümlerde iki elemanın katkısı birbirine eklenir; sonuç simetriktir ve mesnet uygulanmadan tekildir."
    )
    kmatrisler = []
    sema_konum = len(anl.bloklar)
    sema_adim: list[dict] = []
    for e, (k, dof) in enumerate(elemanlar, start=1):
        k = matris(k)
        dof = [int(d) for d in dof]
        kmatrisler.append((k, dof))
        if k.rows != len(dof) or not k.is_square:
            raise MatrisHatasi(f"Eleman {e}: matris {k.rows}x{k.cols} ama {len(dof)} serbestlik numarası verildi.")
        if max(dof) > n_serbestlik or min(dof) < 1:
            raise MatrisHatasi(f"Eleman {e}: serbestlik numaraları 1..{n_serbestlik} arasında olmalı.")
        dof_metin = ", ".join(map(str, dof))
        anl.metin(f"**Eleman {e}** — global serbestlikler [{dof_metin}]: $k^{{({e})}}_{{ab}}$, satır/sütun numaraları "
                  f"$[{dof_metin}]$ olan $K_{{IJ}}$ konumlarına eklenir.")
        anl.mat(rf"\mathbf{{k}}^{{({e})}} = {LM(k)}\quad\text{{(satır/sütun sırası: }}{dof_metin}\text{{)}}")
        satirlar = []
        for ai, I_ in enumerate(dof):
            for bi, J_ in enumerate(dof):
                if _sifir(k[ai, bi]):
                    continue
                K[I_ - 1, J_ - 1] = _sade(K[I_ - 1, J_ - 1] + k[ai, bi])
                satirlar.append(rf"K_{{{I_}{J_}}} &\mathrel{{+}}= k^{{({e})}}_{{{ai+1}{bi+1}}} = {L(k[ai, bi])}")
        if len(satirlar) <= ayarlar.en_fazla_eleman:
            anl.mat(r"\begin{aligned}" + r" \\ ".join(satirlar) + r"\end{aligned}")
        anl.mat(rf"{B(ad)}\ \text{{(eleman {e} eklendikten sonra)}} = {LM(K)}")
        if ayarlar.sema:
            sema_adim.append({"k": k, "dof": dof, "K": K.copy()})
    if sema_adim and _sema_sigar(K, *[a["k"] for a in sema_adim], kare=len(sema_adim)):
        anl.sema("Elemanlar global matrise eklenir", _sema_birlestir(sema_adim, n_serbestlik, ad), max(1, sema_konum))
    anl.sonuc(rf"{B(ad)} = {LM(K)}")
    semb = _sembolik_mi(K)
    kod = _kod_baslangic(semb, K)
    if semb:
        kod += [f"K = sp.zeros({n_serbestlik}, {n_serbestlik})"]
        for e, (k, dof) in enumerate(kmatrisler, start=1):
            kod += [_sp_kodu(f"k{e}", k), f"dof{e} = {[d-1 for d in dof]}  # Python 0'dan sayar",
                    f"for a, I in enumerate(dof{e}):", f"    for b, J in enumerate(dof{e}):", f"        K[I, J] += k{e}[a, b]"]
        kod += ["sp.pprint(sp.simplify(K))"]
    else:
        kod += [f"K = np.zeros(({n_serbestlik}, {n_serbestlik}))"]
        for e, (k, dof) in enumerate(kmatrisler, start=1):
            kod += [_np_kodu(f"k{e}", k), f"dof{e} = {[d-1 for d in dof]}  # Python 0'dan sayar",
                    f"K[np.ix_(dof{e}, dof{e})] += k{e}"]
        kod += ["print(K)"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(K, anl, ad, goster, kd, ck)


def _tam_sayi_mi(s):
    """s tam sayı gibi mi (3, np.int64(3), sp.Integer(3), 3.0, "3")? Öyleyse int, değilse None.

    bool, kesirli sayı (2.5) ve sayı olmayan metin tam sayı sayılmaz (``int(2.5)`` sessizce 2 yapardı)."""
    if isinstance(s, bool) or (np is not None and isinstance(s, np.bool_)):
        return None
    try:
        f = float(s)
    except (TypeError, ValueError, OverflowError):
        return None
    return int(f) if f.is_integer() else None


def _sabit_oku(sabit, n: int) -> list[int]:
    """Tutulu (sabit) SD numaralarını (1'den başlayan) sıralı, tekrarsız ``int`` listesine çevirir.

    Kabul edilen biçimler: liste / küme / range / numpy dizisi, tek tam sayı ya da "1, 3" metni."""
    if sabit is None:
        ogeler: list = []
    elif isinstance(sabit, str):
        ogeler = [p for p in re.split(r"[\s,;]+", sabit.strip().strip("[]()")) if p]
    elif np is not None and isinstance(sabit, np.ndarray):
        ogeler = sabit.ravel().tolist()
    else:
        try:
            ogeler = list(sabit)
        except TypeError:       # tek sayı
            ogeler = [sabit]
    bulunan: set[int] = set()
    for s in ogeler:
        t = _tam_sayi_mi(s)
        if t is None:
            raise MatrisHatasi(f"Tutulu (sabit) SD numaraları tam sayı olmalı (örn. [1, 3]); geçersiz değer: {s!r}")
        if t < 1 or t > n:
            raise MatrisHatasi(f"Tutulu (sabit) SD numaraları 1..{n} arasında olmalı (verilen: {t}).")
        bulunan.add(t)
    return sorted(bulunan)


def _yetersiz_mesnet_mesaji(Ks, kad: str, sabit, tutarsiz: bool) -> str:
    """K_s tekil çıktığında (mesnet yetersiz) öğretici hata metni."""
    m = Ks.rows
    try:
        rk = Ks.rank(iszerofunc=_sifir)
    except Exception:  # noqa: BLE001
        rk = None
    rank_s = f" (rank {rk} < {m})" if rk is not None else ""
    kalan = f" ({m - rk} bağımsız rijit cisim hareketi kalıyor)" if rk is not None else ""
    if sabit:
        bas = (f"Yetersiz mesnet: indirgenmiş {kad}_s matrisi tekil{rank_s}; tutulu SD'ler yapıyı yerinde tutmaya "
               f"yetmiyor, yapı rijit cisim gibi hareket edebilir{kalan}.")
    else:
        bas = (f"Hiç mesnet verilmedi (sabit = []): {kad} matrisi tekil{rank_s}; yapı rijit cisim gibi "
               f"hareket edebilir{kalan}.")
    if tutarsiz:
        orta = " Yükler bu hareketi dengelemiyor: sistemin çözümü yok."
    else:
        orta = " Yükler dengede olsa bile yer değiştirmeler tek değil (rijit cisim hareketi kadar belirsiz)."
    son = " Daha fazla SD sabitleyin" + (" (örn. sabit=[1])." if not sabit else ".")
    return bas + orta + son


def sinir_kosulu(K, F, sabit, *, goster=None, adlar=("K", "F"), bilinmeyen: str = "u") -> Sonuc:
    """Sınır koşullarını uygula ve çöz: tutulu (sabit) serbestlik derecelerinin (SD) satır ve sütunları silinir,
    indirgenmiş K_s u_s = F_s çözülür; sonra tüm u ve mesnet tepkileri R = K u − F bulunur.
    sabit = [1, 4] gibi 1'den başlayan SD numaralarıdır (liste, tek sayı ya da "1, 4" metni).
    Mesnet yetersizse (K_s tekil: yapı rijit cisim gibi hareket edebilir) MatrisHatasi verir."""
    MK, MF = matris(K), matris(F)
    kad, fad = _adlar(2, adlar or ("K", "F"))
    bil = _ad_dogrula(bilinmeyen, "Bilinmeyen adı")
    if bil in (kad, fad):
        raise MatrisHatasi(f"Bilinmeyen adı ({bil}) matris adlarından ({kad}, {fad}) farklı olmalı.")
    _kare_kontrol(MK, kad)
    n = MK.rows
    if MF.rows == 1 and MF.cols == n:
        MF = MF.T
    if MF.rows != n or MF.cols != 1:
        raise MatrisHatasi(f"{fad}, {n} elemanlı bir sütun vektörü olmalı.")
    sabit = _sabit_oku(sabit, n)
    serbest = [i for i in range(1, n + 1) if i not in sabit]
    if not serbest:
        raise MatrisHatasi("Tüm serbestlik dereceleri (SD) sabit; çözülecek bilinmeyen yok.")
    rad = _harf_sec("R", {kad, fad, bil})
    idx = [i - 1 for i in serbest]
    Bk, Bf, Bu, Br = B(kad), B(fad), B(bil), B(rad)
    Bks, Bfs, Bus = B(f"{kad}_s"), B(f"{fad}_s"), B(f"{bil}_s")
    xl = bil.replace("_", r"\_")

    anl = Anlatim()
    anl.baslik(r"Sınır koşulları ve çözüm: $\mathbf{K}\mathbf{u}=\mathbf{F}$")
    anl.kural(
        r"Mesnetlenmemiş sistemde $\mathbf{K}$ tekildir: yapı rijit cisim gibi hareket edebilir, tek çözüm yoktur. "
        r"Mesnet, bazı serbestlik derecelerinin (SD) yer değiştirmesini bilinen bir değere (genelde 0) bağlar; "
        r"**tutulu SD'lerin satır ve sütunları silinir** (bu yalnız bilinen değer 0 iken geçerlidir; sıfırdan farklı "
        r"bir yer değiştirmede, örneğin mesnet çökmesinde, silinen sütunların katkısı sağ taraftan çıkarılmalıdır). "
        r"Kalan indirgenmiş sistem $\mathbf{K}_s\mathbf{u}_s = \mathbf{F}_s$ çözülür, sonra tüm $\mathbf{u}$ "
        r"vektörü kurulur (tutulu SD'lere 0 yazılır)."
        "\n\n"
        r"**Mesnet tepkileri** $\mathbf{R} = \mathbf{K}\mathbf{u} - \mathbf{F}$ ile bulunur: serbest SD'lerde $R_i = 0$ "
        r"çıkmalıdır (sağlama); tutulu SD'lerdeki değerler tepkilerdir. "
        r"$R_i$, global eksenin pozitif yönünde pozitiftir; negatif değer hata değildir, mesnedin kuvveti "
        r"eksenin ters yönünde uyguladığını gösterir."
    )
    anl.mat(rf"{Bk} = {LM(MK)},\qquad {Bf} = {LM(MF)}")
    if sabit and serbest and _sema_sigar(MK, MF):
        anl.sema("Mesnetler: serbest ve tutulu bölümler",
                 _sema_mesnet_bolum(MK, MF, serbest, sabit, kad, fad, bil))
    anl.metin(f"Tutulu (sabit) serbestlik dereceleri (SD): {sabit} (yer değiştirme = 0). Serbest SD'ler: {serbest}.")
    Ks = MK.extract(idx, idx)
    Fs = MF.extract(idx, [0])
    bilinmeyenler = ", ".join(rf"{xl}_{{{i}}}" for i in serbest)
    anl.metin("İndirgenmiş sistem (tutulu SD'lerin satır ve sütunları silindi). "
              f"Bilinmeyenler, silinmeyen SD'lerin yer değiştirmeleridir: ${Bus} = [{bilinmeyenler}]^T$.")
    anl.mat(rf"{Bks} = {LM(Ks)},\qquad {Bfs} = {LM(Fs)}")
    try:
        X, _ = _coz_anlat(anl, Ks, Fs, f"{kad}_s", f"{fad}_s", bil, "gauss", goster=goster,
                          indisler=serbest, vektor_etiketi=Bus, ara=True)
    except _TutarsizSistem as e:
        raise MatrisHatasi(_yetersiz_mesnet_mesaji(Ks, kad, sabit, tutarsiz=True)) from e
    if X is None:   # K_s tekil, sonsuz çözüm
        anl.goster(goster)
        raise MatrisHatasi(_yetersiz_mesnet_mesaji(Ks, kad, sabit, tutarsiz=False))

    u = sp.zeros(n, 1)
    for j, i in enumerate(serbest):
        u[i - 1, 0] = X[j, 0]
    anl.metin("Tüm yer değiştirme vektörü (tutulu SD'lere 0 yazılır):")
    anl.mat(rf"{Bu} = {LM(u)}")
    R = _sade(MK * u - MF)
    _tutarlilik(R.extract(idx, [0]), sp.zeros(len(idx), 1), "sinir_kosulu")
    if sabit and _sema_sigar(MK, u, MF, R):
        anl.sema("Mesnet tepkileri", _sema_mesnet_tepki(MK, u, MF, R, sabit, kad, fad, bil, rad))
    anl.metin(
        rf"**Mesnet tepkileri.** Her SD'de denge ${Bk}{Bu} = {Bf} + {Br}$ olmalıdır "
        rf"(${Br}$: mesnedin yapıya uyguladığı kuvvet; serbest SD'lerde 0). "
        rf"Buradan ${Br} = {Bk}{Bu} - {Bf}$:"
    )
    anl.mat(rf"{Br} = {LM(MK)}{LM(u)} - {LM(MF)} = {LM(R)}")
    if sabit:
        anl.metin(f"**Sağlama:** serbest SD'lerde ({serbest}) tepki 0 çıktı ✔ (yük iç kuvvetlerle dengelenmiş); "
                  f"sıfırdan farklı değerler yalnız tutulu SD'lerde ({sabit}) görünür.")
        # Tüm sütun toplamları 0 ise (ör. aynı doğrultudaki çubuk zinciri) toplam denge de sağlanır
        if all(_sifir(sum(MK[:, j], sp.Integer(0))) for j in range(n)):
            sR, sF = _sade(sum(R, sp.Integer(0))), _sade(sum(MF, sp.Integer(0)))
            if _sifir(sR + sF):
                anl.metin(f"**Denge denetimi:** ${Bk}$ matrisinin her sütununun toplamı sıfırdır (tüm SD'lerin birlikte "
                          "ötelenmesi iç kuvvet doğurmaz); bu yüzden dış yüklerle tepkilerin toplamı sıfır olmalıdır:")
                anl.mat(rf"\sum R_i + \sum F_i = {L(sR)} + {Lp(sF)} = 0")
    else:
        anl.metin("Hiçbir SD tutulmadı; tüm tepkiler sıfırdır (yapı yalnız kendi yaylarıyla dengededir).")
    anl.sonuc(rf"{Bu} = {LM(u)},\qquad {Br} = {LM(R)}")

    # Üretilen Python kodu (adlar kullanıcı sembolleriyle çakışmaz)
    kn = _KodAdlari(MK, MF)
    kK, kF, ku, kR = kn.al(kad), kn.al(fad), kn.al(bil), kn.al(rad)
    kser, kKs, kFs, kus = kn.al("serbest"), kn.al("Ks"), kn.al("Fs"), kn.al("us")
    semb = _sembolik_mi(MK, MF)
    kod = _kod_baslangic(semb, MK, MF)
    sd_satiri = f"{kser} = {idx}  # serbest SD'ler; Python 0'dan saydığı için numara − 1"
    if semb:
        ki, kdof = kn.al("i"), kn.al("d")
        kod += [_sp_kodu(kK, MK), _sp_kodu(kF, MF), sd_satiri,
                f"{kKs} = {kK}.extract({kser}, {kser})", f"{kFs} = {kF}.extract({kser}, [0])",
                f"{kus} = sp.simplify({kKs}.LUsolve({kFs}))", f"{ku} = sp.zeros({n}, 1)",
                f"for {ki}, {kdof} in enumerate({kser}): {ku}[{kdof}] = {kus}[{ki}]",
                f"{kR} = sp.simplify({kK}*{ku} - {kF})",
                f"print('{bil} ='); sp.pprint({ku})", f"print('{rad} ='); sp.pprint({kR})"]
    else:
        kes = kn.al("esik")
        kod += [_np_kodu(kK, MK), _np_kodu(kF, MF), sd_satiri,
                f"{kKs} = {kK}[np.ix_({kser}, {kser})]", f"{kFs} = {kF}[{kser}]",
                f"{kus} = np.linalg.solve({kKs}, {kFs})", f"{ku} = np.zeros(({n}, 1))", f"{ku}[{kser}] = {kus}",
                f"{kR} = {kK} @ {ku} - {kF}",
                f"{kes} = 1e-9 * max(1.0, np.abs({kF}).max())   # yuvarlama artığı eşiği",
                f"{kR} = np.where(np.abs({kR}) < {kes}, 0.0, {kR})   # '-0.' görünmesin",
                f"print('{bil} ='); print({ku})", f"print('{rad} ='); print({kR})"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(u, anl, bil, goster, kd, ck)


# ============================================================================
# Yardım
# ============================================================================
YARDIM_METNI = """
**matris_ogren — fonksiyonlar** (hepsi adımları gösterir ve `Sonuc` döndürür)

| Fonksiyon | Ne yapar | Örnek |
|---|---|---|
| `topla(A, B)` / `cikar(A, B)` | eleman eleman toplama / çıkarma | `mo.topla("1 2; 3 4", "5 6; 7 8")` |
| `skaler(k, A)` | sayı ile çarpma | `mo.skaler(3, "1 2; 3 4")` |
| `carp(A, B, ...)` | matris çarpımı (zincir olabilir) | `mo.carp("1 2; 3 4", "5 6; 7 8")` |
| `transpoz(A)` | transpoz | `mo.transpoz("1 2 3; 4 5 6")` |
| `determinant(A)` | determinant (kofaktör / satır indirgeme) | `mo.determinant("2 1; 1 3")` |
| `ters(A)` | ters matris (formül / Gauss–Jordan) | `mo.ters("4 7; 2 6")` |
| `rank(A)` | rank | `mo.rank("1 2; 2 4")` |
| `iz(A)` | iz (köşegen toplamı) | `mo.iz("2 1; 1 3")` |
| `coz(A, b)` | A x = b çözümü (gauss / cramer / ters) | `mo.coz("2 1; 1 3", "3; 5")` |
| `ozdeger(A)` / `ozdeger(K, M)` | özdeğer–özvektör / doğal frekans | `mo.ozdeger("2 1; 1 2")` |
| `cubuk_eleman(E, A, L)` | çubuk elemanı k | `mo.cubuk_eleman("E", "A", "L")` |
| `kiris_eleman(E, I, L)` | kiriş elemanı k (4×4) | `mo.kiris_eleman(200e3, 500, 2000)` |
| `kafes_eleman(E, A, L, açı)` | kafes elemanı k = TᵀkT | `mo.kafes_eleman(1, 1, 1, 45)` |
| `birlestir([(k1,[1,2]), (k2,[2,3])], n)` | global K birleştirme | — |
| `sinir_kosulu(K, F, sabit=[1])` | mesnet uygula, çöz, tepkiler | — |
| `ayarla(ondalik=True, basamak=3)` | gösterim ayarları | — |

`goster=` seçenekleri: `"hepsi"` (varsayılan), `"adimlar"`, `"python"`, `"sonuc"`, `"yok"`.
Girdi: `"1 2; 3 4"`, `"1/3 0.5; E*A/L 2"`, `[[1,2],[3,4]]`, numpy dizisi ya da bir önceki `Sonuc`.
Ok şeması: çarpma, toplama, eliminasyon, geri yerine koyma, birleştirme ve mesnet adımları için matris üstünde
adım adım ok/kutu çizimleri üretilir (`"hepsi"` ve `"adimlar"` içinde); kapatmak için `ayarla(sema=False)`.
"""


def yardim():
    """Fonksiyon listesi."""
    if _IPYTHON:
        display(Markdown(YARDIM_METNI))
    else:
        print(YARDIM_METNI)
