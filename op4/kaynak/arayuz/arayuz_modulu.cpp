// op4 — arayüz modülü (C; sözleşme S21, S23). Ana pencere nesnesini (AnaPencere) kurar ve Hizmetler'e bağlar:
//   * Bildirimler (komut satırı çıktısı, tost, ilerleme) — Hizmetler::bildirim,
//   * C'nin komutları (komutlar.json sahip "C": gorunum.*, secim.*, model.hizli_aks, ayarlar.ac, yardim.*, kapsam.*),
//   * C'nin panelleri / ayar sayfaları için S21 kayıtları (görünürlük durumu; çizimi AnaPencere yapar),
//   * gorunum/gorunum.json belge katkısı (kamera, görünüm kipi, ızgara; MIMARI §7.3, kabul C10),
//   * sahneDegisti / modelYuklendi aboneliği (BVH, gezgin, sığdır).
// ImGui bağlamından bağımsızdır: pencere ve DX12 uygulama tarafından (uygulama.cpp) sonra bağlanır.
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
            if (j.contains("kamera")) {
                KameraDurumu d = a->Kamera().d;
                if (KameraJsonOku(j["kamera"].dump(), d)) a->Kamera().d = d;
            }
            if (h.gorunum) {
                if (j.contains("kip") && j["kip"].is_string()) h.gorunum->kip = j["kip"] == "kesit" ? GorunumKipi::Kesit : GorunumKipi::Cubuk;
                if (j.contains("izgara") && j["izgara"].is_boolean()) h.gorunum->izgara = j["izgara"].get<bool>();
                h.gorunum->SigdirYapildi();  // kayıtlı kamera korunur
            }
            if (j.contains("etkin_kat") && j["etkin_kat"].is_number_integer()) a->etkinKat = j["etkin_kat"].get<int>();
        };
        k.sifirla = [a] { a->StandartGorunum(StandartYon::Izometrik); };
        h.belge->KatkiEkle(std::move(k));
    }
}

}  // namespace op4
