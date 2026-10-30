// op4 — uygulama kabuğu (sözleşme S23; tam uygulama). Platformdan bağımsızdır.
#include "cekirdek/kabuk.h"

#include "platform/dosya_sistemi.h"

namespace op4 {

UygulamaKabugu::UygulamaKabugu() = default;
UygulamaKabugu::~UygulamaKabugu() { Kapat(); }

bool UygulamaKabugu::Kur(KabukAyari ayar, std::string& hata) {
    ortam_ = std::move(ayar.ortam);
    auto gunluk = [this](std::string_view s) {
        if (ortam_.gunluk) ortam_.gunluk(s);
    };
    yedekBildirim_ = std::make_unique<GunlukBildirimleri>(gunluk);
    yedekIletisim_ = std::make_unique<BetikliIletisimKutulari>();

    h_ = Hizmetler{};
    h_.bilgi = ayar.bilgi;
    h_.komutlar = &komutlar;
    h_.arayuz = &arayuz;
    h_.bildirim = yedekBildirim_.get();   // C kendi uygulamasını bağlar
    h_.iletisim = yedekIletisim_.get();   // D kendi uygulamasını bağlar
    h_.belge = &belge;
    h_.secim = &secim;
    h_.gorunum = &gorunum;
    h_.sonuc = &sonuc;
    h_.ayarlar = &ayarlar;

    // Ayarlar (yoksa varsayılan; bozuksa uyarı).
    std::string metin, h2;
    if (!h_.bilgi.ayarDizini.empty() && DosyaOku(h_.bilgi.ayarDizini + "/ayarlar.json", metin, h2)) {
        if (!AyarlariOku(metin, ayarlar, h2)) gunluk("Uyarı: " + h2);
    }
    // Komut kataloğu.
    bool tamam = true;
    std::string katalog;
    if (DosyaOku(h_.bilgi.veriDizini + "/komutlar.json", katalog, h2)) {
        if (!komutlar.KatalogYukle(katalog, h2)) {
            hata = h2;
            tamam = false;
        }
    } else {
        hata = "Komut kataloğu bulunamadı: " + h_.bilgi.veriDizini + "/komutlar.json";
        tamam = false;
    }
    if (!tamam) gunluk("Uyarı: " + hata);

    for (const ModulKaydi& m : ayar.moduller)
        if (m.kur) {
            m.kur(h_, ortam_);
            gunluk(std::string("Modül kuruldu: ") + m.ad + " (" + m.paket + ")");
        }
    // Program her zaman boş model "Adsız 1" ile açılır (açılış dosyasını D ilk karede açar).
    if (h_.cekirdek) {
        ModelYuklendi(h_, h_.cekirdek->YeniBos("Adsız 1"));
        belge.Acildi("", 1, false);
    }
    kuruldu_ = true;
    return tamam;
}

void UygulamaKabugu::Kapat() {
    if (!kuruldu_) return;
    kuruldu_ = false;
    ortam_.Birak();
    h_.cekirdek = nullptr;
    h_.motor = nullptr;
    h_.bildirim = yedekBildirim_.get();
    h_.iletisim = yedekIletisim_.get();
}

}  // namespace op4
