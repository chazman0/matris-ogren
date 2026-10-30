#include "acilis.h"

#include <dwmapi.h>

#include <algorithm>
#include <cmath>
#include <cstring>

#include "gunluk.h"

namespace op4 {
namespace {

constexpr wchar_t kSinif[] = L"op4.Acilis";
constexpr UINT WM_ILERLEME = WM_APP + 1;
// Opus Fortis paleti (kimlik/README.md).
const COLORREF kAntrasit = RGB(0x14, 0x18, 0x1B);
const COLORREF kKahve = RGB(0x8A, 0x6B, 0x3C);
const COLORREF kAltin = RGB(0xB0, 0x89, 0x50);
const COLORREF kKrem = RGB(0xED, 0xE6, 0xD8);

bool DosyaVar(const std::wstring& yol) {
    DWORD a = GetFileAttributesW(yol.c_str());
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

HFONT Yazi(int boy, int kalinlik) {
    return CreateFontW(-boy, 0, 0, 0, kalinlik, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_TT_PRECIS, CLIP_DEFAULT_PRECIS,
                       CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Segoe UI");
}

void Dikdortgen(HDC dc, int x0, int y0, int x1, int y1, COLORREF c) {
    RECT r{x0, y0, x1, y1};
    HBRUSH f = CreateSolidBrush(c);
    FillRect(dc, &r, f);
    DeleteObject(f);
}

void Metin(HDC dc, const std::wstring& s, RECT r, int boy, int kalinlik, COLORREF c, UINT bicim) {
    HFONT f = Yazi(boy, kalinlik);
    HGDIOBJ eski = SelectObject(dc, f);
    SetTextColor(dc, c);
    SetBkMode(dc, TRANSPARENT);
    DrawTextW(dc, s.c_str(), static_cast<int>(s.size()), &r, bicim | DT_NOPREFIX | DT_SINGLELINE);
    SelectObject(dc, eski);
    DeleteObject(f);
}

// Logo yuvası: g × y kutusuna en-boy oranını koruyarak sığacak boyut.
void Sigdir(int kg, int ky, int g, int y, int& og, int& oy) {
    double o = std::min(static_cast<double>(g) / kg, static_cast<double>(y) / ky);
    og = std::max(1, static_cast<int>(std::lround(kg * o)));
    oy = std::max(1, static_cast<int>(std::lround(ky * o)));
}

}  // namespace

std::wstring AcilisEkrani::LogoYolu(const std::wstring& dizin) {
    // Öncelik: kimlik\logo.png (elle konan) → kurumsal yatay logo (açık zemin) → yer tutucu.
    for (const wchar_t* ad : {L"logo.png", L"opus-fortis-yatay-acik-zemin.png"}) {
        std::wstring yol = dizin + L"\\kimlik\\" + ad;
        if (DosyaVar(yol)) return yol;
    }
    return dizin + L"\\kimlik\\opus_fortis_logo_placeholder.png";
}

void AcilisEkrani::Ciz(HDC dc, int g, int y, float s, const Resim* logo, const std::wstring& surum,
                       const std::wstring& metin, float oran) {
    auto P = [s](float v) { return static_cast<int>(std::lround(v * s)); };
    Dikdortgen(dc, 0, 0, g, y, RGB(255, 255, 255));
    // Logo alanı (üst bölüm).
    const int bantY = y - P(78);
    RECT logoKutusu{P(40), P(28), g - P(40), P(28) + P(LOGO_Y)};
    if (logo && logo->g > 0) {
        int og = logo->g, oy = logo->y;  // logo zaten hedef boyuta ölçeklenmiş olarak gelir
        int x = (logoKutusu.left + logoKutusu.right - og) / 2;
        int yy = (logoKutusu.top + logoKutusu.bottom - oy) / 2;
        BITMAPINFO bi{};
        bi.bmiHeader.biSize = sizeof(bi.bmiHeader);
        bi.bmiHeader.biWidth = og;
        bi.bmiHeader.biHeight = -oy;  // üstten alta
        bi.bmiHeader.biPlanes = 1;
        bi.bmiHeader.biBitCount = 32;
        bi.bmiHeader.biCompression = BI_RGB;
        void* bitler = nullptr;
        HDC bdc = CreateCompatibleDC(dc);
        HBITMAP bmp = CreateDIBSection(dc, &bi, DIB_RGB_COLORS, &bitler, nullptr, 0);
        if (bmp && bitler) {
            std::memcpy(bitler, logo->bgra.data(), logo->bgra.size());
            HGDIOBJ eski = SelectObject(bdc, bmp);
            BLENDFUNCTION bf{AC_SRC_OVER, 0, 255, AC_SRC_ALPHA};
            AlphaBlend(dc, x, yy, og, oy, bdc, 0, 0, og, oy, bf);
            SelectObject(bdc, eski);
        }
        if (bmp) DeleteObject(bmp);
        DeleteDC(bdc);
    } else {
        Metin(dc, L"OPUS FORTİS", logoKutusu, P(44), FW_BOLD, kAntrasit, DT_CENTER | DT_VCENTER);
    }
    // Ürün adı ve alt başlık.
    Dikdortgen(dc, g / 2 - P(28), P(200), g / 2 + P(28), P(202), kAltin);  // ince altın ayraç
    RECT ad{P(40), P(204), g - P(40), P(254)};
    Metin(dc, L"op4", ad, P(44), FW_SEMIBOLD, kAntrasit, DT_CENTER | DT_VCENTER);
    RECT alt{P(40), P(254), g - P(40), P(280)};
    Metin(dc, L"Yapısal modelleme, analiz ve tasarım", alt, P(16), FW_NORMAL, kKahve, DT_CENTER | DT_VCENTER);
    // Alt bant: ilerleme.
    Dikdortgen(dc, 0, bantY, g, y, kAntrasit);
    RECT im{P(24), bantY + P(14), g - P(24), bantY + P(38)};
    Metin(dc, metin, im, P(15), FW_NORMAL, kKrem, DT_LEFT | DT_VCENTER | DT_END_ELLIPSIS);
    const int cy = bantY + P(46);
    Dikdortgen(dc, P(24), cy, g - P(24), cy + P(4), RGB(0x34, 0x30, 0x2A));
    int dolu = P(24) + static_cast<int>(std::lround((g - P(48)) * std::clamp(oran, 0.0f, 1.0f)));
    Dikdortgen(dc, P(24), cy, dolu, cy + P(4), kAltin);
    RECT sr{P(24), cy + P(8), g - P(24), y - P(4)};
    Metin(dc, surum, sr, P(12), FW_NORMAL, RGB(0x9A, 0x93, 0x86), DT_RIGHT | DT_VCENTER);
    Metin(dc, L"© Opus Fortis", sr, P(12), FW_NORMAL, RGB(0x9A, 0x93, 0x86), DT_LEFT | DT_VCENTER);
}

LRESULT CALLBACK AcilisEkrani::Yordam(HWND h, UINT m, WPARAM w, LPARAM l) {
    auto* a = reinterpret_cast<AcilisEkrani*>(GetWindowLongPtrW(h, GWLP_USERDATA));
    switch (m) {
        case WM_NCCREATE: {
            auto* cs = reinterpret_cast<CREATESTRUCTW*>(l);
            SetWindowLongPtrW(h, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(cs->lpCreateParams));
            break;
        }
        case WM_ILERLEME:
            InvalidateRect(h, nullptr, FALSE);
            return 0;
        case WM_ERASEBKGND:
            return 1;
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC dc = BeginPaint(h, &ps);
            RECT r;
            GetClientRect(h, &r);
            // Çift tamponlu çizim (titremesiz).
            HDC mdc = CreateCompatibleDC(dc);
            HBITMAP bmp = CreateCompatibleBitmap(dc, r.right, r.bottom);
            HGDIOBJ eski = SelectObject(mdc, bmp);
            if (a) {
                std::wstring metin;
                float oran;
                {
                    std::lock_guard<std::mutex> k(a->kilit_);
                    metin = a->metin_;
                    oran = a->oran_;
                }
                Ciz(mdc, r.right, r.bottom, a->olcek_, a->logoVar_ ? &a->logo_ : nullptr, a->surum_, metin, oran);
            }
            BitBlt(dc, 0, 0, r.right, r.bottom, mdc, 0, 0, SRCCOPY);
            SelectObject(mdc, eski);
            DeleteObject(bmp);
            DeleteDC(mdc);
            EndPaint(h, &ps);
            return 0;
        }
        case WM_NCHITTEST:
            return HTCAPTION;  // sürüklenebilir
    }
    return DefWindowProcW(h, m, w, l);
}

bool AcilisEkrani::Olustur(HINSTANCE ornek, const std::wstring& dizin, const std::wstring& surum) {
    surum_ = surum;
    WNDCLASSEXW wc{sizeof(wc)};
    wc.style = CS_DROPSHADOW;
    wc.lpfnWndProc = Yordam;
    wc.hInstance = ornek;
    wc.hCursor = LoadCursorW(nullptr, IDC_APPSTARTING);
    wc.hIcon = LoadIconW(ornek, MAKEINTRESOURCEW(1));
    wc.lpszClassName = kSinif;
    RegisterClassExW(&wc);

    // Birincil ekranın çalışma alanının ortası; DPI ölçeği o ekranın.
    POINT p{0, 0};
    HMONITOR mon = MonitorFromPoint(p, MONITOR_DEFAULTTOPRIMARY);
    MONITORINFO mi{sizeof(mi)};
    GetMonitorInfoW(mon, &mi);
    UINT dpi = 96;
    {
        HDC ekran = GetDC(nullptr);
        dpi = static_cast<UINT>(GetDeviceCaps(ekran, LOGPIXELSX));
        ReleaseDC(nullptr, ekran);
    }
    using GetDpiForMonitorF = HRESULT(WINAPI*)(HMONITOR, int, UINT*, UINT*);
    if (HMODULE shcore = LoadLibraryW(L"shcore.dll")) {
        if (auto f = reinterpret_cast<GetDpiForMonitorF>(reinterpret_cast<void*>(GetProcAddress(shcore, "GetDpiForMonitor")))) {
            UINT dx = 96, dy = 96;
            if (SUCCEEDED(f(mon, 0, &dx, &dy))) dpi = dx;
        }
    }
    olcek_ = static_cast<float>(dpi) / 96.0f;
    const int g = static_cast<int>(std::lround(TABAN_G * olcek_)), y = static_cast<int>(std::lround(TABAN_Y * olcek_));
    const RECT& c = mi.rcWork;
    const int x = c.left + (c.right - c.left - g) / 2, yy = c.top + (c.bottom - c.top - y) / 2;

    // Logo: yuvaya (genişlik g − 80, yükseklik LOGO_Y taban piksel) sığacak boyutta, yüksek kaliteli ölçekleme.
    std::wstring logoYolu = LogoYolu(dizin);
    int lg = 0, ly = 0;
    if (PngBoyutu(logoYolu, lg, ly)) {
        int og, oy;
        Sigdir(lg, ly, g - static_cast<int>(std::lround(80 * olcek_)), static_cast<int>(std::lround(AcilisEkrani::LOGO_Y * olcek_)), og, oy);
        std::string hata;
        logoVar_ = PngOku(logoYolu, logo_, hata, og, oy);
        if (!logoVar_) Gunluk("Açılış: logo okunamadı (%s): %s", Utf8(logoYolu).c_str(), hata.c_str());
    } else {
        Gunluk("Açılış: logo bulunamadı: %s", Utf8(logoYolu).c_str());
    }

    hwnd_ = CreateWindowExW(WS_EX_TOOLWINDOW | WS_EX_TOPMOST, kSinif, L"op4", WS_POPUP, x, yy, g, y, nullptr, nullptr,
                            ornek, this);
    if (!hwnd_) return false;
    // Windows 11: yuvarlatılmış köşeler.
    DWORD kose = 2;  // DWMWCP_ROUND
    DwmSetWindowAttribute(hwnd_, 33 /* DWMWA_WINDOW_CORNER_PREFERENCE */, &kose, sizeof(kose));
    ShowWindow(hwnd_, SW_SHOWNORMAL);
    UpdateWindow(hwnd_);
    return true;
}

void AcilisEkrani::Ilerleme(const std::string& metin, float oran) {
    {
        std::lock_guard<std::mutex> k(kilit_);
        metin_ = Genis(metin);
        oran_ = std::max(oran_, oran);
    }
    if (hwnd_) PostMessageW(hwnd_, WM_ILERLEME, 0, 0);
}

void AcilisEkrani::Kapat() {
    if (hwnd_) DestroyWindow(hwnd_);
    hwnd_ = nullptr;
}

bool AcilisResmi(const std::wstring& dizin, const std::wstring& surum, const std::wstring& png, float olcek,
                 std::string& hata) {
    const int g = static_cast<int>(std::lround(AcilisEkrani::TABAN_G * olcek));
    const int y = static_cast<int>(std::lround(AcilisEkrani::TABAN_Y * olcek));
    Resim logo;
    bool logoVar = false;
    std::wstring logoYolu = AcilisEkrani::LogoYolu(dizin);
    int lg = 0, ly = 0;
    if (PngBoyutu(logoYolu, lg, ly)) {
        int og, oy;
        Sigdir(lg, ly, g - static_cast<int>(std::lround(80 * olcek)), static_cast<int>(std::lround(AcilisEkrani::LOGO_Y * olcek)), og, oy);
        logoVar = PngOku(logoYolu, logo, hata, og, oy);
    }
    Gunluk("Açılış resmi: logo %s (%s)", logoVar ? "yüklendi" : "YOK", Utf8(logoYolu).c_str());
    BITMAPINFO bi{};
    bi.bmiHeader.biSize = sizeof(bi.bmiHeader);
    bi.bmiHeader.biWidth = g;
    bi.bmiHeader.biHeight = -y;
    bi.bmiHeader.biPlanes = 1;
    bi.bmiHeader.biBitCount = 32;
    bi.bmiHeader.biCompression = BI_RGB;
    void* bitler = nullptr;
    HDC dc = CreateCompatibleDC(nullptr);
    HBITMAP bmp = CreateDIBSection(dc, &bi, DIB_RGB_COLORS, &bitler, nullptr, 0);
    if (!bmp || !bitler) {
        hata = "DIB oluşturulamadı";
        DeleteDC(dc);
        return false;
    }
    HGDIOBJ eski = SelectObject(dc, bmp);
    AcilisEkrani::Ciz(dc, g, y, olcek, logoVar ? &logo : nullptr, surum,
                      L"Hesap motoru yükleniyor (numpy, sympy, web_kopru)…", 0.62f);
    GdiFlush();
    bool tamam = PngYaz(png, g, y, static_cast<const uint8_t*>(bitler), true, hata);
    SelectObject(dc, eski);
    DeleteObject(bmp);
    DeleteDC(dc);
    return tamam;
}

}  // namespace op4
