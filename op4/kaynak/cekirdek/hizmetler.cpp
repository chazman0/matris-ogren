// op4 çekirdek — Hizmetler kancaları ve ortak model akışları (sözleşme S22; tam uygulama).
#include "cekirdek/hizmetler.h"

#include <nlohmann/json.hpp>

#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/proje_belgesi.h"
#include "cekirdek/secim.h"
#include "cekirdek/sonuc.h"

namespace op4 {

void Hizmetler::KareIsiEkle(std::string ad, std::function<void(double)> is) {
    kareIsleri_.emplace_back(std::move(ad), std::move(is));
}

void Hizmetler::KareIsleriniCalistir(double simdiMs) const {
    for (const auto& [ad, is] : kareIsleri_)
        if (is) is(simdiMs);
}

JsonMetni OnayEkle(const JsonMetni& parametreler) {
    nlohmann::json j = parametreler.empty() ? nlohmann::json::object() : nlohmann::json::parse(parametreler, nullptr, false);
    if (j.is_discarded() || !j.is_object()) j = nlohmann::json::object();
    j["onay"] = true;
    return j.dump();
}

namespace {

void Yaz(Hizmetler& h, const std::string& s) {
    if (h.bildirim) h.bildirim->KomutYaz(s);
}

void UyarilariYaz(Hizmetler& h, const IslemRaporu& r) {
    if (!r.basarili && !r.hata.empty()) Yaz(h, "HATA: " + r.hata);
    for (const std::string& u : r.uyarilar) Yaz(h, "Uyarı: " + u);
}

}  // namespace

void ModelIslemiSonrasi(Hizmetler& h, const IslemRaporu& r) {
    UyarilariYaz(h, r);
    if (!r.ModelDegisti()) return;
    if (h.belge) h.belge->KirliIsaretle();
    if (h.secim) h.secim->Ayikla(r.silinen);
    if (h.sonuc) h.sonuc->EskiIsaretle();
    if (h.gorunum) h.gorunum->CizimIste();
    h.modelDegisti.Yay(r);
    h.sahneDegisti.Yay();
}

IslemRaporu ModelIslemiUygula(Hizmetler& h, std::string_view islem, const JsonMetni& parametreler) {
    if (!h.cekirdek) {
        IslemRaporu r;
        r.islem = std::string(islem);
        r.hata = "Model çekirdeği hazır değil.";
        UyarilariYaz(h, r);
        return r;
    }
    IslemRaporu r = h.cekirdek->Uygula(islem, parametreler);
    if (r.gecisOnayi) {
        const int secim = h.iletisim ? h.iletisim->Soru("Genel modele geçiş", r.gecisOnayi->metin,
                                                        {"Genel modele dönüştür", "Vazgeç"}, 1)
                                     : -1;
        if (secim != 0) {
            Yaz(h, "İşlem iptal edildi.");
            r.basarili = false;
            return r;
        }
        r = h.cekirdek->Uygula(islem, OnayEkle(parametreler));
    }
    ModelIslemiSonrasi(h, r);
    return r;
}

IslemRaporu GeriAlUygula(Hizmetler& h) {
    if (!h.cekirdek) return {};
    IslemRaporu r = h.cekirdek->GeriAl();
    ModelIslemiSonrasi(h, r);
    return r;
}

IslemRaporu YineleUygula(Hizmetler& h) {
    if (!h.cekirdek) return {};
    IslemRaporu r = h.cekirdek->Yinele();
    ModelIslemiSonrasi(h, r);
    return r;
}

void ModelYuklendi(Hizmetler& h, const YuklemeSonucu& y) {
    for (const std::string& u : y.uyarilar) Yaz(h, "Uyarı: " + u);
    if (!y.basarili) {
        if (!y.hata.empty()) Yaz(h, "HATA: " + y.hata);
        return;
    }
    if (h.secim) h.secim->Temizle();
    if (h.sonuc) h.sonuc->Temizle();
    if (h.gorunum) h.gorunum->SigdirIste();
    h.modelYuklendi.Yay(y.ozet);
    h.sahneDegisti.Yay();
}

}  // namespace op4
