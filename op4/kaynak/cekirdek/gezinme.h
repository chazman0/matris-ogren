// op4 çekirdek — görünüm alanı fare eşlemesi ve gezinme durum makinesi (MIMARI §7.1, §25; bağlayıcı kullanıcı isteği 8).
//
// Sahibi: C. Platformdan bağımsızdır (Win32 olayları uygulama tarafında çevrilir); Linux'ta sınanır (kamera_*.cpp).
// "op4 varsayılanı" eşlemesi:
//   sol sürükle (eşik 4 px × DPI)   kaydır          Shift + sol sürükle   döndür (plan / cephede kaydır)
//   orta sürükle                    kaydır          Shift + orta sürükle  döndür
//   tekerlek                        imlece yakınlaş (1,2× / çentik, kesirli)
//   sol tık                         seç (yeni)      Ctrl + sol tık        seçimde tersle    Shift + sol tık   çıkar
//   Ctrl + sol sürükle              pencere seçimi (ekle): soldan sağa tam içinde, sağdan sola değen
//   Ctrl + Shift + sol sürükle      pencereyle seçimden çıkar
//   orta çift tık                   sığdır
// "klasik CAD" eşlemesi: orta kaydırır, Shift + orta döndürür, sol sürükle pencere seçer (Ctrl ekler, Ctrl+Shift çıkarır).
#pragma once

#include <cstdint>
#include <functional>
#include <optional>

#include "cekirdek/kamera.h"
#include "cekirdek/secim.h"
#include "cekirdek/secme.h"

namespace op4 {

enum class FareTusu : uint8_t { Sol = 0, Orta = 1, Sag = 2 };

struct Degistiriciler {
    bool ctrl = false, shift = false, alt = false;
};

enum class FareEslemesi : uint8_t { Op4 = 0, Klasik = 1 };

// Gezinmenin dış dünyaya bağlantıları (uygulama doldurur; sınamada sahte).
struct GezinmeBaglantisi {
    // İmlecin altındaki dünya noktası (BVH ışın vuruşu → çalışma düzlemi → hedef derinliği; MIMARI §7.2).
    std::function<V3d(double px, double py)> cekirdekNokta;
    // Tık seçimi ve pencere seçimi.
    std::function<void(double px, double py, SecimKipi kip)> tikla;
    std::function<void(double x0, double y0, double x1, double y1, PencereKipi pk, SecimKipi kip)> pencere;
    std::function<void()> sigdir;
    std::function<void(double px, double py)> baglamMenusu;
};

class Gezinme {
public:
    GezinmeBaglantisi baglanti;
    FareEslemesi esleme = FareEslemesi::Op4;
    double dpiOlcek = 1.0;
    double esikPx = 4.0;          // DPI ölçeksiz sürükleme eşiği
    bool donmeKilitli = false;    // plan ve cephe görünümleri: döndürme isteği kaydırmaya döner

    // Görüş alanı boyutu (piksel); her karede ya da boyut değişince.
    void Boyut(double g, double y) {
        g_ = g;
        y_ = y;
    }

    // Olaylar (görüş alanı pikseli; sol üst = 0,0). Bas yalnız görüş alanının içindeyse çağrılır.
    void Bas(GorunumKamerasi& k, FareTusu t, double px, double py, Degistiriciler m);
    void Hareket(GorunumKamerasi& k, double px, double py, Degistiriciler m);
    void Birak(GorunumKamerasi& k, FareTusu t, double px, double py, Degistiriciler m);
    void Tekerlek(GorunumKamerasi& k, double adim, double px, double py);
    void CiftTik(GorunumKamerasi& k, FareTusu t, double px, double py);
    void Iptal();  // Esc / odak kaybı: sürükleme biter, kamera son hâlinde kalır

    // Durum (çizim ve imleç için).
    bool Surukluyor() const { return surukleme_.Etkin(); }
    SuruklemeTuru Tur() const { return surukleme_.Tur(); }
    bool PencereSeciyor() const { return durum_ == Durum::Pencere; }
    // Pencere seçimi dikdörtgeni (başlangıç → şimdiki); kip sağdan sola ise Degen.
    bool PencereDikdortgeni(double& x0, double& y0, double& x1, double& y1, PencereKipi& pk) const;
    bool Basili() const { return durum_ != Durum::Bos; }
    std::optional<V3d> Cekirdek() const {
        if (!surukleme_.Etkin()) return std::nullopt;
        return surukleme_.Cekirdek();
    }

private:
    enum class Durum : uint8_t { Bos, Bekliyor, Surukle, Pencere };
    void SuruklemeyiBaslat(GorunumKamerasi& k, SuruklemeTuru tur, double px, double py);
    SuruklemeTuru SolTur(Degistiriciler m) const;

    Durum durum_ = Durum::Bos;
    FareTusu tus_ = FareTusu::Sol;
    double bx_ = 0, by_ = 0, sx_ = 0, sy_ = 0;  // basış ve son konum
    Degistiriciler basM_;
    bool shiftSurukleme_ = false;
    KameraSuruklemesi surukleme_;
    double g_ = 1, y_ = 1;
};

}  // namespace op4
