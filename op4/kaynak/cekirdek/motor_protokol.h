// op4 çekirdek sözleşmesi — hesap motoru TEL PROTOKOLÜ (MIMARI §8.2; "F1 paket sözleşmeleri" §S12).
//
// op4.exe (istemci) ile op4motor.exe / `python -m op4_sunucu` (sunucu) arasında, miras alınan İKİ anonim boru üstünde:
//   istek borusu : istemci → sunucu      yanıt borusu : sunucu → istemci
// (Protokol stdout / stderr'den GEÇMEZ; sunucu fd 1 ve 2'yi günlük dosyasına yönlendirir — motordaki print'ler zararsız.)
//
// ÇERÇEVE: 4 bayt küçük-endian işaretsiz uzunluk N (1 ≤ N ≤ 512 MiB), ardından N bayt UTF-8 JSON nesnesi. N = 0 ya da
// sınır aşımı protokol hatasıdır (sunucu çıkış kodu 3; istemci süreci sonlandırıp yeniden başlatır).
//
// İLETİLER (alan sırası ve boşluksuz yazım BAĞLAYICIDIR; kalın alanlar her zaman vardır):
//   istemci → sunucu
//     istek : {"tur":"istek","id":17,"islem":"bina_coz","istek":<web_kopru istek nesnesi>}
//             `istek` web isteğiyle birebir aynıdır ({"islem","girdi","ayarlar"}) ve HER ZAMAN SON alandır. `islem` onun
//             kopyasıdır (günlük ve yönlendirme denetimi için). id: 1 … 2^53−1, istemci sürecinde tekil ve artan.
//     iptal : {"tur":"iptal","id":17}         çalışan ya da kuyruktaki isteği iptal et; bilinmeyen id yok sayılır
//     kapat : {"tur":"kapat"}                  kuyruğu boşaltmadan düzgün çık (çıkış kodu 0)
//   sunucu → istemci
//     hazir : {"tur":"hazir","rol":"ana","basarili":true,"pid":4242,"python":"3.14.0","sure_ms":412.5,"surum":{…},"hata":""}
//             web_kopru içe aktarıldıktan sonra BİR KEZ. `surum` = web_kopru.surum_json() nesnesi. basarili=false ise
//             `hata` doludur ve sunucu ardından 4 koduyla çıkar.
//     durum : {"tur":"durum","metin":"web_kopru yükleniyor","oran":45}            açılış ilerlemesi (oran 0–100)
//     ilerleme: {"tur":"ilerleme","id":17,"metin":"Kombinasyonlar","oran":60}    (Faz 5) istek ilerlemesi
//     gunluk: {"tur":"gunluk","duzey":"bilgi"|"uyari"|"hata","metin":"…"}
//     yanit : {"tur":"yanit","id":17,"sure_ms":2891.0,"yanit":<calistir() çıktısı>}
//             `yanit` web_kopru.calistir()'in döndürdüğü metnin KENDİSİDİR (bir JSON nesnesi; yeniden kodlanmaz, kaçışlanmaz)
//             ve HER ZAMAN SON alandır: istemci 50 MB'lık yanıtı ayrıştırmadan dilimler (YanitDilimle).
//
// DEĞİŞMEZLER:
//   Y1  Her istek id'si için TAM OLARAK BİR yanit gelir (başarı, hata, iptal). Kuyruktayken iptal edilen istek hemen
//       {"hata":"İşlem iptal edildi.","hata_turu":"iptal"} yanıtı alır; çalışırken iptal edilen istek KeyboardInterrupt ile
//       biter ve aynı yanıtı alır (MIMARI §8.4). Sunucu çökerse istemci bekleyen her id için kendisi yanıt üretir
//       (hata_turu "motor_coktu"); 5 s içinde iptal yanıtı gelmezse süreci sonlandırıp yeniden başlatır ("motor_yeniden").
//   Y2  İstekler geliş sırasıyla, tek tek işlenir (ana iş parçacığı). İptal / kapat okuyucu iş parçacığında hemen işlenir.
//   Y3  Yanıtlardaki hata biçimi web_kopru'nunkidir: {"hata":"…","hata_turu":"girdi"|"ic"|"iptal"}. İstemcinin ürettiği
//       hata türleri: "motor_yok" (başlatılamadı), "motor_coktu", "motor_yeniden", "protokol".
//   Y4  İstek borusu kapanırsa (op4.exe öldü) sunucu çıkar (kod 0).
//
// SÜREÇ KOMUT SATIRI: op4motor.exe --istek <tutamaç> --yanit <tutamaç> --rol ana|yardimci [--gunluk <dosya>] [--blas <n>]
//   Windows'ta tutamaç miras alınan HANDLE değerinin onluk yazımı, POSIX'te dosya tanımlayıcısıdır. op4motor.exe aynı
//   bağımsız değişkenleri `-X utf8 -B -m op4_sunucu` ile Py_Main'e iletir. Çıkış kodları: 0 düzgün, 2 kullanım / eksik
//   dosya, 3 protokol hatası, 4 Python ya da web_kopru başlatılamadı; diğerleri çökme.
//
// Ortak sınama vektörleri: op4/testler/ortak/motor_protokol.json — C++ (bu dosya) ve Python (op4/motor/op4_protokol.py)
// kodlayıcıları aynı baytları üretmeli ve aynı alanları çözmelidir.
#pragma once

#include <cstdint>
#include <string>
#include <string_view>

namespace op4::motor_protokolu {

inline constexpr uint32_t EN_BUYUK_CERCEVE = 512u * 1024u * 1024u;
inline constexpr uint64_t EN_BUYUK_ID = (uint64_t{1} << 53) - 1;

// ---- çerçeve ----------------------------------------------------------------------------------------------------------
// Gövdeyi 4 bayt uzunlukla birlikte `cikti`nın sonuna ekler. Gövde boşsa ya da sınırı aşıyorsa false (hiçbir şey eklenmez).
bool CerceveEkle(std::string& cikti, std::string_view govde);

enum class CerceveDurumu : uint8_t {
    Tamam = 0,   // `govde` dolduruldu, çerçeve `tampon`un başından silindi
    Eksik = 1,   // daha fazla bayt gerekli (tampon değişmedi)
    Bozuk = 2,   // uzunluk 0 ya da sınır dışı — protokol hatası
};
// Akış tamponunun başından bir çerçeve çıkarır (kısmi okumalara dayanıklı).
CerceveDurumu CerceveAl(std::string& tampon, std::string& govde);

// ---- istemci → sunucu --------------------------------------------------------------------------------------------------
// istekJson: web_kopru istek nesnesinin JSON metni (doğrulanmaz; olduğu gibi eklenir). islem JSON dizesi olarak kaçışlanır.
std::string IstekIletisi(uint64_t id, std::string_view islem, std::string_view istekJson);
std::string IptalIletisi(uint64_t id);
std::string KapatIletisi();

// ---- sunucu → istemci --------------------------------------------------------------------------------------------------
enum class IletiTuru : uint8_t { Bilinmiyor = 0, Hazir = 1, Durum = 2, Ilerleme = 3, Gunluk = 4, Yanit = 5 };

struct GelenIleti {
    IletiTuru tur = IletiTuru::Bilinmiyor;
    uint64_t id = 0;            // ilerleme, yanit
    double oran = 0;            // durum, ilerleme (0–100)
    double sureMs = 0;          // hazir, yanit
    std::string metin;          // durum, ilerleme, gunluk
    std::string duzey;          // gunluk
    std::string rol;            // hazir
    std::string python;         // hazir
    std::string hata;           // hazir (basarili=false)
    std::string surum;          // hazir: surum nesnesinin JSON metni
    std::string yanit;          // yanit: calistir() metni (dilimlenmiş, ayrıştırılmamış)
    long long pid = 0;          // hazir
    bool basarili = false;      // hazir
};
// Gövdeyi çözer. Bilinmeyen `tur` hata değildir (IletiTuru::Bilinmiyor; ileriye uyum). Bozuk JSON → false + hata.
bool IletiCoz(std::string_view govde, GelenIleti& ileti, std::string& hata);

// Sunucu tarafı kodlayıcıları (C++ sınama sunucusu ve vektör testleri için; asıl sunucu Python'dur).
std::string HazirIletisi(std::string_view rol, bool basarili, long long pid, std::string_view python, double sureMs,
                         std::string_view surumJson, std::string_view hata);
std::string DurumIletisi(std::string_view metin, double oran);
std::string IlerlemeIletisi(uint64_t id, std::string_view metin, double oran);
std::string GunlukIletisi(std::string_view duzey, std::string_view metin);
std::string YanitIletisi(uint64_t id, double sureMs, std::string_view calistirMetni);

// İstemcinin kendi ürettiği hata yanıtı (Y1, Y3): {"hata":"<ileti>","hata_turu":"<tur>"}.
std::string HataYaniti(std::string_view ileti, std::string_view hataTuru);

// JSON dize kaçışı (tırnaksız): " \ ve denetim karakterleri; UTF-8 olduğu gibi kalır.
std::string JsonKacis(std::string_view s);

}  // namespace op4::motor_protokolu
