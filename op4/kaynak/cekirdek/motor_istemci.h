// op4 çekirdek — süreç tabanlı hesap motoru istemcisi (MotorHizmeti'nin F1 uygulaması; MIMARI §8; kabul A8). Sahibi: A.
//
// Her rol (ana, yardımcı; MotorRoluSec, MIMARI §8.3) için bir motor süreci: op4motor.exe (Windows, kurulu program) ya da
// sınamada `<pythonYolu> -X utf8 -B -m op4_sunucu` (PYTHONPATH = MotorAyari::sunucuDizini; platformun yol ayırıcısıyla —
// POSIX ':', Windows ';'). Süreç başına bir okuyucu ve bir yazıcı iş parçacığı vardır; UI iş parçacığı boruya hiç
// yazmaz / boru beklemez. Sözleşmenin (motor_hizmeti.h, motor_protokol.h Y1–Y4) üstüne bu uygulamanın kuralları:
//   * Ana motor Baslat'ta, yardımcı ilk isteğinde (MotorAyari::yardimciTembel) başlar. İstekler süreç hazır olmadan da
//     gönderilir (sunucu kuyruğa alır).
//   * İptal: kuyruktaki istek (sunucuda önünde başka istek varken ya da motor henüz hazır değilken) HEMEN Iptal ile
//     yanıtlanır; çalışan istek sunucuda KeyboardInterrupt ile biter. Iptal true döndüyse işleyici HER ZAMAN Iptal
//     görür (iptal ile yanıt yarışırsa gelen sonuç atılır). iptalBeklemeMs (5 s) içinde yanıt gelmezse süreç sonlandırılır,
//     yeniden başlatılır; o süreçte bekleyen diğer istekler MotorHatasi "motor_yeniden" alır.
//   * Süreç beklenmedik biçimde biterse bekleyen istekler MotorHatasi "motor_coktu" alır ve süreç kendiliğinden yeniden
//     başlatılır (60 s içinde cokmeSiniri kez çökerse durur; motor.yeniden_baslat ile yeniden denenir). Hazır olmadan biten
//     ya da başlatılamayan motor "motor_yok" verir; hata metni sunucu günlüğünün son satırlarını içerir.
//   * Bozuk çerçeve / ileti: süreç sonlandırılır, bekleyenler "protokol" alır, yeniden başlatılır.
//   * Eski (yanıtı zaten verilmiş ya da önceki sürece ait) id'li yanıtlar atılır.
//   * Sunucu günlüğü: <gunlukDizini>/motor-ana.log, motor-yardimci.log (önceki oturumunki *.onceki.log).
#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <string_view>

#include "cekirdek/motor_hizmeti.h"

namespace op4 {

class MotorIstemcisi final : public MotorHizmeti {
public:
    MotorIstemcisi();
    ~MotorIstemcisi() override;  // süreçleri kapatır; bekleyen işleyiciler ÇAĞRILMAZ (kuranlar çoktan bırakılmış olabilir)
    MotorIstemcisi(const MotorIstemcisi&) = delete;
    MotorIstemcisi& operator=(const MotorIstemcisi&) = delete;

    void Baslat(const MotorAyari& ayar) override;
    MotorDurumOzeti Durum(MotorRolu rol = MotorRolu::Ana) const override;
    IstekNo Gonder(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                   YanitIsleyici isleyici) override;
    bool Iptal(IstekNo no) override;
    size_t Pompala() override;
    MotorYaniti CalistirBekle(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                              double zamanAsimiMs) override;
    void Durdur() override;

    // ---- A'ya özgü (MotorModuluKur, --test-motor, sınamalar) ----------------------------------------------------------
    // motor.yeniden_baslat: çalışan süreçleri sonlandırır (bekleyenlere "motor_yeniden", iptal edilmişlere Iptal; yanıtlar
    // bir sonraki Pompala'da), çökme sayacını sıfırlar, ana motoru yeniden başlatır (yardımcı ilk isteğinde).
    void YenidenBaslat();

    // Baslat'tan önce kurulur.
    std::function<void(std::string_view)> gunluk;  // tanı satırları (UI iş parçacığında)
    uint64_t bellekSiniriBayt = 0;                 // süreç başına bellek tavanı (Windows Job Object); 0 = sınırsız
    int sdSiniri = 0;                              // > 0: "bina_" isteklerinin ayarlarına (yoksa) "sd_siniri" eklenir
    int cokmeSiniri = 3;                           // 60 s içinde bu kadar çökmeden sonra kendiliğinden yeniden başlatmaz
    double baslatmaZamanAsimiMs = 120000;          // "hazir" bu sürede gelmezse süreç sonlandırılır (motor_yok)

    // Sınama / tanı.
    long long SurecKimligi(MotorRolu rol) const;   // çalışan sürecin pid'i, yoksa 0
    std::string GunlukYolu(MotorRolu rol) const;   // sunucu günlüğü (boş: günlük dizini verilmedi)

private:
    struct Ic;
    std::unique_ptr<Ic> ic_;
};

}  // namespace op4
