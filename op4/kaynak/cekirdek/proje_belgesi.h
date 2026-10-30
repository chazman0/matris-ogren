// op4 çekirdek sözleşmesi — proje belgesi: açık projenin dosya durumu ve kaydetme katkıları
// (MIMARI §13; "F1 paket sözleşmeleri" §S15).
//
// Pencere başına bir proje vardır (MIMARI D18); tek ProjeBelgesi Hizmetler::belge'dir.
// Sahibi: D (dosya-cozum) — Aç / Kaydet / Farklı kaydet / otomatik kayıt / kurtarma / son dosyalar bu durumu sürer.
// Okuyan: C (başlık çubuğu "op4 — proje.op4 •", Başlangıç paneli), herkes (kirli işareti).
//
// KAYDETME KATKILARI: .op4 içeriği tek modülün işi değildir. Her modül kendi parçasını bir "katkı" olarak kaydeder:
//   B → model/bina.json (çekirdek Metin()), C → gorunum/gorunum.json (kameralar, kipler) ve secim/kumeler.json,
//   D → sonuc/ozet.json, sonuc/veri.json, onizleme.png, manifest.
// D kaydederken bütün katkıların `yaz`ını, açarken (çekirdek modeli yükledikten sonra) bütün `oku`larını çağırır.
// Böylece C kamerayı, D sonucu kendi dosyasında tutar; birbirlerinin koduna dokunmaz.
//
// KİRLİ İŞARETİ: model değişikliği (ModelIslemiSonrasi), görünüm durumundan kaydedilmeye değer bir değişiklik (C:
// kamera sürüklemesi kirletmez; görünüm kipi değişikliği kirletmez — MIMARI §13.2 yalnız model ve kalıcı ayarlar) belgeyi
// kirletir. KirliIsaretle / Temizle yalnız UI iş parçacığından.
#pragma once

#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <utility>
#include <vector>

#include "cekirdek/olay.h"

namespace op4 {

// .op4 ZIP'inin bellekteki karşılığı (MIMARI §13.1). Anahtar ZIP içindeki yol ("model/bina.json"); değer ham baytlar.
// "mimetype" ve "manifest.json"u D yazar; diğerleri katkılardan gelir. Bilinmeyen girdiler açıp kaydederken korunur.
struct ProjeIcerigi {
    std::map<std::string, std::string> girdiler;

    bool Var(const std::string& yol) const { return girdiler.count(yol) != 0; }
    const std::string* Al(const std::string& yol) const {
        const auto i = girdiler.find(yol);
        return i == girdiler.end() ? nullptr : &i->second;
    }
    void Koy(const std::string& yol, std::string veri) { girdiler[yol] = std::move(veri); }
};

// ZIP içindeki bilinen yollar.
namespace proje_yolu {
inline constexpr const char* MIMETYPE = "mimetype";                 // "application/x-op4" (ilk girdi, sıkıştırmasız)
inline constexpr const char* MANIFEST = "manifest.json";
inline constexpr const char* MODEL = "model/bina.json";
inline constexpr const char* GORUNUM = "gorunum/gorunum.json";
inline constexpr const char* SECIM_KUMELERI = "secim/kumeler.json";
inline constexpr const char* SONUC_OZETI = "sonuc/ozet.json";
inline constexpr const char* SONUC_VERISI = "sonuc/veri.json";
inline constexpr const char* IFC_KAYNAGI = "ifc/kaynak.json";
inline constexpr const char* ONIZLEME = "onizleme.png";
inline constexpr const char* MIME_DEGERI = "application/x-op4";
inline constexpr int BICIM_SURUMU = 1;
}  // namespace proje_yolu

// Bir modülün kaydetme / açma katkısı.
struct ProjeKatkisi {
    std::string ad;                                               // "model", "gorunum", "sonuc" … (günlük ve sıralama)
    int sira = 0;                                                 // küçük önce: model 0, görünüm 10, seçim 20, sonuç 30
    std::function<void(ProjeIcerigi&)> yaz;                       // kaydederken: kendi girdilerini Koy
    std::function<void(const ProjeIcerigi&, std::vector<std::string>& uyarilar)> oku;  // açtıktan sonra
    std::function<void()> sifirla;                                // Yeni / boş modelde varsayılana dön
};

class ProjeBelgesi {
public:
    // ---- durum ---------------------------------------------------------------------------------------------------
    const std::string& Yol() const { return yol_; }            // UTF-8 tam yol; boş = hiç kaydedilmedi
    // Başlıkta görünen ad: dosya adı (uzantılı) ya da "Adsız N".
    std::string Ad() const;
    // Pencere başlığı: "op4 — <Ad>" ve kirliyse " •" (MIMARI §5.2).
    std::string PencereBasligi() const;
    bool Kirli() const { return kirli_; }
    bool SaltOkunur() const { return saltOkunur_; }
    uint64_t DegisiklikSayaci() const { return sayac_; }       // her KirliIsaretle'de +1 (otomatik kayıt bunu izler)

    void KirliIsaretle();
    // Kaydetmeden sonra (D): yol ve temiz durum. Yol değiştiyse yolDegisti yayınlanır.
    void Kaydedildi(const std::string& yol);
    // Açtıktan ya da Yeni'den sonra (D): yol (boş = adsız), adsız numarası, salt okunurluk; temiz durum.
    void Acildi(const std::string& yol, int adsizNo, bool saltOkunur);

    // ---- katkılar ------------------------------------------------------------------------------------------------
    void KatkiEkle(ProjeKatkisi k);
    const std::vector<ProjeKatkisi>& Katkilar() const { return katkilar_; }  // sira'ya göre sıralı
    // Bütün katkıların yaz'ını sırayla çağırır (D, ProjeYaz'dan önce).
    void IcerikTopla(ProjeIcerigi& icerik) const;
    // Bütün katkıların oku'sunu sırayla çağırır (D, dosyayı açıp çekirdeğe yükledikten sonra).
    void IcerikDagit(const ProjeIcerigi& icerik, std::vector<std::string>& uyarilar) const;
    void Sifirla() const;

    // ---- olaylar -------------------------------------------------------------------------------------------------
    Olay<bool> kirliDegisti;          // yeni kirli durumu
    Olay<std::string> yolDegisti;     // yeni yol
    Olay<> acildi;                    // Acildi sonrası (C: sığdır, gezgini yenile; D: son dosyalar)
    Olay<std::string> kaydedildi;     // Kaydedildi sonrası (yol)

private:
    std::string yol_;
    int adsizNo_ = 1;
    bool kirli_ = false, saltOkunur_ = false;
    uint64_t sayac_ = 0;
    std::vector<ProjeKatkisi> katkilar_;
};

}  // namespace op4
