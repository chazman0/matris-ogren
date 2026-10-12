---
baslik: Devrik ve simetri
bolum: matris
ozet: Satırları sütun yapmak, (AB)ᵀ = BᵀAᵀ kuralı, simetrik matrisler ve TᵀkT dönüşümü.
sure: 30
---

## Neden?

Her rijitlik matrisi **simetriktir**: $k_{ij}=k_{ji}$. Bu, Maxwell–Betti karşıtlık teoreminin matris dilidir. 1. düğümü itince 2. düğümde doğan kuvvet, 2. düğümü itince 1. düğümde doğan kuvvete eşittir. Eğik bir elemanı global eksene taşıyan $T^T k\,T$ formülünde de devrik vardır. Bu derste devriği ve simetriyi gözle görerek öğreneceksin.

## Devrik nedir?

::: tanim Devrik
$A$ $m\times n$ ise **devriği** (transpose) $A^T$ $n\times m$'dir ve $(A^T)_{ij}=a_{ji}$'dir. $A$'nın $\ka{1.}$ satırı $A^T$'nin $\kb{1.}$ sütunu olur.
:::

$$
A=\begin{bmatrix}\ka{1}&\ka{2}&\ka{3}\\\kb{4}&\kb{5}&\kb{6}\end{bmatrix}
\quad\xrightarrow{\ \text{devrik}\ }\quad
A^T=\begin{bmatrix}\ka{1}&\kb{4}\\\ka{2}&\kb{5}\\\ka{3}&\kb{6}\end{bmatrix}
$$

Kare matriste devrik, **ana köşegen** etrafında ayna yansımasıdır. Köşegen elemanları yerinde kalır, karşılıklı hücreler yer değiştirir.

::: sekil Ana köşegen bir aynadır
<svg viewBox="0 0 320 200" width="100%" font-family="system-ui" font-size="14" fill="currentColor">
<g fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5">
<path d="M40 30 h-8 v140 h8 M180 30 h8 v140 h-8"/>
</g>
<rect x="52" y="40" width="36" height="36" rx="6" fill="var(--sema-c-bg,rgba(16,185,129,.16))"/>
<rect x="92" y="82" width="36" height="36" rx="6" fill="var(--sema-c-bg,rgba(16,185,129,.16))"/>
<rect x="132" y="124" width="36" height="36" rx="6" fill="var(--sema-c-bg,rgba(16,185,129,.16))"/>
<rect class="vurgu" rx="6" x="92" y="40" width="36" height="36" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<rect class="vurgu" rx="6" x="52" y="82" width="36" height="36" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<g text-anchor="middle">
<text x="70" y="63">a₁₁</text><text x="110" y="63">a₁₂</text><text x="150" y="63">a₁₃</text>
<text x="70" y="105">a₂₁</text><text x="110" y="105">a₂₂</text><text x="150" y="105">a₂₃</text>
<text x="70" y="147">a₃₁</text><text x="110" y="147">a₃₂</text><text x="150" y="147">a₃₃</text>
</g>
<path d="M44 34 L176 166" stroke="var(--sema-c,#10b981)" stroke-width="2" stroke-dasharray="6 5" fill="none"/>
<path class="ok" pathLength="1" d="M112 38 C 30 20, 20 70, 56 96" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<polyline class="ok-uc" points="46,90 56,96 50,85" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<path class="ok" pathLength="1" d="M88 118 C 110 140, 140 110, 124 80" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="1.8"/>
<polyline class="ok-uc" points="118,88 124,80 128,90" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="1.8"/>
<text x="250" y="70" text-anchor="middle" fill="var(--sema-c,#10b981)">ana köşegen</text>
<text x="250" y="88" text-anchor="middle" fill="var(--sema-c,#10b981)">yerinde kalır</text>
<text x="250" y="130" text-anchor="middle">a₁₂ ↔ a₂₁</text>
<text x="250" y="148" text-anchor="middle">a₁₃ ↔ a₃₁</text>
</svg>
:::

Kendin dene: bir hücreye dokun, aynadaki eşinin nereye gittiğini izle. Girdiyi dikdörtgen bir matrise çevirip boyutun nasıl döndüğüne bak.

::: etkilesim transpoz-aynasi
{"A": "1 2 3; 4 5 6"}
:::

## Devriğin kuralları

$$
\begin{aligned}
(A^T)^T &= A && \text{iki kez yansıyan geri döner}\\
(A+B)^T &= A^T+B^T\\
(kA)^T &= k\,A^T\\
(AB)^T &= \kutub{B^T}\,\kutua{A^T} && \text{sıra ters döner}
\end{aligned}
$$

::: hata $(AB)^T=A^TB^T$ yazmak
Devrik çarpımın sırasını **ters çevirir**. Gömleği önce giyip sonra ceketi giyersin; çıkarırken önce ceket, sonra gömlek çıkar. Boyutlar da bunu zorunlu kılar: $A$ $2\times 3$, $B$ $3\times 4$ ise $A^TB^T$ $(3\times 2)(4\times 3)$ olur ve tanımsızdır.
:::

## Simetrik ve ters simetrik matrisler

::: tanim Simetrik matris
$A^T=A$ ise, yani her $i,j$ için $a_{ij}=a_{ji}$ ise kare matris $A$ **simetriktir** (symmetric). $A^T=-A$ ise **ters simetriktir** (skew-symmetric); ters simetrik matrisin köşegeni sıfırdır.
:::

$$
\underbrace{\begin{bmatrix}2&\kutua{-1}&0\\\kutua{-1}&2&\kutub{-1}\\0&\kutub{-1}&1\end{bmatrix}}_{\text{simetrik}}
\qquad
\underbrace{\begin{bmatrix}\kc{0}&\ka{3}\\\kb{-3}&\kc{0}\end{bmatrix}}_{\text{ters simetrik}}
$$

Her kare matris bir simetrik ve bir ters simetrik parçanın toplamıdır:

$$
A=\underbrace{\tfrac12\,(A+A^T)}_{\ka{\text{simetrik}}}+\underbrace{\tfrac12\,(A-A^T)}_{\kb{\text{ters simetrik}}}
$$

$A^TA$ ve $AA^T$ çarpımları, $A$ ne olursa olsun **her zaman simetriktir**. Aşağıda kendin gör: $A^T$ ile $A$'yı çarp, sonuçta karşılıklı hücrelerin eşit çıktığına bak.

::: etkilesim carpim-gezgini
{"A": "1 0 1; 2 1 0", "B": "1 2; 0 1; 1 0", "baslik": "AᵀA her zaman simetrik"}
:::

::: not Neden $A^TA$ simetrik?
Kuralı uygula: $(A^TA)^T=A^T(A^T)^T=A^TA$. Devriği kendine eşit olduğu için simetriktir. En küçük kareler yöntemindeki normal denklemler $A^TA\,\mathbf{x}=A^T\mathbf{b}$ bu yüzden hep simetrik bir sistem verir.
:::

## Çözümlü örnekler

::: ornek Dikdörtgen bir matrisin devriği
$A=\begin{bmatrix}1&2&3\\4&5&6\end{bmatrix}$ ise $A^T$ nedir?
--- ipucu
1. satırı 1. sütuna, 2. satırı 2. sütuna yaz. Boyut $2\times 3$'ten $3\times 2$'ye döner.
--- cevap
$$
A^T=\begin{bmatrix}\ka{1}&\kb{4}\\\ka{2}&\kb{5}\\\ka{3}&\kb{6}\end{bmatrix}
$$
--- kod
mo.transpoz("1 2 3; 4 5 6")
--- kontrol
r.deger == sp.Matrix([[1, 4], [2, 5], [3, 6]])
:::

::: ornek Çarpımın devriği
$A=\begin{bmatrix}1&2\\3&4\end{bmatrix}$, $B=\begin{bmatrix}0&1\\1&0\end{bmatrix}$ için $(AB)^T$ nedir?
--- ipucu
Önce $AB$'yi bul, sonra devriğini al.
--- cevap
$$
AB=\begin{bmatrix}2&1\\4&3\end{bmatrix}
\quad\Longrightarrow\quad
(AB)^T=\begin{bmatrix}\kutuc{2}&\kutuc{4}\\\kutuc{1}&\kutuc{3}\end{bmatrix}
$$
$B$ sütunların yerini değiştiren bir **permütasyon** matrisidir.
--- kod
mo.transpoz(mo.carp("1 2; 3 4", "0 1; 1 0"))
--- kontrol
r.deger == sp.Matrix([[2, 4], [1, 3]])
:::

::: ornek Kuralı doğrula: $B^TA^T$
Aynı matrisler için $B^TA^T$'yi hesapla ve önceki sonuçla karşılaştır.
--- cevap
$$
\kutub{B^T}\,\kutua{A^T}=\begin{bmatrix}0&1\\1&0\end{bmatrix}\begin{bmatrix}1&3\\2&4\end{bmatrix}=\begin{bmatrix}\kc{2}&\kc{4}\\\kc{1}&\kc{3}\end{bmatrix}=(AB)^T
$$
--- kod
mo.carp(mo.transpoz("0 1; 1 0"), mo.transpoz("1 2; 3 4"))
--- kontrol
r.deger == sp.Matrix([[2, 4], [1, 3]])
--- yorum
$A^TB^T$ ise $\begin{bmatrix}3&1\\4&2\end{bmatrix}$ çıkar: yanlış sıra yanlış sonuç verir.
:::

::: ornek $A^TA$ simetriktir
$A=\begin{bmatrix}1&2\\0&1\\1&0\end{bmatrix}$ için $A^TA$ nedir?
--- ipucu
$A^T$ $2\times 3$, $A$ $3\times 2$: sonuç $2\times 2$. $(i,j)$ hücresi, $A$'nın $i.$ ve $j.$ sütunlarının iç çarpımıdır.
--- cevap
$$
A^TA=\begin{bmatrix}1&0&1\\2&1&0\end{bmatrix}\begin{bmatrix}1&2\\0&1\\1&0\end{bmatrix}
=\begin{bmatrix}1+0+1&\kutua{2+0+0}\\\kutua{2+0+0}&4+1+0\end{bmatrix}
=\begin{bmatrix}2&\ka{2}\\\ka{2}&5\end{bmatrix}
$$
--- kod
mo.carp(mo.transpoz("1 2; 0 1; 1 0"), "1 2; 0 1; 1 0")
--- kontrol
r.deger == sp.Matrix([[2, 2], [2, 5]])
:::

::: ornek Simetrik parça
$A=\begin{bmatrix}1&4\\2&3\end{bmatrix}$ matrisinin simetrik parçası $\tfrac12(A+A^T)$ nedir?
--- cevap
$$
A+A^T=\begin{bmatrix}1&4\\2&3\end{bmatrix}+\begin{bmatrix}1&2\\4&3\end{bmatrix}=\begin{bmatrix}2&6\\6&6\end{bmatrix}
\quad\Longrightarrow\quad
\tfrac12(A+A^T)=\begin{bmatrix}1&\kutua{3}\\\kutua{3}&3\end{bmatrix}
$$
--- kod
mo.skaler("1/2", mo.topla("1 4; 2 3", mo.transpoz("1 4; 2 3")))
--- kontrol
r.deger == sp.Matrix([[1, 3], [3, 3]])
:::

::: ornek Ters simetrik parça
Aynı $A$ için $\tfrac12(A-A^T)$ nedir? İki parçanın toplamının $A$'yı verdiğini kontrol et.
--- cevap
$$
\tfrac12(A-A^T)=\tfrac12\begin{bmatrix}0&2\\-2&0\end{bmatrix}=\begin{bmatrix}\kc{0}&\kb{1}\\\kb{-1}&\kc{0}\end{bmatrix}
\qquad
\begin{bmatrix}1&3\\3&3\end{bmatrix}+\begin{bmatrix}0&1\\-1&0\end{bmatrix}=\begin{bmatrix}1&4\\2&3\end{bmatrix}=A
$$
--- kod
mo.skaler("1/2", mo.cikar("1 4; 2 3", mo.transpoz("1 4; 2 3")))
--- kontrol
r.deger == sp.Matrix([[0, 1], [-1, 0]])
:::

::: ornek Vektörün boyu: $\mathbf{u}^T\mathbf{u}$
$\mathbf{u}=\begin{bmatrix}3\\4\end{bmatrix}$ ise $\mathbf{u}^T\mathbf{u}$ nedir?
--- cevap
$$
\mathbf{u}^T\mathbf{u}=\begin{bmatrix}\ka{3}&\ka{4}\end{bmatrix}\begin{bmatrix}\kb{3}\\\kb{4}\end{bmatrix}=9+16=\kutuc{25}
\qquad
\lVert\mathbf{u}\rVert=\sqrt{25}=5
$$
--- kod
mo.carp(mo.transpoz([3, 4]), [3, 4])
--- kontrol
r.deger == sp.Matrix([[25]])
:::

::: ornek Eğik çubuğu global eksene taşımak: $T^T k\,T$
Bir çubuk yatayla $\cos\theta=3/5$, $\sin\theta=4/5$ açı yapıyor. Yerel matrisi $k=\tfrac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$, $\tfrac{EA}{L}=1$ alalım. Dönüşüm matrisi $T=\begin{bmatrix}c&s&0&0\\0&0&c&s\end{bmatrix}$. Global matris $K=T^T k\,T$ nedir?
--- ipucu
$T^T$ $4\times 2$, $k$ $2\times 2$, $T$ $2\times 4$: sonuç $4\times 4$. Hücrelerde $c^2$, $cs$, $s^2$ görmelisin.
--- cevap
$$
K=\underbrace{\begin{bmatrix}c&0\\s&0\\0&c\\0&s\end{bmatrix}}_{T^T}
\begin{bmatrix}1&-1\\-1&1\end{bmatrix}
\underbrace{\begin{bmatrix}c&s&0&0\\0&0&c&s\end{bmatrix}}_{T}
=\begin{bmatrix}
\ka{c^2}&\kb{cs}&-c^2&-cs\\
\kb{cs}&\kc{s^2}&-cs&-s^2\\
-c^2&-cs&c^2&cs\\
-cs&-s^2&cs&s^2
\end{bmatrix}
$$
$c^2=\tfrac{9}{25}$, $cs=\tfrac{12}{25}$, $s^2=\tfrac{16}{25}$. Sonuç simetriktir.
--- kod
T = "3/5 4/5 0 0; 0 0 3/5 4/5"
mo.carp(mo.transpoz(T), "1 -1; -1 1", T)
--- kontrol
r.deger[0, 0] == sp.Rational(9, 25) and r.deger[0, 1] == sp.Rational(12, 25) and r.deger == r.deger.T
--- yorum
Formül simetriyi korur: $(T^TkT)^T=T^Tk^T(T^T)^T=T^TkT$. $k$ simetrikse $K$ da simetriktir. Bu matrisi kafes dersinde yeniden kuracaksın.
:::

::: ornek Hangisi simetrik?
$P=\begin{bmatrix}4&1\\1&3\end{bmatrix}$, $Q=\begin{bmatrix}0&2\\-2&0\end{bmatrix}$, $R=\begin{bmatrix}1&2\\3&1\end{bmatrix}$. Hangisi simetrik, hangisi ters simetrik, hangisi ikisi de değil?
--- cevap
$$
P^T=P\ \Rightarrow\ \kc{\text{simetrik}}
\qquad
Q^T=\begin{bmatrix}0&-2\\2&0\end{bmatrix}=-Q\ \Rightarrow\ \kb{\text{ters simetrik}}
\qquad
r_{12}=2\ne 3=r_{21}\ \Rightarrow\ \ksil{\text{hiçbiri}}
$$
:::

## Mühendislikte

::: muhendislik Simetri bir sağlamlık testidir
Kendi yazdığın bir sonlu eleman kodunda global $K$ matrisi simetrik çıkmıyorsa, birleştirmede ya da dönüşümde bir hata vardır. Yığma köprü modelinde kütle matrisi $M$ ve rijitlik matrisi $K$ simetriktir. Bu sayede OMA ile karşılaştıracağın mod şekilleri gerçek sayılardır ve birbirine diktir: $\boldsymbol\phi_i^T M\boldsymbol\phi_j=0$, $i\ne j$. MAC ölçütü bu dikliği kullanır.
:::

::: ozet
- $(A^T)_{ij}=a_{ji}$: satırlar sütun olur, $m\times n$ → $n\times m$.
- $(AB)^T=B^TA^T$: sıra ters döner.
- $A^T=A$ simetrik, $A^T=-A$ ters simetrik; her kare matris ikisinin toplamıdır.
- $A^TA$ ve $T^TkT$ her zaman simetriktir.
- Rijitlik ve kütle matrisleri simetriktir; simetri bozulursa kodda hata ara.
:::

## Alıştırma

::: alistirma transpoz
{"zorluk": 1}
:::

::: alistirma transpoz
{"zorluk": 2}
:::

::: alistirma carpim
{"zorluk": 2, "boyut": 3}
:::
