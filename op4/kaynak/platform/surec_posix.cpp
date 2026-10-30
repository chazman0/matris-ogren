// op4 platform — alt süreç (posix). TASLAK (sözleşme S14): Baslat her zaman başarısız. Uygulayan: A (derleme-motor), F1 iş 1.2.
#include "platform/surec.h"

namespace op4 {
namespace {

class TaslakSurec final : public Surec {
public:
    bool Baslat(const SurecAyari&, std::string& hata) override {
        hata = "Alt süreç desteği henüz uygulanmadı (F1 iş 1.2).";
        return false;
    }
    bool Yaz(const void*, size_t) override { return false; }
    long long Oku(void*, size_t) override { return -1; }
    void YazmayiKapat() override {}
    bool Calisiyor() const override { return false; }
    bool Bekle(uint32_t, int& cikisKodu) override {
        cikisKodu = -1;
        return true;
    }
    void Sonlandir() override {}
    long long Kimlik() const override { return 0; }
};

}  // namespace

std::unique_ptr<Surec> SurecOlustur() { return std::make_unique<TaslakSurec>(); }

}  // namespace op4
