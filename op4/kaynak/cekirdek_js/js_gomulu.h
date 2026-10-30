// op4 model çekirdeği — exe'ye gömülü JS kaynakları (MIMARI §9.2 "Gömme"). Tanım derlemede üretilir (op4/cmake/JsGom.cmake →
// <yapı>/op4_js_gomulu.cpp); sıra yükleme sırasıdır (ön yükleme → docs/ modülleri → op4 cephesi → köprü). Uygulayan: B.
#pragma once

#include <cstddef>

namespace op4 {

struct GomuluJs {
    const char* ad;              // depo köküne göreli yol ("docs/model_ops.js"); QuickJS kaynak adı (hata yığınlarında)
    const unsigned char* veri;   // UTF-8; veri[boyut] == 0 (QuickJS JS_Eval sıfır sonlu girdi ister)
    size_t boyut;
};

const GomuluJs* GomuluJsDosyalari(size_t& sayi);

}  // namespace op4
