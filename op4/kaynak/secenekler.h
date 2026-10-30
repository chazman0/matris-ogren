// op4 — komut satırı seçenekleri ve test kiplerinin ortak yardımcıları (MIMARI §6.14; sözleşme S24).
//
// F1'de gereken BÜTÜN bayraklar burada önceden tanımlıdır; paketler yeni bayrak için bu dosyaya dokunmaz, ilgili alanı
// okur. (Yeni bayrak gerekirse: alan + Ayristir satırı + ana.cpp yardım yorumu, tek değişiklik olarak.) Sahibi: A.
#pragma once

#include <windows.h>

#include <string>

namespace op4 {

struct Secenekler {
    // test kipleri
    bool testMotor = false;           // --test-motor                          (A)
    std::wstring testEkran;           // --test-ekran a.png [--boyut GxY] [--arayuzsuz]   (C)
    std::wstring testAcilis;          // --test-acilis a.png [--olcek 1.5]     (C)
    int testPencere = 0;              // --test-pencere <saniye>               (C)
    std::wstring senaryo;             // --senaryo s.json  (betikli komutlar, olaylar, bekle, çek; MIMARI §6.14) (C)
    bool ozSinama = false;            // --oz-sinama  (kurulu programın kendi kendini sınaması)                   (A)
    // uygulama
    std::wstring proje;               // konumsal: açılacak dosya (.op4, .matris, .json)                          (D)
    bool yeniOrnek = false;           // --yeni-ornek: tek örnek borusunu atla, ayrı süreç (MIMARI §13.5)          (D)
    bool acilisYok = false;           // --acilis-yok: açılış ekranı gösterilmez (MIMARI §18.2)                   (C)
    std::wstring golgelendiriciDizini;  // --golgelendirici-dizini: HLSL'yi çalışma anında derle (geliştirici)   (A)
    // ortak
    std::wstring gunluk;              // --gunluk dosya.log
    bool warp = false;                // --warp
    bool motorsuz = false;            // --motorsuz
    bool surum = false;               // --surum
    bool hataKatmani = false;         // --hata-katmani (eşanlamlı: --grafik-denetim)
    bool arayuzsuz = false;           // --arayuzsuz
    int g = 960, y = 540;             // --boyut GxY
    float olcek = 1.0f;               // --olcek

    bool TestKipiMi() const {
        return testMotor || !testEkran.empty() || !testAcilis.empty() || testPencere > 0 || !senaryo.empty() || ozSinama;
    }
};

bool Ayristir(Secenekler& s, std::string& hata);

std::wstring UygulamaDizini();
std::wstring YerelVeriDizini();
// Veri katalogları klasörü: <uygulama>\veri (kurulu); yoksa geliştirme derlemesinde kaynak ağacındaki op4\veri.
std::wstring VeriDizini();
std::string Bicim(const char* bicim, ...)
#if defined(__GNUC__)
    __attribute__((format(gnu_printf, 1, 2)))
#endif
    ;
// Test kipleri: hata pencereleri açılmasın (CI'da asılı kalmasın), çökme yakalansın (çıkış 5), süre sınırı (çıkış 3).
void TestKipi(unsigned saniye);

}  // namespace op4
