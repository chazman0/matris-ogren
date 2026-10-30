// op4 platform — dosya sistemi, taşınabilir uygulama (std::filesystem). Sözleşme S17. Sahibi: D (dosya-cozum); Windows'a
// özgü sağlamlaştırma (ReplaceFileW, yeniden deneme) dosya_sistemi_win.cpp'ye taşınacak (F1 iş 1.6).
#include "platform/dosya_sistemi.h"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <system_error>

namespace op4 {
namespace fs = std::filesystem;
namespace {

fs::path Yol(const std::string& utf8) {
    return fs::path(std::u8string(reinterpret_cast<const char8_t*>(utf8.data()), utf8.size()));
}

std::string Utf8(const fs::path& p) {
    const std::u8string s = p.u8string();
    return std::string(reinterpret_cast<const char*>(s.data()), s.size());
}

std::string Ortam(const char* ad) {
#if defined(_MSC_VER)
    char* d = nullptr;
    size_t n = 0;
    std::string s;
    if (_dupenv_s(&d, &n, ad) == 0 && d) s = d;
    std::free(d);
    return s;
#else
    const char* d = std::getenv(ad);
    return d ? std::string(d) : std::string();
#endif
}

}  // namespace

bool AtomikYaz(const std::string& yol, std::string_view veri, bool bak, std::string& hata) {
    const fs::path hedef = Yol(yol);
    fs::path gecici = hedef;
    gecici += ".op4-yaziliyor";
    {
        std::ofstream f(gecici, std::ios::binary | std::ios::trunc);
        if (!f) {
            hata = "Geçici dosya açılamadı: " + Utf8(gecici);
            return false;
        }
        f.write(veri.data(), static_cast<std::streamsize>(veri.size()));
        f.flush();
        if (!f) {
            hata = "Yazılamadı (disk dolu olabilir): " + Utf8(gecici);
            std::error_code e;
            fs::remove(gecici, e);
            return false;
        }
    }
    std::error_code e;
    if (bak && fs::exists(hedef, e)) {
        fs::path b = hedef;
        b += ".bak";
        fs::copy_file(hedef, b, fs::copy_options::overwrite_existing, e);
    }
    fs::rename(gecici, hedef, e);
    if (e) {
        hata = "Dosya yerine konamadı: " + yol + " (" + e.message() + ")";
        fs::remove(gecici, e);
        return false;
    }
    return true;
}

bool DosyaOku(const std::string& yol, std::string& veri, std::string& hata, size_t enFazlaBayt) {
    std::ifstream f(Yol(yol), std::ios::binary);
    if (!f) {
        hata = "Dosya açılamadı: " + yol;
        return false;
    }
    f.seekg(0, std::ios::end);
    const auto boyut = static_cast<long long>(f.tellg());
    if (boyut < 0 || static_cast<unsigned long long>(boyut) > enFazlaBayt) {
        hata = "Dosya çok büyük ya da okunamıyor: " + yol;
        return false;
    }
    f.seekg(0, std::ios::beg);
    veri.resize(static_cast<size_t>(boyut));
    if (boyut > 0) f.read(veri.data(), boyut);
    if (!f) {
        hata = "Dosya okunamadı: " + yol;
        return false;
    }
    return true;
}

bool DosyaVar(const std::string& yol) {
    std::error_code e;
    return fs::is_regular_file(Yol(yol), e);
}

bool DizinKur(const std::string& yol) {
    std::error_code e;
    fs::create_directories(Yol(yol), e);
    return fs::is_directory(Yol(yol), e);
}

bool DosyaSil(const std::string& yol) {
    std::error_code e;
    return fs::remove(Yol(yol), e);
}

KullaniciDizinleri KullaniciDizinleriniBul(bool olusturmak) {
    KullaniciDizinleri d;
    const std::string kok = Ortam("OP4_KULLANICI_DIZINI");
    if (!kok.empty()) {
        d.ayarlar = Utf8(Yol(kok) / "ayarlar");
        d.yerel = Utf8(Yol(kok) / "yerel");
    } else {
#if defined(_WIN32)
        const std::string ad = Ortam("APPDATA"), yerel = Ortam("LOCALAPPDATA");
        d.ayarlar = Utf8(Yol(ad.empty() ? "." : ad) / "Opus Fortis" / "op4");
        d.yerel = Utf8(Yol(yerel.empty() ? "." : yerel) / "Opus Fortis" / "op4");
#else
        const std::string ev = Ortam("HOME");
        const std::string ayar = Ortam("XDG_CONFIG_HOME"), veri = Ortam("XDG_DATA_HOME");
        d.ayarlar = Utf8((ayar.empty() ? Yol(ev) / ".config" : Yol(ayar)) / "opus-fortis" / "op4");
        d.yerel = Utf8((veri.empty() ? Yol(ev) / ".local" / "share" : Yol(veri)) / "opus-fortis" / "op4");
#endif
    }
    d.kurtarma = Utf8(Yol(d.yerel) / "kurtarma");
    d.gunluk = Utf8(Yol(d.yerel) / "gunluk");
    d.cokme = Utf8(Yol(d.yerel) / "cokme");
    d.gecici = Utf8(Yol(d.yerel) / "gecici");
    if (olusturmak)
        for (const std::string* y : {&d.ayarlar, &d.yerel, &d.kurtarma, &d.gunluk, &d.cokme, &d.gecici}) DizinKur(*y);
    return d;
}

}  // namespace op4
