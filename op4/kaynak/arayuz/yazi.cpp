// op4 arayüzü — gömülü yazı tiplerinin açılması ve ImGui atlasına eklenmesi (bkz. yazi.h).
#include "arayuz/yazi.h"

#include <cstring>
#include <map>
#include <memory>
#include <string>

#include "imgui.h"
#ifdef IMGUI_ENABLE_FREETYPE
#include "misc/freetype/imgui_freetype.h"
#endif

namespace op4 {
namespace {

// ImGui Decode85 eşleniği.
unsigned Coz85Bayt(char c) { return c >= '\\' ? static_cast<unsigned>(c - 36) : static_cast<unsigned>(c - 35); }

std::vector<uint8_t> Coz85(const char* const* parcalar) {
    std::string tum;
    for (const char* const* p = parcalar; *p; ++p) tum += *p;
    std::vector<uint8_t> o;
    o.reserve(tum.size() / 5 * 4);
    for (size_t i = 0; i + 5 <= tum.size(); i += 5) {
        unsigned v = Coz85Bayt(tum[i]) +
                     85 * (Coz85Bayt(tum[i + 1]) + 85 * (Coz85Bayt(tum[i + 2]) + 85 * (Coz85Bayt(tum[i + 3]) + 85 * Coz85Bayt(tum[i + 4]))));
        for (int k = 0; k < 4; ++k) {
            o.push_back(static_cast<uint8_t>(v & 0xFF));
            v >>= 8;
        }
    }
    return o;
}

// stb_decompress (ImGui imgui_draw.cpp ile aynı biçim; sınır denetimli, durumsuz).
unsigned In(const uint8_t* i, int n) {
    unsigned v = 0;
    for (int k = 0; k < n; ++k) v = (v << 8) | i[k];
    return v;
}

bool StbAc(const std::vector<uint8_t>& girdi, std::vector<uint8_t>& o) {
    if (girdi.size() < 16 || In(girdi.data(), 4) != 0x57bC0000u || In(girdi.data() + 4, 4) != 0) return false;
    const unsigned uzunluk = In(girdi.data() + 8, 4);
    o.assign(uzunluk, 0);
    size_t d = 0;
    const uint8_t* i = girdi.data() + 16;
    const uint8_t* son = girdi.data() + girdi.size();
    auto eslesme = [&](size_t uzak, size_t L) {
        if (uzak == 0 || uzak > d || d + L > o.size()) return false;
        for (size_t k = 0; k < L; ++k, ++d) o[d] = o[d - uzak];
        return true;
    };
    auto yazi = [&](const uint8_t* p, size_t L) {
        if (p + L > son || d + L > o.size()) return false;
        std::memcpy(o.data() + d, p, L);
        d += L;
        return true;
    };
    while (i < son) {
        const uint8_t c = *i;
        if (c >= 0x80) {
            if (i + 2 > son || !eslesme(i[1] + 1u, c - 0x80u + 1u)) return false;
            i += 2;
        } else if (c >= 0x40) {
            if (i + 3 > son || !eslesme(In(i, 2) - 0x4000u + 1u, i[2] + 1u)) return false;
            i += 3;
        } else if (c >= 0x20) {
            const size_t L = c - 0x20u + 1u;
            if (!yazi(i + 1, L)) return false;
            i += 1 + L;
        } else if (c >= 0x18) {
            if (i + 4 > son || !eslesme(In(i, 3) - 0x180000u + 1u, i[3] + 1u)) return false;
            i += 4;
        } else if (c >= 0x10) {
            if (i + 5 > son || !eslesme(In(i, 3) - 0x100000u + 1u, In(i + 3, 2) + 1u)) return false;
            i += 5;
        } else if (c >= 0x08) {
            const size_t L = In(i, 2) - 0x0800u + 1u;
            if (!yazi(i + 2, L)) return false;
            i += 2 + L;
        } else if (c == 0x07) {
            const size_t L = In(i + 1, 2) + 1u;
            if (!yazi(i + 3, L)) return false;
            i += 3 + L;
        } else if (c == 0x06) {
            if (i + 5 > son || !eslesme(In(i + 1, 3) + 1u, i[4] + 1u)) return false;
            i += 5;
        } else if (c == 0x04) {
            if (i + 6 > son || !eslesme(In(i + 1, 3) + 1u, In(i + 4, 2) + 1u)) return false;
            i += 6;
        } else if (c == 0x05 && i + 6 <= son && i[1] == 0xFA) {
            if (d != o.size()) return false;
            unsigned s1 = 1, s2 = 0;
            for (const uint8_t b : o) {
                s1 = (s1 + b) % 65521u;
                s2 = (s2 + s1) % 65521u;
            }
            return ((s2 << 16) | s1) == In(i + 2, 4);
        } else {
            return false;
        }
    }
    return false;
}

}  // namespace

const std::vector<uint8_t>* YaziVerisi(std::string_view ad) {
    static std::map<std::string, std::unique_ptr<std::vector<uint8_t>>, std::less<>> onbellek;
    if (const auto i = onbellek.find(ad); i != onbellek.end()) return i->second.get();
    size_t n = 0;
    const GomuluYazi* y = GomuluYazilar(n);
    for (size_t k = 0; k < n; ++k) {
        if (ad != y[k].ad) continue;
        auto v = std::make_unique<std::vector<uint8_t>>();
        if (!StbAc(Coz85(y[k].parcalar), *v) || v->size() != y[k].boyut) v.reset();
        auto* p = v.get();
        onbellek.emplace(std::string(ad), std::move(v));
        return p;
    }
    return nullptr;
}

bool YazilariYukle(ImFontAtlas* atlas, Yazilar& y) {
    atlas->Clear();
    y = Yazilar{};
    static const char* const kInter[5] = {"Arayuz400", "Arayuz450", "Arayuz500", "Arayuz600", "Arayuz700"};
    // İşleme (tanı notu, MIMARI §25.1): piksele oturan glif ilerlemesi ve konumu, aşırı örnekleme yok, RasterizerMultiply 1.
    // imgui_freetype etkinse hafif oto-ipucu (LightHinting | ForceAutoHint); değilse stb_truetype.
    auto ekle = [&](const char* ad, bool birlestir) -> ImFont* {
        const std::vector<uint8_t>* v = YaziVerisi(ad);
        if (!v) return nullptr;
        ImFontConfig c;
        c.FontDataOwnedByAtlas = false;  // veri önbellekte, süreç boyunca yaşar
        c.MergeMode = birlestir;
        c.OversampleH = 1;
        c.OversampleV = 1;
        c.PixelSnapH = true;
        // PixelSnapV: 1.92'de dikey oturtma varsayılandır (alan kaldırıldı).
        c.RasterizerMultiply = 1.0f;
#ifdef IMGUI_ENABLE_FREETYPE
        c.FontLoaderFlags = ImGuiFreeTypeLoaderFlags_LightHinting | ImGuiFreeTypeLoaderFlags_ForceAutoHint;
#endif
        std::snprintf(c.Name, sizeof(c.Name), "%s", ad);
        return atlas->AddFontFromMemoryTTF(const_cast<uint8_t*>(v->data()), static_cast<int>(v->size()), 12.0f, &c);
    };
    // Her arayüz ağırlığına sembol yedeği (≈ ≤ ≥ ← → …) birleştirilir (MergeMode; ailede olan glifler önceliklidir).
    auto ekleArayuz = [&](const char* ad) -> ImFont* {
        ImFont* f = ekle(ad, false);
        if (f) ekle("Simgeler", true);
        return f;
    };
    // İlk eklenen varsayılandır: gövde metni (arayüz ailesi 450).
    y.inter[1] = ekleArayuz(kInter[1]);
    for (int i = 0; i < 5; ++i)
        if (i != 1) y.inter[i] = ekleArayuz(kInter[i]);
    y.cormorant = ekle("Cormorant600", false);
    bool tamam = true;
    for (ImFont*& f : y.inter)
        if (!f) {
            tamam = false;
            f = y.inter[1];
        }
    if (!y.inter[1]) {
        ImFont* yedek = atlas->AddFontDefault();
        for (ImFont*& f : y.inter) f = yedek;
        tamam = false;
    }
    if (!y.cormorant) y.cormorant = y.inter[3];
    return tamam;
}

}  // namespace op4
