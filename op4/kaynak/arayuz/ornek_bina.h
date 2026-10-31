// op4 arayüzü — ekran sınaması ve önizleme için örnek bina (taslaklardaki "Depo Binası – Tokat OSB": akslar A–D × 1–5,
// 6 m açıklık, katlar ±0,00 / +4,50 / +9,00 / +13,50; HE340A kolon, IPE400 kiriş, IPE200 aşık, L100x10 X çapraz,
// betonarme döşeme). Sahne anlığı + öznitelik tablosu olarak kurulur (B'nin çekirdeği ve D'nin şablonları gelmeden
// --test-ekran görüntülerinin taslakla karşılaştırılabilmesi için). Kullanıcıya sunulan bir şablon DEĞİLDİR.
#pragma once

#include <vector>

#include "cekirdek/oznitelik.h"
#include "cekirdek/sahne.h"

namespace op4 {

struct OrnekBina {
    SahnePtr sahne;
    OznitelikPtr oznitelik;
    std::vector<ElemanKimligi> taslakSecimi;  // taslaktaki seçim: Kat 2'de 1 ve 2 akslarındaki x kirişleri (6 kiriş)
    ElemanKimligi taslakUzerinde;             // taslaktaki üzerine gelinen kolon
};

OrnekBina OrnekBinaKur();

}  // namespace op4
