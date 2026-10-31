// op4 arayüzü — pencereler: Ayarlar (Program / Görüntü / Dil ayarları; S18 grupları, D kalıcılaştırır), Hızlı aks, Kısayollar,
// op4 hakkında, Yönetmelik sihirbazı kancası (S21 iletişim kaydı).
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>

#include <nlohmann/json.hpp>

#include "arayuz/ana_pencere.h"
#include "arayuz/dil.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/komut.h"
#include "cekirdek/turkce.h"

namespace op4 {
namespace {

// ---- Ayarlar penceresi düzeni (Atölye · Modern tasarim.md §7) --------------------------------------------------------------
// Kipli pencere: başlık 56 · sol gezinti 256 (arama, üç kategori, etkin kategorinin bölümleri) · sayfa (başlık 20/600,
// açıklama, iki sütun kart; kart başlığı 40, satır 44 / 36) · alt çubuk 64 (Varsayılana dön ▾, değişiklik sayısı,
// İptal / Uygula / Tamam). Satırların denetimleri ImGui öğeleridir; zemin ve yazılar Ciz ile çizilir.
struct AyarDuzeni {
    Ciz c;
    float ox = 0, oy = 0;      // içerik kökü (mantıksal px, kaydırma dahil)
    float kolW = 0;            // kart genişliği
    float kolY[2] = {0, 0};    // iki sütunun dolu yüksekliği
    int kol = 0;               // etkin sütun
    bool tekSutun = false;
    std::string arama;         // Türkçe katlanmış arama metni
    // etkin kart
    const char* kartAd = nullptr;
    const char* kartIkon = nullptr;
    float kx = 0, ky = 0, y = 0;
    bool baslikCizildi = false;
    int satirSayisi = 0;
    std::vector<std::pair<std::string, float>>* bolumler = nullptr;  // gezinti için kart konumları
};

constexpr float kKartBaslik = 40, kKartArasi = 16;

void KartBasla(AyarDuzeni& d, const char* ad, const char* ikon, int kol) {
    d.kartAd = ad;
    d.kartIkon = ikon;
    d.kol = d.tekSutun ? 0 : kol;
    d.kx = d.ox + static_cast<float>(d.kol) * (d.kolW + 24);
    d.ky = d.oy + d.kolY[d.kol];
    d.y = d.ky + kKartBaslik;
    d.baslikCizildi = false;
    d.satirSayisi = 0;
    d.c.dl->ChannelsSplit(2);
    d.c.dl->ChannelsSetCurrent(1);
}

void KartBasligi(AyarDuzeni& d) {
    if (d.baslikCizildi) return;
    d.baslikCizildi = true;
    const auto& R = d.c.R();
    d.c.Simge(d.kartIkon, d.kx + 24, d.ky + kKartBaslik / 2, 16, R.ikonKucuk, 1.4f);
    d.c.Yazi(d.kx + 40, Taban(d.ky, kKartBaslik, 13), Tr(d.kartAd), 13, tema::Agirlik::Kalin, R.metin);
    d.c.Yatay(d.kx, d.kx + d.kolW, d.ky + kKartBaslik - 1, R.cizgi2);
    if (d.bolumler) d.bolumler->push_back({d.kartAd, d.ky - d.oy});
}

void KartBitir(AyarDuzeni& d) {
    d.c.dl->ChannelsSetCurrent(0);
    if (d.baslikCizildi) {
        const auto& R = d.c.R();
        const float h = d.y - d.ky + 8;
        d.c.Golge(d.kx, d.ky, d.kolW, h, tema::belirtec::R.orta, 4, 0.05f, 1);
        d.c.Yuv(d.kx, d.ky, d.kolW, h, tema::belirtec::R.orta, R.yuzey, R.cizgi);
        d.kolY[d.kol] += h + kKartArasi;
    }
    d.c.dl->ChannelsMerge();
}

// Satır: solda etiket 12/500 + açıklama 11/400, sağda denetim alanı (dx, dy, dw). Varsayılandan farklıysa etiketin
// solunda vurgu nokta + denetimin solunda "Varsayılan: …". Arama eşleşmezse false (denetim çizilmez).
bool Satir(AyarDuzeni& d, const char* etiket, const char* aciklama, bool farkli, const std::string& varsayilan, float dw,
           float& dx, float& dy, float yuk = 0) {
    if (!d.arama.empty()) {
        const std::string m = TurkceKatla(std::string(Tr(etiket)) + " " + (aciklama ? Tr(aciklama) : "") + " " + etiket);
        const std::string k = TurkceKatla(std::string(Tr(d.kartAd)));
        if (m.find(d.arama) == std::string::npos && k.find(d.arama) == std::string::npos) return false;
    }
    KartBasligi(d);
    const auto& R = d.c.R();
    const float h = yuk > 0 ? yuk : (aciklama ? 48.0f : 38.0f);
    if (d.satirSayisi++ > 0) d.c.Yatay(d.kx + 16, d.kx + d.kolW - 16, d.y, R.cizgi2);
    if (farkli) d.c.Daire(d.kx + 9, d.y + (aciklama ? 18 : h / 2), 3, R.vurgu);
    const float ty = aciklama ? d.y + 20 : Taban(d.y, h, 12);
    d.c.Yazi(d.kx + 16, ty, Tr(etiket), 12, tema::Agirlik::Orta, R.metin, d.kolW - dw - 48);
    if (aciklama) d.c.Yazi(d.kx + 16, ty + 15, Tr(aciklama), 11, tema::Agirlik::Normal, R.metin3, d.kolW - dw - 48);
    dx = d.kx + d.kolW - 16 - dw;
    dy = d.y + (yuk > 0 ? 10 : (h - 28) / 2);
    if (farkli && !varsayilan.empty() && dw < d.kolW * 0.5f) {
        const std::string v = std::string(Tr("Varsayılan")) + ": " + varsayilan;
        d.c.YaziSag(dx - 10, Taban(d.y, h, 10), v, 10, tema::Agirlik::Normal, R.metin3);
    }
    d.y += h;
    return true;
}

// Anahtar denetimi (28×16), tıklanınca değişir.
bool AnahtarDenetimi(const Ciz& c, const char* id, float x, float y, bool& deger, bool etkin = true) {
    const bool t = Tiklama(c, id, x, y + 6, 28, 16) && etkin;
    if (t) deger = !deger;
    c.Anahtar(x, y + 6, deger, 28, 16, !etkin);
    return t;
}

// Segment denetimi: seçenek kodları ↔ görünen adlar.
template <class T>
bool SegmentDenetimi(const Ciz& c, const char* id, float x, float y, float w, T& deger, const std::vector<std::pair<T, const char*>>& s,
                     bool etkin = true) {
    std::vector<std::string> adlar;
    int secili = -1;
    for (size_t i = 0; i < s.size(); ++i) {
        adlar.push_back(Tr(s[i].second));
        if (s[i].first == deger) secili = static_cast<int>(i);
    }
    (void)w;  // genişlik metinden (SegmentGenisligi ile aynı)
    const int t = Segmentli(c, id, x, y, 28, adlar, secili, false, 11, 0, nullptr, etkin);
    if (t < 0 || s[static_cast<size_t>(t)].first == deger) return false;
    deger = s[static_cast<size_t>(t)].first;
    return true;
}

float SegmentGenisligi(const Ciz& c, const std::vector<const char*>& adlar) {
    float w = 4;
    for (const char* a : adlar) w += c.Gen(Tr(a), 11, tema::Agirlik::Kalin) + 20;
    return w;
}

// ImGui açılır listesi (dolgulu görünüm stil eşlemesinden).
bool AcilirDenetim(const Ciz& c, const char* id, float x, float y, float w, std::string& deger,
                   const std::vector<std::pair<std::string, std::string>>& s) {
    ImGui::SetCursorScreenPos(c.P(x, y));
    ImGui::SetNextItemWidth(c.S(w));
    std::string gorunen = deger;
    for (const auto& [k, ad] : s)
        if (k == deger) gorunen = Tr(ad.c_str());
    bool degisti = false;
    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(c.S(8), c.S(6)));
    const bool acik = ImGui::BeginCombo(id, gorunen.c_str(), ImGuiComboFlags_NoArrowButton);
    ImGui::PopStyleVar();
    c.Sevron(x + w - 12, y + 14, 0, 10, c.R().metin2);
    if (acik) {
        for (const auto& [k, ad] : s)
            if (ImGui::Selectable(Tr(ad.c_str()), deger == k)) {
                deger = k;
                degisti = true;
            }
        ImGui::EndCombo();
    }
    return degisti;
}

bool KaydiriciDenetim(const Ciz& c, const char* id, float x, float y, float w, double& deger, float en, float enCok, const char* bicim) {
    float v = static_cast<float>(deger);
    ImGui::SetCursorScreenPos(c.P(x, y + 4));
    ImGui::SetNextItemWidth(c.S(w - 64));
    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(0, c.S(1)));
    ImGui::PushStyleVar(ImGuiStyleVar_GrabMinSize, c.S(14));
    ImGui::PushStyleColor(ImGuiCol_FrameBg, ImGui::ColorConvertU32ToFloat4(c.R().zemin2));
    ImGui::PushStyleColor(ImGuiCol_FrameBgHovered, ImGui::ColorConvertU32ToFloat4(c.R().zemin2));
    ImGui::PushStyleColor(ImGuiCol_FrameBgActive, ImGui::ColorConvertU32ToFloat4(c.R().zemin2));
    const bool t = ImGui::SliderFloat(id, &v, en, enCok, "");
    ImGui::PopStyleColor(3);
    ImGui::PopStyleVar(2);
    char b[32];
    std::snprintf(b, sizeof(b), bicim, v);
    std::string m = b;
    for (char& ch : m)
        if (ch == '.') ch = Sayi(0.5, 1).find(',') != std::string::npos ? ',' : '.';
    c.YaziSag(x + w, Taban(y, 28, 12), m, 12, tema::Agirlik::Orta, c.R().metin);
    if (t) deger = std::round(static_cast<double>(v) * 10.0) / 10.0;
    return t;
}

bool RenkDenetimi(const Ciz& c, const char* id, float x, float y, std::string& hex, bool etkin) {
    unsigned v = 0;
    std::sscanf(hex.c_str(), "#%06x", &v);
    float k[3] = {((v >> 16) & 255) / 255.0f, ((v >> 8) & 255) / 255.0f, (v & 255) / 255.0f};
    c.Giris(x, y, 104, 28, "", 12, false);
    ImGui::SetCursorScreenPos(c.P(x + 6, y + 6));
    ImGui::BeginDisabled(!etkin);
    const bool t = ImGui::ColorEdit3(id, k, ImGuiColorEditFlags_NoInputs | ImGuiColorEditFlags_NoLabel);
    ImGui::EndDisabled();
    c.Yazi(x + 30, Taban(y, 28, 11), hex, 11, tema::Agirlik::Normal, etkin ? c.R().metin : c.R().metin3);
    if (!t) return false;
    char b[8];
    std::snprintf(b, sizeof(b), "#%02X%02X%02X", static_cast<int>(k[0] * 255 + 0.5f), static_cast<int>(k[1] * 255 + 0.5f),
                  static_cast<int>(k[2] * 255 + 0.5f));
    hex = b;
    return true;
}

// Açılış ekranı küçük resmi (Kemer Çizgisi; açık / koyu zemin), vektörle.
void AcilisKucukResmi(const Ciz& c, float x, float y, float w, float h, bool koyu, bool secili) {
    const auto& R = c.R();
    const uint32_t zemin = koyu ? tema::Renk(tema::belirtec::NOTR.metin) : tema::Renk(0xF4EFE6);  // kimlik paleti (logo zemini)
    const uint32_t kemer = tema::Renk(0x8A6B3C);                                                   // kimlik kahvesi (yalnız logo)
    c.Yuv(x, y, w, h, tema::belirtec::R.orta, zemin, secili ? R.vurgu : R.cizgi, secili ? 2.0f : 1.0f);
    const float ax = x + w * 0.30f, ay = y + h * 0.30f, ar = h * 0.20f;
    c.dl->PathArcTo(c.P(ax, ay + ar), c.S(ar), 3.14159f, 2 * 3.14159f, 16);
    c.dl->PathStroke(kemer, c.S(3.0f));
    c.Cizgi(ax - ar, ay + ar, ax - ar, ay + ar * 2.6f, kemer, 3.0f);
    c.Cizgi(ax + ar, ay + ar, ax + ar, ay + ar * 2.6f, kemer, 3.0f);
    c.Yazi(x + w * 0.52f, y + h * 0.52f, "op4", 13, tema::Agirlik::Orta, koyu ? R.beyaz : R.metin);
}

}  // namespace

void AnaPencere::AyarlarPenceresi(Ciz& c) {
    if (!h_.ayarlar) return;
    Ayarlar& a = *h_.ayarlar;
    const Ayarlar v{};  // varsayılanlar
    const auto& R = c.R();
    if (ayarlarAcik && !ImGui::IsPopupOpen("##ayarlar")) {
        ImGui::OpenPopup("##ayarlar");
        ayarOnceki_ = std::make_shared<Ayarlar>(a);
        ayarArama_[0] = 0;
    }
    const ImGuiIO& io = ImGui::GetIO();
    const float W = std::min(1440.0f, io.DisplaySize.x / olcek_ * 0.94f), H = std::min(960.0f, io.DisplaySize.y / olcek_ * 0.94f);
    ImGui::SetNextWindowSize(c.P(W, H), ImGuiCond_Always);
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f), ImGuiCond_Always, ImVec2(0.5f, 0.5f));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, c.S(tema::belirtec::R.pencere));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0);
    const bool acik = ImGui::BeginPopupModal("##ayarlar", nullptr, ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                                                        ImGuiWindowFlags_NoSavedSettings);
    ImGui::PopStyleVar(3);
    if (!acik) {
        ayarlarAcik = false;
        return;
    }
    Ciz k = c;
    k.dl = ImGui::GetWindowDrawList();
    const ImVec2 wp = ImGui::GetWindowPos();
    const float X = wp.x / olcek_, Y = wp.y / olcek_;
    auto iptal = [&] {
        if (ayarOnceki_) a = *ayarOnceki_;
        AyarlariUygula();
        ayarlarAcik = false;
    };
    auto uygula = [&] { ayarOnceki_ = std::make_shared<Ayarlar>(a); };
    // ---- başlık 56
    const float bh = 56;
    k.Dikd(X, Y + bh - 1, W, 1, R.cizgi);
    k.Yuv(X + 16, Y + 12, 32, 32, tema::belirtec::R.orta, R.vurguTon);
    k.Simge("ayar", X + 32, Y + 28, 18, R.vurgu, 1.5f);
    const float tw = k.Yazi(X + 60, Taban(Y, bh, 15), Tr("Ayarlar"), 15, tema::Agirlik::Kalin, R.metin);
    k.Yazi(X + 60 + tw + 12, Taban(Y, bh, 11), std::string(Tr("Kullanıcı ayarları")) + " · op4 " + h_.bilgi.surum + " · Ctrl+,", 11,
           tema::Agirlik::Normal, R.metin3);
    if (Tiklama(k, "##ay_kapat", X + W - 44, Y + 14, 28, 28)) iptal();
    if (ImGui::IsItemHovered()) k.Yuv(X + W - 44, Y + 14, 28, 28, tema::belirtec::R.orta, R.hover);
    k.Simge("kapat", X + W - 30, Y + 28, 13, R.ikonKucuk, 1.4f);
    // ---- sol gezinti 256
    const float gw = W < 1000 ? 64.0f : 256.0f, fh = 64, iy = Y + bh, ih = H - bh - fh;
    k.Dikd(X, iy, gw, ih, R.yuzey2);
    k.Dusey(X + gw - 1, iy, iy + ih, R.cizgi);
    k.Dikd(X + gw, iy, W - gw, ih, R.sayfa);
    if (gw > 100) {
        static bool aramaOdak = false;
        k.Giris(X + 16, iy + 16, gw - 32, 28, "", 12, aramaOdak);
        k.Simge("ara", X + 30, iy + 30, 13, R.metin3, 1.4f);
        ImGui::SetCursorScreenPos(k.P(X + 40, iy + 21));
        ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(k.S(2), k.S(2)));
        ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 0);
        ImGui::PushStyleColor(ImGuiCol_FrameBg, IM_COL32(0, 0, 0, 0));
        ImGui::PushStyleColor(ImGuiCol_FrameBgHovered, IM_COL32(0, 0, 0, 0));
        ImGui::PushStyleColor(ImGuiCol_FrameBgActive, IM_COL32(0, 0, 0, 0));
        ImGui::PushStyleColor(ImGuiCol_TextDisabled, ImGui::ColorConvertU32ToFloat4(R.metin3));
        ImGui::SetNextItemWidth(k.S(gw - 32 - 30 - 8));
        if (ImGui::IsKeyChordPressed(ImGuiMod_Ctrl | ImGuiKey_F)) ImGui::SetKeyboardFocusHere();
        ImGui::InputTextWithHint("##ayar_ara", Tr("Ayarlarda ara"), ayarArama_, sizeof(ayarArama_));
        aramaOdak = ImGui::IsItemActive();
        ImGui::PopStyleColor(4);
        ImGui::PopStyleVar(2);
    }
    static const char* const sayfalar[3] = {"Program ayarları", "Görüntü ayarları", "Dil ayarları"};
    static const char* const aciklamalar[3] = {
        "Başlangıç, kayıt ve kurtarma, geri alma, varsayılan birimler, fare ve hesap motoru",
        "Grafik bağdaştırıcısı, kenar yumuşatma, model görünümü, seçim renkleri, vurgu rengi, yoğunluk ve açılış ekranı",
        "Arayüz dili, sayı biçimi ve birim sistemi"};
    static const char* const ikonlar[3] = {"ayar", "pencere", "dil"};
    static std::vector<std::pair<std::string, float>> bolumKonumlari;
    static float kaydirma = 0;
    float ny = iy + (gw > 100 ? 60.0f : 16.0f);
    for (int i = 0; i < 3; ++i) {
        ImGui::PushID(i);
        const bool tik = Tiklama(k, "##ay_sayfa", X + 8, ny, gw - 16, 36);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        const bool etkin = ayarSayfasi == i && ayarArama_[0] == 0;
        if (etkin)
            k.Yuv(X + 8, ny, gw - 16, 36, tema::belirtec::R.orta, R.vurguTon);
        else if (ust)
            k.Yuv(X + 8, ny, gw - 16, 36, tema::belirtec::R.orta, R.hover);
        k.Simge(ikonlar[i], X + 28, ny + 18, 16, etkin ? R.vurgu : R.ikonKucuk, 1.4f);
        if (gw > 100) {
            k.Yazi(X + 44, Taban(ny, 36, 13), Tr(sayfalar[i]), 13, tema::Agirlik::Kalin, etkin ? R.vurguMetin : R.metin);
            k.Sevron(X + gw - 28, ny + 18, etkin ? 0 : 1, 10, R.metin3);
        } else {
            OgeIpucu(k, Tr(sayfalar[i]));
        }
        if (tik) {
            ayarSayfasi = i;
            ayarArama_[0] = 0;
            ImGui::SetNextWindowScroll(ImVec2(0, 0));
        }
        ny += 40;
        if (etkin && gw > 100) {  // alt bölümler: dikey kılavuz üzerinde, görünen bölüm vurgulu
            const float kb = ny;
            int gorunen = 0;  // görünen bölüm: üst kenarı kaydırmanın en yakın üstünde kalan (eşitlikte ilk sıradaki)
            for (size_t j = 0; j < bolumKonumlari.size(); ++j)
                if (bolumKonumlari[j].second <= kaydirma + 40 && bolumKonumlari[j].second > bolumKonumlari[static_cast<size_t>(gorunen)].second)
                    gorunen = static_cast<int>(j);
            for (size_t j = 0; j < bolumKonumlari.size(); ++j) {
                ImGui::PushID(static_cast<int>(100 + j));
                if (Tiklama(k, "##ay_bolum", X + 24, ny, gw - 40, 30)) ImGui::SetNextWindowScroll(ImVec2(0, k.S(bolumKonumlari[j].second)));
                ImGui::PopID();
                const bool g = static_cast<int>(j) == gorunen;
                if (g) k.Yuv(X + 26, ny + 5, 3, 20, 1.5f, R.vurgu);
                k.Yazi(X + 40, Taban(ny, 30, 12), Tr(bolumKonumlari[j].first.c_str()), 12,
                       g ? tema::Agirlik::Kalin : tema::Agirlik::Normal, g ? R.metin : R.metin2);
                ny += 30;
            }
            k.Dusey(X + 27, kb, ny, R.cizgi);
            ny += 8;
        }
    }
    if (gw > 100) {
        k.Yatay(X + 16, X + gw - 16, iy + ih - 56, R.cizgi);
        k.Simge("ac", X + 24, iy + ih - 38, 13, R.ikonKucuk, 1.4f);
        k.Yazi(X + 36, Taban(iy + ih - 48, 20, 11), "ayarlar.json", 11, tema::Agirlik::Normal, R.metin2);
        k.Yazi(X + 16, Taban(iy + ih - 28, 20, 11), Tr("İçe aktar · Dışa aktar (Faz 3)"), 11, tema::Agirlik::Normal, R.metin3);
    }
    // ---- sayfa (kaydırılabilir)
    ImGui::SetCursorScreenPos(k.P(X + gw, iy));
    ImGui::PushStyleColor(ImGuiCol_ChildBg, IM_COL32(0, 0, 0, 0));
    ImGui::BeginChild("##ay_sayfa_icerik", k.P(W - gw, ih), ImGuiChildFlags_None);
    kaydirma = ImGui::GetScrollY() / olcek_;
    bool degisti = false;
    {
        AyarDuzeni d;
        d.c = k;
        d.c.dl = ImGui::GetWindowDrawList();
        const ImVec2 o = ImGui::GetCursorScreenPos();
        const float sayfaW = W - gw - 64;
        d.ox = o.x / olcek_ + 32;
        d.tekSutun = sayfaW < 1000 - 64;
        d.kolW = d.tekSutun ? sayfaW : (sayfaW - 24) / 2;
        d.arama = TurkceKatla(ayarArama_);
        std::vector<std::pair<std::string, float>> konumlar;
        d.bolumler = &konumlar;
        float y = o.y / olcek_ + 28;
        const bool aramada = !d.arama.empty();
        const std::string sayfaBasligi = aramada ? Trf("Arama: “%s”", ayarArama_) : std::string(Tr(sayfalar[ayarSayfasi]));
        d.c.Yazi(d.ox, y + 18, sayfaBasligi, 20, tema::Agirlik::Kalin, R.metin);
        if (!aramada) d.c.Yazi(d.ox, y + 42, Tr(aciklamalar[ayarSayfasi]), 12, tema::Agirlik::Normal, R.metin2, sayfaW);
        y += 64;
        d.oy = y;
        float dx = 0, dy = 0;
        auto sayfaGoster = [&](int sayfa) { return aramada || ayarSayfasi == sayfa; };
        // ===== Program ayarları
        if (sayfaGoster(0)) {
            KartBasla(d, "Başlangıç", "oynat", 0);
            {
                int ac = a.arayuz.acilis == "son_proje" ? 1 : (a.arayuz.acilis == "bos" ? 2 : 0);
                if (Satir(d, "Açılışta", "Program açıldığında ne gösterilsin", a.arayuz.acilis != v.arayuz.acilis, Tr("Başlangıç paneli"), 220, dx, dy, 96)) {
                    static const char* const s[3] = {"Başlangıç paneli", "Son projeyi aç", "Boş çalışma alanı"};
                    for (int i = 0; i < 3; ++i) {
                        ImGui::PushID(300 + i);
                        if (Tiklama(d.c, "##acilis", dx, dy + static_cast<float>(i) * 26.0f, 220, 24)) ac = i, degisti = true;
                        ImGui::PopID();
                        d.c.Radyo(dx + 8, dy + static_cast<float>(i) * 26.0f + 12, ac == i, 7);
                        d.c.Yazi(dx + 22, Taban(dy + static_cast<float>(i) * 26.0f, 24, 12), Tr(s[i]), 12, tema::Agirlik::Normal, R.metin);
                    }
                    a.arayuz.acilis = ac == 1 ? "son_proje" : (ac == 2 ? "bos" : "baslangic");
                }
                if (Satir(d, "Açılışta Başlangıç panelini göster", nullptr, a.arayuz.baslangicPaneli != v.arayuz.baslangicPaneli, Tr("Açık"), 28, dx, dy))
                    degisti |= AnahtarDenetimi(d.c, "##baslangic_paneli", dx, dy, a.arayuz.baslangicPaneli);
            }
            KartBitir(d);
            KartBasla(d, "Kayıt ve kurtarma", "kaydet", 0);
            if (Satir(d, "Otomatik kayıt", "Kurtarma dosyası; çökme sonrası açılışta geri yükleme önerilir",
                      a.dosya.otomatikKayit != v.dosya.otomatikKayit, Tr("Açık"), 28, dx, dy))
                degisti |= AnahtarDenetimi(d.c, "##oto_kayit", dx, dy, a.dosya.otomatikKayit);
            {
                const float sw = SegmentGenisligi(d.c, {"2 dk", "5 dk", "10 dk", "15 dk"});
                if (Satir(d, "Kayıt aralığı", nullptr, a.dosya.otomatikKayitDk != v.dosya.otomatikKayitDk, "5 dk", sw, dx, dy))
                    degisti |= SegmentDenetimi<int>(d.c, "##kayit_dk", dx, dy, sw, a.dosya.otomatikKayitDk,
                                                    {{2, "2 dk"}, {5, "5 dk"}, {10, "10 dk"}, {15, "15 dk"}}, a.dosya.otomatikKayit);
            }
            if (Satir(d, "Kaydederken yedek al (.op4.bak)", nullptr, a.dosya.yedekBak != v.dosya.yedekBak, Tr("Kapalı"), 28, dx, dy))
                degisti |= AnahtarDenetimi(d.c, "##yedek", dx, dy, a.dosya.yedekBak);
            KartBitir(d);
            KartBasla(d, "Geri al", "geri_al", 0);
            if (Satir(d, "Geri al derinliği", "Adım sayısı (10–1000)", a.cekirdek.geriAlAdim != v.cekirdek.geriAlAdim,
                      std::to_string(v.cekirdek.geriAlAdim), 220, dx, dy)) {
                double g = a.cekirdek.geriAlAdim;
                if (KaydiriciDenetim(d.c, "##geri_al", dx, dy, 220, g, 10, 1000, "%.0f")) {
                    a.cekirdek.geriAlAdim = static_cast<int>(g);
                    degisti = true;
                }
            }
            if (Satir(d, "Bellek sınırı", "Geri alma geçmişi (MB)", a.cekirdek.geriAlMb != v.cekirdek.geriAlMb,
                      std::to_string(v.cekirdek.geriAlMb), 220, dx, dy)) {
                double g = a.cekirdek.geriAlMb;
                if (KaydiriciDenetim(d.c, "##geri_al_mb", dx, dy, 220, g, 64, 4096, "%.0f MB")) {
                    a.cekirdek.geriAlMb = static_cast<int>(g);
                    degisti = true;
                }
            }
            KartBitir(d);
            KartBasla(d, "Varsayılan birimler", "olcu", 1);
            {
                const float sw = SegmentGenisligi(d.c, {"kN", "tf"});
                if (Satir(d, "Kuvvet", "Yeni projelerde geçerli", a.arayuz.varsayilanKuvvet != v.arayuz.varsayilanKuvvet, "kN", sw, dx, dy))
                    degisti |= SegmentDenetimi<std::string>(d.c, "##kuvvet", dx, dy, sw, a.arayuz.varsayilanKuvvet, {{"kN", "kN"}, {"tf", "tf"}});
                const float uw = SegmentGenisligi(d.c, {"mm", "cm", "m"});
                if (Satir(d, "Uzunluk", nullptr, a.arayuz.varsayilanUzunluk != v.arayuz.varsayilanUzunluk, "m", uw, dx, dy))
                    degisti |= SegmentDenetimi<std::string>(d.c, "##uzunluk", dx, dy, uw, a.arayuz.varsayilanUzunluk,
                                                            {{"mm", "mm"}, {"cm", "cm"}, {"m", "m"}});
            }
            KartBitir(d);
            KartBasla(d, "Fare ve gezinme", "imlec", 1);
            if (Satir(d, "Fare eşlemesi", "op4: sol sürükle kaydır, Shift + sol döndür, Ctrl + sol pencere",
                      a.arayuz.fareEslemesi != v.arayuz.fareEslemesi, "op4", 220, dx, dy))
                degisti |= AcilirDenetim(d.c, "##fare", dx, dy, 220, a.arayuz.fareEslemesi,
                                         {{"op4", "op4 varsayılanı"}, {"klasik", "Klasik CAD (orta tuş kaydır)"}});
            KartBitir(d);
            // Diğer paketlerin ayar sayfaları (S21 AyarSayfasi): hesap motoru, dosya, çekirdek …
            if (h_.arayuz)
                for (const AyarSayfasi& s : h_.arayuz->AyarSayfalari()) {
                    if (s.sahip == "C" || !s.ciz) continue;
                    KartBasla(d, s.baslik.c_str(), "analiz", 1);
                    if (Satir(d, s.baslik.c_str(), nullptr, false, "", d.kolW - 32, dx, dy, 160)) {
                        ImGui::SetCursorScreenPos(d.c.P(d.kx + 16, d.y - 160 + 8));
                        ImGui::BeginChild(s.id.c_str(), d.c.P(d.kolW - 32, 144), ImGuiChildFlags_None);
                        ImGui::PushItemWidth(d.c.S(200));
                        s.ciz(a);
                        ImGui::PopItemWidth();
                        ImGui::EndChild();
                    }
                    KartBitir(d);
                }
        }
        // ===== Görüntü ayarları
        if (sayfaGoster(1)) {
            if (aramada) d.kolY[0] = d.kolY[1] = std::max(d.kolY[0], d.kolY[1]);
            KartBasla(d, "Grafik", "pencere", 0);
            if (Satir(d, "Grafik bağdaştırıcısı", "Değişiklik program yeniden açılınca uygulanır", !a.grafik.bagdastirici.empty(),
                      Tr("Otomatik"), 240, dx, dy)) {
                std::vector<std::pair<std::string, std::string>> s{{"", Tr("Otomatik — yüksek performanslı")}};
                for (const std::string& b : bagdastiricilar) s.push_back({b, b});
                degisti |= AcilirDenetim(d.c, "##bagdastirici", dx, dy, 240, a.grafik.bagdastirici, s);
            }
            {
                const float sw = SegmentGenisligi(d.c, {"Otomatik", "Kapalı", "2×", "4×", "8×"});
                if (Satir(d, "Kenar yumuşatma (MSAA)", Trf("Etkin: %u× · yeniden açılınca", msaa).c_str(), a.grafik.msaa != v.grafik.msaa,
                          Tr("Otomatik"), sw, dx, dy))
                    degisti |= SegmentDenetimi<int>(d.c, "##msaa", dx, dy, sw, a.grafik.msaa,
                                                    {{0, "Otomatik"}, {1, "Kapalı"}, {2, "2×"}, {4, "4×"}, {8, "8×"}});
            }
            {
                const float sw = SegmentGenisligi(d.c, {"Taslak", "Dengeli", "Yüksek"});
                if (Satir(d, "Görüntü kalitesi", "Profil ayrıntısı ve eğri bölme (LOD ekran sapması)",
                          std::fabs(a.grafik.lodToleransPx - v.grafik.lodToleransPx) > 1e-9, Tr("Dengeli"), sw, dx, dy))
                    degisti |= SegmentDenetimi<double>(d.c, "##kalite", dx, dy, sw, a.grafik.lodToleransPx,
                                                       {{2.0, "Taslak"}, {0.5, "Dengeli"}, {0.25, "Yüksek"}});
            }
            if (Satir(d, "Dikey eşitleme", nullptr, a.grafik.dikeyEsitleme != v.grafik.dikeyEsitleme, Tr("Açık"), 28, dx, dy))
                degisti |= AnahtarDenetimi(d.c, "##vsync", dx, dy, a.grafik.dikeyEsitleme);
            if (Satir(d, "Yazılım işleyiciyi zorla", "Tanı amaçlı (WARP); yeniden açılınca", a.grafik.warpZorla != v.grafik.warpZorla,
                      Tr("Kapalı"), 28, dx, dy))
                degisti |= AnahtarDenetimi(d.c, "##warp", dx, dy, a.grafik.warpZorla);
            KartBitir(d);
            KartBasla(d, "Model görünümü", "kati", 0);
            {
                const float sw = SegmentGenisligi(d.c, {"Gradyan", "Düz"});
                if (Satir(d, "Arka plan", "Dikey gradyan · üst / alt", a.grafik.arkaPlan != v.grafik.arkaPlan, Tr("Gradyan"), sw + 64, dx, dy)) {
                    degisti |= SegmentDenetimi<std::string>(d.c, "##arka", dx, dy, sw, a.grafik.arkaPlan, {{"gradyan", "Gradyan"}, {"duz", "Düz"}});
                    d.c.Gradyan(dx + sw + 12, dy + 2, 52, 24, R.sahneUst, R.sahneAlt);
                    d.c.Yuv(dx + sw + 12, dy + 2, 52, 24, tema::belirtec::R.kucuk, 0, R.cizgi);
                }
            }
            if (Satir(d, "Eleman kenarı · çubuk çizgisi", nullptr, std::fabs(a.grafik.cubukKalinlik - v.grafik.cubukKalinlik) > 1e-9,
                      Sayi(v.grafik.cubukKalinlik, 1) + " px", 220, dx, dy))
                degisti |= KaydiriciDenetim(d.c, "##kenar", dx, dy, 220, a.grafik.cubukKalinlik, 0.5f, 3.0f, "%.1f px");
            if (Satir(d, "Seçim konturu", nullptr, std::fabs(a.grafik.seciliKalinlik - v.grafik.seciliKalinlik) > 1e-9,
                      Sayi(v.grafik.seciliKalinlik, 1) + " px", 220, dx, dy))
                degisti |= KaydiriciDenetim(d.c, "##secim_kontur", dx, dy, 220, a.grafik.seciliKalinlik, 1.0f, 4.0f, "%.1f px");
            {
                const float sw = SegmentGenisligi(d.c, {"Küçük", "Orta", "Büyük"});
                if (Satir(d, "Etiket boyutu", "Aks balonu, kat ve ölçü etiketleri", std::fabs(a.arayuz.etiketBoyu - v.arayuz.etiketBoyu) > 1e-9,
                          Tr("Orta"), sw, dx, dy))
                    degisti |= SegmentDenetimi<double>(d.c, "##etiket", dx, dy, sw, a.arayuz.etiketBoyu,
                                                       {{10.0, "Küçük"}, {11.0, "Orta"}, {13.0, "Büyük"}});
            }
            KartBitir(d);
            KartBasla(d, "Seçim ve üzerinde", "imlec", 1);
            if (Satir(d, "Önizleme", nullptr, false, "", d.kolW - 32, dx, dy, 84)) {
                // canlı örnek: seçili (2 px + hale) · üzerinde (1 px) · normal
                const float px0 = d.kx + 16, py0 = d.y - 84 + 6, pw = d.kolW - 32;
                d.c.Yuv(px0, py0, pw, 72, tema::belirtec::R.orta, R.zemin2);
                const float cy1 = py0 + 30, cy2 = py0 + 58, x0 = px0 + 20, x1 = px0 + pw * 0.45f, x2 = px0 + pw * 0.55f, x3 = px0 + pw - 20;
                for (float hk : {9.0f, 6.0f, 3.5f}) d.c.Cizgi(x0, cy1, x1, cy1, tema::Alfa(R.secim, 0.18f), static_cast<float>(a.grafik.seciliKalinlik) + hk);
                d.c.Cizgi(x0, cy1, x1, cy1, R.secim, static_cast<float>(a.grafik.seciliKalinlik));
                d.c.Cizgi(x0, cy2, x1, cy2, R.uzerinde, static_cast<float>(a.grafik.cubukKalinlik) + 0.6f);
                d.c.Cizgi(x2, cy1, x3, cy1, R.cubukKiris, static_cast<float>(a.grafik.cubukKalinlik));
                d.c.Yazi(x0, py0 + 16, Tr("Seçili"), 10, tema::Agirlik::Kalin, R.vurguMetin);
                d.c.Yazi(x0, py0 + 47, Tr("Üzerinde"), 10, tema::Agirlik::Kalin, R.metin2);
                d.c.Yazi(x2, py0 + 16, Tr("Normal"), 10, tema::Agirlik::Kalin, R.metin2);
            }
            if (Satir(d, "Vurgu rengini izle", "Seçim rengi arayüz vurgusuyla aynı kalır", a.grafik.vurguyuIzle != v.grafik.vurguyuIzle,
                      Tr("Açık"), 28, dx, dy))
                degisti |= AnahtarDenetimi(d.c, "##izle", dx, dy, a.grafik.vurguyuIzle);
            if (Satir(d, "Seçim · üzerinde rengi", "İzleme açıkken salt okunur", false, "", 216, dx, dy)) {
                degisti |= RenkDenetimi(d.c, "##secim_rengi", dx, dy, a.grafik.secimRengi, !a.grafik.vurguyuIzle);
                degisti |= RenkDenetimi(d.c, "##uzerinde_rengi", dx + 112, dy, a.grafik.uzerindeRengi, !a.grafik.vurguyuIzle);
            }
            KartBitir(d);
            KartBasla(d, "Arayüz", "etiket", 1);
            {
                float cw = 0;
                for (int i = 0; i < tema::belirtec::PALET_SAYISI; ++i) cw += d.c.Gen(Tr(tema::belirtec::PALETLER[i].ad), 11, tema::Agirlik::Kalin) + 36;
                if (Satir(d, "Vurgu rengi", "Anlamsal renkler (D/C, uyarı) değişmez", a.arayuz.vurgu != v.arayuz.vurgu, Tr("Kobalt mavisi"), cw,
                          dx, dy)) {
                    float x = dx;
                    for (int i = 0; i < tema::belirtec::PALET_SAYISI; ++i) {
                        const auto& pl = tema::belirtec::PALETLER[i];
                        const char* ad = Tr(pl.ad);
                        const float w = d.c.Gen(ad, 11, tema::Agirlik::Kalin) + 30;
                        const bool sec = a.arayuz.vurgu == pl.kimlik;
                        ImGui::PushID(400 + i);
                        if (Tiklama(d.c, "##palet", x, dy, w, 28) && !sec) {
                            a.arayuz.vurgu = pl.kimlik;
                            degisti = true;
                        }
                        ImGui::PopID();
                        d.c.Yuv(x, dy, w, 28, tema::belirtec::R.orta, sec ? R.vurguTon : R.yuzey, sec ? R.vurgu : R.dugmeKenar, sec ? 1.5f : 1.0f);
                        d.c.Daire(x + 13, dy + 14, 6, tema::Renk(pl.r.vurgu));
                        if (pl.r.secim != pl.r.vurgu) d.c.Daire(x + 13, dy + 14, 2.5f, tema::Renk(pl.r.secim));
                        d.c.Yazi(x + 24, Taban(dy, 28, 11), ad, 11, tema::Agirlik::Kalin, sec ? R.vurguMetin : R.metin);
                        x += w + 6;
                    }
                }
            }
            {
                const float sw = SegmentGenisligi(d.c, {"Rahat", "Sıkı", "Otomatik"});
                if (Satir(d, "Yoğunluk", "Sıkı: 1600 × 900 altında otomatik", a.arayuz.yogunluk != v.arayuz.yogunluk, Tr("Otomatik"), sw, dx, dy))
                    degisti |= SegmentDenetimi<std::string>(d.c, "##yogunluk", dx, dy, sw, a.arayuz.yogunluk,
                                                            {{"rahat", "Rahat"}, {"siki", "Sıkı"}, {"otomatik", "Otomatik"}});
            }
            if (Satir(d, "Açılış ekranı", "Logo ve canlandırma aynı; yalnız zemin", a.arayuz.acilisEkrani != v.arayuz.acilisEkrani,
                      Tr("Açık"), 2 * 132 + 12, dx, dy, 112)) {
                for (int i = 0; i < 2; ++i) {
                    const bool koyu = i == 1, sec = (a.arayuz.acilisEkrani == "koyu") == koyu;
                    const float x = dx + static_cast<float>(i) * 144;
                    ImGui::PushID(500 + i);
                    if (Tiklama(d.c, "##acilis_ekrani", x, dy, 132, 96) && !sec) {
                        a.arayuz.acilisEkrani = koyu ? "koyu" : "acik";
                        degisti = true;
                    }
                    ImGui::PopID();
                    AcilisKucukResmi(d.c, x, dy, 132, 72, koyu, sec);
                    d.c.Radyo(x + 8, dy + 86, sec, 6);
                    d.c.Yazi(x + 20, Taban(dy + 78, 16, 11), Tr(koyu ? "Koyu" : "Açık · varsayılan"), 11,
                             sec ? tema::Agirlik::Kalin : tema::Agirlik::Normal, R.metin);
                }
            }
            KartBitir(d);
        }
        // ===== Dil ayarları
        if (sayfaGoster(2)) {
            if (aramada) d.kolY[0] = d.kolY[1] = std::max(d.kolY[0], d.kolY[1]);
            KartBasla(d, "Arayüz dili", "dil", 0);
            if (Satir(d, "Dil", "Yeniden başlatmadan uygulanır", a.arayuz.dil != v.arayuz.dil, "Türkçe", 2 * 120 + 8, dx, dy, 76)) {
                static const char* const kod[2] = {"tr", "en"};
                static const char* const ad[2] = {"Türkçe", "English"};
                static const char* const ornek[2] = {"Kesit · Başlangıç ucu", "Section · Start release"};
                for (int i = 0; i < 2; ++i) {
                    const bool sec = a.arayuz.dil == kod[i];
                    const float x = dx + static_cast<float>(i) * 128;
                    ImGui::PushID(600 + i);
                    if (Tiklama(d.c, "##dil", x, dy, 120, 58) && !sec) {
                        a.arayuz.dil = kod[i];
                        degisti = true;
                    }
                    ImGui::PopID();
                    d.c.Yuv(x, dy, 120, 58, tema::belirtec::R.orta, sec ? R.vurguTon : R.yuzey, sec ? R.vurgu : R.dugmeKenar, sec ? 1.5f : 1.0f);
                    d.c.Radyo(x + 14, dy + 18, sec, 6);
                    d.c.Yazi(x + 26, Taban(dy + 8, 20, 12), ad[i], 12, tema::Agirlik::Kalin, sec ? R.vurguMetin : R.metin);
                    d.c.Yazi(x + 10, Taban(dy + 32, 20, 10), ornek[i], 10, tema::Agirlik::Normal, R.metin3, 104);
                }
            }
            KartBitir(d);
            KartBasla(d, "Sayı ve tarih", "olcu", 0);
            {
                const float sw = SegmentGenisligi(d.c, {"Virgül (1,5)", "Nokta (1.5)"});
                if (Satir(d, "Ondalık ayırıcı", nullptr, a.arayuz.ondalik != v.arayuz.ondalik, Tr("Virgül"), sw, dx, dy))
                    degisti |= SegmentDenetimi<std::string>(d.c, "##ondalik", dx, dy, sw, a.arayuz.ondalik,
                                                            {{"virgul", "Virgül (1,5)"}, {"nokta", "Nokta (1.5)"}});
                const float bw = SegmentGenisligi(d.c, {"İnce boşluk", "Yok"});
                if (Satir(d, "Binlik ayırıcı", nullptr, a.arayuz.binlikAyirici != v.arayuz.binlikAyirici, Tr("İnce boşluk"), bw, dx, dy))
                    degisti |= SegmentDenetimi<bool>(d.c, "##binlik", dx, dy, bw, a.arayuz.binlikAyirici, {{true, "İnce boşluk"}, {false, "Yok"}});
                if (Satir(d, "Örnek", nullptr, false, "", 200, dx, dy))
                    d.c.YaziSag(dx + 200, Taban(dy, 28, 12), Sayi(12345.678, 3) + " kN", 12, tema::Agirlik::Orta, R.metin);
            }
            KartBitir(d);
            KartBasla(d, "Birim sistemi", "olcu", 1);
            {
                const float sw = SegmentGenisligi(d.c, {"kN · m", "tf · m"});
                if (Satir(d, "Birim sistemi", "4,20 kN/m ⇄ 0,428 tf/m", a.arayuz.birimSistemi != v.arayuz.birimSistemi, "kN · m", sw, dx, dy))
                    degisti |= SegmentDenetimi<std::string>(d.c, "##birim", dx, dy, sw, a.arayuz.birimSistemi, {{"SI", "kN · m"}, {"teknik", "tf · m"}});
            }
            KartBitir(d);
            KartBasla(d, "Komut takma adları", "konsol", 1);
            if (Satir(d, "İngilizce takma adlar", "kolon = column, kiriş = beam (her iki dilde geçerli)", false, "", 28, dx, dy)) {
                bool her = true;
                AnahtarDenetimi(d.c, "##ing", dx, dy, her, false);
            }
            if (Satir(d, "Esnek Türkçe eşleme", "i/ı · s/ş · c/ç · g/ğ · o/ö · u/ü aynı sayılır", false, "", 28, dx, dy)) {
                bool her = true;
                AnahtarDenetimi(d.c, "##esnek", dx, dy, her, false);
            }
            KartBitir(d);
        }
        if (aramada && konumlar.empty())
            d.c.Yazi(d.ox, d.oy + 20, Tr("Eşleşen ayar yok."), 12, tema::Agirlik::Normal, R.metin3);
        if (!aramada) bolumKonumlari = konumlar;
        ImGui::SetCursorScreenPos(d.c.P(d.ox, d.oy));
        ImGui::Dummy(d.c.P(1, std::max(d.kolY[0], d.kolY[1]) + 24));
    }
    ImGui::EndChild();
    ImGui::PopStyleColor();
    if (degisti) AyarlariUygula();  // canlı önizleme; İptal eski duruma döner
    // ---- alt çubuk 64
    const float fy = Y + H - fh;
    k.Dikd(X, fy, W, 1, R.cizgi);
    if (Tiklama(k, "##varsayilana", X + 16, fy + 16, 156, 32)) ImGui::OpenPopup("##varsayilana_menu");
    const bool vu = ImGui::IsItemHovered();
    k.Dugme(X + 16, fy + 16, 156, 32, "", false, 12, false, vu);
    k.Simge("geri_yukle", X + 34, fy + 32, 14, R.ikonBuyuk, 1.5f);
    k.Yazi(X + 48, Taban(fy + 16, 32, 12), Tr("Varsayılana dön"), 12, tema::Agirlik::Orta, R.metin);
    k.Sevron(X + 160, fy + 32, 0, 9, R.metin2);
    if (W > 1100) k.Yazi(X + 188, Taban(fy, fh, 11), Tr("Bu sayfa ya da tüm ayarlar"), 11, tema::Agirlik::Normal, R.metin3);
    if (ImGui::BeginPopup("##varsayilana_menu")) {
        if (ImGui::MenuItem(Tr("Bu sayfayı varsayılana döndür"))) {
            if (ayarSayfasi == 0) {
                a.arayuz.acilis = v.arayuz.acilis;
                a.arayuz.baslangicPaneli = v.arayuz.baslangicPaneli;
                a.arayuz.varsayilanKuvvet = v.arayuz.varsayilanKuvvet;
                a.arayuz.varsayilanUzunluk = v.arayuz.varsayilanUzunluk;
                a.arayuz.fareEslemesi = v.arayuz.fareEslemesi;
                a.dosya.otomatikKayit = v.dosya.otomatikKayit;
                a.dosya.otomatikKayitDk = v.dosya.otomatikKayitDk;
                a.dosya.yedekBak = v.dosya.yedekBak;
                a.cekirdek.geriAlAdim = v.cekirdek.geriAlAdim;
                a.cekirdek.geriAlMb = v.cekirdek.geriAlMb;
            } else if (ayarSayfasi == 1) {
                a.grafik = v.grafik;
                a.arayuz.vurgu = v.arayuz.vurgu;
                a.arayuz.yogunluk = v.arayuz.yogunluk;
                a.arayuz.etiketBoyu = v.arayuz.etiketBoyu;
                a.arayuz.acilisEkrani = v.arayuz.acilisEkrani;
            } else {
                a.arayuz.dil = v.arayuz.dil;
                a.arayuz.ondalik = v.arayuz.ondalik;
                a.arayuz.binlikAyirici = v.arayuz.binlikAyirici;
                a.arayuz.birimSistemi = v.arayuz.birimSistemi;
            }
            AyarlariUygula();
        }
        if (ImGui::MenuItem(Tr("Tüm ayarları varsayılana döndür"))) {
            Ayarlar y{};
            y.dosya.sonDosyalar = a.dosya.sonDosyalar;
            y.dosya.sonKlasor = a.dosya.sonKlasor;
            y.bilinmeyen = a.bilinmeyen;
            a = y;
            AyarlariUygula();
        }
        ImGui::EndPopup();
    }
    // değişiklik sayısı: önceki anlık görüntüyle JSON yaprak farkı
    int fark = 0;
    if (ayarOnceki_) {
        const nlohmann::json j0 = nlohmann::json::parse(AyarlariYaz(*ayarOnceki_), nullptr, false);
        const nlohmann::json j1 = nlohmann::json::parse(AyarlariYaz(a), nullptr, false);
        if (!j0.is_discarded() && !j1.is_discarded()) fark = static_cast<int>(nlohmann::json::diff(j0, j1).size());
    }
    const float bw = 92, by = fy + 16;
    const float bx3 = X + W - 16 - bw, bx2 = bx3 - 10 - bw, bx1 = bx2 - 10 - bw;
    if (fark > 0) {
        const std::string m = Trf("%d değişiklik · Uygula pencereyi açık tutar", fark);
        const float mw = k.Gen(m, 11, tema::Agirlik::Normal);
        k.Daire(bx1 - 24 - mw, fy + fh / 2, 3, R.vurgu);
        k.Yazi(bx1 - 16 - mw, Taban(fy, fh, 11), m, 11, tema::Agirlik::Normal, R.metin2);
    }
    if (Tiklama(k, "##ay_iptal", bx1, by, bw, 32) || (ImGui::IsKeyPressed(ImGuiKey_Escape) && !ImGui::IsAnyItemActive())) iptal();
    k.Dugme(bx1, by, bw, 32, Tr("İptal"), false, 12, false, ImGui::IsItemHovered());
    if (Tiklama(k, "##ay_uygula", bx2, by, bw, 32) && fark > 0) uygula();
    k.Dugme(bx2, by, bw, 32, Tr("Uygula"), false, 12, fark == 0, ImGui::IsItemHovered());
    if (Tiklama(k, "##ay_tamam", bx3, by, bw, 32) || (ImGui::IsKeyPressed(ImGuiKey_Enter) && !ImGui::IsAnyItemActive())) {
        uygula();
        ayarlarAcik = false;
    }
    k.Dugme(bx3, by, bw, 32, Tr("Tamam"), true, 12, false, ImGui::IsItemHovered());
    if (!ayarlarAcik) ImGui::CloseCurrentPopup();
    ImGui::EndPopup();
}

void AnaPencere::HizliAksPenceresi(Ciz& c) {
    if (!hizliAksAcik_) return;
    const ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowSize(c.P(420, 0), ImGuiCond_Appearing);
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.4f), ImGuiCond_Appearing, ImVec2(0.5f, 0.5f));
    if (ImGui::Begin(Tr("Hızlı aks"), &hizliAksAcik_, ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_AlwaysAutoResize)) {
        ImGui::TextWrapped("%s", Tr("Aks aralıkları ve kat yükseklikleri (m, boşlukla ayrılmış; ondalık virgül geçerli)."));
        ImGui::PushItemWidth(c.S(220));
        ImGui::InputText(Tr("X aralıkları"), hizliAksX_, sizeof(hizliAksX_));
        ImGui::InputText(Tr("Y aralıkları"), hizliAksY_, sizeof(hizliAksY_));
        ImGui::InputText(Tr("Kat yükseklikleri"), hizliAksZ_, sizeof(hizliAksZ_));
        ImGui::PopItemWidth();
        if (ImGui::Button(Tr("Uygula"), c.P(96, 26))) {
            // boşluklar argüman ayracıdır: alan içindeki değerler ';' ile taşınır
            std::string a2;
            for (const char* p : {"x=", "y=", "z="}) {
                const char* kaynak = p[0] == 'x' ? hizliAksX_ : p[0] == 'y' ? hizliAksY_ : hizliAksZ_;
                std::string v = kaynak;
                for (char& ch : v)
                    if (ch == ' ') ch = ';';
                a2 += std::string(p) + v + " ";
            }
            KomutCalistir("model.hizli_aks", KomutKaynagi::Menu, a2);
            hizliAksAcik_ = false;
        }
        ImGui::SameLine();
        if (ImGui::Button(Tr("Kapat"), c.P(96, 26))) hizliAksAcik_ = false;
    }
    ImGui::End();
}

void AnaPencere::BilgiPencereleri(Ciz& c) {
    const ImGuiIO& io = ImGui::GetIO();
    if (kisayollarAcik_) {
        ImGui::SetNextWindowSize(c.P(520, 460), ImGuiCond_Appearing);
        ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f), ImGuiCond_Appearing, ImVec2(0.5f, 0.5f));
        if (ImGui::Begin(Tr("Kısayollar"), &kisayollarAcik_, ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoDocking) && h_.komutlar) {
            if (ImGui::BeginTable("##kisayol", 3, ImGuiTableFlags_RowBg | ImGuiTableFlags_ScrollY)) {
                ImGui::TableSetupColumn(Tr("Kısayol"));
                ImGui::TableSetupColumn(Tr("Komut"));
                ImGui::TableSetupColumn(Tr("Komut satırı"));
                ImGui::TableHeadersRow();
                for (const KomutTanimi& t : h_.komutlar->Tanimlar()) {
                    if (t.kisayol.empty()) continue;
                    ImGui::TableNextRow();
                    ImGui::TableNextColumn();
                    ImGui::TextUnformatted(t.kisayol.c_str());
                    ImGui::TableNextColumn();
                    ImGui::TextUnformatted(Tr(t.etiket.c_str()));
                    ImGui::TableNextColumn();
                    ImGui::TextDisabled("%s", t.ad.c_str());
                }
                const std::pair<const char*, const char*> fare[] = {
                    {"Sol sürükle", "Kaydır"}, {"Shift + sol sürükle", "Döndür"}, {"Tekerlek", "İmlece yakınlaş"},
                    {"Orta sürükle", "Kaydır"}, {"Ctrl + sol sürükle", "Pencere seçimi"}, {"Ctrl+Q", "Hızlı başlat"}};
                for (const auto& [k, ad] : fare) {
                    ImGui::TableNextRow();
                    ImGui::TableNextColumn();
                    ImGui::TextUnformatted(Tr(k));
                    ImGui::TableNextColumn();
                    ImGui::TextUnformatted(Tr(ad));
                }
                ImGui::EndTable();
            }
        }
        ImGui::End();
    }
    if (hakkindaAcik_) {
        ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f), ImGuiCond_Appearing, ImVec2(0.5f, 0.5f));
        if (ImGui::Begin(Tr("op4 hakkında"), &hakkindaAcik_, ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_AlwaysAutoResize)) {
            ImGui::Text("op4 %s — Opus Fortis", h_.bilgi.surum.c_str());
            ImGui::TextDisabled("%s", Tr("Yapısal modelleme, analiz ve tasarım"));
            ImGui::Separator();
            ImGui::TextDisabled("%s: %s · MSAA %u×", Tr("Grafik"), bagdastirici.c_str(), msaa);
            ImGui::TextDisabled("Dear ImGui (MIT) · Inter, Cormorant Garamond (SIL OFL 1.1) · nlohmann/json (MIT)");
        }
        ImGui::End();
    }
}

void AnaPencere::SihirbazPenceresi(Ciz& c) {
    (void)c;
    if (sihirbazId_.empty() || !h_.arayuz) return;
    const IletisimKaydi* k = h_.arayuz->Iletisim(sihirbazId_);
    if (!k || !k->ciz) {
        sihirbazId_.clear();
        if (sihirbazSonrasi_) sihirbazSonrasi_();
        sihirbazSonrasi_ = nullptr;
        return;
    }
    const int s = k->ciz();
    if (s == 0) return;
    sihirbazId_.clear();
    auto sonra = std::move(sihirbazSonrasi_);
    sihirbazSonrasi_ = nullptr;
    if (s > 0 && sonra) sonra();
}

}  // namespace op4
