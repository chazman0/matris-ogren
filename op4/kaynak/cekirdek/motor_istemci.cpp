// op4 çekirdek — süreç tabanlı motor istemcisi. TASLAK (sözleşme S13): motor yokmuş gibi davranır; her istek bir sonraki
// Pompala'da MotorHatasi ("motor_yok") alır (Y1 değişmezi taslakta da korunur). Uygulayan: A (derleme-motor), F1 iş 1.2.
#include <deque>
#include <utility>

#include "cekirdek/motor_hizmeti.h"
#include "cekirdek/motor_protokol.h"

namespace op4 {
namespace {

class TaslakMotorIstemcisi final : public MotorHizmeti {
public:
    void Baslat(const MotorAyari&) override {
        durum_.baslatildi = true;
        durum_.hazir = true;
        durum_.basarili = false;
        durum_.hata = "Süreç tabanlı hesap motoru henüz uygulanmadı (F1 iş 1.2).";
        durum_.aciklama = "Hesap motoru yok";
    }
    MotorDurumOzeti Durum(MotorRolu) const override {
        MotorDurumOzeti d = durum_;
        d.bekleyen = bekleyen_.size();
        return d;
    }
    IstekNo Gonder(std::string_view islem, const std::string&, const std::string&, YanitIsleyici isleyici) override {
        const IstekNo no = ++sonNo_;
        MotorYaniti y;
        y.no = no;
        y.islem = std::string(islem);
        y.durum = YanitDurumu::MotorHatasi;
        y.hataTuru = "motor_yok";
        y.hata = "Hesap motoru başlatılamadı: süreç tabanlı motor henüz uygulanmadı.";
        y.yanit = motor_protokolu::HataYaniti(y.hata, y.hataTuru);
        bekleyen_.emplace_back(std::move(y), std::move(isleyici));
        return no;
    }
    bool Iptal(IstekNo) override { return false; }
    size_t Pompala() override {
        size_t n = 0;
        while (!bekleyen_.empty()) {
            auto [y, f] = std::move(bekleyen_.front());
            bekleyen_.pop_front();
            if (f) f(y);
            ++n;
        }
        return n;
    }
    MotorYaniti CalistirBekle(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                              double) override {
        MotorYaniti sonuc;
        Gonder(islem, girdi, ayarlar, [&sonuc](const MotorYaniti& y) { sonuc = y; });
        Pompala();
        return sonuc;
    }
    void Durdur() override { Pompala(); }

private:
    MotorDurumOzeti durum_;
    IstekNo sonNo_ = 0;
    std::deque<std::pair<MotorYaniti, YanitIsleyici>> bekleyen_;
};

}  // namespace

std::unique_ptr<MotorHizmeti> MotorIstemcisiOlustur() { return std::make_unique<TaslakMotorIstemcisi>(); }

}  // namespace op4
