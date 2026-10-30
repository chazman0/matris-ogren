// op4 grafik sözleşmesi — derlemede üretilmiş gölgelendirici bayt kodu (MIMARI §6.1, D12; sözleşme S25).
//
// Uygulayan: A (derleme-motor) — cmake/Golgelendiriciler.cmake op4/golgelendiriciler/*.hlsl dosyalarını Windows SDK fxc.exe
// ile vs_5_1 / ps_5_1'e derler ve bayt kodunu bir kaynak dosyasına gömer; GomuluGolgelendirici o diziyi döndürür.
// Kullanan  : C — grafik.cpp boru hattı kurulumunda önce bunu sorar; boş dönerse (taslak ya da --golgelendirici-dizini)
// çalışma anında D3DCompile ile derler. Giriş adları: vs_kati, ps_kati, vs_cizgi, ps_cizgi, vs_tam, ps_arka, ps_izgara.
#pragma once

#include <cstddef>

namespace op4 {

struct GolgelendiriciBayt {
    const void* veri = nullptr;
    size_t boyut = 0;
    bool Var() const { return veri && boyut; }
};

GolgelendiriciBayt GomuluGolgelendirici(const char* giris);

}  // namespace op4
