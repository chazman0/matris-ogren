// op4 çekirdek — proje küçük resmi (onizleme.png, 256×256; MIMARI §13.1). Sahibi: D (dosya-cozum).
//
// GPU'suz, platformdan bağımsız çizim: sahne anlığı izometrik izdüşümle (Stüdyo model zemini, tür renkleri, döşemeler
// %24 saydam) kenar yumuşatmalı çizgilerle çizilir ve PNG'ye kodlanır. Başlangıç paneli (C) ve son dosyalar listesi bunu
// gösterir; Windows kabuğu dosya önizlemesi için de kullanılabilir. Aynı sahne → aynı baytlar.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "cekirdek/sahne.h"

namespace op4 {

// RGBA8 görüntü (satır sırası yukarıdan aşağı).
struct OnizlemeResmi {
    int genislik = 0, yukseklik = 0;
    std::vector<uint8_t> rgba;
};

OnizlemeResmi OnizlemeCiz(const SahneAnlik& sahne, int boyut = 256);
std::string OnizlemePng(const SahneAnlik& sahne, int boyut = 256);

}  // namespace op4
