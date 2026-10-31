// op4 — tek örnek borusu (MIMARI §13.2, §13.5; kabul D5). Sahibi: D (dosya-cozum). Bkz. dosya_win.h.
//
// Tel: istemci tek ileti yazar ({"tur":"one_gel","yol":"…","surec":<pid>}, UTF-8), sunucu "tamam" yanıtlar. İstemci
// bağlanır bağlanmaz sunucu sürecine AllowSetForegroundWindow verir (yeni başlatılan süreç ön plan hakkına sahiptir);
// sunucu UI iş parçacığında pencereyi geri yükleyip öne getirir. Boru yalnız yerel istemcileri kabul eder ve adında
// kullanıcının SID'i vardır (başka oturum / kullanıcı bağlanamaz).
#include <windows.h>
#include <sddl.h>

#include <cstdio>
#include <string>

#include "dosya/dosya_win.h"

namespace op4::dosya_win {
namespace {

std::wstring KullaniciSid() {
    static const std::wstring sid = [] {
        std::wstring s = L"bilinmeyen";
        HANDLE t = nullptr;
        if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &t)) return s;
        DWORD n = 0;
        GetTokenInformation(t, TokenUser, nullptr, 0, &n);
        std::string tampon(n, '\0');
        if (n && GetTokenInformation(t, TokenUser, tampon.data(), n, &n)) {
            LPWSTR m = nullptr;
            if (ConvertSidToStringSidW(reinterpret_cast<TOKEN_USER*>(tampon.data())->User.Sid, &m) && m) {
                s = m;
                LocalFree(m);
            }
        }
        CloseHandle(t);
        return s;
    }();
    return sid;
}

// Büyük / küçük harf duyarsız (Windows yolları) FNV-1a 64.
std::wstring BelgeKarmasi(const std::string& yol) {
    std::wstring w = Genis(TamYol(yol));
    for (wchar_t& c : w)
        if (c == L'/') c = L'\\';
    if (!w.empty()) CharLowerBuffW(w.data(), static_cast<DWORD>(w.size()));
    uint64_t k = 14695981039346656037ull;
    for (const wchar_t c : w) {
        k ^= static_cast<uint16_t>(c);
        k *= 1099511628211ull;
    }
    wchar_t b[24];
    std::swprintf(b, 24, L"%016llx", static_cast<unsigned long long>(k));
    return b;
}

}  // namespace

std::wstring TekOrnekBoruAdi(const std::string& belgeYolu) {
    return L"\\\\.\\pipe\\OpusFortis.op4." + KullaniciSid() + L"." + BelgeKarmasi(belgeYolu);
}

bool BaskaPenceredeAcikMi(const std::string& belgeYolu) {
    if (belgeYolu.empty()) return false;
    const std::wstring ad = TekOrnekBoruAdi(belgeYolu);
    HANDLE h = CreateFileW(ad.c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, 0, nullptr);
    if (h == INVALID_HANDLE_VALUE && GetLastError() == ERROR_PIPE_BUSY && WaitNamedPipeW(ad.c_str(), 500))
        h = CreateFileW(ad.c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, 0, nullptr);
    if (h == INVALID_HANDLE_VALUE) return false;  // bu belgeyi açık tutan op4 yok
    DWORD kip = PIPE_READMODE_MESSAGE;
    SetNamedPipeHandleState(h, &kip, nullptr, nullptr);
    ULONG sunucu = 0;
    if (GetNamedPipeServerProcessId(h, &sunucu)) AllowSetForegroundWindow(sunucu);
    std::string ileti = "{\"tur\":\"one_gel\",\"surec\":" + std::to_string(GetCurrentProcessId()) + "}";
    DWORD n = 0;
    bool tamam = WriteFile(h, ileti.data(), static_cast<DWORD>(ileti.size()), &n, nullptr) != 0;
    char yanit[64] = {};
    if (tamam) tamam = ReadFile(h, yanit, sizeof(yanit) - 1, &n, nullptr) != 0 && std::string(yanit, n) == "tamam";
    CloseHandle(h);
    return tamam;
}

TekOrnekSunucusu::~TekOrnekSunucusu() { Durdur(); }

void TekOrnekSunucusu::Durdur() {
    if (durdur_) SetEvent(durdur_);
    if (is_.joinable()) is_.join();
    if (durdur_) CloseHandle(durdur_);
    durdur_ = nullptr;
}

void TekOrnekSunucusu::YolAyarla(const std::string& belgeYolu) {
    Durdur();
    if (belgeYolu.empty()) return;
    durdur_ = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    if (!durdur_) return;
    is_ = std::thread(&TekOrnekSunucusu::Dongu, this, TekOrnekBoruAdi(belgeYolu), durdur_);
}

void TekOrnekSunucusu::Dongu(std::wstring ad, HANDLE durdur) {
    for (;;) {
        // FILE_FLAG_FIRST_PIPE_INSTANCE: ad başka bir süreçteyse (aynı belge --yeni-ornek ile açılmış) sunucu açılmaz.
        HANDLE b = CreateNamedPipeW(ad.c_str(), PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED | FILE_FLAG_FIRST_PIPE_INSTANCE,
                                    PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS, 1,
                                    4096, 4096, 0, nullptr);
        if (b == INVALID_HANDLE_VALUE) return;
        OVERLAPPED o{};
        o.hEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
        bool bagli = ConnectNamedPipe(b, &o) != 0;
        if (!bagli) {
            const DWORD k = GetLastError();
            if (k == ERROR_PIPE_CONNECTED) bagli = true;
            else if (k == ERROR_IO_PENDING) {
                HANDLE bekle[2] = {durdur, o.hEvent};
                const DWORD w = WaitForMultipleObjects(2, bekle, FALSE, INFINITE);
                if (w == WAIT_OBJECT_0) {
                    CancelIo(b);
                    CloseHandle(o.hEvent);
                    CloseHandle(b);
                    return;
                }
                DWORD n = 0;
                bagli = GetOverlappedResult(b, &o, &n, FALSE) != 0;
            }
        }
        if (bagli) {
            char tampon[1024];
            DWORD n = 0;
            OVERLAPPED r{};
            r.hEvent = o.hEvent;
            ResetEvent(o.hEvent);
            BOOL okundu = ReadFile(b, tampon, sizeof(tampon), &n, &r);
            if (!okundu && GetLastError() == ERROR_IO_PENDING) {
                if (WaitForSingleObject(r.hEvent, 2000) == WAIT_OBJECT_0) okundu = GetOverlappedResult(b, &r, &n, FALSE);
                else CancelIo(b);
            }
            if (okundu && std::string(tampon, n).find("\"one_gel\"") != std::string::npos) {
                oneGel_ = true;
                const char cevap[] = "tamam";
                OVERLAPPED y{};
                y.hEvent = o.hEvent;
                ResetEvent(o.hEvent);
                if (!WriteFile(b, cevap, sizeof(cevap) - 1, &n, &y) && GetLastError() == ERROR_IO_PENDING)
                    WaitForSingleObject(y.hEvent, 2000);
                FlushFileBuffers(b);
            }
            DisconnectNamedPipe(b);
        }
        CloseHandle(o.hEvent);
        CloseHandle(b);
        if (WaitForSingleObject(durdur, 0) == WAIT_OBJECT_0) return;
    }
}

}  // namespace op4::dosya_win
