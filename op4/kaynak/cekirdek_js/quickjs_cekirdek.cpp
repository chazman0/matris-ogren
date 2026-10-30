// op4 model çekirdeği — QuickJS-ng cephesinin C++ yüzü (sözleşme S11; MIMARI §9.3; kabul B5). Uygulayan: B.
//
// Her yöntem op4/js/op4_kopru.js'teki aynı adlı işlevi çağırır (o da Op4Cekirdek cephesini). Küçük dönüşler JSON metnidir
// (nlohmann); sahne ve öznitelik tablosu tipli dizilerden okunur: ArrayBuffer belleği serileştirilmeden doğrudan
// SahneAnlik / OznitelikTablosu alanlarına yazılır (tek geçiş). Model her değiştiğinde (sahne sürümü artınca) yeni değişmez
// anlıklar üretilir; Sahne(), Oznitelikler(), Ozet(), GeriAlBilgisi() JS'e girmez.
#include <cstdio>
#include <cstring>
#include <memory>
#include <utility>

#include <nlohmann/json.hpp>

#include "cekirdek/model_cekirdegi.h"
#include "cekirdek_js/js_ortami.h"
#include "cekirdek_js/js_ortami_ic.h"

namespace op4 {
namespace {

using nlohmann::json;
using js::Deger;
using js::TipliGorunum;

template <class T>
T Al(const TipliGorunum& g, size_t i) {
    T v;
    std::memcpy(&v, g.veri + i * sizeof(T), sizeof(T));
    return v;
}

json Ayristir(const std::string& s) {
    json j = json::parse(s, nullptr, false);
    return j.is_discarded() ? json::object() : j;
}

std::string Dize(const json& j, const char* ad) {
    const auto i = j.find(ad);
    return i != j.end() && i->is_string() ? i->get<std::string>() : std::string();
}
double Sayi(const json& j, const char* ad, double v = 0) {
    const auto i = j.find(ad);
    return i != j.end() && i->is_number() ? i->get<double>() : v;
}
bool Evet(const json& j, const char* ad) {
    const auto i = j.find(ad);
    return i != j.end() && i->is_boolean() && i->get<bool>();
}
std::vector<std::string> Dizeler(const json& j, const char* ad) {
    std::vector<std::string> l;
    const auto i = j.find(ad);
    if (i != j.end() && i->is_array())
        for (const json& x : *i) l.push_back(x.is_string() ? x.get<std::string>() : x.dump());
    return l;
}
V3d Nokta(const json& j, const char* ad) {
    const auto i = j.find(ad);
    if (i == j.end() || !i->is_array() || i->size() != 3) return {};
    return {(*i)[0].get<double>(), (*i)[1].get<double>(), (*i)[2].get<double>()};
}
ElemanKimligi KimlikJson(const json& k) {
    ElemanKimligi e;
    if (!k.is_object()) return e;
    if (const auto t = TurKodundan(Dize(k, "tur"))) e.tur = *t;
    e.no = static_cast<uint32_t>(Sayi(k, "no"));
    e.alt = static_cast<uint16_t>(Sayi(k, "alt"));
    return e;
}

ModelOzeti OzetJson(const json& o) {
    ModelOzeti z;
    z.baslik = Dize(o, "baslik");
    z.surum = static_cast<int>(Sayi(o, "surum", 3));
    z.sistem = Dize(o, "sistem");
    z.dugum = static_cast<size_t>(Sayi(o, "dugum"));
    z.cubuk = static_cast<size_t>(Sayi(o, "cubuk"));
    z.panel = static_cast<size_t>(Sayi(o, "panel"));
    z.kat = static_cast<size_t>(Sayi(o, "kat"));
    z.aks = static_cast<size_t>(Sayi(o, "aks"));
    z.bos = !o.contains("bos") || Evet(o, "bos");
    return z;
}

OznitelikTuru OznitelikTuruAdi(const std::string& t) {
    if (t == "metin") return OznitelikTuru::Metin;
    if (t == "enum") return OznitelikTuru::Enum;
    if (t == "bool") return OznitelikTuru::Bool;
    if (t == "liste") return OznitelikTuru::Liste;
    return OznitelikTuru::Sayi;
}

class QuickJsCekirdek final : public ModelCekirdegi {
public:
    explicit QuickJsCekirdek(const CekirdekAyari& a) : ayar_(a), ortam_(OrtamAyari(a)) {}

    bool Kur(std::string& hata) {
        if (!ortam_.Kur(hata)) return false;
        std::string r;
        const json kur = {{"geriAlAdim", ayar_.geriAlAdim}, {"geriAlMb", ayar_.geriAlMb}};
        if (!ortam_.CagirMetin("Op4Kopru.kur", {kur.dump()}, r, hata)) return false;
        const json j = Ayristir(r);
        islemler_ = Dizeler(j, "islemler");
        Gunluk("Model çekirdeği (QuickJS-ng " OP4_QUICKJS_SURUM ") kuruldu: " + std::to_string(ortam_.YuklenenDosyalar().size()) +
               " JS dosyası, " + std::to_string(ortam_.YuklenenBayt() / 1024) + " KB.");
        char olcum[160];
        std::snprintf(olcum, sizeof(olcum), "OP4OLCUM cekirdek_derleme_ms=%.1f dosya=%zu bayt=%zu", ortam_.DerlemeMs(),
                      ortam_.YuklenenDosyalar().size(), ortam_.YuklenenBayt());
        Gunluk(olcum);
        Yenile();
        return sahne_ != nullptr;
    }

    // ---- yaşam döngüsü ---------------------------------------------------------------------------------------------
    YuklemeSonucu YeniBos(std::string_view baslik) override {
        return YuklemeOku(Cagir("Op4Kopru.yeniBos", {std::string(baslik.empty() ? std::string_view("Adsız 1") : baslik)}));
    }
    YuklemeSonucu Yukle(std::string_view binaMetni, std::string_view kaynak) override {
        return YuklemeOku(Cagir("Op4Kopru.yukle", {std::string(binaMetni), std::string(kaynak)}));
    }

    // ---- düzenleme -------------------------------------------------------------------------------------------------
    IslemRaporu Uygula(std::string_view islem, const JsonMetni& parametreler) override {
        const std::string p = parametreler.empty() ? std::string("{}") : parametreler;
        return RaporCagir("Op4Kopru.uygula", {std::string(islem), p}, islem);
    }
    IslemRaporu GeriAl() override { return RaporCagir("Op4Kopru.geriAl", {}, "geriAl"); }
    IslemRaporu Yinele() override { return RaporCagir("Op4Kopru.yinele", {}, "yinele"); }
    GeriAlDurumu GeriAlBilgisi() const override { return geriAl_; }
    std::vector<std::string> IslemAdlari() const override { return islemler_; }

    // ---- okuma -----------------------------------------------------------------------------------------------------
    SahnePtr Sahne() const override { return sahne_ ? sahne_ : BosSahne(); }
    OznitelikPtr Oznitelikler() const override { return oznitelik_ ? oznitelik_ : BosOznitelikTablosu(); }
    uint64_t SahneSurumu() const override { return sahneSurumu_; }
    ModelOzeti Ozet() const override { return ozet_; }

    DenetimSonucu Denetle() override {
        DenetimSonucu d;
        std::string r, hata;
        if (!ortam_.CagirMetin("Op4Kopru.denetle", {}, r, hata)) {
            IcHata("denetle", hata);
            d.gecerli = false;
            d.uyarilar.push_back("İç hata: " + IlkSatir(hata));
            return d;
        }
        const json j = Ayristir(r);
        d.gecerli = Evet(j, "gecerli");
        d.uyarilar = Dizeler(j, "uyarilar");
        d.serbestDugum = static_cast<size_t>(Sayi(j, "serbest_dugum"));
        if (j.contains("eleman_uyarilari") && j["eleman_uyarilari"].is_array())
            for (const json& e : j["eleman_uyarilari"]) d.elemanUyarilari.emplace_back(KimlikJson(e.value("kimlik", json())), Dize(e, "metin"));
        return d;
    }

    std::string Metin() override {
        std::string r, hata;
        if (!ortam_.CagirMetin("Op4Kopru.metin", {}, r, hata)) {
            IcHata("metin", hata);
            return {};
        }
        return r;
    }

    // ---- sonuç ve dışa aktarma -------------------------------------------------------------------------------------
    SonucEslemesi SonucEsle(const JsonMetni& veriOzeti) override {
        SonucEslemesi s;
        std::string r, hata;
        if (!ortam_.CagirMetin("Op4Kopru.sonucEsle", {veriOzeti}, r, hata)) {
            IcHata("sonucEsle", hata);
            s.hata = "İç hata: " + IlkSatir(hata);
            return s;
        }
        const json j = Ayristir(r);
        s.basarili = Evet(j, "basarili");
        s.hata = Dize(j, "hata");
        s.uyarilar = Dizeler(j, "uyarilar");
        if (j.contains("elemanlar") && j["elemanlar"].is_array())
            for (const json& e : j["elemanlar"]) {
                ElemanSonucu x;
                x.kimlik = KimlikJson(e.value("kimlik", json()));
                x.dc = Sayi(e, "dc", -1);
                x.belirleyen = Dize(e, "belirleyen");
                x.kombinasyon = Dize(e, "kombinasyon");
                x.tasarimSatiri = static_cast<int>(Sayi(e, "tasarim_satiri", -1));
                s.elemanlar.push_back(std::move(x));
            }
        return s;
    }

    IfcSonucu IfcDisari(const JsonMetni& secenek, const JsonMetni& veri) override {
        IfcSonucu s;
        std::string hata;
        JSContext* c = js::Baglam(ortam_);
        Deger r = js::Cagir(ortam_, "Op4Kopru.ifcDisari", {secenek.empty() ? std::string_view("{}") : std::string_view(secenek),
                                                          std::string_view(veri)}, hata);
        if (r.Istisna()) {
            IcHata("ifcDisari", hata);
            s.hata = "İç hata: " + IlkSatir(hata);
            return s;
        }
        const json j = Ayristir(js::Metin(c, r.Ozellik("json").v()));
        s.basarili = Evet(j, "basarili");
        s.hata = Dize(j, "hata");
        s.dosyaAdi = Dize(j, "dosya_adi");
        s.uyarilar = Dizeler(j, "uyarilar");
        s.metin = js::Metin(c, r.Ozellik("metin").v());
        return s;
    }

private:
    static JsOrtamiAyari OrtamAyari(const CekirdekAyari& a) {
        JsOrtamiAyari o;
        o.jsDizini = a.jsDizini;
        o.deterministikSaat = a.deterministikSaat;
        o.gunluk = a.gunluk;
        return o;
    }
    static std::string IlkSatir(const std::string& s) { return s.substr(0, s.find('\n')); }

    void Gunluk(const std::string& s) const {
        if (ayar_.gunluk) ayar_.gunluk(s);
    }
    void IcHata(const char* nerede, const std::string& hata) const { Gunluk(std::string("HATA: model çekirdeği (") + nerede + "): " + hata); }

    Deger Cagir(const char* yol, const std::vector<std::string>& arg) {
        std::vector<std::string_view> a(arg.begin(), arg.end());
        sonHata_.clear();
        Deger r = js::Cagir(ortam_, yol, a, sonHata_);
        if (r.Istisna()) IcHata(yol, sonHata_);
        return r;
    }

    YuklemeSonucu YuklemeOku(Deger r) {
        YuklemeSonucu y;
        if (r.Istisna()) {
            y.hata = "İç hata: " + IlkSatir(sonHata_);
            return y;
        }
        const json j = Ayristir(js::Metin(js::Baglam(ortam_), r.v()));
        y.basarili = Evet(j, "basarili");
        y.hata = Dize(j, "hata");
        y.uyarilar = Dizeler(j, "uyarilar");
        if (j.contains("ozet")) y.ozet = OzetJson(j["ozet"]);
        Yenile();
        if (y.basarili) y.ozet = ozet_;
        return y;
    }

    IslemRaporu RaporCagir(const char* yol, const std::vector<std::string>& arg, std::string_view islem) {
        IslemRaporu rp;
        rp.islem = std::string(islem);
        Deger r = Cagir(yol, arg);
        if (r.Istisna()) {
            rp.hata = "İç hata: " + IlkSatir(sonHata_);
            rp.sahneSurumu = sahneSurumu_;
            Yenile();
            return rp;
        }
        JSContext* c = js::Baglam(ortam_);
        const json j = Ayristir(js::Metin(c, r.Ozellik("json").v()));
        rp.islem = Dize(j, "islem").empty() ? rp.islem : Dize(j, "islem");
        rp.basarili = Evet(j, "basarili");
        rp.hata = Dize(j, "hata");
        rp.uyarilar = Dizeler(j, "uyarilar");
        rp.icerikDegisti = Evet(j, "icerik_degisti");
        if (j.contains("gecis_onayi") && j["gecis_onayi"].is_object()) rp.gecisOnayi = GecisOnayi{Dize(j["gecis_onayi"], "metin")};
        std::string hata;
        Anahtarlar(c, r.v(), "eklenen", rp.eklenen, hata);
        Anahtarlar(c, r.v(), "silinen", rp.silinen, hata);
        Anahtarlar(c, r.v(), "degisen", rp.degisen, hata);
        if (!hata.empty()) IcHata(yol, hata);
        Yenile();
        rp.sahneSurumu = sahneSurumu_;
        return rp;
    }

    static void Anahtarlar(JSContext* c, JSValueConst r, const char* ad, std::vector<ElemanKimligi>& l, std::string& hata) {
        TipliGorunum g;
        if (!js::TipliDizi(c, r, ad, JS_TYPED_ARRAY_FLOAT64, g, hata)) return;
        l.reserve(g.adet);
        for (size_t i = 0; i < g.adet; ++i) l.push_back(ElemanKimligi::AnahtardanKur(static_cast<uint64_t>(Al<double>(g, i))));
    }

    // Durum (geri al, özet, sahne sürümü) ve gerekirse yeni sahne / öznitelik anlıkları.
    void Yenile() {
        std::string r, hata;
        if (!ortam_.CagirMetin("Op4Kopru.durum", {}, r, hata)) {
            IcHata("durum", hata);
            return;
        }
        const json j = Ayristir(r);
        const json g = j.value("geri_al", json::object());
        geriAl_.geriAlinabilir = Evet(g, "geri_alinabilir");
        geriAl_.yinelenebilir = Evet(g, "yinelenebilir");
        geriAl_.geriAlAdi = Dize(g, "geri_al_adi");
        geriAl_.yineleAdi = Dize(g, "yinele_adi");
        geriAl_.adim = static_cast<size_t>(Sayi(g, "adim"));
        geriAl_.yineAdim = static_cast<size_t>(Sayi(g, "yine_adim"));
        ozet_ = OzetJson(j.value("ozet", json::object()));
        const auto surum = static_cast<uint64_t>(Sayi(j, "sahne_surumu"));
        if (sahne_ && surum == sahneSurumu_) return;
        SahnePtr s = SahneOku(hata);
        if (!s) {
            IcHata("sahne", hata);
            return;
        }
        OznitelikPtr t = OznitelikOku(s->surum, hata);
        if (!t) {
            IcHata("oznitelikler", hata);
            return;
        }
        sahne_ = std::move(s);
        oznitelik_ = std::move(t);
        sahneSurumu_ = surum;
    }

    SahnePtr SahneOku(std::string& hata) {
        Deger r = js::Cagir(ortam_, "Op4Kopru.sahne", {}, hata);
        if (r.Istisna()) return nullptr;
        JSContext* c = js::Baglam(ortam_);
        auto s = std::make_shared<SahneAnlik>();
        const json b = Ayristir(js::Metin(c, r.Ozellik("bilgi").v()));
        s->surum = static_cast<uint64_t>(Sayi(b, "sahne_surumu"));
        s->modelSurumu = static_cast<int>(Sayi(b, "model_surumu", 3));
        s->baslik = Dize(b, "baslik");
        s->sistem = Dize(b, "sistem");
        for (const json& v : b.value("seviyeler", json::array()))
            s->seviyeler.push_back({Dize(v, "ad"), Sayi(v, "z"), static_cast<int>(Sayi(v, "kat", -1))});
        for (const json& a : b.value("akslar", json::array())) {
            SahneAksi x;
            x.kimlik = KimlikJson(a.value("kimlik", json()));
            x.ad = Dize(a, "ad");
            x.sistem = Dize(a, "sistem");
            x.eksen = static_cast<uint8_t>(Sayi(a, "eksen"));
            x.bas = Nokta(a, "bas");
            x.son = Nokta(a, "son");
            x.balon = Nokta(a, "balon");
            s->akslar.push_back(std::move(x));
        }
        for (const json& k : b.value("kesitler", json::array())) {
            SahneKesiti x;
            x.ad = Dize(k, "ad");
            x.profil = Dize(k, "profil");
            x.tur = static_cast<KesitTuru>(static_cast<uint8_t>(Sayi(k, "tur")));
            x.malzeme = Dize(k, "malzeme");
            x.h = Sayi(k, "h");
            x.b = Sayi(k, "b");
            x.tw = Sayi(k, "tw");
            x.tf = Sayi(k, "tf");
            x.r = Sayi(k, "r");
            s->kesitler.push_back(std::move(x));
        }
        s->gruplar = Dizeler(b, "gruplar");
        s->malzemeler = Dizeler(b, "malzemeler");

        // düğümler
        {
            Deger d = r.Ozellik("dugumler");
            TipliGorunum no, xyz, tur, bay;
            if (!js::TipliDizi(c, d.v(), "no", JS_TYPED_ARRAY_UINT32, no, hata) ||
                !js::TipliDizi(c, d.v(), "xyz", JS_TYPED_ARRAY_FLOAT64, xyz, hata) ||
                !js::TipliDizi(c, d.v(), "tur", JS_TYPED_ARRAY_UINT8, tur, hata) ||
                !js::TipliDizi(c, d.v(), "bayrak", JS_TYPED_ARRAY_UINT8, bay, hata))
                return nullptr;
            const size_t n = no.adet;
            if (xyz.adet != 3 * n || tur.adet != n || bay.adet != n) return Bozuk(hata, "dugumler");
            s->dugumler.resize(n);
            for (size_t i = 0; i < n; ++i) {
                SahneDugumu& x = s->dugumler[i];
                x.no = Al<uint32_t>(no, i);
                x.p = {Al<double>(xyz, 3 * i), Al<double>(xyz, 3 * i + 1), Al<double>(xyz, 3 * i + 2)};
                x.tur = static_cast<DugumTuru>(Al<uint8_t>(tur, i));
                x.bayrak = Al<uint8_t>(bay, i);
            }
        }
        const size_t nd = s->dugumler.size();
        // çubuklar
        {
            Deger d = r.Ozellik("cubuklar");
            TipliGorunum no, ci, cj, tur, bay, ser, kes, grp, ure, aci, yy;
            if (!js::TipliDizi(c, d.v(), "no", JS_TYPED_ARRAY_UINT32, no, hata) ||
                !js::TipliDizi(c, d.v(), "i", JS_TYPED_ARRAY_UINT32, ci, hata) ||
                !js::TipliDizi(c, d.v(), "j", JS_TYPED_ARRAY_UINT32, cj, hata) ||
                !js::TipliDizi(c, d.v(), "tur", JS_TYPED_ARRAY_UINT8, tur, hata) ||
                !js::TipliDizi(c, d.v(), "bayrak", JS_TYPED_ARRAY_UINT8, bay, hata) ||
                !js::TipliDizi(c, d.v(), "serbestlik", JS_TYPED_ARRAY_UINT16, ser, hata) ||
                !js::TipliDizi(c, d.v(), "kesit", JS_TYPED_ARRAY_UINT32, kes, hata) ||
                !js::TipliDizi(c, d.v(), "grup", JS_TYPED_ARRAY_UINT32, grp, hata) ||
                !js::TipliDizi(c, d.v(), "uretec", JS_TYPED_ARRAY_UINT32, ure, hata) ||
                !js::TipliDizi(c, d.v(), "aci", JS_TYPED_ARRAY_FLOAT64, aci, hata) ||
                !js::TipliDizi(c, d.v(), "y_yerel", JS_TYPED_ARRAY_FLOAT64, yy, hata))
                return nullptr;
            const size_t n = no.adet;
            for (const TipliGorunum* g : {&ci, &cj, &tur, &bay, &ser, &kes, &grp, &ure, &aci})
                if (g->adet != n) return Bozuk(hata, "cubuklar");
            if (yy.adet != 3 * n) return Bozuk(hata, "cubuklar.y_yerel");
            s->cubuklar.resize(n);
            for (size_t i = 0; i < n; ++i) {
                SahneCubugu& x = s->cubuklar[i];
                x.no = Al<uint32_t>(no, i);
                x.i = Al<uint32_t>(ci, i);
                x.j = Al<uint32_t>(cj, i);
                if (x.i >= nd || x.j >= nd) return Bozuk(hata, "cubuklar.i/j");
                x.tur = static_cast<CubukTuru>(Al<uint8_t>(tur, i));
                x.bayrak = Al<uint8_t>(bay, i);
                x.serbestlik = Al<uint16_t>(ser, i);
                x.kesit = Al<uint32_t>(kes, i);
                x.grup = Al<uint32_t>(grp, i);
                x.uretec = Al<uint32_t>(ure, i);
                x.aci = Al<double>(aci, i);
                x.yYerel = {Al<double>(yy, 3 * i), Al<double>(yy, 3 * i + 1), Al<double>(yy, 3 * i + 2)};
            }
        }
        // paneller
        {
            Deger d = r.Ozellik("paneller");
            TipliGorunum no, bas, say, kose, tur, bay, kal;
            if (!js::TipliDizi(c, d.v(), "no", JS_TYPED_ARRAY_UINT32, no, hata) ||
                !js::TipliDizi(c, d.v(), "kose_bas", JS_TYPED_ARRAY_UINT32, bas, hata) ||
                !js::TipliDizi(c, d.v(), "kose_sayisi", JS_TYPED_ARRAY_UINT32, say, hata) ||
                !js::TipliDizi(c, d.v(), "kose", JS_TYPED_ARRAY_UINT32, kose, hata) ||
                !js::TipliDizi(c, d.v(), "tur", JS_TYPED_ARRAY_UINT8, tur, hata) ||
                !js::TipliDizi(c, d.v(), "bayrak", JS_TYPED_ARRAY_UINT8, bay, hata) ||
                !js::TipliDizi(c, d.v(), "kalinlik", JS_TYPED_ARRAY_FLOAT64, kal, hata))
                return nullptr;
            const size_t n = no.adet;
            for (const TipliGorunum* g : {&bas, &say, &tur, &bay, &kal})
                if (g->adet != n) return Bozuk(hata, "paneller");
            s->paneller.resize(n);
            for (size_t i = 0; i < n; ++i) {
                SahnePaneli& x = s->paneller[i];
                x.no = Al<uint32_t>(no, i);
                x.koseBas = Al<uint32_t>(bas, i);
                x.koseSayisi = Al<uint32_t>(say, i);
                if (size_t(x.koseBas) + x.koseSayisi > kose.adet) return Bozuk(hata, "paneller.kose");
                x.tur = static_cast<PanelTuru>(Al<uint8_t>(tur, i));
                x.bayrak = Al<uint8_t>(bay, i);
                x.kalinlik = Al<double>(kal, i);
            }
            s->panelKoseleri.resize(kose.adet);
            for (size_t i = 0; i < kose.adet; ++i) {
                s->panelKoseleri[i] = Al<uint32_t>(kose, i);
                if (s->panelKoseleri[i] >= nd) return Bozuk(hata, "paneller.kose");
            }
        }
        // mesnetler
        {
            Deger d = r.Ozellik("mesnetler");
            TipliGorunum dg, mk, tur;
            if (!js::TipliDizi(c, d.v(), "dugum", JS_TYPED_ARRAY_UINT32, dg, hata) ||
                !js::TipliDizi(c, d.v(), "maske", JS_TYPED_ARRAY_UINT8, mk, hata) ||
                !js::TipliDizi(c, d.v(), "tur", JS_TYPED_ARRAY_UINT8, tur, hata))
                return nullptr;
            if (mk.adet != dg.adet || tur.adet != dg.adet) return Bozuk(hata, "mesnetler");
            s->mesnetler.resize(dg.adet);
            for (size_t i = 0; i < dg.adet; ++i) {
                s->mesnetler[i].dugum = Al<uint32_t>(dg, i);
                if (s->mesnetler[i].dugum >= nd) return Bozuk(hata, "mesnetler.dugum");
                s->mesnetler[i].maske = Al<uint8_t>(mk, i);
                s->mesnetler[i].tur = static_cast<MesnetTuru>(Al<uint8_t>(tur, i));
            }
        }
        for (const json& t : b.value("temeller", json::array())) {
            SahneTemeli x;
            x.kimlik = KimlikJson(t.value("kimlik", json()));
            x.dugum = static_cast<uint32_t>(Sayi(t, "dugum", SAHNE_YOK));
            if (x.dugum != SAHNE_YOK && x.dugum >= nd) return Bozuk(hata, "temeller.dugum");
            x.tur = static_cast<TemelTuru>(static_cast<uint8_t>(Sayi(t, "tur")));
            x.B = Sayi(t, "B");
            x.L = Sayi(t, "L");
            x.h = Sayi(t, "h");
            s->temeller.push_back(std::move(x));
        }
        s->DizinleriKur();
        return s;
    }

    OznitelikPtr OznitelikOku(uint64_t surum, std::string& hata) {
        Deger r = js::Cagir(ortam_, "Op4Kopru.oznitelik", {}, hata);
        if (r.Istisna()) return nullptr;
        JSContext* c = js::Baglam(ortam_);
        auto t = std::make_shared<OznitelikTablosu>();
        TipliGorunum tur, no, alt;
        if (!js::TipliDizi(c, r.v(), "satir_tur", JS_TYPED_ARRAY_UINT8, tur, hata) ||
            !js::TipliDizi(c, r.v(), "satir_no", JS_TYPED_ARRAY_UINT32, no, hata) ||
            !js::TipliDizi(c, r.v(), "satir_alt", JS_TYPED_ARRAY_UINT16, alt, hata))
            return nullptr;
        const size_t n = no.adet;
        if (tur.adet != n || alt.adet != n) return Bozuk(hata, "satirlar");
        t->satirlar.resize(n);
        for (size_t i = 0; i < n; ++i)
            t->satirlar[i] = ElemanKimligi{static_cast<ElemanTuru>(Al<uint8_t>(tur, i)), Al<uint16_t>(alt, i), Al<uint32_t>(no, i)};
        Deger sut = r.Ozellik("sutunlar");
        int64_t ns = 0;
        if (JS_GetLength(c, sut.v(), &ns) < 0) {
            hata = js::IstisnaMetni(c);
            return nullptr;
        }
        for (int64_t k = 0; k < ns; ++k) {
            Deger s = sut.Eleman(static_cast<uint32_t>(k));
            OznitelikSutunu x;
            x.id = js::Metin(c, s.Ozellik("id").v());
            x.tur = OznitelikTuruAdi(js::Metin(c, s.Ozellik("tur").v()));
            x.birim = js::Metin(c, s.Ozellik("birim").v());
            if (x.tur == OznitelikTuru::Sayi || x.tur == OznitelikTuru::Bool) {
                TipliGorunum g;
                if (!js::TipliDizi(c, s.v(), "sayi", JS_TYPED_ARRAY_FLOAT64, g, hata) || g.adet != n) return Bozuk(hata, x.id.c_str());
                x.sayi.resize(n);
                if (n) std::memcpy(x.sayi.data(), g.veri, n * sizeof(double));
            } else if (x.tur == OznitelikTuru::Liste) {
                TipliGorunum bas, deger;
                if (!js::TipliDizi(c, s.v(), "liste_bas", JS_TYPED_ARRAY_UINT32, bas, hata) ||
                    !js::TipliDizi(c, s.v(), "liste_deger", JS_TYPED_ARRAY_FLOAT64, deger, hata) || bas.adet != n + 1)
                    return Bozuk(hata, x.id.c_str());
                x.listeBas.resize(bas.adet);
                std::memcpy(x.listeBas.data(), bas.veri, bas.adet * sizeof(uint32_t));
                x.listeDeger.resize(deger.adet);
                if (deger.adet) std::memcpy(x.listeDeger.data(), deger.veri, deger.adet * sizeof(double));
                if (x.listeBas.back() != x.listeDeger.size()) return Bozuk(hata, x.id.c_str());
            } else {
                TipliGorunum kod;
                if (!js::TipliDizi(c, s.v(), "kod", JS_TYPED_ARRAY_UINT32, kod, hata) || kod.adet != n) return Bozuk(hata, x.id.c_str());
                x.kod.resize(n);
                if (n) std::memcpy(x.kod.data(), kod.veri, n * sizeof(uint32_t));
                Deger sz = s.Ozellik("sozluk");
                int64_t m = 0;
                if (JS_GetLength(c, sz.v(), &m) < 0) {
                    hata = js::IstisnaMetni(c);
                    return nullptr;
                }
                x.sozluk.reserve(static_cast<size_t>(m));
                for (int64_t q = 0; q < m; ++q) x.sozluk.push_back(js::Metin(c, sz.Eleman(static_cast<uint32_t>(q)).v()));
                for (const uint32_t v : x.kod)
                    if (v != OZNITELIK_YOK && v >= x.sozluk.size()) return Bozuk(hata, x.id.c_str());
            }
            t->sutunlar.push_back(std::move(x));
        }
        t->sahneSurumu = surum;
        t->DizinleriKur();
        return t;
    }

    static std::nullptr_t Bozuk(std::string& hata, const char* ne) {
        hata = std::string("köprü verisi tutarsız: ") + ne;
        return nullptr;
    }

    CekirdekAyari ayar_;
    JsOrtami ortam_;
    std::vector<std::string> islemler_;
    std::string sonHata_;
    SahnePtr sahne_;
    OznitelikPtr oznitelik_;
    uint64_t sahneSurumu_ = 0;
    ModelOzeti ozet_;
    GeriAlDurumu geriAl_;
};

}  // namespace

std::unique_ptr<ModelCekirdegi> ModelCekirdegiOlustur(const CekirdekAyari& ayar, std::string& hata) {
    auto c = std::make_unique<QuickJsCekirdek>(ayar);
    if (!c->Kur(hata)) {
        if (hata.empty()) hata = "model çekirdeği ilk sahneyi üretemedi";
        return nullptr;
    }
    return c;
}

}  // namespace op4
