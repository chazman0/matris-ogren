// op4 çekirdek — görünüm kamerası (çift hassasiyet) ve mutlak çapalı gezinme matematiği (MIMARI §7.2, §7.3, §25).
//
// Sahibi: C (arayuz-goruntu). Platformdan bağımsızdır, Linux'ta doctest ile sınanır (testler/cekirdek/kamera_*.cpp).
// Faz 0'ın float yörünge kamerası (kaynak/kamera.h) ve onu kullanan proje.* kaldırıldı (F1); çizici ve gezinme bunu kullanır.
//
// Kurallar (bağlayıcı, §7.2):
//  * Sürükleme basışta kamerayı (C₀), imleç pikselini (m₀) ve imlecin altındaki dünya noktasını (P) saklar; her olayda
//    sonuç C₀'dan YENİDEN hesaplanır (artımlı birikim yok) — son konum ara yoldan bağımsızdır (K1).
//  * Kaydırma: m'nin C₀'a göre ışını, P'den geçen ve C₀ görüntü düzlemine paralel düzlemle kesişir (Q); C = C₀ ⊕ (P − Q).
//  * Döndürme: sapma = −k·Δx (dünya Z), eğim = −k·Δy (C₀'ın sağ ekseni), merkez P; k = 0,3°/px; eğim ∈ (−89,9°, 89,9°).
//    Kamera P çevresinde katı döndürülür; P'nin ekran konumu değişmez (K4).
//  * Yakınlaştırma: f = 1,2ⁿ; perspektifte göz ve hedef P'ye doğru 1/f ölçeklenir (P sabit, K3); ortografikte görünür
//    yükseklik /= f ve P sabit kalacak biçimde öteleme. Sınırlar: P'ye en az 0,05 m, ortografik yükseklik 0,05–1e6 m.
#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

#include "cekirdek/secme.h"
#include "cekirdek/vektor.h"

namespace op4 {

inline constexpr double KAMERA_PI = 3.14159265358979323846;
inline constexpr double DERECE = KAMERA_PI / 180.0;

// Kalıcı kamera durumu (.op4 gorunum/gorunum.json; görünüm başına bir tane).
struct KameraDurumu {
    V3d hedef{0, 0, 0};          // bakılan nokta (yörüngenin varsayılan merkezi)
    double uzaklik = 30.0;       // göz – hedef uzaklığı (m)
    double sapma = -135.0 * DERECE;  // Z çevresinde; göz yönü (cos e·cos s, cos e·sin s, sin e)
    double egim = 30.0 * DERECE;     // yatay düzlemden yukarı
    bool ortografik = false;
    double ortoYukseklik = 20.0; // ortografikte görüş alanının dünya yüksekliği (m)
    double dikeyAci = 40.0 * DERECE;  // perspektif dikey görüş açısı
};

class GorunumKamerasi {
public:
    KameraDurumu d;

    // Eksenler (dünya). Sağ eksen her zaman yataydır (yuvarlanma yok; eğim ±90°'de de tanımlı).
    V3d GozYonu() const;   // hedeften göze birim vektör
    V3d Ileri() const { return -GozYonu(); }
    V3d Sag() const;
    V3d Yukari() const;
    V3d Goz() const { return d.hedef + GozYonu() * d.uzaklik; }

    // Görüş alanı g × y piksel için çift hassasiyetli izdüşüm (ters-Z; perspektifte sonsuz uzak düzlem).
    GorusIzdusumu Izdusum(double g, double y, double dpiOlcek = 1.0) const;
    // Hedef derinliğinde (ya da ortografikte) bir pikselin dünya boyu.
    double PikselBoyu(double gorusYuksekligi) const;

    // Kutuyu görüş alanına sığdırır (yön korunur). Boş kutuda değişmez.
    void Sigdir(const Kutu3d& k, double g, double y);
};

enum class StandartYon : uint8_t { Izometrik = 0, Plan = 1, On = 2, Yan = 3 };
// Standart görünüm (Alt+1…4): yön + izdüşüm türü; hedef ve ölçek Sığdır ile kurulur.
void StandartYonUygula(GorunumKamerasi& k, StandartYon y);

// ---- mutlak çapalı sürükleme ------------------------------------------------------------------------------------------
enum class SuruklemeTuru : uint8_t { Yok = 0, Kaydir = 1, Dondur = 2 };

class KameraSuruklemesi {
public:
    static constexpr double DONME_K = 0.3 * DERECE;   // rad / px (§7.2)
    static constexpr double EGIM_SINIRI = 89.9 * DERECE;

    // Sürüklemeyi başlatır: c₀ = k.d, m₀ = (px, py), P = cekirdekNokta (imlecin altındaki dünya noktası).
    void Basla(const GorunumKamerasi& k, SuruklemeTuru tur, double px, double py, V3d P, double g, double y);
    // İmleç (px, py) iken kamerayı C₀'dan yeniden kurar. Etkin değilse dokunmaz.
    void Guncelle(GorunumKamerasi& k, double px, double py) const;
    void Bitir() { tur_ = SuruklemeTuru::Yok; }
    bool Etkin() const { return tur_ != SuruklemeTuru::Yok; }
    SuruklemeTuru Tur() const { return tur_; }
    V3d Cekirdek() const { return P_; }
    const KameraDurumu& Baslangic() const { return c0_; }

private:
    SuruklemeTuru tur_ = SuruklemeTuru::Yok;
    KameraDurumu c0_;
    double mx0_ = 0, my0_ = 0, g_ = 1, y_ = 1;
    V3d P_;
};

// Tekerlek / kıstırma: imlecin altındaki P sabit kalacak biçimde f = 1,2^adim yakınlaşır (adim kesirli olabilir).
void Yakinlas(GorunumKamerasi& k, double adim, V3d P);

// İmlecin altındaki nokta için yedek: z = calismaZ düzlemi kesişimi (önünde ise), yoksa hedef derinliğindeki nokta.
V3d CalismaDuzlemiNoktasi(const GorunumKamerasi& k, double px, double py, double g, double y, double calismaZ = 0.0);

// JSON gidiş-dönüşü (gorunum/gorunum.json katkısı).
std::string KameraJson(const KameraDurumu& d);
bool KameraJsonOku(std::string_view json, KameraDurumu& d);

}  // namespace op4
