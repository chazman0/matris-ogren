// op4 model çekirdeği — GEÇİCİ C++ çekirdeği (TASLAK; sözleşme S11). QuickJS-ng barındırıcısı bağlanana dek
// ModelCekirdegiOlustur bunu döndürür: YeniBos / Yukle / Metin / Ozet çalışır (sahne yalnız başlıklı boş anlık, öznitelik
// tablosu boş), düzenleme işlemleri "henüz bağlanmadı" hatası verir. Uygulayan: B (model-cekirdegi), F1 iş 1.3 — bu
// dosya QuickJS cephesiyle değiştirilir.
#include <memory>

#include <nlohmann/json.hpp>

#include "cekirdek/model_cekirdegi.h"

namespace op4 {
namespace {
using nlohmann::json;

// op4/js/op4_ops.js bosModel ile aynı içerik (MIMARI §13.4); asıl kaynak JS'tir.
json BosModel(std::string_view baslik) {
    return json{
        {"tur", "bina"},
        {"surum", 3},
        {"baslik", baslik.empty() ? std::string("Adsız 1") : std::string(baslik)},
        {"sistem", "celik"},
        {"birim", {{"kuvvet", "kN"}, {"uzunluk", "m"}}},
        {"akslar", {{"x", json::array()}, {"y", json::array()}, {"z", json::array({{{"ad", "±0.00"}, {"konum", 0}, {"kat", 0}}})}}},
        {"katlar", json::array({{{"no", 0}, {"ad", "±0.00"}, {"kot", 0}}})},
        {"malzemeler",
         {{"C30", {{"kutuphane", "C30"}}}, {"B420C", {{"kutuphane", "B420C"}}}, {"S275", {{"kutuphane", "S275"}}},
          {"S355", {{"kutuphane", "S355"}}}}},
        {"kesitler", json::object()},
        {"dugumler", json::array()},
        {"cubuklar", json::array()},
        {"paneller", json::array()},
        {"mesnetler", json::array()},
        {"ek_yukler", json::array()},
        {"uretecler", json::array()},
        {"yuk_durumlari", {{"G", {{"acik", true}}}, {"Q", {{"acik", true}}}}},
        {"deprem", {{"etkin", false}}},
        {"temeller", {{"tip", "tekil"}}},
    };
}

size_t Uzunluk(const json& m, const char* ad) { return m.contains(ad) && m[ad].is_array() ? m[ad].size() : 0; }

class GeciciCekirdek final : public ModelCekirdegi {
public:
    YuklemeSonucu YeniBos(std::string_view baslik) override {
        model_ = BosModel(baslik);
        return Yuklendi({});
    }
    YuklemeSonucu Yukle(std::string_view metin, std::string_view kaynak) override {
        YuklemeSonucu y;
        json m = json::parse(metin, nullptr, false);
        if (m.is_discarded() || !m.is_object()) {
            y.hata = "Bina modeli okunamadı (geçerli JSON değil): " + std::string(kaynak);
            return y;
        }
        if (m.contains("bina") && m["bina"].is_object()) m = m["bina"];  // .matris / bina_sablon yanıtı
        if (!m.contains("tur") || m["tur"] != "bina") {
            y.hata = "Dosya bir bina modeli değil (\"tur\": \"bina\" yok): " + std::string(kaynak);
            return y;
        }
        model_ = std::move(m);
        return Yuklendi({"Geçici çekirdek: model yüklendi ama sahne üretilmiyor (QuickJS çekirdeği F1 iş 1.3)."});
    }
    IslemRaporu Uygula(std::string_view islem, const JsonMetni&) override {
        IslemRaporu r;
        r.islem = std::string(islem);
        r.hata = "Model çekirdeği (QuickJS) henüz bağlanmadı; '" + r.islem + "' çalıştırılamıyor.";
        r.sahneSurumu = surum_;
        return r;
    }
    IslemRaporu GeriAl() override { return Uygula("geriAl", {}); }
    IslemRaporu Yinele() override { return Uygula("yinele", {}); }
    GeriAlDurumu GeriAlBilgisi() const override { return {}; }
    std::vector<std::string> IslemAdlari() const override { return {}; }
    SahnePtr Sahne() const override { return sahne_ ? sahne_ : BosSahne(); }
    OznitelikPtr Oznitelikler() const override { return BosOznitelikTablosu(); }
    uint64_t SahneSurumu() const override { return surum_; }
    ModelOzeti Ozet() const override { return ozet_; }
    DenetimSonucu Denetle() override { return {}; }
    std::string Metin() override { return model_.dump(); }
    SonucEslemesi SonucEsle(const JsonMetni&) override {
        SonucEslemesi s;
        s.hata = "Sonuç eşleme QuickJS çekirdeğini gerektirir (F1 iş 1.3).";
        return s;
    }
    IfcSonucu IfcDisari(const JsonMetni&, const JsonMetni&) override {
        IfcSonucu s;
        s.hata = "IFC dışa aktarma QuickJS çekirdeğini gerektirir (F1 iş 1.3).";
        return s;
    }

private:
    YuklemeSonucu Yuklendi(std::vector<std::string> uyarilar) {
        ++surum_;
        ModelOzeti o;
        o.baslik = model_.value("baslik", std::string());
        o.surum = model_.contains("surum") && model_["surum"].is_number_integer() ? model_["surum"].get<int>() : 1;
        o.sistem = model_.value("sistem", std::string("celik"));
        o.dugum = Uzunluk(model_, "dugumler");
        o.cubuk = Uzunluk(model_, "cubuklar") + Uzunluk(model_, "kolonlar") + Uzunluk(model_, "kirisler");
        o.panel = Uzunluk(model_, "paneller") + Uzunluk(model_, "dosemeler");
        o.kat = Uzunluk(model_, "katlar");
        if (model_.contains("akslar") && model_["akslar"].is_object())
            o.aks = Uzunluk(model_["akslar"], "x") + Uzunluk(model_["akslar"], "y");
        o.bos = o.dugum + o.cubuk + o.panel == 0;
        ozet_ = o;
        auto s = std::make_shared<SahneAnlik>();
        s->surum = surum_;
        s->modelSurumu = o.surum;
        s->baslik = o.baslik;
        s->sistem = o.sistem;
        s->DizinleriKur();
        sahne_ = s;
        YuklemeSonucu y;
        y.basarili = true;
        y.ozet = o;
        y.uyarilar = std::move(uyarilar);
        return y;
    }

    json model_ = BosModel("Adsız 1");
    ModelOzeti ozet_;
    SahnePtr sahne_;
    uint64_t surum_ = 0;
};

}  // namespace

std::unique_ptr<ModelCekirdegi> ModelCekirdegiOlustur(const CekirdekAyari&, std::string&) {
    return std::make_unique<GeciciCekirdek>();
}

}  // namespace op4
