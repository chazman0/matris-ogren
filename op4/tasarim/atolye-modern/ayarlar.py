#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atölye · Modern — Ayarlar penceresi (kipli, karartılmış program üstünde).
Sol: arama + kategori listesi (Program / Görüntü / Dil; etkin kategorinin alt bölümleri kaydırma izleyicili).
Sağ: sayfa başlığı + iki sütunlu kartlar. Alt: Varsayılana dön ▾ · değişiklik sayısı · İptal / Uygula / Tamam.
Pencere 1440×960 (1920×1080 ekranda ortalı), kart yarıçapı 6, satır 40 (açıklamalı 52), denetim yüksekliği 28.
"""
import os
from PIL import Image

from belirtec import C, R, PALETLER, rgba, karisim, ustundeki_metin
from tuval import Tuval, taban

KIMLIK = "/home/user/matris-ogren/op4/kimlik"
PW, PH = 1440, 960          # pencere
BAS_H, ALT_H, NAV_W = 56, 64, 256
DH = 28                     # denetim yüksekliği

KATEGORILER = [
    ("program", "disli", "Program ayarları", ["Başlangıç", "Kayıt ve kurtarma", "Geri al", "Varsayılan birimler", "Klasörler", "Hesap motoru", "Kısayollar"]),
    ("goruntu", "ekran", "Görüntü ayarları", ["Grafik", "Model görünümü", "Seçim ve üzerinde", "Arayüz"]),
    ("dil", "dil", "Dil ayarları", ["Arayüz dili", "Sayı ve tarih", "Birim sistemi", "Komut takma adları"]),
]


# ----------------------------------------------------------------------------
# Yardımcılar
# ----------------------------------------------------------------------------
def kart(t, x, y, w, h, baslik, simge, sag=None):
    t.golge(x, y, w, h, r=R["orta"], tur="kabarik", alfa=0.05)
    t.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["cizgi"], r=R["orta"])
    t.simge(simge, x + 24, y + 20, 16, C["simge2"], 1.5)
    t.yazi(x + 40, taban(y, 40, 13), baslik, 13, 600, C["metin"])
    t.yatay(x + 1, x + w - 1, y + 40, C["cizgi2"])
    return y + 41


def satir(t, x, y, w, h, etiket, aciklama=None, degisti=False, ayrac=True, etiket_agirlik=500):
    """Ayar satırı: solda etiket (+ açıklama), sağda denetim. Denetimin sağ kenarını ve dikey merkezini döndürür."""
    if ayrac:
        t.yatay(x + 16, x + w - 16, y, C["cizgi2"])
    if degisti:
        t.daire(x + 9, y + (h / 2 if not aciklama else h / 2 - 8), 3, dolgu=C["vurgu"])
    if aciklama:
        t.yazi(x + 16, y + h / 2 - 3, etiket, 12, etiket_agirlik, C["metin"])
        t.yazi(x + 16, y + h / 2 + 13, aciklama, 11, 400, C["metin3"])
    else:
        t.yazi(x + 16, taban(y, h, 12), etiket, 12, etiket_agirlik, C["metin"])
    return x + w - 16, y + h / 2


def varsayilan_notu(t, xr, cy, metin):
    t.yazi_sag(xr, taban(cy - 10, 20, 11), metin, 11, 400, C["metin3"])
    return xr - t.yazi_gen(metin, 11, 400) - 10


def segment_sag(t, xr, cy, secenekler, secili, h=DH, boyut=11):
    """Sağa hizalı segmentli denetim (parçalar metne göre genişler)."""
    gen = sum(t.yazi_gen(s, boyut, 600) + 20 for s in secenekler) + 4
    t.segmentli(xr - gen, cy - h / 2, secenekler, secili, h=h, boyut=boyut, ic=10)
    return xr - gen


def tablo_basligi(t, x, y, w, sutunlar):
    t.dikdortgen(x, y, w, 28, dolgu=C["yuzey2"])
    t.yatay(x, x + w, y, C["cizgi2"]); t.yatay(x, x + w, y + 27, C["cizgi2"])
    for ad, sx, hiza in sutunlar:
        if hiza == "sag":
            t.yazi_sag(sx, taban(y, 28, 11), ad, 11, 600, C["metin2"])
        else:
            t.yazi(sx, taban(y, 28, 11), ad, 11, 600, C["metin2"])
    return y + 28


# ----------------------------------------------------------------------------
# PENCERE ÇERÇEVESİ
# ----------------------------------------------------------------------------
def pencere(t, x0, y0, sayfa, degisiklik):
    t.golge(x0, y0, PW, PH, r=R["pencere"], tur="kipli")
    t.dikdortgen(x0 - 1, y0 - 1, PW + 2, PH + 2, dolgu=rgba(C["golge"], 0.10), r=R["pencere"] + 1)
    t.dikdortgen(x0, y0, PW, PH, dolgu=C["sayfa"], r=R["pencere"])
    # başlık
    t.dikdortgen(x0, y0, PW, BAS_H, dolgu=C["yuzey"], r=R["pencere"])
    t.dikdortgen(x0, y0 + BAS_H - R["pencere"], PW, R["pencere"], dolgu=C["yuzey"])
    t.yatay(x0, x0 + PW, y0 + BAS_H - 1, C["cizgi"])
    t.dikdortgen(x0 + 16, y0 + 12, 32, 32, dolgu=C["vurgu_ton"], r=R["orta"])
    t.simge("disli", x0 + 32, y0 + 28, 18, C["vurgu"], 1.5)
    t.yazi(x0 + 60, taban(y0, BAS_H, 15), "Ayarlar", 15, 600, C["metin"])
    t.yazi(x0 + 60 + t.yazi_gen("Ayarlar", 15, 600) + 12, taban(y0, BAS_H, 11), "Kullanıcı ayarları · op4 0.1.0 · Ctrl+,", 11, 400, C["metin3"])
    t.simge("kapat", x0 + PW - 28, y0 + BAS_H / 2, 16, C["simge2"], 1.5)
    # sol gezinti
    nx, ny, nh = x0, y0 + BAS_H, PH - BAS_H - ALT_H
    t.dikdortgen(nx, ny, NAV_W, nh, dolgu=C["yuzey2"])
    t.dikey(nx + NAV_W - 1, ny, ny + nh, C["cizgi"])
    t.giris(nx + 16, ny + 16, NAV_W - 32, 32, "Ayarlarda ara", 12, renk=C["metin3"], simge="ara")
    t.kisayol_dizisi(nx + NAV_W - 24, ny + 23, "Ctrl+F", 10, 18, sag=True)
    y = ny + 64
    for anah, simge, ad, alt in KATEGORILER:
        etkin = anah == sayfa
        if etkin:
            t.dikdortgen(nx + 8, y, NAV_W - 16, 36, dolgu=C["vurgu_ton"], r=R["orta"])
        t.simge(simge, nx + 28, y + 18, 16, C["vurgu"] if etkin else C["simge2"], 1.5)
        t.yazi(nx + 44, taban(y, 36, 13), ad, 13, 600, C["vurgu_metin"] if etkin else C["metin"])
        t.sevron(nx + NAV_W - 24, y + 18, "asagi" if etkin else "sag", 10, C["vurgu_metin"] if etkin else C["metin3"])
        y += 40
        if etkin:
            gy0 = y
            for i, a in enumerate(alt):
                if i == 0:
                    t.yazi(nx + 48, taban(y, 30, 12), a, 12, 600, C["metin"])
                else:
                    t.yazi(nx + 48, taban(y, 30, 12), a, 12, 400, C["metin2"])
                y += 30
            t.dikey(nx + 33, gy0 + 4, y - 4, C["cizgi"])
            t.dikdortgen(nx + 32, gy0 + 6, 3, 18, dolgu=C["vurgu"], r=1.5)
            y += 8
    # gezinti altı: ayar dosyası
    fy = ny + nh - 72
    t.yatay(nx + 16, nx + NAV_W - 16, fy, C["cizgi"])
    t.simge("klasor", nx + 24, fy + 24, 14, C["simge2"], 1.4)
    t.yazi(nx + 38, taban(fy + 14, 20, 11), "ayarlar.json", 11, 500, C["metin2"])
    t.yazi(nx + 16, taban(fy + 38, 20, 11), "İçe aktar", 11, 500, C["vurgu_metin"])
    t.yazi(nx + 16 + t.yazi_gen("İçe aktar", 11, 500) + 8, taban(fy + 38, 20, 11), "·", 11, 500, C["metin3"])
    t.yazi(nx + 16 + t.yazi_gen("İçe aktar · ", 11, 500) + 4, taban(fy + 38, 20, 11), "Dışa aktar", 11, 500, C["vurgu_metin"])
    # alt çubuk
    ay = y0 + PH - ALT_H
    t.dikdortgen(x0, ay, PW, ALT_H, dolgu=C["yuzey"], r=R["pencere"])
    t.dikdortgen(x0, ay, PW, R["pencere"], dolgu=C["yuzey"])
    t.yatay(x0, x0 + PW, ay, C["cizgi"])
    bh = 32
    by = ay + (ALT_H - bh) / 2
    vw = t.yazi_gen("Varsayılana dön", 12, 500) + 64
    t.dugme(x0 + 16, by, vw, bh, "Varsayılana dön", "ikincil", simge="sifirla")
    t.dikey(x0 + 16 + vw - 26, by + 7, by + bh - 7, C["cizgi"])
    t.sevron(x0 + 16 + vw - 13, by + bh / 2 + 0.5, "asagi", 10, C["metin2"])
    t.yazi(x0 + 16 + vw + 16, taban(by, bh, 11), "Bu sayfa ya da tüm ayarlar", 11, 400, C["metin3"])
    xr = x0 + PW - 16
    xr -= 96
    t.dugme(xr, by, 96, bh, "Tamam", "birincil")
    xr -= 8 + 88
    t.dugme(xr, by, 88, bh, "Uygula", "ikincil", devre_disi=(degisiklik == 0))
    xr -= 8 + 88
    t.dugme(xr, by, 88, bh, "İptal", "ikincil")
    xr -= 16
    if degisiklik:
        et = f"{degisiklik} değişiklik · Uygula pencereyi açık tutar"
        t.yazi_sag(xr, taban(by, bh, 11), et, 11, 400, C["metin2"])
        t.daire(xr - t.yazi_gen(et, 11, 400) - 10, by + bh / 2, 3, dolgu=C["vurgu"])
    else:
        t.yazi_sag(xr, taban(by, bh, 11), "Değişiklik yok", 11, 400, C["metin3"])
    # içerik alanı
    return x0 + NAV_W, y0 + BAS_H, PW - NAV_W, PH - BAS_H - ALT_H


def sayfa_basligi(t, x, y, w, baslik, aciklama):
    t.yazi(x + 32, y + 38, baslik, 20, 600, C["metin"])
    t.yazi(x + 32, y + 60, aciklama, 12, 400, C["metin3"])


# ----------------------------------------------------------------------------
# PROGRAM AYARLARI
# ----------------------------------------------------------------------------
def sayfa_program(t, x, y, w, h):
    sayfa_basligi(t, x, y, w, "Program ayarları", "Başlangıç, kayıt ve kurtarma, geri al, varsayılan birimler, klasörler, hesap motoru ve kısayollar")
    cw = (w - 64 - 24) / 2
    lx, rx = x + 32, x + 32 + cw + 24
    yy = y + 80
    # --- Başlangıç
    ky = kart(t, lx, yy, cw, 41 + 3 * 40 + 40, "Başlangıç", "ev")
    secenekler = [("Başlangıç paneli", "Boş model ve sağda şablonlar, son dosyalar, hızlı aks sihirbazı", True),
                  ("Son projeyi aç", "Depo Binası – Tokat OSB.op4 · dün 17:42", False),
                  ("Boş çalışma alanı", "Adsız 1 · Başlangıç paneli kapalı", False)]
    for i, (ad, ac, sec) in enumerate(secenekler):
        ry = ky + i * 40
        if i:
            t.yatay(lx + 44, lx + cw - 16, ry, C["cizgi2"])
        t.radyo(lx + 26, ry + 20, sec, 7)
        t.yazi(lx + 44, ry + 17, ad, 12, 500, C["metin"])
        t.yazi(lx + 44, ry + 32, ac, 11, 400, C["metin3"])
        if sec:
            t.cip(lx + cw - 16 - (t.yazi_gen("Varsayılan", 10, 500) + 16), ry + 10, "Varsayılan", 20, "notr", 10, agirlik=500)
    ry = ky + 3 * 40
    xr, cy = satir(t, lx, ry, cw, 40, "Son dosyalar listesi")
    t.adimlayici(xr - 120, cy - DH / 2, 120, DH, "10", 12, "öğe")
    yy += 41 + 3 * 40 + 40 + 16
    # --- Kayıt ve kurtarma
    ky = kart(t, lx, yy, cw, 41 + 4 * 44, "Kayıt ve kurtarma", "kurtarma")
    xr, cy = satir(t, lx, ky, cw, 44, "Otomatik kayıt", "Açık projeyi arka planda kaydeder", ayrac=False)
    t.anahtar(xr - 28, cy - 8, True)
    xr, cy = satir(t, lx, ky + 44, cw, 44, "Kayıt aralığı")
    segment_sag(t, xr, cy, ["2 dk", "5 dk", "10 dk", "15 dk"], 1)
    xr, cy = satir(t, lx, ky + 88, cw, 44, "Kurtarma dosyaları", "%LOCALAPPDATA%\\op4\\Kurtarma")
    t.acilir(xr - 168, cy - DH / 2, 168, DH, "7 gün sakla", 12)
    xr, cy = satir(t, lx, ky + 132, cw, 44, "Kaydederken yedek al", "Önceki sürüm .op4.bak olarak saklanır")
    t.anahtar(xr - 28, cy - 8, True)
    yy += 41 + 4 * 44 + 16
    # --- Geri al
    ky = kart(t, lx, yy, cw, 41 + 2 * 44, "Geri al", "geri_al")
    xr, cy = satir(t, lx, ky, cw, 44, "Geri al derinliği", "Bellekte ≈ 1,2 MB / adım", degisti=True, ayrac=False)
    t.adimlayici(xr - 132, cy - DH / 2, 132, DH, "200", 12, "adım")
    varsayilan_notu(t, xr - 132 - 12, cy, "Varsayılan: 100")
    xr, cy = satir(t, lx, ky + 44, cw, 44, "Görünüm değişikliklerini geçmişe ekle", "Döndür, yakınlaştır, kesit düzlemi")
    t.anahtar(xr - 28, cy - 8, False)
    yy += 41 + 2 * 44 + 16
    # --- Varsayılan birimler
    ky = kart(t, lx, yy, cw, y + h - 24 - yy, "Varsayılan birimler", "olcu")
    birimler = [("Kuvvet", "kN", 76), ("Uzunluk", "m", 68), ("Kesit", "mm", 72), ("Gerilme", "MPa", 84), ("Sıcaklık", "°C", 68), ("Açı", "derece", 0)]
    sabit = sum(b[2] for b in birimler)
    cx_ = lx + 16
    for i, (ad, deger, gw) in enumerate(birimler):
        gw = gw or (cw - 32 - sabit - 5 * 8)
        t.yazi(cx_, ky + 22, ad, 11, 500, C["metin2"])
        t.acilir(cx_, ky + 30, gw, DH, deger, 12)
        cx_ += gw + 8
    t.simge("bilgi", lx + 23, ky + 30 + DH + 18, 13, C["metin3"], 1.4)
    t.yazi(lx + 36, ky + 30 + DH + 22, "Yeni projelerde geçerli; açık projenin birimi durum çubuğundan değişir.", 11, 400, C["metin3"])

    # --- sağ sütun: Klasörler
    yy = y + 80
    ky = kart(t, rx, yy, cw, 41 + 2 * 44, "Klasörler", "klasor")
    for i, (ad, yol) in enumerate((("Şablon klasörü", "%USERPROFILE%\\Belgeler\\op4\\Şablonlar"),
                                   ("Proje klasörü", "%USERPROFILE%\\Belgeler\\op4\\Projeler"))):
        xr, cy = satir(t, rx, ky + i * 44, cw, 44, ad, ayrac=bool(i))
        t.dugme(xr - 84, cy - DH / 2, 84, DH, "Gözat…", "ikincil", boyut=12)
        t.giris(xr - 84 - 8 - 268, cy - DH / 2, 268, DH, yol, 11, simge="klasor")
    yy += 41 + 2 * 44 + 16
    # --- Hesap motoru
    ky = kart(t, rx, yy, cw, 41 + 4 * 44, "Hesap motoru", "islemci")
    xr, cy = satir(t, rx, ky, cw, 44, "İş parçacığı sayısı", "Mantıksal çekirdek: 16", ayrac=False)
    t.acilir(xr - 168, cy - DH / 2, 168, DH, "Otomatik (15)", 12)
    xr, cy = satir(t, rx, ky + 44, cw, 44, "Bellek sınırı", "Sistem belleği 32 GB · varsayılan %50")
    t.yazi_sag(xr, taban(cy - 10, 20, 12), "16 GB", 12, 600, C["metin"], tnum=True)
    t.kaydirici(xr - 48 - 180, cy - 10, 180, 0.47)
    xr, cy = satir(t, rx, ky + 88, cw, 44, "Zaman aşımı", "Süre dolunca durdurmadan önce sorulur")
    t.adimlayici(xr - 120, cy - DH / 2, 120, DH, "30", 12, "dk")
    xr, cy = satir(t, rx, ky + 132, cw, 44, "Arka planda çöz", "Çözüm sürerken arayüz kilitlenmez")
    t.anahtar(xr - 28, cy - 8, True)
    yy += 41 + 4 * 44 + 16
    # --- Kısayollar
    kh = y + h - 24 - yy
    ky = kart(t, rx, yy, cw, kh, "Kısayollar", "klavye")
    t.acilir(rx + cw - 16 - 176, yy + 8, 176, 24, "Profil: op4 varsayılan", 11)
    sy = ky + 12
    t.giris(rx + 16, sy, cw - 32 - 120, DH, "Komut ya da tuş ara (ör. F5, kopyala)", 12, renk=C["metin3"], simge="ara")
    t.dugme(rx + cw - 16 - 112, sy, 112, DH, "Kısayol ekle", "ikincil", boyut=12, simge="artı")
    ty = sy + DH + 12
    c1, c2, c3 = rx + 16, rx + 16 + 236, rx + cw - 16
    ty = tablo_basligi(t, rx + 1, ty, cw - 2, [("Komut", c1, "sol"), ("Kısayol", c2, "sol"), ("Bağlam", c3, "sag")])
    kisayollar = [("Hızlı başlat · komut satırı", "Ctrl+Q", "Genel"), ("Çöz", "F5", "Genel"),
                  ("Seç ve Süz", "Ctrl+Shift+F", "Model"), ("Seçimi tersine çevir", "Ctrl+K", "Model"),
                  ("Tam görünüm", None, "Görünüm"),
                  ("Seçiliye yakınlaş", "Shift+Space", "Görünüm"), ("Kat kapsamı: Bu / Benzer / Tüm", "Alt+1  2  3", "Model"),
                  ("Ayarlar", "Ctrl+,", "Genel")]
    rh = 28
    gosterilen = 0
    for i, (ad, tus, bag) in enumerate(kisayollar):
        ry = ty + i * rh
        if ry + rh > yy + kh - 36:
            break
        gosterilen += 1
        if tus is None:   # düzenlenen satır: tuş yakalama alanı
            t.dikdortgen(rx + 4, ry + 1, cw - 8, rh - 2, dolgu=C["vurgu_ton"], r=R["kucuk"])
            t.yazi(c1, taban(ry, rh, 12), ad, 12, 500, C["metin"])
            fx, fw = c2, 168
            t.odak_halkasi(fx, ry + 3, fw, rh - 6, R["orta"], 2, 0.30)
            t.dikdortgen(fx, ry + 3, fw, rh - 6, dolgu=C["yuzey"], kenar=C["odak"], r=R["orta"])
            t.simge("klavye", fx + 14, ry + rh / 2, 13, C["odak"], 1.4)
            t.yazi(fx + 26, taban(ry + 3, rh - 6, 11), "Tuşlara basın…  (Home)", 11, 400, C["metin3"])
            t.yazi_sag(c3, taban(ry, rh, 11), bag, 11, 400, C["metin2"])
            continue
        t.yatay(rx + 16, rx + cw - 16, ry + rh - 1, C["cizgi2"])
        t.yazi(c1, taban(ry, rh, 12), ad, 12, 400, C["metin"])
        if "  " in tus:
            xx = c2
            for parca in tus.split("  "):
                xx += t.kisayol_dizisi(xx, ry + 5, parca, 10, 18) + 4
        else:
            t.kisayol_dizisi(c2, ry + 5, tus, 10, 18)
        t.yazi_sag(c3, taban(ry, rh, 11), bag, 11, 400, C["metin3"])
    fy = yy + kh - 36
    t.yatay(rx + 1, rx + cw - 1, fy, C["cizgi2"])
    gost = f"{gosterilen} / 142 komut · çakışma yok"
    t.yazi(rx + 16, taban(fy, 36, 11), gost, 11, 400, C["metin3"])
    t.simge("onay", rx + 16 + t.yazi_gen(gost, 11, 400) + 10, fy + 18, 12, C["ok"], 1.8)
    t.yazi_sag(rx + cw - 16, taban(fy, 36, 11), "Profili dışa aktar…", 11, 500, C["vurgu_metin"])
    return 1


# ----------------------------------------------------------------------------
# GÖRÜNTÜ AYARLARI
# ----------------------------------------------------------------------------
def acilis_kucuk(ad):
    im = Image.open(os.path.join(KIMLIK, ad, "kare-100.png")).convert("RGBA")
    return im


def sayfa_goruntu(t, x, y, w, h):
    sayfa_basligi(t, x, y, w, "Görüntü ayarları", "Grafik bağdaştırıcısı, kenar yumuşatma, model görünümü, seçim renkleri, arayüz ölçeği ve açılış ekranı")
    cw = (w - 64 - 24) / 2
    lx, rx = x + 32, x + 32 + cw + 24
    yy = y + 80
    # --- Grafik
    ky = kart(t, lx, yy, cw, 41 + 4 * 44, "Grafik", "ekran")
    xr, cy = satir(t, lx, ky, cw, 44, "Grafik bağdaştırıcısı", "DirectX 12 · özellik düzeyi 12_1 · 12 GB", ayrac=False)
    t.acilir(xr - 236, cy - DH / 2, 236, DH, "Otomatik — yüksek performanslı", 12)
    xr, cy = satir(t, lx, ky + 44, cw, 44, "Kenar yumuşatma (MSAA)")
    segment_sag(t, xr, cy, ["Kapalı", "2×", "4×", "8×"], 2)
    xr, cy = satir(t, lx, ky + 88, cw, 44, "Görüntü kalitesi", "Profil ayrıntısı, eğri bölme, gölge")
    segment_sag(t, xr, cy, ["Taslak", "Dengeli", "Yüksek"], 1)
    xr, cy = satir(t, lx, ky + 132, cw, 44, "Ağ toleransı", "Analiz ağı eniyilemesi: en kaba uygun ağ")
    segment_sag(t, xr, cy, ["±%1", "±%2", "±%5"], 1)
    yy += 41 + 4 * 44 + 16
    # --- Model görünümü
    ky = kart(t, lx, yy, cw, y + h - 24 - yy, "Model görünümü", "bina3")
    xr, cy = satir(t, lx, ky, cw, 44, "Arka plan", "Dikey gradyan · üst / alt", ayrac=False)
    t.dikdortgen(xr - 56, cy - 14, 56, 28, dolgu=C["cizgi"], r=R["orta"])
    t.gradyan(xr - 55, cy - 13, 54, 26, C["vp_ust"], C["vp_alt"])
    t.cerceve(xr - 56, cy - 14, 56, 28, C["kenar"], 1, R["orta"])
    t.renk_ornegi(xr - 56 - 12 - 20, cy - 10, C["vp_alt"], 20)
    t.renk_ornegi(xr - 56 - 12 - 48, cy - 10, C["vp_ust"], 20)
    segment_sag(t, xr - 56 - 12 - 48 - 16, cy, ["Gradyan", "Düz"], 0)
    ry = ky + 44
    t.yatay(lx + 16, lx + cw - 16, ry, C["cizgi2"])
    t.yazi_aralikli(lx + 16, ry + 18, "ÇİZGİ KALINLIKLARI", 9, 600, C["metin3"], 0.6)
    ry += 24
    for ad, oran, deger, degisti, vars_ in (("Eleman kenarı", 0.25, "1,0 px", False, None), ("Aks çizgisi", 0.25, "1,0 px", False, None),
                                            ("Seçim konturu", 0.70, "2,5 px", True, "Varsayılan: 2,0")):
        xr, cy = satir(t, lx, ry, cw, 36, ad, degisti=degisti, ayrac=False, etiket_agirlik=400)
        t.yazi_sag(xr, taban(cy - 10, 20, 12), deger, 12, 600 if degisti else 500, C["metin"], tnum=True)
        t.kaydirici(xr - 56 - 160, cy - 10, 160, oran)
        if vars_:
            varsayilan_notu(t, xr - 56 - 160 - 16, cy, vars_)
        ry += 36
    xr, cy = satir(t, lx, ry + 4, cw, 44, "Etiket boyutu", "Aks balonu, kat ve ölçü etiketleri")
    segment_sag(t, xr, cy, ["Küçük", "Orta", "Büyük"], 1)
    xr, cy = satir(t, lx, ry + 48, cw, 44, "Eksen balonları", "Aks adları model kenarında")
    t.anahtar(xr - 28, cy - 8, True)
    t.acilir(xr - 28 - 16 - 132, cy - DH / 2, 132, DH, "Konum: Baş", 12)
    xr, cy = satir(t, lx, ry + 92, cw, 44, "Kat düzlemleri", "Seviye çizgisi ve etiket; etkin kat vurgulu")
    t.anahtar(xr - 28, cy - 8, True)
    t.acilir(xr - 28 - 16 - 132, cy - DH / 2, 132, DH, "Dolgu: %6", 12)
    xr, cy = satir(t, lx, ry + 136, cw, 44, "Yer gölgesi ve ortam ışığı", "Model altında yumuşak gölge")
    t.anahtar(xr - 28, cy - 8, True)
    xr, cy = satir(t, lx, ry + 180, cw, 44, "Çalışma ızgarası", "1 m aralık · uzaklıkla solar")
    t.anahtar(xr - 28, cy - 8, True)
    t.acilir(xr - 28 - 16 - 132, cy - DH / 2, 132, DH, "Aralık: 1,00 m", 12)

    # --- sağ: Seçim ve üzerinde
    yy = y + 80
    pv_h = 112
    ky = kart(t, rx, yy, cw, 41 + pv_h + 16 + 3 * 44, "Seçim ve üzerinde", "sec")
    # önizleme
    px, py, pw = rx + 16, ky + 16, cw - 32
    t.dikdortgen(px, py, pw, pv_h, dolgu=C["vp_alt"], r=R["orta"])
    t.gradyan(px + 1, py + 1, pw - 2, pv_h - 2, C["vp_ust"], C["vp_alt"])
    t.cerceve(px, py, pw, pv_h, C["cizgi"], 1, R["orta"])

    def kiris_ciz(x0, y0, L, durum):
        if durum == "secili":
            t.dikdortgen(x0 - 6, y0 - 6, L + 12, 32, dolgu=rgba(C["secim"], 0.12), r=8)
        renk = C["secim_dolgu"] if durum == "secili" else C["kiris"]
        kenar = C["secim"] if durum == "secili" else (C["hover_model"] if durum == "hover" else C["kenar"])
        t.dikdortgen(x0, y0, L, 5, dolgu=karisim(renk, "#FFFFFF", 0.25))
        t.dikdortgen(x0, y0 + 5, L, 10, dolgu=karisim(renk, "#000000", 0.06))
        t.dikdortgen(x0, y0 + 15, L, 5, dolgu=karisim(renk, "#000000", 0.20))
        t.yatay(x0, x0 + L, y0 + 5, rgba(kenar, 0.55)); t.yatay(x0, x0 + L, y0 + 14, rgba(kenar, 0.55))
        t.cerceve(x0, y0, L, 20, kenar, 2 if durum == "secili" else 1, 0)
    kiris_ciz(px + 40, py + 32, 180, "secili")
    kiris_ciz(px + 40, py + 84, 180, "hover")
    kiris_ciz(px + 280, py + 32, 180, "")
    kiris_ciz(px + 280, py + 84, 180, "")
    for (hx, dolu) in ((px + 40, True), (px + 220, False)):
        if dolu:
            t.dikdortgen(hx - 5, py + 42 - 5, 10, 10, dolgu=C["yuzey"], r=2); t.dikdortgen(hx - 3, py + 42 - 3, 6, 6, dolgu=C["secim"], r=1)
        else:
            t.dikdortgen(hx - 5, py + 42 - 5, 10, 10, dolgu=C["secim"], r=2); t.dikdortgen(hx - 2.5, py + 42 - 2.5, 5, 5, dolgu=C["yuzey"], r=1)
    t.cip(px + 40, py + 8, "Seçili · 2 px kontur + hale", 18, "secim", 10)
    t.cip(px + 40, py + 62, "Üzerinde · 1 px", 18, "kapali", 10)
    t.cip(px + 280, py + 8, "Normal", 18, "notr", 10, agirlik=500)
    ry = ky + pv_h + 16
    xr, cy = satir(t, rx, ry, cw, 44, "Vurgu rengini izle", "Seçim rengi arayüz vurgusuyla aynı kalır", ayrac=False)
    t.anahtar(xr - 28, cy - 8, True)
    xr, cy = satir(t, rx, ry + 44, cw, 44, "Seçim · üzerinde rengi", "İzleme açıkken salt okunur")
    for i, (renk, et) in enumerate(((C["secim"], C["secim"].upper()), (C["hover_model"], C["hover_model"].upper()))):
        bx = xr - (1 - i) * 0 - (1 - i) * 124 - 112
        t.dikdortgen(bx, cy - 14, 112, 28, dolgu=C["yuzey"], kenar=C["cizgi2"], r=R["orta"])
        t.dikdortgen(bx + 6, cy - 8, 16, 16, dolgu=renk, r=R["kucuk"])
        t.yazi(bx + 30, taban(cy - 14, 28, 11), et, 11, 500, C["metin3"], tnum=True)
    xr, cy = satir(t, rx, ry + 88, cw, 44, "Yalnız seçiliyi göster (Ctrl+5)", "Seçili olmayan nesneler")
    segment_sag(t, xr, cy, ["%60 saydam", "%85 saydam", "Gizle"], 1)
    yy += 41 + pv_h + 16 + 3 * 44 + 16
    # --- Arayüz
    kh = y + h - 24 - yy
    ky = kart(t, rx, yy, cw, kh, "Arayüz", "olcek")
    xr, cy = satir(t, rx, ky, cw, 44, "Vurgu rengi", "Anlamsal renkler (D/C, uyarı) değişmez", ayrac=False)
    xx = xr
    for ad in ("grafit", "petrol", "kobalt"):
        p = PALETLER[ad]
        et = {"kobalt": "Kobalt", "petrol": "Petrol", "grafit": "Grafit"}[ad]
        bw = t.yazi_gen(et, 12, 500) + 40
        xx -= bw
        sec = ad == C["palet"]
        if sec:
            t.odak_halkasi(xx, cy - 14, bw, 28, R["orta"], 2, 0.0)
            t.dikdortgen(xx, cy - 14, bw, 28, dolgu=C["vurgu_ton"], kenar=C["vurgu"], r=R["orta"], kalinlik=1)
        else:
            t.dikdortgen(xx, cy - 14, bw, 28, dolgu=C["yuzey"], kenar=C["kenar"], r=R["orta"])
        t.daire(xx + 15, cy, 6, dolgu=p["vurgu"])
        if ad == "grafit":
            t.daire(xx + 15, cy, 6, dolgu=p["vurgu"])
            t.daire(xx + 19, cy + 4, 3, dolgu=p["secim"])
        t.yazi(xx + 28, taban(cy - 14, 28, 12), et, 12, 600 if sec else 500, C["vurgu_metin"] if sec else C["metin"])
        xx -= 8
    xr, cy = satir(t, rx, ky + 44, cw, 44, "Arayüz ölçeği", "Sistem: %125 · 120 DPI · yazı atlası yeniden kurulur")
    t.acilir(xr - 188, cy - DH / 2, 188, DH, "Sistemi izle (%125)", 12)
    xr, cy = satir(t, rx, ky + 88, cw, 44, "Yoğunluk", "Sıkı: 1600 × 900 altında")
    segment_sag(t, xr, cy, ["Rahat", "Sıkı", "Otomatik"], 2)
    xr, cy = satir(t, rx, ky + 132, cw, 44, "Hareketi azalt", "Panel ve açılır pencere geçişleri anında")
    t.anahtar(xr - 28, cy - 8, False)
    ry = ky + 176
    t.yatay(rx + 16, rx + cw - 16, ry, C["cizgi2"])
    t.yazi(rx + 16, ry + 30, "Açılış ekranı", 12, 500, C["metin"])
    t.yazi(rx + 16, ry + 46, "Logo ve canlandırma", 11, 400, C["metin3"])
    t.yazi(rx + 16, ry + 61, "aynı; yalnız zemin", 11, 400, C["metin3"])
    tw_, th_ = 176, 99
    for i, (ad, et, sec) in enumerate((("acilis", "Açık · varsayılan", True), ("acilis-koyu", "Koyu", False))):
        bx = rx + cw - 16 - (2 - i) * (tw_ + 16) + 16
        by = ry + 16
        if sec:
            t.cerceve(bx - 3, by - 3, tw_ + 6, th_ + 6, C["vurgu"], 2, R["orta"] + 3)
        im = acilis_kucuk(ad)
        t.resim(im, bx, by, w=tw_, h=th_)
        t.cerceve(bx, by, tw_, th_, rgba(C["golge"], 0.14), 1, R["kucuk"])
        t.radyo(bx + 8, by + th_ + 18, sec, 6)
        t.yazi(bx + 20, taban(by + th_ + 8, 20, 11), et, 11, 600 if sec else 500, C["metin"])
        t.simge("gunes" if i == 0 else "ay", bx + tw_ - 8, by + th_ + 18, 13, C["simge2"], 1.4)
    return 1


# ----------------------------------------------------------------------------
# DİL AYARLARI
# ----------------------------------------------------------------------------
ONIZLEME = {
    "tr": dict(sekmeler=["Dosya", "Model", "Düzenle", "Yükler", "Analiz"], baslik="Özellikler",
               satirlar=[("Kesit", "IPE400"), ("Malzeme", "S355"), ("Başlangıç ucu", "Mafsal"), ("Uzunluk", "5,670 m")],
               durum="Kat kapsamı: Benzer katlar", komut="Komut: kiriş"),
    "en": dict(sekmeler=["File", "Model", "Edit", "Loads", "Analysis"], baslik="Properties",
               satirlar=[("Section", "IPE400"), ("Material", "S355"), ("Start release", "Pinned"), ("Length", "5.670 m")],
               durum="Story scope: Similar stories", komut="Command: beam"),
}


def mini_onizleme(t, x, y, w, h, dil, secili):
    t.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["vurgu"] if secili else C["cizgi"], r=R["orta"], kalinlik=1)
    d = ONIZLEME[dil]
    # sekme satırı
    t.dikdortgen(x + 1, y + 1, w - 2, 24, dolgu=C["zemin"], r=R["orta"] - 1)
    t.dikdortgen(x + 1, y + 13, w - 2, 12, dolgu=C["zemin"])
    xx = x + 8
    for i, s in enumerate(d["sekmeler"]):
        if i == 0:
            sw = t.yazi_gen(s, 10, 600) + 12
            t.dikdortgen(xx, y + 5, sw, 16, dolgu=C["vurgu"], r=R["kucuk"])
            t.yazi_orta(xx + sw / 2, taban(y + 5, 16, 10), s, 10, 600, ustundeki_metin(C["vurgu"]))
            xx += sw + 8
        else:
            t.yazi(xx, taban(y + 1, 24, 10), s, 10, 600 if i == 1 else 500, C["metin"] if i == 1 else C["metin2"])
            if i == 1:
                t.dikdortgen(xx - 2, y + 22, t.yazi_gen(s, 10, 600) + 4, 2, dolgu=C["vurgu"], r=1)
            xx += t.yazi_gen(s, 10, 500) + 10
    t.yatay(x + 1, x + w - 1, y + 25, C["cizgi"])
    yy = y + 34
    t.yazi(x + 10, yy + 8, d["baslik"], 11, 600, C["metin"])
    yy += 18
    for et, dg in d["satirlar"]:
        t.yazi(x + 10, taban(yy, 20, 10), et, 10, 400, C["metin2"])
        t.dikdortgen(x + 104, yy + 2, w - 114, 16, dolgu=C["alan"], kenar=C["alan_kenar"], r=R["kucuk"])
        t.yazi(x + 110, taban(yy + 2, 16, 10), dg, 10, 400, C["metin"], tnum=True)
        yy += 20
    yy += 6
    t.yatay(x + 1, x + w - 1, yy, C["cizgi2"])
    t.yazi(x + 10, taban(yy, 22, 10), d["komut"], 10, 600, C["vurgu_metin"])
    t.dikdortgen(x + 1, y + h - 22, w - 2, 21, dolgu=C["zemin"], r=R["orta"] - 1)
    t.dikdortgen(x + 1, y + h - 22, w - 2, 10, dolgu=C["zemin"])
    t.yatay(x + 1, x + w - 1, y + h - 22, C["cizgi"])
    t.daire(x + 12, y + h - 11, 2.5, dolgu=C["vurgu"])
    t.yazi(x + 20, taban(y + h - 22, 22, 10), d["durum"], 10, 500, C["metin2"])


def sayfa_dil(t, x, y, w, h):
    sayfa_basligi(t, x, y, w, "Dil ayarları", "Arayüz dili, sayı ve tarih biçimi, birim sistemi ve komut takma adları")
    cw = (w - 64 - 24) / 2
    lx, rx = x + 32, x + 32 + cw + 24
    yy = y + 80
    # --- Arayüz dili
    ah = 41 + 16 + 64 + 16 + 24 + 196 + 16 + 32 + 16
    ky = kart(t, lx, yy, cw, ah, "Arayüz dili", "dil")
    ow = (cw - 32 - 12) / 2
    for i, (kod, ad, alt, sec) in enumerate((("TR", "Türkçe", "Türkiye · varsayılan", True), ("EN", "English", "United Kingdom", False))):
        bx, by = lx + 16 + i * (ow + 12), ky + 16
        if sec:
            t.dikdortgen(bx, by, ow, 64, dolgu=C["vurgu_ton"], kenar=C["vurgu"], r=R["orta"])
        else:
            t.dikdortgen(bx, by, ow, 64, dolgu=C["yuzey"], kenar=C["kenar"], r=R["orta"])
        t.dikdortgen(bx + 14, by + 14, 36, 36, dolgu=C["yuzey"] if sec else C["zemin"], kenar=C["vurgu_ton2"] if sec else C["cizgi"], r=R["orta"])
        t.yazi_orta(bx + 32, taban(by + 14, 36, 13), kod, 13, 700, C["vurgu_metin"] if sec else C["metin2"])
        t.yazi(bx + 62, by + 28, ad, 13, 600, C["metin"])
        t.yazi(bx + 62, by + 46, alt, 11, 400, C["metin3"])
        t.radyo(bx + ow - 22, by + 32, sec, 7)
    py = ky + 16 + 64 + 16
    t.yazi_aralikli(lx + 16, py + 12, "ÖNİZLEME", 9, 600, C["metin3"], 0.6)
    t.yazi_sag(lx + cw - 16, py + 12, "Model sekmesi · Özellikler · komut satırı · durum çubuğu", 10, 400, C["metin3"])
    py += 24
    pw = (cw - 32 - 12) / 2
    mini_onizleme(t, lx + 16, py, pw, 196, "tr", True)
    mini_onizleme(t, lx + 16 + pw + 12, py, pw, 196, "en", False)
    ny = py + 196 + 16
    t.dikdortgen(lx + 16, ny, cw - 32, 32, dolgu=C["vurgu_ton"], r=R["orta"])
    t.simge("bilgi", lx + 32, ny + 16, 14, C["vurgu_metin"], 1.4)
    t.yazi(lx + 46, taban(ny, 32, 11), "Yeniden başlatmadan uygulanır; komutlar iki dilde de yazılabilir.", 11, 500, C["vurgu_metin"])
    yy += ah + 16
    # --- Sayı ve tarih
    kh = y + h - 24 - yy
    ky = kart(t, lx, yy, cw, kh, "Sayı ve tarih", "sayi")
    xr, cy = satir(t, lx, ky, cw, 44, "Ondalık ayırıcı", ayrac=False)
    segment_sag(t, xr, cy, ["Virgül  1,5", "Nokta  1.5"], 0)
    xr, cy = satir(t, lx, ky + 44, cw, 44, "Binlik ayırıcı")
    segment_sag(t, xr, cy, ["İnce boşluk", "Nokta", "Yok"], 0)
    xr, cy = satir(t, lx, ky + 88, cw, 44, "Tarih biçimi")
    t.acilir(xr - 236, cy - DH / 2, 236, DH, "31.10.2026  (GG.AA.YYYY)", 12)
    xr, cy = satir(t, lx, ky + 132, cw, 44, "Tablo ondalıkları", "Tablo ve raporlarda gösterilen basamak")
    t.adimlayici(xr - 132, cy - DH / 2, 132, DH, "3", 12, "basamak")
    xr, cy = satir(t, lx, ky + 176, cw, 44, "Örnek")
    t.giris(xr - 236, cy - DH / 2, 236, DH, "12 345,678 kN · 31.10.2026", 12, salt=True)

    # --- sağ: Birim sistemi
    yy = y + 80
    ky = kart(t, rx, yy, cw, 41 + 44 + 2 * 32 + 4 + 16, "Birim sistemi", "olcu")
    xr, cy = satir(t, rx, ky, cw, 44, "Birim sistemi", "Girdi, tablo ve raporlarda", ayrac=False)
    t.dugme(xr - 96, cy - DH / 2, 96, DH, "Ayrıntılı…", "hayalet", boyut=12)
    segment_sag(t, xr - 96 - 8, cy, ["kN · m", "tf · m"], 0)
    ry = ky + 44
    t.dikdortgen(rx + 16, ry, cw - 32, 2 * 32 + 4, dolgu=C["yuzey2"], kenar=C["cizgi2"], r=R["orta"])
    for i, (ad, a, b) in enumerate((("Çizgisel yük", "4,20 kN/m", "0,428 tf/m"), ("Kolon eksenel kuvveti", "1 842 kN", "187,8 tf"))):
        yy2 = ry + 2 + i * 32
        if i:
            t.yatay(rx + 28, rx + cw - 28, yy2, C["cizgi2"])
        t.yazi(rx + 28, taban(yy2, 32, 12), ad, 12, 400, C["metin2"])
        t.yazi_sag(rx + cw - 28 - 112, taban(yy2, 32, 12), a, 12, 600, C["metin"], tnum=True)
        t.simge("sevron_sag", rx + cw - 28 - 96, yy2 + 16, 10, C["metin3"], 1.6)
        t.yazi_sag(rx + cw - 28, taban(yy2, 32, 12), b, 12, 400, C["metin3"], tnum=True)
    yy += 41 + 44 + 2 * 32 + 4 + 16 + 16
    # --- Komut takma adları
    kh = y + h - 24 - yy
    ky = kart(t, rx, yy, cw, kh, "Komut takma adları", "komut")
    xr, cy = satir(t, rx, ky, cw, 44, "İngilizce takma adları kabul et", "kolon = column · kiriş = beam", ayrac=False)
    t.anahtar(xr - 28, cy - 8, True)
    xr, cy = satir(t, rx, ky + 44, cw, 44, "Esnek Türkçe eşleme", "i/ı · s/ş · c/ç · g/ğ · o/ö · u/ü aynı sayılır")
    t.anahtar(xr - 28, cy - 8, True)
    sy = ky + 88 + 12
    t.yatay(rx + 16, rx + cw - 16, ky + 88, C["cizgi2"])
    t.giris(rx + 16, sy, cw - 32 - 136, DH, "Takma ad ara", 12, renk=C["metin3"], simge="ara")
    t.dugme(rx + cw - 16 - 128, sy, 128, DH, "Takma ad ekle", "ikincil", boyut=12, simge="artı")
    ty = sy + DH + 12
    c1, c2, c3, c4 = rx + 16, rx + 16 + 140, rx + 16 + 260, rx + cw - 16
    ty = tablo_basligi(t, rx + 1, ty, cw - 2, [("Komut", c1, "sol"), ("Türkçe", c2, "sol"), ("English", c3, "sol"), ("Kısa", c4, "sag")])
    adlar = [("KOLON", "kolon", "column", "KL"), ("KİRİŞ", "kiriş", "beam", "KR"), ("ÇAPRAZ", "çapraz", "brace", "ÇP"),
             ("DÖŞEME", "döşeme", "slab", "DŞ"), ("AKS", "aks", "grid", "AK"), ("KAT", "kat", "story", "KT"),
             ("SEÇSÜZ", "seçsüz", "selectfilter", "SS"), ("KATKOPYALA", "katkopyala", "copystory", "KK"),
             ("TAŞI", "taşı", "move", "TŞ"), ("KOPYALA", "kopyala", "copy", "KP"), ("ÇÖZ", "çöz", "solve", "F5")]
    rh = 28
    for i, (k_, tr, en, ks) in enumerate(adlar):
        ry = ty + i * rh
        if ry + rh > yy + kh - 36:
            break
        if i == 1:
            t.dikdortgen(rx + 4, ry + 1, cw - 8, rh - 2, dolgu=C["hover"], r=R["kucuk"])
            t.simge("nokta3", c4 - 40, ry + rh / 2, 14, C["simge2"], 1.4)
        else:
            t.yatay(rx + 16, rx + cw - 16, ry + rh - 1, C["cizgi2"])
        t.yazi(c1, taban(ry, rh, 12), k_, 12, 600, C["metin"])
        t.yazi(c2, taban(ry, rh, 12), tr, 12, 400, C["metin"])
        t.yazi(c3, taban(ry, rh, 12), en, 12, 400, C["metin2"])
        if ks == "F5":
            t.kisayol_dizisi(c4, ry + 5, "F5", 10, 18, sag=True)
        else:
            t.yazi_sag(c4, taban(ry, rh, 12), ks, 12, 500, C["metin2"])
    fy = yy + kh - 36
    t.yatay(rx + 1, rx + cw - 1, fy, C["cizgi2"])
    t.yazi(rx + 16, taban(fy, 36, 11), "142 komut · 286 takma ad", 11, 400, C["metin3"], tnum=True)
    t.yazi_sag(rx + cw - 16, taban(fy, 36, 11), "CSV olarak dışa aktar…", 11, 500, C["vurgu_metin"])
    return 0


SAYFALAR = {"program": (sayfa_program, 1), "goruntu": (sayfa_goruntu, 1), "dil": (sayfa_dil, 0)}


def ayarlar_ekrani(sayfa, arka_plan):
    W, H = 1920, 1080
    t = Tuval(W, H, 1)
    t.yapistir(arka_plan, 0, 0)
    t.karart(0, 0, W, H, 0.38)
    x0, y0 = (W - PW) // 2, (H - PH) // 2
    fn, degisiklik = SAYFALAR[sayfa]
    ix, iy, iw, ih = pencere(t, x0, y0, sayfa, degisiklik)
    fn(t, ix, iy, iw, ih)
    return t.img
