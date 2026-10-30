// op4 — açılış (yükleme) ekranı: kenarlıksız, ekranın ortasında; Opus Fortis logo yuvası + ilerleme metni ve çubuğu.
// Logo: <uygulama>\kimlik\logo.png → opus-fortis-yatay-acik-zemin.png (kurumsal) → opus_fortis_logo_placeholder.png.
#pragma once

#include <windows.h>

#include <mutex>
#include <string>

#include "resim.h"

namespace op4 {

class AcilisEkrani {
public:
    static std::wstring LogoYolu(const std::wstring& uygulamaDizini);

    bool Olustur(HINSTANCE ornek, const std::wstring& uygulamaDizini, const std::wstring& surum);
    // İş parçacığı güvenli.
    void Ilerleme(const std::string& metin, float oran);
    void Kapat();
    HWND Pencere() const { return hwnd_; }

    // Ekranı (g × y piksel, ölçek = DPI / 96) BGRA belleğe çizer (pencere ve --test-acilis aynı kodu kullanır).
    static void Ciz(HDC dc, int g, int y, float olcek, const Resim* logo, const std::wstring& surum,
                    const std::wstring& metin, float oran);
    static constexpr int TABAN_G = 620, TABAN_Y = 380;  // 96 DPI'daki boyut
    static constexpr int LOGO_Y = 160;                  // logo yuvasının yüksekliği (96 DPI); genişlik TABAN_G − 80

private:
    static LRESULT CALLBACK Yordam(HWND h, UINT m, WPARAM w, LPARAM l);
    HWND hwnd_ = nullptr;
    float olcek_ = 1.0f;
    Resim logo_;
    bool logoVar_ = false;
    std::wstring surum_;
    std::mutex kilit_;
    std::wstring metin_ = L"Başlatılıyor…";
    float oran_ = 0.0f;
};

// --test-acilis: açılış ekranını PNG'ye çizer.
bool AcilisResmi(const std::wstring& uygulamaDizini, const std::wstring& surum, const std::wstring& png, float olcek,
                 std::string& hata);

}  // namespace op4
