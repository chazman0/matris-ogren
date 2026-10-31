#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atölye · Modern — 3B görünüm: parametrik çelik çerçeve (Depo Binası – Tokat OSB) + numpy z-tamponlu
yazılımsal rasterleştirici. Ekstrüde I/L profiller düz gölgelenmiş dörtgenler + ince koyu kenarlar,
beyaz→açık gri gradyan + model arkasında yumuşak ortam ışığı, yer gölgesi, 1 m ızgara, aks balonları,
kat seviye çizgileri (etkin kat vurgulu). Seçim/üzerinde renkleri belirtec.py'deki etkin vurgu paletinden gelir.

Modlar: "secim" (6 kiriş seçili + üzerinde kolon), "dc" (D/C renk haritası), "duz" (seçimsiz).
"""
import math
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from belirtec import C, DC_RENK, DC_ESIK, hex2rgb, karisim
from tuval import yazi_tipi

PROFILLER = {  # h, b, tw, tf (m)
    "HE340A": (0.330, 0.300, 0.0095, 0.0165),
    "IPE400": (0.400, 0.180, 0.0086, 0.0135),
    "IPE200": (0.200, 0.100, 0.0056, 0.0085),
}
X_AKS = [0.0, 6.0, 12.0, 18.0]            # A B C D
Y_AKS = [0.0, 6.0, 12.0, 18.0, 24.0]      # 1 2 3 4 5
Z_KAT = [0.0, 4.5, 9.0, 13.5]             # Zemin, Kat 1, Kat 2, Kat 3 (çatı)
KAT_AD = ["Zemin", "Kat 1", "Kat 2", "Kat 3"]
AKS_X_AD = "ABCD"
AKS_Y_AD = "12345"


def i_profil(h, b, tw, tf):
    hb, bb, tw2 = h / 2, b / 2, tw / 2
    return [(-bb, -hb), (bb, -hb), (bb, -hb + tf), (tw2, -hb + tf), (tw2, hb - tf), (bb, hb - tf),
            (bb, hb), (-bb, hb), (-bb, hb - tf), (-tw2, hb - tf), (-tw2, -hb + tf), (-bb, -hb + tf)]


def i_kapaklar(h, b, tw, tf):
    hb, bb, tw2 = h / 2, b / 2, tw / 2
    return [
        [(-bb, -hb), (bb, -hb), (bb, -hb + tf), (-bb, -hb + tf)],
        [(-tw2, -hb + tf), (tw2, -hb + tf), (tw2, hb - tf), (-tw2, hb - tf)],
        [(-bb, hb - tf), (bb, hb - tf), (bb, hb), (-bb, hb)],
    ]


def l_profil(a, t):
    """Eşit kollu köşebent (L a×t), köşe orijinde değil: kütle merkezine yakın konum."""
    o = -a * 0.3
    return [(o, o), (o + a, o), (o + a, o + t), (o + t, o + t), (o + t, o + a), (o, o + a)]


def l_kapaklar(a, t):
    o = -a * 0.3
    return [[(o, o), (o + a, o), (o + a, o + t), (o, o + t)], [(o, o + t), (o + t, o + t), (o + t, o + a), (o, o + a)]]


def dik_profil(bu, bv):
    return [(-bu / 2, -bv / 2), (bu / 2, -bv / 2), (bu / 2, bv / 2), (-bu / 2, bv / 2)]


def birim(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def capraz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def nokta_carpim(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Eleman:
    """Ekstrüde profil: p0→p1 ekseni, u/v profil eksenleri, kesit çokgeni (CCW), kapak parçaları (dışbükey)."""

    def __init__(self, p0, p1, profil, kapaklar=None, u_ipucu=None, v_ipucu=None, tur="kiris", kat=0, etiket=""):
        self.p0, self.p1, self.profil = p0, p1, profil
        self.tur, self.kat, self.etiket = tur, kat, etiket
        self.durum = ""          # "", "secili", "hover"
        self.dc = None           # D/C oranı
        eksen = birim(tuple(p1[i] - p0[i] for i in range(3)))
        self.eksen = eksen
        if v_ipucu is None:
            v_ipucu = (0, 0, 1) if abs(eksen[2]) < 0.9 else (0, 1, 0)
        if u_ipucu is None:
            u = birim(capraz(v_ipucu, eksen))
        else:
            u = birim(u_ipucu)
        v = birim(capraz(eksen, u))
        self.u, self.v = u, v
        n = len(profil)
        alan = sum(profil[i][0] * profil[(i + 1) % n][1] - profil[(i + 1) % n][0] * profil[i][1] for i in range(n))
        if alan < 0:
            self.profil = profil[::-1]
        self.kapaklar = kapaklar if kapaklar is not None else [self.profil]

    def W(self, p, pu, pv):
        return tuple(p[i] + self.u[i] * pu + self.v[i] * pv for i in range(3))

    def yuzler(self):
        p0, p1, e = self.p0, self.p1, self.eksen
        prof = self.profil
        n = len(prof)
        out = []
        for i in range(n):
            a, b = prof[i], prof[(i + 1) % n]
            d = (b[0] - a[0], b[1] - a[1])
            n2 = (d[1], -d[0])
            nrm = birim(tuple(self.u[k] * n2[0] + self.v[k] * n2[1] for k in range(3)))
            out.append(([self.W(p0, a[0], a[1]), self.W(p0, b[0], b[1]), self.W(p1, b[0], b[1]), self.W(p1, a[0], a[1])], nrm))
        for pc in self.kapaklar:
            out.append(([self.W(p0, q[0], q[1]) for q in pc][::-1], tuple(-c for c in e)))
            out.append(([self.W(p1, q[0], q[1]) for q in pc], e))
        return out

    def kutu_koseleri(self):
        us = [q[0] for q in self.profil]; vs = [q[1] for q in self.profil]
        pts = []
        for p in (self.p0, self.p1):
            for pu in (min(us), max(us)):
                for pv in (min(vs), max(vs)):
                    pts.append(self.W(p, pu, pv))
        return pts

    def orta(self):
        return tuple((self.p0[i] + self.p1[i]) / 2 for i in range(3))


# ----------------------------------------------------------------------------
def model_olustur():
    """Depo Binası – Tokat OSB. Döndürür: elemanlar, seçili kiriş listesi (6), hover elemanı."""
    X, Y, Z = X_AKS, Y_AKS, Z_KAT
    kol = PROFILLER["HE340A"]; kir = PROFILLER["IPE400"]; tali = PROFILLER["IPE200"]
    el = []
    # kolonlar: kat kat ayrı eleman (HE340A, gövde x yönünde: çerçeve düzlemi XZ)
    for k in range(3):
        for xi, x in enumerate(X):
            for yi, y in enumerate(Y):
                e = Eleman((x, y, Z[k]), (x, y, Z[k + 1]), i_profil(*kol), i_kapaklar(*kol),
                           u_ipucu=(0, 1, 0), tur="kolon", kat=k + 1, etiket=f"K{k + 1}-{AKS_X_AD[xi]}{AKS_Y_AD[yi]}")
                el.append(e)
    secili, hover = [], None
    # ana kirişler (IPE400), üst başlık kat seviyesinde
    hk = kir[0]
    for k in (1, 2, 3):
        zc = Z[k] - hk / 2
        for yi, y in enumerate(Y):          # x yönünde (A–D) 3 açıklık
            for xi in range(3):
                x0, x1 = X[xi] + kol[0] / 2, X[xi + 1] - kol[0] / 2
                e = Eleman((x0, y, zc), (x1, y, zc), i_profil(*kir), i_kapaklar(*kir), tur="kiris", kat=k,
                           etiket=f"K{k}-{AKS_Y_AD[yi]}{AKS_X_AD[xi]}{AKS_X_AD[xi + 1]}")
                if k == 2 and yi in (0, 1):
                    e.durum = "secili"; secili.append(e)
                el.append(e)
        for xi, x in enumerate(X):          # y yönünde (1–5) 4 açıklık
            for yi in range(4):
                y0, y1 = Y[yi] + kol[1] / 2, Y[yi + 1] - kol[1] / 2
                el.append(Eleman((x, y0, zc), (x, y1, zc), i_profil(*kir), i_kapaklar(*kir), tur="kiris", kat=k,
                                 etiket=f"K{k}-{AKS_X_AD[xi]}{AKS_Y_AD[yi]}{AKS_Y_AD[yi + 1]}"))
    # hover: C/2 kolonu, Kat 2
    for e in el:
        if e.tur == "kolon" and e.kat == 2 and abs(e.p0[0] - 0) < 1e-6 and abs(e.p0[1] - 0) < 1e-6:
            e.durum = "hover"; hover = e
    # çatı aşıkları IPE200 (y yönünde, 2 m aralık, +13,50)
    ht = tali[0]
    zc = Z[3] + ht / 2 + 0.02
    for xb in range(3):
        for dx in (2.0, 4.0):
            x = X[xb] + dx
            for yi in range(4):
                y0, y1 = Y[yi] + kir[1] / 2, Y[yi + 1] - kir[1] / 2
                el.append(Eleman((x, y0, zc), (x, y1, zc), i_profil(*tali), i_kapaklar(*tali), tur="asik", kat=3))
    # tali kirişler IPE200 (+4,50 altında döşeme altı; +9,00 asma kat bölgesi)
    for k, ybays in ((1, range(4)), (2, range(2, 4))):
        zc = Z[k] - ht / 2
        for xb in range(3):
            for dx in (2.0, 4.0):
                x = X[xb] + dx
                for yi in ybays:
                    y0, y1 = Y[yi] + kir[1] / 2, Y[yi + 1] - kir[1] / 2
                    el.append(Eleman((x, y0, zc), (x, y1, zc), i_profil(*tali), i_kapaklar(*tali), tur="tali", kat=k))
    # düşey X çaprazlar L100x10: A ve D akslarında 1–2 ve 4–5 açıklıkları, üç kat
    lp, lk = l_profil(0.10, 0.010), l_kapaklar(0.10, 0.010)
    for x in (0.0, 18.0):
        for (ya, yb) in ((0.0, 6.0), (18.0, 24.0)):
            for k in range(3):
                za, zb = Z[k], Z[k + 1]
                off = kol[1] / 2 + 0.05
                el.append(Eleman((x, ya + off, za + 0.40), (x, yb - off, zb - 0.55), lp, lk, tur="capraz", kat=k + 1))
                el.append(Eleman((x, yb - off, za + 0.40), (x, ya + off, zb - 0.55), lp, lk, tur="capraz", kat=k + 1))
    # çatı düzlemi yatay çaprazları (A–B/1–2 ve C–D/4–5)
    for (xa, xb, ya, yb) in ((0, 6, 0, 6), (12, 18, 18, 24)):
        zc = Z[3] - 0.10
        el.append(Eleman((xa + 0.5, ya + 0.5, zc), (xb - 0.5, yb - 0.5, zc), dik_profil(0.08, 0.08), tur="capraz", kat=3))
        el.append(Eleman((xb - 0.5, ya + 0.5, zc), (xa + 0.5, yb - 0.5, zc), dik_profil(0.08, 0.08), tur="capraz", kat=3))
    # betonarme döşemeler: Kat 1 tam (18×24), Kat 2 asma kat (y 12–24); 15 cm
    el.append(Eleman((-0.15, 12.0, Z[1] + 0.075), (18.15, 12.0, Z[1] + 0.075), dik_profil(24.3, 0.15), tur="doseme", kat=1))
    el.append(Eleman((-0.15, 18.0, Z[2] + 0.075), (18.15, 18.0, Z[2] + 0.075), dik_profil(12.3, 0.15), tur="doseme", kat=2))
    # temel pabuçları (tekil, 1,8×1,8×0,6)
    for x in X:
        for y in Y:
            el.append(Eleman((x, y, -0.60), (x, y, 0.0), dik_profil(1.8, 1.8), u_ipucu=(1, 0, 0), tur="temel", kat=0))
    return el, secili, hover


def dc_ata(elemanlar):
    """Deterministik, inandırıcı D/C dağılımı: alt kat kolonları ve orta açıklık kirişleri yüksek."""
    for i, e in enumerate(elemanlar):
        o = e.orta()
        h = (math.sin(o[0] * 1.7 + o[1] * 0.9 + i * 0.37) + 1) / 2
        if e.tur == "kolon":
            taban = {1: 0.78, 2: 0.62, 3: 0.42}[e.kat]
            v = taban + 0.22 * h
            if e.kat == 1 and abs(o[0] - 12) < 1e-6 and abs(o[1] - 6) < 1e-6:
                v = 1.04  # bir kolon aşıyor (hikâye: C/2 kolonu)
        elif e.tur == "kiris":
            ic = 0.0 < o[0] < 18.0 and 0.0 < o[1] < 24.0
            taban = 0.58 if ic else 0.44
            v = taban + 0.30 * h
            if e.kat == 1 and abs(o[1] - 12) < 1e-6:
                v = 0.86 + 0.12 * h
        elif e.tur in ("asik", "tali"):
            v = 0.35 + 0.30 * h
        elif e.tur == "capraz":
            v = 0.50 + 0.35 * h
        else:
            v = None
        e.dc = v


def dc_renk(v):
    for esik, renk in zip(DC_ESIK, DC_RENK):
        if v <= esik:
            return renk
    return DC_RENK[-1]


class Kamera:
    def __init__(self, hedef, yon, uzaklik, fov_derece, W, H):
        self.hedef = hedef
        d = birim(yon)
        self.eye = tuple(hedef[i] + d[i] * uzaklik for i in range(3))
        f = birim(tuple(hedef[i] - self.eye[i] for i in range(3)))
        r = birim(capraz(f, (0, 0, 1)))
        u = capraz(r, f)
        self.f, self.r, self.u = f, r, u
        self.W, self.H = W, H
        self.fl = (H / 2) / math.tan(math.radians(fov_derece) / 2)
        self.cx, self.cy = W / 2, H / 2

    def kam(self, p):
        v = tuple(p[i] - self.eye[i] for i in range(3))
        return (nokta_carpim(v, self.r), nokta_carpim(v, self.u), nokta_carpim(v, self.f))

    def izdusum(self, p):
        x, y, z = self.kam(p)
        if z <= 0.05:
            z = 0.05
        return (self.cx + self.fl * x / z, self.cy - self.fl * y / z, z)


def disbukey_kabuk(pts):
    pts = sorted(set(pts))
    if len(pts) <= 2:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    alt = []
    for p in pts:
        while len(alt) >= 2 and cr(alt[-2], alt[-1], p) <= 0:
            alt.pop()
        alt.append(p)
    ust = []
    for p in reversed(pts):
        while len(ust) >= 2 and cr(ust[-2], ust[-1], p) <= 0:
            ust.pop()
        ust.append(p)
    return alt[:-1] + ust[:-1]


class Rasterci:
    def __init__(self, W, H, arka):
        self.W, self.H = W, H
        self.rgb = np.asarray(arka.convert("RGB"), dtype=np.float32).copy()
        self.inv = np.zeros((H, W), dtype=np.float32)

    def cokgen(self, pts, invz, renk):
        W, H = self.W, self.H
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0 = max(int(math.floor(min(xs))), 0); x1 = min(int(math.ceil(max(xs))), W - 1)
        y0 = max(int(math.floor(min(ys))), 0); y1 = min(int(math.ceil(max(ys))), H - 1)
        if x1 < x0 or y1 < y0:
            return
        n = len(pts)
        alan = sum(xs[i] * ys[(i + 1) % n] - xs[(i + 1) % n] * ys[i] for i in range(n))
        if abs(alan) < 1e-6:
            return
        if alan < 0:
            pts = pts[::-1]; invz = invz[::-1]; xs = xs[::-1]; ys = ys[::-1]
        X = np.arange(x0, x1 + 1, dtype=np.float32) + 0.5
        Y = np.arange(y0, y1 + 1, dtype=np.float32) + 0.5
        XX, YY = np.meshgrid(X, Y)
        icerde = np.ones(XX.shape, dtype=bool)
        for i in range(n):
            ax, ay = xs[i], ys[i]; bx, by = xs[(i + 1) % n], ys[(i + 1) % n]
            icerde &= ((bx - ax) * (YY - ay) - (by - ay) * (XX - ax)) >= -0.001
        if not icerde.any():
            return
        i0, i1 = 0, 1
        best, i2 = -1, 2
        for k in range(2, n):
            d = abs((xs[i1] - xs[i0]) * (ys[k] - ys[i0]) - (ys[i1] - ys[i0]) * (xs[k] - xs[i0]))
            if d > best:
                best, i2 = d, k
        A = np.array([[xs[i0], ys[i0], 1], [xs[i1], ys[i1], 1], [xs[i2], ys[i2], 1]], dtype=np.float64)
        try:
            a, b, c = np.linalg.solve(A, np.array([invz[i0], invz[i1], invz[i2]], dtype=np.float64))
        except np.linalg.LinAlgError:
            a, b, c = 0.0, 0.0, float(np.mean(invz))
        Z = (a * XX + b * YY + c).astype(np.float32)
        buf = self.inv[y0:y1 + 1, x0:x1 + 1]
        m = icerde & (Z > buf)
        if not m.any():
            return
        buf[m] = Z[m]
        sub = self.rgb[y0:y1 + 1, x0:x1 + 1]
        sub[m] = np.array(renk, dtype=np.float32)

    def kenar(self, p, q, izp, izq, renk, alfa=0.55, bias=1.004, kalin=1):
        W, H = self.W, self.H
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        if L < 0.5:
            return
        N = int(L * 1.3) + 2
        t = np.linspace(0.0, 1.0, N, dtype=np.float32)
        X = (p[0] + dx * t); Y = (p[1] + dy * t)
        Zi = (izp + (izq - izp) * t) * bias
        r = np.array(renk, dtype=np.float32)
        # kalın çizgi: dik yönde kaydırılmış kopyalar
        nx, ny = -dy / L, dx / L
        kaymalar = [0.0] if kalin <= 1 else [(-(kalin - 1) / 2 + i) for i in range(kalin)]
        for sh in kaymalar:
            xi = np.floor(X + nx * sh).astype(np.int32); yi = np.floor(Y + ny * sh).astype(np.int32)
            ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
            xi2, yi2, Zi2 = xi[ok], yi[ok], Zi[ok]
            if xi2.size == 0:
                continue
            m = Zi2 >= self.inv[yi2, xi2]
            xi2, yi2 = xi2[m], yi2[m]
            if xi2.size == 0:
                continue
            self.rgb[yi2, xi2] = self.rgb[yi2, xi2] * (1 - alfa) + r * alfa

    def resim(self):
        return Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8), "RGB")


# nesne türü → taban rengi (anlam taşıyan nötr palet) ve kenar rengi — belirtec.MODEL'den
def renk_tabani():
    return {t: C[t] for t in ("kolon", "kiris", "tali", "asik", "capraz", "doseme", "temel")}


def kenar_rengi():
    return {"kolon": C["kenar"], "kiris": C["kenar"], "tali": C["kenar_ince"], "asik": C["kenar_ince"],
            "capraz": C["kenar"], "doseme": C["kenar_doseme"], "temel": C["kenar_doseme"]}


def golgele(taban, nrm, isik, acik=False):
    lam = max(0.0, nokta_carpim(nrm, isik))
    gok = max(0.0, nrm[2])
    if acik:   # seçim dolgusu: açık kalsın, yalnız hafif gölge
        k = 0.84 + 0.14 * lam + 0.04 * gok
    else:
        k = 0.50 + 0.40 * lam + 0.12 * gok
    k = min(1.06, k)
    t = hex2rgb(taban)
    return tuple(min(255, c * k) for c in t)


class Sahne:
    """Üretilen görünüm + mantıksal koordinata izdüşüm yardımcıları."""

    def __init__(self, im, kam, k, elemanlar, secili, hover):
        self.im, self.kam, self.k = im, kam, k
        self.elemanlar, self.secili, self.hover = elemanlar, secili, hover

    def iz(self, p):
        """3B nokta → mantıksal (1×) görünüm koordinatı."""
        q = self.kam.izdusum(p)
        return (q[0] / self.k, q[1] / self.k)

    def eksen_vektor(self, v):
        dx = nokta_carpim(v, self.kam.r); dy = nokta_carpim(v, self.kam.u)
        return dx, dy


def sahne_ciz(W, H, s, ss=2, mod="secim", diyagram=False, secili_goster=True):
    """W×H mantıksal görünümü s ölçeğinde (ss kat örnekleme) üretir. Döndürür: Sahne."""
    t0 = time.time()
    k = s * ss
    Wp, Hp = int(W * k), int(H * k)
    elemanlar, secili, hover = model_olustur()
    if mod == "dc":
        dc_ata(elemanlar)
        secili, hover = [], None
        for e in elemanlar:
            e.durum = ""
            if e.tur == "kolon" and e.kat == 1 and abs(e.p0[0] - 12) < 1e-6 and abs(e.p0[1] - 6) < 1e-6:
                e.durum = "secili"; secili.append(e)
    elif mod == "suzgec":   # Seç ve Süz önizlemesi: Kat 2'deki 31 IPE400 kiriş altın konturla
        secili, hover = [], None
        for e in elemanlar:
            e.durum = "secili" if (e.tur == "kiris" and e.kat == 2) else ""
            if e.durum == "secili":
                secili.append(e)
    elif mod == "duz" or not secili_goster:
        for e in elemanlar:
            e.durum = ""
    X, Y, Z = X_AKS, Y_AKS, Z_KAT
    hedef = (9.0, 11.0, 5.2)
    yon = (-1.0, -1.30, 0.62)
    kam = Kamera(hedef, yon, 70.0, 30.0, Wp, Hp)
    onemli = [(x, y, z) for x in (-3.6, 20.6) for y in (-3.8, 26.4) for z in (-0.6, 14.0)]
    pr = [kam.izdusum(p) for p in onemli]
    minx, maxx = min(p[0] for p in pr), max(p[0] for p in pr)
    miny, maxy = min(p[1] for p in pr), max(p[1] for p in pr)
    marj_x, marj_y = 0.045 * Wp, 0.06 * Hp
    sx = (Wp - 2 * marj_x) / (maxx - minx); sy = (Hp - 2 * marj_y) / (maxy - miny)
    kam.fl *= min(sx, sy)
    pr = [kam.izdusum(p) for p in onemli]
    minx, maxx = min(p[0] for p in pr), max(p[0] for p in pr)
    miny, maxy = min(p[1] for p in pr), max(p[1] for p in pr)
    kam.cx += (Wp / 2 - (minx + maxx) / 2) + 0.012 * Wp
    kam.cy += (Hp / 2 - (miny + maxy) / 2) + 0.012 * Hp

    # --- arka plan: beyaz → açık gri dikey gradyan ---
    band = Image.new("RGB", (1, Hp))
    px = band.load()
    u_, a_ = hex2rgb(C["vp_ust"]), hex2rgb(C["vp_alt"])
    for i in range(Hp):
        t = i / (Hp - 1)
        px[0, i] = tuple(int(round(u_[j] + (a_[j] - u_[j]) * t)) for j in range(3))
    arka = band.resize((Wp, Hp))
    # model arkasında yumuşak ortam ışığı (beyaz elips, çok geniş bulanıklık) — "ortam" hissi
    parl = Image.new("L", (Wp, Hp), 0)
    merk = kam.izdusum((9.0, 12.0, 6.0))
    ImageDraw.Draw(parl).ellipse([merk[0] - Wp * 0.36, merk[1] - Hp * 0.40, merk[0] + Wp * 0.36, merk[1] + Hp * 0.34], fill=150)
    parl = parl.filter(ImageFilter.GaussianBlur(Wp * 0.09))
    arka.paste(Image.new("RGB", (Wp, Hp), hex2rgb(C["vp_isik"])), (0, 0), parl)

    isik = birim((-0.45, -0.50, 0.74))
    # yer gölgesi (eleman kutularının ışık yönünde izdüşümü), yumuşak
    golge = Image.new("L", (Wp, Hp), 0)
    gd = ImageDraw.Draw(golge)
    for e in elemanlar:
        if e.tur in ("doseme", "temel"):
            continue
        pts2 = []
        for p in e.kutu_koseleri():
            tt = p[2] / isik[2]
            g = (p[0] - isik[0] * tt, p[1] - isik[1] * tt, 0.0)
            q = kam.izdusum(g)
            pts2.append((q[0], q[1]))
        kabuk = disbukey_kabuk(pts2)
        if len(kabuk) >= 3:
            gd.polygon(kabuk, fill=255)
    golge = golge.filter(ImageFilter.GaussianBlur(Wp * 0.004))
    gol = np.asarray(golge, dtype=np.float32) / 255.0 * 0.17
    arr = np.asarray(arka, dtype=np.float32)
    arr = arr * (1 - gol[..., None]) + np.array([150, 152, 158], dtype=np.float32) * gol[..., None]
    ao = Image.new("L", (Wp, Hp), 0)
    ad = ImageDraw.Draw(ao)
    for x in X:
        for y in Y:
            q = kam.izdusum((x, y, 0.0))
            r = Wp * 0.007
            ad.ellipse([q[0] - r * 1.6, q[1] - r * 0.9, q[0] + r * 1.6, q[1] + r * 0.9], fill=255)
    ao = ao.filter(ImageFilter.GaussianBlur(Wp * 0.004))
    aoa = np.asarray(ao, dtype=np.float32) / 255.0 * 0.20
    arr = arr * (1 - aoa[..., None]) + np.array([120, 124, 130], dtype=np.float32) * aoa[..., None]
    arka = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    # 1 m ızgara, uzaklıkla solan; aks çizgileri daha belirgin
    izg = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0))
    gd = ImageDraw.Draw(izg)
    lw = max(1, int(round(0.5 * k)))

    def yer_cizgi(p, q, renk, alfa, w):
        n = 10
        for i in range(n):
            ta, tb = i / n, (i + 1) / n
            pa = tuple(p[j] + (q[j] - p[j]) * ta for j in range(3)); pb = tuple(p[j] + (q[j] - p[j]) * tb for j in range(3))
            qa = kam.izdusum(pa); qb = kam.izdusum(pb)
            z = (qa[2] + qb[2]) / 2
            fade = max(0.10, min(1.0, 2.0 - z / 60.0))
            gd.line([(qa[0], qa[1]), (qb[0], qb[1])], fill=hex2rgb(renk) + (int(255 * alfa * fade),), width=w)

    for gx in range(-10, 29):
        major = gx % 6 == 0 and -1 < gx < 19
        yer_cizgi((gx, -10, 0), (gx, 34, 0), C["izgara_ana"] if major else C["izgara"], 0.50 if major else 0.24, lw * (2 if major else 1))
    for gy in range(-10, 35):
        major = gy % 6 == 0 and -1 < gy < 25
        yer_cizgi((-10, gy, 0), (28, gy, 0), C["izgara_ana"] if major else C["izgara"], 0.50 if major else 0.24, lw * (2 if major else 1))
    for gx in X:
        yer_cizgi((gx, -3.2, 0), (gx, 0, 0), C["aks"], 0.85, lw * 2)
        yer_cizgi((gx, 24, 0), (gx, 27.2, 0), C["aks"], 0.5, lw * 2)
    for gy in Y:
        yer_cizgi((-3.2, gy, 0), (0, gy, 0), C["aks"], 0.85, lw * 2)
        yer_cizgi((18, gy, 0), (21.2, gy, 0), C["aks"], 0.5, lw * 2)
    arka = Image.alpha_composite(arka.convert("RGBA"), izg).convert("RGB")

    # --- z-tamponlu elemanlar ---
    R = Rasterci(Wp, Hp, arka)
    yuzler = []
    for e in elemanlar:
        for (kose, nrm) in e.yuzler():
            cen = tuple(sum(q[i] for q in kose) / len(kose) for i in range(3))
            bak = tuple(kam.eye[i] - cen[i] for i in range(3))
            if nokta_carpim(nrm, bak) <= 0:
                continue
            yuzler.append((kose, nrm, e))
    kenar_listesi = []
    RENK_TABANI = renk_tabani()
    for kose, nrm, e in yuzler:
        pr = [kam.izdusum(q) for q in kose]
        pts = [(p[0], p[1]) for p in pr]; iz = [1.0 / p[2] for p in pr]
        if e.durum == "secili" and mod != "dc":
            taban = C["secim_dolgu"]
        elif mod == "dc" and e.dc is not None:
            taban = karisim(dc_renk(e.dc), "#FFFFFF", 0.18)
        else:
            taban = RENK_TABANI[e.tur]
        R.cokgen(pts, iz, golgele(taban, nrm, isik, acik=(e.durum == "secili" and mod != "dc")))
        kenar_listesi.append((pr, e))
    kr = {t: hex2rgb(v) for t, v in kenar_rengi().items()}
    ks = hex2rgb(C["secim"]); kh = hex2rgb(C["hover_model"])
    for pr, e in kenar_listesi:
        n = len(pr)
        for i in range(n):
            a, b = pr[i], pr[(i + 1) % n]
            if e.durum == "secili" and mod != "dc":
                R.kenar((a[0], a[1]), (b[0], b[1]), 1.0 / a[2], 1.0 / b[2], ks, alfa=0.60, kalin=max(1, int(round(k * 0.5))))
            elif e.durum == "secili":
                R.kenar((a[0], a[1]), (b[0], b[1]), 1.0 / a[2], 1.0 / b[2], ks, alfa=0.95, kalin=max(1, int(round(k * 0.8))))
            elif e.durum == "hover":
                R.kenar((a[0], a[1]), (b[0], b[1]), 1.0 / a[2], 1.0 / b[2], kh, alfa=0.80, kalin=max(1, int(round(k * 0.5))))
            elif mod == "dc":
                R.kenar((a[0], a[1]), (b[0], b[1]), 1.0 / a[2], 1.0 / b[2], (60, 64, 70), alfa=0.45, kalin=max(1, int(round(k * 0.5))))
            else:
                R.kenar((a[0], a[1]), (b[0], b[1]), 1.0 / a[2], 1.0 / b[2], kr[e.tur], alfa=0.50, kalin=max(1, int(round(k * 0.5))))
    im = R.resim()

    # --- ekran uzayı notları: aks baloncukları, kat seviyeleri, (isteğe bağlı) moment diyagramı ---
    ov = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    fb = yazi_tipi(11, 500, k)
    rb = 10.5 * k
    bal = []
    for i, gx in enumerate(X):
        q = kam.izdusum((gx, -3.2, 0.0)); bal.append((q, AKS_X_AD[i]))
    for i, gy in enumerate(Y):
        q = kam.izdusum((-3.2, gy, 0.0)); bal.append((q, AKS_Y_AD[i]))
    for q, etiket in bal:
        cx, cy = q[0], q[1] - rb * 1.35
        od.line([(q[0], q[1]), (cx, cy + rb)], fill=(126, 133, 143, 220), width=max(1, int(k)))
        od.ellipse([cx - rb, cy - rb, cx + rb, cy + rb], fill=(255, 255, 255, 250), outline=hex2rgb(C["metin2"]) + (255,), width=max(1, int(round(1.0 * k))))
        od.text((cx, cy + 0.5 * k), etiket, font=fb, fill=hex2rgb(C["metin"]), anchor="mm")
    fl = yazi_tipi(11, 500, k)
    fk = yazi_tipi(11, 600, k)
    for z, ad_ in zip(Z, KAT_AD):
        etkin = abs(z - 9.0) < 1e-6 and mod != "dc"
        q = kam.izdusum((18.0, 0.0, z)); q2 = kam.izdusum((20.6, 0.0, z))
        cr = hex2rgb(C["vurgu"]) if etkin else (90, 96, 104)
        od.line([(q[0], q[1]), (q2[0], q2[1])], fill=cr + (200 if etkin else 150,), width=max(1, int(k)))
        tri = [(q2[0] + 1 * k, q2[1]), (q2[0] + 7 * k, q2[1] - 5 * k), (q2[0] + 7 * k, q2[1] + 5 * k)]
        od.polygon(tri, fill=(hex2rgb(C["vurgu"]) if etkin else hex2rgb(C["metin2"])) + (255,))
        metin = f"{z:+.2f}  {ad_}".replace(".", ",").replace("+0,00", "±0,00")
        od.text((q2[0] + 12 * k, q2[1] - 1 * k), metin, font=fk if etkin else fl, fill=hex2rgb(C["metin"]), anchor="lm")
    # seçim: dış kontur (dışbükey kabuk, örtmeden bağımsız — seçim her zaman üstte) + yumuşak hale
    kabuklar = []
    for e in elemanlar:
        if e.durum != "secili":
            continue
        pts2 = [tuple(kam.izdusum(p)[:2]) for p in e.kutu_koseleri()]
        kabuk = disbukey_kabuk(pts2)
        if len(kabuk) >= 3:
            kabuklar.append(kabuk)
    if kabuklar and mod != "dc":
        hale = Image.new("L", (Wp, Hp), 0)
        hd = ImageDraw.Draw(hale)
        for kabuk in kabuklar:
            hd.line(kabuk + [kabuk[0]], fill=255, width=max(2, int(round(5 * k))), joint="curve")
        hale = hale.filter(ImageFilter.GaussianBlur(3.2 * k)).point(lambda v: int(v * 0.42))
        ov.paste(Image.new("RGBA", (Wp, Hp), hex2rgb(C["secim"]) + (255,)), (0, 0), hale)
        od = ImageDraw.Draw(ov)
    for kabuk in kabuklar:
        od.line(kabuk + [kabuk[0]], fill=hex2rgb(C["secim"]) + (245,), width=max(2, int(round(2.0 * k))), joint="curve")
    if diyagram:
        moment_diyagrami(od, kam, k)
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    if ss != 1:
        im = im.resize((int(W * s), int(H * s)), Image.LANCZOS)
    print(f"  3B görünüm {W}×{H} @ {s}× ss{ss} ({len(yuzler)} yüz, {mod}) {time.time() - t0:.1f} s")
    return Sahne(im, kam, k, elemanlar, secili, hover)


def moment_diyagrami(od, kam, k):
    """Aks 1 çerçevesi (y=0) kirişlerinde M3 diyagramı: çerçeve düzleminde, çekme tarafında, yarı saydam Kahve."""
    renk = hex2rgb(C["vurgu"]) + (90,)
    kenar = hex2rgb(C["vurgu"]) + (230,)
    olc = 0.55  # m / (kNm birimsiz), görsel
    for z in Z_KAT[1:]:
        for xi in range(3):
            x0, x1 = X_AKS[xi] + 0.165, X_AKS[xi + 1] - 0.165
            n = 14
            ust, alt = [], []
            for i in range(n + 1):
                t = i / n
                x = x0 + (x1 - x0) * t
                # ankastre kiriş benzeri: uçlarda negatif, ortada pozitif
                m = (-1.0 + 6.0 * t * (1 - t)) * (1.0 if z < 13 else 0.6)
                p = (x, 0.0, z - 0.2)
                q = (x, 0.0, z - 0.2 - m * olc)
                ust.append(kam.izdusum(p)[:2]); alt.append(kam.izdusum(q)[:2])
            od.polygon(ust + alt[::-1], fill=renk)
            od.line(alt, fill=kenar, width=max(1, int(k)))
            # uç ve orta değer etiketleri
            f = yazi_tipi(10, 500, k)
            for t, m in ((0.0, -1.0), (0.5, 0.5), (1.0, -1.0)):
                x = x0 + (x1 - x0) * t
                q = kam.izdusum((x, 0.0, z - 0.2 - m * olc))
                deger = f"{(m * (118 if z < 13 else 71)):.0f}".replace("-", "−")
                od.text((q[0] + (6 * k if t < 1 else -6 * k), q[1] + (8 * k if m < 0 else -8 * k)), deger, font=f,
                        fill=hex2rgb(C["metin"]), anchor="lm" if t < 1 else "rm")
