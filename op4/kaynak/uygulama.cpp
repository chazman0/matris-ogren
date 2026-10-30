// op4 — uygulama: açılış ekranı → ana pencere (Win32 + DirectX 12 + Dear ImGui) → döngü; --test-pencere bu yoldan çalışır.
// Sahibi: C (arayuz-goruntu). Sözleşme nesneleri ve paket modülleri UygulamaKabugu'ndadır (cekirdek/kabuk.h); hesap motoru
// MotorHizmeti üstünden kullanılır (A'nın modülü sağlar), dosya komutları komut defterinden çalışır (D bağladıkça).
#include <windows.h>

#include <algorithm>
#include <cmath>
#include <string>
#include <string_view>
#include <vector>

#include "acilis.h"
#include "arayuz.h"
#include "cekirdek/kabuk.h"
#include "cekirdek/motor_hizmeti.h"
#include "geometri.h"
#include "grafik.h"
#include "gunluk.h"
#include "imgui.h"
#include "imgui_impl_dx12.h"
#include "imgui_impl_win32.h"
#include "motor.h"
#include "platform/dosya_sistemi.h"
#include "proje.h"
#include "test_kipleri.h"

extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

namespace op4 {
namespace {

// Arayüzün (Faz 0) motor paneli eski MotorDurumu yapısını gösterir; MotorHizmeti özetinden doldurulur.
MotorDurumu EskiMotorDurumu(const MotorDurumOzeti& d) {
    MotorDurumu e;
    e.hazir = d.hazir;
    e.basarili = d.basarili;
    e.hata = d.hata;
    e.pythonSurumu = d.pythonSurumu;
    e.surumJson = d.surumJson;
    e.msToplam = d.hazirMs;
    e.sablonSayisi = -1;
    return e;
}

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
    // Komut defterinde işleyicisi bağlı komut varsa onu çalıştırır (D / C komutları devraldıkça eski yol devre dışı kalır).
    bool KomutVarsaCalistir(const char* id);

    HWND hwnd_ = nullptr;
    Grafik grafik_;
    UygulamaKabugu kabuk_;  // sözleşme nesneleri + paket modülleri (cekirdek/kabuk.h)
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
            if (KomutVarsaCalistir("dosya.yeni")) break;
            proje_ = Proje();
            proje_.kamera.Sigdir(ag_.enKucuk, ag_.enBuyuk);
            arayuz_.sahne = proje_.ayar;
            BaslikGuncelle();
            KomutYaz(arayuz_, "Yeni proje.");
            break;
        case Istek::Ac: {
            if (KomutVarsaCalistir("dosya.ac")) break;
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
            if (KomutVarsaCalistir(i == Istek::Kaydet ? "dosya.kaydet" : "dosya.farkli_kaydet")) break;
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
            if (KomutVarsaCalistir("dosya.cikis")) break;
            PostMessageW(hwnd_, WM_CLOSE, 0, 0);
            break;
        case Istek::Sigdir:
            if (KomutVarsaCalistir("gorunum.sigdir")) break;
            proje_.kamera.Sigdir(ag_.enKucuk, ag_.enBuyuk);
            break;
        default:
            break;
    }
}

bool Uygulama::KomutVarsaCalistir(const char* id) {
    Hizmetler& h = kabuk_.H();
    if (!h.komutlar || !h.komutlar->Durum(id, h).bagli) return false;
    std::string hata;
    if (!h.komutlar->Calistir(id, h, KomutKaynagi::Menu, {}, &hata) && !hata.empty()) KomutYaz(arayuz_, hata);
    return true;
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
    MotorHizmeti* motor = kabuk_.H().motor;
    if (!motorAlindi_ && motor) {
        const MotorDurumOzeti md = motor->Durum();
        arayuz_.motor = EskiMotorDurumu(md);
        if (md.hazir) {
            motorAlindi_ = true;
            if (md.basarili)
                KomutYaz(arayuz_, "Hesap motoru hazır: " + md.aciklama + ".");
            else
                KomutYaz(arayuz_, "HATA: hesap motoru başlatılamadı — " + md.hata);
        }
    }
    // Paket modüllerinin kare işleri (motor yanıtları, otomatik kayıt …) ve görünüm istekleri.
    kabuk_.H().KareIsleriniCalistir(GecenMs());
    if (kabuk_.gorunum.SigdirIstendiMi()) {
        proje_.kamera.Sigdir(ag_.enKucuk, ag_.enBuyuk);
        kabuk_.gorunum.SigdirYapildi();
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
        ka.ortam.acilisDosyasi = Utf8(s.proje);  // D devralana dek eski yol da açar (aşağıda)
        ka.ortam.senaryo = Utf8(s.senaryo);
        ka.ortam.gunluk = [](std::string_view m) { Gunluk("%.*s", static_cast<int>(m.size()), m.data()); };
        ka.moduller = StandartModuller();
        std::string kh;
        if (!kabuk_.Kur(std::move(ka), kh)) Gunluk("Uyarı: %s", kh.c_str());
        kabuk_.gorunum.SigdirYapildi();  // açılış kamerası aşağıda kurulur
    }

    AcilisEkrani acilis;
    acilis.Olustur(ornek, dizin, L"Sürüm " OP4_SURUM);
    const ULONGLONG acilisBasi = GetTickCount64();
    MotorHizmeti* motor = kabuk_.H().motor;
    if (motor && !s.motorsuz) {
        motor->durumBildirimi = [&acilis](MotorRolu, const std::string& m, float o) {
            acilis.Ilerleme(m + "…", 0.10f + 0.88f * o);
        };
        MotorAyari ma;
        ma.uygulamaDizini = Utf8(dizin);
        ma.gunlukDizini = kabuk_.H().bilgi.yerelDizin + "\\gunluk";
        motor->Baslat(ma);
    }
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
    motorAlindi_ = s.motorsuz || !motor;
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
        MsgWaitForMultipleObjects(0, nullptr, FALSE, 20, QS_ALLINPUT);
        if (motor) motor->Pompala();
        MSG msg;
        while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) cik = true;
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        const ULONGLONG gecen = GetTickCount64() - acilisBasi;
        if (cik || ((s.motorsuz || !motor || motor->Durum().hazir) && gecen > 1200) || gecen > 120000) break;
    }
    if (motor) motor->durumBildirimi = nullptr;
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
        const MotorDurumOzeti md = motor ? motor->Durum() : MotorDurumOzeti{};
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
