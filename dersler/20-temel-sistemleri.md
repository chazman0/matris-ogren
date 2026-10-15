---
baslik: Temel sistemleri: elastik mesnet, Winkler zemini ve mesnet çökmesi
bolum: se
ozet: Düğüm yayı K'nın köşegenine eklenir, Winkler zemini kiriş elemanına tutarlı zemin matrisiyle girer, mesnet çökmesi K_fs u_s ile sağ tarafa taşınır; kolon, kiriş ve temel tek modelde çözülür.
sure: 50
---

## Neden?

Şimdiye kadar mesnet ya tam tutuyordu ya da hiç yoktu. Gerçek temel öyle davranmaz: zemin bir yay gibi esner, bir ayak komşusundan daha çok oturur, sürekli temel kirişi zemine gömülerek yük taşır. Üst yapıyı rijit temel varsayımıyla çözmek kolon momentlerini de ölçülen frekansları da yanıltabilir. Bu derste üç aracı öğreneceksin: **düğüm yayı**, **Winkler zemini** ve **verilen mesnet çökmesi**; üçü de bildiğin $\mathbf{K}\mathbf{u}=\mathbf{F}$ denklemine küçük eklerle girer.

## Elastik mesnet: tek serbestlikli eleman

::: tanim Elastik mesnet
**Elastik mesnet** (elastic support), bir düğümün tek bir SD'sini sabit zemine bağlayan yaydır: öteleme yayı $k_x$, $k_y$ [kN/m] ya da dönme yayı $k_r$ [kN·m/rad]. Yay yapıya $F_i=-k\,u_i$ kuvvetini uygular ve rijitlik matrisine yalnız **köşegen** terim olarak girer: $K_{ii}\mathrel{+}=k$.
:::

Neden yalnız köşegen? 11. dersteki yay elemanı iki düğümlüdür: $k\begin{bmatrix}1&-1\\-1&1\end{bmatrix}$. İkinci düğüm zemindir ve hiç hareket etmez; satırı ve sütunu silinince geriye tek hücre, $k$, kalır. O hücre yapının $i$. SD'sine eklenir; yeni bir düğüm ya da SD doğmaz.

İki ucu yaylara oturan iki elemanlı kirişte ($EI=4000$ kN·m², $L=4$ m, her eleman 2 m) birleştirilmiş matris şöyle değişir:

$$
\mathbf{K}=
\begin{bmatrix}
\kutuc{6000+k_{\text{sol}}} & 6000 & -6000 & 6000 & 0 & 0\\
6000 & 8000 & -6000 & 4000 & 0 & 0\\
-6000 & -6000 & 12000 & 0 & -6000 & 6000\\
6000 & 4000 & 0 & 16000 & -6000 & 4000\\
0 & 0 & -6000 & -6000 & \kutuc{6000+k_{\text{sağ}}} & -6000\\
0 & 0 & 6000 & 4000 & -6000 & 8000
\end{bmatrix},
\qquad
\kc{F_{y1}}=-k_{\text{sol}}\,v_1,\quad \kc{F_{y3}}=-k_{\text{sağ}}\,v_3
$$

İki sınır durumu aklında kalsın: $k\to\infty$ olunca $u_i\to0$, yay rijit mesnete dönüşür; $k\to0$ olunca yay yok olur, SD serbest kalır. Programda rijit mesnet için köşegene devasa bir sayı yazmak yerine satır ve sütunu silmek hem kesin hem sayısal olarak sağlıklıdır.

Aşağıda yay rijitliklerini değiştir. Yay sıfırlanınca $\mathbf{K}$ tekilleşir: sol yayı kaldırıp dönme yayını da sıfır bırakırsan kiriş sağ yay etrafında serbestçe döner.

::: etkilesim elastik-mesnet
{"L": 4, "P": 10, "k1": 1000, "k2": 1000, "kr": 0}
:::

::: not Yaylı SD serbesttir
Yayla tutulan SD **serbest** sayılır: yer değiştirmesi bilinmeyendir, dış kuvveti bilinir. Yay, 15. dersteki tutulu–serbest bölümlemesini değiştirmez; yalnız $\mathbf{K}_{ff}$'nin köşegenini büyütür. Yay kuvveti çözümden sonra $-k\,u_i$ ile okunur; motor bunu `yaylar` listesinde verir ve denge toplamına katar.
:::

## Winkler zemini

::: tanim Winkler zemini ve yatak katsayısı
**Winkler zemini** (Winkler foundation), kirişin altında birbirinden bağımsız sonsuz sayıda küçük yay varsayar. Zemin basıncı çökmeyle orantılıdır: $p(x)=-k_s\,v(x)$ [kN/m]. **Yatak katsayısı** $k_s$ [kN/m²] birim boydaki yay rijitliğidir; zemin raporundaki $k_0$ [kN/m³] değeri temel genişliği $b$ ile çarpılarak bulunur: $k_s=k_0\,b$.
:::

Sonsuz sayıda yayı tek tek düğümlere bağlayamayız. Bunun yerine zeminin $\tfrac12\int k_s v^2\,dx$ enerjisini Hermite şekil fonksiyonlarıyla yazarız; çıkan matris kiriş elemanının eğilme SD'lerine eklenir:

$$
\mathbf{k}_z=\int_0^L k_s\,\mathbf{N}^T\mathbf{N}\,dx=\frac{k_sL}{420}
\begin{bmatrix}
\kutua{156} & \kutub{22L} & \kutua{54} & \kutub{-13L}\\
\kutub{22L} & \kutuc{4L^2} & \kutub{13L} & \kutuc{-3L^2}\\
\kutua{54} & \kutub{13L} & \kutua{156} & \kutub{-22L}\\
\kutub{-13L} & \kutuc{-3L^2} & \kutub{-22L} & \kutuc{4L^2}
\end{bmatrix},
\qquad
\mathbf{k}=\mathbf{k}_{\text{kiriş}}+\mathbf{k}_z
$$

Mavi hücreler çökme–çökme, turuncu hücreler çökme–dönme, yeşil hücreler dönme–dönme çiftleridir. Bu matris 18. dersteki **tutarlı kütle matrisi** ile aynı integraldir: $k_s$ yerine $\rho A$ yazarsan kirişin $\rho AL/420$ çarpanlı kütle matrisini elde edersin. İkisi de yayılı bir büyüklüğü şekil fonksiyonlarıyla düğümlere taşıma işidir.

### Karakteristik uzunluk ve Hetényi çözümü

Zeminli kirişin davranışını tek bir sayı yönetir:

$$
\kutub{\beta=\left(\frac{k_s}{4EI}\right)^{1/4}}\ [\text{m}^{-1}],
\qquad
w_{\max}=\frac{P\beta}{2k_s},\qquad M_{\max}=\frac{P}{4\beta}
$$

$1/\beta$ **karakteristik uzunluktur** (characteristic length); çökme dalgası bu uzunluk mertebesinde sönümlenir. $w_{\max}$ ve $M_{\max}$ formülleri Hetényi'nin **sonsuz uzun** kiriş çözümüdür ve tekil yükün hemen altında geçerlidir. $\beta L<\pi/4$ ise kiriş zemine göre rijittir ($w\approx P/k_sL$), $\beta L>\pi$ ise sonsuz kiriş gibi davranır; arası orta kiriştir ve formüller yalnız yaklaşık tutar.

Ağ sıklığı da $\beta$ ile ölçülür: eleman boyu $l_e$ için $\beta l_e\lesssim0.5$ tut. Aşağıda $k_s$, $EI$, $L$ ve eleman sayısını değiştir; sonlu eleman çözümünü Hetényi formülüyle karşılaştır.

::: etkilesim winkler-kiris
{"ks": 20000, "EI": 216000, "L": 8, "P": 500, "n": 8}
:::

::: uyari Winkler zemini bir yaklaşımdır
Gerçek zeminde komşu noktalar birbirini sürükler; Winkler yayları bağımsızdır. Yatak katsayısı bir malzeme sabiti değil, temel boyutuna ve yük düzeyine bağlı bir **model parametresidir**. Bu yüzden $k_s$ için bir aralık dene ve sonuçların ne kadar değiştiğine bak.
:::

## Mesnet çökmesi

15. derste bölümlemeyi gördün. Tutulu SD'lerden bazıları sıfır değil, bilinen bir $\mathbf{u}_s$ değerini alırsa üst satırdaki $\mathbf{K}_{fs}\mathbf{u}_s$ terimi sağ tarafa geçer:

$$
\begin{bmatrix}\kutua{\mathbf{K}_{ff}} & \kutuc{\mathbf{K}_{fs}}\\ \kutuc{\mathbf{K}_{sf}} & \kutub{\mathbf{K}_{ss}}\end{bmatrix}
\begin{bmatrix}\ka{\mathbf{u}_f}\\ \mathbf{u}_s\end{bmatrix}
=
\begin{bmatrix}\mathbf{F}_f\\ \mathbf{F}_s+\mathbf{R}\end{bmatrix}
\quad\Rightarrow\quad
\kutua{\mathbf{K}_{ff}}\,\ka{\mathbf{u}_f}=\underbrace{\mathbf{F}_f-\kutuc{\mathbf{K}_{fs}}\,\mathbf{u}_s}_{\text{eşdeğer yük}},
\qquad
\mathbf{R}=\mathbf{K}\mathbf{u}-\mathbf{F}
$$

Çökme bir yük değil, bir yer değiştirmedir; $\mathbf{F}$'ye yazılmaz. Ama sağ tarafa taşınınca **eşdeğer bir yük** gibi davranır ve hiperstatik yapıda iç kuvvet doğurur. İzostatik yapı ise çökmeye rijit cisim gibi uyar: iç kuvvet sıfır kalır. Enerji sağlaması da değişir; tepkiler verilen yer değiştirme üzerinden iş yaptığından $W=\tfrac12\mathbf{u}^T(\mathbf{F}+\mathbf{R})$ olur.

Portal çerçevede sağ tabanın $v_4$ serbestliği 10 mm çökerse $\mathbf{K}_{fs}$'nin $v_4$ sütunu sağ tarafa taşınır. Aşağıda "Kff · Kfs bölümleri"ne dokun; turuncu çerçeveli dikdörtgen bu sütunları içerir.

::: etkilesim dof-haritasi
{"hazir": "portal", "baslik": "Portal çerçevede K_ff ve K_fs bölümleri"}
:::

## Kolon, kiriş ve temel tek modelde

Üç araç bir arada en çok **sürekli temel kirişi** (strip footing) üzerindeki çerçevede işe yarar. Kolonlar temel kirişine düğümlerde bağlanır, temel kirişi Winkler zeminine oturur, yatay kaymayı tek bir mesnet tutar. Düşey yükün tamamını zemin taşır; kolon altlarındaki oturma farkı üst yapıda ek moment doğurur. Hazır `cerceve-temel-kirisi` modeli tam olarak budur.

::: sekil Kolon–kiriş–temel sistemi: temel kirişi Winkler zeminine oturur, yatay kaymayı tek mesnet tutar
<svg viewBox="0 0 420 240" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<rect x="20" y="206" width="380" height="20" fill="var(--sema-c-bg,rgba(16,185,129,.12))"/>
<path d="M20 206H400" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<path d="M32 206l-7 8M62 206l-7 8M92 206l-7 8M122 206l-7 8M152 206l-7 8M182 206l-7 8M212 206l-7 8M242 206l-7 8M272 206l-7 8M302 206l-7 8M332 206l-7 8M362 206l-7 8M392 206l-7 8" stroke="var(--sema-cizgi,#94a3b8)" fill="none"/>
<path d="M50 176l5 5-10 6 10 6-10 6 5 7M96 176l5 5-10 6 10 6-10 6 5 7M142 176l5 5-10 6 10 6-10 6 5 7M188 176l5 5-10 6 10 6-10 6 5 7M234 176l5 5-10 6 10 6-10 6 5 7M280 176l5 5-10 6 10 6-10 6 5 7M326 176l5 5-10 6 10 6-10 6 5 7M372 176l5 5-10 6 10 6-10 6 5 7" stroke="var(--sema-c,#10b981)" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
<path d="M40 170H380" stroke="var(--sema-c,#10b981)" stroke-width="7" stroke-linecap="round" fill="none"/>
<path d="M82 170V60M337 170V60M82 60H337" stroke="currentColor" stroke-width="5" stroke-linecap="round" fill="none"/>
<path d="M100 26H320" stroke="var(--sema-a,#3b82f6)" stroke-width="2" fill="none"/>
<path class="ok" pathLength="1" d="M100 26V52M144 26V52M188 26V52M232 26V52M276 26V52M320 26V52" stroke="var(--sema-a,#3b82f6)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="96,46 100,52 104,46" stroke="var(--sema-a,#3b82f6)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="140,46 144,52 148,46" stroke="var(--sema-a,#3b82f6)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="184,46 188,52 192,46" stroke="var(--sema-a,#3b82f6)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="228,46 232,52 236,46" stroke="var(--sema-a,#3b82f6)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="272,46 276,52 280,46" stroke="var(--sema-a,#3b82f6)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="316,46 320,52 324,46" stroke="var(--sema-a,#3b82f6)" stroke-width="1.6" fill="none"/>
<text x="210" y="16" text-anchor="middle" fill="var(--sema-a,#3b82f6)">q = 30 kN/m</text>
<path class="ok" pathLength="1" d="M30 60H74" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5" fill="none"/>
<polyline class="ok-uc" points="67,54 74,60 67,66" stroke="var(--sema-b,#f59e0b)" stroke-width="2.5" fill="none"/>
<text x="26" y="48" fill="var(--sema-b,#f59e0b)">15 kN</text>
<path d="M78 170L64 161V179Z" fill="var(--sema-sil-bg,rgba(239,68,68,.12))" stroke="var(--sema-sil,#ef4444)" stroke-width="1.5"/>
<path d="M60 158V182" stroke="var(--sema-sil,#ef4444)" stroke-width="1.5"/>
<text x="24" y="152" fill="var(--sema-sil,#ef4444)" font-size="11">uₓ tutulu</text>
<circle cx="40" cy="170" r="4" fill="currentColor"/><circle cx="82" cy="170" r="4" fill="currentColor"/><circle cx="210" cy="170" r="4" fill="currentColor"/><circle cx="337" cy="170" r="4" fill="currentColor"/><circle cx="380" cy="170" r="4" fill="currentColor"/><circle cx="82" cy="60" r="4" fill="currentColor"/><circle cx="337" cy="60" r="4" fill="currentColor"/>
<text x="40" y="162" text-anchor="middle" font-size="11">1</text><text x="92" y="162" font-size="11">2</text><text x="210" y="162" text-anchor="middle" font-size="11">3</text><text x="347" y="162" font-size="11">4</text><text x="380" y="162" text-anchor="middle" font-size="11">5</text><text x="70" y="78" font-size="11">6</text><text x="345" y="78" font-size="11">7</text>
<text x="92" y="120" font-size="11">kolon 5</text><text x="300" y="120" font-size="11">kolon 6</text><text x="210" y="76" text-anchor="middle" font-size="11">üst kiriş 7</text>
<text x="210" y="146" text-anchor="middle" font-size="11" fill="var(--sema-c,#10b981)">temel kirişi 1–4: kₛ = 30 000 kN/m²</text>
<text x="210" y="236" text-anchor="middle" font-size="11" fill="var(--sema-c,#10b981)">Winkler zemin yayları: p = −kₛ v, yükü zemin taşır</text>
</svg>
:::

::: hata Yayı mesnet olarak da işaretlemek
Bir SD'yi hem `mesnetler` içinde tutulu yazıp hem de ona yay bağlarsan mesnet kazanır: $u_i=0$ olur ve yay kuvveti $-k\cdot0=0$ çıkar. Elastik mesnet istiyorsan o SD'yi mesnet listesinden çıkar; yay zaten onu tutar. Tersi yanılgı da yaygındır: yay bir SD ya da düğüm eklemez, yalnız köşegeni büyütür.
:::

::: hata k_s birimini karıştırmak
Zemin raporu yatak katsayısını $k_0$ [kN/m³] verir; kiriş modeli $k_s=k_0\,b$ [kN/m²] ister. Çarpanı unutursan yalnız 1 m genişlikte doğru çıkar: 2 m genişliğinde temelde oturmalar iki kat büyük hesaplanır.
:::

::: hata Çökmeyi yük vektörüne yazmak
$-0.01$ m'yi $\mathbf{F}$'nin bir satırına yazmak hem birim hem anlam hatasıdır. Çökme `cokmeler` listesine, yani $\mathbf{u}_s$'ye girer; sağ tarafa $-\mathbf{K}_{fs}\mathbf{u}_s$ olarak kendisi taşınır ve ancak o zaman birimi kN olur.
:::

## Çözümlü örnekler

::: ornek Yaylı kiriş: kesin çözüm
İki elemanlı kiriş ($L=4$ m, $E=200\times10^6$ kN/m², $I=2\times10^{-5}$ m⁴, $EI=4000$), uçlarında $k=1000$ kN/m düşey yaylar, ortada $P=-10$ kN; mesnet yok. Orta çökmeyi ve yay kuvvetlerini bul.
--- ipucu
Simetri: her yay $P/2$ taşır ve $P/2k$ çöker. Orta çökme, basit kirişin $PL^3/48EI$ sehimi ile yay çökmesinin toplamıdır.
--- cevap
$$
\ka{v_1}=\ka{v_3}=-\frac{P}{2k}=-\frac{10}{2000}=-\frac{1}{200}\ \text{m},
\qquad
\kc{v_2}=-\Big(\underbrace{\tfrac{PL^3}{48EI}}_{1/300}+\underbrace{\tfrac{P}{2k}}_{1/200}\Big)=\kutuc{-\frac{1}{120}}\ \text{m}
$$
Yay kuvvetleri $F=-k\,v_1=1000\cdot\tfrac{1}{200}=\kc{+5}$ kN: iki yay 10 kN'yi yukarı iter, tepki listesi boştur.
--- kod
model = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 2}, {"no": 3, "x": 4}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"}, {"no": 2, "dugumler": [2, 3], "E": "200e6", "I": "2e-5"}], "mesnetler": [], "yaylar": [{"dugum": 1, "ky": 1000}, {"dugum": 3, "ky": 1000}], "yukler": [{"dugum": 2, "Fy": -10}]}
se.se_coz(model)
--- kontrol
r.deger[2] == sp.Rational(-1, 120) and r.deger[0] == sp.Rational(-1, 200) and abs(r.veri["yaylar"][0]["kuvvet"] - 5) < 1e-9 and r.veri["K"][0][0] == 7000
--- yorum
$K_{11}=6000+1000=7000$: anlatımdaki "köşegene eklendi" tablosunu bul. Yayları $k\to\infty$ yaparsan $v_2\to-1/300$ m, yani basit kiriş sehimine döner.
:::

::: ornek Elle: konsol ucunda yay
Sol ucu ankastre $L=4$ m kiriş ($EI=4000$); serbest ucu $k=250$ kN/m düşey yaya oturuyor ve uca $P=-10$ kN geliyor. $\mathbf{K}$'yı kur, yayı köşegene ekle, çöz.
--- ipucu
$EI/L^3=62.5$: $12EI/L^3=750$, $6EI/L^2=1500$, $4EI/L=4000$, $2EI/L=2000$. Yay SD 3'e ($v_2$) gelir: $K_{33}=750+250$.
--- cevap
$$
\begin{bmatrix}750&1500&-750&1500\\1500&4000&-1500&2000\\-750&-1500&\kutuc{750+250}&-1500\\1500&2000&-1500&4000\end{bmatrix}
\xrightarrow{\text{SD 1, 2 tutulu}}
\begin{bmatrix}\kutua{1000}&-1500\\-1500&\kutua{4000}\end{bmatrix}\begin{bmatrix}v_2\\\theta_2\end{bmatrix}=\begin{bmatrix}-10\\0\end{bmatrix}
$$
$$
v_2=\frac{-10\cdot4000}{4000\cdot1000-1500^2}=\kutuc{-\frac{4}{175}}\ \text{m},\qquad \theta_2=-\frac{3}{350}\ \text{rad},\qquad F_{\text{yay}}=-k\,v_2=\kc{\tfrac{40}{7}\approx5.71}\ \text{kN}
$$
--- kod
K = mo.kiris_eleman("200e6", "2e-5", 4)
Ky = mo.topla(K.deger, "0 0 0 0; 0 0 0 0; 0 0 250 0; 0 0 0 0")
K, Ky, mo.sinir_kosulu(Ky.deger, "0; 0; -10; 0", sabit=[1, 2])
--- kontrol
r[1].deger[2, 2] == 1000 and r[-1].deger[2] == sp.Rational(-4, 175) and r[-1].deger[3] == sp.Rational(-3, 350)
--- yorum
Konsol ucu da bir yaydır: rijitliği $3EI/L^3=187.5$ kN/m. İki yay paraleldir: $187.5+250=437.5$ kN/m ve $v_2=-10/437.5=-4/175$. Rijitlik yöntemi bu paylaşımı kendiliğinden yapar; konsol $30/7\approx4.29$ kN, yay $5.71$ kN taşır.
:::

::: ornek Elastik mesnetli portal: taban momenti ve yay kuvveti
Hazır `cerceve-elastik-mesnet`: portal çerçevenin iki tabanı $k_x=20000$, $k_y=100000$, $k_r=30000$ yaylarına oturur; kirişte $q=-10$ kN/m, sol köşede 20 kN yatay yük. Sol kolonun taban momentini dönme yayının kuvvetiyle karşılaştır; ankastre `cerceve-portal` ile kıyasla.
--- ipucu
Taban düğümünde tek moment kaynağı dönme yayıdır: kolonun uç momenti $M(0)$ ile yay momenti dengede olmalı.
--- cevap
$$
\begin{aligned}
\theta_1&=-0.000489\ \text{rad},\qquad \kc{M_{\text{yay}}}=-k_r\theta_1=-30000\cdot(-0.000489)=\kc{+14.68}\ \text{kN·m}\\
M^{(1)}(0)&=\ksil{-14.68}\ \text{kN·m}\quad\Rightarrow\quad M^{(1)}(0)+M_{\text{yay}}=0
\end{aligned}
$$

| | ankastre portal | yaylı portal |
|---|---|---|
| yanal ötelenme $u_2$ | $3.59$ mm | $5.57$ mm |
| sol taban momenti | $13.4$ kN·m | $14.7$ kN·m |
| sağ taban momenti | $31.1$ kN·m | $24.2$ kN·m |
--- kod
se.se_coz(se.ornek_model("cerceve-elastik-mesnet"))
--- kontrol
abs(r.veri["elemanlar"][0]["diyagram"]["M"][0] + r.veri["yaylar"][2]["kuvvet"]) < 1e-9 and r.veri["tepkiler"] == [] and abs(float(r.deger[3]) - 0.005569) < 1e-5
--- yorum
Yumuşak yatay yaylar çerçeveyi daha çok yatırır. Dönme yayı sağ kolonun taban momentini düşürür; solda ise artan ötelenme momenti biraz büyütür. Elastik mesnet momentleri "hep azaltır" diye ezberleme, modeli çöz.
:::

::: ornek Mesnet çökmesi: kesin çözüm
$L=4$ m kiriş ($EI=4000$): sol uç ankastre, sağ uç kayıcı; sağ mesnet $\Delta=10$ mm çöküyor, yük yok. Dönmeyi, tepkileri ve ankastre momentini bul.
--- ipucu
Tek serbest SD $\theta_2$'dir. $\mathbf{K}_{fs}$, 4. satırın tutulu sütunlarıdır: $[1500,\ 2000,\ -1500]$; $\mathbf{u}_s=[0,\ 0,\ -0.01]^T$.
--- cevap
$$
\left[\begin{array}{ccc|c}750&1500&-750&1500\\1500&4000&-1500&2000\\-750&-1500&750&-1500\\\hline \kc{1500}&\kc{2000}&\kc{-1500}&\kutua{4000}\end{array}\right]
\qquad
\kutua{4000}\,\theta_2=0-\kc{(-1500)}\cdot(-0.01)=-15\ \Rightarrow\ \theta_2=\kutuc{-\frac{3}{800}}\ \text{rad}
$$
$$
\begin{aligned}
\mathbf{R}=\mathbf{K}\mathbf{u}:\quad R_1&=-750(-0.01)+1500\big(-\tfrac{3}{800}\big)=\kc{+1.875}\ \text{kN}\\
M_1&=15-7.5=\kc{+7.5}\ \text{kN·m},\qquad R_2=-7.5+5.625=\ksil{-1.875}\ \text{kN}
\end{aligned}
$$
Kapalı form: $R=3EI\Delta/L^3$, $M=3EI\Delta/L^2$.
--- kod
model = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 4}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "200e6", "I": "2e-5"}], "mesnetler": [{"dugum": 1, "uy": True, "rz": True}, {"dugum": 2, "uy": True}], "cokmeler": [{"dugum": 2, "uy": "-0.01"}], "yukler": []}
se.se_coz(model)
--- kontrol
r.deger[3] == sp.Rational(-3, 800) and abs(r.veri["tepkiler"][1]["Fy"] + 1.875) < 1e-9 and abs(r.veri["tepkiler"][0]["M"] - 7.5) < 1e-9
--- yorum
Hiç yük yokken $7.5$ kN·m ankastre momenti doğdu. Kayıcı mesnet olmasaydı kiriş çökmeye rijit cisim gibi uyar, iç kuvvet sıfır kalırdı: çökme yalnız hiperstatik yapıda kuvvet üretir.
:::

::: ornek Süperpozisyon: yük artı çökme
Hazır `cerceve-mesnet-cokmesi`: kirişte $q=-10$ kN/m, sağ ankastre taban 10 mm çöküyor. Yalnız yükle, yalnız çökmeyle ve ikisiyle çöz; toplamın tuttuğunu göster.
--- ipucu
Doğrusal sistemde $\mathbf{u}$, hem $\mathbf{F}$'ye hem $\mathbf{u}_s$'ye doğrusal bağlıdır; çözümler toplanır.
--- cevap
$$
\begin{aligned}
\ka{\text{yalnız yük}}:&\quad R_{1y}=R_{4y}=30\ \text{kN},\quad M_1=-8.95,\ M_4=+8.95\ \text{kN·m}\\
\kb{\text{yalnız çökme}}:&\quad R_{1y}=+2.47,\ R_{4y}=-2.47\ \text{kN},\quad M_1=M_4=+7.40\ \text{kN·m}\\
\kc{\text{toplam}}:&\quad R_{1y}=32.47,\ R_{4y}=27.53\ \text{kN},\quad M_1=-1.55,\ M_4=+16.35\ \text{kN·m}
\end{aligned}
$$
--- kod
tam = se.ornek_model("cerceve-mesnet-cokmesi")
yuk = se.ornek_model("cerceve-mesnet-cokmesi")
yuk["cokmeler"] = []
cokme = se.ornek_model("cerceve-mesnet-cokmesi")
cokme["yayili"] = []
se.se_coz(yuk), se.se_coz(cokme), se.se_coz(tam)
--- kontrol
r[0].deger + r[1].deger == r[2].deger and abs(r[1].veri["tepkiler"][0]["Fy"] + r[1].veri["tepkiler"][1]["Fy"]) < 1e-9 and abs(r[1].veri["tepkiler"][0]["M"] - 7.4001) < 1e-3
--- yorum
Çökme tek başına toplam düşey tepkiyi değiştirmez ($+2.47-2.47=0$); yükü iki ayak arasında yeniden paylaştırır. Oturan ayak yükten kaçar, komşusu daha çok yüklenir; kolonlarda kesme olmadığından çökme momenti kolon boyunca sabit $7.40$ kN·m'dir.
:::

::: ornek Temel kirişi: Winkler zemini
Hazır `kiris-elastik-zemin`: 8 m temel kirişi ($E=3\times10^7$, $I=0.0072$, $EI=216000$ kN·m²), $k_s=20000$ kN/m², ortadaki kolondan 500 kN. Zemin kuvvetlerinin toplamını ve en büyük çökmeyi bul; Hetényi ile karşılaştır.
--- ipucu
$\beta=(20000/864000)^{1/4}$; sekiz elemanda $l_e=1$ m.
--- cevap
$\beta=\kb{0.390}$ m⁻¹, $\beta L=3.12$ (orta kiriş), $\beta l_e=0.39$. Sonlu eleman: $w_{\max}=\kutuc{5.32}$ mm (düğüm 5), $M_{\max}=349$ kN·m. Hetényi: $P\beta/2k_s=4.88$ mm, $P/4\beta=320$ kN·m; ikisi de yaklaşık yüzde 9 küçük. Zemin kuvvetlerinin toplamı $\kc{500}$ kN, tepki listesi boş; uçlardaki çökme ortadakinin yüzde 1'i kadardır.
--- kod
se.se_coz(se.ornek_model("kiris-elastik-zemin"))
--- kontrol
abs(sum(e["zemin_kuvvetleri"][0] + e["zemin_kuvvetleri"][2] for e in r.veri["elemanlar"]) - 500) < 1e-6 and r.veri["tepkiler"] == [] and abs(r.veri["u"][8] + 0.0053156) < 1e-6
--- yorum
Mesnet yok ama $\mathbf{K}$ tekil değil: zemin matrisi her SD'yi tutar. Sonsuz kiriş formülü orta uzunluktaki kirişte yüzde 9 yanılır; uçları serbest olan sonlu kiriş daha az zemin sürükler ve daha çok çöker.
:::

::: ornek Uzun kiriş: Hetényi'yi sonlu elemanla doğrulamak
$L=40$ m, $EI=4000$, $k_s=1000$ kN/m², ortaya $P=10$ kN: $\beta=0.5$ m⁻¹, $\beta L=20$. 40 elemanla ($\beta l_e=0.5$) çöz; $P\beta/2k_s=2.5$ mm ve $P/4\beta=5$ kN·m ile karşılaştır.
--- ipucu
Düğümleri ve elemanları liste üreteciyle kur. 82 SD'de hesap sayısaldır; orta düğüm 21'dir.
--- cevap
$w_{\max}=\kutuc{2.499}$ mm (fark yüzde $0.03$), $M_{\max}=4.9996$ kN·m; uçtaki çökme $4\times10^{-7}$ m. Dalga 40 m'de tamamen sönmüştür: $\beta L=20$ gerçekten "sonsuz" kiriştir.
--- kod
n = 40
model = {"tip": "kiris", "dugumler": [{"no": i + 1, "x": i} for i in range(n + 1)], "elemanlar": [{"no": i + 1, "dugumler": [i + 1, i + 2], "E": "200e6", "I": "2e-5", "zemin": 1000} for i in range(n)], "mesnetler": [], "yukler": [{"dugum": 21, "Fy": -10}]}
se.se_coz(model)
--- kontrol
abs(r.veri["dugumler"][20]["u"][0] + 0.0025) < 1e-5 and abs(max(abs(x) for e in r.veri["elemanlar"] for x in e["diyagram"]["M"]) - 5) < 0.01
--- yorum
Ağı 20 elemana ($\beta l_e=1$) seyreltirsen hata yüzde $0.4$'e çıkar; 80 elemanda ($\beta l_e=0.25$) dört basamak tutar. $\beta l_e\lesssim0.5$ kuralı buradan gelir.
:::

::: ornek Kolon, kiriş ve temel: denge ve oturma
Hazır `cerceve-temel-kirisi`: 6 m açıklıklı çerçeve 8 m'lik temel kirişine oturur ($k_s=30000$ kN/m²); üst kirişte $q=-30$ kN/m, sol köşede 15 kN yatay yük; yalnız düğüm 2'de $u_x$ tutulu. Dengeyi denetle, kolon altlarının oturmasını oku.
--- ipucu
Düşey dengeyi zemin, yatay dengeyi tek mesnet sağlar: $\sum F_x$ için $R_{2x}=-15$ kN, $\sum F_y$ için zemin $=30\cdot6=180$ kN.
--- cevap
$R_{2x}=\ksil{-15}$ kN, $R_{2y}=0$; zemin kuvvetlerinin düşey toplamı $\kc{180}$ kN. Oturmalar: düğüm 2'de $0.84$ mm, düğüm 4'te $1.12$ mm; yatay yük sağ kolonu daha çok bastırır ($N_5=-86.3$, $N_6=-93.7$ kN). Temel kirişinde $|M|_{\max}=76.2$ kN·m. $\beta=0.348$ m⁻¹, 3 m'lik elemanlarda $\beta l_e=1.04$: ağ kabadır, temel kirişini bölerek dene.
--- kod
se.se_coz(se.ornek_model("cerceve-temel-kirisi"))
--- kontrol
abs(r.veri["tepkiler"][0]["Fx"] + 15) < 1e-6 and abs(sum(e["zemin_kuvvetleri"][1] + e["zemin_kuvvetleri"][4] for e in r.veri["elemanlar"] if e["zemin_kuvvetleri"]) - 180) < 1e-6 and r.veri["dugumler"][3]["u"][1] < r.veri["dugumler"][1]["u"][1] < 0
--- yorum
Çerçeve elemanında zemin tepkisi yerel $y'$ yönündedir; `zemin_kuvvetleri` listesinin 2. ve 5. girdileri düşey bileşenlerdir. Ankastre temel varsayımı bu $0.28$ mm'lik oturma farkını ve ondan doğan kiriş momentini hiç göremezdi.
:::

::: ornek Yatak katsayısını rapordan okumak
Zemin raporu $k_0=40000$ kN/m³ veriyor; temel kirişi $b=0.5$ m genişliğinde. Kiriş modelinde hangi $k_s$ kullanılır? $EI=216000$ kN·m² için $\beta$ kaçtır?
--- ipucu
$k_s=k_0\,b$; $\beta=(k_s/4EI)^{1/4}$.
--- cevap
$k_s=40000\cdot0.5=\kutub{20000}$ kN/m² (6. örnekteki değer). $\beta=(20000/864000)^{1/4}=\kb{0.390}$ m⁻¹; karakteristik uzunluk $1/\beta\approx2.6$ m.
--- yorum
Genişliği iki katına çıkarırsan $k_s$ iki katına, $\beta$ yalnız $2^{1/4}\approx1.19$ katına çıkar. Zemin rijitliği $\beta$'yı dördüncü kök içinden etkiler; bu yüzden $k_0$'daki büyük belirsizlik momentlere küçük yansır.
:::

::: muhendislik Köprü ayakları, oturma ve ölçülen frekanslar
Tarihi yığma köprünün ayakları yüzyıllar boyunca zemine oturur; biri kaya, öteki alüvyon üzerindeyse fark oturması kemeri bir mesnet çökmesi gibi zorlar ve hiperstatik kemerde kilit taşı ile üzengi çevresinde çatlak açar. Modelde bu etki `cokmeler` ile, zemin esnekliği ise ayak altındaki $k_x$, $k_y$, $k_r$ yaylarıyla temsil edilir; buna **zemin–yapı etkileşimi** (soil–structure interaction) denir.

OMA ile ölçülen frekanslar temel rijitliğine duyarlıdır: ankastre varsayımı frekansı yukarı iter, yumuşak yaylar aşağı çeker. 18. dersteki model güncellemede en belirsiz ve en etkili parametreler çoğu zaman bu yaylardır; frekans farkını kapatmak için önce elastisite modülünü değil, temel yaylarını sorgula.
:::

::: ozet Özet
- Düğüm yayı: $K_{ii}\mathrel{+}=k$; yay kuvveti $-k\,u_i$; yaylı SD serbest sayılır. $k\to\infty$ rijit mesnet, $k\to0$ serbest SD.
- Winkler zemini: $p=-k_sv$, $k_s=k_0\,b$ [kN/m²]; $\mathbf{k}_z=\frac{k_sL}{420}[\ldots]$ eğilme SD'lerine eklenir; kütle matrisiyle aynı integral.
- $\beta=(k_s/4EI)^{1/4}$; uzun kirişte $w_{\max}=P\beta/2k_s$, $M_{\max}=P/4\beta$; $\beta L<\pi/4$ rijit, $\beta L>\pi$ sonsuz; ağda $\beta l_e\lesssim0.5$.
- Mesnet çökmesi: $\mathbf{K}_{ff}\mathbf{u}_f=\mathbf{F}_f-\mathbf{K}_{fs}\mathbf{u}_s$, $\mathbf{R}=\mathbf{K}\mathbf{u}-\mathbf{F}$, $W=\tfrac12\mathbf{u}^T(\mathbf{F}+\mathbf{R})$; izostatikte iç kuvvet doğmaz.
- Kolon–kiriş–temel sistemi: düşey yükü zemin taşır, yatayı tek mesnet; oturma farkı üst yapıya moment taşır.
:::

## Alıştırma

Yay ve çökme hesabı, 15. dersin bölümleme kurallarının doğrudan uygulamasıdır; önce orada pekiştir.

::: alistirma sinir-kosulu
{"zorluk": 2}
:::

::: alistirma yay-seri
{"zorluk": 2}
:::
