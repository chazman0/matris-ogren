# Ders biçimi (`dersler/*.md`)

Bu dosya ders kaynaklarının sözleşmesidir. `ders_derle.py` dersleri bu kurallara göre okur, denetler ve
`docs/dersler.json` dosyasını üretir. Bu dosya ile adı `_` ile başlayan dosyalar ders sayılmaz.

Denetim: `python ders_derle.py --denetle` (biçim) ve `pytest testler/test_dersler.py` (örnek kodları).
Etkileşimleri tek başına görmek için: `docs/galeri.html` ya da `docs/galeri.html?ad=carpim-gezgini`.

---

## 1. Dosya adı ve sıra

- Ad: `NN-kisa-ad.md`. `NN` iki basamaklı ders numarasıdır ve benzersizdir.
- `01`–`08` matris bölümü, `11`–`20` sonlu elemanlar bölümüdür. Sıra numaradan gelir.
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
| 20 | `20-temel-sistemleri.md` | elastik mesnet $K_{ii}\mathrel{+}=k$, Winkler zemini $(k_sL/420)[\ldots]$ ve $\beta$, mesnet çökmesi $K_{ff}u_f=F_f-K_{fs}u_s$, kolon–kiriş–temel sistemi |

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
| `bolum` | evet | `matris` ya da `se` |
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

- Ad alanında `mo` (matris_ogren), `sp` (sympy) ve varsa `se` (sonlu_eleman) bulunur. `import` yazılmaz.
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

Sonlu eleman modeli çözen örnekler `se.se_coz(model)` kullanır; model §8.3 şemasındadır.

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
| `elastik-mesnet` | `E`, `I`, `L`, `P`, `k1`, `k2`, `kr` | İki ucu düşey yaya oturan iki elemanlı kiriş: yaylar zikzak, sol uçtaki dönme yayı sarmal; elastik eğri ve yay kuvvetleri $-k\,u$ oklarla; 6×6 $K$'da eleman parselleri mavi ve turuncu, yayın düştüğü köşegen hücreler yeşil kutulu; $K_{ii}\mathrel{+}=k$ formülü canlı; yay kaldırılınca mekanizma uyarısı |
| `winkler-kiris` | `ks`, `EI` (ya da `E`, `I`), `L`, `P`, `n`: 4–16 | Winkler zeminine oturan kiriş, tutarlı zemin matrisi $(k_sl/420)[\ldots]$ ile çözülür; zemin yayları çökmeyle sıkışır, zemin basıncı $p=-k_sv$ diyagramı; $\beta$, $\beta L$ (kısa, orta, uzun) ve $\beta l_e$ ağ denetimi; $w_{\max}$ ve $M_{\max}$, Hetényi'nin $P\beta/2k_s$ ve $P/4\beta$ değerleriyle yüzde farkla karşılaştırılır |

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
