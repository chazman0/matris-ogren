---
baslik: Doğrusal denklem sistemleri
bolum: matris
ozet: Ax = b sistemini Gauss eliminasyonu, Cramer kuralı ve ters matrisle çözmek; tek, sonsuz ve sıfır çözüm.
sure: 40
---

## Neden?

Sonlu eleman yönteminin bütün işi sonunda tek bir satıra iner: $K\mathbf{u}=\mathbf{F}$. Rijitlik matrisi ve yük vektörü kurulduktan sonra geriye bilinmeyen yer değiştirmeleri bulmak kalır. Bir köprü modelinde bu, binlerce denklemi aynı anda çözmek demektir. Bu derste bunun elle nasıl yapıldığını, bilgisayarın da aynı adımları nasıl izlediğini göreceksin.

## Sistemin matris yazımı

::: tanim Doğrusal sistem
$n$ bilinmeyenli $m$ denklem $A\mathbf{x}=\mathbf{b}$ biçiminde yazılır. Katsayılar $A$ matrisinde, bilinmeyenler $\mathbf{x}$ vektöründe, sağ taraf $\mathbf{b}$ vektöründe toplanır. Kare sistemde $\det A\ne 0$ ise **tek çözüm** vardır.
:::

$$
\begin{aligned}
\ka{2}x+\ka{1}y&=\kb{5}\\
\ka{1}x+\ka{3}y&=\kb{10}
\end{aligned}
\quad\Longleftrightarrow\quad
\underbrace{\begin{bmatrix}\ka{2}&\ka{1}\\\ka{1}&\ka{3}\end{bmatrix}}_{A}
\underbrace{\begin{bmatrix}x\\y\end{bmatrix}}_{\mathbf{x}}
=
\underbrace{\begin{bmatrix}\kb{5}\\\kb{10}\end{bmatrix}}_{\mathbf{b}}
$$

İki bilinmeyenli her denklem düzlemde bir doğrudur. Çözüm, doğruların kesiştiği noktadır. Üç durum olabilir:

::: sekil Tek çözüm, çözüm yok, sonsuz çözüm
<svg viewBox="0 0 390 160" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<g stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1" fill="none">
<path d="M10 120 H120 M20 130 V20"/>
<path d="M140 120 H250 M150 130 V20"/>
<path d="M270 120 H380 M280 130 V20"/>
</g>
<g fill="none" stroke-width="2.2">
<path d="M25 30 L110 115" stroke="var(--sema-a,#3b82f6)"/>
<path d="M20 95 L115 45" stroke="var(--sema-b,#f59e0b)"/>
<path d="M150 100 L245 40" stroke="var(--sema-a,#3b82f6)"/>
<path d="M155 120 L245 63" stroke="var(--sema-b,#f59e0b)"/>
<path d="M280 110 L375 35" stroke="var(--sema-a,#3b82f6)" stroke-width="5" opacity=".45"/>
<path d="M280 110 L375 35" stroke="var(--sema-b,#f59e0b)" stroke-dasharray="6 5"/>
</g>
<circle class="vurgu" cx="72" cy="71" r="6" fill="var(--sema-c,#10b981)"/>
<g text-anchor="middle">
<text x="65" y="150">tek çözüm</text>
<text x="195" y="150">çözüm yok</text>
<text x="325" y="150">sonsuz çözüm</text>
<text x="65" y="14" fill="var(--sema-c,#10b981)">det A ≠ 0</text>
<text x="195" y="14">paralel, det A = 0</text>
<text x="325" y="14">çakışık, det A = 0</text>
</g>
</svg>
:::

Aşağıdaki çizimde $A$ matrisi düzlemi büker. $A\mathbf{x}=\mathbf{b}$ sorusu şudur: hangi $\mathbf{x}$ vektörü bükülünce tam olarak $\mathbf{b}$ olur?

::: etkilesim donusum-2b
{"A": "2 1; 1 3"}
:::

## Gauss eliminasyonu

Yöntem iki aşamalıdır. **İleri eliminasyonda** genişletilmiş matris $[\,A\mid\mathbf{b}\,]$ satır işlemleriyle üst üçgen yapılır. **Geri yerine koymada** son denklemden başlanır ve bilinmeyenler yukarı doğru bulunur.

$$
\left[\begin{array}{cc|c}\kutua{2}&1&5\\\kb{1}&3&10\end{array}\right]
\xrightarrow{\ R_2-\frac{\kb{1}}{\kutua{2}}R_1\ }
\left[\begin{array}{cc|c}\kutua{2}&1&5\\\kc{0}&\kutua{\tfrac52}&\tfrac{15}{2}\end{array}\right]
\quad\Rightarrow\quad
\begin{aligned}
y&=\tfrac{15/2}{5/2}=\kc{3}\\
x&=\tfrac{5-1\cdot 3}{2}=\kc{1}
\end{aligned}
$$

Kutulu sayılara **pivot** denir. Her adımda pivotun altındaki sayılar, pivot satırının uygun katı çıkarılarak sıfırlanır. Aşağıda 3×3 bir sistemi adım adım ilerlet; her adımda hangi satırın hangi katla çıkarıldığını oklar gösterir.

::: etkilesim gauss-adim
{"A": "2 1 -1; -3 -1 2; -2 1 2", "b": "8; -11; -3", "mod": "coz"}
:::

::: ipucu Çarpanı bulmak
Çarpan her zaman $\dfrac{\text{sıfırlanacak sayı}}{\text{pivot}}$ olur. Yukarıda $\tfrac{1}{2}$ çarpanı, 2. satırdaki 1'i sıfırlamak için seçildi.
:::

## Cramer kuralı

Küçük sistemlerde her bilinmeyen iki determinantın oranıdır. $x_i$'yi bulmak için $A$'nın $i$. sütunu $\mathbf{b}$ ile değiştirilir:

$$
x=\frac{\begin{vmatrix}\kb{5}&1\\\kb{10}&3\end{vmatrix}}{\begin{vmatrix}2&1\\1&3\end{vmatrix}}=\frac{15-10}{\kc{5}}=1
\qquad
y=\frac{\begin{vmatrix}2&\kb{5}\\1&\kb{10}\end{vmatrix}}{\kc{5}}=\frac{20-5}{5}=3
$$

## Ters matrisle

$\det A\ne 0$ ise $\mathbf{x}=A^{-1}\mathbf{b}$ yazılabilir. Kavram olarak en temiz yol budur, ama hesap olarak en pahalısıdır.

::: hata Matrise bölmek
$\mathbf{x}=\mathbf{b}/A$ diye bir işlem **yoktur**. Matrislerde bölme tanımlı değildir; yerine $A^{-1}$ ile soldan çarpılır ya da sistem eliminasyonla çözülür.
:::

::: hata Sıfır pivot
Pivot yerine 0 gelirse o satırla bölme yapılamaz. Bu durumda alttaki satırlardan biriyle **yer değiştirilir**. Bilgisayar programları da en büyük mutlak değerli sayıyı pivot seçer; buna kısmi pivotlama denir.
:::

## Çözümlü örnekler

::: ornek İki bilinmeyen, Gauss
$2x+y=5$ ve $x+3y=10$ sistemini çöz.
--- ipucu
2. satırdan 1. satırın yarısını çıkar.
--- cevap
$$
\left[\begin{array}{cc|c}2&1&5\\0&\tfrac52&\tfrac{15}{2}\end{array}\right]
\Rightarrow y=\kc{3},\quad x=\kc{1}
$$
Sağlama: $2+3=5$ ve $1+9=10$.
--- kod
mo.coz("2 1; 1 3", "5; 10")
--- kontrol
r.deger == sp.Matrix([1, 3])
:::

::: ornek Cramer kuralıyla
$3x+2y=8$ ve $x+4y=6$ sistemini Cramer kuralıyla çöz.
--- cevap
$$
\det A=12-2=\kc{10},\qquad
x=\frac{\begin{vmatrix}\kb{8}&2\\\kb{6}&4\end{vmatrix}}{10}=\frac{20}{10}=2,\qquad
y=\frac{\begin{vmatrix}3&\kb{8}\\1&\kb{6}\end{vmatrix}}{10}=\frac{10}{10}=1
$$
--- kod
mo.coz("3 2; 1 4", "8; 6", yontem="cramer")
--- kontrol
r.deger == sp.Matrix([2, 1])
:::

::: ornek Üç bilinmeyen, Gauss
$2x+y-z=8$, $-3x-y+2z=-11$, $-2x+y+2z=-3$ sistemini çöz.
--- ipucu
Önce 1. sütunda pivotun altını sıfırla: $R_2+\tfrac32R_1$ ve $R_3+R_1$.
--- cevap
$$
\left[\begin{array}{ccc|c}\kutua{2}&1&-1&8\\0&\kutua{\tfrac12}&\tfrac12&1\\0&0&\kutua{-1}&1\end{array}\right]
\Rightarrow z=\kc{-1},\ y=\kc{3},\ x=\kc{2}
$$
--- kod
mo.coz("2 1 -1; -3 -1 2; -2 1 2", "8; -11; -3")
--- kontrol
r.deger == sp.Matrix([2, 3, -1])
:::

::: ornek Üst üçgen sistem, yalnız geri yerine koyma
$\begin{bmatrix}2&1&1\\0&3&1\\0&0&4\end{bmatrix}\mathbf{x}=\begin{bmatrix}7\\11\\8\end{bmatrix}$ sistemini çöz.
--- cevap
Sondan başla:
$$
z=\tfrac{8}{4}=\kc{2},\qquad y=\tfrac{11-\kc{2}}{3}=\kc{3},\qquad x=\tfrac{7-\kc{3}-\kc{2}}{2}=\kc{1}
$$
--- kod
mo.coz("2 1 1; 0 3 1; 0 0 4", "7; 11; 8")
--- kontrol
r.deger == sp.Matrix([1, 3, 2])
--- yorum
Eliminasyonun amacı tam olarak bu biçime ulaşmaktır. Üçgen sistem tek tek, yukarı doğru çözülür.
:::

::: ornek Ters matrisle çözüm
$4x+7y=1$ ve $2x+6y=2$ sistemini $\mathbf{x}=A^{-1}\mathbf{b}$ ile çöz.
--- ipucu
Önceki derste $A^{-1}=\tfrac{1}{10}\begin{bmatrix}6&-7\\-2&4\end{bmatrix}$ bulmuştuk.
--- cevap
$$
\mathbf{x}=\frac{1}{10}\begin{bmatrix}6&-7\\-2&4\end{bmatrix}\begin{bmatrix}1\\2\end{bmatrix}=\frac{1}{10}\begin{bmatrix}-8\\6\end{bmatrix}=\begin{bmatrix}\kc{-\tfrac45}\\\kc{\tfrac35}\end{bmatrix}
$$
--- kod
mo.coz("4 7; 2 6", "1; 2", yontem="ters")
--- kontrol
r.deger == sp.Matrix([sp.Rational(-4, 5), sp.Rational(3, 5)])
:::

::: ornek Yay zinciri: K u = F
Sol ucu ankastre üç birim yaylı zincirde her düğüme 1 kN yük var. $K=\begin{bmatrix}2&-1&0\\-1&2&-1\\0&-1&1\end{bmatrix}$ kN/m ise yer değiştirmeler nedir?
--- cevap
$$
\begin{bmatrix}2&-1&0\\-1&2&-1\\0&-1&1\end{bmatrix}\begin{bmatrix}u_1\\u_2\\u_3\end{bmatrix}=\begin{bmatrix}1\\1\\1\end{bmatrix}
\Rightarrow
\mathbf{u}=\begin{bmatrix}\kc{3}\\\kc{5}\\\kc{6}\end{bmatrix}\ \text{m}
$$
Birinci yay 3 kN taşır ve 3 m uzar. İkinci yay 2 kN, üçüncüsü 1 kN taşır; uzamalar $3+2+1$ diye birikir.
--- kod
mo.coz("2 -1 0; -1 2 -1; 0 -1 1", "1; 1; 1", bilinmeyen="u")
--- kontrol
r.deger == sp.Matrix([3, 5, 6])
:::

::: ornek İki çubuklu sistem, mesnet uygulanmış
Sol ucu mesnetli, seri iki çubuk var; her birinin rijitliği $k=100$ kN/m. Uç düğüme 10 kN çekme uygulanıyor. Mesnet satırı silinmiş sistem $\begin{bmatrix}200&-100\\-100&100\end{bmatrix}\mathbf{u}=\begin{bmatrix}0\\10\end{bmatrix}$ olur. Çöz.
--- cevap
$$
\left[\begin{array}{cc|c}\kutua{200}&-100&0\\0&\kutua{50}&10\end{array}\right]
\Rightarrow u_3=\tfrac{10}{50}=\kc{0.2}\ \text{m},\quad u_2=\tfrac{100\cdot 0.2}{200}=\kc{0.1}\ \text{m}
$$
--- kod
mo.coz("200 -100; -100 100", "0; 10", bilinmeyen="u")
--- kontrol
r.deger == sp.Matrix([sp.Rational(1, 10), sp.Rational(1, 5)])
--- yorum
Mesnet satırı silinmeseydi $K$ tekil olurdu ve sistem çözülemezdi. Sınır koşulları sonlu eleman bölümünde ayrıntılı işlenecek.
:::

::: ornek Sonsuz çözüm
$x+2y=3$ ve $2x+4y=6$ sistemini incele.
--- cevap
İkinci denklem birincinin tam iki katıdır, yani aslında **tek denklem** vardır:
$$
\left[\begin{array}{cc|c}1&2&3\\2&4&6\end{array}\right]\xrightarrow{R_2-2R_1}\left[\begin{array}{cc|c}1&2&3\\\kutusil{0}&\kutusil{0}&\kutusil{0}\end{array}\right]
$$
$y=t$ serbest seçilir ve $x=3-2t$ olur. Doğrular çakışıktır.
:::

::: ornek Çözüm yok
$x+2y=3$ ve $2x+4y=7$ sistemini incele.
--- cevap
$$
\left[\begin{array}{cc|c}1&2&3\\2&4&7\end{array}\right]\xrightarrow{R_2-2R_1}\left[\begin{array}{cc|c}1&2&3\\0&0&\kutusil{1}\end{array}\right]
$$
Son satır $0=1$ der; bu çelişkidir. Doğrular paraleldir ve hiç kesişmez. Yapıda bunun karşılığı, mesnetsiz bir sistemin dengelenemeyen yük almasıdır.
:::

## Mühendislikte

::: muhendislik Büyük sistemler nasıl çözülür?
Bir yığma köprünün katı eleman modelinde $K$ yüz binlerce satırlık olabilir. Neyse ki $K$ simetrik, pozitif tanımlı ve seyrektir. Programlar bunu kullanarak Cholesky ayrıştırması yapar: $K=LL^T$.

Model güncellemede, yani OMA'dan ölçülen frekanslara uydurmada, malzeme parametreleri her değiştiğinde sistem yeniden kurulup çözülür. Bu yüzden çözümün hızlı ve kararlı olması önemlidir.
:::

::: ozet
- $A\mathbf{x}=\mathbf{b}$: katsayılar $A$'da, bilinmeyenler $\mathbf{x}$'te, sağ taraf $\mathbf{b}$'de.
- Gauss: $[\,A\mid\mathbf{b}\,]$ üst üçgen yapılır, sonra geri yerine koyulur.
- Cramer: $x_i=\det A_i/\det A$; yalnız küçük sistemler için.
- $\det A\ne 0$ ise tek çözüm, $\det A=0$ ise ya sonsuz çözüm ya da hiç çözüm yoktur.
- Sonlu elemanların çekirdeği $K\mathbf{u}=\mathbf{F}$ sistemidir.
:::

## Alıştırma

::: alistirma coz
{"zorluk": 1}
:::

::: alistirma coz
{"zorluk": 2}
:::

::: alistirma coz
{"zorluk": 3, "boyut": 3}
:::
