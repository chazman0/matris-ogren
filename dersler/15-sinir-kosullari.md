---
baslik: Sınır koşulları, çözüm ve mesnet tepkileri
bolum: se
ozet: Tekil K'yı mesnetlerle çözülebilir yapmak; serbest ve tutulu SD bölümlemesi, indirgenmiş sistem, tepki hesabı ve mesnet çökmesi.
sure: 45
---

## Neden?

Bir önceki derste birleştirdiğin $\mathbf{K}$ tekildi: yapı havada asılı gibiydi ve kuvvet uygulayınca bütünüyle kayıp gidebilirdi. Gerçek yapı mesnetlere oturur. Mesnetler bazı yer değiştirmeleri **bilinen** değere (çoğunlukla sıfıra) sabitler; geri kalanlar **bilinmeyen** olarak kalır. Bu ders, $\mathbf{K}\mathbf{u}=\mathbf{F}$ denklemini bu iki gruba ayırıp çözmeyi ve mesnetlerin yapıya ne kadar kuvvet verdiğini bulmayı anlatır.

::: tanim Serbest ve tutulu SD
**Serbest SD** (f): yer değiştirmesi bilinmeyen, yükü bilinen SD.
**Tutulu SD** (s): yer değiştirmesi bilinen (genelde 0), kuvveti yani **tepkisi** bilinmeyen SD.
Her SD'de ya yer değiştirme ya kuvvet bilinir; ikisi birden hiçbir zaman bilinmez.
:::

## Bölümleme

SD'leri önce serbestler, sonra tutulular gelecek şekilde sıralarsak denklem dört bloğa ayrılır:

$$
\begin{bmatrix}\kutua{\mathbf{K}_{ff}} & \kutuc{\mathbf{K}_{fs}}\\ \kutuc{\mathbf{K}_{sf}} & \kutub{\mathbf{K}_{ss}}\end{bmatrix}
\begin{bmatrix}\ka{\mathbf{u}_f}\\ \mathbf{u}_s\end{bmatrix}
=
\begin{bmatrix}\mathbf{F}_f\\ \kb{\mathbf{F}_s+\mathbf{R}}\end{bmatrix}
$$

::: sekil K dört bloğa ayrılır: üst satır çözülür, alt satır tepkiyi verir
<svg viewBox="0 0 420 200" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<rect x="20" y="20" width="100" height="100" fill="var(--sema-a,#3b82f6)" opacity="0.3"/>
<rect x="120" y="20" width="50" height="100" fill="var(--sema-c,#10b981)" opacity="0.3"/>
<rect x="20" y="120" width="100" height="50" fill="var(--sema-c,#10b981)" opacity="0.3"/>
<rect x="120" y="120" width="50" height="50" fill="var(--sema-b,#f59e0b)" opacity="0.3"/>
<path d="M20 20H170V170H20Z M120 20V170 M20 120H170" stroke="var(--sema-cizgi,#94a3b8)" fill="none" stroke-width="1.5"/>
<text x="70" y="74" text-anchor="middle">K_ff</text>
<text x="145" y="74" text-anchor="middle">K_fs</text>
<text x="70" y="149" text-anchor="middle">K_sf</text>
<text x="145" y="149" text-anchor="middle">K_ss</text>
<rect x="185" y="20" width="24" height="100" fill="var(--sema-a,#3b82f6)" opacity="0.3"/>
<rect x="185" y="120" width="24" height="50" fill="none" stroke="var(--sema-cizgi,#94a3b8)"/>
<path d="M185 20H209V120H185Z" stroke="var(--sema-cizgi,#94a3b8)" fill="none"/>
<text x="197" y="74" text-anchor="middle">u_f</text>
<text x="197" y="149" text-anchor="middle">0</text>
<text x="224" y="100">=</text>
<path class="ok" pathLength="1" d="M90 30 C200 -10 300 20 318 46" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<polyline class="ok-uc" points="312,42 318,46 318,39" fill="none" stroke="var(--sema-a,#3b82f6)" stroke-width="2"/>
<rect class="vurgu" x="250" y="50" width="160" height="34" rx="6" fill="none" stroke="var(--sema-a,#3b82f6)"/>
<text x="330" y="72" text-anchor="middle">1) K_ff·u_f = F_f → u_f</text>
<path class="ok" pathLength="1" d="M70 172 C120 196 230 180 256 150" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<polyline class="ok-uc" points="250,152 256,150 256,157" fill="none" stroke="var(--sema-b,#f59e0b)" stroke-width="2"/>
<rect x="250" y="118" width="160" height="34" rx="6" fill="none" stroke="var(--sema-b,#f59e0b)"/>
<text x="330" y="140" text-anchor="middle">2) R = K_sf·u_f − F_s</text>
</svg>
:::

Mesnetler sıfır yer değiştirme verdiğinde ($\mathbf{u}_s=\mathbf{0}$) iş iki adıma iner:

1. **Çöz:** $\kutua{\mathbf{K}_{ff}}\,\ka{\mathbf{u}_f}=\mathbf{F}_f$. Tutulu SD'lerin satır ve sütunlarını silmek tam olarak budur.
2. **Tepki:** $\kb{\mathbf{R}}=\kutuc{\mathbf{K}_{sf}}\,\ka{\mathbf{u}_f}-\mathbf{F}_s$. Pratikte bütün $\mathbf{u}$'yu bulup $\mathbf{R}=\mathbf{K}\mathbf{u}-\mathbf{F}$ almak aynı sonucu verir; serbest SD'lerde bu fark sıfır çıkar.

::: not Neden satır ve sütun birlikte silinir?
Sütunu silmek, bilinen $u_s=0$'ı denklemden çıkarmaktır. Satırı silmek, bilinmeyen tepkili denklemi şimdilik kenara koymaktır. İkisi birlikte silinince geriye kare ve tekil olmayan $\mathbf{K}_{ff}$ kalır.
:::

Aşağıdaki yay sisteminde sol uç tutulu. Yükü ve rijitlikleri değiştir, serbest düğümlerin yer değiştirmesinin ve mesnet tepkisinin nasıl değiştiğine bak. Tepki her zaman yüke eşit ve zıt yönlüdür.

::: etkilesim yay-sistemi
{"k": [2000, 1000], "P": 10, "duzen": "seri"}
:::

## Yeterli mesnet ne demek?

$\mathbf{K}_{ff}$ tekil değilse yapı **kararlıdır**. Düzlemde bir rijit cismin üç hareketi vardır: iki öteleme ve bir dönme. Mesnetler bu üçünü birden engellemelidir. Kafeste en az üç mesnet bileşeni gerekir ve bunlar ne paralel ne de tek noktada kesişen doğrultularda olmalıdır.

::: uyari Sayısal kararsızlık
Program "matris tekil" ya da "sıfır pivot" hatası veriyorsa, ilk şüphelenmen gereken eksik mesnet ya da modelde boşta kalmış bir düğümdür. Kafes modelinde mafsallı bir düğüme yalnız tek çubuk bağlıysa o düğüm de mekanizma oluşturur.
:::

::: hata Tepkiyi indirgenmiş sistemden okumak
İndirgenmiş $\mathbf{K}_{ff}\mathbf{u}_f=\mathbf{F}_f$ yalnız yer değiştirmeleri verir. Tepkiler o sistemde yoktur; silinen satırlara geri dönüp $\mathbf{R}=\mathbf{K}\mathbf{u}-\mathbf{F}$ hesaplamak gerekir.
:::

::: hata Tutulu SD'yi yanlış numaralamak
Kafeste düğüm 3 tutuluysa silinecek SD'ler 3 değil, $2\cdot3-1=5$ ve $6$'dır. Bir önceki dersteki $d(i-1)+1$ kuralını burada da uygula.
:::

## Mesnet çökmesi

Mesnet sıfır olmayan bir değere zorlanırsa ($\mathbf{u}_s\neq\mathbf{0}$), üst satırdaki $\mathbf{K}_{fs}\mathbf{u}_s$ terimi sağ tarafa geçer:

$$
\kutua{\mathbf{K}_{ff}}\,\ka{\mathbf{u}_f}=\mathbf{F}_f-\kutuc{\mathbf{K}_{fs}}\,\mathbf{u}_s
$$

Hiç dış yük olmasa bile mesnet çökmesi hiperstatik yapıda iç kuvvet doğurur. Tarihi köprülerde ayak oturması tam olarak bu yüzden çatlak açar.

Hiperstatik üç çubuklu kafeste üç mesnet düğümü ve tek serbest düğüm var. Haritada mesnet düğümlerinin SD'lerini say: 8 SD'den 6'sı tutulu, geriye $2\times2$ bir $\mathbf{K}_{ff}$ kalır.

::: etkilesim dof-haritasi
{"hazir": "kafes-uc-cubuk"}
:::

## Çözümlü örnekler

::: ornek Sol ucu tutulu yay sistemi
Üç düğümlü bir yay sisteminin birleştirilmiş matrisi aşağıda. Düğüm 1 tutulu, düğüm 3'e $F=10$ kN. Yer değiştirmeleri bul.
$$
\mathbf{K}=\begin{bmatrix}2000&-1000&0\\-1000&2000&-1000\\0&-1000&1000\end{bmatrix}
$$
--- ipucu
SD 1'in satır ve sütununu sil. Geriye $2\times2$ sistem kalır.
--- cevap
$\mathbf{u}=[0,\ 1/100,\ 1/50]^T$ m.
--- kod
mo.sinir_kosulu("2000 -1000 0; -1000 2000 -1000; 0 -1000 1000", "0; 0; 10", sabit=[1])
--- kontrol
r.deger[0] == 0 and r.deger[1] == sp.Rational(1, 100) and r.deger[2] == sp.Rational(1, 50)
--- yorum
Motor adım adım satır ve sütun silmeyi, indirgenmiş çözümü ve tepkiyi gösteriyor. Adımları tek tek aç.
:::

::: ornek İndirgenmiş sistemi elle kurmak
Aynı soruyu $\mathbf{K}_{ff}$'yi kendin yazarak çöz.
--- ipucu
$\mathbf{K}_{ff}=\begin{bmatrix}2000&-1000\\-1000&1000\end{bmatrix}$, $\mathbf{F}_f=[0,\ 10]^T$.
--- cevap
$u_2=1/100$, $u_3=1/50$. Bir önceki örnekle aynı.
--- kod
mo.coz("2000 -1000; -1000 1000", "0; 10", bilinmeyen="u")
--- kontrol
r.deger == sp.Matrix([sp.Rational(1, 100), sp.Rational(1, 50)])
--- yorum
`sinir_kosulu` içeride tam olarak bunu yapar. Elle yapmayı bilmek, programın çıktısını denetlerken işe yarar.
:::

::: ornek Mesnet tepkisi R = Ku − F
Bulduğun $\mathbf{u}$ ile mesnet tepkisini hesapla.
--- ipucu
$\mathbf{K}\mathbf{u}$'nun ilk satırı: $2000\cdot0-1000\cdot\tfrac{1}{100}=-10$.
--- cevap
$\mathbf{R}=[-10,\ 0,\ 0]^T$. Mesnet 10 kN'luk yükü zıt yönde karşılar; serbest SD'lerde fark sıfırdır.
--- kod
u = mo.sinir_kosulu("2000 -1000 0; -1000 2000 -1000; 0 -1000 1000", "0; 0; 10", sabit=[1])
u, mo.cikar(mo.carp("2000 -1000 0; -1000 2000 -1000; 0 -1000 1000", u.deger), "0; 0; 10")
--- kontrol
r[-1].deger == sp.Matrix([-10, 0, 0])
--- yorum
Serbest SD'lerde sıfır çıkması bir **denetimdir**. Sıfır çıkmıyorsa çözüm yanlıştır.
:::

::: ornek İki ucu tutulu zincir
Dört düğümlü zincir ($k=1000$), düğüm 1 ve 4 tutulu, düğüm 2'ye $F=10$ kN. Yer değiştirmeleri ve iki tepkiyi bul.
--- ipucu
$\mathbf{K}_{ff}=\begin{bmatrix}2000&-1000\\-1000&2000\end{bmatrix}$. Yük, rijitliğe göre iki mesnete paylaşılır.
--- cevap
$u_2=1/150$, $u_3=1/300$; $R_1=-20/3$, $R_4=-10/3$ kN. Toplam $-10$: denge sağlanıyor.
--- kod
K = "1000 -1000 0 0; -1000 2000 -1000 0; 0 -1000 2000 -1000; 0 0 -1000 1000"
u = mo.sinir_kosulu(K, "0; 10; 0; 0", sabit=[1, 4])
u, mo.cikar(mo.carp(K, u.deger), "0; 10; 0; 0")
--- kontrol
r[0].deger[1] == sp.Rational(1, 150) and r[-1].deger[0] == sp.Rational(-20, 3) and r[-1].deger[3] == sp.Rational(-10, 3)
--- yorum
Bu yapı hiperstatiktir: tepkiler yalnız denge denklemleriyle bulunamaz. Rijitlik yöntemi hiperstatikliği hiç fark etmez; hep aynı adımları izler.
:::

::: ornek Mesnet çökmesi
İki yaylı zincir ($k=1000$): düğüm 1 tutulu, düğüm 3'ün mesnedi $u_3=1/100$ m çöktü, dış yük yok. Ortadaki düğümün yer değiştirmesini bul.
$$
\mathbf{K}=\begin{bmatrix}1000&-1000&0\\-1000&2000&-1000\\0&-1000&1000\end{bmatrix}
$$
--- ipucu
$\mathbf{K}_{ff}=[2000]$, $\mathbf{K}_{fs}=[-1000\ \ -1000]$, $\mathbf{u}_s=[0,\ 1/100]^T$. Sağ taraf $0-\mathbf{K}_{fs}\mathbf{u}_s$.
--- cevap
$2000\,u_2=10 \Rightarrow u_2=1/200$ m. Orta düğüm iki mesnetin tam ortasına gelir.
--- kod
mo.coz("2000", mo.cikar("0", mo.carp("-1000 -1000", "0; 1/100")).deger, bilinmeyen="u")
--- kontrol
r.deger[0] == sp.Rational(1, 200)
--- yorum
Yük yokken bile yaylarda $1000\cdot\tfrac{1}{200}=5$ kN kuvvet doğdu. Oturma, hiperstatik yapıda gerçek bir yüktür.
:::

::: ornek Mesnetsiz matrisin rankı
Mesnet konmamış iki yaylı zincirin $\mathbf{K}$'sının rankını bul. Kaç mesnet gerekir?
--- ipucu
$3\times3$ matris, rijit cisim hareketi tek: eksenel öteleme.
--- cevap
$\operatorname{rank}\mathbf{K}=2$. Eksik rank $3-2=1$; bir mesnet yeterli.
--- kod
mo.rank("1000 -1000 0; -1000 2000 -1000; 0 -1000 1000")
--- kontrol
r.deger == 2
--- yorum
Düzlem kafeste eksik rank 3, düzlem çerçevede de 3 çıkar: iki öteleme ve bir dönme. Mesnetler en az bu kadar SD tutmalıdır.
:::

::: ornek Büyük sayı (ceza) yöntemi
Satır ve sütun silmek yerine, tutulu SD'nin köşegenine çok büyük bir sayı eklenebilir. İlk örnekteki $K_{11}$'e $10^{12}$ ekle ve çöz.
--- ipucu
Büyük rijitlikli bir yay mesnet gibi davranır; $u_1\approx0$ olur.
--- cevap
$u_1=10^{-11}$, $u_3=0{,}02000000001$: tam çözüme on bir basamak yakın.
--- kod
mo.coz("1000000001000 -1000 0; -1000 2000 -1000; 0 -1000 1000", "0; 0; 10", bilinmeyen="u")
--- kontrol
abs(float(r.deger[2]) - 0.02) < 1e-9 and float(r.deger[0]) < 1e-10
--- yorum
Ticari programların çoğu bu yolu seçer, çünkü matrisin boyutunu ve SD numaralarını değiştirmez. Bedeli küçük bir yuvarlama hatasıdır.
:::

::: ornek Hiperstatik kafes: tepkiler ve denge
Hazır `kafes-uc-cubuk` modelinde üç mesnet düğümü ve tek serbest düğüm (4) var; düğüm 4'e $F_x=10$, $F_y=-20$ kN. Çöz, tepkileri oku ve dengeyi denetle.
--- ipucu
Serbest SD'ler 7 ve 8. $\mathbf{K}_{ff}$ yalnız $2\times2$.
--- cevap
$u_4=1/2880$, $v_4=-1/7560$ m. Tepkiler: düğüm 1 $(-2{,}46;\ -3{,}28)$, düğüm 2 $(0;\ 13{,}23)$, düğüm 3 $(-7{,}54;\ 10{,}05)$. $\sum R_x=-10$, $\sum R_y=20$.
--- kod
se.se_coz(se.ornek_model("kafes-uc-cubuk"))
--- kontrol
r.deger[6] == sp.Rational(1, 2880) and abs(r.veri["tepkiler"][1]["Fy"] - 13.2275) < 1e-3 and abs(r.veri["tepkiler"][0]["Fx"] + r.veri["tepkiler"][2]["Fx"] + 10) < 1e-9
--- yorum
Altı tepki bileşeni var, düzlemde yalnız üç denge denklemi. Statik yetmez, ama rijitlik yöntemi tek bir $2\times2$ çözümle hepsini verir.
:::

::: muhendislik Mesnet modeli sonucu belirler
Taş kemer köprüde ayakları ankastre mi, mafsallı mı, yoksa zemin yaylarıyla mı modellediğin, ölçülen frekanslarla model arasındaki farkın en büyük kaynaklarından biridir. OMA ile ölçülen frekanslar modelden düşükse, ilk bakılacak yer çoğu zaman mesnet rijitliğidir.

Zemin yayı, bu dersteki ceza yönteminin fiziksel karşılığıdır: sonsuz rijit yerine sonlu bir $k$ kullanırsın. Model güncellemede bu $k$ değerleri ayarlanan parametreler arasına girer.
:::

::: ozet Özet
- Her SD'de ya yer değiştirme ya kuvvet bilinir.
- Bölümleme: $\mathbf{K}_{ff}\mathbf{u}_f=\mathbf{F}_f-\mathbf{K}_{fs}\mathbf{u}_s$.
- Tepki: $\mathbf{R}=\mathbf{K}\mathbf{u}-\mathbf{F}$; serbest SD'lerde sıfır çıkması bir denetimdir.
- Mesnetler bütün rijit cisim hareketlerini engellemeli, yoksa $\mathbf{K}_{ff}$ tekildir.
- Ceza yöntemi: köşegene büyük sayı ekle; boyut değişmez.
- Mesnet çökmesi hiperstatik yapıda yük gibi iç kuvvet doğurur.
:::

## Alıştırma

::: alistirma sinir-kosulu
{"zorluk": 1}
:::

::: alistirma sinir-kosulu
{"zorluk": 2}
:::
