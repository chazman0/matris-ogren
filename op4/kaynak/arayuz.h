// op4 — Dear ImGui arayüzü: ana menü, yerleştirme alanı (dockspace), Özellikler paneli, Komut paneli, durum çubuğu.
// 3B sahne, yerleştirme alanının merkez düğümüne (saydam, "passthru") çizilir; panellerin altında kalmaz.
#pragma once

#include <deque>
#include <string>
#include <vector>

#include "grafik.h"
#include "motor.h"

namespace op4 {

enum class Istek { Yok, Yeni, Ac, Kaydet, FarkliKaydet, Cikis, Sigdir, YerlesimiSifirla };

struct ArayuzDurumu {
    // girdiler
    std::string bagdastirici;
    bool warp = false;
    unsigned ornek = 1;
    const char* ozellikDuzeyi = "";
    size_t ucgen = 0;
    MotorDurumu motor;
    bool motorBaslatildi = false;
    std::string projeAdi = "Adsız";
    bool degisti = false;
    float fps = 0;
    bool testModu = false;
    // ayarlar (arayüz değiştirir)
    SahneAyari sahne;
    // çıktılar
    GorusAlani gorus;   // 3B sahne alanı (piksel)
    Istek istek = Istek::Yok;
    bool yerlesimKuruldu = false;
    std::deque<std::string> komutGecmisi;
    char komut[256] = {};
};

void ArayuzStili(float olcek);         // tema + DPI ölçeği (her DPI değişiminde yeniden çağrılır)
void ArayuzYazitipi(float olcek);      // Segoe UI (Türkçe karakterler); yoksa ImGui'nin gömülü yazı tipi
void ArayuzCiz(ArayuzDurumu& d);
void KomutYaz(ArayuzDurumu& d, const std::string& satir);

}  // namespace op4
