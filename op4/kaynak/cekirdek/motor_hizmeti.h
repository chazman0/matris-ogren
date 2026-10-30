// op4 çekirdek sözleşmesi — hesap motoru HİZMETİ (istemci tarafı arayüz) (MIMARI §8; "F1 paket sözleşmeleri" §S13).
//
// Arayüzü kullanan: D (F5 çözüm, şablon dökümü, bina_kimlik), A (--test-motor), C (durum çubuğu motor göstergesi),
//                   ileride Belge penceresi (yardımcı motor).
// Uygulayan      : A (derleme-motor) — MotorIstemci: op4motor süreçleri, tel protokolü (motor_protokol.h), iptal,
//                   yeniden başlatma, ana / yardımcı yönlendirmesi. Faz 1 geçişi boyunca Windows'ta Faz 0'ın süreç içi
//                   gömülü motoru da bu arayüzün arkasında çalışır (kaynak/motor_modulu.cpp, GomuluMotorHizmeti).
//
// İş parçacığı kuralı: Gonder / Iptal / Durum / Pompala YALNIZ UI iş parçacığından çağrılır. Yanıt işleyicileri ve durum
// bildirimleri YALNIZ Pompala() içinde, UI iş parçacığında çağrılır (ana döngü her karede, ve beklerken, Pompala çağırır).
// Böylece paketlerin geri çağrıları kilitsiz olarak Hizmetler'e dokunabilir.
#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <string_view>

namespace op4 {

enum class MotorRolu : uint8_t { Ana = 0, Yardimci = 1 };

// MIMARI §8.3 yönlendirme tablosu: bina çözümü ve ayrıntıları → Ana; matris, ders, sonlu eleman, kütüphane, şablonlar,
// deprem önizleme, ifc_iceri → Yardımcı. Bilinmeyen işlem → Yardımcı.
MotorRolu MotorRoluSec(std::string_view islem);

using IstekNo = uint64_t;  // 0 geçersiz; tel protokolündeki id ile aynı

enum class YanitDurumu : uint8_t {
    Tamam = 0,          // web_kopru yanıtı geldi ("hata": null)
    Hata = 1,           // web_kopru hata döndü (hata_turu "girdi" | "ic")
    Iptal = 2,          // kullanıcı iptal etti (hata_turu "iptal")
    MotorHatasi = 3,    // motor başlatılamadı, çöktü ya da yeniden başlatıldı ("motor_yok" | "motor_coktu" | "motor_yeniden")
};

struct MotorYaniti {
    IstekNo no = 0;
    std::string islem;
    YanitDurumu durum = YanitDurumu::Tamam;
    std::string hata;          // durum ≠ Tamam ise öğretici ileti
    std::string hataTuru;      // "girdi" | "ic" | "iptal" | "motor_yok" | "motor_coktu" | "motor_yeniden" | "protokol"
    std::string yanit;         // calistir() metni olduğu gibi (Tamam ve Hata'da dolu; ayrıştırmak çağıranın işi)
    double sureMs = 0;         // motorda geçen süre
    double toplamMs = 0;       // Gonder → işleyici (kuyruk + boru dahil)
};
using YanitIsleyici = std::function<void(const MotorYaniti&)>;

struct MotorDurumOzeti {
    bool baslatildi = false;   // Baslat çağrıldı (yardımcı tembel: ilk istekte)
    bool hazir = false;        // "hazir" iletisi geldi (basarili ya da değil)
    bool basarili = false;
    std::string hata;
    std::string pythonSurumu;  // "3.14.0"
    std::string surumJson;     // web_kopru.surum_json()
    std::string aciklama;      // durum çubuğu metni: "Hesap motoru hazır (Python 3.14.0, 412 ms)"
    double hazirMs = 0;        // süreç başlangıcından hazir'e
    size_t bekleyen = 0;       // yanıtı beklenen istek sayısı
    bool calisiyor = false;    // şu an bir istek işleniyor
    int yenidenBaslatma = 0;   // bu oturumda kaç kez yeniden başlatıldı
};

struct MotorAyari {
    std::string uygulamaDizini;   // op4.exe klasörü (python\, motor\, op4motor.exe burada aranır); UTF-8
    std::string gunlukDizini;     // %LOCALAPPDATA%\Opus Fortis\op4\gunluk (motor-ana.log, motor-yardimci.log)
    std::string pythonYolu;       // POSIX / sınama: op4motor.exe yerine `<python> -m op4_sunucu` (boş = op4motor.exe)
    std::string sunucuDizini;     // POSIX / sınama: op4_sunucu.py ve web_kopru'nun bulunduğu PYTHONPATH (":" ayrık)
    bool yardimciTembel = true;
    int anaBlasIs = 0;            // 0 = çekirdek − 1 (D30)
    double iptalBeklemeMs = 5000; // iptalden sonra yanıt gelmezse süreç sonlandırılır (MIMARI §8.4)
};

class MotorHizmeti {
public:
    virtual ~MotorHizmeti() = default;

    // Ana motoru başlatır (açılış ekranında). Hemen döner; hazır olunca durumBildirimi ve Durum() yansıtır.
    virtual void Baslat(const MotorAyari& ayar) = 0;
    virtual MotorDurumOzeti Durum(MotorRolu rol = MotorRolu::Ana) const = 0;

    // İstek gönderir (rol MotorRoluSec(islem) ile seçilir). girdi / ayarlar JSON nesnesi metinleri (boş = {}).
    // Dönüş: istek no'su. Motor hazır değilse istek kuyrukta bekler; başlatılamamışsa işleyici bir sonraki Pompala'da
    // MotorHatasi ("motor_yok") ile çağrılır. İşleyici her istek için TAM OLARAK BİR KEZ çağrılır (Y1).
    virtual IstekNo Gonder(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                           YanitIsleyici isleyici) = 0;
    // İptal: kuyruktaki istek hemen, çalışan istek KeyboardInterrupt ile biter; işleyici Iptal ile çağrılır.
    // Bilinmeyen / bitmiş no → false.
    virtual bool Iptal(IstekNo no) = 0;

    // UI iş parçacığında: gelen yanıtları ve durum değişikliklerini işleyicilere dağıtır. Dağıtılan yanıt sayısı döner.
    virtual size_t Pompala() = 0;

    // Eşzamanlı yardımcı (yalnız test kipleri ve kapanış): isteği gönderir, yanıt gelene ya da süre dolana dek bekler
    // (bekerken Pompala çağırır). Süre dolarsa iptal eder ve MotorHatasi döner.
    virtual MotorYaniti CalistirBekle(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                                      double zamanAsimiMs) = 0;

    // Süreçlere "kapat" gönderir, bekler (en çok 2 s), gerekirse sonlandırır. Bekleyen isteklere MotorHatasi verilir.
    virtual void Durdur() = 0;

    // Açılış ekranı ve durum çubuğu için: (rol, metin, oran 0–1). Pompala içinde çağrılır.
    std::function<void(MotorRolu, const std::string&, float)> durumBildirimi;
};

// Süreç tabanlı istemci (A, 1.2). Win32 ve POSIX; platform/surec.h üstüne kurulu. Faz 1 taslağı: Baslat motoru
// "henüz uygulanmadı" hatasıyla hazır-başarısız yapar, Gonder isteklerini MotorHatasi ("motor_yok") ile yanıtlar.
std::unique_ptr<MotorHizmeti> MotorIstemcisiOlustur();

}  // namespace op4
