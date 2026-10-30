// op4 — çözüm modülü (D; sözleşme S13, S19, S23). Platformdan bağımsız tutulması önerilir (Linux sınaması).
//
// TASLAK: F1 iş 1.5'te D burada şunları yapar —
//   * analiz.coz (F5): çekirdek Metin() → Hizmetler::motor->Gonder("bina_coz", {"bina":…, "anlat":false}) eşzamansız;
//     analiz.iptal → motor->Iptal; ilerleme Hizmetler::bildirim->Ilerleme,
//   * yanıt → CozumYanitiniCoz + cekirdek->SonucEsle → SonucDurumu::Ata → BoyamaKur → GorunumDurumu::sonuc,
//   * "Sonuç özeti" paneli, "Sonuçlar eski" durum öğesi, analiz.dc_renkleri, sonuc/ozet.json + sonuc/veri.json katkısı,
//   * bina_kimlik ile açılışta sonuç eşleştirme (MIMARI §13.1.4).
#include "cekirdek/kabuk.h"

namespace op4 {

void CozumModuluKur(Hizmetler&, ModulOrtami&) {}

}  // namespace op4
