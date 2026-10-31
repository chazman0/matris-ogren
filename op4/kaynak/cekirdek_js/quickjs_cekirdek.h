// op4 model çekirdeği — QuickJS-ng çekirdeğinin B içi kurucusu (sözleşme S11'in uygulaması; MIMARI §9.3, §9.4). Uygulayan: B.
//
// ModelCekirdegiOlustur (model_cekirdegi.h) bunu varsayılan geri al sınırlarıyla çağırır. Çekirdek modülü
// (cekirdek_modulu.cpp) ve sınamalar sınırları Ayarlar::cekirdek'ten verir: CekirdekAyari (S11) bu alanları taşımaz.
#pragma once

#include <memory>
#include <string>

#include "cekirdek/model_cekirdegi.h"

namespace op4 {

// Geri al yığınının sınırları (MIMARI §9.4; Ayarlar::cekirdek geriAlAdim / geriAlMb). En az bir adım her zaman tutulur.
struct GeriAlSiniri {
    int adim = 100;
    double mb = 512;
};

std::unique_ptr<ModelCekirdegi> QuickJsCekirdegiOlustur(const CekirdekAyari& ayar, const GeriAlSiniri& sinir, std::string& hata);

}  // namespace op4
