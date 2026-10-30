// op4 çekirdek sözleşmesi — kullanıcı ayarları (%APPDATA%\Opus Fortis\op4\ayarlar.json; MIMARI §18.4;
// "F1 paket sözleşmeleri" §S18).
//
// Tek Ayarlar nesnesi Hizmetler::ayarlar'dır. Kalıcılık (oku / yaz, sürüm yükseltme) D'nindir. Alan grupları
// sahiplerine göre ayrılmıştır; bir paket YALNIZ kendi grubuna alan ekler (ekleme sözleşme değişikliği sayılmaz):
//   grafik → C (Ayarlar › Grafik), arayuz → C, dosya → D, motor → A, cekirdek → B.
// JSON anahtarları alan adlarının snake_case karşılığıdır; bilinmeyen anahtarlar okunurken KORUNUR (ileriye uyum).
#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace op4 {

struct GrafikAyarlari {            // C
    std::string bagdastirici;      // boş = otomatik (yüksek başarım tercihli; MIMARI §6.1); yoksa bağdaştırıcı açıklaması
    int msaa = 0;                  // 0 = otomatik (donanımda 8, WARP'ta 4); 1, 2, 4, 8
    bool dikeyEsitleme = true;     // vsync
    bool warpZorla = false;        // yazılım işleyici (tanı)
};

struct ArayuzAyarlari {            // C
    bool baslangicPaneli = true;   // "Açılışta Başlangıç panelini göster" (MIMARI §5.2)
    std::string fareEslemesi = "op4";  // "op4" | "klasik"  (MIMARI §7.1)
    std::string yorunge = "turntable"; // "turntable" | "trackball"
    double donmeDuyarliligi = 1.0;
    bool klasikMenu = false;       // şerit yerine klasik menü çubuğu
    std::string tema = "koyu";     // "koyu" | "acik"
};

struct DosyaAyarlari {             // D
    bool otomatikKayit = true;
    int otomatikKayitDk = 5;       // 1–30 (MIMARI §13.3)
    int sonDosyaSayisi = 10;
    bool yedekBak = false;         // kaydederken .bak bırak
    std::vector<std::string> sonDosyalar;  // en yeni başta
    std::string sonKlasor;         // dosya penceresinin açılacağı klasör
};

struct MotorAyarlari {             // A
    int sdSiniri = 6000;           // ayarlar.sd_siniri (MIMARI §8.6.4)
    bool anlat = false;            // F5 çözümünde adım adım anlatım (op4 varsayılanı kapalı)
    int bellekYuzde = 60;          // Job Object bellek tavanı (sistem belleğinin yüzdesi)
};

struct CekirdekAyarlari {          // B
    int geriAlAdim = 100;          // MIMARI §9.4
    int geriAlMb = 512;
    bool yalnizAksNoktalari = false;  // katı §19 kipi (proje ayarıdır; burada yeni projelerin varsayılanı)
};

struct Ayarlar {
    int bicim = 1;
    GrafikAyarlari grafik;
    ArayuzAyarlari arayuz;
    DosyaAyarlari dosya;
    MotorAyarlari motor;
    CekirdekAyarlari cekirdek;
    std::string bilinmeyen;        // okunurken tanınmayan üst düzey anahtarlar (JSON nesnesi); yazarken geri eklenir
};

// JSON ↔ Ayarlar. Oku: bozuk JSON'da false + hata ve `a` varsayılanlarda kalır; eksik alanlar varsayılandır; aralık dışı
// değerler sınıra çekilir.
bool AyarlariOku(std::string_view json, Ayarlar& a, std::string& hata);
std::string AyarlariYaz(const Ayarlar& a);

}  // namespace op4
