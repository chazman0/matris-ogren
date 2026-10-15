# Matris Öğren

Sonlu elemanlar dersi için öğrenme odaklı matris hesaplayıcı. Her işlemi hem adım adım matematiksel çözümüyle hem de aynı hesabı yapan Python (numpy/sympy) kodu ve çıktısıyla gösterir.

**Uygulama:** https://chazman0.github.io/matris-ogren/

## Kurulum

**iPhone / iPad:** adresi **Safari** ile açın → Paylaş → **Ana Ekrana Ekle**. Ana ekrandaki "Matris" simgesi uygulamayı tam ekran açar.

**Windows / Mac (Edge veya Chrome):** adres çubuğunun sağındaki **"Uygulamayı yükle"** simgesine tıklayın. Başlat menüsüne ve masaüstüne eklenir, kendi penceresinde açılır.

**Bilgisayarda, internet sitesi olmadan:** `Baslat_Bilgisayar.cmd` dosyasına çift tıklayın; uygulama kendi penceresinde açılır (arkada küçültülmüş bir sunucu penceresi kalır, kapatılırsa uygulama durur).

İlk açılışta Python motoru (≈30 MB) bir kez indirilir; sonraki açılışlar internet olmadan da çalışır.

## İşlemler

Toplama, çıkarma, skaler çarpım, matris çarpımı, transpoz, iz, determinant (kofaktör / eliminasyon), ters (formül / Gauss-Jordan), rank, denklem çözümü (Gauss / Cramer / ters matris), özdeğer-özvektör, çubuk / kiriş / kafes eleman rijitlik matrisleri, birleştirme (assembly), sınır koşulu uygulama ve çözüm; Sonlu eleman sayfasında 2B ve 3B yapıların tam çözümü. Elemanlar kesir, ondalık ya da sembol (`E*A/L`, `k`, `P`) olabilir; hesap kesin (sembolik) yapılır.

## Dersler

16 ders iki bölümdedir. **Matris** bölümü (1–8): matris nedir, toplama, çarpım, transpoz, determinant, ters, doğrusal sistemler, özdeğer. **Sonlu eleman** bölümü (11–18): yay sistemleri, çubuk, kafes ve dönüşüm, birleştirme, sınır koşulları ve tepkiler, kiriş, düzlem çerçeve, serbest titreşim.

Her derste renkli matris kutuları ve oklu şekiller, sürükleyerek oynanan etkileşimli çizimler, ipucu ve cevabı açılan çözümlü örnekler (çoğu tek tıkla çalıştırılır ve sonucu denetlenir) ve sınırsız üretilen alıştırmalar vardır.

## Sonlu eleman çözücü

Uygulamadaki **Sonlu eleman** sayfasında hazır bir model seçilir ya da düğüm, eleman, mesnet ve yük tabloları doldurulur. Yay, çubuk, düzlem kafes, kiriş, düzlem çerçeve, **uzay kafes** ve **uzay çerçeve** (burulma ve iki eksende eğilme) modelleri çözülür; şekil değiştirmiş biçim, N/V/M (uzay çerçevede ayrıca Vz, My, T) diyagramları, mesnet tepkileri, denge denetimi ve adım adım anlatım gösterilir. 3 boyutlu modeller aksonometrik izdüşümle çizilir ve bakış açısı kaydırıcıyla çevrilir.

**Kolon–kiriş–temel sistemleri:** elastik mesnetler (temel altındaki zemini temsil eden kx, ky, kr yayları), Winkler zeminine oturan sürekli temel kirişi (eleman başına yatak katsayısı `zemin`, zemin basıncı diyagramı) ve mesnet çökmesi (verilen yer değiştirme, K_ff·u_f = F_f − K_fs·u_s) modellenir. Hazır örnekler arasında iki katlı çerçeve, zemin yaylarına oturan portal, sürekli temel kirişli çerçeve, farklı oturan temel, elastik zemindeki temel kirişi, tripod ve kule uzay kafesleri, L konsol, kiriş ızgarası ve kutu uzay çerçeve vardır.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `matris_ogren.py` | Hesap motoru (sympy). Colab'da ve uygulamanın içinde aynı dosya çalışır. |
| `sonlu_eleman.py` | Model sözlüğünden sonlu eleman çözümü (`se_coz`) ve hazır örnek modeller. |
| `dersler/` | Markdown dersler; yazım kuralları `dersler/BICIM.md`'de. |
| `ders_derle.py` | Dersleri denetler (`--denetle`) ve `docs/dersler.json`'a derler. |
| `PLAN_SONLU_ELEMANLAR.md` | Matristen sonlu eleman uygulamasına geçiş planı. |
| `Matris_Ogren.ipynb` | Google Colab defteri: konu anlatımı + çalıştırılabilir örnekler. |
| `KULLANIM.md` | Motorun fonksiyon fonksiyon kullanım kılavuzu. |
| `docs/` | Yüklenebilir web uygulaması (PWA); motor tarayıcıda Pyodide ile çalışır. |
| `testler/` | pytest testleri. |
| `defter_yap.py`, `web_yap.py` | Defteri ve `docs/` klasörünü üreten betikler. |

Geliştirme: `python web_yap.py` docs klasörünü günceller (motoru kopyalar, dersleri çıkarır, sürüm damgası basar); testler `pytest testler`.
