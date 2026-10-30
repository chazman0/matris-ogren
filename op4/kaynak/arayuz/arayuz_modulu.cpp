// op4 — arayüz modülü (C; sözleşme S21, S23). Windows (ImGui).
//
// TASLAK: F1 iş 1.4'te C burada şunları yapar —
//   * Hizmetler::bildirim'e ImGui komut satırı / tost / ilerleme uygulamasını bağlar (şimdilik kabuğun günlük yedeği),
//   * komutlar.json'daki sahibi "C" olan komutlara işleyici bağlar (gorunum.*, secim.*, model.hizli_aks, ayarlar.ac,
//     yardim.*),
//   * panelleri (model_gezgini, ozellikler, baslangic), durum öğelerini (koordinat, yakalama çipleri, secim_sayisi,
//     bagdastirici) ve Ayarlar › Grafik / Arayüz sayfalarını kaydeder,
//   * gorunum/gorunum.json ve secim/kumeler.json için ProjeBelgesi katkısını ekler,
//   * Hizmetler::sahneDegisti'ye abone olup çiziciyi ve seçme dizinini yeniler.
// Faz 0 arayüzü (arayuz.cpp, uygulama.cpp) bu süre boyunca olduğu gibi çalışır.
#include "cekirdek/kabuk.h"

namespace op4 {

void ArayuzModuluKur(Hizmetler&, ModulOrtami&) {}

}  // namespace op4
