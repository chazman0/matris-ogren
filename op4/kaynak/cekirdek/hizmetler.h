// op4 çekirdek sözleşmesi — Hizmetler: paketlerin birbirine dokunduğu TEK nokta (MIMARI §4 "Proje durumu";
// "F1 paket sözleşmeleri" §S22).
//
// ana.cpp / uygulama.cpp her hizmetin somut nesnesini kurar, işaretçilerini burada toplar ve paket modüllerinin Kur
// işlevlerini sırayla çağırır (kaynak/moduller.h). Modüller birbirinin sınıfını değil yalnız buradaki arayüzleri kullanır;
// komut bağlar, panel / durum öğesi ekler, olaylara abone olur, belge katkısı ekler.
//
// Yaşam süresi: Hizmetler ve gösterdiği her nesne uygulama boyunca yaşar; Kur'dan sonra işaretçiler null DEĞİLDİR
// (Linux sınamaları sahte nesneler bağlar). Bütün erişim UI iş parçacığındadır.
#pragma once

#include <cstdint>
#include <functional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "cekirdek/model_cekirdegi.h"
#include "cekirdek/olay.h"

namespace op4 {

class KomutYoneticisi;
class ArayuzKancalari;
class Bildirimler;
class IletisimKutulari;
class MotorHizmeti;
class ProjeBelgesi;
class Secim;
struct GorunumDurumu;
class SonucDurumu;
struct Ayarlar;

struct UygulamaBilgisi {
    std::string surum;            // OP4_SURUM ("0.1.0")
    std::string uygulamaDizini;   // op4.exe klasörü (UTF-8)
    std::string veriDizini;       // komutlar.json, oznitelikler.json, sablonlar/ (kurulu: <uygulama>\veri; geliştirme: op4/veri)
    std::string ayarDizini;       // %APPDATA%\Opus Fortis\op4
    std::string yerelDizin;       // %LOCALAPPDATA%\Opus Fortis\op4
    bool testKipi = false;        // --test-* / --senaryo: pencere açan iletişim kutusu yok, saat deterministik
};

struct Hizmetler {
    // ---- hizmetler (sahip paket) ------------------------------------------------------------------------------------
    KomutYoneticisi* komutlar = nullptr;   // C (defter); herkes Bagla
    ArayuzKancalari* arayuz = nullptr;     // C (defter); herkes ekler
    Bildirimler* bildirim = nullptr;       // C uygular
    IletisimKutulari* iletisim = nullptr;  // D uygular
    ModelCekirdegi* cekirdek = nullptr;    // B uygular
    MotorHizmeti* motor = nullptr;         // A uygular
    ProjeBelgesi* belge = nullptr;         // D sürer
    Secim* secim = nullptr;                // C sürer
    GorunumDurumu* gorunum = nullptr;      // C sürer; D sonuç boyamasını yazar
    SonucDurumu* sonuc = nullptr;          // D sürer
    Ayarlar* ayarlar = nullptr;            // D kalıcılaştırır; gruplar sahiplerine göre
    UygulamaBilgisi bilgi;

    // ---- olaylar ------------------------------------------------------------------------------------------------------
    Olay<IslemRaporu> modelDegisti;   // ModelIslemiSonrasi yayınlar (düzenleme, geri al, yinele)
    Olay<ModelOzeti> modelYuklendi;   // ModelYuklendi yayınlar (Yeni, Aç, şablon, kurtarma)
    Olay<> sahneDegisti;              // çekirdekte yeni sahne / öznitelik anlığı var (C: çizici, BVH, gezgin)

    // ---- kancalar -----------------------------------------------------------------------------------------------------
    // Pencere kapanmadan önce (D bağlar: "Kaydet / Kaydetme / Vazgeç"). false → kapanma iptal.
    std::function<bool()> kapatmaOnayi;
    // Her karede (ve boşta en az 4 Hz) UI iş parçacığında çağrılan işler: A motor Pompala, D otomatik kayıt zamanlayıcısı.
    // simdiMs: süreç başından beri (test kipinde deterministik).
    void KareIsiEkle(std::string ad, std::function<void(double simdiMs)> is);
    void KareIsleriniCalistir(double simdiMs) const;

private:
    std::vector<std::pair<std::string, std::function<void(double)>>> kareIsleri_;
};

// ---- ortak akışlar (sözleşmeyle tam uygulanmış yapıştırıcı) ---------------------------------------------------------
// Çekirdek işlemini uygular. Rapor geçiş onayı isterse (C1) iletisim->Soru ile sorar ("Genel modele dönüştür" /
// "Vazgeç"); onaylanırsa parametrelere "onay": true ekleyip yeniden uygular. Ardından ModelIslemiSonrasi çağrılır.
// Hata ve uyarılar bildirim->KomutYaz ile yazılır. Komut işleyicileri model değişikliğini HER ZAMAN bu yoldan yapar.
IslemRaporu ModelIslemiUygula(Hizmetler& h, std::string_view islem, const JsonMetni& parametreler);
// Geri al / yinele (B'nin duzenle.geri_al / duzenle.yinele komutları).
IslemRaporu GeriAlUygula(Hizmetler& h);
IslemRaporu YineleUygula(Hizmetler& h);
// Başarılı ve modeli değiştiren rapordan sonra: belge kirli, seçim ayıklanır, sonuç eski işaretlenir, gorunum yeniden
// çizilir, modelDegisti + sahneDegisti yayınlanır. Model değişmediyse yalnız uyarılar yazılır.
void ModelIslemiSonrasi(Hizmetler& h, const IslemRaporu& r);
// Çekirdek yeni model yükledikten sonra (YeniBos / Yukle başarılı): seçim temizlenir, sonuç temizlenir, modelYuklendi +
// sahneDegisti yayınlanır, Sığdır istenir. Belge durumunu (yol, kirli) D ayrıca ProjeBelgesi::Acildi ile kurar.
void ModelYuklendi(Hizmetler& h, const YuklemeSonucu& y);
// JSON nesnesi metnine "onay": true ekler ("" ya da "{}" → {"onay":true}).
JsonMetni OnayEkle(const JsonMetni& parametreler);

}  // namespace op4
