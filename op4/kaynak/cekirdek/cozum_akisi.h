// op4 çekirdek — çözüm akışı (F5): eşzamansız bina_coz, geçen süre, iptal, sonuç özeti, D/C boyaması, eski işareti,
// .op4 sonuc/ katkısı ve açılışta kayıtlı sonucun modelle eşleştirilmesi (MIMARI §4 çözüm akışı, §13.1.4; F1 iş 1.5).
// Sahibi: D (dosya-cozum). Platformdan bağımsızdır; Linux'ta sahte MotorHizmeti ile durum makinesi olarak sınanır.
//
// Durum makinesi:
//   Bos ──Coz()──▶ Cozuluyor ──yanıt (Tamam | Hata | MotorHatasi)──▶ Bos
//                      │ Iptal()                               ▲
//                      ▼                                       │
//                 IptalEdiliyor ──yanıt (Iptal, hata_turu "iptal"; ya da yarışta Tamam)──┘
// Yanıt işleyicisi istek numarasıyla eşlenir; unutulan (yeni model yüklendi) ya da eski isteğin yanıtı atılır.
// Çözüm sürerken model değişirse gelen sonuç hemen "eski" işaretlenir. Sonuç gelince D/C boyaması GorunumDurumu::sonuc'a
// yazılır ve renk kipi Sonuc'a geçer; SonucDurumu "eski" olunca boyama soluk (eski = true) yeniden kurulur.
//
// Kayıtlı sonuç (sonuc/ozet.json): çözülen model metninin karması (model_karmasi) ile açılan modelin Metin() karması
// aynıysa sonuç hemen güncel görünür (D9); değilse "eski" görünür ve motor varsa bina_kimlik ile cozum_kimligi
// karşılaştırılır, eşleşirse güncel olur.
#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "cekirdek/motor_hizmeti.h"
#include "cekirdek/olay.h"
#include "cekirdek/proje_belgesi.h"

namespace op4 {

struct Hizmetler;

enum class CozumEvresi : uint8_t { Bos = 0, Cozuluyor = 1, IptalEdiliyor = 2 };

struct CozumAkisiAyari {
    std::string sabitZaman;          // doluysa sonuç tarihi bu (sınama)
    double ilerlemeAraligiMs = 1000; // geçen süre bildirimi sıklığı
};

// Sonuç özeti panelinin (ve komut satırı SONUÇÖZETİ çıktısının) satırları; renk 0 = varsayılan metin rengi.
struct OzetSatiri {
    std::string etiket, deger;
    uint32_t renk = 0;  // 0xRRGGBBAA
};

class CozumAkisi {
public:
    explicit CozumAkisi(Hizmetler& h, CozumAkisiAyari ayar = {});
    ~CozumAkisi();
    CozumAkisi(const CozumAkisi&) = delete;
    CozumAkisi& operator=(const CozumAkisi&) = delete;

    // Komutlar (analiz.coz, analiz.iptal, analiz.sonuc_ozeti, analiz.dc_renkleri), sonuc/ katkısı, abonelikler, kare işi.
    void Kur();

    bool Coz();
    bool Iptal();
    void KareIsi(double simdiMs);

    CozumEvresi Evre() const { return evre_; }
    IstekNo SurenIstek() const { return istekNo_; }
    double GecenMs() const { return evre_ == CozumEvresi::Bos ? 0.0 : simdiMs_ - baslangicMs_; }
    const std::string& SonHata() const { return sonHata_; }
    bool KimlikDenetimiSuruyor() const { return kimlikIstek_ != 0; }
    const std::string& CozulenModelKarmasi() const { return cozulenKarma_; }

    // Durum çubuğu metni: "Çözülüyor… 3,4 s", "İptal ediliyor…", "Sonuçlar eski", "D/C en büyük 0,998", "".
    std::string DurumMetni() const;
    std::vector<OzetSatiri> OzetSatirlari() const;

    Olay<> degisti;  // evre ya da sonuç değişti (panel / durum öğesi yeniden çizer)

private:
    void YanitGeldi(const MotorYaniti& y);
    void Unut();
    void BoyamayiGuncelle();
    void SonucuYaz(ProjeIcerigi& icerik) const;
    void SonucuOku(const ProjeIcerigi& icerik, std::vector<std::string>& uyarilar);
    void KimlikDenetle(const std::string& kimlik);
    std::string Simdi() const;
    void Yaz(const std::string& satir) const;

    Hizmetler& h_;
    CozumAkisiAyari ayar_;
    CozumEvresi evre_ = CozumEvresi::Bos;
    IstekNo istekNo_ = 0, kimlikIstek_ = 0;
    uint64_t istekSahneSurumu_ = 0, boyamaSurumu_ = 0;
    std::string istekKarma_, cozulenKarma_, sonHata_;
    bool modelDegistiCozumde_ = false, yeniSonuc_ = false;
    double simdiMs_ = 0, baslangicMs_ = 0, sonIlerlemeMs_ = 0;
    // Motor işleyicileri ve iptal geri çağrıları bu nesneden uzun yaşayabilir (motor D'den sonra durur): canlılık bekçisi.
    std::shared_ptr<int> canli_ = std::make_shared<int>(0);
    uint64_t aboneSonuc_ = 0, aboneYuklendi_ = 0, aboneDegisti_ = 0;
};

// "850 ms", "3,4 s", "2 dk 05 s".
std::string SureMetni(double ms);
// Binlik ayraçlı ondalık virgül: 2714.76 → "2 714,76" (Stüdyo sayı yazımı).
std::string SayiMetni(double v, int basamak);

}  // namespace op4
