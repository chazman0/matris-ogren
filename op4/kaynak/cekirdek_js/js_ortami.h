// op4 model çekirdeği — QuickJS-ng çalışma ortamı (MIMARI §9.2; kabul B2). Uygulayan: B (model-cekirdegi).
//
// Bir JSRuntime + JSContext; ön yükleme (op4/js/op4_onyukleme.js + C işlevleri __op4_gunluk, __op4_klon) ve docs/
// modüllerinin, op4 cephesinin ve köprünün sırayla değerlendirilmesi. JS kaynakları exe'ye gömülüdür (js_gomulu.h); geliştirici
// kipinde (jsDizini dolu) aynı göreli yollar o klasörden okunur (depo kökü: "<kök>/docs/model_ops.js").
//
// Bu başlık QuickJS türü içermez (sınamalar ve modül yalnız bunu görür). Köprü (quickjs_cekirdek.cpp) QuickJS'e
// js_ortami_ic.h üstünden erişir. Bütün yöntemler aynı iş parçacığından çağrılmalıdır (UI iş parçacığı, MIMARI §9.4).
#pragma once

#include <cstddef>
#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace op4 {

struct JsOrtamiAyari {
    std::string jsDizini;                           // boş = gömülü kaynaklar
    bool deterministikSaat = false;                 // Date.now 2026-01-01'den 1 ms adımlarla (op4_onyukleme.js)
    std::function<void(std::string_view)> gunluk;   // console.* ve iç hatalar
    size_t bellekSiniri = 0;                        // bayt; 0 = 3 GB (x64)
    double cagriSiniriSn = 300;                     // tek bir çağrının en uzun süresi (sonsuz döngü koruması)
};

class JsOrtami {
public:
    explicit JsOrtami(JsOrtamiAyari ayar);
    ~JsOrtami();
    JsOrtami(const JsOrtami&) = delete;
    JsOrtami& operator=(const JsOrtami&) = delete;

    // Çalışma zamanını kurar ve dosyaları sırayla değerlendirir. Başarısızsa false + hata (dosya adı ve satırıyla).
    bool Kur(std::string& hata);
    // Kur'daki bütün dosyaların derleme + ilk çalıştırma süresi (ms; OP4OLCUM cekirdek_derleme_ms).
    double DerlemeMs() const;
    const std::vector<std::string>& YuklenenDosyalar() const;
    size_t YuklenenBayt() const;

    // Küresel kapsamda bir betik değerlendirir; sonuç JSON.stringify ile döner (undefined → ""). İstisnada false + hata.
    bool Degerlendir(std::string_view kod, const std::string& ad, std::string& sonucJson, std::string& hata);
    // "Nesne.yontem" yolundaki küresel işlevi dize bağımsız değişkenlerle çağırır. Dönüş dize ise olduğu gibi, değilse JSON.
    bool CagirMetin(std::string_view yol, const std::vector<std::string>& argumanlar, std::string& sonuc, std::string& hata);

    // Çöp toplayıcıyı çalıştırır; JS yığınının bayt kullanımı (malloc_size).
    void CopTopla();
    size_t BellekKullanimi() const;

    // QuickJS bağlamı (JSContext*): yalnız kaynak/cekirdek_js içinden (js_ortami_ic.h).
    void* Baglam() const;
    void Gunluk(std::string_view s) const;

    struct Ic;

private:
    std::unique_ptr<Ic> ic_;
};

}  // namespace op4
