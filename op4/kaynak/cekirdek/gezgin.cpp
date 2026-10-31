// op4 çekirdek — model gezgini ağacı (sözleşme S10; tam uygulama). Uygulayan: C, Faz 1 iş 1.4.
//
// Proje → Katlar → Kat k (üstten alta) → alt tür ("Kolonlar", "Kirişler" …) → kullanım yeri ("Köşe", "Kenar", "İç" …).
// Kata atanmamış elemanlar "Temel ve kat dışı" düğümündedir. Her düğümün `elemanlar` listesi o alt ağacın tekrarsız,
// sıralı elemanlarıdır (tık seçer, Ctrl ekler); `sayi` onun uzunluğudur.
#include "cekirdek/gezgin.h"

#include <algorithm>
#include <cmath>
#include <map>

#include "cekirdek/turkce.h"

namespace op4 {
namespace {

struct TurBilgisi {
    const char* kod;
    const char* baslik;
};
// Görüntü sırası (Stüdyo taslağı: Kolonlar, Kirişler, İkincil kirişler, Çaprazlar, Döşemeler, Düğümler).
constexpr TurBilgisi kTurler[] = {
    {"kolon", "Kolonlar"},
    {"kiris", "Kirişler"},
    {"asik", "Aşıklar"},
    {"capraz", "Çaprazlar"},
    {"makas-ust", "Makas üst başlıkları"},
    {"makas-alt", "Makas alt başlıkları"},
    {"makas-dikme", "Makas dikmeleri"},
    {"makas-diyagonal", "Makas diyagonalleri"},
    {"kren", "Kren kirişleri"},
    {"bag", "Bağlar"},
    {"doseme", "Döşemeler"},
    {"cati", "Çatı panelleri"},
    {"cephe", "Cephe panelleri"},
    {"temel", "Temeller"},
    {"mesnet", "Mesnetler"},
    {"dugum", "Düğümler"},
    {"diger", "Diğer"},
};

const char* YerBasligi(std::string_view y) {
    static const std::pair<const char*, const char*> adlar[] = {
        {"kose", "Köşe"},         {"kenar", "Kenar"},         {"ic", "İç"},           {"dis", "Dış"},
        {"konsol", "Konsol"},     {"dis-cephe", "Dış cephe"}, {"temel", "Temel"},     {"kolon-ustu", "Kolon üstü"},
        {"ara", "Ara"},           {"+x", "+X cephesi"},       {"-x", "−X cephesi"},   {"+y", "+Y cephesi"},
        {"-y", "−Y cephesi"},
    };
    for (const auto& [k, b] : adlar)
        if (y == k) return b;
    return nullptr;
}

int TurSirasi(std::string_view kod) {
    for (size_t i = 0; i < std::size(kTurler); ++i)
        if (kod == kTurler[i].kod) return static_cast<int>(i);
    return static_cast<int>(std::size(kTurler));
}

void Tekille(std::vector<ElemanKimligi>& v) {
    std::sort(v.begin(), v.end());
    v.erase(std::unique(v.begin(), v.end()), v.end());
}

// "+9,00", "±0,00", "−3,20"
std::string KotMetni(double z) {
    if (std::fabs(z) < 0.0005) return "±0,00";
    char b[32];
    std::snprintf(b, sizeof(b), "%.2f", std::fabs(z));
    std::string s = b;
    for (char& c : s)
        if (c == '.') c = ',';
    return (z > 0 ? "+" : "−") + s;
}

struct Satir {
    ElemanKimligi k;
    std::string altTur, yer;
};

GezginDugumu TurDugumu(const std::string& onAnahtar, const std::string& tur, std::vector<Satir>& satirlar) {
    GezginDugumu d;
    d.anahtar = onAnahtar + "/alt_tur:" + tur;
    const int s = TurSirasi(tur);
    d.baslik = s < static_cast<int>(std::size(kTurler)) ? kTurler[s].baslik : tur;
    std::map<std::string, std::vector<ElemanKimligi>> yerler;
    for (const Satir& r : satirlar) {
        d.elemanlar.push_back(r.k);
        yerler[r.yer].push_back(r.k);
    }
    Tekille(d.elemanlar);
    d.sayi = d.elemanlar.size();
    const bool sinifli = yerler.size() > 1 || (yerler.size() == 1 && !yerler.begin()->first.empty());
    if (sinifli) {
        for (auto& [yer, el] : yerler) {
            GezginDugumu c;
            c.anahtar = d.anahtar + "/kullanim_yeri:" + yer;
            const char* b = YerBasligi(yer);
            c.baslik = yer.empty() ? "Sınıfsız" : (b ? b : yer);
            c.elemanlar = std::move(el);
            Tekille(c.elemanlar);
            c.sayi = c.elemanlar.size();
            d.cocuklar.push_back(std::move(c));
        }
        // Sınıfsız en sonda.
        std::stable_sort(d.cocuklar.begin(), d.cocuklar.end(), [](const GezginDugumu& a, const GezginDugumu& b) {
            const bool sa = a.baslik == "Sınıfsız", sb = b.baslik == "Sınıfsız";
            return sa != sb ? sb : false;
        });
    }
    return d;
}

GezginDugumu KatDugumu(const std::string& anahtar, std::string baslik, std::vector<Satir>& satirlar) {
    GezginDugumu d;
    d.anahtar = anahtar;
    d.baslik = std::move(baslik);
    std::map<int, std::pair<std::string, std::vector<Satir>>> turler;
    for (const Satir& r : satirlar) {
        auto& t = turler[TurSirasi(r.altTur)];
        t.first = r.altTur;
        t.second.push_back(r);
        d.elemanlar.push_back(r.k);
    }
    Tekille(d.elemanlar);
    d.sayi = d.elemanlar.size();
    for (auto& [s, t] : turler) d.cocuklar.push_back(TurDugumu(anahtar, t.first, t.second));
    return d;
}

}  // namespace

GezginDugumu GezginAgaciKur(const OznitelikTablosu& t) { return GezginAgaciKur(t, nullptr); }

GezginDugumu GezginAgaciKur(const OznitelikTablosu& t, const SahneAnlik* sahne) {
    GezginDugumu kok;
    kok.anahtar = "proje";
    kok.baslik = sahne && !sahne->baslik.empty() ? sahne->baslik : "Proje";
    kok.elemanlar = t.satirlar;
    Tekille(kok.elemanlar);
    kok.sayi = kok.elemanlar.size();
    if (t.satirlar.empty()) return kok;

    std::map<int, std::vector<Satir>> katlar;  // kat no → satırlar; −1 = kat dışı
    for (size_t i = 0; i < t.satirlar.size(); ++i) {
        Satir r;
        r.k = t.satirlar[i];
        if (const auto a = t.Metin(i, oznitelik::ALT_TUR)) r.altTur = std::string(*a);
        if (r.altTur.empty()) {
            switch (r.k.tur) {
                case ElemanTuru::Dugum: r.altTur = "dugum"; break;
                case ElemanTuru::Mesnet: r.altTur = "mesnet"; break;
                case ElemanTuru::Temel: r.altTur = "temel"; break;
                default: r.altTur = "diger"; break;
            }
        }
        if (const auto y = t.Metin(i, oznitelik::KULLANIM_YERI)) r.yer = std::string(*y);
        const std::vector<double> k = t.Liste(i, oznitelik::KAT);
        if (k.empty()) {
            katlar[-1].push_back(r);
        } else {
            std::vector<int> goruldu;
            for (const double v : k) {
                const int no = static_cast<int>(std::lround(v));
                if (std::find(goruldu.begin(), goruldu.end(), no) != goruldu.end()) continue;
                goruldu.push_back(no);
                katlar[no].push_back(r);
            }
        }
    }

    GezginDugumu katKok;
    katKok.anahtar = "katlar";
    katKok.baslik = "Katlar";
    for (auto it = katlar.rbegin(); it != katlar.rend(); ++it) {
        const int no = it->first;
        if (no < 0) continue;
        std::string baslik = no == 0 ? "Zemin" : "Kat " + std::to_string(no);
        GezginDugumu d = KatDugumu("kat:" + std::to_string(no), std::move(baslik), it->second);
        if (sahne)
            for (const SahneSeviyesi& s : sahne->seviyeler)
                if (s.kat == no) {
                    d.bilgi = KotMetni(s.z);
                    break;
                }
        for (const ElemanKimligi& e : d.elemanlar) katKok.elemanlar.push_back(e);
        katKok.cocuklar.push_back(std::move(d));
    }
    Tekille(katKok.elemanlar);
    katKok.sayi = katKok.elemanlar.size();
    if (!katKok.cocuklar.empty()) kok.cocuklar.push_back(std::move(katKok));
    if (const auto d = katlar.find(-1); d != katlar.end())
        kok.cocuklar.push_back(KatDugumu("kat:-", "Temel ve kat dışı", d->second));
    return kok;
}

}  // namespace op4
