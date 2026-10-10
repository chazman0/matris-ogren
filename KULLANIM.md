# Matris Öğren — Kullanım Kılavuzu

Sonlu elemanlar dersi için **adım adım matris hesaplayıcı**. Bir matris yazarsın; uygulama önce o işlemin
**kuralını** ve **elle nasıl yapıldığını** (her ara hesapla birlikte) gösterir, sonra aynı işi yapan
**🐍 Python kodunu ve gerçek çıktısını** verir. Böylece hem matematiği hem Python'u aynı ekranda öğrenirsin.

Uygulama iki parçadan oluşur:

| Parça | Dosya | Ne işe yarar |
|---|---|---|
| Colab defteri | `Matris_Ogren.ipynb` | Tarayıcıda açılır, kurulum gerektirmez; bölüm bölüm form alanlarıyla çalışılır |
| Python modülü | `matris_ogren.py` | Hesapları yapan ve anlatan asıl kod; defter bunu `mo` kısaltmasıyla kullanır |

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
- Transpoz, iz, rank (rank için ayrı form yok; Bölüm 11'deki serbest çalışma alanında `mo.rank(...)` ile)
- Determinant (2×2 ve 3×3'te kofaktör açılımı, daha büyüklerde satır indirgeme)
- Ters matris (2×2 formülü, genel Gauss–Jordan)
- Denklem sistemi çözümü **A x = b** (Gauss eliminasyonu, Cramer, ters matris yöntemi)
- Özdeğer–özvektör ve **K φ = ω² M φ** doğal frekans problemi
- Sonlu elemanlar: çubuk, kiriş (Euler–Bernoulli, 4×4) ve düzlem kafes elemanı rijitlik matrisleri,
  **birleştirme (assembly)**, **sınır koşulları**, yer değiştirme çözümü ve **mesnet tepkileri**

Hesaplar **kesin** yapılır: `0.5` yazarsan `1/2` olarak saklanır, sonuçlar kesir olarak çıkar (istersen
ondalık gösterime çevirebilirsin, bkz. Ayarlar). Harfler (E, A, L, I, k, P …) **sembol** olarak kalır;
yani `E*A/L` gibi sembolik rijitlik matrisleriyle de çalışabilirsin — derste tahtadaki haliyle.

---

## 2. Defteri Colab'da açma (3 yol)

### Yol A — Dosya yükleyerek (en hızlısı)

1. [colab.research.google.com](https://colab.research.google.com) → **Dosya → Not defteri yükle** (File → Upload notebook).
2. Bilgisayarından `C:\Users\Tunay Gülden\Desktop\matris_ogren\Matris_Ogren.ipynb` dosyasını seç.
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
  → `C:\Users\Tunay Gülden\.local\bin\colab-mcp.exe`
- Claude Code'a kullanıcı kapsamında (tüm projelerde geçerli) kaydedildi:
  `claude mcp add --scope user colab-mcp -- "C:\Users\Tunay Gülden\.local\bin\colab-mcp.exe"`
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

Defterin en üstündeki **Kurulum** hücresi `matris_ogren` modülünü Colab oturumuna kurar ve `mo` adıyla
hazır eder. **Her açılışta bir kez** çalıştırılır. Çalıştırmadan form hücreleri
`RuntimeError: Önce '🔧 1) Kurulum' hücresini çalıştırın.` hatası verir (Bölüm 11'deki serbest çalışma hücresi ise
`ModuleNotFoundError: No module named 'matris_ogren'` der).

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
| 11 | Serbest çalışma alanı | tüm işlevler (`rank` yalnız buradan: `mo.rank(...)`) |

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

---

## 6. Geliştirici notu

Klasör: `C:\Users\Tunay Gülden\Desktop\matris_ogren`

| Dosya | Görev |
|---|---|
| `matris_ogren.py` | Modül (sympy tabanlı; anlatım + Python kodu üretimi). Sürüm: `mo.__version__` |
| `defter_yap.py` | `Matris_Ogren.ipynb` defterini üreten betik |
| `Matris_Ogren.ipynb` | Colab defteri (üretilmiş dosya; elle düzenlenmez, `defter_yap.py` ile yeniden üretilir) |
| `testler\` | pytest testleri |
| `KULLANIM.md` | bu kılavuz |

Yerel Python 3.12'de sympy/IPython/nbformat yok; **her zaman uv reçetesi** kullanılır
(PowerShell 5.1: `&&` yok, `;` kullan; yolda boşluk var, çift tırnak şart):

```powershell
Set-Location "C:\Users\Tunay Gülden\Desktop\matris_ogren"
$uv = "C:\Users\Tunay Gülden\.local\bin\uv.exe"

# Hızlı kontrol
& $uv run --python 3.13 --with sympy --with numpy python -c "import matris_ogren as mo; mo.ayarla(goster='sonuc'); print(mo.carp('1 2; 3 4','5 6; 7 8').deger)"

# Modül değişince defteri yeniden üret
& $uv run --python 3.13 --with sympy --with numpy --with ipython --with nbformat --with nbconvert --with ipykernel --with pytest python defter_yap.py

# Testleri çalıştır
& $uv run --python 3.13 --with sympy --with numpy --with ipython --with nbformat --with nbconvert --with ipykernel --with pytest python -m pytest testler -q
```

Defteri yeniden ürettikten sonra Colab'daki kopyayı da güncelle (Yol A: yeniden yükle; Yol B: Drive'daki
dosyanın üzerine yaz).
