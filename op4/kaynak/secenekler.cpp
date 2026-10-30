// op4 — komut satırı seçenekleri ve test kiplerinin ortak yardımcıları (sözleşme S24). Sahibi: A.
#include "secenekler.h"

#include <shellapi.h>
#include <shlobj.h>

#include <algorithm>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <thread>

#include "gunluk.h"

namespace op4 {

std::wstring UygulamaDizini() {
    std::wstring b(32768, L'\0');
    DWORD n = GetModuleFileNameW(nullptr, b.data(), static_cast<DWORD>(b.size()));
    b.resize(n);
    size_t i = b.find_last_of(L"\\/");
    return i == std::wstring::npos ? std::wstring(L".") : b.substr(0, i);
}

std::wstring YerelVeriDizini() {
    PWSTR p = nullptr;
    std::wstring d;
    if (SUCCEEDED(SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, nullptr, &p))) d = p;
    CoTaskMemFree(p);
    if (d.empty()) return UygulamaDizini();
    d += L"\\Opus Fortis";
    CreateDirectoryW(d.c_str(), nullptr);
    d += L"\\op4";
    CreateDirectoryW(d.c_str(), nullptr);
    return d;
}

std::wstring VeriDizini() {
    const std::wstring kurulu = UygulamaDizini() + L"\\veri";
    if (GetFileAttributesW((kurulu + L"\\komutlar.json").c_str()) != INVALID_FILE_ATTRIBUTES) return kurulu;
#ifdef OP4_GELISTIRME_VERI
    return Genis(OP4_GELISTIRME_VERI);
#else
    return kurulu;
#endif
}

bool Ayristir(Secenekler& s, std::string& hata) {
    int n = 0;
    wchar_t** a = CommandLineToArgvW(GetCommandLineW(), &n);
    bool tamam = true;
    for (int i = 1; i < n && tamam; ++i) {
        std::wstring k = a[i];
        auto deger = [&](std::wstring& h) {
            if (i + 1 >= n) {
                hata = Utf8(k) + " bir değer bekliyor";
                tamam = false;
                return;
            }
            h = a[++i];
        };
        if (k == L"--test-motor") s.testMotor = true;
        else if (k == L"--test-ekran") deger(s.testEkran);
        else if (k == L"--test-acilis") deger(s.testAcilis);
        else if (k == L"--senaryo") deger(s.senaryo);
        else if (k == L"--oz-sinama") s.ozSinama = true;
        else if (k == L"--gunluk") deger(s.gunluk);
        else if (k == L"--warp") s.warp = true;
        else if (k == L"--arayuzsuz") s.arayuzsuz = true;
        else if (k == L"--motorsuz") s.motorsuz = true;
        else if (k == L"--surum") s.surum = true;
        else if (k == L"--hata-katmani" || k == L"--grafik-denetim") s.hataKatmani = true;
        else if (k == L"--yeni-ornek") s.yeniOrnek = true;
        else if (k == L"--acilis-yok") s.acilisYok = true;
        else if (k == L"--golgelendirici-dizini") deger(s.golgelendiriciDizini);
        else if (k == L"--test-pencere") {
            std::wstring v;
            deger(v);
            if (tamam) s.testPencere = std::clamp(_wtoi(v.c_str()), 1, 600);
        }
        else if (k == L"--boyut") {
            std::wstring v;
            deger(v);
            if (tamam && (swscanf(v.c_str(), L"%dx%d", &s.g, &s.y) != 2 || s.g < 64 || s.y < 64 || s.g > 8192 || s.y > 8192)) {
                hata = "--boyut GxY biçiminde olmalı (ör. 960x540)";
                tamam = false;
            }
        } else if (k == L"--olcek") {
            std::wstring v;
            deger(v);
            if (tamam) s.olcek = std::clamp(static_cast<float>(_wtof(v.c_str())), 0.5f, 4.0f);
        } else if (!k.empty() && k[0] != L'-') s.proje = k;
        else {
            hata = "bilinmeyen seçenek: " + Utf8(k);
            tamam = false;
        }
    }
    LocalFree(a);
    return tamam;
}

std::string Bicim(const char* bicim, ...) {
    va_list a;
    va_start(a, bicim);
    char b[1024];
    const int n = std::vsnprintf(b, sizeof(b), bicim, a);
    va_end(a);
    return std::string(b, n < 0 ? 0 : std::min(static_cast<size_t>(n), sizeof(b) - 1));
}

namespace {
LONG WINAPI CokmeYakala(EXCEPTION_POINTERS* e) {
    Gunluk("ÇÖKME: özel durum 0x%08lX, adres %p", static_cast<unsigned long>(e->ExceptionRecord->ExceptionCode),
           e->ExceptionRecord->ExceptionAddress);
    GunlukKapat();
    ExitProcess(5);
}
}  // namespace

void TestKipi(unsigned saniye) {
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
#ifdef _MSC_VER
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    SetUnhandledExceptionFilter(CokmeYakala);
    std::thread([saniye] {
        Sleep(saniye * 1000);
        Gunluk("ZAMAN AŞIMI: test %u saniyede bitmedi", saniye);
        GunlukKapat();
        ExitProcess(3);
    }).detach();
}

}  // namespace op4
