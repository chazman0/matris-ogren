// op4 C++ sınamaları (D) — .op4 ZIP biçimi: mimetype ilk ve sıkıştırmasız, manifest, gidiş-dönüş bayt eşitliği, bilinmeyen
// girdilerin korunması, daha yeni biçim, bozuk / kesik arşivler (Türkçe hata), eski biçimler, JSON alt değer tarayıcısı,
// küçük resim (MIMARI §13.1; kabul D1, D3).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <cstring>

#include "cekirdek/proje_dosyasi.h"
#include "cekirdek/proje_json.h"
#include "cekirdek/proje_onizleme.h"
#include "cekirdek/proje_zip.h"
#include "dosya_sahte.h"

using namespace op4;
using namespace op4::sinama;
using nlohmann::json;

namespace {

ProjeIcerigi OrnekIcerik() {
    ProjeIcerigi i;
    i.Koy(proje_yolu::MODEL, "{\"tur\":\"bina\",\"surum\":3,\"baslik\":\"Yapı ŞĞİı\",\"dugumler\":[]}");
    i.Koy(proje_yolu::GORUNUM, "{\"kamera\":{\"hedef\":[1,2,3]}}");
    i.Koy("eklenti/gelecek.bin", std::string("\0\1\2\xff ikili", 10));
    i.Koy(proje_yolu::ONIZLEME, OnizlemePng(*OrnekSahneAnlik(), 64));
    return i;
}

ProjeManifest OrnekManifest() {
    ProjeManifest m;
    m.uygulamaSurumu = "0.1.0";
    m.kaydedildi = "2026-10-31T12:34:56Z";
    m.motorSurumu = "9.9.9";
    m.modelOzeti = "8 düğüm, 8 çubuk, 0 panel";
    return m;
}

uint16_t Le16(const std::string& s, size_t i) {
    return static_cast<uint16_t>(static_cast<unsigned char>(s[i]) | (static_cast<unsigned char>(s[i + 1]) << 8));
}

bool TurkceHata(const std::string& h) {
    return h.find("bozuk") != std::string::npos || h.find("op4 projesi değil") != std::string::npos ||
           h.find("yarım") != std::string::npos || h.find("ZIP") != std::string::npos;
}

}  // namespace

TEST_CASE("D1 .op4 ZIP: mimetype ilk girdi ve sıkıştırmasız, manifest alanları") {
    std::string zip, hata;
    REQUIRE_MESSAGE(ProjeZipKur(OrnekIcerik(), OrnekManifest(), zip, hata), hata);
    // Yerel dosya başlığı: imza, yöntem (8. bayt) = 0 (STORED), ad uzunluğu 8, ad "mimetype", veri hemen ardından.
    REQUIRE(zip.size() > 64);
    CHECK(zip.compare(0, 4, std::string("PK\x03\x04", 4)) == 0);
    CHECK(Le16(zip, 8) == 0);
    CHECK(Le16(zip, 26) == 8);
    CHECK(Le16(zip, 28) == 0);
    CHECK(zip.compare(30, 8, "mimetype") == 0);
    CHECK(zip.compare(38, 17, "application/x-op4") == 0);
    CHECK(BicimSapta(zip.substr(0, 512), ".op4") == DosyaBicimi::Op4);

    const OkumaSonucu o = ProjeZipCoz(zip);
    REQUIRE_MESSAGE(o.basarili, o.hata);
    CHECK(o.uyarilar.empty());
    CHECK(o.manifest.tur == "op4-proje");
    CHECK(o.manifest.bicimSurumu == 1);
    CHECK(o.manifest.uygulamaSurumu == "0.1.0");
    CHECK(o.manifest.kaydedildi == "2026-10-31T12:34:56Z");
    CHECK(o.manifest.motorSurumu == "9.9.9");
    CHECK(o.manifest.modelOzeti == "8 düğüm, 8 çubuk, 0 panel");
    CHECK_FALSE(o.dahaYeniSurum);
    const json m = json::parse(*o.icerik.Al(proje_yolu::MANIFEST));
    CHECK(m["uygulama"]["ad"] == "op4");
    CHECK(m["uygulama"]["firma"] == "Opus Fortis");
    CHECK(m["icerik"].size() == 4);
    for (const auto& [yol, veri] : OrnekIcerik().girdiler) CHECK_MESSAGE(*o.icerik.Al(yol) == veri, yol);
}

TEST_CASE("D1 gidiş-dönüş: aynı içerik + aynı manifest → aynı baytlar; bilinmeyen girdi ve manifest anahtarı korunur") {
    std::string zip, zip2, hata;
    REQUIRE(ProjeZipKur(OrnekIcerik(), OrnekManifest(), zip, hata));
    OkumaSonucu o = ProjeZipCoz(zip);
    REQUIRE(o.basarili);
    REQUIRE(ProjeZipKur(o.icerik, o.manifest, zip2, hata));
    CHECK(zip2 == zip);

    // Daha yeni bir sürümün manifest'e eklediği anahtar ve bilinmeyen girdi, yeniden kaydedince kalır.
    json mj = json::parse(*o.icerik.Al(proje_yolu::MANIFEST));
    mj["gelecek_alan"] = {{"x", 1}};
    o.icerik.Koy(proje_yolu::MANIFEST, mj.dump());
    REQUIRE(ProjeZipKur(o.icerik, o.manifest, zip2, hata));
    const OkumaSonucu o2 = ProjeZipCoz(zip2);
    REQUIRE(o2.basarili);
    CHECK(json::parse(*o2.icerik.Al(proje_yolu::MANIFEST))["gelecek_alan"]["x"] == 1);
    CHECK(*o2.icerik.Al("eklenti/gelecek.bin") == std::string("\0\1\2\xff ikili", 10));
}

TEST_CASE("D1 daha yeni bicim_surumu salt okunur; geçersiz manifest ve mimetype reddedilir") {
    std::string zip, hata;
    ProjeManifest m = OrnekManifest();
    m.bicimSurumu = 7;
    REQUIRE(ProjeZipKur(OrnekIcerik(), m, zip, hata));
    OkumaSonucu o = ProjeZipCoz(zip);
    REQUIRE(o.basarili);
    CHECK(o.dahaYeniSurum);
    REQUIRE_FALSE(o.uyarilar.empty());
    CHECK(o.uyarilar[0].find("salt okunur") != std::string::npos);

    // Başka bir uygulamanın ZIP'i (mimetype yanlış).
    std::string yabanci;
    const std::string mime = "application/zip", veri = "{}";
    REQUIRE(ZipKur({{"mimetype", mime, false}, {"veri.json", veri, true}}, 400000000, yabanci, hata));
    o = ProjeZipCoz(yabanci);
    CHECK_FALSE(o.basarili);
    CHECK(o.hata.find("op4 projesi değil") != std::string::npos);
    // manifest'siz, mimetype'sız ZIP.
    REQUIRE(ZipKur({{"belge.txt", veri, true}}, 400000000, yabanci, hata));
    o = ProjeZipCoz(yabanci);
    CHECK_FALSE(o.basarili);
    CHECK(o.hata.find("op4 projesi değil") != std::string::npos);
    // model/bina.json'u olmayan op4 arşivi.
    const std::string man = R"({"tur":"op4-proje","bicim_surumu":1})";
    REQUIRE(ZipKur({{"mimetype", proje_yolu::MIME_DEGERI, false}, {"manifest.json", man, true}}, 400000000, yabanci, hata));
    o = ProjeZipCoz(yabanci);
    CHECK_FALSE(o.basarili);
    CHECK(o.hata == "Dosya bozuk: model/bina.json yok.");
    // manifest türü yanlış.
    const std::string man2 = R"({"tur":"baska","bicim_surumu":1})", model = R"({"tur":"bina"})";
    REQUIRE(ZipKur({{"mimetype", proje_yolu::MIME_DEGERI, false}, {"manifest.json", man2, true}, {"model/bina.json", model, true}},
                   400000000, yabanci, hata));
    o = ProjeZipCoz(yabanci);
    CHECK_FALSE(o.basarili);
    CHECK(o.hata.find("op4 projesi değil") != std::string::npos);
}

TEST_CASE("D1 bozuk ve kesik arşivler: çökmeden, öğretici Türkçe hata") {
    std::string zip, hata;
    REQUIRE(ProjeZipKur(OrnekIcerik(), OrnekManifest(), zip, hata));
    // Her kesme noktası (ilk 400 bayt tek tek, sonra 37 bayt adımla): ASan / UBSan altında taşma yok, hata Türkçe.
    for (size_t n = 0; n < zip.size(); n += (n < 400 ? 1 : 37)) {
        const OkumaSonucu o = ProjeZipCoz(std::string_view(zip).substr(0, n));
        CHECK_FALSE(o.basarili);
        CHECK_MESSAGE(TurkceHata(o.hata), "n=", n, " hata=", o.hata);
    }
    const OkumaSonucu kesik = ProjeZipCoz(std::string_view(zip).substr(0, zip.size() - 10));
    CHECK(kesik.hata.find("yarım kalmış") != std::string::npos);

    // Sıkıştırılmış model verisinde bit değişikliği → CRC / açma hatası.
    const OkumaSonucu dogru = ProjeZipCoz(zip);
    REQUIRE(dogru.basarili);
    const size_t konum = zip.find("model/bina.json");
    REQUIRE(konum != std::string::npos);
    std::string bozuk = zip;
    bozuk[konum + 15 + 5] = static_cast<char>(bozuk[konum + 15 + 5] ^ 0x5A);
    const OkumaSonucu o = ProjeZipCoz(bozuk);
    CHECK_FALSE(o.basarili);
    CHECK_MESSAGE(o.hata.find("bozuk") != std::string::npos, o.hata);
    CHECK_MESSAGE(o.hata.find("model/bina.json") != std::string::npos, o.hata);

    // Dosyadan: boş dosya, rastgele baytlar, kesik dosya.
    GeciciDizin d;
    DosyaYaz(d.Yol("bos.op4"), "");
    CHECK(ProjeOku(d.Yol("bos.op4")).hata.find("Dosya boş") == 0);
    static const char kRastgele[] = "PK\x03\x04 rastgele baytlar \x01\x02";
    DosyaYaz(d.Yol("rastgele.op4"), std::string(kRastgele, sizeof(kRastgele) - 1));
    const OkumaSonucu r = ProjeOku(d.Yol("rastgele.op4"));
    CHECK_FALSE(r.basarili);
    CHECK(TurkceHata(r.hata));
    DosyaYaz(d.Yol("kesik.op4"), zip.substr(0, zip.size() / 2));
    CHECK(ProjeOku(d.Yol("kesik.op4")).hata.find("yarım kalmış") != std::string::npos);
    CHECK(ProjeOku(d.Yol("yok.op4")).hata.find("Dosya bulunamadı") == 0);
}

TEST_CASE("D2 Türkçe karakterli yol: ProjeYaz / ProjeOku") {
    GeciciDizin d;
    const std::string yol = d.Kur("Proje ŞĞİı") + "/dene.op4";
    std::string hata;
    REQUIRE_MESSAGE(ProjeYaz(yol, OrnekIcerik(), OrnekManifest(), hata), hata);
    const OkumaSonucu o = ProjeOku(yol);
    REQUIRE_MESSAGE(o.basarili, o.hata);
    CHECK(o.bicim == DosyaBicimi::Op4);
    CHECK(*o.icerik.Al(proje_yolu::MODEL) == *OrnekIcerik().Al(proje_yolu::MODEL));
    // Geçici dosya kalmadı.
    size_t n = 0;
    for (const auto& g : std::filesystem::directory_iterator(U8Yol(d.Yol("Proje ŞĞİı")))) {
        (void)g;
        ++n;
    }
    CHECK(n == 1);
}

TEST_CASE("D3 eski biçimler: Faz 0 JSON .op4, .matris, bina .json, IFC, tanınmayan") {
    GeciciDizin d;
    // Faz 0 denemesinin ProjeKaydet çıktısı (op4/kaynak/proje.cpp biçimi).
    DosyaYaz(d.Yol("deneme.op4"),
             "{\n  \"bicim\": \"op4-proje\",\n  \"bicim_surumu\": 1,\n  \"uygulama\": \"op4 0.0.1\",\n"
             "  \"kaydedildi\": \"2026-10-30T10:00:00\",\n"
             "  \"kamera\": {\"hedef\": [1.5, -2.0, 3.25], \"uzaklik\": 42.0, \"sapma\": 0.7, \"egim\": 0.4},\n"
             "  \"gorunum\": {\"kesit\": true, \"kenarlar\": false, \"izgara\": true},\n"
             "  \"model\": {\"surum\": 3, \"dugumler\": [], \"cubuklar\": [], \"paneller\": [], \"mesnetler\": []}\n}\n");
    OkumaSonucu o = ProjeOku(d.Yol("deneme.op4"));
    REQUIRE_MESSAGE(o.basarili, o.hata);
    CHECK(o.bicim == DosyaBicimi::Op4Deneme);
    CHECK_FALSE(o.icerik.Var(proje_yolu::MODEL));  // model boş açılır
    const json g = json::parse(*o.icerik.Al(proje_yolu::GORUNUM));
    CHECK(g["kaynak"] == "op4-deneme");
    CHECK(g["kamera"]["hedef"][2] == 3.25);
    CHECK(g["kamera"]["uzaklik"] == 42.0);
    CHECK(g["kip"] == "kesit");
    CHECK(g["kenarlar"] == false);

    // .matris (web sürümü): bina değeri ham metin olarak çıkar (anahtar sırası, boşluklar korunur).
    const std::string bina = "{\n \"tur\": \"bina\",\n \"surum\": 1,\n \"baslik\": \"Dört katlı ŞĞİı\",\n \"z\": 1e-5\n}";
    DosyaYaz(d.Yol("web.matris"), "\xEF\xBB\xBF{\n \"tur\": \"matris-proje\",\n \"surum\": 1,\n \"uygulama\": \"web\",\n"
                                  " \"bina\": " + bina + ",\n \"gorunum\": {\"x\": 1},\n \"arac_yerlesimi\": null\n}");
    o = ProjeOku(d.Yol("web.matris"));
    REQUIRE_MESSAGE(o.basarili, o.hata);
    CHECK(o.bicim == DosyaBicimi::Matris);
    CHECK(*o.icerik.Al(proje_yolu::MODEL) == bina);
    CHECK(o.uyarilar.size() == 1);
    DosyaYaz(d.Yol("yeni.matris"), R"({"tur":"matris-proje","surum":2,"bina":{"tur":"bina"}})");
    CHECK(ProjeOku(d.Yol("yeni.matris")).hata.find("daha yeni") != std::string::npos);

    // Düz bina JSON'u ve bina_sablon yanıtı sarmalayıcısı.
    DosyaYaz(d.Yol("bina.json"), bina + "\n\n");
    o = ProjeOku(d.Yol("bina.json"));
    REQUIRE(o.basarili);
    CHECK(o.bicim == DosyaBicimi::BinaJson);
    CHECK(*o.icerik.Al(proje_yolu::MODEL) == bina);
    DosyaYaz(d.Yol("sablon.json"), "{\"ad\":\"x\",\"bina\":" + bina + ",\"hata\":null}");
    o = ProjeOku(d.Yol("sablon.json"));
    REQUIRE(o.basarili);
    CHECK(*o.icerik.Al(proje_yolu::MODEL) == bina);
    DosyaYaz(d.Yol("baska.json"), R"({"tur":"cizelge"})");
    CHECK(ProjeOku(d.Yol("baska.json")).hata.find("bina modeli değil") != std::string::npos);
    DosyaYaz(d.Yol("bozuk.json"), R"({"tur":"bina",)");
    CHECK(ProjeOku(d.Yol("bozuk.json")).hata.find("okunamadı") != std::string::npos);

    DosyaYaz(d.Yol("yapi.ifc"), "ISO-10303-21;\nHEADER;\n");
    o = ProjeOku(d.Yol("yapi.ifc"));
    CHECK(o.bicim == DosyaBicimi::Ifc);
    CHECK(o.hata.find("Faz 6") != std::string::npos);
    DosyaYaz(d.Yol("resim.png"), "\x89PNG....");
    CHECK(ProjeOku(d.Yol("resim.png")).hata.find("tanınmadı") != std::string::npos);
}

TEST_CASE("JSON ham alt değer tarayıcısı") {
    const std::string m = "\xEF\xBB\xBF {\"a\" : 1 , \"s\":\"x}\\\"]{\", \"bina\" : {\"t\":[1,{\"u\":\"}\"}]} ,\"son\":null}";
    CHECK(JsonUstDeger(m, "a").value() == "1");
    CHECK(JsonUstDeger(m, "s").value() == "\"x}\\\"]{\"");
    CHECK(JsonUstDeger(m, "bina").value() == "{\"t\":[1,{\"u\":\"}\"}]}");
    CHECK(JsonUstDeger(m, "son").value() == "null");
    CHECK_FALSE(JsonUstDeger(m, "yok"));
    CHECK_FALSE(JsonUstDeger("[1,2]", "a"));
    CHECK_FALSE(JsonUstDeger("{\"a\":{\"b\":1", "a"));  // değer kapanmamış
    CHECK_FALSE(JsonUstDeger("{\"a\":\"x", "a"));        // dizge kapanmamış
    CHECK_FALSE(JsonUstDeger("{\"a\":", "a"));
    CHECK_FALSE(JsonUstDeger("", "a"));
    // Derin ve iç içe "bina" anahtarı üst düzey sayılmaz.
    CHECK(JsonUstDeger("{\"x\":{\"bina\":1},\"bina\":2}", "bina").value() == "2");
}

TEST_CASE("Zaman ve karma yardımcıları") {
    std::time_t t = 0;
    REQUIRE(IsoZamanCoz("2026-10-31T12:34:56Z", t));
    CHECK(IsoZaman(t) == "2026-10-31T12:34:56Z");
    REQUIRE(IsoZamanCoz("1980-01-02T00:00:00", t));
    CHECK(t == 315532800 + 86400);
    CHECK_FALSE(IsoZamanCoz("2026-13-01T00:00:00Z", t));
    CHECK_FALSE(IsoZamanCoz("dün", t));
    CHECK(MetinKarmasi("") == "fnv1a64:cbf29ce484222325");
    CHECK(MetinKarmasi("a") != MetinKarmasi("b"));
}

TEST_CASE("onizleme.png: 256×256 PNG, belirlenimci, boş sahne de çizilir") {
    const std::string a = OnizlemePng(*OrnekSahneAnlik(), 256), b = OnizlemePng(*OrnekSahneAnlik(), 256);
    REQUIRE(a.size() > 100);
    CHECK(a.compare(0, 8, "\x89PNG\r\n\x1a\n") == 0);
    CHECK(a == b);
    // IHDR genişlik / yükseklik (büyük endian).
    auto be32 = [&](size_t i) {
        return (static_cast<uint32_t>(static_cast<unsigned char>(a[i])) << 24) |
               (static_cast<uint32_t>(static_cast<unsigned char>(a[i + 1])) << 16) |
               (static_cast<uint32_t>(static_cast<unsigned char>(a[i + 2])) << 8) | static_cast<unsigned char>(a[i + 3]);
    };
    CHECK(be32(16) == 256);
    CHECK(be32(20) == 256);
    const OnizlemeResmi r = OnizlemeCiz(*OrnekSahneAnlik(), 128);
    CHECK(r.rgba.size() == 128u * 128u * 4u);
    size_t koyu = 0;  // çubuklar çizildi (zeminden belirgin koyu pikseller)
    for (size_t i = 0; i < r.rgba.size(); i += 4)
        if (r.rgba[i] < 150 && r.rgba[i + 1] < 160) ++koyu;
    CHECK(koyu > 200);
    const std::string bos = OnizlemePng(*BosSahne(), 256);
    CHECK(bos.compare(0, 4, "\x89PNG") == 0);
}
