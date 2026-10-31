// op4 arayüzü — ana pencere: yerleşim, kare düzeni, başlık çubuğu, ortak yardımcılar, bildirimler, C komutları.
#include "arayuz/ana_pencere.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <functional>
#include <sstream>

#include <nlohmann/json.hpp>

#include "arayuz/dil.h"
#include "arayuz/stil.h"
#include "cekirdek/ayarlar.h"
#include "cekirdek/gorunum.h"
#include "cekirdek/komut.h"
#include "cekirdek/proje_belgesi.h"
#include "cekirdek/secim.h"
#include "cekirdek/turkce.h"

namespace op4 {
namespace {
AnaPencere* g_etkin = nullptr;

uint32_t HexRenk(const std::string& s, uint32_t yedek) {
    if (s.size() != 7 || s[0] != '#') return yedek;
    char* son = nullptr;
    const unsigned long v = std::strtoul(s.c_str() + 1, &son, 16);
    return son && *son == 0 ? tema::Renk(static_cast<uint32_t>(v)) : yedek;
}
}  // namespace

AnaPencere* EtkinAnaPencere() { return g_etkin; }
void EtkinAnaPencereAyarla(AnaPencere* a) { g_etkin = a; }

// ---- bildirimler (S21; C uygular) --------------------------------------------------------------------------------------
void ArayuzBildirimleri::KomutYaz(std::string_view satir) {
    a_.cikti.emplace_back(satir);
    while (a_.cikti.size() > 200) a_.cikti.pop_front();
    a_.sonKomutIletisi = std::string(satir);
    const bool hata = satir.rfind("HATA", 0) == 0 || satir.find("Bilinmeyen komut") != std::string_view::npos ||
                      satir.find("henüz") != std::string_view::npos;
    if (hata) a_.iletiler.push_back({std::string(satir), TostTuru::Uyari});
    if (gunluk) gunluk(satir);
    a_.cizimGerekli_ = true;
}
void ArayuzBildirimleri::Tost(std::string_view metin, TostTuru tur) {
    a_.tostlar.push_back({std::string(metin), tur, a_.simdi + (tur == TostTuru::Hata ? 8000.0 : 4500.0)});
    if (tur == TostTuru::Hata || tur == TostTuru::Uyari) a_.iletiler.push_back({std::string(metin), tur});
    if (gunluk) gunluk(std::string("[tost] ") + std::string(metin));
    a_.cizimGerekli_ = true;
}
void ArayuzBildirimleri::Ilerleme(std::string_view id, std::string_view metin, float oran, std::function<void()> iptal) {
    for (auto& i : a_.ilerlemeler)
        if (i.id == id) {
            i.metin = std::string(metin);
            i.oran = oran;
            i.iptal = std::move(iptal);
            a_.cizimGerekli_ = true;
            return;
        }
    a_.ilerlemeler.push_back({std::string(id), std::string(metin), oran, std::move(iptal)});
    a_.cizimGerekli_ = true;
}
void ArayuzBildirimleri::IlerlemeBitti(std::string_view id) {
    std::erase_if(a_.ilerlemeler, [&](const op4::Ilerleme& i) { return i.id == id; });
    a_.cizimGerekli_ = true;
}

// ---- kurulum -----------------------------------------------------------------------------------------------------------
AnaPencere::AnaPencere(Hizmetler& h) : h_(h), bildirim_(std::make_unique<ArayuzBildirimleri>(*this)) {
    StandartYonUygula(kamera_, StandartYon::Izometrik);
    kamera_.d.hedef = {6, 6, 0};
    kamera_.d.uzaklik = 40;
    sahne_ = BosSahne();
    oz_ = BosOznitelikTablosu();
    secme_.Kur(sahne_);
    for (const char* a : {"dugum", "kolon", "kiris", "doseme", "duvar", "mesnet", "temel", "capraz", "diger"}) secAnahtar_[a] = true;
    secAnahtar_["aks"] = false;
    secAnahtar_["yuk"] = false;
    gezinme_.baglanti.cekirdekNokta = [this](double px, double py) {
        SecmeAyari a;
        if (const auto v = secme_.IsinVurusu(PikselIsini(Izdusum(), px, py), a)) return v->nokta;
        double z = 0;
        if (etkinKat >= 0 && etkinKat < static_cast<int>(sahne_->seviyeler.size()) && yon_ == StandartYon::Plan)
            z = sahne_->seviyeler[static_cast<size_t>(etkinKat)].z;
        return CalismaDuzlemiNoktasi(kamera_, px, py, gorus_.g, gorus_.y2, z);
    };
    gezinme_.baglanti.tikla = [this](double px, double py, SecimKipi kip) {
        SecmeAyari a;
        std::optional<ElemanKimligi> bulunan;
        for (const SecmeVurusu& v : secme_.Adaylar(Izdusum(), px, py, a))
            if (Secilebilir(v.kimlik)) {
                bulunan = v.kimlik;
                break;
            }
        if (bulunan)
            Secimle(*bulunan, kip);
        else if (kip == SecimKipi::Yeni && h_.secim)
            h_.secim->Temizle();
        cizimGerekli_ = true;
    };
    gezinme_.baglanti.pencere = [this](double x0, double y0, double x1, double y1, PencereKipi pk, SecimKipi kip) {
        SecmeAyari a;
        a.mesnetler = false;
        std::vector<ElemanKimligi> k;
        for (const ElemanKimligi& e : secme_.Pencere(Izdusum(), x0, y0, x1, y1, pk, a))
            if (Secilebilir(e)) k.push_back(e);
        if (h_.secim) h_.secim->Uygula(k, kip);
        cizimGerekli_ = true;
    };
    gezinme_.baglanti.sigdir = [this] { Sigdir(); };
}

AnaPencere::~AnaPencere() {
    // gorunum/gorunum.json katkısı (arayuz_modulu.cpp) bu nesneyi gösterir; belge kabukta daha uzun yaşar (S15, D'nin
    // DosyaIslemleri / CozumAkisi yıkıcıları gibi). Arayüz modülü kapanırken katkı bırakılır.
    if (h_.belge) h_.belge->KatkiKaldir("gorunum");
    if (g_etkin == this) g_etkin = nullptr;
}

void AnaPencere::AyarlariUygula() {
    if (!h_.ayarlar) return;
    const Ayarlar& a = *h_.ayarlar;
    DilAyarla(DilKodundan(a.arayuz.dil));
    SayiBicimiAyarla(a.arayuz.ondalik == "nokta" ? '.' : ',', a.arayuz.binlikAyirici);
    // Vurgu paleti (Kobalt / Petrol / Grafit) → renkler belirteçlerden yeniden kurulur; ImGui stili yeniden uygulanır.
    tema::PaletUygula(tema::PaletKodundan(a.arayuz.vurgu));
    tema::Tema& t = tema::Etkin();
    const tema::Renkler v = t.r;
    stilYenile_ = true;  // ImGui stili bir sonraki karede (ölçek bilinirken) yeniden kurulur
    yogunlukAyari_ = a.arayuz.yogunluk;
    // Yazı boyutu: bir sonraki kareden başlayarak arayüz ölçeği DPI × çarpan (canlı önizleme; İptal eski değere döner).
    yaziCarpani_ = tema::YaziCarpani(a.arayuz.yaziBoyutu);
    t.s.cubukKalinlik = static_cast<float>(a.grafik.cubukKalinlik);
    t.s.seciliKalinlik = static_cast<float>(a.grafik.seciliKalinlik);
    t.s.etiketBoy = static_cast<float>(a.arayuz.etiketBoyu);
    if (!a.grafik.vurguyuIzle) {
        t.r.secim = t.r.tutamacBaslangic = t.r.tutamacBitis = HexRenk(a.grafik.secimRengi, v.secim);
        t.r.uzerinde = HexRenk(a.grafik.uzerindeRengi, v.uzerinde);
    }
    if (a.grafik.arkaPlan == "duz" || a.grafik.arkaPlan == "beyaz") t.r.sahneAlt = t.r.sahneUst;
    gezinme_.esleme = a.arayuz.fareEslemesi == "klasik" ? FareEslemesi::Klasik : FareEslemesi::Op4;
    cizimGerekli_ = true;
}

bool AnaPencere::KesitGorunumu() const { return h_.gorunum && h_.gorunum->kip != GorunumKipi::Cubuk; }
bool AnaPencere::IzgaraGorunur() const { return !h_.gorunum || h_.gorunum->izgara; }

bool AnaPencere::SahneBos() const {
    return !sahne_ || (sahne_->cubuklar.empty() && sahne_->paneller.empty() && sahne_->dugumler.empty());
}

void AnaPencere::AgacAc(const std::string& anahtar, bool ac) {
    if (ac)
        acik_.insert(anahtar);
    else
        acik_.erase(anahtar);
}

void AnaPencere::AnaKatSec() {
    // Etkin kat: kat işaretli seviyelerden en üsttekinin bir altı (çok katlı yapıda tipik "ana kat"), yoksa ilki.
    std::vector<int> katlar;
    for (size_t i = 0; i < sahne_->seviyeler.size(); ++i)
        if (sahne_->seviyeler[i].kat > 0) katlar.push_back(static_cast<int>(i));
    if (katlar.empty()) {
        etkinKat = sahne_->seviyeler.empty() ? -1 : 0;
        return;
    }
    etkinKat = katlar.size() >= 3 ? katlar[katlar.size() - 2] : katlar.back();
}

void AnaPencere::AgaciSecimeAc() {
    if (etkinKat >= 0 && etkinKat < static_cast<int>(sahne_->seviyeler.size()))
        acik_.insert("kat:" + std::to_string(sahne_->seviyeler[static_cast<size_t>(etkinKat)].kat));
    if (!h_.secim || h_.secim->Bos()) return;
    const std::vector<ElemanKimligi>& sec = h_.secim->Liste();
    std::function<bool(const GezginDugumu&)> ac = [&](const GezginDugumu& d) {
        bool icerir = false;
        for (const GezginDugumu& k : d.cocuklar) icerir |= ac(k);
        if (!icerir && d.cocuklar.empty())
            for (const ElemanKimligi& e : d.elemanlar)
                if (std::binary_search(sec.begin(), sec.end(), e)) {
                    icerir = true;
                    break;
                }
        if (icerir && d.anahtar.find("kullanim_yeri") == std::string::npos) acik_.insert(d.anahtar);
        return icerir;
    };
    // yalnız etkin kat altında aç (bütün katlar açılırsa ağaç taşar)
    for (const GezginDugumu& k : agac_.cocuklar)
        for (const GezginDugumu& kat : k.cocuklar)
            if (acik_.count(kat.anahtar))
                for (const GezginDugumu& t : kat.cocuklar) ac(t);
}

void AnaPencere::SahneZorla(SahnePtr s, OznitelikPtr o) {
    zorla_ = true;
    sahne_ = s ? std::move(s) : BosSahne();
    oz_ = o ? std::move(o) : BosOznitelikTablosu();
    sahneSurumu_ = sahne_->surum;
    secme_.Kur(sahne_);
    agac_ = GezginAgaciKur(*oz_, sahne_.get());
    AnaKatSec();
    AgaciSecimeAc();
    if (!SahneBos() && yanPencere == YanPencere::Baslangic) yanPencere = YanPencere::Ozellikler;
    sigdirBekliyor_ = true;
    cizimGerekli_ = true;
    ++vurguSurumu_;
}

void AnaPencere::SahneYenile() {
    if (zorla_ || !h_.cekirdek) return;
    SahnePtr s = h_.cekirdek->Sahne();
    OznitelikPtr o = h_.cekirdek->Oznitelikler();
    const bool bosIdi = SahneBos();
    sahne_ = s ? s : BosSahne();
    oz_ = o ? o : BosOznitelikTablosu();
    sahneSurumu_ = sahne_->surum;
    secme_.Kur(sahne_);
    agac_ = GezginAgaciKur(*oz_, sahne_.get());
    if (etkinKat >= static_cast<int>(sahne_->seviyeler.size()) || etkinKat < 0) AnaKatSec();
    AgaciSecimeAc();
    if (bosIdi && !SahneBos() && yanPencere == YanPencere::Baslangic) yanPencere = YanPencere::Ozellikler;
    cizimGerekli_ = true;
    ++vurguSurumu_;
}

void AnaPencere::Sigdir() {
    Kutu3d k = sahne_->sinir;
    if (k.Bos()) {  // boş model: Z = 0 çalışma ızgarasının 12 × 12 m'lik bölümü
        k.Kapsa(V3d{0, 0, 0});
        k.Kapsa(V3d{12, 12, 0});
    }
    kamera_.Sigdir(k, std::max(1.0f, gorus_.g), std::max(1.0f, gorus_.y2));
    sigdirBekliyor_ = false;
    cizimGerekli_ = true;
}

void AnaPencere::StandartGorunum(StandartYon y) {
    yon_ = y;
    StandartYonUygula(kamera_, y);
    gezinme_.donmeKilitli = y != StandartYon::Izometrik;
    Sigdir();
    if (y == StandartYon::Plan && etkinKat >= 0 && etkinKat < static_cast<int>(sahne_->seviyeler.size()))
        kamera_.d.hedef.z = sahne_->seviyeler[static_cast<size_t>(etkinKat)].z;
}

void AnaPencere::Secimle(ElemanKimligi k, SecimKipi kip) {
    if (h_.secim) h_.secim->Uygula(k, kip);
}

std::string AnaPencere::AltTur(ElemanKimligi k) const {
    if (const auto s = oz_->Satir(k))
        if (const auto a = oz_->Metin(*s, oznitelik::ALT_TUR); a && !a->empty()) return std::string(*a);
    switch (k.tur) {
        case ElemanTuru::Cubuk:
            if (const auto i = sahne_->CubukDizini(k.no)) {
                switch (sahne_->cubuklar[*i].tur) {
                    case CubukTuru::Kolon: return "kolon";
                    case CubukTuru::Kiris: return "kiris";
                    case CubukTuru::Capraz: return "capraz";
                    case CubukTuru::Asik: return "asik";
                    default: return "diger";
                }
            }
            return "diger";
        case ElemanTuru::Panel: return "doseme";
        case ElemanTuru::Dugum: return "dugum";
        case ElemanTuru::Mesnet: return "mesnet";
        case ElemanTuru::Temel: return "temel";
        case ElemanTuru::Aks: return "aks";
        case ElemanTuru::Yuk: return "yuk";
        default: return "diger";
    }
}

bool AnaPencere::Secilebilir(ElemanKimligi k) const {
    std::string t = AltTur(k);
    if (t == "asik" || t == "makas-ust" || t == "makas-alt" || t == "makas-dikme" || t == "makas-diyagonal" || t == "kren" ||
        t == "bag")
        t = "kiris";
    if (t == "cati" || t == "cephe") t = "doseme";
    const auto i = secAnahtar_.find(t);
    return i == secAnahtar_.end() ? true : i->second;
}

std::string AnaPencere::ElemanAdi(ElemanKimligi k) const {
    if (const auto s = oz_->Satir(k))
        if (const auto ad = oz_->Metin(*s, oznitelik::AD); ad && !ad->empty()) return std::string(*ad);
    return std::string(Tr(TurAdi(k.tur))) + " " + std::to_string(k.no);
}

std::string AnaPencere::KatAdi(int seviye, bool kotlu) const {
    if (seviye < 0 || seviye >= static_cast<int>(sahne_->seviyeler.size())) return "—";
    const SahneSeviyesi& s = sahne_->seviyeler[static_cast<size_t>(seviye)];
    const std::string ad = s.kat == 0 ? Tr("Zemin") : (s.kat > 0 ? Trf("Kat %d", s.kat) : s.ad);
    return kotlu ? ad + " (" + Kot(s.z) + ")" : ad;
}

std::string AnaPencere::SecimOzeti() const {
    if (!h_.secim || h_.secim->Bos()) return "";
    std::map<std::string, size_t> turler;
    for (const ElemanKimligi& k : h_.secim->Liste()) ++turler[AltTur(k)];
    const size_t n = h_.secim->Sayi();
    static const std::pair<const char*, const char*> adlar[] = {
        {"kolon", "kolon"}, {"kiris", "kiriş"}, {"capraz", "çapraz"}, {"asik", "aşık"}, {"doseme", "döşeme"},
        {"dugum", "düğüm"}, {"mesnet", "mesnet"}, {"temel", "temel"}};
    const char* ad = "eleman";
    if (turler.size() == 1)
        for (const auto& [k, v] : adlar)
            if (turler.begin()->first == k) ad = v;
    return std::to_string(n) + " " + Tr(ad);
}

std::string AnaPencere::SecimAyrinti() const {
    if (!h_.secim || h_.secim->Bos()) return "";
    const auto ortak = OrtakOzellikler(*oz_, h_.secim->Liste());
    std::string kesit, malzeme, kat;
    for (const auto& [id, deger] : ortak) {
        if (deger == "(çeşitli)") continue;
        if (id == oznitelik::KESIT) kesit = deger;
        if (id == oznitelik::MALZEME) malzeme = deger;
        if (id == oznitelik::KAT && deger.find(',') == std::string::npos) {
            const int no = std::atoi(deger.c_str());
            for (size_t i = 0; i < sahne_->seviyeler.size(); ++i)
                if (sahne_->seviyeler[i].kat == no) kat = KatAdi(static_cast<int>(i));
        }
    }
    std::string s;
    for (const std::string* p : {&kesit, &malzeme, &kat})
        if (!p->empty()) s += (s.empty() ? "" : " · ") + *p;
    return s;
}

void AnaPencere::Engel(float x, float y, float w, float h) {
    engeller_.push_back(ImVec4(x * olcek_, y * olcek_, (x + w) * olcek_, (y + h) * olcek_));
}

bool AnaPencere::KomutCalistir(const std::string& id, KomutKaynagi kaynak, std::string_view arg) {
    if (!h_.komutlar) return false;
    std::string hata;
    const bool tamam = h_.komutlar->Calistir(id, h_, kaynak, arg, &hata);
    if (!tamam && !hata.empty() && h_.bildirim) h_.bildirim->KomutYaz(hata);
    if (tamam) {
        komutSatiri_.KomutCalisti(id);
        vurguluKomut_ = id;
        vurguBitis_ = simdi + 1000;
    }
    cizimGerekli_ = true;
    return tamam;
}

void AnaPencere::YeniProjeAkisi(std::function<void()> eylem) {
    if (h_.arayuz && h_.arayuz->Iletisim(YONETMELIK_SIHIRBAZI)) {
        sihirbazId_ = YONETMELIK_SIHIRBAZI;
        sihirbazSonrasi_ = std::move(eylem);
        return;
    }
    if (eylem) eylem();
}

// ---- yerleşim (atolye uret.py Yerlesim) ------------------------------------------------------------------------------
void AnaPencere::YerlesimKur(float W, float H) {
    // Yoğunluk (tasarim.md §5, §9.1): "otomatik" → pencere 1600×900 ekranın istemci alanından küçükse sıkı.
    {
        const tema::Olculer& e = tema::Etkin().o;
        const bool siki = yogunlukAyari_ == "siki" ||
                          (yogunlukAyari_ != "rahat" && (W < e.darEsikGenislik || H < e.darEsikYukseklik));
        tema::YogunlukUygula(siki ? tema::Yogunluk::Siki : tema::Yogunluk::Rahat);
    }
    const tema::Olculer& o = tema::Etkin().o;
    Yerlesim L;
    L.W = W;
    L.H = H;
    L.dar = tema::Etkin().yogunluk == tema::Yogunluk::Siki;
    L.tekPanel = W < o.tekPanelEsigi;
    L.baslik = o.baslik;
    L.sekme = o.sekme;
    L.serit = o.seritGovde;
    L.ust = L.baslik + L.sekme + L.serit;
    L.ray = o.ray;
    L.agacW = L.tekPanel || !agacSolda_ ? 0 : o.agac;
    L.ozelW = o.ozellik;
    L.serW = o.pencereSeridi;
    L.gsekme = o.gorunumSekme;
    L.rsekme = o.rihtimSekme;
    L.rihtim = o.rihtim;
    L.komut = o.komut;
    L.durum = o.durum;
    L.alt = H - L.durum - L.komut - L.rihtim - L.rsekme;
    L.agacX = L.ray;
    L.vpX0 = L.ray + L.agacW;
    L.vpX1 = W - L.serW - L.ozelW;
    L.vpY0 = L.ust + L.gsekme;
    L.vpY1 = L.alt;
    L.ozelX = L.vpX1;
    L.serX = W - L.serW;
    L_ = L;
}

int AnaPencere::IsabetTesti(float px, float py) const {
    const float x = px / olcek_, y = py / olcek_;
    if (y < 0 || y >= L_.baslik) return 0;
    const float bx = L_.W - 46 * 3;
    if (x >= bx) return 2 + std::min(2, static_cast<int>((x - bx) / 46));
    // hızlı erişim düğmeleri ve sol blok, sağdaki Ayarlar / Yardım düğmeleri istemcidir
    if (x < 260 || x >= bx - 16 - 2 * 30) return 0;
    return 1;
}

// ---- başlık çubuğu (atolye uret.py baslik_cubugu) --------------------------------------------------------------------
void AnaPencere::BaslikCiz(Ciz& c) {
    const auto& R = c.R();
    const float W = L_.W, h = L_.baslik;
    c.Dikd(0, 0, W, h, R.zemin);
    const float lh = 16, lw = lh * logoEnBoy;
    if (logoDokusu != ImTextureID_Invalid) {
        c.dl->AddImage(ImTextureRef(logoDokusu), c.P(12, (h - lh) / 2), c.P(12 + lw, (h + lh) / 2));
    } else {  // vektör kemer yedeği
        c.dl->PathArcTo(c.P(12 + lw / 2, (h - lh) / 2 + lw / 2), c.S(lw / 2 - 1.2f), 3.14159f, 2 * 3.14159f, 12);
        c.dl->PathStroke(R.metin, c.S(2.4f));
        c.Cizgi(12 + 1.2f, (h - lh) / 2 + lw / 2, 12 + 1.2f, (h + lh) / 2, R.metin, 2.4f);
        c.Cizgi(12 + lw - 1.2f, (h - lh) / 2 + lw / 2, 12 + lw - 1.2f, (h + lh) / 2, R.metin, 2.4f);
    }
    float x = 12 + lw + 7;
    c.Yazi(x, Taban(0, h, 13), "op4", 13, tema::Agirlik::Kalin, R.metin);
    x += c.Gen("op4", 13, tema::Agirlik::Kalin) + 12;
    c.Dusey(x, 8, h - 8, R.cizgi);
    x += 10;
    // Hızlı erişim (komutlar.json hizli_erisim); Dosya ile Düzenle komutları arasında ayraç.
    if (h_.komutlar) {
        std::string oncekiGrup;
        int sayac = 0;
        for (const KomutTanimi& t : h_.komutlar->Tanimlar()) {
            if (!t.hizliErisim) continue;
            const std::string grup = t.id.substr(0, t.id.find('.'));
            if (!oncekiGrup.empty() && grup != oncekiGrup) {
                c.Dusey(x + 4, 8, h - 8, R.cizgi);
                x += 14;
            }
            oncekiGrup = grup;
            const KomutDurumu d = h_.komutlar->Durum(t.id, h_);
            ImGui::PushID(sayac++);
            const bool tik = Tiklama(c, "##hizli", x, 4, 26, h - 8);
            const bool ust = ImGui::IsItemHovered();
            ImGui::PopID();
            if (ust) c.Yuv(x, 4, 26, h - 8, tema::belirtec::R.orta, R.hover);
            c.Simge(t.ikon, x + 13, h / 2, 16, d.kullanilabilir ? R.ikonBuyuk : R.ikonKapali, 1.4f);
            OgeIpucu(c, d.kullanilabilir ? Tr(t.etiket.c_str()) : d.neden, t.kisayol);
            if (tik) KomutCalistir(t.id, KomutKaynagi::HizliErisim);
            x += 28;
        }
    }
    // Ortada proje adı + kaydedilmedi işareti.
    std::string ad = Tr("Adsız 1");
    bool kirli = false, kayitli = false;
    if (h_.belge) {
        ad = h_.belge->Ad();
        kirli = h_.belge->Kirli();
        kayitli = !h_.belge->Yol().empty();
    }
    if (!kayitli && !SahneBos() && !sahne_->baslik.empty()) ad = sahne_->baslik;
    const float tw = c.Gen(ad, 12, tema::Agirlik::Orta);
    const float cx = W / 2;
    c.Yazi(cx - tw / 2, Taban(0, h, 12), ad, 12, tema::Agirlik::Orta, R.metin);
    if (kirli || !kayitli) {
        c.Daire(cx + tw / 2 + 10, h / 2, 3, R.uyariDolgu);
        c.Yazi(cx + tw / 2 + 18, Taban(0, h, 11), Tr(kayitli ? "değişti" : "kaydedilmedi"), 11, tema::Agirlik::Normal, R.metin3);
    }
    // Sağ: kullanıcı / kurum, Ayarlar (dişli), Yardım, pencere düğmeleri.
    const float bx = W - 46 * 3;
    {
        const char* ikonlar[2] = {"ayar", "yardim"};
        const char* idler[2] = {"ayarlar.ac", "yardim.kisayollar"};
        for (int i = 0; i < 2; ++i) {
            const float ix = bx - 16 - static_cast<float>(2 - i) * 30;
            ImGui::PushID(200 + i);
            const bool tik = Tiklama(c, "##sag", ix, 4, 26, h - 8);
            const bool ust = ImGui::IsItemHovered();
            ImGui::PopID();
            if (ust) c.Yuv(ix, 4, 26, h - 8, tema::belirtec::R.orta, R.hover);
            c.Simge(ikonlar[i], ix + 13, h / 2, 16, R.ikonBuyuk, 1.4f);
            OgeIpucu(c, i == 0 ? Tr("Ayarlar") : Tr("Yardım"), i == 0 ? "Ctrl+," : "");
            if (tik) KomutCalistir(idler[i], KomutKaynagi::Menu);
        }
        if (!L_.dar)
            c.YaziSag(bx - 16 - 2 * 30 - 12, Taban(0, h, 11), "Opus Fortis · op4 " + h_.bilgi.surum, 11,
                      tema::Agirlik::Normal, R.metin3);
    }
    const bool buyuk = pencere.buyuk && pencere.buyuk();
    const char* ikon[3] = {"kucult", buyuk ? "geri_yukle" : "buyut", "kapat"};
    for (int i = 0; i < 3; ++i) {
        ImGui::PushID(100 + i);
        const bool tik = Tiklama(c, "##pencere", bx + static_cast<float>(i) * 46, 0, 46, h);
        const bool ust = ImGui::IsItemHovered();
        ImGui::PopID();
        if (ust) c.Dikd(bx + static_cast<float>(i) * 46, 0, 46, h, i == 2 ? R.kapatUzerinde : R.basili);
        c.Simge(ikon[i], bx + static_cast<float>(i) * 46 + 23, h / 2, 13, ust && i == 2 ? R.beyaz : R.ikonKucuk, 1.2f);
        if (!tik) continue;
        if (i == 0 && pencere.kucult) pencere.kucult();
        if (i == 1 && pencere.buyutGeriAl) pencere.buyutGeriAl();
        if (i == 2) {
            if (h_.komutlar && h_.komutlar->Durum("dosya.cikis", h_).bagli)
                KomutCalistir("dosya.cikis", KomutKaynagi::Menu);
            else if (pencere.kapat)
                pencere.kapat();
        }
    }
}

void AnaPencere::TostlarCiz(Ciz& c) {
    std::erase_if(tostlar, [&](const op4::Tost& t) { return t.bitis < simdi; });
    float y = L_.vpY1 - 12;
    for (auto it = tostlar.rbegin(); it != tostlar.rend(); ++it) {
        const float w = c.Gen(it->metin, 12, tema::Agirlik::Orta) + 36;
        const float x = L_.vpX1 - 12 - w;
        y -= 34;
        c.Golge(x, y, w, 28, 4, 5, 0.16f, 2);
        c.Yuv(x, y, w, 28, 4, c.R().yuzey, c.R().cizgi);
        const uint32_t renk = it->tur == TostTuru::Hata    ? c.R().hata
                              : it->tur == TostTuru::Uyari  ? c.R().uyari
                              : it->tur == TostTuru::Basari ? c.R().ok
                                                            : c.R().vurgu;
        c.Daire(x + 13, y + 14, 3.5f, renk);
        c.Yazi(x + 24, Taban(y, 28, 12), it->metin, 12, tema::Agirlik::Orta, c.R().metin);
        Engel(x, y, w, 28);
    }
}

// ---- kare --------------------------------------------------------------------------------------------------------------
void AnaPencere::KareCiz(float dpiOlcek, const SahneDokusu& doku, double simdiMs) {
    simdi = simdiMs;
    // Arayüz ölçeği = DPI × yazı boyutu (Ayarlar › Görüntü › Yazı boyutu): yazı ölçeğinin tamamı ve yazıya bağlı modül
    // ölçüleri (satır, şerit, ağaç, özellik satırları) birlikte büyür; metin kırpılmaz. Otomatik yoğunluk ölçeklenmiş
    // mantıksal alanı izler (YerlesimKur). Yazı boyutları her çizimde tam piksele yuvarlanır (Ciz::Yazi).
    const float olcek = dpiOlcek * yaziCarpani_;
    escPopupAcikti_ = ImGui::IsPopupOpen("", ImGuiPopupFlags_AnyPopupId | ImGuiPopupFlags_AnyPopupLevel);
    if (olcek != olcek_) cizimGerekli_ = true;
    if (stilYenile_ || olcek != olcek_) {
        ArayuzStiliUygula(olcek);
        stilYenile_ = false;
    }
    olcek_ = olcek;
    const ImGuiIO& io = ImGui::GetIO();
    YerlesimKur(io.DisplaySize.x / olcek_, io.DisplaySize.y / olcek_);
    if (!zorla_ && h_.cekirdek && h_.cekirdek->SahneSurumu() != sahneSurumu_) SahneYenile();
    if (h_.gorunum && h_.gorunum->SigdirIstendiMi()) {
        sigdirBekliyor_ = true;
        h_.gorunum->SigdirYapildi();
    }
    if (h_.secim && h_.secim->Surum() != sonSecimSurumu_) {
        sonSecimSurumu_ = h_.secim->Surum();
        ++vurguSurumu_;
        cizimGerekli_ = true;
        if (!h_.secim->Bos() && yanPencere == YanPencere::Baslangic) yanPencere = YanPencere::Ozellikler;
        AgaciSecimeAc();
    }

    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(io.DisplaySize);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0);
    ImGui::Begin("##op4", nullptr,
                 ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoBackground |
                     ImGuiWindowFlags_NoBringToFrontOnFocus | ImGuiWindowFlags_NoSavedSettings |
                     ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoNavFocus | ImGuiWindowFlags_NoDocking);
    ImGui::PopStyleVar(2);
    Ciz c;
    c.dl = ImGui::GetWindowDrawList();
    c.olcek = olcek_;
    c.yazi = &yazilar_;
    engeller_.clear();

    c.Dikd(0, 0, L_.W, L_.H, c.R().zemin);
    GorunumCiz(c, doku);
    GorunumSekmeleriCiz(c);
    if (L_.agacW > 0) AgacPaneliCiz(c, L_.agacX, L_.ust, L_.agacW, L_.alt - L_.ust);
    switch (yanPencere) {
        case YanPencere::Baslangic: BaslangicPaneliCiz(c, L_.ozelX, L_.ust, L_.ozelW, L_.alt - L_.ust); break;
        case YanPencere::Ozellikler: OzelliklerPaneliCiz(c, L_.ozelX, L_.ust, L_.ozelW, L_.alt - L_.ust); break;
        case YanPencere::ModelAgaci:
            if (L_.agacW == 0) {
                AgacPaneliCiz(c, L_.ozelX, L_.ust, L_.ozelW, L_.alt - L_.ust);
                break;
            }
            [[fallthrough]];
        default:
            BosPanelCiz(c, L_.ozelX, L_.ust, L_.ozelW, L_.alt - L_.ust,
                        yanPencere == YanPencere::Kataloglar ? "Kataloglar"
                        : yanPencere == YanPencere::Filtre   ? "Filtre & görünürlük"
                        : yanPencere == YanPencere::Sorgu    ? "Sorgu"
                                                             : "Model ağacı",
                        yanPencere == YanPencere::ModelAgaci ? "Model ağacı solda yapıştırılmış."
                                                             : "Bu pencere sonraki fazda gelir (Faz 3).");
            break;
    }
    PencereSeridiCiz(c);
    RayCiz(c);
    RihtimCiz(c);
    KomutSatiriCiz(c);
    DurumCubuguCiz(c);
    BaslikCiz(c);
    SeritCiz(c);
    TostlarCiz(c);
    GorunumGirdisi(c);
    ImGui::End();

    DosyaMenusu(c);
    AyarlarPenceresi(c);
    HizliAksPenceresi(c);
    BilgiPencereleri(c);
    SihirbazPenceresi(c);
    KisayollariIsle();
    if (gezinme_.Surukluyor() || gezinme_.PencereSeciyor() || !tostlar.empty() || komutAktif_ || !ilerlemeler.empty())
        cizimGerekli_ = true;
}

// ---- C komutları -------------------------------------------------------------------------------------------------------
void AnaPencere::KomutlariBagla() {
    KomutYoneticisi* k = h_.komutlar;
    if (!k) return;
    auto bagla = [&](const char* id, std::function<void(KomutBaglami&)> f,
                     std::function<std::string(const Hizmetler&)> neden = {},
                     std::function<bool(const Hizmetler&)> isaret = {}) {
        KomutIsleyici i;
        i.calistir = std::move(f);
        i.kullanilamazNedeni = std::move(neden);
        i.isaretli = std::move(isaret);
        k->Bagla(id, std::move(i));
    };
    auto modelGerek = [this](const char* ad) {
        return [this, ad](const Hizmetler&) { return SahneBos() ? std::string(Tr(ad)) + ": " + Tr("model boş") : std::string(); };
    };
    auto secimGerek = [](const char* ad) {
        return [ad](const Hizmetler& h) {
            return (!h.secim || h.secim->Bos()) ? std::string(Tr(ad)) + ": " + Tr("önce eleman seçin") : std::string();
        };
    };
    bagla("gorunum.sigdir", [this](KomutBaglami&) { Sigdir(); });
    bagla("gorunum.secime_yakinlas",
          [this](KomutBaglami&) {
              const Kutu3d s = secme_.Sinir(h_.secim->Liste());
              if (!s.Bos()) kamera_.Sigdir(s, gorus_.g, gorus_.y2);
          },
          secimGerek("Seçime yakınlaş"));
    bagla("gorunum.3b", [this](KomutBaglami&) { StandartGorunum(StandartYon::Izometrik); });
    bagla("gorunum.plan", [this](KomutBaglami&) { StandartGorunum(StandartYon::Plan); });
    bagla("gorunum.on", [this](KomutBaglami&) { StandartGorunum(StandartYon::On); });
    bagla("gorunum.yan", [this](KomutBaglami&) { StandartGorunum(StandartYon::Yan); });
    auto katDegistir = [this](int yon) {
        const int n = static_cast<int>(sahne_->seviyeler.size());
        int i = etkinKat;
        do {
            i += yon;
        } while (i >= 0 && i < n && sahne_->seviyeler[static_cast<size_t>(i)].kat < 0);
        if (i < 0 || i >= n) return;
        etkinKat = i;
        if (yon_ == StandartYon::Plan) kamera_.d.hedef.z = sahne_->seviyeler[static_cast<size_t>(i)].z;
        if (h_.bildirim) h_.bildirim->KomutYaz(std::string(Tr("Etkin kat")) + ": " + KatAdi(i));
    };
    auto katNeden = [this](const Hizmetler&) {
        return sahne_->seviyeler.size() < 2 ? std::string(Tr("Kat değiştir: modelde birden çok kat yok")) : std::string();
    };
    bagla("gorunum.ust_kat", [katDegistir](KomutBaglami&) { katDegistir(+1); }, katNeden);
    bagla("gorunum.alt_kat", [katDegistir](KomutBaglami&) { katDegistir(-1); }, katNeden);
    auto kipYaz = [this](GorunumKipi kip) {
        h_.gorunum->kip = kip;
        h_.gorunum->degisti.Yay();
        cizimGerekli_ = true;
    };
    bagla("gorunum.kesit_gorunumu",
          [this, kipYaz](KomutBaglami&) { kipYaz(h_.gorunum->kip == GorunumKipi::Cubuk ? GorunumKipi::Kesit : GorunumKipi::Cubuk); },
          {}, [](const Hizmetler& h) { return h.gorunum && h.gorunum->kip != GorunumKipi::Cubuk; });
    bagla("gorunum.cubuk_kipi", [kipYaz](KomutBaglami&) { kipYaz(GorunumKipi::Cubuk); }, {},
          [](const Hizmetler& h) { return h.gorunum && h.gorunum->kip == GorunumKipi::Cubuk; });
    bagla("gorunum.ekstruzyon", [kipYaz](KomutBaglami&) { kipYaz(GorunumKipi::Kesit); }, {},
          [](const Hizmetler& h) { return h.gorunum && h.gorunum->kip != GorunumKipi::Cubuk; });
    bagla("gorunum.izgara",
          [this](KomutBaglami&) {
              h_.gorunum->izgara = !h_.gorunum->izgara;
              h_.gorunum->degisti.Yay();
          },
          {}, [](const Hizmetler& h) { return h.gorunum && h.gorunum->izgara; });
    bagla("gorunum.baslangic", [this](KomutBaglami&) { yanPencere = YanPencere::Baslangic; });
    bagla("gorunum.arayuzu_sifirla", [this](KomutBaglami&) {
        yanPencere = SahneBos() ? YanPencere::Baslangic : YanPencere::Ozellikler;
        etkinSekme = "Model";
        rihtim = RihtimSekmesi::Komut;
        acik_ = {"proje", "katlar"};
        kapaliBolumler_ = {"Analiz", "Tasarım"};
        for (auto& [ad, acik] : secAnahtar_) acik = ad != "aks" && ad != "yuk";
        StandartGorunum(StandartYon::Izometrik);
    });
    bagla("ayarlar.ac", [this](KomutBaglami&) { ayarlarAcik = true; });
    bagla("yardim.kisayollar", [this](KomutBaglami&) { kisayollarAcik_ = true; });
    bagla("yardim.hakkinda", [this](KomutBaglami&) { hakkindaAcik_ = true; });
    bagla("model.hizli_aks", [this](KomutBaglami& b) {
        if (b.arguman.empty()) {
            hizliAksAcik_ = true;
            return;
        }
        // "HIZLIAKS x=6,6,6 y=6,6 z=4.5,4.5" (senaryo ve komut satırı): doğrudan uygula.
        std::istringstream s(b.arguman);
        std::string p;
        while (s >> p) {
            const size_t e = p.find('=');
            if (e == std::string::npos) continue;
            std::string v = p.substr(e + 1);
            for (char& ch : v)
                if (ch == ';') ch = ' ';
            char* hedef = p[0] == 'x' ? hizliAksX_ : p[0] == 'y' ? hizliAksY_ : p[0] == 'z' ? hizliAksZ_ : nullptr;
            if (hedef) std::snprintf(hedef, 64, "%s", v.c_str());
        }
        nlohmann::json j = {{"x", nlohmann::json::array()}, {"y", nlohmann::json::array()}, {"z", nlohmann::json::array()}};
        for (const auto& [ad, m] : {std::pair{"x", hizliAksX_}, std::pair{"y", hizliAksY_}, std::pair{"z", hizliAksZ_}}) {
            std::istringstream ss(m);
            std::string t;
            while (ss >> t) {
                double d;
                if (SayiOku(t, d) && d > 0) j[ad].push_back(d);
            }
        }
        ModelIslemiUygula(h_, islem::HIZLI_AKS, j.dump());
    });
    bagla("secim.sec", [this](KomutBaglami&) {
        if (h_.bildirim) h_.bildirim->KomutYaz(Tr("SEÇ: tık seçer, Ctrl + tık tersler, Shift + tık çıkarır, Ctrl + sürükle pencereyle seçer."));
    });
    auto hepsi = [this] {
        std::vector<ElemanKimligi> k;
        for (const SahneCubugu& c : sahne_->cubuklar)
            if (Secilebilir(CubukKimligi(c.no))) k.push_back(CubukKimligi(c.no));
        for (const SahnePaneli& p : sahne_->paneller)
            if (Secilebilir(PanelKimligi(p.no))) k.push_back(PanelKimligi(p.no));
        return k;
    };
    bagla("secim.tumu", [this, hepsi](KomutBaglami&) { h_.secim->Uygula(hepsi(), SecimKipi::Yeni); }, modelGerek("Tümünü seç"));
    bagla("secim.temizle", [this](KomutBaglami&) { h_.secim->Temizle(); });
    bagla("secim.ters", [this, hepsi](KomutBaglami&) { h_.secim->Uygula(hepsi(), SecimKipi::Tersle); }, modelGerek("Tersine çevir"));
    bagla("secim.benzer",
          [this](KomutBaglami&) {
              // Aynı alt tür ve kesit (ölçüt listesi seçiminin ilk örneği; Seç & Süz Faz 3'te).
              std::set<std::pair<std::string, std::string>> anahtarlar;
              auto anahtar = [&](size_t s) {
                  const auto a = oz_->Metin(s, oznitelik::ALT_TUR);
                  const auto k = oz_->Metin(s, oznitelik::KESIT);
                  return std::pair<std::string, std::string>(a ? std::string(*a) : "", k ? std::string(*k) : "");
              };
              for (const ElemanKimligi& e : h_.secim->Liste())
                  if (const auto s = oz_->Satir(e)) anahtarlar.insert(anahtar(*s));
              std::vector<ElemanKimligi> k;
              for (size_t s = 0; s < oz_->satirlar.size(); ++s)
                  if (anahtarlar.count(anahtar(s))) k.push_back(oz_->satirlar[s]);
              h_.secim->Uygula(k, SecimKipi::Ekle);
          },
          secimGerek("Benzerini seç"));
    bagla("secim.kata_gore",
          [this](KomutBaglami&) {
              if (etkinKat < 0) return;
              const int no = sahne_->seviyeler[static_cast<size_t>(etkinKat)].kat;
              std::vector<ElemanKimligi> k;
              for (size_t s = 0; s < oz_->satirlar.size(); ++s)
                  for (const double v : oz_->Liste(s, oznitelik::KAT))
                      if (static_cast<int>(std::lround(v)) == no && Secilebilir(oz_->satirlar[s])) {
                          k.push_back(oz_->satirlar[s]);
                          break;
                      }
              h_.secim->Uygula(k, SecimKipi::Yeni);
          },
          modelGerek("Kata göre"));
    for (const auto& [id, kp] : {std::pair{"kapsam.bu_kat", KatKapsami::BuKat}, std::pair{"kapsam.benzer", KatKapsami::BenzerKatlar},
                                 std::pair{"kapsam.tum", KatKapsami::TumKatlar}}) {
        const KatKapsami kk = kp;
        bagla(id, [this, kk](KomutBaglami&) { kapsam = kk; }, {}, [this, kk](const Hizmetler&) { return kapsam == kk; });
    }
}

}  // namespace op4
