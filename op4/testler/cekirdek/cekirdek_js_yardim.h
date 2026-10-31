// op4 C++ sınamaları — model çekirdeği (B) ortak yardımcıları.
#pragma once

#include <memory>
#include <string>
#include <vector>

#include "cekirdek/model_cekirdegi.h"
#include "cekirdek_js/quickjs_cekirdek.h"
#include "sinama_yardim.h"

namespace op4::sinama {

// op4/testler/derlem/sablonlar/ altındaki 9 şablon (yapi.bina_sablonlar sırası).
inline const std::vector<std::string>& SablonAdlari() {
    static const std::vector<std::string> l = {"betonarme-tek-aciklik", "betonarme-2kat-3x2", "betonarme-3kat-3x3", "celik-1kat-depo",
                                               "betonarme-4kat-4x3",    "betonarme-3kat-surekli-temel", "betonarme-4kat-radye",
                                               "celik-sanayi-4hol",     "celik-cbf-3kat"};
    return l;
}

inline std::string Sablon(const std::string& ad) { return Op4Dosyasi("testler/derlem/sablonlar/" + ad + ".json"); }

// Deterministik saatli QuickJS çekirdeği; günlük satırları isteğe bağlı toplanır.
inline std::unique_ptr<ModelCekirdegi> CekirdekKur(std::vector<std::string>* gunluk = nullptr, int geriAlAdim = 100,
                                                    double geriAlMb = 512) {
    CekirdekAyari a;
    a.deterministikSaat = true;
    if (gunluk) a.gunluk = [gunluk](std::string_view s) { gunluk->emplace_back(s); };
    std::string hata;
    auto c = QuickJsCekirdegiOlustur(a, GeriAlSiniri{geriAlAdim, geriAlMb}, hata);
    if (!c && gunluk) gunluk->push_back("KURULAMADI: " + hata);
    return c;
}

}  // namespace op4::sinama
