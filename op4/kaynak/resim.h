// op4 — PNG okuma / yazma (Windows Imaging Component; ek kitaplık gerekmez). COM, çağıran iş parçacığında açık olmalı.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace op4 {

struct Resim {
    int g = 0, y = 0;
    std::vector<uint8_t> bgra;  // 32 bit, önceden çarpılmış alfa (PBGRA), üstten alta, sıkı
};

// PNG'yi okur; hedefG/hedefY > 0 ise yüksek kaliteli (Fant) ölçekleme ile o boyuta getirir.
bool PngOku(const std::wstring& yol, Resim& r, std::string& hata, int hedefG = 0, int hedefY = 0);
// Yalnız boyutları okur.
bool PngBoyutu(const std::wstring& yol, int& g, int& y);
// 4 bayt/piksel kaynaktan (bgr = true ise BGRA, değilse RGBA; üstten alta, satır adımı g*4) 24 bit PNG yazar.
bool PngYaz(const std::wstring& yol, int g, int y, const uint8_t* piksel, bool bgr, std::string& hata);

}  // namespace op4
