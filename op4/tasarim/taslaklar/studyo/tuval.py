# -*- coding: utf-8 -*-
"""tuval.py — op4 "Stüdyo" maketleri için çizim altyapısı.

Mantıksal piksel (1× = 96 DPI) koordinatlarıyla çalışır; S ölçeğiyle çarpılarak
çizilir. Yuvarlatılmış köşeler, gölgeler ve ikonlar süper örneklenmiş maskeyle
(kenar yumuşatmalı) üretilir; metin Pillow/FreeType ile doğrudan çizilir.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

KIMLIK = '/home/user/matris-ogren/op4/kimlik'
FONTLAR = os.path.join(KIMLIK, 'fontlar')
FONT_YOL = {
    'inter': os.path.join(FONTLAR, 'inter-Inter[opsz,wght].ttf'),
    'cormorant': os.path.join(FONTLAR, 'cormorantgaramond-CormorantGaramond[wght].ttf'),
    'cinzel': os.path.join(FONTLAR, 'cinzel-Cinzel[wght].ttf'),
}

LANCZOS = Image.Resampling.LANCZOS


# ---------------------------------------------------------------- renkler
def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def karistir(a, b, t):
    """a ile b arasında t oranında (0 → a, 1 → b) karışım."""
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def alfa(rgb, a):
    return (rgb[0], rgb[1], rgb[2], int(round(a * 255)))


# Marka ve tema belirteçleri (tasarim.md ile birebir)
R = {
    'kahve': hexrgb('#8A6B3C'), 'krem': hexrgb('#EDE6D8'), 'altin': hexrgb('#B08950'),
    'antrasit': hexrgb('#14181B'), 'gri': hexrgb('#8C8C8C'),
    'zemin': hexrgb('#F3F1ED'), 'yuzey': hexrgb('#FFFFFF'), 'yuzey2': hexrgb('#F7F5F1'),
    'yuzey3': hexrgb('#EFECE6'),
    'cizgi': hexrgb('#E6E2DB'), 'cizgi2': hexrgb('#D3CEC4'),
    'metin': hexrgb('#14181B'), 'metin2': hexrgb('#5A5E62'), 'metin3': hexrgb('#8C8C8C'),
    'altin_dolgu': hexrgb('#F4EBDA'), 'altin_zemin': hexrgb('#F8F2E6'),
    'kahve_koyu': hexrgb('#6F5530'),
    'hata': hexrgb('#C8372D'), 'uyari': hexrgb('#D9A13B'), 'tamam': hexrgb('#4C9A63'),
    'durum': hexrgb('#ECE9E3'),
    'eksen_x': hexrgb('#B5553F'), 'eksen_y': hexrgb('#4F8F5A'), 'eksen_z': hexrgb('#3F6FAF'),
}
# D/C 5 eşik paleti (açık/koyu zeminde okunur çift olarak seçildi)
DC_RENK = [hexrgb('#5B8FC9'), hexrgb('#55A86E'), hexrgb('#D9B13B'), hexrgb('#E07B2A'), hexrgb('#C8372D')]
DC_ESIK = [0.50, 0.70, 0.90, 1.00]


# ---------------------------------------------------------------- yazı tipleri
class Yazi:
    """Değişken yazı tipi önbelleği: (aile, piksel boyutu, ağırlık) → ImageFont."""
    _cache = {}

    @classmethod
    def al(cls, aile, px, agirlik):
        px = int(round(px))
        key = (aile, px, agirlik)
        f = cls._cache.get(key)
        if f is None:
            f = ImageFont.truetype(FONT_YOL[aile], px)
            if aile == 'inter':
                opsz = max(14, min(32, px))
                f.set_variation_by_axes([opsz, agirlik])
            elif aile == 'cormorant':
                f.set_variation_by_axes([max(300, min(700, agirlik))])
            else:
                f.set_variation_by_axes([max(400, min(900, agirlik))])
            cls._cache[key] = f
        return f


# ---------------------------------------------------------------- ikon kalemi
class IkonKalem:
    """24×24 birimlik ikon uzayında çizim; süper örneklenmiş L maskesine yazar."""

    def __init__(self, mask, k, w):
        self.d = ImageDraw.Draw(mask)
        self.k = k      # piksel / birim
        self.w = max(1, int(round(w)))

    def _p(self, x, y):
        return (x * self.k, y * self.k)

    def line(self, *c):
        pts = [self._p(c[i], c[i + 1]) for i in range(0, len(c), 2)]
        self.d.line(pts, fill=255, width=self.w, joint='curve')
        for p in (pts[0], pts[-1]):
            self._cap(p)

    def _cap(self, p):
        r = self.w / 2.0
        self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)

    def poly(self, pts, close=True):
        pp = [self._p(x, y) for x, y in pts]
        if close:
            pp.append(pp[0])
        self.d.line(pp, fill=255, width=self.w, joint='curve')
        for p in pp:
            self._cap(p)

    def dolu(self, pts):
        self.d.polygon([self._p(x, y) for x, y in pts], fill=255)

    def cember(self, cx, cy, r, dolu=False):
        b = [(cx - r) * self.k, (cy - r) * self.k, (cx + r) * self.k, (cy + r) * self.k]
        if dolu:
            self.d.ellipse(b, fill=255)
        else:
            self.d.ellipse(b, outline=255, width=self.w)

    def yay(self, cx, cy, r, a0, a1):
        b = [(cx - r) * self.k, (cy - r) * self.k, (cx + r) * self.k, (cy + r) * self.k]
        self.d.arc(b, a0, a1, fill=255, width=self.w)
        for a in (a0, a1):
            self._cap(((cx + r * math.cos(math.radians(a))) * self.k,
                       (cy + r * math.sin(math.radians(a))) * self.k))

    def dikd(self, x, y, w, h, r=0):
        b = [x * self.k, y * self.k, (x + w) * self.k, (y + h) * self.k]
        if r:
            self.d.rounded_rectangle(b, radius=r * self.k, outline=255, width=self.w)
        else:
            self.d.rectangle(b, outline=255, width=self.w)

    def nokta(self, cx, cy, r=1.4):
        self.cember(cx, cy, r, dolu=True)


def _I_dik(c):
    c.line(7, 4, 17, 4); c.line(7, 20, 17, 20); c.line(12, 4, 12, 20)


IKONLAR = {}


def ikon(ad):
    def kayit(f):
        IKONLAR[ad] = f
        return f
    return kayit


@ikon('imlec')
def _(c):
    c.poly([(6, 3), (6, 18), (10, 14.6), (13, 20.6), (15.6, 19.4), (12.6, 13.4), (17.6, 13)])


@ikon('sec')
def _(c):
    c.poly([(4, 3), (4, 15), (7.4, 12.2), (9.8, 17.2), (12.2, 16.1), (9.8, 11.2), (14, 11)])
    for x in (13, 16, 19):
        c.line(x, 20, x + 1.2, 20)
    for y in (6, 9, 12):
        c.line(20, y, 20, y + 1.2)
    c.line(13, 3, 14.2, 3); c.line(16, 3, 17.2, 3); c.line(19, 3, 20, 3)


@ikon('kaydir')
def _(c):
    c.line(12, 4, 12, 20); c.line(4, 12, 20, 12)
    c.poly([(9.5, 6.5), (12, 4), (14.5, 6.5)], close=False)
    c.poly([(9.5, 17.5), (12, 20), (14.5, 17.5)], close=False)
    c.poly([(6.5, 9.5), (4, 12), (6.5, 14.5)], close=False)
    c.poly([(17.5, 9.5), (20, 12), (17.5, 14.5)], close=False)


@ikon('dondur')
def _(c):
    c.yay(12, 12, 7.5, 20, 320)
    c.poly([(16.3, 3.2), (19.6, 6.3), (16.0, 8.9)], close=False)


@ikon('yakinlastir')
def _(c):
    c.cember(10.5, 10.5, 6.5); c.line(15.3, 15.3, 20.5, 20.5)
    c.line(7.5, 10.5, 13.5, 10.5); c.line(10.5, 7.5, 10.5, 13.5)


@ikon('ara')
def _(c):
    c.cember(10.5, 10.5, 6.2); c.line(15.2, 15.2, 20.5, 20.5)


@ikon('ev')
def _(c):
    c.poly([(4, 11.5), (12, 4.5), (20, 11.5)], close=False)
    c.poly([(6, 10), (6, 20), (18, 20), (18, 10)], close=False)
    c.poly([(10, 20), (10, 14.5), (14, 14.5), (14, 20)], close=False)


@ikon('plan')
def _(c):
    c.dikd(4, 4, 16, 16); c.line(4, 12, 20, 12); c.line(12, 4, 12, 20)


@ikon('ucb')
def _(c):
    c.poly([(12, 3), (20, 7.5), (20, 16.5), (12, 21), (4, 16.5), (4, 7.5)])
    c.line(12, 12, 20, 7.5); c.line(12, 12, 4, 7.5); c.line(12, 12, 12, 21)


@ikon('kesit')
def _(c):
    c.poly([(3, 17), (9, 7), (21, 7), (15, 17)])
    c.line(6, 3, 6, 5); c.line(6, 8, 6, 10); c.line(6, 13, 6, 15); c.line(6, 18, 6, 21)


@ikon('cubuk')
def _(c):
    c.line(5, 12, 19, 12); c.nokta(5, 12, 1.8); c.nokta(19, 12, 1.8); c.nokta(12, 12, 1.4)


@ikon('ekstr')
def _(c):
    c.poly([(4, 6), (16, 6), (16, 9), (11, 9), (11, 15), (16, 15), (16, 18), (4, 18), (4, 15), (9, 15), (9, 9), (4, 9)])
    c.line(16, 6, 20, 4); c.line(16, 18, 20, 16); c.line(20, 4, 20, 16)


@ikon('olc')
def _(c):
    c.poly([(3, 15.5), (15.5, 3), (21, 8.5), (8.5, 21)])
    c.line(7, 11.5, 9, 13.5); c.line(10, 8.5, 12, 10.5); c.line(13, 5.5, 15, 7.5)


@ikon('sorgu')
def _(c):
    c.cember(12, 12, 8.5); c.line(12, 11, 12, 16.5); c.nokta(12, 8)


@ikon('ozellikler')
def _(c):
    for y, x in ((6.5, 15), (12, 9), (17.5, 13)):
        c.line(4, y, 20, y); c.cember(x, y, 2.2, dolu=True)


@ikon('katalog')
def _(c):
    c.poly([(5, 4), (19, 4), (19, 20), (5, 20)]); c.line(9, 4, 9, 20)
    c.line(12, 8, 16, 8); c.line(12, 11, 16, 11); c.line(12, 14, 16, 14)


@ikon('agac')
def _(c):
    c.dikd(4, 3.5, 6, 5); c.dikd(12, 10, 8, 5); c.dikd(12, 17, 8, 4.5)
    c.line(7, 8.5, 7, 19.3); c.line(7, 12.5, 12, 12.5); c.line(7, 19.3, 12, 19.3)


@ikon('suzgec')
def _(c):
    c.poly([(4, 5), (20, 5), (14, 12.5), (14, 19), (10, 21), (10, 12.5)])


@ikon('goruntu')
def _(c):
    c.poly([(3, 12), (7, 7), (17, 7), (21, 12), (17, 17), (7, 17)])
    c.cember(12, 12, 2.6)


@ikon('goz')
def _(c):
    c.poly([(3, 12), (7, 7.5), (17, 7.5), (21, 12), (17, 16.5), (7, 16.5)])
    c.cember(12, 12, 2.6)


@ikon('aks')
def _(c):
    c.line(8, 3.5, 8, 20.5); c.line(16, 3.5, 16, 20.5); c.line(3.5, 8, 20.5, 8); c.line(3.5, 16, 20.5, 16)
    c.cember(8, 3.5, 1.8, dolu=True); c.cember(16, 3.5, 1.8, dolu=True)
    c.cember(3.5, 8, 1.8, dolu=True); c.cember(3.5, 16, 1.8, dolu=True)


@ikon('kat')
def _(c):
    c.poly([(4, 9), (12, 4.5), (20, 9), (12, 13.5)])
    c.poly([(4, 13), (12, 17.5), (20, 13)], close=False)
    c.poly([(4, 16.5), (12, 21), (20, 16.5)], close=False)


@ikon('kolon')
def _(c):
    c.poly([(6, 4), (18, 4), (18, 7), (14, 7), (14, 17), (18, 17), (18, 20), (6, 20), (6, 17), (10, 17), (10, 7), (6, 7)])


@ikon('kiris')
def _(c):
    c.line(3, 8, 21, 8); c.line(3, 16, 21, 16); c.line(12, 8, 12, 16)
    c.line(3, 8, 3, 16); c.line(21, 8, 21, 16)


@ikon('ikincil')
def _(c):
    c.line(4, 5, 20, 5); c.line(4, 19, 20, 19); c.line(12, 5, 12, 19); c.line(6, 12, 18, 12)


@ikon('asik')
def _(c):
    c.line(4, 7, 20, 7); c.line(4, 12, 20, 12); c.line(4, 17, 20, 17); c.line(12, 4, 12, 20)


@ikon('konsol')
def _(c):
    c.line(5, 4, 5, 20); c.line(5, 9, 19, 9); c.line(19, 9, 19, 12); c.line(5, 13, 13, 13)


@ikon('capraz')
def _(c):
    c.dikd(4, 4, 16, 16); c.line(4, 4, 20, 20); c.line(20, 4, 4, 20)


@ikon('doseme')
def _(c):
    c.poly([(3, 15), (9, 7), (21, 7), (15, 15)]); c.line(3, 15, 3, 18); c.line(15, 15, 15, 18); c.line(3, 18, 15, 18)
    c.line(21, 7, 21, 10); c.line(15, 18, 21, 10)


@ikon('duvar')
def _(c):
    c.dikd(3, 5, 18, 14)
    c.line(3, 9.7, 21, 9.7); c.line(3, 14.3, 21, 14.3)
    c.line(9, 5, 9, 9.7); c.line(15, 5, 15, 9.7); c.line(12, 9.7, 12, 14.3); c.line(6, 14.3, 6, 19); c.line(15, 14.3, 15, 19)


@ikon('temel')
def _(c):
    c.line(10, 3, 10, 13); c.line(14, 3, 14, 13); c.line(10, 3, 14, 3)
    c.poly([(4, 13), (20, 13), (20, 18), (4, 18)])
    c.line(5, 21, 8, 21); c.line(10.5, 21, 13.5, 21); c.line(16, 21, 19, 21)


@ikon('hizli_kolon')
def _(c):
    c.poly([(5, 4), (15, 4), (15, 7), (12, 7), (12, 17), (15, 17), (15, 20), (5, 20), (5, 17), (8, 17), (8, 7), (5, 7)])
    c.poly([(20, 10), (17.5, 14.5), (19.6, 14.5), (18, 19)], close=False)


@ikon('hizli_kiris')
def _(c):
    c.line(3, 9, 15, 9); c.line(3, 15, 15, 15); c.line(9, 9, 9, 15); c.line(3, 9, 3, 15); c.line(15, 9, 15, 15)
    c.poly([(20.5, 4), (18, 8.5), (20.1, 8.5), (18.5, 13)], close=False)


@ikon('benzer')
def _(c):
    c.dikd(4, 4, 11, 11); c.poly([(9, 20), (20, 20), (20, 9)], close=False)
    c.line(9, 15, 14, 15); c.line(15, 9, 15, 15)
    c.poly([(7, 9.5), (9, 11.5), (12.5, 7.5)], close=False)


@ikon('ters')
def _(c):
    c.line(4, 8, 18, 8); c.poly([(15, 5), (18, 8), (15, 11)], close=False)
    c.line(20, 16, 6, 16); c.poly([(9, 13), (6, 16), (9, 19)], close=False)


@ikon('coz')
def _(c):
    c.dolu([(7, 4.5), (19, 12), (7, 19.5)])


@ikon('oynat')
def _(c):
    c.poly([(8, 5), (18, 12), (8, 19)])


@ikon('dur')
def _(c):
    c.dikd(6, 6, 12, 12, 1)


@ikon('disli')
def _(c):
    c.cember(12, 12, 3)
    for i in range(8):
        a = math.radians(i * 45)
        c.line(12 + 6.2 * math.cos(a), 12 + 6.2 * math.sin(a), 12 + 8.8 * math.cos(a), 12 + 8.8 * math.sin(a))
    c.cember(12, 12, 6.2)


@ikon('kucult')
def _(c):
    c.line(6, 12, 18, 12)


@ikon('buyut')
def _(c):
    c.dikd(6, 6, 12, 12)


@ikon('kapat')
def _(c):
    c.line(6, 6, 18, 18); c.line(18, 6, 6, 18)


@ikon('kapat_k')
def _(c):
    c.line(8, 8, 16, 16); c.line(16, 8, 8, 16)


@ikon('sag')
def _(c):
    c.poly([(9, 6), (15, 12), (9, 18)], close=False)


@ikon('asagi')
def _(c):
    c.poly([(6, 9.5), (12, 15.5), (18, 9.5)], close=False)


@ikon('yukari')
def _(c):
    c.poly([(6, 14.5), (12, 8.5), (18, 14.5)], close=False)


@ikon('nokta3')
def _(c):
    c.nokta(6, 12, 1.6); c.nokta(12, 12, 1.6); c.nokta(18, 12, 1.6)


@ikon('arti')
def _(c):
    c.line(12, 5, 12, 19); c.line(5, 12, 19, 12)


@ikon('onay')
def _(c):
    c.poly([(5, 12.5), (10, 17.5), (19, 7)], close=False)


@ikon('kilit')
def _(c):
    c.dikd(5, 11, 14, 9, 1.5); c.yay(12, 10, 4, 180, 360); c.line(8, 10, 8, 11); c.line(16, 10, 16, 11)


@ikon('tablo')
def _(c):
    c.dikd(3.5, 4.5, 17, 15); c.line(3.5, 9.5, 20.5, 9.5); c.line(3.5, 14.5, 20.5, 14.5); c.line(9, 4.5, 9, 19.5); c.line(15, 4.5, 15, 19.5)


@ikon('rapor')
def _(c):
    c.poly([(6, 3), (14, 3), (18, 7), (18, 21), (6, 21)]); c.line(14, 3, 14, 7); c.line(14, 7, 18, 7)
    c.line(9, 12, 15, 12); c.line(9, 15.5, 15, 15.5)


@ikon('yuk')
def _(c):
    c.line(3, 7, 21, 7)
    for x in (6, 12, 18):
        c.line(x, 7, x, 18); c.poly([(x - 2.2, 15.5), (x, 18), (x + 2.2, 15.5)], close=False)


@ikon('mesnet')
def _(c):
    c.poly([(12, 5), (18, 15), (6, 15)]); c.line(4, 18, 20, 18)
    c.line(6, 21, 8, 18); c.line(10, 21, 12, 18); c.line(14, 21, 16, 18)


@ikon('dugum')
def _(c):
    c.cember(12, 12, 3.2, dolu=True); c.line(12, 3, 12, 7.5); c.line(12, 16.5, 12, 21); c.line(3, 12, 7.5, 12); c.line(16.5, 12, 21, 12)


@ikon('tumu')
def _(c):
    c.line(12, 4, 12, 20); c.line(5, 8, 19, 16); c.line(19, 8, 5, 16)


@ikon('sabitle')
def _(c):
    c.poly([(9, 3.5), (15, 3.5), (14, 10), (18, 14), (6, 14), (10, 10)]); c.line(12, 14, 12, 21)


@ikon('yuzdur')
def _(c):
    c.poly([(10, 5), (5, 5), (5, 19), (19, 19), (19, 14)], close=False); c.line(13, 4.5, 19.5, 4.5); c.line(19.5, 4.5, 19.5, 11); c.line(19.5, 4.5, 11, 13)


@ikon('gecmis')
def _(c):
    c.cember(12, 12, 8.5); c.line(12, 7, 12, 12.5); c.line(12, 12.5, 15.5, 14.5)


@ikon('komut')
def _(c):
    c.poly([(5, 6), (11, 12), (5, 18)], close=False); c.line(13, 18, 20, 18)


@ikon('deform')
def _(c):
    c.line(4, 20, 4, 4); c.line(4, 20, 20, 20)
    pts = [(6 + i * 0.7, 13 - 5 * math.sin(i * 0.165)) for i in range(21)]
    c.poly(pts, close=False)


@ikon('diyagram')
def _(c):
    c.line(4, 8, 20, 8)
    pts = [(4 + i * 0.8, 8 + 9 * (1 - ((i - 10) / 10.0) ** 2)) for i in range(21)]
    c.poly(pts, close=False)


@ikon('dc')
def _(c):
    c.dikd(4, 12, 4, 8); c.dikd(10, 7, 4, 13); c.dikd(16, 4, 4, 16)


@ikon('reaksiyon')
def _(c):
    c.line(4, 6, 20, 6); c.poly([(12, 6), (16, 12), (8, 12)]); c.line(12, 12, 12, 20); c.poly([(9.5, 17.5), (12, 20), (14.5, 17.5)], close=False)


@ikon('yonetmelik')
def _(c):
    c.poly([(5, 4), (19, 4), (19, 20), (5, 20)]); c.line(8, 8, 16, 8); c.line(8, 11.5, 16, 11.5); c.line(8, 15, 13, 15)


@ikon('celik')
def _(c):
    c.poly([(6, 4), (18, 4), (18, 7), (14, 7), (14, 17), (18, 17), (18, 20), (6, 20), (6, 17), (10, 17), (10, 7), (6, 7)])


@ikon('beton')
def _(c):
    c.dikd(4, 4, 16, 16, 1); c.nokta(8, 8, 1.1); c.nokta(14, 10, 1.1); c.nokta(9, 15, 1.1); c.nokta(16, 16, 1.1)


@ikon('kompozit')
def _(c):
    c.dikd(3, 4, 18, 5); c.line(9, 9, 15, 9); c.line(12, 9, 12, 17); c.line(8, 17, 16, 17); c.line(8, 20, 16, 20)


@ikon('disa')
def _(c):
    c.poly([(6, 10), (6, 20), (18, 20), (18, 10)], close=False); c.line(12, 3.5, 12, 14); c.poly([(9, 7), (12, 3.5), (15, 7)], close=False)


@ikon('yardim')
def _(c):
    c.cember(12, 12, 8.5); c.yay(12, 10, 3, 200, 450); c.line(12, 13, 12, 14.5); c.nokta(12, 17.5, 1.1)


@ikon('kopyala')
def _(c):
    c.dikd(8, 8, 12, 12, 1); c.poly([(5, 15), (4, 15), (4, 4), (15, 4), (15, 5)], close=False)


@ikon('tasi')
def _(c):
    c.line(4, 12, 20, 12); c.poly([(16, 8), (20, 12), (16, 16)], close=False); c.poly([(8, 8), (4, 12), (8, 16)], close=False)


@ikon('ayna')
def _(c):
    c.line(12, 3, 12, 21); c.poly([(4, 7), (9, 12), (4, 17)]); c.poly([(20, 7), (15, 12), (20, 17)])


@ikon('cogalt')
def _(c):
    c.dikd(3.5, 10, 7, 10); c.dikd(13.5, 10, 7, 10); c.line(7, 4, 7, 7); c.line(17, 4, 17, 7); c.line(7, 4, 17, 4)


@ikon('kalem')
def _(c):
    c.poly([(4, 20), (5, 15.5), (16, 4.5), (19.5, 8), (8.5, 19)]); c.line(13.5, 7, 17, 10.5)


@ikon('sil')
def _(c):
    c.line(5, 7, 19, 7); c.line(10, 4, 14, 4); c.poly([(7, 7), (8, 20), (16, 20), (17, 7)], close=False); c.line(10.5, 10, 10.8, 17); c.line(13.5, 10, 13.2, 17)


@ikon('kaydet')
def _(c):
    c.poly([(4, 4), (16, 4), (20, 8), (20, 20), (4, 20)]); c.dikd(8, 4, 8, 5); c.dikd(7.5, 13, 9, 7)


@ikon('ac')
def _(c):
    c.poly([(3, 7), (3, 19), (21, 19), (21, 9), (11, 9), (9, 7)]); c.line(3, 12, 21, 12)


@ikon('geri')
def _(c):
    c.yay(12, 13, 6.5, 180, 420); c.poly([(4.5, 7), (5.5, 13), (11, 11.5)], close=False)


@ikon('ileri')
def _(c):
    c.yay(12, 13, 6.5, 120, 360); c.poly([(19.5, 7), (18.5, 13), (13, 11.5)], close=False)


@ikon('bos')
def _(c):
    pass


# ---------------------------------------------------------------- tuval
class Tuval:
    def __init__(self, W, H, S=1, bg=(255, 255, 255)):
        self.W, self.H, self.S = W, H, S
        self.im = Image.new('RGB', (int(W * S), int(H * S)), bg)
        self.d = ImageDraw.Draw(self.im, 'RGBA')
        self._mask_cache = {}

    # --- yardımcılar
    def p(self, v):
        return int(round(v * self.S))

    def dikd(self, x, y, w, h, fill=None, outline=None, lw=1):
        x0, y0, x1, y1 = self.p(x), self.p(y), self.p(x + w) - 1, self.p(y + h) - 1
        if x1 < x0 or y1 < y0:
            return
        self.d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=max(1, self.p(lw)))

    def yatay(self, x0, x1, y, renk, lw=1):
        self.dikd(x0, y, x1 - x0, lw, fill=renk)

    def dusey(self, x, y0, y1, renk, lw=1):
        self.dikd(x, y0, lw, y1 - y0, fill=renk)

    def cizgi(self, pts, renk, lw=1):
        self.d.line([(self.p(x), self.p(y)) for x, y in pts], fill=renk, width=max(1, self.p(lw)))

    def kesikli(self, x0, y0, x1, y1, renk, kesik=3, bosluk=3, lw=1):
        L = math.hypot(x1 - x0, y1 - y0)
        if L == 0:
            return
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        t = 0.0
        while t < L:
            t2 = min(L, t + kesik)
            self.cizgi([(x0 + ux * t, y0 + uy * t), (x0 + ux * t2, y0 + uy * t2)], renk, lw)
            t += kesik + bosluk

    def gradyan(self, x, y, w, h, c0, c1, dikey=True):
        n = self.p(h) if dikey else self.p(w)
        for i in range(n):
            t = i / max(1, n - 1)
            c = karistir(c0, c1, t)
            if dikey:
                self.d.line([(self.p(x), self.p(y) + i), (self.p(x + w) - 1, self.p(y) + i)], fill=c)
            else:
                self.d.line([(self.p(x) + i, self.p(y)), (self.p(x) + i, self.p(y + h) - 1)], fill=c)

    def _rr_mask(self, w, h, r, ss):
        """Süper örneklenmiş yuvarlatılmış dikdörtgen maskesi (piksel boyutlarında)."""
        key = (w, h, r, ss)
        m = self._mask_cache.get(key)
        if m is None:
            big = Image.new('L', (w * ss, h * ss), 0)
            ImageDraw.Draw(big).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=255)
            m = big.resize((w, h), LANCZOS) if ss > 1 else big
            self._mask_cache[key] = m
        return m

    def golge(self, x, y, w, h, r=8, bulanik=10, dy=4, a=0.14, renk=None):
        """Yumuşak gölge: bulanıklaştırılmış yuvarlatılmış maske."""
        S = self.S
        pad = int(bulanik * 3 * S)
        pw, ph = self.p(w), self.p(h)
        m = Image.new('L', (pw + 2 * pad, ph + 2 * pad), 0)
        ImageDraw.Draw(m).rounded_rectangle([pad, pad, pad + pw - 1, pad + ph - 1], radius=self.p(r), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(bulanik * S))
        if a != 1:
            m = m.point(lambda v: int(v * a))
        renk = renk or (20, 18, 12)
        self.im.paste(renk, (self.p(x) - pad, self.p(y + dy) - pad), m)

    def yuv(self, x, y, w, h, r=8, fill=None, outline=None, lw=1, golge=None):
        """Yuvarlatılmış dikdörtgen (kenar yumuşatmalı). golge=(bulanik, dy, alfa)."""
        if golge:
            self.golge(x, y, w, h, r, *golge)
        pw, ph = self.p(w), self.p(h)
        if pw <= 0 or ph <= 0:
            return
        pr = self.p(r)
        ss = 4 if max(pw, ph) <= 700 else 2
        if fill is not None:
            m = self._rr_mask(pw, ph, pr, ss)
            if len(fill) == 4:
                col = fill[:3]
                m = m.point(lambda v: int(v * fill[3] / 255))
            else:
                col = fill
            self.im.paste(col, (self.p(x), self.p(y)), m)
        if outline is not None:
            lwp = max(1, self.p(lw))
            big = Image.new('L', (pw * ss, ph * ss), 0)
            ImageDraw.Draw(big).rounded_rectangle([0, 0, pw * ss - 1, ph * ss - 1], radius=pr * ss,
                                                  outline=255, width=lwp * ss)
            m = big.resize((pw, ph), LANCZOS) if ss > 1 else big
            if len(outline) == 4:
                m = m.point(lambda v: int(v * outline[3] / 255))
                outline = outline[:3]
            self.im.paste(outline, (self.p(x), self.p(y)), m)

    def daire(self, cx, cy, r, fill=None, outline=None, lw=1):
        ss = 4
        pr = self.p(r)
        if pr <= 0:
            return
        size = pr * 2 + 2
        big = Image.new('L', (size * ss, size * ss), 0)
        bd = ImageDraw.Draw(big)
        if fill is not None:
            bd.ellipse([ss, ss, (size - 1) * ss, (size - 1) * ss], fill=255)
            m = big.resize((size, size), LANCZOS)
            self.im.paste(fill, (self.p(cx) - pr - 1, self.p(cy) - pr - 1), m)
        if outline is not None:
            big = Image.new('L', (size * ss, size * ss), 0)
            ImageDraw.Draw(big).ellipse([ss, ss, (size - 1) * ss, (size - 1) * ss], outline=255,
                                        width=max(1, int(round(lw * self.S * ss))))
            m = big.resize((size, size), LANCZOS)
            self.im.paste(outline, (self.p(cx) - pr - 1, self.p(cy) - pr - 1), m)

    # --- metin
    def font(self, boy, agirlik=400, aile='inter'):
        return Yazi.al(aile, boy * self.S, agirlik)

    def gen(self, s, boy, agirlik=400, aile='inter'):
        return self.font(boy, agirlik, aile).getlength(s) / self.S

    def yazi(self, x, y, s, boy=13, agirlik=400, renk=None, anchor='ls', aile='inter', maxw=None):
        f = self.font(boy, agirlik, aile)
        renk = renk or R['metin']
        if maxw is not None and f.getlength(s) / self.S > maxw:
            while s and f.getlength(s + '…') / self.S > maxw:
                s = s[:-1]
            s = s.rstrip() + '…'
        self.d.text((self.p(x), self.p(y)), s, font=f, fill=renk, anchor=anchor)
        return f.getlength(s) / self.S

    def yazi_orta(self, x, y, s, boy=13, agirlik=400, renk=None, aile='inter'):
        return self.yazi(x, y, s, boy, agirlik, renk, anchor='ms', aile=aile)

    def yazi_sag(self, x, y, s, boy=13, agirlik=400, renk=None, aile='inter'):
        return self.yazi(x, y, s, boy, agirlik, renk, anchor='rs', aile=aile)

    # --- ikon
    def ikon(self, ad, x, y, boy=16, renk=None, kalinlik=1.5):
        renk = renk or R['metin2']
        ss = 4
        px = self.p(boy)
        key = ('ikon', ad, px, kalinlik)
        m = self._mask_cache.get(key)
        if m is None:
            big = Image.new('L', (px * ss, px * ss), 0)
            k = px * ss / 24.0
            IKONLAR[ad](IkonKalem(big, k, kalinlik * self.S * ss))
            m = big.resize((px, px), LANCZOS)
            self._mask_cache[key] = m
        if len(renk) == 4:
            m = m.point(lambda v: int(v * renk[3] / 255))
            renk = renk[:3]
        self.im.paste(renk, (self.p(x), self.p(y)), m)

    def resim(self, im, x, y, h=None, w=None):
        """RGBA görseli oranını koruyarak yapıştırır (logolar yeniden çizilmez)."""
        if h is not None:
            ph = self.p(h)
            pw = int(round(im.width * ph / im.height))
        else:
            pw = self.p(w)
            ph = int(round(im.height * pw / im.width))
        r = im.resize((pw, ph), LANCZOS)
        self.im.paste(r, (self.p(x), self.p(y)), r)
        return pw / self.S, ph / self.S

    def yapistir(self, im, x, y, maske=None):
        if maske is not None:
            self.im.paste(im, (self.p(x), self.p(y)), maske)
        elif im.mode == 'RGBA':
            self.im.paste(im, (self.p(x), self.p(y)), im)
        else:
            self.im.paste(im, (self.p(x), self.p(y)))

    def kirp(self, x, y, w, h):
        return self.im.crop((self.p(x), self.p(y), self.p(x + w), self.p(y + h)))

    def kaydet(self, yol, olcek=1):
        im = self.im
        if olcek != 1:
            im = im.resize((int(round(im.width * olcek)), int(round(im.height * olcek))), LANCZOS)
        im.save(yol, optimize=True)
        return im
