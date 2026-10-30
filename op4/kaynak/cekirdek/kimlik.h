// op4 çekirdek sözleşmesi — eleman kimliği (MIMARI §4, "F1 paket sözleşmeleri" §S1).
//
// Seçilebilen, vurgulanabilen ve özniteliği olan her şey tek bir 8 baytlık değerle anılır: ElemanKimligi {tur, alt, no}.
// Seçim (Secim), seçme dizini (SecmeDizini), öznitelik tablosu satırları, çekirdeğin değişiklik raporları (eklenen / silinen
// / değişen), sonuç eşlemesi (D/C) ve .op4 içindeki seçim kümeleri hep bu kimliği kullanır.
//
// Platformdan bağımsızdır (Windows başlığı yok); op4_cekirdek kitaplığının parçasıdır ve Linux'ta sınanır.
#pragma once

#include <compare>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <string_view>

namespace op4 {

// Eleman türü. Sayısal değerler op4/veri/sahne_kodlari.json "eleman_turu" tablosuyla aynıdır ve .op4 dosyalarına
// (secim/kumeler.json) yazılır: mevcut değerler DEĞİŞTİRİLMEZ, yeni türler yalnız sona eklenir.
enum class ElemanTuru : uint8_t {
    Yok = 0,
    Cubuk = 1,       // no: bina JSON çubuk no'su
    Panel = 2,       // no: panel no'su
    Dugum = 3,       // no: düğüm no'su (aks–kat: 1000·kat + 20·ix + iy + 1; serbest/bölme: 100001…; aks kesişimi: 800001…,
                     //     yalnız aks düzeni değişmedikçe kararlı — çekirdek atar, bkz. op4_cekirdek.js sahne())
    Mesnet = 4,      // no: mesnetin bağlı olduğu düğüm no'su
    Yuk = 5,         // no: ek_yukler dizisindeki sıra (0 tabanlı)
    Aks = 6,         // alt: aks sistemi sırası (0 = genel akslar), no: eksen·65536 + aks sırası (eksen 0 x, 1 y, 2 z)
    AksSistemi = 7,  // no: aks_sistemleri sırası + 1 (0 = genel sistem)
    Temel = 8,       // no: temelin bağlı olduğu düğüm no'su (tekil); şerit / radye için çekirdek atar
    Referans = 9,    // IFC referans katmanı (Faz 6)
    Olcu = 10,       // ölçü / ölçüm nesnesi (Faz 4)
};
inline constexpr int ELEMAN_TURU_SAYISI = 11;

// Seçilebilir her şeyin kimliği. Alanlar 8 bayta sığar (tür 1, dolgu 1, alt 2, no 4) ve değerle taşınır.
//   no  : türüne göre modeldeki numara (yukarıdaki tabloya bakın).
//   alt : tür içi alt öğe: 0 = bütün eleman. Faz 1'de yalnız Aks kullanır; Faz 4 tutamaçlarında çubuk ucu (1 = i, 2 = j),
//         panel kenarı / köşesi (1…n) için ayrılmıştır.
// Kimlik modelin içinde kararlıdır: aynı eleman, onu silmeyen işlemlerden sonra aynı kimliği taşır. Silinen bir elemanın
// numarası yeniden kullanılabilir; bu yüzden kimlik listeleri (seçim, kümeler) her model değişikliğinde çekirdeğin
// "silinen" listesiyle ayıklanır (Secim::Ayikla).
struct ElemanKimligi {
    ElemanTuru tur = ElemanTuru::Yok;
    uint16_t alt = 0;
    uint32_t no = 0;

    constexpr bool Gecerli() const { return tur != ElemanTuru::Yok; }
    // Sıralama ve karma anahtarı: tür (bit 48–55) | alt (bit 32–47) | no (bit 0–31).
    constexpr uint64_t Anahtar() const {
        return (static_cast<uint64_t>(tur) << 48) | (static_cast<uint64_t>(alt) << 32) | static_cast<uint64_t>(no);
    }
    static constexpr ElemanKimligi AnahtardanKur(uint64_t a) {
        return ElemanKimligi{static_cast<ElemanTuru>((a >> 48) & 0xFFu), static_cast<uint16_t>((a >> 32) & 0xFFFFu),
                             static_cast<uint32_t>(a & 0xFFFFFFFFu)};
    }
    friend constexpr bool operator==(const ElemanKimligi& a, const ElemanKimligi& b) { return a.Anahtar() == b.Anahtar(); }
    friend constexpr std::strong_ordering operator<=>(const ElemanKimligi& a, const ElemanKimligi& b) {
        return a.Anahtar() <=> b.Anahtar();
    }
};
static_assert(sizeof(ElemanKimligi) == 8, "ElemanKimligi 8 bayt olmalı");

// Kısa kurucular.
constexpr ElemanKimligi CubukKimligi(uint32_t no) { return {ElemanTuru::Cubuk, 0, no}; }
constexpr ElemanKimligi PanelKimligi(uint32_t no) { return {ElemanTuru::Panel, 0, no}; }
constexpr ElemanKimligi DugumKimligi(uint32_t no) { return {ElemanTuru::Dugum, 0, no}; }

// Türün kod adı (ASCII, JSON'da ve günlükte kullanılır): "cubuk", "panel", "dugum", "mesnet", "yuk", "aks", "aks_sistemi",
// "temel", "referans", "olcu"; Yok ve bilinmeyen değer için "yok".
const char* TurKodu(ElemanTuru t);
// Türün Türkçe görünen adı: "Çubuk", "Panel", "Düğüm", …
const char* TurAdi(ElemanTuru t);
std::optional<ElemanTuru> TurKodundan(std::string_view kod);

// Metin biçimi: "<tür kodu>:<no>" ya da alt ≠ 0 ise "<tür kodu>:<no>/<alt>" (ör. "cubuk:12", "aks:65538/0").
// Komut satırı, senaryolar, günlük ve .op4 seçim kümeleri bu biçimi kullanır. KimlikCoz bunun tersidir; geçersizde nullopt.
std::string KimlikMetni(ElemanKimligi k);
std::optional<ElemanKimligi> KimlikCoz(std::string_view metin);

struct ElemanKimligiKarma {
    size_t operator()(const ElemanKimligi& k) const noexcept { return std::hash<uint64_t>{}(k.Anahtar()); }
};

}  // namespace op4

template <>
struct std::hash<op4::ElemanKimligi> {
    size_t operator()(const op4::ElemanKimligi& k) const noexcept { return op4::ElemanKimligiKarma{}(k); }
};
