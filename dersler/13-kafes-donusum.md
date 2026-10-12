---
baslik: Düzlem kafes ve koordinat dönüşümü
bolum: se
ozet: Eğik çubuk, yön kosinüsleri c ve s, dönüşüm matrisi T ve k = Tᵀk′T; kafes elemanının eksenel kuvveti.
sure: 45
---

## Neden?

Kafes köprüde çubuklar yatay, düşey ve eğik durur. Her çubuk kendi ekseninde bir yaydır, ama düğümler **x** ve **y** yönünde hareket eder. Çubuğun dilinden yapının diline çeviri yapmamız gerekir. Bu çevirinin adı **koordinat dönüşümüdür**; bütün çerçeve ve kabuk elemanlarında da aynı fikir kullanılır.

## Yerel ve global eksen

::: tanim Yerel ve global eksen
**Yerel eksen** $x'$, çubuğun kendi ekseni boyuncadır ve i düğümünden j düğümüne doğru bakar. **Global eksen** $x$-$y$, bütün yapı için ortak olan eksen takımıdır. Düzlem kafeste her düğümün iki SD'si vardır: $u$ (yatay) ve $v$ (düşey).
:::

::: sekil Eğik kafes elemanı: yerel eksen, açı ve global SD'ler
<svg viewBox="0 0 400 220" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<path d="M20 205 H58 M20 205 V167" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<polyline points="52,201 58,205 52,209" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5"/>
<polyline points="16,173 20,167 24,173" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5"/>
<text x="62" y="209">x</text>
<text x="16" y="161">y</text>
<path d="M90 170 L300 60" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="6" stroke-linecap="round"/>
<path class="vurgu" d="M300 60 L352 33" stroke="var(--sema-a,#3b82f6)" stroke-width="2" stroke-dasharray="5 4"/>
<text x="355" y="30" fill="var(--sema-a,#3b82f6)">x′ (yerel)</text>
<path d="M90 170 H160" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="3 3"/>
<path class="ok" pathLength="1" d="M150 170 A60 60 0 0 0 143 142" fill="none" stroke="var(--sema-c,#10b981)" stroke-width="2"/>
<text x="156" y="157" fill="var(--sema-c,#10b981)">θ</text>
<circle cx="90" cy="170" r="7" fill="var(--sema-cizgi,#94a3b8)"/>
<circle cx="300" cy="60" r="7" fill="var(--sema-cizgi,#94a3b8)"/>
<text x="74" y="196">i (1)</text>
<text x="284" y="86">j (2)</text>
<path class="ok" pathLength="1" d="M90 170 H124" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5" fill="none"/>
<polyline class="ok-uc" points="118,166 124,170 118,174" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5"/>
<path class="ok" pathLength="1" d="M90 170 V134" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5" fill="none"/>
<polyline class="ok-uc" points="86,140 90,134 94,140" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5"/>
<text x="112" y="188" fill="var(--sema-b,#f59e0b)">u₁</text>
<text x="70" y="140" fill="var(--sema-b,#f59e0b)">v₁</text>
<path class="ok" pathLength="1" d="M300 60 H336" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5" fill="none"/>
<polyline class="ok-uc" points="330,56 336,60 330,64" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5"/>
<path class="ok" pathLength="1" d="M300 60 V24" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5" fill="none"/>
<polyline class="ok-uc" points="296,30 300,24 304,30" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5"/>
<text x="338" y="76" fill="var(--sema-b,#f59e0b)">u₂</text>
<text x="280" y="28" fill="var(--sema-b,#f59e0b)">v₂</text>
<text x="170" y="100" transform="rotate(-27 170 100)">eleman: E, A, L</text>
</svg>
:::

## Yön kosinüsleri

Eleman açısını $\theta$ ile gösteririz; global $x$ ekseninden saat yönünün tersine ölçülür. Koordinatlardan doğrudan hesaplanır, açıya hiç gerek kalmaz.

$$
\ka{c}=\cos\theta=\frac{x_j-x_i}{L},
\qquad
\kb{s}=\sin\theta=\frac{y_j-y_i}{L},
\qquad
L=\sqrt{(x_j-x_i)^2+(y_j-y_i)^2}
$$

Çubuğun uzaması yalnız **eksen yönündeki** hareketlerden gelir. Düğümün $(u,v)$ hareketini eksene izdüşürürüz: $u'=\ka{c}\,u+\kb{s}\,v$.

## Dönüşüm matrisi ve k = Tᵀk′T

İki düğümün izdüşümlerini tek matrisle yazarız. $\mathbf{T}$, dört global SD'yi iki yerel eksenel yer değiştirmeye çevirir.

$$
\begin{bmatrix}u'_1\\u'_2\end{bmatrix}
=
\underbrace{\begin{bmatrix}\ka{c}&\kb{s}&0&0\\0&0&\ka{c}&\kb{s}\end{bmatrix}}_{\mathbf{T}\ (2\times4)}
\begin{bmatrix}u_1\\v_1\\u_2\\v_2\end{bmatrix}
$$

Yerel matris bir önceki dersteki çubuk matrisidir. Global matris, enerji eşitliğinden çıkan üçlü çarpımdır; boyutlar $4\times2\cdot2\times2\cdot2\times4$ olur.

$$
\mathbf{k}=\mathbf{T}^T\,\mathbf{k}'\,\mathbf{T}
=\kutua{\frac{EA}{L}}
\begin{bmatrix}
\ka{c^2}&\kc{cs}&-\ka{c^2}&-\kc{cs}\\
\kc{cs}&\kb{s^2}&-\kc{cs}&-\kb{s^2}\\
-\ka{c^2}&-\kc{cs}&\ka{c^2}&\kc{cs}\\
-\kc{cs}&-\kb{s^2}&\kc{cs}&\kb{s^2}
\end{bmatrix}
$$

::: not Desen
Matris dört tane $2\times2$ bloktan oluşur: $\begin{bmatrix}\mathbf{B}&-\mathbf{B}\\-\mathbf{B}&\mathbf{B}\end{bmatrix}$, burada $\mathbf{B}=\frac{EA}{L}\begin{bmatrix}c^2&cs\\cs&s^2\end{bmatrix}$. Yani kafes elemanı hâlâ bir yaydır; yalnız her uçta iki yönlü bir yaydır.
:::

Açıyı değiştir ve renkli terimlerin nasıl değiştiğini izle. $\theta=0$'da yalnız $c^2$, $\theta=90°$'de yalnız $s^2$ kalır.

::: etkilesim kafes-aci
{"E": 200000000, "A": 0.001, "L": 5, "aci": 53.13}
:::

::: uyari Yön seçimi
Elemanı i→j yerine j→i yönünde tanımlarsan $c$ ve $s$ ikisi birden işaret değiştirir. $c^2$, $s^2$ ve $cs$ değişmez; yani **k aynı kalır**. Değişen tek şey, sonradan eksenel kuvveti hesaplarken hangi ucun "baş" sayıldığıdır.
:::

::: hata Dereceyi radyan sanmak
$\cos 30$ yazıp hesap makinesini radyanda bırakırsan $0.154$ çıkar, doğrusu $0.866$'dır. En güvenli yol açıyı hiç kullanmamaktır: $c$ ve $s$'yi düğüm koordinatlarından hesapla.
:::

::: hata Yerel 2×2 matrisi global sisteme koymak
$\frac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$ yalnız eksen yönünü bilir. Eğik bir çubuğu bu haliyle global matrise eklemek, çubuğun düşey rijitliğini tamamen yok sayar. Önce $\mathbf{T}^T\mathbf{k}'\mathbf{T}$ ile $4\times4$'e çevir.
:::

## Eleman kuvvetini geri bulmak

Global yer değiştirmeler bulununca yol geriye işler. $\mathbf{T}$ ile yerel uç yer değiştirmelerini, onların farkıyla uzamayı, oradan eksenel kuvveti buluruz.

$$
\delta=u'_2-u'_1=\begin{bmatrix}-c&-s&c&s\end{bmatrix}\begin{bmatrix}u_1\\v_1\\u_2\\v_2\end{bmatrix},
\qquad
N=\kutuc{\frac{EA}{L}}\,\delta
$$

Aşağıdaki haritada her düğümün SD numarasını ve her elemanın hangi SD'lere bağlandığını görüyorsun. Bir sonraki derste bu numaraları kullanarak birleştirme yapacağız.

::: etkilesim dof-haritasi
{"hazir": "kafes-iki-cubuk"}
:::

## Çözümlü örnekler

::: ornek Yatay eleman
$E=200\times10^6$, $A=0.001$, $L=2$, $\theta=0°$. Global $4\times4$ matrisi bul.
--- ipucu
$c=1$, $s=0$; yalnız $c^2$ terimleri kalır.
--- cevap
$EA/L=100\,000$. Matris yalnız $u_1$ ve $u_2$ satır ve sütunlarında doludur; $v$ satırları sıfırdır.
--- kod
mo.kafes_eleman("200e6", "0.001", 2, 0)
--- kontrol
r.deger[0, 0] == 100000 and r.deger[1, 1] == 0 and r.deger[0, 2] == -100000
--- yorum
Yatay çubuğun düşey rijitliği yoktur. Tek başına bir düğümü düşeyde tutamaz; bu yüzden kafeste her düğüme en az iki doğrultuda çubuk gelmelidir.
:::

::: ornek Düşey eleman
Aynı çubuk dik durursa ($\theta=90°$) matris nasıl olur?
--- ipucu
$c=0$, $s=1$.
--- cevap
Bu kez yalnız $v_1$ ve $v_2$ satırları doludur: $k_{22}=k_{44}=100\,000$, $k_{24}=-100\,000$.
--- kod
mo.kafes_eleman("200e6", "0.001", 2, 90)
--- kontrol
r.deger[1, 1] == 100000 and r.deger[0, 0] == 0 and r.deger[1, 3] == -100000
--- yorum
Yatay ve düşey matrisler aynı sayıları farklı yerlerde taşır. Dönüşüm matrisi sayıları yaratmaz, yalnız doğru konuma yerleştirir.
:::

::: ornek 30 derecelik birim eleman
$EA/L=1$ alarak $\theta=30°$ için matrisi yaz.
--- ipucu
$c=\sqrt3/2$, $s=1/2$; $c^2=3/4$, $s^2=1/4$, $cs=\sqrt3/4$.
--- cevap
$$
\mathbf{k}=\begin{bmatrix}3/4&\sqrt3/4&-3/4&-\sqrt3/4\\ \sqrt3/4&1/4&-\sqrt3/4&-1/4\\ -3/4&-\sqrt3/4&3/4&\sqrt3/4\\ -\sqrt3/4&-1/4&\sqrt3/4&1/4\end{bmatrix}
$$
--- kod
mo.kafes_eleman(1, 1, 1, 30)
--- kontrol
r.deger[0, 0] == sp.Rational(3, 4) and r.deger[0, 1] == sp.sqrt(3) / 4 and r.deger[1, 1] == sp.Rational(1, 4)
--- yorum
Köşegendeki $c^2+s^2=1$ olur: eleman her yönde toplam olarak aynı eksenel rijitliği paylaştırır.
:::

::: ornek 45 derece, simgesel
$E$, $A$, $L$ harf kalsın, $\theta=45°$. Hangi terimler eşit çıkar?
--- ipucu
$c=s=\sqrt2/2$, dolayısıyla $c^2=s^2=cs=1/2$.
--- cevap
Bütün terimlerin büyüklüğü $\dfrac{EA}{2L}$'dir; yalnız işaretleri değişir.
--- kod
mo.kafes_eleman("E", "A", "L", 45)
--- kontrol
sp.simplify(r.deger[0, 0] - r.deger[0, 1]) == 0 and sp.simplify(r.deger[0, 0] - r.deger[1, 1]) == 0
--- yorum
45° çapraz, yatay ve düşey yükü eşit paylaşır. Pratt ve Warren kafeslerinde çaprazların neden bu açıya yakın seçildiğini buradan sezebilirsin.
:::

::: ornek 3-4-5 üçgeninden eleman
Düğüm 1 $(0,0)$, düğüm 3 $(3,4)$. $E=200\times10^6$, $A=0.001$. Açıyı hiç hesaplamadan matrisi kur.
--- ipucu
$L=5$, $c=3/5$, $s=4/5$, $EA/L=40\,000$. $c^2=9/25$, $cs=12/25$, $s^2=16/25$.
--- cevap
$40\,000$ çarpanı içeri girince $c^2\to14\,400$, $cs\to19\,200$, $s^2\to25\,600$ olur.
--- kod
mo.skaler(40000, "9/25 12/25 -9/25 -12/25; 12/25 16/25 -12/25 -16/25; -9/25 -12/25 9/25 12/25; -12/25 -16/25 12/25 16/25")
--- kontrol
r.deger[0, 0] == 14400 and r.deger[0, 1] == 19200 and r.deger[1, 1] == 25600
--- yorum
$53.13°$ yazıp kosinüs almak yuvarlama hatası getirir. Koordinatlardan gelen $3/5$ ve $4/5$ tam sayıdır; sonlu eleman programları da hep böyle hesaplar.
:::

::: ornek İki çubuklu kafes
Hazır `kafes-iki-cubuk` modeli: düğümler $(0,0)$, $(6,0)$, $(3,4)$; tepeye $10$ kN aşağı yük. Tepe çökmesini ve çubuk kuvvetlerini bul.
--- ipucu
Simetriden $u_3=0$. Düşey rijitlik iki çubuğun $s^2$ katkısıdır: $2\cdot25\,600=51\,200$ kN/m.
--- cevap
$v_3=-10/51\,200=-1/5120$ m $\approx-0.195$ mm. İki çubuk da $N=-6.25$ kN basınç. Tepkiler her mesnette $5$ kN yukarı, $\pm3.75$ kN yatay.
--- kod
se.se_coz(se.ornek_model("kafes-iki-cubuk"))
--- kontrol
r.deger[5] == sp.Rational(-1, 5120) and abs(r.veri["elemanlar"][0]["N"] + 6.25) < 1e-9
--- yorum
Elle düğüm dengesi: $2N\cdot\frac45=-10$ ise $N=-6.25$. Rijitlik yöntemi aynı sonucu verir ve ek olarak yer değiştirmeyi de bulur.
:::

::: ornek Uzamayı T ile geri bulmak
Bir önceki örnekte eleman 1'in uç yer değiştirmeleri $[u_1,v_1,u_3,v_3]=[0,0,0,-1/5120]$. $\mathbf{T}$ ile yerel uç yer değiştirmelerini bul, sonra $N$'yi hesapla.
--- ipucu
$\mathbf{T}=\begin{bmatrix}3/5&4/5&0&0\\0&0&3/5&4/5\end{bmatrix}$.
--- cevap
$u'_1=0$, $u'_3=\frac45\cdot(-\frac1{5120})=-\frac1{6400}$ m. $\delta=-1/6400$, $N=40\,000\cdot(-1/6400)=-6.25$ kN (basınç).
--- kod
mo.carp("3/5 4/5 0 0; 0 0 3/5 4/5", "0; 0; 0; -1/5120")
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(-1, 6400)])
--- yorum
Bu adım her programın "eleman kuvvetleri" tablosunun arkasındaki hesaptır. Önce global $\mathbf{u}$, sonra $\mathbf{T}$, sonra $N$.
:::

::: ornek Sıfır çubuk
Pratt kafes köprüde (hazır model) orta düşey çubuk $N=0$ çıkıyor. Neden?
--- ipucu
Üst orta düğüme bak: yük yok, iki yatay başlık çubuğu ve bir düşey çubuk birleşiyor.
--- cevap
Düşey denge: düğümdeki tek düşey bileşen o çubuktan gelir ve yük yoktur, öyleyse $N=0$. Bu çubuk bu yük durumunda **sıfır çubuktur**.
--- yorum
Sıfır çubuk gereksiz demek değildir. Burkulma boyunu kısaltır, başka yük durumlarında çalışır ve montajda yapıyı tutar.
:::

::: muhendislik Kafes köprüler ve basınç çubukları
Demir ve çelik kafes köprülerde üst başlık basınç, alt başlık çekme çalışır. Basınç çubuklarında asıl tehlike çoğu zaman gerilme değil **burkulmadır**; bu yüzden program çıktısında basınç kuvvetini burkulma yüküyle ayrıca karşılaştırırsın.

Yığma kemerleri ön tasarımda basınç çubuklarından oluşan bir kafes gibi düşünmek (basınç çizgisi yaklaşımı) de yaygındır. Taşın çekme taşımadığı kabulü, modelde yalnız basınç çalışan çubuklara karşılık gelir.
:::

::: ozet Özet
- Yön kosinüsleri koordinatlardan: $c=\Delta x/L$, $s=\Delta y/L$.
- $\mathbf{T}=\begin{bmatrix}c&s&0&0\\0&0&c&s\end{bmatrix}$ global SD'leri eksen yönüne izdüşürür.
- $\mathbf{k}=\mathbf{T}^T\mathbf{k}'\mathbf{T}$; dört blok $\pm\frac{EA}{L}\begin{bmatrix}c^2&cs\\cs&s^2\end{bmatrix}$.
- Yön ters çevrilirse k değişmez.
- Eleman kuvveti: $N=\frac{EA}{L}[-c\ -s\ c\ s]\,\mathbf{u}_e$; pozitif çekme, negatif basınç.
:::

## Alıştırma

::: alistirma kafes-k
{"zorluk": 1}
:::

::: alistirma kafes-k
{"zorluk": 2}
:::
