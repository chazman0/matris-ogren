# Matris Öğren — Kullanım Kılavuzu

Sonlu elemanlar dersi için **adım adım matris hesaplayıcı**. Bir matris yazarsın; uygulama önce o işlemin
**kuralını** ve **elle nasıl yapıldığını** (her ara hesapla birlikte) gösterir, sonra aynı işi yapan
**🐍 Python kodunu ve gerçek çıktısını** verir. Böylece hem matematiği hem Python'u aynı ekranda öğrenirsin.

Uygulama üç parçadan oluşur:

| Parça | Dosya | Ne işe yarar |
|---|---|---|
| Colab defteri | `Matris_Ogren.ipynb` | Tarayıcıda açılır, kurulum gerektirmez; matris işlemleri bölüm bölüm form alanlarıyla çalışılır; "Bina modeli" bölümü bina şablonunu çözer, raporu ve kesit önerisini gösterir |
| Python modülleri | `matris_ogren.py` (matris), `sonlu_eleman.py`, `yapi.py`, `yapi_serbest.py`, `yapi_veri.py`, `tasarim.py`, `temel.py`, `rapor.py`, `tablolar.py`, `alan.py` | Hesapları yapan ve anlatan asıl kod; defter bu on modülün hepsini gömülü taşır, matris modülünü `mo` kısaltmasıyla kullanır |
| Web / masaüstü uygulaması | `docs/` ([chazman0.github.io/matris-ogren](https://chazman0.github.io/matris-ogren/)), `masaustu/` | Hesapla, Dersler, Sonlu eleman, Bina ve Yardım sayfaları; aynı Python modülleri tarayıcıda (Pyodide) ya da masaüstü programının içinde, çevrimdışı çalışır |

Bu kılavuzun 1–3.7 bölümleri Colab defterini ve matris modülünü, 3.8 sonlu eleman modülünü, 3.9 bina modüllerini (aks–kat ve genel
model, rapor, tablolar, ısı haritası alanları, köprü işlemleri), 3.10–3.12 uygulamanın Bina sayfasını ve kısayollarını anlatır.
Kod yorumlarının başvurduğu tasarım bölümleri (§1–§19) ve veri şemaları: [`TASARIM.md`](TASARIM.md).

---

## Hızlı başlangıç (5 adım)

1. [colab.research.google.com](https://colab.research.google.com) adresini aç, Google hesabınla giriş yap.
2. **Dosya → Not defteri yükle** ile `Matris_Ogren.ipynb` dosyasını seç.
3. En üstteki **Kurulum** hücresini çalıştır (hücreye tıkla, **Shift+Enter** ya da soldaki ▶ düğmesi).
4. İstediğin bölüme in, form alanına matrisini yaz (örn. `1 2; 3 4`), hücreyi çalıştır.
5. Çıktıyı yukarıdan aşağıya oku: 📘 Kural → adımlar → ✅ Sonuç → 🐍 Python ile.

---

## 1. Bu uygulama nedir, neyi öğretir?

Dersteki her temel matris işlemini **üç katmanda** gösterir:

1. **📘 Kural / tanım** — kısa ders notu (örn. "A'nın sütun sayısı B'nin satır sayısına eşit olmalı").
2. **✏️ Adım adım hesap** — elle nasıl yapıldığı; her elemanın, her satır işleminin açık yazılışı.
3. **🐍 Python ile** — aynı işi yapan numpy/sympy kodu ve o kodun **gerçekten çalıştırılmış** çıktısı.

Öğretilen konular:

- Matris yazımı, boyut, toplama, çıkarma, sayı ile çarpma
- Matris çarpımı (satır × sütun kuralı, birden çok matrisi zincir çarpma)
- Transpoz, iz, rank (rank için ayrı form yok; Bölüm 12'deki serbest çalışma alanında `mo.rank(...)` ile)
- Determinant (2×2 ve 3×3'te kofaktör açılımı, daha büyüklerde satır indirgeme)
- Ters matris (2×2 formülü, genel Gauss–Jordan)
- Denklem sistemi çözümü **A x = b** (Gauss eliminasyonu, Cramer, ters matris yöntemi)
- Özdeğer–özvektör ve **K φ = ω² M φ** doğal frekans problemi
- Sonlu elemanlar: çubuk, kiriş (Euler–Bernoulli, 4×4) ve düzlem kafes elemanı rijitlik matrisleri,
  **birleştirme (assembly)**, **sınır koşulları**, yer değiştirme çözümü ve **mesnet tepkileri**
- Bina modeli (defterin 11. bölümü): hazır bir bina şablonunun çözümü, statik hesap raporu ve kesit önerisi

Hesaplar **kesin** yapılır: `0.5` yazarsan `1/2` olarak saklanır, sonuçlar kesir olarak çıkar (istersen
ondalık gösterime çevirebilirsin, bkz. Ayarlar). Harfler (E, A, L, I, k, P …) **sembol** olarak kalır;
yani `E*A/L` gibi sembolik rijitlik matrisleriyle de çalışabilirsin — derste tahtadaki haliyle.

---

## 2. Defteri Colab'da açma (3 yol)

### Yol A — Dosya yükleyerek (en hızlısı)

1. [colab.research.google.com](https://colab.research.google.com) → **Dosya → Not defteri yükle** (File → Upload notebook).
2. Bilgisayarından `%USERPROFILE%\Desktop\matris_ogren\Matris_Ogren.ipynb` dosyasını seç.
3. Açılınca "Bu not defteri Google tarafından yazılmadı" uyarısı çıkabilir → **Yine de çalıştır**.

Not: Bu yolla yüklenen defterde yaptığın değişiklikler kalıcı değildir. Saklamak istersen
**Dosya → Drive'da bir kopya kaydet**.

### Yol B — Google Drive üzerinden (kalıcı)

1. `Matris_Ogren.ipynb` dosyasını Google Drive'ına yükle (drive.google.com → Yeni → Dosya yükle).
2. Drive'da dosyaya sağ tıkla → **Birlikte aç → Google Colaboratory**
   (listede yoksa: *Daha fazla uygulama bağla* → Colaboratory'yi ekle).
3. Bundan sonra defter Drive'da kalır; yazdığın örnekler ve notlar kaydedilir. Colab'da
   **Dosya → Not defteri aç → Google Drive** sekmesinden de açabilirsin.

### Yol C — Claude Code + colab-mcp (Claude senin yerine hücre yazıp çalıştırır)

Bilgisayarında [colab-mcp](https://github.com/googlecolab/colab-mcp) kurulu ve Claude Code'a kayıtlı:

- Kurulum yapıldı: `uv tool install --python 3.13 git+https://github.com/googlecolab/colab-mcp`
  → `$env:USERPROFILE\.local\bin\colab-mcp.exe`
- Claude Code'a kullanıcı kapsamında (tüm projelerde geçerli) kaydedildi:
  `claude mcp add --scope user colab-mcp -- "$env:USERPROFILE\.local\bin\colab-mcp.exe"`
- **Claude Code yeniden başlatıldıktan sonra** kullanılabilir.

Kullanım:

1. Kontrol: terminalde `claude mcp list` → satırda `colab-mcp … Connected` görünmeli.
2. Claude'a **"Colab'a bağlan"** de. Claude `open_colab_browser_connection` aracını çalıştırır; varsayılan
   tarayıcında `https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=…&mcpProxyPort=…`
   adresi açılır. Tarayıcıda **Google hesabına giriş yapılmış olmalı**.
3. Bağlantı **60 saniye içinde** kurulur. Bundan sonra Claude açılan defterde hücre oluşturabilir,
   çalıştırabilir ve çıktıyı okuyabilir.
4. Bağlantı yereldir ve **tek oturumluktur**: Claude Code'u kapatınca biter; bir sonraki sefer yeniden
   "Colab'a bağlan" dersin.

Örnek istekler (Claude'a yazacakların):

- "Colab'a bağlan, Masaüstündeki `matris_ogren.py` modülünü deftere kur ve `mo.carp("1 2; 3 4", "5 6; 7 8")` çalıştır."
- "Derste verilen K = `2 -1; -1 2`, F = `0; 10` sistemini 1. serbestlik derecesi (SD; düğümün bir hareket yönü) sabitken çöz, adımları göster."

---

## 3. Defteri kullanma

### 3.1 Kurulum hücresi

Defterin en üstündeki **Kurulum** hücresi programın on Python modülünü (matris, sonlu eleman, bina — aks–kat ve genel model —,
temel, tasarım, rapor, tablolar, alan) Colab oturumuna kurar ve matris modülünü `mo` adıyla hazır eder. Modüller hücrenin
içinde sıkıştırılmış (zlib + base64) ve SHA-256 özetiyle gömülüdür: hücre onları açar, özetleri denetler, Colab'da
`/content/matris_modulleri` klasörüne (Colab dışında geçici klasöre) yazar ve klasörü Python yolunun başına ekler. Böylece
`import yapi`, `import rapor` gibi satırlar da defterin içinden çalışır; çalışma klasöründe aynı adlı dosya varsa o değil
gömülü kopya kullanılır. **Her açılışta bir kez** çalıştırılır (ikinci çalıştırma modülleri gömülü kopyadan yeniden yükler).
Çalıştırmadan form hücreleri `RuntimeError: Önce '🔧 1) Kurulum' hücresini çalıştırın.` hatası verir (Bölüm 12'deki serbest
çalışma hücresi ise `ModuleNotFoundError: No module named 'matris_ogren'` der).

### 3.2 Form alanları ve hücre çalıştırma

Her bölümde hücrenin sağında **form alanları** (kutucuklar) bulunur: matrisi, sağ tarafı, yöntemi vb.
oraya yazarsın. Hücreyi çalıştırmak için hücreye tıklayıp **Shift+Enter** ya da soldaki ▶ düğmesi.
Form alanının altındaki kodu görmek istersen hücreye çift tıkla (ya da sağ üstten "Kodu göster").

### 3.3 Matris yazım biçimleri

Aşağıdakilerin hepsi aynı 2×2 matrisi verir:

| Yazım | Açıklama |
|---|---|
| `1 2; 3 4` | satırlar `;` ile ayrılır, elemanlar boşlukla (**en pratik yol**) |
| `1,2;3,4` | elemanlar virgülle |
| `[[1,2],[3,4]]` | Python listesi yazımı |
| çok satırlı: `1 2` ↵ `3 4` | her satır bir matris satırı |

Elemanlar:

| Yazım | Anlamı |
|---|---|
| `3`, `-7` | tam sayı |
| `2.5` | ondalık (**nokta** ile) — kesin olarak `5/2` saklanır |
| `1/3` | kesir |
| `sqrt(2)`, `pi`, `sin(30*pi/180)` | kök, π, trigonometrik |
| `E*A/L`, `2*E*I/L^3` | sembolik ifade (`^` ya da `**` üs demektir) |

Kurallar:

- **Ondalık için nokta kullan:** `2.5` doğrudur. Virgül eleman ayırıcıdır; `2,5` yazarsan `2` ve `5` iki ayrı eleman
  olarak okunur (hata vermez, yanlış matris kurar). Türkçe alışkanlıkla ondalık virgül yazma.
- Harfler **sembol** olur: `E`, `A`, `L`, `I`, `k`, `P`, `u` … Bu modülde `E` Euler sayısı, `I` sanal birim
  **değildir**; dersteki anlamlarındadır (elastisite modülü, atalet momenti).
- Ayrılmış adlar sembol olamaz: `sqrt sin cos tan exp log ln pi abs`.
- Sembolik ifadede **boşluk bırakma**: `E*A/L` yaz. `E A/L` yazarsan boşluk eleman ayırıcı sayılır ve
  `E` ile `A/L` iki ayrı eleman olur (hata vermez, yanlış matris kurar!).
- Sağ taraf vektörü `b` sütun (`3; 5`) ya da satır (`3 5`) olarak yazılabilir; ikisi de sütun vektörü sayılır.
- Bir işlemin sonucunu bir sonraki işleme doğrudan verebilirsin: `C = mo.carp(A, B)` → `mo.transpoz(C)`.

### 3.4 Bölümler

Numaralar defterdeki bölüm numaralarıyla aynıdır:

| Bölüm | Konu | Modül işlevi |
|---|---|---|
| 0 | Kurulum (ilk çalıştırılacak hücre; defterde başlığı "🔧 1) Kurulum") | kurulum hücresi |
| 1 | Matris nedir: boyut, eleman adresleri, transpoz, iz | `matris`, `transpoz`, `iz` |
| 2 | Toplama, çıkarma, skalerle çarpma | `topla`, `cikar`, `skaler` |
| 3 | Matris çarpımı (zincir çarpım dahil) | `carp` |
| 4 | Transpoz | `transpoz` |
| 5 | Determinant | `determinant` |
| 6 | Ters matris | `ters` |
| 7 | Denklem sistemi A x = b | `coz` |
| 8 | Özdeğer (8a), doğal frekans (8b) | `ozdeger` |
| 9 | Sonlu elemanlar: 9a çubuk, 9b kiriş, 9c kafes, 9d birleştirme, 9e sınır koşulu + tepkiler, 9f baştan sona örnek | `cubuk_eleman`, `kiris_eleman`, `kafes_eleman`, `birlestir`, `sinir_kosulu` |
| 10 | Ayarlar | `ayarla` |
| 11 | Bina modeli: 11.1 şablonu çöz (özet: ΣG, en büyük D/C, belirleyen), 11.2 statik hesap raporu (HTML, defter içinde), 11.3 kesit önerisi | `yapi.bina_sablon`, `yapi.bina_coz`, `rapor.statik_rapor`, `yapi_serbest.kesit_oner` |
| 12 | Serbest çalışma alanı | tüm işlevler (`rank` yalnız buradan: `mo.rank(...)`) |

**Bina modeli (Bölüm 11).** 11.1'de açılır listeden bir şablon seçip çalıştırırsın (şablon listesi defter üretilirken
`yapi.bina_sablonlar()`'dan alınır). Hücre binayı yükler, çözer (bütün yük durumları, birleşimler ve kesit tahkikleri) ve özet
tablo verir: toplam sabit ve hareketli yük, tahkik edilen eleman sayısı, en büyük D/C ve onu **belirleyen** eleman, kontrol ve
birleşim, temel tipi, uyarılar. Kendi modelin için uygulamada **💾 Kaydet** ile indirdiğin `.matris` (ya da bina `.json`)
dosyasını Colab'ın 📁 Dosyalar paneline yükleyip adını *dosya* kutusuna yaz. 11.2 aynı çözümün 14 bölümlük statik hesap
raporunu defterin içinde (çerçeve içinde) açar ve istersen `statik_rapor.html` dosyasına yazar. 11.3 her çubuk için kesit
önerisini (yinele = 0: model değişmez) D/C önce → D/C öneri (tahmini) tablosuyla verir; uygulamadaki "Hepsini uygula"
öneriyi binaya uygulayıp yeniden çözer. Çözüm şablona göre birkaç saniye ile yarım dakika sürer.

### 3.5 Çıktıyı okuma

Her işlem aynı düzende çıktı verir:

```
### Matris çarpımı: AB                ← başlık
> 📘 Kural: ...                       ← işlemin tanımı ve kuralı (ders notu)
A = [...], B = [...]                  ← girdiler
Boyut kontrolü ... ✔                  ← adımlar: boyut kontrolü, her elemanın açık hesabı,
c11 = a11 b11 + a12 b21 = 1·5 + 2·7 = 19   satır işlemleri (R2 ← R2 − 2 R1), geri yerine koyma ...
> ⚠️ ...                              ← varsa uyarı (tekil matris, sonsuz çözüm, tanımsız çarpım)
> ✅ Sonuç                            ← sonuç (kesir/sembolik)
**🐍 Python ile**                     ← aynı işin numpy/sympy kodu
(python kod bloğu)                       kopyalayıp başka yerde kullanabilirsin
Çıktı: ...                            ← o kodun gerçek çıktısı (ondalık, numpy biçiminde)
```

Okurken:

- Önce **📘 Kural**'ı oku, sonra adımları tahtadaki çözümle satır satır karşılaştır.
- **✅ Sonuç** kesir/sembol olarak, **Python çıktısı** ondalık olarak gelir; `4/5` ile `0.8` aynı şeydir.
- numpy çıktısında `2.0000000000000004` gibi değerler yuvarlama hatasıdır, `2`'dir.
- Çarpımda **Python** bölümündeki not önemli: numpy'da `@` matris çarpımı, `*` eleman eleman çarpımdır.
- Sembolik girdide (E, A, L …) Python bölümü numpy yerine **sympy** kodu üretir.

### 3.6 Ayarlar hücresi

Gösterimi defterdeki **Ayarlar** hücresinden ya da herhangi bir hücrede `mo.ayarla(...)` ile değiştirirsin
(hesap her zaman kesin yapılır; ayarlar yalnız gösterimi etkiler):

```python
mo.ayarla(goster="hepsi")            # hepsi | adimlar | python | sonuc | yok
mo.ayarla(ondalik=True, basamak=3)   # sonuçları 3 anlamlı basamakla ondalık göster
mo.ayarla(python=False)              # 🐍 Python bölümünü gizle
mo.ayarla(kural=False)               # 📘 Kural kutusunu gizle
mo.ayarla(en_fazla_eleman=36)        # eleman eleman anlatım en fazla bu kadar eleman için (6×6)
```

| `goster=` | Ne gösterir |
|---|---|
| `"hepsi"` (varsayılan) | kural + adımlar + sonuç + Python |
| `"adimlar"` | kural + adımlar + sonuç (Python yok) — sadece matematiğe odaklanmak için |
| `"python"` | sonuç + Python (adımlar yok) — kodu öğrenmek için |
| `"sonuc"` | yalnız ✅ Sonuç — hızlı kontrol için |
| `"yok"` | hiçbir şey basmaz; değer yine döner |

Tek bir çağrı için: `mo.coz("2 1; 1 3", "3; 5", goster="sonuc")`.

### 3.7 Serbest çalışma alanında API (kısa tablo)

Tüm işlevler bir `Sonuc` döndürür; anlatım otomatik gösterilir.

| İşlev | Ne yapar | Örnek |
|---|---|---|
| `mo.topla(A, B)` / `mo.cikar(A, B)` | eleman eleman toplama / çıkarma | `mo.topla("1 2; 3 4", "5 6; 7 8")` |
| `mo.skaler(k, A)` | sayı ile çarpma | `mo.skaler(3, "1 2; 3 4")` |
| `mo.carp(A, B, ...)` | matris çarpımı; 3+ matris zincir | `mo.carp("1 2; 3 4", "5 6; 7 8")` → `19 22; 43 50` |
| `mo.transpoz(A)` | transpoz | `mo.transpoz("1 2 3; 4 5 6")` |
| `mo.iz(A)` / `mo.rank(A)` | köşegen toplamı / rank | `mo.rank("1 2; 2 4")` → 1 |
| `mo.determinant(A, yontem=...)` | `"kofaktor"` ya da `"eliminasyon"` (boşsa ≤3×3 kofaktör) | `mo.determinant("2 1; 1 3")` → 5 |
| `mo.ters(A, yontem=...)` | `"formul"` (2×2) ya da `"gauss"` | `mo.ters("4 7; 2 6")` |
| `mo.coz(A, b, yontem=..., bilinmeyen=...)` | `"gauss"` (varsayılan), `"cramer"` (≤3×3), `"ters"` | `mo.coz("2 1; 1 3", "3; 5")` → `x = 4/5; 7/5` |
| `mo.ozdeger(A)` | özdeğer + özvektör | `mo.ozdeger("2 1; 1 2")` → λ = 1, 3 |
| `mo.ozdeger(K, M)` | K φ = λ M φ, ω = √λ doğal frekans | `mo.ozdeger("2 -1; -1 2", "1 0; 0 1")` |
| `mo.cubuk_eleman(E, A, L)` | çubuk elemanı k (2×2) | `mo.cubuk_eleman("E", "A", "L")` ya da `mo.cubuk_eleman(200e3, 100, 1000)` |
| `mo.kiris_eleman(E, I, L)` | kiriş elemanı k (4×4, SD sırası v1 θ1 v2 θ2; E [MPa], I [mm⁴], L [mm]) | `mo.kiris_eleman(200e3, 2e6, 2000)` |
| `mo.kafes_eleman(E, A, L, açı)` | düzlem kafes k = Tᵀ k' T (4×4) | `mo.kafes_eleman(1, 1, 1, 45)` |
| `mo.birlestir([(k1,[1,2]), (k2,[2,3])], n)` | global K (SD numaraları 1'den başlar) | aşağıdaki örnek |
| `mo.sinir_kosulu(K, F, sabit=[...])` | mesnet uygula, çöz, tepkiler | aşağıdaki örnek |
| `mo.yardim()` | işlev listesi | `mo.yardim()` |

Sonucu kodda kullanmak:

```python
r = mo.coz("2 1; 1 3", "3; 5", goster="yok")
r.deger            # sympy matrisi  → Matrix([[4/5], [7/5]])
r.deger.tolist()   # Python listesi → [[4/5], [7/5]]
r.python_kodu      # üretilen Python kodu (metin)
r.python_ciktisi   # o kodun çıktısı (metin)
print(r.anlatim.markdown())   # anlatımın tamamı Markdown metni olarak
```

### 3.8 Sonlu elemanlar zinciri (derste yapılan sırayla)

İki çubuk eleman, 3 düğüm, 1. düğüm sabit, 3. düğüme 10 N:

```python
k1 = mo.cubuk_eleman(200e3, 100, 1000)   # E = 200000 N/mm², A = 100 mm², L = 1000 mm → EA/L = 20000
k2 = mo.cubuk_eleman(200e3, 100, 1000)
K  = mo.birlestir([(k1, [1, 2]), (k2, [2, 3])], 3)   # eleman 1 → SD 1-2, eleman 2 → SD 2-3
u  = mo.sinir_kosulu(K, "0; 0; 10", sabit=[1])       # u = [0, 1/2000, 1/1000] mm, R = [-10, 0, 0] N
```

Anlatımda sırasıyla: eleman matrislerinin K içine **nereye eklendiği** (K_22 += k1_22 + k2_11 gibi),
sabit SD'nin satır ve sütununun silinmesiyle **indirgenmiş sistem**, Gauss eliminasyonu, tüm
yer değiştirme vektörü ve **mesnet tepkileri** R = K u − F görülür. R₁ = −10 N eksi çıkar: tepki global eksenin
tersine yöneliktir, yani mesnet düğüm 1'i yüke zıt yönde tutar. Serbest SD'lerde R = 0 çıkması çözümün sağlamasıdır.
Önce sembolik (`"E","A","L"`) sonra sayısal yapmak kavramı oturtur.

Bütün zinciri tek çağrıda kurmak için `sonlu_eleman.py` modülü vardır. Model bir sözlüktür: düğümler, elemanlar,
mesnetler (`ux`, `uy`, `rz`) ve yükler (`Fx`, `Fy`). Hazır modeller `se.ornek_model(ad)` ile gelir:

```python
import sonlu_eleman as se
r = se.se_coz(se.ornek_model("cerceve-portal"))   # yer değiştirmeler r.deger
r.veri["tepkiler"]                                 # mesnet tepkileri
r.veri["elemanlar"][0]["diyagram"]["M"]            # eleman 1'in moment diyagramı
se.ornek_listesi()                                 # 20 hazır model: ad, başlık, tür, açıklama
```

Model türleri: `yay`, `cubuk`, `kafes`, `kiris`, `cerceve` (düzlem) ve `kafes3b`, `cerceve3b` (uzay). Uzay modellerde
düğümlere `z`, uzay çerçeve elemanına `E, G, A, Iy, Iz, J` yazılır; mesnetler `ux, uy, uz, rx, ry, rz`, yükler
`Fx, Fy, Fz, Mx, My, Mz`, yayılı yük `q` (yerel y′) ve `qz` (yerel z′) olur. Sonuçta `diyagram` sözlüğüne `Vz`, `My`, `T`
de eklenir; her elemanın `lam` anahtarı yerel eksen matrisidir (y′ düşey düzlemde yukarı, düşey elemanda z′ = Z).

Temel sistemleri için üç ek anahtar vardır:

```python
m = se.ornek_model("cerceve-portal")
m["yaylar"] = [{"dugum": 1, "kx": 20000, "ky": 100000, "kr": 30000}]   # elastik mesnet: K köşegenine eklenir
m["cokmeler"] = [{"dugum": 4, "uy": -0.01}]                             # mesnet çökmesi: K_ff u_f = F_f − K_fs u_s
m["elemanlar"][1]["zemin"] = 25000                                      # Winkler zemini (kiriş/çerçeve): k_s [kN/m²]
r = se.se_coz(m)
r.veri["yaylar"]        # yay kuvvetleri −k·u
r.veri["cokmeler"]      # verilen yer değiştirmeler
r.veri["elemanlar"][1]["zemin_kuvvetleri"]   # zeminin düğümlere aktarılmış (global) kuvvetleri
```

Düzlemdeki `M` ile uzaydaki `Mz`, düzlemdeki `kr` ile uzaydaki `krz` aynı bileşendir; ikisi de kabul edilir (ikisi
birden verilirse toplanır). Harfli (sembolik) girdide çözüm `linsolve` + `cancel` ile yapılır; indirgenmiş sistem
büyükse (çok sembol, köklü doğrultu kosinüsleri) anlatımda adım adım Gauss yok etme yerine indirgenmiş sistem ve
çözümü gösterilir.

Hazır örnekler: `kiris-elastik-zemin`, `cerceve-iki-katli`, `cerceve-elastik-mesnet`, `cerceve-mesnet-cokmesi`,
`cerceve-temel-kirisi` (kolon–kiriş–temel), `kafes3b-tripod`, `kafes3b-kule`, `cerceve3b-konsol-L`, `cerceve3b-izgara`,
`cerceve3b-portal`.

Web uygulamasında aynı çözücü **Sonlu eleman** sayfasında çalışır (3B modeller için bakış açısı kaydırıcıları, yay /
çökme tabloları ve altı diyagram düğmesi vardır); 11–20 numaralı dersler (yay, çubuk, kafes, birleştirme, sınır koşulu,
kiriş, çerçeve, titreşim, uzay yapılar, temel sistemleri) bu zinciri etkileşimli çizimler ve çözümlü örneklerle anlatır;
21–26. dersler (yük akışı, yük durumları ve kombinasyonlar, TBDY eşdeğer deprem, TS 500, ÇYTHYE, bina analizinin program akışı)
aynı zinciri bina ölçeğinde `yapi.py` ile sürdürür (toplam 24 ders).

### 3.9 Bina analizi ve yük akışı (yapi.py)

`yapi.py` bir binayı aks–kat sistemiyle tanımlar, TS 498:2021 yüklerini kurar, döşeme yükünü TS 500 md. 11.4.3'teki
45° kuralıyla kirişlere dağıtır (kısa kenara üçgen, uzun kenara trapez; gerçek şekil parçalı doğrusal yük olarak
motora gider), binayı `cerceve3b` ağına çevirip G ve Q durumlarını tek seferde çözer (`se.coz_coklu`), 1,4G + 1,6Q ve
G + Q kombinasyonlarını (Dilim 2'de bütün TS 500 / ÇYTHYE / TBDY kümesini) süperpozisyonla toplar ve yük akışını (kiriş → kolon → temel → zemin) tablo, şema ve beş sayılık
korunum sağlamasıyla anlatır. Kütüphane değerleri (`yapi_veri.py`: beton, donatı, çelik, IPE/HEA/HEB, TS 498 Çizelge 6
hareketli yükler, birim ağırlıklar, duvar ve kaplama takımları, Çizelge 7 azaltma, TS 500/ÇYTHYE/TBDY kombinasyon listeleri)
her kayıtta `kaynak` ve `dogrulandi` taşır.

```python
import yapi
b = yapi.bina_sablon("betonarme-2kat-3x2")          # 9 şablon (2'si genel surum 3 modeli): yapi.bina_sablonlar()
r = yapi.bina_coz(b)                                # 13 adımlı anlatım (12: kesit tahkikleri) + bağımsız numpy betiği
                                                    # (genel modelin kendi ardışık adımları vardır, son adımı da numpy betiğidir; 3.9.1)
v = r.veri
v["yukler"]["dosemeler"][0]["paylar"]               # her kenar kirişine giden üçgen/trapez pay (tepe, q_eM, q_eV, toplam kN)
v["akis"]["kolonlar"]                               # kat kat N (FE) ve yük alanı (tributary) karşılaştırması, fark %
v["akis"]["temeller"]                               # N, M_X, M_Y, σ_max/min, e/B, D/C
v["akis"]["korunum"]["G"]                           # döşeme + duvar + öz = Σ kolon taban N = Σ temel tepkisi
v["sonuclar"]["1.4G+1.6Q"]["elemanlar"][0]["M"]     # kombinasyon diyagramları (ortak istasyonlarda süperpozisyon; u yazılmaz)
yapi.kombinasyon_kisa(r.ic, "G+Q")                  # yanıtta olmayan kombinasyonun tam kaydı (G+Q = G ve Q'nun toplamı)
v["zarf"]                                           # her eleman için en büyük / en küçük ve belirleyen kombinasyon
yapi.yuk_yolu(b, v, {"tur": "doseme", "no": 1, "durum": "G+Q"})   # tek nesneden zemine adım adım zincir
```

**Temel tipleri** (`temeller.tip`): `tekil` (kolon başına B × L; mesnet ankastre / mafsal / elastik), `surekli` (mütemadi:
seçilen aks çizgileri boyunca ters T kesitli temel kirişleri) ve `radye` (bütün planı taşmayla kaplayan plak; isteğe bağlı aks
kirişleri). Mütemadi ve radyede kolon tabanları sabit mesnet değildir: temel elemanları (`temel.py`) bina ağına eklenir ve
Winkler zeminine (düğüm yayı k_z = k0·A_etki; mütemadide tabla dönme yayı k0·B³/12·l) oturur; radye iki doğrultulu ızgara
(şerit I = b·h³/12, J ≈ b·h³/6) ile temsil edilir. Ağ aralığı `ag` serbestlik sınırına sığmazsa kendiliğinden büyütülür. Aks–kat ve
genel model aynı `temel.py` modülünü kullanır (genel modelin kuralları 3.9.1'de); iki modelde de temel öz ağırlığı G durumuna girer
(`veri.akis.korunum.G.temel_oz`, `veri.temel.oz_yuk`) ve 10.1 korunum denetimi zemin yaylarının toplamıyla (yay_ozet) ✔ verir.

```python
b = yapi.bina_sablon("betonarme-4kat-radye")        # ya da "betonarme-3kat-surekli-temel"
r = yapi.bina_coz(b)                                # 13. adım: Temel ve zemin (Winkler, taban basıncı, zımbalama, donatı)
T = r.veri["temel"]
T["dugumler"][0]                                    # {no, X, Y, w_mm, p_kNm2, A[, kolon]}: servis G+Q oturma ve p = k0·w
T["p_maks"], T["DC_zemin"], T["oturma_maks_mm"], T["farkli_oturma_metin"]
T["zemin_kontrolleri"]                              # TS 500 emniyet (servis, q_em) ve TBDY 16.8 (katsayılı, q_t = q_k/1,4) ayrı
T["tasarim"]                                        # temel kirişi / tabla / radye şeridi donatısı, zımbalama (TS 500 md. 8.3.1)
yapi.kombinasyon_kisa(r.ic, "1.4G+1.6Q")["temel"]   # bir kombinasyonun taban basıncı ve oturması
```

Bina modeli bir sözlüktür (`tur: "bina"`): `akslar` (X harfli, Y sayılı; konum m), `katlar` (0 = temel, kotlar),
`malzemeler` (`{"kutuphane": "C30/37"}` ya da `"S275"`), `kesitler` (`dikdortgen` b/h m ya da `profil` "IPE 300"),
`kolonlar` (`aks`, `kat`, `kesit`, `yon` x/y: güçlü eksenin çalıştığı doğrultu), `kirisler` (`bas`/`son` aynı aks çizgisinde;
komşu olmayan akslar arasında verilirse ara kesişimlerde bölünür), `dosemeler` (tek hücrelik panel, `kullanim` TS 498 sınıfı
ya da `q`, `g_ek` kaplama), `duvarlar`, `ek_yukler`, `temeller` (B, L, q_em, `mesnet`: ankastre / mafsal / elastik). Duvar
oturduğu kirişe yük verir; yüksekliği kirişin **altındaki** kat yüksekliği − kiriş yüksekliğidir (kirişte `duvar_h` ile açıkça
verilir: çatıda parapet 1,0 m; şablonlar çatı kirişine kat boyu duvar koymaz). Betonarme kirişin öz ağırlığı varsayılan
`analiz.kiris_oz = "net"`: A = b·(h − t_döşeme), döşeme içindeki kısım plak ağırlığında sayıldığı için (`"brut"`: b·h). Bina
koordinatı X sağa, Y derinlik, Z yukarı; motor dönüşümü (`x_m = X, y_m = Z, z_m = −Y`) tek yerde yapılır ve sonuçlar
bina koordinatında döner. Sınırlar: aks–kat modelinde 12×12 aks, 12 kat, 1500 SD; genel (surum 3) modelde 2000 SD, aks sınırı yok.
Hatalar öğreticidir (yüzen döşeme, kolonsuz kat, bilinmeyen kesit, model çok büyük…). `yapi.dogrulanmamis_kayitlar()` doğrulanmamış kütüphane kayıtlarını listeler; web köprüsü
bunları yanıtın `ozet.uyarilar` alanına yazar.

**Kar, rüzgâr, deprem ve kombinasyonlar (Dilim 2).** Yük durumları yapı analiz programlarındaki "load pattern" gibi ayrı ayrı kurulur ve bir
K ile birlikte çözülür: G, Q, S (kar, TS 498:2021 md. 11 Çizelge 3: s = μ1·S_k, çatı döşemelerine 45° kuralıyla), W+X / W−X /
W+Y / W−Y (rüzgâr, md. 14: W_i = C·q(z_i)·B_cephe·kat payı, Çizelge 4 basamakları) ve TBDY 2018 eşdeğer deprem yükü EX+, EX−,
EY+, EY− (± %5 dışmerkezlik) ile EZ = (2/3)·S_DS·G. Deprem açıksa her kata kütle merkezinde bir efendi düğüm konur (rijit
diyafram, `deprem.diyafram: "esnek"` ile kapatılır). Betonarme binada deprem açıkken **çatlamış (etkin) kesit rijitliği**
(TBDY 4.5.8, Tablo 4.2: kolon 0,70·EI, kiriş 0,35·EI) varsayılandır (4.5.8.1 zorunlu kılar; `analiz.catlamis_rijitlik: false`
yazılırsa çözülür ama "TBDY 4.5.8.1'e aykırı" uyarısı eklenir). 4.5.8.3 gereği iki K kurulur: brüt K ile G, Q, S, W (deprem
dışı birleşimler, servis, yük akışı); çatlamış K ile deprem durumları ve deprem birleşimlerine giren G~c, Q~c, S~c kopyaları
(`veri.kombinasyonlar[i].catlamis: true`; `kombinasyon_kisa(r.ic, "G~c")` ile okunur). A1 burulma düzensizliğinde (η_bi > 1,2)
±%5 dışmerkezlik kat bazında ve iki doğrultu için D_bi = (max η_bi/1,2)² ile büyütülür (md. 4.7.4; `deprem.D_b_kat`);
η_bi > 2 ise Tablo 4.4'ün "diğer tüm binalar" satırı uygulanır.

```python
b = yapi.bina_sablon("betonarme-2kat-3x2")
b["yuk_durumlari"]["S"] = {"acik": True, "bolge": 4, "rakim": 900, "mu": 0.8}      # S_k = 1,10 kN/m² (Çizelge 3)
b["yuk_durumlari"]["W"] = {"acik": True, "C": 1.2}                                  # Çizelge 5, kapalı bina
b["yuk_durumlari"]["E"] = {"acik": True}
b["deprem"].update({"SS": 1.2, "S1": 0.35, "SS_DD3": 0.45, "S1_DD3": 0.13,          # AFAD TDTH (DD-2 ve DD-3)
                    "zemin_sinifi": "ZD", "BKS": 3, "tasiyici": "betonarme-cerceve-yuksek",   # A11: R = 8, D = 3
                    "periyot": "rayleigh", "dolgu": "bitisik"})
# analiz.catlamis_rijitlik: betonarme + deprem → varsayılan True (Tablo 4.2: kolon 0,70·EI, kiriş 0,35·EI)
r = yapi.bina_coz(b)
d = r.veri["deprem"]
d["SDS"], d["SD1"], d["DTS"], d["BYS"]                      # spektrum ve sınıflar (kaynaklar: d["kaynaklar"]["SDS"] …)
d["TpA"], d["X"]["Tp_rayleigh"], d["Tp"]                    # ampirik ve Rayleigh periyodu (≤ 1,4·T_pA)
d["VtE"], d["VtE_min"], d["dFN"]                            # taban kesme (≥ 0,04·m_t·I·S_DS·g), tepe ek kuvveti
[(k["kat"], k["F_x"], k["V_x"], k["Mb_x"]) for k in d["katlar"]]          # kat kuvveti, kesme, dışmerkezlik momenti
[(k["kat"], k["delta_x"], k["oran_x"], k["eta_bx"], k["theta_x"], k["uygun"]) for k in d["katlar"]]   # Δ (m), λδ/h, η_bi, θ_II
r.veri["ruzgar"]["katlar"], r.veri["kar"]["S_toplam"], r.veri["kutle_merkezi"]
[k["ad"] for k in r.veri["kombinasyonlar"] if k["uygulandi"]][:4]
# ['1.4G+1.6Q', '1.4G+1.6Q+1.6S', 'G+1.3Q+1.3W+X', ...]  ad katsayılardan: 'G+Q+0.2S+EX++0.3EY++0.3EZ', '0.9G+EX-+0.3EY+-0.3EZ'
r.veri["zarf"]["kombinasyon_sayisi"]                        # öteleme (drift) birleşimleri zarfa ve sayıma girmez
tam = yapi.kombinasyon_kisa(r.ic, "G+Q+0.2S+EX++0.3EY++0.3EZ")   # tek kombinasyonun tam diyagramları (yeniden çözüm yok)
yapi.deprem_onizleme(b)                                     # çözümsüz hızlı önizleme (spektrum, V_tE, F_i)
yapi.tasiyici_sistemler()                                   # Tablo 4.1 alt kümesi: ad, etiket, R, D, BYS_izin, kaynak
```

Kombinasyon kümeleri `kombinasyon_kumesi` ile seçilir: `ts500` (TS 500 Denk. 6.3–6.6, 6.9–6.10 + TBDY Denk. 4.11/4.12;
TS 500 kar terimini ayrı vermez, kar TS 498:2021 md. 3.1'e göre hareketli yük: 1,4G + 1,6Q + 1,6S, md. 12.1 kar + rüzgâr
G + 1,3Q + 1,3(S/2) + 1,3W ve G + 1,3Q + 1,3S + 1,3(W/2), servis G + Q + S),
`cythye_ydkt` (ÇYTHYE 5.3.1, rüzgâr 1,6W; deprem satırında TBDY 9.2.5.1: 1,2G), `cythye_gkt` (ÇYTHYE 5.3.2 + TBDY 9.1a–c).
Rüzgâr dört yöne, E_d(H) Denk. (4.9)'a göre ±EX ± 0,3EY ve ±0,3EX ± EY ile ± dışmerkezliğe (32 varyant) açılır; varlık
nedeni olan durum yoksa satır uygulanmaz (6.4'te T, 6.9/6.10'da H, kar satırlarında S), ikincil terim yoksa sıfır alınır
(4.11'de 0,2S, 4.12'de H). Kombinasyonlar yeniden çözülmez, durum sonuçlarının katsayılı toplamıdır (yaygın yapı analiz programları da böyle yapar).
Yanıt boyutu için `durumlar` içinde yalnız G ve Q tam diyagramlıdır; S, W, E durumları uç kuvvetleri ve `enb` taşır
(`diyagram: false`), `sonuclar` yalnız ilk dayanım kombinasyonunu içerir (büyük modelde o da tembel kalır, `ozet.sonuclar_tembel`).

Köprü işlemleri (`bina_coz`, `bina_kombinasyon`, `bina_eleman_tasarim`, `bina_kesit_oner`, `bina_eleman_bilgi`, `bina_rapor`,
`bina_tablolar`, `bina_alan` …): girdi / yanıt tablosu 3.9.5'te.

**Kesit tahkikleri (Dilim 3).** `tasarim.py` yüklüyse `bina_coz` her bina kirişini ve kolonunu dayanım ve deprem
kombinasyonlarının (servis ve öteleme birleşimleri hariç) her biriyle denetler ve sonucu `veri["tasarim"]`a, en büyük D/C'yi
`veri["ozet"]["en_buyuk_dc"]`ye, anlatımı 12. adıma yazar (Python betiği 13. adım olur). `tasarim.py` yoksa bu alanlar
yazılmaz, çözüm aynen çalışır.

- **Betonarme kiriş (TS 500):** bütün FE parçalarında mesnet uçlarındaki en büyük negatif moment → üst donatı, açıklıktaki en
  büyük pozitif moment → alt donatı (motor M işareti: alt lif çekme +), en büyük |V| → etriye (`kiris_egilme`, `kiris_kesme`).
  d′ = paspayı (kesitte `pas`, varsayılan 30 mm) + 20 mm; momentler kolon ekseninde, kesme yüze indirgenmeden (güvenli tarafta).
- **Betonarme kolon (TS 500 + TBDY 7.3):** her kombinasyonun alt ve üst ucundaki **eş zamanlı** (N, Mx, My) noktaları (zarf
  değil) N–M etkileşim eğrisiyle (`kolon_kontrol`, e_min dahil; bağımsız çağrıda varsayılan `tbdy=False` — TBDY 0,40 f_ck A_c
  sınırı için `tbdy=True, deprem=[...]` ile deprem birleşimi noktaları işaretlenir). Eksenler bina eksenleridir: Mx bina X ekseni etrafında
  (derinlik Y yönü boyutu bY), My bina Y ekseni etrafında (derinlik bX); `yon` takası kendiliğinden işlenir. Donatı kesitte
  (`donati_orani` ya da `As` cm²) yoksa ρ = %1 varsayılır ve 0,01 → 0,04 taramasıyla "gerekli ρ" önerilir. Ek denetimler: TBDY
  en küçük boyut 300 mm, N_dm ≤ 0,40 f_ck A_c (N_dm deprem birleşimlerinden; deprem yoksa G + Q).
- **Çelik (ÇYTHYE 2018, YDKT; GKT kümesinde GKT):** kombinasyon başına (N, güçlü eksen Mx, zayıf eksen My, V) ile
  `celik_eleman_kontrol`; kolonda K = 1, L = kat yüksekliği. Döşemeli kirişte döşeme yalnız üst başlığı tutar: pozitif moment
  L_b = 0 ile, negatif moment (mesnet, alt başlık basınçta) L_b = parça açıklığı ve C_b moment diyagramından (ÇYTHYE Denk. 9.1)
  ile ayrı denetlenir, büyük D/C belirler (`ozet.bolge`, `Lb_neg_m`, `Cb_neg`); `analiz.celik_Lb = "boy"`: her yerde L_b = L,
  C_b = 1. Döşemesiz kirişte L_b = açıklık, C_b = 1.
- Elemanın D/C'si dayanım satırlarının en büyüğüdür; yönetmelik alt/üst sınır koşulları (en az donatı, boyut, aralık,
  narinlik; satırda `kosul: true`) yalnız sağlanmadığında belirler. Deprem kombinasyonu varsa uyarı: TBDY kapasite tasarımı
  (güçlü kolon–zayıf kiriş, kapasite kesmesi, birleşim bölgesi) bu araçta yoktur — sonuçlar ön boyutlandırmadır.

```python
t = r.veri["tasarim"]
t["en_buyuk_dc"], t["dc_dagilimi"], t["kritik_elemanlar"][:3]      # {"<0.7": n, "0.7-0.9": n, "0.9-1.0": n, ">1.0": n}
e = t["elemanlar"][0]                                               # {no, tur, adres, kesit, dc, durum, belirleyen, kontroller, ozet}
e["ozet"]["As_ust_cm2"], e["ozet"]["oneri_alt"], e["ozet"]["etriye"]   # kiriş: gerekli donatı, öneri ("3Φ14"), "Φ8/20"
k = yapi.eleman_tasarim(r.ic, "kolon", 1)                           # anlatımlı ayrıntı: kesit şeması, N–M eğrisi
k.veri["egri_x"][:3], k.veri["noktalar"][0]                         # [{N, M}], {ad, kombinasyon, uc, N, Mx, My, dc}
```

### 3.9.1 Genel (surum 3) model: `yapi_serbest.py`

Aks–kat sözlüğü (kolonlar, kirişler, döşemeler) düzenli katlı binaları tanımlar. Çapraz, makas, eğik çatı, kren yolu ya da kat
dışı düğüm gereken yapılar için **genel düğüm–çubuk–panel modeli** kullanılır (bina JSON `"surum": 3`; tasarım haritası
[`TASARIM.md`](TASARIM.md) §12, §19). Motoru `yapi_serbest.py`'dir; `yapi.bina_coz` binayı kendisi yönlendirir (`yapi._serbest_mi`):

- **Genel model** ⇔ `surum` ≥ 3, ya da `cubuklar`, `paneller`, `dugumler`, `mesnetler`, `uretecler` listelerinden biri dolu, ya da
  bir ek yük düğüm başvurulu (`"dugum": {"aks": [..], "z": ..}`), çubuk ya da panel yüküdür. Aks–kat düğüm yükü
  (`{"tur": "dugum", "aks": ["B", "2"], "kat": 1}`) ve boş listeler binayı aks–kat bırakır.
- Aks–kat elemanları varsa önce aynı kurallarla genel listeye çevrilir (`docs/model_ops.js` `genellestir` ile birebir); aynı bina iki
  yoldan aynı tepkileri ve iç kuvvetleri verir.
- Anlatımın kendi ardışık adımları vardır (aks sistemi ve elemanlar, panel yük dağıtımı, ağ ve mesnetler, yük durumları (rüzgâr
  ve kren dahil), deprem, varsa yalnız çekme, kombinasyonlar, denge, kesit tahkikleri, varsa temel ve zemin) ve anlatım **"Aynı hesap
  Python'da"** adımıyla biter: G durumunun tek başına çalışan numpy betiği (düğümler, 6 SD'li uzay çerçeve elemanları, uç
  serbestliklerinin yoğunlaştırılması, mesnetler ve yaylar, yayılı yüklerin eşdeğer düğüm yükleri; K kurulur, çözülür, Σ tepki ve kolon
  alt uç kuvvetleri yazılır). Betiğin çıktısı "Denge ve korunum" adımındaki G toplamıyla aynı olmalıdır; rijit diyafram ve yatay
  durumlar (W, E) betiğe alınmaz, çok büyük modelde (SD sınırı üstü) adım yalnız notla kalır.

**Düğüm başvurusu (REF):** her düğüm bir aks kesişimi ya da bir çubuğun bölme / kesişim noktasıdır; konumlar her çözümde akslardan
hesaplanır, aks taşınınca bağlı düğümler de taşınır. Aynı konuma (1 mm) düşen başvurular tek düğümdür.

```python
{"aks": ["B", "3"], "z": "Saçak"}                       # GLOBAL akslar: X aksı, Y aksı, Z aksı adı
{"sistem": "KANAT-B", "aks": ["C", "2"], "z": "±0.00"}   # ek aks sistemi (silindirikte aks = [r, teta])
{"aks": ["B", "3"], "kat": 1}                            # eski aks–kat başvurusu (= kat 1'in Z aksı)
{"dugum": 100004}                                        # dugumler kaydı:
# {"no": 100004, "tur": "bolme", "cubuk_i": REF, "cubuk_j": REF, "oran": 0.25}      i–j doğrusunun 1/4'ü
# {"no": 100005, "tur": "kesisim", "a": [REF, REF], "b": [REF, REF]}             iki doğrunun kesişimi
# {"no": 100006, "X": 1.0, "Y": 2.0, "Z": 3.0}                                     yalnız geriye uyum (serbest koordinat)
```

**Şema** (aks–kat alanlarına ek; birimler kN, m):

| Alan | Biçim |
|---|---|
| `akslar` | `x`, `y`: `[{ad, konum}]`; `z`: `[{ad, konum, kat?}]` — `kat` işareti olan Z aksı kat seviyesidir (0 = temel), ötekiler (Saçak, Mahya, Kren…) ara kotlardır. `z` yoksa `katlar`'dan türetilir. |
| `aks_sistemleri` | `[{ad, tur: "kartezyen" \| "silindirik", orijin: [X, Y, Z], aci (°), x, y \| r, teta, z?}]`; `z` yoksa GLOBAL Z aksları kullanılır. |
| `dugumler` | bölme, kesişim ya da aks kayıtları (yukarıda); numaralar 100001'den başlar. |
| `cubuklar` | `{no, i: REF, j: REF, tur, kesit, aci?, serbest?: {"i": [...], "j": [...]}, yalniz_cekme?, K?: [güçlü, zayıf], Lb?, duvar?, duvar_h?, grup?}`; `tur`: kolon, kiris, capraz, makas-ust, makas-alt, makas-dikme, makas-diyagonal, asik, kren, bag, diger; serbestlik adları N, Vy, Vz, T, My, Mz. |
| `kesitler` | aks–kat kartlarına ek basit çelik kesitler: `{"tip": "profil", "profil": "BORU 114.3x4" \| "KUTU 150x8" \| "L 100x10" \| "2L 70x7 s=10" \| "UPN 200"}`; vute `{"tip": "vute", ...}`. |
| `paneller` | `{no, kose: [REF × 3+], tur: "doseme" \| "cati" \| "cephe", kalinlik?, g?, q? \| kullanim?, dagitim: "iki" \| "tek-13" \| "tek-24" \| "yok", kar?, ruzgar?: {"cp": "otomatik" \| [4 sayı]}}`; kalınlık 0 taşıyıcı olmayan kaplamadır. |
| `mesnetler` | `{dugum: REF, ux, uy, uz, rx, ry, rz, kx?, ky?, kz?, krx?, kry?, krz?}`: `ux` … `rz` tutulu doğrultular (bool); `kx`, `ky`, `kz` (kN/m) ve `krx`, `kry`, `krz` (kN·m/rad) **yaylı mesnet** rijitlikleri, bina eksenlerinde (X, Y, Z ve onların etrafında dönme); her biri pozitif sayı ya da yok. Bir doğrultu ya tutulu ya yaylıdır (ikisi birden hata). Yay rijitliği olan kayıt çözümde `tip: "yay"` olur, tepkisi yay kuvvetini içerir. Rijit diyaframlı bir kat seviyesindeki düğüme `ux`, `uy`, `rz` verilirse bunlar diyafram bağıyla (ceza rijitliği) uygulanır: o nokta bütün katın yatay hareketini tutar (uyarı yazılır); `uz`, `rx`, `ry` olağan mesnettir. En alt Z aksındaki (kat 0) bütün aks kesişimleri `temeller.mesnet` ile kendiliğinden mesnetlenir (tekil temelde); bölme / kesişim düğümlerine mesnet bu listeyle verilir. |
| `ek_yukler` | çubuk `{tur: "cubuk", cubuk, durum, q \| q1, q2, x1?, x2?, yon?}` ya da tekil `{..., P, x}`; düğüm `{tur: "dugum", dugum: REF, durum, FX, FY, FZ, MX, MY, MZ}`; panel `{tur: "panel", panel, durum: "G" \| "Q" \| "S", p}` (kN/m², aşağı +; eski `{g, q}` biçimi de okunur). |
| `kren` | `[{no, yol: [çubuk no…], tekerlek: {P_maks, P_min, H_yanal, H_fren, aralik, adet}, dinamik, konum_sayisi}]` → K durumu; her köprü konumu bir alt durumdur ve hareketli yük içeren birleşimlere eklenir. |
| `uretecler` | `[{no, tur: "makas" \| "besik-cerceve" \| "asik" \| "kren-yolu" \| "capraz" \| "cephe-kirisi", ...}]`: üreteçlerin kaydı (düzenlemek için); ürettikleri çubuklar `kaynak: {"uretec": no}` taşır, çözüm `cubuklar` / `paneller`'den yapılır. |
| `temeller` | aks–kat ile aynı şema: `tip: "tekil"` (B × L, `ozel` ek sistemde `{sistem, aks}`), `"surekli"` (mütemadi; `surekli: {yon, akslar, B, h_tabla, b_govde, h_govde, tasma, ag, yatay, kh_oran}`) ya da `"radye"` (`radye: {h, tasma, ag, kiris, yatay, kh_oran}`); `zemin`, `malzeme`, `donati`. Genel modelde mütemadi / radye kuralları aşağıda. |

Küçük bir örnek (tek gözlü çelik çerçeve, çatı döşemesi, yalnız çekme çapraz, panel ve düğüm yükü):

```python
import yapi, yapi_serbest
A = lambda x, y, z: {"aks": [x, y], "z": z}
b = {"surum": 3, "tur": "bina", "baslik": "Çelik portal", "sistem": "celik",
     "akslar": {"x": [{"ad": "A", "konum": 0}, {"ad": "B", "konum": 6}], "y": [{"ad": "1", "konum": 0}, {"ad": "2", "konum": 5}],
                "z": [{"ad": "±0.00", "konum": 0, "kat": 0}, {"ad": "Saçak", "konum": 4, "kat": 1}]},
     "malzemeler": {"S275": {"kutuphane": "S275"}},
     "kesitler": {"HEA200": {"tip": "profil", "profil": "HEA 200", "malzeme": "S275"},
                  "IPE240": {"tip": "profil", "profil": "IPE 240", "malzeme": "S275"},
                  "BORU89": {"tip": "profil", "profil": "BORU 88.9x4", "malzeme": "S275"}},
     "cubuklar": [{"no": n, "i": A(x, y, "±0.00"), "j": A(x, y, "Saçak"), "tur": "kolon", "kesit": "HEA200"}
                  for n, (x, y) in enumerate([("A", "1"), ("B", "1"), ("A", "2"), ("B", "2")], start=1)]
               + [{"no": 4 + n, "i": A(*p, "Saçak"), "j": A(*q, "Saçak"), "tur": "kiris", "kesit": "IPE240"}
                  for n, (p, q) in enumerate([(("A", "1"), ("B", "1")), (("A", "2"), ("B", "2")),
                                               (("A", "1"), ("A", "2")), (("B", "1"), ("B", "2"))], start=1)]
               + [{"no": 9, "i": A("A", "1", "±0.00"), "j": A("A", "2", "Saçak"), "tur": "capraz", "kesit": "BORU89",
                   "serbest": {"i": ["My", "Mz"], "j": ["My", "Mz"]}, "yalniz_cekme": True}],
     "paneller": [{"no": 1, "kose": [A("A", "1", "Saçak"), A("B", "1", "Saçak"), A("B", "2", "Saçak"), A("A", "2", "Saçak")],
                   "tur": "doseme", "kalinlik": 0.12, "kullanim": "konut"}],
     "ek_yukler": [{"tur": "panel", "panel": 1, "durum": "G", "p": 1.5},
                   {"tur": "dugum", "dugum": A("B", "2", "Saçak"), "durum": "Q", "FX": 10}]}
r = yapi.bina_coz(b)                                # yapi._serbest_mi(b) → True: yapi_serbest.bina_coz
v = r.veri                                          # v["surum"] == 3, v["model"] == "genel"
v["akis"]["temeller"][0]                            # temel mesnetleri: {dugum, adres, tip, N_G, N_Q, MX, MY, B, L, h, N_temel…}
v["akis"]["mesnetler"]                              # açık "mesnetler" kayıtlarının tepkileri (burada boş)
v["yalniz_cekme"]                                   # birleşim başına devre dışı çubuk ve yineleme sayısı
v["tasarim"]["elemanlar"][0]["cubuk"], v["tasarim"]["en_buyuk_dc"]
yapi.eleman_tasarim(r.ic, "cubuk", 5)               # tek çubuğun anlatımlı tahkiki (genel modelde tur "cubuk")
```

Hazır genel şablonlar: `celik-sanayi-4hol` (4 hol, 7 çerçeve, vuteli mertek, aşık, çatı ve cephe çaprazları, rüzgâr kolonları,
kren yolu) ve `celik-cbf-3kat` (3 katlı merkezi çaprazlı çerçeve: ters V ve X çaprazlar, mafsallı kirişler, TBDY Bölüm 9 koşulları).

**Genel modelde mütemadi ve radye temel.** Temel düğümleri en alt Z seviyesindeki (kat 0), açık `mesnetler` kaydı olmayan ve en az bir
çubuk taşıyan aks kesişimleridir. Tekil temelde bunlar nokta mesnettir. Mütemadi ve radyede sabit mesnet yoktur: düğümler `temel.py`'nin
Winkler ağına bağlanır, ağ **GLOBAL X/Y aks çizgileri** boyunca kurulur (mütemadide temel kotunda kolonu olan akslarda temel kirişleri,
radyede GLOBAL aks zarfı + taşma üzerinde plak ızgarası). `temel.py` aynen kullanılır: genel model ona aks–kat görünümü verir
(`yapi_serbest._temel_gorunum`: GLOBAL akslar, taban kolonları ve ızgara sırası); bu yüzden taban basıncı, oturma, zımbalama ve donatı
aks–kat çözümüyle aynıdır. Kurallar:

- Ek aks sistemindeki (GLOBAL kesişimden 1 mm'den uzak) bir taban yalnız **kirişsiz radyede** ağa katılır: düğümden geçen sanal ızgara
  çizgileri (`x=<X>`, `y=<Y>`) eklenir. Mütemadi temelde ve kirişli radyede öğretici hata verir; o düğüme `mesnetler` ile mesnet verin.
- Ağın üzerindeki bir düğüme açık mesnet verilemez (hata); düğüm temele oturur.
- Temel seviyesindeki bağ çubuğu temel ağıyla paralel çalışır (uyarı: rijitlik ve öz ağırlık ayrıca sayılır).
- Mafsallı taban için kolon çubuğunun alt ucuna `serbest: My, Mz` verin (varsayım notu).
- Temel elemanları `veri.ag.elemanlar`'a (`tur` `temel-kirisi` | `radye-serit`), ağ düğümleri `veri.ag.dugumler`'e (`tur: "temel"`)
  eklenir; `veri.temel` aks–kat şemasıyla aynıdır (+ `oz_yuk`: temel öz ağırlığının elemana ve düğüme dağılışı). Kesit önerisi de
  gerçek temelle çözer.
- Sınır yine 2000 serbestliktir; ağ aralığı (`ag`) sığmazsa kendiliğinden büyütülür.

**Kesit önerisi** (`yapi_serbest.kesit_oner(bina=None, *, ic=None, hedef="hepsi", yinele=0)`; köprü `bina_kesit_oner`): her hedef
çubuk için aynı aileden D/C ≤ 1 en hafif çelik profil ya da betonarme b × h. `ic` genel model paketi doğrudan kullanılır; aks–kat
paketi verilirse bina genel motorla bir kez yeniden çözülür (mütemadi / radye temel dahil, gerçek temelle) ve D/C önce görünen aks–kat
tasarım tablosundan alınır. Birden çok parçaya bölünmüş aks–kat elemanı (ör. ara kesişimlerde bölünen kiriş) **tek öneri** verir:
`cubuklar` bütün parça numaraları, `dc_oneri` parçaların en büyüğü, `uygula` en büyük gereken kesit. `grup=True` ve üye listesi
(aynı kesit ve tür) tek bir grup önerisi döndürür (`grup: {kesit, tur, uye}`; `yinele` ≥ 1 ise kart bütün üyelere uygulanır ve
`dc_sonra` üyelerin gerçek D/C'lerinin en büyüğüdür). Depremli modelde `yinele` yanıtı göreli kat ötelemesini de taşır (`oteleme`:
sınır, önce ve sonra δ/h) ve öneri ötelemeyi bozmaz: gerekiyorsa kesitler öteleme için de büyütülür, `aciklama` önce / sonra en büyük
oranı yazar. Köprü yanıtı işlem süresini `sure_ms` alanında verir. `dc_oneri` mevcut iç kuvvetlerle bir tahmindir. Betonarme kolonda b × h aynı kalıp
gerekli ρ büyükse `degisim` "donatı" olur ve `uygula` yeni bir kart verir (ör. `B30x30-ρ%2.00`, `donati_orani` ile). `yinele` > 0
(en çok 3): ilk turda bütün öneriler uygulanır (aynı kesit ve türdeki çubuklara grubun en ağır önerisi; betonarme kolon grubunda ρ
bütün üyeler yeniden doğrulanarak seçilir), sonraki turlar yalnız D/C > 1 kalan grupları büyütür (küçültmez). Son çözümde D/C > 1
kalırsa `uyarilar` "… turda yakınsamadı" der; yakınsadıysa bu çalışmada açılan kolon kartlarının ρ'su son kuvvetlerle yeterli en
küçük değere indirilir (`donati_azaltma`). Önerilen bina JSON'u döner.

```python
o = yapi_serbest.kesit_oner(b, ic=r.ic, hedef=[{"tur": "cubuk", "no": 5}])
x = o["oneriler"][0]                                # {cubuk, tur, kesit, oneri, sistem, malzeme, b, h, kaynak, gerekce,
x["oneri"], x["dc_once"], x["dc_oneri"], x["degisim"]   #  dc_once, dc_oneri, dc_sonra, degisim, uygula}
x["uygula"]                                         # {"ad": "IPE270", "tanim": {"tip": "profil", "profil": "IPE 270", ...}, "yeni": True}
o2 = yapi_serbest.kesit_oner(b, ic=r.ic, hedef="hepsi", yinele=3)    # o2["bina"]: önerileri uygulanmış bina, o2["dc_sonra"], o2["uyarilar"]
```

Sınır: genel modelde en çok 2000 serbestlik (`yapi_serbest.EN_FAZLA_SD`), aks sınırı yok.

### 3.9.2 Statik hesap raporu: `rapor.py`

`rapor.statik_rapor(bina, veri, *, secenek=None)` tek dosya HTML5 rapor döndürür (gömülü CSS, A4 yazdırma, içindekiler, satır içi
SVG; dış kaynak yok). Bölümler sabit sıradadır: 1 kapak / künye, 2 yönetmelikler, 3 genel bilgiler, 4 malzemeler, 5 kesitler,
6 yükler, 7 deprem, 8 analiz yöntemi, 9 yük birleşimleri, 10 analiz sonuçları, 11 betonarme, 12 çelik, 13 temel, 14 sonuç; metraj
özeti, Ek A düğümler, Ek B çubuklar, Ek C seçilen tablolar. Veri olmayan bölüm "Bu modelde uygulanmadı" notuyla kalır. Köprü:
`bina_rapor`.

```python
import yapi, rapor
b = yapi.bina_sablon("betonarme-3kat-3x3")
v = yapi.bina_coz(b, anlat=False).veri
html = rapor.statik_rapor(b, v, secenek={"proje": {"ad": "Örnek konut", "yer": "Ankara", "hazirlayan": "…"},
                                         "bolumler": [1, 2, 3, 6, 7, 11, 14], "eleman_detay": "kritik",
                                         "tablolar": ["katlar", "metraj_ozet"]})
open(rapor.dosya_adi(b, v, {"proje": {"ad": "Örnek konut"}}), "w", encoding="utf-8").write(html)   # statik_rapor_ornek_konut.html
```

`secenek`: `proje` (ad, yer, il, ilce, ada, parsel, malik, hazirlayan, kontrol, tarih), `bolumler` (1–14, "A", "B", "C", "metraj"),
`eleman_detay` ("kritik": her türde D/C en büyük 5 ve D/C > 1 olanlar; "hepsi"; "yok"), `ek_tablolar` (hazır TABLO listesi),
`tablolar` + `tablo_filtre` (`{ad: {"satirlar": [indeks…]}}`), `program_surumu`.

§10.1'in korunum denetimi Σ tepkiyi mesnet tepkileri + yanıtta yazılan yay kuvvetleri (yaylı mesnet, diyafram bağı, elastik temel) +
`yay_ozet` (yanıta yazılmayan mütemadi / radye zemin yaylarının toplamı) olarak alır (`rapor._Rapor.tepki_toplami`). §13: model
mütemadi / radye ama çözümde o temelin sonucu yoksa (temel tipi çözümden sonra değişti) “Bu çözümde mütemadi/radye temel sonucu yok
(çözüm eski ya da temel tipi değişti); binayı yeniden çözün.” notu düşer; boyutlar çözümün normalize kaydından (`veri.bina.temeller`)
okunur, açık mesnetler ayrı tabloda (yaylı mesnet rijitlikleriyle) listelenir.

### 3.9.3 Tablolar ve metraj: `tablolar.py`

Arayüzdeki tablo editörü ve rapor aynı tabloları kullanır. `tablolar.bina_tablolari(bina, veri=None)` TABLO listesi döndürür:
çözümsüz Model, Yükler ve Metraj (deprem kartı açıksa çözümsüz deprem önizlemesi); `veri` verilirse Analiz, Deprem, Tasarım ve Temel
tabloları da. Düzenlenebilir hücrenin `yol`u bina JSON'undaki gerçek alana işaret eder; düzenlemeler binanın kopyasına uygulanır.
Köprü: `bina_tablolar`.

```python
import yapi, tablolar
b = yapi.bina_sablon("betonarme-2kat-3x2")
T = tablolar.bina_tablolari(b, yapi.bina_coz(b, anlat=False).veri)    # [{ad, baslik, grup, sutunlar, satirlar, toplam, aciklama, kaynak}]
[t["ad"] for t in T][:4]                                               # ['genel', 'katlar', 'akslar', 'aks_sistemleri']
yeni = tablolar.degisiklikleri_uygula(b, [{"yol": ["katlar", {"no": 2}, "kot"], "deger": 6.5}])   # kopya; b değişmez
tablolar.aks_yeniden_adlandir(b, "x", "A", "A1")    # YERİNDE: kolon/kiriş/döşeme aksları ve bütün REF'ler güncellenir
tablolar.metraj_ozeti(b)["satirlar"][0]["degerler"]  # {'kalem': 'Beton — kolon', 'malzeme': 'C30/37', 'miktar': …, 'birim': 'm³'}
```

Metraj eğitim amaçlı yaklaşık keşiftir (birim fiyat yok): betonarme kolon b·h·(H − t), kiriş b·(h − t)·L_net, döşeme alan·t, tekil
temel B·L·h, mütemadi temel (ters T kesit × hat boyu) ve radye (plak alanı × h; kirişli radyede kirişler), kalıp alanları (döşeme alt
yüzü kiriş yüzleri arasındaki net alan), donatı tasarımdan ya da "yaklaşık" etiketli oranlardan; çelikte profil başına uzunluk, birim
ağırlık, bağlantı payı ve boya yüzeyi; genel modelde basit kesitler, vute ve panel / kaplama alanları da. Genel modelin mütemadi /
radye temel tabloları (Temeller, Temel Düğümleri, metraj) çözümsüz de `yapi_serbest._temel_gorunum` ile aks–kat kuralıyla kurulur;
temel betonu aks–kat ile aynıdır (W/25). `tablolar.TUR_ADI` çubuk türlerinin Türkçe adlarıdır (motorla aynı).

### 3.9.4 Isı haritası alanları: `alan.py`

Köprünün önbelleğindeki çözüm paketinden (`r.ic`) yeniden çözmeden alan üretir: kombinasyon = durumların katsayılı toplamı, zarf =
istasyon bazında en büyük / en küçük. Aks–kat ve genel modelde çalışır. Köprü: `bina_alan` (eleman bilgi paneli için
`bina_eleman_bilgi`).

```python
import yapi, alan
r = yapi.bina_coz(yapi.bina_sablon("betonarme-2kat-3x2"), anlat=False)
alan.durum_listesi(r.ic)                       # {"durumlar": ["G", "Q"], "kombinasyonlar": [{ad, tur}], "zarf": ["zarf+", "zarf-"]}
a = alan.eleman_alanlari(r.ic, "1.4G+1.6Q")    # {durum, birim, elemanlar: [istasyonlarda N, Vy, Vz, T, My, Mz, eğri u,
                                               #  σ_maks/σ_min, τ, von Mises, kullanım], dugumler, aralik, not, secenekler}
p = alan.panel_alanlari(r.ic, "G")             # döşeme: {no, adres, kose, izgara: {x, y, w, mx, my, q, ...}, yuk_payi, ...}
rr = yapi.bina_coz(yapi.bina_sablon("betonarme-4kat-radye"), anlat=False)
alan.radye_alani(rr.ic, "G+Q")                 # {tip, k0, q_em, x, y, w, p, p_maks, w_maks, ...}; tekil temelde None
```

İşaret: σ(y, z) = N/A − Mz·y/Iz − My·z/Iy (çekme +, MPa); Mz > 0 alt lifi çeker. Genel modelde döşeme plakları yatay, dört köşeli,
eksenlere paralel `doseme` panellerinden kurulur; öteki paneller notla atlanır.

### 3.9.5 Köprü işlemleri (web ve masaüstü uygulaması)

Uygulama Python modüllerini `docs/web_kopru.py` `calistir(json)` ile çağırır; girdi / yanıt şemalarının tamamı o dosyanın başındadır.
Bina işlemleri:

| İşlem | Girdi → yanıt |
|---|---|
| `bina_coz` | `{bina}` → `{bloklar, veri, sonuc_metin, sure_ms}`; çözümün iç paketi önbelleğe alınır (`veri.cozum_kimligi`); `sure_ms` motordaki işlem süresi (aynısı `veri.ozet.cozum_sure_ms`) |
| `bina_kutuphane`, `bina_sablonlar`, `bina_sablon` | kütüphane (`tasiyici_sistemler` dahil), şablon listesi, `{ad}` → `{bina}` |
| `bina_yuk_yolu` | `{bina, veri, hedef: {tur: "doseme" \| "kiris" \| "kolon", no, durum}}` → `{adimlar}` |
| `bina_deprem` | `{bina}` → `{deprem}` (çözümsüz önizleme: spektrum, V_tE, F_i) |
| `bina_kombinasyon` | `{cozum_kimligi, ad, katsayilar?, bina?}` → `{ad, sonuc}` (tam kayıt). Köprü son çözümleri bellekte tutar; kimlik yoksa `bina` verilirse yeniden çözer |
| `bina_eleman_tasarim` | `{cozum_kimligi, tur: "kiris" \| "kolon" \| "cubuk", no, bina?}` → `{ad, bloklar, sonuc}`; genel modelde `tur: "cubuk"` ve çubuk numarası (tam eşleşme) |
| `bina_kesit_oner` | `{cozum_kimligi \| bina, hedef: "hepsi" \| [{tur, no}], yinele: 0…3, grup?: true}` → `{oneriler, turlar, dc_once, dc_sonra, bina?, oteleme?, uyarilar, sure_ms}` (3.9.1; parçalı elemanda `cubuklar`, grup kipinde `grup`) |
| `bina_eleman_bilgi` | `{cozum_kimligi, tur: "cubuk" \| "kolon" \| "kiris" \| "fe", no, durum?}` → `{paket: {sekmeler: {ic, yer}, sekme_adlari, uyarilar}}`: eleman bilgi panelinin "Motor ayrıntısı" (istasyon iç kuvvetleri, en büyük değerler, uç yer değiştirmeleri) |
| `bina_rapor` | `{cozum_kimligi \| bina, secenek?}` → `{html, dosya_adi}` (3.9.2) |
| `bina_tablolar` | `{cozum_kimligi \| bina}` → `{tablolar, cozumlu}` (3.9.3; önbellekte bu binanın çözümü varsa sonuç tabloları da) |
| `bina_alan` | `{cozum_kimligi \| bina, durum, istasyon?, katsayilar?, elemanlar?}` → `{alan}` (`eleman_alanlari` + `paneller` + `radye`; 3.9.4) |

### 3.10 Bina sayfası (web ve masaüstü): araç kutuları, sağ tık, rapor, IFC, tablolar, ısı haritası

- **Araç kutuları sahnenin kenarlarına yerleşir (rıhtım):** üst ve alt **bantlar** (bütün genişlik) ile sol ve sağ **sütunlar**
  (bantların arasında). Kutular: Çizim, Üreteç ve yük, Düzenleme, Aks, Değiştirme, Ölçme, Görünüm, Analiz, Sonuç; hepsi açık başlar ve
  dizilişteki sıra önceliktir (Çizim, Düzenleme, Görünüm, Analiz, Sonuç önce). Yer daralınca kutular küçülür: önce bantlardaki kutuların
  başlığı gizlenir (ad tutamağın ipucunda kalır), sonra sütunlar iki düğme sütununa geçer. Yine sığmayan kutu sol alt köşedeki
  **“⋯ n” çekmecesine** gider (n: çekmecedeki kutu sayısı; içindeki bir komut etkinse düğmede onun simgesi görünür); çekmece tıklayınca
  açılır, Esc ya da dışarı basma kapatır. Yer açılınca kutu kendiliğinden kenarına döner; yerleşim geçmişe bağlı değildir. Sahnenin
  kenar payları şerit kalınlıklarıdır: kenardaki kutular modeli hiç örtmez. Tam ekran yalnız daha büyük bir alandır: kutular yeniden
  dizilir, çıkınca pencere yerleşimi aynen döner.
- **Kullanıcı kazanır:** kutuyu tutamağından bir kenara sürükleyip bırakın (yerleştirme işareti görünür): kutu o şeridin en öncelikli
  kutusu olur. Sahnenin içine bırakılan kutu **yüzer** (yeri hatırlanır; kenardaki kutuların üstüne binerse en yakın boş yerde
  gösterilir, yer açılınca eski yerine döner). Kutu menüsü: kenardaki kutuda **“Kenar › Üst / Alt / Sol / Sağ”** ve **“Sahnede
  yüzdür”**; çekmecedeki kutuda ayrıca **“Kenara sabitle”** (şeridinin başına; bu yüzden başka bir kutu çekmeceye düşebilir, bildirim
  söyler: “… sığmadı; ⋯ düğmesinden açılır.”); yüzen kutuda “Yatay yap / Dikey yap” ve **“Kenara yerleştir”**. Kullanıcının daralttığı
  (▾) kutu daraltılmış kalır, yerleşim hiçbir kutuyu kendiliğinden daraltmaz. Eski (sürüm 1) yerleşim bir kez dönüştürülür ve şu
  bildirim çıkar: “Araç kutuları kenar yerleşimine geçirildi; bir kutuyu sahneye sürükleyerek yüzdürebilirsiniz.”
- Düğmeyi bir kutudan ötekine sürükleyip bırakın (boş alana bırakmak yeni kutu açar); köşedeki menüden “Özelleştir” (varsayılan
  kutularda olmayan komutlar, ör. “Kesit öner ve uygula”, buradan eklenir), hazır yerleşimler ve “Varsayılana dön” (sayfanın varsayılan
  yerleşimi). Telefonda kutular sahnenin altında kaydırılabilir şerittir.
  Kısayollar tek kaynaktan (araç kutusu komut kaydı) çalışır; tam tablo 3.12'de, sayfada **?** tuşu da gösterir. Soluk düğmelerin
  ipucunda nedeni yazar (ör. Böl / Birleştir için önce çubuk seçin; Deforme için önce çözün).
- **Ölçme:** Uzaklık, açı, alan, eleman boyu, kot farkı, koordinat; imleç düğüme / aks kesişimine / çubuğa yakalanır. Esc yarım ölçümü,
  “Ölçüleri temizle” hepsini siler.
- **Sağ tık (dokunmatikte uzun basma):** elemanın özeti ve komutları: Bilgi (geometri, kesit, yükler, iç kuvvetler, tasarım, metraj,
  yük yolu sekmeli pencere; iğnelenip karşılaştırılabilir; çözümden sonra motorun istasyon iç kuvvetleri ve uç yer değiştirmeleri
  “Motor ayrıntısı” olarak eklenir), Özellikler, Isı haritasında incele, Yük akışı, Tasarım ayrıntısı, Kesit öner ve uygula, Gizle, Yalıt, Sil.
  Klavyede sahneyi seçip Shift+F10. Denetçi açıkken model yeniden çözülürse içeriği tazelenir.
- **Kesit önerisi:** “Kesit öner ve uygula” komutu sağ tıkta tek eleman için; araç kutusunda (Özelleştir ile eklenir) ve masaüstünde
  Tasarım menüsünde seçili elemanlar ya da seçim yoksa bütün model için önerileri D/C önce → sonra ile listeler (sonraki D/C
  “tahmini, mevcut iç kuvvetlerle”; yalnız donatı artışı gereken betonarme kolonda öneri “B30x30-ρ%2.00” gibi görünür). Ara
  kesişimlerde bölünmüş aks–kat kirişi tek öneri olarak görünür (“N parça”; parçalar sahnede birlikte vurgulanır). “Uygula” bir
  öneriyi yazar; aynı kesit ve türde başka çubuklar varsa **“Kesit grubuna uygula (N çubuk)”** grubun ortak önerisini bütün üyelere
  yazar, modeli yeniden çözer ve grubun gerçek D/C'sinin en büyüğünü verir (tek geri al adımı). “Hepsini uygula” en çok 3 turda
  uygular ve yeniden çözer (aynı kesit ve türdeki çubuklara grubun en ağır önerisi); depremli modelde göreli kat ötelemesi sınırını da
  gözetir (gerekirse kesitleri öteleme için büyütür) ve ötelemeyi önce → sonra yazar (“Göreli kat ötelemesi (en büyük δ/h ÷ sınır):
  önce X … → sonra X …”). Beklerken süre notu görünür: “Hesaplanıyor: en çok 4 çözüm, yaklaşık N s” (N görünen çözümün süresinden
  kestirilir). Tarayıcıda (Pyodide) ölçülen süreler: ⟨PYODIDE_SURE⟩. Son çözümde D/C > 1 kalan çubuk varsa ⚠
  uyarısıyla listelenir. Geri al önceki modele döner.
- **📄 Statik Rapor:** çözüm yoksa önce çözer; önizleme, “Yazdır / PDF”, “HTML indir”. Proje künyesi (ad, yer, ada/parsel, hazırlayan…)
  bu tarayıcıda hatırlanır. Tablolar penceresinde onay kutusuyla seçilen tablolar raporun ekine girer. Masaüstünde Rapor › Yazdır…
  (Ctrl+Shift+P) Bina sayfasında statik raporu yazdırır.
- **▦ Tablolar:** model, yük, deprem, analiz, tasarım, temel ve metraj tabloları; sarı hücreler düzenlenebilir, “Uygula” modeli değiştirir
  (Ctrl+Z ile geri alınır; sonuçlar yeniden çözülene kadar eski sayılır). Tablo programından kopyalanan hücreler (sekmeyle ayrılmış)
  etkin hücreden itibaren yapıştırılır; CSV dışa aktarım (BOM, `;`, ondalık virgül). Masaüstünde Dosya › Dışa aktar › Tablolar (.csv)
  ve Rapor › Tabloları CSV kaydet bütün tabloları tek bir CSV dosyasına yazar.
- **CSV içe aktarma:** tablo editöründe “CSV ▾”nin yanındaki **“İçe aktar (.csv)…”** düğmesi (masaüstünde Dosya › İçe aktar ›
  **Tablolar (.csv)…**). Biçim: başta BOM olabilir; ayırıcı `;`, `,` ya da sekme kendiliğinden tanınır. Dosyada `Tablo: başlık;grup;ad`
  bölümleri varsa (dışa aktarılan çok tablolu CSV) her bölüm kendi tablosunu doldurur, yoksa etkin tablo doldurulur. Başlık satırının
  hücreleri sütun başlıklarıyla eşlenir; satırlar anahtar sütunuyla (ör. kiriş no, aks adı), yoksa sırayla eşlenir. Yalnız düzenlenebilir
  hücreler değişir; değişiklikler sarı bekleyen hücreler olarak gelir, “Uygula” ile modele yazılır, Ctrl+Z ile geri alınır. Bilinmeyen
  ya da düzenlenemeyen sütunlar bildirilir.
- **Rapor ve tablo ayrıntıları:** rapor §5'te basit çelik kesitlerin (boru, kutu, korniyer, U) sınıfı da yazılır (ör. “BORU 168.3x6.3:
  basınçta narin olmayan, eğilmede kompakt”, parça oranlarıyla). §10.1 mesnet tablolarında yaylı mesnet (“yaylı mesnet”, k_z = …
  kN/m), diyafram bağlı mesnet (“mesnet (diyafram bağıyla)”) ve elastik temel yayları ayrı türle satırdır; Σ tepki yay kuvvetlerini ve
  mütemadi / radye zemin yaylarını içerir. Genel modelde Duvar Yükleri tablosu duvar taşıyabilen her çubuğu (kiriş, bağ, diğer) listeler:
  duvarsız satırlar “(duvar yok)” ile gelir, Duvar hücresinden seçim o çubuğa duvar atar. Genel metrajın döşeme kalıbı kiriş yüzleri
  arasındaki net alandır (aks–kat ile aynı). Kat ağırlıkları tablosu iki modelde aynı kuralla: her kolonun ağırlığı üst ucundaki kata.
  Genel modelde çubuk adresleri Türkçe tür adıyla yazılır (“Ç13 (kiriş)”).
- **🌡 Isı haritası:** yük durumu, kombinasyon ya da zarf için yer değiştirme, iç kuvvet, gerilme ve kullanım oranı renkleri; döşeme
  panellerinde plak sehimi ve momentleri, radye ve mütemadi temelde taban basıncı ve oturma. Aks–kat ve genel modelde çalışır. Elemana
  dokunun: seçilir, “İncele” ile kesit gerilmeleri. “Tasarım ayrıntısı” Tasarım sekmesine geçer.
- **⬇ IFC:** IFC4 yapı modeli (katlar, aks ızgaraları, elemanlar, kesit ve malzemeler; isteğe bağlı yapısal analiz modeli, yükler ve D/C).
  BIM görüntüleyicilerinde açılır. Yükler: G, Q, S'nin yanında rüzgâr (W±X/Y), deprem (EX±, EY±; EZ, G eylemlerinin katsayılı kopyası)
  ve kren (K…) durumlarının eylemleri her yük durumuna yazılır (çubuk yayılı / tekil yükleri ve düğüm kuvvetleri; rijit diyaframın
  merkezi kendi analiz düğümü “Kat k diyafram merkezi” olarak). Temel öz ağırlığı da yazılır (mütemadi / radyede temel elemanlarına ve
  düğümlerine, tekilde temel başına). Vuteli çubuk: kutu ve U tabanlı vute daralan (değişken kesitli) katı olarak çizilir; boru, korniyer
  ve çift korniyer tabanlı vute sabit kesitle yazılır ve uyarı verir.
- **Proje dosyası:** “💾 Kaydet” `.matris` dosyası indirir (bina + görünüm + araç kutusu yerleşimi); “📂 Aç” `.matris` ya da eski bina
  `.json` dosyasını açar (açma da geri alınabilir). Masaüstü sürümünde Dosya menüsü ve Ctrl+S / Ctrl+O aynı işi yerel dosyayla yapar.

### 3.11 Bina sayfası: aks tabanlı çizim (kolon, kiriş, çapraz, makas, beşik çerçeve, panel)

Serbest koordinatla düğüm çizilmez: her düğüm bir **aks kesişimi** (X × Y × Z aksı) ya da mevcut bir çubuğun **bölme / kesişim
noktasıdır**. Aks taşınınca ona bağlı bütün düğüm ve elemanlar birlikte taşınır. Eski aks–kat şablonları (betonarme, çelik çerçeve…)
aynen açılır, çizilir ve çözülür; aks–kat modelinde kat düzlemindeyken Kolon / Kiriş / Döşeme eski davranışla çalışır.

- **Hızlı aks (Aks kutusu → sihirbaz):** X, Y aralıklarını `4@20`, `6@6, 7.5` gibi yazın ya da tek tek girin; Z sekmesinde kat kotları
  ve ek Z aksları (Saçak, Mahya, Kren…). “Yeni model” boş aks modeli açar (betonarme / çelik); “Mevcut aksları değiştir” aynı adlı
  aksları taşır, olmayanları elemanlarıyla birlikte siler (önce sorar).
- **Aks düzenle / ekle / sil / taşı:** tabloda ad, konum, aralık; sahnede iki aksın arasına dokununca tam ortasına aks eklenir;
  balonu sürükleyerek (0,05 m adım) ya da balona dokunup yeni konumu yazarak taşıyın. Silerken bağlı eleman varsa “elemanlarla sil”
  ya da “en yakın aksa taşı” seçilir. **Aks sistemi:** açılı kartezyen ya da silindirik ek sistemler. **Aks görünürlüğü:** balonlar,
  ölçü zinciri, aks bazında görünür / balon yeri.
- **Düzlem seçici** (üst şerit): plan görünümünde Z aksları, cephede X / Y aksları; PgUp / PgDn komşu düzleme geçer.
- **Çizim:** *Çubuk çiz* (kesişimden kesişime zincir, Esc biter), *Hızlı kolon* (plan: kesişime dokunun; “Tüm katlara” en alttan bu
  düzleme; cephe: düşey aks parçası), *Hızlı kiriş* (aks parçasına dokunun ya da sürükleyerek çoklu), *Hızlı çapraz* (göze dokunun;
  X, tek /, tek \, V, ters V, K, dışmerkez, diz — K ve yalnız çekme seçeneklerinde deprem yönetmeliği uyarısı görünür),
  *Hızlı panel* (betonarme döşeme ya da çatı, sac çatı ya da cephe kaplaması), *Eğik çubuk* (iki farklı Z aksı arasında: mertek, çapraz).
  *Makas*, *Beşik çerçeve*, *Aşık* ve *Kren yolu* önizlemeli pencereyle üretir; gereken Saçak / Mahya / Kren Z aksları ve açıklık
  ortasındaki mahya X aksları kendiliğinden eklenir. Mafsallı gövdeli makasta **“Düzlem dışı tutma”** seçeneği (`yanal_tutma`)
  varsayılan olarak **uç dikmelerini moment sürekli** bırakır (Warren'da ilk / son diyagonal, K makasta ara dikmeler de): bütün gövde
  iki ucu mafsallı olursa üst başlık düzlem dışında mekanizma olur ve çözüm kurulamaz. “Yok” seçilirse bütün gövde mafsallıdır;
  o zaman makasın düzlem dışında aşıklar ya da çaprazlarla tutulması gerekir. Öğretici not: üst başlığın düzlem dışı burkulma boyu
  tutulan noktalar (aşık, çapraz düğümü) arasındaki uzaklıktır; uç dikmesinin sürekliliği yalnız mekanizmayı önler, burkulma boyunu
  kısaltmaz.
- **Mesnet** (ankastre, mafsal, kayıcı, **yaylı (elastik)** ya da kaldır) ve **Yük ata** (G, Q, S durumları). Genel modelde çubuğa
  yayılı / tekil, panele tek bir p (kN/m², aşağı +), düğüme kuvvet; aks–kat modelinde model çevrilmeden kirişe düzgün yayılı q,
  döşemeye g / q, düğüme kuvvet.
  - **Yaylı (elastik)** ön ayarı “Yaylı mesnet” penceresini açar: altı alan `k_x (kN/m)`, `k_y (kN/m)`, `k_z (kN/m)`,
    `k_rx (kN·m/rad)`, `k_ry (kN·m/rad)`, `k_rz (kN·m/rad)` (bina eksenleri); yalnız k_z dolu gelir (10000). Boş bırakılan doğrultu
    serbesttir; yalnız doldurulan yaylar yazılır. Sahnede yaylı mesnet yay (zikzak) simgesiyle çizilir, denetçi rijitlikleri
    (“k_z = 10 000 kN/m”) ve yay kuvvetlerini gösterir.
  - **Rijit diyaframlı kat:** deprem tanımlı ve kat rijit diyaframlıyken (kat seviyesinde kalınlıklı panel varsa) en alt seviye dışındaki
    bir düğüme ux, uy ya da rz mesnedi verilmek istenirse araç sorar: “Olduğu gibi uygula” (mesnet diyafram bağıyla, ceza rijitliğiyle
    uygulanır; o nokta bütün katın yatay hareketini tutar), “Yalnız düşey mesnet (uz, rx, ry)”, “Bu katın diyaframını esnek yap” (mesnet
    yazılır, `analiz.diyafram[kat] = "esnek"`) ya da “Vazgeç”. Eskiden bu durum hata verirdi.
- **Düzenleme / değiştirme:** Taşı, Döndür, Ayna (aks düzlemine göre), Doğrusal dizi, Kopyala / yapıştır (kesişimden kesişime),
  Özellik ata, Mafsal, Yalnız çekme, Böl (eşit parça, uzunluk, oran, aks kesişimlerinde), Kesişimlerde böl, Düzlemle böl, Birleştir,
  Düğüm birleştir, Kesit değiştir, Açı. Çubuğa sağ tık: Böl, Birleştir, Mafsal, Kesit öner ve uygula.
- **Üreteç düzenle:** makas, beşik çerçeve, aşık, kren yolu ve çapraz pencereleri kayıttan dolu açılır; değişiklik üretilen çubukları
  günceller (sağ tık › Üreteci düzenle… ya da Çizim grubundaki “Üreteci düzenle” komutu).
- **Aks–kattan genel modele:** aks–kat modeline çubuk, çapraz, panel ya da mesnet eklemek (ya da üreteç kullanmak) modeli genel (surum 3)
  modele çevirir; uygulama önce sorar, iptal edilirse işlem yapılmaz. Temel ayarı (tekil, mütemadi, radye) olduğu gibi kalır. Temel
  panelindeki not: “Genel modelde temel kirişleri GLOBAL X/Y aks çizgileri boyunca (temel kotunda kolonu olan akslarda), radye GLOBAL
  aks zarfı + taşma üzerinde kurulur. Ek aks sistemindeki kolon tabanları yalnız kirişsiz radyede ağa katılır; mütemadi ve kirişli
  radyede onlara 'mesnetler' ile mesnet verin.” Güncel bir çözüm varsa sahne temel kirişlerini ve radye plağını motorun geometrisinden
  çizer; taban mesnet simgeleri yalnız tekil temelde görünür. Mütemadi / radyede bir taban düğümü ızgara dışına taşınırsa uyarı çıkar
  (Winkler ağının dışında nokta mesnet olur ya da ek sistem kesişiminde kalır).
- **Kat işlemleri ve çatı parapeti:** şablonlarda çatı kirişlerinin duvarı 1,0 m parapettir (`duvar_h = 1.0`; tarayıcıdaki surum 1
  çözümleri de bu parapeti içerir). “+Kat → Üsttekini kopyala” parapeti yeni çatıya taşır; en üst katı silmek onu alttaki (yeniden çatı
  olan) kata geri verir. Dolu bir çatıda **“Alt katı kopyala”** önce sorar (“Çatı katı alttaki katın kopyasıyla değişecek. Devam edilsin
  mi?”) ve çatı kirişlerinin parapetlerini aynı açıklıktaki kirişlerde korur (“Çatı parapetleri korundu (n kiriş).”).
- **Şablon bağlantısı:** `#bina/sablon/<ad>` adresi (ör. derslerdeki “Bina sayfasında aç” bağlantıları) şablonu açar ve seçicide gösterir;
  ad bilinmiyorsa yüklü model ve seçici olduğu gibi kalır, bildirim şablon adlarını listeler (“Şablon bulunamadı: … Şablonlar: …”) ve
  adres `#bina` olur.
- **Yük akışı:** genel modelde akış şeması sütunları Paneller (ve düğüm yükleri) → yatay çubuklar (kirişler) → düşey ve eğik çubuklar
  (kolonlar) → Mesnetler; bantlar panel → çubuk, çubuk → çubuk, çubuk → mesnet, düğüm → çubuk ve düğüm → mesnet aktarımlarıdır (her
  düğümde giren = çıkan). Bant ipucunda kN ve durum yazar; çok büyük modelde en büyük bantlar gösterilir (not düşer). Eleman bilgisinin
  **Yük yolu** sekmesi üç küme verir: “Panellerden aktarılan paylar”, “Çubuklardan ve düğüm yüklerinden gelen” ve “Aktardığı” (bu
  çubuğun yükünü verdiği çubuk ve mesnetler).
- **3B çizimde:** çubuklar türüne göre renklenir, mafsallı uç içi boş daire, yalnız çekme kesikli çizgi, paneller yarı saydam
  (sac ince çizgi), mesnetler ve ek yükler simgeyle gösterilir. Kaydet / Aç, Ctrl+Z, tablolar, rapor, ısı haritası ve IFC genel
  modelde de çalışır.
- **Genel modelin yapabildikleri ve sınırları:** G, Q, S, W (panel normaline rüzgâr), E (TBDY eşdeğer deprem, kat seviyeleri Z
  aksının `kat` işaretinden), kren (K durumu ve konum alt durumları), yalnız çekme çubukları (birleşim başına yinelemeli çözüm),
  uç serbestlikleri, vuteli ve basit çelik kesitler (boru, kutu, korniyer, U), betonarme ve çelik tahkik, kesit önerisi, yük akışı,
  rapor, tablolar, ısı haritası ve IFC; tekil, mütemadi ve radye temel (GLOBAL aks ızgarasında); yaylı ve diyafram bağlı mesnetler.
  Sınırlar: en çok 2000 serbestlik; mütemadi temelde ve kirişli radyede ek aks sistemindeki tabanlar ağa katılmaz (`mesnetler` ile
  mesnet verilir); ısı haritasının plak alanı yalnız yatay, dört köşeli, eksenlere paralel döşeme panellerinde; ikinci mertebe etkileri
  ve kapasite tasarımı yok.

### 3.12 Klavye kısayolları

Bina sayfasında geçerlidir; yazı alanı ya da bir pencere açıkken çalışmaz. Liste araç kutusunun komut kaydından ve sayfa tuşlarından
(Esc, Shift+F10, Enter, ?, PgUp / PgDn, F, Shift+F, Ctrl+Shift+Z, Backspace) üretilir: aynı satırlar Bina sayfasında **?** tuşuyla
açılan pencerede, Yardım sayfasındaki “Klavye kısayolları” kartında ve masaüstünde **Yardım › Klavye kısayolları** penceresindedir;
araç kutusu düğmesinin üstünde beklemek de kısayolu gösterir.

| Tuş | İş | Tuş | İş |
|---|---|---|---|
| `S` | Seç | `M` | Taşı |
| `L` | Çubuk çiz (kesişimden kesişime) | `Shift+R` | Döndür |
| `Shift+L` | Hızlı çubuk (aks parçası) | `B` | Böl |
| `K` | Hızlı kolon | `J` | Birleştir |
| `R` | Hızlı kiriş | `Shift+J` | Düğümleri birleştir |
| `X` | Hızlı çapraz | `Ctrl+C` / `Ctrl+V` | Kopyala / yapıştır (kesişimden kesişime) |
| `D` | Hızlı panel / döşeme | `Del` (`Backspace`) | Seçileni sil (seçim yoksa Sil aracı) |
| `E` | Eğik çubuk | `Ctrl+Z` | Geri al |
| `W` | Duvar | `Ctrl+Y` (`Ctrl+Shift+Z`) | Yinele |
| `Shift+M` | Mesnet | `Ctrl+Enter` | Çöz |
| `Y` | Yük ata | `1` `2` `3` `4` | 3B, plan, ön (cephe), yan (kesit) görünüm |
| `G` | Aks verisi düzenle | `F` | Tam ekran (Esc ya da F ile çıkılır) |
| `Shift+G` | Hızlı aks sihirbazı | `Shift+F` | Modeli sığdır |
| `PgUp` / `PgDn` | Düzlem yukarı / aşağı (aks–kat çiziminde kat) | `U` | Uzaklık ölç |
| `Shift+F10` | Seçili elemanın bağlam (sağ tık) menüsü | `Esc` | Kipten çık, seçimi ya da yarım çizimi / ölçümü bırak; tam ekrandan çık |
| `?` | Kısayol listesi | `Enter` | Bağlam menüsünde: Bilgi |

Yalnız masaüstü sürümünde (menü kısayolları; macOS'ta Ctrl yerine ⌘). **Yardım › Klavye kısayolları** önce bu “Menü” listesini, Bina
sayfası bir kez açıldıktan sonra da “Bina sayfası — <grup>” bölümlerini (araç kutusu komutları ve sayfa tuşları; “Enter — Bağlam
menüsünde: Bilgi” dahil) gösterir:

| Tuş | İş | Tuş | İş |
|---|---|---|---|
| `Ctrl+N` / `Ctrl+O` | Yeni proje / aç | `F5` | Çöz |
| `Ctrl+S` / `Ctrl+Shift+S` | Kaydet / farklı kaydet | `F6` | Tasarım: tüm kontroller |
| `Ctrl+Shift+N` | Yeni pencere | `F9` | Statik hesap raporu |
| `Ctrl+E` | IFC dışa aktar | `Ctrl+T` | Tablolar (düzenle, yapıştır) |
| `Ctrl+P` | Raporu PDF olarak kaydet | `Ctrl+Shift+H` | Isı haritası |
| `Ctrl+Shift+P` | Yazdır (Bina sayfasında statik rapor) | `Ctrl+G` | Aks verisini düzenle |
| `Ctrl+1` … `Ctrl+4` | Hesapla, Dersler, Sonlu eleman, Bina | `Ctrl+Shift+F` | Modeli sığdır |
| `F1` | Dersler | `Ctrl+Shift+T` | Araç kutularını göster / gizle |
| `F11` | Tam ekran (pencere) | `Ctrl+,` | Ayarlar |

---

## 4. Derste kullanım önerileri

- **Dersteki örneği aynı sayılarla yeniden çöz.** Hoca tahtada ne yazdıysa form alanına aynısını yaz;
  adımları tahtadakiyle satır satır karşılaştır. Fark varsa hangi adımda ayrıldığını görürsün.
- **Önce elle, sonra uygulama.** Kağıtta çöz, ardından `goster="adimlar"` ile kontrol et. Sadece sonuca
  bakma; ara adımlardaki pivot, katsayı ve işaretleri karşılaştır.
- **Yöntemleri karşılaştır.** Aynı sistemi `yontem="gauss"`, `"cramer"`, `"ters"` ile çöz; hepsinin aynı
  sonuca farklı yoldan gittiğini gör. Determinantta `"kofaktor"` ile `"eliminasyon"` aynı şekilde.
- **Sembolikten sayısala.** Rijitlik matrislerini önce `E, A, L` harfleriyle kur, formülü gör; sonra
  sayıları koy. Sınavda formülü hatırlamak böyle kolaylaşır.
- **Sınav öncesi hızlı kontrol:** `mo.ayarla(goster="sonuc")` deyip çözdüğün soruların yalnız sonucunu
  karşılaştır; takıldığın soruda `goster="adimlar"` ile aç.
- **Python öğrenirken:** `goster="python"` ile yalnız kodu ve çıktıyı gör; kodu kopyalayıp serbest
  çalışma alanında değiştirerek dene (`@` ile `*` farkı, `np.linalg.solve`, `np.ix_`).
- **Büyük matrislerde** (6×6'dan büyük) eleman eleman anlatım kısaltılır, yalnız ilk eleman örnek
  gösterilir; ödev için `mo.ayarla(en_fazla_eleman=100)` ile açabilirsin.

---

## 5. Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| `RuntimeError: Önce '🔧 1) Kurulum' hücresini çalıştırın.` (serbest çalışma hücresinde `ModuleNotFoundError: No module named 'matris_ogren'`) | Kurulum hücresi çalıştırılmadı ya da oturum sıfırlandı | En üstteki Kurulum hücresini çalıştır |
| `Satırların eleman sayıları farklı: [2, 1]. Her satırda aynı sayıda eleman olmalı.` | Bir satırda eksik/fazla eleman | Her satıra aynı sayıda eleman yaz; `;` ile satır ayırdığını kontrol et |
| `Boyutlar farklı (1x2 ve 1x3); toplama/çıkarma tanımsız.` | Toplanan matrisler aynı boyutta değil | Boyutları eşitle |
| `A (2x3) · B (2x2) tanımsız: A'nın sütun sayısı (3) B'nin satır sayısına (2) eşit olmalı.` | Çarpımda iç boyutlar uymuyor | Sırayı değiştir (B·A?) ya da matrisi kontrol et; uyarı kutusu da aynı şeyi anlatır |
| `A kare değil (2x3); bu işlem yalnız kare matrisler için tanımlıdır.` | Determinant/ters/özdeğer kare olmayan matrise istendi | Kare matris ver |
| `A tekil (det = 0); tersi yoktur.` | Satırlar/sütunlar doğrusal bağımlı (örn. `1 2; 2 4`) | Tersi yoktur; FEM'de bu genellikle **mesnet uygulanmamış** K demektir → `sinir_kosulu` kullan |
| `Sistem tutarsız: çözüm yok.` | A x = b'de `0 = c` çelişkisi çıktı | Girdiyi kontrol et; sistem gerçekten çözümsüz olabilir (mesnetsiz bir K'yı `coz` ile çözmeye çalıştıysan `sinir_kosulu` kullan) |
| `Yetersiz mesnet: indirgenmiş K_s matrisi tekil (rank 1 < 2); ...` ya da `Hiç mesnet verilmedi (sabit = []): K matrisi tekil ...` | `sinir_kosulu`'nda tutulu SD'ler yapıyı yerinde tutmaya yetmiyor; yapı rijit cisim gibi hareket edebilir (mesaj kaç bağımsız rijit cisim hareketinin kaldığını söyler) | Daha fazla SD sabitle (örn. `sabit=[1]`); yükler dengede olsa bile mesnetsiz yapıda yer değiştirmeler tek değildir |
| ⚠️ *sonsuz çözüm* uyarısı ve `{(1 - 2*x2, x2)}` gibi genel çözüm | Pivot sayısı bilinmeyen sayısından az (K tekil) | FEM'de sınır koşullarını uygula; aksi halde genel çözüm doğru cevaptır |
| `A 2 satırlı ama b 3 elemanlı; satır sayıları eşit olmalı.` | Sağ taraf vektörü eksik/fazla | b'nin eleman sayısı = A'nın satır sayısı |
| `Cramer yöntemi burada yalnız 1×1–3×3 kare sistemler için gösterilir.` | 4×4 ve üstünde Cramer istendi | `yontem="gauss"` kullan |
| `Eleman anlaşılamadı: 'E A/L' ...` ya da matris yanlış kuruldu | Sembolik ifadede boşluk | `E*A/L` yaz (çarpma işaretiyle, boşluksuz) |
| `Geçersiz karakter içeren eleman: '$'` | İzin verilmeyen karakter | Yalnız sayı, harf, `+ - * / ^ ( ) . , ;` kullan |
| `Eleman 1: serbestlik numaraları 1..3 arasında olmalı.` | `birlestir`'de SD numarası aralık dışı | SD numaraları 1'den başlar ve `n_serbestlik`'i aşamaz |
| `Tüm serbestlik dereceleri (SD) sabit; çözülecek bilinmeyen yok.` | `sinir_kosulu`'nda hepsi sabitlendi | En az bir SD serbest kalmalı |
| `Bilinmeyen ayar: ...` / `goster='...' geçersiz` | Ayar adı ya da mod yanlış yazıldı | Geçerli adlar: `ondalik basamak en_fazla_eleman python kural goster`; modlar: `hepsi adimlar python sonuc yok` |
| Çıktı kesir olarak geliyor, ondalık istiyorum | Varsayılan kesin gösterim | `mo.ayarla(ondalik=True, basamak=4)` |
| Hücre uzun süre "çalışıyor" ya da "Bağlantı kesildi" | Colab oturumu kapandı (uzun süre kullanılmayınca olur) | **Çalışma zamanı → Oturumu yeniden başlat** (Runtime → Restart session), sonra **Kurulum**'u tekrar çalıştır |
| Formüller düzgün görünmüyor (ham `\begin{bmatrix}` metni) | Çıktı Colab dışında (düz Python) alındı | Colab/Jupyter'de çalıştır; düz terminalde anlatım Markdown metni olarak basılır |
| colab-mcp görünmüyor / "Colab'a bağlan" çalışmıyor | Claude Code yeniden başlatılmadı ya da tarayıcıda Google girişi yok | Claude Code'u kapatıp aç, `claude mcp list` ile `Connected` gör, tarayıcıda Google hesabına gir, 60 sn içinde bağlantıyı bekle |
| `Bina ağı … serbestlik derecesi; tarayıcıda çözüm için en fazla 1500.` (genel modelde `Model … en fazla 2000.`) | Model çözüm sınırını aşıyor: aks–kat 12×12 aks, 12 kat, 1500 SD; genel model 2000 SD | Aks ya da kat sayısını azaltın; genel modelde gereksiz bölme düğümlerini birleştirin, vute parça sayısını düşürün (`analiz.vute_parca`) |
| `Mütemadi temel: taban düğümü N (…) GLOBAL X/Y aks kesişiminde değil (ek aks sistemi). Temel kirişleri yalnız GLOBAL akslar boyunca kurulur: …` (kirişli radyede `Kirişli radye: …`) | Genel modelde bir kolon tabanı ek aks sistemindeki bir kesişimde; temel kirişi ağı yalnız GLOBAL aks çizgilerinde kurulur | O düğüme `mesnetler` listesiyle mesnet verin, kirişsiz radye ya da tekil temel seçin |
| `Düğüm N (A1/T) açık mesnetli ('mesnetler') ve mütemadi temel ağının üzerinde. Açık mesnedi kaldırın (düğüm temele oturur) ya da tekil temel seçin.` (radyede `radye ağının`) | Temel ağına bağlanan bir düğüme ayrıca açık mesnet verilmiş | Açık mesnedi kaldırın ya da tekil temel seçin |
| `Mütemadi temel: taban düğümü N (…) temel ağına bağlanmadı (altında temel kirişi yok). …` | Taban düğümünün aksı `temeller.surekli.akslar` listesinde değil ya da temel kirişleri tek doğrultuda (`yon` x / y) | Aksı listeye ekleyin, `yon = 'xy'` seçin ya da düğüme `mesnetler` ile mesnet verin (kolon taşımayan düğümde: temel kirişinin uçları kolonlara göre belirlenir) |
| `temeller.tip = 'radye': temele oturan aks kesişimi yok (en alt seviyede çubuk ucu olan aks kesişimi bulunmadı); …` | En alt Z seviyesinde çubuk ucu olan aks kesişimi yok (kolonlar bölme düğümünde ya da üst seviyede başlıyor) | Kolon tabanlarını en alt seviyedeki aks kesişimlerine bağlayın |
| `mesnetler[k]: uz hem tutulu hem yaylı verilemez (kz).` / `mesnetler[k]: kz pozitif bir sayı olmalı (kN/m ya da kN·m/rad).` | Yaylı mesnette aynı doğrultu hem tutulmuş hem yay verilmiş, ya da yay rijitliği ≤ 0 / sayı değil | O doğrultunun tutulmasını kaldırın (`uz: false`) ya da yayı silin; rijitliği pozitif sayı yazın |
| `Döşeme … 'yüzen döşeme': … kenarı (…) üzerinde kiriş yok.` | Aks–kat döşemesinin bir kenarında kiriş yok; yük aktarılacak eleman yok | Eksik kirişleri ekleyin (Hızlı kiriş) ya da döşemeyi silin |
| `… hiçbir çubuğa bağlı değil (yüzen düğüm)` | Genel modelde panel köşesi, mesnet ya da düğüm yükü çubuğa bağlı olmayan bir düğümde | Düğüme çubuk çizin ya da yükü / mesneti bağlı bir düğüme taşıyın |
| Bina sayfasında komut düğmesi soluk | Komutun ön koşulu yok (çözüm, seçim, ölçü…) | Düğmenin ipucundaki nedene bakın (ör. "Önce modeli çözün (Çöz ▶)") |
| Isı haritasında döşeme plağı görünmüyor (genel model) | Plak alanı yalnız yatay, dört köşeli, eksenlere paralel `doseme` panellerinde kurulur | Çatı / cephe panelleri ve eğik paneller notla atlanır; çubuk alanları yine gösterilir |

---

## 6. Geliştirici notu

Klasör: `$env:USERPROFILE\Desktop\matris_ogren`

| Dosya | Görev |
|---|---|
| `matris_ogren.py` | Modül (sympy tabanlı; anlatım + Python kodu üretimi). Sürüm: `mo.__version__` |
| `sonlu_eleman.py`, `yapi.py`, `yapi_serbest.py`, `yapi_veri.py`, `tasarim.py`, `temel.py`, `rapor.py`, `tablolar.py`, `alan.py` | Sonlu eleman ve bina modülleri (3.8, 3.9) |
| `defter_yap.py` | `Matris_Ogren.ipynb` defterini üreten betik (on modülü zlib + base64 ve SHA-256 özetiyle gömer; ek paket gerekmez, nbformat kuruluysa şemaya göre doğrular) |
| `Matris_Ogren.ipynb` | Colab defteri (üretilmiş dosya; elle düzenlenmez, `defter_yap.py` ile yeniden üretilir; `testler/test_defter.py` gömülü her modülün özetini ve baytlarını dosyasıyla karşılaştırır, iki üretimin aynı çıktığını denetler) |
| `web_yap.py` | `docs/` klasörünü üretir: kökteki modülleri `docs/`'a kopyalar, dersleri derler (`docs/dersler.json`), `docs/sw.js` ve `docs/surum.json`'a sürüm damgası basar (yalnız izlenen dosyalardan; `__pycache__` sayılmaz) |
| `ders_derle.py` | `dersler/*.md` derslerini `dersler/BICIM.md` kurallarına göre denetler (`--denetle`) ve derler |
| `docs/` | Web uygulaması (PWA). `docs/*.py` kopyadır (elle düzenlenmez), yalnız `docs/web_kopru.py` (köprü) kaynaktır |
| `masaustu\` | Masaüstü sürümü (Node.js 22; `npm ci`, `npm run hazirla`, `npm start`; bkz. `masaustu/README.md`) |
| `testler\` | pytest testleri; `testler\js\` node testleri (`node --test`) |
| `.github/workflows/testler.yml` | Her itmede ve çekme isteğinde: `web_yap.py` sonrası `docs/` farkı yok mu, ders denetimi, pytest, node testleri |
| `KULLANIM.md`, `TASARIM.md` | bu kılavuz; tasarım bölümleri (§1–§19) ve veri şemaları haritası |

Yerel Python 3.12'de sympy/IPython/nbformat yok; **her zaman uv reçetesi** kullanılır
(PowerShell 5.1: `&&` yok, `;` kullan; yolda boşluk var, çift tırnak şart):

```powershell
Set-Location "$env:USERPROFILE\Desktop\matris_ogren"
$uv = "$env:USERPROFILE\.local\bin\uv.exe"

# Hızlı kontrol
& $uv run --python 3.13 --with sympy --with numpy python -c "import matris_ogren as mo; mo.ayarla(goster='sonuc'); print(mo.carp('1 2; 3 4','5 6; 7 8').deger)"

# Gömülü on modülden biri değişince defteri yeniden üret
& $uv run --python 3.13 python defter_yap.py

# Testleri çalıştır
& $uv run --python 3.13 --with sympy --with numpy --with ipython --with nbformat --with nbconvert --with ipykernel --with pytest python -m pytest testler -q
```

Defteri yeniden ürettikten sonra Colab'daki kopyayı da güncelle (Yol A: yeniden yükle; Yol B: Drive'daki
dosyanın üzerine yaz).

Linux / macOS (ya da Python paketleri kurulu herhangi bir ortam), proje klasöründen:

```bash
python3 web_yap.py                                   # kökteki bir modül ya da ders değişince docs/'u güncelle
python3 ders_derle.py --denetle                      # ders biçimi
python3 -m pytest testler -q                         # Python testleri (numpy, sympy, pytest, pyyaml)
node --test testler/js/*.test.js                     # JavaScript testleri (Node.js 22)
python3 defter_yap.py                                # gömülü on modülden biri değişince defteri yeniden üret
```

`docs/*.py` kopyaları ve derlenmiş dersler (`docs/dersler.json`) kaynaklarla aynı tutulur; CI `web_yap.py`'den sonra `docs/` altında
fark kalmamasını ister (`docs/sw.js` ve `docs/surum.json` hariç).
