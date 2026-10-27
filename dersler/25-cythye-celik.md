---
baslik: ÇYTHYE 2018 ile çelik eleman tahkiki
bolum: yapi
ozet: YDKT ve GKT, Tablo 2.1A malzemeleri, Tablo 5.1A/5.1B enkesit sınıfı; eğilmede M_p, L_p, L_r, C_b ve yanal burulmalı burkulmanın üç bölgesi; basınçta KL/i, F_e, F_cr eğrisi ve 4.71√(E/F_y) geçişi, burulmalı burkulma; kesmede C_v1 ve φ_v; çekmede akma ve kırılma; bileşik etki (Denk. 11.1a/b); K seçiminin önemi ve bu araçtaki K = 1 varsayımı; depo şablonunun tasarım sonucu.
sure: 85
---

## Neden?

Çelik malzeme betondan on kat güçlüdür; bu yüzden çelik elemanlar incedir ve ince eleman dayanımına ulaşmadan önce **burkulur**. Bir IPE 300 kirişin taşıyabileceği moment, basınç başlığı ne sıklıkla yanal tutulduğuna göre yarıya inebilir; bir HEB kolonun basınç dayanımı, boyu iki katına çıkınca üçte birine düşebilir. Türkiye'de çelik yapılar **Çelik Yapıların Tasarım, Hesap ve Yapım Esasları** (ÇYTHYE, RG 15.02.2018/30333 Mük.) ile tasarlanır. Bu derste bir çelik elemanın dayanımını adım adım kuracak ve depo şablonunun motor sonuçlarını okuyacaksın.

## İki tasarım yöntemi: YDKT ve GKT

::: tanim YDKT ve GKT
**Yük ve Dayanım Katsayıları ile Tasarım** (YDKT, md. 5.2.2) katsayılı yüklerle hesaplanan gerekli dayanımı **dayanım katsayısı** $\phi$ ile küçültülmüş nominal dayanımla karşılaştırır: $R_u\le\phi R_n$ (Denk. 5.1). **Güvenlik Katsayıları ile Tasarım** (GKT, md. 5.2.3) katsayısız yüklerle çalışır ve nominal dayanımı **güvenlik katsayısı** $\Omega$'ya böler: $R_a\le R_n/\Omega$ (Denk. 5.2). İki yöntem de kullanılabilir.
:::

| Etki | YDKT $\phi$ | GKT $\Omega$ | Madde |
|---|---|---|---|
| eğilme | 0.90 | 1.67 | 9.1 |
| basınç | 0.90 | 1.67 | 8.2 |
| kesme (hadde I, $h/t_w\le2.24\sqrt{E/F_y}$) | 1.00 | 1.50 | 10.2.1(a) |
| çekme, akma / kırılma | 0.90 / 0.75 | 1.67 / 2.00 | 7.2.1 / 7.2.2 |

YDKT yük birleşimleri ÇYTHYE md. 5.3.1'dedir ($1.4G$, $1.2G+1.6Q+0.5S$, $1.2G+Q+0.5S+1.6W$, $0.9G+1.6W$ …); deprem satırları TBDY md. 9.2.5'e göredir (Ders 22).

**Malzeme** (Tablo 2.1A, EN 10025-2, $t\le40$ mm): S235 $F_y=235$, $F_u=360$; S275 $F_y=275$, $F_u=430$; S355 $F_y=355$, $F_u=510$ MPa. $40<t\le80$ mm'de değerler düşer (S275: 255 ve 410). $E=200000$ MPa, $G=77200$ MPa.

## Enkesit sınıfı

Başlık ve gövde ince levhalardır; akmadan önce yerel olarak buruşabilirler. Genişlik/kalınlık oranı $\lambda$ sınırlarla karşılaştırılır (md. 5.4.1). Hadde I profilde başlık için $\lambda_f=b_f/(2t_f)$, gövde için $\lambda_w=h/t_w$ ($h$: eğrilik yarıçapları çıkarılmış başlıklar arası yükseklik):

| Parça | Eğilme (Tablo 5.1B) $\lambda_p$ | $\lambda_r$ | Basınç (Tablo 5.1A) $\lambda_r$ |
|---|---|---|---|
| başlık (Durum 10 / 1) | $0.38\sqrt{E/F_y}$ | $1.00\sqrt{E/F_y}$ | $0.56\sqrt{E/F_y}$ |
| gövde (Durum 15 / 5) | $3.76\sqrt{E/F_y}$ | $5.70\sqrt{E/F_y}$ | $1.49\sqrt{E/F_y}$ |

Eğilmede $\lambda\le\lambda_p$ **kompakt** (tam plastik momente ulaşır), $\lambda_p<\lambda\le\lambda_r$ **kompakt olmayan**, $\lambda>\lambda_r$ **narin**; basınçta yalnız narin olan ve olmayan ayrılır.

## Eğilme: M_p ve yanal burulmalı burkulma

Kompakt kesitin üst sınırı **plastik momenttir**: $M_p=F_yW_{pl,y}$ (Denk. 9.2). Ama basınç başlığı yanal olarak tutulmazsa kiriş yana yatıp burularak **yanal burulmalı burkulma** (YBB) yapar. Belirleyici büyüklük **yanal desteksiz boy** $L_b$'dir ve iki sınır boy vardır (Denk. 9.6a/b):

$$
\ka{L_p=1.76\,i_z\sqrt{\frac{E}{F_y}}},\qquad
\kb{L_r=1.95\,i_{ts}\frac{E}{0.7F_y}\sqrt{\frac{Jc}{W_{el,y}h_o}+\sqrt{\Big(\frac{Jc}{W_{el,y}h_o}\Big)^2+6.76\Big(\frac{0.7F_y}{E}\Big)^2}}}
$$

$i_z$ zayıf eksen atalet yarıçapı, $i_{ts}^2=\sqrt{I_zC_w}/W_{el,y}$ (Denk. 9.8a), $J$ burulma sabiti, $C_w$ çarpılma sabiti, $h_o=d-t_f$, çift simetrili I'da $c=1$. Üç bölge:

$$
M_n=\begin{cases}
\ka{M_p} & L_b\le L_p\\[2pt]
\kb{C_b\Big[M_p-(M_p-0.7F_yW_{el,y})\dfrac{L_b-L_p}{L_r-L_p}\Big]\le M_p} & L_p<L_b\le L_r\quad(\text{Denk. 9.3})\\[6pt]
\ksil{F_{cr}W_{el,y}\le M_p},\quad F_{cr}=\dfrac{C_b\pi^2E}{(L_b/i_{ts})^2}\sqrt{1+0.078\dfrac{Jc}{W_{el,y}h_o}\Big(\dfrac{L_b}{i_{ts}}\Big)^2} & L_b>L_r\quad(\text{Denk. 9.5})
\end{cases}
$$

**Moment düzeltme katsayısı** $C_b=12.5M_{maks}/(2.5M_{maks}+3M_A+4M_B+3M_C)$ (Denk. 9.1) moment desteksiz boy boyunca değişiyorsa YBB'nin daha geç oluştuğunu hesaba katar; $M_A$, $M_B$, $M_C$ çeyrek noktalardaki mutlak momentlerdir, $C_b=1$ her zaman güvenlidir. Başlık kompakt değilse yerel burkulma da sınırlar: $M_n=M_p-(M_p-0.7F_yW_{el})(\lambda-\lambda_{pf})/(\lambda_{rf}-\lambda_{pf})$ (Denk. 9.9).

::: etkilesim celik-yanal-burulma
{"profil": "IPE 300", "Fy": 275, "Lb": 3, "Cb": 1}
:::

## Basınç: narinlik ve F_cr eğrisi

Basınç çubuğunun dayanımı **narinliğine** $KL/i$ bağlıdır; $K$ burkulma boyu katsayısı, $KL$ **burkulma boyu**dur ve $KL/i\le200$ olmalıdır (md. 8.1.1). Elastik burkulma (Euler) gerilmesi ve **kritik gerilme** (Denk. 8.2–8.4):

$$
\ksil{F_e=\frac{\pi^2E}{(KL/i)^2}},\qquad
\kutua{F_{cr}=\begin{cases}0.658^{F_y/F_e}\,F_y & KL/i\le4.71\sqrt{E/F_y}\\ 0.877\,F_e & KL/i>4.71\sqrt{E/F_y}\end{cases}},\qquad
P_n=F_{cr}A_g,\quad P_c=\phi_cP_n
$$

Geçiş narinliği S275 için $4.71\sqrt{200000/275}=127.0$'dır (S235: 137.4, S355: 111.8). Kısa çubukta $F_{cr}$, $F_y$'ye yaklaşır; uzun çubukta Euler gerilmesinin 0.877 katıdır: başlangıç eğrilikleri ve artık gerilmeler gerçek çubuğu ideal Euler çubuğundan zayıf yapar. Çift simetrili açık kesitte **burulmalı burkulma** da denetlenir: $F_e=(\pi^2EC_w/L_{cz}^2+GJ)/(I_x+I_y)$ (Denk. 8.5); hadde I kolonlarda çoğunlukla belirleyici değildir.

::: etkilesim celik-burkulma
{"KLr": 82.24, "Fy": 275, "profil": "HEB 240"}
:::

## Kesme, çekme ve bileşik etki

**Kesme** (md. 10.2.1): $V_n=0.6F_yA_wC_{v1}$, $A_w=d\,t_w$ (Denk. 10.1). Hadde I gövdesinde $h/t_w\le2.24\sqrt{E/F_y}$ ise $C_{v1}=1$ ve $\phi_v=1.00$; değilse $k_v=5.34$ ile Denk. 10.2 ve $\phi_v=0.90$.

**Çekme** (Bölüm 7): brüt kesitte akma $T_n=F_yA_g$ ($\phi_t=0.90$) ve net kesitte kırılma $T_n=F_uA_e$, $A_e=UA_n$ ($\phi_t=0.75$); küçüğü belirler. Çekme elemanında $L/i\le300$ önerilir (md. 7.1.1).

**Bileşik etki** (md. 11.1.1): eksenel kuvvet ve iki eksenli eğilme birlikte:

$$
\frac{P_r}{P_c}\ge0.2:\ \ \kutua{\frac{P_r}{P_c}+\frac89\Big(\frac{M_{rx}}{M_{cx}}+\frac{M_{ry}}{M_{cy}}\Big)\le1}\ (11.1a),\qquad
\frac{P_r}{P_c}<0.2:\ \ \kutub{\frac{P_r}{2P_c}+\frac{M_{rx}}{M_{cx}}+\frac{M_{ry}}{M_{cy}}\le1}\ (11.1b)
$$

$P_r$ ve $M_r$ ikinci mertebe etkilerini içeren gerekli dayanımlardır (Bölüm 6, $B_1$/$B_2$ büyütmesi); zayıf eksen dayanımı $M_{ny}=\min(F_yW_{pl,z},\ 1.6F_yW_{el,z})$ (Bölüm 9.6; AISC F6 karşılığı). Çekme ile eğilmede aynı denklemler kullanılır (md. 11.1.2).

## K seçimi ve bu aracın varsayımı

$K$, çubuk uçlarının dönme ve ötelenme tutulmasına bağlıdır: ideal iki ucu mafsallı çubukta $K=1$, ideal ankastre–serbest konsolda $K=2$ (Euler çözümleri). Yanal ötelenmesi önlenmemiş çerçeve kolonunda $K>1$ olur ve ÇYTHYE bunu Bölüm 6'daki burkulma boyu yöntemiyle (ya da ikinci mertebe etkileri doğrudan hesaba katan yöntemle) belirler. Bu uygulamanın motoru bütün çelik elemanlarda $K=1$, kolonda $L$ = kat yüksekliği alır. Döşemeli kirişte döşeme yalnız **üst** başlığı tutar: pozitif momentte (açıklık, üst başlık basınçta) $L_b=0$; negatif momentte (mesnet, **alt** başlık basınçta) $L_b$ = açıklık ve $C_b$ moment diyagramının çeyrek noktalarından (Denk. 9.1). İki bölge ayrı denetlenir, büyük D/C belirler (`analiz.celik_Lb = "boy"`: her yerde $L_b=L$, $C_b=1$).

::: hata K = 1'i her yerde doğru sanmak
$K=1$ yalnız uçları yanal ötelenmeye karşı tutulmuş (çaprazlı ya da perdeli) sistemde güvenlidir. Bir sanayi yapısının ankastre ayaklı, tepesi serbest kolonunda $K\approx2$'dir: $KL/i$ iki katına çıkar ve basınç dayanımı üçte birine kadar inebilir (örnek 4). Çaprazsız çerçeve kolonunda $K$'yı mutlaka belirle ya da ikinci mertebe çözümle.
:::

::: hata Basınç başlığının tutulu olduğunu varsaymak
Döşemeye bulonla ya da kayma çivisiyle bağlı kirişin üst başlığı tutuludur; ama konsol kirişte ya da deprem momenti mesnette **alt** başlığı bastırdığında basınç başlığı serbesttir. $L_b$'yi yanlış almak $M_n$'yi iki kat büyük gösterebilir (örnek 2). Aşık ve yanal bağlar $L_b$'yi kısaltmanın en ucuz yoludur.
:::

::: hata Narin kesite sıradan formül uygulamak
Tablo 5.1A'ya göre narin kesitte basınç dayanımı etkin alanla (md. 8.5) azaltılır; Tablo 5.1B'de narin başlık için Denk. 9.10 gerekir. Bu motor kompakt gövdeli hadde I profiller içindir ve narin kesitte uyarı verir; önce sınıfı belirle.
:::

## Çözümlü örnekler

Profil değerleri ArcelorMittal kataloğundandır (`yapi_veri.PROFILLER`): örneğin IPE 300 $W_{pl,y}=628.4$ cm³, $W_{el,y}=557.1$ cm³, $i_z=3.35$ cm, $J=20.12$ cm⁴, $C_w=125.9\cdot10^3$ cm⁶; HEB 240 $A=106$ cm², $i_y=10.31$, $i_z=6.08$ cm. Depo şablonunu [Bina sayfasında aç](#bina/sablon/celik-1kat-depo).

::: ornek Enkesit sınıfı: IPE 300 (S275) ve HEA 200 (S355)
İki profilin eğilme ve basınç sınıfını bul. IPE 300: $b_f=150$, $t_f=10.7$, $h=300$, $t_w=7.1$, $r=15$ mm. HEA 200: $b_f=200$, $t_f=10$, $h=190$, $t_w=6.5$, $r=18$ mm.
--- ipucu
$\sqrt{200000/275}=26.97$, $\sqrt{200000/355}=23.74$.
--- cevap
$$
\begin{aligned}
\text{IPE 300}&:\ \lambda_f=\frac{150}{2\cdot10.7}=\ka{7.01}\le0.38\cdot26.97=10.25,\quad \lambda_w=\frac{300-21.4-30}{7.1}=\kb{35.0}\le3.76\cdot26.97=101.4\ \Rightarrow\ \kutuc{\text{kompakt}}\\
&\ \ \text{basınç: } 7.01\le0.56\cdot26.97=15.10,\ 35.0\le1.49\cdot26.97=40.18\ \Rightarrow\ \text{narin olmayan}\\
\text{HEA 200}&:\ \lambda_f=\frac{200}{2\cdot10}=\ksil{10.0}>0.38\cdot23.74=9.02,\ \ \le1.00\cdot23.74\ \Rightarrow\ \kutusil{\text{kompakt olmayan}}
\end{aligned}
$$
--- kod
[tasarim.kesit_sinifi_anlatimli("IPE 300", 275), tasarim.kesit_sinifi_anlatimli("HEA 200", 355)]
--- kontrol
r[0].veri["egilme"] == "kompakt" and r[0].veri["basinc"] == "narin olmayan" and abs(r[0].veri["baslik"]["oran"] - 7.00935) < 1e-4 and abs(r[0].veri["govde"]["oran"] - 35.0141) < 1e-3 and r[-1].veri["egilme"] == "kompakt olmayan" and abs(r[-1].veri["baslik"]["lambda_p"] - 9.01954) < 1e-4
--- yorum
Aynı HEA 200 S275 ile kompakttır: daha yüksek $F_y$ sınırları sıkılaştırır, çünkü levha akmadan önce burkulmaya daha yakındır. HEA serisinin geniş ve ince başlıkları bu yüzden yüksek dayanımlı çelikte dikkat ister.
:::

::: ornek IPE 300 kirişte üç bölge
IPE 300, S275, $C_b=1$. $M_p$, $L_p$ ve $L_r$'yi bul; $L_b=1.5$, 3 ve 6 m için $M_n$ ve $\phi_bM_n$ nedir?
--- ipucu
$i_{ts}=39.56$ mm, $h_o=289.3$ mm, $Jc/(W_{el,y}h_o)=0.0012484$.
--- cevap
$$
\begin{aligned}
M_p&=275\cdot628.4\cdot10^3=\ka{172.81}\ \text{kN·m},\qquad L_p=1.76\cdot33.5\cdot26.97=\ka{1590}\ \text{mm},\qquad L_r=\kb{5097}\ \text{mm}\\
L_b=1.5&\le L_p:\ M_n=\kutua{172.81}\\
L_b=3&:\ M_n=172.81-(172.81-\underbrace{107.24}_{0.7F_yW_{el}})\frac{3-1.59}{5.097-1.59}=\kutub{146.45}\ \text{kN·m}\\
L_b=6&>L_r:\ \frac{L_b}{i_{ts}}=151.7,\quad F_{cr}=\frac{\pi^2\cdot200000}{151.7^2}\sqrt{1+0.078\cdot0.0012484\cdot151.7^2}=154.46,\quad M_n=\kutusil{86.05}\ \text{kN·m}
\end{aligned}
$$
$\phi_bM_n$: 155.53, 131.81 ve 77.44 kN·m.
--- kod
[tasarim.celik_egilme_anlatimli("IPE 300", 275, 1.5), tasarim.celik_egilme_anlatimli("IPE 300", 275, 3), tasarim.celik_egilme_anlatimli("IPE 300", 275, 6)]
--- kontrol
abs(r[0].veri["Mn_kNm"] - 172.81) < 1e-6 and abs(r[0].veri["Lp_m"] - 1.590033) < 1e-5 and abs(r[0].veri["Lr_m"] - 5.097474) < 1e-5 and abs(r[1].veri["Mn_kNm"] - 146.452) < 1e-3 and abs(r[-1].veri["Fcr_MPa"] - 154.4598) < 1e-3 and abs(r[-1].veri["Mc_kNm"] - 77.4446) < 1e-3 and r[-1].veri["bolge"] == "elastik YBB (Lb > Lr)"
--- yorum
Desteksiz boyu 1.5 m'den 6 m'ye çıkarmak dayanımı yarıya indirdi. Aynı kiriş döşemeye bağlıysa açıklıkta $L_b=0$ alınır ve $M_p$'nin tamamı kullanılır; ama mesnette alt başlık serbesttir: depo şablonunun IPE 300 kirişinin B mesnedinde $M=-89.4$ kN·m, $L_b=6$ m ve $C_b=1$ ile $M_c=77.4$ kN·m olur, D/C $1.26$'ya çıkardı. Diyagramdan $C_b\approx2.1$ alınınca $C_bM_n$ yine $M_p$'ye ulaşır (son örnek).
:::

::: ornek Moment düzeltme katsayısı C_b
Basit mesnetli, düzgün yayılı yüklü 6 m'lik IPE 300 kirişin basınç başlığı yalnız uçlarda tutulu. $C_b$'yi bul ve $M_n$'ye etkisini göster.
--- ipucu
Parabolik momentte çeyrek noktalar $0.75M_{maks}$, orta nokta $M_{maks}$.
--- cevap
$$
C_b=\frac{12.5\cdot1}{2.5\cdot1+3\cdot\ka{0.75}+4\cdot\kb{1}+3\cdot\ka{0.75}}=\frac{12.5}{11}=\kutuc{1.136},\qquad M_n=1.1364\cdot86.05=\kutuc{97.78}\ \text{kN·m}\le M_p\ \checkmark
$$
--- kod
tasarim.celik_egilme_anlatimli("IPE 300", 275, 6, Cb=tasarim.cb_katsayisi(1, 0.75, 1, 0.75))
--- kontrol
abs(r.veri["Cb"] - 1.136364) < 1e-5 and abs(r.veri["Mn_kNm"] - 97.7836) < 1e-3 and abs(r.veri["Mc_kNm"] - 88.0052) < 1e-3
--- yorum
Uçlarda ters işaretli momentler olan (deprem gibi) durumda $C_b$ 2.27'ye kadar çıkar: kısa bir bölge bastırıldığı için kiriş daha geç yatar. Motor şablonlarda $C_b=1$ alır, yani güvenli taraftadır.
:::

::: ornek HEB 240 kolon: F_cr ve K'nın etkisi
HEB 240, S275, iki ucu mafsallı 5 m kolon ($K=1$). $P_c$'yi bul. Aynı kolon ankastre ayaklı ve tepesi serbest olsaydı ($K=2$) ne olurdu?
--- ipucu
Zayıf eksen belirler: $i_z=60.8$ mm. $4.71\sqrt{E/F_y}=127.0$.
--- cevap
$$
\begin{aligned}
K=1&:\ \frac{KL}{i_z}=\frac{5000}{60.8}=\ka{82.24}\le127.0,\quad F_e=\frac{\pi^2\cdot200000}{82.24^2}=291.87,\quad F_{cr}=0.658^{275/291.87}\cdot275=\kutua{185.38}\ \text{MPa}\\
&\ \ P_c=0.90\cdot185.38\cdot10600=\kutuc{1768.5}\ \text{kN}\\
K=2&:\ \frac{KL}{i_z}=\ksil{164.47}>127.0,\quad F_e=72.97,\quad F_{cr}=0.877\cdot72.97=63.99\ \text{MPa},\quad P_c=\kutusil{610.5}\ \text{kN}
\end{aligned}
$$
--- kod
[tasarim.celik_basinc_anlatimli("HEB 240", 275, 5, 5), tasarim.celik_basinc_anlatimli("HEB 240", 275, 10, 10)]
--- kontrol
abs(r[0].veri["KLr"] - 82.2368) < 1e-3 and abs(r[0].veri["Fcr_MPa"] - 185.382) < 1e-2 and abs(r[0].veri["Pc_kN"] - 1768.55) < 1e-1 and r[0].veri["Fe_z_MPa"] > r[0].veri["Fe_y_MPa"] and abs(r[-1].veri["Pc_kN"] - 610.50) < 1e-1 and r[-1].veri["bolge"] == "elastik (Denk. 8.3)"
--- yorum
Burkulma boyu iki katına çıkınca dayanım 1768.5'ten 610.5 kN'a, yani %35'ine düştü. Burulmalı burkulma gerilmesi ($F_{ez}=775$ MPa) zayıf eksen Euler gerilmesinden (292 MPa) büyük olduğundan belirleyici değil.
:::

::: ornek Kesme ve çekme dayanımı
IPE 300 (S275) için kesme dayanımını bul. Aynı profil bir çekme çubuğunda bulon delikleriyle $A_n=45$ cm²'ye iniyor, $U=0.85$; çekme dayanımı nedir?
--- ipucu
$h/t_w=248.6/7.1$; $A_w=d\,t_w=300\cdot7.1$. $A_g=53.81$ cm².
--- cevap
$$
\begin{aligned}
\frac{h}{t_w}&=35.0\le2.24\cdot26.97=60.4\ \Rightarrow\ C_{v1}=1,\ \phi_v=1.00,\qquad \kutua{V_c}=0.6\cdot275\cdot2130=\ka{351.45}\ \text{kN}\\
\text{akma}&:\ 0.90\cdot275\cdot5381=\kb{1331.8}\ \text{kN},\qquad \text{kırılma}:\ 0.75\cdot430\cdot(0.85\cdot4500)=\ksil{1233.6}\ \text{kN}\ \Rightarrow\ \kutusil{T_c=1233.6\ \text{kN}}
\end{aligned}
$$
--- kod
[tasarim.celik_kesme_anlatimli("IPE 300", 275), tasarim.celik_cekme_anlatimli("IPE 300", 275, 430, An=45, U=0.85)]
--- kontrol
abs(r[0].veri["Vc_kN"] - 351.45) < 1e-6 and r[0].veri["Cv1"] == 1.0 and r[0].veri["phi_v"] == 1.0 and abs(r[-1].veri["Tc_kN"] - 1233.5625) < 1e-6 and r[-1].veri["belirleyici"] == "kırılma"
--- yorum
Kesme dayanımı genellikle bol kalır; tehlike tekil yük altındaki kısa kirişlerde ve birleşimlerdedir. Çekmede net kesitin kopması, akmadan farklı olarak gevrektir; bu yüzden katsayısı daha küçüktür (0.75).
:::

::: ornek Bileşik etki: Denk. 11.1a ve 11.1b
HEB 240 S275 kolon, $L=L_b=5$ m, $K=1$, $C_b=1$. İki kombinasyon: K1 $P_r=600$ kN, $M_{rx}=60$, $M_{ry}=10$ kN·m; K2 $P_r=150$ kN, $M_{rx}=90$, $M_{ry}=5$ kN·m. D/C'leri bul.
--- ipucu
$P_c=1768.5$ kN (önceki örnek), $M_{cx}=242.15$ kN·m ($L_p=2.89<5\le L_r=14.11$ m), $M_{cy}=0.9\cdot137.06=123.35$ kN·m.
--- cevap
$$
\begin{aligned}
\text{K1}&:\ \frac{600}{1768.5}=\ka{0.339}\ge0.2\ \Rightarrow\ 0.339+\frac89\Big(\frac{60}{242.15}+\frac{10}{123.35}\Big)=0.339+\frac89(0.248+0.081)=\kutua{0.632}\ (11.1a)\\
\text{K2}&:\ \frac{150}{1768.5}=\kb{0.085}<0.2\ \Rightarrow\ \frac{0.085}{2}+\frac{90}{242.15}+\frac{5}{123.35}=\kutub{0.455}\ (11.1b)
\end{aligned}
$$
--- kod
tasarim.celik_eleman_kontrol_anlatimli("HEB 240", "S275", L=5, kuvvetler=[{"ad": "K1", "N": 600, "Mx": 60, "My": 10, "V": 40}, {"ad": "K2", "N": 150, "Mx": 90, "My": 5, "V": 50}])
--- kontrol
abs(r.veri["kombinasyonlar"][0]["dc_etkilesim"] - 0.631569) < 1e-5 and r.veri["kombinasyonlar"][0]["dal"] == "11.1a" and abs(r.veri["kombinasyonlar"][1]["dc_etkilesim"] - 0.454609) < 1e-5 and r.veri["kombinasyonlar"][1]["dal"] == "11.1b" and abs(r.veri["egilme"]["Mc_kNm"] - 242.152) < 1e-2 and abs(r.veri["egilme"]["Mcy_kNm"] - 123.354) < 1e-2
--- yorum
Aynı kolonda $K=2$ alınsaydı $P_c=610.5$ kN olur ve K1'in D/C'si 1.275'e çıkardı. Bu tahkikte $P_r$ ve $M_r$ birinci mertebedir; ÇYTHYE ikinci mertebe etkilerinin (Bölüm 6) eklenmesini ister, motor bunu uyarı olarak yazar.
:::

::: ornek Depo şablonu: tasarım sonucunu okumak
`celik-1kat-depo` şablonunu (HEB 240 kolonlar, IPE 400 ve IPE 300 kirişler, S275, ÇYTHYE YDKT) çöz. En kritik eleman hangisi, D/C hangi denklemden ve hangi moment bölgesinden geliyor? Kirişin narinlik satırı neden 179.1?
--- ipucu
`veri["tasarim"]["kritik_elemanlar"]`; kirişin kontrolleri: N, Mx, My, etkileşim, kesme, narinlik.
--- cevap
$$
\begin{aligned}
\text{K-A2}&\rightarrow\text{B2/k1 (IPE 300)},\ \texttt{1.2G+1.6Q},\ \text{negatif M (B mesnedi, alt başlık basınçta)}:\ L_b=6\ \text{m},\ C_b=2.08\ \Rightarrow\ C_bM_n\ge M_p,\ M_c=\phi_bM_p\\
&\frac{3.65}{2\cdot261.35}+\frac{\ka{98.72}}{\ka{155.53}}+\frac{\kb{2.66}}{\kb{30.99}}=0.007+0.635+0.086=\kutuc{0.728}\ (11.1b);\quad \text{pozitif M bölgesi } (L_b=0):\ 0.467\\
\frac{KL}{i_z}&=\frac{6000}{33.5}=\ksil{179.1}\le200\ \checkmark,\qquad \text{S-B2/k1 (HEB 240)}:\ \text{D/C}=\kc{0.399}
\end{aligned}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("celik-1kat-depo"))
r
--- kontrol
r.veri["tasarim"]["kritik_elemanlar"][0]["adres"] == "K-A2→B2/k1" and abs(r.veri["tasarim"]["en_buyuk_dc"] - 0.72767) < 1e-4 and r.veri["tasarim"]["kritik_elemanlar"][0]["kontrol"] == "etkileşim 11.1b (negatif M)" and abs(next(e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kiris" and e["no"] == 3)["ozet"]["Cb_neg"] - 2.0823) < 1e-3 and r.veri["tasarim"]["kritik_elemanlar"][0]["kombinasyon"] == "1.2G+1.6Q" and abs(next(x for x in next(e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kiris" and e["no"] == 3)["kontroller"] if "Narinlik" in x["ad"])["talep"] - 179.1) < 0.05 and abs(next(e for e in r.veri["tasarim"]["elemanlar"] if e["tur"] == "kolon" and e["no"] == 4)["dc"] - 0.39939) < 1e-4
--- yorum
Mesnetteki negatif moment alt başlığı bastırır; desteksiz boy açıklığın tamamıdır ($L_b=6>L_r$), ama ankastre uçlu kirişin moment diyagramı $C_b=2.08$ verir ve $C_bM_n$, $M_p$'yi aşar: $M_c=\phi_bM_p=155.53$ kN·m. $C_b=1$ ile aynı kesit D/C $\approx1.3$ ile yetmezdi; çerçeve davranışından gelen küçük eksenel kuvvet nedeniyle basınç dayanımı da hesaplanır ve zayıf eksende 6 m burkulma boyu narinlik sınırına yaklaşır. Kolonlarda D/C 0.40'ın altında: rüzgâr ve deprem açılınca (bina kartı) ÇYTHYE ve TBDY 9.2.5 birleşimleri devreye girer ve tablo değişir.
:::

::: muhendislik Yapı analiz programlarında çelik tasarım ve ÇYTHYE
Yaygın yapı analiz programlarının çoğunda doğrudan ÇYTHYE kodu yoktur; ÇYTHYE AISC 360'a çok yakın olduğundan (YDKT = LRFD, GKT = ASD) uygulamada AISC 360-16 seçilir, malzeme S235/S275/S355 ve TBDY 2018 kombinasyonları elle tanımlanır. Program $K$'yı çerçeve rijitliklerinden hesaplar, $L_b$'yi düğümlerden belirler, $C_b$'yi moment diyagramından bulur; her biri elle değiştirilebilir ve **mutlaka denetlenmelidir**: bölünmüş bir çubuğun her parçası ayrı tutulu sayılır.

Tarihi yapılarda çelik çoğu zaman güçlendirme elemanıdır: yığma köprüye eklenen çekme bağları ya da kemer altı iskeleleri. OMA ile ölçülen frekanslar güçlendirme öncesi ve sonrası karşılaştırılarak çelik elemanın gerçekten yük aldığı doğrulanabilir.
:::

::: ozet Özet
- YDKT: $R_u\le\phi R_n$; GKT: $R_a\le R_n/\Omega$. $\phi_b=\phi_c=0.90$, $\phi_v=1.00$ (hadde I), çekme 0.90/0.75. S275: $F_y=275$, $F_u=430$ MPa ($t\le40$ mm).
- Sınıf: başlık $b/2t_f$, gövde $h/t_w$; eğilmede $\lambda_p=0.38$ ve $3.76\sqrt{E/F_y}$, basınçta $\lambda_r=0.56$ ve $1.49\sqrt{E/F_y}$.
- Eğilme: $M_p=F_yW_{pl}$; $L_b\le L_p$ akma, $L_p<L_b\le L_r$ doğrusal (Denk. 9.3), $L_b>L_r$ elastik YBB (Denk. 9.5); $C_b$ Denk. 9.1.
- Basınç: $F_e=\pi^2E/(KL/i)^2$; $KL/i\le4.71\sqrt{E/F_y}$ ise $F_{cr}=0.658^{F_y/F_e}F_y$, değilse $0.877F_e$; $KL/i\le200$.
- Bileşik: $P_r/P_c\ge0.2$ ise 11.1a, değilse 11.1b. $K$ ve $L_b$ dayanımı belirleyen girdilerdir; bu araç $K=1$ alır, döşemeli kirişte açıklıkta $L_b=0$, mesnette (alt başlık) $L_b$ = açıklık ve diyagramdan $C_b$ ile iki bölgeyi ayrı denetler.
:::

## Alıştırma

Kompakt I kirişte $M_n$'yi bölgesine göre hesapla: önce $L_b$'yi $L_p$ ve $L_r$ ile karşılaştır.

::: alistirma celik-mn
{"zorluk": 2}
:::

::: alistirma celik-mn
{"zorluk": 3}
:::
