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
    from IPython.display import Markdown, Math, display  # type: ignore
except ImportError:  # pragma: no cover
    get_ipython = None
    Markdown = Math = display = None


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

__version__ = "1.1.0"


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
    goster: str = "hepsi"       # varsayılan gösterim: hepsi | adimlar | python | sonuc | yok


ayarlar = Ayarlar()


def ayarla(**kw) -> Ayarlar:
    """Ayarları değiştir: mo.ayarla(ondalik=True, basamak=3)"""
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

    # --- dışa verme ---
    def markdown(self) -> str:
        parcalar = []
        for tur, icerik, _ in self.bloklar:
            if tur == "md":
                parcalar.append(icerik)
            elif tur == "math":
                parcalar.append("$$" + icerik + "$$")
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
            "hepsi": {"kural", "adim", "sonuc", "python"},
            "adimlar": {"kural", "adim", "sonuc"},
            "python": {"python", "sonuc"},
            "sonuc": {"sonuc"},
        }.get(mod)
        if secim is None:
            raise MatrisHatasi(f"goster={mod!r} geçersiz. Seçenekler: hepsi, adimlar, python, sonuc, yok")
        if not ayarlar.python:
            secim = secim - {"python"}
        if not ayarlar.kural:
            secim = secim - {"kural"}
        bloklar = [b for b in self.bloklar if b[2] in secim]
        if _IPYTHON:
            for tur, icerik, _ in bloklar:
                if tur == "md":
                    display(Markdown(icerik))
                elif tur == "math":
                    display(Math(icerik))
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


def _ikili_carp(anl: Anlatim, MA, MB, a, b, c, goster=None) -> sp.Matrix:
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
            M.row_swap(p, r)
            degis += 1
            if anlat:
                anl.metin(f"Sütun {c+1}: pivot konumu ($R_{{{r+1}}}$) 0, bu yüzden satır değiştirilir:")
                anl.mat(_op_latex("degis", r, p) + r"\quad\Rightarrow\quad " + LM(M, cizgi))
        pivot = M[r, c]
        if pivot_bir and not _esit(pivot, 1):
            f = _sade(1 / pivot)
            M.row_op(r, lambda v, j, f=f: _sade(v * f))
            if anlat:
                anl.metin(f"Sütun {c+1}: pivotu 1 yapmak için satır {r+1}, ${L(pivot)}$ ile bölünür:")
                anl.mat(_op_latex("olcek", r, k=f) + r"\quad\Rightarrow\quad " + LM(M, cizgi))
        hedef = [i for i in range(m) if i != r] if rref else list(range(r + 1, m))
        for i in hedef:
            if _sifir(M[i, c]):
                continue
            f = _sade(M[i, c] / M[r, c])
            satir_r = [M[r, j] for j in range(M.cols)]
            M.row_op(i, lambda v, j, f=f, sr=satir_r: _sade(v - f * sr[j]))
            if anlat:
                anl.metin(
                    f"Sütun {c+1}: {i+1}. satırın {c+1}. elemanını sıfırlamak için "
                    rf"çarpan $m_{{{i+1}{c+1}}} = a_{{{i+1}{c+1}}}/a_{{{r+1}{c+1}}} = {L(f)}$ "
                    "(sıfırlanacak eleman ÷ pivot) ile:"
                )
                anl.mat(_op_latex("ekle", i, r, f) + r"\quad\Rightarrow\quad " + LM(M, cizgi))
        pivotlar.append(c)
        r += 1
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


def _det_kofaktor(M: sp.Matrix, anl: Anlatim, etiket: str):
    """etiket: det(...) içinde görünecek hazır LaTeX (örn. \\mathbf{A} ya da \\mathbf{K} - \\lambda\\mathbf{M})."""
    n = M.rows
    if n == 1:
        anl.metin("1×1 matrisin determinantı tek elemanın kendisidir.")
        return M[0, 0]
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
        anl.metin("**Geri yerine koyma** — üst üçgen sistemden, son denklemden başlayarak:")
        X = sp.zeros(n_bil, 1)
        satirlar = []
        for i in range(n_bil - 1, -1, -1):
            sag = U[i, n_bil]
            piv = U[i, i]
            bilinenler = [(U[i, j], X[j, 0], j) for j in range(i + 1, n_bil) if not _sifir(U[i, j])]
            deger = _sade((sag - sum((u * xv for u, xv, _ in bilinenler), sp.Integer(0))) / piv)
            X[i, 0] = deger
            ilk = None if (bilinenler and _sifir(sag)) else L(sag)
            pay_s = _lineer_latex([(-u, sim(j)) for u, _, j in bilinenler], ilk=ilk)
            parcalar = [_kesir_latex(pay_s, piv)]
            if bilinenler:
                pay_n = _lineer_latex([(-u, Lp(xv)) for u, xv, _ in bilinenler], ilk=ilk, carpi=r"\cdot ")
                parcalar.append(_kesir_latex(pay_n, piv))
            parcalar.append(L(deger))
            satirlar.append(rf"{sim(i)} &= " + _zincir_esit(parcalar))
        anl.mat(r"\begin{aligned}" + r" \\ ".join(satirlar) + r"\end{aligned}")
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
        p = _det_kofaktor(Bm, anl, f"{a}-\\lambda I")
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
    ara = _ikili_carp(anl, T.T, kloc, "T^T", "k'", "T^Tk'")
    k = _ikili_carp(anl, ara, T, "T^Tk'", "T", "k")
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


def sinir_kosulu(K, F, sabit, *, goster=None, adlar=("K", "F"), bilinmeyen: str = "u") -> Sonuc:
    """Sınır koşullarını uygula ve çöz: sabit serbestliklerin satır/sütunları silinir, indirgenmiş K_s u_s = F_s çözülür,
    tüm u ve mesnet tepkileri R = K u − F bulunur. sabit = [1, 4] gibi 1'den başlayan serbestlik numaraları."""
    MK, MF = matris(K), matris(F)
    kad, fad = adlar
    if MF.rows == 1 and MF.cols == MK.rows:
        MF = MF.T
    n = MK.rows
    if MF.rows != n or MF.cols != 1:
        raise MatrisHatasi(f"F, {n} elemanlı bir sütun vektörü olmalı.")
    sabit = sorted({int(s) for s in sabit})
    if any(s < 1 or s > n for s in sabit):
        raise MatrisHatasi(f"Sabit serbestlik numaraları 1..{n} arasında olmalı.")
    serbest = [i for i in range(1, n + 1) if i not in sabit]
    if not serbest:
        raise MatrisHatasi("Tüm serbestlikler sabit; çözülecek bilinmeyen yok.")
    anl = Anlatim()
    anl.baslik("Sınır koşulları ve çözüm: $\\mathbf{K}\\mathbf{u}=\\mathbf{F}$")
    anl.kural(
        r"Mesnetlenmemiş sistemde $\mathbf{K}$ tekildir; **sabit (bilinen, genelde 0) serbestliklerin satır ve sütunları silinir**. "
        r"Kalan indirgenmiş sistem $\mathbf{K}_s\mathbf{u}_s = \mathbf{F}_s$ çözülür. Sonra tüm yer değiştirme vektörü kurulur ve "
        r"**mesnet tepkileri** $\mathbf{R} = \mathbf{K}\mathbf{u} - \mathbf{F}$ ile bulunur (sabit serbestliklerde sıfırdan farklıdır)."
    )
    anl.mat(rf"{B(kad)} = {LM(MK)},\qquad {B(fad)} = {LM(MF)}")
    anl.metin(f"Sabit serbestlikler: {sabit} (yer değiştirme = 0). Serbest kalanlar: {serbest}.")
    Ks = MK.extract([i - 1 for i in serbest], [i - 1 for i in serbest])
    Fs = MF.extract([i - 1 for i in serbest], [0])
    anl.metin("İndirgenmiş sistem (sabit satır ve sütunlar silindi):")
    anl.mat(rf"{B(kad)}_s = {LM(Ks)},\qquad {B(fad)}_s = {LM(Fs)}")
    alt = coz(Ks, Fs, adlar=(f"{kad}_s", f"{fad}_s"), goster="yok", bilinmeyen=bilinmeyen)
    # alt çözümün adımlarını (başlık ve kural hariç) bu anlatıma aktar
    for blok in alt.anlatim.bloklar:
        tur, icerik, etiket = blok
        if etiket == "kural" or etiket == "python":
            continue
        if tur == "md" and icerik.startswith("###"):
            continue
        anl.bloklar.append(blok)
    us = alt.deger
    u = sp.zeros(n, 1)
    for idx, i in enumerate(serbest):
        u[i - 1, 0] = us[idx, 0]
    anl.metin("Tüm yer değiştirme vektörü (sabit serbestliklere 0 yazılır):")
    anl.mat(rf"\mathbf{{{bilinmeyen}}} = {LM(u)}")
    R = _sade(MK * u - MF)
    anl.metin("Mesnet tepkileri $\\mathbf{R} = \\mathbf{K}\\mathbf{u} - \\mathbf{F}$ (sabit serbestliklerdeki değerler tepkidir):")
    anl.mat(rf"\mathbf{{R}} = {LM(MK)}{LM(u)} - {LM(MF)} = {LM(R)}")
    anl.sonuc(rf"\mathbf{{{bilinmeyen}}} = {LM(u)},\qquad \mathbf{{R}} = {LM(R)}")
    semb = _sembolik_mi(MK, MF)
    kod = _kod_baslangic(semb, MK, MF)
    if semb:
        kod += [_sp_kodu(kad, MK), _sp_kodu(fad, MF), f"serbest = {[i-1 for i in serbest]}  # Python 0'dan sayar",
                f"Ks = {kad}.extract(serbest, serbest)", f"Fs = {fad}.extract(serbest, [0])",
                "us = sp.simplify(Ks.LUsolve(Fs))", f"u = sp.zeros({n}, 1)",
                "for i, d in enumerate(serbest): u[d] = us[i]", f"R = sp.simplify({kad}*u - {fad})",
                "sp.pprint(u)", "sp.pprint(R)"]
    else:
        kod += [_np_kodu(kad, MK), _np_kodu(fad, MF), f"serbest = {[i-1 for i in serbest]}  # Python 0'dan sayar",
                f"Ks = {kad}[np.ix_(serbest, serbest)]", f"Fs = {fad}[serbest]",
                "us = np.linalg.solve(Ks, Fs)", f"u = np.zeros(({n}, 1))", "u[serbest] = us",
                f"R = {kad} @ u - {fad}", "print('u ='); print(u)", "print('R ='); print(R)"]
    kd, ck = _python_bolumu(anl, kod)
    return _bitir(u, anl, bilinmeyen, goster, kd, ck)


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
"""


def yardim():
    """Fonksiyon listesi."""
    if _IPYTHON:
        display(Markdown(YARDIM_METNI))
    else:
        print(YARDIM_METNI)
