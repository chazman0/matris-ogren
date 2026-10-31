// op4 çekirdek — sonuç özeti (sözleşme S19; tam uygulama). Sahibi: D (dosya-cozum), F1 iş 1.5.
// DcRengi / BoyamaKur / SonucDurumu sözleşmeyle gelmişti; bina_coz yanıt çözümü ve sonuc/ozet.json dönüşümü burada.
#include "cekirdek/sonuc.h"

#include <algorithm>
#include <cmath>

#include <nlohmann/json.hpp>

#include "cekirdek/proje_json.h"

namespace op4 {
namespace {
using nlohmann::json;
using ojson = nlohmann::ordered_json;

std::string Metin(const json& j, const char* ad) {
    return j.is_object() && j.contains(ad) && j[ad].is_string() ? j[ad].get<std::string>() : std::string();
}
double Sayi(const json& j, const char* ad, double v) {
    return j.is_object() && j.contains(ad) && j[ad].is_number() ? j[ad].get<double>() : v;
}
size_t Adet(const json& j, const char* ad) {
    if (!j.is_object() || !j.contains(ad) || !j[ad].is_number()) return 0;
    const double d = j[ad].get<double>();
    return d > 0 ? static_cast<size_t>(d) : 0;
}

void UyarilariEkle(const json& j, std::vector<std::string>& o) {
    if (!j.is_array()) return;
    for (const json& u : j) {
        if (u.is_string()) o.push_back(u.get<std::string>());
        else if (u.is_object() && u.contains("metin") && u["metin"].is_string()) o.push_back(u["metin"].get<std::string>());
    }
}

ojson DcDegeri(double dc) { return std::isfinite(dc) ? ojson(dc) : ojson(nullptr); }

}  // namespace

uint32_t DcRengi(double dc) {
    if (!(dc >= 0) || !std::isfinite(dc)) return 0x8C8C8CFFu;
    if (dc < 0.7) return 0x22C55EFFu;
    if (dc < 0.9) return 0xFACC15FFu;
    if (dc <= 1.0) return 0xFB923CFFu;
    return 0xEF4444FFu;
}

std::shared_ptr<const SonucBoyamasi> BoyamaKur(const SonucOzeti& ozet, uint64_t surum) {
    auto b = std::make_shared<SonucBoyamasi>();
    b->surum = surum;
    b->cozumKimligi = ozet.cozumKimligi;
    b->aciklama = "D/C (en büyük, bütün kombinasyonlar)";
    b->renkler.reserve(ozet.elemanlar.size());
    for (const ElemanSonucu& e : ozet.elemanlar) b->renkler.push_back({e.kimlik, DcRengi(e.dc)});
    return b;
}

void SonucDurumu::Ata(SonucOzeti ozet, std::shared_ptr<const std::string> veri) {
    ozet_ = std::move(ozet);
    veri_ = std::move(veri);
    var_ = true;
    eski_ = false;
    degisti.Yay();
}

void SonucDurumu::EskiIsaretle() {
    if (!var_ || eski_) return;
    eski_ = true;
    degisti.Yay();
}

void SonucDurumu::Temizle() {
    if (!var_ && !eski_) return;
    var_ = eski_ = false;
    ozet_ = SonucOzeti{};
    veri_.reset();
    degisti.Yay();
}

bool CozumYanitiniCoz(std::string_view yanit, SonucOzeti& ozet, std::string& veriMetni, std::string& hata) {
    ozet = SonucOzeti{};
    veriMetni.clear();
    const json j = json::parse(JsonBasiniTemizle(yanit), nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        hata = "Çözüm yanıtı okunamadı (geçerli JSON değil).";
        return false;
    }
    if (j.contains("hata") && !j["hata"].is_null()) {
        hata = Metin(j, "hata_turu") == "iptal" ? std::string("İşlem iptal edildi.")
                                                : (j["hata"].is_string() ? j["hata"].get<std::string>() : j["hata"].dump());
        if (hata.empty()) hata = "Hesap motoru bilinmeyen bir hata döndürdü.";
        return false;
    }
    if (!j.contains("veri") || !j["veri"].is_object()) {
        hata = "Çözüm yanıtında \"veri\" nesnesi yok (bina_coz yanıtı bekleniyordu).";
        return false;
    }
    const json& v = j["veri"];
    const auto ham = JsonUstDeger(yanit, "veri");  // yeniden kodlamadan (1–50 MB)
    veriMetni = ham ? std::string(*ham) : v.dump();

    ozet.cozumKimligi = Metin(v, "cozum_kimligi");
    ozet.ozetMetni = Metin(j, "sonuc_metin");
    const json o = v.contains("ozet") && v["ozet"].is_object() ? v["ozet"] : json::object();
    ozet.sureMs = Sayi(j, "sure_ms", Sayi(o, "cozum_sure_ms", 0));
    ozet.sdSayisi = Adet(o, "sd_sayisi");
    ozet.kombinasyonSayisi = Adet(o, "kombinasyon_sayisi");
    UyarilariEkle(o.contains("uyarilar") ? o["uyarilar"] : json(), ozet.uyarilar);
    const json t = v.contains("tasarim") && v["tasarim"].is_object() ? v["tasarim"] : json::object();
    ozet.enBuyukDc = Sayi(o, "en_buyuk_dc", Sayi(t, "en_buyuk_dc", -1));
    if (!std::isfinite(ozet.enBuyukDc)) ozet.enBuyukDc = -1;
    if (t.contains("elemanlar") && t["elemanlar"].is_array())
        for (const json& e : t["elemanlar"])
            if (Sayi(e, "dc", -1) > 1.0) ++ozet.asanSayisi;
    UyarilariEkle(t.contains("uyarilar") ? t["uyarilar"] : json(), ozet.uyarilar);
    if (ozet.cozumKimligi.empty()) ozet.uyarilar.push_back("Çözüm verisinde cozum_kimligi yok; kayıtlı sonuç açılışta eşleştirilemez.");
    return true;
}

std::string SonucOzetiJson(const SonucOzeti& s) {
    ojson j = ojson::object();
    j["bicim"] = 1;
    j["cozum_kimligi"] = s.cozumKimligi;
    j["tarih"] = s.tarih;
    j["motor_surumu"] = s.motorSurumu;
    j["sahne_surumu"] = s.sahneSurumu;
    j["sure_ms"] = s.sureMs;
    j["ozet"] = {{"metin", s.ozetMetni},
                 {"sd_sayisi", s.sdSayisi},
                 {"kombinasyon_sayisi", s.kombinasyonSayisi},
                 {"en_buyuk_dc", DcDegeri(s.enBuyukDc)},
                 {"en_buyuk_dc_elemani", s.enBuyukDcElemani.Gecerli() ? KimlikMetni(s.enBuyukDcElemani) : std::string()},
                 {"asan_sayisi", s.asanSayisi}};
    j["uyarilar"] = s.uyarilar;
    ojson d = ojson::array();
    for (const ElemanSonucu& e : s.elemanlar)
        d.push_back({{"kimlik", KimlikMetni(e.kimlik)},
                     {"dc", DcDegeri(e.dc)},
                     {"belirleyen", e.belirleyen},
                     {"kombinasyon", e.kombinasyon},
                     {"satir", e.tasarimSatiri}});
    j["dc_dizisi"] = std::move(d);
    return j.dump() + "\n";
}

bool SonucOzetiOku(std::string_view metin, SonucOzeti& s, std::string& hata) {
    s = SonucOzeti{};
    const json j = json::parse(JsonBasiniTemizle(metin), nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        hata = "sonuc/ozet.json okunamadı (geçerli JSON değil).";
        return false;
    }
    if (j.contains("bicim") && j["bicim"].is_number_integer() && j["bicim"].get<int>() > 1) {
        hata = "sonuc/ozet.json daha yeni bir biçimde (" + j["bicim"].dump() + "); kayıtlı sonuçlar yok sayıldı.";
        return false;
    }
    s.cozumKimligi = Metin(j, "cozum_kimligi");
    s.tarih = Metin(j, "tarih");
    s.motorSurumu = Metin(j, "motor_surumu");
    s.sahneSurumu = static_cast<uint64_t>(std::max(0.0, Sayi(j, "sahne_surumu", 0)));
    s.sureMs = Sayi(j, "sure_ms", 0);
    if (j.contains("ozet") && j["ozet"].is_object()) {
        const json& o = j["ozet"];
        s.ozetMetni = Metin(o, "metin");
        s.sdSayisi = Adet(o, "sd_sayisi");
        s.kombinasyonSayisi = Adet(o, "kombinasyon_sayisi");
        s.enBuyukDc = Sayi(o, "en_buyuk_dc", -1);
        if (const auto k = KimlikCoz(Metin(o, "en_buyuk_dc_elemani"))) s.enBuyukDcElemani = *k;
        s.asanSayisi = Adet(o, "asan_sayisi");
    }
    UyarilariEkle(j.contains("uyarilar") ? j["uyarilar"] : json(), s.uyarilar);
    if (j.contains("dc_dizisi") && j["dc_dizisi"].is_array()) {
        for (const json& e : j["dc_dizisi"]) {
            const auto k = KimlikCoz(Metin(e, "kimlik"));
            if (!k) continue;
            ElemanSonucu r;
            r.kimlik = *k;
            r.dc = Sayi(e, "dc", -1);
            r.belirleyen = Metin(e, "belirleyen");
            r.kombinasyon = Metin(e, "kombinasyon");
            r.tasarimSatiri = static_cast<int>(Sayi(e, "satir", -1));
            s.elemanlar.push_back(std::move(r));
        }
        std::sort(s.elemanlar.begin(), s.elemanlar.end(),
                  [](const ElemanSonucu& a, const ElemanSonucu& b) { return a.kimlik < b.kimlik; });
    }
    if (s.cozumKimligi.empty()) {
        hata = "sonuc/ozet.json'da cozum_kimligi yok.";
        return false;
    }
    return true;
}

}  // namespace op4
