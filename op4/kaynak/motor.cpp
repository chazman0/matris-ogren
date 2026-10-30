#include "motor.h"

#include <cstdint>
#include <cstdio>

#include "gunluk.h"

namespace op4 {
namespace {

// --- CPython C API'sinin kullanılan bölümü (çalışma anında çözülür) ------------------------------------------------
struct PyObject;  // saydam
using Py_ssize_t = intptr_t;

struct PyApi {
    HMODULE dll = nullptr;
    void (*Py_InitializeEx)(int) = nullptr;
    int (*Py_IsInitialized)() = nullptr;
    int (*Py_FinalizeEx)() = nullptr;
    const char* (*Py_GetVersion)() = nullptr;
    PyObject* (*PyImport_ImportModule)(const char*) = nullptr;
    PyObject* (*PyObject_GetAttrString)(PyObject*, const char*) = nullptr;
    PyObject* (*PyObject_CallObject)(PyObject*, PyObject*) = nullptr;
    PyObject* (*PyObject_Str)(PyObject*) = nullptr;
    PyObject* (*PyTuple_Pack)(Py_ssize_t, ...) = nullptr;
    PyObject* (*PyUnicode_FromString)(const char*) = nullptr;
    const char* (*PyUnicode_AsUTF8AndSize)(PyObject*, Py_ssize_t*) = nullptr;
    PyObject* (*PyUnicode_Join)(PyObject*, PyObject*) = nullptr;
    PyObject* (*PyDict_GetItemString)(PyObject*, const char*) = nullptr;  // ödünç başvuru
    Py_ssize_t (*PyList_Size)(PyObject*) = nullptr;
    PyObject* (*PyList_GetItem)(PyObject*, Py_ssize_t) = nullptr;         // ödünç başvuru
    void (*Py_DecRef)(PyObject*) = nullptr;
    PyObject* (*PyErr_Occurred)() = nullptr;
    void (*PyErr_Fetch)(PyObject**, PyObject**, PyObject**) = nullptr;
    void (*PyErr_NormalizeException)(PyObject**, PyObject**, PyObject**) = nullptr;
    int (*PyException_SetTraceback)(PyObject*, PyObject*) = nullptr;
    void (*PyErr_Clear)() = nullptr;
    PyObject* None = nullptr;  // _Py_NoneStruct (veri dışa aktarımı)

    template <typename T>
    bool Coz(T& f, const char* ad, std::string& eksik) {
        f = reinterpret_cast<T>(reinterpret_cast<void*>(GetProcAddress(dll, ad)));
        if (!f) eksik += std::string(eksik.empty() ? "" : ", ") + ad;
        return f != nullptr;
    }

    bool Yukle(const std::wstring& yol, std::string& hata) {
        // LOAD_WITH_ALTERED_SEARCH_PATH: python3XX.dll'in bağımlılıkları (vcruntime140.dll …) kendi klasöründe aranır.
        dll = LoadLibraryExW(yol.c_str(), nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
        if (!dll) {
            char b[64];
            std::snprintf(b, sizeof(b), " (Windows hata kodu %lu)", GetLastError());
            hata = "Python DLL yüklenemedi: " + Utf8(yol) + b;
            return false;
        }
        std::string eksik;
        Coz(Py_InitializeEx, "Py_InitializeEx", eksik);
        Coz(Py_IsInitialized, "Py_IsInitialized", eksik);
        Coz(Py_FinalizeEx, "Py_FinalizeEx", eksik);
        Coz(Py_GetVersion, "Py_GetVersion", eksik);
        Coz(PyImport_ImportModule, "PyImport_ImportModule", eksik);
        Coz(PyObject_GetAttrString, "PyObject_GetAttrString", eksik);
        Coz(PyObject_CallObject, "PyObject_CallObject", eksik);
        Coz(PyObject_Str, "PyObject_Str", eksik);
        Coz(PyTuple_Pack, "PyTuple_Pack", eksik);
        Coz(PyUnicode_FromString, "PyUnicode_FromString", eksik);
        Coz(PyUnicode_AsUTF8AndSize, "PyUnicode_AsUTF8AndSize", eksik);
        Coz(PyUnicode_Join, "PyUnicode_Join", eksik);
        Coz(PyDict_GetItemString, "PyDict_GetItemString", eksik);
        Coz(PyList_Size, "PyList_Size", eksik);
        Coz(PyList_GetItem, "PyList_GetItem", eksik);
        Coz(Py_DecRef, "Py_DecRef", eksik);
        Coz(PyErr_Occurred, "PyErr_Occurred", eksik);
        Coz(PyErr_Fetch, "PyErr_Fetch", eksik);
        Coz(PyErr_NormalizeException, "PyErr_NormalizeException", eksik);
        Coz(PyException_SetTraceback, "PyException_SetTraceback", eksik);
        Coz(PyErr_Clear, "PyErr_Clear", eksik);
        None = reinterpret_cast<PyObject*>(GetProcAddress(dll, "_Py_NoneStruct"));
        if (!None) eksik += ", _Py_NoneStruct";
        if (!eksik.empty()) {
            hata = "Python DLL'inde beklenen işlevler yok: " + eksik;
            return false;
        }
        return true;
    }
};

// Sahipli başvuru sarmalayıcısı.
class Ref {
public:
    Ref(PyApi& api, PyObject* p) : api_(api), p_(p) {}
    ~Ref() {
        if (p_) api_.Py_DecRef(p_);
    }
    Ref(const Ref&) = delete;
    Ref& operator=(const Ref&) = delete;
    PyObject* get() const { return p_; }
    explicit operator bool() const { return p_ != nullptr; }
    void Birak() {  // Py_FinalizeEx'ten ÖNCE çağrılmalı (sonra Py_DecRef erişim ihlali verir)
        if (p_) api_.Py_DecRef(p_);
        p_ = nullptr;
    }

private:
    PyApi& api_;
    PyObject* p_;
};

std::string Metin(PyApi& api, PyObject* o) {
    if (!o) return {};
    Py_ssize_t n = 0;
    const char* s = api.PyUnicode_AsUTF8AndSize(o, &n);
    if (!s) {
        api.PyErr_Clear();
        return {};
    }
    return std::string(s, static_cast<size_t>(n));
}

// Bekleyen Python hatasını tam geri izleme (traceback) metnine çevirir ve temizler.
std::string HataMetni(PyApi& api) {
    PyObject *tur = nullptr, *deger = nullptr, *iz = nullptr;
    api.PyErr_Fetch(&tur, &deger, &iz);
    if (!tur) return "bilinmeyen Python hatası";
    api.PyErr_NormalizeException(&tur, &deger, &iz);
    if (deger && iz) api.PyException_SetTraceback(deger, iz);
    std::string sonuc;
    {
        Ref tb(api, api.PyImport_ImportModule("traceback"));
        Ref bicimle(api, tb ? api.PyObject_GetAttrString(tb.get(), "format_exception") : nullptr);
        Ref argumanlar(api, (bicimle && deger) ? api.PyTuple_Pack(1, deger) : nullptr);
        Ref satirlar(api, argumanlar ? api.PyObject_CallObject(bicimle.get(), argumanlar.get()) : nullptr);
        Ref bos(api, api.PyUnicode_FromString(""));
        Ref birlesik(api, (satirlar && bos) ? api.PyUnicode_Join(bos.get(), satirlar.get()) : nullptr);
        sonuc = Metin(api, birlesik.get());
    }
    if (sonuc.empty() && deger) {
        api.PyErr_Clear();
        Ref s(api, api.PyObject_Str(deger));
        sonuc = Metin(api, s.get());
    }
    api.PyErr_Clear();
    if (tur) api.Py_DecRef(tur);
    if (deger) api.Py_DecRef(deger);
    if (iz) api.Py_DecRef(iz);
    return sonuc.empty() ? "Python hatası (ayrıntı alınamadı)" : sonuc;
}

bool DosyaVar(const std::wstring& yol) {
    DWORD a = GetFileAttributesW(yol.c_str());
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

// python\ içindeki python3XX.dll (python3.dll kararlı ABI yönlendiricisidir, atlanır).
std::wstring PythonDllBul(const std::wstring& pythonDizini) {
    WIN32_FIND_DATAW v;
    HANDLE h = FindFirstFileW((pythonDizini + L"\\python3*.dll").c_str(), &v);
    std::wstring bulunan;
    if (h == INVALID_HANDLE_VALUE) return bulunan;
    do {
        std::wstring ad = v.cFileName;
        if (_wcsicmp(ad.c_str(), L"python3.dll") != 0) bulunan = ad;
    } while (bulunan.empty() && FindNextFileW(h, &v));
    FindClose(h);
    return bulunan.empty() ? bulunan : pythonDizini + L"\\" + bulunan;
}

// Python, başlarken 0/1/2 tanımlayıcılarından sys.stdin/stdout/stderr kurar: tutamaç YOKSA (Gezgin'den açılan GUI
// süreci) bunları None yapar, ama tutamaç GEÇERSİZSE (üst süreçten bozuk / kapanmış tutamaç devralınmışsa)
// "init_sys_streams: can't initialize sys standard streams" ile süreci sonlandırır (Py_FatalError). Python DLL'i
// yüklenmeden önce geçersiz standart tutamaçlar boşaltılır; Python'un C çalışma zamanı (ucrtbase) tanımlayıcı tablosunu
// ilk yüklendiğinde bu tutamaçlardan kurar.
void StandartTutamaclariTemizle() {
    const DWORD kimlikler[] = {STD_INPUT_HANDLE, STD_OUTPUT_HANDLE, STD_ERROR_HANDLE};
    std::string ozet;
    for (int i = 0; i < 3; ++i) {
        HANDLE h = GetStdHandle(kimlikler[i]);
        char b[48];
        if (h == nullptr || h == INVALID_HANDLE_VALUE) {
            std::snprintf(b, sizeof(b), " %d:yok", i);
        } else {
            SetLastError(NO_ERROR);
            DWORD tur = GetFileType(h);
            DWORD hata = GetLastError();
            if (tur == FILE_TYPE_UNKNOWN && hata != NO_ERROR) {
                SetStdHandle(kimlikler[i], nullptr);
                std::snprintf(b, sizeof(b), " %d:geçersiz(%lu)→boşaltıldı", i, hata);
            } else {
                std::snprintf(b, sizeof(b), " %d:tür%lu", i, tur);
            }
        }
        ozet += b;
    }
    Gunluk("Motor: standart tutamaçlar%s; ucrtbase %s", ozet.c_str(),
           GetModuleHandleW(L"ucrtbase.dll") ? "önceden yüklü" : "yüklü değil");
}

}  // namespace

Motor::~Motor() {
    Durdur();
    if (hazirOlayi_) CloseHandle(hazirOlayi_);
}

void Motor::Baslat(const std::wstring& uygulamaDizini, Ilerleme ilerleme) {
    if (is_.joinable()) return;
    is_ = std::thread(&Motor::Calis, this, uygulamaDizini, std::move(ilerleme));
}

bool Motor::Bekle(DWORD ms) { return WaitForSingleObject(hazirOlayi_, ms) == WAIT_OBJECT_0; }

MotorDurumu Motor::Durum() const {
    std::lock_guard<std::mutex> k(kilit_);
    return durum_;
}

std::string Motor::Calistir(const std::string& istekJson) {
    Is is;
    is.istek = istekJson;
    std::future<std::string> f = is.yanit.get_future();
    {
        std::lock_guard<std::mutex> k(kilit_);
        if (!durum_.basarili || dur_) return R"({"hata": "Hesap motoru hazır değil.", "hata_turu": "ic"})";
        kuyruk_.push_back(&is);
    }
    kosul_.notify_one();
    return f.get();
}

void Motor::Durdur() {
    {
        std::lock_guard<std::mutex> k(kilit_);
        dur_ = true;
    }
    kosul_.notify_all();
    if (is_.joinable()) is_.join();
}

void Motor::Calis(std::wstring dizin, Ilerleme ilerleme) {
    const double t0 = GecenMs();
    PyApi api;
    MotorDurumu d;
    auto bildir = [&](const std::string& m, float o) {
        Gunluk("Motor: %s", m.c_str());
        if (ilerleme) ilerleme(m, o);
    };
    auto bitir = [&](bool basarili, const std::string& hata) {
        d.hazir = true;
        d.basarili = basarili;
        d.hata = hata;
        d.msToplam = GecenMs() - t0;
        if (!basarili) Gunluk("Motor HATASI: %s", hata.c_str());
        {
            std::lock_guard<std::mutex> k(kilit_);
            durum_ = d;
        }
        SetEvent(hazirOlayi_);
    };

    const std::wstring pyDizin = dizin + L"\\python";
    bildir("Gömülü Python aranıyor", 0.05f);
    std::wstring dll = PythonDllBul(pyDizin);
    if (dll.empty()) return bitir(false, "Gömülü Python bulunamadı: " + Utf8(pyDizin) + "\\python3XX.dll yok.");
    // Eksik standart kitaplıkla Py_InitializeEx süreci sonlandırır (Py_FatalError); önce dosyaları denetle.
    std::wstring kok = dll.substr(0, dll.size() - 4);  // ...\python313
    for (const wchar_t* ek : {L".zip", L"._pth"})
        if (!DosyaVar(kok + ek)) return bitir(false, "Gömülü Python eksik: " + Utf8(kok + ek) + " yok.");
    if (!DosyaVar(dizin + L"\\motor\\web_kopru.py"))
        return bitir(false, "Hesap motoru dosyaları eksik: " + Utf8(dizin) + "\\motor\\web_kopru.py yok.");

    StandartTutamaclariTemizle();
    double t = GecenMs();
    std::string hata;
    if (!api.Yukle(dll, hata)) return bitir(false, hata);
    d.msDll = GecenMs() - t;
    d.pythonSurumu = api.Py_GetVersion();
    bildir("Python " + d.pythonSurumu.substr(0, d.pythonSurumu.find(' ')) + " başlatılıyor", 0.15f);

    t = GecenMs();
    api.Py_InitializeEx(0);  // sinyal işleyicileri kurulmaz (gömülü kullanım)
    d.msBaslat = GecenMs() - t;
    if (!api.Py_IsInitialized()) return bitir(false, "Python yorumlayıcısı başlatılamadı.");

    bildir("Hesap motoru yükleniyor (numpy, sympy, web_kopru)", 0.35f);
    t = GecenMs();
    PyObject* kopru = api.PyImport_ImportModule("web_kopru");
    d.msIceAktar = GecenMs() - t;
    if (!kopru) {
        std::string h = HataMetni(api);
        api.Py_FinalizeEx();
        return bitir(false, "web_kopru içe aktarılamadı:\n" + h);
    }
    Ref surumF(api, api.PyObject_GetAttrString(kopru, "surum_json"));
    PyObject* calistirF = api.PyObject_GetAttrString(kopru, "calistir");
    Ref jsonMod(api, api.PyImport_ImportModule("json"));
    Ref yukleF(api, jsonMod ? api.PyObject_GetAttrString(jsonMod.get(), "loads") : nullptr);
    if (!surumF || !calistirF || !yukleF) {
        std::string h = HataMetni(api);
        return bitir(false, "web_kopru beklenen işlevleri içermiyor: " + h);
    }

    bildir("Motor sürümü okunuyor", 0.75f);
    t = GecenMs();
    {
        Ref r(api, api.PyObject_CallObject(surumF.get(), nullptr));
        if (!r) return bitir(false, "surum_json() hatası:\n" + HataMetni(api));
        d.surumJson = Metin(api, r.get());
    }
    d.msSurum = GecenMs() - t;

    auto cagir = [&](const std::string& istek, std::string& yanit) -> bool {
        Ref arg(api, api.PyUnicode_FromString(istek.c_str()));
        Ref argumanlar(api, arg ? api.PyTuple_Pack(1, arg.get()) : nullptr);
        Ref r(api, argumanlar ? api.PyObject_CallObject(calistirF, argumanlar.get()) : nullptr);
        if (!r) {
            yanit = HataMetni(api);
            return false;
        }
        yanit = Metin(api, r.get());
        return true;
    };

    bildir("Yapı şablonları okunuyor (bina_sablonlar)", 0.88f);
    t = GecenMs();
    if (!cagir(R"({"islem":"bina_sablonlar","girdi":{}})", d.sablonlarJson))
        return bitir(false, "calistir(bina_sablonlar) hatası:\n" + d.sablonlarJson);
    d.msSablon = GecenMs() - t;
    {
        // Yanıtı Python'un json modülüyle çözümle: {"sablonlar": [...], "hata": null}
        Ref a(api, api.PyUnicode_FromString(d.sablonlarJson.c_str()));
        Ref aa(api, a ? api.PyTuple_Pack(1, a.get()) : nullptr);
        Ref sozluk(api, aa ? api.PyObject_CallObject(yukleF.get(), aa.get()) : nullptr);
        if (!sozluk) return bitir(false, "bina_sablonlar yanıtı JSON değil:\n" + HataMetni(api));
        PyObject* hataAlani = api.PyDict_GetItemString(sozluk.get(), "hata");
        if (hataAlani && hataAlani != api.None) {
            Ref s(api, api.PyObject_Str(hataAlani));
            return bitir(false, "bina_sablonlar hata döndürdü: " + Metin(api, s.get()));
        }
        PyObject* liste = api.PyDict_GetItemString(sozluk.get(), "sablonlar");
        if (!liste) return bitir(false, "bina_sablonlar yanıtında \"sablonlar\" yok.");
        d.sablonSayisi = static_cast<int>(api.PyList_Size(liste));
        for (Py_ssize_t i = 0; i < d.sablonSayisi; ++i) {
            PyObject* oge = api.PyList_GetItem(liste, i);
            PyObject* ad = oge ? api.PyDict_GetItemString(oge, "ad") : nullptr;
            d.sablonAdlari.push_back(ad ? Metin(api, ad) : std::string("?"));
        }
        api.PyErr_Clear();
    }
    bitir(true, std::string());
    bildir("Hazır", 1.0f);

    // İstek döngüsü.
    for (;;) {
        Is* is = nullptr;
        {
            std::unique_lock<std::mutex> k(kilit_);
            kosul_.wait(k, [&] { return dur_ || !kuyruk_.empty(); });
            if (dur_ && kuyruk_.empty()) break;
            is = kuyruk_.front();
            kuyruk_.pop_front();
        }
        std::string yanit;
        if (!cagir(is->istek, yanit)) yanit = R"({"hata": "Python hatası", "hata_turu": "ic"})";
        is->yanit.set_value(std::move(yanit));
    }
    // Tüm başvurular yorumlayıcı kapanmadan bırakılır; Ref yıkıcıları Py_FinalizeEx'ten sonra çalışırsa çöker.
    surumF.Birak();
    yukleF.Birak();
    jsonMod.Birak();
    api.Py_DecRef(calistirF);
    api.Py_DecRef(kopru);
    double tk = GecenMs();
    int fin = api.Py_FinalizeEx();
    Gunluk("Motor: yorumlayıcı kapatıldı (Py_FinalizeEx = %d, %.1f ms)", fin, GecenMs() - tk);
}

}  // namespace op4
