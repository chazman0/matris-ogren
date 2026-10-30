// op4 — giriş noktası.
//
//   op4.exe                                   uygulama: açılış ekranı → ana pencere (DirectX 12 + Dear ImGui)
//   op4.exe proje.op4                         uygulama, proje açık
//   op4.exe --test-motor                      gömülü Python + hesap motoru (web_kopru) denetimi; pencere açmaz
//   op4.exe --test-ekran a.png [--boyut GxY] [--arayuzsuz]
//                                             tek kareyi WARP (yazılım D3D12) ile ekran dışına çizer, PNG kaydeder
//   op4.exe --test-acilis a.png [--olcek 1.5] açılış ekranını PNG'ye çizer
//   op4.exe --test-pencere 8                  uygulamayı (açılış + motor + pencere) çalıştırır, betikli kaydırma /
//                                             döndürme / yakınlaşma uygular, ölçer ve 8 s sonra kapanır
//   ortak:  --gunluk dosya.log   --warp (uygulamada donanım yerine WARP)   --motorsuz (Python başlatılmaz)   --surum
//           --hata-katmani (D3D12 hata ayıklama katmanı; varsa açılır; --test-ekran'da hata iletisi testi düşürür)
// Ölçümler günlüğe "OP4OLCUM anahtar=değer …" satırları olarak da yazılır (MIMARI §20.3).
// Çıkış kodları: 0 başarılı, 1 kullanım hatası, 2 test hatası, 3 zaman aşımı, 5 çökme.
#include <windows.h>
#include <shellapi.h>
#include <shlobj.h>

#include <algorithm>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <thread>
#include <vector>

#include "acilis.h"
#include "arayuz.h"
#include "geometri.h"
#include "grafik.h"
#include "gunluk.h"
#include "imgui.h"
#include "imgui_impl_dx12.h"
#include "imgui_impl_win32.h"
#include "motor.h"
#include "proje.h"
#include "resim.h"

extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

namespace op4 {
namespace {

struct Secenekler {
    std::wstring testEkran, testAcilis, gunluk, proje;
    bool testMotor = false, warp = false, surum = false, arayuzsuz = false, motorsuz = false, hataKatmani = false;
    int g = 960, y = 540;
    float olcek = 1.0f;
    int testPencere = 0;  // saniye
};

std::wstring UygulamaDizini() {
    std::wstring b(32768, L'\0');
    DWORD n = GetModuleFileNameW(nullptr, b.data(), static_cast<DWORD>(b.size()));
    b.resize(n);
    size_t i = b.find_last_of(L"\\/");
    return i == std::wstring::npos ? std::wstring(L".") : b.substr(0, i);
}

std::wstring YerelVeriDizini() {
    PWSTR p = nullptr;
    std::wstring d;
    if (SUCCEEDED(SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, nullptr, &p))) d = p;
    CoTaskMemFree(p);
    if (d.empty()) return UygulamaDizini();
    d += L"\\Opus Fortis";
    CreateDirectoryW(d.c_str(), nullptr);
    d += L"\\op4";
    CreateDirectoryW(d.c_str(), nullptr);
    return d;
}

bool Ayristir(Secenekler& s, std::string& hata) {
    int n = 0;
    wchar_t** a = CommandLineToArgvW(GetCommandLineW(), &n);
    bool tamam = true;
    for (int i = 1; i < n && tamam; ++i) {
        std::wstring k = a[i];
        auto deger = [&](std::wstring& h) {
            if (i + 1 >= n) {
                hata = Utf8(k) + " bir değer bekliyor";
                tamam = false;
                return;
            }
            h = a[++i];
        };
        if (k == L"--test-motor") s.testMotor = true;
        else if (k == L"--test-ekran") deger(s.testEkran);
        else if (k == L"--test-acilis") deger(s.testAcilis);
        else if (k == L"--gunluk") deger(s.gunluk);
        else if (k == L"--warp") s.warp = true;
        else if (k == L"--arayuzsuz") s.arayuzsuz = true;
        else if (k == L"--motorsuz") s.motorsuz = true;
        else if (k == L"--surum") s.surum = true;
        else if (k == L"--hata-katmani") s.hataKatmani = true;
        else if (k == L"--test-pencere") {
            std::wstring v;
            deger(v);
            if (tamam) s.testPencere = std::clamp(_wtoi(v.c_str()), 1, 600);
        }
        else if (k == L"--boyut") {
            std::wstring v;
            deger(v);
            if (tamam && (swscanf(v.c_str(), L"%dx%d", &s.g, &s.y) != 2 || s.g < 64 || s.y < 64 || s.g > 8192 || s.y > 8192)) {
                hata = "--boyut GxY biçiminde olmalı (ör. 960x540)";
                tamam = false;
            }
        } else if (k == L"--olcek") {
            std::wstring v;
            deger(v);
            if (tamam) s.olcek = std::clamp(static_cast<float>(_wtof(v.c_str())), 0.5f, 4.0f);
        } else if (!k.empty() && k[0] != L'-') s.proje = k;
        else {
            hata = "bilinmeyen seçenek: " + Utf8(k);
            tamam = false;
        }
    }
    LocalFree(a);
    return tamam;
}

std::string Bicim(const char* bicim, ...)
#if defined(__GNUC__)
    __attribute__((format(gnu_printf, 1, 2)))
#endif
    ;
std::string Bicim(const char* bicim, ...) {
    va_list a;
    va_start(a, bicim);
    char b[1024];
    const int n = std::vsnprintf(b, sizeof(b), bicim, a);
    va_end(a);
    return std::string(b, n < 0 ? 0 : std::min(static_cast<size_t>(n), sizeof(b) - 1));
}

LONG WINAPI CokmeYakala(EXCEPTION_POINTERS* e) {
    Gunluk("ÇÖKME: özel durum 0x%08lX, adres %p", static_cast<unsigned long>(e->ExceptionRecord->ExceptionCode),
           e->ExceptionRecord->ExceptionAddress);
    GunlukKapat();
    ExitProcess(5);
}

// Test kipleri: hata pencereleri açılmasın (CI'da asılı kalmasın) ve süre sınırı olsun.
void TestKipi(unsigned saniye) {
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
#ifdef _MSC_VER
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    SetUnhandledExceptionFilter(CokmeYakala);
    std::thread([saniye] {
        Sleep(saniye * 1000);
        Gunluk("ZAMAN AŞIMI: test %u saniyede bitmedi", saniye);
        GunlukKapat();
        ExitProcess(3);
    }).detach();
}

// ------------------------------------------------------------------------------------------------ --test-motor
int MotorTesti() {
    TestKipi(300);
    Gunluk("--test-motor: gömülü Python + hesap motoru (web_kopru) denetimi");
    Gunluk("Uygulama dizini: %s", Utf8(UygulamaDizini()).c_str());
    Motor m;
    m.Baslat(UygulamaDizini(), nullptr);
    m.Bekle(INFINITE);
    MotorDurumu d = m.Durum();
    if (!d.basarili) {
        Gunluk("MOTOR TESTİ BAŞARISIZ: %s", d.hata.c_str());
        return 2;
    }
    Gunluk("Python: %s", d.pythonSurumu.c_str());
    Gunluk("web_kopru.surum_json() = %s", d.surumJson.c_str());
    Gunluk("Şablonlar (%d): ", d.sablonSayisi);
    for (const std::string& a : d.sablonAdlari) Gunluk("  - %s", a.c_str());
    Gunluk("bina_sablonlar yanıtı (%zu bayt): %.240s…", d.sablonlarJson.size(), d.sablonlarJson.c_str());
    Gunluk("SÜRELER: DLL yükleme %.1f ms | Py_InitializeEx %.1f ms | import web_kopru %.1f ms | surum_json %.1f ms | "
           "bina_sablonlar %.1f ms | TOPLAM motor açılışı %.1f ms",
           d.msDll, d.msBaslat, d.msIceAktar, d.msSurum, d.msSablon, d.msToplam);
    GunlukHam(Bicim("OP4OLCUM senaryo=motor dll_ms=%.1f baslat_ms=%.1f ice_aktar_ms=%.1f sablonlar_ms=%.1f toplam_ms=%.1f "
                    "sablon=%d", d.msDll, d.msBaslat, d.msIceAktar, d.msSablon, d.msToplam, d.sablonSayisi));

    bool tamam = d.sablonSayisi > 0 && d.surumJson.find("\"python\"") != std::string::npos;
    // Kuyruk üzerinden iki gidiş-dönüş daha (arayüz iş parçacığından çağrı yolu).
    double t = GecenMs();
    std::string r = m.Calistir(R"({"islem":"determinant","girdi":{"A":"2 1; 1 3"}})");
    Gunluk("determinant([[2,1],[1,3]]) → sonuc_metin %s (%.1f ms)",
           r.find("\"sonuc_metin\": \"5\"") != std::string::npos ? "5 ✓" : "BEKLENMEDİK", GecenMs() - t);
    tamam = tamam && r.find("\"sonuc_metin\": \"5\"") != std::string::npos;
    if (!d.sablonAdlari.empty()) {
        t = GecenMs();
        r = m.Calistir(R"({"islem":"bina_sablon","girdi":{"ad":")" + d.sablonAdlari[0] + R"("}})");
        bool sablonTamam = r.find("\"hata\": null") != std::string::npos && r.find("\"bina\"") != std::string::npos;
        Gunluk("bina_sablon(%s) → %zu bayt, %s (%.1f ms)", d.sablonAdlari[0].c_str(), r.size(),
               sablonTamam ? "hata yok ✓" : r.substr(0, 300).c_str(), GecenMs() - t);
        tamam = tamam && sablonTamam;
    }
    m.Durdur();
    Gunluk(tamam ? "MOTOR TESTİ BAŞARILI" : "MOTOR TESTİ BAŞARISIZ");
    return tamam ? 0 : 2;
}

// ------------------------------------------------------------------------------------------------ --test-ekran
void ImGuiBaglamiKur(float olcek, const char* ini) {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = ini;
    io.ConfigFlags |= ImGuiConfigFlags_DockingEnable | ImGuiConfigFlags_NavEnableKeyboard;
    io.ConfigWindowsMoveFromTitleBarOnly = true;
    ArayuzStili(olcek);
    ArayuzYazitipi(olcek);
}

// D3D12 hata ayıklama katmanının varlığı (MIMARI D13): her ekran testinde yoklanır ve günlüğe yazılır.
void HataKatmaniYaz(const Grafik* g) {
    const HataKatmani y = Grafik::HataKatmaniYokla();
    GunlukHam(Bicim("OP4OLCUM hata_katmani=%s hr=0x%08lX", y.var ? "var" : "yok", static_cast<unsigned long>(y.hr)));
    if (!g) return;
    const HataKatmani k = g->HataKatmaniIletileri();
    if (!k.etkin) return;
    GunlukHam(Bicim("OP4OLCUM hata_katmani_iletileri hata=%u uyari=%u bilgi=%u dusen=%llu", k.hata, k.uyari, k.bilgi,
                    k.dusen));
    for (const std::string& o : k.ornekler) Gunluk("  D3D12 %s", o.c_str());
}

int EkranTesti(const Secenekler& s) {
    TestKipi(600);
    Gunluk("--test-ekran: %dx%d, WARP, %s%s", s.g, s.y, s.arayuzsuz ? "arayüzsüz" : "arayüzlü",
           s.hataKatmani ? ", hata ayıklama katmanı istendi" : "");
    double t0 = GecenMs();
    Grafik g;
    g.HataKatmaniIste(s.hataKatmani);
    std::string hata;
    if (!g.Baslat(true, hata)) {
        HataKatmaniYaz(nullptr);
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    double tAygit = GecenMs() - t0;
    Ag ag = OrnekSahne();
    Gunluk("Sahne: %zu köşe, %zu üçgen, %zu kenar çizgisi, %zu çubuk", ag.koseler.size(), ag.indisler.size() / 3,
           ag.kenarlar.size() / 2, ag.eksenler.size() / 2);
    if (!g.SahneYukle(ag, hata) || !g.EkranDisiKur(static_cast<UINT>(s.g), static_cast<UINT>(s.y), hata)) {
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    const float olcek = s.y >= 900 ? 1.5f : (s.y >= 700 ? 1.25f : 1.0f);
    ImGuiBaglamiKur(olcek, nullptr);
    ImGuiIO& io = ImGui::GetIO();
    io.DisplaySize = ImVec2(static_cast<float>(s.g), static_cast<float>(s.y));
    ImGui_ImplDX12_InitInfo ii;
    g.ImGuiBilgisi(ii);
    ImGui_ImplDX12_Init(&ii);

    ArayuzDurumu d;
    d.bagdastirici = g.BagdastiriciAdi();
    d.warp = g.Warp();
    d.ornek = g.OrnekSayisi();
    d.ozellikDuzeyi = g.OzellikDuzeyi();
    d.ucgen = g.UcgenSayisi();
    d.testModu = true;
    KomutYaz(d, "op4 " OP4_SURUM " — ekran testi (WARP)");
    KomutYaz(d, "Sahne: 2 çerçeve, HE340A kolon ve kirişler, IPE300 bağ kirişleri");
    Kamera k;
    k.Sigdir(ag.enKucuk, ag.enBuyuk);

    std::vector<uint8_t> dolu, bos;
    GorusAlani tam{0, 0, static_cast<float>(s.g), static_cast<float>(s.y)};
    // 1) Sağlama: model olmadan ve modelle (arayüzsüz) iki kare; model piksellerinin oranı.
    Ag bosAg;
    {
        double t = GecenMs();
        if (!g.EkranDisiKaresi(k, SahneAyari{}, tam, nullptr, &dolu)) return 2;
        Gunluk("Kare (arayüzsüz, kesit görünümü): %.1f ms", GecenMs() - t);
    }
    // 2) Asıl kare: arayüzle (ImGui yerleşimi ilk karelerde oturur; 3 kare çizilir, sonuncusu kaydedilir).
    std::vector<uint8_t> rgba;
    if (s.arayuzsuz) {
        rgba = dolu;
    } else {
        for (int i = 0; i < 3; ++i) {
            io.DeltaTime = 1.0f / 60.0f;
            ImGui_ImplDX12_NewFrame();
            ImGui::NewFrame();
            ArayuzCiz(d);
            ImGui::Render();
            double t = GecenMs();
            if (!g.EkranDisiKaresi(k, d.sahne, d.gorus, ImGui::GetDrawData(), i == 2 ? &rgba : nullptr)) return 2;
            Gunluk("Kare %d (arayüzlü; sahne alanı %.0f,%.0f %.0fx%.0f): %.1f ms", i + 1, d.gorus.x, d.gorus.y, d.gorus.g,
                   d.gorus.y2, GecenMs() - t);
        }
    }
    // Model olmadan: çubuk görünümü + eksen tamponu boş değil; bu yüzden ayrı bir boş sahne yükle.
    if (!g.SahneYukle(bosAg, hata) || !g.EkranDisiKaresi(k, SahneAyari{}, tam, nullptr, &bos)) return 2;
    size_t fark = 0;
    for (size_t i = 0; i + 3 < dolu.size(); i += 4)
        if (std::abs(dolu[i] - bos[i]) + std::abs(dolu[i + 1] - bos[i + 1]) + std::abs(dolu[i + 2] - bos[i + 2]) > 24) ++fark;
    double oran = 100.0 * static_cast<double>(fark) / (static_cast<double>(dolu.size()) / 4.0);
    Gunluk("Sağlama: model pikselleri %%%.1f", oran);

    std::wstring yol = s.testEkran;
    if (!PngYaz(yol, s.g, s.y, rgba.data(), false, hata)) {
        Gunluk("EKRAN TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    ImGui_ImplDX12_Shutdown();
    ImGui::DestroyContext();
    g.GpuBekle();
    Gunluk("Aygıt + boru hatları %.1f ms; toplam %.1f ms; PNG: %s", tAygit, GecenMs() - t0, Utf8(yol).c_str());
    GunlukHam(Bicim("OP4OLCUM senaryo=ekran gen=%d yuk=%d arayuz=%d aygit_ms=%.1f toplam_ms=%.1f model_yuzde=%.1f msaa=%u",
                    s.g, s.y, s.arayuzsuz ? 0 : 1, tAygit, GecenMs() - t0, oran, g.OrnekSayisi()));
    HataKatmaniYaz(&g);
    const HataKatmani katman = g.HataKatmaniIletileri();
    bool tamam = oran > 2.0;
    if (katman.etkin && katman.hata > 0) {
        Gunluk("Hata ayıklama katmanı %u hata iletisi verdi", katman.hata);
        tamam = false;
    }
    Gunluk(tamam ? "EKRAN TESTİ BAŞARILI"
                 : (oran > 2.0 ? "EKRAN TESTİ BAŞARISIZ (hata ayıklama katmanı)" : "EKRAN TESTİ BAŞARISIZ (model görünmüyor)"));
    return tamam ? 0 : 2;
}

int AcilisTesti(const Secenekler& s) {
    TestKipi(120);
    std::string hata;
    if (!AcilisResmi(UygulamaDizini(), L"Sürüm " OP4_SURUM, s.testAcilis, s.olcek, hata)) {
        Gunluk("AÇILIŞ TESTİ BAŞARISIZ: %s", hata.c_str());
        return 2;
    }
    Gunluk("AÇILIŞ TESTİ BAŞARILI: %s", Utf8(s.testAcilis).c_str());
    return 0;
}

// ------------------------------------------------------------------------------------------------ uygulama
class Uygulama {
public:
    int Calistir(HINSTANCE ornek, const Secenekler& s);
    LRESULT Yordam(HWND h, UINT m, WPARAM w, LPARAM l);

private:
    void Kare();
    void KameraGirdisi();
    void IstekleriIsle();
    void BaslikGuncelle();
    void TestAdimi();  // --test-pencere: ImGui::NewFrame öncesi betikli girdi
    void TestOlc();    // --test-pencere: kare sonrası ölçüm

    HWND hwnd_ = nullptr;
    Grafik grafik_;
    Motor motor_;
    ArayuzDurumu arayuz_;
    Proje proje_;
    Ag ag_;
    bool imgui_ = false;
    bool kareIcinde_ = false;
    bool motorAlindi_ = false;
    float olcek_ = 1.0f;
    bool olcekDegisti_ = false;
    std::string iniYolu_;
    // --test-pencere
    int testSaniye_ = 0;
    bool testShift_ = false;
    long long kare_ = 0;
    double kareToplamMs_ = 0, kareEnBuyukMs_ = 0;
    struct {
        V3 p;
        bool pan = false, yakin = false;
        float mx = 0, my = 0;
        float panHata = 0, yakinHata = -1, sapma0 = 0, donme = 0;
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
            reinterpret_cast<MINMAXINFO*>(l)->ptMinTrackSize = {800, 500};
            return 0;
        case WM_SYSCOMMAND:
            if ((w & 0xfff0) == SC_KEYMENU) return 0;  // Alt menü tuşu ImGui'ye kalsın
            break;
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(h, m, w, l);
}

void Uygulama::BaslikGuncelle() {
    std::wstring b = L"op4";
    if (!proje_.yol.empty()) {
        size_t i = proje_.yol.find_last_of(L"\\/");
        b += L" — " + (i == std::wstring::npos ? proje_.yol : proje_.yol.substr(i + 1));
    }
    SetWindowTextW(hwnd_, b.c_str());
    arayuz_.projeAdi = proje_.yol.empty() ? "Adsız" : Utf8(proje_.yol.substr(proje_.yol.find_last_of(L"\\/") + 1));
}

void Uygulama::KameraGirdisi() {
    ImGuiIO& io = ImGui::GetIO();
    Kamera& k = proje_.kamera;
    const GorusAlani& g = arayuz_.gorus;
    const ImVec2 m = io.MousePos;
    const bool shift = io.KeyShift || testShift_;
    const bool icinde = m.x >= g.x && m.y >= g.y && m.x < g.x + g.g && m.y < g.y + g.y2;
    if (!io.WantCaptureMouse && icinde) {
        if (ImGui::IsMouseClicked(ImGuiMouseButton_Left)) k.SuruklemeBasla(m.x, m.y, shift);
        if (ImGui::IsMouseClicked(ImGuiMouseButton_Middle)) k.SuruklemeBasla(m.x, m.y, false);
        if (io.MouseWheel != 0.0f) k.Yakinlas(io.MouseWheel, m.x - g.x, m.y - g.y, g.g, g.y2);
    }
    if (k.surukleme.etkin) {
        const bool sol = ImGui::IsMouseDown(ImGuiMouseButton_Left), orta = ImGui::IsMouseDown(ImGuiMouseButton_Middle);
        if (!sol && !orta) {
            k.SuruklemeBitir();
        } else {
            // Sürükleme sırasında Shift basılır / bırakılırsa kip, o anki konumdan kesintisiz değişir.
            if (sol && !orta && k.surukleme.dondur != shift) k.SuruklemeBasla(m.x, m.y, shift);
            k.SuruklemeGuncelle(m.x, m.y, g.y2);
        }
    }
    if (!io.WantCaptureKeyboard) {
        if (ImGui::IsKeyPressed(ImGuiKey_F, false)) arayuz_.istek = Istek::Sigdir;
        if (ImGui::IsKeyPressed(ImGuiKey_K, false)) arayuz_.sahne.kesitGorunumu = !arayuz_.sahne.kesitGorunumu;
        if (ImGui::IsKeyPressed(ImGuiKey_G, false)) arayuz_.sahne.izgara = !arayuz_.sahne.izgara;
    }
}

void Uygulama::IstekleriIsle() {
    Istek i = arayuz_.istek;
    arayuz_.istek = Istek::Yok;
    std::string hata;
    switch (i) {
        case Istek::Yeni:
            proje_ = Proje();
            proje_.kamera.Sigdir(ag_.enKucuk, ag_.enBuyuk);
            arayuz_.sahne = proje_.ayar;
            BaslikGuncelle();
            KomutYaz(arayuz_, "Yeni proje.");
            break;
        case Istek::Ac: {
            std::wstring yol;
            if (!DosyaSec(hwnd_, false, L"", yol)) break;
            Proje p;
            if (ProjeAc(yol, p, hata)) {
                proje_ = p;
                arayuz_.sahne = proje_.ayar;
                BaslikGuncelle();
                KomutYaz(arayuz_, "Açıldı: " + Utf8(yol));
            } else {
                KomutYaz(arayuz_, "HATA: " + hata);
            }
            break;
        }
        case Istek::Kaydet:
        case Istek::FarkliKaydet: {
            std::wstring yol = proje_.yol;
            if (i == Istek::FarkliKaydet || yol.empty())
                if (!DosyaSec(hwnd_, true, yol.empty() ? L"proje.op4" : yol, yol)) break;
            proje_.ayar = arayuz_.sahne;
            if (ProjeKaydet(yol, proje_, hata)) {
                proje_.yol = yol;
                BaslikGuncelle();
                KomutYaz(arayuz_, "Kaydedildi: " + Utf8(yol));
            } else {
                KomutYaz(arayuz_, "HATA: " + hata);
            }
            break;
        }
        case Istek::Cikis:
            PostMessageW(hwnd_, WM_CLOSE, 0, 0);
            break;
        case Istek::Sigdir:
            proje_.kamera.Sigdir(ag_.enKucuk, ag_.enBuyuk);
            break;
        default:
            break;
    }
}

void Uygulama::TestAdimi() {
    // Olay sırası önemli: ImGui girdi kuyruğu (trickle) bir karede konumdan SONRA gelen düğme olayını işler, düğmeden
    // sonra gelen konumu ertelemez ama tekerleği bir sonraki kareye erteler. Win32 arka ucu odaktayken gerçek imleç
    // konumunu her karede kuyruğa ekler; betik konumu onun ardından ve düğme / tekerlekten ÖNCE eklenir.
    ImGuiIO& io = ImGui::GetIO();
    const GorusAlani& g = arayuz_.gorus;
    const Kamera& k = proje_.kamera;
    const float cx = g.x + g.g * 0.5f, cy = g.y + g.y2 * 0.5f;
    const long long n = kare_;
    // 1) konum: kaydırma (20–62) 40 kare × (+3, +1) px; döndürme (70–112) Shift + 40 kare × +4 px; yakınlaşma (120–)
    if (n == 20 || n == 70) {
        betik_.mx = std::floor(cx);
        betik_.my = std::floor(cy);
    } else if (n > 21 && n <= 61) {
        betik_.mx += 3.0f;
        betik_.my += 1.0f;
    } else if (n > 71 && n <= 111) {
        betik_.mx += 4.0f;
    } else if (n == 120) {
        betik_.mx = std::floor(g.x + g.g * 0.3f);  // ImGui fare konumunu tam piksele yuvarlar
        betik_.my = std::floor(g.y + g.y2 * 0.4f);
    }
    if (n >= 20) io.AddMousePosEvent(betik_.mx, betik_.my);
    // 2) düğmeler, Shift, tekerlek
    if (n == 21) {
        betik_.p = k.HedefDuzlemNoktasi(betik_.mx - g.x, betik_.my - g.y, g.g, g.y2);
        betik_.pan = true;
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, true);
    } else if (n == 62) {
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, false);
        betik_.pan = false;
    } else if (n == 70) {
        testShift_ = true;
        betik_.sapma0 = k.sapma;
    } else if (n == 71) {
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, true);
    } else if (n == 112) {
        io.AddMouseButtonEvent(ImGuiMouseButton_Left, false);
    } else if (n == 114) {
        testShift_ = false;
        betik_.donme = k.sapma - betik_.sapma0;
    } else if (n == 122) {
        betik_.p = k.HedefDuzlemNoktasi(betik_.mx - g.x, betik_.my - g.y, g.g, g.y2);
        betik_.yakin = true;
        io.AddMouseWheelEvent(0.0f, 2.0f);
    }
}

void Uygulama::TestOlc() {
    const GorusAlani& g = arayuz_.gorus;
    const Kamera& k = proje_.kamera;
    float sx = 0, sy = 0;
    const ImVec2 m = ImGui::GetIO().MousePos;
    if (betik_.pan && kare_ > 22 && k.surukleme.etkin && k.Izdusur(betik_.p, g.g, g.y2, sx, sy)) {
        betik_.panHata = std::max(betik_.panHata, std::hypot(sx + g.x - m.x, sy + g.y - m.y));
        ++betik_.panOlcum;
    }
    if (betik_.yakin && kare_ == 125 && k.Izdusur(betik_.p, g.g, g.y2, sx, sy))
        betik_.yakinHata = std::hypot(sx + g.x - betik_.mx, sy + g.y - betik_.my);
}

void Uygulama::Kare() {
    if (kareIcinde_) return;
    kareIcinde_ = true;
    const double kareBasi = GecenMs();
    if (olcekDegisti_) {
        ArayuzStili(olcek_);
        olcekDegisti_ = false;
    }
    if (!motorAlindi_) {
        arayuz_.motor = motor_.Durum();
        if (arayuz_.motor.hazir) {
            motorAlindi_ = true;
            if (arayuz_.motor.basarili)
                KomutYaz(arayuz_, "Hesap motoru hazır: Python " +
                                      arayuz_.motor.pythonSurumu.substr(0, arayuz_.motor.pythonSurumu.find(' ')) + ", " +
                                      std::to_string(arayuz_.motor.sablonSayisi) + " yapı şablonu (" +
                                      std::to_string(static_cast<int>(arayuz_.motor.msToplam)) + " ms).");
            else
                KomutYaz(arayuz_, "HATA: hesap motoru başlatılamadı — " + arayuz_.motor.hata);
        }
    }
    arayuz_.fps = ImGui::GetIO().Framerate;
    ImGui_ImplDX12_NewFrame();
    ImGui_ImplWin32_NewFrame();
    if (testSaniye_ > 0) TestAdimi();
    ImGui::NewFrame();
    ArayuzCiz(arayuz_);
    KameraGirdisi();
    ImGui::Render();
    grafik_.PencereKaresi(proje_.kamera, arayuz_.sahne, arayuz_.gorus, ImGui::GetDrawData());
    if (testSaniye_ > 0) TestOlc();
    const double sure = GecenMs() - kareBasi;
    ++kare_;
    kareToplamMs_ += sure;
    kareEnBuyukMs_ = std::max(kareEnBuyukMs_, kare_ > 3 ? sure : 0.0);
    kareIcinde_ = false;
    if (arayuz_.istek != Istek::Yok) IstekleriIsle();
}

int Uygulama::Calistir(HINSTANCE ornek, const Secenekler& s) {
    g_uygulama = this;
    testSaniye_ = s.testPencere;
    if (testSaniye_ > 0) TestKipi(static_cast<unsigned>(testSaniye_) + 240);
    ImGui_ImplWin32_EnableDpiAwareness();
    const std::wstring dizin = UygulamaDizini();
    Gunluk("op4 %s başlıyor; dizin: %s", OP4_SURUM, Utf8(dizin).c_str());

    AcilisEkrani acilis;
    acilis.Olustur(ornek, dizin, L"Sürüm " OP4_SURUM);
    const ULONGLONG acilisBasi = GetTickCount64();
    if (!s.motorsuz)
        motor_.Baslat(dizin, [&acilis](const std::string& m, float o) { acilis.Ilerleme(m + "…", 0.10f + 0.88f * o); });
    acilis.Ilerleme("Grafik başlatılıyor (DirectX 12)…", 0.03f);

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
    std::string hata;
    RECT r;
    GetClientRect(hwnd_, &r);
    grafik_.HataKatmaniIste(s.hataKatmani);
    if (!grafik_.Baslat(s.warp, hata) || !grafik_.TakasZinciriKur(hwnd_, static_cast<UINT>(r.right), static_cast<UINT>(r.bottom), hata)) {
        acilis.Kapat();
        Gunluk("HATA: %s", hata.c_str());
        if (testSaniye_ == 0) MessageBoxW(nullptr, Genis("DirectX 12 başlatılamadı:\n" + hata).c_str(), L"op4", MB_ICONERROR);
        return 2;
    }
    ag_ = OrnekSahne();
    if (!grafik_.SahneYukle(ag_, hata)) Gunluk("HATA: %s", hata.c_str());
    proje_.kamera.Sigdir(ag_.enKucuk, ag_.enBuyuk);
    acilis.Ilerleme("Arayüz hazırlanıyor…", 0.08f);

    iniYolu_ = Utf8(YerelVeriDizini() + L"\\arayuz.ini");
    ImGuiBaglamiKur(olcek_, iniYolu_.c_str());
    ImGui_ImplWin32_Init(hwnd_);
    ImGui_ImplDX12_InitInfo ii;
    grafik_.ImGuiBilgisi(ii);
    ImGui_ImplDX12_Init(&ii);
    imgui_ = true;
    arayuz_.bagdastirici = grafik_.BagdastiriciAdi();
    arayuz_.warp = grafik_.Warp();
    arayuz_.ornek = grafik_.OrnekSayisi();
    arayuz_.ozellikDuzeyi = grafik_.OzellikDuzeyi();
    arayuz_.ucgen = grafik_.UcgenSayisi();
    arayuz_.motorBaslatildi = !s.motorsuz;
    motorAlindi_ = s.motorsuz;
    KomutYaz(arayuz_, "op4 " OP4_SURUM " — Opus Fortis. Gezinme: sol sürükle = kaydır, Shift + sol sürükle = döndür, "
                      "tekerlek = yakınlaş, F = tümünü göster.");

    if (!s.proje.empty()) {
        Proje p;
        if (ProjeAc(s.proje, p, hata)) {
            proje_ = p;
            arayuz_.sahne = p.ayar;
        } else {
            KomutYaz(arayuz_, "HATA: " + hata);
        }
    }
    BaslikGuncelle();

    // Açılış ekranı: motor hazır olana dek (en az 1,2 s, en çok 120 s) mesajları işleyerek bekle.
    bool cik = false;
    for (;;) {
        HANDLE h = motor_.HazirOlayi();
        MsgWaitForMultipleObjects(1, &h, FALSE, 50, QS_ALLINPUT);
        MSG msg;
        while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) cik = true;
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        const ULONGLONG gecen = GetTickCount64() - acilisBasi;
        if (cik || ((s.motorsuz || motor_.Bekle(0)) && gecen > 1200) || gecen > 120000) break;
    }
    acilis.Ilerleme("Hazır", 1.0f);
    acilis.Kapat();
    Gunluk("Açılış ekranı kapandı (%.0f ms)", GecenMs());
    ShowWindow(hwnd_, SW_SHOWMAXIMIZED);
    SetForegroundWindow(hwnd_);

    // Ana döngü: girdi yokken bekler (boşta GPU/CPU harcamaz), girdi gelince hemen çizer.
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
        bosKare = mesaj ? 0 : bosKare + 1;
        if (testSaniye_ == 0 && bosKare > 6 && !proje_.kamera.surukleme.etkin)
            MsgWaitForMultipleObjects(0, nullptr, FALSE, 250, QS_ALLINPUT);
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
        const MotorDurumu md = motor_.Durum();
        const float beklenenDonme = -40.0f * 4.0f * 0.0065f;
        const bool panTamam = betik_.panOlcum >= 30 && betik_.panHata < 0.5f;
        const bool donmeTamam = std::fabs(betik_.donme - beklenenDonme) < 0.02f;
        const bool yakinTamam = betik_.yakinHata >= 0.0f && betik_.yakinHata < 0.5f;
        Gunluk("Pencere testi: kaydırma %d ölçüm, imleç altındaki noktanın en büyük kayması %.4f px %s", betik_.panOlcum,
               betik_.panHata, panTamam ? "✓" : "✗");
        Gunluk("Pencere testi: döndürme Δsapma %.4f rad (beklenen %.4f) %s", betik_.donme, beklenenDonme,
               donmeTamam ? "✓" : "✗");
        Gunluk("Pencere testi: yakınlaşmada imleç altındaki noktanın kayması %.4f px %s", betik_.yakinHata,
               yakinTamam ? "✓" : "✗");
        Gunluk("Pencere testi: motor %s", s.motorsuz ? "başlatılmadı (--motorsuz)"
                                                     : (md.basarili ? "hazır ✓" : ("HATA ✗ " + md.hata).c_str()));
        GunlukHam(Bicim("OP4OLCUM senaryo=pencere kare=%lld ort_kare_ms=%.2f en_uzun_kare_ms=%.2f kaydirma_olcum=%d "
                        "kaydirma_kayma_px=%.4f donme_rad=%.4f yakinlasma_kayma_px=%.4f bagdastirici_warp=%d msaa=%u",
                        kareler, kareler > 0 ? (kareToplamMs_ - ms0) / static_cast<double>(kareler) : 0.0,
                        kareEnBuyukMs_, betik_.panOlcum, betik_.panHata, betik_.donme, betik_.yakinHata,
                        grafik_.Warp() ? 1 : 0, grafik_.OrnekSayisi()));
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
    ImGui_ImplDX12_Shutdown();
    ImGui_ImplWin32_Shutdown();
    ImGui::DestroyContext();
    imgui_ = false;
    motor_.Durdur();
    Gunluk("op4 kapandı");
    return kod;
}

}  // namespace
}  // namespace op4

int WINAPI wWinMain(HINSTANCE ornek, HINSTANCE, PWSTR, int) {
    using namespace op4;
    CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    Secenekler s;
    std::string hata;
    const bool tamam = Ayristir(s, hata);
    std::wstring gunluk = s.gunluk;
    const bool test = s.testMotor || !s.testEkran.empty() || !s.testAcilis.empty() || s.testPencere > 0;
    if (gunluk.empty() && !test) gunluk = YerelVeriDizini() + L"\\op4.log";
    GunlukAc(gunluk);
    if (!tamam) {
        Gunluk("Kullanım hatası: %s", hata.c_str());
        if (!test) MessageBoxW(nullptr, Genis(hata).c_str(), L"op4", MB_ICONWARNING);
        return 1;
    }
    if (s.surum) {
        Gunluk("op4 %s", OP4_SURUM);
        return 0;
    }
    int kod;
    if (s.testMotor)
        kod = MotorTesti();
    else if (!s.testEkran.empty())
        kod = EkranTesti(s);
    else if (!s.testAcilis.empty())
        kod = AcilisTesti(s);
    else {
        Uygulama u;
        kod = u.Calistir(ornek, s);
    }
    GunlukKapat();
    CoUninitialize();
    return kod;
}
