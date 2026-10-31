// op4 çekirdek — komut kayıt defteri (sözleşme S20; tam uygulama). Sahibi: C (arayuz-goruntu).
#include "cekirdek/komut.h"

#include <algorithm>
#include <cctype>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

#include "cekirdek/turkce.h"

namespace op4 {
namespace {

std::string Kirp(std::string_view s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.remove_prefix(1);
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.remove_suffix(1);
    return std::string(s);
}

std::string AsciiKucuk(std::string s) {
    for (char& c : s)
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    return s;
}

std::string TusAdi(const std::string& k) {
    const std::string t = AsciiKucuk(k);
    if (t.size() == 1) {
        const char c = t[0];
        if (c >= 'a' && c <= 'z') return std::string(1, static_cast<char>(c - 'a' + 'A'));
        if (c >= '0' && c <= '9') return t;
        return "";
    }
    if (t.size() >= 2 && t[0] == 'f' && std::all_of(t.begin() + 1, t.end(), [](char c) { return c >= '0' && c <= '9'; })) {
        const int n = std::stoi(t.substr(1));
        return n >= 1 && n <= 24 ? "F" + std::to_string(n) : "";
    }
    static const std::pair<const char*, const char*> adlar[] = {
        {"pageup", "PageUp"},   {"pgup", "PageUp"},     {"pagedown", "PageDown"}, {"pgdn", "PageDown"},
        {"escape", "Escape"},   {"esc", "Escape"},      {"delete", "Delete"},     {"del", "Delete"},
        {"enter", "Enter"},     {"return", "Enter"},    {"space", "Space"},       {"bosluk", "Space"},
        {"tab", "Tab"},         {"home", "Home"},       {"end", "End"},           {"insert", "Insert"},
        {"backspace", "Backspace"},
    };
    for (const auto& [a, b] : adlar)
        if (t == a) return b;
    return "";
}

// Katlanmış iki ad arasındaki düzenleme uzaklığı (Levenshtein); yakın komut önerisi için.
size_t Uzaklik(const std::string& a, const std::string& b) {
    std::vector<size_t> once(b.size() + 1), simdi(b.size() + 1);
    for (size_t j = 0; j <= b.size(); ++j) once[j] = j;
    for (size_t i = 1; i <= a.size(); ++i) {
        simdi[0] = i;
        for (size_t j = 1; j <= b.size(); ++j)
            simdi[j] = std::min({once[j] + 1, simdi[j - 1] + 1, once[j - 1] + (a[i - 1] == b[j - 1] ? 0u : 1u)});
        std::swap(once, simdi);
    }
    return once[b.size()];
}

SecimKosulu SecimOku(const std::string& s) {
    if (s == "once") return SecimKosulu::Once;
    if (s == "sonra") return SecimKosulu::Sonra;
    return SecimKosulu::Yok;
}

}  // namespace

std::string KisayolNormal(std::string_view kisayol) {
    bool ctrl = false, shift = false, alt = false;
    std::string tus;
    size_t bas = 0;
    const std::string s(kisayol);
    if (Kirp(s).empty()) return "";
    while (bas <= s.size()) {
        size_t son = s.find('+', bas);
        if (son == std::string::npos) son = s.size();
        std::string parca = Kirp(std::string_view(s).substr(bas, son - bas));
        if (parca.empty() && son < s.size()) parca = "+";  // "Ctrl++" gibi; desteklenmez
        const std::string k = AsciiKucuk(parca);
        if (k == "ctrl" || k == "control" || k == "ctl") ctrl = true;
        else if (k == "shift") shift = true;
        else if (k == "alt") alt = true;
        else {
            if (!tus.empty()) return "";
            tus = TusAdi(parca);
            if (tus.empty()) return "";
        }
        bas = son + 1;
    }
    if (tus.empty()) return "";
    std::string o;
    if (ctrl) o += "Ctrl+";
    if (shift) o += "Shift+";
    if (alt) o += "Alt+";
    return o + tus;
}

void KomutYoneticisi::DizinKur() {
    idDizini_.clear();
    for (size_t i = 0; i < tanimlar_.size(); ++i) idDizini_[tanimlar_[i].id] = i;
}

void KomutYoneticisi::Tanimla(KomutTanimi t) {
    t.kisayol = KisayolNormal(t.kisayol);
    const auto i = idDizini_.find(t.id);
    if (i != idDizini_.end()) {
        tanimlar_[i->second] = std::move(t);
        return;
    }
    tanimlar_.push_back(std::move(t));
    DizinKur();
}

bool KomutYoneticisi::KatalogYukle(std::string_view katalog, std::string& hata) {
    using nlohmann::json;
    const json j = json::parse(katalog, nullptr, false);
    if (j.is_discarded() || !j.is_object() || !j.contains("komutlar") || !j["komutlar"].is_array()) {
        hata = "komutlar.json bozuk: {\"komutlar\": [...]} bekleniyor";
        return false;
    }
    auto metin = [](const json& o, const char* ad) {
        return o.contains(ad) && o[ad].is_string() ? o[ad].get<std::string>() : std::string();
    };
    auto evet = [](const json& o, const char* ad) { return o.contains(ad) && o[ad].is_boolean() && o[ad].get<bool>(); };
    auto tam = [](const json& o, const char* ad) { return o.contains(ad) && o[ad].is_number_integer() ? o[ad].get<int>() : 0; };
    if (j.contains("sekmeler") && j["sekmeler"].is_array()) {
        sekmeler_.clear();
        for (const json& s : j["sekmeler"])
            if (s.is_string()) sekmeler_.push_back(s.get<std::string>());
    }
    for (const json& k : j["komutlar"]) {
        if (!k.is_object()) continue;
        KomutTanimi t;
        t.id = metin(k, "id");
        t.ad = metin(k, "ad");
        if (t.id.empty() || t.ad.empty()) {
            hata = "komutlar.json: id ve ad zorunlu (" + k.dump().substr(0, 80) + ")";
            return false;
        }
        t.etiket = metin(k, "etiket");
        if (t.etiket.empty()) t.etiket = t.ad;
        if (k.contains("takma_adlar") && k["takma_adlar"].is_array())
            for (const json& a : k["takma_adlar"])
                if (a.is_string()) t.takmaAdlar.push_back(a.get<std::string>());
        t.kisayol = metin(k, "kisayol");
        if (!t.kisayol.empty() && KisayolNormal(t.kisayol).empty()) {
            hata = "komutlar.json: '" + t.id + "' kısayolu anlaşılmadı: " + t.kisayol;
            return false;
        }
        t.ikon = metin(k, "ikon");
        if (k.contains("serit") && k["serit"].is_object()) {
            const json& s = k["serit"];
            t.serit = KomutSeritYeri{metin(s, "sekme"), metin(s, "grup"), metin(s, "boyut") == "buyuk", tam(s, "sira")};
        }
        t.menu = metin(k, "menu");
        t.menuSira = tam(k, "menu_sira");
        t.hizliErisim = evet(k, "hizli_erisim");
        t.ipucu = metin(k, "ipucu");
        t.yardim = metin(k, "yardim");
        t.kosul = metin(k, "kosul");
        t.secim = SecimOku(metin(k, "secim"));
        t.tekrarlanir = evet(k, "tekrarlanir");
        t.onayKutusu = evet(k, "onay_kutusu");
        t.sahip = metin(k, "sahip");
        Tanimla(std::move(t));
    }
    return true;
}

bool KomutYoneticisi::Bagla(std::string_view id, KomutIsleyici isleyici) {
    if (!idDizini_.count(std::string(id))) return false;
    isleyiciler_[std::string(id)] = std::move(isleyici);
    return true;
}

const KomutTanimi* KomutYoneticisi::Bul(std::string_view ad) const {
    if (const auto i = idDizini_.find(std::string(ad)); i != idDizini_.end()) return &tanimlar_[i->second];
    const std::string k = TurkceKatla(Kirp(ad));
    if (k.empty()) return nullptr;
    for (const KomutTanimi& t : tanimlar_) {
        if (TurkceKatla(t.ad) == k) return &t;
        for (const std::string& a : t.takmaAdlar)
            if (TurkceKatla(a) == k) return &t;
    }
    return nullptr;
}

const KomutTanimi* KomutYoneticisi::KisayolBul(std::string_view kisayol) const {
    const std::string k = KisayolNormal(kisayol);
    if (k.empty()) return nullptr;
    for (const KomutTanimi& t : tanimlar_)
        if (t.kisayol == k) return &t;
    return nullptr;
}

std::vector<const KomutTanimi*> KomutYoneticisi::Tamamla(std::string_view yazilan, size_t enFazla) const {
    std::vector<const KomutTanimi*> o;
    const std::string k = TurkceKatla(Kirp(yazilan));
    if (k.empty()) return o;
    auto ekle = [&](const KomutTanimi* t) {
        if (o.size() < enFazla && std::find(o.begin(), o.end(), t) == o.end()) o.push_back(t);
    };
    for (const KomutTanimi& t : tanimlar_) {
        bool onek = TurkceKatla(t.ad).rfind(k, 0) == 0;
        for (const std::string& a : t.takmaAdlar) onek = onek || TurkceKatla(a).rfind(k, 0) == 0;
        if (onek) ekle(&t);
    }
    for (const KomutTanimi& t : tanimlar_)
        if (TurkceKatla(t.ad).find(k) != std::string::npos || TurkceKatla(t.etiket).find(k) != std::string::npos) ekle(&t);
    return o;
}

KomutDurumu KomutYoneticisi::Durum(std::string_view id, const Hizmetler& h) const {
    KomutDurumu d;
    const auto i = idDizini_.find(std::string(id));
    if (i == idDizini_.end()) {
        d.neden = "Komut tanımlı değil: " + std::string(id);
        return d;
    }
    d.tanimli = true;
    const auto f = isleyiciler_.find(std::string(id));
    if (f == isleyiciler_.end() || !f->second.calistir) {
        d.neden = tanimlar_[i->second].etiket + ": henüz uygulanmadı";
        return d;
    }
    d.bagli = true;
    d.neden = f->second.kullanilamazNedeni ? f->second.kullanilamazNedeni(h) : std::string();
    d.kullanilabilir = d.neden.empty();
    d.isaretli = f->second.isaretli && f->second.isaretli(h);
    return d;
}

bool KomutYoneticisi::Calistir(std::string_view id, Hizmetler& h, KomutKaynagi kaynak, std::string_view arguman,
                               std::string* hata) {
    const KomutDurumu d = Durum(id, h);
    if (!d.kullanilabilir) {
        if (hata) *hata = d.neden;
        return false;
    }
    const KomutTanimi& t = tanimlar_[idDizini_.at(std::string(id))];
    const KomutIsleyici isleyici = isleyiciler_.at(std::string(id));  // kopya: işleyici kendini yeniden bağlayabilir
    KomutBaglami b{h, kaynak, Kirp(arguman)};
    isleyici.calistir(b);
    if (t.tekrarlanir) sonKomut_ = t.id;
    calistirildi.Yay(t.id);
    return true;
}

bool KomutYoneticisi::SatirCalistir(std::string_view satir, Hizmetler& h, std::string* hata) {
    const std::string s = Kirp(satir);
    if (s.empty()) {
        if (sonKomut_.empty()) {
            if (hata) *hata = "";
            return false;
        }
        const std::string son = sonKomut_;
        return Calistir(son, h, KomutKaynagi::KomutSatiri, {}, hata);
    }
    size_t bosluk = 0;
    while (bosluk < s.size() && !std::isspace(static_cast<unsigned char>(s[bosluk]))) ++bosluk;
    const std::string ad = s.substr(0, bosluk);
    const KomutTanimi* t = Bul(ad);
    if (!t) {
        if (hata) {
            *hata = "Bilinmeyen komut: '" + ad + "'.";
            auto yakin = Tamamla(ad, 5);
            if (yakin.empty()) {
                // Yazım hatası: katlanmış ada (ya da takma ada) düzenleme uzaklığı en küçük komutlar.
                const std::string k = TurkceKatla(ad);
                const size_t sinir = std::max<size_t>(1, k.size() / 3);
                std::vector<std::pair<size_t, const KomutTanimi*>> aday;
                for (const KomutTanimi& t : tanimlar_) {
                    size_t u = Uzaklik(k, TurkceKatla(t.ad));
                    for (const std::string& a : t.takmaAdlar) u = std::min(u, Uzaklik(k, TurkceKatla(a)));
                    if (u <= sinir) aday.emplace_back(u, &t);
                }
                std::stable_sort(aday.begin(), aday.end(), [](const auto& x, const auto& y) { return x.first < y.first; });
                for (size_t i = 0; i < aday.size() && i < 3; ++i) yakin.push_back(aday[i].second);
            }
            if (!yakin.empty()) {
                *hata += " Yakın komutlar:";
                for (size_t i = 0; i < yakin.size(); ++i) *hata += (i ? ", " : " ") + yakin[i]->ad;
            }
        }
        return false;
    }
    return Calistir(t->id, h, KomutKaynagi::KomutSatiri, std::string_view(s).substr(bosluk), hata);
}

}  // namespace op4
