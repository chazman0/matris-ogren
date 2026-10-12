---
baslik: Global rijitlik matrisinin birleştirilmesi
bolum: se
ozet: SD numaralama, kod numarası, eleman matrisini global matrise saçma, bant yapısı ve global K'nın özellikleri.
sure: 40
---

## Neden?

Bir köprü modelinde yüzlerce, bazen binlerce eleman vardır. Her birinin matrisini elle yerleştiremeyiz; bilgisayara tek bir kural vermemiz gerekir. Bu kuralın adı **birleştirmedir** (assembly). Kural o kadar basittir ki iki satırlık bir döngüyle yazılır, ama doğru anlaşılmazsa bütün sonuçlar yanlış çıkar.

## SD numaralama

Her düğüme sırayla global SD numaraları verilir. Düğüm başına $d$ SD varsa, listedeki $i$. düğüm şu numaraları alır:

$$
\ka{d(i-1)+1},\ \dots,\ \kb{d\,i}
$$

Kafeste $d=2$ olduğu için düğüm 1 → SD 1, 2; düğüm 2 → SD 3, 4; düğüm 3 → SD 5, 6 olur. Kirişte $d=2$ ($v,\theta$), düzlem çerçevede $d=3$ ($u,v,\theta$) alınır.

::: tanim Kod numarası
Bir elemanın **kod numarası** (code number), o elemanın yerel SD'lerinin global karşılıklarının listesidir. İki çubuklu kafeste eleman 1 düğüm 1 ile 3'ü bağlar, kod numarası $[1,2,5,6]$ olur. Birleştirmenin bütün bilgisi bu listededir.
:::

Aşağıdaki haritada Pratt köprüsünün her düğümüne verilen SD numaralarını görüyorsun. Bir elemanın üzerine gel, kod numarası belirsin.

::: etkilesim dof-haritasi
{"hazir": "pratt"}
:::

## Saçma kuralı

Eleman matrisinin $(a,b)$ hücresi, global matrisin $(g_a,g_b)$ hücresine **eklenir**. Burada $g$ kod numarasıdır. Üzerine yazılmaz, toplanır; ortak düğümlerde iki elemanın katkısı üst üste biner.

$$
K_{\,g_a g_b}\ \mathrel{+}=\ k^{(e)}_{ab},
\qquad a,b=1,\dots,n_e
$$

::: sekil Eleman 1'in 4×4 matrisi, kod [1 2 5 6] ile 6×6 global matrise saçılır
<svg viewBox="0 0 400 190" width="100%" font-family="system-ui" font-size="11" fill="currentColor">
<rect x="30" y="50" width="40" height="40" fill="var(--sema-a,#3b82f6)" opacity="0.35"/>
<rect x="70" y="50" width="40" height="40" fill="var(--sema-c,#10b981)" opacity="0.3"/>
<rect x="30" y="90" width="40" height="40" fill="var(--sema-c,#10b981)" opacity="0.3"/>
<rect x="70" y="90" width="40" height="40" fill="var(--sema-b,#f59e0b)" opacity="0.35"/>
<path d="M30 50H110M30 70H110M30 90H110M30 110H110M30 130H110M30 50V130M50 50V130M70 50V130M90 50V130M110 50V130" stroke="var(--sema-cizgi,#94a3b8)" fill="none"/>
<text x="37" y="44">1</text><text x="57" y="44">2</text><text x="77" y="44">5</text><text x="97" y="44">6</text>
<text x="18" y="64">1</text><text x="18" y="84">2</text><text x="18" y="104">5</text><text x="18" y="124">6</text>
<text x="70" y="150" text-anchor="middle">k⁽¹⁾ (4×4)</text>
<text x="70" y="166" text-anchor="middle">kod [1 2 5 6]</text>
<rect x="240" y="30" width="40" height="40" fill="var(--sema-a,#3b82f6)" opacity="0.35"/>
<rect x="320" y="30" width="40" height="40" fill="var(--sema-c,#10b981)" opacity="0.3"/>
<rect x="240" y="110" width="40" height="40" fill="var(--sema-c,#10b981)" opacity="0.3"/>
<rect class="vurgu" x="320" y="110" width="40" height="40" fill="var(--sema-b,#f59e0b)" opacity="0.35"/>
<path d="M240 30H360M240 50H360M240 70H360M240 90H360M240 110H360M240 130H360M240 150H360M240 30V150M260 30V150M280 30V150M300 30V150M320 30V150M340 30V150M360 30V150" stroke="var(--sema-cizgi,#94a3b8)" fill="none"/>
<text x="247" y="24">1</text><text x="267" y="24">2</text><text x="287" y="24">3</text><text x="307" y="24">4</text><text x="327" y="24">5</text><text x="347" y="24">6</text>
<text x="368" y="44">1</text><text x="368" y="64">2</text><text x="368" y="84">3</text><text x="368" y="104">4</text><text x="368" y="124">5</text><text x="368" y="144">6</text>
<text x="300" y="178" text-anchor="middle">K (6×6): satır ve sütun 3, 4 eleman 2'nin</text>
<path class="ok" pathLength="1" d="M50 70 C140 70 190 50 234 50" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<polyline class="ok-uc" points="228,46 234,50 228,54" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<path class="ok" pathLength="1" d="M90 110 C170 110 230 130 314 130" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<polyline class="ok-uc" points="308,126 314,130 308,134" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
</svg>
:::

İşlem sırası şudur. Önce global $\mathbf{K}$ sıfır matris olarak açılır. Sonra her eleman için kod numarası okunur ve eleman matrisinin her hücresi yukarıdaki kuralla eklenir. Bütün elemanlar bitince $\mathbf{K}$ hazırdır.

::: hata Toplamak yerine üzerine yazmak
İki elemanın ortak olduğu düğümde $K_{55}$ hücresine hem eleman 1'in hem eleman 2'nin katkısı gelir. İkincisini yazarken birincisini silersen yapı olduğundan yumuşak çıkar. Kural her zaman $\mathrel{+}=$'dir.
:::

::: hata Düğüm numarasını SD numarası sanmak
Kafeste düğüm 3'ün SD'leri 3 ve 4 değil, **5 ve 6**'dır. Kod numarasını yazmadan önce her zaman $d(i-1)+1$ kuralını uygula.
:::

## Global K'nın özellikleri

Birleştirme bitince $\mathbf{K}$ şu özellikleri taşır. Bunlar aynı zamanda hata yakalamak için kullandığın kontrollerdir.

- **Simetrik:** $K_{ij}=K_{ji}$. Simetrik değilse bir eleman yanlış yerleştirilmiştir.
- **Köşegen pozitif:** her SD'ye birim yer değiştirme vermek pozitif kuvvet ister.
- **Seyrek:** iki SD'yi bir eleman bağlamıyorsa o hücre sıfırdır.
- **Tekil:** mesnet konmadan $\det\mathbf{K}=0$'dır; yapı rijit cisim gibi kayabilir.

## Bant yapısı

Sıfır olmayan hücreler köşegen çevresinde bir **bant** oluşturur. Bant genişliği, bir elemanın bağladığı en uzak iki düğüm numarası arasındaki farka bağlıdır. Düğümleri yapı boyunca sırayla numaralarsan bant dar olur ve büyük modeller çok daha hızlı çözülür.

$$
\text{yarı bant genişliği}=d\,\big(\max_{e}\,|i_e-j_e|+1\big)
$$

::: ipucu Uzun yapıda kısa yönden numarala
Bir köprü tabliyesi uzun ve dardır. Düğümleri **enine** sırayla, sonra bir sonraki kesite geçerek numaralarsan $|i-j|$ farkı küçük kalır. Ticari programlar bunu kendileri yeniden sıralar, ama mantığını bilmek çıktıyı okurken işe yarar.
:::

Hiperstatik üç çubuklu kafeste dört düğüm ve sekiz SD var. Haritada her elemanın serbest düğüm 4'ün SD'leri olan 7 ve 8'e bağlandığını görüyorsun.

::: etkilesim dof-haritasi
{"hazir": "kafes-uc-cubuk"}
:::

## Çözümlü örnekler

::: ornek Yay zinciri: dar bant
Dört düğüm, üç eşit yay ($k=1000$), düğümler sırayla 1-2, 2-3, 3-4 bağlı. Global matrisi kur.
--- ipucu
Kod numaraları $[1,2]$, $[2,3]$, $[3,4]$. İç düğümlerde iki yay toplanır.
--- cevap
$$
\mathbf{K}=\begin{bmatrix}1000&-1000&0&0\\-1000&2000&-1000&0\\0&-1000&2000&-1000\\0&0&-1000&1000\end{bmatrix}
$$
--- kod
mo.birlestir([("1000 -1000; -1000 1000", [1, 2]), ("1000 -1000; -1000 1000", [2, 3]), ("1000 -1000; -1000 1000", [3, 4])], 4)
--- kontrol
r.deger[1, 1] == 2000 and r.deger[0, 2] == 0 and r.deger[0, 3] == 0
--- yorum
Üç köşegenli (tridiagonal) bir matris çıktı. Sıfır olmayan her hücre köşegenin hemen yanında.
:::

::: ornek Aynı zincir, kötü numaralama
Aynı yaylar, ama düğümler fiziksel sırayla 1, 4, 2, 3 diye numaralanmış. Kod numaraları $[1,4]$, $[4,2]$, $[2,3]$ olur. Matrisi kur ve öncekiyle karşılaştır.
--- ipucu
Eleman 1 SD 1 ile 4'ü bağlar; köşeye kadar giden bir hücre doğar.
--- cevap
$K_{14}=-1000$; bant köşeye kadar açıldı. Sayılar aynı, yerleri farklı. Çözüm aynı çıkar ama büyük modelde hesap çok yavaşlar.
--- kod
mo.birlestir([("1000 -1000; -1000 1000", [1, 4]), ("1000 -1000; -1000 1000", [4, 2]), ("1000 -1000; -1000 1000", [2, 3])], 4)
--- kontrol
r.deger[0, 3] == -1000 and r.deger[0, 1] == 0 and r.deger[3, 3] == 2000
--- yorum
Numaralama fiziği değiştirmez, yalnız matrisin görünüşünü ve çözüm maliyetini değiştirir.
:::

::: ornek Paralel iki yay aynı düğümlerde
Düğüm 1 ve 2 arasında $k_1=1000$ ve $k_2=2000$ iki yay var. İkisinin kod numarası da $[1,2]$. Birleştir.
--- ipucu
Aynı hücrelere iki kez eklenir.
--- cevap
$\mathbf{K}=\begin{bmatrix}3000&-3000\\-3000&3000\end{bmatrix}$: paralel yayların rijitlikleri toplanır.
--- kod
mo.birlestir([("1000 -1000; -1000 1000", [1, 2]), ("2000 -2000; -2000 2000", [1, 2])], 2)
--- kontrol
r.deger == sp.Matrix([[3000, -3000], [-3000, 3000]])
--- yorum
Yay sistemleri dersindeki $k_{eş}=k_1+k_2$ formülü, birleştirme kuralının özel bir halidir.
:::

::: ornek İki çubuklu kafesin 6×6 matrisi
Bir önceki derste kurduğun iki $4\times4$ matrisi birleştir. Eleman 1: kod $[1,2,5,6]$, $c=3/5$, $s=4/5$. Eleman 2: kod $[3,4,5,6]$, $c=-3/5$, $s=4/5$.
--- ipucu
İki elemanın da düğüm 3 bloğu ($K_{55}$, $K_{56}$, $K_{66}$) üst üste biner. $cs$ terimleri zıt işaretli olduğu için $K_{56}$ sıfırlanır.
--- cevap
$K_{55}=14\,400+14\,400=28\,800$, $K_{66}=25\,600+25\,600=51\,200$, $K_{56}=19\,200-19\,200=0$.
--- kod
mo.birlestir([("14400 19200 -14400 -19200; 19200 25600 -19200 -25600; -14400 -19200 14400 19200; -19200 -25600 19200 25600", [1, 2, 5, 6]), ("14400 -19200 -14400 19200; -19200 25600 19200 -25600; -14400 19200 14400 -19200; 19200 -25600 -19200 25600", [3, 4, 5, 6])], 6)
--- kontrol
r.deger[4, 4] == 28800 and r.deger[5, 5] == 51200 and r.deger[4, 5] == 0 and r.deger == r.deger.T
--- yorum
$K_{56}=0$ simetrinin sonucudur: tepe düğümü yatay itilince düşeyde kaymaz. Yapı simetrikse bu tür sıfırlar beklenir.
:::

::: ornek Birleştir ve çöz
Aynı kafeste düğüm 1 ve 2 mafsallı (SD 1–4 tutulu), tepeye $F_6=-10$ kN. $\mathbf{K}$'yı birleştir, sonra sınır koşulunu uygula.
--- ipucu
Serbest SD'ler yalnız 5 ve 6. İndirgenmiş matris köşegen: $\mathrm{diag}(28\,800,\ 51\,200)$.
--- cevap
$u_3=0$, $v_3=-10/51\,200=-1/5120$ m.
--- kod
K = mo.birlestir([("14400 19200 -14400 -19200; 19200 25600 -19200 -25600; -14400 -19200 14400 19200; -19200 -25600 19200 25600", [1, 2, 5, 6]), ("14400 -19200 -14400 19200; -19200 25600 19200 -25600; -14400 19200 14400 -19200; 19200 -25600 -19200 25600", [3, 4, 5, 6])], 6)
K, mo.sinir_kosulu(K.deger, "0; 0; 0; 0; 0; -10", sabit=[1, 2, 3, 4])
--- kontrol
r[-1].deger[5] == sp.Rational(-1, 5120) and r[-1].deger[4] == 0
--- yorum
Sonuç, hazır `kafes-iki-cubuk` modelini `se.se_coz` ile çözdüğünde bulduğunla aynı. Programın içinde olan tam olarak budur.
:::

::: ornek Mesnetsiz matris tekildir
Yay zincirinin $\mathbf{K}$'sının determinantını hesapla.
--- ipucu
Her satırın toplamı sıfır; sütunlar doğrusal bağımlı.
--- cevap
$\det\mathbf{K}=0$. Mesnet konmadan sistem çözülemez.
--- kod
mo.determinant("1000 -1000 0 0; -1000 2000 -1000 0; 0 -1000 2000 -1000; 0 0 -1000 1000")
--- kontrol
r.deger == 0
--- yorum
Fiziksel anlamı: bütün zincir hiç uzamadan kayabilir, bu hareket enerji gerektirmez. Bir sonraki derste mesnetleri ekleyip bu tekilliği kaldıracağız.
:::

::: ornek Pratt köprüsünde kod numarası
Pratt modelinde düğüm listesi 1'den 8'e sıralı. Eleman 12, düğüm 6'dan düğüm 3'e gider. Kod numarası nedir?
--- ipucu
$d=2$. Düğüm 6 → $2\cdot5+1=11$ ve $12$. Düğüm 3 → 5 ve 6.
--- cevap
$[11,12,5,6]$.
--- yorum
Kod numarasındaki sıra, elemanın yönüne (i→j) uyar. Yön ters olsa $[5,6,11,12]$ olurdu; birleştirme sonucu aynıdır.
:::

::: ornek Pratt köprüsünün bant genişliği
Pratt modelinde en uzak düğümleri bağlayan eleman 7'dir (düğüm 1 ile 6). Yarı bant genişliğini bul.
--- ipucu
$\max|i-j|=5$, $d=2$.
--- cevap
$2\cdot(5+1)=12$. 16×16 matrisin her satırında, köşegenden en fazla 11 hücre ötede sıfır olmayan değer olabilir.
--- yorum
Alt ve üst düğümleri sırayla yukarı aşağı numaralasaydık en büyük fark 2'ye iner ve bant yarıya yakın daralırdı.
:::

::: muhendislik Büyük modeller ve seyreklik
Tarihi bir taş köprünün katı (solid) modelinde yüz binlerce SD olabilir. Global $\mathbf{K}$'nın hücrelerinin yüzde 99'dan fazlası sıfırdır; programlar yalnız sıfır olmayanları saklar.

Model güncellemede (model updating) $E$ değiştirildiğinde $\mathbf{K}$ baştan birleştirilmez. Yalnız ilgili elemanların katkısı çıkarılıp yenisi eklenir; bu ders tam olarak bu işlemi anlatır.
:::

::: ozet Özet
- Düğüm $i$'nin SD'leri: $d(i-1)+1,\dots,d\,i$.
- Kod numarası, elemanın yerel SD'lerinin global karşılıklarıdır.
- Kural: $K_{g_ag_b}\mathrel{+}=k_{ab}$; ortak düğümde katkılar **toplanır**.
- Global K simetrik, köşegeni pozitif, seyrek ve mesnetsiz halde tekildir.
- Düğümleri yapı boyunca sırayla numaralamak bandı daraltır.
:::

## Alıştırma

::: alistirma birlestir
{"zorluk": 1}
:::

::: alistirma birlestir
{"zorluk": 2}
:::
