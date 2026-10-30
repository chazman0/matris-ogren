// op4 çekirdek sözleşmesi — Türkçe metin yardımcıları (sözleşme S6).
//
// Komut satırı tamamlama (MIMARI §12.1), model gezgini hızlı süzgeci ve Faz 3 sorgu dili alan adları aynı katlama kuralını
// kullanır: büyük/küçük harf duyarsız ve Türkçe harf katlamalı ("ÇUBUK", "çubuk", "cubuk", "CUBUK" eşit).
#pragma once

#include <string>
#include <string_view>

namespace op4 {

// UTF-8 metni karşılaştırma anahtarına çevirir: ASCII harfler küçülür; İ I ı i → i, Ş ş → s, Ğ ğ → g, Ç ç → c, Ö ö → o,
// Ü ü → u, Â â → a, Î î → i, Û û → u. Diğer baytlar olduğu gibi kalır.
std::string TurkceKatla(std::string_view utf8);
// a, b'nin (katlanmış) önekiyse true.
bool TurkceOnekMi(std::string_view onek, std::string_view metin);
// Ondalık virgüllü gösterim (MIMARI §2.2.7): basamak sayısı kadar kesir, sondaki sıfırlar atılır; "-0" yazılmaz.
// OndalikVirgul(3.25, 2) == "3,25", OndalikVirgul(2.0, 3) == "2", OndalikVirgul(-0.0001, 2) == "0".
std::string OndalikVirgul(double deger, int basamak);
// Kullanıcı girdisinde ondalık virgül de kabul eden sayı okuma ("3,25" ya da "3.25"); tam okunmazsa false.
bool SayiOku(std::string_view metin, double& deger);

}  // namespace op4
