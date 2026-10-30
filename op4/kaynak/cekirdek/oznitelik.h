// op4 çekirdek sözleşmesi — sütunlu öznitelik tablosu (MIMARI §4, §11.2; "F1 paket sözleşmeleri" §S5).
//
// Üreten : B — op4_cekirdek.js oznitelikler() (op4_ops.oznitelikCikar, katUyeligi, kullanimYeri) → bu yapı.
// Tüketen: C — model gezgini (kat → tür → kullanım yeri sayıları, tıkla seç), salt okunur Özellikler paneli;
//          Faz 3'te süzgeç dili ve tablolar.
//
// Şema op4/veri/oznitelikler.json'dadır (alan kimliği, ad, tür, birim, eşanlamlılar). Faz 1 alt kümesi aşağıdaki
// `oznitelik::` sabitleridir; JS ve C++ aynı kimlikleri kullanır (sozlesme.test.js ve sozlesme_oznitelik.cpp denetler).
// Tablo DEĞİŞMEZDİR ve sahne anlığıyla aynı `sahneSurumu`nu taşır (aynı modelden üretilmiştir).
#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include "cekirdek/kimlik.h"

namespace op4 {

// Faz 1 öznitelik kimlikleri (oznitelikler.json "id"). Yeni alanlar yalnız eklenir.
namespace oznitelik {
inline constexpr const char* TUR = "tur";                      // enum: eleman tür kodu ("cubuk", "panel", "dugum", "mesnet")
inline constexpr const char* NO = "no";                        // sayi
inline constexpr const char* AD = "ad";                        // metin (boş olabilir)
inline constexpr const char* ALT_TUR = "alt_tur";              // enum: kolon, kiris, doseme, cati, cephe, capraz, makas-ust,
                                                               //   makas-alt, makas-dikme, makas-diyagonal, asik, kren, bag,
                                                               //   temel, mesnet, dugum, diger (MIMARI §10.3)
inline constexpr const char* KULLANIM_YERI = "kullanim_yeri";  // enum: kose, kenar, ic, dis, konsol, dis-cephe, temel,
                                                               //   kolon-ustu, ara, +x, -x, +y, -y ("" = sınıfsız)
inline constexpr const char* KAT = "kat";                      // liste (kat no'ları; kat aralığını aşan kolon birden çok)
inline constexpr const char* SEVIYE = "seviye";                // metin: en yakın Z aksının adı
inline constexpr const char* KESIT = "kesit";                  // metin: modeldeki kesit adı
inline constexpr const char* PROFIL = "profil";                // metin: normal kütüphane adı (profilAdiNormal) ya da ""
inline constexpr const char* MALZEME = "malzeme";              // metin
inline constexpr const char* SISTEM = "sistem";                // enum: celik, betonarme
inline constexpr const char* GRUP = "grup";                    // metin
inline constexpr const char* UZUNLUK = "uzunluk";              // sayi, m (çubuk)
inline constexpr const char* EGIM = "egim";                    // sayi, derece (çubuğun yatayla açısı)
inline constexpr const char* ACI = "aci";                      // sayi, derece (kesit dönüklüğü)
inline constexpr const char* KALINLIK = "kalinlik";            // sayi, m (panel)
inline constexpr const char* ALAN = "alan";                    // sayi, m² (panel)
inline constexpr const char* SERBEST_I = "serbest_i";          // metin: "My,Mz" (i ucunda serbest kuvvetler)
inline constexpr const char* SERBEST_J = "serbest_j";          // metin
inline constexpr const char* SERBEST_DUGUM = "serbest_dugum";  // bool: serbest (REF'siz) düğüme bağlı mı
inline constexpr const char* X = "x";                          // sayi, m (düğüm; çubuk / panelde ağırlık merkezi)
inline constexpr const char* Y = "y";
inline constexpr const char* Z = "z";
}  // namespace oznitelik

enum class OznitelikTuru : uint8_t { Sayi = 0, Metin = 1, Enum = 2, Bool = 3, Liste = 4 };

// Bir sütun. Satır sayısı tablonun `satirlar` uzunluğudur; tür hangi dizinin dolu olduğunu belirler:
//   Sayi, Bool : sayi[satir]       (Bool 0/1; değer yoksa NaN)
//   Metin, Enum: kod[satir] → sozluk (değer yoksa OZNITELIK_YOK)
//   Liste      : listeBas[satir] … listeBas[satir + 1] aralığı listeDeger içinde (listeBas uzunluğu satır + 1)
struct OznitelikSutunu {
    std::string id;
    OznitelikTuru tur = OznitelikTuru::Sayi;
    std::string birim;  // "m", "m²", "°" ya da ""
    std::vector<double> sayi;
    std::vector<uint32_t> kod;
    std::vector<std::string> sozluk;
    std::vector<uint32_t> listeBas;
    std::vector<double> listeDeger;
};
inline constexpr uint32_t OZNITELIK_YOK = 0xFFFFFFFFu;

class OznitelikTablosu {
public:
    uint64_t sahneSurumu = 0;
    std::vector<ElemanKimligi> satirlar;   // satır → eleman (sıralı olması gerekmez)
    std::vector<OznitelikSutunu> sutunlar;

    // Üretici doldurduktan sonra BİR KEZ çağırır (kimlik → satır ve id → sütun eşlemleri).
    void DizinleriKur();
    const OznitelikSutunu* Sutun(std::string_view id) const;
    std::optional<size_t> Satir(ElemanKimligi k) const;

    // Hücre okuma (yoksa nullopt; tür uyuşmazsa nullopt).
    std::optional<double> Sayi(size_t satir, std::string_view id) const;
    std::optional<std::string_view> Metin(size_t satir, std::string_view id) const;  // Metin ve Enum
    std::vector<double> Liste(size_t satir, std::string_view id) const;
    // Gösterim metni: ondalık virgül, birimli ("3,25 m"), Bool "evet" / "hayır", Liste "1, 2". Değer yoksa "".
    std::string Gosterim(size_t satir, const OznitelikSutunu& s) const;

private:
    std::unordered_map<uint64_t, uint32_t> satirDizini_;
    std::unordered_map<std::string, uint32_t> sutunDizini_;
};

using OznitelikPtr = std::shared_ptr<const OznitelikTablosu>;

// Boş tablo (Faz 1 sütun kimlikleri tanımlı, sıfır satır).
OznitelikPtr BosOznitelikTablosu();

// Özellikler paneli için seçili elemanların ortak değerleri: her sütun için tek değer ya da "(çeşitli)" (MIMARI §5.5).
// Dönüş: (sütun id, gösterim metni) çiftleri, tablo sütun sırasıyla; hiçbir seçili elemanda değeri olmayan sütun atlanır.
std::vector<std::pair<std::string, std::string>> OrtakOzellikler(const OznitelikTablosu& t,
                                                                 const std::vector<ElemanKimligi>& secili);

}  // namespace op4
