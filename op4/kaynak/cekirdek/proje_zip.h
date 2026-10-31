// op4 çekirdek — bellek içi ZIP ve PNG yardımcıları (miniz üstüne ince katman; MIMARI §13.1). Sahibi: D (dosya-cozum).
// Yalnız proje_*.cpp kullanır; miniz başlıkları bu dosyanın dışına sızmaz.
#pragma once

#include <cstdint>
#include <ctime>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace op4 {

struct ZipYazGirdisi {
    std::string ad;          // ZIP içindeki yol ("model/bina.json"); UTF-8
    std::string_view veri;
    bool sikistir = true;    // false: STORED ("mimetype", zaten sıkışık PNG)
};

// Girdileri VERİLEN SIRAYLA yazar (ilk girdi "mimetype" olmalıdır). Bütün girdilerin değiştirilme zamanı `zaman`dır:
// aynı girdiler + aynı zaman → aynı baytlar (aynı makinede; DOS zamanı yerel saattir).
bool ZipKur(const std::vector<ZipYazGirdisi>& girdiler, std::time_t zaman, std::string& zip, std::string& hata);

struct ZipOkumaSiniri {
    size_t enFazlaGirdi = 4096;
    uint64_t enFazlaGirdiBayt = uint64_t{1} << 30;   // 1 GiB (tek girdi, açılmış)
    uint64_t enFazlaToplamBayt = uint64_t{3} << 30;  // 3 GiB (bütün girdiler, açılmış; sıkıştırma bombası)
};

struct ZipOkunanGirdi {
    std::string ad;
    std::string veri;
    bool sikistirilmis = false;
};

// ZIP'i açar ve bütün dosya girdilerini (klasör girdileri atlanır) sıra korunarak döndürür. Her girdinin CRC32'si
// denetlenir. Bozuk / yarım dosyada false + öğretici Türkçe hata.
bool ZipCoz(std::string_view zip, std::vector<ZipOkunanGirdi>& girdiler, std::string& hata, const ZipOkumaSiniri& sinir = {});

// RGBA8 görüntüyü PNG'ye çevirir (miniz tdefl). Başarısızsa boş.
std::string PngKodla(const uint8_t* rgba, int genislik, int yukseklik);

// "YYYY-MM-DDTHH:MM:SS[Z]" (UTC) → time_t; okunamazsa false.
bool IsoZamanCoz(std::string_view iso, std::time_t& t);
// time_t → "YYYY-MM-DDTHH:MM:SSZ" (UTC).
std::string IsoZaman(std::time_t t);

// FNV-1a 64 bit (model metni karması: kaydedilen sonucun modelle eşleştiği hızlı denetim). "fnv1a64:<16 hex>".
std::string MetinKarmasi(std::string_view metin);

}  // namespace op4
