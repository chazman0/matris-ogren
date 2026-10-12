# -*- coding: utf-8 -*-
"""
defter_yap.py — Matris_Ogren.ipynb (Google Colab defteri) üretici
=================================================================
matris_ogren.py modülünü base64+zlib olarak defterin kurulum hücresine gömer;
öğretici Markdown hücreleri ve Colab FORM hücreleriyle (#@title / #@param)
Matris_Ogren.ipynb dosyasını baştan kurar.

Çalıştırma (proje klasöründen, Windows PowerShell):
  Set-Location "$env:USERPROFILE\\Desktop\\matris_ogren"
  & "$env:USERPROFILE\\.local\\bin\\uv.exe" run --python 3.13 --with nbformat python defter_yap.py

Modül (matris_ogren.py) değişince bu betiği yeniden çalıştırmak yeterlidir;
defter her seferinde sıfırdan üretilir (yeniden çalıştırılabilir).
"""
from __future__ import annotations

import base64
import hashlib
import re
import textwrap
import zlib
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

KLASOR = Path(__file__).resolve().parent
MODUL = KLASOR / "matris_ogren.py"
DEFTER = KLASOR / "Matris_Ogren.ipynb"


# ============================================================================
# Hücre yardımcıları
# ============================================================================
def md(metin: str):
    """Markdown hücresi (girintiler temizlenir)."""
    return new_markdown_cell(textwrap.dedent(metin).strip("\n"))


def kod(metin: str):
    """Düz kod hücresi."""
    return new_code_cell(textwrap.dedent(metin).strip("\n"))


def form(baslik: str, parametreler: str, govde: str, ipucu: str):
    """Colab form hücresi.

    - ilk satır: #@title ... { display-mode: "form" }
    - parametreler: #@param satırları (hücrenin üstünde, form alanları)
    - govde: mo.<islev>(...) çağrıları; try/except mo.MatrisHatasi ile sarılır
    - ipucu: başarıyla bitince gösterilen kısa "📌 Ne öğrendin?" notu
    """
    parametreler = textwrap.dedent(parametreler).strip("\n")
    govde = textwrap.indent(textwrap.dedent(govde).strip("\n"), "    ")
    ipucu_py = repr("📌 **Ne öğrendin?** " + " ".join(textwrap.dedent(ipucu).split()))
    satirlar = [
        f'#@title {baslik} {{ display-mode: "form" }}',
        parametreler,
        "from IPython.display import Markdown, Math, display",
        "try:",
        "    import matris_ogren as mo",
        "except ModuleNotFoundError as _e:",
        "    if _e.name == 'matris_ogren':",
        "        raise RuntimeError(\"Önce '🔧 1) Kurulum' hücresini çalıştırın.\") from None",
        "    raise",
        "try:",
        govde,
        "except mo.MatrisHatasi as e:",
        '    display(Markdown("> ❌ **Hata:** " + str(e)))',
        "except Exception as e:",
        '    display(Markdown("> ❌ **Beklenmeyen hata** (" + type(e).__name__ + "): " + str(e) + " — girdini kontrol et ve yeniden çalıştır."))',
        "else:",
        f"    display(Markdown({ipucu_py}))",
    ]
    return new_code_cell("\n".join(satirlar), metadata={"cellView": "form"})


# ============================================================================
# 1) Kurulum hücresi — modül base64+zlib olarak gömülür
# ============================================================================
KURULUM_SABLON = r'''#@title 🔧 1) Kurulum — önce bunu çalıştır { display-mode: "form" }
# matris_ogren.py modülü aşağıda zlib ile sıkıştırılmış ve base64 ile kodlanmış olarak gömülüdür.
# Bu hücre onu çalışma dizinine matris_ogren.py olarak yazar ve `mo` adıyla içe aktarır.
# Colab'da sympy / numpy / IPython hazırdır; pip kurulumu gerekmez.
import base64, hashlib, importlib, sys, zlib
from pathlib import Path

_SURUM = "__SURUM__"
_SHA256 = "__SHA__"
_PAKET = (
__PAKET__
)
_kaynak = zlib.decompress(base64.b64decode(_PAKET))
if hashlib.sha256(_kaynak).hexdigest() != _SHA256:
    raise RuntimeError("Gömülü modül bozuk (sağlama toplamı uyuşmuyor). Defteri defter_yap.py ile yeniden üretin.")

_hedef = Path.cwd() / "matris_ogren.py"
try:  # Colab'da mıyız? (find_spec, üst paket 'google' yoksa hata verir; bu yüzden try/except)
    import google.colab  # noqa: F401
    _colab = True
except Exception:  # noqa: BLE001
    _colab = False
if not _hedef.exists():
    _hedef.write_bytes(_kaynak)
    _durum = "yazıldı"
elif _hedef.read_bytes() == _kaynak:
    _durum = "zaten güncel"
elif _colab:
    _hedef.write_bytes(_kaynak)
    _durum = "güncellendi"
else:  # yerel çalışma: klasördeki farklı modül korunur, üzerine yazılmaz
    _durum = "⚠️ klasördeki FARKLI matris_ogren.py korundu; gerekiyorsa defteri defter_yap.py ile yeniden üretin"

if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))
importlib.invalidate_caches()
if "matris_ogren" in sys.modules:          # hücre ikinci kez çalıştırılırsa güvenli yeniden yükleme
    mo = importlib.reload(sys.modules["matris_ogren"])
else:
    import matris_ogren as mo

print(f"✅ Hazır. Sürüm: {mo.__version__}  (gömülü sürüm {_SURUM}; matris_ogren.py {_durum}; "
      f"{len(_kaynak):,} bayt, {len(mo.__all__)} işlev)")
print("Bölümleri sırayla çalıştırabilirsin. Fonksiyon listesi için: mo.yardim()")
'''


def kurulum_hucresi(kaynak: bytes) -> nbformat.NotebookNode:
    paket = base64.b64encode(zlib.compress(kaynak, 9)).decode("ascii")
    satirlar = [paket[i:i + 76] for i in range(0, len(paket), 76)]
    blok = "\n".join(f'    "{s}"' for s in satirlar)
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', kaynak.decode("utf-8"), re.M)
    surum = m.group(1) if m else "?"
    src = (KURULUM_SABLON
           .replace("__SURUM__", surum)
           .replace("__SHA__", hashlib.sha256(kaynak).hexdigest())
           .replace("__PAKET__", blok))
    return new_code_cell(src, metadata={"cellView": "form"})


# ============================================================================
# Defter içeriği
# ============================================================================
def hucreler(kaynak: bytes) -> list:
    H: list = []

    # ------------------------------------------------------------------ 0
    H.append(md(r"""
    # 🧮 Matris Öğren — Sonlu Elemanlar için adım adım matris hesaplayıcı

    Bu defter, **matrisin ne olduğunu ve nasıl hesaplandığını** sıfırdan öğretmek için hazırlandı.
    Her işlemde üç şey görürsün:

    1. 📘 **Kural** — kısa ders notu (tanım, koşul, neden böyle)
    2. ✏️ **Adım adım hesap** — elle nasıl yapılır (sınavda yazacağın biçimde, LaTeX ile)
    3. 🐍 **Python ile** — aynı işin numpy / sympy kodu ve **gerçek** çıktısı

    ## Nasıl kullanılır?
    - Önce **🔧 1) Kurulum** hücresini **bir kez** çalıştır: hücrenin solundaki ▶ düğmesi ya da `Shift+Enter`.
      "✅ Hazır" yazısını görünce devam et.
    - Her bölümde bir **form** var: kutulara kendi matrisini yaz, ▶ ile çalıştır. Çıktıda önce adım adım
      matematik, sonra **🐍 Python ile** bölümü gelir. Kodun kendisini görmek istersen hücreye çift tıkla
      (ya da hücre menüsünden *Kodu göster*).
    - **Matris yazımı:** satırlar `;` ile, elemanlar boşluk ya da virgülle ayrılır.
      `1 2; 3 4` şu matristir: $\begin{bmatrix}1&2\\3&4\end{bmatrix}$. Sütun vektörü: `3; 5`.
    - Elemanlar tam sayı (`3`), ondalık (`2.5`), kesir (`1/3`) ya da **sembol** olabilir:
      `E*A/L, -E*A/L; -E*A/L, E*A/L` (sembolik ifadelerde elemanları **virgülle** ayır, ifade içinde boşluk bırakma).
      `E, A, L, I, k, P` gibi harfler otomatik olarak sembol olur.
    - **Ondalık için nokta kullan:** `2.5` doğrudur. Virgül eleman ayırıcıdır; `2,5` yazarsan `2` ve `5` iki ayrı eleman olarak okunur.
    - Hata yaparsan kırmızı ❌ kutusu Türkçe açıklar (örn. *boyutlar farklı*); düzeltip yeniden çalıştır.
    - Sol taraftaki **İçindekiler** panelinden bölümler arasında atlayabilirsin.
    """))

    H.append(kurulum_hucresi(kaynak))

    # ------------------------------------------------------------------ 1
    H.append(md(r"""
    ## 1) Matris nedir?

    **Matris**, sayıların (ya da sembollerin) **satır** ve **sütun**lar hâlinde dizilmiş tablosudur.
    $m$ satırı ve $n$ sütunu olan matris **$m \times n$ boyutlu**dur ("m'ye n" diye okunur; **önce satır, sonra sütun**).

    $$\mathbf{A} = \begin{bmatrix} 2 & -1 & 0 \\ -1 & 2 & -1 \end{bmatrix} \qquad (2\times3:\ 2\text{ satır},\ 3\text{ sütun})$$

    - Her elemanın bir **adresi** vardır: $a_{ij}$ = $i$. satır, $j$. sütundaki eleman.
      Yukarıda $a_{11}=2$, $a_{12}=-1$, $a_{13}=0$, $a_{21}=-1$, $a_{22}=2$, $a_{23}=-1$.
    - **Vektör:** tek sütunlu ($n\times1$, *sütun vektörü*) ya da tek satırlı ($1\times n$) matris.
      Sonlu elemanlarda yer değiştirmeler $\mathbf{u}$ ve kuvvetler $\mathbf{F}$ sütun vektörüdür.
    - **Kare matris:** satır sayısı = sütun sayısı ($n\times n$). Rijitlik matrisi her zaman karedir.
    - **Birim matris** $\mathbf{I}$: köşegeni 1, kalanı 0. Sayılardaki "1" gibidir: $\mathbf{A}\mathbf{I}=\mathbf{I}\mathbf{A}=\mathbf{A}$.
    - **Sıfır matris** $\mathbf{0}$: bütün elemanları 0.
    - **Transpoz** $\mathbf{A}^T$: satırlar sütun, sütunlar satır olur; $(\mathbf{A}^T)_{ij} = a_{ji}$.
    - **Simetrik matris:** $\mathbf{A}^T = \mathbf{A}$, yani $a_{ij} = a_{ji}$. Rijitlik matrisleri simetriktir.
      Nedeni karşılıklılıktır (Maxwell–Betti): $j$. **serbestlik derecesine** (SD; bir düğümün hareket yönü, aşağıda açıklanıyor)
      1 birim yer değiştirme verince $i$. SD'de doğan kuvvet ($K_{ij}$), $i$. SD'ye 1 birim verince $j$. SD'de doğan kuvvete ($K_{ji}$) eşittir.

    ### Sonlu elemanlarda matris neden var?
    Yapı, **düğümlerle** birbirine bağlı **elemanlara** bölünür. Her düğümün hareket edebildiği bağımsız yönlere
    **serbestlik derecesi** (SD; İngilizce *degree of freedom*, DOF) denir (çubuk düğümünde eksenel yer değiştirme $u$;
    kiriş düğümünde çökme $v$ ve dönme $\theta$). Bu defterde "SD" diye kısaltılır.
    Her eleman bir yay gibi davranır: *kuvvet = rijitlik × yer değiştirme*. Bütün elemanlar bir araya gelince
    bu, **tek bir matris denklemi** olur:

    $$\mathbf{K}\,\mathbf{u} = \mathbf{F}$$

    $\mathbf{K}$: **rijitlik matrisi** ($n\times n$, $n$ = toplam serbestlik derecesi sayısı),
    $\mathbf{u}$: bilinmeyen **yer değiştirmeler**, $\mathbf{F}$: **düğüm kuvvetleri**.
    Örneğin rijitliği $k$ olan iki yayın seri bağlanması (3 düğüm → 3 serbestlik derecesi):

    $$\begin{bmatrix} k & -k & 0 \\ -k & 2k & -k \\ 0 & -k & k \end{bmatrix}
      \begin{bmatrix} u_1 \\ u_2 \\ u_3 \end{bmatrix} =
      \begin{bmatrix} F_1 \\ F_2 \\ F_3 \end{bmatrix}$$

    2. satır tam olarak şu denklemdir: $-k\,u_1 + 2k\,u_2 - k\,u_3 = F_2$ → 2. düğümdeki **kuvvet dengesi**.
    Yani **matris, denklem sistemini kısa yazmanın yoludur.** Dersin geri kalanı bu denklemi kurmak
    ($\mathbf{K}$'yi birleştirmek) ve çözmektir (sınır koşulları + denklem sistemi çözümü).

    Aşağıdaki forma bir matris yaz; boyutunu, eleman adreslerini, transpozunu ve (kareyse) izini gör.
    """))

    H.append(form(
        "🔎 1) Matrisi tanı: boyut, elemanlar, transpoz, iz",
        '''
        A = "2 -1 0; -1 2 -1; 0 -1 1" #@param {type:"string"}
        ad = "A" #@param {type:"string"}
        ''',
        r'''
        import sympy as sp
        ad = ad.strip() if ad.strip().isalnum() else "A"
        M = mo.matris(A)
        m, n = M.rows, M.cols
        ozellik = []
        if n == 1 and m > 1:
            ozellik.append("sütun vektörü")
        elif m == 1 and n > 1:
            ozellik.append("satır vektörü")
        if m == n:
            ozellik.append("kare")
            if M == sp.eye(n):
                ozellik.append("birim matris")
            if M == M.T:
                ozellik.append("simetrik")
        if M == sp.zeros(m, n):
            ozellik.append("sıfır matris")
        ek = (" — " + ", ".join(ozellik)) if ozellik else ""
        display(Markdown(f"### Matris **{ad}**: boyut ${m}\\times{n}$ ({m} satır, {n} sütun, {m*n} eleman){ek}"))
        display(Math(rf"\mathbf{{{ad}}} = {mo.LM(M)}"))
        display(Markdown("Elemanların adresleri — $a_{ij}$: $i$. satır, $j$. sütun (**önce satır, sonra sütun**):"))
        satirlar = [",\\quad ".join(rf"a_{{{i+1}{j+1}}} = {mo.L(M[i, j])}" for j in range(n)) for i in range(m)]
        display(Math(r"\begin{array}{l} " + r" \\ ".join(satirlar) + r" \end{array}"))
        display(Markdown("#### Transpoz"))
        mo.transpoz(A, adlar=[ad])
        if m == n:
            display(Markdown("#### İz (köşegen toplamı)"))
            mo.iz(A, adlar=[ad])
        else:
            display(Markdown(f"İz ($\\operatorname{{tr}}$) yalnız **kare** matrisler için tanımlıdır; {ad} ${m}\\times{n}$ olduğundan izi yoktur."))
        ''',
        """
        Boyut "satır × sütun" diye okunur; $a_{ij}$'de önce satır ($i$) sonra sütun ($j$) gelir.
        Simetrik bir matriste transpoz matrisin kendisidir — rijitlik matrisleri böyledir.
        Dene: `1 2 3; 4 5 6` (2×3, kare değil) ya da `E*A/L, -E*A/L; -E*A/L, E*A/L` (sembolik).
        """,
    ))

    # ------------------------------------------------------------------ 2
    H.append(md(r"""
    ## 2) Toplama, çıkarma ve skalerle çarpma

    - **Toplama / çıkarma** yalnız **aynı boyuttaki** matrisler arasında yapılır; aynı adresteki elemanlar
      toplanır: $c_{ij} = a_{ij} + b_{ij}$.

    $$\begin{bmatrix}1&2\\3&4\end{bmatrix}+\begin{bmatrix}5&6\\7&8\end{bmatrix}
      =\begin{bmatrix}1+5&2+6\\3+7&4+8\end{bmatrix}=\begin{bmatrix}6&8\\10&12\end{bmatrix}$$

    - **Skalerle (sayıyla) çarpma:** sayı **her elemanı** çarpar:
      $3\begin{bmatrix}1&2\\3&4\end{bmatrix} = \begin{bmatrix}3&6\\9&12\end{bmatrix}$.
    - Sonlu elemanlarda: rijitlik matrisinin önündeki $\dfrac{EA}{L}$ çarpanı bir skaler çarpımdır;
      **birleştirme (assembly)** ise ortak düğümlerdeki eleman katkılarının **toplanmasıdır**.
    """))

    H.append(form(
        "➕ 2) Toplama / çıkarma / skalerle çarpma",
        '''
        islem = "topla" #@param ["topla", "cikar", "skaler"]
        A = "1 2; 3 4" #@param {type:"string"}
        B = "5 6; 7 8" #@param {type:"string"}
        k = "3" #@param {type:"string"}
        ''',
        '''
        if islem == "topla":
            sonuc = mo.topla(A, B)
        elif islem == "cikar":
            sonuc = mo.cikar(A, B)
        else:
            sonuc = mo.skaler(k, A)
        ''',
        """
        Toplama/çıkarma eleman eleman yapılır ve boyutlar aynı olmalıdır (farklı boyut → işlem tanımsız; dene:
        A = `1 2; 3 4`, B = `1 2 3; 4 5 6`). Skalerle çarpmada sayı her elemanı çarpar; $k$ yerine `E*A/L` gibi
        sembolik bir çarpan da yazabilirsin.
        """,
    ))

    # ------------------------------------------------------------------ 3
    H.append(md(r"""
    ## 3) Matris çarpımı — "satır × sütun" kuralı

    $\mathbf{A}$ ($m\times n$) ile $\mathbf{B}$ ($n\times p$) çarpılabilmesi için **A'nın sütun sayısı = B'nin satır sayısı**
    olmalıdır; sonuç $m\times p$ olur. Sonucun $i$. satır $j$. sütun elemanı, **A'nın $i$. satırı ile B'nin $j$. sütununun**
    karşılıklı çarpımlarının toplamıdır:

    $$c_{ij} = a_{i1}b_{1j} + a_{i2}b_{2j} + \cdots + a_{in}b_{nj} = \sum_{l=1}^{n} a_{il}\,b_{lj}$$

    ($l$: A'nın sütunları = B'nin satırları boyunca sayan indis.)

    $$\begin{bmatrix}1&2\\3&4\end{bmatrix}\begin{bmatrix}5&6\\7&8\end{bmatrix}
      = \begin{bmatrix}1\cdot5+2\cdot7 & 1\cdot6+2\cdot8\\ 3\cdot5+4\cdot7 & 3\cdot6+4\cdot8\end{bmatrix}
      = \begin{bmatrix}19&22\\43&50\end{bmatrix}$$

    - **Sıra önemlidir:** genelde $\mathbf{AB}\neq\mathbf{BA}$; hatta biri tanımlıyken diğeri tanımsız olabilir.
    - Sonlu elemanlarda $\mathbf{K}\mathbf{u}$ çarpımı: $\mathbf{K}$'nin $i$. satırı × $\mathbf{u}$ = $i$. SD'deki kuvvet $F_i$.
      Kafes elemanında yerel→global dönüşüm $\mathbf{k} = \mathbf{T}^T\mathbf{k}'\mathbf{T}$ bir **üçlü çarpımdır**
      (aşağıda C kutusunu doldurursan üç matris zincir olarak çarpılır).
    """))

    H.append(form(
        "✖️ 3) Matris çarpımı: A·B (isteğe bağlı ·C)",
        '''
        A = "1 2; 3 4" #@param {type:"string"}
        B = "5 6; 7 8" #@param {type:"string"}
        C = "" #@param {type:"string"}
        ''',
        '''
        girdiler = [A, B] + ([C] if C.strip() else [])
        sonuc = mo.carp(*girdiler)
        ''',
        """
        Her $c_{ij}$ için A'nın $i$. satırıyla B'nin $j$. sütunu eşleştirilip çarpımlar toplanır; iç boyutlar
        eşit değilse çarpım tanımsızdır (dene: A = `1 2 3; 4 5 6`, B = `1 2; 3 4`). Python'da `@` matris
        çarpımıdır, `*` ise eleman eleman çarpar — ikisi farklı şeydir. Dene: A ve B'nin yerini değiştir,
        $\\mathbf{AB}$ ile $\\mathbf{BA}$ farklı çıkar.
        """,
    ))

    # ------------------------------------------------------------------ 4
    H.append(md(r"""
    ## 4) Transpoz

    $\mathbf{A}^T$: **satırlar sütun olur.** $m\times n$ matrisin transpozu $n\times m$ olur; $(\mathbf{A}^T)_{ij}=a_{ji}$.

    $$\begin{bmatrix}1&2&3\\4&5&6\end{bmatrix}^T = \begin{bmatrix}1&4\\2&5\\3&6\end{bmatrix}$$

    - Özellikler: $(\mathbf{A}^T)^T=\mathbf{A}$, $(\mathbf{A}+\mathbf{B})^T=\mathbf{A}^T+\mathbf{B}^T$,
      $(\mathbf{AB})^T=\mathbf{B}^T\mathbf{A}^T$ (**sıra ters döner**).
    - $\mathbf{A}^T=\mathbf{A}$ ise matris **simetriktir**. Rijitlik matrisi için hızlı bir kontrol:
      $\mathbf{K}^T=\mathbf{K}$ çıkmıyorsa bir yerde hata vardır.
    - Sonlu elemanlarda kafes elemanının dönüşümünde $\mathbf{T}^T$ kullanılır (iş eşitliği: $\mathbf{f}=\mathbf{T}^T\mathbf{f}'$, bkz. 9c);
      sütun vektörünü satır vektörü yapmak için de transpoz alınır ($\mathbf{u}^T\mathbf{K}\mathbf{u}$ = iki katı şekil değiştirme enerjisi).
    """))

    H.append(form(
        "🔁 4) Transpoz",
        '''
        A = "1 2 3; 4 5 6" #@param {type:"string"}
        ''',
        '''
        sonuc = mo.transpoz(A)
        ''',
        """
        Transpozda 1. satır 1. sütun olur, 2. satır 2. sütun olur... Boyut $m\\times n$'den $n\\times m$'ye döner.
        Dene: `2 -1; -1 2` → transpoz kendisine eşit (simetrik); `1 2; 3 4` → değil.
        """,
    ))

    # ------------------------------------------------------------------ 5
    H.append(md(r"""
    ## 5) Determinant

    Determinant, **kare** matrise karşılık gelen tek bir sayıdır: $\det\mathbf{A}$ ya da $|\mathbf{A}|$.

    - $2\times2$: $\det\begin{bmatrix}a&b\\c&d\end{bmatrix} = ad - bc$.
      Örnek: $\det\begin{bmatrix}2&1\\1&3\end{bmatrix} = 2\cdot3 - 1\cdot1 = 5$.
    - $3\times3$ ve üstü: **kofaktör açılımı** (1. satıra göre):
      $\det\mathbf{A} = a_{11}M_{11} - a_{12}M_{12} + a_{13}M_{13}$; $M_{1j}$, 1. satır ve $j$. sütun silinince kalan $2\times2$
      determinanttır (**minör**); işaretler $+,-,+$ diye değişir.
    - Alternatif: **satır indirgeme (eliminasyon)** ile üst üçgen yap, köşegen elemanlarını çarp (satır değişimi başına işaret değişir).

    **Neden önemli?** $\det\mathbf{A}=0$ ↔ matris **tekil** ↔ tersi yok ↔ $\mathbf{Ax}=\mathbf{b}$ tek çözümlü değil.
    Sonlu elemanlarda **mesnetlenmemiş** yapının $\det\mathbf{K}=0$'dır (yapı rijit cisim gibi kayabilir);
    sınır koşulları uygulanınca (mesnetli SD'lerin satır ve sütunları silinince) kalan $\mathbf{K}_s$ için, **mesnetler bütün
    rijit cisim hareketlerini engelliyorsa** (mekanizma kalmıyorsa) $\det\mathbf{K}_s\neq0$ olur ve çözüm tek çıkar;
    mesnet yetersizse $\mathbf{K}_s$ yine tekil kalır.
    Doğal frekanslar da bir determinanttan gelir: $\det(\mathbf{K}-\omega^2\mathbf{M})=0$.
    """))

    H.append(form(
        "🔢 5) Determinant",
        '''
        A = "2 1 0; 1 3 1; 0 1 4" #@param {type:"string"}
        yontem = "otomatik" #@param ["otomatik", "kofaktor", "eliminasyon"]
        ''',
        '''
        sonuc = mo.determinant(A, yontem=None if yontem == "otomatik" else yontem)
        ''',
        """
        $2\\times2$'de çapraz çarpımların farkı, $3\\times3$'te kofaktör açılımı (işaretler $+,-,+$), daha büyüklerde
        satır indirgeme kullanılır. Dene: `1 2; 2 4` → det = 0 (satırlar orantılı, tekil); mesnetsiz rijitlik
        matrisi `1 -1; -1 1` → det = 0.
        """,
    ))

    # ------------------------------------------------------------------ 6
    H.append(md(r"""
    ## 6) Ters matris

    $\mathbf{A}^{-1}$, $\mathbf{A}\mathbf{A}^{-1}=\mathbf{A}^{-1}\mathbf{A}=\mathbf{I}$ koşulunu sağlayan matristir:
    sayılarda **bölme** ne ise matriste ters odur. Yalnız **kare ve $\det\neq0$** olan matrislerin tersi vardır.

    - $2\times2$ formülü: $\begin{bmatrix}a&b\\c&d\end{bmatrix}^{-1} = \dfrac{1}{ad-bc}\begin{bmatrix}d&-b\\-c&a\end{bmatrix}$
      (köşegen elemanlar yer değiştirir, diğer ikisinin işareti değişir, determinanta bölünür).
      Örnek: $\begin{bmatrix}4&7\\2&6\end{bmatrix}^{-1} = \dfrac{1}{10}\begin{bmatrix}6&-7\\-2&4\end{bmatrix}$.
    - Genel yöntem — **Gauss–Jordan**: $[\,\mathbf{A}\mid\mathbf{I}\,]$ matrisine satır işlemleri uygulanıp sol blok
      $\mathbf{I}$ yapılır; sağ blokta $\mathbf{A}^{-1}$ kalır.
    - Sonlu elemanlarda ters ancak **mesnetler uygulandıktan sonra** alınabilir (mesnetsiz $\mathbf{K}$ tekildir, bkz. Bölüm 5):
      $\mathbf{u}_s=\mathbf{K}_s^{-1}\mathbf{F}_s$. $\mathbf{K}_s^{-1}$ **esneklik (flexibility) matrisidir**: her sütunu,
      bir SD'ye birim kuvvet uygulandığında oluşan yer değiştirmelerdir.
      Uygulamada büyük sistemlerde ters alınmaz (dolu matris, pahalı, yuvarlama hatası birikir), eliminasyon kullanılır.
    """))

    H.append(form(
        "↩️ 6) Ters matris",
        '''
        A = "4 7; 2 6" #@param {type:"string"}
        yontem = "otomatik" #@param ["otomatik", "formul", "gauss"]
        ''',
        '''
        sonuc = mo.ters(A, yontem=None if yontem == "otomatik" else yontem)
        ''',
        """
        Ters almadan önce determinanta bakılır: 0 ise ters yoktur. Sağlama her zaman $\\mathbf{A}\\mathbf{A}^{-1}=\\mathbf{I}$'dır.
        Dene: `2 1 0; 1 3 1; 0 1 4` (Gauss–Jordan adımları) ya da `1 2; 2 4` (tekil → hata kutusu).
        """,
    ))

    # ------------------------------------------------------------------ 7
    H.append(md(r"""
    ## 7) Denklem sistemi: $\mathbf{A}\mathbf{x}=\mathbf{b}$

    İki bilinmeyenli iki denklem $\;2x_1 + x_2 = 3,\quad x_1 + 3x_2 = 5\;$ matris biçiminde:

    $$\underbrace{\begin{bmatrix}2&1\\1&3\end{bmatrix}}_{\mathbf{A}}
      \underbrace{\begin{bmatrix}x_1\\x_2\end{bmatrix}}_{\mathbf{x}} =
      \underbrace{\begin{bmatrix}3\\5\end{bmatrix}}_{\mathbf{b}}
      \qquad\Rightarrow\qquad x_1 = \tfrac{4}{5},\ x_2 = \tfrac{7}{5}$$

    Katsayılar $\mathbf{A}$'da, bilinmeyenler $\mathbf{x}$'te, sağ taraf $\mathbf{b}$'de toplanır. Çözüm yöntemleri:

    - **Gauss eliminasyonu:** genişletilmiş matris $[\,\mathbf{A}\mid\mathbf{b}\,]$ satır işlemleriyle üst üçgen yapılır
      (*ileri eliminasyon*), son denklemden başlayarak bilinmeyenler bulunur (*geri yerine koyma*). FEM yazılımlarının temelidir.
    - **Cramer:** $x_i = \det\mathbf{A}_i/\det\mathbf{A}$ ($\mathbf{A}_i$: $i$. sütun yerine $\mathbf{b}$ konmuş hali) — küçük sistemler için.
    - **Ters matris:** $\mathbf{x} = \mathbf{A}^{-1}\mathbf{b}$.

    Sonlu elemanlarda bu sistem $\mathbf{K}\mathbf{u}=\mathbf{F}$'dir; bilinmeyen adını `u` yapabilirsin.
    Mesnet (sınır koşulu) uygulanmadıysa $\mathbf{K}$ tekildir → tek çözüm yoktur (defter bunu da açıklar).
    """))

    H.append(form(
        "🧩 7) Denklem sistemi çöz: A x = b",
        '''
        A = "2 1; 1 3" #@param {type:"string"}
        b = "3; 5" #@param {type:"string"}
        yontem = "gauss" #@param ["gauss", "cramer", "ters"]
        bilinmeyen = "x" #@param {type:"string"}
        ''',
        '''
        bilinmeyen = bilinmeyen.strip() if bilinmeyen.strip().isalpha() else "x"
        sonuc = mo.coz(A, b, yontem=yontem, bilinmeyen=bilinmeyen)
        ''',
        """
        Gauss eliminasyonu: önce üst üçgen, sonra geri yerine koyma. Sağlama: $\\mathbf{A}\\mathbf{x}$ çarpımı $\\mathbf{b}$'yi
        vermeli. Dene: A = `1 -1; -1 1`, b = `1; -1` (mesnetsiz yay: sonsuz çözüm) ya da b = `1; 1` (tutarsız: çözüm yok);
        3×3 için A = `2 -1 0; -1 2 -1; 0 -1 1`, b = `0; 0; 1`, bilinmeyen = `u`.
        """,
    ))

    # ------------------------------------------------------------------ 8
    H.append(md(r"""
    ## 8) Özdeğerler, özvektörler ve doğal frekans

    $\mathbf{A}\mathbf{v}=\lambda\mathbf{v}$: matris, **özvektör** $\mathbf{v}$'yi yalnızca $\lambda$ katına uzatır/kısaltır,
    yönünü değiştirmez. $\lambda$ sayıları **özdeğer**dir. $(\mathbf{A}-\lambda\mathbf{I})\mathbf{v}=\mathbf{0}$'ın sıfırdan farklı
    çözümü olması için

    $$\det(\mathbf{A}-\lambda\mathbf{I}) = 0 \qquad\text{(karakteristik denklem)}$$

    Örnek: $\mathbf{A}=\begin{bmatrix}2&1\\1&2\end{bmatrix}$ → $\det\begin{bmatrix}2-\lambda&1\\1&2-\lambda\end{bmatrix}
    = (2-\lambda)^2-1 = 0$ → $\lambda_1=1,\ \lambda_2=3$; özvektörler $\begin{bmatrix}1\\-1\end{bmatrix}$ ve $\begin{bmatrix}1\\1\end{bmatrix}$.

    **Serbest titreşim:** $\mathbf{M}\ddot{\mathbf{u}}+\mathbf{K}\mathbf{u}=\mathbf{0}$ denkleminde $\mathbf{u}=\boldsymbol{\phi}\sin\omega t$
    yazılırsa **genelleştirilmiş özdeğer problemi** çıkar:

    $$\mathbf{K}\boldsymbol{\phi} = \omega^2\mathbf{M}\boldsymbol{\phi} \qquad\Rightarrow\qquad \det(\mathbf{K}-\omega^2\mathbf{M})=0$$

    Özdeğer $\lambda=\omega^2$; $\omega=\sqrt{\lambda}$ **doğal açısal frekans** (rad/s), $f=\omega/2\pi$ **doğal frekans** (Hz),
    $T=1/f$ **periyot** (s); özvektör $\boldsymbol{\phi}$ = **mod şekli**. En küçük özdeğer → birinci (temel) mod.

    **Birim uyarısı:** $\omega$'nın rad/s çıkması için $\mathbf{K}$ ile $\mathbf{M}$ birimleri tutarlı olmalıdır.
    $\mathbf{K}$ [N/m] ise $\mathbf{M}$ [kg] yazılır. Bu defterdeki N–mm sisteminde $\mathbf{K}$ [N/mm] ise $\mathbf{M}$
    **ton** (t = 1000 kg) olmalıdır, çünkü 1 N = 1 t·mm/s² (çelik yoğunluğu $7{,}85\cdot10^{-9}$ t/mm³).
    Kütleyi kg yazarsan $\omega$ yaklaşık $\sqrt{1000}\approx31{,}6$ kat küçük çıkar.
    """))

    H.append(form(
        "🎯 8a) Özdeğer ve özvektör: A v = λ v",
        '''
        A = "2 1; 1 2" #@param {type:"string"}
        ozvektor = True #@param {type:"boolean"}
        ''',
        '''
        sonuc = mo.ozdeger(A, ozvektor=ozvektor)
        ''',
        """
        Karakteristik polinom $\\det(\\mathbf{A}-\\lambda\\mathbf{I})$'nın kökleri özdeğerlerdir; her $\\lambda$ için
        $(\\mathbf{A}-\\lambda\\mathbf{I})\\mathbf{v}=\\mathbf{0}$ çözülünce özvektör bulunur. Özvektör bir **sabit çarpan** kadar belirsizdir:
        $\\mathbf{v}$ özvektörse $c\\,\\mathbf{v}$ ($c\\neq0$) de özvektördür; bu yüzden genelde bir bileşeni 1 alınarak
        ya da birim boya getirilerek yazılır.
        Simetrik matrisin özdeğerleri gerçeldir. İz = özdeğerlerin toplamı, det = çarpımı — kontrol et: $1+3=4$, $1\\cdot3=3$.
        """,
    ))

    H.append(form(
        "🎵 8b) Doğal frekans: K φ = ω² M φ",
        '''
        K = "6 -2; -2 2" #@param {type:"string"}
        M = "2 0; 0 1" #@param {type:"string"}
        ''',
        '''
        sonuc = mo.ozdeger(K, M)
        ''',
        """
        Model: 1. düğümü tutulu zincir (zemin–$k_1$–$m_1$–$k_2$–$m_2$). Mesnet uygulanmış rijitlik matrisi
        $\\mathbf{K}=\\begin{bmatrix}k_1+k_2&-k_2\\\\-k_2&k_2\\end{bmatrix}$ ($k_1 = 4$, $k_2 = 2$); kütle matrisi
        $\\mathbf{M}=\\mathrm{diag}(m_1,m_2)=\\mathrm{diag}(2,1)$ (kütleler serbest olan 2. ve 3. düğümdedir).
        Sayılar örnek değerlerdir; $\\mathbf{K}$ [N/mm] ve $\\mathbf{M}$ [ton] alırsan $\\omega$ rad/s çıkar.
        Özdeğerler $\\omega^2$ ($\\lambda = 1, 4$), doğal açısal frekanslar $\\omega=\\sqrt{\\lambda} = 1, 2$ rad/s
        ($f=\\omega/2\\pi \\approx 0{,}16$ ve $0{,}32$ Hz); birinci mod en küçük frekanstır
        ve mod şeklinde iki kütle aynı yönde salınır ($\\phi_1 = [1, 2]^T$), ikinci modda zıt yönde ($\\phi_2 = [-1, 1]^T$;
        özvektörün katı da özvektördür, $[1, -1]^T$ aynı moddur).
        Dene: M = `4 0; 0 2` (kütleler iki katına çıkınca $\\omega^2$ yarıya iner: $\\lambda = 1/2, 2$) ya da
        K = `12 -4; -4 4` (rijitlik iki katına çıkınca $\\omega^2$ iki katına çıkar: $\\lambda = 2, 8$).
        """,
    ))

    # ------------------------------------------------------------------ 9
    H.append(md(r"""
    ## 9) Sonlu elemanlar: eleman matrisinden çözüme

    Bir sonlu eleman çözümünün adımları her zaman aynıdır:

    1. Her eleman için **eleman rijitlik matrisi** $\mathbf{k}^{(e)}$ yaz.
    2. Elemanları **birleştir** (assembly) → **global rijitlik matrisi** $\mathbf{K}$.
    3. **Yük vektörü** $\mathbf{F}$'yi kur (düğüm kuvvetleri).
    4. **Sınır koşullarını** uygula (mesnetlerde yer değiştirme = 0; mesnetler yapının bütün rijit cisim hareketlerini engellemeli).
    5. İndirgenmiş sistemi çöz: $\mathbf{K}_s\mathbf{u}_s=\mathbf{F}_s$ → **yer değiştirmeler**.
    6. Geriye dön: **mesnet tepkileri** $\mathbf{R}=\mathbf{K}\mathbf{u}-\mathbf{F}$, eleman kuvvetleri, gerilmeler.

    ### Çubuk (eksenel) elemanı
    İki düğüm, her düğümde 1 serbestlik derecesi (eksenel yer değiştirme $u$). Eleman bir yay gibidir, yay sabiti $EA/L$:

    $$\mathbf{k} = \frac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix},\qquad
      \begin{bmatrix}f_1\\f_2\end{bmatrix} = \mathbf{k}\begin{bmatrix}u_1\\u_2\end{bmatrix}$$

    **Birimler (tutarlı seç):** $E$ [N/mm² = MPa], $A$ [mm²], $L$ [mm] → $EA/L$ [N/mm]; kuvvet [N], yer değiştirme [mm];
    dinamikte kütle [t], $\omega$ [rad/s] (bkz. Bölüm 8).

    ### Kiriş elemanı (Euler–Bernoulli)
    **Varsayımlar:** düzlem kesitler düzlem ve eksene dik kalır (kesme şekil değiştirmesi ihmal edilir; kısa ve yüksek
    kirişlerde bunu da katan Timoshenko elemanı gerekir), malzeme doğrusal elastik, kesit prizmatik ($EI$ sabit),
    yer değiştirmeler küçük, eksenel etki yok (eksenel SD çubuk elemanıyla ayrıca eklenir), yükler düğümlere indirgenmiş.

    Her düğümde 2 SD: düşey yer değiştirme (çökme) $v$ ve dönme $\theta$ → sıra $[v_1,\theta_1,v_2,\theta_2]$,
    $4\times4$ matris, çarpan $EI/L^3$. **İşaret kuralı:** $v$ yukarı ($+y$), $\theta$ saat yönünün tersi pozitif;
    uç kuvvetleri $[V_1, M_1, V_2, M_2]$ aynı yönlerde pozitif. Her sütun, o SD'ye birim yer değiştirme verilip
    **diğer üçü sıfır tutulduğunda** oluşan uç kuvvetleridir (örnek, 2. sütun: $\theta_1=1$ →
    $V_1=6EI/L^2$, $M_1=4EI/L$, $V_2=-6EI/L^2$, $M_2=2EI/L$).

    ### Kafes elemanı
    Düzlemde eğik çubuk; her düğümde $u$ ve $v$ → $4\times4$. Yerel $2\times2$ matris, dönüşüm matrisi $\mathbf{T}$ ile
    global eksene taşınır: $\mathbf{k}=\mathbf{T}^T\mathbf{k}'\mathbf{T}$, $c=\cos\theta$, $s=\sin\theta$.
    $\theta$: elemanın 1. düğümden 2. düğüme yönünün global $+x$ ekseniyle yaptığı açıdır (saat yönünün tersi pozitif).
    Yerel eksenel yer değiştirme global bileşenlerin eleman eksenine izdüşümüdür: $\mathbf{u}'=\mathbf{T}\mathbf{u}$,
    örneğin $u'_1 = c\,u_1 + s\,v_1$.

    **Neden $\mathbf{T}^T$?** Kuvvetlerin yaptığı iş, eksen seçiminden bağımsızdır:

    $$\mathbf{u}^T\mathbf{f} = \mathbf{u}'^T\mathbf{f}' = (\mathbf{T}\mathbf{u})^T\mathbf{f}' = \mathbf{u}^T\mathbf{T}^T\mathbf{f}'
      \;\Rightarrow\; \mathbf{f}=\mathbf{T}^T\mathbf{f}'$$

    (eksenel kuvvet $x$–$y$ bileşenlerine dağıtılır). $\mathbf{f}'=\mathbf{k}'\mathbf{u}'=\mathbf{k}'\mathbf{T}\mathbf{u}$ yerine
    konunca $\mathbf{f}=\mathbf{T}^T\mathbf{k}'\mathbf{T}\,\mathbf{u}$ çıkar; yani $\mathbf{k}=\mathbf{T}^T\mathbf{k}'\mathbf{T}$ ($4\times4$).

    Önce sembolik ($E$, $A$, $L$ harf olarak) dene, formülü gör; sonra sayı yaz.
    """))

    H.append(form(
        "🪵 9a) Çubuk (eksenel) elemanı: k = EA/L [1 -1; -1 1]",
        '''
        E = "E" #@param {type:"string"}
        A = "A" #@param {type:"string"}
        L = "L" #@param {type:"string"}
        ''',
        '''
        sonuc = mo.cubuk_eleman(E, A, L)
        ''',
        """
        Çubuk elemanı tek sayıyla özetlenir: $EA/L$ (eksenel rijitlik, N/mm). Matris simetrik ve tekildir (det = 0):
        mesnetsiz eleman bütün olarak ötelenebilir. Dene: E = `200000`, A = `100`, L = `1000` → $EA/L = 20000$ N/mm.
        """,
    ))

    H.append(form(
        "📏 9b) Kiriş elemanı (Euler–Bernoulli, 4×4)",
        '''
        E = "E" #@param {type:"string"}
        I = "I" #@param {type:"string"}
        L = "L" #@param {type:"string"}
        ''',
        '''
        sonuc = mo.kiris_eleman(E, I, L)
        ''',
        """
        SD sırası $[v_1,\\theta_1,v_2,\\theta_2]$: çökme–dönme–çökme–dönme. Terimlerin anlamı: $12EI/L^3$, uca verilen
        birim çökmeye karşı kesme kuvvetidir (öteleme rijitliği, N/mm). $6EI/L^2$ çökmeyi dönmeye bağlar: birim çökmenin
        uçta doğurduğu momenttir (N). $4EI/L$, birim dönmeye karşı aynı uçta oluşan momenttir; $2EI/L$ karşı uca taşınan
        momenttir (dönme rijitliği, N·mm/rad). Yani matrisin elemanları farklı birimlerdedir.
        Birimler: E [MPa], I [mm⁴], L [mm] → kuvvetler N, momentler N·mm, $\\theta$ rad.
        Dene: E = `200000`, I = `2000000` (IPE 100 profilinin atalet momenti 1,7·10⁶ mm⁴ mertebesindedir), L = `2000`
        → $EI/L^3 = 50$ N/mm.
        """,
    ))

    H.append(form(
        "📐 9c) Kafes elemanı: k = Tᵀ k' T (açılı çubuk)",
        '''
        E = "1" #@param {type:"string"}
        A = "1" #@param {type:"string"}
        L = "1" #@param {type:"string"}
        aci_derece = 45 #@param {type:"number"}
        ''',
        '''
        sonuc = mo.kafes_eleman(E, A, L, aci_derece)
        ''',
        """
        Açı $\\theta$, elemanın 1. düğümden 2. düğüme yönünün global $+x$ ekseniyle yaptığı açıdır (saat yönünün tersi
        pozitif, derece). Elemanın kendi ekseninde yalnız eksenel rijitlik vardır; $\\mathbf{T}$ bunu global $x$–$y$
        bileşenlerine dağıtır: $c^2$, $cs$, $s^2$ desenleri. Dene: açı = 0 (eleman $x$ ekseninde, yalnız $u$ terimleri kalır),
        90 (eleman düşey, yalnız $v$), 30.
        """,
    ))

    H.append(md(r"""
    ### Birleştirme (assembly)
    Her elemanın matris elemanı $k^{(e)}_{ab}$, yerel $a,b$ SD'lerinin **global numaralarına** karşılık gelen
    $K_{IJ}$ konumuna **eklenir**. İki seri çubukta eleman 1 → SD'ler $[1,2]$, eleman 2 → SD'ler $[2,3]$;
    ortak 2. düğümde iki katkı toplanır: $K_{22} = k^{(1)}_{22} + k^{(2)}_{11}$.

    $$\mathbf{K} = \frac{EA}{L}\begin{bmatrix}1&-1&0\\-1&1+1&-1\\0&-1&1\end{bmatrix}
      = \frac{EA}{L}\begin{bmatrix}1&-1&0\\-1&2&-1\\0&-1&1\end{bmatrix}$$

    Aşağıda her elemanın $E$, $A$ ve boyu ile global SD numaralarını ver (üçüncü eleman isteğe bağlı).
    `n_serbestlik = 0` bırakılırsa en büyük SD numarası alınır.
    """))

    H.append(form(
        "🧱 9d) Birleştirme: seri çubuklardan global K",
        '''
        eleman_sayisi = "2" #@param ["2", "3"]
        E = "E" #@param {type:"string"}
        A = "A" #@param {type:"string"}
        L1 = "L" #@param {type:"string"}
        L2 = "L" #@param {type:"string"}
        L3 = "L" #@param {type:"string"}
        serbestlik1 = "1, 2" #@param {type:"string"}
        serbestlik2 = "2, 3" #@param {type:"string"}
        serbestlik3 = "3, 4" #@param {type:"string"}
        n_serbestlik = 0 #@param {type:"integer"}
        ''',
        '''
        def _sayilar(metin):
            try:
                return [int(t) for t in metin.replace(";", ",").split(",") if t.strip()]
            except ValueError:
                raise mo.MatrisHatasi(f"Serbestlik derecesi (SD) numaraları tam sayı olmalı: {metin!r} (örnek: 1, 2)")
        ne = int(eleman_sayisi)
        boylar = [L1, L2, L3][:ne]
        dofs = [_sayilar(s) for s in [serbestlik1, serbestlik2, serbestlik3][:ne]]
        display(Markdown("#### Eleman rijitlik matrisleri"))
        elemanlar = []
        for i, (Li, dof) in enumerate(zip(boylar, dofs), start=1):
            if len(dof) != 2:
                raise mo.MatrisHatasi(f"Eleman {i}: çubuk elemanın 2 SD numarası olmalı (örnek: 1, 2).")
            ki = mo.cubuk_eleman(E, A, Li, goster="sonuc", ad=f"k{i}")
            display(Markdown(f"**Eleman {i}** — global SD numaraları {dof}"))
            elemanlar.append((ki, dof))
        n = int(n_serbestlik) if int(n_serbestlik) > 0 else max(max(d) for d in dofs)
        display(Markdown("#### Birleştirme"))
        sonuc = mo.birlestir(elemanlar, n)
        ''',
        """
        Ortak düğümlerde eleman katkıları toplanır (örnekte $K_{22}=2EA/L$); diğer konumlara ne gelirse o yazılır,
        hiç eleman gelmeyen konumlar 0 kalır. Sonuç simetriktir ve mesnet uygulanmadan tekildir. Dene:
        eleman sayısı = 3, SD numaraları `1, 2` / `2, 3` / `3, 4`, ya da farklı boylar L1 = `L`, L2 = `2*L`.
        """,
    ))

    H.append(md(r"""
    ### Sınır koşulları ve çözüm
    Mesnetlenmemiş $\mathbf{K}$ tekildir ($\det=0$): yapı bütün olarak kayabilir, çözüm tek değildir.
    Bu defterde **mesnetlerdeki** yer değiştirmeler **sıfır** kabul edilir → o SD'lerin **satır ve sütunları silinir**
    (silme yalnız $u=0$ için geçerlidir; sıfırdan farklı bir mesnet oturması varsa satır ve sütun silinmez, sağ taraf düzeltilir —
    burada ele alınmaz). Kalan indirgenmiş sistem $\mathbf{K}_s\mathbf{u}_s=\mathbf{F}_s$ çözülür. Sonra
    **mesnet tepkileri** $\mathbf{R}=\mathbf{K}\mathbf{u}-\mathbf{F}$ bulunur: serbest SD'lerde $R_i=0$ çıkmalıdır (sağlama);
    sabit SD'lerdeki değerler mesnet tepkileridir ve genelde sıfırdan farklıdır. İşaret global eksene göredir ve
    $\sum R + \sum F = 0$ sağlanır.

    Aşağıdaki varsayılan: çelik iki çubuk ($EA/L = 20000$ N/mm), 1. SD sabit (düğüm 1 tutulu), 3. düğümde 10 000 N.
    Bir önceki hücreden çıkan $\mathbf{K}$'yi de buraya yapıştırabilirsin (sembolik olabilir: `k -k 0; -k 2*k -k; 0 -k k`).
    """))

    H.append(form(
        "⚓ 9e) Sınır koşulları ve çözüm: K u = F",
        '''
        K = "20000 -20000 0; -20000 40000 -20000; 0 -20000 20000" #@param {type:"string"}
        F = "0; 0; 10000" #@param {type:"string"}
        sabit = "1" #@param {type:"string"}
        ''',
        '''
        try:
            sabit_liste = [int(t) for t in sabit.replace(";", ",").split(",") if t.strip()]
        except ValueError:
            raise mo.MatrisHatasi(f"Sabit SD numaraları tam sayı olmalı: {sabit!r} (örnek: 1 ya da 1, 3)")
        sonuc = mo.sinir_kosulu(K, F, sabit=sabit_liste)
        ''',
        """
        Sabit SD'lerin satır ve sütunları silinince kalan sistem çözülebilir hale gelir. Tepkiler dış yüklerle dengededir:
        $\\sum R_i + \\sum F_i = 0$ (örnekte $-10\\,000 + 10\\,000 = 0$). Serbest SD'lerde $R_i = 0$ çıkmalıdır; bu bir
        sağlamadır, sabit SD'lerdeki değerler ise mesnet tepkileridir. İşaret kuralı: $R$ global eksen yönünde pozitiftir;
        $R_1 = -10\\,000$ N, mesnedin düğüm 1'i $-x$ yönünde (yüke zıt) tuttuğunu söyler.
        Dene: sabit = `1, 3` (iki ucu tutulu, ortadan yüklü: F = `0; 10000; 0`; tepkiler $R_1 = R_3 = -5000$ N çıkar,
        $\\sum R + \\sum F = 0$). Sabit kutusunu boş bırakırsan mesnetsiz sistem elde edersin: $\\mathbf{K}$ tekildir,
        yapı rijit cisim gibi kayar ve dengelenmemiş 10 000 N için statik çözüm yoktur; kırmızı ❌ kutusu çözüm olmadığını bildirir.
        """,
    ))

    H.append(md(r"""
    ### Baştan sona bir örnek: iki çubuk seri, 1. düğüm sabit, 3. düğümde $P$

    Düğüm 1 tutulu ($u_1 = 0$), düğüm 3'e $P$ çekme kuvveti. Burada $u_1, u_2, u_3$ düğümlerin yer değiştirmeleridir
    (çubukta her düğümün tek SD'si vardır: $x$ yönündeki yer değiştirme). Beklenen (elle): $u_1 = 0$, $u_2 = \dfrac{PL}{EA}$,
    $u_3 = \dfrac{2PL}{EA}$, mesnet tepkisi $R_1 = -P$ (eksi işareti: mesnet düğüm 1'i yüke zıt, $-x$ yönünde tutar;
    $R_1 + P = 0$ dengesi sağlanır); her iki eleman $P$ çekme taşır, gerilme $\sigma = P/A$.

    **Sayısal seçenek** (çelik): $E = 200\,000$ MPa, $A = 100$ mm², $L = 1000$ mm, $P = 10$ kN $= 10\,000$ N.
    Birimler tutarlı (N, mm, MPa): $EA/L = 200000\cdot100/1000 = 20\,000$ N/mm → $u_2 = 10000/20000 = 0{,}5$ mm, $u_3 = 1{,}0$ mm,
    $\sigma = 10000/100 = 100$ MPa.
    """))

    H.append(form(
        "🏗️ 9f) Baştan sona: iki çubuk seri, 1. düğüm sabit, 3. düğümde P",
        '''
        mod = "sembolik" #@param ["sembolik", "sayisal"]
        E_sayisal = 200000 #@param {type:"number"}
        A_sayisal = 100 #@param {type:"number"}
        L_sayisal = 1000 #@param {type:"number"}
        P_sayisal = 10000 #@param {type:"number"}
        ''',
        r'''
        import sympy as sp
        if mod == "sembolik":
            E, A, L, P = "E", "A", "L", "P"
            display(Markdown("Sembolik çözüm: $E$, $A$, $L$, $P$ harf olarak kalır; sonuç formül çıkar."))
        else:
            E, A, L, P = E_sayisal, A_sayisal, L_sayisal, P_sayisal
            display(Markdown(f"Sayısal çözüm — birimler: E = {E} MPa (N/mm²), A = {A} mm², L = {L} mm, P = {P} N "
                             f"→ EA/L [N/mm], u [mm], R [N], σ [MPa]."))
        display(Markdown("#### Adım 1 — Eleman rijitlik matrisleri (iki eleman aynı)"))
        k1 = mo.cubuk_eleman(E, A, L, ad="k1")
        k2 = mo.cubuk_eleman(E, A, L, goster="sonuc", ad="k2")
        display(Markdown("#### Adım 2 — Birleştirme: eleman 1 → global SD [1, 2], eleman 2 → global SD [2, 3]"))
        K = mo.birlestir([(k1, [1, 2]), (k2, [2, 3])], 3)
        display(Markdown("#### Adım 3 — Yük vektörü ve mesnet: 3. düğümde P, 1. SD sabit (düğüm 1 tutulu)"))
        F = [0, 0, P]
        u = mo.sinir_kosulu(K, F, sabit=[1])
        display(Markdown(r"#### Adım 4 — Eleman 1'in uç kuvvetleri: $\mathbf{f}^{(1)} = \mathbf{k}^{(1)}\mathbf{u}^{(1)}$"))
        display(Markdown(r"Burada $\mathbf{u}^{(1)} = [u_1, u_2]^T$ elemanın iki ucunun yer değiştirmesidir (kodda `u_e`), "
                         r"$\mathbf{k}^{(1)}$ eleman 1'in rijitlik matrisidir (kodda `k1`). Aşağıdaki çıktıda çarpımın sonucu "
                         r"genel adıyla $\mathbf{C}$ görünür; bu $\mathbf{f}^{(1)}$ demektir."))
        u_e = u.deger[0:2, 0]
        f1 = mo.carp(k1, u_e, adlar=["k1", "u_e"], goster="adimlar")
        N = f1.deger[1, 0]
        display(Markdown(r"Eksenel kuvvet $N^{(1)} = f_2^{(1)} = -f_1^{(1)} = \dfrac{EA}{L}(u_2 - u_1)$. "
                         r"$N>0$ çekme, $N<0$ basınçtır. $f_1^{(1)} = -P$, düğüm 1'in elemana uyguladığı kuvvettir; "
                         r"iç kuvvet değildir."))
        sigma = sp.simplify(N / mo.skaler_oku(A))
        display(Markdown("#### Özet"))
        display(Math(rf"u_2 = {mo.L(u.deger[1, 0])},\quad u_3 = {mo.L(u.deger[2, 0])},\quad "
                     rf"R_1 = {mo.L(sp.simplify((mo.matris(K) * u.deger)[0, 0] - mo.matris(F)[0, 0]))},\quad "
                     rf"N^{{(1)}} = {mo.L(N)},\quad \sigma = N/A = {mo.L(sigma)}"))
        if mod == "sayisal":
            display(Markdown(f"Okunuşu: u₂ = {float(u.deger[1, 0]):g} mm, u₃ = {float(u.deger[2, 0]):g} mm, "
                             f"N = {float(N):g} N (çekme), σ = {float(sigma):g} MPa."))
        ''',
        """
        Akış: eleman matrisleri → birleştirme → yük → sınır koşulu → çözüm → tepkiler ve eleman kuvvetleri.
        Sembolikte $u_3 = 2PL/EA$ (iki yay seri: esneklikler toplanır); sayısalda birimler tutarlıysa (N, mm, MPa)
        sonuç doğrudan mm ve N çıkar. Eleman kuvveti $N>0$ çekme, $N<0$ basınçtır; burada $N=+P$ (çekme) ve
        mesnet tepkisi $R_1=-P$ çıkar. Dene: mod = sayisal; sonra A'yı iki katına çıkar, yer değiştirme yarıya iner.
        """,
    ))

    # ------------------------------------------------------------------ 10
    H.append(md(r"""
    ## 10) Ayarlar

    Gösterimi derse göre ayarla (hesap her zaman kesin/sembolik yapılır, yalnız gösterim değişir):

    - **gösterim:** `hepsi` (kural + adımlar + sonuç + Python), `adimlar` (Python yok), `python` (yalnız kod ve sonuç),
      `sonuc` (yalnız sonuç), `yok` (sessiz; `.deger` ile programda kullan).
    - **ondalık:** kesirler yerine ondalık göster (örn. 1/3 → 0.3333), **basamak** anlamlı basamak sayısı.
    - **Python bölümü** ve **kural kutusu** ayrı ayrı açılıp kapanabilir; **en fazla eleman**: eleman eleman anlatım sınırı
      (büyük matrislerde yalnız örnek eleman gösterilir).

    Bu hücre ayarları uygular ve etkisini küçük bir örnekle gösterir; ayar sonraki tüm hücreler için geçerlidir.
    """))

    H.append(form(
        "⚙️ 10) Ayarlar (gösterim modu, ondalık, Python bölümü, kural kutusu)",
        '''
        gosterim = "hepsi" #@param ["hepsi", "adimlar", "python", "sonuc", "yok"]
        ondalik = False #@param {type:"boolean"}
        basamak = 4 #@param {type:"integer"}
        python_bolumu = True #@param {type:"boolean"}
        kural_kutusu = True #@param {type:"boolean"}
        en_fazla_eleman = 36 #@param {type:"integer"}
        ''',
        '''
        a = mo.ayarla(goster=gosterim, ondalik=bool(ondalik), basamak=max(1, int(basamak)),
                      python=bool(python_bolumu), kural=bool(kural_kutusu), en_fazla_eleman=max(1, int(en_fazla_eleman)))
        display(Markdown(f"Ayarlar: gösterim = `{a.goster}`, ondalık = `{a.ondalik}`, basamak = `{a.basamak}`, "
                         f"Python = `{a.python}`, kural = `{a.kural}`, en fazla eleman = `{a.en_fazla_eleman}`"))
        display(Markdown("Örnek (ters matris) bu ayarlarla:"))
        sonuc = mo.ters("4 7; 2 6")
        ''',
        """
        Sınava çalışırken `adimlar`, kodu öğrenirken `python`, hızlı kontrol için `sonuc` kullan. Ondalık gösterim
        mühendislik sayılarında okumayı kolaylaştırır; kesir gösterimi ise kesin sonuç verir.
        """,
    ))

    # ------------------------------------------------------------------ 11
    H.append(md(r"""
    ## 11) Serbest çalışma alanı

    Burası normal bir kod hücresi: formlar yetmediğinde fonksiyonları doğrudan çağır. Her fonksiyon bir `Sonuc` döndürür;
    `.deger` (sympy değeri), `.python_kodu`, `.python_ciktisi`, `.anlatim.markdown()` alanları vardır ve bir sonucu
    doğrudan başka bir fonksiyona verebilirsin (`C = mo.carp(A, B); mo.transpoz(C)`).

    | Çağrı | Ne yapar |
    |---|---|
    | `mo.topla(A, B)`, `mo.cikar(A, B)`, `mo.skaler(k, A)` | toplama, çıkarma, skalerle çarpma |
    | `mo.carp(A, B, C)` | matris çarpımı (zincir) |
    | `mo.transpoz(A)`, `mo.iz(A)`, `mo.rank(A)` | transpoz, iz, rank |
    | `mo.determinant(A, yontem="kofaktor")`, `mo.ters(A, yontem="gauss")` | determinant, ters |
    | `mo.coz(A, b, yontem="gauss", bilinmeyen="u")` | denklem sistemi |
    | `mo.ozdeger(A)`, `mo.ozdeger(K, M)` | özdeğer / doğal frekans |
    | `mo.cubuk_eleman(E, A, L)`, `mo.kiris_eleman(E, I, L)`, `mo.kafes_eleman(E, A, L, aci)` | eleman matrisleri |
    | `mo.birlestir([(k1, [1, 2]), (k2, [2, 3])], 3)`, `mo.sinir_kosulu(K, F, sabit=[1])` | birleştirme, sınır koşulu + çözüm |
    | `mo.ayarla(goster="adimlar", ondalik=True)` | ayarlar; `goster="yok"` sessiz |
    """))

    H.append(kod('''
    import matris_ogren as mo

    # Örnek 1: sonuçları zincirle — çarpımın transpozu (B^T A^T ile aynı çıkar)
    C = mo.carp("1 2; 3 4", "5 6; 7 8", goster="sonuc")
    mo.transpoz(C, goster="sonuc")

    # Örnek 2: kafes çubuğu (E = 200000 MPa, A = 50 mm², L = 1414 mm, 45°), yalnız sonuç
    k = mo.kafes_eleman(200000, 50, 1414, 45, goster="sonuc")
    print("k[0,0] =", k.deger[0, 0], "N/mm")

    # Örnek 3: sessiz hesap, değeri programda kullan
    d = mo.determinant("2 1 0; 1 3 1; 0 1 4", goster="yok")
    print("det =", d.deger)

    # Kendi denemelerini buraya yaz. Fonksiyon listesi:
    mo.yardim()
    '''))

    return H


# ============================================================================
# Defteri kur ve yaz
# ============================================================================
def defter_olustur() -> nbformat.NotebookNode:
    kaynak = MODUL.read_bytes()
    nb = new_notebook()
    nb.cells = hucreler(kaynak)
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"},
        "colab": {"name": "Matris_Ogren.ipynb", "provenance": [], "toc_visible": True},
    }
    return nb


def main() -> None:
    if not MODUL.exists():
        raise SystemExit(f"Modül bulunamadı: {MODUL}")
    nb = defter_olustur()
    nbformat.validate(nb)
    with open(DEFTER, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
    n_kod = sum(1 for c in nb.cells if c.cell_type == "code")
    n_form = sum(1 for c in nb.cells if c.cell_type == "code" and c.metadata.get("cellView") == "form")
    print(f"✅ {DEFTER.name} yazıldı: {len(nb.cells)} hücre ({n_md} markdown, {n_kod} kod, {n_form} form), "
          f"{DEFTER.stat().st_size:,} bayt; gömülü modül {len(MODUL.read_bytes()):,} bayt "
          f"(sha256 {hashlib.sha256(MODUL.read_bytes()).hexdigest()[:12]}…)")


if __name__ == "__main__":
    main()
