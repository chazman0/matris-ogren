// op4 arayüzü — şerit (sekme satırı + gövde), Dosya menüsü ve kısayollar; hepsi komutlar.json'dan (MIMARI §5.3,
// atolye uret.py serit()). Bağsız / kullanılamayan komut soluk çizilir, nedeni ipucundadır (kabul C1).
#include <algorithm>
#include <cstring>
#include <map>

#include "arayuz/ana_pencere.h"
#include "arayuz/dil.h"
#include "cekirdek/komut.h"
#include "imgui_internal.h"

namespace op4 {
namespace {

struct SeritGrubu {
    std::string ad;
    int sira = 0;
    std::vector<const KomutTanimi*> buyukler, kucukler;
};

std::vector<SeritGrubu> Gruplar(const KomutYoneticisi& k, const std::string& sekme) {
    std::vector<SeritGrubu> g;
    for (const KomutTanimi& t : k.Tanimlar()) {
        if (!t.serit || t.serit->sekme != sekme) continue;
        auto it = std::find_if(g.begin(), g.end(), [&](const SeritGrubu& x) { return x.ad == t.serit->grup; });
        if (it == g.end()) {
            g.push_back({t.serit->grup, t.serit->sira, {}, {}});
            it = g.end() - 1;
        }
        it->sira = std::min(it->sira, t.serit->sira);
        (t.serit->buyuk ? it->buyukler : it->kucukler).push_back(&t);
    }
    auto sirala = [](std::vector<const KomutTanimi*>& v) {
        std::stable_sort(v.begin(), v.end(), [](const KomutTanimi* a, const KomutTanimi* b) { return a->serit->sira < b->serit->sira; });
    };
    for (SeritGrubu& x : g) {
        sirala(x.buyukler);
        sirala(x.kucukler);
    }
    std::stable_sort(g.begin(), g.end(), [](const SeritGrubu& a, const SeritGrubu& b) { return a.sira < b.sira; });
    return g;
}

// "Ctrl+Shift+S" → ImGuiKeyChord (0 = çözülemedi).
ImGuiKeyChord Akor(const std::string& k) {
    if (k.empty()) return 0;
    ImGuiKeyChord m = 0;
    size_t b = 0;
    std::string tus;
    while (b <= k.size()) {
        size_t s = k.find('+', b);
        if (s == std::string::npos) s = k.size();
        const std::string p = k.substr(b, s - b);
        if (p == "Ctrl") m |= ImGuiMod_Ctrl;
        else if (p == "Shift") m |= ImGuiMod_Shift;
        else if (p == "Alt") m |= ImGuiMod_Alt;
        else tus = p;
        b = s + 1;
    }
    ImGuiKey key = ImGuiKey_None;
    if (tus.size() == 1 && tus[0] >= 'A' && tus[0] <= 'Z') key = static_cast<ImGuiKey>(ImGuiKey_A + (tus[0] - 'A'));
    else if (tus.size() == 1 && tus[0] >= '0' && tus[0] <= '9') key = static_cast<ImGuiKey>(ImGuiKey_0 + (tus[0] - '0'));
    else if (tus.size() >= 2 && tus[0] == 'F') key = static_cast<ImGuiKey>(ImGuiKey_F1 + (std::atoi(tus.c_str() + 1) - 1));
    else if (tus == "PageUp") key = ImGuiKey_PageUp;
    else if (tus == "PageDown") key = ImGuiKey_PageDown;
    else if (tus == "Escape") key = ImGuiKey_Escape;
    else if (tus == "Delete") key = ImGuiKey_Delete;
    else if (tus == "Enter") key = ImGuiKey_Enter;
    else if (tus == "Space") key = ImGuiKey_Space;
    else if (tus == "Tab") key = ImGuiKey_Tab;
    else if (tus == "Home") key = ImGuiKey_Home;
    else if (tus == "End") key = ImGuiKey_End;
    else if (tus == "Insert") key = ImGuiKey_Insert;
    else if (tus == "Backspace") key = ImGuiKey_Backspace;
    else if (tus == ",") key = ImGuiKey_Comma;
    else if (tus == ".") key = ImGuiKey_Period;
    return key == ImGuiKey_None ? 0 : (m | key);
}

}  // namespace

bool AnaPencere::KomutDugmesi(Ciz& c, const KomutTanimi& t, float x, float y, float w, float h, bool buyuk) {
    // Atölye · Modern §8 şerit: basılı araç vurgu tonu + vurgu tonu 2 kenar + vurgu simge + vurgu metni 600.
    const auto& R = c.R();
    const KomutDurumu d = h_.komutlar->Durum(t.id, h_);
    const bool basili = d.isaretli || (vurguluKomut_ == t.id && simdi < vurguBitis_);
    ImGui::PushID(t.id.c_str());
    const bool tik = Tiklama(c, "##k", x, y, w, h);
    const bool ust = ImGui::IsItemHovered();
    const bool basiliTut = ImGui::IsItemActive();
    ImGui::PopID();
    const float r = tema::belirtec::R.orta;
    const uint32_t ikonRenk = !d.kullanilabilir ? R.ikonKapali : (basili ? R.vurgu : R.ikonBuyuk);
    const uint32_t yaziRenk = !d.kullanilabilir ? R.metin4 : (basili ? R.vurguMetin : R.metin);
    const std::string etiket = Tr(t.etiket.c_str());
    if (buyuk) {
        if (basili)
            c.Yuv(x, y, w, h, r, R.vurguTon, R.vurguTon2);
        else if (basiliTut && d.kullanilabilir)
            c.Yuv(x, y, w, h, r, R.basili);
        else if (ust && d.kullanilabilir)
            c.Yuv(x, y, w, h, r, R.hover);
        const float ik = L_.dar ? 22.0f : 24.0f;
        c.Simge(t.ikon, x + w / 2, y + h * 0.36f, ik, ikonRenk, 1.5f);
        c.YaziOrta(x + w / 2, y + h - 10, etiket, 11, basili ? tema::Agirlik::Kalin : tema::Agirlik::Orta, yaziRenk);
    } else {
        if (basili)
            c.Yuv(x - 3, y, w + 3, h, r, R.vurguTon, R.vurguTon2);
        else if (ust && d.kullanilabilir)
            c.Yuv(x - 3, y, w + 3, h, r, basiliTut ? R.basili : R.hover);
        c.Simge(t.ikon, x + 8, y + h / 2, 16, ikonRenk, 1.4f);
        c.Yazi(x + 22, Taban(y, h, 11), etiket, 11, basili ? tema::Agirlik::Kalin : tema::Agirlik::Normal, yaziRenk);
    }
    std::string ipucu = d.kullanilabilir ? (t.ipucu.empty() ? etiket : std::string(Tr(t.ipucu.c_str()))) : d.neden;
    OgeIpucu(c, ipucu, t.kisayol);
    if (tik && d.kullanilabilir) KomutCalistir(t.id, KomutKaynagi::Serit);
    else if (tik && h_.bildirim) h_.bildirim->KomutYaz(d.neden);
    return tik;
}

void AnaPencere::SeritCiz(Ciz& c) {
    const auto& R = c.R();
    const float W = L_.W, y0 = L_.baslik, sh = L_.sekme;
    c.Dikd(0, y0, W, sh, R.zemin);
    // Dosya: vurgu dolgulu düğme (6 px yarıçap), 12/600 beyaz (arka plan menüsü).
    const float dh = sh - 8, dw = c.Gen(Tr("Dosya"), 12, tema::Agirlik::Kalin) + 26;
    const bool dosyaTik = Tiklama(c, "##dosya", 8, y0 + 4, dw, dh);
    const bool dosyaUst = ImGui::IsItemHovered();
    c.Yuv(8, y0 + 4, dw, dh, tema::belirtec::R.orta, dosyaUst ? R.vurguKoyu : R.vurgu);
    c.YaziOrta(8 + dw / 2, Taban(y0 + 4, dh, 12), Tr("Dosya"), 12, tema::Agirlik::Kalin, R.beyaz);
    if (dosyaTik) ImGui::OpenPopup("##dosya_menusu");
    float x = 8 + dw + 10;
    const float govdeY = y0 + sh;
    std::vector<std::string> sekmeler = h_.komutlar ? h_.komutlar->Sekmeler() : std::vector<std::string>{};
    sekmeler.erase(std::remove(sekmeler.begin(), sekmeler.end(), std::string("Dosya")), sekmeler.end());
    // Sekmeler: metin sekmesi, etkin 600 + 3 px yuvarlak vurgu alt çizgi.
    for (const std::string& s : sekmeler) {
        const std::string ad = Tr(s.c_str());
        const float tw = c.Gen(ad, 12, tema::Agirlik::Kalin), w = tw + 26;
        ImGui::PushID(s.c_str());
        if (Tiklama(c, "##sekme", x, y0 + 2, w, sh - 2)) etkinSekme = s;
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        const bool etkin = s == etkinSekme;
        if (ust && !etkin) c.Yuv(x + 3, y0 + 4, w - 6, sh - 8, tema::belirtec::R.orta, R.hover);
        c.YaziOrta(x + w / 2, Taban(y0, sh, 12), ad, 12, etkin ? tema::Agirlik::Kalin : tema::Agirlik::Orta,
                   etkin || ust ? R.metin : R.metin2);
        if (etkin) c.Yuv(x + 13 - 4, y0 + sh - 3, tw + 8, 3, 1.5f, R.vurgu);
        x += w;
    }
    // Sağ: "Şeridi özelleştir" (göz simgesi) ve daralt.
    {
        const std::string ozel = Tr("Şeridi özelleştir");
        const float ow = c.Gen(ozel, 11, tema::Agirlik::Orta);
        const float ox = W - 34 - ow - 20;
        Tiklama(c, "##ozellestir", ox - 4, y0 + 4, ow + 26, sh - 8);
        const bool ust = ImGui::IsItemHovered();
        if (ust) c.Yuv(ox - 4, y0 + 4, ow + 26, sh - 8, tema::belirtec::R.orta, R.hover);
        c.Simge("goz", ox + 7, y0 + sh / 2, 14, R.ikonKucuk, 1.3f);
        c.Yazi(ox + 18, Taban(y0, sh, 11), ozel, 11, tema::Agirlik::Orta, R.metin2);
        OgeIpucu(c, Tr("Şerit düzeni Faz 3'te özelleştirilebilir"));
        c.Simge("sevron_ust", W - 20, y0 + sh / 2, 12, R.metin2, 1.4f);
    }

    // Gövde: gruplar — büyük düğme + 3'lü küçük sütun, grup adı altta (10/500 ortalı), 1 px ayraç.
    const float gy = govdeY, gh = L_.serit;
    c.Dikd(0, gy, W, gh, R.yuzey);
    c.Yatay(0, W, gy, R.cizgi);
    c.Yatay(0, W, gy + gh - 1, R.cizgi);
    if (!h_.komutlar) return;
    const tema::Olculer& o = tema::Etkin().o;
    const float buyukH = gh - 28, ks = o.kucukAdim;
    x = 8;
    static const char* const kDarGizli[] = {"Kolon", "Çapraz", "Döşeme", "Duvar", "Temel", "Betonarme"};
    for (const SeritGrubu& g : Gruplar(*h_.komutlar, etkinSekme)) {
        const float gx0 = x;
        x += 6;
        for (const KomutTanimi* t : g.buyukler) {
            const float bw = std::max(o.buyukDugmeEnAz, c.Gen(Tr(t->etiket.c_str()), 11, tema::Agirlik::Kalin) + 18);
            if (x + bw > W - 8) break;
            KomutDugmesi(c, *t, x, gy + 6, bw, buyukH, true);
            x += bw + 2;
        }
        const bool kucukGizli = L_.dar && std::find(std::begin(kDarGizli), std::end(kDarGizli), g.ad) != std::end(kDarGizli);
        if (!g.kucukler.empty() && !kucukGizli) {
            x += 6;
            float kw = 0;
            for (const KomutTanimi* t : g.kucukler) kw = std::max(kw, c.Gen(Tr(t->etiket.c_str()), 11, tema::Agirlik::Kalin));
            kw += 30;
            if (x + kw > W - 8) break;
            const float ky = gy + 6 + (buyukH - 3 * ks) / 2;
            for (size_t j = 0; j < g.kucukler.size() && j < 3; ++j)
                KomutDugmesi(c, *g.kucukler[j], x, ky + static_cast<float>(j) * ks, kw - 6, ks, false);
            x += kw;
        }
        x += 6;
        const float gw = x - gx0;
        c.YaziOrta(gx0 + gw / 2, gy + gh - 8, Tr(g.ad.c_str()), 10, tema::Agirlik::Orta, R.metin3);
        c.Dusey(x, gy + 10, gy + gh - 10, R.cizgi2);
        x += 1;
    }
}

void AnaPencere::DosyaMenusu(Ciz& c) {
    (void)c;
    ImGui::SetNextWindowPos(ImVec2(8 * olcek_, (L_.baslik + L_.sekme) * olcek_));
    if (!ImGui::BeginPopup("##dosya_menusu")) return;
    if (h_.komutlar) {
        std::vector<const KomutTanimi*> v;
        for (const KomutTanimi& t : h_.komutlar->Tanimlar())
            if (t.menu.rfind("Dosya", 0) == 0) v.push_back(&t);
        std::stable_sort(v.begin(), v.end(), [](const KomutTanimi* a, const KomutTanimi* b) { return a->menuSira < b->menuSira; });
        int onceki = -1;
        for (const KomutTanimi* t : v) {
            if (onceki >= 0 && t->menuSira / 30 != onceki / 30) ImGui::Separator();
            onceki = t->menuSira;
            const KomutDurumu d = h_.komutlar->Durum(t->id, h_);
            if (ImGui::MenuItem(Tr(t->etiket.c_str()), t->kisayol.c_str(), false, d.kullanilabilir))
                KomutCalistir(t->id, KomutKaynagi::Menu);
            if (!d.kullanilabilir && ImGui::IsItemHovered(ImGuiHoveredFlags_AllowWhenDisabled)) ImGui::SetTooltip("%s", d.neden.c_str());
        }
    }
    if (h_.arayuz) {
        const auto son = h_.arayuz->MenuKatkilari("Dosya/Son dosyalar");
        if (!son.empty() && ImGui::BeginMenu(Tr("Son dosyalar"))) {
            for (const MenuKatkisi* m : son)
                if (m->ciz) m->ciz();
            ImGui::EndMenu();
        }
    }
    ImGui::Separator();
    if (ImGui::MenuItem(Tr("Ayarlar…"))) KomutCalistir("ayarlar.ac", KomutKaynagi::Menu);
    ImGui::EndPopup();
}

void AnaPencere::KisayollariIsle() {
    if (!h_.komutlar) return;
    const ImGuiIO& io = ImGui::GetIO();
    const bool yaziyor = io.WantTextInput;
    // Ctrl+Q ve ':' komut satırına odaklar (hızlı başlat).
    if (ImGui::IsKeyChordPressed(ImGuiMod_Ctrl | ImGuiKey_Q)) komutOdak_ = true;
    for (const KomutTanimi& t : h_.komutlar->Tanimlar()) {
        const ImGuiKeyChord a = Akor(t.kisayol);
        if (!a) continue;
        const ImGuiKey key = static_cast<ImGuiKey>(a & ~ImGuiMod_Mask_);
        const bool fTusu = key >= ImGuiKey_F1 && key <= ImGuiKey_F24;
        const bool degistirici = (a & (ImGuiMod_Ctrl | ImGuiMod_Alt)) != 0;
        if (yaziyor && !degistirici && !fTusu) continue;
        if (ImGui::IsKeyChordPressed(a)) KomutCalistir(t.id, KomutKaynagi::Kisayol);
    }
    // Esc sırası (MIMARI §25.1): açık açılır pencere → etkin komut / sürükleme → seçim. Komut satırına yazılırken Esc
    // girdiyi temizler (InputText). Seçimi temizlemenin ikinci kısayolu Ctrl+Shift+A (secim.temizle).
    if (!yaziyor && ImGui::IsKeyPressed(ImGuiKey_Escape, false)) {
        if (escPopupAcikti_) {
            // açılır pencereyi ImGui kapattı; başka bir şey yapma
        } else if (gezinme_.Surukluyor() || gezinme_.PencereSeciyor()) {
            gezinme_.Iptal();
        } else if (h_.secim && !h_.secim->Bos()) {
            h_.secim->Temizle();
        }
    }
    // Görünüm alanındayken yazılan harfler komut satırına gider (MIMARI §5.4).
    if (!yaziyor && !io.KeyCtrl && !io.KeyAlt && !io.InputQueueCharacters.empty() && !ImGui::IsPopupOpen("", ImGuiPopupFlags_AnyPopupId)) {
        for (const ImWchar ch : io.InputQueueCharacters) {
            if (ch == ':') {
                komutOdak_ = true;
                continue;
            }
            if (ch < 32) continue;
            char b[8] = {};
            ImTextCharToUtf8(b, ch);
            const size_t n = std::strlen(komutGirdi_);
            if (n + std::strlen(b) < sizeof(komutGirdi_) - 1) std::strcat(komutGirdi_, b);
            komutOdak_ = true;
        }
    }
}

}  // namespace op4
