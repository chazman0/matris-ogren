---
baslik: Bina analizi baştan sona: bir yapı analiz programı binayı nasıl çözer
bolum: yapi
ozet: Aks–kat sisteminden düğüm ve eleman üretimi, yerel eksenler (programlardaki yaygın 1-2-3 kuralı ve burada x′y′z′, işaret kuralları), rijit diyafram (efendi–köle, T dönüşümü, rijitlik merkezi); yük → durum → kombinasyon → zarf → tasarım zinciri ve D/C renk bantları; yapı analiz programı kullanıcılarının sık zorlandığı noktalar ve bu uygulamadaki karşılıkları; sonuç okuma, denge sağlaması ve sık hatalar (birim, diyafram, çatlamış rijitlik, periyot üst sınırı, zarfla kolon kontrolü).
sure: 80
---

## Neden?

Bir binayı ticari bir yapı analiz programında modellemek bir hafta, sonuçlara güvenmek ise çoğu zaman daha uzun sürer. Program her düğmeye bir sayı üretir; ama kolon yerel ekseni ters bakıyorsa, öz ağırlık iki kez sayılmışsa ya da diyafram yanlış atanmışsa bu sayılar gerçek binayı anlatmaz. Önceki derslerde zincirin halkalarını tek tek kurdun: yük akışı, durumlar, kombinasyonlar, deprem yükü, kesit tahkiki. Bu ders onları baştan sona tek bir akışta birleştirir ve her adımda "bir yapı analiz programı bunu nasıl yapar, burada nerede, nasıl doğrularım?" sorusunu yanıtlar.

::: sekil Baştan sona: model, çözüm, tasarım
<svg viewBox="0 0 440 250" width="100%" font-family="system-ui" font-size="11" fill="currentColor">
<rect x="6" y="10" width="132" height="54" rx="8" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="1.5"/>
<text x="72" y="30" text-anchor="middle" font-weight="700" fill="var(--sema-a,#3b82f6)">1 Model</text>
<text x="72" y="46" text-anchor="middle">aks, kat, kesit, malzeme</text>
<text x="72" y="58" text-anchor="middle">düğüm, eleman, yerel eksen</text>
<rect x="154" y="10" width="132" height="54" rx="8" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="1.5"/>
<text x="220" y="30" text-anchor="middle" font-weight="700" fill="var(--sema-a,#3b82f6)">2 Kısıtlar</text>
<text x="220" y="46" text-anchor="middle">mesnet, rijit diyafram</text>
<text x="220" y="58" text-anchor="middle">efendi düğüm (u_x, u_y, θ)</text>
<rect x="302" y="10" width="132" height="54" rx="8" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5"/>
<text x="368" y="30" text-anchor="middle" font-weight="700" fill="var(--sema-b,#f59e0b)">3 Yükler</text>
<text x="368" y="46" text-anchor="middle">G, Q, S, W, E desenleri</text>
<text x="368" y="58" text-anchor="middle">kütle G + nQ</text>
<rect x="302" y="98" width="132" height="54" rx="8" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5"/>
<text x="368" y="118" text-anchor="middle" font-weight="700" fill="var(--sema-b,#f59e0b)">4 Durumlar</text>
<text x="368" y="134" text-anchor="middle">K u = F, tek K</text>
<text x="368" y="146" text-anchor="middle">12 sağ taraf</text>
<rect x="154" y="98" width="132" height="54" rx="8" fill="var(--sema-c-bg,rgba(16,185,129,.13))" stroke="var(--sema-c,#10b981)" stroke-width="1.5"/>
<text x="220" y="118" text-anchor="middle" font-weight="700" fill="var(--sema-c,#10b981)">5 Kombinasyon, zarf</text>
<text x="220" y="134" text-anchor="middle">Σ γᵢ · sonuçᵢ</text>
<text x="220" y="146" text-anchor="middle">max, min, belirleyen</text>
<rect x="6" y="98" width="132" height="54" rx="8" fill="var(--sema-sil-bg,rgba(239,68,68,.11))" stroke="var(--sema-sil,#ef4444)" stroke-width="1.5"/>
<text x="72" y="118" text-anchor="middle" font-weight="700" fill="var(--sema-sil,#ef4444)">6 Tasarım</text>
<text x="72" y="134" text-anchor="middle">TS 500, ÇYTHYE</text>
<text x="72" y="146" text-anchor="middle">D/C renk bandı</text>
<path class="ok" pathLength="1" d="M138 37H152M286 37H300M368 64V96M302 125H288M154 125H140" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="147,32 153,37 147,42" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="295,32 301,37 295,42" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="363,91 368,97 373,91" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="293,120 287,125 293,130" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="145,120 139,125 145,130" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<rect x="40" y="180" width="360" height="56" rx="8" fill="none" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="4 3"/>
<text x="220" y="200" text-anchor="middle">her adımda denge: Σ yük = Σ tepki, Σ F_iE = V_tE</text>
<text x="220" y="216" text-anchor="middle">kesit küçült → yeniden çöz → D/C yeniden</text>
<text x="220" y="230" text-anchor="middle">(analiz kesiti = tasarım kesiti olana kadar)</text>
</svg>
:::

## Modelleme: akslardan düğüm ve elemana

Yaygın yapı analiz programlarında model ızgara (grid) çizgileriyle başlar; çubuklar ızgara parçalarına çizilir, düğümler çizimle kendiliğinden oluşur. Bu uygulamada bina bir sözlüktür: **akslar** (X'te A, B, C; Y'de 1, 2, 3), **katlar** (kotlar), kesitler ve elemanların aks adresleri. Motor her aks kesişimi ve her kotta bir düğüm, her kolon ve kiriş parçası için bir **uzay çerçeve elemanı** (12×12, Ders 19) üretir. Ders binasında 3×3 aks ve 4 kot $\Rightarrow$ $9\cdot4=\kutua{36}$ düğüm, $27$ kolon $+\ 36$ kiriş $=\kutub{63}$ eleman ve $36\cdot6=\kutuc{216}$ serbestlik.

### Aks tabanlı genel model

Aks–kat sözlüğü düzenli katlı binalara yeter; çapraz, makas, eğik çatı ya da kren yolu için daha genel bir model gerekir. Genel modelde (`surum: 3`) X, Y ve Z aksları adlandırılmış düzlemlerdir (Z aksları "±0.00", "Saçak", "Mahya" gibi; kat, Z aksının işaretidir) ve gerektiğinde açılı ya da silindirik ek aks sistemleri eklenir. Her düğüm bir aks kesişimi (`{"aks": ["B", "3"], "z": "Saçak"}`) ya da bir çubuğun bölme / kesişim noktasıdır; elemanlar `cubuklar` (kolon, kiriş, çapraz, makas, aşık, kren…), `paneller` (döşeme, çatı, cephe) ve `mesnetler` listelerinde durur. Düğüm konumları her çözümde akslardan yeniden hesaplandığı için aks taşınınca bağlı bütün düğüm ve elemanlar birlikte taşınır.

Bina sayfasındaki akış yaygın programlardakine benzer: Hızlı aks sihirbazıyla ızgara kurulur, Düzlem seçiciyle bir plan ya da cephe düzlemi seçilir, çubuk ve paneller kesişimden kesişime çizilir, üreteçler (makas, beşik çerçeve, aşık, kren yolu) tekrarlayan geometriyi üretir. Aks–kat modeline çubuk, çapraz, panel ya da mesnet eklenince model onayla genel modele çevrilir; aynı binanın iki yoldan çözümü aynı tepkileri ve iç kuvvetleri verir. Genel modelde mütemadi ve radye temel yoktur (en alt Z aksındaki kesişimler tekil temel mesnetidir) ve model en çok 2000 serbestlik olabilir. Hazır örnekler: [çaprazlı çerçeve](#bina/sablon/celik-cbf-3kat) ve [sanayi yapısı](#bina/sablon/celik-sanayi-4hol).

### Yerel eksenler ve işaretler

Her elemanın iç kuvvetleri kendi **yerel ekseninde** verilir. Yapı analiz programlarında yaygın kural şudur: 1 ekseni I ucundan J ucuna gider; yatay elemanda 2 yukarı, 3 $=1\times2$ yataydır. Düşey elemanda 2 ekseni $+X$, 3 ekseni $+Y$ alınır. Bu uygulamanın motorunda (Ders 19) $x'$ $i\to j$ yönünde, $y'$ elemanı içeren düşey düzlemde yukarı, $z'=x'\times y'$; düşey elemanda $z'$ motorun yatay ekseni seçilir ve yukarı giden kolonda $y'=-X$ çıkar.

| Eleman | Program kuralı 1 / 2 / 3 | Burada $x'$ / $y'$ / $z'$ (bina ekseninde) | Sonuç |
|---|---|---|---|
| X doğrultusunda kiriş | $+X$ / $+Z$ / $-Y$ | $+X$ / $+Z$ / $-Y$ | aynı: $M_3\leftrightarrow M_{z'}$ |
| yukarı giden kolon | $+Z$ / $+X$ / $+Y$ | $+Z$ / $\ksil{-X}$ / $\ksil{-Y}$ | yanal eksenler ters işaretli |

İşaretler (programlardaki yaygın iç kuvvet kuralı): pozitif $P$ **çekmedir**; pozitif $M_3$, $+2$ yüzünde basınç yapar, yani yatay kirişte **alt lif çekme** demektir. Bu motorun kiriş momenti aynı kuralı izler (alt lif çekme +) ve eksenel kuvvette basınç negatiftir; kesit tahkikinde (TS 500 $N_d$) ise basınç pozitif alınır. Kolonda tahkik momentleri bina eksenlerinde verilir: $M_x$ bina $X$ ekseni etrafında, $M_y$ $Y$ ekseni etrafında.

::: uyari Çizim yönü ve kolon yönü
1-2-3 kuralını izleyen bir programda kiriş B'den A'ya çizilirse 1 ekseni ters döner; $M_3$ işareti değişmez ama $V_2$ işareti ve "sol, sağ uç" etiketleri yer değiştirir. Kolonun güçlü ekseni yerel 2'ye bakar ve gerekirse 90° döndürülür. Bu uygulamada kiriş adresi `bas` → `son` sırasıyla, kolonun güçlü ekseni `yon` (x ya da y) alanıyla verilir.
:::

## Rijit diyafram: efendi ve köle düğümler

Betonarme döşeme kendi düzleminde çok rijittir. **Rijit diyafram** varsayımında kattaki bütün düğümler (köle) bir **efendi düğümün** (master) üç serbestliğine bağlanır: $u_x$, $u_y$ ve düşey eksen etrafında dönme $\theta$. Yapı analiz programları diyafram kısıtı ("diaphragm constraint") ile bu düğümü kütle merkezinde kendiliğinden kurar; bu motor da kütle merkezine efendi düğüm koyar. Köle düğüm $i$'nin ötelemesi efendi düğümünkinden **dönüşüm matrisi** $\mathbf T_i$ ile bulunur:

$$
\begin{bmatrix}u_{x,i}\\u_{y,i}\end{bmatrix}=
\underbrace{\begin{bmatrix}1&0&\ksil{-(y_i-y_m)}\\0&1&\kb{x_i-x_m}\end{bmatrix}}_{\mathbf T_i}
\begin{bmatrix}u_x\\u_y\\\theta\end{bmatrix},\qquad
\kutua{\mathbf K_{kat}=\sum_i k_i\,\mathbf T_i^{T}\mathbf T_i}\quad(3\times3)
$$

$k_i$ kolonun yanal rijitliğidir (iki ucu ankastre kolonda $12EI/h^3$). Kat kuvveti **rijitlik merkezinden** ($x_r=\sum k_ix_i/\sum k_i$) geçmiyorsa kat döner; rijitlik merkezinden uzak kolonların kesmesi artar. TBDY'nin ±%5 dışmerkezliği (Ders 23) bu dönmeyi bilerek üretir. Aşağıda dört kolonlu bir katta rijitlikleri ve kuvvetin yerini değiştir.

::: etkilesim rijit-diyafram
{"k": [2, 1, 2, 1], "F": 60, "e": 0}
:::

## Yükten tasarıma: zincir ve D/C bantları

Yükler **yük desenleri** (G, Q, S, W±X/Y, E) olarak tanımlanır; her desen bir **doğrusal statik durum** olarak aynı $K$ ile çözülür; **kombinasyonlar** sonuçların katsayılı toplamıdır; **zarf** her kesitte en büyük ve en küçük değerdir (Ders 22). Deprem durumları TBDY eşdeğer deprem yüküyle kurulur (Ders 23), kesitler TS 500 ya da ÇYTHYE ile tahkik edilir (Ders 24 ve 25). Aşağıdaki çizim zincirin ortasını, durum diyagramlarından zarfa geçişi gösterir.

::: etkilesim kombinasyon-zarfi
{"gG": 1.24, "gQ": 1, "gE": 1, "SDS": 1.2, "x": 5}
:::

Tasarımdan sonra yapı analiz programları çubukları D/C oranına göre genellikle beş renk bandına boyar; bantların eşikleri kullanıcı tanımlıdır ve kırmızı tipik olarak D/C > 1'dir. Bu uygulamanın tasarım özeti elemanları dört banda sayar: $<0.7$ (bol), $0.7$–$0.9$, $0.9$–$1.0$ (sınırda) ve $>1.0$ (yetersiz). D/C'yi okurken **belirleyen kontrol** ve **belirleyen kombinasyon** birlikte okunur: aynı 0.95, kirişte "donatıyı tam tasarladım", kolonda "sınırdayım" anlamına gelebilir.

## Yapı analiz programlarında sık zorlanılan noktalar ve buradaki karşılığı

| Programda zorluk | Belirtisi | Bu uygulamada |
|---|---|---|
| birim seti model boyunca değişir (kN·m, N·mm, kgf·cm) | 1000 kat büyük ya da küçük sonuçlar | birimler sabit: kN, m, kN/m²; kesit 30 cm yerine 0.30 yazılmazsa öğretici hata |
| grid ve snap, çakışık düğüm | eleman bağlanmaz, kararsızlık uyarısı | düğümler aks kesişiminden ya da bölme / kesişim noktasından üretilir, motor 1 mm içindeki konumları tek düğümde birleştirir; modeldeki çakışık düğüm kayıtlarını *Düğümleri birleştir* (Shift+J) temizler, aynı iki düğümü bağlayan çubuk uyarılır |
| yerel eksen ve çizim yönü | ters diyagram, yanlış güçlü eksen | kural sabit; kolonda `yon` alanı |
| yerçekimi yönü / global Z işareti | yük yukarı bakar | yük durumları ve döşeme yükleri kartlardan; korunum tablosu yönü doğrular |
| öz ağırlık iki kez (öz ağırlık çarpanı + ayrıca tanımlı kütle ya da yük) | taban tepkisi fazla | öz ağırlık yalnız G'de; $\sum$ yük $=\sum$ tepki satırı |
| kütle kaynağı $G+nQ$ | periyot ve $V_t$ yanlış | TBDY Tablo 4.3 ile $w_i=w_G+n\,w_Q$ kendiliğinden |
| tasarım kombinasyonlarını elle yazmak | eksik işaret ya da yön | 84 kombinasyon şablon satırlarından açılır |
| $K$, $L_b$, $C_b$ varsayılanları | gizli varsayım | varsayımlar `veri["tasarim"]["varsayimlar"]` içinde yazılı |
| mesnet unutmak, yüzen eleman | kararsızlık ("instability") uyarısı | yüzen döşeme, kolonsuz kat gibi öğretici hatalar |

## Sonuç okuma ve denge sağlaması

Her çözümden sonra üç sağlama yapılır. **Düşey denge:** $G$ durumunda temel tepkilerinin toplamı toplam sabit yüke eşittir (programlarda taban tepkileri tablosu). **Yatay denge:** deprem durumunda tepkilerin yatay toplamı $-V_{tE}$'dir. **Kombinasyon tutarlılığı:** bir kombinasyonun tepkisi durum tepkilerinin aynı katsayılı toplamıdır. Bunlardan biri tutmuyorsa sonuçlara bakmadan önce model düzeltilir.

::: hata Birim karışıklığı
Kesiti mm, yükü kN/m, malzemeyi MPa girip programın birim setini kN·m bırakmak $E$'yi bin kat küçük yapar; ötelemeler bin kat büyür ama iç kuvvetler (statikçe belirli kısımlar) neredeyse doğru görünür, hata gözden kaçar. Bir tek birim seti seç; ötelemeyi bir el hesabıyla (örneğin $\delta=PL^3/3EI$) kabaca sına.
:::

::: hata Diyaframı yanlış atamak
Diyafram yalnız aynı düzlemdeki düğümlere atanır; çatı eğimli ya da kat yarım kotluysa ayrı diyafram gerekir. Bütün binayı tek diyaframa bağlamak katları birbirine kilitler. Tersine, döşemesiz çelik çatıda (çaprazsız) rijit diyafram varsaymak yükü gerçekte taşıyamayacak çerçevelere dağıtır.
:::

::: hata Çatlamış rijitliği ve periyot üst sınırını unutmak
Deprem hesabında TBDY Tablo 4.2 etkin rijitlikleri kullanılır (kolon $0.70EI$, kiriş $0.35EI$; md. 4.5.8). Brüt kesit periyodu kısa, ötelemeyi küçük gösterir. Bu uygulama betonarme binada deprem açıkken çatlamış kesiti varsayılan alır ve yalnız deprem birleşimlerine uygular (md. 4.5.8.3: ikinci bir $K$); kapatılırsa "TBDY 4.5.8.1’e aykırı" uyarısı verir. Ticari programlarda kesit özelliği çarpanları ("property modifiers") çoğu zaman bütün durumlara uygulanır; düşey yük tasarımı için ayrı bir model gerekir. Rayleigh periyodu da $1.4\,T_{pA}$'yı geçemez (md. 4.7.3.2): çok yumuşak bir model deprem yükünü sınırsız azaltamaz.
:::

::: hata Kolonu zarfla denetlemek
Zarfın $N_{max}$'ı ile $M_{max}$'ı farklı kombinasyonlardandır. Yapı analiz programları kolon tasarımında her kombinasyonun $(P,M_2,M_3)$ noktasını ayrı denetler; zarf tablosundan elle yapılan kontrol az basınçlı $0.9G\pm E$ noktasını kaçırır (Ders 24, son örnek).
:::

## Çözümlü örnekler

Örnekler `betonarme-3kat-3x3` ders binasını kullanır: akslar 0–5–10 m ve 0–4–8 m, üç kat 3.2 m, 45×45 kolon, 25×55 kiriş, C30, büro yükü, deprem (çatlamış kesit, DD-3 ile $\lambda=0.4$), kar ve rüzgâr açık, rijit diyafram; dış kirişlerde duvar, çatıda 1 m parapet. Aynı binayı [Bina sayfasında aç](#bina/sablon/betonarme-3kat-3x3).

::: ornek Tam çözüm ve iki denge sağlaması
Ders binasını çöz. Düğüm, eleman ve serbestlik sayısı, durum ve kombinasyon sayısı nedir? $G$ durumunda düşey tepki toplamı ve EX+ durumunda yatay tepki toplamı neye eşit olmalı?
--- ipucu
Rijit diyafram her kata bir efendi düğüm ekler. Toplam sabit yük: döşeme 1260, duvar 612.36 (1. ve 2. katta tam duvar, çatıda parapet), kiriş 405 (döşeme içindeki kısım düşülmüş $b(h-t)$), kolon 437.4 kN.
--- cevap
$$
\begin{aligned}
\text{düğüm}&=36+\underbrace{3}_{\text{efendi}}=\ka{39},\qquad \text{eleman}=27+36=\ka{63},\qquad \text{durum}=12,\quad \text{kombinasyon}=84\\
\sum R_Z(G)&=1260+612.36+405+437.4=\kutuc{2714.76}\ \text{kN}=\sum G\ \checkmark\\
\sum R_X(EX+)&=\kutuc{-288.81}\ \text{kN}=-V_{tE}\ \checkmark\quad(\text{tepki kuvvete ters})
\end{aligned}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
r.veri["ozet"]["dugum"] == 39 and r.veri["ozet"]["eleman"] == 63 and r.veri["ozet"]["sd_sayisi"] == 216 and r.veri["ozet"]["durum_sayisi"] == 12 and r.veri["ozet"]["kombinasyon_sayisi"] == 84 and abs(sum(t["FZ"] for t in r.veri["durumlar"]["G"]["tepkiler"]) - 2714.76) < 1e-3 and abs(sum(t["FX"] for t in r.veri["durumlar"]["EX+"]["tepkiler"]) + r.veri["deprem"]["VtE"]) < 1e-2
--- yorum
`veri["akis"]["korunum"]["G"]` aynı denetimi kalem kalem yazar: döşeme + duvar + öz ağırlık = kolon tabanı = temel tepkisi. Betonarme binada deprem durumları ayrı bir çatlamış kesitli $K$ ile çözülür (TBDY 4.5.8); $G$ ve $Q$ burada brüt $K$'nin sonucudur. Yapı analiz programlarında karşılığı taban tepkileri tablosudur; ilk bakılacak yer orasıdır.
:::

::: ornek Rijit diyafram elle: dört kolonlu kat
6×4 m planlı bir katın köşelerinde dört kolon var: sol kolonlar (S1, S3; $x=0$) $k=2$, sağ kolonlar (S2, S4; $x=6$) $k=1$ kN/mm. Efendi düğüm kütle merkezinde (3; 2); $F_y=60$ kN kütle merkezine etkiyor. $\mathbf K$'yı kur, $u_y$ ve $\theta$'yı bul, kolon kesmelerini hesapla.
--- ipucu
$\sum k=6$; $\sum k(x_i-x_m)=2(-3)+1(3)+2(-3)+1(3)=-6$; $\sum k[(x_i-x_m)^2+(y_i-y_m)^2]=6\cdot13=78$.
--- cevap
$$
\underbrace{\begin{bmatrix}6&0&0\\0&\kb{6}&\ksil{-6}\\0&\ksil{-6}&78\end{bmatrix}}_{\mathbf K}\begin{bmatrix}u_x\\u_y\\\theta\end{bmatrix}=\begin{bmatrix}0\\60\\0\end{bmatrix}
\ \Rightarrow\ \kutua{u_y=\tfrac{65}{6}=10.83\ \text{mm}},\quad \kutub{\theta=\tfrac56\ \text{mm/m}}
$$
$$
x_r=\frac{2\cdot0+1\cdot6}{3}=\ksil{2\ \text{m}},\qquad
V_{y,sol}=2\Big(\tfrac{65}{6}-3\cdot\tfrac56\Big)=\kc{16.67},\qquad V_{y,sağ}=1\Big(\tfrac{65}{6}+3\cdot\tfrac56\Big)=\kc{13.33}\ \text{kN}
$$
$2\cdot16.67+2\cdot13.33=60$ kN $\checkmark$.
--- kod
mo.coz("6 0 0; 0 6 -6; 0 -6 78", "0; 60; 0")
--- kontrol
r.deger == sp.Matrix([[0], [sp.Rational(65, 6)], [sp.Rational(5, 6)]])
--- yorum
Rijitlik orantısıyla dağıtılsaydı sol kolonlar 20, sağ kolonlar 10 kN alırdı. Kuvvet rijitlik merkezinin 1 m sağından geçtiği için kat saat yönünün tersine döndü ve yükün bir kısmını sağ kolonlara itti. $\mathbf K$'daki $-6$ terimi öteleme ile dönmenin bağlaşımıdır; rijitlik merkezi efendi düğümle çakışsaydı sıfır olurdu. Yukarıdaki etkileşimde "Ders örneği" düğmesi aynı katı çizer.
:::

::: ornek Diyaframlı ve diyaframsız çözüm
Ders binasını bir de `deprem.diyafram = "esnek"` ile çöz. Düğüm sayısı, 1. katta X depreminde burulma düzensizliği katsayısı $\eta_{bx}$ ve tepe kat ötelemesi nasıl değişir?
--- ipucu
Esnek seçimde efendi düğüm yoktur; döşemenin düzlem içi rijitliği modelde hiç yoktur, kat düğümlerini yalnız kirişlerin eksenel rijitliği bağlar.
--- cevap
$$
\begin{aligned}
\text{düğüm}&:\ \ka{39}\ \to\ \kb{36}\\
\eta_{bx,1}&:\ \ka{1.049}\ \to\ \kb{1.110},\qquad u_{x,3}:\ \ka{10.04}\ \to\ \kb{10.16}\ \text{mm}\\
\text{D/C}_{max}&:\ 0.9979\ \to\ 1.0000
\end{aligned}
$$
--- kod
b = yapi.bina_sablon("betonarme-3kat-3x3")
b["deprem"]["diyafram"] = "esnek"
[yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3")), yapi.bina_coz(b)]
--- kontrol
r[0].veri["ozet"]["dugum"] == 39 and r[-1].veri["ozet"]["dugum"] == 36 and r[-1].veri["ozet"]["diyafram"] == "esnek" and abs(r[0].veri["deprem"]["katlar"][0]["eta_bx"] - 1.0491) < 1e-3 and abs(r[-1].veri["deprem"]["katlar"][0]["eta_bx"] - 1.1097) < 1e-3 and r[-1].veri["deprem"]["katlar"][2]["d_x"] > r[0].veri["deprem"]["katlar"][2]["d_x"]
--- yorum
Bu düzenli binada fark küçüktür; ama esnek modelde ±%5 dışmerkezlik momenti kat düğümlerine kuvvet çifti olarak dağıtılır ve kenar çerçeveler daha çok zorlanır. Kirişsiz döşemeli, büyük boşluklu ya da çok uzun planlı binalarda fark büyür; orada diyafram rijitliği ayrıca değerlendirilir.
:::

::: ornek Kombinasyon tepkisi: süperpozisyon sağlaması
$1.4G+1.6Q$ kombinasyonunda temel tepkilerinin düşey toplamını ve köşe kolon A1'in temel tepkisini bul. Durum toplamlarıyla karşılaştır ($\sum G=2714.76$, $\sum Q=480$ kN).
--- ipucu
Kombinasyon yeniden çözülmez: her tepki aynı katsayılarla toplanır.
--- cevap
$$
\sum R_Z=1.4\cdot\ka{2714.76}+1.6\cdot\kb{480}=3800.664+768=\kutuc{4568.664}\ \text{kN},\qquad R_{Z,A1}=\kc{370.06}\ \text{kN}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
abs(sum(t["FZ"] for t in yapi.kombinasyon_kisa(r.ic, "1.4G+1.6Q")["tepkiler"]) - 4568.664) < 1e-2 and abs(next(t for t in yapi.kombinasyon_kisa(r.ic, "1.4G+1.6Q")["tepkiler"] if t["dugum"] == 1)["FZ"] - 370.064) < 1e-2
--- yorum
A1'in tepkisi Ders 22'deki kolon eksenel kuvvetiyle ($-370.1$ kN, basınç) aynıdır: temel düğümünde kolonun taşıdığı her şey zemine iner. Yapı analiz programlarında düğüm tepkileri tablosunda kombinasyon seçilerek aynı denetim yapılır.
:::

::: ornek D/C okuma: dağılım, kritik eleman, belirleyen
Ders binasının tasarım özetinden D/C dağılımını, en kritik üç elemanı ve kolonların en büyük D/C'sini oku. Kirişlerin çoğu neden 0.9–1.0 bandında?
--- ipucu
`veri["tasarim"]["dc_dagilimi"]`, `kritik_elemanlar`; kolonlar `tur == "kolon"`.
--- cevap
$$
\begin{aligned}
<0.7:\ \kc{31},\quad 0.7\text{–}0.9:\ 2,\quad 0.9\text{–}1.0:\ \kb{30},\quad >1.0:\ \ksil{0}\\
\text{kritik: K-A1}&\rightarrow\text{A2/k2, K-A2}\rightarrow\text{A3/k2, K-C1}\rightarrow\text{C2/k2 (hepsi 0.9979, simetri)}\\
\text{kolon}_{max}&:\ \text{S-A1/k1},\ \kutua{0.685},\ \texttt{0.9G-0.3EX-+EY--0.3EZ}
\end{aligned}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
r.veri["tasarim"]["dc_dagilimi"] == {"<0.7": 31, "0.7-0.9": 2, "0.9-1.0": 30, ">1.0": 0} and [k["no"] for k in r.veri["tasarim"]["kritik_elemanlar"][:3]] == [19, 20, 23] and abs(max(e["dc"] for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kolon") - 0.68522) < 1e-4
--- yorum
Kiriş donatısı tasarlandığı için D/C $\approx1$ "yetersiz" değil "ekonomik" demektir; kirişte asıl çıktı önerilen çubuklardır. Kolonda donatı varsayılmıştır ($\rho=0.01$), D/C gerçek bir kapasite oranıdır. Ticari programlarda da betonarme çerçeve tasarımı kirişte donatı alanı, kolonda (donatı verilmişse) kapasite oranı raporlar.
:::

::: ornek Kesiti küçült, yeniden çöz
Bütün kolonları 35×35'e küçült ve yeniden çöz. Kaç eleman D/C > 1 olur, en kritik eleman hangisi ve hangi kombinasyonda? Kolon donatısı ne olmalı?
--- ipucu
Kolon $\rho=0.01$ varsayılır; motor 0.01 → 0.04 aralığını 0.0025 adımla tarar.
--- cevap
$$
\begin{aligned}
>1.0&:\ \kutusil{10}\ \text{eleman},\qquad \text{S-A1/k1}:\ \text{D/C}=\ksil{1.143}\ \ (\texttt{0.9G-0.3EX-+EY--0.3EZ})\\
N_d&=86.5\ \text{kN}<0.1f_{ck}A_c=367.5\ \Rightarrow\ \frac{M_x}{M_{rx}}+\frac{M_y}{M_{ry}}=1.143\ (\text{doğrusal toplam})\\
\rho_{gerekli}&=\kutuc{0.0125}\ \Rightarrow\ A_s=15.31\ \text{cm}^2\quad(\text{8 çubuk: } 8\phi16=16.08)
\end{aligned}
$$
--- kod
b = yapi.bina_sablon("betonarme-3kat-3x3")
b["kesitler"]["S45x45"].update({"b": 0.35, "h": 0.35})
r = yapi.bina_coz(b)
r
--- kontrol
r.veri["tasarim"]["dc_dagilimi"][">1.0"] == 10 and r.veri["tasarim"]["kritik_elemanlar"][0]["adres"] == "S-A1/k1" and abs(r.veri["tasarim"]["en_buyuk_dc"] - 1.1426) < 1e-3 and next(e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kolon" and e["no"] == 1)["ozet"]["rho_gerekli"] == 0.0125 and r.veri["tasarim"]["kritik_elemanlar"][0]["kombinasyon"] == "0.9G-0.3EX-+EY--0.3EZ"
--- yorum
Kolonlar küçülünce bina yumuşar ve kütle azalır ($V_{tE}$ 289'dan 274 kN'a iner) ama kolon kapasitesi daha hızlı düşer; göreli kat ötelemesi yine sınırın altındadır ($\lambda\delta/h=0.0065$). Belirleyen yine az basınçlı deprem birleşimidir. Yapı analiz programlarında da bu döngü "analiz kesiti = tasarım kesiti olana kadar" yinelenir; kesit değişince rijitlik ve deprem yükü değiştiği için yeniden analiz şarttır. Bu kesit TBDY'nin 300 mm alt sınırını sağlar ama süneklik ve birleşim bölgesi için genellikle yetersiz kalır.
:::

::: ornek Yerel eksen eşlemesi
1-2-3 kuralını izleyen bir programda B'den A'ya çizilmiş X doğrultusundaki bir kirişte ve aşağıdan yukarı çizilmiş kolon A1'de 1-2-3 eksenleri nedir? Bu uygulamadaki $x'y'z'$ ile karşılaştır ve kolonun $M_2$, $M_3$ momentlerinin bina eksenlerindeki karşılığını yaz.
--- ipucu
Kirişte 2 her zaman yukarı; düşey elemanda 2 $=+X$. Burada düşey elemanda $y'=-X$.
--- cevap
$$
\begin{aligned}
\text{kiriş B}\to\text{A}&:\ \ka{1=-X},\ \kb{2=+Z},\ \kc{3=1\times2=+Y}\quad(\text{A}\to\text{B çizilseydi } 3=-Y)\\
\text{kolon}&:\ \ka{1=+Z},\ \kb{2=+X},\ \kc{3=+Y};\qquad x'=+Z,\ \ksil{y'=-X},\ \ksil{z'=-Y}\\
M_2\ (2=X\ \text{etrafında})&\leftrightarrow M_x,\qquad M_3\ (3=Y\ \text{etrafında})\leftrightarrow M_y
\end{aligned}
$$
--- yorum
Ters çizilen kirişte $M_3$ işareti (alt lif çekme +) değişmez, yalnız $V_2$ ve uç adları değişir. Kolonda iki kuralın yanal eksenleri zıt yönlüdür; değerleri karşılaştırırken mutlak değer ve hangi yüzün basınçta olduğu esas alınır. Tasarımda moment işareti değil büyüklüğü ve eşlik eden $N$ önemlidir.
:::

::: muhendislik Yapı analiz programından bu uygulamaya, oradan sahaya
Yaygın yapı analiz programlarının modelleme sırası (birim → ızgara → malzeme ve kesit → çizim → atama → desen, durum, kombinasyon → analiz → sonuç → tasarım) bu uygulamada bina kartlarının sırasıdır. Fark, her adımın arkasındaki matrisin görünür olmasıdır: eleman matrisi (Ders 17, 19), birleştirme (Ders 14), diyafram dönüşümü (bu ders), tek $K$ ile çok sağ taraf (Ders 22). Büyük projede ticari yapı analiz programları kullanılır; bu uygulamanın amacı onların çıktısını **sınayabilecek** el hesabı ve sezgiyi kazandırmaktır.

Mevcut ve tarihi yapılarda model güncellemesi zinciri tamamlar: ortam titreşimiyle (OMA) ölçülen periyotlar ve mod şekilleri, diyafram varsayımının ve rijitliklerin doğru olup olmadığını gösterir. Yığma köprüde dolgu ve kemer rijitliği, binada dolgu duvarların katkısı ve çatlamış kesit oranı bu karşılaştırmayla kalibre edilir.
:::

::: ozet Özet
- Model: aks × kot düğümleri, her parça için 12×12 uzay çerçeve elemanı; ders binasında 36 (+3 efendi) düğüm, 63 eleman, 216 SD.
- Yerel eksen: programlarda 1 (I→J), kirişte 2 yukarı; kolonda 2 = $+X$, 3 = $+Y$. Burada $x'$ (i→j), $y'$ düşey düzlemde yukarı, kolonda $y'=-X$, $z'=-Y$. $P>0$ çekme, kirişte $M>0$ alt lif çekme; tahkikte $N_d>0$ basınç.
- Rijit diyafram: $u_{x,i}=u_x-\theta(y_i-y_m)$, $u_{y,i}=u_y+\theta(x_i-x_m)$; $\mathbf K=\sum k_i\mathbf T_i^T\mathbf T_i$; kuvvet rijitlik merkezinden geçmiyorsa kat döner.
- Zincir: desen → durum (tek $K$) → kombinasyon ($\sum\gamma_i$·sonuç) → zarf → tasarım; D/C belirleyen kontrol ve kombinasyonla okunur, bantlar $<0.7$, $0.7$–$0.9$, $0.9$–$1.0$, $>1.0$.
- Sağlamalar: $\sum R_Z(G)=\sum G$, $\sum R_X(E)=-V_{tE}$, kombinasyon tepkisi = katsayılı toplam. Sık hatalar: birim, diyafram, çatlamış rijitlik, $T_p\le1.4T_{pA}$, zarfla kolon kontrolü.
:::

## Alıştırma

Zincirin ortasını el hesabıyla kur: kombinasyonları yaz, zarfın iki ucunu bul.

::: alistirma kombinasyon
{"zorluk": 3}
:::
