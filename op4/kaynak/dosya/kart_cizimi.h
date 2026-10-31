// op4 — D'nin panel ve kartları için küçük çizim yardımcıları (Windows, ImGui). Sahibi: D.
//
// Renkler ve ölçüler C'nin yayımladığı tema başlığından gelir (arayuz/tema.h: tema::Etkin().r / .o, tema::belirtec::*;
// "Atölye · Modern", MIMARI §25.1): D kendi belirteç kopyasını tutmaz, sabit renk yazmaz. D'nin çizdiği her şey (Sonuç
// özeti, çözüm durum öğesi, Kurtarma ve Şablondan yeni kartları, Ayarlar › Dosya) bu yardımcıları ve ImGui'nin C
// tarafından kurulan stilini kullanır. Vurgu paleti (Kobalt / Petrol / Grafit) çalışma anında değişir; renkler her
// çağrıda etkin temadan okunur.
#pragma once

#include <cstdint>

#include "arayuz/tema.h"
#include "imgui.h"
#include "imgui_internal.h"

namespace op4::kart {

// sonuc.h / gorunum.h renkleri 0xRRGGBBAA → ImGui IM_COL32.
constexpr ImU32 Rgba(uint32_t rgba) { return IM_COL32((rgba >> 24) & 0xFF, (rgba >> 16) & 0xFF, (rgba >> 8) & 0xFF, rgba & 0xFF); }

inline const tema::Renkler& R() { return tema::Etkin().r; }
// Mantıksal px → ekran px (ImGui ölçeği C'nin DPI ve yazı boyutu kurulumundan; gövde yazısı belirteç Y.govde).
inline float Olcek() { return ImGui::GetFontSize() / tema::belirtec::Y.govde.boy; }

// Rozet / pil (çip): yuvarlak, dolgulu, küçük yazı.
inline void Rozet(const char* metin, ImU32 dolgu, ImU32 yazi) {
    const float s = Olcek();
    const ImVec2 b = ImGui::CalcTextSize(metin);
    const ImVec2 p = ImGui::GetCursorScreenPos();
    const ImVec2 boyut(b.x + 14.0f * s, b.y + 4.0f * s);
    ImDrawList* d = ImGui::GetWindowDrawList();
    d->AddRectFilled(p, ImVec2(p.x + boyut.x, p.y + boyut.y), dolgu, boyut.y * 0.5f);
    d->AddText(ImVec2(p.x + 7.0f * s, p.y + 2.0f * s), yazi, metin);
    ImGui::Dummy(boyut);
}

// Birincil eylem düğmesi: düz vurgu dolgusu (üzerinde koyu vurgu), beyaz yazı (C'nin Ciz::Dugme birincil türü).
inline bool BirincilDugme(const char* etiket, ImVec2 boyut = ImVec2(0, 0)) {
    const float s = Olcek();
    const tema::Olculer& o = tema::Etkin().o;
    const ImVec2 b = ImGui::CalcTextSize(etiket, nullptr, true);
    if (boyut.x <= 0) boyut.x = b.x + 24.0f * s;
    if (boyut.y <= 0) boyut.y = o.segment * s;
    const ImVec2 p = ImGui::GetCursorScreenPos();
    const bool basildi = ImGui::InvisibleButton(etiket, boyut);
    const bool uzerinde = ImGui::IsItemHovered(), basili = ImGui::IsItemActive();
    ImDrawList* d = ImGui::GetWindowDrawList();
    const ImVec2 q(p.x + boyut.x, p.y + boyut.y);
    d->AddRectFilled(p, q, uzerinde || basili ? R().vurguKoyu : R().vurgu, o.yaricap * s);
    const char* son = ImGui::FindRenderedTextEnd(etiket);
    d->AddText(ImVec2(p.x + (boyut.x - b.x) * 0.5f, p.y + (boyut.y - b.y) * 0.5f), R().beyaz, etiket, son);
    return basildi;
}

// İkincil düğme: beyaz yüzey, ince kenar, metin rengi yazı; üzerinde nötr hover zemini (C'nin Ciz::Dugme ikincil türü).
inline bool IkincilDugme(const char* etiket, ImVec2 boyut = ImVec2(0, 0)) {
    const float s = Olcek();
    const tema::Olculer& o = tema::Etkin().o;
    const ImVec2 b = ImGui::CalcTextSize(etiket, nullptr, true);
    if (boyut.x <= 0) boyut.x = b.x + 20.0f * s;
    if (boyut.y <= 0) boyut.y = o.segment * s;
    const ImVec2 p = ImGui::GetCursorScreenPos();
    const bool basildi = ImGui::InvisibleButton(etiket, boyut);
    const bool uzerinde = ImGui::IsItemHovered(), basili = ImGui::IsItemActive();
    ImDrawList* d = ImGui::GetWindowDrawList();
    const ImVec2 q(p.x + boyut.x, p.y + boyut.y);
    d->AddRectFilled(p, q, basili ? R().basili : (uzerinde ? R().hover : R().yuzey), o.yaricap * s);
    d->AddRect(p, q, R().dugmeKenar, o.yaricap * s, 1.0f * s);  // 1.92.8: kalınlık, sonra bayraklar
    d->AddText(ImVec2(p.x + (boyut.x - b.x) * 0.5f, p.y + (boyut.y - b.y) * 0.5f), R().metin, etiket,
               ImGui::FindRenderedTextEnd(etiket));
    return basildi;
}

// Kart başlığı (yazı tipi ağırlığı C'nin atlasındadır) + isteğe bağlı açıklama satırı.
inline void Baslik(const char* baslik, const char* aciklama = nullptr) {
    ImGui::PushStyleColor(ImGuiCol_Text, R().metin);
    ImGui::TextUnformatted(baslik);
    ImGui::PopStyleColor();
    if (aciklama && *aciklama) {
        ImGui::PushStyleColor(ImGuiCol_Text, R().metin3);
        ImGui::PushTextWrapPos(0.0f);
        ImGui::TextUnformatted(aciklama);
        ImGui::PopTextWrapPos();
        ImGui::PopStyleColor();
    }
}

inline void Ayrac() {
    const float s = Olcek();
    ImGui::Dummy(ImVec2(0, 4.0f * s));
    const ImVec2 p = ImGui::GetCursorScreenPos();
    ImGui::GetWindowDrawList()->AddLine(p, ImVec2(p.x + ImGui::GetContentRegionAvail().x, p.y), R().cizgi, 1.0f * s);
    ImGui::Dummy(ImVec2(0, 5.0f * s));
}

// İki sütunlu alan satırı (etiket metin2, değer metin / verilen renk).
inline void EtiketDeger(const char* etiket, const char* deger, ImU32 renk = 0, float etiketGenisligi = 140.0f) {
    const float s = Olcek();
    ImGui::PushStyleColor(ImGuiCol_Text, R().metin2);
    ImGui::TextUnformatted(etiket);
    ImGui::PopStyleColor();
    ImGui::SameLine(etiketGenisligi * s);
    ImGui::PushStyleColor(ImGuiCol_Text, renk ? renk : R().metin);
    ImGui::TextUnformatted(deger);
    ImGui::PopStyleColor();
}

// Küçük renk karesi (D/C göstergesi).
inline void RenkKaresi(ImU32 renk) {
    const float s = Olcek(), k = 10.0f * s;
    const ImVec2 p = ImGui::GetCursorScreenPos();
    const float y = p.y + (ImGui::GetTextLineHeight() - k) * 0.5f;
    ImGui::GetWindowDrawList()->AddRectFilled(ImVec2(p.x, y), ImVec2(p.x + k, y + k), renk, tema::belirtec::R.kucuk * 0.5f * s);
    ImGui::Dummy(ImVec2(k, ImGui::GetTextLineHeight()));
}

// Bilgi kutusu (vurgu tonu zemin + solda vurgu şeridi; kesit önerisi, kurtarma iletisi, son hata).
inline void BilgiKutusu(const char* metin) {
    const float s = Olcek();
    const float r = tema::Etkin().o.yaricap * s;
    const float g = ImGui::GetContentRegionAvail().x;
    const ImVec2 b = ImGui::CalcTextSize(metin, nullptr, false, g - 16.0f * s);
    const ImVec2 p = ImGui::GetCursorScreenPos();
    ImDrawList* d = ImGui::GetWindowDrawList();
    d->AddRectFilled(p, ImVec2(p.x + g, p.y + b.y + 12.0f * s), R().vurguTon, r);
    d->AddRectFilled(p, ImVec2(p.x + 3.0f * s, p.y + b.y + 12.0f * s), R().vurgu, 1.5f * s);
    ImGui::SetCursorScreenPos(ImVec2(p.x + 10.0f * s, p.y + 6.0f * s));
    ImGui::PushStyleColor(ImGuiCol_Text, R().metin);
    ImGui::PushTextWrapPos(ImGui::GetCursorPosX() + g - 16.0f * s);
    ImGui::TextUnformatted(metin);
    ImGui::PopTextWrapPos();
    ImGui::PopStyleColor();
    ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + b.y + 12.0f * s));
    ImGui::Dummy(ImVec2(g, 4.0f * s));
}

}  // namespace op4::kart
