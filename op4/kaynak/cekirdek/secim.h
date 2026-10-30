// op4 çekirdek sözleşmesi — seçim (MIMARI §7.1, §11; "F1 paket sözleşmeleri" §S7).
//
// Tek seçim nesnesi Hizmetler::secim'dir. Yazanlar: C (fare tıkı, pencere seçimi, model gezgini, SEÇ komutu), D (açılan
// belgeden sonra Temizle), B'nin rapor yayını sonrası Ayikla (bkz. hizmetler.h ModelIslemiSonrasi). Okuyanlar: çizici
// (vurgu), Özellikler paneli, durum çubuğu (seçim sayısı), komutların kullanılabilirlik koşulları.
// Seçim geri al kapsamına girmez (MIMARI §9.4). Liste her zaman sıralı (ElemanKimligi::Anahtar) ve tekrarsızdır.
#pragma once

#include <cstdint>
#include <span>
#include <vector>

#include "cekirdek/kimlik.h"
#include "cekirdek/olay.h"

namespace op4 {

enum class SecimKipi : uint8_t {
    Yeni = 0,       // seçimi verilen kümeyle değiştir (sol tık, Seç ve Süz "Yeni seçim")
    Ekle = 1,       // birleşim (Ctrl + tık / Ctrl + sol sürükle)
    Cikar = 2,      // fark (Shift + tık, Ctrl + Shift + sol sürükle)
    Tersle = 3,     // simetrik fark (seçim döngüsü, gezgin Ctrl + tık)
    IcindeSuz = 4,  // kesişim ("Seçim içinde süz")
};

class Secim {
public:
    const std::vector<ElemanKimligi>& Liste() const { return liste_; }
    size_t Sayi() const { return liste_.size(); }
    bool Bos() const { return liste_.empty(); }
    bool Iceriyor(ElemanKimligi k) const;
    size_t Say(ElemanTuru t) const;

    // Kümeyi kipe göre uygular; seçim değiştiyse Surum artar ve `degisti` BİR KEZ yayınlanır.
    void Uygula(std::span<const ElemanKimligi> kume, SecimKipi kip);
    void Uygula(ElemanKimligi k, SecimKipi kip) { Uygula(std::span<const ElemanKimligi>(&k, 1), kip); }
    void Temizle();
    // Silinen elemanları seçimden düşürür (çekirdek raporunun `silinen` listesi). Değişirse `degisti` yayınlanır.
    void Ayikla(std::span<const ElemanKimligi> silinen);

    // Her değişiklikte +1; çizici vurgu tamponunu yalnız sürüm değişince yeniler.
    uint64_t Surum() const { return surum_; }

    Olay<> degisti;

private:
    void Ata(std::vector<ElemanKimligi> yeni);
    std::vector<ElemanKimligi> liste_;
    uint64_t surum_ = 0;
};

}  // namespace op4
