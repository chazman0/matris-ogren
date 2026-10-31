// op4 çekirdek sözleşmesi — arayüz kancaları: paneller, durum çubuğu öğeleri, menü ve ayar sayfası katkıları,
// bildirimler, iletişim kutuları (MIMARI §5; "F1 paket sözleşmeleri" §S21).
//
// Kayıt defteri platformdan ve ImGui'den bağımsızdır: `ciz` geri çağrıları ImGui kodu içerir ama yalnız Windows
// derlemesinde, C'nin ana penceresi tarafından ve doğru bağlamda (ImGui::Begin/End içinde, UI iş parçacığında) çağrılır.
//   C (arayuz-goruntu): defteri sahiplenir, panelleri yerleştirme alanına, öğeleri durum çubuğuna, katkıları menülere ve
//                       Ayarlar penceresine çizer; Bildirimler'i uygular (komut satırı çıktısı, tost, ilerleme).
//   D (dosya-cozum)   : IletisimKutulari'nı uygular (IFileDialog, TaskDialogIndirect); "Sonuç özeti" paneli, "Son
//                       dosyalar" menü katkısı, Ayarlar › Dosya sayfası, "Sonuçlar eski" / çözüm ilerlemesi durum öğeleri.
//   A                 : "Hesap motoru" durum öğesi.  B: gerekirse "Denetim uyarıları" paneli.
// Senaryo / test kipinde Bildirimler günlüğe yazar, IletisimKutulari senaryodaki yanıtları verir (pencere açılmaz).
#pragma once

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace op4 {

struct Ayarlar;

enum class PanelYeri : uint8_t { Sol = 0, Sag = 1, Alt = 2, Merkez = 3, Yuzer = 4 };

struct PanelKaydi {
    std::string id;          // "model_gezgini", "ozellikler", "baslangic", "sonuc_ozeti" — kararlı (arayuz.ini)
    std::string baslik;      // pencere başlığı (Türkçe)
    PanelYeri yer = PanelYeri::Sag;
    int sira = 0;            // aynı yerdeki sekme sırası
    bool varsayilanAcik = true;
    std::string sahip;       // "A" | "B" | "C" | "D"
    std::function<void()> ciz;  // ImGui::Begin(baslik) içinde çağrılır
};

struct DurumOgesi {
    std::string id;          // "koordinat", "secim_sayisi", "motor", "sonuc_eski", "bagdastirici"
    int sira = 0;            // soldan sağa
    bool sagda = false;      // sağa yaslı grup
    std::string sahip;
    std::function<void()> ciz;
};

struct MenuKatkisi {
    std::string menu;        // "Dosya/Son dosyalar", "Görünüm/Paneller"
    int sira = 0;
    std::string sahip;
    std::function<void()> ciz;  // ImGui::BeginMenu içinde
};

struct AyarSayfasi {
    std::string id;          // "grafik", "arayuz", "dosya", "motor"
    std::string baslik;      // "Grafik", "Arayüz", "Dosya ve otomatik kayıt", "Hesap motoru"
    int sira = 0;
    std::string sahip;
    std::function<void(Ayarlar&)> ciz;  // değişiklikleri doğrudan Ayarlar'a yazar; pencere kapanınca D kaydeder
};

// İletişim kaydı (eklenti, C, 31.10.2026): paketlerin modsuz pencereleri ve akış adımları. C her karede açık olanın
// `ciz`ini çağırır (ImGui::Begin/End'i kayıt sahibi yapar); dönüş 0 = açık kalır, 1 = tamam, −1 = iptal.
// Bilinen kimlik: "yonetmelik_sihirbazi" — Yeni proje akışında (Başlangıç paneli "Boş model" / şablon, dosya.yeni
// Başlangıç'tan) asıl işlemden ÖNCE açılır; 1 dönerse akış sürer, −1 dönerse vazgeçilir (tasarımı ayrıdır).
struct IletisimKaydi {
    std::string id;
    std::string baslik;
    std::string sahip;
    std::function<int()> ciz;
};
inline constexpr const char* YONETMELIK_SIHIRBAZI = "yonetmelik_sihirbazi";

class ArayuzKancalari {
public:
    void PanelEkle(PanelKaydi p);
    void DurumOgesiEkle(DurumOgesi d);
    void MenuKatkisiEkle(MenuKatkisi m);
    void AyarSayfasiEkle(AyarSayfasi s);

    const std::vector<PanelKaydi>& Paneller() const { return paneller_; }        // (yer, sira) sıralı
    const std::vector<DurumOgesi>& DurumOgeleri() const { return durum_; }       // (sagda, sira) sıralı
    std::vector<const MenuKatkisi*> MenuKatkilari(std::string_view menu) const;  // sira sıralı
    const std::vector<AyarSayfasi>& AyarSayfalari() const { return ayar_; }      // sira sıralı

    void IletisimEkle(IletisimKaydi k);                                          // aynı id yenilenir
    const IletisimKaydi* Iletisim(std::string_view id) const;

    const PanelKaydi* Panel(std::string_view id) const;
    bool PanelAcik(std::string_view id) const;
    void PanelGoster(std::string_view id, bool acik);  // yoksa false yok sayılır

    // C bağlar: ana pencereyi kapatma isteği (D'nin dosya.cikis komutu kapanış onayından sonra çağırır).
    std::function<void()> pencereyiKapat;

private:
    std::vector<PanelKaydi> paneller_;
    std::vector<bool> acik_;
    std::vector<DurumOgesi> durum_;
    std::vector<MenuKatkisi> menu_;
    std::vector<AyarSayfasi> ayar_;
    std::vector<IletisimKaydi> iletisim_;
};

enum class TostTuru : uint8_t { Bilgi = 0, Basari = 1, Uyari = 2, Hata = 3 };

// C uygular.
class Bildirimler {
public:
    virtual ~Bildirimler() = default;
    // Komut satırı çıktı alanına satır ekler (ve günlüğe).
    virtual void KomutYaz(std::string_view satir) = 0;
    virtual void Tost(std::string_view metin, TostTuru tur) = 0;
    // Uzun iş göstergesi (durum çubuğu). oran 0–1, < 0 belirsiz; bitince IlerlemeBitti. iptal boş değilse düğme çıkar.
    virtual void Ilerleme(std::string_view id, std::string_view metin, float oran, std::function<void()> iptal) = 0;
    virtual void IlerlemeBitti(std::string_view id) = 0;
};

struct DosyaSuzgeci {
    std::string ad;     // "op4 projesi"
    std::string desen;  // "*.op4" ya da "*.json;*.matris"
};

// D uygular.
class IletisimKutulari {
public:
    virtual ~IletisimKutulari() = default;
    virtual std::optional<std::string> DosyaAc(std::string_view baslik, const std::vector<DosyaSuzgeci>& suzgecler,
                                               std::string_view klasor) = 0;
    virtual std::optional<std::string> DosyaKaydet(std::string_view baslik, const std::vector<DosyaSuzgeci>& suzgecler,
                                                   std::string_view oneriYol) = 0;
    // Düğmeli soru (TaskDialogIndirect). Dönüş: seçilen düğme dizini; pencere kapatıldıysa (Esc) −1.
    virtual int Soru(std::string_view baslik, std::string_view metin, const std::vector<std::string>& dugmeler,
                     int varsayilan) = 0;
};

// Pencere açmayan sürümler: Bildirimler günlük işlevine yazar; IletisimKutulari sıradaki betik yanıtını verir, yanıt
// yoksa (iptal / −1) döner. Linux sınamaları ve --senaryo kipi kullanır.
class GunlukBildirimleri final : public Bildirimler {
public:
    explicit GunlukBildirimleri(std::function<void(std::string_view)> yaz) : yaz_(std::move(yaz)) {}
    void KomutYaz(std::string_view satir) override;
    void Tost(std::string_view metin, TostTuru tur) override;
    void Ilerleme(std::string_view id, std::string_view metin, float oran, std::function<void()> iptal) override;
    void IlerlemeBitti(std::string_view id) override;
    std::vector<std::string> satirlar;  // yazılan her şey (sınama denetimi)

private:
    std::function<void(std::string_view)> yaz_;
};

class BetikliIletisimKutulari final : public IletisimKutulari {
public:
    std::vector<std::string> yanitlar;  // sırayla: dosya yolu ya da düğme dizini ("0", "1"); "" = iptal
    std::optional<std::string> DosyaAc(std::string_view, const std::vector<DosyaSuzgeci>&, std::string_view) override;
    std::optional<std::string> DosyaKaydet(std::string_view, const std::vector<DosyaSuzgeci>&, std::string_view) override;
    int Soru(std::string_view, std::string_view, const std::vector<std::string>&, int) override;
    std::vector<std::string> sorulanlar;  // sorulan başlıklar (sınama denetimi)

private:
    std::optional<std::string> Siradaki();
};

}  // namespace op4
