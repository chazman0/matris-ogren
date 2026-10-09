# -*- coding: utf-8 -*-
"""matris_ogren motor testleri (pytest).

Kapsam: girdi ayrıştırma, temel işlemler (sympy ile karşılaştırma, tohumlu rastgele matrisler),
determinant / ters / denklem çözümü / özdeğer, sonlu elemanlar yardımcıları (çubuk, kiriş, kafes,
birleştirme, sınır koşulu), üretilen Python kodu ve çıktısı, gösterim ayarları, hata durumları.

Çalıştırma (proje klasöründen):
  uv run --python 3.13 --with sympy --with numpy --with pytest python -m pytest testler -q
"""
from __future__ import annotations

import contextlib
import io
import random
import re

import numpy as np
import pytest
import sympy as sp

import matris_ogren as mo

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
_SAYI = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
_SAYISAL_SATIR = re.compile(r"^[\s\[\]\d.+\-,]*$")

A12 = sp.Matrix([[1, 2], [3, 4]])
B12 = sp.Matrix([[5, 6], [7, 8]])
M3 = sp.Matrix([[2, 1, 0], [1, 3, 1], [0, 1, 4]])
M4 = sp.Matrix([[2, 1, 0, 1], [1, 3, 1, 0], [0, 1, 4, 1], [1, 0, 1, 5]])
K_IKI_CUBUK = sp.Matrix([[20000, -20000, 0], [-20000, 30000, -10000], [0, -10000, 10000]])

BOYUTLAR = [pytest.param(n, t, id=f"{n}x{n}-tohum{t}") for n in (2, 3, 4, 5) for t in (1, 2)]


def sayilar(metin: str) -> list[float]:
    """Metindeki bütün sayıları (float olarak) sırayla döndürür."""
    return [float(t) for t in _SAYI.findall(metin)]


def bas_sayilar(cikti: str) -> list[float]:
    """Python çıktısının başındaki, yalnız sayı/köşeli ayraç içeren satırlardaki sayılar
    (ilk etiket satırında — 'True', 'saglama ...', 'boyut: ...' — durur)."""
    toplanan: list[float] = []
    basladi = False
    for satir in cikti.splitlines():
        if not satir.strip():
            if basladi:
                break
            continue
        if _SAYISAL_SATIR.match(satir):
            basladi = True
            toplanan.extend(sayilar(satir))
        else:
            break
    return toplanan


def duz(deger) -> list[float]:
    """sympy sonucu (matris ya da skaler) satır satır float listesine çevirir."""
    if isinstance(deger, sp.MatrixBase):
        return [float(v) for v in deger]
    return [float(deger)]


def anlatim_metni(r: "mo.Sonuc", etiket: str | None = None) -> str:
    """Anlatımın Python bloğu dışındaki (md + math) içeriği; etiket verilirse yalnız o etiketli bloklar.
    (Python çıktısındaki numpy ondalıkları gösterim testlerini yanıltmasın diye kullanılır.)"""
    parcalar = []
    for tur, icerik, et in r.anlatim.bloklar:
        if tur == "kod" or (etiket is not None and et != etiket):
            continue
        parcalar.append(str(icerik))
    return "\n".join(parcalar)


def karmasik_sayilar(metin: str) -> list[float]:
    """numpy'nin yazdırdığı '[3.+0.j 1.+0.j]' ya da '[3. 1.]' biçimindeki listeyi gerçel kısımlara çevirir."""
    return [complex(t).real for t in metin.strip().strip("[]").split()]


def rastgele(n: int, m: int | None = None, *, tohum: int = 0, kesirli: bool = True, duzenli: bool = False) -> sp.Matrix:
    """Tohumlu rastgele matris (Rational elemanlı). duzenli=True → det ≠ 0 garantili (kare)."""
    rnd = random.Random(tohum)
    m = n if m is None else m
    for _ in range(200):
        if kesirli:
            M = sp.Matrix(n, m, lambda i, j: sp.Rational(rnd.randint(-6, 6), rnd.choice([1, 1, 2, 3])))
        else:
            M = sp.Matrix(n, m, lambda i, j: sp.Integer(rnd.randint(-6, 6)))
        if not duzenli or (M.is_square and M.det() != 0):
            return M
    raise RuntimeError("düzenli rastgele matris üretilemedi")


def sifir_mi(M) -> bool:
    M = sp.sympify(M)
    if isinstance(M, sp.MatrixBase):
        return all(sp.simplify(x) == 0 for x in M)
    return sp.simplify(M) == 0


def ayni_liste(l1, l2) -> bool:
    return len(l1) == len(l2) and all(sp.simplify(sp.sympify(a) - sp.sympify(b)) == 0 for a, b in zip(l1, l2))


def ozdeger_listesi(A: sp.Matrix) -> list:
    """sympy özdeğerleri, çarpanlarına (katlılığına) göre tekrarlı, (re, im) sırasıyla."""
    liste = []
    for lam, kat in A.eigenvals().items():
        liste.extend([lam] * kat)
    return sorted(liste, key=lambda t: (sp.re(t), sp.im(t)))


def kodu_calistir(kod: str) -> str:
    tampon = io.StringIO()
    alan = {"__name__": "__test_kod__"}
    with contextlib.redirect_stdout(tampon):
        exec(compile(kod, "<test_kod>", "exec"), alan)  # noqa: S102
    return tampon.getvalue().rstrip("\n")


# ===========================================================================
# 1. Girdi ayrıştırma (matris)
# ===========================================================================
@pytest.mark.parametrize("girdi", [
    pytest.param("1 2; 3 4", id="bosluk-noktali-virgul"),
    pytest.param("1,2;3,4", id="virgul"),
    pytest.param("1, 2; 3, 4", id="virgul-bosluk"),
    pytest.param("1 2\n3 4", id="cok-satirli"),
    pytest.param("  1 2 \r\n 3 4 \n", id="cok-satirli-bosluklu"),
    pytest.param("[[1,2],[3,4]]", id="liste-metni"),
    pytest.param("[[1, 2], [3, 4]]", id="liste-metni-bosluklu"),
    pytest.param([[1, 2], [3, 4]], id="liste"),
    pytest.param(((1, 2), (3, 4)), id="demet"),
    pytest.param(np.array([[1, 2], [3, 4]]), id="numpy-int"),
    pytest.param(np.array([[1.0, 2.0], [3.0, 4.0]]), id="numpy-float"),
    pytest.param(sp.Matrix([[1, 2], [3, 4]]), id="sympy"),
])
def test_matris_ayristirma(girdi):
    M = mo.matris(girdi)
    assert isinstance(M, sp.Matrix)
    assert M == A12


def test_duz_liste_sutun_vektoru():
    M = mo.matris([1, 2, 3])
    assert M.shape == (3, 1)
    assert M == sp.Matrix([1, 2, 3])


def test_numpy_tek_boyut_sutun_vektoru():
    M = mo.matris(np.array([1.5, 2]))
    assert M.shape == (2, 1)
    assert M == sp.Matrix([sp.Rational(3, 2), 2])


def test_sonuc_girdi_olarak():
    r = mo.carp("1 2; 3 4", "5 6; 7 8")
    assert mo.matris(r) == A12 * B12
    assert mo.transpoz(r).deger == (A12 * B12).T


def test_skaler_girdi_1x1():
    assert mo.matris(5) == sp.Matrix([[5]])
    assert mo.matris(2.5) == sp.Matrix([[sp.Rational(5, 2)]])
    assert mo.matris(sp.Symbol("k")) == sp.Matrix([[sp.Symbol("k")]])


@pytest.mark.parametrize("metin, beklenen", [
    pytest.param("1/2", sp.Rational(1, 2), id="kesir"),
    pytest.param("-3/4", sp.Rational(-3, 4), id="negatif-kesir"),
    pytest.param("0.5", sp.Rational(1, 2), id="ondalik"),
    pytest.param("2.5", sp.Rational(5, 2), id="ondalik-2.5"),
    pytest.param(".25", sp.Rational(1, 4), id="ondalik-noktayla"),
    pytest.param("-3", sp.Integer(-3), id="negatif-tam"),
    pytest.param("sqrt(2)", sp.sqrt(2), id="sqrt"),
    pytest.param("sqrt(2)/2", sp.sqrt(2) / 2, id="sqrt-bolu"),
    pytest.param("E*A/L", sp.Symbol("E") * sp.Symbol("A") / sp.Symbol("L"), id="EA/L"),
    pytest.param("2*E*I/L^3", 2 * sp.Symbol("E") * sp.Symbol("I") / sp.Symbol("L") ** 3, id="EI/L^3-sapka"),
    pytest.param("2*E*I/L**3", 2 * sp.Symbol("E") * sp.Symbol("I") / sp.Symbol("L") ** 3, id="EI/L^3-yildiz"),
    pytest.param("sin(30*pi/180)", sp.Rational(1, 2), id="sin30"),
    pytest.param("cos(60*pi/180)", sp.Rational(1, 2), id="cos60"),
    pytest.param("pi", sp.pi, id="pi"),
    pytest.param("k", sp.Symbol("k"), id="tek-sembol"),
])
def test_eleman_ayristirma(metin, beklenen):
    M = mo.matris(metin)
    assert M.shape == (1, 1)
    assert sp.simplify(M[0, 0] - beklenen) == 0


def test_ondalik_kesin_rational_saklanir():
    x = mo.matris("0.1")[0, 0]
    assert x.is_Rational and x == sp.Rational(1, 10)
    assert not isinstance(x, sp.Float)
    M = mo.matris("0.5 1.25; 2 3")
    assert M == sp.Matrix([[sp.Rational(1, 2), sp.Rational(5, 4)], [2, 3]])


def test_E_I_N_harfleri_sembol_olur():
    """sympy'de E = Euler sayısı, I = sanal birim, N = sayısal değerlendirme; burada sembol olmalı."""
    M = mo.matris("E, I, N")
    assert M.free_symbols == {sp.Symbol("E"), sp.Symbol("I"), sp.Symbol("N")}
    assert sp.E not in M and sp.I not in M
    assert M[0, 1].is_Symbol


def test_sembolik_matris_bosluksuz():
    M = mo.matris("E*A/L -E*A/L; -E*A/L E*A/L")
    E, A, L = sp.symbols("E A L")
    assert sifir_mi(M - E * A / L * sp.Matrix([[1, -1], [-1, 1]]))


@pytest.mark.parametrize("girdi", [
    pytest.param("1 $; 3 4", id="gecersiz-karakter"),
    pytest.param("1 2; 3 x'y", id="tirnak"),
    pytest.param("1 2; 3 __import__(os)", id="import"),
    pytest.param("1 2; 3", id="satir-uzunluklari-farkli"),
    pytest.param("[[1,2],[3]]", id="liste-metni-farkli"),
    pytest.param("1 2; a b c", id="sembolik-farkli-uzunluk"),
    pytest.param("", id="bos"),
    pytest.param("   ", id="bosluk"),
    pytest.param([], id="bos-liste"),
    pytest.param("1 2; 3 import", id="anahtar-kelime"),
    pytest.param(object(), id="anlasilmayan-tip"),
])
def test_gecersiz_girdi(girdi):
    with pytest.raises(mo.MatrisHatasi):
        mo.matris(girdi)


def test_matris_hatasi_valueerror():
    assert issubclass(mo.MatrisHatasi, ValueError)


# ===========================================================================
# 2. Temel işlemler: topla, cikar, skaler, carp, transpoz, iz, rank
# ===========================================================================
@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_topla_cikar_rastgele(n, tohum):
    A = rastgele(n, tohum=tohum)
    B = rastgele(n, tohum=tohum + 100)
    assert mo.topla(A, B).deger == A + B
    assert mo.cikar(A, B).deger == A - B


def test_topla_cikar_bilinen():
    assert mo.topla("1 2; 3 4", "5 6; 7 8").deger == sp.Matrix([[6, 8], [10, 12]])
    assert mo.cikar("1 2; 3 4", "5 6; 7 8").deger == sp.Matrix([[-4, -4], [-4, -4]])
    assert mo.topla("0.5 1.25; 2 3", "1 1; 1 1").deger == sp.Matrix([[sp.Rational(3, 2), sp.Rational(9, 4)], [3, 4]])


@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_skaler_rastgele(n, tohum):
    A = rastgele(n, tohum=tohum)
    assert mo.skaler("3/2", A).deger == sp.Rational(3, 2) * A
    assert mo.skaler(-2, A).deger == -2 * A
    assert mo.skaler(0.5, A).deger == A / 2


def test_skaler_sembolik():
    k = sp.Symbol("k")
    r = mo.skaler("k", "1 2; 3 4")
    assert r.deger == k * A12
    assert sifir_mi(mo.skaler("E*A/L", "1 -1; -1 1").deger - mo.cubuk_eleman().deger)


@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_carp_kare_rastgele(n, tohum):
    A = rastgele(n, tohum=tohum)
    B = rastgele(n, tohum=tohum + 100, kesirli=False)
    r = mo.carp(A, B)
    assert r.deger == A * B
    assert r.ad == "C"


@pytest.mark.parametrize("m, n, p", [(2, 3, 2), (3, 2, 4), (1, 4, 1), (4, 1, 3), (2, 3, 1)])
def test_carp_dikdortgen(m, n, p):
    A = rastgele(m, n, tohum=m * 10 + n)
    B = rastgele(n, p, tohum=n * 10 + p)
    r = mo.carp(A, B)
    assert r.deger.shape == (m, p)
    assert r.deger == A * B


def test_carp_bilinen():
    assert mo.carp("1 2; 3 4", "5 6; 7 8").deger == sp.Matrix([[19, 22], [43, 50]])
    assert mo.carp("1 2 3; 4 5 6", "1; 2; 3").deger == sp.Matrix([[14], [32]])
    assert mo.carp(np.array([[1, 2], [3, 4]]), np.array([[1], [1]])).deger == sp.Matrix([[3], [7]])


def test_carp_zincir_uclu():
    A = rastgele(2, 3, tohum=5)
    B = rastgele(3, 4, tohum=6)
    C = rastgele(4, 2, tohum=7)
    r = mo.carp(A, B, C)
    assert r.deger.shape == (2, 2)
    assert r.deger == A * B * C
    assert r.ad == "ABC"
    assert "AB" in r.python_kodu and "ABC" in r.python_kodu


def test_carp_dortlu_zincir():
    r = mo.carp("1 2; 3 4", "5 6; 7 8", "1 0; 0 1", "2 0; 0 2")
    assert r.deger == A12 * B12 * 2


def test_carp_sembolik():
    E, A, L = sp.symbols("E A L")
    r = mo.carp("E*A/L, -E*A/L; -E*A/L, E*A/L", "1; 0")
    assert sifir_mi(r.deger - sp.Matrix([E * A / L, -E * A / L]))
    k = sp.Symbol("k")
    assert mo.carp("k 0; 0 k", "1; 2").deger == sp.Matrix([k, 2 * k])


def test_carp_adlar():
    r = mo.carp("1 2; 3 4", "1; 1", adlar=("K", "u"))
    md = r.anlatim.markdown()
    assert r"\mathbf{K}" in md and r"\mathbf{u}" in md
    assert "K = np.array" in r.python_kodu


@pytest.mark.parametrize("m, n", [(2, 3), (3, 3), (4, 2), (1, 5), (5, 1)])
def test_transpoz_rastgele(m, n):
    A = rastgele(m, n, tohum=m * 7 + n)
    r = mo.transpoz(A)
    assert r.deger.shape == (n, m)
    assert r.deger == A.T
    assert mo.transpoz(r).deger == A  # (A^T)^T = A


def test_transpoz_bilinen_ve_simetri():
    assert mo.transpoz("1 2 3; 4 5 6").deger == sp.Matrix([[1, 4], [2, 5], [3, 6]])
    assert mo.transpoz([[1, 2], [3, 4]]).deger == A12.T
    md_sim = mo.transpoz("2 1; 1 3").anlatim.markdown()
    assert "**simetrik**" in md_sim
    md_asim = mo.transpoz("1 2; 3 4").anlatim.markdown()
    assert "simetrik değil" in md_asim


@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_iz_rastgele(n, tohum):
    A = rastgele(n, tohum=tohum)
    assert mo.iz(A).deger == A.trace()


def test_iz_bilinen():
    r = mo.iz("2 1; 1 3")
    assert r.deger == 5
    assert r.ad == "tr"
    a, d = sp.symbols("a d")
    assert mo.iz("a b; c d").deger == a + d


@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_rank_rastgele(n, tohum):
    A = rastgele(n, tohum=tohum)
    assert mo.rank(A).deger == A.rank()


@pytest.mark.parametrize("girdi, beklenen", [
    ("1 2; 2 4", 1), ("1 2 3; 4 5 6; 7 8 9", 2), ("0 0; 0 0", 0), ("1 2 3; 4 5 6", 2), ("1; 2; 3", 1),
    ("1 0 0; 0 1 0; 0 0 1", 3), ("k -k; -k k", 1),
])
def test_rank_bilinen(girdi, beklenen):
    r = mo.rank(girdi)
    assert r.deger == beklenen
    assert isinstance(r.deger, sp.Integer)


def test_rank_tekil_metni():
    md = mo.rank("1 2; 2 4").anlatim.markdown()
    assert "tekil" in md
    md2 = mo.rank("1 0; 0 1").anlatim.markdown()
    assert "tam ranklı" in md2


# ===========================================================================
# 3. Determinant
# ===========================================================================
@pytest.mark.parametrize("yontem", ["kofaktor", "eliminasyon"])
@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_determinant_rastgele(n, tohum, yontem):
    A = rastgele(n, tohum=tohum)
    r = mo.determinant(A, yontem=yontem)
    assert r.deger == A.det()
    assert r.ad == "det"


@pytest.mark.parametrize("girdi, beklenen", [
    ("4 7; 2 6", 10), ("2 1 0; 1 3 1; 0 1 4", 18), ("1 2; 2 4", 0), ("5", 5), ("1 0; 0 1", 1),
    ("1/2 1/3; 1/4 1/5", sp.Rational(1, 10) - sp.Rational(1, 12)),
])
def test_determinant_bilinen(girdi, beklenen):
    assert mo.determinant(girdi).deger == beklenen


def test_determinant_4x4_her_iki_yontem():
    assert mo.determinant(M4).deger == M4.det()
    assert mo.determinant(M4, yontem="kofaktor").deger == M4.det()
    assert mo.determinant(M4, yontem="eliminasyon").deger == M4.det()


def test_determinant_sembolik():
    a, b, c, d = sp.symbols("a b c d")
    assert sp.expand(mo.determinant("a b; c d").deger - (a * d - b * c)) == 0
    k = sp.Symbol("k")
    assert sp.simplify(mo.determinant("k -k; -k 2*k").deger - k**2) == 0
    assert sp.simplify(mo.determinant("k -k; -k k").deger) == 0


def test_determinant_varsayilan_yontem_metni():
    md2 = mo.determinant("4 7; 2 6").anlatim.markdown()
    assert "çapraz çarpımların farkı" in md2
    md3 = mo.determinant("2 1 0; 1 3 1; 0 1 4").anlatim.markdown()
    assert "Sarrus" in md3 and "Minörler" in md3
    md4 = mo.determinant(M4).anlatim.markdown()
    assert "Satır indirgeme yöntemi" in md4


def test_determinant_pivot_sifir_satir_degisimi():
    A = sp.Matrix([[0, 1, 2], [1, 0, 3], [4, 5, 6]])
    r = mo.determinant(A, yontem="eliminasyon")
    assert r.deger == A.det()
    md = r.anlatim.markdown()
    assert "satır değiştirilir" in md and r"\leftrightarrow" in md
    assert "Satır değiştirme sayısı: 1" in md


def test_determinant_iki_satir_degisimi():
    A = sp.Matrix([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
    r = mo.determinant(A, yontem="eliminasyon")
    assert r.deger == -1


def test_determinant_tekil():
    r = mo.determinant("1 2; 2 4")
    assert r.deger == 0
    assert "tekil" in r.anlatim.markdown()
    assert "düzenli" in mo.determinant("1 2; 3 4").anlatim.markdown()


# ===========================================================================
# 4. Ters
# ===========================================================================
@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_ters_gauss_rastgele(n, tohum):
    A = rastgele(n, tohum=tohum, duzenli=True)
    r = mo.ters(A, yontem="gauss")
    assert r.deger == A.inv()
    assert A * r.deger == sp.eye(n)


@pytest.mark.parametrize("tohum", [1, 2, 3, 4])
def test_ters_formul_2x2(tohum):
    A = rastgele(2, tohum=tohum, duzenli=True)
    r = mo.ters(A, yontem="formul")
    assert r.deger == A.inv()


def test_ters_bilinen():
    assert mo.ters("4 7; 2 6").deger == sp.Matrix([[sp.Rational(3, 5), sp.Rational(-7, 10)], [sp.Rational(-1, 5), sp.Rational(2, 5)]])
    assert mo.ters(M3).deger == M3.inv()
    assert mo.ters("4 7; 2 6", yontem="gauss").deger == sp.Matrix([[4, 7], [2, 6]]).inv()


def test_ters_varsayilan_yontem_metni():
    md2 = mo.ters("4 7; 2 6").anlatim.markdown()
    assert "2×2 formülü" in md2
    md3 = mo.ters(M3).anlatim.markdown()
    assert "Gauss" in md3 and r"\mathbf{I}" in md3


def test_ters_sembolik():
    a, b, c, d = sp.symbols("a b c d")
    A = sp.Matrix([[a, b], [c, d]])
    r = mo.ters("a b; c d")
    assert sifir_mi(r.deger - A.inv())
    assert sifir_mi(sp.simplify(A * r.deger) - sp.eye(2))


def test_ters_pivot_sifir():
    r = mo.ters("0 1; 1 0", yontem="gauss")
    assert r.deger == sp.Matrix([[0, 1], [1, 0]])
    assert "satır değiştirilir" in r.anlatim.markdown()


def test_ters_tekil_hata():
    with pytest.raises(mo.MatrisHatasi, match="tekil"):
        mo.ters("1 2; 2 4")


# ===========================================================================
# 5. Denklem sistemi çözümü (coz)
# ===========================================================================
@pytest.mark.parametrize("yontem", ["gauss", "ters"])
@pytest.mark.parametrize("n, tohum", BOYUTLAR)
def test_coz_rastgele(n, tohum, yontem):
    A = rastgele(n, tohum=tohum, duzenli=True)
    b = rastgele(n, 1, tohum=tohum + 50, kesirli=False)
    r = mo.coz(A, b, yontem=yontem)
    assert r.deger == A.LUsolve(b)
    assert A * r.deger == b
    assert r.ad == "x"


@pytest.mark.parametrize("n, tohum", [pytest.param(n, t, id=f"{n}x{n}-tohum{t}") for n in (1, 2, 3) for t in (1, 2)])
def test_coz_cramer(n, tohum):
    A = rastgele(n, tohum=tohum, duzenli=True)
    b = rastgele(n, 1, tohum=tohum + 50, kesirli=False)
    r = mo.coz(A, b, yontem="cramer")
    assert r.deger == A.LUsolve(b)
    assert "Cramer" in r.anlatim.markdown()


def test_coz_bilinen():
    beklenen = sp.Matrix([sp.Rational(4, 5), sp.Rational(7, 5)])
    assert mo.coz("2 1; 1 3", "3; 5").deger == beklenen
    assert mo.coz("2 1; 1 3", "3; 5", yontem="cramer").deger == beklenen
    assert mo.coz("2 1; 1 3", "3; 5", yontem="ters").deger == beklenen
    assert mo.coz(M3, "1; 2; 3").deger == M3.LUsolve(sp.Matrix([1, 2, 3]))
    assert mo.coz("2", "6").deger == sp.Matrix([3])


def test_coz_b_satir_vektoru():
    assert mo.coz("2 1; 1 3", "3 5").deger == mo.coz("2 1; 1 3", "3; 5").deger
    assert mo.coz("2 1; 1 3", [3, 5]).deger == mo.coz("2 1; 1 3", "3; 5").deger


def test_coz_pivot_sifir():
    r = mo.coz("0 1; 1 0", "7; 9")
    assert r.deger == sp.Matrix([9, 7])
    assert "satır değiştirilir" in r.anlatim.markdown()
    r3 = mo.coz("0 1 2; 1 0 3; 4 5 6", "1; 2; 3")
    A = sp.Matrix([[0, 1, 2], [1, 0, 3], [4, 5, 6]])
    assert r3.deger == A.LUsolve(sp.Matrix([1, 2, 3]))


def test_coz_tutarsiz_hata():
    with pytest.raises(mo.MatrisHatasi, match="tutarsız"):
        mo.coz("1 2; 2 4", "3; 7")
    with pytest.raises(mo.MatrisHatasi):
        mo.coz("1 2; 2 4", "3; 7", yontem="cramer")
    with pytest.raises(mo.MatrisHatasi):
        mo.coz("1 2; 2 4", "3; 7", yontem="ters")


def test_coz_sonsuz_cozum_linsolve():
    A = sp.Matrix([[1, 2], [2, 4]])
    b = sp.Matrix([3, 6])
    r = mo.coz(A, b)
    x1, x2 = sp.symbols("x1:3")
    assert r.deger == sp.linsolve((A, b), x1, x2)
    assert isinstance(r.deger, sp.FiniteSet)
    (cozum,) = r.deger
    v = sp.Matrix(cozum)
    assert sifir_mi(A * v - b)
    md = r.anlatim.markdown()
    assert "sonsuz çözüm" in md and "sınır koşulları" in md
    assert "linsolve" in r.python_kodu
    assert "x2" in r.python_ciktisi and "[Hata" not in r.python_ciktisi


def test_coz_sonsuz_cozum_3x3():
    A = sp.Matrix([[1, 1, 1], [1, 1, 1], [0, 0, 1]])
    b = sp.Matrix([2, 2, 1])
    r = mo.coz(A, b)
    x = sp.symbols("x1:4")
    assert r.deger == sp.linsolve((A, b), *x)


def test_coz_sembolik():
    k, P = sp.symbols("k P")
    r = mo.coz("k -k; -k 2*k", "0; P", bilinmeyen="u")
    assert sifir_mi(r.deger - sp.Matrix([P / k, P / k]))
    assert r.ad == "u"
    md = r.anlatim.markdown()
    assert "u_{1}" in md and "u_{2}" in md
    assert "sp.symbols" in r.python_kodu and "LUsolve" in r.python_kodu


def test_coz_sembolik_sonsuz():
    k, P = sp.symbols("k P")
    r = mo.coz("k -k; -k k", "P; -P", bilinmeyen="u")
    u = sp.symbols("u1:3")
    assert r.deger == sp.linsolve((sp.Matrix([[k, -k], [-k, k]]), sp.Matrix([P, -P])), *u)


def test_coz_adlar_ve_saglama_metni():
    r = mo.coz("2 1; 1 3", "3; 5", adlar=("K", "F"), bilinmeyen="u")
    md = r.anlatim.markdown()
    assert r"\mathbf{K}" in md and r"\mathbf{F}" in md and "Sağlama" in md
    assert "K = np.array" in r.python_kodu and "np.linalg.solve(K, F)" in r.python_kodu


# ===========================================================================
# 6. Özdeğer / özvektör
# ===========================================================================
@pytest.mark.parametrize("girdi", [
    pytest.param("2 1; 1 2", id="2x2-simetrik"),
    pytest.param("4 1; 2 3", id="2x2-simetrik-degil"),
    pytest.param("2 0; 0 2", id="2x2-katli"),
    pytest.param("1 1; 1 0", id="2x2-irrasyonel"),
    pytest.param("2 0 0; 0 3 4; 0 4 9", id="3x3-simetrik"),
    pytest.param("2 0 0; 0 2 0; 0 0 5", id="3x3-katli"),
    pytest.param("1 2 0; 2 1 0; 0 0 3", id="3x3-katli-blok"),
    pytest.param("3 0 0; 0 1/2 0; 0 0 -1", id="3x3-kesirli"),
])
def test_ozdeger_degerler_ve_vektorler(girdi):
    A = mo.matris(girdi)
    r = mo.ozdeger(A)
    ozd, vekt = r.deger
    assert len(ozd) == A.rows
    assert ayni_liste(ozd, ozdeger_listesi(A))      # çarpanlara (katlılığa) göre aynı
    assert sp.simplify(sum(ozd) - A.trace()) == 0   # iz = özdeğer toplamı
    toplam_vektor = 0
    for lam, vs in vekt:
        assert vs, f"λ={lam} için özvektör yok"
        for v in vs:
            assert v.shape == (A.rows, 1)
            assert not sifir_mi(v)
            assert sifir_mi(A * v - lam * v)          # A v = λ v
            toplam_vektor += 1
    assert toplam_vektor == A.rows                  # köşegenleştirilebilir örnekler
    assert r.ad == "lambda"


def test_ozdeger_2x2_bilinen():
    r = mo.ozdeger("2 1; 1 2")
    ozd, vekt = r.deger
    assert ozd == [1, 3]
    md = r.anlatim.markdown()
    # p(λ) = λ² − 4λ + 3 = (λ − 3)(λ − 1): sympy çarpanları \left( \right) ile sarar, sırası serbesttir
    assert r"p(\lambda)" in md and r"\lambda - 1" in md and r"\lambda - 3" in md
    assert r"\lambda^{2} - 4 \lambda + 3" in md
    assert r"\lambda_{1} = 1" in md and r"\lambda_{2} = 3" in md
    sozluk = {lam: vs for lam, vs in vekt}
    assert sifir_mi(sozluk[1][0] - sp.Matrix([-1, 1])) or sifir_mi(sozluk[1][0] + sp.Matrix([-1, 1]))
    assert sifir_mi(sozluk[3][0] - sp.Matrix([1, 1])) or sifir_mi(sozluk[3][0] + sp.Matrix([1, 1]))


def test_ozdeger_3x3_simetrik_bilinen():
    ozd, vekt = mo.ozdeger("2 0 0; 0 3 4; 0 4 9").deger
    assert ozd == [1, 2, 11]
    assert len(vekt) == 3


def test_ozdeger_irrasyonel():
    r = mo.ozdeger("1 1; 1 0")
    ozd, _ = r.deger
    assert ayni_liste(ozd, [(1 - sp.sqrt(5)) / 2, (1 + sp.sqrt(5)) / 2])
    md = r.anlatim.markdown()
    assert r"\sqrt{5}" in md and r"\approx" in md


def test_ozdeger_genellestirilmis_K_M():
    K = sp.Matrix([[2, -1], [-1, 1]])
    M = sp.Matrix([[2, 0], [0, 1]])
    r = mo.ozdeger(K, M)
    ozd, vekt = r.deger
    assert ayni_liste(ozd, [1 - sp.sqrt(2) / 2, 1 + sp.sqrt(2) / 2])
    for lam, vs in vekt:
        for v in vs:
            assert sifir_mi(K * v - lam * M * v)     # K φ = λ M φ
    md = r.anlatim.markdown()
    assert r"\omega" in md and "doğal frekanslar" in md and r"\mathbf{K}" in md and r"\mathbf{M}" in md
    assert "frekanslar omega" in r.python_ciktisi and "[Hata" not in r.python_ciktisi


def test_ozdeger_genellestirilmis_birim_M():
    r = mo.ozdeger("2 -1; -1 1", "1 0; 0 1")
    ozd, _ = r.deger
    assert ayni_liste(ozd, [(3 - sp.sqrt(5)) / 2, (3 + sp.sqrt(5)) / 2])


def test_ozdeger_ozvektor_kapali():
    ozd, vekt = mo.ozdeger("2 1; 1 2", ozvektor=False).deger
    assert ozd == [1, 3] and vekt == []


def test_ozdeger_4x4_sayisal_yol():
    A = sp.diag(1, 2, 3, 4)
    r = mo.ozdeger(A)
    ozd, vekt = r.deger
    assert sorted(ozd) == [1, 2, 3, 4]
    assert vekt == []
    assert "elle uzun olur" in r.anlatim.markdown()
    assert "np.linalg.eig" in r.python_kodu and "[Hata" not in r.python_ciktisi


def test_ozdeger_sembolik():
    a, b = sp.symbols("a b")
    ozd, _ = mo.ozdeger("a 0; 0 b").deger
    assert set(ozd) == {a, b}


# ===========================================================================
# 7. Sonlu elemanlar: cubuk, kiris, kafes, birlestir, sinir_kosulu
# ===========================================================================
def test_cubuk_eleman_sayisal():
    r = mo.cubuk_eleman(200000, 100, 1000)
    assert r.deger == 20000 * sp.Matrix([[1, -1], [-1, 1]])
    assert r.ad == "k"
    assert r.deger.det() == 0 and r.deger == r.deger.T
    assert mo.cubuk_eleman("200000", "100", "1000").deger == r.deger
    assert mo.cubuk_eleman(200000, 50, 1000).deger == 10000 * sp.Matrix([[1, -1], [-1, 1]])


def test_cubuk_eleman_sembolik():
    E, A, L = sp.symbols("E A L")
    r = mo.cubuk_eleman()
    assert sifir_mi(r.deger - E * A / L * sp.Matrix([[1, -1], [-1, 1]]))
    assert r.deger.free_symbols == {E, A, L}
    r2 = mo.cubuk_eleman("2*E", "A", "L")
    assert sifir_mi(r2.deger - 2 * E * A / L * sp.Matrix([[1, -1], [-1, 1]]))
    assert "sp.symbols" in r.python_kodu


def test_kiris_eleman_sembolik():
    E, I, L = sp.symbols("E I L")
    k = mo.kiris_eleman().deger
    assert k.shape == (4, 4)
    assert sifir_mi(k - k.T)
    assert sp.simplify(k[0, 0] - 12 * E * I / L**3) == 0
    assert sp.simplify(k[0, 1] - 6 * E * I / L**2) == 0
    assert sp.simplify(k[0, 2] + 12 * E * I / L**3) == 0
    assert sp.simplify(k[1, 1] - 4 * E * I / L) == 0
    assert sp.simplify(k[1, 3] - 2 * E * I / L) == 0
    assert sp.simplify(k[1, 2] + 6 * E * I / L**2) == 0
    assert sp.simplify(k.det()) == 0  # mesnetsiz eleman tekil
    assert k.free_symbols == {E, I, L}


def test_kiris_eleman_sayisal():
    k = mo.kiris_eleman(200e3, 500, 2000).deger
    kat = sp.Rational(1, 80)  # E I / L^3
    L = 2000
    T = sp.Matrix([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L**2, -6 * L, 2 * L**2],
                   [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L**2, -6 * L, 4 * L**2]])
    assert k == kat * T
    assert k[0, 0] == sp.Rational(3, 20) and k[0, 1] == 150 and k[1, 1] == 200000 and k[1, 3] == 100000


def test_kafes_eleman_45_tam_kesir():
    k = mo.kafes_eleman(1, 1, 1, 45).deger
    assert k.shape == (4, 4)
    assert all(x.is_Rational and abs(x) == sp.Rational(1, 2) for x in k)
    y = sp.Rational(1, 2)
    assert k == sp.Matrix([[y, y, -y, -y], [y, y, -y, -y], [-y, -y, y, y], [-y, -y, y, y]])


def test_kafes_eleman_90():
    k = mo.kafes_eleman(1, 1, 1, 90).deger
    assert k == sp.Matrix([[0, 0, 0, 0], [0, 1, 0, -1], [0, 0, 0, 0], [0, -1, 0, 1]])


def test_kafes_eleman_0():
    k = mo.kafes_eleman(1, 1, 1, 0).deger
    assert k == sp.Matrix([[1, 0, -1, 0], [0, 0, 0, 0], [-1, 0, 1, 0], [0, 0, 0, 0]])


@pytest.mark.parametrize("aci", [0, 30, 45, 60, 90, 120, 180])
def test_kafes_eleman_kapali_formul(aci):
    E, A, L = 2, 3, 5
    k = mo.kafes_eleman(E, A, L, aci).deger
    c = sp.cos(sp.Integer(aci) * sp.pi / 180)
    s = sp.sin(sp.Integer(aci) * sp.pi / 180)
    beklenen = sp.Rational(E * A, L) * sp.Matrix([[c**2, c * s, -c**2, -c * s], [c * s, s**2, -c * s, -s**2],
                                                  [-c**2, -c * s, c**2, c * s], [-c * s, -s**2, c * s, s**2]])
    assert sifir_mi(k - beklenen)
    assert sifir_mi(k - k.T)


def test_kafes_eleman_sembolik_30():
    E, A, L = sp.symbols("E A L")
    k = mo.kafes_eleman("E", "A", "L", 30).deger
    assert sp.simplify(k[0, 0] - sp.Rational(3, 4) * E * A / L) == 0
    assert sp.simplify(k[0, 1] - sp.sqrt(3) / 4 * E * A / L) == 0
    assert sp.simplify(k[1, 1] - sp.Rational(1, 4) * E * A / L) == 0
    assert sp.simplify(k[0, 2] + sp.Rational(3, 4) * E * A / L) == 0
    assert sifir_mi(k - k.T)


def test_birlestir_iki_cubuk():
    r = mo.birlestir([("20000 -20000; -20000 20000", [1, 2]), ("10000 -10000; -10000 10000", [2, 3])], 3)
    assert r.deger == K_IKI_CUBUK
    assert r.ad == "K"
    assert r.deger == r.deger.T and r.deger.det() == 0
    md = r.anlatim.markdown()
    assert "Eleman 1" in md and "Eleman 2" in md and "K_{22}" in md


def test_birlestir_sonuc_girdileri():
    k1 = mo.cubuk_eleman(200000, 100, 1000)
    k2 = mo.cubuk_eleman(200000, 50, 1000)
    r = mo.birlestir([(k1, [1, 2]), (k2, [2, 3])], 3)
    assert r.deger == K_IKI_CUBUK


def test_birlestir_sembolik():
    k = sp.Symbol("k")
    r = mo.birlestir([("k -k; -k k", [1, 2]), ("k -k; -k k", [2, 3])], 3)
    assert r.deger == sp.Matrix([[k, -k, 0], [-k, 2 * k, -k], [0, -k, k]])
    assert "sp.zeros(3, 3)" in r.python_kodu


def test_birlestir_farkli_sira_ve_bosluk():
    """Serbestlik numaraları ters sırada ve araya boş serbestlik gelince de doğru yerleşir."""
    k = sp.Symbol("k")
    r = mo.birlestir([("k -k; -k k", [3, 1])], 4)
    assert r.deger == sp.Matrix([[k, 0, -k, 0], [0, 0, 0, 0], [-k, 0, k, 0], [0, 0, 0, 0]])


def test_birlestir_kafes_4x4():
    k1 = mo.kafes_eleman(1, 1, 1, 0)
    k2 = mo.kafes_eleman(1, 1, 1, 90)
    r = mo.birlestir([(k1, [1, 2, 3, 4]), (k2, [3, 4, 5, 6])], 6)
    K = sp.zeros(6, 6)
    K[0:4, 0:4] += k1.deger
    K[2:6, 2:6] += k2.deger
    assert r.deger == K


def test_sinir_kosulu_iki_cubuk():
    r = mo.sinir_kosulu(K_IKI_CUBUK, [0, 0, 1000], sabit=[1])
    assert r.deger == sp.Matrix([0, sp.Rational(1, 20), sp.Rational(3, 20)])
    assert r.ad == "u"
    md = r.anlatim.markdown()
    assert "Mesnet tepkileri" in md and "İndirgenmiş sistem" in md
    assert "-1000" in md                       # R_1 = -1000 (mesnet tepkisi)
    assert "Sabit serbestlikler: [1]" in md
    assert "R =" in r.python_ciktisi and "-1000" in r.python_ciktisi
    assert "[Hata" not in r.python_ciktisi
    # K u − F sabit serbestlikte tepki verir, serbestlerde sıfırdır
    R = K_IKI_CUBUK * r.deger - sp.Matrix([0, 0, 1000])
    assert R == sp.Matrix([-1000, 0, 0])


def test_sinir_kosulu_F_bicimleri_ve_Sonuc():
    K = mo.birlestir([("20000 -20000; -20000 20000", [1, 2]), ("10000 -10000; -10000 10000", [2, 3])], 3)
    beklenen = sp.Matrix([0, sp.Rational(1, 20), sp.Rational(3, 20)])
    assert mo.sinir_kosulu(K, "0; 0; 1000", sabit=[1]).deger == beklenen
    assert mo.sinir_kosulu(K, "0 0 1000", sabit=[1]).deger == beklenen
    assert mo.sinir_kosulu(K.deger, np.array([0, 0, 1000]), sabit=[1]).deger == beklenen


def test_sinir_kosulu_iki_mesnet():
    """İki ucu sabit: yalnız ortadaki düğüm hareket eder."""
    r = mo.sinir_kosulu(K_IKI_CUBUK, [0, 3000, 0], sabit=[1, 3])
    assert r.deger == sp.Matrix([0, sp.Rational(3000, 30000), 0])
    R = K_IKI_CUBUK * r.deger - sp.Matrix([0, 3000, 0])
    assert R == sp.Matrix([-2000, 0, -1000])
    assert "Sabit serbestlikler: [1, 3]" in r.anlatim.markdown()


def test_sinir_kosulu_sembolik():
    k, P = sp.symbols("k P")
    K = mo.birlestir([("k -k; -k k", [1, 2]), ("k -k; -k k", [2, 3])], 3)
    r = mo.sinir_kosulu(K, "0; 0; P", sabit=[1])
    assert sifir_mi(r.deger - sp.Matrix([0, P / k, 2 * P / k]))
    R = sp.simplify(K.deger * r.deger - sp.Matrix([0, 0, P]))
    assert sifir_mi(R - sp.Matrix([-P, 0, 0]))
    assert "[Hata" not in r.python_ciktisi and r.python_ciktisi.strip()


# ===========================================================================
# 8. Üretilen Python kodu ve gerçek çıktısı
# ===========================================================================
SAYISAL_DURUMLAR = [
    ("topla", lambda: mo.topla("1 2; 3 4", "5 6; 7 8")),
    ("cikar", lambda: mo.cikar("1 2; 3 4", "5 6; 7 8")),
    ("skaler", lambda: mo.skaler("1/2", "1 2; 3 4")),
    ("carp", lambda: mo.carp("1 2 3; 4 5 6", "1; 2; 3")),
    ("carp_zincir", lambda: mo.carp("1 2; 3 4", "5 6; 7 8", "1 0; 0 1")),
    ("transpoz", lambda: mo.transpoz("1 2 3; 4 5 6")),
    ("transpoz_kare", lambda: mo.transpoz("2 1; 1 3")),
    ("iz", lambda: mo.iz("2 1; 1 3")),
    ("rank", lambda: mo.rank("1 2; 2 4")),
    ("determinant", lambda: mo.determinant("4 7; 2 6")),
    ("determinant_3x3", lambda: mo.determinant("2 1 0; 1 3 1; 0 1 4")),
    ("determinant_elim", lambda: mo.determinant(M4)),
    ("ters", lambda: mo.ters("4 7; 2 6")),
    ("ters_gauss", lambda: mo.ters(M3, yontem="gauss")),
    ("coz", lambda: mo.coz("2 1; 1 3", "3; 5")),
    ("coz_cramer", lambda: mo.coz("2 1; 1 3", "3; 5", yontem="cramer")),
    ("coz_ters", lambda: mo.coz("2 1; 1 3", "3; 5", yontem="ters")),
    ("coz_3x3", lambda: mo.coz(M3, "1; 2; 3")),
    ("cubuk", lambda: mo.cubuk_eleman(200000, 100, 1000)),
    ("kiris", lambda: mo.kiris_eleman(200e3, 500, 2000)),
    ("kafes45", lambda: mo.kafes_eleman(1, 1, 1, 45)),
    ("kafes90", lambda: mo.kafes_eleman(1, 1, 1, 90)),
    ("birlestir", lambda: mo.birlestir([("20000 -20000; -20000 20000", [1, 2]), ("10000 -10000; -10000 10000", [2, 3])], 3)),
]

SEMBOLIK_DURUMLAR = [
    ("topla", lambda: mo.topla("a b; c d", "1 2; 3 4")),
    ("cikar", lambda: mo.cikar("a b; c d", "1 2; 3 4")),
    ("skaler", lambda: mo.skaler("k", "1 2; 3 4")),
    ("carp", lambda: mo.carp("E*A/L, -E*A/L; -E*A/L, E*A/L", "1; 0")),
    ("carp_tek_sembol", lambda: mo.carp("k 0; 0 k", "1; 2")),
    ("transpoz", lambda: mo.transpoz("a b c; d e f")),
    ("iz", lambda: mo.iz("a b; c d")),
    ("rank", lambda: mo.rank("k -k; -k k")),
    ("determinant", lambda: mo.determinant("a b; c d")),
    ("determinant_3x3", lambda: mo.determinant("a 0 0; 0 b 0; 0 0 c")),
    ("ters", lambda: mo.ters("a b; c d")),
    ("ters_gauss", lambda: mo.ters("k 0; 0 2*k", yontem="gauss")),
    ("coz", lambda: mo.coz("k -k; -k 2*k", "0; P", bilinmeyen="u")),
    ("coz_sonsuz", lambda: mo.coz("k -k; -k k", "P; -P", bilinmeyen="u")),
    ("ozdeger", lambda: mo.ozdeger("a 0; 0 b")),
    ("cubuk", lambda: mo.cubuk_eleman()),
    ("kiris", lambda: mo.kiris_eleman()),
    ("kafes", lambda: mo.kafes_eleman("E", "A", "L", 30)),
    ("birlestir", lambda: mo.birlestir([("k -k; -k k", [1, 2]), ("k -k; -k k", [2, 3])], 3)),
    ("sinir_kosulu", lambda: mo.sinir_kosulu(
        mo.birlestir([("k -k; -k k", [1, 2]), ("k -k; -k k", [2, 3])], 3), "0; 0; P", sabit=[1])),
]


@pytest.mark.parametrize("ad, uret", SAYISAL_DURUMLAR, ids=[a for a, _ in SAYISAL_DURUMLAR])
def test_python_ciktisi_sayisal(ad, uret):
    r = uret()
    assert r.python_kodu.strip() and r.python_ciktisi.strip()
    assert "[Hata" not in r.python_ciktisi
    assert "import numpy as np" in r.python_kodu
    bulunan = bas_sayilar(r.python_ciktisi)
    beklenen = duz(r.deger)
    assert len(bulunan) == len(beklenen), f"çıktı:\n{r.python_ciktisi}"
    assert bulunan == pytest.approx(beklenen, rel=1e-3, abs=1e-3)


@pytest.mark.parametrize("ad, uret", SEMBOLIK_DURUMLAR, ids=[a for a, _ in SEMBOLIK_DURUMLAR])
def test_python_ciktisi_sembolik(ad, uret):
    r = uret()
    assert r.python_kodu.strip() and r.python_ciktisi.strip()
    assert "[Hata" not in r.python_ciktisi
    assert "import sympy as sp" in r.python_kodu and "sp.symbols" in r.python_kodu
    assert "numpy" not in r.python_kodu


@pytest.mark.parametrize("ad, uret", SAYISAL_DURUMLAR + SEMBOLIK_DURUMLAR,
                         ids=[a + "-sayisal" for a, _ in SAYISAL_DURUMLAR] + [a + "-sembolik" for a, _ in SEMBOLIK_DURUMLAR])
def test_python_kodu_yeniden_calisinca_ayni_cikti(ad, uret):
    """Gösterilen kod, gösterilen çıktıyı gerçekten üretiyor (Colab'da kopyala-çalıştır güvencesi)."""
    r = uret()
    assert kodu_calistir(r.python_kodu) == r.python_ciktisi


def test_python_ciktisi_ozdeger():
    r = mo.ozdeger("2 1; 1 2")
    satir = next(s for s in r.python_ciktisi.splitlines() if s.startswith("ozdegerler"))
    # np.linalg.eig karmaşık tip döndürebilir: "[3.+0.j 1.+0.j]" → gerçel kısımlar
    bulunan = sorted(karmasik_sayilar(satir.split(":", 1)[1]))
    assert bulunan == pytest.approx([1.0, 3.0], abs=1e-6)
    assert "ozvektorler" in r.python_ciktisi
    # özvektör sütunları ±(1,1)/√2 ve ±(−1,1)/√2 → mutlak değerleri hep 0.7071
    vekt_satirlari = r.python_ciktisi.split("ozvektorler (sutunlar):", 1)[1].strip().splitlines()
    mutlak = sorted(abs(v) for satir_ in vekt_satirlari for v in karmasik_sayilar(satir_))
    assert mutlak == pytest.approx([0.7071] * 4, abs=1e-3)


def test_python_ciktisi_sinir_kosulu():
    r = mo.sinir_kosulu(K_IKI_CUBUK, [0, 0, 1000], sabit=[1])
    ck = r.python_ciktisi
    u_blok = ck.split("u =", 1)[1].split("R =", 1)[0]
    R_blok = ck.split("R =", 1)[1]
    assert sayilar(u_blok) == pytest.approx([0.0, 0.05, 0.15], abs=1e-4)
    assert sayilar(R_blok) == pytest.approx([-1000.0, 0.0, 0.0], abs=1e-3)


def test_python_kodu_icerigi():
    assert "A @ B" in mo.carp("1 2; 3 4", "5 6; 7 8").python_kodu
    assert "np.linalg.det" in mo.determinant("4 7; 2 6").python_kodu
    assert "np.linalg.inv" in mo.ters("4 7; 2 6").python_kodu
    assert "np.linalg.solve" in mo.coz("2 1; 1 3", "3; 5").python_kodu
    assert "np.ix_" in mo.birlestir([("1 -1; -1 1", [1, 2])], 2).python_kodu
    assert "T.T @ k_yerel @ T" in mo.kafes_eleman(1, 1, 1, 45).python_kodu
    assert "A, E, L = sp.symbols('A E L')" in mo.cubuk_eleman().python_kodu


# ===========================================================================
# 9. Gösterim / ayarlar / Sonuc nesnesi
# ===========================================================================
def test_goster_yok_hicbir_sey_basmaz(capsys, monkeypatch):
    monkeypatch.setattr(mo, "_IPYTHON", False)
    mo.carp("1 2; 3 4", "5 6; 7 8")
    mo.coz("2 1; 1 3", "3; 5")
    mo.ozdeger("2 1; 1 2")
    mo.sinir_kosulu(K_IKI_CUBUK, [0, 0, 1000], sabit=[1])
    assert capsys.readouterr().out == ""


def test_goster_hepsi_metin_modu(capsys, monkeypatch):
    monkeypatch.setattr(mo, "_IPYTHON", False)
    mo.ayarla(goster="hepsi")
    mo.coz("2 1; 1 3", "3; 5")
    out = capsys.readouterr().out
    assert "Kural" in out and "Python ile" in out and "Sonuç" in out
    assert "```python" in out and "$$" in out and "Çıktı:" in out
    assert "Geri yerine koyma" in out


def test_goster_parametresi_ayari_gecer(capsys, monkeypatch):
    monkeypatch.setattr(mo, "_IPYTHON", False)
    mo.carp("1 2; 3 4", "5 6; 7 8", goster="hepsi")   # ayar "yok" ama parametre "hepsi"
    assert "Kural" in capsys.readouterr().out
    mo.ayarla(goster="hepsi")
    mo.carp("1 2; 3 4", "5 6; 7 8", goster="yok")     # ayar "hepsi" ama parametre "yok"
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("mod, olmali, olmamali", [
    ("adimlar", ["Kural", "Sonuç", "Her eleman"], ["Python ile"]),
    ("python", ["Python ile", "Sonuç", "```python"], ["Kural", "Her eleman"]),
    ("sonuc", ["Sonuç"], ["Kural", "Python ile", "Her eleman"]),
])
def test_goster_modlari(capsys, monkeypatch, mod, olmali, olmamali):
    monkeypatch.setattr(mo, "_IPYTHON", False)
    mo.carp("1 2; 3 4", "5 6; 7 8", goster=mod)
    out = capsys.readouterr().out
    for s in olmali:
        assert s in out, f"{mod}: {s!r} bekleniyordu"
    for s in olmamali:
        assert s not in out, f"{mod}: {s!r} olmamalıydı"


def test_ayar_python_kapali(capsys, monkeypatch):
    monkeypatch.setattr(mo, "_IPYTHON", False)
    mo.ayarla(python=False, goster="hepsi")
    r = mo.carp("1 2; 3 4", "5 6; 7 8")
    out = capsys.readouterr().out
    assert "Python ile" not in out and "Kural" in out
    assert r.python_kodu and r.python_ciktisi   # kod yine üretilir, yalnız gösterilmez


def test_ayar_kural_kapali(capsys, monkeypatch):
    monkeypatch.setattr(mo, "_IPYTHON", False)
    mo.ayarla(kural=False, goster="hepsi")
    mo.carp("1 2; 3 4", "5 6; 7 8")
    out = capsys.readouterr().out
    assert "Kural" not in out and "Python ile" in out


def test_ayar_en_fazla_eleman():
    mo.ayarla(en_fazla_eleman=4)
    md = mo.topla("1 2 3; 4 5 6", "1 1 1; 1 1 1").anlatim.markdown()
    assert "Matris büyük" in md and "Her eleman ayrı ayrı" not in md
    mo.ayarla(en_fazla_eleman=36)
    md2 = mo.topla("1 2 3; 4 5 6", "1 1 1; 1 1 1").anlatim.markdown()
    assert "Her eleman ayrı ayrı" in md2


def test_ondalik_gosterim():
    # Yalnız Sonuç bloğuna bakılır: 2×2 formül adımındaki 1/det(A) = \frac{1}{3} yapısal bir gösterimdir,
    # Python bloğundaki numpy çıktısı (0.3333) ise ayardan bağımsızdır.
    mo.ayarla(ondalik=True, basamak=3)
    r = mo.ters("3 0; 0 1")
    sonuc = anlatim_metni(r, "sonuc")
    assert "0.333" in sonuc and r"\frac{1}{3}" not in sonuc
    assert "0.333" in anlatim_metni(r)              # adımlarda da ondalık
    assert r.deger[0, 0] == sp.Rational(1, 3)      # hesap kesin kalır, yalnız gösterim ondalık
    mo.ayarla(basamak=5)
    assert "0.33333" in anlatim_metni(mo.ters("3 0; 0 1"), "sonuc")
    mo.ayarla(basamak=2)
    sonuc2 = anlatim_metni(mo.ters("3 0; 0 1"), "sonuc")
    assert "0.33" in sonuc2 and "0.333" not in sonuc2
    # determinant gibi skaler sonuçlar da ondalık yazılır
    mo.ayarla(basamak=4)
    assert "0.6667" in anlatim_metni(mo.determinant("1/3 0; 0 2"), "sonuc")


def test_ondalik_kapali_kesir_gosterir():
    r = mo.ters("3 0; 0 1")
    sonuc = anlatim_metni(r, "sonuc")
    assert r"\frac{1}{3}" in sonuc and "0.333" not in sonuc
    assert "0.333" not in anlatim_metni(r)         # adımlarda da kesir
    assert r"\frac{2}{3}" in anlatim_metni(mo.determinant("1/3 0; 0 2"), "sonuc")


def test_ayarlar_geri_yuklenir_1():
    mo.ayarla(ondalik=True, basamak=7, python=False, kural=False, en_fazla_eleman=2)
    assert mo.ayarlar.basamak == 7


def test_ayarlar_geri_yuklenir_2():
    """Önceki test ayarları değiştirdi; fixture eskiye döndürmüş olmalı."""
    assert mo.ayarlar.ondalik is False and mo.ayarlar.basamak == 4
    assert mo.ayarlar.python is True and mo.ayarlar.kural is True and mo.ayarlar.en_fazla_eleman == 36
    assert mo.ayarlar.goster == "yok"


def test_ayarla_hatalar():
    with pytest.raises(mo.MatrisHatasi):
        mo.ayarla(olmayan_ayar=1)
    with pytest.raises(mo.MatrisHatasi):
        mo.carp("1 2; 3 4", "5 6; 7 8", goster="abc")
    assert mo.ayarla(basamak=4) is mo.ayarlar


def test_sonuc_zincirleme():
    r1 = mo.carp(A12, B12)
    r2 = mo.transpoz(r1)
    assert r2.deger == (A12 * B12).T
    assert r2.ad == "C^T"
    r3 = mo.determinant(mo.ters(mo.carp("1 2; 3 4", "5 6; 7 8")))
    assert r3.deger == 1 / (A12 * B12).det()
    r4 = mo.coz(mo.topla("1 0; 0 1", "1 1; 1 2"), mo.skaler(2, "1; 2"))
    assert r4.deger == sp.Matrix([[2, 1], [1, 3]]).LUsolve(sp.Matrix([2, 4]))


def test_sonuc_repr():
    assert repr(mo.carp("1 2; 3 4", "5 6; 7 8")) == "<Sonuc C 2x2: [[19, 22], [43, 50]]>"
    assert repr(mo.determinant("4 7; 2 6")) == "<Sonuc det: 10>"
    assert repr(mo.iz("2 1; 1 3")) == "<Sonuc tr: 5>"
    assert repr(mo.rank("1 2; 2 4")) == "<Sonuc rank: 1>"
    assert repr(mo.coz("2 1; 1 3", "3; 5")) == "<Sonuc x 2x1: [[4/5], [7/5]]>"
    assert repr(mo.cubuk_eleman(200000, 100, 1000)) == "<Sonuc k 2x2: [[20000, -20000], [-20000, 20000]]>"


def test_sonuc_ozellikleri():
    r = mo.carp("1 2; 3 4", "5 6; 7 8")
    assert r.M is r.deger
    assert r.shape == (2, 2)            # sympy nesnesine yönlendirme
    assert r[0, 0] == 19 and r[1, 1] == 50
    assert r.T == r.deger.T
    assert "bmatrix" in r.latex() and "19" in r.latex()
    assert r.markdown() == r.anlatim.markdown()
    assert mo.son_anlatim is r.anlatim
    assert r.python_kodu and r.python_ciktisi
    with pytest.raises(AttributeError):
        r.olmayan_ozellik  # noqa: B018
    assert r._ipython_display_() is None


def test_anlatim_blok_yapisi():
    r = mo.coz("2 1; 1 3", "3; 5")
    bloklar = r.anlatim.bloklar
    assert bloklar and all(isinstance(b, tuple) and len(b) == 3 for b in bloklar)
    assert {b[0] for b in bloklar} <= {"md", "math", "kod"}
    assert {b[2] for b in bloklar} == {"kural", "adim", "sonuc", "python"}
    assert bloklar[0][0] == "md" and bloklar[0][1].startswith("### ")
    kod_bloklari = [b for b in bloklar if b[0] == "kod"]
    assert len(kod_bloklari) == 1
    baslik, kod, cikti = kod_bloklari[0][1]
    assert "Python ile" in baslik and kod == r.python_kodu and cikti == r.python_ciktisi
    md = r.anlatim.markdown()
    assert md.count("$$") >= 2 and "```python" in md and str(r.anlatim) == md


def test_latex_skaler_ve_matris():
    assert mo.determinant("4 7; 2 6").latex() == "10"
    assert mo.coz("2 1; 1 3", "3; 5").latex() == r"\begin{bmatrix} \frac{4}{5} \\ \frac{7}{5} \end{bmatrix}"


def test_yardim_ve_birim_sifir(capsys, monkeypatch):
    monkeypatch.setattr(mo, "_IPYTHON", False)
    mo.yardim()
    out = capsys.readouterr().out
    assert "carp" in out and "sinir_kosulu" in out
    assert mo.birim(3) == sp.eye(3)
    assert mo.sifir(2, 3) == sp.zeros(2, 3) and mo.sifir(2) == sp.zeros(2, 2)
    assert mo.__version__


# ===========================================================================
# 10. Hata durumları (MatrisHatasi)
# ===========================================================================
@pytest.mark.parametrize("fn, args, kw", [
    pytest.param(mo.carp, ("1 2; 3 4", "1 2 3"), {}, id="carp-boyut"),
    pytest.param(mo.carp, ("1 2; 3 4",), {}, id="carp-tek-matris"),
    pytest.param(mo.topla, ("1 2; 3 4", "1 2 3"), {}, id="topla-boyut"),
    pytest.param(mo.cikar, ("1 2; 3 4", "1; 2"), {}, id="cikar-boyut"),
    pytest.param(mo.topla, ("1 $; 3 4", "1 2; 3 4"), {}, id="gecersiz-eleman"),
    pytest.param(mo.topla, ("1 2; 3", "1 2; 3 4"), {}, id="satir-uzunluk"),
    pytest.param(mo.topla, ("", "1 2"), {}, id="bos-girdi"),
    pytest.param(mo.skaler, ("$", "1 2"), {}, id="skaler-gecersiz"),
    pytest.param(mo.determinant, ("1 2 3; 4 5 6",), {}, id="det-kare-degil"),
    pytest.param(mo.determinant, ("1 2; 3 4",), {"yontem": "abc"}, id="det-yontem"),
    pytest.param(mo.iz, ("1 2 3; 4 5 6",), {}, id="iz-kare-degil"),
    pytest.param(mo.ters, ("1 2 3; 4 5 6",), {}, id="ters-kare-degil"),
    pytest.param(mo.ters, ("1 2; 2 4",), {}, id="ters-tekil"),
    pytest.param(mo.ters, ("2 1 0; 1 3 1; 0 1 4",), {"yontem": "formul"}, id="ters-formul-3x3"),
    pytest.param(mo.ters, ("1 2; 3 4",), {"yontem": "abc"}, id="ters-yontem"),
    pytest.param(mo.coz, ("1 2; 2 4", "3; 7"), {}, id="coz-tutarsiz"),
    pytest.param(mo.coz, ("1 2; 3 4", "1; 2; 3"), {}, id="coz-b-boyut"),
    pytest.param(mo.coz, ("1 2; 3 4", "1 2; 3 4"), {}, id="coz-b-matris"),
    pytest.param(mo.coz, ("1 2; 3 4", "1; 2"), {"yontem": "abc"}, id="coz-yontem"),
    pytest.param(mo.coz, (M4, "1; 2; 3; 4"), {"yontem": "cramer"}, id="coz-cramer-4x4"),
    pytest.param(mo.coz, ("1 2; 2 4", "3; 7"), {"yontem": "cramer"}, id="coz-cramer-det0"),
    pytest.param(mo.coz, ("1 2; 2 4", "3; 7"), {"yontem": "ters"}, id="coz-ters-det0"),
    pytest.param(mo.coz, ("1 2 3; 4 5 6", "1; 2"), {"yontem": "ters"}, id="coz-ters-kare-degil"),
    pytest.param(mo.ozdeger, ("1 2 3; 4 5 6",), {}, id="ozdeger-kare-degil"),
    pytest.param(mo.birlestir, ([("1 2; 3 4", [1, 2, 3])], 3), {}, id="birlestir-dof-sayisi"),
    pytest.param(mo.birlestir, ([("1 2; 3 4", [1, 4])], 3), {}, id="birlestir-dof-aralik"),
    pytest.param(mo.birlestir, ([("1 2; 3 4", [0, 1])], 3), {}, id="birlestir-dof-sifir"),
    pytest.param(mo.sinir_kosulu, ("1 2; 3 4", "1; 2"), {"sabit": [1, 2]}, id="sinir-hepsi-sabit"),
    pytest.param(mo.sinir_kosulu, ("1 2; 3 4", "1; 2; 3"), {"sabit": [1]}, id="sinir-F-boyut"),
    pytest.param(mo.sinir_kosulu, ("1 2; 3 4", "1; 2"), {"sabit": [3]}, id="sinir-sabit-aralik"),
    pytest.param(mo.topla, ("1 2; 3 4", "5 6; 7 8"), {"adlar": ["A"]}, id="adlar-eksik"),
])
def test_matris_hatasi(fn, args, kw):
    with pytest.raises(mo.MatrisHatasi):
        fn(*args, **kw)


# ===========================================================================
# 11. Büyük matris (eleman listesi sınırı) — değerler yine doğru
# ===========================================================================
def test_buyuk_matris_7x7():
    rnd = random.Random(1)
    for _ in range(50):
        M7 = sp.Matrix(7, 7, lambda i, j: rnd.randint(-5, 5))
        if M7.det() != 0:
            break
    b = sp.Matrix(7, 1, lambda i, j: i + 1)
    r = mo.carp(M7, M7)
    assert r.deger == M7 * M7
    assert "örnek olarak ilk eleman" in r.anlatim.markdown()
    assert mo.determinant(M7).deger == M7.det()
    assert mo.ters(M7).deger == M7.inv()
    assert mo.coz(M7, b).deger == M7.LUsolve(b)
    assert mo.rank(M7).deger == 7
    assert "[Hata" not in r.python_ciktisi
