---
baslik: Kiriş elemanı ve eşdeğer düğüm yükleri
bolum: se
ozet: Euler–Bernoulli kiriş elemanı, Hermite şekil fonksiyonları, 4×4 rijitlik matrisi, yayılı ve tekil yüklerin düğümlere aktarılması, kesme ve moment diyagramı.
sure: 50
---

## Neden?

Çubuk yalnız eksenel kuvvet taşır; döşeme kirişi, köprü tabliyesi ya da lento ise **eğilir**. Eğilmeyi modellemek için düğümde yalnız yer değiştirme değil, **dönme** de bilinmeyen olmalıdır. Kiriş elemanı bu iki büyüklüğü birlikte taşır ve yapı mühendisliğinin en çok kullanılan elemanıdır.

::: tanim Kiriş elemanının SD'leri
Her düğümde iki SD vardır: düşey yer değiştirme $v$ ve dönme $\theta$. Eleman başına dört SD: $[\,v_1,\ \theta_1,\ v_2,\ \theta_2\,]$. Karşılık gelen kuvvetler kesme $V$ ve moment $M$'dir.
:::

## Şekil fonksiyonları

Eleman içindeki sehim, dört düğüm değerinden **kübik** bir eğriyle elde edilir. $\xi=x/L$ olmak üzere:

$$
v(\xi)=\ka{N_1}\,v_1+\kb{N_2}\,\theta_1+\kc{N_3}\,v_2+N_4\,\theta_2
$$

$$
\ka{N_1}=1-3\xi^2+2\xi^3,\quad
\kb{N_2}=L(\xi-2\xi^2+\xi^3),\quad
\kc{N_3}=3\xi^2-2\xi^3,\quad
N_4=L(-\xi^2+\xi^3)
$$

::: sekil Hermite şekil fonksiyonları: her biri bir SD'de 1, diğerlerinde 0
<svg viewBox="0 0 400 190" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<path d="M40 110H360 M40 20V170" stroke="var(--sema-cizgi,#94a3b8)" fill="none"/>
<path d="M40 30H360" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="3 4" fill="none"/>
<text x="28" y="34" text-anchor="end">1</text><text x="28" y="114" text-anchor="end">0</text>
<text x="40" y="186" text-anchor="middle">ξ=0</text><text x="360" y="186" text-anchor="middle">ξ=1</text>
<path class="vurgu" d="M40 30 C146.7 30 253.3 110 360 110" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2.5"/>
<path d="M40 110 C146.7 110 253.3 30 360 30" fill="none" stroke="var(--sema-c,#10b981)" stroke-width="2.5"/>
<path d="M40 110 C146.7 56.7 253.3 110 360 110" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2" stroke-dasharray="6 3"/>
<path d="M40 110 C146.7 110 253.3 163.3 360 110" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="2" stroke-dasharray="6 3"/>
<text x="70" y="24" fill="var(--sema-a,#3b82f6)">N₁</text>
<text x="330" y="24" fill="var(--sema-c,#10b981)">N₃</text>
<text x="120" y="76" fill="var(--sema-b,#f59e0b)">N₂/L ×2</text>
<text x="270" y="150">N₄/L ×2</text>
</svg>
:::

$N_1$ sol uçta sehim 1, eğim 0 verir; $N_2$ sol uçta sehim 0, eğim 1 verir. Bu özellik sayesinde düğüm değerleri doğrudan fiziksel anlam taşır. Aşağıda dört SD'yi değiştir, kübik eğrinin nasıl biçim aldığını izle.

::: etkilesim kiris-sekil
{"L": 3}
:::

## Rijitlik matrisi

Şekil fonksiyonlarının ikinci türevlerinden eğilme enerjisi yazılır ve şu matris elde edilir:

$$
\mathbf{k}=\frac{EI}{L^3}
\begin{bmatrix}
\kutua{12} & \kutub{6L} & \kutua{-12} & \kutub{6L}\\
\kutub{6L} & \kutuc{4L^2} & \kutub{-6L} & \kutuc{2L^2}\\
\kutua{-12} & \kutub{-6L} & \kutua{12} & \kutub{-6L}\\
\kutub{6L} & \kutuc{2L^2} & \kutub{-6L} & \kutuc{4L^2}
\end{bmatrix}
$$

Mavi hücreler kuvvet–sehim, yeşil hücreler moment–dönme, turuncu hücreler ikisini birbirine bağlayan terimlerdir. Birinci ve üçüncü satırın toplamı sıfırdır: eleman rijit cisim gibi ötelenirse kuvvet doğmaz.

::: not Dönmenin birimi
$\theta$ radyandır ve boyutsuzdur; $6L$ ve $4L^2$ terimlerindeki $L$'ler birimlerin tutmasını sağlar. Matrisin bir kısmı kN/m, bir kısmı kN, bir kısmı kN·m birimindedir.
:::

::: hata Dereceyle dönme girmek
Programdan çıkan $\theta$ değeri radyandır. 0,01 rad yaklaşık 0,57°'dir; derece sanıp yorumlamak eğimi 57 kat küçük gösterir.
:::

## Eşdeğer düğüm yükleri

Rijitlik yöntemi yalnız düğüm kuvvetleriyle çalışır. Eleman üzerindeki yayılı ya da tekil yük, aynı işi yapan **eşdeğer düğüm kuvvetlerine** çevrilir. Düzgün yayılı yük $q$ için:

$$
\mathbf{f}_{eş}=\Big[\ \ka{\tfrac{qL}{2}},\ \ \kb{\tfrac{qL^2}{12}},\ \ \ka{\tfrac{qL}{2}},\ \ \kb{-\tfrac{qL^2}{12}}\ \Big]^T
$$

Ortadan tekil yük $P$ için $[\,P/2,\ PL/8,\ P/2,\ -PL/8\,]^T$ olur. Aşağıda yükün yerini ve büyüklüğünü değiştir, dört düğüm kuvvetinin nasıl paylaştığını izle.

::: etkilesim esdeger-yuk
{"q": 10, "L": 4, "P": 20, "a": 1.5}
:::

::: hata Yalnız kuvvetleri aktarıp momentleri unutmak
$qL/2$'leri düğümlere koyup $\pm qL^2/12$'yi atlarsan dönmeler ve uç momentleri yanlış çıkar. Basit kirişte orta sehim de bozulur.
:::

::: uyari Eleman momentleri: süperpozisyon
Düğüm değerleri eşdeğer yükle **kesin** çıkar. Ama eleman içindeki moment, düğümlerden bulunan uç kuvvetlerine **ankastre uç kuvvetlerinin** eklenmesiyle hesaplanır. Program bunu senin yerine yapar; elle yaparken bu adımı atlama.
:::

## Kesme ve moment diyagramı

Uç kuvvetleri $\mathbf{f}=\mathbf{k}\mathbf{u}-\mathbf{f}_{eş}$ bulununca eleman boyunca $V(x)$ ve $M(x)$ çizilir. Aşağıda mesnet tipini ve yükü değiştir; tepkileri ve en büyük momenti izle.

::: etkilesim kiris-nvm
{"L": 6, "P": 0, "a": 3, "q": 12, "mesnet": "basit"}
:::

## Çözümlü örnekler

::: ornek Sayısal kiriş matrisi
$E=200$ GPa ($200\times10^6$ kN/m²), $I=8\times10^{-6}$ m⁴, $L=3$ m. Eleman matrisini kur.
--- ipucu
$EI=1600$ kN·m². $12EI/L^3=19200/27$, $6EI/L^2=9600/9$.
--- cevap
$k_{11}=6400/9$, $k_{12}=3200/3$, $k_{22}=6400/3$, $k_{24}=3200/3$.
--- kod
mo.kiris_eleman("200e6", "8e-6", 3)
--- kontrol
r.deger[0, 0] == sp.Rational(6400, 9) and r.deger[1, 1] == sp.Rational(6400, 3) and r.deger[1, 3] == sp.Rational(3200, 3)
--- yorum
$k_{22}=2k_{24}$: uzak ucu tutulu bir kirişin ucunu döndürmek, uzak uçta yarısı kadar moment doğurur. Bu, Cross yönteminin taşıma katsayısı $1/2$'dir.
:::

::: ornek Simgesel kiriş matrisi
$E$, $I$, $L$ simge olarak kalsın. Matrisi kur, iki özelliği denetle.
--- ipucu
Birinci satırın toplamı ve $k_{22}/k_{24}$ oranı.
--- cevap
$k_{11}=12EI/L^3$. $k_{11}+k_{13}=0$, $k_{22}/k_{24}=2$.
--- kod
mo.kiris_eleman()
--- kontrol
sp.simplify(r.deger[0, 0] + r.deger[0, 2]) == 0 and sp.simplify(r.deger[1, 1] / r.deger[1, 3]) == 2
--- yorum
Formül tablolarına bakmadan doğrudan bu simgesel matristen okuyabilirsin.
:::

::: ornek Konsol kiriş: elle çözüm
Aynı eleman ($L=3$, $EI=1600$) sol uçtan ankastre, sağ uca $P=-10$ kN. Uç sehim ve dönmesini bul.
--- ipucu
Ankastre uçta $v_1=\theta_1=0$: SD 1 ve 2 silinir. $\mathbf{F}=[0,0,-10,0]^T$.
--- cevap
$v_2=-9/160$ m, $\theta_2=-9/320$ rad. Formül: $PL^3/3EI=270/4800=9/160$.
--- kod
K = mo.kiris_eleman("200e6", "8e-6", 3)
K, mo.sinir_kosulu(K.deger, "0; 0; -10; 0", sabit=[1, 2])
--- kontrol
r[-1].deger[2] == sp.Rational(-9, 160) and r[-1].deger[3] == sp.Rational(-9, 320)
--- yorum
Tek elemanla **kesin** sonuç. Kübik şekil fonksiyonu, uçtan yüklü konsolun gerçek eğrisiyle aynıdır.
:::

::: ornek Konsol kiriş: hazır model ve tepkiler
Aynı konsolu hazır `kiris-konsol` modeliyle çöz. Mesnet tepkilerini ve en büyük momenti oku.
--- ipucu
$R_y=10$ kN, $M=PL=30$ kN·m.
--- cevap
$v_2=-9/160$; tepki $F_y=10$, $M=30$; ankastre uçta $M_{max}=-30$ kN·m.
--- kod
se.se_coz(se.ornek_model("kiris-konsol"))
--- kontrol
r.deger[2] == sp.Rational(-9, 160) and abs(r.veri["tepkiler"][0]["M"] - 30) < 1e-9 and abs(max(r.veri["elemanlar"][0]["diyagram"]["M"], key=abs) + 30) < 1e-6
--- yorum
Momentin işareti programın kuralına göredir: konsolda üst lif çekmede olduğundan negatif çıkar.
:::

::: ornek Yayılı yüklü konsol: eşdeğer yükle elle
$L=2$ m, $E=200$ GPa, $I=10^{-5}$ m⁴, konsol, $q=-6$ kN/m. Eşdeğer düğüm yüklerini yaz ve çöz.
--- ipucu
$qL/2=-6$, $qL^2/12=-2$. $\mathbf{f}_{eş}=[-6,\ -2,\ -6,\ 2]^T$. SD 1 ve 2 tutulu.
--- cevap
$v_2=-3/500$ m, $\theta_2=-1/250$ rad. Formül $qL^4/8EI=96/16000=3/500$ ile aynı.
--- kod
K = mo.kiris_eleman("200e6", "1e-5", 2)
K, mo.sinir_kosulu(K.deger, "-6; -2; -6; 2", sabit=[1, 2])
--- kontrol
r[-1].deger[2] == sp.Rational(-3, 500) and r[-1].deger[3] == sp.Rational(-1, 250)
--- yorum
Eşdeğer yük yöntemi düğüm değerlerini kesin verir. Ankastre uçtaki tepki momenti ise $\mathbf{K}\mathbf{u}-\mathbf{f}_{eş}$ ile bulunur: $qL^2/2=12$ kN·m.
:::

::: ornek Yayılı yüklü basit kiriş
Hazır `kiris-basit-yayili`: $L=6$ m (iki eleman), $q=-12$ kN/m, $EI=4000$. Orta sehimi, tepkileri ve $M_{max}$'ı bul.
--- ipucu
$5qL^4/384EI$ ve $qL^2/8$.
--- cevap
$v_{orta}=-81/1600$ m, $R_1=R_3=36$ kN, $M_{max}=54$ kN·m.
--- kod
se.se_coz(se.ornek_model("kiris-basit-yayili"))
--- kontrol
r.deger[2] == sp.Rational(-81, 1600) and abs(r.veri["tepkiler"][0]["Fy"] - 36) < 1e-9 and abs(max(r.veri["elemanlar"][0]["diyagram"]["M"], key=abs) - 54) < 1e-6
--- yorum
Simetri gereği orta düğümde dönme sıfır, uçlarda $\mp27/1000$ rad çıkar.
:::

::: ornek Ortadan tekil yüklü basit kiriş
$L=4$ m, iki eleman, $EI=2000$, ortaya $P=-20$ kN. Modeli kendin kur ve çöz.
--- ipucu
Düğümler $x=0,2,4$; mesnetler düğüm 1 ve 3'te yalnız $v$ tutulu.
--- cevap
$v_{orta}=-1/75$ m ($PL^3/48EI=1280/96000$), $M_{max}=PL/4=20$ kN·m.
--- kod
model = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 2}, {"no": 3, "x": 4}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "1e-5"}, {"no": 2, "dugumler": [2, 3], "E": "200e6", "I": "1e-5"}], "mesnetler": [{"dugum": 1, "uy": True}, {"dugum": 3, "uy": True}], "yukler": [{"dugum": 2, "Fy": -20}]}
se.se_coz(model)
--- kontrol
r.deger[2] == sp.Rational(-1, 75) and r.deger[1] == sp.Rational(-1, 100)
--- yorum
Kendi modelini sözlük olarak yazmak, ileride köprü modelini kurmanın ilk adımıdır.
:::

::: ornek Hiperstatik kiriş: ankastre–kayıcı
Hazır `kiris-ankastre-mafsalli`: $L=4$ m, $q=-10$ kN/m, $EI=4000$. Tepkileri ve mafsallı uçtaki dönmeyi bul.
--- ipucu
Klasik sonuç: $R_A=5qL/8$, $R_B=3qL/8$, $M_A=qL^2/8$.
--- cevap
$R_1=25$, $R_2=15$ kN, $M_1=20$ kN·m, $\theta_2=1/300$ rad.
--- kod
se.se_coz(se.ornek_model("kiris-ankastre-mafsalli"))
--- kontrol
r.deger[3] == sp.Rational(1, 300) and abs(r.veri["tepkiler"][1]["Fy"] - 15) < 1e-9 and abs(r.veri["tepkiler"][0]["M"] - 20) < 1e-9
--- yorum
Bir kez hiperstatik bir kiriş. Kuvvet yönteminde uygunluk denklemi yazman gerekirdi; burada tek bir $2\times2$ çözüm yeter.
:::

::: ornek Şekil fonksiyonunu yorumlamak
$\xi=1/2$'de $N_1$ ve $N_3$ kaçtır? Sol düğüm 1 cm aşağı inerse ve başka hiçbir şey değişmezse eleman ortası ne kadar iner?
--- ipucu
$N_1(1/2)=1-3/4+2/8$.
--- cevap
$N_1(1/2)=N_3(1/2)=1/2$. Orta nokta $0{,}5$ cm iner.
--- yorum
$N_1+N_3=1$ her $\xi$ için sağlanır: iki uç birlikte 1 cm inerse eleman rijit olarak 1 cm ötelenir.
:::

::: muhendislik Taş kemer köprüde kiriş elemanı
Tarihi köprünün tabliyesini ve kemerini ilk yaklaşımda kiriş elemanlarıyla modellemek, katı modelden önce frekans mertebesini görmenin hızlı yoludur. Kemeri 10–20 kiriş elemanına bölmek ilk birkaç modu iyi yakalar.

Yığma malzeme çekmeyi taşımaz. Kiriş modelinden çıkan momentlerin $M/N$ oranı, itki çizgisinin kesit dışına çıkıp çıkmadığını gösteren basit ama değerli bir denetimdir.
:::

::: ozet Özet
- Kiriş düğümünde iki SD: $v$ ve $\theta$; eleman $4\times4$.
- Hermite fonksiyonları kübiktir; uçtan yüklü kirişte tek eleman kesin sonuç verir.
- $\mathbf{k}$'nin terimleri: $12EI/L^3$, $6EI/L^2$, $4EI/L$, $2EI/L$.
- Yayılı yük: $[qL/2,\ qL^2/12,\ qL/2,\ -qL^2/12]$; momentleri unutma.
- Uç kuvvetleri: $\mathbf{f}=\mathbf{k}\mathbf{u}-\mathbf{f}_{eş}$.
:::

## Alıştırma

Kiriş elemanlarının birleştirilmesi ve mesnetlenmesi, önceki iki dersteki kurallarla aynıdır.

::: alistirma birlestir
{"zorluk": 2}
:::

::: alistirma sinir-kosulu
{"zorluk": 2}
:::
