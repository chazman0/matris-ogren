// op4 — çökme dökümü (MIMARI §13.3; kabul D5). Sahibi: D (dosya-cozum).
// Yakalanmayan SEH istisnası ve std::terminate'te <cokme>\op4-YYYYMMDD-HHMMSS-<pid>.dmp yazılır (MiniDumpWriteDump;
// dbghelp.dll kurulumda yüklenir, işleyici bellek ayırmaz). Ardından önceki süzgece devredilir (Windows hata raporu).
// Kurtarma için ayrıca bir şey yapılmaz: otomatik kayıt kaydı diskte durur, bir sonraki açılış "Kurtar / Sil / Sonra" sorar.
#include <windows.h>

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cwchar>
#include <exception>
#include <filesystem>
#include <vector>

#include "dosya/dosya_win.h"

namespace op4::dosya_win {
namespace {

// dbghelp.h'nin MINIDUMP_EXCEPTION_INFORMATION'ı (4 bayt paketli); MinGW başlıkları içermediği için burada.
#pragma pack(push, 4)
struct DokumIstisnaBilgisi {
    DWORD ThreadId;
    EXCEPTION_POINTERS* ExceptionPointers;
    BOOL ClientPointers;
};
#pragma pack(pop)
using MiniDumpYazIslevi = BOOL(WINAPI*)(HANDLE, DWORD, HANDLE, int, DokumIstisnaBilgisi*, void*, void*);
constexpr int kDokumTuru = 0x00000001 /*DataSegs*/ | 0x00000004 /*HandleData*/ | 0x00000020 /*UnloadedModules*/ |
                           0x00000040 /*IndirectlyReferencedMemory*/ | 0x00001000 /*ThreadInfo*/;

wchar_t g_dizin[1024] = {};
MiniDumpYazIslevi g_yaz = nullptr;
LPTOP_LEVEL_EXCEPTION_FILTER g_onceki = nullptr;
std::terminate_handler g_oncekiSonlandirma = nullptr;
volatile LONG g_yaziliyor = 0;

void DokumYaz(EXCEPTION_POINTERS* e) {
    if (!g_yaz || InterlockedExchange(&g_yaziliyor, 1)) return;
    SYSTEMTIME t;
    GetLocalTime(&t);
    wchar_t yol[1200];
    std::swprintf(yol, 1200, L"%ls\\op4-%04u%02u%02u-%02u%02u%02u-%lu.dmp", g_dizin, t.wYear, t.wMonth, t.wDay, t.wHour,
                  t.wMinute, t.wSecond, static_cast<unsigned long>(GetCurrentProcessId()));
    HANDLE f = CreateFileW(yol, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return;
    DokumIstisnaBilgisi b{GetCurrentThreadId(), e, FALSE};
    g_yaz(GetCurrentProcess(), GetCurrentProcessId(), f, kDokumTuru, e ? &b : nullptr, nullptr, nullptr);
    CloseHandle(f);
}

LONG WINAPI Suzgec(EXCEPTION_POINTERS* e) {
    DokumYaz(e);
    return g_onceki ? g_onceki(e) : EXCEPTION_CONTINUE_SEARCH;
}

[[noreturn]] void Sonlandirma() {
    // C++ istisnası yakalanmadı: istisna bilgisi olmadan döküm (yığınlar ve modüller yine yazılır).
    DokumYaz(nullptr);
    if (g_oncekiSonlandirma) g_oncekiSonlandirma();
    std::abort();
}

void EskileriBudama(const std::filesystem::path& d, size_t tut) {
    std::error_code e;
    std::vector<std::filesystem::directory_entry> l;
    for (std::filesystem::directory_iterator i(d, e), son; !e && i != son; i.increment(e))
        if (i->path().extension() == ".dmp") l.push_back(*i);
    if (l.size() <= tut) return;
    std::sort(l.begin(), l.end(), [](const auto& a, const auto& b) {
        std::error_code x;
        return a.last_write_time(x) > b.last_write_time(x);
    });
    for (size_t i = tut; i < l.size(); ++i) std::filesystem::remove(l[i].path(), e);
}

}  // namespace

void CokmeDokumuKur(const std::string& cokmeDizini) {
    const std::wstring d = Genis(cokmeDizini);
    if (d.empty() || d.size() >= std::size(g_dizin)) return;
    CreateDirectoryW(d.c_str(), nullptr);
    for (size_t i = 0; i <= d.size(); ++i) g_dizin[i] = i < d.size() ? d[i] : L'\0';
    if (HMODULE m = LoadLibraryW(L"dbghelp.dll"))
        g_yaz = reinterpret_cast<MiniDumpYazIslevi>(reinterpret_cast<void*>(GetProcAddress(m, "MiniDumpWriteDump")));
    if (!g_yaz) return;
    EskileriBudama(std::filesystem::path(d), 10);
    g_onceki = SetUnhandledExceptionFilter(&Suzgec);
    g_oncekiSonlandirma = std::set_terminate(&Sonlandirma);
}

}  // namespace op4::dosya_win
