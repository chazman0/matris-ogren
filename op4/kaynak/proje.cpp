#include "proje.h"

#include <shobjidl.h>
#include <wrl/client.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>

#include "gunluk.h"

namespace op4 {
namespace {

std::string DosyaOku(const std::wstring& yol, bool& tamam) {
    tamam = false;
    HANDLE h = CreateFileW(yol.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, 0, nullptr);
    if (h == INVALID_HANDLE_VALUE) return {};
    LARGE_INTEGER boy{};
    GetFileSizeEx(h, &boy);
    std::string s(static_cast<size_t>(boy.QuadPart), '\0');
    DWORD okunan = 0;
    tamam = ReadFile(h, s.data(), static_cast<DWORD>(s.size()), &okunan, nullptr) && okunan == s.size();
    CloseHandle(h);
    return s;
}

// Basit anahtar okuyucu: "anahtar": sayı | true | false  (iskelet biçimi için yeterli; tam JSON sonraki adımda).
bool Sayi(const std::string& s, const char* anahtar, float& v) {
    std::string a = std::string("\"") + anahtar + "\"";
    size_t i = s.find(a);
    if (i == std::string::npos) return false;
    i = s.find(':', i + a.size());
    if (i == std::string::npos) return false;
    const char* p = s.c_str() + i + 1;
    while (*p == ' ' || *p == '[') ++p;
    char* son = nullptr;
    double d = std::strtod(p, &son);
    if (son == p) return false;
    v = static_cast<float>(d);
    return true;
}

bool Dizi3(const std::string& s, const char* anahtar, V3& v) {
    std::string a = std::string("\"") + anahtar + "\"";
    size_t i = s.find(a);
    if (i == std::string::npos) return false;
    i = s.find('[', i);
    if (i == std::string::npos) return false;
    float x, y, z;
    if (std::sscanf(s.c_str() + i, "[%f , %f , %f", &x, &y, &z) != 3) return false;
    v = {x, y, z};
    return true;
}

bool Mantik(const std::string& s, const char* anahtar, bool& v) {
    std::string a = std::string("\"") + anahtar + "\"";
    size_t i = s.find(a);
    if (i == std::string::npos) return false;
    i = s.find(':', i);
    if (i == std::string::npos) return false;
    size_t j = s.find_first_not_of(" \t\r\n", i + 1);
    if (j == std::string::npos) return false;
    v = s.compare(j, 4, "true") == 0;
    return true;
}

}  // namespace

bool ProjeKaydet(const std::wstring& yol, const Proje& p, std::string& hata) {
    std::time_t t = std::time(nullptr);
    std::tm yerel{};
    localtime_s(&yerel, &t);
    char zaman[32];
    std::strftime(zaman, sizeof(zaman), "%Y-%m-%dT%H:%M:%S", &yerel);
    const Kamera& k = p.kamera;
    char b[1024];
    std::snprintf(b, sizeof(b),
                  "{\n"
                  "  \"bicim\": \"op4-proje\",\n"
                  "  \"bicim_surumu\": 1,\n"
                  "  \"uygulama\": \"op4 %s\",\n"
                  "  \"kaydedildi\": \"%s\",\n"
                  "  \"kamera\": {\"hedef\": [%.6f, %.6f, %.6f], \"uzaklik\": %.6f, \"sapma\": %.6f, \"egim\": %.6f},\n"
                  "  \"gorunum\": {\"kesit\": %s, \"kenarlar\": %s, \"izgara\": %s},\n"
                  "  \"model\": {\"surum\": 3, \"dugumler\": [], \"cubuklar\": [], \"paneller\": [], \"mesnetler\": []}\n"
                  "}\n",
                  OP4_SURUM, zaman, k.hedef.x, k.hedef.y, k.hedef.z, k.uzaklik, k.sapma, k.egim,
                  p.ayar.kesitGorunumu ? "true" : "false", p.ayar.kenarlar ? "true" : "false",
                  p.ayar.izgara ? "true" : "false");
    // Önce geçici dosyaya yaz, sonra yerine taşı: yazma yarıda kalırsa eski dosya bozulmaz.
    std::wstring gecici = yol + L".yaziliyor";
    HANDLE h = CreateFileW(gecici.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (h == INVALID_HANDLE_VALUE) {
        hata = "dosya yazılamadı: " + Utf8(yol);
        return false;
    }
    DWORD yazilan = 0;
    BOOL tamam = WriteFile(h, b, static_cast<DWORD>(std::strlen(b)), &yazilan, nullptr);
    FlushFileBuffers(h);
    CloseHandle(h);
    if (!tamam || !MoveFileExW(gecici.c_str(), yol.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        DeleteFileW(gecici.c_str());
        hata = "dosya yazılamadı: " + Utf8(yol);
        return false;
    }
    return true;
}

bool ProjeAc(const std::wstring& yol, Proje& p, std::string& hata) {
    bool tamam = false;
    std::string s = DosyaOku(yol, tamam);
    if (!tamam) {
        hata = "dosya okunamadı: " + Utf8(yol);
        return false;
    }
    if (s.find("\"op4-proje\"") == std::string::npos) {
        hata = "op4 proje dosyası değil: " + Utf8(yol);
        return false;
    }
    Proje y;
    y.yol = yol;
    Dizi3(s, "hedef", y.kamera.hedef);
    Sayi(s, "uzaklik", y.kamera.uzaklik);
    Sayi(s, "sapma", y.kamera.sapma);
    Sayi(s, "egim", y.kamera.egim);
    Mantik(s, "kesit", y.ayar.kesitGorunumu);
    Mantik(s, "kenarlar", y.ayar.kenarlar);
    Mantik(s, "izgara", y.ayar.izgara);
    p = y;
    return true;
}

bool DosyaSec(HWND sahip, bool kaydet, const std::wstring& oneri, std::wstring& yol) {
    using Microsoft::WRL::ComPtr;
    ComPtr<IFileDialog> d;
    HRESULT hr = CoCreateInstance(kaydet ? CLSID_FileSaveDialog : CLSID_FileOpenDialog, nullptr, CLSCTX_INPROC_SERVER,
                                  IID_PPV_ARGS(d.GetAddressOf()));
    if (FAILED(hr)) return false;
    const COMDLG_FILTERSPEC turler[] = {{L"op4 projesi (*.op4)", L"*.op4"}, {L"Tüm dosyalar", L"*.*"}};
    d->SetFileTypes(2, turler);
    d->SetDefaultExtension(L"op4");
    d->SetTitle(kaydet ? L"Projeyi kaydet" : L"Proje aç");
    if (!oneri.empty()) d->SetFileName(oneri.c_str());
    if (FAILED(d->Show(sahip))) return false;
    ComPtr<IShellItem> oge;
    if (FAILED(d->GetResult(oge.GetAddressOf()))) return false;
    PWSTR p = nullptr;
    if (FAILED(oge->GetDisplayName(SIGDN_FILESYSPATH, &p))) return false;
    yol = p;
    CoTaskMemFree(p);
    return true;
}

}  // namespace op4
