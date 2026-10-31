// op4 arayüzü — paneller: sol ray (ÇİZ paleti + SEÇ anahtarları), model ağacı, Özellikler (salt okunur, F1), Başlangıç,
// pencere şeridi (atolye uret.py ray, model_agaci, ozellikler, pencere_seridi).
#include <algorithm>
#include <cmath>
#include <cstring>

#include <nlohmann/json.hpp>

#include "arayuz/ana_pencere.h"
#include "arayuz/dil.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/komut.h"
#include "cekirdek/proje_belgesi.h"
#include "cekirdek/secim.h"
#include "cekirdek/turkce.h"
#include "platform/dosya_sistemi.h"

namespace op4 {
namespace {

// Ağaç düğümünün simgesi (anahtar yolundan).
const char* DugumSimgesi(const std::string& anahtar) {
    if (anahtar == "proje") return "proje";
    if (anahtar == "katlar") return "kat";
    const size_t a = anahtar.rfind('/');
    const std::string son = a == std::string::npos ? anahtar : anahtar.substr(a + 1);
    if (son.rfind("kat:", 0) == 0) return "kat";
    if (son.rfind("alt_tur:", 0) == 0) {
        const std::string t = son.substr(8);
        if (t == "kolon") return "kolon";
        if (t == "kiris") return "kiris";
        if (t == "asik") return "kiris_tali";
        if (t == "capraz") return "capraz";
        if (t == "doseme" || t == "cati" || t == "cephe") return "doseme";
        if (t == "dugum") return "dugum";
        if (t == "mesnet") return "mesnet";
        if (t == "temel") return "temel";
        return "cubuk";
    }
    return "etiket";
}

// Şablonlar: D'nin veri/sablonlar/dizin.json'u yoksa bilinen 9 şablonun adları (Başlangıç paneli; tıklama dosya.yeni_sablon).
struct SablonBilgisi {
    const char* ad;
    const char* baslik;
    int kat;
    const char* aks;
    const char* sistem;
};
constexpr SablonBilgisi kSablonlar[] = {
    {"betonarme-tek-aciklik", "Tek açıklıklı betonarme çerçeve", 1, "2×2", "betonarme"},
    {"betonarme-2kat-3x2", "2 katlı betonarme konut", 2, "3×2", "betonarme"},
    {"betonarme-3kat-3x3", "3 katlı betonarme büro", 3, "3×3", "betonarme"},
    {"betonarme-4kat-4x3", "4 katlı betonarme konut", 4, "4×3", "betonarme"},
    {"betonarme-3kat-surekli-temel", "3 katlı konut, mütemadi temel", 3, "3×3", "betonarme"},
    {"betonarme-4kat-radye", "4 katlı konut, radye temel", 4, "4×3", "betonarme"},
    {"celik-1kat-depo", "Tek katlı çelik depo / atölye", 1, "3×2", "celik"},
    {"celik-cbf-3kat", "3 katlı çelik çaprazlı çerçeve", 3, "4×3", "celik"},
    {"celik-sanayi-4hol", "Çelik sanayi yapısı, 4 hol", 1, "9×7", "celik"},
};

// veri/sablonlar/dizin.json (D; TASARIM §21) → başlık, kısa özet ("1 kat · 2×2 aks"), sistem. Okunamazsa yerleşik yedek.
struct SablonSatiri {
    std::string ad, baslik, aks, sistem;
    int kat = 0;
};
const std::vector<SablonSatiri>& Sablonlar(const std::string& veriDizini) {
    static std::vector<SablonSatiri> liste;
    static bool okundu = false;
    if (okundu) return liste;
    okundu = true;
    std::string metin, hata;
    if (DosyaOku(veriDizini + "/sablonlar/dizin.json", metin, hata, size_t{1} << 22)) {  // UTF-8 yol (platform katmanı)
        const nlohmann::json j = nlohmann::json::parse(metin, nullptr, false);
        if (!j.is_discarded() && j.contains("sablonlar") && j["sablonlar"].is_array())
            for (const nlohmann::json& k : j["sablonlar"]) {
                if (!k.is_object() || !k.contains("ad") || !k["ad"].is_string()) continue;
                SablonSatiri s;
                s.ad = k["ad"].get<std::string>();
                s.baslik = k.value("baslik", s.ad);
                const size_t parantez = s.baslik.find(" (");  // "… (3×2 aks)" ayrıntısı özet satırına
                if (parantez != std::string::npos) s.baslik.resize(parantez);
                s.kat = k.value("kat", 0);
                s.aks = k.value("aks", std::string());
                s.sistem = k.value("sistem", std::string());
                liste.push_back(std::move(s));
            }
    }
    if (liste.empty())
        for (const SablonBilgisi& b : kSablonlar) liste.push_back({b.ad, b.baslik, b.aks, b.sistem, b.kat});
    return liste;
}

// Öznitelik kodlarının görünen adı (alt_tur, kullanim_yeri).
std::string KodAdi(const std::string& k) {
    static const std::pair<const char*, const char*> adlar[] = {
        {"kolon", "Kolon"}, {"kiris", "Kiriş"}, {"doseme", "Döşeme"}, {"cati", "Çatı"}, {"cephe", "Cephe"},
        {"capraz", "Çapraz"}, {"makas-ust", "Makas üst başlığı"}, {"makas-alt", "Makas alt başlığı"},
        {"makas-dikme", "Makas dikmesi"}, {"makas-diyagonal", "Makas diyagonali"}, {"asik", "Aşık"}, {"kren", "Kren kirişi"},
        {"bag", "Bağ"}, {"temel", "Temel"}, {"mesnet", "Mesnet"}, {"dugum", "Düğüm"}, {"diger", "Diğer"},
        {"kose", "Köşe"}, {"kenar", "Kenar"}, {"ic", "İç"}, {"dis", "Dış"}, {"konsol", "Konsol"}, {"dis-cephe", "Dış cephe"},
        {"kolon-ustu", "Kolon üstü"}, {"ara", "Ara"}};
    for (const auto& [a, b] : adlar)
        if (k == a) return Tr(b);
    return k;
}

// Panel başlığı (§8): yükseklik panelBaslik (40 / 36), yüzey zemin, başlık 13/600, sağda simge düğmeleri (16 px).
// Döndürür: tıklanan simgenin sırası (yoksa -1).
int PanelBasligi(const Ciz& c, float x0, float y0, float w, const char* baslik, std::initializer_list<const char*> ikonlar) {
    const auto& R = c.R();
    const float h = tema::Etkin().o.panelBaslik;
    c.Yazi(x0 + 12, Taban(y0, h, 13), baslik, 13, tema::Agirlik::Kalin, R.metin, w - 24 - 26 * static_cast<float>(ikonlar.size()));
    int tik = -1, i = 0;
    float x = x0 + w - 12 - 22;
    for (auto it = std::rbegin(ikonlar); it != std::rend(ikonlar); ++it, ++i) {
        ImGui::PushID(*it);
        const bool t = Tiklama(c, "##panel_simge", x, y0 + (h - 22) / 2, 22, 22);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        if (ust) c.Yuv(x, y0 + (h - 22) / 2, 22, 22, tema::belirtec::R.orta, R.hover);
        c.Simge(*it, x + 11, y0 + h / 2, std::string_view(*it) == "kapat" ? 12.0f : 14.0f, R.ikonKucuk, 1.4f);
        if (t) tik = static_cast<int>(ikonlar.size()) - 1 - i;
        x -= 26;
    }
    return tik;
}

}  // namespace

// ---- sol ray ------------------------------------------------------------------------------------------------------------
void AnaPencere::RayCiz(Ciz& c) {
    // §8 sol ray: ÇİZ (araçlar; etkin araç vurgu tonu + sol 3 px vurgu çizgi) · SEÇ (seçim anahtarları; açık = beyaz kutu
    // + 1 px çizgi + vurgu nokta, kapalı = metin4) · doğrudan değiştirme · yalnız seçili.
    const auto& R = c.R();
    const tema::Olculer& o = tema::Etkin().o;
    const float y0 = L_.ust, y1 = L_.H - L_.durum, w = L_.ray, bd = o.rayDugme, bx = (w - bd) / 2;
    c.Dikd(0, y0, w, y1 - y0, R.zemin);
    c.Dusey(w - 1, y0, y1, R.cizgi);
    float y = y0 + 8;
    c.YaziOrta(w / 2, y + 9, Tr("ÇİZ"), 9, tema::Agirlik::Kalin, R.metin3);
    y += 16;
    struct Palet {
        const char* ikon;
        const char* komut;
    };
    static const Palet palet[] = {{"sec", "secim.sec"},      {"kolon", "model.kolon"},     {"kiris", "model.kiris"},
                                  {"capraz", "model.capraz"}, {"doseme", "model.doseme"},   {"duvar", "model.duvar"},
                                  {"temel", "model.temel"},   {"aks", "model.hizli_aks"},   {"yuk", "yukler.ata"},
                                  {"mesnet", "yukler.mesnet"}};
    const float adim = L_.dar ? bd - 2 : bd;
    for (const Palet& p : palet) {
        const KomutTanimi* t = h_.komutlar ? h_.komutlar->Bul(p.komut) : nullptr;
        if (!t) continue;
        const KomutDurumu d = h_.komutlar->Durum(t->id, h_);
        const bool basili = vurguluKomut_ == t->id && simdi < vurguBitis_;
        ImGui::PushID(p.komut);
        const bool tik = Tiklama(c, "##ray", bx, y, bd, bd);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        if (basili) {
            c.Yuv(bx, y, bd, bd, tema::belirtec::R.orta, R.vurguTon);
            c.Yuv(0, y + 4, 3, bd - 8, 1.5f, R.vurgu);
        } else if (ust) {
            c.Yuv(bx, y, bd, bd, tema::belirtec::R.orta, R.hover);
        }
        c.Simge(p.ikon, w / 2, y + bd / 2, 18, !d.kullanilabilir ? R.ikonKapali : (basili ? R.vurgu : R.ikonBuyuk), 1.5f);
        OgeIpucu(c, d.kullanilabilir ? std::string(Tr(t->etiket.c_str())) : d.neden, t->kisayol);
        if (tik && d.kullanilabilir) KomutCalistir(t->id, KomutKaynagi::Serit);
        y += adim;
    }
    y += 6;
    c.Yatay(8, w - 8, y, R.cizgi);
    y += 8;
    c.YaziOrta(w / 2, y + 9, Tr("SEÇ"), 9, tema::Agirlik::Kalin, R.metin3);
    y += 16;
    struct Anahtar {
        const char* ikon;
        const char* ad;
        const char* ipucu;
    };
    static const Anahtar anahtarlar[] = {{"sec_pencere", "*", "Tümü (Ctrl + tık: yalnız bu tür)"},
                                         {"dugum", "dugum", "Düğümler"},   {"kolon", "kolon", "Kolonlar"},
                                         {"kiris", "kiris", "Kirişler"},   {"doseme", "doseme", "Döşemeler"},
                                         {"duvar", "duvar", "Duvarlar"},   {"aks", "aks", "Akslar"},
                                         {"yuk", "yuk", "Yükler"},         {"mesnet", "mesnet", "Mesnetler"},
                                         {"temel", "temel", "Temeller"}};
    const float kb = L_.dar ? 24.0f : bd - 2, kadim = L_.dar ? 24.0f : bd;
    for (const Anahtar& a : anahtarlar) {
        if (y + kb > y1 - 72) break;
        const bool tumu = a.ad[0] == '*';
        bool acik = true;
        if (tumu) {
            for (const auto& [k, v] : secAnahtar_) acik = acik && v;
        } else {
            acik = secAnahtar_[a.ad];
        }
        const float kx = (w - kb) / 2;
        ImGui::PushID(a.ad);
        const bool tik = Tiklama(c, "##sec", kx, y, kb, kb);
        ImGui::PopID();
        if (acik) {
            c.Yuv(kx, y, kb, kb, tema::belirtec::R.orta, R.yuzey, R.cizgi);
            c.Simge(a.ikon, w / 2, y + kb / 2, 16, R.ikonBuyuk, 1.5f);
            c.Daire(kx + kb - 4, y + 4, 2.5f, R.vurgu);
        } else {
            c.Simge(a.ikon, w / 2, y + kb / 2, 16, R.ikonKapali, 1.5f);
        }
        OgeIpucu(c, Tr(a.ipucu));
        if (tik) {
            if (tumu) {
                for (auto& [k, v] : secAnahtar_) v = !acik;
                if (acik) secAnahtar_["*"] = false;
            } else if (ImGui::GetIO().KeyCtrl) {
                for (auto& [k, v] : secAnahtar_) v = k == a.ad;
            } else {
                secAnahtar_[a.ad] = !acik;
            }
            secAnahtar_.erase("*");
        }
        y += kadim;
    }
    y += 6;
    c.Yatay(8, w - 8, y, R.cizgi);
    y += 8;
    if (Tiklama(c, "##dm", bx, y, bd, bd - 4)) dogrudanDegistirme = !dogrudanDegistirme;
    OgeIpucu(c, Tr("Doğrudan değiştirme tutamaçları (D)"));
    if (dogrudanDegistirme) c.Yuv(bx, y, bd, bd - 4, tema::belirtec::R.orta, R.secimTon, R.secimTon2);
    c.Simge("dm", w / 2, y + (bd - 4) / 2, 18, dogrudanDegistirme ? R.secim : R.ikonKapali, 1.6f);
    y += bd;
    if (Tiklama(c, "##yalniz", bx, y, bd, bd - 4)) yalnizSecili = !yalnizSecili;
    OgeIpucu(c, Tr("Yalnız seçiliyi göster"), "Ctrl+5");
    if (yalnizSecili) c.Yuv(bx, y, bd, bd - 4, tema::belirtec::R.orta, R.vurguTon, R.vurguTon2);
    c.Simge(yalnizSecili ? "goz_kapali" : "goz", w / 2, y + (bd - 4) / 2, 16, yalnizSecili ? R.vurgu : R.ikonKucuk, 1.4f);
}

// ---- model ağacı -------------------------------------------------------------------------------------------------------
void AnaPencere::AgacPaneliCiz(Ciz& c, float x0, float y0, float w, float h) {
    // §8 model ağacı: başlık 40 → segment 28 → arama 28 → satırlar 24 (girinti kılavuzları, zebra yok) → alt bilgi 32.
    const auto& R = c.R();
    const tema::Olculer& o = tema::Etkin().o;
    c.Dikd(x0, y0, w, h, R.yuzey);
    c.Dusey(x0 + w - 1, y0, y0 + h, R.cizgi);
    const int bt = PanelBasligi(c, x0, y0, w - 1, Tr("Model ağacı"), {"pin", "kapat"});
    const bool solda = x0 < L_.vpX0;
    if (solda && bt >= 0) {  // iğneyi kaldır / kapat: ağaç pencere şeridine döner (sağ panelde açılır)
        agacSolda_ = false;
        yanPencere = YanPencere::ModelAgaci;
    } else if (!solda && bt >= 0) {  // sağda: iğne sola yapıştırır, kapat Özellikler'e döner
        if (bt == 0 && !L_.tekPanel) agacSolda_ = true;
        yanPencere = YanPencere::Ozellikler;
    }
    // segmentli denetim (Model / Göster / Tablolar / Raporlar); F1'de yalnız Model içeriği vardır
    const float sy = y0 + o.panelBaslik;
    static int agacSekmesi = 0;
    const std::vector<std::string> segment = {Tr("Model"), Tr("Göster"), Tr("Tablolar"), Tr("Raporlar")};
    const int st = Segmentli(c, "##agac_segment", x0 + 12, sy, o.segment, segment, agacSekmesi, false, L_.dar ? 10.0f : 11.0f,
                             w - 25);
    if (st >= 0) agacSekmesi = st;
    // arama: dolgulu giriş + sol simge + sağda Ctrl+F rozeti
    const float ay = sy + o.segment + 8, ah = o.arama;
    static bool aramaOdak = false;  // önceki karede giriş etkin miydi (odak halkası)
    c.Giris(x0 + 12, ay, w - 25, ah, "", 12, aramaOdak);
    c.Simge("ara", x0 + 26, ay + ah / 2, 13, R.metin3, 1.4f);
    if (!L_.dar) c.YaziSag(x0 + w - 22, Taban(ay, ah, 10), "Ctrl+F", 10, tema::Agirlik::Orta, R.metin3);
    ImGui::SetCursorScreenPos(c.P(x0 + 36, ay + (ah - 18) / 2));
    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(c.S(2), c.S(2)));
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 0);
    ImGui::PushStyleColor(ImGuiCol_FrameBg, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleColor(ImGuiCol_FrameBgHovered, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleColor(ImGuiCol_FrameBgActive, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleColor(ImGuiCol_TextDisabled, ImGui::ColorConvertU32ToFloat4(R.metin3));
    ImGui::PushFont(c.F(tema::Agirlik::Normal), 12);
    ImGui::SetNextItemWidth(c.S(w - 25 - 24 - (L_.dar ? 8 : 52)));
    ImGui::InputTextWithHint("##agac_ara", Tr("Ağaçta ara (ad, kesit, etiket)"), agacArama_, sizeof(agacArama_));
    aramaOdak = ImGui::IsItemActive();
    ImGui::PopFont();
    ImGui::PopStyleColor(4);
    ImGui::PopStyleVar(2);
    const std::string arama = TurkceKatla(agacArama_);
    // satırlar
    float y = ay + ah + 8;
    const float rh = o.satir, altSinir = y0 + h - 32, ind = o.girintiDuzey;
    const bool bos = SahneBos();
    if (bos) {
        c.Yazi(x0 + 16, Taban(y, rh, 12), Tr("Model boş"), 12, tema::Agirlik::Kalin, R.metin);
        c.Yazi(x0 + 16, Taban(y + rh, rh, 11), Tr("Başlangıç panelinden şablon seçin"), 11, tema::Agirlik::Normal, R.metin3);
        c.Yazi(x0 + 16, Taban(y + 2 * rh, rh, 11), Tr("ya da Hızlı aks ile başlayın."), 11, tema::Agirlik::Normal, R.metin3);
    }
    const std::vector<ElemanKimligi>* secili = h_.secim ? &h_.secim->Liste() : nullptr;
    int sayac = 0;
    const float r6 = tema::belirtec::R.orta;
    // Girinti kılavuzları: derinlik d satırında 1..d-1 düzeylerinin sevron hizasında 1 px çizgi.
    auto kilavuz = [&](int derin, float yy) {
        for (int k = 1; k < derin; ++k) c.Dusey(x0 + 12 + static_cast<float>(k) * ind + 4, yy, yy + rh, R.cizgi2);
    };
    // Satır zemini: içe yerleşik (6 px), 6 px yuvarlak; seçili: seçim tonu + solda 3 px seçim çizgisi.
    auto zemin = [&](bool sec, bool ust, float yy) {
        if (sec) {
            c.Yuv(x0 + 6, yy, w - 13, rh, r6, R.secimTon);
            c.Yuv(x0 + 1, yy + 2, 3, rh - 4, 1.5f, R.secim);
        } else if (ust) {
            c.Yuv(x0 + 6, yy, w - 13, rh, r6, R.hover);
        }
    };
    // Bilgi satırı (aks sistemi, kesitler, malzemeler, gruplar): sahneden türetilir (Faz 3'te tam ağaç).
    auto bilgiSatiri = [&](int derin, const char* ikon, const char* ad, const std::string& sag, bool sevron) {
        if (y + rh > altSinir) return;
        const float ix = x0 + 12 + static_cast<float>(derin) * ind;
        kilavuz(derin, y);
        if (sevron) c.Sevron(ix + 4, y + rh / 2, 1, 10, R.metin2);
        c.Simge(ikon, ix + 18, y + rh / 2, 14, R.ikonKucuk, 1.4f);
        c.Yazi(ix + 28, Taban(y, rh, 12), Tr(ad), 12, tema::Agirlik::Normal, R.metin);
        c.YaziSag(x0 + w - 16, Taban(y, rh, 12), sag, 12, tema::Agirlik::Normal, R.metin3);
        y += rh;
    };
    std::string aksOzeti;
    if (!bos) {
        std::string xa, xb, ya, yb;
        for (const SahneAksi& ak : sahne_->akslar) {
            if (ak.eksen == 0) {
                if (xa.empty()) xa = ak.ad;
                xb = ak.ad;
            } else if (ak.eksen == 1) {
                if (ya.empty()) ya = ak.ad;
                yb = ak.ad;
            }
        }
        aksOzeti = xa.empty() ? std::string("—") : xa + "–" + xb + " × " + ya + "–" + yb;
    }
    // Özyinelemeli satır çizimi.
    std::function<void(const GezginDugumu&, int)> satir = [&](const GezginDugumu& d, int derin) {
        if (y + rh > altSinir) return;
        const bool cocuklu = !d.cocuklar.empty() || (derin >= 3 && !d.elemanlar.empty() && d.elemanlar.size() <= 400);
        const bool acik = acik_.count(d.anahtar) != 0 || !arama.empty();
        if (!arama.empty() && derin > 0 && TurkceKatla(d.baslik).find(arama) == std::string::npos && d.cocuklar.empty()) return;
        // seçili: düğümün bütün elemanları seçimde
        bool hepsiSecili = secili && !secili->empty() && !d.elemanlar.empty() && d.elemanlar.size() <= secili->size();
        size_t seciliSayi = 0;
        if (secili && !secili->empty())
            for (const ElemanKimligi& e : d.elemanlar) seciliSayi += std::binary_search(secili->begin(), secili->end(), e) ? 1 : 0;
        hepsiSecili = hepsiSecili && seciliSayi == d.elemanlar.size() && derin > 1;
        const bool etkin = etkinKat >= 0 && d.anahtar == "kat:" + std::to_string(sahne_->seviyeler[static_cast<size_t>(etkinKat)].kat);
        ImGui::PushID(sayac++);
        const bool tik = Tiklama(c, "##satir", x0, y, w - 1, rh);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        zemin(hepsiSecili, ust, y);
        kilavuz(derin, y);
        const float ix = x0 + 12 + static_cast<float>(derin) * ind;
        if (cocuklu) c.Sevron(ix + 4, y + rh / 2, acik ? 0 : 1, 10, R.metin2);
        c.Simge(DugumSimgesi(d.anahtar), ix + 18, y + rh / 2, 14, hepsiSecili ? R.secim : (etkin ? R.vurgu : R.ikonKucuk), 1.4f);
        const tema::Agirlik ag = derin == 0 || etkin || hepsiSecili ? tema::Agirlik::Kalin : tema::Agirlik::Normal;
        std::string sag = d.bilgi.empty() ? std::to_string(d.sayi) : d.bilgi;
        if (d.anahtar == "katlar") sag = std::to_string(d.cocuklar.size());
        if (d.anahtar == "proje") sag.clear();
        const float sagW = c.Gen(sag, 12, tema::Agirlik::Normal);
        std::string rozet;
        if (seciliSayi > 0 && derin > 1) rozet = L_.dar ? std::to_string(seciliSayi) : std::to_string(seciliSayi) + " " + Tr("seçili");
        const float rozetW = rozet.empty() ? 0 : c.Gen(rozet, 9, tema::Agirlik::Kalin) + 12;
        const float etkinW = etkin ? c.Gen(Tr("etkin"), 9, tema::Agirlik::Kalin) + 12 + 26 : 0;
        const float maxw = w - (ix + 28 - x0) - 16 - (sagW + 10) - (rozet.empty() ? 0 : rozetW + 6) - etkinW;
        std::string baslik = d.baslik;
        if (d.anahtar == "proje") baslik = d.baslik == "Proje" ? std::string(Tr("Proje")) : d.baslik;
        else if (baslik.rfind("Kat ", 0) == 0) baslik = Trf("Kat %s", baslik.c_str() + 4);  // çekirdek ağacı "Kat 2"
        else baslik = Tr(baslik.c_str());
        c.Yazi(ix + 28, Taban(y, rh, 12), baslik, 12, ag, R.metin, maxw);
        if (!rozet.empty()) c.Rozet(x0 + w - 16 - sagW - 8 - rozetW, y + (rh - 16) / 2, rozet, 9, R.secim, R.beyaz, 16);
        c.YaziSag(x0 + w - 16, Taban(y, rh, 12), sag, 12, tema::Agirlik::Normal, R.metin3);
        if (etkin) {  // "etkin" çipi + göz
            const float ew = c.Gen(Tr("etkin"), 9, tema::Agirlik::Kalin) + 12;
            const float ex = x0 + w - 16 - sagW - 10 - ew;
            c.Yuv(ex, y + (rh - 16) / 2, ew, 16, 4, R.vurguTon, R.vurguTon2);
            c.YaziOrta(ex + ew / 2, Taban(y, rh, 9), Tr("etkin"), 9, tema::Agirlik::Kalin, R.vurguMetin);
            c.Simge("goz", ex - 13, y + rh / 2, 13, R.ikonKucuk, 1.3f);
        }
        if (tik) {
            const ImGuiIO& io = ImGui::GetIO();
            const float mx = io.MousePos.x / olcek_;
            if (cocuklu && mx < ix + 12) {
                AgacAc(d.anahtar, !acik);
            } else if (h_.secim && !d.elemanlar.empty()) {
                h_.secim->Uygula(d.elemanlar, io.KeyCtrl ? SecimKipi::Ekle : (io.KeyShift ? SecimKipi::Cikar : SecimKipi::Yeni));
            }
            if (d.anahtar.rfind("kat:", 0) == 0 && d.anahtar.find('/') == std::string::npos) {
                const int no = std::atoi(d.anahtar.c_str() + 4);
                for (size_t i = 0; i < sahne_->seviyeler.size(); ++i)
                    if (sahne_->seviyeler[i].kat == no) etkinKat = static_cast<int>(i);
            }
        }
        if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left) && cocuklu) AgacAc(d.anahtar, !acik);
        y += rh;
        if (!acik) return;
        if (derin == 0) bilgiSatiri(1, "izgara", "Aks sistemi", aksOzeti, false);
        for (const GezginDugumu& k : d.cocuklar) satir(k, derin + 1);
        // yaprak düğümde eleman satırları (en çok 8, sonra "… n daha")
        if (d.cocuklar.empty() && derin >= 2) {
            size_t n = 0;
            for (const ElemanKimligi& e : d.elemanlar) {
                if (y + rh > altSinir) return;
                if (n == 8) {
                    kilavuz(derin + 1, y);
                    c.Yazi(ix + ind + 28, Taban(y, rh, 12), Trf("… %zu eleman daha", d.elemanlar.size() - 8), 12,
                           tema::Agirlik::Normal, R.metin3);
                    y += rh;
                    return;
                }
                const bool sc = secili && std::binary_search(secili->begin(), secili->end(), e);
                ImGui::PushID(sayac++);
                const bool et = Tiklama(c, "##eleman", x0, y, w - 1, rh);
                const bool eu = ImGui::IsItemHovered();
                ImGui::PopID();
                zemin(sc, eu, y);
                kilavuz(derin + 1, y);
                const float ex = ix + ind;
                c.Simge("cubuk", ex + 18, y + rh / 2, 12, sc ? R.secim : R.ikonKapali, 1.3f);
                c.Yazi(ex + 28, Taban(y, rh, 12), ElemanAdi(e), 12, sc ? tema::Agirlik::Kalin : tema::Agirlik::Normal, R.metin,
                       w - (ex + 28 - x0) - 90);
                if (const auto r = oz_->Satir(e))
                    if (const auto k = oz_->Metin(*r, oznitelik::KESIT))
                        c.YaziSag(x0 + w - 16, Taban(y, rh, 11), std::string(*k), 11, tema::Agirlik::Normal, R.metin3);
                if (et && h_.secim) {
                    const ImGuiIO& io = ImGui::GetIO();
                    h_.secim->Uygula(e, io.KeyCtrl ? SecimKipi::Tersle : SecimKipi::Yeni);
                }
                if (eu) uzerinde_ = e;
                y += rh;
                ++n;
            }
        }
    };
    if (!bos) {
        satir(agac_, 0);
        if (acik_.count(agac_.anahtar) || !arama.empty()) {
            bilgiSatiri(1, "kesit", "Kesitler", std::to_string(sahne_->kesitler.size()), true);
            bilgiSatiri(1, "malzeme", "Malzemeler", std::to_string(sahne_->malzemeler.size()), true);
            bilgiSatiri(1, "katman", "Gruplar", std::to_string(sahne_->gruplar.size()), true);
        }
    }
    // alt bilgi (32): özet + seçileni ağaçta göster
    const float oy = y0 + h - 32;
    c.Dikd(x0, oy, w - 1, 32, R.yuzey);
    c.Yatay(x0, x0 + w - 1, oy, R.cizgi2);
    size_t katSayisi = 0;
    for (const SahneSeviyesi& sv : sahne_->seviyeler) katSayisi += sv.kat > 0 ? 1 : 0;
    const std::string ozet = Trf("%zu eleman · %zu düğüm · %zu kat", sahne_->cubuklar.size() + sahne_->paneller.size(),
                                 sahne_->dugumler.size(), katSayisi);
    c.Yazi(x0 + 12, Taban(oy, 32, 11), ozet, 11, tema::Agirlik::Normal, R.metin3, w - 48);
    if (Tiklama(c, "##agacta_goster", x0 + w - 34, oy + 5, 22, 22)) AgaciSecimeAc();
    const bool gu = ImGui::IsItemHovered();
    if (gu) c.Yuv(x0 + w - 34, oy + 5, 22, 22, r6, R.hover);
    c.Simge("tam", x0 + w - 23, oy + 16, 14, R.ikonKucuk, 1.4f);
    OgeIpucu(c, Tr("Seçileni ağaçta göster"));
}

// ---- Özellikler (salt okunur; düzenleme Faz 3) -------------------------------------------------------------------------
void AnaPencere::OzelliklerPaneliCiz(Ciz& c, float x0, float y0, float w, float h) {
    // §8 Özellikler: başlık 40 → nesne başlığı 48 (32 px seçim tonu simge kutusu, ad + "n seçili" rozeti, alt satır) →
    // bölümler (28 px başlık, 24 px satır, dolgulu alanlar, kapalı bölümde özet) → alt çubuk 48 (Uygula · Al · Anında uygula).
    const auto& R = c.R();
    const tema::Olculer& to = tema::Etkin().o;
    c.Dikd(x0, y0, w, h, R.yuzey);
    c.Dusey(x0, y0, y0 + h, R.cizgi);
    if (PanelBasligi(c, x0 + 1, y0, w - 1, Tr("Özellikler"), {"ara", "pin", "kapat"}) == 2) yanPencere = YanPencere::Baslangic;
    // nesne başlığı
    const float oy = y0 + to.panelBaslik, nh = to.nesneBaslik;
    c.Yatay(x0 + 1, x0 + w, oy + nh - 1, R.cizgi2);
    const std::vector<ElemanKimligi> secim = h_.secim ? h_.secim->Liste() : std::vector<ElemanKimligi>{};
    struct Satir {
        std::string etiket, deger;
        int tur = 0;  // 0 metin, 1 açılır, 2 katalog, 3 çeşitli
    };
    struct Bolum {
        const char* ad;
        std::vector<Satir> satirlar;
        std::string ozet;
    };
    std::vector<Bolum> bolumler;
    if (secim.empty()) {
        c.Yuv(x0 + 12, oy + (nh - 32) / 2 - 2, 32, 32, tema::belirtec::R.orta, R.zemin, R.cizgi);
        c.Simge("proje", x0 + 28, oy + nh / 2 - 2, 16, R.ikonKucuk, 1.5f);
        const std::string ad = sahne_->baslik.empty() ? std::string(Tr("Proje")) : sahne_->baslik;
        c.Yazi(x0 + 54, oy + 20, ad, 13, tema::Agirlik::Kalin, R.metin, w - 66);
        c.Yazi(x0 + 54, oy + 36, Tr("Seçim yok · model özeti"), 11, tema::Agirlik::Normal, R.metin3, w - 66);
        size_t kat = 0;
        for (const SahneSeviyesi& s : sahne_->seviyeler) kat += s.kat > 0 ? 1 : 0;
        bolumler.push_back({"Model", {{Tr("Sistem"), Tr(sahne_->sistem == "betonarme" ? "Betonarme" : "Çelik")},
                                      {Tr("Kat"), std::to_string(kat)},
                                      {Tr("Düğüm"), std::to_string(sahne_->dugumler.size())},
                                      {Tr("Çubuk"), std::to_string(sahne_->cubuklar.size())},
                                      {Tr("Panel"), std::to_string(sahne_->paneller.size())},
                                      {Tr("Mesnet"), std::to_string(sahne_->mesnetler.size())},
                                      {Tr("Kesit"), std::to_string(sahne_->kesitler.size())}}, ""});
        bolumler.push_back({"Görünüm", {{Tr("Kip"), Tr(KesitGorunumu() ? "Ekstrüzyon" : "Çubuk")},
                                        {Tr("Etkin kat"), KatAdi(etkinKat)},
                                        {Tr("Kat kapsamı"), Tr(kapsam == KatKapsami::BuKat ? "Bu kat" : kapsam == KatKapsami::BenzerKatlar ? "Benzer katlar" : "Tüm katlar")}}, ""});
    } else {
        const std::string tur = AltTur(secim.front());
        const char* ikon = tur == "kolon" ? "kolon" : tur == "kiris" ? "kiris" : tur == "capraz" ? "capraz" : tur == "doseme" ? "doseme"
                           : tur == "dugum" ? "dugum" : tur == "mesnet" ? "mesnet" : "cubuk";
        c.Yuv(x0 + 12, oy + (nh - 32) / 2 - 2, 32, 32, tema::belirtec::R.orta, R.secimTon, R.secimTon2);
        c.Simge(ikon, x0 + 28, oy + nh / 2 - 2, 16, R.secim, 1.5f);
        bool tekTur = true;
        for (const ElemanKimligi& e : secim) tekTur = tekTur && AltTur(e) == tur;
        const std::string baslik = secim.size() == 1 ? KodAdi(tur) + " · " + ElemanAdi(secim.front())
                                                     : (tekTur ? KodAdi(tur) : std::string(Tr("Eleman")));
        const float bw = c.Yazi(x0 + 54, oy + 20, baslik, 13, tema::Agirlik::Kalin, R.metin, w - 140);
        if (secim.size() > 1) c.Rozet(x0 + 54 + bw + 8, oy + 8, Trf("%zu seçili", secim.size()), 9, R.secim, R.beyaz, 16);
        c.Yazi(x0 + 54, oy + 36, SecimAyrinti(), 11, tema::Agirlik::Normal, R.metin3, w - 66);
        for (int i = -1; i <= 1; ++i) c.Daire(x0 + w - 22 + 4.5f * static_cast<float>(i), oy + 15, 1.3f, R.ikonKucuk);
        // Ortak öznitelikler (S5 OrtakOzellikler; çoklu seçimde "(farklı)").
        std::map<std::string, std::string> o;
        for (const auto& [id, deger] : OrtakOzellikler(*oz_, secim)) o[id] = deger == "(çeşitli)" ? std::string(Tr("(farklı)")) : deger;
        auto al = [&](const char* id) { const auto i = o.find(id); return i == o.end() ? std::string("—") : i->second; };
        auto tur_ = [&](const std::string& d) { return d == std::string(Tr("(farklı)")) ? 3 : 0; };
        std::string katMetni = al(oznitelik::KAT);
        if (katMetni != "—" && katMetni.find(',') == std::string::npos && katMetni != Tr("(farklı)")) {
            const int no = std::atoi(katMetni.c_str());
            for (size_t i = 0; i < sahne_->seviyeler.size(); ++i)
                if (sahne_->seviyeler[i].kat == no) katMetni = KatAdi(static_cast<int>(i));
        }
        bolumler.push_back({"Genel", {{Tr("Ad"), al(oznitelik::AD), tur_(al(oznitelik::AD))},
                                      {Tr("Tür"), KodAdi(al(oznitelik::ALT_TUR)), 0},
                                      {Tr("Kat"), katMetni, 1},
                                      {Tr("Kullanım yeri"), KodAdi(al(oznitelik::KULLANIM_YERI)), 0},
                                      {Tr("Grup"), al(oznitelik::GRUP), 1}}, ""});
        if (secim.front().tur == ElemanTuru::Cubuk)
            bolumler.push_back({"Kesit", {{Tr("Kesit"), al(oznitelik::KESIT), 2},
                                          {Tr("Malzeme"), al(oznitelik::MALZEME), 2},
                                          {Tr("Dönme"), al(oznitelik::ACI), 0}}, ""});
        if (secim.front().tur == ElemanTuru::Panel)
            bolumler.push_back({"Kesit", {{Tr("Kalınlık"), al(oznitelik::KALINLIK), 0}, {Tr("Alan"), al(oznitelik::ALAN), 0}}, ""});
        bolumler.push_back({"Konum", {{Tr("Uzunluk"), al(oznitelik::UZUNLUK), tur_(al(oznitelik::UZUNLUK))},
                                      {Tr("Eğim"), al(oznitelik::EGIM), 0},
                                      {"X", al(oznitelik::X), tur_(al(oznitelik::X))},
                                      {"Y", al(oznitelik::Y), tur_(al(oznitelik::Y))},
                                      {"Z", al(oznitelik::Z), tur_(al(oznitelik::Z))}}, ""});
        auto serbest = [&](const std::string& v) {
            if (v == "—" || v.empty()) return std::string(Tr("Rijit"));
            if (v == Tr("(farklı)")) return v;
            if (v.find("My") != std::string::npos && v.find("Mz") != std::string::npos)
                return std::string(Tr("Mafsal")) + " (" + v + ")";
            return v;
        };
        if (secim.front().tur == ElemanTuru::Cubuk)
            bolumler.push_back({"Serbestlikler", {{Tr("Başlangıç ucu"), serbest(al(oznitelik::SERBEST_I)), 1},
                                                  {Tr("Bitiş ucu"), serbest(al(oznitelik::SERBEST_J)), 1}}, ""});
        bolumler.push_back({"Yükler", {}, Tr("Faz 3")});
        bolumler.push_back({"Analiz", {}, Tr("çözüm yok")});
        bolumler.push_back({"Tasarım", {}, Tr("çözüm yok")});
    }
    float y = oy + nh + 2;
    const float lw = to.etiketSutunu, vx = x0 + 16 + lw, vw = w - 16 - lw - 14, rh = to.ozellikSatiri, bh = to.bolum;
    const float fh = to.alan, altSinir = y0 + h - to.altCubuk;
    bool ilk = true;
    for (const Bolum& b : bolumler) {
        if (y + bh > altSinir) break;
        const bool acik = !kapaliBolumler_.count(b.ad) && !b.satirlar.empty();
        if (!ilk) c.Yatay(x0 + 12, x0 + w - 12, y, R.cizgi2);
        ilk = false;
        ImGui::PushID(b.ad);
        if (Tiklama(c, "##bolum", x0 + 1, y, w - 1, bh)) {
            if (kapaliBolumler_.count(b.ad))
                kapaliBolumler_.erase(b.ad);
            else
                kapaliBolumler_.insert(b.ad);
        }
        const bool bu = ImGui::IsItemHovered();
        ImGui::PopID();
        if (bu) c.Yuv(x0 + 6, y + 2, w - 12, bh - 4, tema::belirtec::R.orta, R.hover);
        c.Sevron(x0 + 18, y + bh / 2, acik ? 0 : 1, 10, R.metin2);
        c.Yazi(x0 + 30, Taban(y, bh, 12), Tr(b.ad), 12, tema::Agirlik::Kalin, R.metin);
        if (!b.ozet.empty() && !acik) c.YaziSag(x0 + w - 16, Taban(y, bh, 11), b.ozet, 11, tema::Agirlik::Normal, R.metin3);
        y += bh;
        if (!acik) continue;
        for (const Satir& sa : b.satirlar) {
            if (y + rh > altSinir) break;
            c.Yazi(x0 + 16, Taban(y, rh, 12), sa.etiket, 12, tema::Agirlik::Normal, R.metin2, lw - 6);
            const float fy = y + (rh - fh) / 2;
            if (sa.tur == 2) {  // katalog: dolgulu alan + ⋯ düğmesi
                c.Giris(vx, fy, vw - 26, fh, sa.deger, 12);
                c.Yuv(vx + vw - 20, fy, 20, fh, tema::belirtec::R.orta, R.yuzey, R.dugmeKenar);
                for (int i = -1; i <= 1; ++i) c.Daire(vx + vw - 10 + 3.5f * static_cast<float>(i), fy + fh / 2, 1.1f, R.metin2);
            } else if (sa.tur == 1) {
                c.Acilir(vx, fy, vw, fh, sa.deger, 12);
            } else if (sa.tur == 3) {
                c.Giris(vx, fy, vw, fh, sa.deger, 12, false, R.metin3);
            } else {
                c.Yazi(vx + 8, Taban(y, rh, 12), sa.deger, 12, tema::Agirlik::Normal, R.metin, vw - 8);
            }
            y += rh;
        }
        y += 4;
    }
    // alt çubuk: Uygula (birincil) · Al · Anında uygula (F1 salt okunur: soluk, ipucu "Faz 3")
    const float ah = to.altCubuk, fy = y0 + h - ah;
    c.Dikd(x0 + 1, fy, w - 1, ah, R.yuzey);
    c.Yatay(x0, x0 + w, fy, R.cizgi2);
    const float dy = fy + (ah - 28) / 2;
    Tiklama(c, "##uygula", x0 + 12, dy, 148, 28);
    OgeIpucu(c, Tr("Özellik düzenleme Faz 3'te gelir (F1'de salt okunur)."));
    c.Dugme(x0 + 12, dy, 84, 28, Tr("Uygula"), true, 12, true);
    c.Dugme(x0 + 104, dy, 52, 28, Tr("Al"), false, 12, true);
    const std::string an = Tr("Anında uygula");
    const float anw = c.Gen(an, 11, tema::Agirlik::Normal);
    c.Anahtar(x0 + w - 16 - anw - 36, fy + (ah - 16) / 2, true, 28, 16, true);
    c.Yazi(x0 + w - 16 - anw, Taban(fy, ah, 11), an, 11, tema::Agirlik::Normal, R.metin3);
}

// ---- Başlangıç (boş çalışma alanı; MIMARI §5.2, kabul C3) ---------------------------------------------------------------
void AnaPencere::BaslangicPaneliCiz(Ciz& c, float x0, float y0, float w, float h) {
    const auto& R = c.R();
    c.Dikd(x0, y0, w, h, R.yuzey);
    c.Dusey(x0, y0, y0 + h, R.cizgi);
    if (PanelBasligi(c, x0 + 1, y0, w - 1, Tr("Başlangıç"), {"kapat"}) == 0) yanPencere = YanPencere::Ozellikler;
    float y = y0 + tema::Etkin().o.panelBaslik + 2;
    const std::string ad = h_.belge ? h_.belge->Ad() : std::string(Tr("Adsız 1"));
    c.Yazi(x0 + 12, y + 14, ad, 13, tema::Agirlik::Kalin, R.metin);
    c.Yazi(x0 + 12, y + 30, Tr("Boş model · Z = 0 çalışma ızgarası"), 11, tema::Agirlik::Normal, R.metin3);
    y += 44;
    // Yeni: Boş model + Hızlı aks (iki kart)
    const float kw = (w - 24 - 8) / 2;
    struct Kutu {
        const char* ikon;
        const char* baslik;
        const char* alt;
        int eylem;
    };
    const Kutu kutular[2] = {{"yeni", "Boş model", "Adsız N", 0}, {"aks", "Hızlı aks…", "aks + kat sihirbazı", 1}};
    for (int i = 0; i < 2; ++i) {
        const float kx = x0 + 12 + static_cast<float>(i) * (kw + 8);
        ImGui::PushID(i);
        const bool tik = Tiklama(c, "##yeni", kx, y, kw, 64);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        c.Yuv(kx, y, kw, 64, tema::belirtec::R.orta, ust ? R.vurguTon : R.yuzey, ust ? R.vurguTon2 : R.cizgi);
        c.Simge(kutular[i].ikon, kx + 20, y + 22, 20, ust ? R.vurgu : R.ikonBuyuk, 1.5f);
        c.Yazi(kx + 12, y + 46, Tr(kutular[i].baslik), 12, tema::Agirlik::Kalin, R.metin, kw - 16);
        c.Yazi(kx + 12, y + 59, Tr(kutular[i].alt), 10, tema::Agirlik::Normal, R.metin3, kw - 16);
        if (tik) {
            if (kutular[i].eylem == 0)
                YeniProjeAkisi([this] { KomutCalistir("dosya.yeni", KomutKaynagi::Menu); });
            else
                YeniProjeAkisi([this] { hizliAksAcik_ = true; });
        }
    }
    y += 64 + 14;
    // Şablondan yeni (9 şablon)
    c.Yazi(x0 + 12, Taban(y, 20, 11), Tr("Şablondan yeni"), 11, tema::Agirlik::Kalin, R.metin2);
    y += 22;
    const float rh = L_.dar ? 30 : 34;
    for (const SablonSatiri& s : Sablonlar(h_.bilgi.veriDizini)) {
        if (y + rh > y0 + h - 150) break;
        ImGui::PushID(s.ad.c_str());
        const bool tik = Tiklama(c, "##sablon", x0 + 1, y, w - 2, rh);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        if (ust) c.Yuv(x0 + 6, y, w - 12, rh, tema::belirtec::R.orta, R.hover);
        const bool celik = s.sistem == "celik";
        c.Yuv(x0 + 12, y + (rh - 24) / 2, 24, 24, tema::belirtec::R.orta, R.zemin);
        c.Simge(celik ? "kolon" : "beton", x0 + 24, y + rh / 2, 14, R.ikonKucuk, 1.3f);
        c.Yazi(x0 + 44, y + rh / 2 - 1, Tr(s.baslik.c_str()), 12, tema::Agirlik::Orta, R.metin, w - 60);
        c.Yazi(x0 + 44, y + rh / 2 + 12, Trf("%d kat · %s aks", s.kat, s.aks.c_str()), 10, tema::Agirlik::Normal, R.metin3);
        OgeIpucu(c, s.ad);
        if (tik) {
            const std::string sablonAdi = s.ad;
            YeniProjeAkisi([this, sablonAdi] { KomutCalistir("dosya.yeni_sablon", KomutKaynagi::Menu, sablonAdi); });
        }
        y += rh;
    }
    // Aç, son dosyalar (dosya.ac <yol>), açılışta göster
    const std::vector<std::string> son = h_.ayarlar ? h_.ayarlar->dosya.sonDosyalar : std::vector<std::string>{};
    const size_t sonN = std::min<size_t>(son.size(), 3);
    const float fy = y0 + h - 92 - 22.0f * static_cast<float>(sonN) - (sonN ? 22 : 0);
    float sy = fy;
    c.Yatay(x0, x0 + w, sy, R.cizgi2);
    if (sonN) {
        c.Yazi(x0 + 12, Taban(sy + 4, 20, 11), Tr("Son dosyalar"), 11, tema::Agirlik::Kalin, R.metin2);
        sy += 24;
        for (size_t i = 0; i < sonN; ++i) {
            const std::string& yol = son[i];
            const size_t b = yol.find_last_of("/\\");
            const std::string dosyaAdi = b == std::string::npos ? yol : yol.substr(b + 1);
            ImGui::PushID(static_cast<int>(700 + i));
            const bool tik = Tiklama(c, "##son_dosya", x0 + 6, sy, w - 12, 22);
            const bool ust = ImGui::IsItemHovered();
            ImGui::PopID();
            if (ust) c.Yuv(x0 + 6, sy, w - 12, 22, tema::belirtec::R.orta, R.hover);
            c.Simge("ac", x0 + 20, sy + 11, 13, R.ikonKucuk, 1.3f);
            c.Yazi(x0 + 32, Taban(sy, 22, 12), dosyaAdi, 12, tema::Agirlik::Normal, R.metin, w - 48);
            OgeIpucu(c, yol);
            if (tik) KomutCalistir("dosya.ac", KomutKaynagi::Menu, yol);
            sy += 22;
        }
    }
    const float by = y0 + h - 92;
    c.Yatay(x0, x0 + w, by, R.cizgi2);
    if (Tiklama(c, "##ac", x0 + 12, by + 12, 96, 28)) KomutCalistir("dosya.ac", KomutKaynagi::Menu);
    c.Dugme(x0 + 12, by + 12, 96, 28, Tr("Aç…"), false, 12, false, ImGui::IsItemHovered());
    if (!sonN) c.Yazi(x0 + 120, Taban(by + 12, 28, 11), Tr("Son dosya yok"), 11, tema::Agirlik::Normal, R.metin3);
    const bool goster = !h_.ayarlar || h_.ayarlar->arayuz.baslangicPaneli;
    if (Tiklama(c, "##goster", x0 + 12, by + 50, w - 24, 22) && h_.ayarlar)
        h_.ayarlar->arayuz.baslangicPaneli = !h_.ayarlar->arayuz.baslangicPaneli;
    c.OnayKutusu(x0 + 12, by + 54, goster, 14);
    c.Yazi(x0 + 32, Taban(by + 50, 22, 11), Tr("Açılışta Başlangıç panelini göster"), 11, tema::Agirlik::Normal, R.metin2);
}

void AnaPencere::BosPanelCiz(Ciz& c, float x0, float y0, float w, float h, const char* baslik, const char* aciklama) {
    const auto& R = c.R();
    c.Dikd(x0, y0, w, h, R.yuzey);
    c.Dusey(x0, y0, y0 + h, R.cizgi);
    if (PanelBasligi(c, x0 + 1, y0, w - 1, Tr(baslik), {"kapat"}) == 0) yanPencere = YanPencere::Ozellikler;
    c.Yazi(x0 + 12, y0 + tema::Etkin().o.panelBaslik + 14, Tr(aciklama), 11, tema::Agirlik::Normal, R.metin3, w - 24);
    // Diğer paketlerin sağ panelleri (S21) burada değil, ImGui pencereleri olarak çizilir.
}

// ---- pencere şeridi (dikey sekmeler) -----------------------------------------------------------------------------------
void AnaPencere::PencereSeridiCiz(Ciz& c) {
    const auto& R = c.R();
    const float x0 = L_.serX, y0 = L_.ust, w = L_.serW, h = L_.alt - L_.ust;
    c.Dikd(x0, y0, w, h, R.zemin);
    c.Dusey(x0, y0, y0 + h, R.cizgi);
    struct Pen {
        YanPencere p;
        const char* ikon;
        const char* ad;
    };
    static const Pen pencereler[] = {{YanPencere::Baslangic, "tam", "Başlangıç"},
                                     {YanPencere::Ozellikler, "etiket", "Özellikler"},
                                     {YanPencere::Kataloglar, "kutuphane", "Kataloglar"},
                                     {YanPencere::ModelAgaci, "katman", "Model ağacı"},
                                     {YanPencere::Filtre, "suz", "Filtre & görünürlük"},
                                     {YanPencere::Sorgu, "sorgu", "Sorgu"}};
    float y = y0 + 8;
    const float r6 = tema::belirtec::R.orta;
    for (const Pen& p : pencereler) {
        const char* ad = Tr(p.ad);
        float th = c.Gen(ad, 11, tema::Agirlik::Kalin) + 36;
        const bool yalnizSimge = y + th > y0 + h - 30;  // sığmayan düğmeler yalnız simge (§9.5)
        if (yalnizSimge) th = 30;
        if (y + th > y0 + h - 30) break;
        ImGui::PushID(static_cast<int>(p.p));
        if (Tiklama(c, "##pencere_seridi", x0 + 1, y, w - 1, th)) yanPencere = p.p;
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        const bool etkin = yanPencere == p.p;
        if (etkin) {
            c.Yuv(x0 + 3, y, w - 6, th, r6, R.vurguTon);
            c.Yuv(x0 + w - 3, y + 4, 3, th - 8, 1.5f, R.vurgu);
        } else if (ust) {
            c.Yuv(x0 + 3, y, w - 6, th, r6, R.hover);
        }
        c.Simge(p.ikon, x0 + w / 2, y + 14, 16, etkin ? R.vurgu : R.ikonKucuk, 1.5f);
        if (!yalnizSimge)
            c.YaziDikey(x0 + w / 2 - 7, y + 28, ad, 11, etkin ? tema::Agirlik::Kalin : tema::Agirlik::Orta,
                        etkin ? R.vurguMetin : R.metin2);
        else
            OgeIpucu(c, ad);
        if (p.p == YanPencere::ModelAgaci && L_.agacW > 0) c.Simge("sol_yapistir", x0 + w / 2, y + th - 8, 9, R.metin3, 1.2f);
        y += th + 8;
    }
    c.Yatay(x0 + 6, x0 + w - 6, y, R.cizgi);
    c.Simge("sevron_cift_asagi", x0 + w / 2, y + 16, 12, R.metin3, 1.3f);
}

}  // namespace op4
