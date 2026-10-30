// op4 çekirdek sözleşmesi — çift hassasiyetli vektör ve kutu (sözleşme S3).
//
// Model koordinatları CPU'da double tutulur (MIMARI §6.2). Dünya: sağ el, Z yukarı, birim metre (bina sistemi: X sağa,
// Y derinlik). GPU'ya giderken sahne çapasına göreli float'a çevrilir (bu C paketinin işidir; bkz. gorunum.h).
#pragma once

#include <algorithm>
#include <cmath>

namespace op4 {

struct V3d {
    double x = 0, y = 0, z = 0;
};

inline V3d operator+(V3d a, V3d b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
inline V3d operator-(V3d a, V3d b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
inline V3d operator-(V3d a) { return {-a.x, -a.y, -a.z}; }
inline V3d operator*(V3d a, double s) { return {a.x * s, a.y * s, a.z * s}; }
inline V3d operator*(double s, V3d a) { return a * s; }
inline bool operator==(V3d a, V3d b) { return a.x == b.x && a.y == b.y && a.z == b.z; }
inline double Nokta(V3d a, V3d b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline V3d Capraz(V3d a, V3d b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
inline double Uzunluk(V3d a) { return std::sqrt(Nokta(a, a)); }
inline V3d Birim(V3d a) {
    const double u = Uzunluk(a);
    return u > 1e-300 ? a * (1.0 / u) : V3d{};
}

// Eksenlere hizalı kutu. Boş kutu: enKucuk > enBuyuk.
struct Kutu3d {
    V3d enKucuk{1e300, 1e300, 1e300};
    V3d enBuyuk{-1e300, -1e300, -1e300};

    bool Bos() const { return enKucuk.x > enBuyuk.x; }
    void Kapsa(V3d p) {
        enKucuk = {std::min(enKucuk.x, p.x), std::min(enKucuk.y, p.y), std::min(enKucuk.z, p.z)};
        enBuyuk = {std::max(enBuyuk.x, p.x), std::max(enBuyuk.y, p.y), std::max(enBuyuk.z, p.z)};
    }
    void Kapsa(const Kutu3d& k) {
        if (k.Bos()) return;
        Kapsa(k.enKucuk);
        Kapsa(k.enBuyuk);
    }
    V3d Merkez() const { return (enKucuk + enBuyuk) * 0.5; }
};

}  // namespace op4
