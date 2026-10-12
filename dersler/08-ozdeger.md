---
baslik: Özdeğer ve özvektör
bolum: matris
ozet: Yönü değişmeyen vektörler; karakteristik denklem, doğal frekanslar ve mod şekilleri.
sure: 40
---

## Neden?

Bir köprüye çekiçle vurduğunda köprü rastgele değil, belirli **şekillerde** ve belirli **frekanslarda** titreşir. Bu şekiller mod şekilleri, frekanslar da doğal frekanslardır. Matematikte ikisi aynı problemin cevabıdır: $K\boldsymbol\phi=\omega^2M\boldsymbol\phi$. Tezindeki OMA ölçümleri de tam olarak bu sayıları ölçer.

## Yönü değişmeyen vektörler

Bir matris çoğu vektörü hem uzatır hem **döndürür**. Ama bazı özel vektörler vardır: matris onları yalnızca uzatır ya da kısaltır, yönlerini değiştirmez.

::: tanim Özdeğer ve özvektör
$A\mathbf{v}=\lambda\mathbf{v}$ eşitliğini sağlayan sıfırdan farklı $\mathbf{v}$ vektörüne **özvektör** (eigenvector), $\lambda$ sayısına da **özdeğer** (eigenvalue) denir. $\lambda$, özvektörün kaç kat uzadığını söyler.
:::

::: sekil Sıradan vektör ve özvektör
<svg viewBox="0 0 380 160" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<g stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1" fill="none">
<path d="M20 130 H170 M40 145 V15"/>
<path d="M210 130 H370 M230 145 V15"/>
</g>
<path d="M40 130 L85 130" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="3"/>
<path class="ok" pathLength="1" d="M40 130 L130 85" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="3"/>
<polyline class="ok-uc" points="120,84 130,85 124,94" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="3"/>
<path d="M95 128 A 55 55 0 0 0 90 106" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="3 3"/>
<text x="70" y="148" text-anchor="middle">v</text>
<text x="140" y="80" fill="var(--sema-b,#f59e0b)">Av</text>
<text x="95" y="30" text-anchor="middle">yön değişti</text>
<path class="ok" pathLength="1" d="M230 130 L335 25" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="5" opacity=".55"/>
<polyline class="ok-uc" points="325,27 335,25 333,35" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="3"/>
<path class="vurgu" d="M230 130 L265 95" stroke="var(--sema-c,#10b981)" stroke-width="3"/>
<text x="278" y="112" fill="var(--sema-c,#10b981)">v</text>
<text x="343" y="30" fill="var(--sema-a,#3b82f6)">Av = 3v</text>
<text x="300" y="148" text-anchor="middle">yalnız uzadı, λ = 3</text>
</svg>
:::

Aşağıdaki çizimde $A=\begin{bmatrix}2&1\\1&2\end{bmatrix}$ düzlemi büküyor. Izgaranın neredeyse her çizgisi döner; yalnızca iki çapraz doğrultu yerinde kalır.

::: etkilesim donusum-2b
{"A": "2 1; 1 2"}
:::

Şimdi vektörü kendin döndür. $\mathbf{v}$ ile $A\mathbf{v}$ aynı doğrultuya geldiği anda bir özvektör yakalamış olursun.

::: etkilesim ozvektor-2b
{"A": "2 1; 1 2"}
:::

## Karakteristik denklem

$A\mathbf{v}=\lambda\mathbf{v}$ eşitliği $(A-\lambda I)\mathbf{v}=\mathbf{0}$ diye yazılabilir. Sıfırdan farklı bir $\mathbf{v}$ ancak $A-\lambda I$ **tekil** ise vardır, yani:

$$
\det(A-\lambda I)=0
$$

Yöntem üç adımdır. **Birincisi:** köşegenden $\lambda$ çıkar. **İkincisi:** determinantı sıfıra eşitle ve kökleri bul. **Üçüncüsü:** her kök için $(A-\lambda I)\mathbf{v}=\mathbf{0}$ sistemini çöz.

$$
A-\lambda I=\begin{bmatrix}\ka{2-\lambda}&1\\1&\ka{2-\lambda}\end{bmatrix}
\quad\Rightarrow\quad
(\ka{2-\lambda})^2-1=\lambda^2-4\lambda+3=(\lambda-\kc{1})(\lambda-\kc{3})=0
$$

$$
\lambda=\kc{3}:\ \begin{bmatrix}-1&1\\1&-1\end{bmatrix}\mathbf{v}=\mathbf{0}\Rightarrow\mathbf{v}=\kutub{\begin{bmatrix}1\\1\end{bmatrix}}
\qquad
\lambda=\kc{1}:\ \begin{bmatrix}1&1\\1&1\end{bmatrix}\mathbf{v}=\mathbf{0}\Rightarrow\mathbf{v}=\kutub{\begin{bmatrix}1\\-1\end{bmatrix}}
$$

::: ipucu İki hızlı sağlama
Özdeğerlerin toplamı köşegen toplamına, yani izine eşittir: $1+3=2+2$. Çarpımları ise determinanta eşittir: $1\cdot 3=4-1$.
:::

::: hata λ'yı her elemandan çıkarmak
$A-\lambda I$ yazarken $\lambda$ **yalnızca köşegenden** çıkarılır. $\begin{bmatrix}2-\lambda&\ksil{1-\lambda}\\\ksil{1-\lambda}&2-\lambda\end{bmatrix}$ yanlıştır, çünkü $I$'nın köşegen dışı elemanları sıfırdır.
:::

::: hata Özvektörün tek olduğunu sanmak
$\begin{bmatrix}1\\1\end{bmatrix}$ bir özvektörse $\begin{bmatrix}2\\2\end{bmatrix}$ ve $\begin{bmatrix}-5\\-5\end{bmatrix}$ de özvektördür. Önemli olan **doğrultudur**, uzunluk değil. Mod şekilleri de bu yüzden ölçeklenerek, örneğin en büyük eleman 1 olacak biçimde verilir.
:::

## Genelleştirilmiş özdeğer: K φ = ω² M φ

Titreşimde kütle de işin içindedir. Problem $K\boldsymbol\phi=\omega^2M\boldsymbol\phi$ olur ve karakteristik denklem $\det(K-\omega^2M)=0$ biçimini alır. Kökler $\omega_i^2$, özvektörler mod şekilleri $\boldsymbol\phi_i$'dir.

::: not Mod şekillerinin dikliği
$K$ ve $M$ simetrikse farklı modlar **kütleye göre diktir**: $\boldsymbol\phi_i^TM\boldsymbol\phi_j=0$. 4. derste gördüğümüz simetrinin titreşimdeki ödülü budur.
:::

## Çözümlü örnekler

::: ornek Simetrik 2×2
$A=\begin{bmatrix}2&1\\1&2\end{bmatrix}$ matrisinin özdeğerlerini ve özvektörlerini bul.
--- cevap
$$
\lambda^2-4\lambda+3=0\Rightarrow\lambda_1=\kc{1},\ \lambda_2=\kc{3}
\qquad
\mathbf{v}_1=\begin{bmatrix}1\\-1\end{bmatrix},\ \mathbf{v}_2=\begin{bmatrix}1\\1\end{bmatrix}
$$
--- kod
mo.ozdeger("2 1; 1 2")
--- kontrol
r.deger[0] == [1, 3]
:::

::: ornek Simetrik olmayan 2×2
$A=\begin{bmatrix}4&1\\2&3\end{bmatrix}$ matrisinin özdeğerleri nedir?
--- ipucu
$\det(A-\lambda I)=(4-\lambda)(3-\lambda)-2$.
--- cevap
$$
\lambda^2-7\lambda+10=(\lambda-\kc{2})(\lambda-\kc{5})=0
$$
Sağlama: $2+5=7$ iz, $2\cdot 5=10$ determinant.
--- kod
mo.ozdeger("4 1; 2 3")
--- kontrol
r.deger[0] == [2, 5]
:::

::: ornek Sağlama: A v = λ v
$A=\begin{bmatrix}2&1\\1&2\end{bmatrix}$ ve $\mathbf{v}=\begin{bmatrix}1\\1\end{bmatrix}$ için $A\mathbf{v}$'yi hesapla.
--- cevap
$$
A\mathbf{v}=\begin{bmatrix}2+1\\1+2\end{bmatrix}=\begin{bmatrix}3\\3\end{bmatrix}=\kc{3}\begin{bmatrix}1\\1\end{bmatrix}
$$
Sonuç $\mathbf{v}$'nin 3 katıdır, demek ki $\lambda=3$.
--- kod
mo.carp("2 1; 1 2", "1; 1")
--- kontrol
r.deger == 3 * sp.Matrix([1, 1])
:::

::: ornek Üçgen matris
$A=\begin{bmatrix}2&3\\0&5\end{bmatrix}$ matrisinin özdeğerleri nedir?
--- cevap
$$
\det\begin{bmatrix}\ka{2-\lambda}&3\\0&\ka{5-\lambda}\end{bmatrix}=(2-\lambda)(5-\lambda)=0\Rightarrow\lambda=\kc{2},\ \kc{5}
$$
Üçgen matrisin özdeğerleri doğrudan **köşegenindedir**.
--- kod
mo.ozdeger("2 3; 0 5")
--- kontrol
r.deger[0] == [2, 5]
:::

::: ornek İz ile hızlı sağlama
$\begin{bmatrix}4&1\\2&3\end{bmatrix}$ matrisinin izini hesapla ve özdeğerlerin toplamıyla karşılaştır.
--- cevap
$$
\operatorname{iz}=4+3=\kc{7}=2+5
$$
--- kod
mo.iz("4 1; 2 3")
--- kontrol
r.deger == 7
:::

::: ornek 3×3, blok yapılı
$A=\begin{bmatrix}2&0&0\\0&3&4\\0&4&9\end{bmatrix}$ matrisinin özdeğerleri nedir?
--- ipucu
İlk satır ve sütun ayrık; 2 doğrudan bir özdeğerdir. Kalan $2\times2$ blok için $\lambda^2-12\lambda+11=0$.
--- cevap
$$
(2-\lambda)\big[(3-\lambda)(9-\lambda)-16\big]=(2-\lambda)(\lambda-1)(\lambda-11)=0
\Rightarrow\lambda=\kc{1},\ \kc{2},\ \kc{11}
$$
--- kod
mo.ozdeger("2 0 0; 0 3 4; 0 4 9")
--- kontrol
r.deger[0] == [1, 2, 11]
:::

::: ornek İki katlı çerçevenin modları
Kayma çerçevesi: alt kat kütlesi $2m$, üst kat $m$; alt kat rijitliği $2k$, üst kat $k$. $k/m$ birimiyle $K=\begin{bmatrix}3&-1\\-1&1\end{bmatrix}$ ve $M=\begin{bmatrix}2&0\\0&1\end{bmatrix}$ olur. Doğal frekansları ve mod şekillerini bul.
--- cevap
$$
\det(K-\lambda M)=(3-2\lambda)(1-\lambda)-1=2\lambda^2-5\lambda+2=0\Rightarrow\lambda=\omega^2=\kc{\tfrac12},\ \kc{2}
$$
$$
\boldsymbol\phi_1=\begin{bmatrix}1\\2\end{bmatrix}\ \text{(iki kat aynı yöne)},\qquad
\boldsymbol\phi_2=\begin{bmatrix}1\\-1\end{bmatrix}\ \text{(katlar zıt yöne)}
$$
Frekanslar $\omega_1=\sqrt{1/2}\approx 0.71\sqrt{k/m}$ ve $\omega_2=\sqrt2\approx1.41\sqrt{k/m}$ olur.
--- kod
mo.ozdeger("3 -1; -1 1", "2 0; 0 1")
--- kontrol
r.deger[0] == [sp.Rational(1, 2), 2]
--- yorum
Birinci modda bütün yapı aynı yöne salınır ve üst kat daha çok yer değiştirir. İkinci modda katlar birbirine karşı salınır. Gerçek binalarda ve köprülerde de ilk mod hep en "yumuşak" olanıdır.
:::

::: ornek Modların kütleye göre dikliği
Önceki örnekteki modlar için $\boldsymbol\phi_1^TM\boldsymbol\phi_2$ değerini hesapla.
--- cevap
$$
\begin{bmatrix}1&2\end{bmatrix}\begin{bmatrix}2&0\\0&1\end{bmatrix}\begin{bmatrix}1\\-1\end{bmatrix}=\begin{bmatrix}2&2\end{bmatrix}\begin{bmatrix}1\\-1\end{bmatrix}=2-2=\kc{0}
$$
--- kod
mo.carp(mo.transpoz("1; 2"), "2 0; 0 1", "1; -1")
--- kontrol
r.deger == sp.zeros(1, 1)
:::

::: ornek Gerçel özdeğeri olmayan matris
$R=\begin{bmatrix}0&-1\\1&0\end{bmatrix}$ düzlemi 90° döndürür. Gerçel özvektörü var mı?
--- cevap
$$
\det(R-\lambda I)=\lambda^2+1=0\Rightarrow\lambda=\pm i
$$
Gerçel kök yoktur. Her vektör 90° döndüğü için hiçbir doğrultu yerinde kalmaz. Simetrik matrislerde bu olmaz; $K$ ve $M$ simetrik olduğu için frekanslar her zaman gerçeldir.
:::

## Mühendislikte

::: muhendislik OMA ile FEM'in buluştuğu yer
OMA, köprünün ortam titreşiminden $\omega_i$ ve $\boldsymbol\phi_i$ değerlerini **ölçer**. FEM ise aynı değerleri $K\boldsymbol\phi=\omega^2M\boldsymbol\phi$ problemini çözerek **hesaplar**.

İkisi frekans farkı ve MAC değeriyle karşılaştırılır: $\mathrm{MAC}=\dfrac{(\boldsymbol\phi_{\text{FEM}}^T\boldsymbol\phi_{\text{OMA}})^2}{(\boldsymbol\phi_{\text{FEM}}^T\boldsymbol\phi_{\text{FEM}})(\boldsymbol\phi_{\text{OMA}}^T\boldsymbol\phi_{\text{OMA}})}$. Model güncelleme, $K$'daki elastisite modülünü bu fark en aza inene kadar ayarlamaktır.
:::

::: ozet
- $A\mathbf{v}=\lambda\mathbf{v}$: özvektör yön değiştirmez, $\lambda$ kat uzar.
- Özdeğerler $\det(A-\lambda I)=0$ denkleminin kökleridir.
- Özdeğer toplamı izdir, çarpımı determinanttır.
- Titreşimde $\det(K-\omega^2M)=0$: kökler doğal frekansların karesidir, özvektörler mod şekilleridir.
- Simetrik $K$ ve $M$ için frekanslar gerçeldir ve modlar kütleye göre diktir.
:::

## Alıştırma

::: alistirma ozdeger
{"zorluk": 1}
:::

::: alistirma ozdeger
{"zorluk": 2}
:::

::: alistirma ozdeger
{"zorluk": 3}
:::
