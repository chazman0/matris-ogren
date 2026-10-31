// op4 — giriş noktası (sözleşme S24; sahibi A). Yalnız komut satırını ayrıştırır ve ilgili kipe dağıtır.
//
//   op4.exe                                   uygulama: açılış ekranı → ana pencere (DirectX 12 + Dear ImGui)
//   op4.exe proje.op4                         uygulama, proje açık
//   op4.exe --test-motor                      hesap motoru süreçleri (op4motor.exe + op4_sunucu) uçtan uca denetimi
//   op4.exe --test-ekran a.png [--boyut GxY] [--arayuzsuz]
//                                             tek kareyi WARP (yazılım D3D12) ile ekran dışına çizer, PNG kaydeder
//   op4.exe --test-acilis a.png [--olcek 1.5] açılış ekranını PNG'ye çizer
//   op4.exe --test-pencere 8                  uygulamayı (açılış + motor + pencere) çalıştırır, betikli kaydırma /
//                                             döndürme / yakınlaşma uygular, ölçer ve 8 s sonra kapanır
//   op4.exe --senaryo s.json                  betikli senaryo (komutlar, olaylar, bekle, çek; F1 iş 1.4 — taslak)
//   op4.exe --oz-sinama                       kurulu programın kendi kendini sınaması (motor, çekirdek, şablon,
//                                             kaydet / aç, ekran; uygulanmamış adımlar atlanır)
//   ortak:  --gunluk dosya.log   --warp (uygulamada donanım yerine WARP)   --motorsuz (hesap motoru başlatılmaz)   --surum
//           --hata-katmani | --grafik-denetim (D3D12 hata ayıklama katmanı; varsa açılır; hata iletisi testi düşürür)
//           --yeni-ornek (tek örnek borusunu atla)   --acilis-yok
//           --golgelendirici-dizini <klasör> (geliştirici: <klasör>\op4.hlsl çalışma anında derlenir)
//   ortam:  OP4_MOTOR=gomulu (tanı: Faz 0 süreç içi gömülü motor)   OP4_KULLANICI_DIZINI (sınama klasörleri)
//           OP4_GOLGELENDIRICI=calisma_ani (ölçüm: gömülü bayt kodu yerine çalışma anı derlemesi; CI kabul A4)
// Ölçümler günlüğe "OP4OLCUM anahtar=değer …" satırları olarak da yazılır (MIMARI §20.3).
// Çıkış kodları: 0 başarılı, 1 kullanım hatası, 2 test hatası, 3 zaman aşımı, 5 çökme.
#include <windows.h>
#include <objbase.h>

#include <string>

#include "grafik/golgelendirici_bayt_gelistirme.h"
#include "gunluk.h"
#include "secenekler.h"
#include "test_kipleri.h"

int WINAPI wWinMain(HINSTANCE ornek, HINSTANCE, PWSTR, int) {
    using namespace op4;
    CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    Secenekler s;
    std::string hata;
    const bool tamam = Ayristir(s, hata);
    std::wstring gunluk = s.gunluk;
    const bool test = s.TestKipiMi();
    if (gunluk.empty() && !test) gunluk = YerelVeriDizini() + L"\\op4.log";
    GunlukAc(gunluk);
    if (!tamam) {
        Gunluk("Kullanım hatası: %s", hata.c_str());
        if (!test) MessageBoxW(nullptr, Genis(hata).c_str(), L"op4", MB_ICONWARNING);
        return 1;
    }
    if (s.surum) {
        Gunluk("op4 %s", OP4_SURUM);
        return 0;
    }
    if (!s.golgelendiriciDizini.empty()) GolgelendiriciDiziniAyarla(s.golgelendiriciDizini);
    int kod;
    if (s.testMotor)
        kod = MotorTesti();
    else if (!s.testEkran.empty())
        kod = EkranTesti(s);
    else if (!s.testAcilis.empty())
        kod = AcilisTesti(s);
    else if (!s.senaryo.empty())
        kod = SenaryoCalistir(s);
    else if (s.ozSinama)
        kod = OzSinama(s);
    else
        kod = UygulamaCalistir(ornek, s);
    GunlukKapat();
    CoUninitialize();
    return kod;
}
