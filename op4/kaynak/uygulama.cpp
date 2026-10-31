// op4 — uygulama: açılış ekranı → ana pencere (Win32 özel krom + DirectX 12 + Dear ImGui) → döngü; --test-pencere bu
// yoldan çalışır. Sahibi: C (arayuz-goruntu). Arayüz kaynak/arayuz/ana_pencere.* (Atölye yerleşimi); sözleşme nesneleri ve
// paket modülleri UygulamaKabugu'ndadır (cekirdek/kabuk.h; C'nin modülü AnaPencere'yi kurar).
#include <windows.h>
#include <dwmapi.h>
#include <windowsx.h>

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#include "acilis.h"
#include "arayuz/ana_pencere.h"
#include "arayuz/dil.h"
#include "arayuz/stil.h"
#include "arayuz/yazi.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/kabuk.h"
#include "cekirdek/motor_hizmeti.h"
#include "grafik.h"
#include "grafik/sahne_agi.h"
#include "gunluk.h"
#include "imgui.h"
#include "imgui_impl_dx12.h"
#include "imgui_impl_win32.h"
#include "imgui_internal.h"
#include "platform/dosya_sistemi.h"
#include "resim.h"
#include "test_kipleri.h"

extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

// Hibrit grafikli dizüstülerde yüksek başarımlı GPU tercihi (MIMARI §6.1, D26; kabul C8).
extern "C" {
__declspec(dllexport) DWORD NvOptimusEnablement = 0x00000001;
__declspec(dllexport) int AmdPowerXpressRequestHighPerformance = 1;
}

namespace op4 {

const Yazilar& ArayuzYazilari();  // test_ekran.cpp (ImGuiBaglamiKur)

namespace {

class Uygulama {
public:
    int Calistir(HINSTANCE ornek, const Secenekler& s);
    LRESULT Yordam(HWND h, UINT m, WPARAM w, LPARAM l);

private:
    void Kare();
    void SahneAgiGuncelle();
    void TestAdimi();
    void TestOlc();
    void LogoYukle();
    CizimAyari Cizim() const;

    HWND hwnd_ = nullptr;
    Grafik grafik_;
    UygulamaKabugu kabuk_;
    AnaPencere* ana_ = nullptr;
    bool imgui_ = false, kareIcinde_ = false, ozelKrom_ = true;
    float olcek_ = 1.0f;
    bool olcekDegisti_ = false;
    std::string iniYolu_;
    uint64_t sonSahne_ = ~0ull, sonVurgu_ = ~0ull;
    bool sonKati_ = false;
    ImTextureData logo_;
    // --test-pencere
    int testSaniye_ = 0;
    long long kare_ = 0;
    double kareToplamMs_ = 0, kareEnBuyukMs_ = 0;
    struct {
        V3d p;
        bool pan = false, yakin = false;
        float mx = 0, my = 0;
        double panHata = 0, yakinHata = -1, sapma0 = 0, donme = 0;
        int panOlcum = 0;
    } betik_;
};

Uygulama* g_uygulama = nullptr;

LRESULT CALLBACK PencereYordami(HWND h, UINT m, WPARAM w, LPARAM l) {
    return g_uygulama ? g_uygulama->Yordam(h, m, w, l) : DefWindowProcW(h, m, w, l);
}

LRESULT Uygulama::Yordam(HWND h, UINT m, WPARAM w, LPARAM l) {
    if (imgui_ && ImGui_ImplWin32_WndProcHandler(h, m, w, l)) return true;
    switch (m) {
        case WM_NCCALCSIZE:
            if (ozelKrom_ && w == TRUE) {
                // İstemci alanı bütün pencere (başlık çubuğunu arayüz çizer); büyütülmüşken çerçeve kalınlığı kadar içeri.
                auto* p = reinterpret_cast<NCCALCSIZE_PARAMS*>(l);
                if (IsZoomed(h)) {
                    const UINT dpi = GetDpiForWindow(h);
                    const int c = GetSystemMetricsForDpi(SM_CXFRAME, dpi) + GetSystemMetricsForDpi(SM_CXPADDEDBORDER, dpi);
                    p->rgrc[0].left += c;
                    p->rgrc[0].right -= c;
                    p->rgrc[0].top += c;
                    p->rgrc[0].bottom -= c;
                }
                return 0;
            }
            break;
        case WM_NCHITTEST:
            if (ozelKrom_) {
                POINT pt{GET_X_LPARAM(l), GET_Y_LPARAM(l)};
                RECT r;
                GetWindowRect(h, &r);
                const int k = static_cast<int>(6 * olcek_);
                if (!IsZoomed(h)) {
                    const bool sol = pt.x < r.left + k, sag = pt.x >= r.right - k, ust = pt.y < r.top + k, alt = pt.y >= r.bottom - k;
                    if (ust && sol) return HTTOPLEFT;
                    if (ust && sag) return HTTOPRIGHT;
                    if (alt && sol) return HTBOTTOMLEFT;
                    if (alt && sag) return HTBOTTOMRIGHT;
                    if (sol) return HTLEFT;
                    if (sag) return HTRIGHT;
                    if (ust) return HTTOP;
                    if (alt) return HTBOTTOM;
                }
                ScreenToClient(h, &pt);
                if (ana_ && ana_->IsabetTesti(static_cast<float>(pt.x), static_cast<float>(pt.y)) == 1) return HTCAPTION;
                return HTCLIENT;
            }
            break;
        case WM_SIZE:
            if (w != SIZE_MINIMIZED && hwnd_) {
                grafik_.BoyutDegistir(LOWORD(l), HIWORD(l));
                if (imgui_ && !kareIcinde_) Kare();  // boyutlandırma sırasında da canlı çiz
            }
            return 0;
        case WM_DPICHANGED: {
            const RECT* r = reinterpret_cast<const RECT*>(l);
            olcek_ = static_cast<float>(HIWORD(w)) / 96.0f;
            olcekDegisti_ = true;
            SetWindowPos(h, nullptr, r->left, r->top, r->right - r->left, r->bottom - r->top, SWP_NOZORDER | SWP_NOACTIVATE);
            return 0;
        }
        case WM_GETMINMAXINFO:
            reinterpret_cast<MINMAXINFO*>(l)->ptMinTrackSize = {960, 600};
            return 0;
        case WM_SYSCOMMAND:
            if ((w & 0xfff0) == SC_KEYMENU) return 0;  // Alt menü tuşu ImGui'ye kalsın
            break;
        case WM_CLOSE:
            if (kabuk_.H().kapatmaOnayi && !kabuk_.H().kapatmaOnayi()) return 0;
            break;
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(h, m, w, l);
}

CizimAyari Uygulama::Cizim() const {
    CizimAyari a;
    a.kati = ana_ && ana_->KesitGorunumu();
    a.izgara = !ana_ || ana_->IzgaraGorunur();
    a.kenarlar = !kabuk_.gorunum.kenarlar ? false : true;
    a.ust = tema::Etkin().r.sahneUst;
    a.alt = tema::Etkin().r.sahneAlt;
    return a;
}

void Uygulama::SahneAgiGuncelle() {
    if (!ana_ || !ana_->KesitGorunumu()) {
        sonKati_ = false;
        return;
    }
    const SahnePtr& s = ana_->Sahne();
    if (sonKati_ && s->surum == sonSahne_ && ana_->VurguSurumu() == sonVurgu_) return;
    sonKati_ = true;
    sonSahne_ = s->surum;
    sonVurgu_ = ana_->VurguSurumu();
    SahneAgiAyari a;
    a.secim = &kabuk_.secim.Liste();
    a.uzerinde = ana_->Uzerinde();
    a.yalnizSecili = ana_->YalnizSecili();
    const double t0 = GecenMs();
    std::string hata;
    const Ag ag = SahneAgiKur(*s, a);
    if (!grafik_.SahneYukle(ag, hata)) Gunluk("HATA: %s", hata.c_str());
    if (kabuk_.H().bilgi.testKipi) Gunluk("Sahne ağı: %zu üçgen, %zu parça (%.1f ms)", ag.indisler.size() / 3, ag.parcalar.size(), GecenMs() - t0);
}

void Uygulama::LogoYukle() {
    // Başlıktaki kemer simgesi: kimlik/opus-fortis-simge-koyu.png → ImGui kullanıcı dokusu (arka uç oluşturur).
    const std::wstring yol = UygulamaDizini() + L"\\kimlik\\opus-fortis-simge-koyu.png";
    Resim r;
    std::string hata;
    const int hy = static_cast<int>(std::lround(32 * olcek_));
    int g = 0, y = 0;
    if (!PngBoyutu(yol, g, y) || y <= 0) return;
    const int hg = std::max(1, static_cast<int>(std::lround(static_cast<double>(hy) * g / y)));
    if (!PngOku(yol, r, hata, hg, hy)) return;
    logo_.Create(ImTextureFormat_RGBA32, r.g, r.y);
    unsigned char* p = static_cast<unsigned char*>(logo_.GetPixels());
    for (int i = 0; i < r.g * r.y; ++i) {  // PBGRA (önceden çarpılmış) → RGBA (düz alfa)
        const uint8_t b = r.bgra[i * 4], gg = r.bgra[i * 4 + 1], rr = r.bgra[i * 4 + 2], a = r.bgra[i * 4 + 3];
        auto duz = [a](uint8_t c) { return static_cast<unsigned char>(a ? std::min(255, c * 255 / a) : 0); };
        p[i * 4] = duz(rr);
        p[i * 4 + 1] = duz(gg);
        p[i * 4 + 2] = duz(b);
        p[i * 4 + 3] = a;
    }
    ImGui::RegisterUserTexture(&logo_);
    if (ana_) ana_->logoEnBoy = static_cast<float>(r.g) / static_cast<float>(r.y);
}

void Uygulama::TestAdimi() {
    // Betikli girdi (--test-pencere): görüş alanının sol alt bölgesinde (yüzen öğelerden uzak) kaydırma, döndürme,
    // yakınlaşma. ImGui girdi kuyruğu konumu düğmeden önce işler; betik konumu her karede kuyruğa eklenir.
    ImGuiIO& io = ImGui::GetIO();
    const GorusDikdortgeni g = ana_->Gorus();
    const long long n = kare_;
    if (n == 20 || n == 70) {
        betik_.mx = std::floor(g.x + g.g * 0.30f);
        betik_.my = std::floor(g.y + g.y2 * 0.68f);
    } else if (n > 21 && n <= 61) {
        betik_.mx += 3.0f;
        betik_.my += 1.0f;
    } else if (n > 71 && n <= 111) {
        betik_.mx += 4.0f;
    } else if (n == 120) {
        betik_.mx = std::floor(g.x + g.g * 0.35f);
        betik_.my = std::floor(g.y + g.y2 * 0.62f);
    }
    if (n >= 20) io.AddMousePosEvent(betik_.mx, betik_.my);
    if (n == 21) {
        betik_.p = CalismaDuzlemiNoktasi(ana_->Kamera(), betik_.mx - g.x, betik_.my - g.y, g.g, g.y2, 0.0);
        betik_.pan = true;
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, true);
    } else if (n == 62) {
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, false);
        betik_.pan = false;
    } else if (n == 70) {
        io.AddKeyEvent(ImGuiMod_Shift, true);
        betik_.sapma0 = ana_->Kamera().d.sapma;
    } else if (n == 71) {
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, true);
    } else if (n == 112) {
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, false);
    } else if (n == 114) {
        io.AddKeyEvent(ImGuiMod_Shift, false);
        betik_.donme = ana_->Kamera().d.sapma - betik_.sapma0;
    } else if (n == 122) {
        betik_.p = CalismaDuzlemiNoktasi(ana_->Kamera(), betik_.mx - g.x, betik_.my - g.y, g.g, g.y2, 0.0);
        betik_.yakin = true;
        io.AddMouseWheelEvent(0.0f, 2.0f);
    }
}

void Uygulama::TestOlc() {
    const GorusDikdortgeni g = ana_->Gorus();
    const GorusIzdusumu iz = ana_->Izdusum();
    double sx = 0, sy = 0;
    const ImVec2 m = ImGui::GetIO().MousePos;
    if (betik_.pan && kare_ > 26 && ana_->GezinmeDurumu().Surukluyor() && iz.Izdusur(betik_.p, sx, sy)) {
        betik_.panHata = std::max(betik_.panHata, std::hypot(sx + g.x - m.x, sy + g.y - m.y));
        ++betik_.panOlcum;
    }
    if (betik_.yakin && kare_ == 125 && iz.Izdusur(betik_.p, sx, sy))
        betik_.yakinHata = std::hypot(sx + g.x - betik_.mx, sy + g.y - betik_.my);
}

void Uygulama::Kare() {
    if (kareIcinde_ || !ana_) return;
    kareIcinde_ = true;
    const double kareBasi = GecenMs();
    if (olcekDegisti_) {
        ArayuzStiliUygula(olcek_);
        olcekDegisti_ = false;
    }
    kabuk_.H().KareIsleriniCalistir(GecenMs());
    ImGui_ImplDX12_NewFrame();
    ImGui_ImplWin32_NewFrame();
    if (testSaniye_ > 0) TestAdimi();
    ImGui::NewFrame();
    const GorusDikdortgeni g0 = ana_->Gorus();
    SahneDokusu d;
    d.kimlik = static_cast<ImTextureID>(grafik_.SahneDokusu());
    d.uvG = grafik_.UvG(g0.g);
    d.uvY = grafik_.UvY(g0.y2);
    ana_->KareCiz(olcek_, d, GecenMs());
    ImGui::Render();
    SahneAgiGuncelle();
    const GorusDikdortgeni g = ana_->Gorus();
    grafik_.PencereKaresi(ana_->Kamera(), Cizim(), GorusAlani{g.x, g.y, g.g, g.y2}, ImGui::GetDrawData(), tema::Etkin().r.zemin,
                          testSaniye_ > 0 || kabuk_.ayarlar.grafik.dikeyEsitleme);
    ana_->CizimYapildi();
    kabuk_.gorunum.CizimYapildi();
    if (testSaniye_ > 0) TestOlc();
    const double sure = GecenMs() - kareBasi;
    ++kare_;
    kareToplamMs_ += sure;
    kareEnBuyukMs_ = std::max(kareEnBuyukMs_, kare_ > 3 ? sure : 0.0);
    kareIcinde_ = false;
}

int Uygulama::Calistir(HINSTANCE ornek, const Secenekler& s) {
    g_uygulama = this;
    testSaniye_ = s.testPencere;
    if (testSaniye_ > 0) TestKipi(static_cast<unsigned>(testSaniye_) + 240);
    ImGui_ImplWin32_EnableDpiAwareness();
    const std::wstring dizin = UygulamaDizini();
    Gunluk("op4 %s başlıyor; dizin: %s", OP4_SURUM, Utf8(dizin).c_str());
    wchar_t ortam[8] = {};
    ozelKrom_ = GetEnvironmentVariableW(L"OP4_STANDART_PENCERE", ortam, 8) == 0;

    // Sözleşme kabuğu: ayarlar, komut kataloğu, paket modülleri (A motor, B çekirdek, C arayüz, D dosya ve çözüm).
    {
        const KullaniciDizinleri kd = KullaniciDizinleriniBul(false);
        KabukAyari ka;
        ka.bilgi.surum = OP4_SURUM;
        ka.bilgi.uygulamaDizini = Utf8(dizin);
        ka.bilgi.veriDizini = Utf8(VeriDizini());
        ka.bilgi.ayarDizini = kd.ayarlar;
        ka.bilgi.yerelDizin = kd.yerel;
        ka.bilgi.testKipi = testSaniye_ > 0;
        ka.ortam.anaPencere = [this]() -> void* { return hwnd_; };
        ka.ortam.testKipi = testSaniye_ > 0;
        ka.ortam.motorsuz = s.motorsuz;
        ka.ortam.acilisDosyasi = Utf8(s.proje);
        ka.ortam.senaryo = Utf8(s.senaryo);
        ka.ortam.gunluk = [](std::string_view m) { Gunluk("%.*s", static_cast<int>(m.size()), m.data()); };
        ka.moduller = StandartModuller();
        std::string kh;
        if (!kabuk_.Kur(std::move(ka), kh)) Gunluk("Uyarı: %s", kh.c_str());
        ana_ = EtkinAnaPencere();
    }
    if (!ana_) {
        Gunluk("HATA: arayüz modülü kurulmadı");
        return 2;
    }

    // Açılış ekranı ("Kemer Çizgisi"; Direct2D + DirectWrite, ayrı iş parçacığı). Adımlar gerçek yükleme olaylarından.
    AcilisEkrani acilis;
    const bool acilisVar = !s.acilisYok;
    if (acilisVar) acilis.Baslat(ornek, dizin, Utf8(L"Sürüm " OP4_SURUM), kabuk_.ayarlar.arayuz.acilisEkrani == "koyu");
    acilis.Adim(AcilisAdimi::Arayuz);
    MotorHizmeti* motor = kabuk_.H().motor;
    if (motor && !s.motorsuz) {
        motor->durumBildirimi = [&acilis](MotorRolu, const std::string&, float o) { acilis.AdimIlerleme(AcilisAdimi::Motor, o); };
        MotorAyari ma;
        ma.uygulamaDizini = Utf8(dizin);
        ma.gunlukDizini = kabuk_.H().bilgi.yerelDizin + "\\gunluk";
        motor->Baslat(ma);
    }
    acilis.Adim(AcilisAdimi::Grafik);

    WNDCLASSEXW wc{sizeof(wc)};
    wc.style = CS_DBLCLKS;
    wc.lpfnWndProc = PencereYordami;
    wc.hInstance = ornek;
    wc.hIcon = LoadIconW(ornek, MAKEINTRESOURCEW(1));
    wc.hIconSm = wc.hIcon;
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.lpszClassName = L"op4.Pencere";
    RegisterClassExW(&wc);
    POINT sifir{0, 0};
    HMONITOR mon = MonitorFromPoint(sifir, MONITOR_DEFAULTTOPRIMARY);
    MONITORINFO mi{sizeof(mi)};
    GetMonitorInfoW(mon, &mi);
    olcek_ = ImGui_ImplWin32_GetDpiScaleForMonitor(mon);
    const int cg = mi.rcWork.right - mi.rcWork.left, cy = mi.rcWork.bottom - mi.rcWork.top;
    const int pg = std::min(cg, static_cast<int>(1600 * olcek_)), py = std::min(cy, static_cast<int>(960 * olcek_));
    hwnd_ = CreateWindowExW(0, wc.lpszClassName, L"op4", WS_OVERLAPPEDWINDOW, mi.rcWork.left + (cg - pg) / 2,
                            mi.rcWork.top + (cy - py) / 2, pg, py, nullptr, nullptr, ornek, nullptr);
    if (ozelKrom_) {
        const MARGINS kenar{0, 0, 1, 0};  // DWM gölgesi ve yuvarlak köşe korunur
        DwmExtendFrameIntoClientArea(hwnd_, &kenar);
        SetWindowPos(hwnd_, nullptr, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED);
    }
    std::string hata;
    RECT r;
    GetClientRect(hwnd_, &r);
    grafik_.HataKatmaniIste(s.hataKatmani);
    grafik_.Tercih(kabuk_.ayarlar.grafik.bagdastirici, kabuk_.ayarlar.grafik.msaa);
    if (!grafik_.Baslat(s.warp || kabuk_.ayarlar.grafik.warpZorla, hata) ||
        !grafik_.TakasZinciriKur(hwnd_, static_cast<UINT>(r.right), static_cast<UINT>(r.bottom), hata)) {
        acilis.Kapat();
        Gunluk("HATA: %s", hata.c_str());
        if (testSaniye_ == 0) MessageBoxW(nullptr, Genis("DirectX 12 başlatılamadı:\n" + hata).c_str(), L"op4", MB_ICONERROR);
        return 2;
    }

    iniYolu_ = Utf8(YerelVeriDizini() + L"\\arayuz.ini");
    ImGuiBaglamiKur(olcek_, iniYolu_.c_str());
    ImGui_ImplWin32_Init(hwnd_);
    ImGui_ImplDX12_InitInfo ii;
    grafik_.ImGuiBilgisi(ii);
    ImGui_ImplDX12_Init(&ii);
    imgui_ = true;
    ana_->YazilariAyarla(ArayuzYazilari());
    ana_->bagdastirici = grafik_.BagdastiriciAdi();
    ana_->warp = grafik_.Warp();
    ana_->msaa = grafik_.OrnekSayisi();
    ana_->bagdastiricilar = Grafik::Bagdastiricilar();
    ana_->testKipi = testSaniye_ > 0;
    ana_->pencere.kucult = [this] { ShowWindow(hwnd_, SW_MINIMIZE); };
    ana_->pencere.buyutGeriAl = [this] { ShowWindow(hwnd_, IsZoomed(hwnd_) ? SW_RESTORE : SW_MAXIMIZE); };
    ana_->pencere.kapat = [this] { PostMessageW(hwnd_, WM_CLOSE, 0, 0); };
    ana_->pencere.buyuk = [this] { return IsZoomed(hwnd_) != 0; };
    LogoYukle();
    ana_->AyarlariUygula();
    if (kabuk_.ayarlar.arayuz.acilis == "bos" || !kabuk_.ayarlar.arayuz.baslangicPaneli) ana_->yanPencere = YanPencere::Ozellikler;
    acilis.Adim(AcilisAdimi::Motor);
    Gunluk("Grafik: %s%s, MSAA %u×, özellik düzeyi %s", grafik_.BagdastiriciAdi().c_str(), grafik_.Warp() ? " (WARP)" : "",
           grafik_.OrnekSayisi(), grafik_.OzellikDuzeyi());
    ana_->Bildirim().KomutYaz(std::string("op4 ") + OP4_SURUM + " — Opus Fortis. " +
                              Tr("Gezinme: sol sürükle = kaydır, Shift + sol sürükle = döndür, tekerlek = yakınlaş, Shift+F = tam görünüm."));

    // Motor hazır olana dek (en az 1,2 s, en çok 120 s) mesajları işleyerek bekle; sonra kalan adımlar ve "Hazır".
    bool cik = false;
    const ULONGLONG acilisBasi = GetTickCount64();
    bool motorBildirildi = false;
    for (;;) {
        MsgWaitForMultipleObjects(0, nullptr, FALSE, 20, QS_ALLINPUT);
        if (motor) motor->Pompala();
        MSG msg;
        while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) cik = true;
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        const bool hazir = s.motorsuz || !motor || motor->Durum().hazir;
        if (hazir && !motorBildirildi) {
            motorBildirildi = true;
            acilis.Adim(AcilisAdimi::Kutuphane);
            kabuk_.H().KareIsleriniCalistir(GecenMs());  // D: açılış dosyası, şablon dizini …
            acilis.Adim(AcilisAdimi::Proje);
            acilis.Adim(AcilisAdimi::Hazir);
        }
        const ULONGLONG gecen = GetTickCount64() - acilisBasi;
        if (cik || (hazir && (acilis.Bitti() || !acilisVar) && gecen > 400) || gecen > 120000) break;
    }
    if (motor) motor->durumBildirimi = nullptr;
    acilis.Kapat();
    Gunluk("Açılış ekranı kapandı (%.0f ms)", GecenMs());
    ShowWindow(hwnd_, SW_SHOWMAXIMIZED);
    SetForegroundWindow(hwnd_);

    // Ana döngü: girdi ya da istek yokken bekler (boşta GPU/CPU harcamaz), girdi gelince hemen çizer.
    int bosKare = 0;
    const ULONGLONG donguBasi = GetTickCount64();
    const long long kare0 = kare_;
    const double ms0 = kareToplamMs_;
    kareEnBuyukMs_ = 0;
    while (!cik) {
        MSG msg;
        bool mesaj = false;
        while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) cik = true;
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
            mesaj = true;
        }
        if (cik) break;
        if (IsIconic(hwnd_)) {
            WaitMessage();
            continue;
        }
        bosKare = mesaj || ana_->CizimGerekli() || kabuk_.gorunum.CizimIstendiMi() ? 0 : bosKare + 1;
        if (testSaniye_ == 0 && bosKare > 6) MsgWaitForMultipleObjects(0, nullptr, FALSE, 250, QS_ALLINPUT);
        Kare();
        if (testSaniye_ > 0 && kare_ - kare0 > 130 && GetTickCount64() - donguBasi >= static_cast<ULONGLONG>(testSaniye_) * 1000)
            DestroyWindow(hwnd_);
    }
    const long long kareler = kare_ - kare0;
    Gunluk("Ana döngü: %lld kare, ortalama %.2f ms/kare, en uzun %.2f ms (%.1f s)", kareler,
           kareler > 0 ? (kareToplamMs_ - ms0) / static_cast<double>(kareler) : 0.0, kareEnBuyukMs_,
           static_cast<double>(GetTickCount64() - donguBasi) / 1000.0);
    int kod = 0;
    if (testSaniye_ > 0) {
        const MotorDurumOzeti md = motor ? motor->Durum() : MotorDurumOzeti{};
        const double beklenenDonme = -40.0 * 4.0 * KameraSuruklemesi::DONME_K;
        const bool panTamam = betik_.panOlcum >= 30 && betik_.panHata < 0.5;
        const bool donmeTamam = std::fabs(betik_.donme - beklenenDonme) < 0.02;
        const bool yakinTamam = betik_.yakinHata >= 0.0 && betik_.yakinHata < 0.5;
        Gunluk("Pencere testi: kaydırma %d ölçüm, imleç altındaki noktanın en büyük kayması %.4f px %s", betik_.panOlcum,
               betik_.panHata, panTamam ? "✓" : "✗");
        Gunluk("Pencere testi: döndürme Δsapma %.4f rad (beklenen %.4f) %s", betik_.donme, beklenenDonme, donmeTamam ? "✓" : "✗");
        Gunluk("Pencere testi: yakınlaşmada imleç altındaki noktanın kayması %.4f px %s", betik_.yakinHata, yakinTamam ? "✓" : "✗");
        Gunluk("Pencere testi: motor %s", s.motorsuz ? "başlatılmadı (--motorsuz)"
                                                     : (md.basarili ? "hazır ✓" : ("HATA ✗ " + md.hata).c_str()));
        GunlukHam(Bicim("OP4OLCUM senaryo=pencere kare=%lld ort_kare_ms=%.2f en_uzun_kare_ms=%.2f kaydirma_olcum=%d "
                        "kaydirma_kayma_px=%.4f donme_rad=%.4f yakinlasma_kayma_px=%.4f bagdastirici_warp=%d msaa=%u ozel_krom=%d",
                        kareler, kareler > 0 ? (kareToplamMs_ - ms0) / static_cast<double>(kareler) : 0.0, kareEnBuyukMs_,
                        betik_.panOlcum, betik_.panHata, betik_.donme, betik_.yakinHata, grafik_.Warp() ? 1 : 0,
                        grafik_.OrnekSayisi(), ozelKrom_ ? 1 : 0));
        bool tamam = kareler > 100 && panTamam && donmeTamam && yakinTamam && (s.motorsuz || md.basarili);
        if (s.hataKatmani) {
            HataKatmaniYaz(&grafik_);
            const HataKatmani k = grafik_.HataKatmaniIletileri();
            tamam = tamam && !(k.etkin && k.hata > 0);
        }
        Gunluk(tamam ? "PENCERE TESTİ BAŞARILI" : "PENCERE TESTİ BAŞARISIZ");
        kod = tamam ? 0 : 2;
    }

    grafik_.GpuBekle();
    ImGui::UnregisterUserTexture(&logo_);
    ImGui_ImplDX12_Shutdown();
    ImGui_ImplWin32_Shutdown();
    ImGui::DestroyContext();
    imgui_ = false;
    ana_ = nullptr;
    kabuk_.Kapat();  // modül nesneleri ters sırada; motor burada durur
    Gunluk("op4 kapandı");
    return kod;
}

}  // namespace

int UygulamaCalistir(HINSTANCE ornek, const Secenekler& s) {
    Uygulama u;
    return u.Calistir(ornek, s);
}

}  // namespace op4
