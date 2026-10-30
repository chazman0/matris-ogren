// op4 çekirdek sözleşmesi — sahne anlığı: model çekirdeğinin ürettiği, çizicinin ve seçme dizininin tükettiği değişmez
// sahne verisi (MIMARI §4, §9.3 "SAHNE içeriği"; "F1 paket sözleşmeleri" §S4).
//
// Üreten : B (model-cekirdegi) — op4_cekirdek.js sahne() → tipli diziler → bu yapı (kaynak/cekirdek_js/).
// Tüketen: C (arayuz-goruntu) — çubuk görünümü çizimi, BVH (SecmeDizini), model gezgini; D — onizleme.png küçük resmi.
//
// Kurallar:
//  * Anlık DEĞİŞMEZDİR ve std::shared_ptr<const SahneAnlik> (SahnePtr) olarak paylaşılır; iş havuzu (BVH, LOD) onu
//    kilitsiz okuyabilir. Model her değiştiğinde çekirdek YENİ bir anlık üretir ve `surum` artar (sahne_surumu).
//  * Dizinler (SahneCubugu::i, j; panel köşeleri; mesnet düğümü) aynı anlığın `dugumler` dizisine göre 0 tabanlıdır.
//    Kalıcı başvuru için dizin değil `no` (ElemanKimligi) kullanılır.
//  * Koordinatlar dünya sistemindedir (m, double): X sağa, Y derinlik, Z yukarı. Çapaya göreli float'a çevirme çizicinin
//    işidir (MIMARI §6.2).
//  * Kod tabloları (CubukTuru, PanelTuru, …) op4/veri/sahne_kodlari.json ile aynıdır; JS (op4_ops.KODLAR) ve C++ aynı
//    dosyaya karşı sınanır (op4/testler/js/sozlesme.test.js, op4/testler/cekirdek/sozlesme_kodlar.cpp). Değerler
//    değiştirilmez, yalnız eklenir.
//  * Surum 1 (aks–kat) modeller çekirdekte `genellestir` görünümüyle sahneye çevrilir; kimlikler genel görünümdekilerdir.
#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "cekirdek/kimlik.h"
#include "cekirdek/vektor.h"

namespace op4 {

inline constexpr uint32_t SAHNE_YOK = 0xFFFFFFFFu;  // "dizin yok" (kesit atanmamış, grup yok …)

// Çubuk alt türü (bina JSON cubuk.tur; bina.js CUBUK_TURLERI). Renk paleti bu türe göredir (MIMARI §6.5).
enum class CubukTuru : uint8_t {
    Diger = 0, Kolon = 1, Kiris = 2, Capraz = 3, MakasUst = 4, MakasAlt = 5, MakasDikme = 6, MakasDiyagonal = 7,
    Asik = 8, Kren = 9, Bag = 10,
};
// Panel türü (bina JSON panel.tur; bina.js PANEL_TURLERI).
enum class PanelTuru : uint8_t { Doseme = 0, Cati = 1, Cephe = 2, Diger = 3 };
// Düğümün nasıl tanımlandığı (MIMARI §10.1 REF öncelik sırası). Serbest düğüm rozetle gösterilir.
enum class DugumTuru : uint8_t { AksKat = 0, AksKesisimi = 1, Bolme = 2, Kesisim = 3, Serbest = 4 };
// Kesit ailesi (MIMARI §6.6). Faz 1 çubuk görünümünde yalnız ad ve aile kullanılır; ölçüler Faz 2'de (kesitCoz) dolar.
enum class KesitTuru : uint8_t {
    Bilinmiyor = 0, I = 1, Kutu = 2, Boru = 3, Dikdortgen = 4, Daire = 5, L = 6, CiftL = 7, Upn = 8,
};
// Mesnet ön ayarı (bina_cizim.js MESNET_ON_AYAR); maske asıl bilgidir, tür yalnız simge seçimi içindir.
enum class MesnetTuru : uint8_t { Diger = 0, Ankastre = 1, Mafsal = 2, Kayici = 3, Yay = 4 };
enum class TemelTuru : uint8_t { Tekil = 0, Surekli = 1, Radye = 2 };

// Bayraklar (bit maskeleri; sahne_kodlari.json "*_bayraklari").
namespace cubuk_bayragi {
inline constexpr uint8_t YALNIZ_CEKME = 1u << 0;
inline constexpr uint8_t SERBEST_DUGUME_BAGLI = 1u << 1;  // uçlarından biri Serbest düğüm
inline constexpr uint8_t VUTE = 1u << 2;
inline constexpr uint8_t URETECTEN = 1u << 3;             // bir üretecin (makas, çapraz …) parçası
}  // namespace cubuk_bayragi
namespace dugum_bayragi {
inline constexpr uint8_t MESNETLI = 1u << 0;
inline constexpr uint8_t BAGLANTISIZ = 1u << 1;  // hiçbir çubuk / panel kullanmıyor
}  // namespace dugum_bayragi
namespace panel_bayragi {
inline constexpr uint8_t DUZLEMSEL_DEGIL = 1u << 0;
}  // namespace panel_bayragi

// Çubuk uç serbestlik maskesi (12 bit): bit = serbest bırakılan iç kuvvet. i ucu: N=0, Vy=1, Vz=2, T=3, My=4, Mz=5;
// j ucu: aynı sıra +6. Ör. iki ucu mafsallı kiriş: My, Mz her iki uçta → 0b110000'110000.
inline constexpr uint16_t SerbestlikBiti(bool jUcu, int kuvvet /*0..5*/) {
    return static_cast<uint16_t>(1u << ((jUcu ? 6 : 0) + kuvvet));
}

struct SahneSeviyesi {      // akslar.z
    std::string ad;         // "±0.00", "+3.20", "Saçak" …
    double z = 0;
    int kat = -1;           // kat işaretliyse katlar[].no; değilse -1
};

struct SahneAksi {
    ElemanKimligi kimlik;   // tür Aks (bkz. kimlik.h)
    std::string ad;         // "A", "1", "Mahya" …
    std::string sistem;     // aks sistemi adı; genel akslar için "GLOBAL"
    uint8_t eksen = 0;      // 0 x, 1 y, 2 z
    V3d bas, son;           // çizilecek doğru parçası (dünya)
    V3d balon;              // balon (ad dairesi) konumu
};

struct SahneDugumu {
    uint32_t no = 0;
    V3d p;
    DugumTuru tur = DugumTuru::Serbest;
    uint8_t bayrak = 0;     // dugum_bayragi
};

struct SahneCubugu {
    uint32_t no = 0;
    uint32_t i = 0, j = 0;            // dugumler dizinleri
    CubukTuru tur = CubukTuru::Diger;
    uint8_t bayrak = 0;               // cubuk_bayragi
    uint16_t serbestlik = 0;          // 12 bit (SerbestlikBiti)
    uint32_t kesit = SAHNE_YOK;       // kesitler dizini
    uint32_t grup = SAHNE_YOK;        // gruplar dizini
    uint32_t uretec = 0;              // üreteç no (0 = yok)
    double aci = 0;                   // derece; x′ çevresinde (model_ops.js yerel eksen kuralı)
    V3d yYerel;                       // y′ (aci uygulanmış) birim vektörü; kesit yönelimi için
};

struct SahnePaneli {
    uint32_t no = 0;
    uint32_t koseBas = 0, koseSayisi = 0;  // SahneAnlik::panelKoseleri[koseBas … koseBas+koseSayisi) → dugumler dizinleri
    PanelTuru tur = PanelTuru::Doseme;
    uint8_t bayrak = 0;                    // panel_bayragi
    double kalinlik = 0;                   // m; 0 = sac / kaplama
};

struct SahneMesnedi {
    uint32_t dugum = 0;       // dugumler dizini
    uint8_t maske = 0;        // 6 bit, bit = tutulu: ux=0, uy=1, uz=2, rx=3, ry=4, rz=5
    MesnetTuru tur = MesnetTuru::Diger;
};

struct SahneTemeli {
    ElemanKimligi kimlik;     // tür Temel
    uint32_t dugum = SAHNE_YOK;
    TemelTuru tur = TemelTuru::Tekil;
    double B = 0, L = 0, h = 0;  // m (tekil); şerit / radyede çekirdek doldurmayabilir
};

struct SahneKesiti {
    std::string ad;           // bina JSON kesitler anahtarı (ör. "KOLON", "HEA 340")
    std::string profil;       // normalleştirilmiş kütüphane adı (profilAdiNormal) ya da boş
    KesitTuru tur = KesitTuru::Bilinmiyor;
    std::string malzeme;      // "S275", "C30" …
    double h = 0, b = 0, tw = 0, tf = 0, r = 0;  // m; bilinmeyen 0 (Faz 2: kesitCoz tam kaydı)
};

struct SahneAnlik {
    uint64_t surum = 0;          // sahne_surumu; aynı modelden üretilen iki anlıkta eşittir
    int modelSurumu = 3;         // bina JSON "surum": 1 aks–kat, 3 genel
    std::string baslik;          // model başlığı ("Adsız 1" …)
    std::string sistem;          // "celik" | "betonarme" | "karma"

    std::vector<SahneSeviyesi> seviyeler;   // z'ye göre artan
    std::vector<SahneAksi> akslar;
    std::vector<SahneDugumu> dugumler;
    std::vector<SahneCubugu> cubuklar;
    std::vector<SahnePaneli> paneller;
    std::vector<uint32_t> panelKoseleri;
    std::vector<SahneMesnedi> mesnetler;
    std::vector<SahneTemeli> temeller;
    std::vector<SahneKesiti> kesitler;
    std::vector<std::string> gruplar;
    std::vector<std::string> malzemeler;

    Kutu3d sinir;                // düğümler + aks uçları (DizinleriKur doldurur)

    // Üretici dizileri doldurduktan sonra BİR KEZ çağırır: no → dizin eşlemlerini ve sınır kutusunu kurar.
    void DizinleriKur();
    std::optional<size_t> DugumDizini(uint32_t no) const;
    std::optional<size_t> CubukDizini(uint32_t no) const;
    std::optional<size_t> PanelDizini(uint32_t no) const;
    // Kimliğin sahnede bir karşılığı var mı (Cubuk, Panel, Dugum, Mesnet, Aks, Temel)?
    bool Var(ElemanKimligi k) const;
    // Elemanın sınır kutusu (çubuk: iki uç; panel: köşeler; düğüm/mesnet: nokta). Bulunamazsa boş kutu.
    Kutu3d Sinir(ElemanKimligi k) const;
    // Eleman sayıları (gezgin, durum çubuğu).
    size_t ElemanSayisi() const { return dugumler.size() + cubuklar.size() + paneller.size(); }

private:
    std::unordered_map<uint32_t, uint32_t> dugumDizini_, cubukDizini_, panelDizini_;
};

using SahnePtr = std::shared_ptr<const SahneAnlik>;

// Boş sahne (sürüm 0): çekirdek hazır olmadan önce çizicinin ve BVH'nin kullandığı geçerli, boş anlık.
SahnePtr BosSahne();

// Sınama düzeneği: Faz 0 iskeletinin örnek yapısı (iki çerçeve; HE340A kolon ve kirişler, IPE300 bağ kirişleri, 6 × 5 m,
// 3,5 m kat; akslar A–B, 1–2) sahne anlığı olarak. B'nin çekirdeği bağlanana dek C ve D bununla geliştirir; testler sabit sayıları
// denetler: 8 düğüm, 8 çubuk (4 kolon + 2 kiriş + 2 bağ), 0 panel, 4 mesnet, 2 seviye.
SahnePtr OrnekSahneAnlik();

}  // namespace op4
