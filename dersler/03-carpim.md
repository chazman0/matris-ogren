---
baslik: Matris çarpımı
bolum: matris
ozet: Satır × sütun kuralı, boyut uyumu, sıranın önemi ve matris × vektör.
sure: 35
---

## Neden?

Sonlu eleman yönteminin ana denklemi $K\mathbf{u}=\mathbf{F}$ bir **matris çarpımıdır**. Rijitlik matrisi $K$ ile yer değiştirme vektörü $\mathbf{u}$ çarpılınca düğüm kuvvetleri çıkar. Koordinat dönüşümü $T^T k\,T$ de üç matrisin çarpımıdır. Çarpımı rahat okuyamayan biri sonlu eleman matrislerini de okuyamaz; bu ders o yüzden uzun ve bol örneklidir.

## Satır × sütun kuralı

::: tanim Matris çarpımı
$A$ $m\times n$, $B$ $n\times p$ ise $C=AB$ $m\times p$'dir. Sonucun $(i,j)$ elemanı, $A$'nın $\ka{i.}$ **satırı** ile $B$'nin $\kb{j.}$ **sütununun** karşılıklı elemanlarının çarpımlarının toplamıdır:
$c_{ij}=\sum_{k=1}^{n} a_{ik}\,b_{kj}$.
:::

Bir hücreyi hesaplamak için $A$'da satır boyunca sağa, $B$'de sütun boyunca aşağı yürürsün. Karşılaşan çiftleri çarpar, sonuçları toplarsın:

$$
\begin{bmatrix} \ka{1} & \ka{2} \\ 3 & 4 \end{bmatrix}
\begin{bmatrix} \kb{5} & 6 \\ \kb{7} & 8 \end{bmatrix}
=
\begin{bmatrix} \kutuc{19} & 22 \\ 43 & 50 \end{bmatrix}
\qquad
\kc{19} = \ka{1}\cdot\kb{5} + \ka{2}\cdot\kb{7}
$$

::: sekil Satır ile sütun buluşur, çiftler çarpılıp toplanır
<svg viewBox="0 0 360 200" width="100%" font-family="system-ui" font-size="13" fill="currentColor">
<rect x="22" y="70" width="96" height="36" rx="6" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<rect x="166" y="30" width="40" height="116" rx="6" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<rect class="vurgu" rx="6" x="262" y="70" width="40" height="36" fill="var(--sema-c-bg,rgba(16,185,129,.16))" stroke="var(--sema-c,#10b981)" stroke-width="2"/>
<g fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5">
<path d="M20 64 h-6 v80 h6 M120 64 h6 v80 h-6"/>
<path d="M164 26 h-6 v124 h6 M246 26 h6 v124 h-6"/>
<path d="M260 64 h-6 v80 h6 M344 64 h6 v80 h-6"/>
</g>
<g text-anchor="middle">
<text x="38" y="93">2</text><text x="70" y="93">1</text><text x="102" y="93">3</text>
<text x="38" y="129">0</text><text x="70" y="129">4</text><text x="102" y="129">1</text>
<text x="186" y="52">1</text><text x="186" y="93">5</text><text x="186" y="134">2</text>
<text x="228" y="52">0</text><text x="228" y="93">1</text><text x="228" y="134">2</text>
<text x="282" y="93" font-weight="700">13</text><text x="326" y="93">7</text>
<text x="282" y="129">22</text><text x="326" y="129">6</text>
<text x="70" y="182" fill="var(--sema-a,#3b82f6)">A: 2×3</text>
<text x="206" y="182" fill="var(--sema-b,#f59e0b)">B: 3×2</text>
<text x="302" y="182" fill="var(--sema-c,#10b981)">C: 2×2</text>
</g>
<path class="ok" pathLength="1" d="M38 68 C 60 20, 150 30, 180 46" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<path class="ok" pathLength="1" d="M70 68 C 100 50, 150 80, 178 88" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<path class="ok" pathLength="1" d="M102 108 C 130 140, 160 140, 178 132" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="1.8"/>
<path class="ok" pathLength="1" d="M208 88 C 230 70, 246 80, 260 86" fill="none" stroke="var(--sema-c,#10b981)" stroke-width="2.2"/>
<polyline class="ok-uc" points="252,80 260,86 252,92" fill="none" stroke="var(--sema-c,#10b981)" stroke-width="2.2"/>
<text x="180" y="16" text-anchor="middle" fill="var(--sema-c,#10b981)">2·1 + 1·5 + 3·2 = 13</text>
</svg>
:::

Şimdi kendin keşfet. Sonuç matrisinde bir hücreye dokun; hangi satırın ve hangi sütunun kullanıldığını, terim çiftlerini ve toplamı gör. Girdileri değiştirip yeniden dene.

::: etkilesim carpim-gezgini
{"A": "2 1 3; 0 4 1", "B": "1 0; 5 1; 2 2", "baslik": "Sonuç hücresine dokun"}
:::

## Boyut uyumu

Çarpımın tanımlı olması için **iç boyutlar** eşit olmalıdır. Sonucun boyutu **dış boyutlardan** gelir:

$$
\underbrace{A}_{m\times \kutua{n}}\;\underbrace{B}_{\kutub{n}\times p}
\;=\;
\underbrace{C}_{\kc{m}\times \kc{p}}
\qquad
\begin{aligned}
2\times\kutua{3}\ \cdot\ \kutub{3}\times 2 &\to \kc{2\times 2}\\
3\times\kutua{1}\ \cdot\ \kutub{1}\times 3 &\to \kc{3\times 3}\\
2\times\kutua{3}\ \cdot\ \kutusil{2}\times 3 &\to \ksil{\text{tanımsız}}
\end{aligned}
$$

::: ipucu Boyut zinciri
Boyutları yan yana yaz: $(2\times 3)(3\times 2)$. Ortadaki iki sayı birbirine "değmeli". Değiyorsa siler, dıştakileri alırsın.
:::

## Sıra önemlidir

Sayılarda $3\cdot 5=5\cdot 3$'tür ama matrislerde genellikle $AB\ne BA$'dır. $AB$ tanımlı olsa bile $BA$ tanımsız olabilir. İkisi de tanımlıysa bile sonuçlar farklı çıkabilir.

$$
\begin{bmatrix}1&2\\3&4\end{bmatrix}\begin{bmatrix}5&6\\7&8\end{bmatrix}=\begin{bmatrix}\kc{19}&\kc{22}\\\kc{43}&\kc{50}\end{bmatrix}
\qquad
\begin{bmatrix}5&6\\7&8\end{bmatrix}\begin{bmatrix}1&2\\3&4\end{bmatrix}=\begin{bmatrix}\ksil{23}&\ksil{34}\\\ksil{31}&\ksil{46}\end{bmatrix}
$$

::: hata Eleman eleman çarpmak
$AB$ hesaplanırken karşılıklı hücreler **çarpılmaz**. $\begin{bmatrix}1&2\\3&4\end{bmatrix}\begin{bmatrix}5&6\\7&8\end{bmatrix}$ işleminin sonucu $\begin{bmatrix}\ksil{5}&\ksil{12}\\\ksil{21}&\ksil{32}\end{bmatrix}$ değildir. Doğru kural her zaman **satır × sütun**dur.
:::

::: hata $AB=0$ ise $A=0$ ya da $B=0$ sanmak
Sayılarda geçerli olan bu kural matrislerde geçmez:
$\begin{bmatrix}1&1\\1&1\end{bmatrix}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}=\begin{bmatrix}0&0\\0&0\end{bmatrix}$. İki matris de sıfır değildir.
:::

## Çarpımın özellikleri

$$
\begin{aligned}
(AB)C &= A(BC) && \text{birleşme: parantez yeri serbest}\\
A(B+C) &= AB+AC && \text{dağılma}\\
AI &= IA = A && \text{birim matris}\\
k(AB) &= (kA)B = A(kB) && \text{skaler serbestçe dolaşır}\\
AB &\ne BA && \text{genelde değişme yok}
\end{aligned}
$$

## Matris × vektör

Bir matrisi bir sütun vektörüyle çarpmak, matrisin **sütunlarının ağırlıklı toplamıdır**. Vektörün elemanları ağırlıklardır:

$$
\begin{bmatrix}\ka{2}&\kb{-1}\\\ka{-1}&\kb{2}\end{bmatrix}
\begin{bmatrix}\ka{3}\\\kb{1}\end{bmatrix}
=
\ka{3}\begin{bmatrix}\ka{2}\\\ka{-1}\end{bmatrix}
+
\kb{1}\begin{bmatrix}\kb{-1}\\\kb{2}\end{bmatrix}
=
\begin{bmatrix}\kc{5}\\\kc{-1}\end{bmatrix}
$$

Bu bakış açısı sonlu elemanda çok işe yarar. $K\mathbf{u}$, "her serbestliğin birim yer değiştirme kuvvetlerinin, gerçek yer değiştirmelerle ölçeklenip toplanmasıdır".

Aşağıda üç serbestlikli bir yay zincirinin $K$ matrisi var. Yer değiştirme vektörünü değiştir, her kuvvet hücresine dokunup hangi satırın kullanıldığını izle.

::: etkilesim carpim-gezgini
{"A": "2 -1 0; -1 2 -1; 0 -1 1", "B": "1; 2; 3", "baslik": "K · u = F"}
:::

## Çözümlü örnekler

::: ornek 2×2 çarpım
$A=\begin{bmatrix}1&2\\3&4\end{bmatrix}$ ve $B=\begin{bmatrix}5&6\\7&8\end{bmatrix}$ için $AB$ nedir?
--- ipucu
Dört hücrenin her biri için bir satır, bir sütun seç: $c_{ij}$ için $A$'nın $i.$ satırı, $B$'nin $j.$ sütunu.
--- cevap
$$
\begin{aligned}
c_{11} &= \ka{1}\cdot\kb{5}+\ka{2}\cdot\kb{7}=\kc{19} &
c_{12} &= \ka{1}\cdot\kb{6}+\ka{2}\cdot\kb{8}=\kc{22}\\
c_{21} &= \ka{3}\cdot\kb{5}+\ka{4}\cdot\kb{7}=\kc{43} &
c_{22} &= \ka{3}\cdot\kb{6}+\ka{4}\cdot\kb{8}=\kc{50}
\end{aligned}
\qquad
AB=\begin{bmatrix}\kutuc{19}&\kutuc{22}\\\kutuc{43}&\kutuc{50}\end{bmatrix}
$$
--- kod
mo.carp("1 2; 3 4", "5 6; 7 8")
--- kontrol
r.deger == sp.Matrix([[19, 22], [43, 50]])
:::

::: ornek Sırayı değiştir: $BA$
Aynı $A$ ve $B$ için $BA$ nedir? $AB$ ile karşılaştır.
--- ipucu
Şimdi satırlar $B$'den, sütunlar $A$'dan gelir.
--- cevap
$$
BA=\begin{bmatrix}\ka{5}&\ka{6}\\7&8\end{bmatrix}\begin{bmatrix}\kb{1}&2\\\kb{3}&4\end{bmatrix}
=
\begin{bmatrix}\kutusil{23}&34\\31&46\end{bmatrix}
\qquad
\kc{23}=\ka{5}\cdot\kb{1}+\ka{6}\cdot\kb{3}
$$
$BA\ne AB$: sıra önemlidir.
--- kod
mo.carp("5 6; 7 8", "1 2; 3 4")
--- kontrol
r.deger == sp.Matrix([[23, 34], [31, 46]])
:::

::: ornek Dikdörtgen matrisler: $(2\times 3)(3\times 2)$
$A=\begin{bmatrix}1&0&2\\-1&3&1\end{bmatrix}$, $B=\begin{bmatrix}3&1\\2&1\\1&0\end{bmatrix}$ için $AB$ nedir?
--- ipucu
İç boyutlar $3=3$: tanımlı. Sonuç $2\times 2$. Her hücrede üç çarpım toplanır.
--- cevap
$$
\begin{aligned}
c_{11} &= \ka{1}\cdot\kb{3}+\ka{0}\cdot\kb{2}+\ka{2}\cdot\kb{1} = \kc{5}\\
c_{12} &= 1\cdot 1+0\cdot 1+2\cdot 0 = \kc{1}\\
c_{21} &= (-1)\cdot 3+3\cdot 2+1\cdot 1 = \kc{4}\\
c_{22} &= (-1)\cdot 1+3\cdot 1+1\cdot 0 = \kc{2}
\end{aligned}
\qquad
AB=\begin{bmatrix}\kutuc{5}&\kutuc{1}\\\kutuc{4}&\kutuc{2}\end{bmatrix}
$$
--- kod
mo.carp("1 0 2; -1 3 1", "3 1; 2 1; 1 0")
--- kontrol
r.deger == sp.Matrix([[5, 1], [4, 2]])
--- yorum
$BA$ da tanımlıdır ama $3\times 3$ çıkar. Aynı iki matris, sıraya göre farklı boyutta sonuç verir.
:::

::: ornek Satır × sütun: tek sayı
$\begin{bmatrix}1&2&3\end{bmatrix}\begin{bmatrix}4\\5\\6\end{bmatrix}$ nedir?
--- ipucu
$(1\times 3)(3\times 1)$: sonuç $1\times 1$, yani tek bir sayı. Buna **iç çarpım** (dot product) denir.
--- cevap
$$
\ka{1}\cdot\kb{4}+\ka{2}\cdot\kb{5}+\ka{3}\cdot\kb{6}=4+10+18=\kutuc{32}
$$
--- kod
mo.carp([[1, 2, 3]], [4, 5, 6])
--- kontrol
r.deger == sp.Matrix([[32]])
--- yorum
Şekil değiştirme enerjisi $U=\tfrac12\,\mathbf{u}^T K\,\mathbf{u}$ da bu tür bir satır × sütun çarpımıyla tek bir sayıya iner.
:::

::: ornek Sütun × satır: bütün bir matris
$\begin{bmatrix}1\\2\end{bmatrix}\begin{bmatrix}3&4\end{bmatrix}$ nedir?
--- ipucu
$(2\times 1)(1\times 2)$: iç boyut 1, sonuç $2\times 2$. Her hücrede yalnız bir çarpım vardır.
--- cevap
$$
\begin{bmatrix}\ka{1}\\\ka{2}\end{bmatrix}\begin{bmatrix}\kb{3}&\kb{4}\end{bmatrix}
=
\begin{bmatrix}\ka{1}\cdot\kb{3}&\ka{1}\cdot\kb{4}\\\ka{2}\cdot\kb{3}&\ka{2}\cdot\kb{4}\end{bmatrix}
=
\begin{bmatrix}\kc{3}&\kc{4}\\\kc{6}&\kc{8}\end{bmatrix}
$$
--- kod
mo.carp([1, 2], [[3, 4]])
--- kontrol
r.deger == sp.Matrix([[3, 4], [6, 8]])
--- yorum
Buna **dış çarpım** (outer product) denir. Çubuk elemanın matrisi $\tfrac{EA}{L}\begin{bmatrix}1\\-1\end{bmatrix}\begin{bmatrix}1&-1\end{bmatrix}$ biçiminde bir dış çarpımdır.
:::

::: ornek Rijitlik × yer değiştirme = kuvvet
İki serbestlikli bir sistemde $K=\begin{bmatrix}200&-100\\-100&100\end{bmatrix}$ kN/m ve $\mathbf{u}=\begin{bmatrix}0.01\\0.03\end{bmatrix}$ m. Düğüm kuvvetleri $\mathbf{F}=K\mathbf{u}$ nedir?
--- ipucu
Her satır bir düğümün denge denklemidir: o satırı $\mathbf{u}$ ile iç çarp.
--- cevap
$$
\begin{bmatrix}\ka{200}&\ka{-100}\\-100&100\end{bmatrix}
\begin{bmatrix}\kb{0.01}\\\kb{0.03}\end{bmatrix}
=
\begin{bmatrix}\ka{200}\cdot\kb{0.01}+(\ka{-100})\cdot\kb{0.03}\\(-100)\cdot 0.01+100\cdot 0.03\end{bmatrix}
=
\begin{bmatrix}\kutuc{-1}\\\kutuc{2}\end{bmatrix}\ \text{kN}
$$
--- kod
mo.carp("200 -100; -100 100", "1/100; 3/100")
--- kontrol
r.deger == sp.Matrix([-1, 2])
--- yorum
Birimler: (kN/m)·(m) = kN. 1. düğümde $-1$ kN, 2. düğümde $+2$ kN kuvvet gerekir.
:::

::: ornek Üç matrisin çarpımı
$S=\begin{bmatrix}1&1\\0&1\end{bmatrix}$ için $S^3=SSS$ nedir?
--- ipucu
Birleşme özelliği sayesinde önce $SS$'yi bul, sonra bir kez daha $S$ ile çarp.
--- cevap
$$
\underbrace{\begin{bmatrix}1&1\\0&1\end{bmatrix}\begin{bmatrix}1&1\\0&1\end{bmatrix}}_{\begin{bmatrix}1&\kb{2}\\0&1\end{bmatrix}}
\begin{bmatrix}1&1\\0&1\end{bmatrix}
=
\begin{bmatrix}1&\kutuc{3}\\0&1\end{bmatrix}
$$
Her çarpımda sağ üstteki sayı 1 artar: $S^n=\begin{bmatrix}1&n\\0&1\end{bmatrix}$.
--- kod
mo.carp("1 1; 0 1", "1 1; 0 1", "1 1; 0 1")
--- kontrol
r.deger == sp.Matrix([[1, 3], [0, 1]])
:::

::: ornek Sıfır olmayan matrislerin çarpımı sıfır
$\begin{bmatrix}1&1\\1&1\end{bmatrix}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$ nedir?
--- cevap
$$
\begin{bmatrix}\ka{1}&\ka{1}\\1&1\end{bmatrix}\begin{bmatrix}\kb{1}&-1\\\kb{-1}&1\end{bmatrix}
\qquad
\ka{1}\cdot\kb{1}+\ka{1}\cdot(\kb{-1})=\kc{0}
\quad\Longrightarrow\quad
\begin{bmatrix}\kc{0}&\kc{0}\\\kc{0}&\kc{0}\end{bmatrix}
$$
--- kod
mo.carp("1 1; 1 1", "1 -1; -1 1")
--- kontrol
r.deger == sp.zeros(2, 2)
--- yorum
İkinci matris, mesnetsiz bir çubuğun rijitlik matrisinin biçimidir. Rijit cisim hareketi $\begin{bmatrix}1\\1\end{bmatrix}$ ona çarpılınca sıfır kuvvet verir. Bu yüzden mesnet koymadan $K\mathbf{u}=\mathbf{F}$ çözülemez.
:::

::: ornek Hangisi tanımlı?
$A$: $2\times 3$, $B$: $3\times 3$, $C$: $3\times 1$. $AB$, $BA$, $AC$, $CA$, $BC$ çarpımlarından hangileri tanımlıdır, boyutları nedir?
--- cevap
$$
\begin{aligned}
AB &: 2\times\kutua{3}\cdot\kutub{3}\times 3 \to \kc{2\times 3}\\
BA &: 3\times\kutua{3}\cdot\kutusil{2}\times 3 \to \ksil{\text{tanımsız}}\\
AC &: 2\times\kutua{3}\cdot\kutub{3}\times 1 \to \kc{2\times 1}\\
CA &: 3\times\kutua{1}\cdot\kutusil{2}\times 3 \to \ksil{\text{tanımsız}}\\
BC &: 3\times\kutua{3}\cdot\kutub{3}\times 1 \to \kc{3\times 1}
\end{aligned}
$$
:::

## Mühendislikte

::: muhendislik Bir köprü modelinde çarpımlar
Statik analizde $K\mathbf{u}=\mathbf{F}$, dinamikte $M\ddot{\mathbf{u}}+C\dot{\mathbf{u}}+K\mathbf{u}=\mathbf{F}(t)$ yazılır; her terim bir matris × vektör çarpımıdır. Eğik bir elemanın matrisi global eksenlere $T^T k\,T$ üç'lü çarpımıyla taşınır. Yığma köprüde OMA ile ölçülen mod şekli $\boldsymbol\phi$ için $\boldsymbol\phi^T M\boldsymbol\phi$ tek bir sayı verir: modal kütle. Model güncellemede bu sayılar ölçümle karşılaştırılır.
:::

::: ozet
- $c_{ij}$ = ($A$'nın $i.$ satırı) · ($B$'nin $j.$ sütunu).
- $(m\times n)(n\times p)\to m\times p$: iç boyutlar eşit olmalı.
- Genelde $AB\ne BA$; $AB=0$ olması $A$ ya da $B$'nin sıfır olduğunu göstermez.
- Matris × vektör, sütunların ağırlıklı toplamıdır: $K\mathbf{u}=\mathbf{F}$.
- Satır × sütun tek sayı (iç çarpım), sütun × satır bir matris (dış çarpım) verir.
:::

## Alıştırma

::: alistirma carpim
{"zorluk": 1}
:::

::: alistirma carpim
{"zorluk": 2}
:::

::: alistirma boyut
{"zorluk": 3}
:::
