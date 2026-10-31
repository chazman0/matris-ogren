// op4 — arayüz modülü (C; sözleşme S21, S23). Ana pencere nesnesini (AnaPencere) kurar ve Hizmetler'e bağlar:
//   * Bildirimler (komut satırı çıktısı, tost, ilerleme) — Hizmetler::bildirim,
//   * C'nin komutları (komutlar.json sahip "C": gorunum.*, secim.*, model.hizli_aks, ayarlar.ac, yardim.*, kapsam.*),
//   * C'nin panelleri / ayar sayfaları için S21 kayıtları (görünürlük durumu; çizimi AnaPencere yapar),
//   * gorunum/gorunum.json belge katkısı (kamera, görünüm kipi, ızgara, kenarlar; MIMARI §7.3, kabul C10; Faz 0 eski şeması
//     TASARIM §21.6 da okunur; kayıtlı kamera geri yüklenince bekleyen Sığdır SigdirYapildi ile iptal edilir),
//   * sahneDegisti / modelYuklendi aboneliği (BVH, gezgin, sığdır).
// ImGui bağlamından bağımsızdır: pencere ve DX12 uygulama tarafından (uygulama.cpp) sonra bağlanır.
#include <algorithm>
#include <cmath>
#include <memory>

#include <nlohmann/json.hpp>

#include "arayuz/ana_pencere.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/kabuk.h"
#include "cekirdek/proje_belgesi.h"

namespace op4 {

void ArayuzModuluKur(Hizmetler& h, ModulOrtami& o) {
    AnaPencere* a = o.Tut(std::make_shared<AnaPencere>(h));
    EtkinAnaPencereAyarla(a);
    a->testKipi = o.testKipi;
    a->Bildirim().gunluk = o.gunluk;
    h.bildirim = &a->Bildirim();
    a->KomutlariBagla();
    a->AyarlariUygula();
    if (h.arayuz) {
        h.arayuz->PanelEkle({"model_gezgini", "Model ağacı", PanelYeri::Sol, 10, true, "C", {}});
        h.arayuz->PanelEkle({"ozellikler", "Özellikler", PanelYeri::Sag, 20, true, "C", {}});
        h.arayuz->PanelEkle({"baslangic", "Başlangıç", PanelYeri::Sag, 10, true, "C", {}});
        h.arayuz->pencereyiKapat = [a] {
            if (a->pencere.kapat) a->pencere.kapat();
        };
    }
    // Sahne değişince (model işlemi, geri al, yükleme) ana pencere sürüm farkını bir sonraki karede görür; burada yalnız
    // çizim istenir. Yeni model yüklenince sığdır.
    h.sahneDegisti.Abone([&h] {
        if (h.gorunum) h.gorunum->CizimIste();
    });
    h.modelYuklendi.Abone([&h](const ModelOzeti&) {
        if (h.gorunum) h.gorunum->SigdirIste();
    });
    // gorunum/gorunum.json: kamera ve görünüm kipi .op4 içinde saklanır.
    if (h.belge) {
        ProjeKatkisi k;
        k.ad = "gorunum";
        k.sira = 10;
        k.yaz = [a, &h](ProjeIcerigi& ic) {
            nlohmann::json j;
            j["bicim"] = 1;
            j["kamera"] = nlohmann::json::parse(KameraJson(a->Kamera().d));
            j["kip"] = h.gorunum && h.gorunum->kip != GorunumKipi::Cubuk ? "kesit" : "cubuk";
            j["izgara"] = !h.gorunum || h.gorunum->izgara;
            j["kenarlar"] = !h.gorunum || h.gorunum->kenarlar;
            j["etkin_kat"] = a->etkinKat;
            ic.Koy("gorunum/gorunum.json", j.dump(1));
        };
        k.oku = [a, &h](const ProjeIcerigi& ic, std::vector<std::string>& uyarilar) {
            const std::string* m = ic.Al("gorunum/gorunum.json");
            if (!m) return;
            const nlohmann::json j = nlohmann::json::parse(*m, nullptr, false);
            if (j.is_discarded() || !j.is_object()) {
                uyarilar.push_back("gorunum/gorunum.json okunamadı; varsayılan görünüm");
                return;
            }
            if (j.contains("kamera") && j["kamera"].is_object()) {
                const nlohmann::json& kj = j["kamera"];
                KameraDurumu d = a->Kamera().d;
                if (kj.contains("sapma") || kj.contains("egim")) {
                    // Eski şema (TASARIM §21.6, Faz 0 denemesi "kaynak": "op4-deneme"): açılar radyan, aynı göz yönü
                    // kuralı (cos e·cos s, cos e·sin s, sin e); perspektif.
                    auto sayi = [&](const char* ad, double& v) {
                        if (kj.contains(ad) && kj[ad].is_number() && std::isfinite(kj[ad].get<double>())) v = kj[ad].get<double>();
                    };
                    if (kj.contains("hedef") && kj["hedef"].is_array() && kj["hedef"].size() == 3 && kj["hedef"][0].is_number() &&
                        kj["hedef"][1].is_number() && kj["hedef"][2].is_number())
                        d.hedef = {kj["hedef"][0].get<double>(), kj["hedef"][1].get<double>(), kj["hedef"][2].get<double>()};
                    sayi("uzaklik", d.uzaklik);
                    sayi("sapma", d.sapma);
                    sayi("egim", d.egim);
                    d.uzaklik = std::max(0.1, d.uzaklik);
                    d.egim = std::clamp(d.egim, -KameraSuruklemesi::EGIM_SINIRI, KameraSuruklemesi::EGIM_SINIRI);
                    d.ortografik = false;
                    a->Kamera().d = d;
                } else if (KameraJsonOku(kj.dump(), d)) {
                    a->Kamera().d = d;
                }
            }
            if (h.gorunum) {
                if (j.contains("kip") && j["kip"].is_string()) h.gorunum->kip = j["kip"] == "kesit" ? GorunumKipi::Kesit : GorunumKipi::Cubuk;
                if (j.contains("izgara") && j["izgara"].is_boolean()) h.gorunum->izgara = j["izgara"].get<bool>();
                if (j.contains("kenarlar") && j["kenarlar"].is_boolean()) h.gorunum->kenarlar = j["kenarlar"].get<bool>();
                h.gorunum->SigdirYapildi();  // kayıtlı kamera korunur
            }
            if (j.contains("etkin_kat") && j["etkin_kat"].is_number_integer()) a->etkinKat = j["etkin_kat"].get<int>();
        };
        k.sifirla = [a] { a->StandartGorunum(StandartYon::Izometrik); };
        h.belge->KatkiEkle(std::move(k));
    }
}

}  // namespace op4
