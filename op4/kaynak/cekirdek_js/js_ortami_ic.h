// op4 model çekirdeği — QuickJS köprüsünün iç yardımcıları (yalnız kaynak/cekirdek_js içinde). Uygulayan: B.
#pragma once

#include <quickjs.h>

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include "cekirdek_js/js_ortami.h"

namespace op4::js {

// JSValue sahibi (RAII). Taşınabilir, kopyalanamaz.
class Deger {
public:
    Deger() = default;
    Deger(JSContext* c, JSValue v) : c_(c), v_(v) {}
    Deger(Deger&& o) noexcept : c_(o.c_), v_(o.v_) { o.c_ = nullptr; o.v_ = JS_UNDEFINED; }
    Deger& operator=(Deger&& o) noexcept {
        if (this != &o) {
            Birak();
            c_ = o.c_;
            v_ = o.v_;
            o.c_ = nullptr;
            o.v_ = JS_UNDEFINED;
        }
        return *this;
    }
    Deger(const Deger&) = delete;
    Deger& operator=(const Deger&) = delete;
    ~Deger() { Birak(); }

    JSValueConst v() const { return v_; }
    bool Istisna() const { return JS_IsException(v_); }
    bool Tanimsiz() const { return JS_IsUndefined(v_) || JS_IsNull(v_); }
    Deger Ozellik(const char* ad) const { return Deger(c_, JS_GetPropertyStr(c_, v_, ad)); }
    Deger Eleman(uint32_t i) const { return Deger(c_, JS_GetPropertyUint32(c_, v_, i)); }
    JSValue Birak_() {
        JSValue v = v_;
        v_ = JS_UNDEFINED;
        c_ = nullptr;
        return v;
    }

private:
    void Birak() {
        if (c_) JS_FreeValue(c_, v_);
        c_ = nullptr;
        v_ = JS_UNDEFINED;
    }
    JSContext* c_ = nullptr;
    JSValue v_ = JS_UNDEFINED;
};

JSContext* Baglam(const JsOrtami& o);
// Bekleyen istisnayı alır ve "Ad: ileti" + yığın metnine çevirir (istisna temizlenir).
std::string IstisnaMetni(JSContext* c);
// Değeri UTF-8 metne çevirir (dize değilse String(v)).
std::string Metin(JSContext* c, JSValueConst v);
// Bir çağrıya girerken: yığın tepesini günceller ve süre sınırını kurar.
void CagriBasla(const JsOrtami& o);
// "Op4Kopru.uygula" gibi yoldaki işlevi dize bağımsız değişkenlerle çağırır. İstisnada sonuç Istisna() ve hata dolu.
Deger Cagir(const JsOrtami& o, std::string_view yol, const std::vector<std::string_view>& arg, std::string& hata);

// Tipli dizi görünümü: nesnenin `ad` özelliğindeki tipli dizinin belleği (ArrayBuffer'dan, kopyasız). Tür / eleman boyutu
// beklenenle uyuşmazsa ya da yoksa false + hata.
struct TipliGorunum {
    Deger tampon;               // ArrayBuffer'ı canlı tutar
    const uint8_t* veri = nullptr;
    size_t adet = 0;
};
bool TipliDizi(JSContext* c, JSValueConst nesne, const char* ad, JSTypedArrayEnum tur, TipliGorunum& g, std::string& hata);

}  // namespace op4::js
