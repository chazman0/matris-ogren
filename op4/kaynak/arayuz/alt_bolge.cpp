// op4 arayüzü — alt bölge: rıhtım (Komut / Mesajlar / Tablolar + diğer paketlerin alt panelleri), komut satırı (Türkçe ad +
// İngilizce takma ad, önek / alt dizi tamamlama, geçmiş, Son / Şerit / Menü / Tümü önerileri, Ctrl+Q hızlı başlat) ve
// durum çubuğu (yönerge, ORTO / YAKALA / SÜRÜKLE, X Y Z, kat kapsamı, etkin kat, birim, koordinat, seçili sayısı)
// (MIMARI §5.4, kabul C2; atolye uret.py dock, komut_satiri, durum_cubugu).
#include <algorithm>
#include <cmath>
#include <cstring>

#include "arayuz/ana_pencere.h"
#include "arayuz/dil.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/komut.h"
#include "cekirdek/secim.h"
#include "cekirdek/turkce.h"

namespace op4 {

// ---- rıhtım --------------------------------------------------------------------------------------------------------------
void AnaPencere::RihtimCiz(Ciz& c) {
    const auto& R = c.R();
    const float x0 = L_.ray, y0 = L_.alt, w = L_.W - L_.ray, th = L_.rsekme, dh = L_.rihtim;
    c.Dikd(x0, y0, w, th, R.zemin);
    c.Yatay(x0, x0 + w, y0, R.cizgi);
    float x = x0 + 12;
    struct Sek {
        RihtimSekmesi s;
        const char* ad;
    };
    const Sek sekmeler[3] = {{RihtimSekmesi::Komut, "Komut"}, {RihtimSekmesi::Mesajlar, "Mesajlar"}, {RihtimSekmesi::Tablolar, "Tablolar"}};
    for (const Sek& s : sekmeler) {
        const char* ad = Tr(s.ad);
        const float tw = c.Gen(ad, 12, tema::Agirlik::Kalin);
        const std::string n = s.s == RihtimSekmesi::Mesajlar && !iletiler.empty() ? std::to_string(std::min<size_t>(iletiler.size(), 99)) : "";
        const float nw = n.empty() ? 0 : std::max(16.0f, c.Gen(n, 9, tema::Agirlik::Kalin) + 10) + 6;
        ImGui::PushID(static_cast<int>(s.s));
        if (Tiklama(c, "##rsekme", x - 6, y0, tw + nw + 12, th)) rihtim = s.s;
        ImGui::PopID();
        const bool etkin = rihtim == s.s;
        c.Yazi(x, Taban(y0, th, 12), ad, 12, etkin ? tema::Agirlik::Kalin : tema::Agirlik::Orta, etkin ? R.metin : R.metin2);
        if (etkin) c.Yuv(x - 3, y0 + th - 3, tw + nw + 6, 3, 1.5f, R.vurgu);
        if (!n.empty()) c.Rozet(x + tw + 6, y0 + (th - 16) / 2, n, 9, R.uyariTon, R.uyari, 16);
        x += tw + nw + 26;
    }
    // ilerleme göstergeleri (uzun işler) rıhtım sekme satırının sağında
    float rx = x0 + w - 56;
    for (const op4::Ilerleme& i : ilerlemeler) {
        const float g = 120;
        c.Yazi(rx - g - c.Gen(i.metin, 11, tema::Agirlik::Normal) - 8, Taban(y0, th, 11), i.metin, 11, tema::Agirlik::Normal, R.metin2);
        c.Yuv(rx - g, y0 + th / 2 - 2, g, 4, 2, R.zemin2);
        if (i.oran >= 0)
            c.Yuv(rx - g, y0 + th / 2 - 2, g * std::clamp(i.oran, 0.0f, 1.0f), 4, 2, R.vurgu);
        else
            c.Yuv(rx - g + std::fmod(static_cast<float>(simdi) * 0.08f, g - 30), y0 + th / 2 - 2, 30, 4, 2, R.vurgu);
        if (i.iptal) {
            ImGui::PushID(i.id.c_str());
            if (Tiklama(c, "##iptal", rx + 4, y0 + 3, 16, th - 6)) i.iptal();
            ImGui::PopID();
            c.Simge("kapat", rx + 12, y0 + th / 2, 10, R.metin2, 1.3f);
        }
        rx -= g + 200;
    }
    c.Simge("pin", x0 + w - 44, y0 + th / 2, 14, R.ikonKucuk, 1.3f);
    c.Simge("sevron_asagi", x0 + w - 20, y0 + th / 2, 12, R.ikonKucuk, 1.4f);
    const float cy = y0 + th;
    c.Dikd(x0, cy, w, dh, R.yuzey);
    const float rh = L_.dar ? 18.0f : 20.0f;
    if (rihtim == RihtimSekmesi::Komut) {
        const size_t n = static_cast<size_t>(std::max(1.0f, std::floor(dh / rh)));
        const size_t bas = cikti.size() > n ? cikti.size() - n : 0;
        float yy = cy + (dh - rh * static_cast<float>(std::min(n, cikti.size()))) / 2;
        for (size_t i = bas; i < cikti.size(); ++i) {
            const std::string& s = cikti[i];
            c.Sevron(x0 + 18, yy + rh / 2, 1, 9, R.metin3);
            // "KOMUT — ileti" biçiminde ilk sözcük vurgu renginde
            const size_t b = s.find(' ');
            const bool buyukHarf = b != std::string::npos && b > 1 && std::all_of(s.begin(), s.begin() + static_cast<long>(b), [](char ch) {
                                       return (ch >= 'A' && ch <= 'Z') || (static_cast<unsigned char>(ch) >= 0x80) || ch == '.';
                                   });
            float tx = x0 + 24;
            if (buyukHarf) {
                tx += c.Yazi(tx, Taban(yy, rh, 11), s.substr(0, b), 11, tema::Agirlik::Kalin, R.vurguMetin) + 10;
                c.Yazi(tx, Taban(yy, rh, 11), s.substr(b + 1), 11, tema::Agirlik::Normal, R.metin2, w - (tx - x0) - 16);
            } else {
                c.Yazi(tx, Taban(yy, rh, 11), s, 11, tema::Agirlik::Normal, R.metin2, w - 40);
            }
            yy += rh;
        }
    } else if (rihtim == RihtimSekmesi::Mesajlar) {
        const size_t n = static_cast<size_t>(std::max(1.0f, std::floor(dh / rh)));
        const size_t bas = iletiler.size() > n ? iletiler.size() - n : 0;
        float yy = cy + 2;
        if (iletiler.empty()) c.Yazi(x0 + 12, Taban(yy, rh, 11), Tr("İleti yok."), 11, tema::Agirlik::Normal, R.metin3);
        for (size_t i = bas; i < iletiler.size(); ++i) {
            const auto& m = iletiler[i];
            c.Simge(m.tur == TostTuru::Hata ? "uyari" : (m.tur == TostTuru::Uyari ? "uyari" : "bilgi"), x0 + 18, yy + rh / 2, 12,
                    m.tur == TostTuru::Hata ? R.hata : (m.tur == TostTuru::Uyari ? R.uyari : R.metin2), 1.4f);
            c.Yazi(x0 + 30, Taban(yy, rh, 11), m.metin, 11, tema::Agirlik::Normal, R.metin2, w - 50);
            yy += rh;
        }
    } else {
        c.Yazi(x0 + 12, Taban(cy + 2, rh, 11), Tr("Model ve sonuç tabloları Faz 5'te gelir."), 11, tema::Agirlik::Normal, R.metin3);
    }
    // Diğer paketlerin alt panelleri (S21 PanelYeri::Alt) rıhtımın üstünde yüzen pencere olarak.
    if (h_.arayuz)
        for (const PanelKaydi& p : h_.arayuz->Paneller()) {
            if (p.sahip == "C" || !h_.arayuz->PanelAcik(p.id) || !p.ciz) continue;
            ImGui::SetNextWindowSize(ImVec2(c.S(420), c.S(220)), ImGuiCond_FirstUseEver);
            ImGui::SetNextWindowPos(c.P(L_.vpX1 - 440, L_.vpY0 + 60), ImGuiCond_FirstUseEver);
            bool acik = true;
            if (ImGui::Begin(Tr(p.baslik.c_str()), &acik, ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_NoCollapse)) p.ciz();
            ImGui::End();
            if (!acik) h_.arayuz->PanelGoster(p.id, false);
        }
}

// ---- komut satırı --------------------------------------------------------------------------------------------------------
namespace {
struct GirdiBaglami {
    KomutSatiri* ks;
    std::vector<const KomutTanimi*>* oneriler;
    int* secili;
    bool oneriAcik;
};
int GirdiGeriCagrisi(ImGuiInputTextCallbackData* v) {
    auto* g = static_cast<GirdiBaglami*>(v->UserData);
    if (v->EventFlag == ImGuiInputTextFlags_CallbackHistory) {
        if (g->oneriAcik && !g->oneriler->empty()) {
            const int n = static_cast<int>(g->oneriler->size());
            *g->secili = (*g->secili + (v->EventKey == ImGuiKey_UpArrow ? -1 : 1) + n) % n;
            return 0;
        }
        std::optional<std::string> s = v->EventKey == ImGuiKey_UpArrow ? g->ks->Onceki(std::string(v->Buf, v->BufTextLen))
                                                                       : g->ks->Sonraki();
        if (s) {
            v->DeleteChars(0, v->BufTextLen);
            v->InsertChars(0, s->c_str());
        }
    } else if (v->EventFlag == ImGuiInputTextFlags_CallbackCompletion) {
        if (!g->oneriler->empty()) {
            const KomutTanimi* t = (*g->oneriler)[static_cast<size_t>(std::clamp(*g->secili, 0, static_cast<int>(g->oneriler->size()) - 1))];
            std::string mevcut(v->Buf, v->BufTextLen);
            const size_t b = mevcut.find(' ');
            const std::string arguman = b == std::string::npos ? std::string() : mevcut.substr(b);
            v->DeleteChars(0, v->BufTextLen);
            v->InsertChars(0, (t->ad + (arguman.empty() ? " " : arguman)).c_str());
        }
    }
    return 0;
}
}  // namespace

void AnaPencere::KomutSatiriCiz(Ciz& c) {
    const auto& R = c.R();
    const float x0 = L_.ray, y0 = L_.alt + L_.rsekme + L_.rihtim, w = L_.W - L_.ray, h = L_.komut;
    // §2 rıhtım / komut: vurgu imleç çizgisi + komut simgesi + "Komut" (vurgu metni 600); ipuçları tuş rozetleri; TR · EN.
    c.Dikd(x0, y0, w, h, R.yuzey);
    c.Yatay(x0, x0 + w, y0, R.cizgi);
    c.Yatay(x0, x0 + w, y0 + h - 1, R.cizgi);
    c.Yuv(x0 + 6, y0 + 6, 3, h - 12, 1.5f, R.vurgu);
    c.Simge("konsol", x0 + 24, y0 + h / 2, 15, R.vurgu, 1.4f);
    const float ew = c.Yazi(x0 + 38, Taban(y0, h, 12), Tr("Komut"), 12, tema::Agirlik::Kalin, R.vurguMetin);
    c.Dusey(x0 + 38 + ew + 10, y0 + 8, y0 + h - 8, R.cizgi);
    const float gx = x0 + 38 + ew + 20;
    // öneriler
    std::vector<const KomutTanimi*> oneriler;
    if (h_.komutlar && komutAktif_) oneriler = komutSatiri_.Oneriler(*h_.komutlar, komutGirdi_, oneriKumesi_, 8);
    if (oneriSecili_ >= static_cast<int>(oneriler.size())) oneriSecili_ = 0;
    const bool oneriAcik = komutAktif_ && (komutGirdi_[0] != 0 || oneriKumesi_ != OneriKumesi::Tumu || !komutSatiri_.SonKomutlar().empty());
    // giriş kutusu
    const float yaziG = std::max(60.0f, c.Gen(komutGirdi_, 12, tema::Agirlik::Normal) + 24);
    ImGui::SetCursorScreenPos(c.P(gx - 2, y0 + (h - 20) / 2));
    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(c.S(2), c.S(3)));
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 0);
    ImGui::PushStyleColor(ImGuiCol_FrameBg, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleColor(ImGuiCol_FrameBgHovered, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleColor(ImGuiCol_FrameBgActive, IM_COL32(0, 0, 0, 0));
    ImGui::PushFont(c.F(tema::Agirlik::Normal), 12);
    ImGui::SetNextItemWidth(c.S(std::min(yaziG, w * 0.5f)));
    if (komutOdak_) {
        ImGui::SetKeyboardFocusHere();
        komutOdak_ = false;
    }
    GirdiBaglami gb{&komutSatiri_, &oneriler, &oneriSecili_, oneriAcik};
    const bool enter = ImGui::InputText("##komut", komutGirdi_, sizeof(komutGirdi_),
                                        ImGuiInputTextFlags_EnterReturnsTrue | ImGuiInputTextFlags_CallbackHistory |
                                            ImGuiInputTextFlags_CallbackCompletion | ImGuiInputTextFlags_EscapeClearsAll,
                                        GirdiGeriCagrisi, &gb);
    komutAktif_ = ImGui::IsItemActive();
    ImGui::PopFont();
    ImGui::PopStyleColor(3);
    ImGui::PopStyleVar(2);
    if (enter) {
        std::string ileti;
        const std::string satir = komutGirdi_;
        const size_t b = satir.find(' ');
        const std::string ad = satir.substr(0, b);
        const KomutTanimi* tam = h_.komutlar ? h_.komutlar->Bul(ad) : nullptr;
        bool tamam = false;
        if (h_.komutlar) {
            if (!tam && !oneriler.empty() && !ad.empty())
                tamam = komutSatiri_.OneriCalistir(*h_.komutlar, h_, *oneriler[static_cast<size_t>(oneriSecili_)], ileti);
            else
                tamam = komutSatiri_.Calistir(*h_.komutlar, h_, satir, ileti);
        }
        if (!ileti.empty() && h_.bildirim) h_.bildirim->KomutYaz(ileti);
        if (tamam && h_.komutlar && !komutSatiri_.SonKomutlar().empty()) {
            vurguluKomut_ = komutSatiri_.SonKomutlar().front();
            vurguBitis_ = simdi + 1000;
            if (const KomutTanimi* t = h_.komutlar->Bul(vurguluKomut_); t && t->serit) etkinSekme = t->serit->sekme;
        }
        komutGirdi_[0] = 0;
        oneriSecili_ = 0;
        komutOdak_ = true;  // yazmaya devam
    }
    // "· Son: …"
    float sx = gx + std::min(yaziG, w * 0.5f) + 4;
    const std::string son = komutSatiri_.SonKomutlar().empty() || !h_.komutlar ? std::string()
                            : h_.komutlar->Bul(komutSatiri_.SonKomutlar().front())
                                ? h_.komutlar->Bul(komutSatiri_.SonKomutlar().front())->ad
                                : std::string();
    std::string sonMetin = sonKomutIletisi.empty() ? std::string() : std::string(Tr("Son")) + ": " + (son.empty() ? "" : son + " — ") + sonKomutIletisi;
    if (!sonMetin.empty()) {
        c.Yazi(sx, Taban(y0, h, 12), "·", 12, tema::Agirlik::Normal, R.metin3);
        c.Yazi(sx + 12, Taban(y0, h, 12), sonMetin, 12, tema::Agirlik::Normal, R.metin3, w * 0.42f);
    }
    // sağ: ipuçları (tuş rozetleri) ve TR · EN takma ad çipi
    std::vector<std::pair<const char*, const char*>> ip{{"Ctrl+Q", "odakla / hızlı başlat"}, {"Tab", "tamamla"}, {"Enter", "yinele"}, {"Esc", "iptal"}};
    if (L_.dar) ip.resize(2);
    float xr = x0 + w - 12;
    const float kh = 18, ky = y0 + (h - kh) / 2;
    for (auto it = ip.rbegin(); it != ip.rend(); ++it) {
        const char* et = Tr(it->second);
        xr -= c.Gen(et, 10, tema::Agirlik::Normal);
        c.Yazi(xr, Taban(y0, h, 10), et, 10, tema::Agirlik::Normal, R.metin3);
        // rozet genişliği: önce ölç (çizimi saydam bir kopyada yapmamak için Kisayol'un ölçüsünü taklit et)
        float kw = 0;
        {
            std::string_view k = it->first;
            size_t b0 = 0;
            int n = 0;
            while (b0 <= k.size()) {
                size_t e = k.find('+', b0);
                if (e == std::string_view::npos) e = k.size();
                kw += std::max(kh, c.Gen(k.substr(b0, e - b0), 10, tema::Agirlik::Orta) + 10);
                ++n;
                b0 = e + 1;
            }
            kw += 3.0f * static_cast<float>(n - 1);
        }
        xr -= kw + 5;
        c.Kisayol(xr, ky, it->first, 10, kh);
        xr -= 14;
    }
    {
        const char* dilCip = "TR · EN";
        const float cw = c.Gen(dilCip, 10, tema::Agirlik::Kalin) + 14;
        xr -= cw;
        c.Yuv(xr, y0 + (h - 20) / 2, cw, 20, tema::belirtec::R.orta, R.zemin2);
        c.YaziOrta(xr + cw / 2, Taban(y0, h, 10), dilCip, 10, tema::Agirlik::Kalin, R.metin2);
        Tiklama(c, "##dil_cip", xr, y0 + (h - 20) / 2, cw, 20);
        OgeIpucu(c, Tr("Komut adları Türkçe ve İngilizce takma adlarla yazılabilir"));
    }
    // öneri kartı (komut satırının üstünde): Son / Şerit / Menü / Tümü
    if (oneriAcik && h_.komutlar) {
        const float kartW = 460, satirH = 22, kartH = 30 + satirH * static_cast<float>(std::max<size_t>(1, oneriler.size()));
        const float kx = gx - 8, kartY = y0 - kartH - 6;
        ImDrawList* on = ImGui::GetForegroundDrawList();
        Ciz k = c;
        k.dl = on;
        k.Golge(kx, kartY, kartW, kartH, 4, 6, 0.16f, 2);
        k.Yuv(kx, kartY, kartW, kartH, 4, R.yuzey, R.cizgi);
        struct Kume {
            OneriKumesi k;
            const char* ad;
        };
        const Kume kumeler[4] = {{OneriKumesi::Tumu, "Tümü"}, {OneriKumesi::Son, "Son"}, {OneriKumesi::Serit, "Şerit"}, {OneriKumesi::Menu, "Menü"}};
        float tx = kx + 10;
        for (const Kume& km : kumeler) {
            const char* ad = Tr(km.ad);
            const float tw = k.Gen(ad, 11, tema::Agirlik::Orta);
            const bool etkin = oneriKumesi_ == km.k;
            k.Yazi(tx, Taban(kartY, 24, 11), ad, 11, etkin ? tema::Agirlik::Kalin : tema::Agirlik::Orta, etkin ? R.metin : R.metin2);
            if (etkin) k.Yatay(tx - 2, tx + tw + 2, kartY + 22, R.vurgu, 2);
            const ImVec2 mp = ImGui::GetIO().MousePos;
            if (ImGui::IsMouseClicked(ImGuiMouseButton_Left) && mp.x >= c.S(tx - 4) && mp.x < c.S(tx + tw + 4) && mp.y >= c.S(kartY) &&
                mp.y < c.S(kartY + 24)) {
                oneriKumesi_ = km.k;
                komutOdak_ = true;
            }
            tx += tw + 16;
        }
        k.YaziSag(kx + kartW - 10, Taban(kartY, 24, 10), Tr("↑↓ seç · Tab tamamla · Enter çalıştır"), 10, tema::Agirlik::Normal, R.metin3);
        k.Yatay(kx, kx + kartW, kartY + 26, R.cizgi2);
        float yy = kartY + 28;
        if (oneriler.empty()) k.Yazi(kx + 12, Taban(yy, satirH, 11), Tr("Eşleşen komut yok"), 11, tema::Agirlik::Normal, R.metin3);
        for (size_t i = 0; i < oneriler.size(); ++i) {
            const KomutTanimi* t = oneriler[i];
            const KomutDurumu d = h_.komutlar->Durum(t->id, h_);
            if (static_cast<int>(i) == oneriSecili_) k.Dikd(kx + 1, yy, kartW - 2, satirH, R.vurguTon);
            k.Simge(t->ikon, kx + 18, yy + satirH / 2, 14, d.kullanilabilir ? R.ikonKucuk : R.ikonKapali, 1.4f);
            const float g = k.Yazi(kx + 34, Taban(yy, satirH, 12), Tr(t->etiket.c_str()), 12, tema::Agirlik::Orta,
                                   d.kullanilabilir ? R.metin : R.metin3);
            std::string adlar = t->ad;
            for (const std::string& a : t->takmaAdlar) adlar += " · " + a;
            k.Yazi(kx + 34 + g + 10, Taban(yy, satirH, 10), adlar, 10, tema::Agirlik::Normal, R.metin3, kartW - g - 150);
            if (!t->kisayol.empty()) k.YaziSag(kx + kartW - 10, Taban(yy, satirH, 10), t->kisayol, 10, tema::Agirlik::Orta, R.metin2);
            yy += satirH;
        }
        Engel(kx, kartY, kartW, kartH);
    }
}

// ---- durum çubuğu --------------------------------------------------------------------------------------------------------
void AnaPencere::DurumCubuguCiz(Ciz& c) {
    // §2 durum çubuğu: yönerge │ ORTO YAKALA SÜRÜKLE çipleri · X Y Z kilitleri │ kat kapsamı (vurgu segmenti) · etkin kat ·
    // birim · XYZ · seçim çipi. Kat kapsamı anahtarı her yoğunlukta görünür (§9.7).
    const auto& R = c.R();
    const float W = L_.W, y0 = L_.H - L_.durum, h = L_.durum;
    const float ch = 20, cy = y0 + (h - ch) / 2, r6 = tema::belirtec::R.orta;
    c.Dikd(0, y0, W, h, R.zemin);
    c.Yatay(0, W, y0, R.cizgi);
    // sol: adım yönergesi
    c.Daire(14, y0 + h / 2, 3, R.vurgu);
    std::string y = yonerge;
    if (y.empty())
        y = L_.dar ? Tr("Nesne seçin — Ctrl: tersle · Shift: çıkar")
                   : Tr("Nesne seçin — Ctrl: tersle · Shift: çıkar · Ctrl + sürükle: pencere · Shift + sürükle: döndür");
    // sağ blok (sağdan sola): seçim çipi · koordinat · birim · etkin kat · kat kapsamı
    float xr = W - 10;
    {
        const size_t n = h_.secim ? h_.secim->Sayi() : 0;
        const std::string sm = Trf("%zu seçili", n);
        const std::string tm = n > 0 && dogrudanDegistirme && !L_.dar ? Trf("%zu tutamaç", 2 * n) : std::string();
        const float sw = c.Gen(sm, 11, tema::Agirlik::Kalin) + (tm.empty() ? 0 : c.Gen(tm, 10, tema::Agirlik::Normal) + 8) + 24;
        xr -= sw;
        if (n > 0) {
            c.Yuv(xr, cy, sw, ch, r6, R.secimTon, R.secimTon2);
            c.Daire(xr + 10, cy + ch / 2, 3, R.secim);
        } else {
            c.Yuv(xr, cy, sw, ch, r6, 0, R.cizgi);
            c.Daire(xr + 10, cy + ch / 2, 3, R.metin4);
        }
        const float tw = c.Yazi(xr + 18, Taban(y0, h, 11), sm, 11, tema::Agirlik::Kalin, n > 0 ? R.vurguMetin : R.metin3);
        if (!tm.empty()) c.Yazi(xr + 18 + tw + 8, Taban(y0, h, 10), tm, 10, tema::Agirlik::Normal, R.metin3);
        xr -= 14;
    }
    {
        const V3d p = imlecDunyaVar_ ? imlecDunya_ : V3d{};
        const std::string ko = "X " + Sayi(p.x, 3) + "   Y " + Sayi(p.y, 3) + "   Z " + Sayi(p.z, 3);
        xr -= c.YaziSag(xr, Taban(y0, h, 11), ko, 11, tema::Agirlik::Normal, R.metin2) + 14;
    }
    {
        const std::string birim = h_.ayarlar && h_.ayarlar->arayuz.birimSistemi == "teknik" ? "tf · m" : "kN · m";
        const float bw = c.Gen(birim, 11, tema::Agirlik::Orta) + 30;
        xr -= bw;
        if (Tiklama(c, "##birim", xr, cy, bw, ch)) {
            ayarlarAcik = true;
            ayarSayfasi = 2;
        }
        const bool ust = ImGui::IsItemHovered();
        c.Yuv(xr, cy, bw, ch, r6, ust ? R.hover : 0, R.cizgi);
        c.Yazi(xr + 8, Taban(y0, h, 11), birim, 11, tema::Agirlik::Orta, R.metin2);
        c.Sevron(xr + bw - 11, cy + ch / 2, 0, 9, R.metin2);
        OgeIpucu(c, Tr("Birim sistemi (Ayarlar › Dil ayarları)"));
        xr -= 10;
    }
    if (!L_.dar) {  // küçük ekranda gizlenir (§9.7; PageUp / PageDown ve ağaç yine çalışır)
        const std::string et = std::string(Tr("Etkin kat")) + ": " + KatAdi(etkinKat, false);
        const float tw = c.Gen(et, 11, tema::Agirlik::Orta) + 30;
        xr -= tw;
        if (Tiklama(c, "##etkin_kat", xr, cy, tw, ch)) ImGui::OpenPopup("##etkin_kat_menu");
        const bool ust = ImGui::IsItemHovered();
        c.Yuv(xr, cy, tw, ch, r6, ust ? R.hover : 0, R.cizgi);
        c.Yazi(xr + 8, Taban(y0, h, 11), et, 11, tema::Agirlik::Orta, R.metin2);
        c.Sevron(xr + tw - 11, cy + ch / 2, 0, 9, R.metin2);
        OgeIpucu(c, Tr("Etkin kat: çizim, seçim ve atamanın kat bağlamı"), "PageUp / PageDown");
        if (ImGui::BeginPopup("##etkin_kat_menu")) {
            for (int i = static_cast<int>(sahne_->seviyeler.size()) - 1; i >= 0; --i)
                if (sahne_->seviyeler[static_cast<size_t>(i)].kat >= 0 && ImGui::MenuItem(KatAdi(i).c_str(), nullptr, i == etkinKat)) {
                    etkinKat = i;
                    if (yon_ == StandartYon::Plan) kamera_.d.hedef.z = sahne_->seviyeler[static_cast<size_t>(i)].z;
                }
            if (sahne_->seviyeler.empty()) ImGui::TextDisabled("%s", Tr("Modelde kat yok"));
            ImGui::EndPopup();
        }
        xr -= 14;
    }
    // kat kapsamı: üç durumlu vurgu segmenti (Alt+1/2/3; MIMARI §25.1)
    float sx = xr;
    {
        const std::vector<std::string> secenek = {Tr("Bu kat"), Tr("Benzer katlar"), Tr("Tüm katlar")};
        const bool etkin = sahne_->seviyeler.size() > 1;
        float toplam = 0;
        for (const std::string& e : secenek) toplam += c.Gen(e, 11, tema::Agirlik::Kalin) + 20;
        toplam += 4;
        sx = xr - toplam;
        static const char* const komutlar[3] = {"kapsam.bu_kat", "kapsam.benzer", "kapsam.tum"};
        const int t = Segmentli(c, "##kapsam", sx, cy, ch, secenek, static_cast<int>(kapsam), true, 11, 0, nullptr, etkin);
        OgeIpucu(c, Tr("Kat kapsamı: çizim, seçim, atama ve silme (temel / zemin hariç)"), "Alt+1 / 2 / 3");
        if (t >= 0) KomutCalistir(komutlar[t], KomutKaynagi::Menu);
        float lx = sx - 8;
        if (!L_.dar) {
            lx -= c.YaziSag(lx, Taban(y0, h, 11), Tr("Kat kapsamı"), 11, tema::Agirlik::Normal, R.metin3) + 6;
        }
        c.Simge("katman", lx - 7, y0 + h / 2, 14, R.ikonKucuk, 1.3f);
        sx = lx - 16;
    }
    // orta: ORTO / YAKALA / SÜRÜKLE çipleri, X Y Z kilitleri, orta tuş ipucu
    static bool orto = false, yakala = true, surukle = false;
    static bool kilit[3] = {false, false, false};
    struct Anahtar {
        const char* et;
        bool* durum;
        const char* ipucu;
    };
    Anahtar anahtarlar[3] = {{"ORTO", &orto, "Ortogonal kip (F8) — çizim komutları Faz 4"},
                             {"YAKALA", &yakala, "Nesne yakalama (F3) — Faz 4"},
                             {"SÜRÜKLE", &surukle, "Sürükle-bırak düzenleme — Faz 4"}};
    float orta = 0;
    for (const Anahtar& a : anahtarlar) orta += c.Gen(Tr(a.et), 10, tema::Agirlik::Kalin) + 22 + 4;
    orta += 8 + 3 * 24 + (L_.dar ? 0 : 12 + c.Gen(Tr("Orta tuş: kaydır"), 10, tema::Agirlik::Normal));
    float x = std::max(22 + std::min(c.Gen(y, 11, tema::Agirlik::Orta), W * 0.3f) + 20, sx - orta - 24);
    c.Yazi(24, Taban(y0, h, 11), y, 11, tema::Agirlik::Orta, R.metin, x - 44);
    for (const Anahtar& a : anahtarlar) {
        const char* et = Tr(a.et);
        ImGui::PushID(a.et);
        const float cw = c.Gen(et, 10, tema::Agirlik::Kalin) + 22;
        if (Tiklama(c, "##anahtar", x, cy, cw, ch)) *a.durum = !*a.durum;
        ImGui::PopID();
        OgeIpucu(c, Tr(a.ipucu));
        x += Cip(c, x, cy, ch, et, *a.durum) + 4;
    }
    x += 8;
    for (int i = 0; i < 3; ++i) {
        const char et[2] = {static_cast<char>('X' + i), 0};
        ImGui::PushID(i + 50);
        if (Tiklama(c, "##kilit", x, cy, 20, ch)) kilit[i] = !kilit[i];
        ImGui::PopID();
        OgeIpucu(c, Tr("Eksen kilidi — Faz 4"));
        if (kilit[i]) {
            c.Yuv(x, cy, 20, ch, tema::belirtec::R.kucuk, R.vurgu);
            c.YaziOrta(x + 10, Taban(cy, ch, 10), et, 10, tema::Agirlik::Kalin, R.beyaz);
        } else {
            c.Yuv(x, cy, 20, ch, tema::belirtec::R.kucuk, 0, R.cizgi);
            c.YaziOrta(x + 10, Taban(cy, ch, 10), et, 10, tema::Agirlik::Kalin, R.metin3);
        }
        x += 24;
    }
    if (!L_.dar) c.Yazi(x + 8, Taban(y0, h, 10), Tr("Orta tuş: kaydır"), 10, tema::Agirlik::Normal, R.metin3);
    // grafik bağdaştırıcısı (yazılım işleyici uyarısı; kabul C8) — kapsamın solunda
    if (warp && !L_.dar) {
        const char* uyari = Tr("yazılım işleyici");
        const float uw = c.Gen(uyari, 10, tema::Agirlik::Kalin) + 22;
        const float ux = x + 8 + c.Gen(Tr("Orta tuş: kaydır"), 10, tema::Agirlik::Normal) + 12;
        if (ux + uw < sx - 8) {
            Tiklama(c, "##warp", ux, cy, uw, ch);
            OgeIpucu(c, bagdastirici);
            c.Yuv(ux, cy, uw, ch, r6, R.uyariTon, tema::Alfa(R.uyariDolgu, 0.7f));
            c.Simge("uyari", ux + 10, y0 + h / 2, 11, R.uyari, 1.4f);
            c.Yazi(ux + 19, Taban(cy, ch, 10), uyari, 10, tema::Agirlik::Kalin, R.uyari);
        }
    }
    // diğer paketlerin durum öğeleri (S21) — sağdakiler yönergenin sağına, küçük ImGui grubu olarak
    if (h_.arayuz && !h_.arayuz->DurumOgeleri().empty()) {
        float ox = 24 + std::min(c.Gen(y, 11, tema::Agirlik::Orta), W * 0.3f) + 16;
        for (const DurumOgesi& o : h_.arayuz->DurumOgeleri()) {
            if (o.sahip == "C" || !o.ciz) continue;
            ImGui::SetCursorScreenPos(c.P(ox, y0 + 4));
            ImGui::PushID(o.id.c_str());
            ImGui::BeginGroup();
            ImGui::PushFont(c.F(tema::Agirlik::Normal), 11);
            o.ciz();
            ImGui::PopFont();
            ImGui::EndGroup();
            ox += ImGui::GetItemRectSize().x / olcek_ + 12;
            ImGui::PopID();
        }
    }
}

}  // namespace op4
