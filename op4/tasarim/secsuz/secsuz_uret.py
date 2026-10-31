#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
secsuz_uret.py — op4 "Seç & Süz" (hibrit: pratik ölçüt rafı + isteğe bağlı Gelişmiş kural katmanı) taslakları.

Atölye üretecinin (uret.py / tuval.py / sahne.py, bu klasördeki kopyalar) kromu, yazı ölçeği, simge dili ve 3B
görünümüyle çizilir. Renkler YALNIZ aşağıdaki PALET sözlüğündedir: yeni belirteçler gelince yalnız bu sözlük değişir.
Taslaktaki bütün sayılar ozn.py ile sahne modelinden hesaplanır (263 eleman, A–D × 1–5, 3 kat).

Çıktılar (bu klasöre): secsuz-pratik.png · secsuz-kat.png · secsuz-gelismis.png · sec-menusu.png · yuk-ata-hedef.png ·
                      karsilastirma.png (2400 px)
Çalıştırma: python3 secsuz_uret.py [--yalniz ad1,ad2]
"""
import os
import sys
import time
from PIL import Image, ImageDraw

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)

# ============================================================================
# PALET — tek yer. Nötr yüzeyler + tek soğuk vurgu (etkin/seçim). Ayrıntı: secsuz.md §15 (renkten bağımsız).
# ============================================================================
PALET = dict(
    zemin="#F3F4F6", yuzey="#FFFFFF", yuzey2="#F8F9FA", yuzey3="#EEF0F2",
    cizgi="#D7DAE0", cizgi2="#E6E8EC", giris_kenar="#C9CDD3",
    metin="#14181B", metin2="#4E545C", metin3="#868C95",
    vurgu="#2563EB", vurgu_ton="#EAF1FE", vurgu_ton2="#C8D9FB", vurgu_koyu="#1D4ED8",
    secim="#2563EB", secim_ton="#EEF4FF", secim_ton2="#D3E1FD",
    hover="#ECEEF1", odak="#2563EB", ok="#2E7D4F", uyari="#C7861B", hata="#B4443A",
    vp_ust="#FCFCFD", vp_alt="#E6E8EB",
    model_secim_dolgu="#D3E1FB", model_secim_kenar="#2563EB", model_hover="#334155",
    ipucu_zemin="#1F2937", ipucu_metin="#F9FAFB",
)

import tuval  # noqa: E402
import sahne  # noqa: E402

tuval.C.update({k: v for k, v in PALET.items() if k in tuval.C})
sahne.SECIM_DOLGU = PALET["model_secim_dolgu"]
sahne.SECIM_KENAR = PALET["model_secim_kenar"]
sahne.HOVER_KENAR = PALET["model_hover"]
import uret  # noqa: E402
uret.ALTIN = PALET["vurgu"]
uret.KAHVE = PALET["metin2"]

from tuval import C, Tuval, taban, hex2rgb, karisim, DC_RENK  # noqa: E402
from sahne import sahne_ciz, X_AKS, Y_AKS, Z_KAT, PROFILLER  # noqa: E402
from uret import Yerlesim, baslik_cubugu, ray, gorunum_sekmeleri, dock, durum_cubugu  # noqa: E402
import ozn  # noqa: E402

P = PALET
TABLO = ozn.tablo()


def rgba(h, a):
    return hex2rgb(h) + (int(round(a * 255)),)


# ============================================================================
# YERLEŞİM: Atölye iskeleti; Seç & Süz etkinken sağ panel 400 px (kullanıcı sürükleyerek değiştirir)
# ============================================================================
class Yer(Yerlesim):
    def __init__(self, W, H, ozel_w=400, dock_h=None):
        super().__init__(W, H, False, dock_h=dock_h)
        self.ozel_w = ozel_w
        self.vp_x1 = W - self.strip_w - self.ozel_w
        self.vp_w = self.vp_x1 - self.vp_x0


# ============================================================================
# KÜÇÜK BİLEŞENLER
# ============================================================================
def onay3(t, x, y, durum, boyut=12):
    """Üç durumlu onay kutusu: True / False / 'kismi'."""
    if durum is True:
        t.dikdortgen(x, y, boyut, boyut, dolgu=P["vurgu"], r=2)
        t.simge("onay", x + boyut / 2, y + boyut / 2, boyut - 2, "#FFFFFF", 1.8)
    elif durum == "kismi":
        t.dikdortgen(x, y, boyut, boyut, dolgu=P["vurgu"], r=2)
        t.yatay(x + 3, x + boyut - 3, y + boyut / 2 - 1, "#FFFFFF", 2)
    else:
        t.dikdortgen(x, y, boyut, boyut, dolgu=P["yuzey"], kenar="#B8BCC4", r=2)


def parcali(t, x, y, w, h, secenekler, etkin, boyut=11, esit=True, soluk=False):
    """Parçalı anahtar (Atölye durum çubuğu biçimi): etkin parça vurgu dolgulu, beyaz yazı."""
    t.dikdortgen(x, y, w, h, dolgu=P["yuzey"], kenar=P["cizgi"], r=3)
    if esit:
        ws = [(w - 2) / len(secenekler)] * len(secenekler)
    else:
        gs = [t.yazi_gen(s, boyut, 500) + 16 for s in secenekler]
        k = (w - 2) / sum(gs)
        ws = [g * k for g in gs]
    cx = x + 1
    for i, (s, ww) in enumerate(zip(secenekler, ws)):
        if i == etkin:
            t.dikdortgen(cx, y + 1, ww, h - 2, dolgu=P["vurgu"] if not soluk else "#B8BCC4", r=2)
            t.yazi_orta(cx + ww / 2, taban(y, h, boyut), s, boyut, 600, "#FFFFFF")
        else:
            if i > 0 and i - 1 != etkin:
                t.dikey(cx, y + 5, y + h - 5, P["cizgi2"])
            t.yazi_orta(cx + ww / 2, taban(y, h, boyut), s, boyut, 500, P["metin2"])
        cx += ww
    return ws


def cip(t, x, y, kategori, deger, h=22, kapat=True, soluk=False):
    """Ölçüt çipi: 'Kategori  değer ×'. Genişliği döndürür."""
    kw = t.yazi_gen(kategori, 10, 500)
    vw = t.yazi_gen(deger, 11, 600)
    w = 10 + kw + 6 + vw + (22 if kapat else 10)
    t.dikdortgen(x, y, w, h, dolgu=P["vurgu_ton"] if not soluk else P["yuzey2"], kenar=P["vurgu_ton2"] if not soluk else P["cizgi"], r=h / 2)
    t.yazi(x + 10, taban(y, h, 10), kategori, 10, 500, P["metin2"])
    t.yazi(x + 10 + kw + 6, taban(y, h, 11), deger, 11, 600, P["metin"])
    if kapat:
        t.simge("kapat", x + w - 12, y + h / 2, 9, P["metin2"], 1.6)
    return w


def ve_bag(t, x, y, h=22, metin="ve"):
    w = t.yazi_gen(metin, 10, 600) + 8
    t.yazi_orta(x + w / 2, taban(y, h, 10), metin, 10, 600, P["metin3"])
    return w


def sayim(t, xr, y, h, n, N, soluk=False, boyut=11):
    s2 = f" / {N}"
    w2 = t.yazi_gen(s2, boyut, 400, True)
    t.yazi(xr - w2, taban(y, h, boyut), s2, boyut, 400, P["metin3"], tnum=True)
    s1 = f"{n}"
    t.yazi_sag(xr - w2, taban(y, h, boyut), s1, boyut, 600, P["metin3"] if (soluk or n == 0) else P["metin"], tnum=True)


def bolum_etiketi(t, x, y, metin, h=20, renk=None):
    t.yazi(x, taban(y, h, 9.5), metin, 9.5, 600, renk or P["metin3"])


def kart(t, x, y, w, h, r=4, golge=True, kenar=None):
    if golge:
        t.golge(x, y, w, h, r=r, yaricap=6, alfa=0.18, dy=3)
    t.dikdortgen(x, y, w, h, dolgu=P["yuzey"], kenar=kenar or "#C4C8CF", r=r)


def ipucu(t, x, y, satirlar, okyon="sol", w=None):
    """Koyu ipucu balonu; satirlar: [(metin, ağırlık)]; (x, y) ok ucu."""
    bw = w or (max(t.yazi_gen(m, 10.5, a) for m, a in satirlar) + 20)
    bh = 8 + 16 * len(satirlar) + 4
    if okyon == "sol":
        bx, by = x + 7, y - bh / 2
        t.cokgen([(x, y), (bx + 1, y - 5), (bx + 1, y + 5)], dolgu=P["ipucu_zemin"])
    elif okyon == "sag":
        bx, by = x - 7 - bw, y - bh / 2
        t.cokgen([(x, y), (bx + bw - 1, y - 5), (bx + bw - 1, y + 5)], dolgu=P["ipucu_zemin"])
    else:  # alt: balon noktanın üstünde
        bx, by = x - bw / 2, y - 7 - bh
        t.cokgen([(x, y), (x - 5, by + bh - 1), (x + 5, by + bh - 1)], dolgu=P["ipucu_zemin"])
    t.golge(bx, by, bw, bh, r=4, yaricap=5, alfa=0.22)
    t.dikdortgen(bx, by, bw, bh, dolgu=P["ipucu_zemin"], r=4)
    yy = by + 6
    for m, a in satirlar:
        t.yazi(bx + 10, taban(yy, 16, 10.5), m, 10.5, a, P["ipucu_metin"] if a >= 500 else "#C9CED6")
        yy += 16
    return bx, by, bw, bh


def onizleme_etiketi(t, x, y, satirlar):
    """Görünümde hover önizlemesi etiketi: beyaz kart, koyu ince kenar; (x, y) hedef nokta."""
    bw = max(t.yazi_gen(m, 10.5, a) for m, a in satirlar) + 20
    bh = 8 + 16 * len(satirlar) + 2
    bx, by = x - bw - 40, y - bh - 34
    t.cizgi(bx + bw, by + bh, x, y, P["model_hover"], 1)
    t.daire(x, y, 3, dolgu=P["model_hover"])
    t.golge(bx, by, bw, bh, r=3, yaricap=4, alfa=0.16)
    t.dikdortgen(bx, by, bw, bh, dolgu=(255, 255, 255, 246), kenar=P["model_hover"], r=3)
    yy = by + 5
    for m, a in satirlar:
        t.yazi(bx + 10, taban(yy, 16, 10.5), m, 10.5, a, P["metin"] if a >= 500 else P["metin2"])
        yy += 16


def kucuk_dugme(t, x, y, w, h, simge, metin, etkin=False, boyut=11):
    t.dikdortgen(x, y, w, h, dolgu=P["vurgu_ton"] if etkin else P["yuzey"], kenar=P["vurgu_ton2"] if etkin else "#C9CDD3", r=3)
    tw = t.yazi_gen(metin, boyut, 500)
    sx = x + (w - (14 + 6 + tw)) / 2
    t.simge(simge, sx + 7, y + h / 2, 13, P["vurgu"] if etkin else "#3C4148", 1.4)
    t.yazi(sx + 20, taban(y, h, boyut), metin, boyut, 500, P["metin"])


def numara(t, x, y, n, metin):
    """Açıklama etiketi: vurgulu daire içinde numara + kısa metin (koyu balon)."""
    w = t.yazi_gen(metin, 11, 600) + 40
    t.golge(x, y, w, 24, r=12, yaricap=5, alfa=0.25)
    t.dikdortgen(x, y, w, 24, dolgu=P["ipucu_zemin"], r=12)
    t.daire(x + 12, y + 12, 8, dolgu=P["vurgu"])
    t.yazi_orta(x + 12, taban(y + 4, 16, 10), str(n), 10, 700, "#FFFFFF")
    t.yazi(x + 26, taban(y, 24, 11), metin, 11, 600, P["ipucu_metin"])
    return w


# ============================================================================
# ŞERİT (Atölye serit() + bölünmüş / basılı-açılır düğme ve etkin küçük düğme)
# ============================================================================
SEC_GRUBU = ("Seç", [("sec", "Seç", "acilir"), ("sec_suz", "Seç & Süz", "")],
             [("benzer", "Benzerini seç", False), ("katman", "Kata göre", True), ("ters", "Tersine çevir", False)], True)
GRUPLAR_MODEL = [g for g in uret.GRUPLAR_MODEL if g[0] not in ("Seç", "Kiriş")]
GRUPLAR_MODEL.insert(2, ("Kiriş", [("kiris", "Kiriş", "")], [("kiris_ana", "Ana kiriş", False), ("kiris_tali", "Tali kiriş", False), ("asik", "Aşık", False)], False))
GRUPLAR_MODEL.append(SEC_GRUBU)
GRUPLAR_YUKLER = [
    ("Desenler", [("yuk", "Yük desenleri", "")], [("tablo", "Yük durumları", False), ("tablo", "Kombinasyonlar", False), ("kutuphane", "Kütle kaynağı", False)], True),
    ("Geçerli desen", [("katman", "G · Sabit", "acilir")], [], False),
    ("Yük ata", [("yuk_nokta", "Düğüm yükü", ""), ("yuk", "Çubuk yükü", "basili"), ("doseme", "Alan yükü", "")],
     [("duvar", "Duvar yükü…", False), ("kopyala", "Atamaları kopyala", False), ("sil", "Atamaları sil", False)], True),
    ("Mesnet & temel", [("mesnet", "Mesnet ata", ""), ("temel", "Temel", "")],
     [("mafsal", "Uç serbestliği", False), ("rijit", "Rijit bölge", False), ("dugum", "Yay mesnet", False)], True),
    ("Göster", [("goz", "Yükleri göster", "")], [("etiket", "Değerler", False), ("katman", "Desene göre", True), ("kapat", "Gösterimi temizle", False)], False),
    SEC_GRUBU,
]


def serit(t, L, etkin="Model", gruplar=None, basili=None, kucuk_etkin=None):
    """Atölye serit(); `basili`: basılı büyük düğme etiketi, `kucuk_etkin`: etkin küçük düğme etiketi."""
    W = L.W
    y0 = L.baslik_h
    t.dikdortgen(0, y0, W, L.sekme_h, dolgu=P["zemin"])
    x = 8
    dw = 58
    t.dikdortgen(x, y0 + 4, dw, L.sekme_h - 4, dolgu=P["vurgu"], r=0)
    t.yazi_orta(x + dw / 2, taban(y0 + 4, L.sekme_h - 4, 12), "Dosya", 12, 600, "#FFFFFF")
    x += dw + 6
    govde_y = y0 + L.sekme_h
    for ad in uret.SEKMELER:
        tw = t.yazi_gen(ad, 12, 500)
        w = tw + 24
        if ad == etkin:
            t.dikdortgen(x, y0 + 4, w, L.sekme_h - 4 + 1, dolgu=P["yuzey"])
            t.dikey(x, y0 + 4, govde_y + 1, P["cizgi"]); t.dikey(x + w - 1, y0 + 4, govde_y + 1, P["cizgi"])
            t.yatay(x, x + w, y0 + 4, P["vurgu"], 2)
            t.yazi(x + 12, taban(y0 + 4, L.sekme_h - 4, 12), ad, 12, 600, P["metin"])
        else:
            t.yazi(x + 12, taban(y0 + 4, L.sekme_h - 4, 12), ad, 12, 500, P["metin2"])
        x += w
    t.simge("yardim", W - 18, y0 + L.sekme_h / 2 + 1, 14, P["metin3"], 1.3)
    t.simge("sevron_ust", W - 40, y0 + L.sekme_h / 2 + 1, 13, P["metin3"], 1.3)
    t.yazi_sag(W - 56, taban(y0, L.sekme_h, 11), "Şeridi özelleştir", 11, 400, P["metin3"])
    t.dikdortgen(0, govde_y, W, L.serit_h, dolgu=P["yuzey"])
    t.yatay(0, W, govde_y, P["cizgi"])
    t.yatay(0, W, govde_y + L.serit_h - 1, P["cizgi"])
    gy = govde_y
    x = 8
    konumlar = {}
    for gad, buyuk, kucukler, baslatici in gruplar:
        gx0 = x
        x += 6
        for ik, et, durum in buyuk:
            acilir = durum == "acilir"
            bas = (et == basili) or durum == "basili"
            bw = max(48, t.yazi_gen(et, 11, 500) + 16 + (10 if acilir else 0))
            if bas:
                t.dikdortgen(x, gy + 5, bw, 54, dolgu=P["vurgu_ton"], kenar=P["vurgu_ton2"], r=3)
            if acilir:   # bölünmüş düğme: üst yarı komut, alt şerit menü
                t.yatay(x + 4, x + bw - 4, gy + 39, P["vurgu_ton2"] if bas else P["cizgi2"])
            t.simge(ik, x + bw / 2 - (5 if acilir else 0), gy + 22, 24, P["vurgu"] if bas else "#2F343B", 1.5)
            t.yazi_orta(x + bw / 2 - (5 if acilir else 0), gy + 50, et, 11, 600 if bas else 500, P["metin"])
            if acilir:
                t.sevron(x + bw - 9, gy + 47, "asagi", 9, P["vurgu"] if bas else P["metin2"])
            konumlar[et] = (x, gy + 5, bw, 54)
            x += bw + 2
        if kucukler:
            x += 2
            kw = max(t.yazi_gen(et, 11, 400) for _, et, _ in kucukler) + 24 + (12 if any(a for _, _, a in kucukler) else 0)
            for j, (ik, et, acilir) in enumerate(kucukler):
                yy = gy + 6 + j * 18
                etk = et == kucuk_etkin
                if etk:
                    t.dikdortgen(x + 1, yy - 1, kw - 4, 18, dolgu=P["vurgu_ton"], kenar=P["vurgu_ton2"], r=3)
                t.simge(ik, x + 10, yy + 8, 14, P["vurgu"] if etk else "#3C4148", 1.4)
                t.yazi(x + 22, taban(yy, 16, 11), et, 11, 600 if etk else 400, P["metin"])
                if acilir:
                    t.sevron(x + 22 + t.yazi_gen(et, 11, 400) + 8, yy + 9, "asagi", 9, P["metin3"])
                konumlar[et] = (x, yy, kw, 18)
            x += kw
        x += 6
        gw = x - gx0
        t.yazi_orta(gx0 + gw / 2, gy + 71, gad, 10, 400, P["metin3"])
        if baslatici:
            t.simge("sevron_sag", x - 8, gy + 68, 8, P["metin3"], 1.6)
        t.dikey(x, gy + 8, gy + L.serit_h - 8, P["cizgi2"])
        x += 1
    return konumlar


# ============================================================================
# MODEL AĞACI (satırlar parametreli; seçim rozetleri hesaplanmış sayılarla)
# ============================================================================
def model_agaci(t, L, satirlar, ozet):
    x0, y0, w, h = L.ray_w, L.ust, L.agac_w, L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=P["yuzey"])
    t.dikey(x0 + w - 1, y0, y0 + h, P["cizgi"])
    t.dikdortgen(x0, y0, w, 28, dolgu=P["yuzey2"])
    t.yatay(x0, x0 + w, y0 + 27, P["cizgi2"])
    t.yazi(x0 + 10, taban(y0, 28, 12), "Model ağacı", 12, 600, P["metin"])
    t.simge("pin", x0 + w - 36, y0 + 14, 13, P["metin3"], 1.3)
    t.simge("kapat", x0 + w - 16, y0 + 14, 12, P["metin3"], 1.3)
    ty = y0 + 28
    t.yatay(x0, x0 + w, ty + 23, P["cizgi2"])
    x = x0 + 8
    for ad in ("Model", "Göster", "Tablolar", "Raporlar"):
        tw = t.yazi_gen(ad, 11, 500)
        if ad == "Model":
            t.yazi(x, taban(ty, 24, 11), ad, 11, 600, P["metin"])
            t.yatay(x - 2, x + tw + 2, ty + 21, P["vurgu"], 2)
        else:
            t.yazi(x, taban(ty, 24, 11), ad, 11, 500, P["metin2"])
        x += tw + 18
    sy = ty + 24 + 6
    t.dikdortgen(x0 + 8, sy, w - 16, 22, dolgu=P["yuzey"], kenar=P["cizgi"], r=3)
    t.simge("ara", x0 + 20, sy + 11, 12, P["metin3"], 1.3)
    t.yazi(x0 + 30, taban(sy, 22, 11), "Ağaçta ara (ad, kesit, etiket)", 11, 400, P["metin3"])
    y = sy + 22 + 6
    rh = 20
    for derin, ik, metin, sag, durum, acik, rozet in satirlar:
        if y + rh > L.alt - 28:
            break
        if durum == "secili":
            t.dikdortgen(x0, y, w - 1, rh, dolgu=P["secim_ton"])
            t.dikey(x0, y, y + rh, P["secim"], 2)
        elif durum == "etkin":
            t.dikdortgen(x0, y, w - 1, rh, dolgu=P["yuzey2"])
        ix = x0 + 10 + derin * 14
        if acik is not None:
            t.sevron(ix + 4, y + rh / 2, "asagi" if acik else "sag", 9, P["metin3"])
        t.simge(ik, ix + 20, y + rh / 2, 13, P["vurgu"] if durum == "secili" else "#4E545C", 1.3)
        agir = 600 if derin == 0 or durum == "etkin" else 400
        sw = t.yazi_gen(sag, 11, 400, True) + 10 if sag else 0
        rw = (t.yazi_gen(rozet, 9, 600) + 12 + 6) if rozet else 0
        maxw = w - (ix + 30 - x0) - 12 - sw - rw - (16 if durum == "etkin" else 0)
        t.yazi(ix + 30, taban(y, rh, 12), t.yazi_kes(metin, maxw, 12, agir), 12, agir, P["metin"])
        xr = x0 + w - 12
        if sag:
            t.yazi_sag(xr, taban(y, rh, 11), sag, 11, 400, P["metin2"] if durum == "etkin" else P["metin3"], tnum=True)
            xr -= sw
        if durum == "etkin":
            t.simge("goz", xr - 6, y + rh / 2, 12, P["metin3"], 1.3)
            xr -= 18
        if rozet:
            bw = t.yazi_gen(rozet, 9, 600) + 12
            t.dikdortgen(xr - bw, y + 3, bw, rh - 6, dolgu=P["secim"], r=7)
            t.yazi_orta(xr - bw / 2, taban(y + 3, rh - 6, 9), rozet, 9, 600, "#FFFFFF", tnum=True)
        y += rh
    oy = L.alt - 24
    t.yatay(x0, x0 + w - 1, oy, P["cizgi2"])
    t.yazi(x0 + 10, taban(oy, 24, 11), ozet, 11, 400, P["metin3"], tnum=True)


def agac_alt(satirlar_ust):
    """Ortak alt düğümler (kütüphane, yükler, gruplar, süzgeçler)."""
    return satirlar_ust + [
        (1, "kesit", "Kesitler", "5", "", False, None),
        (1, "malzeme", "Malzemeler", "4", "", False, None),
        (1, "yuk", "Yük desenleri", "5", "", False, None),
        (1, "tablo", "Kombinasyonlar", "14", "", False, None),
        (1, "grup", "Gruplar", "4", "", False, None),
        (1, "suz", "Süzgeçler", "2", "", False, None),
        (1, "analiz", "Analiz modeli", "", "", None, None),
    ]


# ============================================================================
# PENCERE ŞERİDİ: Seç & Süz kendi penceresi (Filtre & görünürlük → Görünürlük)
# ============================================================================
PENCERELER = [("etiket", "Özellikler"), ("sec_suz", "Seç & Süz"), ("kutuphane", "Kataloglar"), ("katman", "Model ağacı"),
              ("goz", "Görünürlük"), ("sorgu", "Sorgu")]


def pencere_seridi(t, L, etkin="Seç & Süz"):
    x0, y0, w, h = L.W - L.strip_w, L.ust, L.strip_w, L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=P["zemin"])
    t.dikey(x0, y0, y0 + h, P["cizgi"])
    y = y0 + 8
    for ik, ad in PENCERELER:
        th = t.yazi_gen(ad, 11, 500) + 34
        if ad == etkin:
            t.dikdortgen(x0 + 1, y, w - 1, th, dolgu=P["secim_ton"])
            t.dikey(x0 + w - 3, y, y + th, P["secim"], 3)
            t.simge(ik, x0 + w / 2, y + 12, 14, P["vurgu"], 1.5)
            t.yazi_dikey(x0 + w / 2 - 8, y + 24, ad, 11, 600, P["metin"])
        else:
            t.simge(ik, x0 + w / 2, y + 12, 14, P["metin2"], 1.4)
            t.yazi_dikey(x0 + w / 2 - 8, y + 24, ad, 11, 500, P["metin2"])
            if ad == "Model ağacı":
                t.simge("sol_yapistir", x0 + w / 2, y + th - 8, 9, P["metin3"], 1.2)
        y += th + 6
    t.yatay(x0 + 6, x0 + w - 6, y, P["cizgi"])
    t.simge("sevron_cift_asagi", x0 + w / 2, y + 16, 12, P["metin3"], 1.3)


# ============================================================================
# 3B GÖRÜNÜM (sahne yüklemle) + Atölye görünüm pili
# ============================================================================
_SAHNE = {}


def gorunum(t, L, anahtar, secim_fn=None, hover_fn=None, pil_kat="Tüm katlar"):
    x0, y0, w, h = L.vp_x0, L.vp_y0, L.vp_w, L.vp_h
    k = (anahtar, w, h, t.s)
    sc = _SAHNE.get(k)
    if sc is None:
        sc = sahne_ciz(w, h, t.s, ss=2, mod="ozel", secim_fn=secim_fn, hover_fn=hover_fn)
        _SAHNE[k] = sc
    t.yapistir(sc.im, x0, y0)

    def iz(p):
        q = sc.iz(p)
        return (x0 + q[0], y0 + q[1])

    px, py = x0 + 10, y0 + 10
    parcalar = [("bina3", "3B", True), ("perspektif", "Perspektif", True), ("katman", pil_kat, True), ("etiket", "Renk: türe göre", True)]
    pw = 10
    for ik, et, ac in parcalar:
        pw += 18 + t.yazi_gen(et, 11, 500) + (12 if ac else 0) + 16
    pw += 62
    t.golge(px, py, pw, 26, r=13, yaricap=4, alfa=0.10)
    t.dikdortgen(px, py, pw, 26, dolgu=(255, 255, 255, 238), kenar=P["cizgi"], r=13)
    cx = px + 10
    for ik, et, ac in parcalar:
        t.simge(ik, cx + 7, py + 13, 14, P["metin2"], 1.3)
        t.yazi(cx + 18, taban(py, 26, 11), et, 11, 500, P["metin"])
        cx += 18 + t.yazi_gen(et, 11, 500)
        if ac:
            t.sevron(cx + 6, py + 13.5, "asagi", 9, P["metin3"]); cx += 12
        cx += 8
        t.dikey(cx, py + 6, py + 20, P["cizgi2"]); cx += 8
    t.dikdortgen(cx, py + 4, 52, 18, dolgu=P["zemin"], kenar=P["cizgi"], r=9)
    t.dikdortgen(cx + 26, py + 5, 25, 16, dolgu=P["vurgu"], r=8)
    t.simge("cubuk", cx + 13, py + 13, 12, P["metin2"], 1.4)
    t.simge("kati", cx + 38, py + 13, 12, "#FFFFFF", 1.4)
    for i, ad in enumerate(("ev", "sigdir", "kesit_duzlemi", "goz")):
        bx = x0 + w - 10 - (4 - i) * 26
        t.dikdortgen(bx, py, 24, 24, dolgu=(255, 255, 255, 236), kenar=P["cizgi"], r=3)
        t.simge(ad, bx + 12, py + 12, 14, P["metin2"], 1.3)
    ox, oy = x0 + 36, y0 + h - 36
    for ad, v, renk in (("X", (1, 0, 0), "#B4443A"), ("Y", (0, 1, 0), "#2E7D4F"), ("Z", (0, 0, 1), "#2F5FA8")):
        dx, dy = sc.eksen_vektor(v)
        Ln = (dx * dx + dy * dy) ** 0.5 or 1
        ex, ey = ox + dx / Ln * 24, oy - dy / Ln * 24
        t.cizgi(ox, oy, ex, ey, renk, 1.5)
        t.yazi(ex + dx / Ln * 9 - 3.5, ey - dy / Ln * 9 + 4, ad, 10, 600, renk)
    t.daire(ox, oy, 2.2, dolgu=P["metin2"])
    t.yazi_sag(x0 + w - 12, y0 + h - 12, "Perspektif 30° · Bakış: güney-batı · Orta tuş: kaydır · Ctrl+orta: döndür", 10, 400, P["metin3"])
    return sc, iz


def secim_rozeti(t, L, metin, alt):
    """Görünüm üstünde (pilin sağında) seçim özeti — Atölye mini araç çubuğunun çoklu tür karşılığı."""
    x0, y0 = L.vp_x0, L.vp_y0
    px = x0 + 10 + 452
    py = y0 + 10
    w = t.yazi_gen(metin, 11, 600) + t.yazi_gen(alt, 11, 400) + 44
    t.golge(px, py, w, 26, r=13, yaricap=4, alfa=0.10)
    t.dikdortgen(px, py, w, 26, dolgu=(255, 255, 255, 240), kenar=P["vurgu_ton2"], r=13)
    t.daire(px + 13, py + 13, 4, dolgu=P["vurgu"])
    t.yazi(px + 24, taban(py, 26, 11), metin, 11, 600, P["metin"])
    t.yazi(px + 30 + t.yazi_gen(metin, 11, 600), taban(py, 26, 11), alt, 11, 400, P["metin2"])


# ============================================================================
# KOMUT SATIRI (Atölye) — isteğe bağlı komut seçenekleri (Hedef pilleri)
# ============================================================================
def komut_satiri(t, L, komut=None, metin="", son="", secenekler=None, etkin_secenek=None, ipuclari=None, degerli=()):
    x0, y0, w, h = L.ray_w, L.alt + L.dock_tab_h + L.dock_h, L.W - L.ray_w, L.komut_h
    t.dikdortgen(x0, y0, w, h, dolgu=P["yuzey"])
    t.yatay(x0, x0 + w, y0, P["cizgi"])
    t.yatay(x0, x0 + w, y0 + h - 1, P["cizgi"])
    t.dikey(x0, y0, y0 + h, P["vurgu"], 3)
    t.yazi(x0 + 14, taban(y0, h, 12), "Komut:", 12, 600, P["vurgu"])
    x = x0 + 14 + t.yazi_gen("Komut:", 12, 600) + 8
    konum = {}
    if komut:
        t.yazi(x, taban(y0, h, 12), komut, 12, 600, P["metin"])
        x += t.yazi_gen(komut, 12, 600) + 10
    if secenekler:
        for s in secenekler:
            if s == "|":
                t.dikey(x + 2, y0 + 8, y0 + h - 8, P["cizgi"]); x += 10; continue
            if s.endswith(":"):
                t.yazi(x, taban(y0, h, 12), s, 12, 400, P["metin2"]); x += t.yazi_gen(s, 12, 400) + 6; continue
            sw = t.yazi_gen(s, 11, 500) + 16
            et = s == etkin_secenek
            dg = s in degerli
            t.dikdortgen(x, y0 + 5, sw, h - 10, dolgu=P["vurgu"] if et else (P["vurgu_ton"] if dg else P["zemin"]),
                         kenar=P["vurgu"] if et else (P["vurgu_ton2"] if dg else P["cizgi"]), r=3)
            t.yazi(x + 8, taban(y0 + 5, h - 10, 11), s, 11, 600 if (et or dg) else 500, "#FFFFFF" if et else P["metin"])
            konum[s] = (x, y0 + 5, sw, h - 10)
            x += sw + 4
        x += 4
    if metin:
        t.yazi(x, taban(y0, h, 12), metin, 12, 400, P["metin"])
        x += t.yazi_gen(metin, 12, 400) + 1
    t.dikey(x, y0 + 8, y0 + h - 8, P["metin"], 1)
    x += 12
    if son:
        t.yazi(x, taban(y0, h, 12), "·", 12, 400, P["metin3"]); x += 12
        t.yazi(x, taban(y0, h, 12), son, 12, 400, P["metin3"])
    ip = ipuclari or [("Ctrl+Q", "odakla / hızlı başlat"), ("Tab", "tamamla"), ("Enter", "yinele"), ("Esc", "iptal")]
    xr = x0 + w - 12
    for k, et in reversed(ip):
        tw = t.yazi_gen(et, 10, 400)
        xr -= tw
        t.yazi(xr, taban(y0, h, 10), et, 10, 400, P["metin3"])
        kw = t.yazi_gen(k, 10, 500) + 8
        xr -= kw + 4
        t.kisayol(xr, y0 + 7, k, 10, 15)
        xr -= 14
    return konum


# ============================================================================
# SEÇ & SÜZ PANELİ
# ============================================================================
KATEGORI_SUTUNU = [
    ("TEMEL", [("tur", "tur", "Nesne türü"), ("kat", "kat", "Kat"), ("kesit", "kesit", "Kesit"), ("malzeme", "malzeme", "Malzeme"),
               ("yer", "kullanim", "Kullanım yeri")]),
    ("KONUM VE GEOMETRİ", [("aks", "aks", "Aks"), ("dogrultu", "dogrultu", "Doğrultu"), ("duzlem", "duzlem", "Düzlem"),
                           ("uzunluk", "uzunluk", "Uzunluk")]),
    ("ATAMA", [("grup", "grup", "Grup / süzgeç"), ("etiket", "etiket", "Etiket"), ("yuk", "yuk", "Yük deseni"),
               ("serbestlik", "mesnet", "Mesnet / serbestlik")]),
    ("SONUÇ", [("dc", "dc", "D/C aralığı")]),
]
KIPLER = ["Yeni seçim", "Ekle", "Çıkar", "Kesişim"]


def panel_iskelet(t, L, baslik="Seç & Süz", simge="sec_suz"):
    x0, y0, w, h = L.vp_x1, L.ust, L.ozel_w, L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=P["yuzey"])
    t.dikey(x0, y0, y0 + h, P["cizgi"])
    t.dikdortgen(x0 + 1, y0, w - 1, 28, dolgu=P["yuzey2"])
    t.yatay(x0, x0 + w, y0 + 27, P["cizgi2"])
    t.simge(simge, x0 + 20, y0 + 14, 14, P["vurgu"], 1.5)
    t.yazi(x0 + 34, taban(y0, 28, 12), baslik, 12, 600, P["metin"])
    t.simge("pin", x0 + w - 36, y0 + 14, 13, P["metin3"], 1.3)
    t.simge("kapat", x0 + w - 16, y0 + 14, 12, P["metin3"], 1.3)
    return x0, y0, w, h


def ust_bolum(t, L, x0, y0, w, kip, olcut_cipleri, sonuc, gelismis):
    """Kip anahtarı + ölçüt çipleri + sonuç kutusu. Döndürür: alt y."""
    y = y0 + 28 + 8
    t.yazi(x0 + 12, taban(y, 22, 11), "Kip", 11, 500, P["metin2"])
    parcali(t, x0 + 46, y, w - 58, 22, KIPLER, kip, 11)
    y += 22 + 10
    t.yatay(x0 + 12, x0 + w - 12, y, P["cizgi2"])
    y += 6
    bolum_etiketi(t, x0 + 12, y, "ÖLÇÜTLER" if not gelismis else "ÖLÇÜTLER → KURAL SATIRLARI")
    # Gelişmiş anahtarı
    gx = x0 + w - 12
    tw = t.yazi_gen("Gelişmiş", 11, 500)
    t.yazi(gx - tw, taban(y, 20, 11), "Gelişmiş", 11, 600 if gelismis else 500, P["metin"] if gelismis else P["metin2"])
    t.anahtar(gx - tw - 32, y + 3, gelismis, 24, 13)
    if not gelismis:
        t.kisayol(gx - tw - 32 - 8 - t.yazi_gen("Ctrl+Shift+F", 9, 500) - 8, y + 3, "Ctrl+Shift+F", 9, 14)
    y += 22
    if not gelismis:
        # çipler: kategoriler arası "ve", kategori içi "veya"
        cx = x0 + 12
        sinir = x0 + w - 12 - t.yazi_gen("Temizle", 10.5, 500) - 10
        for i, (kat, deg) in enumerate(olcut_cipleri):
            cw = 10 + t.yazi_gen(kat, 10, 500) + 6 + t.yazi_gen(deg, 11, 600) + 22
            vw = (t.yazi_gen("ve", 10, 600) + 12) if i else 0
            if i and cx + vw + cw > sinir:
                cx = x0 + 12; y += 26
                cx += ve_bag(t, cx, y) + 2
            elif i:
                cx += ve_bag(t, cx + 2, y) + 4
            cx += cip(t, cx, y, kat, deg)
        t.yazi_sag(x0 + w - 12, taban(y, 22, 10.5), "Temizle", 10.5, 500, P["vurgu"])
        y += 22 + 8
    # sonuç kutusu
    bas, alt = sonuc
    t.dikdortgen(x0 + 12, y, w - 24, 44, dolgu=P["secim_ton"], kenar=P["secim_ton2"], r=3)
    t.simge("dogrula", x0 + 28, y + 22, 16, P["vurgu"], 1.5)
    t.yazi(x0 + 44, y + 18, bas, 12, 600, P["metin"], tnum=True)
    t.yazi(x0 + 44, y + 34, t.yazi_kes(alt, w - 24 - 44, 10, 400), 10, 400, P["metin2"], tnum=True)
    return y + 44 + 10


def kategori_sutunu(t, x, y, w, h, aktif, suz, etkin_sayi):
    """Sol ölçüt kategorileri sütunu. etkin_sayi: {kategori: işaretli değer sayısı}."""
    t.dikdortgen(x, y, w, h, dolgu=P["yuzey2"])
    t.dikey(x + w - 1, y, y + h, P["cizgi2"])
    yy = y + 4
    for gad, ogeler in KATEGORI_SUTUNU:
        bolum_etiketi(t, x + 10, yy, gad, 20)
        yy += 20
        for anahtar, ik, ad in ogeler:
            rh = 24
            if anahtar == aktif:
                t.dikdortgen(x, yy, w - 1, rh, dolgu=P["yuzey"])
                t.yatay(x, x + w - 1, yy, P["cizgi2"]); t.yatay(x, x + w - 1, yy + rh - 1, P["cizgi2"])
                t.dikey(x, yy, yy + rh, P["vurgu"], 2)
            soluk = anahtar == "dc" and False
            t.simge(ik, x + 18, yy + rh / 2, 13, P["vurgu"] if anahtar == aktif else "#4E545C", 1.35)
            t.yazi(x + 32, taban(yy, rh, 11.5), t.yazi_kes(ad, w - 32 - 18, 11.5, 600 if anahtar == aktif else 400), 11.5,
                   600 if anahtar == aktif else 400, P["metin"] if not soluk else P["metin3"])
            n = etkin_sayi.get(anahtar)
            if n:
                s = str(n)
                bw = max(16, t.yazi_gen(s, 9, 600) + 10)
                t.dikdortgen(x + w - 10 - bw, yy + 5, bw, rh - 10, dolgu=P["vurgu"], r=7)
                t.yazi_orta(x + w - 10 - bw / 2, taban(yy + 5, rh - 10, 9), s, 9, 600, "#FFFFFF", tnum=True)
            else:
                s = str(suz.deger_sayisi(anahtar))
                t.yazi_sag(x + w - 10, taban(yy, rh, 10), s, 10, 400, P["metin3"], tnum=True)
            yy += rh
        yy += 2
    t.simge("artı", x + 18, yy + 12, 11, P["vurgu"], 1.5)
    t.yazi(x + 32, taban(yy, 24, 11), "Özellik ekle…", 11, 500, P["vurgu"])
    yy += 24
    return yy


def hizli_eylemler(t, x0, y, w, etkin=None):
    bolum_etiketi(t, x0 + 12, y, "HIZLI EYLEMLER")
    y += 20
    satir1 = [("tumu", "Tümü"), ("ters", "Tersine çevir"), ("gecmis", "Önceki"), ("silgi", "Temizle")]
    satir2 = [("benzer", "Benzerini seç"), ("goz", "Yalnız seçili"), ("grup", "Grup olarak kaydet…")]
    konum = {}
    for satir in (satir1, satir2):
        gs = [t.yazi_gen(m, 11, 500) + 14 + 6 + 20 for _, m in satir]
        bos = (w - 24 - 4 * (len(satir) - 1) - sum(gs)) / len(satir)
        cx = x0 + 12
        for (ik, m), g in zip(satir, gs):
            bw = g + bos
            kucuk_dugme(t, cx, y, bw, 24, ik, m, etkin=(m == etkin))
            konum[m] = (cx, y, bw, 24)
            cx += bw + 4
        y += 28
    return y, konum


def alt_cubuk(t, x0, y0, w, h):
    fy = y0 + h - 40
    t.dikdortgen(x0 + 1, fy, w - 1, 40, dolgu=P["yuzey2"])
    t.yatay(x0, x0 + w, fy, P["cizgi"])
    t.onay_kutusu(x0 + 12, fy + 14, True, 12)
    t.yazi(x0 + 30, taban(fy, 40, 11), "Yalnız görünenler", 11, 400, P["metin"])
    ax = x0 + 30 + t.yazi_gen("Yalnız görünenler", 11, 400) + 18
    t.anahtar(ax, fy + 13, True, 24, 13)
    t.yazi(ax + 30, taban(fy, 40, 11), "Anında uygula", 11, 400, P["metin2"])
    t.dugme(x0 + w - 12 - 64, fy + 9, 64, 22, "Kapat")


def deger_listesi_kesit(t, x, y, w, suz, isaretli, hover=None):
    """Kesit değer listesi: aile grupları + üç durumlu onay + n / N."""
    sayi = suz.sayim("kesit")
    aileler = [("HEA", ["HE340A"]), ("IPE", ["IPE400", "IPE200"]), ("L köşebent", ["L100x10"]), ("Kutu", ["KUTU 80x4"])]
    yy = y
    konum = {}
    for aile, uyeler in aileler:
        rh = 20
        isa = [u in isaretli for u in uyeler]
        d = True if all(isa) else ("kismi" if any(isa) else False)
        n = sum(sayi[u][0] for u in uyeler); N = sum(sayi[u][1] for u in uyeler)
        t.sevron(x + 6, yy + rh / 2, "asagi", 8, P["metin3"])
        onay3(t, x + 14, yy + 4, d, 12)
        t.yazi(x + 32, taban(yy, rh, 10.5), aile, 10.5, 600, P["metin2"])
        sayim(t, x + w, yy, rh, n, N, boyut=10)
        yy += rh
        for u in uyeler:
            rh = 22
            n, N = sayi[u]
            if u == hover:
                t.dikdortgen(x - 6, yy, w + 12, rh, dolgu=P["hover"], r=3)
            onay3(t, x + 28, yy + 5, u in isaretli, 12)
            t.yazi(x + 46, taban(yy, rh, 12), u, 12, 500 if u in isaretli else 400, P["metin"] if n else P["metin3"])
            sayim(t, x + w, yy, rh, n, N, soluk=(n == 0))
            konum[u] = (x - 6, yy, w + 12, rh)
            yy += rh
        yy += 2
    return yy, konum


def secsuz_pratik(t, L, kip=0, aktif="kesit", olcut=None, cipler=(), hover_deger=None, sonuc=None, govde=None):
    x0, y0, w, h = panel_iskelet(t, L)
    suz = ozn.Suzgec(TABLO, olcut or {})
    y = ust_bolum(t, L, x0, y0, w, kip, cipler, sonuc, False)
    t.yatay(x0, x0 + w, y, P["cizgi"])
    gov_y0 = y
    alt_y = y0 + h - 40 - 82          # hızlı eylemler bloğu
    kw = 160
    etkin_sayi = {k: len(v) for k, v in (olcut or {}).items() if v}
    kategori_sutunu(t, x0 + 1, gov_y0 + 1, kw, alt_y - gov_y0 - 1, aktif, suz, etkin_sayi)
    lx = x0 + 1 + kw + 12
    lw = w - kw - 1 - 24
    sonuc_konum = govde(t, lx, gov_y0, lw, alt_y, suz) if govde else {}
    t.yatay(x0, x0 + w, alt_y, P["cizgi"])
    _, hk = hizli_eylemler(t, x0, alt_y + 4, w)
    alt_cubuk(t, x0, y0, w, h)
    return suz, sonuc_konum, hk


def liste_basligi(t, x, y, w, baslik, sag, arama):
    t.yazi(x, taban(y, 26, 12.5), baslik, 12.5, 600, P["metin"])
    t.yazi_sag(x + w, taban(y, 26, 10), sag, 10, 400, P["metin3"])
    y += 26
    t.dikdortgen(x, y, w, 22, dolgu=P["yuzey"], kenar=P["cizgi"], r=3)
    t.simge("ara", x + 12, y + 11, 12, P["metin3"], 1.3)
    t.yazi(x + 23, taban(y, 22, 11), arama, 11, 400, P["metin3"])
    return y + 22 + 6


def baglantilar(t, x, y, w, sol, sag):
    cx = x
    for i, s in enumerate(sol):
        if i:
            t.yazi(cx, taban(y, 18, 10.5), "·", 10.5, 400, P["metin3"]); cx += 9
        t.yazi(cx, taban(y, 18, 10.5), s, 10.5, 500, P["vurgu"])
        cx += t.yazi_gen(s, 10.5, 500) + 6
    if sag.endswith(" ▾"):
        sag = sag[:-2]
        t.sevron(x + w - 4, y + 9.5, "asagi", 8, P["metin3"])
        t.yazi_sag(x + w - 12, taban(y, 18, 9.5), sag, 9.5, 400, P["metin3"])
    else:
        t.yazi_sag(x + w, taban(y, 18, 9.5), sag, 9.5, 400, P["metin3"])
    t.yatay(x, x + w, y + 20, P["cizgi2"])
    return y + 24


# ============================================================================
# EKRANLAR
# ============================================================================
def ortak_ust(t, L, sekme="Model", gruplar=None, basili=None, kucuk_etkin=None):
    baslik_cubugu(t, L)
    kon = serit(t, L, etkin=sekme, gruplar=gruplar or GRUPLAR_MODEL, basili=basili, kucuk_etkin=kucuk_etkin)
    ray(t, L)
    gorunum_sekmeleri(t, L)
    return kon


def ekran_pratik(s=1):
    """1) Pratik katman: Kesit kategorisi, HE340A + IPE400 işaretli, Kat 2 çipi, 51 eleman; IPE200 satırı üzerinde."""
    L = Yer(1920, 1080)
    t = Tuval(1920, 1080, s)
    ortak_ust(t, L, kucuk_etkin=None, basili="Seç & Süz")
    olcut = {"kat": {"Kat 2"}, "kesit": {"HE340A", "IPE400"}}
    suz = ozn.Suzgec(TABLO, olcut)
    es = suz.eslesen()
    n = len(es)
    sc, iz = gorunum(t, L, "pratik", secim_fn=lambda e: e.kat == 2 and e.tur in ("kolon", "kiris"),
                     hover_fn=lambda e: e.kat == 2 and e.tur == "capraz" and len(e.profil) != 4)
    secim_rozeti(t, L, f"Seçim: {n} eleman", f"{ozn.ozet(es)} · Kat 2")
    agac = agac_alt([
        (0, "proje", uret.PROJE, "", "", True, None),
        (1, "aks", "Aks sistemi", "A–D × 1–5", "", None, None),
        (1, "kat", "Katlar", "3", "", True, None),
        (2, "kat", "Kat 3 (Çatı)", "+13,50", "", False, None),
        (2, "kat", "Kat 2", "+9,00", "etkin", True, None),
        (3, "kolon", "Kolonlar", "20", "secili", False, "20 seçili"),
        (3, "kiris", "Kirişler · IPE400", "31", "secili", False, "31 seçili"),
        (3, "kiris_tali", "Tali kirişler", "12", "", False, None),
        (3, "capraz", "Çaprazlar", "8", "", False, None),
        (3, "doseme", "Döşemeler", "1", "", False, None),
        (2, "kat", "Kat 1", "+4,50", "", False, None),
        (2, "kat", "Zemin", "±0,00", "", False, None),
    ])
    model_agaci(t, L, agac, f"263 eleman · 80 düğüm · 3 kat · {n} seçili")

    def govde(t, x, y, w, ymax, suz):
        y = liste_basligi(t, x, y + 6, w, "Kesit", "n: Kat 2 ile  ·  N: modelde", "Kesit ara — HE340A, IPE 4*")
        y = baglantilar(t, x, y, w, ["Tümü", "Hiçbiri", "Ters"], "aileye göre ▾")
        y2, kon = deger_listesi_kesit(t, x, y + 2, w, suz, olcut["kesit"], hover="L100x10")
        # açıklama kutusu: birleştirme kuralı + tık değiştiricileri
        y2 += 8
        t.dikdortgen(x, y2, w, 62, dolgu=P["yuzey2"], kenar=P["cizgi2"], r=3)
        t.simge("bilgi", x + 12, y2 + 13, 12, P["metin3"], 1.3)
        t.yazi(x + 24, taban(y2 + 4, 18, 10), "Aynı ölçütte işaretliler: veya", 10, 600, P["metin2"])
        t.yazi(x + 24, taban(y2 + 21, 16, 10), "Ölçütler arasında: ve (kesişim)", 10, 600, P["metin2"])
        t.yazi(x + 24, taban(y2 + 39, 16, 10), "Ctrl+tık: ekle · Shift+tık: çıkar", 10, 400, P["metin3"])
        # son kullanılan bileşimler (tek tıkla geri çağır)
        y2 += 62 + 14
        bolum_etiketi(t, x, y2, "SON KULLANILANLAR")
        y2 += 20
        for metin, sayi_ in (("Kat 2 ve IPE400", "31"), ("köşe kolon · Benzer katlar", "12"), ("D/C 0,90 – 1,00 veya > 1,00", "4")):
            t.dikdortgen(x, y2, w, 22, dolgu=P["yuzey"], kenar=P["cizgi2"], r=3)
            t.simge("gecmis", x + 11, y2 + 11, 11, P["metin3"], 1.3)
            t.yazi(x + 22, taban(y2, 22, 10.5), t.yazi_kes(metin, w - 60, 10.5, 500), 10.5, 500, P["metin"])
            t.yazi_sag(x + w - 8, taban(y2, 22, 10.5), sayi_, 10.5, 600, P["metin2"], tnum=True)
            y2 += 26
        return kon

    suz, kon, hk = secsuz_pratik(t, L, kip=0, aktif="kesit", olcut=olcut,
                                 cipler=[("Kat", "2"), ("Kesit", "HE340A veya IPE400")],
                                 sonuc=(f"{n} eleman eşleşiyor → yeni seçim: {n}", f"{ozn.ozet(es)} · Kat 2 · önceki seçim: 6 kiriş (Ctrl+J)"),
                                 govde=govde)
    # L100x10 satırı üzerinde: modelde canlı önizleme (ince koyu kontur) + etiket
    nL = suz.sayim("kesit")["L100x10"][0]
    hed = [e for e in sc.elemanlar if e.durum == "hover"]
    ort = [sum(e.orta()[i] for e in hed if e.p0[0] < 1) / max(1, sum(1 for e in hed if e.p0[0] < 1)) for i in range(3)]
    q = iz(tuple(ort))
    onizleme_etiketi(t, q[0], q[1], [(f"Önizleme · L100x10: +{nL} çapraz → {n + nL}", 600),
                                     ("Tık: Kesit ölçütüne ekler (veya)", 400)])
    rx, ry, rw, rh = kon["L100x10"]
    t.simge("imlec", rx + rw - 64, ry + rh / 2 + 6, 16, "#14181B", 1.2)
    pencere_seridi(t, L, "Seç & Süz")
    dock(t, L, satirlar=[
        ("SEÇ&SÜZ", f"kat = Kat 2 ve kesit içinde [HE340A, IPE400] → {n} eleman ({ozn.ozet(es)}) · kip: Yeni seçim", "0,4 ms · 263 satır", "ok"),
        ("SEÇ", "6 nesne seçildi: Kiriş ×6 · Kat 2 · Aks 1–2", "Ctrl+J: önceki seçime dön", ""),
    ])
    komut_satiri(t, L, son=f"Son: SEÇ&SÜZ — {n} eleman seçildi (Kat 2 · HE340A, IPE400)")
    durum_cubugu(t, L, kapsam="Bu kat", yonerge="Seç & Süz: değer işaretleyin, anında uygulanır — Ctrl+tık: ekle · Shift+tık: çıkar · Esc: kapat",
                 secili=f"Seçili: {n}", koord=("6,000", "12,000", "9,000"))
    t.dikdortgen(0, 0, 1920, 1080, kenar="#C9CCD1")
    return t


def ekran_kat(s=1):
    """2) Kat kategorisi, Benzer katlar kapsamı + Kullanım yeri: köşe kolon → 12 kolon."""
    L = Yer(1920, 1080)
    t = Tuval(1920, 1080, s)
    ortak_ust(t, L, basili="Seç & Süz")
    olcut = {"kat": {"Kat 1", "Kat 2", "Kat 3"}, "yer": {"Kolon › köşe"}}
    suz = ozn.Suzgec(TABLO, olcut)
    es = suz.eslesen()
    n = len(es)

    def kose(e):
        return e.tur == "kolon" and (abs(e.p0[0]) < 1e-6 or abs(e.p0[0] - 18) < 1e-6) and (abs(e.p0[1]) < 1e-6 or abs(e.p0[1] - 24) < 1e-6)

    sc, iz = gorunum(t, L, "kat", secim_fn=kose, pil_kat="Benzer katlar")
    secim_rozeti(t, L, f"Seçim: {n} kolon", "köşe kolon · Kat 1–3")
    agac = agac_alt([
        (0, "proje", uret.PROJE, "", "", True, None),
        (1, "aks", "Aks sistemi", "A–D × 1–5", "", None, None),
        (1, "kat", "Katlar", "3", "", True, None),
        (2, "kat", "Kat 3 (Çatı)", "+13,50", "", False, "4"),
        (2, "kat", "Kat 2", "+9,00", "etkin", True, None),
        (3, "kolon", "Kolonlar", "20", "", True, None),
        (4, "kullanim", "köşe", "4", "secili", None, "4 seçili"),
        (4, "kullanim", "kenar", "10", "", None, None),
        (4, "kullanim", "iç", "6", "", None, None),
        (3, "kiris", "Kirişler · IPE400", "31", "", False, None),
        (3, "kiris_tali", "Tali kirişler", "12", "", False, None),
        (2, "kat", "Kat 1", "+4,50", "", False, "4"),
        (2, "kat", "Zemin", "±0,00", "", False, None),
    ])
    model_agaci(t, L, agac, f"263 eleman · 80 düğüm · 3 kat · {n} seçili")

    def govde(t, x, y, w, ymax, suz):
        y = liste_basligi(t, x, y + 6, w, "Kat", "n: köşe kolon ile  ·  N: katta", "Kat ara — ad ya da kot")
        t.yazi(x, taban(y, 16, 10), "Kat kapsamı — durum çubuğuyla aynı anahtar", 10, 500, P["metin2"])
        y += 18
        parcali(t, x, y, w, 22, ["Bu kat", "Benzer katlar", "Tüm katlar"], 1, 11, esit=False)
        y += 22 + 4
        t.yazi(x, taban(y, 16, 9.5), "Alt+1/2/3 · elle işaretleme → “Özel”", 9.5, 400, P["metin3"])
        y += 20
        y = baglantilar(t, x, y, w, ["Tümü", "Hiçbiri", "Ters"], "kota göre ▾")
        sayi = suz.sayim("kat")
        satirlar = [("Kat 3", "+13,50 · çatı · benzer → Kat 2", True), ("Kat 2", "+9,00 · ana kat · etkin kat", True),
                    ("Kat 1", "+4,50 · benzer → Kat 2", True), ("Zemin", "±0,00 · temel · benzer: Yok", False)]
        for ad, alt, isa in satirlar:
            rh = 34
            nn, NN = sayi.get(ad, (0, 0))
            if ad == "Kat 2":
                t.dikdortgen(x - 6, y, w + 12, rh, dolgu=P["yuzey2"], r=3)
            onay3(t, x + 2, y + 6, isa, 12)
            t.yazi(x + 20, taban(y + 2, 16, 12), ad, 12, 600 if isa else 400, P["metin"] if isa else P["metin3"])
            t.yazi(x + 20, taban(y + 17, 14, 9.5), alt, 9.5, 400, P["metin3"])
            sayim(t, x + w, y + 2, 16, nn, NN, soluk=not isa)
            y += rh
        y += 6
        t.dikdortgen(x, y, w, 80, dolgu=P["secim_ton"], kenar=P["secim_ton2"], r=3)
        t.simge("bilgi", x + 12, y + 13, 12, P["vurgu"], 1.3)
        t.yazi(x + 24, taban(y + 4, 18, 10), "Benzer = etkin kat (Kat 2) +", 10, 600, P["metin"])
        t.yazi(x + 24, taban(y + 20, 16, 10), "ona benzeyen katlar (Kat Verisi)", 10, 600, P["metin"])
        t.yazi(x + 24, taban(y + 38, 16, 10), "Zemin: benzer “Yok” → dışarıda", 10, 400, P["metin2"])
        t.yazi(x + 24, taban(y + 56, 16, 10), "Kat verisi…", 10, 500, P["vurgu"])
        y += 80 + 10
        t.yazi(x, taban(y, 16, 10), "Kat aralığını aşan eleman", 10, 500, P["metin2"])
        y += 18
        parcali(t, x, y, w, 20, ["herhangi bir katı", "tüm katları"], 0, 10, esit=False)
        return {}

    secsuz_pratik(t, L, kip=0, aktif="kat", olcut=olcut,
                  cipler=[("Kat", "1, 2, 3 (benzer)"), ("Kullanım yeri", "köşe kolon")],
                  sonuc=(f"{n} kolon eşleşiyor → yeni seçim: {n}", "4 köşe × 3 kat · Zemin dışarıda (benzer: Yok)"),
                  govde=govde)
    pencere_seridi(t, L, "Seç & Süz")
    dock(t, L, satirlar=[
        ("SEÇ&SÜZ", f"kat içinde benzer(Kat 2) = [1, 2, 3] ve kullanım yeri = köşe kolon → {n} kolon", "kapsam: Benzer katlar (Alt+2)", "ok"),
        ("KAPSAM", "Bu kat → Benzer katlar · Kat ölçütü yeniden üretildi (3 kat işaretli)", "", ""),
    ])
    komut_satiri(t, L, son=f"Son: SEÇ&SÜZ — {n} köşe kolon seçildi (Kat 1–3)")
    durum_cubugu(t, L, kapsam="Benzer katlar", yonerge="Seç & Süz: Kat ölçütü kat kapsamını izliyor — Alt+1/2/3 · elle işaretleme “Özel” yapar",
                 secili=f"Seçili: {n}", koord=("0,000", "0,000", "9,000"))
    t.dikdortgen(0, 0, 1920, 1080, kenar="#C9CCD1")
    return t


def ekran_gelismis(s=1):
    """3) Gelişmiş: çipler kural satırına dönüşmüş + 'Uzunluk > 5,00 m' + Süzgeç olarak kaydet."""
    L = Yer(1920, 1080)
    t = Tuval(1920, 1080, s)
    ortak_ust(t, L, basili="Seç & Süz")
    olcut = {"kat": {"Kat 2"}, "kesit": {"HE340A", "IPE400"}}
    once = ozn.Suzgec(TABLO, olcut).eslesen()
    suz = ozn.Suzgec(TABLO, olcut, ek=[("uzunluk > 5", lambda a: (a["uzunluk"] or 0) > 5.0)])
    es = suz.eslesen()
    n = len(es)
    sc, iz = gorunum(t, L, "gelismis", secim_fn=lambda e: e.kat == 2 and e.tur == "kiris")
    secim_rozeti(t, L, f"Seçim: {n} kiriş", "Kat 2 · uzunluk > 5,00 m")
    agac = agac_alt([
        (0, "proje", uret.PROJE, "", "", True, None),
        (1, "aks", "Aks sistemi", "A–D × 1–5", "", None, None),
        (1, "kat", "Katlar", "3", "", True, None),
        (2, "kat", "Kat 3 (Çatı)", "+13,50", "", False, None),
        (2, "kat", "Kat 2", "+9,00", "etkin", True, None),
        (3, "kolon", "Kolonlar", "20", "", False, None),
        (3, "kiris", "Kirişler · IPE400", "31", "secili", False, "31 seçili"),
        (3, "kiris_tali", "Tali kirişler", "12", "", False, None),
        (3, "capraz", "Çaprazlar", "8", "", False, None),
        (2, "kat", "Kat 1", "+4,50", "", False, None),
        (2, "kat", "Zemin", "±0,00", "", False, None),
    ])
    model_agaci(t, L, agac, f"263 eleman · 80 düğüm · 3 kat · {n} seçili")
    x0, y0, w, h = panel_iskelet(t, L)
    y = ust_bolum(t, L, x0, y0, w, 0, [], (f"{n} kiriş eşleşiyor → yeni seçim: {n}",
                                           f"Uzunluk koşulu {len(once) - n} kolonu eledi (4,50 m) · önceki: {len(once)} eleman"), True)
    # sonuç kutusu ust_bolum'da en üste çizildi; kural kartı altta
    x = x0 + 12
    ww = w - 24
    t.yatay(x0, x0 + w, y, P["cizgi"])
    y += 8
    t.yazi(x, taban(y, 22, 11), "Eşleşme", 11, 500, P["metin2"])
    t.acilir(x + 62, y, 176, 22, "Tümü sağlansın (ve)", 11)
    t.simge("damlalik", x + ww - 104, y + 11, 12, P["metin3"], 1.3)
    t.yazi_sag(x + ww, taban(y, 22, 10), "çiplerden üretildi", 10, 400, P["metin3"])
    y += 30
    kw = [96, 70, ww - 96 - 70 - 8 - 8 - 22]

    def kural(y, alan_, isl, deger, yeni=False, birim=None):
        if yeni:
            t.dikdortgen(x - 6, y - 4, ww + 12, 30, dolgu=P["vurgu_ton"], r=3)
            t.dikey(x - 6, y - 4, y + 26, P["vurgu"], 2)
        t.acilir(x, y, kw[0], 22, alan_, 11.5)
        t.acilir(x + kw[0] + 8, y, kw[1], 22, isl, 11.5, odak=yeni)
        vx = x + kw[0] + kw[1] + 16
        if birim:
            t.giris(vx, y, kw[2] - 30, 22, deger, 11.5, odak=False)
            t.dikdortgen(vx + kw[2] - 28, y, 28, 22, dolgu=P["yuzey2"], kenar="#C9CDD3", r=3)
            t.yazi_orta(vx + kw[2] - 14, taban(y, 22, 11), birim, 11, 500, P["metin2"])
        else:
            t.acilir(vx, y, kw[2], 22, deger, 11.5)
        t.simge("sil", x + ww - 9, y + 11, 13, P["metin3"], 1.3)

    kural(y, "Kat", "içinde", "Kat 2")
    y += 26
    ve_bag(t, x + 4, y - 2, 18)
    y += 18
    kural(y, "Kesit", "içinde", "HE340A, IPE400")
    y += 26
    ve_bag(t, x + 4, y - 2, 18)
    y += 18
    kural(y, "Uzunluk", ">", "5,00", yeni=True, birim="m")
    y += 30
    # histogram: mevcut eşleşmenin uzunluk dağılımı + eşik
    hx, hy, hw, hh = x + 4, y + 4, ww - 8, 52
    t.dikdortgen(x - 6, y - 4, ww + 12, hh + 30, dolgu=P["vurgu_ton"], r=0)
    t.dikey(x - 6, y - 4, y + hh + 26, P["vurgu"], 2)
    dagilim = {}
    for a in once:
        dagilim[a["uzunluk"]] = dagilim.get(a["uzunluk"], 0) + 1
    vmin, vmax = 3.0, 9.0
    enb = max(dagilim.values())

    def xpos(v):
        return hx + (v - vmin) / (vmax - vmin) * hw

    t.yatay(hx, hx + hw, hy + hh, P["cizgi"])
    for v in range(3, 10):
        t.dikey(xpos(v), hy + hh, hy + hh + 3, P["metin3"])
        t.yazi_orta(xpos(v), hy + hh + 13, f"{v}", 9, 400, P["metin3"])
    for v, c in sorted(dagilim.items()):
        bh = (hh - 14) * c / enb
        gecer = v > 5.0
        t.dikdortgen(xpos(v) - 9, hy + hh - bh, 18, bh, dolgu=P["vurgu"] if gecer else "#C3C8D0", r=1)
        t.yazi_orta(xpos(v), hy + hh - bh - 4, str(c), 9.5, 600, P["vurgu_koyu"] if gecer else P["metin3"], tnum=True)
    ex = xpos(5.0)
    t.dikey(ex, hy - 2, hy + hh, P["metin"], 1)
    t.dikdortgen(ex - 4, hy - 6, 8, 8, dolgu=P["yuzey"], kenar=P["metin"], r=1)
    t.yazi(ex + 6, taban(hy - 4, 12, 9.5), "5,00 m", 9.5, 600, P["metin"])
    t.yazi_sag(hx + hw, taban(hy - 4, 12, 9.5), f"geçen {n} · elenen {len(once) - n}", 9.5, 500, P["metin2"], tnum=True)
    t.yazi(xpos(9) + 6, hy + hh + 13, "m", 9, 400, P["metin3"])
    y += hh + 30
    # ekle düğmeleri
    t.simge("artı", x + 6, y + 10, 11, P["vurgu"], 1.5)
    t.yazi(x + 16, taban(y, 20, 11), "Koşul", 11, 600, P["vurgu"])
    t.simge("artı", x + 74, y + 10, 11, P["vurgu"], 1.5)
    t.yazi(x + 84, taban(y, 20, 11), "Veya grubu", 11, 600, P["vurgu"])
    t.yazi_sag(x + ww, taban(y, 20, 9.5), "gruplama tek düzey", 9.5, 400, P["metin3"])
    y += 24
    t.yazi(x, taban(y, 16, 9.5), "İşleçler: = ≠ < ≤ > ≥ · arasında · içerir · ile başlar · boş / dolu", 9.5, 400, P["metin3"])
    y += 18
    # sorgu metni (iki yönlü)
    t.yatay(x0, x0 + w, y, P["cizgi2"])
    y += 8
    bolum_etiketi(t, x, y, "SORGU METNİ · İKİ YÖNLÜ")
    t.simge("kod", x + ww - 6, y + 10, 12, P["metin3"], 1.3)
    y += 20
    t.dikdortgen(x, y, ww, 40, dolgu=P["yuzey2"], kenar="#C9CDD3", r=3)
    t.yazi(x + 8, taban(y + 2, 18, 11), "kat içinde [2] ve kesit içinde", 11, 500, P["metin"])
    t.yazi(x + 8, taban(y + 19, 18, 11), "[HE340A, IPE400] ve uzunluk > 5 m", 11, 500, P["metin"])
    y += 40 + 8
    # süzgeç olarak kaydet
    t.yatay(x0, x0 + w, y, P["cizgi2"])
    y += 8
    bolum_etiketi(t, x, y, "SÜZGEÇ OLARAK KAYDET")
    y += 22
    t.yazi(x, taban(y, 22, 11), "Ad", 11, 400, P["metin2"])
    t.giris(x + 40, y, ww - 40, 22, "Kat 2 uzun HE/IPE elemanlar", 11.5, odak=True, imlec=True)
    y += 30
    for i, (et, isa) in enumerate((("Seçim süzgeci (Grup / süzgeç listesinde)", True), ("Görünüm süzgeci (diğerleri %85 saydam)", False),
                                   ("Renk kuralı (eşleşenler tek renk)", False))):
        t.onay_kutusu(x, y + 4, isa, 12)
        t.yazi(x + 18, taban(y, 20, 11), et, 11, 400, P["metin"])
        y += 20
    y += 8
    t.dugme(x, y, 132, 24, ".filtre dışa aktar…", boyut=11)
    t.dugme(x + ww - 150, y, 150, 24, "Süzgeç olarak kaydet", birincil=True, boyut=11.5)
    y += 24 + 6
    t.yazi(x, taban(y, 14, 9.5), "Dinamik: her kullanımda yeniden değerlendirilir · .op4 içinde saklanır", 9.5, 400, P["metin3"])
    y += 18
    t.yatay(x0, x0 + w, y, P["cizgi2"])
    y += 8
    bolum_etiketi(t, x, y, "KAYITLI SÜZGEÇLER · GRUP / SÜZGEÇ ÖLÇÜTÜNDE GÖRÜNÜR")
    y += 22
    for ad_, n_, kul in (("IPE400 kirişler – Kat 2", "31", "seçim"), ("Zemin kat kolonları", "20", "seçim · görünüm"), ("D/C > 0,90", "4", "renk kuralı")):
        t.dikdortgen(x, y, ww, 20, dolgu=P["yuzey"], kenar=P["cizgi2"], r=3)
        t.simge("suz", x + 11, y + 10, 11, P["metin2"], 1.3)
        t.yazi(x + 24, taban(y, 20, 11), ad_, 11, 500, P["metin"])
        t.yazi(x + 24 + t.yazi_gen(ad_, 11, 500) + 8, taban(y, 20, 9.5), kul, 9.5, 400, P["metin3"])
        t.yazi_sag(x + ww - 8, taban(y, 20, 11), n_, 11, 600, P["metin2"], tnum=True)
        y += 23
    print("  gelişmiş panel alt sınır:", y, "≤", y0 + h - 40 - 4)
    alt_cubuk(t, x0, y0, w, h)
    pencere_seridi(t, L, "Seç & Süz")
    dock(t, L, satirlar=[
        ("SEÇ&SÜZ", f"kat içinde [2] ve kesit içinde [HE340A, IPE400] ve uzunluk > 5 m → {n} kiriş", "Gelişmiş · 3 koşul", "ok"),
        ("SEÇ&SÜZ", f"Gelişmiş açıldı: 2 çip → 2 kural satırı (kayıpsız) · Gelişmiş kapatılınca 3. koşul “Gelişmiş: 1 koşul” çipi olur", "", ""),
    ])
    komut_satiri(t, L, son=f"Son: SEÇ&SÜZ — {n} kiriş (uzunluk > 5,00 m)")
    durum_cubugu(t, L, kapsam="Bu kat", yonerge="Gelişmiş: kural satırları çiplerle eşitlenir — Ctrl+Shift+F aç/kapa · Ad alanında Enter: süzgeç olarak kaydet",
                 secili=f"Seçili: {n}", koord=("6,000", "12,000", "9,000"))
    t.dikdortgen(0, 0, 1920, 1080, kenar="#C9CCD1")
    return t


def menu_karti(t, x, y, w, ogeler, baslik=None, alt_not=None):
    """Açılır menü: ogeler = [(simge|None, metin, sağ, durum)] ; durum: '', 'hover', 'alt', 'soluk', '-' (ayraç), 'baslik'."""
    h = 6
    for o in ogeler:
        h += 9 if o == "-" else (20 if o[3] == "baslik" else 24)
    if baslik:
        h += 38
    if alt_not:
        h += 24
    kart(t, x, y, w, h, r=4)
    yy = y + 3
    if baslik:
        t.dikdortgen(x + 1, y + 1, w - 2, 36, dolgu=P["yuzey2"], r=4)
        t.dikdortgen(x + 1, y + 20, w - 2, 18, dolgu=P["yuzey2"])
        t.yatay(x, x + w, y + 37, P["cizgi2"])
        t.yazi(x + 12, taban(y + 3, 16, 11.5), baslik[0], 11.5, 600, P["metin"])
        t.yazi(x + 12, taban(y + 19, 14, 10), baslik[1], 10, 400, P["metin3"])
        yy = y + 41
    konum = {}
    for o in ogeler:
        if o == "-":
            t.yatay(x + 8, x + w - 8, yy + 4, P["cizgi2"])
            yy += 9
            continue
        ik, m, sag, durum = o
        if durum == "baslik":
            bolum_etiketi(t, x + 12, yy, m, 20)
            yy += 20
            continue
        rh = 24
        if durum in ("hover", "alt"):
            t.dikdortgen(x + 4, yy, w - 8, rh, dolgu=P["vurgu_ton"], r=3)
        renk = P["metin3"] if durum == "soluk" else P["metin"]
        if ik:
            t.simge(ik, x + 20, yy + rh / 2, 14, P["vurgu"] if durum in ("hover", "alt") else ("#B3B7BE" if durum == "soluk" else "#3C4148"), 1.4)
        t.yazi(x + 36, taban(yy, rh, 12), m, 12, 500 if durum in ("hover", "alt") else 400, renk)
        xr = x + w - 12
        if sag == "▸":
            t.sevron(xr - 3, yy + rh / 2, "sag", 9, P["vurgu"] if durum == "alt" else P["metin2"])
        elif sag:
            if sag.startswith("Ctrl") or sag in ("Esc", "Del", "Enter"):
                kw = t.yazi_gen(sag, 9.5, 500) + 8
                t.kisayol(xr - kw, yy + 5, sag, 9.5, 14)
            else:
                t.yazi_sag(xr, taban(yy, rh, 10.5), sag, 10.5, 400, P["metin3"], tnum=True)
        konum[m] = (x, yy, w, rh)
        yy += rh
    if alt_not:
        t.yatay(x + 1, x + w - 1, yy + 2, P["cizgi2"])
        t.yazi(x + 12, taban(yy + 3, 20, 9.5), alt_not, 9.5, 400, P["metin3"])
    return konum, h


def ekran_menu(s=1):
    """4) Şerit 'Seç ▾' menüsü (ölçüte göre seç, alt menüde canlı sayılar) + elemana sağ tık menüsü."""
    L = Yer(1920, 1080, ozel_w=320)
    t = Tuval(1920, 1080, s)
    kon = ortak_ust(t, L, basili="Seç")
    hedef_et = "K2-A23"

    def hov(e):
        return e.tur == "kiris" and e.kat == 2 and abs(e.p0[0]) < 1e-6 and 6 < (e.p0[1] + e.p1[1]) / 2 < 12

    sc, iz = gorunum(t, L, "menu", secim_fn=None, hover_fn=hov)
    agac = agac_alt([
        (0, "proje", uret.PROJE, "", "", True, None),
        (1, "aks", "Aks sistemi", "A–D × 1–5", "", None, None),
        (1, "kat", "Katlar", "3", "", True, None),
        (2, "kat", "Kat 3 (Çatı)", "+13,50", "", False, None),
        (2, "kat", "Kat 2", "+9,00", "etkin", True, None),
        (3, "kolon", "Kolonlar", "20", "", False, None),
        (3, "kiris", "Kirişler · IPE400", "31", "", False, None),
        (3, "kiris_tali", "Tali kirişler", "12", "", False, None),
        (3, "capraz", "Çaprazlar", "8", "", False, None),
        (3, "doseme", "Döşemeler", "1", "", False, None),
        (2, "kat", "Kat 1", "+4,50", "", False, None),
        (2, "kat", "Zemin", "±0,00", "", False, None),
    ])
    model_agaci(t, L, agac, "263 eleman · 80 düğüm · 3 kat · seçim yok")
    # sağ panel: Özellikler boş durum
    x0, y0, w, h = panel_iskelet(t, L, "Özellikler", "etiket")
    yy = y0 + 28 + 560
    t.dikdortgen(x0 + w / 2 - 22, yy, 44, 44, dolgu=P["yuzey2"], kenar=P["cizgi2"], r=22)
    t.simge("sec", x0 + w / 2, yy + 22, 20, P["metin3"], 1.5)
    yy += 60
    t.yazi_orta(x0 + w / 2, taban(yy, 18, 12), "Seçim yok", 12, 600, P["metin"])
    yy += 20
    t.yazi_orta(x0 + w / 2, taban(yy, 16, 11), "Elemana tıklayın, şeritte Seç menüsünü ya da", 11, 400, P["metin2"])
    yy += 16
    t.yazi_orta(x0 + w / 2, taban(yy, 16, 11), "sağ tık menüsünden ölçüte göre seçin.", 11, 400, P["metin2"])
    yy += 30
    for ik, m, k in (("sec_suz", "Seç & Süz paneli", "Ctrl+F"), ("gecmis", "Önceki seçim · 51 eleman", "Ctrl+J"), ("tumu", "Tümünü seç", "Ctrl+A")):
        t.dikdortgen(x0 + 24, yy, w - 48, 26, dolgu=P["yuzey"], kenar=P["cizgi"], r=3)
        t.simge(ik, x0 + 40, yy + 13, 13, "#3C4148", 1.4)
        t.yazi(x0 + 54, taban(yy, 26, 11.5), m, 11.5, 500, P["metin"])
        kw = t.yazi_gen(k, 9.5, 500) + 8
        t.kisayol(x0 + w - 32 - kw, yy + 6, k, 9.5, 14)
        yy += 32
    pencere_seridi(t, L, "Özellikler")
    dock(t, L, satirlar=[
        ("SEÇ", "Seçim temizlendi (Esc) · önceki seçim saklandı: 51 eleman", "Ctrl+J: geri getir", ""),
        ("SEÇ&SÜZ", "kat = Kat 2 ve kesit içinde [HE340A, IPE400] → 51 eleman", "", ""),
    ])
    komut_satiri(t, L, son="Son: SEÇİMİTEMİZLE")
    durum_cubugu(t, L, kapsam="Tüm katlar", yonerge="Sağ tık: elemana göre seç · Seç menüsü: ölçüte göre seç · Ctrl+F: Seç & Süz",
                 secili="Seçili: 0", koord=("0,000", "9,000", "9,000"))
    # --- 1) şerit Seç ▾ menüsü ---
    sx, sy, sw, sh = kon["Seç"]
    mx, my = sx - 2, sy + sh + 4
    TUM = {"Kat 1", "Kat 2", "Kat 3"}          # kapsam: Tüm katlar (Zemin / temel seviyesi hariç — ilke 11)
    S = ozn.Suzgec(TABLO, {"kat": TUM})
    nk = {v: n for v, (n, N) in S.sayim("kesit").items()}
    ogeler = [
        (None, "ÖLÇÜTE GÖRE SEÇ — PANELİ O ÖLÇÜTTE AÇAR", "", "baslik"),
        ("tur", "Türe göre", "▸", ""),
        ("kat", "Kata göre", "▸", ""),
        ("kesit", "Kesite göre", "▸", "alt"),
        ("malzeme", "Malzemeye göre", "▸", ""),
        ("kullanim", "Kullanım yerine göre", "▸", ""),
        ("aks", "Aksa göre", "▸", ""),
        ("dogrultu", "Doğrultuya göre (X / Y / Z)", "▸", ""),
        ("duzlem", "Düzleme göre (XY / XZ / YZ)", "▸", ""),
        ("uzunluk", "Uzunluk aralığına göre…", "", ""),
        ("grup", "Gruba / süzgece göre", "▸", ""),
        ("etiket", "Etikete göre", "▸", ""),
        ("yuk", "Yük desenine göre", "▸", ""),
        ("mesnet", "Mesnet / serbestliğe göre", "▸", ""),
        ("dc", "D/C aralığına göre", "▸", ""),
        "-",
        ("tumu", "Tümünü seç", "Ctrl+A", ""),
        ("ters", "Tersine çevir", "Ctrl+Shift+I", ""),
        ("gecmis", "Önceki seçim", "Ctrl+J", ""),
        ("silgi", "Seçimi temizle", "Esc", ""),
        ("benzer", "Benzerini seç", "Ctrl+B", "soluk"),
        "-",
        ("sec_suz", "Seç & Süz paneli…", "Ctrl+F", ""),
    ]
    mk, mh = menu_karti(t, mx, my, 296, ogeler, alt_not="Benzerini seç: önce bir eleman seçin")
    # alt menü: Kesite göre
    kx, ky, kww, khh = mk["Kesite göre"]
    alt = [
        (None, "KAPSAM: TÜM KATLAR · TIK: YENİ SEÇİM", "", "baslik"),
        ("kesit", "HE340A", f"{nk['HE340A']}", ""),
        ("kesit", "IPE400", f"{nk['IPE400']}", "hover"),
        ("kesit", "IPE200", f"{nk['IPE200']}", ""),
        ("kesit", "L100x10", f"{nk['L100x10']}", ""),
        ("kesit", "KUTU 80x4", f"{nk['KUTU 80x4']}", ""),
        "-",
        ("sec_suz", "Panelde aç: Kesit…", "", ""),
    ]
    menu_karti(t, mx + 296 - 4, ky - 24, 220, alt, alt_not="Ctrl+tık: ekle · Shift+tık: çıkar")
    nm = "Şerit › Seç › menü (bölünmüş düğmenin alt yarısı)"
    nw = t.yazi_gen(nm, 11, 600) + 40
    numara(t, mx - nw - 14, my + 40, 1, nm)
    t.cizgi(mx - 14, my + 52, mx - 2, my + 52, P["ipucu_zemin"], 1.5)
    # --- 2) elemana sağ tık ---
    a = None
    for e in sc.elemanlar:
        if hov(e):
            a = e
    pm = iz(((a.p0[0] + a.p1[0]) / 2, (a.p0[1] + a.p1[1]) / 2, a.p0[2] + 0.2))
    t.simge("imlec", pm[0] + 6, pm[1] + 8, 18, "#14181B", 1.2)
    satir = next(r for r in TABLO if r["ref"].tur == a.tur and r["ref"].kat == a.kat and r["ref"].p0 == a.p0)
    nkat = ozn.Suzgec(TABLO, {"kat": {"Kat 2"}}).eslesen()
    nyer = ozn.Suzgec(TABLO, {"kat": TUM, "yer": {"Kiriş › dış"}}).eslesen()
    naks = ozn.Suzgec(TABLO, {"kat": TUM, "aks": {"A"}}).eslesen()
    nben = ozn.Suzgec(TABLO, {"kat": TUM, "tur": {"Kiriş"}, "kesit": {"IPE400"}}).eslesen()
    ogeler2 = [
        ("benzer", "Benzerini seç", "Ctrl+B", ""),
        (None, "BUNA GÖRE SEÇ", "", "baslik"),
        ("kesit", "Bu kesittekileri seç", f"IPE400 · {nk['IPE400']}", "hover"),
        ("kat", "Bu kattakileri seç", f"Kat 2 · {len(nkat)}", ""),
        ("kullanim", "Bu kullanım yerindekileri seç", f"dış kiriş · {len(nyer)}", ""),
        ("aks", "Bu akstakileri seç", f"Aks A · {len(naks)}", ""),
        ("grup", "Bu gruptakileri seç", "▸", ""),
        "-",
        ("sec_suz", "Seç & Süz'de aç (ölçütleri doldur)", "Ctrl+F", ""),
        "-",
        ("etiket", "Özellikler", "", ""),
        ("goz", "Yalnız bunu göster", "Ctrl+5", ""),
        ("goz_kapali", "Gizle", "", ""),
        ("sil", "Sil", "Del", ""),
    ]
    cx_, cy_ = pm[0] + 14, pm[1] - 30
    mk2, mh2 = menu_karti(t, cx_, cy_, 300, ogeler2, baslik=(f"Kiriş {hedef_et} · IPE400 · Kat 2", f"dış kiriş · Aks A · 2–3 · {str(satir['uzunluk']).replace('.', ',')}0 m · benzer: {len(nben)}"),
                          alt_not="Kat kapsamı: Tüm katlar (Zemin hariç)")
    numara(t, cx_, cy_ + mh2 + 10, 2, "Elemana sağ tık")
    t.dikdortgen(0, 0, 1920, 1080, kenar="#C9CCD1")
    return t


def yuk_oklari(t, iz, satirlar, renk):
    """Seçili çubuklar üstünde yayılı yük önizlemesi: ok sırası + üst çizgi."""
    for a in satirlar:
        p0, p1 = a["p0"], a["p1"]
        z = p0[2] + 0.05
        ust = []
        n = 5
        for i in range(n):
            tt = (i + 0.5) / n
            x = p0[0] + (p1[0] - p0[0]) * tt; y = p0[1] + (p1[1] - p0[1]) * tt
            q0 = iz((x, y, z + 1.05)); q1 = iz((x, y, z + 0.12))
            t.cizgi(q0[0], q0[1], q1[0], q1[1], renk, 1)
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            Ln = (dx * dx + dy * dy) ** 0.5 or 1
            ux, uy = dx / Ln, dy / Ln
            t.cokgen([(q1[0], q1[1]), (q1[0] - ux * 5 - uy * 2.6, q1[1] - uy * 5 + ux * 2.6), (q1[0] - ux * 5 + uy * 2.6, q1[1] - uy * 5 - ux * 2.6)], dolgu=renk)
        a0 = iz((p0[0], p0[1], z + 1.05)); a1 = iz((p1[0], p1[1], z + 1.05))
        t.cizgi(a0[0], a0[1], a1[0], a1[1], renk, 1)


def ekran_yuk(s=1):
    """5) Yük ata komutu: Hedef istemi aynı ölçütleri sunar (Kat · Kesit · Kullanım yeri …)."""
    L = Yer(1920, 1080, ozel_w=352)
    t = Tuval(1920, 1080, s)
    baslik_cubugu(t, L)
    serit(t, L, etkin="Yükler", gruplar=GRUPLAR_YUKLER)
    ray(t, L)
    gorunum_sekmeleri(t, L)
    olcut = {"kat": {"Kat 1", "Kat 2", "Kat 3"}, "yer": {"Kiriş › dış"}}
    suz = ozn.Suzgec(TABLO, olcut)
    es = suz.eslesen()
    n = len(es)

    def dis(e):
        if e.tur != "kiris":
            return False
        if abs(e.p0[1] - e.p1[1]) < 1e-6:
            return abs(e.p0[1]) < 1e-6 or abs(e.p0[1] - 24) < 1e-6
        return abs(e.p0[0]) < 1e-6 or abs(e.p0[0] - 18) < 1e-6

    sc, iz = gorunum(t, L, "yuk", secim_fn=dis, pil_kat="Benzer katlar")
    yuk_oklari(t, iz, es, rgba(P["vurgu"], 0.80))
    secim_rozeti(t, L, f"Hedef: {n} kiriş", "dış kiriş · Kat 1–3 · önizleme")
    agac = agac_alt([
        (0, "proje", uret.PROJE, "", "", True, None),
        (1, "aks", "Aks sistemi", "A–D × 1–5", "", None, None),
        (1, "kat", "Katlar", "3", "", True, None),
        (2, "kat", "Kat 3 (Çatı)", "+13,50", "", False, "14"),
        (2, "kat", "Kat 2", "+9,00", "etkin", True, None),
        (3, "kolon", "Kolonlar", "20", "", False, None),
        (3, "kiris", "Kirişler · IPE400", "31", "", True, None),
        (4, "kullanim", "dış", "14", "secili", None, "14 hedef"),
        (4, "kullanim", "iç", "17", "", None, None),
        (3, "kiris_tali", "Tali kirişler", "12", "", False, None),
        (2, "kat", "Kat 1", "+4,50", "", False, "14"),
        (2, "kat", "Zemin", "±0,00", "", False, None),
    ])
    model_agaci(t, L, agac, f"263 eleman · 80 düğüm · 3 kat · hedef {n}")
    # sağ panel: Yük ata (Özellikler penceresinde komut özellikleri)
    x0, y0, w, h = panel_iskelet(t, L, "Özellikler — Yük ata", "etiket")
    oy = y0 + 28
    t.yatay(x0, x0 + w, oy + 39, P["cizgi2"])
    t.dikdortgen(x0 + 12, oy + 8, 24, 24, dolgu=P["vurgu_ton"], r=4)
    t.simge("yuk", x0 + 24, oy + 20, 16, P["vurgu"], 1.5)
    t.yazi(x0 + 44, oy + 18, "Çubuk yükü · yayılı", 12, 600, P["metin"])
    t.yazi(x0 + 44, oy + 32, "YÜKATA · komut etkin · Enter: uygula", 11, 400, P["metin3"])
    y = oy + 40
    lw_ = 108
    vx = x0 + 12 + lw_
    vw = w - 12 - lw_ - 14

    def baslik_(y, ad, acik=True, rozet=None):
        t.dikdortgen(x0 + 1, y, w - 1, 20, dolgu=P["yuzey2"])
        t.sevron(x0 + 14, y + 10, "asagi" if acik else "sag", 9, P["metin2"])
        t.yazi(x0 + 26, taban(y, 20, 11), ad, 11, 600, P["metin2"])
        if rozet:
            t.yazi_sag(x0 + w - 12, taban(y, 20, 10), rozet, 10, 500, P["vurgu"])
        return y + 20

    def satir_(y, et, deger, tur="acilir"):
        t.yatay(x0 + 1, x0 + w, y + 19, P["cizgi2"])
        t.yazi(x0 + 12, taban(y, 20, 12), et, 12, 400, P["metin2"])
        if tur == "acilir":
            t.acilir(vx, y + 2, vw, 16, deger, 12)
        elif tur == "giris":
            t.giris(vx, y + 2, vw, 16, deger, 12, hiza="sag")
        return y + 20

    y = baslik_(y, "Yük")
    y = satir_(y, "Yük deseni", "G · Sabit (geçerli)")
    y = satir_(y, "Tür", "Yayılı (q)")
    y = satir_(y, "q", "3,60 kN/m", "giris")
    y = satir_(y, "Yön", "Global −Z (yerçekimi)")
    y = satir_(y, "Boyunca", "Tam boy")
    t.yazi(x0 + 12, taban(y, 24, 12), "Kip", 12, 400, P["metin2"])
    parcali(t, vx, y + 3, vw, 18, ["Ekle", "Değiştir", "Sil"], 0, 10.5)
    y += 26
    y = baslik_(y, "Hedef", rozet=f"{n} kiriş")
    y += 8
    xx = x0 + 12
    ww = w - 24
    t.yazi(xx, taban(y, 18, 10), "Seç & Süz ile aynı ölçütler — çip ekle:", 10, 500, P["metin2"])
    y += 20
    # hızlı ölçüt düğmeleri (komut satırındaki pillerle aynı)
    cx = xx
    for s_, et in (("Seçim", False), ("Kat", True), ("Kesit", False), ("Kullanım yeri", True), ("Grup", False), ("Süzgeç", False)):
        sw = t.yazi_gen(s_, 10.5, 500) + 22
        if cx + sw > xx + ww:
            cx = xx; y += 24
        t.dikdortgen(cx, y, sw, 20, dolgu=P["vurgu_ton"] if et else P["yuzey"], kenar=P["vurgu_ton2"] if et else "#C9CDD3", r=10)
        t.simge("artı" if not et else "onay", cx + 9, y + 10, 8, P["vurgu"] if et else P["metin2"], 1.6)
        t.yazi(cx + 16, taban(y, 20, 10.5), s_, 10.5, 600 if et else 500, P["metin"])
        cx += sw + 4
    y += 28
    cx = xx
    cx += cip(t, cx, y, "Kat", "1, 2, 3 · benzer")
    cx += ve_bag(t, cx + 2, y) + 4
    y2 = y
    if cx + 150 > xx + ww:
        cx = xx; y2 = y + 28
    cip(t, cx, y2, "Kullanım yeri", "dış kiriş")
    y = y2 + 30
    t.dikdortgen(xx, y, ww, 58, dolgu=P["secim_ton"], kenar=P["secim_ton2"], r=3)
    t.simge("dogrula", xx + 16, y + 20, 16, P["vurgu"], 1.5)
    t.yazi(xx + 32, y + 18, f"{n} kiriş · 3 kat · {n} yük kaydı", 12, 600, P["metin"], tnum=True)
    t.yazi(xx + 32, y + 34, "Kat 1: 14 · Kat 2: 14 · Kat 3: 14 — önizleme modelde", 10, 400, P["metin2"], tnum=True)
    t.yazi(xx + 32, y + 49, "Önceki G yükü olan 14 kiriş: Ekle → toplanır", 10, 400, P["uyari"], tnum=True)
    y += 58 + 10
    t.onay_kutusu(xx, y + 4, True, 12)
    t.yazi(xx + 18, taban(y, 20, 11), "Önizleme (oklar + kontur)", 11, 400, P["metin"])
    y += 20
    t.onay_kutusu(xx, y + 4, False, 12)
    t.yazi(xx + 18, taban(y, 20, 11), "Hedefi süzgeç olarak kaydet: “Dış kirişler”", 11, 400, P["metin"])
    y += 28
    y = baslik_(y, "Gösterim", acik=False)
    y += 12
    t.dikdortgen(xx, y, ww, 104, dolgu=P["yuzey2"], kenar=P["cizgi2"], r=3)
    t.simge("bilgi", xx + 12, y + 13, 12, P["metin3"], 1.3)
    t.yazi(xx + 24, taban(y + 4, 18, 10.5), "Aynı Hedef istemi bu komutlarda da var:", 10.5, 600, P["metin2"])
    yy_ = y + 24
    for k_, a_ in (("MESNETATA", "en alt düğümler · kolon alt uçları · Kat"), ("KESİTATA", "Kesit · Kullanım yeri · Kat"),
                   ("SERBESTLİK", "Nesne türü · Doğrultu · Aks"), ("GRUPATA", "Seçim · Süzgeç")):
        t.yazi(xx + 24, taban(yy_, 18, 10), k_, 10, 600, P["vurgu"])
        t.yazi(xx + 24 + 76, taban(yy_, 18, 10), a_, 10, 400, P["metin2"])
        yy_ += 18
    y += 104 + 14
    bolum_etiketi(t, xx, y, "SON HEDEFLER")
    y += 20
    for m_, n_ in (("dış kiriş · Benzer katlar", "42"), ("Kat 2 ve IPE400", "31"), ("Seçim (6 kiriş)", "6")):
        t.dikdortgen(xx, y, ww, 22, dolgu=P["yuzey"], kenar=P["cizgi2"], r=3)
        t.simge("gecmis", xx + 11, y + 11, 11, P["metin3"], 1.3)
        t.yazi(xx + 24, taban(y, 22, 11), m_, 11, 500, P["metin"])
        t.yazi_sag(xx + ww - 8, taban(y, 22, 11), n_, 11, 600, P["metin2"], tnum=True)
        y += 26
    # alt: Uygula / İptal
    fy = y0 + h - 40
    t.dikdortgen(x0 + 1, fy, w - 1, 40, dolgu=P["yuzey2"])
    t.yatay(x0, x0 + w, fy, P["cizgi"])
    t.dugme(x0 + 12, fy + 9, 104, 22, "Uygula (Enter)", birincil=True, boyut=11.5)
    t.dugme(x0 + 122, fy + 9, 60, 22, "İptal", boyut=11.5)
    t.yazi_sag(x0 + w - 12, taban(fy, 40, 10), "tek geri al adımı", 10, 400, P["metin3"])
    pencere_seridi(t, L, "Özellikler")
    dock(t, L, satirlar=[
        ("YÜKATA", "G · yayılı 3,60 kN/m · Global −Z · kip: Ekle", f"hedef bekleniyor · önizleme: {n} kiriş", ""),
        ("HEDEF", f"kat içinde benzer(Kat 2) ve kullanım yeri = dış kiriş → {n} kiriş", "Enter: uygula · Esc: iptal", "ok"),
    ])
    kon = komut_satiri(t, L, komut="YÜKATA", secenekler=["Hedef:", "Seçim", "Kat: benzer (1–3)", "Kesit", "Kullanım yeri: dış kiriş", "Grup", "Süzgeç", "|", "Seç & Süz…"],
                       etkin_secenek="Kullanım yeri: dış kiriş", degerli={"Kat: benzer (1–3)"}, son="Enter: uygula",
                       ipuclari=[("Tab", "sonraki ölçüt"), ("Enter", "uygula"), ("Esc", "iptal")])
    durum_cubugu(t, L, kapsam="Benzer katlar", yonerge="YÜKATA · Hedef ölçütü verin ya da elemanlara tıklayın — Enter: uygula · Esc: iptal",
                 secili=f"Hedef: {n} kiriş", koord=("18,000", "12,000", "9,000"))
    # kullanım yeri açılır listesi (komut satırı pilinin üstünde)
    px, py, pw, ph = kon["Kullanım yeri: dış kiriş"]
    sayi = suz.sayim("yer")
    gruplar = [("Kiriş", ["Kiriş › dış", "Kiriş › iç"]), ("Kolon", ["Kolon › köşe", "Kolon › kenar", "Kolon › iç"]),
               ("Çapraz", ["Çapraz › dış cephe", "Çapraz › çatı düzlemi"]), ("Tali kiriş · Aşık", ["Tali kiriş › iç", "Aşık › iç"])]
    satir_say = sum(1 + len(g[1]) for g in gruplar)
    mw, mh = 260, 40 + satir_say * 22 + 4 + 44
    mx, my = px - 6, py - 8 - mh
    kart(t, mx, my, mw, mh, r=4)
    t.dikdortgen(mx + 1, my + 1, mw - 2, 30, dolgu=P["yuzey2"], r=4)
    t.yatay(mx, mx + mw, my + 31, P["cizgi2"])
    t.simge("kullanim", mx + 16, my + 16, 13, P["vurgu"], 1.4)
    t.yazi(mx + 30, taban(my + 1, 30, 11.5), "Kullanım yeri", 11.5, 600, P["metin"])
    t.yazi_sag(mx + mw - 12, taban(my + 1, 30, 9.5), "n: Benzer katlarda / N", 9.5, 400, P["metin3"])
    yy = my + 36
    for g, uyeler in gruplar:
        bolum_etiketi(t, mx + 12, yy, g.upper(), 20)
        yy += 20
        for u in uyeler:
            nn, NN = sayi[u]
            isa = u in olcut["yer"]
            if isa:
                t.dikdortgen(mx + 4, yy, mw - 8, 22, dolgu=P["vurgu_ton"], r=3)
            onay3(t, mx + 14, yy + 5, isa, 12)
            et_ = u.split(" › ")[1] if not g.startswith("Tali") else (u.split(" › ")[0].lower() + " · " + u.split(" › ")[1])
            t.yazi(mx + 32, taban(yy, 22, 11.5), et_, 11.5, 600 if isa else 400, P["metin"])
            sayim(t, mx + mw - 12, yy, 22, nn, NN)
            yy += 22
    yy += 4
    t.yatay(mx + 1, mx + mw - 1, yy, P["cizgi2"])
    t.yazi(mx + 12, taban(yy + 2, 20, 9.5), "Aynı bileşen: Seç & Süz değer listesi", 9.5, 400, P["metin3"])
    t.yazi(mx + 12, taban(yy + 18, 20, 9.5), "↑↓ gez · Boşluk işaretle · Enter: uygula", 9.5, 400, P["metin3"])
    t.dikdortgen(0, 0, 1920, 1080, kenar="#C9CCD1")
    return t


# ============================================================================
# KARŞILAŞTIRMA SAYFASI (2400 px)
# ============================================================================
def karsilastirma(yollar):
    W = 2400
    pad = 40
    gw = (W - pad * 3) // 2
    gh = int(gw * 1080 / 1920)
    bas_h = 120
    et_h = 44
    H = bas_h + 3 * (gh + et_h + pad) + pad
    t = Tuval(W, H, 1, zemin=P["zemin"])
    t.yazi(pad, 58, "op4 · Seç & Süz — hibrit tasarım (pratik ölçüt rafı + isteğe bağlı Gelişmiş kural katmanı)", 26, 600, P["metin"])
    t.yazi(pad, 92, "Atölye iskeleti · geçici nötr palet + tek soğuk vurgu (tek satırla yeniden üretilir) · sayılar sahne modelinden hesaplandı (263 eleman)",
           15, 400, P["metin2"])
    etiketler = [
        ("1", "secsuz-pratik.png", "Pratik katman — Kesit listesi, Kat 2 ve HE340A veya IPE400 → 51 eleman; L100x10 üzerinde canlı önizleme"),
        ("2", "secsuz-kat.png", "Kat ölçütü — Benzer katlar kapsamı + köşe kolon → 12 kolon; durum çubuğuyla eşzamanlı"),
        ("3", "secsuz-gelismis.png", "Gelişmiş — çipler kural satırına döndü + Uzunluk > 5,00 m → 31 kiriş; Süzgeç olarak kaydet"),
        ("4", "sec-menusu.png", "Girişler — şerit Seç menüsü (ölçüte göre, canlı sayılar) ve elemana sağ tık"),
        ("5", "yuk-ata-hedef.png", "Atama tümleşimi — YÜKATA Hedef istemi: Kat · Kesit · Kullanım yeri … → 42 dış kiriş"),
    ]
    for i, (no, ad, aciklama) in enumerate(etiketler):
        r, c = divmod(i, 2)
        x = pad + c * (gw + pad)
        y = bas_h + r * (gh + et_h + pad)
        im = Image.open(yollar[ad]).convert("RGB").resize((gw, gh), Image.LANCZOS)
        t.golge(x, y + et_h, gw, gh, r=6, yaricap=10, alfa=0.16, dy=4)
        t.yapistir(im, x, y + et_h)
        t.dikdortgen(x, y + et_h, gw, gh, kenar=P["cizgi"])
        t.daire(x + 14, y + 20, 14, dolgu=P["vurgu"])
        t.yazi_orta(x + 14, y + 26, no, 15, 700, "#FFFFFF")
        t.yazi(x + 38, y + 27, ad, 16, 600, P["metin"])
        t.yazi(x + 38 + t.yazi_gen(ad, 16, 600) + 14, y + 27, aciklama, 14, 400, P["metin2"])
    # 6. hücre: hibrit özeti
    x = pad + (gw + pad)
    y = bas_h + 2 * (gh + et_h + pad) + et_h
    t.dikdortgen(x, y, gw, gh, dolgu=P["yuzey"], kenar=P["cizgi"], r=6)
    yy = y + 48
    t.yazi(x + 36, yy, "Hibrit: iki katman, tek yer", 22, 600, P["metin"])
    yy += 40
    maddeler = [
        ("Pratik (varsayılan)", "Sol: 14 ölçüt kategorisi · sağ: sayılı onay listesi (n / N) · tık anında uygular."),
        ("Birleştirme", "Aynı ölçütte veya · ölçütler arasında ve — üstte çip olarak yazılı: “Kat 2 ve HE340A veya IPE400”."),
        ("Kip", "Yeni seçim / Ekle / Çıkar / Kesişim — taban seçime göre; Ctrl+tık ekle, Shift+tık çıkar."),
        ("Kat kapsamı", "Bu kat / Benzer katlar / Tüm katlar = Kat ölçütünü üretir; durum çubuğuyla aynı anahtar."),
        ("Hızlı eylemler", "Tümü · Tersine çevir · Önceki · Temizle · Benzerini seç · Yalnız seçili · Grup olarak kaydet."),
        ("Gelişmiş (isteğe bağlı)", "Çipler kural satırına dönüşür (boş editör yok); sayısal / metin / boş-dolu, tek düzey veya grubu."),
        ("Kaydet", "Süzgeç olarak kaydet → seçim süzgeci, görünüm süzgeci, renk kuralı: tek motor, sorgu dili §11.3."),
        ("Girişler", "Şerit Seç menüsü (ölçüte göre), sağ tık (Bu kesittekileri / kattakileri…), Ctrl+F, komutların Hedef istemi."),
    ]
    for b, m in maddeler:
        t.daire(x + 42, yy - 5, 4, dolgu=P["vurgu"])
        t.yazi(x + 56, yy, b, 15, 600, P["metin"])
        t.yazi(x + 56, yy + 22, m, 13.5, 400, P["metin2"])
        yy += 54
    return t


def ana():
    t0 = time.time()
    hedef = None
    if "--yalniz" in sys.argv:
        hedef = set(sys.argv[sys.argv.index("--yalniz") + 1].split(","))
    isler = [("secsuz-pratik.png", ekran_pratik), ("secsuz-kat.png", ekran_kat), ("secsuz-gelismis.png", ekran_gelismis),
             ("sec-menusu.png", ekran_menu), ("yuk-ata-hedef.png", ekran_yuk)]
    yollar = {}
    for ad, fn in isler:
        yol = os.path.join(BURASI, ad)
        yollar[ad] = yol
        if hedef and ad.split(".")[0] not in hedef and ad not in hedef:
            continue
        tt = fn(2)   # 2× çizip 1920×1080'e LANCZOS ile indir: küçük puntoda harf aralıkları doğru kalır
        tt.img.resize((1920, 1080), Image.LANCZOS).save(yol, optimize=True)
        print(f"yazıldı: {yol} ({time.time() - t0:.1f} s)")
    if not hedef or "karsilastirma" in hedef:
        k = karsilastirma(yollar)
        yol = os.path.join(BURASI, "karsilastirma.png")
        k.img.save(yol, optimize=True)
        print(f"yazıldı: {yol} {k.img.size}")
    print(f"bitti ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    ana()
