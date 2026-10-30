// op4 çekirdek — proje dosyası. TASLAK (sözleşme S16): BicimSapta ve SonDosyaEkle tamdır; ZIP okuma / yazma ve kurtarma
// "henüz uygulanmadı" döner. Uygulayan: D (dosya-cozum), F1 iş 1.6.
#include "cekirdek/proje_dosyasi.h"

#include <algorithm>

#include "cekirdek/turkce.h"

namespace op4 {
namespace {

std::string Kucuk(std::string_view s) {
    std::string o(s);
    for (char& c : o)
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    return o;
}

std::string_view BaslangicBosluksuz(std::string_view s) {
    if (s.size() >= 3 && static_cast<unsigned char>(s[0]) == 0xEF && static_cast<unsigned char>(s[1]) == 0xBB &&
        static_cast<unsigned char>(s[2]) == 0xBF)
        s.remove_prefix(3);  // UTF-8 BOM
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t' || s.front() == '\r' || s.front() == '\n')) s.remove_prefix(1);
    return s;
}

}  // namespace

DosyaBicimi BicimSapta(std::string_view ilk, std::string_view uzanti) {
    if (ilk.size() >= 4 && ilk.substr(0, 4) == std::string_view("PK\x03\x04", 4)) return DosyaBicimi::Op4;
    const std::string_view s = BaslangicBosluksuz(ilk);
    if (s.substr(0, 13) == "ISO-10303-21;") return DosyaBicimi::Ifc;
    const std::string u = Kucuk(uzanti);
    if (!s.empty() && s.front() == '{') {
        if (u == ".op4" || u == "op4") return DosyaBicimi::Op4Deneme;
        if (u == ".matris" || u == "matris") return DosyaBicimi::Matris;
        return DosyaBicimi::BinaJson;
    }
    if (u == ".ifc" || u == "ifc") return DosyaBicimi::Ifc;
    return DosyaBicimi::Bilinmiyor;
}

OkumaSonucu ProjeOku(const std::string&) {
    OkumaSonucu s;
    s.hata = "Proje dosyası okuma henüz uygulanmadı (F1 iş 1.6).";
    return s;
}

bool ProjeYaz(const std::string&, const ProjeIcerigi&, const ProjeManifest&, std::string& hata) {
    hata = "Proje dosyası yazma henüz uygulanmadı (F1 iş 1.6).";
    return false;
}

bool ProjeZipKur(const ProjeIcerigi&, const ProjeManifest&, std::string&, std::string& hata) {
    hata = "ZIP yazma henüz uygulanmadı (F1 iş 1.6).";
    return false;
}

OkumaSonucu ProjeZipCoz(std::string_view) {
    OkumaSonucu s;
    s.hata = "ZIP okuma henüz uygulanmadı (F1 iş 1.6).";
    return s;
}

void SonDosyaEkle(std::vector<std::string>& liste, const std::string& yol, size_t enFazla) {
    if (yol.empty()) return;
    const std::string anahtar = TurkceKatla(yol);
    liste.erase(std::remove_if(liste.begin(), liste.end(), [&](const std::string& y) { return TurkceKatla(y) == anahtar; }),
                liste.end());
    liste.insert(liste.begin(), yol);
    if (liste.size() > enFazla) liste.resize(enFazla);
}

std::vector<KurtarmaKaydi> KurtarmaKayitlari(const std::string&) { return {}; }

}  // namespace op4
