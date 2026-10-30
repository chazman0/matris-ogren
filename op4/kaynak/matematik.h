// op4 — küçük vektör / matris kitaplığı. Dünya: sağ el, Z yukarı (yapı yazılımlarındaki gibi), birim metre.
// M4 satır öncelikli saklanır ve sütun vektörüyle çarpılır: p' = M · p (HLSL'de "row_major" ile aynı düzen).
#pragma once

#include <cmath>

namespace op4 {

constexpr float PI = 3.14159265358979f;

struct V3 {
    float x = 0, y = 0, z = 0;
};

inline V3 operator+(V3 a, V3 b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
inline V3 operator-(V3 a, V3 b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
inline V3 operator-(V3 a) { return {-a.x, -a.y, -a.z}; }
inline V3 operator*(V3 a, float s) { return {a.x * s, a.y * s, a.z * s}; }
inline V3 operator*(float s, V3 a) { return a * s; }
inline float Nokta(V3 a, V3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline V3 Capraz(V3 a, V3 b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
inline float Uzunluk(V3 a) { return std::sqrt(Nokta(a, a)); }
inline V3 Birim(V3 a) {
    float u = Uzunluk(a);
    return u > 1e-20f ? a * (1.0f / u) : V3{0, 0, 0};
}

struct M4 {
    float m[16] = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    float& operator()(int r, int c) { return m[r * 4 + c]; }
    float operator()(int r, int c) const { return m[r * 4 + c]; }
};

inline M4 Carp(const M4& a, const M4& b) {
    M4 c;
    for (int r = 0; r < 4; ++r)
        for (int k = 0; k < 4; ++k) {
            float t = 0;
            for (int j = 0; j < 4; ++j) t += a(r, j) * b(j, k);
            c(r, k) = t;
        }
    return c;
}

// (x, y, z, w) dönüşümü; w'ye bölmez.
inline void Donustur(const M4& a, const float v[4], float o[4]) {
    for (int r = 0; r < 4; ++r) o[r] = a(r, 0) * v[0] + a(r, 1) * v[1] + a(r, 2) * v[2] + a(r, 3) * v[3];
}

// Sağ el bakış matrisi: kamera -Z yönüne bakar.
inline M4 BakisMatrisi(V3 goz, V3 hedef, V3 yukari) {
    V3 f = Birim(hedef - goz);
    V3 s = Birim(Capraz(f, yukari));
    V3 u = Capraz(s, f);
    M4 v;
    v(0, 0) = s.x; v(0, 1) = s.y; v(0, 2) = s.z; v(0, 3) = -Nokta(s, goz);
    v(1, 0) = u.x; v(1, 1) = u.y; v(1, 2) = u.z; v(1, 3) = -Nokta(u, goz);
    v(2, 0) = -f.x; v(2, 1) = -f.y; v(2, 2) = -f.z; v(2, 3) = Nokta(f, goz);
    v(3, 0) = 0; v(3, 1) = 0; v(3, 2) = 0; v(3, 3) = 1;
    return v;
}

// Ters-Z, sonsuz uzak düzlemli perspektif: yakın düzlemde derinlik 1, sonsuzda 0. D32_FLOAT ile birlikte
// derinlik duyarlılığı uzaklıkla neredeyse sabit kalır (yakınlaştırınca z-titremesi / kalite kaybı olmaz).
inline M4 PerspektifTersZ(float dikeyAci, float enBoy, float yakin) {
    float fy = 1.0f / std::tan(dikeyAci * 0.5f);
    M4 p;
    for (float& x : p.m) x = 0;
    p(0, 0) = fy / enBoy;
    p(1, 1) = fy;
    p(2, 3) = yakin;
    p(3, 2) = -1.0f;
    return p;
}

// Genel 4×4 ters (kofaktör). Tekilse false.
inline bool Ters(const M4& a, M4& t) {
    const float* m = a.m;
    float inv[16];
    inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
    inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
    inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
    inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
    inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
    inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
    inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
    inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
    inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
    inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
    inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
    inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
    inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
    inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
    inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
    inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];
    float det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
    if (std::fabs(det) < 1e-30f) return false;
    det = 1.0f / det;
    for (int i = 0; i < 16; ++i) t.m[i] = inv[i] * det;
    return true;
}

}  // namespace op4
