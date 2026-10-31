// op4 arayüzü — tema: TEK giriş noktası. Değerlerin kaynağı op4/tasarim/atolye-modern/belirtec.py'dir; oradan üretilen
// tema_belirtec.h (python3 op4/araclar/kimlik_uret.py --tema) dışında renk değeri YAZILMAZ. Bu başlık belirteçleri
// çizim kodunun kullandığı adlara bağlar (RenkleriKur, OlculeriKur; tema.cpp). Yön: "Atölye · Modern" (MIMARI §25.1;
// tasarim.md §3–§10): açık nötr yüzeyler, tek soğuk vurgu (Kobalt varsayılan · Petrol · Grafit; Ayarlar › Görüntü ›
// Vurgu rengi, çalışma anında), bronz / kahve–altın yok. Ölçüler mantıksal pikseldir (96 DPI = 1×); çizim kodu
// S(x) = x · ölçek ile çarpar. ImGui'ye bağlı değildir; renkler ImGui IM_COL32 düzenindedir (0xAABBGGRR).
// YAYIMLANMIŞ BAŞLIK: diğer paketler (ör. D'nin Başlangıç / dosya kartları) kendi kopyalarını tutmaz, bunu içerir:
//   #include "arayuz/tema.h"  →  tema::Etkin().r.<rol> (etkin palet, IM_COL32), tema::Etkin().o.<ölçü>,
//   tema::belirtec::NOTR / PALETLER / ANLAM / MODEL / R / A / GOLGE / Y / OLCU_* (ham 0xRRGGBB ve px değerleri).
#pragma once

#include <cstdint>
#include <string_view>

#include "arayuz/tema_belirtec.h"

namespace op4::tema {

// #RRGGBB → IM_COL32 (A B G R).
constexpr uint32_t Renk(uint32_t rrggbb, float alfa = 1.0f) {
    const uint32_t a = static_cast<uint32_t>(alfa * 255.0f + 0.5f);
    return (a << 24) | ((rrggbb & 0xFF) << 16) | (rrggbb & 0xFF00) | ((rrggbb >> 16) & 0xFF);
}
constexpr uint32_t Alfa(uint32_t renk, float alfa) {
    const uint32_t a = static_cast<uint32_t>(static_cast<float>(renk >> 24) * alfa + 0.5f);
    return (renk & 0x00FFFFFFu) | (a << 24);
}
// İki IM_COL32 rengini t oranında karıştırır (t = 0 → a); alfa da karışır.
uint32_t Karisim(uint32_t a, uint32_t b, float t);

// ---- vurgu paleti ve yoğunluk -------------------------------------------------------------------------------------------
enum class Palet : uint8_t { Kobalt = 0, Petrol = 1, Grafit = 2 };
Palet PaletKodundan(std::string_view kod);  // "kobalt" | "petrol" | "grafit"; bilinmeyen → varsayılan
const char* PaletKodu(Palet p);
const char* PaletAdi(Palet p);               // Türkçe görünen ad (Tr() ile çevrilir)

enum class Yogunluk : uint8_t { Rahat = 0, Siki = 1 };

// ---- renkler (tasarim.md §3) ---------------------------------------------------------------------------------------------
// Alan adları çizim kodunun rolleridir; hepsi RenkleriKur'da belirteçlerden doldurulur.
struct Renkler {
    // nötr yüzeyler
    uint32_t zemin, zemin2, yuzey, yuzey2, sayfa, alan, alanKenar, hover, basili, cizgi, cizgi2;
    uint32_t yuzey3;      // = basili (nötr basılı düğme)
    uint32_t girisKenar;  // = alanKenar (dolgulu giriş)
    uint32_t dugmeKenar;  // = kenar belirteci (ikincil düğme, onay kutusu, tuş rozeti alt kenarı)
    uint32_t anahtarKapali;
    uint32_t metin, metin2, metin3, metin4;
    uint32_t ikonBuyuk, ikonKucuk, ikonKapali;  // simge · simge2 · metin4
    uint32_t golge, karartma, beyaz, antrasit;
    // vurgu ailesi (palet)
    uint32_t vurgu, vurguKoyu, vurguMetin, vurguTon, vurguTon2, vurguUzerinde;
    uint32_t secim, secimTon, secimTon2, seciliDolgu, uzerinde, odak;
    // anlamsal
    uint32_t ok, okTon, uyari, uyariTon, uyariDolgu, hata, hataTon, hataKenar, bilgi, kapatUzerinde;
    uint32_t eksenX, eksenY, eksenZ;
    // görünüm (model)
    uint32_t sahneUst, sahneAlt, sahneIsik;
    uint32_t kolon, kiris, asik, capraz, doseme, temel, digerCubuk, kenar, kenarInce, kenarDoseme;
    uint32_t izgara, izgaraAna;
    // çubuk görünümü (sabit piksel çizgiler; model kenar belirteçlerinden)
    uint32_t cubukKolon, cubukKiris, cubukAsik, cubukCapraz, cubukDiger;
    uint32_t panelDolgu, panelKenar, aksCizgisi, aksBalonKenar, katCizgisi;
    uint32_t dugum, serbestDugum, mesnet;
    uint32_t tutamacBaslangic, tutamacBitis;  // dolu kare / içi boş kare (ikisi de seçim rengi; biçimle ayrışır)
    uint32_t dc[5];
};
Renkler RenkleriKur(Palet p);

// ---- tipografi (tasarim.md §4; belirtec::YAZI_AILESI 400 / 500 / 600) ----------------------------------------------------
enum class Agirlik : uint8_t { Normal = 0, Yari = 1, Orta = 2, Kalin = 3, Cok = 4 };  // 400 · 450 · 500 · 600 · 700
struct Tipografi {
    float sayfa, pencere, baslik, govde, etiket, kucuk, rozet, rayBolum;
};

// ---- ölçüler (tasarim.md §5; belirteç OLCU + bileşen ölçüleri) ------------------------------------------------------------
struct Olculer {
    float baslik, sekme, seritGovde;
    float ray, agac, ozellik, pencereSeridi;
    float gorunumSekme, rihtimSekme, rihtim, komut, durum;
    float panelBaslik, nesneBaslik, altCubuk, segment, arama, satir, ozellikSatiri, alan, bolum;
    float buyukDugme, kucukAdim, rayDugme;
    float etiketSutunu = 104;  // Özellikler etiket sütunu (§6 özellik satırı)
    float girintiDuzey = 16;   // ağaç girintisi (sıkıda 12)
    float buyukDugmeEnAz = 52;
    float yaricapKucuk, yaricap, kartYaricap, pencereYaricap;  // 4 · 6 · 8 · 10
    float pilYaricap;                                        // görünüm pili / düğme grubu (= büyük)
    float ikonKalem = 1.5f, ikonKalemKucuk = 1.3f;
    // yoğunluk eşikleri (pencere istemci alanı; görev çubuğu payıyla 1600×900 ekran)
    float darEsikGenislik = 1600, darEsikYukseklik = 860;
    float tekPanelEsigi = 1280;  // bunun altında model ağacı pencere şeridine döner (§9.8)
    // En küçük istemci alanı (mantıksal px; tasarim.md §9): Sıkı yoğunluk, tek panel, görünüm ≥ %60 ve durum çubuğu
    // öğeleri çakışmadan sığar. Pencere WM_GETMINMAXINFO ile arayüz ölçeğiyle (DPI × yazı boyutu) çarpıp uygular;
    // ekran dışı sınamada daha küçük --boyut olduğu gibi çizilir (günlüğe uyarı).
    float enAzGenislik = 1024, enAzYukseklik = 640;
};
Olculer OlculeriKur(Yogunluk y);

// ---- görünüm (sahne) çizimi ----------------------------------------------------------------------------------------------
struct SahneCizimi {
    float cubukKalinlik = 1.6f, seciliKalinlik = 2.0f, uzerindeKalinlik = 1.0f;  // MIMARI §6.5 + tasarim.md §3.6 (px)
    float haleKalinlik = 5.0f, haleSaydamlik = 0.42f;                            // seçim halesi (5 px, %42)
    float dugumYaricap = 2.2f, serbestDugumYaricap = 3.0f;
    float mesnetBoy = 9.0f;
    float aksBalonYaricap = 8.5f;
    float aksKesik = 7.0f, aksBosluk = 4.0f;
    float mafsalYaricap = 3.0f, mafsalUzaklik = 9.0f;
    float etiketBoy = 11.0f;
    float tutamac = 9.0f;  // tutamaç karesi (px; tasarımda 12 px @ 1,35× önizleme)
};

// Yazı boyutu çarpanı (Ayarlar › Görüntü › Yazı boyutu; S18 arayuz.yazi_boyutu "kucuk" | "orta" | "buyuk"): bütün yazı
// ölçeği ve yazıya bağlı modül ölçüleri aynı oranla büyür; AnaPencere arayüz ölçeğini DPI × çarpan kurar. Bilinmeyen → 1.
inline float YaziCarpani(std::string_view kod) {
    for (const belirtec::YaziBoyutu& b : belirtec::YAZI_BOYUTLARI)
        if (kod == b.kimlik) return b.carpan;
    return 1.0f;
}

struct Tema {
    Renkler r;
    Tipografi y;
    Olculer o;
    SahneCizimi s;
    Palet palet = Palet::Kobalt;
    Yogunluk yogunluk = Yogunluk::Rahat;
};

// Etkin tema. Ayarlar › Görüntü bazı değerleri çalışma anında değiştirir (vurgu rengi, yoğunluk, çizgi kalınlıkları,
// seçim / üzerinde renkleri, etiket boyu, arka plan); AnaPencere::AyarlariUygula PaletUygula / YogunlukUygula çağırır.
Tema& Etkin();
void PaletUygula(Palet p);         // r yeniden kurulur (ImGui stilini çağıran yeniden uygular)
void YogunlukUygula(Yogunluk y);   // o yeniden kurulur

}  // namespace op4::tema
