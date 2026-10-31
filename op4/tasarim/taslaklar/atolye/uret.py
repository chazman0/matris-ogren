#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
op4 arayüz yönü B — "Atölye" (yoğun profesyonel) — yüksek doğruluklu taslak görselleri.

Üretilenler (bu klasöre):
  ana.png 1920×1080 · ana-2x.png 3840×2160 · kucuk.png 1366×768
  detay-serit.png (şerit kırpımı 2×) · detay-panel.png (model ağacı + Özellikler kırpımı 2×)
  secsuz.png (Seç ve Süz iletişim kutusu) · sonuc.png (Tasarım sekmesi, D/C haritası, tablolar)
  kat-kapsami.png (durum çubuğu kat kapsamı anahtarı + "3 katta uygulanacak" kırpımı 2×)

Her şey Pillow ile çizilir: arayüz kromu (dikdörtgen/çizgi/Inter yazı), elle çizilmiş tek renkli çizgi
simgeler (tuval.py) ve numpy z-tamponlu yazılımsal 3B görünüm (sahne.py).

Çalıştırma:  python3 uret.py            (tüm çıktılar)
             python3 uret.py --hizli    (yalnız 1× ana.png)
"""
import os
import sys
import time
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tuval import (C, KAHVE, KREM, ALTIN, ANTRASIT, GRI, DC_RENK, DC_ESIK, Tuval, taban, hex2rgb, karisim,
                   logo_simge)
from sahne import sahne_ciz, X_AKS, Y_AKS, Z_KAT, PROFILLER

BURASI = os.path.dirname(os.path.abspath(__file__))
PROJE = "Depo Binası – Tokat OSB"


# ============================================================================
# YERLEŞİM
# ============================================================================
class Yerlesim:
    def __init__(self, W, H, kucuk=False, dock_h=None):
        self.W, self.H, self.kucuk = W, H, kucuk
        self.baslik_h = 30
        self.sekme_h = 26
        self.serit_h = 78            # 26 + 78 = 104 px şerit
        self.ray_w = 36
        self.agac_w = 232 if kucuk else 268
        self.ozel_w = 288 if kucuk else 320
        self.strip_w = 28
        self.gtab_h = 22             # görünüm sekmeleri
        self.dock_tab_h = 22
        self.dock_h = dock_h if dock_h is not None else (36 if kucuk else 40)
        self.komut_h = 30
        self.durum_h = 26
        self.ust = self.baslik_h + self.sekme_h + self.serit_h                      # 134
        self.alt = H - self.durum_h - self.komut_h - self.dock_h - self.dock_tab_h  # 962 @1080
        self.vp_x0 = self.ray_w + self.agac_w
        self.vp_x1 = W - self.strip_w - self.ozel_w
        self.vp_y0 = self.ust + self.gtab_h
        self.vp_y1 = self.alt
        self.vp_w, self.vp_h = self.vp_x1 - self.vp_x0, self.vp_y1 - self.vp_y0


# ============================================================================
# BAŞLIK ÇUBUĞU
# ============================================================================
def baslik_cubugu(t, L):
    W = L.W
    t.dikdortgen(0, 0, W, L.baslik_h, dolgu=C["zemin"])
    simge = logo_simge()
    h = 16
    w = h * simge.width / simge.height
    t.resim(simge, 12, (L.baslik_h - h) / 2, w=w, h=h)
    x = 12 + w + 7
    t.yazi(x, taban(0, L.baslik_h, 13), "op4", 13, 600, C["metin"])
    x += t.yazi_gen("op4", 13, 600) + 12
    t.dikey(x, 8, L.baslik_h - 8, C["cizgi"])
    x += 10
    for ad in ("yeni", "ac", "kaydet", "yazdir", None, "geri_al", "yinele"):
        if ad is None:
            t.dikey(x + 4, 8, L.baslik_h - 8, C["cizgi"]); x += 14; continue
        t.simge(ad, x + 11, L.baslik_h / 2, 15, "#3C4148", 1.4); x += 26
    ad = f"{PROJE}.op4"
    tw = t.yazi_gen(ad, 12, 500)
    cx = W / 2
    t.yazi(cx - tw / 2, taban(0, L.baslik_h, 12), ad, 12, 500, C["metin"])
    t.daire(cx + tw / 2 + 10, L.baslik_h / 2, 3, dolgu=C["vurgu"])
    t.yazi(cx + tw / 2 + 18, taban(0, L.baslik_h, 11), "kaydedilmedi", 11, 400, C["metin3"])
    # sağ: kullanıcı + pencere düğmeleri
    kul = "Opus Fortis · Proje Mühendisi"
    t.yazi_sag(W - 46 * 3 - 18, taban(0, L.baslik_h, 11), kul, 11, 400, C["metin3"])
    for i, ad in enumerate(("kucult", "buyut", "kapat")):
        t.simge(ad, W - 46 * (3 - i) + 23, L.baslik_h / 2, 13, "#3C4148", 1.2)


# ============================================================================
# ŞERİT
# ============================================================================
SEKMELER = ["Model", "Düzenle", "Yükler", "Analiz", "Tasarım", "Görünüm", "Raporlar"]

# (grup adı, büyük düğmeler [(simge, etiket, durum)], küçük düğmeler [(simge, etiket, açılır)], başlatıcı)
GRUPLAR_MODEL = [
    ("Aks & Kat", [("aks", "Aks", ""), ("kat", "Kat", "")],
     [("izgara", "Aks sistemi…", False), ("kat_verisi", "Kat verisi…", False), ("duzlem", "Çalışma düzlemi", True)], True),
    ("Kolon", [("kolon", "Kolon", "")], [("kolon", "Çelik", False), ("kolon", "Betonarme", False), ("kolon", "Kompozit", False)], False),
    ("Kiriş", [("kiris", "Kiriş", "basili")], [("kiris_ana", "Ana kiriş", False), ("kiris_tali", "Tali kiriş", False), ("asik", "Aşık", False)], False),
    ("Çapraz", [("capraz", "Çapraz", "")], [("capraz", "X çapraz", False), ("capraz_v", "V / Λ çapraz", False), ("capraz_tek", "Tek diyagonal", False)], False),
    ("Döşeme", [("doseme", "Döşeme", "")], [("doseme", "Betonarme", False), ("doseme", "Kompozit", False), ("doseme_bosluk", "Boşluk", False)], False),
    ("Duvar", [("duvar", "Duvar", "")], [("duvar", "Perde", False), ("duvar", "Dolgu", False), ("doseme_bosluk", "Açıklık", False)], False),
    ("Temel", [("temel", "Temel", "")], [("temel", "Tekil", False), ("temel_surekli", "Sürekli", False), ("temel_radye", "Radye", False)], False),
    ("Hızlı kolon / kiriş", [("hizli_kolon", "Hızlı kolon", ""), ("hizli_kiris", "Hızlı kiriş", "")],
     [("hizli_capraz", "Hızlı çapraz", False), ("kiris_tali", "Tali kirişler…", False), ("kopyala_kat", "Kat kopyala…", False)], False),
    ("Seç", [("sec", "Seç", ""), ("sec_suz", "Seç & Süz", "")],
     [("benzer", "Benzerini seç", False), ("katman", "Kata göre", True), ("ters", "Tersine çevir", False)], True),
]
GRUPLAR_TASARIM = [
    ("Yönetmelik", [("yonetmelik", "ÇYTHYE 2018", "acilir")],
     [("ayar", "Tercihler…", False), ("tablo", "Kombinasyonlar", False), ("malzeme", "Malzeme katsayıları", False)], True),
    ("Çelik", [("tasarim", "Tasarla", ""), ("kontrol", "Kontrol et", "")],
     [("kesit", "Otomatik kesit", True), ("asik", "Yanal tutma", False), ("birlestir", "Birleşimler", False)], False),
    ("Betonarme", [("tasarim", "Tasarla", "")], [("kesit", "Donatı", False), ("capraz_tek", "Kesme", False), ("rapor", "Detay", False)], False),
    ("Göster", [("dc", "D/C haritası", "basili"), ("deform", "Deformasyon", ""), ("diyagram", "Diyagram", "")],
     [("etiket", "Değerler", False), ("analiz", "N · V · M", True), ("katman", "1,2G + 1,6Q", True)], True),
    ("Sonuç", [("tablo", "Tablolar", ""), ("rapor", "Rapor", "")],
     [("sec", "Etkileşimli tasarım", False), ("tablo_disa", "Tabloya aktar", False), ("kutuphane", "Tablo kümeleri", False)], False),
]


def serit(t, L, etkin="Model", gruplar=None):
    W = L.W
    gruplar = gruplar or GRUPLAR_MODEL
    y0 = L.baslik_h
    t.dikdortgen(0, y0, W, L.sekme_h, dolgu=C["zemin"])
    x = 8
    dw = 58
    t.dikdortgen(x, y0 + 4, dw, L.sekme_h - 4, dolgu=C["vurgu"], r=0)
    t.yazi_orta(x + dw / 2, taban(y0 + 4, L.sekme_h - 4, 12), "Dosya", 12, 600, "#FFFFFF")
    x += dw + 6
    govde_y = y0 + L.sekme_h
    for ad in SEKMELER:
        tw = t.yazi_gen(ad, 12, 500)
        w = tw + 24
        if ad == etkin:
            t.dikdortgen(x, y0 + 4, w, L.sekme_h - 4 + 1, dolgu=C["yuzey"])
            t.dikey(x, y0 + 4, govde_y + 1, C["cizgi"]); t.dikey(x + w - 1, y0 + 4, govde_y + 1, C["cizgi"])
            t.yatay(x, x + w, y0 + 4, C["vurgu"], 2)
            t.yazi(x + 12, taban(y0 + 4, L.sekme_h - 4, 12), ad, 12, 600, C["metin"])
        else:
            t.yazi(x + 12, taban(y0 + 4, L.sekme_h - 4, 12), ad, 12, 500, C["metin2"])
        x += w
    # sağ: özelleştir, daralt, yardım
    t.simge("yardim", W - 18, y0 + L.sekme_h / 2 + 1, 14, C["metin3"], 1.3)
    t.simge("sevron_ust", W - 40, y0 + L.sekme_h / 2 + 1, 13, C["metin3"], 1.3)
    t.yazi_sag(W - 56, taban(y0, L.sekme_h, 11), "Şeridi özelleştir", 11, 400, C["metin3"])
    # gövde
    t.dikdortgen(0, govde_y, W, L.serit_h, dolgu=C["yuzey"])
    t.yatay(0, W, govde_y, C["cizgi"])
    t.yatay(0, W, govde_y + L.serit_h - 1, C["cizgi"])
    gy = govde_y
    x = 8
    kucuk = L.kucuk
    for gi, (gad, buyuk, kucukler, baslatici) in enumerate(gruplar):
        gx0 = x
        x += 6
        for ik, et, durum in buyuk:
            bw = max(48, t.yazi_gen(et, 11, 500) + 16 + (10 if durum == "acilir" else 0))
            if durum == "basili":
                t.dikdortgen(x, gy + 5, bw, 54, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=3)
            t.simge(ik, x + bw / 2 - (5 if durum == "acilir" else 0), gy + 22, 24, C["vurgu"] if durum == "basili" else "#2F343B", 1.5)
            t.yazi_orta(x + bw / 2 - (5 if durum == "acilir" else 0), gy + 50, et, 11, 500 if durum != "basili" else 600, C["metin"])
            if durum == "acilir":
                t.sevron(x + bw - 9, gy + 47, "asagi", 9, C["metin2"])
            x += bw + 2
        if kucukler and not (kucuk and gad in ("Kolon", "Çapraz", "Döşeme", "Duvar", "Temel", "Betonarme")):
            x += 2
            kw = max(t.yazi_gen(et, 11, 400) for _, et, _ in kucukler) + 24 + (12 if any(a for _, _, a in kucukler) else 0)
            for j, (ik, et, acilir) in enumerate(kucukler):
                yy = gy + 6 + j * 18
                t.simge(ik, x + 10, yy + 8, 14, "#3C4148", 1.4)
                t.yazi(x + 22, taban(yy, 16, 11), et, 11, 400, C["metin"])
                if acilir:
                    t.sevron(x + 22 + t.yazi_gen(et, 11, 400) + 8, yy + 9, "asagi", 9, C["metin3"])
            x += kw
        x += 6
        gw = x - gx0
        # grup etiketi + başlatıcı + ayraç
        t.yazi_orta(gx0 + gw / 2, gy + 71, gad, 10, 400, C["metin3"])
        if baslatici:
            t.simge("sevron_sag", x - 8, gy + 68, 8, C["metin3"], 1.6)
        t.dikey(x, gy + 8, gy + L.serit_h - 8, C["cizgi2"])
        x += 1


# ============================================================================
# SOL RAY: hızlı çizim paleti + seçim anahtarları
# ============================================================================
PALET = [("sec", "Seç"), ("kolon", "Kolon"), ("kiris", "Kiriş"), ("capraz", "Çapraz"), ("doseme", "Döşeme"),
         ("duvar", "Duvar"), ("temel", "Temel"), ("aks", "Aks"), ("yuk", "Yük"), ("mesnet", "Mesnet"), ("olcu", "Ölçü")]
ANAHTARLAR = [("sec_pencere", True), ("dugum", True), ("kolon", True), ("kiris", True), ("doseme", False), ("duvar", False),
              ("aks", False), ("yuk", False), ("mesnet", True), ("temel", False)]


def ray(t, L):
    x0, y0, y1 = 0, L.ust, L.H - L.durum_h
    t.dikdortgen(x0, y0, L.ray_w, y1 - y0, dolgu=C["zemin"])
    t.dikey(L.ray_w - 1, y0, y1, C["cizgi"])
    y = y0 + 6
    t.yazi_orta(L.ray_w / 2, y + 8, "ÇİZ", 8, 600, C["metin3"])
    y += 12
    for ik, et in PALET:
        secili = ik == "kiris"
        if secili:
            t.dikdortgen(5, y, 26, 26, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=3)
            t.dikey(0, y + 4, y + 22, C["vurgu"], 2)
        t.simge(ik, 18, y + 13, 16, C["vurgu"] if secili else "#3C4148", 1.5)
        y += 28
    y += 4
    t.yatay(8, L.ray_w - 8, y, C["cizgi"])
    y += 8
    t.yazi_orta(L.ray_w / 2, y + 8, "SEÇ", 8, 600, C["metin3"])
    y += 12
    for ik, acik in ANAHTARLAR:
        if acik:
            t.dikdortgen(5, y, 26, 24, dolgu=C["yuzey"], kenar=C["cizgi"], r=3)
            t.simge(ik, 18, y + 12, 15, "#2F343B", 1.5)
            t.daire(27, y + 5, 2, dolgu=C["vurgu"])
        else:
            t.simge(ik, 18, y + 12, 15, "#B3B7BE", 1.5)
        y += 26
    y += 4
    t.yatay(8, L.ray_w - 8, y, C["cizgi"])
    y += 8
    # doğrudan değiştirme (D) açık, anahtarları gizle
    t.dikdortgen(5, y, 26, 24, dolgu=C["secim_ton"], kenar=C["secim_ton2"], r=3)
    t.simge("dm", 18, y + 12, 16, C["secim"], 1.6)
    y += 28
    t.simge("goz", 18, y + 12, 15, "#8C8C8C", 1.4)
    # altta: şerit sekmesi kısayolu yok; ray sonu


# ============================================================================
# MODEL AĞACI (sol panel)
# ============================================================================
AGAC = [
    # (derinlik, simge, metin, sağ metin, durum, açık?)
    (0, "proje", PROJE, "", "", True),
    (1, "aks", "Aks sistemi", "A–D × 1–5", "", False),
    (1, "kat", "Katlar", "3", "", True),
    (2, "kat", "Kat 3 (Çatı)", "+13,50", "", False),
    (2, "kat", "Kat 2", "+9,00", "etkin", True),
    (3, "kolon", "Kolonlar", "20", "", False),
    (3, "kiris", "Kirişler · IPE400", "31", "", True),
    (4, "kiris_ana", "Ana çerçeve", "15", "secili", False),
    (4, "kiris_ana", "Bağ kirişleri", "16", "", False),
    (3, "kiris_tali", "Tali kirişler", "12", "", False),
    (3, "capraz", "Çaprazlar", "8", "", False),
    (3, "doseme", "Döşemeler", "1", "", False),
    (2, "kat", "Kat 1", "+4,50", "", False),
    (2, "kat", "Zemin", "±0,00", "", False),
    (1, "kesit", "Kesitler", "4", "", False),
    (1, "malzeme", "Malzemeler", "2", "", False),
    (1, "yuk", "Yük desenleri", "5", "", False),
    (1, "tablo", "Yük durumları", "5", "", False),
    (1, "tablo", "Kombinasyonlar", "14", "", False),
    (1, "katman", "Gruplar", "3", "", False),
    (1, "analiz", "Analiz modeli", "", "", False),
]


def model_agaci(t, L):
    x0, y0, w, h = L.ray_w, L.ust, L.agac_w, L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.dikey(x0 + w - 1, y0, y0 + h, C["cizgi"])
    # başlık
    t.dikdortgen(x0, y0, w, 28, dolgu=C["yuzey2"])
    t.yatay(x0, x0 + w, y0 + 27, C["cizgi2"])
    t.yazi(x0 + 10, taban(y0, 28, 12), "Model ağacı", 12, 600, C["metin"])
    t.simge("pin", x0 + w - 36, y0 + 14, 13, C["metin3"], 1.3)
    t.simge("kapat", x0 + w - 16, y0 + 14, 12, C["metin3"], 1.3)
    # sekmeler
    ty = y0 + 28
    t.dikdortgen(x0, ty, w, 24, dolgu=C["yuzey"])
    t.yatay(x0, x0 + w, ty + 23, C["cizgi2"])
    x = x0 + 8
    for ad in ("Model", "Göster", "Tablolar", "Raporlar"):
        tw = t.yazi_gen(ad, 11, 500)
        if ad == "Model":
            t.yazi(x, taban(ty, 24, 11), ad, 11, 600, C["metin"])
            t.yatay(x - 2, x + tw + 2, ty + 21, C["vurgu"], 2)
        else:
            t.yazi(x, taban(ty, 24, 11), ad, 11, 500, C["metin2"])
        x += tw + 18
    # arama
    sy = ty + 24 + 6
    t.dikdortgen(x0 + 8, sy, w - 16, 22, dolgu=C["yuzey"], kenar=C["cizgi"], r=3)
    t.simge("ara", x0 + 20, sy + 11, 12, C["metin3"], 1.3)
    t.yazi(x0 + 30, taban(sy, 22, 11), "Ağaçta ara (ad, kesit, etiket)", 11, 400, C["metin3"])
    # satırlar
    y = sy + 22 + 6
    rh = 20
    for derin, ik, metin, sag, durum, acik in AGAC:
        if y + rh > L.alt - 28:
            break
        if durum == "secili":
            t.dikdortgen(x0, y, w - 1, rh, dolgu=C["secim_ton"])
            t.dikey(x0, y, y + rh, C["secim"], 2)
        elif durum == "etkin":
            t.dikdortgen(x0, y, w - 1, rh, dolgu=C["yuzey2"])
        ix = x0 + 10 + derin * 14
        cocuk = derin < 4 and metin not in ("Aks sistemi", "Analiz modeli")
        if cocuk:
            t.sevron(ix + 4, y + rh / 2, "asagi" if acik else "sag", 9, C["metin3"])
        t.simge(ik, ix + 20, y + rh / 2, 13, "#4E545C" if durum != "secili" else C["vurgu"], 1.3)
        agir = 600 if derin == 0 or durum == "etkin" else 400
        renk = C["metin"]
        maxw = w - (ix + 30 - x0) - 12 - (t.yazi_gen(sag, 11, 400, True) + 10 if sag else 0) - ((22 if L.kucuk else 52) if durum == "secili" else 0)
        t.yazi(ix + 30, taban(y, rh, 12), t.yazi_kes(metin, maxw, 12, agir), 12, agir, renk)
        if durum == "secili":
            rz = "6" if L.kucuk else "6 seçili"
            bw = t.yazi_gen(rz, 9, 600) + 12
            t.dikdortgen(x0 + w - 12 - t.yazi_gen(sag, 11, 400, True) - 8 - bw, y + 3, bw, rh - 6, dolgu=C["secim"], r=7)
            t.yazi_orta(x0 + w - 12 - t.yazi_gen(sag, 11, 400, True) - 8 - bw / 2, taban(y, rh, 9), rz, 9, 600, "#FFFFFF")
        if sag:
            t.yazi_sag(x0 + w - 12, taban(y, rh, 11), sag, 11, 400, C["metin3"] if durum != "etkin" else C["metin2"], tnum=True)
        if durum == "etkin":
            t.simge("goz", x0 + w - 12 - t.yazi_gen(sag, 11, 400, True) - 16, y + rh / 2, 12, C["metin3"], 1.3)
        y += rh
    # alt özet
    oy = L.alt - 24
    t.yatay(x0, x0 + w - 1, oy, C["cizgi2"])
    t.yazi(x0 + 10, taban(oy, 24, 11), "263 eleman · 80 düğüm · 3 kat", 11, 400, C["metin3"], tnum=True)


# ============================================================================
# GÖRÜNÜM SEKMELERİ + 3B GÖRÜNÜM
# ============================================================================
def gorunum_sekmeleri(t, L, etkin="3B görünüm"):
    x0, y0, w, h = L.vp_x0, L.ust, L.vp_w, L.gtab_h
    t.dikdortgen(x0, y0, w, h, dolgu=C["zemin"])
    t.yatay(x0, x0 + w, y0 + h - 1, C["cizgi"])
    x = x0 + 6
    for ad in ("3B görünüm", "Plan – Kat 2 (+9,00)", "Yükselti – Aks 1"):
        tw = t.yazi_gen(ad, 11, 500) + 22
        if ad == etkin:
            t.dikdortgen(x, y0 + 3, tw, h - 3, dolgu=C["yuzey"])
            t.dikey(x, y0 + 3, y0 + h, C["cizgi"]); t.dikey(x + tw - 1, y0 + 3, y0 + h, C["cizgi"])
            t.yatay(x, x + tw, y0 + 3, C["cizgi"])
            t.yazi(x + 11, taban(y0 + 3, h - 3, 11), ad, 11, 600, C["metin"])
        else:
            t.yazi(x + 11, taban(y0 + 3, h - 3, 11), ad, 11, 500, C["metin2"])
        x += tw + 2
    t.simge("artı", x + 10, y0 + h / 2 + 1, 12, C["metin3"], 1.4)
    t.yazi_sag(x0 + w - 10, taban(y0, h, 10), "Görünüm özellikleri: arka plana çift tık", 10, 400, C["metin3"])


def viewport(t, L, mod="secim", sahne_onbellek=None):
    x0, y0, w, h = L.vp_x0, L.vp_y0, L.vp_w, L.vp_h
    key = (w, h, t.s, mod)
    sc = sahne_onbellek.get(key) if sahne_onbellek is not None else None
    if sc is None:
        sc = sahne_ciz(w, h, t.s, ss=2, mod=mod)
        if sahne_onbellek is not None:
            sahne_onbellek[key] = sc
    t.yapistir(sc.im, x0, y0)

    def iz(p):
        q = sc.iz(p)
        return (x0 + q[0], y0 + q[1])

    # --- üst sol: görünüm araç pili ---
    px, py = x0 + 10, y0 + 10
    parcalar = [("bina3", "3B", True), ("perspektif", "Perspektif", True), ("katman", "Tüm katlar", True), ("etiket", "Renk: türe göre", True)]
    pw = 10
    for ik, et, ac in parcalar:
        pw += 18 + t.yazi_gen(et, 11, 500) + (12 if ac else 0) + 16
    pw += 62  # render anahtarı
    t.golge(px, py, pw, 26, r=13, yaricap=4, alfa=0.10)
    t.dikdortgen(px, py, pw, 26, dolgu=(255, 255, 255, 238), kenar=C["cizgi"], r=13)
    cx = px + 10
    for ik, et, ac in parcalar:
        t.simge(ik, cx + 7, py + 13, 14, C["metin2"], 1.3)
        t.yazi(cx + 18, taban(py, 26, 11), et, 11, 500, C["metin"])
        cx += 18 + t.yazi_gen(et, 11, 500)
        if ac:
            t.sevron(cx + 6, py + 13.5, "asagi", 9, C["metin3"]); cx += 12
        cx += 8
        t.dikey(cx, py + 6, py + 20, C["cizgi2"]); cx += 8
    # render modu anahtarı: çubuk ↔ ekstrüde
    t.dikdortgen(cx, py + 4, 52, 18, dolgu=C["zemin"], kenar=C["cizgi"], r=9)
    t.dikdortgen(cx + 26, py + 5, 25, 16, dolgu=C["vurgu"], r=8)
    t.simge("cubuk", cx + 13, py + 13, 12, C["metin2"], 1.4)
    t.simge("kati", cx + 38, py + 13, 12, "#FFFFFF", 1.4)
    # --- üst sağ: görünüm düğmeleri (küp yok) ---
    for i, (ad, _ip) in enumerate((("ev", "Tam görünüm"), ("sigdir", "Seçiliye yakınlaş"), ("kesit_duzlemi", "Kesit düzlemi"), ("goz", "Gösterim seçenekleri"))):
        bx = x0 + w - 10 - (4 - i) * 26
        t.dikdortgen(bx, py, 24, 24, dolgu=(255, 255, 255, 236), kenar=C["cizgi"], r=3)
        t.simge(ad, bx + 12, py + 12, 14, C["metin2"], 1.3)
    # --- alt sol: eksen üçlüsü ---
    ox, oy = x0 + 36, y0 + h - 36
    for ad, v, renk in (("X", (1, 0, 0), "#B4443A"), ("Y", (0, 1, 0), "#2E7D4F"), ("Z", (0, 0, 1), "#2F5FA8")):
        dx, dy = sc.eksen_vektor(v)
        Ln = (dx * dx + dy * dy) ** 0.5 or 1
        ex, ey = ox + dx / Ln * 24, oy - dy / Ln * 24
        t.cizgi(ox, oy, ex, ey, renk, 1.5)
        t.yazi(ex + dx / Ln * 9 - 3.5, ey - dy / Ln * 9 + 4, ad, 10, 600, renk)
    t.daire(ox, oy, 2.2, dolgu=C["metin2"])
    # --- alt sağ: görünüm bilgisi ---
    if mod != "dc":
        bilgi = "Perspektif 30° · Bakış: güney-batı · Orta tuş: kaydır · Ctrl+orta: döndür"
        t.yazi_sag(x0 + w - 12, y0 + h - 12, bilgi, 10, 400, C["metin3"])

    if mod == "secim":
        secim_notlari(t, L, sc, iz)
    return sc


def secim_notlari(t, L, sc, iz):
    """Doğrudan değiştirme tutamaçları, ölçü etiketi, bağlamsal mini araç çubuğu, imleç + hover ipucu."""
    kir = PROFILLER["IPE400"]; kol = PROFILLER["HE340A"]
    zc = Z_KAT[2] - kir[0] / 2
    # tutamaçlı kiriş: Aks 1, B–C açıklığı
    p0 = (X_AKS[1] + kol[0] / 2, 0.0, zc); p1 = (X_AKS[2] - kol[0] / 2, 0.0, zc)
    a, b = iz(p0), iz(p1)
    m = iz(((p0[0] + p1[0]) / 2, 0.0, zc))
    # başlangıç (altın) / bitiş (kahve) tutamaçları, orta nokta tutamacı
    for (cx_, cy_, renk) in ((a[0], a[1], ALTIN), (b[0], b[1], KAHVE)):
        t.dikdortgen(cx_ - 6, cy_ - 6, 12, 12, dolgu="#FFFFFF", kenar="#3C3326", kalinlik=1, r=1)
        t.dikdortgen(cx_ - 4, cy_ - 4, 8, 8, dolgu=renk)
    t.daire(m[0], m[1], 4, dolgu="#FFFFFF", kenar="#3C3326", kalinlik=1)
    t.daire(m[0], m[1], 2, dolgu=ALTIN)
    # ölçü etiketi (değer yazılabilir): kirişin altında
    u = iz(((p0[0] + p1[0]) / 2, 0.0, zc - 0.75))
    et = "5 670"
    ew = t.yazi_gen(et, 11, 500, True) + 14
    t.dikdortgen(u[0] - ew / 2, u[1] - 9, ew, 18, dolgu=(255, 255, 255, 240), kenar=ALTIN, r=2)
    t.yazi_orta(u[0], taban(u[1] - 9, 18, 11), et, 11, 500, C["metin"], tnum=True)
    a2 = iz((p0[0], 0.0, zc - 0.75)); b2 = iz((p1[0], 0.0, zc - 0.75))
    t.cizgi(a2[0], a2[1], u[0] - ew / 2 - 2, u[1], ALTIN, 1)
    t.cizgi(u[0] + ew / 2 + 2, u[1], b2[0], b2[1], ALTIN, 1)
    # bağlamsal mini araç çubuğu: seçimin üstünde
    alanlar = [("kiris", "IPE400"), ("malzeme", "S355"), ("kat", "Kat 2"), ("mafsal", "Mafsal")]
    cw = 10
    for ik, et in alanlar:
        cw += 18 + t.yazi_gen(et, 11, 500) + 12 + 14
    cw += 3 * 24 + 10
    merkez = iz((5.5, 2.5, Z_KAT[2]))
    cx, cy = merkez[0] - cw / 2, merkez[1] - 74
    t.golge(cx, cy, cw, 28, r=4, yaricap=5, alfa=0.16)
    t.dikdortgen(cx, cy, cw, 28, dolgu=(255, 255, 255, 246), kenar=C["cizgi"], r=4)
    x = cx + 10
    for ik, et in alanlar:
        t.simge(ik, x + 7, cy + 14, 14, C["metin2"], 1.3)
        t.yazi(x + 18, taban(cy, 28, 11), et, 11, 500, C["metin"])
        x += 18 + t.yazi_gen(et, 11, 500)
        t.sevron(x + 6, cy + 14.5, "asagi", 9, C["metin3"])
        x += 12 + 7
        t.dikey(x, cy + 7, cy + 21, C["cizgi2"]); x += 7
    for ik in ("kopyala", "tasi", "sil"):
        t.simge(ik, x + 10, cy + 14, 14, C["metin2"], 1.3); x += 24
    # ok: araç çubuğu → seçim
    t.cokgen([(cx + cw / 2 - 5, cy + 28), (cx + cw / 2 + 5, cy + 28), (cx + cw / 2, cy + 33)], dolgu="#FFFFFF", kenar=C["cizgi"], kalinlik=1)
    # imleç: A/1 kolonu (hover, kahve ince kontur sahnede) + ipucu
    hp = iz((X_AKS[0] + kol[0] / 2 + 0.05, -0.2, Z_KAT[1] + 2.4))
    t.simge("imlec", hp[0] + 6, hp[1] + 8, 18, "#14181B", 1.2)
    ip = "Kolon K2-A1 · HE340A · S355"
    iw = t.yazi_gen(ip, 10, 500) + 12
    t.dikdortgen(hp[0] + 18, hp[1] + 16, iw, 18, dolgu=(255, 255, 255, 240), kenar=KAHVE, r=2)
    t.yazi(hp[0] + 24, taban(hp[1] + 16, 18, 10), ip, 10, 500, C["metin"])


# ============================================================================
# ÖZELLİKLER PANELİ (sağ) + PENCERE ŞERİDİ
# ============================================================================
OZELLIKLER_KIRIS = [
    ("Genel", True, [("Ad", "K2-1AB … K2-2CD", "coklu"), ("Tür", "Kiriş", "salt"), ("Kat", "Kat 2  (+9,00)", "acilir"),
                     ("Grup", "Ana çerçeve", "acilir"), ("Sınıf / renk", "3 · Çelik kiriş", "renk")]),
    ("Kesit", True, [("Kesit", "IPE400", "katalog"), ("Malzeme", "S355", "katalog"), ("Dönme", "0°", ""),
                     ("h / b", "400 / 180 mm", "salt"), ("tw / tf", "8,6 / 13,5 mm", "salt")]),
    ("Konum", True, [("Başlangıç", "(farklı)", "coklu"), ("Bitiş", "(farklı)", "coklu"), ("Uzunluk", "5,670 m", "salt"),
                     ("Düzlemde", "Orta", "acilir"), ("Derinlik", "Üst", "acilir")]),
    ("Serbestlikler", True, [("Başlangıç ucu", "Mafsal", "acilir_altin"), ("Bitiş ucu", "Mafsal", "acilir_kahve"), ("Mesnet", "Bağlı", "acilir")]),
    ("Yükler", True, [("Geçerli desen", "G · Sabit", "acilir"), ("Çizgisel yük", "G 4,20 · Q 7,50 kN/m", ""), ("Öz ağırlık", "Evet", "onay")]),
    ("Analiz", False, []),
    ("Tasarım", True, [("Yönetmelik", "ÇYTHYE 2018", "acilir"), ("Lcr,y / Lcr,z", "5,67 / 2,00 m", ""),
                       ("Yanal tutma", "Aşık noktaları", "acilir"), ("Son D/C", "0,62", "dc")]),
]
OZELLIKLER_KOLON = [
    ("Genel", True, [("Ad", "K1-C2", ""), ("Tür", "Kolon", "salt"), ("Kat", "Kat 1  (+4,50)", "acilir"), ("Grup", "Orta kolonlar", "acilir")]),
    ("Kesit", True, [("Kesit", "HE340A", "katalog"), ("Malzeme", "S355", "katalog"), ("Dönme", "90°", "")]),
    ("Serbestlikler", False, []),
    ("Analiz", False, []),
    ("Tasarım", True, [("Yönetmelik", "ÇYTHYE 2018", "acilir"), ("Kritik komb.", "1,2G + 1,6Q", "acilir"),
                       ("N_Ed / N_b,Rd", "1 842 / 2 310 kN", "salt"), ("M_y,Ed / M_y,Rd", "212 / 308 kNm", "salt"),
                       ("Lcr,y / Lcr,z", "4,50 / 4,50 m", ""), ("Son D/C", "1,04", "dc_kirmizi"), ("Durum", "Yetersiz — kesit büyüt", "hata")]),
    ("Sonuç", True, [("Tepki Rz (G+Q)", "1 236 kN", "salt"), ("Düğüm uz / Δ", "2,8 mm · 1/1607", "salt")]),
]


def ozellikler(t, L, nesne="kiris"):
    x0, y0, w, h = L.vp_x1, L.ust, L.ozel_w, L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.dikey(x0, y0, y0 + h, C["cizgi"])
    # başlık
    t.dikdortgen(x0 + 1, y0, w - 1, 28, dolgu=C["yuzey2"])
    t.yatay(x0, x0 + w, y0 + 27, C["cizgi2"])
    t.yazi(x0 + 12, taban(y0, 28, 12), "Özellikler", 12, 600, C["metin"])
    t.simge("ara", x0 + w - 56, y0 + 14, 13, C["metin3"], 1.3)
    t.simge("pin", x0 + w - 36, y0 + 14, 13, C["metin3"], 1.3)
    t.simge("kapat", x0 + w - 16, y0 + 14, 12, C["metin3"], 1.3)
    # nesne başlığı
    oy = y0 + 28
    t.dikdortgen(x0 + 1, oy, w - 1, 40, dolgu=C["yuzey"])
    t.yatay(x0, x0 + w, oy + 39, C["cizgi2"])
    if nesne == "kiris":
        t.dikdortgen(x0 + 12, oy + 8, 24, 24, dolgu=C["secim_ton"], r=4)
        t.simge("kiris", x0 + 24, oy + 20, 16, C["vurgu"], 1.5)
        t.yazi(x0 + 44, oy + 18, "Kiriş · 6 seçili", 12, 600, C["metin"])
        t.yazi(x0 + 44, oy + 32, "IPE400 · S355 · Kat 2 (+9,00) · Aks 1–2", 11, 400, C["metin3"])
        bolumler = OZELLIKLER_KIRIS
    else:
        t.dikdortgen(x0 + 12, oy + 8, 24, 24, dolgu="#F6E0DE", r=4)
        t.simge("kolon", x0 + 24, oy + 20, 16, C["hata"], 1.5)
        t.yazi(x0 + 44, oy + 18, "Kolon · K1-C2", 12, 600, C["metin"])
        t.yazi(x0 + 44, oy + 32, "HE340A · S355 · Kat 1 (+4,50) · Aks C/2", 11, 400, C["metin3"])
        bolumler = OZELLIKLER_KOLON
    y = oy + 40
    lw = 108
    vx = x0 + 12 + lw
    vw = w - 12 - lw - 14
    rh = 20
    alt_sinir = y0 + h - 40          # alt çubuk (Uygula / Al) — kaydırılan içerik satır sınırında kesilir
    tasti = False
    for bad, acik, satirlar in bolumler:
        if y + rh > alt_sinir:
            tasti = True
            break
        t.dikdortgen(x0 + 1, y, w - 1, rh, dolgu=C["yuzey2"])
        t.sevron(x0 + 14, y + rh / 2, "asagi" if acik else "sag", 9, C["metin2"])
        t.yazi(x0 + 26, taban(y, rh, 11), bad, 11, 600, C["metin2"])
        y += rh
        if not acik:
            continue
        for etiket, deger, tur in satirlar:
            if y + rh > alt_sinir:
                tasti = True
                break
            t.yatay(x0 + 1, x0 + w, y + rh - 1, C["cizgi2"])
            t.yazi(x0 + 12, taban(y, rh, 12), etiket, 12, 400, C["metin2"])
            fy, fh = y + 2, rh - 4
            if tur == "katalog":
                fw = vw - 24
                t.giris(vx, fy, fw, fh, deger, 12, odak=(etiket == "Kesit" and nesne == "kiris"), imlec=(etiket == "Kesit" and nesne == "kiris"))
                t.dikdortgen(vx + fw + 4, fy, 20, fh, dolgu=C["yuzey"], kenar="#C9CDD3", r=3)
                t.yazi_orta(vx + fw + 14, taban(fy, fh, 12), "…", 12, 600, C["metin2"])
            elif tur.startswith("acilir"):
                t.acilir(vx, fy, vw, fh, deger, 12)
                if tur == "acilir_altin":
                    t.dikdortgen(vx + vw - 32, fy + 4, 8, 8, dolgu=ALTIN, kenar="#FFFFFF")
                elif tur == "acilir_kahve":
                    t.dikdortgen(vx + vw - 32, fy + 4, 8, 8, dolgu=KAHVE, kenar="#FFFFFF")
            elif tur == "coklu":
                t.giris(vx, fy, vw, fh, deger, 12, renk=C["metin3"])
            elif tur == "salt":
                t.yazi(vx + 7, taban(y, rh, 12), deger, 12, 400, C["metin"], tnum=True)
            elif tur == "renk":
                t.dikdortgen(vx + 6, fy + 3, 10, 10, dolgu="#D5D8DD", kenar="#454B53")
                t.yazi(vx + 22, taban(y, rh, 12), deger, 12, 400, C["metin"])
            elif tur == "onay":
                t.onay_kutusu(vx + 6, fy + 2, True, 12)
                t.yazi(vx + 24, taban(y, rh, 12), deger, 12, 400, C["metin"])
            elif tur == "dc":
                t.dikdortgen(vx + 6, fy + 2, 36, fh - 4, dolgu=DC_RENK[1], r=2)
                t.yazi_orta(vx + 24, taban(fy, fh, 11), deger, 11, 600, "#FFFFFF", tnum=True)
                t.yazi(vx + 50, taban(y, rh, 11), "1,2G + 1,6Q", 11, 400, C["metin3"])
            elif tur == "dc_kirmizi":
                t.dikdortgen(vx + 6, fy + 2, 36, fh - 4, dolgu=DC_RENK[4], r=2)
                t.yazi_orta(vx + 24, taban(fy, fh, 11), deger, 11, 600, "#FFFFFF", tnum=True)
                t.yazi(vx + 50, taban(y, rh, 11), "eğilme + eksenel", 11, 400, C["metin3"])
            elif tur == "hata":
                t.simge("uyari", vx + 12, y + rh / 2, 13, C["hata"], 1.4)
                t.yazi(vx + 24, taban(y, rh, 12), deger, 12, 500, C["hata"])
            else:
                t.giris(vx, fy, vw, fh, deger, 12)
            y += rh
        if tasti:
            break
    # kaydırma çubuğu ipucu (taşan içerikte daha kısa tutamaç)
    t.dikdortgen(x0 + w - 6, oy + 44, 3, 160 if tasti else 220, dolgu="#D3D6DB", r=1.5)
    # alt: Uygula / Al / anında uygula
    fy = y0 + h - 40
    t.dikdortgen(x0 + 1, fy, w - 1, 40, dolgu=C["yuzey2"])
    t.yatay(x0, x0 + w, fy, C["cizgi"])
    t.dugme(x0 + 12, fy + 9, 78, 22, "Uygula", birincil=True)
    t.dugme(x0 + 96, fy + 9, 48, 22, "Al")
    t.anahtar(x0 + w - 110, fy + 13, True, 24, 13)
    t.yazi(x0 + w - 80, taban(fy, 40, 11), "Anında uygula", 11, 400, C["metin2"])


PENCERELER = [("etiket", "Özellikler"), ("kutuphane", "Kataloglar"), ("katman", "Model ağacı"), ("suz", "Filtre & görünürlük"), ("sorgu", "Sorgu")]


def pencere_seridi(t, L, etkin="Özellikler"):
    x0, y0, w, h = L.W - L.strip_w, L.ust, L.strip_w, L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=C["zemin"])
    t.dikey(x0, y0, y0 + h, C["cizgi"])
    y = y0 + 8
    for ik, ad in PENCERELER:
        th = t.yazi_gen(ad, 11, 500) + 34
        if ad == etkin:
            t.dikdortgen(x0 + 1, y, w - 1, th, dolgu=C["secim_ton"])
            t.dikey(x0 + w - 3, y, y + th, C["secim"], 3)
            t.simge(ik, x0 + w / 2, y + 12, 14, C["vurgu"], 1.5)
            t.yazi_dikey(x0 + w / 2 - 8, y + 24, ad, 11, 600, C["metin"])
        else:
            t.simge(ik, x0 + w / 2, y + 12, 14, C["metin2"], 1.4)
            t.yazi_dikey(x0 + w / 2 - 8, y + 24, ad, 11, 500, C["metin2"])
            if ad == "Model ağacı":  # sola yapıştırılmış
                t.simge("sol_yapistir", x0 + w / 2, y + th - 8, 9, C["metin3"], 1.2)
        y += th + 6
    t.yatay(x0 + 6, x0 + w - 6, y, C["cizgi"])
    t.simge("sevron_cift_asagi", x0 + w / 2, y + 16, 12, C["metin3"], 1.3)


# ============================================================================
# ALT RIHTIM: sekmeli (Komut / Mesajlar / Tablolar) + komut satırı + durum çubuğu
# ============================================================================
DOCK_SATIRLAR = [
    ("KİRİŞ", "IPE400 · S355 · Kat 2 · Mafsal–Mafsal · kapsam: Benzer katlar", "6 kiriş eklendi (Kat 2) · 0,3 s", "ok"),
    ("SEÇ", "6 nesne seçildi: Kiriş ×6 · Kat 2 · Aks 1–2", "Enter: KİRİŞ'i yinele", ""),
]


def dock(t, L, mod="komut", satirlar=None):
    x0, y0, w = L.ray_w, L.alt, L.W - L.ray_w
    th, dh = L.dock_tab_h, L.dock_h
    t.dikdortgen(x0, y0, w, th, dolgu=C["zemin"])
    t.yatay(x0, x0 + w, y0, C["cizgi"])
    x = x0 + 10
    etkin = "Tablolar" if mod == "tablolar" else "Komut"
    for ad, rozet in (("Komut", ""), ("Mesajlar", "2"), ("Tablolar", "" if mod != "tablolar" else "Çelik tasarım özeti")):
        tw = t.yazi_gen(ad, 11, 500)
        if ad == etkin:
            t.yazi(x, taban(y0, th, 11), ad, 11, 600, C["metin"])
            t.yatay(x - 2, x + tw + 2, y0 + th - 2, C["vurgu"], 2)
        else:
            t.yazi(x, taban(y0, th, 11), ad, 11, 500, C["metin2"])
        x += tw + 6
        if rozet and ad == "Mesajlar":
            t.dikdortgen(x, y0 + 5, 14, 13, dolgu=C["uyari"], r=6.5)
            t.yazi_orta(x + 7, taban(y0 + 5, 13, 9), rozet, 9, 600, "#FFFFFF")
            x += 16
        elif rozet:
            t.yazi(x, taban(y0, th, 11), "· " + rozet, 11, 400, C["metin3"])
            x += t.yazi_gen("· " + rozet, 11, 400) + 6
        x += 12
    t.simge("pin", x0 + w - 40, y0 + th / 2, 12, C["metin3"], 1.3)
    t.simge("sevron_asagi", x0 + w - 18, y0 + th / 2, 12, C["metin3"], 1.3)
    cy = y0 + th
    t.dikdortgen(x0, cy, w, dh, dolgu=C["yuzey"])
    if mod == "tablolar":
        tablo_icerik(t, x0, cy, w, dh)
    else:
        satirlar = satirlar or DOCK_SATIRLAR
        rh = 18
        yy = cy + (dh - rh * len(satirlar)) / 2
        for k, ozet, sonuc, renk in satirlar:
            t.yazi(x0 + 12, taban(yy, rh, 11), "›", 11, 600, C["metin3"])
            t.yazi(x0 + 24, taban(yy, rh, 11), k, 11, 600, C["vurgu"])
            t.yazi(x0 + 24 + t.yazi_gen(k, 11, 600) + 10, taban(yy, rh, 11), ozet, 11, 400, C["metin2"])
            t.yazi_sag(x0 + w - 14, taban(yy, rh, 11), sonuc, 11, 500 if renk == "ok" else 400, C["ok"] if renk == "ok" else C["metin3"])
            yy += rh


TABLO_BASLIK = ["Eleman", "Kat", "Kesit", "Kritik komb.", "N_Ed (kN)", "M_y,Ed (kNm)", "V_Ed (kN)", "D/C", "Durum"]
TABLO_SATIR = [
    ["K1-C2", "Kat 1", "HE340A", "1,2G + 1,6Q", "−1 842", "212", "64", "1,04", "Yetersiz"],
    ["K1-B2", "Kat 1", "HE340A", "1,2G + 1,6Q", "−1 790", "188", "58", "0,96", "Yeterli"],
    ["K1-3BC", "Kat 1", "IPE400", "1,2G + 1,6Q", "12", "118", "81", "0,91", "Yeterli"],
    ["K2-1BC", "Kat 2", "IPE400", "G + Q + 0,3W", "8", "96", "66", "0,62", "Yeterli"],
    ["Ç1-A12", "Kat 1", "L100x10", "G + E_x", "−214", "—", "—", "0,79", "Yeterli"],
]


def tablo_icerik(t, x0, y0, w, h):
    kolw = [70, 54, 72, 104, 80, 92, 74, 52, 80]
    rh = 20
    x = x0 + 10
    t.dikdortgen(x0, y0, w, rh, dolgu=C["yuzey2"])
    t.yatay(x0, x0 + w, y0 + rh - 1, C["cizgi"])
    for b, kw in zip(TABLO_BASLIK, kolw):
        sag = b in ("N_Ed (kN)", "M_y,Ed (kNm)", "V_Ed (kN)", "D/C")
        if sag:
            t.yazi_sag(x + kw - 8, taban(y0, rh, 11), b, 11, 600, C["metin2"])
        else:
            t.yazi(x, taban(y0, rh, 11), b, 11, 600, C["metin2"])
        x += kw
    t.yazi_sag(x0 + w - 12, taban(y0, rh, 10), "263 satır · süzgeç: D/C > 0,60 · CSV'ye aktar", 10, 400, C["metin3"])
    y = y0 + rh
    for i, sat in enumerate(TABLO_SATIR):
        if y + rh > y0 + h:
            break
        if i == 0:
            t.dikdortgen(x0, y, w, rh, dolgu=C["secim_ton"])
        t.yatay(x0, x0 + w, y + rh - 1, C["cizgi2"])
        x = x0 + 10
        for j, (v, kw) in enumerate(zip(sat, kolw)):
            sag = j in (4, 5, 6, 7)
            renk = C["metin"]
            if j == 8:
                renk = C["hata"] if v == "Yetersiz" else C["ok"]
            if j == 7:
                dcv = float(v.replace(",", "."))
                rk = next((r for e, r in zip(DC_ESIK, DC_RENK) if dcv <= e), DC_RENK[-1])
                t.dikdortgen(x + kw - 8 - 34, y + 3, 34, rh - 6, dolgu=rk, r=2)
                t.yazi_orta(x + kw - 8 - 17, taban(y + 3, rh - 6, 10), v, 10, 600, "#FFFFFF", tnum=True)
            elif sag:
                t.yazi_sag(x + kw - 8, taban(y, rh, 11), v, 11, 400, renk, tnum=True)
            else:
                t.yazi(x, taban(y, rh, 11), v, 11, 500 if j == 0 else 400, renk, tnum=True)
            x += kw
        y += rh


def komut_satiri(t, L, metin="", son="Son: KİRİŞ — 6 kiriş eklendi (Kat 2)"):
    x0, y0, w, h = L.ray_w, L.alt + L.dock_tab_h + L.dock_h, L.W - L.ray_w, L.komut_h
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.yatay(x0, x0 + w, y0, C["cizgi"])
    t.yatay(x0, x0 + w, y0 + h - 1, C["cizgi"])
    t.dikey(x0, y0, y0 + h, C["vurgu"], 3)
    t.yazi(x0 + 14, taban(y0, h, 12), "Komut:", 12, 600, C["vurgu"])
    x = x0 + 14 + t.yazi_gen("Komut:", 12, 600) + 8
    if metin:
        t.yazi(x, taban(y0, h, 12), metin, 12, 400, C["metin"])
        x += t.yazi_gen(metin, 12, 400) + 1
    t.dikey(x, y0 + 8, y0 + h - 8, C["metin"], 1)   # imleç
    x += 12
    t.yazi(x, taban(y0, h, 12), "·", 12, 400, C["metin3"]); x += 12
    t.yazi(x, taban(y0, h, 12), son, 12, 400, C["metin3"])
    # sağ: ipuçları + hızlı başlat
    ip = [("Ctrl+Q", "odakla / hızlı başlat"), ("Tab", "tamamla"), ("Enter", "yinele"), ("Esc", "iptal")]
    if L.kucuk:
        ip = ip[:2]
    xr = x0 + w - 12
    for k, et in reversed(ip):
        tw = t.yazi_gen(et, 10, 400)
        xr -= tw
        t.yazi(xr, taban(y0, h, 10), et, 10, 400, C["metin3"])
        kw = t.yazi_gen(k, 10, 500) + 8
        xr -= kw + 4
        t.kisayol(xr, y0 + 7, k, 10, 15)
        xr -= 14


def durum_cubugu(t, L, kapsam="Benzer katlar", yonerge=None, koord=("0,000", "0,000", "6,900"), secili="Seçili: 6 (12 tutamaç)", kapsam_etkin=True):
    W = L.W
    y0, h = L.H - L.durum_h, L.durum_h
    t.dikdortgen(0, y0, W, h, dolgu=C["zemin"])
    t.yatay(0, W, y0, C["cizgi"])
    # sol: adım yönergesi
    t.simge("sevron_sag", 12, y0 + h / 2, 10, C["vurgu"], 1.8)
    if yonerge is None:
        yonerge = "Nesne seçin — Shift: ekle · Ctrl: çıkar" if L.kucuk else "Nesne seçin — Shift: ekle · Ctrl: çıkar · Enter: KİRİŞ'i yinele"
    t.yazi(22, taban(y0, h, 11), yonerge, 11, 500, C["metin"])
    # orta: Orto / Akıllı yakalama / Sürükle-bırak / X Y Z kilitleri / orta tuş
    x = (W / 2 - 240) if not L.kucuk else 300
    for et, acik, kis in (("ORTO", False, "O"), ("YAKALA", True, "S"), ("SÜRÜKLE", False, "D")):
        tw = t.yazi_gen(et, 10, 600) + 14
        if acik:
            t.dikdortgen(x, y0 + 5, tw, h - 10, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=3)
            t.yazi(x + 7, taban(y0 + 5, h - 10, 10), et, 10, 600, C["vurgu"])
        else:
            t.dikdortgen(x, y0 + 5, tw, h - 10, dolgu=None, kenar=C["cizgi"], r=3)
            t.yazi(x + 7, taban(y0 + 5, h - 10, 10), et, 10, 600, C["metin3"])
        x += tw + 4
    x += 6
    for et in "XYZ":
        t.dikdortgen(x, y0 + 5, 18, h - 10, dolgu=None, kenar=C["cizgi"], r=3)
        t.yazi_orta(x + 9, taban(y0 + 5, h - 10, 10), et, 10, 600, C["metin3"])
        x += 20
    if not L.kucuk:
        x += 8
        t.yazi(x, taban(y0, h, 10), "Orta tuş: Kaydır", 10, 400, C["metin3"])
    # sağ: seçili sayısı · koordinat · birim · etkin kat · kat kapsamı anahtarı
    xr = W - 12
    tw = t.yazi_gen(secili, 11, 500, True)
    t.yazi(xr - tw, taban(y0, h, 11), secili, 11, 500, C["metin2"], tnum=True)
    xr -= tw + 14
    t.dikey(xr, y0 + 6, y0 + h - 6, C["cizgi"]); xr -= 12
    ko = f"X {koord[0]}   Y {koord[1]}   Z {koord[2]}"
    tw = t.yazi_gen(ko, 11, 400, True)
    t.yazi(xr - tw, taban(y0, h, 11), ko, 11, 400, C["metin2"], tnum=True)
    xr -= tw + 14
    t.dikey(xr, y0 + 6, y0 + h - 6, C["cizgi"]); xr -= 12
    bw = 62
    t.acilir(xr - bw, y0 + 4, bw, h - 8, "kN · m", 11)
    xr -= bw + 12
    t.dikey(xr, y0 + 6, y0 + h - 6, C["cizgi"]); xr -= 12
    if not L.kucuk:
        et = "Etkin kat: Kat 2"
        tw = t.yazi_gen(et, 11, 500)
        t.sevron(xr - 6, y0 + h / 2 + 0.5, "asagi", 9, C["metin2"])
        t.yazi(xr - tw - 14, taban(y0, h, 11), et, 11, 500, C["metin2"])
        xr -= tw + 26
    # kat kapsamı: üç durumlu segmentli anahtar
    secenekler = ["Bu kat", "Benzer katlar", "Tüm katlar"]
    sw = [t.yazi_gen(s, 11, 500) + 16 for s in secenekler]
    toplam = sum(sw) + 2
    sx = xr - toplam
    t.dikdortgen(sx, y0 + 4, toplam, h - 8, dolgu=C["yuzey"] if kapsam_etkin else C["zemin"], kenar=C["cizgi"], r=3)
    x = sx + 1
    for s, w_ in zip(secenekler, sw):
        if s == kapsam:
            t.dikdortgen(x, y0 + 5, w_, h - 10, dolgu=C["vurgu"] if kapsam_etkin else "#B8BCC4", r=2)
            t.yazi_orta(x + w_ / 2, taban(y0 + 5, h - 10, 11), s, 11, 600, "#FFFFFF")
        else:
            t.yazi_orta(x + w_ / 2, taban(y0 + 5, h - 10, 11), s, 11, 500, C["metin2"] if kapsam_etkin else C["metin3"])
        x += w_
    t.simge("katman", sx - 12, y0 + h / 2, 12, C["metin2"], 1.3)
    return sx, toplam


def kat_kapsami_ipucu(t, L, sx, toplam):
    """'3 katta uygulanacak' önizlemesi: anahtarın üstünde küçük balon."""
    y0 = L.H - L.durum_h
    satirlar = [("3 katta uygulanacak", 600, C["metin"]), ("Kat 1  +4,50", 400, C["metin2"]), ("Kat 2  +9,00  (ana kat)", 400, C["metin2"]),
                ("Kat 3  +13,50", 400, C["metin2"]), ("Zemin hariç · Alt+1/2/3 ile değiştir", 400, C["metin3"])]
    bw = max(t.yazi_gen(m, 11, a) for m, a, _ in satirlar) + 24
    bh = 10 + 18 * len(satirlar) + 6
    bx = sx + toplam / 2 - bw / 2 + 30
    by = y0 - bh - 10
    t.golge(bx, by, bw, bh, r=4, yaricap=5, alfa=0.16)
    t.dikdortgen(bx, by, bw, bh, dolgu="#FFFFFF", kenar=C["cizgi"], r=4)
    t.cokgen([(sx + toplam / 2 + 40, by + bh), (sx + toplam / 2 + 50, by + bh), (sx + toplam / 2 + 45, by + bh + 6)], dolgu="#FFFFFF", kenar=C["cizgi"], kalinlik=1)
    y = by + 8
    for i, (m, a, r) in enumerate(satirlar):
        if 1 <= i <= 3:
            t.dikdortgen(bx + 12, y + 5, 8, 8, dolgu=C["vurgu"] if i == 2 else C["vurgu_ton2"], r=1)
            t.yazi(bx + 26, taban(y, 18, 11), m, 11, a, r, tnum=True)
        else:
            t.yazi(bx + 12, taban(y, 18, 11), m, 11, a, r)
        y += 18


# ============================================================================
# SEÇ VE SÜZ İLETİŞİM KUTUSU
# ============================================================================
def secsuz_iletisim(t, L):
    W, H = 824, 520
    # görünümün sağına kaydırılmış (modsuz pencere): soldaki altın önizleme görünür kalır
    x0 = L.vp_x1 - W - 14
    y0 = L.vp_y0 + (L.vp_h - H) / 2 + 30
    t.karart(L.vp_x0, L.vp_y0, L.vp_w, L.vp_h, 0.06)
    t.golge(x0, y0, W, H, r=6, yaricap=12, alfa=0.28, dy=6)
    t.dikdortgen(x0, y0, W, H, dolgu=C["yuzey"], kenar="#B9BDC4", r=6)
    # başlık
    t.dikdortgen(x0, y0, W, 36, dolgu=C["yuzey2"], r=6)
    t.dikdortgen(x0, y0 + 20, W, 16, dolgu=C["yuzey2"])
    t.yatay(x0, x0 + W, y0 + 35, C["cizgi"])
    t.simge("sec_suz", x0 + 20, y0 + 18, 16, C["vurgu"], 1.5)
    t.yazi(x0 + 36, taban(y0, 36, 13), "Seç ve Süz", 13, 600, C["metin"])
    t.yazi(x0 + 36 + t.yazi_gen("Seç ve Süz", 13, 600) + 10, taban(y0, 36, 11), "Seçim süzgeci · görünüm süzgeci · renk kuralı aynı motoru kullanır", 11, 400, C["metin3"])
    t.simge("kapat", x0 + W - 18, y0 + 18, 13, C["metin2"], 1.3)
    # sol: kayıtlı süzgeçler
    lx, ly, lw = x0 + 16, y0 + 50, 196
    t.yazi(lx, taban(ly, 20, 11), "KAYITLI SÜZGEÇLER", 10, 600, C["metin3"])
    t.simge("artı", lx + lw - 10, ly + 10, 12, C["metin2"], 1.4)
    ly += 24
    t.dikdortgen(lx, ly, lw, 300, dolgu=C["yuzey"], kenar=C["cizgi"], r=3)
    kayitli = [("IPE400 kirişler – Kat 2", True, True), ("Ana çerçeve kirişleri", False, False), ("Çatı aşıkları", False, False),
               ("Çaprazlar – A ve D aksı", False, False), ("Zemin kat kolonları", False, False), ("Mafsallı uçlar", False, False),
               ("Döşemeler (tümü)", False, False)]
    y = ly + 4
    for ad, secili, degisti in kayitli:
        if secili:
            t.dikdortgen(lx + 1, y, lw - 2, 22, dolgu=C["vurgu_ton"])
            t.dikey(lx + 1, y, y + 22, C["vurgu"], 2)
        t.simge("suz", lx + 14, y + 11, 12, C["vurgu"] if secili else C["metin3"], 1.3)
        t.yazi(lx + 26, taban(y, 22, 12), ad + (" *" if degisti else ""), 12, 600 if secili else 400, C["metin"])
        y += 22
    t.yazi(lx, taban(ly + 304, 18, 10), "Dosya: Depo Binası.op4/suzgecler/*.filtre", 10, 400, C["metin3"])
    # sağ: kural satırları
    rx, ry = x0 + 230, y0 + 50
    kw = [112, 126, 92, 140, 20]
    bas = ["Kategori", "Özellik", "Koşul", "Değer", ""]
    x = rx
    for b, w_ in zip(bas, kw):
        t.yazi(x, taban(ry, 20, 10), b.upper(), 10, 600, C["metin3"])
        x += w_ + 6
    t.yazi(rx + sum(kw) + 30, taban(ry, 20, 10), "VE / VEYA", 10, 600, C["metin3"])
    ry += 24
    kurallar = [("(", "Kiriş", "Kesit", "eşittir", "IPE400", "Ve"), ("", "Kiriş", "Kat", "eşittir", "Kat 2", "Ve"),
                ("", "Kiriş", "Serbestlik (başlangıç)", "eşittir", "Mafsal", "Veya"), (")", "Kiriş", "Malzeme", "eşittir", "S355", "")]
    for i, (par, kat, oz, kos, deg, bag) in enumerate(kurallar):
        y = ry + i * 30
        x = rx
        t.yazi(x - 12, taban(y, 24, 12), par, 12, 500, C["metin3"])
        t.acilir(x, y, kw[0], 24, kat, 12); x += kw[0] + 6
        t.acilir(x, y, kw[1], 24, oz, 12); x += kw[1] + 6
        t.acilir(x, y, kw[2], 24, kos, 12); x += kw[2] + 6
        if oz in ("Kesit", "Malzeme"):
            t.giris(x, y, kw[3] - 24, 24, deg, 12, odak=(i == 0))
            t.dikdortgen(x + kw[3] - 20, y, 20, 24, dolgu=C["yuzey"], kenar="#C9CDD3", r=3)
            t.yazi_orta(x + kw[3] - 10, taban(y, 24, 12), "…", 12, 600, C["metin2"])
        else:
            t.acilir(x, y, kw[3], 24, deg, 12)
        x += kw[3] + 6
        t.simge("sil", x + 10, y + 12, 13, C["metin3"], 1.3); x += kw[4] + 10
        if bag:
            t.acilir(x, y, 64, 24, bag, 11)
    y = ry + len(kurallar) * 30 + 2
    t.simge("artı", rx + 8, y + 10, 12, C["vurgu"], 1.5)
    t.yazi(rx + 20, taban(y, 20, 11), "Satır ekle", 11, 500, C["vurgu"])
    t.yazi(rx + 110, taban(y, 20, 11), "Boş koşul = Ve · Parantezle gruplama · Değerde * joker", 11, 400, C["metin3"])
    # kapsam
    y += 32
    t.yazi(rx, taban(y, 24, 11), "Kapsam", 11, 600, C["metin2"])
    sx = rx + 70
    for s, etkin in (("Bu kat", False), ("Benzer katlar", True), ("Tüm katlar", False), ("Tüm model", False)):
        w_ = t.yazi_gen(s, 11, 500) + 18
        if etkin:
            t.dikdortgen(sx, y + 2, w_, 20, dolgu=C["vurgu"], r=3)
            t.yazi_orta(sx + w_ / 2, taban(y + 2, 20, 11), s, 11, 600, "#FFFFFF")
        else:
            t.dikdortgen(sx, y + 2, w_, 20, dolgu=C["yuzey"], kenar=C["cizgi"], r=3)
            t.yazi_orta(sx + w_ / 2, taban(y + 2, 20, 11), s, 11, 500, C["metin2"])
        sx += w_ + 4
    t.onay_kutusu(sx + 12, y + 6, True, 12)
    t.yazi(sx + 30, taban(y, 24, 11), "Yalnız görünür nesneler", 11, 400, C["metin"])
    # sonuç
    y += 36
    t.dikdortgen(rx, y, W - 230 - 16, 44, dolgu=C["secim_ton"], kenar=C["secim_ton2"], r=3)
    t.simge("dogrula", rx + 16, y + 22, 16, C["vurgu"], 1.5)
    t.yazi(rx + 32, y + 18, "Eşleşen: 31 nesne — Kat 2: 31 · Benzer katlar (3 kat): 93", 12, 600, C["metin"], tnum=True)
    t.yazi(rx + 32, y + 34, "Önizleme modelde altın konturla vurgulanıyor · Ctrl+K: seçimi tersine çevir · Ctrl+J: önceki seçim", 10, 400, C["metin2"])
    # renk kuralı / görünüm süzgeci satırı
    y += 56
    t.onay_kutusu(rx, y + 4, False, 12)
    t.yazi(rx + 18, taban(y, 20, 11), "Görünüm süzgeci olarak da uygula (eşleşmeyenler %85 saydam)", 11, 400, C["metin"])
    y += 22
    t.onay_kutusu(rx, y + 4, False, 12)
    t.yazi(rx + 18, taban(y, 20, 11), "Renk kuralı yap:", 11, 400, C["metin"])
    t.dikdortgen(rx + 112, y + 2, 14, 16, dolgu=ALTIN, kenar="#FFFFFF")
    t.yazi(rx + 132, taban(y, 20, 11), "Altın · 'IPE400 kirişler – Kat 2'", 11, 400, C["metin3"])
    # alt düğmeler
    by = y0 + H - 44
    t.yatay(x0, x0 + W, by, C["cizgi2"])
    t.dugme(x0 + 16, by + 10, 108, 24, "Benzerini seç")
    t.dugme(x0 + 130, by + 10, 84, 24, "Kaydet…")
    t.dugme(x0 + 220, by + 10, 96, 24, "Farklı kaydet…")
    t.dugme(x0 + W - 16 - 72, by + 10, 72, 24, "Kapat")
    t.dugme(x0 + W - 16 - 72 - 8 - 72, by + 10, 72, 24, "Seç", birincil=True)
    t.dugme(x0 + W - 16 - 72 - 8 - 72 - 8 - 96, by + 10, 96, 24, "Seçime ekle")
    t.yazi(x0 + 326, taban(by + 10, 24, 10), "Uygula ile açık kalır", 10, 400, C["metin3"])


# ============================================================================
# SONUÇ EKRANI PARÇALARI: D/C lejantı + deformasyon kartı
# ============================================================================
def dc_lejant(t, L):
    x0, y1, w = L.vp_x0, L.vp_y1, L.vp_w
    lw, lh = 640, 36
    lx = x0 + w / 2 - lw / 2 - 40
    ly = y1 - lh - 12
    t.golge(lx, ly, lw, lh, r=4, yaricap=5, alfa=0.14)
    t.dikdortgen(lx, ly, lw, lh, dolgu=(255, 255, 255, 244), kenar=C["cizgi"], r=4)
    t.yazi(lx + 10, taban(ly, lh, 11), "D/C", 11, 600, C["metin"])
    sx = lx + 44
    sw = 84
    etik = ["≤ 0,50", "0,70", "0,90", "1,00", "> 1,00"]
    for i, r in enumerate(DC_RENK):
        t.dikdortgen(sx + i * sw, ly + 8, sw - 2, 12, dolgu=r, r=1)
        if 1 <= i <= 3:
            t.giris(sx + i * sw - 20, ly + 21, 40, 13, etik[i], 9, hiza="sag")
        elif i == 0:
            t.yazi(sx, taban(ly + 21, 13, 9), etik[i], 9, 500, C["metin2"], tnum=True)
        else:
            t.yazi_sag(sx + 5 * sw - 2, taban(ly + 21, 13, 9), etik[i], 9, 500, C["metin2"], tnum=True)
    t.yazi_sag(lx + lw - 10, taban(ly, lh, 10), "Çelik oranları · 5 eşik", 10, 400, C["metin3"])
    # sayım rozeti: aşan eleman
    bx = lx + lw + 10
    t.dikdortgen(bx, ly + 6, 118, 24, dolgu="#FBE9E7", kenar="#E6B9B4", r=12)
    t.simge("uyari", bx + 14, ly + 18, 13, C["hata"], 1.4)
    t.yazi(bx + 26, taban(ly + 6, 24, 11), "1 eleman > 1,00", 11, 600, C["hata"], tnum=True)


def deform_karti(t, L):
    x0, y0 = L.vp_x0, L.vp_y0
    kw, kh = 236, 150
    kx, ky = x0 + 10, y0 + 46
    t.golge(kx, ky, kw, kh, r=4, yaricap=5, alfa=0.14)
    t.dikdortgen(kx, ky, kw, kh, dolgu=(255, 255, 255, 246), kenar=C["cizgi"], r=4)
    t.dikdortgen(kx, ky, kw, 24, dolgu=C["yuzey2"], r=4)
    t.dikdortgen(kx, ky + 12, kw, 12, dolgu=C["yuzey2"])
    t.yatay(kx, kx + kw, ky + 23, C["cizgi2"])
    t.simge("deform", kx + 14, ky + 12, 13, C["vurgu"], 1.4)
    t.yazi(kx + 26, taban(ky, 24, 11), "Sonuç gösterimi", 11, 600, C["metin"])
    t.simge("kapat", kx + kw - 12, ky + 12, 11, C["metin3"], 1.3)
    y = ky + 30
    t.yazi(kx + 10, taban(y, 20, 11), "Kombinasyon", 11, 400, C["metin2"])
    t.acilir(kx + 92, y + 1, kw - 102, 18, "1,2G + 1,6Q", 11)
    y += 22
    t.yazi(kx + 10, taban(y, 20, 11), "Gösterim", 11, 400, C["metin2"])
    sx = kx + 92
    for s, etkin in (("D/C", True), ("Deformasyon", False), ("M3", False)):
        w_ = t.yazi_gen(s, 10, 500) + 12
        if etkin:
            t.dikdortgen(sx, y + 2, w_, 16, dolgu=C["vurgu"], r=2)
            t.yazi_orta(sx + w_ / 2, taban(y + 2, 16, 10), s, 10, 600, "#FFFFFF")
        else:
            t.dikdortgen(sx, y + 2, w_, 16, dolgu=C["yuzey"], kenar=C["cizgi"], r=2)
            t.yazi_orta(sx + w_ / 2, taban(y + 2, 16, 10), s, 10, 500, C["metin2"])
        sx += w_ + 3
    y += 22
    t.yazi(kx + 10, taban(y, 20, 11), "Ölçek", 11, 400, C["metin2"])
    t.acilir(kx + 92, y + 1, 70, 18, "Otomatik", 11)
    t.giris(kx + 166, y + 1, kw - 176, 18, "1 : 250", 11, renk=C["metin3"], hiza="sag")
    y += 22
    t.onay_kutusu(kx + 10, y + 4, True, 12); t.yazi(kx + 28, taban(y, 20, 11), "Gölge (deformasyonsuz)", 11, 400, C["metin"])
    y += 20
    t.onay_kutusu(kx + 10, y + 4, True, 12); t.yazi(kx + 28, taban(y, 20, 11), "Kübik eğri", 11, 400, C["metin"])
    t.onay_kutusu(kx + 120, y + 4, False, 12); t.yazi(kx + 138, taban(y, 20, 11), "Değerler", 11, 400, C["metin"])
    y += 22
    t.dikdortgen(kx + 10, y, 22, 18, dolgu=C["yuzey"], kenar=C["cizgi"], r=3)
    t.simge("oynat", kx + 21, y + 9, 11, C["vurgu"], 1.5)
    t.yazi(kx + 38, taban(y, 18, 10), "Animasyon", 10, 400, C["metin2"])
    t.dikdortgen(kx + 100, y + 8, kw - 112, 2, dolgu=C["cizgi"])
    t.dikdortgen(kx + 100, y + 8, 48, 2, dolgu=C["vurgu"])
    t.daire(kx + 148, y + 9, 5, dolgu="#FFFFFF", kenar=C["vurgu"], kalinlik=1.5)


# ============================================================================
# EKRAN KOMPOZİSYONU
# ============================================================================
def ekran(W, H, s=1, kucuk=False, mod="ana", onbellek=None):
    """mod: ana | secsuz | sonuc | kapsam"""
    dock_h = 128 if mod == "sonuc" else None
    L = Yerlesim(W, H, kucuk, dock_h=dock_h)
    t = Tuval(W, H, s)
    baslik_cubugu(t, L)
    if mod == "sonuc":
        serit(t, L, etkin="Tasarım", gruplar=GRUPLAR_TASARIM)
    else:
        serit(t, L, etkin="Model")
    ray(t, L)
    model_agaci(t, L)
    gorunum_sekmeleri(t, L)
    sahne_mod = "dc" if mod == "sonuc" else ("suzgec" if mod == "secsuz" else "secim")
    viewport(t, L, mod=sahne_mod, sahne_onbellek=onbellek)
    if mod == "sonuc":
        dc_lejant(t, L)
        deform_karti(t, L)
        ozellikler(t, L, nesne="kolon")
        pencere_seridi(t, L)
        dock(t, L, mod="tablolar")
        komut_satiri(t, L, son="Son: TASARLA — 263 eleman kontrol edildi · 1 yetersiz (K1-C2) · 2,4 s")
        durum_cubugu(t, L, yonerge="Tasarım tamamlandı — elemana tıklayın: ayrıntı · sağ tık: etkileşimli tasarım",
                     secili="Seçili: 1 (kolon)", koord=("12,000", "6,000", "2,250"), kapsam_etkin=True)
    else:
        ozellikler(t, L)
        pencere_seridi(t, L)
        dock(t, L)
        komut_satiri(t, L)
        sx, toplam = durum_cubugu(t, L)
        if mod == "secsuz":
            secsuz_iletisim(t, L)
    t.dikdortgen(0, 0, W, H, kenar="#C9CCD1")
    return t, L


def kaydet(img, ad):
    yol = os.path.join(BURASI, ad)
    img.save(yol, optimize=True)
    print(f"  yazıldı: {yol}  ({img.width}×{img.height})")
    return yol


def kat_kapsami_gorsel(onbellek):
    """Plan bağlamında durum çubuğu: anahtar 'Benzer katlar' + '3 katta uygulanacak' önizlemesi; 2× kırpım."""
    W, H = 1920, 1080
    L = Yerlesim(W, H)
    t = Tuval(W, H, 2)
    # yalnızca alt bölge gerekli: komut satırı + durum çubuğu + biraz görünüm
    t.dikdortgen(0, 0, W, H, dolgu=C["vp_alt"])
    t.gradyan(0, L.vp_y1 - 160, W, 160, C["vp_ust"], C["vp_alt"])
    dock(t, L, satirlar=[
        ("KİRİŞ", "IPE400 · S355 · Kat 2 · Mafsal–Mafsal · kapsam: Benzer katlar", "ilk nokta: B/2 (6,000 · 6,000)", ""),
        ("PLAN", "Plan – Kat 2 (+9,00) etkin · yakalama: aks kesişimi · Orto kapalı", "Alt+1/2/3: kapsam", ""),
    ])
    komut_satiri(t, L, metin="kiriş", son="İkinci noktayı seçin · Esc: iptal")
    sx, toplam = durum_cubugu(t, L, yonerge="KİRİŞ · İkinci noktayı seçin — Plan: Kat 2 (+9,00) · kapsam: Benzer katlar",
                              koord=("12,000", "6,000", "9,000"), secili="Seçili: 0")
    kat_kapsami_ipucu(t, L, sx, toplam)
    im = t.img.crop((t.p(W - 1100), t.p(L.H - 150), t.p(W), t.p(H)))
    return im


def ana():
    hizli = "--hizli" in sys.argv
    t0 = time.time()
    print("Atölye — üretim başlıyor")
    onb = {}
    t1, L1 = ekran(1920, 1080, 1, onbellek=onb)
    kaydet(t1.img, "ana.png")
    if hizli:
        return
    t2, L2 = ekran(1920, 1080, 2, onbellek=onb)
    kaydet(t2.img, "ana-2x.png")
    serit_k = t2.img.crop((0, t2.p(L2.baslik_h - 2), t2.p(1620), t2.p(L2.ust + 2)))
    kaydet(serit_k, "detay-serit.png")
    yh = 720
    ag = t2.img.crop((t2.p(L2.ray_w), t2.p(L2.ust), t2.p(L2.ray_w + L2.agac_w), t2.p(L2.ust + yh)))
    oz = t2.img.crop((t2.p(L2.vp_x1), t2.p(L2.ust), t2.p(L2.W), t2.p(L2.ust + yh)))
    bos = t2.p(16)
    pan = Image.new("RGB", (ag.width + bos + oz.width, ag.height), hex2rgb(C["zemin"]))
    pan.paste(ag, (0, 0)); pan.paste(oz, (ag.width + bos, 0))
    kaydet(pan, "detay-panel.png")
    t3, _ = ekran(1366, 768, 1, kucuk=True, onbellek=onb)
    kaydet(t3.img, "kucuk.png")
    t4, _ = ekran(1920, 1080, 1, mod="secsuz", onbellek=onb)
    kaydet(t4.img, "secsuz.png")
    t5, _ = ekran(1920, 1080, 1, mod="sonuc", onbellek=onb)
    kaydet(t5.img, "sonuc.png")
    kaydet(kat_kapsami_gorsel(onb), "kat-kapsami.png")
    print(f"bitti ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    ana()
