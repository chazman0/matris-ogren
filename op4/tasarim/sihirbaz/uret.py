#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
op4 — Yönetmelik Sihirbazı taslak görselleri ("Atölye" yerleşimi, modernize; tunç/kahve–altın vurgu YOK).

Üretilenler (bu klasöre):
  sihirbaz-1-proje.png  sihirbaz-4-deprem.png  sihirbaz-5-zemin.png  sihirbaz-8-ozet.png   (1920×1080)
  karsilastirma.png     (2400 px genişlik; dördü etiketli)

Renkler: YALNIZ aşağıdaki PALET sözlüğü. Modernize palet hazır olunca bu sözlük (ya da PALET_SEC satırı) değişir,
`python3 uret.py` yeniden çalıştırılır; başka hiçbir dosyada sabit renk yoktur (tuval.py renkleri buradan alır).

Sayılar elle yazılmaz: S_DS, S_D1, F_S, F_1, T_A, T_B, DTS, BYS, T_pA, λ, kar S_k, kombinasyon sayıları ve malzeme
değerleri depodaki hesap motorunun kendi işlevlerinden (yapi._spektrum, _dts, _bys, _kombinasyon_listesi; yapi_veri
tabloları) hesaplanır. Örnek saha değerleri (S_S, S_1, q_em, k0 …) TEMSİLİDİR; gerçek bir parsel için değildir.
"""
import math
import os
import sys

# ============================================================================
# PALET — tek renk kaynağı (nötr yüzeyler + tek soğuk vurgu; "kobalt" yer tutucu)
# ============================================================================
PALETLER = {
    "kobalt": dict(
        # yüzeyler
        zemin="#F3F4F6", yuzey="#FFFFFF", yuzey2="#F8F9FA", yuzey3="#EEF0F2", hover="#ECEEF1",
        cizgi="#D7DAE0", cizgi2="#E6E8EC", giris_kenar="#C9CDD3", onay_kenar="#B8BCC4", dugme_kenar="#C4C8CF",
        pencere_kenar="#B9BDC4", kod_zemin="#F2F4F7", kod_kenar="#E3E6EB",
        # metin
        metin="#14181B", metin2="#4E545C", metin3="#868B93", kod_metin="#2B3440", beyaz="#FFFFFF",
        # simge
        simge="#2F343B", simge2="#3C4148", simge_pasif="#B3B7BE",
        # tek vurgu (etkin / birincil / odak / seçim)
        vurgu="#2563EB", vurgu_koyu="#1D4ED8", vurgu_ton="#EEF3FE", vurgu_ton2="#C9D9FB", odak="#2563EB",
        secim="#2563EB", secim_ton="#EEF3FE", secim_ton2="#C9D9FB",
        # durum renkleri (simge + metinle birlikte)
        ok="#2E7D4F", ok_ton="#E7F3EC", ok_kenar="#B9DCC6",
        uyari="#B7791F", uyari_ton="#FCF3E3", uyari_kenar="#EBCF9C",
        hata="#B4443A", hata_ton="#FBEAE8", hata_kenar="#E6B9B4",
        # gölge / karartma
        golge="#14181B", karartma="#0B0F14",
        # 3B görünüm zemini ve ızgara
        vp_ust="#FCFCFD", vp_alt="#E6E8EB", izgara="#D5D9DF", izgara2="#C2C7CF",
        eksen_x="#B4443A", eksen_y="#2E7D4F", eksen_z="#2F5FA8",
        # grafik serileri (doğrulayıcıdan geçti: CVD ΔE ≥ 9,2; seri3 düşük kontrast → kesik çizgi + doğrudan etiket)
        seri1="#2563EB", seri2="#EB6834", seri3="#1BAF7A",
        # temel kesiti çizimi
        beton="#E3E6EA", beton_kenar="#6B727C", zemin_tarama="#C8B99A",
    ),
}
PALET_SEC = "kobalt"
PALET = PALETLER[PALET_SEC]

BURASI = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/user/matris-ogren"
sys.path.insert(0, BURASI)
sys.path.insert(0, REPO)

import tuval as tv                                  # noqa: E402
from tuval import Tuval, taban, hex2rgb, rgba, yazi_tipi, logo_simge   # noqa: E402
from PIL import Image, ImageDraw, ImageFont, ImageFilter            # noqa: E402

tv.palet_kur(PALET)
C = tv.C

import yapi                    # noqa: E402  (hesap motoru: yalnız sayıları üretmek için)
import yapi_veri as yv         # noqa: E402

FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
_MONO = {}


def mono(boyut, s=1):
    k = (boyut, s)
    if k not in _MONO:
        _MONO[k] = ImageFont.truetype(FONT_MONO, int(round(boyut * s)))
    return _MONO[k]


# ============================================================================
# ÖRNEK PROJE (temsilî saha değerleri) ve motorla hesaplanan büyüklükler
# ============================================================================
ORN = dict(ad="Konut Bloğu A", il="Tokat", ilce="Merkez", enlem="40,31390", boylam="36,55440", rakim=623,
           kat=4, kat_h=3.0, SS=1.200, S1=0.350, SS3=0.450, S13=0.130, zemin="ZD", BKS=3,
           tasiyici="betonarme-cerceve-yuksek", beton="C30/37", donati="B420C",
           q_em=150, q_k=450, k0=18000, gamma_z=19.0)
HN = ORN["kat"] * ORN["kat_h"]
SP2 = yapi._spektrum(ORN["SS"], ORN["S1"], ORN["zemin"])
SP3 = yapi._spektrum(ORN["SS3"], ORN["S13"], ORN["zemin"])
DTS = yapi._dts(SP2["SDS"], ORN["BKS"])
BYS = yapi._bys(HN, DTS)
TS = yv.TBDY_TASIYICI[ORN["tasiyici"]]
R_, D_ = TS["R"], TS["D"]
I_ = yv.TBDY_BKS_I[ORN["BKS"]]["I"]
CT = yv.TBDY_CT["betonarme-cerceve"]
TPA = CT * HN ** 0.75
LAM = SP3["Sae"](TPA) / SP2["Sae"](TPA)
EDYY_ESIK = yv.TBDY_UYGULANABILIRLIK["duzenli"]["dts12" if DTS[0] in "12" else "dts34"]
AMPIRIK_YETER = (DTS[0] in "34") or (DTS[0] in "12" and BYS >= 6)
KAR_BOLGE = yv.kar_bolgesi(ORN["il"], ORN["ilce"])
KAR_SK, _ = yv.kar_Sk(KAR_BOLGE, ORN["rakim"])
KAR_S = 0.8 * KAR_SK
Q_T = ORN["q_k"] / 1.4
BETON = yv.BETONLAR[ORN["beton"]]
DONATI = yv.DONATILAR[ORN["donati"]]
KAPLAMA = yv.KAPLAMALAR["sap-seramik-siva"]
KAPLAMA_CATI = yv.KAPLAMALAR["cati-teras"]
DUVAR = yv.DUVARLAR["tugla-delikli-19"]


def _komb_say():
    from types import SimpleNamespace
    mevcut = {"G", "Q", "S", "W+X", "W-X", "W+Y", "W-Y", "EX+", "EX-", "EY+", "EY-", "EZ"}
    L = yapi._kombinasyon_listesi(SimpleNamespace(kombinasyon_kumesi="ts500"), mevcut)
    say = {}
    for k in L:
        if k["uygulandi"]:
            say[k["tur"]] = say.get(k["tur"], 0) + 1
    return say


KOMB = _komb_say()
KOMB_TOPLAM = sum(KOMB.values())


def sy(x, n=2, binlik=True):
    """Türkçe sayı: ondalık virgül, binlik ince boşluk."""
    s = f"{x:,.{n}f}" if binlik else f"{x:.{n}f}"
    return s.replace(",", " ").replace(".", ",")


# ============================================================================
# KÜÇÜK YARDIMCILAR
# ============================================================================
def sar(t, metin, w, boyut=11, agirlik=400):
    """Sözcük kaydırma (açgözlü)."""
    satirlar, s = [], ""
    for k in metin.split(" "):
        aday = (s + " " + k).strip()
        if t.yazi_gen(aday, boyut, agirlik) <= w or not s:
            s = aday
        else:
            satirlar.append(s)
            s = k
    if s:
        satirlar.append(s)
    return satirlar


def paragraf(t, x, y, metin, w, boyut=11, agirlik=400, renk=None, satir=16):
    for s in sar(t, metin, w, boyut, agirlik):
        t.yazi(x, y, s, boyut, agirlik, renk or C["metin2"])
        y += satir
    return y


def _parcala(metin):
    """'S_{DS}' gösterimi → [(metin, alt_mi)]."""
    out, i = [], 0
    while i < len(metin):
        j = metin.find("_{", i)
        if j < 0:
            out.append((metin[i:], False))
            break
        if j > i:
            out.append((metin[i:j], False))
        k = metin.index("}", j)
        out.append((metin[j + 2:k], True))
        i = k + 1
    return out


def alt_gen(t, metin, boyut=12, agirlik=400, tnum=False):
    w = 0.0
    for p, alt in _parcala(metin):
        w += t.yazi_gen(p, round(boyut * 0.74) if alt else boyut, agirlik, tnum) + (0.5 if alt else 0)
    return w


def alt_yazi(t, x, y, metin, boyut=12, agirlik=400, renk=None, tnum=False):
    """Alt simgeli yazı (taban çizgisi y). Genişliği döndürür."""
    renk = renk or C["metin"]
    x0 = x
    for p, alt in _parcala(metin):
        if alt:
            b = round(boyut * 0.74)
            t.yazi(x, y + boyut * 0.24, p, b, agirlik, renk, tnum=tnum)
            x += t.yazi_gen(p, b, agirlik, tnum) + 0.5
        else:
            t.yazi(x, y, p, boyut, agirlik, renk, tnum=tnum)
            x += t.yazi_gen(p, boyut, agirlik, tnum)
    return x - x0


def mono_yazi(t, x, y, metin, boyut=10, renk=None):
    f = mono(boyut, t.s)
    t.d.text((x * t.s, y * t.s), metin, font=f, fill=renk or C["kod_metin"], anchor="ls")


def mono_gen(t, metin, boyut=10):
    return mono(boyut, t.s).getlength(metin) / t.s


def ref_cip(t, xr, y, metin, h=18):
    """Sağa hizalı yönetmelik başvuru çipi: ⓘ + metin (ipucu açar)."""
    w = t.yazi_gen(metin, 10, 500) + 26
    x = xr - w
    t.dikdortgen(x, y, w, h, dolgu=C["yuzey2"], kenar=C["cizgi2"], r=h / 2)
    t.simge("bilgi", x + 10, y + h / 2, 11, C["metin3"], 1.4)
    t.yazi(x + 18, taban(y, h, 10), metin, 10, 500, C["metin2"])
    return w


def bilgi(t, cx, cy, renk=None):
    t.simge("bilgi", cx, cy, 13, renk or C["metin3"], 1.4)


def bolum(t, x, y, w, baslik, ref=None, simge=None):
    tx = x
    if simge:
        t.simge(simge, x + 8, y + 11, 15, C["metin2"], 1.4)
        tx = x + 22
    t.yazi(tx, taban(y, 22, 12), baslik, 12, 600, C["metin"])
    if ref:
        ref_cip(t, x + w, y + 2, ref)
    t.yatay(x, x + w, y + 26, C["cizgi2"])
    return y + 36


def etiket(t, x, y, metin, h=26, boyut=12, renk=None):
    alt_yazi(t, x, taban(y, h, boyut), metin, boyut, 400, renk or C["metin2"])


def birimli(t, x, y, w, deger, birim="", h=26, odak=False, durum=None, hiza="sag", renk=None, yer_tutucu=False):
    """Sayı/metin giriş kutusu; birim kutunun içinde sağda (soluk)."""
    kenar = C["vurgu"] if odak else (C["hata"] if durum == "hata" else (C["uyari"] if durum == "uyari" else C["giris_kenar"]))
    t.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=kenar, r=4, kalinlik=1.5 if odak else 1)
    if odak:
        t.dikdortgen(x - 2, y - 2, w + 4, h + 4, kenar=rgba(C["vurgu"], 0.22), r=6, kalinlik=2)
    bw = 0
    if birim:
        bw = alt_gen(t, birim, 11, 400) + 8
        alt_yazi(t, x + w - 8 - bw + 8, taban(y, h, 11), birim, 11, 400, C["metin3"])
    yr = renk or (C["metin3"] if yer_tutucu else C["metin"])
    if hiza == "sag":
        t.yazi_sag(x + w - 10 - bw, taban(y, h, 12), deger, 12, 400, yr, tnum=True)
        if odak:
            t.dikey(x + w - 8 - bw, y + 5, y + h - 5, C["vurgu"], 1)
    else:
        t.yazi(x + 9, taban(y, h, 12), deger, 12, 400, yr, tnum=True)
        if odak:
            t.dikey(x + 9 + t.yazi_gen(deger, 12, 400, True) + 2, y + 5, y + h - 5, C["vurgu"], 1)


def acilir(t, x, y, w, metin, h=26, salt=False, renk=None, on_simge=None):
    t.dikdortgen(x, y, w, h, dolgu=C["yuzey"] if not salt else C["yuzey2"], kenar=C["giris_kenar"] if not salt else C["cizgi2"], r=4)
    tx = x + 9
    if on_simge:
        t.simge(on_simge, x + 16, y + h / 2, 13, C["metin2"], 1.3)
        tx = x + 28
    t.yazi(tx, taban(y, h, 12), t.yazi_kes(metin, w - (tx - x) - 26, 12), 12, 400, renk or C["metin"])
    t.sevron(x + w - 13, y + h / 2 + 0.5, "asagi", 10, C["metin2"])


def dugme(t, x, y, w, metin, tur="ikincil", h=30, simge=None, simge_sag=None, pasif=False):
    if tur == "birincil":
        t.dikdortgen(x, y, w, h, dolgu=C["vurgu"], r=5)
        renk, agir = C["beyaz"], 600
    elif tur == "hayalet":
        renk, agir = (C["metin3"] if pasif else C["metin2"]), 500
    else:
        t.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["dugme_kenar"], r=5)
        renk, agir = (C["metin3"] if pasif else C["metin"]), 500
    tw = t.yazi_gen(metin, 12, agir) + (20 if simge else 0) + (16 if simge_sag else 0)
    x0 = x + (w - tw) / 2
    if simge:
        t.simge(simge, x0 + 7, y + h / 2, 14, renk, 1.5)
        x0 += 20
    t.yazi(x0, taban(y, h, 12), metin, 12, agir, renk)
    if simge_sag:
        t.simge(simge_sag, x0 + t.yazi_gen(metin, 12, agir) + 10, y + h / 2 + 0.5, 11, renk, 1.8)


def segment(t, x, y, secenekler, secili, h=26, boyut=11, min_w=0, pasifler=(), isaretli=()):
    ws = [max(min_w, t.yazi_gen(s, boyut, 600) + 22) for s in secenekler]
    toplam = sum(ws)
    t.dikdortgen(x, y, toplam, h, dolgu=C["yuzey"], kenar=C["giris_kenar"], r=5)
    xx = x
    for s, w_ in zip(secenekler, ws):
        if s == secili:
            t.dikdortgen(xx + 2, y + 2, w_ - 4, h - 4, dolgu=C["vurgu"], r=4)
            t.yazi_orta(xx + w_ / 2, taban(y, h, boyut), s, boyut, 600, C["beyaz"])
        else:
            t.yazi_orta(xx + w_ / 2, taban(y, h, boyut), s, boyut, 500, C["metin3"] if s in pasifler else C["metin2"])
        if s in isaretli:
            t.daire(xx + w_ - 7, y + 7, 2.6, dolgu=C["uyari"])
        xx += w_
        if xx < x + toplam - 1 and s != secili and secenekler[secenekler.index(s) + 1] != secili:
            t.dikey(xx, y + 6, y + h - 6, C["cizgi2"])
    return toplam


def cip(t, x, y, ad, deger, birim="", tur="notr", h=24, kaynak=None):
    """Hesaplanmış (salt okunur) değer çipi: 'ad = değer birim'. Genişliği döndürür."""
    renk_d = {"notr": C["metin"], "vurgu": C["vurgu_koyu"], "ok": C["ok"], "uyari": C["uyari"], "hata": C["hata"]}[tur]
    zem = {"notr": C["yuzey3"], "vurgu": C["vurgu_ton"], "ok": C["ok_ton"], "uyari": C["uyari_ton"], "hata": C["hata_ton"]}[tur]
    ken = {"notr": C["cizgi2"], "vurgu": C["vurgu_ton2"], "ok": C["ok_kenar"], "uyari": C["uyari_kenar"], "hata": C["hata_kenar"]}[tur]
    w_ad = alt_gen(t, ad, 11, 500)
    w_d = t.yazi_gen(deger, 12, 600, True)
    w_b = alt_gen(t, birim, 10, 400) + 4 if birim else 0
    w = 10 + w_ad + (t.yazi_gen(" = ", 11, 400) if deger else 0) + w_d + w_b + 10
    t.dikdortgen(x, y, w, h, dolgu=zem, kenar=ken, r=h / 2)
    xx = x + 10
    xx += alt_yazi(t, xx, taban(y, h, 11), ad, 11, 500, C["metin2"])
    if deger:
        t.yazi(xx, taban(y, h, 11), " = ", 11, 400, C["metin3"])
        xx += t.yazi_gen(" = ", 11, 400)
        t.yazi(xx, taban(y, h, 12), deger, 12, 600, renk_d, tnum=True)
        xx += w_d
    if birim:
        alt_yazi(t, xx + 4, taban(y, h, 10), birim, 10, 400, C["metin3"])
    return w


def etiket_cip(t, x, y, metin, tur="notr", h=18, boyut=10, simge=None):
    renk = {"notr": C["metin2"], "vurgu": C["vurgu_koyu"], "ok": C["ok"], "uyari": C["uyari"], "hata": C["hata"], "pasif": C["metin3"]}[tur]
    zem = {"notr": C["yuzey3"], "vurgu": C["vurgu_ton"], "ok": C["ok_ton"], "uyari": C["uyari_ton"], "hata": C["hata_ton"], "pasif": C["yuzey2"]}[tur]
    ken = {"notr": C["cizgi2"], "vurgu": C["vurgu_ton2"], "ok": C["ok_kenar"], "uyari": C["uyari_kenar"], "hata": C["hata_kenar"], "pasif": C["cizgi2"]}[tur]
    w = t.yazi_gen(metin, boyut, 600) + 14 + (14 if simge else 0)
    t.dikdortgen(x, y, w, h, dolgu=zem, kenar=ken, r=h / 2)
    xx = x + 7
    if simge:
        t.simge(simge, xx + 5, y + h / 2, 10, renk, 1.8)
        xx += 14
    t.yazi(xx, taban(y, h, boyut), metin, boyut, 600, renk)
    return w


def durum_ikon(t, cx, cy, durum, no, r=11):
    if durum == "etkin":
        t.daire(cx, cy, r + 3, dolgu=C["vurgu_ton2"])
        t.daire(cx, cy, r, dolgu=C["vurgu"])
        t.yazi_orta(cx, taban(cy - r, 2 * r, 11), str(no), 11, 700, C["beyaz"])
    elif durum == "tamam":
        t.daire(cx, cy, r, dolgu=C["ok"])
        t.simge("onay", cx, cy, 13, C["beyaz"], 2.0)
    elif durum == "uyari":
        t.daire(cx, cy, r, dolgu=C["uyari"])
        t.yazi_orta(cx, taban(cy - r, 2 * r, 12), "!", 12, 800, C["beyaz"])
    elif durum == "eksik":
        t.daire(cx, cy, r, dolgu=C["yuzey"], kenar=C["hata"], kalinlik=1.6)
        t.yazi_orta(cx, taban(cy - r, 2 * r, 12), "!", 12, 800, C["hata"])
    else:
        t.daire(cx, cy, r, dolgu=C["yuzey"], kenar=C["giris_kenar"], kalinlik=1.2)
        t.yazi_orta(cx, taban(cy - r, 2 * r, 11), str(no), 11, 600, C["metin3"])


def radyo(t, cx, cy, secili, r=7):
    t.daire(cx, cy, r, dolgu=C["yuzey"], kenar=C["vurgu"] if secili else C["onay_kenar"], kalinlik=1.4 if secili else 1)
    if secili:
        t.daire(cx, cy, r - 3.5, dolgu=C["vurgu"])


def anahtar(t, x, y, acik, w=30, h=16):
    if acik:
        t.dikdortgen(x, y, w, h, dolgu=C["vurgu"], r=h / 2)
        t.daire(x + w - h / 2, y + h / 2, h / 2 - 2.5, dolgu=C["beyaz"])
    else:
        t.dikdortgen(x, y, w, h, dolgu=C["giris_kenar"], r=h / 2)
        t.daire(x + h / 2, y + h / 2, h / 2 - 2.5, dolgu=C["beyaz"])


# ============================================================================
# ARKA PLAN: Atölye kabuğu (boş "Adsız 1" projesi) — sihirbazın arkasında karartılır
# ============================================================================
class Yer:
    W, H = 1920, 1080
    baslik_h, sekme_h, serit_h = 30, 26, 78
    ray_w, agac_w, ozel_w, strip_w = 36, 268, 320, 28
    gtab_h, dock_tab_h, dock_h, komut_h, durum_h = 22, 22, 40, 30, 26
    ust = 30 + 26 + 78
    alt = 1080 - 26 - 30 - 40 - 22
    vp_x0 = 36 + 268
    vp_x1 = 1920 - 28 - 320
    vp_y0 = ust + 22
    vp_y1 = alt


SEKMELER = ["Model", "Çizim", "Düzenle", "Seçim", "Yükler", "Mesnet ve Temel", "Analiz", "Sonuçlar", "Tasarım", "Rapor", "Görünüm", "Öğren", "Yardım"]
GRUPLAR = [
    ("Aks & Kat", [("aks", "Aks"), ("kat", "Kat")], [("izgara", "Aks sistemi…"), ("kat_verisi", "Kat verisi…"), ("duzlem", "Çalışma düzlemi")]),
    ("Kolon", [("kolon", "Kolon")], [("kolon", "Çelik"), ("kolon", "Betonarme"), ("kolon", "Kompozit")]),
    ("Kiriş", [("kiris", "Kiriş")], [("kiris_ana", "Ana kiriş"), ("kiris_tali", "Tali kiriş"), ("asik", "Aşık")]),
    ("Döşeme", [("doseme", "Döşeme")], [("doseme", "Betonarme"), ("doseme", "Kompozit"), ("doseme_bosluk", "Boşluk")]),
    ("Duvar", [("duvar", "Duvar")], [("duvar", "Perde"), ("duvar", "Dolgu"), ("doseme_bosluk", "Açıklık")]),
    ("Temel", [("temel", "Temel")], [("temel", "Tekil"), ("temel_surekli", "Sürekli"), ("temel_radye", "Radye")]),
    ("Proje", [("yonetmelik", "Yönetmelik")], [("sablon", "Yönetmelik şablonu…"), ("rapor", "Proje künyesi…"), ("kutuphane", "Kütüphane")]),
]


def kabuk(t, L, komut="YÖNETMELİK", son="Yönetmelik sihirbazı açıldı (yeni proje)"):
    W = L.W
    # başlık
    t.dikdortgen(0, 0, W, L.baslik_h, dolgu=C["zemin"])
    s = logo_simge()
    h = 16
    w = h * s.width / s.height
    t.resim(s, 12, (L.baslik_h - h) / 2, w=w, h=h)
    x = 12 + w + 7
    t.yazi(x, taban(0, L.baslik_h, 13), "op4", 13, 600, C["metin"])
    x += t.yazi_gen("op4", 13, 600) + 12
    t.dikey(x, 8, L.baslik_h - 8, C["cizgi"])
    x += 10
    for ad in ("yeni", "ac", "kaydet", None, "geri_al", "yinele", None, "coz"):
        if ad is None:
            t.dikey(x + 4, 8, L.baslik_h - 8, C["cizgi"]); x += 14; continue
        t.simge(ad, x + 11, L.baslik_h / 2, 15 if ad != "coz" else 12, C["simge2"], 1.4); x += 26
    ad = "Adsız 1"
    tw = t.yazi_gen(ad, 12, 500)
    t.yazi(W / 2 - tw / 2, taban(0, L.baslik_h, 12), ad, 12, 500, C["metin"])
    t.daire(W / 2 + tw / 2 + 10, L.baslik_h / 2, 3, dolgu=C["vurgu"])
    t.yazi(W / 2 + tw / 2 + 18, taban(0, L.baslik_h, 11), "kaydedilmedi", 11, 400, C["metin3"])
    t.yazi_sag(W - 46 * 3 - 18, taban(0, L.baslik_h, 11), "Opus Fortis · Proje Mühendisi", 11, 400, C["metin3"])
    for i, ad in enumerate(("kucult", "buyut", "kapat")):
        t.simge(ad, W - 46 * (3 - i) + 23, L.baslik_h / 2, 13, C["simge2"], 1.2)
    # şerit
    y0 = L.baslik_h
    t.dikdortgen(0, y0, W, L.sekme_h, dolgu=C["zemin"])
    x = 8
    t.dikdortgen(x, y0 + 4, 58, L.sekme_h - 4, dolgu=C["vurgu"])
    t.yazi_orta(x + 29, taban(y0 + 4, L.sekme_h - 4, 12), "Dosya", 12, 600, C["beyaz"])
    x += 64
    govde = y0 + L.sekme_h
    for ad in SEKMELER:
        w = t.yazi_gen(ad, 12, 500) + 22
        if ad == "Model":
            t.dikdortgen(x, y0 + 4, w, L.sekme_h - 3, dolgu=C["yuzey"])
            t.dikey(x, y0 + 4, govde + 1, C["cizgi"]); t.dikey(x + w - 1, y0 + 4, govde + 1, C["cizgi"])
            t.yatay(x, x + w, y0 + 4, C["vurgu"], 2)
            t.yazi(x + 11, taban(y0 + 4, L.sekme_h - 4, 12), ad, 12, 600, C["metin"])
        else:
            t.yazi(x + 11, taban(y0 + 4, L.sekme_h - 4, 12), ad, 12, 500, C["metin2"])
        x += w
    t.dikdortgen(0, govde, W, L.serit_h, dolgu=C["yuzey"])
    t.yatay(0, W, govde, C["cizgi"]); t.yatay(0, W, govde + L.serit_h - 1, C["cizgi"])
    x = 8
    for gad, buyuk, kucuk in GRUPLAR:
        gx0 = x
        x += 6
        for ik, et in buyuk:
            bw = max(48, t.yazi_gen(et, 11, 500) + 16)
            bas = ik == "yonetmelik"
            if bas:
                t.dikdortgen(x, govde + 5, bw, 54, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=3)
            t.simge(ik, x + bw / 2, govde + 22, 24, C["vurgu"] if bas else C["simge"], 1.5)
            t.yazi_orta(x + bw / 2, govde + 50, et, 11, 600 if bas else 500, C["metin"])
            x += bw + 2
        kw = max(t.yazi_gen(et, 11, 400) for _, et in kucuk) + 26
        for j, (ik, et) in enumerate(kucuk):
            yy = govde + 6 + j * 18
            t.simge(ik, x + 10, yy + 8, 14, C["simge2"], 1.4)
            t.yazi(x + 22, taban(yy, 16, 11), et, 11, 400, C["metin"])
        x += kw + 6
        t.yazi_orta(gx0 + (x - gx0) / 2, govde + 71, gad, 10, 400, C["metin3"])
        t.dikey(x, govde + 8, govde + L.serit_h - 8, C["cizgi2"])
        x += 1
    # sol ray
    t.dikdortgen(0, L.ust, L.ray_w, L.H - L.durum_h - L.ust, dolgu=C["zemin"])
    t.dikey(L.ray_w - 1, L.ust, L.H - L.durum_h, C["cizgi"])
    yy = L.ust + 6
    t.yazi_orta(L.ray_w / 2, yy + 8, "ÇİZ", 8, 600, C["metin3"]); yy += 12
    for ik in ("sec", "kolon", "kiris", "capraz", "doseme", "duvar", "temel", "aks", "yuk", "mesnet", "olcu"):
        if ik == "sec":
            t.dikdortgen(5, yy, 26, 26, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=3)
            t.dikey(0, yy + 4, yy + 22, C["vurgu"], 2)
        t.simge(ik, 18, yy + 13, 16, C["vurgu"] if ik == "sec" else C["simge2"], 1.5)
        yy += 28
    # model ağacı (boş proje)
    x0, y0, w, h = L.ray_w, L.ust, L.agac_w, L.alt - L.ust
    t.dikdortgen(x0, y0, w, h, dolgu=C["yuzey"])
    t.dikey(x0 + w - 1, y0, y0 + h, C["cizgi"])
    t.dikdortgen(x0, y0, w, 28, dolgu=C["yuzey2"]); t.yatay(x0, x0 + w, y0 + 27, C["cizgi2"])
    t.yazi(x0 + 10, taban(y0, 28, 12), "Model ağacı", 12, 600, C["metin"])
    yy = y0 + 64
    for derin, ik, metin, sag in ((0, "proje", "Adsız 1", ""), (1, "yonetmelik", "Yönetmelik verileri", "tanımlanıyor"),
                                  (1, "aks", "Aks sistemi", "—"), (1, "kat", "Katlar", "1"), (2, "kat", "Zemin", "±0,00"),
                                  (1, "kesit", "Kesitler", "0"), (1, "malzeme", "Malzemeler", "0"), (1, "yuk", "Yük desenleri", "2"),
                                  (1, "tablo", "Kombinasyonlar", "0")):
        ix = x0 + 10 + derin * 14
        t.simge(ik, ix + 20, yy + 10, 13, C["metin2"], 1.3)
        t.yazi(ix + 30, taban(yy, 20, 12), metin, 12, 600 if derin == 0 else 400, C["metin"])
        if sag:
            t.yazi_sag(x0 + w - 12, taban(yy, 20, 11), sag, 11, 400, C["metin3"])
        yy += 20
    # görünüm sekmeleri + boş görünüm (Z = 0 ızgarası)
    t.dikdortgen(L.vp_x0, L.ust, L.vp_x1 - L.vp_x0, L.gtab_h, dolgu=C["zemin"])
    t.yatay(L.vp_x0, L.vp_x1, L.ust + L.gtab_h - 1, C["cizgi"])
    tw = t.yazi_gen("3B görünüm", 11, 600) + 22
    t.dikdortgen(L.vp_x0 + 6, L.ust + 3, tw, L.gtab_h - 3, dolgu=C["yuzey"], kenar=C["cizgi"])
    t.yazi(L.vp_x0 + 17, taban(L.ust + 3, L.gtab_h - 3, 11), "3B görünüm", 11, 600, C["metin"])
    bos_gorunum(t, L)
    # özellikler (seçim yok)
    x0 = L.vp_x1
    t.dikdortgen(x0, L.ust, L.ozel_w, L.alt - L.ust, dolgu=C["yuzey"])
    t.dikey(x0, L.ust, L.alt, C["cizgi"])
    t.dikdortgen(x0 + 1, L.ust, L.ozel_w - 1, 28, dolgu=C["yuzey2"]); t.yatay(x0, x0 + L.ozel_w, L.ust + 27, C["cizgi2"])
    t.yazi(x0 + 12, taban(L.ust, 28, 12), "Özellikler", 12, 600, C["metin"])
    t.yazi(x0 + 12, L.ust + 60, "Seçim yok — proje özellikleri", 12, 400, C["metin3"])
    # pencere şeridi
    xs = L.W - L.strip_w
    t.dikdortgen(xs, L.ust, L.strip_w, L.alt - L.ust, dolgu=C["zemin"]); t.dikey(xs, L.ust, L.alt, C["cizgi"])
    yy = L.ust + 8
    for ik, ad in (("etiket", "Özellikler"), ("kutuphane", "Kataloglar"), ("katman", "Model ağacı"), ("suz", "Filtre & görünürlük")):
        th = t.yazi_gen(ad, 11, 500) + 34
        t.simge(ik, xs + L.strip_w / 2, yy + 12, 14, C["metin2"], 1.4)
        t.yazi_dikey(xs + L.strip_w / 2 - 8, yy + 24, ad, 11, 500, C["metin2"])
        yy += th + 6
    # rıhtım + komut satırı + durum çubuğu
    y0 = L.alt
    t.dikdortgen(L.ray_w, y0, W - L.ray_w, L.dock_tab_h, dolgu=C["zemin"]); t.yatay(L.ray_w, W, y0, C["cizgi"])
    xx = L.ray_w + 10
    for ad in ("Komut", "Mesajlar", "Tablolar"):
        tw = t.yazi_gen(ad, 11, 500)
        if ad == "Komut":
            t.yazi(xx, taban(y0, L.dock_tab_h, 11), ad, 11, 600, C["metin"]); t.yatay(xx - 2, xx + tw + 2, y0 + L.dock_tab_h - 2, C["vurgu"], 2)
        else:
            t.yazi(xx, taban(y0, L.dock_tab_h, 11), ad, 11, 500, C["metin2"])
        xx += tw + 24
    cy = y0 + L.dock_tab_h
    t.dikdortgen(L.ray_w, cy, W - L.ray_w, L.dock_h, dolgu=C["yuzey"])
    t.yazi(L.ray_w + 12, taban(cy + 2, 18, 11), "›", 11, 600, C["metin3"])
    t.yazi(L.ray_w + 24, taban(cy + 2, 18, 11), "YENİ", 11, 600, C["vurgu"])
    t.yazi(L.ray_w + 60, taban(cy + 2, 18, 11), "Boş model “Adsız 1” oluşturuldu", 11, 400, C["metin2"])
    t.yazi(L.ray_w + 12, taban(cy + 20, 18, 11), "›", 11, 600, C["metin3"])
    t.yazi(L.ray_w + 24, taban(cy + 20, 18, 11), komut, 11, 600, C["vurgu"])
    t.yazi(L.ray_w + 32 + t.yazi_gen(komut, 11, 600), taban(cy + 20, 18, 11), son, 11, 400, C["metin2"])
    y0 = cy + L.dock_h
    t.dikdortgen(L.ray_w, y0, W - L.ray_w, L.komut_h, dolgu=C["yuzey"])
    t.yatay(L.ray_w, W, y0, C["cizgi"]); t.yatay(L.ray_w, W, y0 + L.komut_h - 1, C["cizgi"])
    t.dikey(L.ray_w, y0, y0 + L.komut_h, C["vurgu"], 3)
    t.yazi(L.ray_w + 14, taban(y0, L.komut_h, 12), "Komut:", 12, 600, C["vurgu"])
    t.dikey(L.ray_w + 68, y0 + 8, y0 + L.komut_h - 8, C["metin"], 1)
    t.yazi(L.ray_w + 82, taban(y0, L.komut_h, 12), "· Son: " + son, 12, 400, C["metin3"])
    y0 = L.H - L.durum_h
    t.dikdortgen(0, y0, W, L.durum_h, dolgu=C["zemin"]); t.yatay(0, W, y0, C["cizgi"])
    t.simge("sevron_sag", 12, y0 + L.durum_h / 2, 10, C["vurgu"], 1.8)
    t.yazi(22, taban(y0, L.durum_h, 11), "Yönetmelik sihirbazı — adımları sırayla tamamlayın · Esc: kapat", 11, 500, C["metin"])
    t.yazi_sag(W - 12, taban(y0, L.durum_h, 11), "X 0,000   Y 0,000   Z 0,000", 11, 400, C["metin2"], tnum=True)
    w_ = etiket_cip(t, 0, -100, "Yönetmelik: tanımlanmadı", "pasif")   # ölçüm için ekran dışı
    etiket_cip(t, W - 220 - w_, y0 + 4, "Yönetmelik: tanımlanmadı", "pasif", h=18, simge="yonetmelik")


def bos_gorunum(t, L):
    x0, y0, w, h = L.vp_x0, L.vp_y0, L.vp_x1 - L.vp_x0, L.vp_y1 - L.vp_y0
    t.gradyan(x0, y0, w, h, C["vp_ust"], C["vp_alt"])
    # perspektif Z = 0 ızgarası (basit iğne deliği kamerası)
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    yaw, pitch, dist, f = math.radians(-35), math.radians(28), 46.0, 900.0

    def proj(X, Y, Z=0.0):
        xr = X * math.cos(yaw) - Y * math.sin(yaw)
        yr = X * math.sin(yaw) + Y * math.cos(yaw)
        yc = yr * math.cos(pitch) - Z * math.sin(pitch)
        zc = yr * math.sin(pitch) + Z * math.cos(pitch)
        depth = dist + yc
        return (w / 2 + f * xr / depth) * S, (h * 0.52 - f * zc / depth) * S

    n = 24
    for i in range(-n, n + 1):
        ana = i % 5 == 0
        renk = rgba(C["izgara2"] if ana else C["izgara"], 0.9 if ana else 0.7)
        for a, b in (((i, -n), (i, n)), ((-n, i), (n, i))):
            p, q = proj(*a), proj(*b)
            d.line([p, q], fill=renk, width=S if ana else max(1, S - 1))
    o = proj(0, 0)
    for v, renk in (((4, 0, 0), C["eksen_x"]), ((0, 4, 0), C["eksen_y"]), ((0, 0, 4), C["eksen_z"])):
        d.line([o, proj(*v)], fill=hex2rgb(renk) + (255,), width=2 * S)
    im = im.resize((w * t.s, h * t.s), Image.LANCZOS)
    t.img.paste(im, (t.p(x0), t.p(y0)), im)
    t._yenile()


# ============================================================================
# SİHİRBAZ ÇERÇEVESİ
# ============================================================================
MW, MH = 1600, 944
MX, MY = (1920 - MW) // 2, (1080 - MH) // 2
HDR, FTR = 56, 60
STEP_W, RAIL_W = 272, 344
BODY_Y = MY + HDR
BODY_Y1 = MY + MH - FTR
MAIN_X = MX + STEP_W
RAIL_X = MX + MW - RAIL_W
CX = MAIN_X + 28                 # içerik sol
CW = RAIL_X - 28 - CX            # içerik genişliği (928)
SOL_W = 448
SAG_X = CX + SOL_W + 24
SAG_W = CX + CW - SAG_X

ADIMLAR = [
    (1, "Proje ve yapı türü", "Künye · sistem · yönetmelikler"),
    (2, "Malzemeler", "TS 500 · ÇYTHYE 2018"),
    (3, "Yükler", "TS 498:2021"),
    (4, "Deprem", "TBDY 2018 Bölüm 2–4"),
    (5, "Zemin ve temel", "TBDY 16 · TS 500 md. 10"),
    (6, "Yük birleşimleri", "TS 500 · ÇYTHYE · TBDY 4.4.4"),
    (7, "Analiz seçenekleri", "TBDY 4.5.8 · motor ayarları"),
    (8, "Özet ve onay", "Projeyi oluştur"),
]


def cerceve(t, adim, durumlar, altlar, sablon="Opus Fortis — betonarme konut (varsayılan)"):
    """Modal pencere: başlık, adım çubuğu, gövde zemini, sağ ray zemini, alt çubuk zemini."""
    t.karart(0, 0, 1920, 1080, 0.42)
    t.golge(MX, MY, MW, MH, r=8, yaricap=18, alfa=0.38, dy=10)
    t.dikdortgen(MX, MY, MW, MH, dolgu=C["yuzey"], kenar=C["pencere_kenar"], r=8)
    # başlık
    t.yatay(MX + 1, MX + MW - 1, MY + HDR - 1, C["cizgi"])
    t.dikdortgen(MX + 16, MY + 12, 32, 32, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=7)
    t.simge("yonetmelik", MX + 32, MY + 28, 19, C["vurgu"], 1.6)
    t.yazi(MX + 60, MY + 26, "Yönetmelik Sihirbazı", 15, 600, C["metin"])
    t.yazi(MX + 60, MY + 43, "Adsız 1 · yeni proje — analiz için gereken dış veriler, yönetmelik sırasıyla", 11, 400, C["metin3"])
    xr = MX + MW - 16
    t.simge("kapat", xr - 12, MY + HDR / 2, 14, C["metin2"], 1.4)
    xr -= 36
    dugme(t, xr - 168, MY + 13, 168, "Şablon olarak kaydet…", simge="kaydet", h=30)
    xr -= 180
    acilir(t, xr - 330, MY + 13, 330, sablon, h=30, on_simge="sablon")
    t.yazi_sag(xr - 340, taban(MY + 13, 30, 11), "Yönetmelik şablonu", 11, 500, C["metin2"])
    # adım çubuğu
    t.dikdortgen(MX + 1, BODY_Y, STEP_W - 1, BODY_Y1 - BODY_Y, dolgu=C["yuzey2"])
    t.dikey(MX + STEP_W - 1, BODY_Y, BODY_Y1, C["cizgi"])
    adim_cubugu(t, adim, durumlar, altlar)
    # sağ ray
    t.dikdortgen(RAIL_X, BODY_Y, RAIL_W - 1, BODY_Y1 - BODY_Y, dolgu=C["yuzey2"])
    t.dikey(RAIL_X, BODY_Y, BODY_Y1, C["cizgi"])
    # alt çubuk zemini
    t.dikdortgen(MX + 1, BODY_Y1, MW - 2, FTR - 1, dolgu=C["yuzey"], r=0)
    t.yatay(MX + 1, MX + MW - 1, BODY_Y1, C["cizgi"])
    t.dikdortgen(MX, MY, MW, MH, kenar=C["pencere_kenar"], r=8)


def adim_cubugu(t, adim, durumlar, altlar):
    x0 = MX
    y = BODY_Y + 18
    t.yazi(x0 + 20, y + 8, "YÖNETMELİK SIRASI", 10, 600, C["metin3"])
    y += 22
    rh = 62
    cx = x0 + 34
    merkez = []
    for (no, baslik, kod), durum, alt in zip(ADIMLAR, durumlar, altlar):
        merkez.append((y + 22, durum))
        y += rh
    # bağlantı çizgileri
    for i in range(len(merkez) - 1):
        (y1, d1), (y2, d2) = merkez[i], merkez[i + 1]
        renk = C["ok"] if d1 in ("tamam", "uyari") and d2 in ("tamam", "uyari", "etkin") else C["cizgi"]
        t.dikey(cx - 1, y1 + 14, y2 - 14, renk, 2)
    y = BODY_Y + 40
    for (no, baslik, kod), durum, alt in zip(ADIMLAR, durumlar, altlar):
        if no == adim:
            t.dikdortgen(x0 + 10, y + 2, STEP_W - 20, rh - 6, dolgu=C["yuzey"], kenar=C["vurgu_ton2"], r=7)
            t.dikdortgen(x0 + 10, y + 12, 3, rh - 26, dolgu=C["vurgu"], r=1.5)
        durum_ikon(t, cx, y + 22, durum, no)
        renk_b = C["vurgu_koyu"] if no == adim else (C["metin"] if durum != "bekliyor" else C["metin2"])
        t.yazi(x0 + 58, y + 20, baslik, 12, 600, renk_b)
        t.yazi(x0 + 58, y + 36, t.yazi_kes(kod, STEP_W - 76, 10), 10, 500, C["metin3"])
        alt_metin, alt_tur = alt
        renk_a = {"uyari": C["uyari"], "eksik": C["hata"], "tamam": C["metin2"], "bekliyor": C["metin3"]}.get(alt_tur, C["metin2"])
        alt_yazi(t, x0 + 58, y + 51, t.yazi_kes(alt_metin, STEP_W - 76, 11) if "_{" not in alt_metin else alt_metin, 11, 400, renk_a)
        y += rh
    # alt: ilerleme, açıklama
    yb = BODY_Y1 - 150
    t.yatay(x0 + 18, x0 + STEP_W - 18, yb, C["cizgi"])
    tamam = sum(1 for d in durumlar if d in ("tamam", "uyari"))
    uy = sum(1 for d in durumlar if d == "uyari")
    t.yazi(x0 + 20, yb + 24, f"{tamam} / 8 adım tamam", 12, 600, C["metin"])
    if uy:
        t.yazi_sag(x0 + STEP_W - 20, yb + 24, f"{uy} uyarı", 11, 600, C["uyari"])
    t.dikdortgen(x0 + 20, yb + 34, STEP_W - 40, 6, dolgu=C["cizgi2"], r=3)
    t.dikdortgen(x0 + 20, yb + 34, (STEP_W - 40) * tamam / 8, 6, dolgu=C["ok"], r=3)
    yy = yb + 58
    for d, et in (("tamam", "Tamam"), ("uyari", "Uyarı"), ("eksik", "Eksik"), ("bekliyor", "Bekliyor")):
        pass
    xx = x0 + 20
    for d, et in (("tamam", "Tamam"), ("uyari", "Uyarı"), ("eksik", "Eksik"), ("bekliyor", "Varsayılan")):
        durum_ikon(t, xx + 6, yy, d, "", r=6)
        t.yazi(xx + 16, yy + 4, et, 10, 500, C["metin2"])
        xx += t.yazi_gen(et, 10, 500) + 28
    paragraf(t, x0 + 20, yy + 30, "Değerler hesap motorunun kütüphanesinden gelir; “doğrulanmamış” kayıt kullanılırsa adım uyarı alır.",
             STEP_W - 40, 10, 400, C["metin3"], 14)


def ana_baslik(t, adim, baslik, aciklama, refler=()):
    y = BODY_Y + 22
    t.yazi(CX, y + 9, "ADIM", 10, 700, C["vurgu"])
    t.yazi(CX + t.yazi_gen("ADIM", 10, 700) + 5, y + 9, f"{adim} / 8", 10, 700, C["vurgu"], tnum=True)
    t.yazi(CX, y + 34, baslik, 18, 600, C["metin"])
    xr = CX + CW
    for r in reversed(refler):
        w = etiket_cip(t, -400, -400, r)
        etiket_cip(t, xr - w, y + 18, r, "notr", h=20, boyut=10)
        xr -= w + 6
    son = paragraf(t, CX, y + 56, aciklama, CW - 20, 12, 400, C["metin2"], 17) - 17
    t.yatay(CX, CX + CW, son + 14, C["cizgi"])
    return son + 30


def alt_cubuk(t, sol, dugmeler):
    y = BODY_Y1 + 15
    x = MX + 20
    t.simge("sifirla", x + 7, y + 15, 14, C["vurgu"], 1.5)
    t.yazi(x + 20, taban(y, 30, 12), sol, 12, 500, C["vurgu"])
    x += 28 + t.yazi_gen(sol, 12, 500)
    t.yazi(x, taban(y, 30, 11), "Alt+→ İleri · Alt+← Geri · Esc kapat", 11, 400, C["metin3"])
    xr = MX + MW - 20
    for metin, tur, w, simge, simge_sag, pasif in reversed(dugmeler):
        dugme(t, xr - w, y, w, metin, tur, h=30, simge=simge, simge_sag=simge_sag, pasif=pasif)
        xr -= w + 10


def ray_baslik(t, baslik="Bu adımın etkisi"):
    x, y = RAIL_X + 20, BODY_Y + 20
    t.dikdortgen(x, y, 26, 26, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=6)
    t.simge("bilgi", x + 13, y + 13, 15, C["vurgu"], 1.5)
    t.yazi(x + 36, y + 18, baslik, 13, 600, C["metin"])
    return y + 44


def ray_etiket(t, y, metin):
    t.yazi(RAIL_X + 20, y + 10, metin, 10, 700, C["metin3"])
    return y + 18


def kod_blogu(t, y, satirlar, boyut=10, satir=16):
    x, w = RAIL_X + 20, RAIL_W - 40
    h = len(satirlar) * satir + 12
    t.dikdortgen(x, y, w, h, dolgu=C["kod_zemin"], kenar=C["kod_kenar"], r=5)
    yy = y + 6 + satir - 4
    for s in satirlar:
        if isinstance(s, tuple):
            anahtar_, deger = s
            mono_yazi(t, x + 10, yy, anahtar_, boyut, C["metin2"])
            mono_yazi(t, x + 10 + mono_gen(t, anahtar_, boyut), yy, deger, boyut, C["kod_metin"])
        else:
            mono_yazi(t, x + 10, yy, s, boyut, C["metin3"])
        yy += satir
    return y + h + 12


def ray_madde(t, y, metin, simge="sevron_sag", renk_s=None, w=None, boyut=11):
    x = RAIL_X + 20
    w = w or RAIL_W - 40
    t.simge(simge, x + 6, y - 4, 10 if simge == "sevron_sag" else 13, renk_s or C["metin3"], 1.6 if simge == "sevron_sag" else 1.4)
    satirlar = sar(t, metin, w - 18, boyut)
    for s in satirlar:
        alt_yazi(t, x + 18, y, s, boyut, 400, C["metin2"])
        y += 15
    return y + 5


# ============================================================================
# SPEKTRUM GRAFİĞİ (4× örneklemeli ayrı tuvalde çizilir, sonra küçültülür)
# ============================================================================
def spektrum_grafik(t, x, y, w, h):
    S = 4
    g = Tuval(w, h, S, zemin=C["yuzey"])
    sol, sag, ust, alt = 42, 16, 30, 28
    pw, ph = w - sol - sag, h - ust - alt
    Tmax, Smax = 3.0, 1.4

    def px(T):
        return sol + pw * T / Tmax

    def py(v):
        return ust + ph * (1 - v / Smax)

    # ızgara + eksenler (çekingen)
    for k in range(0, 8):
        v = k * 0.2
        g.yatay(sol, sol + pw, py(v), C["cizgi2"] if k else C["cizgi"], 1)
        if k % 2 == 0:
            g.yazi_sag(sol - 6, py(v) + 3.5, sy(v, 1), 10, 400, C["metin3"], tnum=True)
    for k in range(0, 7):
        T = k * 0.5
        g.dikey(px(T), ust + ph, ust + ph + 4, C["cizgi"])
        g.yazi_orta(px(T), ust + ph + 16, sy(T, 1), 10, 400, C["metin3"], tnum=True)
    alt_yazi(g, 4, ust - 10, "S_{a}(T)  [g]", 10, 500, C["metin2"])
    g.yazi_sag(sol + pw, ust + ph + 26, "T  [s]", 10, 500, C["metin2"])
    # köşe periyotları
    for T, ad in ((SP2["TA"], "T_{A}"), (SP2["TB"], "T_{B}")):
        yy = ust
        while yy < ust + ph:
            g.dikey(px(T), yy, min(yy + 3, ust + ph), C["metin3"], 1)
            yy += 6
        alt_yazi(g, px(T) + 3, ust - 4 if ad == "T_{B}" else ust + 10, ad, 10, 500, C["metin2"])

    def egri(f, renk, kal, kesik=False):
        Ts = [i * Tmax / 600 for i in range(601)]
        pts = [(px(T), py(min(f(T), Smax))) for T in Ts]
        if not kesik:
            g.d.line([(a * S, b * S) for a, b in pts], fill=renk, width=int(kal * S), joint="curve")
        else:
            seg, uz, acik = [], 0.0, True
            for i in range(1, len(pts)):
                (a1, b1), (a2, b2) = pts[i - 1], pts[i]
                L = math.hypot(a2 - a1, b2 - b1)
                if acik:
                    g.d.line([(a1 * S, b1 * S), (a2 * S, b2 * S)], fill=renk, width=int(kal * S))
                uz += L
                if uz > (6 if acik else 4):
                    acik, uz = not acik, 0.0

    def Ra(T):
        return R_ / I_ if T > SP2["TB"] else D_ + (R_ / I_ - D_) * T / SP2["TB"]

    egri(SP3["Sae"], C["seri3"], 1.6, kesik=True)
    egri(SP2["Sae"], C["seri1"], 2.0)
    egri(lambda T: SP2["Sae"](T) / Ra(T), C["seri2"], 2.0)
    # T_pA işareti
    xT = px(TPA)
    yy = ust
    while yy < ust + ph:
        g.dikey(xT, yy, min(yy + 2, ust + ph), C["metin2"], 1)
        yy += 4
    for v, renk in ((SP2["Sae"](TPA), C["seri1"]), (SP2["Sae"](TPA) / Ra(TPA), C["seri2"])):
        g.daire(xT, py(v), 4.5, dolgu=C["yuzey"], kenar=renk, kalinlik=2)
    et = f"T_{{pA}} ≈ {sy(TPA, 3)} s"
    ew = alt_gen(g, et, 10, 600) + 12
    g.dikdortgen(xT + 8, py(SP2["Sae"](TPA)) - 26, ew, 18, dolgu=C["yuzey"], kenar=C["cizgi"], r=3)
    alt_yazi(g, xT + 14, py(SP2["Sae"](TPA)) - 13, et, 10, 600, C["metin"])
    # doğrudan etiketler (metin rengi metin belirteçlerinden; çizgi örneği seri rengi)
    for T, f, ad, dy in ((1.55, SP2["Sae"], "DD-2 · S_{ae}", -8), (0.17, lambda T: SP3["Sae"](SP3["TB"] * 0.9), "DD-3 · S_{ae}", -8),
                         (0.80, lambda T: SP2["Sae"](T) / Ra(T), "S_{aR}", -7)):
        v = f(T)
        alt_yazi(g, px(T) + 4, py(v) + dy, ad, 10, 500, C["metin2"])
    # lejant (üst sağ)
    lx = sol + pw
    for ad, renk, kesik in reversed((("DD-2 elastik", C["seri1"], False), ("S_{aR} = S_{ae}/R_{a}", C["seri2"], False), ("DD-3 elastik", C["seri3"], True))):
        tw = alt_gen(g, ad, 10, 500)
        lx -= tw
        alt_yazi(g, lx, 13, ad, 10, 500, C["metin2"])
        lx -= 22
        if kesik:
            for k in range(3):
                g.yatay(lx + k * 6, lx + k * 6 + 4, 9, renk, 2)
        else:
            g.yatay(lx, lx + 16, 9, renk, 2)
        lx -= 14
    im = g.img.resize((w * t.s, h * t.s), Image.LANCZOS)
    t.img.paste(im, (t.p(x), t.p(y)))
    t._yenile()
    t.dikdortgen(x, y, w, h, kenar=C["cizgi2"], r=4)


# ============================================================================
# ADIM 1 — Proje ve yapı türü
# ============================================================================
def adim1(t):
    durumlar = ["etkin", "bekliyor", "bekliyor", "eksik", "bekliyor", "bekliyor", "bekliyor", "bekliyor"]
    altlar = [("Konut Bloğu A · Betonarme", "tamam"), ("C30/37 · B420C (şablon)", "bekliyor"), ("Konut · tuğla 19 · kar açık (şablon)", "bekliyor"),
              ("S_{S}, S_{1} girilmedi", "eksik"), ("Tekil · q_{em} 200 (şablon)", "bekliyor"), ("TS 500 + TBDY 4.4.4 (öneri)", "bekliyor"),
              ("Çatlamış kesit · rijit diyafram", "bekliyor"), ("Gözden geçirilmedi", "bekliyor")]
    cerceve(t, 1, durumlar, altlar)
    y = ana_baslik(t, 1, "Proje ve yapı türü",
                   "Proje künyesi rapor kapağına, il / ilçe ve rakım kar yüküne gider. Yapı türü hangi tasarım yönetmeliklerinin uygulanacağını ve sonraki adımlardaki seçenekleri belirler.",
                   ("Rapor künyesi", "TS 498 Ek 1"))
    # --- künye
    y = bolum(t, CX, y, CW, "Proje künyesi", "rapor kapağı · kar bölgesi (TS 498:2021 Ek 1)", "proje")
    lw = 132
    iw = SOL_W - lw
    iw2 = SAG_W - lw
    etiket(t, CX, y, "Proje adı")
    birimli(t, CX + lw, y, CW - lw, ORN["ad"], hiza="sol", odak=True)
    y += 36
    etiket(t, CX, y, "İl")
    acilir(t, CX + lw, y, iw, ORN["il"])
    etiket(t, SAG_X, y, "İlçe")
    acilir(t, SAG_X + lw, y, iw2, ORN["ilce"])
    y += 36
    etiket(t, CX, y, "Ada / parsel")
    birimli(t, CX + lw, y, iw / 2 - 4, "1124", hiza="sol")
    birimli(t, CX + lw + iw / 2 + 4, y, iw / 2 - 4, "7", hiza="sol")
    etiket(t, SAG_X, y, "Yapı sahibi")
    birimli(t, SAG_X + lw, y, iw2, "isteğe bağlı", hiza="sol", yer_tutucu=True)
    y += 36
    etiket(t, CX, y, "Enlem")
    birimli(t, CX + lw, y, iw, ORN["enlem"], "° K")
    etiket(t, SAG_X, y, "Boylam")
    birimli(t, SAG_X + lw, y, iw2 - 150, ORN["boylam"], "° D")
    dugme(t, SAG_X + lw + iw2 - 142, y, 142, "Panodan yapıştır", simge="yapistir", h=26)
    y += 36
    etiket(t, CX, y, "Rakım")
    birimli(t, CX + lw, y, 120, f"{ORN['rakim']}", "m")
    alt_yazi(t, CX + lw + 132, taban(y, 26, 11), "→ kar yükü S_{k} (Adım 3)", 11, 400, C["metin3"])
    etiket(t, SAG_X, y, "Tarih")
    birimli(t, SAG_X + lw, y, iw2, "31.10.2026", hiza="sol")
    t.simge("takvim", SAG_X + lw + iw2 - 16, y + 13, 14, C["metin2"], 1.4)
    y += 36
    etiket(t, CX, y, "Hazırlayan")
    birimli(t, CX + lw, y, iw, "Ayşe Kaya, İnş. Müh.", hiza="sol")
    etiket(t, SAG_X, y, "Kontrol eden")
    birimli(t, SAG_X + lw, y, iw2, "isteğe bağlı", hiza="sol", yer_tutucu=True)
    y += 46
    # --- yapı türü
    y = bolum(t, CX, y, CW, "Yapı türü", "tasarım yönetmeliklerini belirler", "bina")
    kw = (CW - 32) / 3
    kartlar = [("kolon", "Betonarme", ["TS 500:2000 (+T1/T2/T3)", "TBDY 2018 Bölüm 7", "Beton + donatı çeliği"], True, None),
               ("kesit", "Çelik", ["ÇYTHYE 2018 (YDKT / GKT)", "TBDY 2018 Bölüm 9", "Yapı çeliği (S235–S355)"], False, None),
               ("malzeme", "Karma", ["Ana taşıyıcı sistem seçilir", "Eleman, kendi malzemesinin", "yönetmeliğiyle tahkik edilir"], False, "kısıtlı")]
    for i, (ik, ad, satirlar, secili, rozet) in enumerate(kartlar):
        x = CX + i * (kw + 16)
        h = 112
        if secili:
            t.dikdortgen(x, y, kw, h, dolgu=C["vurgu_ton"], kenar=C["vurgu"], r=8, kalinlik=1.5)
        else:
            t.dikdortgen(x, y, kw, h, dolgu=C["yuzey"], kenar=C["cizgi"], r=8)
        t.dikdortgen(x + 14, y + 14, 36, 36, dolgu=C["yuzey"] if secili else C["yuzey2"], kenar=C["vurgu_ton2"] if secili else C["cizgi2"], r=7)
        t.simge(ik, x + 32, y + 32, 22, C["vurgu"] if secili else C["simge"], 1.5)
        t.yazi(x + 62, y + 30, ad, 14, 600, C["metin"])
        if rozet:
            etiket_cip(t, x + 62 + t.yazi_gen(ad, 14, 600) + 8, y + 18, rozet, "uyari", h=17, boyut=9)
        radyo(t, x + kw - 22, y + 24, secili)
        yy = y + 66
        for s in satirlar:
            t.yazi(x + 16, yy, s, 11, 400, C["metin2"])
            yy += 16
    y += 112 + 22
    # --- ön geometri
    y = bolum(t, CX, y, CW, "Ön geometri (tahmini)", "TBDY md. 3.3.1.3 · BYS, periyot, rüzgâr", "kat")
    etiket(t, CX, y, "Kat sayısı")
    birimli(t, CX + lw, y, 76, "4", hiza="sag")
    for j, ik in enumerate(("kucult", "artı")):
        t.dikdortgen(CX + lw + 82 + j * 30, y, 26, 26, dolgu=C["yuzey"], kenar=C["giris_kenar"], r=4)
        t.simge(ik, CX + lw + 95 + j * 30, y + 13, 12, C["metin2"], 1.6)
    t.yazi(CX + lw + 150, taban(y, 26, 11), "1–12 (aks–kat modeli)", 11, 400, C["metin3"])
    etiket(t, SAG_X, y, "Tipik kat yüksekliği")
    birimli(t, SAG_X + lw + 20, y, 110, sy(ORN["kat_h"]), "m")
    t.yazi(SAG_X + lw + 140, taban(y, 26, 11), "≥ 2,00 m", 11, 400, C["metin3"])
    y += 36
    etiket(t, CX, y, "Bina yüksekliği H_{N}")
    w = cip(t, CX + lw, y + 1, "H_{N}", sy(HN), "m", "vurgu")
    t.yazi(CX + lw + w + 10, taban(y, 26, 11), "= kat sayısı × kat yüksekliği; model kurulunca kat kotlarından yeniden hesaplanır", 11, 400, C["metin3"])
    y += 46
    # --- uygulanacak yönetmelikler
    y = bolum(t, CX, y, CW, "Uygulanacak yönetmelikler", "Adım 2–7'nin içeriğini belirler", "yonetmelik")
    x = CX
    for metin, tur in (("TS 498:2021 · Yükler", "ok"), ("TS 500:2000 · Betonarme", "ok"), ("TBDY 2018 · Deprem", "ok"),
                       ("TS 708:2016 · Donatı", "ok"), ("ÇYTHYE 2018 · Çelik — uygulanmaz", "pasif")):
        x += etiket_cip(t, x, y, metin, tur, h=24, boyut=11, simge="onay" if tur == "ok" else "kapat") + 8
    y += 34
    t.yazi(CX, y + 4, "Öneriler: birleşim kümesi TS 500 + TBDY 4.4.4 (Adım 6) · çatlamış kesit rijitliği açık (Adım 7, TBDY md. 4.5.8.1).", 11, 400, C["metin2"])
    # --- sağ ray
    y = ray_baslik(t)
    y = ray_etiket(t, y, "MODELE YAZILAN  ·  model/bina.json")
    y = kod_blogu(t, y, [("baslik = ", '"Konut Bloğu A"'), ("sistem = ", '"betonarme"'), ("yuk_durumlari.S.il = ", '"Tokat"'),
                         ("yuk_durumlari.S.ilce = ", '"Merkez"'), ("yuk_durumlari.S.rakim = ", "623")])
    y = ray_etiket(t, y, "PROJE BELGESİNE  ·  proje/yonetmelik.json")
    y = kod_blogu(t, y, [("kunye: ", "ad, il, ilce, ada, parsel,"), ("       ", "koordinat, hazirlayan, tarih"),
                         ("on_geometri: ", "kat 4, h 3.00, HN 12.00")])
    y = ray_etiket(t, y + 2, "ETKİLEDİĞİ ADIMLAR")
    y += 14
    for m in ("Adım 2 — beton ve donatı grupları açılır; yapı çeliği gizlenir.",
              f"Adım 3 — kar bölgesi Ek 1'den: Tokat / Merkez → {KAR_BOLGE} (doğrulanmalı).",
              "Adım 4 — Tablo 4.1'in A ve B satırları; C_{t} = 0,10.",
              "Adım 6 — varsayılan küme TS 500 + TBDY 4.4.4.",
              "Adım 7 — çatlamış kesit varsayılanı açık."):
        y = ray_madde(t, y, m)
    y = ray_etiket(t, y + 4, "NOT")
    y += 14
    ray_madde(t, y, "op4 çevrimdışı çalışır: koordinat kayıt içindir, S_{S} / S_{1} haritadan otomatik çekilmez (Adım 4).", "bilgi", C["vurgu"])
    alt_cubuk(t, "Adımı varsayılana döndür", [("Geri", "ikincil", 92, None, None, True), ("İleri: Malzemeler", "birincil", 196, None, "sevron_sag", False)])


# ============================================================================
# ADIM 4 — Deprem (TBDY 2018)
# ============================================================================
def adim4(t):
    durumlar = ["tamam", "tamam", "uyari", "etkin", "bekliyor", "bekliyor", "bekliyor", "bekliyor"]
    altlar = [("Konut Bloğu A · Betonarme", "tamam"), ("C30/37 · B420C", "tamam"), ("1 doğrulanmamış kayıt", "uyari"),
              (f"ZD · S_{{DS}} {sy(SP2['SDS'], 3)} · DTS {DTS}", "tamam"), ("Tekil · q_{em} 200 (şablon)", "bekliyor"),
              ("TS 500 + TBDY 4.4.4", "bekliyor"), ("Çatlamış kesit · rijit diyafram", "bekliyor"), ("Gözden geçirilmedi", "bekliyor")]
    cerceve(t, 4, durumlar, altlar)
    y0 = ana_baslik(t, 4, "Deprem — TBDY 2018",
                    "Harita spektral ivme katsayıları, yerel zemin sınıfı, bina kullanım sınıfı ve taşıyıcı sistemden tasarım spektrumu, deprem tasarım sınıfı ve azaltma katsayıları hesaplanır.",
                    ("Bölüm 2", "Bölüm 3", "Bölüm 4"))
    # ---------------- sol sütun
    x, w = CX, SOL_W
    y = bolum(t, x, y0, w, "Deprem yer hareketi", "md. 2.2 – 2.3.2", "deprem")
    etiket(t, x, y, "Deprem etkisi")
    anahtar(t, x + 150, y + 5, True)
    t.yazi(x + 190, taban(y, 26, 11), "E yük durumu açık · EX±, EY±, EZ", 11, 400, C["metin2"])
    y += 34
    # tablo
    c1, c2 = x + 150, x + 150 + 128
    t.yazi(x, y + 10, "DÜZEY", 10, 700, C["metin3"])
    alt_yazi(t, c1, y + 10, "S_{S}  (kısa periyot)", 10, 700, C["metin3"])
    alt_yazi(t, c2, y + 10, "S_{1}  (1 s)", 10, 700, C["metin3"])
    y += 18
    etiket(t, x, y, "DD-2 · tasarım")
    t.yazi(x, taban(y, 26, 10) + 14, "475 yıl · %10 / 50 yıl", 10, 400, C["metin3"])
    birimli(t, c1, y, 116, sy(ORN["SS"], 3), "g", odak=True)
    birimli(t, c2, y, 116, sy(ORN["S1"], 3), "g")
    y += 40
    etiket(t, x, y, "DD-3 · yalnız λ için")
    t.yazi(x, taban(y, 26, 10) + 14, "72 yıl · isteğe bağlı", 10, 400, C["metin3"])
    birimli(t, c1, y, 116, sy(ORN["SS3"], 3), "g")
    birimli(t, c2, y, 116, sy(ORN["S13"], 3), "g")
    y += 42
    t.simge("konum", x + 7, y + 6, 14, C["metin2"], 1.4)
    paragraf(t, x + 20, y + 10, f"Türkiye Deprem Tehlike Haritası (resmî etkileşimli harita hizmeti) · {ORN['enlem']}° K, {ORN['boylam']}° D · elle girildi",
             w - 20, 11, 400, C["metin3"], 15)
    y += 34
    dugme(t, x + 20, y, 172, "Rapordan içe aktar…", simge="ice_aktar_belge", h=26)
    dugme(t, x + 200, y, 150, "Panodan yapıştır", simge="yapistir", h=26)
    y += 44
    # zemin
    y = bolum(t, x, y, w, "Yerel zemin sınıfı", "Tablo 16.1", "zemin")
    segment(t, x, y, ["ZA", "ZB", "ZC", "ZD", "ZE", "ZF"], "ZD", h=28, boyut=12, min_w=w / 6, isaretli=("ZF",))
    y += 36
    alt_yazi(t, x, y + 10, "ZD — orta sıkı–sıkı kum, çakıl ya da çok katı kil · V_{S30} 180–360 m/s", 11, 400, C["metin2"])
    y += 22
    xx = x
    xx += cip(t, xx, y, "F_{S}", sy(SP2["FS"], 3), "", "notr") + 8
    xx += cip(t, xx, y, "F_{1}", sy(SP2["F1"], 3), "", "notr") + 10
    t.yazi(xx, taban(y, 24, 10), "Tablo 2.1 / 2.2 · doğrusal ara değer", 10, 400, C["metin3"])
    y += 32
    t.simge("uyari", x + 6, y + 5, 12, C["uyari"], 1.4)
    t.yazi(x + 18, y + 9, "ZF: sahaya özel zemin davranış analizi gerekir (md. 16.5); motor çözmez → adım “eksik”.", 10, 400, C["metin3"])
    y += 26
    # BKS
    y = bolum(t, x, y, w, "Bina kullanım sınıfı", "Tablo 3.1", "bina")
    acilir(t, x, y, w - 104, "BKS 3 — konut, işyeri, otel, endüstri")
    cip(t, x + w - 92, y + 1, "I", sy(I_, 1), "", "vurgu")
    y += 44
    # taşıyıcı
    y = bolum(t, x, y, w, "Taşıyıcı sistem", "Tablo 4.1 · md. 4.3", "cerceve")
    acilir(t, x, y, w, f"{TS['kod']} — Tamamı moment aktaran SDY betonarme çerçeve")
    y += 34
    xx = x
    xx += cip(t, xx, y, "R", sy(R_, 0), "", "vurgu") + 6
    xx += cip(t, xx, y, "D", sy(D_, 0), "", "vurgu") + 6
    xx += etiket_cip(t, xx, y + 3, "süneklik yüksek", "notr") + 6
    etiket_cip(t, xx, y + 3, f"BYS ≥ {TS['BYS_min']} · sağlanıyor", "ok", simge="onay")
    y += 32
    t.yazi(x, y + 8, "Liste yapı türüne göre süzülür (Adım 1: betonarme → A ve B satırları).", 10, 400, C["metin3"])

    # ---------------- sağ sütun
    x, w = SAG_X, SAG_W
    y = bolum(t, x, y0, w, "Hesaplanan değerler", "Denk. 2.1–2.3 · Tablo 3.2–3.3 · 4.4", "tablo")
    tw = (w - 3 * 8) / 4
    karolar = [("S_{DS}", sy(SP2["SDS"], 3), "g", "vurgu"), ("S_{D1}", sy(SP2["SD1"], 3), "g", "vurgu"),
               ("T_{A}", sy(SP2["TA"], 3), "s", "notr"), ("T_{B}", sy(SP2["TB"], 3), "s", "notr"),
               ("DTS", DTS, "Tablo 3.2", "vurgu"), ("BYS", str(BYS), "Tablo 3.3", "vurgu"),
               ("T_{pA}", sy(TPA, 3), "s", "notr"), ("EDYY", "uygun", f"BYS ≥ {EDYY_ESIK}", "ok")]
    for i, (ad, deger, birim, tur) in enumerate(karolar):
        kx = x + (i % 4) * (tw + 8)
        ky = y + (i // 4) * 54
        zem = {"vurgu": C["vurgu_ton"], "notr": C["yuzey2"], "ok": C["ok_ton"]}[tur]
        ken = {"vurgu": C["vurgu_ton2"], "notr": C["cizgi2"], "ok": C["ok_kenar"]}[tur]
        t.dikdortgen(kx, ky, tw, 46, dolgu=zem, kenar=ken, r=6)
        alt_yazi(t, kx + 10, ky + 16, ad, 11, 600, C["metin2"])
        renk = {"vurgu": C["vurgu_koyu"], "notr": C["metin"], "ok": C["ok"]}[tur]
        dw = t.yazi_gen(deger, 16, 600, True)
        t.yazi(kx + 10, ky + 37, deger, 16, 600, renk, tnum=True)
        t.yazi(kx + 14 + dw, ky + 37, birim, 10, 400, C["metin3"])
    y += 2 * 54
    alt_yazi(t, x, y + 6, f"H_{{N}} = {sy(HN)} m tahmini (Adım 1) — model kurulunca yeniden hesaplanır · T_{{pA}}: Denk. 4.27, C_{{t}} = {sy(CT)}",
             10, 400, C["metin3"])
    y += 24
    y = bolum(t, x, y, w, "Tasarım spektrumu", "Denk. 2.2 · 4.1 · 4.8", "spektrum")
    spektrum_grafik(t, x, y - 4, w, 232)
    y += 232 + 14
    y = bolum(t, x, y, w, "Hesap seçenekleri", "md. 4.5.10 · 4.7.3 · 4.9.1", "ayar")
    lw = 132
    etiket(t, x, y, "Periyot T_{p}")
    sw = segment(t, x + lw, y, ["Otomatik", "Ampirik", "Rayleigh"], "Otomatik", h=26)
    t.yazi(x + lw + sw + 8, taban(y, 26, 11), "→ ampirik (md. 4.7.3.3)" if AMPIRIK_YETER else "→ Rayleigh", 11, 400, C["metin3"])
    y += 34
    etiket(t, x, y, "C_{t}  (Denk. 4.27)")
    acilir(t, x + lw, y, w - lw, "Otomatik · 0,10 — betonarme çerçeve")
    y += 34
    etiket(t, x, y, "n  (Tablo 4.3)")
    acilir(t, x + lw, y, w - lw, "Otomatik · 0,3 — kullanım sınıfından (konut)")
    y += 34
    etiket(t, x, y, "Ek dışmerkezlik")
    birimli(t, x + lw, y, 96, "0,05", "")
    alt_yazi(t, x + lw + 104, taban(y, 26, 11), "× B_{i}  (± %5, md. 4.5.10.2)", 11, 400, C["metin3"])
    y += 34
    etiket(t, x, y, "Dolgu duvarlar")
    acilir(t, x + lw, y, w - lw, "Çerçeveye bitişik gevrek dolgu · 0,008κ")

    # ---------------- sağ ray
    y = ray_baslik(t)
    y = ray_etiket(t, y, "MODELE YAZILAN  ·  deprem, yuk_durumlari.E")
    y = kod_blogu(t, y, [("deprem.SS = ", "1.2   S1 = 0.35"), ("deprem.SS_DD3 = ", "0.45   S1_DD3 = 0.13"),
                         ("deprem.zemin_sinifi = ", '"ZD"'), ("deprem.BKS = ", "3   I = 1.0"),
                         ("deprem.tasiyici = ", '"betonarme-cerceve-yuksek"'), ("deprem.R = ", "8   D = 3   DD = \"DD-2\""),
                         ("deprem.periyot = ", '"otomatik"'), ("deprem.dismerkezlik = ", '0.05'), ("deprem.dolgu = ", '"bitisik"'),
                         ("yuk_durumlari.E.acik = ", "true")], satir=15)
    y = ray_etiket(t, y, "ETKİLEDİĞİ")
    y += 14
    for m in ("Adım 5 — zemin sınıfı ZD temel adımına taşınır.",
              f"Adım 6 — Denk. 4.11 / 4.12: {KOMB.get('deprem', 0)} deprem ve {KOMB.get('drift', 0)} öteleme birleşimi.",
              "Adım 7 — betonarme + deprem: çatlamış kesit zorunlu (md. 4.5.8.1).",
              f"EZ = (2/3)·S_{{DS}}·G = {sy(2 / 3 * SP2['SDS'], 3)}·G (Denk. 4.10).",
              f"λ = S_{{ae}}(DD-3) / S_{{ae}}(DD-2) = {sy(LAM, 3)} (md. 4.9.1.4)."):
        y = ray_madde(t, y, m)
    y = ray_etiket(t, y + 2, "UYARILAR")
    y += 14
    y = ray_madde(t, y, f"DTS {DTS}: süneklik düzeyi sınırlı sistemler (A31, B31, C31) listede soluk; md. 4.3.4.1 / 4.3.4.3.", "bilgi", C["vurgu"])
    y = ray_madde(t, y, "H_{N} tahminidir; BYS ve T_{pA} model kurulunca yeniden hesaplanır.", "uyari", C["uyari"])
    y = ray_etiket(t, y + 4, "KAYNAK")
    y += 14
    y = ray_madde(t, y, "TBDY 2018 (RG 18.03.2018 / 30364 Mük.); tablolar motor kütüphanesinden, hepsi doğrulanmış.", "yonetmelik", C["metin2"])
    t.yazi(RAIL_X + 38, y + 2, "Madde metnini Belge penceresinde aç  ›", 11, 500, C["vurgu"])
    alt_cubuk(t, "Adımı varsayılana döndür", [("Geri", "ikincil", 92, "sevron_sol", None, False), ("Atla", "hayalet", 64, None, None, False),
                                             ("İleri: Zemin ve temel", "birincil", 214, None, "sevron_sag", False)])


# ============================================================================
# ADIM 5 — Zemin ve temel
# ============================================================================
def ters_t_cizim(t, x, y, w, h):
    """Ters T temel kirişi kesiti + Winkler yayları + boyutlar (ölçekli, 80 px/m)."""
    S = 4
    g = Tuval(w, h, S, zemin=C["yuzey"])
    olc = 80.0
    B, ht, bg, hg = 1.2, 0.40, 0.50, 1.00
    cx = 132
    taban_y = h - 52
    tx0, tx1 = cx - B * olc / 2, cx + B * olc / 2
    # başlık
    g.yazi(14, 18, "Kesit önizlemesi", 10, 600, C["metin2"])
    alt_yazi(g, 14, 32, "Winkler: k_{z} = k_{0}·B·l_{etki}", 10, 400, C["metin3"])
    # zemin (taralı) ve yaylar
    zy = taban_y + 16
    g.dikdortgen(16, zy, w - 32, 14, dolgu=rgba(C["zemin_tarama"], 0.16))
    k = 16
    while k < w - 24:
        g.cizgi(k, zy + 14, k + 8, zy + 4, rgba(C["zemin_tarama"], 0.75), 1)
        k += 9
    g.yatay(16, w - 16, zy, C["zemin_tarama"], 1)
    for i in range(7):
        sx_ = tx0 + 6 + i * (B * olc - 12) / 6
        pts = [(sx_, taban_y + 1)]
        for j in range(5):
            pts.append((sx_ + (3.5 if j % 2 == 0 else -3.5), taban_y + 3 + j * 2.4))
        pts.append((sx_, zy))
        g.d.line([(a_ * S, b_ * S) for a_, b_ in pts], fill=C["metin2"], width=S)
    # kesit
    g.dikdortgen(tx0, taban_y - ht * olc, B * olc, ht * olc, dolgu=C["beton"], kenar=C["beton_kenar"], kalinlik=1.5)
    g.dikdortgen(cx - bg * olc / 2, taban_y - hg * olc, bg * olc, (hg - ht) * olc + 1.5, dolgu=C["beton"], kenar=C["beton_kenar"], kalinlik=1.5)
    g.yatay(cx - bg * olc / 2 + 1.5, cx + bg * olc / 2 - 1.5, taban_y - ht * olc, C["beton"], 2)
    g.dikdortgen(cx - 14, taban_y - hg * olc - 16, 28, 16, dolgu=C["yuzey3"], kenar=C["beton_kenar"], kalinlik=1)
    g.yazi_orta(cx, taban_y - (hg + ht) * olc / 2 + 4, "b 0,50", 9, 600, C["metin2"])
    # ölçüler
    g.yatay(tx0, tx1, taban_y + 38, C["metin2"], 1)
    g.dikey(tx0, taban_y + 34, taban_y + 42, C["metin2"]); g.dikey(tx1 - 1, taban_y + 34, taban_y + 42, C["metin2"])
    g.dikdortgen(cx - 34, taban_y + 31, 68, 14, dolgu=C["yuzey"])
    g.yazi_orta(cx, taban_y + 42, "B = 1,20 m", 10, 600, C["metin"])
    xr = tx1 + 10
    g.dikey(xr, taban_y - ht * olc, taban_y, C["metin2"], 1)
    g.yatay(xr - 4, xr + 4, taban_y - ht * olc, C["metin2"]); g.yatay(xr - 4, xr + 4, taban_y - 1, C["metin2"])
    g.yazi(xr + 6, taban_y - ht * olc / 2 + 4, "0,40", 10, 600, C["metin"], tnum=True)
    xl = tx0 - 12
    g.dikey(xl, taban_y - hg * olc, taban_y, C["metin2"], 1)
    g.yatay(xl - 4, xl + 4, taban_y - hg * olc, C["metin2"]); g.yatay(xl - 4, xl + 4, taban_y - 1, C["metin2"])
    g.yazi_sag(xl - 6, taban_y - hg * olc / 2 + 4, "1,00", 10, 600, C["metin"], tnum=True)
    im = g.img.resize((w * t.s, h * t.s), Image.LANCZOS)
    t.img.paste(im, (t.p(x), t.p(y)))
    t._yenile()


def adim5(t):
    durumlar = ["tamam", "tamam", "uyari", "tamam", "etkin", "bekliyor", "bekliyor", "bekliyor"]
    altlar = [("Konut Bloğu A · Betonarme", "tamam"), ("C30/37 · B420C", "tamam"), ("1 doğrulanmamış kayıt", "uyari"),
              (f"ZD · S_{{DS}} {sy(SP2['SDS'], 3)} · DTS {DTS}", "tamam"), ("Mütemadi · q_{em} 150", "tamam"),
              ("TS 500 + TBDY 4.4.4", "bekliyor"), ("Çatlamış kesit · rijit diyafram", "bekliyor"), ("Gözden geçirilmedi", "bekliyor")]
    cerceve(t, 5, durumlar, altlar)
    y0 = ana_baslik(t, 5, "Zemin ve temel",
                    "Geoteknik rapordaki zemin değerleri ve temel tipi. Emniyet gerilmesi servis kontrolünde, karakteristik taşıma gücü TBDY 16.8 kontrolünde, yatak katsayısı Winkler zemin yaylarında kullanılır.",
                    ("TBDY Bölüm 16", "TS 500 md. 10"))
    # ---------------- sol
    x, w = CX, SOL_W
    y = bolum(t, x, y0, w, "Yerel zemin", "Tablo 16.1", "zemin")
    t.dikdortgen(x, y, 46, 38, dolgu=C["vurgu_ton"], kenar=C["vurgu_ton2"], r=6)
    t.yazi_orta(x + 23, y + 25, "ZD", 15, 700, C["vurgu_koyu"])
    t.yazi(x + 58, y + 15, "Orta sıkı – sıkı kum, çakıl ya da çok katı kil", 12, 500, C["metin"])
    alt_yazi(t, x + 58, y + 32, "V_{S30} 180–360 m/s · Adım 4'te seçildi", 11, 400, C["metin3"])
    t.yazi_sag(x + w, y + 32, "Adım 4'te değiştir", 11, 500, C["vurgu"])
    y += 58
    y = bolum(t, x, y, w, "Geoteknik rapor değerleri", "TS 500 md. 10.1 · TBDY 16.8", "rapor")
    lw = 160
    iw = 150
    etiket(t, x, y, "Emniyet gerilmesi q_{em}")
    birimli(t, x + lw, y, iw, f"{ORN['q_em']}", "kN/m²")
    bilgi(t, x + lw + iw + 14, y + 13)
    alt_yazi(t, x + lw + iw + 26, taban(y, 26, 10), "servis: p_{maks} ≤ q_{em}", 10, 400, C["metin3"])
    y += 34
    etiket(t, x, y, "Taşıma gücü q_{k}")
    birimli(t, x + lw, y, iw, f"{ORN['q_k']}", "kN/m²", odak=True)
    bilgi(t, x + lw + iw + 14, y + 13)
    t.yazi(x + lw + iw + 26, taban(y, 26, 10), "karakteristik", 10, 400, C["metin3"])
    y += 32
    xx = x + lw
    xx += cip(t, xx, y, "q_{t} = q_{k}/γ_{Rv}", sy(Q_T, 1), "kN/m²", "vurgu") + 8
    alt_yazi(t, xx, taban(y, 24, 10), "γ_{Rv} = 1,4 · Tablo 16.2", 10, 400, C["metin3"])
    y += 34
    etiket(t, x, y, "Yatak katsayısı k_{0}")
    birimli(t, x + lw, y, iw, sy(ORN["k0"], 0), "kN/m³")
    bilgi(t, x + lw + iw + 14, y + 13)
    y += 32
    # aralık çubuğu: tipik k0 aralıkları (öğretici; bina.js tablosu)
    bx, bw = x + lw, w - lw
    kmax = 80000.0
    t.dikdortgen(bx, y + 8, bw, 6, dolgu=C["cizgi2"], r=3)
    a0, a1 = 9600, 48000
    t.dikdortgen(bx + bw * a0 / kmax, y + 8, bw * (a1 - a0) / kmax, 6, dolgu=C["vurgu_ton2"], r=3)
    mx = bx + bw * ORN["k0"] / kmax
    t.daire(mx, y + 11, 5.5, dolgu=C["yuzey"], kenar=C["vurgu"], kalinlik=2)
    for v in (0, 20000, 40000, 60000, 80000):
        tx_ = bx + bw * v / kmax
        t.dikey(tx_, y + 15, y + 18, C["giris_kenar"])
        if v == 0:
            t.yazi(tx_, y + 29, "0", 9, 500, C["metin3"], tnum=True)
        elif v == kmax:
            t.yazi_sag(tx_, y + 29, sy(v, 0), 9, 500, C["metin3"], tnum=True)
        else:
            t.yazi_orta(tx_, y + 29, sy(v, 0), 9, 500, C["metin3"], tnum=True)
    t.yazi(x, y + 15, "Tipik aralık", 11, 400, C["metin3"])
    y += 40
    paragraf(t, x + lw, y + 4, "Orta sıkı kum / katı kil: 9 600–48 000 kN/m³ (plaka deneyi); temel boyutuna göre küçültülür — rapordaki değer esastır.",
             w - lw, 10, 400, C["metin3"], 14)
    y += 38
    etiket(t, x, y, "Zemin birim hacim ağ. γ")
    birimli(t, x + lw, y, iw, sy(ORN["gamma_z"], 1), "kN/m³")
    t.yazi(x + lw + iw + 10, taban(y, 26, 10), "kayıt (tahkikte yok)", 10, 400, C["metin3"])
    y += 34
    etiket(t, x, y, "Rapor no / tarih")
    birimli(t, x + lw, y, 120, "GR-26/114", hiza="sol")
    birimli(t, x + lw + 128, y, w - lw - 128, "12.10.2026", hiza="sol")
    y += 46
    y = bolum(t, x, y, w, "Temel malzemesi", "TS 500 md. 10.1", "malzeme")
    etiket(t, x, y, "Beton")
    acilir(t, x + 54, y, 150, "C30/37 · Adım 2")
    etiket(t, x + 224, y, "Donatı")
    acilir(t, x + 278, y, w - 278, "B420C")
    y += 34
    etiket_cip(t, x + 54, y + 2, "Paspayı ≥ 50 mm · TS 500 md. 10.1 (sabit)", "notr", h=20)

    # ---------------- sağ
    x, w = SAG_X, SAG_W
    y = bolum(t, x, y0, w, "Temel tipi", "TS 500 md. 10 · temeller.tip", "temel")
    kw = (w - 16) / 3
    for i, (ik, ad, aciklama, secili) in enumerate((("temel", "Tekil", "Kolon başına B × L · ankastre, mafsal ya da elastik", False),
                                                    ("temel_surekli", "Mütemadi", "Aks boyunca ters T temel kirişi · Winkler", True),
                                                    ("temel_radye", "Radye", "Plak ızgarası · Winkler · isteğe bağlı kiriş", False))):
        kx = x + i * (kw + 8)
        h = 112
        if secili:
            t.dikdortgen(kx, y, kw, h, dolgu=C["vurgu_ton"], kenar=C["vurgu"], r=8, kalinlik=1.5)
        else:
            t.dikdortgen(kx, y, kw, h, dolgu=C["yuzey"], kenar=C["cizgi"], r=8)
        t.simge(ik, kx + 24, y + 26, 24, C["vurgu"] if secili else C["simge"], 1.5)
        radyo(t, kx + kw - 18, y + 18, secili)
        t.yazi(kx + 14, y + 62, ad, 13, 600, C["metin"])
        paragraf(t, kx + 14, y + 80, aciklama, kw - 24, 10, 400, C["metin2"], 13)
    y += 112 + 22
    y = bolum(t, x, y, w, "Mütemadi temel varsayılanları", "md. 10.4.2", "temel_surekli")
    hw = (w - 16) / 2
    lw2 = 86
    alanlar = [(("Doğrultu", "acilir", "x ve y (ızgara)", ""), ("Akslar", "acilir", "Tümü", "")),
               (("B tabla", "sayi", "1,20", "m"), ("Taşma", "sayi", "0,50", "m")),
               (("h tabla", "sayi", "0,40", "m"), ("b gövde", "sayi", "0,50", "m")),
               (("h gövde", "sayi", "1,00", "m"), ("Ağ aralığı", "acilir", "Otomatik", "")),
               (("Yatay", "acilir", "Tutulu", ""), None)]
    for sat in alanlar:
        for j, a in enumerate(sat):
            if a is None:
                continue
            ax = x + j * (hw + 16)
            et, tur, deger, birim = a
            etiket(t, ax, y, et)
            if tur == "acilir":
                acilir(t, ax + lw2, y, hw - lw2, deger)
            else:
                birimli(t, ax + lw2, y, hw - lw2, deger, birim)
        y += 32
    y -= 32
    # Yatay satırının sağına denetimler
    y += 40
    t.dikdortgen(x, y, w, 186, dolgu=C["yuzey"], kenar=C["cizgi2"], r=6)
    ters_t_cizim(t, x + 1, y + 1, 258, 184)
    t.dikey(x + 260, y + 10, y + 176, C["cizgi2"])
    dx = x + 274
    yy = y + 22
    t.yazi(dx, yy, "Anında denetim", 11, 600, C["metin"])
    yy += 22
    for durum, metin in (("ok", "h tabla ≥ 0,20 m"), ("ok", "b gövde ≤ B"), ("ok", "h tabla ≤ h gövde"),
                         ("ok", "B ≤ 6,0 m · h ≤ 4,0 m"), ("bekle", "h gövde ≥ L_{n} / 10"), ("bekle", "zımbalama, ρ ≥ 0,002")):
        if durum == "ok":
            t.daire(dx + 7, yy - 4, 7, dolgu=C["ok_ton"], kenar=C["ok_kenar"])
            t.simge("onay", dx + 7, yy - 4, 9, C["ok"], 2.0)
        else:
            t.daire(dx + 7, yy - 4, 7, dolgu=C["yuzey"], kenar=C["giris_kenar"])
            t.daire(dx + 7, yy - 4, 1.6, dolgu=C["metin3"])
        alt_yazi(t, dx + 20, yy, metin, 11, 400, C["metin"] if durum == "ok" else C["metin2"])
        yy += 21
    t.yazi(dx, yy + 6, "○ model kurulunca / çözümde", 10, 400, C["metin3"])

    # ---------------- sağ ray
    y = ray_baslik(t)
    y = ray_etiket(t, y, "MODELE YAZILAN  ·  temeller")
    y = kod_blogu(t, y, [("tip = ", '"surekli"'), ("zemin.q_em = ", "150   q_k = 450"), ("zemin.k0 = ", "18000   gamma = 19"),
                         ("surekli.yon = ", '"xy"   akslar = "tum"'), ("surekli.B = ", "1.2   h_tabla = 0.4"),
                         ("surekli.b_govde = ", "0.5   h_govde = 1.0"), ("surekli.tasma = ", '0.5   ag = "otomatik"'),
                         ("surekli.yatay = ", '"tutulu"'), ("malzeme = ", '"C30"   donati = "B420C"')], satir=15)
    y = ray_etiket(t, y, "ÇÖZÜMDE KULLANILDIĞI YER")
    y += 14
    for m in (f"TS 500 md. 10.1 — servis G+Q: p_{{maks}} ≤ q_{{em}} = {ORN['q_em']} kN/m².",
              f"TBDY 16.8 — katsayılı q_{{o}} ≤ q_{{t}} = {sy(Q_T, 1)} kN/m².",
              "Winkler — düğüm yayı k_{z} = k_{0}·B·l, tabla dönme yayı k_{0}·B³/12·l.",
              "TS 500 md. 8.3.1 zımbalama; md. 10.3.3 ρ ≥ 0,002."):
        y = ray_madde(t, y, m)
    y = ray_etiket(t, y + 2, "UYARILAR")
    y += 14
    y = ray_madde(t, y, "k_{0} temel boyutuna bağlıdır; plaka deneyi değerleri küçültülmelidir — rapordaki değeri girin.", "bilgi", C["vurgu"])
    y = ray_madde(t, y, "q_{k} boş bırakılırsa motor q_{k} = 3·q_{em} varsayar ve rapora uyarı yazar.", "bilgi", C["vurgu"])
    alt_cubuk(t, "Adımı varsayılana döndür", [("Geri", "ikincil", 92, "sevron_sol", None, False),
                                             ("İleri: Yük birleşimleri", "birincil", 226, None, "sevron_sag", False)])


# ============================================================================
# ADIM 8 — Özet ve onay
# ============================================================================
def ozet_kart(t, x, y, w, no, baslik, satirlar, uyari_satir=()):
    h = 34 + len(satirlar) * 22 + 8
    t.dikdortgen(x, y, w, h, dolgu=C["yuzey"], kenar=C["cizgi"], r=7)
    t.dikdortgen(x + 1, y + 1, w - 2, 30, dolgu=C["yuzey2"], r=7)
    t.dikdortgen(x + 1, y + 16, w - 2, 15, dolgu=C["yuzey2"])
    t.yatay(x + 1, x + w - 1, y + 31, C["cizgi2"])
    t.daire(x + 18, y + 16, 9, dolgu=C["uyari"] if uyari_satir else C["ok"])
    t.yazi_orta(x + 18, y + 20, str(no), 10, 700, C["beyaz"])
    t.yazi(x + 34, y + 21, baslik, 12, 600, C["metin"])
    t.yazi_sag(x + w - 12, y + 21, "Düzenle", 11, 500, C["vurgu"])
    yy = y + 36
    for i, (et, deger, ref) in enumerate(satirlar):
        t.yazi(x + 12, yy + 15, et, 11, 400, C["metin2"])
        uy = i in uyari_satir
        rw = t.yazi_gen(ref, 10, 400) if ref else 0
        dx = x + 104
        if uy:
            t.simge("uyari", dx + 6, yy + 10, 12, C["uyari"], 1.4)
            dx += 16
        alt_yazi(t, dx, yy + 15, deger, 11, 500, C["metin"], tnum=True)
        if ref:
            t.yazi_sag(x + w - 12, yy + 15, ref, 10, 400, C["metin3"])
        if i < len(satirlar) - 1:
            t.yatay(x + 12, x + w - 12, yy + 22, C["cizgi2"])
        yy += 22
    return y + h


def uyari_satir_no(us):
    return {"uyari"} if us else set()


def adim8(t):
    durumlar = ["tamam", "tamam", "uyari", "tamam", "tamam", "tamam", "tamam", "etkin"]
    altlar = [("Konut Bloğu A · Betonarme", "tamam"), ("C30/37 · B420C", "tamam"), ("1 doğrulanmamış · 1 doğrulanmalı", "uyari"),
              (f"ZD · S_{{DS}} {sy(SP2['SDS'], 3)} · DTS {DTS}", "tamam"), ("Mütemadi · q_{em} 150", "tamam"),
              (f"TS 500 + TBDY · {KOMB_TOPLAM} birleşim", "tamam"), ("Çatlamış kesit · rijit diyafram", "tamam"), ("Hazır", "tamam")]
    cerceve(t, 8, durumlar, altlar)
    y0 = ana_baslik(t, 8, "Özet ve onay",
                    "Seçilen değerler yönetmelik kaynaklarıyla. “Projeyi oluştur” değerleri modele tek geri alma adımı olarak yazar; hepsi sonradan “Proje › Yönetmelik verileri” ile düzenlenebilir.",
                    ("Bütün adımlar",))
    x = CX
    y = y0 - 4
    # durum bandı
    xx = x
    for sayi_, et, tur in (("7", "adım tamam", "ok"), ("2", "uyarı", "uyari"), ("0", "eksik", "notr")):
        zem = {"ok": C["ok_ton"], "uyari": C["uyari_ton"], "notr": C["yuzey2"]}[tur]
        ken = {"ok": C["ok_kenar"], "uyari": C["uyari_kenar"], "notr": C["cizgi2"]}[tur]
        rk = {"ok": C["ok"], "uyari": C["uyari"], "notr": C["metin2"]}[tur]
        w = 54 + t.yazi_gen(et, 12, 500)
        t.dikdortgen(xx, y, w, 40, dolgu=zem, kenar=ken, r=7)
        t.yazi(xx + 14, y + 28, sayi_, 20, 700, rk, tnum=True)
        t.yazi(xx + 38, y + 26, et, 12, 500, C["metin"])
        xx += w + 10
    paragraf(t, xx + 8, y + 17, "Projeyi oluşturmaya hazır. Uyarılar oluşturmayı engellemez; eksik alan olsaydı “Projeyi oluştur” pasif olurdu.",
             CX + CW - xx - 8, 11, 400, C["metin2"], 15)
    y += 52
    # uyarı kutusu
    t.dikdortgen(x, y, CW, 64, dolgu=C["uyari_ton"], kenar=C["uyari_kenar"], r=7)
    for i, (m, ad) in enumerate(((f"Adım 3 · Kaplama “şap + seramik + sıva” {sy(KAPLAMA['deger'])} kN/m²: seramik birim hacim ağırlığı kütüphanede doğrulanmamış (TS 498 md. 5 → TS ISO 9194).", "Düzenle"),
                                 (f"Adım 3 · Kar bölgesi Tokat / Merkez → {KAR_BOLGE}: TS 498:2021 Ek 1 listesi tek tek doğrulanmadı; bölgeyi Ek 2 haritasından teyit edin.", "Düzenle"))):
        yy = y + 22 + i * 24
        t.simge("uyari", x + 18, yy - 4, 13, C["uyari"], 1.5)
        t.yazi(x + 32, yy, t.yazi_kes(m, CW - 110, 11), 11, 400, C["metin"])
        t.yazi_sag(x + CW - 14, yy, ad, 11, 600, C["vurgu"])
    y += 76
    # kartlar
    sw = SOL_W
    ys = y
    ys = ozet_kart(t, x, ys, sw, 1, "Proje ve yapı türü", [
        ("Proje", "Konut Bloğu A · Tokat / Merkez", "künye"),
        ("Yapı türü", "Betonarme", "TS 500:2000"),
        ("Ön geometri", f"4 kat · H_{{N}} ≈ {sy(HN)} m (tahmini)", "md. 3.3.1.3")]) + 12
    ys = ozet_kart(t, x, ys, sw, 3, "Yükler — TS 498:2021", [
        ("Normal kat", f"Konut · Q 2,0 · kaplama {sy(KAPLAMA['deger'])} kN/m²", "Çizelge 6"),
        ("Çatı", f"Teras · Q 2,0 · kaplama {sy(KAPLAMA_CATI['deger'])} kN/m²", "Çizelge 6"),
        ("Duvar", f"Yatay delikli tuğla 19 · {sy(DUVAR['deger'])} kN/m²", "md. 5"),
        ("Kar", f"Bölge {KAR_BOLGE} · {ORN['rakim']} m · S_{{k}} {sy(KAR_SK)} · s {sy(KAR_S)} kN/m²", "Çizelge 3"),
        ("Rüzgâr", "C = 1,2 · q = 0,5 / 0,8 kN/m² (z ≤ 8 / ≤ 20 m)", "Çizelge 4–5")], uyari_satir=(0, 3)) + 12
    ys = ozet_kart(t, x, ys, sw, 5, "Zemin ve temel", [
        ("Zemin", f"q_{{em}} {ORN['q_em']} · q_{{k}} {ORN['q_k']} kN/m² · k_{{0}} {sy(ORN['k0'], 0)}", "md. 10.1 · 16.8"),
        ("Temel", "Mütemadi x+y · B 1,20 · h 1,00 m", "md. 10.4.2"),
        ("Malzeme", "C30/37 · B420C · paspayı 50 mm", "md. 10.1")]) + 12
    ys = ozet_kart(t, x, ys, sw, 7, "Analiz seçenekleri", [
        ("Rijitlik", "Çatlamış: kolon 0,70·EI · kiriş 0,35·EI", "Tablo 4.2"),
        ("Diyafram", "Rijit (kat kütle merkezinde efendi düğüm)", "motor"),
        ("Diğer", "Kiriş öz ağırlığı net · diyagram 11 nokta", "motor")])
    x2 = SAG_X
    w2 = SAG_W
    ys = y
    ys = ozet_kart(t, x2, ys, w2, 2, "Malzemeler", [
        ("Beton", f"C30/37 · f_{{ck}} 30 · f_{{cd}} {sy(BETON['fcd'], 1)} · E_{{c}} {sy(BETON['Ec'], 0)} MPa", "Çizelge 3.2"),
        ("Donatı", f"B420C · f_{{yk}} 420 · f_{{yd}} {sy(DONATI['fyd'], 1)} MPa", "TS 708")]) + 12
    ys = ozet_kart(t, x2, ys, w2, 4, "Deprem — TBDY 2018", [
        ("Yer hareketi", f"S_{{S}} {sy(ORN['SS'], 3)} · S_{{1}} {sy(ORN['S1'], 3)} (DD-2) · DD-3 girildi", "md. 2.3.2"),
        ("Zemin", f"ZD · F_{{S}} {sy(SP2['FS'], 3)} · F_{{1}} {sy(SP2['F1'], 3)}", "Tablo 2.1–2.2"),
        ("Spektrum", f"S_{{DS}} {sy(SP2['SDS'], 3)} · S_{{D1}} {sy(SP2['SD1'], 3)} · T_{{B}} {sy(SP2['TB'], 3)} s", "Denk. 2.1–2.3"),
        ("Sınıflar", f"BKS 3 · I {sy(I_, 1)} · DTS {DTS} · BYS {BYS}", "Tablo 3.1–3.3"),
        ("Sistem", f"{TS['kod']} · R {sy(R_, 0)} · D {sy(D_, 0)} · periyot otomatik", "Tablo 4.1")]) + 12
    ys = ozet_kart(t, x2, ys, w2, 6, "Yük birleşimleri", [
        ("Küme", "TS 500 + TBDY 4.4.4 (ts500)", "md. 6.2.6 · 4.4.4"),
        ("Üretilen", f"{KOMB_TOPLAM} birleşim: {KOMB.get('dayanim', 0)} dayanım · {KOMB.get('deprem', 0)} deprem · {KOMB.get('servis', 0)} servis · {KOMB.get('drift', 0)} öteleme", "")]) + 12
    # ardından
    t.dikdortgen(x2, ys, w2, 112, dolgu=C["yuzey"], kenar=C["cizgi"], r=7)
    t.yazi(x2 + 14, ys + 22, "Ardından", 12, 600, C["metin"])
    yy = ys + 46
    for metin, secili in (("Boş modelle başla (Z = 0 çalışma ızgarası)", False), ("Hızlı aks sihirbazını aç", True),
                          ("Şablondan başla:  betonarme-4kat-4x3", False)):
        radyo(t, x2 + 22, yy - 4, secili)
        t.yazi(x2 + 36, yy, metin, 12, 500 if secili else 400, C["metin"])
        yy += 22

    # ---------------- sağ ray: yazılacaklar
    y = ray_baslik(t, "Projeye uygulanacak")
    y = ray_etiket(t, y, "model/bina.json  ·  yama (özet)")
    y = kod_blogu(t, y, [("sistem: ", '"betonarme"'), ("malzemeler: ", 'C30 → "C30/37", B420C'),
                         ("yuk_durumlari: ", "G Q S W E açık"), ("  S: ", 'il "Tokat", rakim 623, mu 0.8'), ("  W: ", "C 1.2"),
                         ("deprem: ", 'SS 1.2  S1 0.35  ZD  BKS 3'), ("  ", 'tasiyici A11  R 8  D 3'),
                         ("temeller: ", 'tip "surekli"  q_em 150'), ("  ", "q_k 450  k0 18000"),
                         ("kombinasyon_kumesi: ", '"ts500"'), ("analiz: ", "catlamis_rijitlik true"),
                         ("  ", 'kiris_oz "net"  diyagram_nokta 11')], satir=15)
    y = ray_etiket(t, y, "proje/yonetmelik.json")
    y = kod_blogu(t, y, [("kunye, kaynaklar, ", "on_geometri,"), ("varsayilanlar: ", "doseme, cati, duvar"),
                         ("sablon: ", '"Opus Fortis — betonarme konut"')], satir=15)
    y = ray_etiket(t, y, "OLUŞTURUNCA")
    y += 14
    for m in ("Tek geri alma adımı (Ctrl+Z ile tümü geri alınır).",
              "Model ağacında “Yönetmelik verileri” düğümü; durum çubuğunda TBDY · DTS 1 · ZD çipi.",
              "Komut satırına eşdeğer komut yazılır: YÖNETMELİK UYGULA."):
        y = ray_madde(t, y, m)
    alt_cubuk(t, "Tüm adımları gözden geçir", [("Geri", "ikincil", 92, "sevron_sol", None, False),
                                              ("Şablon olarak kaydet…", "ikincil", 186, "kaydet", None, False),
                                              ("Projeyi oluştur", "birincil", 190, "onay", None, False)])


# ============================================================================
# ÜRETİM
# ============================================================================
def ekran(adim_fn):
    t = Tuval(1920, 1080, 1)
    L = Yer()
    kabuk(t, L)
    adim_fn(t)
    t.dikdortgen(0, 0, 1920, 1080, kenar=C["giris_kenar"])
    return t.img


def karsilastirma(gorseller):
    W = 2400
    pad, gap = 40, 32
    cw = (W - 2 * pad - gap) // 2
    ch = round(cw * 1080 / 1920)
    lab = 34
    ust = 86
    H = ust + 2 * (lab + ch) + gap + pad
    t = Tuval(W, H, 1, zemin=C["zemin"])
    t.yazi(pad, 44, "op4 · Yönetmelik Sihirbazı — taslak görseller", 22, 600, C["metin"])
    t.yazi(pad, 68, "“Atölye” yerleşimi, modernize · tek soğuk vurgu (yer tutucu palet: kobalt) · örnek saha değerleri temsilîdir", 13, 400, C["metin2"])
    etiketler = ["1 · Proje ve yapı türü", "4 · Deprem — TBDY 2018 (spektrum önizlemesi)", "5 · Zemin ve temel", "8 · Özet ve onay"]
    for i, (im, et) in enumerate(zip(gorseller, etiketler)):
        x = pad + (i % 2) * (cw + gap)
        y = ust + (i // 2) * (lab + ch + gap)
        t.dikdortgen(x, y + 4, 26, 22, dolgu=C["vurgu"], r=5)
        t.yazi_orta(x + 13, y + 20, et.split(" · ")[0], 12, 700, C["beyaz"])
        t.yazi(x + 36, y + 21, et.split(" · ", 1)[1], 15, 600, C["metin"])
        k = im.resize((cw, ch), Image.LANCZOS)
        t.golge(x, y + lab, cw, ch, r=4, yaricap=8, alfa=0.16, dy=3)
        t.img.paste(k, (x, y + lab))
        t._yenile()
        t.dikdortgen(x, y + lab, cw, ch, kenar=C["cizgi"])
    return t.img


def ana():
    cikti = []
    for ad, fn in (("sihirbaz-1-proje.png", adim1), ("sihirbaz-4-deprem.png", adim4), ("sihirbaz-5-zemin.png", adim5),
                   ("sihirbaz-8-ozet.png", adim8)):
        im = ekran(fn)
        yol = os.path.join(BURASI, ad)
        im.save(yol, optimize=True)
        print("yazıldı:", yol, im.size)
        cikti.append(im)
    k = karsilastirma(cikti)
    yol = os.path.join(BURASI, "karsilastirma.png")
    k.save(yol, optimize=True)
    print("yazıldı:", yol, k.size)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        fn = {"1": adim1, "4": adim4, "5": adim5, "8": adim8}[sys.argv[1]]
        ekran(fn).save(os.path.join(BURASI, f"_dene-{sys.argv[1]}.png"))
    else:
        ana()
