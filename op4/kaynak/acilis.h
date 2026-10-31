// op4 — açılış ekranı "Kemer Çizgisi" (MIMARI §25; kimlik/acilis/aciklama.md, koyu ikizi kimlik/acilis-koyu/).
//
// Kenarlıksız katmanlı pencere, kendi iş parçacığında Direct2D (WIC bit eşlemi hedefi) + DirectWrite ile çizilir; d2d1.dll ve
// dwrite.dll çalışma anında yüklenir (bağlama değişikliği yok). Kalem yolları kaynak/arayuz/acilis_kontur.h'den
// (kimlik/acilis/kontur.json), yazı tipleri gömülü veriden (arayuz/yazi.h; DirectWrite bellek içi yükleyici, yoksa
// Segoe UI), logo katmanları kimlik/acilis/katmanlar/*.png ve kimlik/opus-fortis-yazi-*-zemin.png'den gelir.
//
// Zaman çizelgesi aciklama.md "Hareket çizelgesi" ile aynıdır; adımlar GERÇEK yükleme olaylarından gelir (Adim,
// AdimIlerleme): görsel saat gerçek adımın sonunu geçmez (bekler), gerçek adım öndeyse 2,5× hızla yetişir.
#pragma once

#include <windows.h>

#include <memory>
#include <string>

namespace op4 {

enum class AcilisAdimi : int { Arayuz = 0, Grafik = 1, Motor = 2, Kutuphane = 3, Proje = 4, Hazir = 5 };

class AcilisEkrani {
public:
    AcilisEkrani();
    ~AcilisEkrani();
    AcilisEkrani(const AcilisEkrani&) = delete;
    AcilisEkrani& operator=(const AcilisEkrani&) = delete;

    // Pencereyi ve çizim iş parçacığını başlatır (hemen döner). koyu = Ayarlar › Görüntü › Açılış ekranı "Koyu".
    void Baslat(HINSTANCE ornek, const std::wstring& uygulamaDizini, const std::string& surum, bool koyu);
    // İş parçacığı güvenli. Adim(a): a adımı başladı (öncekiler bitti). AdimIlerleme: adım içi oran (0–1).
    void Adim(AcilisAdimi a);
    void AdimIlerleme(AcilisAdimi a, float oran);
    // "Hazır" canlandırması (kilit taşı oturur, OPUS FORTİS belirir) bitti mi. Başlatılmadıysa true.
    bool Bitti() const;
    void Kapat();

    struct Ic;

private:
    std::unique_ptr<Ic> ic_;
};

// --test-acilis: t (ms) anındaki kareyi (960×540 DIP × ölçek) PNG'ye çizer; adımlar çizelgedeki gibi varsayılır.
bool AcilisResmi(const std::wstring& uygulamaDizini, const std::string& surum, const std::wstring& png, float olcek,
                 double zamanMs, bool koyu, std::string& hata);

}  // namespace op4
