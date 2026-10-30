// op4 — hesap motoru test kipleri (A; MIMARI §6.14, §8; F1 iş 1.2, kabul A6, A10, A11):
//   --test-motor   süreç tabanlı motor (op4motor.exe + op4_sunucu, tel protokolü) uçtan uca: ana motorun soğuk açılışı,
//                  tembel yardımcı, yönlendirme, şablonlar, bina_kimlik, anlatımsız bina_coz, hesap ortasında iptal
//                  (KeyboardInterrupt), motor.yeniden_baslat, düzgün kapanış. Sunucu günlükleri sonda test günlüğüne basılır.
//   --oz-sinama    kurulu programın kendi kendini sınaması: motor, model çekirdeği (kabuk, "Adsız 1", şablon yükleme),
//                  .op4 kaydet / aç gidiş-dönüşü (D'nin ZIP'i hazırsa), ekran (WARP). Uygulanmamış (taslak) adımlar
//                  "atlandı" olarak yazılır ve testi düşürmez; uygulanmış bir adımın hatası düşürür.
// Ölçümler: OP4OLCUM senaryo=motor … / senaryo=oz_sinama …
#include <windows.h>

#include <algorithm>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "cekirdek/kabuk.h"
#include "cekirdek/motor_istemci.h"
#include "cekirdek/proje_dosyasi.h"
#include "gunluk.h"
#include "platform/dosya_sistemi.h"
#include "test_kipleri.h"

namespace op4 {
namespace {

using nlohmann::json;

json Coz(const MotorYaniti& y) {
    json j = json::parse(y.yanit, nullptr, false);
    return j.is_discarded() ? json::object() : j;
}

std::string Kisa(const std::string& s, size_t n = 300) { return s.size() <= n ? s : s.substr(0, n) + "…"; }

void SunucuGunlukleriniBas(const MotorIstemcisi& m) {
    for (const MotorRolu r : {MotorRolu::Ana, MotorRolu::Yardimci}) {
        const std::string yol = m.GunlukYolu(r);
        if (yol.empty()) continue;
        std::string metin, hata;
        if (!DosyaOku(yol, metin, hata)) continue;
        if (metin.size() > 6000) metin = "…" + metin.substr(metin.size() - 6000);
        Gunluk("---- sunucu günlüğü (%s): %s ----", r == MotorRolu::Ana ? "ana" : "yardimci", yol.c_str());
        GunlukHam(metin);
        Gunluk("---- günlük sonu ----");
    }
}

struct MotorSonucu {
    bool tamam = false;
    double sogukMs = 0, yardimciMs = 0, determinantMs = 0, sablonMs = 0, kimlikMs = 0, cozMs = 0, iptalMs = 0,
           yenidenMs = 0;
    int sablonSayisi = 0;
    std::string ilkSablon, ilkSablonBina;
};

void MotorAyariKur(MotorIstemcisi& m, MotorAyari& a) {
    m.gunluk = [](std::string_view s) { Gunluk("%.*s", static_cast<int>(s.size()), s.data()); };
    m.sdSiniri = 6000;
    a.uygulamaDizini = Utf8(UygulamaDizini());
    a.gunlukDizini = KullaniciDizinleriniBul(true).gunluk;
}

// Motor testinin gövdesi (--test-motor ve --oz-sinama). tam = false: yalnız açılış + şablonlar (öz sınama).
MotorSonucu MotorSina(MotorIstemcisi& m, bool tam) {
    MotorSonucu r;
    MotorAyari a;
    MotorAyariKur(m, a);
    const double t0 = GecenMs();
    m.Baslat(a);
    while (!m.Durum().hazir && GecenMs() - t0 < 120000) {
        m.Pompala();
        Sleep(2);
    }
    const MotorDurumOzeti d = m.Durum();
    r.sogukMs = d.hazirMs;
    if (!d.basarili) {
        Gunluk("MOTOR BAŞLATILAMADI: %s", d.hata.c_str());
        return r;
    }
    Gunluk("Python: %s", d.pythonSurumu.c_str());
    Gunluk("web_kopru.surum_json() = %s", d.surumJson.c_str());
    Gunluk("Ana motor hazır: %.1f ms (süreç başlatma → hazir iletisi) %s", r.sogukMs,
           r.sogukMs <= 1000 ? "≤ 1 s ✓" : "> 1 s (A10 hedefi aşıldı)");
    bool tamam = true;
    auto adim = [&](bool kosul, const std::string& ad, const std::string& ayrinti) {
        Gunluk("%s %s%s%s", kosul ? "✓" : "✗", ad.c_str(), ayrinti.empty() ? "" : " — ", ayrinti.c_str());
        tamam = tamam && kosul;
        return kosul;
    };
    // bina_sablonlar → yardımcı motor (tembel: ilk istekte başlar)
    double t = GecenMs();
    MotorYaniti y = m.CalistirBekle("bina_sablonlar", "", "", 120000);
    r.sablonMs = GecenMs() - t;
    r.yardimciMs = m.Durum(MotorRolu::Yardimci).hazirMs;
    json j = Coz(y);
    std::vector<std::string> adlar;
    if (j.contains("sablonlar") && j["sablonlar"].is_array())
        for (const json& s : j["sablonlar"]) adlar.push_back(s.value("ad", std::string()));
    r.sablonSayisi = static_cast<int>(adlar.size());
    adim(y.durum == YanitDurumu::Tamam && r.sablonSayisi >= 9, "bina_sablonlar (yardımcı motor, tembel başlatma)",
         std::to_string(r.sablonSayisi) + " şablon, " + std::to_string(static_cast<int>(r.sablonMs)) + " ms; yardımcı hazır " +
             std::to_string(static_cast<int>(r.yardimciMs)) + " ms" + (y.hata.empty() ? "" : "; " + y.hata));
    for (const std::string& s : adlar) Gunluk("  - %s", s.c_str());
    if (adlar.empty()) {
        r.tamam = false;
        return r;
    }
    r.ilkSablon = std::find(adlar.begin(), adlar.end(), "betonarme-tek-aciklik") != adlar.end() ? "betonarme-tek-aciklik"
                                                                                                 : adlar.front();
    y = m.CalistirBekle("bina_sablon", json({{"ad", r.ilkSablon}}).dump(), "", 60000);
    j = Coz(y);
    adim(y.durum == YanitDurumu::Tamam && j.contains("bina"), "bina_sablon(" + r.ilkSablon + ")",
         std::to_string(y.yanit.size()) + " bayt");
    if (j.contains("bina")) r.ilkSablonBina = j["bina"].dump();
    if (!tam) {
        r.tamam = tamam;
        return r;
    }
    t = GecenMs();
    y = m.CalistirBekle("determinant", R"({"A":"2 1; 1 3"})", "", 60000);
    r.determinantMs = GecenMs() - t;
    adim(Coz(y).value("sonuc_metin", std::string()) == "5", "determinant([[2,1],[1,3]]) = 5 (yardımcı)",
         std::to_string(static_cast<int>(r.determinantMs)) + " ms");
    // bina_kimlik + anlatımsız bina_coz → ana motor (MIMARI §8.6)
    t = GecenMs();
    y = m.CalistirBekle("bina_kimlik", "{\"bina\":" + r.ilkSablonBina + "}", "", 60000);
    r.kimlikMs = GecenMs() - t;
    const std::string kimlik = Coz(y).value("cozum_kimligi", std::string());
    adim(y.durum == YanitDurumu::Tamam && kimlik.rfind("bina-", 0) == 0, "bina_kimlik (ana)",
         kimlik + ", " + std::to_string(static_cast<int>(r.kimlikMs)) + " ms" + (y.hata.empty() ? "" : "; " + y.hata));
    t = GecenMs();
    y = m.CalistirBekle("bina_coz", "{\"bina\":" + r.ilkSablonBina + "}", "{\"anlat\":false}", 120000);
    r.cozMs = GecenMs() - t;
    j = Coz(y);
    const bool cozTamam = y.durum == YanitDurumu::Tamam && j.contains("bloklar") && j["bloklar"].empty() &&
                          j.contains("veri") && j["veri"].value("cozum_kimligi", std::string()) == kimlik;
    adim(cozTamam, "bina_coz anlat:false (ana; bloklar [], cozum_kimligi eşleşir)",
         std::to_string(static_cast<int>(r.cozMs)) + " ms, " + std::to_string(y.yanit.size()) + " bayt" +
             (y.hata.empty() ? "" : "; " + Kisa(y.hata)));
    // Hesap ortasında iptal: KeyboardInterrupt (interrupt_main) yolu; süreç sonlandırılmamalı.
    std::string buyuk;
    if (std::find(adlar.begin(), adlar.end(), "celik-sanayi-4hol") != adlar.end()) {
        y = m.CalistirBekle("bina_sablon", R"({"ad":"celik-sanayi-4hol"})", "", 60000);
        j = Coz(y);
        if (j.contains("bina")) buyuk = j["bina"].dump();
    }
    if (!buyuk.empty()) {
        bool geldi = false;
        MotorYaniti iy;
        const IstekNo no = m.Gonder("bina_coz", "{\"bina\":" + buyuk + "}", "{\"anlat\":true}", [&](const MotorYaniti& x) {
            iy = x;
            geldi = true;
        });
        const double b0 = GecenMs();
        while (!geldi && GecenMs() - b0 < 600) {
            m.Pompala();
            Sleep(2);
        }
        const double i0 = GecenMs();
        const bool iptalKabul = m.Iptal(no);
        while (!geldi && GecenMs() - i0 < 15000) {
            m.Pompala();
            Sleep(2);
        }
        r.iptalMs = GecenMs() - i0;
        adim(iptalKabul && geldi && iy.durum == YanitDurumu::Iptal && m.Durum().yenidenBaslatma == 0,
             "hesap ortasında iptal (celik-sanayi-4hol bina_coz; KeyboardInterrupt, süreç sonlandırılmadan)",
             std::to_string(static_cast<int>(r.iptalMs)) + " ms" + (iptalKabul ? "" : "; çözüm iptalden önce bitti"));
    }
    // motor.yeniden_baslat
    t = GecenMs();
    m.YenidenBaslat();
    while (!m.Durum().hazir && GecenMs() - t < 120000) {
        m.Pompala();
        Sleep(2);
    }
    y = m.CalistirBekle("bina_kimlik", "{\"bina\":" + r.ilkSablonBina + "}", "", 60000);
    r.yenidenMs = GecenMs() - t;
    adim(y.durum == YanitDurumu::Tamam && Coz(y).value("cozum_kimligi", std::string()) == kimlik,
         "motor.yeniden_baslat → ana motor yeniden hazır, istek yanıtlandı",
         std::to_string(static_cast<int>(r.yenidenMs)) + " ms");
    r.tamam = tamam;
    return r;
}

}  // namespace

int MotorTesti() {
    TestKipi(300);
    Gunluk("--test-motor: süreç tabanlı hesap motoru (op4motor.exe → Py_Main → op4_sunucu; tel protokolü, MIMARI §8)");
    Gunluk("Uygulama dizini: %s", Utf8(UygulamaDizini()).c_str());
    const double t0 = GecenMs();
    MotorIstemcisi m;
    const MotorSonucu r = MotorSina(m, true);
    const double kapanis0 = GecenMs();
    m.Durdur();
    const double kapanisMs = GecenMs() - kapanis0;
    const bool kapandi = m.SurecKimligi(MotorRolu::Ana) == 0 && m.SurecKimligi(MotorRolu::Yardimci) == 0;
    Gunluk("%s Durdur: motor süreçleri kapandı (%.0f ms)", kapandi ? "✓" : "✗", kapanisMs);
    Gunluk("SÜRELER: ana motor hazır %.1f ms | yardımcı hazır %.1f ms | bina_sablonlar %.1f ms | determinant %.1f ms | "
           "bina_kimlik %.1f ms | bina_coz %.1f ms | iptal %.1f ms | yeniden başlatma %.1f ms | TOPLAM motor açılışı %.1f ms",
           r.sogukMs, r.yardimciMs, r.sablonMs, r.determinantMs, r.kimlikMs, r.cozMs, r.iptalMs, r.yenidenMs, r.sogukMs);
    GunlukHam(Bicim("OP4OLCUM senaryo=motor soguk_hazir_ms=%.1f yardimci_hazir_ms=%.1f sablonlar_ms=%.1f determinant_ms=%.1f "
                    "kimlik_ms=%.1f coz_ms=%.1f iptal_ms=%.1f yeniden_ms=%.1f kapanis_ms=%.0f sablon=%d toplam_ms=%.0f",
                    r.sogukMs, r.yardimciMs, r.sablonMs, r.determinantMs, r.kimlikMs, r.cozMs, r.iptalMs, r.yenidenMs,
                    kapanisMs, r.sablonSayisi, GecenMs() - t0));
    SunucuGunlukleriniBas(m);
    const bool tamam = r.tamam && kapandi;
    Gunluk(tamam ? "MOTOR TESTİ BAŞARILI" : "MOTOR TESTİ BAŞARISIZ");
    return tamam ? 0 : 2;
}

int OzSinama(const Secenekler& s) {
    TestKipi(600);
    Gunluk("--oz-sinama: kurulu programın kendi kendini sınaması (motor, çekirdek, şablon, kaydet / aç, ekran)");
    Gunluk("Uygulama dizini: %s", Utf8(UygulamaDizini()).c_str());
    std::vector<std::pair<std::string, std::string>> durum;  // adım → "tamam" | "hata" | "atlandi"
    bool tamam = true;
    auto yaz = [&](const std::string& ad, const std::string& d, const std::string& ayrinti) {
        durum.emplace_back(ad, d);
        if (d == "hata") tamam = false;
        Gunluk("%s %s: %s%s%s", d == "tamam" ? "✓" : (d == "hata" ? "✗" : "–"), ad.c_str(), d.c_str(),
               ayrinti.empty() ? "" : " — ", ayrinti.c_str());
    };
    const KullaniciDizinleri kd = KullaniciDizinleriniBul(true);

    // 1) motor
    MotorIstemcisi m;
    const MotorSonucu mr = MotorSina(m, false);
    yaz("motor", mr.tamam ? "tamam" : "hata", Bicim("hazır %.0f ms, %d şablon", mr.sogukMs, mr.sablonSayisi));
    m.Durdur();

    // 2) model çekirdeği (kabuk: yalnız A + B modülleri; pencere yok)
    UygulamaKabugu k;
    KabukAyari ka;
    ka.bilgi.surum = OP4_SURUM;
    ka.bilgi.uygulamaDizini = Utf8(UygulamaDizini());
    ka.bilgi.veriDizini = Utf8(VeriDizini());
    ka.bilgi.ayarDizini = kd.ayarlar;
    ka.bilgi.yerelDizin = kd.yerel;
    ka.bilgi.testKipi = true;
    ka.ortam.testKipi = true;
    ka.ortam.motorsuz = true;
    ka.ortam.gunluk = [](std::string_view x) { Gunluk("%.*s", static_cast<int>(x.size()), x.data()); };
    ka.moduller = {{"motor", "A", &MotorModuluKur}, {"cekirdek", "B", &CekirdekModuluKur}};
    std::string hata;
    const bool kuruldu = k.Kur(std::move(ka), hata);
    Hizmetler& h = k.H();
    std::string modelMetni;
    if (!kuruldu || !h.cekirdek) {
        yaz("cekirdek", "hata", hata.empty() ? "model çekirdeği kurulamadı" : hata);
    } else {
        modelMetni = h.cekirdek->Metin();
        const json mj = json::parse(modelMetni, nullptr, false);
        const bool ok = h.belge->Ad() == "Adsız 1" && mj.is_object() && mj.value("tur", std::string()) == "bina";
        yaz("cekirdek", ok ? "tamam" : "hata", "boş model \"" + h.belge->Ad() + "\", " + std::to_string(modelMetni.size()) + " bayt");
    }
    // 3) şablon (motorun verdiği bina JSON'u çekirdeğe yüklenir)
    if (h.cekirdek && !mr.ilkSablonBina.empty()) {
        const YuklemeSonucu y = h.cekirdek->Yukle(mr.ilkSablonBina, "sablon:" + mr.ilkSablon);
        if (y.basarili) {
            ModelYuklendi(h, y);
            modelMetni = h.cekirdek->Metin();
            yaz("sablon", "tamam", mr.ilkSablon + ": " + y.ozet.baslik + ", " + std::to_string(modelMetni.size()) + " bayt");
        } else {
            yaz("sablon", y.hata.find("henüz") != std::string::npos ? "atlandi" : "hata", y.hata);
        }
    } else {
        yaz("sablon", "atlandi", "motor ya da çekirdek yok");
    }
    // 4) .op4 kaydet / aç gidiş-dönüşü (bellekte; D'nin ZIP'i)
    if (h.cekirdek) {
        ProjeIcerigi ic;
        h.belge->IcerikTopla(ic);
        if (!ic.Var(proje_yolu::MODEL)) ic.Koy(proje_yolu::MODEL, modelMetni);
        ProjeManifest mf;
        mf.uygulamaSurumu = OP4_SURUM;
        std::string zip;
        if (!ProjeZipKur(ic, mf, zip, hata)) {
            yaz("kaydet_ac", hata.find("henüz") != std::string::npos ? "atlandi" : "hata", hata);
        } else {
            const OkumaSonucu o = ProjeZipCoz(zip);
            const std::string* geri = o.icerik.Al(proje_yolu::MODEL);
            const bool ayni = o.basarili && geri && *geri == *ic.Al(proje_yolu::MODEL);
            yaz("kaydet_ac", ayni ? "tamam" : "hata",
                std::to_string(zip.size()) + " bayt ZIP" + (o.basarili ? (ayni ? ", model baytları aynı" : ", model farklı") : "; " + o.hata));
        }
    }
    k.Kapat();
    // 5) ekran (WARP, ekran dışı)
    {
        Secenekler e = s;
        e.testEkran = Genis(kd.gecici) + L"\\oz_sinama.png";
        e.g = 640;
        e.y = 360;
        DizinKur(kd.gecici);
        const int kod = EkranTesti(e);
        yaz("ekran", kod == 0 ? "tamam" : "hata", Utf8(e.testEkran));
    }
    std::string olcum = "OP4OLCUM senaryo=oz_sinama";
    for (const auto& [ad, d] : durum) olcum += " " + ad + "=" + d;
    olcum += std::string(" durum=") + (tamam ? "gecti" : "kaldi");
    GunlukHam(olcum);
    Gunluk(tamam ? "ÖZ SINAMA BAŞARILI" : "ÖZ SINAMA BAŞARISIZ");
    return tamam ? 0 : 2;
}

}  // namespace op4
