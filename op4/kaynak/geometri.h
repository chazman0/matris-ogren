// op4 — eleman geometrisi: kesit dış çizgisi (2B) → boyuna uzatılmış katı ağ (3B), kenar çizgileri ve çubuk ekseni.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "matematik.h"

namespace op4 {

struct Kose {  // köşe (vertex): konum + normal
    V3 p;
    V3 n;
};

// Ağın renk parçası: [indisBas, indisBas + indisSayi) üçgenleri ve [kenarBas, kenarBas + kenarSayi) kenar köşeleri aynı
// renkle çizilir (renkler IM_COL32 düzeninde, sRGB). Parça listesi boşsa ağ tek renkle çizilir (Faz 0 yolu).
struct AgParcasi {
    uint32_t indisBas = 0, indisSayi = 0, kenarBas = 0, kenarSayi = 0;
    uint32_t renk = 0, kenarRenk = 0;
};

struct Ag {  // üçgen ağı + çizgi listeleri
    std::vector<AgParcasi> parcalar;
    std::vector<Kose> koseler;
    std::vector<uint32_t> indisler;
    std::vector<V3> kenarlar;   // çizgi listesi (her çift bir doğru): kesit görünümünün keskin kenarları
    std::vector<V3> eksenler;   // çizgi listesi: çubuk görünümü (eleman eksenleri)
    V3 enKucuk{1e30f, 1e30f, 1e30f}, enBuyuk{-1e30f, -1e30f, -1e30f};
    void Kapsa(V3 p);
};

// Kesit: yerel (u, v) düzleminde saat yönü tersine (CCW) çokgen; v = kesit yüksekliği yönü (güçlü eksen dik).
struct Kesit2B {
    std::string ad;
    std::vector<float> u, v;
};

// Haddelenmiş I / H profili (h, b, tw, tf, r: metre). yayParca: her köşe yuvarlatmasının doğru parçası sayısı.
Kesit2B IProfil(const std::string& ad, float h, float b, float tw, float tf, float r, int yayParca);

// Kesiti bas → son ekseni boyunca uzatır. Yerel eksenler: x = eksen, v = dünya Z'nin eksene dik izdüşümü
// (düşey elemanda dünya X), u = v × x. kenarAcisi (derece): komşu yüzey normalleri arasındaki açı bundan büyükse keskin
// kenar (ayrı normal + kenar çizgisi), küçükse yumuşak (ortak normal).
void Uzat(const Kesit2B& k, V3 bas, V3 son, Ag& ag, float kenarAcisi = 40.0f);

// Basit kulak kırpma (ear clipping) üçgenleme; CCW çokgen. Çıktı: yerel indis üçlüleri.
std::vector<uint32_t> Ucgenle(const std::vector<float>& u, const std::vector<float>& v);

// İskelet sahnesi: iki çerçeveli küçük çelik yapı (HE340A kolon ve kirişler, IPE300 bağ kirişleri).
Ag OrnekSahne(int yayParca = 4);

}  // namespace op4
