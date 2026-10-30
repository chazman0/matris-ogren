// op4 C++ sınamaları — hesap motoru sınamalarının ortak yardımcıları (A). Python yorumlayıcısı CMake'ten (OP4_PYTHON);
// yoksa sınamalar atlanır. OP4_MOTOR_SINAMA_ZORUNLU=1 iken (CI) Python ya da gerçek motorun bağımlılıkları (numpy, sympy)
// eksikse sınama BAŞARISIZ olur — böylece CI'da sessizce atlanmaz.
#pragma once

#include <doctest/doctest.h>

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <functional>
#include <string>
#include <thread>

#include "cekirdek/motor_hizmeti.h"

namespace op4::sinama {

inline bool MotorSinamasiZorunlu() {
    const char* z = std::getenv("OP4_MOTOR_SINAMA_ZORUNLU");
    return z && std::string(z) == "1";
}

inline std::string PythonYolu() {
#ifdef OP4_PYTHON
    return OP4_PYTHON;
#else
    return {};
#endif
}

#ifdef _WIN32
inline constexpr char kYolAyirici = ';';
#else
inline constexpr char kYolAyirici = ':';
#endif

inline std::string MotorDizini() { return std::string(OP4_KAYNAK_DIZINI) + "/motor"; }
inline std::string SahteMotorDizini() { return MotorDizini() + kYolAyirici + OP4_KAYNAK_DIZINI + "/testler/python/sahte_motor"; }
inline std::string GercekMotorDizini() { return MotorDizini() + kYolAyirici + OP4_DEPO_DIZINI + "/docs"; }

// Python yoksa false (zorunluysa sınamayı düşürür).
inline bool PythonVar() {
    if (!PythonYolu().empty()) return true;
    if (MotorSinamasiZorunlu()) FAIL("OP4_MOTOR_SINAMA_ZORUNLU=1 ama CMake Python bulamadı (OP4_PYTHON tanımsız)");
    MESSAGE("Python yok: motor sınaması atlandı");
    return false;
}

// Gerçek web_kopru için numpy + sympy var mı (python -c ile).
inline bool GercekMotorVar() {
    if (!PythonVar()) return false;
    const std::string komut = "\"" + PythonYolu() + "\" -c \"import numpy, sympy\"";
#ifdef _WIN32
    const int r = std::system(("\"" + komut + " >NUL 2>&1\"").c_str());
#else
    const int r = std::system((komut + " >/dev/null 2>&1").c_str());
#endif
    if (r == 0) return true;
    if (MotorSinamasiZorunlu()) FAIL("OP4_MOTOR_SINAMA_ZORUNLU=1 ama Python'da numpy / sympy yok (gerçek motor sınaması)");
    MESSAGE("numpy / sympy yok: gerçek motor sınaması atlandı");
    return false;
}

inline MotorAyari SahteAyar(double iptalBeklemeMs = 5000) {
    MotorAyari a;
    a.pythonYolu = PythonYolu();
    a.sunucuDizini = SahteMotorDizini();
    a.iptalBeklemeMs = iptalBeklemeMs;
    a.anaBlasIs = 2;
    return a;
}

// Koşul sağlanana dek (ya da süre dolana dek) Pompala çağırır.
inline bool PompalaBekle(MotorHizmeti& m, const std::function<bool()>& kosul, double ms = 20000) {
    const auto bitis = std::chrono::steady_clock::now() + std::chrono::duration<double, std::milli>(ms);
    for (;;) {
        m.Pompala();
        if (kosul()) return true;
        if (std::chrono::steady_clock::now() > bitis) return false;
        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
}

inline bool HazirBekle(MotorHizmeti& m, MotorRolu rol = MotorRolu::Ana, double ms = 60000) {
    return PompalaBekle(m, [&] { return m.Durum(rol).hazir; }, ms);
}

inline double SimdiMs() {
    using namespace std::chrono;
    static const auto t0 = steady_clock::now();
    return duration<double, std::milli>(steady_clock::now() - t0).count();
}

// Sınama başına geçici klasör (çıkışta silinir).
struct GeciciDizin {
    std::filesystem::path yol;
    explicit GeciciDizin(const std::string& ad) {
        yol = std::filesystem::temp_directory_path() /
              ("op4-sinama-" + ad + "-" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        static_cast<void>(std::filesystem::create_directories(yol));
    }
    ~GeciciDizin() {
        std::error_code e;
        static_cast<void>(std::filesystem::remove_all(yol, e));
    }
    std::string Utf8() const {
        const std::u8string s = yol.u8string();
        return std::string(reinterpret_cast<const char*>(s.data()), s.size());
    }
};

inline void OrtamAyarla(const char* ad, const char* deger) {
#ifdef _WIN32
    _putenv_s(ad, deger ? deger : "");
#else
    if (deger) setenv(ad, deger, 1);
    else unsetenv(ad);
#endif
}

}  // namespace op4::sinama
