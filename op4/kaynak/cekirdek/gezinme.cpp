// op4 çekirdek — gezinme durum makinesi (bkz. gezinme.h). Sahibi: C.
#include "cekirdek/gezinme.h"

#include <cmath>

namespace op4 {

SuruklemeTuru Gezinme::SolTur(Degistiriciler m) const {
    if (m.shift && !donmeKilitli) return SuruklemeTuru::Dondur;
    return SuruklemeTuru::Kaydir;
}

void Gezinme::SuruklemeyiBaslat(GorunumKamerasi& k, SuruklemeTuru tur, double px, double py) {
    const V3d P = baglanti.cekirdekNokta ? baglanti.cekirdekNokta(px, py) : CalismaDuzlemiNoktasi(k, px, py, g_, y_);
    surukleme_.Basla(k, tur, px, py, P, g_, y_);
}

void Gezinme::Bas(GorunumKamerasi& k, FareTusu t, double px, double py, Degistiriciler m) {
    if (durum_ != Durum::Bos) return;  // ikinci tuş: ilk sürükleme sürer
    tus_ = t;
    bx_ = sx_ = px;
    by_ = sy_ = py;
    basM_ = m;
    if (t == FareTusu::Orta) {
        // Orta tuş: eşik beklemeden kaydır / döndür (iki eşlemede de).
        durum_ = Durum::Surukle;
        shiftSurukleme_ = m.shift;
        SuruklemeyiBaslat(k, (m.shift && !donmeKilitli) ? SuruklemeTuru::Dondur : SuruklemeTuru::Kaydir, px, py);
        return;
    }
    durum_ = Durum::Bekliyor;
}

void Gezinme::Hareket(GorunumKamerasi& k, double px, double py, Degistiriciler m) {
    sx_ = px;
    sy_ = py;
    switch (durum_) {
        case Durum::Bos:
            return;
        case Durum::Bekliyor: {
            if (std::hypot(px - bx_, py - by_) < esikPx * dpiOlcek) return;
            if (tus_ == FareTusu::Sag) return;  // sağ tuş sürüklemesi Faz 1'de yok sayılır (bağlam menüsü bırakınca)
            const bool pencere = esleme == FareEslemesi::Op4 ? basM_.ctrl : true;
            if (pencere) {
                durum_ = Durum::Pencere;
                return;
            }
            durum_ = Durum::Surukle;
            shiftSurukleme_ = m.shift;
            // Çapa basış anındaki imleçtir (§7.2: m₀); sürükleme eşiği aşınca sahne imlece yetişir.
            SuruklemeyiBaslat(k, SolTur(m), bx_, by_);
            surukleme_.Guncelle(k, px, py);
            return;
        }
        case Durum::Surukle:
            // Shift sürükleme sırasında değişirse kip o anki konumdan kesintisiz değişir.
            if (m.shift != shiftSurukleme_ && !donmeKilitli) {
                shiftSurukleme_ = m.shift;
                const SuruklemeTuru yeni = m.shift ? SuruklemeTuru::Dondur : SuruklemeTuru::Kaydir;
                if (yeni != surukleme_.Tur()) SuruklemeyiBaslat(k, yeni, px, py);
            }
            surukleme_.Guncelle(k, px, py);
            return;
        case Durum::Pencere:
            return;
    }
}

void Gezinme::Birak(GorunumKamerasi& k, FareTusu t, double px, double py, Degistiriciler m) {
    if (durum_ == Durum::Bos || t != tus_) return;
    sx_ = px;
    sy_ = py;
    const Durum d = durum_;
    durum_ = Durum::Bos;
    if (d == Durum::Surukle) {
        surukleme_.Guncelle(k, px, py);
        surukleme_.Bitir();
        return;
    }
    if (d == Durum::Pencere) {
        const PencereKipi pk = px >= bx_ ? PencereKipi::TamIcinde : PencereKipi::Degen;
        SecimKipi sk = SecimKipi::Ekle;  // op4: Ctrl + sol sürükle seçime ekler
        if (basM_.shift) sk = SecimKipi::Cikar;
        else if (!basM_.ctrl && esleme == FareEslemesi::Klasik) sk = SecimKipi::Yeni;
        if (baglanti.pencere) baglanti.pencere(bx_, by_, px, py, pk, sk);
        return;
    }
    // Eşik aşılmadı: tık.
    if (t == FareTusu::Sol) {
        const SecimKipi sk = m.ctrl ? SecimKipi::Tersle : (m.shift ? SecimKipi::Cikar : SecimKipi::Yeni);
        if (baglanti.tikla) baglanti.tikla(px, py, sk);
    } else if (t == FareTusu::Sag) {
        if (baglanti.baglamMenusu) baglanti.baglamMenusu(px, py);
    }
}

void Gezinme::Tekerlek(GorunumKamerasi& k, double adim, double px, double py) {
    if (adim == 0.0) return;
    const V3d P = baglanti.cekirdekNokta ? baglanti.cekirdekNokta(px, py) : CalismaDuzlemiNoktasi(k, px, py, g_, y_);
    Yakinlas(k, adim, P);
    // Sürükleme sürerken tekerlek: yeni kamera C₀ olur (çapa korunur).
    if (surukleme_.Etkin()) {
        const SuruklemeTuru tur = surukleme_.Tur();
        const V3d c = surukleme_.Cekirdek();
        surukleme_.Basla(k, tur, sx_, sy_, c, g_, y_);
    }
}

void Gezinme::CiftTik(GorunumKamerasi&, FareTusu t, double, double) {
    if (t == FareTusu::Orta && baglanti.sigdir) baglanti.sigdir();
}

void Gezinme::Iptal() {
    durum_ = Durum::Bos;
    surukleme_.Bitir();
}

bool Gezinme::PencereDikdortgeni(double& x0, double& y0, double& x1, double& y1, PencereKipi& pk) const {
    if (durum_ != Durum::Pencere) return false;
    x0 = bx_;
    y0 = by_;
    x1 = sx_;
    y1 = sy_;
    pk = sx_ >= bx_ ? PencereKipi::TamIcinde : PencereKipi::Degen;
    return true;
}

}  // namespace op4
