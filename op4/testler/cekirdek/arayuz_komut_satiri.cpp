// C (arayuz-goruntu) sınamaları — komut satırı / hızlı başlat (MIMARI §5.4, §12.1; kabul C1, C2) ve Türkçe katlama (S6).
#include <doctest/doctest.h>

#include <set>

#include "cekirdek/hizmetler.h"
#include "cekirdek/komut.h"
#include "cekirdek/komut_satiri.h"
#include "cekirdek/turkce.h"
#include "sinama_yardim.h"

using namespace op4;

namespace {

struct Duzenek {
    KomutYoneticisi k;
    Hizmetler h;
    std::vector<std::string> calisan;
    Duzenek() {
        std::string hata;
        REQUIRE_MESSAGE(k.KatalogYukle(sinama::Op4Dosyasi("veri/komutlar.json"), hata), hata);
        h.komutlar = &k;
        for (const KomutTanimi& t : k.Tanimlar()) {
            KomutIsleyici i;
            const std::string id = t.id;
            i.calistir = [this, id](KomutBaglami&) { calisan.push_back(id); };
            k.Bagla(t.id, i);
        }
    }
};

}  // namespace

TEST_CASE("C2 tamamlama: önek önce, sonra alt dizi; Türkçe katlama; İngilizce takma adlar") {
    Duzenek d;
    KomutSatiri ks;
    auto ilk = [&](const char* s) {
        const auto o = ks.Oneriler(d.k, s, OneriKumesi::Tumu);
        return o.empty() ? std::string() : o.front()->id;
    };
    CHECK(ilk("çöz") == "analiz.coz");
    CHECK(ilk("COZ") == "analiz.coz");
    CHECK(ilk("sığ") == "gorunum.sigdir");
    CHECK(ilk("SIG") == "gorunum.sigdir");
    CHECK(ilk("kay") == "dosya.kaydet");
    // İngilizce takma adlar (ARAYUZ_ILKELERI 25: "kolon" / "column").
    CHECK(ilk("solve") == "analiz.coz");
    CHECK(ilk("save") == "dosya.kaydet");
    CHECK(ilk("undo") == "duzenle.geri_al");
    CHECK(ilk("open") == "dosya.ac");
    CHECK(ilk("zoomext") == "gorunum.sigdir");
    // Alt dizi: "görünüm" adı geçen komutlar ("Kesit görünümü", "3B görünüm").
    const auto alt = ks.Oneriler(d.k, "görünüm", OneriKumesi::Tumu, 20);
    std::set<std::string> idler;
    for (const KomutTanimi* t : alt) idler.insert(t->id);
    CHECK(idler.count("gorunum.kesit_gorunumu") == 1);
    CHECK(idler.count("gorunum.3b") == 1);
    // Argüman yazılırken öneri komutun kendisi.
    CHECK(ilk("çöz hızlı") == "analiz.coz");
    // Kümeler: Şerit yalnız şeritte yeri olanlar, Menü yalnız menü yolu olanlar.
    for (const KomutTanimi* t : ks.Oneriler(d.k, "a", OneriKumesi::Serit, 50)) CHECK(t->serit.has_value());
    for (const KomutTanimi* t : ks.Oneriler(d.k, "a", OneriKumesi::Menu, 50)) CHECK_FALSE(t->menu.empty());
    // Her komutun en az bir İngilizce (ASCII, Türkçe katlamada değişmeyen) takma adı var.
    for (const KomutTanimi& t : d.k.Tanimlar()) {
        CAPTURE(t.id);
        bool ingilizce = false;
        for (const std::string& a : t.takmaAdlar)
            if (a.size() >= 3 && std::all_of(a.begin(), a.end(), [](char c) { return c >= 'A' && c <= 'Z'; })) ingilizce = true;
        CHECK(ingilizce);
    }
}

TEST_CASE("C2 çalıştırma: geçmiş, boşta Enter son komutu yineler, bilinmeyende yakın komut önerisi, Son kümesi") {
    Duzenek d;
    KomutSatiri ks;
    std::string ileti;
    CHECK(ks.Calistir(d.k, d.h, "çöz", ileti));
    CHECK(d.calisan.back() == "analiz.coz");
    CHECK(ks.Calistir(d.k, d.h, "  ızgara ", ileti));
    CHECK(d.calisan.back() == "gorunum.izgara");
    // Boş satır: tekrarlanır son komut (analiz.coz tekrarlanır; ızgara değil).
    const KomutTanimi* coz = d.k.Bul("analiz.coz");
    REQUIRE(coz);
    if (coz->tekrarlanir) {
        CHECK(ks.Calistir(d.k, d.h, "", ileti));
        CHECK(d.calisan.back() == "analiz.coz");
    }
    // Bilinmeyen: öğretici hata + yakın komutlar.
    CHECK_FALSE(ks.Calistir(d.k, d.h, "kaydett", ileti));
    CHECK(ileti.find("Bilinmeyen komut") != std::string::npos);
    CHECK(ileti.find("KAYDET") != std::string::npos);
    // Geçmiş: yukarı / aşağı ok.
    CHECK(ks.Gecmis().size() == 2);
    auto o = ks.Onceki("yazılan");
    REQUIRE(o);
    CHECK(*o == "ızgara");
    o = ks.Onceki("");
    REQUIRE(o);
    CHECK(*o == "çöz");
    CHECK_FALSE(ks.Onceki(""));
    o = ks.Sonraki();
    REQUIRE(o);
    CHECK(*o == "ızgara");
    o = ks.Sonraki();
    REQUIRE(o);
    CHECK(*o == "yazılan");  // gezinmeden önceki girdi geri gelir
    CHECK_FALSE(ks.Sonraki());
    // Son kümesi: en yeni başta.
    REQUIRE(ks.SonKomutlar().size() >= 2);
    CHECK(ks.SonKomutlar().front() == (coz->tekrarlanir ? "analiz.coz" : "gorunum.izgara"));
    const auto bos = ks.Oneriler(d.k, "", OneriKumesi::Son);
    REQUIRE_FALSE(bos.empty());
    CHECK(bos.front()->id == ks.SonKomutlar().front());
    // Öneriden çalıştırma.
    CHECK(ks.OneriCalistir(d.k, d.h, *d.k.Bul("gorunum.sigdir"), ileti));
    CHECK(d.calisan.back() == "gorunum.sigdir");
}

TEST_CASE("C1 kısayollar: tek harf kısayolu yok; F, K, G yerine Shift+F, Ctrl+Shift+K, F7") {
    Duzenek d;
    for (const KomutTanimi& t : d.k.Tanimlar()) {
        CAPTURE(t.id);
        if (t.kisayol.empty()) continue;
        const bool tekHarf = t.kisayol.size() == 1;
        CHECK_FALSE(tekHarf);
    }
    CHECK(d.k.KisayolBul("Shift+F")->id == "gorunum.sigdir");
    CHECK(d.k.KisayolBul("Ctrl+Shift+K")->id == "gorunum.kesit_gorunumu");
    CHECK(d.k.KisayolBul("F7")->id == "gorunum.izgara");
    CHECK(d.k.KisayolBul("Alt+1")->id == "gorunum.3b");
    CHECK(d.k.KisayolBul("PageUp")->id == "gorunum.ust_kat");
    // Şerit sekmeleri Stüdyo sırasında (MIMARI §25): Dosya · Model · Düzenle · Yükler · Analiz · Tasarım · Görünüm · Raporlar.
    const std::vector<std::string> beklenen{"Dosya", "Model", "Düzenle", "Yükler", "Analiz", "Tasarım", "Görünüm", "Raporlar"};
    CHECK(d.k.Sekmeler() == beklenen);
    for (const KomutTanimi& t : d.k.Tanimlar())
        if (t.serit) CHECK_MESSAGE(std::find(beklenen.begin(), beklenen.end(), t.serit->sekme) != beklenen.end(), t.id);
}

TEST_CASE("S6 Türkçe katlama: noktalı / noktasız I, ondalık virgül") {
    CHECK(TurkceKatla("İSTANBUL") == TurkceKatla("istanbul"));
    CHECK(TurkceKatla("ISPARTA") == TurkceKatla("ısparta"));
    CHECK(TurkceKatla("ŞĞÜÖÇ") == "sguoc");
    CHECK(TurkceKatla("Seç & Süz") == "sec & suz");
    CHECK(TurkceOnekMi("SEÇİ", "seçimi temizle"));
    CHECK_FALSE(TurkceOnekMi("seçx", "seçim"));
    CHECK(OndalikVirgul(9.0, 2) == "9");
    CHECK(OndalikVirgul(-13.5, 2) == "-13,5");
    double v = 0;
    CHECK(SayiOku(" 6 ", v));
    CHECK(v == 6);
    CHECK(SayiOku("1,04", v));
    CHECK(v == doctest::Approx(1.04));
    CHECK_FALSE(SayiOku("1,0,4", v));
}
