// Model çekirdeği (B) — modül ve komutlar (sözleşme S23; kabul B8): duzenle.geri_al, duzenle.yinele, model.denetle bağlı;
// GeriAlBilgisi menü adlarını verir; Ayarlar::cekirdek geri al sınırı uygulanır.
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <filesystem>
#include <fstream>

#include "cekirdek/kabuk.h"
#include "cekirdek_js_yardim.h"

using namespace op4;
using nlohmann::json;

TEST_CASE("cekirdek_js B8: kabukta çekirdek modülü — komutlar, kullanılabilirlik, geri al adı, denetim çıktısı, ayar") {
    const auto dizin = std::filesystem::temp_directory_path() / "op4_cekirdek_js_kabuk";
    std::filesystem::create_directories(dizin);
    {
        std::ofstream f(dizin / "ayarlar.json", std::ios::binary);
        f << R"({"cekirdek": {"geri_al_adim": 2}})";
    }
    UygulamaKabugu k;
    KabukAyari a;
    a.bilgi.surum = OP4_SURUM;
    a.bilgi.veriDizini = std::string(OP4_KAYNAK_DIZINI) + "/veri";
    a.bilgi.ayarDizini = dizin.string();
    a.bilgi.testKipi = true;
    a.ortam.testKipi = true;
    std::vector<std::string> gunluk;
    a.ortam.gunluk = [&gunluk](std::string_view s) { gunluk.emplace_back(s); };
    a.moduller = {{"cekirdek", "B", &CekirdekModuluKur}};
    std::string hata;
    REQUIRE_MESSAGE(k.Kur(std::move(a), hata), hata);
    Hizmetler& h = k.H();
    REQUIRE(h.cekirdek);
    CHECK(h.ayarlar->cekirdek.geriAlAdim == 2);
    bool kuruldu = false, olcum = false;
    for (const std::string& s : gunluk) {
        kuruldu = kuruldu || s.find("Model çekirdeği (QuickJS-ng") != std::string::npos;
        olcum = olcum || s.rfind("OP4OLCUM cekirdek_derleme_ms=", 0) == 0;
    }
    CHECK(kuruldu);
    CHECK(olcum);

    for (const char* id : {"duzenle.geri_al", "duzenle.yinele", "model.denetle"}) {
        const KomutDurumu d = h.komutlar->Durum(id, h);
        CHECK_MESSAGE(d.bagli, id);
        CHECK_FALSE_MESSAGE(d.kullanilabilir, id);  // boş model: geri alınacak, yinelenecek, denetlenecek bir şey yok
    }
    CHECK(h.komutlar->Durum("model.denetle", h).neden == "Model boş: denetlenecek eleman yok");

    // üç işlem; ayar 2 adım tutar
    for (const char* p : {R"({"x":[5],"y":[5],"z":[3]})", R"({"baslik":"A"})", R"({"baslik":"B"})"}) {
        const std::string islemAdi = std::string(p).find("baslik") != std::string::npos ? islem::BASLIK_DEGISTIR : islem::HIZLI_AKS;
        REQUIRE(ModelIslemiUygula(h, islemAdi, p).basarili);
    }
    CHECK(h.belge->Kirli());
    CHECK(h.cekirdek->GeriAlBilgisi().adim == 2);
    CHECK(h.cekirdek->GeriAlBilgisi().geriAlAdi == "Başlık değiştir");
    CHECK(h.komutlar->Durum("duzenle.geri_al", h).kullanilabilir);
    CHECK(h.komutlar->Calistir("duzenle.geri_al", h, KomutKaynagi::Kisayol));
    CHECK(json::parse(h.cekirdek->Metin())["baslik"] == "A");
    CHECK(h.cekirdek->GeriAlBilgisi().yineleAdi == "Başlık değiştir");
    CHECK(h.komutlar->Durum("duzenle.yinele", h).kullanilabilir);
    CHECK(h.komutlar->SatirCalistir("YİNELE", h, &hata));
    CHECK(json::parse(h.cekirdek->Metin())["baslik"] == "B");

    // denetim: şablon yüklenince komut kullanılabilir; çıktı komut satırına yazılır
    ModelYuklendi(h, h.cekirdek->Yukle(sinama::Sablon("celik-1kat-depo"), "sablon:celik-1kat-depo"));
    CHECK(h.komutlar->Durum("model.denetle", h).kullanilabilir);
    auto* bl = dynamic_cast<GunlukBildirimleri*>(h.bildirim);
    REQUIRE(bl);
    const size_t once = bl->satirlar.size();
    CHECK(h.komutlar->Calistir("model.denetle", h, KomutKaynagi::Menu));
    REQUIRE(bl->satirlar.size() > once);
    CHECK(bl->satirlar[once].rfind("Denetim:", 0) == 0);
    k.Kapat();
    std::filesystem::remove_all(dizin);
}
