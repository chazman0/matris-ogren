// op4 çekirdek — seçim kümesi (sözleşme S7; tam uygulama).
#include "cekirdek/secim.h"

#include <algorithm>
#include <iterator>

namespace op4 {

bool Secim::Iceriyor(ElemanKimligi k) const { return std::binary_search(liste_.begin(), liste_.end(), k); }

size_t Secim::Say(ElemanTuru t) const {
    return static_cast<size_t>(std::count_if(liste_.begin(), liste_.end(), [t](const ElemanKimligi& k) { return k.tur == t; }));
}

void Secim::Ata(std::vector<ElemanKimligi> yeni) {
    if (yeni == liste_) return;
    liste_ = std::move(yeni);
    ++surum_;
    degisti.Yay();
}

void Secim::Uygula(std::span<const ElemanKimligi> kume, SecimKipi kip) {
    std::vector<ElemanKimligi> k;
    k.reserve(kume.size());
    for (const ElemanKimligi& e : kume)
        if (e.Gecerli()) k.push_back(e);
    std::sort(k.begin(), k.end());
    k.erase(std::unique(k.begin(), k.end()), k.end());
    std::vector<ElemanKimligi> o;
    switch (kip) {
        case SecimKipi::Yeni:
            o = std::move(k);
            break;
        case SecimKipi::Ekle:
            std::set_union(liste_.begin(), liste_.end(), k.begin(), k.end(), std::back_inserter(o));
            break;
        case SecimKipi::Cikar:
            std::set_difference(liste_.begin(), liste_.end(), k.begin(), k.end(), std::back_inserter(o));
            break;
        case SecimKipi::Tersle:
            std::set_symmetric_difference(liste_.begin(), liste_.end(), k.begin(), k.end(), std::back_inserter(o));
            break;
        case SecimKipi::IcindeSuz:
            std::set_intersection(liste_.begin(), liste_.end(), k.begin(), k.end(), std::back_inserter(o));
            break;
    }
    Ata(std::move(o));
}

void Secim::Temizle() { Ata({}); }

void Secim::Ayikla(std::span<const ElemanKimligi> silinen) {
    if (silinen.empty() || liste_.empty()) return;
    Uygula(silinen, SecimKipi::Cikar);
}

}  // namespace op4
