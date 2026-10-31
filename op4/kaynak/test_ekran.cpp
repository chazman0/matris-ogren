// op4 — ekran test kipleri (C): --test-ekran (WARP ekran dışı kare → PNG, Atölye yerleşimi), --test-acilis (açılış ekranı
// kareleri → PNG), --senaryo (betikli komutlar, olaylar, bekle, çek; deterministik saat) ve ortak ImGui / hata ayıklama
// katmanı yardımcıları.
//
//   op4.exe --test-ekran e.png --boyut 1920x1080 [--senaryo bos|ornek|ornek-kati|ayarlar|ayarlar-program|ayarlar-dil]
//           (--senaryo burada değişken adıdır; .json uzantılıysa betik olarak yürütülür ve son kare e.png'ye yazılır)
//   op4.exe --test-acilis a.png [--olcek 2]   → a.png (son kare) + a-0 / a-50 / a-oturma / a-100 ve a-koyu-*.png
//   op4.exe --senaryo s.json [--boyut GxY]    → betik (bkz. SenaryoYurut)
#include <windows.h>

#include <cmath>
#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "acilis.h"
#include "arayuz/ana_pencere.h"
#include "arayuz/ornek_bina.h"
#include "arayuz/stil.h"
#include "arayuz/yazi.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/kabuk.h"
#include "grafik.h"
#include "grafik/sahne_agi.h"
#include "gunluk.h"
#include "imgui.h"
#include "imgui_impl_dx12.h"
#include "platform/dosya_sistemi.h"
#include "resim.h"
#include "test_kipleri.h"

namespace op4 {
namespace {
Yazilar g_yazilar;
}  // namespace

const Yazilar& ArayuzYazilari() { return g_yazilar; }

void ImGuiBaglamiKur(float olcek, const char* ini) {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = ini;
    io.ConfigFlags |= ImGuiConfigFlags_DockingEnable | ImGuiConfigFlags_NavEnableKeyboard;
    io.ConfigWindowsMoveFromTitleBarOnly = true;
    if (!YazilariYukle(io.Fonts, g_yazilar)) Gunluk("Uyarı: gömülü yazı tipleri açılamadı; ImGui yedek yazı tipi kullanılıyor");
    ArayuzStiliUygula(olcek);
}

// D3D12 hata ayıklama katmanının varlığı (MIMARI D13): her ekran testinde yoklanır ve günlüğe yazılır.
void HataKatmaniYaz(const Grafik* g) {
    const HataKatmani y = Grafik::HataKatmaniYokla();
    GunlukHam(Bicim("OP4OLCUM hata_katmani=%s hr=0x%08lX", y.var ? "var" : "yok", static_cast<unsigned long>(y.hr)));
    if (!g) return;
    const HataKatmani k = g->HataKatmaniIletileri();
    if (!k.etkin) return;
    GunlukHam(Bicim("OP4OLCUM hata_katmani_iletileri hata=%u uyari=%u bilgi=%u dusen=%llu", k.hata, k.uyari, k.bilgi, k.dusen));
    for (const std::string& o : k.ornekler) Gunluk("  D3D12 %s", o.c_str());
}

namespace {

// Ekran dışı test ortamı: sözleşme kabuğu (bütün modüller, motorsuz) + WARP + ImGui; kareler deterministik saatle çizilir.
class EkranOrtami {
public:
    ~EkranOrtami() { Kapat(); }

    bool Kur(const Secenekler& s, int g, int y, std::string& hata) {
        g_ = g;
        y_ = y;
        KabukAyari ka;
        const KullaniciDizinleri kd = KullaniciDizinleriniBul(false);
        ka.bilgi.surum = OP4_SURUM;
        ka.bilgi.uygulamaDizini = Utf8(UygulamaDizini());
        ka.bilgi.veriDizini = Utf8(VeriDizini());
        ka.bilgi.ayarDizini = Utf8(YerelVeriDizini()) + "\\test-ayarlar";  // kullanıcının ayarları test görüntüsünü değiştirmesin
        ka.bilgi.yerelDizin = kd.yerel;
        ka.bilgi.testKipi = true;
        ka.ortam.testKipi = true;
        ka.ortam.motorsuz = true;
        ka.ortam.gunluk = [](std::string_view m) { Gunluk("%.*s", static_cast<int>(m.size()), m.data()); };
        ka.moduller = StandartModuller();
        std::string kh;
        if (!kabuk_.Kur(std::move(ka), kh)) Gunluk("Uyarı: %s", kh.c_str());
        ana_ = EtkinAnaPencere();
        if (!ana_) {
            hata = "arayüz modülü kurulmadı";
            return false;
        }
        grafik_.HataKatmaniIste(s.hataKatmani);
        if (!grafik_.Baslat(true, hata) || !grafik_.EkranDisiKur(static_cast<UINT>(g), static_cast<UINT>(y), hata)) return false;
        ImGuiBaglamiKur(1.0f, nullptr);
        imgui_ = true;
        ImGuiIO& io = ImGui::GetIO();
        io.DisplaySize = ImVec2(static_cast<float>(g), static_cast<float>(y));
        ImGui_ImplDX12_InitInfo ii;
        grafik_.ImGuiBilgisi(ii);
        ImGui_ImplDX12_Init(&ii);
        dx12_ = true;
        ana_->YazilariAyarla(ArayuzYazilari());
        ana_->bagdastirici = grafik_.BagdastiriciAdi();
        ana_->warp = grafik_.Warp();
        ana_->msaa = grafik_.OrnekSayisi();
        ana_->bagdastiricilar = Grafik::Bagdastiricilar();
        ana_->testKipi = true;
        ana_->AyarlariUygula();
        return true;
    }

    // Değişken: bos (boş çalışma alanı + Başlangıç paneli), ornek (örnek bina, 6 kiriş seçili, çubuk görünümü),
    // ornek-kati (aynısı ekstrüzyon), ayarlar[-program|-dil] (örnek bina üstünde Ayarlar penceresi).
    void Degisken(const std::string& d) {
        if (d.empty() || d == "bos") {
            ana_->yanPencere = YanPencere::Baslangic;
            return;
        }
        const OrnekBina o = OrnekBinaKur();
        ana_->SahneZorla(o.sahne, o.oznitelik);
        kabuk_.secim.Uygula(o.taslakSecimi, SecimKipi::Yeni);
        ana_->yanPencere = YanPencere::Ozellikler;
        ana_->Bildirim().KomutYaz("KİRİŞ IPE400 · S355 · Kat 2 · Mafsal–Mafsal · kapsam: Benzer katlar");
        ana_->Bildirim().KomutYaz("SEÇ 6 nesne seçildi: Kiriş ×6 · Kat 2");
        if (d == "ornek-kati") kabuk_.gorunum.kip = GorunumKipi::Kesit;
        if (d.rfind("ayarlar", 0) == 0) {
            ana_->ayarlarAcik = true;
            ana_->ayarSayfasi = d == "ayarlar-program" ? 0 : (d == "ayarlar-dil" ? 2 : 1);
        }
    }

    // Bir kare: sahne dokusu önceki karenin görüş alanıyla; rgba != null ise piksel döner.
    bool Kare(std::vector<uint8_t>* rgba) {
        ImGuiIO& io = ImGui::GetIO();
        io.DeltaTime = 1.0f / 60.0f;
        const double simdi = 1000.0 + static_cast<double>(kare_) * (1000.0 / 60.0);  // deterministik saat
        kabuk_.H().KareIsleriniCalistir(simdi);
        ImGui_ImplDX12_NewFrame();
        ImGui::NewFrame();
        const GorusDikdortgeni g0 = ana_->Gorus();
        SahneDokusu d;
        d.kimlik = static_cast<ImTextureID>(grafik_.SahneDokusu());
        d.uvG = grafik_.UvG(g0.g);
        d.uvY = grafik_.UvY(g0.y2);
        ana_->KareCiz(1.0f, d, simdi);
        ImGui::Render();
        SahneAgiGuncelle();
        const GorusDikdortgeni g = ana_->Gorus();
        CizimAyari a;
        a.kati = ana_->KesitGorunumu();
        a.izgara = ana_->IzgaraGorunur();
        a.ust = tema::Etkin().r.sahneUst;
        a.alt = tema::Etkin().r.sahneAlt;
        ++kare_;
        return grafik_.EkranDisiKaresi(ana_->Kamera(), a, GorusAlani{g.x, g.y, g.g, g.y2}, ImGui::GetDrawData(), tema::Etkin().r.zemin, rgba);
    }

    // Görünüm alanında arka plan gradyanından ayrışan piksellerin yüzdesi (model / arayüz öğeleri görünüyor mu).
    double ModelYuzdesi(const std::vector<uint8_t>& rgba) const {
        const GorusDikdortgeni g = ana_->Gorus();
        const tema::Renkler& R = tema::Etkin().r;
        auto kanal = [](uint32_t c, int k) { return static_cast<int>((c >> (8 * k)) & 0xFF); };
        size_t fark = 0, toplam = 0;
        const int x0 = static_cast<int>(g.x), y0 = static_cast<int>(g.y), x1 = static_cast<int>(g.x + g.g), y1 = static_cast<int>(g.y + g.y2);
        for (int y = std::max(0, y0); y < std::min(y_, y1); y += 2) {
            const float t = static_cast<float>(y - y0) / std::max(1.0f, g.y2);
            int arka[3];
            for (int k = 0; k < 3; ++k)
                arka[k] = static_cast<int>(static_cast<float>(kanal(R.sahneUst, k)) + static_cast<float>(kanal(R.sahneAlt, k) - kanal(R.sahneUst, k)) * t);
            for (int x = std::max(0, x0); x < std::min(g_, x1); x += 2) {
                const uint8_t* p = &rgba[(static_cast<size_t>(y) * g_ + x) * 4];
                ++toplam;
                if (std::abs(p[0] - arka[0]) + std::abs(p[1] - arka[1]) + std::abs(p[2] - arka[2]) > 36) ++fark;
            }
        }
        return toplam ? 100.0 * static_cast<double>(fark) / static_cast<double>(toplam) : 0.0;
    }

    void Kapat() {
        if (dx12_) {
            grafik_.GpuBekle();
            ImGui_ImplDX12_Shutdown();
            dx12_ = false;
        }
        if (imgui_) {
            ImGui::DestroyContext();
            imgui_ = false;
        }
        ana_ = nullptr;
        kabuk_.Kapat();
    }

    Grafik& G() { return grafik_; }
    AnaPencere* Ana() { return ana_; }
    UygulamaKabugu& Kabuk() { return kabuk_; }
    int Genislik() const { return g_; }
    int Yukseklik() const { return y_; }

private:
    void SahneAgiGuncelle() {
        if (!ana_->KesitGorunumu()) {
            sonKati_ = false;
            return;
        }
        const SahnePtr& s = ana_->Sahne();
        if (sonKati_ && s->surum == sonSahne_ && ana_->VurguSurumu() == sonVurgu_) return;
        sonKati_ = true;
        sonSahne_ = s->surum;
        sonVurgu_ = ana_->VurguSurumu();
        SahneAgiAyari a;
        a.secim = &kabuk_.secim.Liste();
        a.uzerinde = ana_->Uzerinde();
        a.yalnizSecili = ana_->YalnizSecili();
        std::string hata;
        if (!grafik_.SahneYukle(SahneAgiKur(*s, a), hata)) Gunluk("HATA: %s", hata.c_str());
    }

    UygulamaKabugu kabuk_;
    Grafik grafik_;
    AnaPencere* ana_ = nullptr;
    bool imgui_ = false, dx12_ = false;
    int g_ = 0, y_ = 0;
    long long kare_ = 0;
    uint64_t sonSahne_ = ~0ull, sonVurgu_ = ~0ull;
    bool sonKati_ = false;
};

// Betik adımları (JSON dizi ya da {"adimlar": [...]}):
//   {"degisken": "ornek"}                         ekran değişkeni (EkranOrtami::Degisken)
//   {"komut": "kolon"}                            komut satırı dizgisi (Türkçe ad, İngilizce takma ad, argümanlar)
//   {"tus": "Ctrl+Q"} / {"yazi": "kiris"}        tuş akoru / karakter girdisi
//   {"fare": [x, y], "tus_fare": "sol", "bas": true|false} | {"tekerlek": 1}   sentetik fare olayları (piksel)
//   {"bekle": 10}                                 kare sayısı (deterministik saat: 60 kare = 1 s)
//   {"cek": "a.png"}                              o anki kareyi PNG'ye yazar
//   {"bekle_kosul": "secim>0", "en_cok": 120}     koşul sağlanana dek (secim>N | komut_bitti) ya da zaman aşımı → hata
int SenaryoYurut(EkranOrtami& o, const nlohmann::json& betik, const std::wstring& varsayilanCikti) {
    const nlohmann::json& adimlar = betik.is_object() && betik.contains("adimlar") ? betik["adimlar"] : betik;
    if (!adimlar.is_array()) {
        Gunluk("SENARYO BAŞARISIZ: adım dizisi yok");
        return 1;
    }
    ImGuiIO& io = ImGui::GetIO();
    int cekim = 0, hataSayisi = 0;
    std::vector<uint8_t> rgba;
    auto akor = [&](const std::string& k, bool bas) {
        ImGuiKey tus = ImGuiKey_None;
        std::string kalan = k;
        std::vector<ImGuiKey> mod;
        for (;;) {
            const size_t a = kalan.find('+');
            const std::string p = kalan.substr(0, a);
            if (p == "Ctrl") mod.push_back(ImGuiMod_Ctrl);
            else if (p == "Shift") mod.push_back(ImGuiMod_Shift);
            else if (p == "Alt") mod.push_back(ImGuiMod_Alt);
            else if (p.size() == 1 && p[0] >= 'A' && p[0] <= 'Z') tus = static_cast<ImGuiKey>(ImGuiKey_A + (p[0] - 'A'));
            else if (p.size() == 1 && p[0] >= '0' && p[0] <= '9') tus = static_cast<ImGuiKey>(ImGuiKey_0 + (p[0] - '0'));
            else if (p.size() >= 2 && p[0] == 'F') tus = static_cast<ImGuiKey>(ImGuiKey_F1 + std::atoi(p.c_str() + 1) - 1);
            else if (p == "Escape" || p == "Esc") tus = ImGuiKey_Escape;
            else if (p == "Enter") tus = ImGuiKey_Enter;
            else if (p == "Tab") tus = ImGuiKey_Tab;
            else if (p == "PageUp") tus = ImGuiKey_PageUp;
            else if (p == "PageDown") tus = ImGuiKey_PageDown;
            else if (p == "Delete") tus = ImGuiKey_Delete;
            else if (p == ",") tus = ImGuiKey_Comma;
            if (a == std::string::npos) break;
            kalan = kalan.substr(a + 1);
        }
        for (ImGuiKey m : mod) io.AddKeyEvent(m, bas);
        if (tus != ImGuiKey_None) io.AddKeyEvent(tus, bas);
    };
    for (const nlohmann::json& a : adimlar) {
        if (!a.is_object()) continue;
        if (a.contains("degisken")) o.Degisken(a["degisken"].get<std::string>());
        if (a.contains("komut") && a["komut"].is_string()) {
            std::string ileti;
            const std::string satir = a["komut"].get<std::string>();
            const bool tamam = o.Kabuk().komutlar.SatirCalistir(satir, o.Kabuk().H(), &ileti);
            Gunluk("senaryo: komut \"%s\" → %s%s%s", satir.c_str(), tamam ? "tamam" : "HATA", ileti.empty() ? "" : " · ", ileti.c_str());
            if (!tamam && !a.value("hata_beklenir", false)) ++hataSayisi;
        }
        if (a.contains("tus") && a["tus"].is_string()) {
            akor(a["tus"].get<std::string>(), true);
            o.Kare(nullptr);
            akor(a["tus"].get<std::string>(), false);
        }
        if (a.contains("yazi") && a["yazi"].is_string()) io.AddInputCharactersUTF8(a["yazi"].get<std::string>().c_str());
        if (a.contains("fare") && a["fare"].is_array() && a["fare"].size() == 2)
            io.AddMousePosEvent(a["fare"][0].get<float>(), a["fare"][1].get<float>());
        if (a.contains("tus_fare")) {
            const std::string t = a["tus_fare"].get<std::string>();
            io.AddMouseButtonEvent(t == "sag" ? ImGuiMouseButton_Right : (t == "orta" ? ImGuiMouseButton_Middle : ImGuiMouseButton_Left),
                                   a.value("bas", true));
        }
        if (a.contains("tekerlek")) io.AddMouseWheelEvent(0.0f, a["tekerlek"].get<float>());
        const int bekle = a.value("bekle", a.contains("cek") ? 3 : 1);
        for (int i = 0; i < bekle; ++i) o.Kare(nullptr);
        if (a.contains("bekle_kosul")) {
            const std::string k = a["bekle_kosul"].get<std::string>();
            const int enCok = a.value("en_cok", 120);
            bool saglandi = false;
            for (int i = 0; i < enCok && !saglandi; ++i) {
                o.Kare(nullptr);
                if (k.rfind("secim>", 0) == 0) saglandi = o.Kabuk().secim.Sayi() > static_cast<size_t>(std::atoi(k.c_str() + 6));
                else saglandi = !o.Ana()->CizimGerekli();
            }
            Gunluk("senaryo: koşul %s %s", k.c_str(), saglandi ? "sağlandı" : "ZAMAN AŞIMI");
            if (!saglandi) ++hataSayisi;
        }
        if (a.contains("cek")) {
            if (!o.Kare(&rgba)) return 2;
            const std::wstring yol = Genis(a["cek"].get<std::string>());
            std::string hata;
            if (!PngYaz(yol, o.Genislik(), o.Yukseklik(), rgba.data(), false, hata)) {
                Gunluk("SENARYO BAŞARISIZ: %s", hata.c_str());
                return 2;
            }
            ++cekim;
            Gunluk("senaryo: çekim %s", Utf8(yol).c_str());
        }
    }
    if (!varsayilanCikti.empty()) {
        std::string hata;
        if (!o.Kare(&rgba) || !PngYaz(varsayilanCikti, o.Genislik(), o.Yukseklik(), rgba.data(), false, hata)) return 2;
        ++cekim;
    }
    GunlukHam(Bicim("OP4OLCUM senaryo=betik adim=%zu cekim=%d hata=%d secim=%zu", adimlar.size(), cekim, hataSayisi,
                    o.Kabuk().secim.Sayi()));
    return hataSayisi == 0 ? 0 : 2;
}

bool JsonOku(const std::wstring& yol, nlohmann::json& j) {
    FILE* f = _wfopen(yol.c_str(), L"rb");
    if (!f) return false;
    std::string metin;
    char tampon[65536];
    size_t n;
    while ((n = std::fread(tampon, 1, sizeof(tampon), f)) > 0) metin.append(tampon, n);
    std::fclose(f);
    j = nlohmann::json::parse(metin, nullptr, false);
    return !j.is_discarded();
}

bool UzantiJson(const std::wstring& y) { return y.size() > 5 && _wcsicmp(y.c_str() + y.size() - 5, L".json") == 0; }

}  // namespace

int EkranTesti(const Secenekler& s) {
    TestKipi(600);
    const bool betik = UzantiJson(s.senaryo);
    const std::string degisken = betik ? std::string() : Utf8(s.senaryo);
    Gunluk("--test-ekran: %dx%d, WARP, değişken %s%s", s.g, s.y, betik ? "betik" : (degisken.empty() ? "bos" : degisken.c_str()),
           s.hataKatmani ? ", hata ayıklama katmanı istendi" : "");
    const double t0 = GecenMs();
    EkranOrtami o;
    std::string hata;
    if (!o.Kur(s, s.g, s.y, hata)) {
        HataKatmaniYaz(nullptr);
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    const double tKur = GecenMs() - t0;
    if (betik) {
        nlohmann::json j;
        if (!JsonOku(s.senaryo, j)) {
            Gunluk("EKRAN TESTİ BAŞARISIZ: %s okunamadı", Utf8(s.senaryo).c_str());
            return 1;
        }
        const int kod = SenaryoYurut(o, j, s.testEkran);
        HataKatmaniYaz(&o.G());
        return kod;
    }
    o.Degisken(degisken);
    // Yerleşim ve yazı atlası ilk karelerde oturur; sahne dokusu bir kare geriden gelir: 6 kare, sonuncusu kaydedilir.
    std::vector<uint8_t> rgba;
    double sonKareMs = 0;
    for (int i = 0; i < 6; ++i) {
        const double t = GecenMs();
        if (!o.Kare(i == 5 ? &rgba : nullptr)) {
            Gunluk("EKRAN TESTİ BAŞARISIZ: kare çizilemedi");
            return 2;
        }
        sonKareMs = GecenMs() - t;
    }
    const double yuzde = o.ModelYuzdesi(rgba);
    if (!PngYaz(s.testEkran, s.g, s.y, rgba.data(), false, hata)) {
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    const ImDrawData* dd = ImGui::GetDrawData();
    const int kose = dd ? dd->TotalVtxCount : 0;
    const bool ornekli = !degisken.empty() && degisken != "bos";
    Gunluk("Ekran: %s, arayüz %d köşe, görünümde ayrışan piksel %%%.1f, son kare %.1f ms", Utf8(s.testEkran).c_str(), kose, yuzde,
           sonKareMs);
    GunlukHam(Bicim("OP4OLCUM senaryo=ekran degisken=%s gen=%d yuk=%d kur_ms=%.1f kare_ms=%.1f arayuz_kose=%d model_yuzde=%.1f msaa=%u",
                    degisken.empty() ? "bos" : degisken.c_str(), s.g, s.y, tKur, sonKareMs, kose, yuzde, o.G().OrnekSayisi()));
    HataKatmaniYaz(&o.G());
    const HataKatmani katman = o.G().HataKatmaniIletileri();
    bool tamam = kose > 2000 && (!ornekli || yuzde > 1.0);
    if (katman.etkin && katman.hata > 0) {
        Gunluk("Hata ayıklama katmanı %u hata iletisi verdi", katman.hata);
        tamam = false;
    }
    Gunluk(tamam ? "EKRAN TESTİ BAŞARILI" : "EKRAN TESTİ BAŞARISIZ");
    return tamam ? 0 : 2;
}

int AcilisTesti(const Secenekler& s) {
    TestKipi(180);
    // a.png → a.png (son kare) + a-0, a-50, a-oturma, a-100 (aciklama.md kare zamanları) ve koyu ikizi a-koyu-*.
    std::wstring kok = s.testAcilis;
    if (kok.size() > 4 && _wcsicmp(kok.c_str() + kok.size() - 4, L".png") == 0) kok.resize(kok.size() - 4);
    const struct {
        const wchar_t* ek;
        double t;
    } kareler[] = {{L"-0", 250}, {L"-50", 1960}, {L"-oturma", 4050}, {L"-100", 4650}};
    const std::string surum = Utf8(L"Sürüm " OP4_SURUM);
    std::string hata;
    int sayi = 0;
    if (!AcilisResmi(UygulamaDizini(), surum, s.testAcilis, s.olcek, 4650, false, hata)) {
        Gunluk("AÇILIŞ TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    ++sayi;
    for (int koyu = 0; koyu < 2; ++koyu)
        for (const auto& k : kareler) {
            const std::wstring yol = kok + (koyu ? L"-koyu" : L"") + k.ek + L".png";
            if (!AcilisResmi(UygulamaDizini(), surum, yol, s.olcek, k.t, koyu != 0, hata)) {
                Gunluk("AÇILIŞ TESTİ BAŞARISIZ: %s: %s", Utf8(yol).c_str(), hata.c_str());
                return 2;
            }
            ++sayi;
        }
    GunlukHam(Bicim("OP4OLCUM senaryo=acilis kare=%d olcek=%.2f", sayi, s.olcek));
    Gunluk("AÇILIŞ TESTİ BAŞARILI: %s (+%d kare)", Utf8(s.testAcilis).c_str(), sayi - 1);
    return 0;
}

int SenaryoCalistir(const Secenekler& s) {
    TestKipi(600);
    nlohmann::json j;
    if (!JsonOku(s.senaryo, j)) {
        Gunluk("SENARYO BAŞARISIZ: %s okunamadı", Utf8(s.senaryo).c_str());
        return 1;
    }
    EkranOrtami o;
    std::string hata;
    const int g = j.is_object() && j.contains("boyut") ? j["boyut"][0].get<int>() : std::max(s.g, 1280);
    const int y = j.is_object() && j.contains("boyut") ? j["boyut"][1].get<int>() : std::max(s.y, 720);
    if (!o.Kur(s, g, y, hata)) {
        Gunluk("SENARYO BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    const int kod = SenaryoYurut(o, j, {});
    Gunluk(kod == 0 ? "SENARYO BAŞARILI" : "SENARYO BAŞARISIZ");
    return kod;
}

}  // namespace op4
