// op4 çekirdek — dosya işlemleri akışı (F1 iş 1.6). Sahibi: D (dosya-cozum). Bkz. proje_islemleri.h.
#include "cekirdek/proje_islemleri.h"

#include <algorithm>
#include <cstdlib>
#include <ctime>
#include <filesystem>
#include <random>

#include <nlohmann/json.hpp>

#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/hizmetler.h"
#include "cekirdek/komut.h"
#include "cekirdek/model_cekirdegi.h"
#include "cekirdek/motor_hizmeti.h"
#include "cekirdek/proje_belgesi.h"
#include "cekirdek/proje_onizleme.h"
#include "cekirdek/proje_zip.h"
#include "cekirdek/sonuc.h"
#include "platform/dosya_sistemi.h"

namespace op4 {
namespace {
namespace fs = std::filesystem;
using nlohmann::json;

fs::path Yol(const std::string& utf8) {
    return fs::path(std::u8string(reinterpret_cast<const char8_t*>(utf8.data()), utf8.size()));
}
std::string Utf8(const fs::path& p) {
    const std::u8string s = p.u8string();
    return std::string(reinterpret_cast<const char*>(s.data()), s.size());
}
std::string DosyaAdi(const std::string& yol) {
    const size_t i = yol.find_last_of("\\/");
    return i == std::string::npos ? yol : yol.substr(i + 1);
}
std::string Klasor(const std::string& yol) {
    const size_t i = yol.find_last_of("\\/");
    return i == std::string::npos ? std::string() : yol.substr(0, i);
}
std::string KucukUzanti(const std::string& yol) {
    const std::string ad = DosyaAdi(yol);
    const size_t n = ad.find_last_of('.');
    if (n == std::string::npos) return {};
    std::string u = ad.substr(n);
    for (char& c : u)
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    return u;
}
// Uzantısız dosya adı: "C:/x/bina.matris" → "bina".
std::string Govde(const std::string& yol) {
    const std::string ad = DosyaAdi(yol);
    const size_t n = ad.find_last_of('.');
    return n == std::string::npos || n == 0 ? ad : ad.substr(0, n);
}
std::string UzantiDegistir(const std::string& yol, const std::string& uzanti) {
    const std::string govde = Govde(yol);
    const std::string k = Klasor(yol);
    return k.empty() ? govde + uzanti : Utf8(Yol(k) / Yol(govde + uzanti));
}
std::string Birlestir(const std::string& klasor, const std::string& ad) {
    return klasor.empty() ? ad : Utf8(Yol(klasor) / Yol(ad));
}
std::string GuvenliAd(std::string ad) {
    for (char& c : ad)
        if (c == '\\' || c == '/' || c == ':' || c == '*' || c == '?' || c == '"' || c == '<' || c == '>' || c == '|' ||
            (static_cast<unsigned char>(c) < 32))
            c = '_';
    while (!ad.empty() && (ad.back() == ' ' || ad.back() == '.')) ad.pop_back();
    while (!ad.empty() && ad.front() == ' ') ad.erase(ad.begin());
    return ad;
}
std::string Kirp(std::string_view s) {
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t')) s.remove_prefix(1);
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t' || s.back() == '\r' || s.back() == '\n')) s.remove_suffix(1);
    if (s.size() >= 2 && s.front() == '"' && s.back() == '"') s = s.substr(1, s.size() - 2);
    return std::string(s);
}
std::string KurtarmaKimligi() {
    std::random_device rd;
    std::mt19937_64 u(rd() ^ (static_cast<uint64_t>(std::time(nullptr)) << 20) ^ SurecNo());
    static const char* const kHex = "0123456789abcdef";
    std::string s;
    for (int i = 0; i < 32; ++i) {
        if (i == 8 || i == 12 || i == 16 || i == 20) s += '-';
        s += kHex[u() & 15u];
    }
    return s;
}
bool SablonAdiGecerli(const std::string& ad) {
    if (ad.empty() || ad.size() > 80) return false;
    return std::all_of(ad.begin(), ad.end(), [](char c) {
        return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-' || c == '_';
    });
}
std::string MetinAl(const json& j, const char* ad) {
    return j.is_object() && j.contains(ad) && j[ad].is_string() ? j[ad].get<std::string>() : std::string();
}

// Korunan girdiler: açılan / yazılan arşivin her şeyi; D'nin katkılarının HER kaydetmede yeniden yazdığı (ya da sildiği)
// girdiler bellekte ikinci kez tutulmaz (sonuc/veri.json 50 MB'a varabilir). Diğer paketlerin katkı girdileri (görünüm,
// seçim) korunur: katkı henüz yoksa da dosyadan kaybolmasınlar.
ProjeIcerigi Korunacaklar(ProjeIcerigi i) {
    for (const char* y : {proje_yolu::MIMETYPE, proje_yolu::MODEL, proje_yolu::SONUC_OZETI, proje_yolu::SONUC_VERISI,
                          proje_yolu::ONIZLEME})
        i.girdiler.erase(y);
    return i;
}

}  // namespace

std::string ModelOzetMetni(const ModelOzeti& o) {
    std::string s = std::to_string(o.dugum) + " düğüm, " + std::to_string(o.cubuk) + " çubuk, " + std::to_string(o.panel) +
                    " panel";
    if (o.kat) s += ", " + std::to_string(o.kat) + " kat";
    return s;
}

std::vector<SablonBilgisi> SablonDizini(const std::string& veriDizini, std::string& hata) {
    std::vector<SablonBilgisi> o;
    std::string metin;
    if (!DosyaOku(Birlestir(Birlestir(veriDizini, "sablonlar"), "dizin.json"), metin, hata)) return o;
    const json j = json::parse(metin, nullptr, false);
    if (j.is_discarded() || !j.contains("sablonlar") || !j["sablonlar"].is_array()) {
        hata = "sablonlar/dizin.json okunamadı.";
        return o;
    }
    for (const json& s : j["sablonlar"]) {
        SablonBilgisi b;
        b.ad = MetinAl(s, "ad");
        b.baslik = MetinAl(s, "baslik");
        b.aciklama = MetinAl(s, "aciklama");
        b.sistem = MetinAl(s, "sistem");
        b.dosya = MetinAl(s, "dosya");
        b.kat = s.value("kat", 0);
        b.aks = MetinAl(s, "aks");
        if (!b.ad.empty()) o.push_back(std::move(b));
    }
    return o;
}

DosyaIslemleri::DosyaIslemleri(Hizmetler& h, DosyaIslemleriAyari ayar, DosyaPlatformu platform)
    : h_(h), ayar_(std::move(ayar)), platform_(std::move(platform)) {
    if (!ayar_.kurtarmaDizini.empty()) {
        DizinKur(ayar_.kurtarmaDizini);
        kurtarmaKok_ = Birlestir(ayar_.kurtarmaDizini, KurtarmaKimligi());
        kurtarmaZip_ = kurtarmaKok_ + ".op4";
        oturumKilidi_.Al(kurtarmaKok_ + ".kilit");  // kurtarma kaydının sahibi yaşıyor (başka oturum silmesin)
    }
}

DosyaIslemleri::~DosyaIslemleri() {
    if (h_.kapatmaOnayi) h_.kapatmaOnayi = nullptr;
    if (h_.belge) {
        h_.belge->KatkiKaldir("model");  // katkılar bu nesneyi gösterir; belge kabukta daha uzun yaşar (S15)
        h_.belge->KatkiKaldir("onizleme");
        h_.belge->kirliDegisti.Birak(aboneler_[0]);
        h_.belge->yolDegisti.Birak(aboneler_[1]);
        h_.belge->acildi.Birak(aboneler_[2]);
        h_.belge->kaydedildi.Birak(aboneler_[3]);
    }
    // Temiz kapanış: belge temizse ya da kullanıcı kapanışı onayladıysa ("Kaydetme" dahil) kurtarma kaydı gereksizdir.
    // Onaysız kapanışta (ör. pencere WM_CLOSE'u kapatmaOnayi'na bağlamadıysa) kayıt kalır, bir sonraki açılış sorar.
    if (h_.belge && (!h_.belge->Kirli() || kapanisOnaylandi_)) KurtarmaKaydiniSil();
    oturumKilidi_.Birak();
    AyarlariKaydet();
}

void DosyaIslemleri::Kur() {
    ProjeBelgesi& b = *h_.belge;
    b.KatkiEkle({"model", 0,
                 [this](ProjeIcerigi& i) {
                     if (h_.cekirdek) i.Koy(proje_yolu::MODEL, h_.cekirdek->Metin());
                 },
                 {}, {}});
    b.KatkiEkle({"onizleme", 40,
                 [this](ProjeIcerigi& i) {
                     if (!h_.cekirdek) return;
                     std::string png = OnizlemePng(*h_.cekirdek->Sahne(), 256);
                     if (png.empty()) i.girdiler.erase(proje_yolu::ONIZLEME);
                     else i.Koy(proje_yolu::ONIZLEME, std::move(png));
                 },
                 {}, {}});
    aboneler_[0] = b.kirliDegisti.Abone([this](const bool& kirli) {
        if (kirli) kapanisOnaylandi_ = false;  // onaydan sonra yeni değişiklik: yeniden sorulur
        BasligiYay();
    });
    aboneler_[1] = b.yolDegisti.Abone([this](const std::string& yol) {
        BasligiYay();
        if (platform_.belgeYoluDegisti) platform_.belgeYoluDegisti(yol);
    });
    aboneler_[2] = b.acildi.Abone([this] { BasligiYay(); });
    aboneler_[3] = b.kaydedildi.Abone([this](const std::string&) { BasligiYay(); });
    h_.kapatmaOnayi = [this] { return KapatmaOnayi(); };
    h_.KareIsiEkle("dosya", [this](double t) { KareIsi(t); });

    if (!h_.komutlar) return;
    auto bagla = [this](const char* id, std::function<void(KomutBaglami&)> f,
                        std::function<std::string(const Hizmetler&)> neden = {}) {
        KomutIsleyici k;
        k.calistir = std::move(f);
        k.kullanilamazNedeni = std::move(neden);
        if (!h_.komutlar->Bagla(id, std::move(k)) && h_.bildirim) h_.bildirim->KomutYaz(std::string("İç hata: komut yok: ") + id);
    };
    auto cekirdekYok = [](const Hizmetler& x) { return x.cekirdek ? std::string() : std::string("Model çekirdeği hazır değil"); };
    bagla("dosya.yeni", [this](KomutBaglami&) { Yeni(); }, cekirdekYok);
    bagla("dosya.yeni_sablon",
          [this](KomutBaglami& k) {
              const std::string ad = Kirp(k.arguman);
              if (!ad.empty()) {
                  SablondanYeni(ad);
                  return;
              }
              if (platform_.sablonSeciciGoster) {
                  platform_.sablonSeciciGoster();
                  return;
              }
              std::string liste;
              for (const SablonBilgisi& s : Sablonlar()) liste += (liste.empty() ? "" : ", ") + s.ad;
              Bilgi("Şablonlar: " + (liste.empty() ? std::string("(yok)") : liste) + ". Kullanım: ŞABLONDAN <ad>", false);
          },
          cekirdekYok);
    bagla("dosya.ac", [this](KomutBaglami& k) {
        const std::string y = Kirp(k.arguman);
        if (y.empty()) AcSor();
        else Ac(y);
    }, cekirdekYok);
    bagla("dosya.kaydet", [this](KomutBaglami&) { Kaydet(); }, cekirdekYok);
    bagla("dosya.farkli_kaydet", [this](KomutBaglami& k) { FarkliKaydet(Kirp(k.arguman)); }, cekirdekYok);
    bagla("dosya.ice_aktar", [this](KomutBaglami& k) {
        const std::string y = Kirp(k.arguman);
        if (y.empty()) IceAktarSor();
        else Ac(y);
    }, cekirdekYok);
    bagla("dosya.bina_disa", [this](KomutBaglami& k) { BinaDisaAktar(Kirp(k.arguman)); },
          [](const Hizmetler& x) { return x.cekirdek ? std::string() : std::string("Model çekirdeği hazır değil"); });
    bagla("dosya.ifc_disa", [this](KomutBaglami& k) { IfcDisaAktar(Kirp(k.arguman)); },
          [](const Hizmetler& x) {
              if (!x.cekirdek) return std::string("Model çekirdeği hazır değil");
              return x.cekirdek->Ozet().bos ? std::string("Model boş: dışa aktarılacak eleman yok") : std::string();
          });
    bagla("dosya.kurtar",
          [this](KomutBaglami& k) {
              std::string a = Kirp(k.arguman);
              for (char& c : a)
                  if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
              if (a.empty()) {
                  KurtarmalariYenile();
                  if (kurtarmalar_.empty()) {
                      Bilgi("Kurtarılacak kayıt yok.", true);
                      return;
                  }
                  kurtarmaSorusu_ = true;
                  kurtarmaDegisti.Yay();
                  if (platform_.kurtarmaGoster) platform_.kurtarmaGoster();
                  for (size_t i = 0; i < kurtarmalar_.size(); ++i)
                      Bilgi("Kurtarma " + std::to_string(i + 1) + ": " + kurtarmalar_[i].baslik + " (" + kurtarmalar_[i].zaman +
                                ")  →  KURTAR " + std::to_string(i + 1) + " | KURTAR sil " + std::to_string(i + 1),
                            false);
                  return;
              }
              if (a == "sonra") {
                  KurtarmaSonra();
                  return;
              }
              const bool sil = a.rfind("sil", 0) == 0;
              const std::string no = Kirp(sil ? a.substr(3) : a);
              const long n = std::strtol(no.c_str(), nullptr, 10);
              if (n < 1 || static_cast<size_t>(n) > kurtarmalar_.size()) {
                  Bilgi("Kurtarma kaydı numarası geçersiz: " + no, false);
                  return;
              }
              if (sil) KurtarmaSil(static_cast<size_t>(n - 1));
              else Kurtar(static_cast<size_t>(n - 1));
          },
          {});
    bagla("dosya.cikis", [this](KomutBaglami&) { Cikis(); });
}

// ---- yardımcılar -----------------------------------------------------------------------------------------------------
void DosyaIslemleri::Bilgi(const std::string& satir, bool tost) {
    if (!h_.bildirim) return;
    h_.bildirim->KomutYaz(satir);
    if (tost) h_.bildirim->Tost(satir, TostTuru::Basari);
}

bool DosyaIslemleri::HataBildir(const std::string& baslik, const std::string& hata) {
    if (h_.bildirim) {
        h_.bildirim->KomutYaz("HATA: " + baslik + ": " + hata);
        h_.bildirim->Tost(baslik + ": " + hata, TostTuru::Hata);
    }
    return false;
}

std::string DosyaIslemleri::Simdi() const { return ayar_.sabitZaman.empty() ? IsoZaman(std::time(nullptr)) : ayar_.sabitZaman; }

void DosyaIslemleri::BasligiYay() {
    if (platform_.pencereBasligi && h_.belge) platform_.pencereBasligi(h_.belge->PencereBasligi());
}

ProjeManifest DosyaIslemleri::ManifestKur() const {
    ProjeManifest m;
    m.uygulamaSurumu = h_.bilgi.surum;
    m.kaydedildi = Simdi();
    if (h_.cekirdek) m.modelOzeti = ModelOzetMetni(h_.cekirdek->Ozet());
    if (h_.motor) {
        const json s = json::parse(h_.motor->Durum().surumJson, nullptr, false);
        m.motorSurumu = MetinAl(s, "motor");
    }
    return m;
}

std::string DosyaIslemleri::OneriYolu(const std::string& uzanti) const {
    if (h_.belge && !h_.belge->Yol().empty()) return UzantiDegistir(h_.belge->Yol(), uzanti);
    if (!eskiKaynak_.empty()) return UzantiDegistir(eskiKaynak_, uzanti);
    std::string ad = GuvenliAd(h_.cekirdek ? h_.cekirdek->Ozet().baslik : std::string());
    if (ad.empty() && h_.belge) ad = GuvenliAd(h_.belge->Ad());
    if (ad.empty()) ad = "proje";
    return Birlestir(h_.ayarlar ? h_.ayarlar->dosya.sonKlasor : std::string(), ad + uzanti);
}

void DosyaIslemleri::SonDosya(const std::string& yol) {
    if (h_.ayarlar) {
        DosyaAyarlari& d = h_.ayarlar->dosya;
        SonDosyaEkle(d.sonDosyalar, yol, static_cast<size_t>(std::max(d.sonDosyaSayisi, 0)));
        d.sonKlasor = Klasor(yol);
        AyarlariKaydet();
    }
    if (platform_.sonBelgeEkle) platform_.sonBelgeEkle(yol);
}

bool DosyaIslemleri::AyarlariKaydet(bool zorla) {
    if (!h_.ayarlar || h_.bilgi.ayarDizini.empty()) return false;
    const std::string m = AyarlariYaz(*h_.ayarlar);
    if (!zorla && m == sonAyarMetni_) return true;
    const std::string yol = Birlestir(h_.bilgi.ayarDizini, "ayarlar.json");
    std::string eski, hata;
    if (!zorla && sonAyarMetni_.empty() && DosyaOku(yol, eski, hata) && eski == m) {
        sonAyarMetni_ = m;
        return true;
    }
    DizinKur(h_.bilgi.ayarDizini);
    if (!AtomikYaz(yol, m, false, hata)) {
        if (h_.bildirim) h_.bildirim->KomutYaz("Uyarı: ayarlar kaydedilemedi: " + hata);
        sonAyarMetni_ = m;  // her karede yeniden denenmesin
        return false;
    }
    sonAyarMetni_ = m;
    return true;
}

std::vector<SablonBilgisi> DosyaIslemleri::Sablonlar() const {
    std::string hata;
    return SablonDizini(h_.bilgi.veriDizini, hata);
}

// ---- belge durumu ----------------------------------------------------------------------------------------------------
void DosyaIslemleri::YeniBelge(const YuklemeSonucu& y, int adsizNo) {
    ModelYuklendi(h_, y);
    h_.belge->Sifirla();
    korunanlar_ = ProjeIcerigi{};
    eskiKaynak_.clear();
    okumaKilidi_.Birak();
    h_.belge->Acildi("", adsizNo, false);
    sonOtomatikSayac_ = h_.belge->DegisiklikSayaci();
    kirliBaslangicMs_ = -1;
    KurtarmaKaydiniSil();
}

bool DosyaIslemleri::OkunaniYukle(OkumaSonucu& o, const std::string& yol, bool kurtarma, const std::string& asilYol) {
    const bool eskiBicim = o.bicim != DosyaBicimi::Op4;
    const std::string ad = DosyaAdi(kurtarma && !asilYol.empty() ? asilYol : yol);
    const std::string* model = o.icerik.Al(proje_yolu::MODEL);
    YuklemeSonucu y = model ? h_.cekirdek->Yukle(*model, (kurtarma ? "kurtarma:" : "dosya:") + yol)
                            : h_.cekirdek->YeniBos("Adsız " + std::to_string(adsizSayaci_ + 1));
    if (!y.basarili) return HataBildir("'" + ad + "' açılamadı", "Model yüklenemedi: " + y.hata);
    const DenetimSonucu d = h_.cekirdek->Denetle();
    ModelYuklendi(h_, y);
    size_t yazilan = 0;
    for (const std::string& u : d.uyarilar)
        if (++yazilan <= 20 && h_.bildirim) h_.bildirim->KomutYaz("Denetim: " + u);
    h_.belge->Sifirla();
    korunanlar_ = Korunacaklar(o.icerik);
    std::vector<std::string> uyarilar = o.uyarilar;
    h_.belge->IcerikDagit(o.icerik, uyarilar);
    const std::string belgeYolu = kurtarma ? asilYol : (eskiBicim ? std::string() : yol);
    if (belgeYolu.empty()) ++adsizSayaci_;
    eskiKaynak_ = eskiBicim && !kurtarma ? yol : std::string();
    // İçe aktarılan eski biçimli belge başlıkta "Adsız N" yerine kaynak dosyanın gövdesiyle görünür (S15).
    h_.belge->Acildi(belgeYolu, adsizSayaci_, o.dahaYeniSurum, eskiKaynak_.empty() ? std::string() : Govde(eskiKaynak_));
    if (kurtarma) h_.belge->KirliIsaretle();
    sonOtomatikSayac_ = kurtarma ? 0 : h_.belge->DegisiklikSayaci();
    kirliBaslangicMs_ = -1;
    if (!kurtarma) KurtarmaKaydiniSil();
    if (!kurtarma && !eskiBicim) okumaKilidi_.Ac(yol);
    else okumaKilidi_.Birak();
    if (h_.bildirim)
        for (const std::string& u : uyarilar) h_.bildirim->KomutYaz("Uyarı: " + u);
    if (!kurtarma) SonDosya(yol);
    if (kurtarma) Bilgi("Kurtarıldı: " + ad + " (kaydedilmemiş değişiklikler geri geldi; kaydetmeyi unutmayın).", true);
    else if (eskiBicim) Bilgi("İçe aktarıldı: " + ad + " — kaydederken yeni .op4 biçimi yazılır.", true);
    else Bilgi("Açıldı: " + ad + (o.dahaYeniSurum ? " (salt okunur)" : ""), true);
    if (o.dahaYeniSurum && h_.bildirim)
        h_.bildirim->Tost("Bu proje daha yeni bir op4 sürümüyle kaydedilmiş; salt okunur açıldı.", TostTuru::Uyari);
    return true;
}

// ---- işlemler --------------------------------------------------------------------------------------------------------
bool DosyaIslemleri::KaydedilmemisSor(std::string_view eylem) {
    if (!h_.belge || !h_.belge->Kirli()) return true;
    const std::string metin = "\"" + h_.belge->Ad() + "\" içinde kaydedilmemiş değişiklikler var.\n" + std::string(eylem) +
                              " kaydedilsin mi?";
    const int s = h_.iletisim ? h_.iletisim->Soru("Kaydedilmemiş değişiklikler", metin, {"Kaydet", "Kaydetme", "Vazgeç"}, 0) : 2;
    if (s == 0) return Kaydet();
    return s == 1;
}

bool DosyaIslemleri::Yeni() {
    if (!h_.cekirdek) return false;
    if (!KaydedilmemisSor("Yeni projeye geçmeden önce")) return false;
    const int no = adsizSayaci_ + 1;
    const YuklemeSonucu y = h_.cekirdek->YeniBos("Adsız " + std::to_string(no));
    if (!y.basarili) return HataBildir("Yeni proje açılamadı", y.hata);
    adsizSayaci_ = no;
    YeniBelge(y, no);
    Bilgi("Yeni proje: Adsız " + std::to_string(no), false);
    return true;
}

bool DosyaIslemleri::SablondanYeni(const std::string& ad) {
    if (!h_.cekirdek) return false;
    if (!SablonAdiGecerli(ad)) return HataBildir("Şablon açılamadı", "geçersiz şablon adı: " + ad);
    const std::string yol = Birlestir(Birlestir(h_.bilgi.veriDizini, "sablonlar"), ad + ".json");
    std::string metin, hata;
    if (!DosyaOku(yol, metin, hata))
        return HataBildir("Şablon bulunamadı", ad + " (" + yol + "; şablonlar derlemede araclar/sablon_dok.py ile üretilir)");
    if (!KaydedilmemisSor("Şablondan yeni projeye geçmeden önce")) return false;
    const YuklemeSonucu y = h_.cekirdek->Yukle(metin, "sablon:" + ad);
    if (!y.basarili) return HataBildir("Şablon yüklenemedi", y.hata);
    const int no = ++adsizSayaci_;
    YeniBelge(y, no);
    Bilgi("Şablondan yeni: " + (y.ozet.baslik.empty() ? ad : y.ozet.baslik), true);
    return true;
}

bool DosyaIslemleri::Ac(const std::string& yolHam) {
    if (!h_.cekirdek) return false;
    const std::string yol = Kirp(yolHam);
    OkumaSonucu o = ProjeOku(yol);
    if (!o.basarili) {
        if (!DosyaVar(yol) && h_.ayarlar) {  // son dosyalar listesinden düşür
            auto& l = h_.ayarlar->dosya.sonDosyalar;
            l.erase(std::remove(l.begin(), l.end(), yol), l.end());
        }
        return HataBildir("'" + DosyaAdi(yol) + "' açılamadı", o.hata);
    }
    if (!KaydedilmemisSor("Başka bir proje açmadan önce")) return false;
    return OkunaniYukle(o, yol, false, "");
}

bool DosyaIslemleri::AcSor() {
    if (!h_.iletisim) return false;
    const auto y = h_.iletisim->DosyaAc("Proje aç",
                                         {{"Desteklenen dosyalar", "*.op4;*.matris;*.json"},
                                          {"op4 projesi", "*.op4"},
                                          {"Web sürümü projesi", "*.matris"},
                                          {"Bina JSON", "*.json"}},
                                         h_.ayarlar ? h_.ayarlar->dosya.sonKlasor : std::string());
    return y ? Ac(*y) : false;
}

bool DosyaIslemleri::IceAktarSor() {
    if (!h_.iletisim) return false;
    const auto y = h_.iletisim->DosyaAc("İçe aktar",
                                         {{"Web sürümü projesi ve bina JSON", "*.matris;*.json"},
                                          {"Web sürümü projesi", "*.matris"},
                                          {"Bina JSON", "*.json"}},
                                         h_.ayarlar ? h_.ayarlar->dosya.sonKlasor : std::string());
    return y ? Ac(*y) : false;
}

bool DosyaIslemleri::Kaydet() {
    if (!h_.belge) return false;
    if (h_.belge->Yol().empty() || h_.belge->SaltOkunur()) return FarkliKaydet();
    return YolaKaydet(h_.belge->Yol());
}

bool DosyaIslemleri::FarkliKaydet(std::string yol) {
    if (yol.empty()) {
        if (!h_.iletisim) return false;
        const auto s = h_.iletisim->DosyaKaydet("Farklı kaydet", {{"op4 projesi", "*.op4"}}, OneriYolu(".op4"));
        if (!s) return false;
        yol = *s;
    }
    if (KucukUzanti(yol) != ".op4") yol += ".op4";
    return YolaKaydet(yol);
}

bool DosyaIslemleri::YolaKaydet(const std::string& yol) {
    if (!h_.cekirdek || !h_.belge) return false;
    ProjeIcerigi icerik = korunanlar_;
    h_.belge->IcerikTopla(icerik);
    std::string zip, hata;
    const ProjeManifest m = ManifestKur();
    if (!ProjeZipKur(icerik, m, zip, hata)) return HataBildir("Kaydedilemedi", hata);
    OkumaSonucu d = ProjeZipCoz(zip);  // bozuk arşiv hiçbir zaman eski dosyanın yerine konmaz
    if (!d.basarili) return HataBildir("Kaydedilemedi", "iç hata: arşiv doğrulanamadı (" + d.hata + "); dosyaya dokunulmadı");
    const std::string kilitli = okumaKilidi_.Yol();
    okumaKilidi_.Birak();  // açık tanıtıcı varken ReplaceFileW başarısız olur (D23)
    const bool tamam = AtomikYaz(yol, zip, h_.ayarlar && h_.ayarlar->dosya.yedekBak, hata);
    if (!tamam) {
        if (!kilitli.empty()) okumaKilidi_.Ac(kilitli);
        return HataBildir("'" + DosyaAdi(yol) + "' kaydedilemedi", hata);
    }
    okumaKilidi_.Ac(yol);
    korunanlar_ = Korunacaklar(std::move(d.icerik));  // yazılan arşivin kendisi (yeni manifest dahil)
    eskiKaynak_.clear();
    h_.belge->Kaydedildi(yol);
    sonOtomatikSayac_ = h_.belge->DegisiklikSayaci();
    kirliBaslangicMs_ = -1;
    KurtarmaKaydiniSil();
    SonDosya(yol);
    Bilgi("Kaydedildi: " + DosyaAdi(yol) + " (" + std::to_string((zip.size() + 1023) / 1024) + " KB)", true);
    return true;
}

bool DosyaIslemleri::BinaDisaAktar(std::string yol) {
    if (!h_.cekirdek) return false;
    if (yol.empty()) {
        if (!h_.iletisim) return false;
        const auto s = h_.iletisim->DosyaKaydet("Bina modelini dışa aktar",
                                                {{"Web sürümü projesi", "*.matris"}, {"Bina JSON", "*.json"}},
                                                OneriYolu(".matris"));
        if (!s) return false;
        yol = *s;
    }
    const std::string u = KucukUzanti(yol);
    if (u != ".matris" && u != ".json") yol += ".matris";
    const std::string metin = h_.cekirdek->Metin();
    const std::string veri = KucukUzanti(yol) == ".json"
                                 ? metin + "\n"
                                 : "{\"tur\":\"matris-proje\",\"surum\":1,\"uygulama\":\"op4 · Opus Fortis\",\"kaydedildi\":\"" +
                                       Simdi() + "\",\"bina\":" + metin + "}\n";
    std::string hata;
    if (!AtomikYaz(yol, veri, false, hata)) return HataBildir("Dışa aktarılamadı", hata);
    Bilgi("Bina modeli dışa aktarıldı: " + DosyaAdi(yol), true);
    return true;
}

bool DosyaIslemleri::IfcDisaAktar(std::string yol) {
    if (!h_.cekirdek) return false;
    if (h_.cekirdek->Ozet().bos) return HataBildir("IFC dışa aktarılamadı", "model boş; dışa aktarılacak eleman yok");
    const bool dc = h_.sonuc && h_.sonuc->Var() && !h_.sonuc->Eski() && h_.sonuc->Veri();
    std::string zaman = ayar_.ifcZamani;
    if (zaman.empty()) {
        zaman = Simdi();
        if (!zaman.empty() && zaman.back() == 'Z') zaman.pop_back();
    }
    const json secenek = {{"analiz", true},
                          {"yukler", true},
                          {"dc", dc},
                          {"uygulama", {{"ad", "op4"}, {"surum", h_.bilgi.surum}, {"firma", "Opus Fortis"},
                                        {"tam_ad", "op4 · Opus Fortis"}}},
                          {"zaman", zaman}};
    const IfcSonucu r = h_.cekirdek->IfcDisari(secenek.dump(), dc ? *h_.sonuc->Veri() : std::string());
    if (!r.basarili) return HataBildir("IFC dışa aktarılamadı", r.hata);
    if (yol.empty()) {
        if (!h_.iletisim) return false;
        const std::string ad = GuvenliAd(r.dosyaAdi);
        const std::string oneri = ad.empty() ? OneriYolu(".ifc") : Birlestir(Klasor(OneriYolu(".ifc")), ad);
        const auto s = h_.iletisim->DosyaKaydet("IFC olarak dışa aktar", {{"IFC4 (STEP)", "*.ifc"}}, oneri);
        if (!s) return false;
        yol = *s;
    }
    if (KucukUzanti(yol) != ".ifc") yol += ".ifc";
    std::string hata;
    if (!AtomikYaz(yol, r.metin, false, hata)) return HataBildir("IFC yazılamadı", hata);
    if (h_.bildirim)
        for (const std::string& u : r.uyarilar) h_.bildirim->KomutYaz("Uyarı (IFC): " + u);
    Bilgi("IFC dışa aktarıldı: " + DosyaAdi(yol) + " (" + std::to_string((r.metin.size() + 1023) / 1024) + " KB" +
              (dc ? ", D/C dahil" : "") + ")",
          true);
    return true;
}

bool DosyaIslemleri::KapatmaOnayi() {
    if (kapanisOnaylandi_) return true;
    if (h_.belge && h_.belge->Kirli()) {
        const int s = h_.iletisim ? h_.iletisim->Soru("op4 kapatılıyor",
                                                      "\"" + h_.belge->Ad() +
                                                          "\" içinde kaydedilmemiş değişiklikler var.\nKapatmadan önce "
                                                          "kaydedilsin mi?",
                                                      {"Kaydet", "Kaydetme", "Vazgeç"}, 0)
                                  : 2;
        if (s == 0) {
            if (!Kaydet()) return false;
        } else if (s != 1) {
            return false;
        }
    }
    kapanisOnaylandi_ = true;
    return true;
}

bool DosyaIslemleri::Cikis() {
    if (!KapatmaOnayi()) return false;
    if (h_.arayuz && h_.arayuz->pencereyiKapat) h_.arayuz->pencereyiKapat();
    return true;
}

// ---- otomatik kayıt ve kurtarma --------------------------------------------------------------------------------------
void DosyaIslemleri::KareIsi(double simdiMs) {
    simdiMs_ = simdiMs;
    if (!ilkKare_) {
        ilkKare_ = true;
        if (!ayar_.acilisDosyasi.empty()) Ac(ayar_.acilisDosyasi);
        KurtarmalariYenile();
        if (!kurtarmalar_.empty()) {
            kurtarmaSorusu_ = true;
            Bilgi("op4 son oturumda beklenmedik biçimde kapanmış: " + std::to_string(kurtarmalar_.size()) +
                      " kurtarma kaydı var (Kurtar / Sil / Sonra; komut: KURTAR).",
                  false);
            if (platform_.kurtarmaGoster) platform_.kurtarmaGoster();
            kurtarmaDegisti.Yay();
        }
    }
    if (h_.belge && h_.ayarlar && !kurtarmaZip_.empty() && h_.ayarlar->dosya.otomatikKayit && h_.belge->Kirli() &&
        h_.belge->DegisiklikSayaci() != sonOtomatikSayac_) {
        if (kirliBaslangicMs_ < 0) kirliBaslangicMs_ = simdiMs;
        const double aralik =
            ayar_.otomatikKayitMs > 0 ? ayar_.otomatikKayitMs : h_.ayarlar->dosya.otomatikKayitDk * 60000.0;
        if (simdiMs - kirliBaslangicMs_ >= aralik && !OtomatikKaydet()) kirliBaslangicMs_ = simdiMs;  // sonra yeniden dene
    }
    if (simdiMs - sonAyarDenetimiMs_ >= 1000) {
        sonAyarDenetimiMs_ = simdiMs;
        AyarlariKaydet();
    }
}

bool DosyaIslemleri::OtomatikKaydet() {
    if (kurtarmaZip_.empty() || !h_.cekirdek || !h_.belge) return false;
    ProjeIcerigi icerik = korunanlar_;
    h_.belge->IcerikTopla(icerik);
    ProjeManifest m = ManifestKur();
    std::string zip, hata;
    bool tamam = ProjeZipKur(icerik, m, zip, hata) && AtomikYaz(kurtarmaZip_, zip, false, hata);
    if (tamam) {
        const json meta = {{"bicim", 1},
                           {"asil_yol", h_.belge->Yol()},
                           {"baslik", h_.belge->Yol().empty() ? h_.cekirdek->Ozet().baslik : DosyaAdi(h_.belge->Yol())},
                           {"zaman", m.kaydedildi},
                           {"model_ozeti", m.modelOzeti},
                           {"surum", h_.bilgi.surum},
                           {"surec", SurecNo()}};
        tamam = AtomikYaz(kurtarmaKok_ + ".json", meta.dump(1) + "\n", false, hata);
    }
    if (!tamam) {
        if (!otomatikHataBildirildi_ && h_.bildirim) {
            h_.bildirim->KomutYaz("Uyarı: otomatik kayıt yazılamadı: " + hata);
            h_.bildirim->Tost("Otomatik kayıt yazılamadı: " + hata, TostTuru::Uyari);
        }
        otomatikHataBildirildi_ = true;
        return false;
    }
    otomatikHataBildirildi_ = false;
    sonOtomatikSayac_ = h_.belge->DegisiklikSayaci();
    kirliBaslangicMs_ = -1;
    ++otomatikKayitSayisi_;
    return true;
}

void DosyaIslemleri::KurtarmaKaydiniSil() {
    if (kurtarmaKok_.empty()) return;
    DosyaSil(kurtarmaZip_);
    DosyaSil(kurtarmaKok_ + ".json");
}

void DosyaIslemleri::KurtarmalariYenile() {
    kurtarmalar_.clear();
    if (ayar_.kurtarmaDizini.empty()) return;
    for (KurtarmaKaydi& k : KurtarmaKayitlari(ayar_.kurtarmaDizini))
        if (k.dosya != kurtarmaZip_) kurtarmalar_.push_back(std::move(k));
}

bool DosyaIslemleri::Kurtar(size_t i) {
    if (i >= kurtarmalar_.size() || !h_.cekirdek) return false;
    const KurtarmaKaydi k = kurtarmalar_[i];
    OkumaSonucu o = ProjeOku(k.dosya);
    if (!o.basarili) return HataBildir("Kurtarma kaydı açılamadı", o.hata + " (kayıt silinebilir: KURTAR sil " +
                                                                       std::to_string(i + 1) + ")");
    if (!KaydedilmemisSor("Kurtarılan projeye geçmeden önce")) return false;
    if (!OkunaniYukle(o, k.dosya, true, k.asilYol)) return false;
    // Önce bu oturumun kaydı yazılır, sonra eski kayıt silinir: arada çökse de veri kaybolmaz.
    if (OtomatikKaydet()) {
        DosyaSil(k.dosya);
        DosyaSil(UzantiDegistir(k.dosya, ".json"));
    }
    kurtarmalar_.erase(kurtarmalar_.begin() + static_cast<std::ptrdiff_t>(i));
    if (kurtarmalar_.empty()) kurtarmaSorusu_ = false;
    kurtarmaDegisti.Yay();
    return true;
}

bool DosyaIslemleri::KurtarmaSil(size_t i) {
    if (i >= kurtarmalar_.size()) return false;
    const KurtarmaKaydi k = kurtarmalar_[i];
    DosyaSil(k.dosya);
    DosyaSil(UzantiDegistir(k.dosya, ".json"));
    DosyaSil(UzantiDegistir(k.dosya, ".kilit"));
    kurtarmalar_.erase(kurtarmalar_.begin() + static_cast<std::ptrdiff_t>(i));
    if (kurtarmalar_.empty()) kurtarmaSorusu_ = false;
    Bilgi("Kurtarma kaydı silindi: " + k.baslik, false);
    kurtarmaDegisti.Yay();
    return true;
}

void DosyaIslemleri::KurtarmaSonra() {
    if (!kurtarmaSorusu_) return;
    kurtarmaSorusu_ = false;
    Bilgi("Kurtarma kayıtları saklandı; istediğinizde Dosya › Kurtar (KURTAR).", false);
    kurtarmaDegisti.Yay();
}

}  // namespace op4
