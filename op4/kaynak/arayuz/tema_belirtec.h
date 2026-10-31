// op4 — arayüz belirteçleri. ÜRETİLMİŞ DOSYA: python3 op4/araclar/kimlik_uret.py --tema
// Kaynak: op4/tasarim/atolye-modern/belirtec.py (Atölye · Modern, MIMARI §25.1). Elle düzenlenmez; renkler
// 0xRRGGBB, ölçüler 1× mantıksal pikseldir. Kullanım: tema.h / tema.cpp (tema::RenkleriKur, tema::OlculeriKur).
#pragma once

#include <cstdint>

namespace op4::tema::belirtec {

// Nötr yüzeyler (üç palette ortak)
struct Notr {
    uint32_t zemin, zemin2, yuzey, yuzey2, sayfa, alan, alan_kenar, hover;
    uint32_t basili, cizgi, cizgi2, kenar, metin, metin2, metin3, metin4;
    uint32_t simge, simge2, golge, karartma, beyaz;
};
inline constexpr Notr NOTR = {0xF3F4F6, 0xE9ECEF, 0xFFFFFF, 0xF8F9FA, 0xF5F6F8, 0xF3F4F6, 0xE3E6EA, 0xF0F2F4,
    0xE7EAEE, 0xE1E4E8, 0xECEEF1, 0xCDD2D8, 0x14181B, 0x4A515A, 0x646B75, 0xA0A6AE, 0x353B43, 0x59606A, 0x0F172A,
    0x0F172A, 0xFFFFFF};

// Vurgu paleti (bronz / kahve–altın yok); rol tanımları belirtec.py başında
struct PaletRenk {
    uint32_t vurgu, vurgu_koyu, vurgu_metin, vurgu_ton, vurgu_ton2, secim, secim_ton, secim_ton2;
    uint32_t secim_dolgu, hover_model, odak;
};
struct Palet {
    const char* kimlik;  // ayar değeri ("kobalt" | "petrol" | "grafit")
    const char* ad;      // görünen ad (Türkçe; Tr() ile çevrilir)
    PaletRenk r;
};
inline constexpr int PALET_SAYISI = 3;
inline constexpr Palet PALETLER[PALET_SAYISI] = {
    {"kobalt", "Kobalt mavisi", {0x2563EB, 0x1D4ED8, 0x1D4ED8, 0xEEF3FE, 0xCFDDFC, 0x2563EB, 0xEAF1FE, 0xC9DAFC,
    0xC9DBFB, 0x5B8FF2, 0x2563EB}},
    {"petrol", "Petrol yeşili", {0x0F766E, 0x115E59, 0x0F6B64, 0xE8F4F2, 0xBFE0DB, 0x0F766E, 0xE6F3F1, 0xBCDDD8,
    0xBFE3DD, 0x3E9C93, 0x0F766E}},
    {"grafit", "Grafit (tek renk)", {0x262B31, 0x111418, 0x262B31, 0xEBEDF0, 0xD3D8DE, 0x2F6FDB, 0xECF2FD, 0xC9DBF8,
    0xCCDDF8, 0x6E9BE6, 0x2F6FDB}},
};
inline constexpr int VARSAYILAN_PALET = 0;  // kobalt

// Anlamsal renkler (vurgudan bağımsız)
struct Anlam {
    uint32_t ok, ok_ton, uyari, uyari_ton, uyari_dolgu, hata, hata_ton, hata_kenar;
    uint32_t bilgi, eksen_x, eksen_y, eksen_z;
};
inline constexpr Anlam ANLAM = {0x1E7B4C, 0xE8F5EE, 0xA15C07, 0xFEF3DC, 0xE9A23B, 0xC0362C, 0xFCEBEA, 0xF2C4C0,
    0x2E6AB3, 0xC0362C, 0x1E7B4C, 0x2E6AB3};

// Model (3B görünüm) nötr nesne renkleri ve arka plan
struct Model {
    uint32_t vp_ust, vp_alt, vp_isik, kolon, kiris, tali, asik, capraz;
    uint32_t doseme, temel, kenar, kenar_ince, kenar_doseme, izgara, izgara_ana, aks;
};
inline constexpr Model MODEL = {0xFBFCFD, 0xE4E8EC, 0xFFFFFF, 0xCBD0D7, 0xD3D7DD, 0xD9DDE2, 0xD9DDE2, 0xC4C9D0,
    0xE3E5E8, 0xD6D8DB, 0x454B53, 0x5A616A, 0x8E939A, 0xB7BCC4, 0x9AA0A8, 0x7E858F};

// D/C ölçeği (5 eşik)
inline constexpr uint32_t DC_RENK[5] = {0x2E6AB3, 0x2BA37B, 0xF3D84C, 0xDD6A1C, 0xA61B2E};
inline constexpr float DC_ESIK[4] = {0.5f, 0.7f, 0.9f, 1.0f};

// Yarıçaplar (px)
struct Yaricap {
    float kucuk, orta, buyuk, pencere, hap;
};
inline constexpr Yaricap R = {4.0f, 6.0f, 8.0f, 10.0f, 999.0f};
// Aralık (8 px ızgara, 4 px yarım adım)
struct Aralik {
    float a1, a2, a3, a4, a5, a6;
};
inline constexpr Aralik A = {4.0f, 8.0f, 12.0f, 16.0f, 24.0f, 32.0f};
struct Golge {
    float bulaniklik, dy, saydamlik;
};
// Gölgeler (bulanıklık yarıçapı, dy, saydamlık)
struct Golgeler {
    Golge panel, kabarik, yuzen, acilir, kipli;
};
inline constexpr Golgeler GOLGE = {{6.0f, 0.0f, 0.06f}, {2.0f, 1.0f, 0.1f}, {8.0f, 2.0f, 0.1f}, {14.0f, 6.0f, 0.14f},
    {28.0f, 12.0f, 0.24f}};
struct YaziRolu {
    float boy;
    int agirlik;  // 400 · 500 · 600
};
// Yazı ölçeği (Inter; boyut px @1×, ağırlık)
struct YaziOlcegi {
    YaziRolu sayfa, pencere, baslik, govde, govde_orta, govde_kalin;
    YaziRolu etiket, etiket_ince, kucuk, rozet, bolum;
};
inline constexpr YaziOlcegi Y = {{20.0f, 600}, {15.0f, 600}, {13.0f, 600}, {12.0f, 400}, {12.0f, 500}, {12.0f, 600},
    {11.0f, 500}, {11.0f, 400}, {10.0f, 500}, {9.0f, 600}, {9.0f, 600}};

// Modül ölçüleri; "rahat" ≥ 1600×900, "siki" daha küçük ekranda
struct Olcu {
    float baslik, sekme, serit, ray, agac, ozel, pencere_seridi, gsekme;
    float rihtim_sekme, rihtim, komut, durum, panel_baslik, nesne, panel_alt, segment;
    float arama, satir_agac, satir_ozel, alan_h, bolum, buyuk_dugme, kucuk_satir, ray_dugme;
};
inline constexpr Olcu OLCU_RAHAT = {32.0f, 32.0f, 88.0f, 40.0f, 272.0f, 320.0f, 32.0f, 32.0f, 32.0f, 48.0f, 32.0f,
    28.0f, 40.0f, 48.0f, 48.0f, 28.0f, 28.0f, 24.0f, 24.0f, 20.0f, 28.0f, 64.0f, 20.0f, 32.0f};
inline constexpr Olcu OLCU_SIKI = {28.0f, 28.0f, 76.0f, 36.0f, 232.0f, 288.0f, 28.0f, 28.0f, 28.0f, 40.0f, 28.0f,
    26.0f, 36.0f, 48.0f, 44.0f, 24.0f, 24.0f, 22.0f, 22.0f, 20.0f, 24.0f, 56.0f, 18.0f, 28.0f};

}  // namespace op4::tema::belirtec
