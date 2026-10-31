// op4 — dosya modülü (D; sözleşme S15–S18, S21, S23; F1 iş 1.6). Windows.
//
// Kurulum sırası (DosyaModuluKur; pencere henüz yok):
//   1. Tek örnek: açılış dosyası başka bir op4 penceresinde açıksa o pencere öne getirilir ve kabuktan çıkış istenir
//      (ModulOrtami::cikisIste: kalan modüller kurulmaz, uygulama pencere açmadan çıkar). ModulOrtami::yeniOrnek
//      (--yeni-ornek) ve test kipleri atlar.
//   2. Kullanıcı klasörleri (%LOCALAPPDATA%\Opus Fortis\op4\kurtarma, cokme); çökme dökümü (test kipinde değil).
//   3. Hizmetler::iletisim ← yerel IFileDialog / TaskDialog (test kipinde kabuğun betikli yedeği kalır).
//   4. DosyaIslemleri (platformdan bağımsız akış; cekirdek/proje_islemleri.h): dosya.* komutları, model ve önizleme
//      katkıları, kapatmaOnayi, otomatik kayıt, kurtarma, son dosyalar, ayar kalıcılığı.
//   5. Kancalar (C çizer; renkler C'nin tema belirteçlerinden, dosya/kart_cizimi.h): "Kurtarma" ve "Şablondan yeni" yüzen kartları, "Dosya/Son dosyalar"
//      menü katkısı, Ayarlar › "Dosya ve otomatik kayıt" sayfası.
//   6. Kare işi: pencere başlığı ("op4 — ad •"), tek örnek borusundan gelen "öne gel" isteği.
#include <windows.h>
#include <shellapi.h>

#include <ctime>
#include <memory>
#include <vector>

#include "cekirdek/kabuk.h"
#include "cekirdek/proje_islemleri.h"
#include "cekirdek/proje_zip.h"
#include "dosya/dosya_win.h"
#include "dosya/kart_cizimi.h"
#include "imgui.h"
#include "platform/dosya_sistemi.h"

namespace op4 {
namespace {

std::string DosyaAdi(const std::string& yol) {
    const size_t i = yol.find_last_of("\\/");
    return i == std::string::npos ? yol : yol.substr(i + 1);
}

// "2026-10-31T12:05:00Z" → yerel "31.10.2026 15:05".
std::string YerelZaman(const std::string& iso) {
    std::time_t t = 0;
    if (!IsoZamanCoz(iso, t)) return iso;
    std::tm y{};
    localtime_s(&y, &t);
    char b[32];
    std::strftime(b, sizeof(b), "%d.%m.%Y %H:%M", &y);
    return b;
}

struct DosyaModulu {
    Hizmetler& h;
    ModulOrtami& o;
    std::unique_ptr<DosyaIslemleri> islemler;
    dosya_win::TekOrnekSunucusu sunucu;
    KullaniciDizinleri dizinler;
    std::string bekleyenBaslik, uygulananBaslik;
    std::vector<SablonBilgisi> sablonlar;
    int secilenSablon = -1;

    DosyaModulu(Hizmetler& hh, ModulOrtami& oo) : h(hh), o(oo) {}
    ~DosyaModulu() {
        sunucu.Durdur();
        islemler.reset();  // temiz kapanış: kurtarma kaydı, ayarlar
    }

    HWND Pencere() const { return o.anaPencere ? static_cast<HWND>(o.anaPencere()) : nullptr; }

    void BaslikUygula() {
        HWND w = Pencere();
        if (!w || bekleyenBaslik.empty() || bekleyenBaslik == uygulananBaslik) return;
        SetWindowTextW(w, dosya_win::Genis(bekleyenBaslik).c_str());
        uygulananBaslik = bekleyenBaslik;
    }

    void KareIsi() {
        BaslikUygula();
        if (sunucu.OneGetirIstendi()) {
            if (HWND w = Pencere()) {
                if (IsIconic(w)) ShowWindow(w, SW_RESTORE);
                SetForegroundWindow(w);
            }
            if (h.bildirim) h.bildirim->Tost("Bu proje zaten bu pencerede açık.", TostTuru::Bilgi);
        }
    }

    void Komut(const char* id, const std::string& arguman = {}) {
        std::string hata;
        if (h.komutlar && !h.komutlar->Calistir(id, h, KomutKaynagi::Menu, arguman, &hata) && h.bildirim && !hata.empty())
            h.bildirim->KomutYaz(hata);
    }

    // ---- kartlar -----------------------------------------------------------------------------------------------
    void KurtarmaKarti() {
        using namespace kart;
        if (!islemler->KurtarmaSorusuAcik()) {
            h.arayuz->PanelGoster("kurtarma", false);
            return;
        }
        Baslik("Kaydedilmemiş çalışma bulundu",
               "op4 son oturumda beklenmedik biçimde kapanmış. Otomatik kayıtlardan birini kurtarabilir, silebilir ya da "
               "sonraya bırakabilirsiniz (Dosya › Kurtarma dosyaları).");
        Ayrac();
        const std::vector<KurtarmaKaydi> kayitlar = islemler->Kurtarmalar();
        for (size_t i = 0; i < kayitlar.size(); ++i) {
            const KurtarmaKaydi& k = kayitlar[i];
            ImGui::PushID(static_cast<int>(i));
            ImGui::PushStyleColor(ImGuiCol_Text, R().metin);
            ImGui::TextUnformatted(k.baslik.c_str());
            ImGui::PopStyleColor();
            ImGui::PushStyleColor(ImGuiCol_Text, R().metin3);
            ImGui::TextUnformatted(k.asilYol.empty() ? "Hiç kaydedilmemiş proje" : k.asilYol.c_str());
            ImGui::TextUnformatted(("Otomatik kayıt: " + YerelZaman(k.zaman)).c_str());
            ImGui::PopStyleColor();
            bool bitti = false;
            if (IkincilDugme("Sil")) {
                islemler->KurtarmaSil(i);
                bitti = true;
            }
            ImGui::SameLine();
            if (!bitti && BirincilDugme("Kurtar")) {
                islemler->Kurtar(i);
                bitti = true;
            }
            ImGui::PopID();
            if (bitti) return;  // liste değişti; bir sonraki karede yeniden çizilir
            Ayrac();
        }
        const float g = ImGui::CalcTextSize("Sonra").x + 20.0f * Olcek();
        ImGui::SetCursorPosX(ImGui::GetCursorPosX() + ImGui::GetContentRegionAvail().x - g);
        if (IkincilDugme("Sonra")) islemler->KurtarmaSonra();
    }

    void SablonKarti() {
        using namespace kart;
        if (sablonlar.empty()) sablonlar = islemler->Sablonlar();
        Baslik("Şablondan yeni proje", "Hazır yapı şablonları hesap motoru olmadan açılır; açılan model \"Adsız\" yeni bir "
                                       "projedir.");
        Ayrac();
        for (size_t i = 0; i < sablonlar.size(); ++i) {
            const SablonBilgisi& s = sablonlar[i];
            ImGui::PushID(static_cast<int>(i));
            const bool secili = secilenSablon == static_cast<int>(i);
            ImGui::PushStyleColor(ImGuiCol_Header, R().seciliDolgu);
            ImGui::PushStyleColor(ImGuiCol_HeaderHovered, R().hover);
            ImGui::PushStyleColor(ImGuiCol_Text, R().metin);
            if (ImGui::Selectable(s.baslik.c_str(), secili, ImGuiSelectableFlags_AllowDoubleClick)) {
                secilenSablon = static_cast<int>(i);
                if (ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left)) {
                    ImGui::PopStyleColor(3);
                    ImGui::PopID();
                    Ac();
                    return;
                }
            }
            ImGui::PopStyleColor(3);
            Rozet(s.sistem == "celik" ? "Çelik" : "Betonarme", R().yuzey3, R().metin2);
            ImGui::SameLine();
            Rozet((std::to_string(s.kat) + " kat").c_str(), R().yuzey3, R().metin2);
            if (!s.aks.empty()) {
                ImGui::SameLine();
                Rozet(("Aks " + s.aks).c_str(), R().yuzey3, R().metin2);
            }
            if (secili) {
                ImGui::PushStyleColor(ImGuiCol_Text, R().metin3);
                ImGui::PushTextWrapPos(0.0f);
                ImGui::TextUnformatted(s.aciklama.c_str());
                ImGui::PopTextWrapPos();
                ImGui::PopStyleColor();
            }
            ImGui::PopID();
        }
        Ayrac();
        const float s = Olcek();
        const float g = ImGui::CalcTextSize("Vazgeç").x + ImGui::CalcTextSize("Şablondan yeni").x + 52.0f * s;
        ImGui::SetCursorPosX(ImGui::GetCursorPosX() + ImGui::GetContentRegionAvail().x - g);
        if (IkincilDugme("Vazgeç")) h.arayuz->PanelGoster("sablon_secici", false);
        ImGui::SameLine();
        if (BirincilDugme("Şablondan yeni") && secilenSablon >= 0) Ac();
    }

    void Ac() {
        if (secilenSablon < 0 || static_cast<size_t>(secilenSablon) >= sablonlar.size()) return;
        if (islemler->SablondanYeni(sablonlar[static_cast<size_t>(secilenSablon)].ad))
            h.arayuz->PanelGoster("sablon_secici", false);
    }

    void SonDosyalarMenusu() {
        auto& l = h.ayarlar->dosya.sonDosyalar;
        if (l.empty()) {
            ImGui::MenuItem("(liste boş)", nullptr, false, false);
            return;
        }
        const std::vector<std::string> kopya = l;  // tıklama listeyi değiştirir
        for (size_t i = 0; i < kopya.size(); ++i) {
            const std::string etiket = std::to_string(i + 1) + "  " + DosyaAdi(kopya[i]) + "##" + kopya[i];
            if (ImGui::MenuItem(etiket.c_str())) Komut("dosya.ac", kopya[i]);
            if (ImGui::IsItemHovered()) ImGui::SetTooltip("%s", kopya[i].c_str());
        }
        ImGui::Separator();
        if (ImGui::MenuItem("Listeyi temizle")) l.clear();
    }

    void AyarSayfasi(Ayarlar& a) {
        using namespace kart;
        DosyaAyarlari& d = a.dosya;
        Baslik("Otomatik kayıt", "Kaydedilmemiş değişiklikler kurtarma klasörüne yazılır; beklenmedik kapanıştan sonra "
                                 "açılışta \"Kurtar / Sil / Sonra\" sorulur.");
        ImGui::Checkbox("Otomatik kayıt", &d.otomatikKayit);
        ImGui::BeginDisabled(!d.otomatikKayit);
        ImGui::SliderInt("Aralık (dakika)", &d.otomatikKayitDk, 1, 30);
        ImGui::EndDisabled();
        Ayrac();
        Baslik("Kaydetme");
        ImGui::Checkbox("Kaydederken önceki sürümü .bak olarak sakla", &d.yedekBak);
        Ayrac();
        Baslik("Son dosyalar");
        if (ImGui::SliderInt("Listede en çok", &d.sonDosyaSayisi, 0, 30) &&
            d.sonDosyalar.size() > static_cast<size_t>(d.sonDosyaSayisi))
            d.sonDosyalar.resize(static_cast<size_t>(d.sonDosyaSayisi));
        if (IkincilDugme("Son dosyaları temizle")) d.sonDosyalar.clear();
        Ayrac();
        Baslik("Klasörler", dizinler.kurtarma.c_str());
        if (IkincilDugme("Kurtarma klasörünü aç"))
            ShellExecuteW(nullptr, L"open", dosya_win::Genis(dizinler.kurtarma).c_str(), nullptr, nullptr, SW_SHOWNORMAL);
        ImGui::SameLine();
        if (IkincilDugme("Çökme dökümleri"))
            ShellExecuteW(nullptr, L"open", dosya_win::Genis(dizinler.cokme).c_str(), nullptr, nullptr, SW_SHOWNORMAL);
    }
};

}  // namespace

void DosyaModuluKur(Hizmetler& h, ModulOrtami& o) {
    const std::string acilis = o.acilisDosyasi.empty() ? std::string() : dosya_win::TamYol(o.acilisDosyasi);
    if (!o.testKipi && !o.yeniOrnek && !acilis.empty() && dosya_win::BaskaPenceredeAcikMi(acilis)) {
        if (o.gunluk) o.gunluk("Tek örnek: '" + acilis + "' başka bir op4 penceresinde açık; o pencere öne getirildi.");
        if (o.cikisIste) o.cikisIste(0);  // S23: kabuk kalan modülleri kurmaz, uygulama pencere açmadan çıkar
        return;
    }

    auto m = std::make_shared<DosyaModulu>(h, o);
    DosyaModulu* mp = o.Tut(m);
    mp->dizinler = KullaniciDizinleriniBul(true);
    if (!o.testKipi) dosya_win::CokmeDokumuKur(mp->dizinler.cokme);
    if (!o.testKipi) {
        static std::unique_ptr<IletisimKutulari> yerel;  // süreç boyunca: kapanışta başka modüller de sorabilir
        if (!yerel) yerel = dosya_win::WinIletisimKutulariOlustur(o.anaPencere);
        h.iletisim = yerel.get();
    }

    DosyaIslemleriAyari a;
    a.kurtarmaDizini = mp->dizinler.kurtarma;
    a.acilisDosyasi = acilis;
    if (o.testKipi) {  // senaryolar belirlenimci (MIMARI §6.14)
        a.sabitZaman = "2026-01-01T00:00:00Z";
        a.ifcZamani = "2026-01-01T00:00:00";
    }
    DosyaPlatformu p;
    p.sonBelgeEkle = [](const std::string& yol) { dosya_win::SonBelgeEkle(yol); };
    p.pencereBasligi = [mp](const std::string& b) {
        mp->bekleyenBaslik = b;
        mp->BaslikUygula();
    };
    p.belgeYoluDegisti = [mp, test = o.testKipi](const std::string& yol) {
        if (!test) mp->sunucu.YolAyarla(yol);
    };
    p.kurtarmaGoster = [&h] { h.arayuz->PanelGoster("kurtarma", true); };
    p.sablonSeciciGoster = [&h, mp] {
        mp->secilenSablon = -1;
        h.arayuz->PanelGoster("sablon_secici", true);
    };
    mp->islemler = std::make_unique<DosyaIslemleri>(h, a, p);
    mp->islemler->Kur();

    PanelKaydi kurtarma;
    kurtarma.id = "kurtarma";
    kurtarma.baslik = "Kurtarma";
    kurtarma.yer = PanelYeri::Yuzer;
    kurtarma.varsayilanAcik = false;
    kurtarma.sahip = "D";
    kurtarma.ciz = [mp] { mp->KurtarmaKarti(); };
    h.arayuz->PanelEkle(std::move(kurtarma));
    PanelKaydi sablon;
    sablon.id = "sablon_secici";
    sablon.baslik = "Şablondan yeni";
    sablon.yer = PanelYeri::Yuzer;
    sablon.varsayilanAcik = false;
    sablon.sahip = "D";
    sablon.ciz = [mp] { mp->SablonKarti(); };
    h.arayuz->PanelEkle(std::move(sablon));
    h.arayuz->MenuKatkisiEkle({"Dosya/Son dosyalar", 0, "D", [mp] { mp->SonDosyalarMenusu(); }});
    h.arayuz->AyarSayfasiEkle({"dosya", "Dosya ve otomatik kayıt", 30, "D", [mp](Ayarlar& x) { mp->AyarSayfasi(x); }});
    h.KareIsiEkle("dosya-win", [mp](double) { mp->KareIsi(); });
}

}  // namespace op4
