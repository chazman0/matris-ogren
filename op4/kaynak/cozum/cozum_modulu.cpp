// op4 — çözüm modülü (D; sözleşme S13, S19, S21, S23; F1 iş 1.5). Windows (ImGui çizimi); akışın kendisi
// platformdan bağımsızdır ve Linux'ta sınanır (cekirdek/cozum_akisi.h: F5 eşzamansız bina_coz, iptal, eski işareti,
// D/C boyaması, sonuc/ katkısı, açılışta bina_kimlik eşleştirmesi).
//
// Bu dosya C'nin kancalarına Stüdyo belirteçleriyle çizilen iki öğe ekler:
//   * "Sonuç özeti" paneli (sağ denetçi): durum rozeti (Güncel / Sonuçlar eski), SD, kombinasyon, ΣG, ΣQ, en büyük D/C
//     (eleman, renk), D/C > 1 sayısı, süre; D/C gösterge ölçeği (eşik ve sayılar), "D/C renkleri" anahtarı, "En kritik
//     elemanı seç", uyarılar; çözüm sürerken geçen süre + belirsiz ilerleme + İptal; birincil eylem "Çöz F5".
//   * "cozum" durum çubuğu öğesi: "Çözülüyor… 3,4 s" + İptal, "Sonuçlar eski" rozeti ya da en büyük D/C çipi.
#include <memory>
#include <string>

#include "cekirdek/cozum_akisi.h"
#include "cekirdek/kabuk.h"
#include "cekirdek/sonuc_ek.h"
#include "dosya/studyo_tema.h"
#include "imgui.h"

namespace op4 {
namespace {

struct CozumModulu {
    Hizmetler& h;
    std::unique_ptr<CozumAkisi> akis;
    explicit CozumModulu(Hizmetler& hh) : h(hh) {}

    void Komut(const char* id) {
        std::string hata;
        if (h.komutlar && !h.komutlar->Calistir(id, h, KomutKaynagi::Serit, {}, &hata) && h.bildirim && !hata.empty())
            h.bildirim->KomutYaz(hata);
    }

    void Panel() {
        using namespace studyo;
        const float s = Olcek();
        if (akis->Evre() != CozumEvresi::Bos) {
            Baslik(akis->Evre() == CozumEvresi::Cozuluyor ? "Çözülüyor" : "İptal ediliyor",
                   "Hesap motoru ayrı süreçte çalışıyor; bu sırada modeli gezebilir ve inceleyebilirsiniz.");
            ImGui::PushStyleColor(ImGuiCol_PlotHistogram, ALTIN);
            ImGui::PushStyleColor(ImGuiCol_FrameBg, YUZEY3);
            ImGui::ProgressBar(-1.0f * static_cast<float>(ImGui::GetTime()), ImVec2(-1.0f, 6.0f * s), "");
            ImGui::PopStyleColor(2);
            EtiketDeger("Geçen süre", SureMetni(akis->GecenMs()).c_str());
            if (akis->Evre() == CozumEvresi::Cozuluyor && IkincilDugme("İptal")) Komut("analiz.iptal");
            return;
        }
        if (!h.sonuc->Var()) {
            Baslik("Henüz sonuç yok", "Modeli hesap motoruyla çözün; D/C renkleri ve özet burada görünür.");
            if (!akis->SonHata().empty()) BilgiKutusu(akis->SonHata().c_str());
            const KomutDurumu d = h.komutlar->Durum("analiz.coz", h);
            ImGui::BeginDisabled(!d.kullanilabilir);
            if (BirincilDugme("Çöz   F5")) Komut("analiz.coz");
            ImGui::EndDisabled();
            if (!d.kullanilabilir && !d.neden.empty() && ImGui::IsItemHovered(ImGuiHoveredFlags_AllowWhenDisabled))
                ImGui::SetTooltip("%s", d.neden.c_str());
            return;
        }
        const SonucOzeti& o = h.sonuc->Ozet();
        const bool eski = h.sonuc->Eski();
        Rozet(eski ? "Sonuçlar eski" : "Güncel", eski ? Rgb(0xD9A13B, 48) : Rgb(0x4C9A63, 40), eski ? KAHVE_KOYU : TAMAM);
        if (eski) {
            ImGui::SameLine();
            if (BirincilDugme("Yeniden çöz   F5")) Komut("analiz.coz");
        }
        Ayrac();
        for (const OzetSatiri& r : akis->OzetSatirlari()) {
            if (r.etiket == "Durum") continue;
            EtiketDeger(r.etiket.c_str(), r.deger.c_str(), r.renk ? Rgba(r.renk) : 0);
        }
        Ayrac();
        // D/C gösterge ölçeği (sonuc.h DcRengi; görünümdeki renklerle aynı).
        Baslik("D/C dağılımı", o.elemanlar.empty() ? "Elemanlar modele eşlenemedi; özet yine geçerli." : nullptr);
        const DcDagilimi d = DcDagilimiHesapla(o);
        const struct {
            const char* ad;
            double ornek;
            size_t sayi;
        } siniflar[] = {{"< 0,70", 0.5, d.yesil}, {"0,70 – 0,90", 0.8, d.sari}, {"0,90 – 1,00", 0.95, d.turuncu},
                        {"> 1,00", 1.5, d.kirmizi}, {"tasarım yok", -1, d.yok}};
        for (const auto& c : siniflar) {
            RenkKaresi(Rgba(DcRengi(c.ornek)));
            ImGui::SameLine();
            EtiketDeger(c.ad, std::to_string(c.sayi).c_str(), 0, 130.0f);
        }
        bool renkler = h.gorunum->renkKipi == RenkKipi::Sonuc;
        if (ImGui::Checkbox("D/C renkleri", &renkler)) Komut("analiz.dc_renkleri");
        if (o.enBuyukDcElemani.Gecerli()) {
            ImGui::SameLine();
            if (IkincilDugme("En kritik elemanı seç")) {
                h.secim->Uygula(o.enBuyukDcElemani, SecimKipi::Yeni);
                h.gorunum->CizimIste();
            }
        }
        if (!o.uyarilar.empty()) {
            Ayrac();
            if (ImGui::TreeNode("uyarilar", "Uyarılar (%d)", static_cast<int>(o.uyarilar.size()))) {
                ImGui::PushStyleColor(ImGuiCol_Text, METIN2);
                ImGui::PushTextWrapPos(0.0f);
                for (const std::string& u : o.uyarilar) ImGui::BulletText("%s", u.c_str());
                ImGui::PopTextWrapPos();
                ImGui::PopStyleColor();
                ImGui::TreePop();
            }
        }
    }

    void DurumOgesi() {
        using namespace studyo;
        const std::string m = akis->DurumMetni();
        if (m.empty()) return;
        if (akis->Evre() != CozumEvresi::Bos) {
            ImGui::PushStyleColor(ImGuiCol_Text, KAHVE);
            ImGui::TextUnformatted(m.c_str());
            ImGui::PopStyleColor();
            if (akis->Evre() == CozumEvresi::Cozuluyor) {
                ImGui::SameLine();
                ImGui::PushStyleColor(ImGuiCol_Text, METIN2);
                if (ImGui::SmallButton("İptal")) Komut("analiz.iptal");
                ImGui::PopStyleColor();
            }
            return;
        }
        if (h.sonuc->Eski()) {
            Rozet(m.c_str(), Rgb(0xD9A13B, 48), KAHVE_KOYU);
        } else {
            RenkKaresi(Rgba(DcRengi(h.sonuc->Ozet().enBuyukDc)));
            ImGui::SameLine();
            ImGui::PushStyleColor(ImGuiCol_Text, METIN2);
            ImGui::TextUnformatted(m.c_str());
            ImGui::PopStyleColor();
        }
        if (ImGui::IsItemClicked()) h.arayuz->PanelGoster("sonuc_ozeti", true);
    }
};

}  // namespace

void CozumModuluKur(Hizmetler& h, ModulOrtami& o) {
    auto m = std::make_shared<CozumModulu>(h);
    CozumModulu* mp = o.Tut(m);
    CozumAkisiAyari a;
    if (o.testKipi) a.sabitZaman = "2026-01-01T00:00:00Z";
    a.olcum = o.gunluk;
    mp->akis = std::make_unique<CozumAkisi>(h, a);
    mp->akis->Kur();

    PanelKaydi p;
    p.id = "sonuc_ozeti";
    p.baslik = "Sonuç özeti";
    p.yer = PanelYeri::Sag;
    p.sira = 30;
    p.varsayilanAcik = false;
    p.sahip = "D";
    p.ciz = [mp] { mp->Panel(); };
    h.arayuz->PanelEkle(std::move(p));
    DurumOgesi d;
    d.id = "cozum";
    d.sira = 5;
    d.sagda = true;
    d.sahip = "D";
    d.ciz = [mp] { mp->DurumOgesi(); };
    h.arayuz->DurumOgesiEkle(std::move(d));
}

}  // namespace op4
