// op4 çekirdek — komut satırı / hızlı başlat modeli (bkz. komut_satiri.h). Sahibi: C.
#include "cekirdek/komut_satiri.h"

#include <algorithm>
#include <cctype>

#include "cekirdek/turkce.h"

namespace op4 {
namespace {

std::string Kirp(std::string_view s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.remove_prefix(1);
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.remove_suffix(1);
    return std::string(s);
}

}  // namespace

void KomutSatiri::GecmiseEkle(std::string_view satir) {
    const std::string s = Kirp(satir);
    konum_ = -1;
    if (s.empty()) return;
    if (!gecmis_.empty() && gecmis_.back() == s) return;
    gecmis_.push_back(s);
    while (gecmis_.size() > enFazla_) gecmis_.pop_front();
}

std::optional<std::string> KomutSatiri::Onceki(std::string_view simdiki) {
    if (gecmis_.empty()) return std::nullopt;
    if (konum_ < 0) {
        bekleyen_ = std::string(simdiki);
        konum_ = static_cast<int>(gecmis_.size()) - 1;
    } else if (konum_ > 0) {
        --konum_;
    } else {
        return std::nullopt;
    }
    return gecmis_[static_cast<size_t>(konum_)];
}

std::optional<std::string> KomutSatiri::Sonraki() {
    if (konum_ < 0) return std::nullopt;
    if (konum_ + 1 < static_cast<int>(gecmis_.size())) {
        ++konum_;
        return gecmis_[static_cast<size_t>(konum_)];
    }
    konum_ = -1;
    return bekleyen_;
}

void KomutSatiri::KomutCalisti(std::string_view id) {
    const std::string s(id);
    son_.erase(std::remove(son_.begin(), son_.end(), s), son_.end());
    son_.push_front(s);
    while (son_.size() > 12) son_.pop_back();
}

std::vector<const KomutTanimi*> KomutSatiri::Oneriler(const KomutYoneticisi& k, std::string_view yazilan,
                                                      OneriKumesi kume, size_t enFazla) const {
    std::vector<const KomutTanimi*> o;
    auto uygun = [&](const KomutTanimi* t) {
        switch (kume) {
            case OneriKumesi::Tumu: return true;
            case OneriKumesi::Son: return std::find(son_.begin(), son_.end(), t->id) != son_.end();
            case OneriKumesi::Serit: return t->serit.has_value();
            case OneriKumesi::Menu: return !t->menu.empty();
        }
        return true;
    };
    const std::string y = Kirp(yazilan);
    if (y.empty()) {
        for (const std::string& id : son_)
            if (const KomutTanimi* t = k.Bul(id); t && uygun(t) && o.size() < enFazla) o.push_back(t);
        if (o.empty() && kume != OneriKumesi::Son)
            for (const KomutTanimi& t : k.Tanimlar())
                if (t.hizliErisim && uygun(&t) && o.size() < enFazla) o.push_back(&t);
        return o;
    }
    // İlk sözcük komut adıdır; argüman yazılıyorsa öneri yalnız o komut.
    const size_t b = y.find(' ');
    const std::string ad = b == std::string::npos ? y : y.substr(0, b);
    for (const KomutTanimi* t : k.Tamamla(ad, 64))
        if (uygun(t) && o.size() < enFazla) o.push_back(t);
    return o;
}

bool KomutSatiri::Calistir(KomutYoneticisi& k, Hizmetler& h, std::string_view satir, std::string& ileti) {
    ileti.clear();
    const std::string s = Kirp(satir);
    std::string hata;
    const bool tamam = k.SatirCalistir(s, h, &hata);
    if (!tamam) {
        ileti = hata.empty() && s.empty() ? std::string("Yinelenecek komut yok.") : hata;
        return false;
    }
    if (!s.empty()) GecmiseEkle(s);
    if (const KomutTanimi* t = k.Bul(s.substr(0, s.find(' '))); t)
        KomutCalisti(t->id);
    else if (s.empty() && !k.SonKomut().empty())
        KomutCalisti(k.SonKomut());
    return true;
}

bool KomutSatiri::OneriCalistir(KomutYoneticisi& k, Hizmetler& h, const KomutTanimi& t, std::string& ileti) {
    ileti.clear();
    std::string hata;
    if (!k.Calistir(t.id, h, KomutKaynagi::KomutSatiri, {}, &hata)) {
        ileti = hata;
        return false;
    }
    GecmiseEkle(t.ad);
    KomutCalisti(t.id);
    return true;
}

}  // namespace op4
