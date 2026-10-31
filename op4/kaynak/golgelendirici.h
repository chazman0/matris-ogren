// op4 — HLSL gölgelendiricilerinin metni (çalışma anı yedeği: grafik.cpp, gömülü bayt kodu yoksa D3DCompile ile derler).
// Tek kaynak op4/golgelendiriciler/op4.hlsl'dir; derleme bu dosyayı bayt dizisi olarak golgelendirici_kaynak.inc'e yazar
// (cmake/Golgelendiriciler.cmake). Asıl yol derlemede FXC ile üretilmiş SM 5.1 bayt kodudur (grafik/golgelendirici_bayt.h).
#pragma once

namespace op4 {

// NUL ile biten HLSL metni (sizeof − 1 = metin uzunluğu).
inline constexpr char kGolgelendirici[] = {
#include "golgelendirici_kaynak.inc"
};

}  // namespace op4
