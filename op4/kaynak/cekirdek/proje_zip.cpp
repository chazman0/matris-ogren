// op4 çekirdek — bellek içi ZIP / PNG (miniz 3.0.2) ve küçük zaman / karma yardımcıları. Sahibi: D (dosya-cozum).
#include "cekirdek/proje_zip.h"

#include <miniz.h>

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <memory>

namespace op4 {
namespace {

std::string MinizHatasi(mz_zip_error e, const std::string& ad) {
    const std::string girdi = ad.empty() ? std::string() : " ('" + ad + "')";
    switch (e) {
        case MZ_ZIP_FAILED_FINDING_CENTRAL_DIR:
        case MZ_ZIP_NOT_AN_ARCHIVE:
        case MZ_ZIP_UNSUPPORTED_CDIR_SIZE:
            return "Dosya bozuk ya da yarım kalmış: ZIP dizini bulunamadı (dosya kesilmiş olabilir; varsa .bak yedeğini "
                   "ya da kurtarma kaydını açın).";
        case MZ_ZIP_INVALID_HEADER_OR_CORRUPTED:
            return "Dosya bozuk: ZIP başlıkları geçersiz" + girdi + ".";
        case MZ_ZIP_UNSUPPORTED_MULTIDISK:
            return "Çok parçalı ZIP arşivleri desteklenmez.";
        case MZ_ZIP_DECOMPRESSION_FAILED:
        case MZ_ZIP_UNEXPECTED_DECOMPRESSED_SIZE:
            return "Dosya bozuk: sıkıştırılmış veri açılamadı" + girdi + ".";
        case MZ_ZIP_CRC_CHECK_FAILED:
            return "Dosya bozuk: sağlama toplamı (CRC32) tutmuyor" + girdi + ".";
        case MZ_ZIP_UNSUPPORTED_METHOD:
            return "Desteklenmeyen sıkıştırma yöntemi" + girdi + " (op4 yalnız deflate ve sıkıştırmasız girdileri okur).";
        case MZ_ZIP_UNSUPPORTED_ENCRYPTION:
            return "Şifreli ZIP girdileri desteklenmez" + girdi + ".";
        case MZ_ZIP_ALLOC_FAILED:
            return "Bellek yetmedi" + girdi + ".";
        case MZ_ZIP_TOO_MANY_FILES:
        case MZ_ZIP_FILE_TOO_LARGE:
        case MZ_ZIP_ARCHIVE_TOO_LARGE:
            return "Arşiv çok büyük" + girdi + ".";
        default:
            return std::string("ZIP işlenemedi") + girdi + " (miniz: " + mz_zip_get_error_string(e) + ").";
    }
}

// Bellekten okuma geri çağrısı: miniz'in kendi bellek okuyucusu bozuk ofsetlerde sınırı aşan işaretçi aritmetiği yapar
// (UBSan); bu okuyucu önce sınırı denetler.
struct BellekOkuyucu {
    const char* p;
    size_t n;
};

size_t BellektenOku(void* opak, mz_uint64 ofs, void* tampon, size_t n) {
    const BellekOkuyucu* b = static_cast<const BellekOkuyucu*>(opak);
    if (ofs >= b->n) return 0;
    const size_t s = static_cast<size_t>(std::min<mz_uint64>(n, b->n - ofs));
    std::memcpy(tampon, b->p + ofs, s);
    return s;
}

struct ZipBirakici {
    mz_zip_archive* z;
    ~ZipBirakici() {
        if (z->m_zip_mode == MZ_ZIP_MODE_READING) mz_zip_reader_end(z);
        else if (z->m_zip_mode != MZ_ZIP_MODE_INVALID) mz_zip_writer_end(z);
    }
};

// Gün sayısı (1970-01-01'den) ↔ takvim (proleptik Gregoryen; H. Hinnant algoritması).
int64_t GunlerdenTakvime(int64_t y, unsigned m, unsigned d) {
    y -= m <= 2;
    const int64_t era = (y >= 0 ? y : y - 399) / 400;
    const unsigned yoe = static_cast<unsigned>(y - era * 400);
    const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
    const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + static_cast<int64_t>(doe) - 719468;
}

void TakvimdenGunlere(int64_t z, int64_t& y, unsigned& m, unsigned& d) {
    z += 719468;
    const int64_t era = (z >= 0 ? z : z - 146096) / 146097;
    const unsigned doe = static_cast<unsigned>(z - era * 146097);
    const unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    y = static_cast<int64_t>(yoe) + era * 400;
    const unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    const unsigned mp = (5 * doy + 2) / 153;
    d = doy - (153 * mp + 2) / 5 + 1;
    m = mp < 10 ? mp + 3 : mp - 9;
    y += m <= 2;
}

}  // namespace

bool ZipKur(const std::vector<ZipYazGirdisi>& girdiler, std::time_t zaman, std::string& zip, std::string& hata) {
    mz_zip_archive z;
    std::memset(&z, 0, sizeof(z));
    if (!mz_zip_writer_init_heap(&z, 0, 64 * 1024)) {
        hata = MinizHatasi(mz_zip_get_last_error(&z), "");
        return false;
    }
    ZipBirakici b{&z};
    MZ_TIME_T t = static_cast<MZ_TIME_T>(zaman);
    for (const ZipYazGirdisi& g : girdiler) {
        const mz_uint duzey = g.sikistir ? static_cast<mz_uint>(MZ_DEFAULT_LEVEL) : static_cast<mz_uint>(MZ_NO_COMPRESSION);
        if (!mz_zip_writer_add_mem_ex_v2(&z, g.ad.c_str(), g.veri.data(), g.veri.size(), nullptr, 0, duzey, 0, 0, &t, nullptr,
                                         0, nullptr, 0)) {
            hata = MinizHatasi(mz_zip_get_last_error(&z), g.ad);
            return false;
        }
    }
    void* tampon = nullptr;
    size_t boyut = 0;
    if (!mz_zip_writer_finalize_heap_archive(&z, &tampon, &boyut)) {
        hata = MinizHatasi(mz_zip_get_last_error(&z), "");
        return false;
    }
    zip.assign(static_cast<const char*>(tampon), boyut);
    mz_free(tampon);  // sonlandırılmış yığın arşivinin tamponu çağırana geçer
    return true;
}

bool ZipCoz(std::string_view veri, std::vector<ZipOkunanGirdi>& girdiler, std::string& hata, const ZipOkumaSiniri& sinir) {
    girdiler.clear();
    mz_zip_archive z;
    std::memset(&z, 0, sizeof(z));
    BellekOkuyucu okuyucu{veri.data(), veri.size()};
    z.m_pRead = &BellektenOku;
    z.m_pIO_opaque = &okuyucu;
    if (!mz_zip_reader_init(&z, veri.size(), 0)) {
        hata = MinizHatasi(mz_zip_get_last_error(&z), "");
        return false;
    }
    ZipBirakici b{&z};
    const mz_uint n = mz_zip_reader_get_num_files(&z);
    if (n > sinir.enFazlaGirdi) {
        hata = "Arşivde çok fazla girdi var (" + std::to_string(n) + "; en çok " + std::to_string(sinir.enFazlaGirdi) + ").";
        return false;
    }
    uint64_t toplam = 0;
    for (mz_uint i = 0; i < n; ++i) {
        mz_zip_archive_file_stat st;
        if (!mz_zip_reader_file_stat(&z, i, &st)) {
            hata = MinizHatasi(mz_zip_get_last_error(&z), "");
            return false;
        }
        if (mz_zip_reader_is_file_a_directory(&z, i)) continue;
        const std::string ad = st.m_filename;
        if (!st.m_is_supported) {
            hata = MinizHatasi(st.m_bit_flag & 1 ? MZ_ZIP_UNSUPPORTED_ENCRYPTION : MZ_ZIP_UNSUPPORTED_METHOD, ad);
            return false;
        }
        if (st.m_uncomp_size > sinir.enFazlaGirdiBayt || (toplam += st.m_uncomp_size) > sinir.enFazlaToplamBayt) {
            hata = "Arşiv girdisi çok büyük ('" + ad + "', " + std::to_string(st.m_uncomp_size) +
                   " bayt): dosya bozuk ya da op4 projesi değil.";
            return false;
        }
        ZipOkunanGirdi g;
        g.ad = ad;
        g.sikistirilmis = st.m_method != 0;
        g.veri.resize(static_cast<size_t>(st.m_uncomp_size));
        if (!g.veri.empty() && !mz_zip_reader_extract_to_mem(&z, i, g.veri.data(), g.veri.size(), 0)) {
            hata = MinizHatasi(mz_zip_get_last_error(&z), ad);
            return false;
        }
        if (g.veri.empty() && st.m_crc32 != 0) {  // boş girdi ama CRC sıfır değil
            hata = MinizHatasi(MZ_ZIP_CRC_CHECK_FAILED, ad);
            return false;
        }
        girdiler.push_back(std::move(g));
    }
    return true;
}

std::string PngKodla(const uint8_t* rgba, int genislik, int yukseklik) {
    size_t n = 0;
    void* p = tdefl_write_image_to_png_file_in_memory_ex(rgba, genislik, yukseklik, 4, &n, 6, MZ_FALSE);
    if (!p) return {};
    std::string s(static_cast<const char*>(p), n);
    mz_free(p);
    return s;
}

bool IsoZamanCoz(std::string_view iso, std::time_t& t) {
    // "YYYY-MM-DDTHH:MM:SS" (sonrası — "Z", kesir — yok sayılır). sscanf yerine elle: MSVC'de kullanımdan kalkma uyarısı yok.
    if (iso.size() < 19) return false;
    auto sayi = [&](size_t bas, size_t uzunluk, int& v) {
        v = 0;
        for (size_t i = bas; i < bas + uzunluk; ++i) {
            if (iso[i] < '0' || iso[i] > '9') return false;
            v = v * 10 + (iso[i] - '0');
        }
        return true;
    };
    int y = 0, mo = 0, d = 0, h = 0, mi = 0, s = 0;
    if (!sayi(0, 4, y) || iso[4] != '-' || !sayi(5, 2, mo) || iso[7] != '-' || !sayi(8, 2, d) || (iso[10] != 'T' && iso[10] != ' ') ||
        !sayi(11, 2, h) || iso[13] != ':' || !sayi(14, 2, mi) || iso[16] != ':' || !sayi(17, 2, s))
        return false;
    if (mo < 1 || mo > 12 || d < 1 || d > 31 || h > 23 || mi > 59 || s > 60) return false;
    const int64_t gun = GunlerdenTakvime(y, static_cast<unsigned>(mo), static_cast<unsigned>(d));
    t = static_cast<std::time_t>(gun * 86400 + h * 3600 + mi * 60 + s);
    return true;
}

std::string IsoZaman(std::time_t t) {
    const int64_t sn = static_cast<int64_t>(t);
    int64_t gun = sn / 86400, kalan = sn % 86400;
    if (kalan < 0) {
        kalan += 86400;
        --gun;
    }
    int64_t y = 0;
    unsigned m = 0, d = 0;
    TakvimdenGunlere(gun, y, m, d);
    char b[64];
    std::snprintf(b, sizeof(b), "%04lld-%02u-%02uT%02d:%02d:%02dZ", static_cast<long long>(y), m, d,
                  static_cast<int>(kalan / 3600), static_cast<int>(kalan / 60 % 60), static_cast<int>(kalan % 60));
    return b;
}

std::string MetinKarmasi(std::string_view metin) {
    uint64_t k = 14695981039346656037ull;
    for (const char c : metin) {
        k ^= static_cast<unsigned char>(c);
        k *= 1099511628211ull;
    }
    char b[32];
    std::snprintf(b, sizeof(b), "fnv1a64:%016llx", static_cast<unsigned long long>(k));
    return b;
}

}  // namespace op4
