# Sonlu Elemanlar Öğretim Programı — Mühendislik İçeriği Planı (taslak, 10.10.2026)

## 1. Hedef kitle ve öğrenme çıktıları

**Hedef kitle:** yapı mühendisliği yüksek lisans öğrencisi; "Sonlu Elemanlar Yöntemi" / "Yapı Mekaniğinde Matris Yöntemler" dersini izlerken ve tezinde (OMA + FEM, yığma köprü) kullanacak. Ön bilgi: mukavemet, yapı statiği, uygulamanın mevcut matris modülü.

**Tipik ders akışıyla hizalama:**

| Blok | Ders konusu | Uygulama modülü |
|---|---|---|
| 1–2 | Direkt rijitlik yöntemi, çubuk | mevcut `cubuk_eleman`, `birlestir`, `sinir_kosulu` |
| 3–4 | Düzlem kafes, dönüşüm matrisi | `kafes_eleman` + iç kuvvet geri hesabı |
| 5–6 | Kiriş, çerçeve, yayılı yük, mesnet çökmesi, sıcaklık | `kiris_eleman` → `cerceve_eleman` |
| 7 | Enerji ilkeleri, Rayleigh–Ritz, Galerkin, şekil fonksiyonu türetimi | `sekil_fonksiyonu` (sembolik) |
| 8–9 | Düzlem gerilme / şekil değiştirme (plane stress / strain), CST, Q4 | `cst_eleman`, `q4_eleman` |
| 10–11 | İzoparametrik formülasyon, Gauss integrasyonu, Q8 | `gauss_integrasyon`, `q8_eleman` |
| 12 | Plak / kabuk giriş | `plak_eleman` (ileri) |
| 13–14 | Dinamik: kütle matrisi, özdeğer, mod şekli, Rayleigh sönüm | mevcut `ozdeger` + `kutle_matrisi`, `rayleigh_sonum` |

**Öğrenme çıktıları (ölçülebilir):**
- ÖÇ1 Şekil fonksiyonlarından eleman rijitlik ve kütle matrisini elle türetir; uygulama çıktısıyla doğrular.
- ÖÇ2 ≤ 12 SD'li sistemi kâğıtta kurar ve çözer; tepkileri dengeyle denetler.
- ÖÇ3 Yerel–global dönüşümü, SD numaralamayı ve birleştirmeyi hatasız uygular.
- ÖÇ4 Yayılı yük, sıcaklık, mesnet çökmesi için eşdeğer düğüm yüklerini türetir; N, V, M'yi geri hesaplar.
- ÖÇ5 İzoparametrik elemanda Jakobiyen ve Gauss noktalarıyla K'yı integre eder; yama testi (patch test) uygular.
- ÖÇ6 Genelleştirilmiş özdeğer problemini çözer, modları kütle-normalize eder, iki mod setini MAC ile karşılaştırır.
- ÖÇ7 (tez bağı) Yığma kemeri poligonal çerçeve ve düzlem şekil değiştirme makro-modeli olarak kurar; E ve ρ'nun frekansa duyarlılığını hesaplar; HBIM/IFC geometrisini düğüm–eleman listesine çevirme adımını tanır.

## 2. Eleman kütüphanesi yol haritası

Ortak şablon: SD → şekil fonksiyonu → K (kapalı form / sayısal integrasyon) → M (yığılı, lumped / tutarlı, consistent) → T → iç kuvvet → doğrulama örneği. Semboller: E, A, I, L, G, J, ν, t, ρ, α.

| Aşama | Eleman | SD | Şekil fonksiyonu | K | M | T | İç kuvvet | Doğrulama örneği |
|---|---|---|---|---|---|---|---|---|
| 1 | 2B çubuk | 2 | lineer N₁=1−ξ, N₂=ξ | kapalı (EA/L)[1 −1; −1 1] | yığılı ρAL/2·I; tutarlı (ρAL/6)[2 1; 1 2] | — | N = EA(u₂−u₁)/L | kademeli çubuk (Logan); sabit-serbest çubuk ω_n = (2n−1)π/(2L)·√(E/ρ) |
| 1 | 2B kafes | 4 | lineer | kapalı, TᵀkT | 4×4 tutarlı | 2×4 (c, s) | N = (EA/L)[−c −s c s]·u | üç çubuklu kafes (Logan, Hutton); ∑F = 0 |
| 2 | Euler–Bernoulli kiriş | 4 | Hermite kübik | kapalı (EI/L³)[12 6L −12 6L; …] | tutarlı (ρAL/420)[156 22L 54 −13L; …]; yığılı ρAL/2, dönme 0 | — | M = EI·v″, V = EI·v‴; f = k·u − f_eq | konsol PL³/3EI; basit kiriş 5qL⁴/384EI; ankastre uç momenti qL²/12; konsol β₁L = 1,8751, β₂L = 4,6941 |
| 2 | 2B çerçeve | 6 | lineer + Hermite | kapalı; Timoshenko seçeneği Φ = 12EI/(κGAL²): 12→12/(1+Φ), 4L²→(4+Φ)L²/(1+Φ), 2L²→(2−Φ)L²/(1+Φ) | 6×6 tutarlı | 6×6 | N, V, M diyagramı | portal çerçeve (Kassimali; McGuire–Gallagher–Ziemian); kısa kirişte EB–Timoshenko farkı |
| 2 | Çerçeve ekleri | — | — | mafsal: statik yoğunlaştırma (3EI/L³ biçimi); rijit kol: ofsetli T; elastik mesnet: köşegene k; ızgara (grid) elemanı GJ ile 6 SD (isteğe bağlı) | — | — | — | mafsallı çerçeve el hesabı; yay mesnetli kiriş |
| 3 | 3B kafes | 6 | lineer | kapalı | tutarlı | 2×6 doğrultu kosinüsleri | N | uzay kafes (Logan) |
| 3 | 3B çerçeve | 12 | lineer + 2 Hermite + burulma | kapalı (GJ, Iy, Iz) | 12×12 tutarlı | 12×12; düşey eleman için yardımcı vektör kuralı | N, Vy, Vz, T, My, Mz | uzay çerçeve (Logan; McGuire–Gallagher–Ziemian) |
| 4 | CST | 6 | alan koordinatları, lineer | kapalı tA·BᵀDB; D düzlem gerilme / şekil değiştirme | tutarlı (ρtA/12)[2 0 1 0 1 0; …] | — | σ = DBu (eleman sabiti) | Logan CST örneği; yama testi; konsol plakta aşırı rijitlik, yavaş yakınsama |
| 4 | Q4 | 8 | bilineer, izoparametrik (ξ, η) | 2×2 Gauss, \|J\| | ∫ρNᵀN dV | — | Gauss noktalarında σ → düğüme ekstrapolasyon | yama testi; düzgün çekme (kesin); eğilmede kayma kilitlenmesi (shear locking); 1 noktalı integrasyonda kum saati (hourglass) modları |
| 5 | Q8 (serendipity) | 16 | kuadratik | 3×3 Gauss (2×2 indirgenmiş: uyarıyla) | tutarlı | — | Gauss noktaları | konsol: Q4'e kıyasla yakınsama; eğri kenarda Jakobiyen |
| 6 | Plak | 12 | Kirchhoff: ACM uyumsuz kübik; Mindlin: bilineer + kayma (seçici indirgenmiş integrasyon / MITC4) | Kirchhoff kapalı; Mindlin sayısal | tutarlı | — | Mx, My, Mxy, Qx, Qy | basit mesnetli kare plak (Timoshenko & Woinowsky-Krieger tablosu) |
| 7 | Düz kabuk | 24 | Q4 membran + Mindlin plak süperpozisyonu; dönme-6 (drilling) SD sorunu | sayısal | tutarlı | 24×24 | N + M | MacNeal–Harder test seti (Scordelis–Lo çatı, sıkıştırılmış silindir) — yalnız gösterim |
| 8 | 3B katı giriş | Tet4 12, Hex8 24 | lineer / trilineer | Tet4 kapalı; Hex8 2×2×2 Gauss | tutarlı | — | 6 bileşenli σ, von Mises | tek eksenli blok; 3B yama testi; konsol yakınsaması |

**Dinamik katman (her aşamaya paralel):** M seçimi (tutarlı/yığılı); Kφ = ω²Mφ (mevcut `ozdeger`); yığılı M'de dönme kütlesi 0 → M tekil → dönme SD'leri Guyan yoğunlaştırmasıyla atılır ya da tutarlı M kullanılır (öğretici not); kütle-normalizasyon φᵀMφ = 1; Rayleigh sönüm C = a₀M + a₁K, eşit ξ için a₀ = 2ξω_iω_j/(ω_i+ω_j), a₁ = 2ξ/(ω_i+ω_j); basit kiriş ω_n = (nπ/L)²√(EI/ρA) doğrulaması.

**Yığma / HBIM bağı:** kemer → poligonal çerçeve (aşama 2; Heyman itme çizgisi el kontrolü); kemer + dolgu → düzlem şekil değiştirme Q4/Q8 makro-modeli (aşama 5; homojenleştirilmiş E, ρ); hafifletme odacığı → ağ geometrisi parametresi (odacıklı / dolu kesit frekans farkı); 3B katı yalnız kavram (aşama 8). Tam köprü modeli uygulamanın değil tez çözücüsünün (ANSYS/Abaqus) işidir.

## 3. Yükler, mesnetler, sınır koşulları

- **Düğüm yükleri:** F'ye doğrudan; moment → dönme SD'si.
- **Yayılı yük (düzgün, lineer, eleman içi tekil):** f_eq = ∫Nᵀq dx (sembolik türetim gösterilir); düzgün q için [qL/2, qL²/12, qL/2, −qL²/12]; iç kuvvette f = k·u − f_eq düzeltmesi zorunlu.
- **Sıcaklık:** düzgün ΔT → yerel f_T = EAαΔT·[−1, 1]ᵀ; kesit gradyanı → uç momentleri EIαΔT/h; serbest uzamada iç kuvvet sıfır (test).
- **Mesnet çökmesi:** bilinen u_s ≠ 0; K_ff·u_f = F_f − K_fs·u_s; tepkiler R = K_sf·u_f + K_ss·u_s − F_s.
- **Eğik mesnet:** düğüm SD'sini mesnet eksenine döndüren yerel dönüşüm veya MPC.
- **Elastik yay (öteleme / dönme):** köşegene k; zemin için Winkler yayı.
- **Çoklu nokta kısıtı (MPC):** rijit bağ, eşit yer değiştirme. Üç yöntem yan yana: efendi–köle eliminasyonu (kesin, boyut küçülür), ceza (penalty; büyük k_p koşullanmayı bozar → uyarı), Lagrange çarpanı (sistem büyür, köşegende sıfır → belirsiz matris, Cholesky kullanılamaz).
- **İşaret ve numaralama — tek "Kurallar" sayfası:** global X sağa, Y yukarı, Z düzlemden dışa; dönme ve moment sağ el kuralı (saat yönünün tersi +); eleman açısı θ global X'ten yerel x'e, saat yönünün tersi; düğüm i (2 SD/düğüm) → SD 2i−1, 2i; kodda 0 tabanlı 2i, 2i+1 — her matris kenarında ikisi birlikte gösterilir; eleman uç kuvveti kabulü ↔ yapı statiği kabulü (alt lifleri çeken M +, N çekme +) dönüşüm tablosu.

## 4. Çözüm hattı (pipeline)

1. **Model:** düğüm (x, y, z), eleman (tip, bağlantı, malzeme, kesit), mesnet, yük — tek sözlük şeması; IFC'den dışa aktarım aynı şemayı hedefler.
2. **Eleman matrisleri:** yerel k, m, f_eq.
3. **Dönüşüm:** K_e = TᵀkT (yerel eksen → global animasyonu).
4. **Birleştirme:** bağlantı vektörüyle scatter-add (mevcut `birlestir`); simetri ve öteleme SD satır toplamı = 0 denetimi.
5. **Sınır koşulları:** bölüntüleme (öğretim) / ceza / Lagrange.
6. **Çözüm:** öğretim modunda Gauss eliminasyonu adım adım; hesap modunda Cholesky (K_ff simetrik pozitif tanımlı) → bantlı / skyline → `scipy.sparse` + `eigsh` (shift-invert, en düşük modlar). Kötü koşullanma uyarısı: pivot ≈ 0 veya cond(K_ff) çok büyük (örnek eşik 10¹²) → "mekanizma veya birim ölçeği sorunu" + boş uzay vektörü animasyonu.
7. **Geri hesaplama:** u → u_e = T·u → f = k·u_e − f_eq → N, V, M veya σ (Gauss noktası → düğüm).
8. **Son işlem:** ölçekli deformasyon, N-V-M diyagramı, gerilme konturu, tepkiler, ∑F = 0 ve ∑M = 0, enerji denetimi ½uᵀKu = ½uᵀF.

| Mod | Araç | Model boyutu (öneri; ölçümle ayarlanır) | Çıktı |
|---|---|---|---|
| Öğretim | sympy, kesin kesir | ≤ ~12 SD sembolik; ≤ ~30 SD kesirli sayısal | her adım LaTeX + kod |
| Hesap | numpy yoğun | ~30–2 000 SD | sonuç tabloları, grafikler, adım özeti |
| Hesap (seyrek) | scipy.sparse | > 2 000 SD (tarayıcı belleği sınır; Colab daha geniş) | aynı |

Aynı model iki modda çözülür; fark raporlanır (§5).

## 5. Doğrulama ve karşılaştırma

**Kabul testleri (her eleman için otomatik test; geçmeden eleman yayına girmez):**

| Test | Ölçüt |
|---|---|
| Ders kitabı örneği | yer değiştirme, tepki, iç kuvvet kitap değeriyle ≤ %0,1 (çubuk/kiriş/çerçeve); sürekli ortamda kitabın ağıyla özdeş ağ |
| Yama testi | keyfi iç düğümlü yamaya sınırdan lineer yer değiştirme alanı → iç düğüm ve gerilme makine hassasiyetinde kesin |
| Rijit cisim | mesnetsiz K'nın sıfır özdeğer sayısı = 3 (2B) / 6 (3B); K·u_rijit = 0 |
| Simetri / tanımlılık | K = Kᵀ; sınır koşulundan sonra tüm özdeğerler > 0 |
| Sembolik–sayısal eşleşme | sympy kesin sonuç ile numpy bağıl fark ≤ 10⁻¹⁰ |
| Denge ve enerji | ∑tepki + ∑yük = 0; ½uᵀKu = ½uᵀF |
| Ağ yakınsaması | h-yarılamada hata monoton azalır; mertebe eleman teorisiyle uyumlu |
| Dinamik | analitik frekanslar (çubuk, kiriş); φᵀMφ = I, φᵀKφ = Λ |
| Çapraz yazılım | aynı model SAP2000 (OAPI, Windows) ve OpenSeesPy'de; çerçeve ≤ %0,1; sürekli ortamda formülasyon farkı notuyla birkaç % |

**Referans kitaplar (gerçek; yıl/sayfa uygulama içinde yalnız elde baskı varken girilir):** Logan — *A First Course in the Finite Element Method*; Hutton — *Fundamentals of Finite Element Analysis*; Chandrupatla & Belegundu — *Introduction to Finite Elements in Engineering*; Cook, Malkus, Plesha & Witt — *Concepts and Applications of Finite Element Analysis*; Bathe — *Finite Element Procedures*; Kassimali — *Matrix Analysis of Structures*; McGuire, Gallagher & Ziemian — *Matrix Structural Analysis*; Przemieniecki — *Theory of Matrix Structural Analysis*; Chopra — *Dynamics of Structures*; Timoshenko & Woinowsky-Krieger — *Theory of Plates and Shells*; Friswell & Mottershead — *Finite Element Model Updating in Structural Dynamics*. Türkçe (başlık düzeyinde biliniyor, baskı/yıl teyit edilecek): Çakıroğlu & Çetmeli — *Yapı Sistemlerinin Hesabı için Matris Metodları ve Elektronik Hesap Makinası Programları*; Omurtag — *Çubuk Sonlu Elemanlar*; Topçu — *Sonlu Elemanlar Metodu* (ESOGÜ ders notları, çevrim içi); Celep & Kumbasar — *Yapı Dinamiği*.

**OMA bağlantısı (ileri aşama, tez için):**
- Mod şekli karşılaştırması: MAC = |φ_aᵀφ_e|² / [(φ_aᵀφ_a)(φ_eᵀφ_e)]; FE modlarının sensör SD'lerine indirgenmesi; MAC ısı haritası; Δf/f tablosu; mod eşleştirme MAC ile.
- Parametre duyarlılığı: kütle-normalize modlar için ∂λ_i/∂θ = φ_iᵀ(∂K/∂θ − λ_i·∂M/∂θ)φ_i (Fox–Kapoor); sonlu farkla doğrulama; kemer modelinde E, ρ, dolgu E'si için normalize duyarlılık tablosu.
- Basit model güncelleme: r(θ) = [w_f·Δf/f; w_m·√(1−MAC)], en küçük kareler; duyarlılık matrisi koşul sayısı → tanımlanabilir parametre sayısı uyarısı.
- Sınır: uygulama kavramı küçük modelde öğretir; Hıdırlık güncellemesi tez hattında (doğrulanmış çözücü + PyOMA2) yapılır.

## 6. Öğretim tasarımı

- **Üçlü korunur:** her adımda (a) formül (LaTeX, sembolik), (b) sayı (kesir / ondalık), (c) üretilmiş kod + çıktı. Üretilen kod, tezde kullanılacak numpy/scipy kalıbıyla aynı (kopyalanıp tezde çalışır).
- **Şema / animasyon fikirleri:**
  - eleman → global: eleman hücrelerinin K'daki hedef hücrelere uçması, çakışmada toplama vurgusu (mevcut);
  - mesnet silme: satır/sütun soluklaşıp çöker, K_ff çerçevelenir, tepki satırları ayrı renkte geri gelir (mevcut);
  - dönüşüm: yerel eksen takımı elemana oturur, θ yayı çizilir, c ve s değerleri T'ye yerleşir;
  - şekil fonksiyonu: ξ kaydırıcısıyla N_i(ξ) eğrileri ve deforme eleman;
  - Gauss integrasyonu: Q4 üzerinde Gauss noktaları belirir, her noktanın K katkısı toplanır, |J| renk haritası;
  - deformasyon: ölçek kaydırıcısı (başlangıç: en büyük yer değiştirme ≈ yapı boyutunun %10'u);
  - N-V-M: eleman uç kuvvetlerinden kesit kesit çizim; yayılı yükte parabolik M;
  - mod şekli: kütle-normalize φ_i'nin sin(ωt) ile salınımı, frekans etiketi; MAC ısı haritası;
  - mekanizma: K'nın boş uzay vektörünün animasyonu ("yapı böyle serbestçe hareket ediyor").
- **Sık öğrenci hataları → öğretici hata mesajı:**

| Hata | Tespit | Mesaj (öz) |
|---|---|---|
| Yetersiz mesnet / mekanizma | K_ff tekil, rank eksik | "n serbest rijit cisim hareketi var: eksik mesnet veya bağlantısız eleman; hareketi izleyin" |
| Bağlantısız düğüm / sıfır boylu eleman | köşegen sıfır / L = 0 | "Düğüm k hiçbir elemana bağlı değil" / "Eleman boyu sıfır" |
| Birim karışıklığı | E, ρ beklenen aralık dışı | "E = 200 000 girildi: MPa mı? Sistem kN–m; çelik için 2,0×10⁸ bekleniyor" |
| SD sırası | u₁u₂v₁v₂ gibi dizim | sabit dizim; her matris kenarında etiket (u₁, v₁, u₂, v₂) |
| Yerel–global eksen | θ veya sin işareti | T yanında eleman çizimi ve θ yayı |
| Eşdeğer yük düzeltmesi unutuldu | eleman uç kuvvetleri dengesiz | "f = k·u − f_eq uygulanmadı" |
| Mafsal çift sayımı | aynı dönme SD'si iki kez serbest | "Mafsal tek eleman ucunda tanımlanır" |
| Negatif Jakobiyen | Q4 düğümleri saat yönünde | "Düğüm sırası saat yönünde; sırayı tersine çevirin" |
| ν = 0,5 düzlem şekil değiştirme | D tekil | "Sıkıştırılamaz malzeme: D tanımsız" |
| Kısa derin kiriş EB ile | L/h küçük (örnek eşik < 5–8) | "Kayma şekil değiştirmesi önemli olabilir; Timoshenko'yu deneyin" |
| Kütle birimi | kg ile kN karışımı | "Frekans ≈ 31,6 kat hatalı çıkar; ρ'yu t/m³ girin" |

## 7. Birimler ve işaret kabulleri

- **Temel sistem:** kN, m, s. Türevler: kN/m² (kPa), kN·m, t/m³ (= kN·s²/m⁴). Dönüşümler: 1 MPa = 1 N/mm² = 1 000 kN/m²; 1 GPa = 10⁶ kN/m²; çelik E = 200 GPa = 2,0×10⁸ kN/m²; ρ = 7 850 kg/m³ = 7,85 t/m³. Frekans ω [rad/s] → f = ω/2π [Hz]. Açılar girişte derece, hesapta radyan (dönüşüm görünür).
- **Alternatif sistem:** N, mm, MPa — ders kitabı örneklerini orijinal birimle doğrulamak için; karışık giriş yok.
- **Birim denetimi fikri:** her büyüklüğe boyut etiketi (F, L, T); eleman matrisinin birimi otomatik türetilir (çubuk k → F/L; kiriş k karışık F/L, F, F·L) ve matris kenarında gösterilir; aralık uyarıları (§6); isteğe bağlı `pint` çapraz doğrulaması (yalnız Colab/masaüstü).
- **İşaret kabulleri:** §3'teki "Kurallar" sayfası tek kaynaktır; FE uç kuvveti ↔ yapı statiği (alt lif çeken M +, N çekme +, V kabulü) dönüşümü N-V-M çiziminden önce açıkça uygulanır ve gösterilir.

## 8. Riskler ve kapsam dışı

**Kapsam dışı (bilinçli):**
- Doğrusal olmayan analiz (malzeme, geometri): iteratif çözüm ve yakınsama ölçütleri formül→sayı→kod üçlüsünü adım adım gösterilemez kılar; doğrulama yükü büyük. Yığma nonlineeri gerekirse tez çözücüsünde yapılır.
- Zaman tanım alanı (Newmark vb.): dersin odağı modal analiz; yalnız "ileri okuma" bağlantısı.
- Kontak, zemin–yapı etkileşimi, eklenmiş su kütlesi: tez hattına ait.
- Lineer burkulma: olası ileri modül, şimdilik dışarıda.
- Tasarım tahkiki (TS 500, TBDY 2018, Eurocode): uygulama analiz aracıdır, tasarım aracı değil; ekranda beyan.
- Büyük model çözücüsü: tarayıcı belleği; SAP2000/OpenSees yerine geçmez.

**Riskler ve önlemler:**

| Risk | Olasılık / etki | Önlem |
|---|---|---|
| Formülasyon hatası (işaret, dönüşüm, plak/kabuk) | orta / yüksek | test-önce: kitap örneği + yama + rijit cisim testi geçmeden eleman yayına girmez |
| Kapsam şişmesi (plak, kabuk, 3B katı) tez zamanını yer | yüksek / yüksek | dönem hedefi aşama 1–5 + dinamik katman; 6–8 kavramsal, tez takvimine göre ertelenir |
| Sembolik hesabın Pyodide'de yavaşlaması | orta / orta | sembolik mod ≤ ~12 SD; üstünde otomatik sayısal mod |
| Birim / işaret karışıklığı kullanıcıyı yanıltır | orta / yüksek | tek Kurallar sayfası, aralık uyarıları, matris kenarında birim ve etiket |
| Çapraz yazılım farkının yanlış yorumu | orta / orta | çerçevede sıkı, sürekli ortamda formülasyon notuyla gevşek tolerans |
| Referans doğruluğu | düşük / orta | yıl/sayfa yalnız elde kitap varken; Türkçe kaynaklar teyitten sonra |
| Uygulamanın tez FEM'inin yerini alması yanılgısı | düşük / yüksek | uygulama "öğrenme kapısı" ve el hesabı / çapraz kontrol aracı; tez modeli doğrulanmış çözücüde |

**En zayıf nokta:** plak/kabuk aşamaları (6–7) öğretim üçlüsüne en zor uyan, doğrulaması en pahalı ve tez için en az gerekli kısımdır; dönem içinde aşama 1–5 + dinamik katman tamamlanmazsa bu iki aşama plandan çıkarılmalıdır.

## 9. Yazılım mimarisi ve geçiş planı

Bölüm 1–8 mühendislik içeriğini tanımlar. Bu bölüm o içeriğin Matris Öğren uygulamasına nasıl yerleştiğini anlatır.
Uygulama 10.10.2026'da başladı; "Durum" sütunları o günün durumudur.

### 9.1 Mevcut temel

- **Motor** `matris_ogren.py`: her işlem bir `Sonuc` döndürür. İçinde değer, adım adım anlatım, üretilmiş numpy kodu ve bu kodun gerçek çıktısı vardır. Anlatım blokları dört türdür: md, math, kod, sema.
- **Ok şemaları** (sema blokları): işlem sırasını matrisin üzerinde oklarla, renkli satır ve sütun kutularıyla, bölümleme çerçeveleriyle gösteren statik SVG kareleri. Uygulama bu kareleri adım adım canlandırır.
- **Web köprüsü** `docs/web_kopru.py`: `calistir(istek_json)` JSON isteğini alır, motoru çalıştırır, anlatım bloklarını JSON olarak döndürür.
- **PWA** `docs/`: aynı Python motoru tarayıcıda Pyodide ile, bir Web Worker içinde çalışır; formüller KaTeX ile çizilir. Telefona ve bilgisayara uygulama olarak kurulur.
- **Colab defteri** ve **pytest** test takımı (Python 3.11 ve 3.13).
- **Var olan sonlu eleman parçaları:** `cubuk_eleman`, `kiris_eleman`, `kafes_eleman`, `birlestir`, `sinir_kosulu`, `ozdeger(A, M)`.

### 9.2 Modül yapısı

Hedef yapı:

```
cekirdek/         Anlatim, Sonuc, LaTeX, ok şeması çizimleri
matris/           var olan matris işlemleri
se/               model, birim, yukler, cozucu, sonislem, dinamik
se/elemanlar/     cubuk, kafes2b, kiris, cerceve2b, kafes3b, cerceve3b, cst, q4, q8
matris_ogren.py   geriye uyumlu cephe: bugünkü bütün çağrılar çalışmaya devam eder
```

Faz 1'deki ara adım: sonlu eleman kodu tek dosyada, `sonlu_eleman.py` içinde başlar ve motoru `import matris_ogren as mo` ile kullanır.
Pyodide worker'ı dosyaları tek tek sanal dosya sistemine yazdığı için tek dosya en az değişiklikle çalışır.
Paket bölünmesi kiriş ve çerçeve elemanları oturduktan sonra, Faz 2 sonunda yapılır.

### 9.3 Model JSON şeması

Faz 1'de uygulanan şema:

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

- `tip`: `yay`, `cubuk`, `kafes`, `kiris`, `cerceve`.
- Değerler sayı ya da sympy'nin okuyabildiği metindir. `E`, `A`, `I`, `k`, `P`, `q`, `L` sembolleri yazılırsa çözüm sembolik çıkar; koordinatlar sayısal olmalıdır.
- Yayılı yük `q` elemanın yerel y ekseni yönünde ve kN/m cinsindendir.

Faz 2 ve sonrası için eklenecek anahtarlar: `malzemeler` (E, nu, rho), `kesitler` (A, I), elemanlarda `tip`, `malzeme`, `kesit`, `mafsal`;
yüklerde `sicaklik` ve `cokme`; `analiz` (statik ya da modal, mod sayısı, tutarlı ya da yığılı kütle).
Faz 1 şeması geçerli kalır; eleman içinde verilen E, A, I değerleri malzeme ve kesit tanımının önüne geçer.

### 9.4 Eleman arayüzü

Her eleman türü aynı arayüzü sağlar: `sd_sayisi`, `k_yerel()`, `T()`, `k_global()`, `m_yerel(tur)`, `f_esdeger(yuk)`, `ic_kuvvet(u_e)` ve anlatıma kendi adımlarını yazan `anlat(anl)`.
Aynı arayüz iki arka uçla çalışır: öğretimde sympy (kesin kesirler ve semboller), hesapta numpy.
Faz 1 bu arayüzün karşılığı olan yardımcı fonksiyonlarla başlar; sınıf arayüzü sürekli ortam elemanları (Faz 4) gelmeden önce zorunlu hale gelir.

### 9.5 Çözüm hattının var olan fonksiyonlara eşlenmesi

| Adım | Faz 1 | Sonraki fazlar |
|---|---|---|
| Eleman matrisleri | eleman türüne göre k, T ve kᵉ = Tᵀ k T | kütle matrisi, mafsal yoğuşturması, rijit uç bölgesi |
| Birleştirme | `mo.birlestir([(kᵉ, sd), …], n)`; anlatımı ve ok şemaları olduğu gibi kullanılır | bağlantı tablosundan genel birleştirme, seyrek matris |
| Yük vektörü | düğüm yükleri ve yayılı yükün eşdeğer düğüm yükleri | sıcaklık, mesnet çökmesi |
| Sınır koşulları | `mo.sinir_kosulu(K, F, sabit)`; bölümleme kareleri gösterilir | verilen deplasman (K_fs u_s), yay mesnet, ceza ve Lagrange yöntemleri |
| Çözüm | 12 SD'ye kadar kesin sympy, üstü numpy | `scipy.linalg.cho_solve` |
| Modal analiz | derslerde `mo.ozdeger(K, M)` | `scipy.linalg.eigh`, mod animasyonu |

### 9.6 Öğretim ve hesap modları

- 12 serbestlik derecesine (SD) kadar **kesin mod**: sympy kesirleri ve semboller; her matris tam yazılır.
- 12 SD'nin üstünde **sayısal mod** (numpy): rijitlik matrisi tam yazılmaz; yerine hangi elemanın hangi hücreye katkı yaptığını gösteren bir doluluk haritası çizilir.
- Sembolik girdiyle 12 SD'yi aşan model öğretici bir hata mesajıyla durdurulur.
- Bölüm 4'teki "30 SD'ye kadar kesirli" ara kademe Faz 2'de değerlendirilir.

### 9.7 Pyodide sınırları

- Faz 1 için numpy yeter; scipy yalnız hesap modunda ve gerektiğinde yüklenir (yaklaşık 20 MB).
- Hesaplar Web Worker içinde çalışır, arayüz donmaz.
- Birkaç bin SD'lik modeller için Colab defteri önerilir.

### 9.8 Arayüz

- **Sonlu Eleman sayfası:** hazır örnek modeller; telefonda kullanılabilen düğüm, eleman, mesnet ve yük tabloları; canlı SVG model çizimi.
- **Sonuçlar:** ölçek kaydırıcılı şekil değiştirmiş biçim, N, V ve M diyagramları, tepki tablosu; dinamik katmanla birlikte mod animasyonu.
- Ok şeması adımlayıcısı dönüşüm, birleştirme ve mesnet satır ve sütunlarının silinmesi adımlarında yeniden kullanılır.
- Model JSON olarak içe ve dışa aktarılır; ileride AutoCAD DXF çizgilerinden model okunur.

### 9.9 Dersler 2.0

- Ders kaynakları `dersler/*.md` dosyalarıdır; `ders_derle.py` bunları `docs/dersler.json` dosyasına derler. Biçim `dersler/BICIM.md` içinde tanımlıdır.
- Her ders: sezgi ve görsel, tanım, etkileşimli çizim, 3–6 çözümlü örnek (önce kendin dene, ipucu, cevap, ok şemalı adım adım çözüm), üretilen alıştırmalar, sık hatalar, özet.
- Program: 8 matris dersi ve 8 sonlu eleman dersi. Sonlu eleman dersleri: yay sistemleri; çubuk eleman; koordinat dönüşümü ve 2B kafes; birleştirme; sınır koşulları, çözüm ve tepkiler; kiriş eleman ve eşdeğer düğüm yükleri; 2B çerçeve ve N, V, M diyagramları; kütle matrisi ve titreşim modları.
- Her çözümlü örneğin kodu testte çalıştırılır ve beklenen sonuçla karşılaştırılır (`testler/test_dersler.py`).

### 9.10 Köprü

Yeni köprü işlemleri: `se_coz` (model alır; anlatım blokları ve çizim verisi döndürür) ve `ders_calistir` (ders örneğinin kodunu çalıştırır).
`ISLEMLER` ve `app.js` işlem listesi birlikte güncellenir; worker `sonlu_eleman.py` dosyasını da sanal dosya sistemine yazar.

### 9.11 Testler

- `testler/test_se.py`: ders kitabı karşılaştırmaları (seri yaylar, kademeli çubuk, iki çubuklu kafes, Pratt köprü kafesi, konsol kiriş, yayılı yüklü basit kiriş, ankastre ve mafsallı kiriş, konsol kolon, portal çerçeve), K simetrisi, rijit cisim sıfır özdeğerleri, denge ve enerji, öğretici hatalar, JSON çıktısı.
- `testler/test_dersler.py`: bütün derslerin biçim denetimi ve çözümlü örnek kodlarının sonuç denetimi.
- Sonraki fazlarda: patch testi, sympy ve numpy sonuçlarının 1e-10 içinde uyumu, ağ yakınsaması; isteğe bağlı GitHub Actions.

### 9.12 Fazlı yol haritası ve durum

| Faz | Kapsam | Süre | Durum (12.10.2026) |
|---|---|---|---|
| Faz 0 | paket bölünmesi, şema, birimler, Kurallar sayfası | ~1 hafta | şema ve birimler Faz 1 ile geldi; paket bölünmesi ertelendi |
| Faz 1 | 2B kafes hattı; yay, çubuk, kiriş ve 2B çerçevenin statik çekirdeği | ~2 hafta | tamamlandı: İP1–İP4 bitti, 11–18 dersleri ve Sonlu eleman sayfası yayında |
| Faz 2 | kiriş ve 2B çerçeve tamamlanır: mafsal, mesnet çökmesi, sıcaklık, rijit uç | ~3 hafta | kısmen (15.10.2026): mesnet çökmesi, elastik mesnet (yay) ve Winkler zemini (temel kirişi) bitti; mafsal, sıcaklık ve rijit uç sırada |
| Faz 3 | dinamik katman: kütle matrisi, modal analiz, mod animasyonu, Rayleigh, MAC | ~2 hafta | sırada; titreşim modları Faz 1'de ders düzeyinde tanıtılır |
| Faz 4 | CST ve Q4, Gauss integrasyonu, patch testi, gerilme konturları | ~3 hafta | — |
| Faz 5 | Q8, yakınsama, kemer makro-modeli, duyarlılık | ~2 hafta | — |
| Faz 6+ | isteğe bağlı: 3B, plak ve kabuk (kavramsal), model güncelleme | — | 3B öne alındı ve bitti (15.10.2026): uzay kafes ve uzay çerçeve (İP5); plak/kabuk ve model güncelleme — |

### 9.13 Faz 1 iş paketleri

| Paket | İçerik | Dosyalar | Durum |
|---|---|---|---|
| İP1 Ok şemaları | işlem sırasını matris üzerinde oklarla, satır ve sütun kutularıyla, bölümleme çerçeveleriyle gösterme; adımlayıcı | `matris_ogren.py`, `docs/app.js`, `docs/style.css`, `docs/index.html`, `docs/web_kopru.py` | bitti |
| İP2 Dersler 2.0 | ders biçimi ve derleyicisi, etkileşimli çizimler, çözümlü örnekler, alıştırmalar, 16 ders | `dersler/`, `ders_derle.py`, `docs/etkilesim*.js`, `testler/test_dersler.py` | bitti: 16 ders, 138 çözümlü örnek, 33 etkileşimli çizim, 38 alıştırma |
| İP3 Sonlu eleman motoru | `se_coz(model)`: yay, çubuk, kafes, kiriş, çerçeve; adım adım anlatım, model ve sonuç şemaları, numpy kodu, hazır modeller | `sonlu_eleman.py`, `testler/test_se.py` | bitti |
| İP4 Sonlu eleman sayfası | model düzenleyici, hazır modeller, sonuç diyagramları | `docs/se.js`, `docs/app.js`, `docs/index.html`, `docs/style.css` | bitti |
| İP5 3B yapılar ve temel sistemleri (15.10.2026) | `kafes3b` (3 SD/düğüm, doğrultu kosinüsleri) ve `cerceve3b` (6 SD/düğüm, 12×12: eksenel, burulma, iki eksende eğilme; Kassimali yerel eksen kuralı, λ ve T = diag(λ,λ,λ,λ); Vz, My, T diyagramları; aksonometrik şemalar); `yaylar` (elastik mesnet, köşegen), `zemin` (tutarlı Winkler matrisi (k_s L/420)[…], zemin basıncı diyagramı), `cokmeler` (K_ff u_f = F_f − K_fs u_s; enerjide ½uᵀR); 10 yeni hazır model; web sayfasında z sütunu, 3B izdüşüm ve bakış kaydırıcıları, yay/çökme tabloları, altı diyagram düğmesi | `sonlu_eleman.py`, `docs/se.js`, `docs/style.css`, `testler/test_se.py` | bitti: kapalı form testleri (tripod dengesi, L konsol PL³/3EI + PL²L₁/GJ, Hetényi sonsuz kiriş, 3EIΔ/L³ çökme, yaylı kiriş), 2B–3B tutarlılık, bağımsız referans çözücü |

### 9.14 Faz 1 bitiş ölçütü

- Bütün hazır modeller el hesabı ya da ders kitabı sonucuyla tutar; testler Python 3.11 ve 3.13'te geçer.
- Her ders telefonda (375 px) yatay kaydırma olmadan okunur; her çözümlü örneğin adım adım çözümü ok şemalarıyla açılır.
- Sonlu Eleman sayfasında bir model düzenlenip çözülür; şekil değiştirmiş biçim ve N, V, M diyagramları görünür.
