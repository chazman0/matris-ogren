---
baslik: Yay sistemleri
bolum: se
ozet: İlk sonlu eleman; düğüm, eleman, serbestlik derecesi, yay matrisi, birleştirme ve mesnet.
sure: 40
---

## Neden?

Sonlu eleman yöntemi ilk bakışta korkutucu görünür, ama özünde **yaylardan** ibarettir. Bir çubuk eksenel bir yaydır, bir kiriş eğilen bir yaydır, koca bir köprü de binlerce küçük yayın birleşimidir. Bu derste tek bir yay elemanını tanıyacak, iki yayı birleştirip ilk sonlu eleman çözümünü kendin yapacaksın. Sonraki bütün dersler aynı tarifi tekrar eder.

## Düğüm, eleman, serbestlik

Yapıyı küçük parçalara bölüyoruz. Parçalar uçlarından birbirine bağlanır.

::: tanim Düğüm, eleman ve serbestlik derecesi
**Düğüm** (node), parçaların birleştiği noktadır. **Eleman** (element), iki düğüm arasındaki parçadır. Bir düğümün yapabildiği her bağımsız hareket bir **serbestlik derecesidir** (SD; degree of freedom). Yay sisteminde her düğüm yalnız sağa sola kayar, yani düğüm başına 1 SD vardır.
:::

::: sekil Seri bağlı iki yay: 3 düğüm, 2 eleman, 3 SD
<svg viewBox="0 0 400 150" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<g stroke="var(--sema-cizgi,#94a3b8)" stroke-width="2">
<path d="M30 40 V110"/>
<path d="M30 50 L20 60 M30 65 L20 75 M30 80 L20 90 M30 95 L20 105"/>
</g>
<polyline points="30,75 60,75 70,60 85,90 100,60 115,90 130,60 140,75 180,75" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="3"/>
<polyline points="200,75 230,75 240,60 255,90 270,60 285,90 300,60 310,75 340,75" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="3"/>
<circle cx="30" cy="75" r="7" fill="var(--sema-cizgi,#94a3b8)"/>
<circle cx="190" cy="75" r="7" fill="var(--sema-c,#10b981)"/>
<circle cx="350" cy="75" r="7" fill="var(--sema-cizgi,#94a3b8)"/>
<path d="M180 75 H200" stroke="var(--sema-c,#10b981)" stroke-width="3"/>
<text x="100" y="45" text-anchor="middle" fill="var(--sema-a,#3b82f6)">eleman 1, k₁</text>
<text x="270" y="45" text-anchor="middle" fill="var(--sema-b,#f59e0b)">eleman 2, k₂</text>
<text x="30" y="132" text-anchor="middle">düğüm 1</text>
<text x="190" y="132" text-anchor="middle" fill="var(--sema-c,#10b981)">düğüm 2</text>
<text x="350" y="132" text-anchor="middle">düğüm 3</text>
<path class="ok" pathLength="1" d="M355 100 H390" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<polyline class="ok-uc" points="383,95 390,100 383,105" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<text x="372" y="118" text-anchor="middle">P</text>
<text x="190" y="20" text-anchor="middle">ortak düğüm iki elemana da aittir</text>
</svg>
:::

## Bir yay elemanının matrisi

Yayın sol ucu $u_1$, sağ ucu $u_2$ kadar kaysın. Yay $u_2-u_1$ kadar uzar ve iki ucuna eşit, zıt kuvvet uygular:

$$
f_1=k(u_1-u_2),\qquad f_2=k(u_2-u_1)
$$

Bu iki denklemi matrisle yazınca **eleman rijitlik matrisi** ortaya çıkar. Köşegen artı, köşegen dışı eksidir; her satırın toplamı sıfırdır.

$$
\begin{bmatrix}f_1\\f_2\end{bmatrix}=
\kutua{\begin{bmatrix}k&-k\\-k&k\end{bmatrix}}
\begin{bmatrix}u_1\\u_2\end{bmatrix}
$$

::: not Satır toplamı neden sıfır?
İki ucu aynı miktarda kaydırırsan yay uzamaz, kuvvet de oluşmaz. Bu **rijit cisim hareketi**dir ve matrisi $[1,1]$ vektörüyle çarpınca sıfır çıkmasının sebebidir.
:::

Aşağıdaki çizimde yay katsayılarını ve yükü değiştir. Her yayın 2×2 matrisi kendi renginde, büyük $K$ içinde düştüğü yere yerleşir.

::: etkilesim yay-sistemi
{"k": [1000, 2000], "P": 10, "duzen": "seri"}
:::

## Birleştirme: küçük matrisleri büyüğe yerleştirmek

Her eleman matrisi, bağlandığı düğümlerin satır ve sütunlarına eklenir. Eleman 1 düğüm 1 ve 2'ye, eleman 2 düğüm 2 ve 3'e bağlıdır. Ortak düğüm 2'nin köşegen hücresine **iki eleman birden** katkı verir.

$$
K=\begin{bmatrix}
\ka{k_1}&\ka{-k_1}&0\\
\ka{-k_1}&\kutuc{k_1+k_2}&\kb{-k_2}\\
0&\kb{-k_2}&\kb{k_2}
\end{bmatrix}
$$

Mavi kısım eleman 1, turuncu kısım eleman 2'dir. Yeşil kutuda iki renk üst üste gelir ve toplanır. Birbirine bağlı olmayan düğüm 1 ile 3'ün hücresi sıfır kalır.

::: hata Ortak düğümde toplamayı unutmak
İkinci elemanı yerleştirirken $K_{22}$ hücresine $k_2$ yazıp $k_1$'i silmek en sık hatadır. Birleştirme **üzerine yazma değil, ekleme**dir. Doğrusu $K_{22}=k_1+k_2$.
:::

Aynı iki yayı yan yana, yani **paralel** bağlayınca ne değişir? İkisi de aynı iki düğüme bağlanır, bütün katkılar aynı dört hücreye düşer.

::: etkilesim yay-sistemi
{"k": [1000, 2000], "P": 30, "duzen": "paralel"}
:::

## Mesnet ve çözüm

Hiç mesnet yoksa sistem havada süzülür ve $\det K=0$ olur; çözüm yoktur. Düğüm 1'i duvara bağlayınca $u_1=0$ olur. Bu SD'nin satır ve sütununu siliyoruz, kalan küçük sistemi çözüyoruz.

$$
\begin{bmatrix}
\ksil{k_1}&\ksil{-k_1}&\ksil{0}\\
\ksil{-k_1}&k_1+k_2&-k_2\\
\ksil{0}&-k_2&k_2
\end{bmatrix}
\quad\Rightarrow\quad
\begin{bmatrix}k_1+k_2&-k_2\\-k_2&k_2\end{bmatrix}
\begin{bmatrix}u_2\\u_3\end{bmatrix}=
\begin{bmatrix}0\\P\end{bmatrix}
$$

Silinen satır boşa gitmez. Bulunan $u$ değerlerini oraya koyunca **mesnet tepkisi** çıkar: $R_1=-k_1u_2$.

::: hata Mesnetsiz sistemi çözmeye çalışmak
Mesnet koymadan $K\mathbf{u}=\mathbf{F}$ çözülmez, çünkü $K$ tekildir. Programda bu, "matris tekil" hatası ya da çok büyük, anlamsız yer değiştirmeler olarak görünür. Önce rijit cisim hareketini engelleyecek kadar mesnet koy.
:::

## Seri ve paralel kısa yolu

İki yay için birleştirme sonucu bildik formüllerle aynıdır:

$$
\text{seri: }\frac{1}{k_{eş}}=\frac{1}{k_1}+\frac{1}{k_2}
\qquad
\text{paralel: }k_{eş}=k_1+k_2
$$

::: ipucu Hangisi hangisi?
Seri yaylarda **kuvvet aynı**, uzamalar toplanır. Paralel yaylarda **uzama aynı**, kuvvetler toplanır. Rijitlik matrisi bu ikisini ayrıca düşünmeden kendiliğinden doğru yapar.
:::

## Çözümlü örnekler

::: ornek Tek yay elemanının matrisi
$k=500$ kN/m olan yay elemanının rijitlik matrisini yaz.
--- ipucu
Kalıp $\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$, önüne $k$ gelir.
--- cevap
$$
k=\begin{bmatrix}500&-500\\-500&500\end{bmatrix}\ \text{kN/m}
$$
--- kod
mo.skaler(500, "1 -1; -1 1")
--- kontrol
r.deger == sp.Matrix([[500, -500], [-500, 500]])
--- yorum
Satır toplamları sıfır, matris simetrik. Her yay elemanı bu iki özelliği taşır.
:::

::: ornek İki yayı birleştir
$k_1=1000$ kN/m eleman 1–2 düğümleri, $k_2=2000$ kN/m eleman 2–3 düğümleri arasında. Global $K$ matrisini kur.
--- ipucu
Eleman 1'i satır ve sütun 1, 2'ye; eleman 2'yi 2, 3'e ekle. $K_{22}$ iki katkı alır.
--- cevap
$$
K=\begin{bmatrix}1000&-1000&0\\-1000&\kutuc{3000}&-2000\\0&-2000&2000\end{bmatrix}
$$
--- kod
mo.birlestir([("1000 -1000; -1000 1000", [1, 2]), ("2000 -2000; -2000 2000", [2, 3])], 3)
--- kontrol
r.deger == sp.Matrix([[1000, -1000, 0], [-1000, 3000, -2000], [0, -2000, 2000]])
--- yorum
Çözümde her elemanın hangi hücreye düştüğü renkli kutularla gösterilir. $K_{13}=0$, çünkü 1 ile 3 doğrudan bağlı değil.
:::

::: ornek Mesneti uygula ve çöz
Aynı sistemde düğüm 1 sabit, düğüm 3'e $P=10$ kN çekme var. Yer değiştirmeleri bul.
--- ipucu
1. satır ve sütunu sil: $\begin{bmatrix}3000&-2000\\-2000&2000\end{bmatrix}\begin{bmatrix}u_2\\u_3\end{bmatrix}=\begin{bmatrix}0\\10\end{bmatrix}$.
--- cevap
$u_2=0.01$ m, $u_3=0.015$ m. Tepki $R_1=-10$ kN.
--- kod
K = mo.birlestir([("1000 -1000; -1000 1000", [1, 2]), ("2000 -2000; -2000 2000", [2, 3])], 3).deger
mo.sinir_kosulu(K, "0; 0; 10", sabit=[1])
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(1, 100), sp.Rational(3, 200)])
--- yorum
Yay 1 $10/1000=0.01$ m, yay 2 $10/2000=0.005$ m uzar. Uzamalar üst üste eklenir: $0.015$ m.
:::

::: ornek Aynı soruyu sonlu eleman çözücüsüyle
Hazır `yay-seri` modelini çözücüye ver; düğüm yer değiştirmelerini ve tepkiyi oku.
--- ipucu
Çözücü modeli düğüm, eleman, mesnet ve yük tablolarıyla alır; bütün adımları sırayla gösterir.
--- cevap
$\mathbf{u}=[0,\ 0.01,\ 0.015]$ m, $R_1=-10$ kN.
--- kod
se.se_coz(se.ornek_model("yay-seri"))
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(1, 100), sp.Rational(3, 200)])
--- yorum
Elle bulduğunla aynı. Çözücü ayrıca her yayın kuvvetini (10 kN çekme) ve denge kontrolünü de yazar.
:::

::: ornek Paralel iki yay
$k_1=1000$ ve $k_2=2000$ kN/m olan iki yay aynı düğümler (1 ve 2) arasında. Düğüm 1 sabit, düğüm 2'ye $30$ kN. $u_2$ nedir?
--- ipucu
İki eleman da $[1,2]$ SD'lerine yerleşir; $K_{22}=3000$ olur.
--- cevap
$u_2=30/3000=0.01$ m.
--- kod
K = mo.birlestir([("1000 -1000; -1000 1000", [1, 2]), ("2000 -2000; -2000 2000", [1, 2])], 2).deger
mo.sinir_kosulu(K, "0; 30", sabit=[1])
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(1, 100)])
--- yorum
Uzama ikisinde aynı (0.01 m); kuvvetler $10$ ve $20$ kN diye paylaşılır. Daha rijit yay daha çok yük alır.
:::

::: ornek İki ucu tutulu yay sistemi
Düğüm 1 ve 3 sabit, ortadaki düğüm 2'ye $30$ kN. $k_1=1000$, $k_2=2000$ kN/m. Ortadaki yer değiştirmeyi ve iki tepkiyi bul.
--- ipucu
Yalnız $u_2$ bilinmeyendir: $(k_1+k_2)u_2=30$.
--- cevap
$u_2=0.01$ m. $R_1=-k_1u_2=-10$ kN, $R_3=-k_2u_2=-20$ kN.
--- kod
model = {"tip": "yay", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 1}, {"no": 3, "x": 2}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "k": "1000"}, {"no": 2, "dugumler": [2, 3], "k": "2000"}], "mesnetler": [{"dugum": 1, "ux": True}, {"dugum": 3, "ux": True}], "yukler": [{"dugum": 2, "Fx": 30}]}
se.se_coz(model)
--- kontrol
r.deger == sp.Matrix([0, sp.Rational(1, 100), 0]) and abs(r.veri["tepkiler"][1]["Fx"] + 20) < 1e-9
--- yorum
Yük iki duvara, rijitlikleri oranında dağıldı: 1/3 ve 2/3. Hiperstatik sistemlerde yük her zaman rijit olana yönelir.
:::

::: ornek Eşdeğer rijitlikle sağlama
$k_1=1000$, $k_2=2000$ kN/m seri. Eşdeğer rijitliği bul ve uç yer değiştirmesini $P=10$ kN için hesapla.
--- ipucu
$1/k_{eş}=1/1000+1/2000$.
--- cevap
$k_{eş}=2000/3\approx 666.7$ kN/m; $u_3=10/(2000/3)=0.015$ m.
--- yorum
Matris yöntemiyle bulunan $0.015$ m ile aynı. Kısa yol yalnız basit seri ve paralel düzenlerde işe yarar; matris yöntemi her düzende çalışır.
:::

::: ornek Mesnetsiz sistem
İki yaylı sistemde hiç mesnet yok. $\det K$ nedir, ne anlama gelir?
--- ipucu
$K$'nin satırlarını topla.
--- cevap
Satırların toplamı sıfır vektörüdür, satırlar bağımlıdır, dolayısıyla $\det K=0$. Sistem rijit cisim gibi kayabilir; çözüm tek değildir.
--- yorum
Bu, sonlu eleman programlarındaki "mekanizma" uyarısının matematikteki karşılığıdır.
:::

::: muhendislik Köprüde yaylar
Tarihi taş köprü modelinde zemin çoğu zaman **yaylarla** temsil edilir: ayakların altına düşey ve yatay yaylar konur. Bu yayların rijitliği belirsizdir. OMA ile ölçülen frekanslara uyacak şekilde ayarlanan ilk parametreler genellikle bunlardır.

Model güncellemede yay katsayısını değiştirmek, bu dersteki $K$ matrisinde birkaç hücreyi değiştirmek demektir. Bu yüzden hangi hücrenin hangi elemandan geldiğini bilmek hesap kadar önemlidir.
:::

::: ozet Özet
- Düğüm birleşme noktası, eleman iki düğüm arası parça, SD bağımsız hareket sayısıdır.
- Yay elemanı: $k\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$; simetrik, satır toplamı sıfır.
- Birleştirme: her eleman matrisi kendi SD'lerinin hücrelerine **eklenir**; ortak düğümde katkılar toplanır.
- Mesnet: tutulu SD'nin satır ve sütunu silinir, kalan sistem çözülür, silinen satırdan tepki bulunur.
- Mesnet yoksa $\det K=0$; sistem mekanizmadır.
:::

## Alıştırma

::: alistirma yay-seri
{"zorluk": 1}
:::

::: alistirma birlestir
{"zorluk": 1}
:::
