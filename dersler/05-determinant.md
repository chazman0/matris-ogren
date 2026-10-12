---
baslik: Determinant
bolum: matris
ozet: Bir kare matrisin tek sayılık özeti; alan ölçeği, kofaktör açılımı, satır indirgeme ve tekillik.
sure: 35
---

## Neden?

Bir sistemin çözülebilir olup olmadığını tek bir sayı söyler: **determinant**. Mesnetsiz bir yapının rijitlik matrisinde $\det K=0$ çıkar; yapı rijit cisim gibi kayıp gider ve $K\mathbf{u}=\mathbf{F}$ çözülemez. Doğal frekansları bulan denklem de bir determinanttır: $\det(K-\omega^2M)=0$. Bu derste determinantı hem hesaplamayı hem de anlamını görmeyi öğreneceksin.

## Determinant ne ölçer?

::: tanim Determinant
Kare bir $A$ matrisinin **determinantı** (determinant) $\det A$ ya da $|A|$ ile gösterilen tek bir sayıdır. Geometrik anlamı şudur: $A$ ile dönüştürülen birim karenin (3B'de birim küpün) **işaretli alanı** (hacmi). $\det A=0$ ise matris **tekildir** (singular): tersi yoktur.
:::

::: sekil Birim kare, alanı det A olan bir paralelkenara dönüşür
<svg viewBox="0 0 360 210" width="100%" font-family="system-ui" font-size="13" fill="currentColor">
<g stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1" fill="none">
<path d="M20 180 H340 M40 200 V20"/>
</g>
<rect x="40" y="130" width="50" height="50" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<text x="65" y="160" text-anchor="middle" fill="var(--sema-a,#3b82f6)">1</text>
<text x="65" y="198" text-anchor="middle">birim kare</text>
<path class="ok" pathLength="1" d="M100 120 C 130 90, 160 90, 190 110" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8"/>
<polyline class="ok-uc" points="181,104 190,110 180,113" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8"/>
<text x="145" y="84" text-anchor="middle">A = [2 1; 0 1]</text>
<g transform="translate(200,0)">
<path d="M0 180 H140 M0 200 V20" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1" fill="none"/>
<polygon class="vurgu" points="0,180 100,180 150,130 50,130" fill="var(--sema-c-bg,rgba(16,185,129,.16))" stroke="var(--sema-c,#10b981)" stroke-width="2"/>
<path d="M0 180 L100 180" stroke="var(--sema-a,#3b82f6)" stroke-width="3"/>
<path d="M0 180 L50 130" stroke="var(--sema-b,#f59e0b)" stroke-width="3"/>
<text x="70" y="198" text-anchor="middle" fill="var(--sema-a,#3b82f6)">1. sütun (2, 0)</text>
<text x="10" y="122" fill="var(--sema-b,#f59e0b)">2. sütun (1, 1)</text>
<text x="76" y="162" text-anchor="middle" fill="var(--sema-c,#10b981)" font-weight="700">alan = 2</text>
</g>
</svg>
:::

Kendin dene: matrisin elemanlarını değiştir, paralelkenarın alanının determinantla birlikte nasıl değiştiğini izle. Sütunlar aynı doğrultuya düşünce alan sıfıra iner.

::: etkilesim donusum-2b
{"A": "2 1; 0 1"}
:::

## 2×2 determinant

Ana köşegenin çarpımından yan köşegenin çarpımı çıkarılır:

$$
\det\begin{bmatrix}\ka{a}&\kb{b}\\\kb{c}&\ka{d}\end{bmatrix}=\ka{a\,d}-\kb{b\,c}
\qquad
\det\begin{bmatrix}\ka{3}&\kb{1}\\\kb{2}&\ka{4}\end{bmatrix}=\ka{12}-\kb{2}=\kutuc{10}
$$

## 3×3: kofaktör açılımı

Bir satır seçilir (genelde 1. satır). O satırın her elemanı, kendi satırı ve sütunu silinince kalan $2\times 2$ **minör** ile çarpılır. İşaretler satranç tahtası gibi $+,-,+$ diye gider:

$$
\det A
= \ka{a_{11}}\begin{vmatrix}\ksil{\cdot}&\ksil{\cdot}&\ksil{\cdot}\\\ksil{\cdot}&a_{22}&a_{23}\\\ksil{\cdot}&a_{32}&a_{33}\end{vmatrix}
\;-\; \ka{a_{12}}\begin{vmatrix}\ksil{\cdot}&\ksil{\cdot}&\ksil{\cdot}\\a_{21}&\ksil{\cdot}&a_{23}\\a_{31}&\ksil{\cdot}&a_{33}\end{vmatrix}
\;+\; \ka{a_{13}}\begin{vmatrix}\ksil{\cdot}&\ksil{\cdot}&\ksil{\cdot}\\a_{21}&a_{22}&\ksil{\cdot}\\a_{31}&a_{32}&\ksil{\cdot}\end{vmatrix}
$$

$$
\text{işaret deseni:}\quad
\begin{bmatrix}\kc{+}&\ksil{-}&\kc{+}\\\ksil{-}&\kc{+}&\ksil{-}\\\kc{+}&\ksil{-}&\kc{+}\end{bmatrix}
\qquad (-1)^{i+j}
$$

Aşağıdaki çizimde açılımı adım adım yürüt. Her adımda silinen satır ve sütun kırmızıyla çizilir, kalan minör kutuya alınır.

::: etkilesim kofaktor-acilim
{"A": "2 -1 0; -1 2 -1; 0 -1 2"}
:::

::: ipucu En çok sıfırı olan satırı seç
Açılımı herhangi bir satıra ya da sütuna göre yapabilirsin; sonuç aynıdır. Sıfır elemanların terimi hiç hesaplanmaz. Bu yüzden en çok sıfır içeren satırı seçmek işini kısaltır.
:::

## Kısayollar ve özellikler

$$
\begin{aligned}
\det(\text{üçgen matris}) &= \text{köşegen elemanların çarpımı}\\
\det(A^T) &= \det A\\
\det(AB) &= \det A\cdot\det B\\
\det(kA) &= k^{\,n}\det A && n\times n \text{ matris için}\\
\text{iki satır yer değiştirirse} &\Rightarrow \text{işaret değişir}\\
\text{bir satıra başka satırın katı eklenirse} &\Rightarrow \text{det değişmez}
\end{aligned}
$$

Son iki kural **satır indirgeme** ile determinant hesabının temelidir. Matris üçgen hale getirilir, köşegen çarpılır ve yapılan satır değişimi sayısı kadar işaret düzeltilir. $4\times 4$ ve daha büyük matrislerde bu yol kofaktörden çok daha kısadır.

::: hata $\det(A+B)=\det A+\det B$ sanmak
Determinant toplamaya dağılmaz. $A=B=I_2$ için $\det(A+B)=\det(2I)=4$ ama $\det A+\det B=2$'dir. Çarpımda ise kural çalışır: $\det(AB)=\det A\cdot\det B$.
:::

::: hata Kare olmayan matrisin determinantı
$2\times 3$ bir matrisin determinantı **tanımsızdır**. Determinant yalnızca kare matrisler içindir.
:::

## Çözümlü örnekler

::: ornek 2×2 determinant
$\det\begin{bmatrix}3&1\\2&4\end{bmatrix}$ nedir?
--- cevap
$$
\ka{3\cdot 4}-\kb{1\cdot 2}=12-2=\kutuc{10}
$$
--- kod
mo.determinant("3 1; 2 4")
--- kontrol
r.deger == 10
:::

::: ornek Satır değiştirince işaret
$\det\begin{bmatrix}2&4\\3&1\end{bmatrix}$ nedir? $\begin{bmatrix}3&1\\2&4\end{bmatrix}$ ile karşılaştır.
--- cevap
$$
2\cdot 1-4\cdot 3=2-12=\kutusil{-10}
$$
Satırları yer değiştirmiş matrisin determinantı $10$ idi: işaret döndü.
--- kod
mo.determinant("2 4; 3 1")
--- kontrol
r.deger == -10
:::

::: ornek Üç yaylı zincirin $K$ matrisi
$K=\begin{bmatrix}2&-1&0\\-1&2&-1\\0&-1&2\end{bmatrix}$ için $\det K$ nedir?
--- ipucu
1. satıra göre aç. $a_{13}=0$ olduğu için üçüncü terim düşer.
--- cevap
$$
\det K=\ka{2}\begin{vmatrix}2&-1\\-1&2\end{vmatrix}-\ka{(-1)}\begin{vmatrix}-1&-1\\0&2\end{vmatrix}+\ksil{0}\cdot(\dots)
=2\cdot 3+1\cdot(-2)=\kutuc{4}
$$
--- kod
mo.determinant("2 -1 0; -1 2 -1; 0 -1 2")
--- kontrol
r.deger == 4
:::

::: ornek Kofaktörle 3×3
$\det\begin{bmatrix}1&2&3\\0&1&4\\5&6&0\end{bmatrix}$ nedir?
--- cevap
$$
\begin{aligned}
&\ka{1}\cdot(1\cdot 0-4\cdot 6)\;-\;\ka{2}\cdot(0\cdot 0-4\cdot 5)\;+\;\ka{3}\cdot(0\cdot 6-1\cdot 5)\\
&=-24+40-15=\kutuc{1}
\end{aligned}
$$
--- kod
mo.determinant("1 2 3; 0 1 4; 5 6 0")
--- kontrol
r.deger == 1
--- yorum
Determinantı 1 olan bu matrisin tersi tamsayılardan oluşur. Bunu 6. derste göreceksin.
:::

::: ornek Üçgen matris: köşegeni çarp
$\det\begin{bmatrix}3&5&7\\0&2&9\\0&0&4\end{bmatrix}$ nedir?
--- cevap
$$
\ka{3}\cdot\ka{2}\cdot\ka{4}=\kutuc{24}
$$
Köşegenin altı sıfır olduğundan açılımda yalnız köşegen terimi kalır.
--- kod
mo.determinant("3 5 7; 0 2 9; 0 0 4")
--- kontrol
r.deger == 24
:::

::: ornek Mesnetsiz çubuk: tekil matris
Mesnetsiz bir çubuğun rijitlik matrisi $\tfrac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$ biçimindedir. $\tfrac{EA}{L}=1$ için determinant nedir?
--- cevap
$$
1\cdot 1-(-1)(-1)=\kutusil{0}
$$
Matris **tekildir**. Çubuk iki ucu birlikte kayarsa hiç kuvvet doğmaz; yer değiştirme tek türlü bulunamaz.
--- kod
mo.determinant("1 -1; -1 1")
--- kontrol
r.deger == 0
:::

::: ornek Mesnet ekleyince
Aynı yay zincirinin sağ ucu serbest, sol ucu mesnetli: $K=\begin{bmatrix}2&-1&0\\-1&2&-1\\0&-1&1\end{bmatrix}$. $\det K$ nedir?
--- cevap
$$
\ka{2}\,(2\cdot 1-1)-\ka{(-1)}\,\big((-1)\cdot 1-0\big)+0=2-1=\kutuc{1}
$$
$\det K\ne 0$: mesnet rijit cisim hareketini engelledi, sistem çözülebilir.
--- kod
mo.determinant("2 -1 0; -1 2 -1; 0 -1 1")
--- kontrol
r.deger == 1
:::

::: ornek 4×4: satır indirgeme
$\det\begin{bmatrix}2&1&0&0\\1&2&1&0\\0&1&2&1\\0&0&1&2\end{bmatrix}$ nedir?
--- ipucu
Kofaktör 24 terim üretir. Bunun yerine satır işlemleriyle üst üçgen yap; satırın katını eklemek determinantı değiştirmez.
--- cevap
$$
\xrightarrow{\ R_2-\tfrac12R_1,\ R_3-\tfrac23R_2,\ R_4-\tfrac34R_3\ }
\begin{bmatrix}\ka{2}&1&0&0\\0&\ka{\tfrac32}&1&0\\0&0&\ka{\tfrac43}&1\\0&0&0&\ka{\tfrac54}\end{bmatrix}
\qquad
\det=2\cdot\tfrac32\cdot\tfrac43\cdot\tfrac54=\kutuc{5}
$$
--- kod
mo.determinant("2 1 0 0; 1 2 1 0; 0 1 2 1; 0 0 1 2", yontem="eliminasyon")
--- kontrol
r.deger == 5
:::

::: ornek Skalerle çarpılan matris
$\det\big(2\begin{bmatrix}1&2\\3&4\end{bmatrix}\big)$ nedir?
--- ipucu
$\det(kA)=k^n\det A$ ve $n=2$.
--- cevap
$$
\det A=4-6=-2
\qquad
\det(2A)=\kb{2^2}\cdot(-2)=\kutuc{-8}
$$
Doğrudan: $\det\begin{bmatrix}2&4\\6&8\end{bmatrix}=16-24=-8$.
--- kod
mo.determinant(mo.skaler(2, "1 2; 3 4"))
--- kontrol
r.deger == -8
:::

::: ornek Hangi $k$ için tekil?
$\begin{bmatrix}k&2\\2&k\end{bmatrix}$ matrisi hangi $k$ değerlerinde tekildir?
--- cevap
$$
\det=k^2-4=0\quad\Longrightarrow\quad k=\kutusil{2}\ \text{ya da}\ k=\kutusil{-2}
$$
Bu soru, 8. dersteki özdeğer probleminin küçük bir provasıdır: $\det(A-\lambda I)=0$.
:::

## Mühendislikte

::: muhendislik Determinant ve mekanizma
Sonlu eleman programları sistem matrisinin tekil olup olmadığını çözüm sırasında yakalar. "Singular stiffness matrix" uyarısı, modelde eksik mesnet ya da bağlanmamış bir düğüm olduğunu söyler. Yığma köprü modelinde doğal frekansları veren karakteristik denklem $\det(K-\omega^2M)=0$'dır. OMA ile ölçtüğün frekanslar, model doğruysa bu denklemin kökleriyle örtüşmelidir.
:::

::: ozet
- $\det A$, birim karenin $A$ ile dönüşünce aldığı işaretli alandır.
- $2\times 2$: $ad-bc$; $3\times 3$: kofaktör açılımı, işaretler $+,-,+$.
- Üçgen matriste determinant köşegenin çarpımıdır; büyük matrislerde satır indirgeme kullan.
- $\det(AB)=\det A\det B$, $\det(kA)=k^n\det A$, ama $\det(A+B)\ne\det A+\det B$.
- $\det K=0$ ise yapı mesnetsizdir ya da mekanizmadır.
:::

## Alıştırma

::: alistirma determinant
{"zorluk": 1}
:::

::: alistirma determinant
{"zorluk": 2}
:::

::: alistirma determinant
{"zorluk": 3, "boyut": 3}
:::
