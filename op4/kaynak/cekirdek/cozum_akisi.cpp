// op4 çekirdek — çözüm akışı (F1 iş 1.5). Sahibi: D (dosya-cozum). Bkz. cozum_akisi.h.
#include "cekirdek/cozum_akisi.h"

#include <cmath>
#include <cstdio>
#include <ctime>

#include <nlohmann/json.hpp>

#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/hizmetler.h"
#include "cekirdek/komut.h"
#include "cekirdek/proje_islemleri.h"
#include "cekirdek/proje_zip.h"
#include "cekirdek/sonuc.h"
#include "cekirdek/sonuc_ek.h"
#include "cekirdek/turkce.h"

namespace op4 {
namespace {
using nlohmann::json;
using ojson = nlohmann::ordered_json;

std::string MotorSurumu(const Hizmetler& h) {
    if (!h.motor) return {};
    const json s = json::parse(h.motor->Durum().surumJson, nullptr, false);
    return s.is_object() && s.contains("motor") && s["motor"].is_string() ? s["motor"].get<std::string>() : std::string();
}

}  // namespace

std::string SayiMetni(double v, int basamak) {
    if (!std::isfinite(v)) return "—";
    std::string s = OndalikVirgul(v, basamak);
    const bool eksi = !s.empty() && s[0] == '-';
    const size_t bas = eksi ? 1 : 0;
    size_t virgul = s.find(',');
    if (virgul == std::string::npos) virgul = s.size();
    for (size_t i = virgul; i > bas + 3; i -= 3) s.insert(i - 3, " ");
    return s;
}

std::string SureMetni(double ms) {
    if (!(ms >= 0)) ms = 0;
    if (ms < 1000) return std::to_string(static_cast<long long>(std::lround(ms))) + " ms";
    if (ms < 60000) return OndalikVirgul(std::round(ms / 100.0) / 10.0, 1) + " s";
    const long long sn = static_cast<long long>(ms / 1000.0);
    char b[32];
    std::snprintf(b, sizeof(b), "%lld dk %02lld s", sn / 60, sn % 60);
    return b;
}

CozumAkisi::CozumAkisi(Hizmetler& h, CozumAkisiAyari ayar) : h_(h), ayar_(std::move(ayar)) {}

CozumAkisi::~CozumAkisi() {
    // Süren isteklerin işleyicileri bu nesneyi gösteriyor: yanıtlar artık eşlenmesin.
    canli_.reset();
    if (h_.sonuc) h_.sonuc->degisti.Birak(aboneSonuc_);
    h_.modelYuklendi.Birak(aboneYuklendi_);
    h_.modelDegisti.Birak(aboneDegisti_);
    if (h_.motor && istekNo_) h_.motor->Iptal(istekNo_);
    if (istekNo_ && h_.bildirim) h_.bildirim->IlerlemeBitti("cozum");
    istekNo_ = kimlikIstek_ = 0;
}

void CozumAkisi::Yaz(const std::string& satir) const {
    if (h_.bildirim) h_.bildirim->KomutYaz(satir);
}

std::string CozumAkisi::Simdi() const { return ayar_.sabitZaman.empty() ? IsoZaman(std::time(nullptr)) : ayar_.sabitZaman; }

void CozumAkisi::Kur() {
    if (h_.sonuc) aboneSonuc_ = h_.sonuc->degisti.Abone([this] {
        BoyamayiGuncelle();
        degisti.Yay();
    });
    aboneYuklendi_ = h_.modelYuklendi.Abone([this](const ModelOzeti&) { Unut(); });
    aboneDegisti_ = h_.modelDegisti.Abone([this](const IslemRaporu&) {
        if (evre_ != CozumEvresi::Bos) modelDegistiCozumde_ = true;
        kimlikIstek_ = 0;  // süren bina_kimlik denetimi artık bu modele ait değil
    });
    h_.KareIsiEkle("cozum", [this](double t) { KareIsi(t); });
    if (h_.belge)
        h_.belge->KatkiEkle({"sonuc", 30, [this](ProjeIcerigi& i) { SonucuYaz(i); },
                             [this](const ProjeIcerigi& i, std::vector<std::string>& u) { SonucuOku(i, u); },
                             [this] { kimlikIstek_ = 0; }});
    if (!h_.komutlar) return;
    KomutIsleyici coz;
    coz.calistir = [this](KomutBaglami&) { Coz(); };
    coz.kullanilamazNedeni = [this](const Hizmetler& x) -> std::string {
        if (!x.cekirdek) return "Model çekirdeği hazır değil";
        if (!x.motor) return "Hesap motoru yok";
        if (evre_ != CozumEvresi::Bos) return "Çözüm sürüyor (durdurmak için: Çözümü iptal et)";
        if (x.cekirdek->Ozet().bos) return "Model boş: önce eleman ekleyin ya da şablondan başlayın";
        const MotorDurumOzeti d = x.motor->Durum();
        if (d.hazir && !d.basarili) return "Hesap motoru başlatılamadı: " + d.hata;
        return {};
    };
    h_.komutlar->Bagla("analiz.coz", coz);
    KomutIsleyici iptal;
    iptal.calistir = [this](KomutBaglami&) { Iptal(); };
    iptal.kullanilamazNedeni = [this](const Hizmetler&) {
        return evre_ == CozumEvresi::Cozuluyor ? std::string() : std::string("Süren çözüm yok");
    };
    h_.komutlar->Bagla("analiz.iptal", iptal);
    KomutIsleyici ozet;
    ozet.calistir = [this](KomutBaglami&) {
        if (h_.arayuz) h_.arayuz->PanelGoster("sonuc_ozeti", true);
        for (const OzetSatiri& s : OzetSatirlari()) Yaz(s.etiket + ": " + s.deger);
    };
    ozet.kullanilamazNedeni = [](const Hizmetler& x) {
        return x.sonuc && x.sonuc->Var() ? std::string() : std::string("Henüz sonuç yok: önce çözün (F5)");
    };
    h_.komutlar->Bagla("analiz.sonuc_ozeti", ozet);
    KomutIsleyici dc;
    dc.calistir = [this](KomutBaglami&) {
        if (!h_.gorunum) return;
        h_.gorunum->renkKipi = h_.gorunum->renkKipi == RenkKipi::Sonuc ? RenkKipi::Tur : RenkKipi::Sonuc;
        h_.gorunum->degisti.Yay();
        h_.gorunum->CizimIste();
    };
    dc.kullanilamazNedeni = [](const Hizmetler& x) {
        return x.sonuc && x.sonuc->Var() ? std::string() : std::string("Önce çözün (F5)");
    };
    dc.isaretli = [](const Hizmetler& x) { return x.gorunum && x.gorunum->renkKipi == RenkKipi::Sonuc; };
    h_.komutlar->Bagla("analiz.dc_renkleri", dc);
}

bool CozumAkisi::Coz() {
    auto hata = [this](const std::string& m) {
        sonHata_ = m;
        if (h_.bildirim) {
            h_.bildirim->KomutYaz("HATA: Çözülemedi: " + m);
            h_.bildirim->Tost("Çözülemedi: " + m, TostTuru::Hata);
        }
        return false;
    };
    if (evre_ != CozumEvresi::Bos) {
        Yaz("Çözüm zaten sürüyor (" + SureMetni(GecenMs()) + "); durdurmak için İPTAL.");
        return false;
    }
    if (!h_.cekirdek) return hata("model çekirdeği hazır değil.");
    if (!h_.motor) return hata("hesap motoru yok.");
    const ModelOzeti oz = h_.cekirdek->Ozet();
    if (oz.bos) return hata("model boş: önce eleman ekleyin ya da şablondan başlayın.");
    const MotorDurumOzeti md = h_.motor->Durum();
    if (md.hazir && !md.basarili) return hata("hesap motoru başlatılamadı: " + md.hata);
    const std::string metin = h_.cekirdek->Metin();
    istekKarma_ = MetinKarmasi(metin);
    istekSahneSurumu_ = h_.cekirdek->SahneSurumu();
    modelDegistiCozumde_ = false;
    sonHata_.clear();
    const bool anlat = h_.ayarlar && h_.ayarlar->motor.anlat;
    const int sd = h_.ayarlar ? h_.ayarlar->motor.sdSiniri : 6000;
    std::string girdi;
    girdi.reserve(metin.size() + 32);
    girdi += "{\"bina\":";
    girdi += metin;
    girdi += anlat ? ",\"anlat\":true}" : ",\"anlat\":false}";
    const std::string ayarlar = "{\"sd_siniri\":" + std::to_string(sd) + "}";
    evre_ = CozumEvresi::Cozuluyor;
    baslangicMs_ = sonIlerlemeMs_ = simdiMs_;
    const std::weak_ptr<int> canli = canli_;
    istekNo_ = h_.motor->Gonder("bina_coz", girdi, ayarlar, [this, canli](const MotorYaniti& y) {
        if (!canli.expired()) YanitGeldi(y);
    });
    if (h_.sonuc) {
        h_.sonuc->surenIstek = istekNo_;
        h_.sonuc->surenBaslangicMs = simdiMs_;
    }
    if (h_.bildirim) {
        h_.bildirim->Ilerleme("cozum", "Çözülüyor…", -1.0f, [this, canli] {
            if (!canli.expired()) Iptal();
        });
        h_.bildirim->KomutYaz("Çözüm başladı: " + ModelOzetMetni(oz) + (md.hazir ? "" : " (motor hazır olunca)") + ".");
    }
    degisti.Yay();
    return true;
}

bool CozumAkisi::Iptal() {
    if (evre_ != CozumEvresi::Cozuluyor || !h_.motor) return false;
    if (!h_.motor->Iptal(istekNo_)) return false;
    evre_ = CozumEvresi::IptalEdiliyor;
    if (h_.bildirim) {
        h_.bildirim->KomutYaz("Çözüm iptal ediliyor…");
        h_.bildirim->Ilerleme("cozum", "İptal ediliyor…", -1.0f, nullptr);
    }
    degisti.Yay();
    return true;
}

void CozumAkisi::Unut() {
    kimlikIstek_ = 0;
    if (evre_ == CozumEvresi::Bos) return;
    if (h_.motor && istekNo_) h_.motor->Iptal(istekNo_);
    istekNo_ = 0;
    evre_ = CozumEvresi::Bos;
    if (h_.sonuc) h_.sonuc->surenIstek = 0;
    if (h_.bildirim) {
        h_.bildirim->IlerlemeBitti("cozum");
        h_.bildirim->KomutYaz("Süren çözüm bırakıldı (yeni model yüklendi).");
    }
    degisti.Yay();
}

void CozumAkisi::KareIsi(double simdiMs) {
    simdiMs_ = simdiMs;
    if (evre_ == CozumEvresi::Cozuluyor && h_.bildirim && simdiMs - sonIlerlemeMs_ >= ayar_.ilerlemeAraligiMs) {
        sonIlerlemeMs_ = simdiMs;
        const std::weak_ptr<int> canli = canli_;
        h_.bildirim->Ilerleme("cozum", "Çözülüyor… " + SureMetni(GecenMs()), -1.0f, [this, canli] {
            if (!canli.expired()) Iptal();
        });
    }
}

void CozumAkisi::YanitGeldi(const MotorYaniti& y) {
    if (istekNo_ == 0 || y.no != istekNo_) return;  // unutulmuş ya da eski istek
    const double gecen = GecenMs();
    istekNo_ = 0;
    evre_ = CozumEvresi::Bos;
    if (h_.sonuc) h_.sonuc->surenIstek = 0;
    if (h_.bildirim) h_.bildirim->IlerlemeBitti("cozum");
    auto hata = [this](const std::string& baslik, const std::string& m) {
        sonHata_ = m;
        if (h_.bildirim) {
            h_.bildirim->KomutYaz("HATA: " + baslik + ": " + m);
            h_.bildirim->Tost(baslik + ": " + m, TostTuru::Hata);
        }
    };
    switch (y.durum) {
        case YanitDurumu::Tamam: {
            SonucOzeti o;
            std::string veri, h;
            if (!CozumYanitiniCoz(y.yanit, o, veri, h)) {
                hata("Çözüm", h);
                break;
            }
            o.tarih = Simdi();
            o.motorSurumu = MotorSurumu(h_);
            if (o.sureMs <= 0) o.sureMs = y.sureMs;
            o.sahneSurumu = istekSahneSurumu_;
            SonucEslemesi e = h_.cekirdek ? h_.cekirdek->SonucEsle(veri) : SonucEslemesi{};
            if (!e.basarili) {
                const std::string neden = e.hata;
                e = TasarimdanEsle(veri);
                e.uyarilar.insert(e.uyarilar.begin(), "Model çekirdeği sonuçları eşleyemedi (" + neden +
                                                          "); genel model çubukları tasarım tablosundan doğrudan eşlendi.");
            }
            EslemeyiYerlestir(o, std::move(e));
            cozulenKarma_ = istekKarma_;
            yeniSonuc_ = true;
            const std::string metin = o.ozetMetni;
            const double enBuyuk = o.enBuyukDc;
            if (ayar_.olcum) {
                char b[256];
                std::snprintf(b, sizeof(b),
                              "OP4OLCUM senaryo=cozum motor_ms=%.0f toplam_ms=%.0f sd=%llu kombinasyon=%llu en_buyuk_dc=%.6f "
                              "eleman=%llu",
                              o.sureMs, gecen, static_cast<unsigned long long>(o.sdSayisi),
                              static_cast<unsigned long long>(o.kombinasyonSayisi), o.enBuyukDc,
                              static_cast<unsigned long long>(o.elemanlar.size()));
                ayar_.olcum(b);
            }
            if (h_.sonuc) {
                h_.sonuc->Ata(std::move(o), std::make_shared<const std::string>(std::move(veri)));
                if (modelDegistiCozumde_ || (h_.cekirdek && h_.cekirdek->SahneSurumu() != istekSahneSurumu_))
                    h_.sonuc->EskiIsaretle();
            }
            const std::string ozet = "Çözüm tamam (" + SureMetni(gecen) + "): " + metin +
                                     (enBuyuk >= 0 ? "; en büyük D/C " + OndalikVirgul(enBuyuk, 3) : std::string());
            if (h_.bildirim) {
                h_.bildirim->KomutYaz(ozet);
                h_.bildirim->Tost(ozet, enBuyuk > 1.0 ? TostTuru::Uyari : TostTuru::Basari);
                if (h_.sonuc)
                    for (const std::string& u : h_.sonuc->Ozet().uyarilar) h_.bildirim->KomutYaz("Uyarı: " + u);
            }
            if (h_.arayuz) h_.arayuz->PanelGoster("sonuc_ozeti", true);
            break;
        }
        case YanitDurumu::Iptal:
            sonHata_ = "Çözüm iptal edildi.";
            if (h_.bildirim) {
                h_.bildirim->KomutYaz(sonHata_);
                h_.bildirim->Tost(sonHata_, TostTuru::Bilgi);
            }
            break;
        case YanitDurumu::Hata:
            hata("Çözüm", y.hata.empty() ? std::string("hesap motoru hata döndürdü") : y.hata);
            break;
        case YanitDurumu::MotorHatasi:
        default:
            hata("Hesap motoru", y.hata.empty() ? std::string("yanıt alınamadı") : y.hata);
            break;
    }
    degisti.Yay();
}

void CozumAkisi::BoyamayiGuncelle() {
    if (!h_.gorunum || !h_.sonuc) return;
    if (!h_.sonuc->Var()) {
        if (h_.gorunum->sonuc || h_.gorunum->renkKipi == RenkKipi::Sonuc) {
            h_.gorunum->sonuc = nullptr;
            h_.gorunum->renkKipi = RenkKipi::Tur;
            h_.gorunum->degisti.Yay();
            h_.gorunum->CizimIste();
        }
        return;
    }
    auto b = std::make_shared<SonucBoyamasi>(*BoyamaKur(h_.sonuc->Ozet(), ++boyamaSurumu_));
    b->eski = h_.sonuc->Eski();
    if (b->eski) b->aciklama += " — sonuçlar eski";
    h_.gorunum->sonuc = std::move(b);
    if (yeniSonuc_) {
        h_.gorunum->renkKipi = RenkKipi::Sonuc;
        yeniSonuc_ = false;
    }
    h_.gorunum->degisti.Yay();
    h_.gorunum->CizimIste();
}

// ---- .op4 sonuc/ ------------------------------------------------------------------------------------------------------
void CozumAkisi::SonucuYaz(ProjeIcerigi& i) const {
    if (!h_.sonuc || !h_.sonuc->Var()) {
        i.girdiler.erase(proje_yolu::SONUC_OZETI);
        i.girdiler.erase(proje_yolu::SONUC_VERISI);
        return;
    }
    ojson j = ojson::parse(SonucOzetiJson(h_.sonuc->Ozet()));
    j["model_karmasi"] = cozulenKarma_;
    j["eski"] = h_.sonuc->Eski();
    i.Koy(proje_yolu::SONUC_OZETI, j.dump() + "\n");
    if (h_.sonuc->Veri()) i.Koy(proje_yolu::SONUC_VERISI, *h_.sonuc->Veri());
    else i.girdiler.erase(proje_yolu::SONUC_VERISI);
}

void CozumAkisi::SonucuOku(const ProjeIcerigi& i, std::vector<std::string>& uyarilar) {
    const std::string* metin = i.Al(proje_yolu::SONUC_OZETI);
    if (!metin || !h_.sonuc || !h_.cekirdek) return;
    SonucOzeti o;
    std::string hata;
    if (!SonucOzetiOku(*metin, o, hata)) {
        uyarilar.push_back("Kayıtlı sonuçlar okunamadı: " + hata);
        return;
    }
    const json ek = json::parse(*metin, nullptr, false);
    const std::string kayitliKarma = ek.is_object() ? ek.value("model_karmasi", std::string()) : std::string();
    const bool eskiKaydedildi = ek.is_object() && ek.value("eski", false);
    const std::string* v = i.Al(proje_yolu::SONUC_VERISI);
    o.sahneSurumu = h_.cekirdek->SahneSurumu();
    const std::string kimlik = o.cozumKimligi;
    const bool ayni = !kayitliKarma.empty() && kayitliKarma == MetinKarmasi(h_.cekirdek->Metin());
    cozulenKarma_ = kayitliKarma;
    yeniSonuc_ = true;
    h_.sonuc->Ata(std::move(o), v ? std::make_shared<const std::string>(*v) : nullptr);
    if (ayni && !eskiKaydedildi) {
        Yaz("Kayıtlı sonuçlar modelle eşleşti; D/C renkleri güncel.");
        return;
    }
    h_.sonuc->EskiIsaretle();
    if (eskiKaydedildi) {
        Yaz("Kayıtlı sonuçlar kaydedilirken de eskiydi; yeniden çözün (F5).");
        return;
    }
    KimlikDenetle(kimlik);
}

void CozumAkisi::KimlikDenetle(const std::string& kimlik) {
    if (!h_.motor || !h_.cekirdek || kimlik.empty()) {
        Yaz("Kayıtlı sonuçlar doğrulanamadı (hesap motoru yok); \"Sonuçlar eski\" olarak gösteriliyor.");
        return;
    }
    const uint64_t sayac = h_.belge ? h_.belge->DegisiklikSayaci() : 0;
    kimlikIstek_ = h_.motor->Gonder("bina_kimlik", "{\"bina\":" + h_.cekirdek->Metin() + "}", "{}",
                                    [this, kimlik, sayac, canli = std::weak_ptr<int>(canli_)](const MotorYaniti& y) {
                                        if (canli.expired() || kimlikIstek_ == 0 || y.no != kimlikIstek_) return;
                                        kimlikIstek_ = 0;
                                        std::string gelen;
                                        if (y.durum == YanitDurumu::Tamam) {
                                            const json j = json::parse(y.yanit, nullptr, false);
                                            if (j.is_object() && j.contains("cozum_kimligi") && j["cozum_kimligi"].is_string())
                                                gelen = j["cozum_kimligi"].get<std::string>();
                                        }
                                        if (gelen.empty()) {
                                            Yaz("Kayıtlı sonuçlar doğrulanamadı (bina_kimlik: " +
                                                (y.hata.empty() ? std::string("yanıt yok") : y.hata) +
                                                "); \"Sonuçlar eski\" olarak gösteriliyor.");
                                            return;
                                        }
                                        const bool degismedi = !h_.belge || h_.belge->DegisiklikSayaci() == sayac;
                                        if (gelen != kimlik || !degismedi || !h_.sonuc || !h_.sonuc->Var() ||
                                            h_.sonuc->Ozet().cozumKimligi != kimlik) {
                                            Yaz("Kayıtlı sonuçlar bu modele ait değil (cozum_kimligi farklı); yeniden "
                                                "çözün (F5).");
                                            return;
                                        }
                                        SonucOzeti o = h_.sonuc->Ozet();
                                        auto v = h_.sonuc->Veri();
                                        cozulenKarma_ = MetinKarmasi(h_.cekirdek->Metin());
                                        h_.sonuc->Ata(std::move(o), std::move(v));
                                        Yaz("Kayıtlı sonuçlar modelle eşleşti (bina_kimlik); D/C renkleri güncel.");
                                    });
}

// ---- gösterim --------------------------------------------------------------------------------------------------------
std::string CozumAkisi::DurumMetni() const {
    switch (evre_) {
        case CozumEvresi::Cozuluyor: return "Çözülüyor… " + SureMetni(GecenMs());
        case CozumEvresi::IptalEdiliyor: return "İptal ediliyor…";
        case CozumEvresi::Bos: break;
    }
    if (!h_.sonuc || !h_.sonuc->Var()) return {};
    if (h_.sonuc->Eski()) return "Sonuçlar eski";
    const double dc = h_.sonuc->Ozet().enBuyukDc;
    return dc >= 0 ? "D/C en büyük " + OndalikVirgul(dc, 3) : std::string("Sonuçlar güncel");
}

std::vector<OzetSatiri> CozumAkisi::OzetSatirlari() const {
    std::vector<OzetSatiri> s;
    if (!h_.sonuc || !h_.sonuc->Var()) return s;
    const SonucOzeti& o = h_.sonuc->Ozet();
    const CozumToplamlari t = OzetToplamlari(o);
    s.push_back({"Durum", h_.sonuc->Eski() ? "Sonuçlar eski (model çözümden sonra değişti)" : "Güncel",
                 h_.sonuc->Eski() ? 0xD9A13BFFu : 0x4C9A63FFu});
    s.push_back({"Serbestlik derecesi", SayiMetni(static_cast<double>(o.sdSayisi), 0), 0});
    s.push_back({"Kombinasyon", SayiMetni(static_cast<double>(o.kombinasyonSayisi), 0), 0});
    s.push_back({"ΣG", SayiMetni(t.G, 2) + " kN", 0});
    s.push_back({"ΣQ", SayiMetni(t.Q, 2) + " kN", 0});
    std::string dc = o.enBuyukDc >= 0 ? OndalikVirgul(o.enBuyukDc, 3) : std::string("tasarım yok");
    if (o.enBuyukDc >= 0 && o.enBuyukDcElemani.Gecerli()) dc += " (" + KimlikMetni(o.enBuyukDcElemani) + ")";
    s.push_back({"En büyük D/C", dc, o.enBuyukDc >= 0 ? DcRengi(o.enBuyukDc) : 0});
    s.push_back({"D/C > 1", std::to_string(o.asanSayisi) + " eleman", o.asanSayisi ? 0xC8372DFFu : 0});
    s.push_back({"Süre", SureMetni(o.sureMs), 0});
    if (!o.tarih.empty()) s.push_back({"Tarih", o.tarih, 0});
    if (!o.cozumKimligi.empty()) s.push_back({"Çözüm kimliği", o.cozumKimligi, 0});
    return s;
}

}  // namespace op4
