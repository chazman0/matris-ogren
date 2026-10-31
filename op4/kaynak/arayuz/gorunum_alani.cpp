// op4 arayüzü — görünüm alanı: görünüm sekmeleri, sahne dokusu, çubuk görünümü çizimi (sabit piksel kalınlığı, düğümler,
// mafsal ve mesnet simgeleri, akslar ve balonlar, kat seviyeleri, ekran uzayı etiketleri), vurgu, araç pili, dört düğme,
// eksen üçlüsü, seçim notları (tutamaçlar, ölçü, mini araç çubuğu, üzerinde ipucu) ve fare girdisi (MIMARI §6.5, §6.8,
// §6.9, §7.1; atolye uret.py gorunum_sekmeleri, viewport, secim_notlari).
#include <algorithm>
#include <cmath>
#include <cstring>

#include "arayuz/ana_pencere.h"
#include "arayuz/dil.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/komut.h"
#include "cekirdek/secim.h"

namespace op4 {
namespace {

struct K4 {
    double x, y, z, w;
};
K4 Kirp(const GorusIzdusumu& g, V3d p) {
    const auto& m = g.gorunumIzdusum;
    return {m[0] * p.x + m[1] * p.y + m[2] * p.z + m[3], m[4] * p.x + m[5] * p.y + m[6] * p.z + m[7],
            m[8] * p.x + m[9] * p.y + m[10] * p.z + m[11], m[12] * p.x + m[13] * p.y + m[14] * p.z + m[15]};
}
inline double Yari(const K4& c) { return std::min(c.w - c.z, c.w); }

// İzdüşüm yardımcısı: dünya → ekran pikseli (görüş alanı ofsetiyle).
struct Izd {
    GorusIzdusumu g;
    float ox, oy;
    bool Nokta(V3d p, ImVec2& o) const {
        const K4 c = Kirp(g, p);
        if (Yari(c) < 0 || c.w <= 1e-12) return false;
        o = ImVec2(ox + static_cast<float>((c.x / c.w * 0.5 + 0.5) * g.genislik),
                   oy + static_cast<float>((0.5 - c.y / c.w * 0.5) * g.yukseklik));
        return true;
    }
    // Yakın düzleme göre kırpılmış parça.
    bool Parca(V3d a, V3d b, ImVec2& pa, ImVec2& pb) const {
        K4 ca = Kirp(g, a), cb = Kirp(g, b);
        const double ha = Yari(ca), hb = Yari(cb);
        if (ha < 0 && hb < 0) return false;
        if (ha < 0 || hb < 0) {
            const double t = ha / (ha - hb);
            const K4 k{ca.x + (cb.x - ca.x) * t, ca.y + (cb.y - ca.y) * t, ca.z + (cb.z - ca.z) * t, ca.w + (cb.w - ca.w) * t};
            (ha < 0 ? ca : cb) = k;
        }
        if (ca.w <= 1e-12 || cb.w <= 1e-12) return false;
        auto e = [&](const K4& c) {
            return ImVec2(ox + static_cast<float>((c.x / c.w * 0.5 + 0.5) * g.genislik),
                          oy + static_cast<float>((0.5 - c.y / c.w * 0.5) * g.yukseklik));
        };
        pa = e(ca);
        pb = e(cb);
        return true;
    }
};

void KesikCizgi(ImDrawList* dl, ImVec2 a, ImVec2 b, ImU32 c, float kal, float kesik, float bosluk) {
    const float dx = b.x - a.x, dy = b.y - a.y, L = std::sqrt(dx * dx + dy * dy);
    if (L < 0.5f) return;
    const float ux = dx / L, uy = dy / L;
    for (float t = 0; t < L; t += kesik + bosluk) {
        const float t2 = std::min(L, t + kesik);
        dl->AddLine(ImVec2(a.x + ux * t, a.y + uy * t), ImVec2(a.x + ux * t2, a.y + uy * t2), c, kal);
    }
}

const char* Pusula(double sapma) {
    // Göz yönü (hedeften göze): +X doğu, +Y kuzey.
    static const char* const yonler[8] = {"doğu", "kuzey-doğu", "kuzey", "kuzey-batı", "batı", "güney-batı", "güney", "güney-doğu"};
    double d = sapma * 180.0 / 3.14159265358979;
    d = std::fmod(d + 360.0 * 4 + 22.5, 360.0);
    return yonler[static_cast<int>(d / 45.0) & 7];
}

}  // namespace

// ---- görünüm sekmeleri ---------------------------------------------------------------------------------------------------
void AnaPencere::GorunumSekmeleriCiz(Ciz& c) {
    const auto& R = c.R();
    const float x0 = L_.vpX0, y0 = L_.ust, w = L_.vpX1 - L_.vpX0, h = L_.gsekme;
    c.Dikd(x0, y0, w, h, R.zemin);
    c.Yatay(x0, x0 + w, y0 + h - 1, R.cizgi);
    struct Sekme {
        std::string ad;
        StandartYon yon;
        const char* ikon;
    };
    std::vector<Sekme> sekmeler{{Tr("3B görünüm"), StandartYon::Izometrik, "bina3"},
                                {std::string(Tr("Plan")) + " – " + KatAdi(etkinKat), StandartYon::Plan, "plan"},
                                {std::string(Tr("Yükselti")) + " – " + Tr("Ön"), StandartYon::On, "yukselti"}};
    if (etkinKat < 0) sekmeler[1].ad = Tr("Plan");
    // Belge sekmeleri (§6): etkin olan üst köşeleri 6 px yuvarlak, görünüme kesintisiz bağlanır, simgesi vurgu.
    float x = x0 + 8;
    const float r6 = tema::belirtec::R.orta;
    for (const Sekme& s : sekmeler) {
        const float tw = c.Gen(s.ad, 12, tema::Agirlik::Kalin) + 44;
        ImGui::PushID(static_cast<int>(s.yon));
        if (Tiklama(c, "##gsekme", x, y0 + 4, tw, h - 4)) StandartGorunum(s.yon);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        const bool etkin = yon_ == s.yon || (s.yon == StandartYon::On && yon_ == StandartYon::Yan);
        if (etkin) {
            c.dl->AddRectFilled(c.P(x, y0 + 4), c.P(x + tw, y0 + h), R.yuzey, c.S(r6), ImDrawFlags_RoundCornersTop);
            c.dl->AddRect(c.P(x + 0.5f, y0 + 4.5f), c.P(x + tw - 0.5f, y0 + h + 2), R.cizgi, c.S(r6), c.S(1), ImDrawFlags_RoundCornersTop);
            c.Dikd(x + 1, y0 + h - 1, tw - 2, 2, R.yuzey);
        } else if (ust) {
            c.Yuv(x + 2, y0 + 6, tw - 4, h - 10, r6, R.hover);
        }
        c.Simge(s.ikon, x + 18, y0 + 4 + (h - 4) / 2, 14, etkin ? R.vurgu : R.ikonKucuk, 1.4f);
        c.Yazi(x + 30, Taban(y0 + 4, h - 4, 12), s.ad, 12, etkin ? tema::Agirlik::Kalin : tema::Agirlik::Orta,
               etkin || ust ? R.metin : R.metin2);
        x += tw + 4;
    }
    c.Simge("arti", x + 12, y0 + h / 2 + 2, 13, R.ikonKucuk, 1.4f);
    if (!L_.dar)
        c.YaziSag(x0 + w - 12, Taban(y0, h, 10), Tr("Görünüm özellikleri: arka plana çift tık"), 10, tema::Agirlik::Normal, R.metin3);
}

// ---- görünüm -----------------------------------------------------------------------------------------------------------
void AnaPencere::GorunumCiz(Ciz& c, const SahneDokusu& d) {
    const auto& R = c.R();
    const float x0 = L_.vpX0, y0 = L_.vpY0, w = L_.vpX1 - L_.vpX0, h = L_.vpY1 - L_.vpY0;
    gorus_ = {c.S(x0), c.S(y0), std::max(1.0f, c.S(w)), std::max(1.0f, c.S(h))};
    gezinme_.Boyut(gorus_.g, gorus_.y2);
    gezinme_.dpiOlcek = olcek_;
    if (sigdirBekliyor_) Sigdir();
    c.dl->PushClipRect(c.P(x0, y0), c.P(x0 + w, y0 + h), true);
    if (d.kimlik != ImTextureID_Invalid) {
        c.dl->AddImage(ImTextureRef(d.kimlik), c.P(x0, y0), c.P(x0 + w, y0 + h), ImVec2(0, 0), ImVec2(d.uvG, d.uvY));
    } else {
        // Yedek (önizleme / doku yok): arka plan gradyanı ve Z = 0 ızgarası ImDrawList ile.
        c.Gradyan(x0, y0, w, h, R.sahneUst, R.sahneAlt);
        if (IzgaraGorunur()) {
            const Izd iz{Izdusum(), gorus_.x, gorus_.y};
            const Kutu3d k = sahne_->sinir;
            const double cx = k.Bos() ? 6.0 : std::round((k.enKucuk.x + k.enBuyuk.x) * 0.5);
            const double cy = k.Bos() ? 6.0 : std::round((k.enKucuk.y + k.enBuyuk.y) * 0.5);
            const int yari = k.Bos() ? 30 : static_cast<int>(std::max(k.enBuyuk.x - k.enKucuk.x, k.enBuyuk.y - k.enKucuk.y) * 0.5) + 12;
            for (int i = -yari; i <= yari; ++i) {
                const bool kalin = (static_cast<int>(cx) + i) % 5 == 0;
                const uint32_t renk = tema::Alfa(R.antrasit, kalin ? 0.10f : 0.05f);
                ImVec2 a, b;
                if (iz.Parca({cx + i, cy - yari, 0}, {cx + i, cy + yari, 0}, a, b)) c.dl->AddLine(a, b, renk, 1.0f);
                if (iz.Parca({cx - yari, cy + i, 0}, {cx + yari, cy + i, 0}, a, b)) c.dl->AddLine(a, b, renk, 1.0f);
            }
        }
    }
    SahneCiz(c);
    SecimNotlariCiz(c);

    // ---- araç pili (sol üst) ----
    const float px = x0 + 10, py = y0 + 10;
    struct Parca {
        const char* ikon;
        std::string metin;
        const char* popup;
    };
    const char* gorunumAdi = yon_ == StandartYon::Izometrik ? "3B" : yon_ == StandartYon::Plan ? "Plan" : yon_ == StandartYon::On ? "Ön" : "Yan";
    const char* renkKipi = h_.gorunum && h_.gorunum->renkKipi == RenkKipi::Sonuc ? "Renk: D/C" : "Renk: türe göre";
    std::vector<Parca> parcalar{{"bina3", Tr(gorunumAdi), "##p_gorunum"},
                                {"perspektif", Tr(kamera_.d.ortografik ? "Ortografik" : "Perspektif"), "##p_izdusum"},
                                {"katman", Tr(kapsam == KatKapsami::BuKat ? "Bu kat" : "Tüm katlar"), "##p_katlar"},
                                {"etiket", Tr(renkKipi), "##p_renk"}};
    // Görünüm pili (§6): beyaz %96, 1 px çizgi, 8 px, yüzen gölge, 32 px; çubuk ↔ ekstrüde simgeli segment.
    const float ph = 32, pr = tema::belirtec::R.buyuk;
    const auto& yg = tema::belirtec::GOLGE.yuzen;
    float pw = 8;
    for (const Parca& p : parcalar) pw += 18 + c.Gen(p.metin, 11, tema::Agirlik::Orta) + 12 + 16;
    pw += 60;
    c.Golge(px, py, pw, ph, pr, yg.bulaniklik * 0.6f, yg.saydamlik, yg.dy);
    c.Yuv(px, py, pw, ph, pr, tema::Alfa(R.yuzey, 0.96f), R.cizgi);
    Engel(px, py, pw, ph);
    float cx = px + 10;
    for (const Parca& p : parcalar) {
        const float pg = 18 + c.Gen(p.metin, 11, tema::Agirlik::Orta) + 12;
        if (Tiklama(c, p.popup, cx - 5, py + 4, pg + 8, ph - 8)) ImGui::OpenPopup(p.popup);
        if (ImGui::IsItemHovered()) c.Yuv(cx - 5, py + 4, pg + 8, ph - 8, tema::belirtec::R.orta, R.hover);
        c.Simge(p.ikon, cx + 7, py + ph / 2, 14, R.ikonKucuk, 1.3f);
        c.Yazi(cx + 18, Taban(py, ph, 11), p.metin, 11, tema::Agirlik::Orta, R.metin);
        cx += 18 + c.Gen(p.metin, 11, tema::Agirlik::Orta);
        c.Sevron(cx + 6, py + ph / 2 + 0.5f, 0, 9, R.metin2);
        cx += 12 + 8;
        c.Dusey(cx, py + 8, py + ph - 8, R.cizgi2);
        cx += 6;
    }
    // çubuk ↔ ekstrüzyon
    const bool kati = KesitGorunumu();
    if (Tiklama(c, "##kip_cubuk", cx, py + 4, 24, ph - 8)) KomutCalistir("gorunum.cubuk_kipi", KomutKaynagi::Serit);
    OgeIpucu(c, Tr("Çubuk görünümü"), "Ctrl+1");
    if (Tiklama(c, "##kip_kati", cx + 26, py + 4, 24, ph - 8)) KomutCalistir("gorunum.ekstruzyon", KomutKaynagi::Serit);
    OgeIpucu(c, Tr("Ekstrüzyon görünümü"), "Ctrl+4");
    c.Yuv(kati ? cx + 26 : cx, py + 4, 24, ph - 8, tema::belirtec::R.orta, R.vurguTon);
    c.Simge("cubuk", cx + 12, py + ph / 2, 14, kati ? R.ikonKucuk : R.vurgu, 1.4f);
    c.Simge("kati", cx + 38, py + ph / 2, 14, kati ? R.vurgu : R.ikonKucuk, 1.4f);
    // açılır pencereler
    if (ImGui::BeginPopup("##p_gorunum")) {
        if (ImGui::MenuItem(Tr("3B görünüm"), "Ctrl+Alt+1")) KomutCalistir("gorunum.3b", KomutKaynagi::Menu);
        if (ImGui::MenuItem(Tr("Plan"), "Ctrl+Alt+2")) KomutCalistir("gorunum.plan", KomutKaynagi::Menu);
        if (ImGui::MenuItem(Tr("Ön cephe"), "Ctrl+Alt+3")) KomutCalistir("gorunum.on", KomutKaynagi::Menu);
        if (ImGui::MenuItem(Tr("Yan cephe"), "Ctrl+Alt+4")) KomutCalistir("gorunum.yan", KomutKaynagi::Menu);
        ImGui::EndPopup();
    }
    if (ImGui::BeginPopup("##p_izdusum")) {
        if (ImGui::MenuItem(Tr("Perspektif"), nullptr, !kamera_.d.ortografik, yon_ == StandartYon::Izometrik)) kamera_.d.ortografik = false;
        if (ImGui::MenuItem(Tr("Ortografik"), nullptr, kamera_.d.ortografik)) {
            if (!kamera_.d.ortografik) {
                kamera_.d.ortoYukseklik = kamera_.PikselBoyu(gorus_.y2) * gorus_.y2;
                kamera_.d.ortografik = true;
            }
        }
        ImGui::EndPopup();
    }
    if (ImGui::BeginPopup("##p_katlar")) {
        if (ImGui::MenuItem(Tr("Tüm katlar"), nullptr, kapsam != KatKapsami::BuKat)) kapsam = KatKapsami::TumKatlar;
        if (ImGui::MenuItem(Tr("Yalnız etkin kat"), nullptr, kapsam == KatKapsami::BuKat)) kapsam = KatKapsami::BuKat;
        ImGui::EndPopup();
    }
    if (ImGui::BeginPopup("##p_renk")) {
        const bool sonucVar = h_.gorunum && h_.gorunum->sonuc;
        if (ImGui::MenuItem(Tr("Türe göre"), nullptr, !h_.gorunum || h_.gorunum->renkKipi == RenkKipi::Tur) && h_.gorunum)
            h_.gorunum->renkKipi = RenkKipi::Tur;
        if (ImGui::MenuItem(Tr("D/C oranı"), nullptr, h_.gorunum && h_.gorunum->renkKipi == RenkKipi::Sonuc, sonucVar))
            h_.gorunum->renkKipi = RenkKipi::Sonuc;
        ImGui::EndPopup();
    }

    // ---- sağ üst dört düğme (küp yok) ----
    struct Dugme {
        const char* ikon;
        const char* ipucu;
        const char* komut;
    };
    static const Dugme dugmeler[4] = {{"ev", "Tam görünüm", "gorunum.sigdir"},
                                      {"sigdir", "Seçiliye yakınlaş", "gorunum.secime_yakinlas"},
                                      {"kesit_duzlemi", "Kesit düzlemi (Faz 4)", ""},
                                      {"goz", "Gösterim seçenekleri", "*"}};
    {
        const float gw = 4 * 28 + 8, gx = x0 + w - 10 - gw;
        c.Golge(gx, py, gw, ph, pr, yg.bulaniklik * 0.6f, yg.saydamlik, yg.dy);
        c.Yuv(gx, py, gw, ph, pr, tema::Alfa(R.yuzey, 0.96f), R.cizgi);
        Engel(gx, py, gw, ph);
    }
    for (int i = 0; i < 4; ++i) {
        const float bx = x0 + w - 10 - 4 - static_cast<float>(4 - i) * 28;
        ImGui::PushID(200 + i);
        const bool tik = Tiklama(c, "##vpdugme", bx, py + 4, 28, ph - 8);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        const bool etkin = dugmeler[i].komut[0] && (dugmeler[i].komut[0] == '*' ||
                                                    (h_.komutlar && h_.komutlar->Durum(dugmeler[i].komut, h_).kullanilabilir));
        if (ust) c.Yuv(bx, py + 4, 28, ph - 8, tema::belirtec::R.orta, R.hover);
        c.Simge(dugmeler[i].ikon, bx + 14, py + ph / 2, 16, etkin ? R.ikonKucuk : R.ikonKapali, 1.4f);
        const auto* t = dugmeler[i].komut[0] && dugmeler[i].komut[0] != '*' && h_.komutlar ? h_.komutlar->Bul(dugmeler[i].komut) : nullptr;
        OgeIpucu(c, Tr(dugmeler[i].ipucu), t ? t->kisayol : std::string());
        if (!tik) continue;
        if (dugmeler[i].komut[0] == '*') ImGui::OpenPopup("##gosterim");
        else if (etkin) KomutCalistir(dugmeler[i].komut, KomutKaynagi::Serit);
    }
    if (ImGui::BeginPopup("##gosterim")) {
        bool izgara = IzgaraGorunur();
        if (ImGui::MenuItem(Tr("Izgara"), "F7", &izgara)) KomutCalistir("gorunum.izgara", KomutKaynagi::Menu);
        ImGui::MenuItem(Tr("Akslar"), nullptr, &akslarGorunur_);
        ImGui::MenuItem(Tr("Düğümler"), nullptr, &dugumlerGorunur_);
        ImGui::MenuItem(Tr("Eleman etiketleri"), nullptr, &etiketlerGorunur_);
        ImGui::MenuItem(Tr("Yalnız seçiliyi göster"), "Ctrl+5", &yalnizSecili);
        ImGui::EndPopup();
    }

    // ---- eksen üçlüsü (sol alt) ----
    {
        const float ox = x0 + 42, oy = y0 + h - 42;
        c.Daire(ox, oy, 30, tema::Alfa(R.yuzey, 0.55f), tema::Alfa(R.cizgi, 0.8f));
        const V3d sag = kamera_.Sag(), yuk = kamera_.Yukari();
        const struct {
            const char* ad;
            V3d v;
            uint32_t renk;
        } eksen[3] = {{"X", {1, 0, 0}, R.eksenX}, {"Y", {0, 1, 0}, R.eksenY}, {"Z", {0, 0, 1}, R.eksenZ}};
        for (const auto& e : eksen) {
            const float dx = static_cast<float>(Nokta(e.v, sag)), dy = static_cast<float>(Nokta(e.v, yuk));
            const float Ln = std::max(0.25f, std::sqrt(dx * dx + dy * dy));
            const float ex = ox + dx * 24, ey = oy - dy * 24;
            c.Cizgi(ox, oy, ex, ey, e.renk, 1.5f);
            c.Yazi(ex + dx / Ln * 9 - 3.5f, ey - dy / Ln * 9 + 4, e.ad, 10, tema::Agirlik::Kalin, e.renk);
        }
        c.Daire(ox, oy, 2.2f, R.metin2);
    }
    // ---- sağ alt: kamera bilgisi ----
    if (!L_.dar || w > 700) {
        std::string bilgi = kamera_.d.ortografik ? std::string(Tr("Ortografik"))
                                                 : Trf("Perspektif %d°", static_cast<int>(std::lround(kamera_.d.dikeyAci * 180.0 / 3.14159265358979)));
        if (yon_ == StandartYon::Izometrik) bilgi += " · " + std::string(Tr("Bakış")) + ": " + Tr(Pusula(kamera_.d.sapma));
        bilgi += " · " + std::string(Tr("Sol sürükle: kaydır")) + " · " + Tr("Shift+sol: döndür") + " · " + Tr("Tekerlek: yakınlaş");
        // gezinme çipi (§8, MIMARI §25 gezinme kuralı)
        const float bw = c.Gen(bilgi, 10, tema::Agirlik::Normal) + 20;
        c.Yuv(x0 + w - 10 - bw, y0 + h - 10 - 22, bw, 22, tema::belirtec::R.orta, tema::Alfa(R.yuzey, 0.9f), R.cizgi);
        c.Yazi(x0 + w - bw, Taban(y0 + h - 32, 22, 10), bilgi, 10, tema::Agirlik::Normal, R.metin2);
    }
    // ---- boş çalışma alanı ipucu ----
    if (SahneBos()) {
        const char* s1 = Tr("Boş model — Z = 0 çalışma ızgarası");
        const char* s2 = Tr("Başlangıç panelinden şablon seçin, Hızlı aks açın ya da komut yazın (Ctrl+Q).");
        const float bw = std::max(c.Gen(s1, 13, tema::Agirlik::Kalin), c.Gen(s2, 11, tema::Agirlik::Normal)) + 32;
        const float bx = x0 + (w - bw) / 2, by = y0 + h * 0.42f;
        c.Golge(bx, by, bw, 52, tema::belirtec::R.buyuk, 8, 0.10f, 2);
        c.Yuv(bx, by, bw, 52, tema::belirtec::R.buyuk, tema::Alfa(R.yuzey, 0.94f), R.cizgi);
        c.YaziOrta(bx + bw / 2, by + 22, s1, 13, tema::Agirlik::Kalin, R.metin);
        c.YaziOrta(bx + bw / 2, by + 40, s2, 11, tema::Agirlik::Normal, R.metin3);
    }
    // ---- pencere seçimi lastik bandı ----
    double rx0, ry0, rx1, ry1;
    PencereKipi pk;
    if (gezinme_.PencereDikdortgeni(rx0, ry0, rx1, ry1, pk)) {
        const ImVec2 a(gorus_.x + static_cast<float>(std::min(rx0, rx1)), gorus_.y + static_cast<float>(std::min(ry0, ry1)));
        const ImVec2 b(gorus_.x + static_cast<float>(std::max(rx0, rx1)), gorus_.y + static_cast<float>(std::max(ry0, ry1)));
        c.dl->AddRectFilled(a, b, tema::Alfa(R.vurgu, pk == PencereKipi::TamIcinde ? 0.08f : 0.05f));
        if (pk == PencereKipi::TamIcinde) {
            c.dl->AddRect(a, b, R.vurgu, 0, 1.0f);
        } else {
            KesikCizgi(c.dl, a, ImVec2(b.x, a.y), R.vurgu, 1, 4, 3);
            KesikCizgi(c.dl, ImVec2(b.x, a.y), b, R.vurgu, 1, 4, 3);
            KesikCizgi(c.dl, b, ImVec2(a.x, b.y), R.vurgu, 1, 4, 3);
            KesikCizgi(c.dl, ImVec2(a.x, b.y), a, R.vurgu, 1, 4, 3);
        }
    }
    c.dl->PopClipRect();
}

// ---- çubuk görünümü ve sahne üstü çizimler -------------------------------------------------------------------------------
void AnaPencere::SahneCiz(Ciz& c) {
    const auto& R = c.R();
    const tema::SahneCizimi& T = tema::Etkin().s;
    const SahneAnlik& s = *sahne_;
    const Izd iz{Izdusum(), gorus_.x, gorus_.y};
    const float S = olcek_;
    const std::vector<ElemanKimligi>* secim = h_.secim ? &h_.secim->Liste() : nullptr;
    auto secili = [&](ElemanKimligi k) { return secim && std::binary_search(secim->begin(), secim->end(), k); };
    // Plan görünümünde etkin kat ± yarım kat normal, dışı hayalet (MIMARI §6.12).
    double zAlt = -1e300, zUst = 1e300;
    if (yon_ == StandartYon::Plan && etkinKat >= 0) {
        const double z = s.seviyeler[static_cast<size_t>(etkinKat)].z;
        double yari = 1.5;
        if (etkinKat > 0) yari = std::min(yari, (z - s.seviyeler[static_cast<size_t>(etkinKat - 1)].z) * 0.5);
        zAlt = z - yari - 1e-6;
        zUst = z + 0.05;
    }
    auto hayalet = [&](double za, double zb) { return std::min(za, zb) < zAlt || std::max(za, zb) > zUst; };

    // Akslar (dünya uzayında kesikli çizgi) ve balonlar (ekran uzayı).
    if (akslarGorunur_) {
        for (const SahneAksi& a : s.akslar) {
            if (a.eksen > 1) continue;
            ImVec2 pa, pb;
            if (iz.Parca(a.bas, a.son, pa, pb)) KesikCizgi(c.dl, pa, pb, R.aksCizgisi, 1.0f * S, T.aksKesik * S, T.aksBosluk * S);
        }
    }
    // Kat seviyeleri: yapının sağında ◀ +9,00 Kat 2 (3B ve cephede).
    if (yon_ != StandartYon::Plan && !s.sinir.Bos()) {
        const V3d sag = kamera_.Sag();
        const Kutu3d& k = s.sinir;
        // ekranda sağda kalan köşe (x, y)
        V3d kose{k.enBuyuk.x, k.enKucuk.y, 0};
        double en = -1e300;
        for (const V3d q : {V3d{k.enKucuk.x, k.enKucuk.y, 0}, V3d{k.enBuyuk.x, k.enKucuk.y, 0}, V3d{k.enKucuk.x, k.enBuyuk.y, 0},
                            V3d{k.enBuyuk.x, k.enBuyuk.y, 0}})
            if (Nokta(q, sag) > en) {
                en = Nokta(q, sag);
                kose = q;
            }
        const V3d dis = sag * (0.05 * std::max(1.0, k.enBuyuk.x - k.enKucuk.x + k.enBuyuk.y - k.enKucuk.y));
        for (size_t i = 0; i < s.seviyeler.size(); ++i) {
            const SahneSeviyesi& sv = s.seviyeler[i];
            if (sv.kat < 0) continue;
            ImVec2 p;
            if (!iz.Nokta(kose + dis + V3d{0, 0, sv.z}, p)) continue;
            const bool etkin = static_cast<int>(i) == etkinKat;
            const float gen = c.Gen(Kot(sv.z), 11, tema::Agirlik::Orta) + 6 + c.Gen(KatAdi(static_cast<int>(i), false), 11, tema::Agirlik::Kalin);
            p.x = std::min(p.x, (L_.vpX1 - 14 - gen - 10) * S);
            c.dl->AddTriangleFilled(ImVec2(p.x, p.y), ImVec2(p.x + 6 * S, p.y - 4 * S), ImVec2(p.x + 6 * S, p.y + 4 * S),
                                    etkin ? R.vurgu : R.metin);
            const float tx = p.x / S + 10, ty = p.y / S + 4;
            const float g = c.Yazi(tx, ty, Kot(sv.z), 11, tema::Agirlik::Orta, R.metin);
            c.Yazi(tx + g + 6, ty, KatAdi(static_cast<int>(i), false), 11, tema::Agirlik::Kalin, etkin ? R.vurgu : R.metin);
        }
    }

    const bool cubukKipi = !KesitGorunumu();
    const float kal = T.cubukKalinlik * S;
    // Paneller (yarı saydam).
    if (cubukKipi) {
        std::vector<ImVec2> p;
        for (const SahnePaneli& pn : s.paneller) {
            p.clear();
            bool tamam = true;
            double za = 1e300, zb = -1e300;
            for (uint32_t i = 0; i < pn.koseSayisi && pn.koseBas + i < s.panelKoseleri.size(); ++i) {
                const uint32_t d = s.panelKoseleri[pn.koseBas + i];
                if (d >= s.dugumler.size()) continue;
                ImVec2 q;
                if (!iz.Nokta(s.dugumler[d].p, q)) {
                    tamam = false;
                    break;
                }
                za = std::min(za, s.dugumler[d].p.z);
                zb = std::max(zb, s.dugumler[d].p.z);
                p.push_back(q);
            }
            if (!tamam || p.size() < 3) continue;
            const ElemanKimligi k = PanelKimligi(pn.no);
            const bool sec = secili(k), h = uzerinde_ == k;
            float a = hayalet(za, zb) || (yalnizSecili && !sec) ? 0.2f : 1.0f;
            c.dl->AddConcavePolyFilled(p.data(), static_cast<int>(p.size()), tema::Alfa(sec ? R.seciliDolgu : R.panelDolgu, a * (sec ? 0.6f : 1.0f)));
            c.dl->AddPolyline(p.data(), static_cast<int>(p.size()), sec ? R.secim : (h ? R.uzerinde : tema::Alfa(R.panelKenar, a)),
                              (sec ? 1.5f : 1.0f) * S, ImDrawFlags_Closed);
        }
    }
    // Çubuklar: sabit piksel kalınlığı; seçili kalın vurgu rengi, üzerinde ince kontur.
    auto turRengi = [&](CubukTuru t) {
        switch (t) {
            case CubukTuru::Kolon: return R.cubukKolon;
            case CubukTuru::Kiris: return R.cubukKiris;
            case CubukTuru::Capraz: return R.cubukCapraz;
            case CubukTuru::Asik: return R.cubukAsik;
            default: return R.cubukDiger;
        }
    };
    std::vector<size_t> sonraki;  // seçili / üzerinde: en üstte çizilir
    for (size_t ci = 0; ci < s.cubuklar.size(); ++ci) {
        const SahneCubugu& cb = s.cubuklar[ci];
        if (cb.i >= s.dugumler.size() || cb.j >= s.dugumler.size()) continue;
        const ElemanKimligi k = CubukKimligi(cb.no);
        if (secili(k) || uzerinde_ == k) {
            sonraki.push_back(ci);
            continue;
        }
        if (!cubukKipi) continue;
        const V3d a = s.dugumler[cb.i].p, b = s.dugumler[cb.j].p;
        ImVec2 pa, pb;
        if (!iz.Parca(a, b, pa, pb)) continue;
        const float al = hayalet(a.z, b.z) || yalnizSecili ? 0.18f : 1.0f;
        const uint32_t renk = tema::Alfa(turRengi(cb.tur), al);
        if (cb.bayrak & cubuk_bayragi::YALNIZ_CEKME)
            KesikCizgi(c.dl, pa, pb, renk, kal, 6 * S, 4 * S);
        else
            c.dl->AddLine(pa, pb, renk, kal);
    }
    // Seçim (tasarim.md §3.6): vurgu konturu + yumuşak hale + açık dolgu. Çubuk kipinde hale, seçim çizgisinin altında
    // giderek genişleyen saydam katmanlardır (5 px çizginin ≈ 3 px bulanıklığı, %42); katı kipte dolgu ve kontur GPU'da,
    // hale burada kesit yüksekliğinin ekrandaki karşılığı kadar geniş, çok saydam bir şerittir.
    const GorunumKamerasi& kam = kamera_;
    auto hale = [&](ImVec2 pa, ImVec2 pb, float cekirdek) {
        static const float kat[3][2] = {{9.0f, 0.10f}, {6.0f, 0.13f}, {3.5f, 0.19f}};
        for (const auto& k : kat)
            c.dl->AddLine(pa, pb, tema::Alfa(R.secim, T.haleSaydamlik * k[1] / 0.42f * 1.6f), (cekirdek + k[0]) * S);
    };
    for (const size_t ci : sonraki) {
        const SahneCubugu& cb = s.cubuklar[ci];
        const ElemanKimligi k = CubukKimligi(cb.no);
        ImVec2 pa, pb;
        const V3d A = s.dugumler[cb.i].p, B = s.dugumler[cb.j].p;
        if (!iz.Parca(A, B, pa, pb)) continue;
        if (secili(k)) {
            if (cubukKipi) {
                hale(pa, pb, T.seciliKalinlik);
                c.dl->AddLine(pa, pb, tema::Alfa(R.seciliDolgu, 0.9f), (T.seciliKalinlik + 2.0f) * S);
                c.dl->AddLine(pa, pb, R.secim, T.seciliKalinlik * S);
            } else {
                // kesit derinliğinin ekrandaki genişliği (kamera yukarı yönünde ≈ 0,4 m)
                const V3d m = (A + B) * 0.5;
                const double hm = cb.kesit < s.kesitler.size() && s.kesitler[cb.kesit].h > 0 ? s.kesitler[cb.kesit].h : 0.4;
                ImVec2 m0, m1;
                if (iz.Nokta(m, m0) && iz.Nokta(m + kam.Yukari() * hm, m1)) {
                    const float gen = std::hypot(m1.x - m0.x, m1.y - m0.y) / S;
                    hale(pa, pb, std::max(2.0f, gen));
                }
            }
        }
        if (uzerinde_ == k) {
            if (cubukKipi) c.dl->AddLine(pa, pb, tema::Alfa(R.uzerinde, 0.85f), (T.cubukKalinlik + 0.6f) * S);
        }
    }
    // Mafsallı uçlar (My ve Mz serbest): içi boş daire.
    if (cubukKipi) {
        for (const SahneCubugu& cb : s.cubuklar) {
            if (!cb.serbestlik || cb.i >= s.dugumler.size() || cb.j >= s.dugumler.size()) continue;
            ImVec2 pa, pb;
            if (!iz.Parca(s.dugumler[cb.i].p, s.dugumler[cb.j].p, pa, pb)) continue;
            const float dx = pb.x - pa.x, dy = pb.y - pa.y, L = std::sqrt(dx * dx + dy * dy);
            if (L < 4 * T.mafsalUzaklik * S) continue;
            const float ux = dx / L, uy = dy / L, d = T.mafsalUzaklik * S;
            const uint32_t renk = turRengi(cb.tur);
            for (int u = 0; u < 2; ++u) {
                const bool my = cb.serbestlik & SerbestlikBiti(u == 1, 4), mz = cb.serbestlik & SerbestlikBiti(u == 1, 5);
                if (!my && !mz) continue;
                const ImVec2 m = u == 0 ? ImVec2(pa.x + ux * d, pa.y + uy * d) : ImVec2(pb.x - ux * d, pb.y - uy * d);
                c.dl->AddCircleFilled(m, T.mafsalYaricap * S, R.beyaz, 12);
                c.dl->AddCircle(m, T.mafsalYaricap * S, renk, 12, 1.2f * S);
            }
        }
    }
    // Düğümler ve serbest düğümler.
    if (dugumlerGorunur_ && cubukKipi) {
        for (const SahneDugumu& d : s.dugumler) {
            ImVec2 p;
            if (!iz.Nokta(d.p, p)) continue;
            const ElemanKimligi k = DugumKimligi(d.no);
            const bool sec = secili(k);
            if (d.tur == DugumTuru::Serbest) {
                c.dl->AddCircleFilled(p, T.serbestDugumYaricap * S, R.beyaz, 12);
                c.dl->AddCircle(p, T.serbestDugumYaricap * S, R.serbestDugum, 12, 1.3f * S);
            } else {
                const float a = hayalet(d.p.z, d.p.z) || (yalnizSecili && !sec) ? 0.25f : 1.0f;
                c.dl->AddCircleFilled(p, (sec ? T.dugumYaricap + 1.2f : T.dugumYaricap) * S, sec ? R.secim : tema::Alfa(R.dugum, a), 10);
            }
            if (uzerinde_ == k) c.dl->AddCircle(p, (T.dugumYaricap + 3) * S, R.uzerinde, 16, 1.0f * S);
        }
    }
    // Mesnetler: ekran boyutlu simgeler (düğümün altında).
    for (const SahneMesnedi& m : s.mesnetler) {
        if (m.dugum >= s.dugumler.size()) continue;
        ImVec2 p;
        if (!iz.Nokta(s.dugumler[m.dugum].p, p)) continue;
        const float b = T.mesnetBoy * S;
        const uint32_t renk = secili({ElemanTuru::Mesnet, 0, s.dugumler[m.dugum].no}) ? R.secim : R.mesnet;
        if (m.tur == MesnetTuru::Ankastre || (m.maske & 0x38) == 0x38) {
            c.dl->AddRectFilled(ImVec2(p.x - b * 0.8f, p.y + 1.5f * S), ImVec2(p.x + b * 0.8f, p.y + 1.5f * S + b * 0.45f), renk);
            for (int i = 0; i < 4; ++i) {
                const float hx = p.x - b * 0.8f + static_cast<float>(i) * b * 0.45f;
                c.dl->AddLine(ImVec2(hx, p.y + 1.5f * S + b * 0.45f), ImVec2(hx - b * 0.3f, p.y + 1.5f * S + b * 0.8f), renk, 1.0f * S);
            }
        } else {
            c.dl->AddTriangle(p, ImVec2(p.x - b * 0.6f, p.y + b), ImVec2(p.x + b * 0.6f, p.y + b), renk, 1.3f * S);
            if (m.tur == MesnetTuru::Kayici) {
                c.dl->AddCircle(ImVec2(p.x - b * 0.3f, p.y + b + 2.5f * S), 1.8f * S, renk, 8, 1.0f * S);
                c.dl->AddCircle(ImVec2(p.x + b * 0.3f, p.y + b + 2.5f * S), 1.8f * S, renk, 8, 1.0f * S);
            } else {
                c.dl->AddLine(ImVec2(p.x - b * 0.8f, p.y + b + 1.5f * S), ImVec2(p.x + b * 0.8f, p.y + b + 1.5f * S), renk, 1.2f * S);
            }
        }
    }
    // Aks balonları (en üstte; ekran uzayı).
    if (akslarGorunur_) {
        for (const SahneAksi& a : s.akslar) {
            if (a.eksen > 1) continue;
            ImVec2 p;
            if (!iz.Nokta(a.balon, p)) continue;
            const float r = T.aksBalonYaricap * S;
            c.dl->AddCircleFilled(p, r, tema::Alfa(R.beyaz, 0.94f), 20);
            c.dl->AddCircle(p, r - 0.5f * S, R.aksBalonKenar, 20, 1.0f * S);
            c.YaziOrta(p.x / S, p.y / S + 3.8f, a.ad, 10.5f, tema::Agirlik::Orta, R.metin2);
        }
    }
    // Eleman etiketleri (isteğe bağlı): ekran kovalarıyla çakışma ayıklama, seçili önce.
    if (etiketlerGorunur_ && cubukKipi) {
        std::vector<ImVec4> dolu;
        auto bos = [&](ImVec4 r) {
            for (const ImVec4& q : dolu)
                if (!(r.z < q.x || r.x > q.z || r.w < q.y || r.y > q.w)) return false;
            dolu.push_back(r);
            return true;
        };
        for (int tur = 0; tur < 2; ++tur)
            for (const SahneCubugu& cb : s.cubuklar) {
                const ElemanKimligi k = CubukKimligi(cb.no);
                if ((tur == 0) != secili(k)) continue;
                ImVec2 p;
                if (!iz.Nokta((s.dugumler[cb.i].p + s.dugumler[cb.j].p) * 0.5, p)) continue;
                const std::string ad = ElemanAdi(k);
                const float g = c.Gen(ad, T.etiketBoy, tema::Agirlik::Orta) * S;
                if (!bos(ImVec4(p.x - g / 2 - 2, p.y - 8 * S, p.x + g / 2 + 2, p.y + 6 * S))) continue;
                c.YaziOrta(p.x / S, p.y / S + 4, ad, T.etiketBoy, tema::Agirlik::Orta, secili(k) ? R.vurgu : R.metin2);
            }
    }
}

// ---- seçim notları ---------------------------------------------------------------------------------------------------
void AnaPencere::SecimNotlariCiz(Ciz& c) {
    const auto& R = c.R();
    const SahneAnlik& s = *sahne_;
    const Izd iz{Izdusum(), gorus_.x, gorus_.y};
    const float S = olcek_;
    if (h_.secim && !h_.secim->Bos()) {
        // Doğrudan değiştirme tutamaçları: ilk seçili çubukta başlangıç (vurgu) / bitiş (koyu) karesi, orta daire, ölçü.
        const SahneCubugu* ilk = nullptr;
        for (const ElemanKimligi& k : h_.secim->Liste())
            if (k.tur == ElemanTuru::Cubuk)
                if (const auto i = s.CubukDizini(k.no)) {
                    ilk = &s.cubuklar[*i];
                    break;
                }
        if (ilk && dogrudanDegistirme && ilk->i < s.dugumler.size() && ilk->j < s.dugumler.size()) {
            const V3d A = s.dugumler[ilk->i].p, B = s.dugumler[ilk->j].p;
            ImVec2 a, b, m;
            if (iz.Nokta(A, a) && iz.Nokta(B, b) && iz.Nokta((A + B) * 0.5, m)) {
                // Başlangıç: beyaz çerçeveli DOLU seçim karesi · Bitiş: seçim çerçeveli İÇİ BOŞ kare · Orta: beyaz daire +
                // 1,5 px seçim halkası (renk körlüğünde de biçimle ayrışır; ARAYUZ_ILKELERI 16).
                const float t = tema::Etkin().s.tutamac * 0.5f * S;
                for (int u = 0; u < 2; ++u) {
                    const ImVec2 p = u == 0 ? a : b;
                    c.dl->AddRectFilled(ImVec2(p.x - t - S, p.y - t - S), ImVec2(p.x + t + S, p.y + t + S),
                                        tema::Alfa(R.golge | 0xFF000000u, 0.18f), 2 * S);
                    if (u == 0) {
                        c.dl->AddRectFilled(ImVec2(p.x - t, p.y - t), ImVec2(p.x + t, p.y + t), R.beyaz, 1.5f * S);
                        c.dl->AddRectFilled(ImVec2(p.x - t + 1.5f * S, p.y - t + 1.5f * S),
                                            ImVec2(p.x + t - 1.5f * S, p.y + t - 1.5f * S), R.tutamacBaslangic, 1 * S);
                    } else {
                        c.dl->AddRectFilled(ImVec2(p.x - t, p.y - t), ImVec2(p.x + t, p.y + t), R.beyaz, 1.5f * S);
                        c.dl->AddRect(ImVec2(p.x - t + 0.75f * S, p.y - t + 0.75f * S), ImVec2(p.x + t - 0.75f * S, p.y + t - 0.75f * S),
                                      R.tutamacBitis, 1 * S, 1.5f * S);
                    }
                }
                c.dl->AddCircleFilled(m, 4.5f * S, R.beyaz, 16);
                c.dl->AddCircle(m, 4.5f * S, R.secim, 16, 1.5f * S);
                // ölçü etiketi (mm, binlik ayırıcılı)
                const double L = Uzunluk(B - A) * 1000.0;
                const std::string et = Sayi(std::round(L), 0);
                const float ew = c.Gen(et, 11, tema::Agirlik::Kalin) + 16;
                const float ux = m.x / S - ew / 2, uy = m.y / S + 16;
                c.Yuv(ux, uy - 10, ew, 20, tema::belirtec::R.orta, R.beyaz, R.secim);
                c.YaziOrta(m.x / S, Taban(uy - 10, 20, 11), et, 11, tema::Agirlik::Kalin, R.metin);
            }
        }
        // Bağlamsal mini araç çubuğu: seçim merkezinin üstünde (F1 salt okunur).
        Kutu3d kutu = secme_.Sinir(h_.secim->Liste());
        ImVec2 merkez;
        if (!kutu.Bos() && iz.Nokta(V3d{kutu.Merkez().x, kutu.Merkez().y, kutu.enBuyuk.z}, merkez)) {
            std::vector<std::pair<const char*, std::string>> alanlar;
            const auto ortak = OrtakOzellikler(*oz_, h_.secim->Liste());
            auto al = [&](const char* id) {
                for (const auto& [k, v] : ortak)
                    if (k == id) return v == "(çeşitli)" ? std::string(Tr("(farklı)")) : v;
                return std::string("—");
            };
            alanlar.push_back({"kiris", al(oznitelik::KESIT)});
            alanlar.push_back({"malzeme", al(oznitelik::MALZEME)});
            std::string kat = al(oznitelik::KAT);
            if (kat.find(',') == std::string::npos && kat != "—" && kat != Tr("(farklı)")) kat = Trf("Kat %s", kat.c_str());
            alanlar.push_back({"kat", kat});
            std::string serbest = al(oznitelik::SERBEST_I) == "—" ? std::string(Tr("Rijit")) : std::string(Tr("Mafsal"));
            alanlar.push_back({"mafsal", serbest});
            float cw = 10;
            for (const auto& [ik, et] : alanlar) cw += 18 + c.Gen(et, 11, tema::Agirlik::Orta) + 12 + 14;
            cw += 3 * 24 + 10;
            const float vx0 = L_.vpX0 + 8, vx1 = L_.vpX1 - 8;
            float cx = std::clamp(merkez.x / S - cw / 2, vx0, vx1 - cw);
            const float mh = 32;
            float cy = std::clamp(merkez.y / S - 80, L_.vpY0 + 48, L_.vpY1 - 84);
            const auto& g = tema::belirtec::GOLGE.acilir;
            c.Golge(cx, cy, cw, mh, tema::belirtec::R.buyuk, g.bulaniklik * 0.6f, g.saydamlik, g.dy * 0.5f);
            c.Yuv(cx, cy, cw, mh, tema::belirtec::R.buyuk, R.yuzey, R.cizgi);
            Engel(cx, cy, cw, mh);
            Tiklama(c, "##mini", cx, cy, cw, mh);
            OgeIpucu(c, Tr("Düzenleme Faz 3'te: alanlar şimdilik salt okunur."));
            float x = cx + 10;
            for (const auto& [ik, et] : alanlar) {
                c.Simge(ik, x + 7, cy + mh / 2, 14, R.ikonKucuk, 1.3f);
                c.Yazi(x + 18, Taban(cy, mh, 11), et, 11, tema::Agirlik::Orta, R.metin);
                x += 18 + c.Gen(et, 11, tema::Agirlik::Orta);
                c.Sevron(x + 6, cy + mh / 2 + 0.5f, 0, 9, R.metin2);
                x += 12 + 7;
                c.Dusey(x, cy + 8, cy + mh - 8, R.cizgi2);
                x += 7;
            }
            for (const char* ik : {"kopyala", "tasi", "sil"}) {
                c.Simge(ik, x + 10, cy + mh / 2, 14, std::string_view(ik) == "sil" ? tema::Alfa(R.hata, 0.55f) : R.ikonKapali, 1.3f);
                x += 24;
            }
            const float ox = std::clamp(merkez.x / S, cx + 12, cx + cw - 12);
            c.dl->AddTriangleFilled(c.P(ox - 6, cy + mh - 0.5f), c.P(ox + 6, cy + mh - 0.5f), c.P(ox, cy + mh + 6), R.yuzey);
            c.dl->AddLine(c.P(ox - 6, cy + mh), c.P(ox, cy + mh + 6), R.cizgi, S);
            c.dl->AddLine(c.P(ox + 6, cy + mh), c.P(ox, cy + mh + 6), R.cizgi, S);
        }
    }
    // Üzerinde ipucu: imleç yanında beyaz kart, vurgu kenarı.
    if (uzerinde_.Gecerli() && !gezinme_.Surukluyor()) {
        const ImVec2 m = ImGui::GetIO().MousePos;
        if (m.x >= gorus_.x && m.y >= gorus_.y && m.x < gorus_.x + gorus_.g && m.y < gorus_.y + gorus_.y2) {
            std::string ip = ElemanAdi(uzerinde_);
            if (const auto r = oz_->Satir(uzerinde_)) {
                if (const auto k = oz_->Metin(*r, oznitelik::KESIT)) ip += " · " + std::string(*k);
                if (const auto k = oz_->Metin(*r, oznitelik::MALZEME)) ip += " · " + std::string(*k);
            }
            c.IpucuKarti(m.x / S + 18, m.y / S + 16, ip, 10);
        }
    }
}

// ---- fare girdisi --------------------------------------------------------------------------------------------------------
void AnaPencere::GorunumGirdisi(Ciz& c) {
    (void)c;
    ImGuiIO& io = ImGui::GetIO();
    const ImVec2 m = io.MousePos;
    const double px = m.x - gorus_.x, py = m.y - gorus_.y;
    bool icinde = m.x >= gorus_.x && m.y >= gorus_.y && m.x < gorus_.x + gorus_.g && m.y < gorus_.y + gorus_.y2;
    for (const ImVec4& e : engeller_)
        if (m.x >= e.x && m.y >= e.y && m.x < e.z && m.y < e.w) icinde = false;
    const bool serbest = icinde && ImGui::IsWindowHovered() && !ImGui::IsAnyItemHovered() &&
                         !ImGui::IsPopupOpen("", ImGuiPopupFlags_AnyPopupId);
    const Degistiriciler d{io.KeyCtrl, io.KeyShift, io.KeyAlt};
    const FareTusu tuslar[3] = {FareTusu::Sol, FareTusu::Orta, FareTusu::Sag};
    const ImGuiMouseButton im[3] = {ImGuiMouseButton_Left, ImGuiMouseButton_Middle, ImGuiMouseButton_Right};
    if (serbest)
        for (int i = 0; i < 3; ++i) {
            if (ImGui::IsMouseDoubleClicked(im[i])) gezinme_.CiftTik(kamera_, tuslar[i], px, py);
            if (ImGui::IsMouseClicked(im[i])) gezinme_.Bas(kamera_, tuslar[i], px, py, d);
        }
    if (gezinme_.Basili()) {
        gezinme_.Hareket(kamera_, px, py, d);
        for (int i = 0; i < 3; ++i)
            if (ImGui::IsMouseReleased(im[i])) gezinme_.Birak(kamera_, tuslar[i], px, py, d);
        cizimGerekli_ = true;
    }
    if (serbest && io.MouseWheel != 0.0f) {
        gezinme_.Tekerlek(kamera_, io.MouseWheel, px, py);
        cizimGerekli_ = true;
    }
    if (serbest && ImGui::IsMouseReleased(ImGuiMouseButton_Right) && !gezinme_.Basili()) ImGui::OpenPopup("##baglam");
    // Üzerine gelme ve imleç koordinatı.
    ElemanKimligi yeni{};
    if (serbest && !gezinme_.Surukluyor()) {
        SecmeAyari a;
        for (const SecmeVurusu& v : secme_.Adaylar(Izdusum(), px, py, a))
            if (Secilebilir(v.kimlik)) {
                yeni = v.kimlik;
                break;
            }
        double z = 0;
        if (etkinKat >= 0 && etkinKat < static_cast<int>(sahne_->seviyeler.size())) z = sahne_->seviyeler[static_cast<size_t>(etkinKat)].z;
        imlecDunya_ = CalismaDuzlemiNoktasi(kamera_, px, py, gorus_.g, gorus_.y2, z);
        imlecDunyaVar_ = true;
    } else if (!icinde) {
        imlecDunyaVar_ = false;
    }
    if (!gezinme_.Surukluyor() && !(yeni == uzerinde_)) {
        uzerinde_ = yeni;
        ++vurguSurumu_;
        cizimGerekli_ = true;
    }
    if (gezinme_.Surukluyor())
        ImGui::SetMouseCursor(gezinme_.Tur() == SuruklemeTuru::Dondur ? ImGuiMouseCursor_Hand : ImGuiMouseCursor_ResizeAll);
    // Bağlam menüsü (seçimin türüne göre; F1 alt kümesi).
    if (ImGui::BeginPopup("##baglam")) {
        const bool secimVar = h_.secim && !h_.secim->Bos();
        if (ImGui::MenuItem(Tr("Özellikler"), nullptr, false, secimVar)) yanPencere = YanPencere::Ozellikler;
        if (ImGui::MenuItem(Tr("Benzerini seç"), nullptr, false, secimVar)) KomutCalistir("secim.benzer", KomutKaynagi::Baglam);
        if (ImGui::MenuItem(Tr("Seçime yakınlaş"), nullptr, false, secimVar)) KomutCalistir("gorunum.secime_yakinlas", KomutKaynagi::Baglam);
        if (ImGui::MenuItem(Tr("Yalnız seçiliyi göster"), "Ctrl+5", yalnizSecili, secimVar)) yalnizSecili = !yalnizSecili;
        if (ImGui::MenuItem(Tr("Seçimi temizle"), "Esc", false, secimVar)) KomutCalistir("secim.temizle", KomutKaynagi::Baglam);
        ImGui::Separator();
        if (ImGui::MenuItem(Tr("Tam görünüm"), "Shift+F")) KomutCalistir("gorunum.sigdir", KomutKaynagi::Baglam);
        ImGui::EndPopup();
    }
    if (ImGui::IsKeyChordPressed(ImGuiMod_Ctrl | ImGuiKey_5)) yalnizSecili = !yalnizSecili;
}

}  // namespace op4
