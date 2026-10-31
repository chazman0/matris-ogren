// op4 C++ sınamaları (D) — atomik yazma (MIMARI §13.2, D23; kabul D2): Windows yolu sahte işlemlerle (ReplaceFileW
// benzetimi: açık tanıtıcı varken paylaşım ihlali), POSIX yolu gerçek işlemler + kilit benzetimiyle; yarım yazmada hedef
// bozulmaz; Türkçe karakterli yol; oturum kilidi.
#include <doctest/doctest.h>

#include <map>
#include <set>

#include "dosya_sahte.h"

using namespace op4;
using namespace op4::sinama;

namespace {

// Bellek içi "Windows dosya sistemi": tutulan (açık tanıtıcılı) dosyada ReplaceFileW paylaşım ihlali verir.
struct SahteWinDosyaSistemi {
    std::map<std::string, std::string> dosyalar;
    std::set<std::string> tutulan;   // FILE_SHARE_READ tanıtıcısı açık (eşitleme istemcisi, başka program)
    int birakmaBeklemesi = -1;       // kaçıncı beklemeden sonra tutulan bırakılsın (−1: hiç)
    int bekleme = 0, beklenenMs = 0, yerineKoyma = 0;
    bool diskDolu = false, kalici = false;

    AtomikYazmaIslemleri Islemler() {
        AtomikYazmaIslemleri is;
        is.geciciYaz = [this](const std::string& g, std::string_view v, std::string& h) {
            if (diskDolu) {
                dosyalar[g] = std::string(v.substr(0, v.size() / 2));  // yarım yazılmış geçici
                h = "Yazılamadı (disk dolu): " + g;
                return false;
            }
            dosyalar[g] = std::string(v);
            return true;
        };
        is.yerineKoy = [this](const std::string& g, const std::string& hedef, bool bak, std::string& h) {
            ++yerineKoyma;
            if (kalici) {
                h = "Dosya yerine konamadı (erişim reddedildi): " + hedef + ".";
                return YerineKoymaSonucu::Hata;
            }
            if (tutulan.count(hedef)) return YerineKoymaSonucu::PaylasimIhlali;  // ERROR_SHARING_VIOLATION
            if (bak && dosyalar.count(hedef)) dosyalar[hedef + ".bak"] = dosyalar[hedef];
            dosyalar[hedef] = dosyalar[g];
            dosyalar.erase(g);
            return YerineKoymaSonucu::Tamam;
        };
        is.bekle = [this](int ms) {
            ++bekleme;
            beklenenMs += ms;
            if (bekleme == birakmaBeklemesi) tutulan.clear();
        };
        is.sil = [this](const std::string& y) { dosyalar.erase(y); };
        return is;
    }
    size_t GeciciSayisi() const {
        size_t n = 0;
        for (const auto& [y, v] : dosyalar)
            if (y.find(".~op4-") != std::string::npos) ++n;
        return n;
    }
};

std::vector<std::string> Liste(const std::string& klasor) {
    std::vector<std::string> o;
    for (const auto& g : std::filesystem::directory_iterator(U8Yol(klasor))) o.push_back(U8(g.path().filename()));
    std::sort(o.begin(), o.end());
    return o;
}

}  // namespace

TEST_CASE("D2 Windows yolu (sahte): paylaşım ihlalinde 5 × 100 ms yeniden deneme, sonra başarı") {
    SahteWinDosyaSistemi fs;
    const std::string hedef = "C:\\Kullanıcılar\\Şükrü\\OneDrive\\Proje ŞĞİı\\dene.op4";
    fs.dosyalar[hedef] = "eski";
    fs.tutulan.insert(hedef);
    fs.birakmaBeklemesi = 3;  // eşitleme istemcisi 3. beklemeden sonra bırakıyor
    std::string hata;
    int deneme = 0;
    REQUIRE_MESSAGE(AtomikYazIle(fs.Islemler(), hedef, "yeni", true, hata, {}, &deneme), hata);
    CHECK(deneme == 4);
    CHECK(fs.bekleme == 3);
    CHECK(fs.beklenenMs == 300);
    CHECK(fs.dosyalar[hedef] == "yeni");
    CHECK(fs.dosyalar[hedef + ".bak"] == "eski");
    CHECK(fs.GeciciSayisi() == 0);
}

TEST_CASE("D2 Windows yolu (sahte): tutulmaya devam ederse 5 denemede vazgeçilir, hedef değişmez, geçici silinir") {
    SahteWinDosyaSistemi fs;
    const std::string hedef = "C:\\op4 dene ŞĞİı\\proje.op4";
    fs.dosyalar[hedef] = "eski";
    fs.tutulan.insert(hedef);
    std::string hata;
    int deneme = 0;
    CHECK_FALSE(AtomikYazIle(fs.Islemler(), hedef, "yeni", false, hata, {}, &deneme));
    CHECK(deneme == 5);
    CHECK(fs.bekleme == 4);
    CHECK(fs.beklenenMs == 400);
    CHECK(fs.dosyalar[hedef] == "eski");
    CHECK(fs.GeciciSayisi() == 0);
    CHECK(hata.find("başka bir program tarafından kullanılıyor") != std::string::npos);
    CHECK(hata.find("eski hâli değişmedi") != std::string::npos);
}

TEST_CASE("D2 Windows yolu (sahte): yarım yazma ve kalıcı hata hedefi bozmaz; kalıcı hata yeniden denenmez") {
    SahteWinDosyaSistemi fs;
    const std::string hedef = "D:\\proje.op4";
    fs.dosyalar[hedef] = "eski";
    fs.diskDolu = true;
    std::string hata;
    CHECK_FALSE(AtomikYazIle(fs.Islemler(), hedef, "yepyeni içerik", false, hata));
    CHECK(fs.dosyalar[hedef] == "eski");
    CHECK(fs.GeciciSayisi() == 0);
    CHECK(fs.yerineKoyma == 0);
    CHECK(hata.find("disk dolu") != std::string::npos);

    fs.diskDolu = false;
    fs.kalici = true;
    int deneme = 0;
    CHECK_FALSE(AtomikYazIle(fs.Islemler(), hedef, "yeni", false, hata, {}, &deneme));
    CHECK(deneme == 1);
    CHECK(fs.dosyalar[hedef] == "eski");
    CHECK(fs.GeciciSayisi() == 0);
    CHECK(hata.find("eski hâli değişmedi") != std::string::npos);
    CHECK_FALSE(AtomikYazIle(fs.Islemler(), "", "x", false, hata));
}

TEST_CASE("D2 POSIX yolu (gerçek işlemler + kilit benzetimi), Türkçe karakterli yol") {
    GeciciDizin d;
    const std::string klasor = d.Kur("Proje ŞĞİı");
    const std::string hedef = klasor + "/dene.op4";
    std::string hata;
    REQUIRE_MESSAGE(AtomikYaz(hedef, "birinci", false, hata), hata);
    CHECK(DosyaIcerigi(hedef) == "birinci");

    // İlk 3 yerine koyma "dosya kilitli" döner (POSIX'te paylaşım kilidi yok; benzetim).
    const AtomikYazmaIslemleri& gercek = PlatformAtomikIslemleri();
    int kilitli = 3, bekleme = 0;
    AtomikYazmaIslemleri is = gercek;
    is.yerineKoy = [&](const std::string& g, const std::string& h, bool bak, std::string& m) {
        if (kilitli-- > 0) return YerineKoymaSonucu::PaylasimIhlali;
        return gercek.yerineKoy(g, h, bak, m);
    };
    is.bekle = [&](int ms) {
        ++bekleme;
        gercek.bekle(ms / 50);  // sınama hızlı kalsın
    };
    int deneme = 0;
    REQUIRE_MESSAGE(AtomikYazIle(is, hedef, "ikinci", true, hata, {}, &deneme), hata);
    CHECK(deneme == 4);
    CHECK(bekleme == 3);
    CHECK(DosyaIcerigi(hedef) == "ikinci");
    CHECK(DosyaIcerigi(hedef + ".bak") == "birinci");
    CHECK(Liste(klasor) == std::vector<std::string>{"dene.op4", "dene.op4.bak"});

    // Kilit bırakılmazsa: 5 deneme, hedef "ikinci" olarak kalır, geçici dosya kalmaz.
    kilitli = 100;
    CHECK_FALSE(AtomikYazIle(is, hedef, "üçüncü", false, hata, {}, &deneme));
    CHECK(deneme == 5);
    CHECK(DosyaIcerigi(hedef) == "ikinci");
    CHECK(Liste(klasor) == std::vector<std::string>{"dene.op4", "dene.op4.bak"});

    // Geçici dosya yazımı yarıda kesilirse (disk doldu benzetimi): hedef değişmez, geçici kalmaz.
    AtomikYazmaIslemleri yarim = gercek;
    yarim.geciciYaz = [&](const std::string& g, std::string_view v, std::string& m) {
        gercek.geciciYaz(g, v.substr(0, 3), m);
        m = "Yazılamadı (disk dolu): " + g;
        return false;
    };
    CHECK_FALSE(AtomikYazIle(yarim, hedef, "dördüncü", false, hata));
    CHECK(DosyaIcerigi(hedef) == "ikinci");
    CHECK(Liste(klasor) == std::vector<std::string>{"dene.op4", "dene.op4.bak"});

    // Var olmayan klasör: kalıcı hata.
    CHECK_FALSE(AtomikYaz(d.Yol("yok/klasör/x.op4"), "x", false, hata));
    CHECK(hata.find("klasör bulunamadı") != std::string::npos);
}

TEST_CASE("Geçici ad hedefle aynı klasörde ve benzersiz") {
    const std::string a = GeciciDosyaAdi("/x/y/proje.op4"), b = GeciciDosyaAdi("/x/y/proje.op4");
    CHECK(a != b);
    CHECK(a.rfind("/x/y/proje.op4.~op4-", 0) == 0);
    CHECK(a.size() > 4);
    CHECK(a.substr(a.size() - 4) == ".tmp");
}

TEST_CASE("Oturum kilidi: tutulurken başkası alamaz, bırakınca dosya silinir") {
    GeciciDizin d;
    const std::string yol = d.Yol("oturum ş.kilit");
    {
        OturumKilidi a;
        REQUIRE(a.Al(yol));
        CHECK(a.Tutuluyor());
        CHECK(KilitTutuluyorMu(yol));
        OturumKilidi b;
        CHECK_FALSE(b.Al(yol));
        a.Birak();
        CHECK_FALSE(KilitTutuluyorMu(yol));
        CHECK_FALSE(DosyaVar(yol));
        CHECK(b.Al(yol));
    }
    CHECK_FALSE(KilitTutuluyorMu(yol));
    ProjeOkumaKilidi k;
    CHECK(k.Ac(yol));
    k.Birak();
}
