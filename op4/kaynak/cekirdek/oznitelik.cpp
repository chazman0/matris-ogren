// op4 çekirdek — öznitelik tablosu yardımcıları (sözleşme S5; tam uygulama — tabloyu üreten B'nin çekirdeğidir).
#include "cekirdek/oznitelik.h"

#include <cmath>

#include "cekirdek/turkce.h"

namespace op4 {

void OznitelikTablosu::DizinleriKur() {
    satirDizini_.clear();
    sutunDizini_.clear();
    satirDizini_.reserve(satirlar.size());
    for (size_t i = 0; i < satirlar.size(); ++i) satirDizini_[satirlar[i].Anahtar()] = static_cast<uint32_t>(i);
    for (size_t i = 0; i < sutunlar.size(); ++i) sutunDizini_[sutunlar[i].id] = static_cast<uint32_t>(i);
}

const OznitelikSutunu* OznitelikTablosu::Sutun(std::string_view id) const {
    const auto i = sutunDizini_.find(std::string(id));
    return i == sutunDizini_.end() ? nullptr : &sutunlar[i->second];
}

std::optional<size_t> OznitelikTablosu::Satir(ElemanKimligi k) const {
    const auto i = satirDizini_.find(k.Anahtar());
    if (i == satirDizini_.end()) return std::nullopt;
    return static_cast<size_t>(i->second);
}

std::optional<double> OznitelikTablosu::Sayi(size_t satir, std::string_view id) const {
    const OznitelikSutunu* s = Sutun(id);
    if (!s || (s->tur != OznitelikTuru::Sayi && s->tur != OznitelikTuru::Bool) || satir >= s->sayi.size()) return std::nullopt;
    const double v = s->sayi[satir];
    if (std::isnan(v)) return std::nullopt;
    return v;
}

std::optional<std::string_view> OznitelikTablosu::Metin(size_t satir, std::string_view id) const {
    const OznitelikSutunu* s = Sutun(id);
    if (!s || (s->tur != OznitelikTuru::Metin && s->tur != OznitelikTuru::Enum) || satir >= s->kod.size()) return std::nullopt;
    const uint32_t k = s->kod[satir];
    if (k == OZNITELIK_YOK || k >= s->sozluk.size()) return std::nullopt;
    return std::string_view(s->sozluk[k]);
}

std::vector<double> OznitelikTablosu::Liste(size_t satir, std::string_view id) const {
    const OznitelikSutunu* s = Sutun(id);
    if (!s || s->tur != OznitelikTuru::Liste || satir + 1 >= s->listeBas.size()) return {};
    const uint32_t a = s->listeBas[satir], b = s->listeBas[satir + 1];
    if (a > b || b > s->listeDeger.size()) return {};
    return std::vector<double>(s->listeDeger.begin() + a, s->listeDeger.begin() + b);
}

std::string OznitelikTablosu::Gosterim(size_t satir, const OznitelikSutunu& s) const {
    switch (s.tur) {
        case OznitelikTuru::Sayi: {
            if (satir >= s.sayi.size() || std::isnan(s.sayi[satir])) return "";
            std::string m = OndalikVirgul(s.sayi[satir], 3);
            if (!s.birim.empty()) m += (s.birim == "°" ? "" : " ") + s.birim;
            return m;
        }
        case OznitelikTuru::Bool:
            if (satir >= s.sayi.size() || std::isnan(s.sayi[satir])) return "";
            return s.sayi[satir] != 0.0 ? "evet" : "hayır";
        case OznitelikTuru::Metin:
        case OznitelikTuru::Enum: {
            if (satir >= s.kod.size()) return "";
            const uint32_t k = s.kod[satir];
            return k == OZNITELIK_YOK || k >= s.sozluk.size() ? std::string() : s.sozluk[k];
        }
        case OznitelikTuru::Liste: {
            if (satir + 1 >= s.listeBas.size()) return "";
            std::string m;
            for (uint32_t i = s.listeBas[satir]; i < s.listeBas[satir + 1] && i < s.listeDeger.size(); ++i) {
                if (!m.empty()) m += ", ";
                m += OndalikVirgul(s.listeDeger[i], 3);
            }
            return m;
        }
    }
    return "";
}

OznitelikPtr BosOznitelikTablosu() {
    static const OznitelikPtr bos = [] {
        auto t = std::make_shared<OznitelikTablosu>();
        using namespace oznitelik;
        const std::pair<const char*, OznitelikTuru> sutunlar[] = {
            {TUR, OznitelikTuru::Enum},       {NO, OznitelikTuru::Sayi},        {AD, OznitelikTuru::Metin},
            {ALT_TUR, OznitelikTuru::Enum},   {KULLANIM_YERI, OznitelikTuru::Enum}, {KAT, OznitelikTuru::Liste},
            {SEVIYE, OznitelikTuru::Metin},   {KESIT, OznitelikTuru::Metin},    {PROFIL, OznitelikTuru::Metin},
            {MALZEME, OznitelikTuru::Metin},  {SISTEM, OznitelikTuru::Enum},    {GRUP, OznitelikTuru::Metin},
            {UZUNLUK, OznitelikTuru::Sayi},   {EGIM, OznitelikTuru::Sayi},      {ACI, OznitelikTuru::Sayi},
            {KALINLIK, OznitelikTuru::Sayi},  {ALAN, OznitelikTuru::Sayi},      {SERBEST_I, OznitelikTuru::Metin},
            {SERBEST_J, OznitelikTuru::Metin}, {SERBEST_DUGUM, OznitelikTuru::Bool}, {X, OznitelikTuru::Sayi},
            {Y, OznitelikTuru::Sayi},         {Z, OznitelikTuru::Sayi},
        };
        for (const auto& [id, tur] : sutunlar) {
            OznitelikSutunu s;
            s.id = id;
            s.tur = tur;
            if (tur == OznitelikTuru::Liste) s.listeBas = {0};
            t->sutunlar.push_back(std::move(s));
        }
        t->DizinleriKur();
        return OznitelikPtr(t);
    }();
    return bos;
}

std::vector<std::pair<std::string, std::string>> OrtakOzellikler(const OznitelikTablosu& t,
                                                                 const std::vector<ElemanKimligi>& secili) {
    std::vector<size_t> satirlar;
    for (const ElemanKimligi& k : secili)
        if (const auto s = t.Satir(k)) satirlar.push_back(*s);
    std::vector<std::pair<std::string, std::string>> sonuc;
    if (satirlar.empty()) return sonuc;
    for (const OznitelikSutunu& s : t.sutunlar) {
        bool ilk = true, cesitli = false, herhangi = false;
        std::string deger;
        for (const size_t r : satirlar) {
            const std::string g = t.Gosterim(r, s);
            if (!g.empty()) herhangi = true;
            if (ilk) {
                deger = g;
                ilk = false;
            } else if (g != deger) {
                cesitli = true;
                break;
            }
        }
        if (!herhangi) continue;
        sonuc.emplace_back(s.id, cesitli ? std::string("(çeşitli)") : deger);
    }
    return sonuc;
}

}  // namespace op4
