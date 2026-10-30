// op4 çekirdek sözleşmesi — proje DOSYASI: .op4 ZIP okuma / yazma, eski biçimler, kurtarma, son dosyalar
// (MIMARI §13; "F1 paket sözleşmeleri" §S16).
//
// Uygulayan: D (dosya-cozum) — kaynak/cekirdek/proje_dosyasi.cpp (miniz ile ZIP; platformdan bağımsız, Linux'ta
// gidiş-dönüş testi) + platform/dosya_sistemi.h (atomik yazma; Win32 ReplaceFileW / MoveFileExW, POSIX rename).
// Windows'a özgü kabuk işleri (IFileDialog, TaskDialog, tek örnek borusu, ilişkilendirme, atlama listesi, çökme dökümü)
// kaynak/dosya/ altındadır ve bu başlığa girmez.
#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include "cekirdek/proje_belgesi.h"

namespace op4 {

enum class DosyaBicimi : uint8_t {
    Bilinmiyor = 0,
    Op4 = 1,          // ZIP, ilk girdi "mimetype" = application/x-op4
    Op4Deneme = 2,    // Faz 0 denemesinin JSON biçimli .op4'ü (ilk bayt '{', "kamera" alanı): kamera alınır, model boş
    BinaJson = 3,     // düz bina JSON'u ({"tur":"bina", …}) — .json
    Matris = 4,       // web sürümünün .matris dışa aktarımı (JSON; bina alanı içinde)
    Ifc = 5,          // "ISO-10303-21;" — içe aktarma Faz 6; Faz 1'de "henüz desteklenmiyor"
};

// İlk baytlara (en az 512 önerilir) ve uzantıya bakarak biçimi saptar. İçerik uzantıya üstün gelir.
DosyaBicimi BicimSapta(std::string_view ilkBaytlar, std::string_view uzanti);

struct ProjeManifest {
    std::string tur = "op4-proje";
    int bicimSurumu = proje_yolu::BICIM_SURUMU;
    std::string uygulamaSurumu;   // "0.1.0"
    std::string kaydedildi;       // ISO 8601 UTC
    std::string motorSurumu;      // web_kopru surum_json "motor" alanı
    std::string modelOzeti;       // "12 kolon, 18 kiriş, 6 döşeme"
};

struct OkumaSonucu {
    bool basarili = false;
    std::string hata;                    // öğretici: "Dosya bozuk: model/bina.json yok"
    DosyaBicimi bicim = DosyaBicimi::Bilinmiyor;
    ProjeIcerigi icerik;                 // Op4Deneme/BinaJson/Matris için D, model/bina.json (ve deneme kamerası için
                                         // gorunum/gorunum.json) girdilerini doldurur — çağıran tek yol izler
    ProjeManifest manifest;
    bool dahaYeniSurum = false;          // dosya daha yeni bir bicim_surumu ile yazılmış → salt okunur aç (MIMARI §13.1.5)
    std::vector<std::string> uyarilar;
};

// Dosyayı okur ve ProjeIcerigi'ne çevirir (bicim_surumu yükseltme zinciri dahil). Model yüklemesi çağıranın işidir.
OkumaSonucu ProjeOku(const std::string& yol);
// Belleği ZIP'e çevirir ("mimetype" ilk ve sıkıştırmasız) ve atomik yazar. manifest.json'u `manifest`ten üretir.
bool ProjeYaz(const std::string& yol, const ProjeIcerigi& icerik, const ProjeManifest& manifest, std::string& hata);
// Bellek içi ZIP (sınama ve kurtarma için): ProjeYaz/ProjeOku'nun dosyasız karşılıkları.
bool ProjeZipKur(const ProjeIcerigi& icerik, const ProjeManifest& manifest, std::string& zip, std::string& hata);
OkumaSonucu ProjeZipCoz(std::string_view zip);

// ---- son dosyalar (MIMARI §13.5) -------------------------------------------------------------------------------------
// En yeni başta, tekrarsız (Windows'ta büyük/küçük harf duyarsız karşılaştırma), en çok `enFazla`.
void SonDosyaEkle(std::vector<std::string>& liste, const std::string& yol, size_t enFazla = 10);

// ---- otomatik kayıt ve kurtarma (MIMARI §13.3) -------------------------------------------------------------------------
struct KurtarmaKaydi {
    std::string dosya;        // %LOCALAPPDATA%\Opus Fortis\op4\kurtarma\<guid>.op4
    std::string asilYol;      // belgenin asıl yolu (adsızsa boş)
    std::string zaman;        // ISO 8601
    std::string baslik;
};
// Kurtarma klasöründeki artık kayıtlar (açılışta "Kurtar / Sil / Sonra" sorusu için).
std::vector<KurtarmaKaydi> KurtarmaKayitlari(const std::string& kurtarmaDizini);

}  // namespace op4
