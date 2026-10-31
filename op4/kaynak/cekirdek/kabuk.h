// op4 çekirdek sözleşmesi — uygulama kabuğu ve paket modülleri (sözleşme S23; "F1 paket sözleşmeleri").
//
// Kabuk (UygulamaKabugu) sözleşmenin somut ortak nesnelerinin sahibidir (komut defteri, arayüz kancaları, seçim,
// görünüm durumu, proje belgesi, sonuç durumu, ayarlar) ve Hizmetler'i kurar. Paket modülleri kendi hizmet
// uygulamalarını oluşturup Hizmetler'e bağlar, komutlarına işleyici bağlar, panel / durum öğesi / belge katkısı ekler.
// Kur modülleri (KabukAyari::moduller, op4.exe'de StandartModuller()) BU SIRAYLA çağırır: A (motor) → B (çekirdek) → C (arayüz) → D (dosya) → D (çözüm); sonra
// çekirdek boş model "Adsız 1" ile başlatılır (MIMARI §13.4). Bir modül kurulurken çıkış isterse (ModulOrtami::cikisIste)
// kalan modüller kurulmaz, boş model açılmaz; uygulama CikisIstendi()'ye bakıp pencere açmadan çıkar.
//
// Her modülün Kur işlevi kendi paketinin dosyasındadır; bu başlık yalnız bildirir:
//   MotorModuluKur    A  kaynak/motor_modulu.cpp            (Windows; Linux sınamasında taslak motor istemcisi)
//   CekirdekModuluKur B  kaynak/cekirdek_js/cekirdek_modulu.cpp
//   ArayuzModuluKur   C  kaynak/arayuz/arayuz_modulu.cpp     (Windows)
//   DosyaModuluKur    D  kaynak/dosya/dosya_modulu.cpp       (Windows)
//   CozumModuluKur    D  kaynak/cozum/cozum_modulu.cpp
// Kabuk platformdan bağımsızdır; Windows'a özgü olan yalnız modüllerin içidir.
#pragma once

#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/hizmetler.h"
#include "cekirdek/komut.h"
#include "cekirdek/proje_belgesi.h"
#include "cekirdek/secim.h"
#include "cekirdek/sonuc.h"

namespace op4 {

// Modüllerin kuruluş ortamı.
struct ModulOrtami {
    std::function<void*()> anaPencere;          // Windows: HWND (pencere kurulmadan önce null döner); sınamada boş
    bool testKipi = false;
    bool motorsuz = false;                      // --motorsuz: A motoru başlatmaz
    std::string acilisDosyasi;                  // komut satırındaki proje yolu (D ilk karede açar)
    std::string senaryo;                        // --senaryo yolu (C yürütür)
    std::function<void(std::string_view)> gunluk;
    bool yeniOrnek = false;                     // --yeni-ornek (S24): D tek örnek borusunu atlar. Uygulama, bir kez
                                                // ayrıştırılmış Secenekler'den doldurur; modüller komut satırını yeniden
                                                // ayrıştırmaz.
    // Çıkış isteği (kod = süreç çıkış kodu). UygulamaKabugu::Kur bağlar (ev sahibi bir işlev verdiyse onu da çağırır);
    // modüller çağırır. Kurulum sırasında istenirse kabuk sonraki modülleri kurmaz ve boş modeli açmaz; uygulama Kur'dan
    // hemen sonra UygulamaKabugu::CikisIstendi()'ye bakar ve pencere açmadan CikisKodu() ile çıkar (D: belge başka bir
    // op4 penceresinde açık — tek örnek devri). Kurulumdan sonra istenirse (ev sahibi işlev vermediyse)
    // ArayuzKancalari::pencereyiKapat çağrılır (kapanış onayı sorulmaz; sorulacaksa dosya.cikis komutu kullanılır).
    // İlk isteğin kodu geçerlidir.
    std::function<void(int kod)> cikisIste;

    // Modül nesnelerinin sahipliği: kabuk kapanırken TERS sırada bırakılır.
    template <class T>
    T* Tut(std::shared_ptr<T> p) {
        T* ham = p.get();
        nesneler_.push_back(std::move(p));
        return ham;
    }
    void Birak() {
        while (!nesneler_.empty()) nesneler_.pop_back();
    }

private:
    std::vector<std::shared_ptr<void>> nesneler_;
};

void MotorModuluKur(Hizmetler& h, ModulOrtami& o);
void CekirdekModuluKur(Hizmetler& h, ModulOrtami& o);
void ArayuzModuluKur(Hizmetler& h, ModulOrtami& o);
void DosyaModuluKur(Hizmetler& h, ModulOrtami& o);
void CozumModuluKur(Hizmetler& h, ModulOrtami& o);

struct ModulKaydi {
    const char* ad;     // "motor", "cekirdek", "arayuz", "dosya", "cozum"
    const char* paket;  // "A" | "B" | "C" | "D"
    void (*kur)(Hizmetler&, ModulOrtami&);
};
// op4.exe'nin modül listesi, yukarıdaki sırayla (kaynak/moduller_listesi.cpp; yalnız Windows derlemesinde). Linux
// sınamaları kendi listelerini verir (ör. yalnız CekirdekModuluKur + sahte modüller).
std::vector<ModulKaydi> StandartModuller();

struct KabukAyari {
    UygulamaBilgisi bilgi;              // surum, dizinler, testKipi
    ModulOrtami ortam;
    std::vector<ModulKaydi> moduller;   // sırayla çağrılır
};

class UygulamaKabugu {
public:
    UygulamaKabugu();
    ~UygulamaKabugu();
    UygulamaKabugu(const UygulamaKabugu&) = delete;
    UygulamaKabugu& operator=(const UygulamaKabugu&) = delete;

    // Ayarları (ayarDizini/ayarlar.json) ve komut kataloğunu (veriDizini/komutlar.json) yükler, Hizmetler'i kurar,
    // modülleri sırayla çağırır, boş modeli açar. Katalog okunamazsa false + hata (program yine açılır; komutlar yok).
    bool Kur(KabukAyari ayar, std::string& hata);
    // Modül nesnelerini ters sırada bırakır (motor durdurma A'nın nesnesinin yıkıcısındadır).
    void Kapat();

    Hizmetler& H() { return h_; }
    ModulOrtami& Ortam() { return ortam_; }
    // Bir modül ModulOrtami::cikisIste ile çıkış istedi mi; istendiyse kodu. Uygulama Kur'dan hemen sonra bakar.
    bool CikisIstendi() const { return cikisIstendi_; }
    int CikisKodu() const { return cikisKodu_; }

    // Ortak nesneler (Hizmetler bunları gösterir).
    KomutYoneticisi komutlar;
    ArayuzKancalari arayuz;
    Secim secim;
    GorunumDurumu gorunum;
    ProjeBelgesi belge;
    SonucDurumu sonuc;
    Ayarlar ayarlar;

private:
    Hizmetler h_;
    ModulOrtami ortam_;
    std::unique_ptr<GunlukBildirimleri> yedekBildirim_;
    std::unique_ptr<BetikliIletisimKutulari> yedekIletisim_;
    bool kuruldu_ = false;
    bool cikisIstendi_ = false;
    int cikisKodu_ = 0;
};

}  // namespace op4
