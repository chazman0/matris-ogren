// Sözleşme sınamaları: uygulama kabuğu ve ortak model akışları (S22, S23), proje belgesi katkıları (S15), öznitelik
// tablosu (S5), ayarlar (S18), dosya yardımcıları (S16, S17), sonuç durumu (S19), gezgin (S10).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cstdlib>
#include <filesystem>
#include <set>

#include "cekirdek/gezgin.h"
#include "cekirdek/kabuk.h"
#include "cekirdek/motor_hizmeti.h"
#include "cekirdek/oznitelik.h"
#include "cekirdek/proje_dosyasi.h"
#include "cekirdek/secme.h"
#include "platform/dosya_sistemi.h"
#include "sinama_yardim.h"

using namespace op4;
using nlohmann::json;

namespace {

// Sahte A modülü: taslak süreç istemcisi.
void SahteMotorKur(Hizmetler& h, ModulOrtami& o) {
    std::shared_ptr<MotorHizmeti> m(MotorIstemcisiOlustur().release());
    h.motor = o.Tut(m);
    h.KareIsiEkle("motor", [mp = m.get()](double) { mp->Pompala(); });
}

// Sahte çekirdek: C1 geçiş onayını sınamak için.
class OnayliCekirdek final : public ModelCekirdegi {
public:
    int cagri = 0;
    YuklemeSonucu YeniBos(std::string_view) override { return {true, "", {}, {}}; }
    YuklemeSonucu Yukle(std::string_view, std::string_view) override { return {true, "", {}, {}}; }
    IslemRaporu Uygula(std::string_view islem, const JsonMetni& p) override {
        ++cagri;
        IslemRaporu r;
        r.islem = std::string(islem);
        r.basarili = true;
        if (p.find("\"onay\":true") == std::string::npos) {
            r.gecisOnayi = GecisOnayi{"Model genel modele çevrilecek."};
            return r;
        }
        r.eklenen = {CubukKimligi(1)};
        r.silinen = {CubukKimligi(7)};
        r.sahneSurumu = 2;
        return r;
    }
    IslemRaporu GeriAl() override { return {}; }
    IslemRaporu Yinele() override { return {}; }
    GeriAlDurumu GeriAlBilgisi() const override { return {}; }
    std::vector<std::string> IslemAdlari() const override { return {"kolonEkle"}; }
    SahnePtr Sahne() const override { return BosSahne(); }
    OznitelikPtr Oznitelikler() const override { return BosOznitelikTablosu(); }
    uint64_t SahneSurumu() const override { return 0; }
    ModelOzeti Ozet() const override { return {}; }
    DenetimSonucu Denetle() override { return {}; }
    std::string Metin() override { return "{}"; }
    SonucEslemesi SonucEsle(const JsonMetni&) override { return {}; }
    IfcSonucu IfcDisari(const JsonMetni&, const JsonMetni&) override { return {}; }
};

}  // namespace

TEST_CASE("S23 kabuk: katalog, modüller, boş model 'Adsız 1', geri al komutu bağlı") {
    UygulamaKabugu k;
    KabukAyari a;
    a.bilgi.surum = OP4_SURUM;
    a.bilgi.veriDizini = std::string(OP4_KAYNAK_DIZINI) + "/veri";
    a.bilgi.testKipi = true;
    a.ortam.testKipi = true;
    a.moduller = {{"motor", "A", &SahteMotorKur}, {"cekirdek", "B", &CekirdekModuluKur}};
    std::string hata;
    REQUIRE_MESSAGE(k.Kur(std::move(a), hata), hata);
    Hizmetler& h = k.H();
    REQUIRE(h.cekirdek);
    REQUIRE(h.motor);
    CHECK(h.belge->Ad() == "Adsız 1");
    CHECK(h.belge->PencereBasligi() == "op4 — Adsız 1");
    CHECK_FALSE(h.belge->Kirli());
    const json m = json::parse(h.cekirdek->Metin());
    CHECK(m["tur"] == "bina");
    CHECK(m["surum"] == 3);
    CHECK(m["baslik"] == "Adsız 1");
    CHECK(h.cekirdek->Sahne() != nullptr);
    CHECK(h.cekirdek->Oznitelikler() != nullptr);
    const KomutDurumu d = h.komutlar->Durum("duzenle.geri_al", h);
    CHECK(d.bagli);
    CHECK_FALSE(d.kullanilabilir);
    // Taslak çekirdekte düzenleme hata verir ve model / belge değişmez.
    const IslemRaporu r = ModelIslemiUygula(h, islem::HIZLI_AKS, "{}");
    CHECK_FALSE(r.basarili);
    CHECK_FALSE(h.belge->Kirli());
    h.KareIsleriniCalistir(0);
    k.Kapat();
}

namespace {
// Çıkış isteği sınaması: kurulumda çıkış isteyen modül (D'nin tek örnek devri gibi) ve yeniOrnek'i okuyan modül.
int CikisKurulanlar = 0;
bool CikisYeniOrnek = false;
void CikisIsteyenModul(Hizmetler&, ModulOrtami& o) {
    ++CikisKurulanlar;
    CikisYeniOrnek = o.yeniOrnek;
    if (!o.yeniOrnek) o.cikisIste(3);
}
void SayanModul(Hizmetler&, ModulOrtami&) { ++CikisKurulanlar; }
}  // namespace

TEST_CASE("S23 kabuk: çıkış isteği (cikisIste) ve yeniOrnek; kurulumda kalan modüller kurulmaz, boş model açılmaz") {
    auto ayar = [] {
        KabukAyari a;
        a.bilgi.surum = OP4_SURUM;
        a.bilgi.veriDizini = std::string(OP4_KAYNAK_DIZINI) + "/veri";
        a.bilgi.testKipi = true;
        a.moduller = {{"cekirdek", "B", &CekirdekModuluKur}, {"dosya", "D", &CikisIsteyenModul},
                      {"cozum", "D", &SayanModul}};
        return a;
    };
    std::string hata;
    {
        UygulamaKabugu k;
        CikisKurulanlar = 0;
        REQUIRE_MESSAGE(k.Kur(ayar(), hata), hata);
        CHECK(k.CikisIstendi());
        CHECK(k.CikisKodu() == 3);
        CHECK(CikisKurulanlar == 1);  // "cozum" kurulmadı
        CHECK_FALSE(CikisYeniOrnek);
        REQUIRE(k.H().cekirdek);
        CHECK(k.H().cekirdek->Ozet().bos);
        CHECK(k.H().belge->Ad() == "Adsız 1");
        k.Ortam().cikisIste(9);  // ilk isteğin kodu geçerli
        CHECK(k.CikisKodu() == 3);
        k.Kapat();
    }
    {
        // --yeni-ornek: modül ortamdan okur, çıkış istemez; bütün modüller kurulur. Kurulumdan sonraki istek pencereyi
        // kapatma kancasına gider (C bağlar).
        UygulamaKabugu k;
        CikisKurulanlar = 0;
        KabukAyari a = ayar();
        a.ortam.yeniOrnek = true;
        REQUIRE(k.Kur(std::move(a), hata));
        CHECK(CikisYeniOrnek);
        CHECK_FALSE(k.CikisIstendi());
        CHECK(CikisKurulanlar == 2);
        int kapat = 0;
        k.arayuz.pencereyiKapat = [&kapat] { ++kapat; };
        REQUIRE(k.Ortam().cikisIste);
        k.Ortam().cikisIste(0);
        CHECK(k.CikisIstendi());
        CHECK(k.CikisKodu() == 0);
        CHECK(kapat == 1);
        k.Kapat();
    }
    {
        // Ev sahibi kendi işlevini verirse kabuk kaydeder ve onu çağırır (pencere kancası çağrılmaz).
        UygulamaKabugu k;
        std::vector<int> evSahibi;
        KabukAyari a = ayar();
        a.ortam.cikisIste = [&evSahibi](int kod) { evSahibi.push_back(kod); };
        int kapat = 0;
        k.arayuz.pencereyiKapat = [&kapat] { ++kapat; };
        REQUIRE(k.Kur(std::move(a), hata));
        CHECK(k.CikisIstendi());
        CHECK(evSahibi == std::vector<int>{3});
        CHECK(kapat == 0);
        k.Kapat();
    }
}

TEST_CASE("S22 ModelIslemiUygula: C1 onayı, kirli işareti, seçim ayıklama, sonuç eski") {
    Hizmetler h;
    OnayliCekirdek c;
    BetikliIletisimKutulari il;
    GunlukBildirimleri bl(nullptr);
    ProjeBelgesi belge;
    Secim secim;
    GorunumDurumu gorunum;
    SonucDurumu sonuc;
    h.cekirdek = &c;
    h.iletisim = &il;
    h.bildirim = &bl;
    h.belge = &belge;
    h.secim = &secim;
    h.gorunum = &gorunum;
    h.sonuc = &sonuc;
    int degisti = 0;
    h.modelDegisti.Abone([&](const IslemRaporu&) { ++degisti; });
    secim.Uygula(std::vector<ElemanKimligi>{CubukKimligi(7), CubukKimligi(8)}, SecimKipi::Yeni);
    sonuc.Ata(SonucOzeti{}, nullptr);

    il.yanitlar = {"1"};  // Vazgeç
    IslemRaporu r = ModelIslemiUygula(h, "kolonEkle", "{\"x\":1}");
    CHECK_FALSE(r.basarili);
    CHECK(c.cagri == 1);
    CHECK_FALSE(belge.Kirli());

    il.yanitlar = {"0"};  // Dönüştür
    r = ModelIslemiUygula(h, "kolonEkle", "{\"x\":1}");
    CHECK(r.ModelDegisti());
    CHECK(c.cagri == 3);
    CHECK(belge.Kirli());
    CHECK(belge.PencereBasligi() == "op4 — Adsız 1 •");
    CHECK(secim.Liste() == std::vector<ElemanKimligi>{CubukKimligi(8)});
    CHECK(sonuc.Eski());
    CHECK(degisti == 1);
    CHECK(OnayEkle("") == "{\"onay\":true}");
    CHECK(json::parse(OnayEkle("{\"a\":2}")) == json::parse("{\"a\":2,\"onay\":true}"));
}

TEST_CASE("S15 proje belgesi: katkılar sırayla toplanır ve dağıtılır") {
    ProjeBelgesi b;
    std::vector<std::string> sira;
    b.KatkiEkle({"sonuc", 30, [&](ProjeIcerigi& i) { i.Koy(proje_yolu::SONUC_OZETI, "{}"); sira.push_back("sonuc"); }, {}, {}});
    b.KatkiEkle({"model", 0, [&](ProjeIcerigi& i) { i.Koy(proje_yolu::MODEL, "{\"tur\":\"bina\"}"); sira.push_back("model"); },
                 [&](const ProjeIcerigi& i, std::vector<std::string>&) { CHECK(i.Var(proje_yolu::MODEL)); }, {}});
    ProjeIcerigi i;
    b.IcerikTopla(i);
    CHECK(sira == std::vector<std::string>{"model", "sonuc"});
    CHECK(*i.Al(proje_yolu::MODEL) == "{\"tur\":\"bina\"}");
    std::vector<std::string> uyarilar;
    b.IcerikDagit(i, uyarilar);
    bool kirli = false;
    b.kirliDegisti.Abone([&](const bool& k) { kirli = k; });
    b.KirliIsaretle();
    CHECK(kirli);
    b.Kaydedildi("/proje/yapi.op4");
    CHECK_FALSE(kirli);
    CHECK(b.Ad() == "yapi.op4");

    // KatkiKaldir: modül kapanırken kendi katkılarını bırakır; kalanlar sırasını korur.
    b.KatkiEkle({"gorunum", 10, {}, {}, {}});
    CHECK(b.KatkiKaldir("sonuc") == 1);
    CHECK(b.KatkiKaldir("sonuc") == 0);
    CHECK(b.KatkiKaldir("yok") == 0);
    REQUIRE(b.Katkilar().size() == 2);
    CHECK(b.Katkilar()[0].ad == "model");
    CHECK(b.Katkilar()[1].ad == "gorunum");
    sira.clear();
    ProjeIcerigi j;
    b.IcerikTopla(j);
    CHECK(sira == std::vector<std::string>{"model"});
    CHECK_FALSE(j.Var(proje_yolu::SONUC_OZETI));

    // Görünen ad: yolsuz belge (içe aktarılan) "Adsız N" yerine onu gösterir; 3 değişkenli Acildi ve Kaydedildi siler.
    b.Acildi("", 4, false, "bina");
    CHECK(b.Ad() == "bina");
    CHECK(b.PencereBasligi() == "op4 — bina");
    b.Acildi("/proje/a.op4", 5, false, "yok sayılır");
    CHECK(b.Ad() == "a.op4");
    b.Acildi("", 6, false, "bina");
    b.Kaydedildi("/proje/bina.op4");
    CHECK(b.Ad() == "bina.op4");
    b.Acildi("", 7, false, "bina");
    b.Acildi("", 8, false);
    CHECK(b.Ad() == "Adsız 8");
    b.Acildi("", 9, false, "");
    CHECK(b.Ad() == "Adsız 9");
}

TEST_CASE("S16/S17 biçim saptama, son dosyalar, atomik yazma") {
    CHECK(BicimSapta(std::string("PK\x03\x04rest", 8), ".op4") == DosyaBicimi::Op4);
    CHECK(BicimSapta("\xEF\xBB\xBF  {\"kamera\":{}}", ".op4") == DosyaBicimi::Op4Deneme);
    CHECK(BicimSapta("{\"tur\":\"bina\"}", ".json") == DosyaBicimi::BinaJson);
    CHECK(BicimSapta("{}", ".MATRIS") == DosyaBicimi::Matris);
    CHECK(BicimSapta("ISO-10303-21;\nHEADER;", ".ifc") == DosyaBicimi::Ifc);
    CHECK(BicimSapta("xyz", ".txt") == DosyaBicimi::Bilinmiyor);
    std::vector<std::string> son{"a.op4", "B.op4", "c.op4"};
    SonDosyaEkle(son, "b.op4", 3);
    CHECK(son == std::vector<std::string>{"b.op4", "a.op4", "c.op4"});

    const auto dizin = std::filesystem::temp_directory_path() / std::filesystem::path(u8"op4 sınama ŞĞİı");
    std::filesystem::create_directories(dizin);
    const std::u8string u = (dizin / std::filesystem::path(u8"yapı.op4")).u8string();
    const std::string yol(reinterpret_cast<const char*>(u.data()), u.size());
    std::string hata, okunan;
    REQUIRE_MESSAGE(AtomikYaz(yol, "birinci", false, hata), hata);
    REQUIRE(AtomikYaz(yol, "ikinci", true, hata));
    REQUIRE(DosyaOku(yol, okunan, hata));
    CHECK(okunan == "ikinci");
    REQUIRE(DosyaOku(yol + ".bak", okunan, hata));
    CHECK(okunan == "birinci");
    CHECK(DosyaVar(yol));
    std::filesystem::remove_all(dizin);
}

TEST_CASE("S18 ayarlar: gidiş-dönüş, sınırlar, bilinmeyen anahtarlar korunur") {
    Ayarlar a;
    std::string hata;
    REQUIRE(AyarlariOku("{\"grafik\":{\"msaa\":3},\"dosya\":{\"otomatik_kayit_dk\":99,\"son_dosyalar\":[\"x.op4\"]},"
                        "\"gelecek\":{\"z\":1}}",
                        a, hata));
    CHECK(a.grafik.msaa == 0);
    CHECK(a.dosya.otomatikKayitDk == 30);
    CHECK(a.dosya.sonDosyalar == std::vector<std::string>{"x.op4"});
    Ayarlar b;
    REQUIRE(AyarlariOku(AyarlariYaz(a), b, hata));
    CHECK(b.dosya.sonDosyalar == a.dosya.sonDosyalar);
    CHECK(json::parse(AyarlariYaz(b))["gelecek"]["z"] == 1);
    CHECK_FALSE(AyarlariOku("{bozuk", a, hata));
    CHECK(a.dosya.otomatikKayitDk == 5);
}

TEST_CASE("S5 öznitelik şeması: Faz 1 sütunları oznitelikler.json'da; ortak değerler") {
    const json s = json::parse(sinama::Op4Dosyasi("veri/oznitelikler.json"));
    std::set<std::string> ids;
    for (const json& o : s["oznitelikler"]) ids.insert(o["id"].get<std::string>());
    for (const OznitelikSutunu& c : BosOznitelikTablosu()->sutunlar) CHECK_MESSAGE(ids.count(c.id) == 1, c.id);

    OznitelikTablosu t;
    t.satirlar = {CubukKimligi(1), CubukKimligi(2)};
    OznitelikSutunu kesit{oznitelik::KESIT, OznitelikTuru::Metin, "", {}, {0, 0}, {"HEA 340"}, {}, {}};
    OznitelikSutunu uz{oznitelik::UZUNLUK, OznitelikTuru::Sayi, "m", {3.5, 6.0}, {}, {}, {}, {}};
    OznitelikSutunu kat{oznitelik::KAT, OznitelikTuru::Liste, "", {}, {}, {}, {0, 1, 3}, {1, 1, 2}};
    t.sutunlar = {kesit, uz, kat};
    t.DizinleriKur();
    CHECK(t.Gosterim(0, *t.Sutun(oznitelik::UZUNLUK)) == "3,5 m");
    CHECK(t.Liste(1, oznitelik::KAT) == std::vector<double>{1, 2});
    const auto o = OrtakOzellikler(t, {CubukKimligi(1), CubukKimligi(2)});
    REQUIRE(o.size() == 3);
    CHECK(o[0].second == "HEA 340");
    CHECK(o[1].second == "(çeşitli)");
    const GezginDugumu g = GezginAgaciKur(t);
    CHECK(g.sayi == 2);
}

TEST_CASE("S19 sonuç: D/C renkleri web ölçeğiyle aynı, eski işareti") {
    CHECK(DcRengi(0.5) == 0x22C55EFFu);
    CHECK(DcRengi(0.8) == 0xFACC15FFu);
    CHECK(DcRengi(1.0) == 0xFB923CFFu);
    CHECK(DcRengi(1.01) == 0xEF4444FFu);
    CHECK(DcRengi(-1) == 0x8C8C8CFFu);
    SonucDurumu s;
    int olay = 0;
    s.degisti.Abone([&] { ++olay; });
    s.EskiIsaretle();
    CHECK(olay == 0);
    SonucOzeti o;
    o.elemanlar = {{CubukKimligi(1), 0.95, "", "", 0}};
    s.Ata(o, nullptr);
    s.EskiIsaretle();
    s.EskiIsaretle();
    CHECK(olay == 2);
    const auto b = BoyamaKur(s.Ozet(), 1);
    REQUIRE(b->renkler.size() == 1);
    CHECK(b->renkler[0].rgba == 0xFB923CFFu);
}

TEST_CASE("S8 seçme: izdüşüm yardımcıları ve sınır") {
    GorusIzdusumu g;
    g.genislik = 200;
    g.yukseklik = 100;
    double x = 0, y = 0;
    REQUIRE(g.Izdusur({0, 0, 0}, x, y));
    CHECK(x == doctest::Approx(100));
    CHECK(y == doctest::Approx(50));
    SecmeDizini d;
    d.Kur(OrnekSahneAnlik());
    CHECK(d.SahneSurumu() == 1);
    const Kutu3d k = d.Sinir({CubukKimligi(1), CubukKimligi(8)});
    CHECK_FALSE(k.Bos());
}
