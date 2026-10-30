#include "gunluk.h"

#include <windows.h>

#include <cstdarg>
#include <cstdio>
#include <mutex>
#include <vector>

namespace op4 {
namespace {

LARGE_INTEGER BaslangicSayaci() {
    LARGE_INTEGER t;
    QueryPerformanceCounter(&t);
    return t;
}

const LARGE_INTEGER g_baslangic = BaslangicSayaci();
std::mutex g_kilit;
HANDLE g_dosya = INVALID_HANDLE_VALUE;

void Yaz(HANDLE h, const std::string& s) {
    if (h == nullptr || h == INVALID_HANDLE_VALUE) return;
    DWORD yazilan = 0;
    WriteFile(h, s.data(), static_cast<DWORD>(s.size()), &yazilan, nullptr);
}

void Satir(const std::string& satir) {
    std::lock_guard<std::mutex> kilit(g_kilit);
    Yaz(g_dosya, satir);
    if (g_dosya != INVALID_HANDLE_VALUE) FlushFileBuffers(g_dosya);
    // GUI alt sistemindeki bir süreçte standart çıktı ancak üst süreç (ör. CI kabuğu) tutamaç verdiyse vardır.
    Yaz(GetStdHandle(STD_OUTPUT_HANDLE), satir);
    OutputDebugStringW(Genis(satir).c_str());
}

}  // namespace

double GecenMs() {
    LARGE_INTEGER simdi, siklik;
    QueryPerformanceCounter(&simdi);
    QueryPerformanceFrequency(&siklik);
    return 1000.0 * static_cast<double>(simdi.QuadPart - g_baslangic.QuadPart) / static_cast<double>(siklik.QuadPart);
}

std::string Utf8(const std::wstring& w) {
    if (w.empty()) return {};
    int n = WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), nullptr, 0, nullptr, nullptr);
    std::string s(static_cast<size_t>(n), '\0');
    WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), s.data(), n, nullptr, nullptr);
    return s;
}

std::wstring Genis(const std::string& s) {
    if (s.empty()) return {};
    int n = MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), nullptr, 0);
    std::wstring w(static_cast<size_t>(n), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), w.data(), n);
    return w;
}

void GunlukAc(const std::wstring& dosya) {
    std::lock_guard<std::mutex> kilit(g_kilit);
    if (g_dosya != INVALID_HANDLE_VALUE) CloseHandle(g_dosya);
    g_dosya = INVALID_HANDLE_VALUE;
    if (!dosya.empty())
        g_dosya = CreateFileW(dosya.c_str(), GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_ALWAYS,
                              FILE_ATTRIBUTE_NORMAL, nullptr);
}

void GunlukKapat() { GunlukAc(std::wstring()); }

void Gunluk(const char* bicim, ...) {
    char zaman[32];
    std::snprintf(zaman, sizeof(zaman), "[%9.1f ms] ", GecenMs());
    va_list a;
    va_start(a, bicim);
    va_list b;
    va_copy(b, a);
    int n = std::vsnprintf(nullptr, 0, bicim, a);
    va_end(a);
    std::string govde(n > 0 ? static_cast<size_t>(n) : 0, '\0');
    if (n > 0) std::vsnprintf(govde.data(), govde.size() + 1, bicim, b);
    va_end(b);
    Satir(std::string(zaman) + govde + "\n");
}

void GunlukHam(const std::string& metin) { Satir(metin + "\n"); }

}  // namespace op4
