---
baslik: Ters matris
bolum: matris
ozet: A⁻¹ ile geri dönmek; 2×2 formülü, Gauss–Jordan yöntemi ve esneklik matrisi.
sure: 35
---

## Neden?

Sayılarda $5x=10$ ise $x=5^{-1}\cdot 10=2$ olur. Matrislerde de $K\mathbf{u}=\mathbf{F}$ ise $\mathbf{u}=K^{-1}\mathbf{F}$ yazılır. $K^{-1}$'in yapıdaki adı **esneklik matrisidir** (flexibility matrix): $j$ düğümüne birim kuvvet uygulanınca $i$ düğümünün ne kadar yer değiştirdiğini söyler. Bu derste tersi bulmayı ve ne anlama geldiğini göreceksin.

## Ters matris nedir?

::: tanim Ters matris
Kare bir $A$ matrisi için $A\,A^{-1}=A^{-1}A=I$ eşitliğini sağlayan $A^{-1}$ matrisine **ters matris** (inverse) denir. Ters yalnızca $\det A\ne 0$ ise vardır. Böyle matrislere **düzenli** ya da **tersinir** (invertible) denir.
:::

$$
\underbrace{\begin{bmatrix}\ka{3}&\ka{5}\\1&2\end{bmatrix}}_{A}
\underbrace{\begin{bmatrix}\kb{2}&-5\\\kb{-1}&3\end{bmatrix}}_{A^{-1}}
=
\begin{bmatrix}\kutuc{1}&0\\0&1\end{bmatrix}
\qquad
\kc{1}=\ka{3}\cdot\kb{2}+\ka{5}\cdot(\kb{-1})
$$

Aşağıda $A$ ile $A^{-1}$'i çarp. Hangi hücreye dokunursan dokun, köşegende 1, dışında 0 çıktığını gör.

::: etkilesim carpim-gezgini
{"A": "3 5; 1 2", "B": "2 -5; -1 3", "baslik": "A · A⁻¹ = I"}
:::

## 2×2 için formül

Köşegeni **yer değiştir**, yan köşegenin **işaretini çevir**, determinanta böl:

$$
\begin{bmatrix}\ka{a}&\kb{b}\\\kb{c}&\ka{d}\end{bmatrix}^{-1}
=\frac{1}{\kc{ad-bc}}
\begin{bmatrix}\ka{d}&\kb{-b}\\\kb{-c}&\ka{a}\end{bmatrix}
$$

::: sekil 2×2 tersin üç hamlesi
<svg viewBox="0 0 360 150" width="100%" font-family="system-ui" font-size="15" fill="currentColor">
<g fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5">
<path d="M30 30 h-6 v80 h6 M110 30 h6 v80 h-6"/>
<path d="M230 30 h-6 v80 h6 M330 30 h6 v80 h-6"/>
</g>
<rect class="vurgu" rx="6" x="34" y="36" width="32" height="30" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<rect class="vurgu" rx="6" x="74" y="74" width="32" height="30" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<g text-anchor="middle">
<text x="50" y="57">a</text><text x="90" y="57" fill="var(--sema-b,#f59e0b)">b</text>
<text x="50" y="95" fill="var(--sema-b,#f59e0b)">c</text><text x="90" y="95">d</text>
<text x="252" y="57">d</text><text x="306" y="57" fill="var(--sema-b,#f59e0b)">−b</text>
<text x="252" y="95" fill="var(--sema-b,#f59e0b)">−c</text><text x="306" y="95">a</text>
<text x="190" y="76" fill="var(--sema-c,#10b981)">1 / det</text>
</g>
<path class="ok" pathLength="1" d="M50 34 C 70 0, 110 0, 90 72" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<polyline class="ok-uc" points="85,64 90,72 95,64" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<path class="ok" pathLength="1" d="M90 106 C 70 140, 30 140, 50 68" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<polyline class="ok-uc" points="45,76 50,68 55,76" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<path class="ok" pathLength="1" d="M124 70 L 160 70" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8"/>
<polyline class="ok-uc" points="152,64 160,70 152,76" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8"/>
<text x="60" y="146" text-anchor="middle" fill="var(--sema-a,#3b82f6)" font-size="12">köşegen yer değiştirir</text>
<text x="280" y="138" text-anchor="middle" fill="var(--sema-b,#f59e0b)" font-size="12">yan köşegen işaret değiştirir</text>
</svg>
:::

## Gauss–Jordan yöntemi

$3\times 3$ ve daha büyük matrislerde $A$'nın yanına $I$ yazılır: $[\,A\mid I\,]$. Satır işlemleriyle sol taraf $I$'ya çevrilir. Aynı işlemler sağ tarafa da uygulandığı için sağda $A^{-1}$ belirir:

$$
\big[\;\kutua{A}\;\big|\;\kutub{I}\;\big]
\;\xrightarrow{\ \text{satır işlemleri}\ }\;
\big[\;\kutub{I}\;\big|\;\kutuc{A^{-1}}\;\big]
$$

Kullanılan üç satır işlemi şunlardır: iki satırın yerini değiştirmek, bir satırı sıfırdan farklı bir sayıyla çarpmak, bir satıra başka bir satırın katını eklemek. Aşağıdaki çizimde her adımı tek tek ilerlet; hangi satırın hangi satırla birleştiğini oklar gösterir.

::: etkilesim gauss-adim
{"A": "2 1 0; 1 2 1; 0 1 2", "mod": "ters"}
:::

## Tersin kuralları

$$
\begin{aligned}
(A^{-1})^{-1} &= A\\
(AB)^{-1} &= \kutub{B^{-1}}\,\kutua{A^{-1}} && \text{devrikte olduğu gibi sıra ters döner}\\
(A^T)^{-1} &= (A^{-1})^T && \text{simetrik matrisin tersi de simetriktir}\\
(kA)^{-1} &= \tfrac1k\,A^{-1}\\
\det(A^{-1}) &= 1/\det A
\end{aligned}
$$

::: hata Elemanları tek tek ters çevirmek
$\begin{bmatrix}4&7\\2&6\end{bmatrix}^{-1}$ matrisi $\begin{bmatrix}\ksil{1/4}&\ksil{1/7}\\\ksil{1/2}&\ksil{1/6}\end{bmatrix}$ değildir. Bu kural yalnızca **köşegen** matrislerde doğru sonuç verir.
:::

::: hata Büyük sistemi tersle çözmek
$K\mathbf{u}=\mathbf{F}$'yi çözmek için $K^{-1}$'i bulup $\mathbf{F}$ ile çarpmak, doğrudan eliminasyondan yaklaşık üç kat daha pahalıdır ve yuvarlama hatasını büyütür. Sonlu eleman programları tersi **hesaplamaz**; sistemi doğrudan çözer. Ters, kavramı anlamak ve küçük el hesapları içindir.
:::

## Çözümlü örnekler

::: ornek 2×2 formülüyle ters
$A=\begin{bmatrix}4&7\\2&6\end{bmatrix}$ ise $A^{-1}$ nedir?
--- ipucu
Önce $\det A=4\cdot 6-7\cdot 2$ değerini bul.
--- cevap
$$
\det A=24-14=\kc{10}
\qquad
A^{-1}=\frac{1}{\kc{10}}\begin{bmatrix}\ka{6}&\kb{-7}\\\kb{-2}&\ka{4}\end{bmatrix}
=\begin{bmatrix}\tfrac35&-\tfrac{7}{10}\\-\tfrac15&\tfrac25\end{bmatrix}
$$
--- kod
mo.ters("4 7; 2 6")
--- kontrol
r.deger == sp.Matrix([[sp.Rational(3, 5), sp.Rational(-7, 10)], [sp.Rational(-1, 5), sp.Rational(2, 5)]])
:::

::: ornek Sağlama: A·A⁻¹ = I
Bulduğun tersi $A$ ile çarparak doğrula.
--- cevap
$$
\begin{bmatrix}4&7\\2&6\end{bmatrix}\begin{bmatrix}0.6&-0.7\\-0.2&0.4\end{bmatrix}
=\begin{bmatrix}2.4-1.4&-2.8+2.8\\1.2-1.2&-1.4+2.4\end{bmatrix}
=\begin{bmatrix}\kc{1}&0\\0&\kc{1}\end{bmatrix}
$$
--- kod
mo.carp("4 7; 2 6", mo.ters("4 7; 2 6"))
--- kontrol
r.deger == sp.eye(2)
:::

::: ornek Gauss–Jordan ile 3×3
$A=\begin{bmatrix}1&2&3\\0&1&4\\5&6&0\end{bmatrix}$ ise $A^{-1}$ nedir? Bu matrisin determinantı 1'dir.
--- ipucu
$[\,A\mid I\,]$ yaz. 3. satırdan 1. satırın 5 katını çıkararak başla.
--- cevap
$$
\left[\begin{array}{ccc|ccc}
1&2&3&1&0&0\\0&1&4&0&1&0\\5&6&0&0&0&1
\end{array}\right]
\xrightarrow{\ R_3-5R_1,\ R_3+4R_2,\ \dots\ }
\left[\begin{array}{ccc|ccc}
1&0&0&\kc{-24}&\kc{18}&\kc{5}\\0&1&0&\kc{20}&\kc{-15}&\kc{-4}\\0&0&1&\kc{-5}&\kc{4}&\kc{1}
\end{array}\right]
$$
--- kod
mo.ters("1 2 3; 0 1 4; 5 6 0", yontem="gauss")
--- kontrol
r.deger == sp.Matrix([[-24, 18, 5], [20, -15, -4], [-5, 4, 1]])
--- yorum
$\det A=1$ olduğu için bölme gerekmedi ve ters tamsayılardan oluştu.
:::

::: ornek Yay zincirinin esneklik matrisi
Sol ucu ankastre, üç birim yayla bağlı üç düğüm: $K=\begin{bmatrix}2&-1&0\\-1&2&-1\\0&-1&1\end{bmatrix}$ kN/m. Esneklik matrisi $K^{-1}$ nedir?
--- cevap
$$
K^{-1}=\begin{bmatrix}1&1&1\\1&\kutua{2}&2\\1&2&\kutub{3}\end{bmatrix}\ \text{m/kN}
$$
$(i,j)$ hücresi, $j$ düğümüne 1 kN uygulanınca $i$ düğümünün yer değiştirmesidir. Ankastre uca yakın düğüm daha az yer değiştirir ve sonuç simetriktir.
--- kod
mo.ters("2 -1 0; -1 2 -1; 0 -1 1")
--- kontrol
r.deger == sp.Matrix([[1, 1, 1], [1, 2, 2], [1, 2, 3]])
--- yorum
Bu tablonun her elemanı $\min(i,j)$ değeridir: $j$ düğümünü çeken kuvvet, ondan önceki yayların hepsini uzatır.
:::

::: ornek Uç yükünden yer değiştirmeler
Aynı sistemde yalnız uç düğüme $F_3=1$ kN uygulanıyor. $\mathbf{u}=K^{-1}\mathbf{F}$ nedir?
--- ipucu
$\mathbf{F}=\begin{bmatrix}0\\0\\1\end{bmatrix}$ ile çarpmak $K^{-1}$'in 3. sütununu seçer.
--- cevap
$$
\mathbf{u}=\begin{bmatrix}1&1&\kb{1}\\1&2&\kb{2}\\1&2&\kb{3}\end{bmatrix}\begin{bmatrix}0\\0\\\kb{1}\end{bmatrix}=\begin{bmatrix}\kc{1}\\\kc{2}\\\kc{3}\end{bmatrix}\ \text{m}
$$
Seri yaylarda her yay 1 kN taşır ve 1 m uzar; uzamalar toplanır.
--- kod
mo.carp(mo.ters("2 -1 0; -1 2 -1; 0 -1 1"), "0; 0; 1")
--- kontrol
r.deger == sp.Matrix([1, 2, 3])
:::

::: ornek Köşegen matrisin tersi
$D=\begin{bmatrix}2&0&0\\0&4&0\\0&0&5\end{bmatrix}$ ise $D^{-1}$ nedir?
--- cevap
$$
D^{-1}=\begin{bmatrix}\kc{\tfrac12}&0&0\\0&\kc{\tfrac14}&0\\0&0&\kc{\tfrac15}\end{bmatrix}
$$
Köşegen matriste her eleman ayrı ayrı ters çevrilir. Toplu kütle matrisi $M$ böyledir; tersi bu yüzden çok ucuzdur.
--- kod
mo.ters("2 0 0; 0 4 0; 0 0 5")
--- kontrol
r.deger == sp.diag(sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 5))
:::

::: ornek Çarpımın tersi
$A=\begin{bmatrix}1&1\\0&1\end{bmatrix}$ ve $B=\begin{bmatrix}2&0\\0&1\end{bmatrix}$ için $(AB)^{-1}$'i $B^{-1}A^{-1}$ olarak hesapla.
--- cevap
$$
\kutub{B^{-1}}\,\kutua{A^{-1}}=\begin{bmatrix}\tfrac12&0\\0&1\end{bmatrix}\begin{bmatrix}1&-1\\0&1\end{bmatrix}=\begin{bmatrix}\kc{\tfrac12}&\kc{-\tfrac12}\\0&\kc{1}\end{bmatrix}
$$
Doğrudan yoldan $AB=\begin{bmatrix}2&1\\0&1\end{bmatrix}$ bulunur ve formülle tersi aynı sonucu verir.
--- kod
mo.carp(mo.ters("2 0; 0 1"), mo.ters("1 1; 0 1"))
--- kontrol
r.deger == mo.ters(mo.carp("1 1; 0 1", "2 0; 0 1")).deger
:::

::: ornek Dönme matrisinin tersi devriğidir
$R=\begin{bmatrix}\tfrac35&-\tfrac45\\\tfrac45&\tfrac35\end{bmatrix}$ ise $R^{-1}$ nedir?
--- cevap
$$
\det R=\tfrac{9}{25}+\tfrac{16}{25}=1
\qquad
R^{-1}=\begin{bmatrix}\tfrac35&\kb{\tfrac45}\\\kb{-\tfrac45}&\tfrac35\end{bmatrix}=R^T
$$
--- kod
mo.ters("3/5 -4/5; 4/5 3/5")
--- kontrol
r.deger == sp.Matrix([[sp.Rational(3, 5), sp.Rational(4, 5)], [sp.Rational(-4, 5), sp.Rational(3, 5)]])
--- yorum
Dönme matrisleri **ortogonaldir**: $R^{-1}=R^T$. Eleman dönüşüm matrisinin tersini almak bu yüzden yalnızca devrik almaktır.
:::

::: ornek Tersi olmayan matris
$\begin{bmatrix}1&2\\2&4\end{bmatrix}$ matrisinin tersi var mı?
--- cevap
$$
\det=1\cdot 4-2\cdot 2=\kutusil{0}
$$
Determinant sıfır olduğu için formülde sıfıra bölme çıkar; **tersi yoktur**. İkinci satır birincinin iki katıdır, yani matris yalnızca bir doğrultu taşır.
:::

## Mühendislikte

::: muhendislik Esneklik ve rijitlik
Kuvvet yöntemi esneklik matrisiyle, deplasman yöntemi rijitlik matrisiyle çalışır. İkisi birbirinin tersidir. Yığma bir köprüde bir noktaya bilinen bir yük koyup yer değiştirmeyi ölçmek, esneklik matrisinin bir sütununu ölçmek demektir.

OMA'dan bulunan mod şekilleri ve frekanslar da esnekliği yaklaşık verir: $K^{-1}\approx\sum_i \boldsymbol\phi_i\boldsymbol\phi_i^T/\omega_i^2$. Bu ilişki hasar tespitinde kullanılır.
:::

::: ozet
- $AA^{-1}=I$; ters yalnızca $\det A\ne 0$ ise vardır.
- $2\times 2$: köşegeni değiştir, yan köşegenin işaretini çevir, $\det$ değerine böl.
- Büyük matrislerde $[\,A\mid I\,]\to[\,I\mid A^{-1}\,]$ Gauss–Jordan yöntemi kullanılır.
- $(AB)^{-1}=B^{-1}A^{-1}$; dönme matrisinde $R^{-1}=R^T$.
- $K^{-1}$ esneklik matrisidir, ama büyük sistemler tersle değil eliminasyonla çözülür.
:::

## Alıştırma

::: alistirma ters
{"zorluk": 1}
:::

::: alistirma ters
{"zorluk": 2}
:::

::: alistirma ters
{"zorluk": 3, "boyut": 3}
:::
