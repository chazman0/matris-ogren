// op4 arayüzü — örnek bina (bkz. ornek_bina.h; geometri taslak sahne.py Bina sınıfıyla aynı).
#include "arayuz/ornek_bina.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <map>
#include <memory>
#include <string>

namespace op4 {
namespace {

// Öznitelik tablosu kurucusu (sütun türleri BosOznitelikTablosu ile aynı).
struct TabloKurucu {
    std::shared_ptr<OznitelikTablosu> t = std::make_shared<OznitelikTablosu>();
    std::map<std::string, size_t> sutun;
    TabloKurucu() {
        const OznitelikTablosu& b = *BosOznitelikTablosu();
        t->sutunlar = b.sutunlar;
        for (size_t i = 0; i < t->sutunlar.size(); ++i) {
            sutun[t->sutunlar[i].id] = i;
            if (t->sutunlar[i].id == oznitelik::UZUNLUK || t->sutunlar[i].id == oznitelik::X || t->sutunlar[i].id == oznitelik::Y ||
                t->sutunlar[i].id == oznitelik::Z || t->sutunlar[i].id == oznitelik::KALINLIK)
                t->sutunlar[i].birim = "m";
            if (t->sutunlar[i].id == oznitelik::EGIM || t->sutunlar[i].id == oznitelik::ACI) t->sutunlar[i].birim = "°";
            if (t->sutunlar[i].id == oznitelik::ALAN) t->sutunlar[i].birim = "m²";
        }
    }
    OznitelikSutunu& S(const char* id) { return t->sutunlar[sutun.at(id)]; }
    void Satir(ElemanKimligi k) {
        t->satirlar.push_back(k);
        for (OznitelikSutunu& s : t->sutunlar) {
            switch (s.tur) {
                case OznitelikTuru::Sayi:
                case OznitelikTuru::Bool: s.sayi.push_back(std::nan("")); break;
                case OznitelikTuru::Metin:
                case OznitelikTuru::Enum: s.kod.push_back(OZNITELIK_YOK); break;
                case OznitelikTuru::Liste: s.listeBas.push_back(s.listeBas.back()); break;
            }
        }
    }
    void Metin(const char* id, const std::string& v) {
        OznitelikSutunu& s = S(id);
        uint32_t k = OZNITELIK_YOK;
        for (uint32_t i = 0; i < s.sozluk.size(); ++i)
            if (s.sozluk[i] == v) k = i;
        if (k == OZNITELIK_YOK) {
            s.sozluk.push_back(v);
            k = static_cast<uint32_t>(s.sozluk.size() - 1);
        }
        s.kod.back() = k;
    }
    void Sayi(const char* id, double v) { S(id).sayi.back() = v; }
    void Liste(const char* id, std::initializer_list<double> v) {
        OznitelikSutunu& s = S(id);
        for (const double x : v) s.listeDeger.push_back(x);
        s.listeBas.back() = static_cast<uint32_t>(s.listeDeger.size());
    }
};

}  // namespace

OrnekBina OrnekBinaKur() {
    OrnekBina o;
    auto s = std::make_shared<SahneAnlik>();
    s->surum = 0x0D0;
    s->baslik = "Depo Binası – Tokat OSB";
    s->sistem = "celik";
    const double X[4] = {0, 6, 12, 18}, Y[5] = {0, 6, 12, 18, 24}, Z[4] = {0, 4.5, 9, 13.5};
    const char* XA[4] = {"A", "B", "C", "D"};
    const char* YA[5] = {"1", "2", "3", "4", "5"};
    s->seviyeler = {{"±0.00", 0, 0}, {"+4.50", 4.5, 1}, {"+9.00", 9.0, 2}, {"+13.50", 13.5, 3}};
    s->kesitler = {{"HE340A", "HEA 340", KesitTuru::I, "S355", 0.330, 0.300, 0.0095, 0.0165, 0.027},
                   {"IPE400", "IPE 400", KesitTuru::I, "S355", 0.400, 0.180, 0.0086, 0.0135, 0.021},
                   {"IPE200", "IPE 200", KesitTuru::I, "S355", 0.200, 0.100, 0.0056, 0.0085, 0.012},
                   {"L100x10", "L 100x10", KesitTuru::L, "S355", 0.100, 0.100, 0.010, 0.010, 0.012}};
    s->malzemeler = {"S355", "C30"};
    s->gruplar = {"Kolonlar", "Ana kirişler", "Aşıklar", "Çaprazlar"};
    TabloKurucu t;
    auto dno = [](int i, int j, int k) { return static_cast<uint32_t>(1000 * k + 20 * i + j + 1); };
    std::map<uint32_t, uint32_t> dizin;
    auto dugum = [&](uint32_t no, V3d p, DugumTuru tur) {
        if (dizin.count(no)) return dizin[no];
        SahneDugumu d;
        d.no = no;
        d.p = p;
        d.tur = tur;
        dizin[no] = static_cast<uint32_t>(s->dugumler.size());
        s->dugumler.push_back(d);
        return dizin[no];
    };
    for (int k = 0; k < 4; ++k)
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 5; ++j) dugum(dno(i, j, k), {X[i], Y[j], Z[k]}, DugumTuru::AksKat);
    // akslar
    for (int i = 0; i < 4; ++i) {
        SahneAksi a;
        a.kimlik = {ElemanTuru::Aks, 0, static_cast<uint32_t>(i)};
        a.ad = XA[i];
        a.sistem = "GLOBAL";
        a.eksen = 0;
        a.bas = {X[i], Y[0] - 2.0, 0};
        a.son = {X[i], Y[4] + 2.0, 0};
        a.balon = {X[i], Y[0] - 2.6, 0};
        s->akslar.push_back(a);
    }
    for (int j = 0; j < 5; ++j) {
        SahneAksi a;
        a.kimlik = {ElemanTuru::Aks, 0, 65536u + static_cast<uint32_t>(j)};
        a.ad = YA[j];
        a.sistem = "GLOBAL";
        a.eksen = 1;
        a.bas = {X[0] - 2.0, Y[j], 0};
        a.son = {X[3] + 2.0, Y[j], 0};
        a.balon = {X[0] - 2.6, Y[j], 0};
        s->akslar.push_back(a);
    }
    uint32_t cno = 1;
    auto cubuk = [&](uint32_t i, uint32_t j, CubukTuru tur, uint32_t kesit, const std::string& ad, const char* altTur,
                     const char* yer, int kat, bool mafsal) {
        SahneCubugu c;
        c.no = cno++;
        c.i = i;
        c.j = j;
        c.tur = tur;
        c.kesit = kesit;
        c.grup = tur == CubukTuru::Kolon ? 0 : tur == CubukTuru::Kiris ? 1 : tur == CubukTuru::Asik ? 2 : 3;
        if (mafsal) c.serbestlik = SerbestlikBiti(false, 4) | SerbestlikBiti(false, 5) | SerbestlikBiti(true, 4) | SerbestlikBiti(true, 5);
        const V3d a = s->dugumler[i].p, b = s->dugumler[j].p, d = b - a;
        const double L = Uzunluk(d);
        const V3d x = Birim(d);
        const double D = std::hypot(x.x, x.y);
        c.yYerel = D > 1e-9 ? V3d{-x.x * x.z / D, -x.y * x.z / D, D} : V3d{x.z > 0 ? -1.0 : 1.0, 0, 0};
        s->cubuklar.push_back(c);
        const ElemanKimligi k = CubukKimligi(c.no);
        t.Satir(k);
        t.Metin(oznitelik::TUR, "cubuk");
        t.Sayi(oznitelik::NO, c.no);
        t.Metin(oznitelik::AD, ad);
        t.Metin(oznitelik::ALT_TUR, altTur);
        if (yer && *yer) t.Metin(oznitelik::KULLANIM_YERI, yer);
        t.Liste(oznitelik::KAT, {static_cast<double>(kat)});
        t.Metin(oznitelik::SEVIYE, s->seviyeler[static_cast<size_t>(kat)].ad);
        t.Metin(oznitelik::KESIT, s->kesitler[kesit].ad);
        t.Metin(oznitelik::PROFIL, s->kesitler[kesit].profil);
        t.Metin(oznitelik::MALZEME, "S355");
        t.Metin(oznitelik::SISTEM, "celik");
        t.Metin(oznitelik::GRUP, s->gruplar[c.grup]);
        t.Sayi(oznitelik::UZUNLUK, L);
        t.Sayi(oznitelik::EGIM, std::atan2(std::fabs(d.z), std::hypot(d.x, d.y)) * 180.0 / 3.14159265358979);
        t.Sayi(oznitelik::ACI, 0);
        if (mafsal) {
            t.Metin(oznitelik::SERBEST_I, "My,Mz");
            t.Metin(oznitelik::SERBEST_J, "My,Mz");
        }
        t.Sayi(oznitelik::SERBEST_DUGUM, 0);
        t.Sayi(oznitelik::X, (a.x + b.x) / 2);
        t.Sayi(oznitelik::Y, (a.y + b.y) / 2);
        t.Sayi(oznitelik::Z, (a.z + b.z) / 2);
        return k;
    };
    char ad[32];
    // kolonlar (kat kat)
    int n = 0;
    for (int k = 0; k < 3; ++k)
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 5; ++j) {
                const bool kose = (i == 0 || i == 3) && (j == 0 || j == 4), kenar = i == 0 || i == 3 || j == 0 || j == 4;
                std::snprintf(ad, sizeof(ad), "C%d-%02d", k + 1, ++n);
                const ElemanKimligi c = cubuk(dizin[dno(i, j, k)], dizin[dno(i, j, k + 1)], CubukTuru::Kolon, 0, ad, "kolon",
                                              kose ? "kose" : (kenar ? "kenar" : "ic"), k + 1, false);
                if (k == 1 && i == 2 && j == 0) o.taslakUzerinde = c;
            }
    // ana kirişler (x yönü, sonra y yönü), aşıklar
    for (int k = 1; k <= 3; ++k) {
        n = 0;
        for (int j = 0; j < 5; ++j)
            for (int i = 0; i < 3; ++i) {
                std::snprintf(ad, sizeof(ad), "K%d-%02d", k, ++n);
                const ElemanKimligi c = cubuk(dizin[dno(i, j, k)], dizin[dno(i + 1, j, k)], CubukTuru::Kiris, 1, ad, "kiris",
                                              j == 0 || j == 4 ? "dis" : "ic", k, true);
                if (k == 2 && (j == 0 || j == 1)) o.taslakSecimi.push_back(c);
            }
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 4; ++j) {
                std::snprintf(ad, sizeof(ad), "K%d-%02d", k, ++n);
                // aşığın bağlandığı açıklık ortası bölme düğümü
                const uint32_t orta = dugum(dno(i, j, k) + 500, {X[i], (Y[j] + Y[j + 1]) / 2, Z[k]}, DugumTuru::Bolme);
                const ElemanKimligi c1 = cubuk(dizin[dno(i, j, k)], orta, CubukTuru::Kiris, 1, ad, "kiris", i == 0 || i == 3 ? "dis" : "ic", k, true);
                (void)c1;
                std::snprintf(ad, sizeof(ad), "K%d-%02db", k, n);
                cubuk(orta, dizin[dno(i, j + 1, k)], CubukTuru::Kiris, 1, ad, "kiris", i == 0 || i == 3 ? "dis" : "ic", k, true);
            }
        int a = 0;
        for (int j = 0; j < 4; ++j)
            for (int i = 0; i < 3; ++i) {
                std::snprintf(ad, sizeof(ad), "A%d-%02d", k, ++a);
                cubuk(dizin[dno(i, j, k) + 500], dizin[dno(i + 1, j, k) + 500], CubukTuru::Asik, 2, ad, "asik", "ic", k, true);
            }
    }
    // çaprazlar: A ve D aksları (1–2, 4–5 açıklıkları), 1 ve 5 aksları (B–C açıklığı) — X çapraz
    n = 0;
    for (int k = 0; k < 3; ++k) {
        for (const int i : {0, 3})
            for (const int j : {0, 3}) {
                std::snprintf(ad, sizeof(ad), "Ç%d-%02d", k + 1, ++n);
                cubuk(dizin[dno(i, j, k)], dizin[dno(i, j + 1, k + 1)], CubukTuru::Capraz, 3, ad, "capraz", "dis-cephe", k + 1, true);
                std::snprintf(ad, sizeof(ad), "Ç%d-%02d", k + 1, ++n);
                cubuk(dizin[dno(i, j + 1, k)], dizin[dno(i, j, k + 1)], CubukTuru::Capraz, 3, ad, "capraz", "dis-cephe", k + 1, true);
            }
        for (const int j : {0, 4}) {
            std::snprintf(ad, sizeof(ad), "Ç%d-%02d", k + 1, ++n);
            cubuk(dizin[dno(1, j, k)], dizin[dno(2, j, k + 1)], CubukTuru::Capraz, 3, ad, "capraz", "dis-cephe", k + 1, true);
            std::snprintf(ad, sizeof(ad), "Ç%d-%02d", k + 1, ++n);
            cubuk(dizin[dno(2, j, k)], dizin[dno(1, j, k + 1)], CubukTuru::Capraz, 3, ad, "capraz", "dis-cephe", k + 1, true);
        }
    }
    // döşemeler (açıklık başına panel)
    uint32_t pno = 1;
    for (int k = 1; k <= 3; ++k)
        for (int j = 0; j < 4; ++j)
            for (int i = 0; i < 3; ++i) {
                SahnePaneli p;
                p.no = pno++;
                p.koseBas = static_cast<uint32_t>(s->panelKoseleri.size());
                for (const uint32_t d : {dizin[dno(i, j, k)], dizin[dno(i + 1, j, k)], dizin[dno(i + 1, j + 1, k)], dizin[dno(i, j + 1, k)]})
                    s->panelKoseleri.push_back(d);
                p.koseSayisi = 4;
                p.tur = PanelTuru::Doseme;
                p.kalinlik = 0.14;
                s->paneller.push_back(p);
                t.Satir(PanelKimligi(p.no));
                t.Metin(oznitelik::TUR, "panel");
                t.Sayi(oznitelik::NO, p.no);
                std::snprintf(ad, sizeof(ad), "D%d-%02d", k, static_cast<int>(j * 3 + i + 1));
                t.Metin(oznitelik::AD, ad);
                t.Metin(oznitelik::ALT_TUR, "doseme");
                t.Metin(oznitelik::KULLANIM_YERI, i == 1 && (j == 1 || j == 2) ? "ic" : "kenar");
                t.Liste(oznitelik::KAT, {static_cast<double>(k)});
                t.Metin(oznitelik::MALZEME, "C30");
                t.Sayi(oznitelik::KALINLIK, 0.14);
                t.Sayi(oznitelik::ALAN, 36.0);
                t.Sayi(oznitelik::X, (X[i] + X[i + 1]) / 2);
                t.Sayi(oznitelik::Y, (Y[j] + Y[j + 1]) / 2);
                t.Sayi(oznitelik::Z, Z[k]);
            }
    // mesnetler (zemin düğümleri, ankastre) ve düğüm satırları
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 5; ++j) {
            s->mesnetler.push_back({dizin[dno(i, j, 0)], 0x3F, MesnetTuru::Ankastre});
            s->dugumler[dizin[dno(i, j, 0)]].bayrak |= dugum_bayragi::MESNETLI;
        }
    for (const SahneDugumu& d : s->dugumler) {
        t.Satir(DugumKimligi(d.no));
        t.Metin(oznitelik::TUR, "dugum");
        t.Sayi(oznitelik::NO, d.no);
        t.Metin(oznitelik::ALT_TUR, "dugum");
        const int kat = static_cast<int>(std::lround(d.p.z / 4.5));
        t.Metin(oznitelik::KULLANIM_YERI, kat == 0 ? "temel" : (d.tur == DugumTuru::Bolme ? "ara" : "kolon-ustu"));
        t.Liste(oznitelik::KAT, {static_cast<double>(kat)});
        t.Sayi(oznitelik::X, d.p.x);
        t.Sayi(oznitelik::Y, d.p.y);
        t.Sayi(oznitelik::Z, d.p.z);
    }
    s->DizinleriKur();
    t.t->sahneSurumu = s->surum;
    t.t->DizinleriKur();
    o.sahne = s;
    o.oznitelik = t.t;
    std::sort(o.taslakSecimi.begin(), o.taslakSecimi.end());
    return o;
}

}  // namespace op4
