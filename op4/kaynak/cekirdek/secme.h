// op4 çekirdek sözleşmesi — CPU seçme dizini (BVH), üzerine gelme, pencere seçimi, ışın vuruşu
// (MIMARI §6.9, §7.2; "F1 paket sözleşmeleri" §S8).
//
// Uygulayan: C (arayuz-goruntu) — kaynak/cekirdek/secme.cpp. Platformdan bağımsızdır ve Linux'ta doctest ile sınanır.
// Girdi: değişmez SahneAnlik (SahnePtr). Kur() iş havuzunda çağrılabilir; sorgular const ve iş parçacığı güvenlidir.
// Bütçe (MIMARI §6.13): üzerine gelme ve yakalama 100 bin elemanda ≤ 1 ms.
#pragma once

#include <array>
#include <cstdint>
#include <memory>
#include <optional>
#include <vector>

#include "cekirdek/kimlik.h"
#include "cekirdek/sahne.h"
#include "cekirdek/vektor.h"

namespace op4 {

// Bir görünümün kamera durumu, çift hassasiyetle. Matrisler satır öncelikli saklanır ve sütun vektörüyle çarpılır
// (p' = M · p; kaynak/matematik.h ile aynı kural). `gorunumIzdusum` = izdusum · gorunum. Görüş alanı pikselleri sol üstten
// başlar (x sağa, y aşağı); (0, 0) görüş alanının sol üst köşesidir (pencerenin değil).
struct GorusIzdusumu {
    std::array<double, 16> gorunumIzdusum{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    double genislik = 1, yukseklik = 1;  // görüş alanı (piksel)
    V3d goz;                             // kamera konumu (perspektif) ya da bakış doğrultusunun gerisinde bir nokta
    bool ortografik = false;
    double dpiOlcek = 1.0;               // piksel toleransları bununla çarpılır

    // Dünya noktasını görüş alanı pikseline izdüşürür; kameranın arkasındaysa false.
    bool Izdusur(V3d p, double& px, double& py) const;
};

struct Isin {
    V3d baslangic;
    V3d yon;  // birim
};
// Görüş alanı pikselinden geçen ışın (perspektifte gözden, ortografikte görüntü düzleminden).
Isin PikselIsini(const GorusIzdusumu& g, double px, double py);

struct SecmeAyari {
    double tolPx = 4.0;          // üzerine gelme / tık toleransı (DPI ölçeksiz piksel; MIMARI §6.9)
    bool dugumler = true;        // seçilebilirlik süzgeci (durum çubuğu tür çipleri, MIMARI §5.2)
    bool cubuklar = true;
    bool paneller = true;
    bool mesnetler = true;
    bool akslar = false;         // Faz 4
};

struct SecmeVurusu {
    ElemanKimligi kimlik;
    V3d nokta;                   // elemanın üstündeki en yakın dünya noktası (çapa olarak kullanılır)
    double derinlik = 0;         // ışın boyunca uzaklık (m)
    double ekranUzakligiPx = 0;  // imleçten ekran uzaklığı
};

enum class PencereKipi : uint8_t {
    TamIcinde = 0,  // soldan sağa sürükleme: elemanın tamamı dikdörtgenin içinde
    Degen = 1,      // sağdan sola sürükleme: dikdörtgene değen ya da kesen
};

class SecmeDizini {
public:
    SecmeDizini();
    ~SecmeDizini();
    SecmeDizini(SecmeDizini&&) noexcept;
    SecmeDizini& operator=(SecmeDizini&&) noexcept;

    // Dizini kurar (BVH). Sahne null ise boş dizin.
    void Kur(SahnePtr sahne);
    uint64_t SahneSurumu() const;
    const SahnePtr& Sahne() const;

    // İmlecin altındaki en öndeki eleman (üzerine gelme ve tık). Öncelik: düğüm > mesnet > çubuk > panel, aynı türde
    // ekrana en yakın, sonra en öndeki. Tolerans dışında kalırsa nullopt.
    std::optional<SecmeVurusu> EnYakin(const GorusIzdusumu& g, double px, double py, const SecmeAyari& a) const;
    // Seçim döngüsü (aynı noktaya tekrar tık): noktadaki bütün adaylar, EnYakin sırasıyla.
    std::vector<SecmeVurusu> Adaylar(const GorusIzdusumu& g, double px, double py, const SecmeAyari& a) const;
    // Pencere seçimi; (x0, y0)–(x1, y1) herhangi iki köşe. Sonuç sıralı ve tekrarsız.
    std::vector<ElemanKimligi> Pencere(const GorusIzdusumu& g, double x0, double y0, double x1, double y1, PencereKipi kip,
                                       const SecmeAyari& a) const;
    // Işının ilk vurduğu eleman (gezinme çapası, MIMARI §7.2). Çubuk kapsül yarıçapı kesit boyutundan, yoksa 0,05 m.
    std::optional<SecmeVurusu> IsinVurusu(const Isin& isin, const SecmeAyari& a) const;
    // Kimliklerin ortak sınır kutusu ("Seçime yakınlaş", Sığdır). Hiçbiri yoksa boş kutu.
    Kutu3d Sinir(const std::vector<ElemanKimligi>& kimlikler) const;

private:
    struct Ic;
    std::unique_ptr<Ic> ic_;
};

}  // namespace op4
