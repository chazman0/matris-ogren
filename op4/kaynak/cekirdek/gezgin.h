// op4 çekirdek sözleşmesi — model gezgini ağacı (MIMARI §5.6; "F1 paket sözleşmeleri" §S10).
//
// Uygulayan: C (arayuz-goruntu) — kaynak/cekirdek/gezgin.cpp; platformdan bağımsız, Linux'ta sınanır.
// Girdi: öznitelik tablosu (B). Faz 1 ağacı: Proje → Seviyeler ve katlar → Kat k → alt tür (Kolon, Kiriş, Döşeme …) →
// kullanım yeri (köşe, kenar, iç …); her düğümde eleman sayısı ve elemanların kimlikleri (tıkla seç, Ctrl ile ekle).
// Kata atanmamış elemanlar (kat listesi boş) "Temel ve kat dışı" düğümünde toplanır. Kat aralığını aşan kolon her katında
// görünür (sayılar kat düğümünde tekrar sayılabilir; Proje toplamı tekrarsızdır).
#pragma once

#include <cstddef>
#include <string>
#include <vector>

#include "cekirdek/kimlik.h"
#include "cekirdek/oznitelik.h"

namespace op4 {

struct GezginDugumu {
    std::string anahtar;                  // kararlı yol: "kat:2/alt_tur:kolon/kullanim_yeri:kose" (açık / kapalı durumu için)
    std::string baslik;                   // "Kat 2 (+6.40)", "Kolon", "köşe"
    size_t sayi = 0;                      // alt ağaçtaki tekrarsız eleman sayısı
    std::vector<ElemanKimligi> elemanlar; // sıralı, tekrarsız; bu düğüm seçilince seçilecek küme
    std::vector<GezginDugumu> cocuklar;
};

// Kök "Proje" düğümünü kurar. Tablo boşsa çocuksuz kök (sayi 0).
GezginDugumu GezginAgaciKur(const OznitelikTablosu& t);

}  // namespace op4
