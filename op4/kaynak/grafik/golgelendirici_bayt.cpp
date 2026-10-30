// op4 grafik — derlemede üretilmiş gölgelendirici bayt kodu (sözleşme S25; F1 iş 1.1, kabul A4). Sahibi: A.
//
// Bayt kodu cmake/Golgelendiriciler.cmake'in ürettiği golgelendirici_gomulu.cpp tablosundadır (FXC, SM 5.1). Tablo boşsa
// (fxc yok) ya da giriş adı tabloda yoksa boş dönülür; grafik.cpp çalışma anında derler. Geliştirici kipinde
// (--golgelendirici-dizini) <klasör>\op4.hlsl çalışma anında derlenir (golgelendirici_bayt_gelistirme.h).
#include <windows.h>
#include <d3dcompiler.h>
#include <wrl/client.h>

#include <cstring>
#include <map>
#include <mutex>
#include <string>

#include "grafik/golgelendirici_bayt.h"
#include "grafik/golgelendirici_bayt_gelistirme.h"
#include "gunluk.h"

namespace op4 {
namespace golgelendirici_gomulu {
struct Girdi {
    const char* ad;
    const void* veri;
    size_t boyut;
};
extern const Girdi kGirdiler[];
extern const size_t kGirdiSayisi;
}  // namespace golgelendirici_gomulu

namespace {

std::mutex g_kilit;
std::wstring g_dizin;
std::map<std::string, Microsoft::WRL::ComPtr<ID3DBlob>> g_gelistirme;
bool g_yazildi = false;

void BirKezYaz() {
    if (g_yazildi) return;
    g_yazildi = true;
    if (!g_dizin.empty()) {
        Gunluk("Gölgelendiriciler: geliştirici kipi — %s\\op4.hlsl çalışma anında derlenir", Utf8(g_dizin).c_str());
        return;
    }
    size_t bayt = 0;
    for (size_t i = 0; i < golgelendirici_gomulu::kGirdiSayisi; ++i) bayt += golgelendirici_gomulu::kGirdiler[i].boyut;
    if (golgelendirici_gomulu::kGirdiSayisi > 0)
        Gunluk("Gölgelendiriciler: gömülü bayt kodu (FXC, SM 5.1; %zu giriş noktası, %zu bayt) — çalışma anı derlemesi yok",
               golgelendirici_gomulu::kGirdiSayisi, bayt);
    else
        Gunluk("Gölgelendiriciler: gömülü bayt kodu yok (derlemede fxc bulunamadı) — çalışma anında derlenecek");
}

GolgelendiriciBayt GelistirmeDerle(const char* giris) {
    auto it = g_gelistirme.find(giris);
    if (it == g_gelistirme.end()) {
        const std::wstring yol = g_dizin + L"\\op4.hlsl";
        const std::string hedef = std::string(giris).substr(0, 2) + "_5_1";
        Microsoft::WRL::ComPtr<ID3DBlob> kod, hatalar;
        const HRESULT hr = D3DCompileFromFile(yol.c_str(), nullptr, D3D_COMPILE_STANDARD_FILE_INCLUDE, giris, hedef.c_str(),
                                              D3DCOMPILE_DEBUG | D3DCOMPILE_SKIP_OPTIMIZATION, 0, kod.GetAddressOf(),
                                              hatalar.GetAddressOf());
        if (FAILED(hr)) {
            Gunluk("HATA: geliştirici gölgelendiricisi derlenemedi (%s, %s): %s", Utf8(yol).c_str(), giris,
                   hatalar ? std::string(static_cast<const char*>(hatalar->GetBufferPointer()), hatalar->GetBufferSize()).c_str()
                           : "dosya okunamadı");
            kod.Reset();
        }
        it = g_gelistirme.emplace(giris, kod).first;
    }
    if (!it->second) return {};
    return {it->second->GetBufferPointer(), it->second->GetBufferSize()};
}

}  // namespace

void GolgelendiriciDiziniAyarla(const std::wstring& dizin) {
    std::lock_guard<std::mutex> k(g_kilit);
    g_dizin = dizin;
    while (!g_dizin.empty() && (g_dizin.back() == L'\\' || g_dizin.back() == L'/')) g_dizin.pop_back();
    g_gelistirme.clear();
    g_yazildi = false;
}

GolgelendiriciBayt GomuluGolgelendirici(const char* giris) {
    std::lock_guard<std::mutex> k(g_kilit);
    BirKezYaz();
    if (!giris) return {};
    if (!g_dizin.empty()) return GelistirmeDerle(giris);
    for (size_t i = 0; i < golgelendirici_gomulu::kGirdiSayisi; ++i)
        if (std::strcmp(golgelendirici_gomulu::kGirdiler[i].ad, giris) == 0)
            return {golgelendirici_gomulu::kGirdiler[i].veri, golgelendirici_gomulu::kGirdiler[i].boyut};
    return {};
}

}  // namespace op4
