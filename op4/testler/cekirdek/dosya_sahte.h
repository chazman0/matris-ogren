// op4 C++ sınamaları (D: dosya-cozum) — sahte model çekirdeği, sahte hesap motoru, geçici klasör ve Hizmetler düzeneği.
// Sahte çekirdek model metnini OLDUĞU GİBİ saklar (Metin() = Yukle'ye verilen baytlar); böylece .op4 gidiş-dönüşünde
// "model/bina.json, Metin() ile bayt bayt aynı" denetimi çekirdeğin kanonikleştirmesinden bağımsız sınanır.
#pragma once

#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <atomic>
#include <deque>
#include <filesystem>
#include <memory>
#include <string>
#include <vector>

#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/cozum_akisi.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/hizmetler.h"
#include "cekirdek/komut.h"
#include "cekirdek/model_cekirdegi.h"
#include "cekirdek/motor_hizmeti.h"
#include "cekirdek/motor_protokol.h"
#include "cekirdek/proje_belgesi.h"
#include "cekirdek/proje_islemleri.h"
#include "cekirdek/proje_zip.h"
#include "cekirdek/secim.h"
#include "cekirdek/sonuc.h"
#include "cekirdek/sonuc_ek.h"
#include "cekirdek/turkce.h"
#include "platform/dosya_sistemi.h"
#include "platform/dosya_sistemi_atomik.h"
#include "sinama_yardim.h"

namespace op4::sinama {

inline std::filesystem::path U8Yol(const std::string& s) {
    return std::filesystem::path(std::u8string(reinterpret_cast<const char8_t*>(s.data()), s.size()));
}
inline std::string U8(const std::filesystem::path& p) {
    const std::u8string s = p.u8string();
    return std::string(reinterpret_cast<const char*>(s.data()), s.size());
}

// Sınama başına benzersiz, Türkçe karakterli geçici klasör; yıkıcı siler.
class GeciciDizin {
public:
    GeciciDizin() {
        static std::atomic<int> sayac{0};
        kok_ = std::filesystem::temp_directory_path() /
               U8Yol("op4 D sınama ŞĞİı " + std::to_string(SurecNo()) + "-" + std::to_string(++sayac));
        std::filesystem::remove_all(kok_);
        std::filesystem::create_directories(kok_);
    }
    ~GeciciDizin() {
        std::error_code e;
        std::filesystem::remove_all(kok_, e);
    }
    std::string Yol(const std::string& goreli = {}) const { return goreli.empty() ? U8(kok_) : U8(kok_ / U8Yol(goreli)); }
    std::string Kur(const std::string& goreli) const {
        std::filesystem::create_directories(kok_ / U8Yol(goreli));
        return Yol(goreli);
    }

private:
    std::filesystem::path kok_;
};

inline std::string DosyaIcerigi(const std::string& yol) {
    std::string v, h;
    DosyaOku(yol, v, h);
    return v;
}
inline void DosyaYaz(const std::string& yol, const std::string& veri) {
    std::string h;
    REQUIRE_MESSAGE(AtomikYaz(yol, veri, false, h), h);
}

class SahteCekirdek final : public ModelCekirdegi {
public:
    std::string model;
    uint64_t surum = 0;
    bool eslemeVar = false;
    int ifcCagri = 0;
    std::string sonIfcSecenek, sonIfcVeri;
    SahnePtr sahne = OrnekSahneAnlik();

    YuklemeSonucu YeniBos(std::string_view baslik) override {
        model = nlohmann::ordered_json{{"tur", "bina"}, {"surum", 3}, {"baslik", baslik.empty() ? "Adsız 1" : std::string(baslik)},
                                       {"dugumler", nlohmann::json::array()}, {"cubuklar", nlohmann::json::array()}}
                    .dump();
        ++surum;
        return {true, "", Ozet(), {}};
    }
    YuklemeSonucu Yukle(std::string_view metin, std::string_view kaynak) override {
        const nlohmann::json j = nlohmann::json::parse(metin, nullptr, false);
        if (j.is_discarded() || !j.is_object() || j.value("tur", std::string()) != "bina")
            return {false, "Bina modeli okunamadı: " + std::string(kaynak), {}, {}};
        while (!metin.empty() && (metin.back() == '\n' || metin.back() == '\r' || metin.back() == ' ')) metin.remove_suffix(1);
        model.assign(metin);  // kanonik metinde sonda satır sonu yok
        ++surum;
        return {true, "", Ozet(), {}};
    }
    IslemRaporu Uygula(std::string_view islem, const JsonMetni& p) override {
        IslemRaporu r;
        r.islem = std::string(islem);
        if (islem != islem::BASLIK_DEGISTIR) {
            r.hata = "sahte çekirdek: işlem yok";
            return r;
        }
        nlohmann::ordered_json j = nlohmann::ordered_json::parse(model);
        j["baslik"] = nlohmann::json::parse(p).value("baslik", std::string("?"));
        model = j.dump();
        r.basarili = true;
        r.degisen = {CubukKimligi(1)};
        r.sahneSurumu = ++surum;
        return r;
    }
    IslemRaporu GeriAl() override { return {}; }
    IslemRaporu Yinele() override { return {}; }
    GeriAlDurumu GeriAlBilgisi() const override { return {}; }
    std::vector<std::string> IslemAdlari() const override { return {islem::BASLIK_DEGISTIR}; }
    SahnePtr Sahne() const override { return sahne; }
    OznitelikPtr Oznitelikler() const override { return BosOznitelikTablosu(); }
    uint64_t SahneSurumu() const override { return surum; }
    ModelOzeti Ozet() const override {
        ModelOzeti o;
        const nlohmann::json j = nlohmann::json::parse(model, nullptr, false);
        if (!j.is_object()) return o;
        auto n = [&](const char* a) { return j.contains(a) && j[a].is_array() ? j[a].size() : size_t{0}; };
        o.baslik = j.value("baslik", std::string());
        o.surum = j.value("surum", 1);
        o.dugum = n("dugumler");
        o.cubuk = n("cubuklar") + n("kolonlar") + n("kirisler");
        o.panel = n("paneller") + n("dosemeler");
        o.kat = n("katlar");
        o.bos = o.dugum + o.cubuk + o.panel == 0;
        return o;
    }
    DenetimSonucu Denetle() override { return {}; }
    std::string Metin() override { return model; }
    SonucEslemesi SonucEsle(const JsonMetni& veri) override {
        if (!eslemeVar) return {false, "sahte çekirdek: sonuç eşleme yok", {}, {}};
        return TasarimdanEsle(veri);
    }
    IfcSonucu IfcDisari(const JsonMetni& secenek, const JsonMetni& veri) override {
        ++ifcCagri;
        sonIfcSecenek = secenek;
        sonIfcVeri = veri;
        IfcSonucu r;
        r.basarili = true;
        r.metin = "ISO-10303-21;\nHEADER;\n/* secenek " + secenek + " */\nENDSEC;\nDATA;\n/* model " + MetinKarmasi(model) +
                  " */\nENDSEC;\nEND-ISO-10303-21;\n";
        r.dosyaAdi = Ozet().baslik + ".ifc";
        return r;
    }
};

// Sahte hesap motoru: istekleri biriktirir; sınama Yanitla / HataVer ile yanıt kuyruğa koyar, Pompala dağıtır.
class SahteMotor final : public MotorHizmeti {
public:
    struct Istek {
        IstekNo no = 0;
        std::string islem, girdi, ayarlar;
        YanitIsleyici isleyici;
        bool bitti = false;
    };
    std::vector<Istek> istekler;
    MotorDurumOzeti durum;
    SahteMotor() {
        durum.baslatildi = durum.hazir = durum.basarili = true;
        durum.surumJson = R"({"motor":"9.9.9","sympy":"1.14.0","python":"3.14.0"})";
    }
    void Baslat(const MotorAyari&) override {}
    MotorDurumOzeti Durum(MotorRolu) const override { return durum; }
    IstekNo Gonder(std::string_view islem, const std::string& girdi, const std::string& ayarlar, YanitIsleyici f) override {
        istekler.push_back({++sonNo_, std::string(islem), girdi, ayarlar, std::move(f), false});
        return sonNo_;
    }
    bool Iptal(IstekNo no) override {
        Istek* i = Bul(no);
        if (!i || i->bitti) return false;
        MotorYaniti y = Taban(*i, YanitDurumu::Iptal);
        y.hata = "İşlem iptal edildi.";
        y.hataTuru = "iptal";
        y.yanit = motor_protokolu::HataYaniti(y.hata, y.hataTuru);
        Kuyruk(*i, std::move(y));
        return true;
    }
    size_t Pompala() override {
        size_t n = 0;
        while (!kuyruk_.empty()) {
            auto [y, f] = std::move(kuyruk_.front());
            kuyruk_.pop_front();
            if (f) f(y);
            ++n;
        }
        return n;
    }
    MotorYaniti CalistirBekle(std::string_view, const std::string&, const std::string&, double) override { return {}; }
    void Durdur() override {}

    // sınama tarafı
    Istek* Son(std::string_view islem) {
        for (auto i = istekler.rbegin(); i != istekler.rend(); ++i)
            if (i->islem == islem) return &*i;
        return nullptr;
    }
    void Yanitla(IstekNo no, std::string yanit, double sureMs = 12) {
        Istek* i = Bul(no);
        REQUIRE(i);
        MotorYaniti y = Taban(*i, YanitDurumu::Tamam);
        y.yanit = std::move(yanit);
        y.sureMs = sureMs;
        Kuyruk(*i, std::move(y));
    }
    void HataVer(IstekNo no, YanitDurumu d, std::string hata, std::string tur) {
        Istek* i = Bul(no);
        REQUIRE(i);
        MotorYaniti y = Taban(*i, d);
        y.hata = std::move(hata);
        y.hataTuru = std::move(tur);
        y.yanit = motor_protokolu::HataYaniti(y.hata, y.hataTuru);
        Kuyruk(*i, std::move(y));
    }

private:
    Istek* Bul(IstekNo no) {
        for (Istek& i : istekler)
            if (i.no == no) return &i;
        return nullptr;
    }
    static MotorYaniti Taban(const Istek& i, YanitDurumu d) {
        MotorYaniti y;
        y.no = i.no;
        y.islem = i.islem;
        y.durum = d;
        return y;
    }
    void Kuyruk(Istek& i, MotorYaniti y) {
        i.bitti = true;
        kuyruk_.emplace_back(std::move(y), i.isleyici);
    }
    IstekNo sonNo_ = 0;
    std::deque<std::pair<MotorYaniti, YanitIsleyici>> kuyruk_;
};

// C'nin görünüm katkısını taklit eder (gorunum/gorunum.json).
struct SahteGorunumKatkisi {
    std::string durum = "{\"kamera\":{\"hedef\":[1,2,3]},\"kip\":\"cubuk\"}\n";
    std::string okunan;
    int sifirlama = 0;
    void Ekle(ProjeBelgesi& b) {
        b.KatkiEkle({"gorunum", 10, [this](ProjeIcerigi& i) { i.Koy(proje_yolu::GORUNUM, durum); },
                     [this](const ProjeIcerigi& i, std::vector<std::string>&) {
                         const std::string* g = i.Al(proje_yolu::GORUNUM);
                         okunan = g ? *g : std::string();
                     },
                     [this] { ++sifirlama; }});
    }
};

struct DOrtamAyari {
    double otomatikKayitMs = 2000;
    std::string kurtarmaDizini;     // boş: ortamın geçici klasöründe yerel/kurtarma
    DosyaPlatformu platform;
    bool gorunumKatkisi = true;
    std::function<void(std::string_view)> olcum;  // CozumAkisiAyari::olcum
};

// Sözleşme nesneleri + sahte çekirdek / motor + D'nin dosya ve çözüm akışları. (ProjeBelgesi katkı kaldırmayı
// desteklemediği için DosyaIslemleri / CozumAkisi ortam başına bir kez kurulur.)
struct DOrtam {
    GeciciDizin dizin;
    KomutYoneticisi komutlar;
    ArayuzKancalari arayuz;
    GunlukBildirimleri bildirim{nullptr};
    BetikliIletisimKutulari iletisim;
    ProjeBelgesi belge;
    Secim secim;
    GorunumDurumu gorunum;
    SonucDurumu sonuc;
    Ayarlar ayarlar;
    SahteCekirdek cekirdek;
    SahteMotor motor;
    SahteGorunumKatkisi gorunumKatkisi;
    Hizmetler h;
    std::unique_ptr<DosyaIslemleri> dosya;
    std::unique_ptr<CozumAkisi> cozum;

    explicit DOrtam(DOrtamAyari ayar = {}) {
        std::string hata;
        REQUIRE_MESSAGE(komutlar.KatalogYukle(Op4Dosyasi("veri/komutlar.json"), hata), hata);
        h.komutlar = &komutlar;
        h.arayuz = &arayuz;
        h.bildirim = &bildirim;
        h.iletisim = &iletisim;
        h.cekirdek = &cekirdek;
        h.motor = &motor;
        h.belge = &belge;
        h.secim = &secim;
        h.gorunum = &gorunum;
        h.sonuc = &sonuc;
        h.ayarlar = &ayarlar;
        h.bilgi.surum = "0.1.0";
        h.bilgi.veriDizini = std::string(OP4_KAYNAK_DIZINI) + "/veri";
        h.bilgi.ayarDizini = dizin.Kur("ayarlar");
        h.bilgi.yerelDizin = dizin.Kur("yerel");
        h.bilgi.testKipi = true;
        DosyaIslemleriAyari a;
        a.kurtarmaDizini = ayar.kurtarmaDizini.empty() ? dizin.Kur("yerel/kurtarma") : ayar.kurtarmaDizini;
        a.otomatikKayitMs = ayar.otomatikKayitMs;
        a.sabitZaman = "2026-10-31T12:00:00Z";
        a.ifcZamani = "2026-01-01T00:00:00";
        dosya = std::make_unique<DosyaIslemleri>(h, a, ayar.platform);
        dosya->Kur();
        if (ayar.gorunumKatkisi) gorunumKatkisi.Ekle(belge);
        CozumAkisiAyari ca;
        ca.sabitZaman = "2026-10-31T12:00:00Z";
        ca.olcum = ayar.olcum;
        cozum = std::make_unique<CozumAkisi>(h, ca);
        cozum->Kur();
        ModelYuklendi(h, cekirdek.YeniBos("Adsız 1"));
        belge.Acildi("", 1, false);
    }
    ~DOrtam() {
        cozum.reset();
        dosya.reset();
    }
    bool Komut(const char* id, std::string_view arguman = {}) {
        std::string hata;
        const bool b = komutlar.Calistir(id, h, KomutKaynagi::Kod, arguman, &hata);
        if (!b) MESSAGE("komut çalışmadı: ", id, " — ", hata);
        return b;
    }
    bool SatirdaVar(std::string_view parca) const {
        for (const std::string& s : bildirim.satirlar)
            if (s.find(parca) != std::string::npos) return true;
        return false;
    }
    // Şablon dosyası (sondaki satır sonu atılmış; sahte çekirdeğin Metin()'i ile karşılaştırılır).
    static std::string Sablon(const std::string& ad) {
        std::string s = Op4Dosyasi("veri/sablonlar/" + ad + ".json");
        while (!s.empty() && s.back() == '\n') s.pop_back();
        return s;
    }
};

}  // namespace op4::sinama
