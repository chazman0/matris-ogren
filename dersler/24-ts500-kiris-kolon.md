---
baslik: TS 500 ile betonarme kiriş ve kolon tahkiki
bolum: yapi
ozet: Malzeme katsayıları ve tasarım dayanımları; TS 500 md. 7.1 varsayımları ve eşdeğer dikdörtgen blok (k1, Çizelge 7.1); tek donatılı kirişte A_s'nin türetilmesi, ρ_min, ρ_b, ρ_max ve TBDY sınırı, çift donatı, M_r ve D/C, çubuk seçimi; kesmede V_cr, V_c, V_max, A_sw/s, en az etriye ve aralık; kolonda şekil değiştirme uygunluğuyla N–M etkileşim eğrisi, N_0, N_t ve dengeli nokta, e_min, 0.9 f_cd A_c ve 0.40 f_ck A_c, ρ = 0.01–0.04, eş zamanlı (N, M) noktaları, iki eksenli eğilme ve Bresler.
sure: 90
---

## Neden?

Bina çözümü sana her kesitte bir moment, bir kesme ve bir eksenel kuvvet verdi; ama çözüm "bu kiriş taşır mı?" sorusunu yanıtlamaz. Yanıt kesitin içindedir: beton nerede ezilir, çelik ne zaman akar, kaç çubuk ve hangi aralıkta etriye gerekir. Türkiye'de betonarme kesit hesabının kuralları **TS 500:2000**'dedir; deprem bölgesindeki binalarda **TBDY 2018** Bölüm 7 bunlara boyut ve donatı sınırları ekler. Bu derste ders binasının en zorlanan kirişini ve kolonunu el hesabıyla ve `tasarim` motoruyla tahkik edeceksin.

::: sekil Kesitten taşıma gücüne: kiriş ve kolon
<svg viewBox="0 0 440 210" width="100%" font-family="system-ui" font-size="11" fill="currentColor">
<rect x="20" y="30" width="70" height="140" fill="var(--sema-cizgi-bg,rgba(148,163,184,.12))" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5"/>
<rect x="20" y="30" width="70" height="30" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.5"/>
<path d="M14 66H96" stroke="var(--sema-cizgi,#94a3b8)" stroke-dasharray="4 3"/>
<circle cx="32" cy="155" r="5" fill="var(--sema-a,#3b82f6)"/><circle cx="55" cy="155" r="5" fill="var(--sema-a,#3b82f6)"/><circle cx="78" cy="155" r="5" fill="var(--sema-a,#3b82f6)"/>
<text x="55" y="22" text-anchor="middle">kiriş b × h</text>
<text x="100" y="49" fill="var(--sema-b,#f59e0b)">a = k₁c</text>
<text x="100" y="70" fill="var(--sema-cizgi,#94a3b8)">tarafsız eksen</text>
<text x="100" y="159" fill="var(--sema-a,#3b82f6)">A_s</text>
<path class="ok" pathLength="1" d="M200 45H160" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="166,40 160,45 166,50" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<text x="204" y="49" fill="var(--sema-b,#f59e0b)">C = 0.85 f_cd b a</text>
<path class="ok" pathLength="1" d="M160 155H200" stroke="var(--sema-a,#3b82f6)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="194,150 200,155 194,160" stroke="var(--sema-a,#3b82f6)" stroke-width="2" fill="none"/>
<text x="204" y="159" fill="var(--sema-a,#3b82f6)">T = A_s f_yd</text>
<text x="160" y="104">M_r = T (d − a/2)</text>
<path d="M330 185V25M330 185H430" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.4" fill="none"/>
<path d="M330 32C380 40 418 90 414 120C410 150 370 176 330 182" stroke="var(--sema-c,#10b981)" stroke-width="2.2" fill="var(--sema-c-bg,rgba(16,185,129,.13))"/>
<circle cx="414" cy="118" r="4" fill="var(--sema-b,#f59e0b)"/>
<text x="336" y="22">N</text><text x="428" y="200" text-anchor="end">M</text>
<text x="340" y="48" fill="var(--sema-c,#10b981)">N_0</text>
<text x="404" y="108" text-anchor="end" fill="var(--sema-b,#f59e0b)">dengeli</text>
<text x="340" y="176" fill="var(--sema-c,#10b981)">N_t</text>
<text x="380" y="200" text-anchor="middle">kolon N–M</text>
</svg>
:::

## Malzeme ve tasarım dayanımları

::: tanim Tasarım dayanımı
**Karakteristik dayanım** (deneylerin %5 alt sınırı) **malzeme katsayısına** bölünerek **tasarım dayanımı** (design strength) bulunur (TS 500 md. 6.2.5). Yerinde dökme betonda $\gamma_{mc}=1.5$, donatıda $\gamma_{ms}=1.15$:
$$
f_{cd}=\frac{f_{ck}}{\gamma_{mc}},\qquad f_{ctd}=\frac{f_{ctk}}{\gamma_{mc}},\qquad f_{yd}=\frac{f_{yk}}{\gamma_{ms}}
$$
:::

$f_{ck}$ silindir basınç dayanımı, $f_{ctk}$ çekme dayanımıdır; ikisi de TS 500 Çizelge 3.2'den okunur. C30 ve B420C için:

| Sınıf | $f_{ck}$ | $f_{ctk}$ | $f_{cd}$ | $f_{ctd}$ | $k_1$ (Çizelge 7.1) |
|---|---|---|---|---|---|
| C25 | 25 | 1.8 | 16.67 | 1.20 | 0.85 |
| C30 | 30 | 1.9 | 20.00 | 1.267 | 0.82 |
| C35 | 35 | 2.1 | 23.33 | 1.40 | 0.79 |
| C40 | 40 | 2.2 | 26.67 | 1.467 | 0.76 |

Donatıda $f_{yd}=420/1.15=365.22$ MPa ve $E_s=2\cdot10^5$ MPa, akma birim uzaması $\varepsilon_{yd}=f_{yd}/E_s=0.001826$. TBDY 2018 deprem elemanlarında en az C25 ve B420C ya da B500C ister (md. 7.2.5).

## Eşdeğer dikdörtgen blok

TS 500 md. 7.1'in kesit varsayımları şunlardır: beton çekme taşımaz, düzlem kesit düzlem kalır, çelik ile beton tam aderanslıdır, en dış basınç lifinde beton $\varepsilon_{cu}=0.003$'te ezilir, çelik elasto-plastiktir ($\sigma_s=E_s\varepsilon_s\le f_{yd}$). Gerçek parabolik beton gerilmesinin yerine aynı bileşkeyi veren **eşdeğer dikdörtgen blok** kullanılır: şiddeti $0.85f_{cd}$, derinliği $a=k_1c$ ($c$: tarafsız eksen derinliği).

$$
\underbrace{\ka{0.85f_{cd}\,b\,a}}_{C}=\underbrace{\kb{A_sf_{yd}}}_{T},\qquad
M_r=T\Big(d-\frac a2\Big),\qquad \varepsilon_s=0.003\,\frac{d-c}{c}\ \ge\ \varepsilon_{yd}
$$

$d$ faydalı yükseklik (basınç yüzünden çekme donatısının ağırlık merkezine) ve $b$ gövde genişliğidir. Son koşul çeliğin aktığını, yani kırılmanın **sünek** olduğunu doğrular.

## Tek donatılı kiriş: A_s'nin türetilmesi

$T=C$'den $A_s=0.85f_{cd}ba/f_{yd}$; bunu moment denklemine koyunca $M_d=0.85f_{cd}\,b\,a\,(d-a/2)$ çıkar. Bu, $a$ için ikinci derece denklemdir:

$$
\frac{a^2}{2}-d\,a+\frac{M_d}{0.85f_{cd}b}=0\ \ \Longrightarrow\ \
\kutub{a=d-\sqrt{d^2-\frac{2M_d}{0.85f_{cd}\,b}}},\qquad \kutua{A_s=\frac{0.85f_{cd}\,b\,a}{f_{yd}}}
$$

Kök içi negatifse kesit tek donatıyla yetmez. Donatı oranı $\rho=A_s/(bd)$ iki sınır arasında kalmalıdır (TS 500 md. 7.3):

$$
\ksil{\rho_{min}=0.8\,\frac{f_{ctd}}{f_{yd}}}\ \ (\text{Denk. 7.3}),\qquad
\rho-\rho'\le0.85\,\rho_b\ \ (\text{Denk. 7.4}),\qquad \rho\le0.02\ \ (\text{Denk. 7.5; TBDY md. 7.4.2.4})
$$

**Dengeli donatı oranı** $\rho_b$ çeliğin aktığı anda betonun ezildiği orandır. TS 500 kapalı formül vermez; md. 7.1 varsayımlarından $c_b/d=0.003/(0.003+\varepsilon_{yd})=600/(600+f_{yd})$ ile türetilir: $\rho_b=0.85\,k_1\,(f_{cd}/f_{yd})\cdot600/(600+f_{yd})$. En az donatı çatlayan kesitte donatının kopmamasını, üst sınır ise kırılmanın sünek kalmasını sağlar.

::: etkilesim kiris-donati
{"Md": 125.59, "b": 0.25, "h": 0.55, "beton": "C30"}
:::

## Çift donatı ve taşıma gücü

$M_d$, tek donatıyla taşınabilen en büyük moment $M_{lim}$'i ($\rho=\rho_{max}$ için) aşarsa basınç bölgesine **basınç donatısı** $A_s'$ konur. Fazla moment $A_s'$ ile ona eşit ek çekme donatısının oluşturduğu kuvvet çiftine verilir:

$$
A_s'=\frac{M_d-M_{lim}}{\sigma_s'(d-d')},\qquad A_s=A_{s,lim}+A_s'\,\frac{\sigma_s'}{f_{yd}},\qquad \sigma_s'=\min\Big(E_s\,0.003\,\frac{c-d'}{c},\ f_{yd}\Big)
$$

Seçilen çubuklarla **taşıma gücü momenti** $M_r$ tarafsız eksen derinliği $c$ kuvvet dengesinden bulunarak hesaplanır (şekil değiştirme uygunluğu). Talep/kapasite oranı $\text{D/C}=M_d/M_r\le1$ olmalıdır. Çubuk seçiminde kirişte en küçük çap $\phi12$, tek sırada net aralık $\ge\max(20\ \text{mm},\ \phi)$'dir (md. 7.3); TBDY ayrıca $b_w\ge250$ mm ve $h\le3.5\,b_w$ ister (md. 7.4.1.1).

## Kesme: V_cr, V_c, V_max ve etriye

Kesme betonda eğik çatlak açar. **Eğik çatlama dayanımı** (TS 500 md. 8.1.3, Denk. 8.1) ve çatlak sonrası beton katkısı (Denk. 8.4):

$$
\ka{V_{cr}=0.65\,f_{ctd}\,b_w\,d\,\Big(1+\gamma\frac{N_d}{A_c}\Big)},\qquad V_c=0.8\,V_{cr},\qquad
\kb{\frac{A_{sw}}{s}=\frac{V_d-V_c}{f_{ywd}\,d}}\ \ (V_d>V_{cr})
$$

$\gamma$ eksenel basınçta 0.07, çekmede $-0.3$'tür; kirişte $N_d\approx0$. $V_d\le V_{cr}$ ise hesap gerekmez ama **en az etriye** konur: $A_{sw}/s\ge0.3\,f_{ctd}\,b_w/f_{ywd}$ (Denk. 8.6). Beton basınç dikmelerinin ezilmemesi için $V_d\le\ksil{V_{max}=0.22\,f_{cd}\,b_wd}$ (Denk. 8.7). Etriye aralığı $s\le d/2$, $V_d>3V_{cr}$ ise $s\le d/4$ (md. 8.1.6); TBDY sarılma bölgesinde $s\le d/4$, $8\phi_l$ ve 150 mm (md. 7.4.4).

## Kolon: N–M etkileşim eğrisi

Kolon eksenel kuvvet ve momenti birlikte taşır. Tarafsız eksen derinliği $c$'yi saf çekmeden saf basınca kaydırıp her konumda **şekil değiştirme uygunluğuyla** her çubuğun gerilmesini bulursak kesitin taşıyabildiği $(N_r,M_r)$ çiftlerini, yani **etkileşim eğrisini** çizeriz:

$$
\varepsilon_{si}=0.003\,\frac{c-d_i}{c},\quad \sigma_{si}=E_s\varepsilon_{si}\in[-f_{yd},f_{yd}],\quad
N_r=0.85f_{cd}\,b\,a+\sum_i A_{si}\sigma_{si},\quad M_r=0.85f_{cd}\,b\,a\Big(\frac h2-\frac a2\Big)+\sum_iA_{si}\sigma_{si}\Big(\frac h2-d_i\Big)
$$

Eğrinin üç özel noktası vardır. **Saf basınç** $\ka{N_0=0.85f_{cd}(A_c-A_s)+A_sf_{yd}}$, **saf çekme** $\ka{N_t=-A_sf_{yd}}$ ve **dengeli nokta**: en uzak çubuk $\varepsilon_{yd}$'ye ulaşırken beton 0.003'te ezilir, $c_b=0.003\,d/(0.003+\varepsilon_{yd})$. Dengeli noktanın üstünde **basınç kırılması**, altında **çekme kırılması** olur; az basınç ($0.9G-E$ gibi) momente dayanımı düşürür.

Talep noktası $P=(N_d,M_d)$ eğrinin içindeyse kesit yeterlidir. Kapasite oranı orijinden $P$'ye çizilen ışının eğriyi kestiği $Q$ noktasıyla ölçülür: $\text{D/C}=|OP|/|OQ|$ (SAP2000 ve ETABS'taki PMM oranıyla aynı fikir).

::: etkilesim kolon-nm
{"b": 0.45, "h": 0.45, "rho": 0.01, "beton": "C30", "N": 386.63, "M": 85.4}
:::

## Kolon için yönetmelik koşulları

- **En küçük dışmerkezlik** (TS 500 md. 6.3.10, Denk. 6.16): $e_{min}=15\ \text{mm}+0.03h$; $h$ eğilme düzlemindeki boyuttur. Tasarım momenti en az $N_d\,e_{min}$ alınır.
- **Eksenel kuvvet sınırları:** TS 500 $N_d\le0.9f_{cd}A_c$ (md. 7.4.1, Denk. 7.7); TBDY $N_{dm}\le0.40f_{ck}A_c$ (md. 7.3.1.2), $N_{dm}$ $G+Q+E$ birleşimlerindeki en büyük basınçtır.
- **Boyuna donatı:** $0.01\le\rho_t\le0.04$ (TS 500 Denk. 7.8–7.9, TBDY md. 7.3.2); en küçük kesit boyutu TS 500'de 250, TBDY'de 300 mm.
- **Eş zamanlı noktalar:** her kombinasyonun kendi $(N,M)$ çifti denetlenir; zarfın $N_{max}$'ı ile $M_{max}$'ı aynı anda oluşmaz (Ders 22).

::: uyari İki eksenli eğilme: TS 500 ne söyler?
TS 500 md. 7.6.2.6 yalnız "iki doğrultudaki momentler β katsayılarıyla ayrı ayrı büyütülmeli ve hesapta bu momentler esas alınmalıdır" der; bir etkileşim formülü vermez. Doğru çözüm üç boyutlu $N$–$M_x$–$M_y$ yüzeyidir. Bu uygulama öğretici bir yaklaşım kullanır: $N_d\ge0.1f_{ck}A_c$ ise **Bresler ters yük formülü** $1/N_r=1/N_{rx}+1/N_{ry}-1/N_0$, daha az basınçta doğrusal toplam $M_x/M_{rx}+M_y/M_{ry}\le1$.
:::

::: hata Zarfın köşesiyle kolon denetlemek
$N_{max}$ ile $M_{max}$'ı farklı kombinasyonlardan alıp tek nokta yapmak gerçek dışıdır. Bu nokta çoğu zaman güvenli tarafta kalır ama az basınçlı $0.9G\pm E$ noktası, momenti küçük olduğu hâlde, eğrinin çekme kırılması bölümünde belirleyici olabilir. Her kombinasyonun $(N,M_x,M_y)$ üçlüsü ayrı denetlenir.
:::

::: hata Paspayını d sanmak, birimleri karıştırmak
$d=h-d'$; $d'$ paspayı değil, donatı ağırlık merkezinin dış yüze uzaklığıdır (paspayı + etriye + çubuk yarıçapı; burada 50 mm). Formülde $M_d$ N·mm, boyutlar mm, gerilmeler MPa (N/mm²) olmalıdır: 125.59 kN·m $=125.59\cdot10^6$ N·mm. $A_s$ mm² çıkar, cm²'ye 100'e bölerek geçilir.
:::

::: hata ρ_min'i unutmak
Küçük momentte hesap donatısı çok az çıkar. Çatlama momenti aşıldığında beton çekmesi bir anda donatıya aktarılır; donatı azsa kopar ve kiriş uyarı vermeden kırılır. $A_s\ge\rho_{min}\,b\,d$ her zaman denetlenir.
:::

## Çözümlü örnekler

Örneklerin çoğu `betonarme-3kat-3x3` ders binasını kullanır: C30, B420C, 25×55 kirişler, 45×45 kolonlar, paspayı 30 mm (d′ = 50 mm). Aynı binayı [Bina sayfasında aç](#bina/sablon/betonarme-3kat-3x3); anlatımın 12. adımı kesit tahkiklerini özetler.

::: ornek Malzeme ve donatı sınırları (C30, B420C)
C30 beton ve B420C donatı için $f_{cd}$, $f_{ctd}$, $f_{yd}$, $\rho_b$, $\rho_{min}$ ve tek donatılı kesit için $\rho_{max}$'ı bul.
--- ipucu
Çizelge 3.2: $f_{ck}=30$, $f_{ctk}=1.9$ MPa; Çizelge 7.1: $k_1=0.82$.
--- cevap
$$
\begin{aligned}
f_{cd}&=\frac{30}{1.5}=\ka{20},\qquad f_{ctd}=\frac{1.9}{1.5}=\ka{1.267},\qquad f_{yd}=\frac{420}{1.15}=\kb{365.22}\ \text{MPa}\\
\rho_b&=0.85\cdot0.82\cdot\frac{20}{365.22}\cdot\frac{600}{600+365.22}=\kutuc{0.02373},\qquad 0.85\rho_b=0.02017\\
\rho_{min}&=0.8\cdot\frac{1.267}{365.22}=\kutusil{0.00277},\qquad \rho_{max}=\min(0.02017;\ 0.02)=\kutusil{0.02}
\end{aligned}
$$
--- yorum
C30 ve üstünde $0.85\rho_b>0.02$ olduğundan üst sınırı Denk. 7.5 (TBDY 7.4.2.4 ile aynı) belirler; C25'te ise $0.85\rho_b=0.01742$ daha küçüktür. Alt sınır TBDY Denk. 7.8'de de aynıdır.
:::

::: ornek Ders binasının kritik kirişi: gerekli A_s
K-A2→B2/k1 kirişinin mesnet momenti (zarfın $M_{min}$'i, Ders 22) $M_d=125.59$ kN·m; $b=250$, $h=550$, $d=500$ mm, C30, B420C. Gerekli üst donatıyı, çubuk önerisini ve $M_r$'yi bul.
--- ipucu
$0.85f_{cd}b=0.85\cdot20\cdot250=4250$ N/mm; $M_d=125.59\cdot10^6$ N·mm.
--- cevap
$$
\begin{aligned}
\kutub{a}&=500-\sqrt{500^2-\frac{2\cdot125.59\cdot10^6}{4250}}=500-436.92=\kb{63.08}\ \text{mm}\\
\kutua{A_s}&=\frac{4250\cdot63.08}{365.22}=\ka{734.1}\ \text{mm}^2=7.34\ \text{cm}^2,\qquad \rho=\frac{734.1}{250\cdot500}=0.00587\in[\ksil{0.00277},\ \ksil{0.02}]\ \checkmark\\
\text{öneri}&:\ 2\phi18+2\phi12=735.1\ \text{mm}^2,\qquad c=77.0\ \text{mm},\ \ \varepsilon_s=0.003\,\frac{500-77.0}{77.0}=0.0165\ge\varepsilon_{yd}\ \checkmark\\
\kutuc{M_r}&=125.76\ \text{kN·m},\qquad \text{D/C}=\frac{125.59}{125.76}=0.9986
\end{aligned}
$$
--- kod
tasarim.kiris_egilme_anlatimli(125.59, 0.25, 0.55, 0.05)
--- kontrol
r.veri["tek_donatili"] and abs(r.veri["a_mm"] - 63.0803) < 1e-3 and abs(r.veri["As_gerekli_cm2"] - 7.34059) < 1e-4 and r.veri["oneri"]["metin"] == "2Φ18 + 2Φ12" and abs(r.veri["Mr_kNm"] - 125.761) < 1e-2 and abs(r.veri["eps_s_r"] - 0.01647) < 1e-4
--- yorum
`tasarim.kiris_egilme(Md, b, h, paspayi)` boyutları m, momenti kN·m alır; `paspayi` burada donatı ağırlık merkezinin yüze uzaklığıdır (d′ = 0.05 m). D/C'nin 1'e bu kadar yakın çıkması tesadüf değildir: öneri gerekli alanı en az fazlalıkla karşılayan çubuk takımıdır. Bina motoru da aynı kirişe aynı öneriyi verir.
:::

::: ornek Çift donatılı kesit
30×60 cm kiriş, C25, B420C, $d=550$ mm, $d'=50$ mm; $M_d=480$ kN·m. Tek donatı yeter mi? Yetmezse $A_s'$ ve $A_s$'yi bul.
--- ipucu
C25'te $\rho_b=0.02050$, $0.85\rho_b=0.01742<0.02$; $k_1=0.85$. Önce $M_{lim}$.
--- cevap
$$
\begin{aligned}
A_{s,lim}&=0.01742\cdot300\cdot550=\ka{2874.5}\ \text{mm}^2,\quad a_{lim}=\frac{2874.5\cdot365.22}{0.85\cdot16.67\cdot300}=247.0,\quad M_{lim}=\ka{447.74}\ \text{kN·m}<480\\
c&=\frac{247.0}{0.85}=290.6\ \text{mm},\qquad \varepsilon_s'=0.003\,\frac{290.6-50}{290.6}=0.00248>\varepsilon_{yd}\ \Rightarrow\ \sigma_s'=f_{yd}\\
\kutub{A_s'}&=\frac{(480-447.74)\cdot10^6}{365.22\,(550-50)}=\kb{176.7}\ \text{mm}^2,\qquad \kutua{A_s}=2874.5+176.7=\ka{3051.2}\ \text{mm}^2\\
\rho&=\frac{3051.2}{300\cdot550}=0.0185\le0.02\ \checkmark,\qquad \rho-\rho'=0.01742\le0.85\rho_b\ \checkmark
\end{aligned}
$$
--- kod
tasarim.kiris_egilme_anlatimli(480, 0.30, 0.60, 0.05, beton="C25")
--- kontrol
not r.veri["tek_donatili"] and r.veri["ust_akiyor"] and abs(r.veri["As_gerekli_cm2"] - 30.5117) < 1e-3 and abs(r.veri["As_ust_gerekli_cm2"] - 1.76661) < 1e-4 and abs(r.veri["c_mm"] - 290.608) < 1e-2 and not r.veri["oneri"]["sigar"]
--- yorum
Alanlar sağlanıyor ama 30.5 cm² 300 mm genişliğe tek sırada sığmaz: motor $12\phi18$ önerip "iki sıra donatı ya da daha geniş kesit" uyarısı verir. İki sırada $d$ küçülür ve hesap yinelenir; çoğu zaman kirişi derinleştirmek daha ekonomiktir. Basınç donatısı ayrıca tarafsız ekseni yukarı çekerek çeliğin daha çok uzamasına, yani sünekliğe katkı verir.
:::

::: ornek Kesme: hesap gerekmeyen ve gereken durum
Aynı 25×55 kirişte (C30, $d=500$ mm) $V_d=90.16$ kN (bina zarfından) ve $V_d=190$ kN için etriyeyi bul.
--- ipucu
$V_{cr}=0.65\cdot1.267\cdot250\cdot500$; iki kollu $\phi8$: $A_{sw}=100.5$ mm².
--- cevap
$$
\begin{aligned}
\ka{V_{cr}}&=0.65\cdot1.267\cdot250\cdot500=\ka{102.92}\ \text{kN},\quad V_c=0.8V_{cr}=82.33,\quad \ksil{V_{max}}=0.22\cdot20\cdot250\cdot500=\ksil{550}\ \text{kN}\\
V_d&=90.16<V_{cr}:\ \Big(\frac{A_{sw}}{s}\Big)_{min}=\frac{0.3\cdot1.267\cdot250}{365.22}=0.260\ \text{mm}^2/\text{mm},\ s\le\frac d2=250\ \Rightarrow\ \kutuc{\phi8/25}\\
V_d&=190>V_{cr}:\ \kutub{\frac{A_{sw}}{s}}=\frac{190000-82333}{365.22\cdot500}=\kb{0.590}\ \Rightarrow\ s\le\frac{100.5}{0.590}=170\ \Rightarrow\ \kutuc{\phi8/17}
\end{aligned}
$$
--- kod
[tasarim.kiris_kesme_anlatimli(90.161, 0.25, 0.55, 0.05), tasarim.kiris_kesme_anlatimli(190, 0.25, 0.55, 0.05)]
--- kontrol
abs(r[0].veri["V_cr_kN"] - 102.9167) < 1e-3 and not r[0].veri["hesap_gerekli"] and r[0].veri["oneri"]["metin"] == "Φ8/25 (2 kollu)" and r[-1].veri["hesap_gerekli"] and abs(r[-1].veri["Asw_s_gerekli"] - 0.589603) < 1e-5 and r[-1].veri["oneri"]["s_mm"] == 170 and abs(r[-1].veri["V_max_kN"] - 550) < 1e-9
--- yorum
Bu hesap TS 500 kesmesidir. TBDY'de deprem kirişlerinin kesmesi **kapasite tasarımıyla** (uçlardaki moment kapasitelerinden) bulunur ve sarılma bölgesinde daha sık etriye çıkar; bu araç kapasite tasarımını yapmaz, uyarı olarak yazar.
:::

::: ornek Kolon N–M eğrisinin uç ve dengeli noktaları
45×45 kolon, C30, B420C, $\rho=0.01$ ($A_s=20.25$ cm², dört yüze dağıtılmış 8 çubuk, $d'=50$ mm). $N_0$, $N_t$ ve dengeli noktayı bul; TS 500 ve TBDY eksenel sınırlarını yaz.
--- ipucu
Katmanlar: üstte 3 çubuk (759.4 mm²), ortada 2 (506.3 mm²), altta 3. $d=400$ mm.
--- cevap
$$
\begin{aligned}
\ka{N_0}&=0.85\cdot20\,(202500-2025)+2025\cdot365.22=3408.1+739.6=\ka{4147.6}\ \text{kN},\qquad \ka{N_t}=-739.6\ \text{kN}\\
\kb{c_b}&=\frac{0.003\cdot400}{0.003+0.001826}=\kb{248.6}\ \text{mm},\quad a_b=0.82\cdot248.6=203.9\ \text{mm}\\
\text{dengeli}&:\ \varepsilon_{s,üst}=0.0024\ (\text{akar}),\ \varepsilon_{s,orta}=0.00029\ (\sigma=57.1),\ \varepsilon_{s,alt}=-\varepsilon_{yd}\ \Rightarrow\ \kutuc{(N_b,M_b)=(1575.8;\ 286.7)}\\
N_d&\le0.9f_{cd}A_c=\ksil{3645}\ \text{kN}\ (\text{TS 500}),\qquad N_{dm}\le0.40f_{ck}A_c=\ksil{2430}\ \text{kN}\ (\text{TBDY})
\end{aligned}
$$
--- kod
tasarim.kolon_etkilesim_anlatimli(0.45, 0.45, 20.25, 0.05)
--- kontrol
abs(r.veri["N0_kN"] - 4147.64) < 1e-2 and abs(r.veri["Nt_kN"] + 739.565) < 1e-2 and abs(r.veri["dengeli"]["N_kN"] - 1575.75) < 1e-2 and abs(r.veri["dengeli"]["M_kNm"] - 286.745) < 1e-2 and abs(r.veri["N_max_TBDY_kN"] - 2430) < 1e-9 and r.veri["n_cubuk"] == 8
--- yorum
Dengeli nokta eğrinin en büyük momentidir (286.7 kN·m). TBDY sınırı (2430 kN) dengeli noktanın epey üstündedir; deprem kolonunu basınç kırılması bölgesinin derinlerine sokmamak, yani sünek kalmasını sağlamak içindir. Hesap bloğun yerini aldığı çubuk alanındaki betonu düşer.
:::

::: ornek Kolon A1: eş zamanlı noktalar ve zarf köşesi
Kolon A1 (1. kat, 45×45, $\rho=0.01$) için Ders 22'deki eş zamanlı çiftler: $N_{min}$ kombinasyonu $(447.54;\ 24.82)$, $M_{max}$ kombinasyonu $(386.63;\ 85.4)$, az basınç $(79.07;\ 10.9)$; zarf köşesi $(447.54;\ 85.4)$. Her biri için $e_{min}$ ve radyal D/C'yi bul (yalnız $M_x$).
--- ipucu
$e_{min}=15+0.03\cdot450=28.5$ mm: $N\,e_{min}=447.54\cdot0.0285=12.75$ kN·m $<24.82$.
--- cevap
$$
\begin{aligned}
P_1&=(447.54;\ 24.82):\ Q=(3119.6;\ 173.0)\ \Rightarrow\ \text{D/C}=\frac{24.82}{173.0}=\ka{0.143}\\
P_2&=(386.63;\ 85.4):\ Q=(1250.6;\ 276.2)\ \Rightarrow\ \text{D/C}=\frac{85.4}{276.2}=\kutub{0.309}\\
P_3&=(79.07;\ 10.9):\ Q=(1958.6;\ 270.0)\ \Rightarrow\ \text{D/C}=\kc{0.040}\\
\ksil{P_k}&=\ksil{(447.54;\ 85.4)}:\ \text{D/C}=\ksil{0.300}\ \ (\text{hiçbir kombinasyonda oluşmaz})
\end{aligned}
$$
--- kod
tasarim.kolon_kontrol_anlatimli([447.54, 386.63, 79.073, 447.54], [24.821, 85.4, 10.9, 85.4], 0, 0.45, 0.45, 20.25, 0.05, adlar=["Nmin", "Mmax", "Nmax", "kose"])
--- kontrol
abs(r.veri["noktalar"][0]["dc_x"] - 0.14346) < 1e-4 and abs(r.veri["noktalar"][1]["dc_x"] - 0.30916) < 1e-4 and abs(r.veri["noktalar"][2]["dc_x"] - 0.04037) < 1e-4 and abs(r.veri["noktalar"][3]["dc_x"] - 0.29979) < 1e-4 and abs(r.veri["noktalar"][0]["e_min_x_mm"] - 28.5) < 1e-9
--- yorum
Bu kolonda belirleyen $M_{max}$ kombinasyonudur ve zarf köşesi onu yakalar; ama bina çözümündeki gerçek belirleyen nokta iki eksenli eğilmeli $0.9G-0.3E_X+E_Y-0.3E_Z$ birleşimidir (D/C = 0.660, son örnek). $M_y=0$ verildiğinde de $e_{min}$ y doğrultusunda $N\,e_{min}$ kadar moment doğurur; motor iki doğrultuyu ayrı denetler.
:::

::: ornek İki eksenli eğilme: Bresler ters yük formülü
Aynı kolonda $N_d=1200$ kN, $M_{dx}=90$, $M_{dy}=60$ kN·m. $N_d\ge0.1f_{ck}A_c$ mi? Bresler formülüyle $N_r$ ve D/C'yi bul.
--- ipucu
$0.1f_{ck}A_c=607.5$ kN. Her eksende orijinden $(N_d, M)$ ışınının eğriyi kestiği $N$ değeri: $N_{rx}=2795.3$, $N_{ry}=3214.5$ kN.
--- cevap
$$
\begin{aligned}
\frac{1}{N_r}&=\frac{1}{\ka{N_{rx}}}+\frac{1}{\kb{N_{ry}}}-\frac{1}{N_0}=\frac{1}{\ka{2795.3}}+\frac{1}{\kb{3214.5}}-\frac{1}{4147.6}=4.2774\cdot10^{-4}\\
\kutuc{N_r}&=2337.9\ \text{kN},\qquad \text{D/C}=\frac{1200}{2337.9}=\kutuc{0.513}
\end{aligned}
$$
--- kod
tasarim.kolon_kontrol_anlatimli(1200, 90, 60, 0.45, 0.45, 20.25, 0.05)
--- kontrol
r.veri["noktalar"][0]["iki_eksen_yontemi"] == "Bresler ters yük" and abs(r.veri["noktalar"][0]["N_rx_kN"] - 2795.26) < 0.05 and abs(r.veri["noktalar"][0]["N_ry_kN"] - 3214.47) < 0.05 and abs(r.veri["noktalar"][0]["N_r_kN"] - 2337.86) < 0.05 and abs(r.veri["noktalar"][0]["dc_iki_eksen"] - 0.51329) < 1e-4
--- yorum
Bresler formülü yüksek basınçta iyi sonuç verir; az basınçta tutucu ya da güvensiz olabilir, bu yüzden motor orada doğrusal moment toplamına geçer. TS 500'ün kendisi bu formülü vermez (md. 7.6.2.6); SAP2000 ve ETABS üç boyutlu PMM yüzeyini sayısal olarak kurar.
:::

::: ornek Bina motoru: tasarım sonucunu okumak
Ders binasını çöz ve `veri["tasarim"]`'dan en kritik elemanı, K-A2→B2/k1 kirişinin (bina no 3) donatı önerisini ve kolon A1'in belirleyen kombinasyonunu oku.
--- ipucu
`kritik_elemanlar[0]`; kirişte `ozet["oneri_ust"]`, `ozet["etriye"]`; kolonda `belirleyen["kombinasyon"]`.
--- cevap
$$
\begin{aligned}
\text{kritik}&:\ \text{K-A2}\rightarrow\text{B2/k1},\ \text{eğilme (mesnet, üst)},\ \texttt{G+Q+0.2S+EX++0.3EY++0.3EZ}\\
M_d&=\ka{125.59},\quad M_r=\kb{125.76}\ \text{kN·m}\ \Rightarrow\ \text{D/C}=\kutuc{0.9986},\quad \text{üst}\ 2\phi18+2\phi12,\ \text{alt}\ 2\phi16,\ \phi8/25\\
\text{S-A1/k1}&:\ \text{D/C}=\kutuc{0.660}\ \ (\texttt{0.9G-0.3EX-+EY--0.3EZ},\ \text{iki eksenli, alt uç}),\quad N_{dm}=447.5\le\ksil{2430}
\end{aligned}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-3kat-3x3"))
r
--- kontrol
r.veri["tasarim"]["kritik_elemanlar"][0]["adres"] == "K-A2→B2/k1" and abs(r.veri["tasarim"]["en_buyuk_dc"] - 0.99862) < 1e-4 and next(e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kiris" and e["no"] == 3)["ozet"]["oneri_ust"] == "2Φ18 + 2Φ12" and abs(next(e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kolon" and e["no"] == 1)["dc"] - 0.65969) < 1e-4 and next(e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kolon" and e["no"] == 1)["belirleyen"]["kombinasyon"] == "0.9G-0.3EX-+EY--0.3EZ"
--- yorum
Kirişlerin D/C'si 1'e yakındır çünkü donatı tasarlanır; asıl bilgi önerilen çubuklardadır. Kolonda donatı verilmediği için $\rho=0.01$ varsayıldı ve belirleyen nokta en büyük basınç değil, az basınçlı deprem birleşimidir: zarfla yapılan kolon kontrolünün kaçırdığı durum. Tek elemanın anlatımlı tahkikini (N–M eğrisi ve bütün kombinasyon noktaları) `yapi.eleman_tasarim(r.ic, "kolon", 1)` verir.
:::

::: muhendislik SAP2000, ETABS ve kapasite tasarımı
ETABS ve SAP2000'de betonarme için "TS 500-2000(R2018)" kodu seçilir; program kirişte her istasyonda zarftan üst ve alt donatı ile $A_{sw}/s$, kolonda üç boyutlu $N$–$M_2$–$M_3$ yüzeyi ve orijinden ışınla kapasite oranı verir, $e_{min}=15+0.03h$'yi de uygular. Bu uygulama aynı mantığı açık formüllerle gösterir. Gerçek deprem tasarımı bir adım daha ister: TBDY'nin **kapasite tasarımı** (güçlü kolon–zayıf kiriş, kapasite kesmesi, birleşim bölgesi). Buradaki sonuçlar bu yüzden ön boyutlandırmadır.

Tarihi yığma köprülerde betonarme kesit hesabı yoktur ama aynı düşünce geçerlidir: kemer kesitindeki $(N,M)$ çifti, çekme taşımayan malzemenin etkileşim bölgesinde kalmalıdır (bileşkenin kesit çekirdeğinde ya da kesit içinde kalması). OMA ile güncellenen modelden alınan iç kuvvetler bu denetimin girdisidir.
:::

::: ozet Özet
- $f_{cd}=f_{ck}/1.5$, $f_{ctd}=f_{ctk}/1.5$, $f_{yd}=f_{yk}/1.15$ (md. 6.2.5); $\varepsilon_{cu}=0.003$, blok $0.85f_{cd}$, $a=k_1c$ (md. 7.1, Çizelge 7.1).
- Tek donatı: $a=d-\sqrt{d^2-2M_d/(0.85f_{cd}b)}$, $A_s=0.85f_{cd}ba/f_{yd}$; $\rho_{min}=0.8f_{ctd}/f_{yd}\le\rho$, $\rho-\rho'\le0.85\rho_b$, $\rho\le0.02$ (Denk. 7.3–7.5, TBDY 7.4.2.4). $M_d>M_{lim}$: çift donatı.
- Kesme: $V_{cr}=0.65f_{ctd}b_wd$, $V_c=0.8V_{cr}$, $A_{sw}/s=(V_d-V_c)/(f_{ywd}d)\ge0.3f_{ctd}b_w/f_{ywd}$, $V_d\le0.22f_{cd}b_wd$, $s\le d/2$.
- Kolon: N–M eğrisi şekil değiştirme uygunluğuyla; $N_0$, $N_t$, dengeli nokta; D/C $=|OP|/|OQ|$; $e_{min}=15+0.03h$ (Denk. 6.16); $N_d\le0.9f_{cd}A_c$, $N_{dm}\le0.40f_{ck}A_c$; $0.01\le\rho\le0.04$.
- Kolon her kombinasyonun eş zamanlı noktasıyla denetlenir; iki eksenli eğilmede TS 500 yalnız momentleri ayrı büyütmeyi söyler, Bresler öğretici bir yaklaşımdır.
:::

## Alıştırma

Kiriş donatısını el hesabıyla bul: önce blok derinliği, sonra alan, en sonda en az donatı.

::: alistirma kiris-as
{"zorluk": 1}
:::

::: alistirma kiris-as
{"zorluk": 3}
:::
