// op4 — yörünge kamerası (hedef noktası çevresinde). Gezinme kuralları (kullanıcı isteği):
//   sol sürükle = kaydır (pan), Shift + sol sürükle = döndür, orta sürükle = kaydır, tekerlek = imlece doğru yakınlaş.
// Titreşimsiz kaydırma: her fare olayında artımlı (delta) birikim yerine sürükleme başındaki kamera durumundan
// MUTLAK ofset hesaplanır; imlecin altındaki nokta (hedef derinliğinde) imleçle birlikte birebir hareket eder ve
// yuvarlama hatası birikmez.
#pragma once

#include <algorithm>

#include "matematik.h"

namespace op4 {

struct Kamera {
    V3 hedef{3.0f, 2.5f, 1.6f};
    float uzaklik = 17.0f;
    float sapma = -2.25f;   // Z çevresinde (yaw), radyan
    float egim = 0.42f;     // yatay düzlemden yukarı (pitch), radyan
    float dikeyAci = 40.0f * PI / 180.0f;
    float yakin = 0.05f;

    V3 Yon() const {  // gözden hedefe doğru birim vektörün tersi (hedeften göze)
        return {std::cos(egim) * std::cos(sapma), std::cos(egim) * std::sin(sapma), std::sin(egim)};
    }
    V3 Goz() const { return hedef + Yon() * uzaklik; }
    M4 Gorunum() const { return BakisMatrisi(Goz(), hedef, {0, 0, 1}); }
    M4 Izdusum(float enBoy) const { return PerspektifTersZ(dikeyAci, enBoy, yakin); }
    M4 GorunumIzdusum(float enBoy) const { return Carp(Izdusum(enBoy), Gorunum()); }

    // Ekran düzlemindeki sağ ve yukarı birim vektörleri (dünya).
    void EkranEksenleri(V3& sag, V3& yukari) const {
        V3 f = -Yon();
        sag = Birim(Capraz(f, {0, 0, 1}));
        yukari = Capraz(sag, f);
    }
    // Hedef derinliğinde bir pikselin dünya boyu.
    float PikselBoyu(float gorusYuksekligi) const {
        return 2.0f * uzaklik * std::tan(dikeyAci * 0.5f) / std::max(1.0f, gorusYuksekligi);
    }

    // --- sürükleme (mutlak) -----------------------------------------------------------------------------------
    struct Surukleme {
        bool etkin = false;
        bool dondur = false;
        float x0 = 0, y0 = 0;
        V3 hedef0;
        float sapma0 = 0, egim0 = 0;
    } surukleme;

    void SuruklemeBasla(float x, float y, bool dondur) {
        surukleme = {true, dondur, x, y, hedef, sapma, egim};
    }
    void SuruklemeGuncelle(float x, float y, float gorusYuksekligi) {
        if (!surukleme.etkin) return;
        float dx = x - surukleme.x0, dy = y - surukleme.y0;
        if (surukleme.dondur) {
            sapma = surukleme.sapma0 - dx * 0.0065f;
            egim = std::clamp(surukleme.egim0 + dy * 0.0065f, -1.553f, 1.553f);
            hedef = surukleme.hedef0;
        } else {
            V3 sag, yukari;
            EkranEksenleri(sag, yukari);
            float s = PikselBoyu(gorusYuksekligi);
            hedef = surukleme.hedef0 - sag * (dx * s) + yukari * (dy * s);
        }
    }
    void SuruklemeBitir() { surukleme.etkin = false; }

    // Görüş alanındaki (px, py) pikselinin altında, hedeften geçen ekran düzlemindeki dünya noktası.
    V3 HedefDuzlemNoktasi(float px, float py, float g, float y) const {
        V3 sag, yukari;
        EkranEksenleri(sag, yukari);
        float s = PikselBoyu(y);
        return hedef + sag * ((px - g * 0.5f) * s) - yukari * ((py - y * 0.5f) * s);
    }
    // Dünya noktasını görüş alanı pikseline izdüşürür (g × y alan). Kameranın arkasındaysa false.
    bool Izdusur(V3 p, float g, float y, float& sx, float& sy) const {
        M4 vp = GorunumIzdusum(g / std::max(1.0f, y));
        float v[4] = {p.x, p.y, p.z, 1.0f}, o[4];
        Donustur(vp, v, o);
        if (o[3] <= 1e-9f) return false;
        sx = (o[0] / o[3] * 0.5f + 0.5f) * g;
        sy = (0.5f - o[1] / o[3] * 0.5f) * y;
        return true;
    }

    // Tekerlek: (px, py) görüş alanı içindeki piksel; (g, y) görüş alanı boyutu. İmlecin altındaki nokta sabit kalır.
    void Yakinlas(float adim, float px, float py, float g, float y) {
        float k = std::pow(0.85f, adim);
        float yeni = std::clamp(uzaklik * k, 0.2f, 5000.0f);
        k = yeni / uzaklik;
        V3 p = HedefDuzlemNoktasi(px, py, g, y);
        hedef = p + (hedef - p) * k;
        uzaklik = yeni;
    }

    // Kutuyu (min, max) görüş alanına sığdır.
    void Sigdir(V3 enKucuk, V3 enBuyuk) {
        hedef = (enKucuk + enBuyuk) * 0.5f;
        float r = 0.5f * Uzunluk(enBuyuk - enKucuk);
        uzaklik = std::max(1.0f, r / std::sin(dikeyAci * 0.5f) * 0.9f);  // küre sınırı tutucu; biraz sıkılaştır
    }
};

}  // namespace op4
