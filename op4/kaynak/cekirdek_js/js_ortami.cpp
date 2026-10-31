// op4 model çekirdeği — QuickJS-ng çalışma ortamı (MIMARI §9.2; kabul B2). Uygulayan: B (model-cekirdegi).
#include "cekirdek_js/js_ortami.h"

#include <chrono>
#include <cstring>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <utility>

#include "cekirdek_js/js_gomulu.h"
#include "cekirdek_js/js_ortami_ic.h"

namespace op4 {

struct JsOrtami::Ic {
    JsOrtamiAyari ayar;
    JSRuntime* rt = nullptr;
    JSContext* c = nullptr;
    double derlemeMs = 0;
    std::vector<std::string> dosyalar;
    size_t bayt = 0;
    bool sinirVar = false;
    std::chrono::steady_clock::time_point sinir{};
    // structuredClone için önbellek (Kur'da alınır, yıkıcıda bırakılır)
    JSValue kurucular[5] = {JS_UNDEFINED, JS_UNDEFINED, JS_UNDEFINED, JS_UNDEFINED, JS_UNDEFINED};  // Map Set WeakMap WeakSet RegExp
};

namespace {

using Saat = std::chrono::steady_clock;

int Kesme(JSRuntime*, void* opak) {
    const auto* ic = static_cast<const JsOrtami::Ic*>(opak);
    return ic->sinirVar && Saat::now() > ic->sinir ? 1 : 0;
}

JsOrtami::Ic* IcAl(JSContext* c) { return static_cast<JsOrtami::Ic*>(JS_GetContextOpaque(c)); }

// __op4_gunluk(düzey, metin)
JSValue JsGunluk(JSContext* c, JSValueConst, int argc, JSValueConst* argv) {
    JsOrtami::Ic* ic = IcAl(c);
    const std::string duzey = argc > 0 ? js::Metin(c, argv[0]) : std::string("bilgi");
    const std::string metin = argc > 1 ? js::Metin(c, argv[1]) : std::string();
    if (ic && ic->ayar.gunluk) ic->ayar.gunluk("[js " + duzey + "] " + metin);
    return JS_UNDEFINED;
}

// ---- structuredClone (C++; HTML yapısal kopya algoritmasının model verisi için gereken kısmı) ----------------------------
// Desteklenen: ilkel değerler, Array, düz nesne (ve sınıf örnekleri: kendi sayılabilir dize anahtarlı özellikleri, düz nesne
// olarak — V8 ile aynı), Date, ArrayBuffer, tipli diziler. Paylaşılan alt nesneler ve döngüler korunur. İşlev, Symbol, Map,
// Set, WeakMap, WeakSet, RegExp → DataCloneError (sessizce bozulmaz).
struct Klon {
    JSContext* c;
    JsOrtami::Ic* ic;
    std::unordered_map<void*, JSValue> gorulen;  // kaynak nesne → kopya (sahipsiz)
    int derinlik = 0;
};

JSValue KlonHata(JSContext* c, const char* neden) {
    return JS_ThrowDOMException(c, "DataCloneError", "structuredClone: %s kopyalanamaz", neden);
}

JSValue Kopyala(Klon& k, JSValueConst v) {
    JSContext* c = k.c;
    if (!JS_IsObject(v)) {
        if (JS_IsSymbol(v)) return KlonHata(c, "Symbol");
        return JS_DupValue(c, v);
    }
    if (JS_IsFunction(c, v)) return KlonHata(c, "işlev");
    void* ptr = JS_VALUE_GET_PTR(v);
    if (const auto i = k.gorulen.find(ptr); i != k.gorulen.end()) return JS_DupValue(c, i->second);
    // Yerel yığın: Windows ana iş parçacığı 1 MB; QuickJS'e 640 KB ayrılır (Kur). 1000 düzey ≈ 250 KB (model verisi < 20 düzey).
    if (++k.derinlik > 1000) {
        --k.derinlik;
        return JS_ThrowRangeError(c, "structuredClone: nesne çok derin");
    }
    struct Cikis {
        Klon& k;
        ~Cikis() { --k.derinlik; }
    } cikis{k};

    const int ta = JS_GetTypedArrayType(v);
    if (ta >= 0) {
        size_t ofset = 0, uzunluk = 0, eb = 0;
        js::Deger tampon(c, JS_GetTypedArrayBuffer(c, v, &ofset, &uzunluk, &eb));
        if (tampon.Istisna()) return JS_EXCEPTION;
        size_t boyut = 0;
        uint8_t* p = JS_GetArrayBuffer(c, &boyut, tampon.v());
        if (!p && uzunluk) return JS_EXCEPTION;
        js::Deger yeni(c, JS_NewArrayBufferCopy(c, p ? p + ofset : nullptr, uzunluk));
        if (yeni.Istisna()) return JS_EXCEPTION;
        JSValue arg[3] = {yeni.v(), JS_NewInt32(c, 0), JS_NewInt64(c, static_cast<int64_t>(eb ? uzunluk / eb : 0))};
        JSValue r = JS_NewTypedArray(c, 3, arg, static_cast<JSTypedArrayEnum>(ta));
        if (!JS_IsException(r)) k.gorulen.emplace(ptr, r);
        return r;
    }
    if (JS_IsArrayBuffer(v)) {
        size_t boyut = 0;
        uint8_t* p = JS_GetArrayBuffer(c, &boyut, v);
        JSValue r = JS_NewArrayBufferCopy(c, p, boyut);
        if (!JS_IsException(r)) k.gorulen.emplace(ptr, r);
        return r;
    }
    if (JS_IsDate(v)) {
        double t = 0;
        if (JS_ToFloat64(c, &t, v) < 0) return JS_EXCEPTION;
        JSValue r = JS_NewDate(c, t);
        if (!JS_IsException(r)) k.gorulen.emplace(ptr, r);
        return r;
    }
    if (JS_IsArray(v)) {
        int64_t n = 0;
        if (JS_GetLength(c, v, &n) < 0) return JS_EXCEPTION;
        JSValue d = JS_NewArray(c);
        if (JS_IsException(d)) return d;
        k.gorulen.emplace(ptr, d);
        for (int64_t i = 0; i < n; ++i) {
            js::Deger e(c, JS_GetPropertyUint32(c, v, static_cast<uint32_t>(i)));
            if (e.Istisna()) { JS_FreeValue(c, d); return JS_EXCEPTION; }
            JSValue x = Kopyala(k, e.v());
            if (JS_IsException(x) ||
                JS_DefinePropertyValueUint32(c, d, static_cast<uint32_t>(i), x, JS_PROP_C_W_E) < 0) {
                JS_FreeValue(c, d);
                return JS_EXCEPTION;
            }
        }
        return d;
    }
    for (const JSValue& kur : k.ic->kurucular) {
        if (!JS_IsUndefined(kur)) {
            const int s = JS_IsInstanceOf(c, v, kur);
            if (s < 0) return JS_EXCEPTION;
            if (s > 0) return KlonHata(c, "Map / Set / WeakMap / WeakSet / RegExp");
        }
    }
    JSValue d = JS_NewObject(c);
    if (JS_IsException(d)) return d;
    k.gorulen.emplace(ptr, d);
    JSPropertyEnum* tab = nullptr;
    uint32_t n = 0;
    if (JS_GetOwnPropertyNames(c, &tab, &n, v, JS_GPN_STRING_MASK | JS_GPN_ENUM_ONLY) < 0) {
        JS_FreeValue(c, d);
        return JS_EXCEPTION;
    }
    bool tamam = true;
    for (uint32_t i = 0; i < n && tamam; ++i) {
        js::Deger e(c, JS_GetProperty(c, v, tab[i].atom));
        if (e.Istisna()) { tamam = false; break; }
        JSValue x = Kopyala(k, e.v());
        if (JS_IsException(x) || JS_DefinePropertyValue(c, d, tab[i].atom, x, JS_PROP_C_W_E) < 0) tamam = false;
    }
    JS_FreePropertyEnum(c, tab, n);
    if (!tamam) {
        JS_FreeValue(c, d);
        return JS_EXCEPTION;
    }
    return d;
}

JSValue JsKlon(JSContext* c, JSValueConst, int argc, JSValueConst* argv) {
    Klon k{c, IcAl(c), {}, 0};
    return Kopyala(k, argc > 0 ? argv[0] : JS_UNDEFINED);
}

bool DosyaOkuIkili(const std::string& yol, std::string& icerik) {
    std::ifstream f(yol, std::ios::binary);
    if (!f) return false;
    std::ostringstream s;
    s << f.rdbuf();
    icerik = s.str();
    return true;
}

void KuresElKoy(JSContext* c, const char* ad, JSValue v) {
    js::Deger g(c, JS_GetGlobalObject(c));
    JS_SetPropertyStr(c, g.v(), ad, v);
}

}  // namespace

// ---- js:: yardımcıları --------------------------------------------------------------------------------------------------
namespace js {

JSContext* Baglam(const JsOrtami& o) { return static_cast<JSContext*>(o.Baglam()); }

std::string Metin(JSContext* c, JSValueConst v) {
    size_t n = 0;
    const char* s = JS_ToCStringLen(c, &n, v);
    if (!s) {
        JS_FreeValue(c, JS_GetException(c));
        return {};
    }
    std::string r(s, n);
    JS_FreeCString(c, s);
    return r;
}

std::string IstisnaMetni(JSContext* c) {
    JSValue e = JS_GetException(c);
    std::string m;
    if (JS_IsError(e)) {
        Deger ad(c, JS_GetPropertyStr(c, e, "name")), ileti(c, JS_GetPropertyStr(c, e, "message")),
            yigin(c, JS_GetPropertyStr(c, e, "stack"));
        m = Metin(c, ad.v()) + ": " + Metin(c, ileti.v());
        if (!yigin.Tanimsiz()) {
            const std::string y = Metin(c, yigin.v());
            if (!y.empty()) m += "\n" + y;
        }
    } else if (JS_IsUninitialized(e)) {
        m = "bilinmeyen istisna";
    } else {
        m = Metin(c, e);
        if (m == "null" || m.empty()) m = "kesildi (süre sınırı ya da iç hata)";
    }
    JS_FreeValue(c, e);
    return m;
}

void CagriBasla(const JsOrtami& o) {
    JsOrtami::Ic* ic = IcAl(Baglam(o));
    JS_UpdateStackTop(ic->rt);
    ic->sinirVar = ic->ayar.cagriSiniriSn > 0;
    if (ic->sinirVar)
        ic->sinir = Saat::now() + std::chrono::duration_cast<Saat::duration>(std::chrono::duration<double>(ic->ayar.cagriSiniriSn));
}

Deger Cagir(const JsOrtami& o, std::string_view yol, const std::vector<std::string_view>& arg, std::string& hata) {
    JSContext* c = Baglam(o);
    CagriBasla(o);
    Deger sahip(c, JS_GetGlobalObject(c));
    Deger islev(c, JS_DupValue(c, sahip.v()));
    size_t bas = 0;
    while (bas <= yol.size()) {
        const size_t son = yol.find('.', bas);
        const std::string parca(yol.substr(bas, son == std::string_view::npos ? std::string_view::npos : son - bas));
        Deger sonraki(c, JS_GetPropertyStr(c, islev.v(), parca.c_str()));
        if (sonraki.Istisna()) {
            hata = IstisnaMetni(c);
            return Deger(c, JS_EXCEPTION);
        }
        sahip = std::move(islev);
        islev = std::move(sonraki);
        if (son == std::string_view::npos) break;
        bas = son + 1;
    }
    if (!JS_IsFunction(c, islev.v())) {
        hata = "JS işlevi yok: " + std::string(yol);
        return Deger(c, JS_EXCEPTION);
    }
    std::vector<JSValue> a;
    a.reserve(arg.size());
    for (const std::string_view s : arg) a.push_back(JS_NewStringLen(c, s.data(), s.size()));
    JSValue r = JS_Call(c, islev.v(), sahip.v(), static_cast<int>(a.size()), a.data());
    for (JSValue& x : a) JS_FreeValue(c, x);
    IcAl(c)->sinirVar = false;
    if (JS_IsException(r)) hata = IstisnaMetni(c);
    return Deger(c, r);
}

bool TipliDizi(JSContext* c, JSValueConst nesne, const char* ad, JSTypedArrayEnum tur, TipliGorunum& g, std::string& hata) {
    Deger d(c, JS_GetPropertyStr(c, nesne, ad));
    if (d.Istisna()) {
        hata = std::string(ad) + ": " + IstisnaMetni(c);
        return false;
    }
    if (JS_GetTypedArrayType(d.v()) != static_cast<int>(tur)) {
        hata = std::string(ad) + ": beklenen tipli dizi değil";
        return false;
    }
    size_t ofset = 0, uzunluk = 0, eb = 0;
    g.tampon = Deger(c, JS_GetTypedArrayBuffer(c, d.v(), &ofset, &uzunluk, &eb));
    if (g.tampon.Istisna()) {
        hata = std::string(ad) + ": " + IstisnaMetni(c);
        return false;
    }
    size_t boyut = 0;
    const uint8_t* p = JS_GetArrayBuffer(c, &boyut, g.tampon.v());
    if ((!p && uzunluk) || ofset + uzunluk > boyut || eb == 0) {
        hata = std::string(ad) + ": tipli dizi belleği okunamadı";
        return false;
    }
    g.veri = p ? p + ofset : nullptr;
    g.adet = uzunluk / eb;
    return true;
}

}  // namespace js

// ---- JsOrtami -----------------------------------------------------------------------------------------------------------
JsOrtami::JsOrtami(JsOrtamiAyari ayar) : ic_(std::make_unique<Ic>()) { ic_->ayar = std::move(ayar); }

JsOrtami::~JsOrtami() {
    if (ic_->c) {
        for (JSValue& k : ic_->kurucular) JS_FreeValue(ic_->c, k);
        JS_FreeContext(ic_->c);
    }
    if (ic_->rt) JS_FreeRuntime(ic_->rt);
}

bool JsOrtami::Kur(std::string& hata) {
    Ic& i = *ic_;
    i.rt = JS_NewRuntime();
    if (!i.rt) {
        hata = "QuickJS çalışma zamanı kurulamadı";
        return false;
    }
    size_t sinir = i.ayar.bellekSiniri;
    if (sinir == 0) sinir = sizeof(void*) >= 8 ? size_t(3) * 1024 * 1024 * 1024 : size_t(1536) * 1024 * 1024;
    JS_SetMemoryLimit(i.rt, sinir);
#if defined(_WIN32)
    JS_SetMaxStackSize(i.rt, 3 * 1024 * 1024);  // op4.exe ve sınama ikilisi 4 MB yığınla bağlanır (CMakeLists, OP4_YIGIN)
#else
    JS_SetMaxStackSize(i.rt, 4 * 1024 * 1024);
#endif
    JS_SetInterruptHandler(i.rt, &Kesme, &i);
    i.c = JS_NewContext(i.rt);
    if (!i.c) {
        hata = "QuickJS bağlamı kurulamadı";
        return false;
    }
    JS_SetContextOpaque(i.c, &i);
    JSContext* c = i.c;
    KuresElKoy(c, "__op4_gunluk", JS_NewCFunction(c, &JsGunluk, "__op4_gunluk", 2));
    KuresElKoy(c, "__op4_klon", JS_NewCFunction(c, &JsKlon, "structuredClone", 1));
    KuresElKoy(c, "__op4_deterministik", JS_NewBool(c, i.ayar.deterministikSaat));
    {
        js::Deger g(c, JS_GetGlobalObject(c));
        const char* adlar[5] = {"Map", "Set", "WeakMap", "WeakSet", "RegExp"};
        for (int k = 0; k < 5; ++k) i.kurucular[k] = JS_GetPropertyStr(c, g.v(), adlar[k]);
    }

    size_t n = 0;
    const GomuluJs* dosyalar = GomuluJsDosyalari(n);
    const auto t0 = Saat::now();
    for (size_t k = 0; k < n; ++k) {
        const GomuluJs& d = dosyalar[k];
        std::string disk;
        const char* kaynak = reinterpret_cast<const char*>(d.veri);
        size_t boyut = d.boyut;
        if (!i.ayar.jsDizini.empty()) {
            const std::string yol = i.ayar.jsDizini + "/" + d.ad;
            if (!DosyaOkuIkili(yol, disk)) {
                hata = "JS dosyası okunamadı: " + yol;
                return false;
            }
            kaynak = disk.c_str();  // std::string sıfır sonludur
            boyut = disk.size();
        }
        js::CagriBasla(*this);
        JSValue r = JS_Eval(c, kaynak, boyut, d.ad, JS_EVAL_TYPE_GLOBAL);
        i.sinirVar = false;
        if (JS_IsException(r)) {
            hata = std::string(d.ad) + ": " + js::IstisnaMetni(c);
            return false;
        }
        JS_FreeValue(c, r);
        i.dosyalar.emplace_back(d.ad);
        i.bayt += boyut;
    }
    i.derlemeMs = std::chrono::duration<double, std::milli>(Saat::now() - t0).count();
    js::Deger g(c, JS_GetGlobalObject(c));
    for (const char* ad : {"ModelOps", "MatrisAks", "MatrisBinaCizim", "MatrisIFC", "MatrisTablo", "Op4Ops", "Op4Cekirdek", "Op4Kopru"}) {
        js::Deger m = g.Ozellik(ad);
        if (!JS_IsObject(m.v())) {
            hata = std::string("JS modülü kurulmadı: ") + ad;
            return false;
        }
    }
    return true;
}

double JsOrtami::DerlemeMs() const { return ic_->derlemeMs; }
const std::vector<std::string>& JsOrtami::YuklenenDosyalar() const { return ic_->dosyalar; }
size_t JsOrtami::YuklenenBayt() const { return ic_->bayt; }
void* JsOrtami::Baglam() const { return ic_->c; }

void JsOrtami::Gunluk(std::string_view s) const {
    if (ic_->ayar.gunluk) ic_->ayar.gunluk(s);
}

bool JsOrtami::Degerlendir(std::string_view kod, const std::string& ad, std::string& sonucJson, std::string& hata) {
    JSContext* c = ic_->c;
    if (!c) {
        hata = "ortam kurulmadı";
        return false;
    }
    const std::string k(kod);
    js::CagriBasla(*this);
    js::Deger r(c, JS_Eval(c, k.c_str(), k.size(), ad.c_str(), JS_EVAL_TYPE_GLOBAL));
    ic_->sinirVar = false;
    if (r.Istisna()) {
        hata = js::IstisnaMetni(c);
        return false;
    }
    js::Deger j(c, JS_JSONStringify(c, r.v(), JS_UNDEFINED, JS_UNDEFINED));
    if (j.Istisna()) {
        hata = js::IstisnaMetni(c);
        return false;
    }
    sonucJson = j.Tanimsiz() ? std::string() : js::Metin(c, j.v());
    return true;
}

bool JsOrtami::CagirMetin(std::string_view yol, const std::vector<std::string>& argumanlar, std::string& sonuc,
                          std::string& hata) {
    JSContext* c = ic_->c;
    if (!c) {
        hata = "ortam kurulmadı";
        return false;
    }
    std::vector<std::string_view> a(argumanlar.begin(), argumanlar.end());
    js::Deger r = js::Cagir(*this, yol, a, hata);
    if (r.Istisna()) return false;
    if (JS_IsString(r.v())) {
        sonuc = js::Metin(c, r.v());
        return true;
    }
    if (r.Tanimsiz()) {
        sonuc.clear();
        return true;
    }
    js::Deger j(c, JS_JSONStringify(c, r.v(), JS_UNDEFINED, JS_UNDEFINED));
    if (j.Istisna()) {
        hata = js::IstisnaMetni(c);
        return false;
    }
    sonuc = js::Metin(c, j.v());
    return true;
}

void JsOrtami::CopTopla() {
    if (ic_->rt) JS_RunGC(ic_->rt);
}

size_t JsOrtami::BellekKullanimi() const {
    if (!ic_->rt) return 0;
    JSMemoryUsage u;
    std::memset(&u, 0, sizeof(u));
    JS_ComputeMemoryUsage(ic_->rt, &u);
    return static_cast<size_t>(u.malloc_size);
}

}  // namespace op4
