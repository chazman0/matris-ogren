// op4 — yerel iletişim kutuları (IletisimKutulari, sözleşme S21; D uygular): IFileDialog ve TaskDialogIndirect.
// Sahibi: D (dosya-cozum). Dosya pencereleri Windows'un kendi pencereleridir (Stüdyo §6 diyalog kuralı yerel dosya
// penceresine uygulanmaz); soru penceresi TaskDialog: başlık = ana yönerge, Türkçe düğmeler, varsayılan düğme, Esc = −1.
#include <windows.h>
#include <commctrl.h>
#include <shlobj.h>
#include <shobjidl.h>

#include <vector>

#include "dosya/dosya_win.h"

namespace op4::dosya_win {

std::wstring Genis(const std::string& s) {
    if (s.empty()) return {};
    const int n = MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), nullptr, 0);
    std::wstring w(static_cast<size_t>(n), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), w.data(), n);
    return w;
}

std::string Dar(const std::wstring& w) {
    if (w.empty()) return {};
    const int n = WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), nullptr, 0, nullptr, nullptr);
    std::string s(static_cast<size_t>(n), '\0');
    WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), s.data(), n, nullptr, nullptr);
    return s;
}

std::string TamYol(const std::string& yol) {
    const std::wstring w = Genis(yol);
    const DWORD n = GetFullPathNameW(w.c_str(), 0, nullptr, nullptr);
    if (n == 0) return yol;
    std::wstring t(n, L'\0');
    const DWORD m = GetFullPathNameW(w.c_str(), n, t.data(), nullptr);
    if (m == 0 || m >= n) return yol;
    t.resize(m);
    return Dar(t);
}

void SonBelgeEkle(const std::string& yol) {
    const std::wstring w = Genis(TamYol(yol));
    SHAddToRecentDocs(SHARD_PATHW, w.c_str());
}

namespace {

template <class T>
struct ComPtr {
    T* p = nullptr;
    ~ComPtr() {
        if (p) p->Release();
    }
    T** operator&() { return &p; }
    T* operator->() const { return p; }
    explicit operator bool() const { return p != nullptr; }
};

std::wstring Klasoru(const std::wstring& yol) {
    const size_t i = yol.find_last_of(L"\\/");
    return i == std::wstring::npos ? std::wstring() : yol.substr(0, i);
}
std::wstring Adi(const std::wstring& yol) {
    const size_t i = yol.find_last_of(L"\\/");
    return i == std::wstring::npos ? yol : yol.substr(i + 1);
}

class WinIletisimKutulari final : public IletisimKutulari {
public:
    explicit WinIletisimKutulari(std::function<void*()> sahip) : sahip_(std::move(sahip)) {}

    std::optional<std::string> DosyaAc(std::string_view baslik, const std::vector<DosyaSuzgeci>& s,
                                       std::string_view klasor) override {
        return Pencere(false, baslik, s, std::string(klasor), {});
    }
    std::optional<std::string> DosyaKaydet(std::string_view baslik, const std::vector<DosyaSuzgeci>& s,
                                           std::string_view oneri) override {
        const std::wstring w = Genis(std::string(oneri));
        return Pencere(true, baslik, s, Dar(Klasoru(w)), Adi(w));
    }

    int Soru(std::string_view baslik, std::string_view metin, const std::vector<std::string>& dugmeler,
             int varsayilan) override {
        const std::wstring b = Genis(std::string(baslik)), m = Genis(std::string(metin));
        std::vector<std::wstring> adlar;
        for (const std::string& d : dugmeler) adlar.push_back(Genis(d));
        std::vector<TASKDIALOG_BUTTON> td;
        for (size_t i = 0; i < adlar.size(); ++i) td.push_back({static_cast<int>(100 + i), adlar[i].c_str()});
        using TaskDialogIslevi = HRESULT(WINAPI*)(const TASKDIALOGCONFIG*, int*, int*, BOOL*);
        HMODULE cc = GetModuleHandleW(L"comctl32.dll");
        if (!cc) cc = LoadLibraryW(L"comctl32.dll");
        const auto islev = cc ? reinterpret_cast<TaskDialogIslevi>(reinterpret_cast<void*>(GetProcAddress(cc, "TaskDialogIndirect")))
                              : nullptr;
        HWND sahip = sahip_ ? static_cast<HWND>(sahip_()) : nullptr;
        if (islev && !td.empty()) {
            TASKDIALOGCONFIG c{};
            c.cbSize = sizeof(c);
            c.hwndParent = sahip;
            c.dwFlags = TDF_ALLOW_DIALOG_CANCELLATION | TDF_POSITION_RELATIVE_TO_WINDOW;
            c.pszWindowTitle = L"op4";
            c.pszMainIcon = TD_WARNING_ICON;
            c.pszMainInstruction = b.c_str();
            c.pszContent = m.c_str();
            c.cButtons = static_cast<UINT>(td.size());
            c.pButtons = td.data();
            c.nDefaultButton = 100 + (varsayilan >= 0 && static_cast<size_t>(varsayilan) < td.size() ? varsayilan : 0);
            int secilen = 0;
            if (SUCCEEDED(islev(&c, &secilen, nullptr, nullptr))) return secilen >= 100 ? secilen - 100 : -1;
        }
        // Yedek: MessageBoxW (Evet / Hayır / İptal ↔ düğme sırası).
        const UINT tur = dugmeler.size() >= 3 ? MB_YESNOCANCEL : dugmeler.size() == 2 ? MB_OKCANCEL : MB_OK;
        const std::wstring tam = b + L"\n\n" + m;
        const int r = MessageBoxW(sahip, tam.c_str(), L"op4", tur | MB_ICONWARNING);
        switch (r) {
            case IDYES:
            case IDOK: return 0;
            case IDNO: return 1;
            case IDCANCEL: return dugmeler.size() >= 3 ? 2 : (dugmeler.size() == 2 ? 1 : -1);
            default: return -1;
        }
    }

private:
    std::optional<std::string> Pencere(bool kaydet, std::string_view baslik, const std::vector<DosyaSuzgeci>& s,
                                       const std::string& klasor, const std::wstring& ad) {
        ComPtr<IFileDialog> d;
        if (FAILED(CoCreateInstance(kaydet ? CLSID_FileSaveDialog : CLSID_FileOpenDialog, nullptr, CLSCTX_INPROC_SERVER,
                                    IID_IFileDialog, reinterpret_cast<void**>(&d))))
            return std::nullopt;
        std::vector<std::wstring> adlar, desenler;
        for (const DosyaSuzgeci& f : s) {
            adlar.push_back(Genis(f.ad + " (" + f.desen + ")"));
            desenler.push_back(Genis(f.desen));
        }
        adlar.push_back(L"Tüm dosyalar (*.*)");
        desenler.push_back(L"*.*");
        std::vector<COMDLG_FILTERSPEC> fs;
        for (size_t i = 0; i < adlar.size(); ++i) fs.push_back({adlar[i].c_str(), desenler[i].c_str()});
        d->SetFileTypes(static_cast<UINT>(fs.size()), fs.data());
        d->SetFileTypeIndex(1);
        const std::wstring b = Genis(std::string(baslik));
        d->SetTitle(b.c_str());
        FILEOPENDIALOGOPTIONS secenek = 0;
        d->GetOptions(&secenek);
        secenek |= FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST | (kaydet ? FOS_OVERWRITEPROMPT : FOS_FILEMUSTEXIST);
        d->SetOptions(secenek);
        if (kaydet && !s.empty()) {
            std::wstring u = desenler[0];
            const size_t n = u.find(L'.');
            if (n != std::wstring::npos) u = u.substr(n + 1);
            const size_t k = u.find(L';');
            if (k != std::wstring::npos) u = u.substr(0, k);
            d->SetDefaultExtension(u.c_str());
        }
        if (!klasor.empty()) {
            ComPtr<IShellItem> k;
            const std::wstring wk = Genis(klasor);
            if (SUCCEEDED(SHCreateItemFromParsingName(wk.c_str(), nullptr, IID_IShellItem, reinterpret_cast<void**>(&k))))
                d->SetFolder(k.p);
        }
        if (!ad.empty()) d->SetFileName(ad.c_str());
        HWND sahip = sahip_ ? static_cast<HWND>(sahip_()) : nullptr;
        if (FAILED(d->Show(sahip))) return std::nullopt;  // iptal
        ComPtr<IShellItem> sonuc;
        if (FAILED(d->GetResult(&sonuc))) return std::nullopt;
        PWSTR p = nullptr;
        if (FAILED(sonuc->GetDisplayName(SIGDN_FILESYSPATH, &p)) || !p) return std::nullopt;
        const std::string yol = Dar(p);
        CoTaskMemFree(p);
        return yol;
    }

    std::function<void*()> sahip_;
};

}  // namespace

std::unique_ptr<IletisimKutulari> WinIletisimKutulariOlustur(std::function<void*()> anaPencere) {
    return std::make_unique<WinIletisimKutulari>(std::move(anaPencere));
}

}  // namespace op4::dosya_win
