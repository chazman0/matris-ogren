---
baslik: Eksenel çubuk elemanı
bolum: se
ozet: Şekil fonksiyonları, birim şekil değiştirme, gerilme ve k = EA/L; çubuk aslında bir yaydır.
sure: 40
---

## Neden?

Bir çubuğu ucundan çektiğinde biraz uzar, bıraktığında geri döner. Yani çubuk bir **yaydır**; yalnız yay katsayısını malzeme ve kesitten hesaplarız. Kafes köprülerin bütün elemanları, kemerlerin basınç çizgisi ve gergi çubukları bu davranışla modellenir. Bu derste $k=EA/L$ formülünün nereden geldiğini, eleman içinde yer değiştirmenin nasıl dağıldığını ve gerilmenin nasıl bulunduğunu göreceksin.

## Çubuk bir yaydır

Uzunluğu $L$, kesit alanı $A$, elastisite modülü $E$ olan çubuğa $P$ kuvveti uygulayalım. Mukavemetten bildiğin uzama $\delta=PL/(EA)$ idi. Bunu $P=(EA/L)\,\delta$ diye yazınca yay denklemi çıkar.

::: tanim Eksenel çubuk elemanı
Yalnız kendi ekseni boyunca kuvvet taşıyan, iki düğümlü elemandır. Her düğümde bir SD vardır: eksen boyunca yer değiştirme $u$. Rijitliği $k=EA/L$ olan bir yay gibi davranır.
:::

$$
k=\kutua{\frac{EA}{L}}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}
$$

::: uyari Birimleri tek sistemde tut
Bu uygulamada kuvvet kN, uzunluk m kullanılır. Çelik için $E=200$ GPa $=200\times10^6$ kN/m² yazılır. MPa ile m² karıştırmak sonucu bin kat yanlış verir.
:::

## Şekil fonksiyonları

Düğümlerde $u_1$ ve $u_2$ biliniyorsa eleman içinde ne olur? En basit kabul, yer değiştirmenin **doğrusal** değişmesidir. Bunu iki ağırlık fonksiyonuyla yazarız.

$$
u(x)=\ka{N_1(x)}\,u_1+\kb{N_2(x)}\,u_2,
\qquad
\ka{N_1}=1-\frac{x}{L},\quad \kb{N_2}=\frac{x}{L}
$$

::: tanim Şekil fonksiyonu
**Şekil fonksiyonu** (shape function) $N_i$, kendi düğümünde 1, öteki düğümde 0 olan fonksiyondur. Düğüm değerlerini eleman içine yayar. Her noktada $N_1+N_2=1$ olur; bu sayede rijit kayma doğru temsil edilir.
:::

::: sekil Doğrusal şekil fonksiyonları
<svg viewBox="0 0 400 170" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<path d="M40 130 H360 M40 140 V25" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1" fill="none"/>
<path d="M40 40 H36 M40 130 H36" stroke="var(--sema-cizgi,#94a3b8)"/>
<text x="30" y="44" text-anchor="end">1</text>
<text x="30" y="134" text-anchor="end">0</text>
<path class="ok" pathLength="1" d="M40 40 L340 130" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="3"/>
<path class="ok" pathLength="1" d="M40 130 L340 40" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="3"/>
<circle cx="40" cy="130" r="6" fill="var(--sema-cizgi,#94a3b8)"/>
<circle cx="340" cy="130" r="6" fill="var(--sema-cizgi,#94a3b8)"/>
<text x="80" y="38" fill="var(--sema-a,#3b82f6)">N₁ = 1 − x/L</text>
<text x="250" y="38" fill="var(--sema-b,#f59e0b)">N₂ = x/L</text>
<path class="vurgu" d="M190 130 V85" stroke="var(--sema-c,#10b981)" stroke-width="2" stroke-dasharray="4 3"/>
<text x="196" y="100" fill="var(--sema-c,#10b981)">ortada ikisi de 1/2</text>
<text x="40" y="155" text-anchor="middle">düğüm 1</text>
<text x="340" y="155" text-anchor="middle">düğüm 2</text>
<text x="365" y="134">x</text>
</svg>
:::

Uç yer değiştirmelerini kendin oynat. Çubuğun içindeki her noktanın nasıl doğrusal kaydığını ve gerilmenin nasıl değiştiğini izle.

::: etkilesim cubuk-sekil
{"E": 200000000, "A": 0.001, "L": 2, "P": 100}
:::

## Birim şekil değiştirme ve gerilme

**Birim şekil değiştirme** (strain), yer değiştirmenin $x$'e göre türevidir. Doğrusal $u(x)$'in türevi sabittir, yani eleman boyunca $\varepsilon$ ve $\sigma$ sabit kalır.

$$
\varepsilon=\frac{du}{dx}=\frac{\kb{u_2}-\ka{u_1}}{L},
\qquad
\sigma=E\varepsilon,
\qquad
N=\sigma A=\kutuc{\frac{EA}{L}}(\kb{u_2}-\ka{u_1})
$$

Adımlar her zaman aynı sıradadır: önce düğüm yer değiştirmeleri, sonra $\varepsilon$, sonra $\sigma$, en son eksenel kuvvet $N$. Pozitif $N$ **çekme**, negatif $N$ **basınç** demektir.

::: hata Gerilmeyi düğümde aramak
Yer değiştirme düğümde bulunur, gerilme ise **eleman içinde** tanımlıdır. Bu elemanda gerilme baştan sona sabittir; "düğüm 2'deki gerilme" diye bir şey sorulmaz. Kademeli çubukta iki elemanın gerilmesi farklı çıkar ve düğümde sıçrar.
:::

## Kademeli çubuk: çubuklar seri yaydır

Kesiti yarı yolda değişen çubuğu iki elemana böleriz. Her elemanın kendi $EA/L$ değeri vardır; birleştirme yaylardaki gibidir. Aşağıda kademeli çubuğun iki yay gibi çalıştığını görüyorsun: $k_1=400\,000$, $k_2=200\,000$ kN/m.

::: etkilesim yay-sistemi
{"k": [400000, 200000], "P": 100, "duzen": "seri"}
:::

::: hata Toplam boyu her elemanda kullanmak
Çubuğu iki elemana böldüysen her elemanın $L$'si **kendi boyudur**. Toplam boy 2 m, eleman boyu 1 m ise $k=EA/1$ yazılır, $EA/2$ değil.
:::

## Çözümlü örnekler

::: ornek Çubuk elemanının matrisi
$E=200\times10^6$ kN/m², $A=0.001$ m², $L=2$ m. Eleman rijitlik matrisini bul.
--- ipucu
$EA/L=200\times10^6\cdot 0.001/2$.
--- cevap
$EA/L=100\,000$ kN/m.
$$
k=\begin{bmatrix}100000&-100000\\-100000&100000\end{bmatrix}
$$
--- kod
mo.cubuk_eleman("200e6", "0.001", 2)
--- kontrol
r.deger == sp.Matrix([[100000, -100000], [-100000, 100000]])
--- yorum
Bu çubuk, $100\,000$ kN/m'lik bir yay ile aynıdır: 1 mm uzatmak için 100 kN gerekir.
:::

::: ornek Simgesel matris
$E$, $A$, $L$ harf olarak kalsın. Matrisi simgesel yazdır ve satır toplamının sıfır olduğunu gör.
--- ipucu
Fonksiyona harfleri metin olarak ver.
--- cevap
$$
k=\begin{bmatrix}\dfrac{EA}{L}&-\dfrac{EA}{L}\\-\dfrac{EA}{L}&\dfrac{EA}{L}\end{bmatrix}
$$
--- kod
mo.cubuk_eleman("E", "A", "L")
--- kontrol
r.deger.shape == (2, 2) and sp.simplify(r.deger[0, 0] + r.deger[0, 1]) == 0
--- yorum
Formülün kendisini görmek, sayılara geçmeden önce hangi parametrenin neyi değiştirdiğini anlamaya yarar. $E$ ya da $A$ iki katına çıkarsa rijitlik de iki katına çıkar; $L$ iki katına çıkarsa yarıya iner.
:::

::: ornek Şekil fonksiyonuyla ara nokta
$L=2$ m'lik elemanda $u_1=0$, $u_2=0.004$ m. $x=0.5$ m'deki yer değiştirme nedir?
--- ipucu
$N_1(0.5)=1-0.5/2=0.75$, $N_2(0.5)=0.25$. Satır vektörü ile sütun vektörünü çarp.
--- cevap
$u(0.5)=0.75\cdot 0+0.25\cdot 0.004=0.001$ m.
--- kod
mo.carp("3/4 1/4", "0; 4/1000")
--- kontrol
r.deger == sp.Matrix([[sp.Rational(1, 1000)]])
--- yorum
Şekil fonksiyonu satırı $[N_1\ N_2]$ ile düğüm vektörünün çarpımı, sonlu elemanın en temel işlemidir. Kirişte aynı şey dört terimle yapılır.
:::

::: ornek Tek çubuk, ucundan çekme
Yukarıdaki çubuk sol ucundan sabit, sağ ucundan $P=100$ kN ile çekiliyor. Uç yer değiştirmesini, gerilmeyi ve tepkiyi bul.
--- ipucu
Tek bilinmeyen $u_2$: $100\,000\,u_2=100$.
--- cevap
$u_2=0.001$ m $=1$ mm. $\sigma=100/0.001=100\,000$ kN/m² $=100$ MPa (çekme). $R_1=-100$ kN.
--- kod
model = {"tip": "cubuk", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 2}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.001"}], "mesnetler": [{"dugum": 1, "ux": True}], "yukler": [{"dugum": 2, "Fx": 100}]}
se.se_coz(model)
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(1, 1000)]) and abs(r.veri["elemanlar"][0]["N"] - 100) < 1e-9
--- yorum
Mukavemetteki $\delta=PL/EA=100\cdot2/200\,000=0.001$ m ile birebir aynı. Tek elemanlı çubukta sonlu eleman tam sonuç verir.
:::

::: ornek Kademeli çubuk
Hazır `cubuk-kademeli` modeli: iki 1 m'lik parça, $A_1=0.002$, $A_2=0.001$ m², uca 100 kN çekme. Yer değiştirmeleri ve iki gerilmeyi bul.
--- ipucu
$k_1=400\,000$, $k_2=200\,000$ kN/m. Kuvvet iki parçada da 100 kN'dur.
--- cevap
$u_2=100/400\,000=0.00025$ m, $u_3=0.00025+100/200\,000=0.00075$ m. $\sigma_1=50$ MPa, $\sigma_2=100$ MPa.
--- kod
se.se_coz(se.ornek_model("cubuk-kademeli"))
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(1, 4000), sp.Rational(3, 4000)])
--- yorum
Kuvvet aynı ama ince parça iki kat gerilme taşır ve iki kat uzar. Düğüm 2'de gerilme 50 MPa'dan 100 MPa'ya sıçrar.
:::

::: ornek İki ucu ankastre çubuk, ortadan yük
1 m'lik iki eşit elemandan oluşan çubuğun iki ucu tutulu, ortadaki düğüme $60$ kN eksenel yük geliyor. $E=200\times10^6$, $A=0.001$.
--- ipucu
Her elemanın $k=200\,000$ kN/m. Tek bilinmeyen $u_2$: $400\,000\,u_2=60$.
--- cevap
$u_2=0.00015$ m. Sol eleman $+30$ kN çekme, sağ eleman $-30$ kN basınç. Tepkiler $-30$ ve $-30$ kN.
--- kod
model = {"tip": "cubuk", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 1}, {"no": 3, "x": 2}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "A": "0.001"}, {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.001"}], "mesnetler": [{"dugum": 1, "ux": True}, {"dugum": 3, "ux": True}], "yukler": [{"dugum": 2, "Fx": 60}]}
se.se_coz(model)
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(3, 20000), 0]) and r.veri["elemanlar"][1]["N"] < 0
--- yorum
Denge denklemi tek başına yetmez: iki bilinmeyen tepki, bir denklem. Rijitlik yöntemi uyumu da kullandığı için hiperstatik çubuğu sorunsuz çözer.
:::

::: ornek Uç yer değiştirmesinden gerilme
$L=2$ m'lik çelik elemanda $u_1=0.0005$ m, $u_2=0.0015$ m bulunmuş. $\varepsilon$, $\sigma$ ve $N$ nedir? ($A=0.001$ m²)
--- ipucu
$\varepsilon=(u_2-u_1)/L$.
--- cevap
$\varepsilon=0.001/2=0.0005$. $\sigma=200\times10^6\cdot0.0005=100\,000$ kN/m² $=100$ MPa. $N=100$ kN çekme.
--- yorum
Eleman ötelenmiş ($u_1\ne0$) ama gerilme yalnız **farka** bağlı. Rijit kayma gerilme üretmez.
:::

::: ornek Elemanı bölmek sonucu değiştirir mi?
Ucundan yüklü, kesiti sabit bir çubuğu 1, 2 ve 4 elemana bölüyorsun. Uç yer değiştirmesi değişir mi?
--- ipucu
Kuvvet çubuk boyunca sabit; gerçek $u(x)$ zaten doğrusal.
--- cevap
Değişmez. Gerçek çözüm doğrusal olduğu için doğrusal şekil fonksiyonu onu tam yakalar. Yalnız ara düğümlerde ek bilgi elde edersin.
--- yorum
Kendi ağırlığı gibi yayılı eksenel yük olsaydı gerçek $u(x)$ ikinci derece olurdu. O zaman eleman sayısı arttıkça sonuç gerçeğe yaklaşır; buna **ağ yakınsaması** denir.
:::

::: muhendislik Taş kemerde eksenel kuvvet
Yığma köprü kemerleri çoğunlukla **basınç** çalışır; taşın çekme dayanımı neredeyse sıfırdır. Bir modelde çekme çıkan bölge çatlak adayıdır. Tarihi köprülerde zamanla eklenen demir gergi çubukları da tam bu dersteki eksenel elemanlardır.

OMA tarafında, boyuna titreşim modları eksenel rijitliğe ($EA$) duyarlıdır. Ölçülen boyuna frekans modelden yüksekse, modeldeki $E$ ya da bağlantı rijitliği büyük olasılıkla küçük seçilmiştir.
:::

::: ozet Özet
- Çubuk elemanı bir yaydır: $k=\dfrac{EA}{L}\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$.
- Şekil fonksiyonları $N_1=1-x/L$, $N_2=x/L$; düğüm değerlerini eleman içine doğrusal yayar.
- $\varepsilon=(u_2-u_1)/L$, $\sigma=E\varepsilon$, $N=\sigma A$; eleman boyunca sabittir.
- Pozitif $N$ çekme, negatif $N$ basınçtır.
- Kademeli çubuk, rijitlikleri farklı seri yaylar gibi birleştirilir.
:::

## Alıştırma

::: alistirma cubuk-k
{"zorluk": 1}
:::

::: alistirma cubuk-k
{"zorluk": 2}
:::
