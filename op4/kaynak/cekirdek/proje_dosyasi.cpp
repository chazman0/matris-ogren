// op4 çekirdek — proje dosyası (sözleşme S16; tam uygulama). Sahibi: D (dosya-cozum), F1 iş 1.6.
//
// .op4 = ZIP (miniz): "mimetype" ilk girdi ve sıkıştırmasız, ardından manifest.json, model/bina.json ve diğer katkı
// girdileri yol sırasıyla (TASARIM §21). Bilinmeyen girdiler okunur ve yeniden yazılırken korunur; manifest.json'daki
// bilinmeyen anahtarlar da korunur. Eski biçimler: Faz 0 denemesinin JSON .op4'ü (kamera alınır, model boş), web
// sürümünün .matris projesi ve düz bina .json'u (model metni yeniden yazılmadan çekirdeğe gider).
#include "cekirdek/proje_dosyasi.h"

#include <algorithm>
#include <filesystem>
#include <nlohmann/json.hpp>

#include "cekirdek/proje_json.h"
#include "cekirdek/proje_zip.h"
#include "cekirdek/turkce.h"
#include "platform/dosya_sistemi.h"
#include "platform/dosya_sistemi_atomik.h"

namespace op4 {
namespace {
using nlohmann::json;
using ojson = nlohmann::ordered_json;
namespace fs = std::filesystem;

std::string Kucuk(std::string_view s) {
    std::string o(s);
    for (char& c : o)
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    return o;
}

std::string_view BaslangicBosluksuz(std::string_view s) { return JsonBasiniTemizle(s); }

std::string Uzanti(const std::string& yol) {
    const size_t b = yol.find_last_of("\\/");
    const size_t n = yol.find_last_of('.');
    if (n == std::string::npos || (b != std::string::npos && n < b)) return {};
    return yol.substr(n);
}

fs::path Yol(const std::string& utf8) {
    return fs::path(std::u8string(reinterpret_cast<const char8_t*>(utf8.data()), utf8.size()));
}

std::string Utf8(const fs::path& p) {
    const std::u8string s = p.u8string();
    return std::string(reinterpret_cast<const char*>(s.data()), s.size());
}

bool BilinenYol(const std::string& y) {
    return y == proje_yolu::MIMETYPE || y == proje_yolu::MANIFEST;
}

// ---- manifest -------------------------------------------------------------------------------------------------------
std::string ManifestMetni(const ProjeManifest& m, const ProjeIcerigi& icerik, const std::string* eski) {
    ojson j = ojson::object();
    j["tur"] = m.tur.empty() ? std::string("op4-proje") : m.tur;
    j["bicim_surumu"] = m.bicimSurumu;
    j["uygulama"] = {{"ad", "op4"}, {"surum", m.uygulamaSurumu}, {"firma", "Opus Fortis"}};
    j["kaydedildi"] = m.kaydedildi;
    j["model_ozeti"] = m.modelOzeti;
    j["motor_surumu"] = m.motorSurumu;
    ojson liste = ojson::array();
    for (const auto& [yol, veri] : icerik.girdiler)
        if (!BilinenYol(yol)) liste.push_back({{"yol", yol}, {"bayt", veri.size()}});
    j["icerik"] = std::move(liste);
    if (eski) {  // bilinmeyen anahtarlar (daha yeni sürüm) korunur
        const ojson e = ojson::parse(*eski, nullptr, false);
        if (e.is_object())
            for (auto i = e.begin(); i != e.end(); ++i)
                if (!j.contains(i.key())) j[i.key()] = i.value();
    }
    return j.dump(1) + "\n";
}

std::string MetinAl(const json& j, const char* ad) {
    return j.is_object() && j.contains(ad) && j[ad].is_string() ? j[ad].get<std::string>() : std::string();
}

bool ManifestOku(const std::string& metin, ProjeManifest& m, OkumaSonucu& s) {
    const json j = json::parse(metin, nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        s.hata = "Dosya bozuk: manifest.json okunamadı (geçerli JSON değil).";
        return false;
    }
    m.tur = MetinAl(j, "tur");
    if (m.tur != "op4-proje") {
        s.hata = "Bu dosya bir op4 projesi değil (manifest.json \"tur\": \"" + m.tur + "\").";
        return false;
    }
    if (!j.contains("bicim_surumu") || !j["bicim_surumu"].is_number_integer() || j["bicim_surumu"].get<int>() < 1) {
        s.hata = "Dosya bozuk: manifest.json'da geçerli bir \"bicim_surumu\" yok.";
        return false;
    }
    m.bicimSurumu = j["bicim_surumu"].get<int>();
    if (j.contains("uygulama")) m.uygulamaSurumu = MetinAl(j["uygulama"], "surum");
    m.kaydedildi = MetinAl(j, "kaydedildi");
    m.motorSurumu = MetinAl(j, "motor_surumu");
    m.modelOzeti = MetinAl(j, "model_ozeti");
    return true;
}

// bicim_surumu yükseltme zinciri (MIMARI §13.1.2). Her adım n → n+1; bugün tek biçim var (1).
void BicimYukselt(ProjeIcerigi&, ProjeManifest& m, std::vector<std::string>&) {
    while (m.bicimSurumu < proje_yolu::BICIM_SURUMU) {
        // (n → n+1 dönüştürücüleri buraya; biçim 2 geldiğinde 1 → 2.)
        ++m.bicimSurumu;
    }
}

// ---- eski biçimler --------------------------------------------------------------------------------------------------
bool BinaNesnesiMi(const json& j) { return j.is_object() && j.contains("tur") && j["tur"] == "bina"; }

// Düz bina JSON'u ya da {"bina": {...}} sarmalayıcısı (bina_sablon yanıtı); model metni ham kalır.
bool BinaMetniCikar(std::string_view metin, std::string& model, std::string& hata) {
    const std::string_view s = JsonBasiniTemizle(metin);
    const json j = json::parse(s, nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        hata = "JSON olarak okunamadı (dosya bozuk ya da yarım).";
        return false;
    }
    if (BinaNesnesiMi(j)) {
        std::string_view g = s;
        while (!g.empty() && (g.back() == '\n' || g.back() == '\r' || g.back() == ' ' || g.back() == '\t')) g.remove_suffix(1);
        model.assign(g);
        return true;
    }
    if (j.contains("bina") && BinaNesnesiMi(j["bina"])) {
        const auto ham = JsonUstDeger(s, "bina");
        model = ham ? std::string(*ham) : j["bina"].dump();
        return true;
    }
    hata = "Bu JSON bir bina modeli değil (\"tur\": \"bina\" alanı yok). op4; .op4 projelerini, web sürümünün .matris "
           "projelerini ve bina JSON'unu açar.";
    return false;
}

void MatrisOku(std::string_view metin, OkumaSonucu& s) {
    const std::string_view m = JsonBasiniTemizle(metin);
    const json j = json::parse(m, nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        s.hata = ".matris projesi JSON olarak okunamadı (dosya bozuk ya da yarım).";
        return;
    }
    if (j.value("tur", std::string()) == "matris-proje") {
        const int surum = j.contains("surum") && j["surum"].is_number_integer() ? j["surum"].get<int>() : 1;
        if (surum > 1) {
            s.hata = "Bu proje web sürümünün daha yeni bir biçimiyle kaydedilmiş (surum " + std::to_string(surum) +
                     "); op4 .matris surum 1'i okur.";
            return;
        }
        if (!j.contains("bina") || !BinaNesnesiMi(j["bina"])) {
            s.hata = ".matris projesinde bina modeli yok (\"bina\" alanı).";
            return;
        }
        const auto ham = JsonUstDeger(m, "bina");
        s.icerik.Koy(proje_yolu::MODEL, ham ? std::string(*ham) : j["bina"].dump());
        if (j.contains("gorunum") && !j["gorunum"].is_null())
            s.uyarilar.push_back("Web sürümünün görünüm ve araç kutusu ayarları alınmadı; op4 kendi görünümünü kullanır.");
        s.basarili = true;
        return;
    }
    std::string model, hata;  // web sürümü düz bina JSON'unu da .matris diye açar
    if (!BinaMetniCikar(m, model, hata)) {
        s.hata = hata;
        return;
    }
    s.icerik.Koy(proje_yolu::MODEL, std::move(model));
    s.basarili = true;
}

double Sayi(const json& j, const char* ad, double v) { return j.is_object() && j.contains(ad) && j[ad].is_number() ? j[ad].get<double>() : v; }

void DenemeOku(std::string_view metin, OkumaSonucu& s) {
    const json j = json::parse(JsonBasiniTemizle(metin), nullptr, false);
    if (j.is_discarded() || !j.is_object() || j.value("bicim", std::string()) != "op4-proje") {
        s.hata = "Dosya .op4 uzantılı ama ne ZIP ne de Faz 0 denemesinin JSON biçimi (\"bicim\": \"op4-proje\").";
        return;
    }
    ojson g = ojson::object();
    g["bicim"] = 1;
    g["kaynak"] = "op4-deneme";
    if (j.contains("kamera") && j["kamera"].is_object()) {
        const json& k = j["kamera"];
        ojson hedef = ojson::array({0.0, 0.0, 0.0});
        if (k.contains("hedef") && k["hedef"].is_array() && k["hedef"].size() == 3)
            for (size_t i = 0; i < 3; ++i) hedef[i] = k["hedef"][i].is_number() ? k["hedef"][i].get<double>() : 0.0;
        g["kamera"] = {{"hedef", hedef}, {"uzaklik", Sayi(k, "uzaklik", 30)}, {"sapma", Sayi(k, "sapma", 0)},
                       {"egim", Sayi(k, "egim", 0)}};
    }
    if (j.contains("gorunum") && j["gorunum"].is_object()) {
        const json& v = j["gorunum"];
        g["kip"] = v.value("kesit", false) ? "kesit" : "cubuk";
        g["kenarlar"] = v.value("kenarlar", true);
        g["izgara"] = v.value("izgara", true);
    }
    s.icerik.Koy(proje_yolu::GORUNUM, g.dump(1) + "\n");
    s.uyarilar.push_back("Faz 0 denemesinin JSON biçimli .op4 dosyası: kamera ve görünüm alındı, model boş açıldı (deneme "
                         "biçimi model saklamıyordu). Kaydederken yeni .op4 biçimi yazılır.");
    s.basarili = true;
}

}  // namespace

DosyaBicimi BicimSapta(std::string_view ilk, std::string_view uzanti) {
    if (ilk.size() >= 4 && ilk.substr(0, 4) == std::string_view("PK\x03\x04", 4)) return DosyaBicimi::Op4;
    const std::string_view s = BaslangicBosluksuz(ilk);
    if (s.substr(0, 13) == "ISO-10303-21;") return DosyaBicimi::Ifc;
    const std::string u = Kucuk(uzanti);
    if (!s.empty() && s.front() == '{') {
        if (u == ".op4" || u == "op4") return DosyaBicimi::Op4Deneme;
        if (u == ".matris" || u == "matris") return DosyaBicimi::Matris;
        return DosyaBicimi::BinaJson;
    }
    if (u == ".ifc" || u == "ifc") return DosyaBicimi::Ifc;
    return DosyaBicimi::Bilinmiyor;
}

bool ProjeZipKur(const ProjeIcerigi& icerik, const ProjeManifest& manifest, std::string& zip, std::string& hata) {
    if (!icerik.Var(proje_yolu::MODEL)) {
        hata = "Kaydedilecek model yok (model/bina.json katkısı boş).";
        return false;
    }
    const std::string manifestMetni = ManifestMetni(manifest, icerik, icerik.Al(proje_yolu::MANIFEST));
    std::vector<ZipYazGirdisi> g;
    g.reserve(icerik.girdiler.size() + 2);
    g.push_back({proje_yolu::MIMETYPE, proje_yolu::MIME_DEGERI, false});
    g.push_back({proje_yolu::MANIFEST, manifestMetni, true});
    g.push_back({proje_yolu::MODEL, *icerik.Al(proje_yolu::MODEL), true});
    for (const auto& [yol, veri] : icerik.girdiler) {
        if (BilinenYol(yol) || yol == proje_yolu::MODEL) continue;
        const bool png = yol.size() > 4 && Kucuk(yol.substr(yol.size() - 4)) == ".png";
        g.push_back({yol, veri, !png});
    }
    std::time_t t = 0;
    if (!IsoZamanCoz(manifest.kaydedildi, t) || t < 315532800 + 86400) t = 315532800 + 86400;  // DOS zamanı 1980'den
    return ZipKur(g, t, zip, hata);
}

OkumaSonucu ProjeZipCoz(std::string_view zip) {
    OkumaSonucu s;
    s.bicim = DosyaBicimi::Op4;
    std::vector<ZipOkunanGirdi> girdiler;
    if (!ZipCoz(zip, girdiler, s.hata)) return s;
    if (girdiler.empty()) {
        s.hata = "Dosya bozuk: ZIP arşivi boş.";
        return s;
    }
    const std::string* mime = nullptr;
    for (const ZipOkunanGirdi& g : girdiler) {
        if (g.ad == proje_yolu::MIMETYPE) {
            mime = &g.veri;
            continue;
        }
        if (s.icerik.Var(g.ad)) s.uyarilar.push_back("Arşivde aynı adlı iki girdi var: " + g.ad + " (sonuncusu alındı).");
        s.icerik.Koy(g.ad, g.veri);
    }
    if (mime && *mime != proje_yolu::MIME_DEGERI) {
        s.hata = "Bu ZIP bir op4 projesi değil (mimetype: \"" + mime->substr(0, 64) + "\").";
        return s;
    }
    const std::string* manifest = s.icerik.Al(proje_yolu::MANIFEST);
    if (!manifest) {
        s.hata = mime ? "Dosya bozuk: manifest.json yok." : "Bu ZIP bir op4 projesi değil (mimetype ve manifest.json yok).";
        return s;
    }
    if (!mime) s.uyarilar.push_back("Arşivde \"mimetype\" girdisi yok; dosya op4 dışında bir araçla değiştirilmiş olabilir.");
    else if (girdiler.front().ad != proje_yolu::MIMETYPE)
        s.uyarilar.push_back("\"mimetype\" ilk girdi değil; dosya op4 dışında bir araçla yeniden paketlenmiş olabilir.");
    if (!ManifestOku(*manifest, s.manifest, s)) return s;
    if (s.manifest.bicimSurumu > proje_yolu::BICIM_SURUMU) {
        s.dahaYeniSurum = true;
        s.uyarilar.push_back("Bu proje op4'ün daha yeni bir sürümüyle kaydedilmiş (biçim " +
                             std::to_string(s.manifest.bicimSurumu) + ", op4 " + s.manifest.uygulamaSurumu +
                             "); salt okunur açıldı. Değişiklikleri Farklı kaydet ile yeni bir dosyaya yazın.");
    } else {
        BicimYukselt(s.icerik, s.manifest, s.uyarilar);
    }
    if (!s.icerik.Var(proje_yolu::MODEL)) {
        s.hata = "Dosya bozuk: model/bina.json yok.";
        return s;
    }
    s.basarili = true;
    return s;
}

OkumaSonucu ProjeOku(const std::string& yol) {
    OkumaSonucu s;
    std::string veri, hata;
    if (!DosyaVar(yol)) {
        s.hata = "Dosya bulunamadı: " + yol;
        return s;
    }
    if (!DosyaOku(yol, veri, hata)) {
        s.hata = hata;
        return s;
    }
    if (veri.empty()) {
        s.hata = "Dosya boş (0 bayt): yazma yarıda kalmış olabilir; varsa .bak yedeğini ya da kurtarma kaydını açın.";
        return s;
    }
    s.bicim = BicimSapta(std::string_view(veri).substr(0, 512), Uzanti(yol));
    switch (s.bicim) {
        case DosyaBicimi::Op4: {
            OkumaSonucu z = ProjeZipCoz(veri);
            z.bicim = DosyaBicimi::Op4;
            return z;
        }
        case DosyaBicimi::Op4Deneme:
            DenemeOku(veri, s);
            return s;
        case DosyaBicimi::Matris:
            MatrisOku(veri, s);
            return s;
        case DosyaBicimi::BinaJson: {
            std::string model;
            if (!BinaMetniCikar(veri, model, s.hata)) return s;
            s.icerik.Koy(proje_yolu::MODEL, std::move(model));
            s.basarili = true;
            return s;
        }
        case DosyaBicimi::Ifc:
            s.hata = "IFC içe aktarma Faz 6'da gelecek; op4 şimdilik IFC'ye yalnız dışa aktarır (Dosya › Dışa aktar › IFC).";
            return s;
        case DosyaBicimi::Bilinmiyor:
        default:
            s.hata = "Dosya biçimi tanınmadı: op4 projesi (.op4), web sürümü projesi (.matris) ya da bina JSON'u (.json) "
                     "bekleniyor.";
            return s;
    }
}

bool ProjeYaz(const std::string& yol, const ProjeIcerigi& icerik, const ProjeManifest& manifest, std::string& hata) {
    std::string zip;
    if (!ProjeZipKur(icerik, manifest, zip, hata)) return false;
    // Diske gitmeden önce bellekteki arşiv denetlenir: bozuk bir arşiv eski dosyanın yerine hiç konmaz.
    const OkumaSonucu d = ProjeZipCoz(zip);
    if (!d.basarili) {
        hata = "İç hata: yazılacak arşiv doğrulanamadı (" + d.hata + "); dosyaya dokunulmadı.";
        return false;
    }
    return AtomikYaz(yol, zip, false, hata);
}

void SonDosyaEkle(std::vector<std::string>& liste, const std::string& yol, size_t enFazla) {
    if (yol.empty()) return;
    const std::string anahtar = TurkceKatla(yol);
    liste.erase(std::remove_if(liste.begin(), liste.end(), [&](const std::string& y) { return TurkceKatla(y) == anahtar; }),
                liste.end());
    liste.insert(liste.begin(), yol);
    if (liste.size() > enFazla) liste.resize(enFazla);
}

std::vector<KurtarmaKaydi> KurtarmaKayitlari(const std::string& kurtarmaDizini) {
    std::vector<KurtarmaKaydi> o;
    std::error_code e;
    const fs::path d = Yol(kurtarmaDizini);
    if (kurtarmaDizini.empty() || !fs::is_directory(d, e)) return o;
    for (fs::directory_iterator i(d, e), son; !e && i != son; i.increment(e)) {
        const fs::path p = i->path();
        if (!i->is_regular_file(e) || p.extension() != ".op4") continue;
        const fs::path kok = p.parent_path() / p.stem();
        if (KilitTutuluyorMu(Utf8(fs::path(kok) += ".kilit"))) continue;  // sahibi yaşıyor (başka op4 penceresi)
        KurtarmaKaydi k;
        k.dosya = Utf8(p);
        std::string meta, h;
        if (DosyaOku(Utf8(fs::path(kok) += ".json"), meta, h)) {
            const json j = json::parse(meta, nullptr, false);
            k.asilYol = MetinAl(j, "asil_yol");
            k.zaman = MetinAl(j, "zaman");
            k.baslik = MetinAl(j, "baslik");
        }
        if (k.zaman.empty()) {
            std::string zip;
            if (DosyaOku(k.dosya, zip, h)) {
                const OkumaSonucu z = ProjeZipCoz(zip);
                k.zaman = z.manifest.kaydedildi;
            }
        }
        if (k.baslik.empty()) k.baslik = k.asilYol.empty() ? Utf8(p.stem()) : Utf8(Yol(k.asilYol).filename());
        o.push_back(std::move(k));
    }
    std::sort(o.begin(), o.end(), [](const KurtarmaKaydi& a, const KurtarmaKaydi& b) {
        return a.zaman != b.zaman ? a.zaman > b.zaman : a.dosya < b.dosya;
    });
    return o;
}

}  // namespace op4
