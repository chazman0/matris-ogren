// op4 platform — atomik yazmanın platform işlemleri ve kilitler (MIMARI §13.2, §13.3, D23). Sahibi: D (dosya-cozum).
//
// Sözleşme işlevi AtomikYaz (platform/dosya_sistemi.h) bu dosyadaki ALGORİTMAYI platformun işlemleriyle çalıştırır:
//   1. Hedefle aynı klasörde benzersiz adlı geçici dosya yazılır, diske boşaltılır (FlushFileBuffers / fsync) ve
//      tanıtıcısı KAPATILIR (açık tanıtıcı varken ReplaceFileW başarısız olur, D23).
//   2. Hedef varsa yerine konur (Win32 ReplaceFileW, isteğe bağlı .bak), yoksa taşınır (MoveFileExW REPLACE_EXISTING |
//      WRITE_THROUGH; POSIX rename + klasör fsync).
//   3. Paylaşım ihlalinde (OneDrive, virüs tarayıcısı, başka program dosyayı tutuyor) 5 kez, 100 ms aralıkla yeniden
//      denenir. Sonunda da olmazsa geçici dosya silinir ve hedef DEĞİŞMEDEN kalır.
// İşlemler bir yapıya toplanmıştır: Linux sınamaları Windows davranışını (paylaşım ihlali, yarım kalan yer değiştirme)
// sahte işlemlerle, POSIX yolunu da gerçek işlemlerin üstüne kurulmuş "kilit benzetimiyle" sınar.
#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <string_view>

namespace op4 {

enum class YerineKoymaSonucu : uint8_t {
    Tamam = 0,
    PaylasimIhlali = 1,  // geçici durum: yeniden denenir (ERROR_SHARING_VIOLATION, ERROR_LOCK_VIOLATION, …)
    Hata = 2,            // kalıcı: denenmez (klasör yok, disk dolu, erişim reddedildi …)
};

struct AtomikYazmaIslemleri {
    // Geçici dosyayı oluşturur (yoksa), yazar, boşaltır ve KAPATIR. false → hata dolu (öğretici, Türkçe).
    std::function<bool(const std::string& gecici, std::string_view veri, std::string& hata)> geciciYaz;
    // Geçiciyi hedefin yerine koyar. bak = true ise eski hedef "<hedef>.bak" olur. Tamam değilse hedef değişmemiş olmalı.
    std::function<YerineKoymaSonucu(const std::string& gecici, const std::string& hedef, bool bak, std::string& hata)>
        yerineKoy;
    std::function<void(int ms)> bekle;
    std::function<void(const std::string& yol)> sil;
};

// Platformun gerçek işlemleri (Win32: dosya_sistemi_win.cpp, POSIX: dosya_sistemi_posix.cpp).
const AtomikYazmaIslemleri& PlatformAtomikIslemleri();

struct AtomikYazmaAyari {
    int deneme = 5;        // yerine koyma için toplam deneme (MIMARI §13.2: 5 kez)
    int aralikMs = 100;    // denemeler arası bekleme
};

// Atomik yazma algoritması (bkz. dosya başı). AtomikYaz(yol, veri, bak, hata) ≡ AtomikYazIle(PlatformAtomikIslemleri(), …).
// denemeSayisi doluysa yapılan yerine koyma denemesi sayısı yazılır (sınama).
bool AtomikYazIle(const AtomikYazmaIslemleri& is, const std::string& yol, std::string_view veri, bool bak,
                  std::string& hata, const AtomikYazmaAyari& ayar = {}, int* denemeSayisi = nullptr);

// Hedefle aynı klasörde benzersiz geçici ad: "<yol>.~op4-<süreç>-<sayaç>.tmp" (aynı birimde olduğu için yer değiştirme
// atomiktir; tarayıcılar ".tmp"yi atlar).
std::string GeciciDosyaAdi(const std::string& yol);

// ---- kilitler --------------------------------------------------------------------------------------------------------
// Oturum kilidi: süreç yaşadıkça tutulan dışlayıcı kilit (kurtarma kaydının "sahibi yaşıyor mu" sorusu; MIMARI §13.3).
// Win32: paylaşımsız açılmış, kapanınca silinen dosya (FILE_FLAG_DELETE_ON_CLOSE); POSIX: flock(LOCK_EX | LOCK_NB).
// Süreç çökse bile işletim sistemi kilidi bırakır.
class OturumKilidi {
public:
    OturumKilidi();
    ~OturumKilidi();
    OturumKilidi(const OturumKilidi&) = delete;
    OturumKilidi& operator=(const OturumKilidi&) = delete;
    bool Al(const std::string& yol);   // başka süreç tutuyorsa false
    void Birak();
    bool Tutuluyor() const;

private:
    struct Ic;
    std::unique_ptr<Ic> ic_;
};
// Kilit dosyasını başka bir süreç (ya da bu süreçteki başka bir OturumKilidi) tutuyor mu? Dosya yoksa false.
bool KilitTutuluyorMu(const std::string& yol);

// Açık projenin okuma kilidi (MIMARI §13.2 adım 2 ve 5): Win32'de dosya FILE_SHARE_READ ile açık tutulur (başka program
// okuyabilir, yazamaz / silemez); kaydetmeden önce Birak, yerine koyduktan sonra yeniden Ac. POSIX'te işlem yapmaz.
class ProjeOkumaKilidi {
public:
    ProjeOkumaKilidi();
    ~ProjeOkumaKilidi();
    ProjeOkumaKilidi(const ProjeOkumaKilidi&) = delete;
    ProjeOkumaKilidi& operator=(const ProjeOkumaKilidi&) = delete;
    bool Ac(const std::string& yol);
    void Birak();
    const std::string& Yol() const { return yol_; }

private:
    struct Ic;
    std::unique_ptr<Ic> ic_;
    std::string yol_;
};

// Süreç kimliği (geçici adlar, kurtarma kayıtları).
uint32_t SurecNo();

}  // namespace op4
