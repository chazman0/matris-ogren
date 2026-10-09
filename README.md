# Matris Öğren

Sonlu elemanlar dersi için öğrenme odaklı matris hesaplayıcı. Her işlemi hem adım adım matematiksel çözümüyle hem de aynı hesabı yapan Python (numpy/sympy) kodu ve çıktısıyla gösterir.

**Uygulama:** https://chazman0.github.io/matris-ogren/

## Kurulum

**iPhone / iPad:** adresi **Safari** ile açın → Paylaş → **Ana Ekrana Ekle**. Ana ekrandaki "Matris" simgesi uygulamayı tam ekran açar.

**Windows / Mac (Edge veya Chrome):** adres çubuğunun sağındaki **"Uygulamayı yükle"** simgesine tıklayın. Başlat menüsüne ve masaüstüne eklenir, kendi penceresinde açılır.

İlk açılışta Python motoru (≈30 MB) bir kez indirilir; sonraki açılışlar internet olmadan da çalışır.

## İşlemler

Toplama, çıkarma, skaler çarpım, matris çarpımı, transpoz, iz, determinant (kofaktör / eliminasyon), ters (formül / Gauss-Jordan), rank, denklem çözümü (Gauss / Cramer / ters matris), özdeğer-özvektör, çubuk / kiriş / kafes eleman rijitlik matrisleri, birleştirme (assembly), sınır koşulu uygulama ve çözüm. Elemanlar kesir, ondalık ya da sembol (`E*A/L`, `k`, `P`) olabilir; hesap kesin (sembolik) yapılır.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `matris_ogren.py` | Hesap motoru (sympy). Colab'da ve uygulamanın içinde aynı dosya çalışır. |
| `Matris_Ogren.ipynb` | Google Colab defteri: konu anlatımı + çalıştırılabilir örnekler. |
| `KULLANIM.md` | Motorun fonksiyon fonksiyon kullanım kılavuzu. |
| `docs/` | Yüklenebilir web uygulaması (PWA); motor tarayıcıda Pyodide ile çalışır. |
| `testler/` | pytest testleri. |
| `defter_yap.py`, `web_yap.py` | Defteri ve `docs/` klasörünü üreten betikler. |

Geliştirme: `python web_yap.py` docs klasörünü günceller (motoru kopyalar, dersleri çıkarır, sürüm damgası basar); testler `pytest testler`.
