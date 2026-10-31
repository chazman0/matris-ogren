// op4 C++ sınamaları (D) — çözüm akışı durum makinesi, sahte MotorHizmeti ile (MIMARI §4, §8.4; kabul D7, D9): F5
// isteği (anlat: false, sd_siniri), geçen süre, iptal → hata_turu "iptal", eski yanıtın atılması, model değişince "eski",
// çözüm sürerken değişiklik, yeni model yüklenince bırakma, hata türleri, D/C boyaması, sonuc/ katkısı ve açılışta
// kayıtlı sonucun eşleştirilmesi (model karması ve bina_kimlik).
#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include "dosya_sahte.h"

using namespace op4;
using namespace op4::sinama;
using nlohmann::json;

namespace {

std::string Fikstur(const std::string& ad) {
    static const std::vector<ZipOkunanGirdi> g = [] {
        std::vector<ZipOkunanGirdi> o;
        std::string hata;
        REQUIRE_MESSAGE(ZipCoz(Op4Dosyasi("testler/cekirdek/cozum_yanitlar.zip"), o, hata), hata);
        return o;
    }();
    for (const ZipOkunanGirdi& x : g)
        if (x.ad == ad) return x.veri;
    FAIL("fikstür yok: " << ad);
    return {};
}

// Ortam: celik-cbf-3kat modeli yüklü (sahte çekirdek bina metnini olduğu gibi tutar).
void ModelYukle(DOrtam& o, const std::string& ad = "celik-cbf-3kat") {
    REQUIRE(o.Komut("dosya.yeni_sablon", ad));
    REQUIRE_FALSE(o.cekirdek.Ozet().bos);
}

void Degistir(DOrtam& o, const std::string& baslik) {
    REQUIRE(ModelIslemiUygula(o.h, islem::BASLIK_DEGISTIR, json{{"baslik", baslik}}.dump()).ModelDegisti());
}

IstekNo CozVeYanitla(DOrtam& o, const std::string& fikstur = "celik-cbf-3kat.yanit.json") {
    REQUIRE(o.Komut("analiz.coz"));
    SahteMotor::Istek* i = o.motor.Son("bina_coz");
    REQUIRE(i);
    const IstekNo no = i->no;
    o.motor.Yanitla(no, Fikstur(fikstur), 1234);
    o.motor.Pompala();
    return no;
}

}  // namespace

TEST_CASE("D7 F5: bina_coz isteği eşzamansız, anlat:false, sd_siniri; geçen süre; yanıtla sonuç, boyama, özet") {
    DOrtam o;
    // Boş modelde çözülmez (öğretici neden).
    const KomutDurumu bos = o.komutlar.Durum("analiz.coz", o.h);
    CHECK(bos.bagli);
    CHECK_FALSE(bos.kullanilabilir);
    CHECK(bos.neden.find("Model boş") == 0);
    ModelYukle(o);
    CHECK(o.komutlar.Durum("analiz.coz", o.h).kullanilabilir);
    CHECK_FALSE(o.komutlar.Durum("analiz.iptal", o.h).kullanilabilir);
    CHECK(o.komutlar.KisayolBul("F5")->id == "analiz.coz");

    o.cozum->KareIsi(1000);
    REQUIRE(o.Komut("analiz.coz"));
    CHECK(o.cozum->Evre() == CozumEvresi::Cozuluyor);
    SahteMotor::Istek* i = o.motor.Son("bina_coz");
    REQUIRE(i);
    const json girdi = json::parse(i->girdi);
    CHECK(girdi["anlat"] == false);
    CHECK(girdi["bina"] == json::parse(o.cekirdek.Metin()));
    CHECK(json::parse(i->ayarlar)["sd_siniri"] == 6000);
    CHECK(o.sonuc.surenIstek == i->no);
    CHECK(o.komutlar.Durum("analiz.iptal", o.h).kullanilabilir);
    const KomutDurumu suruyor = o.komutlar.Durum("analiz.coz", o.h);
    CHECK_FALSE(suruyor.kullanilabilir);
    CHECK(suruyor.neden.find("Çözüm sürüyor") == 0);
    CHECK_FALSE(o.cozum->Coz());  // ikinci F5 yeni istek açmaz
    CHECK(o.motor.istekler.size() == 1);

    o.cozum->KareIsi(4400);  // 3,4 s
    CHECK(o.cozum->GecenMs() == 3400);
    CHECK(o.cozum->DurumMetni() == "Çözülüyor… 3,4 s");
    CHECK(o.SatirdaVar("[ilerleme cozum] Çözülüyor… 3,4 s"));

    o.motor.Yanitla(i->no, Fikstur("celik-cbf-3kat.yanit.json"), 1234);
    CHECK(o.motor.Pompala() == 1);
    CHECK(o.cozum->Evre() == CozumEvresi::Bos);
    CHECK(o.sonuc.surenIstek == 0);
    CHECK(o.SatirdaVar("[ilerleme cozum] bitti"));
    REQUIRE(o.sonuc.Var());
    CHECK_FALSE(o.sonuc.Eski());
    const json v = json::parse(Fikstur("celik-cbf-3kat.yanit.json"))["veri"];
    const SonucOzeti& oz = o.sonuc.Ozet();
    CHECK(oz.cozumKimligi == v["cozum_kimligi"].get<std::string>());
    CHECK(oz.sdSayisi == v["ozet"]["sd_sayisi"].get<size_t>());
    CHECK(oz.enBuyukDc == v["ozet"]["en_buyuk_dc"].get<double>());
    CHECK(oz.tarih == "2026-10-31T12:00:00Z");
    CHECK(oz.motorSurumu == "9.9.9");
    CHECK(oz.elemanlar.size() == v["tasarim"]["elemanlar"].size());  // yedek eşleme (sahte çekirdekte SonucEsle yok)
    CHECK(o.SatirdaVar("genel model çubukları tasarım tablosundan doğrudan eşlendi"));
    REQUIRE(o.sonuc.Veri());
    CHECK(json::parse(*o.sonuc.Veri()) == v);
    // D/C boyaması görünüme yazıldı, renk kipi Sonuc.
    REQUIRE(o.gorunum.sonuc);
    CHECK_FALSE(o.gorunum.sonuc->eski);
    CHECK(o.gorunum.renkKipi == RenkKipi::Sonuc);
    CHECK(o.gorunum.sonuc->renkler.size() == oz.elemanlar.size());
    CHECK(o.gorunum.sonuc->cozumKimligi == oz.cozumKimligi);
    CHECK(o.komutlar.Durum("analiz.dc_renkleri", o.h).isaretli);
    REQUIRE(o.Komut("analiz.dc_renkleri"));
    CHECK(o.gorunum.renkKipi == RenkKipi::Tur);
    REQUIRE(o.Komut("analiz.dc_renkleri"));
    CHECK(o.gorunum.renkKipi == RenkKipi::Sonuc);
    // Özet satırları: SD, ΣG, ΣQ, en büyük D/C.
    const auto satirlar = o.cozum->OzetSatirlari();
    auto deger = [&](const std::string& e) {
        for (const OzetSatiri& s : satirlar)
            if (s.etiket == e) return s.deger;
        return std::string("<yok>");
    };
    CHECK(deger("Durum") == "Güncel");
    CHECK(deger("Serbestlik derecesi") == SayiMetni(static_cast<double>(oz.sdSayisi), 0));
    CHECK(deger("ΣG") == SayiMetni(v["ozet"]["toplam_G"].get<double>(), 2) + " kN");
    CHECK(deger("ΣQ") == SayiMetni(v["ozet"]["toplam_Q"].get<double>(), 2) + " kN");
    CHECK(deger("En büyük D/C").find(OndalikVirgul(oz.enBuyukDc, 3)) == 0);
    CHECK(deger("En büyük D/C").find("cubuk:") != std::string::npos);
    CHECK(o.cozum->DurumMetni() == "D/C en büyük " + OndalikVirgul(oz.enBuyukDc, 3));
    REQUIRE(o.Komut("analiz.sonuc_ozeti"));
    CHECK(o.SatirdaVar("Serbestlik derecesi: "));
}

TEST_CASE("D8 ölçüm satırı: OP4OLCUM senaryo=cozum") {
    std::vector<std::string> olcumler;
    DOrtamAyari a;
    a.olcum = [&](std::string_view s) { olcumler.emplace_back(s); };
    DOrtam o(a);
    ModelYukle(o);
    REQUIRE(o.cozum->Coz());
    o.motor.Yanitla(o.motor.Son("bina_coz")->no, Fikstur("celik-cbf-3kat.yanit.json"), 1234);
    o.motor.Pompala();
    REQUIRE(olcumler.size() == 1);
    CHECK(olcumler[0].rfind("OP4OLCUM senaryo=cozum motor_ms=", 0) == 0);
    CHECK(olcumler[0].find(" sd=" + std::to_string(o.sonuc.Ozet().sdSayisi)) != std::string::npos);
}

TEST_CASE("D7 iptal: hata_turu 'iptal', sonuç değişmez; geç gelen eski yanıt atılır") {
    DOrtam o;
    ModelYukle(o);
    CozVeYanitla(o);
    REQUIRE(o.sonuc.Var());
    const std::string kimlik = o.sonuc.Ozet().cozumKimligi;

    REQUIRE(o.Komut("analiz.coz"));
    SahteMotor::Istek* i = o.motor.Son("bina_coz");
    const IstekNo no = i->no;
    REQUIRE(o.Komut("analiz.iptal"));
    CHECK(o.cozum->Evre() == CozumEvresi::IptalEdiliyor);
    CHECK(o.cozum->DurumMetni() == "İptal ediliyor…");
    CHECK_FALSE(o.komutlar.Durum("analiz.iptal", o.h).kullanilabilir);
    CHECK_FALSE(o.cozum->Iptal());
    o.motor.Pompala();
    CHECK(o.cozum->Evre() == CozumEvresi::Bos);
    CHECK(o.cozum->SonHata() == "Çözüm iptal edildi.");
    CHECK(o.SatirdaVar("[tost bilgi] Çözüm iptal edildi."));
    CHECK(o.sonuc.Var());  // önceki sonuç korunur
    CHECK(o.sonuc.Ozet().cozumKimligi == kimlik);
    // Yarış: iptal edilmiş isteğin yanıtı sonradan gelirse atılır.
    o.motor.istekler.back().bitti = false;
    o.motor.Yanitla(no, Fikstur("celik-1kat-depo.yanit.json"));
    o.motor.Pompala();
    CHECK(o.sonuc.Ozet().cozumKimligi == kimlik);
}

TEST_CASE("D7 eski işareti: model değişince 'Sonuçlar eski', boyama soluk; çözüm sürerken değişiklik") {
    DOrtam o;
    ModelYukle(o);
    CozVeYanitla(o);
    REQUIRE(o.sonuc.Var());
    const uint64_t boyama = o.gorunum.sonuc->surum;
    Degistir(o, "Değişti");
    CHECK(o.sonuc.Eski());
    REQUIRE(o.gorunum.sonuc);
    CHECK(o.gorunum.sonuc->eski);
    CHECK(o.gorunum.sonuc->surum > boyama);
    CHECK(o.cozum->DurumMetni() == "Sonuçlar eski");
    CHECK(o.cozum->OzetSatirlari()[0].deger.find("Sonuçlar eski") == 0);
    // Yeniden çöz → güncel.
    CozVeYanitla(o);
    CHECK_FALSE(o.sonuc.Eski());
    CHECK_FALSE(o.gorunum.sonuc->eski);

    // Çözüm sürerken model değişirse gelen sonuç hemen eski.
    REQUIRE(o.Komut("analiz.coz"));
    const IstekNo no = o.motor.Son("bina_coz")->no;
    Degistir(o, "Çözüm sırasında");
    o.motor.Yanitla(no, Fikstur("celik-cbf-3kat.yanit.json"));
    o.motor.Pompala();
    REQUIRE(o.sonuc.Var());
    CHECK(o.sonuc.Eski());
    CHECK(o.gorunum.sonuc->eski);
}

TEST_CASE("D7 yeni model yüklenince süren çözüm bırakılır; yanıt atılır, sonuç temizlenir") {
    DOrtam o;
    ModelYukle(o);
    REQUIRE(o.Komut("analiz.coz"));
    const IstekNo no = o.motor.Son("bina_coz")->no;
    REQUIRE(o.Komut("dosya.yeni"));
    CHECK(o.cozum->Evre() == CozumEvresi::Bos);
    CHECK(o.SatirdaVar("Süren çözüm bırakıldı"));
    o.motor.Pompala();  // iptal yanıtı (Unut motoru iptal etti) — işleyici eşlemez
    o.motor.istekler.back().bitti = false;
    o.motor.Yanitla(no, Fikstur("celik-cbf-3kat.yanit.json"));
    o.motor.Pompala();
    CHECK_FALSE(o.sonuc.Var());
    CHECK_FALSE(o.gorunum.sonuc);
    CHECK(o.gorunum.renkKipi == RenkKipi::Tur);
}

TEST_CASE("D7 hata türleri: girdi hatası, motor hatası, motor başlatılamadı") {
    DOrtam o;
    ModelYukle(o);
    REQUIRE(o.Komut("analiz.coz"));
    IstekNo no = o.motor.Son("bina_coz")->no;
    o.motor.HataVer(no, YanitDurumu::Hata, "Malzeme yok: en az bir malzeme tanımlayın.", "girdi");
    o.motor.Pompala();
    CHECK(o.cozum->Evre() == CozumEvresi::Bos);
    CHECK(o.SatirdaVar("HATA: Çözüm: Malzeme yok"));
    CHECK_FALSE(o.sonuc.Var());
    REQUIRE(o.Komut("analiz.coz"));
    no = o.motor.Son("bina_coz")->no;
    o.motor.HataVer(no, YanitDurumu::MotorHatasi, "Hesap motoru çöktü; yeniden başlatıldı.", "motor_coktu");
    o.motor.Pompala();
    CHECK(o.SatirdaVar("HATA: Hesap motoru: Hesap motoru çöktü"));
    // Tamam durumlu ama hata içeren yanıt (köprü sözleşmesi dışı) da hata sayılır.
    REQUIRE(o.Komut("analiz.coz"));
    no = o.motor.Son("bina_coz")->no;
    o.motor.Yanitla(no, Fikstur("hata.yanit.json"));
    o.motor.Pompala();
    CHECK(o.cozum->SonHata().find("Malzeme yok") == 0);
    o.motor.durum.basarili = false;
    o.motor.durum.hata = "python314.dll bulunamadı";
    const KomutDurumu d = o.komutlar.Durum("analiz.coz", o.h);
    CHECK_FALSE(d.kullanilabilir);
    CHECK(d.neden.find("Hesap motoru başlatılamadı: python314.dll") == 0);
}

TEST_CASE("D9 .op4 sonuc/: kaydet → aç, model aynıysa D/C hemen güncel; değiştiyse eski + bina_kimlik denetimi") {
    DOrtam o;
    ModelYukle(o);
    CozVeYanitla(o);
    const SonucOzeti once = o.sonuc.Ozet();
    const std::string yol = o.dizin.Yol("sonuçlu ŞĞİı.op4");
    REQUIRE(o.Komut("dosya.farkli_kaydet", yol));
    const OkumaSonucu r = ProjeOku(yol);
    REQUIRE(r.basarili);
    const json oz = json::parse(*r.icerik.Al(proje_yolu::SONUC_OZETI));
    CHECK(oz["cozum_kimligi"] == once.cozumKimligi);
    CHECK(oz["model_karmasi"] == MetinKarmasi(o.cekirdek.Metin()));
    CHECK(oz["eski"] == false);
    CHECK(oz["dc_dizisi"].size() == once.elemanlar.size());
    CHECK(*r.icerik.Al(proje_yolu::SONUC_VERISI) == *o.sonuc.Veri());

    // Aç: aynı model → hemen güncel, boyama var (motor isteği yok).
    REQUIRE(o.Komut("dosya.yeni"));
    CHECK_FALSE(o.sonuc.Var());
    const size_t istek = o.motor.istekler.size();
    REQUIRE(o.Komut("dosya.ac", yol));
    REQUIRE(o.sonuc.Var());
    CHECK_FALSE(o.sonuc.Eski());
    CHECK(o.sonuc.Ozet().cozumKimligi == once.cozumKimligi);
    CHECK(o.sonuc.Ozet().elemanlar.size() == once.elemanlar.size());
    CHECK(o.sonuc.Ozet().enBuyukDcElemani == once.enBuyukDcElemani);
    REQUIRE(o.gorunum.sonuc);
    CHECK(o.gorunum.renkKipi == RenkKipi::Sonuc);
    CHECK_FALSE(o.gorunum.sonuc->eski);
    CHECK(o.motor.istekler.size() == istek);
    CHECK(o.SatirdaVar("Kayıtlı sonuçlar modelle eşleşti; D/C renkleri güncel."));

    // Model metni farklı (ör. çekirdek kanonik biçimi değişti) ama motor aynı kimliği verirse → güncel.
    OkumaSonucu r2 = ProjeOku(yol);
    json m = json::parse(*r2.icerik.Al(proje_yolu::MODEL));
    r2.icerik.Koy(proje_yolu::MODEL, m.dump(2));  // aynı model, başka yazım
    std::string hata;
    const std::string yol2 = o.dizin.Yol("yazim.op4");
    REQUIRE(ProjeYaz(yol2, r2.icerik, r2.manifest, hata));
    REQUIRE(o.Komut("dosya.ac", yol2));
    CHECK(o.sonuc.Eski());
    CHECK(o.cozum->KimlikDenetimiSuruyor());
    SahteMotor::Istek* k = o.motor.Son("bina_kimlik");
    REQUIRE(k);
    CHECK(json::parse(k->girdi)["bina"] == m);
    o.motor.Yanitla(k->no, json{{"cozum_kimligi", once.cozumKimligi}, {"hata", nullptr}}.dump());
    o.motor.Pompala();
    CHECK_FALSE(o.sonuc.Eski());
    CHECK_FALSE(o.gorunum.sonuc->eski);
    CHECK(o.SatirdaVar("(bina_kimlik)"));

    // Başka kimlik → eski kalır.
    REQUIRE(o.Komut("dosya.ac", yol2));
    k = o.motor.Son("bina_kimlik");
    o.motor.Yanitla(k->no, R"({"cozum_kimligi":"bina-baska","hata":null})");
    o.motor.Pompala();
    CHECK(o.sonuc.Eski());
    CHECK(o.SatirdaVar("bu modele ait değil"));

    // bina_kimlik henüz motorda yoksa (hata) → eski kalır, öğretici satır.
    REQUIRE(o.Komut("dosya.ac", yol2));
    k = o.motor.Son("bina_kimlik");
    o.motor.HataVer(k->no, YanitDurumu::Hata, "Bilinmeyen işlem: 'bina_kimlik'", "girdi");
    o.motor.Pompala();
    CHECK(o.sonuc.Eski());
    CHECK(o.SatirdaVar("doğrulanamadı"));

    // Denetim sürerken kullanıcı modeli değiştirirse eşleşme kabul edilmez.
    REQUIRE(o.Komut("dosya.ac", yol2));
    k = o.motor.Son("bina_kimlik");
    Degistir(o, "Kullanıcı değiştirdi");
    o.motor.Yanitla(k->no, json{{"cozum_kimligi", once.cozumKimligi}, {"hata", nullptr}}.dump());
    o.motor.Pompala();
    CHECK(o.sonuc.Eski());

    // Eskiyken kaydedilen sonuç "eski" olarak geri gelir, denetim istenmez.
    REQUIRE(o.Komut("dosya.kaydet"));
    const size_t n = o.motor.istekler.size();
    REQUIRE(o.Komut("dosya.ac", yol2));
    CHECK(o.sonuc.Eski());
    CHECK(o.motor.istekler.size() == n);
}

TEST_CASE("D10 IFC dışa aktarma güncel sonuçta D/C ile, eskide D/C'siz") {
    DOrtam o;
    ModelYukle(o);
    CozVeYanitla(o);
    REQUIRE(o.Komut("dosya.ifc_disa", o.dizin.Yol("dc.ifc")));
    CHECK(json::parse(o.cekirdek.sonIfcSecenek)["dc"] == true);
    CHECK(o.cekirdek.sonIfcVeri == *o.sonuc.Veri());
    Degistir(o, "x");
    REQUIRE(o.Komut("dosya.ifc_disa", o.dizin.Yol("dcsiz.ifc")));
    CHECK(json::parse(o.cekirdek.sonIfcSecenek)["dc"] == false);
    CHECK(o.cekirdek.sonIfcVeri.empty());
}
