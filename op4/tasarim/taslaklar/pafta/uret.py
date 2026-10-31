#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
op4 arayüz taslağı — Yön A "Pafta" (çizim paftası dinginliği).

Tüm görselleri yeniden üretir:   python3 uret.py            (hepsi)
                                 python3 uret.py ana sonuc  (yalnız seçilenler)
                                 python3 uret.py --hizli    (düşük kalite, hızlı deneme)
Çıktılar bu dosyanın yanına yazılır:
  ana.png 1920×1080 · ana-2x.png 3840×2160 · kucuk.png 1366×768 · detay-serit.png (şerit, 2×)
  detay-panel.png (model ağacı + Özellikler, 2×) · secsuz.png (Seç ve Süz) · sonuc.png (Tasarım sekmesi, D/C)
  kat-kapsami.png (durum çubuğu kat kapsamı anahtarı, 2× kırpım)

Yalnız Pillow + numpy kullanır. Yazı tipleri ve logolar kurumsal kimlik klasöründen okunur (OP4_KIMLIK ortam
değişkeni ile değiştirilebilir). Logolar yeniden çizilmez; yalnız ölçeklenir. Simgeler 24 birimlik ızgarada tek renk
1,5 px çizgiyle burada çizilir (emoji yok).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BURASI = os.path.dirname(os.path.abspath(__file__))
KIMLIK = os.environ.get('OP4_KIMLIK', '/home/user/matris-ogren/op4/kimlik')
FONTLAR = os.path.join(KIMLIK, 'fontlar')
INTER = os.path.join(FONTLAR, 'inter-Inter[opsz,wght].ttf')
CORMORANT = os.path.join(FONTLAR, 'cormorantgaramond-CormorantGaramond[wght].ttf')
SIMGE = os.path.join(KIMLIK, 'opus-fortis-simge-koyu.png')
YAZI_LOGO = os.path.join(KIMLIK, 'opus-fortis-yazi-acik-zemin.png')
HIZLI = False   # --hizli: görünüm penceresi düşük kalitede


# ------------------------------------------------------------------ renk belirteçleri
def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def karisim(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def rgba(c, a=1.0):
    return (c[0], c[1], c[2], max(0, min(255, int(round(255 * a)))))


KAHVE = hx('8A6B3C')
KREM = hx('EDE6D8')
ALTIN = hx('B08950')
ANTRASIT = hx('14181B')
GRI = hx('8C8C8C')

KAGIT = hx('F6F2EA')          # ana yüzey (şerit, paneller)
KAGIT_ACIK = hx('FBF8F2')     # giriş alanları, kartlar
KAGIT_KOYU = hx('EFE9DD')     # başlık çubuğu, durum çubuğu, pasif dolgu
CIZGI = karisim(KAGIT, ANTRASIT, 0.13)      # kıl çizgi
CIZGI_SOLUK = karisim(KAGIT, ANTRASIT, 0.07)
CIZGI_KOYU = karisim(KAGIT, ANTRASIT, 0.26)
METIN1 = ANTRASIT
METIN2 = karisim(KAGIT, ANTRASIT, 0.68)     # ikincil metin
METIN3 = GRI                                 # sönük metin, grup adları, sayımlar
ALTIN_ACIK = karisim(KAGIT, ALTIN, 0.16)     # seçili satır / etkin düğme dolgusu
ALTIN_ORTA = karisim(KAGIT, ALTIN, 0.48)     # seçili kenar
BEYAZ = (255, 255, 255)
HATA = hx('A8453A')
YESIL = hx('5B8A4A')

CELIK = (214, 212, 206)        # görünümde çelik temel rengi
BETON = (233, 230, 223)        # döşeme
SECIM_DOLGU = karisim(CELIK, ALTIN, 0.30)
GOK_UST = (255, 255, 255)      # model arka planı: beyaz → açık gri gradyan
GOK_ALT = (233, 231, 226)
PAFTA_ZEMIN = (250, 248, 243)  # zemin paftası

# D/C renk sınıfları (5 eşik: <0,50 · 0,50–0,70 · 0,70–0,90 · 0,90–1,00 · >1,00) — açık tema çifti
DC_ESIK = [0.50, 0.70, 0.90, 1.00]
DC_RENK = [hx('86A9C8'), hx('83B072'), hx('DCBC52'), hx('DE8B40'), hx('C4463A')]
DC_ETIKET = ['< 0,50', '0,50 – 0,70', '0,70 – 0,90', '0,90 – 1,00', '> 1,00']


def dc_sinif(r):
    for i, e in enumerate(DC_ESIK):
        if r < e:
            return i
    return 4


# ------------------------------------------------------------------ yazı tipleri
_FONT_ONBELLEK = {}


def font(boy_px, w=400, ad='inter', opsz=14):
    key = (ad, boy_px, w, opsz)
    f = _FONT_ONBELLEK.get(key)
    if f is None:
        yol = INTER if ad == 'inter' else CORMORANT
        f = ImageFont.truetype(yol, boy_px, layout_engine=ImageFont.Layout.RAQM)
        if ad == 'inter':
            f.set_variation_by_axes([opsz, w])
        else:
            f.set_variation_by_axes([w])
        _FONT_ONBELLEK[key] = f
    return f


# ------------------------------------------------------------------ simgeler (24 birimlik ızgarada tek renk çizgi)
IKONLAR = {}


def ikon(ad):
    def sar(fn):
        IKONLAR[ad] = fn
        return fn
    return sar


class Kalem:
    """24×24 tasarım ızgarasından piksele çeviren basit çizim kalemi."""

    def __init__(self, d, k, renk, w):
        self.d, self.k, self.renk, self.w = d, k, renk, w

    def _p(self, p):
        return (p[0] * self.k, p[1] * self.k)

    def L(self, pts, kapali=False):
        q = [self._p(p) for p in pts]
        if kapali:
            q = q + [q[0]]
        self.d.line(q, fill=self.renk, width=self.w, joint='curve')
        r = self.w / 2.0
        for x, y in q:
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=self.renk)

    def C(self, c, r):
        x, y = self._p(c)
        R = r * self.k
        self.d.ellipse([x - R, y - R, x + R, y + R], outline=self.renk, width=self.w)

    def D(self, c, r):
        x, y = self._p(c)
        R = r * self.k
        self.d.ellipse([x - R, y - R, x + R, y + R], fill=self.renk)

    def R(self, a, b, r=0):
        x0, y0 = self._p(a)
        x1, y1 = self._p(b)
        self.d.rounded_rectangle([x0, y0, x1, y1], radius=r * self.k, outline=self.renk, width=self.w)

    def F(self, pts):
        self.d.polygon([self._p(p) for p in pts], fill=self.renk)

    def A(self, c, r, a0, a1):
        x, y = self._p(c)
        R = r * self.k
        self.d.arc([x - R, y - R, x + R, y + R], a0, a1, fill=self.renk, width=self.w)

    def Kesikli(self, a, b, n=4):
        ax, ay = a
        bx, by = b
        for i in range(n):
            t0 = (i + 0.15) / n
            t1 = (i + 0.7) / n
            self.L([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)])


# --- yapı elemanları
@ikon('kolon')
def _(K):
    K.L([(6, 3), (18, 3)]); K.L([(6, 21), (18, 21)]); K.L([(10, 3), (10, 21)]); K.L([(14, 3), (14, 21)])


@ikon('kiris')
def _(K):
    K.R((3, 8), (21, 13)); K.L([(6, 13), (6, 19)]); K.L([(18, 13), (18, 19)]); K.L([(3, 19), (9, 19)]); K.L([(15, 19), (21, 19)])


@ikon('capraz')
def _(K):
    K.R((4, 4), (20, 20)); K.L([(4, 4), (20, 20)]); K.L([(20, 4), (4, 20)])


@ikon('doseme')
def _(K):
    K.L([(3, 14), (9, 6), (21, 6), (15, 14)], True); K.L([(3, 14), (3, 18), (15, 18), (15, 14)]); K.L([(15, 18), (21, 10), (21, 6)])


@ikon('duvar')
def _(K):
    K.R((3, 5), (21, 19)); K.L([(3, 10), (21, 10)]); K.L([(3, 15), (21, 15)])
    K.L([(9, 5), (9, 10)]); K.L([(15, 5), (15, 10)]); K.L([(6, 10), (6, 15)]); K.L([(12, 10), (12, 15)]); K.L([(18, 10), (18, 15)])
    K.L([(9, 15), (9, 19)]); K.L([(15, 15), (15, 19)])


@ikon('temel')
def _(K):
    K.L([(10, 3), (10, 12)]); K.L([(14, 3), (14, 12)]); K.R((4, 12), (20, 18)); K.Kesikli((2, 21.5), (22, 21.5), 5)


@ikon('aks')
def _(K):
    K.L([(9, 7), (9, 21)]); K.L([(16, 7), (16, 21)]); K.L([(5, 11), (21, 11)]); K.L([(5, 18), (21, 18)])
    K.C((9, 4), 2.2); K.C((16, 4), 2.2); K.C((3, 11), 2.2); K.C((3, 18), 2.2)


@ikon('kat')
def _(K):
    for y0 in (3.5, 9.5, 15.5):
        K.L([(3, y0 + 4.5), (9, y0), (21, y0), (15, y0 + 4.5)], True)


@ikon('hizli_kolon')
def _(K):
    K.L([(4, 4), (12, 4)]); K.L([(4, 18), (12, 18)]); K.L([(7, 4), (7, 18)]); K.L([(9, 4), (9, 18)])
    K.F([(13, 11), (21, 15), (17.5, 16), (16, 20)]); K.L([(13, 11), (21, 15), (17.5, 16), (16, 20)], True)


@ikon('hizli_kiris')
def _(K):
    K.R((3, 6), (21, 10)); K.L([(6, 10), (6, 14)]); K.L([(18, 10), (18, 14)])
    K.F([(12, 13), (20, 17), (16.5, 18), (15, 22)]); K.L([(12, 13), (20, 17), (16.5, 18), (15, 22)], True)


@ikon('sec')
def _(K):
    K.L([(6, 3), (6, 18), (10, 14.5), (13, 21), (15.5, 20), (12.5, 13.5), (18, 13.5)], True)


@ikon('suz')
def _(K):
    K.L([(3, 5), (21, 5), (14, 13), (14, 20), (10, 22), (10, 13)], True)


@ikon('benzer')
def _(K):
    K.R((3, 3), (14, 14), 1.5); K.R((10, 10), (21, 21), 1.5); K.L([(13, 16), (15, 18), (19, 13)])


@ikon('ters')
def _(K):
    K.C((12, 12), 8.5); K.F([(12, 3.5), (20.5, 12), (12, 20.5)]); K.L([(12, 3.5), (12, 20.5)])


@ikon('grup')
def _(K):
    K.C((6, 7), 3); K.C((18, 7), 3); K.C((12, 18), 3); K.L([(8.5, 8.5), (10.5, 15.5)]); K.L([(15.5, 8.5), (13.5, 15.5)]); K.L([(9, 7), (15, 7)])


@ikon('plan')
def _(K):
    K.R((4, 4), (20, 20)); K.L([(4, 9.5), (20, 9.5)]); K.L([(4, 14.5), (20, 14.5)]); K.L([(9.5, 4), (9.5, 20)]); K.L([(14.5, 4), (14.5, 20)])


@ikon('yukselti')
def _(K):
    K.R((4, 8), (20, 21)); K.L([(4, 8), (12, 3), (20, 8)]); K.L([(4, 14.5), (20, 14.5)]); K.L([(12, 8), (12, 21)])


@ikon('referans')
def _(K):
    K.Kesikli((3, 16), (11, 7), 3); K.Kesikli((11, 7), (21, 7), 3); K.Kesikli((21, 7), (13, 16), 3); K.Kesikli((13, 16), (3, 16), 3)


@ikon('kesit_k')
def _(K):
    K.L([(6, 4), (18, 4)]); K.L([(6, 20), (18, 20)]); K.L([(12, 4), (12, 20)])


@ikon('kot')
def _(K):
    K.L([(4, 6), (20, 6)]); K.L([(4, 18), (20, 18)]); K.L([(12, 6), (12, 18)]); K.L([(9, 9), (12, 6), (15, 9)]); K.L([(9, 15), (12, 18), (15, 15)])


@ikon('dondur')
def _(K):
    K.A((12, 12), 8, 200, 120); K.L([(15, 18.5), (19.5, 18.5), (18.8, 14)])


@ikon('tali')
def _(K):
    K.L([(3, 6), (21, 6)]); K.L([(3, 18), (21, 18)]); K.L([(8, 6), (8, 18)]); K.L([(16, 6), (16, 18)])


@ikon('serbestlik')
def _(K):
    K.L([(3, 12), (8, 12)]); K.C((12, 12), 4); K.L([(16, 12), (21, 12)])


@ikon('xvk')
def _(K):
    K.R((3, 4), (21, 20)); K.L([(3, 20), (12, 4), (21, 20)])


@ikon('kalinlik')
def _(K):
    K.L([(3, 9), (21, 9)]); K.L([(3, 15), (21, 15)]); K.L([(12, 3), (12, 21)]); K.L([(9.5, 5.5), (12, 3), (14.5, 5.5)]); K.L([(9.5, 18.5), (12, 21), (14.5, 18.5)])


@ikon('bosluk')
def _(K):
    K.R((3, 3), (21, 21)); K.Kesikli((9, 9), (15, 9), 2); K.Kesikli((15, 9), (15, 15), 2); K.Kesikli((15, 15), (9, 15), 2); K.Kesikli((9, 15), (9, 9), 2)


@ikon('tekil')
def _(K):
    K.R((7, 13), (17, 19)); K.L([(11, 4), (11, 13)]); K.L([(13, 4), (13, 13)])


@ikon('surekli')
def _(K):
    K.R((2, 13), (22, 19)); K.L([(7, 4), (7, 13)]); K.L([(9, 4), (9, 13)]); K.L([(15, 4), (15, 13)]); K.L([(17, 4), (17, 13)])


@ikon('radye')
def _(K):
    K.R((2, 15), (22, 20)); K.L([(2, 15), (2, 11), (22, 11), (22, 15)])


# --- başlık, pencere, genel
@ikon('yeni')
def _(K):
    K.L([(6, 3), (14, 3), (19, 8), (19, 21), (6, 21)], True); K.L([(14, 3), (14, 8), (19, 8)])


@ikon('ac')
def _(K):
    K.L([(3, 6), (9, 6), (11, 8.5), (21, 8.5), (21, 19), (3, 19)], True); K.L([(3, 12), (21, 12)])


@ikon('kaydet')
def _(K):
    K.L([(4, 4), (17, 4), (20, 7), (20, 20), (4, 20)], True); K.R((8, 4), (15, 9)); K.R((8, 14), (16, 20))


@ikon('geri')
def _(K):
    K.L([(10, 6), (5, 11), (10, 16)]); K.L([(5, 11), (15, 11)]); K.A((14, 15), 4, 270, 90)


@ikon('yinele')
def _(K):
    K.L([(14, 6), (19, 11), (14, 16)]); K.L([(19, 11), (9, 11)]); K.A((10, 15), 4, 90, 270)


@ikon('kucult')
def _(K):
    K.L([(5, 12), (19, 12)])


@ikon('buyut')
def _(K):
    K.R((5, 5), (19, 19))


@ikon('kapat')
def _(K):
    K.L([(6, 6), (18, 18)]); K.L([(18, 6), (6, 18)])


@ikon('ara')
def _(K):
    K.C((10.5, 10.5), 6.5); K.L([(15.5, 15.5), (21, 21)])


@ikon('pin')
def _(K):
    K.L([(9, 3), (15, 3)]); K.L([(10, 3), (10, 10), (6, 14), (18, 14), (14, 10), (14, 3)]); K.L([(12, 14), (12, 21)])


@ikon('sag2')
def _(K):
    K.L([(6, 6), (12, 12), (6, 18)]); K.L([(13, 6), (19, 12), (13, 18)])


@ikon('sol2')
def _(K):
    K.L([(18, 6), (12, 12), (18, 18)]); K.L([(11, 6), (5, 12), (11, 18)])


@ikon('chev_d')
def _(K):
    K.L([(5, 9), (12, 16), (19, 9)])


@ikon('chev_u')
def _(K):
    K.L([(5, 15), (12, 8), (19, 15)])


@ikon('chev_r')
def _(K):
    K.L([(9, 5), (16, 12), (9, 19)])


@ikon('goz')
def _(K):
    K.L([(2, 12), (7, 7), (17, 7), (22, 12), (17, 17), (7, 17)], True); K.C((12, 12), 3)


@ikon('goz_kapali')
def _(K):
    K.L([(2, 12), (7, 7), (17, 7), (22, 12), (17, 17), (7, 17)], True); K.L([(4, 20), (20, 4)])


@ikon('daralt')
def _(K):
    K.L([(5, 9), (12, 3), (19, 9)]); K.L([(5, 20), (12, 14), (19, 20)])


@ikon('bilgi')
def _(K):
    K.C((12, 12), 9); K.L([(12, 11), (12, 17)]); K.D((12, 7.5), 1.1)


@ikon('ayar')
def _(K):
    K.C((12, 12), 3)
    for i in range(8):
        a = math.radians(i * 45)
        K.L([(12 + 6.5 * math.cos(a), 12 + 6.5 * math.sin(a)), (12 + 9 * math.cos(a), 12 + 9 * math.sin(a))])


@ikon('onay')
def _(K):
    K.L([(5, 12.5), (10, 17.5), (19, 7)])


@ikon('arti')
def _(K):
    K.L([(12, 5), (12, 19)]); K.L([(5, 12), (19, 12)])


@ikon('nokta')
def _(K):
    K.D((12, 12), 2.2)


@ikon('menu')
def _(K):
    K.L([(4, 7), (20, 7)]); K.L([(4, 12), (20, 12)]); K.L([(4, 17), (20, 17)])


@ikon('ucnokta')
def _(K):
    K.D((6, 12), 1.6); K.D((12, 12), 1.6); K.D((18, 12), 1.6)


@ikon('gecmis')
def _(K):
    K.A((12, 12), 8, 300, 240); K.L([(4, 5), (4.3, 10), (9, 10)]); K.L([(12, 8), (12, 12.5), (15.5, 14.5)])


# --- yan panel şeridi
@ikon('ozellik')
def _(K):
    K.L([(4, 7), (20, 7)]); K.L([(4, 12), (20, 12)]); K.L([(4, 17), (20, 17)]); K.D((9, 7), 2); K.D((15, 12), 2); K.D((7, 17), 2)


@ikon('katalog')
def _(K):
    K.L([(5, 4), (19, 4), (19, 20), (5, 20)], True); K.L([(9, 4), (9, 20)]); K.L([(12, 8), (16, 8)]); K.L([(12, 11), (16, 11)])


@ikon('agac')
def _(K):
    K.L([(6, 4), (6, 18), (12, 18)]); K.L([(6, 11), (12, 11)]); K.R((12, 2.5), (20, 6.5)); K.R((12, 9), (20, 13)); K.R((12, 16), (20, 20)); K.L([(6, 4), (12, 4)])


@ikon('filtre_gor')
def _(K):
    K.L([(3, 4), (15, 4), (10.5, 10), (10.5, 17), (7.5, 19), (7.5, 10)], True); K.L([(13, 17), (16, 14), (20, 14), (23, 17), (20, 20), (16, 20)], True); K.D((18, 17), 1.3)


@ikon('sorgu')
def _(K):
    K.C((12, 12), 9); K.A((12, 10), 3.2, 200, 90); K.L([(12, 13.2), (12, 15)]); K.D((12, 18), 1.1)


# --- görünüm araç çubuğu
@ikon('cubuk')
def _(K):
    K.L([(4, 19), (4, 7), (20, 7), (20, 19)]); K.L([(12, 7), (12, 19)]); K.D((4, 7), 1.5); K.D((20, 7), 1.5); K.D((12, 7), 1.5)


@ikon('ekstruzyon')
def _(K):
    K.L([(4, 9), (9, 4), (21, 4), (21, 15), (16, 20), (4, 20)], True); K.L([(4, 9), (16, 9), (21, 4)]); K.L([(16, 9), (16, 20)])


@ikon('golge')
def _(K):
    K.C((12, 10), 6); K.L([(5, 20), (19, 20)]); K.L([(7, 17), (17, 17)])


@ikon('izgara')
def _(K):
    K.R((4, 4), (20, 20)); K.L([(4, 12), (20, 12)]); K.L([(12, 4), (12, 20)])


@ikon('kat_duzlem')
def _(K):
    K.L([(3, 10), (9, 5), (21, 5), (15, 10)], True); K.L([(3, 18), (9, 13), (21, 13), (15, 18)], True)


@ikon('perspektif')
def _(K):
    K.L([(5, 20), (9, 7), (15, 7), (19, 20)], True); K.L([(5, 20), (19, 20)]); K.L([(9, 7), (15, 7)])


@ikon('kesit_duzlem')
def _(K):
    K.L([(4, 9), (9, 4), (21, 4), (21, 15), (16, 20), (4, 20)], True); K.Kesikli((2, 14), (22, 10), 4)


@ikon('sinir')
def _(K):
    K.R((4, 4), (20, 20), 1); K.D((4, 4), 1.6); K.D((20, 4), 1.6); K.D((4, 20), 1.6); K.D((20, 20), 1.6); K.L([(9, 12), (15, 12)])


@ikon('renk')
def _(K):
    K.C((12, 12), 8.5); K.A((12, 12), 5, 0, 180); K.F([(12, 3.5), (20.5, 12), (12, 20.5), (3.5, 12)])


# --- durum çubuğu
@ikon('orto')
def _(K):
    K.L([(5, 19), (5, 5)]); K.L([(5, 19), (19, 19)]); K.L([(5, 5), (7, 8), (3, 8)]); K.L([(19, 19), (16, 17), (16, 21)])


@ikon('yakala')
def _(K):
    K.A((12, 11), 6.5, 180, 360); K.L([(5.5, 11), (5.5, 17)]); K.L([(18.5, 11), (18.5, 17)]); K.L([(5.5, 17), (9, 17)]); K.L([(15, 17), (18.5, 17)]); K.L([(9, 17), (9, 11)]); K.L([(15, 17), (15, 11)])


@ikon('surukle')
def _(K):
    K.R((3, 8), (12, 17)); K.Kesikli((12, 7), (21, 7), 2); K.Kesikli((21, 7), (21, 16), 2); K.Kesikli((21, 16), (12, 16), 2)


@ikon('kilit')
def _(K):
    K.R((6, 11), (18, 20), 1); K.A((12, 11), 4, 180, 360)


# --- seçim anahtarları
@ikon('dugum')
def _(K):
    K.C((12, 12), 3.5); K.L([(12, 3), (12, 8.5)]); K.L([(12, 15.5), (12, 21)]); K.L([(3, 12), (8.5, 12)]); K.L([(15.5, 12), (21, 12)])


@ikon('yuk')
def _(K):
    K.L([(4, 4), (20, 4)])
    for x in (6, 12, 18):
        K.L([(x, 4), (x, 15)]); K.L([(x - 2.5, 12.5), (x, 15), (x + 2.5, 12.5)])
    K.L([(3, 20), (21, 20)])


@ikon('mesnet')
def _(K):
    K.L([(12, 4), (4, 16), (20, 16)], True); K.L([(2, 20), (22, 20)]); K.D((12, 4), 1.5)


@ikon('tumu')
def _(K):
    K.R((3, 3), (10, 10)); K.R((14, 3), (21, 10)); K.R((3, 14), (10, 21)); K.R((14, 14), (21, 21))


# --- sonuç / tasarım
@ikon('yonetmelik')
def _(K):
    K.L([(5, 4), (19, 4), (19, 20), (5, 20)], True); K.L([(8, 9), (16, 9)]); K.L([(8, 13), (14, 13)]); K.L([(8, 17), (12, 17)])


@ikon('basla')
def _(K):
    K.L([(7, 4), (19, 12), (7, 20)], True)


@ikon('kontrol')
def _(K):
    K.C((12, 12), 9); K.L([(7.5, 12.5), (10.5, 15.5), (16.5, 9)])


@ikon('dc')
def _(K):
    K.A((12, 14), 8.5, 180, 360); K.L([(3.5, 14), (3.5, 17)]); K.L([(20.5, 14), (20.5, 17)]); K.L([(12, 14), (17, 8.5)]); K.D((12, 14), 1.6)


@ikon('pm')
def _(K):
    K.L([(4, 20), (4, 4)]); K.L([(4, 20), (20, 20)]); K.L([(6, 6), (12, 7), (17, 11), (19, 18)])


@ikon('ayrinti')
def _(K):
    K.R((4, 4), (20, 20)); K.L([(8, 9), (16, 9)]); K.L([(8, 13), (16, 13)]); K.L([(8, 17), (12, 17)])


@ikon('deform')
def _(K):
    K.Kesikli((3, 8), (21, 8), 4); K.L([(3, 8), (7, 13), (12, 15), (17, 13), (21, 8)])


@ikon('diyagram')
def _(K):
    K.L([(3, 8), (21, 8)]); K.L([(3, 8), (6, 15), (12, 18), (18, 15), (21, 8)]); K.L([(12, 8), (12, 18)])


@ikon('reaksiyon')
def _(K):
    K.L([(12, 4), (6, 13), (18, 13)], True); K.L([(3, 16), (21, 16)]); K.L([(12, 22), (12, 17)]); K.L([(9.5, 19.5), (12, 17), (14.5, 19.5)])


@ikon('tablo')
def _(K):
    K.R((3, 4), (21, 20)); K.L([(3, 9.5), (21, 9.5)]); K.L([(3, 14.5), (21, 14.5)]); K.L([(9, 4), (9, 20)]); K.L([(15, 9.5), (15, 20)])


@ikon('rapor')
def _(K):
    K.L([(6, 3), (14, 3), (19, 8), (19, 21), (6, 21)], True); K.L([(9, 11), (16, 11)]); K.L([(9, 15), (16, 15)]); K.L([(9, 18), (13, 18)])


@ikon('tablo_disa')
def _(K):
    K.L([(5, 3), (19, 3), (19, 21), (5, 21)], True); K.L([(8, 8), (16, 16)]); K.L([(16, 8), (8, 16)])


@ikon('kume')
def _(K):
    K.R((3, 5), (15, 15)); K.L([(8, 15), (8, 19), (21, 19), (21, 9), (15, 9)])


@ikon('anim')
def _(K):
    K.L([(5, 5), (13, 12), (5, 19)], True); K.L([(16, 5), (16, 19)]); K.L([(19.5, 5), (19.5, 19)])


@ikon('olcek')
def _(K):
    K.L([(3, 12), (21, 12)]); K.L([(3, 9), (3, 15)]); K.L([(21, 9), (21, 15)]); K.L([(9, 10.5), (9, 13.5)]); K.L([(15, 10.5), (15, 13.5)])


@ikon('etiket')
def _(K):
    K.L([(3, 10), (10, 3), (21, 14), (14, 21)], True); K.D((8, 8), 1.4)


@ikon('temizle')
def _(K):
    K.L([(4, 7), (20, 7)]); K.L([(9, 7), (9, 4), (15, 4), (15, 7)]); K.L([(6, 7), (7, 20), (17, 20), (18, 7)])


@ikon('komb')
def _(K):
    K.L([(4, 6), (20, 6)]); K.L([(4, 12), (20, 12)]); K.L([(4, 18), (20, 18)]); K.L([(7, 4), (7, 8)]); K.L([(13, 10), (13, 14)]); K.L([(10, 16), (10, 20)])


@ikon('tercih')
def _(K):
    K.L([(4, 8), (20, 8)]); K.L([(4, 16), (20, 16)]); K.C((9, 8), 2.5); K.C((15, 16), 2.5)


@ikon('secili')
def _(K):
    K.R((4, 4), (20, 20), 1); K.L([(8, 12), (11, 15), (16.5, 9)])


@ikon('kaydedilmis')
def _(K):
    K.L([(6, 3), (18, 3), (18, 21), (12, 16), (6, 21)], True)


@ikon('parantez')
def _(K):
    K.A((9, 12), 7, 110, 250); K.A((15, 12), 7, 290, 70)


@ikon('yapi')
def _(K):
    K.L([(3, 21), (21, 21)]); K.L([(5, 21), (5, 9), (12, 4), (19, 9), (19, 21)]); K.L([(9, 21), (9, 15), (15, 15), (15, 21)]); K.L([(12, 9), (12, 11)])


_IKON_ONBELLEK = {}


def ikon_resmi(ad, px, renk, kalin_px):
    key = (ad, px, renk, round(kalin_px, 2))
    im = _IKON_ONBELLEK.get(key)
    if im is None:
        SS = 4
        big = Image.new('RGBA', (px * SS, px * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        K = Kalem(d, px * SS / 24.0, renk + (255,), max(1, int(round(kalin_px * SS))))
        IKONLAR[ad](K)
        im = big.resize((px, px), Image.LANCZOS)
        _IKON_ONBELLEK[key] = im
    return im


# ------------------------------------------------------------------ tuval (mantıksal piksel → fiziksel piksel)
class Tuval:
    def __init__(self, W, H, S, zemin=KAGIT):
        self.W, self.H, self.S = W, H, S
        self.im = Image.new('RGBA', (W * S, H * S), zemin + (255,))
        self.d = ImageDraw.Draw(self.im)

    def p(self, v):
        return int(round(v * self.S))

    # --- temel biçimler
    def dolgu(self, x0, y0, x1, y1, renk, r=0):
        if len(renk) == 4 and renk[3] < 255:
            w, h = self.p(x1) - self.p(x0), self.p(y1) - self.p(y0)
            if w <= 0 or h <= 0:
                return
            lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rounded_rectangle([0, 0, w - 1, h - 1], radius=self.p(r), fill=renk)
            self.im.alpha_composite(lay, (self.p(x0), self.p(y0)))
        else:
            self.d.rounded_rectangle([self.p(x0), self.p(y0), self.p(x1) - 1, self.p(y1) - 1], radius=self.p(r), fill=renk)

    def cerceve(self, x0, y0, x1, y1, renk, r=0, w=1):
        self.d.rounded_rectangle([self.p(x0), self.p(y0), self.p(x1) - 1, self.p(y1) - 1], radius=self.p(r), outline=renk,
                                 width=max(1, self.p(w)))

    def yatay(self, x0, x1, y, renk=CIZGI, w=1):
        self.d.rectangle([self.p(x0), self.p(y), self.p(x1) - 1, self.p(y) + max(1, self.p(w)) - 1], fill=renk)

    def dikey(self, x, y0, y1, renk=CIZGI, w=1):
        self.d.rectangle([self.p(x), self.p(y0), self.p(x) + max(1, self.p(w)) - 1, self.p(y1) - 1], fill=renk)

    def cizgi(self, pts, renk, w=1.0):
        q = [(self.p(x), self.p(y)) for x, y in pts]
        self.d.line(q, fill=renk, width=max(1, int(round(w * self.S))), joint='curve')

    def kesikli(self, a, b, renk, w=1.0, cizgi=4, bosluk=3):
        ax, ay = a
        bx, by = b
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-6:
            return
        ux, uy = (bx - ax) / L, (by - ay) / L
        s = 0.0
        while s < L:
            e = min(L, s + cizgi)
            self.cizgi([(ax + ux * s, ay + uy * s), (ax + ux * e, ay + uy * e)], renk, w)
            s = e + bosluk

    def daire(self, cx, cy, r, dolgu=None, kenar=None, w=1):
        box = [self.p(cx - r), self.p(cy - r), self.p(cx + r), self.p(cy + r)]
        self.d.ellipse(box, fill=dolgu, outline=kenar, width=max(1, self.p(w)) if kenar else 0)

    def cokgen(self, pts, dolgu=None, kenar=None, w=1):
        self.d.polygon([(self.p(x), self.p(y)) for x, y in pts], fill=dolgu, outline=kenar, width=max(1, self.p(w)) if kenar else 0)

    # --- metin
    def _f(self, boy, w, ad):
        # yarım boylar yukarı yuvarlanır (10,5 → 11): Python'un bankacı yuvarlaması 10 px'e düşürüp
        # FreeType'ın "n" gövdesini yutmasına yol açıyordu ("nesne" → "resre")
        return font(max(1, int(math.floor(boy * self.S + 0.5))), w, ad, opsz=max(14, min(32, int(round(boy)))))

    def yazi(self, x, y, s, boy=12, w=400, renk=METIN1, anchor='ls', ad='inter'):
        f = self._f(boy, w, ad)
        self.d.text((self.p(x), self.p(y)), s, font=f, fill=renk, anchor=anchor)
        return self.d.textlength(s, font=f) / self.S

    def gen(self, s, boy=12, w=400, ad='inter'):
        return self.d.textlength(s, font=self._f(boy, w, ad)) / self.S

    def aralikli(self, x, y, s, boy=10, w=500, renk=METIN3, aralik=1.2, anchor='l'):
        """Harf aralıklı büyük harf etiket (pafta başlığı tadı)."""
        f = self._f(boy, w, 'inter')
        toplam = sum(self.d.textlength(ch, font=f) for ch in s) / self.S + aralik * (len(s) - 1)
        if anchor == 'm':
            x -= toplam / 2
        elif anchor == 'r':
            x -= toplam
        for ch in s:
            self.d.text((self.p(x), self.p(y)), ch, font=f, fill=renk, anchor='ls')
            x += self.d.textlength(ch, font=f) / self.S + aralik
        return toplam

    def dikey_yazi(self, cx, cy, s, boy=12, w=400, renk=METIN1):
        f = self._f(boy, w, 'inter')
        tw = int(self.d.textlength(s, font=f)) + 4
        th = int(boy * self.S * 1.5)
        lay = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((2, th // 2), s, font=f, fill=renk, anchor='lm')
        lay = lay.rotate(90, expand=True)
        self.im.alpha_composite(lay, (self.p(cx) - lay.width // 2, self.p(cy) - lay.height // 2))

    # --- simge, resim
    def ikon(self, ad, cx, cy, boy, renk=METIN1, kalin=1.5):
        im = ikon_resmi(ad, self.p(boy), renk, kalin * self.S)
        self.im.alpha_composite(im, (self.p(cx - boy / 2.0), self.p(cy - boy / 2.0)))

    def resim(self, im, x, y, yuk):
        h = self.p(yuk)
        w = int(round(im.width * h / im.height))
        self.im.alpha_composite(im.resize((w, h), Image.LANCZOS), (self.p(x), self.p(y)))
        return w / self.S

    def yumusak_golge(self, x0, y0, x1, y1, r=6, yay=10, kay=3, a=0.16):
        pad = yay * 3
        w, h = self.p(x1 - x0 + 2 * pad), self.p(y1 - y0 + 2 * pad)
        lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle([self.p(pad), self.p(pad + kay), self.p(pad + x1 - x0), self.p(pad + y1 - y0 + kay)],
                                              radius=self.p(r), fill=ANTRASIT + (int(255 * a),))
        lay = lay.filter(ImageFilter.GaussianBlur(self.p(yay)))
        self.im.alpha_composite(lay, (self.p(x0 - pad), self.p(y0 - pad)))

    def kirp(self, x0, y0, x1, y1):
        return self.im.crop((self.p(x0), self.p(y0), self.p(x1), self.p(y1)))

    # --- bileşik denetimler
    def alan(self, x0, y0, x1, y1, metin, menu=False, soluk=False, boy=12, w=400, odak=False):
        """Giriş alanı: açık zemin, alt kıl çizgi; menu=True ise sağda ok."""
        self.dolgu(x0, y0, x1, y1, KAGIT_ACIK, r=3)
        self.yatay(x0, x1, y1 - 1, ALTIN if odak else CIZGI)
        self.yazi(x0 + 8, (y0 + y1) / 2 + boy * 0.36, metin, boy, w, METIN3 if soluk else METIN1)
        if menu:
            self.ikon('chev_d', x1 - 11, (y0 + y1) / 2, 10, METIN3, 1.5)

    def katalog_dugmesi(self, x0, y0, x1, y1):
        """'…' katalog düğmesi (kesit/malzeme alanlarının yanında)."""
        self.dolgu(x0, y0, x1, y1, KAGIT_ACIK, r=3)
        self.cerceve(x0, y0, x1, y1, CIZGI_KOYU, r=3)
        self.ikon('ucnokta', (x0 + x1) / 2, (y0 + y1) / 2, 14, METIN1, 1.5)

    def segment(self, x, y, ogeler, etkin, h=22, boy=11, pad=10, dolgu=KAGIT_KOYU):
        """Segmentli anahtar; etkin dilim altın çerçeveli açık zemin. Toplam genişliği döndürür."""
        ws = [self.gen(s, boy, 500) + 2 * pad for s in ogeler]
        tw = sum(ws) + 4
        self.dolgu(x, y, x + tw, y + h, dolgu, r=4)
        xx = x + 2
        for s, w in zip(ogeler, ws):
            if s == etkin:
                self.dolgu(xx, y + 2, xx + w, y + h - 2, KAGIT_ACIK, r=3)
                self.cerceve(xx, y + 2, xx + w, y + h - 2, ALTIN, r=3)
            self.yazi(xx + w / 2, y + h / 2 + boy * 0.36, s, boy, 500, METIN1 if s == etkin else METIN2, anchor='ms')
            xx += w
        return tw

    def anahtar(self, x, cy, on, w=28, h=14):
        if on:
            self.dolgu(x, cy - h / 2, x + w, cy + h / 2, ALTIN, r=h / 2)
            self.daire(x + w - h / 2, cy, h / 2 - 2.5, dolgu=KAGIT_ACIK)
        else:
            self.dolgu(x, cy - h / 2, x + w, cy + h / 2, KAGIT_KOYU, r=h / 2)
            self.cerceve(x, cy - h / 2, x + w, cy + h / 2, CIZGI_KOYU, r=h / 2)
            self.daire(x + h / 2, cy, h / 2 - 2.5, dolgu=METIN3)

    def onay(self, x, y, on, boy=14):
        if on:
            self.dolgu(x, y, x + boy, y + boy, ALTIN, r=3)
            self.ikon('onay', x + boy / 2, y + boy / 2, boy - 2, KAGIT_ACIK, 1.8)
        else:
            self.dolgu(x, y, x + boy, y + boy, KAGIT_ACIK, r=3)
            self.cerceve(x, y, x + boy, y + boy, CIZGI_KOYU, r=3)

    def radyo(self, cx, cy, on):
        self.daire(cx, cy, 6.5, dolgu=KAGIT_ACIK, kenar=ALTIN if on else CIZGI_KOYU, w=1)
        if on:
            self.daire(cx, cy, 3, dolgu=ALTIN)

    def dugme(self, x0, y0, x1, y1, metin, tur='ikincil', boy=12):
        if tur == 'birincil':
            self.dolgu(x0, y0, x1, y1, ANTRASIT, r=4)
            self.yazi((x0 + x1) / 2, (y0 + y1) / 2 + boy * 0.36, metin, boy, 500, KREM, anchor='ms')
        elif tur == 'ikincil':
            self.dolgu(x0, y0, x1, y1, KAGIT_ACIK, r=4)
            self.cerceve(x0, y0, x1, y1, CIZGI_KOYU, r=4)
            self.yazi((x0 + x1) / 2, (y0 + y1) / 2 + boy * 0.36, metin, boy, 500, METIN1, anchor='ms')
        else:
            self.yazi((x0 + x1) / 2, (y0 + y1) / 2 + boy * 0.36, metin, boy, 500, METIN2, anchor='ms')

    def yuzen(self, x0, y0, x1, y1, r=6, a=0.12):
        """Yüzen kart: gölge + açık kâğıt + kıl çerçeve."""
        self.yumusak_golge(x0, y0, x1, y1, r=r, yay=6, kay=2, a=a)
        self.dolgu(x0, y0, x1, y1, rgba(KAGIT_ACIK, 0.97), r=r)
        self.cerceve(x0, y0, x1, y1, CIZGI, r=r)


# ------------------------------------------------------------------ yapı modeli: Depo Binası – Tokat OSB
AKS_X = [0.0, 6.0, 12.0, 18.0]            # A–D
AKS_Y = [0.0, 6.0, 12.0, 18.0, 24.0]      # 1–5
KOTLAR = [0.0, 4.5, 9.0, 13.5]
KAT_AD = ['Zemin', 'Kat 1', 'Kat 2', 'Kat 3 (Çatı)']
AKS_X_AD = ['A', 'B', 'C', 'D']
AKS_Y_AD = ['1', '2', '3', '4', '5']


def i_kesit(b, h, tw, tf):
    return [(-b / 2, h / 2), (b / 2, h / 2), (b / 2, h / 2 - tf), (tw / 2, h / 2 - tf), (tw / 2, -h / 2 + tf), (b / 2, -h / 2 + tf),
            (b / 2, -h / 2), (-b / 2, -h / 2), (-b / 2, -h / 2 + tf), (-tw / 2, -h / 2 + tf), (-tw / 2, h / 2 - tf), (-b / 2, h / 2 - tf)]


def l_kesit(b, t):
    return [(-b / 2, -b / 2), (b / 2, -b / 2), (b / 2, -b / 2 + t), (-b / 2 + t, -b / 2 + t), (-b / 2 + t, b / 2), (-b / 2, b / 2)]


HE340A = i_kesit(0.300, 0.330, 0.0095, 0.0165)
IPE400 = i_kesit(0.180, 0.400, 0.0086, 0.0135)
IPE200 = i_kesit(0.100, 0.200, 0.0056, 0.0085)
L100 = l_kesit(0.100, 0.010)


def kap_ucgenleri(n):
    if n == 12:
        return [(0, 1, 2, 11), (10, 3, 4, 9), (8, 5, 6, 7)]
    if n == 6:
        return [(0, 1, 2, 3), (0, 3, 4, 5)]
    return [(0, 1, 2, 3)]


class Model:
    def __init__(self):
        self.uyeler = []
        self.kutular = []

    def uye(self, ad, tur, kat, p0, p1, kesit, vdir, kesit_ad):
        self.uyeler.append(dict(ad=ad, tur=tur, kat=kat, p0=np.array(p0, float), p1=np.array(p1, float), kesit=kesit,
                                vdir=np.array(vdir, float), kesit_ad=kesit_ad, secili=False, hover=False, dc=0.0))
        return self.uyeler[-1]

    def kutu(self, x0, y0, z0, x1, y1, z1):
        self.kutular.append((x0, y0, z0, x1, y1, z1))

    def bul(self, ad):
        for u in self.uyeler:
            if u['ad'] == ad:
                return u
        raise KeyError(ad)


def depo_binasi():
    """3 kat çelik endüstriyel bina: HE340A kolon, IPE400 kiriş, IPE200 aşık (çatı), L100×10 X çapraz, BA döşeme
    (ofis bölümü: 3–5 aksları arası, +4.50 ve +9.00)."""
    m = Model()
    bx, by = 0.150, 0.165
    for ix, x in enumerate(AKS_X):
        for iy, y in enumerate(AKS_Y):
            for k in range(3):
                m.uye('C%d-%s%s' % (k + 1, AKS_X_AD[ix], AKS_Y_AD[iy]), 'kolon', k + 1, (x, y, KOTLAR[k]), (x, y, KOTLAR[k + 1]),
                      HE340A, (0, 1, 0), 'HE340A')
    for k in (1, 2, 3):
        z = KOTLAR[k]
        zc = z - 0.200
        for iy, y in enumerate(AKS_Y):
            for i in range(len(AKS_X) - 1):
                ad = 'K%d-%s%s%s' % (k, AKS_Y_AD[iy], AKS_X_AD[i], AKS_X_AD[i + 1])
                m.uye(ad, 'kiris', k, (AKS_X[i] + bx, y, zc), (AKS_X[i + 1] - bx, y, zc), IPE400, (0, 0, 1), 'IPE400')
        for ix, x in enumerate(AKS_X):
            for j in range(len(AKS_Y) - 1):
                ad = 'K%d-%s%s%s' % (k, AKS_X_AD[ix], AKS_Y_AD[j], AKS_Y_AD[j + 1])
                m.uye(ad, 'kiris', k, (x, AKS_Y[j] + by, zc), (x, AKS_Y[j + 1] - by, zc), IPE400, (0, 0, 1), 'IPE400')
    # çatı aşıkları IPE200: Y yönünde, 2 m aralıklı, ana kirişlerin üstünde
    zc = 13.5 + 0.10
    n = 0
    for i in range(len(AKS_X) - 1):
        for dx in (2.0, 4.0):
            x = AKS_X[i] + dx
            for j in range(len(AKS_Y) - 1):
                n += 1
                m.uye('A3-%02d' % n, 'asik', 3, (x, AKS_Y[j] + 0.09, zc), (x, AKS_Y[j + 1] - 0.09, zc), IPE200, (0, 0, 1), 'IPE200')
    # döşemeler: ofis bölümü 3–5 aksları, +4.50 ve +9.00, 15 cm
    for z in (4.5, 9.0):
        for i in range(3):
            for j in (2, 3):
                m.kutu(AKS_X[i], AKS_Y[j], z, AKS_X[i + 1], AKS_Y[j + 1], z + 0.15)
    # X çaprazlar L100×10: A ve D cepheleri (1–2, 4–5 açıklıkları), 1 ve 5 cepheleri (B–C açıklığı)
    n = 0
    for k in range(3):
        z0, z1 = KOTLAR[k], KOTLAR[k + 1]
        for x in (0.0, 18.0):
            for (ya, yb) in ((0.0, 6.0), (18.0, 24.0)):
                n += 1; m.uye('X%d-%02d' % (k + 1, n), 'capraz', k + 1, (x, ya, z0), (x, yb, z1), L100, (1, 0, 0), 'L100×10')
                n += 1; m.uye('X%d-%02d' % (k + 1, n), 'capraz', k + 1, (x, yb, z0), (x, ya, z1), L100, (1, 0, 0), 'L100×10')
        for y in (0.0, 24.0):
            n += 1; m.uye('X%d-%02d' % (k + 1, n), 'capraz', k + 1, (6.0, y, z0), (12.0, y, z1), L100, (0, 1, 0), 'L100×10')
            n += 1; m.uye('X%d-%02d' % (k + 1, n), 'capraz', k + 1, (12.0, y, z0), (6.0, y, z1), L100, (0, 1, 0), 'L100×10')
    # D/C oranları (tasarım görünümü için deterministik, gerçekçi dağılım)
    for i, u in enumerate(m.uyeler):
        h = (i * 7919) % 97 / 97.0
        if u['tur'] == 'kolon':
            u['dc'] = 0.32 + 0.30 * h + (0.12 if u['kat'] == 1 else 0.0)
        elif u['tur'] == 'kiris':
            u['dc'] = 0.48 + 0.42 * h
        elif u['tur'] == 'asik':
            u['dc'] = 0.55 + 0.30 * h
        else:
            u['dc'] = 0.18 + 0.30 * h
    m.bul('K2-3BC')['dc'] = 0.87
    m.bul('K2-2BC')['dc'] = 0.93
    m.bul('K1-3BC')['dc'] = 1.04
    m.bul('K3-3BC')['dc'] = 0.71
    return m


SECILI_KIRISLER = ['K2-2AB', 'K2-2BC', 'K2-2CD', 'K2-3AB', 'K2-3BC', 'K2-3CD']


# ------------------------------------------------------------------ kamera ve yazılım görüntüleyici
class Kamera:
    def __init__(self, goz, hedef, fov_derece, W, H):
        self.goz = np.array(goz, float)
        f = np.array(hedef, float) - self.goz
        self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, np.array([0, 0, 1.0]))
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.W, self.H = W, H
        self.odak = (H / 2.0) / math.tan(math.radians(fov_derece) / 2.0)

    def izdusum(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        d = P - self.goz
        xc, yc, zc = d @ self.r, d @ self.u, d @ self.f
        zc = np.maximum(zc, 1e-3)
        return self.W / 2.0 + xc / zc * self.odak, self.H / 2.0 - yc / zc * self.odak, zc


def normalize(v):
    return v / np.linalg.norm(v)


def disbukey(pts):
    pts = sorted(set((round(x, 5), round(y, 5)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    alt, ust = [], []
    for p in pts:
        while len(alt) >= 2 and cr(alt[-2], alt[-1], p) <= 0:
            alt.pop()
        alt.append(p)
    for p in reversed(pts):
        while len(ust) >= 2 and cr(ust[-2], ust[-1], p) <= 0:
            ust.pop()
        ust.append(p)
    return alt[:-1] + ust[:-1]


def ucgenler_uret(model, isik, kip):
    """Tüm üyeleri üçgenlere ayırır. Yüz kimliği → üye bayrakları (seçili/hover) ayrı dizilerde döner."""
    V, C, I = [], [], []
    yuz_sec, yuz_hov = [False], [False]     # yüz 0 = boş
    golge_cokgenler = []
    yuz = 0

    def golgele(n, taban, secili):
        n = normalize(n)
        dif = max(0.0, float(n @ isik))
        gok = 0.5 * (1.0 + n[2])
        if secili:
            s = 0.74 + 0.18 * dif + 0.10 * gok
        else:
            s = 0.63 + 0.27 * dif + 0.13 * gok
        return tuple(min(255.0, c * s) for c in taban)

    def ekle(a, b, c, n, taban, secili, yid):
        V.append((a, b, c)); C.append(golgele(n, taban, secili)); I.append(yid)

    def yeni_yuz(u):
        nonlocal yuz
        yuz += 1
        yuz_sec.append(bool(u['secili'])); yuz_hov.append(bool(u['hover']))
        return yuz

    for u in model.uyeler:
        p0, p1 = u['p0'], u['p1']
        if kip == 'dc':
            taban = karisim(DC_RENK[dc_sinif(u['dc'])], BEYAZ, 0.22)
        elif u['secili']:
            taban = SECIM_DOLGU
        else:
            taban = CELIK
        t = normalize(p1 - p0)
        v = u['vdir'] - t * (u['vdir'] @ t)
        v = normalize(v)
        w = np.cross(v, t)
        pts = u['kesit']
        n = len(pts)
        alan = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
        yon = 1.0 if alan > 0 else -1.0
        P0 = [p0 + w * a + v * b for a, b in pts]
        P1 = [p1 + w * a + v * b for a, b in pts]
        for i in range(n):
            j = (i + 1) % n
            du, dv = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            nrm = (w * dv - v * du) * yon
            yid = yeni_yuz(u)
            ekle(P0[i], P0[j], P1[j], nrm, taban, u['secili'], yid)
            ekle(P0[i], P1[j], P1[i], nrm, taban, u['secili'], yid)
        for Pk, nrm in ((P0, -t), (P1, t)):
            yid = yeni_yuz(u)
            for (a, b, c, d) in kap_ucgenleri(n):
                ekle(Pk[a], Pk[b], Pk[c], nrm, taban, u['secili'], yid)
                ekle(Pk[a], Pk[c], Pk[d], nrm, taban, u['secili'], yid)
        golge_cokgenler.append(P0 + P1)
    bos = dict(secili=False, hover=False)
    for (x0, y0, z0, x1, y1, z1) in model.kutular:
        c = {}
        for ix, x in enumerate((x0, x1)):
            for iy, y in enumerate((y0, y1)):
                for iz, z in enumerate((z0, z1)):
                    c[(ix, iy, iz)] = np.array((x, y, z))
        yuzler = [(((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)), (0, 0, 1)), (((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)), (0, 0, -1)),
                  (((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), (0, -1, 0)), (((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)), (0, 1, 0)),
                  (((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)), (-1, 0, 0)), (((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)), (1, 0, 0))]
        taban = karisim(BETON, BEYAZ, 0.3) if kip == 'dc' else BETON
        for (k, nrm) in yuzler:
            yid = yeni_yuz(bos)
            a, b, cc, d = (c[q] for q in k)
            ekle(a, b, cc, np.array(nrm, float), taban, False, yid)
            ekle(a, cc, d, np.array(nrm, float), taban, False, yid)
        golge_cokgenler.append(list(c.values()))
    return np.array(V), np.array(C), np.array(I), np.array(yuz_sec), np.array(yuz_hov), golge_cokgenler


def rasterize(sx, sy, iz, renkler, idler, W, H):
    zb = np.zeros((H, W), np.float32)
    idb = np.zeros((H, W), np.int32)
    cb = np.zeros((H, W, 3), np.float32)
    n = len(idler)
    for k in range(n):
        x0, x1, x2 = sx[k]
        y0, y1, y2 = sy[k]
        xmin = int(max(0, math.floor(min(x0, x1, x2))))
        xmax = int(min(W - 1, math.ceil(max(x0, x1, x2))))
        ymin = int(max(0, math.floor(min(y0, y1, y2))))
        ymax = int(min(H - 1, math.ceil(max(y0, y1, y2))))
        if xmin > xmax or ymin > ymax:
            continue
        alan = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        if abs(alan) < 1e-9:
            continue
        X = np.arange(xmin, xmax + 1, dtype=np.float32) + 0.5
        Y = (np.arange(ymin, ymax + 1, dtype=np.float32) + 0.5)[:, None]
        e0 = (x1 - x0) * (Y - y0) - (y1 - y0) * (X - x0)
        e1 = (x2 - x1) * (Y - y1) - (y2 - y1) * (X - x1)
        e2 = (x0 - x2) * (Y - y2) - (y0 - y2) * (X - x2)
        if alan < 0:
            e0, e1, e2, alan = -e0, -e1, -e2, -alan
        icinde = (e0 >= 0) & (e1 >= 0) & (e2 >= 0)
        if not icinde.any():
            continue
        z = (e1 * iz[k][0] + e2 * iz[k][1] + e0 * iz[k][2]) / alan
        alt = zb[ymin:ymax + 1, xmin:xmax + 1]
        g = icinde & (z > alt)
        if not g.any():
            continue
        alt[g] = z[g]
        idb[ymin:ymax + 1, xmin:xmax + 1][g] = idler[k]
        cb[ymin:ymax + 1, xmin:xmax + 1][g] = renkler[k]
    return zb, idb, cb


def fark(a, kalin):
    e = np.zeros(a.shape, bool)
    for s in range(1, kalin + 1):
        e |= a != np.roll(a, s, axis=0)
        e |= a != np.roll(a, s, axis=1)
    return e


_GORUNUM_ONBELLEK = {}


class Gorunum:
    """Görünüm penceresi içeriği: beyaz→açık gri gradyan, zemin paftası ve 1 m ızgara, yumuşak gölge, z-tamponlu
    ekstrüzyon modeli, kenar çizgileri (seçili: altın, üzerine gelinen: kahverengi)."""

    def __init__(self, model, vw, vh, S, kip='normal', kamera=None):
        self.model, self.vw, self.vh, self.S, self.kip = model, vw, vh, S, kip
        self.Q = 1 if HIZLI else 2
        self.W, self.H = vw * S * self.Q, vh * S * self.Q
        goz, hedef, fov = kamera or ((-27.5, -32.0, 20.0), (10.2, 13.0, 5.6), 29.5)
        self.kam = Kamera(goz, hedef, fov, self.W, self.H)
        self.isik = normalize(np.array([-0.45, -0.35, 0.82]))

    def ekran(self, p):
        sx, sy, _ = self.kam.izdusum(p)
        k = self.S * self.Q
        return float(sx[0]) / k, float(sy[0]) / k

    def ciz(self):
        key = (self.vw, self.vh, self.S, self.kip, HIZLI, tuple(self.kam.goz))
        im = _GORUNUM_ONBELLEK.get(key)
        if im is None:
            im = self._ciz()
            _GORUNUM_ONBELLEK[key] = im
        return im

    def _ciz(self):
        W, H, k = self.W, self.H, self.S * self.Q
        # --- gradyan arka plan
        g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        zemin = np.array(GOK_UST, np.float32) * (1 - g) + np.array(GOK_ALT, np.float32) * g
        zemin = np.repeat(zemin, W, axis=1)
        pafta = Image.fromarray(zemin.astype(np.uint8))
        d = ImageDraw.Draw(pafta)
        # --- zemin paftası ve 1 m ızgara
        X0, X1, Y0, Y1 = -7.0, 25.0, -7.0, 31.0
        kose = [(X0, Y0, 0), (X1, Y0, 0), (X1, Y1, 0), (X0, Y1, 0)]
        sx, sy, _ = self.kam.izdusum(kose)
        d.polygon(list(zip(sx, sy)), fill=PAFTA_ZEMIN)
        inc = max(1, int(round(0.5 * k)))
        for x in range(int(X0), int(X1) + 1):
            a, b, _ = self.kam.izdusum([(x, Y0, 0), (x, Y1, 0)])
            d.line([(a[0], b[0]), (a[1], b[1])], fill=karisim(PAFTA_ZEMIN, ANTRASIT, 0.055 if x % 6 else 0.10), width=inc)
        for y in range(int(Y0), int(Y1) + 1):
            a, b, _ = self.kam.izdusum([(X0, y, 0), (X1, y, 0)])
            d.line([(a[0], b[0]), (a[1], b[1])], fill=karisim(PAFTA_ZEMIN, ANTRASIT, 0.055 if y % 6 else 0.10), width=inc)
        d.polygon(list(zip(sx, sy)), outline=karisim(PAFTA_ZEMIN, ANTRASIT, 0.22), width=max(1, int(round(0.75 * k))))
        # --- üçgenler ve yumuşak gölgeler
        V, C, I, yuz_sec, yuz_hov, golgeler = ucgenler_uret(self.model, self.isik, self.kip)
        gol = Image.new('L', (W, H), 0)
        gd = ImageDraw.Draw(gol)
        l = self.isik
        for cok in golgeler:
            duz = []
            for p in cok:
                s = p[2] / l[2]
                duz.append((p[0] - l[0] * s, p[1] - l[1] * s))
            h = disbukey(duz)
            if len(h) >= 3:
                a, b, _ = self.kam.izdusum([(x, y, 0) for x, y in h])
                gd.polygon(list(zip(a, b)), fill=255)
        gol = gol.filter(ImageFilter.GaussianBlur(2.5 * k))
        zemin = np.asarray(pafta, np.float32)
        gm = np.asarray(gol, np.float32)[:, :, None] / 255.0
        zemin = zemin * (1.0 - 0.11 * gm)
        # --- aks çizgileri (zeminde, kesik-noktalı)
        aks_lay = Image.new('L', (W, H), 0)
        ad = ImageDraw.Draw(aks_lay)
        inc2 = max(1, int(round(0.6 * k)))
        for x in AKS_X:
            self._kesikli(ad, (x, -3.2, 0), (x, 26.5, 0), inc2)
        for y in AKS_Y:
            self._kesikli(ad, (-3.2, y, 0), (20.5, y, 0), inc2)
        a = np.asarray(aks_lay, np.float32)[:, :, None] / 255.0 * 0.45
        zemin = zemin * (1 - a) + np.array(ANTRASIT, np.float32) * a
        # --- üyeler: z-tampon
        P = V.reshape(-1, 3)
        sx, sy, zc = self.kam.izdusum(P)
        sx = sx.reshape(-1, 3); sy = sy.reshape(-1, 3); iz = (1.0 / zc).reshape(-1, 3)
        zb, idb, cb = rasterize(sx, sy, iz, C, I, W, H)
        ortu = idb > 0
        z = np.where(ortu, 1.0 / np.maximum(zb, 1e-6), 0.0)
        zmin, zmax = z[ortu].min(), z[ortu].max()
        sis = np.where(ortu, (z - zmin) / max(1e-6, zmax - zmin), 0)[:, :, None] * 0.20
        cb = cb * (1 - sis) + np.array(GOK_ALT, np.float32) * sis
        img = np.where(ortu[:, :, None], cb, zemin)
        # --- kenar çizgileri: yüz kimliği değişen pikseller (ince, koyu)
        kalin = max(1, int(round(0.75 * k)))
        kenar = fark(idb, kalin) & (ortu | np.roll(ortu, -kalin, axis=0) | np.roll(ortu, -kalin, axis=1))
        ka = kenar[:, :, None] * 0.52
        img = img * (1 - ka) + np.array(ANTRASIT, np.float32) * ka
        # --- üzerine gelme: ince kahverengi kontur
        hov = yuz_hov[idb]
        if hov.any():
            e = fark(np.where(hov, idb, 0), max(1, int(round(0.9 * k))))
            e &= (hov | np.roll(hov, -1, 0) | np.roll(hov, -1, 1))
            ea = e[:, :, None] * 0.95
            img = img * (1 - ea) + np.array(KAHVE, np.float32) * ea
        # --- seçim: altın kontur (dış siluet + yüz kenarları)
        sec = yuz_sec[idb]
        if sec.any():
            e = fark(np.where(sec, idb, 0), max(1, int(round(1.5 * k))))
            ea = e[:, :, None] * 1.0
            img = img * (1 - ea) + np.array(ALTIN, np.float32) * ea
        out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        if self.Q != 1:
            out = out.resize((self.vw * self.S, self.vh * self.S), Image.LANCZOS)
        return out

    def _kesikli(self, d, a, b, inc):
        a, b = np.array(a, float), np.array(b, float)
        L = np.linalg.norm(b - a)
        t = (b - a) / L
        s = 0.0
        desen = [(0.9, True), (0.25, False), (0.12, True), (0.25, False)]
        i = 0
        while s < L:
            ln, ciz = desen[i % 4]
            e = min(L, s + ln)
            if ciz:
                p, q, _ = self.kam.izdusum([a + t * s, a + t * e])
                d.line([(p[0], q[0]), (p[1], q[1])], fill=255, width=inc)
            s = e
            i += 1


# ------------------------------------------------------------------ arayüz ölçüleri (mantıksal px, 8'lik ızgara)
BASLIK_H = 36
SEKME_H = 30
SERIT_H = 84          # şerit toplamı 114 px
KOMUT_H = 30
DURUM_H = 26
STRIP_W = 36
DOCK_H = 224          # sonuç tablo bölmesi
LEJANT_H = 30


def yerlesim(W, H, kucuk=False, kip='ana'):
    L = dict(W=W, H=H, kucuk=kucuk, kip=kip)
    L['sol'] = STRIP_W if kucuk else 300
    L['sag'] = 280 if kucuk else 320
    L['ust'] = BASLIK_H + SEKME_H + SERIT_H           # 150
    L['alt'] = H - DURUM_H - KOMUT_H                   # panellerin alt sınırı
    vp_alt = L['alt']
    if kip == 'sonuc':
        vp_alt = L['alt'] - DOCK_H - LEJANT_H
    L['vp'] = (L['sol'], L['ust'], W - L['sag'] - STRIP_W, vp_alt)
    return L


# --- şerit tanımları ----------------------------------------------------------------------------------------------
SERIT_SEKMELER = ['Dosya', 'Model', 'Düzenle', 'Yükler', 'Analiz', 'Tasarım', 'Görünüm', 'Raporlar']
SERIT = {
    'Model': [
        ('Aks & Kat', [('aks', 'Aks\nsistemi', False), ('kat', 'Kat\nverisi', False)],
         [('plan', 'Plan: Kat 2', True), ('yukselti', 'Yükselti…', True), ('referans', 'Referans düzlemi', False)]),
        ('Kolon', [('kolon', 'Kolon', False)], [('kesit_k', 'HE340A', True), ('kot', 'Alt / Üst kot', False), ('dondur', 'Döndür', False)]),
        ('Kiriş', [('kiris', 'Kiriş', False)], [('kesit_k', 'IPE400', True), ('tali', 'Tali kiriş', False), ('serbestlik', 'Mafsal – Mafsal', True)]),
        ('Çapraz', [('capraz', 'Çapraz', False)], [('kesit_k', 'L100×10', True), ('xvk', 'X / V / K', True)]),
        ('Döşeme', [('doseme', 'Döşeme', False)], [('kalinlik', '15 cm BA', True), ('bosluk', 'Boşluk', False)]),
        ('Duvar', [('duvar', 'Duvar', False)], []),
        ('Temel', [('temel', 'Temel', False)], [('tekil', 'Tekil', False), ('surekli', 'Sürekli', False), ('radye', 'Radye', False)]),
        ('Hızlı kolon / kiriş', [('hizli_kolon', 'Hızlı\nkolon', False), ('hizli_kiris', 'Hızlı\nkiriş', False)], []),
        ('Seç', [('sec', 'Seç', True), ('suz', 'Seç ve\nSüz', False)],
         [('benzer', 'Benzerini seç', False), ('ters', 'Tersine çevir', False), ('grup', 'Gruplar…', False)]),
    ],
    'Tasarım': [
        ('Yönetmelik', [('yonetmelik', 'TS EN\n1993', False)],
         [('tercih', 'Tercihler…', False), ('komb', 'Kombinasyonlar', False), ('grup', 'Tasarım grupları', False)]),
        ('Tasarım', [('basla', 'Tasarımı\nbaşlat', False), ('kontrol', 'Kontrol\net', False)],
         [('secili', 'Yalnız seçili', False), ('yinele', 'Yinele', False), ('kilit', 'Kesitleri kilitle', False)]),
        ('Göster', [('dc', 'D/C\noranı', True), ('pm', 'P–M\noranı', False), ('ayrinti', 'Ayrıntı', False)],
         [('renk', 'Eşikler…', False), ('etiket', 'Değerleri yaz', False), ('temizle', 'Gösterimi temizle', False)]),
        ('Sonuçlar', [('deform', 'Şekil\ndeğiştirme', False), ('diyagram', 'N / V / M', False), ('reaksiyon', 'Reaksiyon', False)],
         [('komb', 'Zarf (12 komb.)', True), ('olcek', 'Ölçek: Otomatik', True), ('anim', 'Animasyon', False)]),
        ('Tablolar', [('tablo', 'Tablo\nseç', False), ('rapor', 'Rapor', False)],
         [('tablo_disa', 'CSV’ye aktar', False), ('kume', 'Tablo kümeleri', False)]),
    ],
}
BUYUK_W = 68


def grup_genislik(t, grup, dar):
    ad, buyuk, kucuk = grup
    w = 24 + BUYUK_W * len(buyuk)
    if kucuk and not dar:
        w += 8 + 22 + max(t.gen(s, 11.5) + (14 if m else 0) for _, s, m in kucuk) + 10
    return max(w, t.gen(ad, 10, 500) * 1.12 + 24)


def ciz_baslik(t, L, simge):
    W = L['W']
    t.dolgu(0, 0, W, BASLIK_H, KAGIT_KOYU)
    t.yatay(0, W, BASLIK_H - 1, CIZGI)
    lw = t.resim(simge, 14, 9, 18)
    t.yazi(14 + lw + 8, 23.5, 'op4', 13, 500, METIN1)
    x = 14 + lw + 8 + t.gen('op4', 13, 500) + 14
    t.dikey(x, 10, 26, CIZGI_KOYU)
    x += 12
    for ad in ('yeni', 'ac', 'kaydet'):
        t.ikon(ad, x + 8, 18, 16, METIN2, 1.5)
        x += 30
    t.dikey(x - 6, 10, 26, CIZGI_KOYU)
    x += 6
    for ad in ('geri', 'yinele'):
        t.ikon(ad, x + 8, 18, 16, METIN2, 1.5)
        x += 30
    # belge adı: pafta başlığı gibi serifli
    ad = 'Depo Binası – Tokat OSB'
    w1 = t.gen(ad, 19, 600, 'cormorant'); w2 = t.gen('.op4', 12, 400)
    cx = W / 2 - (w1 + w2 + 6) / 2
    t.yazi(cx, 24.5, ad, 19, 600, METIN1, ad='cormorant')
    t.yazi(cx + w1 + 6, 23.5, '.op4', 12, 400, METIN3)
    t.daire(cx - 12, 19, 2.5, dolgu=ALTIN)        # kaydedilmemiş değişiklik
    # sağ: dil ve pencere düğmeleri
    bx = W - 3 * 46
    for i, ad in enumerate(('kucult', 'buyut', 'kapat')):
        t.ikon(ad, bx + 46 * i + 23, 18, 14, METIN2, 1.25)
    t.yazi(bx - 20, 22.5, 'TR', 10.5, 500, METIN3, anchor='rs')
    t.dikey(bx - 8, 10, 26, CIZGI_KOYU)


def ciz_sekmeler(t, L, etkin='Model'):
    W = L['W']
    y0, y1 = BASLIK_H, BASLIK_H + SEKME_H
    t.dolgu(0, y0, W, y1, KAGIT)
    t.yatay(0, W, y1 - 1, CIZGI)
    x = 16
    for ad in SERIT_SEKMELER:
        on = (ad == etkin)
        if ad == 'Dosya':
            w = t.gen(ad, 13, 500)
            t.dolgu(x - 8, y0 + 4, x + w + 8, y1 - 5, KAHVE, r=3)
            t.yazi(x, y0 + 20, ad, 13, 500, KREM)
            x += w + 30
            continue
        renk = METIN1 if on else METIN2
        w = t.yazi(x, y0 + 20, ad, 13, 500 if on else 450, renk)
        if on:
            t.dolgu(x - 1, y1 - 3, x + w + 1, y1 - 1, ALTIN)
        x += w + 26
    t.ikon('bilgi', W - 24 - 32, y0 + 15, 16, METIN2, 1.4)
    t.ikon('chev_u', W - 24, y0 + 15, 14, METIN2, 1.5)


def ciz_serit(t, L, sekme='Model'):
    W = L['W']
    y0 = BASLIK_H + SEKME_H
    y1 = y0 + SERIT_H
    t.dolgu(0, y0, W, y1, KAGIT)
    t.yatay(0, W, y1 - 1, CIZGI)
    gruplar = SERIT[sekme]
    dar = False
    genislikler = [grup_genislik(t, g, dar) for g in gruplar]
    if sum(genislikler) + 32 > W:
        dar = True
        genislikler = [grup_genislik(t, g, dar) for g in gruplar]
    x = 16
    for gi, (ad, buyuk, kucuk) in enumerate(gruplar):
        gx0 = x
        gw = genislikler[gi]
        bx = gx0 + 12
        for (ik, etiket, etkin) in buyuk:
            if etkin:
                t.dolgu(bx, y0 + 6, bx + BUYUK_W, y0 + 64, ALTIN_ACIK, r=4)
                t.cerceve(bx, y0 + 6, bx + BUYUK_W, y0 + 64, ALTIN_ORTA, r=4)
            t.ikon(ik, bx + BUYUK_W / 2, y0 + 26, 30, METIN1, 1.5)
            satirlar = etiket.split('\n')
            if len(satirlar) == 1:
                t.yazi(bx + BUYUK_W / 2, y0 + 55, etiket, 11, 450, METIN1, anchor='ms')
            else:
                t.yazi(bx + BUYUK_W / 2, y0 + 50, satirlar[0], 11, 450, METIN1, anchor='ms')
                t.yazi(bx + BUYUK_W / 2, y0 + 62, satirlar[1], 11, 450, METIN1, anchor='ms')
            bx += BUYUK_W
        if kucuk and not dar:
            bx += 8
            for r, (ik, s, menu) in enumerate(kucuk):
                yy = y0 + 8 + r * 20
                t.ikon(ik, bx + 9, yy + 10, 15, METIN2, 1.4)
                w = t.yazi(bx + 22, yy + 14.5, s, 11.5, 400, METIN1)
                if menu:
                    t.ikon('chev_d', bx + 22 + w + 8, yy + 10, 9, METIN3, 1.5)
        # grup adı (harf aralıklı küçük başlık) ve kıl ayırıcı
        t.aralikli(gx0 + gw / 2, y1 - 8, ad.upper(), 9, 500, METIN3, 1.1, anchor='m')
        x = gx0 + gw
        if gi < len(gruplar) - 1:
            t.dikey(x, y0 + 10, y1 - 10, CIZGI)
        x += 1


# --- model ağacı ----------------------------------------------------------------------------------------------------
def agac_satirlari(kip):
    S = (kip != 'sonuc')
    return [
        (0, 'yapi', 'Depo Binası – Tokat OSB', '', '', 'd', False),
        (1, 'aks', 'Aks sistemi', 'A–D × 1–5', '', 'r', False),
        (1, 'kat', 'Katlar', '4 kot', '', 'd', False),
        (2, 'kat', 'Kat 3 (Çatı)', '+13.50', '87', 'r', False),
        (2, 'kat', 'Kat 2', '+9.00', '69', 'd', False),
        (3, 'kolon', 'Kolonlar', 'HE340A', '20', 'r', False),
        (3, 'kiris', 'Kirişler', 'IPE400', '31', 'd', False),
        (4, 'nokta', 'K2-2AB', 'Aks 2 · A–B', '', '', S),
        (4, 'nokta', 'K2-2BC', 'Aks 2 · B–C', '', '', S),
        (4, 'nokta', 'K2-2CD', 'Aks 2 · C–D', '', '', S),
        (4, 'nokta', 'K2-3AB', 'Aks 3 · A–B', '', '', S),
        (4, 'nokta', 'K2-3BC', 'Aks 3 · B–C', '', '', True),
        (4, 'nokta', 'K2-3CD', 'Aks 3 · C–D', '', '', S),
        (4, 'ucnokta', '25 kiriş daha', '', '', '', False),
        (3, 'capraz', 'Çaprazlar', 'L100×10', '12', 'r', False),
        (3, 'doseme', 'Döşemeler', '15 cm BA', '6', 'r', False),
        (2, 'kat', 'Kat 1', '+4.50', '69', 'r', False),
        (2, 'kat', 'Zemin', '±0.00', '20', 'r', False),
        (1, 'katalog', 'Kütüphaneler', 'kesit · malzeme', '', 'd', False),
        (2, 'kesit_k', 'Kesitler', 'HE340A · IPE400 · …', '4', '', False),
        (2, 'yonetmelik', 'Malzemeler', 'S355 · C30/37', '2', '', False),
        (1, 'yuk', 'Yükler', '', '', 'd', False),
        (2, 'komb', 'Yük desenleri', 'G · Q · W · E', '4', '', False),
        (2, 'komb', 'Kombinasyonlar', 'TS EN 1990', '12', '', False),
        (1, 'grup', 'Gruplar', 'Kat 2 çerçevesi · …', '3', 'r', False),
    ]


def ciz_panel_basligi(t, x0, x1, y, ad, ikonlar):
    t.yazi(x0 + 16, y + 23, ad, 12.5, 600, METIN1)
    xx = x1 - 12
    for ik in reversed(ikonlar):
        t.ikon(ik, xx - 8, y + 18, 16, METIN2, 1.4)
        xx -= 26
    t.yatay(x0, x1, y + 35, CIZGI_SOLUK)


def ciz_arama(t, x0, x1, y, metin):
    t.dolgu(x0, y, x1, y + 28, KAGIT_ACIK, r=4)
    t.cerceve(x0, y, x1, y + 28, CIZGI, r=4)
    t.ikon('ara', x0 + 14, y + 14, 14, METIN3, 1.4)
    t.yazi(x0 + 28, y + 18.5, metin, 12, 400, METIN3)


def ciz_agac(t, L):
    x0, x1 = 0, L['sol']
    y0, y1 = L['ust'], L['alt']
    kip = L['kip']
    t.dolgu(x0, y0, x1, y1, KAGIT)
    t.dikey(x1 - 1, y0, y1, CIZGI)
    # panel başlığı + sekmeler: Model / Göster / Tablolar / Raporlar
    t.yazi(x0 + 16, y0 + 23, 'Model ağacı', 12.5, 600, METIN1)
    t.ikon('pin', x1 - 36, y0 + 18, 16, METIN2, 1.4)
    t.ikon('sol2', x1 - 16, y0 + 18, 16, METIN2, 1.4)
    t.yatay(x0, x1, y0 + 35, CIZGI_SOLUK)
    y = y0 + 36
    xx = x0 + 16
    for ad in ('Model', 'Göster', 'Tablolar', 'Raporlar'):
        on = (ad == 'Model')
        w = t.yazi(xx, y + 19, ad, 11.5, 500 if on else 450, METIN1 if on else METIN2)
        if on:
            t.dolgu(xx - 1, y + 26, xx + w + 1, y + 28, ALTIN)
        xx += w + 18
    t.yatay(x0, x1, y + 28, CIZGI)
    y += 36
    ciz_arama(t, x0 + 12, x1 - 12, y, 'Ağaçta ara: kat, tür, etiket')
    y += 40
    RH = 24
    for (lvl, ik, ad, alt, adet, acik, secili) in agac_satirlari(kip):
        if secili:
            t.dolgu(x0 + 1, y, x1 - 1, y + RH, ALTIN_ACIK)
            t.dolgu(x0 + 1, y, x0 + 3, y + RH, ALTIN)
        xx = x0 + 14 + lvl * 14
        if acik:
            t.ikon('chev_d' if acik == 'd' else 'chev_r', xx + 5, y + RH / 2, 10, METIN3, 1.6)
        xx += 14
        t.ikon(ik, xx + 8, y + RH / 2, 15 if ik not in ('nokta', 'ucnokta') else 12, METIN2 if lvl else METIN1, 1.4)
        xx += 22
        w = t.yazi(xx, y + RH / 2 + 4.5, ad, 12, 500 if lvl <= 2 and ik != 'nokta' else 400, METIN1 if ik != 'ucnokta' else METIN3)
        if alt:
            t.yazi(xx + w + 6, y + RH / 2 + 4.5, alt, 11, 400, METIN3)
        if adet:
            t.yazi(x1 - 40, y + RH / 2 + 4.5, adet, 11, 400, METIN3, anchor='rs')
        if lvl == 2 and ik == 'kat':
            t.ikon('goz', x1 - 22, y + RH / 2, 14, METIN3, 1.3)
        y += RH
    # alt bilgi
    t.yatay(x0, x1, y1 - 36, CIZGI_SOLUK)
    t.daire(x0 + 20, y1 - 18, 3, dolgu=ALTIN)
    n = '1 seçili' if kip == 'sonuc' else '6 seçili'
    t.yazi(x0 + 30, y1 - 13.5, n, 12, 500, METIN1)
    t.yazi(x0 + 30 + t.gen(n, 12, 500) + 6, y1 - 13.5, '· 245 nesne · 4 kat', 12, 400, METIN3)
    t.yazi(x1 - 16, y1 - 13.5, 'Seçiliye git', 11, 500, KAHVE, anchor='rs')


def ciz_sol_strip(t, L):
    x0, x1 = 0, STRIP_W
    y0, y1 = L['ust'], L['alt']
    t.dolgu(x0, y0, x1, y1, KAGIT)
    t.dikey(x1 - 1, y0, y1, CIZGI)
    t.ikon('sag2', 18, y0 + 18, 16, METIN2, 1.4)
    t.yatay(8, 28, y0 + 36, CIZGI_SOLUK)
    y = y0 + 48
    for ik, ad, etkin in (('agac', 'Model ağacı', True), ('goz', 'Göster', False), ('tablo', 'Tablolar', False), ('rapor', 'Raporlar', False)):
        h = 24 + t.gen(ad, 11, 500) + 24
        if etkin:
            t.dolgu(x0 + 1, y, x1 - 1, y + h, KAGIT_ACIK)
            t.dolgu(x1 - 3, y, x1 - 1, y + h, ALTIN)
        t.ikon(ik, 18, y + 16, 16, METIN1 if etkin else METIN2, 1.4)
        t.dikey_yazi(18, y + 28 + (h - 40) / 2, ad, 11, 500, METIN1 if etkin else METIN2)
        y += h + 8


# --- özellikler -----------------------------------------------------------------------------------------------------
def ozellik_bolumleri(kip, kucuk):
    sec = (kip == 'sonuc')
    genel = [('Tür', 'Kiriş', ''), ('Etiket', 'K2-3BC' if sec else 'K2-2AB … K2-3CD', '' if sec else 'çoklu'),
             ('Kat', 'Kat 2 (+9.00)', 'menu'), ('Ad', 'Ana kiriş', ''), ('Sınıf', '3', 'sinif')]
    kesit = [('Kesit', 'IPE400', 'katalog'), ('Malzeme', 'S355', 'katalog'), ('Döndürme', 'Üst · 0°', 'menu')]
    konum = [('Düzlemde', 'Orta', 'menu'), ('Derinlikte', 'Orta', 'menu'), ('Uç ofseti', '0,000 / 0,000 m', ''), ('Uzunluk', '6,000 m', 'soluk')]
    serb = [('● Başlangıç', 'Mafsal', 'menu_bas'), ('● Bitiş', 'Mafsal', 'menu_bit'), ('Serbest', 'M2 · M3', 'cip')]
    if kucuk:
        genel = genel[:4]; konum = konum[:3]
    b = [('GENEL', True, genel, ''), ('KESİT', True, kesit, ''), ('KONUM', True, konum, ''), ('SERBESTLİKLER', True, serb, '')]
    if sec:
        b = [('GENEL', True, genel[:3], ''), ('KESİT', True, kesit[:2], ''), ('KONUM', False, [], '6,000 m · Orta / Orta'),
             ('SERBESTLİKLER', False, [], 'Mafsal – Mafsal'), ('YÜKLER', False, [], 'G 2,50 · Q 5,00 kN/m'), ('ANALİZ', False, [], 'Çubuk · 1 parça'),
             ('TASARIM', True, [('D/C oranı', '0,87', 'dc'), ('Kombinasyon', 'K12 · 1,35G + 1,5Q', ''), ('Eğilme (My)', '0,81', 'oran'),
                                ('Kesme (Vz)', '0,34', 'oran'), ('Yanal burkulma', '0,87', 'oran'), ('Sehim', 'L/312 ✓', ''),
                                ('Tasarım grubu', 'Kirişler', 'menu')], '')]
    else:
        b += [('YÜKLER', False, [], 'G 2,50 · Q 5,00 kN/m'), ('ANALİZ', False, [], 'Çubuk · Diyafram: Kat 2'), ('TASARIM', False, [], 'TS EN 1993 · Kirişler')]
    return b


def ciz_ozellikler(t, L):
    W = L['W']
    x0, x1 = W - STRIP_W - L['sag'], W - STRIP_W
    y0, y1 = L['ust'], L['alt']
    kucuk, kip = L['kucuk'], L['kip']
    t.dolgu(x0, y0, x1, y1, KAGIT)
    t.dikey(x0, y0, y1, CIZGI)
    ciz_panel_basligi(t, x0, x1, y0, 'Özellikler', ['ara', 'pin', 'sag2'])
    # seçim özeti
    y = y0 + 36
    t.dolgu(x0 + 1, y, x1, y + 56, KAGIT_ACIK)
    t.yatay(x0, x1, y + 56, CIZGI_SOLUK)
    t.daire(x0 + 22, y + 20, 3, dolgu=ALTIN)
    if kip == 'sonuc':
        t.yazi(x0 + 32, y + 24.5, 'Kiriş K2-3BC', 13, 600, METIN1)
        t.yazi(x0 + 32, y + 43, 'IPE400 · S355 · Kat 2 · Aks 3 · B–C', 11, 400, METIN2)
    else:
        t.yazi(x0 + 32, y + 24.5, '6 kiriş seçili', 13, 600, METIN1)
        t.yazi(x0 + 32, y + 43, 'IPE400 · S355 · Kat 2 · Σ 36,0 m', 11, 400, METIN2)
        sw = t.segment(x1 - 16 - 104, y + 12, ['Ortak', 'Tek tek'], 'Ortak', h=20, boy=10, pad=8)
    y += 57
    deg_x = x0 + (120 if kucuk else 134)
    for (baslik, acik, satirlar, ozet) in ozellik_bolumleri(kip, kucuk):
        t.ikon('chev_d' if acik else 'chev_r', x0 + 21, y + 14, 10, METIN3, 1.6)
        t.aralikli(x0 + 32, y + 18, baslik, 9.5, 600, METIN2, 1.0)
        if not acik:
            t.yazi(x1 - 16, y + 18, ozet, 10.5, 400, METIN3, anchor='rs')
        y += 28
        for (etiket, deger, tur) in satirlar:
            if tur.startswith('menu_'):
                t.daire(x0 + 36, y + 12, 3.5, dolgu=ALTIN if tur == 'menu_bas' else KAHVE)
                t.yazi(x0 + 46, y + 16.5, etiket[2:], 12, 400, METIN2)
                tur = 'menu'
            else:
                t.yazi(x0 + 32, y + 16.5, etiket, 12, 400, METIN2)
            if tur == 'katalog':
                t.alan(deg_x, y + 2, x1 - 40, y + 22, deger, boy=12, w=500)
                t.katalog_dugmesi(x1 - 36, y + 2, x1 - 12, y + 22)
            elif tur == 'sinif':
                t.alan(deg_x, y + 2, x1 - 12, y + 22, deger, menu=True)
                t.dolgu(deg_x + 26, y + 6, deg_x + 38, y + 18, hx('7FA7C9'), r=2)
            elif tur == 'cip':
                for i, c in enumerate(deger.split(' · ')):
                    cw = t.gen(c, 10.5, 500) + 14
                    cx = deg_x + i * (cw + 6)
                    t.dolgu(cx, y + 3, cx + cw, y + 21, ALTIN_ACIK, r=9)
                    t.cerceve(cx, y + 3, cx + cw, y + 21, ALTIN_ORTA, r=9)
                    t.yazi(cx + cw / 2, y + 16, c, 10.5, 500, METIN1, anchor='ms')
                t.ikon('arti', x1 - 22, y + 12, 12, METIN3, 1.5)
            elif tur == 'dc':
                t.alan(deg_x, y + 2, x1 - 12, y + 22, '', boy=12)
                r = float(deger.replace(',', '.'))
                bw = (x1 - 12 - deg_x - 16) - 44
                t.dolgu(deg_x + 8, y + 10, deg_x + 8 + bw, y + 14, KAGIT_KOYU, r=2)
                t.dolgu(deg_x + 8, y + 10, deg_x + 8 + bw * min(1.0, r), y + 14, DC_RENK[dc_sinif(r)], r=2)
                t.yazi(x1 - 18, y + 16.5, deger, 12, 600, METIN1, anchor='rs')
            elif tur == 'oran':
                t.alan(deg_x, y + 2, x1 - 12, y + 22, deger, boy=12, w=500)
                r = float(deger.replace(',', '.'))
                t.dolgu(x1 - 24, y + 8, x1 - 16, y + 16, DC_RENK[dc_sinif(r)], r=2)
            else:
                t.alan(deg_x, y + 2, x1 - 12, y + 22, deger, menu=(tur == 'menu'), soluk=(tur == 'soluk'), boy=12, w=500 if tur == 'menu' else 400)
                if tur == 'çoklu':
                    t.yazi(x1 - 20, y + 16.5, '6', 10, 500, METIN3, anchor='rs')
            y += 24
        y += 4
        t.yatay(x0 + 16, x1 - 12, y, CIZGI_SOLUK)
        y += 4
    # alt: uygula / al
    t.yatay(x0, x1, y1 - 44, CIZGI_SOLUK)
    t.dolgu(x0 + 1, y1 - 43, x1, y1, KAGIT)
    t.dugme(x0 + 16, y1 - 34, x0 + 92, y1 - 10, 'Uygula', 'birincil', 11.5)
    t.dugme(x0 + 100, y1 - 34, x0 + 150, y1 - 10, 'Al', 'ikincil', 11.5)
    t.anahtar(x1 - 16 - 28, y1 - 22, True, w=26, h=13)
    t.yazi(x1 - 16 - 28 - 8, y1 - 18, 'Anında uygula', 10.5, 400, METIN2, anchor='rs')
    # kesit önizlemesi (yer kalırsa)
    if y1 - 52 - y >= 104:
        ciz_kesit_onizleme(t, x0, x1, y1 - 52 - 100, y1 - 52)


def ciz_kesit_onizleme(t, x0, x1, y0, y1):
    t.dolgu(x0 + 16, y0, x1 - 12, y1, KAGIT_ACIK, r=4)
    t.cerceve(x0 + 16, y0, x1 - 12, y1, CIZGI, r=4)
    t.yazi(x0 + 28, y0 + 18, 'IPE400', 12, 600, METIN1)
    t.yazi(x0 + 28 + t.gen('IPE400', 12, 600) + 8, y0 + 18, 'S355 · A = 84,5 cm²', 10.5, 400, METIN3)
    t.yazi(x1 - 24, y0 + 18, 'Katalog ›', 10.5, 500, KAHVE, anchor='rs')
    H = (y1 - y0) - 36
    k = H / 0.400
    b, h, tw, tf = 0.180 * k, 0.400 * k, max(2.0, 0.0086 * k), 0.0135 * k
    cx, cy = x0 + 60, y0 + 28 + H / 2
    pts = [(cx - b / 2, cy - h / 2), (cx + b / 2, cy - h / 2), (cx + b / 2, cy - h / 2 + tf), (cx + tw / 2, cy - h / 2 + tf),
           (cx + tw / 2, cy + h / 2 - tf), (cx + b / 2, cy + h / 2 - tf), (cx + b / 2, cy + h / 2), (cx - b / 2, cy + h / 2),
           (cx - b / 2, cy + h / 2 - tf), (cx - tw / 2, cy + h / 2 - tf), (cx - tw / 2, cy - h / 2 + tf), (cx - b / 2, cy - h / 2 + tf)]
    t.cokgen(pts, dolgu=karisim(KAGIT_ACIK, ANTRASIT, 0.10))
    t.cizgi(pts + [pts[0]], ANTRASIT, 1.0)
    t.cizgi([(cx - b / 2 - 8, cy), (cx + b / 2 + 8, cy)], CIZGI_KOYU, 0.75)
    dx = cx + b / 2 + 24
    t.yazi(dx, cy - 18, 'h 400 · b 180', 10.5, 400, METIN2)
    t.yazi(dx, cy - 3, 'tw 8,6 · tf 13,5', 10.5, 400, METIN2)
    t.yazi(dx, cy + 12, 'Iy 23 130 cm⁴', 10.5, 400, METIN2)
    t.yazi(dx, cy + 27, 'Wpl,y 1 307 cm³', 10.5, 400, METIN2)


def ciz_sag_strip(t, L):
    """Yan panel iskeleti: tek çerçeve, çok pencere — etkin pencere altın vurgulu."""
    W = L['W']
    x0, x1 = W - STRIP_W, W
    y0, y1 = L['ust'], L['alt']
    t.dolgu(x0, y0, x1, y1, KAGIT)
    t.dikey(x0, y0, y1, CIZGI)
    y = y0 + 12
    for ik, ad, etkin in (('ozellik', 'Özellikler', True), ('katalog', 'Kataloglar', False), ('agac', 'Model ağacı', False),
                          ('filtre_gor', 'Filtre & görünürlük', False), ('sorgu', 'Sorgu', False)):
        h = 24 + t.gen(ad, 11, 500) + 24
        if etkin:
            t.dolgu(x0 + 1, y, x1, y + h, KAGIT_ACIK)
            t.dolgu(x0 + 1, y, x0 + 3, y + h, ALTIN)
        t.ikon(ik, x0 + 18, y + 16, 16, METIN1 if etkin else METIN2, 1.4)
        t.dikey_yazi(x0 + 18, y + 28 + (h - 40) / 2, ad, 11, 500, METIN1 if etkin else METIN2)
        if ad == 'Model ağacı':
            t.daire(x0 + 18, y + h - 8, 2, dolgu=METIN3)   # sol kenara yapıştırılmış
        y += h + 8


# --- görünüm penceresi ve üstündeki öğeler ---------------------------------------------------------------------------
def ciz_gorunum(t, L, model):
    vx0, vy0, vx1, vy1 = L['vp']
    vw, vh = vx1 - vx0, vy1 - vy0
    kip = L['kip']
    kam = ((-27.5, -32.0, 20.0), (10.2, 13.0, 4.3), 29.5) if L['kucuk'] else None
    g = Gorunum(model, vw, vh, t.S, 'dc' if kip == 'sonuc' else 'normal', kam)
    im = g.ciz()
    t.im.paste(im, (t.p(vx0), t.p(vy0)))

    def E(p):
        x, y = g.ekran(p)
        return (vx0 + x, vy0 + y)

    # aks balonları (zeminde)
    for x, ad in zip(AKS_X, AKS_X_AD):
        bx, by = E((x, -3.2, 0))
        t.daire(bx, by, 10, dolgu=KAGIT_ACIK, kenar=karisim(KAGIT_ACIK, ANTRASIT, 0.55), w=1)
        t.yazi(bx, by + 4, ad, 11, 500, METIN1, anchor='ms')
    for y, ad in zip(AKS_Y, AKS_Y_AD):
        bx, by = E((-3.2, y, 0))
        t.daire(bx, by, 10, dolgu=KAGIT_ACIK, kenar=karisim(KAGIT_ACIK, ANTRASIT, 0.55), w=1)
        t.yazi(bx, by + 4, ad, 11, 500, METIN1, anchor='ms')
    # kat seviye çizgileri ve kot etiketleri (A/1 köşesi)
    for z, ad in zip(KOTLAR, KAT_AD):
        a = E((18.4, 0.0, z)); b = E((21.0, 0.0, z)); c = E((21.0, 9.0, z))
        t.kesikli(b, c, karisim(KAGIT_ACIK, ANTRASIT, 0.30), 0.75, 6, 4)
        t.cizgi([a, b], karisim(KAGIT_ACIK, ANTRASIT, 0.5), 0.75)
        t.cokgen([(a[0], a[1]), (a[0] + 6, a[1] - 4), (a[0] + 6, a[1] + 4)], dolgu=KAGIT_ACIK, kenar=karisim(KAGIT_ACIK, ANTRASIT, 0.6))
        kot = ('%+.2f' % z) if z else '±0.00'
        w = t.gen(kot, 11, 600)
        t.yazi(b[0] + 8, b[1] - 3, kot, 11, 600, METIN1)
        t.yazi(b[0] + 8 + w + 6, b[1] - 3, ad, 11, 400, METIN2)
    if kip in ('ana', 'kat', 'secsuz'):
        # doğrudan değiştirme tutamaçları: K2-3BC (altın = başlangıç, kahverengi = bitiş), orta tutamaç, ölçü etiketi
        u = model.bul('K2-3BC')
        p0, p1 = E(u['p0']), E(u['p1'])
        pm = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        t.daire(p0[0], p0[1], 6, dolgu=ALTIN, kenar=KAGIT_ACIK, w=1.5)
        t.daire(p1[0], p1[1], 6, dolgu=KAHVE, kenar=KAGIT_ACIK, w=1.5)
        t.dolgu(pm[0] - 4, pm[1] - 4, pm[0] + 4, pm[1] + 4, KAGIT_ACIK, r=1)
        t.cerceve(pm[0] - 4, pm[1] - 4, pm[0] + 4, pm[1] + 4, ALTIN, r=1)
        # ölçü etiketi (doğrudan yazılabilir)
        ew = t.gen('6,000 m', 11, 500) + 16
        ex, ey = pm[0] - ew / 2, pm[1] + 14
        t.dolgu(ex, ey, ex + ew, ey + 20, rgba(KAGIT_ACIK, 0.96), r=3)
        t.cerceve(ex, ey, ex + ew, ey + 20, ALTIN, r=3)
        t.yazi(ex + ew / 2, ey + 14, '6,000 m', 11, 500, METIN1, anchor='ms')
        # bağlamsal mini araç çubuğu: seçimin sağ üstünde
        merkez = np.mean([E(model.bul(a)['p0']) for a in SECILI_KIRISLER] + [E(model.bul(a)['p1']) for a in SECILI_KIRISLER], axis=0)
        ciz_mini_arac(t, merkez[0] - 60, merkez[1] - 118, (merkez[0] - 10, merkez[1] - 36))
        # üzerine gelme: imleç (çapraz) hover kolonun üstünde
        hx_, hy_ = E((6.0, 0.0, 12.0))
        t.cizgi([(hx_ - 11, hy_), (hx_ - 4, hy_)], METIN1, 1.0); t.cizgi([(hx_ + 4, hy_), (hx_ + 11, hy_)], METIN1, 1.0)
        t.cizgi([(hx_, hy_ - 11), (hx_, hy_ - 4)], METIN1, 1.0); t.cizgi([(hx_, hy_ + 4), (hx_, hy_ + 11)], METIN1, 1.0)
        t.cerceve(hx_ - 4, hy_ - 4, hx_ + 5, hy_ + 5, METIN1, r=0, w=1)
        tip = 'C3-B1 · HE340A'
        tw = t.gen(tip, 10.5, 500) + 14
        t.dolgu(hx_ + 14, hy_ + 10, hx_ + 14 + tw, hy_ + 28, rgba(ANTRASIT, 0.86), r=3)
        t.yazi(hx_ + 21, hy_ + 23, tip, 10.5, 500, KREM)
    if kip == 'sonuc':
        u = model.bul('K2-3BC')
        p0, p1 = E(u['p0']), E(u['p1'])
        pm = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        tw = t.gen('K2-3BC · D/C 0,87', 11, 500) + 20
        t.yuzen(pm[0] - tw / 2, pm[1] - 44, pm[0] + tw / 2, pm[1] - 20, r=4)
        t.dolgu(pm[0] - tw / 2 + 8, pm[1] - 36, pm[0] - tw / 2 + 16, pm[1] - 28, DC_RENK[2], r=2)
        t.yazi(pm[0] - tw / 2 + 22, pm[1] - 28, 'K2-3BC · D/C 0,87', 11, 500, METIN1)
        t.cizgi([(pm[0], pm[1] - 20), (pm[0], pm[1] - 6)], METIN2, 1.0)
        # ölçek/değer: birkaç eleman üstüne değer etiketi
        for ad in ('K1-3BC', 'K2-2BC'):
            u2 = model.bul(ad)
            q0, q1 = E(u2['p0']), E(u2['p1'])
            qm = ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2)
            s = '%.2f' % u2['dc']
            s = s.replace('.', ',')
            w = t.gen(s, 10, 600) + 10
            t.dolgu(qm[0] - w / 2, qm[1] - 9, qm[0] + w / 2, qm[1] + 9, rgba(KAGIT_ACIK, 0.92), r=3)
            t.cerceve(qm[0] - w / 2, qm[1] - 9, qm[0] + w / 2, qm[1] + 9, DC_RENK[dc_sinif(u2['dc'])], r=3)
            t.yazi(qm[0], qm[1] + 3.5, s, 10, 600, METIN1, anchor='ms')
    # yüzen görünüm araç çubuğu (sol üst)
    if kip == 'sonuc':
        ciz_sonuc_cubugu(t, vx0 + 16, vy0 + 16)
    else:
        ciz_gorunum_cubugu(t, vx0 + 16, vy0 + 16, dar=L['kucuk'])
    # seçim anahtarları çubuğu (alt orta)
    ciz_secim_anahtarlari(t, vx0 + 88, vy1 - 16)
    # eksen üçlüsü (sol alt, küp yok)
    ox, oy = vx0 + 36, vy1 - 34
    t.cizgi([(ox, oy), (ox + 26, oy + 7)], METIN2, 1.0); t.yazi(ox + 31, oy + 11, 'X', 10, 500, METIN2)
    t.cizgi([(ox, oy), (ox + 15, oy - 15)], METIN2, 1.0); t.yazi(ox + 18, oy - 17, 'Y', 10, 500, METIN2)
    t.cizgi([(ox, oy), (ox, oy - 27)], METIN2, 1.0); t.yazi(ox - 3, oy - 31, 'Z', 10, 500, METIN2)
    t.daire(ox, oy, 2, dolgu=METIN2)
    # pafta köşesi: görünüm başlık bloğu (sağ alt)
    ciz_pafta_kosesi(t, vx1 - 16, vy1 - 16, kip)
    return g


def ciz_mini_arac(t, x, y, hedef):
    """Bağlamsal mini araç çubuğu: kesit · malzeme · kat · serbestlik (özelleştirilebilir)."""
    ogeler = [('kesit_k', 'IPE400', True), ('yonetmelik', 'S355', True), ('kat', 'Kat 2', False), ('serbestlik', 'Mafsal', True)]
    w = 10
    for ik, s, m in ogeler:
        w += 20 + t.gen(s, 11.5, 500) + (14 if m else 6) + 10
    w += 22
    t.yuzen(x, y, x + w, y + 32, r=16, a=0.14)
    xx = x + 10
    for i, (ik, s, m) in enumerate(ogeler):
        t.ikon(ik, xx + 9, y + 16, 15, METIN2, 1.4)
        tw = t.yazi(xx + 22, y + 20.5, s, 11.5, 500, METIN1)
        xx += 22 + tw
        if m:
            t.ikon('chev_d', xx + 7, y + 16, 9, METIN3, 1.5)
            xx += 14
        else:
            xx += 6
        xx += 10
        if i < len(ogeler) - 1:
            t.dikey(xx - 5, y + 9, y + 23, CIZGI)
    t.ikon('ayar', x + w - 14, y + 16, 13, METIN3, 1.3)
    # seçime ince bağlantı
    t.cizgi([(x + 24, y + 32), hedef], ALTIN, 1.0)
    t.daire(hedef[0], hedef[1], 2.5, dolgu=ALTIN)


def ciz_gorunum_cubugu(t, x, y, dar=False):
    ogeler = [('seg', [('cubuk', 'Çubuk'), ('ekstruzyon', 'Ekstrüzyon')], 'Ekstrüzyon'), ('|',), ('on', 'golge', 'Gölge', True),
              ('on', 'izgara', 'Izgara', True), ('on', 'kat_duzlem', 'Kat düzlemleri', True), ('|',), ('menu', 'perspektif', 'Perspektif'),
              ('menu', 'plan', 'Görünüm: 3B'), ('|',), ('btn', 'kesit_duzlem', 'Kesit düzlemi'), ('btn', 'sinir', 'Görünüm sınırları')]
    if dar:
        ogeler = ogeler[:-3]
    w = 8
    for o in ogeler:
        if o[0] == '|':
            w += 17
        elif o[0] == 'seg':
            w += sum(24 + t.gen(s, 11.5, 500) + 12 for _, s in o[1]) + 4
        else:
            w += 24 + t.gen(o[2], 11.5, 500) + (16 if o[0] == 'menu' else 0) + (14 if o[0] == 'on' else 0) + 10
    t.yuzen(x, y, x + w, y + 32, r=6)
    xx = x + 8
    for o in ogeler:
        if o[0] == '|':
            t.dikey(xx + 8, y + 8, y + 24, CIZGI)
            xx += 17
            continue
        if o[0] == 'seg':
            sx = xx
            for ik, s in o[1]:
                bw = 24 + t.gen(s, 11.5, 500) + 12
                on = (s == o[2])
                if on:
                    t.dolgu(xx, y + 4, xx + bw, y + 28, ALTIN_ACIK, r=4)
                    t.cerceve(xx, y + 4, xx + bw, y + 28, ALTIN_ORTA, r=4)
                t.ikon(ik, xx + 14, y + 16, 15, METIN1 if on else METIN2, 1.4)
                t.yazi(xx + 26, y + 20.5, s, 11.5, 500, METIN1 if on else METIN2)
                xx += bw
            xx += 4
            continue
        tur, ik, ad = o[0], o[1], o[2]
        tw = t.gen(ad, 11.5, 500)
        on = o[3] if tur == 'on' else False
        t.ikon(ik, xx + 14, y + 16, 15, METIN1 if (on or tur != 'on') else METIN2, 1.4)
        t.yazi(xx + 26, y + 20.5, ad, 11.5, 500, METIN1 if (on or tur != 'on') else METIN2)
        xx += 26 + tw
        if tur == 'on':
            t.daire(xx + 7, y + 16, 2.2, dolgu=ALTIN if on else CIZGI_KOYU)
            xx += 14
        elif tur == 'menu':
            t.ikon('chev_d', xx + 8, y + 16, 10, METIN3, 1.5)
            xx += 16
        xx += 10


def ciz_sonuc_cubugu(t, x, y):
    """Sonuç gösterimi araç çubuğu: gösterim türü, kombinasyon, ölçek, deformasyon seçenekleri, animasyon."""
    seg = [('cubuk', 'Model'), ('deform', 'Deformasyon'), ('diyagram', 'N'), ('diyagram', 'V'), ('diyagram', 'M'), ('dc', 'D/C')]
    w = 8 + sum(24 + t.gen(s, 11.5, 500) + 12 for _, s in seg) + 4 + 17
    w += 24 + t.gen('Zarf (12 komb.)', 11.5, 500) + 16 + 10 + 17
    w += 24 + t.gen('Ölçek: Oto', 11.5, 500) + 16 + 10 + 17
    w += 24 + t.gen('Gölge', 11.5, 500) + 14 + 10 + 24 + t.gen('Kübik', 11.5, 500) + 14 + 10 + 17
    w += 24 + 104 + 10
    t.yuzen(x, y, x + w, y + 32, r=6)
    xx = x + 8
    for ik, s in seg:
        bw = 24 + t.gen(s, 11.5, 500) + 12
        on = (s == 'D/C')
        if on:
            t.dolgu(xx, y + 4, xx + bw, y + 28, ALTIN_ACIK, r=4)
            t.cerceve(xx, y + 4, xx + bw, y + 28, ALTIN_ORTA, r=4)
        t.ikon(ik, xx + 14, y + 16, 15, METIN1 if on else METIN2, 1.4)
        t.yazi(xx + 26, y + 20.5, s, 11.5, 500, METIN1 if on else METIN2)
        xx += bw
    xx += 4
    for ik, s in (('komb', 'Zarf (12 komb.)'), ('olcek', 'Ölçek: Oto')):
        t.dikey(xx + 8, y + 8, y + 24, CIZGI); xx += 17
        t.ikon(ik, xx + 14, y + 16, 15, METIN1, 1.4)
        tw = t.yazi(xx + 26, y + 20.5, s, 11.5, 500, METIN1)
        t.ikon('chev_d', xx + 26 + tw + 8, y + 16, 10, METIN3, 1.5)
        xx += 26 + tw + 16 + 10
    t.dikey(xx + 8, y + 8, y + 24, CIZGI); xx += 17
    for ik, s, on in (('golge', 'Gölge', True), ('deform', 'Kübik', False)):
        t.ikon(ik, xx + 14, y + 16, 15, METIN1 if on else METIN2, 1.4)
        tw = t.yazi(xx + 26, y + 20.5, s, 11.5, 500, METIN1 if on else METIN2)
        t.daire(xx + 26 + tw + 7, y + 16, 2.2, dolgu=ALTIN if on else CIZGI_KOYU)
        xx += 26 + tw + 14 + 10
    t.dikey(xx + 8, y + 8, y + 24, CIZGI); xx += 17
    t.ikon('anim', xx + 14, y + 16, 15, METIN1, 1.4)
    t.yatay(xx + 28, xx + 28 + 70, y + 16, CIZGI_KOYU)
    t.daire(xx + 28 + 26, y + 16, 4, dolgu=ALTIN)
    t.yazi(xx + 28 + 78, y + 20, '1×', 10, 500, METIN3)


def ciz_secim_anahtarlari(t, x, y1):
    """Seçim anahtarları: nesne türü geçişleri + tümü + kapsam seviyesi."""
    anahtarlar = [('dugum', 'Düğüm', False), ('kolon', 'Kolon', True), ('kiris', 'Kiriş', True), ('capraz', 'Çapraz', True),
                  ('doseme', 'Döşeme', True), ('duvar', 'Duvar', True), ('aks', 'Aks', False), ('yuk', 'Yük', False),
                  ('mesnet', 'Mesnet', True), ('temel', 'Temel', True)]
    bw = 32
    w = 8 + len(anahtarlar) * bw + 8 + 17 + bw + 17 + 24 + t.gen('Kapsam: Nesne', 11, 500) + 16 + 8
    y = y1 - 30
    t.yuzen(x, y, x + w, y + 30, r=6)
    xx = x + 8
    for ik, ad, on in anahtarlar:
        if on:
            t.dolgu(xx + 2, y + 4, xx + bw - 2, y + 26, ALTIN_ACIK, r=4)
        t.ikon(ik, xx + bw / 2, y + 15, 17, METIN1 if on else METIN3, 1.4)
        xx += bw
    t.dikey(xx + 8, y + 7, y + 23, CIZGI); xx += 17
    t.ikon('tumu', xx + bw / 2, y + 15, 16, METIN1, 1.4); xx += bw
    t.dikey(xx + 8, y + 7, y + 23, CIZGI); xx += 17
    t.yazi(xx, y + 19, 'Kapsam: Nesne', 11, 500, METIN1)
    t.ikon('chev_d', xx + t.gen('Kapsam: Nesne', 11, 500) + 9, y + 15, 10, METIN3, 1.5)


def ciz_pafta_kosesi(t, x1, y1, kip):
    """Pafta köşesi: görünüm başlık bloğu — proje, görünüm, gösterim, birim."""
    w, h = 236, 44
    x0, y0 = x1 - w, y1 - h
    t.dolgu(x0, y0, x1, y1, rgba(KAGIT_ACIK, 0.92))
    t.cerceve(x0, y0, x1, y1, CIZGI_KOYU)
    t.yatay(x0, x1, y0 + 22, CIZGI)
    t.dikey(x0 + 150, y0, y1, CIZGI)
    t.aralikli(x0 + 8, y0 + 15, 'DEPO BİNASI – TOKAT OSB', 8.5, 600, METIN2, 0.9)
    t.yazi(x0 + 8, y0 + 36, '3B · Güneybatı · Perspektif', 10, 400, METIN2)
    t.aralikli(x0 + 158, y0 + 15, 'D/C · ZARF' if kip == 'sonuc' else 'EKSTRÜZYON', 8.5, 600, METIN2, 0.9)
    t.yazi(x0 + 158, y0 + 36, 'm · kN · °C', 10, 400, METIN2)


# --- komut satırı ve durum çubuğu ----------------------------------------------------------------------------------
def ciz_komut(t, L):
    W = L['W']
    y0 = L['alt']
    y1 = y0 + KOMUT_H
    kip = L['kip']
    t.dolgu(0, y0, W, y1, KAGIT_ACIK)
    t.yatay(0, W, y0, CIZGI)
    x = 16
    w = t.yazi(x, y0 + 19.5, 'Komut:', 12, 500, METIN2)
    x += w + 8
    if kip == 'kat':
        w2 = t.yazi(x, y0 + 19.5, 'kiriş', 12.5, 500, METIN1)
        x += w2 + 2
    t.dolgu(x, y0 + 8, x + 1.5, y0 + 22, ALTIN)       # imleç
    t.dolgu(16, y1 - 3, x + 200, y1 - 2, ALTIN)        # odak çizgisi
    if kip == 'kat':
        t.yazi(x + 10, y0 + 19.5, 'beam · kiriş  ·  Enter: en üstteki komut', 11, 400, METIN3)
    else:
        t.yazi(x + 10, y0 + 19.5, '· Son: KİRİŞ — 6 kiriş eklendi (Kat 2)', 12, 400, METIN2)
    # sağ: hızlı başlat ipucu ve geçmiş
    rx = W - 16
    t.ikon('chev_u', rx - 6, y0 + 15, 12, METIN3, 1.5); rx -= 22
    t.ikon('gecmis', rx - 7, y0 + 15, 14, METIN3, 1.4); rx -= 28
    kw = t.gen('Ctrl+Q', 10, 500) + 10
    t.dolgu(rx - kw, y0 + 7, rx, y0 + 23, KAGIT_KOYU, r=3)
    t.yazi(rx - kw / 2, y0 + 18.5, 'Ctrl+Q', 10, 500, METIN2, anchor='ms')
    rx -= kw + 8
    t.yazi(rx, y0 + 19.5, 'Hızlı başlat: komut, iletişim kutusu, ayar, etiket (K12, B3) · TR / EN', 11, 400, METIN3, anchor='rs')


def ciz_durum(t, L, yazi_logo):
    W, H = L['W'], L['H']
    kip, kucuk = L['kip'], L['kucuk']
    y0 = H - DURUM_H
    t.dolgu(0, y0, W, H, KAGIT_KOYU)
    t.yatay(0, W, y0, CIZGI)
    by = y0 + 17
    # sol: adım yönergesi
    if kip == 'kat':
        t.daire(20, by - 4, 3, dolgu=ALTIN)
        t.yazi(30, by, 'Kiriş: ikinci noktayı seçin', 11.5, 500, METIN1)
        x = 30 + t.gen('Kiriş: ikinci noktayı seçin', 11.5, 500) + 8
        t.yazi(x, by, '· Enter bitirir · Esc iptal · Tab yakalama adayı', 11, 400, METIN3)
        sol_son = x + t.gen('· Enter bitirir · Esc iptal · Tab yakalama adayı', 11, 400)
    elif kip == 'sonuc':
        t.yazi(16, by, 'Tasarım tamamlandı: 213 çelik eleman · 1 eleman sınırı aşıyor (K1-3BC) · sağ tık: ayrıntı', 11, 400, METIN2)
        sol_son = 16 + t.gen('Tasarım tamamlandı: 213 çelik eleman · 1 eleman sınırı aşıyor (K1-3BC) · sağ tık: ayrıntı', 11, 400)
    else:
        s = 'Nesne seçin veya komut yazın' if kucuk else 'Nesne seçin veya komut yazın · D: doğrudan değiştirme · Shift+tekerlek: kapsam seviyesi'
        t.yazi(16, by, s, 11, 400, METIN2)
        sol_son = 16 + t.gen(s, 11, 400)
    # sağ blok: kat kapsamı anahtarı · birim · koordinat · seçili sayısı (sağdan sola)
    rx = W - 16
    h = 7
    w = int(round(yazi_logo.width * h / yazi_logo.height))
    if not kucuk:
        t.resim(yazi_logo, rx - w, y0 + 9.5, h)
        rx -= w + 14
        t.dikey(rx, y0 + 7, H - 7, CIZGI_KOYU)
        rx -= 14
    secili = {'sonuc': '1 seçili', 'kat': '0 seçili'}.get(kip, '6 seçili · 12 tutamaç')
    t.yazi(rx, by, secili, 11, 500, METIN1, anchor='rs')
    rx -= t.gen(secili, 11, 500) + 14
    t.dikey(rx, y0 + 7, H - 7, CIZGI_KOYU); rx -= 14
    koord = [('Z', '10,500' if kip == 'kat' else '12,000'), ('Y', '6,000' if kip == 'kat' else '0,000'), ('X', '12,000' if kip == 'kat' else '6,000')]
    for ad, val in koord:
        t.yazi(rx, by, val, 11, 450, METIN1, anchor='rs')
        rx -= t.gen(val, 11, 450) + 4
        t.yazi(rx, by, ad, 10, 500, METIN3, anchor='rs')
        rx -= t.gen(ad, 10, 500) + 10
    rx -= 4
    t.dikey(rx, y0 + 7, H - 7, CIZGI_KOYU); rx -= 14
    bw = t.gen('m · kN', 11, 500) + 32
    t.alan(rx - bw, y0 + 4, rx, H - 4, 'm · kN', menu=True, boy=11, w=500)
    rx -= bw + 14
    t.dikey(rx, y0 + 7, H - 7, CIZGI_KOYU); rx -= 14
    sw = t.gen('Bu kat', 10.5, 500) + t.gen('Benzer katlar', 10.5, 500) + t.gen('Tüm katlar', 10.5, 500) + 6 * 9 + 4
    sx = rx - sw
    t.segment(sx, y0 + 3, ['Bu kat', 'Benzer katlar', 'Tüm katlar'], 'Benzer katlar', h=20, boy=10.5, pad=9, dolgu=KAGIT)
    L['kapsam_x'] = (sx, sx + sw)
    rx = sx - 8
    if kip == 'kat':
        s = '3 katta uygulanacak'
        t.yazi(rx, by, s, 10.5, 600, KAHVE, anchor='rs')
        rx -= t.gen(s, 10.5, 600) + 8
    t.yazi(rx, by, 'Kat kapsamı', 10.5, 400, METIN3, anchor='rs')
    rx -= t.gen('Kat kapsamı', 10.5, 400) + 14
    t.dikey(rx, y0 + 7, H - 7, CIZGI_KOYU)
    # orta: Orto / Akıllı yakalama / Sürükle-bırak + X Y Z kilitleri (tıklanabilir)
    ogeler = [('orto', 'Orto', False, 'O'), ('yakala', 'Akıllı yakalama', True, 'S'), ('surukle', 'Sürükle-bırak', True, 'D')]
    tw = sum(20 + t.gen(ad, 10.5, 500) + 18 for _, ad, _, _ in ogeler) + 3 * 22 + 26
    x = max(sol_son + 28, min(W * 0.36, rx - 20 - tw)) if not kucuk else max(sol_son + 24, rx - 16 - tw)
    for ik, ad, on, k in ogeler:
        if on:
            t.dolgu(x - 4, y0 + 4, x + 20 + t.gen(ad, 10.5, 500) + 8, H - 4, ALTIN_ACIK, r=3)
        t.ikon(ik, x + 7, by - 4, 14, METIN1 if on else METIN3, 1.4)
        t.yazi(x + 20, by, ad, 10.5, 500, METIN1 if on else METIN3)
        x += 20 + t.gen(ad, 10.5, 500) + 18
    t.dikey(x - 4, y0 + 7, H - 7, CIZGI_KOYU)
    x += 8
    for ad, on in (('X', False), ('Y', False), ('Z', kip == 'kat')):
        if on:
            t.dolgu(x, y0 + 5, x + 18, H - 5, ALTIN, r=3)
            t.yazi(x + 9, by, ad, 10.5, 600, KAGIT_ACIK, anchor='ms')
        else:
            t.cerceve(x, y0 + 5, x + 18, H - 5, CIZGI_KOYU, r=3)
            t.yazi(x + 9, by, ad, 10.5, 500, METIN3, anchor='ms')
        x += 22
    t.yazi(x + 2, by, 'kilit', 10, 400, METIN3)


def ciz_kapsam_onizleme(t, L):
    """Kat kapsamı anahtarının üstünde açılan önizleme: hangi katlara uygulanacağı."""
    sx0, sx1 = L['kapsam_x']
    W, H = L['W'], L['H']
    w, h = 316, 146
    x1 = min(W - 16, sx1 + 20)
    x0 = x1 - w
    y1 = H - DURUM_H - 8
    y0 = y1 - h
    t.yuzen(x0, y0, x1, y1, r=6, a=0.18)
    # ok ucu
    cx = (sx0 + sx1) / 2
    t.cokgen([(cx - 6, y1), (cx + 6, y1), (cx, y1 + 6)], dolgu=KAGIT_ACIK, kenar=CIZGI)
    t.yatay(cx - 5, cx + 5, y1 - 1, KAGIT_ACIK)
    t.aralikli(x0 + 14, y0 + 20, 'BENZER KATLAR', 9, 600, METIN2, 1.0)
    t.yazi(x1 - 14, y0 + 20, 'Alt+2', 10, 500, METIN3, anchor='rs')
    t.yatay(x0 + 14, x1 - 14, y0 + 28, CIZGI_SOLUK)
    y = y0 + 36
    for ad, kot, rol, on in (('Kat 3 (Çatı)', '+13.50', 'Benzer → Kat 2', True), ('Kat 2', '+9.00', 'Ana kat', True),
                             ('Kat 1', '+4.50', 'Benzer → Kat 2', True), ('Zemin', '±0.00', 'Yok', False)):
        t.onay(x0 + 14, y + 3, on, 13)
        t.yazi(x0 + 34, y + 14, ad, 11.5, 500 if on else 400, METIN1 if on else METIN3)
        t.yazi(x0 + 124, y + 14, kot, 11, 400, METIN3)
        t.yazi(x1 - 14, y + 14, rol, 10.5, 400, KAHVE if rol == 'Ana kat' else (METIN2 if on else METIN3), anchor='rs')
        y += 20
    t.yatay(x0 + 14, x1 - 14, y + 2, CIZGI_SOLUK)
    t.daire(x0 + 20, y + 14, 3, dolgu=ALTIN)
    t.yazi(x0 + 30, y + 18, '3 katta uygulanacak · plan konumu + nesne türü eşleşir', 10.5, 500, METIN1)


# --- Seç ve Süz penceresi ---------------------------------------------------------------------------------------------
def ciz_sec_suz(t, L):
    vx0, vy0, vx1, vy1 = L['vp']
    t.dolgu(vx0, vy0, vx1, vy1, rgba(KAGIT, 0.55))
    DW, DH = 960, 690
    x0 = (vx0 + vx1) / 2 - DW / 2
    y0 = (vy0 + vy1) / 2 - DH / 2 - 8
    x1, y1 = x0 + DW, y0 + DH
    t.yumusak_golge(x0, y0, x1, y1, r=8, yay=18, kay=8, a=0.20)
    t.dolgu(x0, y0, x1, y1, KAGIT, r=8)
    t.cerceve(x0, y0, x1, y1, CIZGI_KOYU, r=8)
    # başlık
    t.ikon('suz', x0 + 28, y0 + 24, 18, METIN1, 1.5)
    t.yazi(x0 + 46, y0 + 29.5, 'Seç ve Süz', 15, 600, METIN1)
    t.yazi(x0 + 46 + t.gen('Seç ve Süz', 15, 600) + 10, y0 + 29.5, 'Aynı kural motoru: seçim · görünüm süzgeci · renk kuralı', 11.5, 400, METIN3)
    t.ikon('kapat', x1 - 26, y0 + 24, 14, METIN2, 1.4)
    t.yatay(x0, x1, y0 + 48, CIZGI)
    t.segment(x0 + 24, y0 + 60, ['Seçim süzgeci', 'Görünüm süzgeci', 'Renk kuralı'], 'Seçim süzgeci', h=24, boy=11, pad=12)
    # sol: kayıtlı süzgeçler
    lx0, lx1 = x0 + 24, x0 + 232
    yy = y0 + 100
    t.aralikli(lx0, yy, 'KAYITLI SÜZGEÇLER', 9.5, 600, METIN2, 1.0)
    t.ikon('arti', lx1 - 8, yy - 4, 12, METIN2, 1.5)
    yy += 10
    for ad, on in (('Kat 2 kirişleri', True), ('IPE400 — tümü', False), ('Mafsallı kirişler', False), ('A aksı çerçevesi', False),
                   ('Çaprazlar (L100×10)', False), ('Q > 3 kN/m² döşemeler', False)):
        if on:
            t.dolgu(lx0 - 8, yy, lx1, yy + 26, ALTIN_ACIK, r=3)
            t.dolgu(lx0 - 8, yy, lx0 - 6, yy + 26, ALTIN)
        t.ikon('kaydedilmis', lx0 + 7, yy + 13, 13, METIN2, 1.4)
        t.yazi(lx0 + 22, yy + 17.5, ad, 12, 500 if on else 400, METIN1 if on else METIN2)
        yy += 26
    yy += 10
    t.yazi(lx0, yy + 12, 'proje/suzgecler/*.filtre', 10, 400, METIN3)
    t.yazi(lx0, yy + 30, 'Firma profiliyle paylaşılır', 10, 400, METIN3)
    t.dikey(x0 + 252, y0 + 96, y1 - 64, CIZGI)
    # sağ: kurallar
    rx0, rx1 = x0 + 276, x1 - 24
    yy = y0 + 100
    t.aralikli(rx0, yy, 'KURALLAR', 9.5, 600, METIN2, 1.0)
    t.yazi(rx1, yy, 'Boş bağlaç = Ve', 10.5, 400, METIN3, anchor='rs')
    yy += 12
    kol = [(0, '(', 24), (24, 'Kategori', 96), (120, 'Özellik', 118), (238, 'Koşul', 70), (308, 'Değer', 190), (498, ')', 24), (522, 'Ve / Veya', 78)]
    t.dolgu(rx0, yy, rx1, yy + 24, KAGIT_KOYU, r=3)
    for cx, ad, cw in kol:
        t.yazi(rx0 + 8 + cx, yy + 16, ad, 10.5, 600, METIN2)
    yy += 24
    satirlar = [('(', 'Nesne', 'Tür', '=', 'Kiriş', '', 'Ve'), ('', 'Nesne', 'Kesit', '=', 'IPE400', ')', 'Ve'),
                ('', 'Nesne', 'Kat', 'içinde', 'Kat 2 · Kat 3', '', 'Veya'), ('', 'Nesne', 'Serbestlik', '=', 'Mafsal – Mafsal', '', '—'),
                ('', 'Yük', 'Yük deseni', '=', 'Q (hareketli)', '', '')]
    for i, s in enumerate(satirlar):
        if i == 4:
            t.yazi(rx0 + 8 + 24, yy + 18, '+ Satır ekle', 11.5, 500, KAHVE)
            t.yazi(rx0 + 8 + 120, yy + 18, 'Parantez ( )', 11.5, 500, METIN2)
            t.yazi(rx0 + 8 + 238, yy + 18, 'Satırı sil', 11.5, 500, METIN2)
            yy += 28
            break
        t.yatay(rx0, rx1, yy + 27, CIZGI_SOLUK)
        for (cx, _, cw), v in zip(kol, s):
            if cx in (0, 498):
                t.yazi(rx0 + 8 + cx + 6, yy + 18, v, 12, 500, METIN2, anchor='ms')
            else:
                t.alan(rx0 + 4 + cx, yy + 4, rx0 + cx + cw - 2, yy + 24, v, menu=(cx != 308), boy=11.5, w=500 if cx == 308 else 400)
        yy += 28
    yy += 4
    # seçimden kural üret
    t.dolgu(rx0, yy, rx1, yy + 30, KAGIT_ACIK, r=4); t.cerceve(rx0, yy, rx1, yy + 30, CIZGI, r=4)
    t.ikon('benzer', rx0 + 16, yy + 15, 15, METIN1, 1.4)
    t.yazi(rx0 + 30, yy + 19.5, 'Benzerini seç', 11.5, 600, METIN1)
    t.yazi(rx0 + 30 + t.gen('Benzerini seç', 11.5, 600) + 8, yy + 19.5, 'seçili 6 kirişten kural üretildi: Tür + Kesit + Kat', 11, 400, METIN2)
    yy += 44
    # sonuç
    t.aralikli(rx0, yy, 'SONUÇ', 9.5, 600, METIN2, 1.0)
    yy += 10
    t.daire(rx0 + 6, yy + 12, 3.5, dolgu=ALTIN)
    t.yazi(rx0 + 16, yy + 16.5, '24 nesne eşleşiyor', 13, 600, METIN1)
    t.yazi(rx0 + 16 + t.gen('24 nesne eşleşiyor', 13, 600) + 8, yy + 16.5, '· Kat 2: 18 · Kat 3: 6 · Σ 144,0 m · 7,8 t', 11.5, 400, METIN2)
    yy += 30
    for i, (ad, n) in enumerate((('Kiriş', 24), ('IPE400', 24), ('Mafsal – Mafsal', 20), ('Kat 2', 18), ('Kat 3', 6))):
        s = '%s %d' % (ad, n)
        cw = t.gen(s, 10.5, 500) + 16
        cx = rx0 + sum(t.gen('%s %d' % a, 10.5, 500) + 16 + 8 for a in (('Kiriş', 24), ('IPE400', 24), ('Mafsal – Mafsal', 20), ('Kat 2', 18), ('Kat 3', 6))[:i])
        t.dolgu(cx, yy, cx + cw, yy + 20, KAGIT_KOYU, r=10)
        t.yazi(cx + cw / 2, yy + 14, s, 10.5, 500, METIN1, anchor='ms')
    yy += 36
    t.onay(rx0, yy, True, 13); t.yazi(rx0 + 20, yy + 11, 'Görünümde vurgula', 11.5, 400, METIN2)
    t.onay(rx0 + 190, yy, True, 13); t.yazi(rx0 + 210, yy + 11, 'Kat kapsamına uy (Benzer katlar)', 11.5, 400, METIN2)
    t.onay(rx0 + 440, yy, False, 13); t.yazi(rx0 + 460, yy + 11, 'Yalnız görünür nesneler', 11.5, 400, METIN2)
    yy += 30
    t.aralikli(rx0, yy + 8, 'EŞLEŞENLER', 9.5, 600, METIN2, 1.0)
    t.yazi(rx1, yy + 8, 'çift tık: nesneye git', 10.5, 400, METIN3, anchor='rs')
    yy += 16
    kol2 = [(0, 'Etiket', 'l'), (80, 'Kat', 'l'), (140, 'Kesit', 'l'), (215, 'Aks', 'l'), (290, 'Uzunluk', 'r'), (390, 'Serbestlik', 'l'), (530, 'Grup', 'l')]
    t.dolgu(rx0, yy, rx1, yy + 22, KAGIT_KOYU, r=3)
    for cx, ad, al in kol2:
        t.yazi(rx0 + 8 + cx + (56 if al == 'r' else 0), yy + 15, ad, 10.5, 600, METIN2, anchor='rs' if al == 'r' else 'ls')
    yy += 22
    satirlar2 = [('K2-2AB', 'Kat 2', 'IPE400', '2 · A–B', '6,000 m', 'Mafsal – Mafsal', 'Kat 2 çerçevesi'),
                 ('K2-2BC', 'Kat 2', 'IPE400', '2 · B–C', '6,000 m', 'Mafsal – Mafsal', 'Kat 2 çerçevesi'),
                 ('K2-2CD', 'Kat 2', 'IPE400', '2 · C–D', '6,000 m', 'Mafsal – Mafsal', 'Kat 2 çerçevesi'),
                 ('K2-3AB', 'Kat 2', 'IPE400', '3 · A–B', '6,000 m', 'Mafsal – Mafsal', 'Kat 2 çerçevesi'),
                 ('K3-1AB', 'Kat 3', 'IPE400', '1 · A–B', '6,000 m', 'Ankastre – Mafsal', '—')]
    for i, s in enumerate(satirlar2):
        if i % 2:
            t.dolgu(rx0, yy, rx1, yy + 22, KAGIT_ACIK)
        for (cx, _, al), v in zip(kol2, s):
            t.yazi(rx0 + 8 + cx + (56 if al == 'r' else 0), yy + 15, v, 11, 500 if cx == 0 else 400, METIN1, anchor='rs' if al == 'r' else 'ls')
        t.yatay(rx0, rx1, yy + 21, CIZGI_SOLUK)
        yy += 22
    t.yazi(rx0 + 8, yy + 15, '… 19 nesne daha', 10.5, 400, METIN3)
    # alt düğmeler
    t.yatay(x0, x1, y1 - 56, CIZGI)
    t.yazi(x0 + 24, y1 - 24.5, 'Süzgeci kaydet…', 12, 500, KAHVE)
    bx = x1 - 24
    for ad, tur in (('Seç', 'birincil'), ('Seçime ekle', 'ikincil'), ('Seçimden çıkar', 'ikincil'), ('İptal', 'duz')):
        w = t.gen(ad, 12, 500) + 28
        bx -= w
        t.dugme(bx, y1 - 42, bx + w, y1 - 14, ad, tur)
        bx -= 8


# --- sonuç: lejant ve tablo bölmesi ---------------------------------------------------------------------------------
def ciz_lejant(t, L):
    vx0, vy0, vx1, vy1 = L['vp']
    y0, y1 = vy1, vy1 + LEJANT_H
    t.dolgu(vx0, y0, vx1, y1, KAGIT)
    t.yatay(vx0, vx1, y0, CIZGI)
    x = vx0 + 16
    t.yazi(x, y0 + 19, 'D/C oranı', 11, 600, METIN1)
    x += t.gen('D/C oranı', 11, 600) + 6
    t.yazi(x, y0 + 19, 'TS EN 1993-1-1 · Zarf (12 komb.)', 11, 400, METIN3)
    x += t.gen('TS EN 1993-1-1 · Zarf (12 komb.)', 11, 400) + 24
    sayilar = (86, 71, 44, 11, 1)
    for renk, et, n in zip(DC_RENK, DC_ETIKET, sayilar):
        t.dolgu(x, y0 + 9, x + 22, y0 + 21, renk, r=2)
        s = '%s  (%d)' % (et, n)
        t.yazi(x + 28, y0 + 19, s, 11, 400, METIN1)
        x += 28 + t.gen(s, 11, 400) + 20
    t.yazi(vx1 - 16, y0 + 19, 'Eşikleri düzenle…', 11, 500, KAHVE, anchor='rs')


def ciz_dock(t, L):
    vx0, vy0, vx1, vy1 = L['vp']
    y0, y1 = vy1 + LEJANT_H, L['alt']
    t.dolgu(vx0, y0, vx1, y1, KAGIT)
    t.yatay(vx0, vx1, y0, CIZGI)
    # sekmeler
    x = vx0 + 16
    for ad in ('Çelik tasarım özeti', 'Eleman kuvvetleri', 'Mesnet reaksiyonları', 'Kat tepkileri', 'Uyarılar (1)'):
        on = (ad == 'Çelik tasarım özeti')
        w = t.yazi(x, y0 + 21, ad, 11.5, 500 if on else 450, METIN1 if on else (HATA if ad.startswith('Uyarı') else METIN2))
        if on:
            t.dolgu(x - 1, y0 + 29, x + w + 1, y0 + 31, ALTIN)
        x += w + 20
    t.yatay(vx0, vx1, y0 + 31, CIZGI)
    rx = vx1 - 16
    for ad, ik in (('CSV’ye aktar', 'tablo_disa'), ('Tablo kümesi', 'kume'), ('Süz…', 'suz')):
        w = t.gen(ad, 11, 500)
        t.yazi(rx, y0 + 21, ad, 11, 500, METIN2, anchor='rs')
        t.ikon(ik, rx - w - 11, y0 + 16, 14, METIN2, 1.4)
        rx -= w + 34
    t.yazi(rx, y0 + 21, 'Kombinasyon: Zarf  ·  Kat: Tümü  ·  Sıralama: D/C ↓', 11, 400, METIN3, anchor='rs')
    # tablo
    y = y0 + 32
    kol = [('Eleman', 0, 'l'), ('Kat', 80, 'l'), ('Kesit', 140, 'l'), ('Tasarım grubu', 220, 'l'), ('Kombinasyon', 330, 'l'), ('N (kN)', 480, 'r'),
           ('My (kNm)', 560, 'r'), ('Vz (kN)', 640, 'r'), ('Eğilme', 720, 'r'), ('Kesme', 790, 'r'), ('LTB', 860, 'r'), ('D/C', 920, 'r'), ('Durum', 1020, 'l')]
    t.dolgu(vx0, y, vx1, y + 22, KAGIT_KOYU)
    for ad, cx, al in kol:
        xx = vx0 + 16 + cx
        t.yazi(xx + (54 if al == 'r' else 0), y + 15, ad, 10.5, 600, METIN2, anchor='rs' if al == 'r' else 'ls')
    y += 22
    satirlar = [('K1-3BC', 'Kat 1', 'IPE400', 'Kirişler', 'K12', '−3,1', '244,8', '118,2', '0,98', '0,41', '1,04', '1,04', 'Sınır aşıldı'),
                ('K2-2BC', 'Kat 2', 'IPE400', 'Kirişler', 'K12', '−2,4', '218,6', '106,0', '0,88', '0,37', '0,93', '0,93', 'Uygun'),
                ('K2-3BC', 'Kat 2', 'IPE400', 'Kirişler', 'K12', '−2,2', '204,1', '99,5', '0,81', '0,34', '0,87', '0,87', 'Uygun'),
                ('C1-B3', 'Zemin', 'HE340A', 'Kolonlar', 'K7', '−1 412,0', '96,3', '41,8', '0,52', '0,12', '0,79', '0,79', 'Uygun'),
                ('K3-3BC', 'Kat 3', 'IPE400', 'Kirişler', 'K12', '−1,8', '166,2', '80,9', '0,66', '0,28', '0,71', '0,71', 'Uygun'),
                ('X1-05', 'Kat 1', 'L100×10', 'Çaprazlar', 'K9', '212,5', '0,0', '0,0', '—', '—', '—', '0,64', 'Uygun'),
                ('A3-07', 'Kat 3', 'IPE200', 'Aşıklar', 'K12', '0,0', '28,4', '18,6', '0,58', '0,21', '0,61', '0,61', 'Uygun')]
    for i, s in enumerate(satirlar):
        if y + 24 > y1:
            break
        secili = (s[0] == 'K2-3BC')
        if secili:
            t.dolgu(vx0 + 1, y, vx1, y + 24, ALTIN_ACIK)
            t.dolgu(vx0 + 1, y, vx0 + 3, y + 24, ALTIN)
        elif i % 2:
            t.dolgu(vx0, y, vx1, y + 24, KAGIT_ACIK)
        for (ad, cx, al), v in zip(kol, s):
            xx = vx0 + 16 + cx
            renk = METIN1
            if ad == 'D/C':
                r = float(v.replace(',', '.'))
                t.dolgu(xx + 54 - t.gen(v, 11, 600) - 20, y + 8, xx + 54 - t.gen(v, 11, 600) - 10, y + 17, DC_RENK[dc_sinif(r)], r=2)
                t.yazi(xx + 54, y + 16.5, v, 11, 600, METIN1, anchor='rs')
                continue
            if ad == 'Durum' and v != 'Uygun':
                renk = HATA
            t.yazi(xx + (54 if al == 'r' else 0), y + 16.5, v, 11, 500 if ad == 'Eleman' else 400, renk, anchor='rs' if al == 'r' else 'ls')
        t.yatay(vx0, vx1, y + 23, CIZGI_SOLUK)
        y += 24


# ------------------------------------------------------------------ bütün ekran
def model_hazirla(kip):
    m = depo_binasi()
    if kip in ('ana', 'kat', 'secsuz'):
        for ad in SECILI_KIRISLER:
            m.bul(ad)['secili'] = True
        m.bul('C3-B1')['hover'] = True
    elif kip == 'sonuc':
        m.bul('K2-3BC')['secili'] = True
    return m


def ekran(W, H, S, kucuk=False, kip='ana'):
    L = yerlesim(W, H, kucuk, kip)
    t = Tuval(W, H, S, KAGIT)
    simge = Image.open(SIMGE).convert('RGBA')
    yazi_logo = Image.open(YAZI_LOGO).convert('RGBA')
    model = model_hazirla(kip)
    ciz_gorunum(t, L, model)
    ciz_baslik(t, L, simge)
    sekme = 'Tasarım' if kip == 'sonuc' else 'Model'
    ciz_sekmeler(t, L, sekme)
    ciz_serit(t, L, sekme)
    if kucuk:
        ciz_sol_strip(t, L)
    else:
        ciz_agac(t, L)
    ciz_ozellikler(t, L)
    ciz_sag_strip(t, L)
    if kip == 'sonuc':
        ciz_lejant(t, L)
        ciz_dock(t, L)
    ciz_komut(t, L)
    ciz_durum(t, L, yazi_logo)
    if kip == 'secsuz':
        ciz_sec_suz(t, L)
    if kip == 'kat':
        ciz_kapsam_onizleme(t, L)
    t.cerceve(0, 0, W, H, karisim(KAGIT, ANTRASIT, 0.18), r=0, w=1)
    return t


def kaydet(im, ad):
    yol = os.path.join(BURASI, ad)
    im.convert('RGB').save(yol, optimize=True)
    print('yazıldı', yol, im.size)


def main():
    global HIZLI
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    HIZLI = '--hizli' in sys.argv
    hangi = set(args) or {'ana', 'kucuk', 'secsuz', 'sonuc', '2x', 'kat'}
    if 'ana' in hangi:
        kaydet(ekran(1920, 1080, 1).im, 'ana.png')
    if 'kucuk' in hangi:
        kaydet(ekran(1366, 768, 1, kucuk=True).im, 'kucuk.png')
    if 'secsuz' in hangi:
        kaydet(ekran(1920, 1080, 1, kip='secsuz').im, 'secsuz.png')
    if 'sonuc' in hangi:
        kaydet(ekran(1920, 1080, 1, kip='sonuc').im, 'sonuc.png')
    if '2x' in hangi:
        t = ekran(1920, 1080, 2)
        kaydet(t.im, 'ana-2x.png')
        kaydet(t.kirp(0, 0, 1920, BASLIK_H + SEKME_H + SERIT_H + 6), 'detay-serit.png')
        sol = t.kirp(0, 150, 300, 150 + 874)
        sag = t.kirp(1920 - STRIP_W - 320, 150, 1920, 150 + 874)
        birlesik = Image.new('RGB', (sol.width + 48 * 2 + sag.width, sol.height), KAGIT_KOYU)
        birlesik.paste(sol, (0, 0))
        birlesik.paste(sag, (sol.width + 96, 0))
        kaydet(birlesik, 'detay-panel.png')
    if 'kat' in hangi:
        t = ekran(1920, 1080, 2, kip='kat')
        kaydet(t.kirp(900, 1080 - DURUM_H - 200, 1920, 1080), 'kat-kapsami.png')


if __name__ == '__main__':
    main()
