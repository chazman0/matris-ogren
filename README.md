# Matris Öğren

Sonlu elemanlar dersi için öğrenme odaklı matris hesaplayıcı. Her işlemi hem adım adım matematiksel çözümüyle hem de aynı hesabı yapan Python (numpy/sympy) kodu ve çıktısıyla gösterir.

**Uygulama:** https://chazman0.github.io/matris-ogren/

## Kurulum

**iPhone / iPad:** adresi **Safari** ile açın → Paylaş → **Ana Ekrana Ekle**. Ana ekrandaki "Matris" simgesi uygulamayı tam ekran açar.

**Windows / Mac (Edge veya Chrome):** adres çubuğunun sağındaki **"Uygulamayı yükle"** simgesine tıklayın. Başlat menüsüne ve masaüstüne eklenir, kendi penceresinde açılır.

**Bilgisayarda, internet sitesi olmadan:** `Baslat_Bilgisayar.cmd` dosyasına çift tıklayın; uygulama kendi penceresinde açılır (arkada küçültülmüş bir sunucu penceresi kalır, kapatılırsa uygulama durur).

İlk açılışta Python motoru (≈30 MB) bir kez indirilir; sonraki açılışlar internet olmadan da çalışır.

## Masaüstü sürümü

Windows, macOS ve Linux için kurulabilen bilgisayar programı: aynı uygulama, Python motoru içinde gelir (ilk açılışta bile
internet gerekmez). Türkçe menü çubuğu (Dosya, Düzen, Görünüm, Çizim, Aks, Analiz, Tasarım, Rapor, Yardım) ve kısayollar
(Ctrl+S kaydet, Ctrl+O aç, F5 çöz, F11 tam ekran…), `.matris` proje dosyaları (çift tıklayınca ya da pencereye sürükleyince açılır),
son dosyalar, çoklu pencere, otomatik kayıt ve beklenmedik kapanmadan sonra kurtarma, IFC / CSV / rapor için yerel "Kaydet"
penceresi ve rapordan doğrudan PDF.

Paketler GitHub'da **Releases** sayfasındadır (Windows kurulum ve taşınabilir `.exe`, macOS `.dmg`, Linux `.AppImage` / `.deb`).
Kurulum, imzasız paket uyarıları, geliştirme (`masaustu/`: `npm ci`, `npm run hazirla`, `npm start`) ve sayfa ↔ masaüstü
sözleşmesi için: [`masaustu/README.md`](masaustu/README.md).

## İşlemler

Toplama, çıkarma, skaler çarpım, matris çarpımı, transpoz, iz, determinant (kofaktör / eliminasyon), ters (formül / Gauss-Jordan), rank, denklem çözümü (Gauss / Cramer / ters matris), özdeğer-özvektör, çubuk / kiriş / kafes eleman rijitlik matrisleri, birleştirme (assembly), sınır koşulu uygulama ve çözüm; Sonlu eleman sayfasında 2B ve 3B yapıların tam çözümü; Bina sayfasında 3B bina modelinin yük akışı, deprem, birleşimler ve kesit tahkikleri. Elemanlar kesir, ondalık ya da sembol (`E*A/L`, `k`, `P`) olabilir; hesap kesin (sembolik) yapılır.

## Dersler

24 ders üç bölümdedir. **Matris** bölümü (1–8): matris nedir, toplama, çarpım, transpoz, determinant, ters, doğrusal sistemler, özdeğer. **Sonlu eleman** bölümü (11–20): yay sistemleri, çubuk, kafes ve dönüşüm, birleştirme, sınır koşulları ve tepkiler, kiriş, düzlem çerçeve, serbest titreşim, uzay kafes ve uzay çerçeve (3 boyutlu yapılar), temel sistemleri (elastik mesnet, Winkler zemini, mesnet çökmesi). **Yapı analizi** bölümü (21–26): yük akışı döşemeden zemine (TS 498:2021 yükleri, TS 500 45° kuralıyla üçgen/trapez dağılım, eşdeğer yükler, kolon birikimi ve yük alanı, temel taban basıncı, korunum); yük durumları, kombinasyonlar ve zarf (yük deseni → durum → kombinasyon → zarf zinciri, süperpozisyon, TS 500 / TBDY 4.4.4 / ÇYTHYE birleşimleri, belirleyen kombinasyon, kolonda eş zamanlı N–M, rüzgâr ve kar); TBDY 2018 eşdeğer deprem yükü (spektrum, R ve D, kat kütleleri, T_pA ve Rayleigh periyodu, V_tE ve kat kuvvetleri, dışmerkezlik, göreli kat ötelemesi); TS 500 ile betonarme kiriş ve kolon tahkiki (eşdeğer blok, A_s, ρ sınırları, çift donatı, kesme, N–M etkileşim eğrisi, e_min, eş zamanlı N–M noktaları, Bresler); ÇYTHYE 2018 ile çelik eleman tahkiki (YDKT/GKT, enkesit sınıfı, yanal burulmalı burkulma, F_cr eğrisi, kesme, çekme, bileşik etki, K seçimi); bina analizi baştan sona (yapı analiz programlarının iş akışı, yerel eksenler, rijit diyafram, D/C okuma, denge sağlaması, sık hatalar).

Her derste renkli matris kutuları ve oklu şekiller, sürükleyerek oynanan etkileşimli çizimler, ipucu ve cevabı açılan çözümlü örnekler (çoğu tek tıkla çalıştırılır ve sonucu denetlenir) ve sınırsız üretilen alıştırmalar vardır.

## Sonlu eleman çözücü

Uygulamadaki **Sonlu eleman** sayfasında hazır bir model seçilir ya da düğüm, eleman, mesnet ve yük tabloları doldurulur. Yay, çubuk, düzlem kafes, kiriş, düzlem çerçeve, **uzay kafes** ve **uzay çerçeve** (burulma ve iki eksende eğilme) modelleri çözülür; şekil değiştirmiş biçim, N/V/M (uzay çerçevede ayrıca Vz, My, T) diyagramları, mesnet tepkileri, denge denetimi ve adım adım anlatım gösterilir. 3 boyutlu modeller aksonometrik izdüşümle çizilir ve bakış açısı kaydırıcıyla çevrilir.

**Kolon–kiriş–temel sistemleri:** elastik mesnetler (temel altındaki zemini temsil eden kx, ky, kr yayları), Winkler zeminine oturan sürekli temel kirişi (eleman başına yatak katsayısı `zemin`, zemin basıncı diyagramı) ve mesnet çökmesi (verilen yer değiştirme, K_ff·u_f = F_f − K_fs·u_s) modellenir. Hazır örnekler arasında iki katlı çerçeve, zemin yaylarına oturan portal, sürekli temel kirişli çerçeve, farklı oturan temel, elastik zemindeki temel kirişi, tripod ve kule uzay kafesleri, L konsol, kiriş ızgarası ve kutu uzay çerçeve vardır.

## Bina sayfası (yapı analizi)

Aks tabanlı 3B bina modeli: çiz, yükle, çöz, tahkik et, raporla. Öğretim ve ön boyutlandırma içindir.

- **9 hazır şablon:** 7 aks–kat binası (tek açıklıklı çerçeve; 2, 3 ve 4 katlı betonarme; tek katlı çelik depo; mütemadi temelli
  ve radye temelli betonarme) ve 2 genel (surum 3) düğüm–çubuk–panel modeli (çelik sanayi yapısı: 4 hol, vuteli mertek, aşık,
  çaprazlar, kren yolu; 3 katlı merkezi çaprazlı çelik çerçeve).
- **Aks sistemi ve aks tabanlı çizim:** Hızlı aks sihirbazı, açılı / silindirik ek aks sistemleri, plan ve cephe düzlemi seçici
  (PgUp / PgDn). Her düğüm bir aks kesişimi ya da çubuğun bölme / kesişim noktasıdır; aks taşınınca bağlı elemanlar da taşınır.
  Kolon, kiriş, çapraz, panel, eğik çubuk; makas, beşik çerçeve, aşık ve kren yolu üreteçleri; mesnet ve yük atama.
- **Yükler ve çözüm:** TS 498:2021 yükleri, döşemeden zemine yük akışı, kar, rüzgâr, TBDY 2018 eşdeğer deprem yükü, kren;
  TS 500 / ÇYTHYE / TBDY birleşimleri ve zarf; yalnız çekme çaprazları yinelemeli çözülür.
- **Tasarım ve kesit önerisi:** TS 500 betonarme ve ÇYTHYE 2018 çelik kontrolleri, eleman başına D/C; seçili eleman ya da bütün
  model için kesit önerisi ve "Hepsini uygula" ile yeniden çözüm.
- **Temeller:** tekil temel; mütemadi (ters T temel kirişleri) ve radye (ızgara plak) Winkler zemininde, taban basıncı ve oturma.
  Aks–kat ve genel model aynı temel modülünü (`temel.py`) kullanır: genel modelde temel kirişleri ve radye GLOBAL X/Y aks çizgileri
  boyunca kurulur (ek aks sistemindeki tabanlar yalnız kirişsiz radyede ağa katılır); genel modele geçerken temel ayarı korunur.
- **Mesnetler:** açık mesnet her doğrultuda tutulu ya da yaylı olabilir (k_x, k_y, k_z kN/m; k_rx, k_ry, k_rz kN·m/rad); rijit
  diyaframlı kat seviyesindeki mesnet diyafram bağıyla (ceza rijitliği) uygulanır.
- **Çıktılar:** statik hesap raporu (önizleme, yazdır / PDF, HTML), tablolar ve metraj (hücre düzenleme, yapıştırma, CSV dışa ve
  içe aktarma), ısı haritası (yer değiştirme, iç kuvvet, gerilme, kullanım oranı; döşeme paneli ve radye alanları), IFC4 yapı modeli
  (rüzgâr, deprem ve kren eylemleri, temel öz ağırlığı dahil), `.matris` proje dosyası.
- **Arayüz:** sahne kenarlarına yerleşen (rıhtım) araç kutuları — sığmayanlar "⋯" çekmecesinde, istenen kutu sahnede yüzdürülür —,
  sağ tık (dokunmatikte uzun basma) ile eleman bilgisi ve komutları, ölçme araçları (uzaklık, açı, alan, kot farkı, koordinat), tek
  geri al yığını; `?` bütün klavye kısayollarını gösterir.

Ayrıntılar: [`KULLANIM.md`](KULLANIM.md) §3.9 (Python: `yapi`, genel model, rapor, tablolar, ısı haritası alanları) ve §3.10–3.12
(Bina sayfası, aks tabanlı çizim, kısayollar); modüllerin dayandığı tasarım kararları ve veri şemaları: [`TASARIM.md`](TASARIM.md).

## Dosyalar

| Dosya | İçerik |
|---|---|
| `matris_ogren.py` | Matris hesap motoru (sympy): adım adım anlatım ve Python kodu. Colab defteri ve uygulama bu modülü kullanır. |
| `sonlu_eleman.py` | Model sözlüğünden sonlu eleman çözümü (`se_coz`, `coz_coklu`) ve hazır örnek modeller. |
| `yapi.py` | Aks–kat bina modeli (surum 1): TS 498 yükleri, yük akışı, kar, rüzgâr, TBDY 2018 deprem, birleşimler, zarf; `bina_coz` genel modeli `yapi_serbest`'e yönlendirir. |
| `yapi_serbest.py` | Genel düğüm–çubuk–panel modeli (surum 3): aks sistemleri, REF düğümleri, panel yük dağıtımı, kren, yalnız çekme, kesit önerisi (`kesit_oner`). |
| `yapi_veri.py` | Kütüphane: malzemeler, profiller, TS 498 yükleri, duvar ve kaplama takımları, kombinasyon kümeleri, TBDY tabloları (kaynaklı). |
| `tasarim.py` | TS 500 betonarme ve ÇYTHYE 2018 çelik kesit tahkikleri, N–M etkileşimi, kesit önerisi. |
| `temel.py` | Mütemadi ve radye temel: temel kirişi / ızgara plak, Winkler zemini, taban basıncı, zımbalama, donatı. |
| `rapor.py` | Statik hesap raporu (tek dosya HTML, A4 yazdırma). |
| `tablolar.py` | Bina tabloları (düzenlenebilir hücreler, JSON yolları) ve metraj. |
| `alan.py` | Isı haritası alanları: çubuk boyunca iç kuvvet, gerilme, kullanım, eğri yer değiştirme; döşeme plağı ve radye. |
| `docs/web_kopru.py` | Tarayıcı ↔ Python köprüsü (`calistir`): bütün işlemlerin girdi / yanıt şemaları. Kopya değil kaynaktır, yalnız `docs/`'ta durur. |
| `dersler/` | Markdown dersler; yazım kuralları `dersler/BICIM.md`'de. |
| `ders_derle.py` | Dersleri denetler (`--denetle`) ve `docs/dersler.json`'a derler. |
| `PLAN_SONLU_ELEMANLAR.md` | Matristen sonlu eleman uygulamasına geçiş planı. |
| `Matris_Ogren.ipynb` | Google Colab defteri: matris modülünün (`matris_ogren.py`) konu anlatımı ve çalıştırılabilir örnekleri; kurulum hücresi programın on modülünü (matris, sonlu eleman, bina, temel, tasarım, rapor, tablolar, alan) gömülü taşır, "Bina modeli" bölümü bir şablonu çözer, statik hesap raporunu ve kesit önerisini defterde gösterir. |
| `KULLANIM.md` | Motorun fonksiyon fonksiyon kullanım kılavuzu (matris, sonlu eleman, bina, rapor, tablolar, ısı haritası, köprü işlemleri, Bina sayfası). |
| `TASARIM.md` | Tasarım belgesi haritası: kod yorumlarındaki §1–§19 bölümleri, veri şemaları ve sürüm şeması. |
| `docs/` | Yüklenebilir web uygulaması (PWA); motor tarayıcıda Pyodide ile çalışır. `docs/*.py` (köprü hariç) kökteki modüllerin kopyasıdır. |
| `masaustu/` | Masaüstü sürümü: `docs/`'u çevrimdışı çalışan bir bilgisayar programı olarak paketler (bkz. `masaustu/README.md`). |
| `testler/` | pytest testleri; `testler/js/` node testleri. |
| `web_yap.py` | `docs/` klasörünü üretir: modülleri kopyalar, dersleri derler, sürüm damgası basar. |
| `defter_yap.py` | Colab defterini üretir (on modülü zlib + base64 ve SHA-256 özetiyle gömer; sympy ve numpy yeter, nbformat gerekmez). |
| `.github/workflows/` | `testler.yml` (her itmede testler), `masaustu.yml` (masaüstü paketleri). |

Geliştirme: kökteki bir modül ya da ders değişince `python3 web_yap.py` docs klasörünü günceller (modülleri kopyalar, dersleri
derler, sürüm damgası basar); gömülü on modülden biri değişince `python3 defter_yap.py` defteri yeniden üretir. Testler:
`python3 -m pytest testler -q` ve `node --test testler/js/*.test.js`; dersler için ayrıca `python3 ders_derle.py --denetle`.
