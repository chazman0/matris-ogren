"""Kemer Çizgisi (açık zemin) — açılış ekranı kareleri (Pillow).

1920x1080 (2x) çizer, sonra 960x540'a Lanczos ile indirger.
Kareler milisaniye cinsinden zamanla üretilir; zaman çizelgesi animasyon.sablon.html ile birebirdir.
Kullanım: python3 -I uret.py
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

KOK = os.path.dirname(os.path.abspath(__file__))
KIMLIK = os.path.join(KOK, '..')
FONT = os.path.join(KOK, '..', 'fontlar')

S = 2                      # 2x (200% DPI)
W, H = 960, 540            # mantıksal piksel
SS = 4                     # çizgi katmanı için ek süper örnekleme

# --- renkler (kimlik) ---
KAHVE = (0x8A, 0x6B, 0x3C)
KREM = (0xED, 0xE6, 0xD8)
ALTIN = (0xB0, 0x89, 0x50)
ANTRASIT = (0x14, 0x18, 0x1B)
GRI = (0x8C, 0x8C, 0x8C)
# --- açık zemin (Krem'den türetilmiş kâğıt tonu) ---
KAGIT = (0xF6, 0xF2, 0xEA)         # zemin
KAGIT_MERKEZ = (0xFB, 0xF8, 0xF2)  # kemerin arkasında hafif aydınlanma
KAGIT_KENAR = (0xEF, 0xE9, 0xDD)   # köşelerde hafif vinyet
UC = tuple(round(ALTIN[i] * 0.7 + KREM[i] * 0.3) for i in range(3))   # ilerleme ucu: Altın %70 + Krem %30 = #C2A579

# --- çizgi ayarları (DIP) ---
IZ_KALINLIK = 1.75         # altın çizim izi (koyu sürümde 1,5; açık zeminde biraz daha dolu)
KENAR_KALINLIK = 0.9       # kilit taşı kenar çizgisi
KENAR_ALFA = 0.70

# --- yerleşim (mantıksal px) ---
KEMER_CX = 268             # kemerin ekseni
KEMER_UST = 112            # simge içeriğinin (kilit taşı tepesi) üstü
KEMER_YUK = 256            # simge içeriğinin yüksekliği (kilit taşı tepesi -> ayak)
SAG_X = 512                # sağ sütunun sol kenarı
SAG_SON = 904              # sağ sütunun sağ kenarı

K = json.load(open(os.path.join(KOK, 'kontur.json')))
OLCU = K['olcu']
BX0, BY0, BX1, BY1 = OLCU['bbox']
OLCEK = KEMER_YUK / (BY1 - BY0)          # simge px -> mantıksal px


def simge_xy(x, y):
    """Simge PNG koordinatı -> mantıksal ekran koordinatı."""
    return (KEMER_CX + (x - OLCU['cx']) * OLCEK, KEMER_UST + (y - BY0) * OLCEK)


KEMER_ALT = simge_xy(0, BY1)[1]
UZENGI_Y = simge_xy(0, OLCU['uzengi_y'])[1]
KEMER_SOL = simge_xy(BX0, 0)[0]
KEMER_SAG = simge_xy(BX1, 0)[0]

# --- kilit taşı ışığı ---
KILIT_MERKEZ = (268.0, 136.9)   # kilit taşı ağırlık merkezi (konturdan)
KILIT_GEN = 49.5                # kilit taşının üst genişliği
ISIK_R = 112.0                  # ≈ 2,25 × kilit taşı genişliği
ISIK_TEPE = 0.22                # merkezde en yüksek opaklık
ISIK_KALAN = 0.05               # son karede kalan opaklık
HALKA_R0, HALKA_R1 = 28.0, 150.0
HALKA_TEPE = 0.035
HALKA_GEN = 26.0                # halkanın yumuşak yarı genişliği (kenarı belli olmayan geniş bir dalga)


def font(ad, boy, eksen):
    yol = {'inter': 'inter-Inter[opsz,wght].ttf', 'cinzel': 'cinzel-Cinzel[wght].ttf',
           'cormorant': 'cormorantgaramond-CormorantGaramond[wght].ttf'}[ad]
    f = ImageFont.truetype(os.path.join(FONT, yol), round(boy * S), layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes(eksen)
    return f


def renk(c, a=1.0):
    return (c[0], c[1], c[2], max(0, min(255, round(255 * a))))


def karistir(c1, c2, t):
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ------------------------------------------------------------------ zaman çizelgesi (animasyon.sablon.html ile aynı)
ADIM = [   # durum metni, başlangıç zamanı, o ana kadarki ilerleme
    ('Arayüz hazırlanıyor…', 0, 0.00),
    ('DirectX 12 aygıtı açılıyor…', 700, 0.12),
    ('Hesap motoru (Python) yükleniyor…', 1300, 0.30),
    ('Kesit kütüphanesi okunuyor…', 2400, 0.62),
    ('Son proje açılıyor…', 3050, 0.84),
    ('Hazır', 3650, 1.00),
]
IZ_BASLA = 250
T_HAZIR = ADIM[-1][1]
KEMER_PAY = 0.86          # ilerlemenin kemer yarılarına ayrılan kısmı; kalanı kilit taşı


def kis(v, a=0.0, b=1.0):
    return min(b, max(a, v))


def aralik(t, a, b):
    return kis((t - a) / (b - a))


def cikis3(u):
    return 1 - (1 - u) ** 3


def yumusak(u):
    return 0.55 * u + 0.45 * (0.5 - 0.5 * math.cos(math.pi * u))


def ilerleme(t):
    if t >= T_HAZIR:
        return 1.0
    for i in range(len(ADIM) - 1):
        a, b = ADIM[i], ADIM[i + 1]
        if t < b[1]:
            t0 = IZ_BASLA if i == 0 else a[1]
            return a[2] + (b[2] - a[2]) * yumusak(aralik(t, t0, b[1]))
    return 1.0


def durum_indeks(t):
    k = 0
    for i, a in enumerate(ADIM):
        if t >= a[1]:
            k = i
    return k


def isik(t):
    """Kilit taşı ışığı: 3820–4060 ms'de yükselir (ease-out), 4060–5100 ms'de kalan değere iner."""
    yukselis = cikis3(aralik(t, 3820, 4060))
    inis = cikis3(aralik(t, 4060, 5100))
    return ISIK_TEPE * yukselis - (ISIK_TEPE - ISIK_KALAN) * inis


def halka(t):
    """Bir kez genişleyen yumuşak halka: yarıçap ve opaklık."""
    u = aralik(t, 3900, 4800)
    r = HALKA_R0 + (HALKA_R1 - HALKA_R0) * cikis3(u)
    a = HALKA_TEPE * min(1.0, u * 6) * (1 - u) ** 1.5
    return r, a


def anlik(t):
    """t (ms) anındaki bütün sahne değerleri."""
    d = {}
    d['t'] = t
    d['p'] = ilerleme(t)
    d['dolgu_kemer'] = cikis3(aralik(t, T_HAZIR, T_HAZIR + 350))
    d['dolgu_kilit'] = cikis3(aralik(t, T_HAZIR + 150, T_HAZIR + 600))
    d['kilit_dy'] = -12 * (1 - d['dolgu_kilit'])
    d['iz_alfa'] = 1 - aralik(t, T_HAZIR + 100, T_HAZIR + 500)
    d['iskele_alfa'] = 1 - cikis3(aralik(t, T_HAZIR + 50, T_HAZIR + 550))
    d['yazi'] = cikis3(aralik(t, T_HAZIR + 500, T_HAZIR + 1000))
    d['kurulus'] = cikis3(aralik(t, 80, 680))
    d['hayalet'] = cikis3(aralik(t, 150, 750))
    d['merkez'] = aralik(t, 500, 800)
    d['isik'] = isik(t)
    d['halka_r'], d['halka_a'] = halka(t)
    d['giris'] = [cikis3(aralik(t, a, b)) for a, b in ((120, 620), (220, 720), (320, 820), (420, 920))]
    di = durum_indeks(t)
    Td = ADIM[di][1]
    d['durum'] = di
    d['durum_eski_a'] = (1 - aralik(t, Td, Td + 110)) if di > 0 else 0.0
    d['durum_yeni_u'] = cikis3(aralik(t, Td + 70, Td + 250)) if di > 0 else 1.0
    d['uc_alfa'] = min(1.0, d['p'] * 25) * (1 - aralik(t, T_HAZIR, T_HAZIR + 220))
    return d


# ------------------------------------------------------------------ yollar
def yol_ekran(noktalar):
    return np.array([simge_xy(x, y) for x, y in noktalar])


def kumulatif(p):
    seg = np.hypot(*np.diff(p, axis=0).T)
    return np.concatenate([[0], np.cumsum(seg)])


def kismi(p, g, t):
    """Yolun g parametresine göre ilk t (0..1) kısmını döndürür."""
    if t <= 0:
        return p[:1]
    if t >= 1:
        return p
    i = int(np.searchsorted(g, t, side='right'))
    u = (t - g[i - 1]) / max(g[i] - g[i - 1], 1e-9)
    son = p[i - 1] + (p[i] - p[i - 1]) * u
    return np.vstack([p[:i], son])


def kesikli(p, acik, kapali, faz=0.0):
    """Yolu kesikli parçalara böler (D2D dash stilinin karşılığı)."""
    c = kumulatif(p)
    parcalar, s, toplam = [], -faz, c[-1]
    while s < toplam:
        a, b = max(s, 0), min(s + acik, toplam)
        if b > a:
            parcalar.append(alt_yol(p, c, a, b))
        s += acik + kapali
    return parcalar


def alt_yol(p, c, a, b):
    def nokta(d):
        i = min(max(int(np.searchsorted(c, d)), 1), len(p) - 1)
        u = (d - c[i - 1]) / max(c[i] - c[i - 1], 1e-9)
        return p[i - 1] + (p[i] - p[i - 1]) * u
    ic = [p[i] for i in range(len(p)) if a < c[i] < b]
    return np.array([nokta(a)] + ic + [nokta(b)])


KALEM = {ad: (yol_ekran(v['p']), np.array(v['g'])) for ad, v in K['kalemler'].items()}
HAYALET = {ad: yol_ekran(v) for ad, v in K['hayalet'].items()}
KEMER_KALEM = ('kemer_sol_dis', 'kemer_sol_ic', 'kemer_sag_dis', 'kemer_sag_ic')
KILIT_KALEM = ('kilit_sol_ust', 'kilit_sag_ust', 'kilit_sol_alt', 'kilit_sag_alt')


# ------------------------------------------------------------------ çizgi katmanı
class Cizgi:
    """Süper örneklemeli çizgi katmanı (yalnız kemer bölgesi)."""

    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = x0, y0
        self.k = S * SS
        self.w, self.h = round((x1 - x0) * self.k), round((y1 - y0) * self.k)
        self.im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def pt(self, x, y):
        return ((x - self.x0) * self.k, (y - self.y0) * self.k)

    def cizgi(self, p, kal, c, yuvarlak=True):
        pts = [self.pt(x, y) for x, y in p]
        g = max(1, round(kal * self.k))
        if len(pts) >= 2:
            self.d.line(pts, fill=c, width=g, joint='curve')
        if yuvarlak:
            r = g / 2
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=c)

    def daire(self, x, y, r, c, kal=None):
        X, Y = self.pt(x, y)
        R = r * self.k
        if kal is None:
            self.d.ellipse((X - R, Y - R, X + R, Y + R), fill=c)
        else:
            self.d.ellipse((X - R, Y - R, X + R, Y + R), outline=c, width=max(1, round(kal * self.k)))

    def sonuc(self):
        return self.im.resize((self.w // SS, self.h // SS), Image.LANCZOS)


def katman_ciz(govde, katman, alfa):
    """Katmanı (alfa çarpanıyla) gövdeye bindirir."""
    if alfa <= 0:
        return
    if alfa < 1:
        a = katman.getchannel('A').point(lambda v: round(v * alfa))
        katman = katman.copy()
        katman.putalpha(a)
    govde.alpha_composite(katman)


def logo_yerlestir(govde, yol, x, y, gen, alfa=1.0, kirp=None):
    """PNG'yi en-boy oranını koruyarak Lanczos ile ölçekler ve yerleştirir.
    x, y, gen mantıksal; kirp = PNG içinde (x0,y0,x1,y1) hizalama kutusu."""
    im = Image.open(yol).convert('RGBA')
    kx0, ky0, kx1, ky1 = kirp or (0, 0, im.width, im.height)
    o = gen * S / (kx1 - kx0)
    yeni = im.resize((round(im.width * o), round(im.height * o)), Image.LANCZOS)
    hedef = Image.new('RGBA', govde.size, (0, 0, 0, 0))
    hedef.paste(yeni, (round(x * S - kx0 * o), round(y * S - ky0 * o)))
    katman_ciz(govde, hedef, alfa)


def radyal_katman(govde, cx, cy, R, profil, c, rx=1.0, ry=1.0):
    """Altın radyal ışık katmanı: alfa = profil(r/R). (D2D: ID2D1RadialGradientBrush)"""
    x0, x1 = max(0, int((cx - R * rx) * S) - 2), min(W * S, int((cx + R * rx) * S) + 3)
    y0, y1 = max(0, int((cy - R * ry) * S) - 2), min(H * S, int((cy + R * ry) * S) + 3)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    r = np.hypot((xx / S - cx) / rx, (yy / S - cy) / ry) / R
    a = np.clip(profil(np.clip(r, 0, 1)), 0, 1)
    kat = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    kat[..., 0], kat[..., 1], kat[..., 2] = c
    kat[..., 3] = np.round(a * 255).astype(np.uint8)
    tam = Image.new('RGBA', govde.size, (0, 0, 0, 0))
    tam.paste(Image.fromarray(kat, 'RGBA'), (x0, y0))
    govde.alpha_composite(tam)


# ------------------------------------------------------------------ metin
def metin(govde, xy, s, f, c, cap='ls', izleme=0.0, ozellik=None):
    """Metni kapsama maskesi olarak çizer, sonra renk+opaklıkla bindirir
    (ImageDraw'ın RGBA üzerinde alfayı değiştirmesini önler)."""
    if c[3] <= 0:
        return 0
    x, y = xy[0] * S, xy[1] * S
    maske = Image.new('L', govde.size, 0)
    md = ImageDraw.Draw(maske)
    if izleme == 0:
        md.text((x, y), s, font=f, fill=255, anchor=cap, features=ozellik)
        gen = f.getlength(s, features=ozellik) / S
    else:  # harf aralığı (tracking): harf harf
        toplam = sum(f.getlength(ch) for ch in s) + izleme * S * (len(s) - 1)
        if cap[0] == 'r':
            x -= toplam
        elif cap[0] == 'm':
            x -= toplam / 2
        for ch in s:
            md.text((x, y), ch, font=f, fill=255, anchor='l' + cap[1])
            x += f.getlength(ch) + izleme * S
        gen = toplam / S
    if c[3] < 255:
        maske = maske.point(lambda v: round(v * c[3] / 255))
    katman = Image.new('RGBA', govde.size, (c[0], c[1], c[2], 0))
    katman.putalpha(maske)
    govde.alpha_composite(katman)
    return gen


# ------------------------------------------------------------------ sahne
def zemin_yap():
    """Açık kâğıt zemini: Krem'den türetilmiş sıcak ton, kemerin arkasında hafif aydınlanma,
    köşelere doğru hafif vinyet; bantlaşmaya karşı ±0,5 LSB titreşim."""
    yy, xx = np.mgrid[0:H * S, 0:W * S].astype(np.float32)
    r = np.hypot(xx - KEMER_CX * S, (yy - (KEMER_UST + KEMER_YUK * 0.48) * S) * 1.15) / (380 * S)
    t = np.clip(1 - r, 0, 1) ** 2
    d = np.hypot((xx / S - W / 2) / (W / 2 + 80), (yy / S - H / 2) / (H / 2 + 90))
    v = np.clip((d - 0.5) / 0.9, 0, 1) ** 1.5
    zemin = np.zeros((H * S, W * S, 4), np.float32)
    for i in range(3):   # iki radyal fırça üst üste: önce merkez aydınlanması, sonra vinyet (canvas/D2D ile aynı sıra)
        zemin[..., i] = (KAGIT[i] + (KAGIT_MERKEZ[i] - KAGIT[i]) * t) * (1 - v) + KAGIT_KENAR[i] * v
    zemin[..., 3] = 255
    rng = np.random.default_rng(7)
    zemin[..., :3] += rng.uniform(-0.5, 0.5, (H * S, W * S, 1))
    return Image.fromarray(np.clip(np.round(zemin), 0, 255).astype(np.uint8), 'RGBA')


def sahne(t, **ustune):
    """t (ms) anının karesi. ustune: anlik(t) değerlerinin üzerine yazılacak değerler."""
    A = anlik(t)
    A.update(ustune)
    p = A['p']
    dolgu_kemer, dolgu_kilit, kilit_dy = A['dolgu_kemer'], A['dolgu_kilit'], A['kilit_dy']
    iz_alfa, iskele_alfa, yazi = A['iz_alfa'], A['iskele_alfa'], A['yazi']
    kurulus, hayalet_a = A['kurulus'], A['hayalet']

    # 1) zemin
    govde = zemin_yap()

    # 1b) kilit taşı ışığı ve halkası (logonun ARKASINDA; D2D'de radyal degrade fırça)
    if A['isik'] > 0:
        tepe = A['isik']
        radyal_katman(govde, KILIT_MERKEZ[0], KILIT_MERKEZ[1], ISIK_R,
                      lambda r: tepe * (0.5 + 0.5 * np.cos(np.pi * r)), ALTIN)
    if A['halka_a'] > 0:
        hr, ha = A['halka_r'], A['halka_a']
        R = hr + HALKA_GEN
        radyal_katman(govde, KILIT_MERKEZ[0], KILIT_MERKEZ[1], R,
                      lambda r: ha * (0.5 + 0.5 * np.cos(np.pi * np.clip(np.abs(r * R - hr) / HALKA_GEN, 0, 1))) ** 2, ALTIN)

    # 2) kemer bölgesi çizgi katmanı
    cx0, cy0, cx1, cy1 = KEMER_SOL - 70, KEMER_UST - 40, KEMER_SAG + 70, KEMER_ALT + 30
    cz = Cizgi(cx0, cy0, cx1, cy1)

    # 2a) iskele (yapı çizgileri): eksen, üzengi çizgisi, zemin çizgisi, merkez işareti
    ia = iskele_alfa
    if ia > 0:
        g = renk(ANTRASIT, 0.22 * ia)
        g2 = renk(ANTRASIT, 0.15 * ia)
        k = kurulus
        # eksen (nokta-çizgi; teknik resimde simetri ekseni)
        ex_ust, ex_alt = KEMER_UST - 26, KEMER_ALT + 18
        eks = np.array([[KEMER_CX, ex_ust], [KEMER_CX, ex_ust + (ex_alt - ex_ust) * k]])
        if k > 0:
            for parca in kesikli(eks, 14, 3 + 1.5 + 3):
                cz.cizgi(parca, 0.75, g, yuvarlak=False)
            c = kumulatif(eks)[-1]
            s_ = 14 + 3
            while s_ < c:
                cz.daire(KEMER_CX, ex_ust + s_ + 0.75, 0.55, g)
                s_ += 14 + 3 + 1.5 + 3
        # üzengi çizgisi (yayların başladığı yatay)
        yar = (KEMER_SAG - KEMER_SOL) / 2 + 30
        cz.cizgi(np.array([[KEMER_CX - yar * k, UZENGI_Y], [KEMER_CX + yar * k, UZENGI_Y]]), 0.75, g2, False)
        # zemin çizgisi + tarama
        yz = (KEMER_SAG - KEMER_SOL) / 2 + 46
        cz.cizgi(np.array([[KEMER_CX - yz * k, KEMER_ALT], [KEMER_CX + yz * k, KEMER_ALT]]), 0.75, g, False)
        x = KEMER_CX - yz * k + 3
        while x < KEMER_CX + yz * k - 6:
            cz.cizgi(np.array([[x + 5, KEMER_ALT + 0.5], [x, KEMER_ALT + 5.5]]), 0.6, renk(ANTRASIT, 0.10 * ia), False)
            x += 6
        # yay merkezi işareti
        if A['merkez'] > 0:
            cz.daire(KEMER_CX, UZENGI_Y, 3.2, renk(ANTRASIT, 0.30 * ia * A['merkez']), kal=0.75)

    # 2b) hayalet kontur: kesikli gizli çizgi
    if ia > 0 and hayalet_a > 0:
        for p_ in HAYALET.values():
            for parca in kesikli(p_, 3.5, 3.0):
                cz.cizgi(parca, 0.75, renk(ANTRASIT, 0.20 * ia * hayalet_a), yuvarlak=False)

    # 2c) altın iz: dört kalem ayaklardan tepeye, sonra kilit taşı
    t_kemer = min(p / KEMER_PAY, 1.0)
    t_kilit = max(0.0, min((p - KEMER_PAY) / (1 - KEMER_PAY), 1.0))
    # tamamlanan adımlar: kalemler arasında derz çizgisi (bacakta yatay, yayda radyal)
    if iz_alfa > 0:
        for i in range(1, len(ADIM) - 1):
            te = min(ADIM[i][2] / KEMER_PAY, 1.0)
            da = aralik(t, ADIM[i][1], ADIM[i][1] + 220)
            if te < 1 and da > 0:
                for a_, b_ in (('kemer_sol_dis', 'kemer_sol_ic'), ('kemer_sag_dis', 'kemer_sag_ic')):
                    p1 = kismi(*KALEM[a_], te)[-1]
                    p2 = kismi(*KALEM[b_], te)[-1]
                    cz.cizgi(np.array([p1, p2]), 0.75, renk(ALTIN, 0.55 * iz_alfa * da), yuvarlak=False)
    uclar = []
    if iz_alfa > 0:
        c = renk(ALTIN, iz_alfa)
        for ad in KEMER_KALEM:
            q = kismi(*KALEM[ad], t_kemer)
            if t_kemer > 0:
                cz.cizgi(q, IZ_KALINLIK, c)
            if t_kemer < 1:
                uclar.append(q[-1])
        if t_kemer >= 1:
            for ad in KILIT_KALEM:
                q = kismi(*KALEM[ad], t_kilit)
                if t_kilit > 0:
                    cz.cizgi(q, IZ_KALINLIK, c)
                if t_kilit < 1:
                    uclar.append(q[-1])
    # 2d) kilit taşı kenarı: taşın kâğıda değen üst ve alt kenarında kalıcı ince altın çizgi
    # (kilit taşı kalemlerinin yolları; taşla birlikte iner)
    if dolgu_kilit > 0:
        ck = renk(ALTIN, KENAR_ALFA * dolgu_kilit)
        for ad in KILIT_KALEM:
            cz.cizgi(KALEM[ad][0] + np.array([0, kilit_dy]), KENAR_KALINLIK, ck)
    # kalem uçları: küçük kahve nokta (hale ayrıca)
    uc_a = iz_alfa * hayalet_a
    for x, y in uclar:
        cz.daire(x, y, 1.6, renk(KAHVE, uc_a))
    cizgi_im = cz.sonuc()

    # hale (uçlarda yumuşak altın leke; D2D radyal fırça r = 13: %22 → %10 → %0)
    if uclar and uc_a > 0:
        par = Image.new('RGBA', govde.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(par)
        for x, y in uclar:
            R = 8 * S
            pd.ellipse((x * S - R, y * S - R, x * S + R, y * S + R), fill=renk(ALTIN, 0.24 * uc_a))
        par = par.filter(ImageFilter.GaussianBlur(4.0 * S))
        govde.alpha_composite(par)

    # 3) dolgu: renk maskesiyle ayrılmış kemer ve kilit taşı katmanları
    gen = (BX1 - BX0) * OLCEK
    kemer_k = os.path.join(KOK, 'katmanlar', 'kemer.png')
    kilit_k = os.path.join(KOK, 'katmanlar', 'kilit.png')
    if dolgu_kemer >= 1 and dolgu_kilit >= 1 and abs(kilit_dy) < 1e-6:
        # tam hâl: resmî PNG'nin kendisi
        logo_yerlestir(govde, os.path.join(KIMLIK, 'opus-fortis-simge-renkli.png'),
                       KEMER_SOL, KEMER_UST, gen, 1.0, kirp=(BX0, BY0, BX1, BY1))
    else:
        if dolgu_kemer > 0:
            logo_yerlestir(govde, kemer_k, KEMER_SOL, KEMER_UST, gen, dolgu_kemer, kirp=(BX0, BY0, BX1, BY1))
        if dolgu_kilit > 0:
            logo_yerlestir(govde, kilit_k, KEMER_SOL, KEMER_UST + kilit_dy, gen, dolgu_kilit, kirp=(BX0, BY0, BX1, BY1))

    # çizgileri dolgunun üstüne bindir (iz dolgu gelirken söner, kilit kenarı kalır)
    tam = Image.new('RGBA', govde.size, (0, 0, 0, 0))
    tam.paste(cizgi_im, (round(cx0 * S), round(cy0 * S)))
    govde.alpha_composite(tam)

    # 4) kurum yazısı (kemerin altında): açık zemin sürümü
    if yazi > 0:
        yk = os.path.join(KIMLIK, 'opus-fortis-yazi-acik-zemin.png')
        yg = 232          # yazı genişliği (mantıksal)
        # hizalama: harflerin alt çizgisi (PNG y=285) ve yatay içerik (98..1902)
        o = yg / (1902 - 98)
        ust = KEMER_ALT + 50 - (285 - 86) * o + 8 * (1 - yazi)
        logo_yerlestir(govde, yk, KEMER_CX - yg / 2, ust, yg, yazi, kirp=(98, 86, 1902, 285))

    # 5) sağ sütun: ürün adı, alt başlık, durum, sürüm
    d = govde
    f_urun = font('inter', 92, [32, 300])
    f_alt = font('cormorant', 25, [500])
    f_durum = font('inter', 12.5, [14, 400])
    f_yuzde = font('inter', 12.5, [14, 500])
    f_kucuk = font('inter', 11, [14, 400])
    g1, g2, g3, g4 = A['giris']

    taban = 236                                      # op4 taban çizgisi
    metin(d, (SAG_X - 4, taban + 6 * (1 - g1)), 'op4', f_urun, renk(ANTRASIT, g1))
    metin(d, (SAG_X, taban + 46 + 6 * (1 - g2)), 'Yapı analizi ve tasarımı', f_alt, renk(ANTRASIT, 0.80 * g2))

    # durum satırı (değişince çapraz geçiş) + yüzde
    dy = 352 + 6 * (1 - g3)
    di = A['durum']
    son_adim = len(ADIM) - 1

    def durum_renk(i, al):
        return renk(ANTRASIT, (0.92 if i == son_adim else 0.62) * al)
    if di > 0 and A['durum_eski_a'] > 0:
        metin(d, (SAG_X, dy), ADIM[di - 1][0], f_durum, durum_renk(di - 1, g3 * A['durum_eski_a']))
    yu = A['durum_yeni_u']
    metin(d, (SAG_X, dy + 4 * (1 - yu)), ADIM[di][0], f_durum, durum_renk(di, g3 * yu))
    metin(d, (SAG_SON, dy), f'%{round(p * 100)}', f_yuzde, renk(ALTIN, g3), cap='rs')

    # ilerleme çizgisi ("Gece" biçimi): 1 px iz, Altın dolgu, açık uç, hareket ederken parıltı
    oy = dy + 16
    x0, x1 = SAG_X, SAG_SON
    kat = Image.new('RGBA', govde.size, (0, 0, 0, 0))
    kd = ImageDraw.Draw(kat)
    kd.rectangle([x0 * S, oy * S, x1 * S - 1, oy * S + S - 1], fill=renk(ANTRASIT, 0.12 * g3))
    if p > 0:
        ux = x0 + (x1 - x0) * p
        kd.rectangle([x0 * S, oy * S, ux * S - 1, oy * S + S - 1], fill=renk(ALTIN, g3))
        ua = A['uc_alfa'] * g3
        if ua > 0:
            bas = 48 * S
            for i in range(int(bas)):
                tt = ((i + 1) / bas) ** 2 * ua
                x = ux * S - bas + i
                if x >= x0 * S:
                    kd.line([(x, oy * S), (x, oy * S + S - 1)], fill=karistir(ALTIN, UC, tt) + (255,))
    govde.alpha_composite(kat)
    if p > 0 and A['uc_alfa'] * g3 > 0:
        # parıltı: ucun gerisinde 12×2,5 px, 1,5 px bulanık açık altın (UC) leke
        par = Image.new('RGBA', govde.size, (0, 0, 0, 0))
        ux = x0 + (x1 - x0) * p
        ImageDraw.Draw(par).rectangle([max(x0 * S, ux * S - 12 * S), oy * S - 0.75 * S, ux * S, oy * S + S * 1.75],
                                      fill=renk(UC, 0.45 * A['uc_alfa'] * g3))
        govde.alpha_composite(par.filter(ImageFilter.GaussianBlur(1.5 * S)))

    # alt bilgi
    metin(d, (SAG_X, 500 + 6 * (1 - g4)), 'Sürüm 0.1.0', f_kucuk, renk(ANTRASIT, 0.55 * g4))
    metin(d, (SAG_SON, 500 + 6 * (1 - g4)), '© 2026 Opus Fortis', f_kucuk, renk(ANTRASIT, 0.45 * g4), cap='rs')

    # pencere: 8 px yuvarlak köşe + 1 px iç kenar (Antrasit %8)
    maske = Image.new('L', govde.size, 0)
    ImageDraw.Draw(maske).rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=8 * S, fill=255)
    kenar = Image.new('RGBA', govde.size, (0, 0, 0, 0))
    ImageDraw.Draw(kenar).rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=8 * S,
                                            outline=ANTRASIT + (20,), width=S)
    govde.alpha_composite(kenar)
    govde.putalpha(ImageChops.multiply(govde.getchannel('A'), maske))
    return govde


def kaydet(im, ad):
    im.save(os.path.join(KOK, ad + '.png'), optimize=True)
    im.resize((W, H), Image.LANCZOS).save(os.path.join(KOK, ad + '-960x540.png'), optimize=True)


def t_yuzde(hedef):
    """ilerleme(t) = hedef olan t'yi bulur (ikiye bölme)."""
    a, b = IZ_BASLA, T_HAZIR
    for _ in range(60):
        m = (a + b) / 2
        if ilerleme(m) < hedef:
            a = m
        else:
            b = m
    return round((a + b) / 2)


T_KARE_50 = t_yuzde(0.5)
T_OTURMA = 4050
T_SON = 4650

if __name__ == '__main__':
    # %0: giriş geçişleri bitmiş, kalemler henüz yola çıkmamış (gerçek t = 250 ms'de giriş sürer)
    kaydet(sahne(IZ_BASLA, kurulus=1.0, hayalet=1.0, merkez=1.0, giris=[1, 1, 1, 1]), 'kare-0')
    kaydet(sahne(T_KARE_50), 'kare-50')
    kaydet(sahne(T_OTURMA), 'kare-oturma')
    kaydet(sahne(T_SON), 'kare-100')
    print('tamam; kare-50 t =', T_KARE_50, 'ms')
