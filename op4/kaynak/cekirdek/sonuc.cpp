// op4 çekirdek — sonuç özeti. DcRengi, BoyamaKur ve SonucDurumu tamdır; yanıt çözümü ve .op4 sonuc/ozet.json dönüşümü
// TASLAKTIR (sözleşme S19). Uygulayan: D (dosya-cozum), F1 iş 1.5.
#include "cekirdek/sonuc.h"

#include <cmath>

namespace op4 {

uint32_t DcRengi(double dc) {
    if (!(dc >= 0) || !std::isfinite(dc)) return 0x8C8C8CFFu;
    if (dc < 0.7) return 0x22C55EFFu;
    if (dc < 0.9) return 0xFACC15FFu;
    if (dc <= 1.0) return 0xFB923CFFu;
    return 0xEF4444FFu;
}

std::shared_ptr<const SonucBoyamasi> BoyamaKur(const SonucOzeti& ozet, uint64_t surum) {
    auto b = std::make_shared<SonucBoyamasi>();
    b->surum = surum;
    b->cozumKimligi = ozet.cozumKimligi;
    b->aciklama = "D/C (en büyük, bütün kombinasyonlar)";
    b->renkler.reserve(ozet.elemanlar.size());
    for (const ElemanSonucu& e : ozet.elemanlar) b->renkler.push_back({e.kimlik, DcRengi(e.dc)});
    return b;
}

void SonucDurumu::Ata(SonucOzeti ozet, std::shared_ptr<const std::string> veri) {
    ozet_ = std::move(ozet);
    veri_ = std::move(veri);
    var_ = true;
    eski_ = false;
    degisti.Yay();
}

void SonucDurumu::EskiIsaretle() {
    if (!var_ || eski_) return;
    eski_ = true;
    degisti.Yay();
}

void SonucDurumu::Temizle() {
    if (!var_ && !eski_) return;
    var_ = eski_ = false;
    ozet_ = SonucOzeti{};
    veri_.reset();
    degisti.Yay();
}

bool CozumYanitiniCoz(std::string_view, SonucOzeti&, std::string&, std::string& hata) {
    hata = "Çözüm yanıtı çözümü henüz uygulanmadı (F1 iş 1.5).";
    return false;
}

std::string SonucOzetiJson(const SonucOzeti&) { return "{}"; }

bool SonucOzetiOku(std::string_view, SonucOzeti&, std::string& hata) {
    hata = "sonuc/ozet.json okuma henüz uygulanmadı (F1 iş 1.5).";
    return false;
}

}  // namespace op4
