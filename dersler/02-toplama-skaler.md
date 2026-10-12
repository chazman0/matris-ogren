---
baslik: Toplama, çıkarma ve skalerle çarpma
bolum: matris
ozet: Eleman eleman işlemler, boyut şartı, özellikler ve yük birleşimleri.
sure: 25
---

## Neden?

Bir köprü kirişine hem kendi ağırlığı (ölü yük $G$) hem trafik (hareketli yük $Q$) etkir. Yönetmelik ikisini katsayılarla çarpıp toplamanı ister: $1.35\,G+1.5\,Q$. Düğüm kuvvetlerini birer vektör olarak yazarsan bu hesap tek satırdır. İki yayı paralel bağladığında rijitlik matrisleri de aynı biçimde toplanır.

## Matris toplama

::: tanim Toplama ve çıkarma
Aynı boyuttaki $A$ ve $B$ matrislerinin **toplamı** (sum), karşılıklı elemanların toplanmasıyla bulunur: $(A+B)_{ij}=a_{ij}+b_{ij}$. **Fark** da aynı yolla bulunur: $(A-B)_{ij}=a_{ij}-b_{ij}$. Sonuç da aynı boyuttadır.
:::

Her hücre yalnız kendi karşılığıyla buluşur. Mavi $A$'dan, turuncu $B$'den gelir, yeşil sonuçtur:

$$
\begin{bmatrix}\ka{1}&\ka{-2}\\\ka{3}&\ka{0}\end{bmatrix}
+
\begin{bmatrix}\kb{4}&\kb{5}\\\kb{-1}&\kb{2}\end{bmatrix}
=
\begin{bmatrix}\ka{1}+\kb{4}&\ka{-2}+\kb{5}\\\ka{3}+(\kb{-1})&\ka{0}+\kb{2}\end{bmatrix}
=
\begin{bmatrix}\kc{5}&\kc{3}\\\kc{2}&\kc{2}\end{bmatrix}
$$

::: sekil Karşılıklı hücreler sonuca akar
<svg viewBox="0 0 360 150" width="100%" font-family="system-ui" font-size="13" fill="currentColor">
<g fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5">
<path d="M18 30 h-6 v80 h6 M92 30 h6 v80 h-6"/>
<path d="M148 30 h-6 v80 h6 M222 30 h6 v80 h-6"/>
<path d="M278 30 h-6 v80 h6 M352 30 h6 v80 h-6"/>
</g>
<rect class="vurgu" rx="6" x="20" y="34" width="34" height="34" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<rect class="vurgu" rx="6" x="150" y="34" width="34" height="34" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<rect class="vurgu" rx="6" x="280" y="34" width="34" height="34" fill="var(--sema-c-bg,rgba(16,185,129,.16))" stroke="var(--sema-c,#10b981)" stroke-width="2"/>
<g text-anchor="middle">
<text x="37" y="56">1</text><text x="75" y="56">-2</text><text x="37" y="96">3</text><text x="75" y="96">0</text>
<text x="167" y="56">4</text><text x="205" y="56">5</text><text x="167" y="96">-1</text><text x="205" y="96">2</text>
<text x="297" y="56" font-weight="700">5</text><text x="335" y="56">3</text><text x="297" y="96">2</text><text x="335" y="96">2</text>
<text x="120" y="76" font-size="18">+</text><text x="250" y="76" font-size="18">=</text>
<text x="55" y="135" fill="var(--sema-a,#3b82f6)">A</text><text x="185" y="135" fill="var(--sema-b,#f59e0b)">B</text><text x="315" y="135" fill="var(--sema-c,#10b981)">A+B</text>
</g>
<path class="ok" pathLength="1" d="M37 32 C 100 -4, 230 -4, 292 30" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<polyline class="ok-uc" points="284,26 292,30 288,22" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<path class="ok" pathLength="1" d="M167 32 C 200 10, 260 10, 298 30" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<polyline class="ok-uc" points="290,27 298,30 294,22" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
</svg>
:::

Kendin dene: adım adım ilerle ya da oynat. Her adımda bir hücre çifti sonuca akar.

::: etkilesim eleman-eleman
{"A": "1 -2; 3 0", "B": "4 5; -1 2", "islem": "topla", "baslik": "Karşılıklı hücreler toplanır"}
:::

::: hata Farklı boyutları toplamak
$2\times 3$'lük bir matrisle $3\times 2$'lik bir matris toplanamaz; eleman sayıları aynı (6) olsa bile. Toplama için **satır sayıları da sütun sayıları da** eşit olmalıdır. Uygulama böyle bir girdide boyut uyuşmuyor uyarısı verir.
:::

## Skalerle çarpma

::: tanim Skaler çarpım
Bir **skaler** (scalar) tek bir sayıdır. $kA$, $A$'nın her elemanının $k$ ile çarpılmasıdır: $(kA)_{ij}=k\,a_{ij}$. Boyut değişmez.
:::

$$
\kb{3}\begin{bmatrix}\ka{2}&\ka{-1}\\\ka{0}&\ka{4}\end{bmatrix}
=
\begin{bmatrix}\kb{3}\cdot\ka{2}&\kb{3}\cdot(\ka{-1})\\\kb{3}\cdot\ka{0}&\kb{3}\cdot\ka{4}\end{bmatrix}
=
\begin{bmatrix}\kc{6}&\kc{-3}\\\kc{0}&\kc{12}\end{bmatrix}
$$

$-1$ ile çarpmak işaretleri çevirir: $A-B=A+(-1)B$. Çıkarma aslında skaler çarpım ve toplamadır.

::: etkilesim eleman-eleman
{"A": "2 -1; 0 4", "islem": "skaler", "k": 3, "baslik": "Her hücre aynı sayıyla çarpılır"}
:::

## Özellikler

Toplama ve skaler çarpım, sayılardaki alışık olduğun kurallara uyar. $A$, $B$, $C$ aynı boyutta, $k$ ve $l$ skaler olsun:

$$
\begin{aligned}
A+B &= B+A && \text{değişme}\\
(A+B)+C &= A+(B+C) && \text{birleşme}\\
A+0 &= A,\quad A+(-A)=0 && \text{etkisiz ve ters eleman}\\
\kb{k}(\ka{A}+\kc{B}) &= \kb{k}\ka{A}+\kb{k}\kc{B} && \text{dağılma}\\
(k+l)A &= kA+lA,\quad k(lA)=(kl)A
\end{aligned}
$$

::: not
Toplamada sıra önemli değildir. Matris **çarpımında** ise sıra önemlidir; bunu 3. derste göreceksin.
:::

## Çözümlü örnekler

::: ornek 2×2 toplama
$A=\begin{bmatrix}1&-2\\3&0\end{bmatrix}$, $B=\begin{bmatrix}4&5\\-1&2\end{bmatrix}$ için $A+B$ nedir?
--- ipucu
Aynı konumdaki iki sayıyı topla; negatif sayılarda işarete dikkat et.
--- cevap
$$
\begin{bmatrix}\ka{1}+\kb{4}&\ka{-2}+\kb{5}\\\ka{3}+(\kb{-1})&\ka{0}+\kb{2}\end{bmatrix}
=
\begin{bmatrix}\kutuc{5}&\kutuc{3}\\\kutuc{2}&\kutuc{2}\end{bmatrix}
$$
--- kod
mo.topla("1 -2; 3 0", "4 5; -1 2")
--- kontrol
r.deger == sp.Matrix([[5, 3], [2, 2]])
:::

::: ornek 2×3 çıkarma
$\begin{bmatrix}5&0&3\\2&-1&4\end{bmatrix}-\begin{bmatrix}1&2&3\\4&5&6\end{bmatrix}$ nedir?
--- ipucu
Her hücrede soldakinden sağdakini çıkar. $0-2$ ve $-1-5$ negatif çıkar.
--- cevap
$$
\begin{bmatrix}\ka{5}-\kb{1}&\ka{0}-\kb{2}&\ka{3}-\kb{3}\\\ka{2}-\kb{4}&\ka{-1}-\kb{5}&\ka{4}-\kb{6}\end{bmatrix}
=
\begin{bmatrix}\kc{4}&\kc{-2}&\kc{0}\\\kc{-2}&\kc{-6}&\kc{-2}\end{bmatrix}
$$
--- kod
mo.cikar("5 0 3; 2 -1 4", "1 2 3; 4 5 6")
--- kontrol
r.deger == sp.Matrix([[4, -2, 0], [-2, -6, -2]])
:::

::: ornek Skalerle çarpma
$3\begin{bmatrix}2&-1\\0&4\end{bmatrix}$ nedir?
--- cevap
$$
\kb{3}\begin{bmatrix}\ka{2}&\ka{-1}\\\ka{0}&\ka{4}\end{bmatrix}
\xrightarrow{\ \text{her hücre}\ \times\kb{3}\ }
\begin{bmatrix}\kc{6}&\kc{-3}\\\kc{0}&\kc{12}\end{bmatrix}
$$
--- kod
mo.skaler(3, "2 -1; 0 4")
--- kontrol
r.deger == sp.Matrix([[6, -3], [0, 12]])
:::

::: ornek Doğrusal birleşim: $2A-3B$
$A=\begin{bmatrix}1&2\\0&-1\end{bmatrix}$, $B=\begin{bmatrix}2&0\\1&1\end{bmatrix}$ için $2A-3B$ nedir?
--- ipucu
Önce iki skaler çarpımı ayrı ayrı yap, sonra çıkar.
--- cevap
$$
\underbrace{\begin{bmatrix}\ka{2}&\ka{4}\\\ka{0}&\ka{-2}\end{bmatrix}}_{2A}
-
\underbrace{\begin{bmatrix}\kb{6}&\kb{0}\\\kb{3}&\kb{3}\end{bmatrix}}_{3B}
=
\begin{bmatrix}\kc{-4}&\kc{4}\\\kc{-3}&\kc{-5}\end{bmatrix}
$$
--- kod
mo.cikar(mo.skaler(2, "1 2; 0 -1"), mo.skaler(3, "2 0; 1 1"))
--- kontrol
r.deger == sp.Matrix([[-4, 4], [-3, -5]])
:::

::: ornek Bilinmeyen matris
$X+\begin{bmatrix}3&-1\\2&5\end{bmatrix}=\begin{bmatrix}7&0\\-2&5\end{bmatrix}$ ise $X$ nedir?
--- ipucu
Sayılardaki gibi: bilinen matrisi karşı tarafa çıkararak geçir.
--- cevap
$$
X=\begin{bmatrix}\ka{7}&\ka{0}\\\ka{-2}&\ka{5}\end{bmatrix}-\begin{bmatrix}\kb{3}&\kb{-1}\\\kb{2}&\kb{5}\end{bmatrix}
=
\begin{bmatrix}\kutuc{4}&\kutuc{1}\\\kutuc{-4}&\kutuc{0}\end{bmatrix}
$$
--- kod
mo.cikar("7 0; -2 5", "3 -1; 2 5")
--- kontrol
r.deger == sp.Matrix([[4, 1], [-4, 0]])
:::

::: ornek Yük birleşimi: $1.35\,G+1.5\,Q$
Üç düğümlü bir kirişte düşey düğüm yükleri (kN) ölü yük için $G=\begin{bmatrix}10\\20\\10\end{bmatrix}$, hareketli yük için $Q=\begin{bmatrix}6\\8\\6\end{bmatrix}$. Tasarım yükü $F=1.35\,G+1.5\,Q$ nedir?
--- ipucu
$1.35=\tfrac{27}{20}$ ve $1.5=\tfrac{3}{2}$. Önce iki vektörü katsayılarla çarp, sonra topla.
--- cevap
$$
\kb{1.35}\begin{bmatrix}\ka{10}\\\ka{20}\\\ka{10}\end{bmatrix}
+
\kb{1.5}\begin{bmatrix}\ka{6}\\\ka{8}\\\ka{6}\end{bmatrix}
=
\begin{bmatrix}13.5\\27\\13.5\end{bmatrix}
+
\begin{bmatrix}9\\12\\9\end{bmatrix}
=
\begin{bmatrix}\kutuc{22.5}\\\kutuc{39}\\\kutuc{22.5}\end{bmatrix}\ \text{kN}
$$
--- kod
G = [10, 20, 10]
Q = [6, 8, 6]
mo.topla(mo.skaler("27/20", G), mo.skaler("3/2", Q))
--- kontrol
r.deger == sp.Matrix([sp.Rational(45, 2), 39, sp.Rational(45, 2)])
--- yorum
Sistem doğrusal elastik olduğu sürece **süperpozisyon** geçerlidir: yükleri birleştirmek ile yer değiştirmeleri birleştirmek aynı sonucu verir. $K(1.35\,\mathbf{u}_G+1.5\,\mathbf{u}_Q)=1.35\,G+1.5\,Q$.
:::

::: ornek Paralel yayların rijitlik matrisi
İki düğüm arasına $k_1=100$ kN/m ve $k_2=50$ kN/m yayları paralel bağlanmıştır. Her yayın matrisi $k\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$ biçimindedir. Toplam rijitlik matrisi nedir?
--- ipucu
Paralel yaylar aynı iki düğüme bağlıdır; matrisleri aynı hücrelere düşer ve doğrudan toplanır.
--- cevap
$$
\underbrace{\begin{bmatrix}\ka{100}&\ka{-100}\\\ka{-100}&\ka{100}\end{bmatrix}}_{k_1}
+
\underbrace{\begin{bmatrix}\kb{50}&\kb{-50}\\\kb{-50}&\kb{50}\end{bmatrix}}_{k_2}
=
\underbrace{\begin{bmatrix}\kc{150}&\kc{-150}\\\kc{-150}&\kc{150}\end{bmatrix}}_{(k_1+k_2)}
$$
--- kod
mo.topla("100 -100; -100 100", "50 -50; -50 50")
--- kontrol
r.deger == sp.Matrix([[150, -150], [-150, 150]])
--- yorum
Paralel yaylarda rijitlikler toplanır: $k_{\text{eş}}=k_1+k_2$. Sonlu elemanda **birleştirme** (assembly) işleminin özü budur; 14. derste her elemanın matrisini global matristeki kendi hücrelerine ekleyeceksin.
:::

::: ornek Toplanamayan matrisler
$A=\begin{bmatrix}1&2&3\\4&5&6\end{bmatrix}$ ile $B=\begin{bmatrix}1&2\\3&4\\5&6\end{bmatrix}$ toplanabilir mi?
--- cevap
$$
\underbrace{A}_{\ka{2\times 3}}+\underbrace{B}_{\kb{3\times 2}}
\qquad
\ka{2}\ne\kb{3}\ \Longrightarrow\ \kutusil{\text{tanımsız}}
$$
Satır sayıları farklı olduğundan karşılıklı hücre yoktur. $B^T$ ise $2\times 3$'tür; $A+B^T$ tanımlıdır.
:::

## Mühendislikte

::: muhendislik Süperpozisyon ve birleştirme
Doğrusal sonlu eleman analizinde her yük durumu ayrı çözülür, sonuçlar katsayılarla toplanır. Bu, matris toplama ve skaler çarpımın doğrudan uygulamasıdır. Global rijitlik matrisi $K$ de eleman matrislerinin uygun hücrelere **toplanmasıyla** kurulur. Yığma köprü modelinde zati yük, dolgu yükü ve trafik yükü ayrı vektörlerdir; deprem birleşiminde bunlar katsayılarla toplanır.
:::

::: ozet
- Toplama ve çıkarma yalnız **aynı boyuttaki** matrislerde, eleman eleman yapılır.
- $kA$: her eleman $k$ ile çarpılır, boyut değişmez.
- Toplama değişmeli ve birleşmelidir; skaler çarpım toplamaya dağılır.
- Yük birleşimi ($1.35\,G+1.5\,Q$) ve paralel yayların rijitliği bu işlemlerle hesaplanır.
:::

## Alıştırma

::: alistirma toplama
{"zorluk": 1, "boyut": 2}
:::

::: alistirma skaler
{"zorluk": 2, "boyut": 3}
:::
