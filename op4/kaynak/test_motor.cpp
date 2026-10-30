// op4 — hesap motoru test kipleri (A): --test-motor (Faz 0 süreç içi gömülü motor; MIMARI §8.1'e göre süreç tabanlı
// istemciye geçince MotorHizmeti üstünden yeniden yazılır) ve --oz-sinama (TASLAK).
#include <windows.h>

#include <string>

#include "gunluk.h"
#include "motor.h"
#include "test_kipleri.h"

namespace op4 {

int MotorTesti() {
    TestKipi(300);
    Gunluk("--test-motor: gömülü Python + hesap motoru (web_kopru) denetimi");
    Gunluk("Uygulama dizini: %s", Utf8(UygulamaDizini()).c_str());
    Motor m;
    m.Baslat(UygulamaDizini(), nullptr);
    m.Bekle(INFINITE);
    MotorDurumu d = m.Durum();
    if (!d.basarili) {
        Gunluk("MOTOR TESTİ BAŞARISIZ: %s", d.hata.c_str());
        return 2;
    }
    Gunluk("Python: %s", d.pythonSurumu.c_str());
    Gunluk("web_kopru.surum_json() = %s", d.surumJson.c_str());
    Gunluk("Şablonlar (%d): ", d.sablonSayisi);
    for (const std::string& a : d.sablonAdlari) Gunluk("  - %s", a.c_str());
    Gunluk("bina_sablonlar yanıtı (%zu bayt): %.240s…", d.sablonlarJson.size(), d.sablonlarJson.c_str());
    Gunluk("SÜRELER: DLL yükleme %.1f ms | Py_InitializeEx %.1f ms | import web_kopru %.1f ms | surum_json %.1f ms | "
           "bina_sablonlar %.1f ms | TOPLAM motor açılışı %.1f ms",
           d.msDll, d.msBaslat, d.msIceAktar, d.msSurum, d.msSablon, d.msToplam);
    GunlukHam(Bicim("OP4OLCUM senaryo=motor dll_ms=%.1f baslat_ms=%.1f ice_aktar_ms=%.1f sablonlar_ms=%.1f toplam_ms=%.1f "
                    "sablon=%d", d.msDll, d.msBaslat, d.msIceAktar, d.msSablon, d.msToplam, d.sablonSayisi));

    bool tamam = d.sablonSayisi > 0 && d.surumJson.find("\"python\"") != std::string::npos;
    // Kuyruk üzerinden iki gidiş-dönüş daha (arayüz iş parçacığından çağrı yolu).
    double t = GecenMs();
    std::string r = m.Calistir(R"({"islem":"determinant","girdi":{"A":"2 1; 1 3"}})");
    Gunluk("determinant([[2,1],[1,3]]) → sonuc_metin %s (%.1f ms)",
           r.find("\"sonuc_metin\": \"5\"") != std::string::npos ? "5 ✓" : "BEKLENMEDİK", GecenMs() - t);
    tamam = tamam && r.find("\"sonuc_metin\": \"5\"") != std::string::npos;
    if (!d.sablonAdlari.empty()) {
        t = GecenMs();
        r = m.Calistir(R"({"islem":"bina_sablon","girdi":{"ad":")" + d.sablonAdlari[0] + R"("}})");
        bool sablonTamam = r.find("\"hata\": null") != std::string::npos && r.find("\"bina\"") != std::string::npos;
        Gunluk("bina_sablon(%s) → %zu bayt, %s (%.1f ms)", d.sablonAdlari[0].c_str(), r.size(),
               sablonTamam ? "hata yok ✓" : r.substr(0, 300).c_str(), GecenMs() - t);
        tamam = tamam && sablonTamam;
    }
    m.Durdur();
    Gunluk(tamam ? "MOTOR TESTİ BAŞARILI" : "MOTOR TESTİ BAŞARISIZ");
    return tamam ? 0 : 2;
}

int OzSinama(const Secenekler&) {
    TestKipi(300);
    // TASLAK (A, F1 iş 1.1–1.2): kurulu programın kendi kendini sınaması — motor süreci, çekirdek, şablon açma, kaydet /
    // aç gidiş-dönüşü, ekran görüntüsü. Uygulanana dek atlanır (CI bu kipi henüz çağırmaz).
    Gunluk("--oz-sinama: henüz uygulanmadı (atlandı)");
    GunlukHam("OP4OLCUM senaryo=oz_sinama durum=atlandi");
    return 0;
}

}  // namespace op4
