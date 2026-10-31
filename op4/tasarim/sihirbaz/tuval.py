#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yönetmelik sihirbazı taslakları — çizim altyapısı (Atölye tuval.py kopyası; renkler palet sözlüğünden): renk belirteçleri, Inter değişken yazı tipi, mantıksal-piksel tuval,
elle çizilmiş tek renkli çizgi simgeler (24 birimlik ızgara, 1,5 px kalem, 4× örnekleme).
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

KIMLIK = "/home/user/matris-ogren/op4/kimlik"
FONT_INTER = os.path.join(KIMLIK, "fontlar", "inter-Inter[opsz,wght].ttf")
LOGO_SIMGE = os.path.join(KIMLIK, "opus-fortis-simge-koyu.png")
LOGO_YAZI = os.path.join(KIMLIK, "opus-fortis-yazi-acik-zemin.png")

# ----------------------------------------------------------------------------
# Renk belirteçleri: bu dosyada SABİT RENK YOKTUR. Bütün renkler uret.py'nin başındaki tek PALET sözlüğünden
# palet_kur() ile gelir (modernize palet gelince yalnız o sözlük değişir).
# ----------------------------------------------------------------------------
C = {}


def palet_kur(palet):
    """Tek palet sözlüğünü etkinleştirir (C yerinde güncellenir; varsayılan değerler çağrı anında okunur)."""
    C.clear()
    C.update(palet)


def hex2rgb(h):
    if isinstance(h, tuple):
        return h[:3]
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def karisim(a, b, t):
    """a ile b renklerini t oranında karıştır (t=0 → a)."""
    a, b = hex2rgb(a), hex2rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def rgba(h, a):
    return hex2rgb(h) + (int(round(a * 255)),)


# ----------------------------------------------------------------------------
# Yazı tipleri
# ----------------------------------------------------------------------------
_FONTLAR = {}


def yazi_tipi(boyut_px, agirlik=400, olcek=1):
    """Inter değişken yazı tipi; opsz mantıksal boyuttan, piksel boyutu ölçekle çarpılır."""
    key = (boyut_px, agirlik, olcek)
    f = _FONTLAR.get(key)
    if f is None:
        f = ImageFont.truetype(FONT_INTER, max(1, int(round(boyut_px * olcek))))
        opsz = min(32, max(14, boyut_px))
        f.set_variation_by_axes([opsz, agirlik])
        _FONTLAR[key] = f
    return f


def taban(y, h, boyut):
    """h yüksekliğindeki satırın ortasına büyük harf yüksekliğine göre taban çizgisi (Inter cap ≈ 0,727 em)."""
    return y + h / 2 + 0.36 * boyut


# ----------------------------------------------------------------------------
# Tuval: mantıksal piksel koordinatlarıyla çizim (ölçek s = 1 ya da 2)
# ----------------------------------------------------------------------------
class Tuval:
    def __init__(self, w, h, s=1, zemin=None):
        zemin = zemin or C["zemin"]
        self.s = s
        self.w, self.h = w, h
        self.img = Image.new("RGB", (int(w * s), int(h * s)), zemin)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def p(self, v):
        return int(round(v * self.s))

    def _yenile(self):
        self.d = ImageDraw.Draw(self.img, "RGBA")

    # --- temel biçimler -------------------------------------------------------
    def dikdortgen(self, x, y, w, h, dolgu=None, kenar=None, kalinlik=1, r=0):
        x0, y0, x1, y1 = self.p(x), self.p(y), self.p(x + w) - 1, self.p(y + h) - 1
        if x1 < x0 or y1 < y0:
            return
        if r > 0:
            self.d.rounded_rectangle([x0, y0, x1, y1], radius=self.p(r), fill=dolgu, outline=kenar,
                                     width=self.p(kalinlik) if kenar else 0)
        else:
            self.d.rectangle([x0, y0, x1, y1], fill=dolgu, outline=kenar, width=self.p(kalinlik) if kenar else 0)

    def yatay(self, x0, x1, y, renk, kalinlik=1):
        a, b = self.p(x0), self.p(x1) - 1
        c, d = self.p(y), max(self.p(y), self.p(y + kalinlik) - 1)
        if b >= a:
            self.d.rectangle([a, c, b, d], fill=renk)

    def dikey(self, x, y0, y1, renk, kalinlik=1):
        a, b = self.p(x), max(self.p(x), self.p(x + kalinlik) - 1)
        c, d = self.p(y0), self.p(y1) - 1
        if d >= c:
            self.d.rectangle([a, c, b, d], fill=renk)

    def cizgi(self, x0, y0, x1, y1, renk, kalinlik=1):
        self.d.line([(x0 * self.s, y0 * self.s), (x1 * self.s, y1 * self.s)], fill=renk, width=max(1, self.p(kalinlik)))

    def cokgen(self, pts, dolgu=None, kenar=None, kalinlik=1):
        P = [(x * self.s, y * self.s) for x, y in pts]
        self.d.polygon(P, fill=dolgu, outline=kenar, width=max(1, self.p(kalinlik)) if kenar else 0)

    def daire(self, cx, cy, r, dolgu=None, kenar=None, kalinlik=1):
        self.d.ellipse([self.p(cx - r), self.p(cy - r), self.p(cx + r), self.p(cy + r)], fill=dolgu, outline=kenar,
                       width=max(1, self.p(kalinlik)) if kenar else 0)

    def kesik_yatay(self, x0, x1, y, renk, parca=3, bosluk=2, kalinlik=1):
        x = x0
        while x < x1:
            self.yatay(x, min(x1, x + parca), y, renk, kalinlik)
            x += parca + bosluk

    def kesik_dikey(self, x, y0, y1, renk, parca=3, bosluk=2, kalinlik=1):
        y = y0
        while y < y1:
            self.dikey(x, y, min(y1, y + parca), renk, kalinlik)
            y += parca + bosluk

    def gradyan(self, x, y, w, h, ust, alt):
        ust, alt = hex2rgb(ust), hex2rgb(alt)
        H = max(1, self.p(h))
        band = Image.new("RGB", (1, H))
        px = band.load()
        for i in range(H):
            t = i / max(1, H - 1)
            px[0, i] = tuple(int(round(ust[k] + (alt[k] - ust[k]) * t)) for k in range(3))
        band = band.resize((max(1, self.p(w)), H))
        self.img.paste(band, (self.p(x), self.p(y)))
        self._yenile()

    # --- yazı --------------------------------------------------------------------
    def yazi(self, x, y, metin, boyut=12, agirlik=400, renk=None, hiza="ls", tnum=False):
        renk = renk or C["metin"]
        f = yazi_tipi(boyut, agirlik, self.s)
        feats = ["tnum"] if tnum else None
        self.d.text((x * self.s, y * self.s), metin, font=f, fill=renk, anchor=hiza, features=feats)

    def yazi_gen(self, metin, boyut=12, agirlik=400, tnum=False):
        f = yazi_tipi(boyut, agirlik, self.s)
        feats = ["tnum"] if tnum else None
        return f.getlength(metin, features=feats) / self.s

    def yazi_orta(self, cx, y, metin, boyut=12, agirlik=400, renk=None, tnum=False):
        self.yazi(cx - self.yazi_gen(metin, boyut, agirlik, tnum) / 2, y, metin, boyut, agirlik, renk, tnum=tnum)

    def yazi_sag(self, xr, y, metin, boyut=12, agirlik=400, renk=None, tnum=False):
        self.yazi(xr - self.yazi_gen(metin, boyut, agirlik, tnum), y, metin, boyut, agirlik, renk, tnum=tnum)

    def yazi_kes(self, metin, max_w, boyut=12, agirlik=400):
        """Sığmayan metni … ile kısalt."""
        if self.yazi_gen(metin, boyut, agirlik) <= max_w:
            return metin
        while metin and self.yazi_gen(metin + "…", boyut, agirlik) > max_w:
            metin = metin[:-1]
        return metin.rstrip() + "…"

    def yazi_dikey(self, x, y, metin, boyut=11, agirlik=500, renk=None):
        renk = renk or C["metin2"]
        """Saat yönünde 90° döndürülmüş yazı (yukarıdan aşağı okunur); (x,y) sol-üst köşe."""
        f = yazi_tipi(boyut, agirlik, self.s)
        w = int(f.getlength(metin)) + 4
        h = int(boyut * self.s * 1.4)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((2, int(boyut * self.s * 1.05)), metin, font=f, fill=renk, anchor="ls")
        im = im.rotate(-90, expand=True)
        self.img.paste(im, (self.p(x), self.p(y)), im)
        self._yenile()

    # --- simge / resim ---------------------------------------------------------
    def simge(self, ad, cx, cy, boyut=16, renk=None, kalinlik=1.5):
        renk = renk or C["metin"]
        im = simge_ciz(ad, boyut, self.s, renk, kalinlik)
        self.img.paste(im, (self.p(cx - boyut / 2), self.p(cy - boyut / 2)), im)
        self._yenile()

    def resim(self, im, x, y, w=None, h=None):
        if w is not None:
            oran = im.width / im.height
            if h is None:
                h = w / oran
            im = im.resize((max(1, self.p(w)), max(1, self.p(h))), Image.LANCZOS)
        self.img.paste(im, (self.p(x), self.p(y)), im if im.mode == "RGBA" else None)
        self._yenile()

    def yapistir(self, im, x, y):
        self.img.paste(im, (self.p(x), self.p(y)), im if im.mode == "RGBA" else None)
        self._yenile()

    def golge(self, x, y, w, h, r=4, yaricap=6, alfa=0.18, dy=2):
        """Yumuşak düşen gölge (kutunun altına)."""
        pad = yaricap * 3
        W, H = self.p(w + 2 * pad), self.p(h + 2 * pad)
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        dd.rounded_rectangle([self.p(pad), self.p(pad + dy), self.p(pad + w), self.p(pad + h + dy)],
                             radius=self.p(r), fill=rgba(C["golge"], alfa))
        im = im.filter(ImageFilter.GaussianBlur(self.p(yaricap)))
        self.img.paste(im, (self.p(x - pad), self.p(y - pad)), im)
        self._yenile()

    def karart(self, x, y, w, h, alfa=0.18):
        self.d.rectangle([self.p(x), self.p(y), self.p(x + w) - 1, self.p(y + h) - 1], fill=rgba(C["karartma"], alfa))

    # --- bileşik küçük parçalar ---------------------------------------------------
    def sevron(self, cx, cy, yon="asagi", boyut=10, renk=None):
        renk = renk or C["metin3"]
        self.simge({"asagi": "sevron_asagi", "sag": "sevron_sag", "ust": "sevron_ust", "sol": "sevron_sol"}[yon], cx, cy, boyut, renk, 1.4)

    def onay_kutusu(self, x, y, isaretli, boyut=12, renk=None):
        renk = renk or C["vurgu"]
        if isaretli:
            self.dikdortgen(x, y, boyut, boyut, dolgu=renk, r=2)
            self.simge("onay", x + boyut / 2, y + boyut / 2, boyut - 2, C["beyaz"], 1.8)
        else:
            self.dikdortgen(x, y, boyut, boyut, dolgu=C["yuzey"], kenar=C["onay_kenar"], r=2)

    def radyo(self, cx, cy, secili, r=6):
        self.daire(cx, cy, r, dolgu=C["yuzey"], kenar=C["vurgu"] if secili else C["onay_kenar"], kalinlik=1)
        if secili:
            self.daire(cx, cy, r - 3, dolgu=C["vurgu"])

    def anahtar(self, x, y, acik, w=26, h=14):
        """Kaydırmalı aç/kapa anahtarı."""
        if acik:
            self.dikdortgen(x, y, w, h, dolgu=C["vurgu"], r=h / 2)
            self.daire(x + w - h / 2, y + h / 2, h / 2 - 2, dolgu=C["beyaz"])
        else:
            self.dikdortgen(x, y, w, h, dolgu=C["giris_kenar"], r=h / 2)
            self.daire(x + h / 2, y + h / 2, h / 2 - 2, dolgu=C["beyaz"])

    def kisayol(self, x, y, metin, boyut=10, h=15):
        """Klavye kısayolu rozeti; genişliğini döndürür."""
        w = self.yazi_gen(metin, boyut, 500) + 8
        self.dikdortgen(x, y, w, h, dolgu=C["zemin"], kenar=C["cizgi"], r=2)
        self.yazi(x + 4, taban(y, h, boyut), metin, boyut, 500, C["metin2"])
        return w

    def dugme(self, x, y, w, h, metin, birincil=False, boyut=12, ikincil_kenar=None):
        if birincil:
            self.dikdortgen(x, y, w, h, dolgu=C["vurgu"], r=3)
            self.yazi_orta(x + w / 2, taban(y, h, boyut), metin, boyut, 600, C["beyaz"])
        else:
            self.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=ikincil_kenar or C["dugme_kenar"], r=3)
            self.yazi_orta(x + w / 2, taban(y, h, boyut), metin, boyut, 500, C["metin"])

    def acilir(self, x, y, w, h, metin, boyut=12, odak=False, salt=False, renk=None):
        """Açılır liste kutusu."""
        kenar = C["vurgu"] if odak else (C["giris_kenar"] if not salt else C["cizgi2"])
        self.dikdortgen(x, y, w, h, dolgu=C["yuzey"] if not salt else C["yuzey2"], kenar=kenar, r=3, kalinlik=1)
        self.yazi(x + 7, taban(y, h, boyut), self.yazi_kes(metin, w - 26, boyut), boyut, 400, renk or C["metin"])
        self.sevron(x + w - 10, y + h / 2 + 0.5, "asagi", 9, C["metin2"])

    def giris(self, x, y, w, h, metin, boyut=12, odak=False, imlec=False, renk=None, hiza="sol"):
        kenar = C["vurgu"] if odak else C["giris_kenar"]
        self.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=kenar, r=3)
        if hiza == "sag":
            self.yazi_sag(x + w - 7, taban(y, h, boyut), metin, boyut, 400, renk or C["metin"], tnum=True)
        else:
            self.yazi(x + 7, taban(y, h, boyut), metin, boyut, 400, renk or C["metin"], tnum=True)
            if imlec:
                tx = x + 7 + self.yazi_gen(metin, boyut, 400, True) + 3   # 3 px boşluk: imleç harfe yapışmasın
                self.dikey(tx, y + 4, y + h - 4, C["vurgu"], 1)


# ----------------------------------------------------------------------------
# Simge kütüphanesi: 4× örneklemeli küçük tuvale çizgi, sonra LANCZOS küçültme
# ----------------------------------------------------------------------------
_SIMGE_ONBELLEK = {}


def simge_ciz(ad, boyut, s, renk, kalinlik=1.5):
    key = (ad, boyut, s, renk, kalinlik)
    if key in _SIMGE_ONBELLEK:
        return _SIMGE_ONBELLEK[key]
    SS = 4
    N = int(round(boyut * s * SS))
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rgb = hex2rgb(renk)
    col = rgb + (255,)
    u = N / 24.0  # 24 birimlik simge ızgarası
    k = max(1.0, kalinlik * s * SS)

    def L(pts, w=None, dolgu=None, kapali=False):
        P = [(p[0] * u, p[1] * u) for p in pts]
        if dolgu is not None:
            d.polygon(P, fill=col)
            return
        if kapali:
            P = P + [P[0]]
        d.line(P, fill=col, width=int(round(w if w else k)), joint="curve")

    def R(x0, y0, x1, y1, w=None, dolgu=False):
        if dolgu:
            d.rectangle([x0 * u, y0 * u, x1 * u, y1 * u], fill=col)
        else:
            d.rectangle([x0 * u, y0 * u, x1 * u, y1 * u], outline=col, width=int(round(w if w else k)))

    def E(x0, y0, x1, y1, w=None, dolgu=False):
        if dolgu:
            d.ellipse([x0 * u, y0 * u, x1 * u, y1 * u], fill=col)
        else:
            d.ellipse([x0 * u, y0 * u, x1 * u, y1 * u], outline=col, width=int(round(w if w else k)))

    def nokta(x, y, r=1.6):
        d.ellipse([(x - r) * u, (y - r) * u, (x + r) * u, (y + r) * u], fill=col)

    def I_dik(cx, y0, y1, b=5):
        L([(cx - b, y0), (cx + b, y0)]); L([(cx - b, y1), (cx + b, y1)]); L([(cx, y0), (cx, y1)], w=k * 1.6)

    a = ad
    if a == "kolon":        # dikey I profil
        I_dik(12, 4, 20)
        L([(9, 4), (9, 6.5)]); L([(15, 4), (15, 6.5)]); L([(9, 20), (9, 17.5)]); L([(15, 20), (15, 17.5)])
    elif a == "kiris":      # yatay I kiriş
        L([(3, 8), (21, 8)]); L([(3, 16), (21, 16)]); L([(3, 12), (21, 12)], w=k * 1.6)
        L([(3, 8), (3, 16)]); L([(21, 8), (21, 16)])
    elif a == "kiris_ana":
        L([(3, 7), (21, 7)], w=k * 1.4); L([(3, 17), (21, 17)], w=k * 1.4); L([(3, 12), (21, 12)], w=k * 1.6)
    elif a == "kiris_tali":
        L([(3, 9), (21, 9)]); L([(3, 15), (21, 15)]); L([(3, 12), (21, 12)])
    elif a == "asik":       # Z aşık
        L([(6, 6), (18, 6)]); L([(18, 6), (6, 18)]); L([(6, 18), (18, 18)])
    elif a == "capraz":     # çerçeve içinde X
        R(4, 4, 20, 20); L([(4, 4), (20, 20)]); L([(20, 4), (4, 20)])
    elif a == "capraz_v":
        R(4, 4, 20, 20); L([(4, 4), (12, 20), (20, 4)])
    elif a == "capraz_tek":
        R(4, 4, 20, 20); L([(4, 20), (20, 4)])
    elif a == "doseme":     # plaka, perspektif paralelkenar + kalınlık
        L([(3, 14), (9, 6), (21, 6), (15, 14)], kapali=True); L([(3, 14), (3, 17), (15, 17), (15, 14)]); L([(15, 17), (21, 9), (21, 6)])
    elif a == "doseme_bosluk":
        L([(3, 14), (9, 6), (21, 6), (15, 14)], kapali=True); L([(8, 11.5), (10.5, 8.5), (16, 8.5), (13.5, 11.5)], kapali=True)
    elif a == "duvar":      # tuğla örgü
        R(3, 5, 21, 19); L([(3, 10), (21, 10)]); L([(3, 14.5), (21, 14.5)])
        L([(9, 5), (9, 10)]); L([(15, 5), (15, 10)]); L([(12, 10), (12, 14.5)]); L([(6, 10), (6, 14.5)]); L([(18, 10), (18, 14.5)]); L([(9, 14.5), (9, 19)]); L([(15, 14.5), (15, 19)])
    elif a == "temel":      # kolon + pabuç
        L([(10, 3), (10, 13)]); L([(14, 3), (14, 13)]); L([(10, 3), (14, 3)])
        L([(4, 13), (20, 13), (20, 20), (4, 20)], kapali=True); L([(4, 22), (20, 22)])
    elif a == "temel_surekli":
        L([(3, 12), (21, 12), (21, 19), (3, 19)], kapali=True); L([(7, 5), (7, 12)]); L([(17, 5), (17, 12)])
    elif a == "temel_radye":
        R(3, 11, 21, 17); L([(6, 5), (6, 11)]); L([(12, 5), (12, 11)]); L([(18, 5), (18, 11)]); L([(3, 20), (21, 20)])
    elif a == "aks":        # aks çizgileri ve baloncuklar
        L([(8, 5), (8, 21)]); L([(16, 5), (16, 21)]); L([(3, 10), (21, 10)]); L([(3, 16), (21, 16)])
        E(5.5, 2, 10.5, 7, dolgu=True); E(13.5, 2, 18.5, 7, dolgu=True)
    elif a == "kat":        # kat seviyeleri
        L([(4, 6), (20, 6)]); L([(4, 12), (20, 12)]); L([(4, 18), (20, 18)])
        L([(20, 6), (22, 3), (18, 3)], dolgu=True); L([(20, 12), (22, 9), (18, 9)], dolgu=True); L([(20, 18), (22, 15), (18, 15)], dolgu=True)
    elif a == "kat_verisi":
        R(3, 4, 21, 20); L([(3, 9), (21, 9)]); L([(3, 14), (21, 14)]); L([(9, 4), (9, 20)])
    elif a == "duzlem":     # çalışma düzlemi
        L([(3, 15), (9, 6), (21, 6), (15, 15)], kapali=True); L([(12, 10.5), (12, 2)]); L([(9.5, 4.5), (12, 2), (14.5, 4.5)])
    elif a == "hizli_kolon":  # aks kesişimine tek tık
        L([(4, 12), (20, 12)]); L([(12, 4), (12, 20)]); nokta(12, 12, 2.2)
        L([(15, 14), (15, 22), (17.2, 19.8), (18.8, 22.6), (20.4, 21.6), (18.8, 18.8), (21.6, 18.8)], dolgu=True)
    elif a == "hizli_kiris":  # aks parçasına tek tık
        L([(3, 10), (21, 10)], w=k * 1.6); nokta(3, 10, 1.6); nokta(21, 10, 1.6)
        L([(11, 12), (11, 21), (13.4, 18.6), (15.2, 21.6), (16.8, 20.6), (15, 17.6), (18, 17.6)], dolgu=True)
    elif a == "hizli_capraz":
        L([(4, 4), (20, 20)]); L([(20, 4), (4, 20)]); nokta(12, 12, 1.8)
    elif a == "izgara":
        R(3, 3, 21, 21); L([(9, 3), (9, 21)]); L([(15, 3), (15, 21)]); L([(3, 9), (21, 9)]); L([(3, 15), (21, 15)])
    elif a == "kesit":      # I kesit ana hat
        L([(5, 4), (19, 4), (19, 7), (13.5, 7), (13.5, 17), (19, 17), (19, 20), (5, 20), (5, 17), (10.5, 17), (10.5, 7), (5, 7)], kapali=True)
    elif a == "malzeme":    # küp
        L([(4, 9), (12, 5), (20, 9), (12, 13)], kapali=True); L([(4, 9), (4, 17), (12, 21), (20, 17), (20, 9)]); L([(12, 13), (12, 21)])
    elif a == "kutuphane":  # kitaplar
        R(4, 4, 8, 20); R(10, 4, 14, 20); L([(16, 5), (20.5, 5.8), (18.4, 20.5), (14, 19.5)], kapali=True)
    elif a == "sec":        # imleç oku
        L([(6, 3), (6, 19), (10, 15), (13, 21), (15.5, 19.8), (12.5, 14), (18, 14)], dolgu=True)
    elif a == "imlec":      # beyaz dolgulu, çerçeveli imleç (model üstünde)
        pts = [(6, 3), (6, 19), (10, 15), (13, 21), (15.5, 19.8), (12.5, 14), (18, 14)]
        d.polygon([(p[0] * u, p[1] * u) for p in pts], fill=hex2rgb(C["beyaz"]) + (255,), outline=col, width=int(k))
    elif a == "sec_pencere":
        for i in range(0, 18, 4):
            L([(3 + i, 3), (3 + i + 2, 3)]); L([(3 + i, 21), (3 + i + 2, 21)]); L([(3, 3 + i), (3, 3 + i + 2)]); L([(21, 3 + i), (21, 3 + i + 2)])
        L([(10, 9), (10, 19), (12.5, 16.5), (14.5, 20.5), (16.2, 19.6), (14.2, 15.7), (17.5, 15.7)], dolgu=True)
    elif a == "suz":        # huni
        L([(3, 4), (21, 4), (14, 12.5), (14, 20), (10, 17.5), (10, 12.5)], kapali=True)
    elif a == "sec_suz":    # huni + ok
        L([(3, 4), (17, 4), (11.5, 11), (11.5, 18), (8, 15.5), (8, 11)], kapali=True)
        L([(15, 13), (15, 22), (17.4, 19.6), (19.2, 22.6), (20.8, 21.6), (19, 18.6), (22, 18.6)], dolgu=True)
    elif a == "benzer":     # iki özdeş çubuk, biri seçili
        R(3, 5, 21, 9); R(3, 15, 21, 19); L([(3, 12), (21, 12)], w=k * 0.6)
    elif a == "ters":       # seçimi tersine çevir
        R(3, 3, 11, 11, dolgu=True); R(13, 13, 21, 21, dolgu=True); R(13, 3, 21, 11); R(3, 13, 11, 21)
    elif a == "katman":
        L([(12, 3), (21, 8), (12, 13), (3, 8)], kapali=True); L([(3, 12), (12, 17), (21, 12)]); L([(3, 16), (12, 21), (21, 16)])
    elif a == "etiket":
        L([(3, 3), (12, 3), (21, 12), (12, 21), (3, 12)], kapali=True); nokta(7.5, 7.5, 1.4)
    elif a == "ice_aktar":
        L([(4, 10), (4, 21), (20, 21), (20, 10)]); L([(12, 2), (12, 15)]); L([(7.5, 10.5), (12, 15), (16.5, 10.5)])
    elif a == "disa_aktar":
        L([(4, 10), (4, 21), (20, 21), (20, 10)]); L([(12, 15), (12, 2)]); L([(7.5, 6.5), (12, 2), (16.5, 6.5)])
    elif a == "dogrula":
        E(3, 3, 21, 21); L([(7.5, 12.5), (10.8, 15.8), (16.8, 8.8)])
    elif a == "rapor":
        L([(5, 2.5), (14, 2.5), (19, 7.5), (19, 21.5), (5, 21.5)], kapali=True); L([(14, 2.5), (14, 7.5), (19, 7.5)]); L([(8, 12), (16, 12)]); L([(8, 15.5), (16, 15.5)]); L([(8, 19), (13, 19)])
    elif a == "ayar":
        for i in range(8):
            ang = i * math.pi / 4
            L([(12 + 7 * math.cos(ang), 12 + 7 * math.sin(ang)), (12 + 10 * math.cos(ang), 12 + 10 * math.sin(ang))], w=k * 1.6)
        E(5, 5, 19, 19); E(9.5, 9.5, 14.5, 14.5)
    elif a == "ara":
        E(4, 4, 15, 15); L([(13.5, 13.5), (20.5, 20.5)], w=k * 1.3)
    elif a == "kapat":
        L([(6, 6), (18, 18)]); L([(18, 6), (6, 18)])
    elif a == "kucult":
        L([(5, 12), (19, 12)])
    elif a == "buyut":
        R(5.5, 5.5, 18.5, 18.5)
    elif a == "geri_al":
        L([(4, 10), (20, 10)]); L([(9, 5), (4, 10), (9, 15)]); L([(20, 10), (20, 16), (10, 16)])
    elif a == "yinele":
        L([(20, 10), (4, 10)]); L([(15, 5), (20, 10), (15, 15)]); L([(4, 10), (4, 16), (14, 16)])
    elif a == "kaydet":
        L([(4, 4), (17, 4), (20, 7), (20, 20), (4, 20)], kapali=True); R(8, 4, 15, 9); R(7.5, 13, 16.5, 20)
    elif a == "ac":
        L([(3, 6), (9, 6), (11, 8.5), (21, 8.5), (21, 19), (3, 19)], kapali=True); L([(3, 12), (21, 12)])
    elif a == "yeni":
        L([(5, 2.5), (14, 2.5), (19, 7.5), (19, 21.5), (5, 21.5)], kapali=True); L([(14, 2.5), (14, 7.5), (19, 7.5)]); L([(12, 11), (12, 18)]); L([(8.5, 14.5), (15.5, 14.5)])
    elif a == "yazdir":
        L([(7, 9), (7, 3), (17, 3), (17, 9)]); R(3, 9, 21, 17); L([(7, 14), (7, 21), (17, 21), (17, 14)])
    elif a == "ok_asagi":
        L([(7, 9.5), (17, 9.5), (12, 15)], dolgu=True)
    elif a == "sevron_asagi":
        L([(6, 9), (12, 15), (18, 9)])
    elif a == "sevron_sag":
        L([(9, 6), (15, 12), (9, 18)])
    elif a == "sevron_ust":
        L([(6, 15), (12, 9), (18, 15)])
    elif a == "sevron_sol":
        L([(15, 6), (9, 12), (15, 18)])
    elif a == "sevron_cift_ust":
        L([(6, 12), (12, 6), (18, 12)]); L([(6, 18), (12, 12), (18, 18)])
    elif a == "sevron_cift_asagi":
        L([(6, 6), (12, 12), (18, 6)]); L([(6, 12), (12, 18), (18, 12)])
    elif a == "pin":
        L([(9, 3), (15, 3)]); L([(10, 3), (10, 11), (6.5, 14), (17.5, 14), (14, 11), (14, 3)]); L([(12, 14), (12, 21)])
    elif a == "goz":
        L([(2.5, 12), (6.5, 7), (12, 5.5), (17.5, 7), (21.5, 12), (17.5, 17), (12, 18.5), (6.5, 17)], kapali=True); E(9, 9, 15, 15)
    elif a == "goz_kapali":
        L([(2.5, 12), (6.5, 7), (12, 5.5), (17.5, 7), (21.5, 12)]); L([(4, 20), (20, 4)])
    elif a == "proje":
        R(4, 5, 20, 21); L([(8, 9), (10, 9)]); L([(14, 9), (16, 9)]); L([(8, 13), (10, 13)]); L([(14, 13), (16, 13)]); L([(10.5, 21), (10.5, 17), (13.5, 17), (13.5, 21)])
    elif a == "dugum":
        L([(12, 3), (12, 21)]); L([(3, 12), (21, 12)]); E(8.5, 8.5, 15.5, 15.5, dolgu=True)
    elif a == "tasi":
        L([(12, 3), (12, 21)]); L([(3, 12), (21, 12)]); L([(9, 6), (12, 3), (15, 6)]); L([(9, 18), (12, 21), (15, 18)]); L([(6, 9), (3, 12), (6, 15)]); L([(18, 9), (21, 12), (18, 15)])
    elif a == "kopyala":
        R(8, 8, 21, 21); L([(16, 8), (16, 3), (3, 3), (3, 16), (8, 16)])
    elif a == "dondur":
        d.arc([4 * u, 4 * u, 20 * u, 20 * u], start=200, end=120, fill=col, width=int(k)); L([(13, 2), (17.5, 5.5), (13.5, 9)]); nokta(12, 12, 1.5)
    elif a == "aynala":
        L([(12, 3), (12, 21)], w=k * 0.9); L([(9, 7), (9, 17), (3, 17)], kapali=True); L([(15, 7), (15, 17), (21, 17)], kapali=True)
    elif a == "bol":
        L([(3, 12), (21, 12)]); L([(12, 5), (12, 19)]); nokta(12, 12, 2); nokta(3, 12, 1.5); nokta(21, 12, 1.5)
    elif a == "sil":        # çöp kutusu
        L([(4, 6), (20, 6)]); L([(9, 6), (9, 3.5), (15, 3.5), (15, 6)]); L([(6, 6), (7, 21), (17, 21), (18, 6)]); L([(10, 10), (10, 17)]); L([(14, 10), (14, 17)])
    elif a == "olcu":
        L([(3, 15), (15, 3), (21, 9), (9, 21)], kapali=True)
        for i in range(1, 5):
            L([(5 + i * 2.4, 15 - i * 2.4), (5 + i * 2.4 + 2, 15 - i * 2.4 + 2)])
    elif a == "kesit_duzlemi":
        L([(3, 15), (9, 6), (21, 6), (15, 15)], kapali=True); L([(12, 2), (12, 22)], w=k * 0.9); L([(9, 19), (12, 22), (15, 19)])
    elif a == "yakinlastir":
        E(4, 4, 15, 15); L([(13.5, 13.5), (20.5, 20.5)], w=k * 1.3); L([(9.5, 6.5), (9.5, 12.5)]); L([(6.5, 9.5), (12.5, 9.5)])
    elif a == "sigdir":
        L([(3, 8), (3, 3), (8, 3)]); L([(16, 3), (21, 3), (21, 8)]); L([(21, 16), (21, 21), (16, 21)]); L([(8, 21), (3, 21), (3, 16)]); R(8, 8, 16, 16)
    elif a == "ev":
        L([(3, 12), (12, 4), (21, 12)]); L([(6, 10), (6, 20), (18, 20), (18, 10)])
    elif a == "kilit":
        R(5, 11, 19, 21); d.arc([8 * u, 4 * u, 16 * u, 14 * u], start=180, end=360, fill=col, width=int(k)); L([(8, 9), (8, 11)]); L([(16, 9), (16, 11)])
    elif a == "onay":
        L([(5, 12.5), (10, 17.5), (19, 7)], w=k * 1.3)
    elif a == "yuk":        # yayılı yük okları
        L([(3, 19), (21, 19)]); L([(7, 4), (7, 15)]); L([(12, 4), (12, 15)]); L([(17, 4), (17, 15)]); L([(5, 13), (7, 15.5), (9, 13)]); L([(10, 13), (12, 15.5), (14, 13)]); L([(15, 13), (17, 15.5), (19, 13)])
    elif a == "yuk_nokta":
        L([(3, 19), (21, 19)]); L([(12, 3), (12, 16)], w=k * 1.3); L([(8.5, 12.5), (12, 16.5), (15.5, 12.5)])
    elif a == "mesnet":     # üçgen mesnet
        L([(12, 5), (19, 16), (5, 16)], kapali=True); L([(3, 20), (21, 20)]); L([(5, 20), (3, 22.5)]); L([(10, 20), (8, 22.5)]); L([(15, 20), (13, 22.5)]); L([(20, 20), (18, 22.5)])
    elif a == "mafsal":     # içi boş daire + çubuk
        L([(3, 12), (8, 12)]); L([(16, 12), (21, 12)]); E(8, 8, 16, 16)
    elif a == "rijit":
        L([(3, 12), (21, 12)]); L([(12, 5), (12, 19)], w=k * 1.4)
    elif a == "analiz":     # moment diyagramı
        L([(3, 19), (21, 19)]); d.arc([3 * u, 6 * u, 21 * u, 32 * u], start=200, end=340, fill=col, width=int(k)); L([(3, 19), (3, 6)]); L([(21, 19), (21, 6)])
    elif a == "coz":        # oynat üçgeni
        L([(6, 4), (20, 12), (6, 20)], dolgu=True)
    elif a == "oynat":
        L([(7, 5), (19, 12), (7, 19)], kapali=True)
    elif a == "durdur":
        R(6, 6, 18, 18)
    elif a == "deform":     # eğilmiş çubuk + gölge
        L([(3, 8), (21, 8)], w=k * 0.6); d.arc([3 * u, 2 * u, 21 * u, 26 * u], start=20, end=160, fill=col, width=int(k * 1.3))
    elif a == "diyagram":   # kesit tesiri diyagramı
        L([(3, 18), (21, 18)]); L([(3, 18), (3, 8), (21, 14), (21, 18)], kapali=True)
    elif a == "dc":         # D/C renk haritası
        R(3, 14, 7, 20, dolgu=True); R(8.5, 10, 12.5, 20, dolgu=True); R(14, 6, 18, 20, dolgu=True); L([(3, 22), (21, 22)])
    elif a == "sonuc":
        L([(3, 21), (21, 21)]); R(5, 12, 9, 21, dolgu=True); R(10.5, 6, 14.5, 21, dolgu=True); R(16, 15, 20, 21, dolgu=True)
    elif a == "tablo":
        R(3, 4, 21, 20); L([(3, 9.5), (21, 9.5)]); L([(3, 15), (21, 15)]); L([(9, 4), (9, 20)]); L([(15, 4), (15, 20)])
    elif a == "mesaj":
        L([(3, 4), (21, 4), (21, 16), (10, 16), (6, 20), (6, 16), (3, 16)], kapali=True)
    elif a == "bilgi":
        E(3, 3, 21, 21); L([(12, 11), (12, 17)]); nokta(12, 7.8, 1.3)
    elif a == "uyari":
        L([(12, 3.5), (21.5, 20), (2.5, 20)], kapali=True); L([(12, 9), (12, 14.5)]); nokta(12, 17.3, 1.2)
    elif a == "yakala":     # yakalama hedefi
        R(5, 5, 19, 19); L([(12, 1), (12, 7)]); L([(12, 17), (12, 23)]); L([(1, 12), (7, 12)]); L([(17, 12), (23, 12)])
    elif a == "orto":
        L([(4, 20), (4, 4)]); L([(4, 20), (20, 20)]); R(4, 14, 10, 20)
    elif a == "perspektif":
        L([(5, 20), (9, 6), (15, 6), (19, 20)], kapali=True); L([(3, 12), (21, 12)])
    elif a == "kati":       # ekstrüde kutu
        L([(12, 3), (21, 8), (12, 13), (3, 8)], kapali=True); L([(3, 8), (3, 17), (12, 22), (21, 17), (21, 8)]); L([(12, 13), (12, 22)])
    elif a == "cubuk":      # tek çizgi gösterimi
        L([(3, 18), (21, 6)]); nokta(3, 18, 1.8); nokta(21, 6, 1.8)
    elif a == "yonetmelik":  # kitap + onay
        L([(4, 4), (18, 4), (18, 20), (4, 20)], kapali=True); L([(4, 4), (4, 20)], w=k * 1.6); L([(8, 12), (10.5, 14.5), (15, 9.5)])
    elif a == "tasarim":    # cetvel + kalem
        L([(3, 17), (17, 3)], w=k * 1.2); L([(5, 21), (21, 5)], w=k * 1.2); L([(3, 17), (5, 21)]); L([(17, 3), (21, 5)])
    elif a == "kontrol":    # onay işaretli kalkan
        L([(12, 3), (20, 6), (20, 12), (12, 21), (4, 12), (4, 6)], kapali=True); L([(8.5, 12), (11, 14.5), (15.5, 9.5)])
    elif a == "bina3":
        L([(4, 9), (12, 4), (20, 9), (12, 14)], kapali=True); L([(4, 9), (4, 18), (12, 23), (20, 18), (20, 9)]); L([(12, 14), (12, 23)])
    elif a == "cerceve":
        L([(4, 20), (4, 6), (20, 6), (20, 20)]); L([(12, 6), (12, 20)]); L([(4, 13), (20, 13)])
    elif a == "plan":       # plan görünümü
        R(3, 3, 21, 21); L([(3, 12), (21, 12)]); L([(12, 3), (12, 21)]); nokta(7.5, 7.5, 1.4); nokta(16.5, 16.5, 1.4)
    elif a == "yukselti":
        R(3, 3, 21, 21); L([(3, 9), (21, 9)]); L([(3, 15), (21, 15)]); L([(8, 3), (8, 21)]); L([(16, 3), (16, 21)])
    elif a == "sorgu":      # soru işaretli etiket
        L([(3, 3), (12, 3), (21, 12), (12, 21), (3, 12)], kapali=True); nokta(7.5, 7.5, 1.3)
    elif a == "pencere":
        R(3, 4, 21, 20); L([(3, 9), (21, 9)])
    elif a == "sol_yapistir":
        R(3, 4, 21, 20); R(3, 4, 9, 20, dolgu=True)
    elif a == "tam":
        R(3, 5, 21, 19); L([(6, 8), (10, 8)]); L([(6, 11), (14, 11)])
    elif a == "yardim":
        E(3, 3, 21, 21); d.arc([8.5 * u, 6.5 * u, 15.5 * u, 13.5 * u], start=190, end=90, fill=col, width=int(k)); L([(12, 13.5), (12, 15.5)]); nokta(12, 18.3, 1.2)
    elif a == "anahtar":    # aç/kapa anahtar simgesi
        d.rounded_rectangle([3 * u, 8 * u, 21 * u, 16 * u], radius=4 * u, outline=col, width=int(k)); E(13, 9.5, 18, 14.5, dolgu=True)
    elif a == "dm":         # doğrudan değiştirme: tutamaçlı çubuk
        L([(5, 12), (19, 12)]); R(2.5, 9.5, 7.5, 14.5, dolgu=True); R(16.5, 9.5, 21.5, 14.5, dolgu=True)
    elif a == "nokta_ekle":
        L([(12, 4), (12, 20)]); L([(4, 12), (20, 12)])
    elif a == "kopyala_kat":  # kat kopyala
        L([(4, 6), (20, 6)]); L([(4, 12), (20, 12)]); L([(4, 18), (20, 18)], w=k * 1.4); L([(22, 10), (22, 16)]); L([(20, 12), (22, 14), (24, 12)])
    elif a == "tablo_disa":
        R(3, 4, 21, 20); L([(3, 9.5), (21, 9.5)]); L([(3, 15), (21, 15)]); L([(9, 4), (9, 20)]); L([(13, 12), (17, 18)]); L([(17, 12), (13, 18)])
    elif a == "nokta":
        nokta(12, 12, 3)
    elif a == "artı":
        L([(12, 5), (12, 19)]); L([(5, 12), (19, 12)])
    elif a == "deprem":     # sismograf dalgası
        L([(2, 12), (6, 12), (8, 7), (10.5, 18), (13, 4), (15.5, 16), (17.5, 10), (19, 12), (22, 12)])
    elif a == "zemin":      # zemin katmanları + temel
        L([(3, 9), (21, 9)], w=k * 1.4); L([(3, 14), (8, 13), (14, 15), (21, 14)]); L([(3, 19), (9, 18.5), (15, 20), (21, 19)])
        nokta(7, 11.5, 0.9); nokta(16, 11.5, 0.9); nokta(11, 16.8, 0.9); nokta(18, 17, 0.9)
    elif a == "kar":        # kar tanesi
        for i in range(3):
            ang = i * math.pi / 3
            dx, dy = 9 * math.cos(ang), 9 * math.sin(ang)
            L([(12 - dx, 12 - dy), (12 + dx, 12 + dy)])
        for i in range(6):
            ang = i * math.pi / 3
            cx_, cy_ = 12 + 6 * math.cos(ang), 12 + 6 * math.sin(ang)
            for s_ in (-1, 1):
                b_ = ang + s_ * 0.9
                L([(cx_, cy_), (cx_ + 2.6 * math.cos(b_), cy_ + 2.6 * math.sin(b_))], w=k * 0.9)
    elif a == "ruzgar":     # rüzgâr çizgileri
        L([(3, 8), (15, 8)]); d.arc([13 * u, 3 * u, 19 * u, 9 * u], start=180, end=90, fill=col, width=int(k))
        L([(3, 13), (19, 13)]); d.arc([17 * u, 8 * u, 23 * u, 14 * u], start=180, end=90, fill=col, width=int(k))
        L([(3, 18), (12, 18)]); d.arc([10 * u, 15 * u, 16 * u, 21 * u], start=270, end=180, fill=col, width=int(k))
    elif a == "konum":      # harita iğnesi
        d.arc([6 * u, 3 * u, 18 * u, 15 * u], start=145, end=35, fill=col, width=int(k))
        L([(7.1, 12.6), (12, 21), (16.9, 12.6)]); E(9.8, 6.8, 14.2, 11.2)
    elif a == "sablon":     # şablon: üst üste iki sayfa + yıldız noktası
        R(7, 3, 20, 17); L([(4, 7), (4, 21), (17, 21)]); L([(10, 8), (17, 8)]); L([(10, 11.5), (17, 11.5)]); L([(10, 15), (14, 15)])
    elif a == "yapistir":   # pano
        R(5, 5, 19, 21); R(9, 3, 15, 7, dolgu=True); L([(8.5, 12), (15.5, 12)]); L([(8.5, 16), (13.5, 16)])
    elif a == "takvim":
        R(3.5, 5, 20.5, 20.5); L([(3.5, 10), (20.5, 10)]); L([(8, 3), (8, 7)]); L([(16, 3), (16, 7)]); nokta(8, 14, 1.1); nokta(12, 14, 1.1); nokta(16, 14, 1.1); nokta(8, 17.5, 1.1)
    elif a == "kisi":
        E(8, 3.5, 16, 11.5); d.arc([4 * u, 13 * u, 20 * u, 29 * u], start=180, end=360, fill=col, width=int(k))
    elif a == "bina":       # cephe: katlı bina
        R(5, 3, 19, 21); L([(5, 8), (19, 8)]); L([(5, 12.5), (19, 12.5)]); L([(5, 17), (19, 17)]); L([(12, 3), (12, 21)])
    elif a == "birlesim":   # Σ
        L([(18, 4), (6, 4), (12.5, 12), (6, 20), (18, 20)])
    elif a == "spektrum":   # spektrum eğrisi
        L([(3, 21), (21, 21)]); L([(3, 21), (3, 3)]); L([(3, 15), (6, 7), (10, 7)]); d.arc([4 * u, 7 * u, 36 * u, 39 * u], start=180, end=242, fill=col, width=int(k))
    elif a == "sifirla":    # varsayılana dön
        d.arc([4 * u, 4 * u, 20 * u, 20 * u], start=120, end=400, fill=col, width=int(k)); L([(4.2, 6.5), (6.2, 10.6), (10.4, 9)])
    elif a == "ice_aktar_belge":
        L([(5, 2.5), (14, 2.5), (19, 7.5), (19, 21.5), (5, 21.5)], kapali=True); L([(14, 2.5), (14, 7.5), (19, 7.5)]); L([(12, 10), (12, 18)]); L([(9, 15), (12, 18), (15, 15)])
    else:
        E(5, 5, 19, 19)
    im = im.resize((max(1, int(round(boyut * s))), max(1, int(round(boyut * s)))), Image.LANCZOS)
    _SIMGE_ONBELLEK[key] = im
    return im


def logo_simge():
    im = Image.open(LOGO_SIMGE).convert("RGBA")
    return im.crop(im.getbbox())


def logo_yazi():
    im = Image.open(LOGO_YAZI).convert("RGBA")
    return im.crop(im.getbbox())
