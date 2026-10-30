// op4 çekirdek — model gezgini ağacı. TASLAK (sözleşme S10): yalnız kök ve toplam sayı. Uygulayan: C, Faz 1 iş 1.4.
#include "cekirdek/gezgin.h"

#include <algorithm>

namespace op4 {

GezginDugumu GezginAgaciKur(const OznitelikTablosu& t) {
    GezginDugumu kok;
    kok.anahtar = "proje";
    kok.baslik = "Proje";
    kok.elemanlar = t.satirlar;
    std::sort(kok.elemanlar.begin(), kok.elemanlar.end());
    kok.elemanlar.erase(std::unique(kok.elemanlar.begin(), kok.elemanlar.end()), kok.elemanlar.end());
    kok.sayi = kok.elemanlar.size();
    return kok;
}

}  // namespace op4
