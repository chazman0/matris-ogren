// op4 arayüzü — çizgi ikonları (MIMARI §25; tasarim.md §8). Kaynak: op4/tasarim/taslaklar/studyo/tuval.py IKONLAR —
// aynı 24 birimlik kutu, aynı yollar; ImDrawList yollarına çevrilmiştir (emoji ya da yazı tipi simgesi yok).
// Kalem varsayılan 1,5 px × DPI ölçeği, yuvarlak uç; renk tek (etkin metin, pasif metin2, açıklama metin3).
#pragma once

#include <cstdint>
#include <string_view>

struct ImDrawList;
struct ImVec2;

namespace op4 {

// ad: tuval.py ikon adı ("kiris", "kolon", "sec", …) ya da op4 eki ("yeni", "sablon", "ice", "izgara", "cephe_on",
// "cephe_yan", "baslangic", "klavye", "geri_yukle"). Bilinmeyen ad boş kutu çizer ve false döner.
// (x, y): ikon kutusunun sol üstü (piksel); boy: kutu kenarı (piksel); kalem: çizgi kalınlığı (piksel).
bool IkonCiz(ImDrawList* dl, std::string_view ad, float x, float y, float boy, uint32_t renk, float kalem);
bool IkonVar(std::string_view ad);

}  // namespace op4
