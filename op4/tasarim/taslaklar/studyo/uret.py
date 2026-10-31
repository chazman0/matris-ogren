# -*- coding: utf-8 -*-
"""uret.py — op4 arayüz yönü C "Stüdyo": yüksek sadakatli maket görselleri.

python3 uret.py   → ana.png, ana-2x.png, kucuk.png, detay-serit.png, detay-panel.png,
                     secsuz.png, sonuc.png, kat-kapsami.png (bu klasöre)
"""
import os
import sys
from PIL import Image

KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KOK)
from tuval import Tuval, R, DC_RENK, hexrgb, karistir, alfa, KIMLIK  # noqa: E402
from sahne import Bina, Sahne  # noqa: E402

LOGO_SIMGE = Image.open(os.path.join(KIMLIK, 'opus-fortis-simge-koyu.png')).convert('RGBA')
LOGO_YAZI = Image.open(os.path.join(KIMLIK, 'opus-fortis-yazi-acik-zemin.png')).convert('RGBA')

PROJE = 'Depo Binası – Tokat OSB'
SEKMELER = ['Model', 'Düzenle', 'Yükler', 'Analiz', 'Tasarım', 'Görünüm', 'Raporlar']


# ================================================================ yerleşim
def yerlesim(W, H, kompakt=False):
    L = dict(W=W, H=H, kompakt=kompakt)
    L['baslik_h'] = 36 if kompakt else 40
    L['sekme_h'] = 30 if kompakt else 32
    L['grup_h'] = 74 if kompakt else 84
    L['serit_y1'] = L['baslik_h'] + L['sekme_h'] + L['grup_h']
    L['kenar'] = 12 if kompakt else 16
    L['durum_h'] = 26
    L['komut_h'] = 30
    L['govde_y0'] = L['serit_y1'] + L['kenar']
    L['govde_y1'] = H - L['durum_h'] - L['kenar']
    L['sol_w'] = 0 if kompakt else 300
    L['sag_w'] = 300 if kompakt else 340
    k = L['kenar']
    L['sol_x'] = k
    L['vp_x0'] = k + (L['sol_w'] + k if L['sol_w'] else 0)
    L['vp_x1'] = W - k - L['sag_w'] - k
    L['sag_x'] = W - k - L['sag_w']
    L['vp_y0'] = L['govde_y0']
    L['vp_y1'] = L['govde_y1']
    return L


# ================================================================ bileşenler
def kart(t, x, y, w, h, r=8, golge=(10, 4, 0.10)):
    t.yuv(x, y, w, h, r, fill=R['yuzey'], golge=golge)
    t.yuv(x, y, w, h, r, outline=alfa(R['antrasit'], 0.06))


def birincil(t, x, y, w, h, etiket, ikon=None, kisayol=None):
    """Tek gradyanlı düğme: Kahve → Altın (yalnız birincil eylem)."""
    t.golge(x, y, w, h, 6, 6, 2, 0.16, renk=R['kahve_koyu'])
    tmp = Tuval(w, h, t.S, R['kahve'])
    tmp.gradyan(0, 0, w, h, R['kahve'], R['altin'], dikey=False)
    m = t._rr_mask(t.p(w), t.p(h), t.p(6), 4)
    t.im.paste(tmp.im, (t.p(x), t.p(y)), m)
    cx = x + 12
    if ikon:
        t.ikon(ikon, cx, y + (h - 16) / 2, 16, (255, 255, 255))
        cx += 22
    t.yazi(cx, y + h / 2 + 4.5, etiket, 13, 600, (255, 255, 255))
    if kisayol:
        t.yazi_sag(x + w - 12, y + h / 2 + 4.5, kisayol, 11, 500, alfa((255, 255, 255), 0.75))


def dugme(t, x, y, w, h, etiket=None, ikon=None, stil='ikincil', boy=12, aktif=False):
    if stil == 'ikincil':
        t.yuv(x, y, w, h, 6, fill=R['yuzey'], outline=R['cizgi2'])
    elif stil == 'sade':
        if aktif:
            t.yuv(x, y, w, h, 6, fill=R['altin_dolgu'], outline=alfa(R['altin'], 0.7))
    elif stil == 'tonlu':
        t.yuv(x, y, w, h, 6, fill=R['altin_dolgu'])
    cx = x + 10
    renk = R['metin'] if (aktif or stil != 'sade') else R['metin2']
    if ikon and etiket:
        t.ikon(ikon, cx, y + (h - 16) / 2, 16, renk)
        cx += 22
        t.yazi(cx, y + h / 2 + boy * 0.36, etiket, boy, 500, renk)
    elif ikon:
        t.ikon(ikon, x + (w - 16) / 2, y + (h - 16) / 2, 16, renk)
    else:
        t.yazi_orta(x + w / 2, y + h / 2 + boy * 0.36, etiket, boy, 500, renk)


def alan(t, x, y, w, h, deger, acilir=False, katalog=False, boy=12, renk=None, ikon=None):
    """Giriş alanı; acilir → ▾, katalog → yanında '…' katalog düğmesi."""
    aw = w - (26 if katalog else 0)
    t.yuv(x, y, aw, h, 5, fill=R['yuzey2'], outline=R['cizgi'])
    cx = x + 8
    if ikon:
        t.ikon(ikon, cx, y + (h - 14) / 2, 14, R['metin2'])
        cx += 18
    t.yazi(cx, y + h / 2 + boy * 0.36, deger, boy, 450, renk or R['metin'], maxw=aw - 26)
    if acilir:
        t.ikon('asagi', x + aw - 20, y + (h - 14) / 2, 14, R['metin3'])
    if katalog:
        bx = x + aw + 4
        t.yuv(bx, y, 22, h, 5, fill=R['yuzey'], outline=R['cizgi2'])
        t.ikon('nokta3', bx + 3, y + (h - 16) / 2, 16, R['metin2'])


def onay_kutusu(t, x, y, etiket, secili=True, boy=12):
    if secili:
        t.yuv(x, y, 14, 14, 3, fill=R['kahve'])
        t.ikon('onay', x - 1, y - 1, 16, (255, 255, 255), 1.8)
    else:
        t.yuv(x, y, 14, 14, 3, fill=R['yuzey'], outline=R['cizgi2'])
    t.yazi(x + 20, y + 11.5, etiket, boy, 450, R['metin'])


def anahtar(t, x, y, acik=True):
    if acik:
        t.yuv(x, y, 30, 16, 8, fill=R['altin'])
        t.daire(x + 22, y + 8, 5.5, fill=(255, 255, 255))
    else:
        t.yuv(x, y, 30, 16, 8, fill=R['cizgi2'])
        t.daire(x + 8, y + 8, 5.5, fill=(255, 255, 255))


def parcali(t, x, y, h, secenekler, aktif, boy=11.5, pad=10, ikonlar=None, konum=None):
    """Parçalı anahtar; aktif parça altın dolgulu. Toplam genişliği döndürür."""
    if konum is None:
        konum = []
    ws = []
    for i, s in enumerate(secenekler):
        w = (t.gen(s, boy, 500) if s else 0) + pad * 2 + (18 if ikonlar and ikonlar[i] else 0)
        ws.append(w)
    W = sum(ws) + 4
    t.yuv(x, y, W, h, h / 2, fill=R['yuzey3'])
    cx = x + 2
    for i, s in enumerate(secenekler):
        if i == aktif:
            t.yuv(cx, y + 2, ws[i], h - 4, (h - 4) / 2, fill=R['yuzey'], outline=alfa(R['altin'], 0.9))
            t.yuv(cx, y + 2, ws[i], h - 4, (h - 4) / 2, fill=alfa(R['altin'], 0.14))
        tx = cx + pad
        renk = R['metin'] if i == aktif else R['metin2']
        if ikonlar and ikonlar[i]:
            t.ikon(ikonlar[i], tx - 2, y + (h - 14) / 2, 14, renk)
            tx += 18
        if s:
            t.yazi(tx, y + h / 2 + boy * 0.36, s, boy, 600 if i == aktif else 500, renk)
        konum.append((cx, ws[i]))
        cx += ws[i]
    return W


def parcali_konum(t, x, y, h, secenekler, aktif, boy=11.5, pad=10, ikonlar=None):
    return parcali(t, x, y, h, secenekler, aktif, boy, pad, ikonlar, konum=[])


def etiket_pul(t, x, y, s, boy=10.5, renk=None, zemin=None, h=18):
    w = t.gen(s, boy, 600) + 14
    t.yuv(x, y, w, h, h / 2, fill=zemin or R['altin_dolgu'])
    t.yazi(x + 7, y + h / 2 + boy * 0.36, s, boy, 600, renk or R['kahve_koyu'])
    return w


def ipucu(t, x, y, s, boy=11, yon='sag'):
    """Koyu ipucu balonu; x,y hedef noktası (ok ucu)."""
    w = t.gen(s, boy, 500) + 16
    h = 22
    if yon == 'sag':
        bx, by = x + 8, y - h / 2
        t.yuv(bx, by, w, h, 5, fill=R['antrasit'], golge=(5, 2, 0.18))
        t.d.polygon([(t.p(x + 1), t.p(y)), (t.p(bx + 0.5), t.p(y - 4)), (t.p(bx + 0.5), t.p(y + 4))], fill=R['antrasit'])
    else:  # üst
        bx, by = x - w / 2, y - h - 7
        t.yuv(bx, by, w, h, 5, fill=R['antrasit'], golge=(5, 2, 0.18))
        t.d.polygon([(t.p(x), t.p(y - 1)), (t.p(x - 4), t.p(by + h - 0.5)), (t.p(x + 4), t.p(by + h - 0.5))], fill=R['antrasit'])
    t.yazi(bx + 8, by + h / 2 + boy * 0.36, s, boy, 500, R['krem'])


# ================================================================ üst çerçeve
def ciz_baslik(t, L, degisti=True):
    W, h = L['W'], L['baslik_h']
    t.dikd(0, 0, W, h, fill=R['yuzey'])
    k = L['kenar']
    lw, lh = t.resim(LOGO_SIMGE, k, (h - 20) / 2, h=20)
    x = k + lw + 10
    t.yazi(x, h / 2 + 5, 'op4', 15, 600, R['metin'])
    x += t.gen('op4', 15, 600) + 12
    t.dusey(x, h / 2 - 8, h / 2 + 8, R['cizgi2'])
    x += 12
    t.yazi(x, h / 2 + 6, PROJE, 19, 600, R['metin'], aile='cormorant')
    x += t.gen(PROJE, 19, 600, 'cormorant') + 8
    if degisti:
        t.daire(x + 4, h / 2 - 1, 3, fill=R['altin'])
        x += 14
    t.yazi(x, h / 2 + 4.5, 'depo-binasi-tokat.op4', 11, 400, R['metin3'])
    # sağ: yardım, pencere denetimleri
    cx = W - 46 * 3
    for i, ad in enumerate(('kucult', 'buyut', 'kapat')):
        t.ikon(ad, cx + i * 46 + 15, (h - 16) / 2, 16, R['metin2'], 1.2)
    t.ikon('yardim', cx - 40, (h - 16) / 2, 16, R['metin2'])
    t.yazi_sag(cx - 52, h / 2 + 4.5, 'Opus Fortis · lisans: ofis', 11, 400, R['metin3'])


def ciz_sekmeler(t, L, aktif):
    y0, h = L['baslik_h'], L['sekme_h']
    W = L['W']
    t.dikd(0, y0, W, h, fill=R['yuzey'])
    k = L['kenar']
    # Dosya (arka plan menüsü) — kahve pil
    x = k
    dw = t.gen('Dosya', 13, 600) + 40
    t.yuv(x, y0 + 5, dw, h - 10, 5, fill=R['kahve'])
    t.yazi(x + 10, y0 + h / 2 + 4.5, 'Dosya', 13, 600, R['krem'])
    t.ikon('asagi', x + dw - 20, y0 + (h - 14) / 2, 14, R['krem'])
    x += dw + 14
    for s in SEKMELER:
        w = t.gen(s, 13, 600) + 20
        if s == aktif:
            t.yazi(x + 10, y0 + h / 2 + 4.5, s, 13, 600, R['metin'])
            t.yuv(x + 8, y0 + h - 3, w - 16, 2.5, 1.2, fill=R['altin'])
        else:
            t.yazi(x + 10, y0 + h / 2 + 4.5, s, 13, 500, R['metin2'])
        x += w
    # sağ: şerit özelleştirme (göz: sekme gizle, sürükle-sırala), daralt
    rx = W - k - 16
    t.ikon('yukari', rx, y0 + (h - 14) / 2, 14, R['metin3'])
    rx -= 26
    t.ikon('disli', rx, y0 + (h - 14) / 2, 14, R['metin3'])
    rx -= 26
    t.ikon('goz', rx, y0 + (h - 14) / 2, 14, R['metin3'])
    t.yazi_sag(rx - 8, y0 + h / 2 + 4, 'Şeridi özelleştir', 11, 400, R['metin3'])


GRUPLAR_MODEL = [
    ('Aks & Kat', [('b', 'aks', 'Aks sistemi'), ('b', 'kat', 'Katlar')]),
    ('Kolon', [('b', 'kolon', 'Kolon')]),
    ('Kiriş', [('b', 'kiris', 'Kiriş', 'aktif'), ('k', [('ikincil', 'İkincil kiriş'), ('asik', 'Aşık'), ('konsol', 'Konsol')])]),
    ('Çapraz', [('b', 'capraz', 'Çapraz')]),
    ('Döşeme', [('b', 'doseme', 'Döşeme')]),
    ('Duvar', [('b', 'duvar', 'Duvar')]),
    ('Temel', [('b', 'temel', 'Temel')]),
    ('Hızlı kolon/kiriş', [('b', 'hizli_kolon', 'Hızlı kolon'), ('b', 'hizli_kiris', 'Hızlı kiriş')]),
    ('Seç', [('b', 'sec', 'Seç'), ('k', [('suzgec', 'Seç & Süz…'), ('benzer', 'Benzerini seç'), ('ters', 'Tersine çevir')])]),
]
GRUPLAR_TASARIM = [
    ('Yönetmelik', [('b', 'yonetmelik', 'Yönetmelik'), ('k', [('disli', 'Tercihler'), ('kat', 'Kombinasyonlar'), ('tablo', 'Otomatik liste')])]),
    ('Tasarım', [('b', 'celik', 'Çelik tasarım'), ('b', 'beton', 'Betonarme'), ('b', 'kompozit', 'Kompozit')]),
    ('Göster', [('b', 'dc', 'D/C renkleri', 'aktif'), ('b', 'deform', 'Şekil değiştirme'), ('b', 'diyagram', 'N / V / M'), ('b', 'reaksiyon', 'Reaksiyonlar')]),
    ('Tablolar', [('b', 'tablo', 'Tablolar'), ('k', [('kaydet', 'Tablo kümesi'), ('disa', "CSV'ye aktar"), ('kalem', 'Etkileşimli düzenle')])]),
    ('Rapor', [('b', 'rapor', 'Rapor'), ('k', [('yonetmelik', 'Şablon'), ('disa', 'PDF'), ('kopyala', 'Pano')])]),
]


def ciz_gruplar(t, L, gruplar, yuk_deseni=True):
    y0 = L['baslik_h'] + L['sekme_h']
    h = L['grup_h']
    W = L['W']
    t.dikd(0, y0, W, h, fill=R['yuzey'])
    kompakt = L['kompakt']
    k = L['kenar']
    x = k
    by = y0 + 6
    bh = h - 26
    for ad, ogeler in gruplar:
        gx = x
        for og in ogeler:
            if og[0] == 'b':
                aktif = len(og) > 3
                bw = max(58, t.gen(og[2], 11, 500) + 14)
                if aktif:
                    t.yuv(x, by, bw, bh, 6, fill=R['altin_dolgu'], outline=alfa(R['altin'], 0.8))
                t.ikon(og[1], x + (bw - 24) / 2, by + 7, 24, R['metin'] if aktif else R['metin2'])
                t.yazi_orta(x + bw / 2, by + bh - 9, og[2], 11, 500 if not aktif else 600, R['metin'] if aktif else R['metin2'])
                x += bw + 2
            else:
                if kompakt:
                    # dar ekranda küçük yığın yalnız ikon
                    for i, (ik, et) in enumerate(og[1]):
                        t.ikon(ik, x + 4, by + i * 19 + 2, 16, R['metin2'])
                    x += 26
                else:
                    mw = max(t.gen(et, 11, 500) for _, et in og[1]) + 30
                    for i, (ik, et) in enumerate(og[1]):
                        yy = by + i * 19
                        t.ikon(ik, x + 4, yy + 1, 16, R['metin2'])
                        t.yazi(x + 26, yy + 13, et, 11, 500, R['metin2'])
                    x += mw
        x += 6
        t.yazi_orta((gx + x) / 2, y0 + h - 8, ad, 10.5, 500, R['metin3'])
        t.dusey(x + 4, y0 + 10, y0 + h - 10, R['cizgi'])
        x += 14
    # sağ uç: geçerli yük deseni + birincil Çöz
    rx = W - k
    bw = 96 if not kompakt else 88
    birincil(t, rx - bw, y0 + h / 2 - 16, bw, 32, 'Çöz', 'coz', 'F5')
    rx -= bw + 12
    if yuk_deseni and not kompakt:
        aw = 176
        t.yazi_sag(rx, y0 + h / 2 - 10, 'Geçerli yük deseni', 10.5, 500, R['metin3'])
        alan(t, rx - aw, y0 + h / 2 - 4, aw, 24, 'G — Ölü yük (öz ağırlık ×1)', acilir=True, boy=11.5)
    # şerit alt sınırı + yumuşak gölge
    t.yatay(0, W, y0 + h - 1, R['cizgi'])
    for i in range(6):
        t.yatay(0, W, y0 + h + i, alfa(R['antrasit'], 0.025 * (1 - i / 6.0)))


# ================================================================ model ağacı
def ciz_agac(t, L, secili_isimler=('K2-01', 'K2-02', 'K2-03', 'K2-04', 'K2-05', 'K2-06')):
    x, y, w, h = L['sol_x'], L['govde_y0'], L['sol_w'], L['govde_y1'] - L['govde_y0']
    kart(t, x, y, w, h)
    # sekmeler
    tx = x + 12
    ty = y + 12
    for i, s in enumerate(('Model', 'Göster', 'Tablolar', 'Raporlar')):
        tw = t.gen(s, 12, 600) + 16
        if i == 0:
            t.yazi(tx + 8, ty + 15, s, 12, 600, R['metin'])
            t.yuv(tx + 6, ty + 22, tw - 12, 2.5, 1.2, fill=R['altin'])
        else:
            t.yazi(tx + 8, ty + 15, s, 12, 500, R['metin2'])
        tx += tw
    t.yatay(x, x + w, y + 40, R['cizgi'])
    alan(t, x + 12, y + 50, w - 24, 26, 'Ağaçta ara… (ad, etiket: K12, B3)', ikon='ara', boy=11.5, renk=R['metin3'])

    satirlar = [
        (0, 'asagi', 'rapor', PROJE, None, None),
        (1, 'asagi', 'kat', 'Katlar', '4', None),
        (2, 'sag', 'kat', 'Kat 3', '+13,50', 'benzer → Kat 2'),
        (2, 'asagi', 'kat', 'Kat 2', '+9,00', 'ana kat'),
        (3, 'sag', 'kolon', 'Kolonlar', '20', None),
        (3, 'asagi', 'kiris', 'Kirişler', '24', None),
        (4, None, None, 'K2-01', 'IPE400 · A/1–B/1', 'sec'),
        (4, None, None, 'K2-02', 'IPE400 · B/1–C/1', 'sec'),
        (4, None, None, 'K2-03', 'IPE400 · C/1–D/1', 'sec'),
        (4, None, None, 'K2-04', 'IPE400 · A/2–B/2', 'sec'),
        (4, None, None, 'K2-05', 'IPE400 · B/2–C/2', 'sec'),
        (4, None, None, 'K2-06', 'IPE400 · C/2–D/2', 'sec'),
        (4, None, None, 'K2-07', 'IPE400 · A/3–B/3', None),
        (4, None, None, 'K2-08', 'IPE400 · B/3–C/3', None),
        (4, None, None, '… 16 kiriş daha', None, 'soluk'),
        (3, 'sag', 'ikincil', 'İkincil kirişler', '12', None),
        (3, 'sag', 'capraz', 'Çaprazlar', '12', None),
        (3, 'sag', 'doseme', 'Döşemeler', '12', None),
        (3, 'sag', 'dugum', 'Düğümler', '20', None),
        (2, 'sag', 'kat', 'Kat 1', '+4,50', 'benzer → Kat 2'),
        (2, 'sag', 'kat', 'Zemin', '±0,00', 'temel'),
        (1, 'sag', 'aks', 'Aks sistemleri', '1', None),
        (1, 'sag', 'katalog', 'Kütüphane', 'kesit 4 · malzeme 2', None),
        (1, 'sag', 'yuk', 'Yükler', 'desen 5 · durum 6 · komb. 12', None),
        (1, 'sag', 'benzer', 'Gruplar', '3', None),
    ]
    ry = y + 88
    rh = 24
    for (sev, chev, ik, ad, bilgi, not_) in satirlar:
        if ry + rh > y + h - 44:
            break
        ix = x + 12 + sev * 14
        secili = (not_ == 'sec')
        if secili:
            t.dikd(x + 1, ry, w - 2, rh, fill=R['altin_dolgu'])
            t.dikd(x + 1, ry, 3, rh, fill=R['altin'])
        if chev:
            t.ikon(chev, ix, ry + 5, 14, R['metin3'])
        if ik:
            t.ikon(ik, ix + 16, ry + 5, 14, R['metin2'])
            tx = ix + 36
        else:
            tx = ix + 20
        soluk = (not_ == 'soluk')
        kalin = 600 if (ad == 'Kat 2' or sev == 0) else 450
        t.yazi(tx, ry + 16, ad, 12, kalin, R['metin3'] if soluk else R['metin'], maxw=w - (tx - x) - 90)
        if bilgi:
            if ad.startswith('K2-'):
                t.yazi(tx + 46, ry + 16, bilgi, 11, 400, R['metin3'])
            elif bilgi.replace(',', '').replace('+', '').replace('±', '').replace('.', '').isdigit() and (bilgi[0] in '+±'):
                t.yazi(tx + t.gen(ad, 12, kalin) + 8, ry + 16, bilgi, 11, 400, R['metin3'])
            else:
                t.yazi_sag(x + w - 14, ry + 16, bilgi, 11, 400, R['metin3'])
        if not_ in ('ana kat', 'benzer → Kat 2', 'temel'):
            pw = t.gen(not_, 10, 600) + 12
            # kat satırlarında: kot sağda, rozet solunda
            bw_ = t.gen(bilgi, 11, 400)
            etiket_pul(t, x + w - 14 - bw_ - 8 - pw, ry + 4, not_, 10, h=16,
                       zemin=R['altin_dolgu'] if not_ == 'ana kat' else R['yuzey3'],
                       renk=R['kahve_koyu'] if not_ == 'ana kat' else R['metin2'])
        ry += rh
    # alt bilgi
    t.yatay(x, x + w, y + h - 40, R['cizgi'])
    t.ikon('sec', x + 12, y + h - 28, 14, R['metin2'])
    t.yazi(x + 32, y + h - 17, 'Seçileni ağaçta göster', 11.5, 500, R['metin2'])
    t.yazi_sag(x + w - 12, y + h - 17, '6 / 285', 11, 400, R['metin3'])


# ================================================================ özellikler paneli
def ciz_pencere_dugmeleri(t, x, y, w, aktif='ozellikler'):
    """Yan panel = tek iskelet, çok pencere: ikon düğmeleri, aktif altın pil."""
    pencereler = [('ozellikler', 'Özellikler'), ('katalog', 'Kataloglar'), ('agac', 'Model ağacı'),
                  ('suzgec', 'Filtre & görünürlük'), ('sorgu', 'Sorgu')]
    cx = x + 10
    for ik, ad in pencereler:
        if ik == aktif:
            bw = t.gen(ad, 12, 600) + 38
            t.yuv(cx, y, bw, 30, 15, fill=R['altin_dolgu'], outline=alfa(R['altin'], 0.8))
            t.ikon(ik, cx + 10, y + 7, 16, R['kahve_koyu'])
            t.yazi(cx + 32, y + 19.5, ad, 12, 600, R['kahve_koyu'])
            cx += bw + 4
        else:
            t.ikon(ik, cx + 7, y + 7, 16, R['metin2'])
            cx += 32
    t.ikon('sabitle', x + w - 54, y + 7, 16, R['metin3'])
    t.ikon('yuzdur', x + w - 30, y + 7, 16, R['metin3'])


def bolum_basligi(t, x, y, w, ad, acik=True, ozet=None, rozet=None):
    t.yatay(x, x + w, y, R['cizgi'])
    t.ikon('asagi' if acik else 'sag', x + 10, y + 7, 14, R['metin2'])
    t.yazi(x + 28, y + 19, ad, 12.5, 600, R['metin'])
    if rozet:
        etiket_pul(t, x + 28 + t.gen(ad, 12.5, 600) + 8, y + 6, rozet, 10, h=16)
    if ozet and not acik:
        t.yazi_sag(x + w - 12, y + 19, ozet, 11, 400, R['metin3'], )
    return y + 28


def satir(t, x, y, w, etiket, deger, **kw):
    t.yazi(x + 12, y + 17, etiket, 11.5, 450, R['metin2'])
    alan(t, x + 108, y + 2, w - 120, 22, deger, **kw)
    return y + 26


def ciz_ozellikler(t, L, mod='model'):
    x, y, w, h = L['sag_x'], L['govde_y0'], L['sag_w'], L['govde_y1'] - L['govde_y0']
    kart(t, x, y, w, h)
    ciz_pencere_dugmeleri(t, x, y + 10, w)
    t.yatay(x, x + w, y + 50, R['cizgi'])
    cy = y + 62
    if mod == 'model':
        t.ikon('kiris', x + 12, cy, 20, R['metin'])
        t.yazi(x + 40, cy + 15, 'Kiriş', 15, 600, R['metin'])
        etiket_pul(t, x + 40 + t.gen('Kiriş', 15, 600) + 8, cy + 1, '6 seçili', 10.5)
        t.yazi(x + 40, cy + 33, 'K2-01 … K2-06 · IPE400 · S355 · Kat 2', 11.5, 400, R['metin3'])
        t.ikon('nokta3', x + w - 32, cy + 2, 16, R['metin3'])
        cy += 50
        kompakt = L['kompakt']
        # Genel
        if kompakt:
            cy = bolum_basligi(t, x, cy, w, 'Genel', acik=False, ozet='Kiriş · 3 · Ana kirişler')
        else:
            cy = bolum_basligi(t, x, cy, w, 'Genel')
            cy = satir(t, x, cy, w, 'Ad', 'K2-01 … K2-06  (6 farklı)', renk=R['metin2'])
            cy = satir(t, x, cy, w, 'Tür', 'Kiriş · çelik', acilir=True)
            t.yazi(x + 12, cy + 17, 'Sınıf / renk', 11.5, 450, R['metin2'])
            t.yuv(x + 108, cy + 2, 22, 22, 5, fill=hexrgb('#AAB3BD'), outline=R['cizgi2'])
            alan(t, x + 136, cy + 2, w - 148, 22, '3 · Ana kiriş', acilir=True)
            cy += 26
            cy = satir(t, x, cy, w, 'Grup', 'Ana kirişler', acilir=True)
            cy += 6
        # Kesit
        cy = bolum_basligi(t, x, cy, w, 'Kesit')
        cy = satir(t, x, cy, w, 'Profil', 'IPE400', katalog=True)
        cy = satir(t, x, cy, w, 'Malzeme', 'S355', katalog=True)
        cy = satir(t, x, cy, w, 'Dönme', 'Üst (gövde düşey)', acilir=True)
        cy += 6
        # Konum
        if kompakt:
            cy = bolum_basligi(t, x, cy, w, 'Konum', acik=False, ozet='Kat 2 (+9,00) · Orta · Orta')
        else:
            cy = bolum_basligi(t, x, cy, w, 'Konum')
            cy = satir(t, x, cy, w, 'Kat', 'Kat 2  (+9,00)', acilir=True)
            cy = satir(t, x, cy, w, 'Düzlemde', 'Orta', acilir=True)
            cy = satir(t, x, cy, w, 'Derinlik', 'Orta', acilir=True)
            cy = satir(t, x, cy, w, 'Ofset dz', '0 mm')
            cy += 6
        # Serbestlikler
        cy = bolum_basligi(t, x, cy, w, 'Serbestlikler')
        t.yazi(x + 12, cy + 17, 'Uç', 11.5, 450, R['metin2'])
        sx = x + 108
        kon = []
        parcali(t, sx, cy + 1, 24, ['Başlangıç', 'Bitiş'], 0, boy=11, pad=18, konum=kon)
        t.daire(kon[0][0] + 10, cy + 13, 3.2, fill=R['altin'])
        t.daire(kon[1][0] + 10, cy + 13, 3.2, fill=R['kahve'])
        cy += 28
        cy = satir(t, x, cy, w, 'Ön ayar', 'Mafsal (moment serbest)', acilir=True)
        t.yazi(x + 12, cy + 17, 'Serbestlik', 11.5, 450, R['metin2'])
        dx = x + 108
        adim = (w - 120) / 6
        cw_ = adim - 4
        for i, d in enumerate(('Ux', 'Uy', 'Uz', 'Rx', 'Ry', 'Rz')):
            tutulu = i < 3
            if tutulu:
                t.yuv(dx, cy + 2, cw_, 22, 5, fill=R['antrasit'])
                t.yazi_orta(dx + cw_ / 2, cy + 17, d, 11, 600, R['krem'])
            else:
                t.yuv(dx, cy + 2, cw_, 22, 5, fill=R['yuzey'], outline=R['cizgi2'])
                t.yazi_orta(dx + cw_ / 2, cy + 17, d, 11, 500, R['metin2'])
            dx += adim
        cy += 28
        t.yazi(x + 108, cy + 12, 'dolu = tutulu · boş = serbest · kısmi / yay: sağ tık', 10, 400, R['metin3'], maxw=w - 120)
        cy += 20
        # kapalı bölümler
        cy = bolum_basligi(t, x, cy, w, 'Yükler', acik=False, ozet='G 4,2 kN/m · Q 6,0 kN/m', rozet='2')
        cy = bolum_basligi(t, x, cy, w, 'Analiz', acik=False, ozet='Analiz parçası · elastik')
        cy = bolum_basligi(t, x, cy, w, 'Tasarım', acik=False, ozet='ÇYTHYE 2018 · D/C 0,74')
        t.yatay(x, x + w, cy, R['cizgi'])
    else:  # sonuç: tasarım bölümü açık
        t.ikon('kiris', x + 12, cy, 20, R['metin'])
        t.yazi(x + 40, cy + 15, 'K2-05', 15, 600, R['metin'])
        etiket_pul(t, x + 40 + t.gen('K2-05', 15, 600) + 8, cy + 1, 'D/C 1,04', 10.5, renk=(255, 255, 255), zemin=R['hata'])
        t.yazi(x + 40, cy + 33, 'Kiriş · IPE400 · S355 · Kat 2 · B/2–C/2', 11.5, 400, R['metin3'])
        cy += 50
        cy = bolum_basligi(t, x, cy, w, 'Genel', acik=False, ozet='Kiriş · 3 · Ana kirişler')
        cy = bolum_basligi(t, x, cy, w, 'Kesit', acik=False, ozet='IPE400 · S355')
        cy = bolum_basligi(t, x, cy, w, 'Konum', acik=False, ozet='Kat 2 · Orta')
        cy = bolum_basligi(t, x, cy, w, 'Serbestlikler', acik=False, ozet='Mafsal / Mafsal')
        cy = bolum_basligi(t, x, cy, w, 'Yükler', acik=False, ozet='G 4,2 · Q 6,0 kN/m', rozet='2')
        cy = bolum_basligi(t, x, cy, w, 'Analiz', acik=False, ozet='M3 maks 187 kN·m')
        cy = bolum_basligi(t, x, cy, w, 'Tasarım', acik=True)
        cy = satir(t, x, cy, w, 'Yönetmelik', 'ÇYTHYE 2018 — YDKT', acilir=True)
        cy = satir(t, x, cy, w, 'Kombinasyon', '1,2G + 1,6Q  (kritik)', acilir=True)
        # kontrol çubukları
        t.yazi(x + 12, cy + 17, 'Kontroller', 11.5, 450, R['metin2'])
        cy += 4
        for ad, dc in (('Eğilme M3', 1.04), ('Kesme V2', 0.41), ('Sehim L/300', 0.88), ('Yanal burkulma', 0.97)):
            bx = x + 108
            bw = w - 120
            t.yazi(bx, cy + 15, ad, 11, 450, R['metin'])
            t.yazi_sag(bx + bw, cy + 15, ('%.2f' % dc).replace('.', ','), 11, 600,
                       DC_RENK[4] if dc > 1 else DC_RENK[3] if dc > 0.9 else R['metin'])
            t.yuv(bx, cy + 19, bw, 5, 2.5, fill=R['yuzey3'])
            renk = DC_RENK[4] if dc > 1 else DC_RENK[3] if dc > 0.9 else DC_RENK[2] if dc > 0.7 else DC_RENK[1] if dc > 0.5 else DC_RENK[0]
            t.yuv(bx, cy + 19, bw * min(1, dc / 1.1), 5, 2.5, fill=renk)
            cy += 28
        cy += 4
        t.yuv(x + 12, cy, w - 24, 44, 6, fill=R['altin_zemin'], outline=alfa(R['altin'], 0.5))
        t.ikon('celik', x + 22, cy + 6, 16, R['kahve_koyu'])
        t.yazi(x + 44, cy + 18, 'Kesit önerisi: IPE450 → D/C 0,82', 11.5, 600, R['kahve_koyu'])
        t.yazi(x + 44, cy + 34, 'Aynı seri, bir boy üst · 6 benzer kirişe uygula', 10.5, 400, R['metin2'])
        cy += 56
        dugme(t, x + 12, cy, (w - 32) / 2, 28, 'Etkileşimli tasarım…', 'kalem')
        dugme(t, x + 12 + (w - 32) / 2 + 8, cy, (w - 32) / 2, 28, 'Ayrıntı raporu', 'rapor')
        cy += 36
        cy = bolum_basligi(t, x, cy, w, 'Tasarım girdileri', acik=False, ozet='Lb 6,0 m · Cb 1,0 · K 1,0')
        t.yatay(x, x + w, cy, R['cizgi'])
    # alt bilgi: anında uygula / Uygula / Al
    fy = y + h - 44
    t.yatay(x, x + w, fy, R['cizgi'])
    anahtar(t, x + 12, fy + 14, True)
    t.yazi(x + 50, fy + 26, 'Anında uygula', 11.5, 500, R['metin'])
    dugme(t, x + w - 150, fy + 9, 72, 26, 'Uygula', boy=11.5)
    dugme(t, x + w - 72, fy + 9, 60, 26, 'Al', boy=11.5)


# ================================================================ görünüm
def ciz_rail(t, L, aktif_render='ekstr', ipucu_goster=True):
    x = L['vp_x0'] + 16
    y = L['vp_y0'] + 16
    ogeler = [('imlec', 'Seç', True), ('kaydir', 'Kaydır', False), ('dondur', 'Döndür', False),
              ('yakinlastir', 'Pencereyle yakınlaştır', False), ('ev', 'Tam görünüm · Home', False), None,
              ('plan', 'Plan görünümü', False), ('ucb', '3B görünüm', True), ('kesit', 'Kesit düzlemi', False), None,
              ('cubuk', 'Çubuk gösterimi · Ctrl+1', aktif_render == 'cubuk'), ('ekstr', 'Ekstrüzyon · Ctrl+4', aktif_render == 'ekstr'), None,
              ('olc', 'Ölç', False), ('sorgu', 'Sorgu', False)]
    if L['kompakt']:
        ogeler = [('agac', 'Model ağacı', False), None] + ogeler
    h = sum(36 if o else 9 for o in ogeler) + 8
    kart(t, x, y, 40, h, 8, golge=(8, 3, 0.12))
    cy = y + 4
    for o in ogeler:
        if o is None:
            t.yatay(x + 10, x + 30, cy + 4, R['cizgi'])
            cy += 9
            continue
        ik, ad, aktif = o
        if aktif:
            t.yuv(x + 4, cy + 2, 32, 32, 6, fill=R['altin_dolgu'])
        t.ikon(ik, x + 10, cy + 8, 20, R['metin'] if aktif else R['metin2'])
        if ipucu_goster and ik == 'ekstr':
            ipucu(t, x + 42, cy + 18, 'Ekstrüzyon görünümü  ·  Ctrl+4')
        cy += 36
    return x + 40


def ciz_eksen_uclusu(t, kam, x, y):
    for v, ad, renk in (((1, 0, 0), 'X', R['eksen_x']), ((0, 1, 0), 'Y', R['eksen_y']), ((0, 0, 1), 'Z', R['eksen_z'])):
        dx, dy = kam.yon2d(v)
        L_ = 26
        t.cizgi([(x, y), (x + dx * L_, y + dy * L_)], renk, 1.5)
        t.daire(x + dx * L_, y + dy * L_, 2.2, fill=renk)
        t.yazi_orta(x + dx * (L_ + 11), y + dy * (L_ + 11) + 4, ad, 10.5, 600, renk)
    t.daire(x, y, 2.2, fill=R['metin2'])


def ciz_secim_anahtarlari(t, x1, y1):
    """Seçim anahtarları çubuğu: nesne türü anahtarları + tümü + kapsam seviyesi."""
    ogeler = [('tumu', True), None, ('dugum', False), ('kolon', True), ('kiris', True), ('doseme', True), ('duvar', True),
              ('aks', False), ('yuk', False), ('mesnet', True), ('temel', True), None]
    w = sum(28 if o else 9 for o in ogeler) + 12 + 118 + 8
    x, y = x1 - w, y1 - 32
    kart(t, x, y, w, 32, 16, golge=(8, 3, 0.12))
    cx = x + 6
    for o in ogeler:
        if o is None:
            t.dusey(cx + 4, y + 9, y + 23, R['cizgi'])
            cx += 9
            continue
        ik, acik = o
        if acik:
            t.yuv(cx, y + 5, 26, 22, 5, fill=R['altin_dolgu'] if ik == 'tumu' else R['yuzey3'])
        t.ikon(ik, cx + 5, y + 8, 16, R['metin'] if acik else alfa(R['metin3'], 0.7))
        cx += 28
    t.yazi(cx + 6, y + 20, 'Kapsam: Eleman', 11, 500, R['metin2'])
    t.ikon('asagi', cx + 6 + t.gen('Kapsam: Eleman', 11, 500) + 2, y + 9, 14, R['metin3'])
    t.ikon('goz', x + w - 24, y + 8, 16, R['metin3'])
    return x


def ciz_komut(t, L, metin='Komut:', son='Son: KİRİŞ — 6 kiriş eklendi (Kat 2)'):
    x0, x1 = L['vp_x0'] + 16, L['vp_x1'] - 16
    y = L['vp_y1'] - 16 - L['komut_h']
    h = L['komut_h']
    kart(t, x0, y, x1 - x0, h, 8, golge=(8, 3, 0.12))
    t.ikon('komut', x0 + 10, y + 7, 16, R['kahve'])
    cx = x0 + 34
    t.yazi(cx, y + 19.5, metin, 12.5, 600, R['metin2'])
    cx += t.gen(metin, 12.5, 600) + 6
    t.dikd(cx, y + 8, 1.5, 15, fill=R['kahve'])     # imleç
    cx += 16
    t.yazi(cx, y + 19.5, '·', 12.5, 500, R['metin3'])
    cx += 12
    t.yazi(cx, y + 19.5, son, 12, 400, R['metin3'], maxw=x1 - cx - 230)
    # sağ: Ctrl+Q ipucu, geçmiş, dil
    rx = x1 - 10
    pw = t.gen('Ctrl+Q · Hızlı başlat', 10.5, 500) + 14
    t.yuv(rx - pw, y + 6, pw, 18, 4, fill=R['yuzey3'])
    t.yazi(rx - pw + 7, y + 18.5, 'Ctrl+Q · Hızlı başlat', 10.5, 500, R['metin2'])
    rx -= pw + 10
    t.ikon('gecmis', rx - 16, y + 7, 16, R['metin3'])
    rx -= 26
    t.yazi_sag(rx, y + 19, 'TR | EN takma adlar', 10.5, 400, R['metin3'])


def ciz_durum(t, L, yonerge='Kiriş: ikinci noktayı seçin', ipucu_metin='Enter yinele · Esc bitir · sağ tık yakalama',
              kapsam=1, kapsam_not='3 katta uygulanacak', secili='6 nesne · 12 tutamaç', koord='X 12,000   Y 6,000   Z 9,000',
              animasyon=False):
    W, H = L['W'], L['H']
    y = H - L['durum_h']
    h = L['durum_h']
    t.dikd(0, y, W, h, fill=R['durum'])
    t.yatay(0, W, y, R['cizgi'])
    k = L['kenar']
    kompakt = L['kompakt']
    by = y + h / 2 + 4
    # sol: adım yönergesi
    t.daire(k + 5, y + h / 2, 3.5, fill=R['altin'])
    t.yazi(k + 16, by, yonerge, 11.5, 600, R['metin'])
    if not kompakt:
        t.yazi(k + 20 + t.gen(yonerge, 11.5, 600), by, ipucu_metin, 11, 400, R['metin3'])
    # orta: Orto / Akıllı yakalama / Sürükle · X Y Z · orta tuş
    cx = W * (0.36 if not kompakt else 0.34)
    def tog(s, acik, kisa=None):
        nonlocal cx
        w = t.gen(s, 11, 500) + 12
        if acik:
            t.yuv(cx, y + 4, w, h - 8, 4, fill=R['altin_dolgu'])
        t.yazi(cx + 6, by, s, 11, 600 if acik else 500, R['metin'] if acik else R['metin3'])
        cx += w + 4
    tog('Orto', True)
    tog('Akıllı yakalama', True)
    tog('Sürükle', False)
    cx += 6
    t.dusey(cx, y + 7, y + h - 7, R['cizgi2'])
    cx += 10
    for ad, kilit in (('X', False), ('Y', False), ('Z', True)):
        if kilit:
            t.yuv(cx, y + 5, 18, h - 10, 4, fill=R['antrasit'])
            t.yazi_orta(cx + 9, by, ad, 10.5, 700, R['krem'])
        else:
            t.yuv(cx, y + 5, 18, h - 10, 4, outline=R['cizgi2'])
            t.yazi_orta(cx + 9, by, ad, 10.5, 600, R['metin3'])
        cx += 22
    if not kompakt:
        cx += 6
        t.dusey(cx, y + 7, y + h - 7, R['cizgi2'])
        cx += 10
        t.yazi(cx, by, 'Orta tuş: Kaydır', 11, 400, R['metin3'])
        cx += t.gen('Orta tuş: Kaydır', 11) + 12
        if animasyon:
            t.dusey(cx, y + 7, y + h - 7, R['cizgi2'])
            cx += 10
            t.ikon('oynat', cx, y + 5, 16, R['kahve'])
            t.yazi(cx + 20, by, 'Animasyon', 11, 500, R['metin2'])
            cx += 20 + t.gen('Animasyon', 11, 500) + 8
            t.yuv(cx, y + h / 2 - 1.5, 70, 3, 1.5, fill=R['cizgi2'])
            t.yuv(cx, y + h / 2 - 1.5, 30, 3, 1.5, fill=R['altin'])
            t.daire(cx + 30, y + h / 2, 5, fill=R['yuzey'], outline=R['altin'], lw=1.5)
            cx += 80
    # sağ: seçili sayısı, koordinat, birim, kat kapsamı
    rx = W - k
    t.yazi_sag(rx, by, secili, 11, 500, R['metin2'])
    rx -= t.gen(secili, 11, 500) + 14
    t.dusey(rx, y + 7, y + h - 7, R['cizgi2'])
    rx -= 12
    if not kompakt:
        t.yazi_sag(rx, by, koord, 11, 400, R['metin2'])
        rx -= t.gen(koord, 11, 400) + 14
        t.dusey(rx, y + 7, y + h - 7, R['cizgi2'])
        rx -= 12
    birim = 'kN, m, °C'
    t.ikon('asagi', rx - 14, y + (h - 14) / 2, 14, R['metin3'])
    t.yazi_sag(rx - 14, by, birim, 11, 500, R['metin2'])
    rx -= t.gen(birim, 11, 500) + 14 + 14
    t.dusey(rx, y + 7, y + h - 7, R['cizgi2'])
    rx -= 12
    if kapsam_not and not kompakt:
        t.yazi_sag(rx, by, kapsam_not, 11, 600, R['kahve'])
        rx -= t.gen(kapsam_not, 11, 600) + 10
    sec = ['Bu kat', 'Benzer katlar', 'Tüm katlar'] if not kompakt else ['Bu kat', 'Benzer', 'Tümü']
    pw = sum(t.gen(s, 11, 500) + 16 for s in sec) + 4
    px = rx - pw
    parcali(t, px, y + 3, h - 6, sec, kapsam, boy=11, pad=8)
    rx = px - 10
    t.yazi_sag(rx, by, 'Kat kapsamı', 10.5, 400, R['metin3'])
    rx -= t.gen('Kat kapsamı', 10.5) + 8
    t.ikon('kat', rx - 14, y + (h - 14) / 2, 14, R['metin3'])
    return px, pw


def kapsam_popover(t, L, px, pw):
    """Kat kapsamı anahtarı üstünde önizleme balonu (kat-kapsami.png için)."""
    W = 300
    H = 150
    x = px + pw / 2 - W / 2
    y = L['H'] - L['durum_h'] - 12 - H
    kart(t, x, y, W, H, 8, golge=(12, 4, 0.16))
    t.d.polygon([(t.p(x + W / 2), t.p(y + H + 7)), (t.p(x + W / 2 - 7), t.p(y + H - 0.5)), (t.p(x + W / 2 + 7), t.p(y + H - 0.5))], fill=R['yuzey'])
    t.yazi(x + 14, y + 22, 'Benzer katlar', 12.5, 600, R['metin'])
    t.yazi_sag(x + W - 14, y + 22, 'Alt+2', 10.5, 500, R['metin3'])
    t.yazi(x + 14, y + 38, 'Ana kat: Kat 2 · eşleşme: plan konumu + nesne türü', 10.5, 400, R['metin3'])
    ry = y + 50
    for ad, kot, durum, ik in (('Kat 3', '+13,50', 'benzer → Kat 2', 'onay'), ('Kat 2', '+9,00', 'ana kat', 'onay'),
                               ('Kat 1', '+4,50', 'benzer → Kat 2', 'onay'), ('Zemin', '±0,00', 'Yok — etkilenmez', None)):
        if ik:
            t.yuv(x + 14, ry + 3, 14, 14, 3, fill=R['kahve'])
            t.ikon('onay', x + 13, ry + 2, 16, (255, 255, 255), 1.8)
        else:
            t.yuv(x + 14, ry + 3, 14, 14, 3, outline=R['cizgi2'])
        t.yazi(x + 36, ry + 14, ad, 11.5, 600 if ad == 'Kat 2' else 500, R['metin'] if ik else R['metin3'])
        t.yazi(x + 86, ry + 14, kot, 11, 400, R['metin3'])
        t.yazi_sag(x + W - 14, ry + 14, durum, 10.5, 500, R['kahve'] if ad == 'Kat 2' else R['metin2'] if ik else R['metin3'])
        ry += 20
    t.yatay(x + 14, x + W - 14, ry + 2, R['cizgi'])
    t.yazi(x + 14, ry + 16, 'Çizim · seçim · atama · silme → 3 katta uygulanacak · geri al tek adım', 10, 400, R['metin2'])


def ciz_gorunum(t, L, mod='model', secim=True, ipucu_goster=True, dock_h=0):
    """Görünüm kartı: 3B sahne + yüzen denetimler. Döndürür: sahne bilgisi."""
    x, y, w, h = L['vp_x0'], L['vp_y0'], L['vp_x1'] - L['vp_x0'], L['vp_y1'] - L['vp_y0'] - dock_h
    kart(t, x, y, w, h)
    bina = Bina(secili_kirisler=secim, hover=(mod == 'model'))
    sahne = Sahne(bina, mod='dc' if mod == 'dc' else 'model')
    ss = 3 if t.S == 1 else 2
    kompakt = L['kompakt']
    sig = (0.10, 0.12, 0.90, 0.80) if not kompakt else (0.10, 0.14, 0.92, 0.80)
    if mod == 'dc':
        sig = (0.08, 0.14, 0.80, 0.84)
    im, bilgi = sahne.render(w - 2, h - 2, t.S, ss, az=-127, el=23, sig=sig)
    m = t._rr_mask(t.p(w - 2), t.p(h - 2), t.p(7), 4)
    t.im.paste(im, (t.p(x + 1), t.p(y + 1)), m)
    ox, oy = x + 1, y + 1
    proj = bilgi['proj']
    P = lambda p: (ox + p[0], oy + p[1])
    # rail
    rail_x1 = ciz_rail(t, L, ipucu_goster=ipucu_goster and mod == 'model')
    # görünüm başlığı pili
    bx = rail_x1 + 12
    by = y + 16
    baslik = '3B görünüm · Perspektif' if mod == 'model' else '3B görünüm · Tasarım sonuçları'
    bw = t.gen(baslik, 12, 600) + 44
    kart(t, bx, by, bw, 30, 15, golge=(6, 2, 0.10))
    t.ikon('ucb', bx + 10, by + 7, 16, R['metin2'])
    t.yazi(bx + 32, by + 19.5, baslik, 12, 600, R['metin'])
    bx += bw + 8
    alt = 'Derinlik: tümü · Sınır: Zemin–Kat 3' if not kompakt else 'Derinlik: tümü'
    bw2 = t.gen(alt, 11, 500) + 36
    kart(t, bx, by, bw2, 30, 15, golge=(6, 2, 0.10))
    t.ikon('kat', bx + 10, by + 8, 14, R['metin3'])
    t.yazi(bx + 28, by + 19.5, alt, 11, 500, R['metin2'])
    bx += bw2 + 8
    # sağ üst: render modu + görünüm düğmeleri
    rx = x + w - 16
    kw = 120
    kart(t, rx - kw, by, kw, 30, 15, golge=(6, 2, 0.10))
    parcali(t, rx - kw + 4, by + 3, 24, ['', ''], 1, ikonlar=['cubuk', 'ekstr'], pad=12)
    t.ikon('goz', rx - 30, by + 7, 16, R['metin2'])
    rx -= kw + 8
    for ik in ('kesit', 'disli'):
        kart(t, rx - 30, by, 30, 30, 15, golge=(6, 2, 0.10))
        t.ikon(ik, rx - 23, by + 7, 16, R['metin2'])
        rx -= 38
    # eksen üçlüsü (sol alt)
    # sonuç kipinde D/C lejantı sol altta durur; üçlü onun üstüne alınır (çakışma olmasın)
    ciz_eksen_uclusu(t, bilgi['kam'], x + 96, y + h - 16 - L['komut_h'] - 54 - (76 if mod == 'dc' else 0))
    # seçim anahtarları (sağ alt)
    ciz_secim_anahtarlari(t, x + w - 16, y + h - 16 - L['komut_h'] - 10)
    if mod == 'model' and secim:
        # yüzen "Seçim" çipi (üst orta)
        cw = 500 if not kompakt else 300
        cx = bx + 12
        kart(t, cx, by, cw, 30, 15, golge=(6, 2, 0.10))
        t.yazi(cx + 14, by + 19.5, 'Seçim', 11, 600, R['kahve'])
        t.yazi(cx + 56, by + 19.5, '6 kiriş', 12, 600, R['metin'])
        t.yazi(cx + 102, by + 19.5, 'IPE400 · Kat 2', 11.5, 400, R['metin3'])
        if not kompakt:
            sx = cx + 196
            t.dusey(sx, by + 8, by + 22, R['cizgi'])
            sx += 10
            for ik, ad in (('benzer', 'Benzerini seç'), ('goz', 'Yalnız seçili')):
                t.ikon(ik, sx, by + 8, 14, R['metin2'])
                t.yazi(sx + 18, by + 19.5, ad, 11, 500, R['metin2'])
                sx += 18 + t.gen(ad, 11, 500) + 14
            t.yazi(sx, by + 19.5, 'Ctrl+K ters', 10.5, 400, R['metin3'])
        t.ikon('kapat_k', cx + cw - 26, by + 7, 16, R['metin3'])
        # doğrudan değiştirme tutamaçları (altın = başlangıç, kahve = bitiş, orta = böl)
        p0, p1 = P(bilgi['tutamac'][0]), P(bilgi['tutamac'][1])
        pm = P(bilgi['tutamac_orta'])
        t.daire(p0[0], p0[1], 6, fill=R['altin'], outline=(255, 255, 255), lw=1.5)
        t.daire(p1[0], p1[1], 6, fill=R['kahve'], outline=(255, 255, 255), lw=1.5)
        t.yuv(pm[0] - 4, pm[1] - 4, 8, 8, 2, fill=(255, 255, 255), outline=R['kahve'])
        # ölçü etiketi (değer yazılabilir)
        ew = 56
        t.yuv(pm[0] - ew / 2, pm[1] + 10, ew, 18, 4, fill=(255, 255, 255), outline=alfa(R['altin'], 0.9))
        t.yazi_orta(pm[0], pm[1] + 23, '6 000', 11, 600, R['kahve_koyu'])
        # bağlamsal mini araç çubuğu
        sk = bilgi['secim_kutu']
        mx = ox + sk[2] - 240
        my = oy + sk[1] - 50
        mx = min(mx, x + w - 16 - 330)
        mw = 316
        kart(t, mx, my, mw, 32, 8, golge=(8, 3, 0.14))
        cx = mx + 8
        t.ikon('kiris', cx, my + 8, 16, R['metin2'])
        cx += 22
        for s in ('IPE400', 'S355', 'Kat 2', 'Mafsal'):
            t.yazi(cx, my + 20.5, s, 12, 600 if s == 'IPE400' else 500, R['metin'])
            cx += t.gen(s, 12, 600) + 4
            t.ikon('asagi', cx, my + 10, 12, R['metin3'])
            cx += 16
            t.dusey(cx, my + 9, my + 23, R['cizgi'])
            cx += 10
        t.ikon('nokta3', mx + mw - 24, my + 8, 16, R['metin2'])
        # ince bağlayıcı çizgi
        t.cizgi([(mx + 30, my + 32), (ox + bilgi['secim_merkez'][0], oy + bilgi['secim_merkez'][1])], alfa(R['altin'], 0.6), 1)
        # üzerine gelme (hover) ipucu: ince kahverengi kontur sahnede, küçük etiket burada
        if 'hover' in bilgi:
            hx, hy = P(bilgi['hover'])
            e = bilgi['hover_e']
            s = '%s · HE340A · Kat %d' % (e.etiket, e.kat)
            lw_ = t.gen(s, 10.5, 500) + 12
            t.yuv(hx + 10, hy - 9, lw_, 18, 4, fill=alfa((255, 255, 255), 0.92), outline=alfa(R['kahve'], 0.6))
            t.yazi(hx + 16, hy + 4, s, 10.5, 500, R['kahve_koyu'])
    if mod == 'dc':
        ciz_dc_lejant(t, L, x, y, w, h, bilgi, P)
        ciz_deform_karti(t, L, x, y, w, h)
    ciz_komut(t, dict(L, vp_y1=y + h))
    return bilgi


def ciz_dc_lejant(t, L, x, y, w, h, bilgi, P):
    lw = 620 if not L['kompakt'] else 520
    lx = x + 104
    ly = y + h - 16 - L['komut_h'] - 12 - 46
    kart(t, lx, ly, lw, 46, 8, golge=(8, 3, 0.12))
    t.yazi(lx + 14, ly + 18, 'D/C oranı — Çelik tasarım · ÇYTHYE 2018', 11.5, 600, R['metin'])
    t.yazi_sag(lx + lw - 14, ly + 18, 'Eşikleri düzenle…  ·  Maks 1,04 (K2-05)', 10.5, 500, R['kahve'])
    etiketler = ['≤ 0,50', '0,50 – 0,70', '0,70 – 0,90', '0,90 – 1,00', '> 1,00']
    sayilar = ['92', '74', '46', '10', '3']
    cx = lx + 14
    cw = (lw - 28) / 5
    for i in range(5):
        t.yuv(cx, ly + 26, cw - 3, 6, 3, fill=DC_RENK[i])
        t.yazi(cx + 2, ly + 41, etiketler[i], 9.5, 500, R['metin2'])
        t.yazi_sag(cx + cw - 6, ly + 41, sayilar[i], 9.5, 500, R['metin3'])
        cx += cw
    # maksimum eleman işareti
    mp = P(bilgi['dc_maks_p'])
    t.daire(mp[0], mp[1], 9, outline=DC_RENK[4], lw=1.5)
    s = 'K2-05 · 1,04'
    ww = t.gen(s, 10.5, 600) + 12
    t.yuv(mp[0] + 12, mp[1] - 20, ww, 18, 4, fill=(255, 255, 255), outline=DC_RENK[4])
    t.yazi(mp[0] + 18, mp[1] - 7, s, 10.5, 600, DC_RENK[4])


def ciz_deform_karti(t, L, x, y, w, h):
    kw = 300
    kx = x + w - 16 - kw
    ky = y + 16 + 30 + 10
    kh = 292
    kart(t, kx, ky, kw, kh, 8, golge=(10, 4, 0.14))
    t.ikon('deform', kx + 12, ky + 11, 16, R['metin'])
    t.yazi(kx + 34, ky + 23, 'Şekil değiştirmiş şekil', 12.5, 600, R['metin'])
    anahtar(t, kx + kw - 42, ky + 12, False)
    t.yatay(kx, kx + kw, ky + 36, R['cizgi'])
    cy = ky + 44
    t.yazi(kx + 12, cy + 15, 'Durum / Kombinasyon', 11, 450, R['metin2'])
    alan(t, kx + 12, cy + 20, kw - 24, 22, '1,0G + 1,0Q + 1,0Ex  (statik)', acilir=True, boy=11.5)
    cy += 50
    t.yazi(kx + 12, cy + 15, 'Ölçek', 11, 450, R['metin2'])
    parcali(t, kx + 60, cy + 2, 22, ['Otomatik', 'Elle'], 0, boy=10.5, pad=8)
    alan(t, kx + kw - 82, cy + 1, 70, 22, '× 120', boy=11.5)
    cy += 30
    onay_kutusu(t, kx + 12, cy + 4, 'Gölge: deformasyonsuz şekil', True, 11)
    cy += 22
    onay_kutusu(t, kx + 12, cy + 4, 'Kübik eğri (çubuklar)', True, 11)
    cy += 22
    onay_kutusu(t, kx + 12, cy + 4, 'Kontur: düğüm yer değiştirmesi Uz', False, 11)
    cy += 28
    t.yazi(kx + 12, cy + 12, 'Kesit tesiri diyagramı', 11, 450, R['metin2'])
    parcali(t, kx + 12, cy + 18, 22, ['N', 'V2', 'V3', 'T', 'M2', 'M3'], 5, boy=10.5, pad=8)
    t.yazi(kx + 200, cy + 33, 'Dolu · değerli', 10, 400, R['metin3'])
    cy += 48
    t.yatay(kx, kx + kw, cy, R['cizgi'])
    t.ikon('oynat', kx + 12, cy + 8, 16, R['kahve'])
    t.yazi(kx + 34, cy + 20, 'Animasyon', 11, 500, R['metin2'])
    t.yuv(kx + 110, cy + 15, 120, 3, 1.5, fill=R['cizgi2'])
    t.yuv(kx + 110, cy + 15, 50, 3, 1.5, fill=R['altin'])
    t.daire(kx + 160, cy + 16.5, 5, fill=R['yuzey'], outline=R['altin'], lw=1.5)
    t.yazi_sag(kx + kw - 12, cy + 20, 'hız', 10, 400, R['metin3'])


def ciz_dock(t, L, dock_h):
    x, w = L['vp_x0'], L['vp_x1'] - L['vp_x0']
    y = L['vp_y1'] - dock_h + 16
    h = dock_h - 16
    kart(t, x, y, w, h)
    # sekmeler
    tx = x + 12
    for i, s in enumerate(('Çelik tasarım özeti', 'Kat tepkileri', 'Mesnet reaksiyonları', 'Yük durumları', 'Modal')):
        tw = t.gen(s, 12, 600) + 20
        if i == 0:
            t.yazi(tx + 10, y + 22, s, 12, 600, R['metin'])
            t.yuv(tx + 8, y + 32, tw - 16, 2.5, 1.2, fill=R['altin'])
        else:
            t.yazi(tx + 10, y + 22, s, 12, 500, R['metin2'])
        tx += tw
    t.ikon('tablo', x + w - 390, y + 10, 16, R['metin2'])
    t.yazi(x + w - 368, y + 22, 'Tablo seç…', 11.5, 500, R['metin2'])
    alan(t, x + w - 280, y + 8, 150, 24, 'Küme: Tasarım özeti', acilir=True, boy=11)
    dugme(t, x + w - 120, y + 7, 108, 26, "CSV'ye aktar", 'disa', boy=11)
    t.yatay(x, x + w, y + 36, R['cizgi'])
    # tablo
    kol = [('Eleman', 70), ('Kat', 60), ('Kesit', 80), ('Kombinasyon', 150), ('Kontrol', 110), ('D/C', 70), ('Durum', 110), ('Öneri', 180)]
    cx = x + 16
    hy = y + 54
    for ad, kw in kol:
        t.yazi(cx, hy, ad, 10.5, 600, R['metin3'])
        cx += kw
    t.yatay(x + 12, x + w - 12, hy + 7, R['cizgi'])
    satirlar = [
        ('K2-05', 'Kat 2', 'IPE400', '1,2G + 1,6Q', 'Eğilme M3', 1.04, 'Yetersiz', 'IPE450 (0,82)'),
        ('K2-06', 'Kat 2', 'IPE400', '1,2G + 1,6Q', 'Eğilme M3', 1.01, 'Yetersiz', 'IPE450 (0,80)'),
        ('C1-14', 'Kat 1', 'HE340A', '1,0G + 1,0Q + 1,0Ex', 'P–M etkileşim', 1.02, 'Yetersiz', 'HE360A (0,91)'),
        ('C1-07', 'Kat 1', 'HE340A', '1,0G + 1,0Q + 1,0Ey', 'P–M etkileşim', 0.91, 'Uygun', '—'),
        ('K3-11', 'Kat 3', 'IPE400', '1,2G + 1,6Q', 'Sehim L/300', 0.88, 'Uygun', '—'),
        ('Ç2-03', 'Kat 2', 'L100x10', '1,0G + 1,0Ex', 'Çekme / burkulma', 0.86, 'Uygun', '—'),
    ]
    ry = hy + 14
    for i, s in enumerate(satirlar):
        if ry + 22 > y + h - 30:
            break
        if i % 2 == 1:
            t.dikd(x + 12, ry, w - 24, 22, fill=R['yuzey2'])
        cx = x + 16
        for j, (ad, kw) in enumerate(kol):
            v = s[j]
            if j == 5:
                renk = DC_RENK[4] if v > 1 else DC_RENK[3] if v > 0.9 else R['metin']
                t.daire(cx + 5, ry + 11, 4, fill=DC_RENK[4] if v > 1 else DC_RENK[3] if v > 0.9 else DC_RENK[2] if v > 0.7 else DC_RENK[1])
                t.yazi(cx + 14, ry + 15, ('%.2f' % v).replace('.', ','), 11, 600, renk)
            elif j == 6:
                t.yazi(cx, ry + 15, v, 11, 600 if v == 'Yetersiz' else 450, R['hata'] if v == 'Yetersiz' else R['tamam'])
            else:
                t.yazi(cx, ry + 15, v, 11, 500 if j == 0 else 400, R['metin'] if j == 0 else R['metin2'])
            cx += kw
        ry += 22
    t.yatay(x, x + w, y + h - 26, R['cizgi'])
    t.yazi(x + 16, y + h - 9, '189 eleman · 3 yetersiz · 12 kontrol · süzgeç: D/C > 0,85', 10.5, 400, R['metin3'])
    t.yazi_sag(x + w - 16, y + h - 9, 'Satıra çift tık: ayrıntı penceresi (I/J ucu, istasyonlar)  ·  Ctrl+T tüm tablolar', 10.5, 400, R['metin3'])


# ================================================================ Seç & Süz
def ciz_secsuz(t, L):
    W, H = L['W'], L['H']
    t.d.rectangle([0, 0, t.p(W), t.p(H)], fill=alfa(R['antrasit'], 0.22))
    dw, dh = 900, 560
    x = L['vp_x0'] + (L['vp_x1'] - L['vp_x0'] - dw) / 2
    y = L['vp_y0'] + (L['vp_y1'] - L['vp_y0'] - dh) / 2 - 10
    kart(t, x, y, dw, dh, 10, golge=(22, 10, 0.30))
    # başlık
    t.ikon('suzgec', x + 20, y + 20, 20, R['kahve'])
    t.yazi(x + 50, y + 35, 'Seç & Süz', 17, 600, R['metin'])
    t.yazi(x + 50, y + 54, 'Kategori → Özellik → Koşul → Değer satırları; aynı kural görünüm süzgeci ve renk kuralı olarak da kullanılır (.filtre)', 11, 400, R['metin3'])
    t.ikon('kapat', x + dw - 36, y + 20, 18, R['metin2'])
    t.yatay(x, x + dw, y + 70, R['cizgi'])
    # sol: kayıtlı süzgeçler
    lw = 220
    t.dikd(x + 1, y + 71, lw, dh - 72 - 60, fill=R['yuzey2'])
    t.dusey(x + lw, y + 71, y + dh - 60, R['cizgi'])
    t.yazi(x + 16, y + 94, 'Kayıtlı süzgeçler', 11, 600, R['metin3'])
    ry = y + 106
    for i, (ad, ek) in enumerate((('Kat 2 kirişleri', '4 satır'), ('IPE400 — tümü', '2 satır'), ('Çaprazlar L100x10', '2 satır'),
                                  ('Mesnetli düğümler', '1 satır'), ('Zemin kat kolonları', '2 satır'), ('D/C > 0,90', 'renk kuralı'))):
        if i == 0:
            t.dikd(x + 1, ry, lw - 1, 28, fill=R['altin_dolgu'])
            t.dikd(x + 1, ry, 3, 28, fill=R['altin'])
        t.ikon('suzgec' if i < 5 else 'dc', x + 16, ry + 7, 14, R['metin2'])
        t.yazi(x + 38, ry + 18, ad, 12, 600 if i == 0 else 450, R['metin'])
        t.yazi_sag(x + lw - 12, ry + 18, ek, 10, 400, R['metin3'])
        ry += 28
    ry += 10
    dugme(t, x + 16, ry, lw - 32, 26, 'Yeni süzgeç', 'arti', boy=11)
    ry += 32
    dugme(t, x + 16, ry, lw - 32, 26, 'İçe aktar (.filtre)', 'ac', boy=11)
    t.yazi(x + 16, y + dh - 76, 'Firma profili: ortak klasör · 6 süzgeç', 10, 400, R['metin3'])
    # ana: kural tablosu
    mx = x + lw + 20
    mw = dw - lw - 40
    t.yazi(mx, y + 94, 'Kurallar', 11, 600, R['metin3'])
    t.yazi_sag(mx + mw, y + 94, 'Boş bağlaç = Ve · parantezle gruplayın', 10, 400, R['metin3'])
    kol = [('(', 26), ('Kategori', 116), ('Özellik', 116), ('Koşul', 90), ('Değer', 166), (')', 26), ('Ve / Veya', 82)]
    cx = mx
    hy = y + 112
    for ad, kw in kol:
        t.yazi(cx + (kw / 2 if ad in '()' else 4), hy + 4, ad, 10.5, 500, R['metin3'], anchor='ms' if ad in '()' else 'ls')
        cx += kw
    kurallar = [
        ('(', 'Nesne', 'Tür', '=', 'Kiriş', '', 'Ve'),
        ('', 'Kiriş', 'Kesit', '=', 'IPE400', '', 'Ve'),
        ('', 'Nesne', 'Kat', 'içinde', 'Kat 2, Kat 3', ')', 'Veya'),
        ('', 'Kiriş', 'Malzeme', '≠', 'S275', '', ''),
    ]
    ry = hy + 14
    for k in kurallar:
        cx = mx
        for j, (ad, kw) in enumerate(kol):
            v = k[j]
            if ad in '()':
                t.yuv(cx + 4, ry + 2, kw - 8, 24, 5, fill=R['yuzey2'], outline=R['cizgi'])
                if v:
                    t.yazi_orta(cx + kw / 2, ry + 19, v, 12, 500, R['metin'])
            elif ad == 'Ve / Veya':
                if v:
                    parcali(t, cx + 2, ry + 3, 22, ['Ve', 'Veya'], 0 if v == 'Ve' else 1, boy=10, pad=6)
            else:
                alan(t, cx + 2, ry + 2, kw - 6, 24, v, acilir=(ad != 'Değer'), boy=11.5)
            cx += kw
        t.ikon('sil', mx + mw - 14, ry + 7, 14, R['metin3'])
        ry += 30
    t.ikon('arti', mx + 2, ry + 6, 14, R['kahve'])
    t.yazi(mx + 20, ry + 17, 'Satır ekle', 11.5, 600, R['kahve'])
    t.yazi(mx + 100, ry + 17, 'Özellik listesi nesne türüne göre daralır (kesit, malzeme, kat, grup, etiket, serbestlik, yük deseni, paralellik, düzlem)', 10, 400, R['metin3'], maxw=mw - 110)
    ry += 40
    t.yatay(mx, mx + mw, ry, R['cizgi'])
    ry += 14
    onay_kutusu(t, mx, ry, 'Yalnız görünür nesneler', True, 11.5)
    onay_kutusu(t, mx + 190, ry, 'Kat kapsamına uy (Benzer katlar)', True, 11.5)
    onay_kutusu(t, mx + 440, ry, 'Seçime ekle (Shift)', False, 11.5)
    ry += 34
    # canlı sonuç
    t.yuv(mx, ry, mw, 48, 6, fill=R['altin_zemin'], outline=alfa(R['altin'], 0.45))
    t.daire(mx + 16, ry + 24, 4, fill=R['tamam'])
    t.yazi(mx + 30, ry + 21, 'Eşleşen: 48 nesne', 12.5, 600, R['metin'])
    t.yazi(mx + 30, ry + 38, 'Kat 2: 24 kiriş · Kat 3: 24 kiriş · canlı önizleme: modelde altın kontur', 10.5, 400, R['metin2'])
    t.yazi_sag(mx + mw - 14, ry + 30, 'Önizleme', 11, 500, R['metin2'])
    anahtar(t, mx + mw - 110, ry + 16, True)
    # alt düğmeler
    fy = y + dh - 60
    t.yatay(x, x + dw, fy, R['cizgi'])
    bx = x + 20
    dugme(t, bx, fy + 16, 140, 30, 'Benzerini seç', 'benzer', boy=11.5)
    bx += 148
    dugme(t, bx, fy + 16, 172, 30, 'Görünüm süzgeci yap', 'goz', boy=11.5)
    bx += 180
    dugme(t, bx, fy + 16, 120, 30, 'Renk kuralı…', 'dc', boy=11.5)
    rx = x + dw - 20
    birincil(t, rx - 100, fy + 15, 100, 32, 'Seç', 'sec', 'Enter')
    rx -= 110
    dugme(t, rx - 90, fy + 16, 90, 30, 'Kaydet…', 'kaydet', boy=11.5)
    rx -= 100
    dugme(t, rx - 80, fy + 16, 80, 30, 'Uygula', boy=11.5)


# ================================================================ sayfalar
def sayfa(W, H, S, sekme='Model', mod='model', secsuz=False, popover=False, ipucu_goster=True, kompakt=False):
    L = yerlesim(W, H, kompakt)
    t = Tuval(W, H, S, R['zemin'])
    ciz_baslik(t, L)
    ciz_sekmeler(t, L, sekme)
    ciz_gruplar(t, L, GRUPLAR_MODEL if sekme == 'Model' else GRUPLAR_TASARIM)
    if L['sol_w']:
        ciz_agac(t, L)
    dock_h = 236 if mod == 'dc' and not kompakt else 0
    ciz_gorunum(t, L, mod=mod, secim=(mod == 'model'), ipucu_goster=ipucu_goster, dock_h=dock_h)
    if dock_h:
        ciz_dock(t, L, dock_h)
    ciz_ozellikler(t, L, mod='model' if mod == 'model' else 'sonuc')
    if mod == 'dc':
        px, pw = ciz_durum(t, L, yonerge='Tasarım tamamlandı', ipucu_metin='189 eleman · 3 yetersiz (K2-05, K2-06, C1-14) · F6 şekil değiştirme',
                           kapsam=1, kapsam_not=None, secili='1 nesne (K2-05)', koord='X 9,000   Y 6,000   Z 9,000', animasyon=True)
    else:
        px, pw = ciz_durum(t, L)
    if popover:
        kapsam_popover(t, L, px, pw)
    if secsuz:
        ciz_secsuz(t, L)
    return t, L


def main():
    cik = KOK
    # 2× ana (hi-DPI) — şerit, panel ve kat kapsamı kırpmaları da bundan
    t2, L2 = sayfa(1920, 1080, 2)
    t2.kaydet(os.path.join(cik, 'ana-2x.png'))
    t2.kirp(0, 0, 1920, L2['serit_y1'] + 24).save(os.path.join(cik, 'detay-serit.png'))
    # panel kırpması: model ağacı + özellikler yan yana
    a = t2.kirp(L2['sol_x'] - 8, L2['govde_y0'] - 8, L2['sol_w'] + 16, 700)
    b = t2.kirp(L2['sag_x'] - 8, L2['govde_y0'] - 8, L2['sag_w'] + 16, 700)
    pan = Image.new('RGB', (a.width + b.width + 48, max(a.height, b.height) + 48), R['zemin'])
    pan.paste(a, (24, 24)); pan.paste(b, (a.width + 48, 24))
    pan.save(os.path.join(cik, 'detay-panel.png'))
    # 1× ana
    t1, _ = sayfa(1920, 1080, 1)
    t1.kaydet(os.path.join(cik, 'ana.png'))
    # kat kapsamı: 2×, balonlu, durum çubuğu kırpması
    tk, Lk = sayfa(1920, 1080, 2, popover=True, ipucu_goster=False)
    tk.kirp(1000, 1080 - 216, 920, 216).save(os.path.join(cik, 'kat-kapsami.png'))
    # küçük ekran
    ts, _ = sayfa(1366, 768, 1, kompakt=True, ipucu_goster=False)
    ts.kaydet(os.path.join(cik, 'kucuk.png'))
    # Seç & Süz
    tf, _ = sayfa(1920, 1080, 1, secsuz=True, ipucu_goster=False)
    tf.kaydet(os.path.join(cik, 'secsuz.png'))
    # Sonuç / Tasarım
    tr, _ = sayfa(1920, 1080, 1, sekme='Tasarım', mod='dc', ipucu_goster=False)
    tr.kaydet(os.path.join(cik, 'sonuc.png'))
    print('tamam')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'hizli':
        t, _ = sayfa(1920, 1080, 1)
        t.kaydet(os.path.join(KOK, 'ana.png'))
        print('ana.png')
    else:
        main()
