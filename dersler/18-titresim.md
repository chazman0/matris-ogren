---
baslik: Serbest titreşim, doğal frekans ve mod şekilleri
bolum: se
ozet: Kütle matrisi, genelleştirilmiş özdeğer problemi K φ = λ M φ, doğal frekans ve periyot, mod şekillerinin ortogonalliği, Rayleigh oranı ve OMA ile karşılaştırma için MAC.
sure: 50
---

## Neden?

Şimdiye kadar yük sabitti, yapı da dengede duruyordu. Rüzgâr, trafik ya da deprem altında yapı **titreşir**. Her yapının kendine özgü titreşim frekansları ve biçimleri vardır. OMA ölçümüyle bulduğun frekanslar ile sonlu eleman modelinin verdiği frekansları karşılaştırmak, model güncellemenin temelidir.

::: tanim Serbest titreşim denklemi
Sönümsüz serbest titreşimde $\mathbf{M}\ddot{\mathbf{u}}+\mathbf{K}\mathbf{u}=\mathbf{0}$. Çözümü $\mathbf{u}=\boldsymbol\phi\sin\omega t$ biçiminde ararsak

$$
\big(\mathbf{K}-\omega^2\mathbf{M}\big)\boldsymbol\phi=\mathbf{0}
\quad\Longrightarrow\quad
\mathbf{K}\boldsymbol\phi=\lambda\,\mathbf{M}\boldsymbol\phi,\qquad \lambda=\omega^2
$$

$\lambda$ özdeğer, $\boldsymbol\phi$ **mod şekli**, $\omega$ açısal doğal frekanstır (rad/s).
:::

## Kütle matrisi

Rijitlik matrisi gibi kütle matrisi de elemanlardan birleştirilir. İki yaygın seçenek vardır:

$$
\mathbf{m}_{toplu}=\frac{\rho AL}{2}\begin{bmatrix}\ka{1}&0\\0&\ka{1}\end{bmatrix}
\qquad
\mathbf{m}_{tutarlı}=\frac{\rho AL}{6}\begin{bmatrix}\kb{2}&\kc{1}\\\kc{1}&\kb{2}\end{bmatrix}
$$

**Toplu kütle** köşegendir, hesabı kolaydır. **Tutarlı kütle** şekil fonksiyonlarından gelir ve aynı ağ ile biraz daha doğru frekans verir. Kat kütlesi döşemede toplanan binalarda köşegen kütle doğaldır.

## İki katlı kayma binası

Kat kütleleri $m_1=2$ t, $m_2=1$ t; kat rijitlikleri $k_1=200$ kN/m, $k_2=100$ kN/m. Birleştirme kuralıyla:

$$
\mathbf{K}=\begin{bmatrix}\kutua{k_1+k_2}&\kutub{-k_2}\\\kutub{-k_2}&\kutua{k_2}\end{bmatrix}=\begin{bmatrix}300&-100\\-100&100\end{bmatrix},
\qquad
\mathbf{M}=\begin{bmatrix}2&0\\0&1\end{bmatrix}
$$

::: sekil İki katlı kayma binası ve iki mod şekli
<svg viewBox="0 0 400 230" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<path d="M20 200H150" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="3" fill="none"/>
<path d="M45 200V60 M125 200V60" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="2" fill="none"/>
<path d="M40 130H130 M40 60H130" stroke="var(--sema-a,#3b82f6)" stroke-width="6" stroke-linecap="round" fill="none"/>
<text x="62" y="122">m₁ = 2</text><text x="62" y="52">m₂ = 1</text>
<text x="52" y="172" font-size="11">k₁ = 200</text><text x="52" y="100" font-size="11">k₂ = 100</text>
<path d="M210 200V50 M320 200V50" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="4 4" fill="none"/>
<polyline class="vurgu" points="210,200 235,130 260,60" stroke="var(--sema-a,#3b82f6)" stroke-width="2.5" fill="none"/>
<circle cx="235" cy="130" r="5" fill="var(--sema-a,#3b82f6)"/><circle cx="260" cy="60" r="5" fill="var(--sema-a,#3b82f6)"/>
<polyline points="320,200 290,130 350,60" stroke="var(--sema-c,#10b981)" stroke-width="2.5" fill="none"/>
<circle cx="290" cy="130" r="5" fill="var(--sema-c,#10b981)"/><circle cx="350" cy="60" r="5" fill="var(--sema-c,#10b981)"/>
<path class="ok" pathLength="1" d="M60 30H110" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="100,24 110,30 100,36" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<text x="68" y="20" fill="var(--sema-b,#f59e0b)">u₂</text>
<text x="180" y="222" fill="var(--sema-a,#3b82f6)">Mod 1: φ=[1, 2], λ=50</text>
<text x="290" y="222" fill="var(--sema-c,#10b981)">Mod 2: φ=[−1, 1]</text>
</svg>
:::

Birinci modda iki kat aynı yöne, üst kat iki kat fazla gider. İkinci modda katlar ters yöne hareket eder ve frekans daha yüksektir. Aşağıda kütleleri ve rijitlikleri değiştir, iki modun nasıl değiştiğini izle.

::: etkilesim modal-titresim
{"m": [2, 1], "k": [200, 100]}
:::

## Özdeğer ve özvektör olarak modlar

$\mathbf{M}^{-1}\mathbf{K}=\begin{bmatrix}150&-50\\-100&100\end{bmatrix}$ matrisinin özdeğerleri de 50 ve 200'dür. 50'ye bölünmüş hâli $\begin{bmatrix}3&-1\\-2&2\end{bmatrix}$ aynı özvektörleri taşır. Aşağıda birim vektörü döndür: $\mathbf{A}\mathbf{x}$ ile $\mathbf{x}$ aynı doğrultuya geldiğinde bir mod şekli yakaladın demektir.

::: etkilesim ozvektor-2b
{"A": "3 -1; -2 2"}
:::

Özdeğerler karakteristik denklemden de bulunur:

$$
\det(\mathbf{K}-\lambda\mathbf{M})=\begin{vmatrix}300-2\lambda&-100\\-100&100-\lambda\end{vmatrix}=2(\lambda-50)(\lambda-200)=0
$$

Frekansa geçiş: $\omega=\sqrt{\lambda}$, $f=\omega/2\pi$, $T=1/f$.

::: hata λ'yı ω, ω'yı f sanmak
$\lambda=50$ s⁻² ise $\omega=\sqrt{50}\approx7{,}07$ rad/s, $f=\omega/2\pi\approx1{,}13$ Hz, $T\approx0{,}89$ s. OMA ölçümü hertz verir; modelden çıkan $\lambda$'yı doğrudan hertzle karşılaştırmak 6–7 kat hata demektir.
:::

::: hata Mod şeklini gerçek genlik sanmak
$\boldsymbol\phi=[1,\,2]$ ile $[5,\,10]$ aynı moddur. Mod şekli yalnız **oranları** verir; genlik serbest titreşim denkleminden bulunamaz, yükten ya da başlangıç koşulundan gelir.
:::

::: uyari Birimler tutarlı olmalı
kN ve m kullanıyorsan kütle **ton** olmalıdır: $1\ \text{kN}=1\ \text{t}\cdot\text{m/s}^2$. Kütleyi kg girersen frekanslar $\sqrt{1000}\approx31{,}6$ kat küçük çıkar.
:::

## Ortogonallik ve Rayleigh oranı

Farklı iki mod, kütle ve rijitlik matrisine göre diktir:

$$
\boldsymbol\phi_i^T\,\mathbf{M}\,\boldsymbol\phi_j=0,\qquad \boldsymbol\phi_i^T\,\mathbf{K}\,\boldsymbol\phi_j=0\qquad(i\ne j)
$$

Bir mod için $\lambda=\dfrac{\boldsymbol\phi^T\mathbf{K}\boldsymbol\phi}{\boldsymbol\phi^T\mathbf{M}\boldsymbol\phi}$ **Rayleigh oranıdır**. Kaba bir şekil tahmininden bile iyi bir birinci frekans tahmini verir.

::: not Kütleye göre normalleştirme
$\boldsymbol\phi^T\mathbf{M}\boldsymbol\phi=1$ olacak biçimde ölçeklenmiş modlar, modal süperpozisyonda denklemleri birbirinden ayırır. Birinci mod için $\boldsymbol\phi_1=[1,\,2]/\sqrt6$.
:::

## Çözümlü örnekler

::: ornek Genelleştirilmiş özdeğer problemi
İki katlı binanın özdeğerlerini ve mod şekillerini bul.
--- ipucu
`mo.ozdeger(K, M)` doğrudan $\mathbf{K}\boldsymbol\phi=\lambda\mathbf{M}\boldsymbol\phi$'yi çözer.
--- cevap
$\lambda_1=50$, $\boldsymbol\phi_1=[1,\,2]$; $\lambda_2=200$, $\boldsymbol\phi_2=[-1,\,1]$.
--- kod
mo.ozdeger("300 -100; -100 100", "2 0; 0 1")
--- kontrol
r.deger[0] == [50, 200]
--- yorum
$\omega_1\approx7{,}07$ rad/s ($f_1\approx1{,}13$ Hz), $\omega_2\approx14{,}14$ rad/s ($f_2\approx2{,}25$ Hz).
:::

::: ornek Karakteristik denklem
$\det(\mathbf{K}-\lambda\mathbf{M})$'yi $\lambda$ cinsinden aç ve köklerini bul.
--- ipucu
$(300-2\lambda)(100-\lambda)-100^2$.
--- cevap
$2\lambda^2-500\lambda+20000=2(\lambda-50)(\lambda-200)$; kökler 50 ve 200.
--- kod
mo.determinant("300-2*l -100; -100 100-l")
--- kontrol
sorted(sp.solve(r.deger)) == [50, 200]
--- yorum
$n$ SD'li sistemde $n$. dereceden bir polinom çıkar. Büyük modellerde program bu polinomu kurmaz, yinelemeli yöntemler kullanır.
:::

::: ornek Özdeğerde matris tekildir
$\lambda=50$ ve $\lambda=200$ için $\mathbf{K}-\lambda\mathbf{M}$'nin determinantını hesapla.
--- ipucu
$\lambda=50$: $[200\ -100;\ -100\ 50]$.
--- cevap
İkisi de 0. Matris tekil olduğu için sıfırdan farklı bir $\boldsymbol\phi$ bulunabilir.
--- kod
mo.determinant("200 -100; -100 50"), mo.determinant("-100 -100; -100 -100")
--- kontrol
r[0].deger == 0 and r[1].deger == 0
--- yorum
Mod şeklinin ölçeğinin serbest olması bu tekillikten gelir.
:::

::: ornek Ortogonallik
$\boldsymbol\phi_1^T\mathbf{M}\boldsymbol\phi_2$ ve $\boldsymbol\phi_1^T\mathbf{K}\boldsymbol\phi_2$'yi hesapla.
--- ipucu
Satır vektörü `"1 2"`, sütun vektörü `"-1; 1"`.
--- cevap
İkisi de 0.
--- kod
mo.carp("1 2", "2 0; 0 1", "-1; 1"), mo.carp("1 2", "300 -100; -100 100", "-1; 1")
--- kontrol
r[0].deger[0] == 0 and r[1].deger[0] == 0
--- yorum
Dikkat: $\boldsymbol\phi_1^T\boldsymbol\phi_2=-1+2=1\ne0$. Modlar sıradan anlamda değil, $\mathbf{M}$'ye göre diktir.
:::

::: ornek Rayleigh oranı
Birinci mod için modal kütle ve modal rijitliği hesapla, oranlarını al.
--- ipucu
$\boldsymbol\phi_1^T\mathbf{M}\boldsymbol\phi_1$ ve $\boldsymbol\phi_1^T\mathbf{K}\boldsymbol\phi_1$.
--- cevap
Modal kütle 6, modal rijitlik 300, oran $300/6=50=\lambda_1$.
--- kod
mo.carp("1 2", "2 0; 0 1", "1; 2"), mo.carp("1 2", "300 -100; -100 100", "1; 2")
--- kontrol
r[0].deger[0] == 6 and r[1].deger[0] == 300 and r[1].deger[0] / r[0].deger[0] == 50
--- yorum
Kaba tahmin $[1,\,1]$ ile oran $200/3\approx66{,}7$ olur: gerçek değerden büyük ama yakın. Rayleigh oranı her zaman $\lambda_1$'in üstünde kalır.
:::

::: ornek MAC: modeli ölçümle karşılaştırmak
OMA ile ölçülen birinci mod $\boldsymbol\phi_e=[1,\ 1{,}9]$, modelin modu $\boldsymbol\phi_a=[1,\ 2]$. MAC değerini hesapla.
--- ipucu
$\text{MAC}=\dfrac{(\boldsymbol\phi_a^T\boldsymbol\phi_e)^2}{(\boldsymbol\phi_a^T\boldsymbol\phi_a)(\boldsymbol\phi_e^T\boldsymbol\phi_e)}$.
--- cevap
$4{,}8^2/(5\cdot4{,}61)=2304/2305\approx0{,}9996$.
--- kod
mo.carp("1 2", "1; 19/10"), mo.carp("1 2", "1; 2"), mo.carp("1 19/10", "1; 19/10")
--- kontrol
r[0].deger[0] ** 2 / (r[1].deger[0] * r[2].deger[0]) == sp.Rational(2304, 2305)
--- yorum
MAC 1'e yakınsa iki mod aynı biçimdedir. Uygulamada 0,9 üstü iyi eşleşme sayılır. MAC ölçekten bağımsızdır; bu yüzden ölçüm birimini dert etmezsin.
:::

::: ornek Eşit kütleli iki kat
$\mathbf{K}=[2000\ -1000;\ -1000\ 1000]$, $\mathbf{M}=\mathbf{I}$. Birinci özdeğeri bul.
--- ipucu
Kökler $1500\mp500\sqrt5$.
--- cevap
$\lambda_1=1500-500\sqrt5\approx381{,}97$, $\omega_1\approx19{,}54$ rad/s, $f_1\approx3{,}11$ Hz.
--- kod
mo.ozdeger("2000 -1000; -1000 1000", "1 0; 0 1")
--- kontrol
abs(float(r.deger[0][0]) - 381.966) < 1e-3
--- yorum
Mod şeklinde üst katın alt kata oranı altın oran $(1+\sqrt5)/2\approx1{,}618$ çıkar.
:::

::: ornek Tek serbestlik dereceli sistem
$k=4000$ kN/m, $m=10$ t. Doğal frekans ve periyodu bul.
--- ipucu
$\lambda=k/m$.
--- cevap
$\lambda=400$, $\omega=20$ rad/s, $f\approx3{,}18$ Hz, $T\approx0{,}314$ s.
--- kod
mo.ozdeger("4000", "10")
--- kontrol
r.deger[0] == [400]
--- yorum
Matris formülasyonu tek SD'de bildiğin $\omega=\sqrt{k/m}$'ye iner.
:::

::: ornek Frekans dönüşümleri
$\lambda_2=200$ için $\omega_2$, $f_2$ ve $T_2$'yi hesapla.
--- ipucu
$\sqrt{200}=10\sqrt2$.
--- cevap
$\omega_2\approx14{,}14$ rad/s, $f_2\approx2{,}25$ Hz, $T_2\approx0{,}44$ s.
--- yorum
$\lambda_2/\lambda_1=4$ olduğundan $f_2/f_1=2$. Frekans oranları, ölçümle modeli karşılaştırırken birimden bağımsız ilk denetimdir.
:::

::: muhendislik OMA ve model güncelleme
Tarihi köprüde OMA ile ilk birkaç modun frekansı ve şekli ölçülür. Sonlu eleman modelinde aynı modlar $\mathbf{K}\boldsymbol\phi=\lambda\mathbf{M}\boldsymbol\phi$ ile hesaplanır. Frekans farkı ve MAC değerleri birlikte değerlendirilir. Fark büyükse elastisite modülü, dolgu rijitliği ve mesnet yayları gibi belirsiz parametreler, frekans hatasını küçültecek biçimde güncellenir. Önce modların **eşleştirilmesi** gelir: frekansı yakın ama MAC'i düşük iki mod aynı mod değildir.
:::

::: ozet Özet
- Serbest titreşim: $\mathbf{K}\boldsymbol\phi=\lambda\mathbf{M}\boldsymbol\phi$, $\lambda=\omega^2$.
- $\omega$ rad/s, $f=\omega/2\pi$ Hz, $T=1/f$ s.
- Mod şekli yalnız oranları verir; ölçeği serbesttir.
- Modlar $\mathbf{M}$ ve $\mathbf{K}$'ye göre diktir.
- Rayleigh oranı $\lambda_1$'i üstten yaklaşık verir; MAC mod şekillerini karşılaştırır.
- kN–m sisteminde kütle ton olmalıdır.
:::

## Alıştırma

Özdeğer alıştırmaları, mod hesabının matris tarafını pekiştirir.

::: alistirma ozdeger
{"zorluk": 2}
:::

::: alistirma ozdeger
{"zorluk": 3}
:::
