# Ders biçimi (`dersler/*.md`)

Bu dosya ders kaynaklarının sözleşmesidir. `ders_derle.py` dersleri bu kurallara göre okur, denetler ve
`docs/dersler.json` dosyasını üretir. Bu dosya ile adı `_` ile başlayan dosyalar ders sayılmaz.

Denetim: `python ders_derle.py --denetle` (biçim) ve `pytest testler/test_dersler.py` (örnek kodları).
Etkileşimleri tek başına görmek için: `docs/galeri.html` ya da `docs/galeri.html?ad=carpim-gezgini`.

---

## 1. Dosya adı ve sıra

- Ad: `NN-kisa-ad.md`. `NN` iki basamaklı ders numarasıdır ve benzersizdir.
- `01`–`08` matris bölümü, `11`–`20` sonlu elemanlar bölümü, `21`–`29` yapı analizi bölümüdür. Sıra numaradan gelir.
- Kodlama UTF-8. Satır sonu LF ya da CRLF olabilir.

| No | Dosya | Konu |
|---|---|---|
| 01 | `01-matris-nedir.md` | matris, boyut, eleman indisi, vektör, özel matrisler |
| 02 | `02-toplama-skaler.md` | toplama, çıkarma, skalerle çarpma, özellikler |
| 03 | `03-carpim.md` | satır × sütun, boyut uyumu, değişmezlik yok, matris × vektör |
| 04 | `04-transpoz-simetri.md` | devrik, $(AB)^T=B^TA^T$, simetri, $\mathbf{x}^T\mathbf{K}\mathbf{x}$ |
| 05 | `05-determinant.md` | 2×2, Sarrus, kofaktör açılımı, alan anlamı, tekillik |
| 06 | `06-ters-matris.md` | 2×2 formülü, Gauss–Jordan $[A\,|\,I]$, tekil matris |
| 07 | `07-dogrusal-sistemler.md` | $A\mathbf{x}=\mathbf{b}$, Gauss eliminasyonu, Cramer, rank ve çözüm sayısı |
| 08 | `08-ozdeger.md` | $A\mathbf{x}=\lambda\mathbf{x}$, karakteristik denklem, $K\boldsymbol\phi=\omega^2M\boldsymbol\phi$ |
| 11 | `11-yay-sistemleri.md` | yay elemanı, düğüm, serbestlik, seri ve paralel yaylar |
| 12 | `12-cubuk-eleman.md` | eksenel çubuk, şekil fonksiyonları, $k=EA/L$, gerilme |
| 13 | `13-kafes-donusum.md` | koordinat dönüşümü, $c$ ve $s$, 2B kafes eleman matrisi |
| 14 | `14-birlestirme.md` | serbestlik numaralama, birleştirme, bant yapısı |
| 15 | `15-sinir-kosullari.md` | $K_{ff}$, $K_{fs}$ bölümleri, çözüm, tepkiler, eleman kuvvetleri |
| 16 | `16-kiris-eleman.md` | Hermite şekil fonksiyonları, 4×4 kiriş matrisi, eşdeğer düğüm yükleri |
| 17 | `17-cerceve.md` | 6×6 çerçeve elemanı, dönüşüm, N, V, M diyagramları |
| 18 | `18-titresim.md` | kütle matrisi, serbest titreşim, modlar, OMA bağlantısı |
| 19 | `19-uzay-yapilar.md` | uzay kafes $c_x, c_y, c_z$ ve 6×6; uzay çerçeve 12×12, $\boldsymbol\lambda$ ve yerel eksen kuralı, burulma, kiriş ızgarası |
| 20 | `20-temel-sistemleri.md` | elastik mesnet $K_{ii}\mathrel{+}=k$, Winkler zemini $(k_sL/420)[\ldots]$ ve $\beta$, mesnet çökmesi $K_{ff}u_f=F_f-K_{fs}u_s$, kolon–kiriş–temel sistemi |
| 21 | `21-yuk-akisi.md` | yük akışı: TS 498:2021 yükleri, $m=l_u/l_k$, TS 500 md. 11.4.3 45° kuralı (üçgen/trapez, tepe $wl_k/2$), $q_{eM}$, $q_{eV}$, kiriş tepkileri el ↔ FE, kolon birikimi ve yük alanı, $\sigma=N/A\pm6M/BL^2$, $e\le B/6$, korunum |
| 22 | `22-yuk-durumlari-kombinasyonlar.md` | yük durumları G, Q, S, W, E; load pattern → case → combination → envelope zinciri; süperpozisyon; TS 500 md. 6.2.6, TBDY 4.4.4 (4.9–4.12), ÇYTHYE 5.3.1/5.3.2, TBDY 9.2.5; yön ve işaret çoğaltımı; zarf, belirleyen kombinasyon, kolonda eş zamanlı $(N,M)$; rüzgâr kat kuvveti ve kar |
| 23 | `23-tbdy-esdeger-deprem.md` | TBDY 2018 eşdeğer deprem yükü: DD-1…4, $S_S$, $S_1$, $F_S$, $F_1$ ara değeri, $S_{ae}(T)$, BKS/I, DTS, BYS, $R$, $D$, $R_a$, $w_i=w_G+nw_Q$, $T_{pA}$ ve Rayleigh, $V_{tE}$, $\Delta F_{NE}$, $F_{iE}$, ±%5 dışmerkezlik, $\eta_{bi}$, göreli kat ötelemesi, $\theta_{II}$, Tablo 4.2 ve 4.4 |
| 24 | `24-ts500-kiris-kolon.md` | TS 500: $\gamma_{mc}$, $\gamma_{ms}$, $f_{cd}$, $f_{ctd}$, $f_{yd}$; md. 7.1 ve eşdeğer blok ($k_1$, Çizelge 7.1); $a$ ve $A_s$ türetimi, $\rho_{min}$, $\rho_b$, $\rho_{max}$, TBDY 7.4.2.4; çift donatı, $M_r$, D/C, çubuk seçimi; $V_{cr}$, $V_c$, $V_{max}$, $A_{sw}/s$; kolon N–M eğrisi, $N_0$, $N_t$, dengeli nokta, $e_{min}$ (Denk. 6.16), $0.9f_{cd}A_c$, $0.40f_{ck}A_c$, eş zamanlı noktalar, md. 7.6.2.6 ve Bresler |
| 25 | `25-cythye-celik.md` | ÇYTHYE 2018: YDKT/GKT, Tablo 2.1A, Tablo 5.1A/5.1B; $M_p$, $L_p$, $L_r$, $C_b$, YBB üç bölge (Denk. 9.1–9.6, 9.9); $KL/i$, $F_e$, $F_{cr}$ ve $4.71\sqrt{E/F_y}$, burulmalı burkulma; $C_{v1}$, $\phi_v$; çekme; Denk. 11.1a/b; $K$ seçimi ve $K=1$ varsayımı; depo şablonu |
| 26 | `26-bina-analizi-program-akisi.md` | yapı analiz programlarının iş akışı ve bu uygulama: aks–kat, düğüm ve eleman üretimi, yerel eksenler (1-2-3 ↔ $x'y'z'$, işaretler), rijit diyafram ($\mathbf T_i$, $\mathbf K=\sum k_i\mathbf T_i^T\mathbf T_i$, rijitlik merkezi), yük → durum → kombinasyon → zarf → tasarım, D/C bantları, sık zorluklar, denge sağlaması, sık hatalar |

## 2. Ön bilgi

Dosya `---` satırıyla başlar ve ikinci `---` satırıyla biten ön bilgiyle devam eder:

```text
---
baslik: Matris çarpımı
bolum: matris
ozet: Satır × sütun kuralı, boyut uyumu ve sıranın önemi.
sure: 25
---
```

| Alan | Zorunlu | Anlamı |
|---|---|---|
| `baslik` | evet | Ders başlığı. Satır içi `$…$` olabilir. |
| `bolum` | evet | `matris`, `se` ya da `yapi` (numara aralığıyla uyumlu: 01–09, 10–20, 21 ve üstü) |
| `ozet` | evet | Tek cümle |
| `sure` | evet | Tahmini çalışma süresi, dakika, tam sayı |

## 3. Gövde

- Markdown (GFM) ve KaTeX. Satır içi matematik `$…$` tek satırda kalır. Blok matematik `$$` ile açılır, `$$` ile
  kapanır; açılış ve kapanış kendi satırında olabilir. `$$` sayısı çift olmalıdır.
- Başlıklar `##` ve `###`. `#` kullanılmaz; ders başlığı ön bilgiden gelir.
- `$` işareti yalnız matematik içindir. Para birimi gerekiyorsa `TL` yazılır.
- Ham HTML kullanılmaz. Tek istisna `::: sekil` ve `--- sekil` içindeki SVG'dir.
- Paragraflar kısa tutulur: en çok 4 cümle.

### 3.1 Görsel matematik

Çözümler yalnız yazıyla geçmez. Her adımda göz neye bakacağını renkten, kutudan ve oktan anlar.

| Araç | Yazım | Ne zaman |
|---|---|---|
| Renkli yazı | `\ka{a_{11}}`, `\kb{…}`, `\kc{…}`, `\ksil{…}` | Aynı renkteki parçalar birbirine karşılık gelir |
| Renkli kutu | `\kutua{…}`, `\kutub{…}`, `\kutuc{…}`, `\kutusil{…}` | Bir elemanı, bloğu ya da ara sonucu çerçevelemek |
| Parsel (blok) | `\left[\begin{array}{cc|c} … \\ \hline … \end{array}\right]` | $[A\,|\,\mathbf{b}]$, $[A\,|\,I]$, $K_{ff}$ ve $K_{fs}$ bölümleri |
| Kesik çizgi | `\hdashline` (array içinde) | İkincil bölme |
| Ayraç | `\underbrace{…}_{\text{ad}}`, `\overbrace{…}^{\text{ad}}` | Bir parçaya ad vermek |
| Ok | `\xrightarrow{R_2-3R_1}`, `\xrightarrow[\text{alt}]{\text{üst}}` | Satır işlemi, dönüşüm, adım |
| Hizalı adımlar | `\begin{aligned} … \end{aligned}` | Çok adımlı hesap |

Renklerin anlamı her derste aynıdır:

| Renk | Makro | Anlam |
|---|---|---|
| mavi | `a` | birinci girdi, satır, 1. eleman |
| turuncu | `b` | ikinci girdi, sütun, 2. eleman |
| yeşil | `c` | sonuç, üçüncü eleman |
| kırmızı | `sil` | silinen, sıfırlanan, hatalı |

Makrolar uygulamada renkli yazı ve renkli zeminli çerçeve olarak çizilir. Colab defterinde `\textcolor` ve
`\boxed` karşılıklarına çevrilir; bu yüzden makronun içine yalnız matematik yazılır.

Örnek:

```latex
$$
\begin{bmatrix} \ka{1} & \ka{2} \\ 3 & 4 \end{bmatrix}
\begin{bmatrix} \kb{5} & 6 \\ \kb{7} & 8 \end{bmatrix}
=
\begin{bmatrix} \kutuc{19} & 22 \\ 43 & 50 \end{bmatrix}
\qquad
\kc{19} = \ka{1}\cdot\kb{5} + \ka{2}\cdot\kb{7}
$$
```

Parsel örneği (genişletilmiş matris ve satır işlemi):

```latex
$$
\left[\begin{array}{cc|c} \kutua{2} & 1 & 5 \\ \ksil{6} & 4 & 18 \end{array}\right]
\xrightarrow{R_2 \,-\, 3R_1}
\left[\begin{array}{cc|c} 2 & 1 & 5 \\ \kc{0} & 1 & 3 \end{array}\right]
$$
```

## 4. Yönergeler

Yönerge satırı 0. sütunda `:::` ile başlar ve tek başına `:::` satırıyla kapanır. İç içe yönerge yoktur.
Kod çiti (```` ``` ````) içindeki satırlar yönerge sayılmaz.

### 4.1 `::: etkilesim <ad>`

Etkileşimli çizim. İçi boş ya da tek bir JSON nesnesidir (parametreler). `baslik` anahtarı başlığı değiştirir.
Ad, §6 kataloğunda olmalıdır. Matrisler metin olarak verilir: `"1 2; 3 4"`.

```text
::: etkilesim carpim-gezgini
{"A": "1 2; 3 4", "B": "5 6; 7 8", "baslik": "Sonuç hücresine dokun"}
:::
```

### 4.2 `::: alistirma <ad>`

Sınırsız rastgele soru üreten alıştırma. İçi boş ya da JSON (`zorluk`: 1, 2 ya da 3; bazılarında `boyut`).
Ad, §7 kataloğunda olmalıdır.

```text
::: alistirma determinant
{"zorluk": 2, "boyut": 3}
:::
```

### 4.3 `::: ornek <başlık>`

Çözümlü örnek. İlk `--- bölüm` satırına kadar olan kısım sorudur. Bölüm satırı tek başına `--- ad` biçimindedir.

| Bölüm | Zorunlu | İçerik |
|---|---|---|
| `ipucu` | hayır | Bir iki cümlelik yönlendirme |
| `cevap` | evet | Görsel çözüm: renkler, kutular, parseller, oklar, adım adım |
| `kod` | hayır | Aynı soruyu motorla çözen Python (§5) |
| `kontrol` | `kod` varsa evet | `r` üzerinde doğru ya da yanlış veren tek ifade |
| `yorum` | hayır | Sonucun anlamı, mühendislik bağlantısı |
| `sekil` | hayır | Sorunun altında gösterilen SVG (§4.5 kuralları) |

Uygulamadaki akış: soru ve şekil, sonra **İpucu**, **Cevabı göster**, **Adım adım çözüm**. Son düğme `kod`
bölümünü motorda çalıştırır ve ok şemalı anlatımı gösterir. Örnekler ders içinde 1'den başlayarak numaralanır.

```text
::: ornek 2×2 çarpım
$A=\begin{bmatrix}1&2\\3&4\end{bmatrix}$ ve $B=\begin{bmatrix}5&6\\7&8\end{bmatrix}$ için $AB$ nedir?
--- ipucu
Sonucun $(i,j)$ elemanı, $A$'nın $i$. satırı ile $B$'nin $j$. sütununun çarpımlarının toplamıdır.
--- cevap
$$
c_{11} = \ka{1}\cdot\kb{5} + \ka{2}\cdot\kb{7} = \kc{19}
$$
--- kod
mo.carp("1 2; 3 4", "5 6; 7 8")
--- kontrol
r.deger == sp.Matrix([[19, 22], [43, 50]])
--- yorum
$BA \ne AB$: sırayı değiştirip dene.
:::
```

### 4.4 Bilgi kutuları

`::: not|uyari|ipucu|tanim|ozet|hata|muhendislik [başlık]` … `:::`. İçerik markdown ve KaTeX'tir.
Başlık verilmezse varsayılanlar: Not, Dikkat, İpucu, Tanım, Özet, Sık yapılan hata, Mühendislikte.

### 4.5 `::: sekil <başlık>`

Statik çizim. İçerik ham SVG'dir; en çok 8000 karakter, `viewBox` zorunlu, genişlik yüzdeyle uyarlanır.

- Yasak: `<script>`, `<foreignObject>`, `<iframe>`, `<image>`, `<marker>`, `on…=` öznitelikleri, `javascript:`,
  dış bağlantı (`href="http…"`).
- Renkler değişkenle: `var(--sema-a,#3b82f6)`, `var(--sema-b,#f59e0b)`, `var(--sema-c,#10b981)`,
  `var(--sema-sil,#ef4444)`; zeminler `var(--sema-a-bg,rgba(59,130,246,.12))` gibi; nötr çizgi
  `var(--sema-cizgi,#94a3b8)`. Yazı `fill="currentColor"`, `font: 13px system-ui`.
- Ok gövdesi `<path class="ok" pathLength="1" …>`, ucu `<polyline class="ok-uc" …>`. Vurgu `<rect class="vurgu" rx="6" …>`.
- Koyu temada okunur kalması için sabit siyah ya da beyaz renk kullanılmaz.

## 5. Örnek kodu kuralları

- Ad alanında `mo` (matris_ogren), `sp` (sympy), varsa `se` (sonlu_eleman), `yapi` (bina analizi) ve `tasarim` (TS 500 / ÇYTHYE kesit tahkikleri) bulunur. `import` yazılmaz.
- Son satır bir ifadedir ve `Sonuc` ya da `Sonuc` listesi döndürür. Önceki satırlar atama olabilir.
- Belirlenimci ve hızlı: her örnek 2 saniyenin altında. Dosya, ağ ve rastgele sayı yok.
- `kontrol` tek satırlık ifadedir; `r` son ifadenin değeridir. Liste dönerse `r[-1]` kullanılır.
  Örnekler: `r.deger == sp.Matrix([[19, 22], [43, 50]])`, `r.deger == -2`,
  `abs(float(r.deger[0]) - 0.0125) < 1e-9`.
- Motor fonksiyonları (matrisler `"1 2; 3 4"` metni, liste ya da önceki `Sonuc` olabilir):

| Fonksiyon | Not |
|---|---|
| `mo.matris`, `mo.birim(n)`, `mo.sifir(m, n)` | kurulum |
| `mo.topla(A, B)`, `mo.cikar(A, B)`, `mo.skaler(k, A)` | |
| `mo.carp(A, B, …)` | ikiden çok matris olabilir |
| `mo.transpoz(A)`, `mo.iz(A)`, `mo.rank(A)` | |
| `mo.determinant(A, yontem="kofaktor"\|"eliminasyon")` | |
| `mo.ters(A, yontem="formul"\|"gauss")` | |
| `mo.coz(A, b, yontem="gauss"\|"cramer"\|"ters", bilinmeyen="x")` | |
| `mo.ozdeger(A, M=None, ozvektor=True)` | $M$ verilirse genelleştirilmiş |
| `mo.cubuk_eleman(E, A, L)`, `mo.kiris_eleman(E, I, L)`, `mo.kafes_eleman(E, A, L, aci_derece)` | sembol olabilir: `"E"` |
| `mo.birlestir([(k1, [1, 2]), (k2, [2, 3])], n)` | serbestlik numaraları 1'den başlar |
| `mo.sinir_kosulu(K, F, sabit=[1])` | tutulu serbestlikler 1'den başlar |

Sonlu eleman modeli çözen örnekler `se.se_coz(model)` kullanır; model §8.3 şemasındadır. Bina örnekleri
`yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"))` ile çözülür; `r.veri` alanları (`yukler.dosemeler[].paylar`,
`yukler.kirisler[].el_hesabi`, `durumlar.G.elemanlar`, `akis.kolonlar`, `akis.temeller`, `akis.korunum`, `kombinasyonlar`, `zarf.elemanlar`, `deprem`, `ruzgar`, `kar`) `kontrol`
ifadesinde okunur. Tek kombinasyonun tam kaydı `yapi.kombinasyon_kisa(r.ic, ad)` (sözlük; `kontrol` içinde çağrılabilir), çözümsüz deprem
önizlemesi `yapi.deprem_onizleme(bina)` (sözlük) ile alınır; son satır yine `Sonuc` olmalıdır (gerekirse `mo.transpoz([[...]])`).
Şablonlar: `yapi.bina_sablonlar()`.

Kesit tahkiki örnekleri `tasarim.*_anlatimli(...)` sarmalayıcılarını kullanır (dönüş `Sonuc`, `r.veri` sonuç sözlüğü; boyutlar m, kuvvet kN, moment kN·m, donatı cm²):
`kiris_egilme_anlatimli(Md, b, h, paspayi, beton="C30")` (`a_mm`, `As_gerekli_cm2`, `oneri`, `Mr_kNm`, `tek_donatili` …), `kiris_kesme_anlatimli(Vd, b, h, paspayi)`,
`kolon_etkilesim_anlatimli(b, h, As_toplam, paspayi)` (`N0_kN`, `Nt_kN`, `dengeli`), `kolon_kontrol_anlatimli(Nd, Mdx, Mdy, b, h, As_toplam, paspayi, adlar=[…])` (`noktalar[].dc_x`, Bresler alanları),
`kesit_sinifi_anlatimli(profil, Fy)`, `celik_egilme_anlatimli(profil, Fy, Lb, Cb=…)`, `celik_basinc_anlatimli(profil, Fy, KLx, KLy)`, `celik_kesme_anlatimli`, `celik_cekme_anlatimli`,
`celik_eleman_kontrol_anlatimli(profil, malzeme, L=…, kuvvetler=[{"ad", "N", "Mx", "My", "V"}])`; bina tasarım özeti `r.veri["tasarim"]` (`elemanlar`, `kritik_elemanlar`, `dc_dagilimi`, `en_buyuk_dc`).

## 6. Etkileşim kataloğu

Parametreler isteğe bağlıdır; verilmeyenler varsayılanı alır. Her çizim telefonda (375 px) yatay kaydırmasız
çalışır, dokunma ile kullanılır ve koyu temada okunur.

### 6.1 Matris (`docs/etkilesim_matris.js`)

| Ad | Parametreler | Ne gösterir, ne yapılır |
|---|---|---|
| `matris-gezgini` | `A`, `ad` | Hücreye dokun: satırı mavi, sütunu turuncu bant; $a_{ij}$ adı ve değeri; kenarlarda $m$ ve $n$ ok ölçüleri; satır ve sütun vektörü görünümü |
| `eleman-eleman` | `A`, `B`, `islem`: `topla`\|`cikar`\|`skaler`, `k` | Karşılıklı hücreler oklarla sonuca akar; adım adım ya da oynat |
| `carpim-gezgini` | `A`, `B` | Sonuç hücresine dokun: $A$ satırı ve $B$ sütunu yanar, terim çiftleri oklarla bağlanır, renkli toplam yazılır; iç boyutlar kutulu boyut denetimi; girdiler düzenlenebilir |
| `transpoz-aynasi` | `A` | Ana köşegen ayna çizgisi; elemanlar $(i,j)$'den $(j,i)$'ye kayar; kaydırıcı ile ara konum |
| `kofaktor-acilim` | `A` (3×3) | Açılım satırı ya da sütunu seçilir; her terimde satır ve sütun kırmızı çizilir, minör kutulanır, işaret satrancı gösterilir, toplam birikir |
| `donusum-2b` | `A` | Birim kare ve ızgara $A$ ile dönüşür; sütun vektörlerinin uçları sürüklenir; hazırlar: dönme, ölçek, kayma, yansıma, tekil; alan $=|\det A|$; $\det A=0$ olunca çizgiye çöker |
| `gauss-adim` | `A`, `b`, `mod`: `coz`\|`ters` | Tam kesirlerle eliminasyon; pivot kutusu, satır işlemi oku, sıfırlanan hücre kırmızıdan yeşile; `ters` kipinde $[A\,|\,I]$ üzerinde Gauss–Jordan; Geri, İleri, Baştan |
| `ozvektor-2b` | `A` | Birim vektör $\mathbf{x}$ döner, $A\mathbf{x}$ çizilir; ikisi aynı doğrultuya gelince özvektör ve $\lambda$ vurgulanır |

### 6.2 Sonlu elemanlar (`docs/etkilesim_se.js`)

| Ad | Parametreler | Ne gösterir, ne yapılır |
|---|---|---|
| `yay-sistemi` | `k`: [..], `P`, `duzen`: `seri`\|`paralel` | Yaylar zikzak çizilir; her elemanın 2×2 matrisi kendi renginde, global $K$ içinde düştüğü kutu aynı renkte; ortak düğüm hücresinde iki renk toplanır; kaydırıcılar ve yer değiştirme animasyonu |
| `cubuk-sekil` | `E`, `A`, `L`, `P` | Doğrusal $N_1$, $N_2$; $u_1$, $u_2$ kaydırıcıları ile şekil değiştirmiş çubuk; $k=EA/L$ ve gerilme |
| `kafes-aci` | `E`, `A`, `L`, `aci` | Açı kaydırıcısı ya da uç sürükleme; $c$, $s$ ve 4×4 matristeki $c^2$, $cs$, $s^2$ deseni renkli |
| `dof-haritasi` | `model` ya da `hazir`: `kafes-iki-cubuk`\|`kafes-uc-cubuk`\|`pratt`\|`portal`\|`kiris-iki-eleman` | Düğüm serbestlik numaraları; elemana dokununca $K$ içindeki satır ve sütunları yanar; mesnet aç ve kapa: $K_{ff}$, $K_{fs}$ bölümleri çizilir, yetersiz mesnette mekanizma uyarısı |
| `kiris-sekil` | `L` | Hermite $N_1$–$N_4$; $v_1$, $\theta_1$, $v_2$, $\theta_2$ kaydırıcıları; elastik eğri |
| `esdeger-yuk` | `q`, `L`, `P`, `a` | Yayılı ve tekil yükün eşdeğer düğüm kuvvetleri ve momentleri oklarla |
| `kiris-nvm` | `L`, `P`, `a`, `q`, `mesnet`: `basit`\|`konsol`\|`ankastre-mafsalli` | Kesme ve moment diyagramları; yük konumu sürüklenir; en büyük değerler |
| `cerceve-k` | `E`, `A`, `I`, `L`, `aci` | 6×6 eleman matrisi; eksenel terimler mavi, eğilme terimleri turuncu parsel; açı ile dönüşüm |
| `modal-titresim` | `m`: [..], `k`: [..] | Kat kütleleri ve yaylar; $\det(K-\omega^2M)=0$, $\omega$, $f$, $T$; mod şekli animasyonu; OMA ile ölçülen modlarla bağlantı notu |
| `uzay-kafes-cubuk` | `E`, `A`, `L`, `fi`, `psi` | Aksonometrik çubuk; yatay açı $\varphi$ ve düşey açı $\psi$ kaydırıcıları ya da uç sürükleme; $c_x$, $c_y$, $c_z$ bileşenleri renkli; 6×6 global matris $c_xc_y$ deseniyle, hücre tonu değerin büyüklüğüyle; katsayı ya da kN/m görünümü; hazır doğrultular |
| `uzay-cerceve-k` | `E`, `G`, `A`, `Iy`, `Iz`, `J`, `L`, `fi`, `psi`, `gorunum`: `yerel`\|`global` | 12×12 uzay çerçeve elemanı dört renkli parsel: eksenel (mavi), eğilme $x'y'$ (turuncu), eğilme $x'z'$ (yeşil), burulma (kırmızı); yerel ve global seçici; iki yön açısından $\boldsymbol\lambda$ (düşey elemanda $z'=Z$); eleman ve yerel eksenleri aksonometrik çizim |
| `elastik-mesnet` | `E`, `I`, `L`, `P`, `k1`, `k2`, `kr` | İki ucu düşey yaya oturan iki elemanlı kiriş: yaylar zikzak, sol uçtaki dönme yayı sarmal; elastik eğri ve yay kuvvetleri $-k\,u$ oklarla; 6×6 $K$'da eleman parselleri mavi ve turuncu, yayın düştüğü köşegen hücreler yeşil kutulu; $K_{ii}\mathrel{+}=k$ formülü canlı; yay kaldırılınca mekanizma uyarısı |
| `winkler-kiris` | `ks`, `EI` (ya da `E`, `I`), `L`, `P`, `n`: 4–16 | Winkler zeminine oturan kiriş, tutarlı zemin matrisi $(k_sl/420)[\ldots]$ ile çözülür; zemin yayları çökmeyle sıkışır, zemin basıncı $p=-k_sv$ diyagramı; $\beta$, $\beta L$ (kısa, orta, uzun) ve $\beta l_e$ ağ denetimi; $w_{\max}$ ve $M_{\max}$, Hetényi'nin $P\beta/2k_s$ ve $P/4\beta$ değerleriyle yüzde farkla karşılaştırılır |

### 6.3 Yapı analizi (`docs/etkilesim_yapi.js`)

| Ad | Parametreler | Ne gösterir, ne yapılır |
|---|---|---|
| `doseme-dagilimi` | `lx`, `ly`, `w`, `dagitim`: `otomatik`\|`cift`\|`tek` | Plan karesi; köşelerden 45° çizgiler ($m\le2$) ve kenar kirişleri üstüne üçgen (kısa kenar, mavi) ve trapez (uzun kenar, turuncu) yük şekilleri; $m>2$'de uzun kenarlara düzgün yük, kısa kenarlar boş; tepe $p=wl_k/2$, her kenarın payı kN, $q_{eM}$ ve $q_{eV}$ formülleri ve korunum $\sum=wl_kl_u$ canlı; $l_x$, $l_y$, $w$ kaydırıcıları, hazır paneller |
| `kolon-birikimi` | `kat`: 1–8, `g`, `q`, `lx`, `ly`, `konum`: `ic`\|`kenar`\|`kose`, `beta`: true\|false | Solda plan ve kolonun yük alanı (iç: $l_xl_y$, kenar: yarısı, köşe: çeyreği); sağda kolon şeridi: her kat düzeyinde gelen $G$ ve $Q$ okları, aşağı inerken kalınlaşan kümülatif $N$ çubuğu ve sayıları; TS 498:2021 Çizelge 7 $\beta$ azaltması (üçten çok kat) seçilebilir; $A_{\text{trib}}$, $N_{\text{taban}}$ ve $\sigma=N/A$ için gerekli temel alanı formülü |
| `deprem-spektrumu` | `SS`, `S1`, `zemin`: `ZA`…`ZE`, `R`, `I`: 1\|1.2\|1.5, `D`, `Tp` | TBDY 2018 yatay elastik tasarım spektrumu $S_{ae}(T)$ (Denk. 2.2) ve azaltılmış $S_{aR}=S_{ae}/R_a$ (Denk. 4.1, 4.8); Tablo 2.1/2.2 ara değerli $F_S$, $F_1$; $T_A$, $T_B$ kesikli çizgiler; $T_p$ noktasında iki eğrinin değeri ve formüller canlı; hazır parseller |
| `kombinasyon-zarfi` | `G`, `Q`, `E` (istasyon değerleri, kN·m), `L`, `gG`, `gQ`, `gE`, `SDS`, `x` | Üst panelde $G$ (mavi), $Q$ (turuncu), $E$ (yeşil) moment diyagramları; altta $1.4G+1.6Q$, TBDY (4.11) $G+Q\pm E+0.3E_Z$ ve (4.12) $0.9G\pm E-0.3E_Z$ zarfı: en büyük ve en küçük eğri her bölgede belirleyen ailenin renginde (−E kesikli), aradaki bant gri; $\gamma_G$, $\gamma_Q$, $\gamma_E$ kaydırıcılarıyla kendi kombinasyonun; $S_{DS}$ deprem satırlarındaki $G$ katsayısını değiştirir; kesit kaydırıcısında $M=\sum\gamma_iM_i$ ve zarf; uçlar ve orta için belirleyen tablosu. Varsayılan: ders binası eleman 30 |
| `ruzgar-kat-kuvveti` | `kat`: 1–30, `h`, `B`, `C`: 1.2\|1.6, `sarp` | TS 498:2021 md. 14: solda Çizelge 4 $q(z)$ basamakları, ortada cephe ve kat düzeylerinde $F_i=C\,q(z_i)\,B\,h_{\text{pay}}$ okları, sağda kat kesmesi $V_i$ basamakları; $V_t$ ve $M_o$ formülü; sarp yamaçta $q\ge1.1$ |
| `kat-kuvvetleri` | `N`: 1–12, `w`, `wN`, `h`, `SDS`, `SD1`, `R`, `D`, `I`, `Tp` (0: $T_{pA}$) | TBDY 2018 md. 4.7: $T_{pA}=0.1H_N^{3/4}$ ya da elle $T_p$, $S_{ae}$, $R_a$, $S_{aR}$, $V_{tE}\ge0.04IS_{DS}W_t$; cephede ters üçgen $F_{iE}$ okları (mavi), tepede $\Delta F_{NE}$ (kırmızı), kütle noktaları; sağda kat kesmesi $V_i$; $\sum F+\Delta F=V_{tE}$ denetimi canlı |
| `kiris-donati` | `Md`, `b`, `h`, `beton`: C20…C50 | TS 500 kiriş kesiti: basınç bloğu $a$ (turuncu), tarafsız eksen $c$, önerilen çubuklar, birim uzama dağılımı ($\varepsilon_{cu}$, $\varepsilon_s$, $\varepsilon_{yd}$), kuvvet çifti $C$ ve $T$; $\rho$ ölçeğinde $\rho_{min}$–$\rho_{max}$ bandı; tek / çift donatı, $M_{lim}$, $A_s$, $A_s'$, öneri ve $M_r$ formülleri canlı; $\rho>0.02$'de "kesit büyüt"; hazırlar |
| `kolon-nm` | `b`, `h`, `rho`, `beton`, `N`, `M` | TS 500 N–M etkileşim eğrisi (dört yüze 8 çubuk), $N_0$, $N_t$, dengeli nokta; $0.9f_{cd}A_c$ ve TBDY $0.40f_{ck}A_c$ çizgileri; sürüklenebilir $(N,M)$ noktası, $e_{min}$ ile büyütülmüş nokta, orijinden ışın ve kesişim kutusu, radyal D/C (dışarıda kırmızı); Ders 22 kolon A1 noktaları ve zarf köşesi hazır |
| `celik-burkulma` | `KLr`, `Fy`: 235\|275\|355, `profil` | ÇYTHYE Bölüm 8: $F_{cr}$ eğrisi (Denk. 8.2/8.3) ve Euler $F_e$ (kesikli), $F_y$ çizgisi, $4.71\sqrt{E/F_y}$ geçişi, $KL/i>200$ bölgesi; nokta sürüklenir; $P_c=\phi_cF_{cr}A_g$ |
| `celik-yanal-burulma` | `profil`, `Fy`, `Lb`, `Cb` | ÇYTHYE 9.2: $M_n$–$L_b$ eğrisi, $L_p$, $L_r$ ve üç bölge renkli zeminde, $M_p$ ve $0.7F_yW_{el}$ çizgileri, $C_b>1$'de $C_b=1$ eğrisi kesikli; kompakt olmayan başlıkta Denk. 9.9; nokta sürüklenir |
| `rijit-diyafram` | `k`: [4 sayı], `F`, `e` | 6×4 m kat, köşelerde dört kolon: rijitlik kaydırıcıları, $F_y$ ve dışmerkezlik; $\mathbf K=\sum k_i\mathbf T_i^T\mathbf T_i$ (3×3) ve çözüm $u_x$, $u_y$, $\theta$; ötelenmiş plan (abartılı), efendi düğüm (KM), rijitlik merkezi (RM), kolon kesme okları ve pay tablosu |

## 7. Alıştırma kataloğu

Her alıştırma rastgele soru üretir, cevabı tam kesirle denetler (ondalık yazılırsa $10^{-3}$ bağıl hata içinde
"yaklaşık doğru" sayar), ipucu ve cevap gösterir, **Adım adım çözüm** ile motoru çağırır.

| Ad | Parametreler | Soru |
|---|---|---|
| `boyut` | `zorluk` | Matrisin boyutu, $a_{ij}$ okuma, çarpımın tanımlı olup olmadığı |
| `toplama` | `zorluk`, `boyut` | $A+B$ ya da $A-B$ |
| `skaler` | `zorluk`, `boyut` | $kA$ |
| `carpim` | `zorluk` | $AB$ (2×2, 2×3 · 3×2, 3×3) |
| `transpoz` | `zorluk` | $A^T$ |
| `determinant` | `zorluk`, `boyut` | $\det A$ (2×2 ya da 3×3) |
| `ters` | `zorluk` | $A^{-1}$ (2×2, kesirli) |
| `coz` | `zorluk`, `boyut` | $A\mathbf{x}=\mathbf{b}$ |
| `ozdeger` | `zorluk` | 2×2 özdeğerler (tam sayı) |
| `cubuk-k` | `zorluk` | Çubuk elemanının $k$ matrisi |
| `kafes-k` | `zorluk` | Açılı kafes elemanının 4×4 matrisi (0°, 90°, 45°, 3-4-5, 5-12-13) |
| `birlestir` | `zorluk` | İki ya da üç elemanlı birleştirme |
| `sinir-kosulu` | `zorluk` | Mesnetli sistemde bilinmeyen yer değiştirmeler |
| `yay-seri` | `zorluk` | Seri yaylarda düğüm yer değiştirmeleri ve tepki |
| `doseme-esdeger` | `zorluk` | Döşeme payı: $m$ ve tepe $p=wl_k/2$ (1), üçgen $q_{eM}$ ya da $q_{eV}$ (2), trapez $q_{eM}$ ya da $q_{eV}$ (3) |
| `kombinasyon` | `zorluk` | Durum momentlerinden $1.4G+1.6Q$ (1); TBDY (4.11) ya da (4.12), $0.3E_d^{(Z)}=0.2S_{DS}G$ dahil (2); TS 500 rüzgâr ya da TBDY deprem birleşimlerinin zarfında $M_{\max}$ ve $M_{\min}$ (3) |
| `deprem-vt` | `zorluk` | $S_{DS}$, $S_{D1}$, $T_p$, $R$, $D$, $I$, $m_t$ ile $V_{tE}$: $T_p>T_B$ (1), platoda $R_a=D+(R/I-D)T_p/T_B$ (2), karışık ve alt sınır, ayrıca $\Delta F_{NE}$ (3) |
| `kiris-as` | `zorluk` | TS 500 kiriş: verilen çubuklarla $a$ ve $M_r$ (1), $M_d$'den gerekli $A_s$ (2), $a$ ve $\rho_{min}$ denetimli $A_s$ (3); %0.5 tolerans |
| `celik-mn` | `zorluk` | ÇYTHYE 9.2 kompakt I kiriş: $L_b\le L_p$'de $M_n$ ve $\phi_bM_n$ (1), elastik olmayan YBB (2), elastik YBB'de $F_{cr}$ ve $M_n$ (3); %0.5 tolerans |

## 8. Pedagoji kuralları

### 8.1 Ders akışı

1. **Neden?** Bir mühendislik sorusuyla açılış (2–4 cümle).
2. **Kavram:** `::: tanim` kutusu ve küçük sayısal örnek.
3. **Görsel:** her ana kavram için en az bir `::: etkilesim` ya da `::: sekil`. Ders başına en az iki etkileşim.
4. **Yöntem:** adım adım, renkli ve kutulu blok matematik; satır işlemleri okla.
5. **Çözümlü örnekler:** ders başına en az 6, kolaydan zora. Her `cevap` görsel araç (renk, kutu, parsel ya da ok)
   kullanır. En az 4 örnekte `kod` ve `kontrol` bulunur.
6. **Sık yapılan hata:** en az bir `::: hata` kutusu.
7. **Mühendislikte:** en az bir `::: muhendislik` kutusu; sonlu eleman ve yapı bağlantısı, uygun düştüğünde tarihi
   yığma köprü ve OMA.
8. **Özet:** `::: ozet` kutusu.
9. **Alıştırma:** en az bir `::: alistirma`.

### 8.2 Dil

- Sade Türkçe, "sen" diliyle. Terim ilk geçtiğinde kalın yazılır, İngilizcesi bir kez parantezde verilir.
- Her yeni sembol ilk kullanıldığı yerde tanımlanır. Birimler yazılır: kN, m, kN/m, MPa.
- Sayılar ondalık virgülle yazılmaz; KaTeX içinde nokta kullanılır (`0.5`).

### 8.3 Sonlu eleman modeli (`se.se_coz` ve `dof-haritasi` için)

```json
{"tip": "kafes", "baslik": "İki çubuklu kafes",
 "birim": {"kuvvet": "kN", "uzunluk": "m"},
 "dugumler": [{"no": 1, "x": 0, "y": 0}, {"no": 2, "x": 6, "y": 0}, {"no": 3, "x": 3, "y": 4}],
 "elemanlar": [{"no": 1, "dugumler": [1, 3], "E": "200e6", "A": "0.001"},
               {"no": 2, "dugumler": [2, 3], "E": "200e6", "A": "0.001"}],
 "mesnetler": [{"dugum": 1, "ux": true, "uy": true}, {"dugum": 2, "ux": true, "uy": true}],
 "yukler": [{"dugum": 3, "Fx": 0, "Fy": -10}],
 "yayili": []}
```

`tip`: `yay`, `cubuk`, `kafes`, `kiris`, `cerceve`. `E`, `A`, `I`, `k`, `P`, `q`, `L` sembol olabilir; koordinatlar
sayıdır. `q` elemanın yerel $y$ ekseninde, kN/m.
