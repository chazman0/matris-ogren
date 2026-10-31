// op4 — hesap motoru modülü (A; sözleşme S13, S21, S23; F1 iş 1.2, kabul A10). Windows.
//
// MotorModuluKur, süreç tabanlı istemciyi (cekirdek/motor_istemci.h: op4motor.exe süreçleri, tel protokolü, iptal,
// yeniden başlatma, ana / yardımcı yönlendirmesi) Hizmetler::motor'a bağlar; "Hesap motoru" durum öğesini, Ayarlar ›
// Hesap motoru sayfasını ve motor.yeniden_baslat komutunu ekler. Her karede (ve boşta) Pompala çağrılır.
//
// Tanı kipi (MIMARI §8.1; Faz 1 boyunca): OP4_MOTOR=gomulu ortam değişkeniyle Faz 0'ın SÜREÇ İÇİ gömülü motoru
// (motor.h, Motor) aynı arayüzün arkasında çalışır (GomuluMotorHizmeti). Sınırları: çalışan istek iptal edilemez, tek motor.
#include <windows.h>

#include <algorithm>
#include <condition_variable>
#include <cstdlib>
#include <deque>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <utility>

#include <nlohmann/json.hpp>

#include "cekirdek/kabuk.h"
#include "cekirdek/motor_hizmeti.h"
#include "cekirdek/motor_istemci.h"
#include "cekirdek/motor_protokol.h"
#include "gunluk.h"
#include "imgui.h"
#include "motor.h"

namespace op4 {
namespace {

MotorYaniti YanitKur(uint64_t no, const std::string& islem, std::string metin, double sureMs, double toplamMs) {
    MotorYaniti y;
    y.no = no;
    y.islem = islem;
    y.sureMs = sureMs;
    y.toplamMs = toplamMs;
    // web_kopru hata yanıtları {"hata": "…", "hata_turu": …} ile başlar; başarılı yanıtlarda "hata": null sonradadır.
    if (metin.rfind("{\"hata\": \"", 0) == 0 || metin.rfind("{\"hata\":\"", 0) == 0) {
        const nlohmann::json j = nlohmann::json::parse(metin, nullptr, false);
        y.hata = j.is_object() && j.contains("hata") && j["hata"].is_string() ? j["hata"].get<std::string>() : "hesap motoru hatası";
        y.hataTuru = j.is_object() && j.contains("hata_turu") && j["hata_turu"].is_string() ? j["hata_turu"].get<std::string>()
                                                                                              : "ic";
        y.durum = y.hataTuru == "iptal" ? YanitDurumu::Iptal : YanitDurumu::Hata;
    }
    y.yanit = std::move(metin);
    return y;
}

class GomuluMotorHizmeti final : public MotorHizmeti {
public:
    // Yıkıcıda bekleyen işleyiciler ÇAĞRILMAZ: kabuk kapanırken onları kuran modüller (C, D) çoktan bırakılmıştır.
    ~GomuluMotorHizmeti() override { Kapat(false); }

    void Baslat(const MotorAyari& ayar) override {
        if (baslatildi_) return;
        baslatildi_ = true;
        motor_.Baslat(Genis(ayar.uygulamaDizini), [this](const std::string& m, float o) {
            std::lock_guard<std::mutex> k(kilit_);
            durumlar_.emplace_back(m, o);
        });
        isci_ = std::thread([this] { Isci(); });
    }

    MotorDurumOzeti Durum(MotorRolu) const override {
        MotorDurumOzeti d;
        d.baslatildi = baslatildi_;
        if (!baslatildi_) return d;
        const MotorDurumu m = motor_.Durum();
        d.hazir = m.hazir;
        d.basarili = m.basarili;
        d.hata = m.hata;
        d.pythonSurumu = m.pythonSurumu.substr(0, m.pythonSurumu.find(' '));
        d.surumJson = m.surumJson;
        d.hazirMs = m.msToplam;
        if (m.hazir && m.basarili)
            d.aciklama = "Python " + d.pythonSurumu + ", " + std::to_string(m.sablonSayisi) + " yapı şablonu (" +
                         std::to_string(static_cast<int>(m.msToplam)) + " ms)";
        else if (m.hazir)
            d.aciklama = "Hesap motoru başlatılamadı";
        else
            d.aciklama = "Hesap motoru başlatılıyor";
        std::lock_guard<std::mutex> k(kilit_);
        d.bekleyen = kuyruk_.size() + (calisan_ ? 1 : 0);
        d.calisiyor = calisan_ != 0;
        return d;
    }

    IstekNo Gonder(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                   YanitIsleyici isleyici) override {
        const IstekNo no = ++sonNo_;
        Is is;
        is.no = no;
        is.islem = std::string(islem);
        is.istek = "{\"islem\":\"" + motor_protokolu::JsonKacis(islem) + "\",\"girdi\":" + (girdi.empty() ? "{}" : girdi) +
                   ",\"ayarlar\":" + (ayarlar.empty() ? "{}" : ayarlar) + "}";
        is.baslangic = GecenMs();
        isleyiciler_.emplace_back(no, std::move(isleyici));
        std::lock_guard<std::mutex> k(kilit_);
        if (!baslatildi_ || dur_) {
            MotorYaniti y = YanitKur(no, is.islem,
                                     motor_protokolu::HataYaniti("Hesap motoru başlatılmadı (--motorsuz ya da kapanıyor).", "motor_yok"),
                                     0, 0);
            y.durum = YanitDurumu::MotorHatasi;
            tamam_.push_back(std::move(y));
        } else {
            kuyruk_.push_back(std::move(is));
            kosul_.notify_one();
        }
        return no;
    }

    bool Iptal(IstekNo no) override {
        std::lock_guard<std::mutex> k(kilit_);
        for (auto i = kuyruk_.begin(); i != kuyruk_.end(); ++i)
            if (i->no == no) {
                tamam_.push_back(YanitKur(no, i->islem, motor_protokolu::HataYaniti("İşlem iptal edildi.", "iptal"), 0,
                                          GecenMs() - i->baslangic));
                kuyruk_.erase(i);
                return true;
            }
        return false;  // çalışan istek gömülü motorda kesilemez
    }

    size_t Pompala() override {
        std::deque<std::pair<std::string, float>> durumlar;
        std::deque<MotorYaniti> tamam;
        {
            std::lock_guard<std::mutex> k(kilit_);
            durumlar.swap(durumlar_);
            tamam.swap(tamam_);
        }
        for (const auto& [m, o] : durumlar)
            if (durumBildirimi) durumBildirimi(MotorRolu::Ana, m, o);
        for (MotorYaniti& y : tamam) Dagit(y);
        return tamam.size();
    }

    MotorYaniti CalistirBekle(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                              double zamanAsimiMs) override {
        bool geldi = false;
        MotorYaniti sonuc;
        const IstekNo no = Gonder(islem, girdi, ayarlar, [&](const MotorYaniti& y) {
            sonuc = y;
            geldi = true;
        });
        const double bas = GecenMs();
        while (!geldi) {
            Pompala();
            if (geldi) break;
            if (GecenMs() - bas > zamanAsimiMs && Iptal(no)) continue;
            Sleep(1);
        }
        return sonuc;
    }

    void Durdur() override { Kapat(true); }

private:
    void Kapat(bool dagit) {
        {
            std::lock_guard<std::mutex> k(kilit_);
            if (dur_) return;
            dur_ = true;
            for (Is& is : kuyruk_) {
                MotorYaniti y = YanitKur(is.no, is.islem, motor_protokolu::HataYaniti("Hesap motoru kapatıldı.", "motor_yok"), 0, 0);
                y.durum = YanitDurumu::MotorHatasi;
                tamam_.push_back(std::move(y));
            }
            kuyruk_.clear();
        }
        kosul_.notify_all();
        if (isci_.joinable()) isci_.join();
        motor_.Durdur();
        if (dagit) Pompala();  // Y1: bekleyen her isteğin işleyicisi bir kez çağrılır
    }

    struct Is {
        IstekNo no = 0;
        std::string islem, istek;
        double baslangic = 0;
    };

    void Isci() {
        motor_.Bekle(INFINITE);
        for (;;) {
            Is is;
            {
                std::unique_lock<std::mutex> k(kilit_);
                kosul_.wait(k, [this] { return dur_ || !kuyruk_.empty(); });
                if (dur_) return;
                is = std::move(kuyruk_.front());
                kuyruk_.pop_front();
                calisan_ = is.no;
            }
            const double t0 = GecenMs();
            std::string r = motor_.Calistir(is.istek);
            const double t1 = GecenMs();
            std::lock_guard<std::mutex> k(kilit_);
            calisan_ = 0;
            tamam_.push_back(YanitKur(is.no, is.islem, std::move(r), t1 - t0, t1 - is.baslangic));
        }
    }

    void Dagit(const MotorYaniti& y) {
        for (auto i = isleyiciler_.begin(); i != isleyiciler_.end(); ++i)
            if (i->first == y.no) {
                YanitIsleyici f = std::move(i->second);
                isleyiciler_.erase(i);
                if (f) f(y);
                return;
            }
    }

    Motor motor_;
    bool baslatildi_ = false;
    IstekNo sonNo_ = 0;
    std::vector<std::pair<IstekNo, YanitIsleyici>> isleyiciler_;  // yalnız UI iş parçacığı
    mutable std::mutex kilit_;
    std::condition_variable kosul_;
    std::deque<Is> kuyruk_;
    std::deque<MotorYaniti> tamam_;
    std::deque<std::pair<std::string, float>> durumlar_;
    IstekNo calisan_ = 0;
    bool dur_ = false;
    std::thread isci_;
};

// "Hesap motoru" durum öğesi (durum çubuğu, sağda).
void DurumOgesiCiz(const MotorHizmeti* m, bool motorsuz) {
    const MotorDurumOzeti a = m->Durum(MotorRolu::Ana);
    const MotorDurumOzeti y = m->Durum(MotorRolu::Yardimci);
    const ImVec4 krem(0.93f, 0.90f, 0.85f, 1.0f), altin(0.69f, 0.54f, 0.31f, 1.0f), kirmizi(0.90f, 0.35f, 0.30f, 1.0f);
    const size_t bekleyen = a.bekleyen + y.bekleyen;
    if (motorsuz || !a.baslatildi) {
        ImGui::TextColored(krem, "Hesap motoru: kapalı");
    } else if (!a.hazir) {
        ImGui::TextColored(altin, "Hesap motoru: başlatılıyor…");
    } else if (!a.basarili) {
        ImGui::TextColored(kirmizi, "Hesap motoru: hata");
    } else if (a.calisiyor || y.calisiyor) {
        ImGui::TextColored(altin, "Hesap motoru: çalışıyor (%zu)", bekleyen);
    } else {
        ImGui::TextColored(krem, "Hesap motoru: hazır");
    }
    if (ImGui::IsItemHovered()) {
        std::string ipucu = a.aciklama;
        if (!a.hata.empty()) ipucu += "\n" + a.hata;
        if (y.baslatildi) ipucu += "\nYardımcı: " + y.aciklama + (y.hata.empty() ? "" : " — " + y.hata);
        if (a.yenidenBaslatma + y.yenidenBaslatma > 0)
            ipucu += "\nBu oturumda " + std::to_string(a.yenidenBaslatma + y.yenidenBaslatma) + " kez yeniden başlatıldı";
        ImGui::SetTooltip("%s", ipucu.c_str());
    }
}

void AyarSayfasiCiz(Ayarlar& a) {
    ImGui::TextWrapped("Hesap motoru ayrı süreçte çalışır (op4motor). Değişiklikler sonraki isteklerde geçerlidir; bellek tavanı "
                       "motor yeniden başlatılınca (Analiz › Hesap motorunu yeniden başlat).");
    ImGui::InputInt("Serbestlik derecesi sınırı", &a.motor.sdSiniri, 500, 2000);
    a.motor.sdSiniri = std::clamp(a.motor.sdSiniri, 100, 200000);
    ImGui::Checkbox("F5 çözümünde adım adım anlatım", &a.motor.anlat);
    ImGui::SliderInt("Bellek tavanı (% sistem belleği)", &a.motor.bellekYuzde, 10, 95);
}

}  // namespace

void MotorModuluKur(Hizmetler& h, ModulOrtami& o) {
    MotorHizmeti* m = nullptr;
    MotorIstemcisi* istemci = nullptr;
    const char* secim = std::getenv("OP4_MOTOR");
    if (secim && std::string(secim) == "gomulu") {
        m = o.Tut(std::make_shared<GomuluMotorHizmeti>());
        if (o.gunluk) o.gunluk("Hesap motoru: süreç içi gömülü motor (OP4_MOTOR=gomulu; Faz 0 tanı kipi)");
    } else {
        auto p = std::make_shared<MotorIstemcisi>();
        p->gunluk = o.gunluk;
        if (h.ayarlar) {
            p->sdSiniri = h.ayarlar->motor.sdSiniri;
            MEMORYSTATUSEX bellek{sizeof(bellek)};
            if (GlobalMemoryStatusEx(&bellek))
                p->bellekSiniriBayt = bellek.ullTotalPhys / 100 * static_cast<uint64_t>(std::clamp(h.ayarlar->motor.bellekYuzde, 10, 95));
        }
        istemci = p.get();
        m = o.Tut(std::shared_ptr<MotorHizmeti>(p));
    }
    h.motor = m;
    Hizmetler* hp = &h;
    h.KareIsiEkle("motor", [m, istemci, hp](double) {
        if (istemci && hp->ayarlar) istemci->sdSiniri = hp->ayarlar->motor.sdSiniri;  // ayar değişikliği sonraki isteklerde
        m->Pompala();
    });

    const bool motorsuz = o.motorsuz;
    KomutIsleyici yeniden;
    yeniden.calistir = [istemci](KomutBaglami& b) {
        if (!istemci) return;
        istemci->YenidenBaslat();
        if (b.h.bildirim) b.h.bildirim->KomutYaz("Hesap motoru yeniden başlatılıyor (çözüm önbelleği boşaldı)…");
    };
    yeniden.kullanilamazNedeni = [istemci, motorsuz](const Hizmetler&) {
        if (motorsuz) return std::string("Hesap motoru kapalı (--motorsuz)");
        if (!istemci) return std::string("Süreç içi gömülü motor yeniden başlatılamaz (OP4_MOTOR=gomulu)");
        return std::string();
    };
    if (h.komutlar) h.komutlar->Bagla("motor.yeniden_baslat", yeniden);
    if (h.arayuz) {
        h.arayuz->DurumOgesiEkle({"motor", 50, true, "A", [m, motorsuz] { DurumOgesiCiz(m, motorsuz); }});
        h.arayuz->AyarSayfasiEkle({"motor", "Hesap motoru", 40, "A", &AyarSayfasiCiz});
    }
}

}  // namespace op4
