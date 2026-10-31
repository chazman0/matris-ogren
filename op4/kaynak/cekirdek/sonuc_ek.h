// op4 çekirdek — sonuç özeti yardımcıları (çözüm akışı ve Sonuç özeti paneli için; sözleşme S19'un yanında). Sahibi: D.
#pragma once

#include <cstddef>
#include <string>
#include <string_view>

#include "cekirdek/model_cekirdegi.h"
#include "cekirdek/sonuc.h"

namespace op4 {

// D/C sınıflarına göre eleman sayıları (DcRengi ölçeği: < 0,7 / 0,7–0,9 / 0,9–1,0 / > 1,0 / tasarım yok).
struct DcDagilimi {
    size_t yesil = 0, sari = 0, turuncu = 0, kirmizi = 0, yok = 0;
};
DcDagilimi DcDagilimiHesapla(const SonucOzeti& ozet);

// Çekirdeğin SonucEsle'si yokken (geçici çekirdek) yedek eşleme: genel (surum 3) modelde veri.tasarim.elemanlar[] kaydının
// "cubuk" numarası doğrudan çubuk kimliğidir. Aks–kat modelinde eşleme çekirdeğin işidir (boş döner, uyarı yazar).
SonucEslemesi TasarimdanEsle(std::string_view veriMetni);

// Eşlemeyi özete yerleştirir: kimliğe göre sıralar, aynı kimlikte en büyük D/C'yi tutar, en büyük D/C elemanını ve
// (eşlemede varsa) D/C > 1 sayısını günceller.
void EslemeyiYerlestir(SonucOzeti& ozet, SonucEslemesi esleme);

}  // namespace op4
