# -*- coding: utf-8 -*-
"""sahne.py — parametrik çelik çerçevenin yazılımsal perspektif çizimi.

Depo Binası – Tokat OSB: aks A–D (x, 3 açıklık × 6 m) × 1–5 (y, 4 açıklık × 6 m),
katlar ±0.00 / +4.50 / +9.00 / +13.50. HE340A kolon, IPE400 kiriş, IPE200 aşık
(ikincil kiriş), L100x10 X-çapraz, betonarme döşeme. Ekstrüde kesitler: her
eleman bir prizma; yüzler tek ışık yönüyle gölgelenir, ressam sırasıyla çizilir.
"""
import math
import random
from PIL import Image, ImageDraw
from tuval import R, karistir, hexrgb, Yazi, DC_RENK, DC_ESIK, LANCZOS

# ---------------------------------------------------------------- vektör
def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def v_cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def v_len(a): return math.sqrt(v_dot(a, a))
def v_norm(a):
    l = v_len(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l else (0.0, 0.0, 0.0)


# ---------------------------------------------------------------- kesitler (m)
PROFIL = {
    'HE340A': ('I', 0.330, 0.300, 0.0165, 0.0095),
    'IPE400': ('I', 0.400, 0.180, 0.0135, 0.0086),
    'IPE200': ('I', 0.200, 0.100, 0.0085, 0.0056),
    'L100x10': ('L', 0.100, 0.100, 0.010, 0.010),
}


def kesit_konturu(ad):
    tur, h, b, tf, tw = PROFIL[ad]
    if tur == 'I':
        pts = [(-b / 2, h / 2), (b / 2, h / 2), (b / 2, h / 2 - tf), (tw / 2, h / 2 - tf),
               (tw / 2, -h / 2 + tf), (b / 2, -h / 2 + tf), (b / 2, -h / 2), (-b / 2, -h / 2),
               (-b / 2, -h / 2 + tf), (-tw / 2, -h / 2 + tf), (-tw / 2, h / 2 - tf), (-b / 2, h / 2 - tf)]
    else:
        a, t = h, tf
        pts = [(-a / 2, -a / 2), (a / 2, -a / 2), (a / 2, -a / 2 + t), (-a / 2 + t, -a / 2 + t),
               (-a / 2 + t, a / 2), (-a / 2, a / 2)]
    # saat yönünün tersi (CCW) olsun: dış normal = kenar × eksen
    alan = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if alan < 0:
        pts.reverse()
    return pts


# ---------------------------------------------------------------- renkler
RENK_TUR = {
    'kolon': hexrgb('#8E99A6'),
    'kiris': hexrgb('#AAB3BD'),
    'asik': hexrgb('#C2C8CF'),
    'capraz': hexrgb('#B39C7E'),
    'doseme': hexrgb('#DAD7D1'),
}
SECILI_DOLGU = hexrgb('#E9D3A8')
KENAR_KOYU = hexrgb('#2E3338')


def dc_rengi(dc):
    for esik, renk in zip(DC_ESIK, DC_RENK):
        if dc <= esik:
            return renk
    return DC_RENK[-1]


# ---------------------------------------------------------------- eleman
class Eleman:
    def __init__(self, tur, etiket, kat, p0, p1, profil, secili=False, hover=False, dc=0.5):
        self.tur, self.etiket, self.kat = tur, etiket, kat
        self.p0, self.p1, self.profil = p0, p1, profil
        self.secili, self.hover, self.dc = secili, hover, dc

    def cerceve(self):
        t = v_norm(v_sub(self.p1, self.p0))
        if abs(t[2]) > 0.99:                 # kolon: u = X, v = Y
            u, v = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
        else:                                # kiriş/çapraz: v = düşey (gövde dik)
            z = (0.0, 0.0, 1.0)
            v = v_norm(v_sub(z, v_mul(t, v_dot(z, t))))
            u = v_cross(v, t)
        return t, u, v

    def yuzler(self):
        t, u, v = self.cerceve()
        k = kesit_konturu(self.profil)
        if self.tur == 'capraz':   # L köşesi eksende dursun
            a = PROFIL[self.profil][1]
            k = [(x + a / 2, y + a / 2) for x, y in k]
        P0 = [v_add(self.p0, v_add(v_mul(u, x), v_mul(v, y))) for x, y in k]
        P1 = [v_add(self.p1, v_add(v_mul(u, x), v_mul(v, y))) for x, y in k]
        n = len(k)
        out = []
        for i in range(n):
            a, b = P0[i], P0[(i + 1) % n]
            c, d = P1[(i + 1) % n], P1[i]
            e = v_norm(v_sub(b, a))
            nrm = v_norm(v_cross(e, t))
            out.append(([a, b, c, d], nrm))
        out.append((P0, v_mul(t, -1)))
        out.append((P1, t))
        return out


class Doseme:
    def __init__(self, x0, y0, x1, y1, z, kat, kalinlik=0.14):
        self.x0, self.y0, self.x1, self.y1, self.z, self.kat, self.kal = x0, y0, x1, y1, z, kat, kalinlik
        self.tur = 'doseme'

    def yuzler(self):
        z0, z1 = self.z, self.z + self.kal
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        A, B, C, D = (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
        a, b, c, d = (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)
        return [([A, B, C, D], (0, 0, 1)), ([a, b, B, A], (0, -1, 0)), ([b, c, C, B], (1, 0, 0)),
                ([c, d, D, C], (0, 1, 0)), ([d, a, A, D], (-1, 0, 0))]


# ---------------------------------------------------------------- bina
class Bina:
    AKS_X = [0.0, 6.0, 12.0, 18.0]
    AKS_Y = [0.0, 6.0, 12.0, 18.0, 24.0]
    AKS_XE = ['A', 'B', 'C', 'D']
    AKS_YE = ['1', '2', '3', '4', '5']
    KOT = [0.0, 4.5, 9.0, 13.5]
    KAT_AD = ['Zemin', 'Kat 1', 'Kat 2', 'Kat 3']

    def __init__(self, secili_kirisler=True, hover=True, tohum=4):
        rnd = random.Random(tohum)
        self.elemanlar = []
        self.dosemeler = []
        hk, bk = PROFIL['HE340A'][1], PROFIL['HE340A'][2]
        hb = PROFIL['IPE400'][1]
        bb = PROFIL['IPE400'][2]
        X, Y, Z = self.AKS_X, self.AKS_Y, self.KOT
        # kolonlar (kat kat)
        n = 0
        for s in range(3):
            for i, x in enumerate(X):
                for j, y in enumerate(Y):
                    n += 1
                    e = Eleman('kolon', 'C%d-%02d' % (s + 1, n), s + 1, (x, y, Z[s]), (x, y, Z[s + 1]), 'HE340A',
                               dc=rnd.uniform(0.32, 0.82))
                    if hover and s == 1 and i == 2 and j == 0:
                        e.hover = True
                    self.elemanlar.append(e)
        # ana kirişler
        self.secili = []
        for s in range(1, 4):
            z = Z[s] - hb / 2
            n = 0
            for j, y in enumerate(Y):          # x yönü
                for i in range(len(X) - 1):
                    n += 1
                    et = 'K%d-%02d' % (s, n)
                    e = Eleman('kiris', et, s, (X[i] + bk / 2, y, z), (X[i + 1] - bk / 2, y, z), 'IPE400',
                               dc=rnd.uniform(0.45, 0.93))
                    if secili_kirisler and s == 2 and j in (0, 1):
                        e.secili = True
                        self.secili.append(e)
                    if s == 2 and j == 1 and i == 1:
                        e.dc = 1.04
                    if s == 2 and j == 1 and i == 2:
                        e.dc = 1.01
                    self.elemanlar.append(e)
            for i, x in enumerate(X):          # y yönü
                for j in range(len(Y) - 1):
                    n += 1
                    e = Eleman('kiris', 'K%d-%02d' % (s, n), s, (x, Y[j] + hk / 2, z), (x, Y[j + 1] - hk / 2, z), 'IPE400',
                               dc=rnd.uniform(0.40, 0.90))
                    self.elemanlar.append(e)
            # aşıklar / ikincil kirişler (x yönü, açıklık ortası)
            z2 = Z[s] - PROFIL['IPE200'][1] / 2
            n = 0
            for j in range(len(Y) - 1):
                for i in range(len(X) - 1):
                    n += 1
                    ym = (Y[j] + Y[j + 1]) / 2
                    self.elemanlar.append(Eleman('asik', 'A%d-%02d' % (s, n), s, (X[i] + bb / 2, ym, z2),
                                                 (X[i + 1] - bb / 2, ym, z2), 'IPE200', dc=rnd.uniform(0.35, 0.8)))
            # döşemeler (açıklık başına)
            for j in range(len(Y) - 1):
                for i in range(len(X) - 1):
                    self.dosemeler.append(Doseme(X[i] + 0.05, Y[j] + 0.05, X[i + 1] - 0.05, Y[j + 1] - 0.05, Z[s], s))
        # çaprazlar: A ve D aksları (1-2, 4-5 açıklıkları), 1 ve 5 aksları (B-C)
        def xcapraz(p_a, p_b, s, ad):
            d = v_norm(v_sub(p_b, p_a))
            a = v_add(p_a, v_mul(d, 0.55))
            b = v_sub(p_b, v_mul(d, 0.55))
            self.elemanlar.append(Eleman('capraz', ad + 'a', s, a, b, 'L100x10', dc=rnd.uniform(0.4, 0.88)))
        n = 0
        for s in range(3):
            z0, z1 = Z[s], Z[s + 1]
            for x in (X[0], X[-1]):
                off = -0.25 if x == X[0] else 0.25
                for (ya, yb) in ((Y[0], Y[1]), (Y[3], Y[4])):
                    n += 1
                    xcapraz((x + off, ya, z0), (x + off, yb, z1), s + 1, 'Ç%d-%02d' % (s + 1, n))
                    xcapraz((x + off, yb, z0), (x + off, ya, z1), s + 1, 'Ç%d-%02db' % (s + 1, n))
            for y in (Y[0], Y[-1]):
                off = -0.25 if y == Y[0] else 0.25
                n += 1
                xcapraz((X[1], y + off, z0), (X[2], y + off, z1), s + 1, 'Ç%d-%02d' % (s + 1, n))
                xcapraz((X[2], y + off, z0), (X[1], y + off, z1), s + 1, 'Ç%d-%02db' % (s + 1, n))


# ---------------------------------------------------------------- kamera
class Kamera:
    def __init__(self, hedef, az_deg, el_deg, mesafe):
        az, el = math.radians(az_deg), math.radians(el_deg)
        d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
        self.goz = v_add(hedef, v_mul(d, mesafe))
        self.f = v_norm(v_sub(hedef, self.goz))
        self.r = v_norm(v_cross(self.f, (0.0, 0.0, 1.0)))
        self.u = v_cross(self.r, self.f)
        self.k = 1.0
        self.cx = self.cy = 0.0

    def ham(self, p):
        d = v_sub(p, self.goz)
        z = v_dot(d, self.f)
        return (v_dot(d, self.r) / z, v_dot(d, self.u) / z, z)

    def proj(self, p):
        x, y, z = self.ham(p)
        return (self.cx + self.k * x, self.cy - self.k * y, z)

    def sigdir(self, noktalar, x0, y0, x1, y1):
        xs, ys = [], []
        for p in noktalar:
            x, y, _ = self.ham(p)
            xs.append(x); ys.append(y)
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        self.k = min((x1 - x0) / bw, (y1 - y0) / bh)
        self.cx = (x0 + x1) / 2 - self.k * (min(xs) + max(xs)) / 2
        self.cy = (y0 + y1) / 2 + self.k * (min(ys) + max(ys)) / 2

    def yon2d(self, v):
        return (v_dot(v, self.r), -v_dot(v, self.u))


# ---------------------------------------------------------------- çizim
class Sahne:
    def __init__(self, bina, mod='model', deform=False):
        self.bina = bina
        self.mod = mod            # 'model' | 'dc'
        self.deform = deform
        self.isik = v_norm((-0.45, -0.55, 0.70))

    def render(self, w, h, S, ss, az=-128, el=24, sig=(0.07, 0.11, 0.93, 0.86), arka=None):
        """w×h mantıksal; S ölçek; ss süper örnekleme. Döndürür: (RGB görsel, bilgi)."""
        k = S * ss
        W, H = int(w * k), int(h * k)
        im = Image.new('RGB', (W, H), (255, 255, 255))
        d = ImageDraw.Draw(im, 'RGBA')
        # arka plan: beyaz → açık gri gradyan
        c0, c1 = arka or ((255, 255, 255), hexrgb('#E7E8EA'))
        for yy in range(H):
            t = yy / max(1, H - 1)
            d.line([(0, yy), (W, yy)], fill=karistir(c0, c1, t ** 1.2))
        b = self.bina
        X, Y, Z = b.AKS_X, b.AKS_Y, b.KOT
        hedef = ((X[0] + X[-1]) / 2, (Y[0] + Y[-1]) / 2, Z[-1] * 0.42)
        kam = Kamera(hedef, az, el, 70.0)
        kutu = [(x, y, z) for x in (X[0] - 3.2, X[-1] + 2.0) for y in (Y[0] - 3.2, Y[-1] + 2.0) for z in (0.0, Z[-1] + 0.6)]
        kam.sigdir(kutu, W * sig[0], H * sig[1], W * sig[2], H * sig[3])
        P = kam.proj
        bilgi = {'proj': lambda p: tuple(c / k for c in P(p)[:2]), 'kam': kam, 'k': k}

        def ciz_cizgi(p, q, renk, lw):
            a, bq = P(p), P(q)
            d.line([(a[0], a[1]), (bq[0], bq[1])], fill=renk, width=max(1, int(round(lw * k))))

        # zemin gölgesi (yumuşak ortam hissi)
        golge = Image.new('L', (W, H), 0)
        gd = ImageDraw.Draw(golge)
        foot = [P((X[0] - 0.6, Y[0] - 0.6, 0))[:2], P((X[-1] + 0.6, Y[0] - 0.6, 0))[:2],
                P((X[-1] + 0.6, Y[-1] + 0.6, 0))[:2], P((X[0] - 0.6, Y[-1] + 0.6, 0))[:2]]
        gd.polygon(foot, fill=255)
        from PIL import ImageFilter
        golge = golge.filter(ImageFilter.GaussianBlur(10 * k)).point(lambda v: int(v * 0.09))
        im.paste((60, 56, 48), (0, 0), golge)

        # ince kâğıt ızgarası (1 m) ve ana akslar
        ince = (0, 0, 0, 14)
        for xx in range(int(X[0]) - 2, int(X[-1]) + 3):
            ciz_cizgi((xx, Y[0] - 2.5, 0), (xx, Y[-1] + 2.5, 0), ince, 0.5)
        for yy in range(int(Y[0]) - 2, int(Y[-1]) + 3):
            ciz_cizgi((X[0] - 2.5, yy, 0), (X[-1] + 2.5, yy, 0), ince, 0.5)
        aks_r = (120, 116, 108, 150)
        for x in X:
            ciz_cizgi((x, Y[0] - 2.6, 0), (x, Y[-1] + 2.0, 0), aks_r, 0.6)
        for y in Y:
            ciz_cizgi((X[0] - 2.6, y, 0), (X[-1] + 2.0, y, 0), aks_r, 0.6)
        # kat çizgileri (çevre, hafif)
        kat_r = (140, 136, 128, 110)
        for s in range(1, 4):
            z = Z[s]
            o = 0.9
            cev = [(X[0] - o, Y[0] - o, z), (X[-1] + o, Y[0] - o, z), (X[-1] + o, Y[-1] + o, z), (X[0] - o, Y[-1] + o, z)]
            for i in range(4):
                ciz_cizgi(cev[i], cev[(i + 1) % 4], kat_r, 0.5)

        # yüzleri topla
        yuzler = []
        goz = kam.goz
        for e in b.elemanlar:
            if self.mod == 'dc':
                taban = karistir(dc_rengi(e.dc), (255, 255, 255), 0.18)
            elif e.secili:
                taban = SECILI_DOLGU
            else:
                taban = RENK_TUR[e.tur]
            for pts, n in e.yuzler():
                c = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
                if v_dot(n, v_sub(goz, c)) <= 0:
                    continue
                sh = 0.58 + 0.42 * max(0.0, v_dot(n, self.isik))
                sh += 0.06 * max(0.0, n[2])
                renk = tuple(min(255, int(ch * sh)) for ch in taban)
                yuzler.append((v_dot(v_sub(c, goz), kam.f), pts, renk, e))
        for ds in b.dosemeler:
            taban = RENK_TUR['doseme']
            for pts, n in ds.yuzler():
                c = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
                if v_dot(n, v_sub(goz, c)) <= 0:
                    continue
                sh = 0.72 + 0.28 * max(0.0, v_dot(n, self.isik))
                renk = tuple(min(255, int(ch * sh)) for ch in taban)
                yuzler.append((v_dot(v_sub(c, goz), kam.f), pts, renk, ds))
        yuzler.sort(key=lambda f: -f[0])
        kenar_w = max(1, int(round(0.5 * k)))
        sec_w = max(1, int(round(1.4 * k)))
        for _, pts, renk, e in yuzler:
            poly = [P(p)[:2] for p in pts]
            if e.tur == 'doseme':
                d.polygon(poly, fill=renk + (62,))
                d.line(poly + [poly[0]], fill=(150, 146, 138, 120), width=kenar_w)
                continue
            d.polygon(poly, fill=renk)
            if e.secili and self.mod != 'dc':
                kenar = R['altin'] + (255,)
                d.line(poly + [poly[0]], fill=kenar, width=sec_w)
            elif e.hover and self.mod != 'dc':
                d.line(poly + [poly[0]], fill=R['kahve'] + (255,), width=max(1, int(round(1.0 * k))))
            else:
                kenar = karistir(renk, KENAR_KOYU, 0.5) + (150,)
                d.line(poly + [poly[0]], fill=kenar, width=kenar_w)

        # aks balonları (kat 0 düzleminde, uçlarda)
        fb = Yazi.al('inter', 10.5 * k, 500)
        rb = 8.5 * k
        for x, et in zip(X, b.AKS_XE):
            self._balon(d, P((x, Y[0] - 2.6, 0)), rb, et, fb)
        for y, et in zip(Y, b.AKS_YE):
            self._balon(d, P((X[0] - 2.6, y, 0)), rb, et, fb)
        # kot cetveli (A/1 köşesinin önünde)
        cx, cy = X[0] - 2.6, Y[-1] + 2.6
        ciz_cizgi((cx, cy, 0), (cx, cy, Z[-1]), (120, 116, 108, 200), 0.6)
        fk = Yazi.al('inter', 10 * k, 500)
        fk2 = Yazi.al('inter', 9.5 * k, 400)
        for s, z in enumerate(Z):
            ciz_cizgi((cx - 0.5, cy, z), (cx, cy, z), (120, 116, 108, 220), 0.6)
            sx, sy, _ = P((cx - 0.7, cy, z))
            lab = ('%+.2f' % z).replace('+0.00', '±0.00').replace('.', ',')
            d.text((sx, sy - 1 * k), lab, font=fk, fill=R['metin2'], anchor='rs')
            d.text((sx, sy + 10 * k), b.KAT_AD[s], font=fk2, fill=R['metin3'], anchor='rs')

        # seçim bilgileri
        if b.secili:
            e = b.secili[0]
            bilgi['tutamac'] = (bilgi['proj'](e.p0), bilgi['proj'](e.p1))
            orta = v_mul(v_add(e.p0, e.p1), 0.5)
            bilgi['tutamac_orta'] = bilgi['proj'](orta)
            cs = [v_mul(v_add(s.p0, s.p1), 0.5) for s in b.secili]
            c = tuple(sum(p[i] for p in cs) / len(cs) for i in range(3))
            bilgi['secim_merkez'] = bilgi['proj'](c)
            bilgi['secim_ust'] = bilgi['proj']((c[0], c[1], c[2] + 0.5))
            xs = [bilgi['proj'](v)[0] for s in b.secili for v in (s.p0, s.p1)]
            ys = [bilgi['proj'](v)[1] for s in b.secili for v in (s.p0, s.p1)]
            bilgi['secim_kutu'] = (min(xs), min(ys), max(xs), max(ys))
        for e in b.elemanlar:
            if e.hover:
                bilgi['hover'] = bilgi['proj'](v_mul(v_add(e.p0, e.p1), 0.5))
                bilgi['hover_e'] = e
        kot = bilgi['proj']
        bilgi['dc_maks'] = max(b.elemanlar, key=lambda e: e.dc)
        bilgi['dc_maks_p'] = kot(v_mul(v_add(bilgi['dc_maks'].p0, bilgi['dc_maks'].p1), 0.5))
        out = im.resize((int(w * S), int(h * S)), LANCZOS) if ss > 1 else im
        return out, bilgi

    @staticmethod
    def _balon(d, p, r, et, f):
        x, y = p[0], p[1]
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 235), outline=(110, 106, 98, 255), width=max(1, int(r / 7)))
        d.text((x, y + r * 0.42), et, font=f, fill=R['metin2'], anchor='ms')
