// op4 arayüzü — çizim yardımcıları ve bileşenler (bkz. bilesenler.h).
#include "arayuz/bilesenler.h"

#include <algorithm>
#include <cfloat>
#include <cmath>

#include "arayuz/ikonlar.h"

namespace op4 {

float Ciz::Gen(std::string_view s, float boy, tema::Agirlik a) const {
    if (s.empty()) return 0;
    // Boyut DPI ile çarpıldıktan sonra tam piksele yuvarlanır (ipucu bozulmasın; %125'te 11 → 14, 12 → 15, 13 → 16 px).
    return F(a)->CalcTextSizeA(std::round(S(boy)), FLT_MAX, 0.0f, s.data(), s.data() + s.size()).x / olcek;
}

std::string Ciz::Kes(std::string_view s, float maxw, float boy, tema::Agirlik a) const {
    if (maxw <= 0 || Gen(s, boy, a) <= maxw) return std::string(s);
    std::string t(s);
    while (!t.empty()) {
        do t.pop_back();
        while (!t.empty() && (static_cast<unsigned char>(t.back()) & 0xC0) == 0x80);
        if (!t.empty() && (static_cast<unsigned char>(t.back()) & 0x80)) t.pop_back();  // kısmi çok baytlı karakter
        while (!t.empty() && t.back() == ' ') t.pop_back();
        if (Gen(t + "…", boy, a) <= maxw) break;
    }
    return t + "…";
}

namespace {
void Yaz(const Ciz& c, ImFont* f, float x, float taban, std::string_view s, float boy, uint32_t renk) {
    if (s.empty() || !c.dl) return;
    const float px = std::max(1.0f, std::round(c.S(boy)));  // tam piksel boyut
    ImFontBaked* b = f->GetFontBaked(px);
    const float ust = c.S(taban) - (b ? b->Ascent : px * 0.8f);
    c.dl->AddText(f, px, ImVec2(std::round(c.S(x)), std::round(ust)), renk, s.data(), s.data() + s.size());
}
}  // namespace

float Ciz::Yazi(float x, float taban, std::string_view s, float boy, tema::Agirlik a, uint32_t renk, float maxw) const {
    if (maxw > 0) {
        const std::string k = Kes(s, maxw, boy, a);
        Yaz(*this, F(a), x, taban, k, boy, renk);
        return Gen(k, boy, a);
    }
    Yaz(*this, F(a), x, taban, s, boy, renk);
    return Gen(s, boy, a);
}
float Ciz::YaziOrta(float x, float taban, std::string_view s, float boy, tema::Agirlik a, uint32_t renk) const {
    const float g = Gen(s, boy, a);
    Yaz(*this, F(a), x - g * 0.5f, taban, s, boy, renk);
    return g;
}
float Ciz::YaziSag(float x, float taban, std::string_view s, float boy, tema::Agirlik a, uint32_t renk) const {
    const float g = Gen(s, boy, a);
    Yaz(*this, F(a), x - g, taban, s, boy, renk);
    return g;
}

void Ciz::YaziDikey(float x, float y, std::string_view s, float boy, tema::Agirlik a, uint32_t renk) const {
    if (s.empty()) return;
    // Yatay yaz, yeni köşeleri (x, y) çevresinde 90° saat yönünde döndür (ImRotate tekniği).
    const int i0 = dl->VtxBuffer.Size;
    const float yuk = boy * 1.4f;
    // Yatay yazı döndürmeden önce pencere dışına taşabilir: geniş kırpma dikdörtgeniyle yaz.
    dl->PushClipRect(ImVec2(-1e5f, -1e5f), ImVec2(1e5f, 1e5f), false);
    Yaz(*this, F(a), x, y + boy * 1.05f, s, boy, renk);
    dl->PopClipRect();
    // Döndürme: (px, py) → (X + (H − (py − Y)), Y + (px − X)) — yazı yukarıdan aşağı, harflerin üstü sağda.
    const float X = S(x), Y = S(y), H = S(yuk);
    for (int i = i0; i < dl->VtxBuffer.Size; ++i) {
        ImDrawVert& v = dl->VtxBuffer[i];
        const float px = v.pos.x - X, py = v.pos.y - Y;
        v.pos = ImVec2(X + (H - py), Y + px);
    }
}

void Ciz::Dikd(float x, float y, float w, float h, uint32_t renk) const {
    if (w <= 0 || h <= 0 || !(renk >> 24)) return;
    dl->AddRectFilled(P(x, y), P(x + w, y + h), renk);
}

void Ciz::Yuv(float x, float y, float w, float h, float r, uint32_t dolgu, uint32_t kenar, float lw) const {
    if (w <= 0 || h <= 0) return;
    const float rr = std::min(S(r), 0.5f * std::min(S(w), S(h)));
    if (dolgu >> 24) dl->AddRectFilled(P(x, y), P(x + w, y + h), dolgu, rr);
    if (kenar >> 24) {
        const float i = S(lw) * 0.5f;
        dl->AddRect(ImVec2(S(x) + i, S(y) + i), ImVec2(S(x + w) - i, S(y + h) - i), kenar, std::max(0.0f, rr - i),
                    S(lw));
    }
}

void Ciz::Golge(float x, float y, float w, float h, float r, float yaricap, float alfa, float dy) const {
    // Gauss bulanıklığı (σ = yarıçap) kenar profili Φ(−d/σ), katmanlı yuvarlak dikdörtgenlerle.
    const float sigma = std::max(0.5f, yaricap);
    const int N = 10;
    const float e0 = -dy, e1 = 2.2f * sigma;
    float onceki = 0;
    for (int i = N - 1; i >= 0; --i) {
        const float e = e0 + (e1 - e0) * static_cast<float>(i) / static_cast<float>(N - 1);
        const float hedef = alfa * 0.5f * std::erfc(e / (sigma * std::sqrt(2.0f)));
        const float a = std::clamp((hedef - onceki) / std::max(1e-4f, 1.0f - onceki), 0.0f, 1.0f);
        onceki = hedef;
        if (a <= 0.0005f) continue;
        dl->AddRectFilled(P(x - e, y + dy - e), P(x + w + e, y + dy + h + e), tema::Alfa(R().golge | 0xFF000000u, a),
                          S(std::max(0.0f, r + e)));
    }
}

void Ciz::Daire(float cx, float cy, float r, uint32_t dolgu, uint32_t kenar, float lw) const {
    if (dolgu >> 24) dl->AddCircleFilled(P(cx, cy), S(r), dolgu, 0);
    if (kenar >> 24) dl->AddCircle(P(cx, cy), S(r) - S(lw) * 0.5f, kenar, 0, S(lw));
}

void Ciz::Cizgi(float x0, float y0, float x1, float y1, uint32_t renk, float lw) const {
    dl->AddLine(P(x0, y0), P(x1, y1), renk, S(lw));
}

void Ciz::Gradyan(float x, float y, float w, float h, uint32_t ust, uint32_t alt) const {
    dl->AddRectFilledMultiColor(P(x, y), P(x + w, y + h), ust, ust, alt, alt);
}

void Ciz::Simge(std::string_view ad, float cx, float cy, float boy, uint32_t renk, float kalem) const {
    IkonCiz(dl, ad, S(cx - boy / 2), S(cy - boy / 2), S(boy), renk, std::max(0.9f, S(kalem)));
}

void Ciz::Sevron(float cx, float cy, int yon, float boy, uint32_t renk) const {
    static const char* const ad[4] = {"sevron_asagi", "sevron_sag", "sevron_ust", "sevron_sol"};
    Simge(ad[yon & 3], cx, cy, boy, renk ? renk : R().metin3, 1.4f);
}

void Ciz::OnayKutusu(float x, float y, bool isaretli, float boy, bool soluk) const {
    // §6: 14 px, 4 px yarıçap; işaretli vurgu + beyaz onay, işaretsiz beyaz + 1 px kenar.
    const uint32_t v = soluk ? R().ikonKapali : R().vurgu;
    const float r = tema::belirtec::R.kucuk * boy / 14.0f;
    if (isaretli) {
        Yuv(x, y, boy, boy, r, v);
        Simge("onay", x + boy / 2, y + boy / 2, boy - 2, R().beyaz, 1.8f);
    } else {
        Yuv(x, y, boy, boy, r, R().yuzey, R().dugmeKenar);
    }
}

void Ciz::Radyo(float cx, float cy, bool secili, float r) const {
    if (secili) {
        Daire(cx, cy, r, R().vurgu);
        Daire(cx, cy, r * 0.38f, R().beyaz);
    } else {
        Daire(cx, cy, r, R().yuzey, R().dugmeKenar);
    }
}

void Ciz::Anahtar(float x, float y, bool acik, float w, float h, bool soluk) const {
    // §6: 28×16 hap; açık vurgu, kapalı nötr; 12 px beyaz düğme + hafif gölge.
    const float d = h / 2 - 2;
    const float kx = acik ? x + w - h / 2 : x + h / 2;
    Yuv(x, y, w, h, h / 2, acik ? (soluk ? R().ikonKapali : R().vurgu) : R().anahtarKapali);
    Daire(kx, y + h / 2 + 0.6f, d + 0.6f, tema::Alfa(R().golge | 0xFF000000u, 0.18f));
    Daire(kx, y + h / 2, d, R().beyaz);
}

float Ciz::Kisayol(float x, float y, std::string_view metin, float boy, float h) const {
    // Tuş rozeti (§6): yüzey + 1 px çizgi + 1 px koyu alt kenar, 4 px; birleşik tuşlar ayrı rozetler.
    float gx = x;
    std::string_view kalan = metin;
    bool ilk = true;
    while (!kalan.empty()) {
        size_t k = kalan.find('+');
        if (k == 0 || kalan.size() == 1) k = std::string_view::npos;  // "+" tuşunun kendisi
        const std::string_view tus = kalan.substr(0, k);
        kalan = k == std::string_view::npos ? std::string_view{} : kalan.substr(k + 1);
        if (!ilk) gx += 3;
        ilk = false;
        const float w = std::max(h, Gen(tus, boy, tema::Agirlik::Orta) + 10);
        Yuv(gx, y, w, h, tema::belirtec::R.kucuk, R().dugmeKenar);
        Yuv(gx, y, w, h - 1, tema::belirtec::R.kucuk, R().yuzey, R().cizgi);
        YaziOrta(gx + w / 2, Taban(y, h - 1, boy), tus, boy, tema::Agirlik::Orta, R().metin2);
        gx += w;
    }
    return gx - x;
}

void Ciz::Dugme(float x, float y, float w, float h, std::string_view metin, bool birincil, float boy, bool soluk,
                bool uzerinde) const {
    const float r = tema::belirtec::R.orta;
    if (birincil) {
        uint32_t z = uzerinde ? R().vurguKoyu : R().vurgu;
        if (soluk) z = R().ikonKapali;
        if (!soluk) Yuv(x, y + 1, w, h, r, tema::Alfa(R().golge | 0xFF000000u, 0.10f));
        Yuv(x, y, w, h, r, z);
        YaziOrta(x + w / 2, Taban(y, h, boy), metin, boy, tema::Agirlik::Kalin, R().beyaz);
    } else {
        Yuv(x, y + 1, w, h, r, tema::Alfa(R().golge | 0xFF000000u, 0.06f));
        Yuv(x, y, w, h, r, uzerinde ? R().hover : R().yuzey, R().dugmeKenar);
        YaziOrta(x + w / 2, Taban(y, h, boy), metin, boy, tema::Agirlik::Orta, soluk ? R().metin4 : R().metin);
    }
}

void Ciz::Acilir(float x, float y, float w, float h, std::string_view metin, float boy, bool odak, bool salt,
                 uint32_t renk) const {
    // Dolgulu açılır liste (§6); salt okunur türü yüzey + kenar.
    const float r = tema::belirtec::R.orta;
    if (odak) Yuv(x - 3, y - 3, w + 6, h + 6, r + 3, tema::Alfa(R().odak, 0.28f));
    Yuv(x, y, w, h, r, odak || salt ? R().yuzey : R().alan, odak ? R().odak : (salt ? R().dugmeKenar : R().alanKenar));
    Yazi(x + 8, Taban(y, h, boy), Kes(metin, w - 28, boy), boy, tema::Agirlik::Normal, renk ? renk : R().metin);
    Sevron(x + w - 11, y + h / 2 + 0.5f, 0, 10, R().metin2);
}

void Ciz::Giris(float x, float y, float w, float h, std::string_view metin, float boy, bool odak, uint32_t renk,
                bool sag) const {
    // Dolgulu giriş (§6): alan + 1 px alan kenarı; odakta yüzey + odak kenar + 3 px %28 halka.
    const float r = tema::belirtec::R.orta;
    if (odak) Yuv(x - 3, y - 3, w + 6, h + 6, r + 3, tema::Alfa(R().odak, 0.28f));
    Yuv(x, y, w, h, r, odak ? R().yuzey : R().alan, odak ? R().odak : R().alanKenar);
    if (sag)
        YaziSag(x + w - 8, Taban(y, h, boy), metin, boy, tema::Agirlik::Normal, renk ? renk : R().metin);
    else
        Yazi(x + 8, Taban(y, h, boy), metin, boy, tema::Agirlik::Normal, renk ? renk : R().metin, w - 14);
}

float Ciz::Rozet(float x, float y, std::string_view s, float boy, uint32_t zemin, uint32_t renk, float h) const {
    const float w = Gen(s, boy, tema::Agirlik::Kalin) + 12;
    Yuv(x, y, w, h, h / 2, zemin);
    YaziOrta(x + w / 2, Taban(y, h, boy), s, boy, tema::Agirlik::Kalin, renk);
    return w;
}

void Ciz::IpucuKarti(float x, float y, std::string_view s, float boy) const {
    // Görünümdeki ipucu kartı (§3.6 "Üzerinde"): 6 px, açılır gölge, solda seçim noktası.
    const float w = Gen(s, boy, tema::Agirlik::Orta) + 24, h = 22;
    const auto& g = tema::belirtec::GOLGE.acilir;
    Golge(x, y, w, h, tema::belirtec::R.orta, g.bulaniklik * 0.6f, g.saydamlik, g.dy * 0.5f);
    Yuv(x, y, w, h, tema::belirtec::R.orta, R().yuzey, R().cizgi);
    Daire(x + 10, y + h / 2, 2.5f, R().uzerinde);
    Yazi(x + 17, Taban(y, h, boy), s, boy, tema::Agirlik::Orta, R().metin);
}

int Segmentli(const Ciz& c, const char* id, float x, float y, float h, const std::vector<std::string>& ogeler, int secili,
              bool vurgu, float boy, float esitW, float* toplamW, bool etkin) {
    const auto& R = c.R();
    const size_t n = ogeler.size();
    std::vector<float> g(n);
    float toplam = 4;
    for (size_t i = 0; i < n; ++i) {
        g[i] = esitW > 0 ? (esitW - 4) / static_cast<float>(n) : c.Gen(ogeler[i], boy, tema::Agirlik::Kalin) + 20;
        toplam += g[i];
    }
    if (toplamW) *toplamW = toplam;
    const float r = tema::belirtec::R.orta;
    c.Yuv(x, y, toplam, h, r, R.zemin2);
    int tik = -1;
    float px = x + 2;
    ImGui::PushID(id);
    for (size_t i = 0; i < n; ++i) {
        ImGui::PushID(static_cast<int>(i));
        if (Tiklama(c, "##parca", px, y + 2, g[i], h - 4) && etkin) tik = static_cast<int>(i);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        const bool sec = static_cast<int>(i) == secili;
        if (sec) {
            if (vurgu) {
                c.Yuv(px, y + 2, g[i], h - 4, r - 2, etkin ? R.vurgu : R.ikonKapali);
            } else {
                const auto& k = tema::belirtec::GOLGE.kabarik;
                c.Yuv(px, y + 2 + k.dy, g[i], h - 4, r - 2, tema::Alfa(R.golge | 0xFF000000u, k.saydamlik));
                c.Yuv(px, y + 2, g[i], h - 4, r - 2, R.yuzey);
            }
        } else if (ust && etkin) {
            c.Yuv(px, y + 2, g[i], h - 4, r - 2, tema::Alfa(R.yuzey, 0.6f));
        } else if (i > 0 && static_cast<int>(i) - 1 != secili) {
            c.Dusey(px, y + 6, y + h - 6, R.dugmeKenar);  // seçiliye komşu olmayan parçalar arası ayraç
        }
        const uint32_t renk = !etkin ? R.metin3 : sec ? (vurgu ? R.beyaz : R.metin) : R.metin2;
        c.YaziOrta(px + g[i] / 2, Taban(y, h, boy), c.Kes(ogeler[i], g[i] - 6, boy, tema::Agirlik::Kalin), boy,
                   sec ? tema::Agirlik::Kalin : tema::Agirlik::Orta, renk);
        px += g[i];
    }
    ImGui::PopID();
    return tik;
}

float Cip(const Ciz& c, float x, float y, float h, std::string_view metin, bool acik, bool nokta, float boy) {
    const auto& R = c.R();
    const float w = c.Gen(metin, boy, tema::Agirlik::Kalin) + (nokta ? 22 : 14);
    const float r = tema::belirtec::R.orta;
    if (acik)
        c.Yuv(x, y, w, h, r, R.vurguTon, R.vurguTon2);
    else
        c.Yuv(x, y, w, h, r, 0, R.cizgi);
    float tx = x + 7;
    if (nokta) {
        c.Daire(x + 9, y + h / 2, 2.5f, acik ? R.vurgu : R.metin4);
        tx = x + 15;
    }
    c.Yazi(tx, Taban(y, h, boy), metin, boy, tema::Agirlik::Kalin, acik ? R.vurguMetin : R.metin3);
    return w;
}

bool Tiklama(const Ciz& c, const char* id, float x, float y, float w, float h, int fareTuslari) {
    ImGui::SetCursorScreenPos(c.P(x, y));
    ImGuiButtonFlags f = 0;
    if (fareTuslari & 1) f |= ImGuiButtonFlags_MouseButtonLeft;
    if (fareTuslari & 2) f |= ImGuiButtonFlags_MouseButtonRight;
    if (fareTuslari & 4) f |= ImGuiButtonFlags_MouseButtonMiddle;
    return ImGui::InvisibleButton(id, ImVec2(std::max(1.0f, c.S(w)), std::max(1.0f, c.S(h))), f);
}

void OgeIpucu(const Ciz& c, std::string_view metin, std::string_view kisayol) {
    if (metin.empty() || !ImGui::IsItemHovered(ImGuiHoveredFlags_DelayNormal | ImGuiHoveredFlags_AllowWhenDisabled)) return;
    std::string s(metin);
    if (!kisayol.empty()) s += "  ·  " + std::string(kisayol);
    const ImVec2 mn = ImGui::GetItemRectMin(), mx = ImGui::GetItemRectMax();
    Ciz k = c;
    k.dl = ImGui::GetForegroundDrawList();
    const ImVec2 ekran = ImGui::GetIO().DisplaySize;
    const float w = k.Gen(s, 11, tema::Agirlik::Orta) + 16, h = 22;
    float x = (mn.x + mx.x) * 0.5f / c.olcek - w / 2;
    x = std::clamp(x, 4.0f, ekran.x / c.olcek - w - 4);
    float y = mx.y / c.olcek + 6;
    if (y + h > ekran.y / c.olcek - 4) y = mn.y / c.olcek - h - 6;
    // İpucu (§6 açılır pencere): yüzey, 1 px çizgi, 6 px, açılır gölge; 11/400 metin.
    const auto& g = tema::belirtec::GOLGE.acilir;
    k.Golge(x, y, w, h, tema::belirtec::R.orta, g.bulaniklik * 0.6f, g.saydamlik, g.dy * 0.5f);
    k.Yuv(x, y, w, h, tema::belirtec::R.orta, k.R().yuzey, k.R().cizgi);
    k.Yazi(x + 8, Taban(y, h, 11), s, 11, tema::Agirlik::Normal, k.R().metin);
}

}  // namespace op4
