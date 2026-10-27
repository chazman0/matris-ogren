---
baslik: Yük durumları, kombinasyonlar ve zarf (SAP2000 akışı)
bolum: yapi
ozet: G, Q, S, W ve E yük durumları; SAP2000'in load pattern → load case → combination → envelope zinciri; süperpozisyonla kombinasyon, TS 500 md. 6.2.6, TBDY 4.4.4, ÇYTHYE 5.3 birleşimleri, yön ve işaret çoğaltımı, zarf, belirleyen kombinasyon ve kolonda eş zamanlı (N, M) çiftleri; rüzgâr kat kuvveti ve kar.
sure: 75
---

## Neden?

Bir kirişin mesnet momentini sorduğunda tek bir sayı beklersin; oysa bina önce on iki ayrı **yük durumu** için çözülür ve kirişin o kesiti yetmiş dört **kombinasyonun** her birinde başka bir moment taşır. Tasarımcının işi bunların içinden en elverişsizini bulmaktır: kiriş donatısı için **zarf** (envelope), kolon için ise aynı anda oluşan eksenel kuvvet ve moment çifti. SAP2000, ETABS ve bu uygulamanın motoru aynı sırayı izler: yükleri ayrı ayrı tanımla, her birini bir kez çöz, sonuçları katsayılarla topla, en kötüsünü seç. Bu derste bu sıranın her halkasını el hesabıyla ve `yapi` motoruyla izleyeceksin.

::: sekil SAP2000 zinciri: yük tanımından tasarım değerine
<svg viewBox="0 0 440 210" width="100%" font-family="system-ui" font-size="11" fill="currentColor">
<rect x="6" y="20" width="96" height="74" rx="8" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="1.5"/>
<text x="54" y="38" text-anchor="middle" font-weight="700" fill="var(--sema-a,#3b82f6)">Load Pattern</text>
<text x="54" y="54" text-anchor="middle">yük deseni</text>
<text x="54" y="70" text-anchor="middle">G, Q, S, W±X/Y</text>
<text x="54" y="84" text-anchor="middle">EX±, EY±</text>
<rect x="118" y="20" width="96" height="74" rx="8" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5"/>
<text x="166" y="38" text-anchor="middle" font-weight="700" fill="var(--sema-b,#f59e0b)">Load Case</text>
<text x="166" y="54" text-anchor="middle">K u = F</text>
<text x="166" y="70" text-anchor="middle">tek K, çok sağ taraf</text>
<text x="166" y="84" text-anchor="middle">doğrusal statik</text>
<rect x="230" y="20" width="96" height="74" rx="8" fill="var(--sema-c-bg,rgba(16,185,129,.13))" stroke="var(--sema-c,#10b981)" stroke-width="1.5"/>
<text x="278" y="38" text-anchor="middle" font-weight="700" fill="var(--sema-c,#10b981)">Combination</text>
<text x="278" y="54" text-anchor="middle">Linear Add</text>
<text x="278" y="70" text-anchor="middle">Σ γᵢ · sonuçᵢ</text>
<text x="278" y="84" text-anchor="middle">çözüm yok</text>
<rect x="342" y="20" width="92" height="74" rx="8" fill="var(--sema-sil-bg,rgba(239,68,68,.11))" stroke="var(--sema-sil,#ef4444)" stroke-width="1.5"/>
<text x="388" y="38" text-anchor="middle" font-weight="700" fill="var(--sema-sil,#ef4444)">Envelope</text>
<text x="388" y="54" text-anchor="middle">zarf</text>
<text x="388" y="70" text-anchor="middle">max ve min</text>
<text x="388" y="84" text-anchor="middle">+ belirleyen</text>
<path class="ok" pathLength="1" d="M102 57H116" stroke="var(--sema-a,#3b82f6)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="111,52 117,57 111,62" stroke="var(--sema-a,#3b82f6)" stroke-width="2" fill="none"/>
<path class="ok" pathLength="1" d="M214 57H228" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="223,52 229,57 223,62" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<path class="ok" pathLength="1" d="M326 57H340" stroke="var(--sema-c,#10b981)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="335,52 341,57 335,62" stroke="var(--sema-c,#10b981)" stroke-width="2" fill="none"/>
<text x="54" y="118" text-anchor="middle" fill="var(--sema-a,#3b82f6)">yapi: yuk_durumlari</text>
<text x="166" y="118" text-anchor="middle" fill="var(--sema-b,#f59e0b)">se.coz_coklu</text>
<text x="278" y="118" text-anchor="middle" fill="var(--sema-c,#10b981)">kombinasyon_kisa</text>
<text x="388" y="118" text-anchor="middle" fill="var(--sema-sil,#ef4444)">veri["zarf"]</text>
<rect x="60" y="140" width="320" height="56" rx="8" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="4 3"/>
<text x="220" y="160" text-anchor="middle">12 durum çözülür (K bir kez ayrıştırılır),</text>
<text x="220" y="176" text-anchor="middle">84 kombinasyon toplanır, zarf her kesitte en kötüyü seçer;</text>
<text x="220" y="191" text-anchor="middle">kolon kontrolü zarftan değil kombinasyonun kendisinden okunur.</text>
</svg>
:::

## Yük durumları: G, Q, S, W, E

::: tanim Yük durumu
**Yük durumu** (load pattern), aynı kökenden gelen ve birlikte değişen yüklerin uzaydaki dağılımıdır: "nerede, ne kadar". Bir yük durumu tek başına iç kuvvet üretmez; çözülmesi gerekir. Her yük durumu yönetmelikte bir harfle anılır ve kombinasyonlarda kendi katsayısını alır.
:::

| Simge | Yük | Kaynak | Bu uygulamada |
|---|---|---|---|
| $G$ | sabit yük: öz ağırlık, kaplama, duvar | TS 498:2021 md. 5 (TS ISO 9194) | döşeme, kiriş, kolon, duvar |
| $Q$ | hareketli yük | TS 498:2021 md. 15.1 Çizelge 6 | kullanım sınıfından |
| $S$ | kar | TS 498:2021 md. 11 Çizelge 3, $s=\mu_1 S_k$ | çatı döşemelerine |
| $W$ | rüzgâr | TS 498:2021 md. 14, $W=C\,q(z)\,A$ | dört yön: W+X, W−X, W+Y, W−Y |
| $E$ | deprem | TBDY 2018 md. 4.4 ve 4.7 | EX±, EY± (±%5 dışmerkezlik), EZ |

Deprem iki parçadır. **Yatay deprem** $E_d^{(H)}$ eşdeğer deprem yüküyle her doğrultu için ayrı kurulur; bir sonraki derste $V_{tE}$ ve kat kuvvetlerini ayrıntılı hesaplayacağız. **Düşey deprem** ise TBDY Denk. (4.10) ile sabit yükün bir katıdır:

$$
\kutub{E_d^{(Z)}\approx\tfrac{2}{3}\,S_{DS}\,G}\qquad(S_{DS}=1.2\ \Rightarrow\ E_d^{(Z)}=0.8\,G)
$$

## SAP2000 zinciri ve bu uygulamadaki karşılığı

SAP2000'de **Load Pattern** yükün yerini ve değerini, **Load Case** onun nasıl çözüleceğini (doğrusal statik, modal, spektrum…), **Load Combination** çözülmüş sonuçların katsayılarla nasıl birleştirileceğini, **Envelope** ise birleşimlerin en büyük ve en küçük değerlerini tanımlar. Kombinasyon "Linear Add" türündeyse program yeni bir $K\mathbf{u}=\mathbf{F}$ çözmez; analiz sonrasında sonuçları ölçekleyip toplar.

| SAP2000 | Anlamı | `yapi` motorunda |
|---|---|---|
| Load Pattern (DEAD, LIVE, SNOW, WIND, QUAKE) | yükün dağılımı | `bina["yuk_durumlari"]`: G, Q, S, W, E |
| Load Case (Linear Static) | $K\mathbf{u}=\mathbf{F}$ çözümü | `se.coz_coklu`: $K$ bir kez ayrıştırılır, her durum bir sağ taraf |
| Mass Source ($G+n\,Q$) | deprem kütlesi | TBDY Tablo 4.3: $w_i=w_G+n\,w_Q$ |
| Diaphragm constraint | kat düzlemi rijit | kütle merkezinde efendi düğüm |
| Load Combination (Linear Add) | $\sum\gamma_i\cdot$ sonuç$_i$ | `veri["kombinasyonlar"]`, `yapi.kombinasyon_kisa` |
| Envelope | her büyüklük için max ve min | `veri["zarf"]`: `M_max`, `M_min`, `belirleyen` |

::: not Neden tek $K$?
Doğrusal statik çözümde rijitlik matrisi yükten bağımsızdır. $K$ bir kez $LDL^T$ biçiminde ayrıştırılınca her yük durumu yalnız bir ileri ve bir geri yerine koymadır. Bu yüzden yük durumu eklemek ucuzdur; kombinasyon eklemek daha da ucuzdur, çünkü hiç çözüm gerektirmez.

Betonarme binada deprem varsa **iki** $K$ vardır: TBDY md. 4.5.8 (Tablo 4.2) deprem hesabında çatlamış (etkin) kesit rijitliğini ister (kolon $0.70EI$, kiriş $0.35EI$), ama yalnız deprem birleşimlerinde ve onlara giren yükler altında (4.5.8.3). Motor brüt $K$ ile $G$, $Q$, $S$, $W$'yu; çatlamış $K$ ile deprem durumlarını ve $G$, $Q$, $S$'nin kopyaları `G~c`, `Q~c`, `S~c`'yi çözer. $1.4G+1.6Q$ brüt sonuçları, $G+Q+0.2S+E$ çatlamış sonuçları toplar; her $K$ içinde süperpozisyon yine geçerlidir.
:::

## Doğrusallık ve süperpozisyon

Malzeme doğrusal elastik ve yer değiştirmeler küçükse $K$ sabittir. O zaman yükleri toplamak ile çözümleri toplamak aynı sonucu verir:

$$
K\,\mathbf{u}_G=\ka{\mathbf{F}_G},\quad K\,\mathbf{u}_Q=\kb{\mathbf{F}_Q}
\ \ \Longrightarrow\ \
K\big(1.4\,\mathbf{u}_G+1.6\,\mathbf{u}_Q\big)=1.4\,\ka{\mathbf{F}_G}+1.6\,\kb{\mathbf{F}_Q}
$$

Aynı doğrusallık iç kuvvetlere de taşınır: her kesitte $\kutuc{M_{\text{komb}}(x)=\sum_i\gamma_i\,M_i(x)}$. Tepkiler, uç kuvvetleri ve ötelemeler de böyle toplanır.

::: uyari Süperpozisyonun bittiği yer
P-Delta, büyük yer değiştirme, çatlayan ya da akan malzeme, yalnız basınç taşıyan zemin yayı gibi **doğrusal olmayan** çözümlerde sonuçlar toplanamaz. SAP2000 belgeleri de doğrusal olmayan analiz sonuçlarının süperpoze edilmemesini, yüklerin bir "nonlinear case" içinde birleştirilmesini söyler. Bu durumda her kombinasyon ayrı bir çözümdür.
:::

## Yönetmelik birleşimleri

**TS 500 md. 6.2.6** betonarme için tasarım yükü $F_d$'yi şöyle verir ($T$: sıcaklık, büzülme, farklı oturma; $H$: yanal toprak itkisi):

| Denklem | Birleşim | Ne zaman |
|---|---|---|
| (6.3) | $1.4G+1.6Q$ | düşey yükler |
| (6.3) + TS 498 md. 3.1 | $1.4G+1.6Q+1.6S$ | kar varsa: kar hareketli yüktür |
| (6.4) | $G+1.2Q+1.2T$ | $T$ etkisi varsa |
| (6.5) | $G+1.3Q+1.3W$ | rüzgâr |
| (6.5) + TS 498 md. 12.1 | $G+1.3Q+1.3(S/2)+1.3W$ ve $G+1.3Q+1.3S+1.3(W/2)$ | kar ve rüzgâr birlikte |
| (6.6) | $0.9G+1.3W$ | rüzgâr, devrilme ve çekme |
| (6.9) | $1.4G+1.6Q+1.6H$ | toprak itkisi |
| (6.10) | $0.9G+1.6H$ | toprak itkisi |
| md. 6.2.6(f) | $G+Q$ (kar varsa $G+Q+S$) | kullanılabilirlik: bütün katsayılar 1.0 |

TS 500 md. 6.2.6 kar terimini **ayrı vermez**. Karakteristik yükleri TS 498'e bırakır; TS 498:2021 md. 3.1 kar yükünü hareketli yük sayar, md. 12.1 de kar ile rüzgârın birlikte etkisini iki durumla verir: $S/2+W$ ya da $S+W/2$ (eğimi 45°'ye kadar çatılarda, en elverişsizi). Bu yüzden kar $Q$ gibi katsayılandırılır.

TS 500'ün deprem satırları (6.7) ve (6.8) eski deprem yönetmeliğine dayanır; bugün betonarme binada deprem birleşimleri **TBDY 2018 md. 4.4.4** ile kurulur:

$$
\begin{aligned}
\text{(4.9):}\quad & E_d^{(H)}=\pm E_d^{(X)}\pm0.3\,E_d^{(Y)}\quad\text{ya da}\quad \pm0.3\,E_d^{(X)}\pm E_d^{(Y)}\\
\text{(4.11):}\quad & \kutua{G+Q+0.2S+E_d^{(H)}+0.3E_d^{(Z)}}\\
\text{(4.12):}\quad & \kutub{0.9G+H+E_d^{(H)}-0.3E_d^{(Z)}}
\end{aligned}
$$

$0.3E_d^{(Z)}=0.3\cdot\tfrac{2}{3}S_{DS}G=0.2\,S_{DS}\,G$ olduğundan (4.11)'de $G$'nin katsayısı $1+0.2S_{DS}$'ye çıkar, (4.12)'de $0.9-0.2S_{DS}$'ye iner. $S_{DS}=1.2$ için bunlar $\ka{1.24}$ ve $\kb{0.66}$'dır: (4.12) çekme, kalkma ve devrilme denetimi içindir.

**Çelik yapılar** ÇYTHYE 2018'e göre iki yöntemden biriyle tasarlanır. Yük ve Dayanım Katsayıları ile Tasarım (**YDKT**, md. 5.3.1) birleşimlerinde rüzgâr katsayısı 1.3 değil **1.6**'dır: $1.4G$, $1.2G+1.6Q+0.5S$, $1.2G+Q+0.5S+1.6W$, $0.9G+1.6W$ … Güvenlik Katsayıları ile Tasarım (**GKT**, md. 5.3.2) ise $G+Q$, $G+W$, $0.6G+W$, $G+0.7E$ gibi katsayısı 1 civarında birleşimler kullanır. Deprem satırında TBDY md. 9.2.5.1 (ve 4.4.4.2a) çelik YDKT için (4.11)'deki $G$ yerine **$1.2G$** yazar: $1.2G+Q+0.2S+E_d^{(H)}+0.3E_d^{(Z)}$.

::: tanim Kombinasyon kümesi
Bu uygulamada bina kartındaki `kombinasyon_kumesi` üç kümeden birini seçer: `ts500` (TS 500 + TBDY 4.4.4), `cythye_ydkt` (ÇYTHYE 5.3.1 + TBDY 9.2.5.1) ve `cythye_gkt` (ÇYTHYE 5.3.2 + TBDY Denk. 9.1). Bir satırın varlık nedeni olan durum yoksa (6.4'te $T$, 6.9 ve 6.10'da $H$) satır **uygulanmaz**; ikincil terim yoksa ($0.2S$, $H$) sıfır alınır.
:::

## Kombinasyon sayısının patlaması

Rüzgâr dört yönden eser: W+X, W−X, W+Y, W−Y. Bu yüzden (6.5) ve (6.6)'nın her biri **dört** kombinasyon olur. Deprem daha çok çoğalır: Denk. (4.9)'da asıl doğrultu X ya da Y (2), asıl terimin işareti (2), ikincil terimin işareti (2), asıl doğrultuda $+$ ya da $-$%5 dışmerkezlik (2), ikincil doğrultuda dışmerkezlik (2):

$$
\underbrace{2}_{\text{asıl yön}}\times\underbrace{2}_{\pm E_{\text{asıl}}}\times\underbrace{2}_{\pm0.3E_{\text{ikincil}}}\times\underbrace{2}_{e_{\text{asıl}}=\pm5\%}\times\underbrace{2}_{e_{\text{ikincil}}=\pm5\%}=\kutusil{32}
$$

(4.11) ve (4.12)'nin her biri 32 kombinasyondur. Kar–rüzgâr satırları da dörder yöne açılır. Üç katlı ders binasında: $1+1+4+4+4+4+32+32+1+1=\kutuc{84}$ dayanım ve servis kombinasyonu, ayrıca göreli kat ötelemesi için dört tek doğrultulu birleşim. Elle yazılacak iş değildir; motor şablon satırlarını eldeki durumlarla otomatik açar ve her birine katsayılardan bir ad verir: `G+Q+0.2S+EX++0.3EY-+0.3EZ` gibi.

## Zarf ve belirleyen kombinasyon

**Zarf** (envelope), her büyüklük ve her kesit için bütün kombinasyonların en büyüğü ve en küçüğüdür. Zarfı kuran kombinasyona o kesitteki **belirleyen kombinasyon** denir. Bir kirişte mesnet momentini çoğunlukla deprem, açıklık momentini düşey yük belirler; zarf eğrisi kesitten kesite farklı kombinasyonlardan parçalar alır.

$$
M_{\max}(x)=\max_k\sum_i\gamma_{ki}\,M_i(x),\qquad M_{\min}(x)=\min_k\sum_i\gamma_{ki}\,M_i(x)
$$

Aşağıda ders binasının bir kirişinin $G$, $Q$ ve $E$ diyagramları var. Katsayıları değiştirip kendi kombinasyonunu çiz; zarfın üst ve alt eğrisi her bölgede belirleyen ailenin renginde görünür. $S_{DS}$'yi değiştirince deprem birleşimlerindeki $G$ katsayısı da değişir.

::: etkilesim kombinasyon-zarfi
{"gG": 1.4, "gQ": 1.6, "gE": 0, "SDS": 1.2, "x": 5}
:::

## Kolon: zarf değil, eş zamanlı (N, M) çifti

Kiriş donatısı her kesitte zarfa göre konabilir: alt donatı $M_{\max}$'a, üst donatı $M_{\min}$'e göre. Kolon ise **eksenel kuvvet ve momenti birlikte** taşır ve dayanımı ikisinin etkileşimine (N–M etkileşim diyagramı) bağlıdır. Zarfın $N_{\min}$'i bir kombinasyondan, $M_{\max}$'ı başka birinden gelir; $(N_{\min},M_{\max})$ çifti hiçbir anda oluşmaz.

::: sekil Kolon için doğru noktalar: her kombinasyonun kendi (N, M) çifti
<svg viewBox="0 0 420 230" width="100%" font-family="system-ui" font-size="11" fill="currentColor">
<path d="M60 200H400M60 200V14" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.4" fill="none"/>
<text x="400" y="216" text-anchor="end">M (kN·m)</text>
<text x="66" y="18">basınç N (kN)</text>
<path d="M60 22C210 26 330 80 352 130C362 160 300 196 60 200" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="5 4" fill="none"/>
<text x="300" y="70" fill="var(--sema-cizgi,#94a3b8)">N–M etkileşim eğrisi</text>
<circle cx="120" cy="58" r="5" fill="var(--sema-a,#3b82f6)"/>
<text x="128" y="54" fill="var(--sema-a,#3b82f6)">(394.7; 26.3) N_min kombinasyonu</text>
<circle cx="236" cy="80" r="5" fill="var(--sema-b,#f59e0b)"/>
<text x="244" y="94" fill="var(--sema-b,#f59e0b)">(380.4; 89.1) M_max kombinasyonu</text>
<rect x="231" y="53" width="10" height="10" fill="none" stroke="var(--sema-sil,#ef4444)" stroke-width="2"/>
<text x="246" y="40" fill="var(--sema-sil,#ef4444)">zarf köşesi (394.7; 89.1): gerçek değil</text>
<path d="M120 58H231M236 80V63" stroke="var(--sema-sil,#ef4444)" stroke-dasharray="3 3" fill="none"/>
<circle cx="80" cy="172" r="5" fill="var(--sema-c,#10b981)"/>
<text x="88" y="168" fill="var(--sema-c,#10b981)">(76.9; 11.7) N_max: az basınç, 0.9G − E</text>
</svg>
:::

Doğru yol, her kombinasyonun kendi $(N,M)$ çiftini etkileşim diyagramıyla karşılaştırmaktır. SAP2000 ve ETABS kolon tasarımında bunu yapar: her istasyonda her kombinasyon için $(N_d,M_{d2},M_{d3})$ noktası ayrı denetlenir. Zarfın köşesi güvenli tarafta kalabilir ama gereksiz donatıya yol açar; tersine, az basınçlı $0.9G-E$ çifti zarfın köşesinde hiç görünmez, oysa çoğu zaman belirleyen odur.

## Rüzgâr ve kar

**Rüzgâr** (TS 498:2021 md. 14): bileşke $W=C\,q\,A$. Emme basıncı $q$ zeminden yüksekliğe göre Çizelge 4'ten basamaklı alınır ($q=v^2/1600$): 8 m'ye kadar 0.5, 8–20 m 0.8, 20–100 m 1.1, 100 m'den yukarı 1.3 kN/m². Kapalı binada rüzgâra bakan yüzün basıncı $+0.8q$ ile arka yüzün emmesi $-0.4q$ toplanır: $C=1.2$ (Çizelge 5; kule tipi 1.6). Kat kuvveti kat düzeyindeki $q$ ile, kat yüksekliğinin yarısı alttan yarısı üstten olmak üzere:

$$
\kutua{F_i=C\,q(z_i)\,B\,h_{\text{pay}}},\qquad h_{\text{pay}}=\tfrac{h_i}{2}+\tfrac{h_{i+1}}{2},\qquad V_t=\sum_i F_i
$$

::: etkilesim ruzgar-kat-kuvveti
{"kat": 3, "h": 3.2, "B": 8, "C": 1.2}
:::

**Kar** (TS 498:2021 md. 11): karakteristik zemin kar yükü $S_k$ kar bölgesi (1–9) ve rakımla Çizelge 3'ten okunur; 1000 m üstünde 1500 m'ye kadar %10, daha yukarıda %15 artırılır. Çatı kar yükü TS EN 1991-1-3 ile $s=\mu_1\,C_e\,C_t\,S_k$ olur; düz ya da 30°'ye kadar eğimli çatıda $\mu_1=0.8$, $C_e=C_t=1$. Kar yalnız çatı döşemelerine konur; TS 500 kümesinde hareketli yük gibi $1.6S$ (ve rüzgârla $1.3\cdot S/2$ ya da $1.3S$) ile, TBDY (4.11)'de $0.2S$ ile, deprem kütlesine çatıda %30 ile girer.

::: hata Zarfın köşesiyle kolon tasarlamak
$N_{\max}$, $N_{\min}$, $M_{\max}$ ve $M_{\min}$'i ayrı ayrı alıp $(N_{\min},M_{\max})$ gibi bir çiftle kolon denetlemek hem gerçek dışı hem de tehlikeli olabilir: az basınçlı $0.9G-E$ durumunda kolonun eğilme kapasitesi düşer ve bu çift zarfta yoktur. Her kombinasyonun kendi çiftini denetle; motor `kombinasyon_kisa(r.ic, ad)` ile her kombinasyonun tam diyagramlarını verir.
:::

::: hata Kombinasyonda en büyükleri toplamak
$\max(M_G)+\max(M_Q)$ genellikle $\max(M_G+M_Q)$'dan büyüktür, çünkü iki en büyük değer farklı kesitlerde oluşur. Kombinasyon **her kesitte** ayrı toplanır, en büyük değer sonra aranır. Tersine sıralama gereksiz büyük kesitler verir; süperpozisyon kanıtı örneğinde fark açıkça görülür.
:::

::: hata Depremin işaretini tek yönlü almak
Deprem ileri geri sallar: $E_d^{(H)}$ her zaman $\pm$ ile girer ve bir kirişin iki ucunda moment işaretini değiştirir. Yalnız $+E$ ile kurulmuş kombinasyon listesi zarfın yarısını kaçırır. Rüzgâr da öyle: dört yön ayrı durumdur.
:::

## Çözümlü örnekler

Bina örnekleri `betonarme-3kat-3x3` şablonunu kullanır: akslar A–B–C (0, 5, 10 m) ve 1–2–3 (0, 4, 8 m), üç kat 3.2 m, 45×45 kolon, 25×55 kiriş, 15 cm döşeme, büro yükü; deprem ($S_S=1.0$, $S_1=0.3$, ZC, A11), kar (bölge 3) ve rüzgâr açık, `ts500` kümesi. Aynı binayı [Bina sayfasında aç](#bina/sablon/betonarme-3kat-3x3).

::: ornek Süperpozisyonun kanıtı: kombinasyonu ayrıca çözmek
İki açıklıklı sürekli kiriş (0–5–10 m, üç mesnet). $G$: her iki açıklıkta 20 kN/m; $Q$: yalnız birinci açıklıkta 10 kN/m. Önce $G$ ve $Q$'yu ayrı çöz, sonra yükleri $1.4G+1.6Q$ olarak birleştirip **yeniden** çöz. Orta mesnet momenti ve tepkiler $1.4\cdot G+1.6\cdot Q$ sonucuna eşit mi? Açıklıkların en büyük momentleri de toplanır mı?
--- ipucu
Birleşik yük: birinci açıklıkta $1.4\cdot20+1.6\cdot10=44$, ikincide $1.4\cdot20=28$ kN/m.
--- cevap
$$
\begin{aligned}
M_B:\quad & 1.4\cdot(\ka{-62.5})+1.6\cdot(\kb{-15.625})=-87.5-25=\kutuc{-112.5}=M_B^{\text{yeniden çözüm}}\ \checkmark\\
R_A:\quad & 1.4\cdot\ka{37.5}+1.6\cdot\kb{21.875}=\kutuc{87.5},\quad R_B=175+50=\kutuc{225},\quad R_C=52.5+1.6\cdot(\kb{-3.125})=\kutuc{47.5}
\end{aligned}
$$
Açıklık en büyükleri: $G$'de $35.16$ ($x=1.875$), $Q$'da $23.93$ ($x\approx2.19$); $1.4\cdot35.16+1.6\cdot23.93=\ksil{87.50}$, oysa birleşik çözümün en büyüğü $\kc{87.00}$ kN·m ($x\approx1.98$).
--- kod
kiris = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 5}, {"no": 3, "x": 10}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "32e6", "I": "0.0026"}, {"no": 2, "dugumler": [2, 3], "E": "32e6", "I": "0.0026"}], "mesnetler": [{"dugum": 1, "uy": True}, {"dugum": 2, "uy": True}, {"dugum": 3, "uy": True}], "yukler": []}
G = dict(kiris, yayili=[{"eleman": 1, "q": -20}, {"eleman": 2, "q": -20}])
Q = dict(kiris, yayili=[{"eleman": 1, "q": -10}])
K = dict(kiris, yayili=[{"eleman": 1, "q": -44}, {"eleman": 2, "q": -28}])
se.se_coz(G), se.se_coz(Q), se.se_coz(K)
--- kontrol
all(abs(k["Fy"] - (1.4 * g["Fy"] + 1.6 * q["Fy"])) < 1e-9 for g, q, k in zip(r[0].veri["tepkiler"], r[1].veri["tepkiler"], r[2].veri["tepkiler"])) and abs(r[2].veri["elemanlar"][0]["diyagram"]["M"][-1] - (1.4 * r[0].veri["elemanlar"][0]["diyagram"]["M"][-1] + 1.6 * r[1].veri["elemanlar"][0]["diyagram"]["M"][-1])) < 1e-9 and max(r[2].veri["elemanlar"][0]["diyagram"]["M"]) < 1.4 * max(r[0].veri["elemanlar"][0]["diyagram"]["M"]) + 1.6 * max(r[1].veri["elemanlar"][0]["diyagram"]["M"]) - 0.4
--- yorum
Yeniden çözüm, toplamla aynı tepkiyi ve aynı orta mesnet momentini verdi: doğrusal sistemde kombinasyon için çözüme gerek yoktur. En büyük değerler ise toplanmaz; kombinasyonu her kesitte kurup en büyüğü sonra aramak gerekir. $Q$'nun yalnız bir açıklıkta olması (hareketli yükün en elverişsiz düzenlemesi, TS 500 md. 6.3.3) $C$ mesnedinde $-3.125$ kN'luk kalkma üretti.
:::

::: ornek 1.4G + 1.6Q: kiriş diyagramı katsayılı toplamdır
1. kattaki iç kiriş K-A2→B2 (eleman 30, 5 m) için motorun $G$ ve $Q$ moment diyagramlarından sol uç, orta ve sağ uçta $1.4G+1.6Q$ momentini elle bul; `kombinasyon_kisa` sonucuyla karşılaştır.
--- ipucu
$G$: $-30.821$, $23.823$, $-40.408$; $Q$: $-10.399$, $7.976$, $-12.983$ kN·m.
--- cevap
$$
\begin{aligned}
x=0:\quad & 1.4\cdot(\ka{-30.821})+1.6\cdot(\kb{-10.399})=-43.149-16.638=\kutuc{-59.79}\\
x=2.5:\quad & 1.4\cdot\ka{23.823}+1.6\cdot\kb{7.976}=33.352+12.762=\kutuc{46.11}\\
x=5:\quad & 1.4\cdot(\ka{-40.408})+1.6\cdot(\kb{-12.983})=-56.571-20.773=\kutuc{-77.34}\ \text{kN·m}
\end{aligned}
$$
Motor aynı toplamı on bir istasyonun hepsinde yapar: $-59.788$, $46.113$, $-77.344$. Bu birleşim deprem içermediği için brüt kesitli $G$ ve $Q$'yu toplar.
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
all(abs(m - (1.4 * g + 1.6 * q)) < 1e-3 for m, g, q in zip(next(e for e in yapi.kombinasyon_kisa(r.ic, "1.4G+1.6Q")["elemanlar"] if e["no"] == 30)["M"], next(e for e in r.veri["durumlar"]["G"]["elemanlar"] if e["no"] == 30)["M"], next(e for e in r.veri["durumlar"]["Q"]["elemanlar"] if e["no"] == 30)["M"])) and abs(next(e for e in yapi.kombinasyon_kisa(r.ic, "1.4G+1.6Q")["elemanlar"] if e["no"] == 30)["M"][-1] + 77.344) < 1e-3
--- yorum
`yapi.kombinasyon_kisa(r.ic, ad)` istenen kombinasyonun bütün diyagramlarını, tepkilerini ve ötelemelerini **yeniden çözmeden** verir: içeride `_Paket.birlesim` her diziyi $\sum\gamma_i\cdot$ dizi$_i$ olarak toplar. SAP2000'de "Linear Add" kombinasyonunun yaptığı da budur.
:::

::: ornek Deprem kombinasyonu: kolonun eksenel kuvveti
Köşe kolon A1'in 1. kat parçası (eleman 1) için deprem birleşimine giren durumların eksenel kuvvetleri (basınç $-$; $G$, $Q$, $S$ çatlamış kesitli $K$'den: `G~c`, `Q~c`, `S~c`): $N_G=-232.50$, $N_Q=-29.26$, $N_S=-2.86$, $N_{EX+}=+48.50$, $N_{EY+}=+57.65$ kN; $S_{DS}=1.2$. `G+Q+0.2S+EX++0.3EY++0.3EZ` kombinasyonunun eksenel kuvvetini bul.
--- ipucu
$E_d^{(Z)}=\tfrac{2}{3}\cdot1.2\cdot G=0.8\,G$; motor bunu `EZ` durumu olarak kurar ($N_{EZ}=-186.00$).
--- cevap
$$
\begin{aligned}
N&=\ka{N_G}+\kb{N_Q}+0.2N_S+\kc{N_{EX+}}+0.3N_{EY+}+0.3\cdot\underbrace{0.8N_G}_{N_{EZ}}\\
&=\ka{1.24}\cdot(-232.50)+(-29.26)+0.2\cdot(-2.86)+48.50+0.3\cdot57.65\\
&=-288.30-29.26-0.57+48.50+17.29=\kutuc{-252.33}\ \text{kN}
\end{aligned}
$$
+X depremi devirme momentiyle A aksındaki kolonu **çeker**: $1.4G+1.6Q$'daki $-370.1$ kN basınç burada $-252.3$'e iner. Brüt kesitli $G$'de $N_G=-230.80$ kN'dur; çatlamış $K$'de kirişler yumuşadığı için kolonlar arası paylaşım biraz değişir, toplam düşey yük aynıdır.
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
abs(next(e for e in yapi.kombinasyon_kisa(r.ic, "G+Q+0.2S+EX++0.3EY++0.3EZ")["elemanlar"] if e["no"] == 1)["N"][0] - sum(g * next(e for e in yapi.kombinasyon_kisa(r.ic, d)["elemanlar"] if e["no"] == 1)["N"][0] for d, g in {"G~c": 1, "Q~c": 1, "S~c": 0.2, "EX+": 1, "EY+": 0.3, "EZ": 0.3}.items())) < 1e-2 and abs(next(e for e in yapi.kombinasyon_kisa(r.ic, "G+Q+0.2S+EX++0.3EY++0.3EZ")["elemanlar"] if e["no"] == 1)["N"][0] + 252.332) < 1e-2 and r.veri["deprem"]["EZ_katsayi"] == 0.8
--- yorum
`veri["kombinasyonlar"]` her kaydın `katsayilar` sözlüğünü taşır: burada `{"G": 1, "Q": 1, "S": 0.2, "EX+": 1, "EY+": 0.3, "EZ": 0.3}`; `catlamis: true` alanı $G$, $Q$, $S$'nin çatlamış kesitli kopyalardan alındığını söyler (`r.ic["kombinasyonlar"]` hesapta kullanılan `G~c`, `Q~c`, `S~c` adlarını gösterir). EZ durumu $0.8\,G$ olduğundan $0.3E_d^{(Z)}$ terimi sabit yükü yüzde 24 artırır; (4.12)'de ise aynı oranda azaltır.
:::

::: ornek Kaç kombinasyon? Yön ve işaret çoğaltımı
`ts500` kümesinin satırları G, Q, S, W ve E durumları açık ders binasında kaç kombinasyona açılır? Hangi satırlar uygulanmaz?
--- ipucu
Rüzgâr 4 yön; kar açık olduğundan $1.6S$ satırı, kar–rüzgâr iki satırı ve $G+Q+S$ de var; deprem Denk. (4.9) $\times$ dışmerkezlik $=32$; $T$ ve $H$ durumu yok.
--- cevap
$$
\underbrace{1+1}_{(6.3),\ +1.6S}+\underbrace{4}_{(6.5)}+\underbrace{4+4}_{S/2+W,\ S+W/2}+\underbrace{4}_{(6.6)}+\underbrace{32}_{(4.11)}+\underbrace{32}_{(4.12)}+\underbrace{1+1}_{G+Q,\ G+Q+S}=\kutuc{84},\qquad \text{öteleme: }\underbrace{4}_{G+Q\pm EX,\ \pm EY}
$$
Uygulanmayan: $\ksil{(6.4)}$ ($T$ yok), $\ksil{(6.9)}$ ve $\ksil{(6.10)}$ ($H$ yok). (4.12)'deki $H$ ikincil terimdir, sıfır alınır ve satır uygulanır.
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
r.veri["zarf"]["kombinasyon_sayisi"] == 84 and r.veri["ozet"]["drift_kombinasyon_sayisi"] == 4 and sum(1 for k in r.veri["kombinasyonlar"] if k["aile"] == "G+Q+0.2S+Ed(H)+0.3Ed(Z)" and k["uygulandi"]) == 32 and sum(1 for k in r.veri["kombinasyonlar"] if k["aile"] == "G+1.3Q+1.3W" and k["uygulandi"]) == 4 and sorted(k["aile"] for k in r.veri["kombinasyonlar"] if not k["uygulandi"]) == ["0.9G+1.6H", "1.4G+1.6Q+1.6H", "G+1.2Q+1.2T"]
--- yorum
Durum sayısı 12'dir (G, Q, S, dört W, dört E, EZ), pakette ayrıca deprem birleşimleri için çatlamış kesitli G~c, Q~c, S~c var. Hepsi bu on beş çözümün katsayılı toplamı olduğu için 84 kombinasyon motorda tek bir matris çarpımıdır: $\Gamma_{84\times15}\,D_{15\times L}$.
:::

::: ornek Zarf ve belirleyen kombinasyon: kiriş mesnet momenti
Eleman 30'un (K-A2→B2/k1) zarfında $M_{\min}$ ve $M_{\max}$ nedir, hangi kombinasyon belirler? $M_{\min}$'i sağ uçta elle doğrula (deprem birleşimi: çatlamış kesitli $M_G=-39.595$, $M_Q=-12.882$, $M_S=0.007$; $M_{EX+}=-47.013$, $M_{EY+}=0$).
--- ipucu
Sağ uçta $G$, $Q$ ve $EX+$ aynı işaretli: (4.11) $+EX$ en olumsuz.
--- cevap
$$
\begin{aligned}
M_{\min}&=\ka{1.24}\cdot(-39.595)+(-12.882)+0.2\cdot0.007+(\kc{-47.013})\\
&=-49.098-12.882+0.001-47.013=\kutusil{-108.99}\ \text{kN·m}\quad(\texttt{G+Q+0.2S+EX++0.3EY++0.3EZ})
\end{aligned}
$$
$M_{\max}=\kutuc{46.14}$ kN·m ise açıklık ortasında ($x=2.5$ m) karlı düşey birleşim `1.4G+1.6Q+1.6S`'ten gelir; deprem birleşimi açıklıkta en çok $43.55$ verir. Düşey yük kombinasyonu $1.4G+1.6Q$ mesnette yalnız $-77.34$'e iner; mesnet donatısını deprem, açıklık donatısını düşey yük belirler.
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
abs(next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 30)["M_min"] + 108.991) < 1e-3 and next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 30)["belirleyen"]["M_min"] == "G+Q+0.2S+EX++0.3EY++0.3EZ" and abs(next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 30)["M_max"] - 46.1416) < 1e-3 and next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 30)["belirleyen"]["M_max"] == "1.4G+1.6Q+1.6S" and abs(min(next(e for e in yapi.kombinasyon_kisa(r.ic, "G+Q+0.2S+EX++0.3EY++0.3EZ")["elemanlar"] if e["no"] == 30)["M"]) + 108.991) < 1e-3
--- yorum
`veri["zarf"]["elemanlar"]` her eleman ve her büyüklük için `_max`, `_min` ve `belirleyen` adını verir; bütün kombinasyonlar tek matris çarpımıyla taranır. Belirleyen adı `kombinasyon_kisa`'ya verip o kombinasyonun tam diyagramını açabilirsin.
:::

::: ornek Kolon A1: zarf köşesi mi, gerçek çift mi?
Eleman 1'in (köşe kolon A1, 1. kat) zarfında en büyük basınç ($N_{\min}$) ve en büyük $M$ hangi kombinasyonlardan gelir? Her kombinasyonda öteki büyüklüğün değeri nedir?
--- ipucu
`belirleyen["N_min"]` ile `belirleyen["M_max"]` farklı mı? Her birini `kombinasyon_kisa` ile aç.
--- cevap
$$
\begin{aligned}
\ka{N_{\min}}:\quad & \texttt{G+Q+0.2S-0.3EX+-EY-+0.3EZ}\ \Rightarrow\ (N,M)=(\ka{-394.7},\ 26.3)\\
\kb{M_{\max}}:\quad & \texttt{G+Q+0.2S-EX--0.3EY++0.3EZ}\ \Rightarrow\ (N,M)=(-380.4,\ \kb{89.1})\\
\text{zarf köşesi:}\quad & (\ksil{-394.7},\ \ksil{89.1})\ \ \text{hiçbir kombinasyonda yok}
\end{aligned}
$$
Az basınç ucu da ayrıca denetlenir: $N_{\max}=-76.9$ kN, `0.9G+0.3EX++EY--0.3EZ`.
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 1)["belirleyen"]["N_min"] != next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 1)["belirleyen"]["M_max"] and abs(max(next(e for e in yapi.kombinasyon_kisa(r.ic, next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 1)["belirleyen"]["N_min"])["elemanlar"] if e["no"] == 1)["M"]) - 26.266) < 1e-2 and abs(next(e for e in yapi.kombinasyon_kisa(r.ic, next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 1)["belirleyen"]["M_max"])["elemanlar"] if e["no"] == 1)["N"][0] + 380.403) < 1e-2 and abs(next(z for z in r.veri["zarf"]["elemanlar"] if z["no"] == 1)["N_min"] + 394.726) < 1e-3
--- yorum
Kolon etkileşim diyagramında $(394.7;\,26.3)$ ve $(380.4;\,89.1)$ noktaları ayrı ayrı denetlenir, ayrıca $(76.9;\,11.7)$ gibi az basınçlı noktalar. TBDY md. 7.3.1.2'deki $N_{dm}\le0.40f_{ck}A_c$ sınırı ise en büyük basıncı ister: orada zarfın $N_{\min}$'i doğru büyüklüktür.
:::

::: ornek Rüzgâr kat kuvvetleri: el hesabı ve motor
Ders binasında X yönündeki rüzgâr (W+X) Y doğrultusundaki 8 m genişliğindeki cepheye çarpıyor; kat yüksekliği 3.2 m, $C=1.2$. Kat kuvvetlerini ve taban kesmesini bul.
--- ipucu
$z=3.2$ ve $6.4$ m'de $q=0.5$; $z=9.6>8$ m'de $q=0.8$ kN/m². Çatı katının payı yalnız alttaki yarım kattır.
--- cevap
$$
\begin{aligned}
F_1&=1.2\cdot\kb{0.5}\cdot8\cdot\ka{3.2}=\kutua{15.36},\qquad F_2=1.2\cdot0.5\cdot8\cdot3.2=\kutua{15.36}\\
F_3&=1.2\cdot\kb{0.8}\cdot8\cdot\ka{1.6}=\kutua{12.288}\\
V_t&=15.36+15.36+12.288=\kutuc{43.008}\ \text{kN}
\end{aligned}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
[k["F_x"] for k in r.veri["ruzgar"]["katlar"]] == [15.36, 15.36, 12.288] and [k["q"] for k in r.veri["ruzgar"]["katlar"]] == [0.5, 0.5, 0.8] and abs(r.veri["ruzgar"]["toplam_x"] - 43.008) < 1e-9 and abs(sum(t["FX"] for t in r.veri["durumlar"]["W+X"]["tepkiler"]) + 43.008) < 1e-3
--- yorum
Temel tepkilerinin toplamı $-43.008$ kN: rüzgâr kuvveti eksiksiz zemine indi. Y yönünde cephe 10 m olduğundan $V_t=53.76$ kN. Aynı binada deprem taban kesmesi 289 kN'dur; alçak betonarme binada rüzgâr kombinasyonları zarfa nadiren girer, yüksek ya da hafif (çelik çatı) yapıda ise belirleyici olabilir.
:::

::: ornek Kar: Çizelge 3, μ1 ve çatı yükü
Ders binası 4. kar bölgesinde, 900 m rakımda olsun. Düz çatı için $S_k$, $s$, çatıya gelen toplam kar yükünü ve deprem kütlesine giren payı bul. Çatı 10×8 m.
--- ipucu
Çizelge 3, bölge 4, rakım ≤ 900 m sütunu; $\mu_1=0.8$.
--- cevap
$$
\begin{aligned}
S_k&=\kutub{1.10}\ \text{kN/m}^2\ (\text{Çizelge 3, bölge 4, 900 m}),\qquad s=\ka{\mu_1}\,S_k=0.8\cdot1.10=\kutua{0.88}\ \text{kN/m}^2\\
S_{\text{toplam}}&=0.88\cdot(10\cdot8)=\kutuc{70.4}\ \text{kN},\qquad \text{kütleye: }0.3\cdot70.4=21.12\ \text{kN}
\end{aligned}
$$
--- kod
b = yapi.bina_sablon("betonarme-3kat-3x3")
b["yuk_durumlari"]["S"].update({"bolge": 4, "rakim": 900})
r = yapi.bina_coz(b)
r
--- kontrol
r.veri["kar"]["Sk"] == 1.1 and abs(r.veri["kar"]["s"] - 0.88) < 1e-9 and abs(r.veri["kar"]["S_toplam"] - 70.4) < 1e-6 and abs(sum(t["FZ"] for t in r.veri["durumlar"]["S"]["tepkiler"]) - 70.4) < 1e-2
--- yorum
Kar yalnız en üst kat döşemelerine 45° kuralıyla dağıtılır ve S durumu olarak çözülür. Deprem birleşiminde $0.2S$, kat kütlesinde $0.3S$ girer; TS 500 kümesinde kar hareketli yük gibi $1.6S$ ile (TS 498:2021 md. 3.1), rüzgârla birlikte md. 12.1'in iki durumuyla ($S/2+W$ ya da $S+W/2$, eğimi 45°'ye kadar çatılarda) girer; motor bu satırları kendisi açar.
:::

::: ornek Çelik kolon: TS 500 mi, ÇYTHYE mi?
Bir çelik çerçeve kolonunun durumları: $N_G=-120$, $N_Q=-40$, $N_W=\pm60$, $N_E=\pm50$ kN (basınç $-$), $S=0$, $S_{DS}=1.2$. ÇYTHYE YDKT ve TBDY 9.2.5.1 birleşimleriyle en büyük basıncı ve en küçük basıncı (ya da çekmeyi) bul; betonarme (TS 500 + TBDY 4.11/4.12) değerleriyle karşılaştır.
--- ipucu
$0.3E_d^{(Z)}=0.24\,G$. Çelik YDKT deprem satırında $G$ yerine $1.2G$; rüzgâr katsayısı 1.6.
--- cevap
$$
\begin{aligned}
\text{ÇYTHYE YDKT:}\quad & 1.4G=-168,\quad 1.2G+1.6Q=-208,\quad 1.2G+Q\mp1.6W=\kutusil{-280}\ /\ -88\\
& 0.9G\pm1.6W=-204\ /\ \kutuc{-12},\quad (1.2+0.24)G+Q\mp E=-262.8\ /\ -162.8\\
& (0.9-0.24)G\pm E=-129.2\ /\ -29.2\\[2pt]
\text{TS 500 + TBDY:}\quad & 1.4G+1.6Q=-232,\quad G+1.3Q\mp1.3W=\ka{-250}\ /\ -94,\quad 0.9G\pm1.3W=-186\ /\ -30\\
& 1.24G+Q\mp E=-238.8\ /\ -138.8,\quad 0.66G\pm E=-129.2\ /\ \kb{-29.2}
\end{aligned}
$$
Çelikte en büyük basınç $-280$ kN (rüzgârlı satır), en küçük $-12$ kN; betonarme kümesinde $-250$ ve $-29.2$ kN.
--- yorum
Aynı durum değerleri iki kümede farklı tasarım kuvveti verir; kümeyi malzeme ve tasarım yöntemi seçer, karıştırılmaz. ÇYTHYE'de rüzgârın 1.6 ile girmesi hafif çelik yapılarda rüzgârı çoğu zaman belirleyici yapar. Bina kartında `kombinasyon_kumesi: "cythye_ydkt"` seçilirse motor bu satırları kendisi açar.
:::

::: muhendislik SAP2000'de aynı iş, farklı adlar
SAP2000'de "Define → Load Patterns" ile G, Q, W, E tanımlanır; her biri için aynı adlı "Linear Static" load case kendiliğinden oluşur. "Define → Load Combinations → Add Default Design Combos" seçilen tasarım koduna göre kombinasyonları üretir; Türkiye'de çoğu kullanıcı TBDY 2018 birleşimlerini elle tanımlar. Kombinasyon türü **Linear Add** toplam, **Envelope** zarftır; spektrum analizinde sonuçlar işaretsiz geldiği için program alt kombinasyonlar üretir. Kolon tasarımında program zarfı değil, her kombinasyonun $(N, M_2, M_3)$ noktasını etkileşim yüzeyiyle karşılaştırır.

Tarihi yığma köprüde de aynı mantık geçerlidir ama kombinasyon daha azdır: öz ağırlık ve dolgu ($G$), trafik ($Q$), sıcaklık ve deprem. OMA ile ölçülen modlar sonlu eleman modelini güncellemeye yarar; güncellenen model doğrusal kalırsa her durum bir kez çözülür, kombinasyonlar yine toplanır.
:::

::: ozet Özet
- Yük durumları ayrı ayrı tanımlanır ve çözülür: $G$, $Q$ (TS 498:2021), $S=\mu_1S_k$ (md. 11 Çizelge 3), $W=C\,q(z)\,A$ (md. 14 Çizelge 4, $C=1.2$), $E$: EX±, EY± (±%5 dışmerkezlik) ve $E_d^{(Z)}=\tfrac{2}{3}S_{DS}G$.
- SAP2000 zinciri: Load Pattern → Load Case ($K$ bir kez, çok sağ taraf) → Combination (Linear Add: $\sum\gamma_i\cdot$ sonuç$_i$, çözüm yok) → Envelope. Süperpozisyon yalnız doğrusal çözümde geçerlidir.
- TS 500 md. 6.2.6: $1.4G+1.6Q$, $G+1.3Q\pm1.3W$, $0.9G\pm1.3W$, servis $G+Q$; kar TS 498 md. 3.1 ile hareketli yük ($1.6S$), kar + rüzgâr md. 12.1 ($S/2+W$ ya da $S+W/2$). TBDY 4.4.4: $G+Q+0.2S+E_d^{(H)}+0.3E_d^{(Z)}$ ve $0.9G+H+E_d^{(H)}-0.3E_d^{(Z)}$, $E_d^{(H)}=\pm E_X\pm0.3E_Y$. ÇYTHYE YDKT rüzgârda 1.6, TBDY 9.2.5.1 çelik depremde $1.2G$; GKT katsayıları 1 civarı.
- Yön ve işaret çoğaltımı: rüzgâr 4, deprem 32 varyant; ders binasında 84 kombinasyon + 4 öteleme birleşimi. Betonarme deprem birleşimleri çatlamış kesitli ikinci bir $K$'den gelir (TBDY 4.5.8.3).
- Zarf her büyüklük ve kesit için max ve min ile belirleyen kombinasyondur; kiriş donatısı zarftan, kolon denetimi her kombinasyonun eş zamanlı $(N,M)$ çiftinden yapılır.
:::

## Alıştırma

Kombinasyonu el hesabıyla kurmayı pekiştir: deprem birleşiminde düşey deprem payını unutma, zarfta iki yönü de dene.

::: alistirma kombinasyon
{"zorluk": 2}
:::

::: alistirma kombinasyon
{"zorluk": 3}
:::
