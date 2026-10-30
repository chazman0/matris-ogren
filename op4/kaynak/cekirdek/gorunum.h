// op4 çekirdek sözleşmesi — görünüm durumu ve çizici girdisi (MIMARI §6, §7.3; "F1 paket sözleşmeleri" §S9).
//
// Görünüm durumu Hizmetler::gorunum'dadır ve paketler arası tek ortak "ne çizilecek" bilgisidir:
//   C (arayuz-goruntu) okur ve çizer; görünüm kipi, ızgara, standart görünümler, kamera, üzerine gelinen eleman C'nindir.
//   D (dosya-cozum) `sonuc` boyamasını yazar (D/C renkleri, eski işareti) ve kameraları .op4'e C'nin katkısıyla kaydeder.
//   B'nin sahnesi Hizmetler::sahne'den gelir (bkz. hizmetler.h); burada tutulmaz.
// Değişiklikten sonra `CizimIste()` çağrılır: çizim isteğe bağlıdır (MIMARI §6.1), boşta kare üretilmez.
#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "cekirdek/kimlik.h"
#include "cekirdek/olay.h"

namespace op4 {

enum class GorunumKipi : uint8_t {
    Cubuk = 0,          // eksen çizgileri, sabit piksel kalınlığı (Faz 1)
    Kesit = 1,          // gerçek kesit katıları (Faz 2; Faz 1'de deneme ekstrüzyonu)
    KesitVeEksen = 2,
};
// Alt+1…4 (MIMARI §7.1): 3B (izometrik, döndürülebilir), Plan (Z aksı; ortografik), Ön cephe (Y'ye bakış), Yan cephe.
enum class StandartGorunum : uint8_t { Izometrik3B = 0, Plan = 1, OnCephe = 2, YanCephe = 3 };
enum class RenkKipi : uint8_t {
    Tur = 0,     // eleman türü paleti (MIMARI §6.5)
    Sonuc = 1,   // D/C renkleri (SonucBoyamasi)
};

// Eleman başına renk (0xAABBGGRR değil: 0xRRGGBBAA, sRGB). Sıralı (kimlik), tekrarsız.
struct ElemanRengi {
    ElemanKimligi kimlik;
    uint32_t rgba = 0;
};

// D'nin çözüm sonrası ürettiği boyama: çizici RenkKipi::Sonuc iken bunu kullanır. Listede olmayan eleman nötr gri çizilir.
// `eski` true ise (model çözümden sonra değişti) çizici renkleri soluk (%50 doygunluk) çizer ve D durum çubuğunda
// "Sonuçlar eski" rozeti gösterir (MIMARI §4 çözüm akışı, F1 iş 1.5).
struct SonucBoyamasi {
    uint64_t surum = 0;              // her yeni boyamada artar
    std::string cozumKimligi;        // bina_kimlik / bina_coz cozum_kimligi
    std::vector<ElemanRengi> renkler;
    bool eski = false;
    std::string aciklama;            // gösterge başlığı: "D/C (en büyük, bütün kombinasyonlar)"
};

struct GorunumDurumu {
    GorunumKipi kip = GorunumKipi::Cubuk;
    RenkKipi renkKipi = RenkKipi::Tur;
    bool izgara = true;             // F7
    bool kenarlar = true;
    ElemanKimligi uzerinde;         // imlecin altındaki eleman (C yazar; vurgu)
    std::shared_ptr<const SonucBoyamasi> sonuc;  // D yazar; null = yok

    // Bir sonraki karede yeniden çizim iste (her iş parçacığından değil: yalnız UI iş parçacığı).
    void CizimIste() { cizimIstendi_ = true; }
    bool CizimIstendiMi() const { return cizimIstendi_; }
    void CizimYapildi() { cizimIstendi_ = false; }

    // Kamera / görünüm komutları için istekler. Yazan: herkes (ör. D belge açınca SigdirIste); tüketen: C her karede.
    void SigdirIste() { sigdirIstendi_ = true; CizimIste(); }
    bool SigdirIstendiMi() const { return sigdirIstendi_; }
    void SigdirYapildi() { sigdirIstendi_ = false; }

    Olay<> degisti;   // kip, renk kipi, ızgara ya da sonuç boyaması değişince (yazan yayınlar)

private:
    bool cizimIstendi_ = true;
    bool sigdirIstendi_ = false;
};

}  // namespace op4
