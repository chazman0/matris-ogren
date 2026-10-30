// op4 — günlük (log): süreç başından beri geçen süreyle zaman damgalı UTF-8 satırlar.
// Hedefler: isteğe bağlı günlük dosyası, (varsa) standart çıktı tutamacı ve hata ayıklayıcı (OutputDebugString).
#pragma once

#include <string>

namespace op4 {

// dosya boşsa yalnız konsol + hata ayıklayıcı. Birden çok kez çağrılabilir (önceki dosya kapanır).
void GunlukAc(const std::wstring& dosya);
void GunlukKapat();
// printf biçimli, UTF-8. Satır sonu kendiliğinden eklenir.
void Gunluk(const char* bicim, ...)
#if defined(__GNUC__)
    __attribute__((format(gnu_printf, 1, 2)))
#endif
    ;
// Biçimsiz uzun metin (ör. base64 ya da JSON); satır sonu eklenir.
void GunlukHam(const std::string& metin);

double GecenMs();  // süreç başından beri milisaniye (QueryPerformanceCounter)

std::string Utf8(const std::wstring& w);
std::wstring Genis(const std::string& s);

}  // namespace op4
