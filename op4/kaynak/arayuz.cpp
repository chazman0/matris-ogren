#include "arayuz.h"

#include <windows.h>

#include <cstdio>

#include "imgui.h"
#include "imgui_internal.h"

namespace op4 {
namespace {

bool DosyaVar(const char* yol) {
    DWORD a = GetFileAttributesA(yol);  // etkin kod sayfası UTF-8 (bildirim dosyası)
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

void Satir(const char* ad, const char* deger) {
    ImGui::TableNextRow();
    ImGui::TableSetColumnIndex(0);
    ImGui::TextDisabled("%s", ad);
    ImGui::TableSetColumnIndex(1);
    ImGui::TextUnformatted(deger);
}

void Satirf(const char* ad, const char* bicim, double v) {
    char b[96];
    std::snprintf(b, sizeof(b), bicim, v);
    Satir(ad, b);
}

}  // namespace

void ArayuzStili(float olcek) {
    ImGuiStyle& s = ImGui::GetStyle();
    s = ImGuiStyle();
    ImGui::StyleColorsDark(&s);
    s.WindowRounding = 0.0f;
    s.FrameRounding = 3.0f;
    s.GrabRounding = 3.0f;
    s.TabRounding = 3.0f;
    s.WindowBorderSize = 1.0f;
    s.FramePadding = ImVec2(6, 4);
    s.ItemSpacing = ImVec2(8, 5);
    s.FontSizeBase = 15.0f;
    ImVec4* c = s.Colors;
    const ImVec4 lacivert(0.094f, 0.157f, 0.251f, 1.0f), altin(0.788f, 0.635f, 0.153f, 1.0f);
    c[ImGuiCol_WindowBg] = ImVec4(0.105f, 0.118f, 0.137f, 1.0f);
    c[ImGuiCol_ChildBg] = c[ImGuiCol_WindowBg];
    c[ImGuiCol_PopupBg] = ImVec4(0.12f, 0.135f, 0.16f, 0.98f);
    c[ImGuiCol_MenuBarBg] = ImVec4(0.085f, 0.095f, 0.11f, 1.0f);
    c[ImGuiCol_TitleBg] = lacivert;
    c[ImGuiCol_TitleBgActive] = ImVec4(0.13f, 0.22f, 0.35f, 1.0f);
    c[ImGuiCol_Header] = ImVec4(0.16f, 0.25f, 0.38f, 1.0f);
    c[ImGuiCol_HeaderHovered] = ImVec4(0.21f, 0.32f, 0.48f, 1.0f);
    c[ImGuiCol_HeaderActive] = ImVec4(0.25f, 0.38f, 0.56f, 1.0f);
    c[ImGuiCol_Tab] = lacivert;
    c[ImGuiCol_TabSelected] = ImVec4(0.17f, 0.28f, 0.44f, 1.0f);
    c[ImGuiCol_TabDimmedSelected] = ImVec4(0.14f, 0.22f, 0.34f, 1.0f);
    c[ImGuiCol_CheckMark] = altin;
    c[ImGuiCol_SliderGrab] = altin;
    c[ImGuiCol_DockingPreview] = ImVec4(altin.x, altin.y, altin.z, 0.6f);
    c[ImGuiCol_Separator] = ImVec4(0.22f, 0.25f, 0.30f, 1.0f);
    s.ScaleAllSizes(olcek);
    s.FontScaleDpi = olcek;
}

void ArayuzYazitipi(float /*olcek*/) {
    ImGuiIO& io = ImGui::GetIO();
    io.Fonts->Clear();
    char windows[MAX_PATH] = {};
    GetWindowsDirectoryA(windows, MAX_PATH);
    std::string segoe = std::string(windows) + "\\Fonts\\segoeui.ttf";
    ImFontConfig ic;
    ic.OversampleH = 2;
    if (!DosyaVar(segoe.c_str()) || !io.Fonts->AddFontFromFileTTF(segoe.c_str(), 15.0f, &ic)) io.Fonts->AddFontDefault();
}

void KomutYaz(ArayuzDurumu& d, const std::string& satir) {
    d.komutGecmisi.push_back(satir);
    while (d.komutGecmisi.size() > 200) d.komutGecmisi.pop_front();
}

void ArayuzCiz(ArayuzDurumu& d) {
    ImGuiViewport* vp = ImGui::GetMainViewport();

    // --- ana menü ---------------------------------------------------------------------------------------------
    if (ImGui::BeginMainMenuBar()) {
        if (ImGui::BeginMenu("Dosya")) {
            if (ImGui::MenuItem("Yeni", "Ctrl+N")) d.istek = Istek::Yeni;
            if (ImGui::MenuItem("Aç…", "Ctrl+O")) d.istek = Istek::Ac;
            ImGui::Separator();
            if (ImGui::MenuItem("Kaydet", "Ctrl+S")) d.istek = Istek::Kaydet;
            if (ImGui::MenuItem("Farklı Kaydet…", "Ctrl+Shift+S")) d.istek = Istek::FarkliKaydet;
            ImGui::Separator();
            if (ImGui::MenuItem("Çıkış", "Alt+F4")) d.istek = Istek::Cikis;
            ImGui::EndMenu();
        }
        if (ImGui::BeginMenu("Görünüm")) {
            if (ImGui::MenuItem("Kesit (katı) görünümü", "K", d.sahne.kesitGorunumu)) d.sahne.kesitGorunumu = true;
            if (ImGui::MenuItem("Çubuk görünümü", "K", !d.sahne.kesitGorunumu)) d.sahne.kesitGorunumu = false;
            ImGui::MenuItem("Kenar çizgileri", nullptr, &d.sahne.kenarlar);
            ImGui::MenuItem("Izgara", "G", &d.sahne.izgara);
            ImGui::Separator();
            if (ImGui::MenuItem("Tümünü göster", "F")) d.istek = Istek::Sigdir;
            if (ImGui::MenuItem("Panel yerleşimini sıfırla")) d.istek = Istek::YerlesimiSifirla;
            ImGui::EndMenu();
        }
        if (ImGui::BeginMenu("Yardım")) {
            ImGui::MenuItem("op4 " OP4_SURUM " — Opus Fortis", nullptr, false, false);
            ImGui::MenuItem("Gezinme: sol sürükle = kaydır, Shift+sol = döndür, tekerlek = yakınlaş", nullptr, false, false);
            ImGui::EndMenu();
        }
        ImGui::EndMainMenuBar();
    }
    // Kısayollar (ImGui metin kutusu odaktayken de çalışır).
    if (ImGui::Shortcut(ImGuiMod_Ctrl | ImGuiKey_N, ImGuiInputFlags_RouteGlobal)) d.istek = Istek::Yeni;
    if (ImGui::Shortcut(ImGuiMod_Ctrl | ImGuiKey_O, ImGuiInputFlags_RouteGlobal)) d.istek = Istek::Ac;
    if (ImGui::Shortcut(ImGuiMod_Ctrl | ImGuiKey_S, ImGuiInputFlags_RouteGlobal)) d.istek = Istek::Kaydet;
    if (ImGui::Shortcut(ImGuiMod_Ctrl | ImGuiMod_Shift | ImGuiKey_S, ImGuiInputFlags_RouteGlobal))
        d.istek = Istek::FarkliKaydet;

    // --- durum çubuğu -----------------------------------------------------------------------------------------
    const ImGuiWindowFlags cubukBayrak = ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoSavedSettings | ImGuiWindowFlags_MenuBar;
    if (ImGui::BeginViewportSideBar("##durum", vp, ImGuiDir_Down, ImGui::GetFrameHeight(), cubukBayrak)) {
        if (ImGui::BeginMenuBar()) {
            if (!d.motorBaslatildi)
                ImGui::TextDisabled("Motor: başlatılmadı");
            else if (!d.motor.hazir)
                ImGui::TextUnformatted("Motor: yükleniyor…");
            else if (d.motor.basarili)
                ImGui::Text("Motor: hazır (Python %s)", d.motor.pythonSurumu.substr(0, d.motor.pythonSurumu.find(' ')).c_str());
            else
                ImGui::TextColored(ImVec4(1.0f, 0.45f, 0.4f, 1.0f), "Motor: HATA");
            ImGui::Separator();
            ImGui::Text("DirectX 12 · %s%s · MSAA %u×", d.bagdastirici.c_str(), d.warp ? " (WARP)" : "", d.ornek);
            ImGui::Separator();
            ImGui::Text("%s%s", d.projeAdi.c_str(), d.degisti ? " *" : "");
            if (d.fps > 0) {
                ImGui::Separator();
                ImGui::Text("%.0f kare/s", d.fps);
            }
            ImGui::EndMenuBar();
        }
    }
    ImGui::End();

    // --- yerleştirme alanı ------------------------------------------------------------------------------------
    const ImGuiID alan = ImGui::GetID("op4.Yerlesim");
    if (!d.yerlesimKuruldu || d.istek == Istek::YerlesimiSifirla) {
        d.yerlesimKuruldu = true;
        ImGuiDockNode* dugum = ImGui::DockBuilderGetNode(alan);
        if (!dugum || dugum->IsLeafNode() || d.istek == Istek::YerlesimiSifirla) {
            ImGui::DockBuilderRemoveNode(alan);
            ImGui::DockBuilderAddNode(alan, ImGuiDockNodeFlags_DockSpace);
            ImGui::DockBuilderSetNodeSize(alan, vp->WorkSize);
            ImGuiID kalan = alan;
            ImGuiID sag = ImGui::DockBuilderSplitNode(kalan, ImGuiDir_Right, 0.25f, nullptr, &kalan);
            ImGuiID alt = ImGui::DockBuilderSplitNode(kalan, ImGuiDir_Down, 0.22f, nullptr, &kalan);
            ImGui::DockBuilderDockWindow("Özellikler", sag);
            ImGui::DockBuilderDockWindow("Komut", alt);
            ImGui::DockBuilderFinish(alan);
        }
        if (d.istek == Istek::YerlesimiSifirla) d.istek = Istek::Yok;
    }
    ImGui::DockSpaceOverViewport(alan, vp, ImGuiDockNodeFlags_PassthruCentralNode);
    if (ImGuiDockNode* merkez = ImGui::DockBuilderGetCentralNode(alan)) {
        d.gorus.x = merkez->Pos.x - vp->Pos.x;
        d.gorus.y = merkez->Pos.y - vp->Pos.y;
        d.gorus.g = merkez->Size.x;
        d.gorus.y2 = merkez->Size.y;
    } else {
        d.gorus = {vp->WorkPos.x - vp->Pos.x, vp->WorkPos.y - vp->Pos.y, vp->WorkSize.x, vp->WorkSize.y};
    }

    // --- Özellikler -------------------------------------------------------------------------------------------
    if (ImGui::Begin("Özellikler")) {
        const ImGuiTableFlags tb = ImGuiTableFlags_SizingStretchProp | ImGuiTableFlags_RowBg;
        if (ImGui::CollapsingHeader("Seçili eleman", ImGuiTreeNodeFlags_DefaultOpen)) {
            if (ImGui::BeginTable("##eleman", 2, tb)) {
                Satir("Tür", "Kolon");
                Satir("Profil", "HE340A");
                Satir("Malzeme", "S355");
                Satirf("h × b", "%.0f × 300 mm", 330.0);
                Satirf("tw / tf", "9,5 / %.1f mm", 16.5);
                Satirf("A", "%.1f cm²", 133.5);
                Satirf("Iy", "%.0f cm⁴", 27690.0);
                Satirf("Uzunluk", "%.3f m", 3.665);
                ImGui::EndTable();
            }
        }
        if (ImGui::CollapsingHeader("Görünüm", ImGuiTreeNodeFlags_DefaultOpen)) {
            int kip = d.sahne.kesitGorunumu ? 0 : 1;
            ImGui::RadioButton("Kesit", &kip, 0);
            ImGui::SameLine();
            ImGui::RadioButton("Çubuk", &kip, 1);
            d.sahne.kesitGorunumu = kip == 0;
            ImGui::Checkbox("Kenar çizgileri", &d.sahne.kenarlar);
            ImGui::SameLine();
            ImGui::Checkbox("Izgara", &d.sahne.izgara);
            ImGui::TextDisabled("%zu üçgen · MSAA %u× · ters-Z D32", d.ucgen, d.ornek);
        }
        if (ImGui::CollapsingHeader("Hesap motoru", ImGuiTreeNodeFlags_DefaultOpen)) {
            if (!d.motorBaslatildi) {
                ImGui::TextDisabled("Bu oturumda başlatılmadı.");
            } else if (!d.motor.hazir) {
                ImGui::TextUnformatted("Yükleniyor…");
            } else if (!d.motor.basarili) {
                ImGui::TextColored(ImVec4(1.0f, 0.45f, 0.4f, 1.0f), "Başlatılamadı");
                ImGui::TextWrapped("%s", d.motor.hata.c_str());
            } else if (ImGui::BeginTable("##motor", 2, tb)) {
                Satir("Python", d.motor.pythonSurumu.substr(0, d.motor.pythonSurumu.find(' ')).c_str());
                Satir("Sürüm", d.motor.surumJson.c_str());
                Satirf("Şablonlar", "%.0f", static_cast<double>(d.motor.sablonSayisi));
                Satirf("Açılış", "%.0f ms", d.motor.msToplam);
                ImGui::EndTable();
            }
        }
    }
    ImGui::End();

    // --- Komut ------------------------------------------------------------------------------------------------
    if (ImGui::Begin("Komut")) {
        const float girdiY = ImGui::GetFrameHeightWithSpacing();
        if (ImGui::BeginChild("##gecmis", ImVec2(0, -girdiY), ImGuiChildFlags_None)) {
            for (const std::string& s : d.komutGecmisi) ImGui::TextUnformatted(s.c_str());
            if (ImGui::GetScrollY() >= ImGui::GetScrollMaxY()) ImGui::SetScrollHereY(1.0f);
        }
        ImGui::EndChild();
        ImGui::SetNextItemWidth(-1);
        if (ImGui::InputTextWithHint("##komut", "Komut yazın (çizim komutları sonraki adımda)…", d.komut,
                                     sizeof(d.komut), ImGuiInputTextFlags_EnterReturnsTrue)) {
            if (d.komut[0]) KomutYaz(d, std::string("> ") + d.komut + "  (henüz tanımlı değil)");
            d.komut[0] = 0;
            ImGui::SetKeyboardFocusHere(-1);
        }
    }
    ImGui::End();
}

}  // namespace op4
