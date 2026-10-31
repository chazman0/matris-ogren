// op4 arayüzü — belirteçlerden (tema_belirtec.h) etkin temanın kurulması (bkz. tema.h). Renk değeri burada da yazılmaz:
// türetilmiş roller (çubuk çizgileri, panel dolgusu, aks çizgisi…) belirteçlerin saydamlık / karışımıdır.
#include "arayuz/tema.h"

#include <algorithm>
#include <cmath>

namespace op4::tema {
namespace {

namespace b = belirtec;

constexpr uint32_t K(uint32_t rrggbb, float alfa = 1.0f) { return Renk(rrggbb, alfa); }

Tipografi TipografiKur() {
    Tipografi y{};
    y.sayfa = b::Y.sayfa.boy;
    y.pencere = b::Y.pencere.boy;
    y.baslik = b::Y.baslik.boy;
    y.govde = b::Y.govde.boy;
    y.etiket = b::Y.etiket.boy;
    y.kucuk = b::Y.kucuk.boy;
    y.rozet = b::Y.rozet.boy;
    y.rayBolum = b::Y.bolum.boy;
    return y;
}

Tema IlkTema() {
    Tema t{};
    t.palet = static_cast<Palet>(b::VARSAYILAN_PALET);
    t.r = RenkleriKur(t.palet);
    t.y = TipografiKur();
    t.o = OlculeriKur(Yogunluk::Rahat);
    return t;
}

}  // namespace

uint32_t Karisim(uint32_t a, uint32_t c, float t) {
    t = std::clamp(t, 0.0f, 1.0f);
    uint32_t s = 0;
    for (int k = 0; k < 32; k += 8) {
        const float x = static_cast<float>((a >> k) & 0xFF), y = static_cast<float>((c >> k) & 0xFF);
        s |= static_cast<uint32_t>(std::lround(x + (y - x) * t)) << k;
    }
    return s;
}

Palet PaletKodundan(std::string_view kod) {
    for (int i = 0; i < b::PALET_SAYISI; ++i)
        if (kod == b::PALETLER[i].kimlik) return static_cast<Palet>(i);
    return static_cast<Palet>(b::VARSAYILAN_PALET);
}
const char* PaletKodu(Palet p) { return b::PALETLER[std::min<int>(static_cast<int>(p), b::PALET_SAYISI - 1)].kimlik; }
const char* PaletAdi(Palet p) { return b::PALETLER[std::min<int>(static_cast<int>(p), b::PALET_SAYISI - 1)].ad; }

Renkler RenkleriKur(Palet p) {
    const b::Notr& n = b::NOTR;
    const b::PaletRenk& v = b::PALETLER[std::min<int>(static_cast<int>(p), b::PALET_SAYISI - 1)].r;
    const b::Anlam& a = b::ANLAM;
    const b::Model& m = b::MODEL;
    Renkler r{};
    r.zemin = K(n.zemin);
    r.zemin2 = K(n.zemin2);
    r.yuzey = K(n.yuzey);
    r.yuzey2 = K(n.yuzey2);
    r.sayfa = K(n.sayfa);
    r.alan = K(n.alan);
    r.alanKenar = K(n.alan_kenar);
    r.hover = K(n.hover);
    r.basili = K(n.basili);
    r.cizgi = K(n.cizgi);
    r.cizgi2 = K(n.cizgi2);
    r.yuzey3 = r.basili;
    r.girisKenar = r.alanKenar;
    r.dugmeKenar = K(n.kenar);
    r.anahtarKapali = Karisim(K(n.kenar), K(n.metin4), 0.35f);  // tasarım: kapalı anahtar izi
    r.metin = K(n.metin);
    r.metin2 = K(n.metin2);
    r.metin3 = K(n.metin3);
    r.metin4 = K(n.metin4);
    r.ikonBuyuk = K(n.simge);
    r.ikonKucuk = K(n.simge2);
    r.ikonKapali = K(n.metin4);
    r.golge = K(n.golge);
    r.karartma = K(n.karartma, 0.38f);
    r.beyaz = K(n.beyaz);
    r.antrasit = K(n.metin);

    r.vurgu = K(v.vurgu);
    r.vurguKoyu = K(v.vurgu_koyu);
    r.vurguUzerinde = r.vurguKoyu;
    r.vurguMetin = K(v.vurgu_metin);
    r.vurguTon = K(v.vurgu_ton);
    r.vurguTon2 = K(v.vurgu_ton2);
    r.secim = K(v.secim);
    r.secimTon = K(v.secim_ton);
    r.secimTon2 = K(v.secim_ton2);
    r.seciliDolgu = K(v.secim_dolgu);
    r.uzerinde = K(v.hover_model);
    r.odak = K(v.odak);

    r.ok = K(a.ok);
    r.okTon = K(a.ok_ton);
    r.uyari = K(a.uyari);
    r.uyariTon = K(a.uyari_ton);
    r.uyariDolgu = K(a.uyari_dolgu);
    r.hata = K(a.hata);
    r.hataTon = K(a.hata_ton);
    r.hataKenar = K(a.hata_kenar);
    r.bilgi = K(a.bilgi);
    r.kapatUzerinde = K(a.hata);  // pencere kapat düğmesi üzerinde
    r.eksenX = K(a.eksen_x);
    r.eksenY = K(a.eksen_y);
    r.eksenZ = K(a.eksen_z);

    r.sahneUst = K(m.vp_ust);
    r.sahneAlt = K(m.vp_alt);
    r.sahneIsik = K(m.vp_isik);
    r.kolon = K(m.kolon);
    r.kiris = K(m.kiris);
    r.asik = K(m.asik);
    r.capraz = K(m.capraz);
    r.doseme = K(m.doseme);
    r.temel = K(m.temel);
    r.digerCubuk = K(m.tali);
    r.kenar = K(m.kenar, 0.85f);
    r.kenarInce = K(m.kenar_ince, 0.8f);
    r.kenarDoseme = K(m.kenar_doseme);
    r.izgara = K(m.izgara);
    r.izgaraAna = K(m.izgara_ana);
    // Çubuk görünümü: sabit pikselli çizgiler model kenar renklerinden (tür ayrımı ton farkıyla, renk değil).
    r.cubukKolon = K(m.kenar);
    r.cubukKiris = K(m.kenar_ince);
    r.cubukAsik = K(m.kenar_doseme);
    r.cubukCapraz = K(m.aks);
    r.cubukDiger = K(m.kenar_doseme);
    r.panelDolgu = K(m.izgara, 0.22f);
    r.panelKenar = K(m.kenar_doseme, 0.7f);
    r.aksCizgisi = K(m.aks, 0.7f);
    r.aksBalonKenar = K(m.aks);
    r.katCizgisi = K(m.izgara_ana, 0.55f);
    r.dugum = K(n.metin2);
    r.serbestDugum = K(a.hata);
    r.mesnet = K(n.metin2);
    r.tutamacBaslangic = r.secim;
    r.tutamacBitis = r.secim;
    for (int i = 0; i < 5; ++i) r.dc[i] = K(b::DC_RENK[i]);
    return r;
}

Olculer OlculeriKur(Yogunluk y) {
    const b::Olcu& k = y == Yogunluk::Siki ? b::OLCU_SIKI : b::OLCU_RAHAT;
    Olculer o{};
    o.baslik = k.baslik;
    o.sekme = k.sekme;
    o.seritGovde = k.serit;
    o.ray = k.ray;
    o.agac = k.agac;
    o.ozellik = k.ozel;
    o.pencereSeridi = k.pencere_seridi;
    o.gorunumSekme = k.gsekme;
    o.rihtimSekme = k.rihtim_sekme;
    o.rihtim = k.rihtim;
    o.komut = k.komut;
    o.durum = k.durum;
    o.panelBaslik = k.panel_baslik;
    o.nesneBaslik = k.nesne;
    o.altCubuk = k.panel_alt;
    o.segment = k.segment;
    o.arama = k.arama;
    o.satir = k.satir_agac;
    o.ozellikSatiri = k.satir_ozel;
    o.alan = k.alan_h;
    o.bolum = k.bolum;
    o.buyukDugme = k.buyuk_dugme;
    o.kucukAdim = k.kucuk_satir;
    o.rayDugme = k.ray_dugme;
    o.girintiDuzey = y == Yogunluk::Siki ? 12.0f : 16.0f;
    o.yaricapKucuk = b::R.kucuk;
    o.yaricap = b::R.orta;
    o.kartYaricap = b::R.buyuk;
    o.pencereYaricap = b::R.pencere;
    o.pilYaricap = b::R.buyuk;
    return o;
}

Tema& Etkin() {
    static Tema t = IlkTema();
    return t;
}

void PaletUygula(Palet p) {
    Tema& t = Etkin();
    t.palet = p;
    t.r = RenkleriKur(p);
}

void YogunlukUygula(Yogunluk y) {
    Tema& t = Etkin();
    if (t.yogunluk == y) return;
    t.yogunluk = y;
    t.o = OlculeriKur(y);
}

}  // namespace op4::tema
