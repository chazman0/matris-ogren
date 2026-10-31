#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
op4 arayüz yönü B — "Atölye · Modern": Atölye iskeleti (şerit, sol ray, model ağacı, Özellikler + dikey pencere
şeridi, sekmeli rıhtım, komut satırı, kat kapsamlı durum çubuğu) korunarak modernleştirilmiş taslak görselleri.

Üretilenler (bu klasöre):
  ana-kobalt.png · ana-petrol.png · ana-grafit.png   1920×1080, üç vurgu seçeneği, aynı içerik
  kucuk.png                                          1366×768, varsayılan (kobalt), "sıkı" yoğunluk
  ayarlar-program.png · ayarlar-goruntu.png · ayarlar-dil.png   1920×1080, Ayarlar penceresi (karartılmış program üstünde)
  detay-serit.png · detay-panel.png                  2× kırpımlar (kobalt)
  karsilastirma.png                                  2400 px: üç vurgu + üç Ayarlar sayfası

Bütün renk/yarıçap/aralık/yazı değerleri belirtec.py'dedir (palet değişimi tek satır).
Çalıştırma:  python3 uret.py           (tümü)
             python3 uret.py --hizli   (yalnız ana-kobalt.png)
"""
import os
import sys
import time
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import belirtec
from belirtec import C, R, OLCU, DC_RENK, DC_ESIK, hex2rgb, rgba, karisim, ustundeki_metin, palet_uygula
from tuval import Tuval, taban, logo_simge
from sahne import sahne_ciz, X_AKS, Z_KAT, PROFILLER

BURASI = os.path.dirname(os.path.abspath(__file__))
PROJE = "Depo Binası – Tokat OSB"


# ============================================================================
# YERLEŞİM
# ============================================================================
class Yerlesim:
    def __init__(self, W, H, yogunluk="rahat"):
        self.W, self.H = W, H
        self.yog = yogunluk
        self.kucuk = yogunluk == "siki"
        O = OLCU[yogunluk]
        self.O = O
        for k_, v in O.items():
            setattr(self, k_, v)
        self.ust = O["baslik"] + O["sekme"] + O["serit"]
        self.alt = H - O["durum"] - O["komut"] - O["rihtim"] - O["rihtim_sekme"]
        self.vp_x0 = O["ray"] + O["agac"]
        self.vp_x1 = W - O["pencere_seridi"] - O["ozel"]
        self.vp_y0 = self.ust + O["gsekme"]
        self.vp_y1 = self.alt
        self.vp_w, self.vp_h = self.vp_x1 - self.vp_x0, self.vp_y1 - self.vp_y0


# ============================================================================
# BAŞLIK ÇUBUĞU
# ============================================================================
def baslik_cubugu(t, L):
    W, h = L.W, L.baslik
    t.dikdortgen(0, 0, W, h, dolgu=C["zemin"])
    simge = logo_simge()
    lh = 16 if not L.kucuk else 15
    lw = lh * simge.width / simge.height
    t.resim(simge, 14, (h - lh) / 2, w=lw, h=lh)
    x = 14 + lw + 8
    t.yazi(x, taban(0, h, 13), "op4", 13, 600, C["metin"])
    x += t.yazi_gen("op4", 13, 600) + 12
    t.dikey(x, 9, h - 9, C["cizgi"])
    x += 8
    for ad in ("yeni", "ac", "kaydet", "yazdir", None, "geri_al", "yinele"):
        if ad is None:
            t.dikey(x + 4, 9, h - 9, C["cizgi"]); x += 10; continue
        t.simge(ad, x + 14, h / 2, 16, C["simge"], 1.4); x += 28
    ad = f"{PROJE}.op4"
    tw = t.yazi_gen(ad, 12, 500)
    cx = W / 2
    t.yazi(cx - tw / 2, taban(0, h, 12), ad, 12, 500, C["metin"])
    t.daire(cx + tw / 2 + 10, h / 2, 3, dolgu=C["uyari_dolgu"])
    t.yazi(cx + tw / 2 + 18, taban(0, h, 11), "kaydedilmedi", 11, 400, C["metin3"])
    # sağ: kullanıcı · Ayarlar · yardım · pencere düğmeleri
    xr = W - 46 * 3 - 8
    for ad, ip in (("yardim", "Yardım"), ("disli", "Ayarlar (Ctrl+,)")):
        xr -= 28
        t.simge(ad, xr + 14, h / 2, 16, C["simge"], 1.4)
    xr -= 10
    t.dikey(xr, 9, h - 9, C["cizgi"])
    xr -= 12
    if not L.kucuk:
        kul = "Opus Fortis · Proje Mühendisi"
        t.yazi_sag(xr, taban(0, h, 11), kul, 11, 400, C["metin3"])
    for i, ad in enumerate(("kucult", "buyut", "kapat")):
        t.simge(ad, W - 46 * (3 - i) + 23, h / 2, 13, C["simge"], 1.2)


# ============================================================================
# ŞERİT
# ============================================================================
SEKMELER = ["Model", "Düzenle", "Yükler", "Analiz", "Tasarım", "Görünüm", "Raporlar"]

GRUPLAR_MODEL = [
    ("Aks & Kat", [("aks", "Aks", ""), ("kat", "Kat", "")],
     [("izgara", "Aks sistemi…", False), ("kat_verisi", "Kat verisi…", False), ("duzlem", "Çalışma düzlemi", True)], True),
    ("Kolon", [("kolon", "Kolon", "")], [("kolon", "Çelik", False), ("kolon", "Betonarme", False), ("kolon", "Kompozit", False)], False),
    ("Kiriş", [("kiris", "Kiriş", "basili")], [("kiris_ana", "Ana kiriş", False), ("kiris_tali", "Tali kiriş", False), ("asik", "Aşık", False)], False),
    ("Çapraz", [("capraz", "Çapraz", "")], [("capraz", "X çapraz", False), ("capraz_v", "V / Λ çapraz", False), ("capraz_tek", "Tek diyagonal", False)], False),
    ("Döşeme", [("doseme", "Döşeme", "")], [("doseme", "Betonarme", False), ("doseme", "Kompozit", False), ("doseme_bosluk", "Boşluk", False)], False),
    ("Duvar", [("duvar", "Duvar", "")], [("duvar", "Perde", False), ("duvar", "Dolgu", False), ("doseme_bosluk", "Açıklık", False)], False),
    ("Temel", [("temel", "Temel", "")], [("temel", "Tekil", False), ("temel_surekli", "Sürekli", False), ("temel_radye", "Radye", False)], False),
    ("Hızlı yerleştir", [("hizli_kolon", "Hızlı kolon", ""), ("hizli_kiris", "Hızlı kiriş", "")],
     [("hizli_capraz", "Hızlı çapraz", False), ("kiris_tali", "Tali kirişler…", False), ("kopyala_kat", "Kat kopyala…", False)], True),
    ("Seç", [("sec", "Seç", ""), ("sec_suz", "Seç ve Süz", "")],
     [("benzer", "Benzerini seç", False), ("katman", "Kata göre", True), ("ters", "Tersine çevir", False)], True),
]
KUCUKTE_GIZLI = ("Kolon", "Çapraz", "Döşeme", "Duvar", "Temel")


def serit(t, L, etkin="Model", gruplar=None):
    W = L.W
    gruplar = gruplar or GRUPLAR_MODEL
    y0, sh = L.baslik, L.sekme
    t.dikdortgen(0, y0, W, sh, dolgu=C["zemin"])
    # Dosya: vurgu dolgulu düğme (arka plan menüsü)
    dh = sh - 8
    dw = t.yazi_gen("Dosya", 12, 600) + 24
    t.dikdortgen(8, y0 + 4, dw, dh, dolgu=C["vurgu"], r=R["orta"])
    t.yazi_orta(8 + dw / 2, taban(y0 + 4, dh, 12), "Dosya", 12, 600, ustundeki_metin(C["vurgu"]))
    x = 8 + dw + 10
    govde_y = y0 + sh
    for ad in SEKMELER:
        tw = t.yazi_gen(ad, 12, 600)
        w = tw + 24
        if ad == etkin:
            t.yazi(x + 12, taban(y0, sh, 12), ad, 12, 600, C["metin"])
            t.dikdortgen(x + 8, govde_y - 3, w - 16, 3, dolgu=C["vurgu"], r=1.5)
        else:
            t.yazi(x + 12, taban(y0, sh, 12), ad, 12, 500, C["metin2"])
        x += w
    # sağ: Şeridi özelleştir · daralt
    xr = W - 12
    t.simge("sevron_ust", xr - 8, y0 + sh / 2, 14, C["simge2"], 1.5)
    xr -= 26
    et = "Şeridi özelleştir"
    t.yazi_sag(xr, taban(y0, sh, 11), et, 11, 500, C["metin2"])
    t.simge("goz", xr - t.yazi_gen(et, 11, 500) - 12, y0 + sh / 2, 14, C["simge2"], 1.4)
    # gövde
    by = govde_y
    t.dikdortgen(0, by, W, L.serit, dolgu=C["yuzey"])
    t.yatay(0, W, by - 1, C["cizgi"])
    t.yatay(0, W, by + L.serit - 1, C["cizgi"])
    bh = L.serit - 28                    # büyük düğme yüksekliği
    ks = L.kucuk_satir
    x = 8
    for gi, (gad, buyuk, kucukler, baslatici) in enumerate(gruplar):
        gx0 = x
        x += 4
        for ik, et, durum in buyuk:
            bw = max(52, t.yazi_gen(et, 11, 600) + 16)
            if durum == "basili":
                t.dikdortgen(x, by + 6, bw, bh, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=R["orta"])
            renk_s = C["vurgu"] if durum == "basili" else C["simge"]
            t.simge(ik, x + bw / 2, by + 6 + bh * 0.38, 24, renk_s, 1.5)
            t.yazi_orta(x + bw / 2, by + 6 + bh - 9, et, 11, 600 if durum == "basili" else 500,
                        C["vurgu_metin"] if durum == "basili" else C["metin"])
            x += bw + 2
        if kucukler and not (L.kucuk and gad in KUCUKTE_GIZLI):
            x += 4
            kw = max(t.yazi_gen(et, 11, 400) + (14 if ac else 0) for _, et, ac in kucukler) + 32
            for j, (ik, et, acilir) in enumerate(kucukler):
                yy = by + 7 + j * ks
                t.simge(ik, x + 10, yy + ks / 2, 16, C["simge"], 1.4)
                t.yazi(x + 24, taban(yy, ks, 11), et, 11, 400, C["metin"])
                if acilir:
                    t.sevron(x + 24 + t.yazi_gen(et, 11, 400) + 9, yy + ks / 2 + 0.5, "asagi", 10, C["metin3"])
            x += kw
        x += 6
        gw = x - gx0
        gy = by + L.serit - 9
        t.yazi_orta(gx0 + gw / 2 - (5 if baslatici else 0), gy, gad, 10, 500, C["metin3"])
        if baslatici:
            t.simge("baslatici", x - 9, gy - 3.5, 10, C["metin3"], 1.8)
        t.dikey(x, by + 10, by + L.serit - 10, C["cizgi2"])
        x += 1


# ============================================================================
# SOL RAY: hızlı çizim paleti + seçim anahtarları
# ============================================================================
PALET = [("sec", "Seç"), ("kolon", "Kolon"), ("kiris", "Kiriş"), ("capraz", "Çapraz"), ("doseme", "Döşeme"),
         ("duvar", "Duvar"), ("temel", "Temel"), ("aks", "Aks"), ("yuk", "Yük"), ("mesnet", "Mesnet"), ("olcu", "Ölçü")]
ANAHTARLAR = [("sec_pencere", True), ("dugum", True), ("kolon", True), ("kiris", True), ("doseme", False), ("duvar", False),
              ("aks", False), ("yuk", False), ("mesnet", True), ("temel", False)]


def ray(t, L):
    rw = L.ray
    y0, y1 = L.ust, L.H - L.durum
    t.dikdortgen(0, y0, rw, y1 - y0, dolgu=C["zemin"])
    t.dikey(rw - 1, y0, y1, C["cizgi"])
    bd = L.ray_dugme
    bx = (rw - 1 - bd) / 2
    y = y0 + 8
    t.yazi_aralikli(rw / 2, y + 9, "ÇİZ", 9, 600, C["metin3"], 0.6, orta=True)
    y += 16
    palet = PALET if not L.kucuk else PALET[:7] + [("nokta3", "Diğer araçlar")]
    for ik, et in palet:
        secili = ik == "kiris"
        if secili:
            t.dikdortgen(bx, y, bd, bd, dolgu=C["vurgu_ton"], r=R["orta"])
            t.dikdortgen(0, y + 8, 3, bd - 16, dolgu=C["vurgu"], r=1.5)
        t.simge(ik, bx + bd / 2, y + bd / 2, 18 if not L.kucuk else 16, C["vurgu"] if secili else C["simge"], 1.5)
        y += bd
    y += 8
    t.yatay(10, rw - 10, y, C["cizgi"])
    y += 8
    t.yazi_aralikli(rw / 2, y + 9, "SEÇ", 9, 600, C["metin3"], 0.6, orta=True)
    y += 16
    ah = bd - 4 if not L.kucuk else bd - 6
    for ik, acik in ANAHTARLAR:
        if acik:
            t.dikdortgen(bx + 1, y, bd - 2, ah, dolgu=C["yuzey"], kenar=C["cizgi"], r=R["orta"])
            t.simge(ik, bx + bd / 2, y + ah / 2, 16, C["simge"], 1.5)
            t.daire(bx + bd - 6, y + 5, 2.2, dolgu=C["vurgu"])
        else:
            t.simge(ik, bx + bd / 2, y + ah / 2, 16, C["metin4"], 1.5)
        y += ah + 2
    y += 6
    t.yatay(10, rw - 10, y, C["cizgi"])
    y += 8
    # doğrudan değiştirme (açık) + anahtarları gizle
    t.dikdortgen(bx, y, bd, bd, dolgu=C["secim_ton"], kenar=C["secim_ton2"], r=R["orta"])
    t.simge("dm", bx + bd / 2, y + bd / 2, 18, C["secim"], 1.6)
    y += bd + 2
    if not L.kucuk:   # sıkı yoğunlukta "anahtarları gizle" taşma menüsüne geçer
        t.simge("goz", bx + bd / 2, y + bd / 2, 16, C["simge2"], 1.4)


# ============================================================================
# MODEL AĞACI
# ============================================================================
AGAC = [
    # (derinlik, simge, metin, sağ metin, durum, açık?)
    (0, "proje", PROJE, "", "kok", True),
    (1, "aks", "Aks sistemi", "A–D × 1–5", "", False),
    (1, "kat", "Katlar", "3", "", True),
    (2, "kat", "Kat 3 (Çatı)", "+13,50", "", False),
    (2, "kat", "Kat 2", "+9,00", "etkin", True),
    (3, "kolon", "Kolonlar", "20", "", False),
    (3, "kiris", "Kirişler · IPE400", "31", "", True),
    (4, "kiris_ana", "Ana çerçeve", "15", "secili", False),
    (4, "kiris_ana", "Bağ kirişleri", "16", "", False),
    (3, "kiris_tali", "Tali kirişler · IPE200", "12", "", False),
    (3, "capraz", "Çaprazlar · L100×10", "8", "", False),
    (3, "doseme", "Döşemeler", "1", "", False),
    (2, "kat", "Kat 1", "+4,50", "", False),
    (2, "kat", "Zemin", "±0,00", "", False),
    (1, "kesit", "Kesitler", "4", "", False),
    (1, "malzeme", "Malzemeler", "2", "", False),
    (1, "yuk", "Yük desenleri", "5", "", False),
    (1, "tablo", "Yük durumları", "5", "", False),
    (1, "tablo", "Kombinasyonlar", "14", "", False),
    (1, "katman", "Gruplar", "3", "", False),
    (1, "analiz", "Analiz modeli", "", "yaprak", False),
]


def panel_golgesi(t, x, y0, y1, yon=1, gen=8):
    """Panelden görünüme düşen çok yumuşak gölge (yon=+1 sağa, -1 sola)."""
    for i in range(gen):
        a = 0.055 * (1 - i / gen) ** 2
        xx = x + i if yon > 0 else x - 1 - i
        t.dikey(xx, y0, y1, rgba(C["golge"], a))


def panel_basligi(t, x0, y0, w, h, baslik, simgeler):
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.yazi(x0 + 12, taban(y0, h, 13), baslik, 13, 600, C["metin"])
    xr = x0 + w - 10
    for ad in reversed(simgeler):
        t.simge(ad, xr - 10, y0 + h / 2, 14, C["simge2"], 1.4)
        xr -= 26


def model_agaci(t, L):
    x0, y0, w = L.ray, L.ust, L.agac
    h = L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.dikey(x0 + w - 1, y0, y0 + h, C["cizgi"])
    ph = L.panel_baslik
    panel_basligi(t, x0, y0, w - 1, ph, "Model ağacı", ["pin", "kapat"])
    # segmentli sekmeler
    sy = y0 + ph
    t.segmentli(x0 + 12, sy, ["Model", "Göster", "Tablolar", "Raporlar"], 0, h=L.segment, boyut=11 if not L.kucuk else 10, w=w - 25)
    # arama
    ay = sy + L.segment + 8
    t.giris(x0 + 12, ay, w - 25, L.arama, "Ağaçta ara (ad, kesit, etiket)", 11, renk=C["metin3"], simge="ara", ek="Ctrl+F" if not L.kucuk else None)
    # satırlar
    y = ay + L.arama + 8
    rh = L.satir_agac
    alt_bilgi = 32
    girinti = 16 if not L.kucuk else 12
    for derin, ik, metin, sag, durum, acik in AGAC:
        if y + rh > L.alt - alt_bilgi - 4:
            break
        ix = x0 + 10 + derin * girinti
        # girinti kılavuzları (1. düzeyden itibaren)
        for p in range(1, derin):
            gx = x0 + 10 + p * girinti + 6
            t.dikey(gx, y, y + rh, C["cizgi2"])
        if durum == "secili":
            t.dikdortgen(x0 + 6, y + 1, w - 13, rh - 2, dolgu=C["secim_ton"], r=R["orta"])
            t.dikdortgen(x0 + 6, y + 5, 3, rh - 10, dolgu=C["secim"], r=1.5)
        cocuk = durum not in ("yaprak",) and derin < 4 and metin not in ("Aks sistemi",)
        if cocuk:
            t.sevron(ix + 6, y + rh / 2, "asagi" if acik else "sag", 10, C["metin3"])
        simge_renk = C["secim"] if durum == "secili" else (C["vurgu"] if durum == "etkin" else C["simge2"])
        t.simge(ik, ix + 22, y + rh / 2, 14, simge_renk, 1.4)
        agir = 600 if durum in ("kok", "etkin", "secili") else 400
        sag_w = (t.yazi_gen(sag, 11, 400, True) + 12) if sag else 0
        ek_w = 0
        if durum == "secili":
            ek_w = (t.yazi_gen("6 seçili" if not L.kucuk else "6", 9, 600) + 12) + 8
        if durum == "etkin":
            ek_w = t.yazi_gen("etkin", 9, 600) + 12 + 8 + 18
        maxw = (x0 + w - 12) - (ix + 32) - sag_w - ek_w
        t.yazi(ix + 32, taban(y, rh, 12), t.yazi_kes(metin, maxw, 12, agir), 12, agir, C["metin"])
        xr = x0 + w - 14
        if sag:
            t.yazi_sag(xr, taban(y, rh, 11), sag, 11, 400 if durum != "etkin" else 500, C["metin3"] if durum != "etkin" else C["metin2"], tnum=True)
            xr -= t.yazi_gen(sag, 11, 400, True) + 8
        if durum == "secili":
            t.rozet(xr, y + (rh - 16) / 2, "6 seçili" if not L.kucuk else "6", C["secim"], sag=True)
        if durum == "etkin":
            ew = t.yazi_gen("etkin", 9, 600) + 12
            t.dikdortgen(xr - ew, y + (rh - 16) / 2, ew, 16, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=R["kucuk"])
            t.yazi_orta(xr - ew / 2, taban(y + (rh - 16) / 2, 16, 9), "etkin", 9, 600, C["vurgu_metin"])
            t.simge("goz", xr - ew - 12, y + rh / 2, 13, C["simge2"], 1.3)
        y += rh
    # alt bilgi
    oy = L.alt - alt_bilgi
    t.yatay(x0, x0 + w - 1, oy, C["cizgi2"])
    t.yazi(x0 + 12, taban(oy, alt_bilgi, 11), "263 eleman · 80 düğüm · 3 kat", 11, 400, C["metin3"], tnum=True)
    t.simge("sigdir", x0 + w - 22, oy + alt_bilgi / 2, 14, C["simge2"], 1.4)


# ============================================================================
# GÖRÜNÜM SEKMELERİ + 3B GÖRÜNÜM
# ============================================================================
def gorunum_sekmeleri(t, L, etkin="3B görünüm"):
    x0, y0, w, h = L.vp_x0, L.ust, L.vp_w, L.gsekme
    t.dikdortgen(x0, y0, w, h, dolgu=C["zemin"])
    x = x0 + 8
    sekmeler = [("bina3", "3B görünüm"), ("plan", "Plan – Kat 2 (+9,00)"), ("yukselti", "Yükselti – Aks 1")]
    for ik, ad in sekmeler:
        tw = t.yazi_gen(ad, 11, 600) + 40
        if ad == etkin:
            t.dikdortgen(x, y0 + 4, tw, h - 4 + 8, dolgu=C["cizgi"], r=R["orta"])
            t.dikdortgen(x + 1, y0 + 5, tw - 2, h - 5 + 8, dolgu=C["vp_ust"], r=R["orta"] - 1)
            t.simge(ik, x + 16, y0 + 4 + (h - 4) / 2, 14, C["vurgu"], 1.4)
            t.yazi(x + 28, taban(y0 + 4, h - 4, 11), ad, 11, 600, C["metin"])
        else:
            t.simge(ik, x + 16, y0 + 4 + (h - 4) / 2, 14, C["simge2"], 1.4)
            t.yazi(x + 28, taban(y0 + 4, h - 4, 11), ad, 11, 500, C["metin2"])
        x += tw + 4
    t.simge("artı", x + 12, y0 + 4 + (h - 4) / 2, 14, C["simge2"], 1.5)
    if not L.kucuk:
        t.yazi_sag(x0 + w - 12, taban(y0, h, 10), "Görünüm özellikleri: arka plana çift tık", 10, 400, C["metin3"])
    return x0, y0 + h


def pil_kap(t, x, y, w, h):
    t.golge(x, y, w, h, r=R["buyuk"], tur="yuzen")
    t.dikdortgen(x, y, w, h, dolgu=rgba(C["yuzey"], 0.96), kenar=C["cizgi"], r=R["buyuk"])


def viewport(t, L, mod="secim", sahne_onbellek=None):
    x0, y0, w, h = L.vp_x0, L.vp_y0, L.vp_w, L.vp_h
    key = (w, h, t.s, mod, C["palet"])
    sc = sahne_onbellek.get(key) if sahne_onbellek is not None else None
    if sc is None:
        sc = sahne_ciz(w, h, t.s, ss=2, mod=mod)
        if sahne_onbellek is not None:
            sahne_onbellek[key] = sc
    t.yapistir(sc.im, x0, y0)
    # görünüm üst kenarı: etkin sekme dışında ince çizgi
    t.yatay(x0, x0 + w, y0 - 1, C["cizgi"])
    akt_w = t.yazi_gen("3B görünüm", 11, 600) + 40
    t.yatay(x0 + 9, x0 + 8 + akt_w - 1, y0 - 1, C["vp_ust"])

    def iz(p):
        q = sc.iz(p)
        return (x0 + q[0], y0 + q[1])

    # --- üst sol: görünüm araç pili ---
    ph = 32
    px, py = x0 + 12, y0 + 12
    parcalar = [("bina3", "3B"), ("perspektif", "Perspektif"), ("katman", "Tüm katlar"), ("etiket", "Renk: türe göre")]
    if L.kucuk:
        parcalar = parcalar[:3]
    pw = 8
    for ik, et in parcalar:
        pw += 22 + t.yazi_gen(et, 11, 500) + 16 + 9
    pw += 60 + 6
    pil_kap(t, px, py, pw, ph)
    cx = px + 10
    for ik, et in parcalar:
        t.simge(ik, cx + 7, py + ph / 2, 14, C["simge2"], 1.4)
        t.yazi(cx + 20, taban(py, ph, 11), et, 11, 500, C["metin"])
        cx += 20 + t.yazi_gen(et, 11, 500)
        t.sevron(cx + 8, py + ph / 2 + 0.5, "asagi", 10, C["metin3"])
        cx += 18
        t.dikey(cx, py + 8, py + ph - 8, C["cizgi"])
        cx += 8
    # çubuk ↔ ekstrüde: ikonlu segmentli
    sx = cx
    t.dikdortgen(sx, py + 4, 56, ph - 8, dolgu=C["zemin2"], r=R["orta"])
    t.dikdortgen(sx + 28, py + 7, 26, ph - 13, dolgu=rgba(C["golge"], 0.10), r=R["kucuk"])
    t.dikdortgen(sx + 28, py + 6, 26, ph - 12, dolgu=C["yuzey"], r=R["kucuk"])
    t.simge("cubuk", sx + 15, py + ph / 2, 14, C["simge2"], 1.4)
    t.simge("kati", sx + 41, py + ph / 2, 14, C["vurgu"], 1.4)
    # --- üst sağ: görünüm düğmeleri grubu (küp yok) ---
    dugmeler = ("ev", "sigdir", "kesit_duzlemi", "goz")
    gw = 32 * len(dugmeler) + 4
    gx = x0 + w - 12 - gw
    pil_kap(t, gx, py, gw, ph)
    for i, ad in enumerate(dugmeler):
        bx = gx + 2 + i * 32
        t.simge(ad, bx + 16, py + ph / 2, 16, C["simge2"], 1.4)
        if i:
            t.dikey(bx, py + 8, py + ph - 8, C["cizgi2"])
    # --- alt sol: eksen üçlüsü ---
    ox, oy = x0 + 40, y0 + h - 40
    t.daire(ox, oy, 26, dolgu=rgba(C["yuzey"], 0.55))
    for ad, v, renk in (("X", (1, 0, 0), C["eksen_x"]), ("Y", (0, 1, 0), C["eksen_y"]), ("Z", (0, 0, 1), C["eksen_z"])):
        dx, dy = sc.eksen_vektor(v)
        Ln = (dx * dx + dy * dy) ** 0.5 or 1
        ex, ey = ox + dx / Ln * 20, oy - dy / Ln * 20
        t.cizgi(ox, oy, ex, ey, renk, 1.6)
        t.yazi_orta(ex + dx / Ln * 8, ey - dy / Ln * 8 + 3.5, ad, 10, 600, renk)
    t.daire(ox, oy, 2.5, dolgu=C["metin2"])
    # --- alt sağ: gezinme bilgisi çipi ---
    if mod != "dc":
        bilgi = "Perspektif 30° · Sol sürükle: kaydır · Shift+sol: döndür · Tekerlek: yakınlaş" if not L.kucuk else "Shift+sol: döndür · Tekerlek: yakınlaş"
        bw = t.yazi_gen(bilgi, 10, 500) + 20
        bx, by = x0 + w - 12 - bw, y0 + h - 12 - 24
        t.dikdortgen(bx, by, bw, 24, dolgu=rgba(C["yuzey"], 0.80), kenar=rgba(C["cizgi"], 0.9), r=R["orta"])
        t.yazi(bx + 10, taban(by, 24, 10), bilgi, 10, 500, C["metin2"])
    if mod == "secim":
        secim_notlari(t, L, sc, iz)
    return sc


def secim_notlari(t, L, sc, iz):
    """Doğrudan değiştirme tutamaçları, ölçü etiketi, bağlamsal mini araç çubuğu, imleç + üzerinde ipucu."""
    kir = PROFILLER["IPE400"]; kol = PROFILLER["HE340A"]
    zc = Z_KAT[2] - kir[0] / 2
    p0 = (X_AKS[1] + kol[0] / 2, 0.0, zc); p1 = (X_AKS[2] - kol[0] / 2, 0.0, zc)
    a, b = iz(p0), iz(p1)
    m = iz(((p0[0] + p1[0]) / 2, 0.0, zc))
    # ölçü etiketi
    u = iz(((p0[0] + p1[0]) / 2, 0.0, zc - 0.85))
    a2 = iz((p0[0], 0.0, zc - 0.85)); b2 = iz((p1[0], 0.0, zc - 0.85))
    et = "5 670"
    ew = t.yazi_gen(et, 11, 600, True) + 16
    t.cizgi(a2[0], a2[1], u[0] - ew / 2 - 3, u[1], C["secim"], 1)
    t.cizgi(u[0] + ew / 2 + 3, u[1], b2[0], b2[1], C["secim"], 1)
    for q in (a2, b2):
        t.cizgi(q[0], q[1] - 4, q[0], q[1] + 4, C["secim"], 1)
    t.golge(u[0] - ew / 2, u[1] - 10, ew, 20, r=R["kucuk"], tur="yuzen", alfa=0.08)
    t.dikdortgen(u[0] - ew / 2, u[1] - 10, ew, 20, dolgu=C["yuzey"], kenar=C["secim"], r=R["kucuk"])
    t.yazi_orta(u[0], taban(u[1] - 10, 20, 11), et, 11, 600, C["metin"], tnum=True)
    # tutamaçlar: başlangıç = dolu kare, bitiş = içi boş kare (renk körlüğünde de ayrışır), orta = daire
    t.dikdortgen(a[0] - 6, a[1] - 6, 12, 12, dolgu=C["yuzey"], r=2)
    t.dikdortgen(a[0] - 4, a[1] - 4, 8, 8, dolgu=C["secim"], r=1)
    t.dikdortgen(b[0] - 6, b[1] - 6, 12, 12, dolgu=C["secim"], r=2)
    t.dikdortgen(b[0] - 3.5, b[1] - 3.5, 7, 7, dolgu=C["yuzey"], r=1)
    t.daire(m[0], m[1], 5, dolgu=C["yuzey"], kenar=C["secim"], kalinlik=1.5)
    # bağlamsal mini araç çubuğu (açılır pencere biçimi)
    alanlar = [("kiris", "IPE400"), ("malzeme", "S355"), ("kat", "Kat 2"), ("mafsal", "Mafsal")]
    ch = 32
    cw = 8
    for ik, et_ in alanlar:
        cw += 20 + t.yazi_gen(et_, 11, 500) + 18 + 9
    cw += 3 * 28 + 4
    merkez = iz((5.5, 2.5, Z_KAT[2]))
    cx, cy = merkez[0] - cw / 2, merkez[1] - 78
    t.golge(cx, cy, cw, ch, r=R["buyuk"], tur="acilir")
    t.dikdortgen(cx, cy, cw, ch, dolgu=C["yuzey"], kenar=C["cizgi"], r=R["buyuk"])
    x = cx + 10
    for ik, et_ in alanlar:
        t.simge(ik, x + 7, cy + ch / 2, 14, C["simge2"], 1.4)
        t.yazi(x + 20, taban(cy, ch, 11), et_, 11, 500, C["metin"])
        x += 20 + t.yazi_gen(et_, 11, 500)
        t.sevron(x + 8, cy + ch / 2 + 0.5, "asagi", 10, C["metin3"])
        x += 18
        t.dikey(x, cy + 8, cy + ch - 8, C["cizgi"])
        x += 9
    for ik in ("kopyala", "tasi", "sil"):
        t.simge(ik, x + 13, cy + ch / 2, 15, C["simge2"] if ik != "sil" else C["hata"], 1.4); x += 28
    # ok: araç çubuğu → seçim
    ax_ = cx + cw / 2
    t.cokgen([(ax_ - 6, cy + ch - 1), (ax_ + 6, cy + ch - 1), (ax_, cy + ch + 5)], dolgu=C["yuzey"])
    t.cizgi(ax_ - 6, cy + ch - 0.5, ax_, cy + ch + 5.5, C["cizgi"], 1)
    t.cizgi(ax_, cy + ch + 5.5, ax_ + 6, cy + ch - 0.5, C["cizgi"], 1)
    # imleç (A/1 kolonu üzerinde) + ipucu kartı
    hp = iz((X_AKS[0] + kol[0] / 2 + 0.05, -0.2, Z_KAT[1] + 2.4))
    t.simge("imlec", hp[0] + 6, hp[1] + 8, 18, C["metin"], 1.2)
    ip = "K2-A1"
    ip2 = "Kolon · HE340A · S355"
    iw = t.yazi_gen(ip, 11, 600) + t.yazi_gen(ip2, 11, 400) + 30
    ix_, iy_ = hp[0] + 18, hp[1] + 18
    t.golge(ix_, iy_, iw, 24, r=R["orta"], tur="acilir", alfa=0.12)
    t.dikdortgen(ix_, iy_, iw, 24, dolgu=C["yuzey"], kenar=C["cizgi"], r=R["orta"])
    t.daire(ix_ + 10, iy_ + 12, 3, dolgu=C["hover_model"])
    t.yazi(ix_ + 18, taban(iy_, 24, 11), ip, 11, 600, C["metin"])
    t.yazi(ix_ + 24 + t.yazi_gen(ip, 11, 600), taban(iy_, 24, 11), ip2, 11, 400, C["metin2"])


# ============================================================================
# ÖZELLİKLER PANELİ + PENCERE ŞERİDİ
# ============================================================================
OZELLIKLER_KIRIS = [
    ("Genel", True, "", [("Ad", "K2-1AB … K2-2CD", "coklu"), ("Tür", "Kiriş · çelik", "salt"), ("Kat", "Kat 2  (+9,00)", "acilir"),
                         ("Grup", "Ana çerçeve", "acilir"), ("Sınıf / renk", "3 · Çelik kiriş", "renk")]),
    ("Kesit", True, "", [("Kesit", "IPE400", "katalog"), ("Malzeme", "S355", "katalog"), ("Dönme", "0°", ""),
                         ("h × b · tw / tf", "400 × 180 · 8,6 / 13,5 mm", "salt")]),
    ("Konum", True, "", [("Başlangıç", "(farklı)", "coklu"), ("Bitiş", "(farklı)", "coklu"), ("Uzunluk", "5,670 m", "salt"),
                         ("Hizalama", "Orta · Üst", "acilir")]),
    ("Serbestlikler", True, "", [("Başlangıç ucu", "Mafsal", "uc_bas"), ("Bitiş ucu", "Mafsal", "uc_bit"), ("Mesnet", "Bağlı", "acilir")]),
    ("Yükler", True, "", [("Geçerli desen", "G · Sabit", "acilir"), ("Çizgisel yük", "G 4,20 · Q 7,50 kN/m", ""), ("Öz ağırlık", "Dahil", "onay")]),
    ("Analiz", False, "Çubuk · elastik", []),
    ("Tasarım", False, "dc", []),
]


def ozellikler(t, L):
    x0, y0, w = L.vp_x1, L.ust, L.ozel
    h = L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.dikey(x0, y0, y0 + h, C["cizgi"])
    ph = L.panel_baslik
    panel_basligi(t, x0 + 1, y0, w - 1, ph, "Özellikler", ["ara", "pin", "kapat"])
    # nesne başlığı
    oy = y0 + ph
    nh = L.nesne
    tile = 32 if not L.kucuk else 28
    ty = oy + (nh - tile) / 2 - 4
    t.dikdortgen(x0 + 12, ty, tile, tile, dolgu=C["secim_ton"], kenar=C["secim_ton2"], r=R["orta"])
    t.simge("kiris", x0 + 12 + tile / 2, ty + tile / 2, 18, C["secim"], 1.5)
    tx = x0 + 12 + tile + 10
    t.yazi(tx, ty + 13, "Kiriş", 13, 600, C["metin"])
    t.rozet(tx + t.yazi_gen("Kiriş", 13, 600) + 8, ty + 0.5, "6 seçili", C["secim"])
    alt = "IPE400 · S355 · Kat 2 (+9,00) · Aks 1–2"
    t.yazi(tx, ty + tile - 2, t.yazi_kes(alt, x0 + w - 40 - tx, 11, 400), 11, 400, C["metin3"])
    t.simge("nokta3", x0 + w - 22, ty + 8, 16, C["simge2"], 1.4)
    y = oy + nh
    t.yatay(x0 + 1, x0 + w, y - 1, C["cizgi2"])
    lw = 104 if not L.kucuk else 96
    vx = x0 + 16 + lw
    vw = w - 16 - lw - 14
    rh = L.satir_ozel
    fh = L.alan_h
    bolh = L.bolum
    alt_sinir = y0 + h - L.panel_alt
    tasti = False
    for bi, (bad, acik, ozet, satirlar) in enumerate(OZELLIKLER_KIRIS):
        if y + bolh > alt_sinir:
            tasti = True
            break
        if bi:
            t.yatay(x0 + 12, x0 + w - 12, y, C["cizgi2"])
        t.sevron(x0 + 18, y + bolh / 2, "asagi" if acik else "sag", 10, C["metin2"])
        t.yazi(x0 + 30, taban(y, bolh, 12), bad, 12, 600, C["metin"])
        if not acik and ozet == "dc":
            # özet: yönetmelik + D/C rozeti
            rw = t.rozet(x0 + w - 16, y + (bolh - 16) / 2, "0,62", DC_RENK[1], sag=True)
            t.yazi_sag(x0 + w - 16 - rw - 6, taban(y, bolh, 11), "ÇYTHYE 2018 · D/C", 11, 400, C["metin3"])
        elif not acik and ozet:
            t.yazi_sag(x0 + w - 16, taban(y, bolh, 11), ozet, 11, 400, C["metin3"])
        y += bolh
        if not acik:
            continue
        for etiket, deger, tur in satirlar:
            if y + rh > alt_sinir:
                tasti = True
                break
            t.yazi(x0 + 16, taban(y, rh, 12), t.yazi_kes(etiket, lw - 6, 12, 400), 12, 400, C["metin2"])
            fy = y + (rh - fh) / 2
            if tur == "katalog":
                fw = vw - fh - 4
                odak = etiket == "Kesit"
                t.giris(vx, fy, fw, fh, deger, 12, odak=odak, imlec=odak)
                t.dikdortgen(vx + fw + 4, fy, fh, fh, dolgu=C["alan"], kenar=C["alan_kenar"], r=R["orta"])
                t.simge("nokta3", vx + fw + 4 + fh / 2, fy + fh / 2, 12, C["simge2"], 1.4)
            elif tur == "acilir":
                t.acilir(vx, fy, vw, fh, deger, 12)
            elif tur in ("uc_bas", "uc_bit"):
                t.acilir(vx, fy, vw, fh, deger, 12)
                kx = vx + vw - 34
                if tur == "uc_bas":
                    t.dikdortgen(kx - 4, fy + fh / 2 - 4, 8, 8, dolgu=C["secim"], r=1)
                else:
                    t.dikdortgen(kx - 4.5, fy + fh / 2 - 4.5, 9, 9, dolgu=C["secim"], r=1.5)
                    t.dikdortgen(kx - 2, fy + fh / 2 - 2, 4, 4, dolgu=C["alan"])
            elif tur == "coklu":
                t.giris(vx, fy, vw, fh, deger, 12, renk=C["metin3"])
            elif tur == "salt":
                t.yazi(vx + 8, taban(y, rh, 12), t.yazi_kes(deger, vw - 8, 12, 400), 12, 400, C["metin"], tnum=True)
            elif tur == "renk":
                t.dikdortgen(vx + 8, fy + fh / 2 - 6, 12, 12, dolgu=C["kiris"], kenar=C["kenar"], r=3)
                t.yazi(vx + 26, taban(y, rh, 12), deger, 12, 400, C["metin"])
            elif tur == "onay":
                t.onay_kutusu(vx + 6, fy + (fh - 14) / 2, True, 14)
                t.yazi(vx + 28, taban(y, rh, 12), deger, 12, 400, C["metin"])
            else:
                t.giris(vx, fy, vw, fh, deger, 12)
            y += rh
        if tasti:
            break
    # kaydırma çubuğu
    if tasti:
        t.kaydirma(x0 + w - 7, oy + nh + 4, 0, oy + nh + 6, 220)
    # alt çubuk: Uygula / Al / Anında uygula
    fy = y0 + h - L.panel_alt
    t.dikdortgen(x0 + 1, fy, w - 1, L.panel_alt, dolgu=C["yuzey"])
    t.yatay(x0 + 1, x0 + w, fy, C["cizgi"])
    bh = 28 if not L.kucuk else 26
    t.dugme(x0 + 12, fy + (L.panel_alt - bh) / 2, 84, bh, "Uygula", "birincil")
    t.dugme(x0 + 104, fy + (L.panel_alt - bh) / 2, 52, bh, "Al", "ikincil")
    t.anahtar(x0 + w - 116, fy + (L.panel_alt - 16) / 2, True, 28, 16)
    t.yazi(x0 + w - 82, taban(fy, L.panel_alt, 11), "Anında uygula", 11, 500, C["metin2"])


PENCERELER = [("ozellik", "Özellikler"), ("kutuphane", "Kataloglar"), ("agac", "Model ağacı"), ("suz", "Filtre & görünürlük"), ("sorgu", "Sorgu")]


def pencere_seridi(t, L, etkin="Özellikler"):
    w = L.pencere_seridi
    x0, y0 = L.W - w, L.ust
    h = L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=C["zemin"])
    t.dikey(x0, y0, y0 + h, C["cizgi"])
    y = y0 + 8
    for ik, ad in PENCERELER:
        th = t.yazi_gen(ad, 11, 600) + 40 + (14 if ad == "Model ağacı" else 0)
        if y + th > y0 + h - 8:          # sığmayan pencere düğmesi yalnız simge olarak kalır
            t.simge(ik, x0 + w / 2, y + 14, 15, C["simge2"], 1.4)
            y += 32
            continue
        if ad == etkin:
            t.dikdortgen(x0 + 3, y, w - 6, th, dolgu=C["vurgu_ton"], r=R["orta"])
            t.dikdortgen(x0 + w - 3, y + 6, 3, th - 12, dolgu=C["vurgu"], r=1.5)
            t.simge(ik, x0 + w / 2, y + 14, 15, C["vurgu"], 1.5)
            t.yazi_dikey(x0 + w / 2 - 8, y + 28, ad, 11, 600, C["metin"])
        else:
            t.simge(ik, x0 + w / 2, y + 14, 15, C["simge2"], 1.4)
            t.yazi_dikey(x0 + w / 2 - 8, y + 28, ad, 11, 500, C["metin2"])
            if ad == "Model ağacı":  # sola yapıştırılmış
                t.simge("sol_yapistir", x0 + w / 2, y + th - 6, 10, C["metin3"], 1.3)
        y += th + 4
    t.yatay(x0 + 8, x0 + w - 8, y + 2, C["cizgi"])


# ============================================================================
# ALT RIHTIM + KOMUT SATIRI + DURUM ÇUBUĞU
# ============================================================================
DOCK_SATIRLAR = [
    ("KİRİŞ", "IPE400 · S355 · Kat 2 · Mafsal–Mafsal · kapsam: Benzer katlar", "6 kiriş eklendi (Kat 2) · 0,3 s", "ok"),
    ("SEÇ", "6 nesne seçildi: Kiriş ×6 · Kat 2 · Aks 1–2", "Enter: KİRİŞ'i yinele", ""),
]


def dock(t, L, satirlar=None):
    x0, y0, w = L.ray, L.alt, L.W - L.ray
    th, dh = L.rihtim_sekme, L.rihtim
    t.dikdortgen(x0, y0, w, th, dolgu=C["zemin"])
    t.yatay(x0, x0 + w, y0, C["cizgi"])
    t.yatay(x0, x0 + w, y0 + th - 1, C["cizgi"])
    x = x0 + 14
    for ad, rozet in (("Komut", ""), ("Mesajlar", "2"), ("Tablolar", "")):
        tw = t.yazi_gen(ad, 11, 600)
        if ad == "Komut":
            t.yazi(x, taban(y0, th, 11), ad, 11, 600, C["metin"])
            t.dikdortgen(x - 4, y0 + th - 3, tw + 8, 3, dolgu=C["vurgu"], r=1.5)
        else:
            t.yazi(x, taban(y0, th, 11), ad, 11, 500, C["metin2"])
        x += tw + 6
        if rozet:
            rw = t.rozet(x, y0 + (th - 16) / 2, rozet, C["uyari_ton"], C["uyari"])
            x += rw
        x += 18
    t.simge("pin", x0 + w - 44, y0 + th / 2, 14, C["simge2"], 1.4)
    t.simge("sevron_asagi", x0 + w - 18, y0 + th / 2, 14, C["simge2"], 1.5)
    cy = y0 + th
    t.dikdortgen(x0, cy, w, dh, dolgu=C["yuzey"])
    satirlar = satirlar or DOCK_SATIRLAR
    rh = 20 if not L.kucuk else 18
    yy = cy + (dh - rh * len(satirlar)) / 2
    for k_, ozet, sonuc, renk in satirlar:
        t.sevron(x0 + 18, yy + rh / 2, "sag", 9, C["metin3"])
        t.yazi(x0 + 30, taban(yy, rh, 11), k_, 11, 600, C["vurgu_metin"])
        t.yazi(x0 + 30 + t.yazi_gen(k_, 11, 600) + 10, taban(yy, rh, 11), ozet, 11, 400, C["metin2"])
        if renk == "ok":
            sw = t.yazi_gen(sonuc, 11, 500)
            t.yazi_sag(x0 + w - 16, taban(yy, rh, 11), sonuc, 11, 500, C["ok"])
            t.simge("onay", x0 + w - 16 - sw - 10, yy + rh / 2, 12, C["ok"], 1.8)
        else:
            t.yazi_sag(x0 + w - 16, taban(yy, rh, 11), sonuc, 11, 400, C["metin3"])
        yy += rh


def komut_satiri(t, L, metin="", son="Son: KİRİŞ — 6 kiriş eklendi (Kat 2)"):
    x0, y0, w, h = L.ray, L.alt + L.rihtim_sekme + L.rihtim, L.W - L.ray, L.komut
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.yatay(x0, x0 + w, y0, C["cizgi"])
    t.dikdortgen(x0 + 8, y0 + 5, 3, h - 10, dolgu=C["vurgu"], r=1.5)
    t.simge("komut", x0 + 26, y0 + h / 2, 15, C["vurgu"], 1.4)
    t.yazi(x0 + 40, taban(y0, h, 12), "Komut", 12, 600, C["vurgu_metin"])
    x = x0 + 40 + t.yazi_gen("Komut", 12, 600) + 12
    if metin:
        t.yazi(x, taban(y0, h, 12), metin, 12, 400, C["metin"])
        x += t.yazi_gen(metin, 12, 400) + 1
    t.dikey(x, y0 + 8, y0 + h - 8, C["metin"], 1)
    x += 12
    t.yazi(x, taban(y0, h, 12), son, 12, 400, C["metin3"])
    ip = [("Ctrl+Q", "odakla / hızlı başlat"), ("Tab", "tamamla"), ("Enter", "yinele"), ("Esc", "iptal")]
    if L.kucuk:
        ip = ip[:2]
    xr = x0 + w - 14
    for k_, et in reversed(ip):
        tw = t.yazi_gen(et, 10, 400)
        xr -= tw
        t.yazi(xr, taban(y0, h, 10), et, 10, 400, C["metin3"])
        xr -= 6
        kw = t.kisayol_dizisi(xr, y0 + (h - 18) / 2, k_, 10, 18, sag=True)
        xr -= kw + 16
    # TR/EN takma ad çipi
    cw_ = t.yazi_gen("TR · EN", 10, 600) + 16
    xr -= cw_ - 4
    t.cip(xr, y0 + (h - 20) / 2, "TR · EN", 20, "notr", 10)


def durum_cubugu(t, L, kapsam="Benzer katlar", yonerge=None, koord=("0,000", "0,000", "6,900"), secili=("6 seçili", "12 tutamaç")):
    W = L.W
    y0, h = L.H - L.durum, L.durum
    t.dikdortgen(0, y0, W, h, dolgu=C["zemin"])
    t.yatay(0, W, y0, C["cizgi"])
    ch = 20
    cy = y0 + (h - ch) / 2
    t.daire(14, y0 + h / 2, 3.5, dolgu=C["vurgu"])
    if yonerge is None:
        yonerge = "Nesne seçin — Shift: ekle · Ctrl: çıkar" if L.kucuk else "Nesne seçin — Shift: ekle · Ctrl: çıkar · Enter: KİRİŞ'i yinele"
    t.yazi(26, taban(y0, h, 11), yonerge, 11, 500, C["metin"])
    # orta: Orto / Yakalama / Sürükle-bırak + X Y Z kilitleri + orta tuş
    x = (W / 2 - 250) if not L.kucuk else 286
    for et, acik in (("ORTO", False), ("YAKALA", True), ("SÜRÜKLE", False)):
        x += t.cip(x, cy, et, ch, "acik" if acik else "kapali", 10, nokta=True) + 4
    x += 6
    for et in "XYZ":
        t.dikdortgen(x, cy, ch, ch, dolgu=None, kenar=C["cizgi"], r=R["orta"])
        t.yazi_orta(x + ch / 2, taban(cy, ch, 10), et, 10, 600, C["metin3"])
        x += ch + 4
    if not L.kucuk:
        x += 8
        t.yazi(x, taban(y0, h, 10), "Orta tuş: kaydır", 10, 400, C["metin3"])
    # sağdan sola: seçili · koordinat · birim · etkin kat · kat kapsamı
    xr = W - 10
    sw = t.yazi_gen(secili[0], 10, 600) + t.yazi_gen(secili[1], 10, 400) + 30
    t.dikdortgen(xr - sw, cy, sw, ch, dolgu=C["secim_ton"], kenar=C["secim_ton2"], r=R["orta"])
    t.daire(xr - sw + 9, cy + ch / 2, 3, dolgu=C["secim"])
    t.yazi(xr - sw + 16, taban(cy, ch, 10), secili[0], 10, 600, C["metin"], tnum=True)
    t.yazi(xr - sw + 20 + t.yazi_gen(secili[0], 10, 600), taban(cy, ch, 10), secili[1], 10, 400, C["metin2"], tnum=True)
    xr -= sw + 12
    ko = f"X {koord[0]}   Y {koord[1]}   Z {koord[2]}"
    tw = t.yazi_gen(ko, 11, 400, True)
    t.yazi(xr - tw, taban(y0, h, 11), ko, 11, 400, C["metin2"], tnum=True)
    xr -= tw + 12
    t.dikey(xr, y0 + 7, y0 + h - 7, C["cizgi"]); xr -= 10
    bw = 68
    t.acilir(xr - bw, cy, bw, ch, "kN · m", 11, salt=False)
    xr -= bw + 8
    if not L.kucuk:
        et = "Etkin kat: Kat 2"
        bw = t.yazi_gen(et, 11, 500) + 38
        t.acilir(xr - bw, cy, bw, ch, et, 11, agirlik=500)
        xr -= bw + 10
    t.dikey(xr, y0 + 7, y0 + h - 7, C["cizgi"]); xr -= 10
    sec = ["Bu kat", "Benzer katlar", "Tüm katlar"]
    sgw = sum(t.yazi_gen(s, 11, 600) + 20 for s in sec) + 4
    sx = xr - sgw
    t.segmentli(sx, cy - 1, sec, sec.index(kapsam), h=ch + 2, boyut=11, stil="vurgu", ic=10)
    if not L.kucuk:
        t.yazi_sag(sx - 8, taban(y0, h, 10), "Kat kapsamı", 10, 500, C["metin3"])
        t.simge("katman", sx - 8 - t.yazi_gen("Kat kapsamı", 10, 500) - 12, y0 + h / 2, 13, C["simge2"], 1.3)
    else:
        t.simge("katman", sx - 12, y0 + h / 2, 13, C["simge2"], 1.3)
    return sx, sgw


# ============================================================================
# EKRAN KOMPOZİSYONU
# ============================================================================
def ekran(W, H, s=1, yogunluk="rahat", onbellek=None):
    L = Yerlesim(W, H, yogunluk)
    t = Tuval(W, H, s)
    baslik_cubugu(t, L)
    serit(t, L, etkin="Model")
    ray(t, L)
    gorunum_sekmeleri(t, L)
    viewport(t, L, mod="secim", sahne_onbellek=onbellek)
    model_agaci(t, L)
    ozellikler(t, L)
    panel_golgesi(t, L.vp_x0, L.vp_y0, L.vp_y1, +1)
    panel_golgesi(t, L.vp_x1, L.vp_y0, L.vp_y1, -1)
    pencere_seridi(t, L)
    dock(t, L)
    komut_satiri(t, L)
    durum_cubugu(t, L)
    t.cerceve(0, 0, W, H, "#C5CAD1", 1)
    return t, L


def kaydet(img, ad):
    yol = os.path.join(BURASI, ad)
    img.save(yol, optimize=True)
    print(f"  yazıldı: {yol}  ({img.width}×{img.height})")
    return yol


def ana():
    hizli = "--hizli" in sys.argv
    t0 = time.time()
    print("Atölye · Modern — üretim başlıyor")
    onb = {}
    ekranlar = {}
    for palet in (["kobalt"] if hizli else ["kobalt", "petrol", "grafit"]):
        palet_uygula(palet)
        t1, L1 = ekran(1920, 1080, 1, onbellek=onb)
        ekranlar[palet] = t1.img
        kaydet(t1.img, f"ana-{palet}.png")
    if hizli:
        return
    palet_uygula("kobalt")
    t3, _ = ekran(1366, 768, 1, yogunluk="siki", onbellek=onb)
    kaydet(t3.img, "kucuk.png")
    # 2× kırpımlar
    t2, L2 = ekran(1920, 1080, 2, onbellek=onb)
    serit_k = t2.img.crop((0, 0, t2.p(1720), t2.p(L2.ust + 1)))
    kaydet(serit_k, "detay-serit.png")
    yh = 640
    ag = t2.img.crop((0, t2.p(L2.ust), t2.p(L2.ray + L2.agac), t2.p(L2.ust + yh)))
    oz = t2.img.crop((t2.p(L2.vp_x1), t2.p(L2.ust), t2.p(L2.W), t2.p(L2.ust + yh)))
    bos = t2.p(24)
    pan = Image.new("RGB", (ag.width + bos + oz.width, ag.height), hex2rgb(C["sayfa"]))
    pan.paste(ag, (0, 0)); pan.paste(oz, (ag.width + bos, 0))
    kaydet(pan, "detay-panel.png")
    import ayarlar
    sayfalar = {}
    for sayfa in ("program", "goruntu", "dil"):
        palet_uygula("kobalt")
        im = ayarlar.ayarlar_ekrani(sayfa, ekranlar["kobalt"])
        sayfalar[sayfa] = im
        kaydet(im, f"ayarlar-{sayfa}.png")
    import karsilastir
    kaydet(karsilastir.karsilastirma(ekranlar, sayfalar), "karsilastirma.png")
    print(f"bitti ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    ana()
