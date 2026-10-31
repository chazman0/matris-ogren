// op4 arayüzü — yerelleştirme (kullanıcı kararı 31.10.2026: arayüz dili Türkçe / English, çalışma anında değişir).
//
// Bütün arayüz metinleri Tr("Türkçe metin") ile geçer: Türkçe kaynak metin anahtardır; İngilizce etkinse dil.cpp
// tablosundaki karşılık döner (yoksa Türkçe metin). Komut adları (komut satırı) Türkçe ad + İngilizce takma adlarla
// her iki dilde geçerlidir; komut etiketleri ve ipuçları da bu tablodan çevrilir. Sayı biçimi (ondalık virgül / nokta,
// binlik ayırıcı) Ayarlar › Dil'den gelir. Platformdan bağımsızdır.
#pragma once

#include <cstddef>

#include <cstdint>
#include <string>
#include <string_view>

namespace op4 {

enum class ArayuzDili : uint8_t { Turkce = 0, Ingilizce = 1 };

void DilAyarla(ArayuzDili d);
ArayuzDili EtkinDil();
// "tr" | "en" (Ayarlar arayuz.dil) → dil; tanınmazsa Türkçe.
ArayuzDili DilKodundan(std::string_view kod);

// Çeviri: anahtar Türkçe metindir. Dönen işaretçi süreç boyunca geçerlidir.
const char* Tr(const char* turkce);
inline std::string Tr(const std::string& turkce) { return Tr(turkce.c_str()); }
// printf biçimli çeviri: biçim dizesi çevrilir, sonra doldurulur.
std::string Trf(const char* turkceBicim, ...)
#if defined(__MINGW32__)
    __attribute__((format(gnu_printf, 1, 2)))  // MinGW: %zu (C99) denetimi
#elif defined(__GNUC__)
    __attribute__((format(printf, 1, 2)))
#endif
    ;

// Sayı biçimi (Ayarlar › Dil): ondalık ayırıcı ',' ya da '.', binlik ayırıcı ince boşluk ya da yok.
void SayiBicimiAyarla(char ondalik, bool binlik);
// basamak kadar kesir, sondaki sıfırlar atılmaz (sabit) ya da atılır; "-0" yazılmaz.
std::string Sayi(double v, int basamak, bool sabit = true);
// Kot: "+9,00", "±0,00", "−3,20".
std::string Kot(double z);

// Sınama: tablodaki bütün Türkçe anahtarların İngilizce karşılığı boş değil; dönen sayı girdi sayısı.
size_t CeviriSayisi();

// Çeviri tablosu (dil_tablosu.cpp): Türkçe kaynak metin → İngilizce.
struct CeviriGirdisi {
    const char* tr;
    const char* en;
};
const CeviriGirdisi* CeviriTablosu(size_t& n);

}  // namespace op4
