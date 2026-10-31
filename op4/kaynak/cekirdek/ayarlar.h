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
    // eklenti (C, 31.10.2026; Ayarlar › Görüntü ayarları)
    double lodToleransPx = 0.5;    // görüntü ağı LOD ekran sapması sınırı (MIMARI §6.11), 0,25–4 px
    std::string arkaPlan = "gradyan";  // "gradyan" (dikey, belirteç vp_ust → vp_alt) | "duz"
    double cubukKalinlik = 1.6;    // çubuk görünümü / eleman kenarı çizgi kalınlığı (px), 0,5–3
    double seciliKalinlik = 2.0;   // seçim konturu (px), 1–4
    bool vurguyuIzle = true;       // seçim ve üzerinde renkleri vurgu paletinden; kapalıyken aşağıdaki renkler
    std::string secimRengi = "#2563EB";     // seçim konturu ("#RRGGBB"; vurguyuIzle kapalıyken)
    std::string uzerindeRengi = "#5B8FF2";  // üzerine gelme konturu
};

struct ArayuzAyarlari {            // C
    bool baslangicPaneli = true;   // "Açılışta Başlangıç panelini göster" (MIMARI §5.2)
    std::string fareEslemesi = "op4";  // "op4" | "klasik"  (MIMARI §7.1)
    std::string yorunge = "turntable"; // "turntable" | "trackball"
    double donmeDuyarliligi = 1.0;
    bool klasikMenu = false;       // şerit yerine klasik menü çubuğu
    // KULLANILMIYOR (eski, Faz 0): arayüz açık temadır ("Atölye · Modern", MIMARI §25.1); açılış ekranının zemini
    // acilisEkrani'dır. Alan ve "tema" anahtarı dosya gidiş-dönüşü için okunur / yazılır; değeri hiçbir yerde okunmaz.
    std::string tema = "koyu";     // "koyu" | "acik" (eskimiş)
    // eklenti (C, 31.10.2026; Ayarlar › Program / Görüntü / Dil ayarları)
    std::string acilis = "baslangic";       // açılışta: "baslangic" (Başlangıç paneli) | "son_proje" | "bos"
    std::string acilisEkrani = "acik";      // açılış ekranı: "acik" (Kemer Çizgisi) | "koyu" (ikizi)
    std::string vurgu = "kobalt";           // vurgu rengi: "kobalt" | "petrol" | "grafit" (tasarim/atolye-modern)
    std::string yogunluk = "otomatik";      // "otomatik" (1600×900 altında sıkı) | "rahat" | "siki"
    std::string yaziBoyutu = "orta";        // Ayarlar › Görüntü › Yazı boyutu: "kucuk" | "orta" | "buyuk" (arayüz ölçeği
                                            // çarpanı tema_belirtec.h YAZI_BOYUTLARI; bilinmeyen değer → "orta")
    double etiketBoyu = 11.0;               // görünüm etiketleri (px), 9–16
    std::string dil = "tr";                 // arayüz dili: "tr" | "en"
    std::string ondalik = "virgul";         // sayı biçimi: "virgul" | "nokta"
    bool binlikAyirici = true;              // binlik ayırıcı ince boşluk ("1 842")
    std::string birimSistemi = "SI";        // "SI" (kN, m) | "teknik" (tf, m)
    std::string varsayilanKuvvet = "kN";    // yeni projelerin birimleri: "kN" | "tf"
    std::string varsayilanUzunluk = "m";    // "m" | "cm" | "mm"
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
