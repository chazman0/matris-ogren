// op4 — D'nin panel ve kartları için Stüdyo belirteçleri ve küçük çizim yardımcıları (Windows, ImGui). Sahibi: D.
//
// Kaynak: op4/tasarim/taslaklar/studyo/tasarim.md §3 (renk belirteçleri), §5 (8 px ızgara, 6–8 px yuvarlatma),
// §6 (diyalog: kart 10 px yarıçap, birincil düğme en sağda Kahve→Altın gradyanlı), §9 (Altın = etkin / seçili).
// C (arayuz-goruntu) ortak tema tablosunu (tema.json / tema.h) yayımlayınca bu değerler oradan okunacak; o zamana dek
// D'nin çizdiği her şey (Sonuç özeti, çözüm durum öğesi, Kurtarma ve Şablondan yeni kartları, Ayarlar › Dosya) yalnız
// bu belirteçleri ve ImGui'nin C tarafından kurulan stilini kullanır. Sabit renk yazılmaz.
#pragma once

#include <cstdint>

#include "imgui.h"
#include "imgui_internal.h"

namespace op4::studyo {

constexpr ImU32 Rgb(uint32_t rgb, uint32_t a = 255) {
    return IM_COL32((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF, a);
}
// sonuc.h / gorunum.h renkleri 0xRRGGBBAA.
constexpr ImU32 Rgba(uint32_t rgba) { return IM_COL32((rgba >> 24) & 0xFF, (rgba >> 16) & 0xFF, (rgba >> 8) & 0xFF, rgba & 0xFF); }

// §3 renk belirteçleri
inline constexpr ImU32 ZEMIN = Rgb(0xF3F1ED), YUZEY = Rgb(0xFFFFFF), YUZEY2 = Rgb(0xF7F5F1), YUZEY3 = Rgb(0xEFECE6),
                       DURUM = Rgb(0xECE9E3), CIZGI = Rgb(0xE6E2DB), CIZGI2 = Rgb(0xD3CEC4), METIN = Rgb(0x14181B),
                       METIN2 = Rgb(0x5A5E62), METIN3 = Rgb(0x8C8C8C), KAHVE = Rgb(0x8A6B3C), KAHVE_KOYU = Rgb(0x6F5530),
                       ALTIN = Rgb(0xB08950), ALTIN_DOLGU = Rgb(0xF4EBDA), ALTIN_ZEMIN = Rgb(0xF8F2E6), KREM = Rgb(0xEDE6D8),
                       HATA = Rgb(0xC8372D), UYARI = Rgb(0xD9A13B), TAMAM = Rgb(0x4C9A63);
// §5 ölçüler (mantıksal px; ImGui ölçeği C'nin DPI kurulumundan gelir)
inline constexpr float YARICAP = 6.0f, KART_YARICAP = 10.0f, BOSLUK = 8.0f, SATIR = 24.0f;

inline float Olcek() { return ImGui::GetFontSize() / 13.0f; }

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

// Birincil eylem düğmesi: Kahve→Altın gradyanı (Stüdyo §1, §6; yalnız birincil eylemde), krem yazı.
inline bool BirincilDugme(const char* etiket, ImVec2 boyut = ImVec2(0, 0)) {
    const float s = Olcek();
    const ImVec2 b = ImGui::CalcTextSize(etiket, nullptr, true);
    if (boyut.x <= 0) boyut.x = b.x + 24.0f * s;
    if (boyut.y <= 0) boyut.y = SATIR * s;
    const ImVec2 p = ImGui::GetCursorScreenPos();
    const bool basildi = ImGui::InvisibleButton(etiket, boyut);
    const bool uzerinde = ImGui::IsItemHovered(), basili = ImGui::IsItemActive();
    ImDrawList* d = ImGui::GetWindowDrawList();
    const ImVec2 q(p.x + boyut.x, p.y + boyut.y);
    const int bas = d->VtxBuffer.Size;
    d->AddRectFilled(p, q, IM_COL32_WHITE, YARICAP * s);
    ImGui::ShadeVertsLinearColorGradientKeepAlpha(d, bas, d->VtxBuffer.Size, p, ImVec2(q.x, p.y), basili ? KAHVE_KOYU : KAHVE,
                                                  uzerinde ? ALTIN : Rgb(0xA07E48));
    const char* son = ImGui::FindRenderedTextEnd(etiket);
    d->AddText(ImVec2(p.x + (boyut.x - b.x) * 0.5f, p.y + (boyut.y - b.y) * 0.5f), YUZEY, etiket, son);
    return basildi;
}

// İkincil düğme: beyaz yüzey, ince kenar, Antrasit yazı; üzerinde Kahve kontur (Stüdyo §9).
inline bool IkincilDugme(const char* etiket, ImVec2 boyut = ImVec2(0, 0)) {
    const float s = Olcek();
    const ImVec2 b = ImGui::CalcTextSize(etiket, nullptr, true);
    if (boyut.x <= 0) boyut.x = b.x + 20.0f * s;
    if (boyut.y <= 0) boyut.y = SATIR * s;
    const ImVec2 p = ImGui::GetCursorScreenPos();
    const bool basildi = ImGui::InvisibleButton(etiket, boyut);
    const bool uzerinde = ImGui::IsItemHovered(), basili = ImGui::IsItemActive();
    ImDrawList* d = ImGui::GetWindowDrawList();
    const ImVec2 q(p.x + boyut.x, p.y + boyut.y);
    d->AddRectFilled(p, q, basili ? ALTIN_DOLGU : YUZEY, YARICAP * s);
    d->AddRect(p, q, uzerinde ? KAHVE : CIZGI2, YARICAP * s, 1.0f * s);  // 1.92.8: kalınlık, sonra bayraklar
    d->AddText(ImVec2(p.x + (boyut.x - b.x) * 0.5f, p.y + (boyut.y - b.y) * 0.5f), METIN, etiket,
               ImGui::FindRenderedTextEnd(etiket));
    return basildi;
}

// Kart başlığı (panel başlığı 15/600 rolü; yazı tipi ağırlığı C'nin atlasındadır) + isteğe bağlı açıklama satırı.
inline void Baslik(const char* baslik, const char* aciklama = nullptr) {
    ImGui::PushStyleColor(ImGuiCol_Text, METIN);
    ImGui::TextUnformatted(baslik);
    ImGui::PopStyleColor();
    if (aciklama && *aciklama) {
        ImGui::PushStyleColor(ImGuiCol_Text, METIN3);
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
    ImGui::GetWindowDrawList()->AddLine(p, ImVec2(p.x + ImGui::GetContentRegionAvail().x, p.y), CIZGI, 1.0f * s);
    ImGui::Dummy(ImVec2(0, 5.0f * s));
}

// İki sütunlu alan satırı (etiket metin2, değer metin / verilen renk), 26 px satır adımı (Stüdyo §5).
inline void EtiketDeger(const char* etiket, const char* deger, ImU32 renk = 0, float etiketGenisligi = 140.0f) {
    const float s = Olcek();
    ImGui::PushStyleColor(ImGuiCol_Text, METIN2);
    ImGui::TextUnformatted(etiket);
    ImGui::PopStyleColor();
    ImGui::SameLine(etiketGenisligi * s);
    ImGui::PushStyleColor(ImGuiCol_Text, renk ? renk : METIN);
    ImGui::TextUnformatted(deger);
    ImGui::PopStyleColor();
}

// Küçük renk karesi (D/C göstergesi).
inline void RenkKaresi(ImU32 renk) {
    const float s = Olcek(), k = 10.0f * s;
    const ImVec2 p = ImGui::GetCursorScreenPos();
    const float y = p.y + (ImGui::GetTextLineHeight() - k) * 0.5f;
    ImGui::GetWindowDrawList()->AddRectFilled(ImVec2(p.x, y), ImVec2(p.x + k, y + k), renk, 2.0f * s);
    ImGui::Dummy(ImVec2(k, ImGui::GetTextLineHeight()));
}

// Bilgi kutusu (altın zemin; kesit önerisi, kurtarma iletisi — Stüdyo §3 altin_zemin).
inline void BilgiKutusu(const char* metin) {
    const float s = Olcek();
    const float g = ImGui::GetContentRegionAvail().x;
    const ImVec2 b = ImGui::CalcTextSize(metin, nullptr, false, g - 16.0f * s);
    const ImVec2 p = ImGui::GetCursorScreenPos();
    ImDrawList* d = ImGui::GetWindowDrawList();
    d->AddRectFilled(p, ImVec2(p.x + g, p.y + b.y + 12.0f * s), ALTIN_ZEMIN, YARICAP * s);
    d->AddRectFilled(p, ImVec2(p.x + 3.0f * s, p.y + b.y + 12.0f * s), ALTIN, 1.5f * s);
    ImGui::SetCursorScreenPos(ImVec2(p.x + 10.0f * s, p.y + 6.0f * s));
    ImGui::PushStyleColor(ImGuiCol_Text, METIN);
    ImGui::PushTextWrapPos(ImGui::GetCursorPosX() + g - 16.0f * s);
    ImGui::TextUnformatted(metin);
    ImGui::PopTextWrapPos();
    ImGui::PopStyleColor();
    ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + b.y + 12.0f * s));
    ImGui::Dummy(ImVec2(g, 4.0f * s));
}

}  // namespace op4::studyo
