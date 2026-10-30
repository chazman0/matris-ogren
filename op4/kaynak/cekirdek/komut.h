// op4 çekirdek sözleşmesi — komut kayıt defteri (MIMARI §5.3, §5.4, §12.1; "F1 paket sözleşmeleri" §S20).
//
// Komutların TANIMI veridir: op4/veri/komutlar.json (id, komut satırı adı, takma adlar, kısayol, şerit / menü yeri, ipucu,
// sahip paket). Şerit, menüler, hızlı erişim çubuğu, bağlam menüsü, komut satırı tamamlama ve Yardım › Kısayollar tablosu
// bu tanımlardan üretilir (C). Komutların DAVRANIŞI koddur: her paket kendi komutlarına Bagla() ile işleyici bağlar
// (sahip alanı hangi paketin bağlayacağını söyler). Tanımı olmayan id'ye bağlanamaz; tanımı olup işleyicisi olmayan komut
// arayüzde soluk görünür ("henüz uygulanmadı").
//
// Kayıt defteri platformdan bağımsızdır ve Linux'ta sınanır. Tam uygulama sözleşmeyle gelir; sahibi C'dir.
#pragma once

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

#include "cekirdek/olay.h"

namespace op4 {

struct Hizmetler;

enum class SecimKosulu : uint8_t {
    Yok = 0,    // seçimden bağımsız
    Once = 1,   // önce seçim gerekir (seçim yoksa komut seçim ister)
    Sonra = 2,  // komut kendi seçim istemini açar
};

enum class KomutKaynagi : uint8_t { Menu = 0, Serit = 1, HizliErisim = 2, Kisayol = 3, KomutSatiri = 4, Baglam = 5, Senaryo = 6, Kod = 7 };

struct KomutSeritYeri {
    std::string sekme;   // "Dosya", "Model", "Düzenle", "Seçim", "Analiz", "Görünüm", "Yardım" (MIMARI §5.2)
    std::string grup;    // "Proje", "Gezinme" …
    bool buyuk = false;  // büyük düğme
    int sira = 0;
};

struct KomutTanimi {
    std::string id;                       // "dosya.ac", "analiz.coz" — kararlı, ASCII
    std::string ad;                       // komut satırı adı (Türkçe, büyük harf): "AÇ", "ÇÖZ"
    std::string etiket;                   // menü / şerit metni: "Aç…", "Çöz"
    std::vector<std::string> takmaAdlar;  // "A", "COZ" … (kullanıcı takma adları ayrıca takma_adlar.json'dan)
    std::string kisayol;                  // KisayolNormal biçiminde: "Ctrl+O", "Ctrl+Shift+S", "F5", "Alt+1", "PageUp"
    std::string ikon;
    std::optional<KomutSeritYeri> serit;
    std::string menu;                     // klasik menü yolu: "Dosya", "Dosya/Dışa aktar"
    int menuSira = 0;
    bool hizliErisim = false;
    std::string ipucu, yardim;
    std::string kosul;                    // bilgi amaçlı koşul adı ("model_dolu", "secim_var", "sonuc_var", "motor_hazir")
    SecimKosulu secim = SecimKosulu::Yok;
    bool tekrarlanir = false;             // boşta Enter son komutu yineler
    bool onayKutusu = false;              // açık / kapalı komut (Izgara, Kesit görünümü)
    std::string sahip;                    // "A" | "B" | "C" | "D" — işleyiciyi bağlayacak paket
};

struct KomutBaglami {
    Hizmetler& h;
    KomutKaynagi kaynak = KomutKaynagi::Kod;
    std::string arguman;                  // komut satırında addan sonra kalan metin ("KOLON tum" → "tum")
};

struct KomutIsleyici {
    std::function<void(KomutBaglami&)> calistir;
    // Boş dönerse kullanılabilir; değilse soluk gösterilir ve ipucunda neden yazar ("Böl: önce çubuk seçin").
    std::function<std::string(const Hizmetler&)> kullanilamazNedeni;
    // onayKutusu komutlarında işaret durumu.
    std::function<bool(const Hizmetler&)> isaretli;
};

struct KomutDurumu {
    bool tanimli = false;
    bool bagli = false;
    bool kullanilabilir = false;
    bool isaretli = false;
    std::string neden;  // kullanılamıyorsa
};

// "ctrl+shift+s", "Shift + Ctrl + S", "CTRL+S" → "Ctrl+Shift+S" (sıra Ctrl, Shift, Alt; tuş adı büyük: "F5", "PageUp",
// "Escape", "Delete", "1"). Tanınmazsa "".
std::string KisayolNormal(std::string_view kisayol);

class KomutYoneticisi {
public:
    // op4/veri/komutlar.json içeriğini yükler (mevcut tanımların üstüne; aynı id yenilenir, işleyiciler korunur).
    bool KatalogYukle(std::string_view json, std::string& hata);
    // Katalog dışı tanım (sınama, eklenti). Aynı id varsa yenilenir.
    void Tanimla(KomutTanimi t);
    // İşleyici bağlar. id tanımlı değilse false (paket yanlış id kullanıyor: geliştirme hatası, günlüğe yazılır).
    bool Bagla(std::string_view id, KomutIsleyici isleyici);

    // id, komut satırı adı ya da takma ad ile arama (Türkçe katlamalı, büyük / küçük harf duyarsız).
    const KomutTanimi* Bul(std::string_view idYaDaAd) const;
    const KomutTanimi* KisayolBul(std::string_view kisayol) const;
    // Komut satırı tamamlama: önce ad / takma ad öneki, sonra alt dizi eşleşmeleri; tekrarsız, en çok `enFazla`.
    std::vector<const KomutTanimi*> Tamamla(std::string_view yazilan, size_t enFazla = 12) const;
    const std::vector<KomutTanimi>& Tanimlar() const { return tanimlar_; }
    std::vector<std::string> Sekmeler() const { return sekmeler_; }  // katalogdaki sekme sırası

    KomutDurumu Durum(std::string_view id, const Hizmetler& h) const;
    // Çalıştırır. Tanımsız / bağsız / kullanılamaz ise false ve `hata` (öğretici). Başarılıysa `calistirildi` yayınlanır.
    bool Calistir(std::string_view id, Hizmetler& h, KomutKaynagi kaynak, std::string_view arguman = {},
                  std::string* hata = nullptr);
    // Komut satırı: "KOLON tum" → ad "KOLON", argüman "tum". Boş satır: tekrarlanır son komutu yineler.
    bool SatirCalistir(std::string_view satir, Hizmetler& h, std::string* hata = nullptr);
    const std::string& SonKomut() const { return sonKomut_; }

    Olay<std::string> calistirildi;  // komut id'si

private:
    std::vector<KomutTanimi> tanimlar_;
    std::vector<std::string> sekmeler_;
    std::unordered_map<std::string, size_t> idDizini_;
    std::unordered_map<std::string, KomutIsleyici> isleyiciler_;
    std::string sonKomut_;
    void DizinKur();
};

}  // namespace op4
