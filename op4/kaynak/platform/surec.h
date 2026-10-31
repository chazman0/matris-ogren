// op4 platform sözleşmesi — alt süreç + iki anonim boru (MIMARI §8.1; "F1 paket sözleşmeleri" §S14).
//
// Uygulayan: A (derleme-motor) — kaynak/platform/surec_win.cpp (CreatePipe + STARTUPINFOEX PROC_THREAD_ATTRIBUTE_HANDLE_LIST
// ile yalnız iki boru tutamacı miras verilir; Job Object bellek tavanı) ve kaynak/platform/surec_posix.cpp (pipe2 +
// posix_spawn; Linux'ta `python3 -m op4_sunucu` sınaması). Başlıkta platform türü yoktur.
#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace op4 {

struct SurecAyari {
    std::string program;                 // UTF-8 tam yol
    std::vector<std::string> argumanlar; // program adı hariç; "{istek}" ve "{yanit}" yer tutucuları çocuğun tutamaç / fd
                                         // değeriyle değiştirilir
    std::vector<std::pair<std::string, std::string>> ortam;  // eklenecek / değiştirilecek ortam değişkenleri
    std::string calismaDizini;           // boş = üst süreçle aynı
    std::string ciktiDosyasi;            // çocuğun stdout + stderr'i (boş = boşa)
    uint64_t bellekSiniriBayt = 0;       // 0 = sınırsız (Windows: Job Object; POSIX: yok sayılır)
};

class Surec {
public:
    virtual ~Surec() = default;
    // Süreci başlatır; borular kurulur. Başarısızsa false + hata.
    virtual bool Baslat(const SurecAyari& ayar, std::string& hata) = 0;
    // İstek borusuna yazar (tamamı yazılana dek). Boru kapalıysa false.
    virtual bool Yaz(const void* veri, size_t boyut) = 0;
    // Yanıt borusundan okur: en çok `boyut` bayt; veri gelene dek bekler. 0 = karşı uç kapandı (süreç bitti), <0 hata.
    // Ayrı bir okuyucu iş parçacığından çağrılır.
    virtual long long Oku(void* tampon, size_t boyut) = 0;
    // İstek borusunu kapatır (sunucu EOF görür ve çıkar, Y4).
    virtual void YazmayiKapat() = 0;
    virtual bool Calisiyor() const = 0;
    // En çok `ms` bekler; bittiyse çıkış kodunu yazar ve true döner.
    virtual bool Bekle(uint32_t ms, int& cikisKodu) = 0;
    virtual void Sonlandir() = 0;  // TerminateProcess / SIGKILL
    virtual long long Kimlik() const = 0;  // pid
};

// Platforma uygun uygulama (surec_win.cpp ya da surec_posix.cpp).
std::unique_ptr<Surec> SurecOlustur();

}  // namespace op4
