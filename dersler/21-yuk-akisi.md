---
baslik: Yük akışı: döşemeden zemine
bolum: yapi
ozet: TS 498:2021 yükleri, TS 500 md. 11.4.3 45° kuralıyla döşemeden kirişe üçgen ve trapez yük, eşdeğer düzgün yükler ve sınırları, kirişten kolona ve temele birikim, taban basıncı ve beş sayılık korunum.
sure: 60
---

## Neden?

Bir salonun ortasına koyduğun 1 kN'luk koltuk zemine nasıl ulaşır? Önce döşeme plağı onu dört kenarındaki kirişlere paylaştırır, kirişler uç kesmeleriyle kolonlara verir, kolonlar kat kat biriktirir, temel tabanı zemine basınç olarak yayar. Bu yolculuğa **yük akışı** (load path) denir ve her yapı hesabı onun üstüne kurulur: yükü yanlış yoldan gönderirsen doğru çözülmüş bir sonlu eleman modeli bile yanlış kuvvet verir. Bu derste yolu hem el hesabıyla hem `yapi` motoruyla izleyeceksin; her durakta iki sonucu karşılaştıracağız.

::: sekil Bir kN'un yolculuğu: döşeme → kiriş → kolon → temel → zemin
<svg viewBox="0 0 420 250" width="100%" font-family="system-ui" font-size="12" fill="currentColor">
<rect x="150" y="18" width="120" height="70" rx="4" fill="var(--sema-a-bg,rgba(59,130,246,.12))" stroke="var(--sema-a,#3b82f6)" stroke-width="1.5"/>
<path d="M150 18L210 53L150 88M270 18L210 53L270 88" stroke="var(--sema-a,#3b82f6)" stroke-dasharray="4 3" fill="none"/>
<text x="210" y="12" text-anchor="middle" fill="var(--sema-a,#3b82f6)">döşeme: w kN/m², 45° çizgileri</text>
<path d="M150 88H270" stroke="var(--sema-b,#f59e0b)" stroke-width="5" stroke-linecap="round" fill="none"/>
<path d="M150 88L170 100H250L270 88Z" fill="var(--sema-b-bg,rgba(245,158,11,.14))" stroke="var(--sema-b,#f59e0b)" stroke-width="1.2"/>
<text x="300" y="100" fill="var(--sema-b,#f59e0b)" font-size="11">kirişe trapez yük</text>
<text x="300" y="114" fill="var(--sema-b,#f59e0b)" font-size="11">tepe p = w·l_k/2</text>
<path class="ok" pathLength="1" d="M210 104V128" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="205,122 210,128 215,122" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<path d="M150 132V196M270 132V196" stroke="var(--sema-c,#10b981)" stroke-width="6" stroke-linecap="round" fill="none"/>
<path class="ok" pathLength="1" d="M160 132H142M260 132H278" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="147,127 142,132 147,137" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<polyline class="ok-uc" points="273,127 278,132 273,137" stroke="var(--sema-b,#f59e0b)" stroke-width="2" fill="none"/>
<text x="20" y="150" fill="var(--sema-c,#10b981)" font-size="11">kolon: N kat kat</text>
<text x="20" y="164" fill="var(--sema-c,#10b981)" font-size="11">birikir (Σ V uç)</text>
<path class="ok" pathLength="1" d="M150 160V186M270 160V186" stroke="var(--sema-c,#10b981)" stroke-width="2.4" fill="none"/>
<polyline class="ok-uc" points="144,180 150,186 156,180" stroke="var(--sema-c,#10b981)" stroke-width="2.4" fill="none"/>
<polyline class="ok-uc" points="264,180 270,186 276,180" stroke="var(--sema-c,#10b981)" stroke-width="2.4" fill="none"/>
<rect x="120" y="196" width="60" height="16" rx="2" fill="var(--sema-cizgi,#94a3b8)" opacity=".5"/>
<rect x="240" y="196" width="60" height="16" rx="2" fill="var(--sema-cizgi,#94a3b8)" opacity=".5"/>
<path d="M20 212H400" stroke="var(--sema-cizgi,#94a3b8)" stroke-width="1.5" fill="none"/>
<path d="M30 212l-7 8M60 212l-7 8M90 212l-7 8M120 212l-7 8M150 212l-7 8M180 212l-7 8M210 212l-7 8M240 212l-7 8M270 212l-7 8M300 212l-7 8M330 212l-7 8M360 212l-7 8M390 212l-7 8" stroke="var(--sema-cizgi,#94a3b8)" fill="none"/>
<path class="ok" pathLength="1" d="M128 226V214M142 226V214M158 226V214M172 226V214M248 226V214M262 226V214M278 226V214M292 226V214" stroke="var(--sema-sil,#ef4444)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="124,218 128,214 132,218" stroke="var(--sema-sil,#ef4444)" stroke-width="1.6" fill="none"/>
<polyline class="ok-uc" points="288,218 292,214 296,218" stroke="var(--sema-sil,#ef4444)" stroke-width="1.6" fill="none"/>
<text x="210" y="243" text-anchor="middle" fill="var(--sema-sil,#ef4444)" font-size="11">temel: σ = N/(BL) ± 6M/(BL²) ≤ q_em; Σ döşeme = Σ kiriş = Σ kolon = Σ temel</text>
<text x="330" y="182" fill="var(--sema-c,#10b981)" font-size="11">N_temel = Σ N_kat</text>
</svg>
:::

## Yük türleri: TS 498:2021

::: tanim Sabit ve hareketli yük
**Sabit yük** $G$ (dead load), yapının kendisiyle gelen ve yeri değişmeyen yüktür: plak, kaplama, sıva, duvar, kiriş ve kolonun öz ağırlığı. **Hareketli yük** $Q$ (live load), kullanımdan gelen ve yeri değişebilen yüktür: insan, eşya, hafif bölme duvarı. Türkiye'de düşey yüklerin hesap değerlerini **TS 498:2021** verir; birim ağırlıklar için md. 5 TS ISO 9194 Ek A'ya yollar, hareketli yükler md. 15.1 Çizelge 6'dadır.
:::

::: uyari TS 498:1997 yürürlükten kalktı
TSE Teknik Kurulu 30.09.2021'de TS 498:2021'i kabul etti; kapakta "TS 498:1997 yerine" yazar ve önsöz önceki baskıları geçersiz sayar. Değerler büyük ölçüde aynı kaldı ama madde ve çizelge numaraları değişti: 1997'deki Çizelge 7 (hareketli yükler) 2021'de **md. 15.1 Çizelge 6**, azaltma çizelgesi **md. 16 Çizelge 7** oldu. TBDY 2018 Tablo 1.1 TS 498'e tarihsiz atıf yapar; md. 1.5 gereği son baskı, yani 2021 kullanılır.
:::

Döşemenin sabit yükü katmanların toplamıdır; betonarme için $\gamma_{ba}=25$ kN/m³ alınır:

$$
\kutua{g}=h_{\text{plak}}\,\gamma_{ba}+\underbrace{\sum_i t_i\,\gamma_i}_{g_{\text{ek}}:\ \text{şap, kaplama, sıva}}
\qquad
\kutub{q}=\text{TS 498:2021 Çizelge 6, kullanım sınıfı}
$$

| Kullanım (Çizelge 6) | $q$ [kN/m²] | Satır |
|---|---|---|
| Çatı arası odalar | 1.5 | 1 |
| Konut odaları ve koridorları, bürolar, teras, hastane odaları, zaman zaman kullanılan düz çatılar | 2.0 | 2 |
| Derslikler, yatakhaneler, konut merdivenleri, çatı bahçesi, hastane mutfağı | 3.5 | 3 |
| Mağaza, lokanta, kütüphane, toplantı salonu, balkon (≤ 10 m²), umuma açık koridor ve merdivenler | 5.0 | 4 |
| Tribün, oturma yeri sabit olmayan | 7.5 | 5 |
| Garaj (≤ 2.5 t araç) | 5.0 | 6 |

Balkon 10 m²'den büyükse $q=5.0+0.35\,(A-10)$ kN/m² (2021'de eklenen tek yeni kural). Duvarlar kirişe **çizgisel** yük olarak gelir: $g_d$ bir metrekare duvarın ağırlığı (tuğla + iki yüz sıva), $h_{\text{net}}$ kat yüksekliğinden kiriş yüksekliği çıkarılmış duvar boyudur. Motorun kuralı: duvar oturduğu kirişe yük verir ve $h_{\text{net}}$ **kirişin altındaki kat yüksekliği** eksi kiriş yüksekliğidir (katlar eşit yükseklikteyse kirişin üstündeki duvarla aynı sayı). Zemin kat duvarları temele oturur; çatı kirişine kat boyu duvar konmaz, yalnız parapet ($h=1.0$ m, `duvar_h`). Kirişin öz ağırlığında döşemeyle çakışan üst kısım çıkarılır, çünkü o hacim plak ağırlığında $\gamma_{ba}h_{\text{plak}}$ olarak zaten sayıldı:

$$
\kutub{g_{\text{duvar}}}=g_d\,h_{\text{net}}\ [\text{kN/m}],\qquad
\kutub{g_{\text{öz}}}=\gamma_{ba}\,b\,(h-t_{\text{döşeme}})\ [\text{kN/m}]
$$

Örneğin 19 cm yatay delikli tuğla ($\gamma=10$ kN/m³) ve 2 + 2 cm sıva ($\gamma=20$): $g_d=0.19\cdot10+0.04\cdot20=2.70$ kN/m²; 25×50 kiriş üstünde $h_{\text{net}}=3.0-0.5=2.5$ m için duvar $6.75$ kN/m, 14 cm döşemeli kirişin öz ağırlığı $0.25\cdot(0.50-0.14)\cdot25=2.25$ kN/m (brüt $b\,h$ ile $3.125$ olurdu: plağın 14 cm'si iki kez sayılırdı; brüte `analiz.kiris_oz = "brut"` ile dönülür).

## Döşemeden kirişe: 45° kuralı

::: tanim Döşeme tipi ve $m$
Dört kenarı kirişe oturan dikdörtgen plakta kısa kenar $l_k$, uzun kenar $l_u$ ve oran $m=l_u/l_k$'dir. $m\le2$ ise **çift doğrultulu** (two-way) döşemedir: plak yükü her iki doğrultuda taşır (TS 500 md. 11.4.1). $m>2$ ise **tek doğrultulu** (one-way) döşemedir: yük yalnız kısa doğrultuda taşınır, uzun kenar kirişlerine gider (md. 11.2.1).
:::

TS 500 md. 11.4.3 kiriş hesabı için yükün dağılışını köşelerden çizilen **45° doğrularının** oluşturduğu alanlara göre verir. Köşelerden 45° çizdiğinde kısa kenara bir üçgen, uzun kenara bir yamuk düşer. Alanı $w$ ile çarpıp kiriş boyuna yaydığında kısa kenar kirişinde **üçgen**, uzun kenar kirişinde **trapez** yayılı yük çıkar; ikisinin de tepesi aynıdır:

$$
\kutua{p=\frac{w\,l_k}{2}}\ [\text{kN/m}],\qquad
\text{üçgen: } \ka{\tfrac{w\,l_k^2}{4}}\ \text{kN},\quad
\text{trapez: } \kb{\tfrac{w\,l_k}{2}\Big(l_u-\tfrac{l_k}{2}\Big)}\ \text{kN}
$$

İki üçgen ve iki trapezin toplamı $w\,l_k\,l_u$, yani panelin bütün yüküdür. Bu **korunum** her dağıtımın denetimidir: hiçbir kN kaybolmaz, hiçbiri iki kez sayılmaz. Aşağıda kenarları ve yükü değiştir; 45° çizgileri, kiriş üstündeki şekiller ve toplam canlı güncellenir. $m$ 2'yi geçince plak tek doğrultulu olur ve kısa kenar kirişleri döşemeden pay almaz.

::: etkilesim doseme-dagilimi
{"lx": 5, "ly": 4, "w": 5}
:::

### Eşdeğer düzgün yükler

El hesabında üçgen ve trapezle uğraşmak yerine basit kirişte **aynı en büyük momenti** veren düzgün yük $q_{eM}$ ya da **aynı mesnet tepkisini** veren $q_{eV}$ kullanılır:

$$
\begin{aligned}
\text{üçgen:}\quad & \kutua{q_{eM}=\tfrac{w\,l_k}{3}},\qquad \kutub{q_{eV}=\tfrac{w\,l_k}{4}}\\[2pt]
\text{trapez:}\quad & \kutua{q_{eM}=\tfrac{w\,l_k}{2}\Big(1-\tfrac{1}{3m^2}\Big)},\qquad \kutub{q_{eV}=\tfrac{w\,l_k}{2}\Big(1-\tfrac{1}{2m}\Big)}
\end{aligned}
$$

::: not TS 500 bu formülleri vermez
Eşdeğer yükler yönetmelik kuralı değil, basit kiriş statiğinden türetilmiş **el hesabı kısayollarıdır**. Moment eşdeğeri ile kesme eşdeğeri farklıdır; ikisi de yalnız iki ucu basit mesnetli kiriş için kesindir. Sonlu eleman modelinde kısayola gerek yoktur: `yapi` motoru gerçek üçgen ve trapezi parçalı doğrusal yayılı yük olarak elemana verir ($q_1,q_2,x_1,x_2$ kayıtları), eşdeğer düğüm yüklerini Gauss integrasyonuyla kesin alır.
:::

## Kirişten kolona, kolondan temele

Bir kirişin toplam yükü $W$ döşeme payı, duvar, öz ağırlık ve varsa ek yüklerin toplamıdır. El hesabında basit kiriş varsayılır: her uca $R=W/2$ gider, açıklık momenti $q_{eM}L^2/8$ olur. Sonlu eleman modelinde kiriş kolonlara **ankastre** bağlı sürekli bir çerçeve parçasıdır; uç kesmeleri $W/2$'den sapar ve uçlarda negatif moment doğar. İki uç kesmesinin toplamı yine $W$'dir; değişen yalnız paylaşımdır.

Kolon eksenel kuvveti kat kat birikir: $N_k=N_{k+1}+\sum V_{\text{kiriş uçları}}+G_{\text{kolon}}$. El hesabı için **yük alanı** (tributary area) yöntemi kullanılır: kolon, çevresindeki panellerin çeyreklerini ve komşu kirişlerin yarısını taşır.

$$
\kutub{N_{\text{trib}}}=\sum_{\text{kat}}\Big[(g+q)\,A_{\text{trib}}+\sum_{\text{kiriş}}\tfrac{(g_{\text{öz}}+g_{\text{duvar}})\,L}{2}+G_{\text{kolon}}\Big],\qquad
A_{\text{trib}}=\frac{l_{x1}+l_{x2}}{2}\cdot\frac{l_{y1}+l_{y2}}{2}
$$

Sonlu eleman sonucu $N_{\text{FE}}$ bundan birkaç yüzde sapar: sürekli kirişin iç mesnedine dış mesnetten daha çok yük gelir, bu yüzden iç kolonlar yük alanı tahmininden biraz **fazla**, köşe kolonlar biraz **az** yüklenir. Aşağıda kat sayısı, kat yükü ve aks aralıklarıyla oyna; kolon şeridinde kat kat gelen oklar ve kümülatif $N$ büyür.

::: etkilesim kolon-birikimi
{"kat": 4, "g": 5, "q": 2, "lx": 5, "ly": 4, "konum": "ic"}
:::

::: not Hareketli yük azaltması
TS 498:2021 md. 16 Çizelge 7, üçten çok kat taşıyan kolon ve temellerde hareketli yük toplamının $\beta$ ile çarpılmasına izin verir: konut ve büroda 4 kat için 0.95, 5 kat 0.88, 6 kat 0.80 … en az 0.60. Döşeme ve kiriş hesabında azaltma yoktur; depo ve ağır atölyede hiç yapılmaz. Yukarıdaki çizim $N_Q$ sütununda bu katsayıyı gösterir.
:::

### Temel taban basıncı

Kolon tabanındaki servis yükü $N=N_G+N_Q$ ve momentler $M_X$, $M_Y$ temel tabanına doğrusal basınç dağılımıyla iner:

$$
\kutuc{\sigma_{\max,\min}=\frac{N}{B\,L}\pm\frac{6M_X}{B\,L^2}\pm\frac{6M_Y}{L\,B^2}}\le q_{em},
\qquad
e_X=\frac{M_Y}{N}\le\frac{B}{6},\quad e_Y=\frac{M_X}{N}\le\frac{L}{6}
$$

Bileşke **çekirdek** (kern) içinde, yani $e\le B/6$ ise taban tümüyle basınçtadır ve formül geçerlidir; dışına çıkarsa bir kenar kalkar ve dağılım yeniden hesaplanır. $q_{em}$ zemin raporundaki **emniyetli taşıma gücüdür**; oran $\sigma_{\max}/q_{em}$ "talep/kapasite" (D/C) olarak yazılır.

## Korunum: beş sayı

Doğrusal statikte düşey yük hiçbir durakta kaybolmaz. Motor bunu beş sayıyla sağlar ve her biri aynı olmalıdır:

$$
\underbrace{\sum G_{\text{döşeme}}+\sum G_{\text{duvar}}+\sum G_{\text{kiriş öz}}+\sum G_{\text{kolon öz}}}_{\text{yük dökümü}}
=\sum_{\text{kiriş}} W
=\sum_{\text{taban}} N_{\text{kolon}}
=\sum R_{\text{temel}}
$$

Şablon bina için bu sayı $360+245.7+135+144=\kc{884.7}$ kN'dur (G) ve 144 kN'dur (Q). Beş sayıdan biri tutmazsa ya bir yük iki kez girilmiş ya bir kiriş döşemeden pay almamış ya da bir mesnet eksiktir.

::: hata q_eM ile kesme hesaplamak
$q_{eM}$ yalnız açıklık momentini tutturur; onunla $R=q_{eM}L/2$ yazarsan trapez kirişte tepkiyi yüzde 20–30 fazla bulursun (5 m kirişte 19.7 yerine 15 kN). Kesme ve tepki için $q_{eV}$, moment için $q_{eM}$ kullan; sonlu elemanda ikisine de gerek yok, gerçek şekli ver.
:::

::: hata Döşeme yükünü iki kez saymak
Döşeme payını kirişe verdikten sonra aynı alanı kolonun yük alanına da eklersen ya da plak öz ağırlığını hem $g$ içinde hem kiriş öz ağırlığında sayarsan toplam yük şişer. Döşeme yükü **yalnız bir yoldan** gider: plak → kiriş → kolon. Beş sayılık korunumu her modelde denetle; iki kez sayılan yük orada hemen görünür.
:::

::: hata Hareketli yükü azaltıp döşemeyi de azaltmak
Çizelge 7 azaltması yalnız üç kattan çok kat toplayan kolon, perde ve temel içindir. Kiriş ve döşemede uygulanmaz; TBDY 2018'in deprem kütlesi için kullandığı $n$ katsayısı (konut 0.3) başka bir kavramdır ve bununla karıştırılmaz.
:::

## Çözümlü örnekler

Örnekler `betonarme-2kat-3x2` şablonunu kullanır: akslar A–B–C (0, 5, 9 m) ve 1–2 (0, 4 m), iki kat 3 m, 40×40 kolon, 25×50 kiriş, 14 cm döşeme, 1. kat dış kirişlerinde 19 cm tuğla duvar, çatı dış kirişlerinde 1 m parapet. Aynı binayı düzenleyip çözmek için [Bina sayfasında aç](#bina/sablon/betonarme-2kat-3x2).

::: ornek Döşeme yükü: g ve q
D1 paneli 4×5 m, plak 14 cm, kaplama + sıva $g_{\text{ek}}=1.5$ kN/m², kullanım konut. $g$, $q$ ve panelin toplam yüklerini bul.
--- ipucu
Plak öz ağırlığı $25\cdot0.14$; $q$ TS 498:2021 Çizelge 6 satır 2.
--- cevap
$$
\kutua{g}=25\cdot0.14+1.5=3.5+1.5=\kutua{5.0}\ \text{kN/m}^2,\qquad
\kutub{q}=\kutub{2.0}\ \text{kN/m}^2\ (\text{Çizelge 6, satır 2})
$$
$$
W_G=g\,l_k\,l_u=5\cdot4\cdot5=\kc{100}\ \text{kN},\qquad W_Q=2\cdot20=\kc{40}\ \text{kN}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))
r
--- kontrol
r.veri["yukler"]["dosemeler"][0]["g"] == 5 and r.veri["yukler"]["dosemeler"][0]["q"] == 2 and r.veri["yukler"]["dosemeler"][0]["G_toplam"] == 100 and "Çizelge 6" in r.veri["yukler"]["dosemeler"][0]["q_kaynak"]
--- yorum
Motor $q$'yu kütüphaneden kaynak maddesiyle çeker (`q_kaynak`); her kütüphane değerinde `dogrulandi` alanı vardır. Çatı katı "zaman zaman kullanılan düz çatı" sınıfındadır: aynı satır, yine 2.0 kN/m².
:::

::: ornek 45° kuralı: D1 panelinin kirişlere payı
D1 paneli ($l_k=4$, $l_u=5$, $g=5$ kN/m²) için döşeme tipini, tepe yükünü, kenar kirişlerine giden şekilleri, $q_{eM}$ ve $q_{eV}$ değerlerini bul; korunumu denetle.
--- ipucu
$m=5/4=1.25\le2$: çift doğrultulu. Tepe $p=g\,l_k/2$; trapez formülünde $m^2=1.5625$.
--- cevap
$$
m=\frac{5}{4}=\kutua{1.25}\le2,\qquad p=\frac{5\cdot4}{2}=\kutua{10}\ \text{kN/m}
$$
Kısa kenar kirişleri K5 ve K6 (4 m) **üçgen**, uzun kenar kirişleri K1 ve K3 (5 m) **trapez** alır:
$$
\begin{aligned}
\text{üçgen:}\quad & \ka{q_{eM}}=\tfrac{5\cdot4}{3}=\ka{6.67},\quad \kb{q_{eV}}=\tfrac{5\cdot4}{4}=\kb{5.0}\\
& \text{pay } \tfrac{5\cdot4^2}{4}=\kc{20}\ \text{kN}\\[2pt]
\text{trapez:}\quad & \ka{q_{eM}}=10\Big(1-\tfrac{1}{3\cdot1.5625}\Big)=\ka{7.87}\\
& \kb{q_{eV}}=10\Big(1-\tfrac{1}{2.5}\Big)=\kb{6.0},\quad \text{pay } 10\,(5-2)=\kc{30}\ \text{kN}
\end{aligned}
$$
Korunum: $20+20+30+30=\kutuc{100}=5\cdot4\cdot5$ ✓
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))
r
--- kontrol
r.veri["yukler"]["dosemeler"][0]["m"] == 1.25 and r.veri["yukler"]["dosemeler"][0]["tip"] == "cift" and abs(sum(p["toplam_G"] for p in r.veri["yukler"]["dosemeler"][0]["paylar"]) - 100) < 1e-9 and abs(r.veri["yukler"]["dosemeler"][0]["paylar"][0]["q_eM_g"] - 7.8667) < 1e-3 and r.veri["yukler"]["dosemeler"][0]["paylar"][0]["sekil"] == "trapez" and r.veri["yukler"]["dosemeler"][0]["paylar"][2]["sekil"] == "ucgen"
--- yorum
`paylar` listesinde her kenar kirişi için `sekil`, `tepe_g`, `q_eM_g`, `q_eV_g` ve `toplam_G` bulunur; `parcalar_birim` ise motora giden parçalı yükün birim tepe için koordinatlarıdır: $[0,2,0,1],[2,3,1,1],[3,5,1,0]$ trapezin rampaları ve platosudur. D2 paneli karedir ($m=1$): dört kenara da üçgen.
:::

::: ornek Trapez mi, eşdeğer düzgün yük mü? Basit kirişte karşılaştırma
5 m basit kirişe tepesi 10 kN/m, rampaları 2 m olan trapez yük geliyor. Aynı kirişi $q_{eM}=118/15\approx7.87$ kN/m ve $q_{eV}=6$ kN/m düzgün yüklerle de çöz; en büyük momenti ve tepkileri karşılaştır.
--- ipucu
Trapezin bileşkesi $10\,(5-2)=30$ kN, $R=15$. Orta moment: $15\cdot2.5-10\cdot(2.5-\tfrac{4}{3})-5\cdot0.25$.
--- cevap
$$
\begin{aligned}
\text{trapez:}\quad & R=\kb{15}\ \text{kN}\\
& M_{\text{orta}}=37.5-11.67-1.25=\ka{24.58}\ \text{kN·m}\\[2pt]
q_{eM}=7.87:\quad & M=\tfrac{7.87\cdot25}{8}=\ka{24.58}\ \checkmark\\
& R=\tfrac{7.87\cdot5}{2}=\ksil{19.67}\ \text{kN}\ (\text{yüzde }31\text{ fazla})\\[2pt]
q_{eV}=6:\quad & R=\tfrac{6\cdot5}{2}=\kb{15}\ \checkmark\\
& M=\tfrac{6\cdot25}{8}=\ksil{18.75}\ \text{kN·m}\ (\text{yüzde }24\text{ eksik})
\end{aligned}
$$
--- kod
kiris = {"tip": "kiris", "dugumler": [{"no": 1, "x": 0}, {"no": 2, "x": 5}], "elemanlar": [{"no": 1, "dugumler": [1, 2], "E": "32e6", "I": "0.0026"}], "mesnetler": [{"dugum": 1, "uy": True}, {"dugum": 2, "uy": True}], "yukler": []}
trapez = dict(kiris, yayili=[{"eleman": 1, "q1": 0, "q2": -10, "x1": 0, "x2": 2}, {"eleman": 1, "q": -10, "x1": 2, "x2": 3}, {"eleman": 1, "q1": -10, "q2": 0, "x1": 3, "x2": 5}])
moment = dict(kiris, yayili=[{"eleman": 1, "q": "-118/15"}])
kesme = dict(kiris, yayili=[{"eleman": 1, "q": -6}])
se.se_coz(trapez), se.se_coz(moment), se.se_coz(kesme)
--- kontrol
abs(max(r[0].veri["elemanlar"][0]["diyagram"]["M"]) - max(r[1].veri["elemanlar"][0]["diyagram"]["M"])) < 1e-9 and abs(max(r[0].veri["elemanlar"][0]["diyagram"]["M"]) - 24.5833333) < 1e-6 and abs(r[0].veri["tepkiler"][0]["Fy"] - r[2].veri["tepkiler"][0]["Fy"]) < 1e-9 and abs(r[1].veri["tepkiler"][0]["Fy"] - 19.6667) < 1e-3
--- yorum
Moment eşdeğeri momenti, kesme eşdeğeri tepkiyi kesin tutturdu; hiçbiri ikisini birden tutturmaz. Sehim de farklıdır: trapezde $0.466$ mm, $q_{eM}$ ile $0.492$ mm. Sonlu elemanda `yayili` kayıtlarına $q_1,q_2,x_1,x_2$ ile gerçek şekli ver; kısayola gerek kalmaz.
:::

::: ornek Kiriş K1: yük dökümü, el hesabı ve FE uç kesmeleri
1. kattaki K1 kirişi (A1→B1, 5 m) D1'den trapez pay alır; üstünde 19 cm tuğla duvar ($h_{\text{net}}=2.5$ m) vardır. $G$ dökümünü, basit kiriş tepkisini ve sonlu eleman uç kesmelerini bul.
--- ipucu
Döşeme payı 30 kN; duvar $2.70\cdot2.5=6.75$ kN/m; öz $0.25\cdot(0.50-0.14)\cdot25=2.25$ kN/m (döşeme içindeki kısım plakta sayıldı).
--- cevap
$$
\begin{aligned}
W_G&=\underbrace{30}_{\text{döşeme}}+\underbrace{6.75\cdot5}_{33.75\ \text{duvar}}+\underbrace{2.25\cdot5}_{11.25\ \text{öz}}=\kutua{75.0}\ \text{kN}\\
R_{\text{el}}&=\frac{W_G}{2}=\kutub{37.5}\ \text{kN}
\end{aligned}
$$
Sonlu eleman (eleman 13, G durumu): $V_{A1}=\kc{35.90}$, $V_{B1}=\kc{39.10}$ kN; toplam $75.0$ ✓. B1 iç kolondur ve kirişin öteki açıklığıyla süreklilik kurar; iç uca daha çok yük gider. Açıklık momenti FE'de $21.2$ kN·m, uç momentleri $-27.5$ ve $-35.5$ kN·m; basit kiriş tahmini $q_{eM}L^2/8=16.87\cdot25/8=52.7$ kN·m idi.
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))
r
--- kontrol
abs(r.veri["yukler"]["kirisler"][0]["G"]["toplam_kN"] - 75.0) < 1e-9 and abs(r.veri["yukler"]["kirisler"][0]["el_hesabi"]["R_G"] - 37.5) < 1e-9 and abs(next(e for e in r.veri["durumlar"]["G"]["elemanlar"] if e["no"] == 13)["uc_kuvvetleri"][1] - 35.901) < 1e-3 and abs(next(e for e in r.veri["durumlar"]["G"]["elemanlar"] if e["no"] == 13)["uc_kuvvetleri"][1] + next(e for e in r.veri["durumlar"]["G"]["elemanlar"] if e["no"] == 13)["uc_kuvvetleri"][7] - 75.0) < 1e-6
--- yorum
Ankastre uçlu sürekli kirişte açıklık momenti basit kiriş değerinin yarısından azdır; fark uç momentlerine gitmiştir. Toplam statik moment ($M_{\text{açıklık}}+\overline{M}_{\text{uç}}\approx21.2+31.5=52.7$) yine $q_{eM}L^2/8$'e eşittir: uç mesnetleri momenti yok etmez, paylaştırır.
:::

::: ornek Kolon B1: yük alanı ile FE birikimi
İç kolon B1'in çatı katındaki (kat 2) payını yük alanı yöntemiyle hesapla ve sonlu eleman eksenel kuvvetiyle karşılaştır; 1. kat kümülatif değerini de oku.
--- ipucu
B1 köşesine D3 (4×5) ve D4 (4×4) panellerinin çeyreği gelir: $A_{\text{trib}}=5+4=9$ m². Komşu kirişler K8 (5 m) ve K9 (4 m) çatı dış kirişidir, üstlerinde 1 m parapet ($2.70$ kN/m) vardır; K13 (4 m) duvarsız. Kiriş öz ağırlığı $2.25$ kN/m; kolon öz ağırlığı $25\cdot0.16\cdot3=12$ kN.
--- cevap
$$
\begin{aligned}
N_{\text{trib},G}&=\underbrace{5\cdot9}_{45\ \text{döşeme}}+\underbrace{\tfrac{4.95\cdot5}{2}}_{12.375\ (\text{K8})}+\underbrace{\tfrac{4.95\cdot4}{2}}_{9.9\ (\text{K9})}\\
&\quad+\underbrace{\tfrac{2.25\cdot4}{2}}_{4.5\ (\text{K13})}+\underbrace{12}_{\text{kolon}}=\kutub{83.78}\ \text{kN}\\[2pt]
N_{\text{FE},G}&=\kutuc{88.02}\ \text{kN}\quad(\text{fark }+5.2\text{ yüzde})\\
N_{\text{trib},Q}&=2\cdot9=18,\qquad N_{\text{FE},Q}=19.03\ \text{kN}
\end{aligned}
$$
1. katta kümülatif: $N_{\text{FE}}=193.76$ kN, yük alanı $185.78$ kN (fark $+4.3$ yüzde). Köşe kolon A1'de tersi: $133.32$ FE, $136.78$ yük alanı ($-2.6$ yüzde).
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))
r
--- kontrol
abs(next(k for k in r.veri["akis"]["kolonlar"] if k["no"] == 9)["N_trib_G"] - 83.775) < 1e-6 and abs(next(k for k in r.veri["akis"]["kolonlar"] if k["no"] == 9)["N_G"] - 88.019) < 1e-3 and next(k for k in r.veri["akis"]["kolonlar"] if k["no"] == 9)["A_trib"] == 9 and abs(next(k for k in r.veri["akis"]["kolonlar"] if k["no"] == 3)["N_kum_G"] - 193.763) < 1e-3 and next(k for k in r.veri["akis"]["kolonlar"] if k["no"] == 1)["fark_yuzde"] < 0 < next(k for k in r.veri["akis"]["kolonlar"] if k["no"] == 3)["fark_yuzde"]
--- yorum
`akis.kolonlar` her kolon için `N_G` (kat payı), `N_kum_G` (kümülatif), `N_trib_G` ve `fark_yuzde` verir. İç kolonun fazla, köşenin az yüklenmesi sürekli kirişin iç mesnet etkisidir; ön boyutlandırmada yük alanı yeter, kesin kuvvet için çerçeveyi çöz.
:::

::: ornek Temel A1: taban basıncı ve çekirdek
A1 kolonunun 1.6×1.6×0.6 m tekil temeline kolon tabanından servis yükü $N_G+N_Q=133.32+19.34=152.66$ kN, $M_X=-3.92$, $M_Y=6.22$ kN·m geliyor; temelin öz ağırlığı $25\cdot1.6\cdot1.6\cdot0.6=38.4$ kN de tabana iner; $q_{em}=200$ kN/m². $\sigma_{\max}$, $\sigma_{\min}$, dışmerkezlikleri ve D/C oranını bul.
--- ipucu
$N=152.66+38.4=191.06$ kN; $A=2.56$ m²; $BL^2=4.096$ m³. Dışmerkezlik $e_X=M_Y/N$, çekirdek $B/6=0.267$ m.
--- cevap
$$
\begin{aligned}
\frac{N}{BL}&=\frac{191.06}{2.56}=\ka{74.63}\\
\frac{6|M_X|}{BL^2}&=\frac{23.51}{4.096}=\kb{5.74},\qquad
\frac{6|M_Y|}{LB^2}=\frac{37.31}{4.096}=\kb{9.11}\\[2pt]
\sigma_{\max}&=74.63+5.74+9.11=\kutuc{89.48}\ \text{kN/m}^2\\
\sigma_{\min}&=74.63-5.74-9.11=\kutuc{59.78}\ \text{kN/m}^2\\[2pt]
e_X&=\frac{6.22}{191.06}=0.033\le\frac{1.6}{6}=0.267\ \checkmark,\qquad \frac{\sigma_{\max}}{q_{em}}=\kc{0.45}
\end{aligned}
$$
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))
r
--- kontrol
abs(r.veri["akis"]["temeller"][0]["sigma_max"] - 89.483) < 1e-3 and abs(r.veri["akis"]["temeller"][0]["sigma_min"] - 59.784) < 1e-3 and r.veri["akis"]["temeller"][0]["cekirdek_icinde"] and abs(r.veri["akis"]["temeller"][0]["DC"] - 0.447) < 1e-3 and abs(r.veri["akis"]["temeller"][0]["N_servis"] - (r.veri["akis"]["temeller"][0]["N_G"] + r.veri["akis"]["temeller"][0]["N_Q"] + r.veri["akis"]["temeller"][0]["N_temel"])) < 1e-6
--- yorum
Taban tümüyle basınçta, D/C 0.45: temel rahat. Temelin öz ağırlığı eksenel yükü artırır ama momenti değiştirmez; dolgu ağırlığı bu araçta ihmal edilir. Momentler yalnız düşey yükten geliyor (çerçeve etkisi); deprem birleşiminde $M$ büyür, $e$ çekirdeği aşabilir ve dağılım üçgene döner. `temeller` listesi `N_servis`, `N_temel`, `e_X`, `e_Y`, `DC` ve `cekirdek_icinde` alanlarını taşır.
:::

::: ornek Korunum: beş sayı
Şablon bina için G yük dökümünü (döşeme, duvar, kiriş öz, kolon öz) topla; kolon tabanlarındaki $\sum N$ ve temel tepkilerinin $\sum F_Z$ değeriyle karşılaştır. Q için de yap.
--- ipucu
Dört panel, on dört kiriş (toplam 60 m, öz $2.25$ kN/m), on iki kolon. Döşeme $2\cdot(100+80)$; duvar: 26 m dış kiriş, 1. katta $6.75$, çatıda parapet $2.70$ kN/m; kolon öz $12\cdot12$.
--- cevap
$$
\begin{aligned}
G:\quad & \underbrace{360}_{\text{döşeme}}+\underbrace{245.7}_{\text{duvar}}+\underbrace{135}_{\text{kiriş öz}}+\underbrace{144}_{\text{kolon öz}}=\kutuc{884.7}\\
& =\sum N_{\text{taban}}=\sum R_{\text{temel}}=884.7\ \checkmark\\[2pt]
Q:\quad & 2\cdot(40+32)=\kutuc{144}=\sum N_{\text{taban}}=\sum R_{\text{temel}}\ \checkmark
\end{aligned}
$$
Kat 1: $G=495.0$ (duvarlı), çatı: $G=389.7$ kN (parapet); her katta $Q=72$ kN; toplam servis yükü $1028.7$ kN.
--- kod
r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))
r
--- kontrol
abs(r.veri["akis"]["korunum"]["G"]["toplam"] - 884.7) < 1e-6 and abs(r.veri["akis"]["korunum"]["G"]["kolon_taban"] - 884.7) < 1e-6 and abs(r.veri["akis"]["korunum"]["G"]["temel"] - 884.7) < 1e-6 and abs(r.veri["akis"]["korunum"]["Q"]["temel"] - 144) < 1e-6 and abs(sum(t["FZ"] for t in r.veri["durumlar"]["G"]["tepkiler"]) - 884.7) < 1e-6
--- yorum
Korunum, modelin değil yük girişinin denetimidir: $\mathbf{K}\mathbf{u}=\mathbf{F}$ dengeyi zaten sağlar, ama $\mathbf{F}$'ye yanlış yük yazıldıysa denge yanlış yükü doğrular. Beş sayı tutuyorsa döşemeden temele giden yolda ne bir kN kaybolmuş ne bir kN iki kez sayılmıştır.
:::

::: ornek Tek doğrultulu döşeme: 3×8 m derslik
Bir derslik paneli $l_k=3$, $l_u=8$ m, plak 15 cm, $g_{\text{ek}}=1.5$ kN/m². $m$'yi, kirişlere giden yükleri ve korunumu bul.
--- ipucu
$m=8/3>2$: tek doğrultulu. Yük yalnız uzun kenar kirişlerine, düzgün $w\,l_k/2$ olarak gider; $q$ Çizelge 6 satır 3.
--- cevap
$$
g=25\cdot0.15+1.5=\kutua{5.25},\quad q=\kutub{3.5}\ \text{kN/m}^2,\qquad m=\frac{8}{3}=\kutua{2.67}>2
$$
$$
\begin{aligned}
\text{uzun kenar (8 m):}\quad & q_G=\frac{5.25\cdot3}{2}=\kc{7.875},\quad q_Q=\frac{3.5\cdot3}{2}=\kc{5.25}\ \text{kN/m}\\
\text{kısa kenar (3 m):}\quad & \ksil{0}
\end{aligned}
$$
Korunum: $2\cdot7.875\cdot8=126=5.25\cdot24$ ✓. Tek doğrultulu plakta $q_{eM}=q_{eV}=w\,l_k/2$: şekil zaten düzgündür.
--- yorum
Kısa kenar kirişleri döşemeden pay almasa da öz ağırlık ve duvar yükünü taşır; "yük yok" demek "kiriş yok" demek değildir. Plak kısa doğrultuda bir sürekli kiriş şeridi gibi çalışır; TS 500 md. 11.2.2 moment katsayıları ($p_dl^2/11$, $/15$ …) bu şerit içindir.
:::

::: ornek Kullanım sınıfını seçmek
Aynı katta 12 m² bir balkon ve bir derslik var. TS 498:2021'e göre hareketli yükleri yaz; balkon için 10 m² kuralını uygula.
--- ipucu
Çizelge 6 satır 3 ve satır 4; balkon ekine dikkat.
--- cevap
$$
q_{\text{derslik}}=\kutub{3.5}\ \text{kN/m}^2\ (\text{satır }3),\qquad
q_{\text{balkon}}=5.0+0.35\,(12-10)=\kutub{5.7}\ \text{kN/m}^2\ (\text{satır }4,\ A>10\ \text{m}^2)
$$
--- yorum
Balkon kuralı TS 498:2021'in 1997 baskısına göre tek sayısal değişikliğidir. Kütüphanede `balkon` kaydı 5.0 ile ≤ 10 m² için verilir; büyük balkonda ek yükü `ek_yukler` ile döşemeye girmelisin.
:::

::: muhendislik Yapı analiz programlarında aynı yol
Yaygın yapı analiz programlarında döşeme yükünü kirişe aktarmanın karşılığı alan yükünü çerçeveye dağıtma seçeneğidir ("uniform to frame": kabuğa alan yükü verip tek ya da iki doğrultuda aktarımı seçmek): program 45° kuralıyla aynı üçgen ve trapezleri üretir ve kirişe parçalı yük olarak yazar; bu derste motorun yaptığı da budur. Yük durumları ("load pattern") G ve Q olarak ayrı tanımlanır, kombinasyon ("load combination") sonradan toplanır; bir sonraki derste bunu ayrıntılı göreceğiz.

Tarihi yığma köprüde yük yolu yine vardır ama kiriş–kolon yerine **tonoz ve ayaklar** üzerinden geçer: dolgu ağırlığı tonoza, tonoz itkisi ayaklara ve temele iner. OMA ile ölçülen frekanslar bu yolun rijitliğine duyarlıdır; dolgu kütlesi $G$'nin büyük parçasıdır ve model güncellemede ilk sorgulanacak sayıdır.
:::

::: ozet Özet
- TS 498:2021 yürürlüktedir (1997 kalktı): hareketli yük md. 15.1 Çizelge 6, azaltma md. 16 Çizelge 7; birim ağırlıklar TS ISO 9194. $g=h\gamma_{ba}+g_{\text{ek}}$, duvar $g_d h_{\text{net}}$ kN/m, öz $\gamma b (h-t_{\text{döşeme}})$ (döşeme içindeki kısım plakta sayılır).
- $m=l_u/l_k\le2$ çift doğrultulu: TS 500 md. 11.4.3 45° kuralı, kısa kenara üçgen, uzun kenara trapez, tepe $p=wl_k/2$; $m>2$ tek doğrultulu: uzun kenarlara düzgün $wl_k/2$. Korunum $\sum=wl_kl_u$.
- Eşdeğer düzgün yükler yalnız el hesabı içindir: üçgen $q_{eM}=wl_k/3$, $q_{eV}=wl_k/4$; trapez $q_{eM}=\tfrac{wl_k}{2}(1-\tfrac{1}{3m^2})$, $q_{eV}=\tfrac{wl_k}{2}(1-\tfrac{1}{2m})$. FE'ye gerçek şekil gider.
- Kiriş: $W$ dökümü, el hesabı $R=W/2$; FE uç kesmeleri sürekliliğe göre sapar, toplamı $W$. Kolon: $N_k=N_{k+1}+\sum V+G_{\text{kolon}}$; yük alanı iç kolonda eksik, köşede fazla tahmin eder.
- Temel: $\sigma=N/BL\pm6M_X/BL^2\pm6M_Y/LB^2\le q_{em}$, çekirdek $e\le B/6$. Korunum: döküm $=\sum W=\sum N_{\text{taban}}=\sum R_{\text{temel}}$.
:::

## Alıştırma

Döşeme payı hesabını pekiştir: verilen kenarlar ve yükten tepe değerini, üçgen ya da trapez için $q_{eM}$'i bul.

::: alistirma doseme-esdeger
{"zorluk": 2}
:::

::: alistirma doseme-esdeger
{"zorluk": 3}
:::
