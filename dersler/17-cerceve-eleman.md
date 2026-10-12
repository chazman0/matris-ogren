---
baslik: Düzlem çerçeve elemanı ve koordinat dönüşümü
bolum: se
ozet: Eksenel ve eğilme rijitliğini birleştiren 6×6 çerçeve elemanı, yerel ve global eksenler, T dönüşüm matrisi, konsol kolon ve portal çerçeve çözümü.
sure: 50
---

## Neden?

Bina iskeletinde kolon hem eksenel kuvvet hem moment taşır; kiriş de yatay yükte eksenel kuvvet alır. Kafes elemanı yalnız eksenel, kiriş elemanı yalnız eğilme bilir. **Çerçeve elemanı** ikisini tek matriste birleştirir ve elemanı düzlemde istediğin açıyla döndürmene izin verir.

::: tanim Çerçeve elemanının SD'leri
Her düğümde üç SD vardır: yatay $u$, düşey $v$ ve dönme $\theta$. Eleman başına altı SD: $[\,u_1,\ v_1,\ \theta_1,\ u_2,\ v_2,\ \theta_2\,]$. Karşılık gelen kuvvetler $N$, $V$ ve $M$'dir.
:::

## Yerel rijitlik matrisi

Eleman ekseni boyunca $x'$, ona dik $y'$ eksenini alırsak matris iki parçanın üst üste konmasıdır: eksenel kısım kafesten, eğilme kısmı kiriş elemanından gelir.

$$
\mathbf{k}'=
\begin{bmatrix}
\kutua{\tfrac{EA}{L}} & 0 & 0 & \kutua{-\tfrac{EA}{L}} & 0 & 0\\
0 & \kutub{\tfrac{12EI}{L^3}} & \kutub{\tfrac{6EI}{L^2}} & 0 & \kutub{-\tfrac{12EI}{L^3}} & \kutub{\tfrac{6EI}{L^2}}\\
0 & \kutub{\tfrac{6EI}{L^2}} & \kutuc{\tfrac{4EI}{L}} & 0 & \kutub{-\tfrac{6EI}{L^2}} & \kutuc{\tfrac{2EI}{L}}\\
\kutua{-\tfrac{EA}{L}} & 0 & 0 & \kutua{\tfrac{EA}{L}} & 0 & 0\\
0 & \kutub{-\tfrac{12EI}{L^3}} & \kutub{-\tfrac{6EI}{L^2}} & 0 & \kutub{\tfrac{12EI}{L^3}} & \kutub{-\tfrac{6EI}{L^2}}\\
0 & \kutub{\tfrac{6EI}{L^2}} & \kutuc{\tfrac{2EI}{L}} & 0 & \kutub{-\tfrac{6EI}{L^2}} & \kutuc{\tfrac{4EI}{L}}
\end{bmatrix}
$$

Mavi hücreler eksenel, turuncu ve yeşil hücreler eğilme terimleridir. Sıfırlar önemlidir: **yerel eksende** eksenel kuvvet ile eğilme birbirinden bağımsızdır.

## Koordinat dönüşümü

Yapıda elemanlar farklı açılarda durur; birleştirme ise tek bir **global** eksen takımında yapılır. Eleman ekseni global $x$ ile $\alpha$ açısı yapıyorsa, $c=\cos\alpha$ ve $s=\sin\alpha$ ile:

$$
\begin{bmatrix} u' \\ v' \\ \theta' \end{bmatrix}=
\begin{bmatrix} \kutua{c} & \kutua{s} & 0 \\ \kutub{-s} & \kutub{c} & 0 \\ 0 & 0 & \kutuc{1} \end{bmatrix}
\begin{bmatrix} u \\ v \\ \theta \end{bmatrix}
\qquad
\mathbf{T}=\begin{bmatrix}\boldsymbol\lambda & \mathbf{0}\\ \mathbf{0} & \boldsymbol\lambda\end{bmatrix},\qquad
\mathbf{k}=\mathbf{T}^T\,\mathbf{k}'\,\mathbf{T}
$$

::: sekil Yerel ve global eksenler: dönme SD'si dönüşümden etkilenmez
<svg viewBox="0 0 400 230" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<path d="M30 200H370 M30 200V20" stroke="var(--sema-cizgi,#94a3b8)" fill="none"/>
<text x="372" y="196">x</text><text x="36" y="26">y</text>
<path class="vurgu" d="M90 180L290 65" stroke="var(--sema-b,#f59e0b)" stroke-width="6" stroke-linecap="round" fill="none"/>
<circle cx="90" cy="180" r="6" fill="var(--sema-a,#3b82f6)"/><circle cx="290" cy="65" r="6" fill="var(--sema-a,#3b82f6)"/>
<text x="78" y="204">1</text><text x="298" y="58">2</text>
<path class="ok" pathLength="1" d="M290 65L345 33" stroke="var(--sema-a,#3b82f6)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="333,34 345,33 338,44" stroke="var(--sema-a,#3b82f6)" stroke-width="2" fill="none"/>
<text x="350" y="30" fill="var(--sema-a,#3b82f6)">x′</text>
<path class="ok" pathLength="1" d="M290 65L322 120" stroke="var(--sema-c,#10b981)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="312,112 322,120 321,107" stroke="var(--sema-c,#10b981)" stroke-width="2" fill="none"/>
<text x="326" y="134" fill="var(--sema-c,#10b981)">−y′</text>
<path d="M150 180A60 60 0 0 0 142 150" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<path d="M90 180H170" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="4 3" fill="none"/>
<text x="156" y="168">α</text>
<path d="M276 52A20 20 0 1 1 306 52" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5" fill="none"/>
<text x="268" y="30" fill="var(--sema-b,#f59e0b)">θ = θ′</text>
<text x="40" y="225">c = cos α, s = sin α: u, v döner; θ aynı kalır</text>
</svg>
:::

Aşağıda açıyı değiştir: $\alpha=0$'da global matris yerel matrisle aynıdır; $\alpha=90°$'de eksenel ve eğilme terimleri yer değiştirir.

::: etkilesim cerceve-k
{"E": 200000000, "A": 0.01, "I": 0.000008, "L": 3, "aci": 90}
:::

::: hata Dönme SD'sini de döndürmek
$\boldsymbol\lambda$'nın üçüncü satırı $[0\ 0\ 1]$'dir. Dönme düzleme diktir, eksen takımını çevirmek onu değiştirmez. Kafes elemanının $2\times2$ dönüşüm bloğunu $3\times3$'e genişletirken bu satırı unutursan matris yanlış çıkar.
:::

::: not Elemanın yönü
Eleman $[4,3]$ diye tanımlanırsa yerel $x'$ ekseni 4'ten 3'e doğrudur. Global $\mathbf{K}$ değişmez; değişen yalnız yerel uç kuvvetlerinin işaretidir. Program diyagramları bu yöne göre çizer.
:::

## Portal çerçevede SD haritası

Dört düğümlü portal çerçevede $4\times3=12$ SD vardır. Ankastre iki taban 6 SD'yi tutar, 6 serbest SD kalır. Haritada her elemanın kod numarasını izle.

::: etkilesim dof-haritasi
{"hazir": "portal"}
:::

::: uyari Eksenel ve eğilme rijitliği çok farklıdır
Aynı elemanda $EA/L$ ile $12EI/L^3$ oranı $AL^2/12I$'dır. Aşağıdaki kolonda bu oran yaklaşık 940'tır. Bu fark çözümü bozmaz ama eksenel deformasyonun neden çoğu zaman ihmal edilebildiğini açıklar.
:::

## Çözümlü örnekler

::: ornek Kolonun global matrisi: Tᵀ k′ T
$L=3$ m düşey kolon ($\alpha=90°$), $E=200$ GPa, $A=0{,}01$ m², $I=8\times10^{-6}$ m⁴. Global matrisi kur, tabanı ankastre yapıp üst uca $F_x=10$ kN uygula.
--- ipucu
$c=0$, $s=1$: $\boldsymbol\lambda=[0\ 1\ 0;\ -1\ 0\ 0;\ 0\ 0\ 1]$. Yerel terimler $EA/L=2\times10^6/3$, $12EI/L^3=6400/9$, $6EI/L^2=3200/3$, $4EI/L=6400/3$, $2EI/L=3200/3$.
--- cevap
$K_{11}=6400/9$: kolonun yatay rijitliği eğilmeden gelir. $K_{22}=2\times10^6/3$: düşey rijitliği eksenel. Üst uç: $u=9/160$ m, $\theta=-9/320$ rad.
--- kod
k = "2000000/3 0 0 -2000000/3 0 0; 0 6400/9 3200/3 0 -6400/9 3200/3; 0 3200/3 6400/3 0 -3200/3 3200/3; -2000000/3 0 0 2000000/3 0 0; 0 -6400/9 -3200/3 0 6400/9 -3200/3; 0 3200/3 3200/3 0 -3200/3 6400/3"
T = "0 1 0 0 0 0; -1 0 0 0 0 0; 0 0 1 0 0 0; 0 0 0 0 1 0; 0 0 0 -1 0 0; 0 0 0 0 0 1"
K = mo.carp(mo.transpoz(T).deger, k, T)
K, mo.sinir_kosulu(K.deger, "0; 0; 0; 10; 0; 0", sabit=[1, 2, 3])
--- kontrol
r[0].deger[0, 0] == sp.Rational(6400, 9) and r[0].deger[1, 1] == sp.Rational(2000000, 3) and r[0].deger[0, 2] == sp.Rational(-3200, 3) and r[-1].deger[3] == sp.Rational(9, 160)
--- yorum
Dönüşümden sonra eksenel ve eğilme terimleri global matriste yer değiştirdi. Sonuç, konsol formülü $PL^3/3EI$ ile aynıdır.
:::

::: ornek Konsol kolon: hazır model
Aynı kolonu hazır `cerceve-konsol-kolon` modeliyle çöz. Taban tepkilerini oku.
--- ipucu
Yatay denge $R_x=-10$ kN, moment dengesi $M=10\cdot3$.
--- cevap
$u_2=9/160$ m; tepkiler $F_x=-10$ kN, $F_y=0$, $M=30$ kN·m.
--- kod
se.se_coz(se.ornek_model("cerceve-konsol-kolon"))
--- kontrol
r.deger[3] == sp.Rational(9, 160) and abs(r.veri["tepkiler"][0]["Fx"] + 10) < 1e-9 and abs(r.veri["tepkiler"][0]["M"] - 30) < 1e-9
--- yorum
Elle kurduğun $\mathbf{T}^T\mathbf{k}'\mathbf{T}$ ile programın sonucu aynı. Program her eleman için bu dönüşümü kendisi yapar.
:::

::: ornek Yatay konsol: eksenel ve eğilme birlikte
Aynı eleman yatay ($\alpha=0$), sol ucu ankastre. Sağ uca $F_x=100$ kN ve $F_y=-10$ kN. Uzama ve sehimi karşılaştır.
--- ipucu
$\alpha=0$'da $\mathbf{T}=\mathbf{I}$: global matris yerel matristir. SD 1, 2, 3 tutulu.
--- cevap
$u_2=3/20000$ m $=0{,}15$ mm, $v_2=-9/160$ m $\approx56$ mm, $\theta_2=-9/320$ rad.
--- kod
k = "2000000/3 0 0 -2000000/3 0 0; 0 6400/9 3200/3 0 -6400/9 3200/3; 0 3200/3 6400/3 0 -3200/3 3200/3; -2000000/3 0 0 2000000/3 0 0; 0 -6400/9 -3200/3 0 6400/9 -3200/3; 0 3200/3 3200/3 0 -3200/3 6400/3"
mo.sinir_kosulu(k, "0; 0; 0; 100; -10; 0", sabit=[1, 2, 3])
--- kontrol
r.deger[3] == sp.Rational(3, 20000) and r.deger[4] == sp.Rational(-9, 160) and r.deger[5] == sp.Rational(-9, 320)
--- yorum
On kat büyük kuvvet, 375 kat küçük yer değiştirme verdi. Eksenel rijitliğin büyüklüğü sayılarda böyle görünür.
:::

::: ornek Yatay konsol: modelle eksenel kuvvet
Aynı yatay konsolu sözlük modeliyle kur ve elemanın eksenel kuvvetini oku.
--- ipucu
Mesnette $u_x$, $u_y$ ve $r_z$ tutulu.
--- cevap
$N=+100$ kN (çekme); tepkiler $F_x=-100$, $F_y=10$, $M=30$.
--- kod
model = {"tip": "cerceve", "dugumler": [{"no": 1, "x": 0, "y": 0}, {"no": 2, "x": 3, "y": 0}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.01", "I": "8e-6"}], "mesnetler": [{"dugum": 1, "ux": True, "uy": True, "rz": True}], "yukler": [{"dugum": 2, "Fx": 100, "Fy": -10}]}
se.se_coz(model)
--- kontrol
abs(r.veri["elemanlar"][0]["N"] - 100) < 1e-9 and abs(r.veri["tepkiler"][0]["M"] - 30) < 1e-9 and r.deger[3] == sp.Rational(3, 20000)
--- yorum
Eksenel kuvvetin işareti: pozitif çekme, negatif basınç.
:::

::: ornek Portal çerçeve
Hazır `cerceve-portal`: 6 m açıklık, 4 m yükseklik, ankastre tabanlar, kirişte $q=10$ kN/m, sol üst köşede 20 kN yatay yük. Dengeyi ve sağ taban momentini denetle.
--- ipucu
$\sum F_y$: tepkiler toplamı $10\cdot6=60$ kN. $\sum F_x$: tepkiler toplamı $-20$ kN.
--- cevap
$R_{1y}\approx24{,}08$, $R_{4y}\approx35{,}92$ kN; $R_{1x}\approx-3{,}30$, $R_{4x}\approx-16{,}70$ kN; $M_4\approx31{,}11$ kN·m. Kirişte $|M|_{max}\approx35{,}69$ kN·m.
--- kod
se.se_coz(se.ornek_model("cerceve-portal"))
--- kontrol
abs(r.veri["tepkiler"][0]["Fy"] + r.veri["tepkiler"][1]["Fy"] - 60) < 1e-6 and abs(r.veri["tepkiler"][0]["Fx"] + r.veri["tepkiler"][1]["Fx"] + 20) < 1e-6 and abs(r.veri["tepkiler"][1]["M"] - 31.108) < 1e-3
--- yorum
Yatay yük sağa ittiği için sağ kolon daha çok basınç ve kesme alır. Simetrik düşey yük tek başına iki tabana eşit yük verirdi; asimetri yatay yükten gelir.
:::

::: ornek Portalın SD sayısı
Portal çerçevenin global matrisi kaç boyutludur? Kaç SD serbesttir? Kolon 1'in kod numarası nedir?
--- ipucu
Düğüm $i$'nin SD'leri $3i-2,\ 3i-1,\ 3i$.
--- cevap
$12\times12$; 6 serbest SD (düğüm 2 ve 3). Kolon 1 düğüm 1–2: kod $[1,2,3,4,5,6]$.
--- yorum
İndirgenmiş sistem $6\times6$'dır. Elle çözülmez ama programın ne yaptığını tam olarak bilirsin.
:::

::: ornek α = 90° için dönüşüm
Düşey bir kolonda yerel $v'$ hangi global SD'ye karşılık gelir?
--- ipucu
$v'=-s\,u+c\,v$; $c=0$, $s=1$.
--- cevap
$v'=-u$. Kolonun yerel dik ekseni global $-x$ yönündedir; bu yüzden $K_{13}$ negatif çıkar.
--- yorum
İşaret karışıklıklarının çoğu bu satırdan gelir. Şüphede kaldığında $\mathbf{T}^T\mathbf{k}'\mathbf{T}$'yi programa hesaplat.
:::

::: ornek Rijitlik oranı
Örnekteki kolonda $\dfrac{EA/L}{12EI/L^3}$ kaçtır?
--- ipucu
$AL^2/12I$.
--- cevap
$0{,}01\cdot9/(12\cdot8\times10^{-6})=937{,}5$.
--- yorum
Bu oran büyüdükçe çerçeve “eksenel olarak rijit” davranır. Elle çözümlerde eksenel deformasyonu ihmal etmenin dayanağı budur.
:::

::: muhendislik Köprü ayakları ve kemer: çerçeve modeli
Tarihi köprüde ayaklar ve kemer halkası çerçeve elemanıyla modellenirse eksenel basınç ile moment birlikte çıkar. Yığma kesitte asıl soru, $e=M/N$ dış merkezliğinin kesit çekirdeğinde kalıp kalmadığıdır. Çerçeve modeli bu denetimi kemer boyunca her kesitte yapmanı sağlar ve katı modelden önce hızlı bir ilk tahmin verir.
:::

::: ozet Özet
- Çerçeve düğümünde üç SD: $u$, $v$, $\theta$; eleman $6\times6$.
- $\mathbf{k}'$ = kafesin eksenel kısmı + kirişin eğilme kısmı; yerelde bağımsızdırlar.
- $\mathbf{k}=\mathbf{T}^T\mathbf{k}'\mathbf{T}$; $\boldsymbol\lambda$'nın üçüncü satırı $[0\ 0\ 1]$.
- Uç kuvvetleri yerel eksende okunur: $N$ çekmede pozitif.
- Dengeyi her zaman tepki toplamlarıyla denetle.
:::

## Alıştırma

Dönüşüm mantığı kafes elemanıyla aynıdır; önce orada pekiştir, sonra birleştirmeye geç.

::: alistirma kafes-k
{"zorluk": 2}
:::

::: alistirma birlestir
{"zorluk": 2}
:::
