#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atölye · Modern — karşılaştırma paftası (2400 px genişlik): üst sırada üç vurgu seçeneği (A Kobalt, B Petrol, C Grafit)
renk örnekleriyle, alt sırada Ayarlar penceresinin üç sayfası.
"""
from PIL import Image, ImageFilter

from belirtec import C, R, PALETLER, NOTR, hex2rgb, rgba, palet_uygula, ustundeki_metin
from tuval import Tuval, taban

GEN = 2400
KENAR = 48
ARA = 32
KUC_W = (GEN - 2 * KENAR - 2 * ARA) // 3          # 746
ANA_H = round(KUC_W * 1080 / 1920)                 # 420
PEN_KIRP = (216, 36, 1704, 1044)                   # Ayarlar penceresi + biraz karartılmış çevre
PEN_H = round(KUC_W * (PEN_KIRP[3] - PEN_KIRP[1]) / (PEN_KIRP[2] - PEN_KIRP[0]))


def kucult(im, w, h):
    k = im.resize((w, h), Image.LANCZOS)
    return k.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=1))


def karsilastirma(ekranlar, sayfalar):
    palet_uygula("kobalt")
    H = 64 + 72 + 40 + 44 + ANA_H + 92 + 56 + 44 + PEN_H + 96
    t = Tuval(GEN, H, 1, zemin=NOTR["sayfa"])
    y = 64
    t.yazi(KENAR, y + 8, "op4 · Atölye — modern", 32, 600, NOTR["metin"])
    t.yazi(KENAR, y + 44, "Atölye iskeleti korunur (şerit · sol ray · model ağacı · Özellikler + pencere şeridi · rıhtım · komut satırı · kat kapsamlı durum çubuğu); "
           "bronz vurgu kaldırıldı, üç vurgu seçeneği ve Ayarlar penceresi eklendi.", 15, 400, NOTR["metin3"])
    t.yazi_sag(GEN - KENAR, y + 8, "Önerilen varsayılan: A — Kobalt mavisi", 15, 600, NOTR["metin2"])
    t.yazi_sag(GEN - KENAR, y + 32, "Palet değişimi tek satır: belirtec.py › VARSAYILAN_PALET", 13, 400, NOTR["metin3"])
    y += 72 + 40
    t.yazi_aralikli(KENAR, y, "VURGU SEÇENEKLERİ · ANA EKRAN 1920 × 1080 · MODEL SEKMESİ · 6 KİRİŞ SEÇİLİ", 12, 600, NOTR["metin3"], 1.2)
    y += 20
    for i, ad in enumerate(("kobalt", "petrol", "grafit")):
        p = PALETLER[ad]
        x = KENAR + i * (KUC_W + ARA)
        # etiket
        t.dikdortgen(x, y, 28, 28, dolgu=p["vurgu"], r=R["orta"])
        t.yazi_orta(x + 14, taban(y, 28, 14), p["kisa"], 14, 700, ustundeki_metin(p["vurgu"]))
        t.yazi(x + 40, taban(y, 28, 18), p["ad"], 18, 600, NOTR["metin"])
        if ad == "kobalt":
            bw = t.yazi_gen("önerilen", 11, 600) + 16
            t.dikdortgen(x + KUC_W - bw, y + 4, bw, 20, dolgu=p["vurgu_ton"], kenar=p["vurgu_ton2"], r=R["orta"])
            t.yazi_orta(x + KUC_W - bw / 2, taban(y + 4, 20, 11), "önerilen", 11, 600, p["vurgu_metin"])
        iy = y + 44
        t.golge(x, iy, KUC_W, ANA_H, r=R["buyuk"], tur="acilir", alfa=0.12)
        im = kucult(ekranlar[ad], KUC_W, ANA_H)
        t.yapistir(im, x, iy)
        t.cerceve(x, iy, KUC_W, ANA_H, rgba(NOTR["golge"], 0.18), 1, 0)
        # renk örnekleri
        sy = iy + ANA_H + 16
        ornekler = [("vurgu", p["vurgu"]), ("vurgu_ton", p["vurgu_ton"]), ("secim", p["secim"]), ("secim_dolgu", p["secim_dolgu"]), ("odak", p["odak"])]
        sx = x
        for et, renk in ornekler:
            t.dikdortgen(sx, sy, 20, 20, dolgu=renk, kenar=rgba(NOTR["golge"], 0.15), r=R["kucuk"])
            t.yazi(sx + 28, sy + 9, et, 11, 600, NOTR["metin2"])
            t.yazi(sx + 28, sy + 23, renk.upper(), 11, 400, NOTR["metin3"], tnum=True)
            sx += 28 + max(t.yazi_gen(et, 11, 600), t.yazi_gen(renk.upper(), 11, 400)) + 22
        not_ = {"kobalt": "Mavi vurgu = seçim: tek renk dili, en tanıdık.",
                "petrol": "Sakin, mühendislik tonu; D/C yeşilinden ayrı tutulur.",
                "grafit": "Arayüz tek renk; mavi yalnız seçim ve odakta."}[ad]
        t.yazi(x, sy + 48, not_, 13, 400, NOTR["metin2"])
    y += 44 + ANA_H + 92 + 24
    t.yatay(KENAR, GEN - KENAR, y - 24, NOTR["cizgi"])
    t.yazi_aralikli(KENAR, y + 8, "AYARLAR PENCERESİ · KİPLİ · 1440 × 960 · KARARTILMIŞ PROGRAM ÜSTÜNDE · KOBALT", 12, 600, NOTR["metin3"], 1.2)
    y += 28
    for i, (ad, baslik, alt) in enumerate((("program", "Program ayarları", "Başlangıç · kayıt/kurtarma · geri al · birimler · klasörler · hesap motoru · kısayollar"),
                                          ("goruntu", "Görüntü ayarları", "Grafik · MSAA · kalite / ağ ±%2 · model görünümü · seçim renkleri · arayüz"),
                                          ("dil", "Dil ayarları", "Türkçe / English önizlemeli · sayı ve tarih · kN·m / tf·m · takma adlar"))):
        x = KENAR + i * (KUC_W + ARA)
        t.yazi(x, y + 18, baslik, 18, 600, NOTR["metin"])
        t.yazi(x, y + 40, alt, 12, 400, NOTR["metin3"])
        iy = y + 56
        kirp = sayfalar[ad].crop(PEN_KIRP)
        t.golge(x, iy, KUC_W, PEN_H, r=R["buyuk"], tur="acilir", alfa=0.12)
        t.yapistir(kucult(kirp, KUC_W, PEN_H), x, iy)
        t.cerceve(x, iy, KUC_W, PEN_H, rgba(NOTR["golge"], 0.18), 1, 0)
    y += 56 + PEN_H + 40
    t.yazi(KENAR, y, "Üreteç: uret.py · ayarlar.py · karsilastir.py · sahne.py · tuval.py — bütün renk, yarıçap, aralık ve yazı değerleri tek modülde: belirtec.py", 12, 400, NOTR["metin3"])
    return t.img
