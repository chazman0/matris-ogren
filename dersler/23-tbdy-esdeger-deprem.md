---
baslik: TBDY 2018 eşdeğer deprem yükü
bolum: yapi
ozet: Deprem yer hareketi düzeyleri, AFAD haritası, zemin sınıfı ve F_S, F_1 ara değeri, S_DS, S_D1 ve S_ae(T); BKS, DTS, BYS, R, D ve R_a(T); kat kütleleri, T_pA ve Rayleigh periyodu, V_tE ve alt sınırı, ΔF_NE ve F_iE dağılımı; rijit diyafram, ±%5 dışmerkezlik ve η_bi; göreli kat ötelemesi, θ_II, çatlamış rijitlik ve yöntemin uygulanabilirliği.
sure: 80
---

## Neden?

Deprem binaya bir yük koymaz; zemini sallar ve bina kütlesinin eylemsizliği iç kuvvet üretir. Dinamik hesabın en basit güvenli karşılığı, birinci modu ters üçgen kabul edip depremi kat düzeylerine etkiyen **eşdeğer statik kuvvetlere** çevirmektir: **eşdeğer deprem yükü yöntemi** (EDYY). Türkiye'de bu yöntem TBDY 2018 md. 4.7'de tanımlıdır ve alçak, düzenli binaların çoğunda kullanılır. Bu derste bir binanın koordinatından başlayıp kat kuvvetlerine, oradan göreli kat ötelemesi denetimine kadar zinciri el hesabıyla ve `yapi` motoruyla kuracaksın.

::: sekil Eşdeğer deprem yükü zinciri
<svg viewBox="0 0 440 236" width="100%" font-family="system-ui" font-size="11" fill="currentColor">
<rect x="6" y="10" width="128" height="44" rx="8" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="1.5"/>
<text x="70" y="28" text-anchor="middle" font-weight="700" fill="var(--sema-a,#3b82f6)">AFAD haritası</text>
<text x="70" y="44" text-anchor="middle">S_S, S_1 (DD-2)</text>
<rect x="156" y="10" width="128" height="44" rx="8" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="1.5"/>
<text x="220" y="28" text-anchor="middle" font-weight="700" fill="var(--sema-a,#3b82f6)">zemin sınıfı</text>
<text x="220" y="44" text-anchor="middle">F_S, F_1 → S_DS, S_D1</text>
<rect x="306" y="10" width="128" height="44" rx="8" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="1.5"/>
<text x="370" y="28" text-anchor="middle" font-weight="700" fill="var(--sema-a,#3b82f6)">spektrum</text>
<text x="370" y="44" text-anchor="middle">S_ae(T): T_A, T_B, T_L</text>
<rect x="6" y="92" width="128" height="44" rx="8" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5"/>
<text x="70" y="110" text-anchor="middle" font-weight="700" fill="var(--sema-b,#f59e0b)">bina</text>
<text x="70" y="126" text-anchor="middle">BKS→I, DTS, BYS, R, D</text>
<rect x="156" y="92" width="128" height="44" rx="8" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5"/>
<text x="220" y="110" text-anchor="middle" font-weight="700" fill="var(--sema-b,#f59e0b)">kütle ve periyot</text>
<text x="220" y="126" text-anchor="middle">m_i, T_pA, Rayleigh T_p</text>
<rect x="306" y="92" width="128" height="44" rx="8" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5"/>
<text x="370" y="110" text-anchor="middle" font-weight="700" fill="var(--sema-b,#f59e0b)">taban kesme</text>
<text x="370" y="126" text-anchor="middle">V_tE = m_t S_aR g</text>
<rect x="6" y="174" width="128" height="44" rx="8" fill="var(--sema-c-bg,rgba(16,185,129,.13))" stroke="var(--sema-c,#10b981)" stroke-width="1.5"/>
<text x="70" y="192" text-anchor="middle" font-weight="700" fill="var(--sema-c,#10b981)">kat kuvvetleri</text>
<text x="70" y="208" text-anchor="middle">ΔF_NE, F_iE (ters üçgen)</text>
<rect x="156" y="174" width="128" height="44" rx="8" fill="var(--sema-c-bg,rgba(16,185,129,.13))" stroke="var(--sema-c,#10b981)" stroke-width="1.5"/>
<text x="220" y="192" text-anchor="middle" font-weight="700" fill="var(--sema-c,#10b981)">rijit diyafram</text>
<text x="220" y="208" text-anchor="middle">±%5 e, η_bi, D_bi</text>
<rect x="306" y="174" width="128" height="44" rx="8" fill="var(--sema-sil-bg,rgba(239,68,68,.11))" stroke="var(--sema-sil,#ef4444)" stroke-width="1.5"/>
<text x="370" y="192" text-anchor="middle" font-weight="700" fill="var(--sema-sil,#ef4444)">denetimler</text>
<text x="370" y="208" text-anchor="middle">λδ/h ≤ 0.008κ, θ_II</text>
<path class="ok" pathLength="1" d="M134 32H154M284 32H304M370 54V90M306 114H286M156 114H136M70 136V172M134 196H154M284 196H304" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="149,27 155,32 149,37" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="299,27 305,32 299,37" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="365,85 370,91 375,85" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="291,109 285,114 291,119" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="141,109 135,114 141,119" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="65,167 70,173 75,167" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="149,191 155,196 149,201" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
<polyline class="ok-uc" points="299,191 305,196 299,201" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.8" fill="none"/>
</svg>
:::

## Deprem yer hareketi ve harita

::: tanim Deprem yer hareketi düzeyi
TBDY 2018 md. 2.2 dört düzey tanımlar. Tasarımın esası **DD-2**'dir: 50 yılda aşılma olasılığı %10, tekrarlanma periyodu 475 yıl. Öteki düzeyler performans hedefleri ve göreli kat ötelemesi için kullanılır.
:::

| Düzey | 50 yılda aşılma | Tekrarlanma | Kullanım |
|---|---|---|---|
| DD-1 | %2 | 2475 yıl | en büyük deprem, ileri performans |
| DD-2 | %10 | 475 yıl | standart tasarım depremi |
| DD-3 | %50 | 72 yıl | sık deprem; öteleme sınırında $\lambda$ |
| DD-4 | %68 (30 yılda %50) | 43 yıl | servis depremi |

**Harita spektral ivme katsayıları** $S_S$ (kısa periyot) ve $S_1$ (1 s), $V_{S30}=760$ m/s referans zemini ve %5 sönüm için boyutsuzdur (g cinsinden). Yönetmelikte sayı tablosu yoktur: değerler koordinatla AFAD Türkiye Deprem Tehlike Haritası'ndan (tdth.afad.gov.tr) her düzey için ayrı okunur (md. 2.3.2.1).

## Zemin sınıfı ve tasarım spektrumu

Yerel zemin sınıfı (Tablo 16.1) üst 30 m'nin kayma dalgası hızından okunur: ZA ($V_{S30}>1500$ m/s), ZB (760–1500), ZC (360–760), ZD (180–360), ZE (< 180); ZF sahaya özel analiz ister. Zemin, haritanın kayadaki ivmesini **yerel zemin etki katsayılarıyla** büyütür (Tablo 2.1 ve 2.2):

| Zemin | $F_S$: $S_S\le0.25$ | 0.50 | 0.75 | 1.00 | 1.25 | $\ge1.50$ | $F_1$: $S_1\le0.1$ | 0.2 | 0.3 | 0.4 | 0.5 | $\ge0.6$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZA | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |
| ZB | 0.9 | 0.9 | 0.9 | 0.9 | 0.9 | 0.9 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |
| ZC | 1.3 | 1.3 | 1.2 | 1.2 | 1.2 | 1.2 | 1.5 | 1.5 | 1.5 | 1.5 | 1.5 | 1.4 |
| ZD | 1.6 | 1.4 | 1.2 | 1.1 | 1.0 | 1.0 | 2.4 | 2.2 | 2.0 | 1.9 | 1.8 | 1.7 |
| ZE | 2.4 | 1.7 | 1.3 | 1.1 | 0.9 | 0.8 | 4.2 | 3.3 | 2.8 | 2.4 | 2.2 | 2.0 |

Ara değerler için doğrusal enterpolasyon yapılır (md. 2.3.3.1); uç sütunların dışında değer sabittir. Sonra Denk. (2.1) ve (2.3):

$$
\kutua{S_{DS}=S_S\,F_S},\qquad \kutua{S_{D1}=S_1\,F_1},\qquad T_A=0.2\,\frac{S_{D1}}{S_{DS}},\qquad T_B=\frac{S_{D1}}{S_{DS}},\qquad T_L=6\ \text{s}
$$

**Yatay elastik tasarım spektrumu** (Denk. 2.2) dört koldan oluşur:

$$
\ka{S_{ae}(T)}=\begin{cases}
\big(0.4+0.6\,\tfrac{T}{T_A}\big)\,S_{DS} & 0\le T\le T_A\\[2pt]
S_{DS} & T_A\le T\le T_B\\[2pt]
\tfrac{S_{D1}}{T} & T_B\le T\le T_L\\[2pt]
\tfrac{S_{D1}\,T_L}{T^2} & T\ge T_L
\end{cases}
$$

## Bina sınıfları, R ve D

- **Bina kullanım sınıfı** (BKS, Tablo 3.1) ve **önem katsayısı** $I$: hastane, okul, yurt, itfaiye BKS 1 ($I=1.5$); AVM, spor salonu, sinema, ibadethane BKS 2 ($I=1.2$); konut, işyeri, otel BKS 3 ($I=1.0$).
- **Deprem tasarım sınıfı** (DTS, Tablo 3.2) $S_{DS}$'ye göre: $\ge0.75$ DTS 1, $0.50$–$0.75$ DTS 2, $0.33$–$0.50$ DTS 3, $<0.33$ DTS 4; BKS 1'de "a" eki (1a, 2a …).
- **Bina yükseklik sınıfı** (BYS, Tablo 3.3) $H_N$'ye ve DTS'ye göre: DTS 1–2'de $H_N\le7$ m BYS 8, $7$–$10.5$ BYS 7, $10.5$–$17.5$ BYS 6, $17.5$–$28$ BYS 5, $28$–$42$ BYS 4 …; küçük BYS yüksek bina demektir.

Taşıyıcı sistemin **taşıyıcı sistem davranış katsayısı** $R$ ve **dayanım fazlalığı katsayısı** $D$ Tablo 4.1'dedir: tamamı moment aktaran süneklik düzeyi yüksek betonarme çerçeve (A11) $R=8$, $D=3$, BYS ≥ 3; boşluksuz perde (A13) $R=6$, $D=2.5$; süneklik düzeyi sınırlı çerçeve (A31) $R=4$, $D=2.5$, yalnız DTS 3–4. **Deprem yükü azaltma katsayısı** (Denk. 4.1) ve azaltılmış spektrum (Denk. 4.8):

$$
\kutub{R_a(T)}=\begin{cases}\tfrac{R}{I} & T>T_B\\[2pt] D+\big(\tfrac{R}{I}-D\big)\tfrac{T}{T_B} & T\le T_B\end{cases}
\qquad\qquad
\kutuc{S_{aR}(T)=\frac{S_{ae}(T)}{R_a(T)}}
$$

$I$ büyüdükçe $R_a$ küçülür, deprem yükü büyür. Kısa periyotta $R_a$ $D$'ye iner: çok rijit yapı sünekliğinden az yararlanır. Aşağıda harita değerlerini, zemini ve sistemi değiştir; $T_p$ noktasındaki $S_{ae}$ ve $S_{aR}$ canlı hesaplanır.

::: etkilesim deprem-spektrumu
{"SS": 1.0, "S1": 0.3, "zemin": "ZC", "R": 8, "I": 1.0, "D": 3, "Tp": 0.54}
:::

## Kat kütleleri ve hakim periyot

Kat kütlesi sabit yükün tamamı ile hareketli yükün $n$ katıdır (Denk. 4.16, Tablo 4.3): konut, işyeri, otel, hastane $n=0.3$; okul, yurt, mağaza, lokanta, sinema $n=0.6$; depo $n=0.8$; çatı katında karın %30'u da eklenir.

$$
\kutua{w_i=w_{G,i}+n\,w_{Q,i}},\qquad m_i=\frac{w_i}{g},\qquad m_t=\sum_i m_i
$$

**Ampirik periyot** (Denk. 4.27) bina yüksekliğinden: $T_{pA}=C_t\,H_N^{3/4}$; yalnız betonarme çerçevede $C_t=0.1$, çelik çerçevede $0.08$, diğerlerinde $0.07$. **Rayleigh periyodu** (Denk. 4.26) ise modelin kendisinden gelir: katlara keyfi büyüklükte ama ters üçgen biçimli **kurgusal kuvvetler** $F_{fi}$ uygulanır, kat yer değiştirmeleri $d_{fi}$ okunur:

$$
\kutub{T_p=2\pi\left(\frac{\sum_i m_i\,d_{fi}^2}{\sum_i F_{fi}\,d_{fi}}\right)^{1/2}}\ \le\ 1.4\,T_{pA}\qquad(\text{md. 4.7.3.2})
$$

DTS 3–4 binalarda ve DTS 1–2'de BYS ≥ 6 binalarda $T_p\cong T_{pA}$ alınabilir (md. 4.7.3.3). Rayleigh periyodu deprem hesabında **çatlamış kesit** rijitlikleriyle (Tablo 4.2, md. 4.5.8) bulunmalıdır: çerçeve kolonu $0.70\,EI$, çerçeve kirişi $0.35\,EI$, perde $0.50$, bağ kirişi $0.15$. Çatlamamış kesit binayı olduğundan rijit, periyodu kısa gösterir.

## Taban kesme ve kat kuvvetleri

**Toplam eşdeğer deprem yükü** (taban kesme kuvveti, Denk. 4.19) ve alt sınırı:

$$
\kutuc{V_{tE}=m_t\,S_{aR}(T_p)\,g\ \ \ge\ \ 0.04\,m_t\,I\,S_{DS}\,g}
$$

$V_{tE}$'nin bir kısmı yüksek modların etkisi için tepe kata ayrılır (Denk. 4.22); kalanı katlara kütle ve yükseklikle orantılı, yani **ters üçgen** biçiminde dağıtılır (Denk. 4.23). $H_i$ bina tabanından ölçülür:

$$
\ksil{\Delta F_{NE}=0.0075\,N\,V_{tE}},\qquad
\ka{F_{iE}=(V_{tE}-\Delta F_{NE})\,\frac{m_i\,H_i}{\sum_j m_j\,H_j}},\qquad
V_{tE}=\Delta F_{NE}+\sum_i F_{iE}
$$

Kat kesmesi $V_i$ o katın ve üstündeki katların kuvvetlerinin toplamıdır; taban devrilme momenti $M_o=\sum F_{iE}H_i$ (Denk. 4.25). Kat sayısını, ağırlığı ve yüksekliği değiştir; ters üçgen, $\Delta F_N$ ve kat kesmesi canlı güncellenir.

::: etkilesim kat-kuvvetleri
{"N": 3, "w": 1006.38, "wN": 787.5, "h": 3.2, "SDS": 1.2, "SD1": 0.45, "R": 8, "D": 3, "I": 1.0}
:::

## Rijit diyafram, dışmerkezlik ve burulma

Betonarme döşeme kendi düzleminde çok rijittir: bir kattaki bütün düğümler birlikte ötelenir ve döner. Bu **rijit diyafram** varsayımı kat başına üç serbestlik ($u_X$, $u_Y$, $\theta_Z$) bırakır; SAP2000'de "Diaphragm constraint", bu motorda kütle merkezindeki efendi düğümdür. Kat kuvveti kütle merkezine etkir, ama kütlenin yeri ve deprem hareketinin dönme bileşeni belirsiz olduğu için kuvvet **±%5 kaydırılır** (md. 4.5.10.2):

$$
e_i=\pm0.05\,B_i,\qquad M_{ib}=F_{iE}\,e_i\qquad(\text{Denk. 4.17};\ B_i:\ \text{depreme dik kat boyutu})
$$

Burulma, kenardaki düşey elemanların ortadakilerden çok ötelenmesine yol açar. **Burulma düzensizliği katsayısı** (Tablo 3.6, A1):

$$
\eta_{bi}=\frac{(\Delta_i)_{\max}}{(\Delta_i)_{\text{ort}}},\qquad (\Delta_i)_{\text{ort}}=\tfrac12\big[(\Delta_i)_{\max}+(\Delta_i)_{\min}\big];\qquad
\eta_{bi}>1.2\ \Rightarrow\ \text{A1},\quad D_{bi}=\Big(\frac{\eta_{bi}}{1.2}\Big)^2
$$

A1 düzensizliği olan **her katta ayrı ayrı** ($1.2<\eta_{bi}\le2.0$), o katın ±%5 dışmerkezliği **her iki deprem doğrultusu için** $D_{bi}$ ile büyütülür (Denk. 4.29, md. 4.7.4); düzensizlik yalnız Y depreminde çıksa da X depreminin dışmerkezliği de büyür. Motor $\eta_{bi}$ olarak o katın iki doğrultudaki değerinin büyüğünü alır ve birim burulmayı kat kat ayrı çözer. $\eta_{bi}>2$ ise yöntem kendiliğinden yasak değildir: bina Tablo 4.4'ün "diğer tüm binalar" satırına düşer.

## Göreli kat ötelemesi ve ikinci mertebe

Azaltılmış deprem yükleriyle bulunan göreli kat ötelemesi $\Delta_i=u_i-u_{i-1}$ (Denk. 4.32) gerçek ötelemenin $R/I$'da biridir; etkin değer $\delta_i=(R/I)\,\Delta_i$ (Denk. 4.33). Sınır (Denk. 4.34) dolgu duvarın çerçeveye bağlanışına göredir:

$$
\lambda\,\frac{\delta_{i,\max}}{h_i}\le\begin{cases}0.008\,\kappa & \text{gevrek dolgu çerçeveye bitişik}\\ 0.016\,\kappa & \text{esnek derzli ya da bağımsız dolgu}\end{cases}
\qquad \lambda=\frac{S_{ae}(T_p;\text{DD-3})}{S_{ae}(T_p;\text{DD-2})},\quad \kappa=\begin{cases}1 & \text{betonarme}\\0.5 & \text{çelik}\end{cases}
$$

Bu hesapta 1.4$T_{pA}$ sınırı ve Denk. (4.19) alt sınırı uygulanmaz (md. 4.9.1.1). **İkinci mertebe gösterge değeri** (Denk. 4.35–4.37) $\theta_{II,i}=(\Delta_i)_{\text{ort}}\sum_{k\ge i}w_k/(V_i\,h_i)\le0.12\,D/(C_h\,R)$; betonarmede $C_h=0.5$. Aşılırsa iç kuvvetler $\beta_{II}=0.88+(C_hR/D)\,\theta_{II,\max}\ge1$ ile büyütülür.

::: not Yöntem ne zaman kullanılabilir? (Tablo 4.4)
Her katta $\eta_{bi}\le2.0$ olan ve yumuşak kat (B2) düzensizliği bulunmayan binalarda EDYY, DTS 1–2'de BYS ≥ 4, DTS 3–4'te BYS ≥ 5 için kullanılabilir; öteki binalarda sınırlar BYS ≥ 5 ve BYS ≥ 6'dır. Daha yüksek binalar mod birleştirme yöntemi (md. 4.8) ister. Motor $\eta_{bi}$'yi çözümden sonra denetler ($\eta_{bi}>2$ ise ikinci satırın eşiğiyle karşılaştırır); B2'yi denetlemez.
:::

::: hata Spektrum değerini doğrudan V_tE'ye çevirmek
$V_{tE}=m_t\,S_{ae}\,g$ yazmak deprem yükünü $R_a$ kat (betonarme çerçevede 8 kat) büyük bulur; $V_{tE}=W_t\,S_{ae}$'yi ise $g$'yi iki kez kullanarak $m_t\,S_{ae}\,g^2$ diye yazmak birim hatasıdır. $S_{aR}$ boyutsuzdur (g cinsinden): $V_{tE}=m_t\,S_{aR}\,g=W_t\,S_{aR}$.
:::

::: hata Çatlamamış kesitle periyot hesaplamak
Brüt kesitle bulunan Rayleigh periyodu kısa çıkar ($0.349$ s) ve plato yakınında deprem yükünü büyütür ama göreli kat ötelemesini küçük gösterir. Deprem hesabında Tablo 4.2 çarpanları zorunludur (md. 4.5.8.1); ders binasında periyot $0.502$ s'ye çıkar, aynı $\lambda$ ile 2. kattaki öteleme oranı $0.0034$'ten $0.0048$'e, yaklaşık 1.4 katına büyür. Motor betonarme binada deprem açıkken çatlamış kesiti varsayılan alır; `catlamis_rijitlik: false` yazılırsa çözer ama "TBDY 4.5.8.1'e aykırı" uyarısı verir. Yalnız deprem birleşimleri çatlamış $K$'den gelir (md. 4.5.8.3); $1.4G+1.6Q$ brüt kesitle kalır.
:::

::: hata λ'yı unutmak ya da DD-2 spektrumuyla denetlemek
Göreli kat ötelemesi sınırı DD-3 (sık deprem) için yazılmıştır; $\lambda$ katsayısı DD-2 ötelemesini o düzeye indirir. AFAD'dan DD-3 değerleri alınmadan $\lambda=1$ yazmak güvenli taraftadır ama ders binasında oranı $0.0120$'ye çıkarıp sınırı (0.008) üç katta da "aşar"; doğru $\lambda=0.40$ ile 2. katta oran $0.0048$'dir.
:::

## Çözümlü örnekler

Örnekler `betonarme-3kat-3x3` şablonunu kullanır: akslar 0–5–10 m ve 0–4–8 m, üç kat 3.2 m ($H_N=9.6$ m), 45×45 kolon, 25×55 kiriş, büro ($n=0.3$); $S_S=1.0$, $S_1=0.3$, ZC, BKS 3, A11 ($R=8$, $D=3$), rijit diyafram, çatlamış kesit (Tablo 4.2); DD-3 için $S_S=0.4$, $S_1=0.12$. Dış kirişlerde tuğla duvar, çatıda 1 m parapet. Aynı binayı [Bina sayfasında aç](#bina/sablon/betonarme-3kat-3x3).

::: ornek Ara değerli F_S, F_1 ve spektrum köşeleri
Bir parselde $S_S=1.2$, $S_1=0.35$ (DD-2) ve zemin ZD. $F_S$, $F_1$, $S_{DS}$, $S_{D1}$, $T_A$ ve $T_B$'yi bul.
--- ipucu
$S_S=1.2$, 1.00 ile 1.25 sütunları arasında (ZD: 1.1 ve 1.0); $S_1=0.35$, 0.3 ile 0.4 arasında (ZD: 2.0 ve 1.9).
--- cevap
$$
\begin{aligned}
F_S&=1.1+\frac{1.2-1.0}{1.25-1.0}\,(1.0-1.1)=1.1-0.08=\kutua{1.02},\qquad
F_1=2.0+\frac{0.35-0.3}{0.4-0.3}\,(1.9-2.0)=\kutua{1.95}\\
S_{DS}&=1.2\cdot1.02=\kutuc{1.224},\qquad S_{D1}=0.35\cdot1.95=\kutuc{0.6825}\\
T_B&=\frac{0.6825}{1.224}=\kb{0.5576}\ \text{s},\qquad T_A=0.2\,T_B=\kb{0.1115}\ \text{s}
\end{aligned}
$$
--- kod
b = yapi.bina_sablon("betonarme-3kat-3x3")
b["deprem"].update({"SS": 1.2, "S1": 0.35, "zemin_sinifi": "ZD"})
d = yapi.deprem_onizleme(b)
mo.transpoz([[d["FS"], d["F1"], d["SDS"], d["SD1"], round(d["TA"], 4), round(d["TB"], 4)]])
--- kontrol
abs(float(r.deger[0]) - 1.02) < 1e-9 and abs(float(r.deger[1]) - 1.95) < 1e-9 and abs(float(r.deger[2]) - 1.224) < 1e-9 and abs(float(r.deger[3]) - 0.6825) < 1e-9 and abs(float(r.deger[5]) - 0.5576) < 1e-9
--- yorum
`yapi.deprem_onizleme(b)` çözüm yapmadan spektrumu, sınıfları, kat ağırlıklarını ve $T_{pA}$ ile $V_{tE}$'yi verir (arayüzün deprem kartı bunu kullanır). Yumuşak zeminde $F_1$ büyük olduğundan $T_B$ sağa kayar: plato uzar, orta periyotlu binalar daha büyük ivme alır.
:::

::: ornek Sınıflar: DTS, BYS, sistem ve yöntem
Ders binası için ($S_{DS}=1.2$, $H_N=9.6$ m, BKS 3, A11) DTS ve BYS'yi bul; A11 sistemi ve eşdeğer deprem yükü yöntemi kullanılabilir mi? $T_p\cong T_{pA}$ alınabilir mi?
--- ipucu
Tablo 3.2'de $S_{DS}\ge0.75$; Tablo 3.3'te DTS 1–2 sütunu.
--- cevap
$$
\begin{aligned}
S_{DS}=1.2\ge0.75\ &\Rightarrow\ \kutua{\text{DTS}=1}\quad(\text{BKS 3: "a" eki yok}),\qquad I=1.0\\
7<H_N=9.6\le10.5\ &\Rightarrow\ \kutua{\text{BYS}=7}\\
\text{A11: BYS}\ge3\ &\Rightarrow\ 7\ge3\ \checkmark,\qquad \text{Tablo 4.4: BYS}\ge4\ \Rightarrow\ \kc{\text{EDYY uygulanabilir}}\\
\text{md. 4.7.3.3: DTS 1 ve BYS}\ge6\ &\Rightarrow\ T_p\cong T_{pA}\ \text{alınabilir}
\end{aligned}
$$
--- yorum
BYS büyüdükçe bina alçalır; "BYS ≥ 4" kuralı 4, 5, 6, 7 ve 8'i kapsar. Aynı bina BKS 1 olsaydı (okul) DTS 1a olur, süneklik düzeyi sınırlı sistemler (A31 …) kullanılamazdı (md. 4.3.4.1).
:::

::: ornek Kat kütleleri, T_pA ve V_tE
Ders binasının kat ağırlıkları $w_1=w_2=1006.38$ kN, $w_3=787.5$ kN. Ampirik periyotla $V_{tE}$'yi ve alt sınırı bul.
--- ipucu
$w_1=w_G+0.3\,w_Q=958.38+0.3\cdot160$; çatıda üstte kolon ve kat boyu duvar yok (1 m parapet), karın %30'u eklenir. $T_{pA}=0.1\cdot9.6^{0.75}$.
--- cevap
$$
\begin{aligned}
W_t&=2\cdot1006.38+787.5=\ka{2800.26}\ \text{kN},\qquad m_t=\frac{2800.26}{9.81}=\ka{285.45}\ \text{t}\\
T_{pA}&=0.1\cdot9.6^{0.75}=\kb{0.5454}\ \text{s}>T_B=0.375\ \Rightarrow\ S_{ae}=\frac{0.45}{0.5454}=0.8251,\quad R_a=\frac{R}{I}=8\\
S_{aR}&=\frac{0.8251}{8}=0.10314,\qquad V_{tE}=m_t\,S_{aR}\,g=2800.26\cdot0.10314=\kutuc{288.81}\ \text{kN}\\
V_{\min}&=0.04\cdot1.0\cdot1.2\cdot2800.26=134.41\ \text{kN}<288.81\ \checkmark
\end{aligned}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
abs(r.veri["deprem"]["W_t"] - 2800.26) < 1e-6 and abs(r.veri["deprem"]["TpA"] - 0.5453853) < 1e-6 and r.veri["deprem"]["Tp_yontem"] == "ampirik" and abs(r.veri["deprem"]["SaR"] - 0.1031381) < 1e-6 and abs(r.veri["deprem"]["VtE"] - 288.8135) < 1e-3 and abs(r.veri["deprem"]["VtE_min"] - 134.4125) < 1e-3 and [k["w_i"] for k in r.veri["deprem"]["katlar"]] == [1006.38, 1006.38, 787.5]
--- yorum
Çatı katının ağırlığı daha azdır: üstünde kolon yoktur ($9\cdot8.1=72.9$ kN eksik), dış kirişlerde kat boyu duvar yerine 1 m parapet vardır, karın %30'u ($0.3\cdot48=14.4$ kN) eklenir. $V_{tE}/W_t=0.103$: binanın ağırlığının onda biri yatay kuvvet olarak tasarıma girer. Motor DTS 1 ve BYS 7 için `periyot: "otomatik"` ile ampirik periyodu seçti.
:::

::: ornek Rayleigh periyodunu elle hesaplamak
Binada `periyot: "rayleigh"` seçildi (çatlamış kesit, Tablo 4.2, betonarmede varsayılan). Toplamı 100 kN olan kurgusal kuvvetler $F_{fi}=18.700$, $37.400$, $43.899$ kN altında kütle merkezinin X ötelemeleri $d_{fi}=0.9921$, $2.4388$, $3.4471$ mm; $m_i=102.587$, $102.587$, $80.275$ t. $T_p$'yi bul ve motorla karşılaştır.
--- ipucu
$m$ t, $d$ m ve $F$ kN alınırsa oran s² olur. $F_{fi}$ ters üçgendir: $F_{fi}\propto m_iH_i$.
--- cevap
$$
\begin{aligned}
\sum m_i d_{fi}^2&=102.587\,(0.9921^2+2.4388^2)\cdot10^{-6}+80.275\cdot3.4471^2\cdot10^{-6}=\ka{1.6650\cdot10^{-3}}\ \text{t·m}^2\\
\sum F_{fi}d_{fi}&=(18.700\cdot0.9921+37.400\cdot2.4388+43.899\cdot3.4471)\cdot10^{-3}=\kb{0.26109}\ \text{kN·m}\\
T_p&=2\pi\sqrt{\frac{\ka{1.6650\cdot10^{-3}}}{\kb{0.26109}}}=2\pi\cdot0.07986=\kutuc{0.5018}\ \text{s}\ \le1.4\,T_{pA}=0.7635\ \checkmark
\end{aligned}
$$
--- kod
b = yapi.bina_sablon("betonarme-3kat-3x3")
b["deprem"]["periyot"] = "rayleigh"
r = yapi.bina_coz(b)
r
--- kontrol
abs(float(2 * sp.pi) * (sum(k["m"] * k["d_f"] ** 2 for k in r.veri["deprem"]["X"]["rayleigh"]) / sum(k["F_f"] * k["d_f"] for k in r.veri["deprem"]["X"]["rayleigh"])) ** 0.5 - r.veri["deprem"]["Tp"]) < 1e-6 and abs(r.veri["deprem"]["Tp"] - 0.5017564) < 1e-6 and r.veri["deprem"]["Tp_yontem"] == "rayleigh" and r.veri["deprem"]["catlamis_rijitlik"]
--- yorum
Motor kurgusal yükün toplamını 1 kN alır (`rayleigh` listesindeki `F_f`, `d_f`); 100 kN ile her şey 100 katına çıkar, oran değişmez. Brüt kesitle aynı hesap $0.349$ s verir; çatlamış kesit binayı yumuşatır ve periyodu $T_{pA}=0.545$'e yaklaştırır. Y yönünde periyot $0.472$ s'dir: o doğrultudaki çerçevelerin 4 m'lik kısa açıklıkları daha rijittir.
:::

::: ornek V_tE, ΔF_NE ve kat kuvvetleri
Rayleigh periyodu $T_p=0.5018$ s ile (çatlamış kesit) X yönünde $V_{tE}$, $\Delta F_{NE}$, $F_{iE}$ ve kat kesmelerini bul; $\sum F$'nin $V_{tE}$'ye eşit olduğunu denetle.
--- ipucu
$w_iH_i$: $1006.38\cdot3.2$, $1006.38\cdot6.4$, $787.5\cdot9.6$; toplam $17221.2$.
--- cevap
$$
\begin{aligned}
S_{aR}&=\frac{0.45/0.5018}{8}=0.11211,\qquad V_{tE}=2800.26\cdot0.11211=\kutua{313.93}\ \text{kN}\\
\ksil{\Delta F_{NE}}&=0.0075\cdot3\cdot313.93=\ksil{7.063}\ \text{kN},\qquad V_{tE}-\Delta F_{NE}=306.86\\
\ka{F_{1E}}&=306.86\cdot\tfrac{3220.4}{17221.2}=\ka{57.38},\quad \ka{F_{2E}}=306.86\cdot\tfrac{6440.8}{17221.2}=\ka{114.77}\\
\ka{F_{3E}}&=306.86\cdot\tfrac{7560}{17221.2}=134.71,\quad +\Delta F_{NE}=\ka{141.77}\\
V_3&=141.77,\quad V_2=256.54,\quad V_1=\kutuc{313.93}=V_{tE}\ \checkmark
\end{aligned}
$$
--- kod
b = yapi.bina_sablon("betonarme-3kat-3x3")
b["deprem"]["periyot"] = "rayleigh"
r = yapi.bina_coz(b)
r
--- kontrol
abs(r.veri["deprem"]["VtE"] - 313.9265) < 1e-3 and abs(r.veri["deprem"]["dFN"] - 7.0633) < 1e-3 and abs(sum(k["F_x"] for k in r.veri["deprem"]["katlar"]) - r.veri["deprem"]["VtE"]) < 1e-6 and abs(r.veri["deprem"]["katlar"][0]["F_x"] - 57.3842) < 1e-3 and abs(r.veri["deprem"]["katlar"][2]["F_x"] - 141.7740) < 1e-3 and abs(r.veri["deprem"]["katlar"][0]["V_x"] - r.veri["deprem"]["VtE"]) < 1e-6
--- yorum
Tabloda tepe katın `F_x` değeri $\Delta F_{NE}$'yi içerir. Taban devrilme momenti $M_o=2279$ kN·m'dir. Motor E durumlarını yeniden yük yazarak değil birim durumların süperpozisyonuyla kurar: $(V_{tE}-\Delta F_{NE})\cdot$(birim ters üçgen) $+\ \Delta F_{NE}\cdot$(tepe birim yük) $\pm\,0.05\sum_i D_{bi}\cdot$(kat $i$'nin birim burulması).
:::

::: ornek Dışmerkezlik, η_bi ve göreli kat ötelemesi
Aynı çözümde X depremi için 2. katın kolon hatlarındaki göreli ötelemeler $(\Delta_2)_{\max}=4.785$ mm, $(\Delta_2)_{\min}=4.364$ mm; $h=3.2$ m. DD-3 değerleri $S_S=0.4$, $S_1=0.12$ (ZC). $e$, tepe katın burulma momenti, $\eta_{b2}$, $\lambda$, öteleme oranı ve $\theta_{II}$'yi bul ($V_2=256.54$ kN, $w_2+w_3=1793.88$ kN).
--- ipucu
X depremine dik kat boyutu $B=8$ m. DD-3: $S_{DS}=0.4\cdot1.3=0.52$, $S_{D1}=0.12\cdot1.5=0.18$; $T_p$ her iki spektrumda da inen kolda.
--- cevap
$$
\begin{aligned}
e&=0.05\cdot8=\kb{0.4}\ \text{m},\qquad M_{3b}=141.77\cdot0.4=\kb{56.71}\ \text{kN·m}\\
(\Delta_2)_{\text{ort}}&=\tfrac12(4.785+4.364)=4.575,\qquad \eta_{b2}=\frac{4.785}{4.575}=\kutua{1.046}<1.2\ \Rightarrow\ \text{A1 yok},\ D_{b2}=1\\
\lambda&=\frac{0.18/T_p}{0.45/T_p}=\ka{0.40},\qquad \lambda\,\frac{(R/I)\,\Delta_{\max}}{h}=0.40\cdot\frac{8\cdot0.004785}{3.2}=\kutuc{0.00478}\le0.008\ \checkmark\\
\theta_{II,2}&=\frac{0.004575\cdot1793.88}{256.54\cdot3.2}=\kc{0.0100}\le0.12\cdot\frac{3}{0.5\cdot8}=0.09\ \checkmark
\end{aligned}
$$
--- kod
b = yapi.bina_sablon("betonarme-3kat-3x3")
b["deprem"]["periyot"] = "rayleigh"
r = yapi.bina_coz(b)
r
--- kontrol
abs(r.veri["deprem"]["lambda"] - 0.4) < 1e-9 and abs(r.veri["deprem"]["katlar"][1]["oran_x"] - 0.0047847) < 1e-6 and abs(r.veri["deprem"]["katlar"][1]["eta_bx"] - 1.04594) < 1e-4 and abs(r.veri["deprem"]["katlar"][2]["Mb_x"] - 56.7096) < 1e-3 and abs(r.veri["deprem"]["katlar"][1]["theta_x"] - 0.0099962) < 1e-6 and all(k["uygun"] for k in r.veri["deprem"]["katlar"]) and r.veri["deprem"]["theta_sinir"] == 0.09
--- yorum
`veri["deprem"]["katlar"]` her kat için `delta_x` ($\Delta_{\max}$), `delta_etkin_x` ($\delta$), `oran_x`, `eta_bx`, `theta_x`, `e_x`, `Mb_x` ve `uygun` alanlarını taşır. DD-3 verilmeseydi $\lambda=1$ alınır, 2. kattaki oran $0.0120$ olur (üç katta da $>0.008$) ve motor "sınır aşıldı" uyarısı verirdi. Şablon DD-3 değerlerini taşır ve yönetmeliği sağlar.
:::

::: muhendislik Eşdeğer yükten modal analize, oradan OMA'ya
EDYY birinci modun ters üçgen olduğunu ve kütlenin büyük kısmının o modda titreştiğini varsayar; bu yüzden alçak ve düzenli binalarla sınırlıdır (Tablo 4.4). Daha yüksek ya da düzensiz binada mod birleştirme yöntemi (md. 4.8) her modu spektrumdan ayrı alır ve etkin kütle katılımının en az %95'ini ister. SAP2000 ve ETABS'ta Rayleigh periyodunu modal analizin birinci periyoduyla karşılaştırmak iyi bir model denetimidir.

Mevcut yapılarda periyot ölçülebilir: ortam titreşimiyle modal analiz (OMA) gerçek $T_1$'i verir. Tarihi yığma köprülerde ölçülen frekanslar sonlu eleman modelinin rijitliğini ve dolgu kütlesini güncellemekte kullanılır; güncellenmiş model, Rayleigh formülündeki $d_{fi}$'lerin gerçekçi olmasını sağlar.
:::

::: ozet Özet
- DD-2 (475 yıl) tasarım düzeyi; $S_S$, $S_1$ AFAD haritasından. Zemin sınıfıyla Tablo 2.1/2.2'den ara değerli $F_S$, $F_1$; $S_{DS}=S_SF_S$, $S_{D1}=S_1F_1$, $T_A=0.2S_{D1}/S_{DS}$, $T_B=S_{D1}/S_{DS}$, $T_L=6$ s; $S_{ae}(T)$ Denk. (2.2).
- BKS → $I$ (1.0 / 1.2 / 1.5), $S_{DS}$ → DTS, $H_N$ → BYS; Tablo 4.1'den $R$, $D$; $R_a=R/I$ ($T>T_B$) ya da $D+(R/I-D)T/T_B$; $S_{aR}=S_{ae}/R_a$.
- $w_i=w_G+n\,w_Q$ (Tablo 4.3, çatıda karın %30'u); $T_{pA}=C_tH_N^{3/4}$; Rayleigh $T_p=2\pi\sqrt{\sum m d_f^2/\sum F_f d_f}\le1.4T_{pA}$, çatlamış kesitle (Tablo 4.2).
- $V_{tE}=m_tS_{aR}g\ge0.04m_tIS_{DS}g$; $\Delta F_{NE}=0.0075NV_{tE}$; $F_{iE}=(V_{tE}-\Delta F_{NE})m_iH_i/\sum m_jH_j$.
- Rijit diyafram, $e=\pm0.05B$, $M_{ib}=F_{iE}e$; $\eta_{bi}>1.2$ → A1, o katta her iki doğrultu için $D_{bi}=(\eta_{bi}/1.2)^2$; $\eta_{bi}>2$ → Tablo 4.4'ün ikinci satırı. Öteleme $\lambda(R/I)\Delta_{\max}/h\le0.008\kappa$; $\theta_{II}\le0.12D/(C_hR)$. EDYY yalnız Tablo 4.4 sınırları içinde.
:::

## Alıştırma

Taban kesme kuvvetini adım adım kur: önce spektrumun hangi kolundasın, sonra $R_a$, sonra alt sınır.

::: alistirma deprem-vt
{"zorluk": 2}
:::

::: alistirma deprem-vt
{"zorluk": 3}
:::
