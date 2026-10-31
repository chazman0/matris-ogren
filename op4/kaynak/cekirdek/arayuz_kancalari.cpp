// op4 çekirdek — arayüz kancaları kayıt defteri ve pencere açmayan bildirim / iletişim sürümleri (sözleşme S21; tam
// uygulama). Sahibi: C (arayuz-goruntu).
#include "cekirdek/arayuz_kancalari.h"

#include <algorithm>
#include <cstdlib>

namespace op4 {

void ArayuzKancalari::PanelEkle(PanelKaydi p) {
    const bool acik = p.varsayilanAcik;
    for (size_t i = 0; i < paneller_.size(); ++i)
        if (paneller_[i].id == p.id) {
            paneller_[i] = std::move(p);
            return;
        }
    paneller_.push_back(std::move(p));
    acik_.push_back(acik);
    // (yer, sira) sırası; açık bayrakları birlikte taşınır.
    std::vector<size_t> d(paneller_.size());
    for (size_t i = 0; i < d.size(); ++i) d[i] = i;
    std::stable_sort(d.begin(), d.end(), [&](size_t a, size_t b) {
        const PanelKaydi &x = paneller_[a], &y = paneller_[b];
        return x.yer != y.yer ? x.yer < y.yer : x.sira < y.sira;
    });
    std::vector<PanelKaydi> p2;
    std::vector<bool> a2;
    for (const size_t i : d) {
        p2.push_back(std::move(paneller_[i]));
        a2.push_back(acik_[i]);
    }
    paneller_ = std::move(p2);
    acik_ = std::move(a2);
}

void ArayuzKancalari::DurumOgesiEkle(DurumOgesi o) {
    (void)std::erase_if(durum_, [&](const DurumOgesi& x) { return x.id == o.id; });
    durum_.push_back(std::move(o));
    std::stable_sort(durum_.begin(), durum_.end(), [](const DurumOgesi& a, const DurumOgesi& b) {
        return a.sagda != b.sagda ? !a.sagda : a.sira < b.sira;
    });
}

void ArayuzKancalari::MenuKatkisiEkle(MenuKatkisi m) {
    menu_.push_back(std::move(m));
    std::stable_sort(menu_.begin(), menu_.end(), [](const MenuKatkisi& a, const MenuKatkisi& b) { return a.sira < b.sira; });
}

void ArayuzKancalari::AyarSayfasiEkle(AyarSayfasi s) {
    (void)std::erase_if(ayar_, [&](const AyarSayfasi& x) { return x.id == s.id; });
    ayar_.push_back(std::move(s));
    std::stable_sort(ayar_.begin(), ayar_.end(), [](const AyarSayfasi& a, const AyarSayfasi& b) { return a.sira < b.sira; });
}

void ArayuzKancalari::IletisimEkle(IletisimKaydi k) {
    (void)std::erase_if(iletisim_, [&](const IletisimKaydi& x) { return x.id == k.id; });
    iletisim_.push_back(std::move(k));
}

const IletisimKaydi* ArayuzKancalari::Iletisim(std::string_view id) const {
    for (const IletisimKaydi& k : iletisim_)
        if (k.id == id) return &k;
    return nullptr;
}

std::vector<const MenuKatkisi*> ArayuzKancalari::MenuKatkilari(std::string_view menu) const {
    std::vector<const MenuKatkisi*> o;
    for (const MenuKatkisi& m : menu_)
        if (m.menu == menu) o.push_back(&m);
    return o;
}

const PanelKaydi* ArayuzKancalari::Panel(std::string_view id) const {
    for (const PanelKaydi& p : paneller_)
        if (p.id == id) return &p;
    return nullptr;
}

bool ArayuzKancalari::PanelAcik(std::string_view id) const {
    for (size_t i = 0; i < paneller_.size(); ++i)
        if (paneller_[i].id == id) return acik_[i];
    return false;
}

void ArayuzKancalari::PanelGoster(std::string_view id, bool acik) {
    for (size_t i = 0; i < paneller_.size(); ++i)
        if (paneller_[i].id == id) acik_[i] = acik;
}

// ---- pencere açmayan sürümler --------------------------------------------------------------------------------------
void GunlukBildirimleri::KomutYaz(std::string_view satir) {
    satirlar.emplace_back(satir);
    if (yaz_) yaz_(satir);
}

void GunlukBildirimleri::Tost(std::string_view metin, TostTuru tur) {
    static const char* const kTur[] = {"bilgi", "basari", "uyari", "hata"};
    const std::string s = std::string("[tost ") + kTur[static_cast<int>(tur) & 3] + "] " + std::string(metin);
    satirlar.push_back(s);
    if (yaz_) yaz_(s);
}

void GunlukBildirimleri::Ilerleme(std::string_view id, std::string_view metin, float oran, std::function<void()>) {
    const std::string s = "[ilerleme " + std::string(id) + "] " + std::string(metin) + " " +
                          std::to_string(static_cast<int>(oran * 100.0f)) + "%";
    satirlar.push_back(s);
    if (yaz_) yaz_(s);
}

void GunlukBildirimleri::IlerlemeBitti(std::string_view id) {
    const std::string s = "[ilerleme " + std::string(id) + "] bitti";
    satirlar.push_back(s);
    if (yaz_) yaz_(s);
}

std::optional<std::string> BetikliIletisimKutulari::Siradaki() {
    if (yanitlar.empty()) return std::nullopt;
    std::string y = yanitlar.front();
    yanitlar.erase(yanitlar.begin());
    if (y.empty()) return std::nullopt;
    return y;
}

std::optional<std::string> BetikliIletisimKutulari::DosyaAc(std::string_view baslik, const std::vector<DosyaSuzgeci>&,
                                                           std::string_view) {
    sorulanlar.emplace_back(baslik);
    return Siradaki();
}

std::optional<std::string> BetikliIletisimKutulari::DosyaKaydet(std::string_view baslik, const std::vector<DosyaSuzgeci>&,
                                                               std::string_view) {
    sorulanlar.emplace_back(baslik);
    return Siradaki();
}

int BetikliIletisimKutulari::Soru(std::string_view baslik, std::string_view, const std::vector<std::string>& dugmeler,
                                  int) {
    sorulanlar.emplace_back(baslik);
    const auto y = Siradaki();
    if (!y) return -1;
    const int i = std::atoi(y->c_str());
    return i >= 0 && static_cast<size_t>(i) < dugmeler.size() ? i : -1;
}

}  // namespace op4
