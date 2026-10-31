// op4 grafik — sahne anlığından katı (ekstrüzyon) görünüm ağı (MIMARI §6.4, §6.6; Faz 1 "deneme ekstrüzyonu": gerçek
// kesit katıları Faz 2'de kesitCoz ile gelir). Sahibi: C. Platformdan bağımsızdır (DX12'ye geometri.h Ag'ı verilir).
//
// Çubuklar kesit ailesine göre uzatılır: I (h, b, tw, tf, r bilinen ya da türe göre varsayılan), diğerleri dikdörtgen;
// paneller kalınlıkları kadar (üst yüz düğüm düzleminde) uzatılır. Elemanlar renk sınıfına göre gruplanır (Ag::parcalar):
// tür paleti, seçili (açık vurgu dolgu + vurgu kenar), üzerinde (kenar), yalnız seçili kipinde soluk.
#pragma once

#include <cstdint>
#include <vector>

#include "cekirdek/kimlik.h"
#include "cekirdek/sahne.h"
#include "geometri.h"

namespace op4 {

struct SahneAgiAyari {
    const std::vector<ElemanKimligi>* secim = nullptr;  // sıralı
    ElemanKimligi uzerinde;
    bool yalnizSecili = false;
    int yayParca = 2;  // kesit köşe yuvarlatması (LOD0 ±%2 Faz 2'de)
};

Ag SahneAgiKur(const SahneAnlik& s, const SahneAgiAyari& a);

}  // namespace op4
