// op4 çekirdek — proje belgesi durumu ve katkılar (sözleşme S15; tam uygulama). Sahibi: D (dosya-cozum).
#include "cekirdek/proje_belgesi.h"

#include <algorithm>

namespace op4 {

std::string ProjeBelgesi::Ad() const {
    if (yol_.empty()) return gorunenAd_.empty() ? "Adsız " + std::to_string(adsizNo_) : gorunenAd_;
    const size_t i = yol_.find_last_of("\\/");
    return i == std::string::npos ? yol_ : yol_.substr(i + 1);
}

std::string ProjeBelgesi::PencereBasligi() const {
    std::string b = "op4 — " + Ad();
    if (saltOkunur_) b += " (salt okunur)";
    if (kirli_) b += " •";
    return b;
}

void ProjeBelgesi::KirliIsaretle() {
    ++sayac_;
    if (kirli_) return;
    kirli_ = true;
    kirliDegisti.Yay(true);
}

void ProjeBelgesi::Kaydedildi(const std::string& yol) {
    const bool yolDegisti_ = yol != yol_;
    yol_ = yol;
    gorunenAd_.clear();
    saltOkunur_ = false;
    if (yolDegisti_) yolDegisti.Yay(yol_);
    if (kirli_) {
        kirli_ = false;
        kirliDegisti.Yay(false);
    }
    kaydedildi.Yay(yol_);
}

void ProjeBelgesi::Acildi(const std::string& yol, int adsizNo, bool saltOkunur) { Acildi(yol, adsizNo, saltOkunur, {}); }

void ProjeBelgesi::Acildi(const std::string& yol, int adsizNo, bool saltOkunur, const std::string& gorunenAd) {
    const bool yolDegisti_ = yol != yol_;
    yol_ = yol;
    gorunenAd_ = yol.empty() ? gorunenAd : std::string();
    adsizNo_ = adsizNo > 0 ? adsizNo : 1;
    saltOkunur_ = saltOkunur;
    if (yolDegisti_) yolDegisti.Yay(yol_);
    if (kirli_) {
        kirli_ = false;
        kirliDegisti.Yay(false);
    }
    acildi.Yay();
}

void ProjeBelgesi::KatkiEkle(ProjeKatkisi k) {
    katkilar_.push_back(std::move(k));
    std::stable_sort(katkilar_.begin(), katkilar_.end(),
                     [](const ProjeKatkisi& a, const ProjeKatkisi& b) { return a.sira < b.sira; });
}

size_t ProjeBelgesi::KatkiKaldir(const std::string& ad) {
    const size_t once = katkilar_.size();
    katkilar_.erase(std::remove_if(katkilar_.begin(), katkilar_.end(), [&](const ProjeKatkisi& k) { return k.ad == ad; }),
                    katkilar_.end());
    return once - katkilar_.size();
}

void ProjeBelgesi::IcerikTopla(ProjeIcerigi& icerik) const {
    for (const ProjeKatkisi& k : katkilar_)
        if (k.yaz) k.yaz(icerik);
}

void ProjeBelgesi::IcerikDagit(const ProjeIcerigi& icerik, std::vector<std::string>& uyarilar) const {
    for (const ProjeKatkisi& k : katkilar_)
        if (k.oku) k.oku(icerik, uyarilar);
}

void ProjeBelgesi::Sifirla() const {
    for (const ProjeKatkisi& k : katkilar_)
        if (k.sifirla) k.sifirla();
}

}  // namespace op4
