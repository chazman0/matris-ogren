// op4 grafik — gölgelendirici geliştirici kipi (--golgelendirici-dizini <klasör>; MIMARI §6.1). Sahibi: A.
//
// Klasör verilirse GomuluGolgelendirici (golgelendirici_bayt.h, S25) gömülü bayt kodu yerine <klasör>\op4.hlsl'yi
// çalışma anında D3DCompileFromFile ile (hata ayıklama bilgisiyle, SM 5.1) derleyip döndürür: HLSL yeniden derleme
// gerektirmeden denenir. Derleme hatası günlüğe yazılır ve boş dönülür (grafik.cpp gömülü metni derler).
#pragma once

#include <string>

namespace op4 {

void GolgelendiriciDiziniAyarla(const std::wstring& dizin);  // ana.cpp, grafik başlamadan önce; boş = gömülü bayt kodu

}  // namespace op4
