// Sözleşme sınamaları: komut kataloğu (op4/veri/komutlar.json) ve kayıt defteri (S20), arayüz kancaları (S21).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <set>

#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/hizmetler.h"
#include "cekirdek/komut.h"
#include "cekirdek/turkce.h"
#include "sinama_yardim.h"

using namespace op4;

TEST_CASE("S20 kısayol normalleştirme") {
    CHECK(KisayolNormal("ctrl+shift+s") == "Ctrl+Shift+S");
    CHECK(KisayolNormal("Shift + Ctrl + S") == "Ctrl+Shift+S");
    CHECK(KisayolNormal("f5") == "F5");
    CHECK(KisayolNormal("Alt+1") == "Alt+1");
    CHECK(KisayolNormal("PgUp") == "PageUp");
    CHECK(KisayolNormal("Ctrl+") == "");
    CHECK(KisayolNormal("Ctrl+F99") == "");
    CHECK(KisayolNormal("") == "");
}

TEST_CASE("S20 katalog: yüklenir; id, kısayol ve katlanmış adlar tekil; her komutun sahibi A–D") {
    KomutYoneticisi k;
    std::string hata;
    REQUIRE_MESSAGE(k.KatalogYukle(sinama::Op4Dosyasi("veri/komutlar.json"), hata), hata);
    CHECK(k.Tanimlar().size() >= 30);
    std::set<std::string> idler, kisayollar, adlar;
    for (const KomutTanimi& t : k.Tanimlar()) {
        CAPTURE(t.id);
        CHECK(idler.insert(t.id).second);
        CHECK(std::set<std::string>{"A", "B", "C", "D"}.count(t.sahip) == 1);
        if (!t.kisayol.empty()) CHECK(kisayollar.insert(t.kisayol).second);
        std::set<std::string> kendi{TurkceKatla(t.ad)};
        for (const std::string& a : t.takmaAdlar) kendi.insert(TurkceKatla(a));
        for (const std::string& a : kendi) CHECK_MESSAGE(adlar.insert(a).second, a);
        if (t.serit) CHECK(!t.serit->sekme.empty());
    }
    // F1 iş listesinin dayandığı komutlar (MIMARI "F1 paket sözleşmeleri" §K).
    for (const char* id : {"dosya.yeni", "dosya.ac", "dosya.kaydet", "dosya.farkli_kaydet", "dosya.ifc_disa", "duzenle.geri_al",
                           "duzenle.yinele", "model.hizli_aks", "gorunum.sigdir", "gorunum.kesit_gorunumu", "gorunum.izgara",
                           "gorunum.3b", "gorunum.plan", "gorunum.ust_kat", "analiz.coz", "analiz.iptal", "motor.yeniden_baslat"})
        CHECK_MESSAGE(k.Bul(id) != nullptr, id);
    CHECK(k.KisayolBul("F5")->id == "analiz.coz");
    CHECK(k.KisayolBul("ctrl+shift+k")->id == "gorunum.kesit_gorunumu");
    CHECK(k.KisayolBul("F7")->id == "gorunum.izgara");
    CHECK(k.Bul("çöz")->id == "analiz.coz");
    CHECK(k.Bul("COZ")->id == "analiz.coz");
    CHECK(k.Bul("sığdır")->id == "gorunum.sigdir");
    CHECK(k.Sekmeler().front() == "Dosya");
}

TEST_CASE("S20 kayıt defteri: bağlama, durum, satır çalıştırma, tamamlama, son komut") {
    KomutYoneticisi k;
    std::string hata;
    REQUIRE(k.KatalogYukle(sinama::Op4Dosyasi("veri/komutlar.json"), hata));
    Hizmetler h;
    h.komutlar = &k;
    CHECK_FALSE(k.Bagla("yok.boyle", {}));
    KomutDurumu d = k.Durum("analiz.coz", h);
    CHECK(d.tanimli);
    CHECK_FALSE(d.bagli);
    CHECK(d.neden.find("henüz uygulanmadı") != std::string::npos);

    int cozum = 0;
    std::string arg;
    bool modelVar = false;
    KomutIsleyici i;
    i.calistir = [&](KomutBaglami& b) {
        ++cozum;
        arg = b.arguman;
    };
    i.kullanilamazNedeni = [&](const Hizmetler&) { return modelVar ? std::string() : std::string("Çöz: önce model kurun"); };
    REQUIRE(k.Bagla("analiz.coz", i));
    CHECK_FALSE(k.Calistir("analiz.coz", h, KomutKaynagi::Kisayol, {}, &hata));
    CHECK(hata == "Çöz: önce model kurun");
    modelVar = true;
    CHECK(k.SatirCalistir("  çöz   hızlı ", h, &hata));
    CHECK(cozum == 1);
    CHECK(arg == "hızlı");
    CHECK(k.SonKomut() == "analiz.coz");
    CHECK(k.SatirCalistir("", h, &hata));  // boş satır: tekrarlanır son komut
    CHECK(cozum == 2);
    CHECK_FALSE(k.SatirCalistir("KOLONN", h, &hata));
    CHECK(hata.find("Bilinmeyen komut") != std::string::npos);
    const auto t = k.Tamamla("ka");
    REQUIRE_FALSE(t.empty());
    CHECK(t.front()->id == "dosya.kaydet");
}

TEST_CASE("S21 arayüz kancaları: sıralama, açık durumu, betikli iletişim") {
    ArayuzKancalari a;
    a.PanelEkle({"ozellikler", "Özellikler", PanelYeri::Sag, 20, true, "C", {}});
    a.PanelEkle({"sonuc_ozeti", "Sonuç özeti", PanelYeri::Sag, 10, false, "D", {}});
    a.PanelEkle({"model_gezgini", "Model gezgini", PanelYeri::Sol, 10, true, "C", {}});
    REQUIRE(a.Paneller().size() == 3);
    CHECK(a.Paneller()[0].id == "model_gezgini");
    CHECK(a.Paneller()[1].id == "sonuc_ozeti");
    CHECK_FALSE(a.PanelAcik("sonuc_ozeti"));
    CHECK(a.PanelAcik("ozellikler"));
    a.PanelGoster("sonuc_ozeti", true);
    CHECK(a.PanelAcik("sonuc_ozeti"));
    a.DurumOgesiEkle({"motor", 10, true, "A", {}});
    a.DurumOgesiEkle({"koordinat", 10, false, "C", {}});
    CHECK(a.DurumOgeleri()[0].id == "koordinat");
    a.MenuKatkisiEkle({"Dosya/Son dosyalar", 0, "D", {}});
    CHECK(a.MenuKatkilari("Dosya/Son dosyalar").size() == 1);

    BetikliIletisimKutulari b;
    b.yanitlar = {"/tmp/x.op4", "", "1"};
    CHECK(b.DosyaAc("Aç", {}, "") == std::optional<std::string>("/tmp/x.op4"));
    CHECK_FALSE(b.DosyaKaydet("Kaydet", {}, ""));
    CHECK(b.Soru("Kaydedilsin mi?", "", {"Kaydet", "Kaydetme", "Vazgeç"}, 0) == 1);
    CHECK(b.Soru("Tükendi", "", {"Evet"}, 0) == -1);
    CHECK(b.sorulanlar.size() == 4);
}
