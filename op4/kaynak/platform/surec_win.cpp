// op4 platform — alt süreç + iki anonim boru, Win32 (sözleşme S14; F1 iş 1.2, MIMARI §8.1, §8.4). Uygulayan: A.
//
// CreatePipe ×2; çocuğa YALNIZ dört tutamaç miras verilir (STARTUPINFOEX + PROC_THREAD_ATTRIBUTE_HANDLE_LIST): istek
// borusunun okuma ucu, yanıt borusunun yazma ucu, stdin (NUL) ve stdout/stderr (ciktiDosyasi'na ekleme kipinde ya da NUL).
// "{istek}" / "{yanit}" yer tutucuları çocuktaki HANDLE değerlerinin onluk yazımı olur (miras alınan tutamaçlar aynı
// değeri taşır). Süreç CREATE_NO_WINDOW ile, askıda başlatılır, bir Job Object'e konur (KILL_ON_JOB_CLOSE: op4.exe ölürse
// motor da ölür; bellekSiniriBayt > 0 ise JOB_OBJECT_LIMIT_PROCESS_MEMORY) ve sonra sürdürülür.
//
// İş parçacığı kuralı: Oku ayrı bir okuyucu iş parçacığından, Yaz ve YazmayiKapat tek bir yazıcı iş parçacığından
// çağrılabilir; Calisiyor / Bekle / Sonlandir her iş parçacığından güvenlidir. Yıkıcıdan önce okuyucu bitmiş olmalıdır.
#include <windows.h>

#include <algorithm>
#include <cstdio>
#include <cwchar>
#include <cwctype>
#include <map>
#include <string>
#include <vector>

#include "platform/surec.h"

namespace op4 {
namespace {

std::wstring Genis(const std::string& s) {
    if (s.empty()) return {};
    const int n = MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), nullptr, 0);
    std::wstring w(static_cast<size_t>(n), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), w.data(), n);
    return w;
}

std::string Utf8(const std::wstring& w) {
    if (w.empty()) return {};
    const int n = WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), nullptr, 0, nullptr, nullptr);
    std::string s(static_cast<size_t>(n), '\0');
    WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), s.data(), n, nullptr, nullptr);
    return s;
}

std::string SonHata(const char* ne) {
    const DWORD e = GetLastError();
    wchar_t* b = nullptr;
    FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, nullptr, e, 0,
                   reinterpret_cast<wchar_t*>(&b), 0, nullptr);
    std::wstring m = b ? b : L"";
    if (b) LocalFree(b);
    while (!m.empty() && (m.back() == L'\r' || m.back() == L'\n' || m.back() == L' ')) m.pop_back();
    char kod[32];
    std::snprintf(kod, sizeof(kod), " (Windows hata %lu)", static_cast<unsigned long>(e));
    return std::string(ne) + ": " + Utf8(m) + kod;
}

void Kapat(HANDLE& h) {
    if (h && h != INVALID_HANDLE_VALUE) CloseHandle(h);
    h = nullptr;
}

// CommandLineToArgvW / MSVC CRT kuralıyla tırnaklama.
void ArgumanEkle(std::wstring& satir, const std::wstring& a) {
    if (!satir.empty()) satir += L' ';
    if (!a.empty() && a.find_first_of(L" \t\n\v\"") == std::wstring::npos) {
        satir += a;
        return;
    }
    satir += L'"';
    size_t ters = 0;
    for (const wchar_t c : a) {
        if (c == L'\\') {
            ++ters;
            continue;
        }
        if (c == L'"') satir.append(ters * 2 + 1, L'\\');
        else satir.append(ters, L'\\');
        ters = 0;
        satir += c;
    }
    satir.append(ters * 2, L'\\');
    satir += L'"';
}

std::wstring Buyuk(std::wstring s) {
    for (wchar_t& c : s) c = static_cast<wchar_t>(std::towupper(c));
    return s;
}

// Üst sürecin ortamı + değişiklikler → CREATE_UNICODE_ENVIRONMENT bloğu (anahtarlar büyük harf duyarsız, sıralı).
std::wstring OrtamBlogu(const std::vector<std::pair<std::string, std::string>>& degisiklikler) {
    std::map<std::wstring, std::wstring> m;  // BÜYÜK ad → "Ad=değer"
    if (wchar_t* e = GetEnvironmentStringsW()) {
        for (const wchar_t* p = e; *p; p += wcslen(p) + 1) {
            const std::wstring s(p);
            const size_t esit = s.find(L'=', 1);  // "=C:=C:\..." biçimli girdiler '=' ile başlar
            m[Buyuk(s.substr(0, esit))] = s;
        }
        FreeEnvironmentStringsW(e);
    }
    for (const auto& [k, v] : degisiklikler) {
        const std::wstring ad = Genis(k);
        m[Buyuk(ad)] = ad + L"=" + Genis(v);
    }
    std::wstring blok;
    for (const auto& [ad, girdi] : m) {
        blok += girdi;
        blok += L'\0';
    }
    blok += L'\0';
    return blok;
}

class WinSurec final : public Surec {
public:
    ~WinSurec() override {
        if (surec_) {
            if (WaitForSingleObject(surec_, 0) == WAIT_TIMEOUT) TerminateProcess(surec_, 1);
            WaitForSingleObject(surec_, 5000);
        }
        Kapat(yaz_);
        Kapat(oku_);
        Kapat(surec_);
        Kapat(is_);  // KILL_ON_JOB_CLOSE
    }

    bool Baslat(const SurecAyari& a, std::string& hata) override {
        if (surec_) {
            hata = "süreç zaten başlatıldı";
            return false;
        }
        if (a.program.empty()) {
            hata = "program yolu boş";
            return false;
        }
        const std::wstring program = Genis(a.program);
        const bool yolVar = program.find_first_of(L"\\/") != std::wstring::npos;
        if (yolVar && GetFileAttributesW(program.c_str()) == INVALID_FILE_ATTRIBUTES) {
            hata = "program bulunamadı: " + a.program;
            return false;
        }
        SECURITY_ATTRIBUTES sa{sizeof(sa), nullptr, TRUE};
        HANDLE istekOku = nullptr, istekYaz = nullptr, yanitOku = nullptr, yanitYaz = nullptr, nul = nullptr,
               cikti = nullptr;
        auto temizle = [&] {
            Kapat(istekOku);
            Kapat(istekYaz);
            Kapat(yanitOku);
            Kapat(yanitYaz);
            Kapat(nul);
            Kapat(cikti);
        };
        if (!CreatePipe(&istekOku, &istekYaz, &sa, 1u << 16) || !CreatePipe(&yanitOku, &yanitYaz, &sa, 1u << 20)) {
            hata = SonHata("CreatePipe");
            temizle();
            return false;
        }
        // Üst sürecin uçları miras alınmaz.
        SetHandleInformation(istekYaz, HANDLE_FLAG_INHERIT, 0);
        SetHandleInformation(yanitOku, HANDLE_FLAG_INHERIT, 0);
        nul = CreateFileW(L"NUL", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, &sa, OPEN_EXISTING, 0,
                          nullptr);
        if (!a.ciktiDosyasi.empty())
            cikti = CreateFileW(Genis(a.ciktiDosyasi).c_str(), FILE_APPEND_DATA | SYNCHRONIZE,
                                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, &sa, OPEN_ALWAYS,
                                FILE_ATTRIBUTE_NORMAL, nullptr);
        if (cikti == INVALID_HANDLE_VALUE) cikti = nullptr;
        if (nul == INVALID_HANDLE_VALUE) nul = nullptr;
        HANDLE ciktiH = cikti ? cikti : nul;

        std::vector<HANDLE> miras = {istekOku, yanitYaz};
        if (nul) miras.push_back(nul);
        if (cikti) miras.push_back(cikti);
        SIZE_T boyut = 0;
        InitializeProcThreadAttributeList(nullptr, 1, 0, &boyut);
        std::vector<unsigned char> liste(boyut);
        auto* ozn = reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(liste.data());
        if (!InitializeProcThreadAttributeList(ozn, 1, 0, &boyut) ||
            !UpdateProcThreadAttribute(ozn, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST, miras.data(), miras.size() * sizeof(HANDLE),
                                       nullptr, nullptr)) {
            hata = SonHata("PROC_THREAD_ATTRIBUTE_HANDLE_LIST");
            temizle();
            return false;
        }
        STARTUPINFOEXW si{};
        si.StartupInfo.cb = sizeof(si);
        si.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
        si.StartupInfo.hStdInput = nul;
        si.StartupInfo.hStdOutput = ciktiH;
        si.StartupInfo.hStdError = ciktiH;
        si.lpAttributeList = ozn;

        const std::wstring hIstek = std::to_wstring(reinterpret_cast<uintptr_t>(istekOku));
        const std::wstring hYanit = std::to_wstring(reinterpret_cast<uintptr_t>(yanitYaz));
        std::wstring satir;
        ArgumanEkle(satir, program);
        for (const std::string& s : a.argumanlar) {
            std::wstring w = Genis(s);
            for (size_t i = w.find(L"{istek}"); i != std::wstring::npos; i = w.find(L"{istek}", i)) w.replace(i, 7, hIstek);
            for (size_t i = w.find(L"{yanit}"); i != std::wstring::npos; i = w.find(L"{yanit}", i)) w.replace(i, 7, hYanit);
            ArgumanEkle(satir, w);
        }
        std::wstring ortam = OrtamBlogu(a.ortam);
        const std::wstring dizin = Genis(a.calismaDizini);

        PROCESS_INFORMATION pi{};
        const DWORD bayrak = CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT | CREATE_SUSPENDED;
        const BOOL tamam = CreateProcessW(yolVar ? program.c_str() : nullptr, satir.data(), nullptr, nullptr, TRUE, bayrak,
                                          ortam.data(), dizin.empty() ? nullptr : dizin.c_str(), &si.StartupInfo, &pi);
        DeleteProcThreadAttributeList(ozn);
        if (!tamam) {
            hata = SonHata(("süreç başlatılamadı (" + a.program + ")").c_str());
            temizle();
            return false;
        }
        // Job Object: op4.exe kapanınca / çökünce motor da kapanır; isteğe bağlı bellek tavanı (MIMARI §8.4).
        is_ = CreateJobObjectW(nullptr, nullptr);
        if (is_) {
            JOBOBJECT_EXTENDED_LIMIT_INFORMATION li{};
            li.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            if (a.bellekSiniriBayt > 0) {
                li.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_PROCESS_MEMORY;
                li.ProcessMemoryLimit = static_cast<SIZE_T>(a.bellekSiniriBayt);
            }
            if (!SetInformationJobObject(is_, JobObjectExtendedLimitInformation, &li, sizeof(li)) ||
                !AssignProcessToJobObject(is_, pi.hProcess))
                Kapat(is_);  // iç içe iş desteklenmiyorsa süreç işsiz çalışır
        }
        ResumeThread(pi.hThread);
        CloseHandle(pi.hThread);
        surec_ = pi.hProcess;
        pid_ = pi.dwProcessId;
        // Çocuğun uçları üst süreçte kapatılır: çocuk bitince Oku 0 döner, Yaz başarısız olur.
        Kapat(istekOku);
        Kapat(yanitYaz);
        Kapat(nul);
        Kapat(cikti);
        yaz_ = istekYaz;
        oku_ = yanitOku;
        return true;
    }

    bool Yaz(const void* veri, size_t boyut) override {
        const char* p = static_cast<const char*>(veri);
        while (boyut > 0) {
            if (!yaz_) return false;
            DWORD n = 0;
            const DWORD parca = static_cast<DWORD>(std::min<size_t>(boyut, 1u << 20));
            if (!WriteFile(yaz_, p, parca, &n, nullptr)) return false;
            p += n;
            boyut -= n;
        }
        return true;
    }

    long long Oku(void* tampon, size_t boyut) override {
        for (;;) {
            if (!oku_) return -1;
            DWORD n = 0;
            if (!ReadFile(oku_, tampon, static_cast<DWORD>(std::min<size_t>(boyut, 1u << 24)), &n, nullptr))
                return GetLastError() == ERROR_BROKEN_PIPE ? 0 : -1;
            if (n > 0) return static_cast<long long>(n);
        }
    }

    void YazmayiKapat() override { Kapat(yaz_); }

    bool Calisiyor() const override { return surec_ && WaitForSingleObject(surec_, 0) == WAIT_TIMEOUT; }

    bool Bekle(uint32_t ms, int& cikisKodu) override {
        if (!surec_) {
            cikisKodu = -1;
            return true;
        }
        if (WaitForSingleObject(surec_, ms) != WAIT_OBJECT_0) return false;
        DWORD kod = 0;
        GetExitCodeProcess(surec_, &kod);
        cikisKodu = static_cast<int>(kod);
        return true;
    }

    void Sonlandir() override {
        if (surec_ && WaitForSingleObject(surec_, 0) == WAIT_TIMEOUT) TerminateProcess(surec_, 1);
    }

    long long Kimlik() const override { return static_cast<long long>(pid_); }

private:
    HANDLE surec_ = nullptr;
    HANDLE is_ = nullptr;
    HANDLE yaz_ = nullptr;
    HANDLE oku_ = nullptr;
    DWORD pid_ = 0;
};

}  // namespace

std::unique_ptr<Surec> SurecOlustur() { return std::make_unique<WinSurec>(); }

}  // namespace op4
