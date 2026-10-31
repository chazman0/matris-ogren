// op4motor.exe — hesap motoru süreç barındırıcısı (MIMARI §8.1, D3; F1 iş 1.2, kabul A6). Sahibi: A. Yalnız Windows.
//
//   op4motor.exe --istek <tutamaç> --yanit <tutamaç> --rol ana|yardimci [--gunluk <dosya>] [--blas <n>]
//   op4motor.exe --denetle          kurulumun motor dosyalarını denetler (eksikse okunur ileti, çıkış 2)
//
// 1. Geçersiz standart tutamaçlar boşaltılır (devralınan bozuk tutamaç Python'un init_sys_streams'inde süreci sonlandırır).
// 2. <uygulama>\python\python3XX.dll, python3XX.zip, python3XX._pth ve <uygulama>\motor\op4_sunucu.py, op4_protokol.py,
//    web_kopru.py denetlenir. Eksik dosya okunur ileti + çıkış kodu 2 verir; Py_FatalError ile karşılaşılmaz.
// 3. OPENBLAS / OMP / MKL iş parçacığı sayısı: --blas, yoksa ana çekirdek − 1, yardımcı 1 (MIMARI D30).
// 4. python3XX.dll LoadLibraryExW ile yüklenir (başlık / lib gerekmez) ve
//    Py_Main([op4motor, -X, utf8, -B, -m, op4_sunucu, <aynı bağımsız değişkenler>]) çağrılır. Yalıtımı ._pth sağlar
//    (python3XX.zip, ., Lib\site-packages, ..\motor; import site yok). Python olağan yoldan başlar (sinyal işleyicileri).
// Çıkış kodları motor_protokol.h'dedir: 0 düzgün, 2 kullanım / eksik dosya, 3 protokol, 4 Python ya da web_kopru.
#include <windows.h>

#include <cwchar>
#include <string>
#include <vector>

namespace {

std::wstring ExeDizini() {
    std::wstring b(32768, L'\0');
    const DWORD n = GetModuleFileNameW(nullptr, b.data(), static_cast<DWORD>(b.size()));
    b.resize(n);
    const size_t i = b.find_last_of(L"\\/");
    return i == std::wstring::npos ? std::wstring(L".") : b.substr(0, i);
}

bool Var(const std::wstring& yol) { return GetFileAttributesW(yol.c_str()) != INVALID_FILE_ATTRIBUTES; }

void StdTemizle() {
    for (const DWORD n : {STD_INPUT_HANDLE, STD_OUTPUT_HANDLE, STD_ERROR_HANDLE}) {
        const HANDLE h = GetStdHandle(n);
        if (h == nullptr || h == INVALID_HANDLE_VALUE) continue;
        SetLastError(NO_ERROR);
        if (GetFileType(h) == FILE_TYPE_UNKNOWN && GetLastError() != NO_ERROR) SetStdHandle(n, nullptr);
    }
}

std::string Utf8(const std::wstring& w) {
    if (w.empty()) return {};
    const int n = WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), nullptr, 0, nullptr, nullptr);
    std::string s(static_cast<size_t>(n), '\0');
    WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), s.data(), n, nullptr, nullptr);
    return s;
}

// İleti: stderr'e (varsa; op4 onu sunucu günlüğüne bağlar) ve --gunluk dosyasına (UTF-8, eklenir).
void Bildir(const std::wstring& gunluk, const std::wstring& metin) {
    const std::string s = "op4motor: " + Utf8(metin) + "\r\n";
    DWORD yazilan = 0;
    if (const HANDLE h = GetStdHandle(STD_ERROR_HANDLE); h && h != INVALID_HANDLE_VALUE)
        WriteFile(h, s.data(), static_cast<DWORD>(s.size()), &yazilan, nullptr);
    if (gunluk.empty()) return;
    const HANDLE f = CreateFileW(gunluk.c_str(), FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                 nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return;
    WriteFile(f, s.data(), static_cast<DWORD>(s.size()), &yazilan, nullptr);
    CloseHandle(f);
}

// python\ içinde python3XX.dll (python3.dll kararlı ABI yönlendiricisi değil) → "3XX"; yoksa boş.
std::wstring PythonSurumu(const std::wstring& dizin) {
    WIN32_FIND_DATAW v;
    const HANDLE a = FindFirstFileW((dizin + L"\\python3*.dll").c_str(), &v);
    if (a == INVALID_HANDLE_VALUE) return {};
    std::wstring sonuc;
    do {
        const std::wstring ad = v.cFileName;  // python314.dll
        if (ad.size() > 10 && ad.size() <= 13 && _wcsicmp(ad.c_str() + ad.size() - 4, L".dll") == 0) {
            const std::wstring xy = ad.substr(6, ad.size() - 10);  // "314"
            if (xy.size() >= 2 && xy.find_first_not_of(L"0123456789") == std::wstring::npos && xy > sonuc) sonuc = xy;
        }
    } while (FindNextFileW(a, &v));
    FindClose(a);
    return sonuc;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
    StdTemizle();
    std::wstring istek, yanit, rol = L"ana", gunluk, blas;
    bool denetle = false;
    std::vector<std::wstring> ilet;  // Py_Main'e aynen iletilen bağımsız değişkenler
    for (int i = 1; i < argc; ++i) {
        const std::wstring k = argv[i];
        auto deger = [&](std::wstring& h) {
            if (i + 1 < argc) {
                h = argv[++i];
                ilet.push_back(k);
                ilet.push_back(h);
            }
        };
        if (k == L"--istek") deger(istek);
        else if (k == L"--yanit") deger(yanit);
        else if (k == L"--rol") deger(rol);
        else if (k == L"--gunluk") deger(gunluk);
        else if (k == L"--blas") deger(blas);
        else if (k == L"--denetle") denetle = true;
        else {
            Bildir(gunluk, L"bilinmeyen bağımsız değişken: " + k);
            return 2;
        }
    }
    if (!denetle && (istek.empty() || yanit.empty() || (rol != L"ana" && rol != L"yardimci"))) {
        Bildir(gunluk, L"kullanım: op4motor.exe --istek <tutamaç> --yanit <tutamaç> --rol ana|yardimci [--gunluk <dosya>] "
                       L"[--blas <n>] | --denetle (op4 hesap motoru; op4.exe tarafından başlatılır)");
        return 2;
    }
    const std::wstring dizin = ExeDizini();
    const std::wstring py = dizin + L"\\python", motor = dizin + L"\\motor";
    const std::wstring xy = PythonSurumu(py);
    std::wstring eksik;
    if (xy.empty()) eksik += L"\n  " + py + L"\\python3XX.dll";
    std::vector<std::wstring> gerekli = {motor + L"\\op4_sunucu.py", motor + L"\\op4_protokol.py", motor + L"\\web_kopru.py"};
    if (!xy.empty()) {
        gerekli.push_back(py + L"\\python" + xy + L".zip");
        gerekli.push_back(py + L"\\python" + xy + L"._pth");
    }
    for (const std::wstring& g : gerekli)
        if (!Var(g)) eksik += L"\n  " + g;
    if (!eksik.empty()) {
        Bildir(gunluk, L"hesap motoru dosyaları eksik (kurulumu onarın: op4-setup'ı yeniden çalıştırın):" + eksik);
        return 2;
    }
    if (denetle) {
        Bildir(gunluk, L"motor dosyaları tamam: Python " + xy.substr(0, 1) + L"." + xy.substr(1) + L", " + py);
        return 0;
    }
    // BLAS iş parçacıkları numpy yüklenmeden önce (Python da --blas ile aynısını yapar).
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    int n = blas.empty() ? 0 : _wtoi(blas.c_str());
    if (n <= 0) n = rol == L"ana" ? (si.dwNumberOfProcessors > 1 ? static_cast<int>(si.dwNumberOfProcessors) - 1 : 1) : 1;
    const std::wstring ns = std::to_wstring(n);
    for (const wchar_t* ad : {L"OPENBLAS_NUM_THREADS", L"OMP_NUM_THREADS", L"MKL_NUM_THREADS"}) SetEnvironmentVariableW(ad, ns.c_str());

    const std::wstring dll = py + L"\\python" + xy + L".dll";
    const HMODULE m = LoadLibraryExW(dll.c_str(), nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!m) {
        Bildir(gunluk, L"Python DLL yüklenemedi: " + dll + L" (Windows hata kodu " + std::to_wstring(GetLastError()) + L")");
        return 4;
    }
    using PyMainIslevi = int (*)(int, wchar_t**);
    const auto py_main = reinterpret_cast<PyMainIslevi>(reinterpret_cast<void*>(GetProcAddress(m, "Py_Main")));
    if (!py_main) {
        Bildir(gunluk, L"Python DLL'inde Py_Main yok: " + dll);
        return 4;
    }
    std::vector<std::wstring> a = {argv[0], L"-X", L"utf8", L"-B", L"-m", L"op4_sunucu"};
    a.insert(a.end(), ilet.begin(), ilet.end());
    std::vector<wchar_t*> pa;
    for (std::wstring& s : a) pa.push_back(s.data());
    pa.push_back(nullptr);
    return py_main(static_cast<int>(a.size()), pa.data());
}
