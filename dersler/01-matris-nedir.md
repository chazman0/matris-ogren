---
baslik: Matris nedir?
bolum: matris
ozet: Matris, boyut, eleman indisi, satır ve sütun vektörü, özel matrisler.
sure: 30
---

## Neden matris?

Üç düğümlü bir çubuğu düşün. Her düğümdeki kuvvet, bütün düğümlerin yer değiştirmesine bağlıdır. Bu bağları tek tek denklem olarak yazmak yerine sayıları bir tabloya dizeriz. Sonlu eleman yönteminin bütün dili bu tablodur: **matris** (matrix).

Tarihi bir yığma köprünün sonlu eleman modelinde binlerce bilinmeyen vardır. Bilgisayar onları tek bir denklemle çözer: $K\mathbf{u}=\mathbf{F}$. Bu derste o denklemin harflerini okumayı öğreneceksin.

## Matris ve boyut

::: tanim Matris
**Matris**, sayıların satır ve sütunlar hâlinde dikdörtgen bir tabloya dizilmesidir. $m$ satırı ve $n$ sütunu olan matrise $m\times n$ matris denir; $m\times n$ onun **boyutudur** (size). Eleman sayısı $m\cdot n$'dir.
:::

Aşağıdaki $A$ matrisinin 3 satırı, 4 sütunu vardır. Boyutu $3\times 4$, eleman sayısı $12$'dir.

$$
A=\begin{bmatrix}
2 & 0 & 7 & 1\\
5 & -3 & 4 & 8\\
6 & 9 & -2 & 0
\end{bmatrix}
\qquad
\underbrace{3}_{\ka{m}\ \text{satır}}\times\underbrace{4}_{\kb{n}\ \text{sütun}}
$$

Boyut her zaman **önce satır, sonra sütun** diye okunur. $4\times 3$ başka bir matristir.

## Eleman indisi $a_{ij}$

Matrisin her elemanının bir adresi vardır. $a_{ij}$, $\ka{i}$. satır ile $\kb{j}$. sütunun kesiştiği hücredir. İlk indis satır, ikinci indis sütundur.

::: sekil Satır bandı ile sütun bandının kesişimi: $a_{23}$
<svg viewBox="0 0 360 230" width="100%" font-family="system-ui" font-size="13" fill="currentColor">
<rect x="80" y="90" width="240" height="40" fill="var(--sema-a-bg,rgba(59,130,246,.12))"/>
<rect x="200" y="50" width="60" height="120" fill="var(--sema-b-bg,rgba(245,158,11,.14))"/>
<rect class="vurgu" rx="6" x="203" y="93" width="54" height="34" fill="var(--sema-c-bg,rgba(16,185,129,.16))" stroke="var(--sema-c,#10b981)" stroke-width="2"/>
<path d="M84 50 h-8 v120 h8 M316 50 h8 v120 h-8" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="2"/>
<g text-anchor="middle">
<text x="110" y="75">2</text><text x="170" y="75">0</text><text x="230" y="75">7</text><text x="290" y="75">1</text>
<text x="110" y="115">5</text><text x="170" y="115">-3</text><text x="230" y="115" font-weight="700" fill="var(--sema-c,#10b981)">4</text><text x="290" y="115">8</text>
<text x="110" y="155">6</text><text x="170" y="155">9</text><text x="230" y="155">-2</text><text x="290" y="155">0</text>
</g>
<path class="ok" pathLength="1" d="M14 110 H72" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2.5"/>
<polyline class="ok-uc" points="64,104 72,110 64,116" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2.5"/>
<text x="14" y="100" fill="var(--sema-a,#3b82f6)">i = 2</text>
<path class="ok" pathLength="1" d="M230 12 V44" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5"/>
<polyline class="ok-uc" points="224,36 230,44 236,36" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5"/>
<text x="240" y="24" fill="var(--sema-b,#f59e0b)">j = 3</text>
<path d="M80 192 H320 M80 186 v12 M320 186 v12" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5"/>
<text x="200" y="214" text-anchor="middle">n = 4 sütun</text>
<path d="M340 50 V170 M334 50 h12 M334 170 h12" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5"/>
<text x="352" y="114" text-anchor="middle" transform="rotate(90 352 114)">m = 3 satır</text>
</svg>
:::

Mavi bant 2. satırı, turuncu bant 3. sütunu gösteriyor. Kesiştikleri yeşil hücre $a_{23}=4$'tür. Şimdi kendin dene: hücrelere dokun ve indisin nasıl değiştiğine bak.

::: etkilesim matris-gezgini
{"A": "2 0 7 1; 5 -3 4 8; 6 9 -2 0", "ad": "A", "baslik": "Bir hücreye dokun: satırı ve sütunu yanar"}
:::

::: hata Satır ile sütunu karıştırmak
$a_{23}$ ile $a_{32}$ aynı eleman değildir. Yukarıdaki matriste $a_{23}=\kutuc{4}$ ama $a_{32}=\kutusil{9}$. Kural: **önce satır (aşağı in), sonra sütun (sağa git).**
:::

## Vektörler: tek satırlı ya da tek sütunlu matris

Tek sütunlu matrise **sütun vektörü** (column vector), tek satırlı matrise **satır vektörü** (row vector) denir. Mühendislikte vektör denince çoğunlukla sütun vektörü kastedilir. Yer değiştirmeler $\mathbf{u}$ ve kuvvetler $\mathbf{F}$ birer sütun vektörüdür.

$$
\underbrace{\begin{bmatrix} \ka{u_1} \\ \ka{u_2} \\ \ka{u_3} \end{bmatrix}}_{3\times 1\ \text{sütun vektörü}}
\qquad
\underbrace{\begin{bmatrix} \kb{1} & \kb{4} & \kb{-2} \end{bmatrix}}_{1\times 3\ \text{satır vektörü}}
$$

Bir matrisin her satırı bir satır vektörü, her sütunu bir sütun vektörüdür. $3\times 4$'lük $A$, üst üste dizilmiş 3 satır vektörü ya da yan yana dizilmiş 4 sütun vektörü olarak görülebilir.

## Özel matrisler

::: tanim Kare matris ve köşegen
Satır sayısı sütun sayısına eşitse ($m=n$) matris **karedir** (square). Kare matriste $a_{11}, a_{22}, \dots, a_{nn}$ elemanları **ana köşegeni** (main diagonal) oluşturur. Köşegen elemanlarının toplamına **iz** (trace) denir: $\operatorname{tr}(A)=\sum_i a_{ii}$.
:::

$$
\begin{bmatrix}
\kutuc{4} & 1 & 0\\
2 & \kutuc{5} & 3\\
0 & 7 & \kutuc{6}
\end{bmatrix}
\qquad
\operatorname{tr}=\kc{4}+\kc{5}+\kc{6}=15
$$

Sık karşılaşacağın özel kare matrisler şunlardır:

- **Köşegen matris** (diagonal): köşegen dışı bütün elemanlar sıfırdır. Toplanmış kütle matrisi $M$ böyledir.
- **Birim matris** $I$ (identity): köşegeni 1, geri kalanı 0. Her matrisi çarpınca değiştirmez: $IA=A$.
- **Sıfır matris** $0$: bütün elemanlar sıfır. Toplamada etkisizdir: $A+0=A$.
- **Üst üçgen** (upper triangular): köşegenin altı sıfır. Gauss eliminasyonu matrisi bu biçime getirir.
- **Simetrik** (symmetric): $a_{ij}=a_{ji}$; köşegene göre ayna görüntüsü. Rijitlik matrisi $K$ her zaman simetriktir.

$$
\underbrace{\begin{bmatrix} 1&0&0\\0&1&0\\0&0&1 \end{bmatrix}}_{I_3\ \text{birim}}
\qquad
\underbrace{\begin{bmatrix} 2&\ka{-1}&0\\\kb{-1}&2&\ka{-1}\\0&\kb{-1}&2 \end{bmatrix}}_{\text{simetrik: } \ka{a_{ij}}=\kb{a_{ji}}}
\qquad
\underbrace{\begin{bmatrix} 3&1&4\\\ksil{0}&2&5\\\ksil{0}&\ksil{0}&6 \end{bmatrix}}_{\text{üst üçgen}}
$$

Simetriyi gözünle gör: aşağıdaki çizimde elemanlar köşegen aynasına göre yer değiştiriyor. Simetrik bir matris bu yansımada hiç değişmez.

::: etkilesim transpoz-aynasi
{"A": "2 -1 0; -1 2 -1; 0 -1 2", "baslik": "Simetrik matris köşegen aynasında değişmez"}
:::

## Çözümlü örnekler

::: ornek Boyut ve eleman sayısı
$B=\begin{bmatrix}1&4\\-2&0\\3&7\end{bmatrix}$ matrisinin boyutu nedir? Kaç elemanı vardır? $b_{31}$ ve $b_{12}$ nedir?
--- ipucu
Önce satırları say (yukarıdan aşağı), sonra sütunları (soldan sağa).
--- cevap
$$
B=\begin{bmatrix}1&\kb{4}\\-2&0\\\ka{3}&7\end{bmatrix}
\qquad
\begin{aligned}
\text{boyut} &= 3\times 2,\quad 3\cdot 2=6\ \text{eleman}\\
b_{31} &= \ka{3}\quad(\text{3. satır, 1. sütun})\\
b_{12} &= \kb{4}\quad(\text{1. satır, 2. sütun})
\end{aligned}
$$
:::

::: ornek Kurala göre matris kurmak
$a_{ij}=i+2j$ kuralıyla $2\times 3$'lük $A$ matrisini yaz.
--- ipucu
Her hücre için satır numarası $i$'yi ve sütun numarası $j$'yi kurala koy.
--- cevap
$$
A=\begin{bmatrix}
\ka{1}+2\cdot\kb{1} & \ka{1}+2\cdot\kb{2} & \ka{1}+2\cdot\kb{3}\\
\ka{2}+2\cdot\kb{1} & \ka{2}+2\cdot\kb{2} & \ka{2}+2\cdot\kb{3}
\end{bmatrix}
=
\begin{bmatrix} \kc{3} & \kc{5} & \kc{7}\\ \kc{4} & \kc{6} & \kc{8} \end{bmatrix}
$$
--- yorum
Rijitlik matrisleri de böyle kurallarla dolar: $k_{ij}$, $j$. serbestlikteki birim yer değiştirmenin $i$. serbestlikte doğurduğu kuvvettir.
:::

::: ornek İz
$A=\begin{bmatrix}4&1&0\\2&5&3\\0&7&6\end{bmatrix}$ için $\operatorname{tr}(A)$ nedir?
--- ipucu
Yalnız ana köşegene bak: sol üstten sağ alta.
--- cevap
$$
\begin{bmatrix}
\kutuc{4} & 1 & 0\\
2 & \kutuc{5} & 3\\
0 & 7 & \kutuc{6}
\end{bmatrix}
\xrightarrow{\ \text{köşegeni topla}\ }
\kc{4}+\kc{5}+\kc{6}=\kutuc{15}
$$
--- kod
mo.iz("4 1 0; 2 5 3; 0 7 6")
--- kontrol
r.deger == 15
:::

::: ornek Satır vektöründen sütun vektörüne
$\mathbf{v}=\begin{bmatrix}1&4&-2\end{bmatrix}$ satır vektörünü sütun vektörüne çevir. Yeni boyut nedir?
--- ipucu
Satır sütun olur: yatay diziyi dikey yaz. Bu işleme devrik (transpoz) denir; 4. derste ayrıntısı var.
--- cevap
$$
\underbrace{\begin{bmatrix}\ka{1}&\kb{4}&\kc{-2}\end{bmatrix}}_{1\times 3}
\xrightarrow{\ T\ }
\underbrace{\begin{bmatrix}\ka{1}\\\kb{4}\\\kc{-2}\end{bmatrix}}_{3\times 1}
$$
--- kod
mo.transpoz([[1, 4, -2]])
--- kontrol
r.deger.shape == (3, 1)
:::

::: ornek Birim matris hiçbir şeyi değiştirmez
$I_2\,A$ çarpımını hesapla: $A=\begin{bmatrix}3&-1\\4&2\end{bmatrix}$.
--- ipucu
Birim matrisin her satırında yalnız bir tane 1 vardır; o 1, $A$'nın bir satırını aynen seçer.
--- cevap
$$
\begin{bmatrix}\ka{1}&\ka{0}\\0&1\end{bmatrix}
\begin{bmatrix}\kb{3}&-1\\\kb{4}&2\end{bmatrix}
=
\begin{bmatrix}\kutuc{3}&-1\\4&2\end{bmatrix}
\qquad
\kc{3}=\ka{1}\cdot\kb{3}+\ka{0}\cdot\kb{4}
$$
Her hücrede aynı şey olur; sonuç $A$'nın kendisidir: $IA=A$.
--- kod
mo.carp(mo.birim(2), "3 -1; 4 2")
--- kontrol
r.deger == sp.Matrix([[3, -1], [4, 2]])
:::

::: ornek Birim vektörle bir sütunu seçmek
$A=\begin{bmatrix}2&0&1\\3&5&4\end{bmatrix}$ matrisini $\mathbf{e}_2=\begin{bmatrix}0\\1\\0\end{bmatrix}$ ile çarp. Sonuç neyi verir?
--- ipucu
$\mathbf{e}_2$'nin yalnız 2. elemanı 1'dir; çarpımda yalnız $A$'nın 2. sütunu hayatta kalır.
--- cevap
$$
\begin{bmatrix}2&\kutub{0}&1\\3&\kutub{5}&4\end{bmatrix}
\begin{bmatrix}\ksil{0}\\\kb{1}\\\ksil{0}\end{bmatrix}
=
\begin{bmatrix}2\cdot\ksil{0}+\kb{0}\cdot 1+1\cdot\ksil{0}\\3\cdot\ksil{0}+\kb{5}\cdot 1+4\cdot\ksil{0}\end{bmatrix}
=
\begin{bmatrix}\kc{0}\\\kc{5}\end{bmatrix}
$$
--- kod
mo.carp("2 0 1; 3 5 4", [[0], [1], [0]])
--- kontrol
r.deger == sp.Matrix([[0], [5]])
--- yorum
Rijitlik matrisinin $j$. sütunu tam olarak budur: yalnız $j$. serbestliğe birim yer değiştirme verince düğümlerde doğan kuvvetler.
:::

::: ornek Simetri denetimi
$K=\begin{bmatrix}2&-1&0\\-1&2&-1\\0&-1&2\end{bmatrix}$ simetrik mi? Devriğini alıp karşılaştır.
--- ipucu
Köşegenin üstündeki her elemanı aynadaki eşiyle karşılaştır: $k_{12}$ ile $k_{21}$, $k_{13}$ ile $k_{31}$, $k_{23}$ ile $k_{32}$.
--- cevap
$$
\begin{aligned}
\ka{k_{12}}&=-1=\kb{k_{21}}\\
\ka{k_{13}}&=\phantom{-}0=\kb{k_{31}}\\
\ka{k_{23}}&=-1=\kb{k_{32}}
\end{aligned}
\qquad\Longrightarrow\qquad
K^T=K\ \ \kutuc{\text{simetrik}}
$$
--- kod
mo.transpoz("2 -1 0; -1 2 -1; 0 -1 2")
--- kontrol
r.deger == sp.Matrix([[2, -1, 0], [-1, 2, -1], [0, -1, 2]])
--- yorum
Bu matris, uç uca bağlı yaylardan oluşan bir zincirin rijitlik matrisine benzer. Maxwell–Betti karşılıklılık teoremi yüzünden doğrusal elastik yapılarda $K$ hep simetriktir.
:::

::: ornek Sıfır matris toplamada etkisizdir
$\begin{bmatrix}1&2\\3&4\end{bmatrix}+0_{2\times 2}$ nedir?
--- cevap
$$
\begin{bmatrix}\ka{1}&\ka{2}\\\ka{3}&\ka{4}\end{bmatrix}
+
\begin{bmatrix}\kb{0}&\kb{0}\\\kb{0}&\kb{0}\end{bmatrix}
=
\begin{bmatrix}\kc{1}&\kc{2}\\\kc{3}&\kc{4}\end{bmatrix}
$$
--- kod
mo.topla("1 2; 3 4", mo.sifir(2))
--- kontrol
r.deger == sp.Matrix([[1, 2], [3, 4]])
:::

::: ornek Matrisin türünü tanı
Hangisi köşegen, hangisi üst üçgen, hangisi simetrik?
$P=\begin{bmatrix}5&0\\0&-2\end{bmatrix}$, $Q=\begin{bmatrix}1&3\\0&4\end{bmatrix}$, $R=\begin{bmatrix}1&3\\3&4\end{bmatrix}$
--- ipucu
Önce köşegen dışına bak: hepsi sıfır mı, yalnız altı mı sıfır, yoksa aynadaki eşler mi eşit?
--- cevap
$$
P=\begin{bmatrix}5&\ksil{0}\\\ksil{0}&-2\end{bmatrix}\ \text{köşegen}
\qquad
Q=\begin{bmatrix}1&3\\\ksil{0}&4\end{bmatrix}\ \text{üst üçgen}
\qquad
R=\begin{bmatrix}1&\ka{3}\\\kb{3}&4\end{bmatrix}\ \text{simetrik}
$$
$P$ aynı zamanda hem üst üçgen hem simetriktir: köşegen matris her ikisinin de özel hâlidir.
:::

## Mühendislikte

::: muhendislik Rijitlik matrisinin elemanları ne anlatır?
Üç düğümlü bir çubuk ya da yay zincirinde denge $K\mathbf{u}=\mathbf{F}$ biçimindedir. $K$ kare ve simetrik, $\mathbf{u}$ ile $\mathbf{F}$ sütun vektörüdür. $k_{ij}$, yalnız $j$. düğüme birim yer değiştirme verildiğinde $i$. düğümde gereken kuvvettir; birimi kN/m'dir. Tezindeki yığma köprü modelinde $K$ binlerce satırlıdır ama okuma kuralı aynıdır. OMA ile ölçtüğün mod şekilleri de birer sütun vektörüdür: her eleman bir ivmeölçer noktasının genliğidir.
:::

::: ozet
- $m\times n$: önce satır, sonra sütun. Eleman sayısı $m\cdot n$.
- $a_{ij}$: $i$. satır ile $j$. sütunun kesişimi.
- Sütun vektörü $n\times 1$, satır vektörü $1\times n$.
- Kare matriste ana köşegen ve iz; birim $I$, sıfır $0$, köşegen, üçgen, simetrik matrisler.
- Rijitlik matrisi $K$ kare ve simetriktir.
:::

## Alıştırma

Boyut, eleman okuma ve çarpımın tanımlı olup olmadığı üzerine sınırsız soru. Önce kolay, sonra orta düzey.

::: alistirma boyut
{"zorluk": 1}
:::

::: alistirma boyut
{"zorluk": 2}
:::
