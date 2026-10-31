// op4 arayüzü — ana pencere (kullanıcı kararı 31.10.2026: "Atölye" yerleşimi, modernleştirilmiş; MIMARI §5 ve §25'in
// yerleşim bölümü yerine; kaynak op4/tasarim/taslaklar/atolye/tasarim.md §1, §6, §7, §9, uret.py). Sahibi: C.
//
// Bölgeler (1920 × 1080, 1×): başlık 30 (kemer simgesi, op4, hızlı erişim, ortada proje adı, pencere düğmeleri) · şerit
// sekme satırı 26 + gövde 78 (komutlar.json'dan) · sol ray 36 (ÇİZ paleti + SEÇ anahtarları) · model ağacı 268 · görünüm
// sekmeleri 22 + 3B görünüm (sahne dokusu, araç pili, dört düğme, eksen üçlüsü, mini araç çubuğu) · Özellikler 320 +
// pencere şeridi 28 (Başlangıç / Özellikler / Kataloglar / Model ağacı / Filtre & görünürlük / Sorgu) · rıhtım 22 + 40
// (Komut / Mesajlar / Tablolar) · komut satırı 30 · durum çubuğu 26 (yönerge, ORTO / YAKALA / SÜRÜKLE, X Y Z, kat kapsamı,
// etkin kat, birim, koordinat, seçili sayısı). Bütün renk ve ölçüler tema.h'tedir; bütün metinler dil.h Tr() ile geçer.
// Platformdan bağımsızdır (Win32 / DX12 yok): pencere işlemleri ve sahne dokusu dışarıdan verilir.
#pragma once

#include <cstdint>
#include <deque>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include "arayuz/bilesenler.h"
#include "arayuz/tema.h"
#include "arayuz/yazi.h"
#include "cekirdek/arayuz_kancalari.h"
#include "cekirdek/gezgin.h"
#include "cekirdek/gezinme.h"
#include "cekirdek/hizmetler.h"
#include "cekirdek/kamera.h"
#include "cekirdek/komut_satiri.h"
#include "cekirdek/secme.h"
#include "imgui.h"

namespace op4 {

// Ana pencerenin platform bağlantıları (uygulama doldurur).
struct PencereIslevleri {
    std::function<void()> kucult, buyutGeriAl, kapat;
    std::function<bool()> buyuk;                  // pencere büyütülmüş mü
};

// Sahne dokusu (DX12 SRV tanımlayıcısı; Linux önizlemesinde CPU dokusu) ve kullanılan uv bölümü.
struct SahneDokusu {
    ImTextureID kimlik = ImTextureID_Invalid;
    float uvG = 1, uvY = 1;
};

// Görüş alanı (ekran pikseli): çiziciye verilen dikdörtgen.
struct GorusDikdortgeni {
    float x = 0, y = 0, g = 1, y2 = 1;
};

enum class YanPencere : uint8_t { Baslangic = 0, Ozellikler = 1, Kataloglar = 2, ModelAgaci = 3, Filtre = 4, Sorgu = 5 };
enum class KatKapsami : uint8_t { BuKat = 0, BenzerKatlar = 1, TumKatlar = 2 };
enum class RihtimSekmesi : uint8_t { Komut = 0, Mesajlar = 1, Tablolar = 2 };

struct Tost {
    std::string metin;
    TostTuru tur = TostTuru::Bilgi;
    double bitis = 0;
};
struct Ilerleme {
    std::string id, metin;
    float oran = -1;
    std::function<void()> iptal;
};
struct Ileti {   // Mesajlar sekmesi
    std::string metin;
    TostTuru tur = TostTuru::Bilgi;
};

class AnaPencere;
// Komut satırı çıktısı, tost, ilerleme (S21 Bildirimler; C uygular).
class ArayuzBildirimleri final : public Bildirimler {
public:
    explicit ArayuzBildirimleri(AnaPencere& a) : a_(a) {}
    void KomutYaz(std::string_view satir) override;
    void Tost(std::string_view metin, TostTuru tur) override;
    void Ilerleme(std::string_view id, std::string_view metin, float oran, std::function<void()> iptal) override;
    void IlerlemeBitti(std::string_view id) override;
    std::function<void(std::string_view)> gunluk;

private:
    AnaPencere& a_;
};

class AnaPencere {
public:
    explicit AnaPencere(Hizmetler& h);
    ~AnaPencere();
    AnaPencere(const AnaPencere&) = delete;
    AnaPencere& operator=(const AnaPencere&) = delete;

    // ---- kurulum ----------------------------------------------------------------------------------------------------
    PencereIslevleri pencere;
    std::string bagdastirici;                     // durum öğesi ve Ayarlar › Görüntü
    bool warp = false;
    unsigned msaa = 1;
    std::vector<std::string> bagdastiricilar;     // Ayarlar › Görüntü seçenekleri
    bool testKipi = false;
    ImTextureID logoDokusu = ImTextureID_Invalid; // başlıktaki kemer simgesi (opus-fortis-simge-koyu.png)
    float logoEnBoy = 1200.0f / 1397.0f;
    void YazilariAyarla(const Yazilar& y) { yazilar_ = y; }
    void KomutlariBagla();                        // C'nin komutları (komutlar.json sahip "C")
    ArayuzBildirimleri& Bildirim() { return *bildirim_; }
    // Ayarlardaki arayüz / görüntü / dil değerlerini uygular (dil, sayı biçimi, çizgi kalınlıkları, renkler).
    void AyarlariUygula();

    // ---- kare -------------------------------------------------------------------------------------------------------
    void KareCiz(float olcek, const SahneDokusu& doku, double simdiMs);
    GorusDikdortgeni Gorus() const { return gorus_; }
    GorusIzdusumu Izdusum() const { return kamera_.Izdusum(gorus_.g, gorus_.y2, olcek_); }
    const GorunumKamerasi& Kamera() const { return kamera_; }
    GorunumKamerasi& Kamera() { return kamera_; }
    bool KesitGorunumu() const;
    bool IzgaraGorunur() const;
    bool CizimGerekli() const { return cizimGerekli_; }
    void CizimYapildi() { cizimGerekli_ = false; }
    // Başlık çubuğu isabet testi (Win32 WM_NCHITTEST): 0 istemci, 1 başlık (sürükle), 2 küçült, 3 büyüt, 4 kapat.
    int IsabetTesti(float pikselX, float pikselY) const;

    // ---- model ------------------------------------------------------------------------------------------------------
    void SahneYenile();
    void Sigdir();
    void StandartGorunum(StandartYon y);
    const SahnePtr& Sahne() const { return sahne_; }
    const OznitelikPtr& Oznitelikler() const { return oz_; }
    ElemanKimligi Uzerinde() const { return uzerinde_; }
    uint64_t VurguSurumu() const { return vurguSurumu_; }
    bool YalnizSecili() const { return yalnizSecili; }
    void SahneZorla(SahnePtr s, OznitelikPtr o);  // sınama / önizleme: çekirdek yerine verilen sahne

    // ---- durum (senaryo, sınama) -----------------------------------------------------------------------------------
    YanPencere yanPencere = YanPencere::Baslangic;
    std::string etkinSekme = "Model";
    RihtimSekmesi rihtim = RihtimSekmesi::Komut;
    bool ayarlarAcik = false;
    int ayarSayfasi = 0;                          // 0 Program, 1 Görüntü, 2 Dil
    KatKapsami kapsam = KatKapsami::BenzerKatlar;
    int etkinKat = -1;                            // sahne->seviyeler dizini (−1: yok)
    bool yalnizSecili = false;
    bool dogrudanDegistirme = true;               // D anahtarı (tutamaçlar)
    std::string yonerge;                          // durum çubuğu adım yönergesi (boşsa varsayılan)
    void KomutSatirinaOdaklan() { komutOdak_ = true; }
    Gezinme& GezinmeDurumu() { return gezinme_; }
    bool AgacAcik(const std::string& anahtar) const { return acik_.count(anahtar) != 0; }
    void AgacAc(const std::string& anahtar, bool ac);

    std::deque<std::string> cikti;                // komut satırı çıktısı (son 200)
    std::vector<op4::Ileti> iletiler;             // Mesajlar
    std::vector<op4::Tost> tostlar;
    std::vector<op4::Ilerleme> ilerlemeler;
    std::string sonKomutIletisi;
    double simdi = 0;

private:
    friend class ArayuzBildirimleri;
    struct Yerlesim {
        float W = 0, H = 0;
        bool dar = false, tekPanel = false;
        float baslik = 32, sekme = 32, serit = 88, ust = 152;
        float ray = 40, agacW = 272, ozelW = 320, serW = 32;
        float gsekme = 32, rsekme = 32, rihtim = 48, komut = 32, durum = 28;
        float alt = 0;                            // görünümün alt kenarı (rıhtım sekmelerinin üstü)
        float agacX = 0, vpX0 = 0, vpX1 = 0, vpY0 = 0, vpY1 = 0, ozelX = 0, serX = 0;
    };
    void YerlesimKur(float W, float H);

    // çizim parçaları
    void BaslikCiz(Ciz& c);                       // ana_pencere.cpp
    void SeritCiz(Ciz& c);                        // serit.cpp: sekme satırı + gövde
    void DosyaMenusu(Ciz& c);                     // serit.cpp
    void KisayollariIsle();                       // serit.cpp
    bool KomutDugmesi(Ciz& c, const KomutTanimi& t, float x, float y, float w, float h, bool buyuk);
    void RayCiz(Ciz& c);                          // paneller.cpp
    void AgacPaneliCiz(Ciz& c, float x0, float y0, float w, float h);
    void OzelliklerPaneliCiz(Ciz& c, float x0, float y0, float w, float h);
    void BaslangicPaneliCiz(Ciz& c, float x0, float y0, float w, float h);
    void BosPanelCiz(Ciz& c, float x0, float y0, float w, float h, const char* baslik, const char* aciklama);
    void PencereSeridiCiz(Ciz& c);
    void GorunumSekmeleriCiz(Ciz& c);             // gorunum_alani.cpp
    void GorunumCiz(Ciz& c, const SahneDokusu& d);
    void SahneCiz(Ciz& c);                        // çubuk görünümü, akslar, mesnetler, vurgu (ImDrawList)
    void SecimNotlariCiz(Ciz& c);                 // tutamaçlar, ölçü, mini araç çubuğu, üzerinde ipucu
    void GorunumGirdisi(Ciz& c);
    void RihtimCiz(Ciz& c);                       // alt_bolge.cpp
    void KomutSatiriCiz(Ciz& c);
    void DurumCubuguCiz(Ciz& c);
    void TostlarCiz(Ciz& c);
    void AyarlarPenceresi(Ciz& c);                // pencereler.cpp
    void HizliAksPenceresi(Ciz& c);
    void BilgiPencereleri(Ciz& c);                // kısayollar, hakkında
    void SihirbazPenceresi(Ciz& c);               // Yönetmelik sihirbazı kancası (S21 iletişim kaydı)

    // yardımcılar
    bool KomutCalistir(const std::string& id, KomutKaynagi kaynak, std::string_view arg = {});
    // Yeni proje akışı: kayıtlı "yonetmelik_sihirbazi" iletişimi varsa önce onu açar, sonra eylem.
    void YeniProjeAkisi(std::function<void()> eylem);
    void Secimle(ElemanKimligi k, SecimKipi kip);
    bool Secilebilir(ElemanKimligi k) const;      // sol raydaki SEÇ anahtarlarına göre
    std::string AltTur(ElemanKimligi k) const;
    std::string ElemanAdi(ElemanKimligi k) const;
    std::string SecimOzeti() const;               // "6 kiriş"
    std::string SecimAyrinti() const;             // "IPE400 · S355 · Kat 2 (+9,00)"
    std::string KatAdi(int seviye, bool kotlu = true) const;
    void Engel(float x, float y, float w, float h);  // görünüm üstündeki yüzen öğe
    bool SahneBos() const;
    void AnaKatSec();
    void AgaciSecimeAc();                         // etkin kat ve seçimi içeren düğümleri aç

    Hizmetler& h_;
    std::unique_ptr<ArayuzBildirimleri> bildirim_;
    Yazilar yazilar_;
    float olcek_ = 1.0f;
    std::string yogunlukAyari_ = "otomatik";
    bool agacSolda_ = true;
    bool stilYenile_ = true;
    bool escPopupAcikti_ = false;  // kare başında açık açılır pencere vardı (Esc önce onu kapatır)
    std::shared_ptr<Ayarlar> ayarOnceki_;  // Ayarlar penceresi açılınca alınan anlık görüntü (İptal / değişiklik sayısı)
    char ayarArama_[64] = {};  // vurgu paleti değişti: ImGui stili yeniden kurulacak  // model ağacı solda yapışık (kapatılınca pencere şeridine döner)  // Ayarlar › Görüntü › Yoğunluk
    Yerlesim L_;
    GorusDikdortgeni gorus_;
    bool cizimGerekli_ = true;

    // model
    SahnePtr sahne_;
    OznitelikPtr oz_;
    uint64_t sahneSurumu_ = ~0ull;
    bool zorla_ = false;
    SecmeDizini secme_;
    GezginDugumu agac_;
    std::set<std::string> acik_{"proje", "katlar"};
    ElemanKimligi uzerinde_;
    uint64_t vurguSurumu_ = 0;
    uint64_t sonSecimSurumu_ = 0;
    char agacArama_[96] = {};

    // görünüm
    GorunumKamerasi kamera_;
    StandartYon yon_ = StandartYon::Izometrik;
    Gezinme gezinme_;
    std::vector<ImVec4> engeller_;  // (x0, y0, x1, y1) piksel
    bool sigdirBekliyor_ = true;
    V3d imlecDunya_{};
    bool imlecDunyaVar_ = false;
    std::map<std::string, bool> secAnahtar_;      // SEÇ anahtarları: dugum, kolon, kiris, doseme, duvar, aks, yuk, mesnet, temel
    bool akslarGorunur_ = true, etiketlerGorunur_ = false, dugumlerGorunur_ = true;

    // komut satırı
    KomutSatiri komutSatiri_;
    char komutGirdi_[256] = {};
    bool komutOdak_ = false;
    bool komutAktif_ = false;
    int oneriSecili_ = 0;
    OneriKumesi oneriKumesi_ = OneriKumesi::Tumu;
    std::string vurguluKomut_;
    double vurguBitis_ = 0;

    // pencereler
    bool hizliAksAcik_ = false;
    char hizliAksX_[64] = "6 6 6";
    char hizliAksY_[64] = "6 6 6 6";
    char hizliAksZ_[64] = "4,5 4,5 4,5";
    bool kisayollarAcik_ = false;
    bool hakkindaAcik_ = false;
    std::string sihirbazId_;                      // açık iletişim (S21) id'si
    std::function<void()> sihirbazSonrasi_;
    std::set<std::string> kapaliBolumler_{"Analiz", "Tasarım"};
};

// Mevcut ana pencere (C modülü kurar; uygulama.cpp, senaryo yürütücüsü ve ekran sınaması erişir). Yoksa null.
AnaPencere* EtkinAnaPencere();
void EtkinAnaPencereAyarla(AnaPencere* a);

}  // namespace op4
