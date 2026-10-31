// op4 C++ sınamaları (D) — dosya işlemleri akışı: Kaydet / Farklı kaydet / Aç gidiş-dönüşü (model/bina.json = Metin(),
// görünüm katkısı geri gelir, bilinmeyen girdi korunur), kirli işareti ve başlık, kapanış onayı, otomatik kayıt (2 s) ve
// kurtarma, son dosyalar ve ayar kalıcılığı, eski biçimlerden açma, bozuk dosya, daha yeni sürüm, IFC ve bina dışa aktarma
// (MIMARI §13, §14.1; kabul D1–D4, D10).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include "cekirdek/proje_dosyasi.h"
#include "dosya_sahte.h"

using namespace op4;
using namespace op4::sinama;
using nlohmann::json;

namespace {

std::string ZipGirdisi(const std::string& yol, const char* ad) {
    const OkumaSonucu o = ProjeOku(yol);
    REQUIRE_MESSAGE(o.basarili, o.hata);
    const std::string* g = o.icerik.Al(ad);
    return g ? *g : std::string("<yok>");
}

void Degistir(DOrtam& o, const std::string& baslik) {
    const IslemRaporu r = ModelIslemiUygula(o.h, islem::BASLIK_DEGISTIR, json{{"baslik", baslik}}.dump());
    REQUIRE(r.ModelDegisti());
}

}  // namespace

TEST_CASE("D1 Kaydet / Aç gidiş-dönüşü: model/bina.json = Metin(), görünüm geri gelir, Türkçe yol, başlık ve kirli") {
    DOrtam o;
    CHECK(o.belge.PencereBasligi() == "op4 — Adsız 1");
    REQUIRE(o.Komut("dosya.yeni_sablon", "celik-cbf-3kat"));
    CHECK(o.cekirdek.Metin() == DOrtam::Sablon("celik-cbf-3kat"));  // şablon metni motor olmadan, olduğu gibi
    CHECK(o.belge.Ad() == "Adsız 2");
    Degistir(o, "Ofis ŞĞİı");
    CHECK(o.belge.Kirli());
    CHECK(o.belge.PencereBasligi() == "op4 — Adsız 2 •");
    const std::string metin = o.cekirdek.Metin();

    const std::string yol = o.dizin.Kur("Proje ŞĞİı") + "/dene.op4";
    REQUIRE(o.Komut("dosya.farkli_kaydet", yol));
    CHECK_FALSE(o.belge.Kirli());
    CHECK(o.belge.Yol() == yol);
    CHECK(o.belge.PencereBasligi() == "op4 — dene.op4");
    CHECK(ZipGirdisi(yol, proje_yolu::MODEL) == metin);
    CHECK(ZipGirdisi(yol, proje_yolu::GORUNUM) == o.gorunumKatkisi.durum);
    CHECK(ZipGirdisi(yol, proje_yolu::ONIZLEME).compare(0, 4, "\x89PNG") == 0);
    CHECK(json::parse(ZipGirdisi(yol, proje_yolu::MANIFEST))["model_ozeti"].get<std::string>().find("çubuk") !=
          std::string::npos);
    CHECK(o.SatirdaVar("Kaydedildi: dene.op4"));

    // Başka bir model ve görünüm, sonra aç: ikisi de geri gelir; belge temiz, yol dosya.
    REQUIRE(o.Komut("dosya.yeni"));
    CHECK(o.cekirdek.Ozet().bos);
    o.gorunumKatkisi.okunan.clear();
    const int sifir = o.gorunumKatkisi.sifirlama;
    REQUIRE(o.Komut("dosya.ac", "\"" + yol + "\""));
    CHECK(o.cekirdek.Metin() == metin);
    CHECK(o.gorunumKatkisi.okunan == o.gorunumKatkisi.durum);
    CHECK(o.gorunumKatkisi.sifirlama == sifir + 1);
    CHECK_FALSE(o.belge.Kirli());
    CHECK(o.belge.Yol() == yol);
    CHECK_FALSE(o.belge.SaltOkunur());

    // Ctrl+S (Kaydet) aynı yola, pencere sormadan; baytlar tutarlı (aynı yürütücüde aynı içerik → aynı model girdisi).
    Degistir(o, "Ofis 2");
    o.iletisim.sorulanlar.clear();
    REQUIRE(o.Komut("dosya.kaydet"));
    CHECK(o.iletisim.sorulanlar.empty());
    CHECK(ZipGirdisi(yol, proje_yolu::MODEL) == o.cekirdek.Metin());
}

TEST_CASE("D1 bilinmeyen girdiler açıp kaydedince korunur; sonuç yoksa sonuc/ yazılmaz") {
    DOrtam o;
    REQUIRE(o.Komut("dosya.yeni_sablon", "betonarme-tek-aciklik"));
    const std::string yol = o.dizin.Yol("yabanci.op4");
    ProjeIcerigi i;
    i.Koy(proje_yolu::MODEL, o.cekirdek.Metin());
    i.Koy("ifc/kaynak.json", "{\"kaynak\":\"x.ifc\"}");
    i.Koy("gelecek/eklenti.dat", std::string("\0\1\2", 3));
    i.Koy(proje_yolu::SONUC_OZETI, "{bozuk");  // okunamayan sonuç uyarıyla atlanır
    ProjeManifest m;
    m.kaydedildi = "2026-10-31T00:00:00Z";
    std::string hata;
    REQUIRE(ProjeYaz(yol, i, m, hata));
    REQUIRE(o.Komut("dosya.ac", yol));
    CHECK(o.SatirdaVar("Kayıtlı sonuçlar okunamadı"));
    CHECK_FALSE(o.sonuc.Var());
    REQUIRE(o.Komut("dosya.kaydet"));
    const OkumaSonucu r = ProjeOku(yol);
    REQUIRE(r.basarili);
    CHECK(*r.icerik.Al("ifc/kaynak.json") == "{\"kaynak\":\"x.ifc\"}");
    CHECK(*r.icerik.Al("gelecek/eklenti.dat") == std::string("\0\1\2", 3));
    CHECK_FALSE(r.icerik.Var(proje_yolu::SONUC_OZETI));  // sonuç katkısı, sonuç yokken girdiyi siler
}

TEST_CASE("D4 kapanış onayı: Kaydet / Kaydetme / Vazgeç; Çıkış pencereyi kapatır") {
    DOrtam o;
    int kapatma = 0;
    o.arayuz.pencereyiKapat = [&] { ++kapatma; };
    CHECK(o.h.kapatmaOnayi());  // temiz belge: sormadan
    REQUIRE(o.Komut("dosya.yeni_sablon", "celik-1kat-depo"));
    Degistir(o, "Depo");
    o.iletisim.yanitlar = {"2"};  // Vazgeç
    CHECK_FALSE(o.h.kapatmaOnayi());
    o.iletisim.yanitlar = {"-1"};  // Esc
    CHECK_FALSE(o.h.kapatmaOnayi());
    o.iletisim.yanitlar = {"0", ""};  // Kaydet → Farklı kaydet penceresi iptal → kapanma
    CHECK_FALSE(o.h.kapatmaOnayi());
    const std::string yol = o.dizin.Yol("depo.op4");
    o.iletisim.yanitlar = {"0", yol};  // Kaydet → Farklı kaydet → yol
    CHECK(o.h.kapatmaOnayi());
    CHECK(DosyaVar(yol));
    CHECK_FALSE(o.belge.Kirli());
    Degistir(o, "Depo 2");  // onaydan sonra yeni değişiklik: yeniden sorulur
    o.iletisim.yanitlar = {"1"};  // Kaydetme
    REQUIRE(o.Komut("dosya.cikis"));
    CHECK(kapatma == 1);
    CHECK(o.iletisim.sorulanlar.back() == "op4 kapatılıyor");
    // Yeni / Aç da kaydedilmemiş değişikliği sorar.
    DOrtam p;
    Degistir(p, "x");
    p.iletisim.yanitlar = {"2"};
    CHECK_FALSE(p.dosya->Yeni());
    CHECK(p.iletisim.sorulanlar.back() == "Kaydedilmemiş değişiklikler");
}

TEST_CASE("D4 otomatik kayıt (2 s) ve kurtarma: kayıt, çökme benzetimi, Kurtar / Sil / Sonra, temiz kapanışta silinir") {
    GeciciDizin ortak;
    const std::string kurtarmaDizini = ortak.Kur("kurtarma");
    const std::string asilYol = ortak.Yol("asıl proje.op4");
    std::string beklenen;
    {
        DOrtamAyari oa;
        oa.kurtarmaDizini = kurtarmaDizini;
        DOrtam o(oa);
        o.dosya->KareIsi(0);  // ilk kare: kurtarma taraması (boş)
        CHECK_FALSE(o.dosya->KurtarmaSorusuAcik());
        REQUIRE(o.Komut("dosya.yeni_sablon", "betonarme-2kat-3x2"));
        REQUIRE(o.Komut("dosya.farkli_kaydet", asilYol));
        Degistir(o, "Kaydedilmemiş ŞĞİı");
        o.dosya->KareIsi(100);   // zamanlayıcı kurulur
        o.dosya->KareIsi(1500);  // 1,4 s: henüz yok
        CHECK_FALSE(DosyaVar(o.dosya->KurtarmaDosyasi()));
        o.dosya->KareIsi(2200);  // 2,1 s: yazıldı
        REQUIRE(DosyaVar(o.dosya->KurtarmaDosyasi()));
        CHECK(o.dosya->OtomatikKayitSayisi() == 1);
        o.dosya->KareIsi(9000);  // değişiklik yok: yeniden yazılmaz
        CHECK(o.dosya->OtomatikKayitSayisi() == 1);
        const std::string kz = o.dosya->KurtarmaDosyasi();
        CHECK(json::parse(DosyaIcerigi(kz.substr(0, kz.size() - 4) + ".json"))["asil_yol"] == asilYol);
        // Yaşayan oturumun kaydı başka oturumlarca "artık" sayılmaz (oturum kilidi).
        CHECK(KurtarmaKayitlari(kurtarmaDizini).empty());
        // "Çökme": kapanış onayı yok, belge kirli → yıkıcı kaydı silmez (kilit düşer).
        Degistir(o, "Son hâl");
        beklenen = o.cekirdek.Metin();
        o.dosya->KareIsi(9100);
        o.dosya->KareIsi(11200);
        CHECK(o.dosya->OtomatikKayitSayisi() == 2);
        CHECK(ZipGirdisi(kz, proje_yolu::MODEL) == beklenen);
    }
    const std::vector<KurtarmaKaydi> kayitlar = KurtarmaKayitlari(kurtarmaDizini);
    REQUIRE(kayitlar.size() == 1);
    CHECK(kayitlar[0].asilYol == asilYol);
    CHECK(kayitlar[0].baslik == "asıl proje.op4");
    CHECK(kayitlar[0].zaman == "2026-10-31T12:00:00Z");

    // Yeni oturum aynı kurtarma klasörüyle: ilk karede soru açılır; Sonra → kapanır, kayıt kalır; KURTAR → yeniden.
    int gosterildi = 0;
    DOrtamAyari pa;
    pa.kurtarmaDizini = kurtarmaDizini;
    pa.platform.kurtarmaGoster = [&] { ++gosterildi; };
    DOrtam p(pa);
    p.dosya->KareIsi(0);
    CHECK(p.dosya->KurtarmaSorusuAcik());
    CHECK(gosterildi == 1);
    REQUIRE(p.dosya->Kurtarmalar().size() == 1);
    REQUIRE(p.Komut("dosya.kurtar", "sonra"));
    CHECK_FALSE(p.dosya->KurtarmaSorusuAcik());
    CHECK(p.dosya->Kurtarmalar().size() == 1);
    REQUIRE(p.Komut("dosya.kurtar"));
    CHECK(p.dosya->KurtarmaSorusuAcik());
    CHECK(gosterildi == 2);
    REQUIRE(p.Komut("dosya.kurtar", "1"));
    CHECK(p.cekirdek.Metin() == beklenen);
    CHECK(p.belge.Kirli());  // asıl dosyaya kaydedilmemiş değişiklik
    CHECK(p.belge.Yol() == asilYol);
    CHECK(p.belge.PencereBasligi() == "op4 — asıl proje.op4 •");
    CHECK(p.dosya->Kurtarmalar().empty());
    CHECK_FALSE(DosyaVar(kayitlar[0].dosya));    // eski kayıt silindi …
    CHECK(DosyaVar(p.dosya->KurtarmaDosyasi()));  // … bu oturumun kaydına taşındı
    CHECK(ZipGirdisi(p.dosya->KurtarmaDosyasi(), proje_yolu::MODEL) == beklenen);
    // Temiz kapanış (Kaydetme): kurtarma kaydı silinir.
    const std::string kendi = p.dosya->KurtarmaDosyasi();
    p.iletisim.yanitlar = {"1"};
    CHECK(p.h.kapatmaOnayi());
    p.cozum.reset();
    p.dosya.reset();
    CHECK_FALSE(DosyaVar(kendi));
    CHECK(KurtarmaKayitlari(kurtarmaDizini).empty());
}

TEST_CASE("D4 kurtarma: Sil ve bozuk kayıt") {
    DOrtam o;
    const std::string dizin = o.dizin.Yol("yerel/kurtarma");
    DosyaYaz(dizin + "/aaaa.op4", "PK\x03\x04 bozuk");
    DosyaYaz(dizin + "/aaaa.json", R"({"bicim":1,"asil_yol":"","baslik":"Adsız 7","zaman":"2026-10-30T09:00:00Z"})");
    o.dosya->KareIsi(0);
    REQUIRE(o.dosya->Kurtarmalar().size() == 1);
    CHECK(o.dosya->Kurtarmalar()[0].baslik == "Adsız 7");
    CHECK_FALSE(o.dosya->Kurtar(0));
    CHECK(o.SatirdaVar("Kurtarma kaydı açılamadı"));
    REQUIRE(o.Komut("dosya.kurtar", "sil 1"));
    CHECK(o.dosya->Kurtarmalar().empty());
    CHECK_FALSE(DosyaVar(dizin + "/aaaa.op4"));
    CHECK_FALSE(DosyaVar(dizin + "/aaaa.json"));
    CHECK_FALSE(o.dosya->KurtarmaSorusuAcik());
}

TEST_CASE("D5 son dosyalar: en yeni başta, tekrarsız, en çok 10; ayarlar.json'a yazılır; bulunamayan dosya düşer") {
    DOrtam o;
    REQUIRE(o.Komut("dosya.yeni_sablon", "betonarme-tek-aciklik"));
    std::vector<std::string> yollar;
    for (int i = 0; i < 12; ++i) {
        yollar.push_back(o.dizin.Yol("proje " + std::to_string(i) + ".op4"));
        REQUIRE(o.dosya->FarkliKaydet(yollar.back()));
    }
    auto& son = o.ayarlar.dosya.sonDosyalar;
    REQUIRE(son.size() == 10);
    CHECK(son.front() == yollar[11]);
    CHECK(son.back() == yollar[2]);
    REQUIRE(o.dosya->Ac(yollar[5]));
    CHECK(son.front() == yollar[5]);
    CHECK(son.size() == 10);
    CHECK(o.ayarlar.dosya.sonKlasor == o.dizin.Yol());
    // Kalıcılık: ayarlar.json okununca aynı liste.
    Ayarlar okunan;
    std::string hata;
    REQUIRE(AyarlariOku(DosyaIcerigi(o.h.bilgi.ayarDizini + "/ayarlar.json"), okunan, hata));
    CHECK(okunan.dosya.sonDosyalar == son);
    // Silinmiş dosya listeden düşer.
    std::filesystem::remove(U8Yol(yollar[11]));
    CHECK_FALSE(o.dosya->Ac(yollar[11]));
    CHECK(std::find(son.begin(), son.end(), yollar[11]) == son.end());
    CHECK(o.SatirdaVar("Dosya bulunamadı"));
}

TEST_CASE("D3 eski biçimlerden açma: Faz 0 .op4 (kamera, boş model), .matris, .json; kaydederken Farklı kaydet") {
    DOrtam o;
    const std::string deneme = o.dizin.Yol("faz0.op4");
    DosyaYaz(deneme, R"({"bicim": "op4-proje", "bicim_surumu": 1, "kamera": {"hedef": [1, 2, 3], "uzaklik": 9,
                 "sapma": 0.5, "egim": 0.25}, "gorunum": {"kesit": false, "kenarlar": true, "izgara": true}, "model": {}})");
    REQUIRE(o.Komut("dosya.ac", deneme));
    CHECK(o.cekirdek.Ozet().bos);
    CHECK(json::parse(o.gorunumKatkisi.okunan)["kamera"]["uzaklik"] == 9);
    CHECK(o.belge.Yol().empty());  // eski biçim: Adsız; Ctrl+S yeni biçimi sorarak yazar
    CHECK(o.SatirdaVar("İçe aktarıldı: faz0.op4"));
    o.iletisim.yanitlar = {o.dizin.Yol("faz0-yeni.op4")};
    REQUIRE(o.Komut("dosya.kaydet"));
    CHECK(o.iletisim.sorulanlar.back() == "Farklı kaydet");
    CHECK(BicimSapta(DosyaIcerigi(o.dizin.Yol("faz0-yeni.op4")).substr(0, 4), ".op4") == DosyaBicimi::Op4);
    CHECK(DosyaIcerigi(deneme).front() == '{');  // eski dosyaya dokunulmadı

    const std::string sablon = DOrtam::Sablon("betonarme-3kat-3x3");
    DosyaYaz(o.dizin.Yol("web.matris"), "{\"tur\":\"matris-proje\",\"surum\":1,\"bina\":" + sablon + ",\"gorunum\":null}");
    REQUIRE(o.Komut("dosya.ice_aktar", o.dizin.Yol("web.matris")));
    CHECK(o.cekirdek.Metin() == sablon);
    // İçe aktarılan dosya Kaydet'te Farklı kaydet penceresini açar (iptal: hiçbir şey yazılmaz).
    o.iletisim.yanitlar = {""};
    CHECK(o.Komut("dosya.kaydet"));
    CHECK(o.iletisim.sorulanlar.back() == "Farklı kaydet");
    CHECK_FALSE(DosyaVar(o.dizin.Yol("web.op4")));

    // IFC henüz içe alınmaz; mevcut model değişmez.
    const std::string onceki = o.cekirdek.Metin();
    DosyaYaz(o.dizin.Yol("yapi.ifc"), "ISO-10303-21;\n");
    o.Komut("dosya.ac", o.dizin.Yol("yapi.ifc"));
    CHECK(o.SatirdaVar("Faz 6"));
    CHECK(o.cekirdek.Metin() == onceki);
}

TEST_CASE("D1/D2 bozuk dosya açılmaz, model değişmez; daha yeni biçim salt okunur açılır") {
    DOrtam o;
    REQUIRE(o.Komut("dosya.yeni_sablon", "celik-1kat-depo"));
    const std::string iyi = o.dizin.Yol("iyi.op4");
    REQUIRE(o.dosya->FarkliKaydet(iyi));
    const std::string zip = DosyaIcerigi(iyi);
    DosyaYaz(o.dizin.Yol("kesik.op4"), zip.substr(0, zip.size() * 2 / 3));
    const std::string once = o.cekirdek.Metin();
    REQUIRE(o.Komut("dosya.yeni"));
    const std::string bos = o.cekirdek.Metin();
    CHECK_FALSE(o.dosya->Ac(o.dizin.Yol("kesik.op4")));
    CHECK(o.cekirdek.Metin() == bos);
    CHECK(o.SatirdaVar("'kesik.op4' açılamadı: Dosya bozuk ya da yarım kalmış"));
    CHECK(once != bos);

    OkumaSonucu r = ProjeOku(iyi);
    REQUIRE(r.basarili);
    r.manifest.bicimSurumu = 2;
    std::string hata;
    REQUIRE(ProjeYaz(o.dizin.Yol("yeni.op4"), r.icerik, r.manifest, hata));
    REQUIRE(o.dosya->Ac(o.dizin.Yol("yeni.op4")));
    CHECK(o.belge.SaltOkunur());
    CHECK(o.belge.PencereBasligi() == "op4 — yeni.op4 (salt okunur)");
    o.iletisim.yanitlar = {""};
    CHECK_FALSE(o.dosya->Kaydet());  // salt okunur: Farklı kaydet'e gider (iptal)
    CHECK(o.iletisim.sorulanlar.back() == "Farklı kaydet");
}

TEST_CASE("D10 IFC dışa aktarma: çekirdek üstünden, uygulama op4 · Opus Fortis, sabit zaman, aynı model → aynı bayt") {
    DOrtam o;
    CHECK_FALSE(o.komutlar.Durum("dosya.ifc_disa", o.h).kullanilabilir);  // boş model
    REQUIRE(o.Komut("dosya.yeni_sablon", "celik-cbf-3kat"));
    CHECK(o.komutlar.Durum("dosya.ifc_disa", o.h).kullanilabilir);
    const std::string a = o.dizin.Yol("çıktı/a.ifc"), b = o.dizin.Yol("çıktı/b");
    o.dizin.Kur("çıktı");
    REQUIRE(o.Komut("dosya.ifc_disa", a));
    REQUIRE(o.Komut("dosya.ifc_disa", b));  // uzantı eklenir
    CHECK(o.cekirdek.ifcCagri == 2);
    const json s = json::parse(o.cekirdek.sonIfcSecenek);
    CHECK(s["uygulama"]["ad"] == "op4");
    CHECK(s["uygulama"]["firma"] == "Opus Fortis");
    CHECK(s["uygulama"]["tam_ad"] == "op4 · Opus Fortis");
    CHECK(s["uygulama"]["surum"] == "0.1.0");
    CHECK(s["zaman"] == "2026-01-01T00:00:00");
    CHECK(s["analiz"] == true);
    CHECK(s["dc"] == false);  // sonuç yok
    CHECK(DosyaIcerigi(a) == DosyaIcerigi(b + ".ifc"));
    CHECK(DosyaIcerigi(a).rfind("ISO-10303-21;", 0) == 0);
    // Pencereden: önerilen ad çekirdeğin dosya adı.
    o.iletisim.yanitlar = {""};
    CHECK_FALSE(o.dosya->IfcDisaAktar());
    CHECK(o.iletisim.sorulanlar.back() == "IFC olarak dışa aktar");
}

TEST_CASE("Bina dışa aktarma: .json = Metin(), .matris web biçimi ve yeniden içe aktarılınca aynı model") {
    DOrtam o;
    REQUIRE(o.Komut("dosya.yeni_sablon", "betonarme-4kat-4x3"));
    const std::string metin = o.cekirdek.Metin();
    REQUIRE(o.Komut("dosya.bina_disa", o.dizin.Yol("bina.json")));
    CHECK(DosyaIcerigi(o.dizin.Yol("bina.json")) == metin + "\n");
    REQUIRE(o.Komut("dosya.bina_disa", o.dizin.Yol("web")));
    const json w = json::parse(DosyaIcerigi(o.dizin.Yol("web.matris")));
    CHECK(w["tur"] == "matris-proje");
    CHECK(w["surum"] == 1);
    REQUIRE(o.Komut("dosya.yeni"));
    REQUIRE(o.Komut("dosya.ac", o.dizin.Yol("web.matris")));
    CHECK(o.cekirdek.Metin() == metin);
}

TEST_CASE("Şablondan yeni: geçersiz ad ve bulunmayan şablon; dizin") {
    DOrtam o;
    CHECK_FALSE(o.dosya->SablondanYeni("../../etc/passwd"));
    CHECK(o.SatirdaVar("geçersiz şablon adı"));
    CHECK_FALSE(o.dosya->SablondanYeni("olmayan-sablon"));
    CHECK(o.SatirdaVar("Şablon bulunamadı"));
    REQUIRE(o.Komut("dosya.yeni_sablon"));  // seçici kancası yok: liste komut satırına
    CHECK(o.SatirdaVar("Şablonlar: betonarme-tek-aciklik"));
    CHECK(o.dosya->Sablonlar().size() == 9);
}
