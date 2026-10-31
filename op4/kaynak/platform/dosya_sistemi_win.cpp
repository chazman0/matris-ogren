// op4 platform — atomik yazma işlemleri ve kilitler, Win32 (MIMARI §13.2, D23). Sahibi: D (dosya-cozum).
//
// Geçici dosya: CreateFileW(CREATE_NEW) → WriteFile → FlushFileBuffers → CloseHandle (tanıtıcı kapanmadan yerine konmaz).
// Yerine koyma: hedef varsa ReplaceFileW (öznitelikler, ACL, oluşturma zamanı ve eşitleme istemcisinin dosya kimliği
// korunur; isteğe bağlı .bak), yoksa MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH). Paylaşım ihlali, kilit ihlali,
// eşlenmiş dosya ve ReplaceFileW'nin "yerine konan kaldırılamadı / taşınamadı" hataları GEÇİCİ sayılır (algoritma 5 × 100 ms
// yeniden dener). ERROR_UNABLE_TO_MOVE_REPLACEMENT_2'de asıl dosya yedek adına taşınmış olabilir: geri alınır.
// Uzun yollar (≥ 248 karakter) "\\?\" önekiyle açılır.
#include <windows.h>

#include <algorithm>
#include <string>

#include "platform/dosya_sistemi_atomik.h"

#ifndef REPLACEFILE_IGNORE_MERGE_ERRORS
#define REPLACEFILE_IGNORE_MERGE_ERRORS 0x00000002
#endif
#ifndef REPLACEFILE_IGNORE_ACL_ERRORS
#define REPLACEFILE_IGNORE_ACL_ERRORS 0x00000004
#endif

namespace op4 {
namespace {

std::wstring Genis(const std::string& s) {
    if (s.empty()) return {};
    const int n = MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), nullptr, 0);
    std::wstring w(static_cast<size_t>(n), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), w.data(), n);
    return w;
}

std::string Dar(const std::wstring& w) {
    if (w.empty()) return {};
    const int n = WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), nullptr, 0, nullptr, nullptr);
    std::string s(static_cast<size_t>(n), '\0');
    WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), s.data(), n, nullptr, nullptr);
    return s;
}

// UTF-8 → Win32 yolu; uzun mutlak yollar için \\?\ öneki (eğik çizgiler ters çevrilir).
std::wstring WinYolu(const std::string& utf8) {
    std::wstring w = Genis(utf8);
    if (w.size() < 248 || w.rfind(L"\\\\?\\", 0) == 0) return w;
    for (wchar_t& c : w)
        if (c == L'/') c = L'\\';
    if (w.size() > 2 && w[1] == L':') return L"\\\\?\\" + w;
    if (w.rfind(L"\\\\", 0) == 0) return L"\\\\?\\UNC\\" + w.substr(2);
    return w;
}

std::string SistemIletisi(DWORD kod) {
    switch (kod) {
        case ERROR_DISK_FULL:
        case ERROR_HANDLE_DISK_FULL: return "disk dolu";
        case ERROR_ACCESS_DENIED: return "erişim reddedildi (klasöre yazma izni yok ya da dosya salt okunur)";
        case ERROR_PATH_NOT_FOUND: return "klasör bulunamadı";
        case ERROR_FILE_NOT_FOUND: return "dosya bulunamadı";
        case ERROR_WRITE_PROTECT: return "ortam yazmaya karşı korumalı";
        case ERROR_FILENAME_EXCED_RANGE: return "yol çok uzun";
        default: break;
    }
    wchar_t* t = nullptr;
    const DWORD n = FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
                                   nullptr, kod, 0, reinterpret_cast<LPWSTR>(&t), 0, nullptr);
    std::wstring w = n && t ? std::wstring(t, n) : std::wstring();
    if (t) LocalFree(t);
    while (!w.empty() && (w.back() == L'\r' || w.back() == L'\n' || w.back() == L' ' || w.back() == L'.')) w.pop_back();
    return "Windows hatası " + std::to_string(kod) + (w.empty() ? "" : ": " + Dar(w));
}

bool GeciciDurumMu(DWORD kod) {
    switch (kod) {
        case ERROR_SHARING_VIOLATION:
        case ERROR_LOCK_VIOLATION:
        case ERROR_USER_MAPPED_FILE:
        case ERROR_UNABLE_TO_REMOVE_REPLACED:
        case ERROR_UNABLE_TO_MOVE_REPLACEMENT:
        case ERROR_ACCESS_DENIED:  // eşitleme istemcileri ve bekleyen silme kısa süre bunu verir
            return true;
        default:
            return false;
    }
}

bool GeciciYaz(const std::string& gecici, std::string_view veri, std::string& hata) {
    const std::wstring y = WinYolu(gecici);
    HANDLE h = CreateFileW(y.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (h == INVALID_HANDLE_VALUE) {
        hata = "Geçici dosya oluşturulamadı (" + SistemIletisi(GetLastError()) + "): " + gecici;
        return false;
    }
    size_t yazilan = 0;
    while (yazilan < veri.size()) {
        const DWORD parca = static_cast<DWORD>(std::min<size_t>(veri.size() - yazilan, size_t{1} << 26));
        DWORD n = 0;
        if (!WriteFile(h, veri.data() + yazilan, parca, &n, nullptr) || n == 0) {
            hata = "Yazılamadı (" + SistemIletisi(GetLastError()) + "): " + gecici;
            CloseHandle(h);
            return false;
        }
        yazilan += n;
    }
    if (!FlushFileBuffers(h)) {
        hata = "Diske boşaltılamadı (" + SistemIletisi(GetLastError()) + "): " + gecici;
        CloseHandle(h);
        return false;
    }
    if (!CloseHandle(h)) {
        hata = "Geçici dosya kapatılamadı (" + SistemIletisi(GetLastError()) + "): " + gecici;
        return false;
    }
    return true;
}

YerineKoymaSonucu YerineKoy(const std::string& gecici, const std::string& hedef, bool bak, std::string& hata) {
    const std::wstring g = WinYolu(gecici), h = WinYolu(hedef), b = WinYolu(hedef + ".bak");
    const DWORD oz = GetFileAttributesW(h.c_str());
    if (oz == INVALID_FILE_ATTRIBUTES) {
        if (MoveFileExW(g.c_str(), h.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
            return YerineKoymaSonucu::Tamam;
        const DWORD k = GetLastError();
        if (GeciciDurumMu(k)) return YerineKoymaSonucu::PaylasimIhlali;
        hata = "Dosya yerine konamadı (" + SistemIletisi(k) + "): " + hedef + ".";
        return YerineKoymaSonucu::Hata;
    }
    if (oz & FILE_ATTRIBUTE_READONLY) {
        hata = "Dosya salt okunur işaretli: " + hedef + ". Özelliklerden salt okunurluğu kaldırın ya da Farklı kaydet'i "
               "kullanın.";
        return YerineKoymaSonucu::Hata;
    }
    if (bak) DeleteFileW(b.c_str());
    if (ReplaceFileW(h.c_str(), g.c_str(), bak ? b.c_str() : nullptr,
                     REPLACEFILE_IGNORE_MERGE_ERRORS | REPLACEFILE_IGNORE_ACL_ERRORS, nullptr, nullptr))
        return YerineKoymaSonucu::Tamam;
    const DWORD k = GetLastError();
    if (k == ERROR_UNABLE_TO_MOVE_REPLACEMENT_2) {
        // Asıl dosya yedek adına taşındı ama yenisi yerine konamadı: asıl dosyayı geri getir, sonra yeniden dene.
        if (bak) MoveFileExW(b.c_str(), h.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
        return YerineKoymaSonucu::PaylasimIhlali;
    }
    if (GeciciDurumMu(k)) return YerineKoymaSonucu::PaylasimIhlali;
    hata = "Dosya yerine konamadı (" + SistemIletisi(k) + "): " + hedef + ".";
    return YerineKoymaSonucu::Hata;
}

}  // namespace

const AtomikYazmaIslemleri& PlatformAtomikIslemleri() {
    static const AtomikYazmaIslemleri is{
        &GeciciYaz,
        &YerineKoy,
        [](int ms) { Sleep(static_cast<DWORD>(ms)); },
        [](const std::string& yol) { DeleteFileW(WinYolu(yol).c_str()); },
    };
    return is;
}

uint32_t SurecNo() { return static_cast<uint32_t>(GetCurrentProcessId()); }

// ---- oturum kilidi: paylaşımsız, kapanınca silinen dosya -------------------------------------------------------------
struct OturumKilidi::Ic {
    HANDLE h = INVALID_HANDLE_VALUE;
};

OturumKilidi::OturumKilidi() : ic_(std::make_unique<Ic>()) {}
OturumKilidi::~OturumKilidi() { Birak(); }

bool OturumKilidi::Al(const std::string& yol) {
    Birak();
    ic_->h = CreateFileW(WinYolu(yol).c_str(), GENERIC_READ | GENERIC_WRITE | DELETE, 0, nullptr, OPEN_ALWAYS,
                         FILE_ATTRIBUTE_HIDDEN | FILE_FLAG_DELETE_ON_CLOSE, nullptr);
    return ic_->h != INVALID_HANDLE_VALUE;
}

void OturumKilidi::Birak() {
    if (ic_->h == INVALID_HANDLE_VALUE) return;
    CloseHandle(ic_->h);  // FILE_FLAG_DELETE_ON_CLOSE: dosya da silinir
    ic_->h = INVALID_HANDLE_VALUE;
}

bool OturumKilidi::Tutuluyor() const { return ic_->h != INVALID_HANDLE_VALUE; }

bool KilitTutuluyorMu(const std::string& yol) {
    const std::wstring y = WinYolu(yol);
    if (GetFileAttributesW(y.c_str()) == INVALID_FILE_ATTRIBUTES) return false;
    HANDLE h = CreateFileW(y.c_str(), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
                           OPEN_EXISTING, 0, nullptr);
    if (h == INVALID_HANDLE_VALUE) return GetLastError() == ERROR_SHARING_VIOLATION;
    CloseHandle(h);
    return false;
}

// ---- proje okuma kilidi: FILE_SHARE_READ ile açık tutulur ------------------------------------------------------------
struct ProjeOkumaKilidi::Ic {
    HANDLE h = INVALID_HANDLE_VALUE;
};

ProjeOkumaKilidi::ProjeOkumaKilidi() : ic_(std::make_unique<Ic>()) {}
ProjeOkumaKilidi::~ProjeOkumaKilidi() { Birak(); }

bool ProjeOkumaKilidi::Ac(const std::string& yol) {
    Birak();
    ic_->h = CreateFileW(WinYolu(yol).c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                         FILE_ATTRIBUTE_NORMAL, nullptr);
    if (ic_->h == INVALID_HANDLE_VALUE) return false;
    yol_ = yol;
    return true;
}

void ProjeOkumaKilidi::Birak() {
    if (ic_->h != INVALID_HANDLE_VALUE) CloseHandle(ic_->h);
    ic_->h = INVALID_HANDLE_VALUE;
    yol_.clear();
}

}  // namespace op4
