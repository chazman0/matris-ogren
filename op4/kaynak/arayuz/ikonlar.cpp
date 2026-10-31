// op4 arayüzü — çizgi ikonları: op4/tasarim/taslaklar/atolye/tuval.py simge_ciz() yol tanımlarının birebir ImDrawList
// karşılığı (24 birimlik ızgara; L = çoklu çizgi / dolu çokgen, R = dikdörtgen, E = elips, nokta). Taslakta olmayan birkaç
// op4 eki aynı dille çizilmiştir (sonda). Bkz. ikonlar.h.
#include "arayuz/ikonlar.h"

#include <cmath>
#include <initializer_list>
#include <vector>

#include "imgui.h"

namespace op4 {
namespace {

constexpr float PI_F = 3.14159265358979f;

struct Kalem {
    ImDrawList* dl;
    float x0, y0, u, k;  // u: piksel / birim; k: kalem kalınlığı (px)
    ImU32 c;

    ImVec2 P(float x, float y) const { return ImVec2(x0 + x * u, y0 + y * u); }
    // L: açık / kapalı çoklu çizgi ya da (dolu) çokgen. w: kalınlık çarpanı (taslaktaki w=k*…).
    void L(std::initializer_list<ImVec2> v, float w = 1.0f, bool dolu = false, bool kapali = false) const {
        L(std::vector<ImVec2>(v), w, dolu, kapali);
    }
    void L(const std::vector<ImVec2>& v, float w = 1.0f, bool dolu = false, bool kapali = false) const {
        std::vector<ImVec2> p;
        p.reserve(v.size());
        for (const ImVec2& q : v) p.push_back(P(q.x, q.y));
        if (p.size() < 2) return;
        if (dolu) {
            dl->AddConcavePolyFilled(p.data(), static_cast<int>(p.size()), c);
            return;
        }
        dl->AddPolyline(p.data(), static_cast<int>(p.size()), c, k * w, kapali ? ImDrawFlags_Closed : ImDrawFlags_None);
    }
    // R: PIL dikdörtgeni (kenar içe çizilir).
    void R(float ax, float ay, float bx, float by, float w = 1.0f, bool dolu = false) const {
        if (dolu) {
            dl->AddRectFilled(P(ax, ay), P(bx, by), c);
            return;
        }
        const float i = k * w * 0.5f;
        dl->AddRect(ImVec2(x0 + ax * u + i, y0 + ay * u + i), ImVec2(x0 + bx * u - i, y0 + by * u - i), c, 0.0f, k * w);
    }
    void E(float ax, float ay, float bx, float by, float w = 1.0f, bool dolu = false) const {
        const ImVec2 m = P((ax + bx) * 0.5f, (ay + by) * 0.5f);
        const float rx = (bx - ax) * 0.5f * u, ry = (by - ay) * 0.5f * u;
        if (dolu)
            dl->AddEllipseFilled(m, ImVec2(rx, ry), c, 0.0f, 0);
        else
            dl->AddEllipse(m, ImVec2(rx - k * w * 0.5f, ry - k * w * 0.5f), c, 0.0f, 0, k * w);
    }
    void nokta(float x, float y, float r = 1.6f) const { dl->AddCircleFilled(P(x, y), r * u, c, 0); }
    // PIL arc: bbox + derece (saat yönü; bitiş < başlangıç ise +360).
    void yay(float ax, float ay, float bx, float by, float a0, float a1, float w = 1.0f) const {
        if (a1 < a0) a1 += 360.0f;
        const ImVec2 m = P((ax + bx) * 0.5f, (ay + by) * 0.5f);
        const float rx = (bx - ax) * 0.5f * u - k * w * 0.5f, ry = (by - ay) * 0.5f * u - k * w * 0.5f;
        const int n = std::max(6, static_cast<int>((a1 - a0) / 8.0f));
        for (int i = 0; i <= n; ++i) {
            const float a = (a0 + (a1 - a0) * static_cast<float>(i) / static_cast<float>(n)) * PI_F / 180.0f;
            dl->PathLineTo(ImVec2(m.x + rx * std::cos(a), m.y + ry * std::sin(a)));
        }
        dl->PathStroke(c, k * w);
    }
    void IDik(float cx, float a, float b, float g = 5) const {
        L({{cx - g, a}, {cx + g, a}});
        L({{cx - g, b}, {cx + g, b}});
        L({{cx, a}, {cx, b}}, 1.6f);
    }
};

using IkonIslevi = void (*)(const Kalem&);
struct IkonKaydi {
    const char* ad;
    IkonIslevi f;
};

#define IK(ad) {ad, [](const Kalem& c)
#define SON }

const IkonKaydi kIkonlar[] = {
    IK("kolon") { c.IDik(12, 4, 20); c.L({{9, 4}, {9, 6.5f}}); c.L({{15, 4}, {15, 6.5f}}); c.L({{9, 20}, {9, 17.5f}}); c.L({{15, 20}, {15, 17.5f}}); } SON,
    IK("kiris") { c.L({{3, 8}, {21, 8}}); c.L({{3, 16}, {21, 16}}); c.L({{3, 12}, {21, 12}}, 1.6f); c.L({{3, 8}, {3, 16}}); c.L({{21, 8}, {21, 16}}); } SON,
    IK("kiris_ana") { c.L({{3, 7}, {21, 7}}, 1.4f); c.L({{3, 17}, {21, 17}}, 1.4f); c.L({{3, 12}, {21, 12}}, 1.6f); } SON,
    IK("kiris_tali") { c.L({{3, 9}, {21, 9}}); c.L({{3, 15}, {21, 15}}); c.L({{3, 12}, {21, 12}}); } SON,
    IK("asik") { c.L({{6, 6}, {18, 6}}); c.L({{18, 6}, {6, 18}}); c.L({{6, 18}, {18, 18}}); } SON,
    IK("capraz") { c.R(4, 4, 20, 20); c.L({{4, 4}, {20, 20}}); c.L({{20, 4}, {4, 20}}); } SON,
    IK("capraz_v") { c.R(4, 4, 20, 20); c.L({{4, 4}, {12, 20}, {20, 4}}); } SON,
    IK("capraz_tek") { c.R(4, 4, 20, 20); c.L({{4, 20}, {20, 4}}); } SON,
    IK("doseme") { c.L({{3, 14}, {9, 6}, {21, 6}, {15, 14}}, 1, false, true); c.L({{3, 14}, {3, 17}, {15, 17}, {15, 14}}); c.L({{15, 17}, {21, 9}, {21, 6}}); } SON,
    IK("doseme_bosluk") { c.L({{3, 14}, {9, 6}, {21, 6}, {15, 14}}, 1, false, true); c.L({{8, 11.5f}, {10.5f, 8.5f}, {16, 8.5f}, {13.5f, 11.5f}}, 1, false, true); } SON,
    IK("duvar") {
        c.R(3, 5, 21, 19); c.L({{3, 10}, {21, 10}}); c.L({{3, 14.5f}, {21, 14.5f}});
        c.L({{9, 5}, {9, 10}}); c.L({{15, 5}, {15, 10}}); c.L({{12, 10}, {12, 14.5f}}); c.L({{6, 10}, {6, 14.5f}});
        c.L({{18, 10}, {18, 14.5f}}); c.L({{9, 14.5f}, {9, 19}}); c.L({{15, 14.5f}, {15, 19}});
    } SON,
    IK("temel") { c.L({{10, 3}, {10, 13}}); c.L({{14, 3}, {14, 13}}); c.L({{10, 3}, {14, 3}}); c.L({{4, 13}, {20, 13}, {20, 20}, {4, 20}}, 1, false, true); c.L({{4, 22}, {20, 22}}); } SON,
    IK("temel_surekli") { c.L({{3, 12}, {21, 12}, {21, 19}, {3, 19}}, 1, false, true); c.L({{7, 5}, {7, 12}}); c.L({{17, 5}, {17, 12}}); } SON,
    IK("temel_radye") { c.R(3, 11, 21, 17); c.L({{6, 5}, {6, 11}}); c.L({{12, 5}, {12, 11}}); c.L({{18, 5}, {18, 11}}); c.L({{3, 20}, {21, 20}}); } SON,
    IK("aks") { c.L({{8, 5}, {8, 21}}); c.L({{16, 5}, {16, 21}}); c.L({{3, 10}, {21, 10}}); c.L({{3, 16}, {21, 16}}); c.E(5.5f, 2, 10.5f, 7, 1, true); c.E(13.5f, 2, 18.5f, 7, 1, true); } SON,
    IK("kat") {
        c.L({{4, 6}, {20, 6}}); c.L({{4, 12}, {20, 12}}); c.L({{4, 18}, {20, 18}});
        c.L({{20, 6}, {22, 3}, {18, 3}}, 1, true); c.L({{20, 12}, {22, 9}, {18, 9}}, 1, true); c.L({{20, 18}, {22, 15}, {18, 15}}, 1, true);
    } SON,
    IK("kat_verisi") { c.R(3, 4, 21, 20); c.L({{3, 9}, {21, 9}}); c.L({{3, 14}, {21, 14}}); c.L({{9, 4}, {9, 20}}); } SON,
    IK("duzlem") { c.L({{3, 15}, {9, 6}, {21, 6}, {15, 15}}, 1, false, true); c.L({{12, 10.5f}, {12, 2}}); c.L({{9.5f, 4.5f}, {12, 2}, {14.5f, 4.5f}}); } SON,
    IK("hizli_kolon") { c.L({{4, 12}, {20, 12}}); c.L({{12, 4}, {12, 20}}); c.nokta(12, 12, 2.2f); c.L({{15, 14}, {15, 22}, {17.2f, 19.8f}, {18.8f, 22.6f}, {20.4f, 21.6f}, {18.8f, 18.8f}, {21.6f, 18.8f}}, 1, true); } SON,
    IK("hizli_kiris") { c.L({{3, 10}, {21, 10}}, 1.6f); c.nokta(3, 10, 1.6f); c.nokta(21, 10, 1.6f); c.L({{11, 12}, {11, 21}, {13.4f, 18.6f}, {15.2f, 21.6f}, {16.8f, 20.6f}, {15, 17.6f}, {18, 17.6f}}, 1, true); } SON,
    IK("hizli_capraz") { c.L({{4, 4}, {20, 20}}); c.L({{20, 4}, {4, 20}}); c.nokta(12, 12, 1.8f); } SON,
    IK("izgara") { c.R(3, 3, 21, 21); c.L({{9, 3}, {9, 21}}); c.L({{15, 3}, {15, 21}}); c.L({{3, 9}, {21, 9}}); c.L({{3, 15}, {21, 15}}); } SON,
    IK("kesit") { c.L({{5, 4}, {19, 4}, {19, 7}, {13.5f, 7}, {13.5f, 17}, {19, 17}, {19, 20}, {5, 20}, {5, 17}, {10.5f, 17}, {10.5f, 7}, {5, 7}}, 1, false, true); } SON,
    IK("malzeme") { c.L({{4, 9}, {12, 5}, {20, 9}, {12, 13}}, 1, false, true); c.L({{4, 9}, {4, 17}, {12, 21}, {20, 17}, {20, 9}}); c.L({{12, 13}, {12, 21}}); } SON,
    IK("kutuphane") { c.R(4, 4, 8, 20); c.R(10, 4, 14, 20); c.L({{16, 5}, {20.5f, 5.8f}, {18.4f, 20.5f}, {14, 19.5f}}, 1, false, true); } SON,
    IK("sec") { c.L({{6, 3}, {6, 19}, {10, 15}, {13, 21}, {15.5f, 19.8f}, {12.5f, 14}, {18, 14}}, 1, true); } SON,
    IK("imlec") {
        const std::vector<ImVec2> p{{6, 3}, {6, 19}, {10, 15}, {13, 21}, {15.5f, 19.8f}, {12.5f, 14}, {18, 14}};
        std::vector<ImVec2> q;
        for (const ImVec2& v : p) q.push_back(c.P(v.x, v.y));
        c.dl->AddConcavePolyFilled(q.data(), static_cast<int>(q.size()), IM_COL32_WHITE);
        c.L(p, 1, false, true);
    } SON,
    IK("sec_pencere") {
        for (int i = 0; i < 18; i += 4) {
            const float f = static_cast<float>(i);
            c.L({{3 + f, 3}, {3 + f + 2, 3}}); c.L({{3 + f, 21}, {3 + f + 2, 21}}); c.L({{3, 3 + f}, {3, 3 + f + 2}}); c.L({{21, 3 + f}, {21, 3 + f + 2}});
        }
        c.L({{10, 9}, {10, 19}, {12.5f, 16.5f}, {14.5f, 20.5f}, {16.2f, 19.6f}, {14.2f, 15.7f}, {17.5f, 15.7f}}, 1, true);
    } SON,
    IK("suz") { c.L({{3, 4}, {21, 4}, {14, 12.5f}, {14, 20}, {10, 17.5f}, {10, 12.5f}}, 1, false, true); } SON,
    IK("sec_suz") { c.L({{3, 4}, {17, 4}, {11.5f, 11}, {11.5f, 18}, {8, 15.5f}, {8, 11}}, 1, false, true); c.L({{15, 13}, {15, 22}, {17.4f, 19.6f}, {19.2f, 22.6f}, {20.8f, 21.6f}, {19, 18.6f}, {22, 18.6f}}, 1, true); } SON,
    IK("benzer") { c.R(3, 5, 21, 9); c.R(3, 15, 21, 19); c.L({{3, 12}, {21, 12}}, 0.6f); } SON,
    IK("ters") { c.R(3, 3, 11, 11, 1, true); c.R(13, 13, 21, 21, 1, true); c.R(13, 3, 21, 11); c.R(3, 13, 11, 21); } SON,
    IK("katman") { c.L({{12, 3}, {21, 8}, {12, 13}, {3, 8}}, 1, false, true); c.L({{3, 12}, {12, 17}, {21, 12}}); c.L({{3, 16}, {12, 21}, {21, 16}}); } SON,
    IK("etiket") { c.L({{3, 3}, {12, 3}, {21, 12}, {12, 21}, {3, 12}}, 1, false, true); c.nokta(7.5f, 7.5f, 1.4f); } SON,
    IK("ice_aktar") { c.L({{4, 10}, {4, 21}, {20, 21}, {20, 10}}); c.L({{12, 2}, {12, 15}}); c.L({{7.5f, 10.5f}, {12, 15}, {16.5f, 10.5f}}); } SON,
    IK("disa_aktar") { c.L({{4, 10}, {4, 21}, {20, 21}, {20, 10}}); c.L({{12, 15}, {12, 2}}); c.L({{7.5f, 6.5f}, {12, 2}, {16.5f, 6.5f}}); } SON,
    IK("dogrula") { c.E(3, 3, 21, 21); c.L({{7.5f, 12.5f}, {10.8f, 15.8f}, {16.8f, 8.8f}}); } SON,
    IK("rapor") { c.L({{5, 2.5f}, {14, 2.5f}, {19, 7.5f}, {19, 21.5f}, {5, 21.5f}}, 1, false, true); c.L({{14, 2.5f}, {14, 7.5f}, {19, 7.5f}}); c.L({{8, 12}, {16, 12}}); c.L({{8, 15.5f}, {16, 15.5f}}); c.L({{8, 19}, {13, 19}}); } SON,
    IK("ayar") {
        for (int i = 0; i < 8; ++i) {
            const float a = static_cast<float>(i) * PI_F / 4.0f;
            c.L({{12 + 7 * std::cos(a), 12 + 7 * std::sin(a)}, {12 + 10 * std::cos(a), 12 + 10 * std::sin(a)}}, 1.6f);
        }
        c.E(5, 5, 19, 19); c.E(9.5f, 9.5f, 14.5f, 14.5f);
    } SON,
    IK("ara") { c.E(4, 4, 15, 15); c.L({{13.5f, 13.5f}, {20.5f, 20.5f}}, 1.3f); } SON,
    IK("kapat") { c.L({{6, 6}, {18, 18}}); c.L({{18, 6}, {6, 18}}); } SON,
    IK("kucult") { c.L({{5, 12}, {19, 12}}); } SON,
    IK("buyut") { c.R(5.5f, 5.5f, 18.5f, 18.5f); } SON,
    IK("geri_al") { c.L({{4, 10}, {20, 10}}); c.L({{9, 5}, {4, 10}, {9, 15}}); c.L({{20, 10}, {20, 16}, {10, 16}}); } SON,
    IK("yinele") { c.L({{20, 10}, {4, 10}}); c.L({{15, 5}, {20, 10}, {15, 15}}); c.L({{4, 10}, {4, 16}, {14, 16}}); } SON,
    IK("kaydet") { c.L({{4, 4}, {17, 4}, {20, 7}, {20, 20}, {4, 20}}, 1, false, true); c.R(8, 4, 15, 9); c.R(7.5f, 13, 16.5f, 20); } SON,
    IK("ac") { c.L({{3, 6}, {9, 6}, {11, 8.5f}, {21, 8.5f}, {21, 19}, {3, 19}}, 1, false, true); c.L({{3, 12}, {21, 12}}); } SON,
    IK("yeni") { c.L({{5, 2.5f}, {14, 2.5f}, {19, 7.5f}, {19, 21.5f}, {5, 21.5f}}, 1, false, true); c.L({{14, 2.5f}, {14, 7.5f}, {19, 7.5f}}); c.L({{12, 11}, {12, 18}}); c.L({{8.5f, 14.5f}, {15.5f, 14.5f}}); } SON,
    IK("yazdir") { c.L({{7, 9}, {7, 3}, {17, 3}, {17, 9}}); c.R(3, 9, 21, 17); c.L({{7, 14}, {7, 21}, {17, 21}, {17, 14}}); } SON,
    IK("ok_asagi") { c.L({{7, 9.5f}, {17, 9.5f}, {12, 15}}, 1, true); } SON,
    IK("sevron_asagi") { c.L({{6, 9}, {12, 15}, {18, 9}}); } SON,
    IK("sevron_sag") { c.L({{9, 6}, {15, 12}, {9, 18}}); } SON,
    IK("sevron_ust") { c.L({{6, 15}, {12, 9}, {18, 15}}); } SON,
    IK("sevron_sol") { c.L({{15, 6}, {9, 12}, {15, 18}}); } SON,
    IK("sevron_cift_ust") { c.L({{6, 12}, {12, 6}, {18, 12}}); c.L({{6, 18}, {12, 12}, {18, 18}}); } SON,
    IK("sevron_cift_asagi") { c.L({{6, 6}, {12, 12}, {18, 6}}); c.L({{6, 12}, {12, 18}, {18, 12}}); } SON,
    IK("pin") { c.L({{9, 3}, {15, 3}}); c.L({{10, 3}, {10, 11}, {6.5f, 14}, {17.5f, 14}, {14, 11}, {14, 3}}); c.L({{12, 14}, {12, 21}}); } SON,
    IK("goz") { c.L({{2.5f, 12}, {6.5f, 7}, {12, 5.5f}, {17.5f, 7}, {21.5f, 12}, {17.5f, 17}, {12, 18.5f}, {6.5f, 17}}, 1, false, true); c.E(9, 9, 15, 15); } SON,
    IK("goz_kapali") { c.L({{2.5f, 12}, {6.5f, 7}, {12, 5.5f}, {17.5f, 7}, {21.5f, 12}}); c.L({{4, 20}, {20, 4}}); } SON,
    IK("proje") { c.R(4, 5, 20, 21); c.L({{8, 9}, {10, 9}}); c.L({{14, 9}, {16, 9}}); c.L({{8, 13}, {10, 13}}); c.L({{14, 13}, {16, 13}}); c.L({{10.5f, 21}, {10.5f, 17}, {13.5f, 17}, {13.5f, 21}}); } SON,
    IK("dugum") { c.L({{12, 3}, {12, 21}}); c.L({{3, 12}, {21, 12}}); c.E(8.5f, 8.5f, 15.5f, 15.5f, 1, true); } SON,
    IK("tasi") { c.L({{12, 3}, {12, 21}}); c.L({{3, 12}, {21, 12}}); c.L({{9, 6}, {12, 3}, {15, 6}}); c.L({{9, 18}, {12, 21}, {15, 18}}); c.L({{6, 9}, {3, 12}, {6, 15}}); c.L({{18, 9}, {21, 12}, {18, 15}}); } SON,
    IK("kopyala") { c.R(8, 8, 21, 21); c.L({{16, 8}, {16, 3}, {3, 3}, {3, 16}, {8, 16}}); } SON,
    IK("dondur") { c.yay(4, 4, 20, 20, 200, 120); c.L({{13, 2}, {17.5f, 5.5f}, {13.5f, 9}}); c.nokta(12, 12, 1.5f); } SON,
    IK("aynala") { c.L({{12, 3}, {12, 21}}, 0.9f); c.L({{9, 7}, {9, 17}, {3, 17}}, 1, false, true); c.L({{15, 7}, {15, 17}, {21, 17}}, 1, false, true); } SON,
    IK("bol") { c.L({{3, 12}, {21, 12}}); c.L({{12, 5}, {12, 19}}); c.nokta(12, 12, 2); c.nokta(3, 12, 1.5f); c.nokta(21, 12, 1.5f); } SON,
    IK("sil") { c.L({{4, 6}, {20, 6}}); c.L({{9, 6}, {9, 3.5f}, {15, 3.5f}, {15, 6}}); c.L({{6, 6}, {7, 21}, {17, 21}, {18, 6}}); c.L({{10, 10}, {10, 17}}); c.L({{14, 10}, {14, 17}}); } SON,
    IK("olcu") {
        c.L({{3, 15}, {15, 3}, {21, 9}, {9, 21}}, 1, false, true);
        for (int i = 1; i < 5; ++i) {
            const float f = static_cast<float>(i) * 2.4f;
            c.L({{5 + f, 15 - f}, {5 + f + 2, 15 - f + 2}});
        }
    } SON,
    IK("kesit_duzlemi") { c.L({{3, 15}, {9, 6}, {21, 6}, {15, 15}}, 1, false, true); c.L({{12, 2}, {12, 22}}, 0.9f); c.L({{9, 19}, {12, 22}, {15, 19}}); } SON,
    IK("yakinlastir") { c.E(4, 4, 15, 15); c.L({{13.5f, 13.5f}, {20.5f, 20.5f}}, 1.3f); c.L({{9.5f, 6.5f}, {9.5f, 12.5f}}); c.L({{6.5f, 9.5f}, {12.5f, 9.5f}}); } SON,
    IK("sigdir") { c.L({{3, 8}, {3, 3}, {8, 3}}); c.L({{16, 3}, {21, 3}, {21, 8}}); c.L({{21, 16}, {21, 21}, {16, 21}}); c.L({{8, 21}, {3, 21}, {3, 16}}); c.R(8, 8, 16, 16); } SON,
    IK("ev") { c.L({{3, 12}, {12, 4}, {21, 12}}); c.L({{6, 10}, {6, 20}, {18, 20}, {18, 10}}); } SON,
    IK("kilit") { c.R(5, 11, 19, 21); c.yay(8, 4, 16, 14, 180, 360); c.L({{8, 9}, {8, 11}}); c.L({{16, 9}, {16, 11}}); } SON,
    IK("onay") { c.L({{5, 12.5f}, {10, 17.5f}, {19, 7}}, 1.3f); } SON,
    IK("yuk") {
        c.L({{3, 19}, {21, 19}}); c.L({{7, 4}, {7, 15}}); c.L({{12, 4}, {12, 15}}); c.L({{17, 4}, {17, 15}});
        c.L({{5, 13}, {7, 15.5f}, {9, 13}}); c.L({{10, 13}, {12, 15.5f}, {14, 13}}); c.L({{15, 13}, {17, 15.5f}, {19, 13}});
    } SON,
    IK("yuk_nokta") { c.L({{3, 19}, {21, 19}}); c.L({{12, 3}, {12, 16}}, 1.3f); c.L({{8.5f, 12.5f}, {12, 16.5f}, {15.5f, 12.5f}}); } SON,
    IK("mesnet") { c.L({{12, 5}, {19, 16}, {5, 16}}, 1, false, true); c.L({{3, 20}, {21, 20}}); c.L({{5, 20}, {3, 22.5f}}); c.L({{10, 20}, {8, 22.5f}}); c.L({{15, 20}, {13, 22.5f}}); c.L({{20, 20}, {18, 22.5f}}); } SON,
    IK("mafsal") { c.L({{3, 12}, {8, 12}}); c.L({{16, 12}, {21, 12}}); c.E(8, 8, 16, 16); } SON,
    IK("rijit") { c.L({{3, 12}, {21, 12}}); c.L({{12, 5}, {12, 19}}, 1.4f); } SON,
    IK("analiz") { c.L({{3, 19}, {21, 19}}); c.yay(3, 6, 21, 32, 200, 340); c.L({{3, 19}, {3, 6}}); c.L({{21, 19}, {21, 6}}); } SON,
    IK("coz") { c.L({{6, 4}, {20, 12}, {6, 20}}, 1, true); } SON,
    IK("oynat") { c.L({{7, 5}, {19, 12}, {7, 19}}, 1, false, true); } SON,
    IK("durdur") { c.R(6, 6, 18, 18); } SON,
    IK("deform") { c.L({{3, 8}, {21, 8}}, 0.6f); c.yay(3, 2, 21, 26, 20, 160, 1.3f); } SON,
    IK("diyagram") { c.L({{3, 18}, {21, 18}}); c.L({{3, 18}, {3, 8}, {21, 14}, {21, 18}}, 1, false, true); } SON,
    IK("dc") { c.R(3, 14, 7, 20, 1, true); c.R(8.5f, 10, 12.5f, 20, 1, true); c.R(14, 6, 18, 20, 1, true); c.L({{3, 22}, {21, 22}}); } SON,
    IK("sonuc") { c.L({{3, 21}, {21, 21}}); c.R(5, 12, 9, 21, 1, true); c.R(10.5f, 6, 14.5f, 21, 1, true); c.R(16, 15, 20, 21, 1, true); } SON,
    IK("tablo") { c.R(3, 4, 21, 20); c.L({{3, 9.5f}, {21, 9.5f}}); c.L({{3, 15}, {21, 15}}); c.L({{9, 4}, {9, 20}}); c.L({{15, 4}, {15, 20}}); } SON,
    IK("mesaj") { c.L({{3, 4}, {21, 4}, {21, 16}, {10, 16}, {6, 20}, {6, 16}, {3, 16}}, 1, false, true); } SON,
    IK("bilgi") { c.E(3, 3, 21, 21); c.L({{12, 11}, {12, 17}}); c.nokta(12, 7.8f, 1.3f); } SON,
    IK("uyari") { c.L({{12, 3.5f}, {21.5f, 20}, {2.5f, 20}}, 1, false, true); c.L({{12, 9}, {12, 14.5f}}); c.nokta(12, 17.3f, 1.2f); } SON,
    IK("yakala") { c.R(5, 5, 19, 19); c.L({{12, 1}, {12, 7}}); c.L({{12, 17}, {12, 23}}); c.L({{1, 12}, {7, 12}}); c.L({{17, 12}, {23, 12}}); } SON,
    IK("orto") { c.L({{4, 20}, {4, 4}}); c.L({{4, 20}, {20, 20}}); c.R(4, 14, 10, 20); } SON,
    IK("perspektif") { c.L({{5, 20}, {9, 6}, {15, 6}, {19, 20}}, 1, false, true); c.L({{3, 12}, {21, 12}}); } SON,
    IK("kati") { c.L({{12, 3}, {21, 8}, {12, 13}, {3, 8}}, 1, false, true); c.L({{3, 8}, {3, 17}, {12, 22}, {21, 17}, {21, 8}}); c.L({{12, 13}, {12, 22}}); } SON,
    IK("cubuk") { c.L({{3, 18}, {21, 6}}); c.nokta(3, 18, 1.8f); c.nokta(21, 6, 1.8f); } SON,
    IK("yonetmelik") { c.L({{4, 4}, {18, 4}, {18, 20}, {4, 20}}, 1, false, true); c.L({{4, 4}, {4, 20}}, 1.6f); c.L({{8, 12}, {10.5f, 14.5f}, {15, 9.5f}}); } SON,
    IK("tasarim") { c.L({{3, 17}, {17, 3}}, 1.2f); c.L({{5, 21}, {21, 5}}, 1.2f); c.L({{3, 17}, {5, 21}}); c.L({{17, 3}, {21, 5}}); } SON,
    IK("kontrol") { c.L({{12, 3}, {20, 6}, {20, 12}, {12, 21}, {4, 12}, {4, 6}}, 1, false, true); c.L({{8.5f, 12}, {11, 14.5f}, {15.5f, 9.5f}}); } SON,
    IK("bina3") { c.L({{4, 9}, {12, 4}, {20, 9}, {12, 14}}, 1, false, true); c.L({{4, 9}, {4, 18}, {12, 23}, {20, 18}, {20, 9}}); c.L({{12, 14}, {12, 23}}); } SON,
    IK("cerceve") { c.L({{4, 20}, {4, 6}, {20, 6}, {20, 20}}); c.L({{12, 6}, {12, 20}}); c.L({{4, 13}, {20, 13}}); } SON,
    IK("plan") { c.R(3, 3, 21, 21); c.L({{3, 12}, {21, 12}}); c.L({{12, 3}, {12, 21}}); c.nokta(7.5f, 7.5f, 1.4f); c.nokta(16.5f, 16.5f, 1.4f); } SON,
    IK("yukselti") { c.R(3, 3, 21, 21); c.L({{3, 9}, {21, 9}}); c.L({{3, 15}, {21, 15}}); c.L({{8, 3}, {8, 21}}); c.L({{16, 3}, {16, 21}}); } SON,
    IK("sorgu") { c.L({{3, 3}, {12, 3}, {21, 12}, {12, 21}, {3, 12}}, 1, false, true); c.nokta(7.5f, 7.5f, 1.3f); } SON,
    IK("pencere") { c.R(3, 4, 21, 20); c.L({{3, 9}, {21, 9}}); } SON,
    IK("sol_yapistir") { c.R(3, 4, 21, 20); c.R(3, 4, 9, 20, 1, true); } SON,
    IK("tam") { c.R(3, 5, 21, 19); c.L({{6, 8}, {10, 8}}); c.L({{6, 11}, {14, 11}}); } SON,
    IK("yardim") { c.E(3, 3, 21, 21); c.yay(8.5f, 6.5f, 15.5f, 13.5f, 190, 90); c.L({{12, 13.5f}, {12, 15.5f}}); c.nokta(12, 18.3f, 1.2f); } SON,
    IK("anahtar") {
        c.dl->AddRect(c.P(3, 8), c.P(21, 16), c.c, 4 * c.u, c.k);
        c.E(13, 9.5f, 18, 14.5f, 1, true);
    } SON,
    IK("dm") { c.L({{5, 12}, {19, 12}}); c.R(2.5f, 9.5f, 7.5f, 14.5f, 1, true); c.R(16.5f, 9.5f, 21.5f, 14.5f, 1, true); } SON,
    IK("nokta_ekle") { c.L({{12, 4}, {12, 20}}); c.L({{4, 12}, {20, 12}}); } SON,
    IK("kopyala_kat") { c.L({{4, 6}, {20, 6}}); c.L({{4, 12}, {20, 12}}); c.L({{4, 18}, {20, 18}}, 1.4f); c.L({{22, 10}, {22, 16}}); c.L({{20, 12}, {22, 14}, {24, 12}}); } SON,
    IK("tablo_disa") { c.R(3, 4, 21, 20); c.L({{3, 9.5f}, {21, 9.5f}}); c.L({{3, 15}, {21, 15}}); c.L({{9, 4}, {9, 20}}); c.L({{13, 12}, {17, 18}}); c.L({{17, 12}, {13, 18}}); } SON,
    IK("nokta") { c.nokta(12, 12, 3); } SON,
    IK("arti") { c.L({{12, 5}, {12, 19}}); c.L({{5, 12}, {19, 12}}); } SON,
    // ---- op4 ekleri (aynı dil) ----
    IK("geri_yukle") { c.R(5, 8, 16, 19); c.L({{8, 8}, {8, 5}, {19, 5}, {19, 16}, {16, 16}}); } SON,
    IK("sablon") { c.R(4, 4, 11, 11); c.R(13, 4, 20, 11); c.R(4, 13, 11, 20); c.R(13, 13, 20, 20); } SON,
    IK("gecmis") { c.E(3, 3, 21, 21); c.L({{12, 7}, {12, 12.5f}, {15.5f, 14.5f}}); } SON,
    IK("klavye") { c.R(3, 6, 21, 18); c.L({{6.5f, 10}, {7.5f, 10}}); c.L({{10, 10}, {11, 10}}); c.L({{13.5f, 10}, {14.5f, 10}}); c.L({{17, 10}, {18, 10}}); c.L({{8, 14.5f}, {16, 14.5f}}); } SON,
    IK("konsol") { c.L({{5, 4}, {5, 20}}, 1.4f); c.L({{5, 9}, {19, 9}}); c.L({{19, 9}, {19, 12}}); c.L({{5, 13}, {13, 13}}); } SON,
    IK("beton") { c.R(4, 4, 20, 20); c.nokta(8, 8, 1.1f); c.nokta(14, 10, 1.1f); c.nokta(9, 15, 1.1f); c.nokta(16, 16, 1.1f); } SON,
    IK("kompozit") { c.R(3, 4, 21, 9); c.L({{9, 9}, {15, 9}}); c.L({{12, 9}, {12, 17}}); c.L({{8, 17}, {16, 17}}); c.L({{8, 20}, {16, 20}}); } SON,
    IK("reaksiyon") { c.L({{4, 6}, {20, 6}}); c.L({{12, 6}, {16, 12}, {8, 12}}, 1, false, true); c.L({{12, 12}, {12, 20}}); c.L({{9.5f, 17.5f}, {12, 20}, {14.5f, 17.5f}}); } SON,
    IK("dil") { c.E(3, 3, 21, 21); c.L({{3, 12}, {21, 12}}); c.yay(7, 3, 17, 21, 270, 450); c.yay(7, 3, 17, 21, 90, 270); } SON,
    IK("bos") { (void)c; } SON,
};

#undef IK
#undef SON

}  // namespace

bool IkonCiz(ImDrawList* dl, std::string_view ad, float x, float y, float boy, uint32_t renk, float kalem) {
    for (const IkonKaydi& k : kIkonlar)
        if (ad == k.ad) {
            const Kalem c{dl, x, y, boy / 24.0f, kalem, renk};
            k.f(c);
            return true;
        }
    const Kalem c{dl, x, y, boy / 24.0f, kalem, renk};
    c.E(5, 5, 19, 19);  // taslaktaki bilinmeyen simge yedeği
    return false;
}

bool IkonVar(std::string_view ad) {
    for (const IkonKaydi& k : kIkonlar)
        if (ad == k.ad) return true;
    return false;
}

}  // namespace op4
