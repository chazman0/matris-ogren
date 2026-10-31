#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atölye · Modern — çizim altyapısı: mantıksal-piksel tuval (1× / 2×), kenar yumuşatmalı yuvarlak biçimler,
Inter değişken yazı tipi, modern bileşenler (düğme, dolgulu giriş, segmentli denetim, anahtar, çip, kısayol rozeti,
kaydırıcı, adımlayıcı, odak halkası) ve elle çizilmiş tek renkli çizgi simgeler (24 birimlik ızgara, 1,5 px kalem).

Renk/yarıçap/aralık/yazı değerleri YALNIZ belirtec.py'den gelir.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from belirtec import C, R, Y, GOLGE, hex2rgb, rgba, karisim, ustundeki_metin

KIMLIK = "/home/user/matris-ogren/op4/kimlik"
FONT_INTER = os.path.join(KIMLIK, "fontlar", "inter-Inter[opsz,wght].ttf")
LOGO_SIMGE = os.path.join(KIMLIK, "opus-fortis-simge-koyu.png")


# ----------------------------------------------------------------------------
# Yazı tipleri
# ----------------------------------------------------------------------------
_FONTLAR = {}


def yazi_tipi(boyut_px, agirlik=400, olcek=1):
    """Inter değişken; opsz mantıksal boyuttan (14–32'ye kırpılır), piksel boyutu ölçekle çarpılır."""
    key = (boyut_px, agirlik, olcek)
    f = _FONTLAR.get(key)
    if f is None:
        f = ImageFont.truetype(FONT_INTER, max(1, int(round(boyut_px * olcek))))
        f.set_variation_by_axes([min(32, max(14, boyut_px)), agirlik])
        _FONTLAR[key] = f
    return f


def taban(y, h, boyut):
    """h yüksekliğindeki kutunun ortasına büyük harf yüksekliğine göre taban çizgisi (Inter cap ≈ 0,727 em)."""
    return y + h / 2 + 0.36 * boyut


# ----------------------------------------------------------------------------
# Kenar yumuşatmalı maske önbelleği (yuvarlak dikdörtgen / elips), 4× örnekleme + kutu süzgeci
# ----------------------------------------------------------------------------
_MASKE = {}


def _maske(W, H, r, tur="dd"):
    key = (W, H, round(r, 2), tur)
    m = _MASKE.get(key)
    if m is None:
        SS = 4
        big = Image.new("L", (W * SS, H * SS), 0)
        d = ImageDraw.Draw(big)
        if tur == "elips":
            d.ellipse([0, 0, W * SS - 1, H * SS - 1], fill=255)
        else:
            d.rounded_rectangle([0, 0, W * SS - 1, H * SS - 1], radius=max(0, r * SS), fill=255)
        m = big.resize((W, H), Image.BOX)
        _MASKE[key] = m
    return m


class Tuval:
    def __init__(self, w, h, s=1, zemin=None):
        self.s = s
        self.w, self.h = w, h
        self.img = Image.new("RGB", (int(round(w * s)), int(round(h * s))), hex2rgb(zemin or C["zemin"]))
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def p(self, v):
        return int(round(v * self.s))

    def _yenile(self):
        self.d = ImageDraw.Draw(self.img, "RGBA")

    # --- maske ile boyama ---------------------------------------------------------
    def _boya(self, X0, Y0, maske, renk):
        rgb = hex2rgb(renk)
        a = renk[3] if (isinstance(renk, tuple) and len(renk) == 4) else 255
        if a < 255:
            maske = maske.point(lambda v: v * a // 255)
        self.img.paste(Image.new("RGB", maske.size, rgb), (X0, Y0), maske)

    # --- temel biçimler -------------------------------------------------------
    def dikdortgen(self, x, y, w, h, dolgu=None, kenar=None, kalinlik=1, r=0):
        X0, Y0 = self.p(x), self.p(y)
        W, H = self.p(x + w) - X0, self.p(y + h) - Y0
        if W <= 0 or H <= 0:
            return
        if r <= 0:
            if kenar is not None:
                self.d.rectangle([X0, Y0, X0 + W - 1, Y0 + H - 1], fill=kenar)
                k = max(1, self.p(kalinlik))
                if dolgu is not None and W > 2 * k and H > 2 * k:
                    self.d.rectangle([X0 + k, Y0 + k, X0 + W - 1 - k, Y0 + H - 1 - k], fill=dolgu)
            elif dolgu is not None:
                self.d.rectangle([X0, Y0, X0 + W - 1, Y0 + H - 1], fill=dolgu)
            return
        rp = min(r * self.s, W / 2, H / 2)
        if kenar is not None and dolgu is None:
            self.cerceve(x, y, w, h, kenar, kalinlik, r)
        elif kenar is not None:
            k = max(1, self.p(kalinlik))
            self._boya(X0, Y0, _maske(W, H, rp), kenar)
            if W > 2 * k and H > 2 * k:
                self._boya(X0 + k, Y0 + k, _maske(W - 2 * k, H - 2 * k, max(0, rp - k)), dolgu)
        elif dolgu is not None:
            self._boya(X0, Y0, _maske(W, H, rp), dolgu)

    def cerceve(self, x, y, w, h, renk, kalinlik=1, r=0):
        """Yalnız kenar (içi boş)."""
        if r <= 0:
            self.yatay(x, x + w, y, renk, kalinlik); self.yatay(x, x + w, y + h - kalinlik, renk, kalinlik)
            self.dikey(x, y, y + h, renk, kalinlik); self.dikey(x + w - kalinlik, y, y + h, renk, kalinlik)
            return
        X0, Y0 = self.p(x), self.p(y)
        W, H = self.p(x + w) - X0, self.p(y + h) - Y0
        k = max(1, self.p(kalinlik))
        rp = min(r * self.s, W / 2, H / 2)
        dis = _maske(W, H, rp)
        ic = Image.new("L", (W, H), 0)
        ic.paste(_maske(W - 2 * k, H - 2 * k, max(0, rp - k)), (k, k))
        from PIL import ImageChops
        self._boya(X0, Y0, ImageChops.subtract(dis, ic), renk)

    def odak_halkasi(self, x, y, w, h, r=6, kalinlik=3, alfa=0.28):
        """Odak halkası: alanın dışında 3 px, vurgu %28."""
        self.cerceve(x - kalinlik, y - kalinlik, w + 2 * kalinlik, h + 2 * kalinlik, rgba(C["odak"], alfa), kalinlik, r + kalinlik)

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
        X0, Y0 = self.p(cx - r), self.p(cy - r)
        D = max(1, self.p(cx + r) - X0)
        if kenar is not None:
            self._boya(X0, Y0, _maske(D, D, 0, "elips"), kenar)
            k = max(1, self.p(kalinlik))
            if D > 2 * k:
                self._boya(X0 + k, Y0 + k, _maske(D - 2 * k, D - 2 * k, 0, "elips"), dolgu if dolgu is not None else C["yuzey"])
        elif dolgu is not None:
            self._boya(X0, Y0, _maske(D, D, 0, "elips"), dolgu)

    def gradyan(self, x, y, w, h, ust, alt, yatay_mi=False):
        ust, alt = hex2rgb(ust), hex2rgb(alt)
        N = max(1, self.p(w if yatay_mi else h))
        band = Image.new("RGB", (N, 1) if yatay_mi else (1, N))
        px = band.load()
        for i in range(N):
            t = i / max(1, N - 1)
            c = tuple(int(round(ust[k] + (alt[k] - ust[k]) * t)) for k in range(3))
            if yatay_mi:
                px[i, 0] = c
            else:
                px[0, i] = c
        band = band.resize((max(1, self.p(w)), max(1, self.p(h))))
        self.img.paste(band, (self.p(x), self.p(y)))

    def golge(self, x, y, w, h, r=6, tur="acilir", alfa=None, dy=None, yaricap=None):
        """Yumuşak düşen gölge (iki katman: geniş ortam + dar yakın)."""
        yr, dyy, al = GOLGE[tur]
        yaricap = yr if yaricap is None else yaricap
        dy = dyy if dy is None else dy
        alfa = al if alfa is None else alfa
        for carpan, a_carpan, dy_carpan in ((1.0, 1.0, 1.0), (0.3, 0.6, 0.3)):
            yc = max(1, yaricap * carpan)
            pad = yc * 3 + abs(dy)
            W, H = self.p(w + 2 * pad), self.p(h + 2 * pad)
            im = Image.new("L", (W, H), 0)
            dd = ImageDraw.Draw(im)
            dd.rounded_rectangle([self.p(pad), self.p(pad + dy * dy_carpan), self.p(pad + w), self.p(pad + h + dy * dy_carpan)],
                                 radius=self.p(r), fill=int(255 * alfa * a_carpan))
            im = im.filter(ImageFilter.GaussianBlur(self.p(yc)))
            self.img.paste(Image.new("RGB", (W, H), hex2rgb(C["golge"])), (self.p(x - pad), self.p(y - pad)), im)

    def karart(self, x, y, w, h, alfa=0.38):
        self.d.rectangle([self.p(x), self.p(y), self.p(x + w) - 1, self.p(y + h) - 1], fill=rgba(C["karartma"], alfa))

    # --- yazı --------------------------------------------------------------------
    def yazi(self, x, y, metin, boyut=12, agirlik=400, renk=None, hiza="ls", tnum=False):
        f = yazi_tipi(boyut, agirlik, self.s)
        feats = ["tnum"] if tnum else None
        self.d.text((x * self.s, y * self.s), metin, font=f, fill=renk or C["metin"], anchor=hiza, features=feats)

    def yazi_gen(self, metin, boyut=12, agirlik=400, tnum=False):
        f = yazi_tipi(boyut, agirlik, self.s)
        feats = ["tnum"] if tnum else None
        return f.getlength(metin, features=feats) / self.s

    def yazi_orta(self, cx, y, metin, boyut=12, agirlik=400, renk=None, tnum=False):
        self.yazi(cx - self.yazi_gen(metin, boyut, agirlik, tnum) / 2, y, metin, boyut, agirlik, renk, tnum=tnum)

    def yazi_sag(self, xr, y, metin, boyut=12, agirlik=400, renk=None, tnum=False):
        self.yazi(xr - self.yazi_gen(metin, boyut, agirlik, tnum), y, metin, boyut, agirlik, renk, tnum=tnum)

    def yazi_kes(self, metin, max_w, boyut=12, agirlik=400):
        if self.yazi_gen(metin, boyut, agirlik) <= max_w:
            return metin
        while metin and self.yazi_gen(metin + "…", boyut, agirlik) > max_w:
            metin = metin[:-1]
        return metin.rstrip() + "…"

    def yazi_aralikli(self, x, y, metin, boyut=9, agirlik=600, renk=None, aralik=0.6, orta=False):
        """Harf aralıklı BÜYÜK HARF etiket (ÇİZ / SEÇ / KISAYOLLAR)."""
        gen = sum(self.yazi_gen(ch, boyut, agirlik) for ch in metin) + aralik * (len(metin) - 1)
        if orta:
            x -= gen / 2
        for ch in metin:
            self.yazi(x, y, ch, boyut, agirlik, renk)
            x += self.yazi_gen(ch, boyut, agirlik) + aralik
        return gen

    def yazi_dikey(self, x, y, metin, boyut=11, agirlik=500, renk=None):
        """Saat yönünde 90° döndürülmüş yazı (yukarıdan aşağı okunur); (x,y) sol-üst köşe."""
        f = yazi_tipi(boyut, agirlik, self.s)
        w = int(f.getlength(metin)) + 4
        h = int(boyut * self.s * 1.4)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((2, int(boyut * self.s * 1.05)), metin, font=f, fill=hex2rgb(renk or C["metin2"]) + (255,), anchor="ls")
        im = im.rotate(-90, expand=True)
        self.img.paste(im, (self.p(x), self.p(y)), im)

    # --- simge / resim ---------------------------------------------------------
    def simge(self, ad, cx, cy, boyut=16, renk=None, kalinlik=1.5):
        im = simge_ciz(ad, boyut, self.s, renk or C["simge"], kalinlik)
        self.img.paste(im, (self.p(cx - boyut / 2), self.p(cy - boyut / 2)), im)

    def resim(self, im, x, y, w=None, h=None):
        if w is not None:
            oran = im.width / im.height
            if h is None:
                h = w / oran
            im = im.resize((max(1, self.p(w)), max(1, self.p(h))), Image.LANCZOS)
        self.img.paste(im, (self.p(x), self.p(y)), im if im.mode == "RGBA" else None)

    def yapistir(self, im, x, y):
        self.img.paste(im, (self.p(x), self.p(y)), im if im.mode == "RGBA" else None)

    # =========================================================================
    # BİLEŞENLER
    # =========================================================================
    def sevron(self, cx, cy, yon="asagi", boyut=10, renk=None):
        self.simge({"asagi": "sevron_asagi", "sag": "sevron_sag", "ust": "sevron_ust", "sol": "sevron_sol"}[yon], cx, cy, boyut,
                   renk or C["metin3"], 1.5)

    def onay_kutusu(self, x, y, isaretli, boyut=14):
        if isaretli:
            self.dikdortgen(x, y, boyut, boyut, dolgu=C["vurgu"], r=R["kucuk"])
            self.simge("onay", x + boyut / 2, y + boyut / 2, boyut - 2, ustundeki_metin(C["vurgu"]), 1.9)
        else:
            self.dikdortgen(x, y, boyut, boyut, dolgu=C["yuzey"], kenar=C["kenar"], r=R["kucuk"])

    def radyo(self, cx, cy, secili, r=7):
        if secili:
            self.daire(cx, cy, r, dolgu=C["vurgu"])
            self.daire(cx, cy, r - 4.5, dolgu=C["yuzey"])
        else:
            self.daire(cx, cy, r, dolgu=C["yuzey"], kenar=C["kenar"], kalinlik=1)

    def anahtar(self, x, y, acik, w=28, h=16):
        """Aç/kapa anahtarı (hap iz + beyaz düğme)."""
        self.dikdortgen(x, y, w, h, dolgu=C["vurgu"] if acik else "#C3C9D0", r=h / 2)
        kx = x + w - h / 2 if acik else x + h / 2
        self.daire(kx, y + h / 2 + 0.5, h / 2 - 2, dolgu=rgba(C["golge"], 0.18))
        self.daire(kx, y + h / 2, h / 2 - 2, dolgu=C["yuzey"])

    def kisayol(self, x, y, metin, boyut=10, h=18):
        """Klavye tuşu rozeti (alt kenarı koyu); genişliğini döndürür."""
        w = self.yazi_gen(metin, boyut, 500) + 10
        self.dikdortgen(x, y, w, h, dolgu=C["kenar"], r=R["kucuk"])
        self.dikdortgen(x, y, w, h - 1, dolgu=C["yuzey"], kenar=C["cizgi"], r=R["kucuk"])
        self.yazi(x + 5, taban(y, h - 1, boyut), metin, boyut, 500, C["metin2"])
        return w

    def kisayol_dizisi(self, x, y, tuslar, boyut=10, h=18, sag=False):
        """'Ctrl+Q' → [Ctrl][Q]; genişlik döndürür."""
        parcalar = tuslar.split("+") if tuslar not in ("+",) else ["+"]
        gen = sum(self.yazi_gen(p, boyut, 500) + 10 for p in parcalar) + 3 * (len(parcalar) - 1)
        if sag:
            x -= gen
        for p in parcalar:
            x += self.kisayol(x, y, p, boyut, h) + 3
        return gen

    def dugme(self, x, y, w, h, metin, tur="ikincil", boyut=12, simge=None, devre_disi=False):
        if tur == "birincil":
            self.dikdortgen(x, y + 1, w, h, dolgu=rgba(C["golge"], 0.10), r=R["orta"])
            self.dikdortgen(x, y, w, h, dolgu=C["vurgu"], r=R["orta"])
            renk, ag = ustundeki_metin(C["vurgu"]), 600
        elif tur == "hayalet":
            renk, ag = C["vurgu_metin"], 500
        elif tur == "notr_hayalet":
            renk, ag = C["metin2"], 500
        else:
            self.dikdortgen(x, y + 1, w, h, dolgu=rgba(C["golge"], 0.06), r=R["orta"])
            self.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["kenar"], r=R["orta"])
            renk, ag = C["metin"], 500
        if devre_disi:
            renk = C["metin4"]
        tw = self.yazi_gen(metin, boyut, ag) + (22 if simge else 0)
        tx = x + w / 2 - tw / 2
        if simge:
            self.simge(simge, tx + 7, y + h / 2, 14, renk, 1.5)
            tx += 22
        self.yazi(tx, taban(y, h, boyut), metin, boyut, ag, renk)

    def giris(self, x, y, w, h, metin, boyut=12, odak=False, imlec=False, renk=None, hiza="sol", simge=None, ek=None,
              salt=False):
        """Dolgulu giriş alanı (kenarsız görünüm, 1 px iç ince kenar); odakta beyaz + vurgu kenar + odak halkası."""
        if odak:
            self.odak_halkasi(x, y, w, h, R["orta"])
            self.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["odak"], r=R["orta"])
        elif salt:
            self.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["cizgi2"], r=R["orta"])
        else:
            self.dikdortgen(x, y, w, h, dolgu=C["alan"], kenar=C["alan_kenar"], r=R["orta"])
        tx = x + 8
        if simge:
            self.simge(simge, x + 8 + 6, y + h / 2, 13, C["metin3"], 1.4)
            tx += 18
        sag_bosluk = 8
        if ek:
            ew = self.yazi_gen(ek, boyut - 1, 400)
            self.yazi(x + w - 8 - ew, taban(y, h, boyut - 1), ek, boyut - 1, 400, C["metin3"])
            sag_bosluk += ew + 6
        sayisal = not any(ch.isalpha() for ch in metin)
        if hiza == "sag":
            self.yazi_sag(x + w - sag_bosluk, taban(y, h, boyut), metin, boyut, 400, renk or C["metin"], tnum=sayisal)
        else:
            m = self.yazi_kes(metin, w - (tx - x) - sag_bosluk, boyut, 400)
            self.yazi(tx, taban(y, h, boyut), m, boyut, 400, renk or C["metin"], tnum=sayisal)
            if imlec:
                ix = tx + self.yazi_gen(m, boyut, 400, sayisal) + 2
                self.dikey(ix, y + 4, y + h - 4, C["odak"], 1)

    def acilir(self, x, y, w, h, metin, boyut=12, odak=False, renk=None, simge=None, salt=False, agirlik=400):
        if odak:
            self.odak_halkasi(x, y, w, h, R["orta"])
            self.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["odak"], r=R["orta"])
        elif salt:
            self.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["kenar"], r=R["orta"])
        else:
            self.dikdortgen(x, y, w, h, dolgu=C["alan"], kenar=C["alan_kenar"], r=R["orta"])
        tx = x + 8
        if simge:
            self.simge(simge, x + 14, y + h / 2, 13, C["metin2"], 1.4)
            tx += 18
        self.yazi(tx, taban(y, h, boyut), self.yazi_kes(metin, w - (tx - x) - 24, boyut, agirlik), boyut, agirlik, renk or C["metin"],
                  tnum=not any(ch.isalpha() for ch in metin))
        self.sevron(x + w - 12, y + h / 2 + 0.5, "asagi", 10, C["metin2"])

    def segmentli(self, x, y, secenekler, secili, h=24, boyut=11, stil="notr", w=None, ic=10, devre_disi=False):
        """Segmentli denetim: gömme iz (zemin2) + seçili hap. stil='notr' → beyaz kabarık hap; 'vurgu' → vurgu dolgulu.
        w verilirse parçalar eşit bölünür. Toplam genişliği döndürür."""
        n = len(secenekler)
        if w is None:
            gen = [self.yazi_gen(s, boyut, 600) + 2 * ic for s in secenekler]
            w = sum(gen) + 4
        else:
            gen = [(w - 4) / n] * n
        self.dikdortgen(x, y, w, h, dolgu=C["zemin2"], r=R["orta"])
        cx = x + 2
        for i, (s, g) in enumerate(zip(secenekler, gen)):
            if i == secili:
                if stil == "vurgu" and not devre_disi:
                    self.dikdortgen(cx, y + 2, g, h - 4, dolgu=C["vurgu"], r=R["kucuk"])
                    renk = ustundeki_metin(C["vurgu"])
                else:
                    self.dikdortgen(cx, y + 3, g, h - 4, dolgu=rgba(C["golge"], 0.10), r=R["kucuk"])
                    self.dikdortgen(cx, y + 2, g, h - 4, dolgu=C["yuzey"], r=R["kucuk"])
                    renk = C["metin"] if not devre_disi else C["metin3"]
                self.yazi_orta(cx + g / 2, taban(y, h, boyut), s, boyut, 600, renk)
            else:
                if i > 0 and i - 1 != secili:
                    self.dikey(cx, y + 6, y + h - 6, C["kenar"])
                self.yazi_orta(cx + g / 2, taban(y, h, boyut), s, boyut, 500, C["metin2"] if not devre_disi else C["metin3"])
            cx += g
        return w

    def cip(self, x, y, metin, h=20, stil="kapali", boyut=10, nokta=False, simge=None, agirlik=600):
        """Durum çipi. stil: 'acik' (vurgu tonu), 'kapali' (çerçeve), 'secim', 'notr' (zemin2). Genişlik döndürür."""
        w = self.yazi_gen(metin, boyut, agirlik) + 16 + (10 if nokta else 0) + (16 if simge else 0)
        if stil == "acik":
            self.dikdortgen(x, y, w, h, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=R["orta"])
            renk = C["vurgu_metin"]
        elif stil == "secim":
            self.dikdortgen(x, y, w, h, dolgu=C["secim_ton"], kenar=C["secim_ton2"], r=R["orta"])
            renk = C["metin"]
        elif stil == "notr":
            self.dikdortgen(x, y, w, h, dolgu=C["zemin2"], r=R["orta"])
            renk = C["metin2"]
        else:
            self.dikdortgen(x, y, w, h, dolgu=None, kenar=C["cizgi"], r=R["orta"])
            renk = C["metin3"]
        tx = x + 8
        if nokta:
            self.daire(tx + 3, y + h / 2, 3, dolgu=C["vurgu"] if stil == "acik" else C["metin4"])
            tx += 10
        if simge:
            self.simge(simge, tx + 6, y + h / 2, 12, renk, 1.4)
            tx += 16
        self.yazi(tx, taban(y, h, boyut), metin, boyut, agirlik, renk)
        return w

    def rozet(self, x, y, metin, dolgu=None, renk=None, h=16, boyut=9, sag=False):
        """Hap sayaç rozeti; genişlik döndürür."""
        dolgu = dolgu or C["secim"]
        w = max(h, self.yazi_gen(metin, boyut, 600, True) + 12)
        if sag:
            x -= w
        self.dikdortgen(x, y, w, h, dolgu=dolgu, r=h / 2)
        self.yazi_orta(x + w / 2, taban(y, h, boyut), metin, boyut, 600, renk or ustundeki_metin(dolgu), tnum=True)
        return w

    def kaydirici(self, x, y, w, oran, h=20, etiketler=None):
        """Kaydırıcı: 4 px iz, vurgu dolu kısım, beyaz düğme."""
        cy = y + h / 2
        self.dikdortgen(x, cy - 2, w, 4, dolgu=C["zemin2"], r=2)
        self.dikdortgen(x, cy - 2, max(4, w * oran), 4, dolgu=C["vurgu"], r=2)
        kx = x + w * oran
        self.daire(kx, cy + 1, 8, dolgu=rgba(C["golge"], 0.14))
        self.daire(kx, cy, 8, dolgu=C["yuzey"], kenar=C["kenar"], kalinlik=1)
        self.daire(kx, cy, 3, dolgu=C["vurgu"])

    def adimlayici(self, x, y, w, h, metin, boyut=12, birim=None):
        """Sayı adımlayıcı: dolgulu alan + sağda − / + düğmeleri."""
        self.dikdortgen(x, y, w, h, dolgu=C["alan"], kenar=C["alan_kenar"], r=R["orta"])
        bw = h
        self.yazi(x + 8, taban(y, h, boyut), metin, boyut, 500, C["metin"], tnum=True)
        if birim:
            self.yazi(x + 8 + self.yazi_gen(metin, boyut, 500, True) + 4, taban(y, h, boyut), birim, boyut, 400, C["metin3"])
        self.dikey(x + w - 2 * bw, y + 5, y + h - 5, C["alan_kenar"])
        self.dikey(x + w - bw, y + 5, y + h - 5, C["alan_kenar"])
        self.simge("eksi", x + w - 1.5 * bw, y + h / 2, 12, C["metin2"], 1.6)
        self.simge("artı", x + w - 0.5 * bw, y + h / 2, 12, C["metin2"], 1.6)

    def kaydirma(self, x, y, h, ty, th):
        """İnce kaydırma çubuğu (iz görünmez, tutamaç 4 px hap)."""
        self.dikdortgen(x, ty, 4, th, dolgu=rgba(C["metin"], 0.22), r=2)

    def renk_ornegi(self, x, y, renk, boyut=20, secili=False):
        if secili:
            self.cerceve(x - 3, y - 3, boyut + 6, boyut + 6, C["vurgu"], 2, R["orta"] + 2)
        self.dikdortgen(x, y, boyut, boyut, dolgu=renk, kenar=rgba(C["golge"], 0.16), r=R["kucuk"])


# ----------------------------------------------------------------------------
# Simge kütüphanesi: 4× örneklemeli küçük tuvale çizgi, sonra LANCZOS küçültme (Atölye'den, genişletildi)
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
        d.polygon([(p[0] * u, p[1] * u) for p in pts], fill=(255, 255, 255, 255), outline=col, width=int(k))
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
    # ---- Atölye · Modern ile eklenen simgeler ----
    elif a == "eksi":
        L([(5, 12), (19, 12)])
    elif a == "disli":       # dişli (Ayarlar): 8 diş
        P = []
        for i in range(32):
            ang = i * math.pi / 16
            rr = 10.0 if (i % 4) in (0, 1) else 7.6
            P.append((12 + rr * math.cos(ang - math.pi / 32 * 3), 12 + rr * math.sin(ang - math.pi / 32 * 3)))
        L(P, kapali=True); E(8.6, 8.6, 15.4, 15.4)
    elif a == "dil":         # küre
        E(3, 3, 21, 21); E(8, 3, 16, 21); L([(3, 12), (21, 12)]); L([(5, 7.5), (19, 7.5)]); L([(5, 16.5), (19, 16.5)])
    elif a == "ekran":       # monitör
        d.rounded_rectangle([3 * u, 4 * u, 21 * u, 16.5 * u], radius=2 * u, outline=col, width=int(round(k)))
        L([(12, 16.5), (12, 20)]); L([(8, 20.5), (16, 20.5)])
    elif a == "klavye":
        d.rounded_rectangle([2 * u, 6 * u, 22 * u, 18 * u], radius=2 * u, outline=col, width=int(round(k)))
        for xx in (6, 9.5, 13, 16.5):
            nokta(xx, 10, 0.9)
        for xx in (6, 18):
            nokta(xx, 14, 0.9)
        L([(8.5, 14), (15.5, 14)])
    elif a == "klasor":
        L([(3, 6.5), (3, 19), (21, 19), (21, 8.5), (11.5, 8.5), (9.5, 6), (3, 6)], kapali=False); L([(3, 6), (9.5, 6)])
    elif a == "islemci":
        R(6.5, 6.5, 17.5, 17.5); R(9.5, 9.5, 14.5, 14.5)
        for t_ in (9.5, 12, 14.5):
            L([(t_, 3), (t_, 6.5)]); L([(t_, 17.5), (t_, 21)]); L([(3, t_), (6.5, t_)]); L([(17.5, t_), (21, t_)])
    elif a == "bellek":
        R(2.5, 7, 21.5, 15.5); R(5.5, 9.5, 8.5, 13); R(10.5, 9.5, 13.5, 13); R(15.5, 9.5, 18.5, 13)
        for xx in (5, 8, 11, 14, 17, 20):
            L([(xx, 15.5), (xx, 18.5)])
    elif a == "saat":
        E(3, 3, 21, 21); L([(12, 7), (12, 12), (15.5, 14)])
    elif a == "sifirla":     # ↺ varsayılana dön
        d.arc([4 * u, 4 * u, 20 * u, 20 * u], start=-60, end=200, fill=col, width=int(round(k)))
        L([(3.2, 6.5), (4.6, 11.4), (9.4, 9.8)])
    elif a == "kurtarma":    # can simidi
        E(3, 3, 21, 21); E(8, 8, 16, 16)
        for ang in (45, 135, 225, 315):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            L([(12 + 4 * ca, 12 + 4 * sa), (12 + 9 * ca, 12 + 9 * sa)])
    elif a == "gunes":
        E(8, 8, 16, 16)
        for i in range(8):
            ang = i * math.pi / 4
            L([(12 + 6.5 * math.cos(ang), 12 + 6.5 * math.sin(ang)), (12 + 9.5 * math.cos(ang), 12 + 9.5 * math.sin(ang))])
    elif a == "ay":
        d.arc([4 * u, 4 * u, 20 * u, 20 * u], start=100, end=350, fill=col, width=int(round(k)))
        d.arc([9 * u, 1.5 * u, 23 * u, 15.5 * u], start=95, end=215, fill=col, width=int(round(k)))
    elif a == "baslatici":   # iletişim kutusu başlatıcısı (köşe + çapraz ok)
        L([(10, 4), (4, 4), (4, 20), (20, 20), (20, 14)]); L([(11, 13), (20, 4)]); L([(14, 4), (20, 4), (20, 10)])
    elif a == "nokta3":
        nokta(6, 12, 1.6); nokta(12, 12, 1.6); nokta(18, 12, 1.6)
    elif a == "cizgi_kalinlik":
        L([(3, 6), (21, 6)], w=k * 0.6); L([(3, 12), (21, 12)], w=k * 1.1); L([(3, 18.5), (21, 18.5)], w=k * 1.9)
    elif a == "balon":       # aks balonu
        E(6, 2.5, 18, 14.5); L([(12, 14.5), (12, 21.5)]); L([(8.5, 21.5), (15.5, 21.5)])
    elif a == "komut":       # komut satırı / takma ad
        d.rounded_rectangle([2.5 * u, 4.5 * u, 21.5 * u, 19.5 * u], radius=2 * u, outline=col, width=int(round(k)))
        L([(6.5, 9), (9.5, 12), (6.5, 15)]); L([(11.5, 15), (16.5, 15)])
    elif a == "sayi":        # # işareti
        L([(9.5, 4), (7.5, 20)]); L([(16.5, 4), (14.5, 20)]); L([(4.5, 9), (20, 9)]); L([(4, 15), (19.5, 15)])
    elif a == "takvim":
        d.rounded_rectangle([3.5 * u, 5 * u, 20.5 * u, 20.5 * u], radius=2 * u, outline=col, width=int(round(k)))
        L([(3.5, 10), (20.5, 10)]); L([(8, 3), (8, 7)]); L([(16, 3), (16, 7)]); nokta(8.5, 14.5, 1.1); nokta(12, 14.5, 1.1); nokta(15.5, 14.5, 1.1)
    elif a == "ozellik":     # kaydırıcılar (Özellikler)
        L([(3, 7), (21, 7)]); L([(3, 12), (21, 12)]); L([(3, 17), (21, 17)])
        for xx, yy in ((15, 7), (8, 12), (13, 17)):
            d.ellipse([(xx - 2.4) * u, (yy - 2.4) * u, (xx + 2.4) * u, (yy + 2.4) * u], fill=(255, 255, 255, 255), outline=col, width=int(round(k)))
    elif a == "agac":        # hiyerarşi
        R(3, 3, 9, 8); L([(6, 8), (6, 18.5), (12, 18.5)]); L([(6, 12), (12, 12)]); R(12, 9.5, 21, 14.5); R(12, 16, 21, 21)
    elif a == "kalite":      # elmas
        L([(7, 4), (17, 4), (21, 9), (12, 20.5), (3, 9)], kapali=True); L([(3, 9), (21, 9)]); L([(9.5, 9), (12, 20.5), (14.5, 9)])
    elif a == "ag":          # sonlu eleman ağı
        R(3, 3, 21, 21); L([(3, 12), (21, 12)]); L([(12, 3), (12, 21)]); L([(3, 3), (21, 21)]); L([(12, 3), (21, 12)]); L([(3, 12), (12, 21)])
    elif a == "katlar_duzlem":
        L([(3, 9), (9, 4), (21, 4), (15, 9)], kapali=True); L([(3, 19), (9, 14), (21, 14), (15, 19)], kapali=True); L([(3, 9), (3, 19)], w=k * 0.7)
    elif a == "olcek":       # Aa
        L([(3, 19), (8, 5), (13, 19)]); L([(5, 14.5), (11, 14.5)]); E(14, 11, 21, 19.5); L([(21, 11), (21, 19.5)])
    elif a == "vurgu_renk":  # damla
        L([(12, 3), (17.5, 11), (18.6, 14.5), (17, 18.5), (12, 21), (7, 18.5), (5.4, 14.5), (6.5, 11)], kapali=True)
    elif a == "goruntu":     # resim çerçevesi
        R(3, 4, 21, 20); L([(3, 17), (9, 11), (13, 15), (16, 12), (21, 17)]); nokta(16, 8, 1.5)
    elif a == "baglanti":    # dış bağlantı / gözat
        L([(13, 4), (20, 4), (20, 11)]); L([(20, 4), (11, 13)]); L([(17, 14), (17, 20), (4, 20), (4, 7), (10, 7)])
    elif a == "geri_yukle":  # kurtarma geçmişi
        d.arc([4 * u, 4 * u, 20 * u, 20 * u], start=200, end=500, fill=col, width=int(round(k)))
        L([(3.2, 8), (4.4, 12.8), (8.8, 10.6)]); L([(12, 8), (12, 12.5), (15, 14.5)])
    elif a == "yildiz_bes":
        P = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = 9 if i % 2 == 0 else 4
            P.append((12 + rr * math.cos(ang), 12.6 + rr * math.sin(ang)))
        L(P, kapali=True)
    else:
        E(5, 5, 19, 19)
    im = im.resize((max(1, int(round(boyut * s))), max(1, int(round(boyut * s)))), Image.LANCZOS)
    _SIMGE_ONBELLEK[key] = im
    return im


def logo_simge():
    im = Image.open(LOGO_SIMGE).convert("RGBA")
    return im.crop(im.getbbox())
