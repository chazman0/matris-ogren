// op4 arayüzü — ImGui stil ayarları (bkz. stil.h). Atölye · Modern tasarim.md §10 "ImGuiStyle" ve "Renk eşleme"
// satırları: yarıçaplar belirteçlerden (R), renkler etkin temadan (vurgu paleti değişince yeniden çağrılır).
#include "arayuz/stil.h"

#include "arayuz/tema.h"
#include "imgui.h"

namespace op4 {
namespace {
ImVec4 V(uint32_t c) { return ImGui::ColorConvertU32ToFloat4(c); }
}  // namespace

void ArayuzStiliUygula(float olcek) {
    namespace b = tema::belirtec;
    ImGuiStyle& s = ImGui::GetStyle();
    s = ImGuiStyle();
    ImGui::StyleColorsLight(&s);
    const tema::Renkler& R = tema::Etkin().r;
    s.WindowRounding = b::R.pencere;
    s.ChildRounding = b::R.orta;
    s.FrameRounding = b::R.orta;
    s.PopupRounding = b::R.buyuk;
    s.GrabRounding = b::R.buyuk;
    s.TabRounding = b::R.orta;
    s.ScrollbarRounding = 2;
    s.ScrollbarSize = 8;
    s.WindowBorderSize = 1;
    s.FrameBorderSize = 1;
    s.PopupBorderSize = 1;
    s.ItemSpacing = ImVec2(b::A.a2, b::A.a2);
    s.ItemInnerSpacing = ImVec2(6, b::A.a1);
    s.FramePadding = ImVec2(b::A.a2, b::A.a1);
    s.WindowPadding = ImVec2(b::A.a3, b::A.a3);
    s.WindowTitleAlign = ImVec2(0.0f, 0.5f);
    s.AntiAliasedFill = s.AntiAliasedLines = true;
    s.FontSizeBase = b::Y.govde.boy;
    ImVec4* c = s.Colors;
    c[ImGuiCol_Text] = V(R.metin);
    c[ImGuiCol_TextDisabled] = V(R.metin4);
    c[ImGuiCol_WindowBg] = V(R.yuzey);
    c[ImGuiCol_ChildBg] = V(R.yuzey);
    c[ImGuiCol_PopupBg] = V(R.yuzey);
    c[ImGuiCol_Border] = V(R.cizgi);
    c[ImGuiCol_BorderShadow] = ImVec4(0, 0, 0, 0);
    c[ImGuiCol_FrameBg] = V(R.alan);
    c[ImGuiCol_FrameBgHovered] = V(R.hover);
    c[ImGuiCol_FrameBgActive] = V(R.yuzey);
    c[ImGuiCol_TitleBg] = V(R.yuzey2);
    c[ImGuiCol_TitleBgActive] = V(R.yuzey2);
    c[ImGuiCol_TitleBgCollapsed] = V(R.yuzey2);
    c[ImGuiCol_MenuBarBg] = V(R.zemin);
    c[ImGuiCol_ScrollbarBg] = ImVec4(0, 0, 0, 0);
    c[ImGuiCol_ScrollbarGrab] = V(tema::Alfa(R.metin, 0.22f));
    c[ImGuiCol_ScrollbarGrabHovered] = V(tema::Alfa(R.metin, 0.32f));
    c[ImGuiCol_ScrollbarGrabActive] = V(tema::Alfa(R.metin, 0.42f));
    c[ImGuiCol_CheckMark] = V(R.vurgu);
    c[ImGuiCol_SliderGrab] = V(R.vurgu);
    c[ImGuiCol_SliderGrabActive] = V(R.vurguKoyu);
    c[ImGuiCol_Button] = V(R.yuzey);
    c[ImGuiCol_ButtonHovered] = V(R.hover);
    c[ImGuiCol_ButtonActive] = V(R.basili);
    c[ImGuiCol_Header] = V(R.secimTon);
    c[ImGuiCol_HeaderHovered] = V(R.hover);
    c[ImGuiCol_HeaderActive] = V(R.secimTon2);
    c[ImGuiCol_Separator] = V(R.cizgi2);
    c[ImGuiCol_SeparatorHovered] = V(R.vurgu);
    c[ImGuiCol_SeparatorActive] = V(R.vurgu);
    c[ImGuiCol_ResizeGrip] = ImVec4(0, 0, 0, 0);
    c[ImGuiCol_ResizeGripHovered] = V(R.vurguTon2);
    c[ImGuiCol_ResizeGripActive] = V(R.vurgu);
    c[ImGuiCol_Tab] = V(R.zemin);
    c[ImGuiCol_TabHovered] = V(R.hover);
    c[ImGuiCol_TabSelected] = V(R.yuzey);
    c[ImGuiCol_TabSelectedOverline] = V(R.vurgu);
    c[ImGuiCol_TableHeaderBg] = V(R.yuzey2);
    c[ImGuiCol_TableBorderStrong] = V(R.cizgi);
    c[ImGuiCol_TableBorderLight] = V(R.cizgi2);
    c[ImGuiCol_TableRowBg] = ImVec4(0, 0, 0, 0);
    c[ImGuiCol_TableRowBgAlt] = ImVec4(0, 0, 0, 0);  // zebra yok
    c[ImGuiCol_TextSelectedBg] = V(tema::Alfa(R.vurgu, 0.25f));
    c[ImGuiCol_NavCursor] = V(R.odak);
    c[ImGuiCol_ModalWindowDimBg] = V(R.karartma);
    c[ImGuiCol_PlotHistogram] = V(R.vurgu);
    s.ScaleAllSizes(olcek);
    s.FontScaleDpi = olcek;
}

}  // namespace op4
