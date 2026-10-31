// op4 çekirdek — ayarlar JSON dönüşümü (sözleşme S18; tam uygulama, nlohmann/json). Sahibi: D (dosya-cozum); alan
// grupları sahiplerine göre genişletilir (ayarlar.h).
#include "cekirdek/ayarlar.h"

#include <algorithm>
#include <iterator>
#include <type_traits>

#include <nlohmann/json.hpp>

namespace op4 {
namespace {
using nlohmann::json;

template <class T>
void Al(const json& j, const char* ad, T& v) {
    if (!j.is_object() || !j.contains(ad)) return;
    const json& d = j[ad];
    if constexpr (std::is_same_v<T, bool>) {
        if (d.is_boolean()) v = d.get<bool>();
    } else if constexpr (std::is_same_v<T, int>) {
        if (d.is_number_integer()) v = d.get<int>();
    } else if constexpr (std::is_same_v<T, double>) {
        if (d.is_number()) v = d.get<double>();
    } else if constexpr (std::is_same_v<T, std::string>) {
        if (d.is_string()) v = d.get<std::string>();
    } else {
        if (d.is_array()) {
            v.clear();
            for (const json& e : d)
                if (e.is_string()) v.push_back(e.get<std::string>());
        }
    }
}

const char* const kBilinen[] = {"bicim", "grafik", "arayuz", "dosya", "motor", "cekirdek"};

}  // namespace

bool AyarlariOku(std::string_view metin, Ayarlar& a, std::string& hata) {
    a = Ayarlar{};
    const json j = json::parse(metin, nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        hata = "ayarlar.json bozuk; varsayılan ayarlar kullanılıyor.";
        return false;
    }
    Al(j, "bicim", a.bicim);
    if (j.contains("grafik")) {
        const json& g = j["grafik"];
        Al(g, "bagdastirici", a.grafik.bagdastirici);
        Al(g, "msaa", a.grafik.msaa);
        Al(g, "dikey_esitleme", a.grafik.dikeyEsitleme);
        Al(g, "warp_zorla", a.grafik.warpZorla);
        Al(g, "lod_tolerans_px", a.grafik.lodToleransPx);  // C eklentisi (31.10.2026)
        Al(g, "arka_plan", a.grafik.arkaPlan);
        Al(g, "cubuk_kalinlik", a.grafik.cubukKalinlik);
        Al(g, "secili_kalinlik", a.grafik.seciliKalinlik);
        Al(g, "vurguyu_izle", a.grafik.vurguyuIzle);
        Al(g, "secim_rengi", a.grafik.secimRengi);
        Al(g, "uzerinde_rengi", a.grafik.uzerindeRengi);
    }
    if (j.contains("arayuz")) {
        const json& g = j["arayuz"];
        Al(g, "baslangic_paneli", a.arayuz.baslangicPaneli);
        Al(g, "fare_eslemesi", a.arayuz.fareEslemesi);
        Al(g, "yorunge", a.arayuz.yorunge);
        Al(g, "donme_duyarliligi", a.arayuz.donmeDuyarliligi);
        Al(g, "klasik_menu", a.arayuz.klasikMenu);
        Al(g, "tema", a.arayuz.tema);
        Al(g, "acilis", a.arayuz.acilis);  // C eklentisi (31.10.2026)
        Al(g, "acilis_ekrani", a.arayuz.acilisEkrani);
        Al(g, "vurgu", a.arayuz.vurgu);
        Al(g, "yogunluk", a.arayuz.yogunluk);
        Al(g, "etiket_boyu", a.arayuz.etiketBoyu);
        Al(g, "dil", a.arayuz.dil);
        Al(g, "ondalik", a.arayuz.ondalik);
        Al(g, "binlik_ayirici", a.arayuz.binlikAyirici);
        Al(g, "birim_sistemi", a.arayuz.birimSistemi);
        Al(g, "varsayilan_kuvvet", a.arayuz.varsayilanKuvvet);
        Al(g, "varsayilan_uzunluk", a.arayuz.varsayilanUzunluk);
    }
    if (j.contains("dosya")) {
        const json& g = j["dosya"];
        Al(g, "otomatik_kayit", a.dosya.otomatikKayit);
        Al(g, "otomatik_kayit_dk", a.dosya.otomatikKayitDk);
        Al(g, "son_dosya_sayisi", a.dosya.sonDosyaSayisi);
        Al(g, "yedek_bak", a.dosya.yedekBak);
        Al(g, "son_dosyalar", a.dosya.sonDosyalar);
        Al(g, "son_klasor", a.dosya.sonKlasor);
    }
    if (j.contains("motor")) {
        const json& g = j["motor"];
        Al(g, "sd_siniri", a.motor.sdSiniri);
        Al(g, "anlat", a.motor.anlat);
        Al(g, "bellek_yuzde", a.motor.bellekYuzde);
    }
    if (j.contains("cekirdek")) {
        const json& g = j["cekirdek"];
        Al(g, "geri_al_adim", a.cekirdek.geriAlAdim);
        Al(g, "geri_al_mb", a.cekirdek.geriAlMb);
        Al(g, "yalniz_aks_noktalari", a.cekirdek.yalnizAksNoktalari);
    }
    // Sınırlar.
    if (a.grafik.msaa != 0 && a.grafik.msaa != 1 && a.grafik.msaa != 2 && a.grafik.msaa != 4 && a.grafik.msaa != 8)
        a.grafik.msaa = 0;
    a.dosya.otomatikKayitDk = std::clamp(a.dosya.otomatikKayitDk, 1, 30);
    a.dosya.sonDosyaSayisi = std::clamp(a.dosya.sonDosyaSayisi, 0, 30);
    if (a.dosya.sonDosyalar.size() > static_cast<size_t>(a.dosya.sonDosyaSayisi))
        a.dosya.sonDosyalar.resize(static_cast<size_t>(a.dosya.sonDosyaSayisi));
    a.motor.sdSiniri = std::clamp(a.motor.sdSiniri, 100, 200000);
    a.motor.bellekYuzde = std::clamp(a.motor.bellekYuzde, 10, 95);
    a.cekirdek.geriAlAdim = std::clamp(a.cekirdek.geriAlAdim, 1, 1000);
    a.cekirdek.geriAlMb = std::clamp(a.cekirdek.geriAlMb, 16, 8192);
    a.arayuz.donmeDuyarliligi = std::clamp(a.arayuz.donmeDuyarliligi, 0.1, 10.0);
    a.grafik.lodToleransPx = std::clamp(a.grafik.lodToleransPx, 0.25, 4.0);  // C eklentisi
    a.grafik.cubukKalinlik = std::clamp(a.grafik.cubukKalinlik, 0.5, 3.0);
    a.grafik.seciliKalinlik = std::clamp(a.grafik.seciliKalinlik, 1.0, 4.0);
    a.arayuz.etiketBoyu = std::clamp(a.arayuz.etiketBoyu, 9.0, 16.0);
    // Bilinmeyen üst düzey anahtarlar korunur.
    json b = json::object();
    for (auto i = j.begin(); i != j.end(); ++i)
        if (std::find_if(std::begin(kBilinen), std::end(kBilinen), [&](const char* k) { return i.key() == k; }) ==
            std::end(kBilinen))
            b[i.key()] = i.value();
    if (!b.empty()) a.bilinmeyen = b.dump();
    return true;
}

std::string AyarlariYaz(const Ayarlar& a) {
    json j = json::object();
    if (!a.bilinmeyen.empty()) {
        const json b = json::parse(a.bilinmeyen, nullptr, false);
        if (b.is_object()) j = b;
    }
    j["bicim"] = a.bicim;
    j["grafik"] = {{"bagdastirici", a.grafik.bagdastirici}, {"msaa", a.grafik.msaa},
                   {"dikey_esitleme", a.grafik.dikeyEsitleme}, {"warp_zorla", a.grafik.warpZorla},
                   {"lod_tolerans_px", a.grafik.lodToleransPx}, {"arka_plan", a.grafik.arkaPlan},
                   {"cubuk_kalinlik", a.grafik.cubukKalinlik}, {"secili_kalinlik", a.grafik.seciliKalinlik},
                   {"vurguyu_izle", a.grafik.vurguyuIzle}, {"secim_rengi", a.grafik.secimRengi},
                   {"uzerinde_rengi", a.grafik.uzerindeRengi}};
    j["arayuz"] = {{"baslangic_paneli", a.arayuz.baslangicPaneli}, {"fare_eslemesi", a.arayuz.fareEslemesi},
                   {"yorunge", a.arayuz.yorunge}, {"donme_duyarliligi", a.arayuz.donmeDuyarliligi},
                   {"klasik_menu", a.arayuz.klasikMenu}, {"tema", a.arayuz.tema},
                   {"acilis", a.arayuz.acilis}, {"acilis_ekrani", a.arayuz.acilisEkrani},
                   {"vurgu", a.arayuz.vurgu}, {"yogunluk", a.arayuz.yogunluk},
                   {"etiket_boyu", a.arayuz.etiketBoyu}, {"dil", a.arayuz.dil}, {"ondalik", a.arayuz.ondalik},
                   {"binlik_ayirici", a.arayuz.binlikAyirici}, {"birim_sistemi", a.arayuz.birimSistemi},
                   {"varsayilan_kuvvet", a.arayuz.varsayilanKuvvet}, {"varsayilan_uzunluk", a.arayuz.varsayilanUzunluk}};
    j["dosya"] = {{"otomatik_kayit", a.dosya.otomatikKayit}, {"otomatik_kayit_dk", a.dosya.otomatikKayitDk},
                  {"son_dosya_sayisi", a.dosya.sonDosyaSayisi}, {"yedek_bak", a.dosya.yedekBak},
                  {"son_dosyalar", a.dosya.sonDosyalar}, {"son_klasor", a.dosya.sonKlasor}};
    j["motor"] = {{"sd_siniri", a.motor.sdSiniri}, {"anlat", a.motor.anlat}, {"bellek_yuzde", a.motor.bellekYuzde}};
    j["cekirdek"] = {{"geri_al_adim", a.cekirdek.geriAlAdim}, {"geri_al_mb", a.cekirdek.geriAlMb},
                     {"yalniz_aks_noktalari", a.cekirdek.yalnizAksNoktalari}};
    return j.dump(2);
}

}  // namespace op4
