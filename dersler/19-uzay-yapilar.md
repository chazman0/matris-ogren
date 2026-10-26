---
baslik: Uzay kafes ve uzay çerçeve: 3 boyutlu yapılar
bolum: se
ozet: Üç doğrultu kosinüsüyle uzay kafes çubuğu ve 6×6 matrisi, düğümde altı serbestlik ve 12×12 uzay çerçeve elemanı, yerel eksen kuralı ile λ, burulma, kiriş ızgarası ve altı iç kuvvet diyagramı.
sure: 55
---

## Neden?

İletim kulesi, stadyum çatısını taşıyan uzay kafes, köprü tabliyesinin altındaki kiriş ızgarası ya da köşe kolonlu bir bina düzleme sığmaz. Düzlem model üç durumda yetmez: yapı bir düzlemde değildir, yük yapının düzlemine diktir ya da elemanlar **burulur**. Reçete yine aynıdır: yerel matris, dönüşüm, birleştirme, sınır koşulu. Değişen yalnız düğümdeki SD sayısı ve dönüşüm matrisidir.

## Uzay kafes çubuğu

::: tanim Doğrultu kosinüsleri
**Uzay kafes** (space truss) düğümünde üç SD vardır: $u$, $v$, $w$. Düğüm $i$'den $j$'ye giden çubuğun uzunluğu $L=\sqrt{\Delta x^2+\Delta y^2+\Delta z^2}$, **doğrultu kosinüsleri** (direction cosines) $\ka{c_x}=\Delta x/L$, $\kb{c_y}=\Delta y/L$, $\kc{c_z}=\Delta z/L$'dir ve $c_x^2+c_y^2+c_z^2=1$ sağlanır.
:::

Çubuğun uzaması yine yalnız eksen yönündeki hareketten gelir. Üç bileşenli hareketi eksene izdüşürmek için $\bar u=\ka{c_x}u+\kb{c_y}v+\kc{c_z}w$ yazılır; 13. dersteki $c$, $s$ çiftinin yerini üç kosinüs alır ve $\mathbf{T}$ $2\times6$ olur.

$$
\begin{bmatrix}\bar u_1\\ \bar u_2\end{bmatrix}=
\underbrace{\begin{bmatrix}\ka{c_x}&\kb{c_y}&\kc{c_z}&0&0&0\\0&0&0&\ka{c_x}&\kb{c_y}&\kc{c_z}\end{bmatrix}}_{\mathbf{T}\ (2\times6)}
\begin{bmatrix}u_1\\v_1\\w_1\\u_2\\v_2\\w_2\end{bmatrix}
$$

Yerel matris $\frac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$ değişmez; global matris $\mathbf{T}^T\mathbf{k}'\mathbf{T}$ ile $6\times6$ olur ve dört $3\times3$ bloktan kurulur.

$$
\mathbf{k}=\kutua{\frac{EA}{L}}\begin{bmatrix}\mathbf{B}&-\mathbf{B}\\-\mathbf{B}&\mathbf{B}\end{bmatrix},\qquad
\mathbf{B}=\mathbf{c}\,\mathbf{c}^T=
\begin{bmatrix}\ka{c_x^2}&c_xc_y&c_xc_z\\ c_xc_y&\kb{c_y^2}&c_yc_z\\ c_xc_z&c_yc_z&\kc{c_z^2}\end{bmatrix}
$$

::: not B'nin rankı 1'dir
$\mathbf{B}=\mathbf{c}\mathbf{c}^T$ yalnız $\mathbf{c}$ doğrultusunda direnç üretir; $\mathbf{c}$'ye dik her harekete sıfır kuvvet verir. Bu yüzden uzayda bir düğümü tutmak için ona en az üç bağımsız doğrultuda çubuk gelmelidir. Düzlem kafes $c_z=0$ özel halidir: 13. dersin $c^2$, $cs$, $s^2$ deseni geri gelir.
:::

Aşağıda çubuğun yatay açısını $\varphi$ ve düşey açısını $\psi$ değiştir; hücre tonu $|c_xc_y|$ gibi çarpımın büyüklüğünü gösterir.

::: etkilesim uzay-kafes-cubuk
{"E": 200000000, "A": 0.001, "L": 5, "fi": 35, "psi": 30}
:::

Çubuk kuvveti düzlemdekiyle aynı mantıkla geri bulunur: $N=\frac{EA}{L}(\bar u_2-\bar u_1)=\frac{EA}{L}\begin{bmatrix}-c_x&-c_y&-c_z&c_x&c_y&c_z\end{bmatrix}\mathbf{u}_e$, çekme pozitif.

## Düğüm dengesiyle uzay kafes

Statikçe belirli bir uzay kafeste düğüm dengesi üç denklem verir. Düğüme bağlı $k$ çubuğunun mesnetten düğüme bakan birim vektörü $\mathbf{e}_k$ ise, çekme çubuğu düğümü mesnede doğru çeker; dış yük $\mathbf{F}$ ile denge $\sum_k N_k\,\mathbf{e}_k=\mathbf{F}$ olur. Sayma kuralı: $m$ çubuk ve $r$ tutulu bileşen için $m+r=3j$ ise yapı statikçe belirlidir; fazlası hiperstatikliktir.

## Uzay çerçeve elemanı

::: tanim Altı serbestlik
**Uzay çerçeve** (space frame) düğümünde üç öteleme ve üç dönme vardır: $[\,u,\ v,\ w,\ \theta_x,\ \theta_y,\ \theta_z\,]$. Karşılıkları eksenel kuvvet $N$, iki kesme $V_y$, $V_z$, burulma momenti $T$ ve iki eğilme momenti $M_y$, $M_z$'dir. Eleman özellikleri $E$, $G$, $A$, $I_y$, $I_z$, $J$'dir; $G$ kayma modülü, $J$ **burulma sabitidir** (torsion constant).
:::

Yerel $12\times12$ matris dört bağımsız parçanın üst üste konmasıdır: eksenel $\ka{a}=EA/L$, burulma $\ksil{t}=GJ/L$, $x'y'$ düzleminde eğilme (16. dersin $4\times4$ kiriş bloğu, $I_z$ ile) ve $x'z'$ düzleminde eğilme ($I_y$ ile). Kısaltmalar: $\kb{z_1}=\frac{12EI_z}{L^3}$, $\kb{z_2}=\frac{6EI_z}{L^2}$, $\kb{z_3}=\frac{4EI_z}{L}$, $\kb{z_4}=\frac{2EI_z}{L}$ ve aynı biçimde $\kc{y_1}\ldots\kc{y_4}$, $I_y$ ile.

$$
\mathbf{k}'=\left[\begin{array}{cccccc|cccccc}
\ka{a}&0&0&0&0&0&\ka{-a}&0&0&0&0&0\\
0&\kb{z_1}&0&0&0&\kb{z_2}&0&\kb{-z_1}&0&0&0&\kb{z_2}\\
0&0&\kc{y_1}&0&\kc{-y_2}&0&0&0&\kc{-y_1}&0&\kc{-y_2}&0\\
0&0&0&\ksil{t}&0&0&0&0&0&\ksil{-t}&0&0\\
0&0&\kc{-y_2}&0&\kc{y_3}&0&0&0&\kc{y_2}&0&\kc{y_4}&0\\
0&\kb{z_2}&0&0&0&\kb{z_3}&0&\kb{-z_2}&0&0&0&\kb{z_4}\\ \hline
\ka{-a}&0&0&0&0&0&\ka{a}&0&0&0&0&0\\
0&\kb{-z_1}&0&0&0&\kb{-z_2}&0&\kb{z_1}&0&0&0&\kb{-z_2}\\
0&0&\kc{-y_1}&0&\kc{y_2}&0&0&0&\kc{y_1}&0&\kc{y_2}&0\\
0&0&0&\ksil{-t}&0&0&0&0&0&\ksil{t}&0&0\\
0&0&\kc{-y_2}&0&\kc{y_4}&0&0&0&\kc{y_2}&0&\kc{y_3}&0\\
0&\kb{z_2}&0&0&0&\kb{z_4}&0&\kb{-z_2}&0&0&0&\kb{z_3}
\end{array}\right]
\quad
\begin{matrix}u_1\\v_1\\w_1\\\theta_{x1}\\\theta_{y1}\\\theta_{z1}\\u_2\\v_2\\w_2\\\theta_{x2}\\\theta_{y2}\\\theta_{z2}\end{matrix}
$$

Mavi eksenel, kırmızı burulma, turuncu $x'y'$ eğilmesi, yeşil $x'z'$ eğilmesidir. SD sırasını $[u_1,u_2\,|\,\theta_{x1},\theta_{x2}\,|\,v_1,\theta_{z1},v_2,\theta_{z2}\,|\,w_1,\theta_{y1},w_2,\theta_{y2}]$ diye yeniden dizsen matris dört ayrı bloğa düşer: yerel eksende bu dört etki birbirinden bağımsızdır.

Yeşil blokta $6L$ terimlerinin işareti turuncu bloğun tersidir. Sebep sağ el kuralıdır: $y$ ekseni etrafında pozitif dönme $+x$ tarafını $-z$'ye götürür, yani $\theta_y=-\,dw/dx$ iken $\theta_z=+\,dv/dx$'tir.

$$
\mathbf{k}_{x'z'}=\frac{EI_y}{L^3}
\begin{bmatrix}12&\ksil{-6L}&-12&\ksil{-6L}\\ \ksil{-6L}&4L^2&\ksil{6L}&2L^2\\ -12&\ksil{6L}&12&\ksil{6L}\\ \ksil{-6L}&2L^2&\ksil{6L}&4L^2\end{bmatrix}
\qquad [\,w_1,\ \theta_{y1},\ w_2,\ \theta_{y2}\,]
$$

## Yerel eksen kuralı ve λ

Düzlemde eleman açısı tek sayıydı. Uzayda $x'$ eksenini bilmek yetmez; $y'$ ve $z'$'nin eleman çevresinde nasıl döndüğü de seçilmelidir, çünkü $I_y$ ve $I_z$ bu eksenlere bağlıdır.

::: tanim Yerel eksen kuralı (Kassimali)
$x'$ eleman boyunca $i\to j$ yönündedir. $y'$, elemanı içeren **düşey düzlemde** yer alır ve yukarı bakar. $z'=x'\times y'$ yataydır. Düşey elemanda düşey düzlem belirsiz kalır; bu durumda $z'=Z$ alınır. Yukarı giden bir kolonda $y'=-X$ çıkar.
:::

::: sekil Yerel eksenler: eğik eleman ve düşey kolon
<svg viewBox="0 0 400 250" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<path d="M100 150L177 197.2L177 115.6Z" fill="var(--sema-b-bg,rgba(245,158,11,.12))" stroke="none"/>
<path d="M100 150L135.4 158.3" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/><polyline points="131,154.3 135.4,158.3 129.7,159.9" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<text x="143.4" y="162.3" fill="var(--sema-cizgi,#94a3b8)">X</text>
<path d="M100 150L100 111.2" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/><polyline points="97.1,116.5 100,111.2 102.9,116.5" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<text x="96" y="103.2" fill="var(--sema-cizgi,#94a3b8)">Y</text>
<path d="M100 150L77.8 163.3" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/><polyline points="83.8,163 77.8,163.3 80.9,158.1" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<text x="65.8" y="169.3" fill="var(--sema-cizgi,#94a3b8)">Z</text>
<path d="M100 150L177 197.2L177 115.6" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="4 3" fill="none"/>
<path d="M100 150L177 115.6" stroke="currentColor" stroke-width="5" stroke-linecap="round" fill="none"/>
<circle cx="100" cy="150" r="5" fill="var(--sema-a,#3b82f6)"/><circle cx="177" cy="115.6" r="5" fill="var(--sema-a,#3b82f6)"/>
<text x="88" y="146">i</text><text x="183" y="131.6">j</text>
<path class="ok" pathLength="1" d="M177 115.6L195.8 107.2" stroke="var(--sema-a,#3b82f6)" stroke-width="2.2" fill="none"/><polyline class="ok-uc" points="188.8,106.6 195.8,107.2 191.5,112.7" stroke="var(--sema-a,#3b82f6)" stroke-width="2.2" fill="none"/>
<text x="201.8" y="105.2" fill="var(--sema-a,#3b82f6)" font-weight="700">x′</text>
<path class="ok" pathLength="1" d="M177 115.6L165.7 75.3" stroke="var(--sema-b,#f59e0b)" stroke-width="2.2" fill="none"/><polyline class="ok-uc" points="164.2,82.1 165.7,75.3 170.6,80.3" stroke="var(--sema-b,#f59e0b)" stroke-width="2.2" fill="none"/>
<text x="151.7" y="71.3" fill="var(--sema-b,#f59e0b)" font-weight="700">y′</text>
<path class="ok" pathLength="1" d="M177 115.6L141.1 123.8" stroke="var(--sema-c,#10b981)" stroke-width="2.2" fill="none"/><polyline class="ok-uc" points="147.9,125.7 141.1,123.8 146.4,119.1" stroke="var(--sema-c,#10b981)" stroke-width="2.2" fill="none"/>
<text x="125.1" y="133.8" fill="var(--sema-c,#10b981)" font-weight="700">z′</text>
<text x="183" y="203.2" fill="var(--sema-b,#f59e0b)" font-size="11">düşey düzlem</text>
<text x="12" y="226" font-size="11">Eğik eleman: y′ elemanı içeren düşey düzlemde yukarı, z′ = x′ × y′ yatay.</text>
<path d="M300 190L327.5 196.4" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/><polyline points="323,192.4 327.5,196.4 321.7,198" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<text x="335.5" y="200.4" fill="var(--sema-cizgi,#94a3b8)">X</text>
<path d="M300 190L282.8 200.3" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/><polyline points="288.8,200.1 282.8,200.3 285.9,195.1" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<text x="270.8" y="206.3" fill="var(--sema-cizgi,#94a3b8)">Z</text>
<path d="M300 190L300 89.9" stroke="currentColor" stroke-width="5" stroke-linecap="round" fill="none"/>
<circle cx="300" cy="190" r="5" fill="var(--sema-a,#3b82f6)"/><circle cx="300" cy="89.9" r="5" fill="var(--sema-a,#3b82f6)"/>
<text x="308" y="194">i</text><text x="308" y="83.9">j</text>
<path class="ok" pathLength="1" d="M300 136.6L300 99.5" stroke="var(--sema-a,#3b82f6)" stroke-width="2.2" fill="none"/><polyline class="ok-uc" points="296.6,105.6 300,99.5 303.4,105.6" stroke="var(--sema-a,#3b82f6)" stroke-width="2.2" fill="none"/>
<text x="308" y="99.5" fill="var(--sema-a,#3b82f6)" font-weight="700">x′ = Y</text>
<path class="ok" pathLength="1" d="M300 136.6L266.1 128.7" stroke="var(--sema-b,#f59e0b)" stroke-width="2.2" fill="none"/><polyline class="ok-uc" points="271.3,133.3 266.1,128.7 272.8,126.8" stroke="var(--sema-b,#f59e0b)" stroke-width="2.2" fill="none"/>
<text x="220.1" y="122.7" fill="var(--sema-b,#f59e0b)" font-weight="700">y′ = −X</text>
<path class="ok" pathLength="1" d="M300 136.6L278.8 149.3" stroke="var(--sema-c,#10b981)" stroke-width="2.2" fill="none"/><polyline class="ok-uc" points="285.8,149 278.8,149.3 282.3,143.3" stroke="var(--sema-c,#10b981)" stroke-width="2.2" fill="none"/>
<text x="258.8" y="161.3" fill="var(--sema-c,#10b981)" font-weight="700">z′ = Z</text>
<text x="12" y="242" font-size="11">Düşey kolon: düşey düzlem belirsiz, Kassimali kuralıyla z′ = Z ve y′ = −X.</text>
</svg>
:::

Kuralın matris hali $\boldsymbol\lambda$'dır: satırları $x'$, $y'$, $z'$ birim vektörlerinin global bileşenleridir. $D=\sqrt{c_x^2+c_z^2}$ elemanın yatay izdüşümünün uzunluğudur.

$$
\boldsymbol\lambda=
\begin{bmatrix}\ka{c_x}&\ka{c_y}&\ka{c_z}\\[2pt] \kb{-\dfrac{c_xc_y}{D}}&\kb{D}&\kb{-\dfrac{c_yc_z}{D}}\\[6pt] \kc{-\dfrac{c_z}{D}}&\kc{0}&\kc{\dfrac{c_x}{D}}\end{bmatrix},
\qquad
\boldsymbol\lambda_{\text{düşey}}=\begin{bmatrix}0&c_y&0\\-c_y&0&0\\0&0&1\end{bmatrix},
\qquad
\mathbf{T}=\operatorname{diag}(\boldsymbol\lambda,\boldsymbol\lambda,\boldsymbol\lambda,\boldsymbol\lambda),
\quad
\mathbf{k}=\mathbf{T}^T\mathbf{k}'\mathbf{T}
$$

$XY$ düzleminde soldan sağa tanımlı bir elemanda $c_z=0$, $D=c_x$ olur ve $\boldsymbol\lambda$ tam olarak 17. dersin $[c\ s\ 0;\ -s\ c\ 0;\ 0\ 0\ 1]$ matrisine iner. Uzay çerçeve, düzlem çerçeveyi içinde taşır.

::: etkilesim uzay-cerceve-k
{"E": 200000000, "G": 80000000, "A": 0.01, "Iy": 0.0001, "Iz": 0.0002, "J": 0.0002, "L": 4, "fi": 30, "psi": 20}
:::

Yayılı yük iki yerel yönde verilir: $q$ yerel $y'$, $q_z$ yerel $z'$ yönündedir. $q$'nun eşdeğer düğüm yükleri 16. dersteki gibidir; $q_z$ için kuvvetler $q_zL/2$, momentler ise $\theta_y$ yüzünden ters işaretlidir: $m_{y,i}=-q_zL^2/12$, $m_{y,j}=+q_zL^2/12$.

| İç kuvvet | Yerel yön | İşaret |
|---|---|---|
| $N$ | $x'$ | çekme $+$ |
| $V_y$ ($=V$), $V_z$ | $y'$, $z'$ | 16. dersteki kesme kuralı |
| $M_z$ ($=M$) | $z'$ etrafında | $-y'$ lifi çekmede $+$, çekilen lif tarafına çizilir |
| $M_y$ | $y'$ etrafında | $-z'$ lifi çekmede $+$ |
| $T$ | $x'$ etrafında | eleman boyunca sabit, $T=-m_{x,i}$ |

## Kiriş ızgarası

**Kiriş ızgarası** (grillage), yatay bir düzlemde kesişen ve düzleme dik yük taşıyan kirişlerdir: köprü tabliyeleri, kirişli döşemeler. Uzay çerçevenin özel halidir: yalnız $v$, $\theta_x$ ve $\theta_z$ çalışır; $u$, $w$ ve $\theta_y$ sıfır kalır. Bir kiriş eğilirken ona dik komşusunu burar; bu yüzden ızgarada $GJ$ olmadan çözüm yoktur.

::: hata Burulmayı unutmak: J = 0
Izgarada ya da L konsolda $J=0$ yazarsan bazı $\theta_x$ serbestliklerine hiç rijitlik gelmez, $\mathbf{K}_{ff}$ tekil olur ve program mekanizma uyarısı verir. $J$ dairesel kesitte kutupsal atalet momentidir; dikdörtgen ve I kesitte çok daha küçüktür ve tablodan alınır; $I_y+I_z$ yazmak büyük hatadır.
:::

::: hata I_y ile I_z'yi karıştırmak
Düşey yük kirişi $z'$ ekseni etrafında eğer; çalışan atalet momenti $I_z$'dir. Dikine duran $30\times50$ kirişte $I_z=0.3\cdot0.5^3/12=3.125\times10^{-3}$ güçlü eksen, $I_y=0.5\cdot0.3^3/12=1.125\times10^{-3}$ zayıf eksendir. $y'$ eksenini keyfi almak, $\theta_y$ işaretini çevirmemek ya da iki ataleti yer değiştirmek, sehimi üç kata kadar yanlış verir.
:::

## Çözümlü örnekler

::: ornek Tripod: düğüm dengesiyle çubuk kuvvetleri
Hazır `kafes3b-tripod`: mesnetler $(4,0,0)$, $(0,0,4)$, $(-4,0,0)$; tepe $(0,3,0)$; her çubuk $5$ m, $E=200\times10^6$, $A=0.001$. Tepeye $\mathbf{F}=(10,-30,5)$ kN. Üç çubuk kuvvetini elle bul, programla doğrula.
--- ipucu
Mesnetten tepeye birim vektörler: $\mathbf{e}_1=(-0.8,0.6,0)$, $\mathbf{e}_2=(0,0.6,-0.8)$, $\mathbf{e}_3=(0.8,0.6,0)$. Denge: $\sum N_k\mathbf{e}_k=\mathbf{F}$.
--- cevap
$$
\begin{aligned}
x:&\quad -0.8\,\ka{N_1}+0.8\,\kc{N_3}=10\\
y:&\quad 0.6\,(\ka{N_1}+\kb{N_2}+\kc{N_3})=-30\\
z:&\quad -0.8\,\kb{N_2}=5\ \xrightarrow{\ }\ \kutub{N_2=-\tfrac{25}{4}}
\end{aligned}
$$
$N_1+N_3=-\tfrac{175}{4}$ ve $N_3-N_1=\tfrac{25}{2}$ birlikte $\kutua{N_1=-\tfrac{225}{8}}$, $\kutuc{N_3=-\tfrac{125}{8}}$ verir; üçü de basınç.
--- kod
se.se_coz(se.ornek_model("kafes3b-tripod"))
--- kontrol
r.veri["elemanlar"][0]["N"] == -28.125 and r.veri["elemanlar"][1]["N"] == -6.25 and r.veri["elemanlar"][2]["N"] == -15.625 and r.deger[9] == sp.Rational(1, 5120)
--- yorum
$12$ SD'li model kesin modda çözülür: $-225/8$ kesri olduğu gibi çıkar. Denge yöntemi kuvvetleri verir; rijitlik yöntemi aynı kuvvetlerin yanında tepe yer değiştirmesini de verir.
:::

::: ornek Bir uzay kafes çubuğunun 6×6 matrisi
Çubuk $(0,0,0)$'dan $(2,1,2)$'ye gidiyor; $E=200\times10^6$, $A=0.00135$ m². Global matrisi $\mathbf{T}^T\mathbf{k}'\mathbf{T}$ ile kur.
--- ipucu
$L=3$, $\mathbf{c}=(\tfrac23,\tfrac13,\tfrac23)$, $EA/L=90\,000$. $\mathbf{B}$'nin elemanları $\tfrac49,\tfrac29,\tfrac19$'dur.
--- cevap
$$
\mathbf{B}\cdot90\,000=\begin{bmatrix}\kutua{40\,000}&20\,000&40\,000\\20\,000&\kutub{10\,000}&20\,000\\40\,000&20\,000&\kutuc{40\,000}\end{bmatrix},
\qquad
\mathbf{k}=\begin{bmatrix}\mathbf{B}&-\mathbf{B}\\-\mathbf{B}&\mathbf{B}\end{bmatrix}\cdot90\,000
$$
--- kod
T = "2/3 1/3 2/3 0 0 0; 0 0 0 2/3 1/3 2/3"
k = "90000 -90000; -90000 90000"
mo.carp(mo.transpoz(T).deger, k, T)
--- kontrol
r.deger[0, 0] == 40000 and r.deger[0, 1] == 20000 and r.deger[1, 1] == 10000 and r.deger[0, 3] == -40000 and r.deger[2, 5] == -40000
--- yorum
Köşegende $c_x^2+c_y^2+c_z^2=1$ olduğundan $40\,000+10\,000+40\,000=90\,000=EA/L$: çubuk toplam rijitliğini üç eksene paylaştırır.
:::

::: ornek Tripodun tepe yer değiştirmesi: elle K_ff
Tripodda yalnız tepe düğümü serbesttir. Üç çubuğun $\mathbf{B}$ bloklarını topla, $3\times3$ sistemi çöz.
--- ipucu
$EA/L=40\,000$. $\mathbf{K}_{ff}=40\,000\,(\mathbf{c}_1\mathbf{c}_1^T+\mathbf{c}_2\mathbf{c}_2^T+\mathbf{c}_3\mathbf{c}_3^T)$; $c_x c_y$ terimleri birbirini götürür.
--- cevap
$$
\left[\begin{array}{ccc|c}\kutua{51\,200}&0&0&10\\0&\kutub{43\,200}&-19\,200&-30\\0&-19\,200&\kutuc{25\,600}&5\end{array}\right]
\ \Rightarrow\
u_4=\tfrac{1}{5120},\quad v_4=-\tfrac{7}{7680},\quad w_4=-\tfrac{1}{2048}\ \text{m}
$$
--- kod
mo.coz("51200 0 0; 0 43200 -19200; 0 -19200 25600", "10; -30; 5")
--- kontrol
r.deger == sp.Matrix([sp.Rational(1, 5120), sp.Rational(-7, 7680), sp.Rational(-1, 2048)])
--- yorum
$x$ yönü ayrışır çünkü $x$'e yatkın iki çubuk simetriktir; $y$ ve $z$ ise 2. çubuk yüzünden birbirine bağlıdır. Programın 1. örnekteki $\mathbf{u}$ değerleri tam olarak bunlardır.
:::

::: ornek Düşey kolonun λ'sı
$(0,0,0)$'dan $(0,3,0)$'a giden kolonda $\boldsymbol\lambda$ nedir? Kolonu yukarıdan aşağı tanımlarsan ne değişir?
--- ipucu
$c_y=1$, $D=0$: düşey hal.
--- cevap
$\boldsymbol\lambda=\begin{bmatrix}0&\ka{1}&0\\ \kb{-1}&0&0\\0&0&\kc{1}\end{bmatrix}$: $x'=Y$, $y'=-X$, $z'=Z$. Tersine tanımda $c_y=-1$: $x'=-Y$, $y'=+X$, $z'$ yine $Z$.
--- yorum
İki tanımda da $z'=Z$ olduğundan $I_z$ hep $Z$ ekseni etrafındaki eğilmeye karşılık gelir; kolonun güçlü eksenini $XY$ düzleminde kullanmak istiyorsan $I_z$ oraya yazılır.
:::

::: ornek L biçimli konsol: eğilme + burulma
Hazır `cerceve3b-konsol-L`: $3$ m'lik kol $x$ yönünde ankastre, ucundan $2$ m'lik ikinci kol $z$ yönünde; uca $10$ kN aşağı. $EI=2\times10^4$, $GJ=1.6\times10^4$. Uç çökmesini kapalı formla bul.
--- ipucu
İkinci kol eğilir; birinci kol hem eğilir hem $T=PL_2=20$ kN·m ile burulur. Burulma dönmesi $\theta=TL_1/GJ$ ikinci kolun ucunu $\theta L_2$ kadar indirir.
--- cevap
$$
v_3=-\Big(\underbrace{\ka{\tfrac{PL_2^3}{3EI}}}_{0.00133}+\underbrace{\kb{\tfrac{PL_1^3}{3EI}}}_{0.0045}+\underbrace{\kc{\tfrac{PL_2^2L_1}{GJ}}}_{0.0075}\Big)=\kutuc{-0.01333\ \text{m}}
$$
Tepkiler: $F_y=10$, $M_z=30$, $M_x=-20$ kN·m.
--- kod
se.se_coz(se.ornek_model("cerceve3b-konsol-L"))
--- kontrol
abs(r.veri["dugumler"][2]["u"][1] + 10 * 8 / 60000 + 10 * 27 / 60000 + 10 * 4 * 3 / 16000) < 1e-9 and abs(abs(r.veri["elemanlar"][0]["diyagram"]["T"][0]) - 20) < 1e-6 and abs(r.veri["tepkiler"][0]["Fy"] - 10) < 1e-6
--- yorum
Çökmenin yarısından çoğu burulmadan gelir. Düzlem çerçeve bu üç terimden yalnız ikincisini görürdü; $GJ$'yi ihmal etmek sehimi yarıdan az gösterir.
:::

::: ornek 2B ile 3B aynı sonucu verir
Hazır `cerceve-portal`'ı $z=0$ düzleminde uzay çerçeveye çevir: $G$, $I_y$, $J$ ekle, $I_z=I$ al, tabanları altı SD'den tut. Düzlem SD'leri karşılaştır.
--- ipucu
3B düğümünün $u$, $v$, $\theta_z$ bileşenleri 2B'nin $u$, $v$, $\theta$'sıdır: indeksler $6i+0$, $6i+1$, $6i+5$ ile $3i+0$, $3i+1$, $3i+2$.
--- cevap
$u_2=0.003588$ m, $v_2=-0.0000482$ m, $\theta_{z2}=-0.001354$ rad iki modelde de aynı; $w$, $\theta_x$, $\theta_y$ sıfır. Tepkiler $M_1=13.37$, $M_4=31.11$ kN·m değişmez.
--- kod
m2 = se.ornek_model("cerceve-portal")
m3 = {"tip": "cerceve3b", "dugumler": [dict(d, z=0) for d in m2["dugumler"]], "elemanlar": [dict(e, G="80e6", Iy="5e-4", Iz=e["I"], J="7e-4") for e in m2["elemanlar"]], "mesnetler": [{"dugum": s["dugum"], "ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True} for s in m2["mesnetler"]], "yukler": m2["yukler"], "yayili": m2["yayili"]}
se.se_coz(m2), se.se_coz(m3)
--- kontrol
all(abs(float(r[0].deger[3 * i + k]) - float(r[1].deger[6 * i + [0, 1, 5][k]])) < 1e-9 for i in range(4) for k in range(3))
--- yorum
Yerel eksen kuralı tutarlı olduğu için $I_y$, $J$ ne olursa olsun düzlem sonuç değişmez. Düzlem dışı serbestlikler yük almadığı için sıfır kalır: 3B program, 2B programı içinde barındırır.
:::

::: ornek Kiriş ızgarası
Hazır `cerceve3b-izgara`: $6\times6$ m, $3$ m aralıklı $30\times50$ betonarme kirişler, dört köşe mafsallı; ortaya $40$, kenar ortalarına $20$ kN. Tepkileri ve en büyük çökmeyi bul.
--- ipucu
Toplam yük $120$ kN ve yapı iki yönde simetrik: dört tepki eşittir.
--- cevap
$R=\kutuc{30}$ kN (dört köşe). $v_5=-2.47$ mm ortada en büyük; kenar ortaları $v_2=v_4=v_6=v_8=-1.37$ mm. Kenar kirişinde $M\approx43.6$, orta kirişte $M\approx32.7$ kN·m; köşe kirişleri $T=\pm1.36$ kN·m burulur.
--- kod
se.se_coz(se.ornek_model("cerceve3b-izgara"))
--- kontrol
all(abs(t["Fy"] - 30) < 1e-6 for t in r.veri["tepkiler"]) and r.veri["dugumler"][4]["u"][1] < r.veri["dugumler"][1]["u"][1] < 0 and abs(r.veri["dugumler"][4]["u"][0]) < 1e-9
--- yorum
$54$ SD'li modelde $u$, $w$, $\theta_y$ bütün düğümlerde sıfırdır: ızgara, uzay çerçevenin yalnız üç serbestliğini kullanır. Köprü tabliyesini ızgara olarak modellemek, yükün kirişler arasında nasıl paylaşıldığını gösterir.
:::

::: ornek Kafes kule: SD sayısı ve hiperstatiklik
Hazır `kafes3b-kule`: $8$ düğüm, $13$ çubuk, dört tabanı küresel mafsallı. Toplam SD, serbest SD ve statik belirsizlik derecesi nedir?
--- ipucu
Düğüm başına $3$ SD; her mafsallı mesnet $3$ bileşen tutar. $m+r-3j$.
--- cevap
$8\times3=\kutua{24}$ SD; $4\times3=12$ tutulu, $\kutub{12}$ serbest. $m+r-3j=13+12-24=\kutuc{1}$: bir kez hiperstatik; fazla olan, tepe düzlemindeki çapraz çubuktur.
--- yorum
$24>12$ olduğu için program sayısal modda çözer. Rüzgâr $+x$ yönünde itince $x=-1$ tarafındaki ayaklar daha az basınç alır; sonuçta $\sum R_y=80$ ve $\sum R_x=-20$ kN çıkar.
:::

::: ornek Uzay portal: altı bileşenli denge
Hazır `cerceve3b-portal`: $5\times4$ m planlı, $3$ m yüksek kutu çerçeve; $x$ kirişlerinde $q=-10$ kN/m, iki köşede $15$ kN yatay, bir köşede $z$ yönünde $-10$ kN. Tepki toplamlarını denetle.
--- ipucu
$\sum F_x=-30$, $\sum F_y=2\cdot10\cdot5=100$, $\sum F_z=10$ kN.
--- cevap
$\sum R_x=\kutua{-30}$, $\sum R_y=\kutub{100}$, $\sum R_z=\kutuc{10}$ kN. Kolon 1'de $N=-21.7$ kN; kiriş 5'te $|M_z|_{max}=23.3$, $|M_y|_{max}=0.89$ kN·m ve küçük bir burulma $T=-0.2$ kN·m.
--- kod
se.se_coz(se.ornek_model("cerceve3b-portal"))
--- kontrol
abs(sum(t["Fx"] for t in r.veri["tepkiler"]) + 30) < 1e-6 and abs(sum(t["Fy"] for t in r.veri["tepkiler"]) - 100) < 1e-6 and abs(sum(t["Fz"] for t in r.veri["tepkiler"]) - 10) < 1e-6
--- yorum
$z$ yönündeki tek yük, $x$ kirişlerini yatay düzlemde eğer: $M_y$ ve $V_z$ sıfırdan ayrılır. Altı iç kuvvetin aynı anda çalıştığı ilk modelin budur; tasarımda her kesit $N$, $M_y$, $M_z$ üçlüsüyle birlikte denetlenir.
:::

::: muhendislik Kuleler, uzay kafes çatılar ve tarihi köprü
İletim kulesi ve stadyum çatısı gibi uzay kafeslerde yüzlerce düğüm, binlerce SD vardır; her çubuk yine $6\times6$'lık aynı matristir. Basınç çubuklarında burkulma, çekme çubuklarında bağlantı tasarımı program çıktısının hemen ardından gelir.

Tarihi yığma köprüde ayaklar ve kemer halkası $XY$ düzleminde kalır; ama yanal rüzgâr, deprem ya da dış merkezli araç yükü kemeri $z$ yönünde eğer ve ayakları burar. Bu etkiler yalnız uzay çerçeve modelinde görünür. OMA ile ölçülen yanal ve burulma modları da ancak 3B modelle karşılaştırılabilir; düzlem model o modları hiç üretmez.
:::

::: ozet Özet
- Uzay kafes: $3$ SD/düğüm, $\mathbf{c}=(c_x,c_y,c_z)$, $\mathbf{k}=\frac{EA}{L}\begin{bmatrix}\mathbf{B}&-\mathbf{B}\\-\mathbf{B}&\mathbf{B}\end{bmatrix}$, $\mathbf{B}=\mathbf{c}\mathbf{c}^T$.
- Düğüm dengesi: $\sum N_k\mathbf{e}_k=\mathbf{F}$; $m+r=3j$ statikçe belirli.
- Uzay çerçeve: $6$ SD/düğüm; $12\times12$ yerel matris dört bağımsız blok: $EA/L$, $GJ/L$, $EI_z$, $EI_y$.
- $x'z'$ bloğunda $6L$ terimleri ters işaretli: $\theta_y=-dw/dx$.
- Yerel eksen kuralı: $y'$ düşey düzlemde yukarı, $z'=x'\times y'$; düşey elemanda $z'=Z$, yukarı kolonda $y'=-X$.
- $\mathbf{T}=\operatorname{diag}(\boldsymbol\lambda\times4)$; $q$ yerel $y'$, $q_z$ yerel $z'$; altı diyagram $N$, $V_y$, $V_z$, $T$, $M_y$, $M_z$.
- Izgara: yalnız $v$, $\theta_x$, $\theta_z$ çalışır; $GJ$ şarttır.
:::

## Alıştırma

Uzay elemanın dönüşümü düzlemdekiyle aynı fikirdir; önce düzlem kafes matrisini, sonra birleştirmeyi pekiştir.

::: alistirma kafes-k
{"zorluk": 2}
:::

::: alistirma birlestir
{"zorluk": 2}
:::
