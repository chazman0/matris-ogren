// op4 çekirdek sözleşmesi — çözüm sonucu özeti ve D/C boyaması (MIMARI §4 çözüm akışı, §13.1 sonuc/;
// "F1 paket sözleşmeleri" §S19).
//
// Sahibi: D (dosya-cozum) — F5 eşzamansız çözüm, iptal, sonuç özeti paneli, D/C renkleri, eski işareti, .op4 sonuc/ katkısı.
// Okuyan: C (çizici SonucBoyamasi'nı kullanır; bkz. gorunum.h), herkes (sonuç var mı / eski mi).
#pragma once

#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

#include "cekirdek/gorunum.h"
#include "cekirdek/kimlik.h"
#include "cekirdek/model_cekirdegi.h"
#include "cekirdek/olay.h"

namespace op4 {

struct SonucOzeti {
    std::string cozumKimligi;     // yapi.cozum_kimligi (bina_kimlik ile karşılaştırılır)
    std::string tarih;            // ISO 8601 UTC
    std::string motorSurumu;
    uint64_t sahneSurumu = 0;     // çözülen modelin sahne sürümü (eski işareti için)
    double sureMs = 0;
    std::string ozetMetni;        // web_kopru sonuc_metin: "216 SD, 12 kombinasyon; G = … kN, Q = … kN"
    size_t sdSayisi = 0, kombinasyonSayisi = 0;
    double enBuyukDc = -1;        // < 0 = tasarım yok
    ElemanKimligi enBuyukDcElemani;
    size_t asanSayisi = 0;        // D/C > 1
    std::vector<std::string> uyarilar;
    std::vector<ElemanSonucu> elemanlar;  // çekirdek SonucEsle sonucu (kimliğe göre sıralı)
    // Yük toplamları (kN): bina_coz veri.ozet.toplam_G / toplam_Q (motor yanıtından; özet metninden ayrıştırılmaz),
    // sonuc/ozet.json'da ozet.toplam_G / toplam_Q. Yanıtta ya da kayıtta yoksa NaN (panel "—" gösterir).
    double toplamG = std::numeric_limits<double>::quiet_NaN();
    double toplamQ = std::numeric_limits<double>::quiet_NaN();
};

// D/C renk ölçeği (web sürümüyle aynı, docs/bina.js dcSinif + style.css): < 0,7 yeşil #22c55e, 0,7–0,9 sarı #facc15,
// 0,9–1,0 turuncu #fb923c, > 1,0 kırmızı #ef4444; tasarım yok (dc < 0 ya da NaN) gri #8c8c8c. Dönüş 0xRRGGBBAA.
uint32_t DcRengi(double dc);
// Özetten çizici boyaması kurar (her elemanSonucu → DcRengi).
std::shared_ptr<const SonucBoyamasi> BoyamaKur(const SonucOzeti& ozet, uint64_t surum);

class SonucDurumu {
public:
    bool Var() const { return var_; }
    bool Eski() const { return eski_; }
    const SonucOzeti& Ozet() const { return ozet_; }
    // Son bina_coz yanıtındaki "veri" nesnesinin JSON metni (sonuc/veri.json, IfcDisari D/C'si, ayrıntı istekleri).
    const std::shared_ptr<const std::string>& Veri() const { return veri_; }

    void Ata(SonucOzeti ozet, std::shared_ptr<const std::string> veri);
    // Model değişince (ModelIslemiSonrasi çağırır). Zaten eskiyse ya da sonuç yoksa olay yayınlanmaz.
    void EskiIsaretle();
    void Temizle();

    // Süren çözüm (durum çubuğu ilerlemesi, iptal düğmesi). 0 = yok.
    uint64_t surenIstek = 0;
    double surenBaslangicMs = 0;

    Olay<> degisti;

private:
    bool var_ = false, eski_ = false;
    SonucOzeti ozet_;
    std::shared_ptr<const std::string> veri_;
};

// bina_coz yanıtını (calistir() metni) çözer: veri nesnesini ayrı metin olarak çıkarır, özet alanlarını doldurur.
// Çekirdek eşlemesini (elemanlar) çağıran ekler. Hata yanıtında false + hata.
bool CozumYanitiniCoz(std::string_view calistirYaniti, SonucOzeti& ozet, std::string& veriMetni, std::string& hata);
// .op4 sonuc/ozet.json ↔ SonucOzeti.
std::string SonucOzetiJson(const SonucOzeti& ozet);
bool SonucOzetiOku(std::string_view json, SonucOzeti& ozet, std::string& hata);

}  // namespace op4
