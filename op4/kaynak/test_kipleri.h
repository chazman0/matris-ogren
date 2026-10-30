// op4 — test kipleri (MIMARI §6.14; sözleşme S24). Her kip kendi paketinin dosyasındadır:
//   MotorTesti, OzSinama        A  kaynak/test_motor.cpp
//   EkranTesti, AcilisTesti,
//   SenaryoCalistir             C  kaynak/test_ekran.cpp
// Çıkış kodları: 0 başarılı, 1 kullanım, 2 test hatası, 3 zaman aşımı, 5 çökme. Ölçümler "OP4OLCUM anahtar=değer …".
#pragma once

#include "secenekler.h"

namespace op4 {

class Grafik;

int MotorTesti();
int OzSinama(const Secenekler& s);
int EkranTesti(const Secenekler& s);
int AcilisTesti(const Secenekler& s);
// --senaryo s.json: betikli komut dizgileri, sentetik olaylar, bekle ve çek adımları, deterministik saat (C, F1 iş 1.4).
int SenaryoCalistir(const Secenekler& s);

// Ortak (C): ImGui bağlamı + tema + yazı tipi; D3D12 hata ayıklama katmanı yoklamasını günlüğe yazar (MIMARI D13).
void ImGuiBaglamiKur(float olcek, const char* ini);
void HataKatmaniYaz(const Grafik* g);

// Uygulama (C): açılış ekranı → ana pencere → döngü; --test-pencere de bu yoldan çalışır.
int UygulamaCalistir(HINSTANCE ornek, const Secenekler& s);

}  // namespace op4
