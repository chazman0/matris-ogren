// op4 çekirdek sözleşmesi — model çekirdeği (QuickJS-ng cephesi) C++ arayüzü
// (MIMARI §9; "F1 paket sözleşmeleri" §S11).
//
// Model otoritesi JS'tedir: docs/ altındaki saf modüller (model_ops, aks_sistemi, bina_cizim, ifc_disari, tablo_editoru)
// ve op4/js/op4_ops.js + op4/js/op4_cekirdek.js QuickJS-ng içinde değişmeden çalışır. Bu sınıf o cephenin C++ yüzüdür:
// her yöntem op4_cekirdek.js'teki aynı adlı işleve karşılık gelir (bkz. op4/js/op4_cekirdek.js JSDoc) ve JS sonuçlarını
// aşağıdaki C++ yapılarına çevirir.
//
// Uygulayan: B (model-cekirdegi) — kaynak/cekirdek_js/ (QuickJS barındırıcı, ön yükleme, tipli dizi köprüsü).
// Kullanan  : C (sahne, öznitelikler, hızlı aks, geri al düğmeleri), D (Yukle / Metin / IfcDisari / SonucEsle).
//
// İş parçacığı: Faz 1'de bütün yöntemler UI iş parçacığından EŞZAMANLI çağrılır (bütçe: 5 bin çubukta ≤ 100 ms,
// MIMARI §6.13). Uygulama ileride işi bir çekirdek iş parçacığına alabilir; dönüşler değer olduğu için çağıranlar etkilenmez.
// Sahne() ve Oznitelikler() JS'e girmez: son işlemden sonra üretilmiş değişmez anlıkları döndürür (her karede çağrılabilir).
//
// Hata kuralı: JS ModelHatasi → IslemRaporu{basarili=false, hata=ileti}; geometrik ret → basarili=true, model değişmez,
// uyarilar dolu (model_ops.js sözleşmesi). JS istisnası / QuickJS hatası → basarili=false, hata "İç hata: …" + günlük.
#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "cekirdek/kimlik.h"
#include "cekirdek/oznitelik.h"
#include "cekirdek/sahne.h"

namespace op4 {

using JsonMetni = std::string;  // UTF-8 JSON metni (nesne ya da dizi); boş = yok

struct ModelOzeti {
    std::string baslik;          // "Adsız 1", şablon başlığı …
    int surum = 3;               // 1 aks–kat, 3 genel
    std::string sistem;          // "celik" | "betonarme"
    size_t dugum = 0, cubuk = 0, panel = 0, kat = 0, aks = 0;
    bool bos = true;             // hiç eleman yok (yeni boş model)
};

// C1 sözleşmesi (MIMARI §9.3): aks–kat modelini genel modele çevirmesi gereken bir işlem önce onay ister. UI metni
// TaskDialog'la sorar (IletisimKutulari::Soru); onaylanırsa aynı işlem parametrelerine "onay": true eklenerek yeniden
// çağrılır (ModelIslemiUygula bunu yapar, bkz. hizmetler.h).
struct GecisOnayi {
    std::string metin;   // BC.genelGecisMetni
};

struct IslemRaporu {
    std::string islem;                    // çağrılan işlem adı (ya da "geriAl" / "yinele" / "yukle" / "yeniBos")
    bool basarili = false;
    std::string hata;                     // basarili=false ise öğretici ileti (Türkçe)
    std::vector<std::string> uyarilar;
    std::vector<ElemanKimligi> eklenen, silinen, degisen;  // sıralı, tekrarsız
    uint64_t sahneSurumu = 0;             // işlemden sonraki sahne sürümü
    std::optional<GecisOnayi> gecisOnayi; // doluysa model DEĞİŞMEDİ; onay bekleniyor
    // Model metni değişti (eleman listeleri boş olsa da: başlık, kesit / malzeme tablosu, yük durumu …). Eklemeli alan
    // (§24.6, 2026-10-30): QuickJS çekirdeği her değişiklikte doldurur; eski sahte çekirdekler false bırakır.
    bool icerikDegisti = false;
    bool ModelDegisti() const {
        return basarili && !gecisOnayi && (icerikDegisti || !eklenen.empty() || !silinen.empty() || !degisen.empty());
    }
};

struct YuklemeSonucu {
    bool basarili = false;
    std::string hata;
    ModelOzeti ozet;
    std::vector<std::string> uyarilar;    // ör. "surum 1 model genel görünümle gösteriliyor"
};

struct GeriAlDurumu {
    bool geriAlinabilir = false, yinelenebilir = false;
    std::string geriAlAdi, yineleAdi;     // menüde "Geri al: Kolon ekle"
    size_t adim = 0, yineAdim = 0;        // yığın derinlikleri (sınır 100 adım / 512 MB, MIMARI §9.4)
};

struct DenetimSonucu {
    bool gecerli = true;
    std::vector<std::string> uyarilar;                                    // ModelOps.denetle
    std::vector<std::pair<ElemanKimligi, std::string>> elemanUyarilari;  // tıkla seç
    size_t serbestDugum = 0;                                              // MIMARI §10.1
};

// Çözüm sonucunun model elemanlarına eşlenmesi (op4_cekirdek.js sonucEsle; MIMARI §4 çözüm akışı 3).
struct ElemanSonucu {
    ElemanKimligi kimlik;
    double dc = -1;              // en büyük D/C; < 0 = tasarım yok
    std::string belirleyen;      // belirleyen kontrol ("eğilme + eksenel", "zımbalama" …)
    std::string kombinasyon;     // belirleyen kombinasyon adı
    int tasarimSatiri = -1;      // veri.tasarim içindeki satır (ayrıntı istemi için)
};
struct SonucEslemesi {
    bool basarili = false;
    std::string hata;
    std::vector<ElemanSonucu> elemanlar;  // kimliğe göre sıralı
    std::vector<std::string> uyarilar;    // eşlenemeyen satırlar
};

struct IfcSonucu {
    bool basarili = false;
    std::string hata;
    std::string metin;          // IFC4 STEP (ISO-10303-21) metni
    std::string dosyaAdi;       // önerilen ad ("<başlık>.ifc")
    std::vector<std::string> uyarilar;
};

struct CekirdekAyari {
    // Geliştirici kipi: JS kaynakları gömülü olanlar yerine bu klasörlerden okunur (boş = gömülü). Sınamada depo kökü.
    std::string jsDizini;
    bool deterministikSaat = false;  // Date.now sabit (senaryolar, eşdeğerlik derlemi)
    std::function<void(std::string_view)> gunluk;  // console.* ve iç hatalar
    // Geri al sınırları (MIMARI §9.4; Ayarlar::cekirdek). Eklemeli alanlar (§24.6, 2026-10-30).
    int geriAlAdim = 100;
    int geriAlMb = 512;
};

class ModelCekirdegi {
public:
    virtual ~ModelCekirdegi() = default;

    // ---- yaşam döngüsü (geri al yığınını sıfırlar) --------------------------------------------------------------
    // Boş model "Adsız N" (MIMARI §13.4; op4_ops.bosModel). baslik boşsa "Adsız 1".
    virtual YuklemeSonucu YeniBos(std::string_view baslik) = 0;
    // Bina JSON metni (surum 1 ya da 3; .op4 model/bina.json, .matris, .json, şablon). kaynak: günlük ve uyarılar için
    // ("dosya:<yol>", "sablon:<ad>", "kurtarma").
    virtual YuklemeSonucu Yukle(std::string_view binaMetni, std::string_view kaynak) = 0;

    // ---- düzenleme (her başarılı çağrı TEK geri al adımıdır) ------------------------------------------------------
    // islem: beyaz listedeki ad (IslemAdlari()); parametreler: JSON nesnesi. Bkz. op4_cekirdek.js uygula().
    virtual IslemRaporu Uygula(std::string_view islem, const JsonMetni& parametreler) = 0;
    virtual IslemRaporu GeriAl() = 0;
    virtual IslemRaporu Yinele() = 0;
    virtual GeriAlDurumu GeriAlBilgisi() const = 0;
    virtual std::vector<std::string> IslemAdlari() const = 0;

    // ---- okuma -----------------------------------------------------------------------------------------------------
    virtual SahnePtr Sahne() const = 0;               // asla null (boşsa BosSahne())
    virtual OznitelikPtr Oznitelikler() const = 0;    // asla null
    virtual uint64_t SahneSurumu() const = 0;
    virtual ModelOzeti Ozet() const = 0;
    virtual DenetimSonucu Denetle() = 0;
    // Kanonik bina JSON metni (kaydetme ve çözüm girdisi; aynı model → aynı bayt dizisi).
    virtual std::string Metin() = 0;

    // ---- sonuç ve dışa aktarma -------------------------------------------------------------------------------------
    // veriOzeti: bina_coz yanıtındaki "veri" nesnesi (JSON metni). Model, çözülen modelle aynı olmalı (çağıran D,
    // cozum_kimligi ile denetler).
    virtual SonucEslemesi SonucEsle(const JsonMetni& veriOzeti) = 0;
    // secenek: {"analiz":bool,"yukler":bool,"dc":bool,"uygulama":{"ad":"op4","surum":…,"firma":"Opus Fortis"},
    //           "zaman":"YYYY-MM-DDTHH:MM:SS"}; veri: son bina_coz "veri"si (D/C için; boş olabilir).
    virtual IfcSonucu IfcDisari(const JsonMetni& secenek, const JsonMetni& veri) = 0;
};

// Fabrika (B): QuickJS-ng çekirdeği (kaynak/cekirdek_js/quickjs_cekirdek.cpp). Ön yükleme, docs/ modülleri ve op4 cephesi
// değerlendirilir; model boş "Adsız 1"dir (sahne sürümü 0). Başarısızsa null ve hata (hangi dosya, hangi satır).
std::unique_ptr<ModelCekirdegi> ModelCekirdegiOlustur(const CekirdekAyari& ayar, std::string& hata);

// Faz 1'de C'nin ve D'nin beklediği işlem adları (beyaz listenin alt kümesi; B en az bunları sağlar).
//   "hizliAks"      : {x:[aralıklar m], y:[…], z:[kat yükseklikleri m], ad?:{…}} → MA.hizliAks + BC.aksSihirbazUygula
//   "aksSihirbazi"  : BC.aksSihirbazUygula parametreleri
//   "baslikDegistir": {baslik}
//   "genellestir"   : {} → C1 dönüşümü (onaylı)
namespace islem {
inline constexpr const char* HIZLI_AKS = "hizliAks";
inline constexpr const char* AKS_SIHIRBAZI = "aksSihirbazi";
inline constexpr const char* BASLIK_DEGISTIR = "baslikDegistir";
inline constexpr const char* GENELLESTIR = "genellestir";
}  // namespace islem

}  // namespace op4
