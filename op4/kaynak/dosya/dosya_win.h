// op4 — dosya modülünün Windows parçaları (D): yerel iletişim kutuları, tek örnek borusu, çökme dökümü, kabuk
// tümleşimi (atlama listesi, pencere başlığı). Yalnız op4.exe'de derlenir (kaynak/dosya/).
#pragma once

#include <windows.h>

#include <atomic>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

#include "cekirdek/arayuz_kancalari.h"

namespace op4::dosya_win {

std::wstring Genis(const std::string& utf8);
std::string Dar(const std::wstring& w);
// Göreli yolu mutlak yapar (GetFullPathNameW); okunamazsa olduğu gibi.
std::string TamYol(const std::string& yol);

// IFileOpenDialog / IFileSaveDialog (süzgeçler, klasör, önerilen ad, varsayılan uzantı) ve TaskDialogIndirect
// (özel düğmeler; Esc = −1). comctl32 v6 yoksa MessageBoxW yedeği. Sahip pencere her çağrıda sorulur.
std::unique_ptr<IletisimKutulari> WinIletisimKutulariOlustur(std::function<void*()> anaPencere);

// Atlama listesi ve Başlat › Son kullanılanlar (SHAddToRecentDocs).
void SonBelgeEkle(const std::string& yol);

// ---- tek örnek borusu (MIMARI §13.2 "ikinci açılış", §13.5) -------------------------------------------------------------
// Ad: \\.\pipe\OpusFortis.op4.<SID>.<belge karması>. Bir belgeyi açık tutan op4 süreci o belgenin adıyla sunucu açar;
// aynı dosya yeniden açılmak istenince (çift tık, ilişkilendirme, komut satırı) yeni süreç bu boruya bağlanır, sunucu
// süreci öne gelir ve yeni süreç çıkar. Başka bir dosya her zaman yeni pencerede açılır (pencere başına bir proje, D18).
// --yeni-ornek denetimi atlar.
std::wstring TekOrnekBoruAdi(const std::string& belgeYolu);
// Yeni süreç tarafı: dosya başka bir op4 penceresinde açıksa onu öne getirir ve true döner.
bool BaskaPenceredeAcikMi(const std::string& belgeYolu);

class TekOrnekSunucusu {
public:
    TekOrnekSunucusu() = default;
    ~TekOrnekSunucusu();
    TekOrnekSunucusu(const TekOrnekSunucusu&) = delete;
    TekOrnekSunucusu& operator=(const TekOrnekSunucusu&) = delete;
    // Belge yolu değişince (Aç, Farklı kaydet, Yeni → boş) borunun adını değiştirir.
    void YolAyarla(const std::string& belgeYolu);
    void Durdur();
    // UI iş parçacığı: bir istemci "öne gel" dedi mi? (okuyunca sıfırlanır)
    bool OneGetirIstendi() { return oneGel_.exchange(false); }

private:
    void Dongu(std::wstring ad, HANDLE durdur);
    std::thread is_;
    HANDLE durdur_ = nullptr;
    std::atomic<bool> oneGel_{false};
};

// ---- çökme dökümü (MIMARI §13.3) --------------------------------------------------------------------------------------
// SetUnhandledExceptionFilter + std::set_terminate: <cokme>\op4-YYYYMMDD-HHMMSS-<pid>.dmp (MiniDumpWriteDump,
// dbghelp.dll önceden yüklenir). En yeni 10 döküm tutulur. Test kiplerinde kurulmaz (A'nın TestKipi işleyicisi geçerli).
void CokmeDokumuKur(const std::string& cokmeDizini);

}  // namespace op4::dosya_win
