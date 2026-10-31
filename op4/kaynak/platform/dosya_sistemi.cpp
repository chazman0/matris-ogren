// op4 platform — dosya sistemi, ortak kısım (sözleşme S17). Sahibi: D (dosya-cozum).
//
// Atomik yazma ALGORİTMASI buradadır (platform işlemlerinden bağımsız; dosya_sistemi_atomik.h). Platform işlemleri:
// dosya_sistemi_win.cpp (CreateFileW + FlushFileBuffers + ReplaceFileW / MoveFileExW, paylaşım ihlali eşlemesi) ve
// dosya_sistemi_posix.cpp (open + fsync + rename + klasör fsync). Okuma, klasör ve kullanıcı dizinleri std::filesystem
// ile taşınabilir yazılmıştır (UTF-8 yollar u8 yolu üzerinden; Windows'ta içeride UTF-16).
#include "platform/dosya_sistemi.h"

#include <atomic>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <system_error>

#include "platform/dosya_sistemi_atomik.h"

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

std::string GeciciDosyaAdi(const std::string& yol) {
    static std::atomic<uint32_t> sayac{0};
    return yol + ".~op4-" + std::to_string(SurecNo()) + "-" + std::to_string(++sayac) + ".tmp";
}

bool AtomikYazIle(const AtomikYazmaIslemleri& is, const std::string& yol, std::string_view veri, bool bak,
                  std::string& hata, const AtomikYazmaAyari& ayar, int* denemeSayisi) {
    if (denemeSayisi) *denemeSayisi = 0;
    if (yol.empty()) {
        hata = "Dosya yolu boş.";
        return false;
    }
    const std::string gecici = GeciciDosyaAdi(yol);
    std::string h;
    if (!is.geciciYaz(gecici, veri, h)) {
        if (is.sil) is.sil(gecici);  // yarım yazılmış geçici kalmasın; hedefe hiç dokunulmadı
        hata = h.empty() ? "Geçici dosya yazılamadı: " + gecici : h;
        return false;
    }
    const int deneme = ayar.deneme < 1 ? 1 : ayar.deneme;
    YerineKoymaSonucu s = YerineKoymaSonucu::Hata;
    for (int i = 0; i < deneme; ++i) {
        if (i > 0 && is.bekle) is.bekle(ayar.aralikMs);
        h.clear();
        s = is.yerineKoy(gecici, yol, bak, h);
        if (denemeSayisi) *denemeSayisi = i + 1;
        if (s != YerineKoymaSonucu::PaylasimIhlali) break;
    }
    if (s == YerineKoymaSonucu::Tamam) return true;
    if (is.sil) is.sil(gecici);
    if (s == YerineKoymaSonucu::PaylasimIhlali)
        hata = "Dosya başka bir program tarafından kullanılıyor (" + std::to_string(deneme) +
               " deneme): " + yol + ". Dosyayı açık tutan programı (eşitleme istemcisi, virüs tarayıcısı, başka bir op4 "
               "penceresi) kapatıp yeniden kaydedin; dosyanın eski hâli değişmedi.";
    else
        hata = (h.empty() ? "Dosya yerine konamadı: " + yol : h) + " Dosyanın eski hâli değişmedi.";
    return false;
}

bool AtomikYaz(const std::string& yol, std::string_view veri, bool bak, std::string& hata) {
    return AtomikYazIle(PlatformAtomikIslemleri(), yol, veri, bak, hata);
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
