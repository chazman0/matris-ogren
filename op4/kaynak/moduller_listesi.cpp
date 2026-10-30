// op4 — op4.exe modül listesi (sözleşme S23). Yalnız Windows derlemesinde; sıra bağlayıcıdır (cekirdek/kabuk.h).
#include "cekirdek/kabuk.h"

namespace op4 {

std::vector<ModulKaydi> StandartModuller() {
    return {
        {"motor", "A", &MotorModuluKur},
        {"cekirdek", "B", &CekirdekModuluKur},
        {"arayuz", "C", &ArayuzModuluKur},
        {"dosya", "D", &DosyaModuluKur},
        {"cozum", "D", &CozumModuluKur},
    };
}

}  // namespace op4
