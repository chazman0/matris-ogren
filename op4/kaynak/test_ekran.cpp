// op4 — ekran test kipleri (C): --test-ekran (WARP ekran dışı kare → PNG), --test-acilis (açılış ekranı → PNG),
// --senaryo (TASLAK) ve ortak ImGui / hata ayıklama katmanı yardımcıları.
#include <windows.h>

#include <cmath>
#include <cstdlib>
#include <string>
#include <vector>

#include "acilis.h"
#include "arayuz.h"
#include "geometri.h"
#include "grafik.h"
#include "gunluk.h"
#include "imgui.h"
#include "imgui_impl_dx12.h"
#include "resim.h"
#include "test_kipleri.h"

namespace op4 {

void ImGuiBaglamiKur(float olcek, const char* ini) {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = ini;
    io.ConfigFlags |= ImGuiConfigFlags_DockingEnable | ImGuiConfigFlags_NavEnableKeyboard;
    io.ConfigWindowsMoveFromTitleBarOnly = true;
    ArayuzStili(olcek);
    ArayuzYazitipi(olcek);
}

// D3D12 hata ayıklama katmanının varlığı (MIMARI D13): her ekran testinde yoklanır ve günlüğe yazılır.
void HataKatmaniYaz(const Grafik* g) {
    const HataKatmani y = Grafik::HataKatmaniYokla();
    GunlukHam(Bicim("OP4OLCUM hata_katmani=%s hr=0x%08lX", y.var ? "var" : "yok", static_cast<unsigned long>(y.hr)));
    if (!g) return;
    const HataKatmani k = g->HataKatmaniIletileri();
    if (!k.etkin) return;
    GunlukHam(Bicim("OP4OLCUM hata_katmani_iletileri hata=%u uyari=%u bilgi=%u dusen=%llu", k.hata, k.uyari, k.bilgi,
                    k.dusen));
    for (const std::string& o : k.ornekler) Gunluk("  D3D12 %s", o.c_str());
}

int EkranTesti(const Secenekler& s) {
    TestKipi(600);
    Gunluk("--test-ekran: %dx%d, WARP, %s%s", s.g, s.y, s.arayuzsuz ? "arayüzsüz" : "arayüzlü",
           s.hataKatmani ? ", hata ayıklama katmanı istendi" : "");
    double t0 = GecenMs();
    Grafik g;
    g.HataKatmaniIste(s.hataKatmani);
    std::string hata;
    if (!g.Baslat(true, hata)) {
        HataKatmaniYaz(nullptr);
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    double tAygit = GecenMs() - t0;
    Ag ag = OrnekSahne();
    Gunluk("Sahne: %zu köşe, %zu üçgen, %zu kenar çizgisi, %zu çubuk", ag.koseler.size(), ag.indisler.size() / 3,
           ag.kenarlar.size() / 2, ag.eksenler.size() / 2);
    if (!g.SahneYukle(ag, hata) || !g.EkranDisiKur(static_cast<UINT>(s.g), static_cast<UINT>(s.y), hata)) {
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    const float olcek = s.y >= 900 ? 1.5f : (s.y >= 700 ? 1.25f : 1.0f);
    ImGuiBaglamiKur(olcek, nullptr);
    ImGuiIO& io = ImGui::GetIO();
    io.DisplaySize = ImVec2(static_cast<float>(s.g), static_cast<float>(s.y));
    ImGui_ImplDX12_InitInfo ii;
    g.ImGuiBilgisi(ii);
    ImGui_ImplDX12_Init(&ii);

    ArayuzDurumu d;
    d.bagdastirici = g.BagdastiriciAdi();
    d.warp = g.Warp();
    d.ornek = g.OrnekSayisi();
    d.ozellikDuzeyi = g.OzellikDuzeyi();
    d.ucgen = g.UcgenSayisi();
    d.testModu = true;
    KomutYaz(d, "op4 " OP4_SURUM " — ekran testi (WARP)");
    KomutYaz(d, "Sahne: 2 çerçeve, HE340A kolon ve kirişler, IPE300 bağ kirişleri");
    Kamera k;
    k.Sigdir(ag.enKucuk, ag.enBuyuk);

    std::vector<uint8_t> dolu, bos;
    GorusAlani tam{0, 0, static_cast<float>(s.g), static_cast<float>(s.y)};
    // 1) Sağlama: model olmadan ve modelle (arayüzsüz) iki kare; model piksellerinin oranı.
    Ag bosAg;
    {
        double t = GecenMs();
        if (!g.EkranDisiKaresi(k, SahneAyari{}, tam, nullptr, &dolu)) return 2;
        Gunluk("Kare (arayüzsüz, kesit görünümü): %.1f ms", GecenMs() - t);
    }
    // 2) Asıl kare: arayüzle (ImGui yerleşimi ilk karelerde oturur; 3 kare çizilir, sonuncusu kaydedilir).
    std::vector<uint8_t> rgba;
    if (s.arayuzsuz) {
        rgba = dolu;
    } else {
        for (int i = 0; i < 3; ++i) {
            io.DeltaTime = 1.0f / 60.0f;
            ImGui_ImplDX12_NewFrame();
            ImGui::NewFrame();
            ArayuzCiz(d);
            ImGui::Render();
            double t = GecenMs();
            if (!g.EkranDisiKaresi(k, d.sahne, d.gorus, ImGui::GetDrawData(), i == 2 ? &rgba : nullptr)) return 2;
            Gunluk("Kare %d (arayüzlü; sahne alanı %.0f,%.0f %.0fx%.0f): %.1f ms", i + 1, d.gorus.x, d.gorus.y, d.gorus.g,
                   d.gorus.y2, GecenMs() - t);
        }
    }
    // Model olmadan: çubuk görünümü + eksen tamponu boş değil; bu yüzden ayrı bir boş sahne yükle.
    if (!g.SahneYukle(bosAg, hata) || !g.EkranDisiKaresi(k, SahneAyari{}, tam, nullptr, &bos)) return 2;
    size_t fark = 0;
    for (size_t i = 0; i + 3 < dolu.size(); i += 4)
        if (std::abs(dolu[i] - bos[i]) + std::abs(dolu[i + 1] - bos[i + 1]) + std::abs(dolu[i + 2] - bos[i + 2]) > 24) ++fark;
    double oran = 100.0 * static_cast<double>(fark) / (static_cast<double>(dolu.size()) / 4.0);
    Gunluk("Sağlama: model pikselleri %%%.1f", oran);

    std::wstring yol = s.testEkran;
    if (!PngYaz(yol, s.g, s.y, rgba.data(), false, hata)) {
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    ImGui_ImplDX12_Shutdown();
    ImGui::DestroyContext();
    g.GpuBekle();
    Gunluk("Aygıt + boru hatları %.1f ms; toplam %.1f ms; PNG: %s", tAygit, GecenMs() - t0, Utf8(yol).c_str());
    GunlukHam(Bicim("OP4OLCUM senaryo=ekran gen=%d yuk=%d arayuz=%d aygit_ms=%.1f toplam_ms=%.1f model_yuzde=%.1f msaa=%u",
                    s.g, s.y, s.arayuzsuz ? 0 : 1, tAygit, GecenMs() - t0, oran, g.OrnekSayisi()));
    HataKatmaniYaz(&g);
    const HataKatmani katman = g.HataKatmaniIletileri();
    bool tamam = oran > 2.0;
    if (katman.etkin && katman.hata > 0) {
        Gunluk("Hata ayıklama katmanı %u hata iletisi verdi", katman.hata);
        tamam = false;
    }
    Gunluk(tamam ? "EKRAN TESTİ BAŞARILI"
                 : (oran > 2.0 ? "EKRAN TESTİ BAŞARISIZ (hata ayıklama katmanı)" : "EKRAN TESTİ BAŞARISIZ (model görünmüyor)"));
    return tamam ? 0 : 2;
}

int AcilisTesti(const Secenekler& s) {
    TestKipi(120);
    std::string hata;
    if (!AcilisResmi(UygulamaDizini(), L"Sürüm " OP4_SURUM, s.testAcilis, s.olcek, hata)) {
        Gunluk("AÇILIŞ TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    Gunluk("AÇILIŞ TESTİ BAŞARILI: %s", Utf8(s.testAcilis).c_str());
    return 0;
}

int SenaryoCalistir(const Secenekler& s) {
    TestKipi(600);
    // TASLAK (C, F1 iş 1.4): senaryo dosyasındaki adımları (komut, olay, bekle, çek) uygulama içinde yürütür. Uygulanana
    // dek CI'ın senaryo adımı bu çıktıyı "atlandı" sayar (çıkış 0).
    Gunluk("--senaryo %s: yürütücü henüz uygulanmadı (atlandı)", Utf8(s.senaryo).c_str());
    GunlukHam("OP4OLCUM senaryo=" + Utf8(s.senaryo) + " durum=atlandi neden=yurutucu_yok");
    return 0;
}

}  // namespace op4
