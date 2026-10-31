// op4 çekirdek — dosya işlemleri akışı: Yeni, Şablondan, Aç, Kaydet, Farklı kaydet, İçe / dışa aktar, IFC, otomatik
// kayıt, kurtarma, son dosyalar, kapanış onayı, ayar kalıcılığı (MIMARI §13, §14.1; F1 iş 1.6). Sahibi: D (dosya-cozum).
//
// Platformdan bağımsızdır ve Linux'ta sınanır: yalnız sözleşme arayüzlerini (Hizmetler: çekirdek, belge, iletişim,
// bildirim, ayarlar, sonuç, motor) ve dosya sistemi yardımcılarını kullanır. Windows'a özgü olanlar (dosya pencereleri,
// TaskDialog, atlama listesi, pencere başlığı, tek örnek borusu) DosyaPlatformu kancaları ve IletisimKutulari
// üzerinden gelir (kaynak/dosya/). Bütün çağrılar UI iş parçacığındadır.
//
// Açma sırası (TASARIM §21.4): ProjeOku → çekirdek Yukle (+ Denetle) → ModelYuklendi → belge Sifirla → IcerikDagit
// (katkılar kendi girdilerini okur: C görünüm, D sonuç) → belge Acildi (temiz durum, `acildi` olayı).
// Kaydetme: korunan girdiler (açılan dosyadaki her şey; bilinmeyenler dahil) + IcerikTopla (her katkı kendi girdisini
// yazar ya da siler) → manifest → ZIP → bellekte doğrulama → atomik yazma.
#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "cekirdek/olay.h"
#include "cekirdek/proje_dosyasi.h"
#include "platform/dosya_sistemi_atomik.h"

namespace op4 {

struct Hizmetler;
struct ModelOzeti;
struct YuklemeSonucu;

// op4/veri/sablonlar/dizin.json kaydı (araclar/sablon_dok.py üretir; motor hazır olmadan açılır).
struct SablonBilgisi {
    std::string ad, baslik, aciklama, sistem, dosya;
    int kat = 0;
    std::string aks;  // aks düzeni, ör. "4×3"
};
std::vector<SablonBilgisi> SablonDizini(const std::string& veriDizini, std::string& hata);

// "12 düğüm, 18 çubuk, 6 panel, 3 kat" (manifest model_ozeti, kurtarma kartı).
std::string ModelOzetMetni(const ModelOzeti& o);

struct DosyaPlatformu {
    std::function<void(const std::string& yol)> sonBelgeEkle;        // Win32: SHAddToRecentDocs (atlama listesi)
    std::function<void(const std::string& baslik)> pencereBasligi;   // Win32: SetWindowTextW("op4 — ad •")
    std::function<void(const std::string& yol)> belgeYoluDegisti;    // Win32: tek örnek borusunun belge adı
    std::function<void()> kurtarmaGoster;                            // Win32: Stüdyo "Kurtarma" kartını aç
    std::function<void()> sablonSeciciGoster;                        // Win32: "Şablondan yeni" kartını aç
};

struct DosyaIslemleriAyari {
    std::string kurtarmaDizini;     // KullaniciDizinleri::kurtarma (boş = otomatik kayıt / kurtarma kapalı)
    std::string acilisDosyasi;      // komut satırındaki dosya (ilk karede açılır)
    double otomatikKayitMs = 0;     // > 0: ayarlar.dosya.otomatikKayitDk yerine (sınama: 2000)
    std::string sabitZaman;         // doluysa "şimdi" bu (ISO 8601 UTC; sınama ve --senaryo belirlenimciliği)
    std::string ifcZamani;          // doluysa IFC başlık zamanı (sınama: "2026-01-01T00:00:00")
};

class DosyaIslemleri {
public:
    DosyaIslemleri(Hizmetler& h, DosyaIslemleriAyari ayar, DosyaPlatformu platform = {});
    // Temiz kapanış: bu oturumun kurtarma kaydı silinir (belge temizse ya da kapanış onaylandıysa) ve ayarlar yazılır.
    ~DosyaIslemleri();
    DosyaIslemleri(const DosyaIslemleri&) = delete;
    DosyaIslemleri& operator=(const DosyaIslemleri&) = delete;

    // Kurulum (DosyaModuluKur): dosya.* komutları, model ve önizleme katkıları, kapatmaOnayi, kare işi.
    void Kur();

    // ---- işlemler (dönüş: işlem tamamlandı mı; iptal ve hata false) ------------------------------------------------
    bool Yeni();
    bool SablondanYeni(const std::string& ad);
    bool Ac(const std::string& yol);          // .op4 / Faz 0 JSON .op4 / .matris / .json (BicimSapta içeriğe bakar)
    bool AcSor();                             // dosya penceresi
    bool IceAktarSor();                       // .matris / .json süzgeçli pencere
    bool Kaydet();
    bool FarkliKaydet(std::string yol = {});  // boşsa pencere
    bool BinaDisaAktar(std::string yol = {}); // .json (bina) ya da .matris (web sürümüyle paylaşım)
    bool IfcDisaAktar(std::string yol = {});
    bool KapatmaOnayi();                      // Hizmetler::kapatmaOnayi: Kaydet / Kaydetme / Vazgeç
    bool Cikis();                             // dosya.cikis: onay + ArayuzKancalari::pencereyiKapat
    // Kirliyse sorar; true = devam (kaydedildi ya da kaydetmeden), false = vazgeçildi.
    bool KaydedilmemisSor(std::string_view eylem);

    // ---- otomatik kayıt ve kurtarma ----------------------------------------------------------------------------------
    void KareIsi(double simdiMs);             // her karede (Hizmetler::KareIsiEkle)
    bool OtomatikKaydet();                    // zamanlayıcıyı beklemeden kurtarma kaydı yazar
    const std::vector<KurtarmaKaydi>& Kurtarmalar() const { return kurtarmalar_; }
    void KurtarmalariYenile();                // klasörü yeniden tarar (kendi kaydı ve yaşayan oturumlarınkiler hariç)
    bool Kurtar(size_t i);
    bool KurtarmaSil(size_t i);
    void KurtarmaSonra();                     // soru kapanır; kayıtlar bir sonraki açılışa (ya da dosya.kurtar'a) kalır
    bool KurtarmaSorusuAcik() const { return kurtarmaSorusu_; }
    const std::string& KurtarmaDosyasi() const { return kurtarmaZip_; }
    uint64_t OtomatikKayitSayisi() const { return otomatikKayitSayisi_; }
    Olay<> kurtarmaDegisti;

    // ---- ayarlar ------------------------------------------------------------------------------------------------------
    bool AyarlariKaydet(bool zorla = false);  // ayarDizini/ayarlar.json (değişmediyse yazmaz)
    std::vector<SablonBilgisi> Sablonlar() const;

private:
    bool YolaKaydet(const std::string& yol);
    bool OkunaniYukle(OkumaSonucu& okuma, const std::string& yol, bool kurtarma, const std::string& asilYol);
    bool HataBildir(const std::string& baslik, const std::string& hata);
    void Bilgi(const std::string& satir, bool tost);
    ProjeManifest ManifestKur() const;
    std::string Simdi() const;
    std::string OneriYolu(const std::string& uzanti) const;
    void SonDosya(const std::string& yol);
    void BasligiYay();
    void KurtarmaKaydiniSil();
    void YeniBelge(const YuklemeSonucu& y, int adsizNo);

    Hizmetler& h_;
    DosyaIslemleriAyari ayar_;
    DosyaPlatformu platform_;
    std::vector<KurtarmaKaydi> kurtarmalar_;
    ProjeIcerigi korunanlar_;          // açılan dosyanın girdileri (kaydederken katkılar üstüne yazar)
    std::string eskiKaynak_;           // içe aktarılan eski biçimli dosyanın yolu (Farklı kaydet önerisi için)
    std::string kurtarmaKok_, kurtarmaZip_;
    OturumKilidi oturumKilidi_;
    ProjeOkumaKilidi okumaKilidi_;
    int adsizSayaci_ = 1;
    bool ilkKare_ = false, kurtarmaSorusu_ = false, kapanisOnaylandi_ = false;
    double simdiMs_ = 0, kirliBaslangicMs_ = -1, sonAyarDenetimiMs_ = -1e300;
    uint64_t sonOtomatikSayac_ = 0, otomatikKayitSayisi_ = 0;
    bool otomatikHataBildirildi_ = false;
    std::string sonAyarMetni_;
    uint64_t aboneler_[4] = {0, 0, 0, 0};
};

}  // namespace op4
