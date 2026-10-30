// op4 çekirdek — motor yönlendirme tablosu (sözleşme S13; tam uygulama, MIMARI §8.3).
#include "cekirdek/motor_hizmeti.h"

namespace op4 {

MotorRolu MotorRoluSec(std::string_view islem) {
    static constexpr std::string_view kAna[] = {
        "bina_coz",          "bina_kombinasyon", "bina_eleman_tasarim", "bina_kesit_oner",
        "bina_eleman_bilgi", "bina_rapor",       "bina_tablolar",       "bina_alan",
        "bina_yuk_yolu",     "bina_kimlik",      "bina_ag_eniyile",
    };
    for (const std::string_view a : kAna)
        if (islem == a) return MotorRolu::Ana;
    return MotorRolu::Yardimci;
}

}  // namespace op4
