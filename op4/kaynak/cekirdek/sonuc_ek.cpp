// op4 çekirdek — sonuç özeti yardımcıları. Sahibi: D (dosya-cozum).
#include "cekirdek/sonuc_ek.h"

#include <algorithm>
#include <cmath>

#include <nlohmann/json.hpp>

namespace op4 {

DcDagilimi DcDagilimiHesapla(const SonucOzeti& o) {
    DcDagilimi d;
    for (const ElemanSonucu& e : o.elemanlar) {
        const double dc = e.dc;
        if (!(dc >= 0) || !std::isfinite(dc)) ++d.yok;
        else if (dc < 0.7) ++d.yesil;
        else if (dc < 0.9) ++d.sari;
        else if (dc <= 1.0) ++d.turuncu;
        else ++d.kirmizi;
    }
    return d;
}

SonucEslemesi TasarimdanEsle(std::string_view veriMetni) {
    using nlohmann::json;
    SonucEslemesi s;
    const json v = json::parse(veriMetni, nullptr, false);
    if (v.is_discarded() || !v.is_object()) {
        s.hata = "Çözüm verisi okunamadı.";
        return s;
    }
    s.basarili = true;
    if (!v.contains("tasarim") || !v["tasarim"].is_object() || !v["tasarim"].contains("elemanlar") ||
        !v["tasarim"]["elemanlar"].is_array())
        return s;
    const json& el = v["tasarim"]["elemanlar"];
    size_t eslenmeyen = 0;
    for (size_t i = 0; i < el.size(); ++i) {
        const json& e = el[i];
        if (!e.is_object() || !e.contains("cubuk") || !e["cubuk"].is_number_integer() || e["cubuk"].get<long long>() <= 0) {
            ++eslenmeyen;
            continue;
        }
        ElemanSonucu r;
        r.kimlik = CubukKimligi(static_cast<uint32_t>(e["cubuk"].get<long long>()));
        r.dc = e.contains("dc") && e["dc"].is_number() ? e["dc"].get<double>() : -1;
        if (e.contains("belirleyen") && e["belirleyen"].is_object()) {
            const json& b = e["belirleyen"];
            r.belirleyen = b.value("kontrol", std::string());
            r.kombinasyon = b.value("kombinasyon", std::string());
        }
        r.tasarimSatiri = static_cast<int>(i);
        s.elemanlar.push_back(std::move(r));
    }
    if (eslenmeyen)
        s.uyarilar.push_back(std::to_string(eslenmeyen) + " tasarım satırı model elemanına eşlenemedi (aks–kat modelinde "
                             "eşlemeyi model çekirdeği yapar).");
    return s;
}

void EslemeyiYerlestir(SonucOzeti& o, SonucEslemesi esleme) {
    auto& e = esleme.elemanlar;
    std::stable_sort(e.begin(), e.end(), [](const ElemanSonucu& a, const ElemanSonucu& b) {
        if (a.kimlik != b.kimlik) return a.kimlik < b.kimlik;
        return a.dc > b.dc;  // aynı kimlikte en büyük D/C önce
    });
    e.erase(std::unique(e.begin(), e.end(), [](const ElemanSonucu& a, const ElemanSonucu& b) { return a.kimlik == b.kimlik; }),
            e.end());
    o.elemanlar = std::move(e);
    for (std::string& u : esleme.uyarilar) o.uyarilar.push_back(std::move(u));
    double enBuyuk = -1;
    size_t asan = 0;
    for (const ElemanSonucu& r : o.elemanlar) {
        if (std::isfinite(r.dc) && r.dc > enBuyuk) {
            enBuyuk = r.dc;
            o.enBuyukDcElemani = r.kimlik;
        }
        if (std::isfinite(r.dc) && r.dc > 1.0) ++asan;
    }
    if (!o.elemanlar.empty()) {
        o.asanSayisi = std::max(o.asanSayisi, asan);
        if (o.enBuyukDc < 0) o.enBuyukDc = enBuyuk;
    }
}

}  // namespace op4
