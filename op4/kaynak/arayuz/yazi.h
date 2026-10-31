// op4 arayüzü — gömülü yazı tipleri (MIMARI §25: sistem yazı tipi kullanılmaz).
//
// Arayüz yazı ailesi TEK yerden gelir: araclar/kimlik_uret.py `ARAYUZ_YAZI = YAZI_ADAYLARI["inter"]` satırı (aile
// belirteci; adaylar tablosunda aile adı + dosya listesi / eksenler; şimdilik Inter yer tutucu, önerilen Noto Sans
// SemiCondensed). Seçilen ailede olmayan semboller (≈ ≤ ≥ ← → …) "Simgeler" alt kümesinden MergeMode ile birleşir. C++ yalnız rol adlarını bilir: "Arayuz400" … "Arayuz700"
// (tema::Agirlik), açılış ekranı için "AcilisInce", "Cormorant500", "Cormorant600". Aile değişimi = o blok + --yazi.
// İşleme: glif ilerlemesi / konumu piksele oturur (PixelSnapH/V), aşırı örnekleme yok, boyut ve konum tam piksel (Ciz). imgui_freetype derlemede etkinse (IMGUI_ENABLE_FREETYPE)
// hafif ipucu (LightHinting) kullanılır; değilse stb_truetype (CMake / bağımlılık A'nındır; rapor: sözleşme isteği).
//
// Veri kaynak/arayuz/yazi_verisi.cpp'dedir (araclar/kimlik_uret.py --yazi üretir: statik örnekler, Latin + Türkçe alt kümesi,
// stb sıkıştırma + base85). ImGui atlası (arayüz) ve DirectWrite (açılış ekranı) aynı açılmış TTF baytlarını kullanır.
// ImGui 1.92 dinamik yazı tipleriyle glifler istenen boyut × DPI'da (1×, 2× …) ilk kullanımda işlenir; Türkçe glifler
// (İ ı ş ğ ü ö ç) alt kümededir.
#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

#include "arayuz/tema.h"

struct ImFont;
struct ImFontAtlas;

namespace op4 {

struct GomuluYazi {
    const char* ad;                 // "Arayuz400", "Arayuz450", … "AcilisInce", "Cormorant600"
    const char* const* parcalar;    // base85 parçaları, nullptr ile biter
    size_t boyut;                   // açılmış TTF bayt sayısı
};
const GomuluYazi* GomuluYazilar(size_t& sayi);
const char* ArayuzYaziAilesi();  // görünen aile adı (Hakkında; üretilmiş)

// Adı verilen yazı tipinin açılmış TTF baytları (ilk çağrıda açılır, süreç boyunca önbellekte). Yoksa / bozuksa null.
const std::vector<uint8_t>* YaziVerisi(std::string_view ad);

struct Yazilar {
    ImFont* inter[5] = {};   // arayüz ailesi, tema::Agirlik sırası: 400, 450, 500, 600, 700
    ImFont* cormorant = nullptr;
    ImFont* Al(tema::Agirlik a) const { return inter[static_cast<int>(a)]; }
};

// Atlası temizler ve gömülü yazı tiplerini ekler (ilk eklenen arayüz 450 varsayılandır). Başarısızsa ImGui'nin gömülü
// yazı tipi yedek olur ve false döner.
bool YazilariYukle(ImFontAtlas* atlas, Yazilar& y);

}  // namespace op4
