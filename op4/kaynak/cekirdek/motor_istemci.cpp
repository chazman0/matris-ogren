// op4 çekirdek — süreç tabanlı hesap motoru istemcisi (sözleşme S12, S13, S14; F1 iş 1.2; kabul A8). Sahibi: A.
// Kurallar motor_istemci.h başlığındadır. Platforma özgü kod yalnız platform/surec_*.cpp'dedir.
#include "cekirdek/motor_istemci.h"

#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <filesystem>
#include <fstream>
#include <map>
#include <mutex>
#include <system_error>
#include <string_view>
#include <thread>
#include <tuple>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

#include "cekirdek/motor_protokol.h"
#include "platform/surec.h"

namespace op4 {
namespace mp = motor_protokolu;

namespace {

using Saat = std::chrono::steady_clock;

double SimdiMs() {
    static const Saat::time_point t0 = Saat::now();
    return std::chrono::duration<double, std::milli>(Saat::now() - t0).count();
}

const char* RolAdi(MotorRolu r) { return r == MotorRolu::Ana ? "ana" : "yardimci"; }

#ifdef _WIN32
constexpr char kYolAyirici = ';';
constexpr const char* kMotorExe = "op4motor.exe";
#else
constexpr char kYolAyirici = ':';
constexpr const char* kMotorExe = "op4motor";
#endif

std::filesystem::path Yol(const std::string& u) {
    return std::filesystem::path(std::u8string(reinterpret_cast<const char8_t*>(u.data()), u.size()));
}

std::string Utf8Yol(const std::filesystem::path& p) {
    const std::u8string s = p.u8string();
    return std::string(reinterpret_cast<const char*>(s.data()), s.size());
}

// Dosyanın son ~1500 baytından son birkaç satır (motor başlatılamadığında öğretici hata metni için).
std::string GunlukKuyrugu(const std::string& yol) {
    if (yol.empty()) return {};
    std::ifstream f(Yol(yol), std::ios::binary);
    if (!f) return {};
    f.seekg(0, std::ios::end);
    const std::streamoff boy = f.tellg();
    const std::streamoff bas = std::max<std::streamoff>(0, boy - 1500);
    f.seekg(bas);
    std::string s(static_cast<size_t>(boy - bas), '\0');
    f.read(s.data(), static_cast<std::streamsize>(s.size()));
    while (!s.empty() && (s.back() == '\n' || s.back() == '\r')) s.pop_back();
    if (bas > 0) {
        const size_t i = s.find('\n');
        if (i != std::string::npos) s.erase(0, i + 1);
    }
    // en çok 8 satır
    size_t n = 0, i = s.size();
    while (i > 0 && n < 8) {
        i = s.rfind('\n', i - 1);
        if (i == std::string::npos) {
            i = 0;
            break;
        }
        ++n;
    }
    return s.substr(i == 0 ? 0 : i + 1);
}

// calistir() metninden durum: web_kopru hata yanıtı {"hata": "…", "hata_turu": …} ile başlar (MIMARI §8.2 Y3).
void YanitDurumuCoz(MotorYaniti& y) {
    const std::string& m = y.yanit;
    if (m.rfind("{\"hata\": \"", 0) != 0 && m.rfind("{\"hata\":\"", 0) != 0) {
        y.durum = YanitDurumu::Tamam;
        return;
    }
    const nlohmann::json j = nlohmann::json::parse(m, nullptr, false);
    const bool nesne = j.is_object();
    y.hata = nesne && j.contains("hata") && j["hata"].is_string() ? j["hata"].get<std::string>() : "hesap motoru hatası";
    y.hataTuru = nesne && j.contains("hata_turu") && j["hata_turu"].is_string() ? j["hata_turu"].get<std::string>() : "ic";
    y.durum = y.hataTuru == "iptal" ? YanitDurumu::Iptal : YanitDurumu::Hata;
}

struct Kayit {
    IstekNo no = 0;
    std::string islem;
    YanitIsleyici isleyici;
    double gonderimMs = 0;
    bool iptal = false;
    double iptalMs = 0;
    bool cozuldu = false;  // işleyici çağrıldı / çağrılmak üzere sıraya alındı
};

struct Olay {
    enum class Tur : uint8_t { Ileti, Bitti, Bozuk } tur = Tur::Ileti;
    mp::GelenIleti ileti;
    std::string hata;
};

enum class Hal : uint8_t { Yok, Basliyor, Hazir, Basarisiz };

// Bir rolün motor süreci. Okuyucu / yazıcı iş parçacıklarıyla paylaşılanlar `kilit` altındadır; gerisi UI iş parçacığının.
struct Sureci {
    MotorRolu rol = MotorRolu::Ana;
    Hal hal = Hal::Yok;
    std::unique_ptr<Surec> surec;
    std::thread okuyucu, yazici;
    // paylaşılan
    std::mutex kilit;
    std::condition_variable kosul;
    std::deque<std::string> giden;
    bool yazmayiBitir = false;
    std::deque<Olay> gelen;
    // UI
    std::string hata, python, surumJson, sonDurum, gunlukYolu;
    double baslamaMs = 0, hazirMs = 0;
    std::map<IstekNo, Kayit> sunucuda;  // gönderilmiş, sunucu yanıtı beklenen (baştaki çalışan)
    IstekNo onNo = 0;
    double onMs = 0;
    int yenidenBaslatma = 0;
    std::deque<double> cokmeler;
    long long pid = 0;
};

}  // namespace

struct MotorIstemcisi::Ic {
    MotorIstemcisi& dis;
    MotorAyari ayar;
    bool baslatildi = false;
    bool durduruldu = false;
    IstekNo sonNo = 0;
    Sureci surecler[2];
    std::vector<std::pair<YanitIsleyici, MotorYaniti>> dagitim;   // Pompala'da çağrılacak işleyiciler
    std::vector<std::tuple<MotorRolu, std::string, float>> bildirimler;

    explicit Ic(MotorIstemcisi& d) : dis(d) {
        surecler[0].rol = MotorRolu::Ana;
        surecler[1].rol = MotorRolu::Yardimci;
    }

    Sureci& S(MotorRolu r) { return surecler[r == MotorRolu::Ana ? 0 : 1]; }

    void Yaz(const std::string& m) const {
        if (dis.gunluk) dis.gunluk(m);
    }

    // ------------------------------------------------------------------------------------------------ yanıt üretimi
    void Coz(Kayit& k, MotorYaniti y) {
        if (k.cozuldu) return;
        k.cozuldu = true;
        y.no = k.no;
        y.islem = k.islem;
        y.toplamMs = SimdiMs() - k.gonderimMs;
        dagitim.emplace_back(std::move(k.isleyici), std::move(y));
        k.isleyici = nullptr;
    }

    static MotorYaniti HataYaniti(YanitDurumu d, const std::string& tur, const std::string& ileti) {
        MotorYaniti y;
        y.durum = d;
        y.hataTuru = tur;
        y.hata = ileti;
        y.yanit = mp::HataYaniti(ileti, tur);
        return y;
    }

    static MotorYaniti IptalYaniti() {
        return HataYaniti(YanitDurumu::Iptal, "iptal", "İşlem iptal edildi.");
    }

    void HemenYanitla(IstekNo no, std::string islem, YanitIsleyici f, MotorYaniti y) {
        Kayit k;
        k.no = no;
        k.islem = std::move(islem);
        k.isleyici = std::move(f);
        k.gonderimMs = SimdiMs();
        Coz(k, std::move(y));
    }

    // Sürecin yanıtlanmamış bütün isteklerini çözer: iptal edilmiş olanlar Iptal, diğerleri verilen hata.
    void HepsiniCoz(Sureci& s, YanitDurumu d, const std::string& tur, const std::string& ileti) {
        for (auto& e : s.sunucuda) Coz(e.second, e.second.iptal ? IptalYaniti() : HataYaniti(d, tur, ileti));
        s.sunucuda.clear();
        s.onNo = 0;
    }

    // ------------------------------------------------------------------------------------------------ iş parçacıkları
    static void Okuyucu(Sureci* s, Surec* surec) {
        std::string tampon, govde;
        std::vector<char> parca(size_t{1} << 18);
        auto ekle = [s](Olay o) {
            std::lock_guard<std::mutex> k(s->kilit);
            s->gelen.push_back(std::move(o));
        };
        for (;;) {
            const long long n = surec->Oku(parca.data(), parca.size());
            if (n <= 0) {
                ekle(Olay{Olay::Tur::Bitti, {}, n < 0 ? "yanıt borusu okunamadı" : ""});
                return;
            }
            tampon.append(parca.data(), static_cast<size_t>(n));
            for (;;) {
                if (tampon.size() >= 4) {  // büyük çerçevede bir kez yer ayır (50 MB yanıt)
                    const auto b = [&](size_t i) { return static_cast<uint32_t>(static_cast<unsigned char>(tampon[i])); };
                    const uint32_t boy = b(0) | (b(1) << 8) | (b(2) << 16) | (b(3) << 24);
                    if (boy <= mp::EN_BUYUK_CERCEVE && tampon.capacity() < size_t{4} + boy) tampon.reserve(size_t{4} + boy);
                }
                const mp::CerceveDurumu d = mp::CerceveAl(tampon, govde);
                if (d == mp::CerceveDurumu::Eksik) break;
                if (d == mp::CerceveDurumu::Bozuk) {
                    ekle(Olay{Olay::Tur::Bozuk, {}, "bozuk çerçeve uzunluğu"});
                    return;
                }
                Olay o;
                std::string h;
                if (!mp::IletiCoz(govde, o.ileti, h)) {
                    ekle(Olay{Olay::Tur::Bozuk, {}, h});
                    return;
                }
                ekle(std::move(o));
            }
        }
    }

    static void Yazici(Sureci* s, Surec* surec) {
        for (;;) {
            std::string c;
            {
                std::unique_lock<std::mutex> k(s->kilit);
                s->kosul.wait(k, [s] { return !s->giden.empty() || s->yazmayiBitir; });
                if (s->giden.empty()) break;
                c = std::move(s->giden.front());
                s->giden.pop_front();
            }
            if (!surec->Yaz(c.data(), c.size())) {  // boru kapandı: süreç bitiyor; okuyucu Bitti bildirir
                std::lock_guard<std::mutex> k(s->kilit);
                s->giden.clear();
                break;
            }
        }
        surec->YazmayiKapat();
    }

    bool Gonderim(Sureci& s, std::string_view govde) {
        std::string c;
        if (!mp::CerceveEkle(c, govde)) return false;
        {
            std::lock_guard<std::mutex> k(s.kilit);
            if (s.yazmayiBitir) return false;
            s.giden.push_back(std::move(c));
        }
        s.kosul.notify_one();
        return true;
    }

    // ------------------------------------------------------------------------------------------------ süreç yaşamı
    void SureciBaslat(Sureci& s) {
        s.hata.clear();
        s.python.clear();
        s.surumJson.clear();
        s.sonDurum.clear();
        s.hazirMs = 0;
        s.pid = 0;
        s.baslamaMs = SimdiMs();
        SurecAyari a;
        const std::string rol = RolAdi(s.rol);
        const unsigned cekirdek = std::max(2u, std::thread::hardware_concurrency());
        const int blas = s.rol == MotorRolu::Ana ? (ayar.anaBlasIs > 0 ? ayar.anaBlasIs : static_cast<int>(cekirdek) - 1) : 1;
        if (!ayar.pythonYolu.empty()) {
            a.program = ayar.pythonYolu;
            a.argumanlar = {"-X", "utf8", "-B", "-m", "op4_sunucu"};
            a.ortam = {{"PYTHONPATH", ayar.sunucuDizini}, {"PYTHONUTF8", "1"}, {"PYTHONDONTWRITEBYTECODE", "1"},
                       {"PYTHONNOUSERSITE", "1"}, {"PYTHONIOENCODING", "utf-8"}};
            a.calismaDizini = ayar.sunucuDizini.substr(0, ayar.sunucuDizini.find(kYolAyirici));
        } else if (!ayar.uygulamaDizini.empty()) {
            a.program = Utf8Yol(Yol(ayar.uygulamaDizini) / kMotorExe);
            a.calismaDizini = ayar.uygulamaDizini;
        }
        for (const char* x : {"--istek", "{istek}", "--yanit", "{yanit}", "--rol"}) a.argumanlar.emplace_back(x);
        a.argumanlar.push_back(rol);
        a.argumanlar.emplace_back("--blas");
        a.argumanlar.push_back(std::to_string(std::max(1, blas)));
        s.gunlukYolu.clear();
        if (!ayar.gunlukDizini.empty()) {
            std::error_code e;
            const std::filesystem::path d = Yol(ayar.gunlukDizini);
            static_cast<void>(std::filesystem::create_directories(d, e));
            const std::filesystem::path g = d / ("motor-" + rol + ".log");
            if (std::filesystem::exists(g, e)) std::filesystem::rename(g, d / ("motor-" + rol + ".onceki.log"), e);
            s.gunlukYolu = Utf8Yol(g);
            a.ciktiDosyasi = s.gunlukYolu;
            a.argumanlar.emplace_back("--gunluk");
            a.argumanlar.push_back(s.gunlukYolu);
        }
        a.bellekSiniriBayt = dis.bellekSiniriBayt;
        if (a.program.empty()) {
            s.hal = Hal::Basarisiz;
            s.hata = "Hesap motoru başlatılamadı: uygulama dizini (op4motor) ya da Python yolu verilmedi.";
            Yaz(s.hata);
            return;
        }
        s.surec = SurecOlustur();
        std::string hata;
        if (!s.surec->Baslat(a, hata)) {
            s.surec.reset();
            s.hal = Hal::Basarisiz;
            s.hata = "Hesap motoru başlatılamadı: " + hata;
            Yaz("motor (" + rol + "): " + s.hata);
            bildirimler.emplace_back(s.rol, "Hesap motoru başlatılamadı", 1.0f);
            return;
        }
        s.pid = s.surec->Kimlik();
        {
            std::lock_guard<std::mutex> k(s.kilit);
            s.giden.clear();
            s.gelen.clear();
            s.yazmayiBitir = false;
        }
        s.okuyucu = std::thread(&Ic::Okuyucu, &s, s.surec.get());
        s.yazici = std::thread(&Ic::Yazici, &s, s.surec.get());
        s.hal = Hal::Basliyor;
        Yaz("motor (" + rol + "): süreç başlatıldı, pid " + std::to_string(s.pid) + " — " + a.program +
            (s.gunlukYolu.empty() ? "" : "; günlük " + s.gunlukYolu));
        bildirimler.emplace_back(s.rol, "Hesap motoru başlatılıyor", 0.02f);
    }

    // İş parçacıklarını bitirir, süreci bırakır. zorla: önce sonlandır. Dönüş: çıkış kodu (bilinmiyorsa -1).
    int SureciKapat(Sureci& s, bool zorla, uint32_t beklemeMs) {
        if (!s.surec) return -1;
        {
            std::lock_guard<std::mutex> k(s.kilit);
            s.yazmayiBitir = true;
        }
        s.kosul.notify_all();
        int kod = -1;
        if (zorla) s.surec->Sonlandir();
        if (!s.surec->Bekle(beklemeMs, kod)) {
            s.surec->Sonlandir();
            s.surec->Bekle(5000, kod);
        }
        if (s.yazici.joinable()) s.yazici.join();
        if (s.okuyucu.joinable()) s.okuyucu.join();
        s.surec.reset();
        s.pid = 0;
        {
            std::lock_guard<std::mutex> k(s.kilit);
            s.giden.clear();
            s.gelen.clear();
        }
        return kod;
    }

    // Kendiliğinden yeniden başlatma (çökme ya da iptal zaman aşımı).
    void YenidenDene(Sureci& s, const std::string& neden) {
        const double simdi = SimdiMs();
        s.cokmeler.push_back(simdi);
        while (!s.cokmeler.empty() && simdi - s.cokmeler.front() > 60000) s.cokmeler.pop_front();
        if (static_cast<int>(s.cokmeler.size()) > dis.cokmeSiniri) {
            s.hal = Hal::Basarisiz;
            s.hata = "Hesap motoru 60 s içinde " + std::to_string(s.cokmeler.size()) +
                     " kez yeniden başlatıldı; kendiliğinden yeniden denenmeyecek (Analiz › Hesap motorunu yeniden başlat). "
                     "Son neden: " + neden;
            Yaz("motor (" + std::string(RolAdi(s.rol)) + "): " + s.hata);
            return;
        }
        ++s.yenidenBaslatma;
        Yaz("motor (" + std::string(RolAdi(s.rol)) + "): yeniden başlatılıyor — " + neden);
        SureciBaslat(s);
    }

    void SureciBitti(Sureci& s, const std::string& okumaHatasi) {
        const bool hazirdi = s.hal == Hal::Hazir;
        const int kod = SureciKapat(s, false, 2000);
        const std::string rol = RolAdi(s.rol);
        if (durduruldu) {
            HepsiniCoz(s, YanitDurumu::MotorHatasi, "motor_yok", "Hesap motoru kapatıldı.");
            s.hal = Hal::Yok;
            return;
        }
        if (!hazirdi) {
            if (s.hata.empty()) {
                s.hata = "Hesap motoru başlatılamadı (çıkış kodu " + std::to_string(kod) + ")";
                const std::string kuyruk = GunlukKuyrugu(s.gunlukYolu);
                if (!kuyruk.empty()) s.hata += ":\n" + kuyruk;
            }
            s.hal = Hal::Basarisiz;
            Yaz("motor (" + rol + "): " + s.hata);
            bildirimler.emplace_back(s.rol, "Hesap motoru başlatılamadı", 1.0f);
            HepsiniCoz(s, YanitDurumu::MotorHatasi, "motor_yok", s.hata);
            return;
        }
        const std::string ileti = "Hesap motoru beklenmedik biçimde kapandı (çıkış kodu " + std::to_string(kod) + ")" +
                                  (okumaHatasi.empty() ? "" : "; " + okumaHatasi) +
                                  ". İstek yarıda kaldı; motor yeniden başlatılıyor.";
        Yaz("motor (" + rol + "): " + ileti);
        HepsiniCoz(s, YanitDurumu::MotorHatasi, "motor_coktu", ileti);
        s.hal = Hal::Yok;
        YenidenDene(s, "çökme (çıkış kodu " + std::to_string(kod) + ")");
    }

    void Sonlandir(Sureci& s, const std::string& tur, const std::string& ileti) {
        SureciKapat(s, true, 2000);
        HepsiniCoz(s, YanitDurumu::MotorHatasi, tur, ileti);
        s.hal = Hal::Yok;
    }

    // ------------------------------------------------------------------------------------------------ olaylar
    void OlaylariIsle(Sureci& s) {
        std::deque<Olay> olaylar;
        {
            std::lock_guard<std::mutex> k(s.kilit);
            olaylar.swap(s.gelen);
        }
        const std::string rol = RolAdi(s.rol);
        for (Olay& o : olaylar) {
            if (!s.surec) break;  // önceki olay süreci bitirdi
            if (o.tur == Olay::Tur::Bitti) {
                SureciBitti(s, o.hata);
                break;
            }
            if (o.tur == Olay::Tur::Bozuk) {
                const std::string ileti = "Hesap motoruyla iletişim bozuldu (protokol hatası: " + o.hata + ").";
                Yaz("motor (" + rol + "): " + ileti);
                const bool hazirdi = s.hal == Hal::Hazir;
                Sonlandir(s, "protokol", ileti);
                if (hazirdi) YenidenDene(s, "protokol hatası");
                else {
                    s.hal = Hal::Basarisiz;
                    s.hata = ileti;
                }
                break;
            }
            mp::GelenIleti& i = o.ileti;
            switch (i.tur) {
                case mp::IletiTuru::Hazir:
                    s.hazirMs = SimdiMs() - s.baslamaMs;
                    s.python = i.python;
                    s.surumJson = i.surum;
                    if (i.basarili) {
                        s.hal = Hal::Hazir;
                        Yaz("motor (" + rol + "): hazır — Python " + i.python + ", " + std::to_string(static_cast<int>(s.hazirMs)) +
                            " ms (sunucu " + std::to_string(static_cast<int>(i.sureMs)) + " ms), pid " + std::to_string(i.pid) +
                            "; " + i.surum);
                        bildirimler.emplace_back(s.rol, "Hesap motoru hazır", 1.0f);
                    } else {
                        s.hal = Hal::Basarisiz;
                        s.hata = "Hesap motoru başlatılamadı: " + i.hata;
                        Yaz("motor (" + rol + "): " + s.hata);
                        bildirimler.emplace_back(s.rol, "Hesap motoru başlatılamadı", 1.0f);
                    }
                    break;
                case mp::IletiTuru::Durum:
                    s.sonDurum = i.metin;
                    bildirimler.emplace_back(s.rol, i.metin, static_cast<float>(std::clamp(i.oran, 0.0, 100.0) / 100.0));
                    break;
                case mp::IletiTuru::Gunluk:
                    Yaz("motor (" + rol + ") [" + i.duzey + "]: " + i.metin);
                    break;
                case mp::IletiTuru::Yanit: {
                    auto it = s.sunucuda.find(i.id);
                    if (it == s.sunucuda.end()) {
                        Yaz("motor (" + rol + "): eski / bilinmeyen id'li yanıt atıldı (" + std::to_string(i.id) + ")");
                        break;
                    }
                    Kayit k = std::move(it->second);
                    s.sunucuda.erase(it);
                    if (k.cozuldu) break;  // kuyruktayken iptal edilmişti; sunucunun onayı
                    MotorYaniti y;
                    y.yanit = std::move(i.yanit);
                    y.sureMs = i.sureMs;
                    YanitDurumuCoz(y);
                    if (k.iptal && y.durum != YanitDurumu::Iptal) y = IptalYaniti();  // iptal ile yanıt yarıştı
                    Coz(k, std::move(y));
                    break;
                }
                case mp::IletiTuru::Ilerleme:  // Faz 5: istek ilerlemesi (arayüz yok)
                case mp::IletiTuru::Bilinmiyor:
                    break;
            }
        }
    }

    void Zamanlayicilar() {
        const double simdi = SimdiMs();
        for (Sureci& s : surecler) {
            if (!s.surec) continue;
            if (s.hal == Hal::Basliyor && simdi - s.baslamaMs > dis.baslatmaZamanAsimiMs) {
                const std::string ileti = "Hesap motoru " + std::to_string(static_cast<int>(dis.baslatmaZamanAsimiMs / 1000)) +
                                          " s içinde hazır olmadı; süreç sonlandırıldı.";
                Yaz("motor (" + std::string(RolAdi(s.rol)) + "): " + ileti);
                Sonlandir(s, "motor_yok", ileti);
                s.hal = Hal::Basarisiz;
                s.hata = ileti;
                continue;
            }
            if (s.hal != Hal::Hazir || s.sunucuda.empty()) {
                s.onNo = 0;
                continue;
            }
            const auto& [no, k] = *s.sunucuda.begin();
            if (no != s.onNo) {
                s.onNo = no;
                s.onMs = simdi;
            }
            if (k.iptal && simdi - std::max(k.iptalMs, s.onMs) > ayar.iptalBeklemeMs) {
                const std::string ileti = "Hesap motoru iptalden sonra " +
                                          std::to_string(static_cast<int>(ayar.iptalBeklemeMs)) +
                                          " ms içinde yanıt vermedi; sonlandırılıp yeniden başlatıldı.";
                Yaz("motor (" + std::string(RolAdi(s.rol)) + "): istek " + std::to_string(no) + " — " + ileti);
                Sonlandir(s, "motor_yeniden", ileti);
                YenidenDene(s, "iptal zaman aşımı");
            }
        }
    }

    std::string AyarZenginlestir(std::string_view islem, const std::string& ayarlar) const {
        if (dis.sdSiniri <= 0 || islem.substr(0, 5) != "bina_") return ayarlar.empty() ? "{}" : ayarlar;
        nlohmann::json j = ayarlar.empty() ? nlohmann::json::object() : nlohmann::json::parse(ayarlar, nullptr, false);
        if (!j.is_object()) return ayarlar;  // bozuk: web_kopru öğretici hatasını verir
        if (!j.contains("sd_siniri")) j["sd_siniri"] = dis.sdSiniri;
        return j.dump(-1, ' ', false, nlohmann::json::error_handler_t::replace);
    }
};

MotorIstemcisi::MotorIstemcisi() : ic_(std::make_unique<Ic>(*this)) {}

MotorIstemcisi::~MotorIstemcisi() {
    ic_->durduruldu = true;
    for (Sureci& s : ic_->surecler) {
        if (!s.surec) continue;
        ic_->Gonderim(s, mp::KapatIletisi());
    }
    for (Sureci& s : ic_->surecler) ic_->SureciKapat(s, false, 2000);
    ic_->dagitim.clear();  // işleyiciler çağrılmaz
}

void MotorIstemcisi::Baslat(const MotorAyari& ayar) {
    if (ic_->baslatildi && !ic_->durduruldu) return;
    ic_->ayar = ayar;
    ic_->baslatildi = true;
    ic_->durduruldu = false;
    ic_->SureciBaslat(ic_->S(MotorRolu::Ana));
    if (!ayar.yardimciTembel) ic_->SureciBaslat(ic_->S(MotorRolu::Yardimci));
}

MotorDurumOzeti MotorIstemcisi::Durum(MotorRolu rol) const {
    const Sureci& s = ic_->surecler[rol == MotorRolu::Ana ? 0 : 1];
    MotorDurumOzeti d;
    d.baslatildi = rol == MotorRolu::Ana ? ic_->baslatildi : s.hal != Hal::Yok || s.yenidenBaslatma > 0;
    d.hazir = s.hal == Hal::Hazir || s.hal == Hal::Basarisiz;
    d.basarili = s.hal == Hal::Hazir;
    d.hata = s.hata;
    d.pythonSurumu = s.python;
    d.surumJson = s.surumJson;
    d.hazirMs = s.hazirMs;
    for (const auto& e : s.sunucuda) d.bekleyen += e.second.cozuldu ? 0u : 1u;
    d.calisiyor = s.hal == Hal::Hazir && !s.sunucuda.empty();
    d.yenidenBaslatma = s.yenidenBaslatma;
    switch (s.hal) {
        case Hal::Yok:
            d.aciklama = ic_->durduruldu ? "Hesap motoru kapatıldı" : "Hesap motoru başlatılmadı";
            break;
        case Hal::Basliyor:
            d.aciklama = "Hesap motoru başlatılıyor" + (s.sonDurum.empty() ? std::string() : " (" + s.sonDurum + ")");
            break;
        case Hal::Hazir:
            d.aciklama = "Hesap motoru hazır (Python " + s.python + ", " + std::to_string(static_cast<int>(s.hazirMs)) + " ms)";
            break;
        case Hal::Basarisiz:
            d.aciklama = "Hesap motoru başlatılamadı";
            break;
    }
    return d;
}

IstekNo MotorIstemcisi::Gonder(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                               YanitIsleyici isleyici) {
    Ic& c = *ic_;
    const IstekNo no = ++c.sonNo;
    std::string islemS(islem);
    if (!c.baslatildi || c.durduruldu) {
        c.HemenYanitla(no, std::move(islemS), std::move(isleyici),
                       Ic::HataYaniti(YanitDurumu::MotorHatasi, "motor_yok",
                                      c.durduruldu ? "Hesap motoru kapatıldı." : "Hesap motoru başlatılmadı."));
        return no;
    }
    Sureci& s = c.S(MotorRoluSec(islem));
    if (s.hal == Hal::Yok) c.SureciBaslat(s);  // yardımcı tembel (ilk istekte) ya da çökmeden sonra
    if (s.hal == Hal::Basarisiz || !s.surec) {
        c.HemenYanitla(no, std::move(islemS), std::move(isleyici),
                       Ic::HataYaniti(YanitDurumu::MotorHatasi, "motor_yok",
                                      s.hata.empty() ? "Hesap motoru başlatılamadı." : s.hata));
        return no;
    }
    const std::string istek = "{\"islem\":\"" + mp::JsonKacis(islem) + "\",\"girdi\":" + (girdi.empty() ? "{}" : girdi) +
                              ",\"ayarlar\":" + c.AyarZenginlestir(islem, ayarlar) + "}";
    Kayit k;
    k.no = no;
    k.islem = islemS;
    k.isleyici = std::move(isleyici);
    k.gonderimMs = SimdiMs();
    if (!c.Gonderim(s, mp::IstekIletisi(no, islem, istek))) {
        c.Coz(k, Ic::HataYaniti(YanitDurumu::MotorHatasi, "protokol",
                                "İstek gönderilemedi (çerçeve sınırı 512 MiB aşıldı ya da motor kapanıyor)."));
        return no;
    }
    s.sunucuda.emplace(no, std::move(k));
    return no;
}

bool MotorIstemcisi::Iptal(IstekNo no) {
    Ic& c = *ic_;
    for (Sureci& s : c.surecler) {
        auto it = s.sunucuda.find(no);
        if (it == s.sunucuda.end() || it->second.cozuldu) continue;
        Kayit& k = it->second;
        if (k.iptal) return true;
        k.iptal = true;
        k.iptalMs = SimdiMs();
        c.Gonderim(s, mp::IptalIletisi(no));
        const bool calisan = s.hal == Hal::Hazir && it == s.sunucuda.begin();
        if (!calisan) c.Coz(k, Ic::IptalYaniti());  // kuyrukta: hemen (sunucunun onayı sonra atılır)
        return true;
    }
    return false;
}

size_t MotorIstemcisi::Pompala() {
    Ic& c = *ic_;
    for (Sureci& s : c.surecler)
        if (s.surec) c.OlaylariIsle(s);
    c.Zamanlayicilar();
    auto bildirimler = std::move(c.bildirimler);
    c.bildirimler.clear();
    if (durumBildirimi)
        for (const auto& [rol, metin, oran] : bildirimler) durumBildirimi(rol, metin, oran);
    auto dagitim = std::move(c.dagitim);
    c.dagitim.clear();
    for (auto& [f, y] : dagitim)
        if (f) f(y);
    return dagitim.size();
}

MotorYaniti MotorIstemcisi::CalistirBekle(std::string_view islem, const std::string& girdi, const std::string& ayarlar,
                                          double zamanAsimiMs) {
    bool geldi = false;
    MotorYaniti sonuc;
    const IstekNo no = Gonder(islem, girdi, ayarlar, [&](const MotorYaniti& y) {
        sonuc = y;
        geldi = true;
    });
    const double bas = SimdiMs();
    bool doldu = false;
    while (!geldi) {
        Pompala();
        if (geldi) break;
        if (!doldu && SimdiMs() - bas > zamanAsimiMs) {
            doldu = true;
            Iptal(no);  // kuyruktaysa hemen, çalışıyorsa en geç iptalBeklemeMs sonra (süreç sonlandırılarak) yanıtlanır
            continue;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    if (doldu) {
        sonuc.durum = YanitDurumu::MotorHatasi;
        sonuc.hata = "Süre doldu (" + std::to_string(static_cast<long long>(zamanAsimiMs)) + " ms); istek iptal edildi.";
        if (sonuc.hataTuru.empty()) sonuc.hataTuru = "iptal";
    }
    return sonuc;
}

void MotorIstemcisi::Durdur() {
    Ic& c = *ic_;
    if (!c.durduruldu) {
        c.durduruldu = true;
        for (Sureci& s : c.surecler)
            if (s.surec) c.Gonderim(s, mp::KapatIletisi());
        const double bas = SimdiMs();
        for (Sureci& s : c.surecler) {
            if (!s.surec) continue;
            const double kalan = std::max(0.0, 2000.0 - (SimdiMs() - bas));
            const int kod = c.SureciKapat(s, false, static_cast<uint32_t>(kalan));
            c.Yaz("motor (" + std::string(RolAdi(s.rol)) + "): kapatıldı (çıkış kodu " + std::to_string(kod) + ")");
        }
        for (Sureci& s : c.surecler) {
            c.HepsiniCoz(s, YanitDurumu::MotorHatasi, "motor_yok", "Hesap motoru kapatıldı.");
            s.hal = Hal::Yok;
        }
    }
    Pompala();  // Y1: bekleyen her isteğin işleyicisi bir kez çağrılır
}

void MotorIstemcisi::YenidenBaslat() {
    Ic& c = *ic_;
    for (Sureci& s : c.surecler) {
        const bool vardi = s.surec != nullptr || s.hal != Hal::Yok;
        if (s.surec) c.Sonlandir(s, "motor_yeniden", "Hesap motoru yeniden başlatıldı; istek yarıda kaldı.");
        s.hal = Hal::Yok;
        s.hata.clear();
        s.cokmeler.clear();
        if (vardi) ++s.yenidenBaslatma;
    }
    if (!c.baslatildi) return;
    c.durduruldu = false;
    c.Yaz("motor: yeniden başlatılıyor (komut)");
    c.SureciBaslat(c.S(MotorRolu::Ana));
}

long long MotorIstemcisi::SurecKimligi(MotorRolu rol) const {
    const Sureci& s = ic_->surecler[rol == MotorRolu::Ana ? 0 : 1];
    return s.surec ? s.pid : 0;
}

std::string MotorIstemcisi::GunlukYolu(MotorRolu rol) const { return ic_->surecler[rol == MotorRolu::Ana ? 0 : 1].gunlukYolu; }

std::unique_ptr<MotorHizmeti> MotorIstemcisiOlustur() { return std::make_unique<MotorIstemcisi>(); }

}  // namespace op4
