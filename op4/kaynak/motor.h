// op4 — gömülü CPython hesap motoru köprüsü.
//
// python3XX.dll derleme anında bağlanmaz: çalışma anında <uygulama>\python\ klasöründen LoadLibraryEx ile yüklenir ve
// kullanılan C API işlevleri GetProcAddress ile çözülür. Böylece
//   * op4.exe'nin Python başlık / .lib dosyasına ihtiyacı yoktur; aynı ikili 3.12 / 3.13 / 3.14 gömülü Python ile çalışır
//     (yalnız kararlı, dışa aktarılan işlevler kullanılır),
//   * Python eksik ya da bozuksa program "DLL bulunamadı" sistem penceresiyle çökmez; açılış ekranı / durum çubuğu
//     anlaşılır bir hata gösterir.
// sys.path, python\python3XX._pth dosyasıyla belirlenir (gömülü dağıtımın standart yöntemi; ortam değişkenleri yok
// sayılır): python3XX.zip, ., Lib\site-packages, ..\motor.
//
// Tüm Python çağrıları TEK bir işçi iş parçacığında yapılır (yorumlayıcı orada başlatılır ve kapatılır); arayüz iş
// parçacığı hiç beklemez. İstekler kuyruğa alınır, yanıtlar geri çağrıyla ya da Calistir() ile döner.
#pragma once

#include <windows.h>

#include <condition_variable>
#include <deque>
#include <functional>
#include <future>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace op4 {

struct MotorDurumu {
    bool hazir = false;      // başlatma bitti (başarılı ya da değil)
    bool basarili = false;
    std::string hata;
    std::string pythonSurumu;     // Py_GetVersion
    std::string surumJson;        // web_kopru.surum_json()
    std::string sablonlarJson;    // web_kopru.calistir({"islem": "bina_sablonlar"})
    int sablonSayisi = -1;
    std::vector<std::string> sablonAdlari;
    double msDll = 0, msBaslat = 0, msIceAktar = 0, msSurum = 0, msSablon = 0, msToplam = 0;
};

class Motor {
public:
    using Ilerleme = std::function<void(const std::string& metin, float oran)>;

    ~Motor();
    // uygulamaDizini: op4.exe'nin klasörü (python\ ve motor\ alt klasörleri burada aranır).
    void Baslat(const std::wstring& uygulamaDizini, Ilerleme ilerleme);
    // Başlatma bitene dek (ya da süre dolana dek) bekler; true: bitti.
    bool Bekle(DWORD ms);
    HANDLE HazirOlayi() const { return hazirOlayi_; }
    MotorDurumu Durum() const;
    // web_kopru.calistir(istek) — eşzamanlı (çağıran bekler). Motor hazır değilse hata JSON'u döner.
    std::string Calistir(const std::string& istekJson);
    // Kuyruğu durdurur, yorumlayıcıyı kapatır (Py_FinalizeEx), iş parçacığını bekler.
    void Durdur();

private:
    struct Is {
        std::string istek;
        std::promise<std::string> yanit;
    };
    void Calis(std::wstring dizin, Ilerleme ilerleme);

    mutable std::mutex kilit_;
    std::condition_variable kosul_;
    std::deque<Is*> kuyruk_;
    bool dur_ = false;
    MotorDurumu durum_;
    std::thread is_;
    HANDLE hazirOlayi_ = CreateEventW(nullptr, TRUE, FALSE, nullptr);
};

}  // namespace op4
