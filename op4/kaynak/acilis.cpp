// op4 — açılış ekranı "Kemer Çizgisi" (bkz. acilis.h; kimlik/acilis/aciklama.md, kimlik/acilis-koyu/aciklama.md).
// Çizim tek işlevdedir (KemerCizimi::Ciz): pencere ve --test-acilis aynı kodu kullanır. Kimlik renkleri (kâğıt, Altın,
// Kahve, Krem) yalnız burada ve logodadır; arayüz belirteçleri (arayuz/tema.h) açılış ekranında kullanılmaz (MIMARI §5.9).
#include "acilis.h"

#include <d2d1.h>
#include <dwrite_3.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <mutex>
#include <thread>
#include <vector>

#include "arayuz/acilis_kontur.h"
#include "arayuz/dil.h"
#include "arayuz/yazi.h"
#include "gunluk.h"
#include "resim.h"
#include "secenekler.h"

namespace op4 {
namespace {

template <class T>
void Birak(T*& p) {
    if (p) {
        p->Release();
        p = nullptr;
    }
}

// ---- zaman çizelgesi (aciklama.md "Hareket çizelgesi"; uret.py ADIM) -------------------------------------------------------
constexpr double kPi = 3.14159265358979323846;
constexpr double ADIM_BAS[6] = {250, 700, 1300, 2400, 3050, 3650};
constexpr double ADIM_P[6] = {0.0, 0.12, 0.30, 0.62, 0.84, 1.0};
constexpr double T_HAZIR = 3650, SON_KARE = 4650, BITIS = 4950;
constexpr double KEMER_PAY = 0.86;
const char* const kDurum[6] = {"Arayüz hazırlanıyor…", "DirectX 12 aygıtı açılıyor…", "Hesap motoru (Python) yükleniyor…",
                               "Kesit kütüphanesi okunuyor…", "Son proje açılıyor…", "Hazır"};

double K01(double x) { return std::clamp(x, 0.0, 1.0); }
double Oran(double t, double a, double b) { return K01((t - a) / (b - a)); }
double E3(double u) {
    u = K01(u);
    return 1.0 - (1.0 - u) * (1.0 - u) * (1.0 - u);
}
double Yumusak(double u) { return 0.55 * u + 0.45 * (0.5 - 0.5 * std::cos(kPi * u)); }
double Ilerleme(double t) {
    if (t <= ADIM_BAS[0]) return 0.0;
    for (int k = 0; k < 5; ++k)
        if (t < ADIM_BAS[k + 1]) return ADIM_P[k] + (ADIM_P[k + 1] - ADIM_P[k]) * Yumusak((t - ADIM_BAS[k]) / (ADIM_BAS[k + 1] - ADIM_BAS[k]));
    return 1.0;
}
int AdimNo(double t) {
    int k = 0;
    for (int i = 1; i < 6; ++i)
        if (t >= ADIM_BAS[i]) k = i;
    return k;
}

// ---- yerleşim (mantıksal px / DIP, 960 × 540) --------------------------------------------------------------------------
constexpr float GEN = 960, YUK = 540;
constexpr float KEMER_CX = 268, KEMER_UST = 112, KEMER_YUKS = 256, SAG_X = 512, SAG_SON = 904;
const float OLCEK_SIMGE = KEMER_YUKS / (kontur::KUTU_Y1 - kontur::KUTU_Y0);
D2D1_POINT_2F Simge(float x, float y) {
    return D2D1::Point2F(KEMER_CX + (x - kontur::CX) * OLCEK_SIMGE, KEMER_UST + (y - kontur::KUTU_Y0) * OLCEK_SIMGE);
}

// ---- iki zemin (açık özgün, koyu ikiz) -----------------------------------------------------------------------------------
struct Palet {
    uint32_t zemin, zeminMerkez, vinyet;
    uint32_t iskele;
    float iskeleA, uzengiA, merkezA, hayaletA;
    float izKalinlik, derzA;
    uint32_t ucNokta;
    float haleR, haleA0, haleA1;
    float isikTepe, isikKalan, halkaTepe;
    bool kilitKenari;
    uint32_t metin, durumRenk, altRenk;
    float altBaslikA, durumA, hazirA, surumA, telifA;
    uint32_t izRenk;
    float izA;
    uint32_t ucRenk;
    float parilti;
    uint32_t kenar;
    float kenarA;
    const wchar_t* yaziPng;
};
constexpr uint32_t ANTRASIT = 0x14181B, ALTIN = 0xB08950, KREM = 0xEDE6D8, GRI = 0x8C8C8C;
const Palet kAcik{0xF6F2EA, 0xFBF8F2, 0xEFE9DD, ANTRASIT, 0.22f, 0.15f, 0.30f, 0.20f, 1.75f, 0.55f, 0x8A6B3C, 13, 0.22f, 0.10f,
                  0.22f, 0.05f, 0.035f, true, ANTRASIT, ANTRASIT, ANTRASIT, 0.80f, 0.62f, 0.92f, 0.55f, 0.45f, ANTRASIT, 0.12f,
                  0xC2A579, 0.45f, ANTRASIT, 0.08f, L"opus-fortis-yazi-acik-zemin.png"};
const Palet kKoyu{ANTRASIT, 0x222425, ANTRASIT, GRI, 0.30f, 0.20f, 0.40f, 0.26f, 1.5f, 0.42f, KREM, 16, 0.42f, 0.20f,
                  0.28f, 0.055f, 0.045f, false, KREM, GRI, GRI, 0.80f, 0.90f, 0.95f, 0.85f, 0.70f, KREM, 0.10f,
                  0xDBCAAF, 0.55f, 0xFFFFFF, 0.07f, L"opus-fortis-yazi-koyu-zemin.png"};

D2D1_COLOR_F Rk(uint32_t rgb, float a = 1.0f) {
    return D2D1::ColorF(((rgb >> 16) & 255) / 255.0f, ((rgb >> 8) & 255) / 255.0f, (rgb & 255) / 255.0f, a);
}

// ---- çalışma anında yüklenen D2D / DWrite ----------------------------------------------------------------------------------
using D2DOlustur = HRESULT(WINAPI*)(D2D1_FACTORY_TYPE, REFIID, const D2D1_FACTORY_OPTIONS*, void**);
using DWOlustur = HRESULT(WINAPI*)(DWRITE_FACTORY_TYPE, REFIID, IUnknown**);

struct Fabrikalar {
    HMODULE d2dDll = nullptr, dwDll = nullptr;
    ID2D1Factory* d2d = nullptr;
    IDWriteFactory* dw = nullptr;
    IDWriteFontCollection* koleksiyon = nullptr;  // gömülü yazı tipleri (yoksa sistem)
    IDWriteInMemoryFontFileLoader* yukleyici = nullptr;
    std::wstring arayuzAilesi = L"Segoe UI", inceAile = L"Segoe UI Light", altAile = L"Georgia";

    bool Kur(std::string& hata) {
        d2dDll = LoadLibraryW(L"d2d1.dll");
        dwDll = LoadLibraryW(L"dwrite.dll");
        auto d2dOl = d2dDll ? reinterpret_cast<D2DOlustur>(reinterpret_cast<void*>(GetProcAddress(d2dDll, "D2D1CreateFactory"))) : nullptr;
        auto dwOl = dwDll ? reinterpret_cast<DWOlustur>(reinterpret_cast<void*>(GetProcAddress(dwDll, "DWriteCreateFactory"))) : nullptr;
        if (!d2dOl || !dwOl) {
            hata = "d2d1.dll / dwrite.dll yüklenemedi";
            return false;
        }
        D2D1_FACTORY_OPTIONS fo{};
        if (FAILED(d2dOl(D2D1_FACTORY_TYPE_SINGLE_THREADED, __uuidof(ID2D1Factory), &fo, reinterpret_cast<void**>(&d2d)))) {
            hata = "D2D1CreateFactory başarısız";
            return false;
        }
        if (FAILED(dwOl(DWRITE_FACTORY_TYPE_ISOLATED, __uuidof(IDWriteFactory), reinterpret_cast<IUnknown**>(&dw)))) {
            hata = "DWriteCreateFactory başarısız";
            return false;
        }
        GomuluYazilariKur();
        return true;
    }
    // Gömülü yazı tipleri: IDWriteFactory5 bellek içi yükleyici (Windows 10 1703+). Yoksa sistem yazı tipleri.
    void GomuluYazilariKur() {
        IDWriteFactory5* f5 = nullptr;
        if (FAILED(dw->QueryInterface(__uuidof(IDWriteFactory5), reinterpret_cast<void**>(&f5)))) return;
        IDWriteFontSetBuilder1* kurucu = nullptr;
        IDWriteFontSet* kume = nullptr;
        IDWriteFontCollection1* kol = nullptr;
        bool tamam = SUCCEEDED(f5->CreateInMemoryFontFileLoader(&yukleyici)) && SUCCEEDED(f5->RegisterFontFileLoader(yukleyici)) &&
                     SUCCEEDED(f5->CreateFontSetBuilder(&kurucu));
        for (const char* ad : {"AcilisInce", "Arayuz400", "Arayuz500", "Cormorant500"}) {
            if (!tamam) break;
            const std::vector<uint8_t>* v = YaziVerisi(ad);
            if (!v) continue;
            IDWriteFontFile* dosya = nullptr;
            if (SUCCEEDED(yukleyici->CreateInMemoryFontFileReference(f5, v->data(), static_cast<UINT32>(v->size()), nullptr, &dosya)))
                kurucu->AddFontFile(dosya);
            Birak(dosya);
        }
        if (tamam && SUCCEEDED(kurucu->CreateFontSet(&kume)) && SUCCEEDED(f5->CreateFontCollectionFromFontSet(kume, &kol))) {
            koleksiyon = kol;
            arayuzAilesi = Genis(ArayuzYaziAilesi());
            inceAile = L"Inter";
            altAile = L"Cormorant Garamond";
        }
        Birak(kume);
        Birak(kurucu);
        Birak(f5);
    }
    ~Fabrikalar() {
        Birak(koleksiyon);
        if (yukleyici && dw) dw->UnregisterFontFileLoader(yukleyici);
        Birak(yukleyici);
        Birak(dw);
        Birak(d2d);
        if (dwDll) FreeLibrary(dwDll);
        if (d2dDll) FreeLibrary(d2dDll);
    }
};

std::wstring KimlikDizini(const std::wstring& uygulama) {
    const std::wstring a = uygulama + L"\\kimlik";
    if (GetFileAttributesW((a + L"\\acilis\\katmanlar\\kemer.png").c_str()) != INVALID_FILE_ATTRIBUTES) return a;
    return VeriDizini() + L"\\..\\kimlik";  // geliştirme derlemesi: kaynak ağacı
}

// ---- çizim ------------------------------------------------------------------------------------------------------------
class KemerCizimi {
public:
    KemerCizimi(Fabrikalar& f, const Palet& p, std::string surum) : f_(f), p_(p), surum_(Genis(surum)) {}
    ~KemerCizimi() { Serbest(); }

    // rt'ye bağlı kaynaklar (bitmap, fırça, biçim).
    bool Kur(ID2D1RenderTarget* rt, const std::wstring& kimlik) {
        rt_ = rt;
        rt->CreateSolidColorBrush(Rk(0), &firca_);
        ID2D1StrokeStyle* s = nullptr;
        D2D1_STROKE_STYLE_PROPERTIES yp = D2D1::StrokeStyleProperties(D2D1_CAP_STYLE_ROUND, D2D1_CAP_STYLE_ROUND, D2D1_CAP_STYLE_ROUND,
                                                                      D2D1_LINE_JOIN_ROUND);
        f_.d2d->CreateStrokeStyle(yp, nullptr, 0, &s);
        yuvarlak_ = s;
        const float kesik[2] = {3.5f / 0.75f, 3.0f / 0.75f};  // kalınlık birimi (0,75 DIP)
        D2D1_STROKE_STYLE_PROPERTIES kp = D2D1::StrokeStyleProperties(D2D1_CAP_STYLE_FLAT, D2D1_CAP_STYLE_FLAT, D2D1_CAP_STYLE_FLAT,
                                                                      D2D1_LINE_JOIN_ROUND, 10.0f, D2D1_DASH_STYLE_CUSTOM);
        f_.d2d->CreateStrokeStyle(kp, kesik, 2, &kesik_);
        kemer_ = Bitmap(kimlik + L"\\acilis\\katmanlar\\kemer.png");
        kilit_ = Bitmap(kimlik + L"\\acilis\\katmanlar\\kilit.png");
        yazi_ = Bitmap(kimlik + L"\\" + p_.yaziPng);
        auto bicim = [&](const std::wstring& aile, float boy, DWRITE_FONT_WEIGHT a, IDWriteTextFormat** o) {
            if (FAILED(f_.dw->CreateTextFormat(aile.c_str(), f_.koleksiyon, a, DWRITE_FONT_STYLE_NORMAL, DWRITE_FONT_STRETCH_NORMAL, boy,
                                               L"tr-TR", o)))
                f_.dw->CreateTextFormat(L"Segoe UI", nullptr, a, DWRITE_FONT_STYLE_NORMAL, DWRITE_FONT_STRETCH_NORMAL, boy, L"tr-TR", o);
        };
        bicim(f_.inceAile, 92, DWRITE_FONT_WEIGHT_LIGHT, &bOp4_);
        bicim(f_.altAile, 25, DWRITE_FONT_WEIGHT_MEDIUM, &bAlt_);
        bicim(f_.arayuzAilesi, 12.5f, DWRITE_FONT_WEIGHT_NORMAL, &bDurum_);
        bicim(f_.arayuzAilesi, 12.5f, DWRITE_FONT_WEIGHT_MEDIUM, &bYuzde_);
        bicim(f_.arayuzAilesi, 11, DWRITE_FONT_WEIGHT_NORMAL, &bAltBilgi_);
        // sabit fırçalar
        auto radyal = [&](std::vector<D2D1_GRADIENT_STOP> d, D2D1_POINT_2F m, float rx, float ry) {
            ID2D1GradientStopCollection* k = nullptr;
            ID2D1RadialGradientBrush* b = nullptr;
            rt->CreateGradientStopCollection(d.data(), static_cast<UINT32>(d.size()), D2D1_GAMMA_2_2, D2D1_EXTEND_MODE_CLAMP, &k);
            if (k) rt->CreateRadialGradientBrush(D2D1::RadialGradientBrushProperties(m, D2D1::Point2F(), rx, ry), k, &b);
            Birak(k);
            return b;
        };
        {  // merkez aydınlanması (1 − u)²
            std::vector<D2D1_GRADIENT_STOP> d;
            for (int i = 0; i <= 8; ++i) {
                const float u = i / 8.0f, a = (1 - u) * (1 - u);
                d.push_back({u, Rk(p_.zeminMerkez, a)});
            }
            merkez_ = radyal(d, D2D1::Point2F(268, 235), 380, 330);
        }
        if (p_.vinyet != p_.zemin) {  // vinyet clamp((d − 0,5)/0,9)^1,5, d = 0 … 1,42
            std::vector<D2D1_GRADIENT_STOP> d;
            for (int i = 0; i <= 10; ++i) {
                const float u = i / 10.0f, dd = u * 1.42f, a = std::pow(std::clamp((dd - 0.5f) / 0.9f, 0.0f, 1.0f), 1.5f);
                d.push_back({u, Rk(p_.vinyet, a)});
            }
            vinyet_ = radyal(d, D2D1::Point2F(480, 270), 795 * 1.42f, 511 * 1.42f);
        }
        {  // kilit taşı ışığı: a(u) = ½ + ½·cos πu, 13 durak
            std::vector<D2D1_GRADIENT_STOP> d;
            for (int i = 0; i <= 12; ++i) {
                const float u = i / 12.0f;
                d.push_back({u, Rk(ALTIN, 0.5f + 0.5f * static_cast<float>(std::cos(kPi * u)))});
            }
            isik_ = radyal(d, D2D1::Point2F(268, 136.9f), 112, 112);
        }
        hale_ = radyal({{0, Rk(ALTIN, p_.haleA0)}, {0.5f, Rk(ALTIN, p_.haleA1)}, {1, Rk(ALTIN, 0)}}, D2D1::Point2F(), p_.haleR, p_.haleR);
        parilti_ = radyal({{0, Rk(p_.ucRenk, 1)}, {1, Rk(p_.ucRenk, 0)}}, D2D1::Point2F(), 7, 2.2f);
        return firca_ && bOp4_ && bDurum_;
    }

    // t ms anındaki kare; ucA: ilerleme ucunun parıltısı (yalnız hareket ederken, 0–1).
    void Ciz(double t, double ucA) {
        ID2D1RenderTarget* rt = rt_;
        const Palet& P = p_;
        const double p = Ilerleme(t);
        const int adim = AdimNo(t);
        rt->SetTransform(D2D1::Matrix3x2F::Identity());
        rt->Clear(Rk(P.zemin));
        const D2D1_RECT_F tum = D2D1::RectF(0, 0, GEN, YUK);
        if (merkez_) rt->FillRectangle(tum, merkez_);
        if (vinyet_) rt->FillRectangle(tum, vinyet_);
        // iskele (eksen, üzengi, zemin), hayalet kontur, yay merkezi işareti
        const double iskeleSon = 1.0 - E3(Oran(t, 3700, 4200));
        const double buyu = E3(Oran(t, 80, 680));
        const float uzengiY = Simge(0, kontur::UZENGI_Y).y, zeminY = Simge(0, kontur::TABAN_Y).y;
        const float yariGen = kontur::DIS_R * OLCEK_SIMGE;
        if (iskeleSon > 0 && buyu > 0) {
            const float a = static_cast<float>(iskeleSon);
            const float y0 = KEMER_UST - 26, y1 = zeminY + 16;
            Cizgi(KEMER_CX, y0, KEMER_CX, static_cast<float>(y0 + (y1 - y0) * buyu), Rk(P.iskele, P.iskeleA * a), 0.75f, kesik_);
            const float u = static_cast<float>(buyu);
            Cizgi(KEMER_CX - (yariGen + 30) * u, uzengiY, KEMER_CX + (yariGen + 30) * u, uzengiY, Rk(P.iskele, P.uzengiA * a), 0.75f);
            Cizgi(KEMER_CX - (yariGen + 46) * u, zeminY, KEMER_CX + (yariGen + 46) * u, zeminY, Rk(P.iskele, P.iskeleA * a), 0.75f);
            const double hayalet = E3(Oran(t, 150, 750)) * iskeleSon;
            if (hayalet > 0)
                for (const kontur::Yol& y : kontur::HAYALETLER) Yol(y.p, y.n, Rk(P.iskele, P.hayaletA * static_cast<float>(hayalet)), 0.75f, kesik_);
            const double mk = Oran(t, 500, 800) * iskeleSon;
            if (mk > 0) {
                firca_->SetColor(Rk(P.iskele, P.merkezA * static_cast<float>(mk)));
                rt->DrawEllipse(D2D1::Ellipse(D2D1::Point2F(KEMER_CX, uzengiY), 3, 3), firca_, 0.75f);
            }
        }
        // kilit taşı ışığı ve halka (logonun ARKASINDA)
        const double isik = P.isikTepe * E3(Oran(t, 3820, 4060)) - (P.isikTepe - P.isikKalan) * E3(Oran(t, 4060, 5100));
        if (isik > 0.001 && isik_) {
            isik_->SetOpacity(static_cast<float>(isik));
            rt->FillRectangle(D2D1::RectF(156, 25, 380, 249), isik_);
        }
        const double hu = Oran(t, 3900, 4800);
        if (hu > 0 && hu < 1) Halka(28.0f + 122.0f * static_cast<float>(E3(hu)),
                                    static_cast<float>(P.halkaTepe * std::min(1.0, 6 * hu) * std::pow(1 - hu, 1.5)));
        // dolgu: kemer (Kahve) ve kilit taşı (Krem) katmanları
        const double dKemer = E3(Oran(t, T_HAZIR, T_HAZIR + 350));
        const double dKilit = E3(Oran(t, T_HAZIR + 150, T_HAZIR + 600));
        const float kilitDy = static_cast<float>(-12.0 * (1.0 - dKilit));
        const D2D1_POINT_2F sol = Simge(kontur::KUTU_X0, kontur::KUTU_Y0), sag = Simge(kontur::KUTU_X1, kontur::KUTU_Y1);
        const D2D1_RECT_F kaynak = D2D1::RectF(kontur::KUTU_X0, kontur::KUTU_Y0, kontur::KUTU_X1, kontur::KUTU_Y1);
        if (kemer_ && dKemer > 0)
            rt->DrawBitmap(kemer_, D2D1::RectF(sol.x, sol.y, sag.x, sag.y), static_cast<float>(dKemer), D2D1_BITMAP_INTERPOLATION_MODE_LINEAR, kaynak);
        if (kilit_ && dKilit > 0)
            rt->DrawBitmap(kilit_, D2D1::RectF(sol.x, sol.y + kilitDy, sag.x, sag.y + kilitDy), static_cast<float>(dKilit),
                           D2D1_BITMAP_INTERPOLATION_MODE_LINEAR, kaynak);
        // altın iz: dört kemer kalemi ayaklardan tepeye (ilerlemenin %86'sı), sonra dört kilit taşı kalemi
        const double izA = 1.0 - E3(Oran(t, 3750, 4150));
        if (izA > 0 && t >= ADIM_BAS[0]) {
            const double gKemer = std::min(1.0, p / KEMER_PAY), gKilit = K01((p - KEMER_PAY) / (1 - KEMER_PAY));
            const D2D1_COLOR_F iz = Rk(ALTIN, static_cast<float>(izA));
            // derzler: tamamlanan adım sınırlarında dış ve iç kalem arasında
            for (int k = 1; k < 5; ++k) {
                if (t < ADIM_BAS[k]) break;
                const double gb = ADIM_P[k] / KEMER_PAY;
                if (gb >= 1.0) break;
                const float a = static_cast<float>(P.derzA * izA * Oran(t, ADIM_BAS[k], ADIM_BAS[k] + 220));
                for (int y = 0; y < 2; ++y) {
                    const kontur::Kalem& dis = kontur::KALEMLER[y * 2], &ic = kontur::KALEMLER[y * 2 + 1];
                    const D2D1_POINT_2F a0 = KalemNoktasi(dis, gb), a1 = KalemNoktasi(ic, gb);
                    Cizgi(a0.x, a0.y, a1.x, a1.y, Rk(ALTIN, a), 0.75f);
                }
            }
            for (size_t i = 0; i < 8; ++i) {
                const kontur::Kalem& k = kontur::KALEMLER[i];
                const double g = i < 4 ? gKemer : gKilit;
                if (g <= 0) continue;
                KalemIzi(k, g, iz, P.izKalinlik);
                if (g < 1.0 && t < T_HAZIR + 220) {  // kalem ucu: nokta + hale
                    const D2D1_POINT_2F u = KalemNoktasi(k, g);
                    const float ua = static_cast<float>(1.0 - Oran(t, T_HAZIR, T_HAZIR + 220));
                    hale_->SetCenter(u);
                    hale_->SetOpacity(ua);
                    rt->FillEllipse(D2D1::Ellipse(u, P.haleR, P.haleR), hale_);
                    firca_->SetColor(Rk(P.ucNokta, ua));
                    rt->FillEllipse(D2D1::Ellipse(u, 1.6f, 1.6f), firca_);
                }
            }
        }
        // kilit taşı kenarı (açık sürüm): taşın üst ve alt kenarında kalıcı ince altın çizgi, taşla birlikte iner
        if (P.kilitKenari && dKilit > 0) {
            rt->SetTransform(D2D1::Matrix3x2F::Translation(0, kilitDy));
            for (size_t i = 4; i < 8; ++i) KalemIzi(kontur::KALEMLER[i], 1.0, Rk(ALTIN, 0.70f * static_cast<float>(dKilit)), 0.9f);
            rt->SetTransform(D2D1::Matrix3x2F::Identity());
        }
        // kurum yazısı (OPUS FORTİS): genişlik 232, x = 268'e ortalı, harf tabanı 418; 8 px yukarı kayarak belirir
        const double dYazi = E3(Oran(t, 4150, 4650));
        if (yazi_ && dYazi > 0) {
            const float kx0 = 98, ky0 = 86, kx1 = 1902, ky1 = 285, o = 232.0f / (kx1 - kx0);
            const float dy = static_cast<float>(8.0 * (1.0 - dYazi));
            rt->DrawBitmap(yazi_, D2D1::RectF(KEMER_CX - 116, 418 - (ky1 - ky0) * o + dy, KEMER_CX + 116, 418 + dy), static_cast<float>(dYazi),
                           D2D1_BITMAP_INTERPOLATION_MODE_LINEAR, D2D1::RectF(kx0, ky0, kx1, ky1));
        }
        // sağ sütun: op4, alt başlık, durum + yüzde, ilerleme çizgisi, alt bilgi (opaklık + 6 px yükselme)
        auto giris = [&](double a, double b) { return E3(Oran(t, a, b)); };
        const double g1 = giris(120, 620), g2 = giris(220, 720), g3 = giris(320, 820), g4 = giris(420, 920);
        Metin(L"op4", bOp4_, SAG_X, 236 + 6 * static_cast<float>(1 - g1), Rk(P.metin, static_cast<float>(g1)));
        Metin(Genis(Tr("Yapı analizi ve tasarımı")), bAlt_, SAG_X, 282 + 6 * static_cast<float>(1 - g2),
              Rk(P.metin, P.altBaslikA * static_cast<float>(g2)));
        const float dy3 = 6 * static_cast<float>(1 - g3);
        const bool hazir = adim >= 5;
        Metin(Genis(Tr(kDurum[adim])), bDurum_, SAG_X, 352 + dy3,
              Rk(hazir ? P.metin : P.durumRenk, (hazir ? P.hazirA : P.durumA) * static_cast<float>(g3)));
        wchar_t yuzde[16];
        swprintf(yuzde, 16, L"%%%d", static_cast<int>(std::lround(p * 100)));
        Metin(yuzde, bYuzde_, SAG_SON, 352 + dy3, Rk(ALTIN, static_cast<float>(g3)), true);
        // ilerleme çizgisi ("Gece" biçimi): iz, Altın dolgu, uçta açık geçiş ve parıltı (yalnız hareket ederken)
        const float iy = 368 + dy3, dolgu = static_cast<float>(p) * (SAG_SON - SAG_X);
        firca_->SetColor(Rk(P.izRenk, P.izA * static_cast<float>(g3)));
        rt->FillRectangle(D2D1::RectF(SAG_X, iy - 0.5f, SAG_SON, iy + 0.5f), firca_);
        firca_->SetColor(Rk(ALTIN, static_cast<float>(g3)));
        rt->FillRectangle(D2D1::RectF(SAG_X, iy - 0.5f, SAG_X + dolgu, iy + 0.5f), firca_);
        const float uA = static_cast<float>(ucA * g3 * (1.0 - Oran(t, T_HAZIR, T_HAZIR + 220)));
        if (uA > 0.01f && dolgu > 1) {
            const float u0 = std::max(SAG_X, SAG_X + dolgu - 48);
            for (int i = 0; i < 12; ++i) {  // son 48 px'te Altın → açık uç, t² ile
                const float a0 = u0 + (SAG_X + dolgu - u0) * i / 12.0f, a1 = u0 + (SAG_X + dolgu - u0) * (i + 1) / 12.0f;
                const float tt = (i + 0.5f) / 12.0f;
                firca_->SetColor(Rk(P.ucRenk, uA * tt * tt));
                rt->FillRectangle(D2D1::RectF(a0, iy - 0.5f, a1, iy + 0.5f), firca_);
            }
            parilti_->SetCenter(D2D1::Point2F(SAG_X + dolgu - 5, iy));
            parilti_->SetOpacity(P.parilti * uA);
            rt->FillEllipse(D2D1::Ellipse(D2D1::Point2F(SAG_X + dolgu - 5, iy), 7, 2.2f), parilti_);
        }
        const float dy4 = 6 * static_cast<float>(1 - g4);
        Metin(surum_, bAltBilgi_, SAG_X, 500 + dy4, Rk(P.altRenk, P.surumA * static_cast<float>(g4)));
        Metin(L"© 2026 Opus Fortis", bAltBilgi_, SAG_SON, 500 + dy4, Rk(P.altRenk, P.telifA * static_cast<float>(g4)), true);
        // pencere kenarı: içten 1 px
        firca_->SetColor(Rk(P.kenar, P.kenarA));
        rt->DrawRectangle(D2D1::RectF(0.5f, 0.5f, GEN - 0.5f, YUK - 0.5f), firca_, 1.0f);
    }

private:
    ID2D1Bitmap* Bitmap(const std::wstring& yol) {
        Resim r;
        std::string hata;
        if (!PngOku(yol, r, hata)) {
            Gunluk("Açılış: %s okunamadı (%s)", Utf8(yol).c_str(), hata.c_str());
            return nullptr;
        }
        ID2D1Bitmap* b = nullptr;
        const D2D1_BITMAP_PROPERTIES bp = D2D1::BitmapProperties(D2D1::PixelFormat(DXGI_FORMAT_B8G8R8A8_UNORM, D2D1_ALPHA_MODE_PREMULTIPLIED), 96, 96);
        rt_->CreateBitmap(D2D1::SizeU(static_cast<UINT32>(r.g), static_cast<UINT32>(r.y)), r.bgra.data(), static_cast<UINT32>(r.g * 4), bp, &b);
        return b;
    }
    void Cizgi(float x0, float y0, float x1, float y1, D2D1_COLOR_F renk, float k, ID2D1StrokeStyle* s = nullptr) {
        firca_->SetColor(renk);
        rt_->DrawLine(D2D1::Point2F(x0, y0), D2D1::Point2F(x1, y1), firca_, k, s ? s : yuvarlak_);
    }
    void Yol(const kontur::Nokta* p, size_t n, D2D1_COLOR_F renk, float k, ID2D1StrokeStyle* s) {
        ID2D1PathGeometry* g = nullptr;
        ID2D1GeometrySink* sk = nullptr;
        if (n < 2 || FAILED(f_.d2d->CreatePathGeometry(&g)) || FAILED(g->Open(&sk))) {
            Birak(g);
            return;
        }
        sk->BeginFigure(Simge(p[0].x, p[0].y), D2D1_FIGURE_BEGIN_HOLLOW);
        for (size_t i = 1; i < n; ++i) sk->AddLine(Simge(p[i].x, p[i].y));
        sk->EndFigure(D2D1_FIGURE_END_OPEN);
        sk->Close();
        Birak(sk);
        firca_->SetColor(renk);
        rt_->DrawGeometry(g, firca_, k, s);
        Birak(g);
    }
    static D2D1_POINT_2F KalemNoktasi(const kontur::Kalem& k, double g) {
        size_t i = 1;
        while (i < k.n && k.g[i] < g) ++i;
        if (i >= k.n) return Simge(k.p[k.n - 1].x, k.p[k.n - 1].y);
        const float u = static_cast<float>((g - k.g[i - 1]) / std::max(1e-9, static_cast<double>(k.g[i] - k.g[i - 1])));
        return Simge(k.p[i - 1].x + (k.p[i].x - k.p[i - 1].x) * u, k.p[i - 1].y + (k.p[i].y - k.p[i - 1].y) * u);
    }
    void KalemIzi(const kontur::Kalem& k, double g, D2D1_COLOR_F renk, float kalinlik) {
        ID2D1PathGeometry* geo = nullptr;
        ID2D1GeometrySink* sk = nullptr;
        if (FAILED(f_.d2d->CreatePathGeometry(&geo)) || FAILED(geo->Open(&sk))) {
            Birak(geo);
            return;
        }
        sk->BeginFigure(Simge(k.p[0].x, k.p[0].y), D2D1_FIGURE_BEGIN_HOLLOW);
        for (size_t i = 1; i < k.n; ++i) {
            if (k.g[i] >= g) {
                sk->AddLine(KalemNoktasi(k, g));
                break;
            }
            sk->AddLine(Simge(k.p[i].x, k.p[i].y));
        }
        sk->EndFigure(D2D1_FIGURE_END_OPEN);
        sk->Close();
        Birak(sk);
        firca_->SetColor(renk);
        rt_->DrawGeometry(geo, firca_, kalinlik, yuvarlak_);
        Birak(geo);
    }
    void Halka(float r, float opaklik) {
        if (opaklik <= 0.0005f) return;
        const float R = r + 26;
        std::vector<D2D1_GRADIENT_STOP> d;
        for (int i = 0; i <= 24; ++i) {
            const float u = i / 24.0f;
            const float c = 0.5f + 0.5f * static_cast<float>(std::cos(kPi * std::min(1.0f, std::fabs(u * R - r) / 26.0f)));
            d.push_back({u, Rk(ALTIN, c * c)});
        }
        ID2D1GradientStopCollection* k = nullptr;
        ID2D1RadialGradientBrush* b = nullptr;
        rt_->CreateGradientStopCollection(d.data(), static_cast<UINT32>(d.size()), D2D1_GAMMA_2_2, D2D1_EXTEND_MODE_CLAMP, &k);
        if (k) rt_->CreateRadialGradientBrush(D2D1::RadialGradientBrushProperties(D2D1::Point2F(268, 136.9f), D2D1::Point2F(), R, R), k, &b);
        if (b) {
            b->SetOpacity(opaklik);
            rt_->FillEllipse(D2D1::Ellipse(D2D1::Point2F(268, 136.9f), R, R), b);
        }
        Birak(b);
        Birak(k);
    }
    // Taban çizgisi y'de metin; sag = true ise x sağ kenardır.
    void Metin(const std::wstring& s, IDWriteTextFormat* b, float x, float taban, D2D1_COLOR_F renk, bool sag = false) {
        if (!b || renk.a <= 0.002f) return;
        IDWriteTextLayout* l = nullptr;
        if (FAILED(f_.dw->CreateTextLayout(s.c_str(), static_cast<UINT32>(s.size()), b, 2000, 400, &l))) return;
        DWRITE_LINE_METRICS lm{};
        UINT32 n = 0;
        l->GetLineMetrics(&lm, 1, &n);
        DWRITE_TEXT_METRICS tm{};
        l->GetMetrics(&tm);
        firca_->SetColor(renk);
        rt_->DrawTextLayout(D2D1::Point2F(sag ? x - tm.widthIncludingTrailingWhitespace : x, taban - lm.baseline), l, firca_,
                            D2D1_DRAW_TEXT_OPTIONS_NONE);
        Birak(l);
    }
    void Serbest() {
        for (ID2D1Bitmap** b : {&kemer_, &kilit_, &yazi_}) Birak(*b);
        for (IDWriteTextFormat** b : {&bOp4_, &bAlt_, &bDurum_, &bYuzde_, &bAltBilgi_}) Birak(*b);
        for (ID2D1RadialGradientBrush** b : {&merkez_, &vinyet_, &isik_, &hale_, &parilti_}) Birak(*b);
        Birak(firca_);
        Birak(yuvarlak_);
        Birak(kesik_);
    }

    Fabrikalar& f_;
    const Palet& p_;
    std::wstring surum_;
    ID2D1RenderTarget* rt_ = nullptr;
    ID2D1SolidColorBrush* firca_ = nullptr;
    ID2D1StrokeStyle *yuvarlak_ = nullptr, *kesik_ = nullptr;
    ID2D1Bitmap *kemer_ = nullptr, *kilit_ = nullptr, *yazi_ = nullptr;
    IDWriteTextFormat *bOp4_ = nullptr, *bAlt_ = nullptr, *bDurum_ = nullptr, *bYuzde_ = nullptr, *bAltBilgi_ = nullptr;
    ID2D1RadialGradientBrush *merkez_ = nullptr, *vinyet_ = nullptr, *isik_ = nullptr, *hale_ = nullptr, *parilti_ = nullptr;
};

// DIB + D2D DC hedefi (pencere: UpdateLayeredWindow; test: PNG).
struct Tuval {
    HDC dc = nullptr;
    HBITMAP bmp = nullptr;
    HGDIOBJ eski = nullptr;
    void* bitler = nullptr;
    int g = 0, y = 0;
    ID2D1DCRenderTarget* rt = nullptr;

    bool Kur(ID2D1Factory* f, int gen, int yuk, float olcek) {
        g = gen;
        y = yuk;
        BITMAPINFO bi{};
        bi.bmiHeader.biSize = sizeof(bi.bmiHeader);
        bi.bmiHeader.biWidth = g;
        bi.bmiHeader.biHeight = -y;
        bi.bmiHeader.biPlanes = 1;
        bi.bmiHeader.biBitCount = 32;
        bi.bmiHeader.biCompression = BI_RGB;
        dc = CreateCompatibleDC(nullptr);
        bmp = CreateDIBSection(dc, &bi, DIB_RGB_COLORS, &bitler, nullptr, 0);
        if (!dc || !bmp) return false;
        eski = SelectObject(dc, bmp);
        const D2D1_RENDER_TARGET_PROPERTIES rp = D2D1::RenderTargetProperties(
            D2D1_RENDER_TARGET_TYPE_DEFAULT, D2D1::PixelFormat(DXGI_FORMAT_B8G8R8A8_UNORM, D2D1_ALPHA_MODE_PREMULTIPLIED), 96 * olcek, 96 * olcek);
        if (FAILED(f->CreateDCRenderTarget(&rp, &rt))) return false;
        const RECT r{0, 0, g, y};
        return SUCCEEDED(rt->BindDC(dc, &r));
    }
    ~Tuval() {
        Birak(rt);
        if (dc && eski) SelectObject(dc, eski);
        if (bmp) DeleteObject(bmp);
        if (dc) DeleteDC(dc);
    }
};

}  // namespace

// ---- pencere ------------------------------------------------------------------------------------------------------------
struct AcilisEkrani::Ic {
    std::thread is;
    std::atomic<int> adim{0};          // gerçek adım (AcilisAdimi)
    std::atomic<float> motorOran{0};
    std::atomic<bool> kapat{false}, bitti{false};
    HINSTANCE ornek = nullptr;
    std::wstring dizin;
    std::string surum;
    bool koyu = false;

    void Calis() {
        HRESULT co = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        Fabrikalar f;
        std::string hata;
        if (!f.Kur(hata)) {
            Gunluk("Açılış ekranı çizilemiyor: %s", hata.c_str());
            bitti = true;
            if (SUCCEEDED(co)) CoUninitialize();
            return;
        }
        const float olcek = static_cast<float>(GetDpiForSystem()) / 96.0f;
        const int g = static_cast<int>(std::lround(GEN * olcek)), y = static_cast<int>(std::lround(YUK * olcek));
        WNDCLASSEXW wc{sizeof(wc)};
        wc.lpfnWndProc = DefWindowProcW;
        wc.hInstance = ornek;
        wc.hCursor = LoadCursorW(nullptr, IDC_APPSTARTING);
        wc.hIcon = LoadIconW(ornek, MAKEINTRESOURCEW(1));
        wc.lpszClassName = L"op4.Acilis";
        RegisterClassExW(&wc);
        POINT sifir{0, 0};
        MONITORINFO mi{sizeof(mi)};
        GetMonitorInfoW(MonitorFromPoint(sifir, MONITOR_DEFAULTTOPRIMARY), &mi);
        const int x = mi.rcWork.left + (mi.rcWork.right - mi.rcWork.left - g) / 2;
        const int yy = mi.rcWork.top + (mi.rcWork.bottom - mi.rcWork.top - y) / 2;
        HWND h = CreateWindowExW(WS_EX_LAYERED | WS_EX_TOOLWINDOW, wc.lpszClassName, L"op4", WS_POPUP, x, yy, g, y, nullptr, nullptr, ornek, nullptr);
        Tuval tv;
        KemerCizimi cizim(f, koyu ? kKoyu : kAcik, surum);
        if (!h || !tv.Kur(f.d2d, g, y, olcek) || !cizim.Kur(tv.rt, KimlikDizini(dizin))) {
            Gunluk("Açılış ekranı kurulamadı");
            if (h) DestroyWindow(h);
            bitti = true;
            if (SUCCEEDED(co)) CoUninitialize();
            return;
        }
        ShowWindow(h, SW_SHOWNOACTIVATE);
        // Görsel saat: gerçek adımın sonunu geçmez; gerçek adım öndeyse 2,5× hızla yetişir.
        double t = 0, oncekiP = 0, ucA = 0;
        LARGE_INTEGER fr, t0;
        QueryPerformanceFrequency(&fr);
        QueryPerformanceCounter(&t0);
        double son = 0;
        bool kapaniyor = false;
        double kapanisBasi = 0;
        for (;;) {
            LARGE_INTEGER s;
            QueryPerformanceCounter(&s);
            const double simdi = 1000.0 * static_cast<double>(s.QuadPart - t0.QuadPart) / static_cast<double>(fr.QuadPart);
            const double dt = std::min(100.0, simdi - son);
            son = simdi;
            const int a = std::clamp(adim.load(), 0, 5);
            double sinir = BITIS + 200;
            if (a < 5) {
                const double oran = a == static_cast<int>(AcilisAdimi::Motor) ? std::clamp(static_cast<double>(motorOran.load()), 0.0, 0.97) : 0.97;
                sinir = ADIM_BAS[a] + oran * (ADIM_BAS[a + 1] - ADIM_BAS[a]);
            }
            const double hiz = t < ADIM_BAS[a] ? 2.5 : 1.0;
            t = std::min(std::max(t, std::min(t + dt * hiz, sinir)), BITIS + 200);
            const double p = Ilerleme(t);
            const double hizP = dt > 0 ? (p - oncekiP) / (dt / 1000.0) : 0;  // ilerleme hızı (1/s)
            oncekiP = p;
            const double hedefUc = std::clamp(hizP / 0.08, 0.0, 1.0);
            ucA += (hedefUc - ucA) * (1.0 - std::exp(-dt / 150.0));
            if (t >= SON_KARE + 300) bitti = true;
            if (kapat && !kapaniyor) {
                kapaniyor = true;
                kapanisBasi = simdi;
            }
            const double gorunur = std::min(Oran(simdi, 0, 220), kapaniyor ? 1.0 - Oran(simdi, kapanisBasi, kapanisBasi + 160) : 1.0);
            tv.rt->BeginDraw();
            cizim.Ciz(t, ucA);
            tv.rt->EndDraw();
            HDC ekran = GetDC(nullptr);
            POINT konum{x, yy}, kaynak{0, 0};
            SIZE boy{g, y};
            BLENDFUNCTION bf{AC_SRC_OVER, 0, static_cast<BYTE>(std::lround(255 * gorunur)), AC_SRC_ALPHA};
            UpdateLayeredWindow(h, ekran, &konum, &boy, tv.dc, &kaynak, 0, &bf, ULW_ALPHA);
            ReleaseDC(nullptr, ekran);
            if (kapaniyor && gorunur <= 0.0) break;
            MSG m;
            while (PeekMessageW(&m, nullptr, 0, 0, PM_REMOVE)) {
                TranslateMessage(&m);
                DispatchMessageW(&m);
            }
            MsgWaitForMultipleObjects(0, nullptr, FALSE, 15, QS_ALLINPUT);
        }
        DestroyWindow(h);
        UnregisterClassW(wc.lpszClassName, ornek);
        bitti = true;
        if (SUCCEEDED(co)) CoUninitialize();
    }
};

AcilisEkrani::AcilisEkrani() = default;
AcilisEkrani::~AcilisEkrani() { Kapat(); }

void AcilisEkrani::Baslat(HINSTANCE ornek, const std::wstring& uygulamaDizini, const std::string& surum, bool koyu) {
    if (ic_) return;
    ic_ = std::make_unique<Ic>();
    ic_->ornek = ornek;
    ic_->dizin = uygulamaDizini;
    ic_->surum = surum;
    ic_->koyu = koyu;
    Ic* ic = ic_.get();
    ic_->is = std::thread([ic] { ic->Calis(); });
}

void AcilisEkrani::Adim(AcilisAdimi a) {
    if (!ic_) return;
    int eski = ic_->adim.load();
    while (static_cast<int>(a) > eski && !ic_->adim.compare_exchange_weak(eski, static_cast<int>(a))) {
    }
    if (a == AcilisAdimi::Motor) ic_->motorOran = 0;
}

void AcilisEkrani::AdimIlerleme(AcilisAdimi a, float oran) {
    if (!ic_) return;
    Adim(a);
    if (a == AcilisAdimi::Motor) ic_->motorOran = std::max(ic_->motorOran.load(), oran);
}

bool AcilisEkrani::Bitti() const { return !ic_ || ic_->bitti.load(); }

void AcilisEkrani::Kapat() {
    if (!ic_) return;
    ic_->kapat = true;
    if (ic_->is.joinable()) ic_->is.join();
    ic_.reset();
}

// ---- --test-acilis --------------------------------------------------------------------------------------------------------
bool AcilisResmi(const std::wstring& uygulamaDizini, const std::string& surum, const std::wstring& png, float olcek, double zamanMs,
                 bool koyu, std::string& hata) {
    const HRESULT co = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    bool tamam = false;
    {
        Fabrikalar f;
        if (f.Kur(hata)) {
            const int g = static_cast<int>(std::lround(GEN * olcek)), y = static_cast<int>(std::lround(YUK * olcek));
            Tuval tv;
            KemerCizimi cizim(f, koyu ? kKoyu : kAcik, surum);
            if (!tv.Kur(f.d2d, g, y, olcek) || !cizim.Kur(tv.rt, KimlikDizini(uygulamaDizini))) {
                hata = "Direct2D hedefi kurulamadı";
            } else {
                tv.rt->BeginDraw();
                const double hareket = zamanMs > ADIM_BAS[0] && zamanMs < T_HAZIR ? 1.0 : 0.0;
                cizim.Ciz(zamanMs, hareket);
                if (FAILED(tv.rt->EndDraw())) {
                    hata = "EndDraw başarısız";
                } else {
                    GdiFlush();
                    tamam = PngYaz(png, g, y, static_cast<const uint8_t*>(tv.bitler), true, hata);
                }
            }
        }
    }
    if (SUCCEEDED(co)) CoUninitialize();
    return tamam;
}

}  // namespace op4
