// A sınamaları: süreç tabanlı hesap motoru istemcisi (cekirdek/motor_istemci.h; S12, S13) ↔ `python -m op4_sunucu`
// (MIMARI §8; kabul A8). Çoğu sınama sahte motoru (op4/testler/python/sahte_motor/web_kopru.py, yalnız standart kitaplık)
// kullanır; "gerçek motor" sınaması docs/web_kopru.py'yi numpy + sympy ile çalıştırır.
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cstdio>
#include <fstream>
#include <map>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "cekirdek/motor_istemci.h"
#include "cekirdek/motor_protokol.h"
#include "motor_sinama_yardim.h"

using namespace op4;
using nlohmann::json;
namespace sn = op4::sinama;

namespace {

// Gönderilen isteklerin yanıtlarını toplar; her işleyicinin tam bir kez çağrıldığını denetler (Y1).
struct Toplayici {
    std::map<IstekNo, MotorYaniti> yanit;
    std::map<IstekNo, int> cagri;
    std::vector<IstekNo> sira;
    YanitIsleyici Isleyici() {
        return [this](const MotorYaniti& y) {
            ++cagri[y.no];
            yanit[y.no] = y;
            sira.push_back(y.no);
        };
    }
    bool Geldi(IstekNo no) const { return yanit.count(no) != 0; }
};

std::string Girdi(const json& j) { return j.dump(); }

std::string DosyaOku(const std::string& yol) {
    std::ifstream f(std::filesystem::path(std::u8string(reinterpret_cast<const char8_t*>(yol.c_str()))), std::ios::binary);
    std::stringstream s;
    s << f.rdbuf();
    return s.str();
}

void Olcum(const std::string& satir) {
    std::printf("OP4OLCUM %s\n", satir.c_str());
    std::fflush(stdout);
}

}  // namespace

TEST_CASE("A8 istemci: hazır, durum bildirimleri, istek / yanıt, sıra, yönlendirme (tembel yardımcı)") {
    if (!sn::PythonVar()) return;
    sn::GeciciDizin d("istemci");
    MotorIstemcisi m;
    std::vector<std::string> gunluk;
    m.gunluk = [&](std::string_view s) { gunluk.emplace_back(s); };
    std::vector<std::pair<std::string, float>> bildirim;
    m.durumBildirimi = [&](MotorRolu r, const std::string& metin, float oran) {
        if (r == MotorRolu::Ana) bildirim.emplace_back(metin, oran);
    };
    MotorAyari a = sn::SahteAyar();
    a.gunlukDizini = d.Utf8();
    const double t0 = sn::SimdiMs();
    m.Baslat(a);
    CHECK(m.Durum().baslatildi);
    CHECK_FALSE(m.Durum(MotorRolu::Yardimci).baslatildi);
    CHECK(m.SurecKimligi(MotorRolu::Ana) > 0);
    CHECK(m.SurecKimligi(MotorRolu::Yardimci) == 0);
    REQUIRE(sn::HazirBekle(m));
    const double hazirMs = sn::SimdiMs() - t0;
    const MotorDurumOzeti ds = m.Durum();
    CHECK(ds.basarili);
    CHECK(ds.hata.empty());
    CHECK_FALSE(ds.pythonSurumu.empty());
    CHECK(json::parse(ds.surumJson)["motor"] == "sahte-1");
    CHECK(ds.aciklama.rfind("Hesap motoru hazır (Python ", 0) == 0u);
    CHECK(ds.hazirMs > 0);
    REQUIRE(bildirim.size() >= 3u);
    CHECK(bildirim.back().first == "Hesap motoru hazır");
    CHECK(bildirim.back().second == doctest::Approx(1.0));
    for (size_t i = 1; i < bildirim.size(); ++i) CHECK(bildirim[i].second >= bildirim[i - 1].second);
    Olcum("senaryo=motor_istemci sahte_hazir_ms=" + std::to_string(hazirMs));

    Toplayici t;
    std::vector<IstekNo> nolar;
    const std::string metin = "Ş\"ğ\\ı\n\t — çözüm";
    const double g0 = sn::SimdiMs();
    for (int i = 0; i < 20; ++i)
        nolar.push_back(m.Gonder("bina_coz", Girdi({{"i", i}, {"metin", metin}}), "{\"anlat\":false}", t.Isleyici()));
    CHECK(t.cagri.empty());  // işleyiciler yalnız Pompala içinde
    REQUIRE(sn::PompalaBekle(m, [&] { return t.yanit.size() == nolar.size(); }));
    Olcum("senaryo=motor_istemci gidis_donus_20_ms=" + std::to_string(sn::SimdiMs() - g0));
    CHECK(t.sira == nolar);  // Y2
    for (size_t i = 0; i < nolar.size(); ++i) {
        const MotorYaniti& y = t.yanit[nolar[i]];
        CHECK(t.cagri[nolar[i]] == 1);
        // bina_coz → ana motor; sahte motor bina_coz'u tanımaz: web_kopru biçiminde "girdi" hatası
        CHECK(y.durum == YanitDurumu::Hata);
        CHECK(y.hataTuru == "girdi");
        CHECK(y.islem == "bina_coz");
        CHECK(y.toplamMs >= y.sureMs);
    }
    CHECK(m.SurecKimligi(MotorRolu::Yardimci) == 0);  // ana işlemler yardımcıyı başlatmaz
    // yardımcı ilk isteğinde başlar
    const IstekNo y1 = m.Gonder("yanki", Girdi({{"metin", metin}}), "", t.Isleyici());
    CHECK(m.SurecKimligi(MotorRolu::Yardimci) > 0);
    CHECK(m.SurecKimligi(MotorRolu::Yardimci) != m.SurecKimligi(MotorRolu::Ana));
    REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(y1); }));
    CHECK(t.yanit[y1].durum == YanitDurumu::Tamam);
    CHECK(json::parse(t.yanit[y1].yanit)["girdi"]["metin"] == metin);
    CHECK(m.Durum(MotorRolu::Yardimci).basarili);
    CHECK(m.Durum().bekleyen == 0u);
    m.Durdur();
    CHECK(m.SurecKimligi(MotorRolu::Ana) == 0);
    // günlük dosyası: sunucunun satırları
    CHECK(DosyaOku(m.GunlukYolu(MotorRolu::Ana)).find("hazır") != std::string::npos);
    CHECK(DosyaOku(m.GunlukYolu(MotorRolu::Yardimci)).find("istek " + std::to_string(y1) + " yanki") != std::string::npos);
    // Durdur'dan sonra istek: hemen motor_yok
    const IstekNo sonra = m.Gonder("yanki", "{}", "{}", t.Isleyici());
    CHECK(m.Pompala() == 1u);
    CHECK(t.yanit[sonra].durum == YanitDurumu::MotorHatasi);
    CHECK(t.yanit[sonra].hataTuru == "motor_yok");
}

TEST_CASE("A8 iptal: kuyruktaki hemen, çalışan KeyboardInterrupt ile; geç ve bilinmeyen iptal") {
    if (!sn::PythonVar()) return;
    MotorIstemcisi m;
    m.Baslat(sn::SahteAyar());
    Toplayici t;
    // sahte işlemler yardımcı motora gider (ilk istek onu başlatır)
    const IstekNo ilk = m.Gonder("yanki", "{}", "{}", t.Isleyici());
    REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(ilk); }));
    const IstekNo uzun = m.Gonder("uyu", Girdi({{"s", 30}}), "{}", t.Isleyici());
    const IstekNo kuyruk = m.Gonder("yanki", Girdi({{"k", 1}}), "{}", t.Isleyici());
    const IstekNo sonraki = m.Gonder("yanki", Girdi({{"k", 2}}), "{}", t.Isleyici());
    CHECK(m.Iptal(kuyruk));
    CHECK_FALSE(m.Iptal(kuyruk));  // kuyruktaki iptal hemen çözüldü: artık "bitmiş" (sözleşme: false)
    m.Pompala();
    REQUIRE(t.Geldi(kuyruk));
    CHECK(t.yanit[kuyruk].durum == YanitDurumu::Iptal);
    CHECK(t.yanit[kuyruk].hataTuru == "iptal");
    CHECK(json::parse(t.yanit[kuyruk].yanit)["hata_turu"] == "iptal");
    // çalışan isteğin iptali
    std::this_thread::sleep_for(std::chrono::milliseconds(300));
    m.Pompala();
    CHECK(m.Durum(MotorRolu::Yardimci).calisiyor);
    const double t0 = sn::SimdiMs();
    CHECK(m.Iptal(uzun));
    REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(uzun); }, 5000));
    const double iptalMs = sn::SimdiMs() - t0;
    CHECK(iptalMs < 2000);
    CHECK(t.yanit[uzun].durum == YanitDurumu::Iptal);
    Olcum("senaryo=motor_istemci calisan_iptal_ms=" + std::to_string(iptalMs));
    REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(sonraki); }));
    CHECK(t.yanit[sonraki].durum == YanitDurumu::Tamam);
    CHECK(json::parse(t.yanit[sonraki].yanit)["girdi"]["k"] == 2);
    // sunucunun kuyruk iptali onayı geldiğinde işleyici ikinci kez çağrılmaz
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    m.Pompala();
    for (const auto& [no, n] : t.cagri) CHECK_MESSAGE(n == 1, "istek ", no);
    CHECK_FALSE(m.Iptal(sonraki));
    CHECK_FALSE(m.Iptal(987654));
    CHECK(m.Durum(MotorRolu::Yardimci).yenidenBaslatma == 0);
}

TEST_CASE("A8 iptale yanıt vermeyen motor: iptalBeklemeMs sonra sonlandırılıp yeniden başlatılır (motor_yeniden)") {
    if (!sn::PythonVar()) return;
    MotorIstemcisi m;
    m.Baslat(sn::SahteAyar(600));
    Toplayici t;
    const IstekNo kilit = m.Gonder("kilitlen", Girdi({{"s", 60}}), "{}", t.Isleyici());
    const IstekNo arkada = m.Gonder("yanki", "{}", "{}", t.Isleyici());
    REQUIRE(sn::PompalaBekle(m, [&] { return m.Durum(MotorRolu::Yardimci).hazir; }));
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    const long long pid = m.SurecKimligi(MotorRolu::Yardimci);
    const double t0 = sn::SimdiMs();
    CHECK(m.Iptal(kilit));
    REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(kilit) && t.Geldi(arkada); }, 10000));
    const double gecen = sn::SimdiMs() - t0;
    CHECK(gecen >= 550);
    CHECK(gecen < 5000);
    CHECK(t.yanit[kilit].durum == YanitDurumu::Iptal);
    CHECK(t.yanit[arkada].durum == YanitDurumu::MotorHatasi);
    CHECK(t.yanit[arkada].hataTuru == "motor_yeniden");
    CHECK(m.Durum(MotorRolu::Yardimci).yenidenBaslatma == 1);
    REQUIRE(sn::PompalaBekle(m, [&] { return m.Durum(MotorRolu::Yardimci).basarili; }));
    CHECK(m.SurecKimligi(MotorRolu::Yardimci) != pid);
    const MotorYaniti y = m.CalistirBekle("yanki", Girdi({{"yeni", true}}), "", 10000);
    CHECK(y.durum == YanitDurumu::Tamam);
    Olcum("senaryo=motor_istemci yeniden_baslatma_ms=" + std::to_string(gecen));
}

TEST_CASE("A8 çökme: bekleyenlere motor_coktu, kendiliğinden yeniden başlatma, çökme sınırı") {
    if (!sn::PythonVar()) return;
    MotorIstemcisi m;
    m.cokmeSiniri = 2;
    m.Baslat(sn::SahteAyar());
    Toplayici t;
    const IstekNo cok = m.Gonder("cok", Girdi({{"kod", 7}}), "{}", t.Isleyici());
    const IstekNo arkada = m.Gonder("yanki", "{}", "{}", t.Isleyici());
    REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(cok) && t.Geldi(arkada); }));
    CHECK(t.yanit[cok].durum == YanitDurumu::MotorHatasi);
    CHECK(t.yanit[cok].hataTuru == "motor_coktu");
    CHECK(t.yanit[cok].hata.find("çıkış kodu 7") != std::string::npos);
    CHECK(json::parse(t.yanit[cok].yanit)["hata_turu"] == "motor_coktu");
    CHECK(t.yanit[arkada].hataTuru == "motor_coktu");
    CHECK(m.Durum(MotorRolu::Yardimci).yenidenBaslatma == 1);
    MotorYaniti y = m.CalistirBekle("yanki", "{}", "", 20000);
    CHECK(y.durum == YanitDurumu::Tamam);
    // sınır: 60 s içinde 3. çökmeden sonra kendiliğinden başlatılmaz
    for (int i = 0; i < 2; ++i) CHECK(m.CalistirBekle("cok", "{}", "", 20000).hataTuru == "motor_coktu");
    CHECK_FALSE(m.Durum(MotorRolu::Yardimci).basarili);
    CHECK(m.Durum(MotorRolu::Yardimci).hata.find("kendiliğinden yeniden denenmeyecek") != std::string::npos);
    y = m.CalistirBekle("yanki", "{}", "", 5000);
    CHECK(y.hataTuru == "motor_yok");
    // motor.yeniden_baslat
    m.YenidenBaslat();
    y = m.CalistirBekle("yanki", "{}", "", 20000);
    CHECK(y.durum == YanitDurumu::Tamam);
}

TEST_CASE("A8 50 MB yanıt, print'ler protokolü bozmaz, sd_siniri eklenir, büyük istek") {
    if (!sn::PythonVar()) return;
    sn::GeciciDizin d("buyuk");
    MotorIstemcisi m;
    m.sdSiniri = 6000;
    MotorAyari a = sn::SahteAyar();
    a.gunlukDizini = d.Utf8();
    m.Baslat(a);
    const double t0 = sn::SimdiMs();
    MotorYaniti y = m.CalistirBekle("buyuk", Girdi({{"mb", 50}}), "", 60000);
    const double ms = sn::SimdiMs() - t0;
    REQUIRE(y.durum == YanitDurumu::Tamam);
    CHECK(y.yanit.size() >= size_t{50} * 1024 * 1024);
    const json j = json::parse(y.yanit);
    CHECK(j["veri"].get<std::string>().size() == j["boyut"].get<size_t>() / 2 * 2);  // 'ş' = 2 bayt
    Olcum("senaryo=motor_istemci yanit_mb=50 sure_ms=" + std::to_string(ms));
    y = m.CalistirBekle("yazdir", "{}", "", 10000);
    CHECK(y.durum == YanitDurumu::Tamam);
    y = m.CalistirBekle("yanki", Girdi({{"sonra", 1}}), "", 10000);
    CHECK(json::parse(y.yanit)["girdi"]["sonra"] == 1);
    const std::string g = DosyaOku(m.GunlukYolu(MotorRolu::Yardimci));
    CHECK(g.find("fd1 ham bayt") != std::string::npos);
    CHECK(g.find("print: stdout") != std::string::npos);
    // sd_siniri yalnız bina_ isteklerine ve yoksa eklenir
    y = m.CalistirBekle("bina_yanki", "{}", "{\"anlat\":false}", 10000);
    CHECK(json::parse(y.yanit)["ayarlar"] == json({{"anlat", false}, {"sd_siniri", 6000}}));
    y = m.CalistirBekle("bina_yanki", "{}", "{\"sd_siniri\":100}", 10000);
    CHECK(json::parse(y.yanit)["ayarlar"]["sd_siniri"] == 100);
    y = m.CalistirBekle("yanki", "{}", "", 10000);
    CHECK(json::parse(y.yanit)["ayarlar"] == json::object());
    // büyük istek (10 MB girdi) yazıcı iş parçacığından geçer
    const std::string buyukMetin(10u << 20, 'a');
    y = m.CalistirBekle("yanki", Girdi({{"m", buyukMetin}}), "", 60000);
    CHECK(json::parse(y.yanit)["girdi"]["m"].get<std::string>().size() == buyukMetin.size());
    m.Durdur();
    // ikinci oturum: önceki günlük *.onceki.log olarak kalır
    MotorIstemcisi m2;
    m2.Baslat(a);
    CHECK(m2.CalistirBekle("yanki", "{}", "", 20000).durum == YanitDurumu::Tamam);
    CHECK(std::filesystem::exists(d.yol / "motor-yardimci.onceki.log"));
}

TEST_CASE("A8 Y1 karışık yük: rastgele iptal, her isteğe tam bir yanıt") {
    if (!sn::PythonVar()) return;
    MotorIstemcisi m;
    m.Baslat(sn::SahteAyar());
    Toplayici t;
    std::mt19937 r(42);
    std::vector<IstekNo> nolar;
    for (int i = 0; i < 150; ++i) {
        const int tur = static_cast<int>(r() % 3);
        const IstekNo no = tur == 0 ? m.Gonder("uyu", Girdi({{"s", 0.002 * static_cast<double>(r() % 5)}}), "", t.Isleyici())
                                    : m.Gonder(tur == 1 ? "yanki" : "bina_coz", Girdi({{"i", i}}), "", t.Isleyici());
        nolar.push_back(no);
        if (r() % 4 == 0) m.Iptal(nolar[r() % nolar.size()]);
        if (r() % 8 == 0) m.Pompala();
    }
    REQUIRE(sn::PompalaBekle(m, [&] { return t.yanit.size() == nolar.size(); }, 30000));
    for (const IstekNo no : nolar) CHECK(t.cagri[no] == 1);
    std::this_thread::sleep_for(std::chrono::milliseconds(300));
    m.Pompala();
    CHECK(t.sira.size() == nolar.size());
    CHECK(m.Durum().bekleyen == 0u);
    CHECK(m.Durum(MotorRolu::Yardimci).bekleyen == 0u);
}

TEST_CASE("A8 başlatma hataları: içe aktarma hatası, olmayan program, boş ayar; Durdur ve yıkıcı") {
    if (!sn::PythonVar()) return;
    {
        sn::OrtamAyarla("OP4_SAHTE_MOTOR_ICE_AKTARMA_HATASI", "1");
        MotorIstemcisi m;
        m.Baslat(sn::SahteAyar());
        Toplayici t;
        const IstekNo no = m.Gonder("bina_coz", "{}", "{}", t.Isleyici());
        REQUIRE(sn::HazirBekle(m));
        sn::OrtamAyarla("OP4_SAHTE_MOTOR_ICE_AKTARMA_HATASI", nullptr);
        REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(no); }));
        CHECK_FALSE(m.Durum().basarili);
        CHECK(m.Durum().hata.find("içe aktarılamadı") != std::string::npos);
        CHECK(t.yanit[no].hataTuru == "motor_yok");
        CHECK(m.CalistirBekle("bina_coz", "{}", "", 5000).hataTuru == "motor_yok");
    }
    {
        MotorIstemcisi m;
        MotorAyari a;
        sn::GeciciDizin d("bos");
        a.uygulamaDizini = d.Utf8();  // op4motor yok
        m.Baslat(a);
        CHECK(m.Durum().hazir);
        CHECK_FALSE(m.Durum().basarili);
        CHECK(m.Durum().hata.find("bulunamadı") != std::string::npos);
        CHECK(m.CalistirBekle("bina_coz", "{}", "", 5000).hataTuru == "motor_yok");
    }
    {
        // Durdur: bekleyenlere motor_yok, süreç hızla kapanır
        MotorIstemcisi m;
        m.Baslat(sn::SahteAyar());
        Toplayici t;
        const IstekNo uzun = m.Gonder("uyu", Girdi({{"s", 30}}), "{}", t.Isleyici());
        const IstekNo arkada = m.Gonder("yanki", "{}", "{}", t.Isleyici());
        REQUIRE(sn::PompalaBekle(m, [&] { return m.Durum(MotorRolu::Yardimci).hazir; }));
        const double t0 = sn::SimdiMs();
        m.Durdur();
        CHECK(sn::SimdiMs() - t0 < 4500);
        REQUIRE(t.Geldi(uzun));
        REQUIRE(t.Geldi(arkada));
        CHECK(t.yanit[uzun].hataTuru == "motor_yok");
        CHECK(t.yanit[arkada].hata == "Hesap motoru kapatıldı.");
        m.Durdur();  // ikinci kez zararsız
    }
    {
        // Yıkıcı: işleyiciler çağrılmaz, asılı kalmaz
        int cagri = 0;
        const double t0 = sn::SimdiMs();
        {
            MotorIstemcisi m;
            m.Baslat(sn::SahteAyar());
            m.Gonder("uyu", Girdi({{"s", 30}}), "{}", [&](const MotorYaniti&) { ++cagri; });
            sn::PompalaBekle(m, [&] { return m.Durum(MotorRolu::Yardimci).hazir; });
        }
        CHECK(cagri == 0);
        CHECK(sn::SimdiMs() - t0 < 10000);
    }
    {
        // YenidenBaslat: bekleyenlere motor_yeniden
        MotorIstemcisi m;
        m.Baslat(sn::SahteAyar());
        Toplayici t;
        const IstekNo uzun = m.Gonder("bina_coz", "{}", "{}", t.Isleyici());
        const IstekNo yrd = m.Gonder("uyu", Girdi({{"s", 30}}), "{}", t.Isleyici());
        REQUIRE(sn::HazirBekle(m));
        REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(uzun); }));
        const long long pid = m.SurecKimligi(MotorRolu::Ana);
        m.YenidenBaslat();
        m.Pompala();
        REQUIRE(t.Geldi(yrd));
        CHECK(t.yanit[yrd].hataTuru == "motor_yeniden");
        CHECK(m.SurecKimligi(MotorRolu::Ana) != pid);
        CHECK(m.SurecKimligi(MotorRolu::Yardimci) == 0);
        REQUIRE(sn::HazirBekle(m));
        CHECK(m.Durum().basarili);
        CHECK(m.Durum().yenidenBaslatma == 1);
    }
}

TEST_CASE("A8 CalistirBekle: süre dolunca iptal eder ve MotorHatasi döner") {
    if (!sn::PythonVar()) return;
    MotorIstemcisi m;
    m.Baslat(sn::SahteAyar());
    REQUIRE(m.CalistirBekle("yanki", "{}", "", 20000).durum == YanitDurumu::Tamam);
    const double t0 = sn::SimdiMs();
    const MotorYaniti y = m.CalistirBekle("uyu", Girdi({{"s", 30}}), "", 300);
    CHECK(sn::SimdiMs() - t0 < 3000);
    CHECK(y.durum == YanitDurumu::MotorHatasi);
    CHECK(y.hata.find("Süre doldu") != std::string::npos);
    CHECK(m.CalistirBekle("yanki", "{}", "", 10000).durum == YanitDurumu::Tamam);
}

TEST_CASE("A8 gerçek motor: web_kopru (numpy, sympy) ana + yardımcı, bina_kimlik, anlatımsız çözüm, iptal") {
    if (!sn::GercekMotorVar()) return;
    MotorIstemcisi m;
    m.sdSiniri = 6000;
    MotorAyari a;
    a.pythonYolu = sn::PythonYolu();
    a.sunucuDizini = sn::GercekMotorDizini();
    const double t0 = sn::SimdiMs();
    m.Baslat(a);
    REQUIRE(sn::HazirBekle(m, MotorRolu::Ana, 120000));
    REQUIRE_MESSAGE(m.Durum().basarili, m.Durum().hata);
    const double hazir = sn::SimdiMs() - t0;
    const json surum = json::parse(m.Durum().surumJson);
    CHECK(surum.contains("numpy"));
    CHECK(surum.contains("sympy"));
    MotorYaniti y = m.CalistirBekle("determinant", Girdi({{"girdi_yok", 0}, {"A", "2 1; 1 3"}}), "", 120000);
    REQUIRE(y.durum == YanitDurumu::Tamam);
    CHECK(json::parse(y.yanit)["sonuc_metin"] == "5");
    y = m.CalistirBekle("bina_sablonlar", "", "", 60000);
    CHECK(json::parse(y.yanit)["sablonlar"].size() >= 9u);
    y = m.CalistirBekle("bina_sablon", Girdi({{"ad", "betonarme-tek-aciklik"}}), "", 60000);
    const json bina = json::parse(y.yanit)["bina"];
    y = m.CalistirBekle("bina_kimlik", Girdi({{"bina", bina}}), "", 60000);
    REQUIRE(y.durum == YanitDurumu::Tamam);
    const std::string kimlik = json::parse(y.yanit)["cozum_kimligi"];
    const double c0 = sn::SimdiMs();
    y = m.CalistirBekle("bina_coz", Girdi({{"bina", bina}}), "{\"anlat\":false}", 120000);
    const double cozMs = sn::SimdiMs() - c0;
    REQUIRE(y.durum == YanitDurumu::Tamam);
    const json c = json::parse(y.yanit);
    CHECK(c["bloklar"].empty());
    CHECK(c["veri"]["cozum_kimligi"] == kimlik);
    // hata yanıtı
    y = m.CalistirBekle("bina_sablon", Girdi({{"ad", "boyle-sablon-yok"}}), "", 60000);
    CHECK(y.durum == YanitDurumu::Hata);
    CHECK(y.hataTuru == "girdi");
    // büyük çözüm hesap ortasında iptal
    y = m.CalistirBekle("bina_sablon", Girdi({{"ad", "celik-sanayi-4hol"}}), "", 60000);
    const json buyuk = json::parse(y.yanit)["bina"];
    Toplayici t;
    const IstekNo no = m.Gonder("bina_coz", Girdi({{"bina", buyuk}}), "{\"anlat\":true}", t.Isleyici());
    sn::PompalaBekle(m, [&] { return false; }, 1000);
    const double i0 = sn::SimdiMs();
    CHECK(m.Iptal(no));
    REQUIRE(sn::PompalaBekle(m, [&] { return t.Geldi(no); }, 10000));
    const double iptalMs = sn::SimdiMs() - i0;
    CHECK(t.yanit[no].durum == YanitDurumu::Iptal);
    CHECK(m.Durum().yenidenBaslatma == 0);  // KeyboardInterrupt ile; süreç sonlandırılmadı
    CHECK(m.CalistirBekle("bina_kimlik", Girdi({{"bina", bina}}), "", 60000).durum == YanitDurumu::Tamam);
    Olcum("senaryo=motor_istemci_gercek ana_hazir_ms=" + std::to_string(hazir) + " yardimci_hazir_ms=" +
          std::to_string(m.Durum(MotorRolu::Yardimci).hazirMs) + " tek_aciklik_coz_ms=" + std::to_string(cozMs) +
          " iptal_ms=" + std::to_string(iptalMs));
    m.Durdur();
}
